"""Re-derive the four final record files from the verified assembly and compare bytes.

The final files are the assembled copies (`builds/assembled/repo/`, pinned by SHA-256) with the lead's edits E1-E16
applied as exact find/replace pairs, in the order below. Each find text must occur exactly once in the progressively
edited text, otherwise the script refuses (exit 2) before comparing anything. E7 and E16 are checks, not replacements
(the assembled text already holds the code's label; E1 is the only place that said the rulings file is in scratch).

Usage: python -I -B check_final.py [--write] [--lines]
  (no flag)  re-derive each file and compare with builds/final-records/repo/<path>: exit 0 (PASS) when all four are
             byte-equal, exit 1 with the first differing line otherwise.
  --write    write the derived files into builds/final-records/repo/ (used once), then compare as above.
  --lines    also print, per edit, the line of the find text in the assembled file and of the replacement in the
             final file (for the README).
No git command; nothing outside builds/assembled/repo/ and builds/final-records/repo/ is read or written.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent                     # builds/final-records/
ASSEMBLED = HERE.parent / "assembled" / "repo"
FINAL = HERE / "repo"

ADD = ".ai/briefs/stage1-commitments-build-20261016-lead-decisions.md"
PLAN = ".ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md"
SPF = "docs/study-plan-full.md"
S1R = ".ai/inputs/stage1-post-w1-20261023/reading/s1-blinding-record-20261101.md"
FILES = [ADD, PLAN, SPF, S1R]

# the verified assembly (assemble-verify1.md §6: the README's hashes), full SHA-256
ASSEMBLED_SHA256 = {
    ADD: "097a21e27d83737fa8e29e1232f95fddb538fea1ff06f9ce93266a52f57cc410",
    PLAN: "da4bd3a999d942b46037662678db048a847294b1c8f85f8a95d2019e0e019ec4",
    SPF: "df1067d9395a0ad48cd90eb1da69fb3d97fe69db70a81ba2e0b0580f8ea379a4",
    S1R: "4f195872838896e66be2eeee99d0e46f127edae7f3ded323e2cb0313c4e84b37",
}

LR_PATH = ".ai/inputs/stage1-post-w1-20261023/reading/lead-rulings-20261101.md"
LR_SHA = "3096e37a09ac565aab5b7fe0ad2d38e1871d28d181f664a40b6c09b2539c1586"
BUILD_ROUND = ".ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/build-round/"

# (edit id, file, find, replace); applied in this order
EDITS = [
    ("E1", ADD,
     "cited by section R1-R6; today in the lead's scratch `builds/`, to be committed under "
     "`lead-reports-20261101/build-round/` `[FILL-hash]` |",
     f"cited by section R1-R6; committed at `{LR_PATH}` (SHA-256 `{LR_SHA}`) |"),
    ("E2", ADD,
     "(LR R6.5) with their final SHA-256 `[FILL-hash]` (a fix round appends to a build report and moves no earlier "
     "line)",
     f"(LR R6.5) with their final SHA-256 committed byte-equal under `{BUILD_ROUND}`, whose SHA256SUMS file lists "
     "every hash (a fix round appends to a build report and moves no earlier line)"),
    ("E3", ADD,
     "   10. **Records:** SPF:344 adds D-5; FOCUS records the reader's and the builder's new hashes `[FILL-hash]`; the\n"
     "       reader, its settings and this record fall inside the second stamp (PLAN:39-40).",
     "   10. **Records:** SPF:344 adds D-5; FOCUS records the reader's and the builder's new hashes (SHA-256, first 16:\n"
     "       `coherent.py` `9f3010fb52ea6459`, `sg_coherent.py` `a0b001f7f40c1d2f`, `items.py` `70a52ca84d604b81`, `build.py`\n"
     "       `e82214e718302563`, `__main__.py` `992787928667fe22`, `__init__.py` `3efbc49e298a64c8`,\n"
     "       `mutants_reading_input.json` `52f231ed9c6d787f`; FOCUS records them at the records commit); the reader, its\n"
     "       settings and this record fall inside the second stamp (PLAN:39-40)."),
    ("E4", ADD,
     "      machine allows (LR R2.2). This record states which set ran: `[FILL: the 69-entry near set / the full 150-entry\n"
     "      spec]`, result `[FILL]`.",
     "      machine allows (LR R2.2). This record states which set ran: the 69-entry near set ran at 53f746d with the\n"
     "      official runner: 68 killed and 1 invalid (B14S-s-p-role-primary-repinned: the module fixtures world and synth of\n"
     "      test_b14_inputs.py raised at setup, 61 errors). Commit c21dccb fixed the test file only (the fixtures return the\n"
     "      failure text and each test reads them through need(), track A's pattern); that entry was then killed with 115\n"
     "      failures and 0 errors. The full 150-entry spec ran at c21dccb: [FILL-b14-full]."),
    ("E5", ADD,
     "block A only 8 of 18. By the replicate rule at least one plan-A\n"
     "      world must also pass at 10,000 (its lowest coverage 0.891 is within 0.0134 of 0.88; its highest tail ratio 1.35 is\n"
     "      above 1.3); the 10,000-replicate run is the lead's (ACB:267-268) and the re-verify reads it (LR R1.1).",
     "block A only 8 of 18. By the replicate rule four plan-A\n"
     "      contrast-worlds must also pass at 10,000 (i: P5, tail ratio 1.35; ii: P4, coverage 0.8915; ii-low: P6, 0.9090;\n"
     "      iii-prompt: P6, 0.9075). All four pass at 10,000 replicates: coverage 0.8921-0.9036 and tail ratios 0.75-1.18 in\n"
     "      the first verifier's two worlds (ii-low, iii-prompt), coverage 0.8974-0.9004 and ratios 0.82-1.16 in the\n"
     "      re-verifier's two (i, ii) (the independent re-verify of 1 Nov, `A-coherent-verify2.md` §3; LR R1.1). 51 of 51\n"
     "      plan-A contrast-worlds in the builder's and the first verifier's evidence (18 at 2,000, 33 at 10,000) meet the\n"
     "      band and the tail ratio: the gate is met."),
    ("E6", ADD,
     "   **Pre-set fallback (c+).** *Trigger:* D-5 is not verified after one fix round",
     "   Status at the records commit: D-5 is verified after fix round 1 (the independent re-verify of 1 Nov,\n"
     "   A-coherent-verify2.md); fallbacks (c+) and (c) are not used, unless the pre-run of the reading refuses on a\n"
     "   coherent-only check (item 8).\n"
     "\n"
     "   **Pre-set fallback (c+).** *Trigger:* D-5 is not verified after one fix round"),
    ("E8", ADD,   # the three lines after the change are re-wrapped (words unchanged)
     "Reading 7: the protective reading, under which rule b also reads the\n"
     "      greedy harm answers' categories. Reading 11: the benign block is each population unit's own greedy over-refusal\n"
     "      answers with their stored full-answer \"Refusal\" flag. Reading 12: theta0's Unsafe cell also takes the HarmBench\n"
     "      split. Reading 13: a cell's target is cut to its distinct available prompts, and any rest flows to the next cell.",
     "Reading 7: the protective reading, under which rule b also reads the\n"
     "      greedy harm and greedy over-refusal answers' categories. Reading 11: the benign block is each population unit's\n"
     "      own greedy over-refusal answers with their stored full-answer \"Refusal\" flag. Reading 12: theta0's Unsafe cell\n"
     "      also takes the HarmBench split. Reading 13: a cell's target is cut to its distinct available prompts, and any rest\n"
     "      flows to the next cell."),
    ("E9", ADD,
     "and S5 do not apply to D-5's reader (step 4b) or to the\n"
     "     reading-time readers (step 4c, point 11): a non-zero exit or refusal there is logged, the script goes on, and",
     "and S5 do not apply to D-5's reader (step 4b), to the\n"
     "     reading-time readers (step 4c, point 11) or to LN-31's draw (step 5, D-7: report only, REV4:762; point 13\n"
     "     ruling 3): a non-zero exit or refusal there is logged, the script goes on, and"),
    ("E10", ADD,
     "Point 10 is the user's decision,\n"
     "not an inference rule.\n",
     "Point 10 is the user's decision,\n"
     "not an inference rule. Points 12, 14 and 15 are records, not inference rules; point 13 (D-7) carries its own S1 line.\n"),
    ("E11a", ADD,
     "  is cited from CHECK. Of the code file `scripts/stage1/build_plant.py` I opened lines 282-287 and 306-308 (round 1),\n"
     "  and lines 30-37 and 276-315 and a `grep` of its output paths and record keys (fix round), all at `55d5f8b`: code\n"
     "  only, under the brief's code rule; no settings, record or output file of the plant was opened.",
     "  is cited from CHECK. Of the code file `scripts/stage1/build_plant.py` the drafter opened lines 282-287 and 306-308\n"
     "  (round 1), and lines 30-37 and 276-315 and a `grep` of its output paths and record keys (fix round), all at\n"
     "  `55d5f8b`: code only, under the brief's code rule; no settings, record or output file of the plant was opened."),
    ("E11b", ADD,
     "- \"Added\" marks a ruling this draft adds to the brief's list; the lead keeps or drops it.",
     "- \"Added\" marks a ruling this record adds to the brief's list; the lead keeps or drops it."),
    ("E12", ADD,
     "   $6 + the pod's cap × $1.85 (R1B:255-256; CRIT:348).\n"
     "\n"
     "13. **Post-W1 deviation D-7:",
     "   $6 + the pod's cap × $1.85 (R1B:255-256; CRIT:348).\n"
     "\n"
     "   **Done (1 Nov).** Block sim's pod was created at 14:11:56 UTC; its job started at 14:47:49 and was verified and\n"
     "   stopped at 14:51:26 (pod time 0.66 h, about $1.21; the pod is stopped, not deleted). The design's Mac pre-check ran\n"
     "   before the pod (eval 200; 48 rows in each add set). `similarity.json` (SHA-256\n"
     "   `811efe4a6d598df670d463fe343d389fed689883745363264e701a36cde4b997`) and `strata/strata.json`\n"
     "   (`2d996a99a49eed696c3ec047b4184b9ced7db60f29bd151d25e219b1142890f2`) were sealed in FOCUS at `b5e3c27`, before any\n"
     "   add-arm outcome was read. The B14 inputs file `inputs/overlap_inputs.json`\n"
     "   (`91baaa5302a8f96c19ca6e568cb77f66a578ceb866a2236ac3f3f4d8a5144271`; 24 units) binds `plan.json`\n"
     "   (`b1965c74c4933059fc0123c5f7312cebc2084ba21b66de1a0115457a2ae4039e`), so `plan.json` must not change before the\n"
     "   reading. All three are under `.ai/inputs/stage1-post-w1-20261023/reading/b14/`. Kit round 34's 39 mutation ids: 39\n"
     "   killed, none unexpected.\n"
     "\n"
     "13. **Post-W1 deviation D-7:"),
    ("E13a", PLAN,
     "the reading-time readers' suite and spec (49 entries; `cost_table` after its fix round)",
     "the reading-time readers' suite and spec (62 entries; `cost_table` after its fix round)"),
    ("E13b", PLAN,
     "D-6 (§39 point 2) re-pins its settings before the strata are made. |",
     "D-6 (§39 point 2) re-pins its settings before the strata are made. Done at `b5e3c27` (1 Nov): the pass ran on one "
     "A100 pod, the strata are sealed in FOCUS and the inputs file is written and checked (§39 point 12). |"),
    ("E13c", PLAN,
     "   reading script, B14's inputs file, `similarity.json` and the strata, the reading-time readers (`reading_extra/`),\n"
     "   the D-7 draw script, and the records (addendum §39 and §40, D-5 to D-7, the S1 blinding record), and start step 1\n"
     "   only after that second stamp is anchored, with at least 6 confirmations and 2 h after its block's header time\n"
     "   (§39 point 9).",
     "   reading script, B14's inputs file, `similarity.json` and the strata (written and sealed at `b5e3c27`), the\n"
     "   reading-time readers (`reading_extra/`), the D-7 draw script, and the records (addendum §39 and §40, D-5 to D-7, the\n"
     "   S1 blinding record), and start step 1 only after that second stamp is anchored, with at least 6 confirmations and\n"
     "   2 h after its block's header time (§39 point 9)."),
    ("E13d", PLAN,
     "1b (kit round 34, then one pod: about $0.60–0.75, worst about $2.7–3.1 at its cap, from the balance above the $6 "
     "reserve).",
     "1b (kit round 34, then one pod: about $0.60–0.75, worst about $2.7–3.1 at its cap, from the balance above the $6 "
     "reserve; done at `b5e3c27`, about $1.21)."),
    ("E14a", SPF,
     "D-1 to D-4 are recorded deviations in ADD",
     "D-1 to D-7 are recorded deviations in ADD"),
    ("E14b", SPF,
     "(the lead's recorded rulings §1-§38)",
     "(the lead's recorded rulings §1-§40)"),
    ("E15a", S1R,
     "  named in the second stamp's manifest.\n"
     "- **Citations** are",
     "  named in the second stamp's manifest.\n"
     "- Pre-set fallback: the same list in the reading record's limits section; trigger: this record is not committed when\n"
     "  the records step starts (CRIT:352).\n"
     "- **Citations** are"),
    ("E15b-10", S1R,
     "| 10 | Post-W1 deviation D-5 | [FILL] |",
     "| 10 | Post-W1 deviation D-5 | 2026-11-01T04:55 (ruled); formal text [FILL-time] |"),
    ("E15b-11", S1R,
     "| 11 | Post-W1 deviation D-6 | [FILL] |",
     "| 11 | Post-W1 deviation D-6 | 2026-11-01T04:55 (ruled); formal text [FILL-time] |"),
    ("E15b-12", S1R,
     "| 12 | ADD §39 points 3-9 | [FILL] |",
     "| 12 | ADD §39 points 3-9 | 2026-11-01T04:55 (ruled); formal text [FILL-time] |"),
    ("E15b-13", S1R,
     "| 13 | ADD §40's readings (added) | [FILL] |",
     "| 13 | ADD §40's readings (added) | 2026-11-01T04:55 (ruled); formal text [FILL-time] |"),
    ("E15b-14", S1R,
     "| 14 | D-7, LN-31's draw built late (added; a report-only draw protocol, listed for completeness) | [FILL] |",
     "| 14 | D-7, LN-31's draw built late (added; a report-only draw protocol, listed for completeness) | "
     "2026-11-01T14:02 (ruled); formal text [FILL-time] |"),
    ("E15b-15", S1R,
     "| 15 | The reading-time readers' stated readings (added; track D1, §39 point 11) | [FILL] |",
     "| 15 | The reading-time readers' stated readings (added; track D1, §39 point 11) | "
     "2026-11-01T14:02 (ruled); formal text [FILL-time] |"),
    ("E15c", S1R,
     "formal text carries [FILL]. Both times come after every Gate B value above",
     "formal text carries [FILL-time]. Both times come after every Gate B value above"),
    ("E11c", S1R,
     "\"Added\" marks a rule this draft adds to the brief's list; the lead keeps or drops it.",
     "\"Added\" marks a rule this record adds to the brief's list; the lead keeps or drops it."),
]

# checks on the derived text (whitespace-collapsed; count of occurrences must equal the number given)
CHECKS = [
    ("E7", ADD, 'labelled as the reader prints it: "unscored counted Unsafe in every arm (not Gate B\'s adverse corner)" '
                "(V1A:363; the reader's `SYMMETRIC_LABEL`, pinned by its test, ACB:21-26", 1),
    ("E16", ADD, "today in the lead's scratch `builds/`", 0),
    ("E16", ADD, "lead-rulings-20261101.md` (SHA-256 `" + LR_SHA + "`)", 1),
    ("E7-code", ADD, "SYMMETRIC_LABEL", 1),
]
# the markers that must remain (the lead fills them at the records commit), per file: marker -> count
MARKERS = {
    ADD: {"[FILL-time]": 7, "[FILL-b14-full]": 1, "[FILL AT W1-P]": 1, "[FILL-hash]": 0, "[FILL]": 0, "[FILL:": 0},
    PLAN: {"[FILL": 0},
    SPF: {"[FILL": 0},
    S1R: {"[FILL-time]": 8, "[FILL]": 0, "[FILL-hash]": 0},
}


def derive(path):
    data = (ASSEMBLED / path).read_bytes()
    have = hashlib.sha256(data).hexdigest()
    if have != ASSEMBLED_SHA256[path]:
        print(f"REFUSED: {path}: assembled copy SHA-256 {have} is not the verified assembly's {ASSEMBLED_SHA256[path]}")
        sys.exit(2)
    text = data.decode("utf-8")
    orig = text
    for eid, f, old, new in EDITS:
        if f != path:
            continue
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: {eid} ({path}): find text found {n} times, not once")
            sys.exit(2)
        text = text.replace(old, new, 1)   # a replacement may contain its find text (E6, E12 insert around it)
    # line numbers for the README: the find text in the original assembled file, the replacement in the final text
    where = []
    for eid, f, old, new in EDITS:
        if f != path:
            continue
        before = orig[:orig.index(old)].count("\n") + 1 if orig.count(old) == 1 else 0
        after = text[:text.index(new)].count("\n") + 1 if text.count(new) == 1 else 0
        where.append((eid, before, old.count("\n") + 1, after, new.count("\n") + 1))
    collapsed = " ".join(text.split())
    for cid, f, phrase, count in CHECKS:
        if f != path:
            continue
        n = collapsed.count(" ".join(phrase.split()))
        if n != count:
            print(f"REFUSED: check {cid} ({path}): {phrase[:60]!r}... occurs {n} times, expected {count}")
            sys.exit(2)
    for marker, count in MARKERS[path].items():
        n = text.count(marker)
        if n != count:
            print(f"REFUSED: {path}: marker {marker!r} occurs {n} times, expected {count}")
            sys.exit(2)
    return text.encode("utf-8"), where


def first_difference(a, b):
    la, lb = a.split(b"\n"), b.split(b"\n")
    for i, (x, y) in enumerate(zip(la, lb), 1):
        if x != y:
            return i, x, y
    if len(la) != len(lb):
        i = min(len(la), len(lb)) + 1
        return i, (la[i - 1] if i <= len(la) else b"<end>"), (lb[i - 1] if i <= len(lb) else b"<end>")
    return None


def main(argv):
    write = "--write" in argv
    show_lines = "--lines" in argv
    failed = False
    for path in FILES:
        derived, where = derive(path)
        target = FINAL / path
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(derived)
        if show_lines:
            for eid, b, nb, a, na in where:
                print(f"  {eid:8s} {path.split('/')[-1]}: assembled line {b}" + (f"-{b + nb - 1}" if nb > 1 else "")
                      + f" -> final line {a}" + (f"-{a + na - 1}" if na > 1 else ""))
        if not target.exists():
            print(f"MISSING: {target}")
            failed = True
            continue
        have = target.read_bytes()
        if have == derived:
            n_lines = derived.count(b"\n")
            print(f"equal: {path} ({hashlib.sha256(derived).hexdigest()[:16]}…, {n_lines} lines)")
        else:
            d = first_difference(have, derived)
            print(f"DIFFERS: {path} at line {d[0]}")
            print(f"  final:   {d[1][:160]!r}")
            print(f"  derived: {d[2][:160]!r}")
            failed = True
    print("FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
