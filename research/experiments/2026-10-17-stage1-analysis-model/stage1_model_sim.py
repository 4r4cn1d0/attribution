#!/usr/bin/env python3
"""stage1_model_sim.py: operating characteristics of the proposed stage-1 primary model (HB) against the alternatives.

Planning simulation only. It reads no evaluation record: the prompt bank and the noise values come from
sim_w2_results.json (written by sim_w2.py in this folder from Gate A labels and the wave-0a noise gate). It opens no
selector.jsonl, hidden/, held-out file, wave-0b rows.jsonl or groups.json. No prompt, answer or id is printed.

HB (the proposed primary): the estimate of contrast k is the mean over the common seeds of the seed-matched differences
U(comparator, j) - U(repair, j). Its variance is (s2_c + s2_m) / J_k + the crossed prompt term, where s2_a is the
arm-specific residual variance of a seed-blocked additive model (arm and seed fixed effects) fitted by REML to all cells
with one residual variance per arm. df: Satterthwaite, from the inverse REML information, combined with the prompt
term's df. HB0 is HB without the prompt term (inference fixed to these 200 prompts).

Compared: (a) unpaired, pooled variance (the 8 Oct text); (aW) unpaired Welch; (b) paired per contrast, crossed
seed x prompt (its own variance; ~5 df); (b2x) seed-blocked, pooled residual, plus the prompt term; (b3) b2x with a
per-arm variance check falling back to (b). Designs: D0 = the approved seed plan (a0 1101-1106, R 1101-1108, method
arms 1102-1107); D1 = R_1108 moved to a0_1107 (a0 1101-1107, R 1101-1107).

Run: PYTHONDONTWRITEBYTECODE=1 <venv python> -B stage1_model_sim.py [--reps N] [--quick]
Writes stage1_model_sim_out.txt and stage1_model_sim_results.json beside this file. All random streams are seeded.
"""
import argparse, importlib.util, json, math, pathlib, sys, time
import numpy as np
import warnings
warnings.filterwarnings("ignore", message=".*encountered in matmul")

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("sim_w2", HERE / "sim_w2.py")
W = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(W)

R0 = json.loads((HERE / "sim_w2_results.json").read_text())
BANK, EMP = R0["bank"], R0["empirical"]
ARMS, CONTRASTS = W.ARMS, W.CONTRASTS
NPROMPT, NSAMP = 200, 3
V_SAMP = 1e4 * BANK["epq"] / (NPROMPT * NSAMP)
KPP = 100.0 * BANK["epq"]
OUT = []


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


class Design:
    def __init__(self, name, arm_seeds):
        self.name = name
        self.arm_seeds = {a: list(arm_seeds[a]) for a in ARMS}
        self.seeds = sorted({s for a in ARMS for s in self.arm_seeds[a]})
        self.cells = [(ai, self.seeds.index(s)) for ai, a in enumerate(ARMS) for s in self.arm_seeds[a]]
        self.cell_arm = np.array([c[0] for c in self.cells])
        self.cell_seed = np.array([c[1] for c in self.cells])
        self.nc = len(self.cells)
        X = np.zeros((self.nc, len(ARMS) + len(self.seeds) - 1))
        for i, (a, s) in enumerate(self.cells):
            X[i, a] = 1.0
            if s > 0:
                X[i, len(ARMS) + s - 1] = 1.0
        self.X = X
        self.XtX_inv = np.linalg.inv(X.T @ X)
        self.pinvT = np.linalg.pinv(X).T
        H = X @ self.XtX_inv @ X.T
        self.df_b2 = self.nc - X.shape[1]
        lev = 1.0 - np.diag(H)
        self.h_arm = np.array([lev[self.cell_arm == a].sum() for a in range(len(ARMS))])
        self.Z = np.zeros((self.nc, len(ARMS)))
        self.Z[np.arange(self.nc), self.cell_arm] = 1.0
        self.arm_cells = [np.where(self.cell_arm == a)[0] for a in range(len(ARMS))]
        self.n_arm = np.array([len(ix) for ix in self.arm_cells])
        self.df_pool = self.nc - len(ARMS)
        self.con = []
        for name_, comp, m in CONTRASTS:
            a, b = ARMS.index(comp), ARMS.index(m)
            common = sorted(set(self.arm_seeds[comp]) & set(self.arm_seeds[m]))
            ia = [self.cells.index((a, self.seeds.index(s))) for s in common]
            ib = [self.cells.index((b, self.seeds.index(s))) for s in common]
            cvec = np.zeros(X.shape[1]); cvec[a] = 1.0; cvec[b] = -1.0
            self.con.append(dict(name=name_, a=a, b=b, ia=ia, ib=ib, J=len(common), common=common,
                                 v2=float(cvec @ self.XtX_inv @ cvec), cvec=cvec))
        self.kappa = W.f_ppf(0.95, float(self.h_arm[2]), float(self.df_b2))


