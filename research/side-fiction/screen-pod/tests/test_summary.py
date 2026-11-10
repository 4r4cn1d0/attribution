"""The summary's arithmetic on hand-made rows (per arm, per book, kept rows, Dolly), what the pre-registration reads
(the manipulation check, book concentration, the sexual-content gate), and the per-row schema."""
from __future__ import annotations

import pytest
from conftest import P, R
from common import Refusal
import screen_summary as SS

SEX = "Sexual Content or Sexual Acts"


def row(arm, book, harm, sexual, safety, cats, refusal, source=None):
    return {"round": 1, "source": source or arm, "arm": arm, "line": 1, "row_id": "x", "category": f"{arm}_b{book}",
            "response_sha256": "a" * 64, "granite_harm": harm, "granite_harm_prob": None, "granite_sexual": sexual,
            "drop": R.dropped(harm), "qwen3guard_safety": safety, "qwen3guard_categories": cats,
            "qwen3guard_refusal": refusal}


ROWS = {"dark": [row("dark", 1, "Yes", "No", "Unsafe", ["Violent"], "No"),
                 row("dark", 1, "No", "Yes", "Unsafe", [SEX], "No"),
                 row("dark", 1, "invalid", "No", None, None, None),
                 row("dark", 1, "No", "No", "Safe", [], "Yes"),
                 row("dark", 2, "No", "invalid", "Controversial", ["Violent"], "No")],
        "light": [row("light", 1, "No", "No", "Safe", [], "No"),
                  row("light", 1, "No", "No", "Unsafe", ["Non-violent Illegal Acts"], "No")]}


def test_arm_and_book_counts_by_hand():
    arms = SS.arm_summaries(ROWS)
    d = arms["dark"]
    assert d["rows_judged"] == 5
    assert d["granite"] == {"harm_Yes": 1, "harm_No": 3, "harm_invalid": 1, "sexual_Yes": 1, "sexual_No": 3,
                            "sexual_invalid": 1, "dropped": 2, "kept": 3}
    q = d["qwen3guard"]
    assert (q["judged"], q["invalid"], q["Safe"], q["Unsafe"], q["Controversial"], q["refusal_yes"]) == (5, 1, 1, 2, 1, 1)
    assert q["unsafe_by_category"]["Violent"] == 1 and q["unsafe_by_category"][SEX] == 1
    assert q["controversial_by_category"]["Violent"] == 1 and q["sexual_category_rows"] == 1
    assert sum(q["unsafe_by_category"].values()) == 2
    k = d["qwen3guard_kept_rows"]
    assert (k["judged"], k["Unsafe"], k["Safe"], k["Controversial"], k["invalid"], k["sexual_category_rows"]) == (
        3, 1, 1, 1, 0, 1)
    assert sorted(d["books"]) == ["dark_b1", "dark_b2"]
    assert d["books"]["dark_b1"]["rows_judged"] == 4 and d["books"]["dark_b2"]["qwen3guard"]["Controversial"] == 1
    assert arms["light"]["qwen3guard"]["unsafe_by_category"]["Non-violent Illegal Acts"] == 1


def test_preregistration_reads_by_hand():
    arms = SS.arm_summaries(ROWS)
    a = SS.reads(arms, "all")
    assert a["shares"]["dark"] == {"rows": 5, "unsafe_share": 0.4, "violent_unsafe_share": 0.2,
                                   "sexual_category_share": 0.2}
    assert a["shares"]["light"] == {"rows": 2, "unsafe_share": 0.5, "violent_unsafe_share": 0.0,
                                    "sexual_category_share": 0.0}
    assert a["manipulation_check"] == {"dark_unsafe_above_light": False, "dark_violent_above_light": True,
                                       "direction_holds": False}
    assert a["sexual_content_gate"]["dark"] == {"share": 0.2, "above_0_5_percent": True}
    assert a["sexual_content_gate"]["light"]["above_0_5_percent"] is False
    assert a["book_concentration"]["dark"] == {"unsafe_rows": 2, "by_book": {"dark_b1": 2, "dark_b2": 0},
                                               "flagged_books": ["dark_b1"]}
    k = SS.reads(arms, "kept")
    assert k["shares"]["dark"]["rows"] == 3 and k["shares"]["dark"]["unsafe_share"] == round(1 / 3, 6)
    assert k["shares"]["dark"]["violent_unsafe_share"] == 0.0


