"""Exploratory analyses of 11 Oct 2026 (not pre-registered; labels and counts only, never prompt or answer text).

    python3 -I explore_20261011.py OUT_DIR

Finds every sealed fine-tuned unit under the main checkout's tmp/*/retrieved/*/tree/round1/*-a0-e1-a1, classifies it
by its host name (model, recipe, seed), and pairs it with its model's untuned unit. Writes OUT_DIR/units.csv and
OUT_DIR/explore.json, and prints a summary:
  1. safety cost per unit of learning: E against the held-out-loss drop, per model and recipe;
  2. selectivity: per recipe change, the change in E against the change in benign over-refusal;
  3. prompt-level paired recipe effect (seed-averaged per-prompt Unsafe rates; a prompt bootstrap, so the interval is
     conditional on these seeds) and the OLMo-minus-Llama interaction per size;
  4. overlap of the prompts that erode (seed-mean Unsafe rate >= 2/3 under Constant) across models (Jaccard);
  5. untuned baselines per model (U, over-refusal, refusal flag on harm prompts).
"""
import csv
import json
import math
import pathlib
import random
import re
import statistics
import sys

T = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp")
OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

# (regex on the host name, model, recipe); first match wins
RULES = [
    (r"^olmo2-1b-(110\d)$", "OLMo-2-1B", "Constant"), (r"^olmo2-1b-g-(110\d)$", "OLMo-2-1B", "Scheduled"),
    (r"^(?:sp-)?olmo2-1b-bt-(110\d)$", "OLMo-2-1B", "Constant token-mean"),
    (r"^llama32-1b-(110\d)$", "Llama-3.2-1B", "Constant"), (r"^sp-llama32-1b-b2?-(110\d)$", "Llama-3.2-1B", "Constant"),
    (r"^llama32-1b-g5-(110\d)$", "Llama-3.2-1B", "Scheduled"), (r"^llama32-1b-g-(110\d)$", "Llama-3.2-1B", "Scheduled"),
    (r"^sp-qwen15-b-(110\d)$", "Qwen2.5-1.5B", "Constant"), (r"^sp-qwen15-g-(110\d)$", "Qwen2.5-1.5B", "Scheduled"),
    (r"^sp-olmo2-7b-b2-(110\d)$", "OLMo-2-7B", "Constant"), (r"^sp-olmo2-7b-(110\d)$", "OLMo-2-7B", "Constant"),
    (r"^sp-olmo2-7b-g-(110\d)$", "OLMo-2-7B", "Scheduled"), (r"^sp-olmo2-7b-b5e5-(110\d)$", "OLMo-2-7B", "Constant half LR"),
    (r"^sp-llama31-8b-(110\d)$", "Llama-3.1-8B", "Constant"), (r"^sp-llama31-8b-g-(110\d)$", "Llama-3.1-8B", "Scheduled"),
    (r"^sp-llama31-8b-b5e5-(110\d)$", "Llama-3.1-8B", "Constant half LR"),
    (r"^sp-qwen7-b-(110\d)$", "Qwen2.5-7B", "Constant"), (r"^sp-qwen7-g-(110\d)$", "Qwen2.5-7B", "Scheduled"),
]
UNTUNED = {"OLMo-2-1B": "olmo2-1b-1101", "Llama-3.2-1B": "llama32-1b-1101", "Qwen2.5-1.5B": "sp-qwen15-b-1101",
           "OLMo-2-7B": "sp-olmo2-7b-b2-1101", "Llama-3.1-8B": "sp-llama31-8b-1101", "Qwen2.5-7B": "sp-qwen7-b-1101"}
FAMILY = {m: m.split("-")[0].replace("Qwen2.5", "Qwen") for m in UNTUNED}
SIZE = {"OLMo-2-1B": "1B", "Llama-3.2-1B": "1B", "Qwen2.5-1.5B": "1B", "OLMo-2-7B": "7-8B", "Llama-3.1-8B": "7-8B",
        "Qwen2.5-7B": "7-8B"}


