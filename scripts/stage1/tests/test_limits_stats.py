"""REQ-19 / W1-16: the statistics of the limit checks on hand-computed cases (no files)."""

from __future__ import annotations

import math
from fractions import Fraction
from statistics import NormalDist

import pytest

from scripts.stage1 import s1common as s1
from scripts.stage1.limits import limits_check as lcheck
from scripts.stage1.limits import limits_common as lc

N = NormalDist()
Z975, Z80, Z95 = N.inv_cdf(0.975), N.inv_cdf(0.8), N.inv_cdf(0.95)

# The hand 3 x 10 table (rows: a0 seeds; cells: y(a0, j, p) - y(theta0, p)). theta0 refuses prompts 1-3; seed 1
# refuses prompt 3; seed 2 prompts 3 and 4; seed 3 none. Worked by hand: column means -1, -1, -1/3, 1/3, 0 x 6;
# grand mean -1/5; SS_P = 82/15 (9 df), SS_seeds = 1/5, SS_total = 34/5, SS_E = 17/15 (18 df).
TABLE = [[-1, -1, 0, 0, 0, 0, 0, 0, 0, 0],
         [-1, -1, 0, 1, 0, 0, 0, 0, 0, 0],
         [-1, -1, -1, 0, 0, 0, 0, 0, 0, 0]]
MS_P, MS_E, COMPONENT = Fraction(82, 135), Fraction(17, 270), Fraction(49, 270)
SEED_VARIANCE = 100.0       # the three seeds' O: 10, 20 and 0 pp of 10 prompts -> sample variance 100 pp^2

# Gate A's a0 means and the known answer (R: research/experiments/2026-10-17-stage1-prereg-references/
# tau_l_check.out.json; draft A section L.4).
GATE_A_MEANS = {"1101": 1.5424909447459505, "1102": 1.5472398312762379, "1103": 1.5449415715783834}
KNOWN = {"s": 0.002374850619448416, "tau_l": 0.0067170919092681925, "se_one_difference": 0.0033585459546340963,
         "se_6v6": 0.0013711206444236926}


def test_the_two_way_analysis_of_the_hand_table():
    out = lcheck.two_way(TABLE)
    assert (out["ms_prompts"], out["ms_error"], out["prompt_component"]) == (MS_P, MS_E, COMPONENT)
    assert (out["df_prompts"], out["df_error"], out["seeds"], out["prompts"]) == (9, 18, 3, 10)
    assert out["grand_mean"] == Fraction(-1, 5)


def test_the_prompt_component_is_clamped_at_zero():
    """Verification item S-5. By hand: column means 1/3, 1/3, 1/3, 0; grand mean 1/4; SS_P = 1/4 (3 df), SS_seeds = 0,
    SS_total = 9/4, SS_E = 2 (6 df): MS_P = 1/12 < MS_E = 1/3, so the component is 0, not negative."""
    out = lcheck.two_way([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])
    assert (out["ms_prompts"], out["ms_error"]) == (Fraction(1, 12), Fraction(1, 3))
    assert out["prompt_component"] == 0


def test_the_two_way_analysis_refuses_a_ragged_or_tiny_table():
    for bad in ([[0, 1]], [[0, 1], [1]], [[0], [1]], [[0, True], [1, 0]]):
        with pytest.raises(s1.Refusal):
            lcheck.two_way(bad)


