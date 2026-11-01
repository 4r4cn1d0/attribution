"""T1's mutation runner, pointed at scripts/stage1_s1 (test tooling; standard library only).

    python -B scripts/stage1_s1/mutation/run_mutants_b14.py --spec SPEC --scratch DIR --report FILE [--timeout S]

Why an adapter. T1's runner (``scripts/stage1/mutation/run_mutants.py``, frozen) copies only ``scripts/stage1`` into
each run's folder, applies the mutants there and runs ``scripts/stage1/tests`` (its run_one hard-codes that layout:
the tree destination, the import probe and the test folder). It cannot mutate or test ``scripts/stage1_s1``, and
editing it is not allowed. This adapter loads T1's runner by path, after its SHA-256 check, and replaces only its
``run_one`` with one that has the same steps and the same outcome rules but this layout: the run folder's copy holds
``scripts/stage1`` UNCHANGED and ``scripts/stage1_s1`` (the mutant's ``file`` paths are relative to scripts/stage1_s1),
the layout of B10's and B11's wrappers, so the merged package's suite (every build's tests) runs from the committed
tree itself (S1 FIX of the merged-tree layout finding: with scripts/stage1 missing from the copy, B11's tests fail
because s1common's REPO is then not the package's root); pytest runs ``<copy>/scripts/stage1_s1/tests`` with T1's
environment (PYTHONPATH = <copy>:<workspace>, so the copy's packages shadow the workspace's while the engine comes
from the workspace); the import probe checks that the copy's ``scripts.stage1_s1.overlap_strata`` is the one
imported. T1's ``main`` then runs unchanged (the baseline first, the
disk check, the per-mutant timeout, the report and its summary); the adapter adds an ``adapter`` block to the report
and corrects its ``command`` field.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent                                   # scripts/stage1_s1
WORKSPACE = PACKAGE.parents[1]
T1_RUNNER = WORKSPACE / "scripts" / "stage1" / "mutation" / "run_mutants.py"
T1_RUNNER_SHA256 = "557a2875da16ac9fd7414c7316867a2c606b824ce8ccbbc6276a45f98dff29ef"
PROBE_MODULE = "scripts.stage1_s1.overlap_strata"


def load_t1():
    digest = hashlib.sha256(T1_RUNNER.read_bytes()).hexdigest()
    if digest != T1_RUNNER_SHA256:
        raise SystemExit(f"REFUSED: T1's runner hashes to {digest}, not the pinned {T1_RUNNER_SHA256}")
    spec = importlib.util.spec_from_file_location("stage1_t1_run_mutants", T1_RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


T1 = load_t1()


def run_one(run_id: str, mutant: dict | None, scratch: Path, python: str, timeout: int,
            expected_tests: int | None = None) -> dict:
    """T1's run_one with the scripts/stage1_s1 layout (its outcome rules are copied unchanged)."""
    folder = scratch / run_id
    if folder.exists():
        shutil.rmtree(folder)
    copy = folder / "copy"
    tree = copy / "scripts" / "stage1_s1"
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(T1.STAGE1, copy / "scripts" / "stage1", ignore=ignore)     # unchanged (B10's and B11's layout)
    shutil.copytree(PACKAGE, tree, ignore=ignore)
    targets = {}
    if mutant is not None:
        for edit in T1.edits_of(mutant):
            target = tree / edit["file"]
            before = T1.sha256(target)
            text = target.read_text()
            if text.count(edit["find"]) != 1:
                return {"outcome": "invalid", "reason": f"a find text occurs {text.count(edit['find'])} times in {edit['file']}"}
            target.write_text(text.replace(edit["find"], edit["replace"]))
            targets.setdefault(edit["file"], {"before": before})["after"] = T1.sha256(target)
    env = T1.clean_env(copy)
    probe = subprocess.run([python, "-B", "-c", f"import {PROBE_MODULE} as m; print(m.__file__)"],
                           cwd=copy, env=env, capture_output=True, text=True)
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
    counts = T1.junit_counts(junit)
    base = {"exit": proc.returncode, "seconds": seconds, "targets": targets, **counts}
    if mutant is None:
        base["tree"] = T1.tree_hashes(tree)
    shutil.rmtree(folder / "bt", ignore_errors=True)
    shutil.rmtree(copy, ignore_errors=True)
    if counts["disk_full"] or T1.DISK_FULL.search(proc.stderr[-5000:]):
        return {"outcome": "invalid", "reason": "a failure carries errno 28 or 122 (the disk is full)", **base}
    if expected_tests is not None and counts["tests"] != expected_tests:
        return {"outcome": "invalid", "reason": f"{counts['tests']} tests ran, the baseline ran {expected_tests}", **base}
    if proc.returncode == 0 and counts["failures"] == 0 and counts["errors"] == 0:
        return {"outcome": "survived" if mutant is not None else "pass", **base}
    if proc.returncode == 1 and counts["failures"] >= 1 and counts["errors"] == 0:
        return {"outcome": "killed" if mutant is not None else "fail", **base}
    return {"outcome": "invalid", "reason": "an error, or an exit code outside 0-1", **base}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    T1.run_one = run_one
    code = T1.main(argv)
    report_path = Path(argv[argv.index("--report") + 1])
    if report_path.is_file():
        report = json.loads(report_path.read_text())
        report["command"] = ("python -B -m pytest -q -rs -p no:cacheprovider --basetemp=<run>/bt "
                             "--junitxml=<run>/junit.xml <copy>/scripts/stage1_s1/tests (cwd <copy>; <copy> holds "
                             "scripts/stage1 unchanged and scripts/stage1_s1 mutated; PYTHONPATH <copy>:<workspace>; "
                             "PYTHONDONTWRITEBYTECODE=1)")
        report["adapter"] = {"script": "scripts/stage1_s1/mutation/run_mutants_b14.py",
                             "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             "t1_runner_sha256": T1_RUNNER_SHA256, "tested_tree": "scripts/stage1_s1",
                             "layout": "the copy holds scripts/stage1 unchanged and scripts/stage1_s1 mutated",
                             "mutant_file_paths": "relative to scripts/stage1_s1"}
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
