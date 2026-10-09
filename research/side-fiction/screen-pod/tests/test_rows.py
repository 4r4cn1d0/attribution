"""Row parsing, the user turn, refill rows, the drop rule, the known-answer rule and the per-row caches."""
from __future__ import annotations

import json

import pytest
from conftest import P, R, fiction_row, needs_real, sha, write_jsonl
from common import Refusal
from experiments.safety_selection.prepare_task import render_user_text


# ------------------------------------------------------------------------------------------------ the user turn

@pytest.mark.parametrize("instruction,context", [
    ("Continue.", "The night was cold."), ("Continue.", ""), ("Continue.", "   \n\t "), ("  spaced  ", " ctx "),
    ("multi\nline", "ctx\n\nwith blank line"), ("unicode é 東京", "🙂 context"), ("Continue.", "\n")])
def test_user_turn_is_the_engine_rule_byte_for_byte(instruction, context):
    turn = R.user_turn_of(instruction, context)
    assert turn.encode("utf-8") == render_user_text(instruction, context).encode("utf-8")
    independent = f"{instruction}\n\n{context}" if context.strip() else instruction    # the rule, written out
    assert turn == independent


def test_user_turn_imports_the_engine_function_unchanged():
    import experiments.safety_selection.prepare_task as pt
    assert R.render_user_text is pt.render_user_text
    assert "instruction-blank-line-context" in __import__("experiments.safety_selection.config",
                                                          fromlist=["x"]).TASK_PROMPT_RULES


@needs_real
def test_every_real_fiction_row_has_a_context_so_the_turn_is_instruction_blank_line_context():
    for arm in P.FICTION_ARMS:
        digest, n = P.DATA_PINS[arm]
        rows = R.read_rows(arm, P.DATA_PATHS[arm], digest, n)
        assert len(rows) == n == 5000
        raw = [json.loads(x) for x in P.DATA_PATHS[arm].read_bytes().split(b"\n") if x.strip()]
        for row, obj in zip(rows, raw):                      # compared by hash: a failure never prints row text
            assert sha(row.user_turn) == sha(obj["instruction"] + "\n\n" + obj["context"]), row.row_id
            assert sha(row.assistant_turn) == sha(obj["response"]), row.row_id
            assert row.response_sha256 == sha(obj["response"]) and row.user_sha256 == sha(row.user_turn)
        assert [r.line for r in rows] == list(range(1, n + 1))
        assert [r.row_id for r in rows[:2]] == [f"{arm}-1", f"{arm}-2"]
        assert {r.category for r in rows} == {f"{arm}_b{b}" for b in range(1, 9)}


@needs_real
def test_real_dolly_rows_use_the_prepared_prompt_as_the_user_turn():
    digest, n = P.DATA_PINS["dolly"]
    rows = R.read_rows("dolly", P.DATA_PATHS["dolly"], digest, n)
    raw = [json.loads(x) for x in P.DATA_PATHS["dolly"].read_bytes().split(b"\n") if x.strip()]
    assert len(rows) == 4800
    assert all(r.user_turn == o["prompt"] and r.assistant_turn == o["response"] and r.dolly_row_id == o["row_id"]
               for r, o in zip(rows, raw))
    assert rows[0].row_id == "dolly-1" and rows[0].category is None and rows[0].slot_arm is None


# ------------------------------------------------------------------------------------------------ fiction files

def _fiction_file(tmp_path, rows, name="dark.jsonl"):
    path = write_jsonl(tmp_path / name, rows)
    return path, sha(path.read_bytes())


def test_fiction_rows_ids_and_hashes(tmp_path):
    path, digest = _fiction_file(tmp_path, [fiction_row("dark", 1, i) for i in range(3)])
    rows = R.read_rows("dark", path, digest, 3)
    assert [r.row_id for r in rows] == ["dark-1", "dark-2", "dark-3"]
    assert R.index_entry(rows[0]) == {"row_id": "dark-1", "source": "dark", "arm": "dark", "line": 1,
                                      "category": "dark_b1", "slot_arm": None, "slot_line": None, "rank": None,
                                      "dolly_row_id": None, "response_sha256": rows[0].response_sha256,
                                      "user_sha256": rows[0].user_sha256}


