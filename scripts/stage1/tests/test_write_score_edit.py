"""REQ-14: the score-to-edit writer and the A1 removal contract (synthetic attributes units only)."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import re
from pathlib import Path
from statistics import fmean

import pytest

import experiments.safety_selection.attribution as attribution
from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from experiments.safety_selection.edits import parse_edit
from scripts.stage1 import s1common as s1
from scripts.stage1 import write_score_edit as wse

import s1fixtures as fx

# The golden synthetic A1 output: SHA-256 of canonical_json({"scores": ..., "selected": ...}) for the fixture
# made by fx.build_fixture(values_seed=11) (8 units x 600 rows; make_prepared seed 7).
GOLDEN_A1_SHA256 = "f9608990dd28ff1ceec1f47e6c00bfb79529f306331d958ce741173da5b47c03"


def files_of(fix: dict) -> dict[str, bytes]:
    return wse.build_a1(fix["prepared"]["root"], fix["unit"], fix["settings"], "f" * 64)


def record_of(files: dict[str, bytes]) -> dict:
    return json.loads(files["a1_selection.json"])


def reference_a1(values: dict, members: dict, k: int = 600) -> tuple[dict, list]:
    """An independent recomputation: plain arithmetic and the stated tie rule, without the writer's code."""
    scores = {r: ((v["q"]["harmful"]["cosine"] - v["q"]["safe"]["cosine"])
                  + (v["e1"]["harmful"]["cosine"] - v["e1"]["safe"]["cosine"])) / 2 for r, v in values.items()}
    order = sorted(scores)
    text = "|".join(["20261008", "stage1-a1-ties-v1"])
    random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")).shuffle(order)
    rank = {r: i for i, r in enumerate(order)}
    return scores, sorted(scores, key=lambda r: (-scores[r], rank[r]))[:k]


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    """The fixture files only: the code under test never runs inside a fixture (an error there would make a
    mutation run invalid, not killed)."""
    return fx.build_fixture(tmp_path_factory.mktemp("a1"))


def base_files(base: dict) -> dict[str, bytes]:
    """The writer's outputs on the base fixture, computed inside the calling test and then cached."""
    if "files" not in base:
        base["files"] = files_of(base)
    return base["files"]


# ----- the contract ---------------------------------------------------------------------------------


def test_golden_synthetic_a1_output(base):
    rec = record_of(base_files(base))
    digest = sha256_bytes(canonical_json({"scores": rec["scores"], "selected": rec["selected"]}))
    assert digest == GOLDEN_A1_SHA256


def test_a1_equals_an_independent_recomputation(base):
    rec = record_of(base_files(base))
    scores, selected = reference_a1(base["values"], base["prepared"]["members"])
    assert rec["scores"] == scores
    assert rec["selection_order"] == selected and rec["selected"] == sorted(selected)


def test_exactly_600_rows_removed_through_the_engine_parse_edit(base):
    data = base_files(base)["a1_remove600.edit.json"]
    view = s1.PreparedView(base["prepared"]["root"], base["prepared"]["manifest_sha256"])
    edit = parse_edit(data, view.engine_stub())
    rec = record_of(base_files(base))
    assert len(edit.removed) == 600 and edit.document["edit_kind"] == "remove"
    assert sorted(edit.removed) == rec["selected"] and rec["edit"]["sha256"] == sha256_bytes(data)
    assert edit.arm == rec["edit"]["arm"] and not edit.rewrite and not edit.added


def test_the_consistency_check_holds_per_unit(base):
    rec = record_of(base_files(base))
    assert sorted(rec["consistency"]["units"]) == sorted(base["prepared"]["members"])
    assert all(u["abs_difference"] <= 1e-12 for u in rec["consistency"]["units"].values())
    assert rec["unit_scores"] == {u: v["rows_mean"] for u, v in rec["consistency"]["units"].items()}


def planted_values(members: dict, planted: set, *, field_noise: dict | None = None, seed: int = 5) -> dict:
    """Random values where the planted rows get a large harmful-minus-safe cosine at both checkpoints."""
    values = fx.random_values(members, seed)
    for rid in planted:
        for c in ("q", "e1"):
            values[rid][c]["harmful"]["cosine"] = 0.9
            values[rid][c]["safe"]["cosine"] = -0.9
    return values


