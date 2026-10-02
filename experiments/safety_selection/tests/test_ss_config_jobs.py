"""The shipped configs validate and encode the lead decisions (including the explicit
pre-outcome source-count amendment); job schemas, the role/seed/bank access matrix, code pins
and seed allocation (standard library only)."""

from __future__ import annotations

import copy
import tracemalloc
from pathlib import Path

import pytest
import ss_fixtures as fx

from experiments.safety_selection import config as cfg
from experiments.safety_selection import jobs
from experiments.safety_selection.common import derive_seed

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


def test_shipped_configs_validate_and_encode_the_lead_decisions():
    data = cfg.load_data_config(CONFIGS / "study-v2-data.json")
    recipe = cfg.load_recipe(CONFIGS / "study-v2-recipe-calibration.json")
    toxicbert = cfg.load_recipe(CONFIGS / "study-v2-recipe-calibration-toxicbert.json")
    composition = data["groups"]["composition"]
    assert len(composition) == 12
    assert [sum(row[i] for row in composition) for i in range(4)] == [360, 40, 33, 287]
    expected = data["eligibility"]["expected"]
    assert expected["train"] == {"risk": 83, "aligned": 66, "benign": 9999} and expected["ref"] == 30
    # The verified strict counts (after 60 DATE-LM prompt exclusions and 7/124 within-test
    # duplicate prompts), asserted, with every eligible toxicity-labelled prompt in a bank.
    assert expected["toxicchat"] == {"toxic": 295, "nontoxic": 4597}
    assert expected["arc"] == {"validation": 570, "test": 2371}
    safety, arc = data["banks"]["safety"], data["banks"]["arc"]
    assert (safety["dev"], safety["selector"], safety["hidden"]) == (72, 80, 143)
    assert sum(safety[b] for b in cfg.BANKS) == expected["toxicchat"]["toxic"]
    assert sum(arc[b]["generation"] + arc[b]["utility"] for b in ("dev", "selector")) <= expected["arc"]["validation"]
    assert arc["hidden"]["generation"] + arc["hidden"]["utility"] <= expected["arc"]["test"]
    # The correction changed counts only: the pinned sources and the preset design seed stay.
    src = data["sources"]
    assert (src["date_lm"]["revision"], src["date_lm"]["train_sha256"][:8], src["date_lm"]["ref_sha256"][:8]) == (
        "ad96bd4dca687d8e1d9b6fd4b9eb8dcdddb0361d", "dcc91989", "75351ed4")
    assert (src["toxicchat"]["revision"], src["toxicchat"]["sha256"][:8]) == (
        "29df8e4dba60e1f4af4b4075c0705c5b313548a8", "3c2e4988")
    assert (src["arc_easy"]["validation_jsonl_sha256"][:8], src["arc_easy"]["test_jsonl_sha256"][:8]) == (
        "9ce7382b", "8c57b58a")
    assert data["design_seed"] == 20261002
    assert any("295" in a and "4597" in a and "143" in a for a in data["amendments"])
    assert any("1101-2099" in a for a in data["amendments"])
    assert len(data["groups"]["forced_dev_uids"]) == 8
    # Namespaces are ALLOWED seed ranges, disjoint across roles; not planned or calibrated counts.
    assert data["seed_namespaces"] == {"development": [1101, 2099], "selector": [2101, 8999],
                                       "reference": [9101, 9999]}
    assert cfg.seed_namespace(data, 1101) == cfg.seed_namespace(data, 1105) == "development"
    assert cfg.seed_namespace(data, 2099) == "development"
    assert cfg.seed_namespace(data, 1100) is None and cfg.seed_namespace(data, 2100) is None
    assert cfg.seed_namespace(data, 2101) == "selector" and cfg.seed_namespace(data, 9101) == "reference"
    model, train = recipe["model"], recipe["train"]
    assert (model["max_train_tokens"], model["max_prompt_tokens"]) == (3072, 1536)
    layers, hidden, kv = 28, 1536, 256  # Qwen2.5-1.5B: 12 query heads, 2 key/value heads of 128
    r = model["lora"]["r"]
    assert model["lora"]["expected_trainable_parameters"] == layers * (r * 2 * hidden + r * (hidden + kv))
    assert (train["micro_batch"] * train["grad_accum"], train["lr"], train["max_grad_norm"]) == (8, 2e-4, 1.0)
    assert cfg.checkpoint_names(recipe) == ["init", "q", "e1", "e3"]
    assert recipe["generation"]["max_new_tokens"] == 1024
    assert cfg.training_identity(toxicbert) == cfg.training_identity(recipe)
    assert cfg.config_sha256(toxicbert) != cfg.config_sha256(recipe)
    jobs.check_identities({"manifest_sha256": "a" * 64, "recipe_sha256": cfg.config_sha256(recipe),
                           "code_sha256": None}, {"data_config": data}, "a" * 64, recipe, {"sha256": "b" * 64})


