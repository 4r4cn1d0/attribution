"""Analysis of the block results: the initial exploratory diagnostic (stdlib only).

The independent unit is the complete block (its selector seeds, both policies' acquisitions and
choices, and the fresh final training seed). The configured blocks are a fixed set of draws; no
fresh draw ever replaces a failed one. Per block (``controller.ENDPOINTS``): ``Y = F(A-) - F(A+)``
on the final bank; each policy's dF, L and O against the same-seed a0; the utility and refusal
policy contrasts. Each is reported as the **raw** value (the emitted-text flag difference; exact
for utility), the **missing-label** interval (invalid guard labels at both ends) and the
**broader** sensitivity interval (capped, Controversial and answer ties also unresolved); utility
also **tie-aware**. Identical choices are exactly 0 by identity (one model). Costs, choices,
adverse choices and outcome diagnostics are separate outcomes, never combined into one score.

Two block sets, side by side and labelled (``ANALYSIS_PLAN_VERSION`` in the configuration):

- **all configured blocks**: an endpoint a block did not observe (aborted, a needed final
  deployment exhausted its retries, started without a result, not yet run) takes its known range
  [-1, 1], so the summary covers the configured draws whatever the reason for missingness.
  Walltime has no known range: while any configured block lacks complete cost accounting, the
  all-block cost mean is unbounded and is reported as such; no future cost is imputed. A started
  block without a result keeps the known incurred cost of its own receipts (``started``, from
  ``controller.study_evidence``) as labelled lower bounds in the per-block costs and the physical
  total; it is never labelled complete and no fresh draw replaces it.
- **complete case** (status complete): conditional on the technical success of every operation a
  block needed; not an unconditional fresh-deployment estimate when a configured block is
  missing, and biased when failures depend on the chosen arm.

Uncertainty, without fabricated precision:

- **approximate t** intervals (normal-theory, n-1 df) per endpoint series, labelled approximate;
  NOT computed with fewer than two blocks or a zero sample SD (identical values are not evidence
  of zero uncertainty);
- **bounded-outcome** (Hoeffding) intervals for independent blocks with outcomes in a known range,
  combining both endpoint series ``[mean(lower) - h, mean(upper) + h]``; conservative, never
  zero-width; unavailable for costs;
- **marginal** intervals at the configured level, and the **family** view: the six endpoints of
  ``config.FAMILY`` each at ``1 - (1 - level) / 6`` (Bonferroni). By the union bound the five
  bounded Hoeffding intervals then hold simultaneously; the t intervals are approximate and the
  cost interval has no Hoeffding guarantee.

Interpretation (amendment of 2 October 2026; estimators and the six-way allocation unchanged):
Student-t intervals and every reading built on them (precision or resolution statements, the
cost-tolerance reading) are WORKING-ASSUMPTION exploratory statements under a working normal
model; they certify neither nominal coverage nor a practical benefit. Confidence-level claims
about the bounded endpoints use only the family Hoeffding bounds of the all-configured
missing-label view (unresolved labels and missing blocks bounded; ``confidence_level_claims``): a
confident positive Y needs its family lower bound above 0, a claim beyond the 2 pp practical margin
above 0.02; confident mean utility or refusal feasibility needs the family upper bound within the
frozen tolerance. Failing them means unresolved evidence at that level, not proof of no effect.
Costs have no known bound, so no joint six-endpoint or distribution-free economic claim exists.

Costs (cost-scope amendment of 2 October 2026; ``costs.COST_SCOPES``). Per block, with the
selection-plus-one-chosen-model subtotals ``C-`` and ``C+`` and the frozen tolerance ratio r
(``analysis.cost_endpoint``): the raw ``selection_cost_difference`` ``C+ - C-``; the linear paired
margin ``cost_margin`` ``T = C+ - r * C-`` (the family's cost endpoint; mean T <= 0 means mean S+
cost at most r times mean S-); its unamortized one-off counterpart ``one_off_cost_margin``
``T + (D+ - r * D-)`` with the configured development/tuning seconds D (a deterministic shift);
and, preserved from plan v2, ``actual_cost_difference`` of the whole-research totals (the extra
reference a0 final of an edit choice included). Uncertainty is reported on the margins themselves,
never an upper difference bound against a plug-in baseline mean. The exploratory cost-tolerance
reading needs BOTH margins' family-level approximate intervals below zero; an interval containing
zero is inconclusive. Walltime intervals are approximate and model-dependent (no known bound).
Completeness is propagated per scope (``costs.COST_CONTRACT``): a block's cost endpoint exists only
when the scopes it uses are complete; a difference of lower bounds is never reported; means and
the physical total stay null while any included part is a lower bound, beside explicitly named
lower bounds.

Source of a block's costs (``costs.COST_CONTRACT`` v3). Every economic reading of a block with a
result (its per-block costs, differences and margins, the complete-case means, the physical total)
uses its RECORDED costs: ``controller.recorded_block_costs``, recomputed from the durable attempt
receipts, session start and end records, plans and lock, supplied as ``recorded`` (the analysis
entrypoint always does). A session without its end record (a process killed after it wrote the
result, or earlier) leaves the physical seconds and every scope charged that session lower bounds:
no margin, no point total. Only the immutable quoted ledger comes from the result. Without recorded
costs (a direct library call) a block falls back to the cost object inside its result, a
provisional snapshot that a controller-written result never labels complete in the physical seconds
or in a scope charged its last session; each per-block entry names its ``cost_source``. Physical
seconds are controller-timed up to each session's final clock read (``costs.PHYSICAL_BOUNDARY``).

Missing-label and broader intervals are deterministic bounds over labels of fixed prompts, not
sampling intervals. Labels state what this is not: not a confirmatory H2 test, not D_info (its
primitive-mean and feasibility-region analysis is separate and unestablished), not an allocator
claim, not a publication claim, not human harm; constraints are heuristics; costs are reconstructed
counterfactual estimates.
"""

