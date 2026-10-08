"""Drive the headroom-v2 hosts (administrative; no experiment logic).

    orchestrate.py after-create HOST   wait for SSH, check GPU and timer, bootstrap, wait until ready, run the preflight,
                                       then by role:
                                         first: record the chosen recipe and the expected fixture, then start its job
                                         job:   wait for the expected fixture (and its edit file), then start its job
                                         lead:  wait for the expected fixture, then start the lead pipeline
    orchestrate.py full HOST           create (through the budget guard in launch.py), then after-create
    orchestrate.py collect-lead        fetch the lead's edit files (removal files first, then all) into edits/
    orchestrate.py status HOST         receipts and the timer's heartbeat

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
SETUP = HERE / "setup/worker-setup-v2.tar.gz"
EXPECTED = HERE / "expected-fixture-v2.json"
EDITS = HERE / "edits"


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


def tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([*HOST_TOOL, *args], capture_output=True, text=True)


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
    deadline = time.time() + seconds
    while time.time() < deadline:
        out = ssh(host, f"cat {REMOTE}/{remote_file} 2>/dev/null")
        if out.returncode == 0 and out.stdout.strip():
            return json.loads(out.stdout)
        time.sleep(every)
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
    if tool("send", host, str(SETUP), f"{REMOTE}/worker-setup-v2.tar.gz", receipt["setup"]["sha256"]).returncode:
        raise SystemExit(f"{host}: setup transfer or hash check failed")
    unpack = (f"cd {REMOTE} && python3 - <<'REMOTE'\n"
              "import pathlib,hashlib,tarfile\n"
              f"p=pathlib.Path('worker-setup-v2.tar.gz');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{receipt['setup']['sha256']}'\n"
              "assert not pathlib.Path('worker-bootstrap-process-001').exists()\n"
              "with tarfile.open(p) as t:t.extractall('.',filter='data')\n"
              "REMOTE")
    if ssh(host, unpack).returncode:
        raise SystemExit(f"{host}: setup unpack failed")
    extra = " --with-generator" if plan()["hosts"][host]["role"] == "lead" else ""
    start_background(host, "worker-bootstrap-process-001", f"bash worker_bootstrap_v2.sh{extra}")
    log(host, "bootstrap-started", generator=bool(extra))


def preflight(host: str) -> dict:
    p = plan()
    recipes = p["first_host_recipes"] if p["hosts"][host]["role"] == "first" else [p["recipe_path"]]
    p_host = dict(p); p_host["preflight_recipes"] = recipes
    local = HERE / "hosts" / host / "plan-preflight.json"
    local.write_text(json.dumps(p_host, indent=1, sort_keys=True) + "\n")
    send(host, local, "plan.json")
    start_background(host, "preflight-outer", "venv/bin/python preflight_v2.py")
    done = wait_file(host, "PREFLIGHT-DONE.json", 3600)
    log(host, "preflight-finished", ok=done["ok"], recipe=done["recipe"], tried=[(t["recipe"], t["verdict"].get("use_this_recipe")) for t in done["tried"]])
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
    subprocess.run([sys.executable, str(HERE / "plan_tool.py"), "set-recipe", done["recipe"]], check=True)
    log(host, "expected-fixture-recorded", sha256=sha(EXPECTED), recipe=done["recipe"])


def start_job(host: str) -> None:
    job = plan()["hosts"][host]
    send(host, HERE / "plan.json", "plan.json")
    send(host, EXPECTED, "expected-fixture-v2.json")
    if job.get("edit"):
        local = EDITS / job["edit"]
        if sha(local) != job["edit_sha256"]:
            raise SystemExit(f"{host}: local edit file is not the planned one")
        send(host, local, f"edits/{job['edit']}")
    start_background(host, "job-outer", f"venv/bin/python job_runner.py {host}")
    log(host, "job-started", plan_sha256=sha(HERE / "plan.json"), edit=job.get("edit"), prepared=job.get("prepared"))


def start_lead(host: str) -> None:
    send(host, HERE / "plan.json", "plan.json")
    start_background(host, "lead-outer", "venv/bin/python lead_pipeline.py")
    log(host, "lead-started", plan_sha256=sha(HERE / "plan.json"))


def wait_for(condition, what: str, seconds: int = 6 * 3600) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if condition():
            return
        time.sleep(30)
    raise SystemExit(f"waited {seconds} s for {what}")


def ready(host: str) -> bool:
    p = plan(); job = p["hosts"][host]
    if not EXPECTED.exists() or not p.get("recipe_path"):
        return False
    if job.get("edit"):
        local = EDITS / job["edit"]
        return bool(job.get("edit_sha256")) and local.exists() and sha(local) == job["edit_sha256"]
    return True


def after_create(host: str) -> None:
    role = plan()["hosts"][host]["role"]
    if role != "first":
        wait_for(lambda: EXPECTED.exists() and bool(plan().get("recipe_path")), f"{host}: the first host's recipe choice")
    wait_ssh(host)
    check(host)
    bootstrap(host)
    ready_rec = wait_file(host, "BOOTSTRAP-READY.json", 3600)
    log(host, "bootstrap-ready", engine=ready_rec.get("engine_sha256", "")[:16])
    done = preflight(host)
    if role == "first":
        record_first(host, done)
        start_job(host)
    elif role == "lead":
        start_lead(host)
    else:
        wait_for(lambda: ready(host), f"{host}: edit file")
        start_job(host)


def collect_lead() -> None:
    p = plan(); lead = next(h for h, j in p["hosts"].items() if j["role"] == "lead")
    EDITS.mkdir(exist_ok=True)
    for stage, folder in (("early", p["early_edits_dir"]), ("final", p["final_edits_dir"])):
        listing = ssh(lead, f"cd {REMOTE} && test -f {folder}/index.json && ls {folder}")
        if listing.returncode:
            print(json.dumps({"stage": stage, "present": False})); continue
        names = [n for n in listing.stdout.split() if n in p["edit_files"]]
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
    out = ssh(host, f"cd {REMOTE} && ls -d round1/*/ 2>/dev/null; ls -d BOOTSTRAP-READY.json PREFLIGHT-DONE.json LEAD-DONE.json JOB-DONE.json "
                    "scores-* rewrites-* edits-* cuda-preflight-* 2>/dev/null; "
                    "python3 -c \"import json;b=json.load(open('/workspace/.pod-timer/heartbeat.json'));"
                    "print('timer',b['state'],b['governing']['source'],b['governing']['stop_at_utc'],b['utc'])\"")
    print(out.stdout or out.stderr)


def main() -> int:
    command = sys.argv[1]
    if command == "collect-lead":
        collect_lead(); return 0
    host = sys.argv[2]
    {"after-create": after_create, "status": status, "check": check, "bootstrap": bootstrap,
     "start-job": start_job, "start-lead": start_lead}[command](host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
