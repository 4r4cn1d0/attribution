"""D-2 for J8 (addendum section 21): d2_score_classifier on a synthetic end-to-end. REQ-8 (build_plant.py itself) runs on
test_build_plant.py's synthetic world and writes its record and its plant (75) and decoy (37) pools; fill_pins fills
the pins from that record (test_d2_representation_pass.make_req8); REQ-23 then scores on the engine's fixture prepared
set and scripted guard (test_score_classifier.py's settings on test_representation_pass.py's env). score_classifier.py
alone refuses the plant and decoy pools (null pins); the wrapper accepts them, and its output equals score_classifier's
with the hand-filled pins document, and score_classifier.py run on a scratch tree whose pins are filled in place by
the W1 rule, except the costs block's two timings (and, for the scratch tree, the provenance's script path). Other
pools behave as before. Nothing real is read."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import types
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
import scripts.stage1 as stage1_package  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import score_classifier as sc  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import d2_representation_pass as d2m  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import d2_score_classifier as dsc  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import fill_pins as fp  # noqa: E402

import d2fixtures as dx  # noqa: E402
from d2guard import guarded  # noqa: E402  (a wrapper defect fails the tests, never errors their setup)
import test_d2_representation_pass as t2r  # noqa: E402  (D-2's REQ-8 fixture maker)
import test_representation_pass as trp  # noqa: E402  (its env fixture: the engine's fixture prepared set)
import test_score_classifier as tsc  # noqa: E402  (REQ-23's test settings on that env)

env = trp.env
sfx = trp.sfx
SC_SHA256 = "ee8ae89865e188a8e9f3430c9fbfbe129a415dcc9f3427111a7c77e02dc34549"
SC_SETTINGS_SHA256 = "5807ec750c74137f3e5c466231de9e73a0cbb5fe5411f7be29a40bbed4c8e58a"
W1_DEFAULTS = (rp.POOL_PINS_PATH, rp.POOL_PINS_SHA256)
TIMINGS = (("costs", "setup_seconds"), ("costs", "score_seconds"))
W1_SC_RUN = sc.run


@pytest.fixture(scope="module")
def req8(tmp_path_factory):
    """REQ-8's record and pools and the pins fill_pins writes from them (D-2's own maker). Guarded."""
    root = tmp_path_factory.mktemp("req8sc")
    return guarded("req8", lambda: t2r.make_req8(root))


@pytest.fixture(scope="module")
def sc_settings(env, tmp_path_factory):
    """REQ-23's settings with the env's pins and k = 5 (test_score_classifier.settings_for) in a file, and its SHA-256."""
    path = tmp_path_factory.mktemp("scs") / "score_classifier.json"
    path.write_bytes(canonical_json(tsc.settings_for(env)))
    return path, sha256_file(path)


@pytest.fixture
def wired(monkeypatch, sc_settings):
    """main() on the fixture env: the fixture loaders for real_loaders, and the privately loaded score_classifier's
    settings pin set to the test settings' SHA-256 (the only test seam). Records each module main() loads."""
    import experiments.safety_selection.loaders as loaders_module

    monkeypatch.setattr(loaders_module, "real_loaders", lambda: sfx.fixture_loaders())
    loaded = []
    real = dsc.load_classifier

    def load_classifier(*args, **kwargs):
        module = real(*args, **kwargs)
        module.SETTINGS_SHA256 = sc_settings[1]
        loaded.append((module, module.run))
        return module
    monkeypatch.setattr(dsc, "load_classifier", load_classifier)
    return loaded


def argv_of(env, sc_settings, out, pools, extra=()):
    argv = ["--prepared", str(env.prepared), "--recipe", str(env.recipe), "--anchors", str(env.anchors)]
    for pair in pools:
        argv += ["--pool", dx.spec(pair)]
    return argv + ["--out", str(out), "--settings", str(sc_settings[0]), *extra]


def d2_argv(env, sc_settings, req8, out, pools):
    return argv_of(env, sc_settings, out, pools,
                   ("--pool-pins", dx.spec(req8["filled"]), "--req8-record", dx.spec(req8["record"])))


