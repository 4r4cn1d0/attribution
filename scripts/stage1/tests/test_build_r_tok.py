"""W1-03: R_tok, the token-matched random removal (synthetic P; the arm's removal is a synthetic remove edit)."""

from __future__ import annotations

import copy
import json

import pytest

from experiments.safety_selection.common import sha256_file
from experiments.safety_selection.edits import parse_edit
from scripts.stage1 import build_r_tok as brt
from scripts.stage1 import s1common as s1
from scripts.stage1 import token_accounting as ta

import s1fixtures_b3 as fb


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("rtok")
    prep = fb.make_prepared(root / "p")
    v = s1.PreparedView(prep["root"], prep["manifest_sha256"])
    removed = sorted(v.tokens, key=lambda r: v.tokens[r])[:600]            # an H1-like removal: the 600 shortest
    doc = s1.edit_document(name="synthetic arm removal", edit_kind="remove", manifest_sha256=v.manifest_sha256,
                           remove=removed, provenance={"test": True})
    data, _ = s1.checked_edit(doc, v.engine_stub())
    path = root / "arm.edit.json"
    path.write_bytes(data)
    settings = copy.deepcopy(json.loads(brt.SETTINGS_PATH.read_bytes()))
    settings["prepared_manifest_sha256"] = prep["manifest_sha256"]
    return {"prep": prep, "view": v, "removal": (path, sha256_file(path)), "removed": removed, "settings": settings,
            "tokens": ta.TokenView(prep["root"], prep["manifest_sha256"])}


def build(env, arm="h1", removal=None, settings=None):
    return brt.build(env["prep"]["root"], arm, removal or env["removal"], settings or env["settings"], "e" * 64)


def test_each_unit_lands_within_half_its_crossing_row_of_the_target(env):
    files = build(env)
    tokens = env["tokens"].total_tokens
    target = sum(tokens[r] for r in env["removed"]) / 8
    v = env["view"]
    for d in (2, 3, 4):
        remove = set(json.loads(files[f"edits/R_tok_h1_d{d}.json"])["remove"])
        for g in v.units:
            order = s1.sealed_order(v.members[g], "random_removal.rtok", "h1", d, g)
            picked = [r for r in order if r in remove]
            assert picked == order[:len(picked)]                            # a prefix of the sealed order
            mass = sum(tokens[r] for r in picked)
            crossing = order[len(picked) - 1] if mass >= target else order[len(picked)]
            assert abs(mass - target) <= tokens[crossing] / 2 + 1e-9
            assert mass == sum(tokens[r] for r in v.members[g] if r in remove)


def test_the_sealed_order_takes_the_arm_as_a_part(env):
    """Arm l1 (a null pin) walks the (l1, d, g) order, not h1's, and the two arms' files differ for one removal."""
    v = env["view"]
    tokens = env["tokens"].total_tokens
    target = sum(tokens[r] for r in env["removed"]) / 8
    l1 = build(env, arm="l1")
    h1 = build(env)
    for d in (2, 3, 4):
        remove = set(json.loads(l1[f"edits/R_tok_l1_d{d}.json"])["remove"])
        for g in v.units:
            order = s1.sealed_order(v.members[g], "random_removal.rtok", "l1", d, g)
            picked = [r for r in order if r in remove]
            assert picked == order[:len(picked)] and 0 < len(picked) < len(order)
            mass = sum(tokens[r] for r in picked)
            crossing = order[len(picked) - 1] if mass >= target else order[len(picked)]
            assert abs(mass - target) <= tokens[crossing] / 2 + 1e-9
        assert json.loads(l1[f"edits/R_tok_l1_d{d}.json"])["remove"] != json.loads(h1[f"edits/R_tok_h1_d{d}.json"])["remove"]
        assert json.loads(l1[f"edits/R_tok_l1_d{d}.json"])["provenance"]["arm"] == "l1"
    rec = json.loads(l1[brt.RECORD])
    assert rec["arm"] == "l1" and rec["provenance"]["inputs"]["removal_l1"] == env["removal"][1]


def test_the_tables_state_each_units_seed_on_the_arm_draw_and_unit(env):
    v = env["view"]
    for arm in ("h1", "l1"):
        files = build(env, arm=arm)
        rec = json.loads(files[brt.RECORD])
        for d, entry in zip((2, 3, 4), rec["files"]):
            assert entry["draw"] == d and entry["seed"] == 1100 + d
            table = entry["table"]["units"]
            assert [t["group_id"] for t in table] == list(v.units)
            assert [t["seed"] for t in table] == [s1.seed("random_removal.rtok", arm, d, g) for g in v.units]
            doc = json.loads(files[f"edits/R_tok_{arm}_d{d}.json"])
            assert doc["provenance"]["table"] == entry["table"] and doc["provenance"]["draw"] == d


def test_a_combined_arm_file_refuses(env, tmp_path):
    v = env["view"]
    other = sorted(set(v.tokens) - set(env["removed"]))[0]
    doc = s1.edit_document(name="synthetic combined", edit_kind="combined", manifest_sha256=v.manifest_sha256,
                           remove=env["removed"], rewrite={other: "A rewritten synthetic answer."},
                           provenance={"test": True})
    data, _ = s1.checked_edit(doc, v.engine_stub())
    path = tmp_path / "combined.edit.json"
    path.write_bytes(data)
    with pytest.raises(s1.Refusal, match="not a remove-only edit"):
        build(env, removal=(path, sha256_file(path)))


