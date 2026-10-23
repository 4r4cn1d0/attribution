"""HB-C's REML (REV3 3.2; AMD A.3, A.12's tests): recovery with known variances, the score against finite
differences, the fit as the maximum, the two-arm cluster, the floors, the stop rule, and the cross-check against
the planning routine of the analysis-model draft (read-only, by path)."""

from __future__ import annotations

import importlib.util
import math
import pathlib
import sys
import warnings

import numpy as np
import pytest

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import reml

ARMS4 = ("a0", "S1", "S3", "S4")


def table(rng, arms, sig, seeds_of, shift=3.0, means=None):
    """Cells of one cluster: mu_a + s_j + e(a, j), Var e = sig[a]."""
    seeds = sorted({j for a in arms for j in seeds_of(a)})
    s = {j: rng.normal(0, shift) for j in seeds}
    cells = []
    for i, a in enumerate(arms):
        for j in seeds_of(a):
            cells.append((a, j, (means or {}).get(a, 10.0 * i) + s[j] + rng.normal(0, math.sqrt(sig[a]))))
    return cells


def d1_seeds(a):
    return range(1101, 1108) if a in ("a0", "R") else range(1102, 1108)


def test_score_equals_finite_difference_of_the_reml_loglik():
    rng = np.random.default_rng(11)
    sig = {"a0": 4.0, "S1": 9.0, "S3": 1.0, "S4": 16.0}
    cells = table(rng, ARMS4, sig, d1_seeds)
    x, y, cell_arm = reml.design(cells, ARMS4)
    z = np.zeros((len(y), 4))
    z[np.arange(len(y)), cell_arm] = 1.0
    th = {"a0": 3.0, "S1": 7.0, "S3": 2.0, "S4": 12.0}
    p = reml._projection(x, 1.0 / np.array([th[a] for a in ARMS4])[cell_arm])
    score, info = reml._score_info(p, y, z)
    for i, a in enumerate(ARMS4):
        h = 1e-5 * th[a]
        up, dn = dict(th), dict(th)
        up[a] += h
        dn[a] -= h
        fd = (reml.reml_loglik(cells, ARMS4, up) - reml.reml_loglik(cells, ARMS4, dn)) / (2 * h)
        assert score[i] == pytest.approx(fd, rel=1e-5, abs=1e-8)
    assert np.allclose(info, info.T) and np.all(np.linalg.eigvalsh(info) > 0)


def test_the_fit_is_the_maximum_and_the_score_vanishes_above_the_floor():
    rng = np.random.default_rng(12)
    for _ in range(8):
        cells = table(rng, ARMS4, {"a0": 4.0, "S1": 9.0, "S3": 2.0, "S4": 16.0}, d1_seeds)
        fit = reml.fit_cells(cells, ARMS4, 0.01, max_iter=400)       # Fisher scoring converges linearly: see the 25-step test
        assert fit.converged and fit.iterations <= 400
        ll = reml.reml_loglik(cells, ARMS4, fit.sigma2)
        for a in ARMS4:
            factors = (1.25,) if a in fit.at_floor else (0.8, 1.25)   # a floored arm sits on the box's edge
            for factor in factors:
                other = dict(fit.sigma2)
                other[a] *= factor
                assert reml.reml_loglik(cells, ARMS4, other) < ll, (a, factor, fit.at_floor)
        x, y, cell_arm = reml.design(cells, ARMS4)
        z = np.zeros((len(y), 4))
        z[np.arange(len(y)), cell_arm] = 1.0
        theta = np.array([fit.sigma2[a] for a in ARMS4])
        score, info = reml._score_info(reml._projection(x, 1.0 / theta[cell_arm]), y, z)
        free = np.array([a not in fit.at_floor for a in ARMS4])
        step = np.linalg.pinv((theta[:, None] * info * theta[None, :])[np.ix_(free, free)], rcond=1e-10) @ (theta * score)[free]
        assert np.all(np.abs(step) < 1e-5)                            # the free arms' score vanishes
        for i, a in enumerate(ARMS4):
            if a in fit.at_floor:
                assert score[i] < 0                                   # the likelihood still falls toward the floor


