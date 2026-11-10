"""Match every hex token of a text against a hash pool (prints tokens, paths, line numbers; no file content).

Usage: python -I -B vtok.py TEXT POOL.tsv OUTDIR
Writes OUTDIR/matched.tsv (line, token, candidate paths, name_on_line flag) and OUTDIR/unmatched.tsv.
"""
import os
import re
import sys

text, pool, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
hashes = []
for line in open(pool):
    h, p = line.rstrip("\n").split("\t", 1)
    hashes.append((h, p))
TOK = re.compile(r"(?<![0-9a-zA-Z])([0-9a-f]{7,64})(?![0-9a-zA-Z])")
lines = open(text, encoding="utf-8").read().split("\n")
matched, unmatched = [], []
seen = set()
for n, line in enumerate(lines, 1):
    for m in TOK.finditer(line):
        tok = m.group(1)
        if not re.search(r"[a-f]", tok) and len(tok) < 16:
            continue  # plain numbers
        seen.add(tok)
        cands = [p for h, p in hashes if h.startswith(tok)]
        if cands:
            before = line[max(0, m.start() - 400):m.start()]
            names = {c.rsplit("/", 1)[-1] for c in cands}
            stems = {x.rsplit(".", 1)[0] for x in names}
            ok = any(x in before for x in names) or any(s in before for s in stems if len(s) > 3)
            matched.append((n, tok, ";".join(sorted(set(cands)))[:600], "name" if ok else "CHECK"))
        else:
            unmatched.append((n, tok))
with open(os.path.join(outdir, "matched.tsv"), "w") as fh:
    for r in matched:
        fh.write("\t".join(map(str, r)) + "\n")
with open(os.path.join(outdir, "unmatched.tsv"), "w") as fh:
    for r in unmatched:
        fh.write("\t".join(map(str, r)) + "\n")
print(f"tokens {len(matched) + len(unmatched)} distinct {len(seen)} matched {len(matched)} "
      f"unmatched {len(unmatched)} check {sum(1 for r in matched if r[3] == 'CHECK')}")
