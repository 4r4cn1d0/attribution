"""The launcher of the fiction training-data screen on one RunPod A100 (runs on the Mac; Python 3.10+, stdlib).

Rebuilt 9 October 2026 (10:27 UTC, clock checked) by the Side Project's Opus worker from the lead's stopped partial
build. Nothing here was run against RunPod or the Hub by the builder. It reuses the reviewed judge-pod launcher
(scripts/gate_b_mac_judges/pod/, commits 6488274 and a4cc490) by import, unchanged: podhost.py IS the host layer (the
budget lock and guard, reconcile, create with the price check and the in-pod stop timer, orphan stops, ssh, send,
fetch, stop), and judge_pod.py's own helpers are imported (the one-shot signals, the log, the secret patterns,
fetch_one with its .part files and retries, the salvage time budget, safe_stop, the STOP-NOT-CONFIRMED and
CHECK-CONSOLE warnings). Every module of that launcher is pinned by SHA-256 as committed (screen_pins.LAUNCHER_PINS):
a changed file refuses (exit 2). The launch below follows judge_pod.launch step for step; what differs is the bundle,
the pod job (screen_run.sh) and its files, the verification, the "sp-" tag, the host records (in this kit's hosts/
folder, where every kit's budget.py looks) and exit code 8.

    ROOT=/Users/spiderishi/Coding/attribution; PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
    $PY -B screen_pod.py bundle --tag sp-T --round 1 [--out DIR] [--limit N]      # no network: build and check
    $PY -B screen_pod.py launch --tag sp-T --round 1 [--limit N]                 # one pod, then stopped
    $PY -B screen_pod.py launch --tag sp-T --round 2 --refill F --refill-sha256 H
    $PY -B screen_pod.py summarize --from <LAUNCH_DIR>/runs/sp-T [--out DIR]     # Mac only, no network
    $PY -B screen_pod.py final-reads [--final-dir DIR] [--screen-dir DIR]          # after sf_screen.py finalize

launch, in order (every step logged to <LAUNCH_DIR>/runs/T/screen-pod-log.jsonl; counts, ids, hashes, codes):
  0. the tag (sp-..., podhost's tag rule): an exclusive non-blocking flock on runs/T.lock for the whole launch; a
     second launch of the tag, or an existing folder runs/T, refuses (exit 2).
  1. the bundle (screen_bundle.py): the launcher's pins, the specification's and the rules' SHA-256, every input
     checked against its pin, the known-answer unit and the Mac labels, the engine code and its identity (pinned:
     e49a978c...; the record also names the engine files' SHA-256 and the files changed since commit 8801456), the
     secret scan, a deterministic tar.gz; rows-index.jsonl (ids and hashes of every row) and bundle-record.json
     (counts, cap, cost). A refusal creates nothing (exit 2).
  2. the cap: the smallest half hour of at least SETUP_UPPER_S + (200 + Granite calls) x --granite-s-per-call + Qwen3Guard
     rows x --qwen-s-per-row + MARGIN_S, at least 1 h and at most 6 h; --cap-hours sets another cap, higher or lower,
     but never below that planned upper time (and never above 6 h).
  3. under the lock every family-probe kit shares: reconcile, the budget guard (budget.py check CAP 1.85), create ONE
     pod (attribution-judge-<tag>; host records <LAUNCH_DIR>/hosts/<tag>/, which every kit's budget.py counts), the
     guard again with 0 extra hours. Codes as judge_pod.py: 3 refused guard, 4 refused create or price check, 7 a lost
     create reply with no pod listed (CHECK-CONSOLE).
  4. wait for SSH, check the GPU and the timer, send the bundle (SHA-256 checked on the pod), unpack and verify it
     there (screen_job.py verify), start screen_run.sh under nohup, poll every 30 s; 5 minutes before the cap the job
     steps get SIGTERM (they stop before the next row: exit 5).
  5. fetch: DONE.json, the run record, the known-answer record and labels, the Granite cache and the Qwen3Guard cache
     first, in that order (a failure raises), then the diagnostics best effort; each file through <file>.part and its
     pod-side SHA-256 (3 tries). Verify: the run record names this bundle, round, tag and exit; the known-answer labels
     are recounted on the Mac against the Mac labels and the rule applied again; every cached record names a row of
     this bundle with its hashes; coverage per source and criteria.
  6. ALWAYS (finally): judge_pod's stop discipline (one-shot signals, a reconcile cut short runs again, the orphan check
     after an interrupted create, the salvage of at most 300 s unless the first signal was SIGTERM or SIGQUIT, the stop
     confirmed EXITED or the timer shortened to 2 min and the stop retried, the exit code the salvaged files support).

Exit codes: 0 done (all fetched and verified, the known-answer check passed on the pod and again on the Mac, every row
of every source judged by each judge; with --limit, every selected row), pod stopped; 2 refused before any pod; 3 the
budget guard refused or could not run; 4 RunPod refused the create, or the price check failed; 5 the job was stopped
(cap or signal) and its partial caches fetched (resume with --resume-from <LAUNCH_DIR>/runs/<old tag> and a new tag); 6
any other failure (a pod that was created is stopped), including a known-answer step that broke before its verdict;
7 A STOP WAS NOT CONFIRMED or a create reply was lost (STOP-NOT-CONFIRMED / CHECK-CONSOLE): check the RunPod console
now; 8 THE KNOWN-ANSWER CHECK FAILED (all 200 judged and the rule failed, on the pod or when the Mac recounts its
labels): no row was screened after it, the pod was stopped, and nothing from the run is used; 9 THE KNOWN ANSWERS
PASSED BUT THE ROUND'S PROJECTED TIME PER GRANITE CALL (their seconds per answer x r, r = the round's mean tokens per
Granite call / the known answers' mean template tokens, both counted at bundle time) IS ABOVE THE CAP'S PLANNING TIME
(pod step ka, exit 3): no row was screened, the pod was stopped; decide the cap or the planning time before a
relaunch.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import pathlib
import re
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402
if str(P.JUDGE_POD_DIR) not in sys.path:
    sys.path.insert(0, str(P.JUDGE_POD_DIR))
import judge_pod as JP  # noqa: E402  (its helpers, imported unchanged)
import podhost  # noqa: E402
import screen_bundle as SB  # noqa: E402
import screen_job as SJ  # noqa: E402
import screen_rows as R  # noqa: E402
from common import Refusal, canonical_bytes, sha256_file  # noqa: E402

EXIT_OK, EXIT_REFUSED, EXIT_BUDGET, EXIT_CREATE = JP.EXIT_OK, JP.EXIT_REFUSED, JP.EXIT_BUDGET, JP.EXIT_CREATE
EXIT_STOPPED, EXIT_FAILED, EXIT_STOP_UNCONFIRMED = JP.EXIT_STOPPED, JP.EXIT_FAILED, JP.EXIT_STOP_UNCONFIRMED
EXIT_KA_FAILED, EXIT_TOO_SLOW = P.EXIT_KA_FAILED, P.EXIT_TOO_SLOW
POD_RUNS = P.POD_RUNS                     # replaced in tests
HOSTS = P.HOSTS                           # replaced in tests
REMOTE = P.REMOTE
TOOL = "bundle/tool"
RECORD_REL, KA_REL, KA_LABELS_REL = "out/run-record.json", "out/ka.json", "out/ka-labels.jsonl"
GRANITE_REL, QWEN_REL = "out/granite.jsonl", "out/qwen.jsonl"
REQUIRED = ("DONE.json", RECORD_REL)
FETCH_FIRST = ("DONE.json", RECORD_REL, KA_REL, KA_LABELS_REL, GRANITE_REL, QWEN_REL)   # in this order; failures raise
FETCH_BEST_EFFORT = tuple(rel for rel in SJ.OUTPUTS if rel not in FETCH_FIRST)          # diagnostics: skipped on failure
LOG_NAME, RESULT_NAME = "screen-pod-log.jsonl", "screen-pod-result.json"
STATUS_COMMAND = f"cd {REMOTE} && python3 -I {TOOL}/screen_job.py status --root {REMOTE}"
SUMS_COMMAND = f"cd {REMOTE} && python3 -I {TOOL}/screen_job.py sums --root {REMOTE}"
TERMINATE_COMMAND = "pkill -TERM -f '[s]creen_job.py (ka|granite|qwen) '; true"   # [s]: never matches this shell itself


# ---------------------------------------------------------------- pins, bundle, cap and resume (no network)

def tag_ok(tag) -> bool:
    return isinstance(tag, str) and tag.startswith(P.TAG_PREFIX) and bool(podhost.TAG_RE.match(tag))


def launcher_pins(base: pathlib.Path = None) -> dict:
    """The reused launcher's files as committed (their parity PASS covers them only so). A changed file refuses."""
    base = pathlib.Path(P.MAC_GATE_B if base is None else base)
    found = {rel: sha256_file(base / rel) for rel in P.LAUNCHER_PINS}
    changed = sorted(rel for rel, digest in found.items() if digest != P.LAUNCHER_PINS[rel])
    if changed:
        raise Refusal(f"the reused judge-pod launcher changed since it was pinned: {changed}; have this build "
                      "checked against it first")
    return found


