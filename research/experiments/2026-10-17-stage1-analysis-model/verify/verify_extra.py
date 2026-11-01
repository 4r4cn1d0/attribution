#!/usr/bin/env python3
"""verify_extra.py: independent checks for verify-report.md (adversarial verification of stage1-analysis-model-DRAFT.md).

Planning simulation only. It reads no evaluation record. It imports the draft's own simulator from verify/rerun/
(a byte copy of stage1_model_sim.py, sim_w2.py and sim_w2_results.json; SHA-256 checked below) and never edits it.
It opens no selector.jsonl, hidden/, held-out file, wave-0b rows.jsonl or groups.json. No prompt, answer or id is printed.

Parts:
  A. Answer-level, the draft's simulator at FRESH seeds: (A1) the pre-Gate-B "low" scenario of PREREG section 2
     (rho 0.67, no CRN), to compare HB with Welch (aW) without any wave-0a value; (A2) per-contrast rejection at the
     levels a single contrast can reach under Holm or the graph (5%, 1%, 0.75%, a/6), the strong-control check for
     partial nulls, in the draft's worst scenarios; (A3) the same FWER / worst-single numbers at fresh seeds.
  B. Seed-level (cell) simulation of HB's seed part under a seed structure that the additive model does not hold:
     a component shared by a SUBSET of arms (clusters). HB0 (no prompt term) is the right comparison here.
  C. The graph Phi: (C1) shortcut = closed test on a reduced 8-node copy (brute force over all 255 intersections);
     (C2) FWER under correlated statistics and partial nulls (24 nodes); (C3) directional (wrong-sign) errors.
  D. Arithmetic for the outcome-dependence record (seen stage-1 cells; the expected shift HB vs S-a).
Run: PYTHONDONTWRITEBYTECODE=1 <venv python> -B verify_extra.py [--reps N]
Writes verify_extra_out.txt and verify_extra_results.json beside this file.
"""
import argparse, hashlib, importlib.util, itertools, json, math, pathlib, sys, time
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
RERUN = HERE / "rerun"
EXPECT = {"stage1_model_sim.py": "581e9bd18de79336", "sim_w2.py": "9f7c4ab924af7cb2",
          "sim_w2_results.json": "5b3a85bed3ab90fb", "stage1_numbers.py": "2c8f432b7be70ab5"}
for fn, pre in EXPECT.items():
    h = hashlib.sha256((RERUN / fn).read_bytes()).hexdigest()
    if not h.startswith(pre):
        raise SystemExit(f"hash mismatch {fn}: {h[:16]} != {pre}")

spec = importlib.util.spec_from_file_location("s1m", RERUN / "stage1_model_sim.py")
S1M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S1M)
W = S1M.W
OUT, RES = [], {}


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


ARMS, CON = S1M.ARMS, S1M.CONTRASTS
LEVELS = [0.05, 0.01, 0.0075, 0.05 / 6]


