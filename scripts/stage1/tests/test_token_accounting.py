"""W1-01's base: the text-free token view and an edit's token accounting (synthetic prepared sets)."""

from __future__ import annotations

import json

import pytest

from experiments.safety_selection.common import canonical_json, sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1 import token_accounting as ta

import s1fixtures as fx


@pytest.fixture()
def view(tmp_path):
    prep = fx.make_prepared(tmp_path / "p", units=4, rows_per_unit=10)
    return ta.TokenView(tmp_path / "p", prep["manifest_sha256"]), prep


def test_the_view_keeps_prompt_target_and_total_tokens(view, tmp_path):
    v, prep = view
    rows = [json.loads(l) for l in (tmp_path / "p" / "engine" / "train_rows.jsonl").read_text().splitlines()]
    for r in rows:
        assert v.prompt_tokens[r["row_id"]] == r["prompt_tokens"] and v.target_tokens[r["row_id"]] == r["target_tokens"]
        assert v.total_tokens[r["row_id"]] == r["prompt_tokens"] + r["target_tokens"]
    assert v.totals() == {"rows": 40, "target_tokens": sum(r["target_tokens"] for r in rows),
                          "total_tokens": sum(r["prompt_tokens"] + r["target_tokens"] for r in rows)}


def test_the_steps_rule():
    assert (ta.steps(4800, 128), ta.steps(4200, 128), ta.steps(4848, 128)) == (38, 33, 38)
    assert ta.steps(4736, 128) == 37 and ta.steps(4737, 128) == 38
    with pytest.raises(s1.Refusal):
        ta.steps(0, 128)


def test_a_removal_by_hand(view):
    v, prep = view
    u0, u1 = v.units[0], v.units[1]
    removed = v.members[u0][:3] + v.members[u1][:2]
    out = ta.account(v, removed=removed, rows_per_step=8)
    target = sum(v.target_tokens[r] for r in removed)
    total = sum(v.total_tokens[r] for r in removed)
    t = v.totals()
    assert out["removed"]["target_tokens"] == target and out["removed"]["total_tokens"] == total
    assert out["removed"]["share_of_target_tokens"] == target / t["target_tokens"]
    assert out["removed"]["share_of_total_tokens"] == total / t["total_tokens"]
    assert out["removed"]["by_unit"][u0]["rows"] == 3 and out["removed"]["by_unit"][u1]["total_tokens"] == \
        sum(v.total_tokens[r] for r in v.members[u1][:2])
    assert out["edited_corpus"] == {"rows": 35, "target_tokens": t["target_tokens"] - target,
                                    "total_tokens": t["total_tokens"] - total, "steps": 5}
    assert sum(c["rows"] for c in out["removed"]["by_category"].values()) == 5


def test_rewrite_and_add_by_hand(view):
    v, prep = view
    row = v.members[v.units[2]][0]
    out = ta.account(v, rewritten={row: {"prompt_tokens": v.prompt_tokens[row], "target_tokens": 7}},
                     added={"add-x-001": {"prompt_tokens": 11, "target_tokens": 13}}, rows_per_step=128)
    assert out["rewritten"]["before"]["target_tokens"] == v.target_tokens[row]
    assert out["rewritten"]["after"] == {"rows": 1, "target_tokens": 7, "total_tokens": v.prompt_tokens[row] + 7}
    assert out["added"]["rows"] == 1 and out["added"]["target_tokens"] == 13 and out["added"]["total_tokens"] == 24
    t = v.totals()
    assert out["edited_corpus"]["rows"] == 41
    assert out["edited_corpus"]["target_tokens"] == t["target_tokens"] - v.target_tokens[row] + 7 + 13
    assert out["added"]["share_of_total_tokens"] == 24 / t["total_tokens"]           # against P, not the edited corpus
    with pytest.raises(s1.Refusal, match="keeps the prompt"):
        ta.account(v, rewritten={row: {"prompt_tokens": v.prompt_tokens[row] + 1, "target_tokens": 7}})


