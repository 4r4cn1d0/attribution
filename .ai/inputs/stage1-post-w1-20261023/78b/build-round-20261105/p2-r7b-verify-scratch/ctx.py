"""ctx.py FILE FROM TO WIDTH PATTERN...: print each match with context (lines FROM..TO, 1-based)."""
import re, sys
f, a, b, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
L = open(f, encoding="utf-8").read().split("\n")
pat = re.compile("|".join(sys.argv[5:]))
for i in range(a - 1, min(b, len(L))):
    for m in pat.finditer(L[i]):
        s = max(0, m.start() - w); e = min(len(L[i]), m.end() + w)
        print(f"{i+1}: [{m.group(0)}] ...{L[i][s:e]}...")