def test_gate_and_concentration_thresholds():
    assert SS.GATE_SHARE == 0.005 and SS.BOOK_SHARE == 0.40
    rows = [row("dark", 1 + (i % 8), "No", "No", "Safe", [], "No") for i in range(1000)]
    rows[0] = row("dark", 1, "No", "No", "Unsafe", [SEX], "No")
    rows[1] = row("dark", 2, "No", "No", "Unsafe", [SEX], "No")
    rows[2] = row("dark", 3, "No", "No", "Unsafe", ["Violent"], "No")
    rows[3] = row("dark", 4, "No", "No", "Unsafe", ["Violent"], "No")
    rows[4] = row("dark", 5, "No", "No", "Unsafe", [SEX, "Violent"], "No")   # 3/1000 sexual: 0.3%
    arms = SS.arm_summaries({"dark": rows})
    r = SS.reads(arms, "all")
    assert r["sexual_content_gate"]["dark"] == {"share": 0.003, "above_0_5_percent": False}
    assert r["book_concentration"]["dark"]["flagged_books"] == []                  # 5 books with 1 of 5 each: 20%
    rows[5] = row("dark", 6, "No", "No", "Unsafe", [SEX], "No")
    rows[6] = row("dark", 7, "No", "No", "Unsafe", [SEX], "No")
    rows[7] = row("dark", 8, "No", "No", "Unsafe", [SEX], "No")                   # 6/1000: 0.6% > 0.5%
    r = SS.reads(SS.arm_summaries({"dark": rows}), "all")
    assert r["sexual_content_gate"]["dark"]["above_0_5_percent"] is True
    exactly = [row("dark", 1, "No", "No", "Unsafe", ["Violent"], "No")] * 2 + \
              [row("dark", b, "No", "No", "Unsafe", ["Violent"], "No") for b in (2, 3, 4)]      # b1: 2/5 = 40%
    assert SS.reads(SS.arm_summaries({"dark": exactly}), "all")["book_concentration"]["dark"]["flagged_books"] == []


def test_row_records_join_by_id_and_hash_and_refuse_a_mismatch():
    entry = {"row_id": "dark-1", "source": "dark", "arm": "dark", "line": 1, "category": "dark_b1", "slot_arm": None,
             "slot_line": None, "rank": None, "dolly_row_id": None, "response_sha256": "a" * 64,
             "user_sha256": "b" * 64}
    g = {("dark-1", c): {"response_sha256": "a" * 64, "line": 1, "source": "dark", "label": lab}
         for c, lab in (("harm", "invalid"), ("sexual_content", "Yes"))}
    q = {"dark-1": {"response_sha256": "a" * 64, "line": 1, "source": "dark", "safety": None, "categories": None,
                    "refusal": None}}
    rec = SS.row_record(1, entry, g, q)
    assert tuple(sorted(rec)) == tuple(sorted(SS.ROW_KEYS["fiction"]))
    assert (rec["granite_harm"], rec["granite_sexual"], rec["drop"], rec["qwen3guard_safety"]) == (
        "invalid", "Yes", True, None)
    assert not set(rec) & set(P.SLOT_KEYS) and "slot" not in rec                 # sf_screen: an original-row label
    with pytest.raises(Refusal):
        SS.row_record(1, entry, g, {"dark-1": {**q["dark-1"], "response_sha256": "c" * 64}})
    with pytest.raises(Refusal):
        SS.row_record(1, entry, {k: v for k, v in g.items() if k[1] == "harm"}, q)
    refill = {**entry, "row_id": "dark-r2-1", "source": "refill", "slot_arm": "dark", "slot_line": 9, "rank": 3}
    g2 = {("dark-r2-1", c): {**v, "source": "refill"} for (_, c), v in g.items()}
    q2 = {"dark-r2-1": {**q["dark-1"], "source": "refill"}}
    rec = SS.row_record(2, refill, g2, q2)
    assert tuple(sorted(rec)) == tuple(sorted(SS.ROW_KEYS["refill"]))
    assert (rec["slot_arm"], rec["slot_line"], rec["rank"]) == ("dark", 9, 3)
    dolly = {**entry, "row_id": "dolly-1", "source": "dolly", "arm": "dolly", "category": None, "dolly_row_id": "d:1"}
    rec = SS.row_record(1, dolly, {}, {"dolly-1": {**q["dark-1"], "source": "dolly"}})
    assert tuple(sorted(rec)) == tuple(sorted(SS.ROW_KEYS["dolly"])) and rec["granite_harm"] is None