def seeds(a0, R, m):
    d = {"a0": a0, "R": R}
    for x in ("A1", "L1", "H1", "S1", "S3", "S4"):
        d[x] = m
    return d


D0 = Design("D0 approved plan (a0 1101-1106, R 1101-1108, methods 1102-1107)",
            seeds(range(1101, 1107), range(1101, 1109), range(1102, 1108)))
D1 = Design("D1 R_1108 moved to a0_1107 (a0 1101-1107, R 1101-1107, methods 1102-1107)",
            seeds(range(1101, 1108), range(1101, 1108), range(1102, 1108)))


def scen(name, sd_tot, c, rho=None, sd_s=None, mults=None, gamma=0.0, neg_arm=None, note=""):
    sc = W.make_scenario(name, BANK, V_SAMP, sd_tot, c=c, rho=rho, sd_s=sd_s, gamma=gamma, neg_arm=neg_arm, note=note)
    sd_t_pp = np.array(sc["sd_t_pp"], float)
    for arm, mult in (mults or {}).items():
        sd_t_pp[ARMS.index(arm)] = math.sqrt((mult * sd_tot) ** 2 - V_SAMP - sc["sd_s_pp"] ** 2)
    sc["sd_t_pp"] = sd_t_pp.tolist()
    sc["sd_t"] = sd_t_pp / KPP
    sc["mults"] = dict(mults or {})
    return sc


def simulate_batch(rng, d, sc, B, eta=None):
    b = rng.standard_normal((B, NPROMPT)) * BANK["s"] + BANK["m"]
    s = rng.standard_normal((B, len(d.seeds))) * sc["sd_s"]
    t = rng.standard_normal((B, d.nc)) * sc["sd_t"][d.cell_arm][None, :]
    lin = b[:, None, :] + (sc["load"][d.cell_arm][None, :] * s[:, d.cell_seed])[:, :, None] + t[:, :, None]
    if eta is not None:
        lin = lin + eta[d.cell_arm][None, :, None]
    if sc["gamma"] > 0:
        g = rng.standard_normal((B, len(ARMS), NPROMPT)) * sc["gamma"]
        lin = lin + g[:, d.cell_arm, :]
    pi = (1.0 / (1.0 + np.exp(-lin))).astype(np.float32)
    V = rng.random((B, len(d.seeds), NPROMPT, NSAMP), dtype=np.float32)
    Wu = rng.random((B, d.nc, NPROMPT, NSAMP), dtype=np.float32)
    if sc["c"] > 0:
        M = rng.random((B, d.nc, NPROMPT, NSAMP), dtype=np.float32) < math.sqrt(sc["c"])
        Wu = np.where(M, V[:, d.cell_seed], Wu)
    Y = (Wu < pi[..., None]).astype(np.float32)
    shares = Y.mean(-1)
    return shares.mean(-1).astype(np.float64) * 100.0, shares


GROUPS4 = {"a0": 0, "R": 1, "A1": 2, "L1": 2, "H1": 2, "S1": 3, "S3": 3, "S4": 3}


