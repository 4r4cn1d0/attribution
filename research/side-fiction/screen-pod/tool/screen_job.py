"""The screen's pod job (runs on the pod; started step by step by screen_run.sh, which screen_pod.py starts over ssh).

Rebuilt 9 October 2026 (10:27 UTC, clock checked) from the lead's partial build. Revised 9 October 2026 (17:11 UTC,
clock checked): ONE Granite-on-CUDA backend, the lead's (scripts/gate_b_mac_judges/pod, 2694bd0).

    screen_job.py verify   --bundle B                                       the bundle's files and pins (stdlib)
    screen_job.py download --bundle B --record R                            the pinned Qwen3Guard snapshot (guard venv)
    screen_job.py ka       --bundle B --granite-root G --granite-exit N --record R    the lead's gate, read (stdlib)
    screen_job.py granite  --bundle B --ka K --cache C --record R           Granite harm + sexual_content (Granite venv)
    screen_job.py qwen     --bundle B --ka K --cache C --record R           Qwen3Guard through the engine (guard venv)
    screen_job.py record   --root ROOT --exit E --step S                    out/run-record.json from the step records
    screen_job.py status   --root ROOT                                      one JSON line: DONE.json, the steps, progress
    screen_job.py sums     --root ROOT                                      one JSON line: SHA-256 of each output file

Before `ka`, screen_run.sh runs the lead's own Granite pod job (pod_run_granite.sh) on the bundle's gate_b/ (a lead
bundle with no requested unit): it makes the Granite venv, builds llama-cpp-python with CUDA, downloads and checks the
GGUF, checks the packages, the GPU offload, the files and the tokenizer fingerprint, and runs the lead's known-answer
gate (pod_job.known_answer_gate: the 200 OLMo-2-1B recipe-B seed-1101 e1 answers, at least 190 identical and |delta
yes| <= 5; exit 3 when it fails). `ka` reads what that job left (its exit code, DONE.json, run record and job.log) and
writes out/ka.json: the lead's gate block, recounted from its own ids and flips against the reference and checked
against the rule; the gate's seconds per answer (from the lead's job.log stamps: the granite_precheck line logged right
before the model loads to the gate's closing line; 1 s resolution, the model load included, so an upper estimate); and
the speed verdict: the projection is those seconds per answer x r, where r = the round's mean tokens per Granite call /
the known answers' mean template tokens, both counted at bundle time (job-manifest.json "granite_tokens"; about 197 /
421 = 0.47 in round 1). It exits 4 when the gate failed (the lead's exit 3), 3 when it passed but the projection is
above GRANITE_S_PER_CALL (0.4 s, the cap's planning time), 5 when the lead's job was stopped, 2 when it refused, 1 on
any other failure of the lead's job (setup, build, download, time limit). The gate is the lead's and runs once: the
screen judges no known answer itself. `granite` (in the lead's Granite venv) checks the packages and the GPU offload
(granite_pod.require_granite_packages, llama_info), then judges every row through granite_pod.judge_triples with one
GraniteSession (gate_b/granite-tokenizer, the GGUF at /root/granite-gguf, the Mac's tokenizer fingerprint required).
`granite` and `qwen` refuse (exit 2) unless out/ka.json holds a pass that its own counts support and is not too slow.
The row limit of a smoke run is the bundle's (job-manifest.json "limit": that many rows of each source). Exit codes:
0 done, 1 error (its type is recorded; the traceback stays in out/job.log on the pod), 2 refused, 3 the known answers
too slow, 4 the known-answer gate failed, 5 stopped by SIGTERM (resumable). Prints and records counts, ids, labels and
SHA-256 only; never row, prompt, answer or judge-output text.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import signal
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
import granite_pod  # noqa: E402  (the lead's backend; stdlib at import)
from common import Refusal, canonical_bytes, sha256_file  # noqa: E402

STOP = {"flag": False}
GJ = P.GRANITE_JOB                    # the lead's Granite job's root, linked beside out/ (screen_run.sh)
LEAD_OUTPUTS = (f"{GJ}/DONE.json", f"{GJ}/out/run-record.json", f"{GJ}/out/llama-build.json",
                f"{GJ}/out/gguf-check.json", f"{GJ}/out/environment-pod.lock", f"{GJ}/out/pip.log",
                f"{GJ}/out/llama-build.log")                     # never the lead's out/job.log (tracebacks stay)
OUTPUTS = ("DONE.json", "out/run-record.json", "out/ka.json", "out/granite.jsonl", "out/qwen.jsonl",
           *LEAD_OUTPUTS, "out/download-check.json", "out/environment-q.lock", "out/pip.log")   # never out/job.log
STEP_RECORDS = {"ka": "out/ka.json", "granite": "out/granite-record.json", "qwen": "out/qwen-record.json",
                "download": "out/download-check.json"}
CACHES = ("out/granite.jsonl", "out/qwen.jsonl")
STATUS_EVENTS = frozenset({"bundle_verified", "packages", "backend_ready", "loaded", "plan", "progress", "ka_done",
                           "granite_done", "qwen_done", "download_done", "record", "stopping_on_signal"})
STATUS_FIELDS = ("event", "step", "judged", "of", "sec_per_item", "eta_min", "cached", "todo", "rows", "seconds",
                 "exit", "identical", "pod_yes", "mac_yes", "delta_yes", "passed", "stopped", "files", "lead_exit")
UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime(UTC_FORMAT)


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


def speed_verdict(per_item, tokens: dict) -> dict:
    """The known answers' measured seconds per answer projected onto this round's Granite calls by r (the manifest's
    token ratio): the projected seconds per call and Granite minutes, and too_slow when the projection is above
    GRANITE_S_PER_CALL (or when the gate was not timed: never a pass)."""
    r = tokens["ratio"]
    projected = None if per_item is None else per_item * r
    return {"seconds_per_item": per_item, "ratio": r,
            "fiction_mean_tokens_per_call": tokens["fiction_mean_tokens_per_call"],
            "ka_mean_tokens": tokens["ka_mean_tokens"], "granite_calls": tokens["fiction_calls"],
            "projected_s_per_call": None if projected is None else round(projected, 4),
            "projected_granite_minutes": None if projected is None else round(projected * tokens["fiction_calls"] / 60, 1),
            "planned_s_per_call": P.GRANITE_S_PER_CALL,
            "too_slow": projected is None or projected > P.GRANITE_S_PER_CALL}


def _epoch(stamp) -> float:
    return dt.datetime.strptime(stamp, UTC_FORMAT).replace(tzinfo=dt.timezone.utc).timestamp()


def gate_timing(job_log: pathlib.Path, judged) -> dict:
    """The lead's gate's judging time, read from the lead's job.log (its judging.log lines carry "utc" to the second):
    from the gate's granite_precheck line (granite_files.granite_judge logs it after the files' check and the token
    check of the 200 answers, right before the model loads) to the gate's closing known_answers line. The interval
    holds the model load and the 200 calls, so seconds_per_item is an upper estimate of the time per answer. None when
    the lines are not found (the speed verdict then stops the run)."""
    out = {"source": "the lead's out/job.log stamps (1 s resolution); the interval includes the model load",
           "judged": judged, "precheck_utc": None, "done_utc": None, "seconds": None, "seconds_per_item": None,
           "ka_input_tokens_max_pod": None, "problem": None}
    try:
        data = pathlib.Path(job_log).read_bytes()
    except OSError:
        return {**out, "problem": "no job.log"}
    events = []
    for line in data.split(b"\n"):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and isinstance(entry.get("event"), str) and isinstance(entry.get("utc"), str):
            events.append(entry)
    starts = [i for i, e in enumerate(events) if e["event"] == "known_answers" and e.get("judged") == 0]
    pre = [i for i in range(starts[-1] + 1, len(events)) if events[i]["event"] == "granite_precheck"] if starts else []
    ends = ([i for i in range(pre[0] + 1, len(events)) if events[i]["event"] == "known_answers"
             and events[i].get("judged") == judged] if pre else [])
    if not (starts and pre and ends) or not (isinstance(judged, int) and judged > 0):
        return {**out, "problem": "the gate's start, precheck or closing line is not in the lead's job.log"}
    first, last = events[pre[0]], events[ends[0]]
    try:
        seconds = _epoch(last["utc"]) - _epoch(first["utc"])
    except ValueError:
        return {**out, "problem": "a stamp is not UTC to the second"}
    if seconds < 0 or first.get("items") != P.KA_N:
        return {**out, "problem": "the stamps run backwards, or the precheck is not the gate's 200 answers"}
    tokens_max = first.get("input_tokens_max")
    return {**out, "precheck_utc": first["utc"], "done_utc": last["utc"], "seconds": seconds,
            "seconds_per_item": round(seconds / judged, 4),
            "ka_input_tokens_max_pod": tokens_max if isinstance(tokens_max, int) else None}


def _read_json(path: pathlib.Path):
    try:
        return json.loads(pathlib.Path(path).read_bytes())
    except (OSError, ValueError):
        return None


def ka_gate(path: pathlib.Path, bundle: pathlib.Path) -> dict:
    """out/ka.json must hold a pass of the lead's gate that its own counts support (the rule, and the recount from its
    ids and flips against the bundle's reference) and must not be too slow; otherwise no row is screened."""
    record = _read_json(path)
    if not isinstance(record, dict):
        raise Refusal("no readable known-answer record: no row is screened before the gate passes")
    block = record.get("known_answers")
    if not (record.get("passed") is True and isinstance(block, dict) and block.get("passed") is True
            and R.ka_rule_passes(block)):
        raise Refusal("the lead's known-answer gate did not pass: no row is screened")
    R.ka_recount(block, SB.ka_reference(pathlib.Path(bundle) / SB.KA_REFERENCE))
    if record.get("too_slow") is not False:
        raise Refusal("the known answers ran slower than the cap was planned for (or were not timed): no row is "
                      "screened")
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