def selected_count(n: int, limit: int | None) -> int:
    return n if limit is None else min(n, limit)


def work(planned: dict, limit: int | None, resume: dict | None) -> dict:
    """Rows and calls left for each judge (a resumed launch's cached records are not judged again)."""
    granite_rows = sum(selected_count(len(s["rows"]), limit) for name, s in planned["sources"].items()
                       if name in P.GRANITE_SOURCES)
    qwen_rows = sum(selected_count(len(s["rows"]), limit) for s in planned["sources"].values())
    resumed = {j: ((resume or {}).get(j) or {}).get("records", 0) for j in ("granite", "qwen")}
    return {"granite_rows": granite_rows, "granite_calls": max(0, 2 * granite_rows - resumed["granite"]),
            "qwen_rows": max(0, qwen_rows - resumed["qwen"]), "ka_calls": P.KA_N, "resumed": resumed}


def cap_hours_for(w: dict, given, granite_s: float, qwen_s: float) -> tuple[float, float]:
    """(cap hours, planned upper hours)."""
    need = (P.SETUP_UPPER_S + (w["ka_calls"] + w["granite_calls"]) * granite_s + w["qwen_rows"] * qwen_s
            + P.MARGIN_S) / 3600
    auto = max(1.0, math.ceil(need * 2) / 2)
    hours = auto if given is None else float(given)
    if hours < need:
        raise Refusal(f"--cap-hours {hours} is below the planned upper time {need:.2f} h")
    if hours > P.MAX_CAP_HOURS:
        raise Refusal(f"the cap {hours} h is above {P.MAX_CAP_HOURS} h; lower the planned times or split the round")
    return hours, need


def estimate(w: dict) -> dict:
    """The expected time and cost range (low, high) at the planning price; estimates, not measurements."""
    minutes = [round((s + (w["ka_calls"] + w["granite_calls"]) * g + w["qwen_rows"] * q) / 60, 1)
               for s, g, q in zip(P.EST_SETUP_S, P.EST_GRANITE_S, P.EST_QWEN_S)]
    return {"minutes": minutes, "usd": [round(m / 60 * podhost.PLANNING_PRICE, 2) for m in minutes]}


def inputs_of(planned: dict) -> dict:
    return {name: s["sha256"] for name, s in planned["sources"].items()}


