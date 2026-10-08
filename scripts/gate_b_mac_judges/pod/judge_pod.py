"""The lead's launcher of the HarmBench judge on one RunPod A100 (runs on the Mac; Python 3.10+, stdlib only).

Written 8 October 2026 (19:52 UTC, clock checked); revised 8 October 2026 (20:48 UTC, clock checked) after the review:
stop safety, one launch per tag, the budget guard's view, fetch retries, orphan stops and the price rule; revised again
8 October 2026 (21:49 UTC, clock checked) after the second review: SIGQUIT and the interrupt line, nohup, a dead
terminal or pipe at exit, the fetch order, the salvage's time budget, orphan names, a lost create reply, record appends,
the budget check after the create, smoke-run verdicts; revised a third time 8 October 2026 (22:44 UTC, clock checked)
after the third review: a reconcile cut short by a signal runs again in the finally block, a 5xx create reply counts as
lost, an orphan stop on a full disk stays confirmed, and a budget.py that hangs or cannot start is a refusal. Nothing
here was run against RunPod or the Hub by the builder.

    PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
    $PY -B judge_pod.py bundle --tag T --out DIR (--run-root R)... (--unit U)... [options]   # no network: build, check
    $PY -B judge_pod.py launch --tag T (--run-root R)... (--unit U)... [options]   # one pod, then stopped; tmp/judge-pod/T

launch, in order (every step logged to tmp/judge-pod/T/judge-pod-log.jsonl; counts, ids, hashes and codes only, no
secret, no text):
  0. the tag: an exclusive non-blocking flock on tmp/judge-pod/T.lock, held for the whole launch. A second launch with
     the same tag refuses at once (exit 2), before any RunPod call, and so does a launch whose folder tmp/judge-pod/T
     exists (every launch has a new tag; its folder is tmp/judge-pod/T).
  1. the bundle (bundle.py): units found and verified as the Mac judges find them, grouped by prepared set, the Mac
     run's pre-checks, a deterministic tar.gz and its SHA-256. A refusal here creates nothing (exit 2), and so does a
     launch with nothing left to judge.
  2. the cap: the pod timer's cap in hours (--cap-hours, or the smallest half hour above 30 min of setup + 0.25 s per
     item to judge + 15 min margin; at most 6 h).
  3. under the lock every family-probe kit shares: reconcile (an untracked pod of this name is stopped), the budget kit's
     guard (budget.py check CAP 1.85, the planning rate; default kit tmp/family-probe-olmo2-1b-bt, reserve $1), and only
     if it allows: create ONE pod (podhost.RunPodHost.create: the kit's image, GPU type, SECURE cloud and in-pod stop
     timer; no hourly price limit, but a price that is not a finite number stops the pod at once). The host records
     (create intent with the cap, pod.json) are written to tmp/family-probe-judge/hosts/judge-T/, where every kit's
     budget.py counts them. Then, still under the lock, the guard again with 0 extra hours (budget.py check 0 1.85):
     every kit's budget.py now counts the new pod at its real costPerHr until its cap. Refused guard: exit 3 (before the
     create: no pod; after it: the pod is stopped); a budget.py that runs past 300 s or cannot start is a refusal.
     RunPod refused the create (a 4xx reply), the price check failed, or the create was interrupted or failed on the Mac
     before a pod was tracked: exit 4 (a pod that was listed or tracked is stopped, confirmed). A create reply that was
     lost (status 0, a 2xx reply without a pod id, a 5xx reply, any status but a 4xx) or interrupted, with no pod in
     any listing: exit 7 with CHECK-CONSOLE (RunPod may still list the pod later).
  4. wait for SSH, check the GPU and the timer, send the bundle (SHA-256 checked on the pod), unpack it and run
     pod_job.py verify there, start pod_run.sh under nohup (venv, torch 2.8.0, pinned pip install, the snapshot
     download without a token, the run), poll its status every 30 s until DONE.json; 5 minutes before the cap the job
     gets SIGTERM (it stops before the next item, exit 5).
  5. fetch the outputs: DONE.json, the run record and the cache first, then the snapshot check, pip freeze and pip log
     best effort (a failed fetch of one of these three is logged fetch-skipped and the fetch goes on). Each file goes
     into <file>.part, its SHA-256 checked against the one sha256-summed on the pod, up to 3 tries, then renamed into
     place (a file in place always has the pod's SHA-256, and the result records each one as soon as it is in place).
     The cache must parse as the tool's HarmBench cache, hold records of this run's units only, each naming the answer
     SHA-256 of the Mac's copy; per-unit coverage and labels are counted. With --limit (a smoke run), exit 0 also needs
     the cache fetched and at least min(limit, todo) newly judged records verified; else exit 6.
  6. ALWAYS: SIGINT, SIGTERM, SIGHUP and SIGQUIT raise ONCE from before the reconcile until after the stop: the first
     one sets all four to SIG_IGN, prints one line ("interrupted: stopping pod <id>; further signals are ignored; the
     in-pod timer stops it at <cap>"), then raises. A signal that was already ignored at the start (nohup) stays
     ignored. The original handlers come back only after the stop has run. The log never raises: a dead terminal or pipe
     switches its echo off and points the dead stdout (or stderr) at /dev/null, so the interpreter's exit flush cannot
     replace the exit code. The finally block runs each step on its own guard, so nothing raised in one skips the stop:
     a reconcile that a signal cut short runs again (the orphan it was stopping is stopped; not confirmed:
     STOP-NOT-CONFIRMED, exit 7); after an interrupted create (once the request was sent), the orphan check (pods of
     this name listed up to 3 times 20 s apart; none listed: CHECK-CONSOLE, exit 7); when the job started and the fetch
     did not complete, the salvage (SIGTERM to the job, then the fetch of the files not yet in place, at most 300 s in
     all; skipped when the first signal was SIGTERM or SIGQUIT: the stop comes first); the stop (never delete),
     confirmed EXITED, else the in-pod timer is shortened to 2 min (the kit's extend_cap.py over ssh's stdin) and the
     stop retried; after a salvage, the exit code that the fetched and verified files support; the result record.

Exit codes: 0 done (all fetched, verified, every unit complete; with --limit, its records judged; pod stopped); 2
refused before any pod (input, tag lock, an existing folder, nothing to judge, no key); 3 budget guard refused or could
not run (before the create: no pod; right after it: the pod is stopped); 4 RunPod refused the create (a 4xx reply and no
pod listed), the price check failed (its stop confirmed), or the create was interrupted or failed on the Mac before a
pod was tracked (any pod that was listed or tracked was stopped, confirmed); 5 the pod job was stopped (cap or signal)
and its partial cache and run record fetched (resume with --resume-from tmp/judge-pod/T and a new tag); 6 any other
failure (a pod that was created is stopped), including a smoke run without its records and a run whose salvage a SIGTERM
or SIGQUIT skipped; 7 A STOP WAS NOT CONFIRMED (STOP-NOT-CONFIRMED names the pod ids and names), or a pod may run that
no listing showed: the create reply was lost (a 5xx reply included) or interrupted (CHECK-CONSOLE), or no listing
worked. Check the RunPod console and stop the pod by hand now; the in-pod timer stops it at its cap at the latest.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import math
import os
import pathlib
import re
import signal
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE.parent
for _p in (TOOL, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import bundle as bundle_mod  # noqa: E402
import pod_job  # noqa: E402
import pod_judge  # noqa: E402
import podhost  # noqa: E402
from cache import Cache  # noqa: E402
from common import HARMBENCH, PREPARED_DIR, Refusal, canonical_bytes, sha256_file  # noqa: E402
from units import add_unit_arguments, load_items, units_from_args  # noqa: E402

JUDGE_POD_ROOT = podhost.ROOT / "tmp/judge-pod"   # launch: the folder of tag T is JUDGE_POD_ROOT/T, its lock T.lock
UPPER_S_PER_ITEM = 0.25          # cap planning: 2 to 4 times the estimated A100 batch-1 fp16 time per answer
EST_S_PER_ITEM = (0.06, 0.12)    # the estimate (README), for the logged time and cost range only
SETUP_UPPER_S = 1800             # pod start, pip, torch, 14.5 GB download, hashing, model load, pre-load length check
MARGIN_S = 900
MAX_CAP_HOURS = 6.0
FINISH_MARGIN_S = 300            # the job gets SIGTERM this long before the cap
POLL_S = 30
SSH_WAIT_S = 1200
MAX_POLL_FAILURES = 10
SALVAGE_WAIT_S = 120             # the salvage's wait for DONE.json after its SIGTERM to the job
SALVAGE_BUDGET_S = 300           # the salvage's whole time (SIGTERM, wait, fetch); the stop follows it
FETCH_TRIES, FETCH_RETRY_S = 3, 10
REMOTE = podhost.REMOTE_ROOT
POD = "bundle/tool/pod"
CACHE_REL, RECORD_REL = "out/harmbench-pod.jsonl", "out/run-record.json"
REQUIRED = ("DONE.json", RECORD_REL)
FETCH_FIRST = ("DONE.json", RECORD_REL, CACHE_REL)                      # in this order; a failed fetch raises
FETCH_BEST_EFFORT = tuple(rel for rel in pod_job.OUTPUTS if rel not in FETCH_FIRST)   # diagnostics: skipped on failure
SKIP_SALVAGE_SIGNALS = (signal.SIGTERM, signal.SIGQUIT)                 # a first signal that asks for the stop first
SECRET_PATTERNS = {"runpod_key": re.compile(r"rpa_[A-Za-z0-9]{10,}"), "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
                   "github_pat": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "hf_token": re.compile(r"hf_[A-Za-z0-9]{30,}"),
                   "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
                   "ssh_public_key": re.compile(r"ssh-(ed25519|rsa) AAAA")}       # = the kits' secret_scan.PATTERNS
EXIT_OK, EXIT_REFUSED, EXIT_BUDGET, EXIT_CREATE, EXIT_STOPPED, EXIT_FAILED, EXIT_STOP_UNCONFIRMED = 0, 2, 3, 4, 5, 6, 7
STOP_BY_HAND = "stop this pod by hand now (RunPod console); the in-pod timer stops it at its cap at the latest"
CHECK_CONSOLE = ("the create reply was lost or interrupted and no listing showed a pod; RunPod may still list one: check "
                 "the RunPod console now and stop any pod of this name by hand (its in-pod timer stops it at its cap)")


class Interrupted(BaseException):
    """SIGTERM, SIGHUP or SIGQUIT during a launch: unwinds into the finally block that stops the pod."""


# ---------------------------------------------------------------- the log (counts, ids, hashes and codes only)

def scrub(value, depth: int = 0):
    """JSON-safe copy; strings are cut at 400 characters and any secret-like string is replaced (defence in depth)."""
    if depth > 6:
        return "[deep]"
    if isinstance(value, dict):
        return {str(k)[:64]: scrub(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [scrub(v, depth + 1) for v in value][:200]
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    s = str(value)
    hits = [name for name, pat in SECRET_PATTERNS.items() if pat.search(s)]
    return f"[redacted: {','.join(hits)}]" if hits else s[:400]


def to_devnull(stream) -> None:
    """After a failed write (EIO from a closed terminal, EPIPE from a dead pipe): point the stream's file descriptor at
    /dev/null. The unwritten bytes stay in the stream's buffer, and the interpreter flushes stdout and stderr at exit;
    a failed exit flush would replace the launcher's exit code with 120. Never raises (a stream without a descriptor,
    as in the tests, is left as it is)."""
    try:
        fd = stream.fileno()
        null = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(null, fd)
        finally:
            os.close(null)
    except Exception:  # noqa: BLE001
        pass


def say(message: str) -> None:
    """One line on stderr that never raises (a closed terminal or pipe must not stop the launcher; a dead stderr is
    pointed at /dev/null)."""
    try:
        print(message, file=sys.stderr, flush=True)
    except OSError:
        to_devnull(sys.stderr)
    except Exception:  # noqa: BLE001 - ValueError (closed), RuntimeError (a reentrant call from the signal handler)
        pass


class RunLog:
    """One JSON line per step, appended to the log file and echoed to stdout. Never raises: a failed append is counted
    and dropped, and the echo is switched off after its first failure (SIGHUP from a closed terminal leaves stdout
    raising EIO; a dead `| tee` raises EPIPE), so no log line can keep the finally block from stopping the pod. After a
    failed write the dead stdout is pointed at /dev/null, so the exit flush keeps the exit code."""

    def __init__(self, path: pathlib.Path, tag: str, echo: bool = True):
        self.path, self.tag, self.echo = pathlib.Path(path), tag, echo
        self.dropped = 0

    def __call__(self, step: str, **fields) -> None:
        stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        try:
            line = json.dumps({**scrub(fields), "utc": stamp, "tag": self.tag, "step": step}, sort_keys=True)
        except (TypeError, ValueError):
            line = json.dumps({"utc": stamp, "tag": self.tag, "step": str(step)[:64], "unserializable": True})
        try:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except (OSError, ValueError):
            self.dropped += 1
        if self.echo:
            try:
                print(line, flush=True)
            except OSError:
                self.echo = False
                to_devnull(sys.stdout)
            except Exception:  # noqa: BLE001
                self.echo = False


# ---------------------------------------------------------------- bundle, resume and cap (no network)

def resume_from(prev: pathlib.Path, units) -> dict:
    """A previous launch's fetched cache, by its own result record: the file's SHA-256 must be the one that launch
    verified at fetch, its run record must say cuda, and its records must belong to this run's units."""
    prev = pathlib.Path(prev)
    result = json.loads((prev / "judge-pod-result.json").read_bytes())
    digest = (result.get("fetched") or {}).get(CACHE_REL)
    path = prev / "fetched" / CACHE_REL
    if not digest or not path.is_file() or sha256_file(path) != digest:
        raise Refusal(f"--resume-from {prev}: no fetched cache with the SHA-256 its result records")
    record = json.loads((prev / "fetched" / RECORD_REL).read_bytes())
    if record.get("device") != "cuda" or record.get("judge") != HARMBENCH:
        raise Refusal(f"--resume-from {prev}: its run record is not a cuda HarmBench run")
    cache = Cache(path, HARMBENCH)
    ours = {u.complete_sha256 for u in units}
    foreign = sum(1 for k in cache.entries if k[0] not in ours)
    if foreign:
        raise Refusal(f"--resume-from {prev}: {foreign} cached records belong to units not given now")
    return {"path": path, "sha256": digest, "from_tag": result.get("tag"), "records": len(cache)}


