"""Recompute every SHA-256 in section 2 of the runbook from the worktrees and the main checkout; print mismatches.
Code and settings files only (no sealed file, no unit, no outcome)."""
import hashlib, pathlib, re, sys
WS = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds")
MAIN = pathlib.Path("/Users/spiderishi/Coding/attribution")
RB = WS / "runbook" / "reading-runbook.md"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
B16 = "scripts/stage1_s1/reading/"; RI = "scripts/stage1_s1/reading_input/"; RX = "scripts/stage1_s1/reading_extra/"; HD = "scripts/stage1_s1/hlc_draw/"
where = {}
for n in ["__init__.py","__main__.py","contrast.py","labels.py","overlap.py","phi.py","reading.py","references.py","reml.py","schema.py","sensitivities.py","settings.py","tdist.py","settings/reading.json"]:
    where["B16/" + n] = MAIN / (B16 + n)
for n in ["__init__.py","__main__.py","build.py","items.py","coherent.py","sg_coherent.py"]:
    where["RI/" + n] = WS / "ws-a" / (RI + n)
for n in ["sources.py","hb.py","hb_claim.py"]:
    where["RI/" + n] = MAIN / (RI + n)
for n in ["__init__.py","common.py","fk_power.py","stage3_pick.py","cap_reports.py","sa_shift.py","cost_table.py"]:
    where["RX/" + n] = WS / "ws-d1" / (RX + n)
for n in ["__init__.py","__main__.py","draw.py","inputs.py","settings/hlc_draw.json"]:
    where["HD/" + n] = WS / "ws-d2" / (HD + n)
for n in ["scripts/stage1_s1/overlap_strata.py","scripts/stage1_s1/settings/overlap_strata.json","scripts/stage1_s1/overlap_inputs.py","scripts/stage1_s1/overlap_inputs_check.py","scripts/stage1_s1/overlap_similarity.py","scripts/stage1_s1/settings/overlap_similarity.json","scripts/family_probe_reading.py","scripts/killtest_stage0_reading.py","scripts/stage1/limits/limits_common.py","scripts/stage1/s1common.py","experiments/safety_selection/configs/family-probe-reading-amended-20261008.json","runkit/stage1-olmo/stage1_rules.py","runkit/stage1-olmo/seal.py","runkit/stage1-olmo/plan_tool.py","runkit/stage1-olmo/judge_units_stage1.py","tmp/stage1-olmo/stage1_rules.py","tmp/stage1-olmo/seal.py","tmp/stage1-olmo/plan_tool.py","tmp/stage1-olmo/judge_units_stage1.py","scripts/stage1_s1/reading/mutation/mutants_b16.json","scripts/stage1_s1/reading/mutation/run_mutants.py","scripts/stage1_s1/mutation/mutants_b14.json","runkit/stage1-olmo/tests/mutants_b15.json"]:
    where[n] = MAIN / n
where["ws-a:mutants_reading_input.json"] = WS / "ws-a" / (RI + "mutation/mutants_reading_input.json")
where["ws-a:RI run_mutants.py"] = WS / "ws-a" / (RI + "mutation/run_mutants.py")
where["ws-d1:mutants_reading_extra.json"] = WS / "ws-d1" / (RX + "mutation/mutants_reading_extra.json")
where["ws-d1:RX run_mutants.py"] = WS / "ws-d1" / (RX + "mutation/run_mutants.py")
where["ws-d2:mutants_hlc_draw.json"] = WS / "ws-d2" / (HD + "mutation/mutants_hlc_draw.json")
where["ws-d2:HD run_mutants.py"] = WS / "ws-d2" / (HD + "mutation/run_mutants.py")
# ws-b and ws-c copies of merged files against main
pairs = [("ws-b", "scripts/stage1_s1/overlap_strata.py"), ("ws-b", "scripts/stage1_s1/settings/overlap_strata.json"), ("ws-b", "scripts/stage1_s1/overlap_inputs.py"), ("ws-b", "scripts/stage1_s1/overlap_inputs_check.py"), ("ws-b", "scripts/stage1_s1/mutation/mutants_b14.json"), ("ws-c", "runkit/stage1-olmo/stage1_rules.py"), ("ws-c", "runkit/stage1-olmo/plan_tool.py"), ("ws-c", "runkit/stage1-olmo/seal.py"), ("ws-c", "runkit/stage1-olmo/judge_units_stage1.py"), ("ws-c", "runkit/stage1-olmo/tests/mutants_b15.json")]
text = RB.read_text()
hexes = set(re.findall(r"`?([0-9a-f]{64})`?", text))
computed = {k: sha(p) for k, p in where.items()}
bad = {k: h for k, h in computed.items() if h not in hexes}
print("files hashed:", len(computed), "; not found in the runbook's text:", bad)
for w, rel in pairs:
    a, b = sha(WS / w / rel), sha(MAIN / rel)
    print(f"{w} {rel}: {'equal to main' if a == b else 'DIFFERS from main: ' + a[:16] + ' vs ' + b[:16]}")
# the runbook's hashes that no file of mine produced
unmatched = sorted(h for h in hexes if h not in set(computed.values()))
print("runbook hex strings with no file here (expected: the two seals and the first manifest):", [h[:16] for h in unmatched])
# spec counts
import json
for k in ["ws-a:mutants_reading_input.json", "ws-d1:mutants_reading_extra.json", "ws-d2:mutants_hlc_draw.json", "scripts/stage1_s1/mutation/mutants_b14.json", "runkit/stage1-olmo/tests/mutants_b15.json", "scripts/stage1_s1/reading/mutation/mutants_b16.json"]:
    d = json.loads(pathlib.Path(where[k]).read_text())
    ms = d["mutants"]
    print(k, len(ms), "entries; expected survivors:", [m["id"] for m in ms if m.get("expect") == "survive"])
near = WS / "reports" / "mutants_b14_near.json"
d = json.loads(near.read_text()); print("near set", len(d["mutants"]), sha(near)[:16])