def resume_from(prev: pathlib.Path, planned: dict) -> dict:
    """An earlier launch of the same round and inputs: its fetched caches, by the SHA-256 its result recorded, after
    its known-answer check passed; every record must name a row of this plan with its hashes."""
    prev = pathlib.Path(prev)
    result = json.loads((prev / RESULT_NAME).read_bytes())
    if result.get("round") != planned["round"] or result.get("inputs") != inputs_of(planned):
        raise Refusal(f"--resume-from {prev.name}: another round or other inputs")
    if not ((result.get("verification") or {}).get("ka") or {}).get("passed"):
        raise Refusal(f"--resume-from {prev.name}: its known-answer check did not pass")
    index = {row.row_id: row for s in planned["sources"].values() for row in s["rows"]}
    out = {"from_tag": result.get("tag")}
    for judge, rel, check, key in (("granite", GRANITE_REL, R.check_granite, R.granite_key),
                                   ("qwen", QWEN_REL, R.check_qwen, R.qwen_key)):
        digest, path = (result.get("fetched") or {}).get(rel), prev / "fetched" / rel
        if not digest or not path.is_file():
            continue
        if sha256_file(path) != digest:
            raise Refusal(f"--resume-from {prev.name}: {rel} does not have the SHA-256 its result records")
        cache = R.JsonlCache(path, check, key)
        for entry in cache.entries.values():
            row = index.get(entry["row_id"])
            if row is None:
                raise Refusal(f"--resume-from {prev.name}: a cached record names a row outside this plan")
            R.check_against(entry, row, f"--resume-from {prev.name}")
        out[judge] = {"path": path, "sha256": digest, "records": len(cache)}
    if "granite" not in out and "qwen" not in out:
        raise Refusal(f"--resume-from {prev.name}: no fetched cache to resume from")
    return out


def build(a, folder: pathlib.Path) -> dict:
    launcher = launcher_pins()
    planned = SB.plan(a.round, a.refill, a.refill_sha256)
    resume = resume_from(a.resume_from, planned) if a.resume_from else None
    w = work(planned, a.limit, resume)
    if w["granite_calls"] + w["qwen_rows"] <= 0:
        raise Refusal(f"nothing is left to screen (--limit {a.limit}, resumed {w['resumed']})")
    cap, need = cap_hours_for(w, a.cap_hours, a.granite_s_per_call, a.qwen_s_per_row)
    planned["granite_tokens"] = SB.granite_token_means(planned, a.limit)     # the speed stop's ratio r (counts only)
    engine_files = SB.engine_files()
    identity = SB.engine_identity(engine_files)              # refuses unless the pinned engine code identity
    engine = {"files": engine_files, "code_sha256": identity["code_sha256"], **SB.engine_provenance()}
    tar = folder / "bundle.tar.gz"
    with tempfile.TemporaryDirectory(dir=folder, prefix="stage-") as tmp:
        manifest = SB.stage_bundle(planned, pathlib.Path(tmp) / "bundle", a.tag, a.limit, engine, SB.pins_record(),
                                   resume, JP.SECRET_PATTERNS)
        manifest_sha = sha256_file(pathlib.Path(tmp) / "bundle" / SB.MANIFEST_NAME)
        import bundle as gate_b_bundle                    # gate_b_mac_judges/pod/bundle.py: the deterministic tar
        tar_sha = gate_b_bundle.write_tar(pathlib.Path(tmp) / "bundle", tar)
    rows = [row for s in planned["sources"].values() for row in s["rows"]]
    (folder / "rows-index.jsonl").write_bytes(b"".join(json.dumps(R.index_entry(row), sort_keys=True).encode() + b"\n"
                                                       for row in rows))
    index_sha = sha256_file(folder / "rows-index.jsonl")
    ka = planned["ka"]
    record = {"kind": "fiction-screen bundle record", "tag": a.tag, "round": a.round, "limit": a.limit,
              "bundle_sha256": tar_sha, "manifest_sha256": manifest_sha, "bundle_bytes": tar.stat().st_size,
              "files": len(manifest["files"]), "inputs": inputs_of(planned),
              "rows": {name: len(s["rows"]) for name, s in planned["sources"].items()},
              "rows_index_sha256": index_sha, "work": w, "documents": planned["documents"],
              "granite_tokens": planned["granite_tokens"],
              "refill": planned["refill"], "launcher_sha256": launcher,
              "known_answer": {"unit": ka["unit"].name, "complete_sha256": ka["unit"].complete_sha256,
                               "n": len(ka["labels"]), "mac_yes": sum(v == "Yes" for v in ka["labels"].values())},
              "engine": {**{k: manifest["engine"][k] for k in ("code_sha256", "git_commit", "recipe_sha256", "files")},
                         **{k: identity[k] for k in ("code_sha256_pinned", "files_sha256", "base_commit",
                                                     "changed_since_base")}},
              "planning_s": {"setup": P.SETUP_UPPER_S, "granite_per_call": a.granite_s_per_call,
                             "qwen_per_row": a.qwen_s_per_row, "margin": P.MARGIN_S},
              "planned_upper_hours": round(need, 2), "cap_hours": cap, "planning_price": podhost.PLANNING_PRICE,
              "cost_upper_usd": round(cap * podhost.PLANNING_PRICE, 2), "estimate": estimate(w),
              "resume": None if resume is None else {"from_tag": resume["from_tag"],
                                                     **{j: {"sha256": resume[j]["sha256"],
                                                            "records": resume[j]["records"]}
                                                        for j in ("granite", "qwen") if j in resume}}}
    (folder / "bundle-record.json").write_bytes(canonical_bytes(record))
    index = {row.row_id: R.index_entry(row) for row in rows}
    selection = {name: [row.row_id for row in s["rows"][:selected_count(len(s["rows"]), a.limit)]]
                 for name, s in planned["sources"].items()}
    return {"manifest": manifest, "manifest_sha256": manifest_sha, "tar": tar, "tar_sha256": tar_sha, "cap_hours": cap,
            "record": record, "index": index, "selection": selection, "round": a.round, "tag": a.tag,
            "ka_labels": dict(ka["labels"]), "ka_answer_sha256": dict(ka["answer_sha256"])}


