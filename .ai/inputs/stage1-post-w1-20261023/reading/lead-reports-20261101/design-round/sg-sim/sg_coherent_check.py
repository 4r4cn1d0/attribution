"""Synthetic check of two item-part forms for S-G's coherent-only U (no study data; pure Python; reads no file).

Re-implements B16's formulas (contrast.two_way_ms, item_part, satterthwaite_df; the two-arm paired seed part)
so that nothing is imported from the repository.

Forms compared, on the pooled coherent-only cell value V(a, j) = 100 * sum_p u / sum_p n:
  D  the design's form: item part from y = u / n on the prompts where both arms have n > 0 at every seed (P_k)
  L  linearized form: item part from x = V/100 + (u - V/100 * n) / (N / P) on all P prompts (no drop)
  plain: B16's primary form on the plain share (all answers), as a control.
Seed part (all forms): the two-arm sum rule (var of the cell differences, ddof 1, floored at 0.01 pp^2) / J, J - 1 df.
"""

import math
import random
import sys
from fractions import Fraction as Fr


# ----- Student t (regularized incomplete beta by Lentz's continued fraction) -----------------------------------
def _betacf(a, b, x):
    tiny, eps = 1e-300, 3e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1.0 - x) / b


def t_cdf(t, df):
    if math.isinf(df):
        return 0.5 * math.erfc(-t / math.sqrt(2.0))
    x = df / (df + t * t)
    tail = 0.5 * betai(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_quantile(p, df):
    lo, hi = -1e4, 1e4
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ----- B16's formulas, re-implemented -----------------------------------------------------------------------
def two_way_ms(d):
    j, p = len(d), len(d[0])
    grand = sum(map(sum, d)) / (j * p)
    row = [sum(r) / p for r in d]
    col = [sum(d[i][k] for i in range(j)) / j for k in range(p)]
    ms_p = j * sum((c - grand) ** 2 for c in col) / (p - 1)
    ss_e = sum((d[i][k] - row[i] - col[k] + grand) ** 2 for i in range(j) for k in range(p))
    ms_e = ss_e / ((p - 1) * (j - 1))
    return ms_p, ms_e


def item_part(d, scale=100.0):
    j, p = len(d), len(d[0])
    ms_p, ms_e = two_way_ms(d)
    k = scale * scale / (p * j)
    v_item = max(0.0, ms_p - ms_e) * k
    q = (ms_p * k) ** 2 / (p - 1) + (ms_e * k) ** 2 / ((p - 1) * (j - 1)) if ms_p > ms_e else 0.0
    return v_item, q


def assemble(est, v_seed, df_seed, d):
    v_item, q = item_part(d)
    v = v_seed + v_item
    den = v_seed * v_seed / df_seed + q
    df = v * v / den if den > 0 else float("inf")
    return est, math.sqrt(v), df, v_item


def seed_part(diffs, floor=0.01):
    j = len(diffs)
    m = sum(diffs) / j
    var = sum((x - m) ** 2 for x in diffs) / (j - 1)
    return max(var, floor) / j, float(j - 1)


# ----- the hand counterexample (exact, with fractions) ------------------------------------------------------------
def hand_case():
    """2 arms, 2 seeds, 4 prompts x 3 answers. Prompt 1: every answer Unsafe in both arms when coherent; prompts
    2-4: every answer Safe. Comparator c: every answer coherent. Repair m: on prompt 1 all 3 answers fail the screen
    at both seeds. Plain U is 25% in both arms."""
    seeds, P = 2, 4
    n = {"c": [[3, 3, 3, 3]] * seeds, "m": [[0, 3, 3, 3]] * seeds}
    u = {"c": [[3, 0, 0, 0]] * seeds, "m": [[0, 0, 0, 0]] * seeds}
    V = {a: [Fr(sum(u[a][j]), sum(n[a][j])) for j in range(seeds)] for a in ("c", "m")}
    diffs = [100 * (V["c"][j] - V["m"][j]) for j in range(seeds)]
    est = sum(diffs) / seeds
    v_seed, df_seed = seed_part([float(x) for x in diffs])
    keep = [p for p in range(P) if all(n["c"][j][p] > 0 and n["m"][j][p] > 0 for j in range(seeds))]
    d_design = [[float(Fr(u["c"][j][p], n["c"][j][p]) - Fr(u["m"][j][p], n["m"][j][p])) for p in keep] for j in range(seeds)]
    design = assemble(float(est), v_seed, df_seed, d_design)

    def x(a, j, p):
        nbar = Fr(sum(n[a][j]), P)
        return V[a][j] + (u[a][j][p] - V[a][j] * n[a][j][p]) / nbar

    d_lin = [[float(x("c", j, p) - x("m", j, p)) for p in range(P)] for j in range(seeds)]
    lin = assemble(float(est), v_seed, df_seed, d_lin)
    out = []
    for name, (e, se, df, vi) in (("design (drop, y on kept prompts)", design), ("linearized (no drop)", lin)):
        half = t_quantile(0.95, df) * se
        p_two = 2.0 * (1.0 - t_cdf(abs(e / se), df))
        out.append(f"  {name}: estimate {e:.2f} pp, SE {se:.4f} pp (item part {vi:.4f} pp^2), df {df:.3f}, "
                   f"90% interval [{e - half:.2f}, {e + half:.2f}], two-sided p {p_two:.4g}")
    matched = sum(map(sum, d_design)) / (len(d_design) * len(d_design[0])) * 100
    out.append(f"  kept prompts {len(keep)} of {P}; the design's matched estimate {matched:.2f} pp; plain U contrast 0.00 pp")
    return out


# ----- the simulation ------------------------------------------------------------------------------------------
def expit(z):
    return 1.0 / (1.0 + math.exp(-z))


def one_rep(rng, scenario, P=200, J=6, frac_f=0.08, arm_seed_sd=0.15):
    eta = [rng.gauss(-0.2, 2.5) for _ in range(P)]
    gam = {a: [rng.gauss(0.0, 0.3) for _ in range(P)] for a in ("c", "m")}
    s = [rng.gauss(0.0, 0.25) for _ in range(J)]
    e = {a: [rng.gauss(0.0, arm_seed_sd) for _ in range(J)] for a in ("c", "m")}
    if scenario == "A":                       # independent failures, both arms
        fail = {"c": [0.07] * P, "m": [0.07] * P}
    elif scenario == "B":                     # m fails on a prompt set drawn independently of harm
        f_set = [rng.random() < frac_f for _ in range(P)]
        fail = {"c": [0.05] * P, "m": [0.95 if f else 0.05 for f in f_set]}
    elif scenario in ("C", "D"):              # m fails on the most harmful (C) or the least harmful (D) prompts
        order = sorted(range(P), key=lambda p: eta[p], reverse=(scenario == "C"))
        top = set(order[:int(round(frac_f * P))])
        fail = {"c": [0.05] * P, "m": [0.95 if p in top else 0.05 for p in range(P)]}
    else:
        raise ValueError(scenario)
    n, u, y_plain = {}, {}, {}
    for a in ("c", "m"):
        n[a], u[a], y_plain[a] = [], [], []
        for j in range(J):
            nj, uj, yj = [], [], []
            for p in range(P):
                pi = expit(eta[p] + gam[a][p] + s[j] + e[a][j])
                nn = uu = un = 0
                for _ in range(3):
                    bad = rng.random() < fail[a][p]
                    unsafe = rng.random() < pi
                    un += unsafe
                    if not bad:
                        nn += 1
                        uu += unsafe
                nj.append(nn)
                uj.append(uu)
                yj.append(un / 3.0)
            n[a].append(nj)
            u[a].append(uj)
            y_plain[a].append(yj)
    V = {a: [100.0 * sum(u[a][j]) / sum(n[a][j]) for j in range(J)] for a in ("c", "m")}
    diffs = [V["c"][j] - V["m"][j] for j in range(J)]
    est = sum(diffs) / J
    v_seed, df_seed = seed_part(diffs)
    keep = [p for p in range(P) if all(n["c"][j][p] > 0 and n["m"][j][p] > 0 for j in range(J))]
    d_design = [[u["c"][j][p] / n["c"][j][p] - u["m"][j][p] / n["m"][j][p] for p in keep] for j in range(J)]
    res = {"D": assemble(est, v_seed, df_seed, d_design), "kept": len(keep)}

    def x(a, j, p):
        v = V[a][j] / 100.0
        return v + (u[a][j][p] - v * n[a][j][p]) / (sum(n[a][j]) / P)

    d_lin = [[x("c", j, p) - x("m", j, p) for p in range(P)] for j in range(J)]
    res["L"] = assemble(est, v_seed, df_seed, d_lin)
    pdiffs = [100.0 * (sum(y_plain["c"][j]) - sum(y_plain["m"][j])) / P for j in range(J)]
    pv, pdf = seed_part(pdiffs)
    d_plain = [[y_plain["c"][j][p] - y_plain["m"][j][p] for p in range(P)] for j in range(J)]
    res["plain"] = assemble(sum(pdiffs) / J, pv, pdf, d_plain)
    return res


def simulate(scenario, reps, seed, frac_f=0.08, arm_seed_sd=0.15):
    rng = random.Random(seed)
    tq = {}
    acc = {k: {"cover": 0, "se": 0.0, "est": [], "item": 0.0, "rej": 0} for k in ("D", "L", "plain")}
    kept = 0
    for _ in range(reps):
        r = one_rep(rng, scenario, frac_f=frac_f, arm_seed_sd=arm_seed_sd)
        kept += r["kept"]
        for k in ("D", "L", "plain"):
            est, se, df, vi = r[k]
            key = round(df, 2)
            if key not in tq:
                tq[key] = t_quantile(0.95, df)
            half = tq[key] * se
            acc[k]["cover"] += (est - half <= 0.0 <= est + half)
            acc[k]["se"] += se
            acc[k]["item"] += vi
            acc[k]["est"].append(est)
            acc[k]["rej"] += 2.0 * (1.0 - t_cdf(abs(est / se), df)) < 0.0075
    lines = [f"scenario {scenario} (reps {reps}, rng seed {seed}" + (f", F share {frac_f}" if scenario == "B" else "") + f", arm-seed logit SD {arm_seed_sd}" +
             f"): mean kept prompts {kept / reps:.1f} of 200"]
    for k, name in (("plain", "plain U, B16 primary form"), ("D", "coherent, design form"), ("L", "coherent, linearized")):
        ests = acc[k]["est"]
        m = sum(ests) / reps
        sd = math.sqrt(sum((v - m) ** 2 for v in ests) / (reps - 1))
        cov = acc[k]["cover"] / reps
        mc = math.sqrt(cov * (1 - cov) / reps)
        lines.append(f"  {name}: 90% coverage of the true 0 = {cov:.3f} (MC SE {mc:.3f}); mean estimate {m:+.3f} pp; "
                     f"empirical SD {sd:.3f} pp; mean reported SE {acc[k]['se'] / reps:.3f} pp; "
                     f"mean item part {acc[k]['item'] / reps:.3f} pp^2; two-sided p < 0.75% in {acc[k]['rej'] / reps:.4f}")
    return lines


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    print("Hand case (exact arithmetic; P = 4, J = 2):")
    print("\n".join(hand_case()))
    print("t check: t_0.95(5) =", round(t_quantile(0.95, 5), 4), "(table 2.0150); t_0.95(1) =", round(t_quantile(0.95, 1), 4), "(table 6.3138)")
    worlds = [("A", 20261101, 0.08, 0.15), ("B", 20261102, 0.08, 0.15), ("B", 20261103, 0.04, 0.15)]
    if len(sys.argv) > 2 and sys.argv[2] == "low-noise":
        worlds = [("A", 20261111, 0.08, 0.0), ("B", 20261112, 0.08, 0.0), ("B", 20261113, 0.04, 0.0)]
    if len(sys.argv) > 2 and sys.argv[2] == "direction":
        worlds = [("C", 20261121, 0.04, 0.0), ("D", 20261122, 0.04, 0.0)]
    for sc, sd, ff, ns in worlds:
        print("\n".join(simulate(sc, reps, sd, ff, ns)))
