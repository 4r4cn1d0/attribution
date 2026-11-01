"""Coverage of S-G coherent's 90% interval and its tail at U_k's start level (0.75%), beside the primary form's, on
synthetic worlds (seeded; no study data; post-W1 deviation D-5's calibration check, the lead's ruling 7).

    python -B scripts/stage1_s1/reading_input/tests/sim_sg_coherent.py --reps 10000 --workers 8 --out <new file>
        [--reading plan_a|plan_a_block_a_only|plan_b] [--worlds i,ii,ii-low,iii-prompt,iii-answer,iii-refusal]
        [--seed 20261101]

Each replicate draws the cells of the reading's full-corpus cluster (a0, S1, S3, S4 at the design's seeds under plan
A and block A only; S1, S4 under plan B, the two-arm sum rule), 200 prompts x 3 answers per cell, and reads every
contrast of that cluster twice with the reader's own code (sg_coherent.x_shares, cluster_fits and estimate: B16's
REML with the pinned settings, D-4's multi-start, its prompt part and Satterthwaite df): on the coherent counts (S-G
coherent) and on the plain counts (n = 3, u = every Unsafe answer; x is then the U share to the last bit, so this is
B16's primary U_k form). A replicate's interval covers when it holds the true value; its tail event is a two-sided
p-value below 0.75% for the test of the true value.

World (logit scale): logit P(Unsafe) = mu_a + eta_p + gamma_ap + s_j + e_aj, eta_p ~ N(-0.2, 2.5^2) shared by the
arms, gamma_ap ~ N(0, 0.3^2), s_j ~ N(0, 0.25^2) shared by the cluster, e_aj ~ N(0, sd_e^2); mu = a0 +0.4, S1 0,
S3 -0.1, S4 +0.05. Each answer fails the screen with a probability by world (S1 is the arm that fails; it is the
repair in P4 and the comparator in P5 and P6):
- i            independent failures: 7% of every answer in every arm (sd_e 0.15);
- ii           failures on some prompts: S1 fails 95% of the answers of a random 8% of the prompts (drawn per
               replicate, unrelated to harm), 5% elsewhere and in every other arm (sd_e 0.15);
- ii-low       ii with sd_e 0 (the review's worst case for the design's drop rule);
- iii-prompt   failures linked to the outcome by prompt: S1 fails 95% on its most harmful prompts (eta above its
               96th percentile; looping or capped compliance), 5% elsewhere and in every other arm;
- iii-answer   linked by answer: S1's Unsafe answers fail 25%, its Safe answers 3% (compliance capped); others 5%;
- iii-refusal  linked by answer the other way: S1's Safe answers fail 15% (terse refusals fail the short-answer
               screen), its Unsafe answers 3%; others 5%.
The true values are the population quantities the estimators target with prompts random: per arm the mean over
t ~ N(0, 0.25^2 + sd_e^2) of E[P(Unsafe)] (plain) or E[P(Unsafe) (1 - f1)] / E[P(Unsafe) (1 - f1) + (1 - P(Unsafe))
(1 - f0)] (coherent-only: G2's pooled share), by quadrature (Gauss-Hermite over gamma and t; a trapezoid grid over
eta with the 96th percentile as a node). Under i and ii the coherent truth equals the plain one.

Printed and written (canonical JSON, exclusive create): per world and contrast the coverage of both forms with its
Monte Carlo SE, the tail rates, their ratio, the mean bias, the empirical SD against the mean reported SE, and the
contrasts not computable; and whether S-G coherent meets the lead's target (coverage 0.88-0.92, tail at most 1.5 x
the primary form's in the same world). A small run is noisy at the tail (0.75% of 2,000 is 15 events); the lead's
run uses 10,000 or more replicates per world.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from statistics import NormalDist

import numpy as np

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.stage1_s1.reading import tdist  # noqa: E402
from scripts.stage1_s1.reading.contrast import Estimate  # noqa: E402
from scripts.stage1_s1.reading.settings import design, settings  # noqa: E402
from scripts.stage1_s1.reading_input import sg_coherent as sgc  # noqa: E402

ITEMS, ANSWERS = 200, 3
MU = {"a0": 0.4, "S1": 0.0, "S3": -0.1, "S4": 0.05}
ETA_MEAN, ETA_SD, GAMMA_SD, SHIFT_SD = -0.2, 2.5, 0.3, 0.25
FAILING_ARM = "S1"
TOP_SHARE = 0.04                                          # iii-prompt: the top 4% of prompts by harm
SET_SHARE = 0.08                                          # ii: a random 8% of prompts
WORLDS = {"i": ("independent", 0.15), "ii": ("concentrated", 0.15), "ii-low": ("concentrated", 0.0),
          "iii-prompt": ("prompt-linked", 0.15), "iii-answer": ("answer-linked", 0.15),
          "iii-refusal": ("refusal-linked", 0.15)}
LEVEL, TAIL = 0.90, 0.0075
TARGET = {"coverage": (0.88, 0.92), "tail_ratio_at_most": 1.5}


def fail_probs(kind: str, arm: str, top: np.ndarray, marked: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(P(fail | Unsafe), P(fail | Safe)) per prompt of one arm in a world (module doc)."""
    base = np.full(top.shape, 0.07 if kind == "independent" else 0.05)
    if arm != FAILING_ARM or kind == "independent":
        return base, base
    if kind == "concentrated":
        f = np.where(marked, 0.95, 0.05)
        return f, f
    if kind == "prompt-linked":
        f = np.where(top, 0.95, 0.05)
        return f, f
    if kind == "answer-linked":
        return np.full(top.shape, 0.25), np.full(top.shape, 0.03)
    if kind == "refusal-linked":
        return np.full(top.shape, 0.03), np.full(top.shape, 0.15)
    raise ValueError(kind)