def cmd_download(a) -> int:
    SB.verify_bundle(a.bundle)
    record = {"kind": "fiction-screen download check", "utc": utc(), "token": False,
              "packages": require_packages(P.GUARD_PACKAGES, P.TORCH_PUBLIC)}
    record["snapshots"] = M.download()
    write_atomic(a.record, canonical_bytes(record))
    log(event="download_done", files=sum(len(v["files"]) for v in record["snapshots"].values()))
    return 0


def lead_summary(root: pathlib.Path, granite_exit: int) -> tuple[dict, dict | None]:
    """What the lead's Granite job left in its root: (a summary of counts, versions and hashes; its run record or None).
    The lead's refusal text is its own (ids and hashes); its job.log is never copied."""
    done, record = _read_json(root / "DONE.json"), _read_json(root / "out/run-record.json")
    done = done if isinstance(done, dict) else None
    rec = record if isinstance(record, dict) else {}
    llama = rec.get("llama") if isinstance(rec.get("llama"), dict) else {}
    build = llama.get("build") if isinstance(llama.get("build"), dict) else {}
    env = rec.get("environment") if isinstance(rec.get("environment"), dict) else {}
    files = rec.get("files") if isinstance(rec.get("files"), dict) else {}
    summary = {"exit": granite_exit, "done": None if done is None else {k: done.get(k) for k in ("exit", "step", "utc")},
               "run_record_sha256": sha256_file(root / "out/run-record.json") if rec else None,
               "run_record_exit": rec.get("exit"), "bundle_manifest_sha256": rec.get("bundle_manifest_sha256"),
               "refused": str(rec.get("refused"))[:500] if rec.get("refused") else None, "error": rec.get("error"),
               "llama": {"version": llama.get("llama_cpp_python"), "gpu_offload": llama.get("gpu_offload"),
                         "cuda": build.get("cuda"), "build_log_sha256": build.get("build_log_sha256"),
                         "build_jobs": build.get("build_jobs"), "build_seconds": build.get("build_seconds")},
               "tokenizer_fingerprint": rec.get("tokenizer_fingerprint"), "gpu": env.get("gpu"),
               "gguf_sha256": files.get("gguf_sha256")}
    return summary, (rec or None)


