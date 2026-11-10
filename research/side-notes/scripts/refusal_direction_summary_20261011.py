"""Summarize the refusal-direction probe outputs (exploratory; numbers only).

    python3 -I refusal_direction_summary_20261011.py OUT_JSON

Reads every tmp/sp-repr/out/<host>/*.json that holds per-layer probe records ("layers" with "cos_r_base_r_ft").
Per unit:
  - the refusal layer = the layer where the BASE model separates harmful from harmless prompts best
    (largest base separation along its own difference-of-means direction r_base);
  - at that layer: base and fine-tuned separation along u = r_base/|r_base|, the retained share
    (fine-tuned / base), cos(r_base, r_ft), and the drop of the harmful prompts' mean projection on u;
  - the same retained share averaged over the upper half of the layers (a robustness check).
Then it pairs each unit with its erosion E (research/side-notes/explore-20261011/units.csv) and prints a table by
family, size and recipe.
"""
import csv
import json
import pathlib
import statistics
import sys

M = pathlib.Path("/Users/spiderishi/Coding/attribution")
W = pathlib.Path("/Users/spiderishi/Coding/attribution/.claude/worktrees/peaceful-jepsen-8b8eee")
HOSTS = {  # host -> (model, recipe, seed)
    "olmo2-1b-1101": ("OLMo-2-1B", "Constant", 1101), "olmo2-1b-g-1101": ("OLMo-2-1B", "Scheduled", 1101),
    "llama32-1b-1101": ("Llama-3.2-1B", "Constant", 1101), "llama32-1b-g5-1101": ("Llama-3.2-1B", "Scheduled", 1101),
    "sp-olmo2-7b-b2-1101": ("OLMo-2-7B", "Constant", 1101), "sp-olmo2-7b-g-1101": ("OLMo-2-7B", "Scheduled", 1101),
    "sp-llama31-8b-1101": ("Llama-3.1-8B", "Constant", 1101), "sp-llama31-8b-g-1101": ("Llama-3.1-8B", "Scheduled", 1101),
}
HOSTS.update({  # the siblings, by their real host names
    "olmo2-1b-1102": ("OLMo-2-1B", "Constant", 1102), "olmo2-1b-1103": ("OLMo-2-1B", "Constant", 1103),
    "olmo2-1b-g-1102": ("OLMo-2-1B", "Scheduled", 1102), "olmo2-1b-g-1103": ("OLMo-2-1B", "Scheduled", 1103),
    "sp-llama32-1b-b2-1102": ("Llama-3.2-1B", "Constant", 1102), "sp-llama32-1b-b-1103": ("Llama-3.2-1B", "Constant", 1103),
    "llama32-1b-g-1102": ("Llama-3.2-1B", "Scheduled", 1102), "llama32-1b-g-1103": ("Llama-3.2-1B", "Scheduled", 1103),
    "sp-olmo2-7b-1102": ("OLMo-2-7B", "Constant", 1102), "sp-olmo2-7b-1103": ("OLMo-2-7B", "Constant", 1103),
    "sp-olmo2-7b-g-1102": ("OLMo-2-7B", "Scheduled", 1102), "sp-olmo2-7b-g-1103": ("OLMo-2-7B", "Scheduled", 1103),
    "sp-llama31-8b-1102": ("Llama-3.1-8B", "Constant", 1102), "sp-llama31-8b-1103": ("Llama-3.1-8B", "Constant", 1103),
    "sp-llama31-8b-g-1102": ("Llama-3.1-8B", "Scheduled", 1102), "sp-llama31-8b-g-1103": ("Llama-3.1-8B", "Scheduled", 1103),
})
E = {}
for row in csv.DictReader(open(W / "research/side-notes/explore-20261011/units.csv")):
    E[(row["model"], row["recipe"], int(row["seed"]))] = float(row["E_pp"])


def summarize(rep: dict) -> dict:
    layers = rep["layers"]
    def sep(rec, which):
        p = (rec.get("projection_onto_unit_r_base") or {}).get(which) or {}
        return p.get("separation")
    usable = [r for r in layers if sep(r, "base") is not None and sep(r, "ft") is not None]
    peak = max(usable, key=lambda r: sep(r, "base"))
    upper = usable[len(usable) // 2:]
    pb, pf = peak["projection_onto_unit_r_base"]["base"], peak["projection_onto_unit_r_base"]["ft"]
    return {"layers": len(layers), "refusal_layer": peak["layer"], "sep_base": sep(peak, "base"), "sep_ft": sep(peak, "ft"),
            "retained": sep(peak, "ft") / sep(peak, "base"), "cos": peak["cos_r_base_r_ft"],
            "harmful_proj_drop": pb["harmful"]["mean"] - pf["harmful"]["mean"],
            "harmless_proj_change": pf["harmless"]["mean"] - pb["harmless"]["mean"],
            "overrefusal_proj_drop": pb["overrefusal"]["mean"] - pf["overrefusal"]["mean"],
            "retained_upper_half_mean": statistics.mean(sep(r, "ft") / sep(r, "base") for r in upper if sep(r, "base")),
            "cos_upper_half_mean": statistics.mean(r["cos_r_base_r_ft"] for r in upper if r["cos_r_base_r_ft"] is not None)}


rows = []
for host, (model, recipe, seed) in HOSTS.items():
    folder = M / "tmp/sp-repr/out" / host
    if not folder.is_dir():
        continue
    for f in sorted(folder.glob("*.json")):
        try:
            rep = json.loads(f.read_text())
        except ValueError:
            continue
        if isinstance(rep, dict) and isinstance(rep.get("layers"), list) and rep["layers"] and "cos_r_base_r_ft" in rep["layers"][0]:
            s = summarize(rep)
            s.update(host=host, model=model, recipe=recipe, seed=seed, E=E.get((model, recipe, seed)),
                     adapter_sha256=(rep.get("identity") or {}).get("adapter_sha256"))
            rows.append(s)
            break
out = pathlib.Path(sys.argv[1])
out.write_text(json.dumps(rows, indent=1, sort_keys=True))
print(f"{'model':13s} {'recipe':10s} seed  E      layer  sep_base sep_ft retained cos   up-half-retained up-half-cos  harm-proj-drop")
for r in sorted(rows, key=lambda x: (x["model"], x["recipe"], x["seed"])):
    print(f"{r['model']:13s} {r['recipe']:10s} {r['seed']}  {r['E'] if r['E'] is None else round(r['E'], 1)!s:6s} {r['refusal_layer']:>3d}/{r['layers']:<3d} "
          f"{r['sep_base']:7.2f} {r['sep_ft']:7.2f} {r['retained']:7.3f} {r['cos']:6.3f}  {r['retained_upper_half_mean']:10.3f} {r['cos_upper_half_mean']:10.3f}  {r['harmful_proj_drop']:9.2f}")
print(f"units summarized: {len(rows)}")
