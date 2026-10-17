"""Computations for check-W3-W4-W12-W13.md (planning arithmetic; no outcome data beyond the Gate A counts file).

Inputs: evidence/gate_a_overrefusal_counts.json (labels and numbers only, from gate_a_overrefusal_counts.py) and the
measured wave-0a ledger timings written below as constants (read from the R arms' ledger.jsonl; timing fields only).
Output: evidence/w3_w4_w12_w13_analysis.json. Seeds fixed; Monte Carlo SEs reported.
Run: PYTHONDONTWRITEBYTECODE=1 <venv python> -B w3_w4_w12_w13_analysis.py
"""
import json, math, pathlib, time
import numpy as np
import mpmath as mp

HERE = pathlib.Path(__file__).resolve().parent
GA = json.loads((HERE / "evidence/gate_a_overrefusal_counts.json").read_text())
OUT = {}
ALPHA, DELTA = 0.05, 5.0
SIG_C, SIG_H = 2.65, 3.85            # per-arm seed SD of U, PLAN-S:117 (central, high)
N = {"R": 8, "a0": 6, "A1": 6, "L1": 6, "H1": 6, "S1": 6, "S3": 6, "S4": 6}
ARMS = list(N)
CON = [("R", "A1"), ("R", "L1"), ("R", "H1"), ("a0", "S1"), ("S1", "S3"), ("S1", "S4")]   # (comparator, repair)
DF = sum(v - 1 for v in N.values())   # 42


# ---------- t distribution helpers (no scipy: mpmath scalars, numpy table for vectors) ----------
def tcdf_scalar(x, df):
    x = mp.mpf(x)
    if df == math.inf:
        return float(mp.ncdf(x))
    z = df / (df + x * x)
    tail = 0.5 * mp.betainc(df / 2, 0.5, 0, z, regularized=True)
    return float(1 - tail) if x > 0 else float(tail)


def tq(p, df):
    if df == math.inf:
        return float(mp.sqrt(2) * mp.erfinv(2 * p - 1))
    return float(mp.findroot(lambda x: tcdf_scalar(x, df) - p, tq(p, math.inf)))


_grid = np.linspace(-15, 15, 30001)
_tab = np.array([tcdf_scalar(x, DF) for x in _grid])


def tcdf(x):
    return np.interp(x, _grid, _tab, left=0.0, right=1.0)


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def holm(p, alpha):
    m = p.shape[1]
    order = np.argsort(p, axis=1)
    ps = np.take_along_axis(p, order, 1)
    ok = ps <= alpha / (m - np.arange(m))
    cum = np.cumprod(ok, axis=1).astype(bool)
    rej = np.zeros_like(cum)
    np.put_along_axis(rej, order, cum, 1)
    return rej


# ---------- simulation of the stage-1 primary design: U, O, L per arm-seed ----------
def simulate(nrep, mu, sd, corr, rng):
    """mu[arm] = (U, O, L) true means; sd = (sU, sO, sL); corr 3x3 within arm-seed. Returns est, se per contrast."""
    L = np.linalg.cholesky(np.array(corr))
    means, ss = {}, np.zeros((nrep, 3))
    for a in ARMS:
        z = rng.standard_normal((nrep, N[a], 3)) @ L.T * np.array(sd) + np.array(mu[a])
        m = z.mean(1)
        means[a] = m
        ss += ((z - m[:, None, :]) ** 2).sum(1)
    s = np.sqrt(ss / DF)
    est, se = np.zeros((nrep, 6, 3)), np.zeros((nrep, 6, 3))
    for k, (c, t) in enumerate(CON):
        f = math.sqrt(1 / N[c] + 1 / N[t])
        est[:, k, 0] = means[c][:, 0] - means[t][:, 0]          # U: positive = repair restores more
        est[:, k, 1] = means[t][:, 1] - means[c][:, 1]          # O: positive = adverse
        est[:, k, 2] = means[t][:, 2] - means[c][:, 2]          # L: positive = adverse
        se[:, k, :] = s * f
    return est, se


