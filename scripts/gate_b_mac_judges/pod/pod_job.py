"""The judge pod's job (runs on the pod; started by pod_run.sh, which judge_pod.py starts over ssh).

Written 8 October 2026 (19:50 UTC, clock checked); revised 8 October 2026 (20:51 UTC, clock checked): the run
record holds the tokenizer fingerprint, and the package check refuses sentencepiece or protobuf.

    pod_job.py verify   --bundle B                          the bundle's files, units and prepared sets (stdlib only)
    pod_job.py download --bundle B --record R               the pinned snapshot, no token, then every file's SHA-256
    pod_job.py run      --bundle B --cache C --record R [--limit N] [--device cuda]
    pod_job.py status   --root /workspace/judge             one JSON line: DONE.json, the step, the last progress
    pod_job.py sums     --root /workspace/judge             one JSON line: SHA-256 of each output file

run: verify_bundle (every file's SHA-256; COMPLETE.json/job.json against the units' records), the pinned packages
(transformers 4.56.2 and the others of pod_judge.POD_PACKAGES exactly; torch 2.8.0 by its public version; neither
sentencepiece nor protobuf), the snapshot's ten files by SHA-256, the tokenizer fingerprint (pod_judge.
tokenizer_fingerprint, into the run record), then for each prepared set: judging.check_units (as the Mac run), bank_prompts of the
bundle's copy of that prepared set (manifest.sha256 compared with the pin, exactly as the Mac path) and judging.run with
the CUDA judge (pod_judge.make_factory("cuda")) into the tool's cache (cache.Cache: keys complete_sha256, mode,
prompt_id, sample_index; labels, token counts, truncation flag, answer SHA-256, source "judged"). Resumable: an item
already in the cache is not judged again; a SIGTERM stops before the next item with exit 5. A resume cache in the
bundle (a previous pod run's fetched cache) seeds the cache when the cache file does not exist yet. The run record
(written at the end, whatever the outcome) holds the device, torch/CUDA/transformers versions, the GPU's name, the
judge's pins and revision, the bundle manifest's SHA-256, per-group counts, the cache's SHA-256 and the exit code.
Exit codes: 0 done (or nothing to judge), 2 refused, 5 stopped by SIGTERM (resumable), 1 any other error (its type is
recorded; the traceback stays in the pod's job.log). Prints counts, ids and hashes only; never prompt or answer text.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import signal
import sys
import traceback

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
for _p in (HERE.parent, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import bundle as bundle_mod  # noqa: E402
import judging  # noqa: E402
import pod_judge  # noqa: E402
from cache import Cache  # noqa: E402
from common import HARMBENCH, Refusal, bank_prompts, canonical_bytes, sha256_file  # noqa: E402
from judging import log, utc  # noqa: E402

MODES = ("greedy", "sampled")
EXIT_STOPPED = 5
STOP = {"flag": False}
TOKEN_VARS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
OFFLINE_VARS = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
OUTPUTS = ("out/harmbench-pod.jsonl", "out/run-record.json", "out/snapshot-check.json", "out/environment-pod.lock",
           "out/pip.log", "DONE.json")       # never out/job.log or run.log (tracebacks stay on the pod)
STATUS_EVENTS = frozenset({"bundle_verified", "packages", "snapshot_verified", "group_start", "judge_plan", "judge_loaded",
                           "progress", "cuda", "judge_end", "group_done", "run_record", "download_done"})
STATUS_FIELDS = ("event", "judged", "of", "sec_per_item", "eta_min", "cached", "todo", "seconds", "exit", "units",
                 "group", "files", "items", "stopped")
MIN_FREE_BYTES = 20 * 1024 ** 3


def write_atomic(path: pathlib.Path, data: bytes) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def item_counts(groups) -> dict:
    return {"units": sum(len(g.units) for g in groups),
            "greedy": sum(len(judging.load_items(u, "greedy")) for g in groups for u in g.units),
            "sampled": sum(len(judging.load_items(u, "sampled")) for g in groups for u in g.units)}


def cmd_verify(a) -> int:
    manifest = bundle_mod.verify_bundle(a.bundle)
    groups = bundle_mod.pod_groups(a.bundle, manifest)
    log(event="bundle_verified", files=len(manifest["files"]), group=len(groups), items=item_counts(groups),
        manifest_sha256=manifest["manifest_sha256"])
    return 0


def cmd_download(a) -> int:
    """The pinned snapshot from the Hub with no token (HF_HUB_OFFLINE unset), then every file's size and SHA-256."""
    import time
    for name in OFFLINE_VARS:
        if os.environ.get(name, "") not in ("", "0"):
            raise Refusal(f"{name} is set; the download step runs online")
    for name in TOKEN_VARS:
        if os.environ.get(name):
            raise Refusal(f"{name} is set; the classifier is public and is downloaded without a token")
    packages = pod_judge.require_pod_packages()
    cache_dir = pod_judge.SNAPSHOT.parents[2]                 # ~/.cache/huggingface/hub
    cache_dir.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(cache_dir).free
    if free < MIN_FREE_BYTES:
        raise Refusal(f"{free // 1024 ** 3} GiB free under {cache_dir}; at least {MIN_FREE_BYTES // 1024 ** 3} needed")
    from huggingface_hub import snapshot_download
    t = time.time()
    path = snapshot_download(repo_id=pod_judge.REPO, revision=pod_judge.REVISION,
                             allow_patterns=sorted(pod_judge.SNAPSHOT_FILES), token=False, cache_dir=str(cache_dir))
    if pathlib.Path(path).resolve() != pod_judge.SNAPSHOT.resolve():
        raise Refusal(f"the snapshot landed at {path}, not at {pod_judge.SNAPSHOT}")
    found = pod_judge.verify_snapshot()
    record = {"kind": "judge-pod snapshot check", "utc": utc(), "repo": pod_judge.REPO, "revision": pod_judge.REVISION,
              "token": False, "seconds": round(time.time() - t, 1), "files": found, "packages": packages}
    write_atomic(a.record, canonical_bytes(record))
    log(event="download_done", files=len(found), seconds=record["seconds"])
    return 0


