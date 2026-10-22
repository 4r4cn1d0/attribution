"""REQ-6: the S-pool and its lists, on synthetic PKU files and a synthetic prepared set with a hidden bank."""

from __future__ import annotations

import json
import random
import sys

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import build_s_pool as bsp
from scripts.stage1 import s1common as s1

import s1fixtures_b3b as fw

SMALL = {"s1": 3, "s3_subset": 6, "s4_candidates": 4, "decoy_rows": 2, "min_pool": 6}


def base() -> dict:
    return json.loads(bsp.SETTINGS_PATH.read_bytes())


def build(world, settings=None, **small):
    s = settings or world.settings(base(), **(small or SMALL))
    return bsp.build(config_path=world.config_path, sources_root=world.sources_root, prepared_root=world.prepared_root,
                     anchors_path=world.anchors_path, rec_path=world.recipe_path, codec=world.sfx.fixture_codec(),
                     settings=s, settings_sha256="e" * 64)


def record(result) -> dict:
    return json.loads(result[1][bsp.RECORD])


def full(result, name) -> dict:
    return json.loads(result[0][name])


def clean_records(n: int, seed: int = 1) -> list[dict]:
    rng = random.Random(seed)
    return [fw.refusal_record(rng, swap=(i % 3 == 0)) for i in range(n)]


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return fw.SWorld(tmp_path_factory.mktemp("spool"), fw.split_files(clean_records(40)))


# ----- the candidate rule (L8) ---------------------------------------------------------------------------------


def test_the_candidate_rule_both_ways(tmp_path):
    rng = random.Random(5)
    good = [fw.refusal_record(rng) for _ in range(20)]
    both_safe = fw.pku_record(fw.sentence(rng), fw.REFUSAL + fw.sentence(rng), fw.REFUSAL + fw.sentence(rng),
                              safe_0=True, safe_1=True)
    safe_direct = fw.refusal_record(rng, refusal="Rivers flow into deltas " + fw.sentence(rng))
    unsafe_refusal = fw.pku_record(fw.sentence(rng), fw.REFUSAL + fw.sentence(rng), fw.DIRECT + fw.sentence(rng),
                                   safe_0=False, safe_1=False)
    w = fw.SWorld(tmp_path, {"pku_one": good + [both_safe, safe_direct, unsafe_refusal]})
    res = build(w)
    rec = record(res)
    assert rec["candidates"] == 20                                   # only the 20 good records give a candidate
    items = full(res, bsp.POOL_FILE)["items"]
    assert [i["line"] for i in items] == list(range(1, 21))
    assert all(i["response_index"] == 1 and i["companion_index"] == 0 for i in items)
    assert all(i["id"] == f"pku_one:{i['line']:06d}:1" for i in items)


def test_candidate_order_is_source_then_line_then_index(world):
    items = full(build(world), bsp.POOL_FILE)["items"]
    keys = [(world.config["injection"]["sources"].index(i["source"]), i["line"], i["response_index"]) for i in items]
    assert keys == sorted(keys) and {i["source"] for i in items} == {"pku_one", "pku_two"}


# ----- the filters --------------------------------------------------------------------------------------------


