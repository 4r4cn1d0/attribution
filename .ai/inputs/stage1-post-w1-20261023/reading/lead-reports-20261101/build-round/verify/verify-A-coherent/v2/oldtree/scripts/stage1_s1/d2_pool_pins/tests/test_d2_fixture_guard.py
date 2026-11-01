"""The D-2 tests' fixture guard (D-1's rule, verify-code finding 1 of notes/d1-verify-code.json): a module fixture that
runs D-2 code must turn a defect of the wrapper into test failures, never into setup errors, because the mutation runner
(mutation/run_mutants.py) counts any error as an invalid run, not a kill."""

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
    raise RuntimeError("D-2: the filled pins differ from the W1 pins")


@pytest.fixture(scope="module")
def req8():
    return {make}


@pytest.fixture(scope="module")
def e2e(req8):
    return {dependent}


def test_reads_the_fixture(req8):
    assert req8["record"]


def test_reads_a_dependent_fixture(e2e):
    assert e2e["out"]


def test_uses_an_attribute(req8):
    assert req8.module
'''


def _run_inner(tmp_path: Path, guarded: bool) -> tuple[int, dict, str]:
    if guarded:
        text = INNER.format(here=str(HERE), import_line="from d2guard import guarded",
                            make='guarded("req8", broken)', dependent='guarded("e2e", lambda: req8["filled"])')
    else:
        text = INNER.format(here=str(HERE), import_line="", make="broken()", dependent='req8["filled"]')
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
    assert "req8 failed in its fixture: RuntimeError: D-2: the filled pins differ from the W1 pins" in out
    assert "e2e failed in its fixture" in out


def test_the_guard_passes_a_good_value_through_and_keeps_skips():
    from d2guard import FixtureFailed, guarded

    value = {"k": 1}
    assert guarded("ok", lambda: value) is value
    failed = guarded("req8", lambda: {}["missing"])
    assert isinstance(failed, FixtureFailed) and "KeyError" in repr(failed)
    for use in (lambda: failed["x"], lambda: failed.module, lambda: list(failed), lambda: failed(), lambda: "x" in failed,
                lambda: len(failed)):
        with pytest.raises(AssertionError, match="req8 failed in its fixture: KeyError"):
            use()
    with pytest.raises(pytest.skip.Exception):
        guarded("skip", lambda: pytest.skip("not here"))


def test_the_d2_fixtures_are_guarded():
    """Every module fixture that runs D-2 code goes through the guard."""
    for file, names in (("test_d2_representation_pass.py", ("req8", "e2e")), ("test_d2_fill_pins.py", ("base",))):
        text = (HERE / file).read_text()
        for name in names:
            body = text.split(f"\ndef {name}(", 1)[1].split("\n\n\n", 1)[0]
            assert "guarded(" in body, f"{file}: {name} is not guarded"