def eval_stats(ev: pathlib.Path) -> dict:
    s = json.loads((ev / "summary.json").read_text())
    per_prompt, unsafe, refused, cats = {}, 0, 0, {}
    for line in (ev / "guard_samples.jsonl").read_text().splitlines():
        r = json.loads(line)
        u = bool(r.get("valid")) and r.get("safety") == "Unsafe"
        per_prompt.setdefault(r["prompt_id"], []).append(1 if u else 0)
        unsafe += u
        refused += r.get("refusal") == "Yes"
        if u:
            for c in r.get("categories") or []:
                cats[c] = cats.get(c, 0) + 1
    toks, capped = [], 0
    for line in (ev / "samples.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("kind", "harm") == "harm":
            toks.append(r.get("output_tokens", 0))
            capped += "cap" in str(r.get("stop_reason", ""))
    n = sum(len(v) for v in per_prompt.values())
    assert n == 600 and unsafe == s["harm"]["sampled"]["unsafe"], (ev, n, unsafe, s["harm"]["sampled"]["unsafe"])
    return {"U": unsafe / n, "refusal_flag": refused / n, "loss": s["query_loss"]["mean"],
            "overrefusal": s["overrefusal"]["refusal_rate"], "per_prompt": {k: sum(v) / len(v) for k, v in per_prompt.items()},
            "categories": cats, "mean_tokens": statistics.mean(toks) if toks else None, "capped_share": capped / len(toks) if toks else None}


units, untuned = [], {}
for summ in sorted(T.glob("*/retrieved/*/tree/round1/*-a0-*-a1/eval/*/summary.json")):
    ev = summ.parent
    host = summ.parts[summ.parts.index("retrieved") + 1]
    unit = ev.parent.parent.name
    if unit.endswith("-a0-init-a1"):
        for m, h in UNTUNED.items():
            if host == h and m not in untuned:
                untuned[m] = eval_stats(ev)
        continue
    for pat, model, recipe in RULES:
        mm = re.match(pat, host)
        if mm and unit.startswith(mm.group(1)):
            units.append({"model": model, "recipe": recipe, "seed": int(mm.group(1)), "host": host, "eval": ev})
            break
# one unit per (model, recipe, seed): keep the first found
seen, kept = set(), []
for u in units:
    key = (u["model"], u["recipe"], u["seed"])
    if key not in seen:
        seen.add(key)
        kept.append(u)
for u in kept:
    u.update(eval_stats(u["eval"]))
    b = untuned[u["model"]]
    u["E"] = 100 * (u["U"] - b["U"])
    u["loss_drop"] = b["loss"] - u["loss"]
    u["d_overrefusal"] = 100 * (u["overrefusal"] - b["overrefusal"])

with open(OUT / "units.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["model", "family", "size", "recipe", "seed", "U", "E_pp", "loss", "loss_drop", "overrefusal", "d_overrefusal_pp",
                "refusal_flag", "mean_tokens", "capped_share"])
    for u in sorted(kept, key=lambda x: (x["model"], x["recipe"], x["seed"])):
        w.writerow([u["model"], FAMILY[u["model"]], SIZE[u["model"]], u["recipe"], u["seed"], f"{u['U']:.4f}", f"{u['E']:.2f}",
                    f"{u['loss']:.4f}", f"{u['loss_drop']:.4f}", f"{u['overrefusal']:.3f}", f"{u['d_overrefusal']:.1f}",
                    f"{u['refusal_flag']:.3f}", f"{u['mean_tokens']:.0f}", f"{u['capped_share']:.3f}"])

cells = {}
for u in kept:
    cells.setdefault((u["model"], u["recipe"]), []).append(u)
res = {"units": len(kept), "cells": {f"{m} | {r}": len(v) for (m, r), v in sorted(cells.items())}}

# 1 and 2: cell means
summary = {}
for (m, r), v in sorted(cells.items()):
    summary[f"{m} | {r}"] = {k: round(statistics.mean(x[k] for x in v), 3) for k in ("E", "loss_drop", "d_overrefusal", "mean_tokens", "capped_share")}
    summary[f"{m} | {r}"]["n"] = len(v)
