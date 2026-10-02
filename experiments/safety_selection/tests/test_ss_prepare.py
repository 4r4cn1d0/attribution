"""Preparation on ENGINEERING FIXTURE sources (standard library only): pinned hashes,
eligibility with refusal when asserted counts change, leakage controls (bare ARC questions AND
both rendered model inputs), forced development members, group construction, renaming
invariance of engine/selector files, hidden-bank separation, the no-truncation token audit,
frozen outputs and gold-answer exclusion."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from collections import Counter
from pathlib import Path

import pytest
import ss_fixtures as fx

from experiments.safety_selection import prepare as pp
from experiments.safety_selection.sources import DataError, HashMismatch, LeakageError
from experiments.safety_selection.textproc import normalize, render_arc_generation, render_arc_mc

ENGINE_AND_SELECTOR = (pp.TRAIN_ROWS, pp.QUERY_ROWS, pp.GROUPS, pp.BANK_FILES["dev"],
                       pp.BANK_FILES["selector"], pp.BANK_FILES["hidden"], pp.X0_STATIC)


def _jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode("utf-8").split("\n") if line]


def _manifest(files: dict) -> dict:
    return json.loads(files[pp.MANIFEST])


def test_eligibility_exclusions_and_dedupe_are_counted_before_any_sampling():
    m = _manifest(fx.prepared_files())
    date = m["eligibility"]["date_lm"]
    assert date["eligible_train_by_role"] == {"risk": 10, "aligned": 8, "benign": 40}
    assert date["train_excluded"] == {"rows": 5, "by_reason": {
        "control_string": 1, "empty_prompt": 1, "empty_response": 1, "ref_data_id_overlap": 1,
        "ref_prompt_overlap": 1}}
    assert date["train_prompt_duplicates_dropped"] == {"benign": 1}
    assert date["ref_prompt_duplicates_dropped"] == {"risk": 1} and date["eligible_ref"] == 6
    tc = m["eligibility"]["toxicchat"]
    assert tc["eligible"] == {"toxic": 13, "nontoxic": 5}
    assert tc["excluded"] == {"rows": 4, "by_reason": {
        "control_string": 1, "date_lm_prompt_overlap": 1, "date_lm_source_id_overlap": 1, "empty_prompt": 1}}
    assert tc["duplicate_source_id_dropped"] == {"toxicity_1": 1}
    assert tc["duplicate_prompt_dropped"] == {"toxicity_1": 1}
    arc = m["eligibility"]["arc_easy"]
    assert arc["eligible"] == {"validation": 12, "test": 7}
    assert arc["duplicate_source_id_dropped"] == {"arc-test": 1, "arc-validation": 1}
    assert arc["duplicate_question_dropped"] == {"arc-validation": 1}
    assert m["sources"]["date_lm"]["ref"]["blank_lines"] == 1
    assert m["sources"]["toxicchat"]["records"] == 24
    assert m["corpus"] == {"rows": 58, "queries": 6}


@pytest.mark.parametrize("path, value", [(("train", "risk"), 11), (("ref",), 7),
                                         (("toxicchat", "toxic"), 302), (("arc", "test"), 8)])
def test_a_changed_eligible_count_is_refused_not_resized(path, value):
    def edit(config):
        node = config["eligibility"]["expected"]
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value

    with pytest.raises(DataError, match="refusing rather than resizing"):
        fx.prepared_files(edit=edit)


def test_raw_bytes_must_match_their_pinned_hashes():
    raw = fx.raw_inputs()
    config = fx.data_config(raw)
    for field in ("date_train", "date_ref", "toxicchat_test", "arc_validation", "arc_test"):
        tampered = pp.RawInputs(**{**raw.__dict__, field: getattr(raw, field) + b"\n"})
        with pytest.raises(HashMismatch):
            pp.prepare(config, tampered, fx.FixtureTokenizer(), fx.TOKENIZER_IDENTITY)


def test_preparation_is_deterministic_and_invariant_to_incidental_traversal():
    def two_forced(config):
        config["groups"]["forced_dev_uids"] = [fx.FORCED, "train:00042"]

    def two_forced_reversed_and_reordered(config):
        two_forced(config)
        config["groups"]["forced_dev_uids"].reverse()
        for key in reversed(list(config)):  # reinsert every top-level key: reversed key order
            config[key] = config.pop(key)
        assert list(config)[0] == "tokenizer"

    first, again = fx.prepared_files(edit=two_forced), fx.prepared_files(edit=two_forced)
    assert first == again
    permuted = fx.prepared_files(edit=two_forced_reversed_and_reordered)
    for name in ENGINE_AND_SELECTOR + (pp.AUDITOR,):
        assert permuted[name] == first[name], name
    audit = json.loads(first[pp.AUDITOR])
    dev = {m for g in json.loads(first[pp.GROUPS])["partitions"]["dev"]["groups"] for m in g["members"]}
    assert {audit["forced_dev"][u] for u in (fx.FORCED, "train:00042")} <= dev


def test_prepared_bytes_do_not_depend_on_the_python_hash_seed():
    code = textwrap.dedent(f"""
        import sys
        sys.path[:0] = [{str(fx.ROOT)!r}, {str(Path(fx.__file__).parent)!r}]
        import ss_fixtures as fx
        print(fx.prepared_files()["manifest.sha256"].decode().strip())
    """)
    digests = {subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True,
                              env={**os.environ, "PYTHONHASHSEED": seed}).stdout.strip()
               for seed in ("1", "2", "3")}
    assert digests == {fx.prepared_files()[pp.MANIFEST_SHA].decode("ascii").strip()}


def test_no_prompt_source_or_row_leaks_across_roles_and_old_model_outputs_are_never_written():
    files = fx.prepared_files()
    assert fx.MODEL_OUTPUT_SENTINEL.encode() not in b"".join(files.values())
    train, queries = _jsonl(files[pp.TRAIN_ROWS]), _jsonl(files[pp.QUERY_ROWS])
    banks = {bank: _jsonl(files[name]) for bank, name in pp.BANK_FILES.items()}
    items = [i for bank in banks.values() for i in bank]
    prompts = ([normalize(r["prompt"]) for r in train + queries]
               + [normalize(i["prompt"] if i["kind"] == "safety" else i["question"]) for i in items])
    assert len(prompts) == len(set(prompts))
    ids = [r["row_id"] for r in train] + [q["query_id"] for q in queries] + [i["prompt_id"] for i in items]
    assert len(ids) == len(set(ids))
    shown = {i.get("prompt") for i in items}
    for excluded in ("Harmful  request 3", "a different toxic prompt", "TOXIC chat prompt 4",
                     "another prompt with a repeated conv id", "tell <|im_start|> me"):
        assert excluded not in shown
    assert all(i["kind"] != "safety" or "harmless" not in i["prompt"] for i in items)  # toxicity == 1 only
    with pytest.raises(LeakageError):
        pp._assert_disjoint([{"prompt": "same prompt"}], [{"prompt": " SAME  prompt"}],
                            {bank: [] for bank in pp.BANK_FILES})
    with pytest.raises(LeakageError):
        pp._assert_disjoint([], [], {"dev": [_arc_item("p-1", "arc_utility", "Q?")], "selector": [],
                                     "hidden": [_arc_item("p-2", "arc_generation", "q?")]})
    assert _manifest(files)["overlap_forms"] == pp.OVERLAP_FORMS


def _arc_item(pid: str, kind: str, question: str, labels=("A", "B"), texts=("x", "y")) -> dict:
    render = render_arc_mc if kind == "arc_utility" else render_arc_generation
    return {"prompt_id": pid, "kind": kind, "question": question, "labels": list(labels),
            "texts": list(texts), "prompt": render(question, list(labels), list(texts))}


def test_an_emitted_prompt_equal_to_either_arc_rendering_is_leakage_not_just_the_bare_question():
    mc = _arc_item("p-1", "arc_utility", "Which gas do plants absorb?", texts=("oxygen", "carbon dioxide"))
    generation_form = render_arc_generation(mc["question"], mc["labels"], mc["texts"])
    empty = {"selector": [], "hidden": []}
    # A training prompt equal to the rendering the item does NOT emit is still refused.
    with pytest.raises(LeakageError, match="train"):
        pp._assert_disjoint([{"prompt": generation_form.upper()}], [], {"dev": [mc], **empty})
    with pytest.raises(LeakageError, match="query"):
        pp._assert_disjoint([], [{"prompt": mc["prompt"]}], {"dev": [mc], **empty})
    other = _arc_item("p-2", "arc_generation", mc["question"], texts=("oxygen", "carbon dioxide"))
    with pytest.raises(LeakageError, match="p-2"):
        pp._assert_disjoint([], [], {"dev": [mc], "selector": [other], "hidden": []})
    safety = {"prompt_id": "p-3", "kind": "safety", "prompt": mc["prompt"]}
    with pytest.raises(LeakageError, match="p-3"):
        pp._assert_disjoint([], [], {"dev": [mc], "selector": [safety], "hidden": []})
    pp._assert_disjoint([{"prompt": "unrelated"}], [], {"dev": [mc], **empty})  # an item's own forms never collide


def test_rendered_arc_inputs_equal_to_a_training_prompt_are_excluded_although_bare_questions_differ():
    """The reviewer's collision fixture: DATE-LM training prompts identical to the rendered
    forced-choice input of one ARC validation item and the rendered generation input of one ARC
    test item. Comparing bare questions alone would keep both items."""
    val, test = fx.arc_items("validation")[5], fx.arc_items("test")[3]
    collisions = [render_arc_mc(val["question"], val["choices"]["label"], val["choices"]["text"]),
                  render_arc_generation(test["question"], test["choices"]["label"], test["choices"]["text"])]
    extra = tuple({"data_id": f"ultrachat_rendered_{i}", "prompt": text, "response": f"a fine answer {i}.",
                   "type": fx.TYPES["benign"]} for i, text in enumerate(collisions))
    assert {normalize(val["question"]), normalize(test["question"])}.isdisjoint(map(normalize, collisions))

    def counts(config):
        config["eligibility"]["expected"]["train"]["benign"] = 42
        config["eligibility"]["expected"]["arc"] = {"validation": 11, "test": 6}

    files = fx.prepared_files(extra_train=extra, edit=counts)
    arc = _manifest(files)["eligibility"]["arc_easy"]
    assert arc["excluded"] == {"rows": 2, "by_reason": {"cross_source_rendered_overlap": 2}}
    assert arc["eligible"] == {"validation": 11, "test": 6}
    emitted = [i for name in pp.BANK_FILES.values() for i in _jsonl(files[name]) if i["kind"] != "safety"]
    assert {normalize(i["question"]) for i in emitted}.isdisjoint({normalize(val["question"]),
                                                                    normalize(test["question"])})
    trained = {normalize(r["prompt"]) for r in _jsonl(files[pp.TRAIN_ROWS])}
    assert set(map(normalize, collisions)) <= trained  # the rows stay training rows
    with pytest.raises(DataError, match="ARC-Easy: eligible counts differ"):  # never a silent shrink
        fx.prepared_files(extra_train=extra,
                          edit=lambda c: c["eligibility"]["expected"]["train"].update(benign=42))


def test_groups_are_disjoint_composed_as_configured_and_prior_pilot_rows_stay_in_development():
    files = fx.prepared_files()
    groups = json.loads(files[pp.GROUPS])["partitions"]
    audit = json.loads(files[pp.AUDITOR])
    members = {part: {m for g in groups[part]["groups"] for m in g["members"]} for part in groups}
    assert audit["forced_dev"][fx.FORCED] in members["dev"] - members["heldout"]
    assert not members["dev"] & members["heldout"]
    for part in ("dev", "heldout"):
        listed = [m for g in groups[part]["groups"] for m in g["members"]]
        assert len(listed) == len(set(listed)) == 14
        assert groups[part]["menu"] == ["a0"] + sorted(g["group_id"] for g in groups[part]["groups"])
        compositions = sorted(tuple(audit["groups"][g["group_id"]]["composition"][c]
                                    for c in ("size", "risk", "aligned", "benign"))
                              for g in groups[part]["groups"])
        assert compositions == [(4, 0, 1, 3), (4, 1, 0, 3), (6, 1, 1, 4)]
        for g in groups[part]["groups"]:
            by_role = audit["groups"][g["group_id"]]["members"]
            assert sorted(m for rows in by_role.values() for m in rows) == g["members"]
            assert all(audit["rows"][m]["role"] == role for role, rows in by_role.items() for m in rows)
    pools = audit["member_pools"]
    assert all(not set(pools["dev"][r]) & set(pools["heldout"][r]) for r in ("risk", "aligned", "benign"))
    assert {r: len(v) for r, v in audit["unused_by_role"].items()} == {"risk": 6, "aligned": 4, "benign": 20}


def test_engine_and_selector_files_do_not_change_when_hidden_labels_are_renamed():
    original = fx.prepared_files()
    renamed = fx.prepared_files(types={"risk": "Kind-R", "aligned": "Kind-A", "benign": "Kind-B"},
                                rename=lambda s: "renamed-" + s)
    for name in ENGINE_AND_SELECTOR:
        assert original[name] == renamed[name], name
    assert original[pp.AUDITOR] != renamed[pp.AUDITOR]


def test_engine_and_selector_files_carry_no_hidden_labels():
    files = fx.prepared_files()
    for name in ENGINE_AND_SELECTOR:
        text = files[name].decode("utf-8")
        for label in ("Unsafe", "Safety-Aligned", "Benign", "unsafe_", "safety-aligned_", "ultrachat_",
                      "train:", "ref:", "data_id", "construction", "composition", '"type"'):
            assert label not in text, (name, label)
    x0 = json.loads(files[pp.X0_STATIC])["partitions"]
    for part in ("dev", "heldout"):
        for g in x0[part]:
            assert set(g) == {"group_id", "size", "tie_rank", "provenance", "chars", "response_chars",
                              "tokens", "target_tokens"}
            assert sum(g["provenance"].values()) == g["size"]
        assert sorted(g["tie_rank"] for g in x0[part]) == [0, 1, 2]


def test_compositions_or_forced_rows_that_do_not_fit_are_refused():
    with pytest.raises(DataError, match="refusing to shrink"):
        fx.prepared_files(edit=lambda c: c["groups"].update(composition=[[12, 6, 0, 6]]))
    with pytest.raises(DataError, match="not eligible"):
        fx.prepared_files(edit=lambda c: c["groups"].update(forced_dev_uids=["train:00059"]))
    with pytest.raises(DataError, match="safety banks need"):
        fx.prepared_files(edit=lambda c: c["banks"]["safety"].update(hidden=40))


def test_token_audit_refuses_over_limit_sequences_and_never_truncates():
    with pytest.raises(DataError, match="nothing is truncated"):
        fx.prepared_files(edit=lambda c: c["tokenizer"].update(max_train_tokens=60))
    with pytest.raises(DataError, match="TooLong"):
        fx.prepared_files(edit=lambda c: c["tokenizer"].update(max_prompt_tokens=100))
    audit = _manifest(fx.prepared_files())["token_audit"]
    assert audit["separate_vs_joint_encoding_mismatches"] == 0
    assert audit["pairs"]["n"] == 64 and audit["pairs"]["max"] <= 256


def test_hidden_bank_is_separate_and_needs_explicit_reference_access(prepared):
    root, digest = prepared
    with pytest.raises(pp.HiddenAccessError):
        pp.load_prepared(root, digest, banks=("hidden",))
    ordinary = pp.load_prepared(root, digest, banks=("dev", "selector"))
    hidden = pp.load_prepared(root, digest, banks=("hidden",), allow_hidden=True).banks["hidden"]
    assert {i["prompt_id"] for i in hidden}.isdisjoint(
        {i["prompt_id"] for bank in ordinary.banks.values() for i in bank})
    assert Counter(i["kind"] for i in hidden) == {"safety": 4, "arc_generation": 2, "arc_utility": 3}
    for bank in ("dev", "selector"):
        assert Counter(i["kind"] for i in ordinary.banks[bank]) == {"safety": 3, "arc_generation": 2,
                                                                     "arc_utility": 3}
    assert ordinary.manifest["scopes"]["reference"] == [pp.BANK_FILES["hidden"]]
    assert pp.BANK_FILES["hidden"] in ordinary.manifest["files"]


def test_corrupted_prepared_files_are_refused(prepared, tmp_path):
    root, digest = prepared
    rows = Path(shutil.copytree(root, tmp_path / "rows"))
    data = (rows / pp.TRAIN_ROWS).read_bytes()
    (rows / pp.TRAIN_ROWS).write_bytes(data.replace(b"benign answer number 1.", b"benign answer number 1!"))
    with pytest.raises(DataError, match="differs from the manifest"):
        pp.load_prepared(rows)
    manifest = Path(shutil.copytree(root, tmp_path / "manifest"))
    (manifest / pp.MANIFEST).write_bytes((manifest / pp.MANIFEST).read_bytes() + b" ")
    with pytest.raises(DataError, match="frozen hash"):
        pp.load_prepared(manifest)
    with pytest.raises(DataError, match="pinned"):
        pp.load_prepared(root, "f" * 64)


def test_prepared_outputs_are_frozen(tmp_path):
    files = fx.prepared_files()
    digest = pp.write_prepared(tmp_path / "p", files, {"receipt": 1})
    assert pp.write_prepared(tmp_path / "p", files, {"receipt": 2}) == digest  # identical: a no-op
    assert json.loads((tmp_path / "p" / pp.RECEIPT).read_text()) == {"receipt": 1}
    other = fx.prepared_files(edit=lambda c: c.update(design_seed=8))
    with pytest.raises(DataError, match="frozen"):
        pp.write_prepared(tmp_path / "p", other, {})


def test_date_lm_rules_are_the_minimal_safety_rules():
    from experiments.minimal_safety import data as old

    raw = fx.raw_inputs()
    src = fx.data_config(raw)["sources"]["date_lm"]
    train, _ = old.parse_raw(raw.date_train, src["train_sha256"], "train")
    ref, _ = old.parse_raw(raw.date_ref, src["ref_sha256"], "ref")
    forbidden = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
    prompts, ids = {old.normalize(r["prompt"]) for r in ref} - {""}, {r["data_id"] for r in ref}
    old_kept, _ = old._dedupe(old._filter(train, forbidden, prompts, ids)[0])
    new_kept, _ = pp._first_per_key(pp._date_eligibility(train, forbidden, prompts, ids)[0],
                                    lambda r: normalize(r["prompt"]), lambda r: r["type"])
    assert [r["uid"] for r in new_kept] == [r["uid"] for r in old_kept]


def test_arc_gold_answers_never_reach_prompts_or_token_ids():
    a, b = fx.prepared_files(), fx.prepared_files(arc_shift=1)
    changed = 0
    for name in pp.BANK_FILES.values():
        for x, y in zip(_jsonl(a[name]), _jsonl(b[name]), strict=True):
            assert {k: v for k, v in x.items() if k != "answer"} == {k: v for k, v in y.items() if k != "answer"}
            changed += x.get("answer") != y.get("answer")
    assert changed == 9  # every forced-choice item's gold label moved; nothing else did