def test_the_active_set_fit_is_at_least_as_likely_as_the_planning_routines_fit():
    """The planning routine (AMD SIM) solves every arm and floors afterwards; at its fixed point the free arms'
    scores are not zero. The reading's active set reaches a REML value at least as high, strictly higher when an
    arm is floored."""
    rng = np.random.default_rng(25)
    higher, floored = 0, 0
    for _ in range(40):
        cells = table(rng, ARMS4, {"a0": 4.0, "S1": 9.0, "S3": 2.0, "S4": 16.0}, d1_seeds)
        ours = reml.fit_cells(cells, ARMS4, 0.01, max_iter=400)
        theirs = reml.fit_cells(cells, ARMS4, 0.01, max_iter=400, planning_floor=True)
        ll_ours, ll_theirs = reml.reml_loglik(cells, ARMS4, ours.sigma2), reml.reml_loglik(cells, ARMS4, theirs.sigma2)
        assert ll_ours >= ll_theirs - 1e-9
        if theirs.at_floor:
            floored += 1
            higher += ll_ours > ll_theirs + 1e-6
        else:
            for a in ARMS4:
                assert ours.sigma2[a] == pytest.approx(theirs.sigma2[a], rel=1e-5)     # no floor: the same fixed point
    assert floored > 5 and higher > 0


def test_information_matrix_equals_minus_the_mean_observed_hessian():
    """The expected information 1/2 tr(P Z_g P Z_h) on the sigma^2 scale equals -E[Hessian of the REML log-lik]:
    checked by Monte Carlo at the true variances (AMD A.4's df rests on this matrix)."""
    rng = np.random.default_rng(26)
    sig = {"a0": 4.0, "S1": 9.0, "S3": 2.0, "S4": 16.0}
    th = np.array([sig[a] for a in ARMS4])
    cells0 = table(rng, ARMS4, sig, d1_seeds)
    x, _, cell_arm = reml.design(cells0, ARMS4)
    z = np.zeros((len(cell_arm), 4))
    z[np.arange(len(cell_arm)), cell_arm] = 1.0
    _, info = reml._score_info(reml._projection(x, 1.0 / th[cell_arm]), np.zeros(len(cell_arm)), z)
    hess = np.zeros((4, 4))
    reps = 150
    for _ in range(reps):
        cells = table(rng, ARMS4, sig, d1_seeds)
        for i, a in enumerate(ARMS4):
            for k, b in enumerate(ARMS4):
                h1, h2 = 1e-3 * th[i], 1e-3 * th[k]
                def ll(da, db):
                    t = dict(sig)
                    t[a] += da
                    t[b] += db
                    return reml.reml_loglik(cells, ARMS4, t)
                hess[i, k] += (ll(h1, h2) - ll(h1, -h2) - ll(-h1, h2) + ll(-h1, -h2)) / (4 * h1 * h2) / reps
    for i in range(4):
        assert -hess[i, i] == pytest.approx(info[i, i], rel=0.15)
        for k in range(4):
            if k != i:
                assert -hess[i, k] == pytest.approx(info[i, k], abs=0.1 * math.sqrt(info[i, i] * info[k, k]))


