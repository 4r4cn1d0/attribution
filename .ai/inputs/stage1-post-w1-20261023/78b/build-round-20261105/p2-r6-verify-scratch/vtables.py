"""Path-aware check of Part 2's hash tables against a pool (prints paths and verdicts only)."""
import re
import sys

text, pool = sys.argv[1], sys.argv[2]
by_path = {}
for line in open(pool):
    h, p = line.rstrip("\n").split("\t", 1)
    by_path[p] = h
lines = open(text, encoding="utf-8").read().split("\n")


def section(start_pat, end_pat):
    out, on = [], False
    for n, l in enumerate(lines, 1):
        if re.search(start_pat, l):
            on = True
            continue
        if on and re.search(end_pat, l):
            break
        if on:
            out.append((n, l))
    return out


ROW = re.compile(r"^\| `([^`]+)`[^|]*\| `([0-9a-f]{64})` \|$")
bad = good = 0
checks = [
    (r"^\*\*Table A\.", r"^The other test files", "scripts/scale78b/"),
    (r"^\*\*Table B\.", r"^\*\*Table C\.", ""),
    (r"^\*\*Table C\.", r"^\*\*Table D\.", "scripts/stage1/settings/"),
    (r"^\*\*Table D\.", r"^### 1\.18", ""),
]
for sp, ep, base in checks:
    for n, l in section(sp, ep):
        m = ROW.match(l)
        if not m:
            continue
        p, h = m.group(1), m.group(2)
        path = p if (p.startswith(("scripts/", "runkit/", ".ai/")) or not base) else base + p
        got = by_path.get(path)
        if got == h:
            good += 1
        else:
            bad += 1
            print(f"BAD line {n}: {path} text {h[:16]} pool {str(got)[:16]}")
# Table A's five test files in prose
for n, l in enumerate(lines, 1):
    if l.startswith("The other test files of the folder"):
        for name, pre in re.findall(r"`(test_[a-z0-9_]+\.py)` `([0-9a-f]{7,})…`", l):
            got = by_path.get("scripts/scale78b/tests/" + name, "")
            ok = got.startswith(pre)
            good += ok
            bad += (not ok)
            if not ok:
                print(f"BAD line {n}: {name} {pre} pool {got[:16]}")
# §2.3 R edits
for n, l in enumerate(lines, 1):
    m = re.match(r"^\| R_d(\d+) \| (.*)\| `R_d\d+\.json`; `([0-9a-f]{64})` \|$", l)
    if not m:
        continue
    d, olmo, llama = m.group(1), m.group(2), m.group(3)
    lp = f".ai/inputs/scale-78b-sealed-llama3-20261105/out/edits/R_d{d}.json"
    oh = re.search(r"`([0-9a-f]{64})`", olmo).group(1)
    di = int(d)
    if di in (4, 5):
        op = f".ai/inputs/gate-b-sealed-20261008/out/edits/R_d{d}.json"
    elif 6 <= di <= 10:
        op = f".ai/inputs/stage1-commitments-20261016/r-draws/edits/R_d{d}.json"
    else:
        op = f".ai/inputs/scale-78b-r-draws-olmo2-20261105/out/edits/R_d{d}.json"
    for path, h in ((op, oh), (lp, llama)):
        got = by_path.get(path)
        if got == h:
            good += 1
        else:
            bad += 1
            print(f"BAD line {n}: {path} text {h[:16]} pool {str(got)[:16]}")
# §16.3 B16 files
for n, l in enumerate(lines, 1):
    if "B16's files at" in l:
        for name, pre in re.findall(r"`([a-z_/]+\.(?:py|json))` `([0-9a-f]{8})…`", l):
            got = by_path.get("scripts/stage1_s1/reading/" + name, "")
            ok = got.startswith(pre)
            good += ok
            bad += (not ok)
            if not ok:
                print(f"BAD line {n}: {name} {pre} pool {got[:16]}")
print(f"good {good} bad {bad}")