def labels_current(est, se, reading):
    """Labels under the current plan's readings of 'worse'. Returns dict of boolean arrays (nrep, 6)."""
    tU = est[:, :, 0] / se[:, :, 0]
    p2U = 2 * (1 - tcdf(np.abs(tU)))
    rejU = holm(p2U, ALPHA)
    better = rejU & (est[:, :, 0] > 0) & (est[:, :, 0] >= DELTA)
    tO, tL = est[:, :, 1] / se[:, :, 1], est[:, :, 2] / se[:, :, 2]
    pO1, pL1 = 1 - tcdf(tO), 1 - tcdf(tL)
    pUadv1 = tcdf(tU)                                             # one-sided adverse U
    if reading == "R1":   # U two-sided Holm-6; O, L each one-sided Holm-6 (three families)
        wU, wO, wL = rejU & (tU < 0), holm(pO1, ALPHA), holm(pL1, ALPHA)
    elif reading == "R2":  # O, L two-sided Holm-6, adverse side read
        wU = rejU & (tU < 0)
        wO = holm(2 * (1 - tcdf(np.abs(tO))), ALPHA) & (tO > 0)
        wL = holm(2 * (1 - tcdf(np.abs(tL))), ALPHA) & (tL > 0)
    elif reading == "R3":  # one Holm over 18 one-sided adverse tests
        r = holm(np.concatenate([pUadv1, pO1, pL1], 1), ALPHA)
        wU, wO, wL = r[:, :6], r[:, 6:12], r[:, 12:]
    elif reading == "R4":  # O, L per comparison, one-sided 5%, unadjusted
        wU, wO, wL = rejU & (tU < 0), pO1 <= ALPHA, pL1 <= ALPHA
    elif reading == "R5":  # three one-sided Holm-6 families (U adverse as its own family)
        wU, wO, wL = holm(pUadv1, ALPHA), holm(pO1, ALPHA), holm(pL1, ALPHA)
    tq95 = tq(0.95, DF)
    lo, hi = est[:, :, 0] - tq95 * se[:, :, 0], est[:, :, 0] + tq95 * se[:, :, 0]
    equiv = (lo > -DELTA) & (hi < DELTA)
    return {"better": better, "worseU": wU, "worseO": wO, "worseL": wL, "equiv": equiv, "rejU": rejU}


# ---------- the proposed graph (Bretz et al. 2009, weighted Bonferroni shortcut) ----------
def graph_spec(gamma):
    """Nodes 0-5 U_k (two-sided), 6-11 O_k, 12-17 L_k (one-sided adverse)."""
    w = np.zeros(18)
    w[:6] = (1 - gamma) / 6
    w[6:] = gamma / 12
    G = np.zeros((18, 18))
    for k in range(6):
        u, o, l = k, 6 + k, 12 + k
        G[u, o] = G[u, l] = 0.25
        for j in range(6):
            if j != k:
                G[u, j] = 0.5 / 5
        G[o, l] = G[o, u] = 0.5
        G[l, o] = G[l, u] = 0.5
    return w, G


def graph_test(p, w0, G0, alpha):
    w, G = w0.copy(), G0.copy()
    active = np.ones(len(p), bool)
    rej = np.zeros(len(p), bool)
    while True:
        cand = np.where(active & (p <= alpha * w + 1e-15))[0]
        if len(cand) == 0:
            return rej
        i = cand[0]
        rej[i], active[i] = True, False
        idx = np.where(active)[0]
        w[idx] += w[i] * G[i, idx]
        w[i] = 0
        Gn = np.zeros_like(G)
        for j in idx:
            for l_ in idx:
                if j != l_:
                    den = 1 - G[j, i] * G[i, j]
                    Gn[j, l_] = (G[j, l_] + G[j, i] * G[i, l_]) / den if den > 1e-12 else 0.0
        G = Gn


def labels_graph(est, se, gamma):
    w0, G0 = graph_spec(gamma)
    tU = est[:, :, 0] / se[:, :, 0]
    p = np.concatenate([2 * (1 - tcdf(np.abs(tU))), 1 - tcdf(est[:, :, 1] / se[:, :, 1]),
                        1 - tcdf(est[:, :, 2] / se[:, :, 2])], 1)
    lim = alpha_max = ALPHA * max(w0.max(), 1e-9)
    rej = np.zeros_like(p, bool)
    # fast path: replicates with no p below the largest weight a node can ever reach (alpha) need no loop
    for r in np.where((p <= ALPHA).any(1))[0]:
        rej[r] = graph_test(p[r], w0, G0, ALPHA)
    rejU = rej[:, :6]
    better = rejU & (est[:, :, 0] > 0) & (est[:, :, 0] >= DELTA)
    worseU = rejU & (tU < 0)
    return {"better": better, "worseU": worseU, "worseO": rej[:, 6:12], "worseL": rej[:, 12:], "rejU": rejU}