# ---------------------------------------------------------------- remote steps (through host.run)

def unpack_command(tar_sha256: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", tar_sha256):
        raise Refusal("bad bundle SHA-256")
    return ("set -e\n"
            f"cd {REMOTE} && python3 -I - <<'PY'\n"
            "import hashlib, pathlib, tarfile\n"
            f"p = pathlib.Path('bundle.tar.gz'); assert hashlib.sha256(p.read_bytes()).hexdigest() == '{tar_sha256}'\n"
            "assert not pathlib.Path('bundle').exists(), 'bundle exists'\n"
            "with tarfile.open(p) as t: t.extractall('.', filter='data')\n"
            "PY\n"
            f"cd {REMOTE} && python3 -I {TOOL}/screen_job.py verify --bundle bundle")


def start_command() -> str:
    return (f"cd {REMOTE} || exit 1\n"
            "test ! -e STARTED.json || exit 1\n"
            "mkdir -p out\n"
            f"nohup bash {TOOL}/screen_run.sh > run.log 2>&1 < /dev/null &\n"
            "sleep 5\n"
            f"test -f {REMOTE}/STARTED.json")


def whitelist(entry) -> dict:
    """The status fields of one pod log line, scalars only, short strings only. The line's own "step" (the job step it
    reports on) becomes "job_step": these fields go into the launcher's log as keywords, whose own `step` argument
    must not be passed twice (the lead's partial build raised TypeError at the first poll)."""
    if not isinstance(entry, dict):
        return {}
    return {("job_step" if k == "step" else k): entry[k] for k in SJ.STATUS_FIELDS
            if k in entry and isinstance(entry[k], (int, float, str, bool))
            and not (isinstance(entry[k], str) and len(entry[k]) > 64)}


def parse_status(stdout: str):
    """The status line's started flag, step, DONE.json and progress (whitelisted)."""
    st = JP.last_json(stdout)
    if st is None or "done" not in st:
        return None
    done = st.get("done")
    return {"started": bool(st.get("started")), "step": str(st.get("step"))[:32] if st.get("step") else None,
            "done": None if not isinstance(done, dict) else {"exit": done.get("exit"), "step": done.get("step")},
            "progress": whitelist(st.get("progress"))}


def poll(host, deadline: float, log, clock=time.time, sleep=time.sleep):
    """DONE.json's {exit, step}, or None when the deadline passed first (judge_pod.poll with this job's status)."""
    failures, last, warned = 0, None, False
    while True:
        code, stdout = host.run(STATUS_COMMAND, timeout=90)
        st = parse_status(stdout) if code == 0 else None
        if st is None:
            failures += 1
            log("status-unreadable", exit=code, failures=failures)
            if failures > JP.MAX_POLL_FAILURES:
                raise podhost.HostError(f"the job status was unreadable {failures} times in a row")
        else:
            failures = 0
            seen = (st["step"], json.dumps(st["progress"], sort_keys=True))
            if seen != last:
                log("progress", pod_step=st["step"], **st["progress"])
                last = seen
            eta = st["progress"].get("eta_min")
            if not warned and isinstance(eta, (int, float)) and clock() + eta * 60 > deadline:
                log("cap-risk", eta_min=eta, minutes_to_deadline=round((deadline - clock()) / 60, 1))
                warned = True
            if st["done"] is not None:
                return st["done"]
        if clock() >= deadline:
            return None
        sleep(JP.POLL_S)


def fetch_outputs(host, folder: pathlib.Path, log, fetched: dict | None = None, sleep=time.sleep, deadline=None,
                  clock=time.time) -> dict:
    """judge_pod.fetch_outputs with this job's files: FETCH_FIRST in order (a failure raises), then the diagnostics
    best effort; each file through JP.fetch_one (.part, the pod's SHA-256, 3 tries); `fetched` gains each file as soon
    as it is in place; a file already in place with the pod's SHA-256 is kept."""
    fetched = {} if fetched is None else fetched
    code, stdout = host.run(SUMS_COMMAND, timeout=JP.time_left(deadline, clock, 180))
    sums = (JP.last_json(stdout) or {}).get("files") if code == 0 else None
    if not isinstance(sums, dict):
        raise podhost.HostError(f"the output sums could not be read (exit {code})")
    try:
        for rel in FETCH_FIRST + FETCH_BEST_EFFORT:
            try:
                digest = sums.get(rel)
                if digest is None:
                    continue
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise podhost.HostError(f"{rel}: the pod reported no SHA-256")
                local = folder / "fetched" / rel
                if local.exists():
                    if sha256_file(local) != digest:
                        raise Refusal(f"{rel}: the file in place does not have the pod's SHA-256 {digest[:16]}")
                    fetched[rel] = digest
                    continue
                JP.fetch_one(host, rel, local, digest, log, sleep, deadline, clock)
                fetched[rel] = digest
            except podhost.HostError as e:
                if rel not in FETCH_BEST_EFFORT:
                    raise
                log("fetch-skipped", file=rel, error=type(e).__name__)
    finally:
        log("fetched", files=dict(fetched))
    missing = [rel for rel in REQUIRED if rel not in fetched]
    if missing:
        raise podhost.HostError(f"the pod has no {missing}")
    return fetched


# ---------------------------------------------------------------- verification (Mac, fetched files only)

def verify_ka(folder: pathlib.Path, built: dict, fetched: dict) -> dict:
    """The known-answer labels recounted against the Mac labels and the rule applied again; the pod's own counts must
    equal the recount. `complete`: the check ran to its verdict (all 200 judged, not stopped, no refusal or error)."""
    absent = {"present": False, "complete": False, "passed": False, "passed_pod": False, "passed_mac": False,
              "counts": None, "stopped": None}
    if KA_REL not in fetched:
        return absent
    pod_record = json.loads((folder / "fetched" / KA_REL).read_bytes())
    pod_labels: dict = {}
    if KA_LABELS_REL in fetched:
        for line in (folder / "fetched" / KA_LABELS_REL).read_bytes().split(b"\n"):
            if not line.strip():
                continue
            entry = json.loads(line)
            pid = entry.get("prompt_id")
            if (pid not in built["ka_labels"] or pid in pod_labels or entry.get("pod") not in P.LABELS
                    or entry.get("answer_sha256") != built["ka_answer_sha256"][pid]
                    or entry.get("mac") != built["ka_labels"][pid]):
                raise Refusal("a fetched known-answer label names another item, answer or Mac label")
            pod_labels[pid] = entry["pod"]
    counts = R.ka_counts([(built["ka_labels"][pid], pod_labels.get(pid)) for pid in sorted(built["ka_labels"])])
    passed_mac, passed_pod = R.ka_passed(counts), pod_record.get("passed") is True
    if pod_record.get("counts") is not None and pod_record.get("counts") != counts:
        raise Refusal("the pod's known-answer counts differ from the recount of its fetched labels")
    complete = (R.ka_complete(counts) and pod_record.get("counts") == counts and pod_record.get("stopped") is False
                and pod_record.get("refused") is None and pod_record.get("error") is None)
    return {"present": True, "complete": complete, "passed": passed_mac and passed_pod, "passed_pod": passed_pod,
            "passed_mac": passed_mac, "counts": counts, "stopped": pod_record.get("stopped"),
            "seconds_per_item": pod_record.get("seconds_per_item"), "refused": pod_record.get("refused") is not None,
            "error": pod_record.get("error"), "too_slow": pod_record.get("too_slow"),
            "speed": pod_record.get("speed")}


def verify_cache(folder: pathlib.Path, built: dict, rel: str, judge: str) -> dict:
    check, key = (R.check_granite, R.granite_key) if judge == "granite" else (R.check_qwen, R.qwen_key)
    cache = R.JsonlCache(folder / "fetched" / rel, check, key)
    sources = [s for s in built["selection"] if judge == "qwen" or s in P.GRANITE_SOURCES]
    expected = {(rid, c) if judge == "granite" else (rid,)
                for s in sources for rid in built["selection"][s] for c in (P.CRITERIA if judge == "granite" else (0,))}
    for k, entry in cache.entries.items():
        if k not in expected:
            raise Refusal(f"the fetched {judge} cache holds a record of a row this launch did not select")
        ref = built["index"][entry["row_id"]]
        if (entry["source"], entry["line"], entry["response_sha256"], entry["user_sha256"]) != (
                ref["source"], ref["line"], ref["response_sha256"], ref["user_sha256"]):
            raise Refusal(f"the fetched {judge} record of {entry['row_id']} names other hashes")
    covered = {s: sum(1 for k in expected if built["index"][k[0]]["source"] == s and k in cache.entries)
               for s in sources}
    return {"records": len(cache), "expected": len(expected), "complete": expected <= set(cache.entries),
            "covered": covered, "undecodable_lines": cache.undecodable}


def verify_outputs(folder: pathlib.Path, built: dict, done: dict, fetched: dict) -> dict:
    record = json.loads((folder / "fetched" / RECORD_REL).read_bytes())
    rec_ok = (record.get("kind") == "fiction-screen run record" and record.get("device") == "cuda"
              and record.get("bundle_manifest_sha256") == built["manifest_sha256"] and record.get("exit") == done.get("exit")
              and record.get("round") == built["round"] and record.get("tag") == built["tag"])
    if not rec_ok:
        raise Refusal("the fetched run record does not match this launch (kind, device, bundle, round, tag or exit)")
    llama = record.get("llama") or {}
    summary = {"pod_exit": record.get("exit"), "pod_step": record.get("step"),
               "llama": {k: llama.get(k) for k in ("version", "gpu_offload", "cmake_args", "nvcc", "nvcc_source",
                                                   "build_log_sha256")},
               "ka": verify_ka(folder, built, fetched), "granite": None, "qwen": None, "complete": False}
    if GRANITE_REL in fetched:
        summary["granite"] = verify_cache(folder, built, GRANITE_REL, "granite")
    if QWEN_REL in fetched:
        summary["qwen"] = verify_cache(folder, built, QWEN_REL, "qwen")
    summary["complete"] = bool(summary["ka"]["passed"] and summary["granite"] and summary["granite"]["complete"]
                               and summary["qwen"] and summary["qwen"]["complete"])
    return summary


def ka_failed(done: dict, ka: dict) -> bool:
    """Exit 8: the pod's ka step said the rule failed (exit 4), or the check ran to its verdict and failed on the pod
    or in the Mac's recount. A ka step that broke, was refused or was stopped before its verdict is not a failed check
    (exit 6 or 5): nothing was compared."""
    return (done.get("exit") == P.POD_EXIT_KA_FAILED and done.get("step") == "ka") or (
        ka["present"] and ka["complete"] and not ka["passed"])


def verdict(folder: pathlib.Path, built: dict, done: dict, result: dict, log) -> int:
    """The exit code the fetched and verified files support: 8 when the known-answer check failed (on the pod, or in
    the Mac's recount); 9 when it passed but ran slower than the cap's planning time per Granite call (nothing
    screened); 0 only when it passed and both judges covered every selected row; 5 a stopped job; else 6."""
    v = verify_outputs(folder, built, done, result["fetched"])
    result["verification"] = v
    log("verified", complete=v["complete"], pod_exit=v["pod_exit"], pod_step=v["pod_step"], llama=v["llama"],
        ka={k: v["ka"].get(k) for k in ("present", "complete", "passed", "passed_pod", "passed_mac", "counts",
                                        "seconds_per_item", "refused", "error", "too_slow", "speed")},
        granite=v["granite"], qwen=v["qwen"])
    if ka_failed(done, v["ka"]):
        log("KNOWN-ANSWER-CHECK-FAILED", passed_pod=v["ka"]["passed_pod"], passed_mac=v["ka"]["passed_mac"],
            counts=v["ka"]["counts"], action="nothing from this run is used")
        return EXIT_KA_FAILED
    if (done.get("exit") == P.POD_EXIT_TOO_SLOW and done.get("step") == "ka" and v["ka"]["passed"]
            and v["ka"].get("too_slow") is True):
        log("KNOWN-ANSWERS-TOO-SLOW", seconds_per_item=v["ka"].get("seconds_per_item"), speed=v["ka"].get("speed"),
            planned_s_per_call=P.GRANITE_S_PER_CALL,
            action="no row was screened; the round would not fit its cap: decide the cap or the planning time first")
        return EXIT_TOO_SLOW
    if done.get("exit") == 0:
        return EXIT_OK if v["complete"] else EXIT_FAILED
    if done.get("exit") == P.POD_EXIT_STOPPED:
        return EXIT_STOPPED
    return EXIT_FAILED


def salvaged_code(folder: pathlib.Path, built: dict, result: dict, log):
    if any(rel not in result["fetched"] for rel in REQUIRED):
        return None
    done_file = json.loads((folder / "fetched" / "DONE.json").read_bytes())
    done = {"exit": done_file.get("exit"), "step": done_file.get("step")} if isinstance(done_file, dict) else {}
    return verdict(folder, built, done, result, log)


def salvage(host, folder: pathlib.Path, log, fetched: dict, sleep=time.sleep, clock=time.time) -> None:
    """judge_pod.salvage with this job's commands: SIGTERM, a wait for DONE.json, the fetch; SALVAGE_BUDGET_S in all."""
    deadline = clock() + JP.SALVAGE_BUDGET_S
    host.run(TERMINATE_COMMAND, timeout=JP.time_left(deadline, clock, 60))
    wait_end = min(clock() + JP.SALVAGE_WAIT_S, deadline)
    while clock() < wait_end:
        code, stdout = host.run(STATUS_COMMAND, timeout=JP.time_left(deadline, clock, 60))
        st = parse_status(stdout) if code == 0 else None
        if st is not None and st["done"] is not None:
            break
        sleep(max(0.0, min(10.0, wait_end - clock())))
    fetch_outputs(host, folder, log, fetched, sleep, deadline, clock)
    log("salvaged", files=sorted(fetched))


# ---------------------------------------------------------------- the launch (judge_pod's structure)

def _run(a, host, built: dict, folder: pathlib.Path, result: dict, ctx: dict, log, clock, sleep) -> int:
    with host.budget_lock():
        ctx["phase"] = "reconcile"
        try:
            host.reconcile()
        except podhost.HostError:
            ctx["phase"] = "guard"
            raise
        ctx["phase"] = "guard"
        allowed, summary = host.budget_check(built["cap_hours"], podhost.PLANNING_PRICE)
        log("budget-guard", allowed=allowed, hours=built["cap_hours"], price=podhost.PLANNING_PRICE, guard=summary)
        if not allowed:
            return EXIT_BUDGET
        ctx["phase"] = "create"
        pod = host.create(built["cap_hours"])
        ctx["phase"] = "after-create"
        result.update(pod_id=pod.get("id"), pod_name=pod.get("name"), cap_stop_utc=pod.get("cap_stop_utc"))
        log("created", pod_id=pod.get("id"), name=pod.get("name"), cost_per_hr=pod.get("costPerHr"),
            cap_stop_utc=pod.get("cap_stop_utc"))
        allowed, summary = host.budget_check(0.0, podhost.PLANNING_PRICE)
        log("budget-guard-after-create", allowed=allowed, hours=0.0, cost_per_hr=pod.get("costPerHr"), guard=summary)
        if not allowed:
            return EXIT_BUDGET
    deadline = JP._utc_epoch(pod["cap_stop_utc"]) - JP.FINISH_MARGIN_S
    host.wait_ssh(JP.SSH_WAIT_S)
    log("ssh-ready")
    log("checked", **host.check())
    host.send(built["tar"], "bundle.tar.gz", built["tar_sha256"])
    log("bundle-sent", sha256=built["tar_sha256"])
    rc, stdout = host.run(unpack_command(built["tar_sha256"]), timeout=600)
    if rc:
        raise podhost.HostError(f"unpacking or verifying the bundle on the pod failed (exit {rc})")
    log("bundle-verified-on-pod", **whitelist(JP.last_json(stdout)))
    rc, _ = host.run(start_command(), timeout=120)
    if rc:
        raise podhost.HostError(f"the job did not start (exit {rc})")
    ctx["started"] = True
    log("job-started")
    done = poll(host, deadline, log, clock, sleep)
    if done is None:
        log("deadline", note="SIGTERM to the job steps before the cap")
        host.run(TERMINATE_COMMAND, timeout=60)
        done = poll(host, clock() + JP.SALVAGE_WAIT_S, log, clock, sleep)
        if done is None:
            raise podhost.HostError("the job did not end after SIGTERM")
    log("job-done", exit=done.get("exit"), pod_step=done.get("step"))
    fetch_outputs(host, folder, log, result["fetched"], sleep)
    ctx["fetch_complete"] = True
    return verdict(folder, built, done, result, log)


def finish(a, host, built: dict, folder: pathlib.Path, result: dict, ctx: dict, log, clock, sleep, sig) -> None:
    """judge_pod.finish with this job's salvage and verdict: signals ignored first, every step on its own guard."""
    sig.ignore()
    if ctx["phase"] == "reconcile":
        try:
            host.reconcile()
            log("reconcile-retry", ok=True)
        except podhost.StopUnconfirmed as e:
            ctx["code"] = EXIT_STOP_UNCONFIRMED
            log("reconcile-retry", error=type(e).__name__)
            JP._not_confirmed(log, e.pod_ids, e.names or [JP._name(host)])
        except podhost.HostError as e:
            log("reconcile-retry", error=type(e).__name__, detail=str(e))
        except BaseException as e:  # noqa: BLE001
            log("reconcile-retry", error=type(e).__name__)
    if (not getattr(host, "pod_id", None) and ctx["phase"] == "create" and not getattr(host, "orphan_check_done", False)
            and getattr(host, "create_sent", True)):
        try:
            stopped = host.stop_orphans("the create did not return a tracked pod")
            log("orphan-check", stopped=stopped)
            if not stopped:
                ctx["code"] = EXIT_STOP_UNCONFIRMED
                JP._check_console(log, JP._name(host), getattr(host, "cap_stop_utc", None))
        except BaseException as e:  # noqa: BLE001
            ctx["code"] = EXIT_STOP_UNCONFIRMED
            log("orphan-check-failed", error=type(e).__name__,
                detail=str(e) if isinstance(e, podhost.HostError) else None)
            JP._not_confirmed(log, getattr(e, "pod_ids", None) or [], getattr(e, "names", None) or [JP._name(host)])
    if getattr(host, "pod_id", None) and ctx["started"] and not ctx["fetch_complete"]:
        if sig.received in JP.SKIP_SALVAGE_SIGNALS:
            log("salvage-skipped", signal=int(sig.received))
        else:
            try:
                salvage(host, folder, log, result["fetched"], sleep, clock)
                ctx["salvaged"] = True
            except BaseException as e:  # noqa: BLE001
                log("salvage-failed", error=type(e).__name__)
    if getattr(host, "pod_id", None):
        stop = JP.safe_stop(host, log)
        log("stop", **stop)
        if not stop.get("confirmed"):
            try:
                shortened = host.shorten_timer(120, JP.HERE / "extend_cap.py")
            except BaseException as e:  # noqa: BLE001
                shortened = False
                log("shorten-timer-failed", error=type(e).__name__)
            stop = JP.safe_stop(host, log)
            log("stop-retry", shortened=shortened, **stop)
        result["stop"] = stop
    if ctx["salvaged"] and ctx["code"] == EXIT_FAILED:
        try:
            code = salvaged_code(folder, built, result, log)
            if code is not None:
                ctx["code"] = code
        except BaseException as e:  # noqa: BLE001
            log("salvage-verify-failed", error=type(e).__name__, detail=str(e) if isinstance(e, Refusal) else None)
    if result.get("stop") is not None and not result["stop"].get("confirmed"):
        ctx["code"] = EXIT_STOP_UNCONFIRMED
        JP._not_confirmed(log, [getattr(host, "pod_id", None)], [result.get("pod_name") or JP._name(host)])
    result["exit"] = ctx["code"]
    try:
        (folder / RESULT_NAME).write_bytes(canonical_bytes(result))
    except BaseException as e:  # noqa: BLE001
        log("result-not-written", error=type(e).__name__)
    log("end", exit=ctx["code"])
    ctx["finished"] = True


def launch(a, host=None, clock=time.time, sleep=time.sleep, signals: bool = True) -> int:
    if not tag_ok(a.tag):
        JP.say(f"refused: --tag must start with {P.TAG_PREFIX} and be 2 to 40 characters of a-z, 0-9 and '-'")
        return EXIT_REFUSED
    root = pathlib.Path(POD_RUNS)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / f"{a.tag}.lock"
    with open(lock_path, "a") as lock_handle:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            JP.say(f"refused: another launch holds {lock_path} (one launch per tag at a time)")
            return EXIT_REFUSED
        try:
            return _launch_locked(a, root / a.tag, host, clock, sleep, signals)
        finally:
            fcntl.flock(lock_handle, fcntl.LOCK_UN)


def _launch_locked(a, folder: pathlib.Path, host, clock, sleep, signals: bool) -> int:
    if folder.exists():
        JP.say(f"refused: {folder} exists; every launch has a new tag")
        return EXIT_REFUSED
    folder.mkdir(parents=True)
    log = JP.RunLog(folder / LOG_NAME, a.tag)
    log("start", round=a.round, limit=a.limit, cap_hours=a.cap_hours)
    try:
        built = build(a, folder)
    except (Refusal, OSError, ValueError, KeyError) as e:
        log("refused", error=type(e).__name__, reason=str(e))
        return EXIT_REFUSED
    log("bundle", **{k: built["record"][k] for k in ("bundle_sha256", "manifest_sha256", "bundle_bytes", "files",
                                                     "inputs", "rows", "work", "cap_hours", "planned_upper_hours",
                                                     "planning_price", "cost_upper_usd", "estimate", "resume")})
    if host is None:
        if not os.environ.get("RUNPOD_OPERATOR_API_KEY", "").strip():
            log("refused", reason="RUNPOD_OPERATOR_API_KEY is not set (source the secrets file first)")
            return EXIT_REFUSED
        host = podhost.RunPodHost(a.tag, records=pathlib.Path(HOSTS) / a.tag, kit=a.ssh_kit,
                                  budget_kit=a.budget_kit, remote_root=REMOTE)
    result = {"kind": "fiction-screen pod result", "version": 2, "tag": a.tag, "round": a.round, "limit": a.limit,
              "inputs": built["record"]["inputs"], "rows_index_sha256": built["record"]["rows_index_sha256"],
              "bundle_sha256": built["tar_sha256"], "manifest_sha256": built["manifest_sha256"],
              "cap_hours": built["cap_hours"], "planning_price": podhost.PLANNING_PRICE,
              "host_records": str(getattr(host, "records", "") or ""), "budget_kit": str(a.budget_kit),
              "pod_id": None, "pod_name": None, "fetched": {}, "verification": None, "stop": None, "exit": None}
    ctx = {"phase": "guard", "started": False, "fetch_complete": False, "salvaged": False, "finished": False,
           "code": EXIT_FAILED}
    sig = JP.OneShotSignals(describe=lambda: (getattr(host, "pod_id", None) or result.get("pod_id"),
                                              getattr(host, "cap_stop_utc", None) or result.get("cap_stop_utc")))
    try:
        sig.install(signals)
        try:
            ctx["code"] = _run(a, host, built, folder, result, ctx, log, clock, sleep)
        except podhost.StopUnconfirmed as e:
            ctx["code"] = EXIT_STOP_UNCONFIRMED
            log("failed", phase=ctx["phase"], error=type(e).__name__, detail=str(e))
            JP._not_confirmed(log, e.pod_ids, e.names or [JP._name(host)])
        except podhost.CreateLost as e:
            ctx["code"] = EXIT_STOP_UNCONFIRMED
            log("failed", phase=ctx["phase"], error=type(e).__name__, detail=str(e))
            JP._check_console(log, e.name or JP._name(host), getattr(host, "cap_stop_utc", None))
        except (podhost.HostError, Refusal) as e:
            ctx["code"] = EXIT_CREATE if ctx["phase"] == "create" else EXIT_FAILED
            log("failed", phase=ctx["phase"], error=type(e).__name__, detail=str(e))
        except BaseException as e:  # noqa: BLE001
            ctx["code"] = EXIT_CREATE if ctx["phase"] == "create" else EXIT_FAILED
            log("failed", phase=ctx["phase"], error=type(e).__name__)
        finally:
            finish(a, host, built, folder, result, ctx, log, clock, sleep, sig)
    except BaseException as e:  # noqa: BLE001 - the one signal-raised exception, after its try block was left
        log("late-signal", error=type(e).__name__, phase=ctx["phase"])
        if not ctx["finished"]:
            finish(a, host, built, folder, result, ctx, log, clock, sleep, sig)
    finally:
        sig.restore()
    return ctx["code"]


# ---------------------------------------------------------------- command line

def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="The fiction training-data screen on one RunPod A100 (the lead launches).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("bundle", "launch"):
        p = sub.add_parser(name)
        p.add_argument("--tag", required=True, help=f"new per launch, starting {P.TAG_PREFIX}")
        if name == "bundle":
            p.add_argument("--out", type=pathlib.Path, default=None, help="a new folder for the dry check "
                           "(default <LAUNCH_DIR>/dry/<tag>)")
        p.add_argument("--round", type=int, choices=(1, 2, 3), required=True)
        p.add_argument("--refill", type=pathlib.Path, default=None, help="rounds 2 and 3: refill-rN.jsonl")
        p.add_argument("--refill-sha256", default=None, help="rounds 2 and 3: the refill file's SHA-256")
        p.add_argument("--limit", type=int, default=None, help="a smoke run: at most N rows of each source")
        p.add_argument("--cap-hours", type=float, default=None)
        p.add_argument("--granite-s-per-call", type=float, default=P.GRANITE_S_PER_CALL)
        p.add_argument("--qwen-s-per-row", type=float, default=P.QWEN_S_PER_ROW)
        p.add_argument("--resume-from", type=pathlib.Path, default=None,
                       help="an earlier launch's folder (<LAUNCH_DIR>/runs/<old tag>) of the same round")
        p.add_argument("--ssh-kit", type=pathlib.Path, default=podhost.KIT)
        p.add_argument("--budget-kit", type=pathlib.Path, default=podhost.BUDGET_KIT)
    p = sub.add_parser("summarize")
    p.add_argument("--from", dest="source", type=pathlib.Path, required=True, help="<LAUNCH_DIR>/runs/<tag>")
    p.add_argument("--out", type=pathlib.Path, default=P.SCREEN_OUT)
    p = sub.add_parser("final-reads")
    p.add_argument("--final-dir", type=pathlib.Path, default=P.W / "tmp/side-fiction/final",
                   help="sf_screen.py finalize's folder (dark.jsonl, light.jsonl, screen-report.json)")
    p.add_argument("--screen-dir", type=pathlib.Path, default=P.SCREEN_OUT, help="the per-row files of every round")
    return ap


def main(argv=None) -> int:
    if sys.version_info < (3, 10):
        print("refused: screen_pod.py needs Python 3.10 or later", file=sys.stderr)
        return EXIT_REFUSED
    a = parser().parse_args(argv)
    if a.cmd in ("summarize", "final-reads"):
        import screen_summary
        try:
            report = (screen_summary.summarize(a.source, a.out) if a.cmd == "summarize"
                      else screen_summary.final_reads(a.final_dir, a.screen_dir))
        except (Refusal, OSError, ValueError, KeyError) as e:
            print(f"refused: {type(e).__name__}: {e}", file=sys.stderr)
            return EXIT_REFUSED
        print(json.dumps(report, indent=1, sort_keys=True))
        return EXIT_OK
    if not tag_ok(a.tag):
        print(f"refused: --tag must start with {P.TAG_PREFIX} and be 2 to 40 characters of a-z, 0-9 and '-'",
              file=sys.stderr)
        return EXIT_REFUSED
    if a.limit is not None and a.limit <= 0:
        print("refused: --limit must be positive", file=sys.stderr)
        return EXIT_REFUSED
    if a.cmd == "launch":
        return launch(a)
    folder = pathlib.Path(a.out if a.out is not None else P.DRY / a.tag).absolute()
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / "bundle.tar.gz").exists():
        print("refused: this --out folder already holds a bundle", file=sys.stderr)
        return EXIT_REFUSED
    try:
        built = build(a, folder)
    except (Refusal, OSError, ValueError, KeyError) as e:
        print(f"refused: {type(e).__name__}: {e}", file=sys.stderr)
        return EXIT_REFUSED
    print(json.dumps(built["record"], indent=1, sort_keys=True))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
