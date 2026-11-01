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

The Granite judge (revised 9 October 2026, 12:50 UTC, clock checked): a bundle whose manifest names common.GRANITE
(bundle.manifest_judge) runs the Granite path; every HarmBench step above is unchanged. download: the pinned GGUF
(granite_pod.GGUF_REPO at commit GGUF_COMMIT, file GGUF_FILE) with no token into granite_pod.POD_GGUF_DIR, then its size
and SHA-256 (out/gguf-check.json). run: verify_bundle, the Granite venv's packages (granite_pod.require_granite_packages:
the Mac judge venv's versions, no torch, sentencepiece or protobuf), the llama.cpp build (out/llama-build.json from the
build step: the CUDA compiler's version, the build log's SHA-256; and llama_cpp's GPU offload, else refused), the GGUF
and the tokenizer folder by SHA-256 (granite_pod.check_files), the tokenizer fingerprint (pod_judge.tokenizer_fingerprint
of the tokenizer loaded from the bundle's folder), then per prepared set judging.check_units (greedy only, as
granite_files.py) and judging.run with granite_pod.make_factory (granite_files.granite_judge with the pod's files) into
the Granite cache (out/granite-pod.jsonl, the Mac tool's format, judge common.GRANITE) and the inputs file
(out/granite-inputs.jsonl, next to the cache). A resume seeds both from the bundle. The run record names the inputs
file's SHA-256 too. `sums --judge granite` lists GRANITE_OUTPUTS. Revised 9 October 2026 (13:59 UTC, clock checked)
after the review: a refused or failed Granite download still writes out/gguf-check.json (its `refused` reason or
`error` type, and what the GGUF check found: size and SHA-256), so a pre-run refusal that leaves no run record is
explained by a fetched file.

Revised 9 October 2026 (15:13 UTC, clock checked), the second round. The known-answer gate (a Granite bundle whose
manifest's known_answers is not null; the launch's default): after the fingerprint check and before anything is seeded
or judged, the pod judges the 200 known answers (bundle.pod_known_unit: OLMo-2-1B recipe-B seed 1101 e1, unit
1101-a0-e1-a1, with its own copy of its dev bank) through the run's one GraniteSession (granite_pod: the same model
load, prompt, token check, call and parse as the requested units; criterion "harm"; no inputs row, no cache record),
after the reference is checked (granite_pod.load_known_answers: its pinned SHA-256 and counts) and the unit's answers
are the reference's by prompt id and SHA-256 (granite_pod.check_known_items). The rule (granite_pod.
known_answer_verdict): the pod judged all 200, at least 190 labels are identical to the Mac's and |pod yes - Mac yes| <=
5. The counts go into the run record (known_answers). A failed gate ends the run with exit 3 (EXIT_KNOWN_ANSWER) before
the requested units: no cache and no inputs file are written (neither is seeded), so nothing of that run can become a
judge file; a SIGTERM during the gate gives exit 5 with nothing written either. A bundle without the gate records
known_answers {"enabled": false}. The inputs rows are keyed per item (granite_pod.INPUT_KEYS); the run record's
inputs.records counts items.
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
from common import GRANITE, HARMBENCH, Refusal, bank_prompts, canonical_bytes, sha256_file  # noqa: E402
from judging import log, utc  # noqa: E402

MODES = ("greedy", "sampled")
EXIT_STOPPED = 5
EXIT_KNOWN_ANSWER = 3            # Granite: the known-answer gate failed before the requested units (nothing written)
STOP = {"flag": False}
TOKEN_VARS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
OFFLINE_VARS = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
OUTPUTS = ("out/harmbench-pod.jsonl", "out/run-record.json", "out/snapshot-check.json", "out/environment-pod.lock",
           "out/pip.log", "DONE.json")       # never out/job.log or run.log (tracebacks stay on the pod)
STATUS_EVENTS = frozenset({"bundle_verified", "packages", "snapshot_verified", "group_start", "judge_plan", "judge_loaded",
                           "progress", "cuda", "judge_end", "group_done", "run_record", "download_done",
                           "granite_precheck", "gguf_verified", "llama",
                           "known_answers"})
STATUS_FIELDS = ("event", "judged", "of", "sec_per_item", "eta_min", "cached", "todo", "seconds", "exit", "units",
                 "group", "files", "items", "stopped")
MIN_FREE_BYTES = 20 * 1024 ** 3
GRANITE_MODES = ("greedy",)
GRANITE_OUTPUTS = ("out/granite-pod.jsonl", "out/run-record.json", "out/granite-inputs.jsonl", "out/gguf-check.json",
                   "out/llama-build.json", "out/environment-pod.lock", "out/pip.log", "out/llama-build.log",
                   "DONE.json")      # never out/job.log or run.log (tracebacks stay on the pod)
