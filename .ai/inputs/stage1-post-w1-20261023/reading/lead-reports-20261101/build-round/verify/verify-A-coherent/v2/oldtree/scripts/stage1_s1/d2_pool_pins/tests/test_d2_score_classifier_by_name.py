"""D-2 for J8 (addendum section 21): two more checks on d2_score_classifier (notes/d2b-verify.json VV-1 and VV-2).

1. The by-name W1 modules stay as they were. score_classifier's _run imports scripts.stage1.representation_pass by
   name (score_classifier.py:68); the wrapper must never change that module (its POOL_PINS_SHA256, POOL_PINS_PATH,
   load_pool_pins' defaults or any other global), nor the by-name scripts.stage1.score_classifier when it is importable,
   nor what sys.modules and the scripts.stage1 package give for either name. Checked after a successful run, after a
   refusal inside score_classifier's main, after a refusal by D-2's own checks, and after an exception.
2. An exception that is not a refusal, raised inside score_classifier's run, propagates out of
   d2_score_classifier.main (it is not turned into exit 2 'REFUSED ... nothing written').

The fixtures are test_d2_score_classifier's (its module fixture req8 goes through the guard, d2guard). Synthetic data
only; nothing real is read."""

from __future__ import annotations

import dataclasses
import importlib
import sys
import types
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from experiments.safety_selection.common import sha256_file  # noqa: E402
import scripts.stage1 as stage1_package  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import d2_score_classifier as dsc  # noqa: E402

import d2fixtures as dx  # noqa: E402
import test_d2_score_classifier as tdsc  # noqa: E402  (its fixtures: req8 is guarded; and its argv helpers)

env = tdsc.env
req8 = tdsc.req8
sc_settings = tdsc.sc_settings
wired = tdsc.wired
sfx = tdsc.sfx

RP_NAME = "scripts.stage1.representation_pass"
SC_NAME = "scripts.stage1.score_classifier"
MISSING = object()


def by_name_modules() -> list[str]:
    """representation_pass, and score_classifier when it is importable."""
    names = [RP_NAME]
    try:
        importlib.import_module(SC_NAME)
    except ImportError:
        return names
    return names + [SC_NAME]


def snapshot() -> dict:
    """For each by-name module: the module sys.modules and the scripts.stage1 package give for its name, every global
    (compared by identity), and, by value, every function's __defaults__ and __kwdefaults__ (they can change while
    the function object stays the same; load_pool_pins' defaults are POOL_PINS_PATH and POOL_PINS_SHA256)."""
    out = {}
    for name in by_name_modules():
        module = sys.modules.get(name)
        values = {}
        for key, value in vars(module).items():
            if isinstance(value, types.FunctionType):
                values[f"{key}.__defaults__"] = value.__defaults__
                values[f"{key}.__kwdefaults__"] = value.__kwdefaults__
        out[name] = {"module": module, "package": getattr(stage1_package, name.rsplit(".", 1)[1], MISSING),
                     "globals": dict(vars(module)), "values": values}
    return out


def differences(before: dict, after: dict) -> list[str]:
    out = [f"{name}: not snapshotted in both" for name in set(before) ^ set(after)]
    for name in sorted(set(before) & set(after)):
        b, a = before[name], after[name]
        out += [f"{name}: the {key} changed" for key in ("module", "package") if a[key] is not b[key]]
        out += [f"{name}.{key} changed" for key in sorted(set(b["globals"]) | set(a["globals"]))
                if a["globals"].get(key, MISSING) is not b["globals"].get(key, MISSING)]
        out += [f"{name}: {key} changed" for key in sorted(set(b["values"]) | set(a["values"]))
                if a["values"].get(key, MISSING) != b["values"].get(key, MISSING)]
    return out


PRISTINE = snapshot()  # at collection, before any test runs


def assert_w1_values() -> None:
    """The by-name representation_pass holds the W1 file's own pins values (not a snapshot: the W1 literal and path)."""
    rp = sys.modules[RP_NAME]
    assert Path(rp.__file__).resolve() == tdsc.fp.w1_root() / "scripts" / "stage1" / "representation_pass.py"
    assert rp.POOL_PINS_SHA256 == dx.W1_PINS_SHA256 == sha256_file(rp.POOL_PINS_PATH)
    assert rp.POOL_PINS_PATH == Path(rp.__file__).resolve().parent / "settings" / "representation_pools.json"
    assert rp.load_pool_pins.__defaults__ == (rp.POOL_PINS_PATH, dx.W1_PINS_SHA256)
    assert sys.modules[SC_NAME].SETTINGS_SHA256 == tdsc.SC_SETTINGS_SHA256