def cmd_ka(a) -> int:
    """The lead's known-answer gate, read (see the module text): out/ka.json, and the exit code that decides the job."""
    with Step(a.record, "known-answer") as step:
        step.record["rule"] = R.KA_RULE
        manifest = SB.verify_bundle(a.bundle)
        step.record["bundle_manifest_sha256"] = manifest["manifest_sha256"]
        root = pathlib.Path(a.granite_root)
        lead, record = lead_summary(root, a.granite_exit)
        step.record.update(lead=lead, known_answers=None, passed=False, stopped=a.granite_exit == P.POD_EXIT_STOPPED,
                           too_slow=None, timing=None, speed=None, seconds_per_item=None)
        verdict_step = {0: "done", P.LEAD_EXIT_GATE_FAILED: "run"}.get(a.granite_exit)
        if verdict_step is None or lead["done"] != {**(lead["done"] or {}), "exit": a.granite_exit, "step": verdict_step}:
            # no gate verdict: the job ended in setup (whatever its code: pip can exit 3 too), was refused, stopped or
            # timed out; a verdict is only exit 0 at step done or exit 3 at step run (the lead's DONE.json)
            block = (record or {}).get("known_answers")
            step.record["known_answers"] = block if isinstance(block, dict) else None
            log(event="ka_done", step="ka", passed=False, stopped=step.record["stopped"], lead_exit=a.granite_exit)
            step.code = (P.POD_EXIT_STOPPED if a.granite_exit == P.POD_EXIT_STOPPED
                         else P.POD_EXIT_REFUSED if a.granite_exit == P.POD_EXIT_REFUSED else P.POD_EXIT_ERROR)
            step.record["lead_verdict"] = False
            return step.code
        if record is None:
            raise Refusal("the lead's Granite job ended with a gate verdict but left no run record")
        if (record.get("kind") != "judge-pod run record" or record.get("device") != "cuda"
                or record.get("judge") != SB.GRANITE or record.get("exit") != a.granite_exit
                or record.get("bundle_manifest_sha256") != manifest["gate_b"]["manifest_sha256"]):
            raise Refusal("the lead's run record is not a cuda Granite run of this bundle's gate_b with this exit")
        block = record.get("known_answers")
        if not (isinstance(block, dict) and block.get("enabled") is True and block.get("stopped") is False
                and block.get("reference_sha256") == P.KA_REFERENCE_SHA256
                and block.get("complete_sha256") == P.KA_COMPLETE_SHA256):
            raise Refusal("the lead's run record holds no finished gate of the pinned reference and unit")
        step.record.update(known_answers=block, lead_verdict=True)
        R.ka_recount(block, SB.ka_reference(pathlib.Path(a.bundle) / SB.KA_REFERENCE))
        passed = block.get("passed") is True
        if passed != R.ka_rule_passes(block) or passed != (a.granite_exit == 0):
            raise Refusal("the gate's verdict contradicts its counts or the lead's exit code")
        tokens = SB.check_granite_tokens(manifest.get("granite_tokens"))
        timing = gate_timing(root / "out/job.log", block.get("judged"))
        speed = speed_verdict(timing["seconds_per_item"], tokens)
        too_slow = passed and speed["too_slow"]
        step.record.update(passed=passed, too_slow=too_slow, timing=timing, speed=speed,
                           seconds_per_item=timing["seconds_per_item"], planned_s_per_call=P.GRANITE_S_PER_CALL)
        log(event="ka_done", step="ka", passed=passed, stopped=False, identical=block.get("identical"),
            pod_yes=block.get("pod_yes"), mac_yes=block.get("mac_yes"), delta_yes=block.get("delta_yes"),
            judged=block.get("judged"), sec_per_item=timing["seconds_per_item"],
            projected_s_per_call=speed["projected_s_per_call"], ratio=speed["ratio"], lead_exit=a.granite_exit)
        step.code = (P.POD_EXIT_KA_FAILED if not passed else P.POD_EXIT_TOO_SLOW if too_slow else P.POD_EXIT_OK)
    return step.code


