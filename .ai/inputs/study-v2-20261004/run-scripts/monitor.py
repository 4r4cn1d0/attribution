"""Off-pod copies for the 4 October run: pull every running host every INTERVAL seconds (administrative).

For each host with hosts/HOST/pod.json and no hosts/HOST/finished.json: host.py pull (a complete tar or nothing),
unpack the newest tar into retrieved/HOST/tree (swapped in only after a clean unpack), record sealed units
(folders with COMPLETE.json) and finished job receipts in retrieved/HOST/summary.json. Older tars beyond the
newest two are removed (they are this script's own redundant copies). Nothing here stops or deletes a pod.

    python3.11 monitor.py [INTERVAL_SECONDS]      runs until no host is left to watch
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import shutil
import subprocess
import sys
import tarfile
import time

HERE = pathlib.Path(__file__).resolve().parent
INTERVAL = int(sys.argv[1]) if len(sys.argv) > 1 else 300


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def watched() -> list[str]:
    return sorted(p.parent.name for p in (HERE / "hosts").glob("*/pod.json") if not (p.parent / "finished.json").exists())


def unpack(host: str) -> dict:
    out = HERE / "retrieved" / host
    tars = sorted(out.glob("pull-*.tar"))
    if not tars:
        return {}
    newest = tars[-1]
    staging = out / "tree.new"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir()
    with tarfile.open(newest) as t:
        t.extractall(staging, filter="data")
    tree = out / "tree"
    old = out / "tree.old"
    shutil.rmtree(old, ignore_errors=True)
    if tree.exists():
        tree.rename(old)
    staging.rename(tree)
    shutil.rmtree(old, ignore_errors=True)
    for extra in tars[:-2]:
        extra.unlink()
    units = sorted(p.parent.name for p in (tree / "dev-matrix-002").glob("*/COMPLETE.json"))
    receipts = {}
    for r in sorted(tree.glob("dev-matrix-*-002/process-receipt.json")):
        data = json.loads(r.read_text())
        receipts[r.parent.name] = {"exit_code": data.get("exit_code"), "elapsed_min": round(data.get("elapsed_s", 0) / 60, 1)}
    summary = {"utc": now(), "tar": newest.name, "sealed_units": units, "receipts": receipts}
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main() -> int:
    while True:
        hosts = watched()
        if not hosts:
            print(json.dumps({"utc": now(), "event": "nothing left to watch"}), flush=True)
            return 0
        for host in hosts:
            code = subprocess.run([sys.executable, str(HERE / "host.py"), "pull", host], capture_output=True).returncode
            try:
                summary = unpack(host) if code == 0 else {}
            except (tarfile.TarError, OSError) as exc:
                summary = {"unpack_error": type(exc).__name__}
            print(json.dumps({"utc": now(), "host": host, "pull_exit": code,
                              "sealed": len(summary.get("sealed_units", [])), "receipts": summary.get("receipts")}), flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
