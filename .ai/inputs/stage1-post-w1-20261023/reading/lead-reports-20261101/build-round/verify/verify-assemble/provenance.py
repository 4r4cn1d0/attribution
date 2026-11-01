#!/usr/bin/env python3
"""Independent provenance check of the assembled files (verifier's own code, not check_assembly.py).

For each target: every line that is not HEAD's must be a line of a verified draft (after removing the 3-space
nesting prefix where the assembly nests a draft section), or one of the builder's stated edits. Prints every
added line that is NOT found verbatim in any draft, so the verifier can compare that list with README's edits.
Also prints, per draft, the draft lines that do NOT appear in the assembled output (to see what was dropped).
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = "/Users/spiderishi/Coding/attribution"
B = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/"
         "ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds")
A = B / "assembled" / "repo"
R = B / "reports"

ADD = ".ai/briefs/stage1-commitments-build-20261016-lead-decisions.md"
PLAN = ".ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md"
SPF = "docs/study-plan-full.md"
S1 = ".ai/inputs/stage1-post-w1-20261023/reading/s1-blinding-record-20261101.md"


def head(path):
    return subprocess.run(["git", "-C", REPO, "show", f"HEAD:{path}"], capture_output=True, check=True).stdout.decode()


drafts = {n: (R / n).read_text().split("\n") for n in
          ["E-D5-D6.md", "E-39.md", "E-misc.md", "E-40.md", "E-S1-blinding.md", "E-plan-updates.md"]}
draft_lines = {}
for n, ls in drafts.items():
    for l in ls:
        draft_lines.setdefault(l, set()).add(n)


def denest(l):
    return l[3:] if l.startswith("   ") else l


# ---- ADD
h = head(ADD).split("\n")
a = (A / ADD).read_text().split("\n")
assert a[:len(h) - 1] == h[:-1], "ADD: HEAD's lines are not a prefix of the assembled file"
print(f"ADD: HEAD prefix of {len(h) - 1} lines intact; appended {len(a) - len(h)} lines")
added = a[len(h) - 1:]
not_found = []
for i, l in enumerate(added, start=len(h)):
    if l == "":
        continue
    cands = [l, denest(l)]
    if not any(c in draft_lines for c in cands):
        not_found.append((i, l))
print(f"ADD: {len(not_found)} appended non-blank lines not found verbatim (or de-nested) in any draft:")
for i, l in not_found:
    print(f"  {i}: {l[:170]}")

# ---- S1 record
s = (A / S1).read_text().split("\n")
nf = [(i + 1, l) for i, l in enumerate(s) if l and l not in draft_lines]
print(f"\nS1: {len(nf)} lines not found verbatim in any draft:")
for i, l in nf:
    print(f"  {i}: {l[:170]}")

# ---- PLAN
hp = head(PLAN)
p = (A / PLAN).read_text()
upd = (R / "E-plan-updates.md").read_text()
olds = re.findall(r"\nOld:\n```\n(.*?)\n```\n", upd, flags=re.S)
news = re.findall(r"\nNew:\n```\n(.*?)\n```\n", upd, flags=re.S)
print(f"\nPLAN: {len(olds)} Old, {len(news)} New blocks in the draft")
for k, old in enumerate(olds, 1):
    c = hp.count(old)
    print(f"  Old {k}: occurs {c} time(s) in the plan at HEAD; New {k} occurs {p.count(news[k-1])} time(s) in the copy; "
          f"Old {k} occurs {p.count(old)} time(s) in the copy")
# every line of the copy is either a HEAD line, a New-block line, or the revision line
new_lines = set(l for n in news for l in n.split("\n"))
head_lines = set(hp.split("\n"))
rev = "Revised 1 November 2026 by addendum §39 and §40; the 31 October text is in git at `55d5f8b`."
extra = [(i + 1, l) for i, l in enumerate(p.split("\n")) if l and l not in head_lines and l not in new_lines and l != rev]
print(f"PLAN: {len(extra)} lines in the copy that are neither HEAD's, a New block's nor the revision line:")
for i, l in extra:
    print(f"  {i}: {l[:170]}")
# every Old-block line must be gone from the copy unless it also occurs in a New block
old_lines = set(l for o in olds for l in o.split("\n")) - new_lines
left = [l for l in p.split("\n") if l in old_lines]
print(f"PLAN: Old-block lines still present in the copy (not also in a New block): {len(left)}")
# pairing check: each Old is immediately followed (in the draft) by its New
pairs = re.findall(r"\nOld:\n```\n(.*?)\n```\nNew:\n```\n(.*?)\n```\n", upd, flags=re.S)
print(f"PLAN: Old/New adjacent pairs in the draft: {len(pairs)}; in-order zip equals adjacent pairs: "
      f"{[ (o, n) for o, n in zip(olds, news)] == pairs}")

# ---- SPF
hs = head(SPF).split("\n")
ss = (A / SPF).read_text().split("\n")
diff = [(i + 1, x, y) for i, (x, y) in enumerate(zip(hs, ss)) if x != y]
print(f"\nSPF: {len(hs)} lines at HEAD, {len(ss)} in the copy; differing lines: {[d[0] for d in diff]}")

# ---- what of each draft is NOT in the assembled outputs (dropped lines)
out_lines = set(a) | set(denest(l) for l in a) | set(s) | set(p.split("\n"))
print("\nDraft lines absent from every assembled output (should be draft-only lines or stated edits):")
for n, ls in drafts.items():
    if n == "E-plan-updates.md":
        continue
    miss = [(i + 1, l) for i, l in enumerate(ls) if l and l != "---" and l not in out_lines]
    print(f"  {n}: {len(miss)} lines")
    for i, l in miss:
        print(f"    {i}: {l[:150]}")
