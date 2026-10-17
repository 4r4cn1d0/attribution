#!/usr/bin/env python3
"""stage1_numbers.py: arithmetic for stage1-analysis-model-DRAFT.md (margin, closed family, O and L limits, costs).

Inputs (this folder only): evidence/gate_a_overrefusal_counts.json (Gate A labels and counts; from
gate_a_overrefusal_counts.py) and sim_w2_results.json (Gate A U values). No evaluation record is opened here.
No prompt, answer or id is printed. Seeds are fixed. Output: evidence/stage1_numbers.json and stdout.
Run: PYTHONDONTWRITEBYTECODE=1 <venv python> -B stage1_numbers.py
"""
import importlib.util, json, math, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("sim_w2", HERE / "sim_w2.py")
W = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(W)
GA = json.loads((HERE / "evidence/gate_a_overrefusal_counts.json").read_text())
R0 = json.loads((HERE / "sim_w2_results.json").read_text())
OUT = {}


def tq(p, df):
    return W.t_ppf(p, df)


def zq(p):
    return W.norm_ppf(p)


# ---------------------------------------------------------------- 1. margin as a share of E
U_a0 = R0["empirical"]["U_a0"]          # pp, seeds 1101-1103
U_un = R0["empirical"]["U_untuned"]
E = [u - U_un for u in U_a0]
E_mean = sum(E) / 3
E_fresh = (E[1] + E[2]) / 2
OUT["margin"] = dict(E_by_seed=E, E_mean=E_mean, E_fresh_seed_mean=E_fresh, delta=5.0, delta_over_E=5.0 / E_mean,
                     delta_over_E_by_seed=[5.0 / e for e in E], delta_over_E_fresh=5.0 / E_fresh,
                     delta_rel_rule=round(5.0 / E_mean, 4), delta_at_E20=0.1108 * 20, delta_at_E55=0.1108 * 55,
                     usable_help_share=13 / 39, delta_usable_help_pp=5.0 * 13 / 39,
                     hb_over_u_ratio=30.3 / E_mean, delta_on_hb_scale_pp=5.0 * 30.3 / E_mean)

# ---------------------------------------------------------------- 2. the closed family (graph), local levels
ALPHA = 0.05


def graph_spec(gamma=0.1):
    """Nodes: U_k 0-5 (two-sided), O_k 6-11, L_k 12-17 (one-sided adverse), F_k 18-23 (feasible, one-sided)."""
    n = 24
    w = np.zeros(n)
    w[:6] = (1 - gamma) / 6
    w[6:18] = gamma / 12
    G = np.zeros((n, n))
    for k in range(6):
        u, o, l, f = k, 6 + k, 12 + k, 18 + k
        G[u, f] = 0.5
        G[u, o] = G[u, l] = 0.125
        for j in range(6):
            if j != k:
                G[u, j] = 0.05
        G[f, o] = G[f, l] = 0.5
        G[o, l] = G[o, u] = 0.5
        G[l, o] = G[l, u] = 0.5
    return w, G


def graph_test(p, w0, G0, alpha=ALPHA):
    """Bretz et al. (2009) sequentially rejective weighted Bonferroni (the shortcut of the closed test)."""
    w, G = w0.copy(), G0.copy()
    active = np.ones(len(p), bool)
    rej = np.zeros(len(p), bool)
    while True:
        cand = np.where(active & (p <= alpha * w + 1e-15))[0]
        if len(cand) == 0:
            return rej
        i = cand[np.argmin((p[cand] / np.maximum(w[cand], 1e-300)))]
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


w0, G0 = graph_spec(0.1)
assert abs(w0.sum() - 1) < 1e-12 and np.all(G0.sum(1) <= 1 + 1e-12)
lv = dict(U_start_two_sided=w0[0] * ALPHA, O_or_L_start_one_sided=w0[6] * ALPHA, F_start=0.0,
          F_after_U=0.15 * 0.5 * ALPHA, O_after_U=(w0[6] + 0.15 * 0.125) * ALPHA,
          O_after_U_and_F=(w0[6] + 0.15 * 0.125 + 0.15 * 0.5 * 0.5) * ALPHA,
          U_second_after_one_U=(w0[0] + 0.15 * 0.05) * ALPHA, holm_first_step=ALPHA / 6,
          holm_second_step=ALPHA / 5)
for nm in ("U_start_two_sided", "holm_first_step"):
    for df_ in (8, 35, 1e6):
        lv[f"t_crit|{nm}|df{df_:g}"] = W.t_ppf(1 - lv[nm] / 2, df_)
lv["U_MDE_factor_graph_vs_holm_df8"] = (W.t_ppf(1 - lv["U_start_two_sided"] / 2, 8) + W.t_ppf(0.8, 8)) / (
    W.t_ppf(1 - lv["holm_first_step"] / 2, 8) + W.t_ppf(0.8, 8))
OUT["graph"] = dict(weights_sum=float(w0.sum()), row_sums=sorted(set(np.round(G0.sum(1), 12).tolist())), levels=lv)

