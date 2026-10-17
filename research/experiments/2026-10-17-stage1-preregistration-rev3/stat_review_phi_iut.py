#!/usr/bin/env python3
"""stat_review_phi_iut.py: statistics review check of the testing family Phi as revision 3 puts it in force.

Phi (rev3 sections 4.2-4.3): 24 nodes, gamma 0.1, start weights U 0.15, O and L 0.1/12, F 0; edges U->F 1/2,
U->O 1/8, U->L 1/8, U->U_j 1/20; F->L 1 (the R1.3 row); O->L 1/2, O->U 1/2; L->O 1/2, L->U 1/2.
O_k and L_k are intersection-union (IUT) nodes: p = max(p_comparator_part, p_theta0_or_a0_part).
F_k uses the same estimate as O_k's theta0 part: p_F = 1 - p_theta0_part (exact complement).

Checks:
 1. exact-fraction graph checks (weights, row sums) for the R1.3 edge and the plan-B graph of LN-21;
 2. brute-force closed test (weighted Bonferroni local tests) against the shortcut on a reduced 2-contrast copy
    (8 nodes) with the R1.3 edge, on random p-vectors;
 3. z-level Monte Carlo family-wise error under named and random true/false configurations, including the
    IUT least-favourable ones (one part at its boundary, the other far into its alternative);
 4. counts of co-rejections that the text says are impossible (F_k with O_k), and of the implications
    "O_k rejected => per-comparison infeasible at 5 pp" and "F_k rejected => per-comparison feasible".
No data input. No record, row, prompt or answer is read. Planning check only (I/M labels in the review).
Run: PYTHONDONTWRITEBYTECODE=1 python3 -B stat_review_phi_iut.py   (numpy only)
"""
import itertools, json, math, pathlib, sys, time
from fractions import Fraction as Fr
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
OUT = []
RES = {}


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


# ----------------------------------------------------------------------------- graph
def graph(K=6, r13=True, uu_total=Fr(1, 4), gamma=Fr(1, 10)):
    """Node order: U_0..U_{K-1}, O_0.., L_0.., F_0..  (exact fractions)."""
    n = 4 * K
    U = lambda k: k
    O = lambda k: K + k
    L = lambda k: 2 * K + k
    F = lambda k: 3 * K + k
    w = [Fr(0)] * n
    G = [[Fr(0)] * n for _ in range(n)]
    for k in range(K):
        w[U(k)] = (1 - gamma) / K
        w[O(k)] = gamma / (2 * K)
        w[L(k)] = gamma / (2 * K)
        G[U(k)][F(k)] = Fr(1, 2)
        G[U(k)][O(k)] = Fr(1, 8)
        G[U(k)][L(k)] = Fr(1, 8)
        for j in range(K):
            if j != k:
                G[U(k)][U(j)] = uu_total / (K - 1)
        if r13:
            G[F(k)][L(k)] = Fr(1)
        else:
            G[F(k)][O(k)] = Fr(1, 2)
            G[F(k)][L(k)] = Fr(1, 2)
        G[O(k)][L(k)] = Fr(1, 2)
        G[O(k)][U(k)] = Fr(1, 2)
        G[L(k)][O(k)] = Fr(1, 2)
        G[L(k)][U(k)] = Fr(1, 2)
    return w, G


def to_np(w, G):
    return np.array([float(x) for x in w]), np.array([[float(x) for x in r] for r in G])


