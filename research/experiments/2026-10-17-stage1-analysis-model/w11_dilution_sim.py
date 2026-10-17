"""W11 check: how much of the planted sweep's M-trend comes from plant dilution (synthetic numbers only).

Row-level model of the lead's L15 (6): Dolly row scores N(u_g, 1), plant row scores N(mu, 1),
AUC = Phi(mu / sqrt 2), grid {0.5, 0.6, 0.75, 0.9}. u_g is a unit (category) effect: tau = 0 is
L15's model; tau = 0.25 row-SD is a sensitivity (I). Cells as in build_plant.json: 8 units x 600,
4 quartiles x 150, 4 quarters 37/38/37/38. The plant (k = 37) replaces one 37-row leaf.

Designs:
  A  the committed nested design: plant share of its cell 37/600, 37/150, 37/37 at M = 8, 32, 128;
  B  options only: every cell is a 37-row leaf (share 100%), M - 1 competitor leaves;
  C  dilution only: M = 8 cells of n = 600, 150 or 37 rows (share 6.2%, 24.7%, 100%).
Aggregation: mean (L15 (6)); design A also with max and the 90th percentile.
Hit: planted cell ranked first; and in the top k = max(1, M / 8).
Placement: the 90% range of the empirical row AUC (37 plant vs 4,763 Dolly rows) at each grid point,
against the binary top-1 hit that L15 (7) uses to place a scorer on the grid.
No real data are read. Output: printed tables and w11_dilution_sim_out.json beside this file.
"""
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np

AUCS = [0.5, 0.6, 0.75, 0.9]
K = 37
LEAF = np.array([37, 38, 37, 38])           # quarter sizes in a 150-row quartile
REPS = 20000
REPS_ROWS = 2000
OUT = Path(__file__).with_name("w11_dilution_sim_out.json")


def mu_of(auc):
    return math.sqrt(2.0) * NormalDist().inv_cdf(auc)


def ranks_first(scores, planted_index):
    """scores: (reps, M); returns P(rank 1) and the rank array (1 = best)."""
    planted = scores[:, planted_index][:, None]
    rank = 1 + (scores > planted).sum(axis=1)
    return rank


def design_a_mean(mu, tau, rng):
    """Nested design, mean aggregation, from leaf sums (exact for normal rows)."""
    sizes = np.tile(LEAF, 32)                      # 128 leaves: unit g = leaf // 16
    unit = np.repeat(np.arange(8), 16)
    u = rng.normal(0.0, tau, size=(REPS, 8)) if tau > 0 else np.zeros((REPS, 8))
    # leaf sums of Dolly rows: n * u_g + N(0, n)
    sums = sizes * u[:, unit] + rng.normal(0.0, 1.0, size=(REPS, 128)) * np.sqrt(sizes)
    # leaf 0 (unit 0, quartile 0, quarter 0, 37 rows) holds the plant instead: 37 * mu + N(0, 37)
    sums[:, 0] = K * mu + rng.normal(0.0, 1.0, size=REPS) * math.sqrt(K)
    out = {}
    # M = 128
    out[128] = ranks_first(sums / sizes, 0)
    # M = 32: quartile = 4 consecutive leaves
    qs = sums.reshape(REPS, 32, 4).sum(axis=2) / 150.0
    out[32] = ranks_first(qs, 0)
    # M = 8
    us = sums.reshape(REPS, 8, 16).sum(axis=2) / 600.0
    out[8] = ranks_first(us, 0)
    return out