def _expit(z):
    return 1.0 / (1.0 + np.exp(-z))


def truths(kind: str, sd_e: float, arms) -> tuple[dict, dict]:
    """({arm: plain truth}, {arm: coherent truth}) as shares (module doc), by quadrature."""
    zstar = NormalDist().inv_cdf(1.0 - TOP_SHARE)
    left, right = np.linspace(-8.0, zstar, 4001), np.linspace(zstar, 8.0, 4001)

    def trap(g):
        w = np.full(len(g), g[1] - g[0])
        w[0] = w[-1] = (g[1] - g[0]) / 2.0
        return w
    z = np.concatenate([left, right])
    wz = np.concatenate([trap(left), trap(right)]) * np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    wz = wz / wz.sum()
    eta = ETA_MEAN + ETA_SD * z
    top = np.concatenate([np.zeros(len(left), bool), np.ones(len(right), bool)])   # each piece takes its own limit
    gx, gw = np.polynomial.hermite_e.hermegauss(48)
    gw = gw / gw.sum()
    t_sd = math.sqrt(SHIFT_SD ** 2 + sd_e ** 2)
    plain, coherent = {}, {}
    for arm in arms:
        marks = ((False, 1.0 - SET_SHARE), (True, SET_SHARE)) if kind == "concentrated" else ((False, 1.0),)
        p_vals, c_vals = [], []
        with np.errstate(all="ignore"):                      # this Mac's numpy prints spurious matmul warnings
            for t in gx * t_sd:
                pi = _expit(MU[arm] + eta[None, :] + GAMMA_SD * gx[:, None] + t)          # gamma x eta
                mean_pi = float(gw @ pi @ wz)
                s1 = s0 = 0.0
                for mark, pm in marks:
                    f1, f0 = fail_probs(kind, arm, top, np.full(top.shape, mark))
                    s1 += pm * float(gw @ (pi * (1.0 - f1)[None, :]) @ wz)
                    s0 += pm * float(gw @ ((1.0 - pi) * (1.0 - f0)[None, :]) @ wz)
                p_vals.append(mean_pi)
                c_vals.append(s1 / (s1 + s0))
            plain[arm], coherent[arm] = float(gw @ np.array(p_vals)), float(gw @ np.array(c_vals))
        if not (0.0 < plain[arm] < 1.0 and 0.0 < coherent[arm] < 1.0):
            raise ValueError(f"the quadrature of {arm} is not a share")
    return plain, coherent


