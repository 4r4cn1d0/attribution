#!/usr/bin/env python3
"""sim_w2.py: a quantitative check of mock review A's W2 and W5 for the stage-1 analysis model (OLMo-2-1B, recipe B).

Read-only. It reads labels and counts only: the Gate A a0 units (seeds 1101-1103) and the untuned unit through
scripts/family_probe_reading.py (its frozen label rule `_unsafe` and its frozen `counts`), and the Gate B wave-0a
noise-gate output (r_j, sigma_gate, sigma_eval,0). It never prints a prompt id, prompt text or answer text.
It opens no selector.jsonl, hidden/, held-out file, wave-0b rows.jsonl or groups.json, and no wave-0a R-arm record.

Run (numpy only; this venv has no scipy, so the t, F and chi-square functions are implemented below and tested):
    PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B \
        sim_w2.py [--reps N] [--quick]
Writes sim_w2_out.txt (a copy of stdout) and sim_w2_results.json beside this file. Every random stream has a fixed seed.

Part 1 (empirical): per-arm seed SD, paired same-seed SD, implied same-seed correlation, sampling and prompt-clustered
SE, prompt x seed term, the per-answer common-random-number (CRN) correlation implied by sigma_eval,0.
Part 2 (analytic): the reviewer's arithmetic (MDE, TOST, Welch factor) re-computed with exact t quantiles.
Part 3 (seed-level replica): the reviewer's heteroscedastic simulation, as the reviewer describes it.
Part 4 (answer-level simulation): 50 arm-seed cells laid out as the stage-1 plan (a0 1101-1106, R 1101-1108, six
method arms 1102-1107), 200 prompts x 3 sampled answers, a logit-normal prompt bank fitted to Gate A, a shared seed
shift, arm-specific seed shifts, CRN sampling, optional arm x prompt interaction. Analyses: (a) unpaired, pooled
variance (the current text); (aW) unpaired Welch; (b) paired by seed on common seeds, crossed seed x prompt
two-way variance per contrast (unequal variances by construction), Satterthwaite df; (b0) paired by seed, seed level
only; (b2) seed-blocked additive model on all 50 cells, residual variance pooled (df 35); (b2x) b2 plus the crossed
prompt term of (b); (b3) b2x with a pre-registered per-arm variance check that falls back to (b) for contrasts that
touch a flagged arm.
"""
import argparse, json, math, pathlib, sys, time, hashlib
import numpy as np
import warnings
warnings.filterwarnings("ignore", message=".*encountered in matmul")   # spurious Accelerate BLAS warnings in numpy 2.2 (results checked finite)

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
NOISE_GATE = ROOT / "research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json"
NOISE_GATE_POST = ROOT / "research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-post-wave0b.json"
GATE_B_INPUTS = ROOT / "tmp/gate-b-olmo/gate_b_inputs_noise_gate.json"

OUT_LINES = []


def say(*parts):
    line = " ".join(str(p) for p in parts)
    print(line)
    OUT_LINES.append(line)


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# ===================================== distributions (no scipy) =====================================================

_LANCZOS = (0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
            12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7)


def lgamma(x):
    """log Gamma(x) for x > 0, vectorized (Lanczos, g = 7; about 1e-15 relative)."""
    x = np.asarray(x, dtype=float)
    small = x < 0.5
    z = np.where(small, 1.0 - x, x) - 1.0
    a = np.full_like(z, _LANCZOS[0])
    t = z + 7.5
    for i in range(1, 9):
        a = a + _LANCZOS[i] / (z + i)
    lg = 0.5 * math.log(2 * math.pi) + (z + 0.5) * np.log(t) - t + np.log(a)
    if small.any():
        lg = np.where(small, math.log(math.pi) - np.log(np.abs(np.sin(math.pi * x))) - lg, lg)
    return lg


def _betacf(a, b, x, iters=2000, eps=3e-14):
    """Continued fraction for the regularized incomplete beta (Lentz), vectorized; early stop on convergence."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = np.ones_like(x)
    d = 1.0 - qab * x / qap
    d = np.where(np.abs(d) < tiny, tiny, d)
    d = 1.0 / d
    h = d.copy()
    for m in range(1, iters + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = np.where(np.abs(d) < tiny, tiny, d)
        c = 1.0 + aa / c
        c = np.where(np.abs(c) < tiny, tiny, c)
        d = 1.0 / d
        h = h * d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = np.where(np.abs(d) < tiny, tiny, d)
        c = 1.0 + aa / c
        c = np.where(np.abs(c) < tiny, tiny, c)
        d = 1.0 / d
        de = d * c
        h = h * de
        if np.all(np.abs(de - 1.0) < eps):
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta I_x(a, b), vectorized over arrays a, b, x (broadcast)."""
    a, b, x = np.broadcast_arrays(np.asarray(a, float), np.asarray(b, float), np.asarray(x, float))
    a, b, x = a.ravel().copy(), b.ravel().copy(), x.ravel().copy()
    out = np.zeros_like(x)
    out[x >= 1.0] = 1.0
    inner = (x > 0.0) & (x < 1.0)
    if inner.any():
        ai, bi, xi = a[inner], b[inner], x[inner]
        lfront = lgamma(ai + bi) - lgamma(ai) - lgamma(bi) + ai * np.log(xi) + bi * np.log1p(-xi)
        direct = xi < (ai + 1.0) / (ai + bi + 2.0)
        res = np.empty_like(xi)
        if direct.any():
            res[direct] = np.exp(lfront[direct]) * _betacf(ai[direct], bi[direct], xi[direct]) / ai[direct]
        if (~direct).any():
            r = ~direct
            res[r] = 1.0 - np.exp(lfront[r]) * _betacf(bi[r], ai[r], 1.0 - xi[r]) / bi[r]
        out[inner] = res
    return out


def t_sf(t, df):
    """One-sided upper tail P(T > t), vectorized."""
    t, df = np.broadcast_arrays(np.asarray(t, float), np.asarray(df, float))
    shape = t.shape
    t, df = t.ravel(), np.minimum(df.ravel(), 1e6)
    x = df / (df + t * t)
    two = betainc(df / 2.0, 0.5, x)          # P(|T| > |t|)
    out = np.where(t > 0, two / 2.0, 1.0 - two / 2.0)
    return out.reshape(shape)


def t_p2(t, df):
    """Two-sided p-value P(|T| > |t|)."""
    t, df = np.broadcast_arrays(np.asarray(t, float), np.asarray(df, float))
    shape = t.shape
    t, df = t.ravel(), np.minimum(df.ravel(), 1e6)
    return betainc(df / 2.0, 0.5, df / (df + t * t)).reshape(shape)


def t_ppf(p, df):
    """Scalar quantile of Student t by bisection on t_sf."""
    if p == 0.5:
        return 0.0
    if p < 0.5:
        return -t_ppf(1.0 - p, df)
    lo, hi = 0.0, 1.0
    while t_sf(hi, df) > 1.0 - p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_sf(mid, df) > 1.0 - p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def norm_ppf(p):
    return t_ppf(p, 1e6)


def f_sf(f, d1, d2):
    """P(F > f) for F(d1, d2)."""
    f, d1, d2 = np.broadcast_arrays(np.asarray(f, float), np.asarray(d1, float), np.asarray(d2, float))
    x = d2 / (d2 + d1 * f)
    return betainc(d2 / 2.0, d1 / 2.0, x).reshape(f.shape)


def f_ppf(p, d1, d2):
    lo, hi = 0.0, 1.0
    while f_sf(hi, d1, d2) > 1.0 - p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f_sf(mid, d1, d2) > 1.0 - p:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


def chi2_cdf(x, k):
    """Regularized lower incomplete gamma P(k/2, x/2) through the beta link is awkward; use the series directly."""
    a, z = k / 2.0, x / 2.0
    if z <= 0:
        return 0.0
    term = 1.0 / a
    total = term
    n = 1
    while n < 10000:
        term *= z / (a + n)
        total += term
        if term < total * 1e-15:
            break
        n += 1
    return math.exp(-z + a * math.log(z) - math.lgamma(a)) * total


def chi2_ppf(p, k):
    lo, hi = 0.0, max(1.0, 4.0 * k)
    while chi2_cdf(hi, k) < p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if chi2_cdf(mid, k) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def self_test():
    checks = [(t_ppf(0.975, 5), 2.570582), (t_ppf(0.975, 42), 2.018082), (t_ppf(0.995, 5), 4.032143),
              (t_ppf(0.95, 3), 2.353363), (t_ppf(0.975, 1e6), 1.959964), (t_ppf(0.8, 5), 0.919544),
              (chi2_ppf(0.05, 2), 0.102587), (chi2_ppf(0.95, 2), 5.991465), (chi2_ppf(0.05, 4), 0.710723),
              (chi2_ppf(0.95, 4), 9.487729), (f_ppf(0.95, 5, 35), 2.485143), (float(t_sf(2.0, 10.0)), 0.036694)]
    worst = max(abs(a - b) for a, b in checks)
    say(f"[self-test] t/chi2/F against tabulated values: max abs error {worst:.2e} "
        f"({'PASS' if worst < 2e-5 else 'FAIL'})")
    if worst >= 2e-5:
        raise SystemExit("distribution self-test failed")