def test_the_returned_information_is_on_the_sigma2_scale_and_feeds_the_seed_df():
    """AMD A.4: Var-hat(V_seed) = (I^-1_cc + I^-1_mm + 2 I^-1_cm)/J^2 with I the REML information of (sigma^2_a)."""
    rng = np.random.default_rng(28)
    cells = table(rng, ARMS4, {"a0": 4.0, "S1": 9.0, "S3": 2.0, "S4": 16.0}, d1_seeds)
    fit = reml.fit_cells(cells, ARMS4, 0.01)
    x, y, cell_arm = reml.design(cells, ARMS4)
    z = np.zeros((len(y), 4))
    z[np.arange(len(y)), cell_arm] = 1.0
    theta = np.array([fit.sigma2[a] for a in ARMS4])
    _, info = reml._score_info(reml._projection(x, 1.0 / theta[cell_arm]), y, z)
    assert np.allclose(fit.info_inv, np.linalg.pinv(info), rtol=1e-8, atol=1e-12)
    assert np.allclose(fit.info_inv @ info, np.eye(4), atol=1e-8)
    v, df = reml.seed_variance(fit, "a0", "S1", 6)
    var_v = (fit.info_inv[0, 0] + fit.info_inv[1, 1] + 2 * fit.info_inv[0, 1]) / 36
    assert v == pytest.approx((fit.sigma2["a0"] + fit.sigma2["S1"]) / 6) and df == pytest.approx(2 * v * v / var_v)
    # the scale matters: on the log scale Var-hat would be off by sigma^4 factors, and the df with it
    assert 2.0 < df < 15.0


def test_an_arm_whose_cells_are_alone_at_their_seeds_is_not_identified():
    rng = np.random.default_rng(27)
    cells = table(rng, ("a0", "S1", "S3"), {"a0": 4.0, "S1": 9.0, "S3": 2.0}, lambda a: range(1101, 1108) if a != "S3" else range(1108, 1110))
    fit = reml.fit_cells(cells, ("a0", "S1", "S3"), 0.01)
    assert fit.not_identified == ("S3",) and fit.residual_df_by_arm["S3"] == pytest.approx(0.0)
    assert fit.sigma2["S3"] == 0.01 and fit.converged


def test_recovery_of_known_variances_at_many_seeds_within_monte_carlo_error():
    """With 60 seeds per arm the small-sample bias is gone: every arm's mean estimate is within 3 MC SE of truth."""
    rng = np.random.default_rng(13)
    sig = {"a0": 4.0, "S1": 9.0, "S3": 1.0, "S4": 16.0}
    reps, est = 120, {a: [] for a in ARMS4}
    for _ in range(reps):
        cells = table(rng, ARMS4, sig, lambda a: range(1101, 1161))
        fit = reml.fit_cells(cells, ARMS4, 1e-6)
        for a in ARMS4:
            est[a].append(fit.sigma2[a])
    for a in ARMS4:
        values = np.array(est[a])
        mc_se = values.std(ddof=1) / math.sqrt(reps)
        assert abs(values.mean() - sig[a]) < 3 * mc_se + 0.02 * sig[a], (a, values.mean(), mc_se)


def test_recovery_at_d1_matches_an_independent_coordinate_ascent_maximizer():
    """At 6 seeds the REML point is biased toward equal variances (an estimator property, not a code fault); the
    code's fixed point equals an independent maximizer of the same REML log-likelihood."""
    rng = np.random.default_rng(14)
    sig = {"a0": 4.0, "S1": 9.0, "S3": 1.0, "S4": 16.0}
    for _ in range(3):
        cells = table(rng, ARMS4, sig, d1_seeds)
        fit = reml.fit_cells(cells, ARMS4, 0.01, tol=1e-10, max_iter=400)
        th = {a: 5.0 for a in ARMS4}
        for _sweep in range(25):                                   # golden-section sweeps on log sigma^2, per arm, in the box
            for a in ARMS4:
                lo, hi = math.log(0.01), math.log(1e4)
                for _ in range(45):
                    m1, m2 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
                    t1, t2 = dict(th), dict(th)
                    t1[a], t2[a] = math.exp(m1), math.exp(m2)
                    if reml.reml_loglik(cells, ARMS4, t1) < reml.reml_loglik(cells, ARMS4, t2):
                        lo = m1
                    else:
                        hi = m2
                th[a] = math.exp(0.5 * (lo + hi))
        ll_fit, ll_ca = reml.reml_loglik(cells, ARMS4, fit.sigma2), reml.reml_loglik(cells, ARMS4, th)
        assert ll_fit >= ll_ca - 1e-6, (ll_fit, ll_ca, fit.sigma2, th)
        for a in ARMS4:
            if a not in fit.at_floor and th[a] > 0.0101:
                assert math.log(fit.sigma2[a]) == pytest.approx(math.log(th[a]), abs=0.05), (a, fit.sigma2[a], th[a])


