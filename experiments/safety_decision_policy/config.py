"""The runtime configuration, its cross-checks and its freeze (stdlib only).

Exact keys and no defaults: every scientific number is an explicit configuration value, and a
missing or unsupported one refuses. The configuration states the frozen rules verbatim
(outcomes, ranking, acquisition, choice; compared up to whitespace) so it describes itself; the
policy code pin covers every implementation (feature catalogue and TF-IDF definition included),
so a changed rule cannot run under an old file. Two definitions are pinned explicitly as well:
``outcome_definition`` (the version of ``outcomes.OUTCOME_DEFINITION``, checked on validation, and
its SHA-256, checked like the other pins by the cross-checks against the implemented definition,
which the development record must share; ``pins`` prints it) and the analysis plan
(``analysis.plan_version``, the six-endpoint ``family`` and its ``multiplicity``, and the
``cost_endpoint``: the cost scope of the economic reading, which must be the amendment's
selection-plus-one-chosen-model scope, and the explicit tolerance ratio r of the linear paired
margin ``C(S+) - r * C(S-)``). Two statuses exist:

- ``ENGINEERING EXAMPLE ONLY`` with ``freeze: false``: accepted for the fake-backend exercise and
  for a development replay; NEVER for confirmation (selector/reference roles, hidden bank).
- ``FROZEN FOR EXECUTION`` with ``freeze: true``: the lead's later immutable file with values
  from development calibration.

Cross-checks (``check_config``) bind a configuration to the actual engine and policy code, the
prepared manifest, the recipe, the development table and record, and the relevance
fingerprint; the record's own rule-based selections (lambda per method and target, attribution
proxy) must equal the configuration's, so both methods get the identical tuning procedure. The
seed plan must respect the engine's role namespaces: per block a disjoint selector progression
``start + k * stride`` (its whole length, not a pool) and a fresh final seed. The budget must
cover, for both methods, the fixed charges, the final reserve and the worst initial top-two
package. ``freeze`` writes the canonical configuration and a receipt as new files (never
replaced); the frozen hash pins everything downstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from experiments.safety_selection.config import INIT

from .common import (PolicyError, canonical_json, finite, sha256_bytes, utc_now, write_once,
                     write_once_json)
from .costs import OP_KINDS, PRIMARY_COST_SCOPE, Shape, feasibility, make_quoter
from .features import ATTRIBUTION_NAMES, TARGETS, method_features
from .outcomes import OUTCOME_CONVENTION, OUTCOME_PIN
from .policy import ACQUISITION_RULE, CHOICE_RULE, RANK_RULE

__all__ = ["CONFIG_KIND", "EXAMPLE_STATUS", "FROZEN_STATUS", "MODES", "SENSITIVITIES",
           "SPECIFIED_LAMBDA_GRID", "FOLDS", "CONVENTIONS", "METHODS", "MODE_ROLES",
           "ANALYSIS_PLAN_VERSION", "FAMILY", "MULTIPLICITY", "SeedProgression", "validate_config",
           "check_config", "check_feasibility", "require_confirmation_ready", "progression", "freeze",
           "config_sha256"]

CONFIG_KIND = "safety-decision-policy config"
EXAMPLE_STATUS = "ENGINEERING EXAMPLE ONLY"
FROZEN_STATUS = "FROZEN FOR EXECUTION"
MODES = ("confirmation", "development-replay")
SENSITIVITIES = ("s_minus_one_extra_purchase",)
SPECIFIED_LAMBDA_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]
FOLDS = "leave-one-group-out"
METHODS = ("S-", "S+")
# The analysis plan (analysis.py): all configured blocks with range-bounded missing outcomes beside
# the labelled complete-case view; marginal intervals; the six-endpoint family view (precision
# targets of 2 October 2026) Bonferroni-adjusted, whose cost endpoint is the linear paired margin
# T = C(S+) - r * C(S-) on the selection-plus-one-chosen-model scope (cost-scope amendment of
# 2 October 2026). v4 (3 October 2026) keeps the estimators and the allocation; it charges session
# overhead and controller seconds by ownership (costs.COST_CONTRACT), propagates each cost scope's
# completeness, keeps started blocks' incurred costs as lower bounds, and labels t-based readings as
# working-assumption exploratory with confidence-level claims from the family Hoeffding bounds only
# (inference-interpretation amendment). Changing it needs new code and a new version.
ANALYSIS_PLAN_VERSION = ("stage-B analysis plan v4 (3 October 2026): all-configured blocks, Bonferroni family, "
                         "cost margin on selection plus one chosen model with owned session overhead and per-scope "
                         "completeness; t readings exploratory, confidence claims from family Hoeffding bounds")
FAMILY = ("Y", "L(S-)", "L(S+)", "O(S-)", "O(S+)", "cost_margin")
MULTIPLICITY = "bonferroni"
CONVENTIONS = {"outcomes": OUTCOME_CONVENTION, "ranking": RANK_RULE, "acquisition": ACQUISITION_RULE,
               "choice": CHOICE_RULE}
# (split, engine role, bank) of selection and final operations, and the seed namespaces.
MODE_ROLES = {
    "confirmation": {"selection": ("heldout", "selector", "selector"),
                     "final": ("heldout", "reference", "hidden"),
                     "namespaces": ("selector", "reference")},
    "development-replay": {"selection": ("dev", "development", "dev"),
                           "final": ("dev", "development", "dev"),
                           "namespaces": ("development", "development")},
}
_KEYS = {
    "config": {"kind", "name", "purpose", "status", "freeze", "mode", "pins", "outcome_definition", "fidelity",
               "features", "predictor", "constraints", "conventions", "tariffs", "budget", "overhead", "retry",
               "blocks", "analysis"},
    "pins": {"engine_code_sha256", "policy_code_sha256", "manifest_sha256", "recipe_sha256",
             "development_table_sha256", "development_record_sha256", "relevance_fingerprint_sha256"},
    "outcome_definition": {"version", "sha256"},
    "fidelity": {"short", "full"},
    "features": {"x0", "attribution"},
    "predictor": {"lambda_grid", "folds", "development_groups", "selected_lambda"},
    "constraints": {"tau_utility_loss", "tau_refusal_increase", "scale_utility_loss",
                    "scale_refusal_increase"},
    "tariffs": {"unit", "cold_setup", "train_per_example", "evaluation", "call_overhead",
                "attribution_per_gradient_pass", "score_groups_per_row"},
    "evaluation": {"selection", "final"},
    "budget": {"total_quote_seconds"},
    "overhead": {"development_seconds"},
    "retry": {"max_attempts"},
    "blocks": {"count", "schedule_seed", "list"},
    "block": {"block", "selector_seed_start", "selector_seed_stride", "final_seed"},
    "analysis": {"plan_version", "confidence_level", "family", "multiplicity", "cost_endpoint",
                 "amortization_decisions", "sensitivity"},
    "cost_endpoint": {"scope", "tolerance_ratio"},
}


def config_sha256(config: dict) -> str:
    return sha256_bytes(canonical_json(config))


def _words(text: str) -> str:
    return " ".join(text.split())


def _keys(obj: object, name: str, where: str) -> dict:
    if not isinstance(obj, dict):
        raise PolicyError(f"{where}: expected an object")
    expected = _KEYS[name]
    if set(obj) != expected:
        raise PolicyError(f"{where}: missing {sorted(expected - set(obj))}, unknown {sorted(set(obj) - expected)}")
    return obj


def _int(value: object, where: str, low: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < low:
        raise PolicyError(f"{where}: expected an integer >= {low}")
    return value


def _nonneg(value: object, where: str, positive: bool = False) -> float:
    number = finite(value, where)
    if number < 0 or (positive and number == 0):
        raise PolicyError(f"{where}: expected a {'positive' if positive else 'non-negative'} number")
    return number


def _hex(value: object, where: str) -> str:
    if not (isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)):
        raise PolicyError(f"{where}: expected a 64-character lowercase hex digest")
    return value


def _text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyError(f"{where}: expected a non-empty string")
    return value


def validate_config(config: dict) -> dict:
    """Raise PolicyError unless ``config`` has exactly the supported schema and values."""
    _keys(config, "config", "config")
    if config["kind"] != CONFIG_KIND:
        raise PolicyError(f"kind must be {CONFIG_KIND!r}")
    _text(config["name"], "name")
    _text(config["purpose"], "purpose")
    if (config["status"], config["freeze"]) not in ((EXAMPLE_STATUS, False), (FROZEN_STATUS, True)):
        raise PolicyError(f"status/freeze must be ({EXAMPLE_STATUS!r}, false) or ({FROZEN_STATUS!r}, true)")
    if config["mode"] not in MODES:
        raise PolicyError(f"mode must be one of {MODES}")
    for key, value in _keys(config["pins"], "pins", "pins").items():
        _hex(value, f"pins.{key}")
    outcome = _keys(config["outcome_definition"], "outcome_definition", "outcome_definition")
    if outcome["version"] != OUTCOME_PIN["version"]:
        raise PolicyError(f"outcome_definition.version must be the implemented {OUTCOME_PIN['version']!r} (a "
                          "changed definition needs new code and a recorded amendment)")
    _hex(outcome["sha256"], "outcome_definition.sha256")
    fidelity = _keys(config["fidelity"], "fidelity", "fidelity")
    _text(fidelity["short"], "fidelity.short")
    _text(fidelity["full"], "fidelity.full")
    if INIT in (fidelity["short"], fidelity["full"]) or fidelity["short"] == fidelity["full"]:
        raise PolicyError("fidelity.short and fidelity.full must be two distinct trained checkpoints")
    features = _keys(config["features"], "features", "features")
    if features["attribution"] not in ATTRIBUTION_NAMES:
        raise PolicyError(f"features.attribution must be one of {ATTRIBUTION_NAMES}")
    method_features(features["x0"], features["attribution"])
    predictor = _keys(config["predictor"], "predictor", "predictor")
    if [float(v) for v in predictor["lambda_grid"]] != SPECIFIED_LAMBDA_GRID or not all(
            isinstance(v, (int, float)) and not isinstance(v, bool) for v in predictor["lambda_grid"]):
        raise PolicyError(f"predictor.lambda_grid must be the frozen grid {SPECIFIED_LAMBDA_GRID}")
    if predictor["folds"] != FOLDS:
        raise PolicyError(f"predictor.folds must be {FOLDS!r}")
    _int(predictor["development_groups"], "predictor.development_groups", 3)
    selected = predictor["selected_lambda"]
    if not (isinstance(selected, dict) and set(selected) == set(METHODS)):
        raise PolicyError(f"predictor.selected_lambda needs exactly {METHODS}")
    for method in METHODS:
        if not (isinstance(selected[method], dict) and set(selected[method]) == set(TARGETS)):
            raise PolicyError(f"predictor.selected_lambda.{method} needs exactly {TARGETS}")
        for target, lam in selected[method].items():
            if finite(lam, f"selected_lambda.{method}.{target}") not in SPECIFIED_LAMBDA_GRID:
                raise PolicyError(f"selected_lambda.{method}.{target} is not in the frozen grid")
    constraints = _keys(config["constraints"], "constraints", "constraints")
    for key in ("tau_utility_loss", "tau_refusal_increase"):
        finite(constraints[key], f"constraints.{key}")
    for key in ("scale_utility_loss", "scale_refusal_increase"):
        _nonneg(constraints[key], f"constraints.{key}", positive=True)
    conventions = config["conventions"]
    if not (isinstance(conventions, dict) and set(conventions) == set(CONVENTIONS)
            and all(isinstance(v, str) and _words(v) == _words(CONVENTIONS[k]) for k, v in conventions.items())):
        raise PolicyError("conventions differ from the implemented frozen rules (state them verbatim; a "
                          "changed rule needs new code and a recorded amendment)")
    tariffs = _keys(config["tariffs"], "tariffs", "tariffs")
    if tariffs["unit"] != "seconds":
        raise PolicyError("tariffs.unit must be 'seconds'")
    for key in ("cold_setup", "train_per_example", "attribution_per_gradient_pass", "score_groups_per_row"):
        _nonneg(tariffs[key], f"tariffs.{key}")
    for key, value in _keys(tariffs["evaluation"], "evaluation", "tariffs.evaluation").items():
        _nonneg(value, f"tariffs.evaluation.{key}", positive=True)
    overhead = tariffs["call_overhead"]
    if not (isinstance(overhead, dict) and set(overhead) == set(OP_KINDS)):
        raise PolicyError(f"tariffs.call_overhead needs exactly {OP_KINDS}")
    for key, value in overhead.items():
        _nonneg(value, f"tariffs.call_overhead.{key}", positive=True)
    _nonneg(_keys(config["budget"], "budget", "budget")["total_quote_seconds"], "budget.total_quote_seconds",
            positive=True)
    development = _keys(config["overhead"], "overhead", "overhead")["development_seconds"]
    if not (isinstance(development, dict) and set(development) == set(METHODS)):
        raise PolicyError(f"overhead.development_seconds needs exactly {METHODS}")
    for method in METHODS:
        _nonneg(development[method], f"overhead.development_seconds.{method}")
    _int(_keys(config["retry"], "retry", "retry")["max_attempts"], "retry.max_attempts", 1)
    blocks = _keys(config["blocks"], "blocks", "blocks")
    count = _int(blocks["count"], "blocks.count", 1)
    _int(blocks["schedule_seed"], "blocks.schedule_seed")
    if not isinstance(blocks["list"], list) or len(blocks["list"]) != count:
        raise PolicyError("blocks.list must hold exactly blocks.count entries")
    for i, entry in enumerate(blocks["list"]):
        _keys(entry, "block", f"blocks.list[{i}]")
        if entry["block"] != i:
            raise PolicyError("blocks.list entries must be numbered 0..count-1 in order")
        _int(entry["selector_seed_start"], f"blocks.list[{i}].selector_seed_start")
        _int(entry["selector_seed_stride"], f"blocks.list[{i}].selector_seed_stride", 1)
        _int(entry["final_seed"], f"blocks.list[{i}].final_seed")
    analysis = _keys(config["analysis"], "analysis", "analysis")
    if analysis["plan_version"] != ANALYSIS_PLAN_VERSION:
        raise PolicyError(f"analysis.plan_version must be the implemented plan {ANALYSIS_PLAN_VERSION!r}")
    if analysis["family"] != list(FAMILY) or analysis["multiplicity"] != MULTIPLICITY:
        raise PolicyError(f"analysis.family must be {list(FAMILY)} with multiplicity {MULTIPLICITY!r}")
    level = finite(analysis["confidence_level"], "analysis.confidence_level")
    if not 0 < level < 1:
        raise PolicyError("analysis.confidence_level must lie strictly between 0 and 1")
    cost = _keys(analysis["cost_endpoint"], "cost_endpoint", "analysis.cost_endpoint")
    if cost["scope"] != PRIMARY_COST_SCOPE:
        raise PolicyError(f"analysis.cost_endpoint.scope must be {PRIMARY_COST_SCOPE!r}, the cost-scope amendment's "
                          "economic scope (another scope needs new code and a new analysis plan version)")
    if finite(cost["tolerance_ratio"], "analysis.cost_endpoint.tolerance_ratio") < 1.0:
        raise PolicyError("analysis.cost_endpoint.tolerance_ratio must be at least 1: the margin C(S+) - ratio * "
                          "C(S-) <= 0 tolerates S+ costing up to ratio times S-")
    if analysis["amortization_decisions"] is not None:
        _int(analysis["amortization_decisions"], "analysis.amortization_decisions", 1)
    sens = analysis["sensitivity"]
    if not (isinstance(sens, list) and len(set(sens)) == len(sens) and set(sens) <= set(SENSITIVITIES)):
        raise PolicyError(f"analysis.sensitivity must be a list of distinct names from {SENSITIVITIES}")
    return config


@dataclass(frozen=True)
class SeedProgression:
    """A block's selector seeds ``start + k * stride`` up to the namespace end."""

    start: int
    stride: int
    last: int

    def at(self, k: int) -> int | None:
        seed = self.start + k * self.stride
        return seed if seed <= self.last else None

    @property
    def capacity(self) -> int:
        return 0 if self.start > self.last else (self.last - self.start) // self.stride + 1

    def seeds(self) -> range:
        return range(self.start, self.last + 1, self.stride)