def output_of(folder: Path) -> bytes:
    assert sorted(p.name for p in folder.iterdir()) == [sc.OUTPUT]
    return (folder / sc.OUTPUT).read_bytes()


def own_settings() -> dict:
    return json.loads(dsc.SETTINGS_PATH.read_bytes())


# ----- the W1 file alone -------------------------------------------------------------------------------------------


def test_score_classifier_alone_refuses_the_plant_and_decoy_pools(env, req8, sc_settings, wired, tmp_path, monkeypatch,
                                                                 capsys):
    """The W1 file with the W1 null pins: run() and main() refuse each pool as 'not filled yet' (nothing written)."""
    for name in ("plant", "decoy"):
        with pytest.raises(s1.Refusal, match=f"pool {name} is a W1-known pool whose pin is not filled yet"):
            sc.run(prepared_root=env.prepared, recipe_path=env.recipe, anchors_path=env.anchors,
                   loaders=sfx.fixture_loaders(), settings=tsc.settings_for(env), settings_sha256=sc_settings[1],
                   pools=[req8[name]])
    monkeypatch.setattr(sc, "SETTINGS_SHA256", sc_settings[1])
    assert sc.main(argv_of(env, sc_settings, tmp_path / "w1", [req8["plant"], req8["decoy"]])) == 2
    assert "not filled yet" in capsys.readouterr().err and not (tmp_path / "w1").exists()


# ----- the end-to-end ------------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def e2e(env, req8, sc_settings, tmp_path_factory):
    """d2_score_classifier.main on the dev units, the plant and the decoy (one run), and the reference: the W1
    module's run() with the hand-filled pins document (same settings SHA-256). Guarded."""
    root = tmp_path_factory.mktemp("e2esc")
    return guarded("e2e", lambda: make_e2e(env, req8, sc_settings, root))


def make_e2e(env, req8, sc_settings, root):
    import experiments.safety_selection.loaders as loaders_module

    pools = [req8["plant"], req8["decoy"]]
    real_loaders, real_load = loaders_module.real_loaders, dsc.load_classifier
    loaded = []

    def load_classifier(*args, **kwargs):
        module = real_load(*args, **kwargs)
        module.SETTINGS_SHA256 = sc_settings[1]
        loaded.append((module, module.run))
        return module
    loaders_module.real_loaders, dsc.load_classifier = (lambda: sfx.fixture_loaders()), load_classifier
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            code = dsc.main(d2_argv(env, sc_settings, req8, root / "out", pools))
    finally:
        loaders_module.real_loaders, dsc.load_classifier = real_loaders, real_load
    assert code == 0, "d2_score_classifier refused the end-to-end"
    hand_doc = json.loads(req8["hand"])
    ref = sc.run(prepared_root=env.prepared.resolve(), recipe_path=env.recipe.resolve(),
                 anchors_path=env.anchors.resolve(), loaders=sfx.fixture_loaders(), settings=tsc.settings_for(env),
                 settings_sha256=sc_settings[1], pools=pools, pool_pins=(hand_doc, sha256_bytes(req8["hand"])))
    return {"out": output_of(root / "out"), "ref": ref[sc.OUTPUT], "pools": pools, "loaded": loaded,
            "stdout": stdout.getvalue()}


def test_d2_accepts_the_plant_and_decoy_pools(e2e, req8, env):
    doc = json.loads(e2e["out"])
    assert doc["pools"]["plant"]["sha256"] == req8["plant"][1] and doc["pools"]["plant"]["items"] == 75
    assert doc["pools"]["decoy"]["sha256"] == req8["decoy"][1] and doc["pools"]["decoy"]["items"] == 37
    assert len(doc["pools"]["plant"]["rows"]) == 75 and len(doc["pools"]["decoy"]["rows"]) == 37
    inputs = doc["provenance"]["inputs"]
    assert inputs["pool_pins"] == req8["filled"][1]
    assert (inputs["pool_plant"], inputs["pool_decoy"]) == (req8["plant"][1], req8["decoy"][1])
    assert doc["provenance"]["script"] == "scripts/stage1/score_classifier.py"
    assert doc["provenance"]["script_sha256"] == SC_SHA256
    assert set(doc["rows"]) == {r for g in env.groups for r in env.view.groups["dev"][g]}


