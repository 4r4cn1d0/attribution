"""The note's fixed family-by-recipe test (Section 4, "The logit scale and our claim rule"), as a script (stdlib only).

    python3 -I interaction_test_20261011.py --selftest
    python3 -I interaction_test_20261011.py --map MAP.json [--judge qwen3guard|harmbench]

The test, as fixed at 1B (research/side-notes/2026-10-09-llama-b-seeds-results.md; the note's Section 4):
  - each fine-tuned seed gives U, the Unsafe share of its 600 sampled answers (Qwen3Guard: summary.json
    harm.sampled.unsafe / answers; HarmBench: the judge file's sampled harm / n);
  - per family, D = mean(logit U | Scheduled) - mean(logit U | Constant), with variance var_C/n_C + var_S/n_S
    (sample variances of the per-seed logits);
  - the interaction I = D_OLMo - D_Llama, SE = sqrt(sum of the four var/n), Welch-Satterthwaite df =
    (sum v)^2 / sum(v^2 / (n - 1)), and a 95% interval with the Student t quantile at that df;
  - the claim "the recipe effect differs between the families" only if the 95% interval excludes 0;
  - the same contrast in percentage points (means of 100 U) is reported beside it.
MAP.json: {"cells": {"olmo_constant": [UNIT, ...], "olmo_scheduled": [...], "llama_constant": [...],
"llama_scheduled": [...]}} where UNIT = {"eval": ".../eval/e1", "harmbench": JUDGE_FILE or null}.
--selftest reruns the 1B test on its recorded counts (Appendix A) and must reproduce -0.57 (SE 0.17, df 5.1,
95% -1.02 to -0.13) and -14.1 pp (SE 3.7). Counts only; never reads prompt or answer text.
"""
import argparse
import json
import math
import pathlib
import statistics
import sys

CELLS = ("olmo_constant", "olmo_scheduled", "llama_constant", "llama_scheduled")


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


def shares_from_map(path: pathlib.Path, judge: str) -> dict:
    m = json.loads(path.read_text())
    shares = {}
    for c in CELLS:
        shares[c] = []
        for unit in m["cells"][c]:
            if judge == "qwen3guard":
                s = json.loads((pathlib.Path(unit["eval"]) / "summary.json").read_text())["harm"]["sampled"]
                assert s["answers"] == 600, unit
                shares[c].append(s["unsafe"] / s["answers"])
            else:
                j = json.loads(pathlib.Path(unit["harmbench"]).read_text())["sampled"]
                assert j["n"] == 600 and j["unparsed"] == 0, unit
                shares[c].append(j["harm"] / j["n"])
    return shares


def selftest() -> None:
    counts = {"olmo_constant": [280, 281, 308], "olmo_scheduled": [193, 205, 178],
              "llama_constant": [458, 451, 407], "llama_scheduled": [443, 422, 412]}
    r = test({c: [x / 600 for x in v] for c, v in counts.items()})
    lg, pp = r["logit"], r["pp"]
    got = (round(lg["interaction"], 2), round(lg["se"], 2), round(lg["welch_df"], 1), round(lg["ci95"][0], 2),
           round(lg["ci95"][1], 2), round(pp["interaction"], 1), round(pp["se"], 1))
    want = (-0.57, 0.17, 5.1, -1.02, -0.13, -14.1, 3.7)
    assert got == want, (got, want)
    print("selftest ok: the 1B test reproduced", got)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--map", type=pathlib.Path)
    ap.add_argument("--judge", choices=("qwen3guard", "harmbench"), default="qwen3guard")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    print(json.dumps(test(shares_from_map(a.map, a.judge)), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
