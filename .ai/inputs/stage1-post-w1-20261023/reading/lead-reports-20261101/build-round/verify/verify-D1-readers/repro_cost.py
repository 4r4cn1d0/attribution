"""Reproductions for cost_table (verifier; synthetic cost kit only)."""
import json, statistics, sys
from pathlib import Path
WS = Path.cwd()
sys.path.insert(0, str(WS)); sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_extra/tests"))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_input/tests"))
import extra_kit as ek
from scripts.stage1_s1.reading_extra import cost_table as ct

base = Path(sys.argv[1]); base.mkdir(parents=True, exist_ok=True)
kit, slots, plan = ek.cost_kit(base / "k", "plan_a")
out = ct.table(kit, "plan_a")
c0 = out["units"]["c0"]["measured_s"]
print("units keys:", sorted(out["units"]))
r = out["arms"]["R"]
print("R record keys:", sorted(r), "| run keys:", sorted(r["run"]))
print("median slot of the stage-1 R runs (by hand):", statistics.median(v["slot_s"] for v in r["runs"].values()),
      "| present anywhere in the output:", any("median" in k for k in json.dumps(out)
                                                 .replace('"', ' ').split() if "median" in k and "R" in k))
for name, rec in out["b10_references"].items():
    print(f"{name}: seconds {rec['seconds']:.3f}  c_lean_c0 {rec['c_lean_c0']:.6f}  seconds/c0 {rec['seconds'] / c0:.6f}"
          f"  equal: {rec['c_lean_c0'] == rec['seconds'] / c0}")
for k in ("ref_eval", "safe_lora"):
    d = out["diagnostics_by_kind"][k]
    print(f"diagnostics_by_kind[{k}]: c_lean_c0 {d['c_lean_c0']:.6f} = seconds/c0 {d['seconds'] / c0:.6f}")
print("readings that mention B10 under C-lean:", [k for k, v in out["readings"].items() if "B10" in v and "lean" in v])
# the frozen planning prices (scripts/stage1/settings/selector_spec.json cost_conventions) for scale
spec = json.loads((WS / "scripts/stage1/settings/selector_spec.json").read_text())["cost_conventions"]
full = spec["C-full"]; lean = spec["C-lean"]["variants"]["a"]
full_eval = full["setup_s"] + full["evaluation_s"] + 400 * (1694 + 80) / 468
lean_eval = lean["setup_s"] + lean["evaluation_s"] + 1516.2
print(f"frozen planning prices: full evaluation-only {full_eval:.1f} s, lean evaluation-only {lean_eval:.1f} s, ratio {full_eval / lean_eval:.2f}")