def draw(rng, kind: str, sd_e: float, dsg, arms, zstar: float) -> tuple[dict, dict]:
    """One replicate's (coherent, plain) counts {(arm, seed): (n, u)} of the cluster's arms (module doc)."""
    seeds = sorted({j for a in arms for j in dsg.seeds[a]})
    eta = rng.normal(ETA_MEAN, ETA_SD, ITEMS)
    top = eta > ETA_MEAN + ETA_SD * zstar
    marked = rng.random(ITEMS) < SET_SHARE
    shift = {j: rng.normal(0.0, SHIFT_SD) for j in seeds}
    coherent, plain = {}, {}
    for arm in arms:
        gamma = rng.normal(0.0, GAMMA_SD, ITEMS)
        f1, f0 = fail_probs(kind, arm, top, marked)
        for j in dsg.seeds[arm]:
            pi = _expit(MU[arm] + eta + gamma + shift[j] + (rng.normal(0.0, sd_e) if sd_e > 0 else 0.0))
            unsafe = rng.random((ITEMS, ANSWERS)) < pi[:, None]
            fails = rng.random((ITEMS, ANSWERS)) < np.where(unsafe, f1[:, None], f0[:, None])
            n = (~fails).sum(axis=1)
            u = (unsafe & ~fails).sum(axis=1)
            coherent[(arm, j)] = (n, u)
            plain[(arm, j)] = (np.full(ITEMS, ANSWERS), unsafe.sum(axis=1))
    return coherent, plain


def read_cluster(counts: dict, dsg, contrasts, cfg) -> dict:
    """{contrast: Estimate or reason} by the reader's own code on one cluster's counts."""
    table = {}
    for key, (n, u) in counts.items():
        x = sgc.x_shares(n, u)
        if x is not None:
            table[key] = x
    cluster = dsg.cluster[contrasts[0][1]]
    scale, floor = float(cfg["endpoints"]["U"]["scale"]), float(cfg["endpoints"]["U"]["floor"])
    fits, reasons = sgc.cluster_fits(table, dsg, scale, floor, cfg, clusters=(cluster,))
    return {name: sgc.estimate(table, fits, reasons, dsg, name, c, m, scale, "S-G coherent") for name, c, m in contrasts}


def _task(args) -> list:
    world, reading, base_seed, start, count = args
    kind, sd_e = WORLDS[world]
    dsg, cfg = design(reading), settings()
    arms = dsg.cluster_arms("full")
    contrasts = [(n, c, m) for n, c, m in dsg.contrasts if dsg.cluster[c] == "full"]
    zstar = NormalDist().inv_cdf(1.0 - TOP_SHARE)
    out = []
    for rep in range(start, start + count):
        rng = np.random.default_rng([base_seed, list(WORLDS).index(world), rep])
        coherent, plain = draw(rng, kind, sd_e, dsg, arms, zstar)
        row = {}
        for form, counts in (("coherent", coherent), ("primary", plain)):
            for name, e in read_cluster(counts, dsg, contrasts, cfg).items():
                row[(form, name)] = (e.est, e.se, e.df) if isinstance(e, Estimate) else None
        failing = [float(1.0 - coherent[(FAILING_ARM, j)][0].sum() / (ITEMS * ANSWERS)) for j in dsg.seeds[FAILING_ARM]]
        out.append((row, float(np.mean(failing))))
    return out


