"""The analysis: Student t quantiles against tabulated values, the Hoeffding half-width, no
zero-width inference from one block or a zero SD; every configured block reported, unobserved
outcomes bounded by their range beside a labelled complete-case view (an arm-dependent final
failure fixture shows why), incurred costs of aborted blocks and of started blocks without a result
kept as labelled lower bounds, unbounded costs never given a finite all-block mean, marginal and
Bonferroni family views, adverse choices, degeneration visibility and labels; the cost margin
T = C(S+) - r*C(S-) on the selection-plus-one-chosen-model subtotals (an extra reference run changes
the whole-research difference, not the margin), its one-off counterpart and the exploratory
both-scopes reading; per-scope completeness propagated to differences, means and the physical
total; confidence-level readings from the family Hoeffding bounds only; recorded costs (recomputed
from the durable records) replacing a result's provisional cost snapshot in every economic reading,
and refused when they do not belong to the results. Hand-made ENGINEERING FIXTURE block results; not
scientific numbers."""

from __future__ import annotations

import copy
import math

import pytest

from experiments.safety_decision_policy import analysis as an
from experiments.safety_decision_policy.common import PolicyError
from experiments.safety_decision_policy.config import config_sha256
from experiments.safety_decision_policy.costs import COST_CONTRACT

METHODS = ("S-", "S+")


def flags(complete: bool) -> dict:
    return {"timing_complete": complete, "incomplete_because": [] if complete else ["a fixture lower bound"]}


@pytest.mark.parametrize("df, expected", [(1, 12.706204736), (4, 2.776445105), (10, 2.228138852),
                                          (30, 2.042272456)])
def test_student_t_quantiles_match_tabulated_values(df, expected):
    assert an.student_t_ppf(0.975, df) == pytest.approx(expected, rel=1e-8)
    assert an.student_t_cdf(an.student_t_ppf(0.9, df), df) == pytest.approx(0.9, abs=1e-10)
    assert an.student_t_cdf(0.0, df) == pytest.approx(0.5)