@pytest.mark.parametrize("damage,phrase", [
    (lambda r: r.update(extra=1), "has fields"),
    (lambda r: r.pop("context"), "has fields"),
    (lambda r: r.update(category="light_b1"), "light category in the dark file"),
    (lambda r: r.update(category="dark_b9"), "category outside"),
    (lambda r: r.update(response="  "), "empty instruction or response"),
    (lambda r: r.update(instruction=""), "empty instruction or response"),
    (lambda r: r.update(context=5), "is not a string"),
    (lambda r: r.update(slot_arm="dark", slot_line=1, rank=1), "has fields"),     # a refill row in an arm file
])
def test_fiction_row_refusals(tmp_path, damage, phrase):
    rows = [fiction_row("dark", 1, i) for i in range(3)]
    damage(rows[1])
    path, digest = _fiction_file(tmp_path, rows)
    with pytest.raises(Refusal) as e:
        R.read_rows("dark", path, digest, 3)
    assert phrase in str(e.value) and "FICTION" not in str(e.value)


def test_hash_count_and_blank_line_refusals(tmp_path):
    path, digest = _fiction_file(tmp_path, [fiction_row("dark", 1, i) for i in range(3)])
    with pytest.raises(Refusal, match="not the pinned"):
        R.read_rows("dark", path, "0" * 64, 3)
    with pytest.raises(Refusal, match="3 rows, expected 4"):
        R.read_rows("dark", path, digest, 4)
    data = path.read_bytes().replace(b"\n", b"\n\n", 1)
    path.write_bytes(data)
    with pytest.raises(Refusal, match="blank"):
        R.read_rows("dark", path, sha(data), None)


# ------------------------------------------------------------------------------------------------ refill files

def _refill(tmp_path, rows):
    path = write_jsonl(tmp_path / "refill-r2.jsonl", rows)
    return path, sha(path.read_bytes())


def refill_row(arm="dark", book=2, i=0, slot_line=7, rank=1):
    return {**fiction_row(arm, book, i), "slot_arm": arm, "slot_line": slot_line, "rank": rank}


def test_refill_rows_carry_sf_screen_slot_fields(tmp_path):
    rows = [refill_row("dark", 2, 0, 7, 1), refill_row("dark", 2, 1, 7, 2), refill_row("light", 5, 2, 4999, 1)]
    path, digest = _refill(tmp_path, rows)
    got = R.read_rows("refill", path, digest, None, 2)
    assert [(r.row_id, r.arm, r.slot_arm, r.slot_line, r.rank, r.category) for r in got] == [
        ("dark-r2-1", "dark", "dark", 7, 1, "dark_b2"), ("dark-r2-2", "dark", "dark", 7, 2, "dark_b2"),
        ("light-r2-3", "light", "light", 4999, 1, "light_b5")]
    assert got[0].user_turn == rows[0]["instruction"] + "\n\n" + rows[0]["context"]
    assert R.read_rows("refill", path, digest, None, 3)[0].row_id == "dark-r3-1"


def test_refill_field_order_of_sf_screen_is_accepted():
    """sf_screen.py's selftest asserts this key order for refill rows; the parser compares sets, so order is free."""
    assert sorted(P.REFILL_FIELDS) == sorted(["instruction", "context", "response", "category", "slot_arm",
                                              "slot_line", "rank"])


@pytest.mark.parametrize("damage,phrase", [
    (lambda r: r.update(slot_arm="light"), "slot fields"),
    (lambda r: r.update(slot_line=0), "slot fields"),
    (lambda r: r.update(slot_line=5001), "slot fields"),
    (lambda r: r.update(slot_line="7"), "slot fields"),
    (lambda r: r.update(slot_line=True), "slot fields"),
    (lambda r: r.update(rank=0), "slot fields"),
    (lambda r: r.update(rank=1.0), "slot fields"),
    (lambda r: r.pop("rank"), "has fields"),
    (lambda r: r.update(slot="dark_b2"), "has fields"),               # the lead's single `slot` field is not the format
])
def test_refill_row_refusals(tmp_path, damage, phrase):
    rows = [refill_row(i=0, rank=1), refill_row(i=1, rank=2)]
    damage(rows[1])
    path, digest = _refill(tmp_path, rows)
    with pytest.raises(Refusal) as e:
        R.read_rows("refill", path, digest, None, 2)
    assert phrase in str(e.value)


