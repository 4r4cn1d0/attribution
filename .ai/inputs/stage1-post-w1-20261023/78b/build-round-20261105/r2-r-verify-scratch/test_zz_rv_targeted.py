"""The R2 Track R verifier's targeted tests for its surviving extra mutants (scratch only; ENGINEERING FIXTURES)."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

import refs_fixtures as rf  # noqa: E402

from scripts.scale78b import refs_78b as rw  # noqa: E402


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return rf.ea_world(tmp_path_factory.mktemp("rv-t"))


def test_T1_compare_reference_is_seed_s_pin(world, tmp_path):
    other = tmp_path / "other.json"
    other.write_bytes(b"{}")
    code, _, err = rf.wrapped(world, ["compare", "--unit", tmp_path / "u", "--reference", other, "--reference-eval",
                                      tmp_path / "e", "--out", tmp_path / "c.json"])
    assert code == 2 and "seed 1102's pinned a0 unit is" in err


def test_T2_evaluate_reference_is_seed_s_pin(world, tmp_path):
    code, _, err = rf.wrapped(world, ["evaluate", "--prepared", world.prepared, "--recipe", world.recipe, "--reference",
                                      world.recipe, "--source-run", tmp_path, "--out", tmp_path / "x", "--mode",
                                      "certify"])
    assert code == 2 and "seed 1102's pinned a0 unit is" in err and not (tmp_path / "x").exists()


def test_T3_run_seed_is_s(world, tmp_path):
    code, _, err = rf.wrapped(world, ["run", *rf.common(world), "--seed", "1103", "--regen-out", tmp_path / "r",
                                      "--eval-root", tmp_path / "e", "--evaluations", "certify"])
    assert code == 2 and "is not this index's reference seed" in err and not (tmp_path / "r").exists()


def test_T4_the_b10_files_manifest_is_the_indexs(world, tmp_path):
    refs = world.refs
    refs.put("eval_adapter", rf.ea_doc(world, refs, prepared__manifest_sha256="2" * 64))
    try:
        code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", tmp_path / "x"])
    finally:
        refs.put("eval_adapter", world.doc)
    assert code == 2 and "pins the manifest" in err and not (tmp_path / "x").exists()


def test_T5_the_index_kind_is_checked(world):
    code, _, err = rf.call(rw.main, ["check", *world.refs.refs_leading(kind="scale78b oext settings index")])
    assert code == 2 and "is not the scale78b refs index" in err


def test_T6_check_holds_the_bindings(world):
    refs = world.refs
    entry = {**rf.sl_entry(refs), "settings": {"path": refs.label("safe_lora"), "sha256": "1" * 64}}
    refs.put("eval_adapter", rf.ea_doc(world, refs, external_transforms={"safe_lora": entry}))
    try:
        code, _, err = rf.call(rw.main, ["check", *refs.refs_leading()])
    finally:
        refs.put("eval_adapter", world.doc)
    assert code == 2 and "Safe LoRA pin is not the index's safe_lora file" in err


def test_T7_a_non_digit_seed_exits_2():
    code, _, err = rf.call(rw.main, ["check", "--family", "olmo2-7b", "--seed", "11o2", "--index", "x",
                                     "--index-sha256", "0" * 64])
    assert code == 2 and "--seed is required" in err
