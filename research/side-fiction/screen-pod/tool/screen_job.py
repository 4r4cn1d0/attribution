"""The screen's pod job (runs on the pod; started step by step by screen_run.sh, which screen_pod.py starts over ssh).

Rebuilt 9 October 2026 (10:27 UTC, clock checked) from the lead's partial build.

    screen_job.py verify     --bundle B                                   the bundle's files and pins (stdlib)
    screen_job.py llama-info --cmake-args A --nvcc-source S --build-log L --record R   llama-cpp-python's build
    screen_job.py download   --bundle B --record R                        the three pinned snapshots, no token (guard venv)
    screen_job.py ka         --bundle B --record R --labels L             the known-answer check (granite venv)
    screen_job.py granite    --bundle B --ka K --cache C --record R       Granite harm + sexual_content (granite venv)
    screen_job.py qwen       --bundle B --ka K --cache C --record R       Qwen3Guard through the engine (guard venv)
    screen_job.py record     --root ROOT --exit E --step S                out/run-record.json from the step records
    screen_job.py status     --root ROOT                                  one JSON line: DONE.json, the step, progress
    screen_job.py sums       --root ROOT                                  one JSON line: SHA-256 of each output file

The known-answer check runs first and alone: `ka` judges the 200 known answers with the screen's own Granite code and
writes out/ka.json (counts, seconds per answer and the verdict of the pre-set rule) and out/ka-labels.jsonl (ids and
labels). It exits 4 when the rule fails, and 2 when the first answers show no GPU offload; screen_run.sh then ends (no
row is screened) and the launcher stops the pod. `granite` and `qwen` refuse (exit 2) unless out/ka.json holds a pass
that its own counts support. The row limit of a smoke run is the bundle's (job-manifest.json "limit": that many rows of
each source). Exit codes: 0 done, 1 error (its type is recorded; the traceback stays in out/job.log on the pod), 2
refused, 4 the known-answer check failed, 5 stopped by SIGTERM (resumable). Prints and records counts, ids, labels and
SHA-256 only; never row, prompt, answer or judge-output text.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import signal
import subprocess
import sys
import traceback
from importlib import metadata

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402
import screen_rows as R  # noqa: E402
import screen_bundle as SB  # noqa: E402
import screen_models as M  # noqa: E402
from common import Refusal, canonical_bytes, sha256_file  # noqa: E402

STOP = {"flag": False}
OUTPUTS = ("DONE.json", "out/run-record.json", "out/ka.json", "out/ka-labels.jsonl", "out/granite.jsonl",
           "out/qwen.jsonl", "out/download-check.json", "out/llama-info.json", "out/environment-g.lock",
           "out/environment-q.lock", "out/pip.log", "out/llama-build.log")      # never out/job.log or run.log
STEP_RECORDS = {"ka": "out/ka.json", "granite": "out/granite-record.json", "qwen": "out/qwen-record.json",
                "llama": "out/llama-info.json", "download": "out/download-check.json"}
CACHES = ("out/ka-labels.jsonl", "out/granite.jsonl", "out/qwen.jsonl")
STATUS_EVENTS = frozenset({"bundle_verified", "packages", "files_verified", "loaded", "plan", "progress", "ka_done",
                           "granite_done", "qwen_done", "download_done", "llama_info", "record",
                           "stopping_on_signal"})
STATUS_FIELDS = ("event", "step", "judged", "of", "sec_per_item", "eta_min", "cached", "todo", "rows", "seconds",
                 "exit", "identical", "pod_yes", "mac_yes", "delta_yes", "passed", "stopped", "files")
NVCC_SOURCES = ("image", "apt")


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(**fields) -> None:
    print(json.dumps({"utc": utc(), **fields}, sort_keys=True), flush=True)


def write_atomic(path: pathlib.Path, data: bytes) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def require_packages(pins: dict, torch_public: str | None = None, version=metadata.version) -> dict:
    """Every pinned distribution at its exact version (importlib.metadata only; nothing is imported); torch at its
    public version when asked."""
    found = {}
    for dist, want in {**pins, **({"torch": None} if torch_public else {})}.items():
        try:
            got = version(dist)
        except metadata.PackageNotFoundError:
            raise Refusal(f"package {dist} is not installed for {sys.executable}") from None
        ok = got.split("+", 1)[0] == torch_public if dist == "torch" else got == want
        if not ok:
            raise Refusal(f"package {dist} is {got}, not the pinned {torch_public if dist == 'torch' else want}")
        found[dist] = got
    return found


def ka_gate(path: pathlib.Path) -> dict:
    """out/ka.json must hold a pass that its own counts support; otherwise no row is screened."""
    try:
        record = json.loads(pathlib.Path(path).read_bytes())
    except (OSError, ValueError):
        raise Refusal("no readable known-answer record: no row is screened before the check passes") from None
    if not (isinstance(record, dict) and record.get("passed") is True and R.ka_passed(record.get("counts") or {})):
        raise Refusal("the known-answer check did not pass: no row is screened")
    return record


def _sources(bundle: pathlib.Path, manifest: dict, names) -> list:
    rows = SB.pod_sources(bundle, manifest)
    return [row for s in manifest["sources"] if s["source"] in names for row in rows[s["source"]]]


def tally(cache, kind: str) -> dict:
    """Counts by source (and criteria and label, or safety label) of a cache: no text, no ids."""
    out: dict = {}
    for entry in cache.entries.values():
        per = out.setdefault(entry["source"], {})
        if kind == "granite":
            c = per.setdefault(entry["criteria"], {"Yes": 0, "No": 0, "invalid": 0, "retried": 0, "trimmed": 0})
            c[entry["label"]] += 1
            c["retried"] += entry["attempts"] == 2
            c["trimmed"] += entry["trimmed"]
        else:
            key = entry["safety"] if entry["valid"] else "invalid"
            per[key] = per.get(key, 0) + 1
    return out


class Step:
    """One step's record, written atomically whatever the outcome, and its exit code."""

    def __init__(self, record_path: pathlib.Path, kind: str):
        self.path = pathlib.Path(record_path)
        self.record = {"kind": f"fiction-screen {kind} record", "started_utc": utc(), "refused": None, "error": None}
        self.code = P.POD_EXIT_ERROR

    def __enter__(self):
        STOP["flag"] = False
        self.previous = signal.signal(signal.SIGTERM, lambda *_: STOP.__setitem__("flag", True))
        return self

    def __exit__(self, exc_type, exc, tb):
        signal.signal(signal.SIGTERM, self.previous)
        if isinstance(exc, Refusal):
            self.record["refused"] = str(exc)
            print(f"refused: {exc}", file=sys.stderr)
            self.code = P.POD_EXIT_REFUSED
        elif exc is not None:
            self.record["error"] = exc_type.__name__
            traceback.print_exception(exc_type, exc, tb, file=sys.stderr)
            self.code = P.POD_EXIT_ERROR
        self.record.update(exit=self.code, ended_utc=utc())
        write_atomic(self.path, canonical_bytes(self.record))
        return exc is None or isinstance(exc, Exception)