def granite_backend(bundle: pathlib.Path, manifest: dict, session_factory=None):
    """The lead's Granite backend for this step: the packages and the GPU offload checked first (no row is judged
    otherwise), then one GraniteSession on the bundle's tokenizer folder and the pod's GGUF, refusing any tokenizer
    whose fingerprint is not the Mac's (judge_triples' own default). session_factory: tests (fake loaders)."""
    if session_factory is not None:
        return session_factory(), {"packages": None, "llama": None, "session": "test factory"}
    packages = granite_pod.require_granite_packages()
    llama = granite_pod.llama_info()
    if llama.get("gpu_offload") is not True:
        raise Refusal("llama-cpp-python cannot offload to the GPU (not a CUDA build): no row is screened")
    tok_dir = pathlib.Path(bundle) / SB.GATE_B / manifest["gate_b"]["tokenizer_dir"]
    session = granite_pod.GraniteSession(tok_dir, granite_pod.POD_GGUF,
                                         require_fingerprint=granite_pod.MAC_TOKENIZER_FINGERPRINT)
    return session, {"packages": packages, "llama": llama, "gguf": str(granite_pod.POD_GGUF),
                     "tokenizer_dir": f"{SB.GATE_B}/{manifest['gate_b']['tokenizer_dir']}",
                     "fingerprint_required": granite_pod.MAC_TOKENIZER_FINGERPRINT}


