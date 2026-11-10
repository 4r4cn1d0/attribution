"""Path-aware check of Part 2's tables A-D: each row's file path -> its hash list entry. Prints counts and bad rows."""
import re, sys
part2, *lists = sys.argv[1:]
h = {}
for f in lists:
    for line in open(f, encoding="utf-8"):
        p = line.split(None, 1)
        if len(p) == 2:
            h[p[1].strip()] = p[0]
t = open(part2, encoding="utf-8").read()
a = t.index("**Table A."); b = t.index("**Table B."); c = t.index("**Table C."); d = t.index("**Table D."); e = t.index("### 1.18")
ok = bad = 0
def rows(sec):
    for m in re.finditer(r"^\| `([^`]+)`[^|]*\| `([0-9a-f]{64})` \|$", sec, re.M):
        yield m.group(1), m.group(2)
for name, sec, prefix in (("A", t[a:b], "scripts/scale78b/"), ("B", t[b:c], ""), ("C", t[c:d], "scripts/stage1/settings/"), ("D", t[d:e], "")):
    for path, sha in rows(sec):
        full = path if path.startswith(("scripts/", "runkit/", ".ai/")) else prefix + path
        got = h.get(full)
        if got == sha:
            ok += 1
        else:
            bad += 1
            print(f"BAD {name} {full} part2={sha[:12]} measured={got[:12] if got else None}")
print(f"rows ok {ok}, bad {bad}")