def test_start_is_each_arms_residual_mean_square_and_residual_df_are_3_75_under_d1():
    rng = np.random.default_rng(15)
    cells = table(rng, ARMS4, {a: 4.0 for a in ARMS4}, d1_seeds)
    fit = reml.fit_cells(cells, ARMS4, 0.01)
    assert fit.residual_df == 15.0
    assert all(fit.residual_df_by_arm[a] == pytest.approx(3.75) for a in ARMS4)
    x, y, cell_arm = reml.design(cells, ARMS4)
    hat = x @ np.linalg.pinv(x.T @ x) @ x.T
    r = y - hat @ y
    lev = 1 - np.diag(hat)
    for i, a in enumerate(ARMS4):
        mask = cell_arm == i
        assert fit.start[a] == pytest.approx((r[mask] ** 2).sum() / lev[mask].sum())
    assert fit.start["a0"] > 0 and fit.not_identified == ()


def test_plan_b_removal_cluster_has_16_residual_df_and_block_a_has_1_5_per_arm():
    rng = np.random.default_rng(16)
    arms = ("R", "A1", "H1")
    cells = table(rng, arms, {a: 4.0 for a in arms}, lambda a: range(1101, 1111) if a == "R" else range(1102, 1111))
    fit = reml.fit_cells(cells, arms, 0.01)
    assert fit.residual_df == 16.0 and all(fit.residual_df_by_arm[a] == pytest.approx(16 / 3) for a in arms)
    cells = table(rng, ARMS4, {a: 4.0 for a in ARMS4}, lambda a: range(1101, 1105) if a == "a0" else range(1102, 1105))
    fit = reml.fit_cells(cells, ARMS4, 0.01)
    assert fit.residual_df == 6.0 and all(fit.residual_df_by_arm[a] == pytest.approx(1.5) for a in ARMS4)


def test_two_arm_cluster_equals_the_paired_t_with_j_minus_1_df_and_prints_no_split():
    """REV3 3.5 item 1; AMD A.12 (V-5): only sigma^2_S1 + sigma^2_S4 is identified."""
    rng = np.random.default_rng(17)
    arms = ("S1", "S4")
    cells = table(rng, arms, {"S1": 4.0, "S4": 9.0}, lambda a: range(1102, 1111))
    fit = reml.fit_cells(cells, arms, 0.01)
    assert fit.two_arm and set(fit.sigma2) == {"sum"} and fit.not_identified == arms and fit.pairs == 9
    d = np.array([v for a, j, v in cells if a == "S1"]) - np.array([v for a, j, v in cells if a == "S4"])
    assert fit.sigma2["sum"] == pytest.approx(d.var(ddof=1))
    v, df = reml.seed_variance(fit, "S1", "S4", 9)
    assert v == pytest.approx(d.var(ddof=1) / 9) and df == 8.0
    table_ = {(a, j): np.full(5, v / 100.0) for a, j, v in cells}
    est_fit = con.contrast_fit(table_, fit, "S1", "S4", tuple(range(1102, 1111)), 100.0, False)
    est_paired = con.contrast_paired(table_, "S1", "S4", tuple(range(1102, 1111)), 100.0, False)
    assert (est_fit.est, est_fit.se, est_fit.df) == pytest.approx((est_paired.est, est_paired.se, est_paired.df))
    assert est_fit.df == 8.0
    with pytest.raises(reml.RemlError):
        reml.own_variance_df(fit, "S1", 9)


