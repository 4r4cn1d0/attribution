"""Run hosts of the 4 October development-matrix run (administrative; no experiment logic).

    orchestrate.py bootstrap HOST   send worker-setup-v3 (hash-checked), extract, start the 2 October bootstrap
    orchestrate.py start HOST       after BOOTSTRAP-VERIFIED: send the frozen matrix assets and run_dev_matrix_v2.py
                                    (hash-checked), verify the assets manifest, start both jobs in the background
    orchestrate.py status HOST      sealed units, receipts and the timer's heartbeat
    orchestrate.py full HOST        create, wait for SSH, check GPU and timer, bootstrap, wait, start

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
ROOT = HERE.parents[1]
HOST_TOOL = [sys.executable, str(HERE / "host.py")]
SETUP, SETUP_SHA = ROOT / "tmp/study-v2-20261002/worker-setup-v3.tar.gz", \
    "4a73f5c41c80cd340fe3e9340018b502af01d059cfeee499b4ce4b31d9fa8151"
ASSETS, ASSETS_SHA = ROOT / "tmp/study-v2-20261002/dev-matrix-assets.tar.gz", \
    "349668b7c3cab7843e31e4bb48e6206c7b6c0f2a4b074467439d0e93b9990048"
RUNNER = HERE / "run_dev_matrix_v2.py"
REMOTE = "/workspace/attribution-study-v2"
GPU = "NVIDIA A100-SXM4-80GB"


def log(host: str, event: str, **fields) -> None:
    record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "host": host, "event": event, **fields}
    (HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(HERE / "hosts" / host / "orchestrate.jsonl", "a") as handle:
        handle.write(json.dumps(record) + "\n")
    print(json.dumps(record), flush=True)


def tool(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run([*HOST_TOOL, *args], capture_output=capture, text=True)


def ssh(host: str, command: str) -> subprocess.CompletedProcess:
    return tool("ssh", host, command)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait_ssh(host: str, seconds: int = 900) -> None:
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
    if tool("send", host, str(SETUP), f"{REMOTE}/worker-setup-v3.tar.gz", SETUP_SHA).returncode:
        raise SystemExit(f"{host}: setup bundle transfer or hash check failed")
    command = (f"cd {REMOTE} && python3 - <<'REMOTE'\n"
               "import pathlib,hashlib,tarfile\n"
               f"p=pathlib.Path('worker-setup-v3.tar.gz');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{SETUP_SHA}'\n"
               "assert not pathlib.Path('worker-bootstrap-process-001').exists()\n"
               "with tarfile.open(p) as t:t.extractall('.',filter='data')\n"
               "REMOTE\n"
               "nohup python3 process_receipt.py --out worker-bootstrap-process-001 -- bash worker_bootstrap_v3.sh "
               "> bootstrap-outer.log 2>&1 &\nsleep 3; test -f worker-bootstrap-process-001/started.json")
    if ssh(host, command).returncode:
        raise SystemExit(f"{host}: bootstrap did not start")
    log(host, "bootstrap-started")


def wait_verified(host: str, seconds: int = 3600) -> None:
    deadline = time.time() + seconds
    probe = (f"cd {REMOTE} && if [ -f worker-bootstrap-process-001/process-receipt.json ]; then "
             "python3 -c \"import json;r=json.load(open('worker-bootstrap-process-001/process-receipt.json'));"
             "print('exit',r.get('exit_code'),'min',round(r.get('elapsed_s',0)/60,1))\"; "
             "python3 -c \"import json;print('fixture_exact',json.load(open('BOOTSTRAP-VERIFIED.json'))['fixture_exact'])\" "
             "2>/dev/null || echo fixture_exact missing; else echo running; fi")
    while time.time() < deadline:
        out = ssh(host, probe).stdout
        if out.startswith("exit"):
            ok = out.startswith("exit 0") and "fixture_exact True" in out
            log(host, "bootstrap-finished", result=out.strip().replace("\n", " | "))
            if not ok:
                raise SystemExit(f"{host}: bootstrap failed or fixture not exact: {out.strip()}")
            return
        time.sleep(60)
    raise SystemExit(f"{host}: bootstrap not finished within {seconds} s")


def start(host: str) -> None:
    if tool("send", host, str(ASSETS), f"{REMOTE}/dev-matrix-assets.tar.gz", ASSETS_SHA).returncode:
        raise SystemExit(f"{host}: matrix assets transfer or hash check failed")
    if tool("send", host, str(RUNNER), f"{REMOTE}/run_dev_matrix_v2.py", sha(RUNNER)).returncode:
        raise SystemExit(f"{host}: runner transfer or hash check failed")
    command = (f"cd {REMOTE} && python3 - <<'REMOTE'\n"
               "import pathlib,tarfile,hashlib,json\n"
               f"p=pathlib.Path('dev-matrix-assets.tar.gz');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{ASSETS_SHA}'\n"
               "assert not pathlib.Path('dev-matrix-plan.json').exists()\n"
               "with tarfile.open(p) as t:t.extractall('.',filter='data')\n"
               "for n,h in json.loads(pathlib.Path('dev-matrix-assets-manifest.json').read_text()).items():"
               "assert hashlib.sha256(pathlib.Path(n).read_bytes()).hexdigest()==h,n\n"
               "assert pathlib.Path('BOOTSTRAP-VERIFIED.json').exists() and not pathlib.Path('dev-matrix-outer-002').exists()\n"
               "REMOTE\n"
               f"nohup python3 process_receipt.py --out dev-matrix-outer-002 -- venv/bin/python run_dev_matrix_v2.py {host} "
               "> matrix-outer.log 2>&1 &\nsleep 20; test -f dev-matrix-outer-002/started.json && "
               "test ! -f dev-matrix-outer-002/process-receipt.json")
    if ssh(host, command).returncode:
        out = ssh(host, f"cd {REMOTE} && tail -20 dev-matrix-outer-002/process.log 2>/dev/null").stdout
        raise SystemExit(f"{host}: jobs did not start or stopped at once:\n{out}")
    log(host, "jobs-started", runner_sha256=sha(RUNNER))


def status(host: str) -> None:
    out = ssh(host, f"cd {REMOTE} && ls -d dev-matrix-002/*/ 2>/dev/null | while read d; do "
                    "[ -f \"$d/COMPLETE.json\" ] && echo \"sealed $d\" || echo \"open   $d\"; done; "
                    "for r in dev-matrix-process-*-002 dev-matrix-outer-002; do [ -f $r/process-receipt.json ] && "
                    "echo \"receipt $r\" && cat $r/process-receipt.json | tr -d '\\n' | cut -c1-200 && echo; done; "
                    "python3 -c \"import json;b=json.load(open('/workspace/.pod-timer/heartbeat.json'));"
                    "print('timer',b['state'],b['governing']['source'],b['governing']['stop_at_utc'],b['utc'])\"")
    print(out.stdout or out.stderr)


def full(host: str) -> None:
    created = tool("create", host)
    if created.returncode:
        raise SystemExit(f"{host}: create failed: {created.stdout[-400:]} {created.stderr[-400:]}")
    log(host, "created")
    after_create(host)


def after_create(host: str) -> None:
    wait_ssh(host)
    check(host)
    bootstrap(host)
    wait_verified(host)
    start(host)


def main() -> int:
    command, host = sys.argv[1:3]
    {"bootstrap": bootstrap, "start": start, "status": status, "full": full, "after-create": after_create,
     "check": check, "wait": wait_verified}[command](host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
