"""Classify hex tokens in a document against blob pools at two revisions.

Usage: python3 -I -B tok.py DOC POOL_NEW POOL_OLD OUT
Token forms: 64 hex (full) and 7-63 hex directly followed by the ellipsis character (prefix).
Output per distinct token: class, count, pool paths (new), pool paths (old), and line numbers.
"""
import collections
import re
import sys

doc, pnew, pold, out = sys.argv[1:5]


def load(p):
    d = collections.defaultdict(set)
    for line in open(p, encoding="utf-8"):
        h, path = line.rstrip("\n").split("\t", 1)
        if h != "SKIPPED":
            d[h].add(path)
    return d


new, old = load(pnew), load(pold)
text = open(doc, encoding="utf-8").read().split("\n")
pat = re.compile(r"(?<![0-9a-f])([0-9a-f]{64}|[0-9a-f]{7,63}(?=…))(?![0-9a-f])")
occ = collections.defaultdict(list)
for i, l in enumerate(text, 1):
    for m in pat.finditer(l):
        occ[m.group(1)].append(i)


def find(pool, t):
    if len(t) == 64:
        return sorted(pool.get(t, ()))
    r = set()
    for h, ps in pool.items():
        if h.startswith(t):
            r |= ps
    return sorted(r)


rows = []
for t, lines in sorted(occ.items(), key=lambda kv: kv[1][0]):
    pn, po = find(new, t), find(old, t)
    if pn and po:
        cls = "both"
    elif pn:
        cls = "new-only"
    elif po:
        cls = "OLD-ONLY"
    else:
        cls = "none"
    rows.append((cls, t, len(lines), pn, po, lines))
with open(out, "w", encoding="utf-8") as f:
    for cls, t, n, pn, po, lines in rows:
        f.write(f"{cls}\t{t}\t{n}\tlines={lines}\tnew={pn[:4]}\told={po[:4] if cls!='both' else '='}\n")
c = collections.Counter(r[0] for r in rows)
print(f"occurrences {sum(len(v) for v in occ.values())} distinct {len(occ)} classes {dict(c)}")