def cap_hours_for(todo: int, given: float | None) -> float:
    need = (SETUP_UPPER_S + todo * UPPER_S_PER_ITEM + MARGIN_S) / 3600
    auto = max(1.0, math.ceil(need * 2) / 2)
    hours = auto if given is None else float(given)
    if hours < need:
        raise Refusal(f"--cap-hours {hours} is below the planned upper time {need:.2f} h for {todo} answers")
    if hours > MAX_CAP_HOURS:
        raise Refusal(f"the cap {hours} h is above {MAX_CAP_HOURS} h; split the units over two launches")
    return hours


def build(a, out: pathlib.Path) -> dict:
    units, skipped = units_from_args(a)
    expect = {"greedy": a.expect_greedy, "sampled": a.expect_sampled}
    prepared = a.prepared or [PREPARED_DIR]
    groups = bundle_mod.plan_groups(units, prepared, expect)
    resume = resume_from(a.resume_from, units) if a.resume_from else None
    items = {m: sum(len(load_items(u, m)) for u in units) for m in ("greedy", "sampled")}
    todo = items["greedy"] + items["sampled"] - (resume["records"] if resume else 0)
    if a.limit is not None:
        todo = min(todo, a.limit)
    if todo <= 0:
        raise Refusal(f"nothing is left to judge: {items['greedy'] + items['sampled']} answers, "
                      f"{resume['records'] if resume else 0} already judged, --limit {a.limit}")
    cap = cap_hours_for(todo, a.cap_hours)
    tar = out / "bundle.tar.gz"
    with tempfile.TemporaryDirectory(dir=out, prefix="stage-") as tmp:
        manifest = bundle_mod.stage_bundle(groups, pathlib.Path(tmp) / "bundle", a.tag, TOOL, resume, a.limit)
        manifest_sha = sha256_file(pathlib.Path(tmp) / "bundle" / bundle_mod.MANIFEST_NAME)
        tar_sha = bundle_mod.write_tar(pathlib.Path(tmp) / "bundle", tar)
    est = [round((SETUP_UPPER_S / 3 + todo * s) / 60, 1) for s in EST_S_PER_ITEM]
    price = podhost.PLANNING_PRICE
    record = {"kind": "judge-pod bundle record", "tag": a.tag, "bundle_sha256": tar_sha, "manifest_sha256": manifest_sha,
              "bundle_bytes": tar.stat().st_size, "files": len(manifest["files"]),
              "scripts": {k: v for k, v in manifest["files"].items() if k.startswith("tool/")},
              "groups": [{"prepared": g.name, "manifest_sha256": g.manifest_sha256, "dev_bank_sha256": g.dev_bank_sha256,
                          "units": len(g.units)} for g in groups],
              "units": [{"label": u.label, "complete_sha256": u.complete_sha256} for u in units],
              "skipped": len(skipped), "items": items, "todo": todo,
              "resume": None if resume is None else {"sha256": resume["sha256"], "records": resume["records"],
                                                      "from_tag": resume["from_tag"]},
              "cap_hours": cap, "planning_price": price, "price_limit": None, "cost_upper_usd": round(cap * price, 2),
              "estimate_minutes": est, "estimate_usd": [round(m / 60 * price, 2) for m in est]}
    (out / "bundle-record.json").write_bytes(canonical_bytes(record))
    return {"units": units, "groups": groups, "manifest": manifest, "manifest_sha256": manifest_sha, "tar": tar,
            "tar_sha256": tar_sha, "cap_hours": cap, "record": record}