def progression(config: dict, data_config: Mapping, block: int) -> SeedProgression:
    entry = config["blocks"]["list"][block]
    space = data_config["seed_namespaces"][MODE_ROLES[config["mode"]]["namespaces"][0]]
    return SeedProgression(entry["selector_seed_start"], entry["selector_seed_stride"], space[1])


def _record_entry(record: dict, table_sha256: str) -> dict:
    entries = [t for t in record["tables"] if t["table_sha256"] == table_sha256]
    if len(entries) != 1:
        raise PolicyError(f"the development record holds no fit of table {table_sha256}")
    return entries[0]


def check_config(config: dict, *, recipe: dict, data_config: Mapping, record: dict,
                 actual_pins: Mapping[str, str]) -> dict:
    """Cross-checks against the actual pins, recipe, data config and development record."""
    validate_config(config)
    wrong = {key: [config["pins"][key], actual_pins.get(key)] for key in sorted(_KEYS["pins"])
             if config["pins"][key] != actual_pins.get(key)}
    if wrong:
        raise PolicyError(f"pins differ from the actual identities (config, actual): {wrong}")
    if config["outcome_definition"] != OUTCOME_PIN:
        raise PolicyError(f"outcome_definition {config['outcome_definition']} differs from the implemented "
                          f"definition {OUTCOME_PIN}")
    names = [INIT] + [c["name"] for c in recipe["train"]["checkpoints"]]
    short, full = config["fidelity"]["short"], config["fidelity"]["full"]
    if short not in names or full not in names or names.index(short) >= names.index(full):
        raise PolicyError(f"fidelity: short must precede full among the recipe checkpoints {names[1:]}")
    entry = _record_entry(record, config["pins"]["development_table_sha256"])
    if (entry["short_checkpoint"], entry["full_checkpoint"]) != (short, full):
        raise PolicyError("the pinned development table was built at other checkpoints")
    if entry.get("outcome_definition") != config["outcome_definition"]:
        raise PolicyError("the development record was fitted under another outcome definition")
    if len(entry["groups"]) != config["predictor"]["development_groups"]:
        raise PolicyError("predictor.development_groups differs from the development record")
    if record["relevance_fingerprint_sha256"] != config["pins"]["relevance_fingerprint_sha256"]:
        raise PolicyError("the record's relevance fingerprint differs from the configuration pin")
    lists = method_features(config["features"]["x0"], config["features"]["attribution"])
    if entry["x0"] != lists["S-"]:
        raise PolicyError("the record's X0 feature list differs from features.x0")
    if entry["selection"]["attribution"] != config["features"]["attribution"]:
        raise PolicyError(f"features.attribution must be the record's development-selected proxy "
                          f"{entry['selection']['attribution']!r} (identical tuning rule for both methods)")
    for method in METHODS:
        key = "S-" if method == "S-" else f"S+/{config['features']['attribution']}"
        if entry["fits"][key]["features"] != lists[method]:
            raise PolicyError(f"the record's {key} feature list differs from the configuration")
        for target in TARGETS:
            chosen = entry["fits"][key]["targets"][target]["selected_lambda"]
            if float(config["predictor"]["selected_lambda"][method][target]) != chosen:
                raise PolicyError(f"selected_lambda.{method}.{target} must equal the record's CV-selected "
                                  f"{chosen} (identical tuning rule for both methods)")
    spaces = data_config["seed_namespaces"]
    selection_space, final_space = (spaces[n] for n in MODE_ROLES[config["mode"]]["namespaces"])
    used: dict[int, int] = {}
    finals = []
    for b in range(config["blocks"]["count"]):
        prog = progression(config, data_config, b)
        if not selection_space[0] <= prog.start <= selection_space[1]:
            raise PolicyError(f"block {b}: selector seeds must start in {selection_space}")
        if prog.capacity < 2:
            raise PolicyError(f"block {b}: the selector progression needs at least z0 and z1")
        for seed in prog.seeds():
            if seed in used:
                raise PolicyError(f"blocks {used[seed]} and {b} share selector seed {seed}")
            used[seed] = b
        final = config["blocks"]["list"][b]["final_seed"]
        if not final_space[0] <= final <= final_space[1]:
            raise PolicyError(f"block {b}: the final seed must lie in {final_space}")
        finals.append(final)
    if len(set(finals)) != len(finals) or set(finals) & set(used):
        raise PolicyError("final seeds must be distinct and disjoint from every selector seed")
    development = set(record["development_seeds"])
    if config["mode"] == "development-replay" and (development & (set(used) | set(finals))):
        raise PolicyError("a development replay must use seeds disjoint from the development record's")
    return {"selector_seed_capacity": {b: progression(config, data_config, b).capacity
                                       for b in range(config["blocks"]["count"])},
            "final_seeds": finals}


