"""An independent reference for section 9.4's HB-C of the halves (tests only). It imports nothing of B16's fit,
contrast or t code: the REML is written on error contrasts (K = an orthonormal basis of the residual space, w = K'y,
Sigma = K'VK), maximized by projected Fisher scoring on the sigma^2 scale (not log sigma^2) with a step-halving line
search, the box sigma^2 >= floor as a constraint, and a stop on the projected step (1e-13 relative) after up to
5,000 steps; the information is 1/2 tr(Sigma^-1 K'D_g K Sigma^-1 K'D_h K). It starts at REV4 3.2's start (each
arm's OLS residual sum of squares over its residual-df share, computed here with its own hat matrix) or at a given
point (to check that a given point is a constrained REML maximum). The item part uses the identity
SS_E = SS_total - SS_seeds - SS_prompts. The t quantile is B14's (``overlap_strata.t_quantile``, its own
incomplete beta), not B16's ``tdist``. The verdict is written again from REV4 9.4's text.

Model (REV4 3.2): y(a, j) = mu_a + s_j + e(a, j), Var e = sigma^2_a, one seed effect per cluster, fixed effects.
Contrast c - m on a half with P_h prompts and J common seeds: the paired mean; V_seed = (sigma^2_c + sigma^2_m) / J
with df_seed = 2 V_seed^2 / Var-hat(V_seed) from the inverse information; V_item = max(0, MS_P - MS_E) / (P_h J)
x 10^4; q as AMD A.4; df = V^2 / (V_seed^2 / df_seed + q). A two-arm cluster: V_seed = var(d) / J (ddof 1),
floored at the one floor, J - 1 df. A pair outside one fit: the paired variance, J - 1 df (LN-20 item 2).
"""

from __future__ import annotations

import math

import numpy as np

from scripts.stage1_s1 import overlap_strata as b14


def _x(cells, arms):
    """Intercept, arm effects (first arm dropped) and seed effects (first seed dropped): a different basis of the
    same column space as B16's design."""
    seeds = sorted({j for _, j, _ in cells})
    x = np.zeros((len(cells), 1 + (len(arms) - 1) + (len(seeds) - 1)))
    for i, (a, j, _) in enumerate(cells):
        x[i, 0] = 1.0
        k = arms.index(a)
        if k > 0:
            x[i, k] = 1.0
        s = seeds.index(j)
        if s > 0:
            x[i, len(arms) - 1 + s] = 1.0
    return x


def _residual_basis(x):
    u, sv, _ = np.linalg.svd(x, full_matrices=True)
    rank = int((sv > 1e-10 * sv[0]).sum())
    return u[:, rank:]


def _parts(theta, cell_arm, k, w, groups):
    v = theta[cell_arm]
    sigma = (k.T * v) @ k
    inv = np.linalg.inv(sigma)
    kdk = [(k[cell_arm == g].T @ k[cell_arm == g]) for g in range(groups)]
    a = inv @ w
    grad = np.array([-0.5 * np.trace(inv @ kdk[g]) + 0.5 * a @ kdk[g] @ a for g in range(groups)])
    m = [inv @ kdk[g] for g in range(groups)]
    info = np.array([[0.5 * np.trace(m[g] @ m[h]) for h in range(groups)] for g in range(groups)])
    sign, logdet = np.linalg.slogdet(sigma)
    ll = -0.5 * (logdet + w @ a)
    return ll, grad, info


def start_rule(cells, arms, floor):
    """REV4 3.2's start, computed here: each arm's OLS residual sum of squares over its residual-df share
    (the sum over its cells of 1 - leverage), floored."""
    x = _x(cells, arms)
    y = np.array([value for _, _, value in cells])
    hat = x @ np.linalg.lstsq(x, np.eye(len(y)), rcond=None)[0]
    res = y - hat @ y
    lev = np.diag(hat)
    cell_arm = np.array([arms.index(a) for a, _, _ in cells])
    return [max(float((res[cell_arm == i] ** 2).sum() / (1.0 - lev[cell_arm == i]).sum()), floor) for i in range(len(arms))]


def reml_loglik(cells, arms, sigma2):
    """The REML log-likelihood on the error contrasts (its own constant), at sigma2 (arm -> value)."""
    arms = list(arms)
    x = _x(cells, arms)
    k = _residual_basis(x)
    w = k.T @ np.array([value for _, _, value in cells])
    cell_arm = np.array([arms.index(a) for a, _, _ in cells])
    return float(_parts(np.array([sigma2[a] for a in arms]), cell_arm, k, w, len(arms))[0])


