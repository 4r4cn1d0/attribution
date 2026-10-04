"""Verify copied sealed units of one host with the frozen engine's own verify (administrative).

    python3.11 verify_units.py HOST

For every unit folder with COMPLETE.json in retrieved/HOST/tree/dev-matrix-002 not yet verified, run
    experiments.safety_selection verify --run UNIT --prepared MIRROR/prepared-v2 --map dev-matrix-002=TREE/dev-matrix-002
with the pinned engine environment and the frozen engine source of the verified mirror (cwd = mirror). A passing
unit is copied, as it was verified, to retrieved/HOST/verified/UNIT (never overwritten) and recorded in
retrieved/HOST/verified.jsonl. Exit 0 when every sealed unit present has passed.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
MIRROR = HERE / "mirror"


def main(host: str) -> int:
    out = HERE / "retrieved" / host
    tree = out / "tree"
    log = out / "verified.jsonl"
    done = set()
    if log.exists():
        done = {json.loads(line)["unit"] for line in log.read_text().splitlines() if json.loads(line).get("passed")}
    units = sorted(p.parent for p in (tree / "dev-matrix-002").glob("*/COMPLETE.json"))
    failures = 0
    for unit in units:
        if unit.name in done:
            continue
        snapshot = out / "verify-staging" / unit.name
        shutil.rmtree(out / "verify-staging", ignore_errors=True)
        shutil.copytree(tree / "dev-matrix-002", out / "verify-staging" / "dev-matrix-002", symlinks=False)
        staged = out / "verify-staging" / "dev-matrix-002" / unit.name
        result = subprocess.run([str(PY), "-m", "experiments.safety_selection", "verify", "--run", str(staged),
                                 "--prepared", str(MIRROR / "prepared-v2"),
                                 "--map", f"dev-matrix-002={out / 'verify-staging' / 'dev-matrix-002'}",
                                 "--map", f"/workspace/attribution-study-v2/dev-matrix-002={out / 'verify-staging' / 'dev-matrix-002'}"],
                                cwd=MIRROR, capture_output=True, text=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(MIRROR)})
        passed = result.returncode == 0
        record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "unit": unit.name, "passed": passed,
                  "exit": result.returncode, "output_tail": (result.stdout + result.stderr)[-1500:]}
        if passed:
            keep = out / "verified" / unit.name
            if not keep.exists():
                shutil.copytree(staged, keep)
        else:
            failures += 1
        with open(log, "a") as handle:
            handle.write(json.dumps(record) + "\n")
        print(json.dumps({k: record[k] for k in ("unit", "passed", "exit")}))
        _ = snapshot
    shutil.rmtree(out / "verify-staging", ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
