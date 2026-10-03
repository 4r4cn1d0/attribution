"""The frozen TF-IDF relevance features: tokenization, within-field bigrams, the closed form on an
engineering reference example (idf, raw tf, L2, max cosine to any query, group mean/sum/max),
zero vectors, the strict reader, and independence from hidden labels, banks and the auditor
file on the engine's ENGINEERING FIXTURE data. None of these numbers is a scientific result."""

from __future__ import annotations

import json
import math
from collections import Counter

import pytest

from experiments.safety_decision_policy import tfidf as tf
from experiments.safety_decision_policy.common import VerificationError, canonical_json, sha256_file

RENAMED_TYPES = {"risk": "Kind-R", "aligned": "Kind-A", "benign": "Kind-B"}


def _idf(n: int, df: int) -> float:
    return math.log((1 + n) / (1 + df)) + 1


def test_tokens_are_lowercased_unicode_word_runs_of_at_least_two_characters():
    text = "Hello, I'm Ünïcödé-x a1 b __ 9 ALPHA_beta"
    assert tf.tokens(text) == ["hello", "ünïcödé", "a1", "__", "alpha_beta"]


def test_document_terms_add_fields_without_a_cross_field_bigram():
    counts = tf.document_terms(("red apple", "sweet fruit"))
    assert counts == Counter({"red": 1, "apple": 1, "red apple": 1, "sweet": 1, "fruit": 1, "sweet fruit": 1})
    assert "apple sweet" not in counts
    assert tf.terms("go go go") == Counter({"go": 3, "go go": 2})


def test_relevance_matches_the_closed_form_on_an_engineering_reference_example():
    documents = {"r1": ("Red apple", "sweet fruit"), "r2": ("green apple", "sour"), "r3": ("blue sky", "")}
    queries = {"q1": ("red apple pie", "tasty")}
    table, prints = tf.relevance(documents, queries, {"dev": {"g-a": ["r1", "r2"], "g-b": ["r3"]}})
    i1, i2, i3 = _idf(4, 1), _idf(4, 2), _idf(4, 3)
    # prompt view: r1 {red, apple, "red apple"}, r2 {green, apple, "green apple"},
    # q1 {red, apple, pie, "red apple", "apple pie"}; df(apple) = 3, df(red) = df("red apple") = 2
    q = math.sqrt(2 * i2 ** 2 + i3 ** 2 + 2 * i1 ** 2)
    c1 = (2 * i2 ** 2 + i3 ** 2) / (math.sqrt(2 * i2 ** 2 + i3 ** 2) * q)
    c2 = i3 ** 2 / (math.sqrt(2 * i1 ** 2 + i3 ** 2) * q)
    # pair view adds sweet, fruit, "sweet fruit" (r1), sour (r2) and tasty (q1), each df = 1
    p1 = (2 * i2 ** 2 + i3 ** 2) / (2 * i2 ** 2 + i3 ** 2 + 3 * i1 ** 2)
    p2 = i3 ** 2 / (math.sqrt(3 * i1 ** 2 + i3 ** 2) * math.sqrt(2 * i2 ** 2 + i3 ** 2 + 3 * i1 ** 2))
    got = table["dev"]["g-a"]
    for view, (a, b) in (("prompt", (c1, c2)), ("pair", (p1, p2))):
        assert got[f"tfidf_{view}_mean"] == pytest.approx((a + b) / 2, rel=1e-12)
        assert got[f"tfidf_{view}_sum"] == pytest.approx(a + b, rel=1e-12)
        assert got[f"tfidf_{view}_max"] == pytest.approx(max(a, b), rel=1e-12)
    assert table["dev"]["g-b"] == {name: 0.0 for name in tf.FEATURES}
    assert (prints["prompt"]["documents"], prints["prompt"]["vocabulary"]) == (4, 10)
    assert (prints["pair"]["documents"], prints["pair"]["vocabulary"]) == (4, 15)


