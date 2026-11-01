"""The estimator, the item part, Satterthwaite's df (a hand case), the LN-20 forms and the sensitivity forms
(REV3 3.1-3.2, 3.4, 3.6; AMD A.2-A.5, A.8)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import reml, tdist
from scripts.stage1_s1.reading.settings import Refusal

SEEDS = tuple(range(1102, 1108))


def make_table(rng, arms, seeds_of, p=20, level=None, seed_sd=0.03, item_sd=0.05, arm_item_sd=0.0):
    out = {}
    base = rng.uniform(0.2, 0.8, p)
    for a in arms:
        b = rng.normal(0, arm_item_sd, p)
        for j in seeds_of(a):
            out[(a, j)] = np.clip(base + b + (level or {}).get(a, 0.0) + rng.normal(0, seed_sd) + rng.normal(0, item_sd, p), 0, 1)
    return out


def test_two_way_mean_squares_hand_case():
    d = np.array([[1.0, 2.0, 6.0], [3.0, 2.0, 7.0]])              # J = 2, P = 3
    grand = 3.5
    col = d.mean(axis=0)                                           # 2, 2, 6.5
    ms_p_hand = 2 * ((col - grand) ** 2).sum() / 2                 # J sum (col - grand)^2 / (P - 1)
    row = d.mean(axis=1, keepdims=True)
    resid = d - row - col[None, :] + grand
    ms_e_hand = (resid ** 2).sum() / (2 * 1)
    ms_p, ms_e = con.two_way_ms(d)
    assert ms_p == pytest.approx(ms_p_hand) and ms_e == pytest.approx(ms_e_hand)
    assert ms_p == pytest.approx(13.5) and ms_e == pytest.approx(0.5)


def test_item_part_formula_and_its_q():
    d = np.array([[1.0, 2.0, 6.0], [3.0, 2.0, 7.0]])
    v, q = con.item_part(d, 100.0)
    k = 1e4 / (3 * 2)
    assert v == pytest.approx((13.5 - 0.5) * k)
    assert q == pytest.approx((13.5 * k) ** 2 / 2 + (0.5 * k) ** 2 / (2 * 1))
    d3 = np.array([[1.0, 2.0, 6.0, 4.0], [3.0, 2.0, 7.0, 5.0], [2.0, 4.0, 5.0, 4.5]])      # J = 3, P = 4: (P - 1)(J - 1) = 6
    ms_p, ms_e = con.two_way_ms(d3)
    v3, q3 = con.item_part(d3, 1.0)
    k3 = 1.0 / 12
    assert v3 == pytest.approx(max(0.0, ms_p - ms_e) * k3)
    assert q3 == pytest.approx((ms_p * k3) ** 2 / 3 + (ms_e * k3) ** 2 / 6)
    flat = np.array([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]])            # MS_P = 0 <= MS_E: no item part, q = 0
    assert con.item_part(flat, 100.0) == (0.0, 0.0)


def test_satterthwaite_hand_case():
    assert con.satterthwaite_df(2.0, 6.0, 1.0, 0.5) == pytest.approx(9.0 / (4.0 / 6.0 + 0.5))
    assert con.satterthwaite_df(2.0, 6.0, 0.0, 0.0) == pytest.approx(6.0)
    assert con.satterthwaite_df(0.0, 6.0, 1.0, 0.25) == pytest.approx(4.0)


def test_item_part_recovers_the_arm_by_item_variance_over_p():
    """E[MS_P - MS_E] = J sigma_b^2, so V_item estimates sigma_b^2 / P (review-statistics 1.1)."""
    rng = np.random.default_rng(31)
    j, p, sb, se = 6, 200, 0.05, 0.1
    values = []
    for _ in range(400):
        d = rng.normal(0, 0.02, (j, 1)) + rng.normal(0, sb, (1, p)) + rng.normal(0, se, (j, p))
        values.append(con.item_part(d, 1.0)[0])
    values = np.array(values)
    assert values.mean() == pytest.approx(sb ** 2 / p, rel=0.08)


def test_the_estimator_is_the_paired_mean_with_the_comparator_first():
    rng = np.random.default_rng(32)
    t = make_table(rng, ("R", "A1"), lambda a: SEEDS, level={"A1": -0.1})
    est = con.paired_mean(t, "R", "A1", SEEDS, 100.0)
    hand = np.mean([100 * (t[("R", j)].mean() - t[("A1", j)].mean()) for j in SEEDS])
    assert est == pytest.approx(hand) and est > 0


def test_contrast_fit_combines_seed_part_item_part_and_df():
    rng = np.random.default_rng(33)
    arms = ("R", "A1", "L1", "H1")
    t = make_table(rng, arms, lambda a: range(1101, 1108) if a == "R" else SEEDS, arm_item_sd=0.08)
    cells = [(a, j, 100.0 * v.mean()) for (a, j), v in t.items()]
    fit = reml.fit_cells(cells, arms, 0.01)
    e = con.contrast_fit(t, fit, "R", "A1", SEEDS, 100.0, True, "P1")
    v_seed, df_seed = reml.seed_variance(fit, "R", "A1", 6)
    v_item, q = con.item_part(con.paired_rows(t, "R", "A1", SEEDS), 100.0)
    assert e.seed_var == pytest.approx(v_seed) and e.seed_df == pytest.approx(df_seed)
    assert e.item_var == pytest.approx(v_item) and e.se == pytest.approx(math.sqrt(v_seed + v_item))
    assert e.df == pytest.approx((v_seed + v_item) ** 2 / (v_seed ** 2 / df_seed + q))
    assert e.pairs == 6 and e.items == 20 and e.with_item
    bare = con.contrast_fit(t, fit, "R", "A1", SEEDS, 100.0, False)
    assert bare.se == pytest.approx(math.sqrt(v_seed)) and bare.df == pytest.approx(df_seed) and not bare.with_item


def test_paired_form_has_j_minus_1_df_and_the_pairs_own_variance():
    rng = np.random.default_rng(34)
    t = make_table(rng, ("a0", "A1"), lambda a: SEEDS)
    e = con.contrast_paired(t, "A1", "a0", SEEDS, 100.0, False)
    d = np.array([100 * (t[("A1", j)].mean() - t[("a0", j)].mean()) for j in SEEDS])
    assert e.est == pytest.approx(d.mean()) and e.se == pytest.approx(d.std(ddof=1) / math.sqrt(6)) and e.df == 5.0
    assert e.p_two_sided() == pytest.approx(tdist.t_two_sided(d.mean() / (d.std(ddof=1) / math.sqrt(6)), 5))


def test_theta0_form_hand_case():
    """LN-20 item 1: m's own between-seed variance / J with J - 1 df; the estimate against the fixed unit."""
    theta0 = np.array([1.0, 0.0, 0.0, 1.0, 0.0])
    t = {("S1", 1102): np.array([1.0, 0, 0, 0, 0]), ("S1", 1103): np.array([1.0, 1, 0, 0, 0]),
         ("S1", 1104): np.array([0.0, 0, 0, 0, 0])}
    e = con.contrast_theta0(t, "S1", (1102, 1103, 1104), theta0, 100.0, False)
    values = np.array([20.0, 40.0, 0.0])
    assert e.est == pytest.approx(values.mean() - 40.0)
    assert e.seed_var == pytest.approx(values.var(ddof=1) / 3) and e.seed_df == 2.0 and e.df == 2.0
    assert e.p_upper(5.0) + e.p_lower(5.0) == pytest.approx(1.0)