def summarize(world: str, reading: str, rows: list, seconds: float) -> dict:
    kind, sd_e = WORLDS[world]
    dsg = design(reading)
    arms = dsg.cluster_arms("full")
    contrasts = [(n, c, m) for n, c, m in dsg.contrasts if dsg.cluster[c] == "full"]
    plain_t, coh_t = truths(kind, sd_e, arms)
    out = {"world": world, "failures": kind, "arm_seed_sd": sd_e, "reps": len(rows), "seconds": round(seconds, 1),
           "failing_arm": FAILING_ARM, "failing_arm_mean_failing_share": float(np.mean([f for _, f in rows])),
           "contrasts": {}}
    for name, c, m in contrasts:
        rec = {}
        for form, truth in (("coherent", coh_t), ("primary", plain_t)):
            target = 100.0 * (truth[c] - truth[m])
            got = [r[(form, name)] for r, _ in rows if r[(form, name)] is not None]
            cover = tail = 0
            ests, ses = [], []
            for est, se, df in got:
                half = tdist.t_quantile(0.5 + LEVEL / 2.0, df) * se
                cover += est - half <= target <= est + half
                tail += (tdist.t_two_sided((est - target) / se, df) if se > 0 else 0.0) < TAIL
                ests.append(est)
                ses.append(se)
            k = len(got)
            cov = cover / k if k else float("nan")
            rec[form] = {"truth_pp": target, "computable": k, "not_computable": len(rows) - k, "coverage_90": cov,
                         "coverage_mc_se": math.sqrt(cov * (1.0 - cov) / k) if k else float("nan"),
                         "tail_rate": tail / k if k else float("nan"),
                         "mean_bias_pp": float(np.mean(ests)) - target if k else float("nan"),
                         "empirical_sd_pp": float(np.std(ests, ddof=1)) if k > 1 else float("nan"),
                         "mean_reported_se_pp": float(np.mean(ses)) if k else float("nan")}
        ratio = rec["coherent"]["tail_rate"] / rec["primary"]["tail_rate"] if rec["primary"]["tail_rate"] > 0 else None
        lo, hi = TARGET["coverage"]
        rec["tail_ratio"] = ratio
        rec["meets_target"] = bool(lo <= rec["coherent"]["coverage_90"] <= hi and ratio is not None
                                   and ratio <= TARGET["tail_ratio_at_most"])
        out["contrasts"][name] = rec
    return out


def simulate(worlds, reps: int, seed: int, reading: str = "plan_a", workers: int = 1, chunk: int = 50) -> dict:
    """{world: summary} (module doc); replicate r of a world always draws from the seed [seed, world, r], so the
    result does not depend on the number of workers."""
    out = {}
    for world in worlds:
        tasks = [(world, reading, seed, start, min(chunk, reps - start)) for start in range(0, reps, chunk)]
        t0 = time.monotonic()
        if workers > 1:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(workers) as pool:
                parts = pool.map(_task, tasks)
        else:
            parts = [_task(t) for t in tasks]
        out[world] = summarize(world, reading, [r for part in parts for r in part], time.monotonic() - t0)
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--reps", type=int, default=2000)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--reading", default="plan_a", choices=("plan_a", "plan_a_block_a_only", "plan_b"))
    p.add_argument("--worlds", default=",".join(WORLDS))
    p.add_argument("--seed", type=int, default=20261101)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)
    worlds = args.worlds.split(",")
    if any(w not in WORLDS for w in worlds) or args.reps < 2 or args.out.exists():
        print("REFUSED: unknown world, fewer than 2 replicates, or the output file exists", file=sys.stderr)
        return 2
    result = simulate(worlds, args.reps, args.seed, args.reading, args.workers)
    doc = {"kind": "stage1 S-G coherent coverage simulation", "version": 1, "reading": args.reading,
           "reps_per_world": args.reps, "seed": args.seed, "level": LEVEL, "tail_level": TAIL, "target": TARGET,
           "model": {"mu": MU, "eta": [ETA_MEAN, ETA_SD], "gamma_sd": GAMMA_SD, "shift_sd": SHIFT_SD,
                     "items": ITEMS, "answers": ANSWERS, "failing_arm": FAILING_ARM},
           "worlds": result}
    with open(args.out, "x") as handle:
        handle.write(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    for world, w in result.items():
        for name, rec in w["contrasts"].items():
            c, pr = rec["coherent"], rec["primary"]
            print(f"{world:<12} {name}: S-G coherent coverage {c['coverage_90']:.3f} (MC SE {c['coverage_mc_se']:.3f}), "
                  f"tail {c['tail_rate']:.4f}; primary {pr['coverage_90']:.3f}, tail {pr['tail_rate']:.4f}; "
                  f"ratio {rec['tail_ratio'] if rec['tail_ratio'] is None else round(rec['tail_ratio'], 2)}; "
                  f"truth {c['truth_pp']:+.2f} pp (plain {pr['truth_pp']:+.2f}); bias {c['mean_bias_pp']:+.3f}; "
                  f"SD {c['empirical_sd_pp']:.3f} vs SE {c['mean_reported_se_pp']:.3f}; not computable "
                  f"{c['not_computable']}; target {'met' if rec['meets_target'] else 'NOT met'}")
        print(f"{world:<12} {w['reps']} replicates, {w['seconds']} s; failing arm's mean failing share "
              f"{w['failing_arm_mean_failing_share']:.3f}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