# ---------------------------------------------------------------- commands

def cmd_verify(a) -> int:
    manifest = SB.verify_bundle(a.bundle)
    log(event="bundle_verified", files=len(manifest["files"]), rows={s["source"]: s["rows"] for s in manifest["sources"]},
        round=manifest["round"], limit=manifest["limit"], manifest_sha256=manifest["manifest_sha256"])
    return 0


def cmd_llama_info(a) -> int:
    """llama-cpp-python's version, GPU offload and system info, nvcc's release line and where nvcc came from, the
    CMAKE_ARGS and the build log's SHA-256 (out/llama-info.json); refuses unless the version is the pinned one, GPU
    offload is built in and the arguments are the pinned ones."""
    import llama_cpp
    nvcc = None
    try:
        q = subprocess.run(["nvcc", "--version"], capture_output=True, text=True, timeout=60)
        nvcc = next((ln.strip() for ln in q.stdout.splitlines() if "release" in ln), None) if q.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        nvcc = None
    record = {"kind": "fiction-screen llama-cpp-python build", "utc": utc(), "version": llama_cpp.__version__,
              "gpu_offload": bool(llama_cpp.llama_supports_gpu_offload()),
              "system_info": llama_cpp.llama_print_system_info().decode("utf-8", "replace")[:2000],
              "cmake_args": a.cmake_args, "nvcc": nvcc, "nvcc_source": a.nvcc_source,
              "sdist_sha256": P.LLAMA_SDIST_SHA256,
              "build_log_sha256": sha256_file(a.build_log) if pathlib.Path(a.build_log).is_file() else None,
              "package": metadata.version("llama_cpp_python")}
    write_atomic(a.record, canonical_bytes(record))
    log(event="llama_info", version=record["version"], gpu_offload=record["gpu_offload"], nvcc=nvcc)
    if (record["version"] != P.LLAMA_VERSION or not record["gpu_offload"] or a.cmake_args != P.LLAMA_CMAKE_ARGS
            or a.nvcc_source not in NVCC_SOURCES):
        raise Refusal("llama-cpp-python is not the pinned version built with CUDA and the pinned CMAKE_ARGS")
    return 0