# check: Holm graph reproduces Holm; FWER under the global null and under partial nulls (independent normal tests)
rng = np.random.default_rng(20261017)
m = 6
wH = np.full(m, 1 / m)
GH = (np.ones((m, m)) - np.eye(m)) / (m - 1)
bad = 0
for _ in range(5000):
    p = rng.uniform(0, 0.06, m) ** rng.uniform(0.5, 2)
    if not np.array_equal(graph_test(p, wH, GH), W.holm(p[None, :])[0]):
        bad += 1
OUT["graph"]["holm_mismatch_of_5000"] = bad


def norm_sf(x):
    return 0.5 * math.erfc(x / math.sqrt(2))


def sim_family(nrep, mu, seed):
    """Independent z-tests; mu: (24,) noncentralities, U two-sided, others one-sided (positive = reject direction)."""
    r = np.random.default_rng(seed)
    z = r.standard_normal((nrep, 24)) + mu[None, :]
    p = np.empty_like(z)
    p[:, :6] = np.array([[2 * norm_sf(abs(x)) for x in row] for row in z[:, :6]])
    p[:, 6:] = np.vectorize(norm_sf)(z[:, 6:])
    rej = np.zeros_like(p, bool)
    for i in np.where((p <= ALPHA).any(1))[0]:
        rej[i] = graph_test(p[i], w0, G0)
    return rej, z


fam = {}
# (i) global null (all 24 nulls true at their boundary)
rej, z = sim_family(100000, np.zeros(24), 1)
fam["global_null_fwer"] = float(rej.any(1).mean())
# (ii) U_1 true 6 SE effect, its F_1 true (feasible), others null: does the false-rejection rate stay below 5%?
mu = np.zeros(24); mu[0] = 6.0; mu[18] = 4.0
rej, z = sim_family(100000, mu, 2)
true_null = np.ones(24, bool); true_null[[0, 18]] = False
fam["one_effect_fwer_other_nulls"] = float((rej & true_null[None, :]).any(1).mean())
fam["one_effect_power_U1"] = float(rej[:, 0].mean())
fam["one_effect_power_F1_at_4SE"] = float(rej[:, 18].mean())
OUT["graph"]["checks"] = fam

# ---------------------------------------------------------------- 3. O (over-refusal) numbers
pp = GA["per_prompt"]
n_p = pp["n_prompts"]
hist = {int(k): v for k, v in pp["a0_seeds_refusing_hist"].items()}
un_by = {int(k): v for k, v in pp["untuned_refused_by_a0_count"].items()}
# per-prompt d = (a0 refusals over 3 seeds)/3 - untuned refusal
d = []
for k, c in un_by.items():
    d += [k / 3 - 1.0] * c
for k, c in hist.items():
    rest = c - un_by.get(k, 0)
    d += [k / 3] * rest
d = np.array(d)
assert len(d) == n_p
se_prompt_a0_vs_un = d.std(ddof=1) / math.sqrt(n_p) * 100
dO_a0 = d.mean() * 100
sO = float(np.std([GA["units"][s]["overrefusal"]["refusals"] for s in ("1101", "1102", "1103")], ddof=1))
o = dict(dO_a0_vs_untuned_pp=dO_a0, se_prompt_random_a0mean_vs_untuned_pp=se_prompt_a0_vs_un, seed_sd_O_a0_pp=sO,
         O_untuned=GA["units"]["untuned"]["overrefusal"]["refusals"])
# feasibility at tau_O = 5 for a removal arm like a0 (6 seeds): t = (tau - dO)/SE; power at graph levels (normal approx)
for tau in (2, 5, 10):
    for lvl_name, lvl in (("one_sided_5pct", 0.05), ("graph_F_after_U", lv["F_after_U"])):
        zc = zq(1 - lvl)
        o[f"removal_like_feasible_power|tau{tau}|{lvl_name}|prompt_random"] = norm_sf(zc - (tau - dO_a0) / se_prompt_a0_vs_un)
# an add arm at the untuned O level (true excess 0) with a share q of prompts discordant with the untuned model
for q in (0.05, 0.10, 0.20):
    for P in (100, 500):
        se = math.sqrt(q / P) * 100          # discordant prompts split evenly: Var(d) ~ q
        for tau in (2, 5, 10):
            for lvl_name, lvl in (("one_sided_5pct", 0.05), ("graph_F_after_U", lv["F_after_U"])):
                o[f"add_at_untuned_feasible_power|q{q}|P{P}|tau{tau}|{lvl_name}"] = norm_sf(zq(1 - lvl) - tau / se)
# 'worse on O' vs comparator: MDE (80%) one-sided, fixed bank (seed noise, 6 v 6 unpaired) and prompt-random
se_fixed = sO * math.sqrt(2 / 6)
for lvl_name, lvl in (("graph_start", lv["O_or_L_start_one_sided"]), ("graph_after_U", lv["O_after_U"]),
                      ("holm6_first", 0.05 / 6), ("one_sided_5pct", 0.05)):
    o[f"worseO_MDE80_fixed_bank_6v6|{lvl_name}|df8"] = (tq(1 - lvl, 8) + tq(0.8, 8)) * se_fixed
    for P in (100, 500):
        # power at a true +delta pp concentrated on delta% of prompts (the add-arm case): prompt-random SE
        for delta in (5, 10, 15):
            f = delta / 100
            se = math.sqrt(se_fixed ** 2 + (f * (1 - f) / P) * 1e4)
            o[f"worseO_power|+{delta}pp|P{P}|{lvl_name}|prompt_random"] = norm_sf(zq(1 - lvl) - delta / se)