def _seed_cache(root: pathlib.Path, manifest: dict, cache_path: pathlib.Path) -> int:
    resume = manifest.get("resume_cache")
    if resume is None or pathlib.Path(cache_path).exists():
        return 0
    src = pathlib.Path(root) / resume["path"]
    if sha256_file(src) != resume["sha256"]:
        raise Refusal("the resume cache does not have its recorded SHA-256")
    pathlib.Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, cache_path)
    return len(Cache(cache_path, HARMBENCH))


def cmd_run(a, judge_factory=None, env_probe=None) -> int:
    real = judge_factory is None
    STOP["flag"] = False
    previous = signal.signal(signal.SIGTERM, lambda *_: STOP.__setitem__("flag", True))
    record = {"kind": "judge-pod run record", "version": 1, "started_utc": utc(), "device": a.device,
              "judge": dict(HARMBENCH), "model_revision": pod_judge.REVISION, "pins": pod_judge.pins(), "groups": [],
              "refused": None, "error": None}
    code = 1
    try:
        manifest = bundle_mod.verify_bundle(a.bundle)
        record["bundle_manifest_sha256"] = manifest["manifest_sha256"]
        record["tag"] = manifest.get("tag")
        groups = bundle_mod.pod_groups(a.bundle, manifest)
        log(event="bundle_verified", files=len(manifest["files"]), group=len(groups), items=item_counts(groups))
        if real:
            record["packages"] = pod_judge.require_pod_packages()
            log(event="packages", **record["packages"])
            record["snapshot"] = pod_judge.verify_snapshot()
            log(event="snapshot_verified", files=len(record["snapshot"]))
            record["tokenizer_fingerprint"] = pod_judge.tokenizer_fingerprint()
            log(event="tokenizer", fingerprint=record["tokenizer_fingerprint"])
        record["resumed_records"] = _seed_cache(a.bundle, manifest, a.cache)
        cache = Cache(a.cache, HARMBENCH)
        factory = judge_factory or pod_judge.make_factory(a.device)
        remaining = a.limit if a.limit is not None else manifest.get("limit")
        stopped = False
        for i, g in enumerate(groups):
            log(event="group_start", group=i, units=len(g.units))
            counts = judging.check_units(g.units, MODES, g.expect, True, g.manifest_sha256)
            prompts = bank_prompts(g.prepared_dir, g.manifest_sha256)
            result = judging.run(g.units, MODES, prompts, factory, cache, limit=remaining,
                                 stop=lambda: STOP["flag"], gpu_guard=None)
            record["groups"].append({"prepared": g.name, "manifest_sha256": g.manifest_sha256,
                                     "dev_bank_sha256": g.dev_bank_sha256, "units": [u.label for u in g.units],
                                     "complete_sha256": [u.complete_sha256 for u in g.units], "counts": counts,
                                     "result": result})
            log(event="group_done", group=i, judged=result["judged"], cached=result["cached"], todo=result["todo"],
                stopped=result["stopped"])
            stopped = stopped or result["stopped"]
            if remaining is not None:
                remaining -= result["judged"]
            if stopped or (remaining is not None and remaining <= 0):
                break
        code = EXIT_STOPPED if stopped else 0
    except Refusal as e:
        record["refused"] = str(e)
        print(f"refused: {e}", file=sys.stderr)
        code = 2
    except BaseException as e:  # noqa: BLE001 - recorded, then the exit code says so
        record["error"] = type(e).__name__
        traceback.print_exc(file=sys.stderr)
        code = 1
    finally:
        signal.signal(signal.SIGTERM, previous)
        record["exit"] = code
        record["ended_utc"] = utc()
        try:
            record["environment"] = (env_probe or pod_judge.environment)(a.device) if (real or env_probe) else None
        except BaseException as e:  # noqa: BLE001
            record["environment"] = {"error": type(e).__name__}
        cache_path = pathlib.Path(a.cache)
        try:
            record["cache"] = ({"sha256": sha256_file(cache_path), "records": len(Cache(cache_path, HARMBENCH))}
                               if cache_path.exists() else None)
        except Refusal:
            record["cache"] = {"sha256": sha256_file(cache_path), "records": None}
        write_atomic(a.record, canonical_bytes(record))
        log(event="run_record", exit=code)
    return code


