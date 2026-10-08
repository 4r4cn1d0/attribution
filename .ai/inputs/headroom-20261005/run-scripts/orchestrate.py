"""Drive the round-1 hosts of the headroom positive control (administrative; no experiment logic).

    orchestrate.py after-create HOST   wait for SSH, check GPU and timer, bootstrap, wait for the fixture, then:
                                       lead: record the expected fixture locally and start the lead pipeline;
                                       job:  wait for the expected fixture (and its edit file), then start the job
    orchestrate.py full HOST           create, then after-create
    orchestrate.py collect-lead        fetch the lead's edit files (removal files first, then all) into edits/
    orchestrate.py status HOST         the host's receipts and the timer's heartbeat

Every step stops at the first failed check. The pod is never deleted; host.py stop is the only stop.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
HOST_TOOL = [sys.executable, str(HERE / "host.py")]
REMOTE = "/workspace/attribution-headroom"
GPU = "NVIDIA A100-SXM4-80GB"
SETUP = HERE / "setup/worker-setup-hr.tar.gz"
EXPECTED = HERE / "expected-fixture-hr.json"
EDITS = HERE / "edits"


def plan() -> dict:
    return json.loads((HERE / "plan.json").read_text())


def log(host: str, event: str, **fields) -> None:
    record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "host": host, "event": event, **fields}
    (HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(HERE / "hosts" / host / "orchestrate.jsonl", "a") as handle:
        handle.write(json.dumps(record) + "\n")
    print(json.dumps(record), flush=True)


def tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([*HOST_TOOL, *args], capture_output=True, text=True)


def ssh(host: str, command: str) -> subprocess.CompletedProcess:
    return tool("ssh", host, command)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def send(host: str, local: pathlib.Path, remote_name: str) -> None:
    if tool("send", host, str(local), f"{REMOTE}/{remote_name}", sha(local)).returncode:
        raise SystemExit(f"{host}: transfer or hash check of {remote_name} failed")


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
    if tool("send", host, str(SETUP), f"{REMOTE}/worker-setup-hr.tar.gz", receipt["setup"]["sha256"]).returncode:
        raise SystemExit(f"{host}: setup transfer or hash check failed")
    extra = " --with-generator" if plan()["hosts"][host]["role"] == "lead" else ""
    command = (f"cd {REMOTE} && python3 - <<'REMOTE'\n"
               "import pathlib,hashlib,tarfile\n"
               f"p=pathlib.Path('worker-setup-hr.tar.gz');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{receipt['setup']['sha256']}'\n"
               "assert not pathlib.Path('worker-bootstrap-process-001').exists()\n"
               "with tarfile.open(p) as t:t.extractall('.',filter='data')\n"
               "REMOTE\n"
               f"nohup python3 process_receipt.py --out worker-bootstrap-process-001 -- bash worker_bootstrap_hr.sh{extra} "
               "> bootstrap-outer.log 2>&1 &\nsleep 3; test -f worker-bootstrap-process-001/started.json")
    if ssh(host, command).returncode:
        raise SystemExit(f"{host}: bootstrap did not start")
    log(host, "bootstrap-started", generator=bool(extra))


def wait_verified(host: str, seconds: int = 3600) -> None:
    deadline = time.time() + seconds
    probe = (f"cd {REMOTE} && if [ -f worker-bootstrap-process-001/process-receipt.json ]; then "
             "python3 -c \"import json;r=json.load(open('worker-bootstrap-process-001/process-receipt.json'));"
             "print('exit',r.get('exit_code'),'min',round(r.get('elapsed_s',0)/60,1))\"; "
             "python3 -c \"import json;print('preflight_ok',json.load(open('PREFLIGHT-DONE.json'))['ok'])\" "
             "2>/dev/null || echo preflight_ok missing; else echo running; fi")
    while time.time() < deadline:
        out = ssh(host, probe).stdout
        if out.startswith("exit"):
            ok = out.startswith("exit 0") and "preflight_ok True" in out
            log(host, "bootstrap-finished", result=out.strip().replace("\n", " | "))
            if not ok:
                raise SystemExit(f"{host}: bootstrap failed or fixture not exact: {out.strip()}")
            return
        time.sleep(60)
    raise SystemExit(f"{host}: bootstrap not finished within {seconds} s")


def record_fixture(host: str) -> None:
    if EXPECTED.exists():
        raise SystemExit("an expected fixture is already recorded")
    target = HERE / "hosts" / host / "verification.json"
    if tool("fetch", host, f"{REMOTE}/cuda-preflight-hr-001/verification.json", str(target)).returncode:
        raise SystemExit(f"{host}: could not fetch the fixture")
    EXPECTED.write_bytes(target.read_bytes())
    log(host, "expected-fixture-recorded", sha256=sha(EXPECTED))


def compare_fixture(host: str) -> None:
    target = HERE / "hosts" / host / "verification.json"
    if tool("fetch", host, f"{REMOTE}/cuda-preflight-hr-001/verification.json", str(target)).returncode:
        raise SystemExit(f"{host}: could not fetch the fixture")
    x, e, keys = json.loads(target.read_text()), json.loads(EXPECTED.read_text()), plan()["fixture_compare"]
    bad = [k for k in keys["equal_keys"] if x[k] != e[k]] + [f"resume.{k}" for k in keys["resume_keys"] if x["resume"][k] != e["resume"][k]]
    if bad:
        raise SystemExit(f"{host}: fixture differs from the recorded one: {bad}")
    log(host, "fixture-matches-expected", sha256=sha(target))


def start_lead(host: str) -> None:
    send(host, HERE / "plan.json", "plan.json")
    command = (f"cd {REMOTE} && test ! -e lead-outer || exit 1\nnohup python3 process_receipt.py --out lead-outer -- "
               "venv/bin/python lead_pipeline.py > lead-outer.log 2>&1 < /dev/null &\nsleep 20; "
               f"cd {REMOTE} && test -f lead-outer/started.json && test ! -f lead-outer/process-receipt.json")
    if ssh(host, command).returncode:
        out = ssh(host, f"cd {REMOTE} && tail -20 lead-outer/process.log 2>/dev/null").stdout
        raise SystemExit(f"{host}: lead pipeline did not start or stopped at once:\n{out}")
    log(host, "lead-started", plan_sha256=sha(HERE / "plan.json"))


def start_job(host: str) -> None:
    job = plan()["hosts"][host]
    send(host, HERE / "plan.json", "plan.json")
    send(host, EXPECTED, "expected-fixture-hr.json")
    if job.get("edit"):
        local = EDITS / job["edit"]
        if sha(local) != job["edit_sha256"]:
            raise SystemExit(f"{host}: local edit file is not the planned one")
        send(host, local, f"edits/{job['edit']}")
    command = (f"cd {REMOTE} && test ! -e job-outer || exit 1\nnohup python3 process_receipt.py --out job-outer -- "
               f"venv/bin/python job_runner.py {host} > job-outer.log 2>&1 < /dev/null &\nsleep 30; "
               f"cd {REMOTE} && test -f job-outer/started.json && test ! -f job-outer/process-receipt.json")
    if ssh(host, command).returncode:
        out = ssh(host, f"cd {REMOTE} && tail -20 job-outer/process.log 2>/dev/null").stdout
        raise SystemExit(f"{host}: job did not start or stopped at once:\n{out}")
    log(host, "job-started", plan_sha256=sha(HERE / "plan.json"), edit=job.get("edit"))


def wait_for(condition, what: str, seconds: int = 4 * 3600) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if condition():
            return
        time.sleep(30)
    raise SystemExit(f"waited {seconds} s for {what}")


def ready(host: str) -> bool:
    job = plan()["hosts"][host]
    if not EXPECTED.exists():
        return False
    if job.get("edit"):
        local = EDITS / job["edit"]
        return bool(job.get("edit_sha256")) and local.exists() and sha(local) == job["edit_sha256"]
    return True


def after_create(host: str) -> None:
    wait_ssh(host)
    check(host)
    bootstrap(host)
    wait_verified(host)
    if plan()["hosts"][host]["role"] == "lead":
        if EXPECTED.exists():          # a replacement lead must reproduce the recorded fixture, not record a new one
            compare_fixture(host)
        else:
            record_fixture(host)
        start_lead(host)
        return
    wait_for(lambda: ready(host), f"{host}: expected fixture and edit file")
    start_job(host)


def continue_job(host: str) -> None:
    """After a bootstrap that already finished: wait for the fixture (and edit file), then start the job."""
    wait_verified(host)
    wait_for(lambda: ready(host), f"{host}: expected fixture and edit file")
    start_job(host)


def collect_lead() -> None:
    lead = next(h for h, j in plan()["hosts"].items() if j["role"] == "lead")
    EDITS.mkdir(exist_ok=True)
    p = plan()
    for stage, folder in (("early", p["early_edits_dir"]), ("final", p["final_edits_dir"])):
        listing = ssh(lead, f"cd {REMOTE} && test -f {folder}/index.json && ls {folder}")
        if listing.returncode:
            print(json.dumps({"stage": stage, "present": False})); continue
        names = [n for n in listing.stdout.split() if n in p["round1_edit_files"]]
        for name in names:
            target = EDITS / f"{stage}-{name}"
            if not target.exists() and tool("fetch", lead, f"{REMOTE}/{folder}/{name}", str(target)).returncode:
                raise SystemExit(f"fetch of {folder}/{name} failed")
            final = EDITS / name
            if final.exists() and sha(final) != sha(target):
                raise SystemExit(f"{name}: differs from the copy already collected")
            if not final.exists():
                final.write_bytes(target.read_bytes())
        print(json.dumps({"stage": stage, "present": True, "files": {n: sha(EDITS / n) for n in names}}))


def status(host: str) -> None:
    out = ssh(host, f"cd {REMOTE} && ls -d round1/*/ 2>/dev/null | while read d; do "
                    "[ -f \"$d/COMPLETE.json\" ] && echo \"sealed $d\" || echo \"open   $d\"; done; "
                    "for r in worker-bootstrap-process-001 lead-outer job-outer lead-process-* job-process-*; do "
                    "[ -f $r/process-receipt.json ] && echo \"receipt $r $(tr -d '\\n' < $r/process-receipt.json | cut -c1-160)\"; done; "
                    "ls -d scores-* rewrites-* edits-* LEAD-DONE.json JOB-DONE.json 2>/dev/null; "
                    "python3 -c \"import json;b=json.load(open('/workspace/.pod-timer/heartbeat.json'));"
                    "print('timer',b['state'],b['governing']['source'],b['governing']['stop_at_utc'],b['utc'])\"")
    print(out.stdout or out.stderr)


def full(host: str) -> None:
    created = tool("create", host)
    if created.returncode:
        raise SystemExit(f"{host}: create failed: {created.stdout[-400:]} {created.stderr[-400:]}")
    log(host, "created")
    after_create(host)


def main() -> int:
    command = sys.argv[1]
    if command == "collect-lead":
        collect_lead(); return 0
    host = sys.argv[2]
    {"full": full, "after-create": after_create, "continue-job": continue_job, "status": status, "bootstrap": bootstrap, "wait": wait_verified,
     "check": check, "fixture": record_fixture, "start-lead": start_lead, "start-job": start_job}[command](host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
