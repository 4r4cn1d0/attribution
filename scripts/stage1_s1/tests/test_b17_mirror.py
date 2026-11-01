"""The B17 mutation mirror (mutation/b17_mirror.py): T1's runner bytes, T1's files without tests, the B17 files at
their relative paths, a read-only link to the engine, and imports that resolve to the mirror. Not copied into the
mirror itself (it is not in B17_FILES)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import b17_support as bs

MIRROR_TOOL = bs.PKG_DIR / "mutation" / "b17_mirror.py"
pytestmark = pytest.mark.skipif(bs.IN_MIRROR, reason="the mirror holds no mirror tool")


def tool():
    spec = importlib.util.spec_from_file_location("b17_mirror_under_test", MIRROR_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def workspace_of_this_package(tmp_path: Path) -> Path:
    """A workspace made of links: the engine tree (found from its import), the scripts/stage1 that s1common comes from
    and the package under test. In ws-s1 these are ws-s1's own folders; in a mutation copy (which holds scripts/stage1
    and scripts/stage1_s1 but no experiments/) they are the copy's packages and the workspace's engine, so the tool is
    tested on the package under test (S1 FIX of the merged-tree layout finding)."""
    engine = Path(importlib.import_module("experiments.safety_selection").__file__).resolve().parents[1]
    workspace = tmp_path / "workspace"
    (workspace / "scripts").mkdir(parents=True)
    (workspace / "experiments").symlink_to(engine, target_is_directory=True)
    (workspace / "scripts" / "stage1").symlink_to(Path(bs.s1.__file__).resolve().parent, target_is_directory=True)
    (workspace / "scripts" / "stage1_s1").symlink_to(bs.PKG_DIR, target_is_directory=True)
    return workspace


def test_the_mirror_holds_t1_without_tests_and_the_b17_files(tmp_path):
    mirror_tool = tool()
    workspace = workspace_of_this_package(tmp_path)
    saved = list(sys.path)
    try:
        record = mirror_tool.build_mirror(tmp_path / "mirror", workspace)
    finally:
        sys.path[:] = saved                  # the tool puts its workspace first on sys.path; this one is temporary
    mirror = tmp_path / "mirror"
    target = mirror / "scripts" / "stage1"
    t1 = workspace / "scripts" / "stage1"
    assert (mirror / "experiments").is_symlink()
    assert (mirror / "experiments").resolve() == (workspace / "experiments").resolve()
    assert (workspace / "experiments").resolve() == Path(bs.runner.__file__).resolve().parents[1]
    assert sha(target / "mutation" / "run_mutants.py") == sha(t1 / "mutation" / "run_mutants.py") == record["runner_sha256"]
    assert sha(target / "s1common.py") == sha(t1 / "s1common.py") and sha(target / "labels.json") == sha(t1 / "labels.json")
    for rel in mirror_tool.B17_FILES:
        assert sha(target / rel) == sha(bs.PKG_DIR / rel), rel
    tests = sorted(p.name for p in (target / "tests").iterdir())
    assert tests == sorted(Path(rel).name for rel in mirror_tool.B17_FILES if rel.startswith("tests/"))
    assert not (target / "mutation" / "b17_mirror.py").exists()
    assert json.loads((mirror / "MIRROR.json").read_bytes())["files"] == record["files"]
    env = {**{k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")},
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(mirror)}
    probe = subprocess.run([sys.executable, "-B", "-c",
                            "import scripts.stage1.s1common as m, scripts.stage1.lean_eval_job as l; "
                            "print(m.__file__); print(l.__file__); print(l.load_lean_settings()[1])"],
                           cwd=mirror, env=env, capture_output=True, text=True)
    assert probe.returncode == 0, probe.stderr[-2000:]
    lines = probe.stdout.split()
    assert lines[0].startswith(str(target)) and lines[1].startswith(str(target))
    assert lines[2] == bs.lej.SETTINGS_SHA256


def test_the_mirror_refuses_an_existing_folder_and_one_inside_the_workspace(tmp_path):
    mirror_tool = tool()
    (tmp_path / "taken").mkdir()
    with pytest.raises(SystemExit):
        mirror_tool.build_mirror(tmp_path / "taken")
    with pytest.raises(SystemExit):
        mirror_tool.build_mirror(bs.REPO / "tmp" / "b17-mirror-must-not-exist")
    assert not (bs.REPO / "tmp" / "b17-mirror-must-not-exist").exists()