# ---------------------------------------------------------------- remote steps (commands run through host.run)

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
            f"cd {REMOTE} && python3 -I {POD}/pod_job.py verify --bundle bundle")


def start_command(limit: int | None) -> str:
    extra = f" --limit {int(limit)}" if limit is not None else ""
    return (f"cd {REMOTE} || exit 1\n"
            "test ! -e STARTED.json || exit 1\n"
            "mkdir -p out\n"
            f"nohup bash {POD}/pod_run.sh{extra} > run.log 2>&1 < /dev/null &\n"
            "sleep 5\n"
            f"test -f {REMOTE}/STARTED.json")


STATUS_COMMAND = f"cd {REMOTE} && python3 -I {POD}/pod_job.py status --root {REMOTE}"
SUMS_COMMAND = f"cd {REMOTE} && python3 -I {POD}/pod_job.py sums --root {REMOTE}"
TERMINATE_COMMAND = "pkill -TERM -f '[t]ool/pod/pod_job.py run'; true"     # [t]: never matches this shell itself


def last_json(stdout: str):
    for line in reversed((stdout or "").strip().splitlines()):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return None


def whitelist(rec) -> dict:
    if not isinstance(rec, dict):
        return {}
    return {k: rec[k] for k in pod_job.STATUS_FIELDS if k in rec and isinstance(rec[k], (int, float, str, bool, dict))
            and not (isinstance(rec[k], str) and len(rec[k]) > 64)}