def error_rates(lab, mu):
    """Familywise error rates from labels and the true contrasts."""
    trueU = np.array([mu[c][0] - mu[t][0] for c, t in CON])
    trueO = np.array([mu[t][1] - mu[c][1] for c, t in CON])
    trueL = np.array([mu[t][2] - mu[c][2] for c, t in CON])
    fb = (lab["better"] & (trueU <= 0)).any(1)
    fwU = (lab["worseU"] & (trueU >= 0)).any(1)
    fwO = (lab["worseO"] & (trueO <= 0)).any(1)
    fwL = (lab["worseL"] & (trueL <= 0)).any(1)
    fw = fwU | fwO | fwL
    res = {"false_better": fb.mean(), "false_worse_U": fwU.mean(), "false_worse_O": fwO.mean(),
           "false_worse_L": fwL.mean(), "false_worse_any": fw.mean(), "any_false_directional": (fb | fw).mean()}
    if "equiv" in lab:
        fe = (lab["equiv"] & (np.abs(trueU) >= DELTA)).any(1)
        res["false_equivalent_any"] = fe.mean()
        res["expected_false_equivalent_labels"] = (lab["equiv"] & (np.abs(trueU) >= DELTA)).sum(1).mean()
        res["any_wrong_label"] = (fb | fw | fe).mean()
    n = fb.shape[0]
    return {k: (round(float(v), 4), round(float(math.sqrt(max(v * (1 - v), 1e-12) / n)), 4)) if k != "expected_false_equivalent_labels" else round(float(v), 3) for k, v in res.items()}


def mu_of(U=None, O=None, Lv=None):
    mu = {a: [0.0, 0.0, 0.0] for a in ARMS}
    for j, d in enumerate((U, O, Lv)):
        for a, v in (d or {}).items():
            mu[a][j] = v
    return mu


def w4(rng):
    res = {}
    t0 = time.time()
    sd = (SIG_C, 1.15, 0.0024)
    scen = {
        "global_null": mu_of(),
        # U effects in U-space: lower U in the repair arm = restoration (mu is U level, not Lambda)
        "all_U_at_minus_delta_boundary": mu_of(U={"A1": -5, "L1": -5, "H1": -5, "S3": -5, "S4": -5, "S1": -5 - 5}),
        "mixed_realistic": mu_of(U={"A1": -2, "L1": 0, "H1": -2, "S1": -10, "S3": -10, "S4": -10},
                                 O={"S1": 8, "S3": 8, "S4": 8}),
    }
    # note: in "all_U_at_minus_delta_boundary" every contrast has |Lambda| = 5 (P4 = 10, P5 = P6 = 5 - 5... see below)
    # recompute exactly: P1-P3 Lambda = 0 - (-5) = 5; P4 = 0 - (-10) = 10; P5 = -10 - (-5) = -5; P6 = -5
    for cname, corr in {"indep": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                        "rhoUO_-0.5": [[1, -0.5, 0], [-0.5, 1, 0], [0, 0, 1]]}.items():
        for sname, mu in scen.items():
            if cname != "indep" and sname != "global_null":
                continue
            est, se = simulate(200000, mu, sd, corr, rng)
            for reading in ("R1", "R2", "R3", "R4", "R5"):
                res[f"{sname}|{cname}|current_{reading}"] = error_rates(labels_current(est, se, reading), mu)
            for g in (0.0, 0.1, 0.2):
                lab = labels_graph(est[:60000], se[:60000], g)
                res[f"{sname}|{cname}|graph_gamma{g}"] = error_rates(lab, mu)
    res["_seconds"] = round(time.time() - t0, 1)
    # TOST variants at true Lambda = 0 (power) and = delta (size), 6 vs 8 and 6 vs 6, central/high noise, df 42
    tost = {}
    for sig in (SIG_C, SIG_H):
        for lab, f in (("6v8", math.sqrt(1 / 6 + 1 / 8)), ("6v6", math.sqrt(2 / 6))):
            se_ = sig * f
            for name, a in (("per_comparison_a0.05", 0.05), ("bonferroni_a0.05/6", 0.05 / 6),
                            ("graph_gamma0.1_a0.0075", 0.9 * 0.05 / 6)):
                hw = tq(1 - a, DF) * se_
                p_eq0 = 2 * ncdf(max(DELTA - hw, 0) / se_) - 1 if DELTA > hw else 0.0
                tost[f"sigma{sig}|{lab}|{name}"] = {"SE": round(se_, 3), "half_width": round(hw, 3),
                                                    "P_equiv_given_true0": round(p_eq0, 3)}
    res["tost_power"] = tost
    # MDE of 'better' at Holm's first step: current alpha/6 two-sided vs graph gamma=0.1 (0.9 alpha/6)
    mde = {}
    for sig in (SIG_C, SIG_H):
        for lab, f in (("6v8", math.sqrt(1 / 6 + 1 / 8)), ("6v6", math.sqrt(2 / 6))):
            se_ = sig * f
            for name, a in (("holm_first_step", 0.05 / 6), ("graph_gamma0.1", 0.9 * 0.05 / 6),
                            ("graph_gamma0.2", 0.8 * 0.05 / 6), ("holm18_first_step", 0.05 / 18)):
                mde[f"sigma{sig}|{lab}|{name}"] = round((tq(1 - a / 2, DF) + tq(0.8, DF)) * se_, 2)
    res["mde_80pct_two_sided"] = mde
    return res