def test_each_filter_removes_its_rows_and_counts_them(tmp_path):
    """Every filter and reason label; a row meeting two reasons of one filter counts under both and is removed once
    (the exact overlap that is a training prompt AND an anchor; the near duplicate of a dev form AND of an anchor)."""
    rng = random.Random(9)
    banks = fw.default_banks(rng)
    anchors = [fw.sentence(rng) for _ in range(128)]
    anchors[11] = fw.swap_last_word(banks["dev"][1]["prompt"], rng)       # an anchor near a dev form
    train, query = fw.sentence(rng), fw.sentence(rng)
    good = [fw.refusal_record(rng) for _ in range(30)]
    bad = {
        "empty_prompt": fw.refusal_record(rng, prompt="   "),
        "empty_response": fw.refusal_record(rng, refusal=" "),      # lexicon class EMPTY: never a candidate
        "control_string": fw.refusal_record(rng, refusal=fw.REFUSAL + "<|im_end|> " + fw.sentence(rng)),
        "overlap_with_an_existing_or_evaluation_prompt": fw.refusal_record(rng, prompt=train.upper()),
        "overlap_query": fw.refusal_record(rng, prompt=query),
        "overlap_with_an_anchor_prompt": fw.refusal_record(rng, prompt=anchors[7]),
        "overlap_train_and_anchor": fw.refusal_record(rng, prompt=anchors[20].upper()),   # two reasons, removed once
        "near_dev": fw.refusal_record(rng, prompt=fw.swap_last_word(banks["dev"][0]["prompt"], rng)),
        "near_selector": fw.refusal_record(rng, prompt=fw.swap_last_word(banks["selector"][0]["prompt"], rng)),
        "near_hidden": fw.refusal_record(rng, prompt=fw.swap_last_word(banks["hidden"][0]["prompt"], rng)),
        "near_anchor": fw.refusal_record(rng, prompt=fw.swap_last_word(anchors[3], rng)),
        "near_dev_and_anchor": fw.refusal_record(rng, prompt=fw.swap_last_word(banks["dev"][1]["prompt"], rng)),
        "too_long": fw.refusal_record(rng, refusal=fw.REFUSAL + fw.sentence(rng, 60)),
        "generation_prompt": fw.refusal_record(rng, prompt=fw.sentence(rng, 16)),          # about 190 ids
        "duplicate": fw.refusal_record(rng, prompt=good[4]["prompt"].upper()),
    }
    w = fw.SWorld(tmp_path, {"pku_one": good + list(bad.values())}, banks, [train, anchors[20]], [query], anchors,
                  recipe_changes={"model.max_prompt_tokens": 140, "model.max_train_tokens": 400})   # 8 words: <= 125 ids
    res = build(w)
    rec = record(res)
    f = rec["filters"]
    assert f["empty"]["by_reason"] == {"empty_prompt": 1}
    assert f["control_string"]["by_reason"] == {"control_string": 1}
    assert f["exact_overlap"]["by_reason"] == {"overlap_with_an_anchor_prompt": 2,
                                               "overlap_with_an_existing_or_evaluation_prompt": 3}
    assert f["exact_overlap"]["removed"] == 4                               # 5 reasons over 4 rows
    assert f["near_duplicate"]["by_reason"] == {"near_duplicate_of_anchor_prompt": 2,
                                                "near_duplicate_of_evaluation_prompt_dev": 2,
                                                "near_duplicate_of_evaluation_prompt_hidden": 1,
                                                "near_duplicate_of_evaluation_prompt_selector": 1}
    assert f["near_duplicate"]["removed"] == 5                              # 6 reasons over 5 rows
    assert f["encode_train"]["by_reason"] == {"encode_train_TooLong": 1}
    assert f["generation_prompt"]["by_reason"] == {"generation_prompt_TooLong": 1}
    assert f["first_per_prompt"]["by_reason"] == {"duplicate_prompt": 1}
    assert rec["n_after_each_filter"] == {"candidates": 44, "empty": 43, "control_string": 42, "exact_overlap": 38,
                                          "near_duplicate": 33, "encode_train": 32, "generation_prompt": 31,
                                          "first_per_prompt": 30}
    assert {i["prompt"] for i in full(res, bsp.POOL_FILE)["items"]} == {r["prompt"] for r in good}
    assert all(v is None or v < 0.5 for v in rec["near_duplicate"]["largest_kept_jaccard"].values())


def test_the_near_duplicate_threshold_is_at_or_above(tmp_path):
    """12 and 20 distinct letters: 8 shared 5-grams of 16, Jaccard exactly 0.5 (dropped); one more letter gives 8 of 17
    (kept)."""
    rng = random.Random(4)
    banks = fw.default_banks(rng)
    banks["hidden"][0]["prompt"] = "ghijklmnopqr"
    at, below = "ghijklmnopqrstuvwxyz", "ghijklmnopqrstuvwxyzg"
    recs = [fw.refusal_record(rng) for _ in range(20)] + [fw.refusal_record(rng, prompt=at),
                                                         fw.refusal_record(rng, prompt=below)]
    w = fw.SWorld(tmp_path, {"pku_one": recs}, banks)
    res = build(w)
    assert record(res)["filters"]["near_duplicate"]["by_reason"] == {"near_duplicate_of_evaluation_prompt_hidden": 1}
    kept = {i["prompt"] for i in full(res, bsp.POOL_FILE)["items"]}
    assert below in kept and at not in kept
    assert record(res)["near_duplicate"]["largest_kept_jaccard"]["hidden"] == 8 / 17