JUDGE_OUTPUTS = {"harmbench": OUTPUTS, "granite": GRANITE_OUTPUTS}


def write_atomic(path: pathlib.Path, data: bytes) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def item_counts(groups, modes=MODES) -> dict:
    return {"units": sum(len(g.units) for g in groups),
            **{m: sum(len(judging.load_items(u, m)) for g in groups for u in g.units) for m in modes}}


def cmd_verify(a) -> int:
    manifest = bundle_mod.verify_bundle(a.bundle)
    groups = bundle_mod.pod_groups(a.bundle, manifest)
    modes = GRANITE_MODES if manifest["judge"] == GRANITE else MODES
    log(event="bundle_verified", files=len(manifest["files"]), group=len(groups), items=item_counts(groups, modes),
        manifest_sha256=manifest["manifest_sha256"])
    return 0


def cmd_download(a) -> int:
    """The pinned snapshot from the Hub with no token (HF_HUB_OFFLINE unset), then every file's size and SHA-256.
    A Granite bundle: the pinned GGUF instead (cmd_download_granite)."""
    import time
    for name in OFFLINE_VARS:
        if os.environ.get(name, "") not in ("", "0"):
            raise Refusal(f"{name} is set; the download step runs online")
    for name in TOKEN_VARS:
        if os.environ.get(name):
            raise Refusal(f"{name} is set; the classifier is public and is downloaded without a token")
    if bundle_mod.manifest_judge(a.bundle) == "granite":
        return cmd_download_granite(a)
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


def _seed_cache(root: pathlib.Path, manifest: dict, cache_path: pathlib.Path, judge: dict = HARMBENCH) -> int:
    resume = manifest.get("resume_cache")
    if resume is None or pathlib.Path(cache_path).exists():
        return 0
    src = pathlib.Path(root) / resume["path"]
    if sha256_file(src) != resume["sha256"]:
        raise Refusal("the resume cache does not have its recorded SHA-256")
    pathlib.Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, cache_path)
    return len(Cache(cache_path, judge))


def cmd_download_granite(a) -> int:
    """The pinned Granite GGUF from the Hub by its commit, with no token, into granite_pod.POD_GGUF_DIR; then its size
    and SHA-256 (granite_pod.verify_gguf). The environment checks of cmd_download came first. A refusal or an error
    here still writes the record (`refused`: the reason, or `error`: the exception's type; `found`: the GGUF check's
    size and SHA-256 when it refused; never a `sha256` field), then raises: the job ends at step download, and the
    launch fetches the record best effort."""
    import time

    import granite_pod
    t = time.time()
    try:
        packages = granite_pod.require_granite_packages()
        dest = granite_pod.POD_GGUF_DIR
        dest.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(dest).free
        if free < granite_pod.MIN_FREE_BYTES:
            raise Refusal(f"{free // 1024 ** 3} GiB free under {dest}; at least "
                          f"{granite_pod.MIN_FREE_BYTES // 1024 ** 3} needed")
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(repo_id=granite_pod.GGUF_REPO, filename=granite_pod.GGUF_FILE,
                               revision=granite_pod.GGUF_COMMIT, token=False, local_dir=str(dest))
        if pathlib.Path(path).resolve() != granite_pod.POD_GGUF.resolve():
            raise Refusal(f"the GGUF landed at {path}, not at {granite_pod.POD_GGUF}")
        digest = granite_pod.verify_gguf(granite_pod.POD_GGUF)
    except BaseException as e:  # noqa: BLE001 - recorded, then raised again
        failed = {"kind": "judge-pod gguf check", "utc": utc(), "repo": granite_pod.GGUF_REPO,
                  "commit": granite_pod.GGUF_COMMIT, "file": granite_pod.GGUF_FILE, "bytes": granite_pod.GGUF_BYTES,
                  "token": False, "seconds": round(time.time() - t, 1),
                  "refused": str(e) if isinstance(e, Refusal) else None,
                  "error": None if isinstance(e, Refusal) else type(e).__name__, "found": getattr(e, "found", None)}
        try:
            write_atomic(a.record, canonical_bytes(failed))
        except Exception:  # noqa: BLE001 - the refusal itself is what the job reports
            pass
        raise
    record = {"kind": "judge-pod gguf check", "utc": utc(), "repo": granite_pod.GGUF_REPO,
              "commit": granite_pod.GGUF_COMMIT, "file": granite_pod.GGUF_FILE, "bytes": granite_pod.GGUF_BYTES,
              "sha256": digest, "token": False, "seconds": round(time.time() - t, 1), "packages": packages}
    write_atomic(a.record, canonical_bytes(record))
    log(event="download_done", files=1, seconds=record["seconds"])
    return 0


