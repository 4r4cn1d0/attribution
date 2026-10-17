#!/usr/bin/env python3
"""review_stats_sim.py: seed-level checks for the statistics review of stage1-preregistration-DRAFT.md (revision 1).

Planning simulation only. It reads no evaluation record, no row, prompt, answer or anchor file, and no Gate B output.
Every input is a number stated in the draft or its sources (per-arm SD 2.65 / 3.85 pp, pair SD 1.83 / 3.75 / 4.5 pp,
rho 0 / 0.76, a0 over-refusal 4-6 of 100, theta0 17 of 100, tau_L = 2*sqrt(2)*s). The t-distribution helpers are
imported read-only from research/experiments/2026-10-17-stage1-analysis-model/sim_w2.py (numpy only; no scipy here).

Run (no bytecode is written into the main checkout):
    PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B \
        review_stats_sim.py
Writes review_stats_sim_out.txt beside this file. Every random stream has a fixed seed.

Parts:
  A  "better"-label power against the test MDE (S-a, S-aW), the plan-A cut included.
  B  The one-sided O "worse" family under S-a when the O seed variance grows with the O level (binomial scaling).
  C  The false-"worse" rate over the U, O and L families (global null, and a realistic mix with heteroscedastic O).
  D  Wrong-sign (directional) errors of Holm over P1-P6 under S-a.
  E  The tau_L screen: null failure rate given the 2-df s (unconditional, s < 0.5 sigma, s = 0.5 sigma, s = sigma).
  F  Label partitions: "worse (U)" with "equivalent", and "significant, below the SESOI" without "equivalent".
  G  The effective df of S-a's pooled variance when seeds are shared (rho 0.76).
  H  S-a family-wise rate with one arm at 3x SD (replicates AMD SIM H2 at seed level).
"""
import importlib.util
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SIMW2 = pathlib.Path("/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-analysis-model/sim_w2.py")
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("sim_w2_ro", SIMW2)
W = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(W)
t_p2, t_sf, t_ppf = W.t_p2, W.t_sf, W.t_ppf

OUT = []


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


ARMS = ["a0", "R", "A1", "L1", "H1", "S1", "S3", "S4"]
SEEDS = list(range(1101, 1109))
ARM_SEEDS = {"a0": list(range(1101, 1107)), "R": list(range(1101, 1109))}
for _a in ("A1", "L1", "H1", "S1", "S3", "S4"):
    ARM_SEEDS[_a] = list(range(1102, 1108))
CONTRASTS = [("P1", "R", "A1"), ("P2", "R", "L1"), ("P3", "R", "H1"), ("P4", "a0", "S1"), ("P5", "S1", "S3"),
             ("P6", "S1", "S4")]
NARM = np.array([len(ARM_SEEDS[a]) for a in ARMS])
DF_POOL = int(NARM.sum() - len(ARMS))  # 42


def holm(p, alpha=0.05):
    m = p.shape[-1]
    order = np.argsort(p, axis=-1)
    ps = np.take_along_axis(p, order, -1)
    thr = alpha / (m - np.arange(m))
    ok = np.cumprod(ps <= thr, axis=-1).astype(bool)
    rej = np.zeros_like(ok)
    np.put_along_axis(rej, order, ok, -1)
    return rej


def draw_cells(rng, B, sd_arm, rho, mu=None):
    """Cells U[a][:, j] for the D0 seed plan. sd_arm: per-arm total SD (array of 8); rho: share of the
    reference variance (sd_ref**2) that is a shared seed shift; arms with a larger SD carry the extra as arm noise."""
    sd_arm = np.asarray(sd_arm, float)
    sd_ref = float(np.min(sd_arm))
    sd_s = math.sqrt(rho) * sd_ref
    s = rng.standard_normal((B, len(SEEDS))) * sd_s
    cells = {}
    for ai, a in enumerate(ARMS):
        idx = [SEEDS.index(x) for x in ARM_SEEDS[a]]
        sd_e = math.sqrt(max(sd_arm[ai] ** 2 - sd_s ** 2, 0.0))
        e = rng.standard_normal((B, len(idx))) * sd_e
        m = 0.0 if mu is None else mu[ai]
        cells[a] = m + s[:, idx] + e
    return cells