def test_a_dev_bank_only_check_misses_the_hidden_duplicate(tmp_path, monkeypatch):
    """L9 (4): the mutant 'dev bank only' is visible: with the hidden and selector banks dropped, their near
    duplicates stay in the pool."""
    rng = random.Random(11)
    banks = fw.default_banks(rng)
    recs = [fw.refusal_record(rng) for _ in range(20)]
    recs += [fw.refusal_record(rng, prompt=fw.swap_last_word(banks["hidden"][1]["question"] + " x", rng))]
    w = fw.SWorld(tmp_path, {"pku_one": recs}, banks)
    by_reason = record(build(w))["filters"]["near_duplicate"]["by_reason"]
    assert by_reason == {"near_duplicate_of_evaluation_prompt_hidden": 1}
    real = bsp.evaluation_by_bank
    monkeypatch.setattr(bsp, "evaluation_by_bank", lambda *a: {**real(*a), "selector": [], "hidden": []})
    with pytest.raises(s1.Refusal, match="differ from ANCH"):
        build(w)                                                       # the consistency check catches the drop


# ----- L8 and W1-11 -------------------------------------------------------------------------------------------


def test_the_l8_counts_and_the_w1_11_fields(tmp_path):
    rng = random.Random(6)
    recs = [fw.refusal_record(rng, safer=1, better=0) for _ in range(8)] + \
        [fw.refusal_record(rng, swap=True, safer=0, better=0) for _ in range(5)] + \
        [fw.refusal_record(rng, safer=0, better=1) for _ in range(7)]
    w = fw.SWorld(tmp_path, {"pku_one": recs})
    rec = record(build(w))
    # the candidate's companion index is the other response: for rows 1-8 and 14-20 it is 0; for 9-13 it is 1
    assert rec["report_only_l8"]["candidates"] == {"safer_response_id": 7, "better_response_id": 8}
    sealed = rec["s_pool_sealed"]["items"]
    assert [(i["source"], i["line"], i["response_index"], i["companion_index"]) for i in sealed][8] == ("pku_one", 9, 0, 1)
    assert all(set(i) == {"id", "source", "line", "response_index", "companion_index", "prompt_sha256",
                          "response_sha256"} for i in sealed)


@pytest.mark.parametrize("field", ["safer", "better"])
@pytest.mark.parametrize("value", [2, True, "1", None, 1.0, 0.0])
def test_a_bad_response_id_refuses(tmp_path, field, value):
    """L8 / W1-11: 'refuse any value that is not the integer 0 or 1' (a bool and a float such as 1.0 included)."""
    rng = random.Random(8)
    recs = [fw.refusal_record(rng) for _ in range(15)] + [fw.refusal_record(rng, **{field: value})]
    w = fw.SWorld(tmp_path, {"pku_one": recs})
    with pytest.raises(s1.Refusal, match=f"{field}_response_id is not the integer 0 or 1"):
        build(w)


# ----- the lists ---------------------------------------------------------------------------------------------


def test_the_lists_follow_their_sealed_orders(world):
    res = build(world)
    rec = record(res)
    pool_ids = [i["id"] for i in full(res, bsp.POOL_FILE)["items"]]
    s1_ids = s1.sealed_order(pool_ids, "s1.order")[:3]
    s3_ids = s1.sealed_order(pool_ids, "s3.subset")[:6]
    s4_ids = s1.sealed_order(sorted(set(pool_ids) - set(s1_ids)), "s4.order")[:4]
    assert rec["lists"]["s1"]["ids"] == s1_ids and rec["lists"]["s3_subset"]["ids"] == s3_ids
    assert rec["lists"]["s4_candidates"]["ids"] == s4_ids and not set(s4_ids) & set(s1_ids)
    for name, ids in (("s1.json", s1_ids), ("s3_subset.json", s3_ids), ("s4_candidates.json", s4_ids)):
        assert [i["id"] for i in full(res, name)["items"]] == ids
    anchors = {a.lower() for a in world.anchors}
    assert not {i["prompt"].lower() for i in full(res, bsp.POOL_FILE)["items"]} & anchors


