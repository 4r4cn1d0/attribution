"""Check that every "Old:" fenced block of E-plan-updates.md occurs exactly once in PLAN at 55d5f8b, and report
the PLAN line numbers each block covers; also print the item header's cited PLAN line for comparison."""
import re, sys, pathlib
drafts = pathlib.Path(sys.argv[1]); plan = pathlib.Path(sys.argv[2]).read_text()
text = drafts.read_text()
items = re.split(r"\n### ", text)
fails = 0
for it in items[1:]:
    header = it.splitlines()[0]
    olds = re.findall(r"Old:\n```\n(.*?)\n```", it, flags=re.S)
    for o in olds:
        n = plan.count(o)
        start = plan.find(o)
        line0 = plan[:start].count("\n") + 1 if start >= 0 else None
        line1 = line0 + o.count("\n") if line0 else None
        ok = n == 1
        fails += not ok
        print(("OK  " if ok else "FAIL"), f"count={n}", f"PLAN:{line0}-{line1}", "|", header[:90])
print("fails", fails)
sys.exit(1 if fails else 0)