def design_a_rows(mu, tau, rng, agg, batch=500):
    """Nested design with explicit rows (for max and q90 aggregation); rows unit-major, so
    unit g = rows[600g:600g+600], quartile j = 150 consecutive rows, quarters 37/38/37/38."""
    f = (lambda a: a.max(axis=-1)) if agg == "max" else (lambda a: np.quantile(a, 0.9, axis=-1))
    cuts = [(0, 37), (37, 75), (75, 112), (112, 150)]
    res = {8: [], 32: [], 128: []}
    for _ in range(REPS_ROWS // batch):
        u = rng.normal(0.0, tau, size=(batch, 8)) if tau > 0 else np.zeros((batch, 8))
        rows = rng.normal(0.0, 1.0, size=(batch, 4800)) + np.repeat(u, 600, axis=1)
        rows[:, 0:K] = rng.normal(mu, 1.0, size=(batch, K))     # leaf 0 = the plant
        q = rows.reshape(batch, 32, 150)
        leaf_s = np.stack([f(q[:, :, a:b]) for a, b in cuts], axis=2).reshape(batch, 128)
        q_s = f(q)
        u_s = f(rows.reshape(batch, 8, 600))
        for M, s in ((128, leaf_s), (32, q_s), (8, u_s)):
            res[M].append(ranks_first(s, 0))
    return {M: np.concatenate(v) for M, v in res.items()}


def design_b(mu, tau, rng, M):
    """Options only: M cells of 37 rows; cell 0 is the plant. Unit effects: competitors' units random."""
    n = K
    comp_u = rng.normal(0.0, tau, size=(REPS, M - 1)) if tau > 0 else np.zeros((REPS, M - 1))
    comp = comp_u + rng.normal(0.0, 1.0, size=(REPS, M - 1)) / math.sqrt(n)
    plant = mu + rng.normal(0.0, 1.0, size=REPS) / math.sqrt(n)
    scores = np.concatenate([plant[:, None], comp], axis=1)
    return ranks_first(scores, 0)


def design_c(mu, tau, rng, n):
    """Dilution only: 8 cells of n rows; cell 0 = 37 plant + (n - 37) Dolly rows."""
    u = rng.normal(0.0, tau, size=(REPS, 8)) if tau > 0 else np.zeros((REPS, 8))
    comp = u[:, 1:] + rng.normal(0.0, 1.0, size=(REPS, 7)) / math.sqrt(n)
    plant = (K * mu + (n - K) * u[:, 0] + rng.normal(0.0, 1.0, size=REPS) * math.sqrt(n)) / n
    scores = np.concatenate([plant[:, None], comp], axis=1)
    return ranks_first(scores, 0)


def summarise(rank, M):
    k = max(1, M // 8)
    return {"p_top1": round(float((rank == 1).mean()), 3), "k": k,
            "p_topk": round(float((rank <= k).mean()), 3)}


def auc_placement(rng):
    out = {}
    n_d = 4800 - K
    for auc in AUCS:
        mu = mu_of(auc)
        vals = []
        for _ in range(4000):
            p = rng.normal(mu, 1.0, size=K)
            d = rng.normal(0.0, 1.0, size=n_d)
            allv = np.concatenate([p, d])
            order = allv.argsort().argsort() + 1          # ranks 1..N (ties have probability 0)
            r_p = order[:K].sum()
            vals.append((r_p - K * (K + 1) / 2) / (K * n_d))
        vals = np.array(vals)
        out[str(auc)] = {"mean": round(float(vals.mean()), 3),
                         "p05": round(float(np.quantile(vals, 0.05)), 3),
                         "p95": round(float(np.quantile(vals, 0.95)), 3)}
    return out


def main():
    rng = np.random.default_rng(20261017)
    result = {"model": __doc__.splitlines()[0], "reps_mean": REPS, "reps_rows": REPS_ROWS,
              "A_mean": {}, "A_max": {}, "A_q90": {}, "B_mean": {}, "C_mean": {}}
    for tau in (0.0, 0.25):
        for auc in AUCS:
            mu = mu_of(auc)
            key = f"tau={tau},auc={auc}"
            a = design_a_mean(mu, tau, rng)
            result["A_mean"][key] = {M: summarise(a[M], M) for M in (8, 32, 128)}
            result["B_mean"][key] = {M: summarise(design_b(mu, tau, rng, M), M) for M in (8, 32, 128)}
            result["C_mean"][key] = {n: summarise(design_c(mu, tau, rng, n), 8) for n in (600, 150, 37)}
    for auc in AUCS:
        mu = mu_of(auc)
        for agg, slot in (("max", "A_max"), ("q90", "A_q90")):
            r = design_a_rows(mu, 0.0, rng, agg)
            result[slot][f"tau=0.0,auc={auc}"] = {M: summarise(r[M], M) for M in (8, 32, 128)}
    result["auc_placement"] = auc_placement(rng)
    # Bernoulli placement: grid points whose 90% range of the binary top-1 hit contains 0 or 1
    bern = {}
    for tau in (0.0,):
        for M in (8, 32, 128):
            ok1, ok0 = [], []
            for auc in AUCS:
                p = result["A_mean"][f"tau={tau},auc={auc}"][M]["p_top1"]
                if p >= 0.05:
                    ok1.append(auc)
                if p <= 0.95:
                    ok0.append(auc)
            bern[M] = {"hit=1 consistent with AUC": ok1, "hit=0 consistent with AUC": ok0}
    result["bernoulli_placement_tau0"] = bern
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True))
    for slot in ("A_mean", "A_max", "A_q90", "B_mean", "C_mean"):
        print(slot)
        for key, v in result[slot].items():
            print("  ", key, {m: (s["p_top1"], s["p_topk"]) for m, s in v.items()})
    print("auc_placement", result["auc_placement"])
    print("bernoulli_placement_tau0", bern)
    print("signal z = k*mu/sqrt(n) per unit mu:", {n: round(K / math.sqrt(n), 2) for n in (600, 150, 37)})


if __name__ == "__main__":
    main()