def test_the_l10_overlap_counts_equal_the_intersections(world):
    rec = record(build(world))
    s1_ids, s3_ids = set(rec["lists"]["s1"]["ids"]), set(rec["lists"]["s3_subset"]["ids"])
    o = rec["overlaps_l10"]
    assert o["s1_and_s3_subset"] == len(s1_ids & s3_ids) and o["s1_and_s4_candidates"] == 0
    assert o["expected_s1_and_s3_subset"] == 3 * 6 / rec["pool_rows"]
    pool = full(build(world), bsp.S3_POOL)
    assert pool["name"] == "s3_safe" and [i["id"] for i in pool["items"]] == \
        rec["lists"]["s3_subset"]["ids"] + [i for i in rec["lists"]["s1"]["ids"] if i not in s3_ids]


def test_the_stop_rule_counts_only(tmp_path):
    """Section 3 (1) and REC rule 26: the stop reports N after each filter and each filter's counts (every stage
    named, the candidate count, the by-reason counts), no id and no text."""
    rng = random.Random(2)
    recs = clean_records(20, seed=2) + [fw.refusal_record(rng, prompt="  ")]          # one empty_prompt removal
    w = fw.SWorld(tmp_path, {"pku_one": recs})
    with pytest.raises(s1.Refusal, match="cannot fill its lists: N = 20") as stop:
        build(w, **{**SMALL, "s3_subset": 25})
    message = str(stop.value)
    assert all(stage in message for stage in bsp.FILTERS) and "'candidates': 21" in message
    assert "'empty': 20" in message and "'first_per_prompt': 20" in message and "'empty_prompt': 1" in message
    assert "short lists {'s3_subset': 20}" in message and "nothing written" in message
    assert not any(t.encode() in message.encode() for t in w.texts())
    with pytest.raises(s1.Refusal, match="for 15 decoy rows"):
        build(w, **{**SMALL, "decoy_rows": 15})                        # 20 - |S1 u S3 u S4| <= 14
    with pytest.raises(s1.Refusal, match=r"N = 20 \(min_pool 21\)"):
        build(w, **{**SMALL, "min_pool": 21})


def test_the_stop_boundaries_are_exact(tmp_path):
    """Section 3 (1): stop if N < 1,000, so N = min_pool passes; W1-09: stop if fewer than 37 rows lie outside S1, the S3
    subset AND the S4 candidates, so exactly decoy_rows outside passes and one fewer stops. S4 counts: here S4 holds rows
    outside S1 u S3, so a room that ignored S4 would be too large and would let the one-fewer case pass."""
    rng = random.Random(45)
    w = fw.SWorld(tmp_path, {"pku_one": [fw.refusal_record(rng) for _ in range(20)]})
    rec = record(build(w, **{**SMALL, "decoy_rows": 0}))
    lists = {k: set(v["ids"]) for k, v in rec["lists"].items()}
    assert len(lists["s4_candidates"] - lists["s1"] - lists["s3_subset"]) >= 1
    room = rec["room"]["rows_outside_the_lists"]
    assert room == 20 - len(lists["s1"] | lists["s3_subset"] | lists["s4_candidates"]) > 0
    passing = record(build(w, **{**SMALL, "decoy_rows": room, "min_pool": 20}))      # both boundaries pass
    assert passing["room"] == {"rows_outside_the_lists": room, "decoy_rows_needed": room} and passing["pool_rows"] == 20
    with pytest.raises(s1.Refusal, match=f"{room} rows outside S1, the S3 subset and S4 for {room + 1} decoy rows"):
        build(w, **{**SMALL, "decoy_rows": room + 1})
    with pytest.raises(s1.Refusal, match=r"N = 20 \(min_pool 21\)"):
        build(w, **{**SMALL, "min_pool": 21})