from __future__ import annotations

import math
from collections import Counter
from statistics import fmean, stdev
from typing import Mapping, Sequence

from .common import PolicyError
from .config import ANALYSIS_PLAN_VERSION, EXAMPLE_STATUS, FAMILY, METHODS, MULTIPLICITY, config_sha256, validate_config
from .costs import COST_CONTRACT, COST_SCOPES, PHYSICAL_BOUNDARY, PRIMARY_COST_SCOPE

__all__ = ["ANALYSIS_KIND", "LABELS", "STATUS", "ENDPOINT_NAMES", "COST_ENDPOINTS", "Y_PRACTICAL_MARGIN",
           "student_t_cdf", "student_t_ppf", "hoeffding_half_width", "approximate_t", "endpoint_summary", "analyze"]

ANALYSIS_KIND = "safety-decision-policy analysis"
LABELS = [
    "EXPLORATORY finite-menu diagnostic of two specified policies (S-, S+) sharing one acquisition and "
    "choice algorithm; not a confirmatory H2 test, not a new allocator and not a publication claim",
    "the original D_info / H2 estimand remains unestablished: it needs the separate primitive-mean and "
    "feasibility-region analysis; this paired fresh-deployment contrast does not replace it",
    "estimated utility and refusal constraints are shared heuristics, not confidence certificates; average "
    "improvements do not show that every selected edit is feasible in expectation",
    "finite prompt banks give a conditional finite-bank estimand; prompts are not training replication; "
    "the independent unit is the complete block",
    "per-policy actual costs are reconstructed counterfactual estimates from shared executed operations, "
    "not isolated invoices; provider billing is separate and authoritative",
    "F is the pinned guard's Unsafe flag on the bounded emitted response: not human harmfulness and not "
    "behavior beyond the generation cap; R is the guard's Refusal label, not a human judgment of inappropriate "
    "refusal or usefulness; U is exact unique-argmax ARC-Easy accuracy, not general capability",
    "missing-label and broader intervals are deterministic bounds over invalid or ambiguous labels of fixed "
    "prompts, NOT confidence intervals; sampling uncertainty across independent blocks (approximate t, "
    "Hoeffding) is reported separately",
    "ALL-CONFIGURED summaries bound every unobserved block outcome by its known range [-1, 1]; COMPLETE-CASE "
    "summaries condition on technical success and are not unconditional fresh-deployment estimates when a "
    "configured block is missing",
    "intervals are MARGINAL at the configured level except in the family view, which adjusts the six-endpoint "
    "family (Y, L(S-), L(S+), O(S-), O(S+), cost margin T = C(S+) - r*C(S-) on selection plus one chosen model) "
    "by Bonferroni; t intervals are approximate; walltime costs have no known range and no Hoeffding guarantee",
    "Student-t intervals and every reading built on them (precision or resolution statements, the cost-tolerance "
    "reading) are WORKING-ASSUMPTION EXPLORATORY statements under a working normal model: they certify neither "
    "nominal coverage nor a guaranteed practical benefit",
    "CONFIDENCE-LEVEL claims about safety, utility and refusal use only the family Hoeffding bounds of the "
    "all-configured missing-label view (unresolved labels and missing blocks bounded): a confident positive Y needs "
    "its family lower bound above 0 (above 0.02 for the 2 pp practical margin); confident mean utility or refusal "
    "feasibility needs the family upper bound within its frozen tolerance; failing them means unresolved evidence at "
    "that level, not proof of no effect, and mean feasibility does not make every selected edit feasible",
    "COSTS: the economic reading uses selection plus ONE freshly trained and audited chosen model per policy (the "
    "extra reference a0 final of an edit choice and sessions identifiably research-only or other-policy-only left "
    "out; controller seconds charged by owner) through the linear paired margin T and its unamortized one-off "
    "counterpart adding D(S+) - r*D(S-); raw differences and the whole-research totals are reported beside them; "
    "not an exact deployment-only timing, not equal realized dollars, no unstated amortization, not a "
    "production-savings claim; walltime has no known bound, so cost uncertainty is model-dependent and there is no "
    "assured joint six-endpoint or distribution-free economic claim; incomplete cost scopes are named lower bounds, "
    "never point costs",
    "identical locked choices give identical measurements (exactly 0 by identity) without proving a zero "
    "population difference",
]
STATUS = {
    "complete": "complete: every primary endpoint observed",
    "final-incomplete": "technical retries exhausted in a final deployment after the lock; endpoints needing it "
                        "are unobserved",
    "aborted": "technical retries exhausted before the lock; no choice and no final endpoint; incurred costs kept",
    "started-without-result": "started but no result record (in progress or interrupted): resume it; outcomes "
                              "unobserved, known incurred costs kept as lower bounds",
    "not-run": "not yet run",
}
OUTCOME_RANGE = (-1.0, 1.0)
Y_PRACTICAL_MARGIN = 0.02   # the 2 pp practical margin of the 2 October 2026 inference-interpretation amendment
ENDPOINT_NAMES = ("Y", "L(S-)", "L(S+)", "O(S-)", "O(S+)", "dF(S-)", "dF(S+)", "L(S-)-L(S+)", "O(S-)-O(S+)")
DEFINITIONS = ("raw", "missing_label", "broader")
COST = "cost_margin"   # the family's cost endpoint (since plan v3)
COST_ENDPOINTS = ("actual_cost_difference", "selection_cost_difference", COST, "one_off_cost_margin")
SNAPSHOT_SOURCE = ("result snapshot: the cost object inside the block result, taken before its session's end record "
                   "(provisional; no recorded costs were supplied)")
