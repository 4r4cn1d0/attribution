"""Drive one family probe's host (administrative; no experiment logic).

    orchestrate.py after-create HOST   wait for SSH, check GPU and timer, bootstrap, wait until ready, for a gated probe
                                       the gated download (the token goes to host.py on stdin, then to ssh's stdin),
                                       the preflight (waiting at most the probe's preflight_wait_s and never past the
                                       cap), then by role:
                                         first: record the chosen recipe and the expected fixture, then start its job
                                         job:   wait for the expected fixture, then start its job
    orchestrate.py full HOST           create (through the budget guard in launch.py), then after-create
    orchestrate.py status HOST         receipts and the timer's heartbeat

Every step stops at the first failed check. The pod is never deleted; host.py stop is the only stop. Every child
process gets an environment without any token variable. start_job refuses a job whose projected upper time does not fit
the remaining cap with 30 min to spare (cap-insufficient; the pod is then stopped). After the job starts, CAP-CHECK.json
is watched and cap-risk is logged when the job runner projects less than 30 min of margin.

Review fixes (8 October): the gated step needs host.py's exit 0 and a record written by that call; the token leaves
this process's environment after the gated step (or at once for an open probe); a pre-job failure first moves the
in-pod stop to 2 min from now (extend-cap 120, a second path), then stops the pod (retried and confirmed by host.py),
unless the job had already started (job-outer/started.json), which then belongs to the finisher; wait_file and
wait_for read once more after their deadline (a Mac that slept); the cap gate runs before record_first, so a refusal
leaves the kit unchanged.
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
import probe_constants as pc  # noqa: E402
import probes  # noqa: E402
import secret_scan  # noqa: E402

HOST_TOOL = [sys.executable, str(HERE / "host.py")]
REMOTE = "/workspace/attribution-headroom"
GPU = "NVIDIA A100-SXM4-80GB"
SETUP = HERE / "setup/worker-setup-probe.tar.gz"
EXPECTED = HERE / "expected-fixture-probe.json"
CAP_MARGIN_S = 1800


def clean_env() -> dict:
    """The environment of every child process: this one's without any token variable (review fix 5)."""
    return secret_scan.scrubbed(os.environ, pc.TOKEN_ENV_NAMES)


def plan() -> dict:
    return json.loads((HERE / "plan.json").read_text())


def save_plan(p: dict) -> None:
    (HERE / "plan.json").write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")