def test_d2_output_equals_score_classifier_with_the_hand_filled_pins_document(e2e):
    """Byte for byte once the costs block's two wall-clock timings are removed; every other costs field equal."""
    assert canonical_json(dx.without(e2e["out"], *TIMINGS)) == canonical_json(dx.without(e2e["ref"], *TIMINGS))
    assert set(json.loads(e2e["out"])["costs"]) == set(json.loads(e2e["ref"])["costs"])
    assert json.loads(e2e["out"])["costs"]["rows"] > 112


def scratch_tree(tmp_path: Path, filled_bytes: bytes):
    """The W1 fill rule done in place on a scratch tree: representation_pass.py with its literal POOL_PINS_SHA256
    replaced and settings/representation_pools.json replaced by the filled bytes (d2fixtures.hand_filled_copy), next to
    byte copies of score_classifier.py and its settings; score_classifier loaded by path from the tree (sys.path
    restored). Returns (the tree's representation_pass, the tree's score_classifier)."""
    hand_rp = dx.hand_filled_copy(tmp_path, filled_bytes)
    real = fp.w1_root() / "scripts" / "stage1"
    tree = tmp_path / "scripts" / "stage1"
    shutil.copyfile(real / "score_classifier.py", tree / "score_classifier.py")
    shutil.copyfile(real / "settings" / "score_classifier.json", tree / "settings" / "score_classifier.json")
    import importlib.util

    saved = list(sys.path)
    try:
        spec = importlib.util.spec_from_file_location("scratch_tree_score_classifier", tree / "score_classifier.py")
        hand_sc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hand_sc)
    finally:
        sys.path[:] = saved
    return hand_rp, hand_sc


def test_d2_output_equals_score_classifier_on_a_scratch_tree_filled_in_place(e2e, env, req8, sc_settings, monkeypatch,
                                                                            tmp_path):
    """score_classifier.py's own main() on a scratch tree filled in place (its by-name representation_pass is the
    tree's, with the filled literal and file; no pool_pins passed): equal to the wrapper's output except the costs
    timings and provenance.script (the tree's path); provenance.script_sha256 is the same file's."""
    import experiments.safety_selection.loaders as loaders_module

    hand_rp, hand_sc = scratch_tree(tmp_path / "tree", req8["hand"])
    assert hand_rp.POOL_PINS_SHA256 == req8["filled"][1] and sha256_file(Path(hand_sc.__file__)) == SC_SHA256
    monkeypatch.setattr(loaders_module, "real_loaders", lambda: sfx.fixture_loaders())
    monkeypatch.setattr(hand_sc, "SETTINGS_SHA256", sc_settings[1])
    monkeypatch.setattr(stage1_package, "representation_pass", hand_rp)
    monkeypatch.setitem(sys.modules, "scripts.stage1.representation_pass", hand_rp)
    assert hand_sc.main(argv_of(env, sc_settings, tmp_path / "out", e2e["pools"])) == 0
    monkeypatch.undo()
    mine = output_of(tmp_path / "out")
    assert json.loads(mine)["provenance"]["script"] != json.loads(e2e["out"])["provenance"]["script"]
    assert json.loads(mine)["provenance"]["script_sha256"] == SC_SHA256
    drop = TIMINGS + (("provenance", "script"),)
    assert canonical_json(dx.without(mine, *drop)) == canonical_json(dx.without(e2e["out"], *drop))


def test_run_is_restored_and_the_w1_module_untouched(e2e):
    """After main(): the private module's run is its own again; the module was private; the normally imported W1
    score_classifier and representation_pass never changed."""
    [(module, run)] = e2e["loaded"]
    assert module.__name__ == dsc.MODULE_NAME and dsc.MODULE_NAME not in sys.modules and module is not sc
    assert module.run is run and run.__name__ == "run" and run is not W1_SC_RUN
    assert module.run.__kwdefaults__ == {"pools": (), "pool_pins": None}
    assert sc.run is W1_SC_RUN and rp.load_pool_pins.__defaults__ == W1_DEFAULTS
    assert sha256_file(Path(sc.__file__)) == SC_SHA256 and sha256_file(rp.POOL_PINS_PATH) == dx.W1_PINS_SHA256
    assert sys.modules["scripts.stage1.representation_pass"] is rp and stage1_package.representation_pass is rp