def cmd_download(a) -> int:
    SB.verify_bundle(a.bundle)
    record = {"kind": "fiction-screen download check", "utc": utc(), "token": False,
              "packages": require_packages(P.GUARD_PACKAGES, P.TORCH_PUBLIC)}
    record["snapshots"] = M.download()
    write_atomic(a.record, canonical_bytes(record))
    log(event="download_done", files=sum(len(v["files"]) for v in record["snapshots"].values()))
    return 0


def _granite_judge(judge_factory):
    import granite_screen as G
    if judge_factory is not None:
        return judge_factory(), {}
    packages = require_packages(P.GRANITE_PACKAGES)
    gguf, tokdir = M.granite_paths()
    log(event="files_verified", files=1 + len(P.GRANITE_TOK_FILES))
    return G.GraniteJudge(G.load_tokenizer(tokdir), G.load_llm(gguf)), packages


def cmd_ka(a, judge_factory=None) -> int:
    import granite_screen as G
    with Step(a.record, "known-answer") as step:
        step.record["rule"] = R.KA_RULE
        manifest = SB.verify_bundle(a.bundle)
        step.record["bundle_manifest_sha256"] = manifest["manifest_sha256"]
        ka_items, mac_labels = SB.pod_ka(a.bundle, manifest)
        log(event="bundle_verified", step="ka", rows=len(ka_items))
        judge, step.record["packages"] = _granite_judge(judge_factory)
        log(event="loaded", step="ka")
        counts, entries, stopped, per_item = G.known_answer(judge, ka_items, mac_labels, lambda: STOP["flag"], log)
        write_atomic(a.labels, b"".join(json.dumps(e, sort_keys=True).encode() + b"\n" for e in entries))
        passed = (not stopped) and R.ka_passed(counts)
        step.record.update(counts=counts, passed=passed, stopped=stopped, calls=judge.calls, retries=judge.retries,
                           errors=judge.errors, seconds_per_item=per_item, labels_sha256=sha256_file(a.labels))
        log(event="ka_done", step="ka", passed=passed, stopped=stopped, identical=counts["identical"],
            pod_yes=counts["pod_yes"], mac_yes=counts["mac_yes"], delta_yes=counts["delta_yes"],
            judged=counts["judged"], sec_per_item=per_item)
        step.code = P.POD_EXIT_STOPPED if stopped else (P.POD_EXIT_OK if passed else P.POD_EXIT_KA_FAILED)
    return step.code


