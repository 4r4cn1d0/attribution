"""Judge numbers of 11 Oct for the note's 7-8B and Qwen cells: E_HB (HarmBench, sampled answers) and Granite greedy E per
unit, each against its model's untuned unit judged in the first pod pair (sp-hb-7b-qwen-1, sp-granite-7b-qwen-1). The
second pair (sp-hb-repl-1, sp-granite-repl-1) judged the Scheduled, half-LR and remaining Constant units; it holds no
untuned units, so every value here is against the first pair's untuned file (same device type, deterministic labels).
Counts only; no prompt or answer text.

    python3 -I judge_numbers_20261011.py OUT_JSON
"""
import json
import pathlib
import statistics
import sys

J = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp/judge-pod")

# model -> (untuned host, untuned unit, first-pair group)
UNTUNED = {
    "OLMo-2-7B": ("sp-olmo2-7b-b2-1101", "1101-a0-init-a1", "olmo7"),
    "Llama-3.1-8B": ("sp-llama31-8b-1101", "1101-a0-init-a1", "llama8"),
    "Qwen2.5-1.5B": ("sp-qwen15-b-1101", "1101-a0-init-a1", "qwen15"),
    "Qwen2.5-7B": ("sp-qwen7-b-1101", "1101-a0-init-a1", "qwen7"),
}
# (model, recipe) -> [(run suffix, group, host, unit)]; run suffix "7b-qwen-1" = first pair, "repl-1" = second pair
CELLS = {
    ("OLMo-2-7B", "Constant"): [("7b-qwen-1", "olmo7", "sp-olmo2-7b-b2-1101", "1101-a0-e1-a1"),
                                ("7b-qwen-1", "olmo7", "sp-olmo2-7b-1102", "1102-a0-e1-a1"),
                                ("repl-1", "olmo7-c", "sp-olmo2-7b-1103", "1103-a0-e1-a1")],
    ("OLMo-2-7B", "Scheduled"): [("repl-1", "olmo7-g", f"sp-olmo2-7b-g-{s}", f"{s}-a0-e1-a1") for s in (1101, 1102, 1103)],
    ("OLMo-2-7B", "Constant, half LR"): [("repl-1", "olmo7-h", f"sp-olmo2-7b-b5e5-{s}", f"{s}-a0-e1-a1") for s in (1101, 1102, 1103)],
    ("Llama-3.1-8B", "Constant"): [("7b-qwen-1", "llama8", "sp-llama31-8b-1101", "1101-a0-e1-a1"),
                                   ("repl-1", "llama8-c", "sp-llama31-8b-1102", "1102-a0-e1-a1"),
                                   ("repl-1", "llama8-c", "sp-llama31-8b-1103", "1103-a0-e1-a1")],
    ("Llama-3.1-8B", "Scheduled"): [("repl-1", "llama8-g", f"sp-llama31-8b-g-{s}", f"{s}-a0-e1-a1") for s in (1101, 1102, 1103)],
    ("Llama-3.1-8B", "Constant, half LR"): [("7b-qwen-1", "llama8-b5e5", f"sp-llama31-8b-b5e5-{s}", f"{s}-a0-e1-a1") for s in (1101, 1102)],
    ("Qwen2.5-1.5B", "Constant"): [("7b-qwen-1", "qwen15", f"sp-qwen15-b-{s}", f"{s}-a0-e1-a1") for s in (1101, 1102, 1103)],
    ("Qwen2.5-1.5B", "Scheduled"): [("repl-1", "qwen15-g", f"sp-qwen15-g-{s}", f"{s}-a0-e1-a1") for s in (1101, 1102, 1103)],
    ("Qwen2.5-7B", "Constant"): [("7b-qwen-1", "qwen7", f"sp-qwen7-b-{s}", f"{s}-a0-e1-a1") for s in (1101, 1102, 1103)],
    ("Qwen2.5-7B", "Scheduled"): [("repl-1", "qwen7-g", f"sp-qwen7-g-{s}", f"{s}-a0-e1-a1") for s in (1101, 1102, 1103)],
}


def read(judge, run, group, host, unit):
    files = list((J / f"sp-{judge if judge == 'granite' else 'hb'}-{run}" / f"judges-{group}").glob(f"{judge}--{host}--{unit}--*.json"))
    assert len(files) == 1, (judge, run, group, host, unit, files)
    d = json.loads(files[0].read_text())
    mode = "greedy" if judge == "granite" else "sampled"
    m = d[mode]
    assert m["unparsed"] == 0 and m["n"] == (200 if judge == "granite" else 600), (files[0], m)
    return m["harm"], m["n"], files[0].name


out = {"untuned": {}, "cells": {}}
base = {}
for model, (host, unit, group) in UNTUNED.items():
    hb = read("harmbench", "7b-qwen-1", group, host, unit)
    gr = read("granite", "7b-qwen-1", group, host, unit)
    base[model] = (hb, gr)
    out["untuned"][model] = {"harmbench_sampled": f"{hb[0]}/{hb[1]}", "harmbench_pct": round(100 * hb[0] / hb[1], 2),
                            "harmbench_file": hb[2], "granite_greedy": f"{gr[0]}/{gr[1]}", "granite_pct": round(100 * gr[0] / gr[1], 2),
                            "granite_file": gr[2]}
for (model, recipe), units in CELLS.items():
    (h0, n0, _), (g0, m0, _) = base[model]
    rows = []
    for run, group, host, unit in units:
        hb = read("harmbench", run, group, host, unit)
        gr = read("granite", run, group, host, unit)
        rows.append({"host": host, "seed": int(unit[:4]), "pair": "first" if run == "7b-qwen-1" else "second",
                     "harmbench_sampled": f"{hb[0]}/{hb[1]}", "E_HB_pp": round(100 * (hb[0] / hb[1] - h0 / n0), 2), "harmbench_file": hb[2],
                     "granite_greedy": f"{gr[0]}/{gr[1]}", "granite_E_pp": round(100 * (gr[0] / gr[1] - g0 / m0), 2), "granite_file": gr[2]})
    ehb = [r["E_HB_pp"] for r in rows]
    egr = [r["granite_E_pp"] for r in rows]
    out["cells"][f"{model} | {recipe}"] = {
        "units": rows, "E_HB_mean": round(statistics.mean(ehb), 2), "E_HB_sd": round(statistics.stdev(ehb), 2) if len(ehb) > 1 else None,
        "granite_E_mean": round(statistics.mean(egr), 2)}
pathlib.Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
for k, v in out["untuned"].items():
    print(f"{k:13s} untuned  HB {v['harmbench_sampled']} ({v['harmbench_pct']}%)  Granite {v['granite_greedy']} ({v['granite_pct']}%)")
for k, v in out["cells"].items():
    seeds = ", ".join(f"{r['E_HB_pp']:+.1f}" for r in v["units"])
    gseeds = ", ".join(f"{r['granite_E_pp']:+.1f}" for r in v["units"])
    print(f"{k:32s} E_HB {seeds} (mean {v['E_HB_mean']:+.1f})   Granite {gseeds} (mean {v['granite_E_mean']:+.1f})")
