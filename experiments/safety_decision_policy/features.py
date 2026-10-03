"""The feature catalogue and the predictor-facing whitelist (stdlib only).

Every feature has an explicit name, units, provenance (the exact source field) and family; the
family names the artifact that buys it. A predictor or ranking receives only rows of
``{feature name: finite number}`` built here from:

- the engine's whitelisted selector view (``static`` and ``guard`` families), read with the
  engine's strict reader and expected hash;
- the frozen relevance table (``relevance``; per-group TF-IDF numbers only);
- a verified paired short-checkpoint evaluation of the edit and a0 at the same seed (``short``;
  under the outcome definition of ``outcomes``: the missing-label interval endpoints of dF and O,
  the exact unique-argmax utility loss, the query-NLL change, the invalid-label fractions and,
  optionally, the broader-sensitivity unresolved fractions);
- one attribution score per group from a verified attributes run (``attribution``; S+ only).

Never: ``Prepared``, the manifest, construction labels, ``data_id`` values, member rows or their
order, source line indices, tie ranks (an opaque tie-breaker, not a feature), full-fidelity or
hidden outcomes, or measured times. Unknown names refuse; a selected value that is missing or
null (for instance a label-score mean of a group with no scored row) refuses rather than being
imputed, and a missing safety label is never a favorable zero: the invalid-label fractions are
required features. This is an experimental information boundary, not filesystem security.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from experiments.safety_selection.config import ATTRIBUTION_VARIANTS

from .common import PolicyError, canonical_json, sha256_bytes
from .outcomes import CHANGES
from .tfidf import FEATURES as RELEVANCE_FEATURES

__all__ = ["FeatureSpec", "FAMILIES", "CATALOGUE", "CATALOGUE_SHA256", "ATTRIBUTION_NAMES",
           "X0_FAMILIES", "TARGETS", "REQUIRED_X0", "validate_names", "validate_x0_composition",
           "method_features", "view_features", "short_features", "attribution_features", "merge", "select"]

FAMILIES = {
    "static": "selector view: static metadata of the removed rows (export-selector-view)",
    "guard": "selector view: Qwen3Guard features of the removed training pairs (score-groups)",
    "relevance": "relevance table: frozen TF-IDF similarity of the removed rows to the query exemplars",
    "short": "paired short-checkpoint evaluations of the edit and a0 at the screen seed",
    "attribution": "attributes run on the screen-seed a0 trajectory at every attribution checkpoint",
}
X0_FAMILIES = ("static", "guard", "relevance", "short")
ATTRIBUTION_NAMES = tuple(ATTRIBUTION_VARIANTS)
TARGETS = CHANGES  # the predictors learn outcomes.adverse of the full-minus-a0 change


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    family: str
    units: str
    provenance: str

    def to_json(self) -> dict:
        return {"family": self.family, "units": self.units, "provenance": self.provenance,
                "artifact": FAMILIES[self.family]}


def _catalogue() -> dict[str, FeatureSpec]:
    specs = [FeatureSpec("edit_rows", "static", "rows", "static.size"),
             FeatureSpec("toxicchat_rows", "static", "rows", "static.provenance.ToxicChat"),
             FeatureSpec("ultrachat_rows", "static", "rows", "static.provenance.UltraChat"),
             FeatureSpec("toxicchat_fraction", "static", "fraction of edit rows",
                         "static.provenance.ToxicChat / static.size")]
    lengths = (("chars", "characters (prompt + response)"), ("response_chars", "characters (response)"),
               ("tokens", "policy tokens (prompt + response + end-of-turn)"),
               ("target_tokens", "policy target tokens (response + end-of-turn)"))
    for key, units in lengths:
        specs += [FeatureSpec(f"{key}_{stat}", "static", units, f"static.{key}.{stat}")
                  for stat in ("sum", "mean", "min", "max")]
    for label in ("unsafe", "controversial", "safe", "invalid"):
        specs += [FeatureSpec(f"guard_{label}_rows", "guard", "rows", f"guard.guard_{label}"),
                  FeatureSpec(f"guard_{label}_fraction", "guard", "fraction of edit rows",
                              f"guard.guard_{label} / guard.size")]
    for answer in ("yes", "no"):
        specs += [FeatureSpec(f"guard_refusal_{answer}_rows", "guard", "rows", f"guard.guard_refusal_{answer}"),
                  FeatureSpec(f"guard_refusal_{answer}_fraction", "guard", "fraction of edit rows",
                              f"guard.guard_refusal_{answer} / guard.size")]
    for label in ("safe", "unsafe", "controversial"):
        specs += [FeatureSpec(f"label_{label}_sum", "guard",
                              "summed normalized label-sequence score over scored rows (relative "
                              "likelihood, not a probability)", f"guard.label_scores.{label}.sum")]
        specs += [FeatureSpec(f"label_{label}_{stat}", "guard",
                              "normalized label-sequence score (relative likelihood, not a probability); "
                              "null when no row is scored", f"guard.label_scores.{label}.{stat}")
                  for stat in ("mean", "max")]
    specs += [FeatureSpec("label_unscored_rows", "guard", "rows", "guard.label_scores.unscored"),
              FeatureSpec("label_unscored_fraction", "guard", "fraction of edit rows",
                          "guard.label_scores.unscored / guard.size")]
    specs += [FeatureSpec(name, "relevance", "cosine similarity (L2-normalized tf-idf)",
                          f"relevance table: {name}") for name in RELEVANCE_FEATURES]
    short = (("safety_change", "fraction of safety prompts flagged Unsafe, edit minus a0 (invalid labels adverse)"),
             ("refusal_increase", "fraction of benign ARC generation prompts with Refusal=Yes, edit minus a0 "
                                  "(invalid labels adverse)"))
    for key, units in short:
        specs += [FeatureSpec(f"short_{key}_{end}", "short", units,
                              f"paired short evaluation: {key} missing-label interval {end} endpoint")
                  for end in ("lo", "hi")]
    specs.append(FeatureSpec("short_utility_loss", "short", "exact unique-argmax ARC accuracy, a0 minus edit",
                             "paired short evaluation: utility_loss raw (exact)"))
    specs.append(FeatureSpec("short_query_nll_change", "short",
                             "nats (mean per-query response NLL), edit minus a0",
                             "paired short evaluation: query_nll_change"))
    for key, units in (("safety", "fraction of safety prompts with an invalid guard label (missing)"),
                       ("refusal", "fraction of benign ARC generation prompts with an invalid guard label (missing)")):
        specs += [FeatureSpec(f"short_{key}_invalid_{arm}", "short", units,
                              f"paired short evaluation: missing_label_fraction.{key}_{arm}") for arm in ("edit", "a0")]
    for key, units in (("safety", "fraction of safety prompts invalid, capped or Controversial (broader, union)"),
                       ("refusal", "fraction of benign ARC generation prompts invalid or capped (broader, union)"),
                       ("utility", "fraction of forced-choice items tied with the answer (broader)")):
        specs += [FeatureSpec(f"short_{key}_broader_unresolved_{arm}", "short", units,
                              f"paired short evaluation: broader_unresolved_fraction.{key}_{arm}")
                  for arm in ("edit", "a0")]
    specs += [FeatureSpec("checkpoint_gradsim", "attribution", "cosine (mean over checkpoints and rows)",
                          "attributes run: scores.<group>.checkpoint_gradsim"),
              FeatureSpec("adam_diag_preconditioned_dot", "attribution",
                          "first-order query-loss change heuristic (nats), summed over rows and checkpoints",
                          "attributes run: scores.<group>.adam_diag_preconditioned_dot")]
    out = {spec.name: spec for spec in specs}
    if len(out) != len(specs):
        raise AssertionError("duplicate feature names")
    return out


CATALOGUE: dict[str, FeatureSpec] = _catalogue()
CATALOGUE_SHA256 = sha256_bytes(canonical_json({name: spec.to_json() for name, spec in CATALOGUE.items()}))


def validate_names(names: Sequence[str], *, attribution: bool) -> list[str]:
    """Distinct catalogue names; X0 families only, plus exactly one attribution feature last
    when ``attribution``."""
    names = list(names)
    if not names or len(set(names)) != len(names) or not all(isinstance(n, str) for n in names):
        raise PolicyError("feature names must be a non-empty list of distinct strings")
    unknown = [n for n in names if n not in CATALOGUE]
    if unknown:
        raise PolicyError(f"features outside the whitelisted catalogue (refused): {unknown}")
    families = [CATALOGUE[n].family for n in names]
    if attribution:
        if families[-1] != "attribution" or "attribution" in families[:-1]:
            raise PolicyError("an S+ feature list is the X0 list plus exactly one attribution feature, last")
    elif "attribution" in families:
        raise PolicyError("X0 never contains an attribution feature")
    return names


REQUIRED_X0 = (*RELEVANCE_FEATURES, "short_safety_change_lo", "short_safety_change_hi", "short_utility_loss",
               "short_refusal_increase_lo", "short_refusal_increase_hi", "short_query_nll_change",
               "short_safety_invalid_edit", "short_safety_invalid_a0", "short_refusal_invalid_edit",
               "short_refusal_invalid_a0")


def validate_x0_composition(x0: Sequence[str]) -> None:
    """X0 as specified: the six relevance features, the paired short observations of safety,
    utility, refusal and query NLL with explicit missing-label (invalid) rates, and at least one
    static, one guard hard-label and one label-sequence feature. Which further ones (for example
    the broader-sensitivity fractions) is a freeze decision."""
    missing = [n for n in REQUIRED_X0 if n not in x0]
    if missing:
        raise PolicyError(f"X0 lacks required features {missing}")
    if not any(CATALOGUE[n].family == "static" for n in x0):
        raise PolicyError("X0 needs at least one static metadata/length/provenance feature")
    if not any(n.startswith("guard_") for n in x0) or not any(n.startswith("label_") for n in x0):
        raise PolicyError("X0 needs guard hard-label features and normalized label-sequence features")


def method_features(x0: Sequence[str], attribution_name: str) -> dict[str, list[str]]:
    """The two compared feature lists: S- = X0; S+ = X0 + one attribution feature."""
    base = validate_names(x0, attribution=False)
    validate_x0_composition(base)
    return {"S-": list(base), "S+": validate_names([*base, attribution_name], attribution=True)}


def _ratio(count: int, size: int) -> float:
    return count / size


def view_features(view: Any) -> tuple[dict[str, dict[str, float | None]], dict[str, int]]:
    """Static and guard features per group of a read selector view, and its tie ranks."""
    features, ties = {}, {}
    for gid in view.menu[1:]:
        static, guard = view.groups[gid]["static"], view.groups[gid]["guard"]
        size = static["size"]
        row: dict[str, float | None] = {
            "edit_rows": float(size), "toxicchat_rows": float(static["provenance"]["ToxicChat"]),
            "ultrachat_rows": float(static["provenance"]["UltraChat"]),
            "toxicchat_fraction": _ratio(static["provenance"]["ToxicChat"], size)}
        for key in ("chars", "response_chars", "tokens", "target_tokens"):
            row.update({f"{key}_{stat}": float(static[key][stat]) for stat in ("sum", "mean", "min", "max")})
        for label in ("unsafe", "controversial", "safe", "invalid"):
            row[f"guard_{label}_rows"] = float(guard[f"guard_{label}"])
            row[f"guard_{label}_fraction"] = _ratio(guard[f"guard_{label}"], size)
        for answer in ("yes", "no"):
            row[f"guard_refusal_{answer}_rows"] = float(guard[f"guard_refusal_{answer}"])
            row[f"guard_refusal_{answer}_fraction"] = _ratio(guard[f"guard_refusal_{answer}"], size)
        scores = guard["label_scores"]
        for label in ("safe", "unsafe", "controversial"):
            for stat in ("sum", "mean", "max"):
                value = scores[label][stat]
                row[f"label_{label}_{stat}"] = None if value is None else float(value)
        row["label_unscored_rows"] = float(scores["unscored"])
        row["label_unscored_fraction"] = _ratio(scores["unscored"], size)
        features[gid], ties[gid] = row, int(static["tie_rank"])
    if sorted(ties.values()) != list(range(len(ties))):
        raise PolicyError("view tie ranks are not a permutation")
    return features, ties


def short_features(change: Mapping[str, Any]) -> dict[str, float]:
    """The short family from one paired short-checkpoint change (outcomes.paired_change)."""
    row = {}
    for key in ("safety_change", "refusal_increase"):
        row[f"short_{key}_lo"], row[f"short_{key}_hi"] = (float(v) for v in change[key]["missing_label"])
    row["short_utility_loss"] = float(change["utility_loss"]["raw"])
    row["short_query_nll_change"] = float(change["query_nll_change"])
    for key in ("safety", "refusal"):
        for arm in ("edit", "a0"):
            row[f"short_{key}_invalid_{arm}"] = float(change["missing_label_fraction"][f"{key}_{arm}"])
    for key in ("safety", "refusal", "utility"):
        for arm in ("edit", "a0"):
            row[f"short_{key}_broader_unresolved_{arm}"] = float(change["broader_unresolved_fraction"][f"{key}_{arm}"])
    return row


def attribution_features(scores: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]:
    """Both attribution variants per group from an attributes run's ``scores``."""
    out = {}
    for gid, values in scores.items():
        if set(values) != set(ATTRIBUTION_NAMES):
            raise PolicyError(f"attribution scores of {gid} must hold exactly {ATTRIBUTION_NAMES}")
        out[gid] = {name: float(values[name]) for name in ATTRIBUTION_NAMES}
    return out


def merge(*parts: Mapping[str, float | None]) -> dict[str, float | None]:
    """One group's family dicts merged; a name may come from one family only."""
    row: dict[str, float | None] = {}
    for part in parts:
        clash = set(row) & set(part)
        if clash:
            raise PolicyError(f"feature names supplied twice: {sorted(clash)}")
        unknown = [n for n in part if n not in CATALOGUE]
        if unknown:
            raise PolicyError(f"values outside the catalogue (refused): {unknown}")
        row.update(part)
    return row


def select(row: Mapping[str, float | None], names: Iterable[str], where: str) -> list[float]:
    """The selected values in order: each must exist, be non-null and finite (never imputed)."""
    out = []
    for name in names:
        if name not in CATALOGUE:
            raise PolicyError(f"{where}: {name!r} is outside the whitelisted catalogue (refused)")
        if name not in row or row[name] is None:
            raise PolicyError(f"{where}: feature {name!r} is unavailable; it is refused, never imputed")
        value = row[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise PolicyError(f"{where}: feature {name!r} is not a finite number")
        out.append(float(value))
    return out
