"""T1's mutation runner on scripts/stage1_s1 (test tooling; standard library only).

T1's runner (scripts/stage1/mutation/run_mutants.py, imported unchanged) copies only scripts/stage1 into each run
and runs only scripts/stage1/tests, so it cannot mutate a file under scripts/stage1_s1. This wrapper replaces only its
run_one (by assignment, before T1's main runs): each run (the baseline and every mutant) copies scripts/stage1
UNCHANGED and scripts/stage1_s1 into its own folder under --scratch, applies the mutant's exact text replacements to
the copy's scripts/stage1_s1 files (paths relative to scripts/stage1_s1; each find text exactly once), checks that the
copy's scripts.stage1_s1.eval_adapter is the one imported, and runs pytest on the copy's scripts/stage1_s1/tests with
T1's flags, environment (PYTHONPATH = <copy>:<workspace>, PYTEST_ADDOPTS and PYTEST_PLUGINS removed) and outcome
rules, word for word: KILLED only on exit 1 with at least one failure and no error; an error, a timeout, a missing JUnit
file, another exit code, a test count other than the baseline's or a disk-full failure is INVALID; exit 0 is
SURVIVED. Everything else is T1's main: the unmutated baseline first, the spec loop, the disk check, the report. The
wrapper adds one block, "s1_wrapper", to the report: its own SHA-256, the package it tested and the real command.

    python -B scripts/stage1_s1/mutation/run_mutants_b10.py --spec scripts/stage1_s1/mutation/mutants_b10.json \\
        --scratch <outside the workspace> --report <file>
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent                                   # scripts/stage1_s1
WORKSPACE = PACKAGE.parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from scripts.stage1.mutation import run_mutants as t1  # noqa: E402

PROBE = "import scripts.stage1_s1.eval_adapter as m; print(m.__file__)"
COMMAND = ("python -B -m pytest -q -rs -p no:cacheprovider --basetemp=<run>/bt --junitxml=<run>/junit.xml "
           "<copy>/scripts/stage1_s1/tests (cwd <copy>; PYTHONPATH <copy>:<workspace>; PYTHONDONTWRITEBYTECODE=1; "
           "<copy> holds scripts/stage1 unchanged and scripts/stage1_s1 mutated)")


def run_one(run_id: str, mutant: dict | None, scratch: Path, python: str, timeout: int,
            expected_tests: int | None = None) -> dict:
    folder = scratch / run_id
    if folder.exists():
        shutil.rmtree(folder)
    copy = folder / "copy"
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(t1.STAGE1, copy / "scripts" / "stage1", ignore=ignore)
    tree = copy / "scripts" / "stage1_s1"
    shutil.copytree(PACKAGE, tree, ignore=ignore)
    targets = {}
    if mutant is not None:
        for edit in t1.edits_of(mutant):
            target = tree / edit["file"]
            before = t1.sha256(target)
            text = target.read_text()
            if text.count(edit["find"]) != 1:
                return {"outcome": "invalid",
                        "reason": f"a find text occurs {text.count(edit['find'])} times in {edit['file']}"}
            target.write_text(text.replace(edit["find"], edit["replace"]))
            targets.setdefault(edit["file"], {"before": before})["after"] = t1.sha256(target)
    env = t1.clean_env(copy)
    probe = subprocess.run([python, "-B", "-c", PROBE], cwd=copy, env=env, capture_output=True, text=True)
    if probe.returncode != 0 or not probe.stdout.strip().startswith(str(copy)):
        return {"outcome": "invalid", "reason": "the copy's scripts.stage1_s1 is not the one imported"}
    junit = folder / "junit.xml"
    command = [python, "-B", "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", f"--basetemp={folder / 'bt'}",
               f"--junitxml={junit}", str(tree / "tests")]
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
        return {"outcome": "invalid", "reason": "no JUnit file", "exit": proc.returncode, "seconds": seconds,
                "targets": targets}
    counts = t1.junit_counts(junit)
    base = {"exit": proc.returncode, "seconds": seconds, "targets": targets, **counts}
    if mutant is None:
        base["tree"] = t1.tree_hashes(tree)
    shutil.rmtree(folder / "bt", ignore_errors=True)
    shutil.rmtree(copy, ignore_errors=True)
    if counts["disk_full"] or t1.DISK_FULL.search(proc.stderr[-5000:]):
        return {"outcome": "invalid", "reason": "a failure carries errno 28 or 122 (the disk is full)", **base}
    if expected_tests is not None and counts["tests"] != expected_tests:
        return {"outcome": "invalid", "reason": f"{counts['tests']} tests ran, the baseline ran {expected_tests}", **base}
    if proc.returncode == 0 and counts["failures"] == 0 and counts["errors"] == 0:
        return {"outcome": "survived" if mutant is not None else "pass", **base}
    if proc.returncode == 1 and counts["failures"] >= 1 and counts["errors"] == 0:
        return {"outcome": "killed" if mutant is not None else "fail", **base}
    return {"outcome": "invalid", "reason": "an error, or an exit code outside 0-1", **base}


def main(argv: list[str] | None = None) -> int:
    t1.run_one = run_one                                 # the only change to T1's runner: what one run copies and tests
    args = list(sys.argv[1:] if argv is None else argv)
    code = t1.main(args)
    if "--report" in args:
        report_path = Path(args[args.index("--report") + 1])
        if report_path.is_file():
            report = json.loads(report_path.read_text())
            report["s1_wrapper"] = {"wrapper": str(Path(__file__).resolve().relative_to(WORKSPACE)),
                                    "wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                    "t1_runner_sha256": t1.sha256(Path(t1.__file__).resolve()),
                                    "tested_package": "scripts/stage1_s1", "command": COMMAND,
                                    "note": "the report's own 'command' field is T1's text; this command is the one run"}
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