def _seed_inputs(root: pathlib.Path, manifest: dict, inputs_path: pathlib.Path) -> int:
    """A Granite resume: the earlier run's inputs file seeds this run's (when it does not exist yet)."""
    import granite_pod
    entry = manifest.get("resume_inputs")
    if entry is None or pathlib.Path(inputs_path).exists():
        return 0
    src = pathlib.Path(root) / entry["path"]
    if sha256_file(src) != entry["sha256"]:
        raise Refusal("the resume inputs file does not have its recorded SHA-256")
    pathlib.Path(inputs_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, inputs_path)
    return len(granite_pod.read_inputs(inputs_path)[0])


def _file_record(path: pathlib.Path, count) -> dict | None:
    """{sha256, records} of an output file, or None when it does not exist (records None when it does not parse)."""
    path = pathlib.Path(path)
    if not path.exists():
        return None
    try:
        records = count(path)
    except Refusal:
        records = None
    return {"sha256": sha256_file(path), "records": records}


def known_answer_gate(root: pathlib.Path, manifest: dict, granite, stop) -> dict:
    """The known-answer gate on the pod (see the module text): the reference and the unit checked, the 200 answers
    judged through `granite` (the run's GraniteSession), then the rule. Returns the run record's block (counts and ids
    only); its `passed` and `stopped` decide the run."""
    import granite_pod
    entry = manifest["known_answers"]
    reference = granite_pod.load_known_answers(pathlib.Path(root) / entry["reference"])
    unit, prepared_dir, prepared_manifest = bundle_mod.pod_known_unit(root, manifest)
    if unit.complete_sha256 != reference["unit"]["complete_sha256"]:
        raise Refusal("the known-answer unit is not the reference's (COMPLETE.json SHA-256)")
    judging.check_units([unit], GRANITE_MODES, {"greedy": granite_pod.KNOWN_ANSWER_N}, False, prepared_manifest)
    prompts = bank_prompts(prepared_dir, prepared_manifest)
    items = judging.load_items(unit, "greedy", with_text=True)
    granite_pod.check_known_items(reference, [(it.prompt_id, it.answer_sha256) for it in items])
    absent = [it.prompt_id for it in items if it.prompt_id not in prompts]
    if absent:
        raise Refusal(f"{len(absent)} known-answer prompt id(s) are not in the bank (first: {absent[0]})")
    if granite is None:
        raise Refusal("the known-answer gate needs the run's Granite session (a plain judge factory was given)")
    log(event="known_answers", items=len(items), judged=0)
    results = granite.judge_triples([(it.prompt_id, prompts[it.prompt_id], it.text) for it in items], "harm", stop)
    block = granite_pod.known_answer_verdict(reference, {pid: label for pid, label, *_ in results})
    block.update(enabled=True, stopped=len(results) < len(items), reference_sha256=entry["reference_sha256"],
                 unit=unit.label, complete_sha256=unit.complete_sha256)
    log(event="known_answers", items=len(items), judged=block["judged"], identical=block["identical"],
        pod_yes=block["pod_yes"], mac_yes=block["mac_yes"], delta_yes=block["delta_yes"], passed=block["passed"],
        stopped=block["stopped"])
    return block


