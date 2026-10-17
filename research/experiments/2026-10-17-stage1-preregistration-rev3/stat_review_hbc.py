#!/usr/bin/env python3
"""stat_review_hbc.py: statistics review checks of HB-C (rev3 section 3.2) at the seed level.

Reuses, read-only, the analysis-model draft's planning code (verify/rerun/stage1_model_sim.py: Design,
reml_hetero; sim_w2.py: t functions, Holm), loaded by file path with bytecode writing off. Nothing is written
outside this folder. Cell-level normal data, as verify/verify_hbc.py does (sampling and prompt noise folded into the
arm-specific part; no arm x prompt term, so this is the seed part only, like S-0).

Checks:
 A. Design D1 (a0 and R at 1101-1107; six method arms at 1102-1107): HB-C per-contrast size at 5% and at Phi's start
    level 0.75% (two-sided), median Satterthwaite df, REML floor rate, and the MDE80 and 80% "better" effect at 0.75%
    (and Holm, to compare with VR-B), for pair SD 1.84 / 3.75 / 4.5 pp, a two-cluster world, and unequal arm variances.
 B. "Block A only" (seeds 1102-1104 for the method arms; a0, R 1101-1104): the same, beside the per-contrast paired t
    (2 df).
 C. LN-20 item 1: the theta0 contrast's seed part. AMD A.8 (REML residual variance / J_m) against LN-20 (the arm's own
    between-seed variance / J_m, J_m - 1 df), with an optional item part.
 D. LN-20 item 2: a cross-cluster pair (A1 against a0). In-model form (REML variances of both arms / J) against the
    pair's own paired variance (J - 1 df).
 E. The t-quantile cost of Phi's start level (0.75%) against Holm's 0.833% at HB-C's df.
Run: <venv python> -I -B stat_review_hbc.py [--reps N]
"""
import argparse, importlib.util, json, math, pathlib, sys, time
import numpy as np
import warnings
warnings.filterwarnings("ignore")

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
AMD_RERUN = pathlib.Path("/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-analysis-model/verify/rerun")
_spec = importlib.util.spec_from_file_location("s1m_ro", AMD_RERUN / "stage1_model_sim.py")
S1M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S1M)
W = S1M.W
ARMS = S1M.ARMS
CLUSTER = {"a0": 0, "S1": 0, "S3": 0, "S4": 0, "R": 1, "A1": 1, "L1": 1, "H1": 1}
FLOOR = 1e-2
OUT, RES = [], {}


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


class ClusterDesign:
    """HB-C: arm columns plus seed x cluster indicator columns (one dropped per cluster)."""

    def __init__(self, d):
        self.cell_arm, self.cell_seed, self.nc, self.con = d.cell_arm, d.cell_seed, d.nc, d.con
        self.arm_cells, self.n_arm, self.seeds = d.arm_cells, d.n_arm, d.seeds
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


def hbc_fit(dc, U):
    th, vth = S1M.reml_hetero(dc, U, floor=FLOOR)
    B = U.shape[0]
    est, se, df = np.zeros((B, 6)), np.zeros((B, 6)), np.zeros((B, 6))
    for ci, c in enumerate(dc.con):
        a, b, J = c["a"], c["b"], c["J"]
        dd = U[:, c["ia"]] - U[:, c["ib"]]
        vs = (th[:, a] + th[:, b]) / J
        var_vs = (vth[:, a, a] + vth[:, b, b] + 2 * vth[:, a, b]) / J ** 2
        est[:, ci], se[:, ci], df[:, ci] = dd.mean(1), np.sqrt(vs), 2 * vs ** 2 / np.maximum(var_vs, 1e-300)
    floor_any = (th <= FLOOR * 1.0001).any(1)
    return est, se, df, th, vth, floor_any


def paired_own(dc, U):
    B = U.shape[0]
    est, se, df = np.zeros((B, 6)), np.zeros((B, 6)), np.zeros((B, 6))
    for ci, c in enumerate(dc.con):
        dd = U[:, c["ia"]] - U[:, c["ib"]]
        J = dd.shape[1]
        est[:, ci], se[:, ci], df[:, ci] = dd.mean(1), dd.std(1, ddof=1) / math.sqrt(J), J - 1
    return est, se, df