def test_orientation_removes_the_largest_a_i(tmp_path):
    prepared = fx.make_prepared(tmp_path / "p0")
    rows = sorted(prepared["tokens"])
    planted = set(random.Random(3).sample(rows, 600))
    fix = fx.build_fixture(tmp_path / "f", values=planted_values(prepared["members"], planted))
    assert set(record_of(files_of(fix))["selected"]) == planted


def test_selection_is_global_not_per_unit(tmp_path):
    prepared = fx.make_prepared(tmp_path / "p0")
    units = sorted(prepared["members"])
    planted = set(prepared["members"][units[0]][:300] + prepared["members"][units[1]][:300])
    fix = fx.build_fixture(tmp_path / "f", values=planted_values(prepared["members"], planted))
    rec = record_of(files_of(fix))
    assert set(rec["selected"]) == planted
    assert rec["stats"]["removed"]["by_unit"][units[0]] == 300 and rec["stats"]["removed"]["by_unit"][units[2]] == 0


def test_the_adam_variant_and_other_fields_are_ignored(tmp_path, base):
    values = copy.deepcopy(base["values"])
    rng = random.Random(99)
    for v in values.values():
        for c in ("q", "e1"):
            for s in ("harmful", "safe"):
                for field in ("adam_score", "dot", "grad_norm", "loss", "preconditioned_grad_norm"):
                    v[c][s][field] = rng.uniform(-50, 50) if field in ("adam_score", "dot") else rng.uniform(0.1, 50)
    fix = fx.build_fixture(tmp_path / "f", values=values)
    rec, ref = record_of(files_of(fix)), record_of(base_files(base))
    assert rec["scores"] == ref["scores"] and rec["selected"] == ref["selected"]


def test_both_checkpoints_and_both_sets_count(tmp_path):
    prepared = fx.make_prepared(tmp_path / "p0")
    rows = sorted(prepared["tokens"])
    values = fx.random_values(prepared["members"], 21)
    for v in values.values():                            # every other row: a_i = 0
        for c in ("q", "e1"):
            v[c]["harmful"]["cosine"] = v[c]["safe"]["cosine"] = 0.0
    q_only, e1_only, safe_only = rows[:600], rows[600:1200], rows[1200:1800]
    for rid in q_only:                                   # q difference 1.2, e1 difference -0.7: a_i = 0.25
        values[rid]["q"]["harmful"]["cosine"], values[rid]["q"]["safe"]["cosine"] = 0.6, -0.6
        values[rid]["e1"]["harmful"]["cosine"], values[rid]["e1"]["safe"]["cosine"] = -0.35, 0.35
    for rid in e1_only:                                  # high at e1 only
        values[rid]["e1"]["harmful"]["cosine"], values[rid]["e1"]["safe"]["cosine"] = 0.6, -0.6
        values[rid]["q"]["harmful"]["cosine"], values[rid]["q"]["safe"]["cosine"] = -0.35, 0.35
    for rid in safe_only:                                # a very low safe cosine but a low harmful cosine too
        for c in ("q", "e1"):
            values[rid][c]["harmful"]["cosine"], values[rid][c]["safe"]["cosine"] = -0.5, -0.8
    fix = fx.build_fixture(tmp_path / "f", values=values)
    rec = record_of(files_of(fix))
    scores, selected = reference_a1(values, prepared["members"])
    assert rec["selected"] == sorted(selected)
    assert set(rec["selected"]) == set(safe_only)        # a_i 0.3 beats q-only and e1-only (0.25); harmful alone
    #                                                      would rank them first (0.125 against -0.5)


def test_ties_follow_the_sealed_rank(tmp_path):
    prepared = fx.make_prepared(tmp_path / "p0")
    values = fx.random_values(prepared["members"], 1)
    for v in values.values():
        for c in ("q", "e1"):
            v[c]["harmful"]["cosine"], v[c]["safe"]["cosine"] = 0.25, 0.125
    fix = fx.build_fixture(tmp_path / "f", values=values)
    rec = record_of(files_of(fix))
    assert rec["selection_order"] == s1.sealed_order(prepared["tokens"], "a1.ties")[:600]
    assert rec["boundary"]["tied_selected"] == 600 and rec["boundary"]["tied_not_selected"] == 4200


# ----- refusals -------------------------------------------------------------------------------------


