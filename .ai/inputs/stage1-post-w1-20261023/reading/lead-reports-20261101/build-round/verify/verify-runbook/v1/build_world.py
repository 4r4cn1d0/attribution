"""Build the synthetic stage-1 world with ws-a's synth_kit (HarmBench pods on, no caps) and move it into the dry-run ROOT."""
import hashlib, json, shutil, sys
from pathlib import Path
WSA, V = Path(sys.argv[1]), Path(sys.argv[2])
R = V / "root"
sys.path[:0] = [str(WSA), str(WSA / "scripts/stage1_s1/reading_input/tests")]
import synth_kit as sk
world = V / "world"
if world.exists():
    shutil.rmtree(world)
s = sk.make(world, "plan_a", seed=0, hb=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
kit = R / "tmp/stage1-olmo"
for p in sorted((world / "kit").iterdir()):
    dest = kit / p.name
    if dest.exists():
        raise SystemExit(f"refuse: {dest} exists")
    shutil.move(str(p), str(dest))
for dest in (R / "runkit/stage1-olmo/stage1_rules.py", kit / "stage1_rules.py"):
    shutil.copy2(world / "repo/rules.py", dest)
shutil.move(str(world / "repo/tmp/synth-gate"), str(R / "tmp/synth-gate"))
assert sha(world / "repo" / sk.BARS) == sha(R / sk.BARS), "bars file differs"
rd = R / ".ai/inputs/stage1-post-w1-20261023/reading"
shutil.copy2(world / "b14/strata.json", rd / "b14/strata/strata.json")
(R / "tmp/synth-b14").mkdir(parents=True)
shutil.copy2(world / "b14/overlap_report.json", R / "tmp/synth-b14/overlap_report.json")
print(json.dumps({"strata_sha256": sha(rd / "b14/strata/strata.json"), "report_sha256": sha(R / "tmp/synth-b14/overlap_report.json"),
                  "kit_entries": sorted(p.name for p in kit.iterdir()), "seals": sorted(p.name for p in (kit / "seals").iterdir()),
                  "plan_seals": json.loads((kit / "plan.json").read_text())["seals"]}, indent=1))