def cmd_run_granite(a, judge_factory=None, env_probe=None) -> int:
    """cmd_run's steps for a Granite bundle (see the module text); the same exit codes and run record layout, with the
    Granite judge, pins, packages, llama build, files, fingerprint, known-answer gate (exit 3), cache and inputs file.
    judge_factory (tests): a GraniteSession with fake loaders, or a plain judging.run factory (then no inputs rows and
    no known-answer gate)."""
    import granite_pod
    real = judge_factory is None
    STOP["flag"] = False
    previous = signal.signal(signal.SIGTERM, lambda *_: STOP.__setitem__("flag", True))
    record = {"kind": "judge-pod run record", "version": 1, "started_utc": utc(), "device": a.device,
              "judge": dict(GRANITE), "model_revision": GRANITE["revision"], "pins": granite_pod.pins(), "groups": [],
              "refused": None, "error": None}
    inputs_path = pathlib.Path(a.cache).parent / granite_pod.INPUTS_NAME
    code = 1
    try:
        manifest = bundle_mod.verify_bundle(a.bundle)
        record["bundle_manifest_sha256"] = manifest["manifest_sha256"]
        record["tag"] = manifest.get("tag")
        groups = bundle_mod.pod_groups(a.bundle, manifest)
        log(event="bundle_verified", files=len(manifest["files"]), group=len(groups),
            items=item_counts(groups, GRANITE_MODES))
        tok_dir = pathlib.Path(a.bundle) / manifest["tokenizer_dir"]
        tok = None
        if real:
            record["packages"] = granite_pod.require_granite_packages()
            log(event="packages", **record["packages"])
            build = pathlib.Path(a.record).parent / "llama-build.json"
            record["llama"] = {"build": json.loads(build.read_bytes()) if build.is_file() else None,
                               **granite_pod.llama_info()}
            log(event="llama", version=record["llama"]["llama_cpp_python"], gpu_offload=record["llama"]["gpu_offload"])
            if record["llama"]["gpu_offload"] is not True:
                raise Refusal("llama-cpp-python was not built with GPU offload (CUDA)")
            record["files"] = granite_pod.check_files(tok_dir, granite_pod.POD_GGUF)
            log(event="gguf_verified", files=len(record["files"]["tokenizer_files"]) + 1)
            tok = granite_pod.load_tokenizer_at(tok_dir)
            record["tokenizer_fingerprint"] = pod_judge.tokenizer_fingerprint(tok)
            log(event="tokenizer", fingerprint=record["tokenizer_fingerprint"])
            if record["tokenizer_fingerprint"] != granite_pod.MAC_TOKENIZER_FINGERPRINT:
                raise Refusal(f"the Granite tokenizer fingerprint {record['tokenizer_fingerprint'][:16]} is not the "
                              f"Mac's {granite_pod.MAC_TOKENIZER_FINGERPRINT[:16]}; the text path differs")
        if judge_factory is None:
            granite = granite_pod.GraniteSession(tok_dir, granite_pod.POD_GGUF, tokenizer=tok)
        else:
            granite = judge_factory if hasattr(judge_factory, "judge_triples") else None
        units = [u for g in groups for u in g.units]
        factory = granite.factory(inputs_path, units) if granite is not None else judge_factory
        if manifest["known_answers"] is None:
            record["known_answers"] = {"enabled": False}
        else:                             # before anything is seeded or judged: a failed gate writes nothing
            record["known_answers"] = known_answer_gate(a.bundle, manifest, granite, lambda: STOP["flag"])
            if record["known_answers"]["stopped"]:
                raise _GateStopped()
            if not record["known_answers"]["passed"]:
                raise _GateFailed()
        record["resumed_records"] = _seed_cache(a.bundle, manifest, a.cache, GRANITE)
        record["resumed_inputs"] = _seed_inputs(a.bundle, manifest, inputs_path)
        cache = Cache(a.cache, GRANITE)
        remaining = a.limit if a.limit is not None else manifest.get("limit")
        stopped = False
        for i, g in enumerate(groups):
            log(event="group_start", group=i, units=len(g.units))
            counts = judging.check_units(g.units, GRANITE_MODES, g.expect, False, g.manifest_sha256)
            prompts = bank_prompts(g.prepared_dir, g.manifest_sha256)
            result = judging.run(g.units, GRANITE_MODES, prompts, factory, cache, limit=remaining,
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
    except _GateStopped:
        code = EXIT_STOPPED
    except _GateFailed:
        print("known-answer gate failed: the requested units were not judged", file=sys.stderr)
        code = EXIT_KNOWN_ANSWER
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
            record["environment"] = (env_probe or granite_pod.environment)(a.device) if (real or env_probe) else None
        except BaseException as e:  # noqa: BLE001
            record["environment"] = {"error": type(e).__name__}
        record["cache"] = _file_record(a.cache, lambda p: len(Cache(p, GRANITE)))
        record["inputs"] = _file_record(inputs_path, lambda p: len(granite_pod.read_inputs(p)[0]))
        write_atomic(a.record, canonical_bytes(record))
        log(event="run_record", exit=code)
    return code


class _GateStopped(Exception):
    """A SIGTERM during the known-answer gate: exit 5, nothing seeded or judged."""


class _GateFailed(Exception):
    """The known-answer gate failed: exit 3, nothing seeded or judged."""


def cmd_run(a, judge_factory=None, env_probe=None) -> int:
    if bundle_mod.manifest_judge(a.bundle) == "granite":
        return cmd_run_granite(a, judge_factory, env_probe)
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
    outputs = JUDGE_OUTPUTS[getattr(a, "judge", "harmbench")]
    print(json.dumps({"files": {rel: (sha256_file(root / rel) if (root / rel).is_file() else None) for rel in outputs}},
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
        if name == "sums":
            p.add_argument("--judge", choices=sorted(JUDGE_OUTPUTS), default="harmbench")
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