def draw(rng, d, B, v_arm, shared, clusters=(), mult=None):
    """Seed-level cells: shared seed shift (share of v_arm), optional cluster components, arm-specific rest."""
    v = np.asarray(v_arm, float) * np.ones(len(ARMS))
    if mult:
        for arm, m in mult.items():
            v[ARMS.index(arm)] *= m ** 2
    s = rng.standard_normal((B, len(d.seeds))) * math.sqrt(shared * v.min())
    U = s[:, d.cell_seed].copy()
    used = np.full(len(ARMS), shared * v.min())
    for members, share in clusters:
        cm = rng.standard_normal((B, len(d.seeds))) * math.sqrt(share * v.min())
        mask = np.array([ARMS[x] in members for x in d.cell_arm])
        U[:, mask] += cm[:, d.cell_seed[mask]]
        for x in members:
            used[ARMS.index(x)] += share * v.min()
    t_sd = np.sqrt(np.maximum(v - used, 0.0))
    return U + rng.standard_normal((B, d.nc)) * t_sd[d.cell_arm][None, :]


GRID = np.round(np.arange(0.0, 25.01, 0.25), 2)


def first_cross(xs, ys, level=0.8):
    prev = None
    for x, y in zip(xs, ys):
        if y >= level:
            if prev is None:
                return float(x)
            return float(prev[0] + (level - prev[1]) * (x - prev[0]) / (y - prev[1]))
        prev = (x, y)
    return float("nan")


def mde_and_better(est, se, df, ci, alpha2, delta=5.0):
    pw, bt = [], []
    for lam in GRID:
        e = est[:, ci] + lam
        p = W.t_p2(e / se[:, ci], df[:, ci])
        r = p <= alpha2
        pw.append(r.mean())
        bt.append((r & (e >= delta)).mean())
    return first_cross(GRID, pw), first_cross(GRID, bt)


def mde_holm(est, se, df, ci):
    p0 = W.t_p2(est / se, df)
    ys = []
    for lam in GRID:
        p = p0.copy()
        p[:, ci] = W.t_p2((est[:, ci] + lam) / se[:, ci], df[:, ci])
        ys.append(W.holm(p)[:, ci].mean())
    return first_cross(GRID, ys)