def reml_hetero(d, y, group_of_arm=None, iters=25, floor=1e-2, tol=1e-6):
    """REML for y = X beta + e, Var(e_i) = th[group(arm(i))]; Fisher scoring on log th.

    group_of_arm: array (A,) mapping each arm to a variance group (default: one group per arm).
    Returns th (B, A) mapped back to arms, and the inverse REML information mapped to arms (B, A, A)."""
    X = d.X
    gmap = np.arange(len(ARMS)) if group_of_arm is None else np.asarray(group_of_arm)
    G = int(gmap.max()) + 1
    cell_g = gmap[d.cell_arm]
    Zg = np.zeros((d.nc, G)); Zg[np.arange(d.nc), cell_g] = 1.0
    resid = y - (y @ d.pinvT) @ X.T
    lev = 1.0 - np.diag(X @ d.XtX_inv @ X.T)
    hg = lev @ Zg
    th = np.maximum((resid ** 2) @ Zg / np.maximum(hg[None, :], 1e-9), floor)
    idx = np.arange(d.nc)
    XT = X.T[None]

    def parts(th_):
        w = 1.0 / th_[:, cell_g]
        WX = w[:, :, None] * X[None]
        Ainv = np.linalg.inv(XT @ WX)
        P = -((WX @ Ainv) @ WX.transpose(0, 2, 1))
        P[:, idx, idx] += w
        return P

    def info_of(P):
        return 0.5 * (Zg.T[None] @ ((P * P) @ Zg))

    eye = 1e-12 * np.eye(G)[None]
    for _ in range(iters):
        P = parts(th)
        Py = (P @ y[:, :, None])[:, :, 0]
        trPD = P[:, idx, idx] @ Zg
        score = 0.5 * ((Py ** 2) @ Zg - trPD)
        info = info_of(P)
        g = th * score
        iphi = th[:, :, None] * info * th[:, None, :]
        step = np.linalg.solve(iphi + eye, g[:, :, None])[:, :, 0]
        step = np.clip(step, -2.0, 2.0)
        th = np.maximum(th * np.exp(step), floor)
        if np.abs(step).max() < tol:
            break
    vth_g = np.linalg.inv(info_of(parts(th)) + eye)
    return th[:, gmap], vth_g[:, gmap][:, :, gmap]


METHODS = ["a", "aW", "b", "b2x", "b3", "HB", "HB0", "HG"]
METHOD_TEXT = {"a": "(a) unpaired, pooled variance [8 Oct text]", "aW": "(aW) unpaired Welch",
               "b": "(b) paired per contrast, crossed, own variance", "b2x": "(b2x) blocked, pooled residual, crossed",
               "b3": "(b3) b2x + per-arm check -> (b)", "HB": "(HB) proposed: paired mean, REML arm variances, crossed",
               "HB0": "(HB0) HB without the prompt term (these 200 prompts)",
               "HG": "(HG) HB with 4 a-priori variance groups: a0 | R | A1 L1 H1 | S1 S3 S4"}
GMAP4 = np.array([GROUPS4[a] for a in ARMS])


