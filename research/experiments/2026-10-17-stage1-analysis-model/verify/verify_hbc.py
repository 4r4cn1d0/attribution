#!/usr/bin/env python3
"""verify_hbc.py: seed-level check of HB's seed part (HB0) against a design-based variant HB-C.

HB-C = HB with one seed effect per design cluster: {a0, S1, S3, S4} (a0's corpus plus 48 rows, 38 steps) and
{R, A1, L1, H1} (600 rows removed, 33 steps). Every primary contrast lies inside one cluster, so HB-C needs no
assumption that the two clusters share one seed shift. The cluster split is fixed by the design (row counts and
step counts), not by any measured value. Same estimator (paired mean on common seeds), same REML per-arm variances
(the draft's reml_hetero, called read-only on a design object with seed x cluster columns), same Satterthwaite df.

Cell-level normal data (sampling folded into the arm-specific part); per-arm total SD 2.65 pp in every scenario.
Planning simulation only; no evaluation record is read. Writes verify_hbc_out.txt and verify_hbc_results.json.
Run: PYTHONDONTWRITEBYTECODE=1 <venv python> -B verify_hbc.py [--reps N]
"""
import argparse, importlib.util, json, math, pathlib, sys, time
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s1m", HERE / "rerun" / "stage1_model_sim.py")
S1M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S1M)
W = S1M.W
ARMS, CON = S1M.ARMS, S1M.CONTRASTS
CLUSTER = {"a0": 0, "S1": 0, "S3": 0, "S4": 0, "R": 1, "A1": 1, "L1": 1, "H1": 1}
OUT, RES = [], {}


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


class ClusterDesign:
    """Same cells as a Design, but the seed columns are seed x cluster indicators (one dropped per cluster)."""

    def __init__(self, d):
        self.cell_arm, self.cell_seed, self.nc, self.con = d.cell_arm, d.cell_seed, d.nc, d.con
        self.arm_cells, self.n_arm = d.arm_cells, d.n_arm
        cols = []
        keys = sorted({(CLUSTER[ARMS[a]], s) for a, s in zip(d.cell_arm, d.cell_seed)})
        first = {}
        for g, s in keys:
            first.setdefault(g, (g, s))
        keys = [k for k in keys if k != first[k[0]]]
        X = np.zeros((d.nc, len(ARMS) + len(keys)))
        for i, (a, s) in enumerate(zip(d.cell_arm, d.cell_seed)):
            X[i, a] = 1.0
            k = (CLUSTER[ARMS[a]], s)
            if k in keys:
                X[i, len(ARMS) + keys.index(k)] = 1.0
        self.X = X
        self.XtX_inv = np.linalg.inv(X.T @ X)
        self.pinvT = np.linalg.pinv(X).T
        lev = 1.0 - np.diag(X @ self.XtX_inv @ X.T)
        self.df_res = d.nc - X.shape[1]
        self.h_arm = np.array([lev[self.cell_arm == a].sum() for a in range(len(ARMS))])


def hb_seed(d, U):
    th, vth = S1M.reml_hetero(d, U)
    B = U.shape[0]
    est, se, df = np.zeros((B, 6)), np.zeros((B, 6)), np.zeros((B, 6))
    for ci, c in enumerate(d.con):
        a, b, J = c["a"], c["b"], c["J"]
        dd = U[:, c["ia"]] - U[:, c["ib"]]
        vs = (th[:, a] + th[:, b]) / J
        var_vs = (vth[:, a, a] + vth[:, b, b] + 2 * vth[:, a, b]) / J ** 2
        est[:, ci], se[:, ci], df[:, ci] = dd.mean(1), np.sqrt(vs), 2 * vs ** 2 / np.maximum(var_vs, 1e-300)
    return est, se, df