def stats(cells, method):
    """Return est (B,6) = mean(comparator) - mean(repair) (or paired), se (B,6), df (B,6)."""
    B = next(iter(cells.values())).shape[0]
    means = {a: cells[a].mean(1) for a in ARMS}
    vars_ = {a: cells[a].var(1, ddof=1) for a in ARMS}
    est = np.zeros((B, 6)); se = np.zeros((B, 6)); df = np.zeros((B, 6))
    if method == "a":
        pooled = sum(vars_[a] * (len(ARM_SEEDS[a]) - 1) for a in ARMS) / DF_POOL
    for k, (_, c, m) in enumerate(CONTRASTS):
        nc, nm = len(ARM_SEEDS[c]), len(ARM_SEEDS[m])
        if method == "a":
            est[:, k] = means[c] - means[m]
            se[:, k] = np.sqrt(pooled * (1 / nc + 1 / nm))
            df[:, k] = DF_POOL
        elif method == "aW":
            est[:, k] = means[c] - means[m]
            vc, vm = vars_[c] / nc, vars_[m] / nm
            se[:, k] = np.sqrt(vc + vm)
            df[:, k] = (vc + vm) ** 2 / (vc ** 2 / (nc - 1) + vm ** 2 / (nm - 1))
        elif method == "b":  # paired per contrast on the common seeds, J - 1 df (exact under normality)
            common = sorted(set(ARM_SEEDS[c]) & set(ARM_SEEDS[m]))
            ic = [ARM_SEEDS[c].index(x) for x in common]
            im = [ARM_SEEDS[m].index(x) for x in common]
            d = cells[c][:, ic] - cells[m][:, im]
            J = len(common)
            est[:, k] = d.mean(1)
            se[:, k] = d.std(1, ddof=1) / math.sqrt(J)
            df[:, k] = J - 1
    return est, se, df


# ----------------------------------------------------------------------------------------------------------------
def part_A(reps=100_000):
    say("\n== A. 'better' label (Holm rejects AND estimate >= 5 pp) against the Holm test alone; one contrast true, five null ==")
    scen = [("PLAN-S central: per-arm SD 2.65, rho 0 (pair SD 3.75)", 2.65, 0.0),
            ("wave-0a: per-arm SD 2.65, rho 0.76 (pair SD 1.83)", 2.65, 0.76),
            ("high: per-arm SD 3.85, rho 0 (pair SD 5.45)", 3.85, 0.0),
            ("plan-A cut, rho 0: pair SD 4.5 (per-arm 3.18)", 4.5 / math.sqrt(2), 0.0),
            ("plan-A cut, rho 0.76: pair SD 4.5 (per-arm 6.50)", 4.5 / math.sqrt(2 * 0.24), 0.76)]
    grid = np.round(np.arange(0.0, 16.01, 0.05), 2)
    alpha = 0.05
    for name, sd, rho in scen:
        rng = np.random.default_rng(11)
        cells = draw_cells(rng, reps, [sd] * 8, rho)
        for method in ("a", "b"):  # S-a (in force) and the exact paired test (b) as a lower bound on HB's power
            est0, se, df = stats(cells, method)
            p_null = t_p2(est0 / se, df)
            row = []
            for k in (0, 3):  # P1 and P4
                # Holm: contrast k is rejected iff p_k <= alpha / (6 - r), r = length of the passing chain among the
                # other five p-values (q_1 <= alpha/6, q_2 <= alpha/5, ...). df is constant per contrast here.
                q = np.sort(np.delete(p_null, k, axis=1), axis=1)
                thr = alpha / (6 - np.arange(5))
                r = np.cumprod(q <= thr[None, :], axis=1).sum(1)
                crit_by_r = np.array([t_ppf(1 - alpha / (6 - rr) / 2, float(df[0, k])) for rr in range(6)])
                crit = crit_by_r[r]
                pow_t, pow_b = [], []
                for th in grid:
                    est_k = est0[:, k] + th
                    rej = np.abs(est_k) / se[:, k] > crit
                    pow_t.append(np.mean(rej & (est_k > 0)))
                    pow_b.append(np.mean(rej & (est_k >= 5.0)))
                pow_t, pow_b = np.array(pow_t), np.array(pow_b)
                mde_t = grid[np.argmax(pow_t >= 0.8)] if (pow_t >= 0.8).any() else float("nan")
                mde_b = grid[np.argmax(pow_b >= 0.8)] if (pow_b >= 0.8).any() else float("nan")
                at5 = pow_b[np.argmin(np.abs(grid - 5.0))]
                row.append(f"{CONTRASTS[k][0]}: test MDE80 {mde_t:.2f}, 'better' 80% at {mde_b:.2f}, P(better | 5 pp) {at5:.2f}")
            say(f"  [{method}] {name}: " + "; ".join(row))


