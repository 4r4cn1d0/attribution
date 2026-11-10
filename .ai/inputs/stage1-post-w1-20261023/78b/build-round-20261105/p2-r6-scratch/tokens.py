"""Hex tokens of a text against a hash pool. Prints line, token, match count and the nearest named file check."""
import re, sys, os
text, pool = sys.argv[1], sys.argv[2]
rows = [l.rstrip("\n").split("\t") for l in open(pool)]
lines = open(text).read().splitlines()
tok_re = re.compile(r"(?<![0-9a-zA-Z])([0-9a-f]{8,64})(?:…)?(?![0-9a-zA-Z])")
total = matched = 0
unmatched, flagged = [], []
for n, line in enumerate(lines, 1):
    for m in tok_re.finditer(line):
        t = m.group(1)
        if len(t) < 8 or not re.search(r"[a-f]", t) and len(t) < 12:
            continue
        total += 1
        hits = [p for p, h in rows if h.startswith(t)]
        if not hits:
            unmatched.append((n, t)); continue
        matched += 1
        before = line[:m.start()]
        # the nearest file-like name before the token
        names = re.findall(r"([A-Za-z0-9_.\-]+\.(?:py|json|md|jsonl|txt))", before)
        near = names[-1] if names else ""
        ok = any(os.path.basename(p) == near for p in hits)
        if not ok:
            flagged.append((n, t, near, sorted(set(hits))[:4]))
print("tokens", total, "matched", matched, "unmatched", len(unmatched), "flagged", len(flagged))
for f in flagged:
    print("FLAG", f)
print("UNMATCHED", " ".join(f"{n}:{t}" for n, t in unmatched))