# ------------------------------------------------------------------------------------------------ Part A
def part_a(reps):
    say("=" * 100)
    say("PART A: answer-level, the draft's simulator, fresh seeds")
    c_emp, rho_a0 = S1M.EMP["c_crn"], S1M.EMP["rho_a0"]
    rho_low = 1 - 2.15 ** 2 / (2 * 2.65 ** 2)
    say(f"PREREG section 2 'low' scenario: sigma_pair 2.15 at per-arm 2.65 -> rho {rho_low:.4f}")
    scen = S1M.scen
    S = [
        ("PL", S1M.D0, scen("PL PREREG low (shared shift takes all non-sampling variance, no CRN)", 2.65, 0.0,
                            sd_s=math.sqrt(2.65 ** 2 - S1M.V_SAMP - 0.01))),
        ("N1", S1M.D0, scen("N1 central, rho 0, no CRN", 2.65, 0.0, rho=0.0)),
        ("N4", S1M.D0, scen("N4 wave-0a (rho 0.76, CRN 0.65)", 2.65, c_emp, rho=rho_a0)),
        ("H2", S1M.D0, scen("H2 N1 + A1 x3", 2.65, 0.0, rho=0.0, mults={"A1": 3.0})),
        ("H3", S1M.D0, scen("H3 N4 + A1 x2", 2.65, c_emp, rho=rho_a0, mults={"A1": 2.0})),
        ("X1", S1M.D0, scen("X1 N4, A1 loads against the shared shift", 2.65, c_emp, rho=rho_a0, neg_arm="A1")),
        ("D1H4", S1M.D1, scen("H4 N4 + S1 x2", 2.65, c_emp, rho=rho_a0, mults={"S1": 2.0})),
        ("G2", S1M.D0, scen("G2 N4 + arm x prompt logit SD 0.5", 2.65, c_emp, rho=rho_a0, gamma=0.5)),
    ]
    out = {}
    for i, (tag, d, sc) in enumerate(S):
        t0 = time.time()
        store, _ = S1M.run_null(d, sc, reps, 200, 99001 + 131 * i)
        nm = S1M.null_metrics(store)
        cv = {c: S1M.curves(store, [x[0] for x in CON].index(c)) for c in ("P1", "P4", "P5")}
        rec = dict(name=sc["name"], design=d.name.split()[0], sd_pair_nominal=sc["sd_pair_nominal"], methods={})
        say(f"--- [{tag}] {sc['name']} ({d.name.split()[0]}); nominal pair SD {sc['sd_pair_nominal']:.2f} pp [{time.time() - t0:.0f} s]")
        for m in ("a", "aW", "b", "b2x", "b3", "HB", "HB0"):
            est, se, df = store[m]
            p = W.t_p2(est / se, df)
            per = {f"{lv:.5f}": (p < lv).mean(0).tolist() for lv in LEVELS}
            rec["methods"][m] = dict(fwer=nm[m]["fwer"], worst_a6=max(nm[m]["rej_a6"]), worse_any=nm[m]["worse_any"],
                                     per_contrast=per, mde80=[cv[c][m]["mde80"] for c in ("P1", "P4", "P5")],
                                     eq0_pc=[cv[c][m]["equiv0_pc"] for c in ("P1", "P4")])
            say(f"   {m:>4}: FWER {nm[m]['fwer'] * 100:.2f}% | worst a/6 {max(nm[m]['rej_a6']) * 100:.2f}% | "
                f"per-contrast at 5% (P1..P6) " + " ".join(f"{x * 100:.2f}" for x in per["0.05000"]) +
                f" | at 1% " + " ".join(f"{x * 100:.2f}" for x in per["0.01000"]) +
                f" | MDE80 P1/P4/P5 " + "/".join(f"{cv[c][m]['mde80']:.2f}" for c in ("P1", "P4", "P5")))
        out[tag] = rec
    RES["A"] = out


# ------------------------------------------------------------------------------------------------ Part B
def hb0_cells(d, U):
    """HB's seed part only (HB0) on cell values U (B, nc); also (b0) paired t on common seeds and (aW)."""
    th, vth = S1M.reml_hetero(d, U)
    B = U.shape[0]
    res = {m: [np.zeros((B, 6)), np.zeros((B, 6)), np.zeros((B, 6))] for m in ("HB0", "b0", "aW")}
    means = np.stack([U[:, ix].mean(1) for ix in d.arm_cells], 1)
    vars_ = np.stack([U[:, ix].var(1, ddof=1) for ix in d.arm_cells], 1)
    for ci, c in enumerate(d.con):
        a, b, J = c["a"], c["b"], c["J"]
        dd = U[:, c["ia"]] - U[:, c["ib"]]
        est = dd.mean(1)
        vs = (th[:, a] + th[:, b]) / J
        var_vs = (vth[:, a, a] + vth[:, b, b] + 2 * vth[:, a, b]) / J ** 2
        res["HB0"][0][:, ci], res["HB0"][1][:, ci] = est, np.sqrt(vs)
        res["HB0"][2][:, ci] = 2 * vs ** 2 / np.maximum(var_vs, 1e-300)
        res["b0"][0][:, ci], res["b0"][1][:, ci], res["b0"][2][:, ci] = est, dd.std(1, ddof=1) / math.sqrt(J), J - 1
        va, vb = vars_[:, a] / d.n_arm[a], vars_[:, b] / d.n_arm[b]
        res["aW"][0][:, ci] = means[:, a] - means[:, b]
        res["aW"][1][:, ci] = np.sqrt(va + vb)
        res["aW"][2][:, ci] = (va + vb) ** 2 / (va ** 2 / (d.n_arm[a] - 1) + vb ** 2 / (d.n_arm[b] - 1))
    return res


