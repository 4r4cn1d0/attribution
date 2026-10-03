"""Configuration validation, cross-checks and freeze: the ENGINEERING EXAMPLE validates but is
never accepted for confirmation; exact keys and supported values; the frozen rules stated
verbatim; the outcome definition and analysis plan pinned by version and hash, with the cost
endpoint's scope and tolerance ratio explicit; pins,
record-selected lambdas and proxy, block seeds in the engine's role namespaces and disjoint; the
budget covers the worst initial top two for both methods; freezing writes new immutable files
only."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from experiments.safety_decision_policy import config as cf
from experiments.safety_decision_policy.common import PolicyError, read_canonical, read_json_strict, sha256_file
from experiments.safety_decision_policy.outcomes import OUTCOME_PIN
from experiments.safety_decision_policy.synthetic import (SYNTHETIC_DATA_CONFIG, SYNTHETIC_RECIPE, make_world,
                                                          prepare_synthetic)


def test_the_engineering_example_validates_but_is_never_accepted_for_confirmation(example_config):
    cf.validate_config(example_config)
    assert example_config["status"] == cf.EXAMPLE_STATUS and example_config["freeze"] is False
    with pytest.raises(PolicyError):
        cf.require_confirmation_ready(example_config)
    frozen = {**example_config, "status": cf.FROZEN_STATUS, "freeze": True}
    cf.require_confirmation_ready(frozen)
    for status, flag in ((cf.FROZEN_STATUS, False), (cf.EXAMPLE_STATUS, True)):
        with pytest.raises(PolicyError):
            cf.validate_config({**example_config, "status": status, "freeze": flag})


def _mutations():
    def setter(path, value):
        def apply(config):
            node = config
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value
        return apply

    def deleter(path):
        def apply(config):
            node = config
            for key in path[:-1]:
                node = node[key]
            del node[path[-1]]
        return apply

    return {
        "missing pin": deleter(["pins", "manifest_sha256"]),
        "unknown key": setter(["defaults"], {}),
        "bad pin": setter(["pins", "recipe_sha256"], "xyz"),
        "grid changed": setter(["predictor", "lambda_grid"], [0.1, 1, 10]),
        "folds changed": setter(["predictor", "folds"], "k-fold"),
        "lambda off grid": setter(["predictor", "selected_lambda", "S+", "utility_loss"], 3.0),
        "scale zero": setter(["constraints", "scale_utility_loss"], 0),
        "tau missing": deleter(["constraints", "tau_refusal_increase"]),
        "overhead kind missing": deleter(["tariffs", "call_overhead", "extend"]),
        "zero call overhead": setter(["tariffs", "call_overhead", "screen"], 0),
        "negative tariff": setter(["tariffs", "train_per_example"], -1),
        "unit": setter(["tariffs", "unit"], "dollars"),
        "budget zero": setter(["budget", "total_quote_seconds"], 0),
        "retry zero": setter(["retry", "max_attempts"], 0),
        "block count": setter(["blocks", "count"], 3),
        "block numbering": setter(["blocks", "list", 1, "block"], 5),
        "stride zero": setter(["blocks", "list", 0, "selector_seed_stride"], 0),
        "confidence one": setter(["analysis", "confidence_level"], 1.0),
        "unknown sensitivity": setter(["analysis", "sensitivity"], ["best_case"]),
        "same fidelity": setter(["fidelity", "full"], "q"),
        "init fidelity": setter(["fidelity", "short"], "init"),
        "attribution unknown": setter(["features", "attribution"], "influence"),
        "forbidden x0": setter(["features", "x0"], ["tie_rank"]),
        "mode unknown": setter(["mode"], "exploratory"),
        "development overhead missing": setter(["overhead", "development_seconds"], {"S-": 0}),
        "outcome definition missing": deleter(["outcome_definition"]),
        "first-draft outcome version": setter(["outcome_definition", "version"], "stage-B outcomes v1"),
        "outcome hash malformed": setter(["outcome_definition", "sha256"], "xyz"),
        "analysis plan version": setter(["analysis", "plan_version"], "complete-case only"),
        "plan v2 before the cost-scope amendment": setter(
            ["analysis", "plan_version"], "stage-B analysis plan v2 (2 October 2026): all-configured blocks, Bonferroni family"),
        "plan v3 before session ownership and the interpretation amendment": setter(
            ["analysis", "plan_version"], "stage-B analysis plan v3 (2 October 2026): all-configured blocks, Bonferroni "
                                          "family, cost margin on selection plus one chosen model"),
        "family shrunk": setter(["analysis", "family"], ["Y"]),
        "family with the raw total cost difference": setter(
            ["analysis", "family"], ["Y", "L(S-)", "L(S+)", "O(S-)", "O(S+)", "actual_cost_difference"]),
        "multiplicity unadjusted": setter(["analysis", "multiplicity"], "none"),
        "cost endpoint missing": deleter(["analysis", "cost_endpoint"]),
        "cost scope with the reference run": setter(["analysis", "cost_endpoint", "scope"], "research_total"),
        "cost tolerance missing": deleter(["analysis", "cost_endpoint", "tolerance_ratio"]),
        "cost tolerance below one": setter(["analysis", "cost_endpoint", "tolerance_ratio"], 0.9),
        "cost tolerance not a number": setter(["analysis", "cost_endpoint", "tolerance_ratio"], "10%"),
        "old utility convention": setter(["conventions", "outcomes"], "U = forced-choice accuracy; ties in [0,1]"),
    }


@pytest.mark.parametrize("name", sorted(_mutations()))
def test_missing_unknown_or_unsupported_values_refuse(name, example_config):
    broken = copy.deepcopy(example_config)
    _mutations()[name](broken)
    with pytest.raises(PolicyError):
        cf.validate_config(broken)


def test_conventions_must_state_the_implemented_rules(example_config):
    spaced = copy.deepcopy(example_config)
    spaced["conventions"]["choice"] = "  " + spaced["conventions"]["choice"].replace("; ", ";\n   ")
    cf.validate_config(spaced)
    changed = copy.deepcopy(example_config)
    changed["conventions"]["choice"] = changed["conventions"]["choice"].replace(">= 2", ">= 1")
    with pytest.raises(PolicyError):
        cf.validate_config(changed)


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    pytest.importorskip("numpy")
    configs = Path(cf.__file__).resolve().parent / "configs"
    world = make_world()
    template = read_json_strict(configs / "example-engineering.json")
    spec = read_json_strict(configs / "example-dev-fit-spec.json")
    return world, prepare_synthetic(tmp_path_factory.mktemp("synthetic"), world, template=template, spec=spec)


def _check(config, setup, pins=None):
    return cf.check_config(config, recipe=SYNTHETIC_RECIPE, data_config=SYNTHETIC_DATA_CONFIG,
                           record=setup["record"], actual_pins=pins or setup["pins"])


def test_cross_checks_bind_pins_record_selections_and_the_seed_plan(synthetic):
    world, setup = synthetic
    config = copy.deepcopy(setup["config"])
    report = _check(config, setup)
    assert report["selector_seed_capacity"] == {0: 3450, 1: 3449}
    with pytest.raises(PolicyError):
        _check(config, setup, {**setup["pins"], "policy_code_sha256": "1" * 64})
    entry = setup["record"]["tables"][0]
    other_lambda = next(v for v in cf.SPECIFIED_LAMBDA_GRID
                        if v != entry["fits"]["S-"]["targets"]["safety_change"]["selected_lambda"])
    variants = {
        "lambda not the record's": lambda c: c["predictor"]["selected_lambda"]["S-"].update(safety_change=other_lambda),
        "proxy not the record's": lambda c: c["features"].update(
            attribution=next(a for a in ("checkpoint_gradsim", "adam_diag_preconditioned_dot")
                             if a != entry["selection"]["attribution"])),
        "groups": lambda c: c["predictor"].update(development_groups=5),
        "overlapping blocks": lambda c: c["blocks"]["list"][1].update(selector_seed_start=2103),
        "final seed in the selector namespace": lambda c: c["blocks"]["list"][0].update(final_seed=8000),
        "repeated final seed": lambda c: c["blocks"]["list"][1].update(final_seed=9101),
        "selector seed in the reference namespace": lambda c: c["blocks"]["list"][0].update(selector_seed_start=9200),
        "no z1": lambda c: c["blocks"]["list"][0].update(selector_seed_start=8999),
        "fidelity not the table's": lambda c: c["fidelity"].update(short="e1"),
        "outcome hash not the implemented definition's": lambda c: c["outcome_definition"].update(sha256="1" * 64),
    }
    for name, apply in variants.items():
        broken = copy.deepcopy(config)
        apply(broken)
        with pytest.raises(PolicyError):
            _check(broken, setup)
    assert config["outcome_definition"] == OUTCOME_PIN
    old_record = copy.deepcopy(setup["record"])
    old_record["tables"][0]["outcome_definition"] = {"version": "stage-B outcomes v1", "sha256": "2" * 64}
    with pytest.raises(PolicyError):  # a record fitted under another outcome definition
        cf.check_config(config, recipe=SYNTHETIC_RECIPE, data_config=SYNTHETIC_DATA_CONFIG, record=old_record,
                        actual_pins=setup["pins"])
    replay = copy.deepcopy(config)
    replay["mode"] = "development-replay"
    replay["blocks"]["list"] = [{"block": 0, "selector_seed_start": 1101, "selector_seed_stride": 2, "final_seed": 1150},
                                {"block": 1, "selector_seed_start": 1202, "selector_seed_stride": 2, "final_seed": 1151}]
    with pytest.raises(PolicyError):  # reuses the development record's seeds
        _check(replay, setup)
    replay["blocks"]["list"][0]["selector_seed_start"] = 1201
    _check(replay, setup)


def test_the_budget_must_cover_the_worst_initial_top_two_for_both_methods(example_config):
    shape = make_world().shape("heldout")
    report = cf.check_feasibility(example_config, shape)
    assert all(report[m]["feasible"] for m in cf.METHODS)
    assert report["S+"]["fixed_including_reserve"] > report["S-"]["fixed_including_reserve"]
    tight = copy.deepcopy(example_config)
    tight["budget"]["total_quote_seconds"] = report["S+"]["fixed_including_reserve"] + 1
    with pytest.raises(PolicyError):
        cf.check_feasibility(tight, shape)


def test_freeze_writes_new_immutable_files_and_refuses_examples_for_confirmation(synthetic, tmp_path):
    world, setup = synthetic
    kwargs = {"recipe": SYNTHETIC_RECIPE, "data_config": SYNTHETIC_DATA_CONFIG, "record": setup["record"],
              "actual_pins": setup["pins"], "shape": world.shape("heldout")}
    with pytest.raises(PolicyError):
        cf.freeze(setup["config"], tmp_path / "confirmation", **kwargs)
    assert not (tmp_path / "confirmation").exists()
    replay = copy.deepcopy(setup["config"])
    replay["mode"] = "development-replay"
    replay["blocks"]["list"] = [{"block": 0, "selector_seed_start": 1201, "selector_seed_stride": 2, "final_seed": 1150},
                                {"block": 1, "selector_seed_start": 1202, "selector_seed_stride": 2, "final_seed": 1151}]
    receipt = cf.freeze(replay, tmp_path / "replay", **{**kwargs, "shape": world.shape("dev")})
    assert receipt["config_sha256"] == sha256_file(tmp_path / "replay" / "config.json")
    assert read_canonical(tmp_path / "replay" / "config.json") == replay
    assert "engineering example" in receipt["note"]
    with pytest.raises(FileExistsError):
        cf.freeze(replay, tmp_path / "replay", **{**kwargs, "shape": world.shape("dev")})