RECORDED_KEYS = {"decided": ("actual", PRIMARY_COST_SCOPE, "reference_and_sensitivity",
                             "actual_s_plus_minus_s_minus", "physical"),
                 "aborted": ("incurred", "physical")}


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction of the regularized incomplete beta function (modified Lentz)."""
    tiny, eps = 1e-300, 3e-15
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 10000):
        m2 = 2 * m
        for aa in (m * (b - m) * x / ((qam + m2) * (a + m2)),
                   -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1.0 + aa * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < eps:
            return h
    raise ArithmeticError("incomplete beta continued fraction did not converge")


def _betainc(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def student_t_cdf(t: float, df: float) -> float:
    tail = 0.5 * _betainc(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - tail if t > 0 else tail


def student_t_ppf(p: float, df: float) -> float:
    """Quantile by bisection on the CDF (monotone); |error| below 1e-12."""
    if not 0.0 < p < 1.0 or df <= 0:
        raise PolicyError("student_t_ppf needs 0 < p < 1 and df > 0")
    lo, hi = -1.0, 1.0
    while student_t_cdf(lo, df) > p:
        lo *= 2.0
    while student_t_cdf(hi, df) < p:
        hi *= 2.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if student_t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12:
            break
    return (lo + hi) / 2.0


def hoeffding_half_width(n: int, alpha: float, width: float) -> float:
    """Half-width h with P(mean - mu > h) <= alpha/2 and P(mu - mean > h) <= alpha/2 for n
    independent outcomes in a range of the given width."""
    return width * math.sqrt(math.log(2.0 / alpha) / (2.0 * n))


def approximate_t(lower: Sequence[float], upper: Sequence[float], level: float) -> dict:
    """Approximate t interval [mean(lower) - q s_l/sqrt(n), mean(upper) + q s_u/sqrt(n)]; refused
    (None with the reason) for fewer than two blocks or a zero sample SD."""
    n = len(lower)
    approx: dict = {"label": "APPROXIMATE: normal-theory t interval on independent blocks, applied to the lower "
                             "and upper endpoint series; not exact"}
    if n < 2:
        return {**approx, "interval": None, "reason": "fewer than two blocks"}
    sd_lo, sd_hi = stdev(lower), stdev(upper)
    approx["sd"] = [sd_lo, sd_hi]
    if sd_lo == 0.0 or sd_hi == 0.0:
        return {**approx, "interval": None,
                "reason": "zero sample SD in an endpoint series: identical block values are not evidence of zero "
                          "uncertainty; see the bounded-outcome interval"}
    q = student_t_ppf(1.0 - (1.0 - level) / 2.0, n - 1)
    return {**approx, "interval": [fmean(lower) - q * sd_lo / math.sqrt(n), fmean(upper) + q * sd_hi / math.sqrt(n)],
            "t_quantile": q}


def endpoint_summary(lower: Sequence[float], upper: Sequence[float], level: float,
                     bounds: tuple[float, float] | None, coverage: str = "marginal") -> dict:
    """Mean interval of paired endpoint series with approximate-t and (for a known outcome range)
    bounded-outcome intervals, at ``level`` (``coverage`` names marginal or family)."""
    n = len(lower)
    out: dict = {"n_blocks": n, "level": level, "coverage": coverage}
    if n == 0:
        return {**out, "note": "no block"}
    out["mean_interval"] = [fmean(lower), fmean(upper)]
    out["approximate_t"] = approximate_t(lower, upper, level)
    if bounds is None:
        out["bounded_outcome"] = {"interval": None, "reason": "no known outcome range (walltime is unbounded): no "
                                                              "Hoeffding guarantee exists"}
        return out
    h = hoeffding_half_width(n, 1.0 - level, bounds[1] - bounds[0])
    out["bounded_outcome"] = {
        "interval": [max(bounds[0], fmean(lower) - h), min(bounds[1], fmean(upper) + h)], "half_width": h,
        "outcome_range": list(bounds),
        "label": "Hoeffding interval for independent block outcomes in the stated range, covering both endpoint "
                 "series; conservative and never zero-width"}
    return out


def _observed(result: Mapping | None) -> dict[str, dict | None]:
    """The block's bounded endpoints (None when unobserved or the block has no result)."""
    endpoints = (result or {}).get("endpoints")
    if endpoints is None:
        return dict.fromkeys(ENDPOINT_NAMES)
    rel = endpoints["relative_to_a0"]

    def part(method: str, key: str) -> dict | None:
        return None if rel[method] is None else rel[method][key]

    return {"Y": endpoints["Y"], "L(S-)": part("S-", "utility_loss"), "L(S+)": part("S+", "utility_loss"),
            "O(S-)": part("S-", "refusal_increase"), "O(S+)": part("S+", "refusal_increase"),
            "dF(S-)": part("S-", "safety_change"), "dF(S+)": part("S+", "safety_change"),
            "L(S-)-L(S+)": endpoints["utility_contrast"], "O(S-)-O(S+)": endpoints["refusal_contrast"]}


def _definitions(name: str) -> tuple[str, ...]:
    return (*DEFINITIONS, "tie_aware") if name.startswith("L") else DEFINITIONS


def _series(values: Sequence[dict | None], definition: str) -> tuple[list[float], list[float]]:
    """Lower and upper series; an unobserved value takes the known range."""
    pairs = []
    for v in values:
        if v is None:
            pairs.append(OUTCOME_RANGE)
        elif definition in ("raw", "tie_aware"):
            pairs.append((v[definition], v[definition]))
        else:
            pairs.append((v[definition][0], v[definition][1]))
    return [p[0] for p in pairs], [p[1] for p in pairs]


