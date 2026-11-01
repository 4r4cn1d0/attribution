"""Independent scan of the four final record files against the assembled copies.

(1) numbering: the ordered sequence of numbered-list markers (e.g. '1.', '2b.', '## 39.') per file, assembled vs final;
(2) hygiene of every changed or added line: CR, tab, trailing whitespace, length (non-table lines > 120);
(3) the task's quoted texts, whitespace-collapsed, each found exactly once in the final file (and the old texts absent);
(4) per-file: changed-hunk count by difflib, so every hunk can be matched to one edit id in the report.
Reads only builds/assembled/repo and builds/final-records/repo. Writes nothing.
"""
import difflib
import re
import sys
from pathlib import Path

B = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/"
         "ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds")
A = B / "assembled" / "repo"
F = B / "final-records" / "repo"
ADD = ".ai/briefs/stage1-commitments-build-20261016-lead-decisions.md"
PLAN = ".ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md"
SPF = "docs/study-plan-full.md"
S1R = ".ai/inputs/stage1-post-w1-20261023/reading/s1-blinding-record-20261101.md"
FILES = [ADD, PLAN, SPF, S1R]

NUM = re.compile(r"^(\s*)((?:##\s+)?\d+[a-z]?\.)\s")        # '1.', '2b.', '10.', '## 39.'
ROW = re.compile(r"^\|\s*(\d+[a-z]?)\s*\|")                 # table rows '| 10 |', '| 1b |'


def markers(text):
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        m = NUM.match(line)
        if m:
            out.append((len(m.group(1)), m.group(2)))
            continue
        r = ROW.match(line)
        if r:
            out.append(("row", r.group(1)))
    return out


def collapse(s):
    return " ".join(s.split())


# the task's texts (E1-E16), as given in the brief; count expected in the FINAL file (whitespace-collapsed)
EXPECT = {
    ADD: [
        ("E1 path+hash", "committed at `.ai/inputs/stage1-post-w1-20261023/reading/lead-rulings-20261101.md` (SHA-256 "
                         "`3096e37a09ac565aab5b7fe0ad2d38e1871d28d181f664a40b6c09b2539c1586`)", 1),
        ("E2", "committed byte-equal under `.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/build-round/`, "
               "whose SHA256SUMS file lists every hash", 1),
        ("E3", "`coherent.py` `9f3010fb52ea6459`, `sg_coherent.py` `a0b001f7f40c1d2f`, `items.py` `70a52ca84d604b81`, "
               "`build.py` `e82214e718302563`, `__main__.py` `992787928667fe22`, `__init__.py` `3efbc49e298a64c8`, "
               "`mutants_reading_input.json` `52f231ed9c6d787f`; FOCUS records them at the records commit", 1),
        ("E4", "the 69-entry near set ran at 53f746d with the official runner: 68 killed and 1 invalid "
               "(B14S-s-p-role-primary-repinned: the module fixtures world and synth of test_b14_inputs.py raised at setup, "
               "61 errors). Commit c21dccb fixed the test file only (the fixtures return the failure text and each test reads "
               "them through need(), track A's pattern); that entry was then killed with 115 failures and 0 errors. The full "
               "150-entry spec ran at c21dccb: [FILL-b14-full].", 1),
        ("E5 worlds", "four plan-A contrast-worlds must also pass at 10,000 (i: P5, tail ratio 1.35; ii: P4, coverage 0.8915; "
                      "ii-low: P6, 0.9090; iii-prompt: P6, 0.9075)", 1),
        ("E5 51/51", "51 of 51 plan-A contrast-worlds", 1),
        ("E5 verify2", "`A-coherent-verify2.md` §3", 1),
        ("E6", "Status at the records commit: D-5 is verified after fix round 1 (the independent re-verify of 1 Nov, "
               "A-coherent-verify2.md); fallbacks (c+) and (c) are not used, unless the pre-run of the reading refuses on a "
               "coherent-only check (item 8).", 1),
        ("E7 label", "\"unscored counted Unsafe in every arm (not Gate B's adverse corner)\"", 1),
        ("E8", "rule b also reads the greedy harm and greedy over-refusal answers' categories", 1),
        ("E9", "or to LN-31's draw (step 5, D-7: report only, REV4:762; point 13 ruling 3)", 1),
        ("E10", "Points 12, 14 and 15 are records, not inference rules; point 13 (D-7) carries its own S1 line.", 1),
        ("E11a", "the drafter opened lines 282-287 and 306-308", 1),
        ("E11b", "marks a ruling this record adds to the brief's list", 1),
        ("E12 pod", "created at 14:11:56 UTC; its job started at 14:47:49 and was verified and stopped at 14:51:26 "
                    "(pod time 0.66 h, about $1.21; the pod is stopped, not deleted)", 1),
        ("E12 precheck", "(eval 200; 48 rows in each add set)", 1),
        ("E12 sim", "`811efe4a6d598df670d463fe343d389fed689883745363264e701a36cde4b997`", 1),
        ("E12 strata", "`2d996a99a49eed696c3ec047b4184b9ced7db60f29bd151d25e219b1142890f2`", 1),
        ("E12 inputs", "`91baaa5302a8f96c19ca6e568cb77f66a578ceb866a2236ac3f3f4d8a5144271`; 24 units", 1),
        ("E12 plan", "`b1965c74c4933059fc0123c5f7312cebc2084ba21b66de1a0115457a2ae4039e`), so `plan.json` must not change "
                     "before the reading", 1),
        ("E12 sealed", "were sealed in FOCUS at `b5e3c27`, before any add-arm outcome was read", 1),
        ("E12 folder", "`.ai/inputs/stage1-post-w1-20261023/reading/b14/`", 1),
        ("E12 kit34", "Kit round 34's 39 mutation ids: 39 killed, none unexpected.", 1),
        # old texts that must be gone
        ("old E1", "today in the lead's scratch `builds/`, to be committed", 0),
        ("old FILL-hash", "[FILL-hash]", 0),
        ("old E4", "[FILL: the 69-entry near set", 0),
        ("old E5", "at least one plan-A world must also pass", 0),
        ("old E8", "rule b also reads the greedy harm answers' categories", 0),
        ("old E9", "D-5's reader (step 4b) or to the reading-time readers (step 4c, point 11):", 0),
        ("old E11a", "I opened", 0),
        ("old E11b", "this draft", 0),
    ],
    PLAN: [
        ("E13a", "(62 entries; `cost_table` after its fix round)", 1),
        ("old E13a", "49 entries", 0),
        ("E13b", "Done at `b5e3c27` (1 Nov)", 1),
        ("E13c", "the strata (written and sealed at `b5e3c27`)", 1),
        ("E13d", "done at `b5e3c27`, about $1.21", 1),
        ("b5e3c27 count", "b5e3c27", 3),
    ],
    SPF: [
        ("E14a", "D-1 to D-7 are recorded deviations in ADD", 1),
        ("old E14a", "D-1 to D-4 are recorded deviations", 0),
        ("E14b", "(the lead's recorded rulings §1-§40)", 1),
        ("old E14b", "§1-§38", 0),
    ],
    S1R: [
        ("E15a", "- Pre-set fallback: the same list in the reading record's limits section; trigger: this record is not "
                 "committed when the records step starts (CRIT:352).", 1),
        ("E15b 04:55", "2026-11-01T04:55 (ruled); formal text [FILL-time]", 4),
        ("E15b 14:02", "2026-11-01T14:02 (ruled); formal text [FILL-time]", 2),
        ("E15c", "The formal text carries [FILL-time].", 1),
        ("E11c", "marks a rule this record adds to the brief's list", 1),
        ("old E11c", "this draft", 0),
        ("old [FILL]", "[FILL]", 0),
    ],
}