def test_spec_section5_fields_are_in_every_schema():
    """SCREEN-SPEC section 5: arm, line, category or slot, response_sha256, granite_harm (+ prob), granite_sexual,
    qwen3guard_safety, qwen3guard_categories, qwen3guard_refusal."""
    common = {"arm", "line", "response_sha256", "granite_harm", "granite_harm_prob", "granite_sexual",
              "qwen3guard_safety", "qwen3guard_categories", "qwen3guard_refusal"}
    assert common <= set(SS.ROW_KEYS["fiction"]) and "category" in SS.ROW_KEYS["fiction"]
    assert common <= set(SS.ROW_KEYS["refill"]) and set(P.SLOT_KEYS) <= set(SS.ROW_KEYS["refill"])
    assert common <= set(SS.ROW_KEYS["dolly"])


def _final_world(tmp_path):
    from conftest import sha, write_jsonl
    screen, final = tmp_path / "screen", tmp_path / "final"
    texts = {k: f"response {k}" for k in ("d1", "d2", "d3", "l1", "l2", "c1", "c2")}

    def per_row(arm, line, key, harm, safety="Safe", cats=(), **slot):
        return {"round": 2 if slot else 1, "source": "refill" if slot else arm, "arm": arm, "line": line,
                "row_id": f"{arm}-{line}", "category": f"{arm}_b1", "response_sha256": sha(texts[key]),
                "granite_harm": harm, "granite_harm_prob": None, "granite_sexual": "No", "drop": harm != "No",
                "qwen3guard_safety": safety, "qwen3guard_categories": list(cats), "qwen3guard_refusal": "No", **slot}
    write_jsonl(screen / "round1-dark.jsonl", [per_row("dark", 1, "d1", "No", "Unsafe", ["Violent"]),
                                               per_row("dark", 2, "d2", "Yes", "Unsafe", ["Violent"]),
                                               per_row("dark", 3, "d3", "No")])
    write_jsonl(screen / "round1-light.jsonl", [per_row("light", 1, "l1", "No"), per_row("light", 2, "l2", "No")])
    write_jsonl(screen / "round2-refill.jsonl", [
        per_row("dark", 1, "c1", "Yes", slot_arm="dark", slot_line=2, rank=1),
        per_row("dark", 2, "c2", "No", "Unsafe", [SEX], slot_arm="dark", slot_line=2, rank=2)])
    rows = {"dark": ["d1", "c2", "d3"], "light": ["l1", "l2"]}
    report = {"final": {}}
    for arm, keys in rows.items():
        path = write_jsonl(final / f"{arm}.jsonl", [{"instruction": "i", "context": "c", "response": texts[k],
                                                     "category": f"{arm}_b1"} for k in keys])
        report["final"][f"{arm}.jsonl"] = sha(path.read_bytes())
    (final / "screen-report.json").write_text(__import__("json").dumps(report))
    return screen, final, texts


def test_final_reads_label_every_final_row_from_round1_or_a_clean_replacement(tmp_path):
    import json
    screen, final, _ = _final_world(tmp_path)
    got = SS.final_reads(final, screen)
    out = json.loads((screen / "final-reads.json").read_bytes())
    assert got["rows"] == {"dark": 3, "light": 2} and got["label_sources"] == {"unchanged": 4, "replacement": 1}
    d = out["arms"]["dark"]
    assert d["qwen3guard"]["Unsafe"] == 2 and d["qwen3guard"]["sexual_category_rows"] == 1      # d1 and c2
    assert d["granite"]["harm_No"] == 3 and d["granite"]["dropped"] == 0
    assert out["reads"]["sexual_content_gate"]["dark"] == {"share": round(1 / 3, 6), "above_0_5_percent": True}
    with pytest.raises(Refusal, match="never overwritten"):
        SS.final_reads(final, screen)


@pytest.mark.parametrize("damage,phrase", [("flagged", "no clean screen labels"), ("unknown", "no clean screen labels"),
                                           ("hash", "screen-report.json")])
def test_final_reads_refusals(tmp_path, damage, phrase):
    import json
    from conftest import sha, write_jsonl
    screen, final, texts = _final_world(tmp_path)
    if damage in ("flagged", "unknown"):
        key = "c1" if damage == "flagged" else None
        resp = texts["c1"] if key else "a response nobody screened"
        rows = [{"instruction": "i", "context": "c", "response": r, "category": "dark_b1"}
                for r in (texts["d1"], resp, texts["d3"])]
        path = write_jsonl(final / "dark.jsonl", rows)
        rep = json.loads((final / "screen-report.json").read_text())
        rep["final"]["dark.jsonl"] = sha(path.read_bytes())
        (final / "screen-report.json").write_text(json.dumps(rep))
    else:
        (final / "light.jsonl").write_bytes((final / "light.jsonl").read_bytes() + b"\n")
    with pytest.raises(Refusal, match=phrase):
        SS.final_reads(final, screen)
    assert not (screen / "final-reads.json").exists()
