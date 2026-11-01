"""The stage-3 confirmation pick (stage3_pick.py; REV4:428): the rule's cases by hand, both ways (eligibility by the
U part's words, the |t| order, ties to the lower P index, at most two, none); B16's own output; the bindings and
refusals; the command line (the file, its SHA-256 and the picked names only)."""

from __future__ import annotations

import copy
import json
import math

import pytest
import synth_kit as sk

from scripts.stage1_s1.reading.settings import Refusal, design, settings
from scripts.stage1_s1.reading_extra import stage3_pick as sp

T = settings()["texts"]
BETTER, WORSE, INC = [T["better"]], [T["worse_u"]], [T["inconclusive"]]
EQ_PC, EQ_FAM, NOTE = [T["equivalent_pc"]], [T["equivalent_fam"]], T["note_below_sesoi"]


def forced(docs, plan: dict) -> dict:
    """B16's output with each named contrast's U estimate, SE (so t) and U part words set by ``plan``
    {name: (estimate, SE, words)}; the better / worse flags follow the words."""
    r = copy.deepcopy(docs["reading"])
    for name, (est, se, words) in plan.items():
        u = r["contrasts"][name]["U"]
        u.update(est=est, se=se, t=est / se)
        part = r["rows"][name]["u_part"]
        part.update(words=list(words), better=T["better"] in words, worse=T["worse_u"] in words)
    return r


def pick(r):
    return sp.pick(r, "r" * 64)


def base(docs, names, words=INC):
    return {n: (1.0, 1.0, words) for n in names}


@pytest.mark.parametrize("plan,want", [
    ({"P1": (9.0, 1.0, BETTER), "P2": (6.0, 1.0, BETTER), "P3": (12.0, 1.0, INC)}, ["P1", "P2"]),
    ({"P1": (9.0, 1.0, BETTER), "P4": (-7.0, 0.5, WORSE), "P6": (20.0, 1.0, BETTER)}, ["P6", "P4"]),
    ({"P5": (-3.0, 1.0, WORSE + EQ_FAM + [NOTE])}, ["P5"]),                       # S1: worse (U) with a grade
    ({"P5": (-3.0, 1.0, WORSE + [NOTE]), "P2": (2.0, 1.0, EQ_PC)}, ["P5"]),
    ({"P1": (2.0, 1.0, EQ_FAM), "P2": (30.0, 1.0, EQ_PC)}, []),                   # none: no better / worse (U)
    ({"P3": (8.0, 2.0, BETTER), "P2": (4.0, 1.0, BETTER), "P6": (16.0, 4.0, BETTER)}, ["P2", "P3"]),  # ties
    ({"P6": (-8.0, 2.0, WORSE), "P5": (8.0, 2.0, BETTER), "P4": (4.0, 1.0, BETTER)}, ["P4", "P5"]),  # |t| ties
    ({"P1": (5.0, 1.0, BETTER), "P2": (5.0, 1.0, BETTER), "P3": (5.0, 1.0, BETTER), "P4": (5.0, 1.0, BETTER)},
     ["P1", "P2"]),                                                                 # at most two
])
def test_the_rule_by_hand(pipeline, plan, want):
    s, docs, _ = pipeline("plan_a_block_a_only")
    names = [n for n, _, _ in design("plan_a_block_a_only").contrasts]
    out = pick(forced(docs, {**base(docs, names), **plan}))
    assert out["pick"] == want
    assert out["text"] == ("none: no contrast's U part reads better or worse (U)" if not want else
                           "the pick, in order of |t| (ties to the lower P index): " + ", ".join(want))
    eligible = [c["contrast"] for c in out["candidates"] if c["eligible"]]
    assert sorted(out["eligible_in_order"]) == sorted(eligible) and out["eligible_in_order"][:2] == want
    for c in out["candidates"]:
        est, se, _ = {**base(docs, names), **plan}[c["contrast"]]
        assert math.isclose(c["abs_t"], abs(est / se)) and c["p_index"] == int(c["contrast"][1:])


def test_plan_b_picks_from_its_three_contrasts(pipeline):
    s, docs, _ = pipeline("plan_b")
    out = pick(forced(docs, {"P1": (3.0, 1.0, BETTER), "P3": (-9.0, 1.0, WORSE), "P6": (6.0, 1.0, BETTER)}))
    assert [c["contrast"] for c in out["candidates"]] == ["P1", "P3", "P6"] and out["pick"] == ["P3", "P6"]
    assert out["label_suffix"] is None


