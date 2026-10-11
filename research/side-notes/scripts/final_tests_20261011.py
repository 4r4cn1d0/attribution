"""Final reads of 11 Oct: judge files of the second pod pair, the pre-registered half-LR test, and every pre-registered
test again on HarmBench (the replication's P3 sign check; descriptive for the rest). Counts only.
python3 -I final_tests_20261011.py"""
import glob
import json
import pathlib
import subprocess
import sys

M = pathlib.Path("/Users/spiderishi/Coding/attribution")
W = M / ".claude/worktrees/peaceful-jepsen-8b8eee"
OUT = W / "research/side-notes/prereg-results-20261011"
SCRIPT = W / "research/side-notes/scripts/interaction_test_20261011.py"
PY = str(M / "tmp/minimal-experiment-20261002/venv/bin/python")
K = M / "scripts/gate_b_mac_judges"
T = M / "tmp"


def unit_dir(host):
    hits = sorted(glob.glob(f"{T}/*/retrieved/{host}/tree/round1/{host[-4:]}-a0-e1-a1"))
    assert hits, host
    return hits[0]


# 1. write_files for the second pair: one --out per (recipe) group, so no (arm, seed, target) collides
groups = {"olmo7-c": ["sp-olmo2-7b-1103"], "olmo7-g": ["sp-olmo2-7b-g-1101", "sp-olmo2-7b-g-1102", "sp-olmo2-7b-g-1103"],
          "olmo7-h": ["sp-olmo2-7b-b5e5-1101", "sp-olmo2-7b-b5e5-1102", "sp-olmo2-7b-b5e5-1103"],
          "llama8-c": ["sp-llama31-8b-1102", "sp-llama31-8b-1103"],
          "llama8-g": ["sp-llama31-8b-g-1101", "sp-llama31-8b-g-1102", "sp-llama31-8b-g-1103"],
          "qwen15-g": ["sp-qwen15-g-1101", "sp-qwen15-g-1102", "sp-qwen15-g-1103"],
          "qwen7-g": ["sp-qwen7-g-1101", "sp-qwen7-g-1102", "sp-qwen7-g-1103"]}
for judge, run in (("harmbench", "sp-hb-repl-1"), ("granite", "sp-granite-repl-1")):
    for g, hosts in groups.items():
        out = T / "judge-pod" / run / f"judges-{g}"
        if out.exists():
            continue
        args = [PY, "-B", str(K / "write_files.py"), "--judge", judge, "--cache", str(T / "judge-pod" / run / f"fetched/out/{judge}-pod.jsonl"),
                "--out", str(out)] + sum((["--unit", unit_dir(h)] for h in hosts), [])
        r = subprocess.run(args, capture_output=True, text=True)
        (T / "judge-pod" / run / f"write-{g}.log").write_text(r.stdout + r.stderr)
        assert r.returncode == 0, (judge, g, r.stderr[-400:])

# 2. every HarmBench judge file, by (host, unit)
hb = {}
for f in sorted(glob.glob(f"{T}/judge-pod/*/judges-*/harmbench--*--*--*.json")):
    parts = pathlib.Path(f).name.split("--")
    hb.setdefault((parts[1], parts[2]), f)

# 3. the half-LR map (Qwen3Guard) and HarmBench versions of every map
def cell(hosts):
    return [{"eval": unit_dir(h) + "/eval/e1", "harmbench": hb.get((h, f"{h[-4:]}-a0-e1-a1"))} for h in hosts]


half = {"cells": {"olmo_constant": cell(["sp-olmo2-7b-b2-1101", "sp-olmo2-7b-1102", "sp-olmo2-7b-1103"]),
                  "olmo_scheduled": cell(groups["olmo7-h"]),
                  "llama_constant": cell(["sp-llama31-8b-1101", "sp-llama31-8b-1102", "sp-llama31-8b-1103"]),
                  "llama_scheduled": cell(["sp-llama31-8b-b5e5-1101", "sp-llama31-8b-b5e5-1102"])},
        "slots": {"olmo": "OLMo-7B (1e-4 vs 5e-5)", "llama": "Llama-8B (1e-4 vs 5e-5)"}}
(OUT / "map-halflr_7b.json").write_text(json.dumps(half, indent=1))
rows = []
for mp in sorted(OUT.glob("map-*.json")):
    m = json.loads(mp.read_text())
    for c in m["cells"].values():
        for u in c:
            host = pathlib.Path(u["eval"]).parts[-6]
            u["harmbench"] = u.get("harmbench") or hb.get((host, f"{host[-4:]}-a0-e1-a1"))
    mp.write_text(json.dumps(m, indent=1))
    name = mp.stem[4:]
    for judge in ("qwen3guard", "harmbench"):
        if judge == "harmbench" and any(u["harmbench"] is None for c in m["cells"].values() for u in c):
            rows.append(f"{name:28s} {judge:10s} missing a HarmBench file")
            continue
        r = subprocess.run([sys.executable, "-I", str(SCRIPT), "--map", str(mp), "--judge", judge], capture_output=True, text=True)
        if r.returncode:
            rows.append(f"{name:28s} {judge:10s} ERROR {r.stderr[-200:]}")
            continue
        (OUT / f"result-{name}-{judge}.json").write_text(r.stdout)
        res = json.loads(r.stdout)
        lg, pp = res["logit"], res["pp"]
        rows.append(f"{name:28s} {judge:10s} D1 {lg['olmo_change']:+.3f} D2 {lg['llama_change']:+.3f} I {lg['interaction']:+.3f} "
                    f"[{lg['ci95'][0]:+.2f}, {lg['ci95'][1]:+.2f}] pp {pp['interaction']:+.1f} | {res['label']}")
print("\n".join(rows))