def test_a_599_row_arm_file_refuses(env, tmp_path):
    v = env["view"]
    doc = s1.edit_document(name="synthetic 599", edit_kind="remove", manifest_sha256=v.manifest_sha256,
                           remove=env["removed"][:599], provenance={"test": True})
    data, _ = s1.checked_edit(doc, v.engine_stub())
    path = tmp_path / "r599.edit.json"
    path.write_bytes(data)
    with pytest.raises(s1.Refusal, match="holds 599 rows, the settings say 600"):
        build(env, removal=(path, sha256_file(path)))


def test_the_crossing_row_rule_by_hand():
    class View:
        units = ["g"]
        members = {"g": ["a", "b", "c", "d"]}
        category = {"g": "x"}
        total_tokens = {"a": 10, "b": 10, "c": 10, "d": 10}
        target_tokens = {"a": 1, "b": 1, "c": 1, "d": 1}
    order = s1.sealed_order(View.members["g"], "random_removal.rtok", "a1", 2, "g")
    rows, table = brt.token_matched(View, ["a", "b", "c"], "a1", 2, "total_tokens", "random_removal.rtok")
    assert rows == sorted(order[:3]) and table["unit_target"] == 30          # 30 reached exactly: the row is kept
    rows, _ = brt.token_matched(View, ["a", "b"], "a1", 2, "total_tokens", "random_removal.rtok")
    assert len(rows) == 2                                                   # 20 exactly
    rows, _ = brt.token_matched(View, ["a", "b", "c", "d"], "a1", 2, "target_tokens", "random_removal.rtok")
    assert len(rows) == 4                                                   # the target-token axis: 4 of 4


def test_ties_keep_and_closer_without_keeps_nothing_more():
    class View:
        units = ["g"]
        members = {"g": ["a", "b"]}
        category = {"g": "x"}
        total_tokens = {"a": 4, "b": 4}
        target_tokens = total_tokens
    order = s1.sealed_order(View.members["g"], "random_removal.rtok", "l1", 3, "g")
    # T_m = 4 + 2 = 6 (the arm's rows a and x): the first row (4) is below 6; the second gives 8: |8 - 6| = |4 - 6|,
    # a tie, so it is kept
    View.total_tokens = {"a": 4, "b": 4, "x": 2}
    rows, table = brt.token_matched(View, ["a", "x"], "l1", 3, "total_tokens", "random_removal.rtok")
    assert table["unit_target"] == 6 and rows == sorted(order)
    View.total_tokens = {"a": 4, "b": 4, "x": 1}                         # target 5: 8 is farther than 4 -> not kept
    rows, _ = brt.token_matched(View, ["a", "x"], "l1", 3, "total_tokens", "random_removal.rtok")
    assert rows == [order[0]]


def test_a_unit_below_the_target_refuses():
    class View:
        units = ["g", "h"]
        members = {"g": ["a"], "h": ["b"]}
        category = {"g": "x", "h": "y"}
        total_tokens = {"a": 1, "b": 100}
        target_tokens = total_tokens
    with pytest.raises(s1.Refusal, match="less than T_m"):
        brt.token_matched(View, ["b"], "a1", 2, "total_tokens", "random_removal.rtok")


def test_the_files_differ_by_d_and_parse(env):
    files = build(env)
    stub = env["view"].engine_stub()
    lists = []
    for d in (2, 3, 4):
        data = files[f"edits/R_tok_h1_d{d}.json"]
        assert parse_edit(data, stub).document["edit_kind"] == "remove"
        lists.append(tuple(json.loads(data)["remove"]))
    assert len(set(lists)) == 3
    rec = json.loads(files[brt.RECORD])
    assert [f["seed"] for f in rec["files"]] == [1102, 1103, 1104] and rec["arm"] == "h1"


def test_the_axis_switch(env):
    total = build(env)
    settings = copy.deepcopy(env["settings"])
    settings["axis"] = "target_tokens"
    target = build(env, settings=settings)
    assert total["edits/R_tok_h1_d2.json"] != target["edits/R_tok_h1_d2.json"]
    assert json.loads(total[brt.RECORD])["files"][0]["table"]["axis"] == "total_tokens"


def test_refusals(env, tmp_path):
    with pytest.raises(s1.Refusal, match="hashes to"):
        build(env, removal=(env["removal"][0], "0" * 64))
    with pytest.raises(s1.Refusal, match="no arm"):
        build(env, arm="x1")
    with pytest.raises(s1.Refusal, match="the settings pin the removal file"):
        build(env, arm="a1")                                               # A1's committed file is pinned
    with pytest.raises(s1.Refusal, match="cannot be read"):
        build(env, removal=(tmp_path / "absent.json", "0" * 64))


def test_the_settings_pin_a1s_committed_removal():
    settings = json.loads(brt.SETTINGS_PATH.read_bytes())
    assert settings["arms"]["a1"]["removal_sha256"] == "5c0e53b78e9ee71d0e16e13f4fa045509401c0afa98f53c3d7af6bd79ccaf4ca"
    assert settings["draws"] == [2, 3, 4] and settings["seed_offset"] == 1100 and settings["axis"] == "total_tokens"
    assert set(settings["arms"]) == {"a1", "l1", "h1"} and all(a["rows"] == 600 for a in settings["arms"].values())


def test_text_free(env):
    for data in build(env).values():
        for text in env["prep"]["texts"][::211]:
            assert text.encode() not in data


def test_the_settings_file_is_literal_pinned():
    doc, digest = s1.load_settings(brt.SETTINGS_PATH, brt.SETTINGS_SHA256, brt.SETTINGS_NAME)
    assert digest == "76155178e39d910aab97517fe22e3693c57ec8129f8ba38818ccab850ab4bb77"
    assert set(doc["label_entries"]) == {"random_removal.rtok"}