def test_main_prints_the_d2_facts_text_free(e2e, req8):
    first, *rest = e2e["stdout"].splitlines()
    assert first == (f"D-2: filled pins {req8['filled'][1]} (decoy {req8['decoy'][1]} 37 items, plant {req8['plant'][1]} "
                     f"75 items); score_classifier.py {SC_SHA256}; W1 pins {dx.W1_PINS_SHA256}")
    assert rest == [f"  {sha256_bytes(e2e['out'])}  {sc.OUTPUT}"]
    texts = [t for name in ("plant", "decoy") for i in json.loads(req8[name][0].read_bytes())["items"]
             for t in (i["prompt"], i["response"])]
    assert not any(t in e2e["stdout"] or t.encode() in e2e["out"] for t in texts if len(t) > 5)


# ----- the replacement of run -----------------------------------------------------------------------------------------


def test_run_classifier_replaces_exactly_run(req8, monkeypatch):
    """Inside the call: run passes the filled pins (load_pool_pins on the filled file and its checked SHA-256) and
    every keyword it was given; main() gets the forwarded arguments unchanged; no other module global changes; a
    caller's own pool_pins refuses."""
    module = dsc.load_classifier(own_settings())
    base = dx.load_base()
    path, sha = req8["filled"][0].resolve(), req8["filled"][1]
    calls, seen = [], {}

    def recorder(*, pools=(), pool_pins=None, **kwargs):
        calls.append({"pools": pools, "pool_pins": pool_pins, **kwargs})
        return {}
    monkeypatch.setattr(module, "run", recorder)
    before = {k: v for k, v in vars(module).items() if k != "run"}

    def fake_main(argv):
        seen["argv"] = argv
        seen["same"] = {k: v for k, v in vars(module).items() if k not in ("run", "main")} == \
            {k: v for k, v in before.items() if k != "main"}
        module.run(prepared_root="P", pools=["x"])
        with pytest.raises(s1.Refusal, match="passed pool pins of its own"):
            module.run(prepared_root="P", pool_pins=({}, "0" * 64))
        return 0
    monkeypatch.setattr(module, "main", fake_main)
    assert dsc.run_classifier(module, base, ["--x"], path, sha) == 0
    assert seen == {"argv": ["--x"], "same": True}
    [call] = calls
    assert call["prepared_root"] == "P" and call["pools"] == ["x"] and call["pool_pins"][1] == sha
    assert call["pool_pins"][0]["pools"]["plant"]["sha256"] == req8["plant"][1]
    assert call["pool_pins"][0] == json.loads(req8["hand"])
    assert module.run is recorder


def test_the_restore_after_an_exception(req8, monkeypatch):
    """An exception other than a refusal inside score_classifier's main(): it propagates, and run is the module's own
    again."""
    module = dsc.load_classifier(own_settings())
    original = module.run
    seen = []

    def boom(argv):
        seen.append(module.run)
        raise RuntimeError("synthetic failure inside score_classifier")
    monkeypatch.setattr(module, "main", boom)
    with pytest.raises(RuntimeError, match="synthetic failure inside score_classifier"):
        dsc.run_classifier(module, dx.load_base(), [], req8["filled"][0].resolve(), req8["filled"][1])
    assert len(seen) == 1 and seen[0] is not original and seen[0].__name__ == "filled_run"
    assert module.run is original


def test_the_restore_after_a_refusal(env, req8, sc_settings, wired, tmp_path, capsys):
    """A pool whose given SHA-256 is wrong: score_classifier refuses inside the call (exit 2, nothing written); run is
    restored."""
    bad = (req8["plant"][0], "0" * 64)
    assert dsc.main(d2_argv(env, sc_settings, req8, tmp_path / "out", [bad])) == 2
    assert "a pool file hashes to" in capsys.readouterr().err and not (tmp_path / "out").exists()
    [(module, run)] = wired
    assert module.run is run