def analyses(d, Ucell, shares):
    B = Ucell.shape[0]
    means = np.stack([Ucell[:, ix].mean(1) for ix in d.arm_cells], 1)
    vars_ = np.stack([Ucell[:, ix].var(1, ddof=1) for ix in d.arm_cells], 1)
    pooled = (vars_ * (d.n_arm - 1)).sum(1) / d.df_pool
    beta = Ucell @ d.pinvT
    resid = Ucell - beta @ d.X.T
    s2_b2 = (resid ** 2).sum(1) / d.df_b2
    s2_arm = (resid ** 2) @ d.Z / d.h_arm[None, :]
    flagged = s2_arm / s2_b2[:, None] > d.kappa
    th, vth = reml_hetero(d, Ucell)
    thg, vthg = reml_hetero(d, Ucell, GMAP4)
    out = {m: [np.zeros((B, 6)), np.zeros((B, 6)), np.zeros((B, 6))] for m in METHODS}
    flag_c = np.zeros((B, 6), bool)
    for ci, c in enumerate(d.con):
        a, b_, J = c["a"], c["b"], c["J"]
        est_u = means[:, a] - means[:, b_]
        out["a"][0][:, ci] = est_u
        out["a"][1][:, ci] = np.sqrt(pooled * (1 / d.n_arm[a] + 1 / d.n_arm[b_]))
        out["a"][2][:, ci] = d.df_pool
        va, vb = vars_[:, a] / d.n_arm[a], vars_[:, b_] / d.n_arm[b_]
        out["aW"][0][:, ci] = est_u
        out["aW"][1][:, ci] = np.sqrt(va + vb)
        out["aW"][2][:, ci] = (va + vb) ** 2 / (va ** 2 / (d.n_arm[a] - 1) + vb ** 2 / (d.n_arm[b_] - 1))
        D = (shares[:, c["ia"], :] - shares[:, c["ib"], :]).astype(np.float64)
        P_ = D.shape[2]
        gm = D.mean((1, 2)); rm = D.mean(1); cm = D.mean(2)
        ms_p = J * ((rm - gm[:, None]) ** 2).sum(1) / (P_ - 1)
        ms_j = P_ * ((cm - gm[:, None]) ** 2).sum(1) / (J - 1)
        ms_e = ((D - rm[:, None, :] - cm[:, :, None] + gm[:, None, None]) ** 2).sum((1, 2)) / ((P_ - 1) * (J - 1))
        dfp, dfj, dfe = P_ - 1, J - 1, (P_ - 1) * (J - 1)
        ap = ms_p > ms_e
        Vb = (ms_j + np.where(ap, ms_p - ms_e, 0.0)) / (P_ * J)
        denb = ms_j ** 2 / dfj + np.where(ap, ms_p ** 2 / dfp + ms_e ** 2 / dfe, 0.0)
        est_p = gm * 100.0
        out["b"][0][:, ci] = est_p
        out["b"][1][:, ci] = np.sqrt(Vb) * 100.0
        out["b"][2][:, ci] = (Vb * P_ * J) ** 2 / denb
        pt = np.where(ap, ms_p - ms_e, 0.0) / (P_ * J) * 1e4
        pt_den = np.where(ap, (ms_p / (P_ * J) * 1e4) ** 2 / dfp + (ms_e / (P_ * J) * 1e4) ** 2 / dfe, 0.0)
        est_2 = beta @ c["cvec"]
        se2 = np.sqrt(s2_b2 * c["v2"])
        v2x = se2 ** 2 + pt
        out["b2x"][0][:, ci] = est_2
        out["b2x"][1][:, ci] = np.sqrt(v2x)
        out["b2x"][2][:, ci] = v2x ** 2 / ((se2 ** 2) ** 2 / d.df_b2 + pt_den)
        flag_c[:, ci] = flagged[:, a] | flagged[:, b_]
        # HB
        vs = (th[:, a] + th[:, b_]) / J
        var_vs = (vth[:, a, a] + vth[:, b_, b_] + 2 * vth[:, a, b_]) / J ** 2
        df_s = 2 * vs ** 2 / np.maximum(var_vs, 1e-300)
        vhb = vs + pt
        out["HB"][0][:, ci] = est_p
        out["HB"][1][:, ci] = np.sqrt(vhb)
        out["HB"][2][:, ci] = vhb ** 2 / (vs ** 2 / df_s + pt_den)
        out["HB0"][0][:, ci] = est_p
        out["HB0"][1][:, ci] = np.sqrt(vs)
        out["HB0"][2][:, ci] = df_s
        # HG: same, with the four a-priori variance groups
        vg = (thg[:, a] + thg[:, b_]) / J
        if GMAP4[a] == GMAP4[b_]:
            var_vg = 4 * vthg[:, a, a] / J ** 2
        else:
            var_vg = (vthg[:, a, a] + vthg[:, b_, b_] + 2 * vthg[:, a, b_]) / J ** 2
        df_g = 2 * vg ** 2 / np.maximum(var_vg, 1e-300)
        vhg = vg + pt
        out["HG"][0][:, ci] = est_p
        out["HG"][1][:, ci] = np.sqrt(vhg)
        out["HG"][2][:, ci] = vhg ** 2 / (vg ** 2 / df_g + pt_den)
    for k in range(3):
        out["b3"][k] = np.where(flag_c, out["b"][k], out["b2x"][k])
    return {m: tuple(v) for m, v in out.items()}, th


def run_null(d, sc, reps, batch, seed):
    rng = np.random.default_rng(seed)
    store = {m: [[], [], []] for m in METHODS}
    ths = []
    done = 0
    while done < reps:
        B = min(batch, reps - done)
        U, sh = simulate_batch(rng, d, sc, B)
        res, th = analyses(d, U, sh)
        for m in METHODS:
            for k in range(3):
                store[m][k].append(res[m][k])
        ths.append(th)
        done += B
    return {m: [np.concatenate(x, 0) for x in store[m]] for m in METHODS}, np.concatenate(ths, 0)


