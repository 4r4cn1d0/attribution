"""Over-refusal label check for review B item 1 / W7 (labels only; counts printed; no text read or printed).

Reads only the fields `kind`, `prompt_id`, `valid` and `refusal` of each unit's greedy guard file
(`eval/<ckpt>/guard.jsonl`, Qwen3Guard response-moderation labels) for the 100 dev over-refusal prompts.
The judge's own output string and every other field are never read. Denominator 100; an invalid answer counts
as not refused (Gate B PREREG revision 5 §6, "Ref").

Run:  python3 -I or_labels_check.py
"""
import itertools
import json
import math
import pathlib
import statistics

T = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp")
UNITS = {
    "untuned": T / "family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1/eval/init/guard.jsonl",
    "B-1101": T / "family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl",
    "B-1102": T / "family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard.jsonl",
    "B-1103": T / "family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard.jsonl",
    "G-1101": T / "family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl",
    "G-1102": T / "family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard.jsonl",
    "G-1103": T / "family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard.jsonl",
    "bt-1101": T / "family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl",
    "bt-1102": T / "family-probe-sp-olmo2-1b-bt-seed1102/retrieved/sp-olmo2-1b-bt-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard.jsonl",
    "bt-1103": T / ("gi-v-steps-4-9/step4-backups/stage/side-kits/family-probe-sp-olmo2-1b-bt-seed1103/retrieved/"
                    "sp-olmo2-1b-bt-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard.jsonl"),
    "G16-1101": T / "family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl",
}


def labels(path):
    out, invalid = {}, 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("kind") != "overrefusal":
                continue
            ok = r.get("valid") is True
            invalid += not ok
            out[r["prompt_id"]] = 1 if (ok and r.get("refusal") == "Yes") else 0
    return out, invalid


lab = {}
for name, p in UNITS.items():
    if not p.exists():
        print(f"{name}: MISSING")
        continue
    lab[name], inv = labels(p)
    print(f"{name}: n={len(lab[name])} refused={sum(lab[name].values())} invalid={inv}")

ids = sorted(lab["untuned"])
assert all(sorted(v) == ids for v in lab.values()), "prompt id sets differ"
P = len(ids)


def rate(u):
    return 100.0 * sum(lab[u].values()) / P


def disc(a, b):
    """Return (a refuses only, b refuses only, both) counts."""
    a_only = sum(1 for i in ids if lab[a][i] and not lab[b][i])
    b_only = sum(1 for i in ids if lab[b][i] and not lab[a][i])
    both = sum(1 for i in ids if lab[a][i] and lab[b][i])
    return a_only, b_only, both


print("\nPairwise (row-only, column-only, both) refusals:")
for a, b in [("untuned", "B-1101"), ("untuned", "B-1102"), ("untuned", "B-1103"),
             ("untuned", "G-1101"), ("untuned", "G-1102"), ("untuned", "G-1103"),
             ("B-1101", "B-1102"), ("B-1101", "B-1103"), ("B-1102", "B-1103"),
             ("G-1101", "G-1102"), ("G-1101", "G-1103"), ("G-1102", "G-1103"),
             ("bt-1101", "bt-1102"), ("bt-1101", "bt-1103"), ("bt-1102", "bt-1103")]:
    if a in lab and b in lab:
        print(f"  {a} vs {b}: {disc(a, b)}")

for fam in ("B", "G", "bt"):
    seeds = [u for u in lab if u.startswith(fam + "-")]
    rs = [rate(u) for u in seeds]
    sd = statistics.stdev(rs) if len(rs) > 1 else float("nan")
    union = sum(1 for i in ids if any(lab[u][i] for u in seeds))
    any_untuned = sum(1 for i in ids if any(lab[u][i] for u in seeds) and lab["untuned"][i])
    print(f"\nrecipe {fam}: per-seed rates {rs}; mean {statistics.mean(rs):.2f}; seed SD {sd:.2f} pp (df {len(rs)-1});"
          f" prompts refused by any seed {union}; of those also refused untuned {any_untuned}")
    # per-prompt seed variance -> binomial-style per-seed SD if prompts independent
    vbar = statistics.mean(statistics.pvariance([lab[u][i] for u in seeds]) * len(seeds) / (len(seeds) - 1) for i in ids)
    print(f"  mean per-prompt seed variance {vbar:.4f}; implied per-seed rate SD if prompt flips independent"
          f" {100*math.sqrt(vbar/P):.2f} pp")

# MDE / non-inferiority planning for a 6-vs-6 arm contrast, seed-only noise (prompts fixed), and
# a prompt-heterogeneity term for an arm whose true shift is concentrated on k prompts.
print("\nPlanning (normal approximation):")
for sd in (1.15, 2.1, 3.0):
    se66 = sd * math.sqrt(2 / 6)
    se6u = sd * math.sqrt(1 / 6)       # arm vs the single, deterministic untuned unit
    print(f"  per-seed SD {sd:.2f} pp: SE(6 vs 6) {se66:.2f}; MDE80 two-sided 5% {2.80*se66:.2f};"
          f" SE(6 vs untuned) {se6u:.2f}; NI power at true 0, tau 2/5/10:"
          + ", ".join(f"{0.5*(1+math.erf(((t/se66)-1.645)/math.sqrt(2))):.2f}" for t in (2, 5, 10)))
for k in (5, 12, 20):
    p = k / P
    het = math.sqrt(p * (1 - p) / P) * 100
    print(f"  prompt-random heterogeneity, true shift on {k} of {P} prompts: extra SE {het:.2f} pp;"
          f" with 1,469 prompts {math.sqrt(p*(1-p)/1469)*100:.2f} pp")


# Prompt-clustered (prompts random) SE of an arm-mean contrast, from per-prompt seed means.
def pmean(prefix):
    seeds = [u for u in lab if u.startswith(prefix + "-")]
    return {i: sum(lab[u][i] for u in seeds) / len(seeds) for i in ids}, len(seeds)


print("\nPrompt-clustered contrasts (per-prompt seed means; SE = SD(d_p)/sqrt(P)):")
ref = {"untuned": ({i: lab["untuned"][i] for i in ids}, 1)}
arms = {f: pmean(f) for f in ("B", "G", "bt")}
arms.update(ref)
for a, b in [("B", "untuned"), ("G", "untuned"), ("bt", "untuned"), ("G", "B"), ("bt", "B")]:
    qa, na = arms[a]
    qb, nb = arms[b]
    d = [qa[i] - qb[i] for i in ids]
    m = statistics.mean(d)
    se = statistics.stdev(d) / math.sqrt(P)
    print(f"  {a}({na}) - {b}({nb}): {100*m:+.2f} pp, prompt-clustered SE {100*se:.2f} pp;"
          f" scaled to 1,569 prompts {100*se*math.sqrt(P/1569):.2f}; to 500 prompts {100*se*math.sqrt(P/500):.2f}")