def cmd_granite(a, judge_factory=None) -> int:
    import granite_screen as G
    with Step(a.record, "granite") as step:
        manifest = SB.verify_bundle(a.bundle)
        step.record["bundle_manifest_sha256"] = manifest["manifest_sha256"]
        step.record["ka_passed"] = ka_gate(a.ka)["passed"]
        rows = _sources(a.bundle, manifest, P.GRANITE_SOURCES)
        judge, step.record["packages"] = _granite_judge(judge_factory)
        log(event="loaded", step="granite", rows=len(rows))
        cache = R.JsonlCache(a.cache, R.check_granite, R.granite_key)
        seeded = seed_cache(a.bundle, manifest, "granite", a.cache, cache)
        try:
            result = G.screen(judge, rows, cache, lambda: STOP["flag"], log, manifest["limit"])
        finally:
            cache.close()
        step.record.update(result=result, seeded=seeded, counts=tally(cache, "granite"), limit=manifest["limit"],
                           cache_sha256=sha256_file(a.cache) if pathlib.Path(a.cache).exists() else None,
                           cache_undecodable_lines=cache.undecodable)
        log(event="granite_done", step="granite", judged=result["judged"], cached=result["cached"],
            todo=result["todo"], stopped=result["stopped"])
        step.code = P.POD_EXIT_STOPPED if result["stopped"] else P.POD_EXIT_OK
    return step.code


def cmd_qwen(a, guard_factory=None) -> int:
    import guard_screen as GS
    with Step(a.record, "qwen3guard") as step:
        manifest = SB.verify_bundle(a.bundle)
        step.record["bundle_manifest_sha256"] = manifest["manifest_sha256"]
        step.record["ka_passed"] = ka_gate(a.ka)["passed"]
        rows = _sources(a.bundle, manifest, P.ROUND_SOURCES[manifest["round"]])
        if guard_factory is None:
            step.record["packages"] = require_packages(P.GUARD_PACKAGES, P.TORCH_PUBLIC)
            step.record["snapshot"] = M.verify_snapshot("qwen3guard")
            guard, info = GS.load_guard(pathlib.Path(a.bundle) / "engine", pathlib.Path(a.cache).parent / "qwen-ledger")
            step.record["environment"] = info["environment"]
        else:
            guard = guard_factory()
        step.record["guard_identity"] = {k: v for k, v in (getattr(guard, "identity", None) or {}).items()
                                         if k in ("repo_id", "revision", "chat_template_sha256", "stop_ids", "pad_id",
                                                  "attn_implementation")}
        log(event="loaded", step="qwen", rows=len(rows))
        cache = R.JsonlCache(a.cache, R.check_qwen, R.qwen_key)
        seeded = seed_cache(a.bundle, manifest, "qwen", a.cache, cache)
        try:
            result = GS.screen(guard, rows, cache, lambda: STOP["flag"], log, manifest["limit"])
        finally:
            cache.close()
        step.record.update(result=result, seeded=seeded, counts=tally(cache, "qwen"), limit=manifest["limit"],
                           cache_sha256=sha256_file(a.cache) if pathlib.Path(a.cache).exists() else None,
                           cache_undecodable_lines=cache.undecodable)
        log(event="qwen_done", step="qwen", judged=result["judged"], cached=result["cached"], todo=result["todo"],
            stopped=result["stopped"])
        step.code = P.POD_EXIT_STOPPED if result["stopped"] else P.POD_EXIT_OK
    return step.code


def seed_cache(bundle: pathlib.Path, manifest: dict, judge: str, cache_path: pathlib.Path, cache) -> int:
    """A resumed launch: the earlier launch's verified cache seeds this one's when this one's is still empty."""
    entry = (manifest.get("resume") or {}).get(judge)
    if entry is None or len(cache) or pathlib.Path(cache_path).exists() and pathlib.Path(cache_path).stat().st_size:
        return 0
    src = pathlib.Path(bundle) / entry["path"]
    if sha256_file(src) != entry["sha256"]:
        raise Refusal(f"the resume cache of {judge} does not have its recorded SHA-256")
    seeded = R.JsonlCache(src, cache.check, cache.key)
    for record in seeded.entries.values():
        cache.append(record)
    return len(seeded)