def cmd_granite(a, judge_factory=None) -> int:
    import granite_screen as G
    with Step(a.record, "granite") as step:
        manifest = SB.verify_bundle(a.bundle)
        step.record["bundle_manifest_sha256"] = manifest["manifest_sha256"]
        step.record["ka_passed"] = ka_gate(a.ka, a.bundle)["passed"]
        rows = _sources(a.bundle, manifest, P.GRANITE_SOURCES)
        session, step.record["backend"] = granite_backend(a.bundle, manifest, judge_factory)
        log(event="backend_ready", step="granite", rows=len(rows))
        cache = R.JsonlCache(a.cache, R.check_granite, R.granite_key)
        seeded = seed_cache(a.bundle, manifest, "granite", a.cache, cache)
        try:
            result = G.screen(session, rows, cache, lambda: STOP["flag"], log, manifest["limit"])
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
        step.record["ka_passed"] = ka_gate(a.ka, a.bundle)["passed"]
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
    record = {"kind": "fiction-screen run record", "version": 3, "device": "cuda", "exit": a.exit, "step": a.step,
              "utc": utc()}
    try:
        manifest, msha = SB.load_manifest(root / "bundle")
        record.update(tag=manifest.get("tag"), round=manifest.get("round"), limit=manifest.get("limit"),
                      bundle_manifest_sha256=msha)
    except (OSError, ValueError, Refusal) as e:
        record["manifest_error"] = type(e).__name__
    for name, rel in STEP_RECORDS.items():
        record[name] = _read_json(root / rel)
    done = _read_json(root / GJ / "DONE.json")
    record["granite_job"] = {"done": {k: done.get(k) for k in ("exit", "step", "utc")} if isinstance(done, dict) else None,
                             "run_record_sha256": (sha256_file(root / GJ / "out/run-record.json")
                                                   if (root / GJ / "out/run-record.json").is_file() else None)}
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
    lead = root / GJ / "STEP"                                # the lead's Granite job's own step (venv ... run, done)
    granite_step = lead.read_text(errors="replace").strip()[:32] if lead.is_file() else None
    print(json.dumps({"started": (root / "STARTED.json").is_file(), "step": step, "granite_step": granite_step,
                      "done": done, "progress": last_status_line(root / "out/job.log")}, sort_keys=True))
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
    p = sub.add_parser("download")
    p.add_argument("--bundle", type=pathlib.Path, required=True)
    p.add_argument("--record", type=pathlib.Path, required=True)
    p = sub.add_parser("ka")
    p.add_argument("--bundle", type=pathlib.Path, required=True)
    p.add_argument("--granite-root", type=pathlib.Path, required=True, help="the lead's Granite job's root")
    p.add_argument("--granite-exit", type=int, required=True, help="the exit code of the lead's pod_run_granite.sh")
    p.add_argument("--record", type=pathlib.Path, required=True)
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
        return cmd_ka(a)
    if a.cmd == "granite":
        return cmd_granite(a, judge_factory)
    if a.cmd == "qwen":
        return cmd_qwen(a, guard_factory)
    try:
        return {"verify": cmd_verify, "download": cmd_download, "record": cmd_record, "status": cmd_status,
                "sums": cmd_sums}[a.cmd](a)
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return P.POD_EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