def parse_status(stdout: str):
    st = last_json(stdout)
    if st is None or "done" not in st:
        return None
    done = st.get("done")
    return {"started": bool(st.get("started")), "step": str(st.get("step"))[:32] if st.get("step") else None,
            "done": None if not isinstance(done, dict) else {"exit": done.get("exit"), "step": done.get("step")},
            "progress": whitelist(st.get("progress"))}


def poll(host, deadline: float, log, clock=time.time, sleep=time.sleep):
    """DONE.json's {exit, step}, or None when the deadline passed first."""
    failures, last, warned = 0, None, False
    while True:
        code, stdout = host.run(STATUS_COMMAND, timeout=90)
        st = parse_status(stdout) if code == 0 else None
        if st is None:
            failures += 1
            log("status-unreadable", exit=code, failures=failures)
            if failures > MAX_POLL_FAILURES:
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
        sleep(POLL_S)


def time_left(deadline, clock, cap: float) -> float:
    """The seconds the next step may take: `cap`, or less when the salvage's time budget (`deadline`) ends first.
    Raises HostError when the budget is spent (less than 1 s left). No deadline: `cap`."""
    if deadline is None:
        return cap
    left = deadline - clock()
    if left < 1:
        raise podhost.HostError(f"the salvage's time budget of {SALVAGE_BUDGET_S} s is spent")
    return min(cap, left)


def fetch_one(host, rel: str, local: pathlib.Path, digest: str, log, sleep=time.sleep, deadline=None,
              clock=time.time) -> None:
    """One output file: scp into <local>.part, then its SHA-256 against the pod's, up to FETCH_TRIES tries. It is renamed
    into place only when it matches, so a file in place always has the pod's SHA-256. With a deadline (the salvage),
    each scp's timeout is cut to the time left, and no try or retry wait starts past the deadline."""
    part = local.with_name(local.name + ".part")
    local.parent.mkdir(parents=True, exist_ok=True)
    try:
        for attempt in range(1, FETCH_TRIES + 1):
            timeout = time_left(deadline, clock, podhost.FETCH_TIMEOUT_S)          # HostError when the budget is spent
            try:
                part.unlink(missing_ok=True)
                if deadline is None:
                    host.fetch(rel, part)
                else:
                    host.fetch(rel, part, timeout=timeout)
                if sha256_file(part) == digest:
                    os.replace(part, local)
                    return
                why = "sha256"
            except (podhost.HostError, OSError) as e:
                why = type(e).__name__
            log("fetch-attempt-failed", file=rel, attempt=attempt, why=why)
            if attempt < FETCH_TRIES:
                if deadline is not None and clock() + FETCH_RETRY_S + 1 > deadline:
                    raise podhost.HostError(f"the salvage's time budget of {SALVAGE_BUDGET_S} s is spent")
                sleep(FETCH_RETRY_S)
    finally:
        with contextlib.suppress(OSError):
            part.unlink(missing_ok=True)
    raise podhost.HostError(f"{rel}: in {FETCH_TRIES} tries the fetched file never had the pod's SHA-256 {digest[:16]}")


def fetch_outputs(host, out: pathlib.Path, log, fetched: dict | None = None, sleep=time.sleep, deadline=None,
                  clock=time.time) -> dict:
    """The pod's output files that exist there, by their pod-side SHA-256: DONE.json, the run record and the cache first
    (a failure raises), then the diagnostics (snapshot check, pip freeze, pip log) best effort: a HostError there is
    logged fetch-skipped and the fetch goes on. `fetched` (the result's record) gains each file as soon as it is in
    place, so a failure part-way leaves the files already fetched recorded; a file already in place with the pod's
    SHA-256 is kept (the salvage after a partial fetch). `deadline`: the salvage's time budget."""
    fetched = {} if fetched is None else fetched
    code, stdout = host.run(SUMS_COMMAND, timeout=time_left(deadline, clock, 180))
    sums = (last_json(stdout) or {}).get("files") if code == 0 else None
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
                local = out / "fetched" / rel
                if local.exists():
                    if sha256_file(local) != digest:
                        raise Refusal(f"{rel}: the file in place does not have the pod's SHA-256 {digest[:16]}")
                    fetched[rel] = digest
                    continue
                fetch_one(host, rel, local, digest, log, sleep, deadline, clock)
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