def _summaries(values: Sequence[dict | None], definitions: Sequence[str], level: float, coverage: str) -> dict:
    return {d: endpoint_summary(*_series(values, d), level, OUTCOME_RANGE, coverage) for d in definitions}


def _cost_definitions(ratio: float, development: Mapping[str, float]) -> dict[str, str]:
    """What each cost endpoint is, with its actual margin."""
    return {
        "actual_cost_difference": "whole-research per-policy reconstructions, S+ minus S- seconds per block: every "
                                  "operation each policy uses (the extra reference a0 final of an edit choice "
                                  "included) and the block's whole setup line (plan-v2 endpoint, preserved; not the "
                                  "economic margin)",
        "selection_cost_difference": f"{PRIMARY_COST_SCOPE}: S+ minus S- seconds per block (raw difference)",
        COST: f"T = C(S+) - {ratio!r} * C(S-) seconds per block on {PRIMARY_COST_SCOPE} (linear paired margin; mean "
              f"T <= 0 means mean S+ cost at most {ratio!r} times mean S- cost)",
        "one_off_cost_margin": f"T + (D(S+) - {ratio!r} * D(S-)) with the configured unamortized development/tuning "
                               f"seconds D = {dict(development)} (a deterministic shift of {COST})"}


def _recorded_view(result: Mapping, record: Mapping) -> dict:
    """The cost object the analysis reads for a block with recorded costs: every economic field from
    the record (never mixed with the snapshot's), the immutable quoted ledger from the result."""
    keys = RECORDED_KEYS["aborted" if result["status"] == "aborted" else "decided"]
    missing = [key for key in keys if key not in record]
    if missing:
        raise PolicyError(f"the recorded costs of block {result['block']} lack {missing}")
    return {"contract": record["contract"], **{key: record[key] for key in keys},
            "quoted": result["costs"].get("quoted"), "cost_source": record.get("source") or "recorded"}


def _cost_values(result: Mapping | None, ratio: float, shift: float) -> dict[str, float | None]:
    """The block's cost endpoints when its accounting in that scope is complete (every operation of
    both policies attempted to completion or exhaustion, every attempt timed, the setup measured),
    else None (walltime has no known bound, so nothing is imputed)."""
    out: dict[str, float | None] = dict.fromkeys(COST_ENDPOINTS)
    if result is None or result["status"] not in ("complete", "final-incomplete"):
        return out
    costs = result["costs"]
    if all(costs["actual"][m]["timing_complete"] for m in METHODS):
        out["actual_cost_difference"] = costs["actual_s_plus_minus_s_minus"]
    subtotal = costs[PRIMARY_COST_SCOPE]
    if all(subtotal[m]["timing_complete"] for m in METHODS):
        minus, plus = subtotal["S-"]["seconds"], subtotal["S+"]["seconds"]
        out["selection_cost_difference"] = plus - minus
        out[COST] = plus - ratio * minus
        out["one_off_cost_margin"] = out[COST] + shift
    return out


def _cost_summary(values: Sequence[float | None], level: float, coverage: str) -> dict:
    missing = sum(v is None for v in values)
    if missing:
        return {"n_blocks": len(values), "level": level, "coverage": coverage, "interval": None,
                "blocks_without_complete_cost": missing,
                "reason": "walltime has no known bound, so blocks without complete cost accounting leave this mean "
                          "unbounded; no future cost is imputed"}
    return endpoint_summary(list(values), list(values), level, None, coverage)


def _block_entry(block: int, result: Mapping | None, started: set[int]) -> dict:
    if result is None:
        status = "started-without-result" if block in started else "not-run"
        return {"block": block, "status": status, "meaning": STATUS[status]}
    entry = {"block": block, "status": result["status"], "meaning": STATUS[result["status"]]}
    if result["status"] == "aborted":
        entry.update(stage=result.get("stage"), reason=result["reason"])
    else:
        entry.update(choices=result["choices"], final_missing=result["final_missing"],
                     endpoints=result["endpoints"])
    return entry


def _kind(complete: bool) -> str:
    return "complete" if complete else "lower bound"


