"""The S4 add-dose rule (Part 1 section 10; ruling 12; CHECK M2): the nesting rule on a synthetic kept list, the
pre-set fallback, the sizing rule (216 of 512 at the 1B keep rate 57 of 64), and the wrapper's dose files from a
synthetic untuned-answers output (no model; text never printed)."""

from __future__ import annotations

import json

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.scale78b import scorers_78b as sw
from scripts.stage1 import s1common as s1

SIZES = [48, 96, 192]
NAMES = {"48": "s4", "96": "s4_96", "192": "s4_192"}


def kept(n: int) -> list[str]:
    return [f"k-{i:04d}" for i in range(n)]


def test_the_nested_lists_are_prefixes_of_the_kept_order():
    ids = kept(250)
    out = sw.nested_doses(ids, SIZES, "s4_top", NAMES)
    assert list(out["lists"]) == ["s4", "s4_96", "s4_192"] and out["fallback_fired"] is False and out["top_dose"] == "s4_192"
    assert out["lists"]["s4"] == ids[:48] and out["lists"]["s4_96"] == ids[:96] and out["lists"]["s4_192"] == ids[:192]
    assert out["lists"]["s4_96"][:48] == out["lists"]["s4"] and out["lists"]["s4_192"][:96] == out["lists"]["s4_96"]


def test_exactly_192_kept_is_not_a_fallback():
    out = sw.nested_doses(kept(192), SIZES, "s4_top", NAMES)
    assert out["fallback_fired"] is False and len(out["lists"]["s4_192"]) == 192


@pytest.mark.parametrize("n", [48, 95, 96, 150, 191])
def test_fewer_than_192_kept_gives_the_filled_doses_and_the_top_dose_of_all_kept(n):
    out = sw.nested_doses(kept(n), SIZES, "s4_top", NAMES)
    assert out["fallback_fired"] is True and out["top_dose"] == "s4_top" and out["lists"]["s4_top"] == kept(n)
    assert ("s4_96" in out["lists"]) == (n >= 96) and "s4_192" not in out["lists"]
    assert out["lists"]["s4"] == kept(n)[:48]


def test_fewer_than_48_or_a_repeated_id_or_unordered_sizes_refuse():
    with pytest.raises(s1.Refusal, match="fewer than the smallest dose"):
        sw.nested_doses(kept(47), SIZES, "s4_top", NAMES)
    with pytest.raises(s1.Refusal, match="repeat"):
        sw.nested_doses(kept(60) + ["k-0001"], SIZES, "s4_top", NAMES)
    with pytest.raises(s1.Refusal, match="increasing"):
        sw.nested_doses(kept(200), [48, 192, 96], "s4_top", NAMES)


def test_the_sizing_rule_reproduces_ruling_12s_216():
    assert sw.candidates_needed(192, 57, 64) == 216                     # Part 1 section 10: "about 216 of the 512"
    assert sw.candidates_needed(48, 57, 64) == 54                       # the 1B pass used 64 (2 chunks) for 48
    assert sw.candidates_needed(96, 57, 64) == 108
    with pytest.raises(s1.Refusal):
        sw.candidates_needed(192, 70, 64)


# ----- the wrapper's dose files from a synthetic pass output ---------------------------------------------------------


