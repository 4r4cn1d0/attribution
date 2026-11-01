"""Parse every NAME:line[-line] citation (with ':n' continuations) in the six E drafts and check each is inside
its source at 55d5f8b (extracts in v2/src) or in the scratch reports. Prints out-of-range and unknown names."""
import re, sys, pathlib
V2 = pathlib.Path(sys.argv[1]); REP = pathlib.Path(sys.argv[2]); PREP = pathlib.Path(sys.argv[3]); NS = pathlib.Path(sys.argv[4])
src = V2 / "src"
files = {
 "ADD": src/"ADD.md", "REV4": src/"REV4.md", "W1R": src/"W1R.md", "PREREG": src/"PREREG.md", "FOCUS": src/"FOCUS.md",
 "SPF": src/"SPF.md", "PLAN": src/"PLAN.md", "KW": src/"KW.json", "LEDGER": src/"LEDGER.md", "RIB": src/"RIB.json",
 "HBB": src/"HBB.json", "B16H": src/"B16H.json", "OTSC": src/"OTSC.json", "HLC": src/"HLC.md", "PLANS": src/"PLANS.md",
 "STR": src/"STR.py", "STRS": src/"STRS.json", "LC": src/"LC.py", "GBR": src/"GBR.py", "SIM": src/"SIM.py",
 "RULES": src/"RULES.py", "PT": src/"PT.py", "JR": src/"JR.py", "MAN1": src/"MAN1.json",
 "CRIT": PREP/"2-critic.md", "R1D": PREP/"1d-reading-runbook-draft.md", "R1B": PREP/"1b-b14-similarity.md",
 "D1A": PREP/"1a-ri-o2-design.md", "V1A": PREP/"1a-ri-o2-review.md",
 "READY": NS/"A-stage1b-readiness.md", "CHECK": NS/"A-stage1b-check.md",
 "B16/README.md": src/"B16_README.md", "B16/reading.py": src/"B16_reading.py", "B16/contrast.py": src/"B16_contrast.py",
 "RI/build.py": src/"RI_build.py", "RI/__main__.py": src/"RI_main.py", "RI/hb_claim.py": src/"RI_hb_claim.py",
 "RI/items.py": src/"RI_items.py",
}
lens = {k: len(p.read_text().splitlines()) for k, p in files.items()}
pat = re.compile(r"(?<![A-Za-z0-9_/.])((?:[A-Z][A-Z0-9]+)|(?:B16/[A-Za-z_./]+\.(?:md|py|json))|(?:RI/[A-Za-z_./]+\.py)):(\d+)(?:-(\d+))?((?:,\s*:\d+(?:-\d+)?)*)")
bad = []; unknown = {}; total = 0
for name in ["E-39.md", "E-D5-D6.md", "E-S1-blinding.md", "E-misc.md", "E-40.md", "E-plan-updates.md"]:
    t = (REP / name).read_text()
    for m in pat.finditer(t):
        short = m.group(1)
        rngs = [(int(m.group(2)), int(m.group(3) or m.group(2)))]
        for c in re.findall(r":(\d+)(?:-(\d+))?", m.group(4) or ""):
            rngs.append((int(c[0]), int(c[1] or c[0])))
        if short not in lens:
            unknown[short] = unknown.get(short, 0) + 1; continue
        for a, b in rngs:
            total += 1
            if not (1 <= a <= b <= lens[short]):
                bad.append((name, short, a, b, lens[short]))
print("checked", total, "citations; out of range:", len(bad))
for x in bad: print("  OUT", x)
print("unknown names (not checked):", unknown)
