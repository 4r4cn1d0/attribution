"""Test tooling: a mirror in which T1's mutation runner, unchanged, mutates the B17 files (standard library only).

T1's runner (scripts/stage1/mutation/run_mutants.py) copies <its workspace>/scripts/stage1 and runs that copy's tests,
so it cannot reach scripts/stage1_s1. This tool builds MIRROR, a new folder outside the workspace:

- MIRROR/experiments: a symbolic link to the workspace's engine tree (read only; the engine identity is unchanged);
- MIRROR/scripts/stage1: every T1 file except tests/ (byte for byte, T1's runner among them), and the B17 files of
  scripts/stage1_s1 (B17_FILES) at the same relative paths, so tests/ holds the B17 tests only.

Then run T1's runner from the mirror; the spec's file paths are relative to scripts/stage1_s1:

  python -B MIRROR/scripts/stage1/mutation/run_mutants.py --spec <ws>/scripts/stage1_s1/mutation/mutants_b17.json \
      --scratch SCRATCH --report REPORT

The B17 tests import the job module by their own package folder's name (tests/b17_support.py), so in the mirror they
import the copy that the runner mutates. A B17 path that is also a T1 path refuses. MIRROR/MIRROR.json records every
copied file's SHA-256, the runner's SHA-256 (equal to T1's) and the engine identity. The workspace is never changed.

  python scripts/stage1_s1/mutation/b17_mirror.py --mirror MIRROR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
WORKSPACE = PACKAGE.parents[1]
B17_FILES = ("lean_eval_job.py", "settings/lean_eval_job.json", "tests/conftest.py", "tests/b17_support.py",
             "tests/test_b17_lean_eval_job.py", "tests/test_b17_engine_subset.py", "tests/test_b17_gaps.py",
             "mutation/mutants_b17.json",
             # addendum 11.13: the shared O-ext module (lean_eval_job imports it by its own package's name), its
             # settings, its fixtures and B17's O-ext tests
             "oext_eval.py", "settings/oext_eval.json", "tests/oext_fixtures.py", "tests/test_b17_oext.py")
KIND = "stage1 S1 B17 mutation mirror"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_mirror(mirror: str | Path, workspace: str | Path = WORKSPACE) -> dict:
    """Builds the mirror (module doc) and returns its record; refuses an existing folder, a folder inside the
    workspace, a missing B17 file and a B17 path that T1 also has."""
    mirror, workspace = Path(mirror).resolve(), Path(workspace).resolve()
    if mirror.exists():
        raise SystemExit(f"REFUSED: {mirror} exists; the mirror is always a new folder")
    if mirror == workspace or workspace in mirror.parents:
        raise SystemExit("REFUSED: the mirror must lie outside the workspace")
    t1, b17 = workspace / "scripts" / "stage1", workspace / "scripts" / "stage1_s1"
    missing = [name for name in B17_FILES if not (b17 / name).is_file()]
    if missing:
        raise SystemExit(f"REFUSED: {len(missing)} B17 files are missing (first: {missing[0]})")
    t1_files = sorted(p for p in t1.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                      and p.suffix != ".pyc" and p.relative_to(t1).parts[0] != "tests")
    clash = sorted(set(B17_FILES) & {p.relative_to(t1).as_posix() for p in t1_files})
    if clash:
        raise SystemExit(f"REFUSED: {len(clash)} B17 paths are also T1 paths (first: {clash[0]})")
    target = mirror / "scripts" / "stage1"
    target.mkdir(parents=True)
    (mirror / "experiments").symlink_to(workspace / "experiments", target_is_directory=True)
    files = {}
    for path in t1_files:
        rel = path.relative_to(t1).as_posix()
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target / rel)
        files[f"t1/{rel}"] = sha256(target / rel)
    for rel in B17_FILES:
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(b17 / rel, target / rel)
        files[f"b17/{rel}"] = sha256(target / rel)
    runner = "mutation/run_mutants.py"
    if sha256(target / runner) != sha256(t1 / runner):
        raise SystemExit("REFUSED: the mirror's runner is not T1's runner")
    sys.path.insert(0, str(workspace))
    from experiments.safety_selection.common import code_identity

    record = {"kind": KIND, "version": 1, "workspace": str(workspace), "mirror": str(mirror),
              "runner_sha256": sha256(t1 / runner), "engine_identity_sha256": code_identity()["sha256"],
              "files": files,
              "command": (f"python -B {target / runner} --spec {b17 / 'mutation' / 'mutants_b17.json'} "
                          "--scratch SCRATCH --report REPORT")}
    (mirror / "MIRROR.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--mirror", type=Path, required=True, help="a new folder outside the workspace")
    args = parser.parse_args(argv)
    record = build_mirror(args.mirror)
    print(json.dumps({"mirror": record["mirror"], "files": len(record["files"]),
                      "runner_sha256": record["runner_sha256"], "command": record["command"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