def test_run_classifier_refuses_a_run_that_is_not_the_w1_run(req8, monkeypatch):
    module = dsc.load_classifier(own_settings())
    monkeypatch.setattr(module, "run", lambda **kwargs: {})
    monkeypatch.setattr(module, "main", lambda argv: (_ for _ in ()).throw(AssertionError("main ran")))
    with pytest.raises(s1.Refusal, match="does not take pool_pins=None"):
        dsc.run_classifier(module, dx.load_base(), [], req8["filled"][0], req8["filled"][1])


def test_the_filled_file_changed_after_the_check_refuses(env, req8, sc_settings, wired, monkeypatch, tmp_path, capsys):
    """The filled file gains one byte after every D-2 check passed: run reads it again against the checked SHA-256 and
    score_classifier's main refuses (exit 2, nothing written)."""
    filled = dx.write(tmp_path / "filled.json", req8["filled"][0].read_bytes())
    real = d2m.checked
    calls = []

    def checked(*args, **kwargs):
        result = real(*args, **kwargs)
        calls.append(result[2])
        filled[0].write_bytes(filled[0].read_bytes() + b" ")
        return result
    monkeypatch.setattr(d2m, "checked", checked)
    argv = argv_of(env, sc_settings, tmp_path / "out", [req8["plant"], req8["decoy"]],
                   ("--pool-pins", dx.spec(filled), "--req8-record", dx.spec(req8["record"])))
    assert dsc.main(argv) == 2
    err = capsys.readouterr().err
    assert calls == [filled[1]]
    assert f"settings representation_pools hash to {sha256_file(filled[0])}, expected {filled[1]}" in err
    assert err.rstrip().endswith("(nothing written)") and not (tmp_path / "out").exists()


# ----- other pools: as before -------------------------------------------------------------------------------------------


def test_other_pools_behave_as_before(env, req8, sc_settings, wired, monkeypatch, tmp_path, capsys):
    """An S3 pool refuses under D-2 as under the W1 null pins (the classifier scores plant and decoy only); a plant pool
    with other bytes refuses under both; with no pool the output equals the W1 run's except the pins' SHA-256 and the
    costs timings."""
    items = [{"id": "s3-1", "prompt": "Synthetic S3 prompt about lakes?", "response": "Synthetic S3 answer."}]
    s3 = trp.pool_file(tmp_path, items, "s3_safe")
    monkeypatch.setattr(sc, "SETTINGS_SHA256", sc_settings[1])
    assert sc.main(argv_of(env, sc_settings, tmp_path / "w1", [s3])) == 2
    assert "is not one the classifier scores" in capsys.readouterr().err
    assert dsc.main(d2_argv(env, sc_settings, req8, tmp_path / "d2", [s3])) == 2
    assert "is not one the classifier scores" in capsys.readouterr().err
    other = trp.pool_file(tmp_path, [dict(i, id=f"add-plant-{j:03d}") for j, i in enumerate(items * 75, 1)], "plant")
    assert sc.main(argv_of(env, sc_settings, tmp_path / "w1", [other])) == 2
    assert "not filled yet" in capsys.readouterr().err
    assert dsc.main(d2_argv(env, sc_settings, req8, tmp_path / "d2", [other])) == 2
    assert f"pool plant hashes to {other[1]}, the pool pins name {req8['plant'][1]}" in capsys.readouterr().err
    assert not (tmp_path / "w1").exists() and not (tmp_path / "d2").exists()
    assert sc.main(argv_of(env, sc_settings, tmp_path / "w1", [])) == 0
    assert dsc.main(d2_argv(env, sc_settings, req8, tmp_path / "d2", [])) == 0
    a, b = output_of(tmp_path / "d2"), output_of(tmp_path / "w1")
    assert json.loads(a)["provenance"]["inputs"]["pool_pins"] == req8["filled"][1]
    assert json.loads(b)["provenance"]["inputs"]["pool_pins"] == dx.W1_PINS_SHA256
    drop = TIMINGS + (("provenance", "inputs", "pool_pins"),)
    assert canonical_json(dx.without(a, *drop)) == canonical_json(dx.without(b, *drop))