A6 = 0.05 / 6


def tost_p(e, se, df, delta=5.0):
    return np.maximum(W.t_sf((e + delta) / se, df), W.t_sf((delta - e) / se, df))


def null_metrics(store):
    out = {}
    for m in METHODS:
        est, se, df = store[m]
        p = W.t_p2(est / se, df)
        rej = W.holm(p)
        tp = tost_p(est, se, df)
        out[m] = dict(fwer=float(rej.any(1).mean()), worse_any=float((rej & (est < 0)).any(1).mean()),
                      rej_a6=(p < A6).mean(0).tolist(), equiv_pc=(tp < 0.05).mean(0).tolist(),
                      equiv_fw=(tp < A6).mean(0).tolist(), sd_est=est.std(0).tolist(),
                      rms_se=np.sqrt((se ** 2).mean(0)).tolist(), med_df=np.median(df, 0).tolist(),
                      p10_df=np.percentile(df, 10, 0).tolist())
    return out


GRID = np.round(np.arange(0.0, 20.01, 0.25), 2)


def first_cross(ys, level=0.8):
    for x0, x1, y0, y1 in zip(GRID[:-1], GRID[1:], ys[:-1], ys[1:]):
        if y0 < level <= y1:
            return float(x0 + (level - y0) * (x1 - x0) / (y1 - y0)) if y1 != y0 else float(x1)
    return float("nan") if ys[-1] < level else float(GRID[0])


def last_above(ys, level=0.8):
    last = float("nan")
    for x, y in zip(GRID, ys):
        if y >= level:
            last = float(x)
    return last


def curves(store, ci):
    out = {}
    for m in METHODS:
        est, se, df = store[m]
        p0 = W.t_p2(est / se, df)
        pw, bt, sb, eqp, eqf = [], [], [], [], []
        for lam in GRID:
            e = est[:, ci] + lam
            p = p0.copy()
            p[:, ci] = W.t_p2(e / se[:, ci], df[:, ci])
            rej = W.holm(p)[:, ci]
            tp = tost_p(e, se[:, ci], df[:, ci])
            pw.append(float(rej.mean())); bt.append(float((rej & (e >= 5.0)).mean()))
            sb.append(float((rej & (e > 0) & (e < 5.0)).mean()))
            eqp.append(float((tp < 0.05).mean())); eqf.append(float((tp < A6).mean()))
        e0 = est[:, ci]
        lo, hi = 0.0, 40.0
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if (tost_p(e0, se[:, ci], df[:, ci], mid) < 0.05).mean() < 0.8:
                lo = mid
            else:
                hi = mid
        i3, i5 = int(np.where(GRID == 3.0)[0][0]), int(np.where(GRID == 5.0)[0][0])
        mde = first_cross(pw)
        imde = None if mde != mde else int(np.argmin(np.abs(GRID - mde)))
        out[m] = dict(mde80=mde, better80=first_cross(bt), power5=pw[i5], better5=bt[i5],
                      better_at_mde=(bt[imde] if imde is not None else float("nan")),
                      equiv0_pc=eqp[0], equiv0_fw=eqf[0], delta80=0.5 * (lo + hi),
                      equiv80_lambda=last_above(eqp), at3=dict(equiv_pc=eqp[i3], sig_below=sb[i3], power=pw[i3]))
    return out