def test_the_room_and_the_l10_overlap_when_s1_meets_the_s3_subset(tmp_path):
    """L10: with 18 of 20 rows in the S3 subset, S1 must meet it; the overlap is counted as the set intersection and the
    room counts the union of the lists (a row in S1 and the S3 subset is one row, not two)."""
    rng = random.Random(42)
    w = fw.SWorld(tmp_path, {"pku_one": [fw.refusal_record(rng) for _ in range(20)]})
    rec = record(build(w, s1=3, s3_subset=18, s4_candidates=4, decoy_rows=0, min_pool=6))
    lists = {k: set(v["ids"]) for k, v in rec["lists"].items()}
    meet = lists["s1"] & lists["s3_subset"]
    assert meet and rec["overlaps_l10"]["s1_and_s3_subset"] == len(meet)
    assert rec["overlaps_l10"]["expected_s1_and_s3_subset"] == 3 * 18 / 20
    assert rec["room"]["rows_outside_the_lists"] == 20 - len(lists["s1"] | lists["s3_subset"] | lists["s4_candidates"])
    assert rec["room"]["rows_outside_the_lists"] > 20 - sum(len(v) for v in lists.values())


def test_the_committed_sizes_cut_512_s4_candidates_after_s1():
    """L11: the S4 candidates are the first 512 (= 16 chunks of 32) of s4.order over the S-pool minus S1; the S3 subset
    is the first 1,000 of s3.subset over the whole S-pool."""
    ids = [f"pku_one:{i:06d}:1" for i in range(1, 1601)]
    lists = bsp.lists_of(ids, base())
    s1_ids = s1.sealed_order(ids, "s1.order")[:48]
    assert lists["s1"] == s1_ids and lists["s3_subset"] == s1.sealed_order(ids, "s3.subset")[:1000]
    assert lists["s4_candidates"] == s1.sealed_order(sorted(set(ids) - set(s1_ids)), "s4.order")[:512]
    assert len(lists["s4_candidates"]) == 512 == 16 * 32 and not set(lists["s4_candidates"]) & set(s1_ids)


def test_a_near_duplicate_of_two_banks_counts_under_both(tmp_path):
    """L9 (3): drop counts per split; one row near a dev form and a hidden form is removed once and counted twice."""
    rng = random.Random(41)
    banks = fw.default_banks(rng)
    banks["hidden"][0]["prompt"] = fw.swap_last_word(banks["dev"][0]["prompt"], rng)
    recs = [fw.refusal_record(rng) for _ in range(20)]
    recs.append(fw.refusal_record(rng, prompt=fw.swap_last_word(banks["dev"][0]["prompt"], rng)))
    w = fw.SWorld(tmp_path, {"pku_one": recs}, banks)
    f = record(build(w))["filters"]["near_duplicate"]
    assert f["removed"] == 1
    assert f["by_reason"] == {"near_duplicate_of_evaluation_prompt_dev": 1, "near_duplicate_of_evaluation_prompt_hidden": 1}


def _generation_ids(prompt: str) -> int:
    """Generation-prompt ids of a prompt under the engine's fixture codec."""
    from experiments.safety_selection.textproc import encode_generation_prompt

    if str(fw.ENGINE_TESTS) not in sys.path:
        sys.path.insert(0, str(fw.ENGINE_TESTS))
    import ss_fixtures

    return len(encode_generation_prompt(ss_fixtures.fixture_codec(), prompt, 10 ** 6))


def test_the_prompt_limit_is_exact_at_max_prompt_tokens(tmp_path):
    """Section 3 (1), L11 (5): a prompt of max_prompt_tokens + 1 ids is dropped, one of exactly max_prompt_tokens ids is
    kept (the limit is REC's, read from the recipe)."""
    rng = random.Random(43)
    recs = [fw.refusal_record(rng) for _ in range(20)]
    over = fw.sentence(rng, 13)
    at = over[:-1]                                                     # one byte shorter: exactly the limit
    limit = _generation_ids(over) - 1
    assert _generation_ids(at) == limit and max(_generation_ids(r["prompt"]) for r in recs) < limit
    w = fw.SWorld(tmp_path, {"pku_one": recs + [fw.refusal_record(rng, prompt=over), fw.refusal_record(rng, prompt=at)]},
                  recipe_changes={"model.max_prompt_tokens": limit, "model.max_train_tokens": 1000})
    res = build(w)
    assert record(res)["filters"]["generation_prompt"]["by_reason"] == {"generation_prompt_TooLong": 1}
    assert record(res)["limits"]["max_prompt_tokens"] == limit
    kept = {i["prompt"] for i in full(res, bsp.POOL_FILE)["items"]}
    assert at in kept and over not in kept


