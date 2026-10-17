#!/usr/bin/env python3
"""verify_floorfix.py: candidate fixes for HB's REML floor events (seed part only, cell-level normal data, D0).

HB      : the draft's rule (REML per-arm variances, floor 0.01 pp^2, Satterthwaite df from the REML information).
HB-max  : per-arm variance = max(REML value, the arm's own leverage-adjusted residual mean square from the
          equal-weight seed-blocked OLS fit); df as HB but each arm's df capped at its OLS residual df h_a.
HB-mod  : per-arm variance moderated toward the pooled blocked residual variance with d0 = 4 prior df
          ((h_a s2_a + d0 s2_pool) / (h_a + d0), s2_a the arm's OLS residual mean square); df per arm h_a + d0,
          combined by Welch-Satterthwaite.
(b0)    : the contrast's own paired differences, J - 1 df (exact under normality, any variance structure).
Planning simulation only; reads no evaluation record. Writes verify_floorfix_out.txt and verify_floorfix_results.json.
"""
import importlib.util, json, math, pathlib, time
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s1m", HERE / "rerun" / "stage1_model_sim.py")
S1M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S1M)
W = S1M.W
ARMS = S1M.ARMS
OUT, RES = [], {}
GRID = np.round(np.arange(0.0, 25.01, 0.25), 2)


def say(s):
    print(s, flush=True)
    OUT.append(s)


def methods(d, U):
    th, vth = S1M.reml_hetero(d, U)
    beta = U @ d.pinvT
    resid = U - beta @ d.X.T
    s2_arm = (resid ** 2) @ d.Z / d.h_arm[None, :]
    s2_pool = (resid ** 2).sum(1) / d.df_b2
    h = d.h_arm
    floor = th <= 1.0001e-2
    B = U.shape[0]
    out = {m: [np.zeros((B, 6)), np.zeros((B, 6)), np.zeros((B, 6))] for m in ("HB", "HB-max", "HB-mod", "b0")}
    flag = np.zeros((B, 6), bool)
    d0 = 4.0
    s2_mod = (h[None, :] * s2_arm + d0 * s2_pool[:, None]) / (h[None, :] + d0)
    for ci, c in enumerate(d.con):
        a, b, J = c["a"], c["b"], c["J"]
        dd = U[:, c["ia"]] - U[:, c["ib"]]
        est = dd.mean(1)
        flag[:, ci] = floor[:, a] | floor[:, b]
        vs = (th[:, a] + th[:, b]) / J
        var_vs = (vth[:, a, a] + vth[:, b, b] + 2 * vth[:, a, b]) / J ** 2
        out["HB"][0][:, ci], out["HB"][1][:, ci] = est, np.sqrt(vs)
        out["HB"][2][:, ci] = 2 * vs ** 2 / np.maximum(var_vs, 1e-300)
        ta, tb = np.maximum(th[:, a], s2_arm[:, a]), np.maximum(th[:, b], s2_arm[:, b])
        vm = (ta + tb) / J
        dfm = vm ** 2 / ((ta / J) ** 2 / h[a] + (tb / J) ** 2 / h[b])
        out["HB-max"][0][:, ci], out["HB-max"][1][:, ci], out["HB-max"][2][:, ci] = est, np.sqrt(vm), np.minimum(dfm, out["HB"][2][:, ci] + 1e9)
        ma, mb = s2_mod[:, a], s2_mod[:, b]
        vmod = (ma + mb) / J
        out["HB-mod"][0][:, ci], out["HB-mod"][1][:, ci] = est, np.sqrt(vmod)
        out["HB-mod"][2][:, ci] = vmod ** 2 / ((ma / J) ** 2 / (h[a] + d0) + (mb / J) ** 2 / (h[b] + d0))
        out["b0"][0][:, ci], out["b0"][1][:, ci], out["b0"][2][:, ci] = est, dd.std(1, ddof=1) / math.sqrt(J), J - 1
    return out, flag


def mde80(est, se, df, ci):
    p0 = W.t_p2(est / se, df)
    prev = None
    for lam in GRID:
        p = p0.copy()
        p[:, ci] = W.t_p2((est[:, ci] + lam) / se[:, ci], df[:, ci])
        pw = W.holm(p)[:, ci].mean()
        if pw >= 0.8:
            if prev is None:
                return float(lam)
            x0, y0 = prev
            return float(x0 + (0.8 - y0) * (lam - x0) / (pw - y0))
        prev = (lam, pw)
    return float("nan")


def main():
    t0 = time.time()
    d = S1M.D0
    v = 2.65 ** 2
    SC = [("equal, rho 0", 0.0, {}), ("equal, rho 0.76", 0.76, {}), ("A1 SD x2, rho 0", 0.0, {"A1": 2.0}),
          ("A1 SD x3, rho 0", 0.0, {"A1": 3.0}), ("A1 SD x2, rho 0.76", 0.76, {"A1": 2.0}),
          ("S1 SD x2, rho 0.76", 0.76, {"S1": 2.0}), ("S1 S3 S4 SD x2, rho 0.76", 0.76, {"S1": 2.0, "S3": 2.0, "S4": 2.0}),
          ("R SD x2, rho 0.76", 0.76, {"R": 2.0})]
    reps = 20000
    for i, (name, rho, mult) in enumerate(SC):
        rng = np.random.default_rng(64001 + 7 * i)
        acc = {m: [[], [], []] for m in ("HB", "HB-max", "HB-mod", "b0")}
        flags = []
        for _ in range(reps // 500):
            sd_t = np.array([math.sqrt(max((mult.get(a, 1.0) ** 2) * v - rho * v, 0.0)) for a in ARMS])
            U = (rng.standard_normal((500, len(d.seeds))) * math.sqrt(rho * v))[:, d.cell_seed]
            U = U + rng.standard_normal((500, d.nc)) * sd_t[d.cell_arm][None, :]
            o, f = methods(d, U)
            for m in acc:
                for k in range(3):
                    acc[m][k].append(o[m][k])
            flags.append(f)
        fl = np.concatenate(flags, 0)
        say(f"--- {name}: contrasts with an arm at the REML floor {fl.mean() * 100:.1f}%")
        rec = {}
        for m in acc:
            est, se, df = [np.concatenate(x, 0) for x in acc[m]]
            p = W.t_p2(est / se, df)
            fw = float(W.holm(p).any(1).mean())
            r6 = p < 0.05 / 6
            per6 = r6.mean(0)
            per5 = (p < 0.05).mean(0)
            cond_f = float(r6[fl].mean()) if fl.any() else float("nan")
            cond_nf = float(r6[~fl].mean())
            mdes = [mde80(est, se, df, ci) for ci in (0, 3)]
            rec[m] = dict(fwer=fw, worst_a6=float(per6.max()), worst_5=float(per5.max()), a6_given_floor=cond_f,
                          a6_given_no_floor=cond_nf, mde80_P1_P4=mdes, per_a6=per6.tolist())
            say(f"   {m:>6}: FWER {fw * 100:.2f}% | worst a/6 {per6.max() * 100:.2f}% | worst at 5% {per5.max() * 100:.2f}% | "
                f"a/6 given floor {cond_f * 100:.2f}%, no floor {cond_nf * 100:.2f}% | MDE80 P1/P4 {mdes[0]:.2f}/{mdes[1]:.2f}")
        RES[name] = rec
    say(f"total {time.time() - t0:.0f} s")
    (HERE / "verify_floorfix_results.json").write_text(json.dumps(RES, indent=1, default=float))
    (HERE / "verify_floorfix_out.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
