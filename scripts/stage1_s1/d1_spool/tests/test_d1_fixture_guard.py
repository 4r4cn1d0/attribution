"""The D-1 tests' fixture guard (verify-code finding 1, notes/d1-verify-code.json): a module fixture that runs D-1 code
must turn a defect of the wrapper into test failures, never into setup errors, because the mutation runner
(mutation/run_mutants.py) counts any error as an invalid run, not a kill. Plus one fact for the lead: at the committed
sizes k depends on N alone, and N = 947 gives k = 855 (verify-rule and verify-code notes)."""

from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from scripts.stage1 import build_s_pool as w1bsp
from scripts.stage1_s1.d1_spool import d1_s_pool as d1m

import d1fixtures as dx

HERE = Path(__file__).resolve().parent

INNER = '''
import sys
import pytest
sys.path.insert(0, {here!r})
{import_line}


def broken():
    raise RuntimeError("D-1: the lists disagree with the k computation")


@pytest.fixture(scope="module")
def chain():
    return {make}


@pytest.fixture(scope="module")
def answers(chain):
    return {dependent}


def test_reads_the_chain(chain):
    assert chain["record"]


def test_reads_a_dependent_fixture(answers):
    assert answers["files"]


def test_uses_an_attribute(chain):
    assert chain.module
'''


def _run_inner(tmp_path: Path, guarded: bool) -> tuple[int, dict, str]:
    """Runs a three-test file whose module fixture raises inside D-1-like code, in a child pytest; returns its exit
    code, the JUnit counts and its output."""
    if guarded:
        text = INNER.format(here=str(HERE), import_line="from d1guard import guarded",
                            make='guarded("chain", broken)', dependent='guarded("answers", lambda: chain["pair"])')
    else:
        text = INNER.format(here=str(HERE), import_line="", make="broken()", dependent='chain["pair"]')
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
    """Unguarded (the build's chain fixture): 3 setup errors, which the runner calls invalid. Guarded: 3 failures and
    0 errors, exit 1 (the runner's 'killed'), each naming the fixture and the wrapper's message."""
    code, counts, _ = _run_inner(tmp_path, guarded=False)
    assert code == 1 and counts == {"tests": 3, "failures": 0, "errors": 3}
    code, counts, out = _run_inner(tmp_path, guarded=True)
    assert code == 1 and counts == {"tests": 3, "failures": 3, "errors": 0}, out
    assert "chain failed in its fixture: RuntimeError: D-1: the lists disagree with the k computation" in out
    assert "answers failed in its fixture" in out


def test_the_guard_passes_a_good_value_through_and_keeps_skips():
    from d1guard import FixtureFailed, guarded

    value = {"k": 1}
    assert guarded("ok", lambda: value) is value
    failed = guarded("chain", lambda: {}["missing"])
    assert isinstance(failed, FixtureFailed) and "KeyError" in repr(failed)
    for use in (lambda: failed["x"], lambda: failed.module, lambda: list(failed), lambda: failed(), lambda: "x" in failed):
        with pytest.raises(AssertionError, match="chain failed in its fixture: KeyError"):
            use()
    with pytest.raises(pytest.skip.Exception):                      # a skip is not a failure; it passes through
        guarded("skip", lambda: pytest.skip("not here"))


def test_the_d1_fixtures_are_guarded():
    """Every module fixture that runs D-1 code goes through the guard (chain, answers, req3, scored; base)."""
    for file, names in (("test_d1_consumers.py", ("chain", "answers", "req3", "scored")), ("test_d1_s_pool.py", ("base",))):
        text = (HERE / file).read_text()
        for name in names:
            body = text.split(f"\ndef {name}(", 1)[1].split("\n\n\n", 1)[0]
            assert "guarded(" in body, f"{file}: {name} is not guarded"


def test_k_depends_on_n_alone_and_is_855_at_n_947():
    """sealed_order shuffles sorted(ids) with a seed from the key alone (s1common.py sealed_order), so at the committed
    sizes (48, 1,000, 512, 37) S1, S4 and the S3 order are fixed permutations of the ranks: two id sets of the same N
    with different ids give the same k. At N = 947 (the lead's real count) k = 855 with exactly 37 rows outside the
    lists, and 36 at k + 1. Synthetic ids only."""
    d1 = dx.committed_d1()
    w1 = dx.committed_w1()
    layouts = {
        "a": [f"pku_one:{i:06d}:1" for i in range(1, 948)],
        "b": [f"pku_two:{(7 * i) % 100003:06d}:{i % 2}" for i in range(1, 948)],
    }
    seen = {}
    for name, ids in layouts.items():
        assert len(set(ids)) == 947
        _, info = d1m.d1_lists(ids, w1, d1, w1bsp.lists_of)
        seen[name] = (info["k"], info["outside_at_k"], info["outside_at_k_plus_1"])
    assert seen["a"] == seen["b"] == (855, 37, 36)