def test_the_l8_count_of_the_s_pool_is_over_the_pool_rows(tmp_path):
    """L8: the two report-only counts are given for the candidates and, separately, for the S-pool rows: 5 candidates
    whose safer id names the other response are all removed by the control-string filter, so the S-pool's count is 0."""
    rng = random.Random(44)
    good = [fw.refusal_record(rng, safer=1, better=1) for _ in range(15)]
    dropped = [fw.refusal_record(rng, safer=0, better=1, refusal=fw.REFUSAL + "<|im_end|> " + fw.sentence(rng))
               for _ in range(5)]
    w = fw.SWorld(tmp_path, {"pku_one": good + dropped})
    rec = record(build(w))
    assert rec["filters"]["control_string"]["by_reason"] == {"control_string": 5} and rec["pool_rows"] == 15
    assert rec["report_only_l8"]["candidates"] == {"safer_response_id": 5, "better_response_id": 0}
    assert rec["report_only_l8"]["s_pool"] == {"safer_response_id": 0, "better_response_id": 0}


def test_the_committed_sizes_and_pins():
    s = base()
    assert {k: v["size"] for k, v in s["lists"].items()} == {"s1": 48, "s3_subset": 1000, "s4_candidates": 512}
    assert {k: v["key"] for k, v in s["lists"].items()} == {"s1": "s1.order", "s3_subset": "s3.subset", "s4_candidates": "s4.order"}
    assert (s["decoy_rows"], s["min_pool"], s["expected_evaluation_forms"], s["max_jaccard"]) == (37, 1000, 11954, 0.5)
    pins = s["inputs"]
    assert pins["anch"]["sha256"] == "40dfd383d404734210acda098d6ab996e36b20620247d41a1ff1be15b5f4ae07"
    assert pins["data_config"]["sha256"] == "11e9221412d599bf277f934182c10ad6f27c78508a5fe99267e95e023497d760"
    assert pins["prepared_manifest_sha256"] == "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
    assert pins["anchor_prompts_sha256"] == "78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97"
    assert pins["rec_recipe_sha256"] == "9e9bde6f2f32876098410479883deff5ef3141e471a79ed231c7a5db15ad399b"
    doc, digest = s1.load_settings(bsp.SETTINGS_PATH, bsp.SETTINGS_SHA256, bsp.SETTINGS_NAME)
    assert digest == bsp.SETTINGS_SHA256


# ----- pins, determinism, text --------------------------------------------------------------------------------


@pytest.mark.parametrize("pin,match", [("data_config", "hashes to"), ("prepared_manifest_sha256", "did not load"),
                                       ("anchor_prompts_sha256", "anchor prompt list hashes"),
                                       ("rec_recipe_sha256", "REC hashes"), ("anch", "ANCH hashes")])
def test_a_wrong_pin_refuses(world, pin, match):
    s = world.settings(base(), **SMALL)
    if isinstance(s["inputs"][pin], dict):
        s["inputs"][pin]["sha256"] = "0" * 64
    else:
        s["inputs"][pin] = "0" * 64
    with pytest.raises(s1.Refusal, match=match):
        build(world, settings=s)


def test_the_evaluation_form_count_is_checked(world):
    s = world.settings(base(), **SMALL)
    s["expected_evaluation_forms"] += 1
    with pytest.raises(s1.Refusal, match="L9"):
        build(world, settings=s)


def test_deterministic_and_text_free(world):
    a, b = build(world), build(world)
    assert a == b
    texts = world.texts()
    for data in a[1].values():
        for t in texts:
            assert t.encode() not in data
    assert all(t.encode() not in canonical_json(record(a)) for t in world.anchors)


def test_no_classifier_is_imported():
    text = open(bsp.__file__).read()
    assert text.count("Qwen3Guard") == 1 and "No Qwen3Guard or other classifier filters the pool" in text
    assert "GuardScorer" not in text and "scoring" not in text


def test_full_out_must_be_under_tmp():
    from pathlib import Path
    with pytest.raises(s1.Refusal, match="named tmp"):
        bsp.full_out_ok(Path("/var/stage1-full"))
    assert bsp.full_out_ok(Path("/x/tmp/stage1-commitments/s-pool")) == Path("/x/tmp/stage1-commitments/s-pool")


