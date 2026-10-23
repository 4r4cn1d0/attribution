"""S1 FIX (notes/s1-fix.json; review finding 3, s1-merge open item 1): the merged package's one mutation layout. Each of
the package's three runner wrappers (B10's, B11's and B14's) builds every run copy with scripts/stage1 UNCHANGED and
scripts/stage1_s1 (the package under test), so each build's spec runs from the committed tree itself, with the whole
package suite as its test set (B17 keeps its mirror). The run is stopped at the import probe (no pytest), and the copy
is compared file by file. Test tooling only; no draw, no model."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PKG = Path(__file__).resolve().parents[1]
WRAPPERS = ("run_mutants_b10.py", "run_b11_mutants.py", "run_mutants_b14.py")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"s1_layout_{name[:-3]}", PKG / "mutation" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_one(module):
    """The wrapper's run_one (B11's is made from T1's module)."""
    if hasattr(module, "make_run_one"):
        return module.make_run_one(module.load_t1())
    return module.run_one


def _tree(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


@pytest.mark.parametrize("name", WRAPPERS)
def test_every_wrapper_copies_scripts_stage1_unchanged_and_the_package(name, tmp_path, monkeypatch):
    module = _load(name)
    calls = []

    def probe(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(module, "subprocess", SimpleNamespace(run=probe, TimeoutExpired=subprocess.TimeoutExpired))
    out = _run_one(module)("layout", None, tmp_path, sys.executable, 10)
    assert out["outcome"] == "invalid" and "imported" in out["reason"] and len(calls) == 1      # stopped at the probe
    copy = tmp_path / "layout" / "copy"
    import scripts.stage1.s1common as s1

    stage1 = Path(s1.__file__).resolve().parent
    assert _tree(copy / "scripts" / "stage1") == _tree(stage1)
    assert _tree(copy / "scripts" / "stage1_s1") == _tree(PKG)
    assert sorted(p.name for p in (copy / "scripts").iterdir()) == ["stage1", "stage1_s1"]