# ---------- W3: references ----------
def w3():
    out = {}
    s, z = SIG_C, tq(0.95, math.inf) + tq(0.80, math.inf)
    designs = {}
    for sd_d in (2.1, 3.0):
        designs[f"current_6v3_refSD=sigma"] = math.sqrt(s * s / 6 + s * s / 3)
        designs[f"current_6v3_refSD=sqrt(sigma^2+sd_d^2)|sd_d={sd_d}"] = math.sqrt(s * s / 6 + (s * s + sd_d ** 2) / 3)
        designs[f"6_seeds_paired_with_a0_m_unpaired|sd_d={sd_d}"] = math.sqrt(2 * s * s / 6 + sd_d ** 2 / 6)
        for rho in (0.5, 0.76):
            designs[f"6_seeds_paired_and_m_seed_paired_rho{rho}|sd_d={sd_d}"] = math.sqrt(2 * s * s * (1 - rho) / 6 + sd_d ** 2 / 6)
    out["contrast_SE_pp"] = {k: round(v, 3) for k, v in designs.items()}
    out["MDE_one_sided_5pct_80pct_pp"] = {k: round(z * v, 2) for k, v in designs.items()}
    out["MDE_bonferroni5_one_sided_pp"] = {k: round((tq(1 - 0.01, math.inf) + tq(0.8, math.inf)) * v, 2)
                                           for k, v in designs.items()}
    # IUT joint power: m must beat 5 references; shared m-bar makes the 5 tests positively correlated.
    rng = np.random.default_rng(20261017)
    nrep = 400000
    res = {}
    for label, adv in {"equal_advantage_4pp_each": [4, 4, 4, 4, 4], "equal_advantage_6pp_each": [6, 6, 6, 6, 6],
                       "one_binding_ref_4pp_others_12pp": [4, 12, 12, 12, 12],
                       "one_binding_ref_6pp_others_12pp": [6, 12, 12, 12, 12]}.items():
        for dname, (n_ref, paired) in {"current(3,3,3,3 seeds; B+Qi 6)": ([3, 3, 3, 3, 6], False),
                                       "fix(SP,AS,SL at 6 paired; G 3; B+Qi 6)": ([6, 6, 6, 3, 6], True)}.items():
            m_bar = rng.standard_normal(nrep) * s / math.sqrt(6)
            a0_bar = rng.standard_normal(nrep) * s / math.sqrt(6)
            ok = np.ones(nrep, bool)
            for r in range(5):
                if paired and r < 3:   # post-hoc refs: ref = a0 - d, d paired by seed (sd_d 2.1)
                    ref_bar = a0_bar + rng.standard_normal(nrep) * 2.1 / math.sqrt(6)
                    se_r = math.sqrt(2 * s * s / 6 + 2.1 ** 2 / 6)
                elif r < 3:            # current: 3 transformed a0 seeds, analysed as an independent arm
                    ref_bar = rng.standard_normal(nrep) * s / math.sqrt(n_ref[r])
                    se_r = math.sqrt(s * s / 6 + s * s / n_ref[r])
                else:
                    ref_bar = rng.standard_normal(nrep) * s / math.sqrt(n_ref[r])
                    se_r = math.sqrt(s * s / 6 + s * s / n_ref[r])
                d = (ref_bar + adv[r]) - m_bar          # U(ref) - U(m); positive = m better
                ok &= d / se_r > tq(0.95, math.inf)
            res[f"{label}|{dname}"] = round(float(ok.mean()), 3)
    out["IUT_joint_power_one_sided_5pct"] = res
    # cost (measured wave-0a R-arm ledgers, timing fields only; job slots from the recost NOTES)
    slot_s = {"R1": 48.9 * 60, "R2": 49.0 * 60, "R3": 43.5 * 60}
    train_s = {"R1": 59.38 + 161.06, "R2": 60.12 + 159.61, "R3": 60.36 + 155.62}
    sample_s = {"R1": 637.79, "R2": 684.97, "R3": 504.18}
    guard_s_s = {"R1": 96.86, "R2": 97.12, "R3": 96.08}
    FRE = 2934.0
    eval_only = {k: slot_s[k] - train_s[k] for k in slot_s}
    med_eval = sorted(eval_only.values())[1]
    per_ans = sorted(sample_s[k] / 600 for k in sample_s)[1]
    per_guard = sorted(guard_s_s[k] / 600 for k in guard_s_s)[1]
    lean_eval = 200 * (per_ans + per_guard) + 15
    rate = 1.79 / 3600
    cost = {"FRE_s": FRE, "eval_only_state_s_median": round(med_eval), "eval_only_state_FRE": round(med_eval / FRE, 3),
            "eval_only_state_usd": round(med_eval * rate, 2), "conservative_49min_state_usd": round(49 * 60 * rate, 2),
            "lean_eval_state_s": round(lean_eval), "lean_eval_state_FRE": round(lean_eval / FRE, 3),
            "lean_eval_state_usd": round(lean_eval * rate, 3),
            "a0_regeneration_s": 0.077 * 3600, "a0_regeneration_usd": round(0.077 * 3600 * rate, 2)}
    plans = {"current_3_seeds": {"SP": 3, "AS(0.75,0.5)": 6, "SL(1 point)": 3},
             "fix_6_seeds": {"SP": 6, "AS(0.75,0.5)": 12, "SL(1 point)": 6},
             "fix_6_seeds_plus_lambda0.9": {"SP": 6, "AS(0.9,0.75,0.5)": 18, "SL(1 point)": 6},
             "fix_6_seeds_plus_lambda0.9_SL2pts": {"SP": 6, "AS(0.9,0.75,0.5)": 18, "SL(2 points)": 12}}
    for name, p in plans.items():
        n = sum(p.values())
        pods = math.ceil(n / 4)
        full = n * med_eval
        cost[name] = {"states": n, "C_full_FRE": round(full / FRE, 1), "C_full_GPU_h": round(full / 3600, 2),
                      "usd_measured_eval_only": round(full * rate, 2), "usd_at_49min": round(n * 49 * 60 * rate, 2),
                      "pods_at_4_per_pod": pods, "overhead_usd_at_19_26min": [round(pods * 18.9 * 60 * rate, 2), round(pods * 26.0 * 60 * rate, 2)],
                      "usd_total_x1.25_range": [round(1.25 * (full * rate + pods * 18.9 * 60 * rate), 2),
                                                round(1.25 * (n * 49 * 60 * rate + pods * 26.0 * 60 * rate), 2)],
                      "C_lean_FRE": round(n * lean_eval / FRE, 2), "C_lean_usd": round(n * lean_eval * rate, 2)}
    inc = cost["fix_6_seeds"]["states"] - cost["current_3_seeds"]["states"]
    cost["increment_fix_minus_current_states"] = inc
    cost["increment_usd_range_x1.25_with_overhead"] = [round(1.25 * (inc * med_eval * rate + 3 * 18.9 * 60 * rate), 2),
                                                       round(1.25 * (inc * 49 * 60 * rate + 3 * 26.0 * 60 * rate), 2)]
    cost["increment_C_full_FRE"] = round(inc * med_eval / FRE, 1)
    cost["increment_C_lean_FRE"] = round(inc * lean_eval / FRE, 2)
    out["cost"] = cost
    return out