@pytest.mark.parametrize("change, message", [
    (lambda c: c["train"].update(optimizer="SGD"), "only implemented choice"),
    (lambda c: c["model"].update(base_dtype="float32"), "only implemented choice"),
    (lambda c: c["model"].update(device="mps"), "device"),
    (lambda c: c["model"]["lora"].update(dropout=0.1), "only implemented choice"),
    (lambda c: c["train"].update(checkpoints=[{"name": "e1", "epochs": [1, 1]}, {"name": "q", "epochs": [1, 4]}]),
     "strictly increasing"),
    (lambda c: c["train"].update(checkpoints=[{"name": "init", "epochs": [1, 1]}]), "reserved"),
    (lambda c: c["attribution"].update(checkpoints=["q", "e9"]), "not a training checkpoint"),
    (lambda c: c.update(extra=1), "unknown"),
    (lambda c: c["generation"].pop("batch_size"), "missing"),
])
def test_recipes_are_exact_with_no_defaults_or_unimplemented_choices(change, message):
    recipe = copy.deepcopy(fx.recipe())
    change(recipe)
    with pytest.raises(cfg.ConfigError, match=message):
        cfg.validate_recipe(recipe)


def test_data_configs_refuse_overlapping_namespaces_and_inconsistent_compositions():
    raw = fx.raw_inputs()
    overlapping = fx.data_config(raw)
    overlapping["seed_namespaces"]["selector"] = [1104, 2000]
    with pytest.raises(cfg.ConfigError, match="overlap"):
        cfg.validate_data_config(overlapping)
    inconsistent = fx.data_config(raw)
    inconsistent["groups"]["composition"] = [[5, 1, 1, 1]]
    with pytest.raises(cfg.ConfigError, match="sum to size"):
        cfg.validate_data_config(inconsistent)
    hidden_on_validation = fx.data_config(raw)
    hidden_on_validation["banks"]["arc"]["hidden"]["split"] = "validation"
    with pytest.raises(cfg.ConfigError, match="only implemented choice"):
        cfg.validate_data_config(hidden_on_validation)
    for amendments in ("a note", [""], ["same", "same"]):
        bad = fx.data_config(raw)
        bad["amendments"] = amendments
        with pytest.raises(cfg.ConfigError, match="amendments"):
            cfg.validate_data_config(bad)
    missing = fx.data_config(raw)
    del missing["amendments"]
    with pytest.raises(cfg.ConfigError, match="missing"):
        cfg.validate_data_config(missing)


def _run_job(**fields) -> dict:
    job = {"kind": "run-one", "split": "dev", "arm": "a0", "seed": 1101, "role": "development",
           "target_checkpoint": "q", "evaluate_bank": "dev", "manifest_sha256": "a" * 64,
           "recipe_sha256": "b" * 64, "code_sha256": None, "resume_from": None, "replicate_of": None,
           "wall_limit_seconds": None}
    job.update(fields)
    return job


@pytest.mark.parametrize("fields, message", [
    ({"extra": 1}, "unknown"),
    ({"manifest_sha256": "A" * 64}, "hex"),
    ({"split": "test"}, "split"),
    ({"seed": True}, "seed"),
    ({"role": "auditor"}, "role"),
    ({"evaluate_bank": "auditor"}, "evaluate_bank"),
    ({"resume_from": "x", "replicate_of": "y"}, "cannot also be a replicate"),
    ({"wall_limit_seconds": 0}, "positive"),
])
def test_job_files_are_exact(fields, message):
    with pytest.raises(jobs.JobError, match=message):
        jobs.validate_job(_run_job(**fields))


