"""Mutation runner for the B16 input builder (test tooling; standard library only). B16's runner
(scripts/stage1_s1/reading/mutation/run_mutants.py) with its tree changed to scripts/stage1_s1/reading_input: the same
rules and spec format as scripts/stage1/mutation/run_mutants.py.

Rules: first an unmutated baseline with exactly the runner's command and temp layout; whole test files, no -x;
--junitxml; a per-mutant timeout. A mutant is KILLED only when pytest exits 1 with at least one test failure and no
error. A collection, setup or teardown error, a timeout, a missing JUnit file, an exit code outside 0-1, a JUnit test
count that differs from the baseline's, or a failure that carries errno 28 or 122 makes the run INVALID, never a
kill. Exit 0 with no failure is SURVIVED. A spec entry with "expect": "survive" must survive.

Each run copies <workspace>/scripts/stage1_s1 (the whole package, since the merged layout gives it an __init__.py;
the builder is <copy>/scripts/stage1_s1/reading_input) into its own folder under --scratch, applies the mutant's exact
text replacements to files under reading_input/ (one "find"/"replace" pair, or a list
"edits"; each find text must occur exactly once in its file), and runs pytest on the copy's tests with
PYTHONPATH = <copy>:<workspace>, so the copy's scripts.stage1_s1 shadows the workspace's and the engine, the kit's
rules and scripts.stage1 come from the workspace. The workspace is never changed. --only runs a comma-separated
subset of mutant ids (a shard); every shard runs its own baseline. The report (JSON) holds ids, outcomes, counts,
hashes and test names only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
READING = HERE.parent                                   # scripts/stage1_s1/reading_input
WORKSPACE = READING.parents[2]
REL = Path("scripts") / "stage1_s1" / "reading_input"
DISK_FULL = re.compile(r"Errno 28\b|Errno 122\b|ENOSPC|EDQUOT|No space left on device|Disk quota exceeded")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def junit_counts(path: Path) -> dict:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    out = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "failing": [], "erroring": [], "disk_full": False}
    for suite in suites:
        for key in ("tests", "failures", "errors", "skipped"):
            out[key] += int(suite.get(key, 0))
        for case in suite.iter("testcase"):
            name = f"{case.get('classname')}::{case.get('name')}"
            for tag, key in (("failure", "failing"), ("error", "erroring")):
                node = case.find(tag)
                if node is not None:
                    out[key].append(name)
                    if DISK_FULL.search(f"{node.get('message', '')}\n{node.text or ''}"):
                        out["disk_full"] = True
    return out


def clean_env(copy: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    return {**env, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": f"{copy}{os.pathsep}{WORKSPACE}"}


def tree_hashes(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


def edits_of(mutant: dict) -> list:
    if "edits" in mutant:
        return mutant["edits"]
    return [{"file": mutant["file"], "find": mutant["find"], "replace": mutant["replace"]}]


def run_one(run_id: str, mutant, scratch: Path, python: str, timeout: int, expected_tests=None) -> dict:
    folder = scratch / run_id
    if folder.exists():
        shutil.rmtree(folder)
    copy = folder / "copy"
    tree = copy / REL
    # The copy holds the whole scripts/stage1_s1 package (a copy of reading_input/ alone would be shadowed by the
    # workspace's regular package); only reading_input/ is mutated and only reading_input/tests runs.
    shutil.copytree(READING.parent, tree.parent, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    targets = {}
    if mutant is not None:
        for edit in edits_of(mutant):
            target = tree / edit["file"]
            before = sha256(target)
            text = target.read_text()
            if text.count(edit["find"]) != 1:
                shutil.rmtree(folder, ignore_errors=True)
                return {"outcome": "invalid", "reason": f"a find text occurs {text.count(edit['find'])} times in {edit['file']}"}
            target.write_text(text.replace(edit["find"], edit["replace"]))
            targets.setdefault(edit["file"], {"before": before})["after"] = sha256(target)
    env = clean_env(copy)
    probe = subprocess.run([python, "-B", "-c", "import scripts.stage1_s1.reading_input.build as m; print(m.__file__)"],
                           cwd=copy, env=env, capture_output=True, text=True)
    if probe.returncode != 0 or not probe.stdout.strip().startswith(str(copy)):
        shutil.rmtree(folder, ignore_errors=True)
        return {"outcome": "invalid", "reason": "the copy's scripts.stage1_s1.reading_input is not the one imported"}
    junit = folder / "junit.xml"
    command = [python, "-B", "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", "-W", "ignore",
               f"--basetemp={folder / 'bt'}", f"--junitxml={junit}", str(tree / "tests")]
    start = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=copy, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        shutil.rmtree(folder / "bt", ignore_errors=True)
        shutil.rmtree(copy, ignore_errors=True)
        return {"outcome": "invalid", "reason": f"timeout after {timeout} s", "seconds": timeout}
    seconds = round(time.monotonic() - start, 1)
    (folder / "pytest.out").write_text(proc.stdout[-20000:] + "\n--- stderr ---\n" + proc.stderr[-5000:])
    if not junit.is_file():
        shutil.rmtree(folder / "bt", ignore_errors=True)
        shutil.rmtree(copy, ignore_errors=True)
        return {"outcome": "invalid", "reason": "no JUnit file", "exit": proc.returncode, "seconds": seconds, "targets": targets}
    counts = junit_counts(junit)
    base = {"exit": proc.returncode, "seconds": seconds, "targets": targets, **counts}
    if mutant is None:
        base["tree"] = tree_hashes(tree)
    shutil.rmtree(folder / "bt", ignore_errors=True)
    shutil.rmtree(copy, ignore_errors=True)
    if counts["disk_full"] or DISK_FULL.search(proc.stderr[-5000:]):
        return {"outcome": "invalid", "reason": "a failure carries errno 28 or 122 (the disk is full)", **base}
    if expected_tests is not None and counts["tests"] != expected_tests:
        return {"outcome": "invalid", "reason": f"{counts['tests']} tests ran, the baseline ran {expected_tests}", **base}
    if proc.returncode == 0 and counts["failures"] == 0 and counts["errors"] == 0:
        return {"outcome": "survived" if mutant is not None else "pass", **base}
    if proc.returncode == 1 and counts["failures"] >= 1 and counts["errors"] == 0:
        return {"outcome": "killed" if mutant is not None else "fail", **base}
    return {"outcome": "invalid", "reason": "an error, or an exit code outside 0-1", **base}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True, help="a folder outside the workspace")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--min-free-gb", type=float, default=3.0)
    parser.add_argument("--only", default=None, help="comma-separated mutant ids (a shard)")
    args = parser.parse_args(argv)
    spec = json.loads(args.spec.read_bytes())
    scratch = args.scratch.resolve()
    if scratch == WORKSPACE or WORKSPACE in scratch.parents:
        print("REFUSED: the scratch folder must lie outside the workspace", file=sys.stderr)
        return 2
    scratch.mkdir(parents=True, exist_ok=True)
    pytest_version = subprocess.run([args.python, "-B", "-m", "pytest", "--version"], cwd=WORKSPACE, env=clean_env(scratch),
                                    capture_output=True, text=True)
    only = set(args.only.split(",")) if args.only else None
    report = {"kind": "stage1 mutation report", "version": 2, "tree_name": "scripts/stage1_s1/reading_input",
              "runner_sha256": sha256(Path(__file__).resolve()), "spec": str(args.spec), "spec_sha256": sha256(args.spec),
              "python": sys.version.split()[0], "pytest_version": (pytest_version.stdout + pytest_version.stderr).strip() or None,
              "dose_axis_sha256": sha256(WORKSPACE / "scripts" / "stage1" / "dose_axis.py"),
              "environment_removed": ["PYTEST_ADDOPTS", "PYTEST_PLUGINS"], "shard": sorted(only) if only else None,
              "rule": "killed = exit 1 with >= 1 failure and 0 errors; survived = exit 0, 0 failures, 0 errors; anything else "
                      "(errors, timeout, other exit codes, no JUnit, a test count other than the baseline's) = invalid; an "
                      "'expect: survive' entry passes only if it survives",
              "command": "python -B -m pytest -q -rs -p no:cacheprovider -W ignore --basetemp=<run>/bt --junitxml=<run>/junit.xml "
                         "<copy>/scripts/stage1_s1/reading_input/tests (cwd <copy>; PYTHONPATH <copy>:<workspace>; PYTHONDONTWRITEBYTECODE=1)",
              "timeout_seconds": args.timeout, "min_free_gb": args.min_free_gb}

    def space_ok(before: str) -> bool:
        free = shutil.disk_usage(scratch).free / 1e9
        if free < args.min_free_gb:
            report["stopped"] = f"before {before}: {free:.1f} GB free on the scratch volume, below {args.min_free_gb} GB"
            args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            print(f"REFUSED: {report['stopped']}; partial report written", file=sys.stderr)
            return False
        return True

    if not space_ok("the baseline"):
        return 2
    baseline = run_one("baseline", None, scratch, args.python, args.timeout)
    report["baseline"] = baseline
    print(f"baseline: {baseline['outcome']} ({baseline.get('tests')} tests, exit {baseline.get('exit')}, {baseline.get('seconds')} s)")
    if baseline["outcome"] != "pass":
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print("REFUSED: the unmutated baseline does not pass; no mutant was run", file=sys.stderr)
        return 2
    results, summary = [], {}
    for mutant in spec["mutants"]:
        if only is not None and mutant["id"] not in only:
            continue
        if not space_ok(mutant["id"]):
            report["mutants"], report["summary"] = results, summary
            args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            return 2
        outcome = run_one(mutant["id"], mutant, scratch, args.python, args.timeout, baseline["tests"])
        expect = mutant.get("expect", "kill")
        results.append({"id": mutant["id"], "part": mutant["part"], "describes": mutant["describes"], "expect": expect, **outcome})
        part = summary.setdefault(mutant["part"], {"mutants": 0, "killed": 0, "survived": 0, "invalid": 0, "equivalent": 0,
                                                   "expected_survivors_ok": 0, "expected_survivors_failed": 0})
        part["mutants"] += 1
        if expect == "survive":
            part["expected_survivors_ok"] += outcome["outcome"] == "survived"
            part["expected_survivors_failed"] += outcome["outcome"] == "killed"
            part["invalid"] += outcome["outcome"] == "invalid"
        else:
            part[outcome["outcome"]] += 1
        print(f"{mutant['id']:<44} {outcome['outcome']:<9} expect {expect:<7} failures {outcome.get('failures', '-')} "
              f"{outcome.get('seconds', '-')} s")
    report["mutants"], report["summary"] = results, summary
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))
    as_expected = all(p["survived"] == 0 and p["invalid"] == 0 and p["expected_survivors_failed"] == 0 for p in summary.values())
    print("every mutant as expected" if as_expected else "NOT every mutant as expected")
    return 0 if as_expected else 1


if __name__ == "__main__":
    sys.exit(main())
