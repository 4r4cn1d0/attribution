"""HB-C and HB: one residual variance per arm by REML (REV3 section 3.2; AMD section A.3; LN-35).

Model: y(a, j) = mu_a + s_{g(a), j} + e(a, j), Var e(a, j) = sigma^2_a. The seed effect s is one per design
cluster under HB-C (``fit_cells`` is then called once per cluster: HB-C shares no parameter across the clusters,
REV3 3.2) and one for all arms under HB. mu and s are fixed effects.

REML: Fisher scoring on log sigma^2. Start at each arm's residual mean square (the OLS residual sum of squares
over the arm's cells divided by the arm's residual-df share, sum of 1 - leverage). Each step solves
I_log step = score_log with score_log,g = sigma^2_g (1/2 y'P Z_g P y - 1/2 tr(P Z_g)) and
I_log,gh = sigma^2_g sigma^2_h 1/2 tr(P Z_g P Z_h), P = W - W X (X'WX)^-1 X'W. A step is clipped to |step| <= 2
on the log scale (a safeguard that changes the path, never the fixed point). After each step sigma^2 is floored
at the endpoint's floor (LN-35: U and O 0.01 pp^2, L 1e-8 nats^2, given by the caller). Stop when the largest
step among the arms above the floor is below tol (1e-6), or after max_iter (25) steps (LN-35); tol, max_iter and the
clip come from the pinned settings through ``options``. A step in which an arm newly reaches the floor never ends
the fit, because the free set has just changed (verify-stats F1). An arm at the floor is reported; there is no
re-fit and no change of model (AMD A.3).

The floor as an active set: an arm at the floor whose score points below the floor takes no step, and the free
arms' step solves their own block of the information matrix. The fixed point is then the REML maximum subject
to the floor. (The planning routine solved for every arm and floored afterwards; at its fixed point the free arms'
scores are not zero when an arm is floored. ``planning_floor=True`` reproduces it for the cross-check.)

The information matrix returned is on the sigma^2 scale (I = D^-1 I_log D^-1, D = diag sigma^2); its
pseudo-inverse gives Var-hat of a contrast's seed part (AMD A.4). A cell alone at its (cluster, seed) has
leverage 1 and contributes nothing (REV3 3.2 "seeds without a partner").

The two-arm cluster (REV3 3.5 item 1; review-statistics 3.3): with seed fixed effects every error contrast is a
function of d_j = y(1, j) - y(2, j), so only sigma^2_1 + sigma^2_2 is identified; ``fit_cells`` then returns the
sum (the sample variance of d over the paired seeds, ddof 1, which is its REML estimate) with ``two_arm`` set,
no split, and seed df J - 1. A two-arm fit never prints a split. The sum is floored at the one endpoint floor
(0.01 pp^2 for U and O), not at twice it: the floor is a bound on a variance that the data cannot place below it,
and the sum is the one variance the fit holds (verify-stats N2; negligible either way).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

STEP_CLIP = 2.0


class RemlError(ValueError):
    """An input the fit does not define."""


@dataclass(frozen=True)
class RemlFit:
    arms: tuple[str, ...]
    sigma2: dict                 # arm -> sigma^2 (the sum under ``two_arm``, under the key "sum")
    info_inv: np.ndarray         # pseudo-inverse of the REML information on the sigma^2 scale (A x A); empty if two_arm
    at_floor: tuple[str, ...]
    iterations: int
    converged: bool
    residual_df: float
    residual_df_by_arm: dict
    start: dict
    not_identified: tuple[str, ...]
    two_arm: bool
    floor: float
    pairs: int = 0               # the number of paired seeds under ``two_arm``
    steps: tuple = field(default_factory=tuple)


def _check_cells(cells):
    if not cells:
        raise RemlError("no cells")
    seen = set()
    for arm, seed, value in cells:
        if not isinstance(arm, str) or not isinstance(seed, int):
            raise RemlError("a cell is (arm: str, seed: int, value)")
        if (arm, seed) in seen:
            raise RemlError(f"the cell ({arm}, {seed}) repeats")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
            raise RemlError(f"the cell ({arm}, {seed}) is not a finite number")
        seen.add((arm, seed))


def design(cells, arms):
    """X (n x (A + S - 1)): arm indicators and seed indicators with the first seed dropped; y; the arm index."""
    seeds = sorted({seed for _, seed, _ in cells})
    arm_index = {arm: i for i, arm in enumerate(arms)}
    seed_index = {seed: i for i, seed in enumerate(seeds)}
    n, a, s = len(cells), len(arms), len(seeds)
    x = np.zeros((n, a + s - 1))
    y = np.zeros(n)
    cell_arm = np.zeros(n, dtype=int)
    for i, (arm, seed, value) in enumerate(cells):
        if arm not in arm_index:
            raise RemlError(f"the arm {arm} is not in the fit")
        x[i, arm_index[arm]] = 1.0
        if seed_index[seed] > 0:
            x[i, a + seed_index[seed] - 1] = 1.0
        y[i] = value
        cell_arm[i] = arm_index[arm]
    return x, y, cell_arm


def _two_arm(cells, arms, floor):
    by_arm = {arm: {} for arm in arms}
    for arm, seed, value in cells:
        by_arm[arm][seed] = value
    common = sorted(set(by_arm[arms[0]]) & set(by_arm[arms[1]]))
    if len(common) < 2:
        raise RemlError("a two-arm cluster needs at least two paired seeds")
    d = np.array([by_arm[arms[0]][j] - by_arm[arms[1]][j] for j in common])
    total = float(d.var(ddof=1))
    at_floor = total <= floor
    total = max(total, floor)
    return RemlFit(arms=tuple(arms), sigma2={"sum": total}, info_inv=np.zeros((0, 0)),
                   at_floor=("sum",) if at_floor else (), iterations=0, converged=True,
                   residual_df=float(len(common) - 1), residual_df_by_arm={arm: float("nan") for arm in arms},
                   start={"sum": float(d.var(ddof=1))}, not_identified=tuple(arms), two_arm=True, floor=floor,
                   pairs=len(common))


def _projection(x, w):
    """P = W - W X (X'WX)^-1 X'W for W = diag(w)."""
    with np.errstate(all="ignore"):                      # this Mac's numpy prints spurious matmul warnings
        wx = w[:, None] * x
        a_inv = np.linalg.pinv(x.T @ wx)
        p = -(wx @ a_inv @ wx.T)
    p[np.diag_indices_from(p)] += w
    if not np.all(np.isfinite(p)):
        raise RemlError("the REML projection is not finite")
    return p


def _score_info(p, y, z):
    """The REML score and expected information on the sigma^2 scale (Z: n x G group indicators)."""
    py = p @ y
    score = 0.5 * ((py ** 2) @ z - np.diag(p) @ z)
    info = 0.5 * (z.T @ (p * p) @ z)
    return score, info


def _step(score_log, info_log, identified, above, planning_floor, clip):
    """One Fisher-scoring step on log sigma^2. Active set (the reading): an arm at the floor whose score points
    below it leaves the step, and the free arms' step solves their own block of the information, so the fixed point
    is the REML maximum subject to the floor. ``planning_floor``: the planning routine's form (AMD SIM
    reml_hetero), one full solve for every arm and then the floor; kept for the cross-check only."""
    if planning_floor:
        free = identified
    else:
        free = identified & (above | (score_log > 0))
    step = np.zeros_like(score_log)
    if free.any():
        block = info_log[np.ix_(free, free)]
        step[free] = np.linalg.pinv(block, rcond=1e-10) @ score_log[free]
    return np.clip(step, -clip, clip)


FLOOR_MODES = ("active_set", "planning")


def options(cfg: dict) -> dict:
    """The fit's keyword arguments from the pinned settings' 'reml' block: tol, max_iter, the log-step clip and the
    floor mode ('active_set' = the reading; 'planning' = the planning routine's form). The reading passes these
    into every ``fit_cells`` call, so the code holds no second copy (verify-stats F4; verify-code F5)."""
    r = cfg["reml"]
    if r.get("floor_mode") not in FLOOR_MODES:
        raise RemlError(f"the settings' reml.floor_mode is not one of {FLOOR_MODES}")
    return {"tol": float(r["tol"]), "max_iter": int(r["max_iter"]), "clip": float(r["step_clip_log"]),
            "planning_floor": r["floor_mode"] == "planning"}


def fit_cells(cells, arms, floor, tol=1e-6, max_iter=25, clip=STEP_CLIP, two_arm_rule=True, planning_floor=False) -> RemlFit:
    """REML with one variance per arm on the cells (arm, seed, value) of ONE seed-effect block (a cluster under
    HB-C; every arm under HB). ``arms`` fixes the parameter order. ``two_arm_rule=False`` runs the generic scoring
    on two arms (the tests' check that only the sum moves); ``planning_floor=True`` reproduces the planning routine's
    floor handling (the tests' cross-check). The reading always keeps the rule and the active set."""
    with np.errstate(all="ignore"):                      # this Mac's numpy prints spurious matmul warnings
        fit = _fit_cells(cells, arms, floor, tol, max_iter, clip, two_arm_rule, planning_floor)
    if not fit.two_arm and not (np.all(np.isfinite(list(fit.sigma2.values()))) and np.all(np.isfinite(fit.info_inv))):
        raise RemlError("the REML fit is not finite")
    return fit


def _fit_cells(cells, arms, floor, tol, max_iter, clip, two_arm_rule=True, planning_floor=False) -> RemlFit:
    _check_cells(cells)
    arms = tuple(arms)
    if len(set(arms)) != len(arms) or len(arms) < 2:
        raise RemlError("a fit needs at least two distinct arms")
    if not (isinstance(floor, (int, float)) and floor > 0):
        raise RemlError("the floor is a positive number in the endpoint's own unit")
    present = {arm for arm, _, _ in cells}
    if present != set(arms):
        raise RemlError("every arm of the fit needs at least one cell, and every cell an arm of the fit")
    if len(arms) == 2 and two_arm_rule:
        return _two_arm(cells, arms, floor)
    x, y, cell_arm = design(cells, arms)
    n, g = len(y), len(arms)
    z = np.zeros((n, g))
    z[np.arange(n), cell_arm] = 1.0
    with np.errstate(all="ignore"):
        hat = x @ np.linalg.pinv(x.T @ x) @ x.T
    if not np.all(np.isfinite(hat)):
        raise RemlError("the design's projection is not finite")
    leverage = np.diag(hat)
    residual = y - hat @ y
    h_arm = (1.0 - leverage) @ z
    identified = h_arm > 1e-9
    rss_arm = (residual ** 2) @ z
    start = np.where(identified, rss_arm / np.where(identified, h_arm, 1.0), floor)
    theta = np.maximum(start, floor)
    steps, converged, it = [], False, 0
    for it in range(1, max_iter + 1):
        p = _projection(x, 1.0 / theta[cell_arm])
        score, info = _score_info(p, y, z)
        score_log = theta * score
        info_log = theta[:, None] * info * theta[None, :]
        above_before = theta > floor
        step = _step(score_log, info_log, identified, above_before, planning_floor, clip)
        theta = np.maximum(theta * np.exp(step), floor)
        above = theta > floor
        largest = float(np.abs(step[above]).max()) if above.any() else 0.0
        steps.append(largest)
        # A step in which an arm newly reaches the floor never ends the fit: the free set has just changed, and the
        # free arms' steps were computed with that arm still free, so a small largest step says nothing about the
        # new fixed point (verify-stats F1: the rule as first built stopped with a free arm's log-score up to 0.99).
        newly_floored = bool(np.any(above_before & ~above))
        if largest < tol and not newly_floored:
            converged = True
            break
    p = _projection(x, 1.0 / theta[cell_arm])
    _, info = _score_info(p, y, z)
    info_inv = np.linalg.pinv(info, rcond=1e-10)
    return RemlFit(arms=arms, sigma2={arm: float(theta[i]) for i, arm in enumerate(arms)}, info_inv=info_inv,
                   at_floor=tuple(arm for i, arm in enumerate(arms) if theta[i] <= floor), iterations=it,
                   converged=converged, residual_df=float(n - np.linalg.matrix_rank(x)),
                   residual_df_by_arm={arm: float(h_arm[i]) for i, arm in enumerate(arms)},
                   start={arm: float(start[i]) for i, arm in enumerate(arms)},
                   not_identified=tuple(arm for i, arm in enumerate(arms) if not identified[i]),
                   two_arm=False, floor=float(floor), steps=tuple(steps))


def reml_loglik(cells, arms, sigma2):
    """The REML log-likelihood (up to a constant) at sigma^2 (arm -> value): for the tests' finite differences."""
    x, y, cell_arm = design(cells, arms)
    v = np.array([sigma2[arm] for arm in arms])[cell_arm]
    w = 1.0 / v
    p = _projection(x, w)
    xtwx = x.T @ (w[:, None] * x)
    sign, logdet = np.linalg.slogdet(xtwx)
    if sign <= 0:
        raise RemlError("the design is not connected: X'WX is singular")
    return float(-0.5 * np.log(v).sum() - 0.5 * logdet - 0.5 * y @ p @ y)


def seed_variance(fit: RemlFit, c: str, m: str, pairs: int):
    """V_seed = (sigma^2_c + sigma^2_m)/J and its Satterthwaite df from the information (AMD A.4); under the
    two-arm rule the sum over J with J - 1 df (REV3 3.5)."""
    if fit.two_arm:
        if {c, m} != set(fit.arms):
            raise RemlError("the two-arm fit holds other arms than this contrast")
        return fit.sigma2["sum"] / pairs, float(fit.pairs - 1)
    i, k = fit.arms.index(c), fit.arms.index(m)
    v = (fit.sigma2[c] + fit.sigma2[m]) / pairs
    var_v = (fit.info_inv[i, i] + fit.info_inv[k, k] + 2.0 * fit.info_inv[i, k]) / pairs ** 2
    df = 2.0 * v * v / var_v if var_v > 0 else float("inf")
    return v, df


def own_variance_df(fit: RemlFit, arm: str, n: int):
    """sigma^2_arm / n with its df from the information: AMD A.8's theta0 form (the sensitivity S-A8)."""
    if fit.two_arm:
        raise RemlError("a two-arm fit has no per-arm variance")
    i = fit.arms.index(arm)
    v = fit.sigma2[arm] / n
    var_v = fit.info_inv[i, i] / n ** 2
    return v, (2.0 * v * v / var_v if var_v > 0 else float("inf"))