def main():
    ok = True
    for p in FILES:
        a = (A / p).read_bytes()
        f = (F / p).read_bytes()
        print(f"\n### {p}")
        # bytes-level hygiene of the whole final file
        cr, tabs = f.count(b"\r"), f.count(b"\t")
        one_nl_f = f.endswith(b"\n") and not f.endswith(b"\n\n")
        one_nl_a = a.endswith(b"\n") and not a.endswith(b"\n\n")
        print(f"  final bytes {len(f)}; CR bytes {cr}; tabs {tabs}; ends with one newline: {one_nl_f}; "
              f"assembled ends same way: {one_nl_a}")
        at, ft = a.decode("utf-8"), f.decode("utf-8")
        # (1) numbering
        ma, mf = markers(at), markers(ft)
        print(f"  numbered markers: assembled {len(ma)}, final {len(mf)}, identical sequence: {ma == mf}")
        if ma != mf:
            ok = False
            for i, (x, y) in enumerate(zip(ma, mf)):
                if x != y:
                    print(f"    first difference at marker #{i}: {x} vs {y}")
                    break
        # (2) hygiene of changed/added lines; (4) hunks
        al, fl = at.split("\n"), ft.split("\n")
        sm = difflib.SequenceMatcher(None, al, fl, autojunk=False)
        hunks = [op for op in sm.get_opcodes() if op[0] != "equal"]
        print(f"  changed hunks (difflib): {len(hunks)}")
        for tag, i1, i2, j1, j2 in hunks:
            print(f"    {tag:7s} assembled {i1 + 1}-{i2} -> final {j1 + 1}-{j2}")
            for k in range(j1, j2):
                line = fl[k]
                bad = []
                if line != line.rstrip():
                    bad.append("trailing whitespace")
                if "\t" in line:
                    bad.append("tab")
                if len(line) > 120 and not line.startswith("|"):
                    bad.append(f"length {len(line)}")
                if bad:
                    ok = False
                    print(f"      line {k + 1}: {', '.join(bad)}")
        # (3) task texts
        cf = collapse(ft)
        ca = collapse(at)
        for name, phrase, want in EXPECT[p]:
            n = cf.count(collapse(phrase))
            flag = "ok " if n == want else "BAD"
            if n != want:
                ok = False
            print(f"  [{flag}] {name}: {n} (expected {want}; in assembled: {ca.count(collapse(phrase))})")
    print("\nSCAN", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
