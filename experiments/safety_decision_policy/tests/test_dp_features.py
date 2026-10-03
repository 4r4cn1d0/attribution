"""The predictor-facing whitelist: every catalogue feature documented; forbidden names (tie ranks,
ids, construction labels, targets, full or hidden outcomes, measured times) refused; X0 holds
the specified components and never attribution; S+ adds exactly one attribution feature;
unavailable values refuse rather than being imputed; predictor-side modules import no engine
data access. An experimental information boundary, not filesystem security."""

from __future__ import annotations

import ast
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.safety_decision_policy import features as ft
from experiments.safety_decision_policy.common import PolicyError
from experiments.safety_decision_policy.outcomes import paired_change
from experiments.safety_decision_policy.synthetic import make_world

PACKAGE = Path(ft.__file__).resolve().parent


def test_every_catalogue_feature_has_a_family_units_provenance_and_artifact():
    assert len(ft.CATALOGUE) == len(set(ft.CATALOGUE))
    for name, spec in ft.CATALOGUE.items():
        described = spec.to_json()
        assert spec.name == name and spec.family in ft.FAMILIES
        assert all(isinstance(described[k], str) and described[k] for k in ("units", "provenance", "artifact"))
    assert set(ft.ATTRIBUTION_NAMES) == {n for n, s in ft.CATALOGUE.items() if s.family == "attribution"}


@pytest.mark.parametrize("name", ["tie_rank", "group_id", "construction_index", "data_id", "type",
                                  "safety_change", "utility_loss", "full_safety_change_hi",
                                  "hidden_unsafe_rate", "short_seconds", "row_order"])
def test_names_outside_the_catalogue_are_refused_everywhere(name, example_config):
    x0 = example_config["features"]["x0"]
    with pytest.raises(PolicyError):
        ft.validate_names([*x0, name], attribution=False)
    with pytest.raises(PolicyError):
        ft.select({name: 1.0}, [name], "row")
    with pytest.raises(PolicyError):
        ft.merge({name: 1.0})


def test_x0_has_the_specified_components_and_s_plus_adds_exactly_one_attribution_feature(example_config):
    x0 = example_config["features"]["x0"]
    lists = ft.method_features(x0, "checkpoint_gradsim")
    assert lists["S-"] == x0 and lists["S+"] == [*x0, "checkpoint_gradsim"]
    with pytest.raises(PolicyError):
        ft.method_features([*x0, "adam_diag_preconditioned_dot"], "checkpoint_gradsim")
    for required in ("tfidf_pair_max", "short_query_nll_change", "short_safety_invalid_a0", "short_utility_loss",
                     "short_refusal_increase_hi"):
        with pytest.raises(PolicyError):
            ft.method_features([n for n in x0 if n != required], "checkpoint_gradsim")
    with pytest.raises(PolicyError):
        ft.method_features([n for n in x0 if not n.startswith("label_")], "checkpoint_gradsim")
    with pytest.raises(PolicyError):
        ft.validate_names([*x0, "checkpoint_gradsim", "adam_diag_preconditioned_dot"], attribution=True)


def test_unavailable_or_non_finite_values_are_refused_never_imputed():
    row = {"label_unsafe_mean": None, "edit_rows": 8.0, "tokens_mean": math.inf}
    with pytest.raises(PolicyError):
        ft.select(row, ["label_unsafe_mean"], "g-1")
    with pytest.raises(PolicyError):
        ft.select(row, ["tokens_mean"], "g-1")
    with pytest.raises(PolicyError):
        ft.select(row, ["guard_unsafe_rows"], "g-1")
    assert ft.select(row, ["edit_rows"], "g-1") == [8.0]
    with pytest.raises(PolicyError):
        ft.merge({"edit_rows": 1.0}, {"edit_rows": 2.0})


def test_view_features_follow_the_selector_view_and_keep_tie_ranks_out_of_the_features():
    view = make_world().view("dev")
    values, ties = ft.view_features(SimpleNamespace(menu=view["menu"], groups=view["groups"]))
    gid = view["menu"][1]
    static, guard = view["groups"][gid]["static"], view["groups"][gid]["guard"]
    assert values[gid]["edit_rows"] == static["size"]
    assert values[gid]["toxicchat_fraction"] == static["provenance"]["ToxicChat"] / static["size"]
    assert values[gid]["guard_unsafe_rows"] == guard["guard_unsafe"]
    assert values[gid]["label_unsafe_mean"] == guard["label_scores"]["unsafe"]["mean"]
    assert ties[gid] == static["tie_rank"] and all("tie_rank" not in v for v in values.values())
    assert sorted(ties.values()) == list(range(len(ties)))


def test_short_and_attribution_families_come_from_their_artifacts_only():
    change = {"safety_change": {"raw": 0.05, "missing_label": [-0.1, 0.2], "broader": [-0.3, 0.4]},
              "utility_loss": {"raw": 0.03, "missing_label": [0.03, 0.03], "broader": [0.0, 0.03], "tie_aware": 0.02},
              "refusal_increase": {"raw": 0.0, "missing_label": [-0.05, 0.05], "broader": [-0.1, 0.1]},
              "query_nll_change": -0.3,
              "missing_label_fraction": {f"{k}_{a}": 0.1 for k in ("safety", "refusal") for a in ("edit", "a0")},
              "broader_unresolved_fraction": {f"{k}_{a}": 0.2 for k in ("safety", "refusal", "utility")
                                              for a in ("edit", "a0")}}
    short = ft.short_features(change)
    assert short["short_safety_change_hi"] == 0.2 and short["short_query_nll_change"] == -0.3
    assert short["short_utility_loss"] == 0.03 and short["short_safety_invalid_edit"] == 0.1   # exact; missing labels
    assert short["short_utility_broader_unresolved_a0"] == 0.2
    assert "short_utility_loss_hi" not in ft.CATALOGUE and "short_safety_unresolved_a0" not in ft.CATALOGUE
    assert {ft.CATALOGUE[n].family for n in short} == {"short"}
    world = make_world()
    a0 = world._eval_obj("dev", "development", "a0", 1101, "q", "dev")
    edit = world._eval_obj("dev", "development", world.edits("dev")[0], 1101, "q", "dev")
    produced = ft.short_features(paired_change(edit, a0))
    assert set(produced) == {n for n, s in ft.CATALOGUE.items() if s.family == "short"}
    assert all(math.isfinite(v) for v in produced.values())
    with pytest.raises(PolicyError):
        ft.attribution_features({"g-1": {"checkpoint_gradsim": 0.1}})


def _imports(module: str) -> set[str]:
    tree = ast.parse((PACKAGE / f"{module}.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
            names.update(f"{node.module}.{a.name}" for a in node.names)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
    return names


@pytest.mark.parametrize("module", ["features", "ridge", "policy"])
def test_predictor_side_modules_import_no_engine_data_access(module):
    imported = _imports(module)
    forbidden = ("experiments.safety_selection.prepare", "experiments.safety_selection.runner",
                 "experiments.safety_selection.loaders", "load_prepared", "read_manifest", "Prepared")
    assert not [name for name in imported if any(bad in name for bad in forbidden)]