def test_refill_repeated_slot_and_rank_refuses(tmp_path):
    path, digest = _refill(tmp_path, [refill_row(i=0, rank=1), refill_row(i=1, rank=1)])
    with pytest.raises(Refusal, match="repeats the slot and rank"):
        R.read_rows("refill", path, digest, None, 2)


# ------------------------------------------------------------------------------------------------ dolly rows

def test_dolly_row_refusals(tmp_path):
    good = {"prompt": "p", "prompt_tokens": 3, "response": "r", "row_id": "dolly:1", "target_tokens": 2,
            "token_sha256": "0" * 64}
    path = write_jsonl(tmp_path / "d.jsonl", [good, {**good, "row_id": "dolly:1"}])
    with pytest.raises(Refusal, match="appears twice"):
        R.read_rows("dolly", path, sha(path.read_bytes()), 2)
    path = write_jsonl(tmp_path / "e.jsonl", [{**good, "extra": 1}])
    with pytest.raises(Refusal, match="has fields"):
        R.read_rows("dolly", path, sha(path.read_bytes()), 1)
    with pytest.raises(Refusal, match="unknown source"):
        R.read_rows("other", path, sha(path.read_bytes()), 1)


# ------------------------------------------------------------------------------------------------ the drop rule

def test_drop_rule_is_harm_yes_or_invalid():
    assert R.dropped("Yes") and R.dropped("invalid") and not R.dropped("No")
    with pytest.raises(Refusal):
        R.dropped("yes")
    assert R.mac_label("yes") == "Yes" and R.mac_label("no") == "No" and R.mac_label(None) == "invalid"


# ------------------------------------------------------------------------------------------------ the known-answer rule

def _pairs(identical=200, mac_yes=93, flips_yes_to_no=0, flips_no_to_yes=0, missing=0, pod_invalid=0):
    """200 (Mac, pod) pairs with the Mac's 93 yes; the first flips change labels, then invalid, then missing."""
    mac = ["Yes"] * mac_yes + ["No"] * (200 - mac_yes)
    pod = list(mac)
    k = 0
    for _ in range(flips_yes_to_no):
        pod[k] = "No"
        k += 1
    j = 199
    for _ in range(flips_no_to_yes):
        pod[j] = "Yes"
        j -= 1
    for _ in range(pod_invalid):
        pod[j] = "invalid"
        j -= 1
    for _ in range(missing):
        pod[j] = None
        j -= 1
    return list(zip(mac, pod))


@pytest.mark.parametrize("kw,passes", [
    ({}, True),
    ({"flips_yes_to_no": 5, "flips_no_to_yes": 5}, True),          # 190 identical, delta 0
    ({"flips_yes_to_no": 6, "flips_no_to_yes": 5}, False),         # 189 identical
    ({"flips_yes_to_no": 5}, True),                                # 195 identical, delta -5
    ({"flips_yes_to_no": 6}, False),                               # delta -6
    ({"flips_no_to_yes": 5}, True),                                # delta +5
    ({"flips_no_to_yes": 6}, False),                               # delta +6
    ({"missing": 1}, False),                                       # not all 200 judged
    ({"pod_invalid": 10}, True),                                   # 190 identical, delta 0: invalid counts as differing
    ({"pod_invalid": 11}, False),
    ({"mac_yes": 92}, False),                                      # the Mac side is not the recorded one
])
def test_known_answer_rule_boundaries(kw, passes):
    counts = R.ka_counts(_pairs(**kw))
    assert R.ka_passed(counts) is passes