def direct_power(d, sc, reps, batch, seed, which, pp=5.0):
    eta = np.zeros(len(ARMS))
    shift = W.logit_shift_for(BANK, -pp)
    if which == "P1":
        eta[ARMS.index("A1")] = shift
    elif which == "P4":
        for a in ("S1", "S3", "S4"):
            eta[ARMS.index(a)] = shift
    ci = [c[0] for c in CONTRASTS].index(which)
    rng = np.random.default_rng(seed)
    hits = {m: [] for m in METHODS}
    lam = []
    done = 0
    while done < reps:
        B = min(batch, reps - done)
        U, sh = simulate_batch(rng, d, sc, B, eta=eta)
        res, _ = analyses(d, U, sh)
        for m in METHODS:
            est, se, df = res[m]
            hits[m].append(W.holm(W.t_p2(est / se, df))[:, ci])
        lam.append(res["HB"][0][:, ci])
        done += B
    return {m: float(np.concatenate(hits[m]).mean()) for m in METHODS}, float(np.concatenate(lam).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20000)
    ap.add_argument("--batch", type=int, default=200)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.reps = 1000
    t0 = time.time()
    say(f"stage1_model_sim.py  numpy {np.__version__}  reps {args.reps}  python {sys.version.split()[0]}")
    W.self_test()
    say(f"bank: logit mean {BANK['m']:.3f}, SD {BANK['s']:.3f} (from sim_w2_results.json); per-arm sampling var {V_SAMP:.3f} pp^2")
    for d in (D0, D1):
        say(f"{d.name}: {d.nc} cells; pooled df {d.df_pool}; blocked residual df {d.df_b2}; residual df by arm "
            + ", ".join(f"{a} {h:.2f}" for a, h in zip(ARMS, d.h_arm)) + f"; (b3) kappa {d.kappa:.3f}")
        say("   common seeds: " + "; ".join(f"{c['name']} {c['common'][0]}-{c['common'][-1]} ({c['J']})" for c in d.con))
    c_emp, rho_a0 = EMP["c_crn"], EMP["rho_a0"]
    g1 = W.gamma_for(BANK, 0.3)
    S = [
        (D0, scen("N1 central, rho 0, no CRN", 2.65, 0.0, rho=0.0)),
        (D0, scen("N2 CRN only", 2.65, c_emp, sd_s=0.0)),
        (D0, scen("N4 wave-0a (rho 0.76, CRN 0.65)", 2.65, c_emp, rho=rho_a0)),
        (D0, scen("N6 high 3.85, rho 0", 3.85, 0.0, rho=0.0)),
        (D0, scen("N8 cut 4.5 at wave-0a rho", 4.5 / math.sqrt(2 * (1 - rho_a0)), c_emp, rho=rho_a0)),
        (D0, scen("H1 N1 + A1 x2", 2.65, 0.0, rho=0.0, mults={"A1": 2.0})),
        (D0, scen("H2 N1 + A1 x3", 2.65, 0.0, rho=0.0, mults={"A1": 3.0})),
        (D0, scen("H3 N4 + A1 x2", 2.65, c_emp, rho=rho_a0, mults={"A1": 2.0})),
        (D0, scen("H4 N4 + S1 x2", 2.65, c_emp, rho=rho_a0, mults={"S1": 2.0})),
        (D0, scen("H5 N4 + S1, S3, S4 x2 (add arms noisier)", 2.65, c_emp, rho=rho_a0, mults={"S1": 2.0, "S3": 2.0, "S4": 2.0})),
        (D0, scen("H6 N4 + R x2 (shared comparator)", 2.65, c_emp, rho=rho_a0, mults={"R": 2.0})),
        (D0, scen("H7 N1 + A1 x2 and S1 x2 (two noisy arms)", 2.65, 0.0, rho=0.0, mults={"A1": 2.0, "S1": 2.0})),
        (D0, scen("G1 N4 + arm x prompt 0.3 pp^2 (CRN 0.85)", 2.65, 0.85, rho=rho_a0, gamma=g1)),
        (D0, scen("G2 N4 + arm x prompt logit SD 0.5", 2.65, c_emp, rho=rho_a0, gamma=0.5)),
        (D0, scen("X1 N4, A1 loads against the shared shift", 2.65, c_emp, rho=rho_a0, neg_arm="A1")),
        (D1, scen("N1 central, rho 0, no CRN", 2.65, 0.0, rho=0.0)),
        (D1, scen("N4 wave-0a (rho 0.76, CRN 0.65)", 2.65, c_emp, rho=rho_a0)),
        (D1, scen("N8 cut 4.5 at wave-0a rho", 4.5 / math.sqrt(2 * (1 - rho_a0)), c_emp, rho=rho_a0)),
        (D1, scen("H4 N4 + S1 x2", 2.65, c_emp, rho=rho_a0, mults={"S1": 2.0})),
    ]
    results = dict(methods=METHOD_TEXT, designs={d.name: dict(df_pool=d.df_pool, df_b2=d.df_b2, h_arm=d.h_arm.tolist(),
                   kappa=d.kappa, common={c["name"]: c["J"] for c in d.con}) for d in (D0, D1)}, scenarios=[])
    for i, (d, sc) in enumerate(S):
        t1 = time.time()
        store, ths = run_null(d, sc, args.reps, args.batch, 20261017 + 7919 * i)
        nm = null_metrics(store)
        cv = {c: curves(store, [x[0] for x in CONTRASTS].index(c)) for c in ("P1", "P4", "P5")}
        tag = d.name.split()[0]
        say("")
        say(f"--- [{tag}] {sc['name']}: shared {sc['sd_s_pp']:.2f} pp, arm-specific {np.round(sc['sd_t_pp'], 2).tolist()}, "
            f"CRN {sc['c']:.2f}, gamma {sc['gamma']:.2f}  [{time.time() - t1:.0f} s]")
        say(f"    REML arm variances, median over replicates (pp^2): " + ", ".join(
            f"{a} {v:.2f}" for a, v in zip(ARMS, np.median(ths, 0))) + f"; share at floor {float((ths <= 1.0001e-2).mean()):.3f}")
        say("    method | FWER | worst single a/6 | false 'worse' | SE/SD P1 P4 | med df P1 P4 (p10) | MDE80 P1 P4 P5 | "
            "power5 P1 | better5 P1 | better80 P1 | P(eq|0) pc P1 P4 | fw P1 P4 | delta80 P1 P4")
        rec = dict(design=tag, name=sc["name"], comp=dict(sd_s=sc["sd_s_pp"], sd_t=sc["sd_t_pp"], c=sc["c"], gamma=sc["gamma"]),
                   null=nm, curves=cv, reml_median=np.median(ths, 0).tolist())
        for m in METHODS:
            z = nm[m]
            say(f"    {m:>3} | {z['fwer'] * 100:.2f} | {max(z['rej_a6']) * 100:.2f} | {z['worse_any'] * 100:.2f} | "
                f"{z['rms_se'][0] / z['sd_est'][0]:.2f} {z['rms_se'][3] / z['sd_est'][3]:.2f} | "
                f"{z['med_df'][0]:.1f} {z['med_df'][3]:.1f} ({z['p10_df'][0]:.1f} {z['p10_df'][3]:.1f}) | "
                f"{cv['P1'][m]['mde80']:.2f} {cv['P4'][m]['mde80']:.2f} {cv['P5'][m]['mde80']:.2f} | "
                f"{cv['P1'][m]['power5']:.2f} | {cv['P1'][m]['better5']:.2f} | {cv['P1'][m]['better80']:.2f} | "
                f"{cv['P1'][m]['equiv0_pc']:.2f} {cv['P4'][m]['equiv0_pc']:.2f} | {cv['P1'][m]['equiv0_fw']:.2f} "
                f"{cv['P4'][m]['equiv0_fw']:.2f} | {cv['P1'][m]['delta80']:.2f} {cv['P4'][m]['delta80']:.2f}")
        if sc["mults"] or sc["neg_arm"] or sc["gamma"] > 0:
            say("    per-contrast rejection at two-sided a/6 (P1..P6), %: " + "; ".join(
                f"{m} " + " ".join(f"{x * 100:.2f}" for x in nm[m]["rej_a6"]) for m in ("a", "b", "b2x", "b3", "HB")))
        results["scenarios"].append(rec)
    say("")
    say("--- direct answer-level power at a true 5 pp effect (checks the shift method; Holm, others null)")
    nd = max(args.reps // 2, 500)
    for j, (d, k, which) in enumerate(((D0, 0, "P1"), (D0, 2, "P1"), (D0, 2, "P4"))):
        pw, lam = direct_power(d, S[k][1], nd, args.batch, 4242 + j, which)
        ref = results["scenarios"][k]["curves"][which]
        say(f"    {S[k][1]['name']} {which}: realized {lam:.2f} pp; direct " + ", ".join(f"{m} {pw[m]:.3f}" for m in METHODS)
            + " | shift " + ", ".join(f"{m} {ref[m]['power5']:.3f}" for m in METHODS))
        results.setdefault("direct", []).append(dict(scenario=S[k][1]["name"], which=which, lam=lam, direct=pw))
    say(f"total {time.time() - t0:.0f} s")
    (HERE / "stage1_model_sim_results.json").write_text(json.dumps(results, indent=1, default=float))
    (HERE / "stage1_model_sim_out.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