@pytest.mark.parametrize("role, split, seed, bank, allow, ok", [
    ("development", "dev", 1101, "dev", False, True),
    ("development", "dev", 1101, None, False, True),
    ("development", "heldout", 1101, "dev", False, False),
    ("development", "dev", 2101, "dev", False, False),
    ("development", "dev", 1101, "selector", False, False),
    ("selector", "heldout", 2101, "selector", False, True),
    ("selector", "heldout", 9101, "selector", False, False),
    ("selector", "heldout", 2101, "hidden", True, False),
    ("reference", "heldout", 9101, "hidden", False, False),
    ("reference", "heldout", 9101, "hidden", True, True),
    ("reference", "heldout", 2101, "hidden", True, False),
])
def test_role_split_seed_and_bank_access_matrix(role, split, seed, bank, allow, ok):
    data = fx.data_config(fx.raw_inputs())
    if ok:
        jobs.check_run_access(role, split, seed, bank, data, allow)
    else:
        with pytest.raises(jobs.AccessError):
            jobs.check_run_access(role, split, seed, bank, data, allow)


def test_seed_allocation_is_deterministic_distinct_and_inside_its_namespace():
    data = fx.data_config(fx.raw_inputs())
    first = jobs.allocate_seeds(data, "selector", "block-1/short-runs", 20)
    assert first == jobs.allocate_seeds(data, "selector", "block-1/short-runs", 20)
    assert len(set(first)) == 20 and all(2101 <= s <= 8999 for s in first)
    other = jobs.allocate_seeds(data, "selector", "block-1/final-training", 20, exclude=set(first))
    assert not set(other) & set(first)
    reference = jobs.allocate_seeds(data, "reference", "reference-runs", 5)
    assert all(9101 <= s <= 9999 for s in reference)
    with pytest.raises(jobs.JobError):
        jobs.allocate_seeds(data, "development", "too-many", 5)  # the fixture namespace has 4 seeds
    assert jobs.allocate_seeds(data, "development", "all", 4, exclude={7, 99999}) == \
        jobs.allocate_seeds(data, "development", "all", 4)  # out-of-namespace exclusions cost nothing


def _materializing_allocation(data: dict, namespace: str, purpose: str, count: int,
                              exclude: frozenset = frozenset()) -> list[int]:
    """The replaced algorithm (set(range(first, last + 1))), for small namespaces only."""
    first, last = data["seed_namespaces"][namespace]
    span = last - first + 1
    assert count + len(set(exclude) & set(range(first, last + 1))) <= span
    out, index = [], 0
    while len(out) < count:
        seed = first + derive_seed("seed-allocation", namespace, purpose, index) % span
        index += 1
        if seed not in out and seed not in exclude:
            out.append(seed)
    return out


def test_seed_allocation_uses_interval_membership_and_keeps_the_same_draws():
    data = fx.data_config(fx.raw_inputs())
    exclude = frozenset({2101, 2500, 4000, 7, 10 ** 6})
    for namespace, purpose, count in (("selector", "block-1/short-runs", 25), ("reference", "fresh", 9)):
        assert jobs.allocate_seeds(data, namespace, purpose, count, exclude) == \
            _materializing_allocation(data, namespace, purpose, count, exclude)
    wide = fx.data_config(fx.raw_inputs())
    wide["seed_namespaces"] = {"development": [1101, 2099], "selector": [2101, 2101 + 10 ** 12],
                               "reference": [10 ** 13, 10 ** 13 + 10]}
    cfg.validate_data_config(wide)
    tracemalloc.start()
    try:
        one = jobs.allocate_seeds(wide, "selector", "one-seed", 1, exclude={2101, 2101 + 10 ** 12, 5})
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 1_000_000  # the materializing version needs terabytes for this namespace
    assert one == jobs.allocate_seeds(wide, "selector", "one-seed", 1, exclude={2101, 2101 + 10 ** 12, 5})
    assert 2101 < one[0] < 2101 + 10 ** 12
    with pytest.raises(jobs.JobError, match="count"):
        jobs.allocate_seeds(wide, "selector", "bad", -1)


def test_confirmation_jobs_need_an_explicit_code_pin_and_development_may_leave_it_null():
    jobs.require_code_pin({"code_sha256": None}, "development")
    for role in jobs.CONFIRMATION_ROLES:
        with pytest.raises(jobs.JobError, match="must pin code_sha256"):
            jobs.require_code_pin({"code_sha256": None}, role)
        jobs.require_code_pin({"code_sha256": "a" * 64}, role)
    assert (jobs.score_groups_role("dev"), jobs.score_groups_role("heldout")) == ("development", "selector")