def test_both_error_models_on_the_hand_table():
    c = float(COMPONENT)
    for J in (6, 9):
        v_seed = SEED_VARIANCE / J
        v_prompt = 49 / 270 * 1e4 / 10                                    # 181.48 pp^2
        se_random = lcheck.contrast_se_pp("prompts_random", J, SEED_VARIANCE, c, 10)
        se_seed = lcheck.contrast_se_pp("seed_only", J, SEED_VARIANCE, c, 10)
        assert se_random == pytest.approx(math.sqrt(v_seed + v_prompt), rel=1e-12)
        assert se_seed == pytest.approx(math.sqrt(v_seed), rel=1e-12)
        assert lcheck.mde_pp(se_random, 0.05, 0.8) == pytest.approx((Z975 + Z80) * math.sqrt(v_seed + v_prompt), rel=1e-12)
        assert lcheck.mde_pp(se_seed, 0.05, 0.8) == pytest.approx((Z975 + Z80) * math.sqrt(v_seed), rel=1e-12)
        comparator = lcheck.contrast_se_pp("seed_only", J, SEED_VARIANCE, c, 10, comparator=True)
        assert comparator == pytest.approx(math.sqrt(2 * SEED_VARIANCE / J), rel=1e-12)
        comparator_random = lcheck.contrast_se_pp("prompts_random", J, SEED_VARIANCE, c, 10, comparator=True)
        assert comparator_random == pytest.approx(math.sqrt(2 * SEED_VARIANCE / J + v_prompt), rel=1e-12)
    # J = 6, by hand: SE^2 = 16.667 + 181.481 = 198.148; MDE = 2.8016 * 14.0765 = 39.44 pp (prompts random)
    assert lcheck.mde_pp(lcheck.contrast_se_pp("prompts_random", 6, SEED_VARIANCE, c, 10), 0.05, 0.8) == pytest.approx(39.436, abs=0.01)
    assert lcheck.mde_pp(lcheck.contrast_se_pp("seed_only", 6, SEED_VARIANCE, c, 10), 0.05, 0.8) == pytest.approx(11.437, abs=0.01)
    with pytest.raises(s1.Refusal):
        lcheck.contrast_se_pp("bank_conditional", 6, SEED_VARIANCE, c, 10)


def test_the_mde_is_two_sided_at_5_percent():
    assert lcheck.mde_pp(1.0, 0.05, 0.8) == pytest.approx(1.959963984540054 + 0.8416212335729143, rel=1e-12)
    assert lcheck.mde_pp(1.0, 0.05, 0.8) != pytest.approx(Z95 + Z80, rel=1e-6)          # not one-sided


def test_t_quantiles_against_table_values():
    """Reference values from an independent mpmath computation (regularized incomplete beta, 30 digits)."""
    table = {(0.975, 1): 12.706204736, (0.975, 2): 4.302652730, (0.975, 3): 3.182446305, (0.975, 4): 2.776445105,
             (0.975, 5): 2.570581836, (0.975, 10): 2.228138852, (0.975, 16): 2.119905299, (0.8, 5): 0.919543780,
             (0.8, 10): 0.879057829, (0.8, 16): 0.864667002}
    for (p, df), value in table.items():
        assert lc.t_quantile(p, df) == pytest.approx(value, abs=2e-7), (p, df)
    assert lc.t_cdf(0.0, 7) == pytest.approx(0.5, abs=1e-15)
    assert lc.t_cdf(1.3, 6) + lc.t_cdf(-1.3, 6) == pytest.approx(1.0, abs=1e-14)
    with pytest.raises(s1.Refusal):
        lc.t_quantile(0.4, 5)


def test_the_t_based_seed_only_values_reproduce_ck3():
    """CK-3 section 4.5's 6-against-6 seed-only MDE (t with 10 df; 9 seeds: 16 df) from the a0 seed SD 1.1547 pp."""
    variance = 4 / 3                                                     # the seeds' O 4, 6, 4 pp
    se6 = lcheck.contrast_se_pp("seed_only", 6, variance, 0.0, 100, comparator=True)
    se9 = lcheck.contrast_se_pp("seed_only", 9, variance, 0.0, 100, comparator=True)
    assert lcheck.mde_t_pp(se6, 0.05, 0.8, 10) == pytest.approx(2.0715, abs=1e-3)
    assert lcheck.mde_t_pp(se9, 0.05, 0.8, 16) == pytest.approx(1.6246, abs=1e-3)


def test_the_ni_planning_report_reproduces_review_b_ni_power():
    """ni_power.out (review B): SE 4.1 pp gives P(feasible | true 0) 0.12 / 0.34 / 0.79 at tau 2 / 5 / 10 and the
    80% tau 10.2 pp; SE 4.1 * sqrt(100/500) gives 0.29 / 0.86 / 1.00 and 4.6 pp."""
    out = lcheck.ni_planning(4.1, [2, 5, 10], 0.95, 0.8)
    for tau, want in (("2", N.cdf(2 / 4.1 - Z95)), ("5", N.cdf(5 / 4.1 - Z95)), ("10", N.cdf(10 / 4.1 - Z95))):
        assert out["p_declared_feasible"][tau] == pytest.approx(want, rel=1e-12)
    assert [round(out["p_declared_feasible"][t], 2) for t in ("2", "5", "10")] == [0.12, 0.34, 0.79]
    assert out["smallest_tau_o_pp_with_power"] == pytest.approx((Z95 + Z80) * 4.1, rel=1e-12)
    assert round(out["smallest_tau_o_pp_with_power"], 1) == 10.2
    out500 = lcheck.ni_planning(4.1 * math.sqrt(100 / 500), [2, 5, 10], 0.95, 0.8)
    assert [round(out500["p_declared_feasible"][t], 2) for t in ("2", "5", "10")] == [0.29, 0.86, 1.0]
    assert round(out500["smallest_tau_o_pp_with_power"], 1) == 4.6