def test_two_arm_sum_equals_the_generic_reml_sum_when_the_split_is_forced():
    """The generic Fisher scoring on two arms (pseudo-inverse) moves only the identified sum: it equals var(d)."""
    rng = np.random.default_rng(18)
    arms = ("S1", "S4")
    cells = table(rng, arms, {"S1": 4.0, "S4": 9.0}, lambda a: range(1102, 1108))
    generic = reml.fit_cells(cells, arms, 1e-9, tol=1e-10, max_iter=200, two_arm_rule=False)
    d = np.array([v for a, j, v in cells if a == "S1"]) - np.array([v for a, j, v in cells if a == "S4"])
    assert not generic.two_arm
    assert generic.sigma2["S1"] + generic.sigma2["S4"] == pytest.approx(d.var(ddof=1), rel=1e-5)
    v, df = reml.seed_variance(generic, "S1", "S4", 6)
    assert v == pytest.approx(d.var(ddof=1) / 6, rel=1e-5)             # the sum's variance is what the contrast needs


def test_an_arm_at_the_floor_is_printed_and_the_stop_rule_skips_it():
    """LN-35: a floored arm keeps proposing a step below the floor, so the stop rule reads the arms above it."""
    rng = np.random.default_rng(19)
    sig = {"a0": 4.0, "S1": 9.0, "S3": 1e-9, "S4": 16.0}
    cells = table(rng, ARMS4, sig, d1_seeds)
    fit = reml.fit_cells(cells, ARMS4, 0.01)
    # REML with fixed seed effects can fit one arm's cells exactly, so the boundary arm need not be the one with the
    # smallest true variance (here a0 goes to the floor; the planning routine gives the same fit: the cross-check below)
    assert len(fit.at_floor) == 1 and fit.sigma2[fit.at_floor[0]] == 0.01
    assert fit.converged and fit.iterations < 25 and fit.steps[-1] < 1e-6
    again = reml.fit_cells(cells, ARMS4, 0.01)
    assert again.sigma2 == fit.sigma2 and again.arms == fit.arms and not again.two_arm      # no re-fit, no model change
    # without the LN-35 wording (the largest step over EVERY arm) the same fit would run to the 25-step cap
    x, y, cell_arm = reml.design(cells, ARMS4)
    z = np.zeros((len(y), 4))
    z[np.arange(len(y)), cell_arm] = 1.0
    theta = np.array([fit.sigma2[a] for a in ARMS4])
    score, info = reml._score_info(reml._projection(x, 1.0 / theta[cell_arm]), y, z)
    step = np.linalg.pinv(theta[:, None] * info * theta[None, :], rcond=1e-10) @ (theta * score)
    assert abs(step[ARMS4.index(fit.at_floor[0])]) > 1e-6                                   # the floored arm still proposes a step


def test_max_iter_without_convergence_stops_at_25_and_says_so():
    rng = np.random.default_rng(20)
    cells = table(rng, ARMS4, {"a0": 4.0, "S1": 9.0, "S3": 1.0, "S4": 16.0}, d1_seeds)
    fit = reml.fit_cells(cells, ARMS4, 0.01, tol=0.0)
    assert fit.iterations == 25 and not fit.converged and len(fit.steps) == 25
    # the spec's 25 steps leave some D1 fits short of 1e-6 (linear convergence); the record says so, and the
    # fixed point is what a longer run reaches to within the last step's size
    rng = np.random.default_rng(24)
    for _ in range(20):
        cells = table(rng, ARMS4, {"a0": 4.0, "S1": 9.0, "S3": 2.0, "S4": 16.0}, d1_seeds)
        short, long = reml.fit_cells(cells, ARMS4, 1e-6), reml.fit_cells(cells, ARMS4, 1e-6, max_iter=400)
        if not short.converged:
            assert short.iterations == 25 and long.converged
            for a in ARMS4:
                assert abs(math.log(short.sigma2[a]) - math.log(long.sigma2[a])) < 25 * short.steps[-1] + 1e-9


def test_each_endpoint_floor_in_its_own_unit():
    """ST-3 / LN-35: on L's scale (nats) a literal 0.01 floors every arm; 1e-8 floors none."""
    rng = np.random.default_rng(21)
    sig = {a: 5.6e-6 for a in ARMS4}
    cells = table(rng, ARMS4, sig, d1_seeds, shift=0.003, means={a: 1.56 for a in ARMS4})
    every = reml.fit_cells(cells, ARMS4, 0.01)
    assert every.at_floor == ARMS4
    own = reml.fit_cells(cells, ARMS4, 1e-8)
    assert own.at_floor == () and all(1e-7 < own.sigma2[a] < 1e-4 for a in ARMS4)