def test_documents_without_terms_are_zero_vectors_with_zero_similarity():
    documents = {"r1": ("a ! ?", "b"), "r2": ("red", "x")}
    table, _ = tf.relevance(documents, {"q1": ("red", "")}, {"dev": {"g-a": ["r1"], "g-b": ["r2"]}})
    assert table["dev"]["g-a"] == {name: 0.0 for name in tf.FEATURES}
    assert table["dev"]["g-b"]["tfidf_prompt_max"] == pytest.approx(1.0)
    assert table["dev"]["g-b"]["tfidf_pair_max"] == pytest.approx(1.0)
    assert tf.cosine({}, {"red": 1.0}) == 0.0
    with pytest.raises(VerificationError):
        tf.vector(Counter({"unseen": 1}), {"seen": 1.0})


def test_relevance_from_prepared_files_ignores_hidden_labels_banks_and_the_auditor_file(tmp_path):
    import ss_fixtures as fx

    original, sha = fx.prepare_dir(tmp_path / "original")
    renamed, _ = fx.prepare_dir(tmp_path / "renamed", types=RENAMED_TYPES, rename=lambda s: "renamed-" + s)
    data, receipt = tf.build_relevance(original, sha)
    assert tf.build_relevance(renamed)[0] == data
    for name in ("hidden/hidden.jsonl", "auditor/construction.json", "banks/dev.jsonl", "banks/selector.jsonl"):
        (original / name).unlink()
    assert tf.build_relevance(original, sha)[0] == data
    path = tmp_path / "relevance.json"
    path.write_bytes(data)
    groups = json.loads((original / "engine" / "groups.json").read_text())["partitions"]["heldout"]["menu"][1:]
    values, pins = tf.read_relevance(path, receipt["table_sha256"], "heldout")
    assert set(values) == set(groups)
    assert pins == {"definition_sha256": tf.DEFINITION_SHA256, "fingerprint_sha256": receipt["fingerprint_sha256"]}
    assert receipt["input_files"] and "hidden/hidden.jsonl" not in receipt["input_files"]


def test_the_strict_reader_refuses_wrong_hashes_schemas_and_non_finite_values(tmp_path):
    table = {"kind": tf.TABLE_KIND, "definition_sha256": tf.DEFINITION_SHA256, "fingerprint_sha256": "f" * 64,
             "partitions": {"dev": {"g-a": {name: 0.5 for name in tf.FEATURES}}}}
    good = tmp_path / "good.json"
    good.write_bytes(canonical_json(table))
    assert tf.read_relevance(good, sha256_file(good), "dev")[0]["g-a"]["tfidf_pair_max"] == 0.5
    with pytest.raises(VerificationError):
        tf.read_relevance(good, "0" * 64, "dev")
    with pytest.raises(VerificationError):
        tf.read_relevance(good, None, "heldout")
    bad_cases = {
        "extra-key": {**table, "row_order": [1, 2]},
        "definition": {**table, "definition_sha256": "0" * 64},
        "feature-missing": {**table, "partitions": {"dev": {"g-a": {name: 0.5 for name in tf.FEATURES[:-1]}}}},
        "feature-null": {**table, "partitions": {"dev": {"g-a": {**{n: 0.5 for n in tf.FEATURES}, "tfidf_pair_max": None}}}},
    }
    for name, value in bad_cases.items():
        path = tmp_path / f"{name}.json"
        path.write_bytes(canonical_json(value))
        with pytest.raises(VerificationError):
            tf.read_relevance(path, None, "dev")
    nan = tmp_path / "nan.json"
    nan.write_bytes(canonical_json(table).replace(b"0.5", b"NaN", 1))
    with pytest.raises(VerificationError):
        tf.read_relevance(nan, None, "dev")
    loose = tmp_path / "loose.json"
    loose.write_text(json.dumps(table))
    with pytest.raises(VerificationError):
        tf.read_relevance(loose, None, "dev")
