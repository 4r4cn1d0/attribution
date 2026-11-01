"""The D-3 tests' fixture guard (D-1's and D-2's rule, notes/d1-verify-code.json finding 1): a module fixture that runs
D-3 code must turn a defect of the wrapper into test failures, never into setup errors, because the mutation runner
(mutation/run_mutants.py) counts any error as an invalid run, not a kill. The module fixture ``world`` runs REQ-3 and
the synthetic fixtures only (no D-3 function), so a failure there is an environment error and stays one."""

from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent

INNER = '''
import sys
import pytest
sys.path.insert(0, {here!r})
{import_line}


def broken():
    raise RuntimeError("D-3: the two passes differ in datashield")


@pytest.fixture(scope="module")
def loaded():
    return {make}


@pytest.fixture(scope="module")
def both(loaded):
    return {dependent}


def test_reads_the_fixture(loaded):
    assert loaded[0]


def test_reads_a_dependent_fixture(both):
    assert both["out"]


def test_uses_an_attribute(loaded):
    assert loaded.module
'''


def _run_inner(tmp_path: Path, guarded: bool) -> tuple[int, dict, str]:
    if guarded:
        text = INNER.format(here=str(HERE), import_line="from d3guard import guarded",
                            make='guarded("loaded", broken)', dependent='guarded("both", lambda: loaded["work"])')
    else:
        text = INNER.format(here=str(HERE), import_line="", make="broken()", dependent='loaded["work"]')
    folder = tmp_path / ("guarded" if guarded else "unguarded")
    folder.mkdir()
    (folder / "test_inner.py").write_text(text)
    junit = folder / "junit.xml"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTEST_ADDOPTS", None)
    proc = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-W", "ignore",
                           f"--basetemp={folder / 'bt'}", f"--junitxml={junit}", "--rootdir", str(folder),
                           str(folder / "test_inner.py")],
                          cwd=folder, env=env, capture_output=True, text=True, timeout=120)
    root = ET.parse(junit).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    counts = {key: sum(int(s.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors")}
    return proc.returncode, counts, proc.stdout + proc.stderr


def test_a_failing_guarded_fixture_gives_failures_not_setup_errors(tmp_path):
    code, counts, _ = _run_inner(tmp_path, guarded=False)
    assert code == 1 and counts == {"tests": 3, "failures": 0, "errors": 3}
    code, counts, out = _run_inner(tmp_path, guarded=True)
    assert code == 1 and counts == {"tests": 3, "failures": 3, "errors": 0}, out
    assert "loaded failed in its fixture: RuntimeError: D-3: the two passes differ in datashield" in out
    assert "both failed in its fixture" in out


def test_the_guard_passes_a_good_value_through_and_keeps_skips():
    from d3guard import FixtureFailed, guarded

    value = {"k": 1}
    assert guarded("ok", lambda: value) is value
    failed = guarded("loaded", lambda: {}["missing"])
    assert isinstance(failed, FixtureFailed) and "KeyError" in repr(failed)
    for use in (lambda: failed["x"], lambda: failed.module, lambda: list(failed), lambda: failed(), lambda: "x" in failed,
                lambda: len(failed)):
        with pytest.raises(AssertionError, match="loaded failed in its fixture: KeyError"):
            use()
    with pytest.raises(pytest.skip.Exception):
        guarded("skip", lambda: pytest.skip("not here"))


def test_the_d3_fixtures_are_guarded():
    """Every module fixture that runs D-3 code goes through the guard; world runs none."""
    text = (HERE / "test_d3_s3_union.py").read_text()
    for name in ("both", "loaded"):
        body = text.split(f"\ndef {name}(", 1)[1].split("\n\n\n", 1)[0]
        assert "guarded(" in body, f"{name} is not guarded"
    body = text.split("\ndef world(", 1)[1].split("\n\n\n", 1)[0]
    assert "d3m." not in body and "guarded(" not in body
