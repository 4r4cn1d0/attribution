"""Spot-check mutants in run_mutants_b14.py's layout (scripts/stage1 unchanged, scripts/stage1_s1 mutated,
PYTHONPATH copy:workspace), on the B14 test files only. Outcome rules as T1's: killed = pytest exit 1 (a test failed);
survived = exit 0; anything else invalid.

    python -B spot_mutants.py WS SCRATCH ID [ID ...]      (ids from the spec, or VB-* defined here)"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

WS, SCRATCH = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
IDS = sys.argv[3:]
SPEC = {m["id"]: m for m in json.loads((WS / "scripts/stage1_s1/mutation/mutants_b14.json").read_text())["mutants"]}
OWN = {
    "VB-absolute": [{"file": "overlap_inputs.py",
                     "find": "root, real = Path(data_root).resolve(), Path(folder).resolve()",
                     "replace": "root, real = Path(data_root).absolute(), Path(folder).absolute()"}],
    "VB-engine-arm-ignored": [{"file": "overlap_inputs.py",
                               "find": "if (edit.get(\"engine_arm\") or f\"edit-{edit['sha256']}\") != want_arm:",
                               "replace": "if f\"edit-{edit['sha256']}\" != want_arm:"}],
}
TESTS = ["test_b14_inputs.py", "test_b14_pins.py", "test_b14_report.py", "test_b14_strata.py"]


def edits(mid):
    if mid in OWN:
        return OWN[mid]
    m = SPEC[mid]
    return m.get("edits") or [{"file": m["file"], "find": m["find"], "replace": m["replace"]}]


def run(mid):
    folder = SCRATCH / mid
    if folder.exists():
        shutil.rmtree(folder)
    copy = folder / "copy"
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(WS / "scripts/stage1", copy / "scripts/stage1", ignore=ignore)
    shutil.copytree(WS / "scripts/stage1_s1", copy / "scripts/stage1_s1", ignore=ignore)
    if mid != "baseline":
        for e in edits(mid):
            t = copy / "scripts/stage1_s1" / e["file"]
            text = t.read_text()
            if text.count(e["find"]) != 1:
                return {"id": mid, "outcome": "invalid", "reason": f"find occurs {text.count(e['find'])} times"}
            t.write_text(text.replace(e["find"], e["replace"]))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=f"{copy}{os.pathsep}{WS}")
    probe = subprocess.run([sys.executable, "-B", "-c", "import scripts.stage1_s1.overlap_inputs as m; print(m.__file__)"],
                           cwd=copy, env=env, capture_output=True, text=True)
    if not probe.stdout.strip().startswith(str(copy)):
        return {"id": mid, "outcome": "invalid", "reason": "probe: " + (probe.stdout + probe.stderr)[-200:]}
    start = time.time()
    p = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "-W", "ignore",
                        f"--basetemp={folder / 'bt'}", *[str(copy / 'scripts/stage1_s1/tests' / t) for t in TESTS]],
                       cwd=copy, env=env, capture_output=True, text=True)
    outcome = {0: "survived", 1: "killed"}.get(p.returncode, "invalid")
    first = next((ln for ln in p.stdout.splitlines() if ln.startswith("FAILED")), "")
    shutil.rmtree(folder, ignore_errors=True)
    return {"id": mid, "outcome": outcome, "exit": p.returncode, "s": round(time.time() - start, 1),
            "first_failure": first[:160], "tail": p.stdout.strip().splitlines()[-1][:120] if p.stdout.strip() else ""}


for mid in IDS:
    print(json.dumps(run(mid)), flush=True)