@pytest.mark.parametrize("index,delta,refused", [(3, 1e-13, False), (3, -1e-13, False), (3, 3e-12, True),
                                                 (3, 1e-9, True), (3, -3e-12, True), (3, -1e-9, True),
                                                 (0, -3e-12, True), (6, 3e-12, True)])
def test_a_perturbed_groups_json_refuses(tmp_path, base, index, delta, refused):
    unit = sorted(base["prepared"]["members"])[index]
    fix = fx.build_fixture(tmp_path / "f", values=base["values"], perturb={unit: delta})
    if refused:
        with pytest.raises(s1.Refusal, match="differs from groups.json"):
            files_of(fix)
    else:
        assert record_of(files_of(fix))["selected"] == record_of(base_files(base))["selected"]


@pytest.mark.parametrize("kwargs", [
    {"job_changes": {"seed": 1102}}, {"marker_changes": {"seed": 1102}}, {"job_changes": {"query_bank": "anchors-" + "0" * 64}},
    {"marker_changes": {"query_bank_sha256": "0" * 64}}, {"marker_changes": {"checkpoints": ["e1", "q"]}},
    {"marker_changes": {"anchor_counts": {"harmful": 64, "safe": 63}}}, {"identity_changes": {"code_sha256": "0" * 64}},
    {"identity_changes": {"recipe_sha256": "0" * 64}}, {"identity_changes": {"manifest_sha256": "0" * 64}},
    {"marker_changes": {"sources": {"q": {"complete_sha256": "0" * 64}, "e1": {"complete_sha256": "0" * 64}}}},
    {"marker_changes": {"kind": "run-one"}}, {"job_changes": {"group_ids": []}}, {"job_changes": {"split": "heldout"}},
    {"marker_changes": {"split": "heldout"}}, {"marker_changes": {"query_bank": "anchors-" + "0" * 64}},
    {"marker_changes": {"group_ids": []}}, {"job_changes": {"kind": "run-one"}},
    {"marker_changes": {"sources": {"q": {"complete_sha256": "d154f23f5d5734c04aedfc9636c93609f980509aa28abdff54462eb9b41fd2a5"},
                                    "e1": {"complete_sha256": "0" * 64}}}},
    {"marker_changes": {"sources": {"q": {"complete_sha256": "0" * 64},
                                    "e1": {"complete_sha256": "d154f23f5d5734c04aedfc9636c93609f980509aa28abdff54462eb9b41fd2a5"}}}},
])
def test_the_attributes_unit_checks_refuse(tmp_path, base, kwargs):
    fix = fx.build_fixture(tmp_path / "f", values=base["values"], **kwargs)
    with pytest.raises(s1.Refusal, match="fails the checks"):
        files_of(fix)