def verify_outputs(out: pathlib.Path, built: dict, done: dict, fetched: dict) -> dict:
    """The fetched run record and cache against this launch's bundle and the Mac's copy of every unit."""
    record = json.loads((out / "fetched" / RECORD_REL).read_bytes())
    env = record.get("environment") or {}
    rec_ok = (record.get("device") == "cuda" and record.get("judge") == HARMBENCH
              and record.get("model_revision") == pod_judge.REVISION
              and record.get("bundle_manifest_sha256") == built["manifest_sha256"] and record.get("exit") == done.get("exit"))
    summary = {"run_record_ok": rec_ok, "pod_exit": record.get("exit"), "refused": record.get("refused"),
               "error": record.get("error"), "gpu": env.get("gpu"), "torch": env.get("torch"),
               "transformers": env.get("transformers"), "torch_cuda": env.get("torch_cuda"),
               "attn": (env.get("loaded") or {}).get("attn"), "tokenizer_fingerprint": record.get("tokenizer_fingerprint"),
               "units": [], "complete": False, "records": 0, "judged": 0}
    if not rec_ok:
        raise Refusal("the fetched run record does not match this launch (device, judge, revision, bundle or exit)")
    if CACHE_REL not in fetched:
        return summary
    cache = Cache(out / "fetched" / CACHE_REL, HARMBENCH)
    ours = {u.complete_sha256 for u in built["units"]}
    foreign = sum(1 for k in cache.entries if k[0] not in ours)
    if foreign:
        raise Refusal(f"the fetched cache holds {foreign} records of units not in this launch")
    complete, judged = True, 0
    for u in built["units"]:
        row = {"unit": u.label, "complete_sha256": u.complete_sha256}
        for mode in ("greedy", "sampled"):
            n = cached = yes = unparsed = 0
            for it in load_items(u, mode):
                n += 1
                rec = cache.get((u.complete_sha256, mode, it.prompt_id, it.sample_index))
                if rec is None:
                    continue
                if rec["answer_sha256"] != it.answer_sha256:
                    raise Refusal(f"{u.label}: a fetched {mode} record of prompt {it.prompt_id} names another answer")
                cached += 1
                yes += rec["label"] == "yes"
                unparsed += rec["label"] == "unparsed"
            row[mode] = {"n": n, "judged": cached, "yes": yes, "unparsed": unparsed}
            complete = complete and cached == n
            judged += cached
        summary["units"].append(row)
    summary.update(complete=complete, records=len(cache), judged=judged, cache_undecodable_lines=cache.undecodable)
    return summary


def verdict(out: pathlib.Path, built: dict, done: dict, result: dict, limit, log) -> int:
    """The exit code that the fetched and verified files support (verify_outputs raises when they do not match). A
    finished job exits 0 only when every unit is complete, or, with --limit (a smoke run), when the cache was fetched
    and holds at least min(limit, todo) newly judged records (built todo; records seeded by --resume-from not counted)
    that match this launch's units; else 6."""
    verification = verify_outputs(out, built, done, result["fetched"])
    result["verification"] = verification
    log("verified", complete=verification["complete"], records=verification["records"],
        pod_exit=verification["pod_exit"], gpu=verification["gpu"], torch=verification["torch"],
        transformers=verification["transformers"], attn=verification["attn"],
        tokenizer_fingerprint=verification["tokenizer_fingerprint"],
        units=[{"unit": r["unit"], "greedy": r["greedy"], "sampled": r["sampled"]} for r in verification["units"]])
    if done.get("exit") == 0:
        if limit is None:
            return EXIT_OK if verification["complete"] else EXIT_FAILED
        need = built["record"]["todo"]
        resumed = (built["record"].get("resume") or {}).get("records") or 0
        new = verification["judged"] - resumed
        ok = CACHE_REL in result["fetched"] and new >= need
        log("limit-check", need=need, judged_new=new, cache_fetched=CACHE_REL in result["fetched"], ok=ok)
        return EXIT_OK if ok else EXIT_FAILED
    if done.get("exit") == pod_job.EXIT_STOPPED:
        return EXIT_STOPPED
    return EXIT_FAILED


def salvaged_code(out: pathlib.Path, built: dict, result: dict, limit, log):
    """After a salvage: the verdict of the fetched files when DONE.json and the run record are in place, else None."""
    if any(rel not in result["fetched"] for rel in REQUIRED):
        return None
    done_file = json.loads((out / "fetched" / "DONE.json").read_bytes())
    done = {"exit": done_file.get("exit"), "step": done_file.get("step")} if isinstance(done_file, dict) else {}
    return verdict(out, built, done, result, limit, log)


# ---------------------------------------------------------------- signals, salvage and stop

def _utc_epoch(text: str) -> float:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