res["cell_means"] = summary
changes = {}
for m in UNTUNED:
    c = cells.get((m, "Constant"))
    for r in ("Scheduled", "Constant half LR", "Constant token-mean"):
        s = cells.get((m, r))
        if c and s:
            mc, ms = (lambda key, xs: statistics.mean(x[key] for x in xs)), None
            changes[f"{m}: {r} minus Constant"] = {
                "dE_pp": round(mc("E", s) - mc("E", c), 2), "d_loss_drop": round(mc("loss_drop", s) - mc("loss_drop", c), 4),
                "d_overrefusal_pp": round(mc("d_overrefusal", s) - mc("d_overrefusal", c), 2),
                "E_per_loss_drop_constant": round(mc("E", c) / mc("loss_drop", c), 1),
                "seeds": [len(c), len(s)]}
res["recipe_changes"] = changes


# 3: prompt-level paired recipe effect, prompt bootstrap (conditional on the seeds)
def prompt_means(xs):
    keys = xs[0]["per_prompt"].keys()
    return {k: statistics.mean(x["per_prompt"][k] for x in xs) for k in keys}


rng = random.Random(20261011)
paired = {}
for m in UNTUNED:
    c, s = cells.get((m, "Constant")), cells.get((m, "Scheduled"))
    if not (c and s):
        continue
    pc, ps = prompt_means(c), prompt_means(s)
    keys = sorted(pc)
    diffs = [ps[k] - pc[k] for k in keys]
    boots = []
    for _ in range(2000):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        boots.append(100 * statistics.mean(sample))
    boots.sort()
    paired[m] = {"diffs": diffs, "mean_pp": round(100 * statistics.mean(diffs), 2), "ci95_pp": [round(boots[50], 2), round(boots[1949], 2)],
                 "prompts_lower": sum(d < 0 for d in diffs), "prompts_higher": sum(d > 0 for d in diffs), "seeds": [len(c), len(s)]}
inter = {}
for a, b, size in (("OLMo-2-1B", "Llama-3.2-1B", "1B"), ("OLMo-2-7B", "Llama-3.1-8B", "7-8B"),
                   ("OLMo-2-1B", "Qwen2.5-1.5B", "1B"), ("Qwen2.5-1.5B", "Llama-3.2-1B", "1B"),
                   ("OLMo-2-7B", "Qwen2.5-7B", "7-8B"), ("Qwen2.5-7B", "Llama-3.1-8B", "7-8B")):
    if a in paired and b in paired:
        da, db = paired[a]["diffs"], paired[b]["diffs"]
        d = [x - y for x, y in zip(da, db)]   # the same prompt ids, sorted alike
        boots = sorted(100 * statistics.mean(d[rng.randrange(len(d))] for _ in d) for _ in range(2000))
        inter[f"{a} minus {b} ({size})"] = {"mean_pp": round(100 * statistics.mean(d), 2), "ci95_pp": [round(boots[50], 2), round(boots[1949], 2)]}
res["paired_recipe_effect"] = {k: {kk: vv for kk, vv in v.items() if kk != "diffs"} for k, v in paired.items()}
res["paired_interactions"] = inter

# 4: overlap of eroded prompts under Constant
eroded = {}
for m in UNTUNED:
    c = cells.get((m, "Constant"))
    if c:
        pm = prompt_means(c)
        eroded[m] = {k for k, v in pm.items() if v >= 2 / 3}
ov = {}
ms = sorted(eroded)
for i, a in enumerate(ms):
    for b in ms[i + 1:]:
        uni = eroded[a] | eroded[b]
        ov[f"{a} vs {b}"] = round(len(eroded[a] & eroded[b]) / len(uni), 3) if uni else None
res["eroded_prompt_counts"] = {m: len(v) for m, v in eroded.items()}
res["eroded_overlap_jaccard"] = ov

# 5: untuned baselines
res["untuned"] = {m: {"U": round(100 * b["U"], 2), "overrefusal": round(100 * b["overrefusal"], 1), "refusal_flag": round(100 * b["refusal_flag"], 1),
                      "loss": round(b["loss"], 4), "mean_tokens": round(b["mean_tokens"] or 0)} for m, b in untuned.items()}
(OUT / "explore.json").write_text(json.dumps(res, indent=1, sort_keys=True))
print(json.dumps(res, indent=1, sort_keys=True))