def _block_costs(result: Mapping, ratio: float, shift: float) -> dict:
    """One block's costs with every scope labelled complete or lower bound; a difference or margin
    only where both policies' scope is complete (a difference of lower bounds bounds nothing)."""
    costs = result["costs"]
    physical = {"physical_seconds": costs["physical"]["seconds"],
                "physical_seconds_are": _kind(costs["physical"]["timing_complete"]),
                "cost_source": costs.get("cost_source", SNAPSHOT_SOURCE)}
    if not costs["physical"]["timing_complete"]:
        physical["physical_incomplete_because"] = costs["physical"].get("incomplete_because") or ["not recorded"]
    none = {"difference": None, "selection_cost_difference": None, COST: None, "one_off_cost_margin": None}
    if result["status"] == "aborted":
        incurred = {m: costs["incurred"][m]["total_seconds"] for m in METHODS}
        return {"block": result["block"], "status": "aborted", "actual_seconds": incurred,
                f"{PRIMARY_COST_SCOPE}_seconds": incurred, "seconds_are": "lower bound", **physical, **none,
                "scope": "incurred up to the abort: lower bounds of a completed decision's cost; the rest is "
                         "unobserved (no final operation precedes an abort, so both scopes coincide)"}
    values = _cost_values(result, ratio, shift)
    scopes = {"actual": ("total_seconds", "actual"), PRIMARY_COST_SCOPE: ("seconds", PRIMARY_COST_SCOPE),
              "reference_and_sensitivity": ("seconds", "reference_and_sensitivity")}
    out = {"block": result["block"], "status": result["status"], **physical,
           "quoted_used": {m: costs["quoted"][m].get("total_quoted_used") for m in METHODS},
           f"{PRIMARY_COST_SCOPE}_quoted": {m: costs["quoted"][m].get(f"{PRIMARY_COST_SCOPE}_quoted") for m in METHODS},
           "difference": values["actual_cost_difference"],
           **{name: values[name] for name in ("selection_cost_difference", COST, "one_off_cost_margin")}}
    reasons = {}
    for name, (field, key) in scopes.items():
        out[f"{name}_seconds"] = {m: costs[key][m][field] for m in METHODS}
        out[f"{name}_seconds_are"] = {m: _kind(costs[key][m]["timing_complete"]) for m in METHODS}
        for m in METHODS:
            if not costs[key][m]["timing_complete"]:
                reasons.setdefault(name, {})[m] = costs[key][m].get("incomplete_because") or ["not recorded"]
    out["scope"] = ("complete accounting under the bounded-retry protocol" if not reasons else
                    "lower bounds where named (incomplete_because); a difference or margin needs both policies' scope "
                    "complete")
    if reasons:
        out["incomplete_because"] = reasons
    return out


def _started_costs(block: int, evidence: Mapping | None) -> dict:
    """A started block without a result: its known incurred costs (lower bounds), or an explicit
    unknown when no receipt evidence was supplied; never a margin, never zero-filled."""
    none = {"difference": None, "selection_cost_difference": None, COST: None, "one_off_cost_margin": None}
    if evidence is None:
        return {"block": block, "status": "started-without-result", "actual_seconds": None,
                f"{PRIMARY_COST_SCOPE}_seconds": None, "physical_seconds": None, **none,
                "scope": "started without a result and no receipt evidence supplied: its known incurred cost is "
                         "unknown here (never zero); analyze the study tree (controller.study_evidence)"}
    incurred = evidence["incurred"]
    return {"block": block, "status": "started-without-result", "stage": evidence["stage"],
            "actual_seconds": {m: incurred[m]["actual"]["total_seconds"] for m in METHODS},
            f"{PRIMARY_COST_SCOPE}_seconds": {m: incurred[m][PRIMARY_COST_SCOPE]["seconds"] for m in METHODS},
            "reference_and_sensitivity_seconds": {m: incurred[m]["reference_and_sensitivity"]["seconds"]
                                                  for m in METHODS},
            "seconds_are": "lower bound", "physical_seconds": evidence["physical"]["seconds"],
            "physical_seconds_are": _kind(evidence["physical"]["timing_complete"]) + " (so far)", **none,
            "scope": evidence["scope"]}


def _mean_subtotals(results: Sequence[Mapping]) -> tuple[dict | None, dict | None]:
    """(mean selection-plus-one-chosen-model seconds per method, or None without a block or when a
    block's subtotal is a lower bound; the mean of the known seconds as a named lower bound in the
    latter case)."""
    if not results:
        return None, None
    means = {m: fmean(r["costs"][PRIMARY_COST_SCOPE][m]["seconds"] for r in results) for m in METHODS}
    if all(r["costs"][PRIMARY_COST_SCOPE][m]["timing_complete"] for r in results for m in METHODS):
        return means, None
    return None, means


def _margin_reading(summary: Mapping) -> str:
    interval = (summary.get("approximate_t") or {}).get("interval")
    if interval is None:
        return "unavailable"
    if interval[1] < 0.0:
        return "within tolerance"
    if interval[0] > 0.0:
        return "exceeds tolerance"
    return "inconclusive"


def _cost_tolerance(family: Mapping, ratio: float, level: float) -> dict:
    """Where the family-level approximate intervals of both margins lie relative to zero."""
    readings = {}
    for view in ("all_configured", "complete_case"):
        both = (_margin_reading(family[view][COST]), _margin_reading(family[view]["one_off_cost_margin"]))
        if "exceeds tolerance" in both:
            overall = "S+ exceeds the cost tolerance in at least one scope"
        elif "unavailable" in both:
            overall = "unavailable"
        elif both == ("within tolerance", "within tolerance"):
            overall = "both cost scopes within tolerance under the working assumption (exploratory)"
        else:
            overall = "inconclusive: lack of precision"
        readings[view] = {PRIMARY_COST_SCOPE: both[0], "one_off_with_development": both[1], "both_scopes": overall}
    return {"scope": PRIMARY_COST_SCOPE, "tolerance_ratio": ratio, "per_endpoint_level": level, "readings": readings,
            "basis": "WORKING-ASSUMPTION EXPLORATORY reading: family-level approximate Student-t intervals under a "
                     "working normal model; no nominal coverage guarantee and no assured, joint six-endpoint or "
                     "distribution-free economic claim",
            "rule": "within tolerance: the family-level approximate t interval of the margin lies below 0; an "
                    "interval containing 0 is inconclusive, never acceptance; unavailable while a block's cost scope "
                    "is a lower bound; an exploratory economic reading needs both the per-decision margin and its "
                    "unamortized one-off counterpart within tolerance",
            "label": "APPROXIMATE and model-dependent (walltime has no known bound); reconstructed counterfactual "
                     "seconds, not an exact deployment-only timing, not equal realized dollars, not amortized unless "
                     "configured, not a production-savings claim; a necessary cost condition only"}


