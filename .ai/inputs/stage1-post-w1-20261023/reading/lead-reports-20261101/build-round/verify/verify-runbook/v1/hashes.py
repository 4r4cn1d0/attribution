"""Compute SHA-256 of every file the runbook's section 2 names, from the worktrees and the main checkout; compare."""
import hashlib, pathlib, re, sys
B = pathlib.Path(sys.argv[1]); ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution"); RB = pathlib.Path(sys.argv[2])
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
A = "scripts/stage1_s1/reading_input/"; B16 = "scripts/stage1_s1/reading/"; RX = "scripts/stage1_s1/reading_extra/"; HD = "scripts/stage1_s1/hlc_draw/"
want = {}
for name in "contrast labels overlap phi reading references reml schema sensitivities settings tdist".split() + ["__init__", "__main__"]:
    want[B16 + name + ".py"] = ROOT
want[B16 + "settings/reading.json"] = ROOT
for name in "__init__ __main__ build items coherent sg_coherent".split(): want[A + name + ".py"] = B / "ws-a"
for name in "sources hb hb_claim".split(): want[A + name + ".py"] = ROOT
for name in "__init__ common fk_power stage3_pick cap_reports sa_shift cost_table".split(): want[RX + name + ".py"] = B / "ws-d1"
for name in "__init__ __main__ draw inputs".split(): want[HD + name + ".py"] = B / "ws-d2"
want[HD + "settings/hlc_draw.json"] = B / "ws-d2"
for rel in ["scripts/stage1_s1/overlap_strata.py", "scripts/stage1_s1/settings/overlap_strata.json", "scripts/stage1_s1/overlap_inputs.py",
            "scripts/stage1_s1/overlap_inputs_check.py", "scripts/stage1_s1/overlap_similarity.py", "scripts/stage1_s1/settings/overlap_similarity.json",
            "scripts/family_probe_reading.py", "scripts/killtest_stage0_reading.py", "scripts/stage1/limits/limits_common.py", "scripts/stage1/s1common.py",
            "runkit/stage1-olmo/stage1_rules.py", "runkit/stage1-olmo/seal.py", "runkit/stage1-olmo/plan_tool.py", "runkit/stage1-olmo/judge_units_stage1.py",
            "scripts/stage1_s1/reading/mutation/mutants_b16.json", "scripts/stage1_s1/reading/mutation/run_mutants.py",
            "scripts/stage1_s1/mutation/mutants_b14.json", "runkit/stage1-olmo/tests/mutants_b15.json"]:
    want[rel] = ROOT
want[A + "mutation/mutants_reading_input.json"] = B / "ws-a"; want[A + "mutation/run_mutants.py"] = ROOT
want[RX + "mutation/mutants_reading_extra.json"] = B / "ws-d1"; want[RX + "mutation/run_mutants.py"] = B / "ws-d1"
want[HD + "mutation/mutants_hlc_draw.json"] = B / "ws-d2"; want[HD + "mutation/run_mutants.py"] = B / "ws-d2"
text = RB.read_text()
hexes = set(re.findall(r"`([0-9a-f]{64})`", text)) | set(re.findall(r"([0-9a-f]{64})", text))
missing = []
for rel, base in sorted(want.items()):
    q = base / rel
    h = sha(q) if q.is_file() else None
    ok = h in hexes if h else False
    print(("ok  " if ok else "MISS") + f" {h[:16] if h else 'ABSENT'} {rel} ({base.name})")
    if not ok: missing.append(rel)
# also: live kit code copies and the bars file
for q in [ROOT / "tmp/stage1-olmo/stage1_rules.py", ROOT / "tmp/stage1-olmo/seal.py", ROOT / "tmp/stage1-olmo/plan_tool.py", ROOT / "tmp/stage1-olmo/judge_units_stage1.py"]:
    h = sha(q); print(("ok  " if h in hexes else "MISS") + f" {h[:16]} {q.relative_to(ROOT)} (live kit)")
# worktree ws-b / ws-c equal main?
for rel in ["scripts/stage1_s1/overlap_strata.py", "scripts/stage1_s1/settings/overlap_strata.json", "scripts/stage1_s1/overlap_inputs.py", "scripts/stage1_s1/overlap_inputs_check.py", "scripts/stage1_s1/mutation/mutants_b14.json"]:
    print("ws-b==main", rel, sha(B / "ws-b" / rel) == sha(ROOT / rel))
for rel in ["runkit/stage1-olmo/stage1_rules.py", "runkit/stage1-olmo/seal.py", "runkit/stage1-olmo/plan_tool.py", "runkit/stage1-olmo/judge_units_stage1.py", "runkit/stage1-olmo/tests/mutants_b15.json"]:
    print("ws-c==main", rel, sha(B / "ws-c" / rel) == sha(ROOT / rel))
print("MISSING:", missing)