def last_status_line(path: pathlib.Path):
    """The last line of job.log that is a JSON object with a known event, reduced to the whitelisted count fields."""
    try:
        data = pathlib.Path(path).read_bytes()[-65536:]
    except OSError:
        return None
    for line in reversed(data.split(b"\n")):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict) and rec.get("event") in STATUS_EVENTS:
            return {k: rec[k] for k in STATUS_FIELDS if k in rec and isinstance(rec[k], (int, float, str, bool, dict))
                    and not (isinstance(rec[k], str) and len(rec[k]) > 64)}
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


def main(argv=None, judge_factory=None, env_probe=None) -> int:
    ap = argparse.ArgumentParser(description="The judge pod's job (counts only).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("verify", "download", "run"):
        p = sub.add_parser(name)
        p.add_argument("--bundle", type=pathlib.Path, required=True)
        if name in ("download", "run"):
            p.add_argument("--record", type=pathlib.Path, required=True)
        if name == "run":
            p.add_argument("--cache", type=pathlib.Path, required=True)
            p.add_argument("--limit", type=int, default=None)
            p.add_argument("--device", choices=pod_judge.DEVICES, default=pod_judge.POD_DEVICE)
    for name in ("status", "sums"):
        p = sub.add_parser(name)
        p.add_argument("--root", type=pathlib.Path, required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "verify":
            return cmd_verify(a)
        if a.cmd == "download":
            return cmd_download(a)
        if a.cmd == "status":
            return cmd_status(a)
        if a.cmd == "sums":
            return cmd_sums(a)
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    return cmd_run(a, judge_factory, env_probe)


if __name__ == "__main__":
    sys.exit(main())
