import re, sys, pathlib
S = pathlib.Path(sys.argv[1])
P, M = S / "ws-p", S / "ws-m"
doc = (P / "research/experiments/2026-11-06-78b-preregistration-part2.md").read_text()
full = sorted(set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", doc)))
srcs = [S / "reports/p2-scratch" / n for n in ("ws-m-scale78b.sha", "head-stage1.sha", "head-other.sha", "head-extra.sha")] + [
    M / "scripts/scale78b/settings/pins_78b.json", M / "scripts/scale78b/scorers_78b.py",
    P / ".ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json",
    P / ".ai/inputs/scale-78b-s1-llama3-20261105/out/MANIFEST.json",
    P / "scripts/stage1_s1/settings/oext_unit.json"]
text = "".join(p.read_text() for p in srcs)
extra = {  # measured in this track's commands (shasum output in the transcript), not in the files above
}
missing = [h for h in full if h not in text]
print("full hashes in Part 2:", len(full)); print("not in the source files:", len(missing))
for h in missing: print(" ", h)