def log(host: str, event: str, **fields) -> None:
    record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "host": host, "event": event, **fields}
    (HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(HERE / "hosts" / host / "orchestrate.jsonl", "a") as handle:
        handle.write(json.dumps(record) + "\n")
    print(json.dumps(record), flush=True)


def tool(*args: str, stdin_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([*HOST_TOOL, *args], capture_output=True, text=True, env=clean_env(), input=stdin_text)


def ssh(host: str, command: str) -> subprocess.CompletedProcess:
    return tool("ssh", host, command)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def send(host: str, local: pathlib.Path, remote_name: str) -> None:
    if tool("send", host, str(local), f"{REMOTE}/{remote_name}", sha(local)).returncode:
        raise SystemExit(f"{host}: transfer or hash check of {remote_name} failed")


def start_background(host: str, outer: str, command: str) -> None:
    """Start COMMAND under a process receipt in OUTER; nohup on its own line so the SSH session ends at once."""
    script = (f"cd {REMOTE} && test ! -e {outer} || exit 1\n"
              f"nohup python3 process_receipt.py --out {outer} -- {command} > {outer}.log 2>&1 < /dev/null &\n"
              f"sleep 15; cd {REMOTE} && test -f {outer}/started.json")
    if ssh(host, script).returncode:
        out = ssh(host, f"cd {REMOTE} && tail -20 {outer}/process.log 2>/dev/null").stdout
        raise SystemExit(f"{host}: {outer} did not start:\n{out}")


def wait_file(host: str, remote_file: str, seconds: int, every: int = 60) -> dict:
    def read():
        out = ssh(host, f"cat {REMOTE}/{remote_file} 2>/dev/null")
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None

    deadline = time.time() + seconds
    while time.time() < deadline:
        found = read()
        if found is not None:
            return found
        time.sleep(every)
    found = read()                        # review fix 14: once more after the deadline (the Mac may have slept)
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


def bootstrap(host: str) -> None:
    receipt = json.loads((HERE / "setup/setup-receipt.json").read_text())
    if tool("send", host, str(SETUP), f"{REMOTE}/worker-setup-probe.tar.gz", receipt["setup"]["sha256"]).returncode:
        raise SystemExit(f"{host}: setup transfer or hash check failed")
    unpack = (f"cd {REMOTE} && python3 - <<'REMOTE'\n"
              "import pathlib,hashlib,tarfile\n"
              f"p=pathlib.Path('worker-setup-probe.tar.gz');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{receipt['setup']['sha256']}'\n"
              "assert not pathlib.Path('worker-bootstrap-process-001').exists()\n"
              "with tarfile.open(p) as t:t.extractall('.',filter='data')\n"
              "REMOTE")
    if ssh(host, unpack).returncode:
        raise SystemExit(f"{host}: setup unpack failed")
    start_background(host, "worker-bootstrap-process-001", "bash worker_bootstrap_probe.sh")
    log(host, "bootstrap-started")


def gated_download(host: str) -> None:
    """For a gated probe: hand the token to host.py gated-download on stdin (never an argument or the environment).
    Success needs host.py's exit 0 and a record written by this call (an earlier record is archived first)."""
    if not any(e["gated"] for e in probes.download_plan(pc.probe())):
        secret_scan.scrub_process(os.environ, pc.TOKEN_ENV_NAMES)        # an open probe never needs the token
        return
    token = os.environ.get(pc.HF_TOKEN_ENV, "").strip()
    if not token:
        raise SystemExit(f"{host}: {pc.HF_TOKEN_ENV} is not set for the gated download")
    record_file = HERE / "hosts" / host / "gated-download.json"
    if record_file.exists():                                              # review fix 7: never trust a stale record
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        record_file.rename(record_file.with_name(f"gated-download-earlier-{stamp}.json"))
    done = tool("gated-download", host, stdin_text=token + "\n")
    token = None
    secret_scan.scrub_process(os.environ, pc.TOKEN_ENV_NAMES)            # the disputed review item: no token after use
    record = json.loads(record_file.read_text()) if record_file.exists() else {"ok": False}
    log(host, "gated-download-finished", ok=record.get("ok"), exit=record.get("exit"), tool_exit=done.returncode)
    if done.returncode != 0 or record.get("ok") is not True:
        raise SystemExit(f"{host}: the gated download failed")


def cap_stop(host: str) -> str:
    """The host's current stop: the later of pod.json's cap and its cap-override.json."""
    folder = HERE / "hosts" / host
    stop = json.loads((folder / "pod.json").read_text())["cap_stop_utc"]
    override = folder / "cap-override.json"
    if override.exists():
        later = json.loads(override.read_text())["stop_at_utc"]
        if parse_utc(later) > parse_utc(stop):
            stop = later
    return stop


def parse_utc(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def preflight_wait(wait_s: int, stop_utc: str, now: dt.datetime) -> int:
    """The probe's preflight wait, never past the cap."""
    return int(max(0, min(wait_s, (parse_utc(stop_utc) - now).total_seconds())))


def cap_gate(done: dict, now: dt.datetime) -> dict:
    """Start a job only when its projected upper time fits the remaining cap with CAP_MARGIN_S to spare; a missing
    stop or projection refuses."""
    stop, projected = done.get("governing_stop_utc"), done.get("projected_job_upper_s")
    if stop is None or projected is None:
        return {"remaining_s": None, "projected_job_upper_s": projected, "ok": False}
    remaining = (parse_utc(stop) - now).total_seconds()
    return {"remaining_s": remaining, "projected_job_upper_s": projected, "ok": projected <= remaining - CAP_MARGIN_S}


def preflight(host: str) -> dict:
    p = plan()
    recipes = p["first_host_recipes"] if p["hosts"][host]["role"] == "first" else [p["recipe_path"]]
    p_host = dict(p); p_host["preflight_recipes"] = recipes
    local = HERE / "hosts" / host / "plan-preflight.json"
    local.write_text(json.dumps(p_host, indent=1, sort_keys=True) + "\n")
    send(host, local, "plan.json")
    start_background(host, "preflight-outer", "venv/bin/python preflight_probe.py")
    wait = preflight_wait(p["hosts"][host]["preflight_wait_s"], cap_stop(host), dt.datetime.now(dt.timezone.utc))
    done = wait_file(host, "PREFLIGHT-DONE.json", wait)
    log(host, "preflight-finished", ok=done["ok"], recipe=done["recipe"], init_equals_untuned=done.get("init_equals_untuned"),
        projected_job_upper_s=done.get("projected_job_upper_s"),
        tried=[(t["recipe"], (t.get("verdict") or {}).get("use_this_recipe")) for t in done["tried"]])
    if not done["ok"]:
        raise SystemExit(f"{host}: no candidate recipe passed the preflight")
    return done


def record_first(host: str, done: dict) -> None:
    if EXPECTED.exists():
        raise SystemExit("an expected fixture is already recorded")
    target = HERE / "hosts" / host / "verification.json"
    if tool("fetch", host, f"{REMOTE}/{done['folder']}/verification.json", str(target)).returncode:
        raise SystemExit(f"{host}: could not fetch the fixture")
    EXPECTED.write_bytes(target.read_bytes())
    subprocess.run([sys.executable, str(HERE / "plan_tool.py"), "set-recipe", done["recipe"]], check=True, env=clean_env())
    log(host, "expected-fixture-recorded", sha256=sha(EXPECTED), recipe=done["recipe"])


def start_job(host: str, done: dict | None = None) -> None:
    job = plan()["hosts"][host]
    done = done or wait_file(host, "PREFLIGHT-DONE.json", 60)
    gate = cap_gate(done, dt.datetime.now(dt.timezone.utc))
    if not gate["ok"]:
        log(host, "cap-insufficient", **gate)
        raise SystemExit(f"{host}: the projected job does not fit the remaining cap")
    send(host, HERE / "plan.json", "plan.json")
    send(host, EXPECTED, "expected-fixture-probe.json")
    start_background(host, "job-outer", f"venv/bin/python job_runner_probe.py {host}")
    log(host, "job-started", plan_sha256=sha(HERE / "plan.json"), prepared=job.get("prepared"),
        base_eval=bool(job.get("base_eval")))


def wait_for(condition, what: str, seconds: int = 6 * 3600) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if condition():
            return
        time.sleep(30)
    if condition():                       # review fix 14: once more after the deadline
        return
    raise SystemExit(f"waited {seconds} s for {what}")


def ready(host: str) -> bool:
    p = plan()
    return EXPECTED.exists() and bool(p.get("recipe_path"))


def _after_create(host: str, step: dict) -> None:
    role = plan()["hosts"][host]["role"]
    if role != "first":
        step["name"] = "wait-for-recipe"
        wait_for(lambda: EXPECTED.exists() and bool(plan().get("recipe_path")), f"{host}: the first host's recipe choice")
    step["name"] = "wait-ssh"
    wait_ssh(host)
    step["name"] = "check"
    check(host)
    step["name"] = "bootstrap"
    bootstrap(host)
    ready_rec = wait_file(host, "BOOTSTRAP-READY.json", 3600)
    log(host, "bootstrap-ready", engine=ready_rec.get("engine_sha256", "")[:16])
    step["name"] = "gated-download"
    gated_download(host)
    step["name"] = "preflight"
    done = preflight(host)
    step["name"] = "cap-gate"                          # review fix 16: before record_first changes the kit
    gate = cap_gate(done, dt.datetime.now(dt.timezone.utc))
    if not gate["ok"]:
        log(host, "cap-insufficient", **gate)
        raise SystemExit(f"{host}: the projected job does not fit the remaining cap")
    if role == "first":
        step["name"] = "record-first"
        record_first(host, done)
    else:
        step["name"] = "wait-for-fixture"
        wait_for(lambda: ready(host), f"{host}: the expected fixture")
    step["name"] = "start-job"
    start_job(host, done)


def after_create(host: str) -> None:
    """``_after_create``; any failure before the job starts (SystemExit and interrupts included) is logged as
    ``pre-job-failed`` with its step, then the pod is stopped (never deleted) so it cannot bill while idle,
    then the failure is raised again. Once a job is running, the finisher owns the pod."""
    step = {"name": "start"}
    try:
        _after_create(host, step)
    except BaseException as exc:
        if job_started(host):                        # review fix 18: a running job belongs to the finisher
            log(host, "job-started", note=f"started although {step['name']} reported {type(exc).__name__}")
        else:
            log(host, "pre-job-failed", step=step["name"], error=type(exc).__name__, detail=str(exc)[-300:])
            shortened = tool("extend-cap", host, "120")      # review fix 10: the in-pod timer as a second stop path
            stopped = tool("stop", host)
            log(host, "pre-job-stop", exit=stopped.returncode, timer_shortened=shortened.returncode == 0,
                out=(stopped.stdout + stopped.stderr)[-300:])
            raise
    try:                                         # a running job belongs to the finisher: a watch failure never stops it
        watch_cap_check(host)
    except BaseException as exc:  # noqa: BLE001
        log(host, "cap-check-watch-ended", error=type(exc).__name__, detail=str(exc)[-200:])


def job_started(host: str) -> bool:
    """Whether the job runner has started on the pod (its outer receipt's started.json exists); False when unknown."""
    try:
        return ssh(host, f"test -f {REMOTE}/job-outer/started.json").returncode == 0
    except BaseException:  # noqa: BLE001
        return False


def watch_cap_check(host: str, every: int = 120) -> None:
    """Log cap-risk when the job runner's CAP-CHECK.json projects less than its margin; the lead then asks the user."""
    remaining = (parse_utc(cap_stop(host)) - dt.datetime.now(dt.timezone.utc)).total_seconds()
    record = wait_file(host, "CAP-CHECK.json", int(max(remaining, 0)), every)
    log(host, "cap-risk" if record.get("cap_risk") else "cap-check-ok",
        projected_e1_upper_s=record.get("projected_e1_upper_s"), remaining_s=record.get("remaining_s"))


def status(host: str) -> None:
    out = ssh(host, f"cd {REMOTE} && ls -d round1/*/ 2>/dev/null; ls -d BOOTSTRAP-READY.json PREFLIGHT-DONE.json JOB-DONE.json "
                    "CAP-CHECK.json gated-download-receipt.json base-job.json cuda-preflight-* 2>/dev/null; "
                    "python3 -c \"import json;b=json.load(open('/workspace/.pod-timer/heartbeat.json'));"
                    "print('timer',b['state'],b['governing']['source'],b['governing']['stop_at_utc'],b['utc'])\"")
    print(out.stdout or out.stderr)


def main() -> int:
    command, host = sys.argv[1], sys.argv[2]
    {"after-create": after_create, "status": status, "check": check, "bootstrap": bootstrap,
     "start-job": start_job}[command](host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
