"""SR-2's error-rate simulation (7-8B tier; Part 2 §10.3, DES K6, DESO3 V2; P1 §6.1-§6.4, §4, §7; $0; numpy).

    python3 -I -B scripts/scale78b/sr2_simulation.py --settings scripts/scale78b/settings/sr2_simulation.json \\
        --option B|C --design full|reduced [--stopped olmo2-7b[,llama31-8b]] [--sigma I,J,...] [--out OUT.json]
    python3 -I -B scripts/scale78b/sr2_simulation.py --merge SHARD.json [SHARD.json ...] [--out OUT.json]

A Monte Carlo of the two-stage rule under the null, on synthetic cells only (it reads no unit and no outcome). Per
replicate and per family, every cell U(a, j) = μ_a + s_{c(a), j} + e(a, j) is drawn with e ~ N(0, σ_e²), σ_e = σ_pair /
√2 (σ_pair, the true SD of a paired difference within a cluster, is the grid's value), μ = 0 and s = 0 (the seed
effects cancel in every quantity read below, so they are set to 0). With the "arm x seed" scenario every method-arm
cell (A1, L1, H1, S1, S3, S4) gets an extra independent term of variance ρ σ_e² (ρ, the term's variance as a share of
the cell variance: 0.5 and 1 in the settings ``interaction``, GXB S-1), which a0 and R do not: N's pairs then
understate the method arms' noise (P1 §4, "What S-P assumes"). The grid's σ_pair is OLMo-2-7B's; two more scenarios
at ρ = 0 set Llama-3.1-8B's σ_pair at 1.5 and 1/1.5 times it, capped at the grid's top (GXB R-12; ``family_sigmas``);
in the others both families share it (an approximation under [B], listed in the settings).

1. **N** (P1 §3.3; GXB S-7): r_F,j = U(a0, j) - U(R_j, j) at 1101-1103 on both families; σ̂_pool = max(√[(2 SD(r_O)² +
   2 SD(r_L)²) / 4], the median of the 6 seed-matched pair SEs) on 4 df, computed as noise_reading.py's ``pooled``
   (a test checks the two agree on the same cells). N's cells carry per-prompt values (``n_prompt_values``: the cell's
   U plus centred prompt noise whose pair SE has expectation the settings' σ_eval,0, over the settings' P prompts), so
   the pair SEs are computed from prompts as the reader computes them. Its plan is printed (P1 §6.3's table), not used:
   block A is the same for every plan.
2. **Block A's σ̂_A** (P2 §10.2 with DESO3 V2; ``blinded_sigma.py``'s estimate and design): √2 × the pooled residual SD of
   the additive arm + seed model per cluster over block A's cells and the reused cells at 1101-1104 (R also at 1105);
   both families under [B], OLMo-2-7B (F1) under [C]; on a stopped family (``--design reduced``) A1, L1 and S3 add no cell.
3. **Block B's plan** by P1 §6.1 applied to σ̂_A: ≤ 4.5 plan A, ≤ 6.0 plan B9, else branch H (b) (ruling 4's first
   choice, its money taken as covered); review when the plan's removal MDE (the noise reader's MDE_FACTOR × σ̂_A) is
   above 2 × SESOI. Review tests nothing. Under [B] one plan governs both families.
4. **The claim test** per family on the plan's primary cells (the same draws as steps 1-2: block A's cells and N's are
   reused): HB-C as B16 (``scripts/stage1_s1/reading/reml.py``, loaded by path and pinned): one variance per arm by
   REML (Fisher scoring on log σ², the pre-registered start, the active-set floor 0.01 pp², the step clip, tol 1e-6,
   25 steps, and D-4's multi-start when the settings say "multi"), the two-arm sum rule for a two-arm cluster (plan
   B9's and H's {S1, S4}; a stopped family's {R, H1}), the paired mean on the common seeds, the seed part with its
   Satterthwaite df from the REML information, Student t two-sided p (B16's ``tdist``), Holm at 5% over the plan's
   primary contrasts (plan A P1-P6; B9 and H P1, P3, P6; on a stopped family the contrasts with A1, L1 or S3 drop).

The familywise rate is the U claims' rate (Holm on U); Φ's O and L words are not simulated (GXB R-11; a limit in the
settings). Printed per σ_pair and scenario: the plans' shares (by σ̂_A and by N); per family each primary contrast's size (its
unadjusted two-sided test at 5%, among the replicates where it is tested) and Holm rejection rate, the familywise
rate (any Holm rejection), the power at the settings' effects (8, 10, 12 pp: contrast k's true value δ, every other
contrast 0; Holm rejects k with a positive estimate) and P(better) (that, and the estimate ≥ SESOI); fits that stopped
at 25 steps. The reading rule (DES K6; GXB S-1: it applies to every simulated σ and every scenario, with or without
the interaction) is printed from the settings, with a reading line beside the largest familywise rate over them; this
script does not apply it to a real run.

**Approximations and limits (written in the settings, printed with the result):** the claim test is Holm on U only, as
a bound on B16's graphical family Φ over U, O, L and F (GXB S-2); a limit (GXB S-3): the crossed prompt (item) part of
each claim-test SE is omitted (no prompt-level data exist before block A), so df is the seed part's. REML runs vectorized over replicates with B16's
algorithm; the tests check it against B16's ``fit_cells`` (cells alone at their seed are left out, which B16 shows to
change nothing: leverage 1). Arm means and seed effects move no fit, no σ̂ and no plan, so one null draw serves every
power effect (the estimate shifts by δ).

**Determinism.** One stream per chunk of replicates (numpy PCG64 on SeedSequence([seed, chunk]); N's prompt noise on
SeedSequence([seed, chunk, 1])); the same draws serve
every σ_pair, scenario, option and design (common random numbers). The output is canonical JSON (sorted keys; rates to
6 decimals; counts as integers), byte-stable for a fixed settings file, option and design. ``--sigma`` runs a shard of
the grid; ``--merge`` joins shards into the document an unsharded run prints, byte for byte.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import pathlib
import sys
from fractions import Fraction

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# ===== pins =====
B16 = ROOT / "scripts/stage1_s1/reading"
FROZEN = {"reml": (B16 / "reml.py", "56f371e603358febb806e83037398d15b9d2f7e7ad5cb3fe173fbd7f528ffb9d"),
          "tdist": (B16 / "tdist.py", "6982a7b119e4a5eae34b5f45a62e0871ab5f3a8ca51cfb882cd31668c61c1fac")}
SETTINGS_KIND = "scale-78b sr2 simulation settings"
OUTPUT_KIND = "scale-78b sr2 simulation"
VERSION = 1
FAMILIES = ("llama31-8b", "olmo2-7b")
F1 = "olmo2-7b"                                            # the family under [C] (ruling 5)
OPTIONS = {"B": FAMILIES, "C": (F1,)}
FIT_ORDER = ("a0", "R", "A1", "L1", "H1", "S1", "S3", "S4")
METHODS = ("A1", "L1", "H1", "S1", "S3", "S4")
CLUSTER = {"R": "removal", "A1": "removal", "L1": "removal", "H1": "removal",
           "a0": "full", "S1": "full", "S3": "full", "S4": "full"}
STOPPED_DROPS = ("A1", "L1", "S3")                          # DESO2 item 36; P2 §2.2
CONTRASTS = {"P1": ("R", "A1"), "P2": ("R", "L1"), "P3": ("R", "H1"), "P4": ("a0", "S1"), "P5": ("S1", "S3"),
             "P6": ("S1", "S4")}
N_SEEDS = (1101, 1102, 1103)
BLOCK_A = {"R": (1101, 1102, 1103, 1104, 1105), "a0": (1101, 1102, 1103, 1104), "method": (1102, 1103, 1104)}
PLANS = {   # P1 §5's layout; B16's plan_b form for B9 and H (b): a0 outside the fit (settings/reading.json plan_b)
    "A": {"method_arms": METHODS, "method_seeds": tuple(range(1102, 1108)), "R_seeds": tuple(range(1101, 1108)),
          "fit_arms": FIT_ORDER, "primary": ("P1", "P2", "P3", "P4", "P5", "P6")},
    "B9": {"method_arms": ("A1", "H1", "S1", "S4"), "method_seeds": tuple(range(1102, 1111)),
           "R_seeds": tuple(range(1101, 1111)), "fit_arms": ("R", "A1", "H1", "S1", "S4"), "primary": ("P1", "P3", "P6")},
    "H": {"method_arms": ("A1", "H1", "S1", "S4"), "method_seeds": tuple(range(1102, 1114)),
          "R_seeds": tuple(range(1101, 1114)), "fit_arms": ("R", "A1", "H1", "S1", "S4"), "primary": ("P1", "P3", "P6")},
}
A0_SEEDS = tuple(range(1101, 1108))
PLAN_LABELS = ("A", "B9", "H", "review")
# ===== end of the pins =====


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(name: str):
    path, want = FROZEN[name]
    if sha256_bytes(path.read_bytes()) != want:
        raise SystemExit(f"B16's {name}.py differs from its pinned SHA-256: the simulation stops")
    label = f"b16_{name}_for_sr2_simulation"
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[label] = module                            # dataclasses resolve their module by name
    spec.loader.exec_module(module)
    return module


REML = _load("reml")
TDIST = _load("tdist")
SELF_SHA256 = sha256_bytes(pathlib.Path(__file__).read_bytes())


# ----- settings -------------------------------------------------------------------------------------------------------------


def read_settings(path) -> tuple[dict, str]:
    data = pathlib.Path(path).read_bytes()
    s = json.loads(data)
    need = {"kind", "version", "written_utc", "seed", "reps", "chunk", "sigma_pair_pp", "interaction", "power_effects_pp",
            "alpha", "sesoi_pp", "rule", "reml", "floor_pp2", "reading_rule", "approximations", "limits", "basis",
            "n_stage"}
    if not isinstance(s, dict) or s.get("kind") != SETTINGS_KIND or s.get("version") != VERSION or set(s) != need:
        raise SystemExit(f"not a {SETTINGS_KIND} file (version 1, exactly its keys)")
    if not (isinstance(s["reps"], int) and isinstance(s["chunk"], int) and s["chunk"] > 0 and s["reps"] > 0
            and s["reps"] % s["chunk"] == 0):
        raise SystemExit("reps and chunk are positive integers and chunk divides reps")
    if not (isinstance(s["seed"], int) and s["seed"] >= 0):
        raise SystemExit("seed is a non-negative integer")
    if not s["sigma_pair_pp"] or len(set(s["sigma_pair_pp"])) != len(s["sigma_pair_pp"]):
        raise SystemExit("sigma_pair_pp is a non-empty list of distinct decimal strings")
    names = [i["name"] for i in s["interaction"]]
    if not names or len(set(names)) != len(names):
        raise SystemExit("interaction names are distinct")
    if s["reml"].get("starts") not in ("multi", "pre-registered"):
        raise SystemExit("reml.starts is multi or pre-registered")
    float(Fraction(s["reading_rule"]["threshold_familywise"]))
    if not (isinstance(s["n_stage"].get("prompts"), int) and s["n_stage"]["prompts"] >= 2):
        raise SystemExit("n_stage.prompts is an integer of at least 2")
    if not all(set(i) == {"name", "method_variance_share", "llama_sigma_ratio"} and num(i["method_variance_share"]) >= 0
               and num(i["llama_sigma_ratio"]) > 0 for i in s["interaction"]):
        raise SystemExit("each scenario has name, method_variance_share >= 0 and llama_sigma_ratio > 0")
    return s, sha256_bytes(data)


def num(text) -> float:
    return float(Fraction(str(text)))


# ----- the designs ----------------------------------------------------------------------------------------------------------


def cell_superset() -> list:
    """Every cell any design or plan can read: a0 at 1101-1107, R at 1101-1113, each method arm at 1102-1113."""
    cells = [("a0", j) for j in A0_SEEDS] + [("R", j) for j in range(1101, 1114)]
    cells += [(m, j) for m in METHODS for j in range(1102, 1114)]
    return cells


CELLS = cell_superset()
INDEX = {c: i for i, c in enumerate(CELLS)}
IS_METHOD = np.array([a in METHODS for a, _ in CELLS])


def block_a_cells(stopped: bool) -> dict:
    """{cluster: [cells]} of block A plus the reused cells (blinded_sigma.design_cells' layout)."""
    methods = [m for m in METHODS if not (stopped and m in STOPPED_DROPS)]
    out = {"removal": [("R", j) for j in BLOCK_A["R"]], "full": [("a0", j) for j in BLOCK_A["a0"]]}
    for m in methods:
        out[CLUSTER[m]] += [(m, j) for j in BLOCK_A["method"]]
    return out


def residual_maker(cells: list) -> tuple[np.ndarray, int]:
    """(M, df): the additive arm + seed model's residual projector I - X X⁺ on the cells, and n - rank(X)."""
    arms = sorted({a for a, _ in cells})
    seeds = sorted({j for _, j in cells})
    x = np.array([[float(j == s) for s in seeds] + [float(a == b) for b in arms[1:]] for a, j in cells])
    m = np.eye(len(cells)) - x @ np.linalg.pinv(x)
    return m, int(len(cells) - np.linalg.matrix_rank(x))


def analysis_design(plan: str, stopped: bool) -> dict:
    """The claim test's fit per cluster (cells with a partner seed only) and its primary contrasts on one family."""
    p = PLANS[plan]
    arms = [a for a in p["fit_arms"] if not (stopped and a in STOPPED_DROPS)]
    seeds_of = {a: (A0_SEEDS if a == "a0" else p["R_seeds"] if a == "R" else p["method_seeds"]) for a in arms}
    clusters = {}
    for name in ("removal", "full"):
        c_arms = [a for a in arms if CLUSTER[a] == name]
        cells = [(a, j) for a in c_arms for j in seeds_of[a]]
        count = {}
        for _, j in cells:
            count[j] = count.get(j, 0) + 1
        cells = [(a, j) for a, j in cells if count[j] > 1]
        if len(c_arms) < 2:
            continue
        x, _, cell_arm = REML.design([(a, j, 0.0) for a, j in cells], tuple(c_arms))
        clusters[name] = {"arms": tuple(c_arms), "cells": cells, "index": np.array([INDEX[c] for c in cells]),
                          "x": x, "cell_arm": cell_arm, "two_arm": len(c_arms) == 2}
    contrasts = {}
    for k in p["primary"]:
        c, m = CONTRASTS[k]
        if c not in arms or m not in arms:
            continue
        common = tuple(j for j in seeds_of[c] if j in seeds_of[m])
        contrasts[k] = {"c": c, "m": m, "cluster": CLUSTER[c], "seeds": common,
                        "ci": np.array([INDEX[(c, j)] for j in common]), "mi": np.array([INDEX[(m, j)] for j in common])}
    return {"clusters": clusters, "contrasts": contrasts}


# ----- vectorized REML (B16's _fit_cells and _multi_start, over replicates) -------------------------------------------------


def _projection(x, w):
    wx = w[:, :, None] * x[None]
    a = np.swapaxes(wx, 1, 2) @ x[None]
    wxt = np.swapaxes(wx, 1, 2)
    p = -(wx @ np.linalg.solve(a, wxt))         # X'WX is positive definite on a connected design (B16: pinv)
    idx = np.arange(x.shape[0])
    p[:, idx, idx] += w
    return p


def _score_info(p, y, z):
    py = (p @ y[:, :, None])[:, :, 0]
    diag = np.diagonal(p, axis1=1, axis2=2)
    score = 0.5 * ((py ** 2) @ z - diag @ z)
    info = 0.5 * (z.T[None] @ ((p * p) @ z[None]))
    return score, info


def _fit(x, cell_arm, g, y, floor, tol, max_iter, clip, start_theta=None):
    """B16's _fit_cells (active set, LN-35's stop rule) on y (R x n): (theta, info_inv, converged, start)."""
    n = x.shape[0]
    z = np.zeros((n, g))
    z[np.arange(n), cell_arm] = 1.0
    hat = x @ np.linalg.pinv(x.T @ x) @ x.T
    leverage = np.diag(hat)
    residual = y - y @ hat.T
    h_arm = (1.0 - leverage) @ z
    identified = h_arm > 1e-9
    if not identified.all():
        raise SystemExit("a fit arm is not identified in the simulated design")
    start = ((residual ** 2) @ z) / h_arm
    theta = np.maximum(start if start_theta is None else start_theta, floor)
    reps = y.shape[0]
    active = np.ones(reps, dtype=bool)
    converged = np.zeros(reps, dtype=bool)
    for _ in range(max_iter):
        idx = np.nonzero(active)[0]
        if idx.size == 0:
            break
        th = theta[idx]
        p = _projection(x, 1.0 / th[:, cell_arm])
        score, info = _score_info(p, y[idx], z)
        score_log = th * score
        info_log = th[:, :, None] * info * th[:, None, :]
        above_before = th > floor
        free = above_before | (score_log > 0)
        block = np.where(free[:, :, None] & free[:, None, :], info_log, 0.0)
        step = (np.linalg.pinv(block, rcond=1e-10) @ np.where(free, score_log, 0.0)[:, :, None])[:, :, 0]
        step = np.clip(step, -clip, clip)
        new = np.maximum(th * np.exp(step), floor)
        above = new > floor
        largest = np.where(above, np.abs(step), 0.0).max(axis=1)
        newly = np.any(above_before & ~above, axis=1)
        done = (largest < tol) & ~newly
        theta[idx] = new
        converged[idx[done]] = True
        active[idx[done]] = False
    p = _projection(x, 1.0 / theta[:, cell_arm])
    _, info = _score_info(p, y, z)
    return theta, np.linalg.pinv(info, rcond=1e-10), converged, start


def _loglik(basis, y, theta, cell_arm):
    k = basis
    w = y @ k
    v = theta[:, cell_arm]
    c = np.linalg.cholesky((k.T[None] * v[:, None, :]) @ k[None])
    zz = np.linalg.solve(c, w[:, :, None])[:, :, 0]
    return -np.log(np.diagonal(c, axis1=1, axis2=2)).sum(axis=1) - 0.5 * (zz ** 2).sum(axis=1)


def reml_batch(cluster: dict, y, floor: float, opts: dict):
    """(sigma2 R x g, info_inv R x g x g, converged R) of one cluster's REML fit on y (R x n), B16's algorithm."""
    x, cell_arm, g = cluster["x"], cluster["cell_arm"], len(cluster["arms"])
    theta, inv, conv, start = _fit(x, cell_arm, g, y, floor, opts["tol"], opts["max_iter"], opts["clip"])
    if opts["starts"] != "multi":
        return theta, inv, conv
    u, sv, _ = np.linalg.svd(x, full_matrices=True)
    basis = u[:, int((sv > 1e-10 * sv[0]).sum()):]
    pre_ll = _loglik(basis, y, theta, cell_arm)
    best = (theta.copy(), inv.copy(), conv.copy(), pre_ll.copy())
    base = np.maximum(start, floor)
    for size in range(1, g + 1):
        for combo in itertools.combinations(range(g), size):
            theta0 = base.copy()
            theta0[:, list(combo)] = floor
            t2, i2, c2, _ = _fit(x, cell_arm, g, y, floor, opts["tol"], opts["max_iter"], opts["clip"], start_theta=theta0)
            ll = _loglik(basis, y, t2, cell_arm)
            better = ll > best[3]
            for held, new in zip(best, (t2, i2, c2, ll)):
                held[better] = new[better]
    take = best[3] > pre_ll + opts["ll_tol"]
    theta[take], inv[take], conv[take] = best[0][take], best[1][take], best[2][take]
    return theta, inv, conv


# ----- one replicate set ----------------------------------------------------------------------------------------------------


def plan_of(sigma2, settings: dict) -> np.ndarray:
    """P1 §6.1 on σ̂² (exact decimals as floats; the comparisons on squares, as the noise reader does)."""
    rule = settings["rule"]
    a, b = num(rule["threshold_A_pp"]) ** 2, num(rule["threshold_B9_pp"]) ** 2
    plan = np.where(sigma2 <= a, "A", np.where(sigma2 <= b, "B9", "H")).astype(object)
    ceiling = (2 * settings["sesoi_pp"]) ** 2
    for name, factor in rule["mde_factor"].items():
        plan[(plan == name) & (num(factor) ** 2 * sigma2 > ceiling)] = "review"
    return plan


def holm(pvals: np.ndarray, alpha: float) -> np.ndarray:
    """Holm's step-down at alpha over the columns (R x m): rejection flags."""
    m = pvals.shape[1]
    order = np.argsort(pvals, axis=1, kind="stable")
    sorted_p = np.take_along_axis(pvals, order, axis=1)
    ok = sorted_p <= alpha / (m - np.arange(m))[None, :]
    keep = np.cumprod(ok, axis=1).astype(bool)
    out = np.zeros_like(keep)
    np.put_along_axis(out, order, keep, axis=1)
    return out


def p_two_sided(t: np.ndarray, df: np.ndarray) -> np.ndarray:
    return np.array([TDIST.t_two_sided(float(a), float(b)) for a, b in zip(t, df)])


def claim_test(design: dict, y, settings: dict) -> dict:
    """One family's claim test on y (R x len(CELLS)) under one plan: per contrast est, se, df, p; refused flags."""
    floor = num(settings["floor_pp2"])
    opts = settings["_reml"]
    fits = {}
    nonconverged = np.zeros(y.shape[0], dtype=int)
    for name, cl in design["clusters"].items():
        yc = y[:, cl["index"]]
        if cl["two_arm"]:
            fits[name] = None
        else:
            s2, inv, conv = reml_batch(cl, yc, floor, opts)
            fits[name] = (s2, inv)
            nonconverged += ~conv
    out = {}
    for k, ct in design["contrasts"].items():
        d = y[:, ct["ci"]] - y[:, ct["mi"]]
        j = len(ct["seeds"])
        est = d.mean(axis=1)
        cl = design["clusters"][ct["cluster"]]
        if fits[ct["cluster"]] is None:
            total = np.maximum(d.var(axis=1, ddof=1), floor)
            v, df = total / j, np.full(y.shape[0], float(j - 1))
        else:
            s2, inv = fits[ct["cluster"]]
            i, m = cl["arms"].index(ct["c"]), cl["arms"].index(ct["m"])
            v = (s2[:, i] + s2[:, m]) / j
            var_v = (inv[:, i, i] + inv[:, m, m] + 2.0 * inv[:, i, m]) / j ** 2
            with np.errstate(divide="ignore", invalid="ignore"):
                df = np.where(var_v > 0, 2.0 * v * v / var_v, np.inf)
        se = np.sqrt(v)
        refused = ~np.isfinite(df) | ~(se > 0)
        safe_df = np.where(refused, 1.0, df)
        safe_se = np.where(refused, 1.0, se)
        out[k] = {"est": est, "se": safe_se, "df": safe_df, "refused": refused,
                  "p": np.where(refused, 1.0, p_two_sided(est / safe_se, safe_df))}
    return {"contrasts": out, "nonconverged": nonconverged}


def new_tally(contrasts, effects) -> dict:
    return {"familywise": 0, "nonconverged_fits": 0, "refused": 0,
            "contrasts": {k: {"tested": 0, "size": 0, "holm": 0} for k in contrasts},
            "power": {e: {k: 0 for k in contrasts} for e in effects}, "better": {e: {k: 0 for k in contrasts} for e in effects}}


def cell_sd(sigma_pair: float, share: float) -> np.ndarray:
    """Each cell's SD: σ_e = σ_pair / √2; a method-arm cell's √(1 + ρ) σ_e under the arm x seed scenario, ρ the term's
    variance as a share of the cell variance (GXB S-1)."""
    return sigma_pair / math.sqrt(2.0) * np.where(IS_METHOD, math.sqrt(1.0 + share), 1.0)


def n_prompt_values(y_all: dict, eta: np.ndarray, sigma_eval0: float) -> dict:
    """N's cells per prompt: {family: {(role, j): R x P values in pp}}. Each cell's prompt values are its U plus
    centred prompt noise τ (η_p - η̄), τ = σ_eval,0 √(P / 2), so their mean is the cell's U and a seed-matched pair's
    prompt-clustered SE has expectation σ_eval,0² (eta: R x 2 families x 2 roles x 3 seeds x P standard normals)."""
    p = eta.shape[-1]
    tau = sigma_eval0 * math.sqrt(p / 2.0)
    out = {}
    for i, f in enumerate(FAMILIES):
        out[f] = {}
        for k, role in enumerate(("a0", "R")):
            for m, j in enumerate(N_SEEDS):
                e = eta[:, i, k, m, :]
                out[f][(role, j)] = y_all[f][:, INDEX[(role, j)]][:, None] + tau * (e - e.mean(axis=1, keepdims=True))
    return out


def sigma_pool_sq(prompts: dict) -> np.ndarray:
    """N's σ̂_pool² per replicate exactly as scripts/scale78b/noise_reading.py's ``pooled`` (P1 §3.3; GXB S-7):
    max(√[(2 SD(r_O)² + 2 SD(r_L)²) / 4], the median of the 6 seed-matched pair SEs)², r_F,j = U(a0, j) - U(R_j, j) at
    1101-1103, each pair SE² the prompt-clustered SE² of the per-prompt difference (variance over the prompts, ddof 1,
    over P), the median of an even count the mean of the two middle SEs (gate_b_reading.median_term)."""
    sd2, se2 = [], []
    for f in FAMILIES:
        r = []
        for j in N_SEEDS:
            d = prompts[f][("a0", j)] - prompts[f][("R", j)]
            r.append(d.mean(axis=1))
            se2.append(d.var(axis=1, ddof=1) / d.shape[1])
        sd2.append(np.stack(r, axis=1).var(axis=1, ddof=1))
    pool = sum(2 * v for v in sd2) / (2 * len(FAMILIES))
    se2 = np.sort(np.stack(se2, axis=1), axis=1)
    n = se2.shape[1]
    median = (np.sqrt(se2[:, n // 2 - 1]) + np.sqrt(se2[:, n // 2])) / 2
    return np.maximum(pool, median ** 2)


def sigma_a_sq(y_all: dict, option: str, stopped: set) -> tuple[np.ndarray, int]:
    """(σ̂_A² per replicate, df): 2 × Σ RSS / Σ df of the additive fits per cluster over the option's families
    (blinded_sigma.pooled_sigma's estimate)."""
    rss, df = 0.0, 0
    for f in OPTIONS[option]:
        for cells in block_a_cells(f in stopped).values():
            m, d = residual_maker(cells)
            yc = y_all[f][:, [INDEX[c] for c in cells]]
            rss = rss + ((yc @ m) * yc).sum(axis=1)
            df += d
    return 2 * rss / df, df


def family_sigmas(sigma_text: str, scenario: dict, settings: dict) -> dict:
    """Each family's true σ_pair in one scenario (GXB R-12): the grid's σ is OLMo-2-7B's; Llama-3.1-8B's is
    llama_sigma_ratio times it, capped at the grid's top."""
    olmo = num(sigma_text)
    top = max(num(x) for x in settings["sigma_pair_pp"])
    return {"olmo2-7b": olmo, "llama31-8b": min(olmo * num(scenario["llama_sigma_ratio"]), top)}


def run_chunk(z: np.ndarray, eta: np.ndarray, sigmas: dict, share: float, option: str, stopped: set, settings: dict,
              tallies: dict, plans: dict, designs: dict) -> None:
    """One chunk of replicates (z: R x 2 x len(CELLS) standard normals; eta: N's prompt noise) at one σ_pair and
    scenario, added to the tallies."""
    y_all = {f: z[:, i, :] * cell_sd(sigmas[f], share)[None, :] for i, f in enumerate(FAMILIES)}
    n_plan = plan_of(sigma_pool_sq(n_prompt_values(y_all, eta, num(settings["n_stage"]["sigma_eval0_pp"]))), settings)
    a_plan = plan_of(sigma_a_sq(y_all, option, stopped)[0], settings)
    for label in PLAN_LABELS:
        plans["sigma_A"][label] += int((a_plan == label).sum())
        plans["N"][label] += int((n_plan == label).sum())
    alpha = num(settings["alpha"])
    sesoi = float(settings["sesoi_pp"])
    for plan in ("A", "B9", "H"):
        rows = np.nonzero(a_plan == plan)[0]
        if rows.size == 0:
            continue
        for f in OPTIONS[option]:
            design = designs[(plan, f in stopped)]
            res = claim_test(design, y_all[f][rows], settings)
            names = list(design["contrasts"])
            t = tallies[f]
            p = np.stack([res["contrasts"][k]["p"] for k in names], axis=1)
            rej = holm(p, alpha)
            t["familywise"] += int(rej.any(axis=1).sum())
            t["nonconverged_fits"] += int(res["nonconverged"].sum())
            t["refused"] += int(sum(res["contrasts"][k]["refused"].sum() for k in names))
            for col, k in enumerate(names):
                c = res["contrasts"][k]
                t["contrasts"][k]["tested"] += int((~c["refused"]).sum())
                t["contrasts"][k]["size"] += int(((c["p"] < alpha) & ~c["refused"]).sum())
                t["contrasts"][k]["holm"] += int(rej[:, col].sum())
                for e in settings["power_effects_pp"]:
                    shifted = c["est"] + num(e)
                    p2 = p.copy()
                    p2[:, col] = np.where(c["refused"], 1.0, p_two_sided(shifted / c["se"], c["df"]))
                    hit = holm(p2, alpha)[:, col] & (shifted > 0)
                    t["power"][e][k] += int(hit.sum())
                    t["better"][e][k] += int((hit & (shifted >= sesoi)).sum())


def rate(count: int, total: int):
    return round(count / total, 6) if total else None


def chunk_normals(seed: int, chunk_index: int, size: int) -> np.ndarray:
    """The standard normals of one chunk: size x 2 families x len(CELLS), from PCG64 on SeedSequence([seed, chunk])."""
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, chunk_index])))
    return rng.standard_normal((size, len(FAMILIES), len(CELLS)))


