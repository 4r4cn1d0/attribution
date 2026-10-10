"""Drive one Gate B host (administrative; no experiment logic; from runkit/family-probe/orchestrate.py).

    orchestrate.py after-create HOST   wait for SSH, check GPU and timer, bootstrap (the host's packed stage), wait for
                                       BOOTSTRAP-READY and compare it with the reference (B5), the preflight (its one
                                       recipe: REC on the anchor pod, S elsewhere), compare its environment and policy
                                       with the reference, then by role:
                                         first (wave 0a): record the expected fixture for S and set the reference
                                         job:  wait for the expected fixture
                                       the cap gate, then start the job runner
    orchestrate.py status HOST         receipts and the timer's heartbeat

B5: at BOOTSTRAP-READY the lock's SHA-256, the GPU name and the CUDA runtime must equal the reference's; a pip_version
difference is logged and never stops the pod. After PREFLIGHT-DONE every compared field (scripts/gate_b_reading.py
compared_fields: the 13 environment fields and the policy block without trainable_parameters, trainable_token_ids
and snapshot) must equal the reference's; a missing field refuses. A difference logs ``environment-mismatch`` (field
names only) and stops the pod through the pre-job failure path. The guard record ([D17] 4: PREFLIGHT-DONE.json's
``guard``, from the engine's guard_pin on the pod) is compared with R_1101's pulled guard in the reference the same
way; a strict reference without it refuses on a host after wave 0a. Before the reference exists (it is set after wave
0a's PREFLIGHT-DONE), the anchor pod and the wave-0a pod compare with Gate A's lock and fixture and only log
(``environment-provisional``); any other host refuses. The cap gate (B3 [V21g]) compares the first job's start
requirement (gateb_rules.requirements: max(plan, this pod's projection), the retrain linked) with the remaining time;
it never subtracts the margin again and never uses projected_job_upper_s. Every step stops at the first failed check;
the pod is never deleted; every child process gets an environment without any token variable. A failure whose job
start cannot be read (ssh exit other than 0 or 1) logs ``job-start-unknown``, never ``pre-job-failed`` ([D17] 3).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gateb_mac as mac  # noqa: E402
import gateb_rules as rules  # noqa: E402
import secret_scan  # noqa: E402

ROOT = HERE.parents[1]
HOST_TOOL = [sys.executable, str(HERE / "host.py")]
PLAN_TOOL = [sys.executable, str(HERE / "plan_tool.py")]
REMOTE = "/workspace/attribution-headroom"
GPU = "NVIDIA A100-SXM4-80GB"
EXPECTED = mac.EXPECTED_FIXTURE                    # plan_tool requeue moves it aside for a first host ([D16] 7)
WORKER_SETUP = "worker-setup-gateb.tar.gz"
WORKER_BOOTSTRAP = "worker_bootstrap_gateb.sh"
BOOTSTRAP_OUTER = "worker-bootstrap-process-001"           # process_receipt's folder: process-receipt.json on exit


def clean_env() -> dict:
    return secret_scan.scrubbed(os.environ, rules.TOKEN_ENV_NAMES)


def plan() -> dict:
    return mac.load_plan()


def log(host: str, event: str, **fields) -> None:
    record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "host": host, "event": event, **fields}
    (HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(HERE / "hosts" / host / "orchestrate.jsonl", "a") as handle:
        handle.write(json.dumps(record) + "\n")
    print(json.dumps(record), flush=True)


def env_record(host: str, record: dict) -> None:
    """The environment-check records (B8): hosts/HOST/environment-checks.jsonl, field names only."""
    (HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(HERE / "hosts" / host / "environment-checks.jsonl", "a") as handle:
        handle.write(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **record}) + "\n")


def tool(*args: str, stdin_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([*HOST_TOOL, *args], capture_output=True, text=True, env=clean_env(), input=stdin_text)


def ssh(host: str, command: str) -> subprocess.CompletedProcess:
    return tool("ssh", host, command)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def send(host: str, local: pathlib.Path, remote_name: str) -> None:
    if tool("send", host, str(local), f"{REMOTE}/{remote_name}", sha(local)).returncode:
        raise SystemExit(f"{host}: transfer or hash check of {remote_name} failed")


def fetch(host: str, remote_name: str, local: pathlib.Path) -> dict:
    if tool("fetch", host, f"{REMOTE}/{remote_name}", str(local)).returncode:
        raise SystemExit(f"{host}: could not fetch {remote_name}")
    return json.loads(local.read_text())


def start_background(host: str, outer: str, command: str) -> None:
    script = (f"cd {REMOTE} && test ! -e {outer} || exit 1\n"
              f"nohup python3 process_receipt.py --out {outer} -- {command} > {outer}.log 2>&1 < /dev/null &\n"
              f"sleep 15; cd {REMOTE} && test -f {outer}/started.json")
    if ssh(host, script).returncode:
        out = ssh(host, f"cd {REMOTE} && tail -20 {outer}/process.log 2>/dev/null").stdout
        raise SystemExit(f"{host}: {outer} did not start:\n{out}")


def wait_file(host: str, remote_file: str, seconds: int, every: int = 60, ended: str | None = None) -> dict:
    """Wait for a JSON file on the pod. With ``ended`` (the producing process's receipt), stop as soon as that process
    has ended without writing the file, instead of waiting out ``seconds`` (8 Oct: a family-probe bootstrap that failed
    at its import waited the full 3600 s for BOOTSTRAP-READY.json, about $1.8)."""
    def read(name=remote_file):
        out = ssh(host, f"cat {REMOTE}/{name} 2>/dev/null")
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None

    deadline = time.time() + seconds
    while time.time() < deadline:
        found = read()
        if found is not None:
            return found
        receipt = read(ended) if ended else None
        if receipt is not None:
            found = read()                                       # the file may land just before the receipt
            if found is not None:
                return found
            raise SystemExit(f"{host}: the process ended (exit {receipt.get('exit_code')}) without {remote_file}")
        time.sleep(every)
    found = read()
    if found is not None:
        return found
    raise SystemExit(f"{host}: {remote_file} did not appear within {seconds} s")


def wait_ssh(host: str, seconds: int = 1200) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if tool("get", host).returncode == 0 and ssh(host, "true").returncode == 0:
            return
        time.sleep(15)
    raise SystemExit(f"{host}: no SSH within {seconds} s")


def check(host: str) -> None:
    out = ssh(host, "nvidia-smi --query-gpu=name --format=csv,noheader; cat /workspace/.pod-timer/heartbeat.json")
    lines = out.stdout.splitlines()
    if out.returncode or not lines or lines[0].strip() != GPU:
        raise SystemExit(f"{host}: GPU is not {GPU}: {lines[:1]}")
    beat = json.loads("\n".join(lines[1:]))
    if not (beat.get("state") == "armed" and beat.get("supervised") is True and (beat.get("governing") or {}).get("source") == "cap"
            and all((beat.get("can_stop") or {}).values())):
        raise SystemExit(f"{host}: the stop timer is not armed and supervised with its cap")
    log(host, "checked", gpu=lines[0].strip(), cap_stop_utc=beat["governing"]["stop_at_utc"])


def packed(host: str) -> pathlib.Path:
    return HERE / "setup" / f"packed-{plan()['hosts'][host]['stage']}"


def bootstrap(host: str) -> None:
    folder = packed(host)
    receipt = json.loads((folder / "setup-receipt.json").read_text())
    if receipt["sealed_files_sha256"] != plan()["hosts"][host]["sealed_files_sha256"]:
        raise SystemExit(f"{host}: the packed setup is not the one the plan names")
    if tool("send", host, str(folder / WORKER_SETUP), f"{REMOTE}/{WORKER_SETUP}", receipt["setup"]["sha256"]).returncode:
        raise SystemExit(f"{host}: setup transfer or hash check failed")
    unpack = (f"cd {REMOTE} && python3 - <<'REMOTE'\n"
              "import pathlib,hashlib,tarfile\n"
              f"p=pathlib.Path('{WORKER_SETUP}');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{receipt['setup']['sha256']}'\n"
              f"assert not pathlib.Path('{BOOTSTRAP_OUTER}').exists()\n"
              "with tarfile.open(p) as t:t.extractall('.',filter='data')\n"
              "REMOTE")
    if ssh(host, unpack).returncode:
        raise SystemExit(f"{host}: setup unpack failed")
    start_background(host, BOOTSTRAP_OUTER, f"bash {WORKER_BOOTSTRAP}")
    log(host, "bootstrap-started")


def provisional_reference() -> dict:
    """Gate A's values for the log-only comparison of the anchor and wave-0a pods: LOCK's SHA-256 (gateb_rules,
    null until the lead pins it) and the Gate A fixture's environment and policy (B5)."""
    fixture = json.loads((ROOT / rules.GATE_A_FIXTURE).read_text())
    return {"bootstrap": {"lock_sha256": rules.LOCK_SHA256, "pip_version": None,
                          "gpu": fixture["environment"]["cuda"]["name"],
                          "cuda_runtime": fixture["environment"]["cuda"]["torch_cuda_runtime"]},
            "fields": mac.compared_fields(fixture["environment"], rules.LOCK_SHA256, fixture.get("policy_identity"))}


def reference_for(host: str) -> tuple[dict, bool]:
    """(the reference, whether a difference stops the pod)."""
    p = plan()
    if p.get("reference"):
        return p["reference"], True
    if p["hosts"][host]["wave"] in ("anchor", "0a"):
        return provisional_reference(), False
    raise SystemExit(f"{host}: no environment reference yet (set after wave 0a's PREFLIGHT-DONE)")


def environment_gate(host: str, point: str, new: dict, fields) -> dict:
    reference, strict = reference_for(host)
    ref = reference["bootstrap"] if point == "bootstrap" else {**reference["fields"], "guard": reference.get("guard")}
    result = rules.compare(new, ref, fields)
    env_record(host, {"point": point, "strict": strict, **result})
    if result["logged"]:
        log(host, "pip-version-differs" if "pip_version" in result["logged"] else "environment-logged",
            fields=result["logged"])
    if not strict:
        log(host, "environment-provisional", point=point, differ=result["differ"], missing=result["missing"])
        return result
    if result["stop"]:
        log(host, "environment-mismatch", point=point, fields=result["differ"], missing=result["missing"])
        raise SystemExit(f"{host}: the environment differs from the reference at {point}: "
                         f"{result['differ'] + result['missing']}")
    return result


def bootstrap_check(host: str, ready: dict) -> dict:
    """B5 at BOOTSTRAP-READY: lock SHA-256, GPU and CUDA runtime stop the pod; pip_version is only logged."""
    return environment_gate(host, "bootstrap", ready, rules.BOOTSTRAP_FIELDS)


def preflight_check(host: str, verification: dict, ready: dict, done: dict | None = None) -> dict:
    """B5 after PREFLIGHT-DONE: every compared field (and the policy block) against the reference, and ([D17] 4) the
    guard record (PREFLIGHT-DONE.json's ``guard``, the engine's guard_pin on this pod) against R_1101's pulled guard
    in the reference (plan_tool record-done puts it there). A strict reference without a guard record refuses on a
    host after wave 0a (wave 0a is complete before them, so its R_1101 guard must be recorded); the anchor and wave-0a
    hosts compare it once it exists."""
    fields = mac.compared_fields(verification.get("environment") or {}, ready.get("lock_sha256"),
                                 verification.get("policy_identity"))
    reference, strict = reference_for(host)
    names = sorted(set(fields) | set(reference["fields"]))
    if reference.get("guard") is not None:
        fields = {**fields, "guard": (done or {}).get("guard")}
        names.append("guard")
    elif strict and plan()["hosts"][host]["wave"] not in ("anchor", "0a"):
        log(host, "guard-reference-missing")
        raise SystemExit(f"{host}: the reference has no guard record (plan_tool.py record-done of R_1101's host "
                         "records it)")
    return environment_gate(host, "preflight", fields, names)


def parse_utc(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def cap_stop(host: str) -> str:
    folder = HERE / "hosts" / host
    stop = json.loads((folder / "pod.json").read_text())["cap_stop_utc"]
    override = folder / "cap-override.json"
    if override.exists():
        later = json.loads(override.read_text())["stop_at_utc"]
        if parse_utc(later) > parse_utc(stop):
            stop = later
    return stop


def preflight_wait(wait_s: int, stop_utc: str, now: dt.datetime) -> int:
    return int(max(0, min(wait_s, (parse_utc(stop_utc) - now).total_seconds())))


def cap_gate(host: str, done: dict, now: dt.datetime) -> dict:
    """The first job's start requirement against the remaining time (B3 [V21g]); a missing stop refuses."""
    jobs = plan()["hosts"][host]["jobs"]
    try:
        need = rules.requirements(jobs, done.get("cap_projection") or {})[0]
    except (KeyError, TypeError, ValueError):
        return {"remaining_s": None, "requirement_s": None, "ok": False}
    stop = done.get("governing_stop_utc")
    remaining = (parse_utc(stop) - now).total_seconds() if stop else None
    return {"remaining_s": remaining, "requirement_s": need, "ok": rules.gate(remaining, need)}


def preflight(host: str) -> dict:
    p = plan()
    h = p["hosts"][host]
    p_host = dict(p)
    p_host["preflight_recipes"], p_host["preflight_prepared"] = [h["recipe_path"]], p["prepared_name"]
    local = HERE / "hosts" / host / "plan-preflight.json"
    local.write_text(json.dumps(p_host, indent=1, sort_keys=True) + "\n")
    send(host, local, "plan.json")
    start_background(host, "preflight-outer", "venv/bin/python preflight_gateb.py")
    wait = preflight_wait(h["preflight_wait_s"], cap_stop(host), dt.datetime.now(dt.timezone.utc))
    done = wait_file(host, "PREFLIGHT-DONE.json", wait)
    log(host, "preflight-finished", ok=done["ok"], recipe=done["recipe"], init_equals_untuned=done.get("init_equals_untuned"))
    if not done["ok"] or done["recipe"] != h["recipe_path"]:
        raise SystemExit(f"{host}: the preflight did not pass for the host's recipe")
    return done


def record_first(host: str, verification_file: pathlib.Path) -> None:
    """Wave 0a's first host: its fixture is the expected one for S; then the environment reference (B5). A host whose
    jobs were moved (requeue or defer) never records them: only its replacement acts as first ([D16] 7, 8)."""
    if any(d.get("from") == host for d in plan().get("deferrals") or []):
        raise SystemExit(f"{host}: its jobs were moved to its replacement; a stopped kit pod is never restarted")
    if EXPECTED.exists():
        raise SystemExit("an expected fixture is already recorded")
    EXPECTED.write_bytes(verification_file.read_bytes())
    log(host, "expected-fixture-recorded", sha256=sha(EXPECTED))
    done = subprocess.run([*PLAN_TOOL, "set-reference", host], capture_output=True, text=True, env=clean_env())
    if done.returncode:
        raise SystemExit(f"{host}: set-reference failed: {done.stderr[-300:]}")
    log(host, "reference-set")


def start_job(host: str, done: dict) -> None:
    gate = cap_gate(host, done, dt.datetime.now(dt.timezone.utc))
    if not gate["ok"]:
        log(host, "cap-insufficient", **gate)
        raise SystemExit(f"{host}: the first job does not fit the remaining cap")
    send(host, mac.PLAN, "plan.json")
    if EXPECTED.exists():
        send(host, EXPECTED, EXPECTED.name)
    start_background(host, "job-outer", f"venv/bin/python job_runner_gateb.py {host}")
    log(host, "job-started", plan_sha256=sha(mac.PLAN), jobs=len(plan()["hosts"][host]["jobs"]))


def wait_for(condition, what: str, seconds: int = 6 * 3600) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if condition():
            return
        time.sleep(30)
    if condition():
        return
    raise SystemExit(f"waited {seconds} s for {what}")


def _after_create(host: str, step: dict) -> None:
    role = plan()["hosts"][host]["role"]
    folder = HERE / "hosts" / host
    step["name"] = "wait-ssh"
    wait_ssh(host)
    step["name"] = "check"
    check(host)
    step["name"] = "bootstrap"
    bootstrap(host)
    step["name"] = "bootstrap-ready"
    wait_file(host, "BOOTSTRAP-READY.json", 3600, ended=f"{BOOTSTRAP_OUTER}/process-receipt.json")
    ready = fetch(host, "BOOTSTRAP-READY.json", folder / "bootstrap-ready.json")
    step["name"] = "bootstrap-check"
    bootstrap_check(host, ready)
    step["name"] = "preflight"
    done = preflight(host)
    verification = fetch(host, f"{done['folder']}/verification.json", folder / "verification.json")
    step["name"] = "preflight-check"
    preflight_check(host, verification, ready, done)
    step["name"] = "cap-gate"                          # before record_first changes the kit
    gate = cap_gate(host, done, dt.datetime.now(dt.timezone.utc))
    if not gate["ok"]:
        log(host, "cap-insufficient", **gate)
        raise SystemExit(f"{host}: the first job does not fit the remaining cap")
    if role == "first":
        step["name"] = "record-first"
        record_first(host, folder / "verification.json")
    elif role == "job":
        step["name"] = "wait-for-fixture"
        wait_for(lambda: EXPECTED.exists() and bool(plan().get("reference")), f"{host}: the expected fixture")
    step["name"] = "start-job"
    start_job(host, done)


def after_create(host: str) -> None:
    """``_after_create``; any failure before the job starts is logged as ``pre-job-failed`` with its step, the in-pod
    stop is moved to 2 min from now and the pod is stopped (never deleted), then the failure is raised again. When
    the pod cannot say whether the job started (``job_started`` None: an ssh exit other than 0 or 1, or an
    exception), the failure is logged as ``job-start-unknown`` instead ([D17] 3), and the pod is stopped the same
    way; ``plan_tool.py requeue`` then needs the operator's confirm-stopped record. ``pre-job-stop`` logs the stop's
    exit (host.py stop exits 1 when it cannot confirm EXITED)."""
    step = {"name": "start"}
    try:
        _after_create(host, step)
    except BaseException as exc:
        started = job_started(host)
        if started:
            log(host, "job-started", note=f"started although {step['name']} reported {type(exc).__name__}")
        else:
            log(host, "pre-job-failed" if started is False else "job-start-unknown", step=step["name"],
                error=type(exc).__name__, detail=str(exc)[-300:])
            shortened = tool("extend-cap", host, "120")
            stopped = tool("stop", host)
            log(host, "pre-job-stop", exit=stopped.returncode, timer_shortened=shortened.returncode == 0,
                out=(stopped.stdout + stopped.stderr)[-300:])
            raise


def job_started(host: str) -> bool | None:
    """True when the job runner's started.json exists (ssh exit 0), False when it does not (exit 1, ``test -f``'s
    false), None (unknown) for any other exit or an exception ([D17] 3: a dropped connection never reads as "not
    started")."""
    try:
        code = ssh(host, f"test -f {REMOTE}/job-outer/started.json").returncode
    except BaseException:  # noqa: BLE001
        return None
    return True if code == 0 else False if code == 1 else None


def status(host: str) -> None:
    out = ssh(host, f"cd {REMOTE} && ls -d round1/*/ anchor-*/ gatec/*/ job-done/* 2>/dev/null; ls -d BOOTSTRAP-READY.json "
                    "PREFLIGHT-DONE.json JOB-DONE.json deferral.json cuda-preflight-* 2>/dev/null; "
                    "python3 -c \"import json;b=json.load(open('/workspace/.pod-timer/heartbeat.json'));"
                    "print('timer',b['state'],b['governing']['source'],b['governing']['stop_at_utc'],b['utc'])\"")
    print(out.stdout or out.stderr)


def main() -> int:
    command, host = sys.argv[1], sys.argv[2]
    {"after-create": after_create, "status": status, "check": check, "bootstrap": bootstrap}[command](host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