def cmd_record(a) -> int:
    """out/run-record.json from the step records (best effort per part: a missing or unreadable part is null)."""
    root = pathlib.Path(a.root)
    record = {"kind": "fiction-screen run record", "version": 2, "device": "cuda", "exit": a.exit, "step": a.step,
              "utc": utc()}
    try:
        manifest, msha = SB.load_manifest(root / "bundle")
        record.update(tag=manifest.get("tag"), round=manifest.get("round"), limit=manifest.get("limit"),
                      bundle_manifest_sha256=msha)
    except (OSError, ValueError, Refusal) as e:
        record["manifest_error"] = type(e).__name__
    for name, rel in STEP_RECORDS.items():
        try:
            record[name] = json.loads((root / rel).read_bytes())
        except (OSError, ValueError):
            record[name] = None
    record["outputs"] = {rel: ({"sha256": sha256_file(root / rel), "bytes": (root / rel).stat().st_size}
                               if (root / rel).is_file() else None) for rel in CACHES}
    write_atomic(root / "out/run-record.json", canonical_bytes(record))
    log(event="record", exit=a.exit, step=a.step)
    return 0


def last_status_line(path: pathlib.Path):
    try:
        data = pathlib.Path(path).read_bytes()[-65536:]
    except OSError:
        return None
    for line in reversed(data.split(b"\n")):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("event") in STATUS_EVENTS:
            return {k: entry[k] for k in STATUS_FIELDS if k in entry and isinstance(entry[k], (int, float, str, bool))
                    and not (isinstance(entry[k], str) and len(entry[k]) > 64)}
    return None


def cmd_status(a) -> int:
    root = pathlib.Path(a.root)
    done = None
    if (root / "DONE.json").is_file():
        try:
            d = json.loads((root / "DONE.json").read_bytes())
            done = {"exit": d.get("exit"), "step": d.get("step"), "utc": d.get("utc")}
        except ValueError:
            done = {"exit": None, "step": "unreadable"}
    step = (root / "STEP").read_text().strip()[:32] if (root / "STEP").is_file() else None
    print(json.dumps({"started": (root / "STARTED.json").is_file(), "step": step, "done": done,
                      "progress": last_status_line(root / "out/job.log")}, sort_keys=True))
    return 0


def cmd_sums(a) -> int:
    root = pathlib.Path(a.root)
    print(json.dumps({"files": {rel: (sha256_file(root / rel) if (root / rel).is_file() else None) for rel in OUTPUTS}},
                     sort_keys=True))
    return 0


def main(argv=None, judge_factory=None, guard_factory=None) -> int:
    ap = argparse.ArgumentParser(description="The fiction screen's pod job (counts, ids, labels and hashes only).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--bundle", type=pathlib.Path, required=True)
    p = sub.add_parser("llama-info")
    p.add_argument("--cmake-args", required=True)
    p.add_argument("--nvcc-source", required=True)
    p.add_argument("--build-log", type=pathlib.Path, required=True)
    p.add_argument("--record", type=pathlib.Path, required=True)
    p = sub.add_parser("download")
    p.add_argument("--bundle", type=pathlib.Path, required=True)
    p.add_argument("--record", type=pathlib.Path, required=True)
    p = sub.add_parser("ka")
    p.add_argument("--bundle", type=pathlib.Path, required=True)
    p.add_argument("--record", type=pathlib.Path, required=True)
    p.add_argument("--labels", type=pathlib.Path, required=True)
    for name in ("granite", "qwen"):
        p = sub.add_parser(name)
        p.add_argument("--bundle", type=pathlib.Path, required=True)
        p.add_argument("--ka", type=pathlib.Path, required=True)
        p.add_argument("--cache", type=pathlib.Path, required=True)
        p.add_argument("--record", type=pathlib.Path, required=True)
    p = sub.add_parser("record")
    p.add_argument("--root", type=pathlib.Path, required=True)
    p.add_argument("--exit", type=int, required=True)
    p.add_argument("--step", required=True)
    for name in ("status", "sums"):
        p = sub.add_parser(name)
        p.add_argument("--root", type=pathlib.Path, required=True)
    a = ap.parse_args(argv)
    if a.cmd == "ka":
        return cmd_ka(a, judge_factory)
    if a.cmd == "granite":
        return cmd_granite(a, judge_factory)
    if a.cmd == "qwen":
        return cmd_qwen(a, guard_factory)
    try:
        return {"verify": cmd_verify, "llama-info": cmd_llama_info, "download": cmd_download, "record": cmd_record,
                "status": cmd_status, "sums": cmd_sums}[a.cmd](a)
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return P.POD_EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