def chunk_prompt_normals(seed: int, chunk_index: int, size: int, prompts: int) -> np.ndarray:
    """N's prompt noise of one chunk: size x 2 families x 2 roles (a0, R) x 3 seeds x P, from PCG64 on
    SeedSequence([seed, chunk, 1]) (a stream apart from the cells')."""
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, chunk_index, 1])))
    return rng.standard_normal((size, len(FAMILIES), 2, len(N_SEEDS), prompts))


def simulate_row(index: int, settings: dict, option: str, stopped: set) -> dict:
    sigma_text = settings["sigma_pair_pp"][index]
    reps, chunk = settings["reps"], settings["chunk"]
    families = OPTIONS[option]
    designs = {(plan, s): analysis_design(plan, s) for plan in ("A", "B9", "H") for s in (False, True)}
    scenarios = {}
    for scenario in settings["interaction"]:
        share = num(scenario["method_variance_share"])
        sigmas = family_sigmas(sigma_text, scenario, settings)
        names = {f: list(designs[("A", f in stopped)]["contrasts"]) for f in families}
        allk = {f: [k for k in CONTRASTS if any(k in designs[(p, f in stopped)]["contrasts"] for p in ("A", "B9", "H"))]
                for f in families}
        tallies = {f: new_tally(allk[f], settings["power_effects_pp"]) for f in families}
        plans = {"sigma_A": {k: 0 for k in PLAN_LABELS}, "N": {k: 0 for k in PLAN_LABELS}}
        for c in range(reps // chunk):
            z = chunk_normals(settings["seed"], c, chunk)
            eta = chunk_prompt_normals(settings["seed"], c, chunk, settings["n_stage"]["prompts"])
            run_chunk(z, eta, sigmas, share, option, stopped, settings, tallies, plans, designs)
        fam_out = {}
        for f in families:
            t = tallies[f]
            fam_out[f] = {
                "familywise_count": t["familywise"], "familywise_rate": rate(t["familywise"], reps),
                "contrasts": {k: {"tested": v["tested"], "size_count": v["size"], "size_rate": rate(v["size"], v["tested"]),
                                  "holm_count": v["holm"], "holm_rate": rate(v["holm"], reps)}
                              for k, v in t["contrasts"].items()},
                "power": {e: {k: rate(v, reps) for k, v in t["power"][e].items()} for e in settings["power_effects_pp"]},
                "better": {e: {k: rate(v, reps) for k, v in t["better"][e].items()} for e in settings["power_effects_pp"]},
                "nonconverged_fits": t["nonconverged_fits"], "refused_contrasts": t["refused"], "primary_under_plan_A": names[f]}
        scenarios[scenario["name"]] = {
            "method_variance_share": scenario["method_variance_share"],
            "llama_sigma_ratio": scenario["llama_sigma_ratio"],
            "sigma_pair_pp_by_family": {f: round(v, 6) for f, v in sorted(sigmas.items())},
            "plan_by_sigma_A": {k: rate(v, reps) for k, v in plans["sigma_A"].items()},
            "plan_by_N": {k: rate(v, reps) for k, v in plans["N"].items()},
            "families": fam_out}
    return {"sigma_index": index, "sigma_pair_pp": sigma_text, "scenarios": scenarios}


def header(settings: dict, settings_sha256: str, option: str, design: str, stopped: list) -> dict:
    return {"kind": OUTPUT_KIND, "version": VERSION, "script_sha256": SELF_SHA256, "settings_sha256": settings_sha256,
            "frozen_sha256": {k: v[1] for k, v in FROZEN.items()}, "option": option,
            "design": {"name": design, "stopped": sorted(stopped)}, "families": list(OPTIONS[option]),
            "reps": settings["reps"], "seed": settings["seed"], "reml_starts": settings["reml"]["starts"],
            "approximations": settings["approximations"], "limits": settings["limits"], "n_stage": settings["n_stage"],
            "reading_rule": settings["reading_rule"]}


def summarize(doc: dict, n_sigma: int) -> dict:
    rows = doc["rows"]
    if sorted(r["sigma_index"] for r in rows) != list(range(n_sigma)):
        raise SystemExit("the rows do not cover the settings' σ grid exactly once")
    best = None
    for r in rows:
        for name, sc in r["scenarios"].items():
            for f, v in sc["families"].items():
                key = (v["familywise_count"], -r["sigma_index"], name, f)
                if best is None or key > best[0]:
                    best = (key, {"sigma_pair_pp": r["sigma_pair_pp"], "scenario": name, "family": f,
                                  "familywise_rate": v["familywise_rate"], "familywise_count": v["familywise_count"]})
    reps = doc["reps"]
    top = best[1]
    threshold = num(doc["reading_rule"]["threshold_familywise"])
    p = top["familywise_count"] / reps
    scenarios = sorted({name for r in rows for name in r["scenarios"]})
    refused = sum(v["refused_contrasts"] for r in rows for sc in r["scenarios"].values() for v in sc["families"].values())
    nonconverged = sum(v["nonconverged_fits"] for r in rows for sc in r["scenarios"].values()
                       for v in sc["families"].values())
    line = (f"The reading rule applies to every simulated sigma ({len(rows)}) and every scenario ({', '.join(scenarios)}), "
            f"with or without the interaction and at either family ratio: the familywise rate is the U claims' rate (Holm on "
            f"U; Phi's O and L words are not simulated); the largest over them is {top['familywise_rate']} "
            f"(sigma_pair {top['sigma_pair_pp']} pp, scenario {top['scenario']}, {top['family']}); a rate above "
            f"{doc['reading_rule']['threshold_familywise']} at any of them means SR-2 is not adopted and N decides alone "
            "(DES K6; GXB S-1). The lead applies it.")
    return {"max_familywise": top, "monte_carlo_se_of_max": round(math.sqrt(p * (1 - p) / reps), 6),
            "threshold_familywise": doc["reading_rule"]["threshold_familywise"], "reading_line": line,
            "scenarios_read": scenarios, "max_above_threshold": bool(p > threshold),
            "refused_contrasts_total": refused, "nonconverged_fits_total": nonconverged,
            "refused_note": ("a refused contrast (no finite df) counts as not rejected, where B16 would refuse the reading: "
                             "the familywise rate is understated by at most refused_contrasts_total / reps (SV-7)"),
            "note": "the reading rule is the lead's to apply (DES K6); this flag is the mechanical comparison only"}


def render(doc: dict) -> bytes:
    return (json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def simulate(settings_path, option: str, design: str, stopped: list, indices=None) -> dict:
    settings, digest = read_settings(settings_path)
    if option not in OPTIONS:
        raise SystemExit(f"--option is one of {sorted(OPTIONS)}")
    stopped = sorted(set(stopped))
    if design == "full" and stopped:
        raise SystemExit("--stopped needs --design reduced")
    if design == "reduced" and (not stopped or not set(stopped) <= set(OPTIONS[option])):
        raise SystemExit(f"--design reduced needs --stopped with families of option {option} ({list(OPTIONS[option])})")
    if design not in ("full", "reduced"):
        raise SystemExit("--design is full or reduced")
    r = settings["reml"]
    settings["_reml"] = {"tol": float(r["tol"]), "max_iter": int(r["max_iter"]), "clip": float(r["step_clip_log"]),
                         "starts": r["starts"], "ll_tol": float(r["multi_start_ll_tolerance"])}
    n = len(settings["sigma_pair_pp"])
    indices = list(range(n)) if indices is None else sorted(set(indices))
    if not indices or any(not (0 <= i < n) for i in indices):
        raise SystemExit(f"--sigma names indices of the settings' grid (0-{n - 1})")
    doc = header(settings, digest, option, design, stopped)
    with np.errstate(all="ignore"):                       # this Mac's numpy prints spurious matmul warnings (B16)
        doc["rows"] = [simulate_row(i, settings, option, set(stopped)) for i in indices]
    if len(indices) == n:
        doc["summary"] = summarize(doc, n)
    else:
        doc["shard"] = indices
        doc["grid_size"] = n
    return doc


def merge(paths: list) -> dict:
    docs = [json.loads(pathlib.Path(p).read_bytes()) for p in paths]
    heads = [{k: v for k, v in d.items() if k not in ("rows", "shard", "summary", "grid_size")} for d in docs]
    if any(h != heads[0] for h in heads) or any("grid_size" not in d for d in docs):
        raise SystemExit("the shards differ in their header (script, settings, option, design) or are not shards")
    n = docs[0]["grid_size"]
    if any(d["grid_size"] != n for d in docs):
        raise SystemExit("the shards name different grid sizes")
    doc = dict(heads[0])
    doc["rows"] = sorted((r for d in docs for r in d["rows"]), key=lambda r: r["sigma_index"])
    doc["summary"] = summarize(doc, n)
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--settings")
    ap.add_argument("--option")
    ap.add_argument("--design", default="full")
    ap.add_argument("--stopped", default="")
    ap.add_argument("--sigma", help="comma-separated grid indices (a shard)")
    ap.add_argument("--merge", nargs="+")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out) if args.out else None
    if out is not None and out.exists():
        raise SystemExit("--out exists: an output is written once")
    if args.merge:
        if args.settings or args.option or args.sigma:
            raise SystemExit("--merge takes shard files only")
        doc = merge(args.merge)
    else:
        if not (args.settings and args.option):
            raise SystemExit("--settings and --option are required")
        stopped = [s for s in args.stopped.split(",") if s]
        indices = [int(i) for i in args.sigma.split(",")] if args.sigma else None
        doc = simulate(args.settings, args.option, args.design, stopped, indices)
    data = render(doc)
    if out is not None:
        out.write_bytes(data)
    sys.stdout.write(data.decode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