def part_ab(reps):
    D1 = S1M.D1
    DA = S1M.Design("block A only (a0, R 1101-1104; methods 1102-1104)",
                    S1M.seeds(range(1101, 1105), range(1101, 1105), range(1102, 1105)))
    say("=" * 100)
    say("A/B. HB-C at the seed level: D1 and block A only")
    for dname, d in (("D1", D1), ("A-only", DA)):
        dc = ClusterDesign(d)
        say(f"[{dname}] cells {d.nc}; HB-C residual df {dc.df_res}; residual df by arm " +
            ", ".join(f"{x} {h:.2f}" for x, h in zip(ARMS, dc.h_arm)) +
            "; pairs per contrast " + ", ".join(f"{c['name']} {c['J']}" for c in d.con))
        v265 = 2.65 ** 2
        scen = [
            ("pair SD 1.84 (one shift, rho 0.76)", v265, 0.76, (), None, True),
            ("pair SD 3.75 (one shift, rho 0)", v265, 0.0, (), None, True),
            ("pair SD 4.5 (rho 0, arm SD 3.18)", (4.5 / math.sqrt(2)) ** 2, 0.0, (), None, True),
            ("two clusters (shared 0.3, cluster 0.4 each)", v265, 0.3,
             (({"a0", "S1", "S3", "S4"}, 0.4), ({"R", "A1", "L1", "H1"}, 0.4)), None, True),
            ("A1 SD x 2, rho 0", v265, 0.0, (), {"A1": 2.0}, False),
            ("S1 SD x 2, rho 0.76", v265, 0.76, (), {"S1": 2.0}, False),
        ]
        if dname == "A-only":
            scen = [scen[0], scen[1], scen[4]]
        for i, (nm, v, sh, cl, mult, do_mde) in enumerate(scen):
            rng = np.random.default_rng(31000 + 101 * i + (7 if dname == "A-only" else 0))
            acc = {"est": [], "se": [], "df": [], "floor": [], "pe": [], "ps": [], "pd": []}
            done = 0
            while done < reps:
                B = min(500, reps - done)
                U = draw(rng, d, B, v, sh, cl, mult)
                est, se, df, th, vth, fl = hbc_fit(dc, U)
                pe, ps, pdf = paired_own(dc, U)
                for k, x in (("est", est), ("se", se), ("df", df), ("floor", fl), ("pe", pe), ("ps", ps), ("pd", pdf)):
                    acc[k].append(x)
                done += B
            est, se, df, fl, pe, ps, pdf = (np.concatenate(acc[k], 0) for k in ("est", "se", "df", "floor", "pe", "ps", "pd"))
            p = W.t_p2(est / se, df)
            pp = W.t_p2(pe / ps, pdf)
            s5, s075 = (p <= 0.05).mean(0), (p <= 0.0075).mean(0)
            q5, q075 = (pp <= 0.05).mean(0), (pp <= 0.0075).mean(0)
            rec = dict(size5=s5.tolist(), size075=s075.tolist(), med_df=np.median(df, 0).tolist(),
                       p10_df=np.percentile(df, 10, 0).tolist(), floor_rate=float(fl.mean()),
                       se_over_sd=(np.sqrt((se ** 2).mean(0)) / est.std(0)).tolist(),
                       paired_size5=q5.tolist(), paired_size075=q075.tolist(),
                       holm_fwer=float(W.holm(p).any(1).mean()))
            line = (f"   [{dname}] {nm}: HB-C size at 5% max {s5.max() * 100:.2f}% (min {s5.min() * 100:.2f}); at 0.75% max "
                    f"{s075.max() * 100:.3f}%; Holm FWER {rec['holm_fwer'] * 100:.2f}%; med df P1 {np.median(df[:, 0]):.2f} "
                    f"P4 {np.median(df[:, 3]):.2f} (10th pct P1 {np.percentile(df[:, 0], 10):.2f}); fits with an arm at the floor "
                    f"{fl.mean() * 100:.2f}%; SE/SD P1 {rec['se_over_sd'][0]:.2f} | paired t (J-1 df): size 5% max "
                    f"{q5.max() * 100:.2f}%, 0.75% max {q075.max() * 100:.3f}%")
            say(line)
            if do_mde:
                m = {}
                for nmc, ci in (("P1", 0), ("P4", 3), ("P5", 4)):
                    m80, b80 = mde_and_better(est, se, df, ci, 0.0075)
                    mh = mde_holm(est, se, df, ci)
                    pm80, pb80 = mde_and_better(pe, ps, pdf, ci, 0.0075)
                    m[nmc] = dict(mde80_phi075=m80, better80_phi075=b80, mde80_holm=mh, paired_mde80_075=pm80, paired_better80_075=pb80)
                rec["mde"] = m
                say("      MDE80 at 0.75% (P1/P4/P5): " + "/".join(f"{m[x]['mde80_phi075']:.2f}" for x in m) +
                    " | Holm MDE80: " + "/".join(f"{m[x]['mde80_holm']:.2f}" for x in m) +
                    " | 80% 'better' effect at 0.75%: " + "/".join(f"{m[x]['better80_phi075']:.2f}" for x in m) +
                    " | paired-t MDE80 at 0.75%: " + "/".join(f"{m[x]['paired_mde80_075']:.2f}" for x in m))
            RES[f"{dname} | {nm}"] = rec