# ---------- W12: over-refusal limits ----------
def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def w12():
    out = {}
    n, p0 = 100, 0.17
    a0 = [GA["units"][s]["overrefusal"]["refusals"] for s in ("1101", "1102", "1103")]
    out["counts"] = {"untuned": GA["units"]["untuned"]["overrefusal"]["refusals"], "a0": a0}
    mean_a0 = sum(a0) / 3
    sd_a0 = math.sqrt(sum((x - mean_a0) ** 2 for x in a0) / 2)
    out["a0_seed_sd_pp"] = round(sd_a0, 3)
    out["binomial_SE_pp_at_level"] = {f"{p:.2f}": round(100 * math.sqrt(p * (1 - p) / n), 2) for p in (0.05, 0.10, 0.17, 0.19, 0.22, 0.27)}
    # paired per-prompt SE of O(a0 seed) - O(untuned) from the Gate A per-prompt labels
    pairs = GA["per_prompt"]["pairs"]
    pse = {}
    for s in ("1101", "1102", "1103"):
        c = pairs[f"{s}|untuned"]
        b, cc = c["first_only"], c["second_only"]
        pse[s] = round(100 * math.sqrt((b + cc) / n ** 2 - (b - cc) ** 2 / n ** 3), 2)
    out["paired_prompt_SE_pp_a0_vs_untuned"] = pse
    out["discordant_a0_vs_untuned"] = {s: pairs[f"{s}|untuned"]["first_only"] + pairs[f"{s}|untuned"]["second_only"] for s in ("1101", "1102", "1103")}
    out["discordant_a0_seed_pairs"] = {k: v["first_only"] + v["second_only"] for k, v in pairs.items() if "untuned" not in k}
    tab = {}
    for tau in (2, 5, 10):
        lim = p0 + tau / 100
        # exact one-sided 5% bound rule (untuned level treated as known): feasible iff X <= k_tau
        k = max(i for i in range(0, 101) if binom_cdf(i, n, lim) <= 0.05)
        row = {"limit_count": round(100 * lim), "bound_rule_feasible_if_X_at_most": k,
               "bound_rule_size_at_limit": round(binom_cdf(k, n, lim), 4)}
        for ptrue in (0.05, 0.10, 0.17, lim - 0.03, lim, lim + 0.03, lim + 0.05):
            row[f"P_feasible_bound|true={round(100*ptrue)}"] = round(binom_cdf(k, n, ptrue), 3)
            row[f"P_feasible_point|true={round(100*ptrue)}"] = round(binom_cdf(round(100 * lim), n, ptrue), 3)
        tab[f"tau{tau}"] = row
    out["feasibility_one_arm_unit_vs_known_untuned_level"] = tab
    # paired normal approximation for an add arm near the limit: SE = sqrt(d)/sqrt(n) (d = discordant share)
    za, zb = tq(0.95, math.inf), tq(0.80, math.inf)
    need = {}
    for tau in (2, 5, 10):
        for d in (0.05, 0.10, 0.20):
            need[f"tau{tau}|paired_d{d}"] = math.ceil(((za + zb) * math.sqrt(d) / (tau / 100)) ** 2)
        need[f"tau{tau}|unpaired_p0.17"] = math.ceil(((za + zb) * math.sqrt(2 * 0.17 * 0.83) / (tau / 100)) ** 2)
        need[f"tau{tau}|CI95_halfwidth_eq_tau_level_p0.19"] = math.ceil((1.96 * math.sqrt(0.19 * 0.81) / (tau / 100)) ** 2)
    out["prompts_needed_80pct_power_one_sided_5pct_true_excess_0"] = need
    # power at 100 prompts, paired, true excess 0 vs limit tau: P(bound < tau) = Phi(tau/SE - z)
    pw = {}
    for tau in (2, 5, 10):
        for d in (0.05, 0.10, 0.20):
            se_ = math.sqrt(d / n) * 100
            pw[f"tau{tau}|paired_d{d}|n100"] = round(ncdf(tau / se_ - za), 3)
            se5 = math.sqrt(d / 500) * 100
            pw[f"tau{tau}|paired_d{d}|n500"] = round(ncdf(tau / se5 - za), 3)
    out["P_declared_feasible_bound_rule_true_excess_0"] = pw
    # fixed-bank (seed-only) model: 6-seed mean, seed SD from a0 (2 df) -> SE and the REQ-19 style MDE (6 vs 6)
    se6 = sd_a0 / math.sqrt(6)
    out["fixed_bank_seed_only"] = {"SE_arm_mean_6_seeds_pp": round(se6, 3),
                                   "MDE_6v6_two_sided_5pct_80pct_pp": round((tq(0.975, 10) + tq(0.8, 10)) * sd_a0 * math.sqrt(2 / 6), 2),
                                   "MDE_9v9_pp": round((tq(0.975, 16) + tq(0.8, 16)) * sd_a0 * math.sqrt(2 / 9), 2)}
    out["prompt_random_model"] = {"MDE_two_sided_5pct_80pct_pp_at_paired_SE": {
        s: round((1.96 + 0.8416) * v, 2) for s, v in pse.items()}}
    return out


