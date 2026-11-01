"""The verifier's own coverage simulation of S-G coherent (D-5) beside the primary form, on worlds the builder's
simulation does not hold (synthetic, seeded; no study data). The estimator here is the verifier's own code (float x,
own seed part, own prompt part, own Satterthwaite df); B16's REML (reml.fit_cells with the pinned options) and B16's
tdist are used as black boxes. It never imports scripts.stage1_s1.reading_input.

    python -B my_sim.py --reps N --workers 8 --worlds A,B,... --out FILE

Model (logit): mu_a + eta_p + gamma_ap + s_j + e_aj; eta ~ N(-0.2, 2.5^2) shared, gamma ~ N(0, 0.3^2) per arm,
s_j ~ N(0, 0.25^2) per cluster and seed, e_aj ~ N(0, 0.15^2). mu: a0 +0.4, S1 0, S3 -0.1, S4 +0.05 (full cluster);
R +0.3, A1 -0.2, L1 +0.25, H1 +0.35 (removal cluster). Worlds (failure probabilities per answer):
- A  both-same: S1 and S3 fail 95% on the same random 8% of prompts (fixed over seeds), 5% elsewhere; others 5%.
- B  seed-varying: S1 fails 95% on a random 8% of prompts drawn anew at each seed; others 5%.
- C  one-bad-seed: S1 at seed 1104 fails 95% on a random 35% of prompts (about 35% of its answers there; pooled over
     its 6 seeds about 8%, under the bar), 3% elsewhere; others 5%.
- D  comparator: a0 fails 95% on a random 8% of prompts (fixed over seeds); others 5%.
- E  harm-linked-top: S1's Unsafe answers on its top 10% of prompts by eta fail 60%, all else 5%; others 5%.
- F  removal-R: (removal cluster) R fails 95% on a random 8% of prompts (fixed over seeds); others 5%.
- G  removal-both: (removal cluster) R and A1 fail 95% on the same random 6% of prompts, 5% elsewhere; others 5%.
The truth: per arm the mean over t ~ N(0, 0.25^2 + 0.15^2) of the population pooled coherent share (G2) or of the
mean Unsafe share (plain); where failures are independent of the outcome the two coincide (worlds A-D, F, G); world
E's coherent truth is computed by Monte Carlo over 4 million prompts per Gauss-Hermite node (common random numbers).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time

import numpy as np

from scripts.stage1_s1.reading import reml, tdist
from scripts.stage1_s1.reading.settings import design, settings

ITEMS, ANS = 200, 3
MU = {"a0": 0.4, "S1": 0.0, "S3": -0.1, "S4": 0.05, "R": 0.3, "A1": -0.2, "L1": 0.25, "H1": 0.35}
ETA_M, ETA_SD, G_SD, S_SD, E_SD = -0.2, 2.5, 0.3, 0.25, 0.15
WORLD_CLUSTER = {"A": "full", "B": "full", "C": "full", "D": "full", "E": "full", "F": "removal", "G": "removal"}
LEVEL, TAIL = 0.90, 0.0075


def expit(z):
    return 1.0 / (1.0 + np.exp(-z))


def fail_matrix(world, arm, seed, rng, eta, unsafe, fixed):
    f = np.full((ITEMS, ANS), 0.05)
    if world == "A" and arm in ("S1", "S3"):
        f[fixed["A"]] = 0.95
    elif world == "B" and arm == "S1":
        f[rng.random(ITEMS) < 0.08] = 0.95
    elif world == "C" and arm == "S1":
        f[:] = 0.03
        if seed == 1104:
            f[rng.random(ITEMS) < 0.35] = 0.95
    elif world == "D" and arm == "a0":
        f[fixed["D"]] = 0.95
    elif world == "E" and arm == "S1":
        top = eta > ETA_M + ETA_SD * 1.2815515655446004        # the population 90th percentile (as the truth)
        f = np.where(unsafe & top[:, None], 0.60, 0.05)
    elif world == "F" and arm == "R":
        f[fixed["F"]] = 0.95
    elif world == "G" and arm in ("R", "A1"):
        f[fixed["G"]] = 0.95
    return f


def x_float(n, u):
    big_n, big_u = n.sum(), u.sum()
    if big_n == 0:
        return None
    v = big_u / big_n
    return v + (u - v * n) / (big_n / ITEMS)


def item_part(d):
    j, p = d.shape
    g = d.mean()
    rm = d.mean(axis=1, keepdims=True)
    cm = d.mean(axis=0, keepdims=True)
    ms_p = j * float(((cm - g) ** 2).sum()) / (p - 1)
    ms_e = float(((d - rm - cm + g) ** 2).sum()) / ((p - 1) * (j - 1))
    k = 1.0e4 / (p * j)
    v = max(0.0, ms_p - ms_e) * k
    q = ((ms_p * k) ** 2 / (p - 1) + (ms_e * k) ** 2 / ((p - 1) * (j - 1))) if ms_p > ms_e else 0.0
    return v, q


def read_form(table, dsg, cluster, contrasts, opts, floor):
    arms = [a for a in dsg.fit_arms if dsg.cluster[a] == cluster and any((a, j) in table for j in dsg.seeds[a])]
    cells = [(a, j, float(100.0 * table[(a, j)].mean())) for a in arms for j in dsg.seeds[a] if (a, j) in table]
    try:
        fit = reml.fit_cells(cells, tuple(arms), floor, **opts)
    except ValueError:
        return {name: None for name, _, _ in contrasts}
    out = {}
    for name, c, m in contrasts:
        common = sorted(set(dsg.seeds[c]) & set(dsg.seeds[m]))
        held = [j for j in common if (c, j) in table and (m, j) in table]
        if len(held) < 2:
            out[name] = None
            continue
        diffs = np.array([100.0 * table[(c, j)].mean() - 100.0 * table[(m, j)].mean() for j in held])
        d = np.stack([table[(c, j)] - table[(m, j)] for j in held])
        jj = len(held)
        if len(held) < len(common):
            v_seed, df_seed = float(diffs.var(ddof=1)) / jj, jj - 1.0
        else:
            i, k = fit.arms.index(c), fit.arms.index(m)
            v_seed = (fit.sigma2[c] + fit.sigma2[m]) / jj
            var_v = (fit.info_inv[i, i] + fit.info_inv[k, k] + 2.0 * fit.info_inv[i, k]) / jj ** 2
            df_seed = 2.0 * v_seed * v_seed / var_v if var_v > 0 else math.inf
        v_item, q = item_part(d)
        v = v_seed + v_item
        den = (v_seed * v_seed / df_seed if math.isfinite(df_seed) else 0.0) + q
        df = v * v / den if den > 0 else math.inf
        if not (v > 0 and math.isfinite(df)):
            out[name] = None
            continue
        out[name] = (float(diffs.mean()), math.sqrt(v), df)
    return out


def task(args):
    world, base, start, count = args
    dsg, cfg = design("plan_a"), settings()
    opts, floor = reml.options(cfg), float(cfg["endpoints"]["U"]["floor"])
    cluster = WORLD_CLUSTER[world]
    arms = dsg.cluster_arms(cluster)
    contrasts = [(n, c, m) for n, c, m in dsg.contrasts if dsg.cluster[c] == cluster]
    rows = []
    for rep in range(start, start + count):
        rng = np.random.default_rng([base, ord(world), rep])
        eta = rng.normal(ETA_M, ETA_SD, ITEMS)
        fixed = {"A": rng.random(ITEMS) < 0.08, "D": rng.random(ITEMS) < 0.08, "F": rng.random(ITEMS) < 0.08,
                 "G": rng.random(ITEMS) < 0.06}
        seeds = sorted({j for a in arms for j in dsg.seeds[a]})
        shift = {j: rng.normal(0, S_SD) for j in seeds}
        coh, plain, fail_share = {}, {}, []
        for a in arms:
            gam = rng.normal(0, G_SD, ITEMS)
            for j in dsg.seeds[a]:
                pi = expit(MU[a] + eta + gam + shift[j] + rng.normal(0, E_SD))
                unsafe = rng.random((ITEMS, ANS)) < pi[:, None]
                f = fail_matrix(world, a, j, rng, eta, unsafe, fixed)
                fails = rng.random((ITEMS, ANS)) < f
                n, u = (~fails).sum(axis=1), (unsafe & ~fails).sum(axis=1)
                x = x_float(n, u)
                if x is not None:
                    coh[(a, j)] = x
                plain[(a, j)] = unsafe.sum(axis=1) / 3.0
                fail_share.append((a, float(fails.mean())))
        rows.append({"coherent": read_form(coh, dsg, cluster, contrasts, opts, floor),
                     "primary": read_form(plain, dsg, cluster, contrasts, opts, floor),
                     "fail": fail_share})
    return rows


def plain_truth(arm):
    gx, gw = np.polynomial.hermite_e.hermegauss(200)
    sd = math.sqrt(ETA_SD ** 2 + G_SD ** 2 + S_SD ** 2 + E_SD ** 2)
    return float((gw / gw.sum()) @ expit(MU[arm] + ETA_M + sd * gx))


def coherent_truth_e(arm):
    """World E's S1: mean over t of E[pi (1 - f1)] / E[pi (1 - f1) + (1 - pi) 0.95] by Monte Carlo (4e6 prompts)."""
    if arm != "S1":
        return plain_truth(arm)
    rng = np.random.default_rng(99)
    eta = rng.normal(ETA_M, ETA_SD, 4_000_000)
    gam = rng.normal(0, G_SD, eta.size)
    top = eta > ETA_M + ETA_SD * 1.2815515655446004          # the population 90th percentile
    f1 = np.where(top, 0.60, 0.05)
    gx, gw = np.polynomial.hermite_e.hermegauss(40)
    gw = gw / gw.sum()
    vals = []
    for t in gx * math.sqrt(S_SD ** 2 + E_SD ** 2):
        pi = expit(MU[arm] + eta + gam + t)
        a = float(np.mean(pi * (1 - f1)))
        b = float(np.mean((1 - pi) * 0.95))
        vals.append(a / (a + b))
    return float(gw @ np.array(vals))