# ----- main(): every check runs before score_classifier ------------------------------------------------------------------


def _forbid_classifier_main(monkeypatch):
    real = dsc.load_classifier

    def load_classifier(*args, **kwargs):
        module = real(*args, **kwargs)
        module.main = lambda argv: (_ for _ in ()).throw(AssertionError("score_classifier ran"))
        return module
    monkeypatch.setattr(dsc, "load_classifier", load_classifier)


@pytest.mark.parametrize("case,match", [
    ("other_field", "not exactly in pools.decoy.sha256 and pools.plant.sha256"),
    ("wrong_hash", "the filled pin of pool plant"),
    ("unfilled", "not exactly in"),
    ("pins_sha", "the filled pins file hashes to"),
    ("record_sha", "REQ-8's record hashes to"),
    ("record_kind", "is not a version-1 'stage1 plant record'"),
    ("record_other_plant", "the filled pin of pool plant"),
    ("record_other_script", "REQ-8's record was not written by the W1 build_plant.py"),
    ("no_hash", "--pool-pins is PATH:SHA256"),
    ("record_no_hash", "--req8-record is PATH:SHA256"),
])
def test_main_refuses_before_score_classifier_runs(env, req8, sc_settings, monkeypatch, tmp_path, capsys, case, match):
    _forbid_classifier_main(monkeypatch)
    filled, record = dx.spec(req8["filled"]), dx.spec(req8["record"])
    if case == "other_field":
        doc = json.loads(req8["hand"])
        doc["pools"]["plant"]["items"] = 74
        filled = dx.spec(dx.write(tmp_path / "f.json", canonical_json(doc)))
    elif case == "wrong_hash":
        filled = dx.spec(dx.write(tmp_path / "f.json", dx.hand_fill(dx.w1_pins_bytes(), "5" * 64, req8["decoy"][1])))
    elif case == "unfilled":
        filled = dx.spec((dx.w1_pins_path(), dx.W1_PINS_SHA256))
    elif case == "pins_sha":
        filled = dx.spec((req8["filled"][0], "0" * 64))
    elif case == "record_sha":
        record = dx.spec((req8["record"][0], "0" * 64))
    elif case == "record_kind":
        record = dx.spec(dx.write(tmp_path / "r.json", canonical_json(dict(req8["record_doc"], kind="stage1 plant rows"))))
    elif case == "record_other_plant":
        doc = json.loads(json.dumps(req8["record_doc"]))
        doc["pools"]["plant"]["sha256"] = doc["full_files"]["plant.pool.json"] = "6" * 64
        record = dx.spec(dx.write(tmp_path / "r.json", canonical_json(doc)))
    elif case == "record_other_script":
        doc = json.loads(json.dumps(req8["record_doc"]))
        doc["provenance"]["script_sha256"] = "7" * 64
        record = dx.spec(dx.write(tmp_path / "r.json", canonical_json(doc)))
    elif case == "no_hash":
        filled = str(req8["filled"][0])
    elif case == "record_no_hash":
        record = str(req8["record"][0])
    argv = argv_of(env, sc_settings, tmp_path / "out", [req8["plant"], req8["decoy"]],
                   ("--pool-pins", filled, "--req8-record", record))
    assert dsc.main(argv) == 2
    err = capsys.readouterr().err
    assert match in err and err.rstrip().endswith("(nothing written)") and not (tmp_path / "out").exists()


def classifier_root(tmp_path: Path) -> Path:
    """d2fixtures.fake_root (the manifest, representation_pass.py, the W1 pins) plus score_classifier.py."""
    root = dx.fake_root(tmp_path)
    rel = own_settings()["base"]["script"]
    shutil.copyfile(fp.w1_root() / rel, root / rel)
    return root