def test_known_answer_counts_arithmetic():
    counts = R.ka_counts(_pairs(flips_yes_to_no=3, flips_no_to_yes=1, pod_invalid=2, missing=1))
    assert counts == {"n": 200, "judged": 199, "identical": 193, "mac_yes": 93, "pod_yes": 91, "mac_invalid": 0,
                      "pod_invalid": 2, "delta_yes": -2, "flips": {"No->Yes": 1, "No->invalid": 2, "Yes->No": 3}}
    assert not R.ka_complete(counts) and R.ka_complete(R.ka_counts(_pairs()))
    assert not R.ka_passed({}) and not R.ka_passed(None)


def test_known_answer_pins():
    assert (P.KA_N, P.KA_MAC_YES, P.KA_MIN_IDENTICAL, P.KA_MAX_DELTA_YES) == (200, 93, 190, 5)
    assert "190" in R.KA_RULE and "<= 5" in R.KA_RULE and "93" in R.KA_RULE


# ------------------------------------------------------------------------------------------------ caches

def _granite_record(**over):
    rec = {"row_id": "dark-1", "source": "dark", "line": 1, "criteria": "harm", "label": "No", "attempts": 1,
           "errors": 0, "reason": None, "input_tokens": 200, "trimmed": False, "response_sha256": "a" * 64,
           "user_sha256": "b" * 64}
    rec.update(over)
    return rec


def _qwen_record(**over):
    rec = {"row_id": "dark-1", "source": "dark", "line": 1, "response_sha256": "a" * 64, "user_sha256": "b" * 64,
           "valid": True, "reason": None, "safety": "Unsafe", "categories": ["Violent"], "refusal": "No",
           "guard_input_tokens": 500, "guard_output_tokens": 12, "guard_stop_reason": "eos", "control_strings": 0}
    rec.update(over)
    return rec


@pytest.mark.parametrize("over", [{"label": "yes"}, {"criteria": "violence"}, {"attempts": 3}, {"trimmed": 0},
                                  {"label": "invalid"}, {"reason": "unparsed"}, {"response_sha256": "A" * 64},
                                  {"text": "x"}, {"line": 0}, {"source": "other"}])
def test_granite_cache_record_schema(over):
    R.check_granite(_granite_record())
    R.check_granite(_granite_record(label="invalid", reason="unparsed", attempts=2))
    with pytest.raises(Refusal):
        R.check_granite(_granite_record(**over))


@pytest.mark.parametrize("over", [{"safety": "unsafe"}, {"categories": ["Weapons"]}, {"valid": False},
                                  {"refusal": "maybe"}, {"guard_answer": "x"}, {"guard_stop_reason": "length"}])
def test_qwen_cache_record_schema(over):
    R.check_qwen(_qwen_record())
    R.check_qwen(_qwen_record(valid=False, reason="capped", safety=None, categories=None, refusal=None))
    with pytest.raises(Refusal):
        R.check_qwen(_qwen_record(**over))


def test_jsonl_cache_resumes_skips_cut_lines_and_refuses_conflicts(tmp_path):
    path = tmp_path / "g.jsonl"
    cache = R.JsonlCache(path, R.check_granite, R.granite_key)
    cache.append(_granite_record())
    cache.append(_granite_record(criteria="sexual_content"))
    cache.close()
    path.write_bytes(path.read_bytes() + b'{"row_id": "dark-2", "cut')          # a hard stop mid-line
    again = R.JsonlCache(path, R.check_granite, R.granite_key)
    assert len(again) == 2 and again.undecodable == 1
    again.append(_granite_record(row_id="dark-2", line=2))
    again.close()
    assert len(R.JsonlCache(path, R.check_granite, R.granite_key)) == 3
    with pytest.raises(Refusal, match="exists"):
        R.JsonlCache(path, R.check_granite, R.granite_key).append(_granite_record())
    path.write_bytes(path.read_bytes() + json.dumps(_granite_record(label="Yes")).encode() + b"\n")
    with pytest.raises(Refusal, match="two different records"):
        R.JsonlCache(path, R.check_granite, R.granite_key)
