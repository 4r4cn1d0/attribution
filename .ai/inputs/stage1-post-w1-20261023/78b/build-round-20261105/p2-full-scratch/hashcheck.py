import re, sys
part2, *shafiles = sys.argv[1:]
known = {}
for f in shafiles:
    for line in open(f):
        parts = line.split()
        if len(parts) >= 2 and re.fullmatch(r'[0-9a-f]{64}', parts[0]):
            known.setdefault(parts[0], []).append(parts[-1])
text = open(part2).read()
toks = set(re.findall(r'(?<![0-9a-f])([0-9a-f]{64})(?![0-9a-f])', text))
pref = set(re.findall(r'(?<![0-9a-zA-Z_])([0-9a-f]{8,63})…', text))
matched, unmatched = 0, []
for h in sorted(toks):
    if h in known: matched += 1
    else: unmatched.append(('full', h))
for h in sorted(pref):
    hits = [k for k in known if k.startswith(h)]
    if hits: matched += 1
    else: unmatched.append(('prefix', h))
print('full', len(toks), 'prefix', len(pref), 'matched to a file', matched, 'not a file hash', len(unmatched))
for kind, h in unmatched:
    print(kind, h)
