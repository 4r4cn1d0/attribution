"""Development: the feature table from verified development runs, and the matched predictor
fit with group cross-fitting (H1 diagnostics). Development split, role and bank only.

**Index** (``INDEX_KIND``): explicit local paths of the supplied development runs, never
invented names: per development seed, the short- and full-checkpoint run folder of a0 and of
every development group, the attributes run of that seed, the exported selector view and the
relevance table with their expected hashes, and an optional read-only path map for dependency
chains recorded on another machine.

**Table** (``build_table``): every run verifies (own files, dependency chain, stream, pins and
summary cross-checks; ``outcomes.read_evaluation``); rows are (group, seed) with the X0
families, both attribution variants and the TARGETS: ``outcomes.adverse`` of the same-seed
full-checkpoint change (the upper missing-label endpoint of dF and O, the exact unique-argmax L).
Each row keeps both whole change records (raw, missing-label, broader and tie-aware endpoints,
missing and unresolved fractions, every diagnostic change); the table pins the outcome
definition. A missing run refuses: no complete-case subset is formed silently.

**Fit** (``fit_record``): for S- (X0) and each candidate S+ (X0 + one attribution variant),
per target, the frozen lambda grid under leave-one-group-out cross-fitting with group-equal
fold scores (``ridge``), the CV-selected lambda (smallest score, ties to the larger), nested
out-of-sample scores of that tuning, cross-fit predictions and squared errors, and final
models at every grid lambda on all development rows. The attribution proxy is selected by one
rule, the smallest normalized CV loss (sum over targets of the selected-lambda CV score divided
by the target's group-equal variance; a constant target is excluded and noted), and that
selection is itself evaluated by nested leave-one-group-out. The fixed decision diagnostic
(plug-in regret, violations, feasibility confusion, best-in-predicted-top-two) uses the honest
nested predictions. Several tables (short-checkpoint candidates) are fitted side by side; the
fidelity choice is a lead decision recorded in the frozen configuration. With few groups the
differences are descriptive (stated in the record's limits); nothing here is an H1 pass. The
record's ``outcome_diagnostics`` show, per group, the mean full-checkpoint raw, missing-label and
broader changes beside every diagnostic change (empty, repetitive, capped, label fractions,
output length, ties), so an apparent benefit explained by degenerate output is not hidden.
"""

from __future__ import annotations

import math
from pathlib import Path
from statistics import fmean
from typing import Mapping, Sequence

from experiments.safety_selection.config import config_sha256 as engine_config_sha256
from experiments.safety_selection.prepare import read_manifest
from experiments.safety_selection.selector_view import read_selector_view
from experiments.safety_selection.verify import PathMap

from . import ridge
from .common import PolicyError, canonical_json, engine_code_identity, finite, sha256_bytes
from .config import FOLDS, SPECIFIED_LAMBDA_GRID
from .features import (ATTRIBUTION_NAMES, CATALOGUE_SHA256, TARGETS, attribution_features, merge,
                       method_features, select, short_features, view_features)
from .outcomes import CHANGES, OUTCOME_PIN, adverse, paired_change, read_attribution, read_evaluation
from .policy import rank_edits
from .tfidf import read_relevance

__all__ = ["INDEX_KIND", "TABLE_KIND", "SPEC_KIND", "RECORD_KIND", "validate_index", "build_table",
           "table_from_parts", "validate_table", "validate_spec", "fit_record", "decision_diagnostic",
           "outcome_diagnostics"]

INDEX_KIND = "safety-decision-policy development index"
TABLE_KIND = "safety-decision-policy development table"
SPEC_KIND = "safety-decision-policy development fit spec"
RECORD_KIND = "safety-decision-policy development record"
SELECTION_RULE = ("attribution proxy: smallest sum over targets of (CV score at the CV-selected lambda) / "
                  "(group-equal target variance); constant targets excluded; ties to the candidate order")


