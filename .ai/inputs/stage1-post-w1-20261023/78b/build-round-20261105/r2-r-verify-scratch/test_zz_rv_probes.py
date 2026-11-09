"""The R2 Track R verifier's probes (scratch only; ENGINEERING FIXTURES; no real unit, answer or prompt is read).

P4-a  compare --against untuned through the wrapper: refused by the wrapper's own --reference rule (any family).
P4-b  check --untuned on an init unit made under a recipe that differs from the settings' recipe only in train.lr
      (Llama's theta0 case, c5462c77 vs MAIN_F 74758af1): the unchanged 1B read_untuned refuses (training identity);
      the same unit under its own recipe's settings passes.
P3    safe_lora transform --point conditional through the wrapper: not refused (a point P2 section 3.2 does not carry).
LBL   the derived files' labels_sha256 is the 1B file's, not the registry they were written on.
VD    the derived Safe LoRA files keep the 1B v_diagnostic.measure text naming K = 39 while their default K is 78.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402
import refs_fixtures as rf  # noqa: E402

from experiments.safety_selection.common import sha256_file  # noqa: E402
from scripts.scale78b import make_refs_settings_78b as mk  # noqa: E402
from scripts.scale78b import refs_78b as rw  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return rf.ea_world(tmp_path_factory.mktemp("rv-ea"))


def test_P4a_compare_against_untuned_is_refused_by_the_wrapper(world, tmp_path):
    theta0_like = tmp_path / "theta0-COMPLETE.json"                 # any file that is not seed S's a0 COMPLETE.json
    theta0_like.write_bytes(b'{"complete": true}')
    code, out, err = rf.wrapped(world, ["compare", "--unit", tmp_path / "unit", "--reference", theta0_like,
                                        "--reference-eval", tmp_path / "ev", "--out", tmp_path / "c.json",
                                        "--against", "untuned"])
    print("P4a", code, err.strip().splitlines()[-1][:200])
    assert code == 2 and "pinned a0 unit is" in err and not (tmp_path / "c.json").exists()


def test_P4b_read_untuned_refuses_an_init_unit_of_another_lr(world, tmp_path):
    other = fb.recipe()
    other["train"]["lr"] = other["train"]["lr"] / 2                 # only train.lr differs (theta0's case on Llama)
    _, init_other = fb.gate_a_resumed(world.prepared, tmp_path / "o" / "1102-a0-e1", rf.SEED, recipe_=other)
    _, init_same = fb.gate_a_resumed(world.prepared, tmp_path / "s" / "1102-a0-e1", rf.SEED)
    for init, ok in ((init_other, False), (init_same, True)):
        doc = rf.ea_doc(world, world.refs, untuned_unit__complete_sha256=sha256_file(init / "COMPLETE.json"))
        settings = rf.settings_of(doc, world.refs)
        if ok:
            assert ea.read_untuned(init / "COMPLETE.json", settings)["seed"] == rf.SEED
        else:
            with pytest.raises(ea.Refusal, match=r"identity differs from the settings in \['training_identity'\]"):
                ea.read_untuned(init / "COMPLETE.json", settings)
        # and through the wrapper's eval_adapter check --untuned
        world.refs.put("eval_adapter", doc)
        try:
            code, out, err = rf.wrapped(world, ["check", "--untuned", init / "COMPLETE.json"])
        finally:
            world.refs.put("eval_adapter", world.doc)
        print("P4b", ok, code, (err.strip().splitlines() or [""])[-1][:200])
        assert (code == 0) is ok


def test_P3_the_conditional_point_is_not_refused_by_the_wrapper(tmp_path):
    import b11_fixtures as fx11
    from scripts.stage1_s1 import safe_lora as sl

    t = fx11.build_tiny(tmp_path / "tiny")
    doc = copy.deepcopy(t.doc)
    doc["adapter"]["accepted"] = {str(rf.SEED): {"fingerprint": t.fingerprint}}
    refs = rf.Refs(tmp_path / "fam")
    refs.manifest = "a" * 64
    rf.o78.oext_inputs(tmp_path / "oext", refs, branch="pending_w1_18")
    refs.put("safe_lora", doc)
    refs.put("eval_adapter", b"{}")
    out = tmp_path / "out"
    code, o, err = rf.call(rw.main, ["safe_lora", *refs.refs_leading(), "transform", "--point", "conditional",
                                     "--adapter", str(t.adapter_file), "--seed", str(rf.SEED), "--aligned",
                                     str(t.aligned), "--base", str(t.base), "--out", str(out)])
    record = json.loads((out / doc["outputs"]["record"]).read_bytes()) if code == 0 else {}
    print("P3", code, sorted(record.get("points", {})), doc["transform"]["points"]["conditional"]["k"])
    assert code == 0 and sorted(record["points"]) == ["conditional"]


def test_LBL_the_derived_files_record_a_registry_they_were_not_written_on():
    now = s1.labels_sha256()
    one_b = json.loads((mk.REPO / mk.BASE["eval_adapter"][0]).read_bytes())["labels_sha256"]
    oext = json.loads((mk.SETTINGS_DIR / "oext_eval__olmo2-7b.json").read_bytes())["labels_sha256"]
    derived = {json.loads(p.read_bytes())["labels_sha256"] for g in ("eval_adapter__*__11*.json", "safe_lora__*__11*.json") for p in mk.SETTINGS_DIR.glob(g)}
    print("LBL now", now[:12], "1B", one_b[:12], "TrackO", oext[:12], "derived", sorted(d[:12] for d in derived))
    assert derived == {one_b} and one_b != now and oext == now


def test_VD_the_vcheck_measure_text_names_1bs_k():
    for p in sorted(mk.SETTINGS_DIR.glob("safe_lora__*__11*.json")):
        d = json.loads(p.read_bytes())
        assert d["transform"]["points"]["default"]["k"] == 78
        assert "K = 39" in d["v_diagnostic"]["measure"] and "K = 78" not in d["v_diagnostic"]["measure"]
    print("VD", len(list(mk.SETTINGS_DIR.glob("safe_lora__*__11*.json"))), "files keep 'K = 39' in v_diagnostic.measure")


def test_ABS_a_wait_field_absent_from_its_file_crashes_instead_of_exit_2(tmp_path):
    """Track O's W2-3 fixed this case (R2-w-absent-field); refs_78b.with_placeholders indexes the field directly."""
    import test_refs_78b_settings as ts
    sdir = ts.make(tmp_path, mk.load_pins()[0])
    name = mk.index_name("llama31-8b", 1104)
    index = json.loads((sdir / name).read_bytes())
    for wait in index["waits"]:
        if wait["pin"] == "REF_UNIT_1104":
            wait["fields"]["eval_adapter"].append({"path": "reference_units.1104.no_such_field", "kind": "sha256"})
    (sdir / name).write_bytes(mk.dumps(index))
    leading = ["--family", "llama31-8b", "--seed", "1104", "--index", str(sdir / name), "--index-sha256",
               sha256_file(sdir / name)]
    try:
        code, out, err = rf.call(rw.main, ["check", *leading])
        outcome = ("exit", code, (err.strip().splitlines() or [""])[-1][:160])
    except Exception as exc:  # noqa: BLE001
        outcome = ("raised", type(exc).__name__)
    print("ABS", outcome)
    assert outcome[0] == "raised" and outcome[1] == "KeyError"


def test_FB_the_fallback_switch_in_place_leaves_the_six_seed_files(tmp_path):
    """P9: 'one pins edit and a maker run'. In place (a settings folder holding the 6-seed files), the maker writes
    the 3-seed files and leaves 1105-1107's; the committed-state consistency check then fails."""
    import shutil
    import test_refs_78b_settings as ts
    sdir = tmp_path / "settings"
    shutil.copytree(mk.SETTINGS_DIR, sdir)               # the committed state, labels re-made below by the maker
    pins = copy.deepcopy(mk.load_pins()[0])
    pins["reference_set"] = "three_seed"
    ts.make(tmp_path, pins, sdir)
    left = sorted(p.name for p in sdir.glob("*__11*.json") if p.name.split("__")[-1][:4] in ("1105", "1106", "1107"))
    print("FB stale files left:", len(left))
    with pytest.raises(AssertionError):
        ts.consistency(sdir, tmp_path / "pins.json")
    assert len(left) == 18