def test_a_changed_unit_file_or_another_complete_refuses(tmp_path, base):
    fix = fx.build_fixture(tmp_path / "f", values=base["values"])
    other = copy.deepcopy(fix["settings"])
    other["a1"]["attributes_unit"]["complete_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="COMPLETE.json hashes"):
        wse.build_a1(fix["prepared"]["root"], fix["unit"], other, "f" * 64)
    rows = fix["unit"] / "rows.jsonl"
    rows.write_bytes(rows.read_bytes().replace(b'"cosine": 0.', b'"cosine": -0.', 1))
    with pytest.raises(s1.Refusal, match="do not verify"):
        files_of(fix)


def test_an_unlisted_file_in_the_unit_refuses(tmp_path, base):
    fix = fx.build_fixture(tmp_path / "f", values=base["values"])
    (fix["unit"] / ".DS_Store").write_bytes(b"\x00")           # the engine's verify_files refuses any added file
    with pytest.raises(s1.Refusal, match="do not verify"):
        files_of(fix)


def test_a_missing_row_refuses(tmp_path, base):
    fix = fx.build_fixture(tmp_path / "f", values=base["values"], drop_rows=1)
    with pytest.raises(s1.Refusal, match="misses 1 training rows"):
        files_of(fix)


def _rewrite_rows_and_complete(fix: dict, change) -> dict:
    """Change rows.jsonl, then re-complete the unit (so its own files verify) and re-pin the settings."""
    rows = fix["unit"] / "rows.jsonl"
    lines = rows.read_bytes().splitlines(keepends=True)
    lines[0] = change(lines[0])
    rows.write_bytes(b"".join(lines))
    marker = json.loads((fix["unit"] / "COMPLETE.json").read_bytes())
    (fix["unit"] / "COMPLETE.json").unlink()
    summary = {k: v for k, v in marker.items() if k not in ("complete", "completed_utc", "files")}
    from experiments.safety_selection.ledger import write_complete
    write_complete(fix["unit"], summary)
    fix["settings"]["a1"]["attributes_unit"]["complete_sha256"] = sha256_file(fix["unit"] / "COMPLETE.json")
    return fix


def _add_e2(rows):
    rows[0]["per_checkpoint"]["e2"] = rows[0]["per_checkpoint"]["e1"]


def _add_top_key(rows):
    rows[0]["extra"] = 1


@pytest.mark.parametrize("rows_edit,match", [(_add_e2, "the checkpoints are not"),
                                             (_add_top_key, "not exactly row_id, group_id, per_checkpoint")])
def test_an_extra_checkpoint_or_row_key_refuses(tmp_path, base, rows_edit, match):
    fix = fx.build_fixture(tmp_path / "f", values=base["values"], rows_edit=rows_edit)
    with pytest.raises(s1.Refusal, match=match):
        files_of(fix)


def _other_sign(doc):
    doc["bi_anchored_sign"] = doc["bi_anchored_sign"] + " (another convention)"


def _no_variant(doc):
    doc["variants"] = [attribution.ADAM]


def _one_unit_missing(doc):
    doc["groups"].pop(sorted(doc["groups"])[2])


@pytest.mark.parametrize("groups_edit,match", [(_other_sign, "another bi-anchored sign"),
                                               (_no_variant, "does not list the variant"),
                                               (_one_unit_missing, "does not hold exactly the prepared set's units")])
def test_a_changed_groups_json_refuses(tmp_path, base, groups_edit, match):
    fix = fx.build_fixture(tmp_path / "f", values=base["values"], groups_edit=groups_edit)
    with pytest.raises(s1.Refusal, match=match):
        files_of(fix)


def _zero_values(members: dict) -> dict:
    values = fx.random_values(members, 2)
    for v in values.values():
        for c in ("q", "e1"):
            v[c]["harmful"]["cosine"] = v[c]["safe"]["cosine"] = 0.125
    return values


def test_the_consistency_tolerance_is_inclusive(tmp_path):
    prepared = fx.make_prepared(tmp_path / "p0")
    values = _zero_values(prepared["members"])

    def set_all(value, last=None):
        def edit(doc):
            for k, unit in enumerate(sorted(doc["groups"])):
                doc["groups"][unit]["bi_anchored"][attribution.GRADSIM] = last if (last is not None and k == 7) else value
        return edit
    fix = fx.build_fixture(tmp_path / "a", values=values, groups_edit=set_all(1e-12))
    rec = record_of(files_of(fix))
    assert all(u["abs_difference"] == 1e-12 for u in rec["consistency"]["units"].values())
    assert set(rec["scores"].values()) == {0.0}
    fix = fx.build_fixture(tmp_path / "b", values=values, groups_edit=set_all(1e-12, math.nextafter(1e-12, 1.0)))
    with pytest.raises(s1.Refusal, match="differs from groups.json"):
        files_of(fix)


def test_ties_at_the_boundary_follow_an_independent_reference(tmp_path, base):
    values = copy.deepcopy(base["values"])
    rows = sorted(values)
    for rid in rows[:550]:                                  # 550 clear picks, then 300 rows tied at the boundary
        for c in ("q", "e1"):
            values[rid][c]["harmful"]["cosine"], values[rid][c]["safe"]["cosine"] = 0.75, -0.75
    for rid in rows[550:850]:
        for c in ("q", "e1"):
            values[rid][c]["harmful"]["cosine"], values[rid][c]["safe"]["cosine"] = 0.5, -0.25
    fix = fx.build_fixture(tmp_path / "f", values=values)
    rec = record_of(files_of(fix))
    scores, selected = reference_a1(values, fix["prepared"]["members"])
    assert rec["selection_order"] == selected
    assert rec["boundary"] == {"kth_score": 0.75, "tied_selected": 50, "tied_not_selected": 250}


@pytest.mark.parametrize("change,match", [
    (lambda line: line.replace(b'"loss":', b'"other": 1, "loss":', 1), "other fields"),
    (lambda line: re.sub(rb'"cosine": -?[0-9.e-]+', b'"cosine": NaN', line, count=1), "not one strict JSON value"),
    (lambda line: line.replace(b'"harmful"', b'"harmfull"', 1), "does not hold the sets"),
    (lambda line: line.replace(b'"group_id": "g-', b'"group_id": "h-', 1), "not the row's unit"),
])
def test_a_malformed_row_refuses(tmp_path, base, change, match):
    fix = _rewrite_rows_and_complete(fx.build_fixture(tmp_path / "f", values=base["values"]), change)
    with pytest.raises(s1.Refusal, match=match):
        files_of(fix)


# ----- outputs --------------------------------------------------------------------------------------


def test_outputs_are_deterministic_and_hold_no_text(tmp_path, base):
    again = files_of(base)
    assert again == base_files(base)
    for data in base_files(base).values():
        for text in base["prepared"]["texts"][::97]:
            assert text.encode() not in data
    out = tmp_path / "out"
    written = s1.write_new_files(out, base_files(base))
    assert written == {name: sha256_bytes(data) for name, data in base_files(base).items()}


def test_the_record_carries_the_spec_section_1_outputs(base):
    rec = record_of(base_files(base))
    stats = rec["stats"]["removed"]
    assert stats["rows"] == 600 and stats["token_mass"] == sum(base["prepared"]["tokens"][r] for r in rec["selected"])
    assert sum(stats["by_unit"].values()) == 600 and "largest_category" in stats
    assert rec["costs"] == {"attribution_seconds": {"q": 100.0, "e1": 100.0}, "gradient_passes": 1}
    assert rec["provenance"]["settings_sha256"] == "f" * 64 and "labels_sha256" not in rec["provenance"]
    assert rec["provenance"]["label_entries"] == base["settings"]["label_entries"]
    assert rec["settings_section"] == base["settings"]["a1"]
    assert set(rec["provenance"]["inputs"]) == {"prepared_manifest", "prepared_train_rows", "prepared_groups",
                                                "attributes_complete", "attributes_job", "attributes_rows",
                                                "attributes_groups"}


# ----- the generic scorer path ----------------------------------------------------------------------


def scorer_output(prepared: dict, name: str, scores: dict, **changes) -> bytes:
    doc = {"kind": "stage1 scorer output", "version": 1, "scorer": name, "manifest_sha256": prepared["manifest_sha256"],
           "orientation": "descending: high = remove", "scores": scores,
           "provenance": {"script_sha256": "a" * 64, "settings_sha256": "b" * 64}, "costs": {"rows_seconds": 1.0}}
    doc.update(changes)
    return canonical_json(doc)


def scorer_settings(prepared: dict) -> dict:
    settings = copy.deepcopy(fx.real_settings())
    settings["prepared"]["manifest_sha256"] = prepared["manifest_sha256"]
    return settings


def test_the_scorer_path_removes_the_top_600(tmp_path):
    prepared = fx.make_prepared(tmp_path / "p")
    rng = random.Random(4)
    scores = {r: rng.gauss(0, 1) for r in prepared["tokens"]}
    path = tmp_path / "l1.json"
    path.write_bytes(scorer_output(prepared, "l1", scores))
    files = wse.build_scorer(prepared["root"], "l1", path, sha256_file(path), scorer_settings(prepared), "e" * 64)
    rec = json.loads(files["l1_selection.json"])
    assert rec["selected"] == sorted(sorted(scores, key=lambda r: -scores[r])[:600])
    assert rec["ties_key"] == "l1.ties" and rec["scorer_output"]["sha256"] == sha256_file(path)
    assert len(json.loads(files["l1_remove600.edit.json"])["remove"]) == 600


@pytest.mark.parametrize("name,changes,match", [
    ("l1", {"scorer": "datashield"}, "scorer output of l1"),
    ("l1", {"orientation": "ascending"}, "another orientation"),
    ("l1", {"manifest_sha256": "0" * 64}, "another prepared set"),
    ("l1", {"provenance": {"script_sha256": "a" * 64}}, "provenance"),
    ("l1", {"extra": 1}, "schema's keys"),
    ("nope", {}, "no scorer"),
])
def test_the_scorer_path_refuses(tmp_path, name, changes, match):
    prepared = fx.make_prepared(tmp_path / "p")
    scores = {r: 1.0 for r in prepared["tokens"]}
    path = tmp_path / "s.json"
    path.write_bytes(scorer_output(prepared, "l1", scores, **changes))
    with pytest.raises(s1.Refusal, match=match):
        wse.build_scorer(prepared["root"], name, path, sha256_file(path), scorer_settings(prepared), "e" * 64)


def test_the_scorer_path_refuses_a_wrong_hash_or_a_missing_row(tmp_path):
    prepared = fx.make_prepared(tmp_path / "p")
    scores = {r: 1.0 for r in sorted(prepared["tokens"])[1:]}
    path = tmp_path / "s.json"
    path.write_bytes(scorer_output(prepared, "l1", scores))
    with pytest.raises(s1.Refusal, match="hashes to"):
        wse.build_scorer(prepared["root"], "l1", path, "0" * 64, scorer_settings(prepared), "e" * 64)
    with pytest.raises(s1.Refusal, match="1 missing"):
        wse.build_scorer(prepared["root"], "l1", path, sha256_file(path), scorer_settings(prepared), "e" * 64)


# ----- the committed settings -----------------------------------------------------------------------


def test_the_settings_file_is_the_pinned_one_and_matches_the_engine():
    data = wse.SETTINGS_PATH.read_bytes()
    assert sha256_bytes(data) == wse.SETTINGS_SHA256
    settings = s1.check_settings(json.loads(data), "write_score_edit")
    a1 = settings["a1"]
    assert a1["category_flag_share"] == 0.5 and all(s["category_flag_share"] == 0.5 for s in settings["scorers"].values())
    assert all(s["k"] == 600 for s in settings["scorers"].values())
    assert a1["bi_anchored_sign"] == attribution.BI_ANCHORED_SIGN and a1["variant"] == attribution.GRADSIM
    assert (a1["k"], a1["ties"], a1["checkpoints"], a1["row_field"]) == (600, "a1.ties", ["q", "e1"], "cosine")
    assert (a1["minuend_set"], a1["subtrahend_set"]) == ("harmful", "safe")
    assert a1["consistency"]["abs_tolerance"] == 1e-12
    source = Path(attribution.__file__).read_text()
    assert all(f'"{field}"' in source for field in a1["row_record_fields"])
    root = Path(attribution.__file__).resolve().parents[2]          # the checkout that holds the engine
    sealed = json.loads((root / "research/experiments/2026-10-16-gate-b-wave0-outputs/rankings-SEALED.json").read_bytes())
    unit = a1["attributes_unit"]
    assert unit["complete_sha256"] == sealed["result"]["attributes_unit"]["complete_sha256"]
    assert unit["retrain_complete_sha256"] == sealed["result"]["retrain"]["complete_sha256"]
    assert unit["query_bank_sha256"] == sealed["result"]["anchor_file_sha256"] == unit["query_bank"][len("anchors-"):]
    assert unit["recipe_sha256"] == sealed["inputs_sha256"]["recipe_s_config_sha256"]
    assert unit["code_sha256"] == sealed["engine_x"] == settings["engine_x"]
    assert settings["prepared"]["manifest_sha256"] == "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"


def test_the_test_settings_differ_from_the_committed_ones_only_in_the_fixture_pins(base):
    real = fx.real_settings()
    used = copy.deepcopy(base["settings"])
    used["prepared"]["manifest_sha256"] = real["prepared"]["manifest_sha256"]
    used["a1"]["attributes_unit"]["complete_sha256"] = real["a1"]["attributes_unit"]["complete_sha256"]
    assert used == real


def test_the_command_refuses_a_settings_file_with_another_hash(tmp_path, capsys):
    changed = tmp_path / "settings.json"
    changed.write_bytes(wse.SETTINGS_PATH.read_bytes().replace(b'"k": 600', b'"k": 601', 1))
    code = wse.main(["a1", "--unit", str(tmp_path), "--prepared", str(tmp_path), "--out", str(tmp_path / "o"),
                     "--settings", str(changed)])
    err = capsys.readouterr().err
    assert code == 2 and "REFUSED" in err and "hash to" in err and not (tmp_path / "o").exists()