def check_feasibility(config: dict, shape: Shape) -> dict:
    """Refuse unless both methods can afford fixed charges, reserve and the worst top-two."""
    short, full = config["fidelity"]["short"], config["fidelity"]["full"]
    quote = make_quoter(config["tariffs"], shape, short, full)
    report = {m: feasibility(m, quote, shape, config["tariffs"], short, full,
                             config["budget"]["total_quote_seconds"]) for m in METHODS}
    bad = [m for m in METHODS if not report[m]["feasible"]]
    if bad:
        raise PolicyError(f"budget infeasible for {bad}: it must cover cold setup, static features, the "
                          f"whole screen, S+ prerequisites and attribution, the final reserve and the worst "
                          f"initial top-two package ({report})")
    return report


def require_confirmation_ready(config: dict) -> None:
    """Confirmation (selector/reference roles, hidden bank) only from a frozen configuration."""
    if config["mode"] == "confirmation" and (config["status"] != FROZEN_STATUS or config["freeze"] is not True):
        raise PolicyError(f"{EXAMPLE_STATUS} configurations are never accepted for confirmation")


def freeze(config: dict, out_dir: str | Path, *, recipe: dict, data_config: Mapping, record: dict,
           actual_pins: Mapping[str, str], shape: Shape) -> dict:
    """Validate, cross-check and write ``config.json`` (canonical) and ``freeze-receipt.json``
    into a NEW folder. An engineering example may be frozen only for a development replay."""
    require_confirmation_ready(config)
    checks = check_config(config, recipe=recipe, data_config=data_config, record=record,
                          actual_pins=actual_pins)
    feasible = check_feasibility(config, shape)
    out = Path(out_dir)
    if out.exists():
        raise FileExistsError(f"{out} exists; a frozen configuration folder is never replaced")
    digest = write_once(out / "config.json", canonical_json(config))
    receipt = {"kind": "safety-decision-policy freeze receipt", "config_sha256": digest,
               "status": config["status"], "mode": config["mode"], "pins": config["pins"],
               "outcome_definition": config["outcome_definition"],
               "analysis_plan_version": config["analysis"]["plan_version"],
               "checks": checks, "feasibility": feasible, "utc": utc_now(),
               "note": ("engineering example: development replay or fake backend only"
                        if config["status"] == EXAMPLE_STATUS else "frozen for execution")}
    write_once_json(out / "freeze-receipt.json", receipt)
    return receipt