def part_b(reps):
    say("=" * 100)
    say("PART B: seed-level simulation, cluster structures the additive seed model does not hold (HB0 = HB seed part)")
    d = S1M.D0
    v = 2.65 ** 2
    # each scenario: shared shift share, {cluster members: share}; arm-specific = rest; per-arm total var = 2.65^2
    SC = [
        ("B0 additive, rho 0.5 (control)", 0.5, []),
        ("B1 A1, L1, H1 share 0.3 (R does not)", 0.3, [({"A1", "L1", "H1"}, 0.3)]),
        ("B2 A1, L1 share 0.4 (overlapping selections)", 0.3, [({"A1", "L1"}, 0.4)]),
        ("B3 S3, S4 share 0.4 (S1 does not)", 0.3, [({"S3", "S4"}, 0.4)]),
        ("B4 two clusters: a0 S1 S3 S4 | R A1 L1 H1, 0.4 each", 0.3, [({"a0", "S1", "S3", "S4"}, 0.4), ({"R", "A1", "L1", "H1"}, 0.4)]),
        ("B5 S1, S3, S4 share 0.4 (a0 does not)", 0.3, [({"S1", "S3", "S4"}, 0.4)]),
    ]
    out = {}
    for i, (name, s_share, clusters) in enumerate(SC):
        rng = np.random.default_rng(55501 + 17 * i)
        acc = {m: [[], [], []] for m in ("HB0", "b0", "aW")}
        done = 0
        while done < reps:
            B = min(500, reps - done)
            s = rng.standard_normal((B, len(d.seeds))) * math.sqrt(s_share * v)
            U = s[:, d.cell_seed].copy()
            used = np.zeros(len(ARMS))
            for members, share in clusters:
                cmp_ = rng.standard_normal((B, len(d.seeds))) * math.sqrt(share * v)
                mask = np.array([ARMS[a] in members for a in d.cell_arm])
                U[:, mask] += cmp_[:, d.cell_seed[mask]]
                for a in members:
                    used[ARMS.index(a)] += share
            t_sd = np.sqrt(np.maximum(1.0 - s_share - used, 0.0) * v)
            U += rng.standard_normal((B, d.nc)) * t_sd[d.cell_arm][None, :]
            r = hb0_cells(d, U)
            for m in acc:
                for k in range(3):
                    acc[m][k].append(r[m][k])
            done += B
        rec = {}
        say(f"--- {name}")
        for m in acc:
            est, se, df = [np.concatenate(x, 0) for x in acc[m]]
            p = W.t_p2(est / se, df)
            fw = float(W.holm(p).any(1).mean())
            per6 = (p < 0.05 / 6).mean(0)
            per5 = (p < 0.05).mean(0)
            true_sd = est.std(0)
            rms_se = np.sqrt((se ** 2).mean(0))
            rec[m] = dict(fwer=fw, per_a6=per6.tolist(), per_5=per5.tolist(), se_over_sd=(rms_se / true_sd).tolist())
            say(f"   {m:>4}: Holm FWER {fw * 100:.2f}% | per-contrast at a/6 (P1..P6) " + " ".join(f"{x * 100:.2f}" for x in per6)
                + " | at 5% " + " ".join(f"{x * 100:.1f}" for x in per5) + " | SE/SD " + " ".join(f"{x:.2f}" for x in rec[m]["se_over_sd"]))
        out[name] = rec
    RES["B"] = out


# ------------------------------------------------------------------------------------------------ Part C
def graph_spec(gamma=0.1, K=6):
    n = 4 * K
    w = np.zeros(n)
    w[:K] = (1 - gamma) / K
    w[K:3 * K] = gamma / (2 * K)
    G = np.zeros((n, n))
    for k in range(K):
        u, o, l, f = k, K + k, 2 * K + k, 3 * K + k
        G[u, f] = 0.5
        G[u, o] = G[u, l] = 0.125
        for j in range(K):
            if j != k:
                G[u, j] = 0.25 / (K - 1)
        G[f, o] = G[f, l] = 0.5
        G[o, l] = G[o, u] = 0.5
        G[l, o] = G[l, u] = 0.5
    return w, G