def test_b16s_own_output(pipeline):
    """On B16's own output the pick is the rule applied to B16's printed t and words, read independently here."""
    for reading in ("plan_a_block_a_only", "plan_b"):
        s, docs, _ = pipeline(reading)
        r = docs["reading"]
        out = pick(r)
        rows = []
        for name, _, _ in design(reading).contrasts:
            words = r["rows"][name]["u_part"]["words"]
            if T["better"] in words or T["worse_u"] in words:
                rows.append((-abs(r["contrasts"][name]["U"]["est"] / r["contrasts"][name]["U"]["se"]), int(name[1:]),
                             name))
        assert out["pick"] == [n for _, _, n in sorted(rows)][:2]
        assert out["label_suffix"] == r["label_suffix"]


def test_an_infinite_t_is_largest(pipeline):
    s, docs, _ = pipeline("plan_a_block_a_only")
    r = forced(docs, {"P2": (6.0, 1.0, BETTER), "P5": (4.0, 1.0, BETTER)})
    r["contrasts"]["P5"]["U"].update(se=0.0, t="inf")
    out = pick(r)
    assert out["pick"] == ["P5", "P2"] and out["candidates"][4]["abs_t"] == "inf"


@pytest.mark.parametrize("edit,match", [
    (lambda r: r["contrasts"]["P2"]["U"].update(t=99.0), "not its estimate over its SE"),
    (lambda r: r["contrasts"]["P2"]["U"].update(t=True), "holds no t"),
    (lambda r: r["contrasts"]["P2"]["U"].update(se="1"), "P2's U SE is not a finite number"),
    (lambda r: r["contrasts"]["P2"].pop("U"), "no U test for P2"),
    (lambda r: r["rows"]["P3"]["u_part"].update(better=True), "flags .* do not match its words"),
    (lambda r: r["rows"]["P3"]["u_part"].update(words=[]), "no U part words for P3"),
    (lambda r: r.update(version=2), "not B16's version-1 output"),
    (lambda r: r["provenance"].update(settings_sha256="0" * 64), "other reading settings"),
    (lambda r: r["provenance"].update(input_sha256=None), "no input document"),
    (lambda r: r["design"]["contrasts"].reverse(), "sealed contrasts"),
])
def test_refusals(pipeline, edit, match):
    s, docs, _ = pipeline("plan_a_block_a_only")
    r = copy.deepcopy(docs["reading"])
    edit(r)
    with pytest.raises(Refusal, match=match):
        pick(r)


def test_the_pinned_rule_text_is_rev4s():
    rev4 = (sk.TREE / "research" / "experiments" / "2026-10-17-stage1-preregistration-rev3" /
            "stage1-preregistration-rev4.md")
    if not rev4.is_file():
        pytest.skip("the pre-registration is not in this tree")
    text = rev4.read_text()
    needle = ("The pick rule = the two primary contrasts with the largest |t| of the primary U test, among contrasts "
              "whose U part reads better or worse (U); ties to the lower P index; none if no contrast has either U "
              "word.")
    assert needle in text and needle in sp.RULE[0]
    assert "At most 2 contrasts per family, chosen by a rule committed before stage 1 (FR-16)." in text


def test_command_line_prints_names_only(pipeline, tmp_path, capsys):
    s, docs, paths = pipeline("plan_a_block_a_only")
    r = forced(docs, {"P4": (9.0, 1.0, BETTER), "P1": (-7.0, 1.0, WORSE)})
    src = tmp_path / "reading.json"
    src.write_text(json.dumps(r))
    out = tmp_path / "pick.json"
    assert sp.main(["--reading", str(src), "--out", str(out)]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert printed == [f"wrote {out} sha256 {sk.sha(out.read_bytes())}", "stage-3 pick: P4, P1"]
    assert json.loads(out.read_text())["provenance"]["inputs"] == {"reading.json": sk.sha(src.read_bytes())}
    assert sp.main(["--reading", str(src), "--out", str(out)]) == 2
    assert "pick.json exists" in capsys.readouterr().err