def test_a_cell_alone_at_its_seed_contributes_nothing():
    """REV3 3.2: a0_1101 is absorbed by its seed effect; the fit with and without it is the same."""
    rng = np.random.default_rng(22)
    cells = table(rng, ARMS4, {"a0": 4.0, "S1": 9.0, "S3": 1.0, "S4": 16.0}, d1_seeds)
    without = [c for c in cells if c[1] != 1101]
    f1, f2 = reml.fit_cells(cells, ARMS4, 0.01), reml.fit_cells(without, ARMS4, 0.01)
    for a in ARMS4:
        assert f1.sigma2[a] == pytest.approx(f2.sigma2[a], rel=1e-6)
    assert np.allclose(f1.info_inv, f2.info_inv, rtol=1e-5, atol=1e-9)


def test_refusals():
    with pytest.raises(reml.RemlError):
        reml.fit_cells([], ARMS4, 0.01)
    with pytest.raises(reml.RemlError):
        reml.fit_cells([("a0", 1101, 1.0), ("a0", 1101, 2.0), ("S1", 1101, 1.0)], ("a0", "S1"), 0.01)
    with pytest.raises(reml.RemlError):
        reml.fit_cells([("a0", 1101, float("nan")), ("S1", 1101, 1.0), ("S3", 1101, 1.0)], ("a0", "S1", "S3"), 0.01)
    with pytest.raises(reml.RemlError):
        reml.fit_cells([("a0", 1101, 1.0), ("S1", 1101, 1.0)], ("a0", "S1", "S3"), 0.01)
    with pytest.raises(reml.RemlError):
        reml.fit_cells([("a0", 1101, 1.0), ("S1", 1101, 1.0), ("S3", 1101, 1.0)], ("a0", "S1", "S3"), 0.0)


REVIEW = pathlib.Path("/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-preregistration-rev3/stat_review_hbc.py")


@pytest.mark.skipif(not REVIEW.is_file(), reason="the statistics review's script is not on this machine")
def test_cross_check_against_the_planning_reml_routine_on_d1_tables():
    """The analysis-model draft's planning REML (AMD SIM reml_hetero, through the review's ClusterDesign) and this
    code give the same arm variances on random D1 tables (floor 0.01; read-only use of the planning scripts)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("stat_review_hbc_ro", REVIEW)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        d = mod.S1M.D1
        dc = mod.ClusterDesign(d)
        rng = np.random.default_rng(23)
        u = mod.draw(rng, d, 40, 2.65 ** 2, 0.5)
        th, _ = mod.S1M.reml_hetero(dc, u, floor=0.01)
    arms = list(mod.ARMS)
    cluster = {"a0": "full", "S1": "full", "S3": "full", "S4": "full", "R": "removal", "A1": "removal", "L1": "removal", "H1": "removal"}
    compared = 0
    for b in range(u.shape[0]):
        cells = [(arms[d.cell_arm[i]], int(d.seeds[d.cell_seed[i]]), float(u[b, i])) for i in range(d.nc)]
        for cl in ("full", "removal"):
            members = tuple(a for a in arms if cluster[a] == cl)
            mine = [c for c in cells if c[0] in members]
            fit = reml.fit_cells(mine, members, 0.01, planning_floor=True)            # their floor handling, same algorithm
            active = reml.fit_cells(mine, members, 0.01)
            for a in members:
                theirs = th[b, arms.index(a)]
                if theirs > 0.0101 and fit.sigma2[a] > 0.0101:
                    assert fit.sigma2[a] == pytest.approx(theirs, rel=2e-3), (b, a)
                    compared += 1
                else:
                    assert theirs <= 0.0101 and fit.sigma2[a] <= 0.0101
                if not fit.at_floor:
                    assert active.sigma2[a] == pytest.approx(theirs, rel=2e-3)        # no floor: the reading agrees too
    assert compared > 200