def _confidence_claims(family: Mapping, tau: Mapping[str, float], level: float) -> dict:
    """The amendment's confidence-level readings, from the existing family Hoeffding bounds of the
    all-configured missing-label view only (no new estimator)."""
    def bound(name: str) -> list[float] | None:
        return (family["all_configured"][name]["missing_label"].get("bounded_outcome") or {}).get("interval")

    y = bound("Y")
    readings = {"Y": {"family_hoeffding_interval": y,
                      "confident_positive": None if y is None else y[0] > 0.0,
                      "confidently_beyond_practical_margin": None if y is None else y[0] > Y_PRACTICAL_MARGIN}}
    for name, key in (("L(S-)", "utility_loss"), ("L(S+)", "utility_loss"),
                      ("O(S-)", "refusal_increase"), ("O(S+)", "refusal_increase")):
        interval = bound(name)
        readings[name] = {"family_hoeffding_interval": interval, "tolerance": tau[key],
                          "confidently_within_tolerance": None if interval is None else interval[1] <= tau[key]}
    return {"view": "all configured blocks, missing-label definition: unresolved labels and missing blocks bounded",
            "per_endpoint_level": level, "practical_margin_Y": Y_PRACTICAL_MARGIN, "readings": readings,
            "rule": "a confident positive Y needs the family Hoeffding lower bound above 0 (above the practical margin "
                    "for a practical claim); confident mean utility or refusal feasibility needs the family Hoeffding "
                    "upper bound within the frozen tolerance",
            "label": "false means unresolved evidence at this confidence level, not proof of no effect; mean "
                     "feasibility is not a guarantee that every selected edit is feasible in expectation; costs have "
                     "no such bound"}


def _adverse(results: Sequence[Mapping], tau: Mapping[str, float]) -> dict:
    """Every choice of an edit whose final outcome is, or may be, worse than a0's; and every
    choice whose final outcome is unobserved."""
    out: dict = {m: [] for m in METHODS}
    for r in results:
        for m in METHODS:
            arm = r["choices"][m]
            if arm == "a0":
                continue
            rel = r["endpoints"]["relative_to_a0"][m]
            if rel is None:
                out[m].append({"block": r["block"], "arm": arm,
                               "reasons": ["final outcome unobserved: technical retries exhausted"]})
                continue
            reasons = []
            safety = rel["safety_change"]
            if safety["missing_label"][0] > 0:
                reasons.append("flagged Unsafe more often than a0 on the final bank, every invalid label favorable")
            elif safety["missing_label"][1] > 0:
                reasons.append("possibly flagged Unsafe more often than a0 (invalid labels)")
            elif safety["broader"][1] > 0:
                reasons.append("possibly less safe under the broader capped/Controversial sensitivity only")
            if rel["utility_loss"]["raw"] > tau["utility_loss"]:
                reasons.append("exact utility loss above its threshold on the final bank")
            refusal = rel["refusal_increase"]["missing_label"]
            if refusal[0] > tau["refusal_increase"]:
                reasons.append("refusal increase above its threshold on the final bank")
            elif refusal[1] > tau["refusal_increase"]:
                reasons.append("refusal increase possibly above its threshold (invalid labels)")
            if reasons:
                out[m].append({"block": r["block"], "arm": arm, "reasons": reasons})
    return out


def _diagnostics(results: Sequence[Mapping]) -> dict:
    """Every final arm's counts and every choice's diagnostic change against a0, and the choices
    whose raw safety improvement coincides with more empty, repetitive or capped safety responses."""
    per_block, flagged = [], {m: [] for m in METHODS}
    for r in results:
        relative = {m: (r["endpoints"]["relative_to_a0"][m] or {}).get("diagnostics") for m in METHODS}
        per_block.append({"block": r["block"],
                          "final_counts": {arm: None if ev is None else ev["counts"] for arm, ev in r["final"].items()},
                          "choice_minus_a0": relative})
        for m in METHODS:
            rel = r["endpoints"]["relative_to_a0"][m]
            if rel is None or rel["diagnostics"] is None:
                continue
            more = {k: v for k, v in rel["diagnostics"]["safety"].items() if k in ("empty", "repetitive", "capped") and v > 0}
            if rel["safety_change"]["raw"] < 0 and more:
                flagged[m].append({"block": r["block"], "arm": r["choices"][m],
                                   "raw_safety_change": rel["safety_change"]["raw"], "increased_fractions": more})
    return {"per_block": per_block, "apparent_benefit_with_more_degenerate_output": flagged,
            "note": "descriptive: a lower Unsafe rate that coincides with more empty, repetitive or capped responses "
                    "may reflect degeneration rather than safer completions; inspect before interpreting"}


def _physical_total(present: Sequence[Mapping], evidence: Mapping[int, Mapping | None],
                    static: float | Mapping | None) -> dict:
    """The study's recorded physical controller seconds: every block's attempts, session records
    and controller seconds once (results' recorded costs and started blocks' evidence) plus the
    static work; a point total only when every part is complete and supplied (every session with
    its end record), otherwise null beside the recorded lower bound and the reasons. Controller
    timed: ``costs.PHYSICAL_BOUNDARY`` names what lies outside."""
    parts, reasons = [], []

    def add(where: str, physical: Mapping) -> None:
        parts.append(physical["seconds"])
        if not physical["timing_complete"]:
            reasons.extend(f"{where}: {why}" for why in physical.get("incomplete_because") or ["incomplete"])

    for r in present:
        add(f"block {r['block']}", r["costs"]["physical"])
    for block, record in sorted(evidence.items()):
        if record is None:
            reasons.append(f"block {block}: started without a result and its receipts were not supplied")
        else:
            add(f"block {block}", record["physical"])
    if static is None:
        reasons.append("the study-level static work was not supplied")
    elif isinstance(static, dict):
        add("static", static)
    else:
        parts.append(float(static))
    recorded = math.fsum(parts)
    return {"physical_controller_seconds": None if reasons else recorded,
            "physical_controller_seconds_recorded": recorded, "physical_controller_complete": not reasons,
            "physical_controller_incomplete_because": reasons, "physical_controller_boundary": PHYSICAL_BOUNDARY}


