"""Original registered Welch/logit arithmetic, copied without dataset access."""
import math,statistics
CELLS=("olmo_constant","olmo_scheduled","llama_constant","llama_scheduled")

def t_quantile(df, q=0.975):
    """Student t quantile by bisection on the CDF (regularized incomplete beta, continued fraction)."""
    def betacf(a, b, x):
        tiny = 1e-300
        c, d = 1.0, 1.0 - (a + b) * x / (a + 1)
        d = 1 / (d if abs(d) > tiny else tiny)
        h = d
        for m in range(1, 300):
            m2 = 2 * m
            for aa in (m * (b - m) * x / ((a + m2 - 1) * (a + m2)), -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1))):
                d = 1 + aa * d
                d = 1 / (d if abs(d) > tiny else tiny)
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
        p = 0.5 * ibeta(df / 2, 0.5, df / (df + t * t))
        return 1 - p if t > 0 else p

    lo, hi = 0.0, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) < q else (lo, mid)
    return (lo + hi) / 2

def welch_contrast(values: dict) -> dict:
    """values: cell -> list of per-seed numbers. I = (S - C)_olmo - (S - C)_llama, Welch."""
    for c in CELLS:
        if len(values[c]) < 2:
            return {"tested": False, "reason": f"{c} has fewer than 2 seeds"}
    v = {c: statistics.variance(values[c]) / len(values[c]) for c in CELLS}
    d_olmo = statistics.mean(values["olmo_scheduled"]) - statistics.mean(values["olmo_constant"])
    d_llama = statistics.mean(values["llama_scheduled"]) - statistics.mean(values["llama_constant"])
    inter = d_olmo - d_llama
    se = math.sqrt(sum(v.values()))
    df = sum(v.values()) ** 2 / sum(v[c] ** 2 / (len(values[c]) - 1) for c in CELLS)
    t = t_quantile(df)
    lo, hi = inter - t * se, inter + t * se
    return {"tested": True, "olmo_change": d_olmo, "llama_change": d_llama, "interaction": inter, "se": se,
            "welch_df": df, "t975": t, "ci95": [lo, hi], "excludes_zero": lo > 0 or hi < 0,
            "seeds": {c: len(values[c]) for c in CELLS}}

def test(shares: dict) -> dict:
    logit = {c: [math.log(p / (1 - p)) for p in shares[c]] for c in CELLS}
    pp = {c: [100 * p for p in shares[c]] for c in CELLS}
    out = {"logit": welch_contrast(logit), "pp": welch_contrast(pp)}
    lg = out["logit"]
    if lg.get("tested"):
        out["label"] = ("the recipe effect differs between the families (OLMo's change is more negative)"
                        if lg["excludes_zero"] and lg["interaction"] < 0 else
                        "the recipe effect differs between the families (the opposite direction)"
                        if lg["excludes_zero"] else "not shown: the 95% interval includes 0")
    else:
        out["label"] = "not tested: " + lg["reason"]
    return out