GRID = np.round(np.arange(0.0, 20.01, 0.25), 2)


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20000)
    a = ap.parse_args()
    t0 = time.time()
    W.self_test()
    v = 2.65 ** 2
    rho_low = 1 - 2.15 ** 2 / (2 * 2.65 ** 2)
    SC = [
        ("additive rho 0 (N1-like)", 0.0, []),
        ("additive rho 0.67 (PREREG low)", rho_low, []),
        ("additive rho 0.76 (N4-like, no CRN)", 0.76, []),
        ("two clusters 0.4 each, shared 0.3", 0.3, [({"a0", "S1", "S3", "S4"}, 0.4), ({"R", "A1", "L1", "H1"}, 0.4)]),
        ("add cluster only 0.4 (a0 S1 S3 S4), shared 0.3", 0.3, [({"a0", "S1", "S3", "S4"}, 0.4)]),
        ("sub-cluster A1 L1 H1 0.3, shared 0.3", 0.3, [({"A1", "L1", "H1"}, 0.3)]),
        ("sub-cluster S1 S3 S4 0.4, shared 0.3", 0.3, [({"S1", "S3", "S4"}, 0.4)]),
    ]
    for dname, d in (("D0", S1M.D0), ("D1", S1M.D1)):
        dc = ClusterDesign(d)
        say(f"[{dname}] HB residual df {d.df_b2}; HB-C residual df {dc.df_res}; HB-C residual df by arm "
            + ", ".join(f"{x} {h:.2f}" for x, h in zip(ARMS, dc.h_arm)))
        for i, (name, s_share, clusters) in enumerate(SC):
            if dname == "D1" and i not in (0, 2, 3):
                continue
            rng = np.random.default_rng(88001 + 13 * i + (500 if dname == "D1" else 0))
            acc = {"HB0": [[], [], []], "HB-C": [[], [], []]}
            done = 0
            while done < a.reps:
                B = min(500, a.reps - done)
                U = (rng.standard_normal((B, len(d.seeds))) * math.sqrt(s_share * v))[:, d.cell_seed]
                used = np.zeros(len(ARMS))
                for members, share in clusters:
                    cm = rng.standard_normal((B, len(d.seeds))) * math.sqrt(share * v)
                    mask = np.array([ARMS[x] in members for x in d.cell_arm])
                    U[:, mask] += cm[:, d.cell_seed[mask]]
                    for x in members:
                        used[ARMS.index(x)] += share
                t_sd = np.sqrt(np.maximum(1.0 - s_share - used, 0.0) * v)
                U = U + rng.standard_normal((B, d.nc)) * t_sd[d.cell_arm][None, :]
                for m, dd in (("HB0", d), ("HB-C", dc)):
                    r = hb_seed(dd, U)
                    for k in range(3):
                        acc[m][k].append(r[k])
                done += B
            rec = {}
            line = f"--- [{dname}] {name}"
            say(line)
            for m in acc:
                est, se, df = [np.concatenate(x, 0) for x in acc[m]]
                p = W.t_p2(est / se, df)
                fw = float(W.holm(p).any(1).mean())
                per6 = (p < 0.05 / 6).mean(0)
                per5 = (p < 0.05).mean(0)
                ratio = np.sqrt((se ** 2).mean(0)) / est.std(0)
                mdes = [mde80(est, se, df, ci) for ci in (0, 3, 4)]
                rec[m] = dict(fwer=fw, per_a6=per6.tolist(), per_5=per5.tolist(), se_over_sd=ratio.tolist(),
                              mde80_P1_P4_P5=mdes, med_df=np.median(df, 0).tolist(), true_sd=est.std(0).tolist())
                say(f"   {m:>4}: FWER {fw * 100:.2f}% | worst a/6 {per6.max() * 100:.2f}% | worst at 5% {per5.max() * 100:.2f}% | "
                    f"SE/SD " + " ".join(f"{x:.2f}" for x in ratio) + f" | med df P1 {np.median(df[:, 0]):.1f} P4 {np.median(df[:, 3]):.1f}"
                    f" | MDE80 P1/P4/P5 " + "/".join(f"{x:.2f}" for x in mdes) + f" | true pair SD P1 {est[:, 0].std() * math.sqrt(6 if dname else 1):.2f}")
            RES[f"{dname} {name}"] = rec
    say(f"total {time.time() - t0:.0f} s")
    (HERE / "verify_hbc_results.json").write_text(json.dumps(RES, indent=1, default=float))
    (HERE / "verify_hbc_out.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