# ----------------------------------------------------------------------------------------------------------------
def part_B(reps=200_000):
    say("\n== B. O 'worse' family: one-sided adverse Holm over 6 at 5%; O seed SD grows with the O level ==")
    say("   adverse = O(repair) - O(comparator) > 0. Nulls counted: P1-P3, P5, P6. P4 (S1 vs a0) is a true adverse change when add arms sit at 12 or 17 pp.")

    def sd_at(level, sd5):
        return sd5 * math.sqrt(level * (100 - level) / (5 * 95))

    sd5 = 1.5
    cases = [("B0 global null, every arm at 5 pp (equal SDs)", [5] * 8, 0.0),
             ("B1 removal arms and a0 at 5 pp; S1, S3, S4 at 17 pp (theta0 level)", [5, 5, 5, 5, 5, 17, 17, 17], 0.0),
             ("B2 as B1 with S1, S3, S4 at 12 pp", [5, 5, 5, 5, 5, 12, 12, 12], 0.0),
             ("B3 as B1 with a shared seed shift (rho 0.5)", [5, 5, 5, 5, 5, 17, 17, 17], 0.5)]
    for name, lev, rho in cases:
        sds = [sd_at(x, sd5) for x in lev]
        rng = np.random.default_rng(23)
        cells = draw_cells(rng, reps, sds, rho, mu=np.array(lev, float))
        res = []
        for method in ("a", "aW", "b"):
            est, se, df = stats(cells, method)
            adverse = -est  # est = comparator - repair; adverse is repair - comparator > 0
            p1 = t_sf(adverse / se, df)
            rej = holm(p1)
            nulls = [0, 1, 2, 4, 5] if lev[5] != lev[0] else [0, 1, 2, 3, 4, 5]
            any_false = rej[:, nulls].any(1).mean()
            p56 = rej[:, [4, 5]].any(1).mean()
            res.append(f"{method}: any false 'worse (O)' {100 * any_false:.1f}% (P5 or P6 {100 * p56:.1f}%)")
        say(f"  {name} [SD ratio add/removal {sds[5] / sds[0]:.2f}]: " + "; ".join(res))