def test_a_changed_score_classifier_byte_refuses(req8, tmp_path, monkeypatch, capsys):
    """load_classifier() and main() against a tmp root whose score_classifier.py has one changed byte."""
    root = classifier_root(tmp_path)
    dx.flip(root / own_settings()["base"]["script"], b'OUTPUT = "classifier_scores.json"',
            b'OUTPUT = "classifier_scores.jsom"')
    with pytest.raises(s1.Refusal, match="score_classifier.py hashes to"):
        dsc.load_classifier(own_settings(), root)
    monkeypatch.setattr(fp, "w1_root", lambda: root)
    assert dsc.main(["--prepared", "p", "--recipe", "r", "--anchors", "a", "--out", str(tmp_path / "o"),
                     "--pool-pins", dx.spec(req8["filled"]), "--req8-record", dx.spec(req8["record"])]) == 2
    err = capsys.readouterr().err
    assert "score_classifier.py hashes to" in err and not (tmp_path / "o").exists()


@pytest.mark.parametrize("key,what", [("script_sha256", "score_classifier.py"),
                                      ("settings_sha256", "score_classifier.json")])
def test_a_pin_the_w1_manifest_does_not_name_refuses(key, what):
    own = own_settings()
    own["base"][key] = "8" * 64
    with pytest.raises(s1.Refusal, match=f"{what}: the W1 manifest names .*, the D-2 settings pin {'8' * 64}"):
        dsc.load_classifier(own)


def test_the_module_literal_settings_pin_is_checked(tmp_path):
    """A score_classifier.py whose own SETTINGS_SHA256 differs (its manifest entry and this file's pin updated to the
    changed bytes, so only the literal check is left) refuses."""
    root = classifier_root(tmp_path)
    own = own_settings()
    path = root / own["base"]["script"]
    dx.flip(path, SC_SETTINGS_SHA256.encode(), b"9" * 64)
    new = sha256_file(path)
    manifest = root / own["base"]["manifest"]
    dx.flip(manifest, SC_SHA256.encode(), new.encode())
    own["base"]["script_sha256"] = new
    with pytest.raises(s1.Refusal, match="score_classifier.py's own settings pin is not"):
        dsc.load_classifier(own, root)


def test_the_module_runs_privately_from_the_checked_bytes(monkeypatch):
    """score_classifier.py is read once (the checked bytes are the ones run) and the module is not in sys.modules."""
    target = (fp.w1_root() / own_settings()["base"]["script"]).resolve()
    real = Path.read_bytes
    reads = []

    def read_bytes(self):
        data = real(self)
        if Path(self).resolve() == target:
            reads.append(1)
            if len(reads) > 1:
                return data.replace(b'OUTPUT = "classifier_scores.json"', b'OUTPUT = "changed.json"')
        return data
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    module = dsc.load_classifier(own_settings())
    assert module.OUTPUT == "classifier_scores.json" and len(reads) == 1
    assert module.__name__ == dsc.MODULE_NAME and dsc.MODULE_NAME not in sys.modules
    assert Path(module.__file__).resolve() == target and module.run is not W1_SC_RUN


def test_a_changed_own_settings_byte_refuses(req8, tmp_path, monkeypatch, capsys):
    copy_path = tmp_path / "d2_score_classifier.json"
    copy_path.write_bytes(dsc.SETTINGS_PATH.read_bytes().replace(b'"version": 1', b'"version": 2'))
    monkeypatch.setattr(dsc, "SETTINGS_PATH", copy_path)
    assert dsc.main(["--prepared", "p", "--recipe", "r", "--anchors", "a", "--out", str(tmp_path / "o"),
                     "--pool-pins", dx.spec(req8["filled"]), "--req8-record", dx.spec(req8["record"])]) == 2
    assert "settings d2_score_classifier hash to" in capsys.readouterr().err


def test_own_settings_must_name_the_d2_settings(monkeypatch):
    monkeypatch.setattr(fp, "SETTINGS_SHA256", "4" * 64)
    with pytest.raises(s1.Refusal, match="name D-2's settings d6fa043f"):
        dsc.load_settings()