# ===================================== Part 1: empirical ============================================================

def load_fpr():
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.dont_write_bytecode = True
    import importlib.util
    spec = importlib.util.spec_from_file_location("family_probe_reading", ROOT / "scripts/family_probe_reading.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def empirical():
    say("=" * 100)
    say("PART 1. Empirical noise components (labels and counts only)")
    say("=" * 100)
    fpr = load_fpr()
    inputs = json.loads(GATE_B_INPUTS.read_text())
    ng = json.loads(NOISE_GATE.read_text())
    ngp = json.loads(NOISE_GATE_POST.read_text())
    bars = json.loads(fpr.DEFAULT_BARS.read_text())
    say(f"[R] noise-gate output {NOISE_GATE.name} sha256 {sha256(NOISE_GATE)[:16]}; bars sha256 "
        f"{sha256(fpr.DEFAULT_BARS)[:16]} (frozen {fpr.FROZEN_BARS['family-probe-reading-amended-20261008'][:16]})")
    units = {}
    for name in ("1101", "1102", "1103", "untuned"):
        unit = pathlib.Path(inputs["gate_a"][name])
        ev = unit / "eval" / ("init" if name == "untuned" else "e1")
        # identity check against the noise-gate output's unit hashes (seeded units only)
        if name != "untuned":
            rec = ng["units"][f"gate_a/{name}"]
            ok = (sha256(unit / "job.json") == rec["job_sha256"]) and (sha256(unit / "COMPLETE.json") == rec["complete_sha256"])
            say(f"[R] Gate A unit {name}: job.json and COMPLETE.json SHA-256 equal the noise-gate output's: {ok}")
            if not ok:
                raise SystemExit("unit identity mismatch")
        guards = fpr.jsonl(ev / "guard_samples.jsonl")
        frozen = fpr.counts(ev, bars, "olmo2", set())     # the frozen counts (numbers only are used)
        lab = {}
        for g in guards:
            lab[(g["prompt_id"], int(g["sample_index"]))] = 1 if fpr._unsafe(g) else 0
        units[name] = {"labels": lab, "frozen": frozen}
        n_unsafe = sum(lab.values())
        if n_unsafe != frozen["frozen"]["sampled_unsafe"] or len(lab) != frozen["frozen"]["sampled_answers"]:
            raise SystemExit(f"{name}: own label count disagrees with the frozen counts")
    prompts = sorted({p for (p, k) in units["1101"]["labels"]})
    for name in units:
        if sorted({p for (p, k) in units[name]["labels"]}) != prompts:
            raise SystemExit("prompt sets differ between units")
    P = len(prompts)
    names = ["1101", "1102", "1103", "untuned"]
    Y = np.array([[[units[n]["labels"][(p, k)] for k in range(3)] for p in prompts] for n in names], dtype=float)
    kcount = Y.sum(-1)                                     # (unit, prompt) unsafe count of 3
    U = Y.mean((1, 2)) * 100.0
    res = {"P": P}
    say(f"[R] prompts {P}, samples per prompt 3; U (pp) a0 1101/1102/1103 = "
        + " / ".join(f"{u:.2f}" for u in U[:3]) + f"; untuned = {U[3]:.2f}"
        + "  (counts " + ", ".join(str(int(units[n]['frozen']['frozen']['sampled_unsafe'])) for n in names) + ")")
    # sampling SE, clustered SE, share between prompts
    say("")
    say("1a. Within-arm SEs (per unit)")
    rows = []
    for i, n in enumerate(names):
        share = kcount[i] / 3.0
        se_cl = math.sqrt(float(units[n]["frozen"]["se2"])) * 100.0
        se_cl_own = share.std(ddof=1) / math.sqrt(P) * 100.0
        s2p = kcount[i] * (3 - kcount[i]) / 6.0           # unbiased within-prompt variance of the 3 binary answers
        se_samp = math.sqrt(s2p.sum() / 3.0) / P * 100.0
        between = 1.0 - se_samp ** 2 / se_cl ** 2
        rows.append((n, se_cl, se_cl_own, se_samp, between))
        say(f"   {n:>8}: clustered SE {se_cl:.3f} pp (frozen se2; own {se_cl_own:.3f}); within-prompt sampling SE "
            f"{se_samp:.3f} pp; share of clustered variance between prompts {between * 100:.1f}%")
    res["within_arm"] = [dict(unit=r[0], se_clustered=r[1], se_sampling=r[3], between_share=r[4]) for r in rows]
    # prompt x seed term and cross-seed correlations
    say("")
    say("1b. Seed pairs of a0 (different seeds, different sampling streams): per-prompt difference")
    pair_rows = []
    for i, j in ((0, 1), (0, 2), (1, 2)):
        d = (kcount[i] - kcount[j]) / 3.0
        se_d = d.std(ddof=1) / math.sqrt(P) * 100.0
        pure = math.sqrt(rows[i][3] ** 2 + rows[j][3] ** 2)
        r = np.corrcoef(kcount[i], kcount[j])[0, 1]
        # residual (within-prompt) correlation matched on (prompt, sample index): the CRN signal
        ri = (Y[i] - Y[i].mean(-1, keepdims=True)).ravel()
        rj = (Y[j] - Y[j].mean(-1, keepdims=True)).ravel()
        rc = float(np.dot(ri, rj) / math.sqrt(np.dot(ri, ri) * np.dot(rj, rj)))
        pair_rows.append(dict(pair=f"{names[i]}-{names[j]}", se_diff=se_d, pure_sampling=pure, prompt_corr=r, resid_corr=rc))
        say(f"   {names[i]} vs {names[j]}: clustered SE of the per-prompt difference {se_d:.3f} pp; pure sampling "
            f"{pure:.3f} pp; ratio {se_d / pure:.3f}; per-prompt count correlation {r:.3f}; within-prompt residual "
            f"correlation (matched sample index) {rc:+.3f}")
    i, j = 3, 0
    ri = (Y[i] - Y[i].mean(-1, keepdims=True)).ravel()
    rj = (Y[j] - Y[j].mean(-1, keepdims=True)).ravel()
    rc_init = float(np.dot(ri, rj) / math.sqrt(np.dot(ri, ri) * np.dot(rj, rj)))
    n_var_init = int(((kcount[3] > 0) & (kcount[3] < 3)).sum())
    n_both = int((((kcount[3] > 0) & (kcount[3] < 3)) & ((kcount[0] > 0) & (kcount[0] < 3))).sum())
    say(f"   untuned vs 1101 (shared sampling streams): residual correlation {rc_init:+.3f}; prompts where the untuned "
        f"unit's 3 answers vary: {n_var_init} of {P}; where both units vary: {n_both}")
    res["a0_seed_pairs"] = pair_rows
    res["untuned_vs_1101_resid_corr"] = rc_init
    res["untuned_varying_prompts"] = n_var_init
    res["both_varying_prompts"] = n_both

    # seed level, from the noise-gate output
    say("")
    say("1c. Seed level: a0 (Gate A) and R_j (wave 0a, U(R_j) = U(a0_j) - r_j)")
    plain, fb = ng["result"]["plain"], ng["result"]["fallback"]
    same_post = (ngp["result"]["plain"]["r_pp"] == plain["r_pp"]) and (ngp["result"]["plain"]["sigma_eval0_pp"] == plain["sigma_eval0_pp"])
    say(f"[R] r_j (pp) = {plain['r_pp']}; sigma_gate {plain['sigma_gate_pp']:.4f}; sigma_eval,0 seed-matched "
        f"{plain['sigma_eval0_pp']:.4f}; fallback (R-arm pairs, not seed-matched) sigma_eval,0 {fb['sigma_eval0_pp']:.4f}; "
        f"post-wave-0b reading identical: {same_post}")
    seeds = ["1101", "1102", "1103"]
    ua = U[:3]
    r = np.array([plain["r_pp"][s] for s in seeds])
    ur = ua - r
    say(f"   U(a0) = {np.round(ua, 3).tolist()}; U(R) = {np.round(ur, 3).tolist()} (counts "
        f"{[int(round(x * 6)) for x in ur]})")
    va, vr, vd = ua.var(ddof=1), ur.var(ddof=1), r.var(ddof=1)
    cov = np.cov(ua, ur, ddof=1)[0, 1]
    rho_sample = cov / math.sqrt(va * vr)
    vpool = (va + vr) / 2.0
    rho_pool = 1.0 - vd / (2.0 * vpool)
    rho_a0 = 1.0 - vd / (2.0 * va)

    def sd_ci(v, df):
        return math.sqrt(df * v / chi2_ppf(0.95, df)), math.sqrt(df * v / chi2_ppf(0.05, df))

    for label, v, df in (("a0 per-arm seed SD", va, 2), ("R per-arm seed SD", vr, 2), ("pooled per-arm seed SD", vpool, 4),
                         ("paired same-seed SD (sigma_gate)", vd, 2)):
        lo, hi = sd_ci(v, df)
        say(f"   {label:<34} {math.sqrt(v):.3f} pp ({df} df; 90% CI {lo:.2f}-{hi:.2f})")
    say(f"   F = var(a0)/var(R) = {va / vr:.2f}; P(F(2,2) >= that) = {1.0 / (1.0 + va / vr):.3f} (one-sided)")
    say(f"   implied same-seed correlation: sample corr(a0_j, R_j) {rho_sample:.3f}; from pooled variance "
        f"1 - s_d^2/(2 s_pool^2) = {rho_pool:.3f}; from a0's variance alone {rho_a0:.3f}")
    # exact small-sample interval for rho (n = 3) by Monte Carlo inversion
    rng = np.random.default_rng(20261017)
    grid = np.round(np.arange(-0.95, 0.991, 0.01), 3)
    lo_ok, hi_ok = [], []
    pzero = None
    for rho in grid:
        z1 = rng.standard_normal((200000, 3))
        z2 = rho * z1 + math.sqrt(1 - rho * rho) * rng.standard_normal((200000, 3))
        z1c = z1 - z1.mean(1, keepdims=True)
        z2c = z2 - z2.mean(1, keepdims=True)
        rr = (z1c * z2c).sum(1) / np.sqrt((z1c ** 2).sum(1) * (z2c ** 2).sum(1))
        pge = float((rr >= rho_sample).mean())
        ple = float((rr <= rho_sample).mean())
        if abs(rho) < 1e-9:
            pzero = pge
        if pge > 0.05 and ple > 0.05:
            lo_ok.append(rho)
    say(f"   P(sample corr >= {rho_sample:.2f} | true rho = 0, n = 3) = {pzero:.3f} (exact value "
        f"{0.5 - math.asin(rho_sample) / math.pi:.3f}); 90% interval for rho by inversion: "
        f"{min(lo_ok):.2f} to {max(lo_ok):.2f} (grid -0.95..0.99)")
    # second same-seed pair in the records: recipe B vs recipe G (FOCUS; E by seed)
    eb = ua - U[3]
    eg = np.array([29.0, 31.0, 26.5])
    rho_bg = np.corrcoef(eb, eg)[0, 1]
    sd_bg = (eb - eg).std(ddof=1)
    say(f"   second same-seed pair (FOCUS: recipe G E by seed {eg.tolist()} against recipe B {np.round(eb, 2).tolist()}): "
        f"sample corr {rho_bg:+.3f}; SD of the paired difference {sd_bg:.2f} pp; per-arm SDs {eb.std(ddof=1):.2f} / "
        f"{eg.std(ddof=1):.2f}")
    # decomposition with sigma_eval,0
    se_samp_mean = float(np.mean([rr_[3] for rr_ in rows[:3]]))
    v_samp = se_samp_mean ** 2
    c_crn = 1.0 - (plain["sigma_eval0_pp"] / fb["sigma_eval0_pp"]) ** 2
    c_crn2 = 1.0 - plain["sigma_eval0_pp"] ** 2 / (2 * v_samp)
    v_train_diff = vd - plain["sigma_eval0_pp"] ** 2
    say("")
    say("1d. Decomposition (I): sampling versus training-seed parts")
    say(f"   per-arm sampling variance (a0 mean) {v_samp:.3f} pp^2 (SE {se_samp_mean:.3f})")
    say(f"   per-answer same-seed CRN correlation c = 1 - (sigma_eval,0 / fallback sigma_eval,0)^2 = {c_crn:.3f}; "
        f"against a0's own pure sampling: 1 - sigma_eval,0^2 / (2 v_samp) = {c_crn2:.3f}")
    say(f"   training part of var(r_j) = {vd:.3f} - {plain['sigma_eval0_pp'] ** 2:.3f} = {v_train_diff:.3f} pp^2 "
        f"(SD {math.sqrt(max(v_train_diff, 0)):.2f}; 2 df)")
    vt_arm = v_train_diff / 2.0
    for label, v in (("a0", va), ("R", vr), ("pooled", vpool)):
        vs = v - v_samp - vt_arm
        say(f"   shared training-seed variance from {label:<6}: {v:.3f} - {v_samp:.3f} - {vt_arm:.3f} = {vs:+.3f} pp^2")
    res.update(dict(U_a0=ua.tolist(), U_R=ur.tolist(), U_untuned=float(U[3]), r=r.tolist(), sd_a0=math.sqrt(va),
                    sd_R=math.sqrt(vr), sd_pool=math.sqrt(vpool), sd_pair=math.sqrt(vd), rho_sample=rho_sample,
                    rho_pool=rho_pool, rho_a0=rho_a0, rho_ci90=[min(lo_ok), max(lo_ok)], p_rho_zero=pzero,
                    rho_recipe_bg=rho_bg, sd_pair_bg=sd_bg, v_samp=v_samp, c_crn=c_crn, c_crn_own=c_crn2,
                    v_train_diff=v_train_diff, sigma_eval0=plain["sigma_eval0_pp"],
                    sigma_eval0_fallback=fb["sigma_eval0_pp"]))
    return res, kcount[:3]


# ===================================== Part 2: analytic arithmetic ==================================================

def power_t(lam, se_hat, df, crit, se_true, nmc=400000, seed=7):
    """P(|lam_hat| > crit * se_hat_draw), lam_hat ~ N(lam, se_true^2), se_hat_draw^2 = se_hat^2 chi2_df/df."""
    rng = np.random.default_rng(seed)
    w = np.sqrt(rng.chisquare(df, nmc) / df) if df < 1e5 else np.ones(nmc)
    z = rng.standard_normal(nmc)
    est = lam + se_true * z
    return float((np.abs(est) > crit * se_hat * w).mean())


def mde(se_hat, df, alpha2, se_true=None, power=0.8):
    se_true = se_hat if se_true is None else se_true
    crit = t_ppf(1 - alpha2 / 2, df)
    lo, hi = 0.0, 30.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if power_t(mid, se_hat, df, crit, se_true) < power:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def p_equiv0(se, df, delta=5.0, alpha1=0.05):
    crit = t_ppf(1 - alpha1, df)
    rng = np.random.default_rng(11)
    w = np.sqrt(rng.chisquare(df, 400000) / df)
    z = rng.standard_normal(400000) * se
    return float(((np.abs(z) + crit * se * w) < delta).mean())


def analytic(emp):
    say("")
    say("=" * 100)
    say("PART 2. The reviewer's arithmetic, re-computed (exact t quantiles; SE estimate drawn from its chi-square)")
    say("=" * 100)
    a6 = 0.05 / 6
    out = {}
    say(f"   t quantiles: Holm step 1 two-sided t(1-a/12): df42 {t_ppf(1 - a6 / 2, 42):.3f}, df35 "
        f"{t_ppf(1 - a6 / 2, 35):.3f}, df11 {t_ppf(1 - a6 / 2, 11):.3f}, df5 {t_ppf(1 - a6 / 2, 5):.3f}, df4 "
        f"{t_ppf(1 - a6 / 2, 4):.3f}, normal {norm_ppf(1 - a6 / 2):.3f}")
    say(f"   factor (t_crit + t_0.80) at df 42: {t_ppf(1 - a6 / 2, 42) + t_ppf(0.8, 42):.3f}; df 11: "
        f"{t_ppf(1 - a6 / 2, 11) + t_ppf(0.8, 11):.3f}; normal (PLAN-S): {norm_ppf(1 - a6 / 2) + norm_ppf(0.8):.3f}")
    welch_df = (1 / 6 + 1 / 8) ** 2 / ((1 / 6) ** 2 / 5 + (1 / 8) ** 2 / 7)
    say(f"   Welch df for 6 vs 8 at equal variances: {welch_df:.2f}")
    k68, k66 = math.sqrt(1 / 6 + 1 / 8), math.sqrt(1 / 3)
    tab = []
    for label, sd in (("central per-arm 2.65", 2.65), ("blinded cut 4.5 read as pair SD (per-arm 3.18)", 4.5 / math.sqrt(2)),
                      ("per-arm 3.75 (pair 3.75 at rho 0.5)", 3.75), ("per-arm 4.5 (cut read per-arm)", 4.5),
                      ("PLAN-S high per-arm 3.85", 3.85)):
        row = {"label": label, "sd": sd}
        for nm, k in (("6v8", k68), ("6v6", k66)):
            se = sd * k
            m_norm = (norm_ppf(1 - a6 / 2) + norm_ppf(0.8)) * se
            m42 = mde(se, 42, a6)
            mw = mde(se, welch_df if nm == "6v8" else 10.0, a6)
            better = 5.0 + t_ppf(0.8, 42) * se
            pe = p_equiv0(se, 42)
            pe_adj = p_equiv0(se, 42, alpha1=a6)
            row[nm] = dict(se=se, mde_norm=m_norm, mde_t42=m42, mde_welch=mw, better80=better, p_equiv0=pe, p_equiv0_bonf=pe_adj)
        tab.append(row)
        say(f"   {label}:")
        for nm in ("6v8", "6v6"):
            r_ = row[nm]
            say(f"      {nm}: SE {r_['se']:.3f}; Holm-step-1 MDE normal {r_['mde_norm']:.2f}, t42 {r_['mde_t42']:.2f}, Welch "
                f"{r_['mde_welch']:.2f}; 80% 'better' effect {r_['better80']:.2f}; P(equivalent | 0) {r_['p_equiv0']:.3f} "
                f"(one-sided a/6 each: {r_['p_equiv0_bonf']:.3f})")
    out["table"] = tab
    # unpaired test with shared seeds and rho > 0: the estimated SE ignores the covariance
    say("   Unpaired pooled test when same-seed arms correlate (6 shared seeds; R 8, method 6):")
    rows = []
    for sd, rho in ((2.65, 0.0), (2.65, 0.5), (3.75, 0.5), (2.65, emp["rho_a0"]), (emp["sd_pool"], emp["rho_pool"])):
        se_hat = sd * k68
        var_true = sd * sd * (1 / 8 + 1 / 6) - 2 * rho * sd * sd * 6 / 48
        se_true = math.sqrt(var_true)
        m = mde(se_hat, 42, a6, se_true=se_true)
        rows.append(dict(sd=sd, rho=rho, se_hat=se_hat, se_true=se_true, mde=m))
        say(f"      per-arm {sd:.2f}, rho {rho:.2f}: estimated SE {se_hat:.3f}, true SE {se_true:.3f}, MDE {m:.2f} pp "
            f"(nominal two-sided level a/6 becomes {2 * float(t_sf(t_ppf(1 - a6 / 2, 42) * se_hat / se_true, 1e6)):.5f})")
    out["unpaired_with_rho"] = rows
    # paired-by-seed with the wave-0a pair SD (reviewer: 2.7-3.8)
    say("   Paired by seed, 6 pairs, pair SD = sigma_gate 1.833 (the reviewer's 2.7-3.8 pp):")
    se = emp["sd_pair"] / math.sqrt(6)
    prs = []
    for df in (1e6, 42, 35, 11, 5):
        m = mde(se, df, a6)
        prs.append(dict(df=df, mde=m))
        say(f"      df {df:>9.0f}: SE {se:.3f}, Holm-step-1 MDE {m:.2f} pp")
    say(f"      5 pairs (P4: S1 1102-1107 against a0 1101-1106), df 4: MDE {mde(emp['sd_pair'] / math.sqrt(5), 4, a6):.2f} pp")
    out["paired_sigma_gate"] = prs
    # W5: label geometry. better = Holm rejects and estimate >= 5; equivalent = 90% CI inside (-5, 5); worse = Holm
    # rejects and estimate < 0 (U only); inconclusive otherwise. Holm at its first step (others null); the SE estimate is
    # held at its expected value (no chi-square draw), so these are approximations (normal estimate, fixed SE).
    # 'worse' takes precedence over 'equivalent' here: an assumption, because the label order is still open (brief U4).
    say("   W5 label geometry (Holm first step, delta 5 pp; estimate normal, SE estimate fixed; worse before equivalent):")
    geo = []
    for label, se_hat, se_true, df in (("(a) central, 6v8", 1.431, 1.431, 42), ("(a) at wave-0a rho 0.76, 6v8", 1.431, 0.845, 42),
                                       ("blocked pooled at wave-0a (SE 0.75, df 35)", 0.75, 0.75, 35),
                                       ("paired per contrast at wave-0a (SE 0.75, df 5)", 0.75, 0.75, 5)):
        c = t_ppf(1 - a6 / 2, df)
        t95 = t_ppf(0.95, df)
        sig, ceil = c * se_hat, 5.0 - t95 * se_hat
        rng = np.random.default_rng(3)
        z = rng.standard_normal(400000)
        row = dict(label=label, sig=sig, ceil=ceil, overlap=sig < ceil, probs={})
        txt = []
        for lam in (-1.0, 0.0, 3.0, 4.0, 5.0, 6.0):
            e = lam + se_true * z
            rej = np.abs(e) > sig
            better = rej & (e >= 5.0)
            worse = rej & (e < 0)
            equiv = (~better) & (~worse) & (np.abs(e) + t95 * se_hat < 5.0)
            inc = ~(better | worse | equiv)
            pr = dict(better=float(better.mean()), equivalent=float(equiv.mean()), worse=float(worse.mean()), inconclusive=float(inc.mean()))
            row["probs"][lam] = pr
            txt.append(f"{lam:+.0f}: B {pr['better']:.2f} E {pr['equivalent']:.2f} W {pr['worse']:.3f} I {pr['inconclusive']:.2f}")
        geo.append(row)
        say(f"      {label}: significant if |est| > {sig:.2f}; equivalent if |est| < {ceil:.2f}; both possible: {sig < ceil}")
        say("         true effect -> P(label): " + "; ".join(txt))
    out["label_geometry"] = geo
    say(f"   W5 arithmetic: 5 pp / E: E ={np.mean(emp['U_a0']) - emp['U_untuned']:.2f} pp (all three seeds) -> "
        f"{5 / (np.mean(emp['U_a0']) - emp['U_untuned']) * 100:.1f}%; at E = 20 / 55 pp: {5 / 20 * 100:.0f}% / "
        f"{5 / 55 * 100:.1f}%; one third of 5 pp = {5 / 3:.2f} pp")
    return out


# ===================================== Part 3: seed-level replica of the reviewer ===================================

def replica(reps=1_000_000):
    say("")
    say("=" * 100)
    say("PART 3. Seed-level replica of the reviewer's heteroscedastic simulation (independent normal arms)")
    say("=" * 100)
    a6 = 0.05 / 6
    ns = np.array([6, 8, 6, 6, 6, 6, 6, 6])        # a0, R, A1(tested), L1, H1, S1, S3, S4: 50 seeds, pooled df 42
    out = []
    for mult in (1.0, 2.0, 3.0):
        rng = np.random.default_rng(int(1000 * mult) + 31)
        sds = np.full(8, 2.65)
        sds[2] = 2.65 * mult
        ss = np.zeros(reps)
        means = np.zeros((reps, 8))
        var = {}
        for a in range(8):
            x = rng.standard_normal((reps, ns[a])) * sds[a]
            means[:, a] = x.mean(1)
            v = x.var(1, ddof=1)
            var[a] = v
            ss += v * (ns[a] - 1)
        pv = ss / 42.0
        lam = means[:, 1] - means[:, 2]
        se_p = np.sqrt(pv * (1 / 8 + 1 / 6))
        t = lam / se_p
        c1 = t_ppf(1 - a6, 42)
        c2 = t_ppf(1 - a6 / 2, 42)
        one = float((t > c1).mean())
        onez = float((t > norm_ppf(1 - a6)).mean())
        two = float((np.abs(t) > c2).mean())
        sew = np.sqrt(var[1] / 8 + var[2] / 6)
        dfw = sew ** 4 / ((var[1] / 8) ** 2 / 7 + (var[2] / 6) ** 2 / 5)
        tw = lam / sew
        onew = float((t_sf(tw[:200000], dfw[:200000]) < a6).mean())
        twow = float((t_p2(tw[:200000], dfw[:200000]) < a6).mean())
        out.append(dict(mult=mult, pooled_one=one, pooled_one_z=onez, pooled_two=two, welch_one=onew, welch_two=twow))
        say(f"   tested arm SD x{mult:.0f}: pooled t (df 42) one-sided at a/6 rejects {one:.4f} (nominal {a6:.4f}; "
            f"with a normal critical value {onez:.4f}); "
            f"two-sided at a/6 {two:.4f}; Welch one-sided {onew:.4f}, two-sided {twow:.4f} "
            f"(MC SE about {math.sqrt(a6 * (1 - a6) / reps):.4f} pooled, {math.sqrt(a6 * (1 - a6) / 200000):.4f} Welch)")
    return out


# ===================================== Part 4: answer-level simulation ==============================================

ARMS = ["a0", "R", "A1", "L1", "H1", "S1", "S3", "S4"]
SEEDS = list(range(1101, 1109))
ARM_SEEDS = {"a0": range(1101, 1107), "R": range(1101, 1109)}
for _m in ("A1", "L1", "H1", "S1", "S3", "S4"):
    ARM_SEEDS[_m] = range(1102, 1108)
CELLS = [(ARMS.index(a), SEEDS.index(s)) for a in ARMS for s in ARM_SEEDS[a]]
CELL_ARM = np.array([c[0] for c in CELLS])
CELL_SEED = np.array([c[1] for c in CELLS])
NC = len(CELLS)
CONTRASTS = [("P1", "R", "A1"), ("P2", "R", "L1"), ("P3", "R", "H1"), ("P4", "a0", "S1"), ("P5", "S1", "S3"), ("P6", "S1", "S4")]
NPROMPT, NSAMP = 200, 3


def fit_bank(kc):
    """Logit-normal prompt bank by maximum marginal likelihood on the pooled per-prompt counts (k of 9)."""
    k = kc.sum(0)
    n = 3 * kc.shape[0]
    gh_x, gh_w = np.polynomial.hermite.hermgauss(80)
    best = None
    for m in np.arange(-2.0, 2.01, 0.02):
        for s in np.arange(0.5, 6.01, 0.05):
            z = m + math.sqrt(2) * s * gh_x
            p = 1 / (1 + np.exp(-z))
            lik = (gh_w[None, :] / math.sqrt(math.pi) * p[None, :] ** k[:, None] * (1 - p[None, :]) ** (n - k[:, None])).sum(1)
            ll = float(np.log(lik + 1e-300).sum())
            if best is None or ll > best[0]:
                best = (ll, m, s)
    ll, m, s = best
    # refine
    for m2 in np.arange(m - 0.02, m + 0.0201, 0.002):
        for s2 in np.arange(s - 0.05, s + 0.0501, 0.005):
            z = m2 + math.sqrt(2) * s2 * gh_x
            p = 1 / (1 + np.exp(-z))
            lik = (gh_w[None, :] / math.sqrt(math.pi) * p[None, :] ** k[:, None] * (1 - p[None, :]) ** (n - k[:, None])).sum(1)
            l2 = float(np.log(lik + 1e-300).sum())
            if l2 > ll:
                ll, m, s = l2, m2, s2
    z = m + math.sqrt(2) * s * gh_x
    p = 1 / (1 + np.exp(-z))
    w = gh_w / math.sqrt(math.pi)
    pred = np.array([(w * math.comb(n, j) * p ** j * (1 - p) ** (n - j)).sum() for j in range(n + 1)]) * len(k)
    obs = np.bincount(k.astype(int), minlength=n + 1)
    epq = float((w * p * (1 - p)).sum())
    mean_p = float((w * p).sum())
    return dict(m=m, s=s, ll=ll, pred=pred.tolist(), obs=obs.tolist(), epq=epq, mean_p=mean_p)


def logit_shift_for(bank, pp):
    """Logit shift that moves the bank-mean U by pp percentage points (negative pp lowers U)."""
    gh_x, gh_w = np.polynomial.hermite.hermgauss(80)
    z = bank["m"] + math.sqrt(2) * bank["s"] * gh_x
    w = gh_w / math.sqrt(math.pi)
    base = float((w / (1 + np.exp(-z))).sum())
    lo, hi = -3.0, 3.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if float((w / (1 + np.exp(-(z + mid)))).sum()) - base < pp / 100.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def gamma_part(bank, sd_gamma, n=400000, seed=99):
    """pp^2 added to a same-prompt contrast's variance by an arm x prompt term of logit SD sd_gamma (prompts random)."""
    rng = np.random.default_rng(seed)
    b = rng.standard_normal(n) * bank["s"] + bank["m"]
    ga, gb = rng.standard_normal(n) * sd_gamma, rng.standard_normal(n) * sd_gamma
    d = 1 / (1 + np.exp(-(b + ga))) - 1 / (1 + np.exp(-(b + gb)))
    return float(d.var() * 1e4 / NPROMPT)


def gamma_for(bank, target_pp2):
    lo, hi = 0.0, 3.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if gamma_part(bank, mid) < target_pp2:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def make_scenario(name, bank, v_samp, sd_tot=2.65, c=0.0, rho=None, sd_s=None, mult=None, mult_arm="A1", gamma=0.0,
                  neg_arm=None, note=""):
    """Per-arm total seed SD sd_tot (pp; sampling included); same-seed correlation rho -> shared shift; CRN c."""
    k = 100.0 * bank["epq"]                                      # pp per logit unit
    v_tot = sd_tot ** 2
    crn_cov = c * v_samp
    if sd_s is None:
        sd_s = math.sqrt(max(rho * v_tot - crn_cov, 0.0)) if rho is not None else 0.0
    v_t = v_tot - v_samp - sd_s ** 2
    if v_t < 0:
        raise SystemExit(f"{name}: infeasible components")
    sd_t = np.full(len(ARMS), math.sqrt(v_t))
    if mult is not None:
        a = ARMS.index(mult_arm)
        sd_t[a] = math.sqrt((mult * sd_tot) ** 2 - v_samp - sd_s ** 2)
    load = np.ones(len(ARMS))
    if neg_arm is not None:
        load[ARMS.index(neg_arm)] = -1.0
    return dict(name=name, note=note, sd_tot=sd_tot, c=c, sd_s_pp=sd_s, sd_t_pp=sd_t.tolist(), gamma=gamma,
                sd_s=sd_s / k, sd_t=(sd_t / k), load=load, mult=mult, mult_arm=mult_arm, neg_arm=neg_arm,
                rho_nominal=(sd_s ** 2 + crn_cov) / v_tot, sd_pair_nominal=math.sqrt(2 * (v_tot - sd_s ** 2 - crn_cov)))


def simulate_batch(rng, sc, bank, B, eta=None):
    """Answer-level data for B replicates: per-cell U (pp) and per-prompt shares (B, NC, P)."""
    b = rng.standard_normal((B, NPROMPT)) * bank["s"] + bank["m"]
    s = rng.standard_normal((B, len(SEEDS))) * sc["sd_s"]
    t = rng.standard_normal((B, NC)) * sc["sd_t"][CELL_ARM][None, :]
    lin = b[:, None, :] + (sc["load"][CELL_ARM][None, :] * s[:, CELL_SEED])[:, :, None] + t[:, :, None]
    if eta is not None:
        lin = lin + eta[CELL_ARM][None, :, None]
    if sc["gamma"] > 0:
        g = rng.standard_normal((B, len(ARMS), NPROMPT)) * sc["gamma"]
        lin = lin + g[:, CELL_ARM, :]
    pi = (1.0 / (1.0 + np.exp(-lin))).astype(np.float32)
    V = rng.random((B, len(SEEDS), NPROMPT, NSAMP), dtype=np.float32)
    W = rng.random((B, NC, NPROMPT, NSAMP), dtype=np.float32)
    if sc["c"] > 0:
        # each answer takes the seed's shared uniform with probability sqrt(c), so two same-seed answers share it with
        # probability c: their correlation is c when the two arms' probabilities are equal (CRN of the shared streams)
        M = rng.random((B, NC, NPROMPT, NSAMP), dtype=np.float32) < math.sqrt(sc["c"])
        W = np.where(M, V[:, CELL_SEED], W)
    Y = (W < pi[..., None]).astype(np.float32)
    shares = Y.mean(-1)
    Ucell = shares.mean(-1).astype(np.float64) * 100.0
    return Ucell, shares


def blocked_design():
    X = np.zeros((NC, len(ARMS) + len(SEEDS) - 1))
    for i, (a, s) in enumerate(CELLS):
        X[i, a] = 1.0
        if s > 0:
            X[i, len(ARMS) + s - 1] = 1.0
    XtX_inv = np.linalg.inv(X.T @ X)
    H = X @ XtX_inv @ X.T
    return X, XtX_inv, H


XB, XTX_INV, HAT = blocked_design()
DF_B2 = NC - XB.shape[1]
LEV_RES = 1.0 - np.diag(HAT)
H_ARM = np.array([LEV_RES[CELL_ARM == a].sum() for a in range(len(ARMS))])


def analyses(Ucell, shares, kappa):
    """Estimates, SEs and df of the six contrasts under each analysis. Returns dict method -> (est, se, df) arrays (B, 6)."""
    B = Ucell.shape[0]
    out = {}
    arm_cells = [np.where(CELL_ARM == a)[0] for a in range(len(ARMS))]
    means = np.stack([Ucell[:, ix].mean(1) for ix in arm_cells], 1)
    vars_ = np.stack([Ucell[:, ix].var(1, ddof=1) for ix in arm_cells], 1)
    ns = np.array([len(ix) for ix in arm_cells])
    pooled = (vars_ * (ns - 1)).sum(1) / (NC - len(ARMS))
    est_u = np.zeros((B, 6)); se_a = np.zeros((B, 6)); se_w = np.zeros((B, 6)); df_w = np.zeros((B, 6))
    est_p = np.zeros((B, 6)); se_b = np.zeros((B, 6)); df_b = np.zeros((B, 6)); se_b0 = np.zeros((B, 6)); df_b0 = np.zeros((B, 6))
    est_2 = np.zeros((B, 6)); se_2 = np.zeros((B, 6)); pt = np.zeros((B, 6)); pt_den = np.zeros((B, 6))
    beta = Ucell @ np.linalg.pinv(XB).T                       # (B, p)
    resid = Ucell - beta @ XB.T
    s2_b2 = (resid ** 2).sum(1) / DF_B2
    s2_arm = np.stack([(resid[:, CELL_ARM == a] ** 2).sum(1) / H_ARM[a] for a in range(len(ARMS))], 1)
    flagged = s2_arm / s2_b2[:, None] > kappa                 # (B, arms)
    flag_c = np.zeros((B, 6), dtype=bool)
    for ci, (_, comp, m) in enumerate(CONTRASTS):
        a, b_ = ARMS.index(comp), ARMS.index(m)
        est_u[:, ci] = means[:, a] - means[:, b_]
        se_a[:, ci] = np.sqrt(pooled * (1 / ns[a] + 1 / ns[b_]))
        va, vb = vars_[:, a] / ns[a], vars_[:, b_] / ns[b_]
        se_w[:, ci] = np.sqrt(va + vb)
        df_w[:, ci] = (va + vb) ** 2 / (va ** 2 / (ns[a] - 1) + vb ** 2 / (ns[b_] - 1))
        common = sorted(set(ARM_SEEDS[comp]) & set(ARM_SEEDS[m]))
        ia = [CELLS.index((a, SEEDS.index(s))) for s in common]
        ib = [CELLS.index((b_, SEEDS.index(s))) for s in common]
        D = (shares[:, ia, :] - shares[:, ib, :]).astype(np.float64)   # (B, J, P)
        J, P = D.shape[1], D.shape[2]
        gm = D.mean((1, 2))
        rm = D.mean(1)
        cm = D.mean(2)
        ms_p = J * ((rm - gm[:, None]) ** 2).sum(1) / (P - 1)
        ms_j = P * ((cm - gm[:, None]) ** 2).sum(1) / (J - 1)
        ms_e = ((D - rm[:, None, :] - cm[:, :, None] + gm[:, None, None]) ** 2).sum((1, 2)) / ((P - 1) * (J - 1))
        dfp, dfj, dfe = P - 1, J - 1, (P - 1) * (J - 1)
        # Var(mean D) = s2_seed/J + s2_prompt/P + s2_e/(PJ); E[MS_J] = P s2_seed + s2_e, E[MS_P - MS_E] = J s2_prompt.
        # The seed term MS_J is always kept (never truncated: truncating it gives sampling-only SEs with ~1000 df);
        # the prompt term (MS_P - MS_E) is added when positive. Satterthwaite df on that combination.
        ap = ms_p > ms_e
        V = (ms_j + np.where(ap, ms_p - ms_e, 0.0)) / (P * J)
        den = ms_j ** 2 / dfj + np.where(ap, ms_p ** 2 / dfp + ms_e ** 2 / dfe, 0.0)
        dfv = (V * P * J) ** 2 / den
        est_p[:, ci] = gm * 100.0
        se_b[:, ci] = np.sqrt(V) * 100.0
        df_b[:, ci] = dfv
        se_b0[:, ci] = cm.std(1, ddof=1) / math.sqrt(J) * 100.0
        pt[:, ci] = np.where(ap, ms_p - ms_e, 0.0) / (P * J) * 1e4                 # prompt term, pp^2
        pt_den[:, ci] = np.where(ap, (ms_p / (P * J) * 1e4) ** 2 / dfp + (ms_e / (P * J) * 1e4) ** 2 / dfe, 0.0)
        df_b0[:, ci] = J - 1
        cvec = np.zeros(XB.shape[1]); cvec[a] = 1.0; cvec[b_] = -1.0
        est_2[:, ci] = beta @ cvec
        se_2[:, ci] = np.sqrt(s2_b2 * float(cvec @ XTX_INV @ cvec))
        flag_c[:, ci] = flagged[:, a] | flagged[:, b_]
    out["a"] = (est_u, se_a, np.full((B, 6), float(NC - len(ARMS))))
    out["aW"] = (est_u, se_w, df_w)
    out["b"] = (est_p, se_b, df_b)
    out["b0"] = (est_p, se_b0, df_b0)
    out["b2"] = (est_2, se_2, np.full((B, 6), float(DF_B2)))
    v2x = se_2 ** 2 + pt
    se_2x = np.sqrt(v2x)
    df_2x = v2x ** 2 / ((se_2 ** 2) ** 2 / DF_B2 + pt_den)
    out["b2x"] = (est_2, se_2x, df_2x)
    out["b3"] = (np.where(flag_c, est_p, est_2), np.where(flag_c, se_b, se_2x), np.where(flag_c, df_b, df_2x))
    return out, flag_c


METHODS = ["a", "aW", "b", "b0", "b2", "b2x", "b3"]
METHOD_TEXT = {"a": "(a) unpaired, pooled variance, df 42 [current text]",
               "aW": "(aW) unpaired, Welch",
               "b": "(b) paired by seed, crossed seed x prompt, per contrast",
               "b0": "(b0) paired by seed, seed level only, per contrast",
               "b2": "(b2) seed-blocked additive model, pooled residual, df 35",
               "b2x": "(b2x) b2 plus the crossed prompt term of (b)",
               "b3": "(b3) b2x + per-arm variance check, falls back to (b) for a flagged arm"}


def holm(p, alpha=0.05):
    """Holm step-down rejections for p of shape (..., m)."""
    m = p.shape[-1]
    order = np.argsort(p, axis=-1)
    ps = np.take_along_axis(p, order, -1)
    thr = alpha / (m - np.arange(m))
    ok = np.cumprod(ps <= thr, axis=-1).astype(bool)
    rej = np.zeros_like(ok)
    np.put_along_axis(rej, order, ok, -1)
    return rej


def run_null(sc, bank, reps, batch, seed, kappa):
    rng = np.random.default_rng(seed)
    store = {m: [[], [], []] for m in METHODS}
    flags = []
    cal = []
    done = 0
    while done < reps:
        B = min(batch, reps - done)
        Ucell, shares = simulate_batch(rng, sc, bank, B)
        res, fl = analyses(Ucell, shares, kappa)
        for m in METHODS:
            for k in range(3):
                store[m][k].append(res[m][k])
        flags.append(fl)
        # calibration: per-arm seed SD, same-seed correlation, pair SD, sigma_eval (same and different seed)
        ia = [CELLS.index((ARMS.index("a0"), SEEDS.index(s))) for s in range(1102, 1107)]
        ir = [CELLS.index((ARMS.index("R"), SEEDS.index(s))) for s in range(1102, 1107)]
        ua, ur = Ucell[:, ia], Ucell[:, ir]
        d_same = shares[:, ia[0], :] - shares[:, ir[0], :]
        d_diff = shares[:, ia[0], :] - shares[:, ir[1], :]
        cal.append(np.stack([ua.var(1, ddof=1), ur.var(1, ddof=1), (ua - ur).var(1, ddof=1),
                             ((ua - ua.mean(1, keepdims=True)) * (ur - ur.mean(1, keepdims=True))).sum(1) / 4,
                             d_same.std(1, ddof=1) / math.sqrt(NPROMPT) * 100, d_diff.std(1, ddof=1) / math.sqrt(NPROMPT) * 100,
                             shares[:, ia[0], :].std(1, ddof=1) / math.sqrt(NPROMPT) * 100], 1))
        done += B
    for m in METHODS:
        store[m] = [np.concatenate(x, 0) for x in store[m]]
    cal = np.concatenate(cal, 0).mean(0)
    calib = dict(sd_a0=math.sqrt(cal[0]), sd_R=math.sqrt(cal[1]), sd_pair=math.sqrt(cal[2]), rho=cal[3] / math.sqrt(cal[0] * cal[1]),
                 sigma_eval_same=cal[4], sigma_eval_diff=cal[5], se_clustered=cal[6])
    return store, np.concatenate(flags, 0), calib


def pvals(est, se, df):
    return t_p2(est / se, df)


def null_metrics(store, flags):
    a6 = 0.05 / 6
    out = {}
    for m in METHODS:
        est, se, df = store[m]
        p = pvals(est, se, df)
        rej = holm(p)
        worse = rej & (est < 0)
        p_one = t_sf(est / se, df)
        tost = np.maximum(t_sf((est + 5.0) / se, df), t_sf((5.0 - est) / se, df))
        out[m] = dict(rej05=(p < 0.05).mean(0).tolist(), rej_a6=(p < a6).mean(0).tolist(), one_a6_P1=float((p_one[:, 0] < a6).mean()),
                      fwer=float(rej.any(1).mean()), worse_any=float(worse.any(1).mean()),
                      equiv=(tost < 0.05).mean(0).tolist(), equiv_bonf=(tost < a6).mean(0).tolist(),
                      sd_est=est.std(0).tolist(), mean_se=se.mean(0).tolist(), rms_se=np.sqrt((se ** 2).mean(0)).tolist(),
                      mean_df=np.median(df, 0).tolist())
    out["b3_flag_rate"] = flags.mean(0).tolist()
    return out


def shift_curves(store, ci, grid):
    """Power curves for contrast ci by shifting its null estimate by each grid value (others stay null)."""
    out = {}
    for m in METHODS:
        est, se, df = store[m]
        p0 = pvals(est, se, df)
        R = est.shape[0]
        pw, bt, eq = [], [], []
        for lam in grid:
            e = est[:, ci] + lam
            pc = t_p2(e / se[:, ci], df[:, ci])
            p = p0.copy()
            p[:, ci] = pc
            rej = holm(p)[:, ci]
            pw.append(float(rej.mean()))
            bt.append(float((rej & (e >= 5.0)).mean()))
            tost = np.maximum(t_sf((e + 5.0) / se[:, ci], df[:, ci]), t_sf((5.0 - e) / se[:, ci], df[:, ci]))
            eq.append(float((tost < 0.05).mean()))
        out[m] = dict(power=pw, better=bt, equiv=eq)
        # equivalence margin needed for 80% at a true 0
        e0 = est[:, ci]
        lo, hi = 0.0, 40.0
        crit = None
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            tost = np.maximum(t_sf((e0 + mid) / se[:, ci], df[:, ci]), t_sf((mid - e0) / se[:, ci], df[:, ci]))
            if (tost < 0.05).mean() < 0.8:
                lo = mid
            else:
                hi = mid
        out[m]["delta80"] = 0.5 * (lo + hi)
    return out


def first_cross(grid, ys, level=0.8):
    for x0, x1, y0, y1 in zip(grid[:-1], grid[1:], ys[:-1], ys[1:]):
        if y0 < level <= y1:
            return x0 + (level - y0) * (x1 - x0) / (y1 - y0) if y1 != y0 else x1
    return float("nan") if ys[-1] < level else grid[0]


def last_above(grid, ys, level=0.8):
    last = float("nan")
    for x, y in zip(grid, ys):
        if y >= level:
            last = x
    return last


def direct_power(sc, bank, reps, batch, seed, kappa, which, pp=5.0):
    """Direct answer-level power at a true pp effect on contrast `which` (others null)."""
    eta = np.zeros(len(ARMS))
    shift = logit_shift_for(bank, -pp)
    if which == "P1":
        eta[ARMS.index("A1")] = shift
    elif which == "P4":
        for a in ("S1", "S3", "S4"):
            eta[ARMS.index(a)] = shift
    elif which == "P5":
        eta[ARMS.index("S3")] = shift
    ci = [c[0] for c in CONTRASTS].index(which)
    rng = np.random.default_rng(seed)
    hits = {m: [] for m in METHODS}
    lam = []
    done = 0
    while done < reps:
        B = min(batch, reps - done)
        Ucell, shares = simulate_batch(rng, sc, bank, B, eta=eta)
        res, _ = analyses(Ucell, shares, kappa)
        for m in METHODS:
            est, se, df = res[m]
            hits[m].append(holm(pvals(est, se, df))[:, ci])
        lam.append(res["a"][0][:, ci])
        done += B
    return {m: float(np.concatenate(hits[m]).mean()) for m in METHODS}, float(np.concatenate(lam).mean())


def tables():
    """Markdown tables for check-W2-W5.md, from sim_w2_results.json (no simulation)."""
    r = json.loads((HERE / "sim_w2_results.json").read_text())
    sc = {x["name"].split()[0]: x for x in r["scenarios"]}
    order = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "H1", "H2", "H3", "H4", "G1", "G2", "X1"]
    ms = ["a", "aW", "b", "b2x", "b3", "b0", "b2"]
    print("FALSE POSITIVES (true effect 0 everywhere): Holm family-wise rate / worst single contrast at two-sided a/6")
    print("| Scenario | " + " | ".join(ms) + " |")
    print("|---|" + "---|" * len(ms))
    for k in order:
        z = sc[k]["null"]
        cells = [f"{z[m]['fwer'] * 100:.1f} / {max(z[m]['rej_a6']) * 100:.2f}" for m in ms]
        print(f"| {k} | " + " | ".join(cells) + " |")
    print()
    print("MDE AT 80% (Holm over 6, others null), pp: P1 (6 vs 8) / P4 (6 vs 6, 5 pairs) / P5 (6 vs 6, 6 pairs)")
    print("| Scenario | " + " | ".join(ms[:5]) + " |")
    print("|---|" + "---|" * 5)
    for k in order:
        cv = sc[k]["curves"]
        cells = []
        for m in ms[:5]:
            v = cv[m]["mde80"]
            cells.append(" / ".join("> 20" if (x != x) else f"{x:.1f}" for x in (v["P1"], v["P4"], v["P5"])))
        print(f"| {k} | " + " | ".join(cells) + " |")
    print()
    print("P1 at 5 pp and TOST: Holm power at 5 pp / P(better | 5) / 80% 'better' effect / P(equivalent | 0) / delta80 / "
          "largest true effect with P(equivalent) >= 0.8")
    print("| Scenario | " + " | ".join(ms[:5]) + " |")
    print("|---|" + "---|" * 5)
    for k in order:
        cv = sc[k]["curves"]
        cells = []
        for m in ms[:5]:
            c = cv[m]
            b80 = c["better80_P1"]
            l80 = c["equiv80_lambda"]["P1"]
            cells.append(f"{c['power5']['P1']:.2f} / {c['better5_P1']:.2f} / {'> 20' if b80 != b80 else f'{b80:.1f}'} / "
                         f"{c['equiv0']['P1']:.2f} / {c['delta80']['P1']:.1f} / {'none' if l80 != l80 else f'{l80:.2f}'}")
        print(f"| {k} | " + " | ".join(cells) + " |")
    print()
    print("calibration (achieved a0 vs R): per-arm SD, same-seed rho, pair SD, same-seed per-prompt diff SE")
    for k in order:
        c = sc[k]["calib"]
        print(f"  {k}: {c['sd_a0']:.2f} {c['rho']:.2f} {c['sd_pair']:.2f} {c['sigma_eval_same']:.2f}  [{sc[k]['name']}]")