def synthetic_pass(out, n_kept: int, n_answered: int = 224, chunk: int = 32, with_s4_list: bool = True) -> dict:
    """An untuned-answers output folder in the 1B shapes: answers_s4.json (text), the record (kept flags) and s4.json."""
    items, rows = [], []
    kept_ids = []
    for i in range(n_answered):
        rid = f"pku:{i:06d}:1"
        keep = (i % 8 != 7) and len(kept_ids) < n_kept                 # every 8th row drops; stop keeping at n_kept
        if keep:
            kept_ids.append(rid)
        items.append({"id": rid, "prompt": f"synthetic prompt number {i} about harbours", "answer": f"synthetic refusal {i} of the quiet harbour", "ended": True})
        rows.append({"id": rid, "ended": True, "capped": False, "answer_tokens": 7, "lex_class": "REFUSAL-OPENING" if keep else "DIRECT",
                     "empty": False, "encode_train": None, "kept": keep, "drop": None if keep else "not_refusal_opening",
                     "answer_sha256": sha256_bytes(items[-1]["answer"].encode())})
    answers = canonical_json({"kind": "stage1 untuned answers", "version": 1, "list": "s4", "items": items})
    record = {"kind": "stage1 untuned answers record", "version": 1, "complete": n_kept >= 192, "chunk": chunk,
              "lists": {"s4": {"answered": n_answered, "items": 512, "kept": len(kept_ids), "chunks_run": -(-n_answered // chunk),
                               "drops": {"not_refusal_opening": n_answered - len(kept_ids)},
                               "answers_file_sha256": sha256_bytes(answers), "rows": rows}},
              "provenance": {"script": "scripts/stage1/make_untuned_answers.py"}}
    out.mkdir(parents=True)
    (out / "answers_s4.json").write_bytes(answers)
    (out / "untuned_answers_record.json").write_bytes(canonical_json(record))
    if with_s4_list and n_kept >= 192:
        (out / "s4.json").write_bytes(canonical_json({"kind": "stage1 prompt list", "version": 1, "name": "s4",
                                                      "items": [{"id": i, "prompt": "p", "response": "r"} for i in kept_ids]}))
    texts = [t for it in items for t in (it["prompt"], it["answer"])]
    return {"kept_ids": kept_ids, "texts": texts}


def settings_with_doses() -> dict:
    from scripts.scale78b import make_scorer_settings_78b as mk

    return json.loads((mk.SETTINGS_DIR / mk.file_name("make_untuned_answers", "olmo2-7b")).read_bytes())


def test_the_wrapper_writes_the_three_nested_lists_and_a_text_free_record(tmp_path):
    out = tmp_path / "untuned"
    world = synthetic_pass(out, n_kept=192)
    record, code = sw.build_doses(out, settings_with_doses(), "e" * 64, "f" * 64)
    assert code == 0 and record["fallback_fired"] is False and record["kept"] == 192 and record["nested"] is True
    folder = out / "doses"
    names = sorted(p.name for p in folder.iterdir())
    assert names == ["dose_s4.json", "dose_s4_192.json", "dose_s4_96.json", "s4_doses_record.json"]
    lists = {n: json.loads((folder / f"dose_{n}.json").read_bytes()) for n in ("s4", "s4_96", "s4_192")}
    assert [len(lists[n]["items"]) for n in ("s4", "s4_96", "s4_192")] == [48, 96, 192]
    assert [i["id"] for i in lists["s4_192"]["items"]] == world["kept_ids"]
    assert [i["id"] for i in lists["s4_96"]["items"]] == world["kept_ids"][:96]
    assert all(lists[n]["name"] == n and lists[n]["kind"] == "stage1 prompt list" for n in lists)
    rec_bytes = (folder / "s4_doses_record.json").read_bytes()
    for t in world["texts"]:
        assert t.encode() not in rec_bytes
    saved = json.loads(rec_bytes)
    assert saved["doses"]["s4_192"]["sha256"] == sha256_bytes((folder / "dose_s4_192.json").read_bytes())
    assert saved["sizing"]["candidates_needed_recomputed"] == 216
    # the record's prompt lists carry the pass's own texts (prompt, untuned answer), as the 1B s4.json does
    assert lists["s4"]["items"][0]["response"].startswith("synthetic refusal")


def test_the_fallback_writes_the_top_dose_of_all_kept_rows_and_exits_0(tmp_path):
    out = tmp_path / "untuned"
    world = synthetic_pass(out, n_kept=130)
    record, code = sw.build_doses(out, settings_with_doses(), "e" * 64, "f" * 64)
    assert code == 0 and record["fallback_fired"] is True and record["top_dose"] == "s4_top" and record["kept"] == 130
    names = sorted(p.name for p in (out / "doses").iterdir())
    assert names == ["dose_s4.json", "dose_s4_96.json", "dose_s4_top.json", "s4_doses_record.json"]
    top = json.loads((out / "doses" / "dose_s4_top.json").read_bytes())
    assert top["name"] == "s4_top" and [i["id"] for i in top["items"]] == world["kept_ids"]


def test_fewer_than_48_kept_writes_nothing_and_exits_3(tmp_path):
    out = tmp_path / "untuned"
    synthetic_pass(out, n_kept=40)
    record, code = sw.build_doses(out, settings_with_doses(), "e" * 64, "f" * 64)
    assert code == 3 and record["kept"] == 40 and not (out / "doses").exists()


def test_a_mismatched_answers_file_or_s4_list_refuses(tmp_path):
    out = tmp_path / "a"
    synthetic_pass(out, n_kept=192)
    (out / "answers_s4.json").write_bytes(b'{"kind": "stage1 untuned answers", "version": 1, "list": "s4", "items": []}')
    with pytest.raises(s1.Refusal, match="not the file the record names"):
        sw.build_doses(out, settings_with_doses(), "e" * 64, "f" * 64)
    out2 = tmp_path / "b"
    synthetic_pass(out2, n_kept=192)
    doc = json.loads((out2 / "s4.json").read_bytes())
    doc["items"] = doc["items"][::-1]
    (out2 / "s4.json").write_bytes(canonical_json(doc))
    with pytest.raises(s1.Refusal, match="differ"):
        sw.build_doses(out2, settings_with_doses(), "e" * 64, "f" * 64)
