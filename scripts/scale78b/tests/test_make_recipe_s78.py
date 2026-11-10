"""T6a: each S_78 config differs from its main config only in Gate B's recipe-S field set (the 1B pair's difference);
its config_sha256 comes from the engine's function under -I -B; its training identity equals the main config's
(P78:76: 36738c38… OLMo-2-7B, 5b4451e1… Llama-3.1-8B; at 1B S and REC share f46279e5…); the engine's loader accepts
it; the maker's refusals. Runs under the engine's environment (it imports experiments.safety_selection.config)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.safety_selection.config import config_sha256, load_recipe, training_identity, validate_recipe
from scripts.scale78b import make_recipe_s78 as mk

ROOT = Path(__file__).resolve().parents[3]
# A synthetic anchor-file hash for the tests only: no family's anchor job has run (the real value comes from its
# sealed anchor record, anchors.sealed.json "anchor_file_sha256").
TEST_ANCHORS = hashlib.sha256(b"scale78b test anchor file, not a real anchor record").hexdigest()
FAMILIES = sorted(mk.MAIN)


def frozen_family_probe_reading():
    spec = importlib.util.spec_from_file_location("fpr_for_s78_tests", ROOT / "scripts" / "family_probe_reading.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_main(family: str) -> dict:
    return validate_recipe(json.loads((mk.CONFIGS / mk.MAIN[family]["file"]).read_text(encoding="utf-8")))


def test_the_1b_pair_differs_in_exactly_the_four_recipe_s_fields():
    rec = json.loads(mk.REC_1B.read_text(encoding="utf-8"))
    s = json.loads(mk.S_1B.read_text(encoding="utf-8"))
    assert config_sha256(rec) == mk.REC_1B_SHA256 and config_sha256(s) == mk.S_1B_SHA256
    assert mk.diff_paths(rec, s) == set(mk.RECIPE_S_FIELDS)
    assert s["attribution"]["checkpoints"] == mk.RECIPE_S_CHECKPOINTS
    assert s["attribution"]["query_bank"].startswith("anchors-") and len(s["attribution"]["query_bank"]) == 8 + 64
    assert training_identity(rec) == training_identity(s) == "f46279e5830f477742189ef03c03ffc0ec86107ae060bb5ef9034ba47acabfac"


@pytest.mark.parametrize("family", FAMILIES)
def test_the_main_config_pins_hold(family):
    main = load_main(family)
    assert config_sha256(main) == mk.MAIN[family]["config_sha256"]
    assert training_identity(main) == mk.MAIN[family]["training_identity"]
    assert main["attribution"]["checkpoints"] == ["q", "e1", "e3"] and main["attribution"]["query_bank"] == "ref"


@pytest.mark.parametrize("family", FAMILIES)
def test_s78_differs_from_its_main_config_only_in_the_recipe_s_field_set(family):
    main = load_main(family)
    s = mk.make(main, family, TEST_ANCHORS)
    assert mk.diff_paths(main, s) == set(mk.RECIPE_S_FIELDS) == mk.diff_paths(
        json.loads(mk.REC_1B.read_text(encoding="utf-8")), json.loads(mk.S_1B.read_text(encoding="utf-8")))
    assert s["attribution"]["checkpoints"] == ["q", "e1"]
    assert s["attribution"]["query_bank"] == f"anchors-{TEST_ANCHORS}"
    assert s["name"] == mk.MAIN[family]["file"].replace("-20261008.json", "").replace("-20261010.json", "") + "-gateb-20261105"
    assert list(s) == list(main) and list(s["attribution"]) == list(main["attribution"])      # the key order is kept


@pytest.mark.parametrize("family", FAMILIES)
def test_s78_has_the_main_configs_training_identity_and_evaluation_config(family):
    main = load_main(family)
    s = validate_recipe(mk.make(main, family, TEST_ANCHORS))
    assert training_identity(s) == training_identity(main) == mk.MAIN[family]["training_identity"]
    assert config_sha256(s) != config_sha256(main)
    fr = frozen_family_probe_reading()
    assert fr.eval_config(s) == fr.eval_config(main)


@pytest.mark.parametrize("family", FAMILIES)
def test_the_cli_writes_the_file_in_the_main_configs_layout_and_the_loader_accepts_it(family, tmp_path):
    main_path = mk.CONFIGS / mk.MAIN[family]["file"]
    name = mk.s78_name(json.loads(main_path.read_text())["name"], mk.DEFAULT_DATE)
    out = tmp_path / f"{name}.json"
    cmd = [sys.executable, "-I", "-B", str(ROOT / "scripts/scale78b/make_recipe_s78.py"), "--family", family,
           "--anchors-sha256", TEST_ANCHORS, "--out", str(out)]
    run = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp_path))
    assert run.returncode == 0, run.stderr
    printed = json.loads(run.stdout)
    written = load_recipe(out)                                   # the engine's loader accepts the file
    assert printed["recipe_sha256"] == config_sha256(written)
    assert printed["training_identity"] == training_identity(written) == mk.MAIN[family]["training_identity"]
    assert printed["main_sha256"] == mk.MAIN[family]["config_sha256"]
    assert set(printed) == {"family", "name", "recipe_sha256", "training_identity", "main_sha256", "main_training_identity"}
    text, main_text = out.read_text(encoding="utf-8"), main_path.read_text(encoding="utf-8")
    assert text.endswith("\n") and mk.indent_of(text) == mk.indent_of(main_text)
    assert list(written) == list(json.loads(main_text))
    assert mk.diff_paths(json.loads(main_text), written) == set(mk.RECIPE_S_FIELDS)
    # the same inputs give the same bytes
    out2 = tmp_path / "again" / f"{name}.json"
    out2.parent.mkdir()
    run2 = subprocess.run(cmd[:-1] + [str(out2)], capture_output=True, text=True, cwd=str(tmp_path))
    assert run2.returncode == 0 and out2.read_bytes() == out.read_bytes()
    assert mk.indent_of(main_text) == {"olmo2-7b": 2, "llama31-8b": 4}[family]   # the two main configs differ in layout


def test_refusals(tmp_path):
    main = load_main("olmo2-7b")
    with pytest.raises(SystemExit, match="64 lowercase hex"):
        mk.make(main, "olmo2-7b", "abc")
    with pytest.raises(SystemExit, match="64 lowercase hex"):
        mk.make(main, "olmo2-7b", TEST_ANCHORS.upper())
    with pytest.raises(SystemExit, match="--family"):
        mk.make(main, "olmo2-1b", TEST_ANCHORS)
    with pytest.raises(SystemExit, match="eight digits"):
        mk.make(main, "olmo2-7b", TEST_ANCHORS, date="5 Nov")
    script = str(ROOT / "scripts/scale78b/make_recipe_s78.py")
    name = mk.s78_name(main["name"], mk.DEFAULT_DATE)
    existing = tmp_path / f"{name}.json"
    existing.write_text("{}")
    run = subprocess.run([sys.executable, "-I", "-B", script, "--family", "olmo2-7b", "--anchors-sha256", TEST_ANCHORS,
                          "--out", str(existing)], capture_output=True, text=True)
    assert run.returncode != 0 and "written once" in run.stderr and existing.read_text() == "{}"
    wrong_stem = tmp_path / "some-other-name.json"
    run = subprocess.run([sys.executable, "-I", "-B", script, "--family", "olmo2-7b", "--anchors-sha256", TEST_ANCHORS,
                          "--out", str(wrong_stem)], capture_output=True, text=True)
    assert run.returncode != 0 and "stem must be the recipe's name" in run.stderr and not wrong_stem.exists()


def test_a_changed_main_config_refuses(monkeypatch):
    def fake_sha(recipe):
        return "0" * 64
    with pytest.raises(SystemExit, match="the main config changed"):
        mk.load_main("llama31-8b", fake_sha, validate_recipe)


GATE_B_1B_ANCHORS = "2cf9633613e235d1f33deee3530c3e53b037845bd3979568887742457c1801ed"   # anchors.sealed.json, the 1B record


def test_any_s78_config_in_the_configs_folder_is_anchored_to_a_committed_record_of_its_family():
    """Route (A), addendum A1 (C-D3): an S_78 config may be present in configs/ only after its family's anchor job. Each
    one present (the main config's name with -gateb-<date>) must differ from its main config in exactly the recipe-S
    field set, keep the training identity, and name in attribution.query_bank an anchors-<hash> equal to a committed
    anchors.sealed.json record's anchor_file_sha256 whose provenance recipe is THIS family's main config: no placeholder,
    no borrowed 1B anchor file. Vacuous today (no S_78 config exists); it holds the day the lead commits them."""
    records = mk.anchor_records(ROOT / ".ai/inputs")
    assert {"anchor_file_sha256": GATE_B_1B_ANCHORS, "recipe_sha256": mk.REC_1B_SHA256} in \
        [{k: r[k] for k in ("anchor_file_sha256", "recipe_sha256")} for r in records]       # Gate B's 1B record is read
    for family in FAMILIES:
        main = load_main(family)
        stem = re.sub(r"-\d{8}$", "", main["name"])
        for path in sorted(mk.CONFIGS.glob(f"{stem}-gateb-*.json")):
            s = validate_recipe(json.loads(path.read_text(encoding="utf-8")))
            assert s["name"] == path.stem and mk.s78_name(main["name"], path.stem[-8:]) == s["name"], path.name
            assert mk.diff_paths(main, s) == set(mk.RECIPE_S_FIELDS), path.name
            assert training_identity(s) == mk.MAIN[family]["training_identity"], path.name
            assert s["attribution"]["checkpoints"] == mk.RECIPE_S_CHECKPOINTS, path.name
            record = mk.anchored_to(s, family, records)
            assert record is not None, (f"{path.name}: attribution.query_bank {s['attribution']['query_bank'][:24]}… is not "
                                        f"a committed anchor record of {family} (its anchor job's anchors.sealed.json)")


def test_the_anchor_link_refuses_a_placeholder_and_a_borrowed_1b_anchor_file():
    """The predicate behind the test above: a synthetic hash is unanchored; Gate B's 1B anchor file is OLMo-2-1B's record
    (recipe 9e9bde6f…), so it anchors neither 7-8B family; a record whose recipe is the family's main config anchors
    that family only."""
    records = mk.anchor_records(ROOT / ".ai/inputs")
    main = load_main("olmo2-7b")
    placeholder = mk.make(main, "olmo2-7b", TEST_ANCHORS)
    assert mk.anchored_to(placeholder, "olmo2-7b", records) is None
    borrowed = mk.make(main, "olmo2-7b", GATE_B_1B_ANCHORS)
    assert mk.anchored_to(borrowed, "olmo2-7b", records) is None
    assert mk.anchored_to(mk.make(load_main("llama31-8b"), "llama31-8b", GATE_B_1B_ANCHORS), "llama31-8b", records) is None
    fake = [{"path": "x/anchors.sealed.json", "anchor_file_sha256": TEST_ANCHORS,
             "recipe_sha256": mk.MAIN["olmo2-7b"]["config_sha256"]}]
    assert mk.anchored_to(placeholder, "olmo2-7b", fake) == fake[0]
    assert mk.anchored_to(placeholder, "llama31-8b", fake) is None
    assert mk.anchored_to(main, "olmo2-7b", fake) is None                      # the main config's query_bank is "ref"
    assert mk.anchored_to(placeholder, "olmo2-1b", fake) is None               # not a 7-8B family


def test_anchor_records_skips_an_incomplete_or_foreign_record(tmp_path):
    """RV-2 (C-D3b): an anchor record is an anchors.sealed.json of kind "gate-c anchor bank record" with complete true;
    an incomplete record (complete false, missing, or not the boolean true), another kind or a non-object document is
    skipped, so no S_78 config can be anchored to it."""
    good = {"kind": mk.ANCHOR_RECORD_KIND, "complete": True, "anchor_file_sha256": TEST_ANCHORS,
            "provenance": {"recipe_sha256": mk.MAIN["olmo2-7b"]["config_sha256"]}}
    cases = {"complete": good, "incomplete": {**good, "complete": False},
             "unfinished": {k: v for k, v in good.items() if k != "complete"},
             "complete-as-a-string": {**good, "complete": "true"}, "foreign-kind": {**good, "kind": "gate-c anchor bank"},
             "a-list": [good]}
    for name, doc in cases.items():
        folder = tmp_path / name / "out"
        folder.mkdir(parents=True)
        (folder / "anchors.sealed.json").write_text(json.dumps(doc), encoding="utf-8")
    records = mk.anchor_records(tmp_path)
    assert [Path(r["path"]).parent.parent.name for r in records] == ["complete"]
    assert records[0]["anchor_file_sha256"] == TEST_ANCHORS and records[0]["recipe_sha256"] == mk.MAIN["olmo2-7b"]["config_sha256"]
    s78 = mk.make(load_main("olmo2-7b"), "olmo2-7b", TEST_ANCHORS)
    assert mk.anchored_to(s78, "olmo2-7b", records) == records[0]
    for name in cases:
        if name != "complete":
            assert mk.anchor_records(tmp_path / name) == [], name
            assert mk.anchored_to(s78, "olmo2-7b", mk.anchor_records(tmp_path / name)) is None, name