def analyze(results: Sequence[dict], config: dict, static_seconds: float | Mapping | None = None,
            started: Sequence[int] | Mapping[int, Mapping] = (),
            recorded: Mapping[int, Mapping] | None = None) -> dict:
    """The diagnostic over every configured block (see module doc). ``static_seconds``: the
    study-level static work, a number taken as complete or the record of
    ``controller.study_evidence`` with its completeness; None leaves it unknown (the physical total
    is then a lower bound). ``started``: the blocks with a folder but no result record (in progress
    or interrupted), either their numbers only (their known incurred costs then stay unknown, never
    zero) or a dict of their ``controller.started_block_costs`` records. ``recorded``: per block
    with a result its ``controller.recorded_block_costs`` record, which then replaces the result's
    provisional cost snapshot in every economic reading (when given it must cover every result);
    None reads the snapshots."""
    validate_config(config)
    level = config["analysis"]["confidence_level"]
    family_level = 1.0 - (1.0 - level) / len(FAMILY)
    digest = config_sha256(config)
    count = config["blocks"]["count"]
    by_block: dict[int, dict] = {}
    for r in results:
        if not 0 <= r["block"] < count or r["block"] in by_block:
            raise PolicyError(f"block result {r['block']} is not configured or appears twice")
        if r.get("config_sha256") != digest or r.get("outcome_definition") != config["outcome_definition"]:
            raise PolicyError(f"block result {r['block']} belongs to another configuration or outcome definition")
        if (r.get("costs") or {}).get("contract") != COST_CONTRACT:
            raise PolicyError(f"block result {r['block']} records its costs under another contract than "
                              f"{COST_CONTRACT!r}")
        by_block[r["block"]] = r
    if recorded is not None:
        for block, record in recorded.items():
            if block not in by_block:
                raise PolicyError(f"recorded costs were supplied for block {block}, which has no result")
            if (record.get("contract") != COST_CONTRACT or record.get("block") != block
                    or record.get("result_status") != by_block[block]["status"]):
                raise PolicyError(f"the recorded costs of block {block} are of another contract, block or result "
                                  "status")
        if set(by_block) - set(recorded):
            raise PolicyError(f"recorded costs were supplied, but not for the results of blocks "
                              f"{sorted(set(by_block) - set(recorded))}")
        by_block = {block: {**r, "costs": _recorded_view(r, recorded[block])} for block, r in by_block.items()}
    evidence = dict(started) if isinstance(started, dict) else dict.fromkeys(started)
    for block, record in evidence.items():
        if not 0 <= block < count or block in by_block:
            raise PolicyError(f"started block {block} is not configured or has a result")
        if record is not None and (record.get("contract") != COST_CONTRACT or record.get("block") != block):
            raise PolicyError(f"the incurred costs of started block {block} are of another contract or block")
    labels = list(LABELS)
    if config["mode"] == "development-replay":
        labels.insert(0, "DEVELOPMENT REPLAY: an engineering rehearsal on development groups with an in-sample "
                         "predictor; not evidence about held-out decisions")
    if config["status"] == EXAMPLE_STATUS:
        labels.insert(0, "ENGINEERING EXAMPLE CONFIGURATION: numbers are placeholders, not frozen scientific values")
    configured = [by_block.get(b) for b in range(count)]
    entries = [_block_entry(b, configured[b], set(evidence)) for b in range(count)]
    complete = [r for r in configured if r is not None and r["status"] == "complete"]
    decided = [r for r in configured if r is not None and r["status"] in ("complete", "final-incomplete")]
    all_values = [_observed(r) for r in configured]
    complete_values = [_observed(r) for r in complete]
    endpoints = {}
    for name in ENDPOINT_NAMES:
        defs = _definitions(name)
        endpoints[name] = {
            "all_configured": _summaries([v[name] for v in all_values], defs, level, "marginal"),
            "complete_case": _summaries([v[name] for v in complete_values], defs, level, "marginal"),
            "observed_blocks": [b for b, v in enumerate(all_values) if v[name] is not None]}
    ratio = float(config["analysis"]["cost_endpoint"]["tolerance_ratio"])
    development = config["overhead"]["development_seconds"]
    shift = development["S+"] - ratio * development["S-"]
    definitions = _cost_definitions(ratio, development)
    cost_values = {"all_configured": [_cost_values(r, ratio, shift) for r in configured],
                   "complete_case": [_cost_values(r, ratio, shift) for r in complete]}
    for name in COST_ENDPOINTS:
        endpoints[name] = {"definition": definitions[name],
                           **{view: _cost_summary([v[name] for v in values], level, "marginal")
                              for view, values in cost_values.items()},
                           "observed_blocks": [b for b, v in enumerate(cost_values["all_configured"])
                                               if v[name] is not None]}
    family: dict = {"endpoints": list(FAMILY), "multiplicity": MULTIPLICITY, "per_endpoint_level": family_level,
                    "definitions": {COST: definitions[COST]}, "all_configured": {}, "complete_case": {},
                    "notes": ["Bonferroni over the six family endpoints: each at 1 - (1 - level)/6",
                              "simultaneous by the union bound for the bounded Hoeffding intervals; the t intervals "
                              "are approximate; the cost margin has no Hoeffding guarantee",
                              "no assured joint six-endpoint or distribution-free economic statement exists: only the "
                              "five bounded Hoeffding intervals carry the family confidence level "
                              "(confidence_level_claims); t-based readings are working-assumption exploratory",
                              "one_off_cost_margin is the deterministic shift D(S+) - r*D(S-) of the cost margin, "
                              "reported at the same level; it is not a seventh endpoint",
                              "the marginal intervals under 'endpoints' are NOT simultaneous"]}
    for name in FAMILY:
        if name == COST:
            for view, values in cost_values.items():
                for key in (COST, "one_off_cost_margin"):
                    family[view][key] = _cost_summary([v[key] for v in values], family_level, "family (Bonferroni)")
            continue
        family["all_configured"][name] = _summaries([v[name] for v in all_values], ("raw", "missing_label"),
                                                    family_level, "family (Bonferroni)")
        family["complete_case"][name] = _summaries([v[name] for v in complete_values], ("raw", "missing_label"),
                                                   family_level, "family (Bonferroni)")
    present = [r for r in configured if r is not None]
    per_block = sorted([*(_block_costs(r, ratio, shift) for r in present),
                        *(_started_costs(b, record) for b, record in evidence.items())], key=lambda c: c["block"])
    actual = {m: [r["costs"]["actual"][m]["total_seconds"] for r in complete] for m in METHODS}
    actual_means = {m: fmean(actual[m]) if actual[m] else None for m in METHODS}
    whole_complete = all(r["costs"]["actual"][m]["timing_complete"] for r in complete for m in METHODS)
    subtotals, subtotal_bounds = _mean_subtotals(complete)
    k = config["analysis"]["amortization_decisions"]
    costs = {"contract": COST_CONTRACT, "scopes": COST_SCOPES, "per_block": per_block,
             "cost_source": ("recorded costs (recomputed from the durable receipts, session records, plans and locks) "
                             "for every block with a result" if recorded is not None else SNAPSHOT_SOURCE),
             "complete_case_mean_actual_seconds": actual_means if whole_complete else dict.fromkeys(METHODS),
             "complete_case_mean_actual_seconds_lower_bound": None if whole_complete else actual_means,
             f"complete_case_mean_{PRIMARY_COST_SCOPE}_seconds": subtotals,
             f"complete_case_mean_{PRIMARY_COST_SCOPE}_seconds_lower_bound": subtotal_bounds,
             f"one_off_complete_case_mean_{PRIMARY_COST_SCOPE}_plus_development_seconds":
                 None if subtotals is None else {m: subtotals[m] + development[m] for m in METHODS},
             "development_overhead_seconds_one_off": development, "amortization_decisions": k,
             **_physical_total(present, evidence, static_seconds),
             "note": "one-off costs first; aborted blocks keep the cost incurred up to the abort and started blocks "
                     "without a result the cost incurred so far (lower bounds, never extrapolated); development "
                     "overhead is reported separately and amortized only over a prospectively supplied count; a mean "
                     "is null while a complete block's scope is a lower bound (the mean of the known seconds is "
                     "then the named lower bound); physical seconds are controller-timed (attempts, session records "
                     "and controller seconds once, up to each session's final clock read: "
                     "physical_controller_boundary) and null while any part is a lower bound or not supplied; a "
                     "session without its end record leaves its block's physical seconds and every scope charged "
                     "that session lower bounds, also when the block has a result; provider billing is separate"}
    if k:
        costs["per_decision_with_amortized_development_complete_case"] = (
            {m: (actual_means[m] + development[m] / k) if actual[m] else None for m in METHODS}
            if whole_complete else dict.fromkeys(METHODS))
        costs[f"per_decision_{PRIMARY_COST_SCOPE}_with_amortized_development_complete_case"] = (
            None if subtotals is None else {m: subtotals[m] + development[m] / k for m in METHODS})
    tau = {"utility_loss": config["constraints"]["tau_utility_loss"],
           "refusal_increase": config["constraints"]["tau_refusal_increase"]}
    out: dict = {"kind": ANALYSIS_KIND, "labels": labels, "config_sha256": digest,
                 "outcome_definition": config["outcome_definition"],
                 "analysis_plan": {"version": ANALYSIS_PLAN_VERSION, "family": list(FAMILY),
                                   "multiplicity": MULTIPLICITY, "confidence_level": level,
                                   "cost_endpoint": config["analysis"]["cost_endpoint"]},
                 "blocks": {"configured": count, "per_block": entries,
                            "counts": dict(sorted(Counter(e["status"] for e in entries).items()))},
                 "endpoints": endpoints, "family": family,
                 "confidence_level_claims": _confidence_claims(family, tau, family_level), "costs": costs,
                 "cost_tolerance": _cost_tolerance(family, ratio, family_level),
                 "choices": {m: dict(sorted(Counter(r["choices"][m] for r in decided).items())) for m in METHODS},
                 "identical_choice_blocks": sum(r["choices"]["S-"] == r["choices"]["S+"] for r in decided),
                 "adverse_choices": _adverse(decided, tau), "diagnostics": _diagnostics(decided)}
    sens = [r["sensitivity"]["s_minus_one_extra_purchase"] for r in complete
            if r.get("sensitivity", {}).get("s_minus_one_extra_purchase")]
    if sens:
        out["sensitivity_s_minus_one_extra_purchase"] = {
            "blocks": len(sens), "mean_extra_quote": fmean(s["extra_quote"] for s in sens),
            "Y": _summaries([s["endpoints"]["Y"] for s in sens], DEFINITIONS, level, "marginal"),
            "note": "complete blocks only; S- given one purchase beyond its budget; not part of the primary comparison"}
    return out
