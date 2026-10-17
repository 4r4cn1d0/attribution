"""Gate A over-refusal and task-loss counts for the W12 / W4 checks (labels and numbers only).

Reads the sealed Gate A units (untuned init unit, a0 seeds 1101-1103 at e1) that the Gate B noise-gate inputs name.
Unit-level numbers come from scripts/family_probe_reading.py's frozen `counts` (after its `sealed` check).
Per-prompt over-refusal labels come from each unit's eval guard.jsonl, kind "overrefusal", fields prompt_id,
refusal and valid only. Nothing else is read from those records, and no prompt id, prompt or answer is printed.
Run: PYTHONDONTWRITEBYTECODE=1 <venv python> -B gate_a_overrefusal_counts.py > evidence/gate_a_overrefusal_counts.json
"""
import json, pathlib, re, sys, hashlib
from collections import Counter

MAIN = pathlib.Path("/Users/spiderishi/Coding/attribution")
sys.path.insert(0, str(MAIN / "scripts"))
import family_probe_reading as fpr  # noqa: E402  (frozen script; read-only use)

INPUTS = MAIN / "tmp/gate-b-olmo/gate_b_inputs_noise_gate_post0b.json"
inputs = json.loads(INPUTS.read_text())
units = {k: pathlib.Path(v) for k, v in inputs["gate_a"].items()}
bars_path = fpr.DEFAULT_BARS
bars = json.loads(bars_path.read_text())
assert hashlib.sha256(bars_path.read_bytes()).hexdigest() == fpr.FROZEN_BARS["family-probe-reading-amended-20261008"]


def eval_dir(unit: pathlib.Path) -> pathlib.Path:
    subs = sorted(p for p in (unit / "eval").iterdir() if p.is_dir())
    assert len(subs) == 1, unit.name
    return subs[0]


out = {"inputs_file": str(INPUTS), "inputs_sha256": hashlib.sha256(INPUTS.read_bytes()).hexdigest(),
       "bars_sha256": hashlib.sha256(bars_path.read_bytes()).hexdigest(), "units": {}, "per_prompt": {}}
labels = {}
for name, unit in units.items():
    fpr.sealed(unit)  # refuses unless the COMPLETE.json file list and hashes hold
    folder = eval_dir(unit)
    c = fpr.counts(folder, bars, "olmo2", set())
    out["units"][name] = {
        "unit": unit.name,
        "complete_sha256": hashlib.sha256((unit / "COMPLETE.json").read_bytes()).hexdigest(),
        "overrefusal": c["overrefusal"],
        "query_loss_mean": c["query_loss_mean"],
        "sampled_n": c["sampled"]["n"], "sampled_capped": c["sampled"]["capped"],
        "sampled_incoherent": c["sampled"]["incoherent"], "sampled_short_only": c["sampled"]["short_only"],
        "U_sampled": float(fpr.Fraction(c["frozen"]["sampled_unsafe"], c["frozen"]["sampled_answers"])),
        "U_clustered_se_pp": 100 * float(c["se2"]) ** 0.5,
    }
    lab = {}
    for line in (folder / "guard.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("kind") != "overrefusal":
            continue
        refused = bool(r.get("valid")) and r.get("refusal") == "Yes"  # invalid counts as not refused (PREREG G4)
        lab[r["prompt_id"]] = (refused, bool(r.get("valid")))
    labels[name] = lab

ids = sorted(set.intersection(*(set(v) for v in labels.values())))
assert all(len(v) == len(ids) for v in labels.values()), "over-refusal prompt sets differ"
# source tag: the leading letters of the id (no text); counts only
src = Counter(re.match(r"[A-Za-z]*", i).group(0)[:12] or "none" for i in ids)
out["per_prompt"]["n_prompts"] = len(ids)
out["per_prompt"]["source_tag_counts"] = dict(src)
order = ["untuned", "1101", "1102", "1103"]
vec = {k: [labels[k][i][0] for i in ids] for k in order}
out["per_prompt"]["refusals"] = {k: sum(v) for k, v in vec.items()}
out["per_prompt"]["invalid"] = {k: sum(not labels[k][i][1] for i in ids) for k in order}
by_src = {}
for tag in src:
    sel = [j for j, i in enumerate(ids) if (re.match(r"[A-Za-z]*", i).group(0)[:12] or "none") == tag]
    by_src[tag] = {k: sum(vec[k][j] for j in sel) for k in order} | {"n": len(sel)}
out["per_prompt"]["refusals_by_source_tag"] = by_src
pairs = {}
for a in order:
    for b in order:
        if a < b:
            n10 = sum(x and not y for x, y in zip(vec[a], vec[b]))
            n01 = sum(y and not x for x, y in zip(vec[a], vec[b]))
            n11 = sum(x and y for x, y in zip(vec[a], vec[b]))
            pairs[f"{a}|{b}"] = {"both": n11, "first_only": n10, "second_only": n01,
                                 "neither": len(ids) - n10 - n01 - n11}
out["per_prompt"]["pairs"] = pairs
# how many prompts each a0 seed set refuses: 0, 1, 2 or 3 of the 3 seeds
k_of = [sum(vec[s][j] for s in ("1101", "1102", "1103")) for j in range(len(ids))]
out["per_prompt"]["a0_seeds_refusing_hist"] = dict(Counter(k_of))
out["per_prompt"]["untuned_refused_by_a0_count"] = dict(Counter(k for k, u in zip(k_of, vec["untuned"]) if u))
print(json.dumps(out, indent=1, sort_keys=True))
