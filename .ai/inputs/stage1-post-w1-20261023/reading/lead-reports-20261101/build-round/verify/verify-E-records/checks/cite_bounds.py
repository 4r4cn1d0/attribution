"""Bounds check of short-name citations (NAME:line[-line][, :line...]) in the E drafts against the sources at 55d5f8b."""
import re, sys, pathlib
src = pathlib.Path(sys.argv[1]); rep = pathlib.Path(sys.argv[2])
files = {"REV4": "REV4.md", "ADD": "ADD.md", "FOCUS": "FOCUS.md", "W1R": "W1R.md", "PLAN": "PLAN.md", "KW": "KW.json",
         "LEDGER": "LEDGER.md", "HLC": "HLC.md", "SPF": "SPF.md", "PREREG": "PREREG.md", "RIB": "RIB.json",
         "HBB": "HBB.json", "B16H": "B16H.json", "OTSC": "OTSC.json", "PLANS": "PLANS.md"}
n_lines = {k: len((src / v).read_text(encoding="utf-8").splitlines()) for k, v in files.items()}
tok = re.compile(r"\b(" + "|".join(files) + r"):(\d+)(?:-(\d+))?((?:,\s*:\d+(?:-\d+)?)*)")
total = bad = 0
for f in sorted(rep.glob("E-*.md")):
    if f.name.startswith("E-records"):
        continue
    text = f.read_text(encoding="utf-8")
    for m in tok.finditer(text):
        name = m.group(1)
        nums = [int(m.group(2))] + ([int(m.group(3))] if m.group(3) else [])
        for extra in re.findall(r":(\d+)(?:-(\d+))?", m.group(4) or ""):
            nums.append(int(extra[0]))
            if extra[1]:
                nums.append(int(extra[1]))
        for k in nums:
            total += 1
            if not (1 <= k <= n_lines[name]):
                bad += 1
                print("OUT OF RANGE", f.name, m.group(0), "file has", n_lines[name])
print("citations parsed:", total, "out of range:", bad)
