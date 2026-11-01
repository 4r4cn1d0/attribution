#!/usr/bin/env python3
"""stat_review_o_power.py: planning power of the over-refusal (O) tests on the 500-prompt primary O bank.

Normal-approximation planning values (E/I in the review), no data input. Model: for each bank prompt p the
repair arm m's greedy "Refusal: Yes" flag differs from theta0's on a share q of prompts (the discordance), with a
mean difference Delta = O(m) - O(theta0). One seed's per-prompt difference has variance q - Delta^2, so the item
part of the SE is sqrt((q - Delta^2) / P) (conservative: it ignores flag changes between m's 6 seeds). The seed part
is sigma_s^2 / J with J - 1 df (LN-20 item 1), sigma_s = the between-seed SD of m's cell O. df by Satterthwaite.
Power uses the normal approximation to the noncentral t: Phi(ncp - t_crit(df)).

Tests:
 F_k "feasible (O, 5)": H0 Delta >= 5, rejected if the estimate is low; per comparison one-sided 5%; inside Phi
   0.375% (after U_k) to 0.411% (after U_k and L_k).
 R1.3 "worse (O)" theta0 part: H0 Delta <= 5; inside Phi 0.0417% (start), 0.135% (after U_k), 0.217% (after U_k
   and L_k). The comparator part is assumed to pass (planning; an add arm's comparator sits near a0 or S1).
 The REQ-19-type 6-seed O MDE (80%, one-sided 5%) at P = 100 and 500.
Answer cap (I): under Branch 128 the cut can change up to 3 of 100 flags per unit (W1-18's bar), so the
discordance between m and theta0 can rise by 0 to about 6 pp if the changes fall on different prompts; the tables
add dq in {0, +3, +6} pp. Under Branch full dq = 0 by construction (the full answers are judged).
Run: python3 -I -B stat_review_o_power.py
"""
import json, math, pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT, RES = [], {}


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


def ncdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def nppf(p):
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if ncdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def lgam(x):
    return math.lgamma(x)


def t_sf(t, df):
    """Upper tail of Student t via the regularized incomplete beta (continued fraction)."""
    if df > 1e5:
        return 1.0 - ncdf(t)
    if t == 0.0:
        return 0.5
    x = df / (df + t * t)
    if x <= 0.0:
        return 0.0 if t > 0 else 1.0
    a, b = df / 2.0, 0.5
    # betainc(a, b, x) by Lentz continued fraction
    def betacf(a, b, x):
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c, d = 1.0, 1.0 - qab * x / qap
        d = 1.0 / (d if abs(d) > tiny else tiny)
        h = d
        for m in range(1, 3000):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
            de = d * c
            h *= de
            if abs(de - 1.0) < 3e-15:
                break
        return h
    lbt = lgam(a + b) - lgam(a) - lgam(b) + a * math.log(x) + b * math.log(1.0 - x)
    if x < (a + 1.0) / (a + b + 2.0):
        ib = math.exp(lbt) * betacf(a, b, x) / a
    else:
        ib = 1.0 - math.exp(lbt) * betacf(b, a, 1.0 - x) / b
    two = ib
    return two / 2.0 if t > 0 else 1.0 - two / 2.0


def t_ppf(p, df):
    if df > 1e5:
        return nppf(p)
    lo, hi = -60.0, 60.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 1.0 - t_sf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def se_df(P, q, delta_pp, sigma_s, J=6):
    d = delta_pp / 100.0
    v_item = max(q - d * d, 1e-12) / P * 1e4
    v_seed = sigma_s ** 2 / J
    V = v_item + v_seed
    df = V ** 2 / ((v_seed ** 2 / (J - 1) if v_seed > 0 else 0.0) + v_item ** 2 / (P - 1))
    return math.sqrt(V), df


def power_feasible(P, q, delta, sigma_s, alpha, tau=5.0):
    se, df = se_df(P, q, delta, sigma_s)
    return ncdf((tau - delta) / se - t_ppf(1 - alpha, df)), se, df


def power_worse(P, q, delta, sigma_s, alpha, tau=5.0):
    se, df = se_df(P, q, delta, sigma_s)
    return ncdf((delta - tau) / se - t_ppf(1 - alpha, df)), se, df


def mde80(P, q, sigma_s, alpha=0.05):
    se, df = se_df(P, q, 0.0, sigma_s)
    return (t_ppf(1 - alpha, df) + t_ppf(0.8, df)) * se