# ----------------------------------------------------------------------------------------------------------------
def part_C(reps=200_000):
    say("\n== C. False 'worse' over three families (U two-sided Holm-6; O and L one-sided Holm-6), S-a form ==")

    def run(mu_u, lev_o, sd_o5, label, method="a"):
        rng = np.random.default_rng(37)
        cu = draw_cells(rng, reps, [2.65] * 8, 0.0, mu=np.array(mu_u, float))
        sds_o = [sd_o5 * math.sqrt(x * (100 - x) / 475) for x in lev_o]
        co = draw_cells(rng, reps, sds_o, 0.0, mu=np.array(lev_o, float))
        cl = draw_cells(rng, reps, [1.0] * 8, 0.0)
        eu, su, du = stats(cu, method)
        rej_u = holm(t_p2(eu / su, du))
        true_u = np.array([(mu_u[ARMS.index(c)] - mu_u[ARMS.index(m)]) for _, c, m in CONTRASTS])
        fw_u = (rej_u & (eu < 0) & (true_u[None, :] >= 0)).any(1)
        eo, so, do = stats(co, method)
        rej_o = holm(t_sf(-eo / so, do))
        true_o = np.array([(lev_o[ARMS.index(m)] - lev_o[ARMS.index(c)]) for _, c, m in CONTRASTS])
        fw_o = (rej_o & (true_o[None, :] <= 0)).any(1)
        el, sl, dl = stats(cl, method)
        rej_l = holm(t_sf(-el / sl, dl))
        fw_l = rej_l.any(1)
        anyf = (fw_u | fw_o | fw_l).mean()
        say(f"  [{method}] {label}: any false 'worse' {100 * anyf:.1f}% (U {100 * fw_u.mean():.1f}, O {100 * fw_o.mean():.1f}, L {100 * fw_l.mean():.1f})")

    run([0] * 8, [5] * 8, 1.5, "global null, equal SDs")
    # realistic mix (CK-3 section 3.2): P1, P3 +2; P2 0; S arms restore 10 pp (P4 +10, P5 = P6 = 0)
    mu_u = [50, 48, 46, 48, 46, 40, 40, 40]
    run(mu_u, [5, 5, 5, 5, 5, 17, 17, 17], 1.5, "realistic mix; add arms at O = 17 pp (binomial SD scaling)")
    run(mu_u, [5, 5, 5, 5, 5, 17, 17, 17], 1.5, "realistic mix; add arms at O = 17 pp (binomial SD scaling)", method="aW")
    say("  Union bound for the global null: 2.5% (U, adverse tail) + 5% (O) + 5% (L) = 12.5%.")


# ----------------------------------------------------------------------------------------------------------------
def part_D(reps=200_000):
    say("\n== D. Wrong-sign errors: Holm over P1-P6, two-sided, S-a; the sign of a rejection gives the claim ==")
    rng = np.random.default_rng(41)
    for rho in (0.0, 0.76):
        cells = draw_cells(rng, reps, [2.65] * 8, rho)
        est0, se, df = stats(cells, "a")
        se_true = 2.65 * np.array([math.sqrt(1 / 8 + 1 / 6)] * 3 + [math.sqrt(1 / 3)] * 3)
        configs = {
            "all +0.5 SE": 0.5 * se_true,
            "P1-P3 +1 SE, P4-P6 -1 SE": np.r_[se_true[:3], -se_true[3:]],
            "P1 +3 SE, others -0.5 SE": np.r_[3 * se_true[0], -0.5 * se_true[1:]],
            "all -0.25 SE": -0.25 * se_true,
            "P4 +4 SE, P5 -0.5 SE, P6 -0.5 SE, P1-P3 +0.5 SE": np.r_[0.5 * se_true[:3], 4 * se_true[3], -0.5 * se_true[4:]],
        }
        for name, lam in configs.items():
            est = est0 + lam[None, :]
            rej = holm(t_p2(est / se, df))
            wrong = (rej & (np.sign(est) != np.sign(lam)[None, :])).any(1).mean()
            say(f"  rho {rho}: {name}: P(any wrong-sign claim) {100 * wrong:.2f}%")


# ----------------------------------------------------------------------------------------------------------------
def part_E(reps=2_000_000):
    say("\n== E. tau_L = 2*sqrt(2)*s with s from 3 a0 seeds (2 df); a null arm, 6 against 6, SE from 42 pooled df ==")
    rng = np.random.default_rng(53)
    sigma = 1.0
    s = sigma * np.sqrt(rng.chisquare(2, reps) / 2)
    tau = 2 * math.sqrt(2) * s
    se_true = sigma * math.sqrt(1 / 3)
    lam = rng.standard_normal(reps) * se_true
    se_hat = se_true * np.sqrt(rng.chisquare(DF_POOL, reps) / DF_POOL)
    for name, q in (("R1.2 bound (two-sided 90% upper end, t 0.95)", t_ppf(0.95, DF_POOL)),
                    ("one-sided 90% bound (t 0.90)", t_ppf(0.90, DF_POOL))):
        fail = lam + q * se_hat > tau
        cond = s < 0.5 * sigma
        say(f"  {name}: unconditional fail {100 * fail.mean():.1f}%; given s < 0.5 sigma {100 * fail[cond].mean():.1f}% "
            f"(P(s < 0.5 sigma) = {cond.mean():.3f}); given s < sigma {100 * fail[s < sigma].mean():.1f}%")
        for ratio in (0.5, 1.0):
            t_fix = 2 * math.sqrt(2) * ratio * sigma
            say(f"     at s = {ratio} sigma exactly: fail {100 * np.mean(lam + q * se_hat > t_fix):.1f}%")


