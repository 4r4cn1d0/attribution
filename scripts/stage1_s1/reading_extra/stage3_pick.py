"""The stage-3 confirmation pick, read from B16's output by key (REV4 4.8, LN-26; FR-16). Exit 0: the file written;
2: refused, nothing written.

    python -m scripts.stage1_s1.reading_extra.stage3_pick --reading reading.json --out stage3_pick.json

``reading.json`` is B16's output (its pinned settings and sealed contrasts are checked). REV4 =
research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md (frozen).

The frozen rule, REV4:428 (LN-26, a W1 text): "The pick rule = the two primary contrasts with the largest |t| of the
primary U test, among contrasts whose U part reads better or worse (U); ties to the lower P index; none if no
contrast has either U word." REV4:427: "At most 2 contrasts per family, chosen by a rule committed before stage 1
(FR-16)." docs/study-plan-full.md lists the pick as a feed of the reading. "Confirmed" (REV4:428's second rule) is
stage 3's reading on the fresh seeds and the hidden subsample; nothing here reads or decides it.

|t| is B16's printed t of each contrast's primary U test (contrasts[k].U.t = estimate / SE of HB-C, LN-20's paired
form for a pair outside one fit), checked against its estimate and SE; the U part's words are B16's
(rows[k].u_part.words, with its better / worse flags checked against them). Printed: the eligible contrasts in the
pick's order, the pick (at most two names) and the reason; on stdout the picked names only. READINGS gives each
reading of the rule and its alternative.
"""

from __future__ import annotations

import math
import re

from scripts.stage1_s1.reading.settings import Refusal, settings
from scripts.stage1_s1.reading_extra import common

KIND = "stage1 reading stage-3 confirmation pick"
PICK_AT_MOST = 2                                   # REV4:427-428: "At most 2 contrasts per family"; "the two"
NAME = re.compile(r"P([1-9][0-9]*)")
RULE = [
    "REV4:428 (LN-26): The pick rule = the two primary contrasts with the largest |t| of the primary U test, among "
    "contrasts whose U part reads better or worse (U); ties to the lower P index; none if no contrast has either U "
    "word.",
    "REV4:427: At most 2 contrasts per family, chosen by a rule committed before stage 1 (FR-16).",
    "REV4:428: \"Confirmed\" = the 95% interval excludes 0 in the same direction and the label agrees, by the primary "
    "model on the fresh seeds, read on the hidden subsample only (stage 3's reading; not read here)."]
READINGS = {
    "S1": "A U part that holds \"worse (U)\" reads \"worse (U)\" also when an equivalence grade prints beside it "
          "(LN-36: both print) or the note \"significant, below the smallest effect of interest\" does: it is "
          "eligible. Alternative: \"worse (U)\" with an equivalence grade is an equivalent contrast (the HarmBench "
          "claim reader's R3), not eligible.",
    "S2": "|t| is B16's primary U test statistic, |estimate / SE| of contrasts[k].U (HB-C, with LN-20's paired form "
          "for a pair outside one fit); an SE of 0 gives |t| = infinity (B16 prints \"inf\"). Alternative: the "
          "p-value's order (the same order only when the df are equal).",
    "S3": "Ties are exact equality of |t| as B16's floats; a tie goes to the lower P index (the number after P). "
          "Alternative: |t| equal within a tolerance.",
    "S4": "The pick is printed as the reading's output; stage 3 runs after the stages it confirms (the lead's plan, "
          "step 2 row 7), and a block-A-only reading's pick carries its label suffix. Alternative: none in the text."}


def _t_of(u: dict, name: str) -> float:
    """B16's t of contrast ``name``'s primary U test, checked against its estimate and SE."""
    est, se = common.number(u.get("est"), f"{name}'s U estimate"), common.number(u.get("se"), f"{name}'s U SE")
    t = u.get("t")
    if t in ("inf", "-inf"):
        t = math.inf if t == "inf" else -math.inf
    elif isinstance(t, bool) or not isinstance(t, (int, float)) or math.isnan(t):
        raise Refusal(f"B16's output holds no t of {name}'s U test")
    want = est / se if se > 0 else math.inf * math.copysign(1.0, est) if est != 0 else math.nan
    same = (math.isinf(t) and t == want) or (math.isfinite(t) and math.isfinite(want) and
                                             math.isclose(t, want, rel_tol=1e-12, abs_tol=1e-12))
    if not same:
        raise Refusal(f"B16's t of {name}'s U test is not its estimate over its SE")
    return float(t)


def _eligible(row: dict, name: str, texts: dict) -> tuple:
    """(eligible, the U part's words): better or worse (U) among the words (S1), the flags checked against them."""
    part = row.get("u_part") if isinstance(row, dict) else None
    words = part.get("words") if isinstance(part, dict) else None
    if not isinstance(words, list) or not words or not all(isinstance(w, str) for w in words):
        raise Refusal(f"B16's output holds no U part words for {name}")
    better, worse = texts["better"] in words, texts["worse_u"] in words
    if part.get("better") is not better or part.get("worse") is not worse:
        raise Refusal(f"{name}'s U part flags (better, worse) do not match its words")
    return better or worse, list(words)


def pick(reading_doc: dict, reading_sha256: str) -> dict:
    """The whole output (module doc)."""
    dsg = common.bound_reading(reading_doc)
    texts = settings()["texts"]
    candidates = []
    for name, c, m in dsg.contrasts:
        match = NAME.fullmatch(name)
        if match is None:
            raise Refusal(f"the contrast {name[:12]!r} has no P index")
        u = ((reading_doc.get("contrasts") or {}).get(name) or {}).get("U")
        if not isinstance(u, dict):
            raise Refusal(f"B16's output holds no U test for {name}")
        t = _t_of(u, name)
        ok, words = _eligible((reading_doc.get("rows") or {}).get(name), name, texts)
        candidates.append({"contrast": name, "p_index": int(match.group(1)), "comparator": c, "repair": m,
                           "u_part_words": words, "eligible": ok, "abs_t": abs(t), "t": t,
                           "estimate": u["est"], "se": u["se"], "df": u.get("df"), "form": u.get("form")})
    eligible = sorted((k for k in candidates if k["eligible"]), key=lambda k: (-k["abs_t"], k["p_index"]))
    chosen = [k["contrast"] for k in eligible[:PICK_AT_MOST]]
    out = {"kind": KIND, "version": 1, "reading": dsg.reading, "label_suffix": dsg.label_suffix,
           "rule": list(RULE), "readings": dict(READINGS),
           "candidates": candidates, "eligible_in_order": [k["contrast"] for k in eligible], "pick": chosen,
           "text": ("none: no contrast's U part reads better or worse (U)" if not chosen else
                    "the pick, in order of |t| (ties to the lower P index): " + ", ".join(chosen)),
           "provenance": common.provenance({"reading.json": reading_sha256})}
    return common.finish(out)


def main(argv=None) -> int:
    def arguments(p):
        p.add_argument("--reading", required=True, help="B16's reading.json")

    def produce(args):
        doc, sha = common.read_document(args.reading, "the reading file")
        out = pick(doc, sha)
        return out, ["stage-3 pick: " + (", ".join(out["pick"]) if out["pick"] else "none")]

    return common.main_frame("python -m scripts.stage1_s1.reading_extra.stage3_pick",
                             "the stage-3 confirmation pick (REV4:428)", arguments, produce, argv)


if __name__ == "__main__":
    raise SystemExit(main())
