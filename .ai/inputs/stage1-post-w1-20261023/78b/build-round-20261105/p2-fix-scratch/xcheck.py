"""Cross-check: every full 64-hex value and every 8+ hex prefix in Part 2 is found in a measured hash list or a
source file (hash lists: `<sha>  <path>`; sources: searched as text for the value). Prints counts and the
unmatched values only (hashes, never file text). Usage: python -I -B xcheck.py PART2 OUT --sha F... --src F..."""
import re
import sys

args = sys.argv[1:]
part2, out = args[0], args[1]
shas, srcs, mode = [], [], None
for a in args[2:]:
    if a in ("--sha", "--src"):
        mode = a
        continue
    (shas if mode == "--sha" else srcs).append(a)

text = open(part2, encoding="utf-8").read()
full = sorted(set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", text)))
prefixes = sorted(set(m for m in re.findall(r"`([0-9a-f]{8,63})…", text)))
known, where = set(), {}
for f in shas:
    for line in open(f, encoding="utf-8"):
        parts = line.split()
        if parts and re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            known.add(parts[0])
            where.setdefault(parts[0], parts[1] if len(parts) > 1 else f)
blob = ""
for f in srcs:
    try:
        blob += open(f, encoding="utf-8", errors="replace").read()
    except OSError as exc:
        print("cannot read", f, type(exc).__name__)
src_hex = set(re.findall(r"[0-9a-f]{64}", blob))
allhex = known | src_hex
miss_full = [h for h in full if h not in allhex]
miss_pre = [p for p in prefixes if not any(h.startswith(p) for h in allhex) and not any(h.startswith(p) for h in full)]
with open(out, "w", encoding="utf-8") as fh:
    for h in full:
        fh.write(f"{h} {'hashlist:' + where[h] if h in known else ('source' if h in src_hex else 'MISSING')}\n")
print(f"full values: {len(full)}; missing: {len(miss_full)}")
for h in miss_full:
    print("  MISSING full", h)
print(f"prefixes: {len(prefixes)}; unresolved: {len(miss_pre)}")
for p in miss_pre:
    print("  UNRESOLVED prefix", p)