def _exact(obj: object, keys: set[str], where: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != keys:
        raise PolicyError(f"{where}: expected exactly {sorted(keys)}")
    return obj


def validate_index(index: dict) -> dict:
    _exact(index, {"kind", "split", "short_checkpoint", "full_checkpoint", "selector_view", "relevance",
                   "seeds", "runs", "attribution", "path_map"}, "index")
    if index["kind"] != INDEX_KIND or index["split"] != "dev":
        raise PolicyError(f"index kind must be {INDEX_KIND!r} for the dev split")
    for key in ("selector_view", "relevance"):
        _exact(index[key], {"path", "sha256"}, f"index.{key}")
    seeds = index["seeds"]
    if not (isinstance(seeds, list) and seeds and len(set(seeds)) == len(seeds)
            and all(isinstance(s, int) and not isinstance(s, bool) for s in seeds)):
        raise PolicyError("index.seeds must be a non-empty list of distinct integers")
    _exact(index["runs"], {"short", "full"}, "index.runs")
    if not (isinstance(index["path_map"], list)
            and all(isinstance(p, list) and len(p) == 2 and all(isinstance(x, str) and x for x in p)
                    for p in index["path_map"])):
        raise PolicyError("index.path_map must be a list of [recorded prefix, local prefix] pairs")
    return index


def table_from_parts(*, split: str, short: str, full: str, static: Mapping[str, dict],
                     ties: Mapping[str, int], relevance: Mapping[str, dict], seeds: Sequence[int],
                     short_changes: Mapping[tuple[str, int], dict], full_changes: Mapping[tuple[str, int], dict],
                     attribution: Mapping[int, Mapping[str, dict]], attribution_sources: Mapping[int, dict],
                     inputs: dict) -> dict:
    """The table schema from verified parts (shared by the engine index and the synthetic world)."""
    groups = sorted(static)
    if set(relevance) != set(groups) or set(ties) != set(groups):
        raise PolicyError("view and relevance tables cover different groups")
    rows = []
    for seed in sorted(seeds):
        attr = attribution_features(attribution[seed])
        if set(attr) != set(groups):
            raise PolicyError(f"seed {seed}: attribution covers other groups than the view")
        for gid in groups:
            key = (gid, seed)
            if key not in short_changes or key not in full_changes:
                raise PolicyError(f"{gid} at seed {seed} lacks a paired short or full observation (refused; "
                                  "no complete-case subset)")
            sc, fc = short_changes[key], full_changes[key]
            rows.append({"group": gid, "seed": seed,
                         "features": merge(static[gid], relevance[gid], short_features(sc), attr[gid]),
                         "targets": adverse(fc), "full": _without_sources(fc), "short": _without_sources(sc),
                         "artifacts": {"short": sc["sources"], "full": fc["sources"],
                                       "attribution": attribution_sources[seed]}})
    return {"kind": TABLE_KIND, "split": split, "short_checkpoint": short, "full_checkpoint": full,
            "catalogue_sha256": CATALOGUE_SHA256, "outcome_definition": OUTCOME_PIN,
            "inputs": inputs, "groups": groups, "seeds": sorted(seeds),
            "tie_ranks": {g: ties[g] for g in groups}, "rows": rows}


def _without_sources(change: Mapping) -> dict:
    """A change record without its source paths (kept under the row's artifacts)."""
    return {k: v for k, v in change.items() if k != "sources"}


def build_table(index: dict, *, prepared_dir: str | Path, recipe: dict) -> dict:
    """The development feature table from a verified index (see module doc)."""
    validate_index(index)
    _, manifest_sha = read_manifest(prepared_dir)
    pins = {"manifest_sha256": manifest_sha, "recipe_sha256": engine_config_sha256(recipe),
            "code_sha256": engine_code_identity()["sha256"]}
    path_map = PathMap([tuple(p) for p in index["path_map"]])
    view = read_selector_view(index["selector_view"]["path"], index["selector_view"]["sha256"])
    if view.split != "dev":
        raise PolicyError("the development selector view must be of the dev split")
    static, ties = view_features(view)
    relevance, relevance_pins = read_relevance(index["relevance"]["path"], index["relevance"]["sha256"], "dev")
    groups = sorted(static)
    short, full = index["short_checkpoint"], index["full_checkpoint"]
    short_changes, full_changes, attribution, attribution_sources = {}, {}, {}, {}
    for seed in index["seeds"]:
        evals = {}
        for fidelity, checkpoint in (("short", short), ("full", full)):
            for arm in ["a0", *groups]:
                try:
                    path = index["runs"][fidelity][arm][str(seed)]
                except (KeyError, TypeError):
                    raise PolicyError(f"index lacks the {fidelity} run of {arm} at seed {seed}") from None
                evals[fidelity, arm] = read_evaluation(
                    path, expect={"split": "dev", "arm": arm, "seed": seed, "role": "development",
                                  "checkpoint": checkpoint, "bank": "dev", **pins},
                    prepared_dir=prepared_dir, path_map=path_map)
        for gid in groups:
            short_changes[gid, seed] = paired_change(evals["short", gid], evals["short", "a0"])
            full_changes[gid, seed] = paired_change(evals["full", gid], evals["full", "a0"])
        try:
            attr_path = index["attribution"][str(seed)]
        except (KeyError, TypeError):
            raise PolicyError(f"index lacks the attributes run of seed {seed}") from None
        scores, attr_sha = read_attribution(attr_path, expect={"split": "dev", "seed": seed, "role": "development",
                                                               "group_ids": groups, **pins},
                                            prepared_dir=prepared_dir, path_map=path_map)
        attribution[seed] = scores
        attribution_sources[seed] = {"run": str(attr_path), "complete_sha256": attr_sha}
    inputs = {"manifest_sha256": pins["manifest_sha256"], "recipe_sha256": pins["recipe_sha256"],
              "engine_code_sha256": pins["code_sha256"], "selector_view_sha256": view.sha256,
              "relevance_sha256": index["relevance"]["sha256"],
              "relevance_fingerprint_sha256": relevance_pins["fingerprint_sha256"],
              "index_sha256": sha256_bytes(canonical_json(index))}
    return table_from_parts(split="dev", short=short, full=full, static=static, ties=ties, relevance=relevance,
                            seeds=index["seeds"], short_changes=short_changes, full_changes=full_changes,
                            attribution=attribution, attribution_sources=attribution_sources, inputs=inputs)


def validate_table(table: dict) -> dict:
    _exact(table, {"kind", "split", "short_checkpoint", "full_checkpoint", "catalogue_sha256",
                   "outcome_definition", "inputs", "groups", "seeds", "tie_ranks", "rows"}, "table")
    if table["kind"] != TABLE_KIND or table["catalogue_sha256"] != CATALOGUE_SHA256:
        raise PolicyError("not a development table of this feature catalogue")
    if table["outcome_definition"] != OUTCOME_PIN:
        raise PolicyError("the table was built under another outcome definition")
    keys = [(r["group"], r["seed"]) for r in table["rows"]]
    if len(set(keys)) != len(keys) or set(keys) != {(g, s) for g in table["groups"] for s in table["seeds"]}:
        raise PolicyError("table rows must be exactly one per (group, seed)")
    for r in table["rows"]:
        _exact(r, {"group", "seed", "features", "targets", "full", "short", "artifacts"}, "table row")
        if set(r["targets"]) != set(TARGETS):
            raise PolicyError("table targets differ from the predicted outcomes")
        if r["targets"] != adverse(r["full"]):
            raise PolicyError(f"targets of {r['group']}@{r['seed']} are not the adverse endpoints of its full change")
        for t in TARGETS:
            finite(r["targets"][t], f"target {t} of {r['group']}@{r['seed']}")
    return table


def outcome_diagnostics(rows: Sequence[dict]) -> dict:
    """Per group, the means over seeds of the full-checkpoint change records: the raw,
    missing-label and broader endpoints (and tie-aware utility) beside every diagnostic change.
    Descriptive: an apparent safety benefit that coincides with more empty, repetitive or capped
    output stays visible; nothing here selects."""
    out = {}
    for g in sorted({r["group"] for r in rows}):
        changes = [r["full"] for r in rows if r["group"] == g]
        entry: dict = {"seeds": len(changes)}
        for key in CHANGES:
            entry[key] = {"raw": fmean(c[key]["raw"] for c in changes),
                          "missing_label": [fmean(c[key]["missing_label"][i] for c in changes) for i in (0, 1)],
                          "broader": [fmean(c[key]["broader"][i] for c in changes) for i in (0, 1)]}
            if "tie_aware" in changes[0][key]:
                entry[key]["tie_aware"] = fmean(c[key]["tie_aware"] for c in changes)
        entry["diagnostics"] = {kind: {name: fmean(c["diagnostics"][kind][name] for c in changes)
                                       for name in values} for kind, values in changes[0]["diagnostics"].items()}
        out[g] = entry
    return out


def validate_spec(spec: dict) -> dict:
    _exact(spec, {"kind", "name", "purpose", "x0", "attribution_candidates", "lambda_grid", "folds",
                  "diagnostic_constraints"}, "spec")
    if spec["kind"] != SPEC_KIND:
        raise PolicyError(f"spec kind must be {SPEC_KIND!r}")
    for key in ("name", "purpose"):
        if not isinstance(spec[key], str) or not spec[key].strip():
            raise PolicyError(f"spec.{key} must be a non-empty string")
    candidates = spec["attribution_candidates"]
    if not (isinstance(candidates, list) and candidates and len(set(candidates)) == len(candidates)
            and set(candidates) <= set(ATTRIBUTION_NAMES)):
        raise PolicyError(f"attribution_candidates must be distinct names from {ATTRIBUTION_NAMES}")
    for name in candidates:
        method_features(spec["x0"], name)
    if [float(v) for v in spec["lambda_grid"]] != SPECIFIED_LAMBDA_GRID:
        raise PolicyError(f"lambda_grid must be the frozen grid {SPECIFIED_LAMBDA_GRID}")
    if spec["folds"] != FOLDS:
        raise PolicyError(f"folds must be {FOLDS!r}")
    constraints = _exact(spec["diagnostic_constraints"], {"tau_utility_loss", "tau_refusal_increase",
                                                          "scale_utility_loss", "scale_refusal_increase"},
                         "diagnostic_constraints")
    for key, value in constraints.items():
        if finite(value, key) <= 0 and key.startswith("scale"):
            raise PolicyError(f"{key} must be positive")
    return spec


def _choose_plug_in(pred: Mapping[str, Mapping[str, float]], ties: Mapping[str, int],
                    constraints: Mapping[str, float]) -> str:
    feasible = [g for g, p in pred.items() if p["utility_loss"] <= constraints["tau_utility_loss"]
                and p["refusal_increase"] <= constraints["tau_refusal_increase"]]
    candidates = [("a0", 0.0, 0, -1)] + [(g, pred[g]["safety_change"], 1, ties[g]) for g in feasible]
    return min(candidates, key=lambda c: (c[1], c[2], c[3]))[0]


def decision_diagnostic(rows: Sequence[dict], predictions: Mapping[str, Sequence[float]],
                        ties: Mapping[str, int], constraints: Mapping[str, float]) -> dict:
    """The fixed decision-relevant diagnostic on the development menu: per development seed, the
    plug-in choice from that seed's predictions (smallest predicted safety change among
    predicted-feasible edits, a0 = 0) scored against the all-seed mean adverse outcomes; an
    infeasible choice scores as a0 and counts as a violation (FOCUS convention)."""
    tau_l, tau_o = constraints["tau_utility_loss"], constraints["tau_refusal_increase"]
    groups = sorted({r["group"] for r in rows})
    observed = {g: {t: fmean(r["targets"][t] for r in rows if r["group"] == g) for t in TARGETS} for g in groups}
    feasible = {g: observed[g]["utility_loss"] <= tau_l and observed[g]["refusal_increase"] <= tau_o for g in groups}
    best = min([("a0", 0.0, 0, -1)] + [(g, observed[g]["safety_change"], 1, ties[g]) for g in groups if feasible[g]],
               key=lambda c: (c[1], c[2], c[3]))
    per_seed = []
    for seed in sorted({r["seed"] for r in rows}):
        idx = [i for i, r in enumerate(rows) if r["seed"] == seed]
        pred = {rows[i]["group"]: {t: predictions[t][i] for t in TARGETS} for i in idx}
        choice = _choose_plug_in(pred, ties, constraints)
        violation = choice != "a0" and not feasible[choice]
        realized = 0.0 if choice == "a0" or violation else observed[choice]["safety_change"]
        ranking = [r["edit"] for r in rank_edits(pred, {g: ties[g] for g in pred}, constraints)]
        predicted_feasible = {g: pred[g]["utility_loss"] <= tau_l and pred[g]["refusal_increase"] <= tau_o
                              for g in pred}
        per_seed.append({"seed": seed, "plug_in_choice": choice, "violation": violation,
                         "realized_safety_change": realized, "regret": realized - best[1],
                         "observed_best_in_predicted_top_two": best[0] == "a0" or best[0] in ranking[:2],
                         "feasibility": {"true_feasible": sum(predicted_feasible[g] and feasible[g] for g in pred),
                                         "false_feasible": sum(predicted_feasible[g] and not feasible[g] for g in pred),
                                         "false_infeasible": sum(not predicted_feasible[g] and feasible[g] for g in pred),
                                         "true_infeasible": sum(not predicted_feasible[g] and not feasible[g]
                                                                for g in pred)}})
    return {"observed_best": best[0], "observed_best_safety_change": best[1],
            "observed_feasible": sorted(g for g in groups if feasible[g]), "per_seed": per_seed,
            "mean_regret": fmean(p["regret"] for p in per_seed),
            "violations": sum(p["violation"] for p in per_seed),
            "best_in_top_two": sum(p["observed_best_in_predicted_top_two"] for p in per_seed),
            "note": ("one development menu; per-seed results share its groups and are dependent; "
                     "observed outcomes are all-seed means, including the seed whose short run "
                     "produced the predictions; descriptive, not inferential")}


def _matrix(rows: Sequence[dict], names: Sequence[str]) -> list[list[float]]:
    return [select(r["features"], names, f"{r['group']}@{r['seed']}") for r in rows]


def _fit_method(rows: Sequence[dict], names: list[str], grid: Sequence[float], variances: dict) -> dict:
    groups = [r["group"] for r in rows]
    X = _matrix(rows, names)
    out = {"features": names, "targets": {}}
    for t in TARGETS:
        y = [r["targets"][t] for r in rows]
        tuned = ridge.tune(X, y, groups, grid, names)
        nest = ridge.nested(X, y, groups, grid, names)
        chosen = next(r for r in tuned["results"] if r["lambda"] == tuned["selected"])
        out["targets"][t] = {
            "cv": [{"lambda": r["lambda"], "score": r["score"], "per_group": r["per_group"]}
                   for r in tuned["results"]],
            "selected_lambda": tuned["selected"], "selected_score": tuned["selected_score"],
            "nested": {k: nest[k] for k in ("score", "selected_by_fold", "per_group")},
            "crossfit": [{"group": r["group"], "seed": r["seed"], "observed": y[i],
                          "prediction": chosen["predictions"][i],
                          "squared_error": (y[i] - chosen["predictions"][i]) ** 2,
                          "nested_prediction": nest["predictions"][i],
                          "nested_squared_error": (y[i] - nest["predictions"][i]) ** 2}
                         for i, r in enumerate(rows)],
            "target_variance": variances[t],
            "models": [{"lambda": float(lam), "model": ridge.fit(X, y, groups, lam, names).to_json()}
                       for lam in grid]}
    return out


def _normalized(scores: Mapping[str, float], variances: Mapping[str, float]) -> float:
    return math.fsum(scores[t] / variances[t] for t in TARGETS if variances[t] > 0)


def _nested_proxy(rows: Sequence[dict], x0: list[str], candidates: list[str], grid: Sequence[float]) -> dict:
    """Outer leave-one-group-out; inside, per candidate and target, lambda by inner folds, then the
    candidate by the selection rule on inner scores; the outer group is predicted with them."""
    groups = [r["group"] for r in rows]
    matrices = {a: _matrix(rows, [*x0, a]) for a in candidates}
    targets = {t: [r["targets"][t] for r in rows] for t in TARGETS}
    preds = {t: [0.0] * len(rows) for t in TARGETS}
    chosen = {}
    for held in sorted(set(groups)):
        train = [i for i, g in enumerate(groups) if g != held]
        tg = [groups[i] for i in train]
        variances = {t: ridge.weighted_variance([targets[t][i] for i in train], tg) for t in TARGETS}
        inner = {}
        for a in candidates:
            X = [matrices[a][i] for i in train]
            inner[a] = {t: ridge.tune(X, [targets[t][i] for i in train], tg, grid, [*x0, a]) for t in TARGETS}
        best = min(candidates, key=lambda a: (_normalized({t: inner[a][t]["selected_score"] for t in TARGETS},
                                                          variances), candidates.index(a)))
        chosen[held] = best
        for t in TARGETS:
            X = [matrices[best][i] for i in train]
            model = ridge.fit(X, [targets[t][i] for i in train], tg, inner[best][t]["selected"], [*x0, best])
            for i, g in enumerate(groups):
                if g == held:
                    preds[t][i] = model.predict(matrices[best][i])
    scores = {t: ridge.cv_score(targets[t], preds[t], groups) for t in TARGETS}
    return {"selected_by_fold": chosen, "score": {t: scores[t][0] for t in TARGETS},
            "per_group": {t: scores[t][1] for t in TARGETS}, "predictions": preds}


def _fold_comparison(a: dict, b: dict) -> dict:
    """Per target, group-level nested scores of a minus b (descriptive counts only)."""
    out = {}
    for t in TARGETS:
        diff = {g: a[t][g] - b[t][g] for g in a[t]}
        out[t] = {"groups": len(diff), "first_lower": sum(d < 0 for d in diff.values()),
                  "first_higher": sum(d > 0 for d in diff.values()), "mean_difference": fmean(diff.values()),
                  "per_group": diff}
    return out


def fit_record(tables: Sequence[tuple[dict, str]], spec: dict) -> dict:
    """The development record (see module doc). ``tables``: (table, its sha256) pairs."""
    validate_spec(spec)
    if not tables:
        raise PolicyError("fit_record needs at least one development table")
    for table, _ in tables:
        validate_table(table)
    first = tables[0][0]
    for table, _ in tables[1:]:
        for key in ("groups", "seeds", "full_checkpoint", "outcome_definition"):
            if table[key] != first[key]:
                raise PolicyError(f"development tables differ in {key}; fidelity candidates must share them")
        if table["inputs"]["relevance_fingerprint_sha256"] != first["inputs"]["relevance_fingerprint_sha256"]:
            raise PolicyError("development tables differ in their relevance fingerprint")
    grid = [float(v) for v in spec["lambda_grid"]]
    x0, candidates = list(spec["x0"]), list(spec["attribution_candidates"])
    constraints = spec["diagnostic_constraints"]
    entries = []
    for table, digest in tables:
        rows = table["rows"]
        groups = [r["group"] for r in rows]
        variances = {t: ridge.weighted_variance([r["targets"][t] for r in rows], groups) for t in TARGETS}
        fits = {"S-": _fit_method(rows, x0, grid, variances)}
        for a in candidates:
            fits[f"S+/{a}"] = _fit_method(rows, [*x0, a], grid, variances)
        normalized = {a: _normalized({t: fits[f"S+/{a}"]["targets"][t]["selected_score"] for t in TARGETS},
                                     variances) for a in candidates}
        selected = min(candidates, key=lambda a: (normalized[a], candidates.index(a)))
        proxy = _nested_proxy(rows, x0, candidates, grid)
        nested_preds = {key: {t: [c["nested_prediction"] for c in fit["targets"][t]["crossfit"]] for t in TARGETS}
                        for key, fit in fits.items()}
        diagnostics = {key: decision_diagnostic(rows, preds, table["tie_ranks"], constraints)
                       for key, preds in nested_preds.items()}
        diagnostics["S+/nested-proxy-selection"] = decision_diagnostic(rows, proxy["predictions"],
                                                                       table["tie_ranks"], constraints)
        group_scores = {key: {t: fit["targets"][t]["nested"]["per_group"] for t in TARGETS} for key, fit in fits.items()}
        entries.append({
            "table_sha256": digest, "short_checkpoint": table["short_checkpoint"],
            "full_checkpoint": table["full_checkpoint"], "groups": table["groups"], "seeds": table["seeds"],
            "outcome_definition": table["outcome_definition"], "outcome_diagnostics": outcome_diagnostics(rows),
            "x0": x0, "fits": fits, "target_variance": variances,
            "selection": {"attribution": selected, "normalized_cv_loss": normalized, "rule": SELECTION_RULE,
                          "constant_targets_excluded": [t for t in TARGETS if variances[t] <= 0]},
            "proxy_nested": {k: proxy[k] for k in ("selected_by_fold", "score", "per_group")},
            "decision_diagnostic": diagnostics,
            "nested_fold_comparison": {
                f"S+/{selected} minus S-": _fold_comparison(group_scores[f"S+/{selected}"], group_scores["S-"]),
                "S+/nested-proxy-selection minus S-": _fold_comparison(proxy["per_group"], group_scores["S-"])}})
    n_groups = len(first["groups"])
    return {"kind": RECORD_KIND, "spec": spec, "spec_sha256": sha256_bytes(canonical_json(spec)),
            "relevance_fingerprint_sha256": first["inputs"]["relevance_fingerprint_sha256"],
            "development_seeds": first["seeds"], "tables": entries,
            "limits": [f"{n_groups} development groups: cross-fitted differences between S+ and S- are "
                       "descriptive; with this few independent groups no inferential H1 claim is made",
                       "all seeds of a group share one fold; seeds are never independent groups",
                       "nested scores (honest) and selected-lambda CV scores (optimistic) are both reported",
                       "the decision diagnostic uses one development menu; per-seed results are dependent",
                       "fidelity across tables is a lead decision recorded in the frozen configuration",
                       "targets are the adverse missing-label endpoints of the guard's emitted-text flags and the "
                       "exact unique-argmax utility loss over finite prompt banks; prompts are not training "
                       "replication; the broader capped/Controversial/tie sensitivity and the diagnostics are "
                       "descriptive and never targets",
                       "selecting the proxy by normalized CV loss is an explicit heuristic; it does not imply "
                       "equally many features, equal capacity or a novel attribution or allocation method",
                       "matched ridge procedures do not imply equal model capacity: S+ has one more input"]}
