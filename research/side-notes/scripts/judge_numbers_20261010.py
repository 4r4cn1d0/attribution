"""Derived judge numbers for the note (10 Oct): E_HB per seed and mean/SD for OLMo B, G, bt and Llama B, G; Granite
greedy E for OLMo bt; the fixed logit-scale interaction test (OLMo change minus Llama change, Welch) on HarmBench.
Reads judge files only (counts). python3 -I judge_numbers.py"""
import json
import math
import pathlib
import statistics

J = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp/judge-pod")


def count(run, group, host, unit, mode="sampled"):
    files = list((J / run / f"judges-{group}").glob(f"*--{host}--{unit}--*.json"))
    assert len(files) == 1, (run, group, host, unit, files)
    d = json.loads(files[0].read_text())
    return d[mode]["harm"], d[mode]["n"]


HB = {
    "olmo_untuned": ("sp-hb-fiction-bt-llama-1", "olmo-D", "olmo2-1b-1101", "1101-a0-init-a1"),
    "olmo_B": [("sp-hb-fiction-bt-llama-1", "olmo-D", "olmo2-1b-1101", "1101-a0-e1-a1"),
               ("sp-hb-fiction-bt-llama-1", "olmo-D", "olmo2-1b-1102", "1102-a0-e1-a1"),
               ("sp-hb-fiction-bt-llama-1", "olmo-D", "olmo2-1b-1103", "1103-a0-e1-a1")],
    "olmo_G": [("olmo-b-g-untuned", "G", "olmo2-1b-g-1101", "1101-a0-e1-a1"),
               ("olmo-b-g-untuned", "G", "olmo2-1b-g-1102", "1102-a0-e1-a1"),
               ("olmo-b-g-untuned", "G", "olmo2-1b-g-1103", "1103-a0-e1-a1")],
    "olmo_bt": [("sp-hb-fiction-bt-llama-1", "olmo-bt", "olmo2-1b-bt-1101", "1101-a0-e1-a1"),
                ("sp-hb-fiction-bt-llama-1", "olmo-bt", "sp-olmo2-1b-bt-1102", "1102-a0-e1-a1"),
                ("sp-hb-fiction-bt-llama-1", "olmo-bt", "sp-olmo2-1b-bt-1103", "1103-a0-e1-a1")],
    "llama_untuned": ("sp-hb-fiction-bt-llama-1", "llama-B", "llama32-1b-1101", "1101-a0-init-a1"),
    "llama_B": [("side-qwen-llama-pairs", "llama-B", "llama32-1b-1101", "1101-a0-e1-a1"),
                ("sp-hb-fiction-bt-llama-1", "llama-B", "sp-llama32-1b-b2-1102", "1102-a0-e1-a1"),
                ("sp-hb-fiction-bt-llama-1", "llama-B", "sp-llama32-1b-b-1103", "1103-a0-e1-a1")],
    "llama_G": [("side-qwen-llama-pairs", "llama-G", "llama32-1b-g5-1101", "1101-a0-e1-a1"),
                ("side-qwen-llama-pairs", "llama-G", "llama32-1b-g-1102", "1102-a0-e1-a1"),
                ("sp-hb-fiction-bt-llama-1", "llama-G", "llama32-1b-g-1103", "1103-a0-e1-a1")],
}
# the untuned units judged in the other runs must equal the ones used here (one device type, deterministic labels)
assert count("olmo-b-g-untuned", "B", "olmo2-1b-1101", "1101-a0-init-a1") == count(*HB["olmo_untuned"])
assert count("side-qwen-llama-pairs", "llama-B", "llama32-1b-1101", "1101-a0-init-a1") == count(*HB["llama_untuned"])
out = {}
shares = {}
for fam in ("olmo", "llama"):
    h0, n0 = count(*HB[f"{fam}_untuned"])
    out[f"{fam}_untuned_HB_pct"] = round(100 * h0 / n0, 3)
    for rec in ("B", "G", "bt"):
        key = f"{fam}_{rec}"
        if key not in HB:
            continue
        cs = [count(*x) for x in HB[key]]
        e = [100 * (h / n - h0 / n0) for h, n in cs]
        shares[key] = [h / n for h, n in cs]
        out[key] = {"counts": [f"{h}/{n}" for h, n in cs], "E_HB": [round(x, 2) for x in e],
                    "mean": round(statistics.mean(e), 2), "sd": round(statistics.stdev(e), 2)}
# Granite greedy, OLMo bt on the pod against the pod-judged untuned unit
g0 = count("sp-granite-fiction-bt-1", "olmo-untuned", "olmo2-1b-1101", "1101-a0-init-a1", "greedy")
gb = [count("sp-granite-fiction-bt-1", "olmo-bt", h, u, "greedy") for _, _, h, u in HB["olmo_bt"]]
ge = [100 * (h / n - g0[0] / g0[1]) for h, n in gb]
out["olmo_bt_granite"] = {"untuned": f"{g0[0]}/{g0[1]}", "counts": [f"{h}/{n}" for h, n in gb],
                          "E": [round(x, 2) for x in ge], "mean": round(statistics.mean(ge), 2)}