# ---------- W13: coherence screen ----------
def w13():
    out = {}
    inc = [GA["units"][s]["sampled_incoherent"] / 600 for s in ("1101", "1102", "1103")]
    short = [GA["units"][s]["sampled_short_only"] for s in ("1101", "1102", "1103")]
    capped = [GA["units"][s]["sampled_capped"] for s in ("1101", "1102", "1103")]
    m = sum(inc) / 3
    sd = math.sqrt(sum((x - m) ** 2 for x in inc) / 2)
    out["a0_incoherent_share"] = [round(x, 4) for x in inc]
    out["a0_short_only_counts"] = short
    out["a0_capped_counts"] = capped
    out["mean_sd"] = [round(m, 4), round(sd, 4)]
    p_norm = 1 - ncdf((0.10 - m) / sd)
    tval = (0.10 - m) / (sd * math.sqrt(1 + 1 / 3))
    p_t2 = 0.5 * (1 - tval / math.sqrt(tval * tval + 2))
    out["P_unit_over_10pct"] = {"normal_plugin": round(p_norm, 4), "t2_predictive": round(p_t2, 4)}
    out["P_any_of_50_units_over_10pct"] = {"normal_plugin": round(1 - (1 - p_norm) ** 50, 3),
                                           "t2_predictive": round(1 - (1 - p_t2) ** 50, 3)}
    out["P_any_of_8_arm_pooled_over_10pct_normal_plugin_seed_sd_over_sqrt6"] = round(
        1 - (1 - (1 - ncdf((0.10 - m) / (sd / math.sqrt(6))))) ** 8, 6)
    # Holm first step after dropping one arm (post hoc family of 5) vs keeping 6
    out["holm_first_step_two_sided"] = {"m=6": round(0.05 / 6, 5), "m=5": round(0.05 / 5, 5),
                                        "MDE_factor_m6": round(tq(1 - 0.05 / 12, DF) + tq(0.8, DF), 3),
                                        "MDE_factor_m5": round(tq(1 - 0.05 / 10, DF) + tq(0.8, DF), 3)}
    return out


if __name__ == "__main__":
    rng = np.random.default_rng(20261017)
    OUT["df_pooled"] = DF
    OUT["t_quantiles"] = {"t_0.95_42": round(tq(0.95, DF), 4), "t_0.99583_42": round(tq(1 - 0.05 / 12, DF), 4)}
    OUT["W12"] = w12()
    OUT["W13"] = w13()
    OUT["W3"] = w3()
    OUT["W4"] = w4(rng)
    (HERE / "evidence/w3_w4_w12_w13_analysis.json").write_text(json.dumps(OUT, indent=1, sort_keys=True))
    print("done")
