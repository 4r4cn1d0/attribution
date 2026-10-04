"""Verify copied units and stop finished hosts for the 4 October run (administrative). Never deletes.

Every INTERVAL seconds, for each host with hosts/HOST/pod.json and no hosts/HOST/finished.json:
1. verify_units.py HOST (the frozen engine's verify on every new sealed unit copied by monitor.py);
2. if both job receipts and the outer receipt exist in the copied tree:
   - all exit 0, all 6 units (q, e1, e3 for both seeds) sealed and verified: pull once more, re-verify,
     stop the pod (host.py stop) and write finished.json {"status": "completed"};
   - any non-zero exit: pull once more, verify what is sealed, stop the pod and write finished.json
     {"status": "failed"} for a later retry through the gated worker.
Events go to finisher.log. The stop timer stays the backstop for anything this misses.

    python3.11 finisher.py [INTERVAL_SECONDS]
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
INTERVAL = int(sys.argv[1]) if len(sys.argv) > 1 else 300
PLAN = json.loads((HERE.parents[1] / "tmp/study-v2-20261002/dev-matrix-assets/dev-matrix-plan.json").read_text())


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def event(**fields) -> None:
    print(json.dumps({"utc": now(), **fields}), flush=True)


def run(*args: str) -> int:
    return subprocess.run([sys.executable, *args], cwd=HERE, capture_output=True, text=True).returncode


def receipts(host: str) -> dict:
    tree = HERE / "retrieved" / host / "tree"
    found = {}
    for name in [f"dev-matrix-process-{j['seed']}-002" for j in PLAN["assignments"][host]] + ["dev-matrix-outer-002"]:
        path = tree / name / "process-receipt.json"
        if path.exists():
            found[name] = json.loads(path.read_text()).get("exit_code")
    return found


def verified(host: str) -> set:
    log = HERE / "retrieved" / host / "verified.jsonl"
    if not log.exists():
        return set()
    return {json.loads(line)["unit"] for line in log.read_text().splitlines() if json.loads(line).get("passed")}


def expected_units(host: str) -> int:
    return 3 * len(PLAN["assignments"][host])


def finish(host: str, status: str) -> None:
    run("host.py", "pull", host)
    subprocess.run([sys.executable, "-c", "import monitor; monitor.unpack(%r)" % host], cwd=HERE, capture_output=True)
    run("verify_units.py", host)
    units = sorted(verified(host))
    if status == "completed" and len(units) < expected_units(host):
        event(host=host, event="not-finishing", reason="final verification incomplete", verified=len(units))
        return
    stop = subprocess.run([sys.executable, "host.py", "stop", host], cwd=HERE, capture_output=True, text=True)
    record = {"utc": now(), "status": status, "verified_units": units, "receipts": receipts(host), "stop": stop.stdout.strip()}
    (HERE / "hosts" / host / "finished.json").write_text(json.dumps(record, indent=1) + "\n")
    event(host=host, event="finished", status=status, verified=len(units), stop=stop.stdout.strip())


def main() -> int:
    while True:
        hosts = sorted(p.parent.name for p in (HERE / "hosts").glob("*/pod.json") if not (p.parent / "finished.json").exists())
        for host in hosts:
            if (HERE / "retrieved" / host / "tree").exists():
                code = run("verify_units.py", host)
                if code:
                    event(host=host, event="verify-failed", note="a sealed unit failed the engine's verify; not stopping")
            r = receipts(host)
            needed = len(PLAN["assignments"][host]) + 1
            if len(r) == needed and all(v == 0 for v in r.values()):
                if len(verified(host)) >= expected_units(host):
                    finish(host, "completed")
            elif any(v not in (0, None) for v in r.values()):
                finish(host, "failed")
        if not hosts:
            event(event="nothing left to finish")
            return 0
        time.sleep(INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