def test_hoeffding_half_width_and_endpoint_summaries_never_claim_zero_width():
    assert an.hoeffding_half_width(8, 0.05, 2.0) == pytest.approx(2.0 * math.sqrt(math.log(40.0) / 16.0))
    one = an.endpoint_summary([0.1], [0.2], 0.95, (-1.0, 1.0))
    assert one["approximate_t"]["interval"] is None and "fewer than two" in one["approximate_t"]["reason"]
    flat = an.endpoint_summary([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.95, (-1.0, 1.0))
    assert flat["approximate_t"]["interval"] is None and "zero sample SD" in flat["approximate_t"]["reason"]
    low, high = flat["bounded_outcome"]["interval"]
    assert low < 0.0 < high
    varied = an.endpoint_summary([0.0, 0.1, 0.3], [0.1, 0.2, 0.4], 0.95, (-1.0, 1.0))
    a, b = varied["approximate_t"]["interval"]
    assert a < varied["mean_interval"][0] <= varied["mean_interval"][1] < b
    unbounded = an.endpoint_summary([10.0, 30.0], [10.0, 30.0], 0.95, None)
    assert unbounded["bounded_outcome"]["interval"] is None and "Hoeffding" in unbounded["bounded_outcome"]["reason"]


def contrast(raw: float, half: float = 0.01, broader: float = 0.05, tie_aware: float | None = None) -> dict:
    out = {"raw": raw, "missing_label": [raw - half, raw + half], "broader": [raw - broader, raw + broader]}
    if tie_aware is not None:
        out["tie_aware"] = tie_aware
    return out


def exact(loss: float) -> dict:
    return {"raw": loss, "missing_label": [loss, loss], "broader": [loss - 0.01, loss], "tie_aware": loss}


def identity(utility: bool = False) -> dict:
    out = {"raw": 0.0, "missing_label": [0.0, 0.0], "broader": [0.0, 0.0]}
    return {**out, "tie_aware": 0.0} if utility else out


A0_RELATIVE = {"safety_change": identity(), "utility_loss": identity(True), "refusal_increase": identity(),
               "diagnostics": None}


def edit_relative(d_f: float, loss: float = 0.0, refusal: float = 0.0, diagnostics: dict | None = None) -> dict:
    return {"safety_change": contrast(d_f), "utility_loss": exact(loss), "refusal_increase": contrast(refusal),
            "diagnostics": diagnostics or {"safety": {"empty": 0.0, "repetitive": 0.0, "capped": 0.0}}}


def costs(minus: float, plus: float, timed: bool = True, subtotals: tuple[float, float] | None = None,
          subtotal_timed: bool | None = None) -> dict:
    """Block costs as the controller writes them: whole-research totals and the
    selection-plus-one-chosen-model subtotals (by default equal to the totals: no reference run)."""
    sub = subtotals or (minus, plus)
    sub_timed = timed if subtotal_timed is None else subtotal_timed
    ledger = lambda total: {"total_seconds": total, **flags(timed)}  # noqa: E731
    subtotal = lambda seconds: {"seconds": seconds, **flags(sub_timed)}  # noqa: E731
    research = lambda seconds: {"seconds": seconds, **flags(timed)}  # noqa: E731
    return {"contract": COST_CONTRACT, "quoted": {m: {"total_quoted_used": 100.0} for m in METHODS},
            "actual": {"S-": ledger(minus), "S+": ledger(plus)}, "actual_s_plus_minus_s_minus": plus - minus,
            "selection_plus_chosen_model": {"S-": subtotal(sub[0]), "S+": subtotal(sub[1])},
            "reference_and_sensitivity": {"S-": research(minus - sub[0]), "S+": research(plus - sub[1])},
            "physical": {"seconds": plus + minus, **flags(timed)}}


def decided(config: dict, block: int, choices: dict, endpoints: dict, block_costs: dict, missing=()) -> dict:
    final = {arm: None if arm in missing else {"counts": {"safety": {"n": 100}}} for arm in {"a0", *choices.values()}}
    return {"block": block, "status": "final-incomplete" if missing else "complete",
            "config_sha256": config_sha256(config), "outcome_definition": config["outcome_definition"],
            "choices": choices, "final_missing": sorted(missing), "final": final,
            "endpoints": {"identical_choices": choices["S-"] == choices["S+"], **endpoints}, "costs": block_costs}


def aborted(config: dict, block: int) -> dict:
    incurred = {"S-": {"total_seconds": 40.0, **flags(True)}, "S+": {"total_seconds": 55.0, **flags(True)}}
    return {"block": block, "status": "aborted", "config_sha256": config_sha256(config),
            "outcome_definition": config["outcome_definition"], "stage": "S+ prerequisite",
            "reason": "attribution exhausted 2 technical attempts",
            "costs": {"contract": COST_CONTRACT, "incurred": incurred, "physical": {"seconds": 60.0, **flags(True)}}}


def started_evidence(block: int, minus: float, plus: float, physical: float, timed: bool = True) -> dict:
    """A started block's incurred costs as ``controller.started_block_costs`` records them."""
    scope = lambda total: {"actual": {"total_seconds": total, **flags(timed)},  # noqa: E731
                           "selection_plus_chosen_model": {"seconds": total, **flags(timed)},
                           "reference_and_sensitivity": {"seconds": 0.0, **flags(True)}}
    return {"contract": COST_CONTRACT, "block": block, "status": "started-without-result",
            "stage": "acquisition (both plans written)", "incurred": {"S-": scope(minus), "S+": scope(plus)},
            "physical": {"seconds": physical, **flags(timed)}, "scope": "incurred so far: lower bounds"}


def recorded_costs(block: int, block_costs: dict, status: str = "complete") -> dict:
    """A block's recorded costs as ``controller.recorded_block_costs`` returns them: the economic
    fields recomputed from the durable records; the quoted ledger stays in the result."""
    return {**{key: value for key, value in block_costs.items() if key != "quoted"}, "block": block,
            "result_status": status, "source": "recorded: fixture"}


@pytest.fixture
def study(example_config):
    """Five configured blocks. S- always keeps a0. Block 0: S+ chooses g-1 (safer, slightly more
    empty output). Block 1: both keep a0. Block 2: S+ chooses g-2, whose final deployment
    exhausts its retries (an ARM-DEPENDENT failure). Block 3: S+'s attribution prerequisite
    aborts the block. Block 4: started, no result."""
    config = copy.deepcopy(example_config)
    config["blocks"]["count"] = 5
    config["blocks"]["list"] = [{"block": b, "selector_seed_start": 2101 + b, "selector_seed_stride": 5,
                                 "final_seed": 9101 + b} for b in range(5)]
    g1 = edit_relative(-0.04, loss=0.01, diagnostics={"safety": {"empty": 0.02, "repetitive": 0.0, "capped": 0.0}})
    results = [
        decided(config, 0, {"S-": "a0", "S+": "g-1"},
                {"Y": contrast(0.04), "relative_to_a0": {"S-": A0_RELATIVE, "S+": g1},
                 "utility_contrast": contrast(-0.01, half=0.0, tie_aware=-0.01), "refusal_contrast": contrast(0.0)},
                costs(50.0, 70.0)),
        decided(config, 1, {"S-": "a0", "S+": "a0"},
                {"Y": identity(), "relative_to_a0": {"S-": A0_RELATIVE, "S+": A0_RELATIVE},
                 "utility_contrast": identity(True), "refusal_contrast": identity()},
                costs(52.0, 75.0)),
        decided(config, 2, {"S-": "a0", "S+": "g-2"},
                {"Y": None, "relative_to_a0": {"S-": A0_RELATIVE, "S+": None},
                 "utility_contrast": None, "refusal_contrast": None},
                costs(51.0, 90.0), missing=("g-2",)),
        aborted(config, 3)]
    return config, results


def test_every_configured_block_is_reported_and_missing_outcomes_are_bounded_not_dropped(study):
    config, results = study
    report = an.analyze(results, config, static_seconds=10.0, started=[4])
    assert [b["status"] for b in report["blocks"]["per_block"]] == [
        "complete", "complete", "final-incomplete", "aborted", "started-without-result"]
    assert "retries exhausted" in report["blocks"]["per_block"][2]["meaning"]
    assert report["blocks"]["per_block"][3]["stage"] == "S+ prerequisite"
    not_started = an.analyze(results, config)
    assert not_started["blocks"]["per_block"][4]["status"] == "not-run"
    y = report["endpoints"]["Y"]
    assert y["complete_case"]["raw"]["mean_interval"] == pytest.approx([0.02, 0.02])
    assert y["complete_case"]["raw"]["n_blocks"] == 2
    # all configured blocks: the arm-dependent failure (block 2), the abort and the unrun block take [-1, 1]
    assert y["all_configured"]["raw"]["n_blocks"] == 5
    assert y["all_configured"]["raw"]["mean_interval"] == pytest.approx([(0.04 - 3) / 5, (0.04 + 3) / 5])
    assert y["observed_blocks"] == [0, 1]
    # partial endpoints are kept: S- kept a0 in block 2, so L(S-) is exactly 0 there; L(S+) is unobserved
    assert report["endpoints"]["L(S-)"]["observed_blocks"] == [0, 1, 2]
    assert report["endpoints"]["L(S+)"]["observed_blocks"] == [0, 1]
    assert report["endpoints"]["L(S+)"]["complete_case"]["tie_aware"]["mean_interval"] == pytest.approx([0.005, 0.005])
    assert any("COMPLETE-CASE" in label and "not unconditional" in label for label in report["labels"])
    assert any("NOT confidence intervals" in label for label in report["labels"])


def test_costs_keep_incurred_spend_and_unbounded_walltime_gets_no_finite_all_block_mean(study):
    config, results = study
    report = an.analyze(results, config, static_seconds=10.0, started=[4])
    per_block = {c["block"]: c for c in report["costs"]["per_block"]}
    assert per_block[3]["actual_seconds"] == {"S-": 40.0, "S+": 55.0} and per_block[3]["difference"] is None
    assert "lower bounds" in per_block[3]["scope"]
    assert per_block[2]["difference"] == 39.0          # the failed final deployment is charged, not dropped
    cost = report["endpoints"]["actual_cost_difference"]
    assert cost["complete_case"]["mean_interval"] == pytest.approx([21.5, 21.5])
    assert cost["complete_case"]["bounded_outcome"]["interval"] is None
    assert cost["all_configured"]["interval"] is None and cost["all_configured"]["blocks_without_complete_cost"] == 2
    assert cost["observed_blocks"] == [0, 1, 2]
    # block 4 started without a result and no receipt evidence was supplied: unknown, never zero
    assert report["costs"]["physical_controller_seconds"] is None
    assert report["costs"]["physical_controller_seconds_recorded"] == pytest.approx(120.0 + 127.0 + 141.0 + 60.0 + 10.0)
    assert any("block 4" in r for r in report["costs"]["physical_controller_incomplete_because"])
    assert per_block[4]["actual_seconds"] is None and "never zero" in per_block[4]["scope"]
    assert per_block[3]["selection_plus_chosen_model_seconds"] == {"S-": 40.0, "S+": 55.0}
    assert per_block[3]["cost_margin"] is None
    assert per_block[2]["cost_margin"] == pytest.approx(90.0 - 1.1 * 51.0)   # failed final charged, kept
    readings = report["cost_tolerance"]["readings"]
    assert readings["all_configured"]["both_scopes"] == "unavailable"          # an abort and an unrun block
    assert readings["complete_case"]["both_scopes"] == "inconclusive: lack of precision"   # two blocks
    untimed = copy.deepcopy(results)
    untimed[0]["costs"] = costs(50.0, 70.0, timed=False)   # an interrupted attempt: lower bounds only
    report = an.analyze(untimed, config)
    assert report["endpoints"]["actual_cost_difference"]["complete_case"]["blocks_without_complete_cost"] == 1


def test_a_started_block_keeps_its_known_incurred_cost_once_as_lower_bounds(study):
    """Second review R2: the interrupted block 4 has paid receipts but no result. Its recorded
    spending stays in the physical total exactly once and in the per-block costs as lower bounds;
    its outcomes stay unobserved (range-bounded) and no cost endpoint or margin is formed."""
    config, results = study
    evidence = {4: started_evidence(4, 3000.0, 3400.0, 9400.0)}
    report = an.analyze(results, config, static_seconds=10.0, started=evidence)
    per_block = {c["block"]: c for c in report["costs"]["per_block"]}
    assert [c["block"] for c in report["costs"]["per_block"]] == [0, 1, 2, 3, 4]
    assert per_block[4]["status"] == "started-without-result" and per_block[4]["seconds_are"] == "lower bound"
    assert per_block[4]["actual_seconds"] == {"S-": 3000.0, "S+": 3400.0}
    assert per_block[4]["selection_plus_chosen_model_seconds"] == {"S-": 3000.0, "S+": 3400.0}
    assert per_block[4]["cost_margin"] is None and per_block[4]["difference"] is None
    assert report["costs"]["physical_controller_seconds"] == pytest.approx(120.0 + 127.0 + 141.0 + 60.0 + 10.0 + 9400.0)
    assert report["blocks"]["per_block"][4]["status"] == "started-without-result"
    assert report["endpoints"]["Y"]["observed_blocks"] == [0, 1]
    assert report["endpoints"]["Y"]["all_configured"]["raw"]["n_blocks"] == 5
    assert report["endpoints"]["cost_margin"]["all_configured"]["interval"] is None
    untimed = {4: started_evidence(4, 3000.0, 3400.0, 9400.0, timed=False)}   # an attempt closed at its lower bound
    report = an.analyze(results, config, static_seconds=10.0, started=untimed)
    assert report["costs"]["physical_controller_seconds"] is None
    assert report["costs"]["physical_controller_seconds_recorded"] == pytest.approx(
        120.0 + 127.0 + 141.0 + 60.0 + 10.0 + 9400.0)
    with pytest.raises(PolicyError):    # a block cannot be both started without a result and decided
        an.analyze(results, config, started={0: started_evidence(0, 1.0, 1.0, 1.0)})


def test_incomplete_cost_scopes_never_become_point_costs_differences_or_readings(example_config):
    """Third review C3: a whole-research ledger with unknown setup, or a physically complete block
    whose subtotal is a lower bound, yields named lower bounds only: no difference of lower bounds,
    no point mean, no margin, no cost reading."""
    config = three_blocks(example_config)
    results = reference_fixture(config)
    results[1]["costs"] = costs(1200.0, 1200.0, timed=False, subtotals=(1200.0, 1200.0), subtotal_timed=True)
    report = an.analyze(results, config, static_seconds=0.0)
    per_block = {c["block"]: c for c in report["costs"]["per_block"]}
    assert per_block[1]["difference"] is None and per_block[1]["actual_seconds_are"] == {
        "S-": "lower bound", "S+": "lower bound"}
    assert per_block[1]["incomplete_because"]["actual"]["S-"] == ["a fixture lower bound"]
    assert report["costs"]["complete_case_mean_actual_seconds"] == {"S-": None, "S+": None}
    assert report["costs"]["complete_case_mean_actual_seconds_lower_bound"] == pytest.approx(
        {"S-": 1100.0, "S+": (1450.0 + 1200.0 + 1100.0) / 3})
    assert report["costs"]["physical_controller_seconds"] is None    # that block's physical seconds are a bound
    assert per_block[1]["cost_margin"] == pytest.approx(1200.0 - 1.1 * 1200.0)   # the subtotal is complete
    results[1]["costs"] = costs(1200.0, 1200.0, subtotals=(1200.0, 1200.0), subtotal_timed=False)
    report = an.analyze(results, config, static_seconds=0.0)
    assert report["costs"]["physical_controller_seconds"] == pytest.approx(sum(
        r["costs"]["physical"]["seconds"] for r in results))   # physically complete ...
    assert report["costs"]["per_block"][1]["cost_margin"] is None                  # ... reconstruction is not
    assert report["costs"]["complete_case_mean_selection_plus_chosen_model_seconds"] is None
    assert report["costs"]["complete_case_mean_selection_plus_chosen_model_seconds_lower_bound"] == pytest.approx(
        {"S-": 1100.0, "S+": 1100.0})
    for view in ("all_configured", "complete_case"):
        assert report["cost_tolerance"]["readings"][view]["both_scopes"] == "unavailable"


def test_the_family_view_is_bonferroni_adjusted_and_labelled_apart_from_marginal_intervals(study):
    config, results = study
    report = an.analyze(results, config)
    family = report["family"]
    assert family["endpoints"] == ["Y", "L(S-)", "L(S+)", "O(S-)", "O(S+)", "cost_margin"]
    assert "1.1 * C(S-)" in family["definitions"]["cost_margin"]       # labelled by its actual margin
    assert family["per_endpoint_level"] == pytest.approx(1 - 0.05 / 6)
    marginal = report["endpoints"]["Y"]["all_configured"]["missing_label"]
    joint = family["all_configured"]["Y"]["missing_label"]
    assert marginal["coverage"] == "marginal" and joint["coverage"] == "family (Bonferroni)"
    assert joint["bounded_outcome"]["half_width"] > marginal["bounded_outcome"]["half_width"]
    assert family["all_configured"]["cost_margin"]["interval"] is None
    assert any("not simultaneous" in note.lower() or "NOT simultaneous" in note for note in family["notes"])
    assert report["analysis_plan"]["version"] == config["analysis"]["plan_version"]


def test_confidence_level_claims_read_only_the_family_hoeffding_bounds(study, example_config):
    """Inference-interpretation amendment: confidence-level claims come from the existing family
    Hoeffding bounds of the all-configured missing-label view (missing blocks and labels bounded);
    t-based readings are labelled working-assumption exploratory. No new estimator."""
    config, results = study
    report = an.analyze(results, config)
    claims = report["confidence_level_claims"]
    family_y = report["family"]["all_configured"]["Y"]["missing_label"]["bounded_outcome"]["interval"]
    assert claims["readings"]["Y"]["family_hoeffding_interval"] == family_y
    assert claims["readings"]["Y"]["confident_positive"] is False        # five blocks, three unobserved
    assert all(claims["readings"][n]["confidently_within_tolerance"] is False for n in ("L(S-)", "L(S+)", "O(S-)", "O(S+)"))
    assert claims["practical_margin_Y"] == 0.02 and "not proof of no effect" in claims["label"]
    assert any("WORKING-ASSUMPTION EXPLORATORY" in label for label in report["labels"])
    assert any(label.startswith("CONFIDENCE-LEVEL") for label in report["labels"])
    many = copy.deepcopy(example_config)      # 60 blocks where S+ always lowers Y by half
    many["blocks"]["count"] = 60
    many["blocks"]["list"] = [{"block": b, "selector_seed_start": 2101 + b, "selector_seed_stride": 100,
                               "final_seed": 9101 + b} for b in range(60)]
    safer = [decided(many, b, {"S-": "a0", "S+": "g-1"},
                     {"Y": contrast(0.5), "relative_to_a0": {"S-": A0_RELATIVE, "S+": edit_relative(-0.5)},
                      "utility_contrast": contrast(0.0, half=0.0, tie_aware=0.0), "refusal_contrast": contrast(0.0)},
                     costs(100.0, 100.0)) for b in range(60)]
    readings = an.analyze(safer, many)["confidence_level_claims"]["readings"]
    assert readings["Y"]["confident_positive"] is True and readings["Y"]["confidently_beyond_practical_margin"] is True
    assert readings["L(S+)"]["confidently_within_tolerance"] is False   # a 0.02 tolerance is not resolved here


def test_choices_adverse_choices_and_degeneration_stay_visible(study):
    config, results = study
    report = an.analyze(results, config)
    assert report["choices"] == {"S-": {"a0": 3}, "S+": {"a0": 1, "g-1": 1, "g-2": 1}}
    assert report["identical_choice_blocks"] == 1
    adverse = {a["block"]: a["reasons"] for a in report["adverse_choices"]["S+"]}
    assert "unobserved" in adverse[2][0]
    assert any("broader" in r for r in adverse[0])    # only the broader sensitivity could make g-1 less safe
    flagged = report["diagnostics"]["apparent_benefit_with_more_degenerate_output"]["S+"]
    assert flagged == [{"block": 0, "arm": "g-1", "raw_safety_change": -0.04, "increased_fractions": {"empty": 0.02}}]
    assert report["diagnostics"]["per_block"][2]["final_counts"]["g-2"] is None


def three_blocks(example_config: dict, development: dict | None = None) -> dict:
    config = copy.deepcopy(example_config)
    config["blocks"]["count"] = 3
    config["blocks"]["list"] = [{"block": b, "selector_seed_start": 2101 + b, "selector_seed_stride": 5,
                                 "final_seed": 9101 + b} for b in range(3)]
    if development is not None:
        config["overhead"]["development_seconds"] = development
    return config


def quiet(config: dict, block: int, plus_choice: str, block_costs: dict) -> dict:
    """A complete block: S- keeps a0; S+ keeps a0 or chooses an edit with no measured effect."""
    if plus_choice == "a0":
        endpoints = {"Y": identity(), "relative_to_a0": {"S-": A0_RELATIVE, "S+": A0_RELATIVE},
                     "utility_contrast": identity(True), "refusal_contrast": identity()}
    else:
        endpoints = {"Y": contrast(0.0), "relative_to_a0": {"S-": A0_RELATIVE, "S+": edit_relative(0.0)},
                     "utility_contrast": contrast(0.0, half=0.0, tie_aware=0.0), "refusal_contrast": contrast(0.0)}
    return decided(config, block, {"S-": "a0", "S+": plus_choice}, endpoints, block_costs)


def reference_fixture(config: dict) -> list[dict]:
    """Equal selection and chosen-run costs per block; S+ chooses an edit in blocks 0 and 1 and pays
    the extra 450 s reference a0 final there; S- keeps a0."""
    return [quiet(config, b, "g-1" if b < 2 else "a0", costs(c, c + (450.0 if b < 2 else 0.0), subtotals=(c, c)))
            for b, c in enumerate((1000.0, 1200.0, 1100.0))]


def test_an_extra_reference_run_moves_the_whole_research_difference_but_not_the_cost_margin(example_config):
    config = three_blocks(example_config)
    report = an.analyze(reference_fixture(config), config)
    ends = report["endpoints"]
    assert ends["actual_cost_difference"]["complete_case"]["mean_interval"] == pytest.approx([300.0, 300.0])
    assert ends["selection_cost_difference"]["complete_case"]["mean_interval"] == pytest.approx([0.0, 0.0])
    assert ends["cost_margin"]["complete_case"]["mean_interval"] == pytest.approx([-110.0, -110.0])   # -0.1 C
    assert ends["cost_margin"]["complete_case"]["bounded_outcome"]["interval"] is None
    assert "1.1 * C(S-)" in ends["cost_margin"]["definition"]
    per_block = {c["block"]: c for c in report["costs"]["per_block"]}
    assert [per_block[b]["cost_margin"] for b in range(3)] == pytest.approx([-100.0, -120.0, -110.0])
    assert per_block[0]["difference"] == pytest.approx(450.0) and per_block[0]["selection_cost_difference"] == 0.0
    assert per_block[0]["reference_and_sensitivity_seconds"] == {"S-": 0.0, "S+": 450.0}
    assert report["costs"]["complete_case_mean_selection_plus_chosen_model_seconds"] == pytest.approx(
        {"S-": 1100.0, "S+": 1100.0})
    for view in ("all_configured", "complete_case"):
        assert report["cost_tolerance"]["readings"][view] == {
            "selection_plus_chosen_model": "within tolerance", "one_off_with_development": "within tolerance",
            "both_scopes": "both cost scopes within tolerance under the working assumption (exploratory)"}
    assert "EXPLORATORY" in report["cost_tolerance"]["basis"] and "distribution-free" in report["cost_tolerance"]["basis"]
    assert any("not a production-savings claim" in label for label in report["labels"])


def test_the_one_off_margin_adds_unamortized_development_and_both_scopes_must_pass(example_config):
    config = three_blocks(example_config, {"S-": 0, "S+": 5000})
    report = an.analyze(reference_fixture(config), config)
    assert report["endpoints"]["one_off_cost_margin"]["complete_case"]["mean_interval"] == pytest.approx(
        [-110.0 + 5000.0, -110.0 + 5000.0])
    assert report["costs"]["one_off_complete_case_mean_selection_plus_chosen_model_plus_development_seconds"] == \
        pytest.approx({"S-": 1100.0, "S+": 6100.0})
    assert "per_decision_selection_plus_chosen_model_with_amortized_development_complete_case" not in report["costs"]
    reading = report["cost_tolerance"]["readings"]["complete_case"]
    assert reading["selection_plus_chosen_model"] == "within tolerance"
    assert reading["one_off_with_development"] == "exceeds tolerance"
    assert reading["both_scopes"] == "S+ exceeds the cost tolerance in at least one scope"
    spread = three_blocks(example_config)          # margins 200, -200, 0: imprecise, never acceptance
    results = [quiet(spread, b, "a0", costs(minus, plus))
               for b, (minus, plus) in enumerate(((1000.0, 1300.0), (1000.0, 900.0), (1000.0, 1100.0)))]
    reading = an.analyze(results, spread)["cost_tolerance"]["readings"]["complete_case"]
    assert reading == {"selection_plus_chosen_model": "inconclusive", "one_off_with_development": "inconclusive",
                       "both_scopes": "inconclusive: lack of precision"}


def test_an_untimed_reference_attempt_leaves_the_margin_and_a_lower_bound_subtotal_removes_it(example_config):
    config = three_blocks(example_config)
    results = reference_fixture(config)
    results[0]["costs"] = costs(1000.0, 1450.0, timed=False, subtotals=(1000.0, 1000.0), subtotal_timed=True)
    report = an.analyze(results, config)
    assert report["endpoints"]["actual_cost_difference"]["complete_case"]["interval"] is None
    assert report["endpoints"]["actual_cost_difference"]["observed_blocks"] == [1, 2]
    assert report["endpoints"]["cost_margin"]["observed_blocks"] == [0, 1, 2]
    assert report["endpoints"]["cost_margin"]["complete_case"]["mean_interval"] == pytest.approx([-110.0, -110.0])
    results[0]["costs"] = costs(1000.0, 1450.0, subtotals=(1000.0, 1000.0), subtotal_timed=False)
    report = an.analyze(results, config)
    assert report["endpoints"]["cost_margin"]["complete_case"]["interval"] is None
    assert report["costs"]["per_block"][0]["cost_margin"] is None
    assert report["costs"]["complete_case_mean_selection_plus_chosen_model_seconds"] is None
    assert report["cost_tolerance"]["readings"]["complete_case"]["both_scopes"] == "unavailable"


def test_recorded_costs_replace_the_result_s_snapshot_in_every_economic_reading(example_config):
    """Fourth review F1/F2. Every result's cost object is a provisional snapshot. With complete
    recorded costs the margins, means and the physical total come from the record alone; a
    complete-looking snapshot beside recorded costs that lack a session end record yields no
    margin, no point mean and no physical total; the bounded endpoints never change."""
    config = three_blocks(example_config)
    provisional = [quiet(config, b, "a0", costs(900.0, 990.0, timed=False)) for b in range(3)]   # snapshots
    complete = {b: recorded_costs(b, costs(c, c + 100.0)) for b, c in enumerate((1000.0, 1200.0, 1100.0))}
    alone = an.analyze(provisional, config, static_seconds=10.0)
    assert alone["endpoints"]["cost_margin"]["observed_blocks"] == [] and alone["costs"]["physical_controller_seconds"] is None
    assert all(c["cost_source"].startswith("result snapshot") for c in alone["costs"]["per_block"])
    report = an.analyze(provisional, config, static_seconds=10.0, recorded=complete)
    per_block = {c["block"]: c for c in report["costs"]["per_block"]}
    assert [per_block[b]["cost_margin"] for b in range(3)] == pytest.approx(
        [c + 100.0 - 1.1 * c for c in (1000.0, 1200.0, 1100.0)])
    assert all(per_block[b]["cost_source"] == "recorded: fixture" for b in range(3))
    assert per_block[0]["quoted_used"] == {"S-": 100.0, "S+": 100.0}            # the immutable quoted ledger
    assert per_block[0]["selection_plus_chosen_model_seconds"] == {"S-": 1000.0, "S+": 1100.0}
    assert report["endpoints"]["cost_margin"]["observed_blocks"] == [0, 1, 2]
    assert report["costs"]["complete_case_mean_selection_plus_chosen_model_seconds"] == pytest.approx(
        {"S-": 1100.0, "S+": 1200.0})
    assert report["costs"]["physical_controller_seconds"] == pytest.approx(2 * 3300.0 + 300.0 + 10.0)
    assert report["costs"]["cost_source"].startswith("recorded")
    assert report["endpoints"]["Y"] == alone["endpoints"]["Y"]
    # the mirror: snapshots that look complete, block 1's recorded costs without a session end record
    looks_complete = [quiet(config, b, "a0", costs(900.0, 990.0)) for b in range(3)]
    assert an.analyze(looks_complete, config)["endpoints"]["cost_margin"]["observed_blocks"] == [0, 1, 2]
    killed = {**complete, 1: recorded_costs(1, costs(1150.0, 1240.0, timed=False))}
    report = an.analyze(looks_complete, config, static_seconds=10.0, recorded=killed)
    per_block = {c["block"]: c for c in report["costs"]["per_block"]}
    assert per_block[1]["cost_margin"] is None and per_block[1]["difference"] is None
    assert per_block[1]["physical_seconds_are"] == "lower bound"
    assert per_block[1]["physical_incomplete_because"] == ["a fixture lower bound"]
    assert per_block[1]["selection_plus_chosen_model_seconds"] == {"S-": 1150.0, "S+": 1240.0}   # the record's
    assert per_block[1]["selection_plus_chosen_model_seconds_are"] == {"S-": "lower bound", "S+": "lower bound"}
    assert report["endpoints"]["cost_margin"]["observed_blocks"] == [0, 2]
    assert report["endpoints"]["cost_margin"]["complete_case"]["interval"] is None
    assert report["costs"]["complete_case_mean_selection_plus_chosen_model_seconds"] is None
    assert report["costs"]["physical_controller_seconds"] is None
    assert report["costs"]["physical_controller_seconds_recorded"] == pytest.approx(2100.0 + 2390.0 + 2300.0 + 10.0)
    assert any("block 1" in why for why in report["costs"]["physical_controller_incomplete_because"])
    assert report["cost_tolerance"]["readings"]["complete_case"]["both_scopes"] == "unavailable"


def test_recorded_costs_of_an_aborted_block_replace_its_snapshot(study):
    config, results = study
    recorded = {b: recorded_costs(b, results[b]["costs"], results[b]["status"]) for b in range(3)}
    recorded[3] = {"contract": COST_CONTRACT, "block": 3, "result_status": "aborted", "source": "recorded: fixture",
                   "incurred": {"S-": {"total_seconds": 41.0, **flags(True)}, "S+": {"total_seconds": 57.0, **flags(True)}},
                   "physical": {"seconds": 66.0, **flags(True)}}
    report = an.analyze(results, config, static_seconds=10.0, recorded=recorded)
    entry = report["costs"]["per_block"][3]
    assert entry["actual_seconds"] == {"S-": 41.0, "S+": 57.0} and entry["physical_seconds"] == 66.0
    assert entry["cost_margin"] is None and entry["cost_source"] == "recorded: fixture"
    assert report["costs"]["physical_controller_seconds"] == pytest.approx(120.0 + 127.0 + 141.0 + 66.0 + 10.0)


def test_recorded_costs_that_do_not_belong_to_the_results_are_refused(study):
    config, results = study
    good = {b: recorded_costs(b, results[b]["costs"], results[b]["status"]) for b in range(3)}
    good[3] = {**results[3]["costs"], "block": 3, "result_status": "aborted", "source": "recorded: fixture"}
    an.analyze(results, config, recorded=good)                                    # the control
    refused = {
        "another contract": {**good, 0: {**good[0], "contract": "stage-B block costs v2"}},
        "another block": {**good, 0: {**good[0], "block": 1}},
        "another result status": {**good, 0: {**good[0], "result_status": "aborted"}},
        "a block without a result": {**good, 4: recorded_costs(4, costs(1.0, 1.0))},
        "a result left out": {b: record for b, record in good.items() if b != 2},
        "an economic field missing": {**good, 0: {k: v for k, v in good[0].items() if k != "physical"}},
    }
    for recorded in refused.values():
        with pytest.raises(PolicyError):
            an.analyze(results, config, started=[4], recorded=recorded)


def test_results_of_another_configuration_or_duplicates_are_refused(study):
    config, results = study
    other = copy.deepcopy(config)
    other["budget"]["total_quote_seconds"] += 1
    with pytest.raises(PolicyError):
        an.analyze(results, other)
    with pytest.raises(PolicyError):
        an.analyze([*results, results[0]], config)