# ----------------------------------------------------------------------------------------------------------------
def part_F(reps=200_000):
    say("\n== F. Label partitions for one contrast (P1), the other five null ==")
    for name, method, sd, rho in (("S-a, per-arm 2.65, rho 0", "a", 2.65, 0.0),
                                  ("paired (b), per-arm 2.65, rho 0.76 (pair SD 1.83)", "b", 2.65, 0.76)):
        rng = np.random.default_rng(61)
        cells = draw_cells(rng, reps, [sd] * 8, rho)
        est0, se, df = stats(cells, method)
        p_null = t_p2(est0 / se, df)
        q90 = np.array([t_ppf(0.95, d) for d in df[0]])[None, :]
        for th in (-3.0, -2.5, -2.0, 3.0, 4.0, 4.5):
            est = est0.copy(); est[:, 0] += th
            p = p_null.copy(); p[:, 0] = t_p2(est[:, 0] / se[:, 0], df[:, 0])
            rej = holm(p)[:, 0]
            e = est[:, 0]
            equiv = (e - q90[:, 0] * se[:, 0] > -5) & (e + q90[:, 0] * se[:, 0] < 5)
            worse_u = rej & (e < 0)
            sig_below = rej & (e > 0) & (e < 5)
            say(f"  {name}: true {th:+.1f} pp: P(worse (U) and equivalent) {np.mean(worse_u & equiv):.3f}; "
                f"P(significant below SESOI, not equivalent -> headline 'inconclusive') {np.mean(sig_below & ~equiv):.3f}; "
                f"P(significant below SESOI and equivalent) {np.mean(sig_below & equiv):.3f}")


# ----------------------------------------------------------------------------------------------------------------
def part_G(reps=200_000):
    say("\n== G. Effective df of S-a's pooled variance when the eight arms share seeds ==")
    for rho in (0.0, 0.3, 0.76):
        rng = np.random.default_rng(71)
        cells = draw_cells(rng, reps, [1.0] * 8, rho)
        pooled = sum(cells[a].var(1, ddof=1) * (len(ARM_SEEDS[a]) - 1) for a in ARMS) / DF_POOL
        dfe = 2 * pooled.mean() ** 2 / pooled.var()
        say(f"  rho {rho}: nominal df {DF_POOL}; effective df (2 E^2 / Var) {dfe:.1f}")


def part_H(reps=200_000):
    say("\n== H. S-a family-wise rate with A1 at 3x the seed SD (rho 0), global null ==")
    rng = np.random.default_rng(83)
    sds = [2.65] * 8; sds[ARMS.index("A1")] = 3 * 2.65
    cells = draw_cells(rng, reps, sds, 0.0)
    for method in ("a", "aW", "b"):
        est, se, df = stats(cells, method)
        rej = holm(t_p2(est / se, df))
        say(f"  [{method}] FWER {100 * rej.any(1).mean():.1f}%; P1 alone {100 * rej[:, 0].mean():.2f}%")


if __name__ == "__main__":
    say("review_stats_sim.py; numpy", np.__version__)
    part_H()
    part_G()
    part_E()
    part_B()
    part_C()
    part_D()
    part_F()
    part_A()
    (HERE / "review_stats_sim_out.txt").write_text("\n".join(OUT) + "\n")