class OneShotSignals:
    """SIGINT, SIGTERM, SIGHUP and SIGQUIT during a launch. The first one sets all four to SIG_IGN, prints one line
    (say(): the pod id and the in-pod timer's stop time from describe()), then raises (KeyboardInterrupt for SIGINT,
    Interrupted otherwise): the launch unwinds into its stop once, and no later signal can interrupt the stop. A signal
    whose disposition is SIG_IGN at install() (nohup) is left ignored. ignore() sets SIG_IGN for the finally block;
    restore() puts the original handlers back and is called only after the stop has run. `received` is the first
    signal (finish() skips the salvage when it was SIGTERM or SIGQUIT)."""

    NAMES = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)

    def __init__(self, describe=None):
        self.enabled, self.saved, self.received, self.describe = False, {}, None, describe

    def install(self, enabled: bool = True) -> None:
        if not enabled:
            return
        self.saved = {s: signal.getsignal(s) for s in self.NAMES}
        self.enabled = True
        for s in self.NAMES:
            if self.saved[s] != signal.SIG_IGN:           # nohup's SIGHUP (or any ignored signal) stays ignored
                signal.signal(s, self._handler)

    def _handler(self, signum, frame):
        self.ignore()
        if self.received is None:
            self.received = signum
            self.announce()
        if signum == signal.SIGINT:
            raise KeyboardInterrupt
        raise Interrupted(f"signal {signum}")

    def announce(self) -> None:
        """The one line on the first signal; never raises."""
        try:
            pod_id, cap = self.describe() if self.describe is not None else (None, None)
        except Exception:  # noqa: BLE001
            pod_id, cap = None, None
        say(f"interrupted: stopping pod {pod_id or '(none tracked yet)'}; further signals are ignored; the in-pod "
            f"timer stops it at {cap or '(no cap set yet)'}")

    def ignore(self) -> None:
        if self.enabled:
            for s in self.NAMES:
                signal.signal(s, signal.SIG_IGN)

    def restore(self) -> None:
        if self.enabled:
            for s, h in self.saved.items():
                signal.signal(s, h if h is not None else signal.SIG_DFL)
            self.enabled = False


def salvage(host, out: pathlib.Path, log, fetched: dict, sleep=time.sleep, clock=time.time) -> None:
    """After a failure with the job started and the fetch not complete: SIGTERM to the job, wait for DONE.json (at most
    SALVAGE_WAIT_S), then fetch the files not yet in place (DONE.json, the run record and the cache first). The whole
    salvage has SALVAGE_BUDGET_S of wall-clock time: every ssh and scp timeout is cut to the time left, and no step
    starts after it (HostError). It may raise; the finally block guards it, so nothing raised here can skip the stop."""
    deadline = clock() + SALVAGE_BUDGET_S
    host.run(TERMINATE_COMMAND, timeout=time_left(deadline, clock, 60))
    wait_end = min(clock() + SALVAGE_WAIT_S, deadline)
    while clock() < wait_end:
        code, stdout = host.run(STATUS_COMMAND, timeout=time_left(deadline, clock, 60))
        st = parse_status(stdout) if code == 0 else None
        if st is not None and st["done"] is not None:
            break
        sleep(max(0.0, min(10.0, wait_end - clock())))
    fetch_outputs(host, out, log, fetched, sleep, deadline, clock)
    log("salvaged", files=sorted(fetched))


def safe_stop(host, log) -> dict:
    """host.stop(), never raising: an error is an unconfirmed stop."""
    try:
        return host.stop()
    except BaseException as e:  # noqa: BLE001
        log("stop-error", error=type(e).__name__)
        return {"confirmed": False, "error": type(e).__name__}


def _names(names) -> str | None:
    found = sorted({str(n) for n in (names or ()) if n})
    return ", ".join(found) or None


def _not_confirmed(log, pod_ids, names) -> None:
    """The warning of a pod that may still run: its ids and its real name(s) (never a moved suffix)."""
    ids, name = [str(p) for p in (pod_ids or ()) if p], _names(names)
    log("STOP-NOT-CONFIRMED", pod_ids=ids, name=name, action=STOP_BY_HAND)
    say(f"STOP NOT CONFIRMED: pod(s) {ids or '(unknown id)'} named {name or '(unknown name)'} may still run; "
        f"{STOP_BY_HAND}")


def _check_console(log, name, cap) -> None:
    """A create whose reply was lost or interrupted, and no listing showed a pod: one may still appear."""
    log("CHECK-CONSOLE", name=name, cap_stop_utc=cap, action=CHECK_CONSOLE)
    say(f"CHECK THE RUNPOD CONSOLE: a pod named {name or '(unknown name)'} may run although no listing showed it; "
        f"{CHECK_CONSOLE}; cap {cap or '(unknown)'}")


def _run(a, host, built: dict, out: pathlib.Path, result: dict, ctx: dict, log, clock, sleep) -> int:
    """The launch from the guard to the verification (the try block); the finally block is finish()."""
    with host.budget_lock():
        ctx["phase"] = "reconcile"                     # a signal here: finish() runs reconcile again (an orphan stop)
        try:
            host.reconcile()
        except podhost.HostError:
            ctx["phase"] = "guard"                     # reconcile concluded with its own error: no second run
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
        # pod.json is saved: every kit's budget.py now counts this pod at its real costPerHr until its cap
        allowed, summary = host.budget_check(0.0, podhost.PLANNING_PRICE)
        log("budget-guard-after-create", allowed=allowed, hours=0.0, cost_per_hr=pod.get("costPerHr"), guard=summary)
        if not allowed:
            return EXIT_BUDGET                         # finish() stops the pod
    deadline = _utc_epoch(pod["cap_stop_utc"]) - FINISH_MARGIN_S
    host.wait_ssh(SSH_WAIT_S)
    log("ssh-ready")
    log("checked", **host.check())
    host.send(built["tar"], "bundle.tar.gz", built["tar_sha256"])
    log("bundle-sent", sha256=built["tar_sha256"])
    rc, stdout = host.run(unpack_command(built["tar_sha256"]), timeout=600)
    if rc:
        raise podhost.HostError(f"unpacking or verifying the bundle on the pod failed (exit {rc})")
    log("bundle-verified-on-pod", **whitelist(last_json(stdout)))
    rc, _ = host.run(start_command(a.limit), timeout=120)
    if rc:
        raise podhost.HostError(f"the job did not start (exit {rc})")
    ctx["started"] = True
    log("job-started")
    done = poll(host, deadline, log, clock, sleep)
    if done is None:
        log("deadline", note="SIGTERM to the job before the cap")
        host.run(TERMINATE_COMMAND, timeout=60)
        done = poll(host, clock() + SALVAGE_WAIT_S, log, clock, sleep)
        if done is None:
            raise podhost.HostError("the job did not end after SIGTERM")
    log("job-done", exit=done.get("exit"), pod_step=done.get("step"))
    fetch_outputs(host, out, log, result["fetched"], sleep)
    ctx["fetch_complete"] = True
    return verdict(out, built, done, result, a.limit, log)