def update_scalar(w, G, i, active):
    """Bretz, Maurer, Brannath and Posch (2009), Algorithm 1, removal of node i (float arrays)."""
    act = active.copy()
    act[i] = False
    w2 = w.copy()
    w2[act] += w[i] * G[i, act]
    w2[i] = 0.0
    den = 1.0 - G[:, i] * G[i, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        Gn = (G + np.outer(G[:, i], G[i, :])) / den[:, None]
    Gn[den <= 1e-12, :] = 0.0
    Gn[~act, :] = 0.0
    Gn[:, ~act] = 0.0
    np.fill_diagonal(Gn, 0.0)
    return w2, Gn


def shortcut_scalar(p, w0, G0, alpha=0.05):
    w, G = w0.copy(), G0.copy()
    active = np.ones(len(p), bool)
    rej = np.zeros(len(p), bool)
    while True:
        cand = [j for j in range(len(p)) if active[j] and p[j] <= alpha * w[j] * (1 + 1e-12)]
        if not cand:
            return rej
        i = cand[-1]                      # last candidate: the result must not depend on the order
        w, G = update_scalar(w, G, i, active)
        active[i] = False
        rej[i] = True


def shortcut_batch(P, w0, G0, alpha=0.05):
    """Vectorized sequentially rejective graphical procedure over replicates (rows of P)."""
    B, n = P.shape
    w = np.repeat(w0[None], B, 0)
    G = np.repeat(G0[None], B, 0)
    active = np.ones((B, n), bool)
    rej = np.zeros((B, n), bool)
    eye = np.eye(n, dtype=bool)
    for _ in range(n):
        cand = active & (P <= alpha * w * (1 + 1e-12))
        has = cand.any(1)
        if not has.any():
            break
        idx = np.where(has)[0]
        j = cand[idx].argmax(1)
        ar = np.arange(len(idx))
        Gi, wi = G[idx], w[idx]
        act = active[idx].copy()
        act[ar, j] = False
        row_j = Gi[ar, j, :]
        col_j = Gi[ar, :, j]
        wj = wi[ar, j]
        wi = wi + wj[:, None] * row_j * act
        wi[ar, j] = 0.0
        den = 1.0 - col_j * row_j
        safe = den > 1e-12
        num = Gi + col_j[:, :, None] * row_j[:, None, :]
        Gn = np.where(safe[:, :, None], num / np.where(safe, den, 1.0)[:, :, None], 0.0)
        Gn = Gn * (act[:, :, None] & act[:, None, :])
        Gn[:, eye] = 0.0
        G[idx], w[idx], active[idx] = Gn, wi, act
        rej[idx, j] = True
    return rej


# ----------------------------------------------------------------------------- 1. exact checks
def exact_checks():
    say("=" * 100)
    say("1. Exact graph checks")
    for name, (w, G) in (("Phi, R1.3 edge (K=6)", graph(6, True)), ("Phi, standard edge (K=6)", graph(6, False)),
                         ("plan-B Phi (LN-21, K=3, U-to-U 1/8 each)", graph(3, True))):
        ws = sum(w)
        rs = sorted({sum(r) for r in G})
        say(f"   {name}: weights sum {ws}; row sums {rs}")
        RES.setdefault("exact", {})[name] = dict(weights_sum=str(ws), row_sums=[str(x) for x in rs])
    # local levels used in the review (one contrast, the others untouched)
    w0, G0 = to_np(*graph(6, True))
    K = 6
    seqs = {"start": [], "after U": [0], "after U,F": [0, 3 * K], "after U,L": [0, 2 * K],
            "after U,O": [0, K], "after U,F,L": [0, 3 * K, 2 * K]}
    lev = {}
    for nm, seq in seqs.items():
        w, G = w0.copy(), G0.copy()
        act = np.ones(4 * K, bool)
        for i in seq:
            w, G = update_scalar(w, G, i, act)
            act[i] = False
        lev[nm] = {"U1": w[0] * 5, "O1": w[K] * 5, "L1": w[2 * K] * 5, "F1": w[3 * K] * 5}
        say(f"   levels (% , one contrast) {nm:>12}: " + ", ".join(f"{k} {v:.4f}%" for k, v in lev[nm].items()))
    RES["levels_pct"] = lev


# ----------------------------------------------------------------------------- 2. closed test on 8 nodes
def closed_test_check(n_cases=3000):
    say("=" * 100)
    say("2. Brute-force closed test vs shortcut, reduced copy (K=2, 8 nodes), R1.3 edge")
    w2, G2 = to_np(*graph(2, True, uu_total=Fr(1, 4)))
    n = 8
    cache = {}
    for r in range(1, n + 1):
        for I in itertools.combinations(range(n), r):
            w, G = w2.copy(), G2.copy()
            act = np.ones(n, bool)
            for j in range(n):
                if j not in I:
                    w, G = update_scalar(w, G, j, act)
                    act[j] = False
            cache[I] = w
    mono = 0
    for I, wI in cache.items():
        if len(I) > 1:
            for j in I:
                J = tuple(x for x in I if x != j)
                if any(cache[J][x] + 1e-12 < wI[x] for x in J):
                    mono += 1
    sums_ok = all(cache[I].sum() <= 1 + 1e-12 for I in cache)
    rng = np.random.default_rng(20261017)
    bad = 0
    for _ in range(n_cases):
        p = rng.uniform(0, 1, n) ** rng.uniform(1, 6)
        p[rng.random(n) < 0.3] = rng.uniform(0, 0.03)
        a = shortcut_scalar(p, w2, G2)
        rejI = {I: any(p[j] <= 0.05 * cache[I][j] * (1 + 1e-12) for j in I) for I in cache}
        b = np.array([all(rejI[I] for I in rejI if j in I) for j in range(n)])
        bad += int(not np.array_equal(a, b))
    say(f"   intersection weights sum <= 1: {sums_ok}; monotonicity violations {mono}; "
        f"shortcut != closed test in {bad} of {n_cases} random p-vectors")
    # batch routine == scalar routine on the full 24-node graph
    w0, G0 = to_np(*graph(6, True))
    P = rng.uniform(0, 1, (3000, 24)) ** rng.uniform(1, 8, (3000, 1))
    P[rng.random((3000, 24)) < 0.2] = 1e-5
    rb = shortcut_batch(P, w0, G0)
    rs = np.array([shortcut_scalar(p, w0, G0) for p in P])
    say(f"   batch shortcut == scalar shortcut on 24 nodes: {np.array_equal(rb, rs)} (3000 random p-vectors)")
    RES["closed_test"] = dict(mismatch=bad, cases=n_cases, monotonicity_violations=mono, batch_equals_scalar=bool(np.array_equal(rb, rs)))


# ----------------------------------------------------------------------------- 3. Monte Carlo
K = 6
# statistic layout (30): U_k, Oc_k, Ot_k, Lc_k, La_k for k = 0..5; index helpers
SU, SOC, SOT, SLC, SLA = 0, 6, 12, 18, 24
P4 = 3            # contrast index of P4 (comparator a0): L's comparator part = L's a0 part shifted by tau_L/SE
TAU_L_SE = 4.9    # tau_L is about 4.9 SE of a 6-against-6 contrast (rev3 section 6.7)


def corr_matrix(kind):
    C = np.eye(30)
    if kind == "independent":
        return C
    s = 1.0 if kind == "base" else 1.4

    def setc(a, b, v):
        C[a, b] = C[b, a] = max(-0.95, min(0.95, v * s))
    # shared comparators: P1-P3 share R; P5, P6 share S1; P4 (a0 - S1) against P5/P6 (S1 - S3/S4)
    for base in (SU, SOC, SLC):
        for a, b in itertools.combinations(range(3), 2):
            setc(base + a, base + b, 0.5)
        setc(base + 4, base + 5, 0.5)
        setc(base + 3, base + 4, -0.5)
        setc(base + 3, base + 5, -0.5)
    for a, b in itertools.combinations(range(K), 2):   # theta0 and a0 parts share theta0 / a0
        setc(SOT + a, SOT + b, 0.3)
        setc(SLA + a, SLA + b, 0.3)
    for k in range(K):
        idx = [SU + k, SOC + k, SOT + k, SLC + k, SLA + k]
        for a, b in itertools.combinations(idx, 2):
            setc(a, b, 0.3)
        setc(SOC + k, SOT + k, 0.6)                   # same repair arm m in both parts
        setc(SLC + k, SLA + k, 0.6)
    ev = np.linalg.eigvalsh(C)
    if ev.min() <= 0.05:
        lam = 0.0
        while np.linalg.eigvalsh((1 - lam) * C + lam * np.eye(30)).min() <= 0.05:
            lam += 0.02
        C = (1 - lam) * C + lam * np.eye(30)
    return C


def nsf(x):
    return 0.5 * np.vectorize(math.erfc)(x / math.sqrt(2.0))


def pvalues(z):
    """z columns: U two-sided; Oc, Ot, Lc, La one-sided adverse (positive = adverse)."""
    B = z.shape[0]
    zu, zoc, zot, zlc, zla = (z[:, b:b + K] for b in (SU, SOC, SOT, SLC, SLA))
    zlc = zlc.copy()
    zlc[:, P4] = zla[:, P4] + TAU_L_SE              # P4: comparator a0, so both L parts use one estimate
    pu = 2 * nsf(np.abs(zu))
    poc, pot = nsf(zoc), nsf(zot)
    plc, pla = nsf(zlc), nsf(zla)
    po = np.maximum(poc, pot)
    pl = np.maximum(plc, pla)
    pf = 1.0 - pot                                  # F: null O(m) - O(theta0) >= 5; same estimate and SE
    P = np.concatenate([pu, po, pl, pf], 1)
    return P, pot, pf, zu


def truth(mu):
    mu_u, mu_oc, mu_ot, mu_lc, mu_la = (mu[b:b + K] for b in (SU, SOC, SOT, SLC, SLA))
    mu_lc = mu_lc.copy()
    mu_lc[P4] = mu_la[P4] + TAU_L_SE
    tu = mu_u == 0
    to = (mu_oc <= 0) | (mu_ot <= 0)
    tl = (mu_lc <= 0) | (mu_la <= 0)
    tf = mu_ot >= 0
    return np.concatenate([tu, to, tl, tf])


def run(mu, C, reps, seed, w0, G0, batch=20000):
    Lc = np.linalg.cholesky(C)
    rng = np.random.default_rng(seed)
    tn = truth(mu)
    fw = 0
    n_fo = n_o_not_inf = n_f_not_fea = n_wrong_sign = 0
    done = 0
    while done < reps:
        b = min(batch, reps - done)
        z = rng.standard_normal((b, 30)) @ Lc.T + mu[None, :]
        P, pot, pf, zu = pvalues(z)
        rej = shortcut_batch(P, w0, G0)
        fw += int((rej & tn[None, :]).any(1).sum())
        ro, rf = rej[:, K:2 * K], rej[:, 3 * K:]
        n_fo += int((ro & rf).any(1).sum())
        n_o_not_inf += int((ro & (pot > 0.05)).sum())
        n_f_not_fea += int((rf & (pf > 0.05)).sum())
        mu_u = mu[SU:SU + K]
        ru = rej[:, :K]
        n_wrong_sign += int((ru & (np.sign(zu) != np.sign(mu_u)[None, :]) & (mu_u[None, :] != 0)).any(1).sum())
        done += b
    return dict(fwer=fw / reps, mcse=math.sqrt(max(fw / reps, 1e-9) * (1 - fw / reps) / reps), co_FO=n_fo,
                O_rej_not_infeasible=n_o_not_inf, F_rej_not_feasible=n_f_not_fea, n_true=int(tn.sum()))


def mu_of(U, OC, OT, LC, LA):
    f = lambda v: np.full(K, v, float) if np.isscalar(v) else np.asarray(v, float)
    return np.concatenate([f(U), f(OC), f(OT), f(LC), f(LA)])


def montecarlo(reps_named=100000, n_random=300, reps_random=4000, reps_top=100000):
    say("=" * 100)
    say("3. Monte Carlo family-wise error, in-force Phi (R1.3 edge, IUT O and L nodes); z-level, correlated")
    w0, G0 = to_np(*graph(6, True))
    big = 8.0
    named = [
        ("G0 global: U null; O, L both parts at boundary; F at boundary", mu_of(0, 0, 0, 0, 0)),
        ("G1 U false; O, L comparator part at boundary, other part false (IUT least favourable)", mu_of(6, 0, big, 0, big)),
        ("G2 U false; O theta0 part and L a0 part at boundary, comparator parts false; F at boundary", mu_of(6, big, 0, big, 0)),
        ("G3 U false; F false (feasible arms); L comparator part at boundary (F->L 1 feeds L)", mu_of(6, 0, -big, 0, big)),
        ("G4 U false; F false; L a0 part at boundary", mu_of(6, 0, -big, big, 0)),
        ("G5 U and F false (feasible arms; O true deep); L false except L_1 at its comparator boundary",
         mu_of(6, 0, -big, [0, big, big, big, big, big], big)),
        ("G6 all false except O_1 (comparator part at boundary); other O false, their F true",
         mu_of(6, [0, big, big, big, big, big], big, big, big)),
        ("G7 U null; F false; O and L at boundary", mu_of(0, 0, -big, 0, 0)),
        ("G8 half U false; O_k false where U false, F_k false elsewhere; L at boundary",
         mu_of([6, 6, 6, 0, 0, 0], [big] * 3 + [0] * 3, [big] * 3 + [-big] * 3, 0, 0)),
    ]
    RES["mc_named"] = {}
    for ck in ("independent", "base", "strong"):
        C = corr_matrix(ck)
        say(f"   correlation set '{ck}': min eigenvalue {np.linalg.eigvalsh(C).min():.3f}")
        for i, (nm, mu) in enumerate(named):
            r = run(mu, C, reps_named, 7000 + 31 * i + {"independent": 0, "base": 1, "strong": 2}[ck], w0, G0)
            say(f"      {nm}: FWER {r['fwer'] * 100:.3f}% (MC SE {r['mcse'] * 100:.3f}; true nulls {r['n_true']}); "
                f"F&O co-rejections {r['co_FO']}; O rejected but not per-comparison infeasible {r['O_rej_not_infeasible']}; "
                f"F rejected but not per-comparison feasible {r['F_rej_not_feasible']}")
            RES["mc_named"][f"{ck} | {nm}"] = r
    # random search over configurations
    say("   random search over configurations (base correlations): " f"{n_random} configs x {reps_random} reps, top 5 re-run at {reps_top}")
    C = corr_matrix("base")
    rng = np.random.default_rng(99)
    o_states = [(0, 0), (0, big), (big, 0), (big, big), (-big, -big), (big, -big), (0, -big), (2, 2), (big, 1.5), (1.5, big)]
    l_states = [(0, 0), (0, big), (big, 0), (big, big), (-big, -big), (2, 2), (big, 1.5), (1.5, big)]
    u_states = [0, 0, 2.5, 6]
    found = []
    for t in range(n_random):
        U = [u_states[rng.integers(len(u_states))] for _ in range(K)]
        OS = [o_states[rng.integers(len(o_states))] for _ in range(K)]
        LS = [l_states[rng.integers(len(l_states))] for _ in range(K)]
        mu = mu_of(U, [a for a, _ in OS], [b for _, b in OS], [a for a, _ in LS], [b for _, b in LS])
        if not truth(mu).any():
            continue
        r = run(mu, C, reps_random, 50000 + t, w0, G0, batch=reps_random)
        found.append((r["fwer"], t, mu, r))
    found.sort(key=lambda x: -x[0])
    say(f"   random search: max FWER {found[0][0] * 100:.2f}% (4,000 reps, MC SE about 0.34); median {np.median([f[0] for f in found]) * 100:.2f}%; "
        f"co-rejections F&O in all configs {sum(f[3]['co_FO'] for f in found)}; O-not-infeasible {sum(f[3]['O_rej_not_infeasible'] for f in found)}; "
        f"F-not-feasible {sum(f[3]['F_rej_not_feasible'] for f in found)}")
    top = []
    for rank, (fv, t, mu, _) in enumerate(found[:5]):
        r = run(mu, C, reps_top, 90000 + t, w0, G0)
        top.append(dict(config=t, fwer_search=fv, fwer_rerun=r["fwer"], mcse=r["mcse"], mu=mu.tolist()))
        say(f"      top {rank + 1} (config {t}): search {fv * 100:.2f}% -> re-run {r['fwer'] * 100:.3f}% (MC SE {r['mcse'] * 100:.3f})")
    RES["mc_random"] = dict(n=len(found), max_search=found[0][0], top=top)


def main():
    t0 = time.time()
    say("stat_review_phi_iut.py; numpy", np.__version__, "; python", sys.version.split()[0])
    exact_checks()
    closed_test_check()
    montecarlo()
    say(f"total {time.time() - t0:.0f} s")
    (HERE / "stat_review_phi_iut_out.txt").write_text("\n".join(OUT) + "\n")
    (HERE / "stat_review_phi_iut_results.json").write_text(json.dumps(RES, indent=1, default=float))


if __name__ == "__main__":
    main()