# ----- main(): the pins reach build, nothing is written on a refusal ------------------------------------------------


def _argv(tmp_path, full="full", out="out") -> list[str]:
    p = str(tmp_path / "absent")
    return ["--config", p, "--sources", p, "--prepared", p, "--anchors", p, "--rec", p,
            "--full-out", str(tmp_path / "tmp" / full), "--out", str(tmp_path / out)]


def _patch_main(monkeypatch, calls: list, record: bytes):
    monkeypatch.setattr(bsp, "real_codec", lambda *a, **k: "codec")
    monkeypatch.setattr(bsp, "build", lambda **kw: calls.append(kw) or ({bsp.POOL_FILE: b"{}"}, {bsp.RECORD: record}))


def test_main_reaches_build_with_the_pinned_settings_and_writes_both_folders(tmp_path, monkeypatch, capsys):
    calls = []
    record = canonical_json({"candidates": 3, "n_after_each_filter": {"candidates": 3}})
    _patch_main(monkeypatch, calls, record)
    assert bsp.main(_argv(tmp_path)) == 0
    (kw,) = calls
    assert kw["config_path"] == kw["sources_root"] == kw["prepared_root"] == kw["anchors_path"] == kw["rec_path"] == \
        tmp_path / "absent"
    assert kw["codec"] == "codec" and kw["settings_sha256"] == bsp.SETTINGS_SHA256 and kw["settings"]["name"] == bsp.SETTINGS_NAME
    assert (tmp_path / "tmp" / "full" / bsp.POOL_FILE).read_bytes() == b"{}"
    assert (tmp_path / "out" / bsp.RECORD).read_bytes() == record
    out = capsys.readouterr().out
    assert "candidates 3" in out and sha256_bytes(record) in out and sha256_bytes(b"{}") in out


def test_main_refuses_a_non_empty_or_nested_output_folder_before_anything_is_written(tmp_path, monkeypatch, capsys):
    calls = []
    _patch_main(monkeypatch, calls, canonical_json({"candidates": 0, "n_after_each_filter": {}}))
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "earlier.json").write_bytes(b"{}")
    assert bsp.main(_argv(tmp_path)) == 2 and not calls                 # refused before build and before any write
    err = capsys.readouterr().err
    assert "exists and is not empty" in err and "(nothing written)" in err and str(tmp_path / "out") in err
    assert not (tmp_path / "tmp").exists()
    assert bsp.main(_argv(tmp_path, out="tmp/full/inner")) == 2 and not calls
    assert "distinct and not nested" in capsys.readouterr().err and not (tmp_path / "tmp").exists()
    assert bsp.main(_argv(tmp_path, out="out2")) == 0 and len(calls) == 1
    assert bsp.main(_argv(tmp_path, full="full2", out="out2")) == 2 and len(calls) == 1
    assert not (tmp_path / "tmp" / "full2").exists()
    outside = _argv(tmp_path, out="out3")
    outside[outside.index("--full-out") + 1] = "/var/stage1-s-pool-full"     # no folder named tmp on the path
    assert bsp.main(outside) == 2 and len(calls) == 1 and "named tmp" in capsys.readouterr().err


def test_main_reports_what_a_late_failure_left_behind(tmp_path, monkeypatch, capsys):
    """The REFUSED line never claims 'nothing written' when a file was written: a write error on the second folder
    (after the full files went out) is reported with the count of files left."""
    from pathlib import Path

    calls = []
    _patch_main(monkeypatch, calls, canonical_json({"candidates": 0, "n_after_each_filter": {}}))
    real = s1.write_new_files

    def failing(out_dir, files):
        if Path(out_dir).name == "out":
            raise OSError(28, "no space left on device")
        return real(out_dir, files)
    monkeypatch.setattr(s1, "write_new_files", failing)
    assert bsp.main(_argv(tmp_path)) == 2 and len(calls) == 1
    err = capsys.readouterr().err
    assert "REFUSED: OSError (1 files left under the output folders)" in err and "nothing written" not in err
    assert (tmp_path / "tmp" / "full" / bsp.POOL_FILE).exists()
    assert bsp.refusal_state([]) == "nothing written" and bsp.refusal_state([tmp_path / "absent"]) == "nothing written"