def main():
    if "--tables" in sys.argv:
        tables()
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--batch", type=int, default=200)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.reps = 1000
    t0 = time.time()
    say(f"sim_w2.py  numpy {np.__version__}  reps per scenario {args.reps}  (python {sys.version.split()[0]})")
    self_test()
    emp, kc = empirical()
    ana = analytic(emp)
    rep = replica(200000 if args.quick else 1000000)

    say("")
    say("=" * 100)
    say("PART 4. Answer-level simulation of the stage-1 primary family")
    say("=" * 100)
    say("   cells: a0 1101-1106 (6), R 1101-1108 (8), A1 L1 H1 S1 S3 S4 1102-1107 (6 each): 50 cells; pooled df 42")
    for name, comp, m in CONTRASTS:
        common = sorted(set(ARM_SEEDS[comp]) & set(ARM_SEEDS[m]))
        only_c = sorted(set(ARM_SEEDS[comp]) - set(ARM_SEEDS[m]))
        only_m = sorted(set(ARM_SEEDS[m]) - set(ARM_SEEDS[comp]))
        say(f"   {name} {comp}-{m}: same-seed pairs {common[0]}-{common[-1]} ({len(common)}); unpaired {comp} {only_c}, {m} {only_m}")
    bank = fit_bank(kc)
    k = 100 * bank["epq"]
    v_samp = 1e4 * bank["epq"] / (NPROMPT * NSAMP)
    say(f"   prompt bank: logit-normal fitted to the pooled Gate A a0 counts (k of 9 per prompt): mean {bank['m']:.3f}, SD "
        f"{bank['s']:.3f}; implied mean U {bank['mean_p'] * 100:.2f} pp, E[pi(1-pi)] {bank['epq']:.4f}, per-arm sampling SE "
        f"{math.sqrt(v_samp):.3f} pp, {k:.2f} pp per logit unit")
    say("   observed vs fitted prompts by count k of 9: " + "; ".join(f"{j}: {o}/{p:.1f}" for j, (o, p) in enumerate(zip(bank['obs'], bank['pred']))))
    c_emp = emp["c_crn"]
    # G1: an arm x prompt term that the a0-R data still allow. A short calibration run (400 replicates per point, grid
    # 0.2-0.5 pp^2 x c 0.75-0.95) found that 0.3 pp^2 with CRN c = 0.85 gives a same-seed per-prompt difference SE of
    # about 1.30 pp (measured sigma_eval,0: 1.28). The arm x prompt term weakens the CRN coupling, so c must exceed the
    # naive 1 - (1.64 - 0.3) / 4.65 = 0.71.
    GP1 = 0.3
    g1 = gamma_for(bank, GP1)
    c_g1 = 0.85
    say(f"   arm x prompt: logit SD {g1:.3f} adds {GP1} pp^2 to a same-prompt contrast (bound for null-like pairs: "
        f"sigma_eval,0^2 = {emp['sigma_eval0'] ** 2:.2f} pp^2, reached only if CRN were perfect)")
    sc_list = [
        make_scenario("N1 central, independent (PLAN-S)", bank, v_samp, 2.65, c=0.0, rho=0.0, note="per-arm 2.65, rho 0, c 0"),
        make_scenario("N2 CRN only", bank, v_samp, 2.65, c=c_emp, sd_s=0.0, note="per-arm 2.65, no shared training shift"),
        make_scenario("N3 rho 0.5", bank, v_samp, 2.65, c=c_emp, rho=0.5, note="per-arm 2.65"),
        make_scenario("N4 wave-0a, a0 scale", bank, v_samp, 2.65, c=c_emp, rho=emp["rho_a0"], note="per-arm 2.65, pair SD 1.83"),
        make_scenario("N5 wave-0a, pooled scale", bank, v_samp, emp["sd_pool"], c=c_emp, rho=emp["rho_pool"], note="per-arm 2.10, pair SD 1.83"),
        make_scenario("N6 PLAN-S high, independent", bank, v_samp, 3.85, c=0.0, rho=0.0, note="per-arm 3.85"),
        make_scenario("N7 blinded cut 4.5, rho 0", bank, v_samp, 4.5 / math.sqrt(2), c=0.0, rho=0.0, note="pair SD 4.5"),
        make_scenario("N8 blinded cut 4.5 at wave-0a rho", bank, v_samp, 4.5 / math.sqrt(2 * (1 - emp["rho_a0"])), c=c_emp,
                      rho=emp["rho_a0"], note="pair SD 4.5"),
        make_scenario("H1 N1 + A1 SD x2 (reviewer)", bank, v_samp, 2.65, c=0.0, rho=0.0, mult=2.0, mult_arm="A1"),
        make_scenario("H2 N1 + A1 SD x3 (reviewer)", bank, v_samp, 2.65, c=0.0, rho=0.0, mult=3.0, mult_arm="A1"),
        make_scenario("H3 N4 + A1 SD x2", bank, v_samp, 2.65, c=c_emp, rho=emp["rho_a0"], mult=2.0, mult_arm="A1"),
        make_scenario("H4 N4 + S1 SD x2", bank, v_samp, 2.65, c=c_emp, rho=emp["rho_a0"], mult=2.0, mult_arm="S1"),
        make_scenario("G1 N4 + arm x prompt, data-consistent", bank, v_samp, 2.65, c=c_g1, rho=emp["rho_a0"], gamma=g1,
                      note=f"arm x prompt adds {GP1:.2f} pp^2; CRN raised to {c_g1:.2f} so the same-seed sigma_eval stays near 1.28"),
        make_scenario("G2 N4 + arm x prompt beyond the a0-R data", bank, v_samp, 2.65, c=c_emp, rho=emp["rho_a0"], gamma=0.5,
                      note=f"logit SD 0.5 adds {gamma_part(bank, 0.5):.2f} pp^2"),
        make_scenario("X1 N4, A1 opposite to the shared shift", bank, v_samp, 2.65, c=c_emp, rho=emp["rho_a0"], neg_arm="A1"),
    ]
    # kappa for (b3): per-arm F-type check, the 95% point of F(h_arm, 35) at the method arms' residual df (frozen here)
    kappa = f_ppf(0.95, float(H_ARM[2]), float(DF_B2))
    say(f"   (b3) variance check: flag an arm if its blocked residual variance / pooled > {kappa:.3f} (F 95% at df "
        f"{H_ARM[2]:.2f}, {DF_B2}); residual df by arm: " + ", ".join(f"{a} {h:.2f}" for a, h in zip(ARMS, H_ARM)))
    grid = np.round(np.arange(0.0, 20.01, 0.25), 2)
    results = dict(empirical=emp, analytic=ana, replica=rep, bank=bank, kappa=kappa, scenarios=[])
    for i, sc in enumerate(sc_list):
        t1 = time.time()
        store, flags, calib = run_null(sc, bank, args.reps, args.batch, 20261017 + 1000 * i, kappa)
        nm = null_metrics(store, flags)
        curves = {c: shift_curves(store, [x[0] for x in CONTRASTS].index(c), grid) for c in ("P1", "P4", "P5")}
        say("")
        say(f"--- {sc['name']} ({sc['note']}): components pp: shared {sc['sd_s_pp']:.2f}, arm-specific "
            f"{sc['sd_t_pp'][0]:.2f}" + (f" ({sc['mult_arm']} {sc['sd_t_pp'][ARMS.index(sc['mult_arm'])]:.2f})" if sc['mult'] else "")
            + f", CRN c {sc['c']:.2f}, arm x prompt {sc['gamma']:.2f}; nominal rho {sc['rho_nominal']:.2f}, pair SD "
            f"{sc['sd_pair_nominal']:.2f}  [{time.time() - t1:.0f} s]")
        say(f"    achieved (a0 vs R, seeds 1102-1106): per-arm SD {calib['sd_a0']:.2f}/{calib['sd_R']:.2f}, same-seed rho "
            f"{calib['rho']:.2f}, pair SD {calib['sd_pair']:.2f}; per-prompt diff SE same seed {calib['sigma_eval_same']:.2f}, "
            f"different seed {calib['sigma_eval_diff']:.2f}; clustered SE {calib['se_clustered']:.2f}")
        say("    method | P1 two-sided a/6 | P1 one-sided a/6 | mean over P1-P6 at 0.05 | Holm FWER | any 'worse' | "
            "SE/SD P1 | P(equiv|0) P1 P4 P5 | Holm power 5pp P1 P4 P5 | MDE80 P1 P4 P5 | P(better|5) P1 | better80 P1 | delta80 P1 P4")
        rec = dict(name=sc["name"], note=sc["note"], calib=calib, null=nm, curves={}, components=dict(
            sd_s=sc["sd_s_pp"], sd_t=sc["sd_t_pp"], c=sc["c"], gamma=sc["gamma"], rho=sc["rho_nominal"], pair=sc["sd_pair_nominal"]))
        i5 = int(np.where(grid == 5.0)[0][0])
        for m in METHODS:
            z = nm[m]
            cv = {c: curves[c][m] for c in curves}
            mde80 = {c: first_cross(grid, cv[c]["power"]) for c in cv}
            b80 = first_cross(grid, cv["P1"]["better"])
            rec["curves"][m] = dict(mde80=mde80, better80_P1=b80, delta80={c: cv[c]["delta80"] for c in cv},
                                    power5={c: cv[c]["power"][i5] for c in cv}, better5_P1=cv["P1"]["better"][i5],
                                    equiv0={c: cv[c]["equiv"][0] for c in cv},
                                    equiv80_lambda={c: last_above(grid, cv[c]["equiv"]) for c in cv})
            say(f"    {m:>3} | {z['rej_a6'][0]:.4f} | {z['one_a6_P1']:.4f} | {np.mean(z['rej05']):.4f} | {z['fwer']:.4f} | "
                f"{z['worse_any']:.4f} | {z['rms_se'][0] / z['sd_est'][0]:.2f} | "
                f"{cv['P1']['equiv'][0]:.2f} {cv['P4']['equiv'][0]:.2f} {cv['P5']['equiv'][0]:.2f} | "
                f"{cv['P1']['power'][i5]:.2f} {cv['P4']['power'][i5]:.2f} {cv['P5']['power'][i5]:.2f} | "
                f"{mde80['P1']:.2f} {mde80['P4']:.2f} {mde80['P5']:.2f} | {cv['P1']['better'][i5]:.2f} | {b80:.2f} | "
                f"{cv['P1']['delta80']:.2f} {cv['P4']['delta80']:.2f}")
        say(f"    median df: " + "; ".join(f"{m} {np.mean(nm[m]['mean_df'][:3]):.1f}/{nm[m]['mean_df'][3]:.1f}" for m in METHODS)
            + f" (P1-P3 / P4); (b3) flag rate by contrast {np.round(nm['b3_flag_rate'], 3).tolist()}")
        if sc["mult"] or sc["neg_arm"] or sc["gamma"] > 0:
            say(f"    per-contrast two-sided rejection at a/6: " + "; ".join(
                f"{m} " + " ".join(f"{x:.4f}" for x in nm[m]["rej_a6"]) for m in METHODS))
        results["scenarios"].append(rec)
    # direct validation of the shift approximation at 5 pp
    say("")
    say("--- direct answer-level power at a true 5 pp effect (validates the shift method; Holm, others null)")
    for i, (sc, which) in enumerate(((sc_list[0], "P1"), (sc_list[3], "P1"), (sc_list[3], "P4"))):
        pw, lam = direct_power(sc, bank, max(args.reps // 2, 500), args.batch, 777 + i, kappa, which)
        ref = next(r for r in results["scenarios"] if r["name"] == sc["name"])
        say(f"    {sc['name']} {which}: realized mean effect {lam:.2f} pp; direct power " + ", ".join(f"{m} {pw[m]:.3f}" for m in METHODS)
            + " | shift method " + ", ".join(f"{m} {ref['curves'][m]['power5'][which]:.3f}" for m in METHODS))
        results.setdefault("direct", []).append(dict(scenario=sc["name"], which=which, lam=lam, direct=pw))
    say("")
    say(f"total time {time.time() - t0:.0f} s")
    (HERE / "sim_w2_results.json").write_text(json.dumps(results, indent=1, default=float))
    (HERE / "sim_w2_out.txt").write_text("\n".join(OUT_LINES) + "\n")


if __name__ == "__main__":
    main()
