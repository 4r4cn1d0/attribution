"""Check each AM1 change: old text found in Part 2 section 1 at c57e456 (count, line); new text contains old (where adding).

Usage: python3 -I oldnew.py AM1 F_BEFORE
"""
import re
import sys

am1 = open(sys.argv[1], encoding="utf-8").read().split("\n")
fb = open(sys.argv[2], encoding="utf-8").read().split("\n")
# section 1 = heading "## 1. The scorer section" to line before "## 2."
start = next(i for i, l in enumerate(fb) if l.startswith("## 1. The scorer section"))
end = next(i for i, l in enumerate(fb) if l.startswith("## 2. "))
s1 = fb[start:end]
s1text = "\n".join(s1)
print(f"section1 lines {start+1}-{end} ({end-start} lines)")

changes = []
cur = None
mode = None
buf = []
infence = False
for i, l in enumerate(am1):
    m = re.match(r"^### (\d+)\. (.*)$", l)
    if m:
        cur = {"n": int(m.group(1)), "title": m.group(2), "old": None, "new": None}
        changes.append(cur)
        continue
    if l.strip() == "**Old**":
        mode = "old"; continue
    if l.strip() == "**New**":
        mode = "new"; continue
    if l.startswith("```"):
        if not infence:
            infence = True; buf = []
        else:
            infence = False
            if cur is not None and mode in ("old", "new"):
                cur[mode] = "\n".join(buf)
            mode = None
        continue
    if infence:
        buf.append(l)

for c in changes:
    old = c["old"]
    m = re.search(r"line (\d+)", c["title"])
    named = int(m.group(1)) if m else None
    cnt = s1text.count(old)
    # which lines contain it (single-line olds)
    lines = [start + 1 + j for j, l in enumerate(s1) if old in l]
    cntfile = "\n".join(fb).count(old)
    added = old in c["new"]
    prefix = c["new"].startswith(old)
    print(f"change {c['n']:2d}: named line {named}; count in s1 {cnt}; count in whole file {cntfile}; at lines {lines}; "
          f"match_named={named in lines}; new contains old={added}; new starts with old={prefix}; multiline_old={chr(10) in old}")