class SyntheticFailure(Exception):
    """Neither a refusal nor an OSError (score_classifier's own main turns those two into exit 2)."""


def raise_inside_the_run(monkeypatch, wired) -> list:
    """real_loaders gives the fixture loaders with a guard loader that raises SyntheticFailure, so score_classifier's
    run raises after its pins and pools checks (runner.Session.guard, score_classifier.py:88). Each raise records the
    name of the private module's run at that moment."""
    import experiments.safety_selection.loaders as loaders_module

    calls = []

    def guard(recipe, ledger, device):
        calls.append(wired[-1][0].run.__name__)
        raise SyntheticFailure("synthetic failure inside score_classifier's run")
    monkeypatch.setattr(loaders_module, "real_loaders", lambda: dataclasses.replace(sfx.fixture_loaders(), guard=guard))
    return calls


def test_the_by_name_modules_are_unchanged_by_the_wrapper(env, req8, sc_settings, wired, monkeypatch, tmp_path, capsys):
    """VV-1: no change to the by-name modules after a successful run, a refusal inside score_classifier's main, a
    refusal by D-2's own checks, or an exception; nor left by any earlier test (the collection-time snapshot)."""
    assert SC_NAME in by_name_modules()
    before = snapshot()
    assert differences(PRISTINE, before) == [], "an earlier test left a by-name module changed"
    assert_w1_values()

    pools = [req8["plant"], req8["decoy"]]
    assert dsc.main(tdsc.d2_argv(env, sc_settings, req8, tmp_path / "ok", pools)) == 0
    assert tdsc.output_of(tmp_path / "ok")
    assert differences(before, snapshot()) == [], "after a successful run"

    bad = (req8["plant"][0], "0" * 64)
    assert dsc.main(tdsc.d2_argv(env, sc_settings, req8, tmp_path / "r1", [bad])) == 2
    assert "a pool file hashes to" in capsys.readouterr().err and not (tmp_path / "r1").exists()
    assert differences(before, snapshot()) == [], "after a refusal inside score_classifier's main"

    argv = tdsc.argv_of(env, sc_settings, tmp_path / "r2", pools,
                        ("--pool-pins", dx.spec((req8["filled"][0], "0" * 64)), "--req8-record", dx.spec(req8["record"])))
    assert dsc.main(argv) == 2
    assert "the filled pins file hashes to" in capsys.readouterr().err and not (tmp_path / "r2").exists()
    assert differences(before, snapshot()) == [], "after a refusal by D-2's own checks"

    calls = raise_inside_the_run(monkeypatch, wired)
    with pytest.raises(SyntheticFailure):
        dsc.main(tdsc.d2_argv(env, sc_settings, req8, tmp_path / "x", pools))
    assert calls == ["filled_run"] and not (tmp_path / "x").exists()
    assert differences(before, snapshot()) == [], "after an exception"

    assert_w1_values()
    assert len(wired) == 3 and all(module.run is run for module, run in wired)


def test_a_non_refusal_exception_inside_the_classifier_run_propagates_out_of_main(env, req8, sc_settings, wired,
                                                                                  monkeypatch, tmp_path, capsys):
    """VV-2: main() catches refusals only. An exception raised inside score_classifier's run (with run replaced)
    propagates out of d2_score_classifier.main: no exit 2, no 'REFUSED' line, nothing written, run restored."""
    assert not issubclass(SyntheticFailure, (s1.Refusal, OSError))
    calls = raise_inside_the_run(monkeypatch, wired)
    with pytest.raises(SyntheticFailure, match="synthetic failure inside score_classifier's run"):
        dsc.main(tdsc.d2_argv(env, sc_settings, req8, tmp_path / "out", [req8["plant"], req8["decoy"]]))
    assert calls == ["filled_run"]
    captured = capsys.readouterr()
    assert captured.out.startswith(f"D-2: filled pins {req8['filled'][1]} (") and "REFUSED" not in captured.err
    assert not (tmp_path / "out").exists()
    [(module, run)] = wired
    assert module.run is run


def test_the_fixtures_here_are_the_guarded_ones():
    """The module fixture here that runs D-2 code is test_d2_score_classifier's guarded req8 (d2guard's rule)."""
    assert req8 is tdsc.req8
    text = Path(tdsc.__file__).read_text()
    body = text.split("\ndef req8(", 1)[1].split("\n\n\n", 1)[0]
    assert "guarded(" in body