def finish(a, host, built: dict, out: pathlib.Path, result: dict, ctx: dict, log, clock, sleep, sig) -> None:
    """The finally block. Signals are ignored first; every step has its own guard, so nothing raised in one step skips
    the next one or the stop. Called a second time only when the first call did not complete (the one signal-raised
    exception came before ignore() took effect)."""
    sig.ignore()
    if ctx["phase"] == "reconcile":              # a reconcile cut short (a signal): an orphan it was stopping may run
        try:
            host.reconcile()
            log("reconcile-retry", ok=True)
        except podhost.StopUnconfirmed as e:
            ctx["code"] = EXIT_STOP_UNCONFIRMED
            log("reconcile-retry", error=type(e).__name__)
            _not_confirmed(log, e.pod_ids, e.names or [_name(host)])
        except podhost.HostError as e:          # e.g. the orphan was stopped (confirmed), or the listing failed
            log("reconcile-retry", error=type(e).__name__, detail=str(e))
        except BaseException as e:  # noqa: BLE001
            log("reconcile-retry", error=type(e).__name__)
    if (not getattr(host, "pod_id", None) and ctx["phase"] == "create" and not getattr(host, "orphan_check_done", False)
            and getattr(host, "create_sent", True)):
        try:                                     # an interrupted create may have left a running pod
            stopped = host.stop_orphans("the create did not return a tracked pod")
            log("orphan-check", stopped=stopped)
            if not stopped:                      # none listed yet: RunPod may still list it
                ctx["code"] = EXIT_STOP_UNCONFIRMED
                _check_console(log, _name(host), getattr(host, "cap_stop_utc", None))
        except BaseException as e:  # noqa: BLE001 - a stop not confirmed, or no listing: a pod may run
            ctx["code"] = EXIT_STOP_UNCONFIRMED
            log("orphan-check-failed", error=type(e).__name__,
                detail=str(e) if isinstance(e, podhost.HostError) else None)
            _not_confirmed(log, getattr(e, "pod_ids", None) or [], getattr(e, "names", None) or [_name(host)])
    if getattr(host, "pod_id", None) and ctx["started"] and not ctx["fetch_complete"]:
        if sig.received in SKIP_SALVAGE_SIGNALS:  # SIGTERM or SIGQUIT first: the stop comes first, no salvage
            log("salvage-skipped", signal=int(sig.received))
        else:
            try:
                salvage(host, out, log, result["fetched"], sleep, clock)
                ctx["salvaged"] = True
            except BaseException as e:  # noqa: BLE001 - best effort; the stop follows
                log("salvage-failed", error=type(e).__name__)
    if getattr(host, "pod_id", None):
        stop = safe_stop(host, log)
        log("stop", **stop)
        if not stop.get("confirmed"):
            try:
                shortened = host.shorten_timer(120, HERE / "extend_cap.py")
            except BaseException as e:  # noqa: BLE001
                shortened = False
                log("shorten-timer-failed", error=type(e).__name__)
            stop = safe_stop(host, log)
            log("stop-retry", shortened=shortened, **stop)
        result["stop"] = stop
    if ctx["salvaged"] and ctx["code"] == EXIT_FAILED:
        try:                                     # local only: the files the salvage put in place
            code = salvaged_code(out, built, result, a.limit, log)
            if code is not None:
                ctx["code"] = code
        except BaseException as e:  # noqa: BLE001
            log("salvage-verify-failed", error=type(e).__name__, detail=str(e) if isinstance(e, Refusal) else None)
    if result.get("stop") is not None and not result["stop"].get("confirmed"):
        ctx["code"] = EXIT_STOP_UNCONFIRMED
        _not_confirmed(log, [getattr(host, "pod_id", None)], [result.get("pod_name") or _name(host)])
    result["exit"] = ctx["code"]
    try:
        (out / "judge-pod-result.json").write_bytes(canonical_bytes(result))
    except BaseException as e:  # noqa: BLE001
        log("result-not-written", error=type(e).__name__)
    log("end", exit=ctx["code"])
    ctx["finished"] = True


def _name(host):
    try:
        return host.name()
    except BaseException:  # noqa: BLE001
        return None


# ---------------------------------------------------------------- launch

