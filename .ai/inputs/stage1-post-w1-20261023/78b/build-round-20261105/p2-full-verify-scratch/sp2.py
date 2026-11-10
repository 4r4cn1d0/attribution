import sys, hashlib, os; sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode=True
import stage1_rules as sr
root=sys.argv[2]
bad=0
for p,h in sorted(sr.SCORER_PINS.items()):
    with open(os.path.join(root,p),"rb") as f: ok = hashlib.sha256(f.read()).hexdigest()==h
    bad += not ok
    if not p.startswith("scripts/scale78b/settings/"): print("  ", p, "ok" if ok else "DIFFERS")
print("SCORER_PINS", len(sr.SCORER_PINS), "differ", bad)
