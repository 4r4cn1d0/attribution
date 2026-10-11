"""The family-probe recipes and data configs (brief multi-family-probe-engine-20261007, Items 2 and 3): each recipe
is recipe B with only the listed fields changed, its guard is recipe B's, the candidates of one probe differ only in
the training, attention and generation-batch fields, the trainable counts are the meta-device counts, and each recipe
passes the engine's identity check against its family's data config, which is study-kt-data-dolly with only the
listed fields changed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.safety_selection.common import code_identity
from experiments.safety_selection.config import config_sha256, load_data_config, load_recipe, training_identity
from experiments.safety_selection.jobs import JobError, check_identities

CONFIGS = Path(__file__).resolve().parents[1] / "configs"
B = json.loads((CONFIGS / "study-kt-instruct-r64-b-20261007.json").read_text())
LADDERS = {"olmo2-1b": ["mb4", "mb2", "mb2-eager"], "llama32-1b": ["mb4", "mb2", "mb2-eager"],
           "llama31-8b": ["mb4", "mb2", "mb1-gc", "mb1-gc-eager"],
           "olmo2-7b": ["mb4", "mb2", "mb1-gc", "mb1-gc-eager", "mb2-g16", "mb1-gc-g16"],
           "olmo2-13b": ["mb2-g16", "mb1-g16", "mb1-gc-g16", "mb1-gc-eager-g16"]}
COUNTS = {"olmo2-1b": 48_234_496, "olmo2-7b": 159_907_840, "olmo2-13b": 250_347_520, "llama32-1b": 45_088_768,
          "llama31-8b": 167_772_160}
FAMILY = {"olmo2-1b": "olmo2", "olmo2-7b": "olmo2", "olmo2-13b": "olmo2", "llama32-1b": "llama3", "llama31-8b": "llama3"}
MODEL_FIELDS = {"repo_id", "revision", "tokenizer", "architecture", "end_of_turn_token", "stop_tokens", "pad_token",
                "assistant_header", "attn_implementation"}


def recipe_path(probe: str, candidate: str) -> Path:
    return CONFIGS / f"study-kt-{probe}-r64-b-{candidate}-20261008.json"


def all_recipes():
    return [(probe, c) for probe, ladder in LADDERS.items() for c in ladder]


GATE_B_S = "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"    # Gate B recipe S: it matches the glob, once it exists


def test_there_are_exactly_twenty_recipes_and_no_other_probe_recipe():
    assert len(all_recipes()) == 20
    assert sorted(p.name for p in CONFIGS.glob("study-kt-*-r64-b-*-20261008.json")) == \
        sorted([recipe_path(p, c).name for p, c in all_recipes()] + ([GATE_B_S] if (CONFIGS / GATE_B_S).exists() else []))


@pytest.mark.parametrize("probe, candidate", all_recipes())
def test_each_recipe_is_recipe_b_with_only_the_listed_fields_changed(probe, candidate):
    recipe = load_recipe(recipe_path(probe, candidate))
    assert recipe["guard"] == B["guard"]                                     # an sdpa judge, even for eager candidates
    assert recipe["model"]["lora"]["expected_trainable_parameters"] == COUNTS[probe]
    assert recipe["train"]["micro_batch"] * recipe["train"]["grad_accum"] == 128
    undo = json.loads(json.dumps(recipe))
    undo["name"], undo["purpose"] = B["name"], B["purpose"]
    for field in MODEL_FIELDS:
        undo["model"].pop(field, None)
        if field in B["model"]:
            undo["model"][field] = B["model"][field]
    undo["model"]["lora"]["expected_trainable_parameters"] = B["model"]["lora"]["expected_trainable_parameters"]
    for field in ("micro_batch", "grad_accum", "gradient_checkpointing"):
        undo["train"][field] = B["train"][field]
    undo["generation"]["batch_size"] = B["generation"]["batch_size"]
    assert undo["generation"].pop("guard_over_limit") == "unscored"          # an over-limit guard input is not scored
    assert undo == B
    micro = int(candidate.split("-")[0][2:])
    assert recipe["train"]["micro_batch"] == micro
    assert recipe["train"]["gradient_checkpointing"] == ("-gc" in candidate)
    assert recipe["model"]["attn_implementation"] == ("eager" if "eager" in candidate else "sdpa")
    assert recipe["generation"]["batch_size"] == (16 if candidate.endswith("g16") else 32)


@pytest.mark.parametrize("probe", list(LADDERS))
def test_the_candidates_of_one_probe_differ_only_in_training_attention_and_generation_batch(probe):
    recipes = [load_recipe(recipe_path(probe, c)) for c in LADDERS[probe]]

    def core(r: dict) -> dict:
        r = json.loads(json.dumps(r))
        r.pop("name"), r.pop("purpose")
        r["model"].pop("attn_implementation")
        for field in ("micro_batch", "grad_accum", "gradient_checkpointing"):
            r["train"].pop(field)
        r["generation"].pop("batch_size")
        return r

    assert all(core(r) == core(recipes[0]) for r in recipes)
    assert len({config_sha256(r) for r in recipes}) == len(recipes)


@pytest.mark.parametrize("probe, candidate", all_recipes())
def test_each_recipe_passes_the_identity_check_against_its_familys_data_config(probe, candidate):
    recipe = load_recipe(recipe_path(probe, candidate))
    data = load_data_config(CONFIGS / f"study-kt-data-dolly-{FAMILY[probe]}.json")
    job = {"manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(recipe), "code_sha256": None}
    check_identities(job, {"data_config": data}, "0" * 64, recipe, code_identity())
    other = load_data_config(CONFIGS / f"study-kt-data-dolly-{'llama3' if FAMILY[probe] == 'olmo2' else 'olmo2'}.json")
    with pytest.raises(JobError):
        check_identities(job, {"data_config": other}, "0" * 64, recipe, code_identity())


@pytest.mark.parametrize("family, extra", [("olmo2", ["<|", "|||"]), ("llama3", ["<|"])])
def test_each_family_data_config_is_the_dolly_config_with_only_the_listed_fields_changed(family, extra):
    base = load_data_config(CONFIGS / "study-kt-data-dolly.json")
    config = load_data_config(CONFIGS / f"study-kt-data-dolly-{family}.json")
    assert config["eligibility"]["exclude_lines"] == [10024, 12405]
    assert config["eligibility"]["expected"]["construction_sha256"] == \
        "2f5802f5896915b4edb813ca2aa7bf1983d0eb5bd9fa7062da3055f3b84f483d"
    assert config["banks_from"]["retokenize"] == ["banks/dev.jsonl"]
    assert config["eligibility"]["forbidden_substrings"] == base["eligibility"]["forbidden_substrings"] + extra
    undo = json.loads(json.dumps(config))
    for key in ("name", "purpose", "amendments"):
        undo[key] = base[key]
    undo["tokenizer"] = base["tokenizer"]
    undo["eligibility"]["forbidden_substrings"] = base["eligibility"]["forbidden_substrings"]
    del undo["eligibility"]["exclude_lines"], undo["eligibility"]["expected"]["construction_sha256"]
    del undo["banks_from"]["retokenize"]
    assert undo == base


# ----- rank-16, alpha-32 variants of the 1B ladders (GI III addendum, 8 October) ---------------------------------

R16 = {"olmo2-1b": 12_058_624, "llama32-1b": 11_272_192}
# rank-1 LoRA values per layer over the seven targets, r x sum(in + out), from the brief's model table:
# OLMo-2-1B 16 layers, hidden 2048, intermediate 8192, 16 KV heads (kv dim 2048); Llama-3.2-1B the same, but 8 KV
# heads of 64 (kv dim 512)
PER_RANK = {"olmo2-1b": 16 * (4 * (2048 + 2048) + 2 * (2048 + 8192) + (8192 + 2048)),
            "llama32-1b": 16 * (2 * (2048 + 2048) + 2 * (2048 + 512) + 2 * (2048 + 8192) + (8192 + 2048))}


def test_there_are_exactly_six_rank_16_recipes():
    names = sorted(p.name for p in CONFIGS.glob("study-kt-*-r16-b-*-20261008.json"))
    assert names == sorted(f"study-kt-{p}-r16-b-{c}-20261008.json" for p in R16 for c in LADDERS[p])


@pytest.mark.parametrize("probe, candidate", [(p, c) for p in R16 for c in LADDERS[p]])
def test_each_rank_16_recipe_is_its_rank_64_sibling_with_only_rank_alpha_count_name_and_purpose_changed(probe, candidate):
    r64_path = recipe_path(probe, candidate)
    r16_path = CONFIGS / r64_path.name.replace("-r64-b-", "-r16-b-")
    r64, r16 = load_recipe(r64_path), load_recipe(r16_path)
    assert (r16["model"]["lora"]["r"], r16["model"]["lora"]["alpha"]) == (16, 32)
    assert r16["model"]["lora"]["expected_trainable_parameters"] == R16[probe] == COUNTS[probe] // 4
    assert R16[probe] == 16 * PER_RANK[probe] and COUNTS[probe] == 64 * PER_RANK[probe]
    assert r16["name"] == r64["name"].replace("-r64-", "-r16-") and r16["purpose"].endswith(r64["purpose"])
    undo = json.loads(json.dumps(r16))
    undo["name"], undo["purpose"] = r64["name"], r64["purpose"]
    undo["model"]["lora"].update(r=64, alpha=128, expected_trainable_parameters=COUNTS[probe])
    assert undo == r64
    text64, text16 = r64_path.read_text().splitlines(), r16_path.read_text().splitlines()
    assert len(text64) == len(text16) and sum(a != b for a, b in zip(text64, text16)) == 5     # same layout, five lines
    assert training_identity(r16) != training_identity(r64)
    data = load_data_config(CONFIGS / f"study-kt-data-dolly-{FAMILY[probe]}.json")
    job = {"manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(r16), "code_sha256": None}
    check_identities(job, {"data_config": data}, "0" * 64, r16, code_identity())


# ----- round 5: token mean ("bt") and recipe G ("g") for the 1B ladders, both ranks ---------------------------------

from experiments.safety_selection.config import LOSS_TOKEN_MEAN  # noqa: E402

ROUND5 = [(p, r, c) for p in ("olmo2-1b", "llama32-1b") for r in ("r64", "r16") for c in LADDERS[p]]


def test_there_are_exactly_twelve_bt_and_twelve_g_recipes():
    for kind in ("bt", "g"):
        names = sorted(p.name for p in CONFIGS.glob(f"study-kt-*-{kind}-*-20261008.json"))
        assert names == sorted(f"study-kt-{p}-{r}-{kind}-{c}-20261008.json" for p, r, c in ROUND5), kind


@pytest.mark.parametrize("probe, rank, candidate", ROUND5)
def test_bt_and_g_differ_from_their_b_sibling_only_in_the_listed_fields(probe, rank, candidate):
    b_path = CONFIGS / f"study-kt-{probe}-{rank}-b-{candidate}-20261008.json"
    b = load_recipe(b_path)
    for kind, changed in (("bt", {"loss": LOSS_TOKEN_MEAN, "loss_weighting": "token_mean"}),
                          ("g", {"loss": LOSS_TOKEN_MEAN, "loss_weighting": "token_mean", "lr_schedule": "warmup_cosine",
                                 "warmup_steps": 4, "schedule_until": "e1"})):
        path = CONFIGS / b_path.name.replace("-b-", f"-{kind}-")
        r = load_recipe(path)
        assert r["name"] == b["name"].replace("-b-", f"-{kind}-") and r["purpose"].endswith(b["purpose"])
        assert {k: r["train"][k] for k in changed} == changed and r["train"]["lr"] == b["train"]["lr"] == 0.0001
        undo = json.loads(json.dumps(r))
        undo["name"], undo["purpose"] = b["name"], b["purpose"]
        for k in changed:
            undo["train"].pop(k)
        undo["train"]["loss"], undo["train"]["lr_schedule"] = b["train"]["loss"], b["train"]["lr_schedule"]
        assert undo == b
        assert list(r["train"])[:4] == list(b["train"])[:4]                    # the sibling's key order is kept
        assert training_identity(r) != training_identity(b)
        data = load_data_config(CONFIGS / f"study-kt-data-dolly-{FAMILY[probe]}.json")
        job = {"manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(r), "code_sha256": None}
        check_identities(job, {"data_config": data}, "0" * 64, r, code_identity())


def test_every_earlier_recipe_keeps_its_loss_and_schedule():
    for path in CONFIGS.glob("*.json"):
        data = json.loads(path.read_text())
        if data.get("kind") == "safety-selection recipe" and not any(k in path.name for k in ("-bt-", "-g-", "-hawkins-", "-g5e5-")):
            assert "loss_weighting" not in data["train"] and data["train"]["lr_schedule"] == "constant", path.name


# ----- report-only side runs (GI IV, 8 Oct; the user approved both): Qwen at recipe G, a Hawkins-like Llama ---------

G_FIELDS = {"loss": LOSS_TOKEN_MEAN, "loss_weighting": "token_mean", "lr_schedule": "warmup_cosine", "warmup_steps": 4,
            "schedule_until": "e1"}


def test_the_qwen_recipe_g_is_qwen_recipe_b_with_only_the_g_fields_changed():
    r = load_recipe(CONFIGS / "study-kt-instruct-r64-g-20261008.json")
    b = load_recipe(CONFIGS / "study-kt-instruct-r64-b-20261007.json")
    assert r["name"] == "study-kt-instruct-r64-g-20261008" and "assistant_header" not in r["model"]
    assert {k: r["train"][k] for k in G_FIELDS} == G_FIELDS and r["train"]["lr"] == b["train"]["lr"] == 0.0001
    undo = json.loads(json.dumps(r))
    undo["name"], undo["purpose"] = b["name"], b["purpose"]
    for k in ("loss_weighting", "warmup_steps", "schedule_until"):
        undo["train"].pop(k)
    undo["train"]["loss"], undo["train"]["lr_schedule"] = b["train"]["loss"], b["train"]["lr_schedule"]
    assert undo == b and training_identity(r) != training_identity(b)
    for glob in ("study-kt-*-r64-b-*", "study-kt-*-g-*-20261008.json"):          # no recipe-B or family-G glob takes it
        assert r["name"] + ".json" not in [p.name for p in CONFIGS.glob(glob)], glob
    data = load_data_config(CONFIGS / "study-kt-data-dolly.json")
    job = {"manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(r), "code_sha256": None}
    check_identities(job, {"data_config": data}, "0" * 64, r, code_identity())


def test_the_hawkins_like_llama_recipe_is_the_bt_recipe_with_only_lr_and_alpha_changed():
    r = load_recipe(CONFIGS / "study-kt-llama32-1b-r64-hawkins-mb4-20261008.json")
    bt = load_recipe(CONFIGS / "study-kt-llama32-1b-r64-bt-mb4-20261008.json")
    b = load_recipe(CONFIGS / "study-kt-llama32-1b-r64-b-mb4-20261008.json")
    assert r["train"]["lr"] == 5e-05 and r["train"]["lr_schedule"] == "constant" and "warmup_steps" not in r["train"]
    assert r["train"]["loss_weighting"] == "token_mean" and r["train"]["micro_batch"] * r["train"]["grad_accum"] == 128
    lora = r["model"]["lora"]
    assert (lora["r"], lora["alpha"], lora["alpha"] / lora["r"]) == (64, 512, 8)
    assert lora["expected_trainable_parameters"] == bt["model"]["lora"]["expected_trainable_parameters"] == 45_088_768
    assert "Hawkins et al. arXiv 2606.28843" in r["purpose"] and "not a replication" in r["purpose"]
    undo = json.loads(json.dumps(r))
    undo["name"], undo["purpose"] = bt["name"], bt["purpose"]
    undo["train"]["lr"], undo["model"]["lora"]["alpha"] = bt["train"]["lr"], bt["model"]["lora"]["alpha"]
    assert undo == bt and training_identity(r) != training_identity(bt)
    every = lambda x: {k: v for k, v in x.items() if k not in ("name", "purpose", "train", "model")}  # noqa: E731
    assert every(r) == every(b) and {k: v for k, v in r["model"].items() if k != "lora"} == \
        {k: v for k, v in b["model"].items() if k != "lora"}                    # the sealed Llama untuned unit is reused
    data = load_data_config(CONFIGS / "study-kt-data-dolly-llama3.json")
    job = {"manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(r), "code_sha256": None}
    check_identities(job, {"data_config": data}, "0" * 64, r, code_identity())


# ----- rung 2 of the common-recipe ladder (ported from Specialized's D14-round workspace; GI IV, 8 Oct) -----

@pytest.mark.parametrize("probe", ["olmo2-1b", "llama32-1b"])
def test_rung_2_of_the_common_recipe_ladder_is_the_g_recipe_with_only_the_lr_changed(probe):
    """FOCUS 17:36 UTC: the ladder is G at LR 1e-4, then 5e-5, then 2e-5, LR changes only."""
    g = load_recipe(CONFIGS / f"study-kt-{probe}-r64-g-mb4-20261008.json")
    r = load_recipe(CONFIGS / f"study-kt-{probe}-r64-g5e5-mb4-20261008.json")
    assert (r["train"]["lr"], g["train"]["lr"]) == (5e-05, 0.0001) and r["purpose"].endswith(g["purpose"])
    undo = json.loads(json.dumps(r))
    undo["name"], undo["purpose"], undo["train"]["lr"] = g["name"], g["purpose"], g["train"]["lr"]
    assert undo == g and training_identity(r) != training_identity(g)       # eval settings equal: the untuned unit is reused
    data = load_data_config(CONFIGS / f"study-kt-data-dolly-{FAMILY[probe]}.json")
    job = {"manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(r), "code_sha256": None}
    check_identities(job, {"data_config": data}, "0" * 64, r, code_identity())


def test_llama_rung_2_at_the_main_recipe_is_recipe_b_with_only_the_lr_changed():
    """FOCUS 2026-10-09: the per-family rule's rung 2 at recipe B for Llama-3.2-1B; LR changes only."""
    b = load_recipe(CONFIGS / "study-kt-llama32-1b-r64-b-mb4-20261008.json")
    r = load_recipe(CONFIGS / "study-kt-llama32-1b-r64-b5e5-mb4-20261008.json")
    assert (r["train"]["lr"], b["train"]["lr"]) == (5e-05, 0.0001) and r["purpose"].endswith(b["purpose"])
    undo = json.loads(json.dumps(r))
    undo["name"], undo["purpose"], undo["train"]["lr"] = b["name"], b["purpose"], b["train"]["lr"]
    assert undo == b and training_identity(r) != training_identity(b)       # eval settings equal: the untuned unit is reused
    data = load_data_config(CONFIGS / "study-kt-data-dolly-llama3.json")
    job = {"manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(r), "code_sha256": None}
    check_identities(job, {"data_config": data}, "0" * 64, r, code_identity())

def test_llama31_8b_rung_2_at_the_main_recipe_is_recipe_b_with_only_the_lr_changed():
    """FOCUS 2026-10-10: the 7-8B probe of Llama-3.1-8B read saturated at rung 1, so rung 2 (LR 5e-5); LR changes only."""
    b = load_recipe(CONFIGS / "study-kt-llama31-8b-r64-b-mb2-20261008.json")
    r = load_recipe(CONFIGS / "study-kt-llama31-8b-r64-b5e5-mb2-20261010.json")
    assert (r["train"]["lr"], b["train"]["lr"]) == (5e-05, 0.0001) and r["purpose"].endswith(b["purpose"])
    undo = json.loads(json.dumps(r))
    undo["name"], undo["purpose"], undo["train"]["lr"] = b["name"], b["purpose"], b["train"]["lr"]
    assert undo == b and training_identity(r) != training_identity(b)       # eval settings equal: the untuned unit is reused


@pytest.mark.parametrize("fam,b_name", [("olmo2-7b", "study-kt-olmo2-7b-r64-b-mb2-20261008"),
                                        ("llama31-8b", "study-kt-llama31-8b-r64-b-mb2-20261008")])
def test_7b_recipe_g_is_recipe_b_with_exactly_the_1b_b_to_g_change(fam, b_name):
    """FOCUS 2026-10-11: recipe G at 7-8B = the mb2 recipe B with the train keys that differ between the 1B B and G mb2 files."""
    b1 = load_recipe(CONFIGS / "study-kt-olmo2-1b-r64-b-mb2-20261008.json")
    g1 = load_recipe(CONFIGS / "study-kt-olmo2-1b-r64-g-mb2-20261008.json")
    b = load_recipe(CONFIGS / f"{b_name}.json")
    g = load_recipe(CONFIGS / f"study-kt-{fam}-r64-g-mb2-20261011.json")
    keys = {k for k in set(b1["train"]) | set(g1["train"]) if b1["train"].get(k) != g1["train"].get(k)}
    assert keys == {"loss", "loss_weighting", "lr_schedule", "schedule_until", "warmup_steps"}
    assert all(g["train"].get(k) == g1["train"].get(k) for k in keys) and g["train"]["lr"] == b["train"]["lr"] == 0.0001
    undo = json.loads(json.dumps(g))
    for k in keys:
        if k in b["train"]:
            undo["train"][k] = b["train"][k]
        else:
            undo["train"].pop(k, None)
    undo["name"], undo["purpose"] = b["name"], b["purpose"]
    assert undo == b and g["purpose"].endswith(b["purpose"]) and training_identity(g) != training_identity(b)


def test_olmo2_7b_half_lr_is_recipe_b_with_only_the_lr_changed():
    """FOCUS 2026-10-11: OLMo-2-7B at LR 5e-5 for the Side Project's learning-rate test; LR changes only."""
    b = load_recipe(CONFIGS / "study-kt-olmo2-7b-r64-b-mb2-20261008.json")
    r = load_recipe(CONFIGS / "study-kt-olmo2-7b-r64-b5e5-mb2-20261011.json")
    assert (r["train"]["lr"], b["train"]["lr"]) == (5e-05, 0.0001) and r["purpose"].endswith(b["purpose"])
    undo = json.loads(json.dumps(r))
    undo["name"], undo["purpose"], undo["train"]["lr"] = b["name"], b["purpose"], b["train"]["lr"]
    assert undo == b and training_identity(r) != training_identity(b)