def launch(a, host=None, clock=time.time, sleep=time.sleep, signals: bool = True) -> int:
    """One launch under the tag lock (see the module text). Returns the exit code."""
    if not podhost.TAG_RE.match(a.tag or ""):
        say("refused: --tag must be 2 to 40 characters of a-z, 0-9 and '-'")
        return EXIT_REFUSED
    root = pathlib.Path(JUDGE_POD_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / f"{a.tag}.lock"
    with open(lock_path, "a") as lock_handle:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            say(f"refused: another launch holds {lock_path} (one launch per tag at a time)")
            return EXIT_REFUSED
        try:
            return _launch_locked(a, root / a.tag, host, clock, sleep, signals)
        finally:
            fcntl.flock(lock_handle, fcntl.LOCK_UN)


def _launch_locked(a, out: pathlib.Path, host, clock, sleep, signals: bool) -> int:
    if out.exists():
        say(f"refused: {out} exists; every launch has a new tag (its folder is tmp/judge-pod/<tag>)")
        return EXIT_REFUSED
    out.mkdir(parents=True)
    log = RunLog(out / "judge-pod-log.jsonl", a.tag)
    log("start", argv_units=len(a.run_root) + len(a.unit), limit=a.limit, cap_hours=a.cap_hours)
    try:
        built = build(a, out)
    except (Refusal, OSError, ValueError, KeyError) as e:      # unreadable inputs refuse too (ids and paths only)
        log("refused", error=type(e).__name__, reason=str(e))
        return EXIT_REFUSED
    log("bundle", **{k: built["record"][k] for k in ("bundle_sha256", "manifest_sha256", "bundle_bytes", "files", "items",
                                                     "todo", "cap_hours", "planning_price", "cost_upper_usd",
                                                     "estimate_minutes", "estimate_usd", "groups", "resume")})
    if host is None:
        if not os.environ.get("RUNPOD_OPERATOR_API_KEY", "").strip():
            log("refused", reason="RUNPOD_OPERATOR_API_KEY is not set (source the secrets file first)")
            return EXIT_REFUSED
        host = podhost.RunPodHost(a.tag, kit=a.ssh_kit, budget_kit=a.budget_kit)
    result = {"kind": "judge-pod result", "version": 2, "tag": a.tag, "bundle_sha256": built["tar_sha256"],
              "manifest_sha256": built["manifest_sha256"], "cap_hours": built["cap_hours"],
              "planning_price": podhost.PLANNING_PRICE, "host_records": str(getattr(host, "records", "") or ""),
              "budget_kit": str(a.budget_kit), "pod_id": None, "pod_name": None, "fetched": {}, "verification": None,
              "stop": None, "exit": None}
    ctx = {"phase": "guard", "started": False, "fetch_complete": False, "salvaged": False, "finished": False,
           "code": EXIT_FAILED}
    sig = OneShotSignals(describe=lambda: (getattr(host, "pod_id", None) or result.get("pod_id"),
                                           getattr(host, "cap_stop_utc", None) or result.get("cap_stop_utc")))
    try:
        sig.install(signals)
        try:
            ctx["code"] = _run(a, host, built, out, result, ctx, log, clock, sleep)
        except podhost.StopUnconfirmed as e:
            ctx["code"] = EXIT_STOP_UNCONFIRMED
            log("failed", phase=ctx["phase"], error=type(e).__name__, detail=str(e))
            _not_confirmed(log, e.pod_ids, e.names or [_name(host)])
        except podhost.CreateLost as e:
            ctx["code"] = EXIT_STOP_UNCONFIRMED
            log("failed", phase=ctx["phase"], error=type(e).__name__, detail=str(e))
            _check_console(log, e.name or _name(host), getattr(host, "cap_stop_utc", None))
        except (podhost.HostError, Refusal) as e:
            ctx["code"] = EXIT_CREATE if ctx["phase"] == "create" else EXIT_FAILED
            log("failed", phase=ctx["phase"], error=type(e).__name__, detail=str(e))
        except BaseException as e:  # noqa: BLE001 - KeyboardInterrupt, Interrupted and the rest: the pod is stopped below
            ctx["code"] = EXIT_CREATE if ctx["phase"] == "create" else EXIT_FAILED
            log("failed", phase=ctx["phase"], error=type(e).__name__)
        finally:
            finish(a, host, built, out, result, ctx, log, clock, sleep, sig)
    except BaseException as e:  # noqa: BLE001 - the one signal-raised exception, after its try block was left
        log("late-signal", error=type(e).__name__, phase=ctx["phase"])
        if not ctx["finished"]:
            finish(a, host, built, out, result, ctx, log, clock, sleep, sig)
    finally:
        sig.restore()
    return ctx["code"]


# ---------------------------------------------------------------- command line

def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="The HarmBench judge on one RunPod A100 (the lead's launcher).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("bundle", "launch"):
        p = sub.add_parser(name)
        p.add_argument("--tag", required=True, help="new per launch: the pod is attribution-judge-<tag>")
        if name == "bundle":
            p.add_argument("--out", type=pathlib.Path, required=True, help="a new folder for the dry check")
        add_unit_arguments(p)
        p.add_argument("--prepared", action="append", default=[], type=pathlib.Path,
                       help="a prepared set folder (repeatable; default: prepared-kt-dolly-olmo2)")
        p.add_argument("--expect-greedy", type=int, default=200, help="0: any count")
        p.add_argument("--expect-sampled", type=int, default=600, help="0: any count")
        p.add_argument("--limit", type=int, default=None, help="judge at most N answers (a smoke run)")
        p.add_argument("--cap-hours", type=float, default=None)
        p.add_argument("--resume-from", type=pathlib.Path, default=None,
                       help="an earlier launch's folder (tmp/judge-pod/<old tag>) whose fetched cache seeds this run")
        p.add_argument("--ssh-kit", type=pathlib.Path, default=podhost.KIT)
        p.add_argument("--budget-kit", type=pathlib.Path, default=podhost.BUDGET_KIT,
                       help="the kit whose budget.py guards the create (default: reserve $1)")
    return ap


def main(argv=None) -> int:
    if sys.version_info < (3, 10):
        print("refused: judge_pod.py needs Python 3.10 or later (the kit's budget.py does)", file=sys.stderr)
        return EXIT_REFUSED
    a = parser().parse_args(argv)
    if not podhost.TAG_RE.match(a.tag):
        print("refused: --tag must be 2 to 40 characters of a-z, 0-9 and '-'", file=sys.stderr)
        return EXIT_REFUSED
    if a.cmd == "launch":
        return launch(a)
    out = pathlib.Path(a.out).absolute()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "bundle.tar.gz").exists():
        print("refused: this --out folder already holds a bundle", file=sys.stderr)
        return EXIT_REFUSED
    try:
        built = build(a, out)
    except (Refusal, OSError, ValueError, KeyError) as e:
        print(f"refused: {type(e).__name__}: {e}", file=sys.stderr)
        return EXIT_REFUSED
    print(json.dumps({k: v for k, v in built["record"].items() if k not in ("units", "scripts")}, indent=1,
                     sort_keys=True))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
