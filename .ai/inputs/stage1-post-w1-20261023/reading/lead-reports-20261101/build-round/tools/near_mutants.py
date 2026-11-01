"""Scratch harness (not part of the repository). Applies chosen mutants of B14's spec in a run copy laid out as
scripts/stage1_s1/mutation/run_mutants_b14.py lays it out (scripts/stage1 unchanged, scripts/stage1_s1 mutated,
PYTHONPATH copy:workspace, cwd the copy, the import probe) and runs a SUBSET of the tests: the B14 test files. A kill
here is a kill in the full run (its tests are a superset); a survivor here may still die in the full suite.
Outcomes follow T1's rules: killed = exit 1 with failures and no errors; survived = exit 0; anything else invalid.

    python3 near_mutants.py WORKTREE SCRATCH REPORT PYTHON [-j N] [--tests a,b] ID_OR_PREFIX...
"""

import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

args = sys.argv[1:]
jobs = 4
tests = ["test_b14_pins.py", "test_b14_report.py", "test_b14_strata.py", "test_b14_inputs.py"]
if "-j" in args:
    i = args.index("-j")
    jobs = int(args[i + 1])
    del args[i:i + 2]
if "--tests" in args:
    i = args.index("--tests")
    tests = args[i + 1].split(",")
    del args[i:i + 2]
ws, scratch, report_path, python, *wanted = args
ws, scratch = Path(ws).resolve(), Path(scratch).resolve()
spec = json.loads((ws / "scripts/stage1_s1/mutation/mutants_b14.json").read_text())
chosen = [m for m in spec["mutants"] if any(m["id"] == w or (w.endswith("*") and m["id"].startswith(w[:-1]))
                                            for w in wanted)]


def edits_of(m):
    return m["edits"] if "edits" in m else [{"file": m["file"], "find": m["find"], "replace": m["replace"]}]


def run(run_id, mutant):
    folder = scratch / run_id
    if folder.exists():
        shutil.rmtree(folder)
    copy = folder / "copy"
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(ws / "scripts/stage1", copy / "scripts/stage1", ignore=ignore)
    shutil.copytree(ws / "scripts/stage1_s1", copy / "scripts/stage1_s1", ignore=ignore)
    tree = copy / "scripts/stage1_s1"
    try:
        if mutant is not None:
            for e in edits_of(mutant):
                target = tree / e["file"]
                text = target.read_text()
                if text.count(e["find"]) != 1:
                    return {"outcome": "invalid", "reason": f"find occurs {text.count(e['find'])} times"}
                target.write_text(text.replace(e["find"], e["replace"]))
        env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=f"{copy}{os.pathsep}{ws}")
        probe = subprocess.run([python, "-B", "-c", "import scripts.stage1_s1.overlap_strata as m; print(m.__file__)"],
                               cwd=copy, env=env, capture_output=True, text=True)
        if probe.returncode != 0 or not probe.stdout.strip().startswith(str(copy)):
            return {"outcome": "invalid", "reason": "probe"}
        junit = folder / "junit.xml"
        start = time.monotonic()
        proc = subprocess.run([python, "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
                               f"--basetemp={folder / 'bt'}", f"--junitxml={junit}",
                               *[str(tree / "tests" / t) for t in tests]],
                              cwd=copy, env=env, capture_output=True, text=True, timeout=900)
        seconds = round(time.monotonic() - start, 1)
        if not junit.is_file():
            return {"outcome": "invalid", "reason": "no junit", "exit": proc.returncode}
        root = ET.parse(junit).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        counts = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
        tail = proc.stdout[-600:]
        if proc.returncode == 0 and counts["failures"] == 0 and counts["errors"] == 0:
            outcome = "survived" if mutant is not None else "pass"
        elif proc.returncode == 1 and counts["failures"] >= 1 and counts["errors"] == 0:
            outcome = "killed" if mutant is not None else "fail"
        else:
            outcome = "invalid"
        first = [ln for ln in proc.stdout.splitlines() if ln.startswith("FAILED") or ln.startswith("ERROR")][:1]
        return {"outcome": outcome, "exit": proc.returncode, "seconds": seconds, **counts, "first": first,
                **({"tail": tail} if outcome in ("invalid", "fail") else {})}
    finally:
        shutil.rmtree(folder, ignore_errors=True)


scratch.mkdir(parents=True, exist_ok=True)
results = {"baseline": run("baseline", None)}
print("baseline", json.dumps(results["baseline"]), flush=True)
if results["baseline"]["outcome"] != "pass":
    sys.exit("baseline did not pass")
with cf.ThreadPoolExecutor(max_workers=jobs) as pool:
    futures = {pool.submit(run, m["id"], m): m["id"] for m in chosen}
    for f in cf.as_completed(futures):
        results[futures[f]] = f.result()
        r = results[futures[f]]
        print(f"{futures[f]}: {r['outcome']} ({r.get('seconds')} s) {r.get('first') or r.get('reason') or ''}",
              flush=True)
summary = {}
for k, v in results.items():
    if k != "baseline":
        summary[v["outcome"]] = summary.get(v["outcome"], 0) + 1
Path(report_path).write_text(json.dumps({"tests": tests, "summary": summary, "results": results}, indent=1,
                                        sort_keys=True) + "\n")
print("summary", summary)
shutil.rmtree(scratch, ignore_errors=True)