def part_c(reps):
    say("=" * 100)
    say("C. LN-20 item 1: the theta0 contrast (theta0 fixed, no seed). Rejection rate at the boundary null, two tails pooled")
    say("   (one-sided 5% = the per-comparison state; one-sided 0.375% = F_k inside Phi after U_k).")
    d = S1M.D1
    dc = ClusterDesign(d)
    v = 2.65 ** 2
    for rho in (0.0, 0.5, 0.76):
        for kappa in (0.0, 1.0, 4.0):
            rng = np.random.default_rng(int(4100 + 100 * rho + 10 * kappa))
            res = {}
            acc = {k: [] for k in ("amd_e", "amd_s", "amd_d", "ln_e", "ln_s", "ln_d", "arm")}
            done = 0
            while done < reps:
                B = min(500, reps - done)
                U = draw(rng, d, B, v, rho)
                th, vth = S1M.reml_hetero(dc, U, floor=FLOOR)
                for arm in ("S1", "a0", "R"):
                    ai = ARMS.index(arm)
                    cells = d.arm_cells[ai]
                    J = len(cells)
                    vals = U[:, cells]
                    true_seed_var = v / J                       # (shift + arm part) / J: the true seed-part variance
                    vitem = kappa * true_seed_var
                    e = vals.mean(1) + rng.standard_normal(B) * math.sqrt(vitem)
                    vs_amd = th[:, ai] / J
                    df_amd_s = 2 * vs_amd ** 2 / np.maximum(vth[:, ai, ai] / J ** 2, 1e-300)
                    vs_ln = vals.var(1, ddof=1) / J
                    for tag, vs, dfs in (("amd", vs_amd, df_amd_s), ("ln", vs_ln, np.full(B, J - 1.0))):
                        V = vs + vitem
                        dfc = V ** 2 / (vs ** 2 / dfs + (vitem ** 2 / 1e6 if vitem > 0 else 0.0))
                        acc[f"{tag}_e"].append(e)
                        acc[f"{tag}_s"].append(np.sqrt(V))
                        acc[f"{tag}_d"].append(dfc)
                    acc["arm"].append(np.full(B, ai))
                done += B
            arm = np.concatenate(acc["arm"])
            for tag in ("amd", "ln"):
                e, s, dfv = (np.concatenate(acc[f"{tag}_{k}"]) for k in ("e", "s", "d"))
                p1 = W.t_sf(np.abs(e) / s, dfv)                  # one tail; pooled over both tails below
                for arm_name in ("S1", "a0", "R"):
                    mk = arm == ARMS.index(arm_name)
                    r5 = (p1[mk] <= 0.05).mean() / 2               # P(one named tail) = P(either tail) / 2
                    r0375 = (p1[mk] <= 0.00375).mean() / 2
                    res[f"{tag}|{arm_name}"] = dict(one_sided_5=float(r5), one_sided_0375=float(r0375),
                                                    med_df=float(np.median(dfv[mk])))
            say(f"   rho {rho:.2f}, item part {kappa:.0f} x seed part: " + "; ".join(
                f"{k} 5%->{v_['one_sided_5'] * 100:.2f}% 0.375%->{v_['one_sided_0375'] * 100:.3f}% (df {v_['med_df']:.1f})" for k, v_ in res.items()))
            RES[f"C rho {rho} kappa {kappa}"] = res