def main():
    say("stat_review_o_power.py (normal approximation; planning values)")
    # 0. reproduce AMD E.3 (item part only, delta 0)
    say("0. Reproduction of AMD E.3 / rev3 6.4 (item part only, arm at theta0's level):")
    rep = {}
    for P in (100, 500):
        for alpha, lab in ((0.05, "per comparison 5%"), (0.00375, "inside Phi 0.375%")):
            row = [power_feasible(P, q, 0.0, 0.0, alpha)[0] for q in (0.05, 0.10, 0.20)]
            rep[f"{P}|{lab}"] = row
            say(f"   P {P}, {lab}: q 5/10/20% -> " + " / ".join(f"{x:.2f}" for x in row))
    RES["reproduce"] = rep
    # 1. feasibility power, wider discordance, seed part, cap sensitivity
    say("1. F_k feasibility power for an arm at theta0's level (Delta = 0), P = 500, J = 6:")
    feas = {}
    for sigma_s in (0.0, 1.15, 2.0):
        for dq in (0.0, 0.03, 0.06):
            for alpha, lab in ((0.05, "pc5"), (0.00375, "phi0375")):
                row = []
                for q in (0.05, 0.10, 0.20, 0.30, 0.40):
                    pw, se, df = power_feasible(500, q + dq, 0.0, sigma_s, alpha)
                    row.append((pw, se, df))
                feas[f"s{sigma_s}|dq{dq}|{lab}"] = [r[0] for r in row]
                say(f"   seed SD {sigma_s:.2f} pp, cap dq +{dq * 100:.0f} pp, {lab:>7}: q 5/10/20/30/40% -> " +
                    " / ".join(f"{r[0]:.2f}" for r in row) + "  (SE " + " / ".join(f"{r[1]:.2f}" for r in row) +
                    f" pp; df {row[0][2]:.0f}-{row[-1][2]:.0f})")
    RES["feasible"] = feas
    # 2. R1.3 worse (O) power, theta0 part
    say("2. R1.3 'worse (O)' power (theta0 part; comparator part assumed to pass), P = 500, seed SD 1.15 pp:")
    worse = {}
    for extra in (0.0, 0.05, 0.10):
        for alpha, lab in ((0.000417, "start 0.042%"), (0.00135, "after U_k 0.135%"), (0.002167, "after U_k, L_k 0.217%"), (0.05, "per comparison 5%")):
            row = []
            for delta in (7.5, 10.0, 15.0, 20.0):
                q = delta / 100.0 + extra
                row.append(power_worse(500, q, delta, 1.15, alpha)[0])
            worse[f"extra{extra}|{lab}"] = row
            say(f"   discordance = Delta + {extra * 100:.0f} pp, {lab:>22}: Delta 7.5/10/15/20 pp -> " + " / ".join(f"{x:.2f}" for x in row))
    for P in (100,):
        row = [power_worse(P, d / 100.0, d, 1.15, 0.00135)[0] for d in (7.5, 10.0, 15.0, 20.0)]
        say(f"   for comparison, P = 100, after U_k 0.135%, discordance = Delta: " + " / ".join(f"{x:.2f}" for x in row))
        worse["P100|after U_k"] = row
    RES["worse"] = worse
    # 3. REQ-19-type MDE
    say("3. 6-seed O MDE against theta0 (80%, one-sided 5%), item part plus seed part 1.15 pp:")
    mdes = {}
    for P in (100, 500):
        row = [mde80(P, q, 1.15) for q in (0.05, 0.10, 0.168, 0.20, 0.30, 0.40)]
        mdes[P] = row
        say(f"   P {P}: q 5/10/16.8/20/30/40% -> " + " / ".join(f"{x:.2f}" for x in row) + " pp")
    RES["mde"] = mdes
    # 4. tau_O = 2 per comparison
    row = [power_feasible(500, q, 0.0, 1.15, 0.05, tau=2.0)[0] for q in (0.05, 0.10, 0.20)]
    say("4. tau_O = 2 pp, per comparison 5%, P = 500, seed SD 1.15: q 5/10/20% -> " + " / ".join(f"{x:.2f}" for x in row))
    RES["tau2"] = row
    (HERE / "stat_review_o_power_out.txt").write_text("\n".join(OUT) + "\n")
    (HERE / "stat_review_o_power_results.json").write_text(json.dumps(RES, indent=1))


if __name__ == "__main__":
    main()