def reml_reference(cells, arms, floor, start=None):
    """(sigma^2 by arm, the inverse information on the sigma^2 scale, at_floor) for one cluster with >= 3 arms, by
    projected Fisher scoring from ``start`` (arm -> sigma^2; default REV4 3.2's start rule)."""
    arms = list(arms)
    x = _x(cells, arms)
    y = np.array([value for _, _, value in cells])
    cell_arm = np.array([arms.index(a) for a, _, _ in cells])
    k = _residual_basis(x)
    w = k.T @ y
    g = len(arms)
    first = start_rule(cells, arms, floor) if start is None else [start[a] for a in arms]
    theta = np.maximum(np.array(first, dtype=float), floor)
    ll, grad, info = _parts(theta, cell_arm, k, w, g)
    for _ in range(5000):
        free = (theta > floor * (1 + 1e-12)) | (grad > 0)
        step = np.zeros(g)
        step[free] = np.linalg.solve(info[np.ix_(free, free)], grad[free])
        t, moved = 1.0, False
        for _ in range(80):
            cand = np.maximum(theta + t * step, floor)
            ll_c, grad_c, info_c = _parts(cand, cell_arm, k, w, g)
            if ll_c >= ll - 1e-13:
                moved = True
                break
            t /= 2.0
        if not moved:
            break
        change = np.max(np.abs(cand - theta) / theta)
        theta, ll, grad, info = cand, ll_c, grad_c, info_c
        if change < 1e-13:
            break
    at_floor = [arm for i, arm in enumerate(arms) if theta[i] <= floor * (1 + 1e-9)]
    return {arm: float(theta[i]) for i, arm in enumerate(arms)}, np.linalg.inv(info), at_floor


def item_part(d):
    """V_item (x 10^4) and q from the J x P table of share differences, by SS_E = SS_total - SS_rows - SS_cols."""
    j, p = d.shape
    grand = d.mean()
    ss_total = ((d - grand) ** 2).sum()
    ss_rows = p * ((d.mean(axis=1) - grand) ** 2).sum()
    ss_cols = j * ((d.mean(axis=0) - grand) ** 2).sum()
    ms_p = ss_cols / (p - 1)
    ms_e = max(ss_total - ss_rows - ss_cols, 0.0) / ((p - 1) * (j - 1))
    k = 1e4 / (p * j)
    if ms_p > ms_e:
        return (ms_p - ms_e) * k, (ms_p * k) ** 2 / (p - 1) + (ms_e * k) ** 2 / ((p - 1) * (j - 1))
    return 0.0, 0.0


def contrast_reference(items_by_cell, cluster_arms, seeds_of, c, m, idx, floor, form, start=None):
    """One contrast c - m on the positions idx. form: 'cluster' (REML over cluster_arms from ``start``, default the
    start rule; the sum rule if two arms), 'paired' (LN-20 item 2 / S-p). Returns est, se, df, the 90% interval,
    the fit's sigma^2 and its REML log-likelihood."""
    common = sorted(set(seeds_of[c]) & set(seeds_of[m]))
    jn = len(common)
    cell = {key: 100.0 * float(np.mean(items[idx])) for key, items in items_by_cell.items()}
    diffs = np.array([cell[(c, j)] - cell[(m, j)] for j in common])
    est = float(diffs.mean())
    d = np.stack([items_by_cell[(c, j)][idx] - items_by_cell[(m, j)][idx] for j in common])
    v_item, q = item_part(d)
    sigma2, ll = None, None
    if form == "paired" or len(cluster_arms) == 2:
        s = float(diffs.var(ddof=1))
        if form != "paired":
            s = max(s, floor)
        v_seed, df_seed = s / jn, float(jn - 1)
    else:
        cells = [(a, j, cell[(a, j)]) for a in cluster_arms for j in seeds_of[a]]
        sigma2, inv, _ = reml_reference(cells, cluster_arms, floor, start)
        ll = reml_loglik(cells, cluster_arms, sigma2)
        i, k = cluster_arms.index(c), cluster_arms.index(m)
        v_seed = (sigma2[c] + sigma2[m]) / jn
        var_v = (inv[i, i] + inv[k, k] + 2.0 * inv[i, k]) / jn ** 2
        df_seed = 2.0 * v_seed ** 2 / var_v
    v = v_seed + v_item
    df = v * v / (v_seed * v_seed / df_seed + q)
    se = math.sqrt(v)
    half = b14.t_quantile(0.95, df) * se
    return {"est": est, "se": se, "df": df, "lower": est - half, "upper": est + half, "v_seed": v_seed,
            "v_item": v_item, "sigma2": sigma2, "loglik": ll}


def verdict_reference(all_est, lower, tol=1e-9):
    """REV4 9.4 written again: the lower half's estimate has the all-prompt sign (never 0) and its 90% interval
    excludes 0; 'holds' or 'not shown'."""
    def sgn(x):
        return 0 if abs(x) <= tol else (1 if x > 0 else -1)
    if lower is None:
        return False
    return sgn(all_est) != 0 and sgn(lower["est"]) == sgn(all_est) and (lower["lower"] > 0 or lower["upper"] < 0)