def test_the_paired_per_seed_se_has_ck3s_form():
    theta0 = [True] * 17 + [False] * 83
    seed = [True] + [False] * 16 + [True] * 3 + [False] * 80               # 1 shared, 16 theta0-only, 3 seed-only
    out = lcheck.per_seed_paired(theta0, seed)
    assert (out["theta0_only"], out["seed_only"], out["both"], out["discordant"]) == (16, 3, 1, 19)
    assert out["paired_se_pp"] == pytest.approx(100 * math.sqrt(19 / 100 ** 2 - 13 ** 2 / 100 ** 3), rel=1e-12)
    assert round(out["paired_se_pp"], 2) == 4.16


def test_tau_l_from_the_recorded_gate_a_means_is_the_known_answer():
    block = lcheck.tau_l_block(GATE_A_MEANS)
    assert block["s"] == KNOWN["s"] and block["tau_l"] == KNOWN["tau_l"]
    assert block["se_6v6"] == KNOWN["se_6v6"] and block["se_one_difference"] == KNOWN["se_one_difference"]
    assert block["ddof"] == 1 and block["mean_of_means"] == pytest.approx(1.5448907825335239, rel=1e-15)
    check = lcheck.known_answer(block, KNOWN, 1e-12)
    assert check["pass"] and all(v["bit_equal"] for v in check["values"].values())


def test_tau_l_by_hand_uses_ddof_1_and_the_root_two():
    block = lcheck.tau_l_block({"1101": 1.0, "1102": 1.25, "1103": 1.5})
    assert block["s"] == 0.25                                            # sqrt(0.125 / 2), not sqrt(0.125 / 3)
    assert block["tau_l"] == pytest.approx(2 * math.sqrt(2) * 0.25, rel=1e-15)
    assert block["tau_l"] == pytest.approx(0.7071067811865476, rel=1e-15)
    assert block["se_6v6"] == pytest.approx(0.25 / math.sqrt(3), rel=1e-15)
    assert block["se_one_difference"] == pytest.approx(0.25 * math.sqrt(2), rel=1e-15)


def test_a_changed_s_fails_the_known_answer_check():
    means = dict(GATE_A_MEANS)
    means["1102"] += 1e-9
    with pytest.raises(s1.Refusal, match="known-answer"):
        lcheck.known_answer(lcheck.tau_l_block(means), KNOWN, 1e-12)
    with pytest.raises(s1.Refusal, match="known-answer"):
        lcheck.known_answer(lcheck.tau_l_block(GATE_A_MEANS), {**KNOWN, "tau_l": KNOWN["tau_l"] * (1 + 1e-9)}, 1e-12)


SIMULATED = {"r1_2_bound_two_sided_90_upper": {"at_s_half_sigma": 22.2, "given_s_below_half_sigma": 52.3,
                                               "unconditional": 13.8}, "source": "a test"}


def test_the_two_df_record_in_closed_form():
    out = lcheck.two_df_record(2, SIMULATED)
    assert out["simulated_failure_rates_report_only"] == SIMULATED
    low, high = out["sigma_over_s_95pct"]
    assert low == pytest.approx(math.sqrt(2 / (-2 * math.log(0.025))), rel=1e-12) and round(low, 4) == 0.5207
    assert high == pytest.approx(math.sqrt(2 / (-2 * math.log(0.975))), rel=1e-12) and round(high, 4) == 6.2847
    assert round(out["p_s_below_half_sigma"], 4) == 0.2212 and round(out["p_s_below_sigma"], 4) == 0.6321
    assert out["tau_l_over_se_6v6_if_sigma_equals_s"] == pytest.approx(2 * math.sqrt(6), rel=1e-12)
    with pytest.raises(s1.Refusal):
        lcheck.two_df_record(3, SIMULATED)


def test_the_known_answer_in_the_settings_follows_the_l16_rule():
    numbers = lcheck.tau_l_numbers_from_s(KNOWN["s"])
    assert numbers == {k: KNOWN[k] for k in ("tau_l", "se_one_difference", "se_6v6")}