def update(w, G, i, active):
    """Bretz et al. (2009) Algorithm 1 update after removing node i (my own, vectorized implementation)."""
    act = active.copy(); act[i] = False
    w = w.copy()
    w[act] += w[i] * G[i, act]
    w[i] = 0.0
    den = 1.0 - G[:, i] * G[i, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        Gn = (G + np.outer(G[:, i], G[i, :])) / den[:, None]
    Gn[den <= 1e-12, :] = 0.0
    Gn[~act, :] = 0.0
    Gn[:, ~act] = 0.0
    np.fill_diagonal(Gn, 0.0)
    return w, Gn


def shortcut(p, w0, G0, alpha=0.05):
    w, G = w0.copy(), G0.copy()
    active = np.ones(len(p), bool)
    rej = np.zeros(len(p), bool)
    while True:
        cand = [j for j in range(len(p)) if active[j] and p[j] <= alpha * w[j]]
        if not cand:
            return rej
        i = cand[0]                                  # any order: the shortcut result must not depend on it
        w, G = update(w, G, i, active)
        active[i] = False
        rej[i] = True


def intersection_weights(I, w0, G0):
    """Weights of H_I: remove every node outside I by the update rule (Bretz et al. 2009)."""
    w, G = w0.copy(), G0.copy()
    active = np.ones(len(w0), bool)
    for j in range(len(w0)):
        if j not in I:
            w, G = update(w, G, j, active)
            active[j] = False
    return w


def closed_test(p, w0, G0, alpha=0.05, cache=None):
    n = len(p)
    rejI = {}
    for r in range(1, n + 1):
        for I in itertools.combinations(range(n), r):
            wI = cache[I]
            rejI[I] = any(p[j] <= alpha * wI[j] for j in I)
    return np.array([all(rejI[I] for I in rejI if j in I) for j in range(n)])


def part_c(reps):
    say("=" * 100)
    say("PART C: the graph Phi")
    # C1: reduced copy, K = 2 contrasts (8 nodes), brute-force closure
    w2, G2 = graph_spec(0.1, K=2)
    assert abs(w2.sum() - 1) < 1e-12 and np.allclose(G2.sum(1), 1)
    cache = {I: intersection_weights(I, w2, G2) for r in range(1, 9) for I in itertools.combinations(range(8), r)}
    mono_bad = 0
    for I, wI in cache.items():                       # consonance precondition: weights only grow as I shrinks
        for j in I:
            if len(I) > 1:
                J = tuple(x for x in I if x != j)
                if any(cache[J][x] + 1e-12 < wI[x] for x in J):
                    mono_bad += 1
    rng = np.random.default_rng(424242)
    bad, tested = 0, 0
    for _ in range(3000):
        p = rng.uniform(0, 1, 8) ** rng.uniform(1, 6)
        p[rng.random(8) < 0.3] = rng.uniform(0, 0.03, 1)[0]
        a = shortcut(p, w2, G2)
        b = closed_test(p, w2, G2, cache=cache)
        tested += 1
        bad += int(not np.array_equal(a, b))
    say(f"C1 reduced graph (8 nodes): weights sum {w2.sum():.3f}; rows sum 1; weight monotonicity violations {mono_bad}; "
        f"shortcut != closed test in {bad} of {tested} random p-vectors")
    RES["C1"] = dict(mismatch=bad, tested=tested, monotonicity_violations=mono_bad)

    # C2/C3: 24 nodes, correlated statistics
    w0, G0 = graph_spec(0.1, 6)
    K = 6
    # correlation: U1..U3 share R (+0.5); U5, U6 share S1 (+0.5); U4 = a0 - S1 vs U5 = S1 - S3 -> -0.5; U4 vs U6 -0.5
    C = np.eye(24)
    for a, b in itertools.combinations(range(3), 2):
        C[a, b] = C[b, a] = 0.5
    C[4, 5] = C[5, 4] = 0.5
    C[3, 4] = C[4, 3] = C[3, 5] = C[5, 3] = -0.5
    for k in range(K):                                # same-contrast U, O, L, F statistics correlated 0.3
        nodes = [k, K + k, 2 * K + k, 3 * K + k]
        for a, b in itertools.combinations(nodes, 2):
            C[a, b] = C[b, a] = 0.3
    ev = np.linalg.eigvalsh(C)
    Lc = np.linalg.cholesky(C)

    def norm_sf(x):
        return 0.5 * np.vectorize(math.erfc)(x / math.sqrt(2))

    def run(mu, true_null, nrep, seed, wrong_sign=None):
        r = np.random.default_rng(seed)
        z = r.standard_normal((nrep, 24)) @ Lc.T + mu[None, :]
        p = np.empty_like(z)
        p[:, :K] = 2 * norm_sf(np.abs(z[:, :K]))
        p[:, K:] = norm_sf(z[:, K:])
        fw = 0
        ws = 0
        for i in range(nrep):
            if not (p[i] <= 0.05).any():
                continue
            rej = shortcut(p[i], w0, G0)
            if (rej & true_null).any():
                fw += 1
            if wrong_sign is not None:
                # wrong_sign[k] = +1: true effect < 0, a claim with z > 0 is wrong; -1: the reverse
                bad = False
                for k in range(K):
                    if wrong_sign[k] != 0 and rej[k] and np.sign(z[i, k]) == wrong_sign[k]:
                        bad = True
                ws += int(bad)
        return fw / nrep, ws / nrep

    say(f"C2 correlation matrix: min eigenvalue {ev.min():.3f}")
    cfgs = []
    mu = np.zeros(24); tn = np.ones(24, bool)
    cfgs.append(("global null", mu.copy(), tn.copy()))
    mu = np.zeros(24); mu[:K] = 6.0; tn = np.ones(24, bool); tn[:K] = False
    cfgs.append(("all U false (6 SE); O, L, F true at the boundary", mu.copy(), tn.copy()))
    mu = np.zeros(24); mu[:5] = 6.0; mu[3 * K:3 * K + 5] = 4.0; tn = np.ones(24, bool); tn[:5] = False; tn[3 * K:3 * K + 5] = False
    cfgs.append(("U1-U5 false and F1-F5 false; U6, all O, L, F6 true", mu.copy(), tn.copy()))
    mu = np.zeros(24); mu[:K] = 6.0; mu[K:3 * K] = 6.0; tn = np.ones(24, bool); tn[:3 * K] = False
    cfgs.append(("U, O, L all false; F all true at the boundary", mu.copy(), tn.copy()))
    c2 = {}
    for j, (nm, mu, tn) in enumerate(cfgs):
        fw, _ = run(mu, tn, min(reps, 20000), 3100 + j)
        c2[nm] = fw
        say(f"   FWER [{nm}]: {fw * 100:.2f}% (MC SE {math.sqrt(fw * (1 - fw) / min(reps, 20000)) * 100:.2f})")
    RES["C2"] = c2
    # C3: wrong-sign claims for the U nodes
    say("C3 directional errors on U (a rejected U_k whose sign is opposite to the true effect)")
    c3 = {}
    tn = np.zeros(24, bool)
    for delta in (0.25, 0.5, 1.0):
        for nm, signs in (("P1-P3 slightly harmful (true -delta SE), P4-P6 large +6 SE", [-1, -1, -1, 6, 6, 6]),
                          ("all six slightly harmful (-delta SE)", [-1] * 6),
                          ("all six slightly helpful (+delta SE)", [1] * 6)):
            mu = np.zeros(24)
            ws_flags = []
            for k, s_ in enumerate(signs):
                if abs(s_) == 1:
                    mu[k] = s_ * delta
                    ws_flags.append(-s_)        # true effect sign s_; a claim with sign -s_ is wrong
                else:
                    mu[k] = s_
                    ws_flags.append(0)
            _, ws = run(mu, tn, min(reps, 10000), 5100 + int(delta * 100) + len(c3), wrong_sign=ws_flags)
            c3[f"{nm} | delta {delta}"] = ws
            say(f"   P(any wrong-sign U claim) [{nm}; delta {delta}]: {ws * 100:.2f}%")
    RES["C3"] = c3
    # how high can one U node's level go?  all other 23 nodes rejected
    p = np.zeros(24); p[0] = 0.049
    rej = shortcut(p, w0, G0)
    RES["C_max_U_level"] = bool(rej[0])
    say(f"   U_1 with p = 0.049 is rejected once all 23 other nodes are rejected: {bool(rej[0])} "
        "(so a single U node can reach the full 5% level: partial-null control needs per-contrast validity at 5%)")


# ------------------------------------------------------------------------------------------------ Part D
def part_d():
    say("=" * 100)
    say("PART D: seen stage-1 cells and the expected HB-vs-S-a shift (arithmetic; values from sim_w2_results.json)")
    e = S1M.EMP
    Ua0, UR, Uun = e["U_a0"], e["U_R"], e["U_untuned"]
    say(f"   seen: U(a0) at 1101-1103 = {[round(x, 2) for x in Ua0]}; U(R) at 1101-1103 = {[round(x, 2) for x in UR]}; "
        f"r = {[round(x, 2) for x in e['r']]}; U(theta0) = {Uun:.2f}")
    mu_a0 = sum(Ua0) / 3
    mu_R = sum(UR) / 3
    # P4 (D0): S-a = mean a0 1101-1106 - mean S1 1102-1107; HB = mean over 1102-1106 of (a0 - S1)
    # E[S-a - HB | seen], unseen a0 seeds at the seen mean; seed effects of 1102, 1103 estimated from a0 with rho_a0
    rho = e["rho_a0"]
    a0_unseen = mu_a0
    mean_a0_1102_1106 = (Ua0[1] + Ua0[2] + 3 * a0_unseen) / 5
    term_a0 = (Ua0[0] - mean_a0_1102_1106) / 6
    s_hat = [rho * (Ua0[1] - mu_a0), rho * (Ua0[2] - mu_a0)]
    term_s1 = -(0.0 - sum(s_hat) / 5) / 6        # -(1/6) E[S1_1107 - mean S1 1102-1106]
    p4_shift = term_a0 + term_s1
    p4_shift_d1 = (Ua0[0] - (Ua0[1] + Ua0[2] + 4 * a0_unseen) / 6) / 7   # D1: a0 1101-1107, S1 1102-1107 both 6 paired
    # P1-P3 (D0): S-a - HB = mean R 1101-1108 - mean R 1102-1107
    p1_shift = (UR[0] + mu_R) / 8 - (UR[1] + UR[2] + 4 * mu_R) / 24
    say(f"   P4, D0: E[S-a - HB | seen] ~ {p4_shift:+.2f} pp (a0_1101 term {term_a0:+.2f}; seed-effect term {term_s1:+.2f}); "
        f"D1: {p4_shift_d1:+.2f} pp. Negative = S-a reads P4 less favourable to S1 than HB does.")
    say(f"   P1-P3, D0: E[S-a - HB | seen] ~ {p1_shift:+.3f} pp")
    say(f"   per-arm seed SD: a0 {e['sd_a0']:.2f} pp, R {e['sd_R']:.2f} pp (2 df each); pair SD {e['sd_pair']:.2f}; "
        f"sample cov {0.5 * (e['sd_a0'] ** 2 + e['sd_R'] ** 2 - e['sd_pair'] ** 2):.2f} pp^2 > Var(R) {e['sd_R'] ** 2:.2f}: "
        "an equal-loading shared shift cannot reproduce these (2-df) values")
    RES["D"] = dict(p4_shift_D0=p4_shift, p4_shift_D1=p4_shift_d1, p1_shift_D0=p1_shift, seen_U_a0=Ua0, seen_U_R=UR,
                    U_theta0=Uun, sd_a0=e["sd_a0"], sd_R=e["sd_R"],
                    cov_a0_R=0.5 * (e['sd_a0'] ** 2 + e['sd_R'] ** 2 - e['sd_pair'] ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20000)
    ap.add_argument("--parts", default="ABCD")
    a = ap.parse_args()
    t0 = time.time()
    say(f"verify_extra.py numpy {np.__version__} python {sys.version.split()[0]} reps {a.reps}")
    W.self_test()
    if "D" in a.parts:
        part_d()
    if "C" in a.parts:
        part_c(a.reps)
    if "B" in a.parts:
        part_b(a.reps)
    if "A" in a.parts:
        part_a(a.reps)
    say(f"total {time.time() - t0:.0f} s")
    tag = a.parts
    (HERE / f"verify_extra_results_{tag}.json").write_text(json.dumps(RES, indent=1, default=float))
    (HERE / f"verify_extra_out_{tag}.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
