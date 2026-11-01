"""REQ-19: the $0 limit checks (over-refusal MDE and tau_L), with the W1-16 items (standard library only; Mac, $0).

    python -B scripts/stage1/limits/limits_check.py --out DIR [--data-root <checkout>/tmp] [--settings FILE]

**Inputs (the allow-list).** The settings file ``settings/limits_check.json`` (pinned by SHA-256 below) lists exactly
four sealed Gate A units: the untuned unit theta0 (arm a0, checkpoint init, seed 1101) and the a0 units of seeds
1101, 1102 and 1103 at checkpoint e1, each by its path under the data root and the SHA-256 of its COMPLETE.json,
job.json, eval/<ck>/summary.json and eval/<ck>/query_loss.jsonl. Any other unit, path, pin or recipe refuses
(limits_common.check_unit). Of each unit only labels and losses are read: guard.jsonl records of kind
"overrefusal" (fields prompt_id, valid, refusal), query_loss.jsonl (query_id, loss), and the numeric summary
fields. No answer, prompt or judge-output text is read, and no Gate B unit.

**O (over-refusal).** Per unit, O = the "Refusal: Yes" share of the greedy answers to the 100 dev over-refusal
prompts, in pp; an invalid judge answer counts as not refused (PREREG section 6 Ref). The count must equal the
unit's summary.json. "f" is the lead's written reading (a required settings field; an empty reading refuses):
f = 1 means all 100 dev over-refusal prompts, each with its greedy answer, with seeds as replicates. Only f = 1 is
defined, so another value refuses.

**The two O error models** (draft B sections A.3, A.8, E.2; W1-16 item 3), for an arm m with J seeds against theta0:

- prompts random: SE^2 = s^2/J + c * 10^4 / P. s = the sample SD (ddof 1) of the a0 seeds' O; c = max(0, MS_P -
  MS_E) / J_t, the prompt variance component from the two-way analysis of variance of the J_t x P table
  y(a0, j, p) - y(theta0, p) (J_t = 3 seeds, P = 100 prompts); it does not shrink with more seeds.
- seed only (the bank is fixed: "on these 100 prompts"): SE^2 = s^2/J.

MDE = (z(1 - alpha/2) + z(power)) * SE: two-sided alpha 5%, 80% power, normal planning approximation, at J = 6
(plan A) and 9 (plan B). The 6-against-6 comparator contrast is reported beside it (seed part 2 s^2/J; under prompts
random the theta0-against-a0 prompt part is used as a stand-in, report only), and so are t-based seed-only values
(df J - 1 against theta0, 2J - 2 for the comparator; report only).

**U8.** The settings key u8_decider names the error model fixed before this check runs (default prompts random).
U8 opens when that model's 6-seed MDE of O(m) - O(theta0) exceeds 5 pp (PLAN-S:197).

**NI planning report** (report only): P(declared feasible) for an arm at true excess 0 against theta0, at tau_O in
{2, 5, 10} pp, at 100 prompts and (if O-ext via N is considered) 500 prompts, under REQ-16's bound (the upper end of
the two-sided 90% interval: quantile 0.95), for both models, the decider's marked; and the smallest tau_O with 80%
NI power. At 500 prompts the prompt part scales by 100/500 (the same per-prompt churn assumed); the seed part stays.

**tau_L** (lead decisions L16): s_L = the sample SD (ddof 1), over seeds 1101-1103, of each a0 unit's mean
per-example query loss on all 200 task rows at e1 (math.fsum mean; it must equal summary.json's and COMPLETE.json's
mean exactly); tau_L = 2 * sqrt(2) * s_L; the SE of one seed-to-seed difference sqrt(2) * s_L and of a 6-against-6
contrast s_L * sqrt(1/3) are reported. A known-answer check against the settings' numbers (relative tolerance) must
pass, or nothing is written. The 2-df record (W1-16 item 8) is computed in closed form; beside it, the record copies
the recorded simulation's failure rates of null arms from the settings (report only; not recomputed here).

Writes into --out (absent or empty) one text-free file, limits_check.json (canonical JSON with provenance). Prints
numbers and hashes only. Exit 0: written; exit 2: refused, nothing written.
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.limits import limits_common as lc  # noqa: E402

SETTINGS_PATH = HERE.parent / "settings" / "limits_check.json"
SETTINGS_SHA256 = "03f1c2c4bfdb680523aa91e38969f6e5e82ad7daf05b385e292de2b18e518e26"
SETTINGS_NAME = "limits_check"
RECORD_KIND = "stage1 limits check"
UNIT_NAMES = ("untuned", "1101", "1102", "1103")
A0_NAMES = ("1101", "1102", "1103")
MODELS = ("prompts_random", "seed_only")
OUTPUT = "limits_check.json"
SIMULATED_BOUNDS = ("r1_2_bound_two_sided_90_upper", "one_sided_90_bound")
SIMULATED_RATES = ("at_s_half_sigma", "given_s_below_half_sigma", "unconditional")


# ----- the settings ----------------------------------------------------------------------------------------------


def _number(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise s1.Refusal(f"settings: {what} is not a finite number")
    return float(value)


def check_allow_list(units: Any) -> None:
    """Exactly theta0 (untuned, init, seed 1101) and the a0 units 1101-1103 at e1, each with its four pins."""
    if not isinstance(units, Mapping) or set(units) != set(UNIT_NAMES):
        raise s1.Refusal("settings: the allow-list must name exactly the units untuned, 1101, 1102 and 1103")
    for name in UNIT_NAMES:
        spec = units[name]
        want = ({"role": "theta0", "arm": "a0", "seed": 1101, "checkpoint": "init"} if name == "untuned"
                else {"role": "a0", "arm": "a0", "seed": int(name), "checkpoint": "e1"})
        if not isinstance(spec, Mapping) or any(spec.get(k) != v for k, v in want.items()):
            raise s1.Refusal(f"settings: allow-list entry {name} is not {want}")
        if not isinstance(spec.get("path"), str):
            raise s1.Refusal(f"settings: allow-list entry {name} has no path")
        for field in ("complete_sha256", "job_sha256", "summary_sha256", "query_loss_sha256"):
            lc.hex64(spec.get(field), f"settings: allow-list entry {name} {field}")


def check_f(f: Any) -> int:
    """The lead's written reading of PLAN-S:197's "f" must be given; only f = 1 is defined by it."""
    reading = f.get("reading") if isinstance(f, Mapping) else None
    if not isinstance(reading, str) or not reading.strip():
        raise s1.Refusal("settings: the written reading of f is empty (the lead's reading is required; do not guess)")
    if f.get("value") != 1 or isinstance(f.get("value"), bool):
        raise s1.Refusal("settings: only f = 1 is defined by the written reading")
    return 1


def check_content(doc: Mapping[str, Any]) -> None:
    """Every rule this script applies, checked before any unit is read."""
    check_allow_list(doc.get("units"))
    check_f(doc.get("f"))
    if doc.get("u8_decider") not in MODELS:
        raise s1.Refusal(f"settings: u8_decider must be one of {list(MODELS)}")
    mde = doc.get("mde") or {}
    if mde.get("sides") != 2:
        raise s1.Refusal("settings: the MDE is two-sided (sides = 2)")
    alpha, power = _number(mde.get("alpha"), "mde.alpha"), _number(mde.get("power"), "mde.power")
    if not (0 < alpha < 1 and 0.5 < power < 1):
        raise s1.Refusal("settings: mde.alpha or mde.power is out of range")
    seeds = mde.get("seeds") or {}
    if set(seeds) != {"plan_a", "plan_b"} or seeds["plan_a"] != 6 or not all(
            isinstance(v, int) and not isinstance(v, bool) and v >= 2 for v in seeds.values()):
        raise s1.Refusal("settings: mde.seeds must be plan_a = 6 and plan_b (integers >= 2)")
    o = doc.get("o") or {}
    if o.get("bank_kind") != "overrefusal" or o.get("bank_size") != 100:
        raise s1.Refusal("settings: the O bank is the 100 dev over-refusal prompts")
    _number(doc.get("o_ext_threshold_pp"), "o_ext_threshold_pp")
    ni = doc.get("ni_report") or {}
    q = _number(ni.get("screen_upper_quantile"), "ni_report.screen_upper_quantile")
    ni_power = _number(ni.get("power"), "ni_report.power")
    if not 0.5 < q < 1 or not 0.5 < ni_power < 1 or not ni.get("tau_o_pp") or not ni.get("prompts"):
        raise s1.Refusal("settings: the NI report needs a quantile and a power in (0.5, 1), a tau_O grid and prompt counts")
    for value in list(ni["tau_o_pp"]) + list(ni["prompts"]):
        if _number(value, "an NI grid value") <= 0:
            raise s1.Refusal("settings: the NI grid values must be positive")
    for key in ("gate_a_identity", "allow_list", "frozen_reader"):
        if not isinstance(doc.get(key), Mapping):
            raise s1.Refusal(f"settings: {key} is missing")
    lc.hex64(doc.get("query_bank_sha256"), "settings: query_bank_sha256")
    tau = doc.get("tau_l") or {}
    if tau.get("ddof") != 1 or tau.get("rows") != 200:
        raise s1.Refusal("settings: tau_L uses ddof 1 over the 200 task rows")
    known = tau.get("known_answer") or {}
    tol = _number(tau.get("relative_tolerance"), "tau_l.relative_tolerance")
    s_known = _number(known.get("s"), "tau_l.known_answer.s")
    expected = tau_l_numbers_from_s(s_known)
    for key in ("tau_l", "se_one_difference", "se_6v6"):
        if not math.isclose(_number(known.get(key), f"tau_l.known_answer.{key}"), expected[key], rel_tol=tol, abs_tol=0.0):
            raise s1.Refusal(f"settings: the known answer's {key} does not follow from its s by the L16 rule")
    simulated = tau.get("two_df_simulated")
    if not isinstance(simulated, Mapping) or not isinstance(simulated.get("source"), str):
        raise s1.Refusal("settings: tau_l.two_df_simulated names no source")
    for bound in SIMULATED_BOUNDS:
        rates = simulated.get(bound)
        if not isinstance(rates, Mapping) or set(rates) != set(SIMULATED_RATES) or not all(
                0 <= _number(rates[k], f"tau_l.two_df_simulated.{bound}.{k}") <= 100 for k in SIMULATED_RATES):
            raise s1.Refusal(f"settings: tau_l.two_df_simulated.{bound} is not the three rates in percent")


# ----- O: labels, the planning table and the two error models ----------------------------------------------------


def o_flags(guard_bytes: bytes, unit: str, bank_kind: str) -> dict[str, tuple[bool, bool]]:
    """prompt id -> (refused, valid) from guard.jsonl's records of the bank's kind (fields prompt_id, valid,
    refusal only). Refused = valid is true and refusal is "Yes"; an invalid answer counts as not refused."""
    out: dict[str, tuple[bool, bool]] = {}
    for record in lc.fields_of(guard_bytes, f"{unit} guard.jsonl", ("prompt_id", "valid", "refusal"), {bank_kind}):
        pid, valid, refusal = record["prompt_id"], record["valid"], record["refusal"]
        if not isinstance(pid, str) or pid in out:
            raise s1.Refusal(f"unit {unit}: the over-refusal prompt ids are not distinct strings")
        if not isinstance(valid, bool) or refusal not in ("Yes", "No", None):
            raise s1.Refusal(f"unit {unit}: an over-refusal judge record has no boolean valid or no Yes/No refusal")
        out[pid] = (valid is True and refusal == "Yes", valid)
    return out


def two_way(table: Sequence[Sequence[int]]) -> dict[str, Fraction | int]:
    """Two-way analysis of variance without replication of a J x P table (rows seeds, columns prompts), exact."""
    J = len(table)
    P = len(table[0]) if J else 0
    if J < 2 or P < 2 or any(len(row) != P for row in table) or any(
            isinstance(v, bool) or not isinstance(v, int) for row in table for v in row):
        raise s1.Refusal("the planning table is not a J x P table of integers with J, P >= 2")
    grand = Fraction(sum(map(sum, table)), J * P)
    row_means = [Fraction(sum(row), P) for row in table]
    col_means = [Fraction(sum(table[j][p] for j in range(J)), J) for p in range(P)]
    ss_p = J * sum((c - grand) ** 2 for c in col_means)
    ss_j = P * sum((r - grand) ** 2 for r in row_means)
    ss_t = sum((Fraction(table[j][p]) - grand) ** 2 for j in range(J) for p in range(P))
    ss_e = ss_t - ss_p - ss_j
    df_p, df_e = P - 1, (P - 1) * (J - 1)
    ms_p, ms_e = ss_p / df_p, ss_e / df_e
    component = max(Fraction(0), ms_p - ms_e) / J
    return {"seeds": J, "prompts": P, "grand_mean": grand, "ms_prompts": ms_p, "ms_error": ms_e,
            "df_prompts": df_p, "df_error": df_e, "prompt_component": component}


def contrast_se_pp(model: str, seeds: int, seed_variance_pp2: float, prompt_component: float, prompts: int,
                   comparator: bool = False) -> float:
    """The SE (pp) of O(m) - O(theta0) (comparator: of a J-against-J contrast) for J = seeds under one model.
    seed_variance_pp2: s^2 in pp^2; prompt_component: c in share^2 units; prompts: P of the planned bank."""
    v_seed = (2.0 if comparator else 1.0) * seed_variance_pp2 / seeds
    v_prompt = prompt_component * 1e4 / prompts
    if model == "prompts_random":
        return math.sqrt(v_seed + v_prompt)
    if model == "seed_only":
        return math.sqrt(v_seed)
    raise s1.Refusal(f"unknown O error model {model!r}")


def mde_pp(se: float, alpha: float, power: float) -> float:
    """The two-sided MDE (pp) at level alpha and the given power: (z(1 - alpha/2) + z(power)) * SE."""
    return (lc.z(1 - alpha / 2) + lc.z(power)) * se


def mde_t_pp(se: float, alpha: float, power: float, df: int) -> float:
    """The same with Student t quantiles at df (report only)."""
    return (lc.t_quantile(1 - alpha / 2, df) + lc.t_quantile(power, df)) * se


def ni_planning(se: float, taus: Sequence[float], quantile: float, power: float) -> dict:
    """For an arm at true excess 0: P(upper bound <= tau) = Phi(tau/SE - z(q)) per tau, and the smallest tau with the
    given NI power, (z(q) + z(power)) * SE."""
    zq = lc.z(quantile)
    return {"se_pp": se, "p_declared_feasible": {f"{t:g}": lc.NORMAL.cdf(t / se - zq) for t in taus},
            "smallest_tau_o_pp_with_power": (zq + lc.z(power)) * se}


def per_seed_paired(theta0: Sequence[bool], seed_flags: Sequence[bool]) -> dict:
    """Report only (CK-3 section 4.2's form): discordant counts and the paired per-prompt SE (pp) of one a0 seed
    against theta0, 100 * sqrt((b + c)/n^2 - (b - c)^2/n^3)."""
    n = len(theta0)
    b = sum(t and not a for t, a in zip(theta0, seed_flags))
    c = sum(a and not t for t, a in zip(theta0, seed_flags))
    variance = Fraction(b + c, n ** 2) - Fraction((b - c) ** 2, n ** 3)          # exact, never below 0
    return {"theta0_only": b, "seed_only": c, "both": sum(t and a for t, a in zip(theta0, seed_flags)),
            "discordant": b + c, "paired_se_pp": 100 * math.sqrt(float(variance))}


def o_block(flags: Mapping[str, Mapping[str, tuple[bool, bool]]], settings: Mapping[str, Any]) -> dict:
    """Every O number of REQ-19 and W1-16 from the units' per-prompt flags (names: untuned and the a0 seeds)."""
    bank = settings["o"]["bank_size"]
    planned = check_f(settings["f"]) * bank
    ids = sorted(flags["untuned"])
    if len(ids) != planned or any(sorted(flags[n]) != ids for n in A0_NAMES):
        raise s1.Refusal(f"the units do not hold the same {planned} over-refusal prompt ids (f = 1: all of the bank)")
    theta0 = [flags["untuned"][p][0] for p in ids]
    seeds = {n: [flags[n][p][0] for p in ids] for n in A0_NAMES}
    o_pp = {n: Fraction(100 * sum(v), bank) for n, v in seeds.items()}
    seed_variance = statistics.variance(list(o_pp.values()))               # ddof 1, exact (pp^2)
    table = [[int(a) - int(t) for a, t in zip(seeds[n], theta0)] for n in A0_NAMES]
    anova = two_way(table)
    component = float(anova["prompt_component"])
    mde = settings["mde"]
    alpha, power = mde["alpha"], mde["power"]
    models: dict[str, dict] = {}
    for model in MODELS:
        block: dict[str, Any] = {"vs_theta0": {}, "comparator_j_vs_j": {}}
        for plan, J in sorted(mde["seeds"].items()):
            se = contrast_se_pp(model, J, float(seed_variance), component, planned)
            se_c = contrast_se_pp(model, J, float(seed_variance), component, planned, comparator=True)
            block["vs_theta0"][plan] = {"seeds": J, "se_pp": se, "mde_pp": mde_pp(se, alpha, power)}
            block["comparator_j_vs_j"][plan] = {"seeds": J, "se_pp": se_c, "mde_pp": mde_pp(se_c, alpha, power)}
            if model == "seed_only":
                block["vs_theta0"][plan]["mde_t_pp"] = mde_t_pp(se, alpha, power, J - 1)
                block["vs_theta0"][plan]["t_df"] = J - 1
                block["comparator_j_vs_j"][plan]["mde_t_pp"] = mde_t_pp(se_c, alpha, power, 2 * J - 2)
                block["comparator_j_vs_j"][plan]["t_df"] = 2 * J - 2
        models[model] = block
    decider = settings["u8_decider"]
    decisive = models[decider]["vs_theta0"]["plan_a"]["mde_pp"]
    threshold = float(settings["o_ext_threshold_pp"])
    ni = settings["ni_report"]
    ni_models = {}
    for model in MODELS:
        ni_models[model] = {str(P): ni_planning(contrast_se_pp(model, mde["seeds"]["plan_a"], float(seed_variance),
                                                               component, P), ni["tau_o_pp"],
                                                ni["screen_upper_quantile"], ni["power"]) for P in ni["prompts"]}
    return {
        "bank": {"kind": settings["o"]["bank_kind"], "prompts": bank, "f": 1, "planning_prompts": planned,
                 "f_reading": settings["f"]["reading"]},
        "o_pp": {"untuned": float(Fraction(100 * sum(theta0), bank)), **{n: float(v) for n, v in o_pp.items()}},
        "a0_seed_sd_pp": math.sqrt(float(seed_variance)), "a0_seed_variance_pp2": float(seed_variance),
        "a0_seed_df": len(A0_NAMES) - 1,
        "planning_table": {"rows": "a0 seeds 1101-1103", "columns": "the dev over-refusal prompts",
                           "cell": "y(a0, j, p) - y(theta0, p), y = the refused flag",
                           "seeds": anova["seeds"], "prompts": anova["prompts"],
                           "grand_mean_pp": 100 * float(anova["grand_mean"]),
                           "ms_prompts": float(anova["ms_prompts"]), "ms_error": float(anova["ms_error"]),
                           "df_prompts": anova["df_prompts"], "df_error": anova["df_error"],
                           "prompt_component_share2": component,
                           "prompt_part_se_pp": math.sqrt(component * 1e4 / planned)},
        "per_seed_paired_report_only": {n: per_seed_paired(theta0, seeds[n]) for n in A0_NAMES},
        "mde_convention": {"alpha": alpha, "sides": "two-sided", "power": power,
                           "quantiles": "normal (planning approximation); the t values are report only",
                           "z_alpha": lc.z(1 - alpha / 2), "z_power": lc.z(power)},
        "error_models": models,
        "u8": {"decider": decider, "decisive": "the plan-A (6-seed) MDE of O(m) - O(theta0) under the decider",
               "decisive_mde_pp": decisive, "threshold_pp": threshold, "opens": decisive > threshold,
               "other_model_mde_pp": {m: models[m]["vs_theta0"]["plan_a"]["mde_pp"] for m in MODELS}},
        "ni_planning_report_only": {"bound": "the upper end of the two-sided 90% interval (REQ-16's screen)",
                                    "sides": "one-sided", "alpha_one_sided": 1 - ni["screen_upper_quantile"],
                                    "quantile": ni["screen_upper_quantile"], "z": lc.z(ni["screen_upper_quantile"]),
                                    "power": ni["power"], "seeds": mde["seeds"]["plan_a"], "decider": decider,
                                    "true_excess_pp": 0, "by_model": ni_models,
                                    "scaling": "more prompts scale the prompt part by 100/P; the seed part stays"}}


# ----- tau_L ------------------------------------------------------------------------------------------------------


def tau_l_numbers_from_s(s: float) -> dict[str, float]:
    """L16: tau_L = 2 * sqrt(2) * s; the SE of one seed-to-seed difference and of a 6-against-6 contrast."""
    return {"tau_l": 2 * math.sqrt(2) * s, "se_one_difference": math.sqrt(2) * s, "se_6v6": s * math.sqrt(1 / 3)}


def tau_l_block(means: Mapping[str, float]) -> dict:
    """s_L (ddof 1) over the a0 seeds' mean query losses, and the L16 numbers."""
    values = [means[n] for n in A0_NAMES]
    s = statistics.stdev(values)
    return {"a0_mean_query_loss": {n: means[n] for n in A0_NAMES}, "mean_of_means": statistics.fmean(values),
            "s": s, "ddof": 1, **tau_l_numbers_from_s(s)}


def known_answer(block: Mapping[str, float], known: Mapping[str, float], tol: float) -> dict:
    """The computed numbers against the settings' known answer; a mismatch refuses (numbers only)."""
    out = {}
    for key in ("s", "tau_l", "se_one_difference", "se_6v6"):
        if not math.isclose(block[key], known[key], rel_tol=tol, abs_tol=0.0):
            raise s1.Refusal(f"the tau_L known-answer check fails at {key} ({block[key]!r} against {known[key]!r})")
        out[key] = {"known": known[key], "bit_equal": block[key] == known[key]}
    return {"pass": True, "relative_tolerance": tol, "values": out}


def two_df_record(df: int, simulated: Mapping[str, Any]) -> dict:
    """W1-16 item 8 in closed form (df = 2 only: (df) s^2 / sigma^2 is chi-square with 2 df, an exponential), with
    the recorded simulation's failure rates from the settings beside it (report only)."""
    if df != 2:
        raise s1.Refusal("the 2-df record is defined for three a0 seeds only")

    def chi2_2_quantile(p: float) -> float:
        return -2.0 * math.log(1.0 - p)

    return {"df": df, "sigma_over_s_95pct": [math.sqrt(df / chi2_2_quantile(0.975)), math.sqrt(df / chi2_2_quantile(0.025))],
            "p_s_below_half_sigma": 1.0 - math.exp(-df * 0.25 / 2.0), "p_s_below_sigma": 1.0 - math.exp(-df / 2.0),
            "tau_l_over_se_6v6_if_sigma_equals_s": (2 * math.sqrt(2)) / math.sqrt(1 / 3),
            "simulated_failure_rates_report_only": dict(simulated)}


# ----- reading the units ------------------------------------------------------------------------------------------


def read_units(settings: Mapping[str, Any], data_root: Path) -> tuple[dict, dict, dict, dict]:
    """(per-unit record, O flags per unit, mean query loss per unit, input hashes), from the allow-listed units only."""
    reader = lc.frozen_reader(settings["frozen_reader"])
    allow = settings["allow_list"]
    rules = {"path_pattern": allow["path_pattern"], "require_pins": True, "identity": settings["gate_a_identity"],
             "refused_recipes": allow["refused_recipes"]}
    inputs = {f"frozen/{k}": v["sha256"] for k, v in sorted(settings["frozen_reader"].items())}
    records, flags, means, query_ids, banks = {}, {}, {}, {}, set()
    for name in UNIT_NAMES:
        spec = settings["units"][name]
        unit = lc.check_unit(data_root, name, spec, rules, reader)
        summary_bytes, summary_sha = lc.unit_file(unit, "summary.json", spec["summary_sha256"], required=True)
        loss_bytes, loss_sha = lc.unit_file(unit, "query_loss.jsonl", spec["query_loss_sha256"], required=True)
        guard_bytes, guard_sha = lc.unit_file(unit, "guard.jsonl")
        prefix = f"{name}/{unit.eval_prefix}"
        inputs.update({f"{name}/COMPLETE.json": unit.complete_sha256, f"{name}/job.json": unit.job_sha256,
                       f"{prefix}/summary.json": summary_sha, f"{prefix}/query_loss.jsonl": loss_sha,
                       f"{prefix}/guard.jsonl": guard_sha})
        summary = s1.strict_json(summary_bytes)
        losses = {}
        for record in lc.fields_of(loss_bytes, f"{name} query_loss.jsonl", ("query_id", "loss")):
            qid, loss = record["query_id"], record["loss"]
            if not isinstance(qid, str) or qid in losses or isinstance(loss, bool) or not isinstance(loss, (int, float)):
                raise s1.Refusal(f"unit {name}: query_loss.jsonl holds a repeated id or a loss that is not a number")
            losses[qid] = float(loss)
        rows = settings["tau_l"]["rows"]
        if len(losses) != rows:
            raise s1.Refusal(f"unit {name}: query_loss.jsonl holds {len(losses)} rows, not {rows}")
        mean = math.fsum(losses.values()) / len(losses)
        ql = summary.get("query_loss") or {}
        recorded = ((unit.complete.get("evaluation") or {}).get("query_loss") or {}).get("mean")
        if ql.get("mean") != mean or recorded != mean or ql.get("n") != rows:
            raise s1.Refusal(f"unit {name}: the recomputed mean query loss differs from summary.json or COMPLETE.json")
        banks.add(ql.get("query_bank_sha256"))
        query_ids[name] = sorted(losses)
        flags[name] = o_flags(guard_bytes, name, settings["o"]["bank_kind"])
        over = summary.get("overrefusal") or {}
        refused = sum(f for f, _ in flags[name].values())
        if over.get("n") != len(flags[name]) or over.get("refusals") != refused:
            raise s1.Refusal(f"unit {name}: the over-refusal labels disagree with summary.json's counts")
        means[name] = mean
        records[name] = {"role": spec["role"], "seed": spec["seed"], "checkpoint": spec["checkpoint"],
                         "path": spec["path"], "complete_sha256": unit.complete_sha256, "job_sha256": unit.job_sha256,
                         "o_refusals": refused, "o_invalid": sum(not v for _, v in flags[name].values()),
                         "o_prompts": len(flags[name]), "query_rows": len(losses), "mean_query_loss": mean}
    if banks != {settings["query_bank_sha256"]}:
        raise s1.Refusal("the units do not all name the pinned query bank")
    if any(query_ids[n] != query_ids["untuned"] for n in UNIT_NAMES):
        raise s1.Refusal("the units do not hold the same task rows")
    return records, flags, means, inputs


def run(settings: Mapping[str, Any], settings_sha256: str, data_root: Path) -> bytes:
    """The text-free record's bytes (canonical JSON)."""
    check_content(settings)
    records, flags, means, inputs = read_units(settings, data_root)
    o = o_block(flags, settings)
    tau = settings["tau_l"]
    block = tau_l_block(means)
    check = known_answer(block, tau["known_answer"], tau["relative_tolerance"])
    doc = {"kind": RECORD_KIND, "version": 1, "requirement": settings["requirement"], "units": records, "o": o,
           "tau_l": {**block, "rule": tau["rule"], "scope": tau["scope"], "known_answer_check": check,
                     "untuned_mean_query_loss_report_only": means["untuned"],
                     "two_df_record": two_df_record(len(A0_NAMES) - 1, tau["two_df_simulated"])},
           "provenance": s1.provenance(Path(__file__), settings_sha256, inputs, {})}
    return canonical_json(doc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="output folder (absent or empty)")
    parser.add_argument("--data-root", type=Path, default=lc.DEFAULT_DATA_ROOT,
                        help="the folder the allow-list paths are relative to (default <checkout>/tmp)")
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        data = run(settings, digest, args.data_root)
        written = s1.write_new_files(args.out.resolve(), {OUTPUT: data})
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    doc = s1.strict_json(data)
    u8 = doc["o"]["u8"]
    print(f"wrote {OUTPUT} into {args.out} ({written[OUTPUT]})")
    print(f"  O MDE, 6 seeds, against theta0: prompts random {u8['other_model_mde_pp']['prompts_random']:.3f} pp; "
          f"seed only {u8['other_model_mde_pp']['seed_only']:.3f} pp; decider {u8['decider']}; U8 opens: {u8['opens']}")
    print(f"  tau_L {doc['tau_l']['tau_l']!r} nats (s {doc['tau_l']['s']!r}); known answer: pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