OUT["O"] = o

# ---------------------------------------------------------------- 4. L (task loss) numbers
Ls = [GA["units"][s]["query_loss_mean"] for s in ("1101", "1102", "1103")]
s_L = float(np.std(Ls, ddof=1))
tau_L = 2 * math.sqrt(2) * s_L
se_L = s_L * math.sqrt(1 / 3)
l = dict(s=s_L, tau_L=tau_L, se_6v6=se_L, tau_over_se=tau_L / se_L)
for lvl_name, lvl in (("graph_start", lv["O_or_L_start_one_sided"]), ("graph_after_U", lv["O_after_U"]),
                      ("holm6_first", 0.05 / 6), ("one_sided_5pct", 0.05)):
    l[f"worseL_MDE80_6v6|{lvl_name}|df8"] = (tq(1 - lvl, 8) + tq(0.8, 8)) * se_L
    l[f"feasibleL_power_at_dL0|{lvl_name}|df8"] = float(W.t_sf(tq(1 - lvl, 8) - tau_L / se_L, 8))
    for ratio in (1.0, 2.0, 3.0):    # true sigma = ratio x s (the 2-df risk)
        l[f"feasibleL_power_at_dL0|{lvl_name}|sigma={ratio}s"] = norm_sf(zq(1 - lvl) - tau_L / (ratio * se_L))
OUT["L"] = l

# ---------------------------------------------------------------- 5. costs (measured bases from check-W3 §2.5)
RATE = 1.79
FRE = 2934.0
EVAL_S = (2714.0, 49 * 60.0)               # eval-only state: measured slot minus training; upper: the 49-min slot (check-W3 convention)
POD_OH_MIN = (18.9, 26.0)
CONT = 1.25


def money(states, sec_per_state, jobs_per_pod=4, overhead=True):
    lo = states * sec_per_state[0] / 3600 * RATE
    hi = states * sec_per_state[1] / 3600 * RATE
    pods = math.ceil(states / jobs_per_pod) if overhead else 0
    ohlo, ohhi = pods * POD_OH_MIN[0] / 60 * RATE, pods * POD_OH_MIN[1] / 60 * RATE
    return dict(states=states, measured=(round(lo, 2), round(hi, 2)), with_overhead_x1_25=(round((lo + ohlo) * CONT, 2),
                round((hi + ohhi) * CONT, 2)), pods=pods)


c = {}
c["refs_on_six_a0_seeds_extra_12_eval_states"] = money(12, EVAL_S)
c["lambda_0.9_at_six_seeds_6_eval_states"] = money(6, EVAL_S)
c["extra_reference_states_at_1107_under_D1_4_states"] = money(4, EVAL_S)
c["recipe_G_4_more_seeds_training_arms"] = money(4, (FRE, 49 * 60.0))
c["recipe_G_6_new_seeds_if_not_reused"] = money(6, (FRE, 49 * 60.0))
per_prompt = (1.06 + 0.16, 3.74 + 0.16)       # s per O-ext prompt (lean sampled-answer rate; Gate A greedy average)
oext_state = (400 * per_prompt[0], 400 * per_prompt[1])
c["oext_seconds_per_state"] = oext_state
c["oext_all_arms_93_states_in_job"] = money(93, oext_state, overhead=False)
c["oext_targeted_49_states_in_job"] = money(49, oext_state, overhead=False)
c["oext_regenerate_6_reused_units"] = round(6 * 0.077 * RATE, 2)
c["basis"] = dict(rate=RATE, FRE_s=FRE, eval_state_s=EVAL_S, pod_overhead_min=POD_OH_MIN, contingency=CONT,
                  jobs_per_pod=4, oext_s_per_prompt=per_prompt)
OUT["cost"] = c

# ---------------------------------------------------------------- 6. a 'beats a reference' MDE (one reference, U only)
b = {}
for name, sd_pair, n_pairs in (("N4 pair SD 1.83", 1.83, 5), ("N1 pair SD 3.75", 3.75, 5), ("N4 6 pairs (D1)", 1.83, 6)):
    for sd_d in (2.1, 3.0):
        se = math.sqrt(sd_pair ** 2 + sd_d ** 2) / math.sqrt(n_pairs)
        for lvl_name, lvl in (("one_sided_5pct", 0.05), ("holm6_first_one_sided", 0.05 / 6)):
            b[f"{name}|sd_d {sd_d}|{lvl_name}"] = (tq(1 - lvl, 2 * (n_pairs - 1)) + tq(0.8, 2 * (n_pairs - 1))) * se
OUT["beats_reference_MDE80"] = b

(HERE / "evidence/stage1_numbers.json").write_text(json.dumps(OUT, indent=1, default=float))
print(json.dumps(OUT, indent=1, default=lambda x: float(x)))