def summarize(world, rows):
    dsg = design("plan_a")
    cluster = WORLD_CLUSTER[world]
    contrasts = [(n, c, m) for n, c, m in dsg.contrasts if dsg.cluster[c] == cluster]
    out = {}
    for name, c, m in contrasts:
        rec = {}
        for form in ("coherent", "primary"):
            if form == "coherent" and world == "E":
                truth = 100.0 * (coherent_truth_e(c) - coherent_truth_e(m))
            else:
                truth = 100.0 * (plain_truth(c) - plain_truth(m))
            got = [r[form][name] for r in rows if r[form][name] is not None]
            cover = tail = 0
            ests, ses, dfs = [], [], []
            for est, se, df in got:
                half = tdist.t_quantile(0.5 + LEVEL / 2.0, df) * se
                cover += est - half <= truth <= est + half
                tail += tdist.t_two_sided((est - truth) / se, df) < TAIL
                ests.append(est), ses.append(se), dfs.append(df)
            k = len(got)
            cov = cover / k
            rec[form] = {"truth_pp": truth, "n": k, "coverage": cov, "coverage_mc_se": math.sqrt(cov * (1 - cov) / k),
                         "tail": tail / k, "tail_events": tail, "bias_pp": float(np.mean(ests)) - truth,
                         "bias_mc_se": float(np.std(ests, ddof=1)) / math.sqrt(k),
                         "sd_over_se": float(np.std(ests, ddof=1)) / float(np.mean(ses)),
                         "median_df": float(np.median(dfs))}
        p = rec["primary"]["tail"]
        rec["tail_ratio"] = rec["coherent"]["tail"] / p if p > 0 else None
        rec["meets"] = bool(0.88 <= rec["coherent"]["coverage"] <= 0.92 and rec["tail_ratio"] is not None
                            and rec["tail_ratio"] <= 1.5)
        out[name] = rec
    fails = {}
    for r in rows:
        for a, s in r["fail"]:
            fails.setdefault(a, []).append(s)
    return {"contrasts": out, "mean_failing_share": {a: float(np.mean(v)) for a, v in fails.items()}}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=2000)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--worlds", default="A,B,C,D,E,F,G")
    p.add_argument("--seed", type=int, default=777)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    import multiprocessing as mp
    result = {}
    for world in a.worlds.split(","):
        t0 = time.monotonic()
        tasks = [(world, a.seed, s, min(100, a.reps - s)) for s in range(0, a.reps, 100)]
        with mp.get_context("spawn").Pool(a.workers) as pool:
            parts = pool.map(task, tasks)
        rows = [r for part in parts for r in part]
        result[world] = summarize(world, rows)
        result[world]["seconds"] = round(time.monotonic() - t0, 1)
        result[world]["reps"] = len(rows)
        for name, rec in result[world]["contrasts"].items():
            c, pr = rec["coherent"], rec["primary"]
            print(f"{world} {name}: coherent cov {c['coverage']:.4f} (MC SE {c['coverage_mc_se']:.4f}) tail {c['tail']:.4f} "
                  f"({c['tail_events']}) | primary cov {pr['coverage']:.4f} tail {pr['tail']:.4f} ({pr['tail_events']}) | "
                  f"ratio {rec['tail_ratio'] if rec['tail_ratio'] is None else round(rec['tail_ratio'], 2)} | "
                  f"truth {c['truth_pp']:+.3f} bias {c['bias_pp']:+.3f}+-{c['bias_mc_se']:.3f} sd/se {c['sd_over_se']:.3f} "
                  f"(prim {pr['sd_over_se']:.3f}) df {c['median_df']:.1f} (prim {pr['median_df']:.1f}) n {c['n']} "
                  f"{'met' if rec['meets'] else 'NOT met'}", flush=True)
        print(f"{world}: {len(rows)} reps, {result[world]['seconds']} s, mean failing share "
              f"{ {k: round(v, 3) for k, v in result[world]['mean_failing_share'].items()} }", flush=True)
    with open(a.out, "x") as h:
        json.dump({"reps": a.reps, "seed": a.seed, "worlds": result}, h, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
