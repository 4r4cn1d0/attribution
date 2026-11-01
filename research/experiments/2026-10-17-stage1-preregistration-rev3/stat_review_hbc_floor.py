#!/usr/bin/env python3
"""stat_review_hbc_floor.py: add-on to stat_review_hbc.py (same model, same read-only reuse of the AMD planning code).

Under design D1 and HB-C, at the seed level:
 1. how often one or both arms of a contrast sit at the REML floor (0.01 pp^2), and the rejection rate of that
    contrast's two-sided test at 5% and 0.75% conditional on it (null true everywhere);
 2. P(equivalent | true 0) for grade 1 (90% interval inside +-5 pp) and grade 2 (98.33% interval inside +-5 pp),
    P1 and P4, at pair SD 1.84 / 3.32 / 3.75 / 4.5 pp, beside the per-contrast paired t (5 df).
Run: <venv python> -I -B stat_review_hbc_floor.py [--reps N]
"""
import argparse, importlib.util, json, math, pathlib, sys
import numpy as np
import warnings
warnings.filterwarnings("ignore")
sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("srh", HERE / "stat_review_hbc.py")
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)
S1M, W, ARMS = H.S1M, H.W, H.ARMS
OUT, RES = [], {}


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20000)
    a = ap.parse_args()
    d = S1M.D1
    dc = H.ClusterDesign(d)
    for nm, v, rho in (("pair SD 1.84", 2.65 ** 2, 0.76), ("pair SD 3.32", 2.65 ** 2, 1 - 3.32 ** 2 / (2 * 2.65 ** 2)),
                       ("pair SD 3.75", 2.65 ** 2, 0.0), ("pair SD 4.5", (4.5 / math.sqrt(2)) ** 2, 0.0)):
        rng = np.random.default_rng(777 + int(100 * rho) + int(v))
        E, S, D, TH, PE, PS = [], [], [], [], [], []
        done = 0
        while done < a.reps:
            B = min(500, a.reps - done)
            U = H.draw(rng, d, B, v, rho)
            est, se, df, th, vth, fl = H.hbc_fit(dc, U)
            pe, ps, pdf = H.paired_own(dc, U)
            E.append(est); S.append(se); D.append(df); TH.append(th); PE.append(pe); PS.append(ps)
            done += B
        est, se, df, th, pe, ps = (np.concatenate(x, 0) for x in (E, S, D, TH, PE, PS))
        p = W.t_p2(est / se, df)
        rec = {}
        for ci, c in enumerate(d.con):
            fa = th[:, c["a"]] <= H.FLOOR * 1.0001
            fb = th[:, c["b"]] <= H.FLOOR * 1.0001
            one = fa ^ fb
            both = fa & fb
            none = ~(fa | fb)
            r = dict(p_one=float(one.mean()), p_both=float(both.mean()),
                     rej5_one=float((p[one] <= 0.05).mean()) if one.any() else None,
                     rej075_one=float((p[one] <= 0.0075).mean()) if one.any() else None,
                     rej5_both=float((p[both] <= 0.05).mean()) if both.any() else None,
                     rej5_none=float((p[none] <= 0.05).mean()), rej075_none=float((p[none] <= 0.0075).mean()))
            rec[c["name"]] = r
        worst = max(rec.values(), key=lambda r: r["rej5_one"] or 0)
        say(f"[{nm}] per contrast: P(one arm at floor) {np.mean([r['p_one'] for r in rec.values()]) * 100:.1f}%, "
            f"P(both) {np.mean([r['p_both'] for r in rec.values()]) * 100:.2f}%; rejection given one at floor: 5% -> "
            f"{np.mean([r['rej5_one'] for r in rec.values()]) * 100:.2f}% (worst {worst['rej5_one'] * 100:.2f}%), 0.75% -> "
            f"{np.mean([r['rej075_one'] for r in rec.values()]) * 100:.3f}%; given none: 5% -> "
            f"{np.mean([r['rej5_none'] for r in rec.values()]) * 100:.2f}%, 0.75% -> {np.mean([r['rej075_none'] for r in rec.values()]) * 100:.3f}%"
            + (f"; given both: 5% -> {np.nanmean([r['rej5_both'] if r['rej5_both'] is not None else np.nan for r in rec.values()]) * 100:.1f}%"
               if any(r['rej5_both'] is not None for r in rec.values()) else ""))
        eq = {}
        for ci, cn in ((0, "P1"), (3, "P4")):
            # vectorized quantiles via a lookup on rounded df
            dfr = np.clip(np.round(df[:, ci] * 4) / 4, 1.0, 200.0)
            uniq = np.unique(dfr)
            q95 = {u: W.t_ppf(0.95, u) for u in uniq}
            q99 = {u: W.t_ppf(1 - 0.05 / 6, u) for u in uniq}
            hw1 = np.array([q95[u] for u in dfr]) * se[:, ci]
            hw2 = np.array([q99[u] for u in dfr]) * se[:, ci]
            g1 = (np.abs(est[:, ci]) + hw1 < 5).mean()
            g2 = (np.abs(est[:, ci]) + hw2 < 5).mean()
            pg1 = (np.abs(pe[:, ci]) + W.t_ppf(0.95, 5) * ps[:, ci] < 5).mean()
            pg2 = (np.abs(pe[:, ci]) + W.t_ppf(1 - 0.05 / 6, 5) * ps[:, ci] < 5).mean()
            eq[cn] = dict(g1=float(g1), g2=float(g2), paired_g1=float(pg1), paired_g2=float(pg2))
        say(f"      P(equivalent | 0): P1 grade 1 {eq['P1']['g1']:.2f}, grade 2 {eq['P1']['g2']:.2f}; P4 grade 1 {eq['P4']['g1']:.2f}, "
            f"grade 2 {eq['P4']['g2']:.2f} | paired t: P1 {eq['P1']['paired_g1']:.2f} / {eq['P1']['paired_g2']:.2f}")
        RES[nm] = dict(floor=rec, equivalence=eq)
    (HERE / "stat_review_hbc_floor_out.txt").write_text("\n".join(OUT) + "\n")
    (HERE / "stat_review_hbc_floor_results.json").write_text(json.dumps(RES, indent=1, default=float))


if __name__ == "__main__":
    main()