def part_d(reps):
    say("=" * 100)
    say("D. LN-20 item 2: a cross-cluster pair (A1 against a0, common seeds 1102-1107), two-sided size")
    d = S1M.D1
    dc = ClusterDesign(d)
    v = 2.65 ** 2
    ia0, iA1 = ARMS.index("a0"), ARMS.index("A1")
    common = [s for s in range(len(d.seeds)) if d.seeds[s] >= 1102]
    cell_of = {(a, s): i for i, (a, s) in enumerate(zip(d.cell_arm, d.cell_seed))}
    c_a0 = [cell_of[(ia0, s)] for s in common]
    c_A1 = [cell_of[(iA1, s)] for s in common]
    J = len(common)
    for nm, sh, cl in (("one shift, rho 0.76", 0.76, ()), ("one shift, rho 0", 0.0, ()),
                       ("two clusters (shared 0.3, cluster 0.4 each)", 0.3,
                        (({"a0", "S1", "S3", "S4"}, 0.4), ({"R", "A1", "L1", "H1"}, 0.4)))):
        rng = np.random.default_rng(5200 + len(nm))
        ps_in, ps_pair, dfs_in = [], [], []
        done = 0
        while done < reps:
            B = min(500, reps - done)
            U = draw(rng, d, B, v, sh, cl)
            th, vth = S1M.reml_hetero(dc, U, floor=FLOOR)
            dd = U[:, c_a0] - U[:, c_A1]
            e = dd.mean(1)
            vs = (th[:, ia0] + th[:, iA1]) / J
            dfv = 2 * vs ** 2 / np.maximum((vth[:, ia0, ia0] + vth[:, iA1, iA1] + 2 * vth[:, ia0, iA1]) / J ** 2, 1e-300)
            ps_in.append(W.t_p2(e / np.sqrt(vs), dfv))
            ps_pair.append(W.t_p2(e / (dd.std(1, ddof=1) / math.sqrt(J)), np.full(B, J - 1.0)))
            dfs_in.append(dfv)
            done += B
        pin, ppair, dfin = np.concatenate(ps_in), np.concatenate(ps_pair), np.concatenate(dfs_in)
        rec = dict(in_model_5=float((pin <= 0.05).mean()), in_model_075=float((pin <= 0.0075).mean()),
                   pair_5=float((ppair <= 0.05).mean()), pair_075=float((ppair <= 0.0075).mean()),
                   in_model_med_df=float(np.median(dfin)))
        say(f"   {nm}: in-model (REML variances of both arms / J) 5% -> {rec['in_model_5'] * 100:.2f}%, 0.75% -> "
            f"{rec['in_model_075'] * 100:.3f}% (med df {rec['in_model_med_df']:.1f}) | pair's own variance (5 df) 5% -> "
            f"{rec['pair_5'] * 100:.2f}%, 0.75% -> {rec['pair_075'] * 100:.3f}%")
        RES[f"D {nm}"] = rec


def part_e():
    say("=" * 100)
    say("E. Cost of Phi's start level (0.75%) against Holm's 0.833% (two-sided), as an MDE ratio at 80% power")
    rows = {}
    for df in (5.0, 5.5, 6.0, 8.0, 42.0):
        z8 = W.t_ppf(0.8, df)
        a = W.t_ppf(1 - 0.0075 / 2, df) + z8
        b = W.t_ppf(1 - 0.05 / 12, df) + z8
        rows[df] = a / b - 1
        say(f"   df {df:>4}: t(0.99625) {W.t_ppf(1 - 0.0075 / 2, df):.3f}, t(0.995833) {W.t_ppf(1 - 0.05 / 12, df):.3f}; MDE rises {100 * (a / b - 1):.2f}%")
    RES["E"] = rows
    q = {}
    for df in (5.0, 5.5, 6.0, 8.0, 100.0, 1e6):
        q[df] = dict(t95=W.t_ppf(0.95, df), t99625=W.t_ppf(0.99625, df), t999583=W.t_ppf(1 - 0.000417, df),
                     t99865=W.t_ppf(1 - 0.00135, df))
        say(f"   one-sided quantiles at df {df:g}: 5% {q[df]['t95']:.3f}; 0.375% {q[df]['t99625']:.3f}; 0.135% {q[df]['t99865']:.3f}; 0.042% {q[df]['t999583']:.3f}")
    RES["quantiles"] = q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20000)
    a = ap.parse_args()
    t0 = time.time()
    W.self_test()
    say("stat_review_hbc.py; numpy", np.__version__, "; reps", a.reps)
    part_e()
    part_ab(a.reps)
    part_c(a.reps)
    part_d(a.reps)
    say(f"total {time.time() - t0:.0f} s")
    (HERE / "stat_review_hbc_out.txt").write_text("\n".join(OUT) + "\n")
    (HERE / "stat_review_hbc_results.json").write_text(json.dumps(RES, indent=1, default=float))


if __name__ == "__main__":
    main()
