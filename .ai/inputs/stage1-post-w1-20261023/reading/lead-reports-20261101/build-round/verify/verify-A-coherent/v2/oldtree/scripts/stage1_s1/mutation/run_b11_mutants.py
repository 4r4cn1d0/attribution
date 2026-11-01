"""Runs T1's mutation runner (scripts/stage1/mutation/run_mutants.py, unchanged) on the scripts/stage1_s1 package.

Why a wrapper. T1's runner copies scripts/stage1 into each run and runs scripts/stage1/tests; the folder name is a
literal in its run_one (the copy, the import probe and the pytest target). So it cannot test a sibling package as it
is, and T1's files are never edited. This wrapper loads T1's runner from its own file, after checking the file's
SHA-256 against T1_RUNNER_SHA256, and calls T1's own main(). Every rule stays T1's: the unmutated baseline with the
same command, whole test files, no -x, JUnit, the per-mutant timeout, the disk checks, the removed PYTEST_ADDOPTS and
PYTEST_PLUGINS, and the classification (killed = exit 1 with at least one failure and no error; survived = exit 0;
anything else, or a test count other than the baseline's, is invalid). Only T1's run_one is replaced, by
run_one_s1 below, which differs in the layout alone:

- each run copy holds scripts/stage1 (unmutated, so s1common's REPO is the copy) and scripts/stage1_s1 (mutated);
- a mutant's "file" is relative to scripts/stage1_s1;
- the import probe checks that scripts.stage1_s1 and scripts.stage1.s1common both come from the copy;
- pytest runs <copy>/scripts/stage1_s1/tests, with PYTHONPATH = <copy>:<workspace> (T1's clean_env), so the engine
  comes from the workspace.

After T1's main has written its report, the wrapper adds a "wrapper" block (its own SHA-256, T1's runner SHA-256 and
the layout) and replaces the report's "command" text with this layout's command.

Usage: python -B scripts/stage1_s1/mutation/run_b11_mutants.py --spec SPEC --scratch DIR --report FILE [T1 options]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent                                     # scripts/stage1_s1
WORKSPACE = PACKAGE.parents[1]
T1_RUNNER = WORKSPACE / "scripts" / "stage1" / "mutation" / "run_mutants.py"
T1_RUNNER_SHA256 = "557a2875da16ac9fd7414c7316867a2c606b824ce8ccbbc6276a45f98dff29ef"
COMMAND = ("python -B -m pytest -q -rs -p no:cacheprovider --basetemp=<run>/bt --junitxml=<run>/junit.xml "
           "<copy>/scripts/stage1_s1/tests (cwd <copy>; the copy holds scripts/stage1 unmutated and scripts/stage1_s1 "
           "mutated; PYTHONPATH <copy>:<workspace>; PYTHONDONTWRITEBYTECODE=1)")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_t1():
    if _sha256(T1_RUNNER) != T1_RUNNER_SHA256:
        raise SystemExit(f"REFUSED: {T1_RUNNER} is not T1's runner {T1_RUNNER_SHA256}")
    spec = importlib.util.spec_from_file_location("stage1_t1_run_mutants", T1_RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_run_one(t1):
    """T1's run_one with the scripts/stage1_s1 layout (the only change; see the module docstring)."""

    def run_one_s1(run_id: str, mutant: dict | None, scratch: Path, python: str, timeout: int,
                   expected_tests: int | None = None) -> dict:
        folder = scratch / run_id
        if folder.exists():
            shutil.rmtree(folder)
        copy = folder / "copy"
        tree = copy / "scripts" / "stage1_s1"
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        shutil.copytree(t1.STAGE1, copy / "scripts" / "stage1", ignore=ignore)
        shutil.copytree(PACKAGE, tree, ignore=ignore)
        targets = {}
        if mutant is not None:
            for edit in t1.edits_of(mutant):
                target = tree / edit["file"]
                before = t1.sha256(target)
                text = target.read_text()
                if text.count(edit["find"]) != 1:
                    return {"outcome": "invalid", "reason": f"a find text occurs {text.count(edit['find'])} times in {edit['file']}"}
                target.write_text(text.replace(edit["find"], edit["replace"]))
                targets.setdefault(edit["file"], {"before": before})["after"] = t1.sha256(target)
        env = t1.clean_env(copy)
        probe = subprocess.run([python, "-B", "-c", "import scripts.stage1_s1 as p, scripts.stage1.s1common as c; "
                                "print(p.__file__); print(c.__file__)"], cwd=copy, env=env, capture_output=True, text=True)
        lines = probe.stdout.split()
        if probe.returncode != 0 or len(lines) != 2 or not all(line.startswith(str(copy)) for line in lines):
            return {"outcome": "invalid", "reason": "the copy's scripts.stage1_s1 or scripts.stage1 is not the one imported"}
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

    return run_one_s1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--report", type=Path)
    known, _ = parser.parse_known_args(argv)
    t1 = load_t1()
    t1.run_one = make_run_one(t1)
    code = t1.main(argv)
    if known.report is not None and known.report.is_file():
        report = json.loads(known.report.read_bytes())
        report["command"] = COMMAND
        report["wrapper"] = {"path": "scripts/stage1_s1/mutation/run_b11_mutants.py",
                             "sha256": _sha256(Path(__file__).resolve()), "t1_runner_sha256": T1_RUNNER_SHA256,
                             "layout": "scripts/stage1 copied unmutated; scripts/stage1_s1 copied and mutated; "
                                       "tests: scripts/stage1_s1/tests"}
        known.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
