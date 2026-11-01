#!/usr/bin/env python3
"""Re-derive the assembled record files from the main checkout's HEAD and the verified E-track drafts, and confirm
byte equality with the copies under assembled/repo/ (exit 0), or print the first difference (exit 1).

    python -B check_assembly.py            # check: re-derive and compare with assembled/repo/
    python -B check_assembly.py --write    # the one-time assembly: write assembled/repo/ (and compare again)

Inputs: `git -C <main checkout> show HEAD:<path>` for the three target files (read-only git), and the six drafts in
builds/reports/ (pinned by SHA-256 below; a changed draft makes the script refuse). A plan "Old" block that does not
occur exactly once in the plan makes the script refuse (exit 2). Nothing on the never-open list is opened.

The derivation is the assembly rule, stated once here; README.md lists every edit it makes.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/spiderishi/Coding/attribution")
BUILDS = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/verify-assemble/ft")
REPORTS = BUILDS / "reports"
OUT = BUILDS / "assembled" / "repo"

ADD_PATH = ".ai/briefs/stage1-commitments-build-20261016-lead-decisions.md"
PLAN_PATH = ".ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md"
SPF_PATH = "docs/study-plan-full.md"
S1_PATH = ".ai/inputs/stage1-post-w1-20261023/reading/s1-blinding-record-20261101.md"

# The verified drafts (fix round 2; E-records-verify3.md "Checked" line), full SHA-256.
DRAFTS = {
    "E-D5-D6.md": "418c2372a56d90d517e9953326657ebbe2d6938f66f3bf1e678622373b23cc0b",
    "E-39.md": "c659161c85b3020a8707d67bb1e82c0d1b35eac7fe0d7cf5196ade70c3a86e64",
    "E-misc.md": "da538abaa80eda1c578285467432732974ed1eebafbf4ad25ca600153265a891",
    "E-40.md": "26fd943d20ff408f60861e82b221e41b12f572371e673fee17c83fd7d09ab97e",
    "E-S1-blinding.md": "8128cac6c45448b48b5a3e68b55da63d03fae334dc2091351fc3db0ed7b4ba39",
    "E-plan-updates.md": "13c52b0057684ca22ca19114178cf35387c99b9aaa1d68cb867d3faf966f7d74",
}
# The targets at the HEAD the assembly started from (53f746d); a different hash is reported, not refused.
HEAD_EXPECTED = {
    ADD_PATH: "f5a7c6bdb404f429bf512ff716d094cd61032c0fbaab1343a3b0185cba4f46c9",
    PLAN_PATH: "121c5119d12e5baed79ffa2c87b1389cb97fdc3074b1cde3f5abc25131c25de1",
    SPF_PATH: "8aedcd4eee80953cd2501b810faab47b2a031ef615978fe5a0c397b79b61df75",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(msg: str, code: int = 2) -> None:
    print(f"REFUSED: {msg}")
    sys.exit(code)


def git_show(path: str) -> bytes:
    r = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{path}"], capture_output=True)
    if r.returncode != 0:
        fail(f"git show HEAD:{path} failed: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


def read_draft(name: str) -> str:
    data = (REPORTS / name).read_bytes()
    if sha(data) != DRAFTS[name]:
        fail(f"{name}: SHA-256 {sha(data)} is not the verified draft's {DRAFTS[name]}")
    return data.decode("utf-8")


def replace_once(text: str, old: str, new: str, where: str) -> str:
    n = text.count(old)
    if n != 1:
        fail(f"{where}: expected exactly one occurrence of {old[:70]!r}, found {n}")
    return text.replace(old, new)


def index_of(lines, prefix: str, where: str) -> int:
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(hits) != 1:
        fail(f"{where}: expected exactly one line starting with {prefix[:60]!r}, found {len(hits)}")
    return hits[0]


def strip_blank(lines):
    a, b = 0, len(lines)
    while a < b and lines[a] == "":
        a += 1
    while b > a and lines[b - 1] == "":
        b -= 1
    return lines[a:b]


def nest(lines, indent="   "):
    return [indent + l if l else "" for l in lines]


def as_point(number: int, title: str, body):
    """A numbered addendum point whose body (a draft section) is nested under it."""
    return [f"{number}. **{title}.**", ""] + nest(strip_blank(body))


def draft_section(lines, heading_prefix: str, where: str):
    """The body of a draft '## X.' section: from its heading to the next '---' separator or the end."""
    h = index_of(lines, heading_prefix, where)
    end = len(lines)
    for i in range(h + 1, len(lines)):
        if lines[i] == "---" or lines[i].startswith("## "):
            end = i
            break
    title = lines[h][len("## "):]
    title = re.sub(r"^[A-Z0-9]+\. ", "", title)   # drop the draft's own "1. " / "A. " label
    return title, strip_blank(lines[h + 1:end])


# ---------------------------------------------------------------- §39: D-5, D-6 (E-D5-D6.md) and E-39.md's points
def build_39():
    d = read_draft("E-D5-D6.md").split("\n")
    e = read_draft("E-39.md").split("\n")
    m = read_draft("E-misc.md").split("\n")

    # Heading: the draft's "2026-11-01T[FILL] UTC" becomes the "[FILL-time]" marker (the task's heading style).
    h = index_of(e, "## 39. Before the stage-1 reading", "E-39 heading")
    heading = replace_once(e[h], "(2026-11-01T[FILL] UTC; decided", "([FILL-time]; decided", "E-39 heading")
    if not (e[h + 1] == "" and e[h + 2].startswith("Before the one-time reading") and e[h + 5] == ""):
        fail("E-39: the intro paragraph is not where expected")
    intro = e[h + 2:h + 5]

    # The Scope bullet: the one sentence that names the draft files is replaced; the rest is verbatim, re-wrapped.
    scope_old = [
        "- **Scope.** Every stated reading that CRIT §2.1 lists (CRIT:125-148; its decision 10, CRIT:354). Points 1 and 2 are",
        "  D-5 and D-6, drafted in `E-D5-D6.md`; this file holds points 3-11. Each point quotes the stated reading, then",
        "  gives the ruling. The default is to adopt the stated reading; no report shows any of them wrong.",
    ]
    s = index_of(e, "- **Scope.**", "E-39 scope")
    if e[s:s + 3] != scope_old:
        fail("E-39: the Scope bullet is not the expected text")
    scope_new = [
        "- **Scope.** Every stated reading that CRIT §2.1 lists (CRIT:125-148; its decision 10, CRIT:354). Points 1 and 2 are",
        "  D-5 and D-6; points 3-11 the stated readings; points 12-15 B14's scheduling gap, D-7, ADD:428's simulations and the",
        "  build round's hard-rule notes. Each point quotes the stated reading, then gives the ruling. The default is to adopt",
        "  the stated reading; no report shows any of them wrong.",
    ]

    # The citation header: E-D5-D6's, without its snapshot of HEAD `a494ff7` (verifier note 5), re-wrapped.
    cit_old = [
        "- **Citations** are `path:line` at commit `55d5f8b` (`git show 55d5f8b:<path>`). FOCUS lines are 55d5f8b's: the",
        "  anchored-stamp entry added one line at FOCUS:74, so every FOCUS line from 74 on is one higher than at `0daca9a`",
        "  (and two lower than at HEAD `a494ff7`; the `55d5f8b` pin stays in every citation header, no remap: LR R6.5). The",
        "  design round's reports are cited by line in their committed copies (table below), byte-equal to the scratch copies",
        "  the round wrote, so their line numbers are unchanged.",
    ]
    c = index_of(d, "- **Citations** are `path:line` at commit `55d5f8b` (`git show", "E-D5-D6 citations")
    if d[c:c + 5] != cit_old:
        fail("E-D5-D6: the Citations bullet is not the expected text")
    cit_new = [
        "- **Citations** are `path:line` at commit `55d5f8b` (`git show 55d5f8b:<path>`). FOCUS lines are 55d5f8b's: the",
        "  anchored-stamp entry added one line at FOCUS:74, so every FOCUS line from 74 on is one higher than at `0daca9a`",
        "  (the `55d5f8b` pin stays in every citation header, no remap: LR R6.5). The design round's reports are cited by line",
        "  in their committed copies (table below), byte-equal to the scratch copies the round wrote, so their line numbers",
        "  are unchanged.",
    ]

    # The merged short-name table: E-D5-D6's rows, then E-39's rows that add names, then E-misc's prose definitions.
    t = index_of(d, "| Short name | Path |", "E-D5-D6 table")
    if d[t + 1] != "|---|---|":
        fail("E-D5-D6: table separator missing")
    rows = []
    i = t + 2
    while i < len(d) and d[i].startswith("| "):
        rows.append(d[i])
        i += 1
    if len(rows) != 12:
        fail(f"E-D5-D6: expected 12 table rows, found {len(rows)}")
    for prefix in ("| FOCUS, PLAN, KW, LEDGER |", "| RIB, HBB, B16H |", "| OTSC |"):
        rows.append(e[index_of(e, prefix, "E-39 table")])
    misc_cit = " ".join(l.strip() for l in m[index_of(m, "- **Citations** are", "E-misc citations"):
                                                index_of(m, "- **Fix round 2**", "E-misc fix round")])
    misc_rows = [
        "| PLANS | `research/review/2026-10-08-sharpened-direction-DRAFT.md` |",
        "| RULES | `runkit/stage1-olmo/stage1_rules.py` |",
        "| SIM | `scripts/stage1_s1/overlap_similarity.py` |",
        "| HLC | `research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md` |",
        "| NOTES | `/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/claude-workspaces/"
        "stage1-integrate-20261017/notes/` (git-ignored; cited by path, SHA-256 and line; the lead commits copies of "
        "the two cited files with the records, LR R6.5) |",
    ]
    for r in misc_rows:   # each row's path and note come from E-misc's Citations bullet
        name, path = r.split(" | ")[0][2:], r.split(" | ")[1][:-2]
        if f"{name} = {path.split('` (')[0]}`" not in misc_cit and f"{name} = {path}" not in misc_cit:
            fail(f"E-misc: the definition of {name} is not in its Citations bullet as expected")
    if "(git-ignored; cited by path, SHA-256 and line; the lead commits copies of the two cited files with the records, LR R6.5)" not in misc_cit:
        fail("E-misc: the NOTES note is not in its Citations bullet as expected")
    rows += misc_rows
    table = ["| Short name | Path |", "|---|---|"] + rows

    # Points 1 and 2: the D-5 and D-6 sections, nested under numbered points.
    title1, body1 = draft_section(d, "## 1. Post-W1 deviation D-5:", "E-D5-D6 §1")
    title2, body2 = draft_section(d, "## 2. Post-W1 deviation D-6:", "E-D5-D6 §2")
    p1 = as_point(1, title1, body1)
    p2 = as_point(2, title2, body2)

    # Points 3-11 verbatim, with two cross-references to draft files converted.
    a = index_of(e, "1. **Post-W1 deviation D-5** (RI-O2, S-G's coherent-only U): the text of `E-D5-D6.md` §1.", "E-39 p1")
    if not e[a + 1].startswith("2. **Post-W1 deviation D-6** (B14's report accepts recipe-S units): the text of `E-D5-D6.md` §2."):
        fail("E-39: point 2's pointer line is not where expected")
    b = index_of(e, "3. **The input builder's open points**", "E-39 p3")
    s1 = index_of(e, "**S1 blinding line (REV4:919; W1R:358).** Written [FILL-time], after the W1 commit (FOCUS:144)", "E-39 S1")
    pts = "\n".join(strip_blank(e[b:s1]))
    pts = replace_once(pts, "Adopted: the only wording is D-6's fallback text (`E-D5-D6.md` §2). The",
                       "Adopted: the only wording is D-6's fallback text (point 2). The", "E-39 point 7")
    pts = replace_once(pts, "`grep -r` over the lead's notes folder) are recorded in `E-misc.md` D (LR R3.5, R6.4, R6.6).",
                       "`grep -r` over the lead's notes folder) are recorded in point 15 (LR R3.5, R6.4, R6.6).", "E-39 point 8(g)")
    p3_11 = pts.split("\n")
    s1_line = strip_blank(e[s1:])

    # Points 12-15: E-misc's A (the B14 route), B (D-7), C (ADD:428) and D (the hard-rule notes).
    tA, bA = draft_section(m, "## A. B14's similarity pass", "E-misc A")
    tB, bB = draft_section(m, "## B. Post-W1 deviation D-7", "E-misc B")
    tC, bC = draft_section(m, "## C. ADD:428", "E-misc C")
    tD, bD = draft_section(m, "## D. The build round's hard-rule notes", "E-misc D")
    bD = replace_once("\n".join(bD), "(part C above)", "(point 14 above)", "E-misc D.3").split("\n")
    p12, p13, p14, p15 = as_point(12, tA, bA), as_point(13, tB, bB), as_point(14, tC, bC), as_point(15, tD, bD)

    sec = [heading, ""] + intro + [""] + scope_new + cit_new + [""] + table + [""]
    for block in (p1, p2, p3_11, p12, p13, p14, p15, s1_line):
        sec += block + [""]
    return sec[:-1]


# ---------------------------------------------------------------- §40 (E-40.md)
def build_40():
    e = read_draft("E-40.md").split("\n")
    h = index_of(e, "## 40. Stage 1b before any pilot unit exists", "E-40 heading")
    heading = replace_once(e[h], "(2026-11-01T[FILL] UTC; decided", "([FILL-time]; decided", "E-40 heading")
    if not (e[h + 1] == "" and e[h + 2].startswith("Stage 1b's design is frozen") and e[h + 6] == ""):
        fail("E-40: the intro paragraph is not where expected")
    intro = e[h + 2:h + 6]
    s = index_of(e, "- **Sources.**", "E-40 sources")
    added = index_of(e, '- "Added" marks a ruling this draft adds', "E-40 added note")
    bullets = "\n".join(e[s:added + 1])
    bullets = replace_once(bullets, "and EV2 = `E-records-verify2.md`, as in `E-D5-D6.md`'s table.",
                           "and EV2 = `E-records-verify2.md`, as in §39's table.", "E-40 sources")
    bullets = replace_once(bullets, "short names as in `E-D5-D6.md`, plus RULES =",
                           "short names as in §39's table, plus RULES =", "E-40 citations")
    body = "\n".join(strip_blank(e[h + 7:]))
    body = replace_once(body, "(no stage-1 outcome in it; `E-misc.md` A ruling 3, LR R3.1)",
                        "(no stage-1 outcome in it; §39 point 12 ruling 3, LR R3.1)", "E-40 point 3")
    return [heading, ""] + intro + [""] + bullets.split("\n") + [""] + body.split("\n")


# ---------------------------------------------------------------- the S1 blinding record (E-S1-blinding.md)
def build_s1():
    e = read_draft("E-S1-blinding.md").split("\n")
    if e[0] != "# Draft: the S1 blinding record (REV4:919; W1R:358)" or e[1] != "":
        fail("E-S1-blinding: title not as expected")
    s = index_of(e, "- **Status.**", "E-S1 status")
    c = index_of(e, "- **Citations** are `path:line` at commit `55d5f8b`; short names as in `E-D5-D6.md`.", "E-S1 citations")
    f = index_of(e, "- **Line numbers of FOCUS.**", "E-S1 FOCUS lines")
    if not (s == 2 and c == s + 5 and f == c + 1 and e[f + 7] == "" and e[f + 8] == "## 1. The rule"):
        fail("E-S1-blinding: the header bullets are not where expected")
    focus_old = [
        "- **Line numbers of FOCUS.** The brief names FOCUS:134, :137 and :139. Those are the line numbers at `0daca9a`.",
        "  Commit `55d5f8b` added one entry at FOCUS:74 (the anchored stamp), so at `55d5f8b` the same entries are",
        "  **FOCUS:135 (final measurements), :138 (the verdict) and :140 (wave 1)**; the W1 commit is FOCUS:144. At `55d5f8b`,",
        "  FOCUS:134 is the user's funding-event definition, :137 the `--final` refusal and :139 the wave-2 launch (checked with",
        "  `git show 55d5f8b:research/FOCUS.md`). At HEAD `a494ff7` every FOCUS line from 74 on is two higher; the `55d5f8b`",
        "  pin stays in every citation header, with no remap (LR R6.5). LR and the build round's reports are as in",
        "  `E-D5-D6.md`'s table.",
    ]
    if e[f:f + 7] != focus_old:
        fail("E-S1-blinding: the FOCUS-lines bullet is not the expected text")
    header = [
        "# The S1 blinding record (REV4:919; W1R:358)",
        "",
        "- **Written** [FILL-time] by the lead (GI VIII), before any stage-1 outcome is read; committed by explicit path and",
        "  named in the second stamp's manifest.",
        "- **Citations** are `path:line` at commit `55d5f8b`; short names as in addendum §39's table",
        "  (`.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md`).",
        "- **Line numbers of FOCUS.** At `0daca9a` the final measurements, the verdict and wave 1 were FOCUS:134, :137 and :139.",
        "  Commit `55d5f8b` added one entry at FOCUS:74 (the anchored stamp), so at `55d5f8b` the same entries are",
        "  **FOCUS:135 (final measurements), :138 (the verdict) and :140 (wave 1)**; the W1 commit is FOCUS:144. At `55d5f8b`,",
        "  FOCUS:134 is the user's funding-event definition, :137 the `--final` refusal and :139 the wave-2 launch (checked with",
        "  `git show 55d5f8b:research/FOCUS.md`). The `55d5f8b` pin stays in every citation header, with no remap (LR R6.5).",
        "  LR and the build round's reports are as in addendum §39's table.",
    ]
    body = "\n".join(e[f + 7:])
    body = replace_once(body, "the stated readings of `E-39.md` (point 11's readings are row 15)",
                        "the stated readings of addendum §39 (point 11's readings are row 15)", "E-S1 row 12")
    body = replace_once(body, "(LR R5; `E-misc.md` B)", "(LR R5; addendum §39 point 13)", "E-S1 row 14")
    return "\n".join(header) + "\n" + body


# ---------------------------------------------------------------- the three targets
def derive_add():
    add = git_show(ADD_PATH).decode("utf-8")
    if not add.endswith(".\n") or add.endswith("\n\n"):
        fail("ADD at HEAD does not end with a single newline after its last sentence")
    lines = add.split("\n")   # the last element is "" (the final newline)
    if not lines[-2].startswith("6. **The user's second decision (2026-10-30T10:52 UTC"):
        fail("ADD at HEAD: §38 point 6 is not the last line; the append point moved")
    if any(l.startswith("## 39.") or l.startswith("## 40.") for l in lines):
        fail("ADD at HEAD already holds §39 or §40")
    out = lines[:-1] + [""] + build_39() + [""] + build_40() + [""]
    return "\n".join(out)


def derive_plan():
    plan = git_show(PLAN_PATH).decode("utf-8")
    upd = read_draft("E-plan-updates.md")
    olds = re.findall(r"\nOld:\n```\n(.*?)\n```\n", upd, flags=re.S)
    news = re.findall(r"\nNew:\n```\n(.*?)\n```\n", upd, flags=re.S)
    if len(olds) != 14 or len(news) != 14:
        fail(f"E-plan-updates: expected 14 Old and 14 New blocks, found {len(olds)} and {len(news)}")
    for k, (old, new) in enumerate(zip(olds, news), 1):
        n = plan.count(old)
        if n != 1:
            fail(f"plan Old block {k} occurs {n} times in the plan at HEAD (must be exactly once):\n{old[:200]}")
        plan = plan.replace(old, new)
    lines = plan.split("\n")
    if lines[0] != "# What comes after stage-1 block B (the lead's plan, 31 October 2026)" or lines[1] != "":
        fail("plan: the title is not as expected")
    rev = "Revised 1 November 2026 by addendum §39 and §40; the 31 October text is in git at `55d5f8b`."
    if f'"{rev}"' not in " ".join(upd.split()):   # the bullet wraps the quoted sentence across two lines
        fail("E-plan-updates: the revision line is not the one its 'How to apply' bullet states")
    return "\n".join([lines[0], "", rev, ""] + lines[2:])


SPF_OLD = ("- Recorded post-W1 deviations: D-1 (the S3 subset size), D-2 (pool pins filled after W1; the plant and decoy pools "
           "are pinned in a separate hash-pinned pool-pins file, MSG-03), D-3 (S3's scorer in one pass), D-4 (REML by "
           "multi-start), and the ADD §38 restart-to-pull deviation (§4.10) [ADD:446-648].")


def derive_spf(add_text: str):
    spf = git_show(SPF_PATH).decode("utf-8")
    lines = spf.split("\n")
    if lines[343] != SPF_OLD:
        fail("SPF at HEAD: line 344 is not the deviations line expected")
    add_lines = add_text.split("\n")
    s = index_of(add_lines, "## 39. ", "assembled ADD") + 1          # 1-based line of the §39 heading
    e40 = index_of(add_lines, "## 40. ", "assembled ADD")             # 0-based index of the §40 heading
    end = e40                                                          # 1-based line of the last line of §39 ...
    while add_lines[end - 1] == "":                                    # ... skipping the blank line before §40
        end -= 1
    new = ("- Recorded post-W1 deviations: D-1 (the S3 subset size), D-2 (pool pins filled after W1; the plant and decoy "
           "pools are pinned in a separate hash-pinned pool-pins file, MSG-03), D-3 (S3's scorer in one pass), D-4 (REML "
           "by multi-start), D-5 (S-G's coherent-only U by a linearized prompt table, read beside B16), D-6 (B14's report "
           "accepts recipe-S units, a settings-only re-pin), D-7 (LN-31's draw built after its deadline, before any "
           "stage-1 outcome was read), and the ADD §38 restart-to-pull deviation (§4.10) "
           f"[ADD:446-648, ADD:{s}-{end}].")
    lines[343] = new
    return "\n".join(lines)


def main():
    write = "--write" in sys.argv[1:]
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    print(f"main checkout HEAD: {head}")
    for p, h in HEAD_EXPECTED.items():
        got = sha(git_show(p))
        print(f"  HEAD:{p}: {got}" + ("" if got == h else f"  (NOTE: differs from the assembly's start {h})"))
    add = derive_add()
    derived = {
        ADD_PATH: add,
        PLAN_PATH: derive_plan(),
        SPF_PATH: derive_spf(add),
        S1_PATH: build_s1(),
    }
    rc = 0
    for path, text in derived.items():
        data = text.encode("utf-8")
        target = OUT / path
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            print(f"wrote {target} ({len(data)} bytes, SHA-256 {sha(data)})")
        if not target.exists():
            print(f"MISSING: {target}")
            rc = 1
            continue
        have = target.read_bytes()
        if have == data:
            print(f"equal: {path} (SHA-256 {sha(data)})")
        else:
            rc = 1
            a, b = have.decode("utf-8", "replace").split("\n"), text.split("\n")
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else "<no line>"
                y = b[i] if i < len(b) else "<no line>"
                if x != y:
                    print(f"DIFFERS: {path} at line {i + 1}\n  on disk:  {x[:160]}\n  derived:  {y[:160]}")
                    break
    print("PASS" if rc == 0 else "FAIL")
    sys.exit(rc)


if __name__ == "__main__":
    main()
