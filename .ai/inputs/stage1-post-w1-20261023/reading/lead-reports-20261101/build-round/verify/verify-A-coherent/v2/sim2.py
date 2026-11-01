"""Verifier 2's coverage simulation of S-G coherent (D-5) beside the primary form (synthetic, seeded; no study data).

    PYTHONPATH=<ws-a> python -B sim2.py --worlds A,B --reps 4000 --workers 8 --reading plan_a --out <new file>

My own x (float form v + (u - v n) / N-bar), cell selection, seed part (from the fit, or the two-arm sum), crossed
prompt part, Satterthwaite df and coverage/tail bookkeeping; B16's REML (reml.fit_cells with the pinned options) and
B16's t functions (tdist) are black boxes. Nothing from scripts.stage1_s1.reading_input is imported.

Model (logit): P(Unsafe) = expit(mu_a + z_ap + s_cluster,j + e_aj), z_ap = eta_p + gamma_ap, eta ~ N(-0.2, 2.5^2) shared
by the arms, gamma ~ N(0, 0.3^2), s ~ N(0, 0.25^2) per cluster and seed, e ~ N(0, sd_e^2). Failure specs per arm (all
other arms fail 5% of answers independently):
  ("label", f_unsafe, f_safe)          a failure probability by the answer's own label;
  ("set", share, hi, lo, per_seed)     hi on a random share of prompts (fixed across seeds, or drawn per seed);
  ("top", share, hi, lo)               hi on the prompts whose z_ap is above the population (1 - share) quantile.
Truths (prompts random): per arm the mean over t ~ N(0, 0.25^2 + sd_e^2) of E[pi] (plain) and of
E[pi (1 - f1)] / E[pi (1 - f1) + (1 - pi)(1 - f0)] (G2's pooled share), by quadrature over (z, t).
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

from scripts.stage1_s1.reading import reml, tdist
from scripts.stage1_s1.reading.settings import design, settings

P, A = 200, 3
MU = {"a0": 0.4, "R": 0.1, "A1": -0.05, "L1": 0.08, "H1": 0.12, "S1": 0.0, "S3": -0.1, "S4": 0.05}
ETA_M, ETA_SD, G_SD, S_SD = -0.2, 2.5, 0.3, 0.25
Z_SD = math.sqrt(ETA_SD ** 2 + G_SD ** 2)
LEVEL, TAIL = 0.90, 0.0075
ALL = ("a0", "R", "A1", "L1", "H1", "S1", "S3", "S4")
WORLDS = {
    "A": ("opposite labels in P5's two arms: S1's Unsafe answers fail 20% (Safe 3%), S3's Safe answers fail 15% "
          "(Unsafe 3%)", 0.15, {"S1": ("label", 0.20, 0.03), "S3": ("label", 0.03, 0.15)}),
    "B": ("S4 fails 95% on a fixed random 12% of prompts (about 16% failing, above the 10% bar)", 0.15,
          {"S4": ("set", 0.12, 0.95, 0.05, False)}),
    "C": ("removal cluster: R fails 95% on its top-5% harmful prompts; A1's Unsafe answers fail 20% (Safe 2%)", 0.15,
          {"R": ("top", 0.05, 0.95, 0.05), "A1": ("label", 0.20, 0.02)}),
    "D": ("low noise (sd_e 0): the comparator a0 fails 95% on a fixed random 8% of prompts", 0.0,
          {"a0": ("set", 0.08, 0.95, 0.05, False)}),
    "E": ("S1 and S4 each fail 95% on a random 8% of prompts drawn anew at each seed", 0.15,
          {"S1": ("set", 0.08, 0.95, 0.05, True), "S4": ("set", 0.08, 0.95, 0.05, True)}),
    "F": ("every arm fails 95% on its own top-4% harmful prompts", 0.15, {a: ("top", 0.04, 0.95, 0.04) for a in ALL}),
    "G": ("heavy, outcome-linked: S1's Unsafe answers fail 40% (Safe 5%; about 22% failing); H1's Safe answers fail "
          "25%", 0.15, {"S1": ("label", 0.40, 0.05), "H1": ("label", 0.03, 0.25)}),
    "H": ("low noise (sd_e 0), outcome-linked by prompt in the repair: S3 fails 95% on its top-6% prompts, L1 on its "
          "top-6%", 0.0, {"S3": ("top", 0.06, 0.95, 0.05), "L1": ("top", 0.06, 0.95, 0.05)}),
    "I": ("independent: every answer of every arm fails 8%", 0.15, {a: ("label", 0.08, 0.08) for a in ALL}),
}


def expit(z):
    return 1.0 / (1.0 + np.exp(-z))


def spec_of(world, arm):
    return WORLDS[world][2].get(arm, ("label", 0.05, 0.05))


def truths(world: str, arms) -> tuple[dict, dict]:
    sd_e = WORLDS[world][1]
    t_sd = math.sqrt(S_SD ** 2 + sd_e ** 2)
    gx, gw = np.polynomial.hermite_e.hermegauss(60)
    gw = gw / gw.sum()
    plain, coh = {}, {}
    for arm in arms:
        spec = spec_of(world, arm)
        if spec[0] == "top":
            cut = NormalDist(ETA_M, Z_SD).inv_cdf(1.0 - spec[1])
            pieces = [(np.linspace(ETA_M - 9 * Z_SD, cut, 6001), spec[3]), (np.linspace(cut, ETA_M + 9 * Z_SD, 6001), spec[2])]
        else:
            pieces = [(np.linspace(ETA_M - 9 * Z_SD, ETA_M + 9 * Z_SD, 12001), None)]
        pv, cv = [], []
        for t in gx * t_sd:
            e_pi = s1 = s0 = 0.0
            for z, f_top in pieces:
                w = np.full(len(z), z[1] - z[0])
                w[0] = w[-1] = (z[1] - z[0]) / 2
                dens = w * np.exp(-0.5 * ((z - ETA_M) / Z_SD) ** 2) / (Z_SD * math.sqrt(2 * math.pi))
                pi = expit(MU[arm] + z + t)
                e_pi += float(dens @ pi)
                if spec[0] == "top":
                    f1 = f0 = f_top
                    s1 += float(dens @ (pi * (1 - f1)))
                    s0 += float(dens @ ((1 - pi) * (1 - f0)))
                elif spec[0] == "set":
                    share, hi, lo = spec[1], spec[2], spec[3]
                    keep = share * (1 - hi) + (1 - share) * (1 - lo)
                    s1 += float(dens @ pi) * keep
                    s0 += float(dens @ (1 - pi)) * keep
                else:
                    s1 += float(dens @ (pi * (1 - spec[1])))
                    s0 += float(dens @ ((1 - pi) * (1 - spec[2])))
            pv.append(e_pi)
            cv.append(s1 / (s1 + s0))
        plain[arm], coh[arm] = float(gw @ np.array(pv)), float(gw @ np.array(cv))
    return plain, coh


def draw(rng, world, dsg):
    sd_e = WORLDS[world][1]
    seeds = sorted({j for a in dsg.arms for j in dsg.seeds[a]})
    eta = rng.normal(ETA_M, ETA_SD, P)
    shift = {cl: {j: rng.normal(0, S_SD) for j in seeds} for cl in ("full", "removal")}
    coh, plain = {}, {}
    for arm in dsg.fit_arms:
        z = eta + rng.normal(0, G_SD, P)
        spec = spec_of(world, arm)
        fixed = rng.random(P) < (spec[1] if spec[0] == "set" else 0.0)
        for j in dsg.seeds[arm]:
            pi = expit(MU[arm] + z + shift[dsg.cluster[arm]][j] + (rng.normal(0, sd_e) if sd_e > 0 else 0.0))
            unsafe = rng.random((P, A)) < pi[:, None]
            if spec[0] == "label":
                f1, f0 = np.full(P, spec[1]), np.full(P, spec[2])
            elif spec[0] == "set":
                marked = (rng.random(P) < spec[1]) if spec[4] else fixed
                f1 = f0 = np.where(marked, spec[2], spec[3])
            else:
                cut = NormalDist(ETA_M, Z_SD).inv_cdf(1.0 - spec[1])
                f1 = f0 = np.where(z >= cut, spec[2], spec[3])
            fails = rng.random((P, A)) < np.where(unsafe, f1[:, None], f0[:, None])
            coh[(arm, j)] = ((~fails).sum(axis=1), (unsafe & ~fails).sum(axis=1))
            plain[(arm, j)] = (np.full(P, A), unsafe.sum(axis=1))
    return coh, plain


def x_float(n, u):
    big_n = int(n.sum())
    if big_n == 0:
        return None
    v = int(u.sum()) / big_n
    return v + (u - v * n) / (big_n / len(n))


def item_part(d):
    j, p = d.shape
    grand, rows, cols = d.mean(), d.mean(axis=1), d.mean(axis=0)
    ms_p = j * float(((cols - grand) ** 2).sum()) / (p - 1)
    ms_e = float(((d - rows[:, None] - cols[None, :] + grand) ** 2).sum()) / ((p - 1) * (j - 1))
    k = 1e4 / (p * j)
    v = max(0.0, ms_p - ms_e) * k
    q = (ms_p * k) ** 2 / (p - 1) + (ms_e * k) ** 2 / ((p - 1) * (j - 1)) if ms_p > ms_e else 0.0
    return v, q


def read(counts, dsg, cfg, opts, floor):
    table = {}
    for key, (n, u) in counts.items():
        x = x_float(n, u)
        if x is not None:
            table[key] = x
    fits = {}
    for cl in ("full", "removal"):
        members = [a for a in dsg.fit_arms if dsg.cluster[a] == cl and any((a, j) in table for j in dsg.seeds[a])]
        if len(members) >= 2:
            cells = [(a, j, float(100.0 * table[(a, j)].mean())) for a in members for j in dsg.seeds[a] if (a, j) in table]
            try:
                fits[cl] = reml.fit_cells(cells, tuple(members), floor, **opts)
            except ValueError:
                pass
    out = {}
    for name, c, m in dsg.contrasts:
        common = sorted(set(dsg.seeds[c]) & set(dsg.seeds[m]))
        have = [j for j in common if (c, j) in table and (m, j) in table]
        if len(have) < 2:
            out[name] = None
            continue
        diffs = np.array([100.0 * (table[(c, j)].mean() - table[(m, j)].mean()) for j in have])
        jj = len(have)
        if len(have) < len(common):
            v_seed, df_seed = float(diffs.var(ddof=1)) / jj, jj - 1.0
        else:
            fit = fits.get(dsg.cluster[c])
            if fit is None:
                out[name] = None
                continue
            if fit.two_arm:
                v_seed, df_seed = max(float(diffs.var(ddof=1)), floor) / jj, float(jj - 1)
            else:
                i, k = fit.arms.index(c), fit.arms.index(m)
                v_seed = (fit.sigma2[c] + fit.sigma2[m]) / jj
                var_v = (fit.info_inv[i, i] + fit.info_inv[k, k] + 2 * fit.info_inv[i, k]) / jj ** 2
                df_seed = 2 * v_seed ** 2 / var_v if var_v > 0 else math.inf
        d = np.stack([table[(c, j)] - table[(m, j)] for j in have])
        v_item, q = item_part(d)
        v = v_seed + v_item
        denom = (v_seed ** 2 / df_seed if math.isfinite(df_seed) else 0.0) + q
        df = v * v / denom if denom > 0 else math.inf
        out[name] = (float(diffs.mean()), math.sqrt(v), df) if (v > 0 and math.isfinite(df)) else None
    return out


def task(args):
    world, reading, seed, start, count = args
    dsg, cfg = design(reading), settings()
    opts, floor = reml.options(cfg), float(cfg["endpoints"]["U"]["floor"])
    rows = []
    for r in range(start, start + count):
        rng = np.random.default_rng([seed, ord(world[0]), r])
        coh, plain = draw(rng, world, dsg)
        rows.append({"coherent": read(coh, dsg, cfg, opts, floor), "primary": read(plain, dsg, cfg, opts, floor),
                     "failing": {a: float(np.mean([1 - coh[(a, j)][0].sum() / (P * A) for j in dsg.seeds[a]]))
                                 for a in dsg.fit_arms}})
    return rows


def summarize(world, reading, rows):
    dsg = design(reading)
    plain_t, coh_t = truths(world, dsg.fit_arms)
    out = {"world": world, "what": WORLDS[world][0], "reps": len(rows),
           "mean_failing_share": {a: float(np.mean([r["failing"][a] for r in rows])) for a in dsg.fit_arms},
           "contrasts": {}}
    for name, c, m in dsg.contrasts:
        rec = {}
        for form, truth in (("coherent", coh_t), ("primary", plain_t)):
            target = 100.0 * (truth[c] - truth[m])
            got = [r[form][name] for r in rows if r[form][name] is not None]
            cover = tail = 0
            ests, ses = [], []
            for est, se, df in got:
                half = tdist.t_quantile(0.5 + LEVEL / 2, df) * se
                cover += est - half <= target <= est + half
                tail += tdist.t_two_sided((est - target) / se, df) < TAIL
                ests.append(est)
                ses.append(se)
            k = len(got)
            cov = cover / k
            rec[form] = {"truth_pp": target, "n": k, "coverage": cov, "mc_se": math.sqrt(cov * (1 - cov) / k),
                         "tail": tail / k, "tail_events": tail, "bias_pp": float(np.mean(ests)) - target,
                         "sd_over_se": float(np.std(ests, ddof=1)) / float(np.mean(ses))}
        ratio = rec["coherent"]["tail"] / rec["primary"]["tail"] if rec["primary"]["tail"] > 0 else None
        rec["tail_ratio"] = ratio
        rec["meets"] = bool(0.88 <= rec["coherent"]["coverage"] <= 0.92 and ratio is not None and ratio <= 1.5)
        out["contrasts"][name] = rec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", default=",".join(WORLDS))
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--reading", default="plan_a")
    ap.add_argument("--seed", type=int, default=31101)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        print("the output exists", file=sys.stderr)
        return 2
    res = {}
    for world in args.worlds.split(","):
        t0 = time.time()
        chunks = [(world, args.reading, args.seed, s, min(50, args.reps - s)) for s in range(0, args.reps, 50)]
        if args.workers > 1:
            import multiprocessing as mpr
            with mpr.get_context("spawn").Pool(args.workers) as pool:
                parts = pool.map(task, chunks)
        else:
            parts = [task(c) for c in chunks]
        res[world] = summarize(world, args.reading, [r for p in parts for r in p])
        res[world]["seconds"] = round(time.time() - t0, 1)
        for name, rec in res[world]["contrasts"].items():
            c, p = rec["coherent"], rec["primary"]
            print(f"{world} {name}: coh cov {c['coverage']:.4f} tail {c['tail']:.4f} ({c['tail_events']}) | prim cov "
                  f"{p['coverage']:.4f} tail {p['tail']:.4f} ({p['tail_events']}) | ratio "
                  f"{rec['tail_ratio'] if rec['tail_ratio'] is None else round(rec['tail_ratio'], 2)} | truth coh "
                  f"{c['truth_pp']:+.2f} plain {p['truth_pp']:+.2f} | bias {c['bias_pp']:+.3f} | sd/se "
                  f"{c['sd_over_se']:.3f} | n {c['n']} | {'met' if rec['meets'] else 'NOT met'}", flush=True)
        print(f"{world}: {res[world]['reps']} reps, {res[world]['seconds']} s; failing {json.dumps({a: round(v, 3) for a, v in res[world]['mean_failing_share'].items()})}", flush=True)
    with open(args.out, "x") as h:
        json.dump({"reading": args.reading, "reps": args.reps, "seed": args.seed, "worlds": res}, h, indent=1,
                  sort_keys=True)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