def test_the_by_name_representation_pass_is_checked(tmp_path, monkeypatch):
    """The module score_classifier's _run gets from `from scripts.stage1 import representation_pass` must hash to
    D-2's pin: the W1 one passes; a module from a changed copy, or one with no file, refuses."""
    dsc.check_by_name_representation_pass()
    changed = tmp_path / "representation_pass.py"
    changed.write_bytes(Path(rp.__file__).read_bytes() + b"\n")
    for origin in (str(changed), None):
        fake = types.ModuleType("scripts.stage1.representation_pass")
        fake.__file__ = origin
        monkeypatch.setattr(stage1_package, "representation_pass", fake)
        monkeypatch.setitem(sys.modules, "scripts.stage1.representation_pass", fake)
        with pytest.raises(s1.Refusal, match="imports by name hashes to"):
            dsc.check_by_name_representation_pass()
        monkeypatch.undo()
    dsc.check_by_name_representation_pass()


def test_main_checks_the_by_name_representation_pass(req8, monkeypatch, tmp_path, capsys):
    _forbid_classifier_main(monkeypatch)
    real = dsc.check_by_name_representation_pass
    calls = []

    def check():
        calls.append(1)
        raise s1.Refusal("synthetic by-name refusal")
    monkeypatch.setattr(dsc, "check_by_name_representation_pass", check)
    assert dsc.main(["--prepared", "p", "--recipe", "r", "--anchors", "a", "--out", str(tmp_path / "o"),
                     "--pool-pins", dx.spec(req8["filled"]), "--req8-record", dx.spec(req8["record"])]) == 2
    assert calls == [1] and "synthetic by-name refusal" in capsys.readouterr().err
    assert real is not check


# ----- the CLI and the settings ---------------------------------------------------------------------------------------------


def test_forwarded_arguments_are_score_classifiers_own():
    import argparse

    args = argparse.Namespace(prepared=Path("P"), recipe=Path("R"), anchors=Path("A"), pool=["x:1", "y:2"],
                              out=Path("O"), settings=Path("S"), pool_pins="F:1", req8_record="Q:2")
    assert dsc.forwarded(args) == ["--prepared", "P", "--recipe", "R", "--anchors", "A", "--pool", "x:1", "--pool", "y:2",
                                   "--out", "O", "--settings", "S"]
    args.settings, args.pool = None, []
    assert dsc.forwarded(args) == ["--prepared", "P", "--recipe", "R", "--anchors", "A", "--out", "O"]


def test_the_committed_settings():
    """This file's settings pin score_classifier.py and its settings at the W1 manifest's entries (which the files
    hash to), and D-2's settings at fill_pins' pin; same engine and registry record as D-2's settings."""
    doc, digest = dsc.load_settings()
    assert digest == dsc.SETTINGS_SHA256 == sha256_file(dsc.SETTINGS_PATH)
    d2 = dx.committed_d2()
    root = fp.w1_root()
    entries, _ = fp.manifest_entries(root / doc["base"]["manifest"])
    assert doc["base"]["manifest"] == d2["base"]["manifest"]
    for path_key, sha_key in (("script", "script_sha256"), ("settings", "settings_sha256")):
        rel = doc["base"][path_key]
        assert entries[rel] == doc["base"][sha_key] == sha256_file(root / rel)
    assert (doc["base"]["script_sha256"], doc["base"]["settings_sha256"]) == (SC_SHA256, SC_SETTINGS_SHA256)
    assert doc["d2_settings_sha256"] == fp.SETTINGS_SHA256 == sha256_file(root / doc["d2_settings"])
    assert (doc["engine_x"], doc["labels_sha256"]) == (d2["engine_x"], d2["labels_sha256"])
    assert sc.SETTINGS_SHA256 == SC_SETTINGS_SHA256
    assert dsc.SETTINGS_PATH.read_bytes() == canonical_json(doc)


def test_the_fixtures_here_are_guarded():
    """Every module fixture here that runs D-2 code goes through the guard (d2guard; test_d2_fixture_guard.py's rule)."""
    text = Path(__file__).read_text()
    for name in ("req8", "e2e"):
        body = text.split(f"\ndef {name}(", 1)[1].split("\n\n\n", 1)[0]
        assert "guarded(" in body, f"{name} is not guarded"
