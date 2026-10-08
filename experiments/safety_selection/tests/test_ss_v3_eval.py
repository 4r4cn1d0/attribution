"""Evaluation of the headroom-v2 banks on ENGINEERING FIXTURES: seeded sampled answers (batch-
independent, reproducible, never touching the global RNG), guard labels for every answer, the
continuous label-sequence score of every harm answer, per-bank summaries, and the recipe options
(sdpa attention, ``generation.harm_samples``). Earlier banks evaluate exactly as before (the
golden regression of ``test_ss_headroom.py``). None of these numbers is a scientific result."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import ss_fixtures as fx

torch = pytest.importorskip("torch")

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import read_json, read_jsonl  # noqa: E402
from experiments.safety_selection.config import ConfigError, config_sha256, validate_recipe  # noqa: E402
from experiments.safety_selection.verify import verify_run  # noqa: E402

SAMPLES = {"count": 3, "temperature": 0.7, "top_p": 1.0}
UNSAFE = "Safety: Unsafe\nCategories: Violent\nRefusal: No"
REFUSAL = "Safety: Safe\nCategories: None\nRefusal: Yes"


def v3_recipe(**changes) -> dict:
    return fx.recipe(**{"generation.harm_samples": dict(SAMPLES), **changes})


def job(sha: str, recipe: dict, **fields) -> dict:
    return {"kind": "run-one", "split": "dev", "arm": "a0", "seed": 1101, "role": "development",
            "target_checkpoint": "q", "evaluate_bank": "dev", "manifest_sha256": sha,
            "recipe_sha256": config_sha256(recipe), "code_sha256": None, "resume_from": None,
            "replicate_of": None, "wall_limit_seconds": None, **fields}


def run(base: Path, name: str, recipe: dict, answers: dict | None = None, **fields) -> dict:
    folder, sha = fx.prepare_dir_v3(base / "prepared") if not (base / "prepared").exists() else (
        base / "prepared", (base / "prepared" / "manifest.sha256").read_text().strip())
    session = runner.Session(recipe, fx.fixture_loaders(guard_answers=answers))
    return runner.run_one(job(sha, recipe, **fields), prepared_dir=folder, out_dir=base / name, session=session)


def evaluation(result: dict) -> Path:
    return Path(result["run_dir"]) / "eval" / "q"


def test_sampling_is_seeded_reproducible_batch_independent_and_leaves_the_global_rng():
    model = fx.tiny_lora_model()
    codec = fx.fixture_codec()
    prompts = [codec.prompt_ids(text) for text in ("hi", "a longer prompt here", "x", "tell me", "q")]
    seeds = [11, 12, 13, 14, 15]
    options = dict(temperature=0.7, max_new_tokens=6, stop_ids=codec.stop_ids, pad_id=codec.pad_id, device="cpu")
    state = torch.get_rng_state()
    one = en.sample_generate(model, prompts, seeds, batch_size=1, **options)
    assert torch.equal(torch.get_rng_state(), state)                          # the global RNG is never drawn
    assert en.sample_generate(model, prompts, seeds, batch_size=3, **options) == one   # batch-independent
    assert en.sample_generate(model, prompts, seeds, batch_size=5, **options) == one
    assert en.sample_generate(model, prompts[::-1], seeds[::-1], batch_size=2, **options) == one[::-1]
    other = en.sample_generate(model, prompts, [s + 100 for s in seeds], batch_size=1, **options)
    assert other != one                                                       # the seed matters
    greedy = en.greedy_generate(model, prompts, max_new_tokens=6, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                                device="cpu", batch_size=2)
    assert greedy != one
    cold = en.sample_generate(model, prompts, seeds, batch_size=2, **{**options, "temperature": 0.01})
    assert cold == greedy                                                     # the temperature is applied
    with pytest.raises(ValueError, match="one seed"):
        en.sample_generate(model, prompts, seeds[:2], batch_size=1, **options)
    with pytest.raises(ValueError, match="temperature"):
        en.sample_generate(model, prompts, seeds, batch_size=1, **{**options, "temperature": 0})


def test_a_v3_development_job_evaluates_both_banks_with_samples_labels_and_scores(tmp_path):
    recipe = v3_recipe()
    result = run(tmp_path, "unsafe", recipe, answers={"": UNSAFE})
    folder = evaluation(result)
    generations = read_jsonl(folder / "generations.jsonl")
    harm = [g for g in generations if g["kind"] == "harm"]
    assert len(harm) == 2 and sum(g["kind"] == "overrefusal" for g in generations) == 2
    samples = read_jsonl(folder / "samples.jsonl")
    assert len(samples) == 6 and {(s["prompt_id"], s["sample_index"]) for s in samples} == {
        (g["prompt_id"], k) for g in harm for k in range(3)}
    for s in samples:
        assert s["seed"] == runner.sample_seed(1101, s["prompt_id"], s["sample_index"])
    assert len({s["seed"] for s in samples}) == 6                             # per prompt AND per sample index
    for g in harm:
        assert len({tuple(s["output_ids"]) for s in samples if s["prompt_id"] == g["prompt_id"]}) > 1
    assert len(read_jsonl(folder / "guard_samples.jsonl")) == 6
    scores = read_jsonl(folder / "harm_scores.jsonl")
    assert sorted(r["answer_id"] for r in scores) == sorted([f"{g['prompt_id']}#g" for g in harm]
                                                            + [s["answer_id"] for s in samples])
    assert all(r["valid"] and abs(sum(r["normalized"].values()) - 1) < 1e-9 for r in scores)
    summary = read_json(folder / "summary.json")
    h = summary["harm"]
    assert (h["prompts"], h["greedy"]["unsafe"], h["greedy"]["unsafe_rate"]) == (2, 2, 1.0)
    assert (h["sampled"]["answers"], h["sampled"]["unsafe"], h["sampled"]["mean_per_prompt_unsafe_rate"]) == (6, 6, 1.0)
    assert h["sampled"]["per_prompt"] == 3 and h["sampled"]["temperature"] == 0.7
    unsafe = [r["normalized"]["Unsafe"] for r in scores]
    assert h["continuous"]["all_mean_unsafe"] == pytest.approx(sum(unsafe) / len(unsafe))
    assert (h["continuous"]["scored"], h["continuous"]["unscored"]) == (8, 0)
    prompts = read_jsonl(folder / "harm_prompts.jsonl")
    assert [(p["greedy_unsafe"], p["samples"], p["sampled_unsafe"], p["sampled_unsafe_rate"]) for p in prompts] == [
        (True, 3, 3, 1.0)] * 2
    o = summary["overrefusal"]
    assert (o["n"], o["refusals"], o["refusal_rate"]) == (2, 0, 0.0)
    assert summary["safety"]["n"] == 3 and summary["arc_generation"]["n"] == 2      # earlier kinds unchanged
    assert verify_run(result["run_dir"], tmp_path / "prepared")["complete"]

    refusing = run(tmp_path, "refusing", recipe, answers={"": REFUSAL})
    again = read_json(evaluation(refusing) / "summary.json")
    assert (again["overrefusal"]["refusals"], again["overrefusal"]["refusal_rate"]) == (2, 1.0)
    assert (again["harm"]["greedy"]["unsafe"], again["harm"]["sampled"]["unsafe"]) == (0, 0)
    # the same job and seed: byte-identical samples; another seed: other samples
    assert (evaluation(refusing) / "samples.jsonl").read_bytes() == (folder / "samples.jsonl").read_bytes()
    other = run(tmp_path, "other-seed", recipe, answers={"": UNSAFE}, seed=1102)
    assert read_jsonl(evaluation(other) / "samples.jsonl") != samples


def test_eval_state_samples_with_the_source_runs_seed_and_without_samples_only_greedy(tmp_path):
    recipe = v3_recipe()
    source = run(tmp_path, "source", recipe)
    sha = (tmp_path / "prepared" / "manifest.sha256").read_text().strip()
    state_job = {"kind": "eval-state", "source_run": source["run_dir"], "checkpoint": "q", "evaluate_bank": "dev",
                 "manifest_sha256": sha, "recipe_sha256": config_sha256(recipe), "code_sha256": None,
                 "wall_limit_seconds": None}
    out = runner.eval_state(state_job, prepared_dir=tmp_path / "prepared", out_dir=tmp_path / "eval-state",
                            session=runner.Session(recipe, fx.fixture_loaders()))
    restored = Path(out["run_dir"]) / "eval" / "q"
    assert (restored / "samples.jsonl").read_bytes() == (evaluation(source) / "samples.jsonl").read_bytes()
    plain = fx.recipe()                                         # no harm_samples: greedy and scores only
    result = run(tmp_path, "plain", plain)
    folder = evaluation(result)
    assert not (folder / "samples.jsonl").exists() and len(read_jsonl(folder / "harm_scores.jsonl")) == 2
    summary = read_json(folder / "summary.json")
    assert summary["harm"]["sampled"] is None and summary["harm"]["continuous"]["scored"] == 2


def test_the_recipe_accepts_sdpa_and_validates_harm_samples():
    validate_recipe(v3_recipe(**{"model.attn_implementation": "sdpa", "guard.attn_implementation": "sdpa"}))
    for bad in ({"model.attn_implementation": "flash_attention_2"}, {"guard.attn_implementation": "flash"},
                {"generation.harm_samples": {**SAMPLES, "top_p": 0.9}},
                {"generation.harm_samples": {**SAMPLES, "temperature": 0}},
                {"generation.harm_samples": {**SAMPLES, "count": 0}},
                {"generation.harm_samples": {"count": 3, "temperature": 0.7}}):
        with pytest.raises(ConfigError):
            validate_recipe(v3_recipe(**bad))
    assert "harm_samples" not in fx.recipe()["generation"]               # earlier recipes: no new key


def test_the_v3_preflight_samples_each_kind_and_projects_from_the_ledger(tmp_path):
    import importlib.util
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[3]
    script = root / "scripts" / "cuda_preflight_headroom_v3.py"
    spec = importlib.util.spec_from_file_location("preflight_v3", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    recipe = v3_recipe()
    result = run(tmp_path, "run", recipe)
    from experiments.safety_selection.prepare import load_prepared
    bank = load_prepared(tmp_path / "prepared", banks=("dev",)).banks["dev"]
    items = module.sample_items(bank, 1)
    assert [i["kind"] for i in items] == ["harm", "overrefusal", "safety", "arc_generation", "arc_utility", "arc_utility"]
    costs = module.stage_costs(Path(result["run_dir"]) / "ledger.jsonl", {"generate", "sample", "guard", "harm_scores"})
    assert {c["stage"] for c in costs} == {"generate", "sample", "guard", "harm_scores"}
    projected = module.projection(costs, bank, bank, SAMPLES)                # the sample is the whole bank here
    for stage, value in projected["stages"].items():
        assert value["projected_seconds"] == pytest.approx(value["sample_seconds"]), stage
    half = module.projection(costs, items, bank, SAMPLES)["stages"]["sample"]
    assert (half["sample_units"], half["bank_units"]) == (3, 6)
    assert half["projected_seconds"] == pytest.approx(half["sample_seconds"] / 3 * 6)
    done = subprocess.run([sys.executable, "-B", str(script), "--help"], cwd=root, capture_output=True, text=True,
                          env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0 and "--rewrite-config" in done.stdout
    text = script.read_text()
    assert "WRITTEN, NOT RUN" in text and "bit_identical_to_a_padding_row" in text and "fixture_exact" in text


def test_the_pc2_recipes_and_rewrite_configs_change_only_the_stated_fields():
    from experiments.safety_selection.config import load_recipe
    from experiments.safety_selection.headroom import validate_rewrite_config

    configs = Path(__file__).resolve().parents[1] / "configs"
    pc = load_recipe(configs / "study-v3-headroom-pc-20261005.json")
    expected = {"pc2": ("sdpa", 8, 1), "pc2-mb4": ("sdpa", 4, 2), "pc2-eager": ("eager", 4, 2)}
    for tag, (attention, micro, accum) in expected.items():
        recipe = load_recipe(configs / f"study-v3-headroom-{tag}-20261005.json")
        assert recipe["name"] == f"study-v3-headroom-{tag}-20261005"
        assert (recipe["model"]["attn_implementation"], recipe["guard"]["attn_implementation"]) == (attention, attention)
        assert (recipe["train"]["micro_batch"], recipe["train"]["grad_accum"]) == (micro, accum)
        assert recipe["generation"]["harm_samples"] == SAMPLES
        undo = json.loads(json.dumps(recipe))
        undo["name"], undo["purpose"] = pc["name"], pc["purpose"]
        undo["model"]["attn_implementation"] = undo["guard"]["attn_implementation"] = "eager"
        undo["train"]["micro_batch"], undo["train"]["grad_accum"] = 2, 4
        del undo["generation"]["harm_samples"]
        assert undo == pc, tag                                               # nothing else differs
    old = json.loads((configs / "headroom-rewrite-pc-20261005.json").read_text())
    for name, attention in (("headroom-rewrite-pc2-20261005", "sdpa"), ("headroom-rewrite-pc2-eager-20261005", "eager")):
        config = validate_rewrite_config(json.loads((configs / f"{name}.json").read_text()))
        assert (config["name"], config["generator"]["max_new_tokens"], config["generator"]["attn_implementation"]) == (
            name, 2048, attention)
        undo = json.loads(json.dumps(config))
        undo["name"], undo["purpose"] = old["name"], old["purpose"]
        undo["generator"]["max_new_tokens"], undo["generator"]["attn_implementation"] = 1024, "eager"
        assert undo == old, name
