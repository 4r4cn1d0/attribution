"""REQ-2: the shared seed, selection, edit and record helpers (synthetic data only)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes
from scripts.stage1 import s1common as s1

import s1fixtures as fx


def formula(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()[:8], "big")


# ----- seeds and draws ------------------------------------------------------------------------------


def test_seed_is_derive_seed_of_the_registry_label():
    assert s1.seed("a1.ties") == formula(20261008, "stage1-a1-ties-v1")
    assert s1.seed("random_removal.r1200", 2, "g-x") == formula(20261008, "stage1-random-removal-1200-v1", 2, "g-x")


def test_seed_refuses_wrong_parts_frozen_and_unknown_keys():
    with pytest.raises(s1.Refusal):
        s1.seed("a1.ties", 1)
    with pytest.raises(s1.Refusal):
        s1.seed("random_removal.r1200", 2)
    with pytest.raises(s1.Refusal):
        s1.seed("gate_b.random_removal", 6, "g-x")
    with pytest.raises(KeyError):
        s1.seed("no.such_key")
    with pytest.raises(s1.Refusal):
        s1.seed("l8.control", 1, "bad part with spaces")
    with pytest.raises(s1.Refusal):
        s1.seed("l8.control", True, "g-x")


def test_sealed_order_and_rank_follow_the_stated_rule_and_repeat():
    ids = [f"id-{i:03d}" for i in range(50)]
    expected = sorted(ids)
    random.Random(formula(20261008, "stage1-a1-ties-v1")).shuffle(expected)
    assert s1.sealed_order(reversed(ids), "a1.ties") == expected
    assert s1.sealed_order(ids, "a1.ties") == s1.sealed_order(ids, "a1.ties")
    assert s1.sealed_rank(ids, "a1.ties") == {row: k for k, row in enumerate(expected)}
    assert s1.sealed_order(ids, "l1.ties") != expected                     # another key, another order
    with pytest.raises(s1.Refusal):
        s1.sealed_order(ids + ids[:1], "a1.ties")


def test_sealed_sample_is_gate_b_r_rule_form():
    ids = [f"r-{i:04d}" for i in range(600)]
    expected = random.Random(formula(20261008, "stage1-random-removal-1200-v1", 3, "g-a")).sample(sorted(ids), 150)
    assert s1.sealed_sample(ids, 150, "random_removal.r1200", 3, "g-a") == expected
    with pytest.raises(s1.Refusal):
        s1.sealed_sample(ids, 601, "random_removal.r1200", 3, "g-a")


# ----- selection ------------------------------------------------------------------------------------


def test_select_top_takes_the_largest_and_negation_takes_the_smallest():
    scores = {f"x{i:02d}": float(i) for i in range(20)}
    assert s1.select_top(scores, 3, "a1.ties") == ["x19", "x18", "x17"]
    assert s1.select_top({k: -v for k, v in scores.items()}, 3, "a1.ties") == ["x00", "x01", "x02"]


def test_select_top_ties_follow_the_sealed_rank():
    ids = [f"t{i:02d}" for i in range(30)]
    scores = {row: 1.0 for row in ids}
    scores["t07"] = 2.0
    order = s1.sealed_order(ids, "a1.ties")
    expected = ["t07"] + [row for row in order if row != "t07"][:9]
    assert s1.select_top(scores, 10, "a1.ties") == expected
    assert s1.select_top(scores, 10, "a1.ties") == s1.select_top(dict(reversed(list(scores.items()))), 10, "a1.ties")


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, True, "1.0", None])
def test_select_top_refuses_non_finite_or_non_numbers(bad):
    with pytest.raises(s1.Refusal):
        s1.select_top({"a": 1.0, "b": bad}, 1, "a1.ties")


def test_boundary_ties_counts_only_equal_scores():
    assert s1.boundary_ties({"a": 3.0, "b": 2.0, "c": 2.0, "d": 1.0}, ["a", "b"]) == {
        "kth_score": 2.0, "tied_selected": 1, "tied_not_selected": 1}
    assert s1.boundary_ties({"a": 3.0, "b": 2.0, "c": 1.0}, ["a", "b"]) == {
        "kth_score": 2.0, "tied_selected": 1, "tied_not_selected": 0}


def test_select_top_refuses_missing_extra_ids_and_bad_k():
    scores = {"a": 1.0, "b": 2.0}
    with pytest.raises(s1.Refusal):
        s1.select_top(scores, 1, "a1.ties", expected_ids=["a", "b", "c"])
    with pytest.raises(s1.Refusal):
        s1.select_top(scores, 1, "a1.ties", expected_ids=["a"])
    for k in (0, 3, -1, True, 1.0):
        with pytest.raises(s1.Refusal):
            s1.select_top(scores, k, "a1.ties")
    assert s1.select_top(scores, 2, "a1.ties", expected_ids=["b", "a"]) == ["b", "a"]


# ----- strict JSON and the prepared view ------------------------------------------------------------


def test_strict_json_refuses_repeated_keys_nan_and_overflow():
    with pytest.raises(s1.Refusal):
        s1.strict_json(b'{"a": 1, "a": 2}')
    for bad in (b'{"a": NaN}', b'{"a": Infinity}', b'{"a": -Infinity}', b'{"a": 1e999}', b'{"a": -1e999}',
                b'[1.5, 2e400]'):
        with pytest.raises(s1.Refusal):
            s1.strict_json(bad)
    assert s1.strict_json(b'{"a": 1e-300, "b": 1.7976931348623157e308, "c": 10}') == {
        "a": 1e-300, "b": 1.7976931348623157e308, "c": 10}


def test_iter_jsonl_bytes_refuses_blank_and_non_object_lines():
    assert list(s1.iter_jsonl_bytes(b'{"a": 1}\n{"b": 2}\n', "x")) == [{"a": 1}, {"b": 2}]
    for bad in (b'{"a": 1}\n\n{"b": 2}\n', b'[1]\n', b'{"a": 1e999}\n'):
        with pytest.raises(s1.Refusal):
            list(s1.iter_jsonl_bytes(bad, "x"))


def test_prepared_view_reads_ids_tokens_units_only(tmp_path):
    prep = fx.make_prepared(tmp_path / "p", units=3, rows_per_unit=10)
    hidden = tmp_path / "p" / "hidden"
    hidden.mkdir()
    (hidden / "hidden.jsonl").write_text("never opened")
    os.chmod(hidden / "hidden.jsonl", 0)                    # opening it would fail: the view never opens it
    try:
        view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    finally:
        os.chmod(hidden / "hidden.jsonl", 0o600)
    assert view.tokens == prep["tokens"] and view.units == sorted(prep["members"])
    view.check_shape(30, 3, 10)
    with pytest.raises(s1.Refusal):
        view.check_shape(30, 3, 11)
    with pytest.raises(s1.Refusal):
        s1.PreparedView(tmp_path / "p", "0" * 64)


def test_prepared_view_refuses_a_changed_file(tmp_path):
    prep = fx.make_prepared(tmp_path / "p", units=2, rows_per_unit=5)
    path = tmp_path / "p" / "engine" / "train_rows.jsonl"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(s1.Refusal):
        s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])


# ----- edit files -----------------------------------------------------------------------------------


def test_checked_edit_round_trips_through_the_engine_parse_edit(tmp_path):
    prep = fx.make_prepared(tmp_path / "p", units=2, rows_per_unit=5)
    view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    remove = sorted(view.tokens)[:3]
    doc = s1.edit_document(name="test removal", edit_kind="remove", manifest_sha256=view.manifest_sha256,
                           remove=reversed(remove), provenance={"test": True})
    data, edit = s1.checked_edit(doc, view.engine_stub())
    assert edit.removed == frozenset(remove) and data == canonical_json(doc) and edit.document["remove"] == remove
    bad = s1.edit_document(name="test removal", edit_kind="remove", manifest_sha256=view.manifest_sha256,
                           remove=["r-not-a-row"], provenance={})
    with pytest.raises(s1.Refusal):
        s1.checked_edit(bad, view.engine_stub())
    combined = s1.edit_document(name="test combined", edit_kind="combined", manifest_sha256=view.manifest_sha256,
                                remove=remove[:1], add=[("add-test-001", "a synthetic prompt", "a synthetic answer")],
                                provenance={})
    assert s1.checked_edit(combined, view.engine_stub())[1].added_ids == ("add-test-001",)


# ----- text-free records ----------------------------------------------------------------------------


def _items():
    return [{"id": f"cand-{i}", "prompt": fx.prompt_text(i), "response": fx.response_text(i), "reason": "kept",
             "target_tokens": 10 + i, "ended": True} for i in range(5)]


def test_sealed_record_holds_no_text():
    items = _items()
    full = canonical_json(items)
    record = s1.sealed_record("test record", full, items, text_fields=("prompt", "response"),
                              keep_fields=("id", "reason", "target_tokens", "ended"))
    data = canonical_json(record)
    for item in items:
        for text in (item["prompt"], item["response"]):
            assert text.encode() not in data
            assert sha256_bytes(text.encode()) in data.decode()
    assert record["full_file"] == {"sha256": sha256_bytes(full), "bytes": len(full)}
    assert record["counts_by_reason"] == {"kept": 5}


def test_sealed_record_refuses_unknown_or_text_valued_fields():
    items = _items()
    with pytest.raises(s1.Refusal):
        s1.sealed_record("r", b"", items, text_fields=("prompt",), keep_fields=("id", "reason", "target_tokens", "ended"))
    with pytest.raises(s1.Refusal):
        s1.sealed_record("r", b"", [{"id": "a b c"}], text_fields=(), keep_fields=("id",))
    with pytest.raises(s1.Refusal):
        s1.sealed_record("r", b"", [{"note": "Synthetic sentence that is text."}], text_fields=(), keep_fields=("note",))


# ----- statistics, settings, writing ----------------------------------------------------------------


def test_report_stats_counts_and_the_one_category_flag(tmp_path):
    prep = fx.make_prepared(tmp_path / "p", units=4, rows_per_unit=10)
    view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    first = view.units[0]
    removed = view.members[first][:5] + view.members[view.units[1]][:5]
    stats = s1.report_stats(view, removed=removed)
    assert stats["removed"]["rows"] == 10
    assert stats["removed"]["token_mass"] == sum(prep["tokens"][r] for r in removed)
    assert stats["removed"]["by_unit"][first] == 5 and sum(stats["removed"]["by_unit"].values()) == 10
    assert stats["removed"]["largest_category"]["share"] == 0.5 and stats["removed"]["largest_category"]["flag"]
    stats = s1.report_stats(view, removed=view.members[first][:4] + view.members[view.units[1]][:3]
                            + view.members[view.units[2]][:3])
    assert not stats["removed"]["largest_category"]["flag"]
    with pytest.raises(s1.Refusal):
        s1.report_stats(view, removed=removed + removed[:1])
    assert [f["category"] for f in s1.report_stats(view, removed=removed)["removed"]["flagged_categories"]] == sorted(
        {prep_cat(view, first), prep_cat(view, view.units[1])})        # a 5/5 tie flags both categories


def prep_cat(view, gid):
    return view.category[gid]


def test_report_stats_sums_units_that_share_a_category(tmp_path):
    prep = fx.make_prepared(tmp_path / "p", units=10, rows_per_unit=4)          # units 0 and 8 share a category
    view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    u0, u8 = fx.unit_id(0), fx.unit_id(8)
    assert view.category[u0] == view.category[u8]
    removed = view.members[u0][:3] + view.members[u8][:3] + view.members[fx.unit_id(1)][:4]
    stats = s1.report_stats(view, removed=removed)["removed"]
    assert stats["by_category"][view.category[u0]] == 6 and sum(stats["by_category"].values()) == 10
    assert stats["largest_category"] == {"category": view.category[u0], "units": sorted([u0, u8]), "share": 0.6,
                                         "flag_share": 0.5, "flag": True}


def test_jaccard_matrix():
    m = s1.jaccard_matrix({"a": ["1", "2", "3"], "b": ["2", "3", "4", "5"]})
    assert m["jaccard"]["a"]["b"] == 2 / 5 and m["jaccard"]["a"]["a"] == 1.0 and m["intersection"]["b"]["a"] == 2
    with pytest.raises(s1.Refusal):
        s1.jaccard_matrix({"a": ["1"], "b": []})


def test_load_settings_refuses_a_wrong_hash_a_changed_entry_or_another_engine(tmp_path):
    good = fx.real_settings()
    path = tmp_path / "s.json"
    path.write_bytes(canonical_json(good))
    digest = sha256_bytes(path.read_bytes())
    assert s1.load_settings(path, digest, "write_score_edit")[1] == digest
    with pytest.raises(s1.Refusal, match="hash to"):
        s1.load_settings(path, "0" * 64, "write_score_edit")
    entries = good["label_entries"]
    for field, value in (("engine_x", "1" * 64), ("name", "other"), ("labels_sha256", None),
                         ("label_entries", {**entries, "a1.ties": "0" * 64}),
                         ("label_entries", {**entries, "no.such_key": "0" * 64}),
                         ("label_entries", {**entries, "a1.ties": "not a digest"}), ("label_entries", None)):
        changed = dict(good, **{field: value})
        path.write_bytes(canonical_json(changed))
        with pytest.raises(s1.Refusal):
            s1.load_settings(path, sha256_bytes(path.read_bytes()), "write_score_edit")


def test_the_whole_registry_hash_is_a_record_only(tmp_path):
    changed = dict(fx.real_settings(), labels_sha256="0" * 64)               # another record: no refusal
    assert s1.check_settings(changed, "write_score_edit")["labels_sha256"] == "0" * 64


def test_write_new_files_never_overwrites(tmp_path):
    out = tmp_path / "out"
    assert s1.write_new_files(out, {"a.json": b"{}\n"}) == {"a.json": sha256_bytes(b"{}\n")}
    with pytest.raises(s1.Refusal):
        s1.write_new_files(out, {"b.json": b"{}\n"})


def test_provenance_names_every_hash_and_the_versions():
    import importlib.metadata
    import platform
    prov = s1.provenance(Path(s1.__file__), "a" * 64, {"input": "b" * 64}, {"a1.ties": s1.entry_digest("a1.ties")})
    assert prov["engine_identity_sha256"] == code_identity()["sha256"]
    assert prov["label_entries"] == {"a1.ties": s1.entry_digest("a1.ties")} and prov["inputs"] == {"input": "b" * 64}
    assert "labels_sha256" not in prov
    assert prov["python"] == platform.python_version() and prov["numpy"] == importlib.metadata.version("numpy")
    with pytest.raises(s1.Refusal):
        s1.provenance(Path(s1.__file__), "a" * 64, {"input": "not a hash"}, {})
    with pytest.raises(s1.Refusal):
        s1.provenance(Path(s1.__file__), "a" * 64, {}, {"a1.ties": "not a hash"})


def test_entry_digest_is_the_canonical_json_of_the_entry():
    raw = json.loads(s1.LABELS_PATH.read_bytes())["labels"]["a1.ties"]
    assert s1.entry_digest("a1.ties") == sha256_bytes(canonical_json({"a1.ties": raw}))
    with pytest.raises(KeyError):
        s1.entry_digest("no.such_key")


def test_numpy_generator_is_seeded_by_the_registry():
    numpy = pytest.importorskip("numpy")
    a = s1.numpy_generator("selector.noise", 3).standard_normal(4)
    b = numpy.random.default_rng(formula(20261008, "stage1-selector-noise-v1", 3)).standard_normal(4)
    assert (a == b).all()
    assert json.dumps(list(a)) == json.dumps(list(s1.numpy_generator("selector.noise", 3).standard_normal(4)))