def test_p_values_and_intervals():
    e = con.Estimate("x", "f", 3.0, 1.5, 5.0, 2.25, 5.0, 0.0, 0.0, 6, 200, False)
    assert e.t == 2.0
    assert e.p_two_sided() == pytest.approx(tdist.t_two_sided(2.0, 5))
    assert e.p_upper(0.0) == pytest.approx(tdist.t_sf(2.0, 5)) and e.p_lower(0.0) == pytest.approx(1 - tdist.t_sf(2.0, 5))
    assert e.p_upper(5.0) == pytest.approx(tdist.t_sf(-4 / 3, 5))
    lo, hi = e.interval(0.90)
    assert hi - e.est == pytest.approx(tdist.t_quantile(0.95, 5) * 1.5) and e.est - lo == pytest.approx(hi - e.est)
    assert e.mde(0.0075) == pytest.approx((tdist.t_quantile(1 - 0.00375, 5) + tdist.t_quantile(0.8, 5)) * 1.5)
    with pytest.raises(Refusal):
        e.interval(1.0)


def test_welch_pooled_and_blocked_forms_under_d1():
    rng = np.random.default_rng(35)
    arms = ("a0", "R", "A1", "L1", "H1", "S1", "S3", "S4")
    seeds_of = lambda a: tuple(range(1101, 1108)) if a in ("a0", "R") else SEEDS
    t = make_table(rng, arms, seeds_of)
    arms_seeds = {a: seeds_of(a) for a in arms}
    s2, df = con.pooled_variance(t, arms_seeds, 100.0)
    assert df == 42.0                                                      # 50 cells - 8 arms (PLAN-S:102)
    s_a = con.contrast_pooled(t, arms_seeds, "a0", "S1", SEEDS, 100.0, False)
    va, vs = con.arm_values(t, "a0", seeds_of("a0"), 100.0), con.arm_values(t, "S1", SEEDS, 100.0)
    assert s_a.est == pytest.approx(va.mean() - vs.mean()) and s_a.df == 42.0
    assert s_a.seed_var == pytest.approx(s2 * (1 / 7 + 1 / 6))
    w = con.contrast_welch(t, "a0", "S1", seeds_of("a0"), SEEDS, SEEDS, 100.0, False)
    assert w.est == pytest.approx(s_a.est)
    assert w.df == pytest.approx(tdist.welch_df(va.var(ddof=1), 7, vs.var(ddof=1), 6))
    s2b, dfb = con.blocked_variance(t, arms_seeds, 100.0)
    assert dfb == 36.0                                                     # 50 - 8 - 7 + 1 (REV3 3.4)
    b = con.contrast_blocked(t, "a0", "S1", SEEDS, s2b, dfb, 100.0, False)
    assert b.seed_var == pytest.approx(2 * s2b / 6) and b.df == 36.0
    assert b.est == pytest.approx(con.paired_mean(t, "a0", "S1", SEEDS, 100.0))


def test_refusals_on_too_few_seeds_or_items():
    t = {("R", 1102): np.array([0.1, 0.2]), ("A1", 1102): np.array([0.1, 0.1])}
    with pytest.raises(Refusal):
        con.paired_rows(t, "R", "A1", (1102,))
    with pytest.raises(Refusal):
        con.two_way_ms(np.array([[1.0], [2.0]]))
    with pytest.raises(Refusal):
        con.contrast_theta0(t, "R", (1102,), np.array([0.0, 0.0]), 100.0)