def test_refusals(view, tmp_path):
    v, prep = view
    with pytest.raises(s1.Refusal):
        ta.account(v, removed=["r-not-a-row"])
    with pytest.raises(s1.Refusal):
        ta.account(v, removed=v.members[v.units[0]][:1] * 2)
    with pytest.raises(s1.Refusal):
        ta.account(v, added={v.members[v.units[0]][0]: {"prompt_tokens": 1, "target_tokens": 1}})
    with pytest.raises(s1.Refusal):
        ta.account(v, removed=v.members[v.units[0]][:1], rewritten={v.members[v.units[0]][0]: {"prompt_tokens": 1, "target_tokens": 1}})
    with pytest.raises(s1.Refusal, match="manifest hashes"):
        ta.TokenView(tmp_path / "p", "0" * 64)


def test_deterministic(view):
    v, prep = view
    removed = v.members[v.units[3]][:4]
    assert canonical_json(ta.account(v, removed=removed)) == canonical_json(ta.account(v, removed=removed))


def test_a_unit_listing_a_row_twice_and_an_empty_rewrite_refuse(view, tmp_path):
    """The critic's note 6: the within-unit duplicate check, and a rewrite's new target tokens are at least 1."""
    v, prep = view
    row = v.members[v.units[1]][0]
    with pytest.raises(s1.Refusal, match="no target tokens"):
        ta.account(v, rewritten={row: {"prompt_tokens": v.prompt_tokens[row], "target_tokens": 0}})
    root = tmp_path / "p"
    doc = json.loads((root / s1.GROUPS).read_bytes())
    doc["partitions"]["dev"]["groups"][0]["members"].append(doc["partitions"]["dev"]["groups"][0]["members"][0])
    (root / s1.GROUPS).write_bytes(canonical_json(doc))
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["files"][s1.GROUPS] = sha256_file(root / s1.GROUPS)
    (root / "manifest.json").write_bytes(canonical_json(manifest))
    with pytest.raises(s1.Refusal, match="lists a row twice"):
        ta.TokenView(root, sha256_file(root / "manifest.json"))


# ----- batch 2 rev 2: the verifier's test (the edited-corpus total and the added share by hand) ----------


def test_v_edited_corpus_total_and_added_target_share_by_hand(view):
    v, prep = view
    row = v.members[v.units[2]][0]
    out = ta.account(v, rewritten={row: {"prompt_tokens": v.prompt_tokens[row], "target_tokens": 7}},
                     added={"add-x-001": {"prompt_tokens": 11, "target_tokens": 13}})
    t = v.totals()
    assert out["edited_corpus"]["total_tokens"] == t["total_tokens"] - v.total_tokens[row] + (v.prompt_tokens[row] + 7) + 24
    assert out["added"]["share_of_target_tokens"] == 13 / t["target_tokens"]


# ----- batch 2 rev 2: the final critic's test (by unit and by category by hand) ---------------------------


def test_fc_by_unit_and_by_category_by_hand(tmp_path):
    """Ten units over eight categories, so two categories hold two units each; every block's by_unit and by_category
    values equal hand sums, for the removed rows and for the rewritten rows' before block."""
    prep = fx.make_prepared(tmp_path / "q", units=10, rows_per_unit=5)
    v = ta.TokenView(tmp_path / "q", prep["manifest_sha256"])
    manifest = json.loads((tmp_path / "q" / "manifest.json").read_bytes())
    cat_of = {g: u["category"] for g, u in manifest["units"].items()}
    assert len(set(cat_of.values())) == 8 and len(cat_of) == 10
    removed = v.members[v.units[0]][:2] + v.members[v.units[8]][:3] + v.members[v.units[1]][:1]
    rewritten = {v.members[v.units[9]][0]: {"prompt_tokens": v.prompt_tokens[v.members[v.units[9]][0]], "target_tokens": 3}}
    out = ta.account(v, removed=removed, rewritten=rewritten)
    for block, rows in ((out["removed"], removed), (out["rewritten"]["before"], list(rewritten))):
        unit_of = {r: g for g in v.units for r in v.members[g]}
        for g in v.units:
            mine = [r for r in rows if unit_of[r] == g]
            assert block["by_unit"][g] == {"rows": len(mine), "target_tokens": sum(v.target_tokens[r] for r in mine),
                                           "total_tokens": sum(v.total_tokens[r] for r in mine)}
        for c in sorted(set(cat_of.values())):
            mine = [r for r in rows if cat_of[unit_of[r]] == c]
            assert block["by_category"][c] == {"rows": len(mine), "target_tokens": sum(v.target_tokens[r] for r in mine),
                                               "total_tokens": sum(v.total_tokens[r] for r in mine)}