# fiction Granite greedy (direction check)
for arm in ("dark", "light"):
    a0 = count("sp-granite-fiction-bt-1", f"fiction-{arm}", f"sp-fic-{arm}-1101", "1101-a0-init-a1", "greedy")
    seeds = [count("sp-granite-fiction-bt-1", f"fiction-{arm}", f"sp-fic-{arm}-{s}", f"{s}-a0-e1-a1", "greedy")
             for s in (1101, 1102, 1103)]
    e = [100 * (h / n - a0[0] / a0[1]) for h, n in seeds]
    out[f"fiction_{arm}_granite"] = {"a0": f"{a0[0]}/{a0[1]}", "E": [round(x, 2) for x in e], "mean": round(statistics.mean(e), 2)}


def logit(p):
    return math.log(p / (1 - p))


def welch_t_quantile(df, q=0.975):
    # bisection on the Student t CDF via the regularized incomplete beta (continued fraction)
    def betacf(a, b, x):
        tiny = 1e-300
        c, d = 1.0, 1.0 - (a + b) * x / (a + 1)
        d = 1 / (d if abs(d) > tiny else tiny)
        h = d
        for m in range(1, 300):
            m2 = 2 * m
            aa = m * (b - m) * x / ((a + m2 - 1) * (a + m2))
            d = 1 + aa * d; d = 1 / (d if abs(d) > tiny else tiny)
            c = 1 + aa / c if abs(c) > tiny else 1 + aa / tiny
            h *= d * c
            aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1))
            d = 1 + aa * d; d = 1 / (d if abs(d) > tiny else tiny)
            c = 1 + aa / c if abs(c) > tiny else 1 + aa / tiny
            h *= d * c
        return h

    def ibeta(a, b, x):
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
        if x < (a + 1) / (a + b + 2):
            return math.exp(lbt) * betacf(a, b, x) / a
        return 1 - math.exp(lbt) * betacf(b, a, 1 - x) / b

    def cdf(t):
        x = df / (df + t * t)
        p = 0.5 * ibeta(df / 2, 0.5, x)
        return 1 - p if t > 0 else p

    lo, hi = 0.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) < q else (lo, mid)
    return (lo + hi) / 2


comp = {}
for fam in ("olmo", "llama"):
    lb = [logit(p) for p in shares[f"{fam}_B"]]
    lg = [logit(p) for p in shares[f"{fam}_G"]]
    comp[fam] = (statistics.mean(lg) - statistics.mean(lb), statistics.variance(lb) / 3, statistics.variance(lg) / 3)
inter = comp["olmo"][0] - comp["llama"][0]
vs = [comp["olmo"][1], comp["olmo"][2], comp["llama"][1], comp["llama"][2]]
se = math.sqrt(sum(vs))
df = sum(vs) ** 2 / sum(v * v / 2 for v in vs)
t = welch_t_quantile(df)
pp_o = statistics.mean([100 * p for p in shares["olmo_G"]]) - statistics.mean([100 * p for p in shares["olmo_B"]])
pp_l = statistics.mean([100 * p for p in shares["llama_G"]]) - statistics.mean([100 * p for p in shares["llama_B"]])
pp_vs = [statistics.variance([100 * p for p in shares[k]]) / 3 for k in ("olmo_B", "olmo_G", "llama_B", "llama_G")]
pp_se = math.sqrt(sum(pp_vs))
pp_df = sum(pp_vs) ** 2 / sum(v * v / 2 for v in pp_vs)
pp_t = welch_t_quantile(pp_df)
out["hb_interaction_logit"] = {"olmo_change": round(comp["olmo"][0], 4), "llama_change": round(comp["llama"][0], 4),
                               "interaction": round(inter, 4), "se": round(se, 4), "welch_df": round(df, 2), "t975": round(t, 4),
                               "ci95": [round(inter - t * se, 3), round(inter + t * se, 3)]}
out["hb_interaction_pp"] = {"olmo_change": round(pp_o, 3), "llama_change": round(pp_l, 3), "interaction": round(pp_o - pp_l, 3),
                            "se": round(pp_se, 3), "welch_df": round(pp_df, 2),
                            "ci95": [round(pp_o - pp_l - pp_t * pp_se, 3), round(pp_o - pp_l + pp_t * pp_se, 3)]}
out["ratios"] = {"olmo_G_over_B": round(out["olmo_G"]["mean"] / out["olmo_B"]["mean"], 3),
                 "llama_G_over_B": round(out["llama_G"]["mean"] / out["llama_B"]["mean"], 3),
                 "bt_share_of_cut": round((out["olmo_B"]["mean"] - out["olmo_bt"]["mean"]) / (out["olmo_B"]["mean"] - out["olmo_G"]["mean"]), 3)}
print(json.dumps(out, indent=1))
