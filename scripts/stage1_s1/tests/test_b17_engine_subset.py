"""B17's first question (RS:107, "UNVERIFIED whether the engine can evaluate a prompt subset"), answered on engine X
with ENGINEERING FIXTURES. These tests read the engine; they change nothing in it.

1. A job cannot name a subset: run-one and eval-state take a fixed key set, and evaluate_bank is null, dev, selector
   or hidden. A recipe cannot either: the generation section has a fixed key set.
2. ``runner.evaluate_checkpoint`` takes any item list, but on a list of only the harm and over-refusal items it still
   makes greedy answers to the harm prompts, ``harm_samples.count`` samples per harm prompt, harm label scores, and an
   evaluation record with outcome summaries in records.jsonl. With a "lean recipe" (count 1) it still makes the greedy
   harm answers and the harm scores. So neither a subset bank file nor a lean recipe gives C-lean (LW-15 (a)).
3. The engine's parts that the lean job uses exist on engine X with the behaviour the job relies on.
So B17 needs no engine change: it composes C-lean from those parts (lean_eval_job.py)."""

from __future__ import annotations

import json

import pytest

import b17_support as bs

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import code_identity, ids_sha256  # noqa: E402
from experiments.safety_selection.config import ConfigError, validate_recipe  # noqa: E402
from experiments.safety_selection.jobs import JOB_KEYS, JobError, validate_job  # noqa: E402
from experiments.safety_selection.ledger import RunLedger  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402

lej = bs.lej


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    return bs.prepared_dirs(tmp_path_factory.mktemp("b17-engine"))


def test_a_job_cannot_name_a_prompt_subset(tmp_path, prepared):
    assert JOB_KEYS["run-one"] == {"kind", "manifest_sha256", "recipe_sha256", "code_sha256", "wall_limit_seconds",
                                   "split", "arm", "seed", "role", "target_checkpoint", "evaluate_bank",
                                   "resume_from", "replicate_of"}
    assert JOB_KEYS["eval-state"] == {"kind", "manifest_sha256", "recipe_sha256", "code_sha256", "wall_limit_seconds",
                                      "source_run", "checkpoint", "evaluate_bank"}
    job = bs.write_job(tmp_path / "job.json", prepared[0], bs.recipe())
    with pytest.raises(JobError):
        validate_job({**job, "prompt_subset": ["harm", "overrefusal"]})
    for bank in ("dev-lean", "subset-" + "0" * 64, "harm"):
        with pytest.raises(JobError):
            validate_job({**job, "evaluate_bank": bank})
    for bank in (None, "dev", "selector", "hidden"):
        validate_job({**job, "evaluate_bank": bank})


def test_a_recipe_cannot_name_a_prompt_subset():
    rec = bs.recipe()
    validate_recipe(rec)
    for key, value in (("prompt_subset", ["harm"]), ("kinds", ["harm", "overrefusal"]), ("greedy_kinds", [])):
        with pytest.raises(ConfigError):
            validate_recipe(bs.recipe(**{f"generation.{key}": value}))
    with pytest.raises(ConfigError):                                   # samples can be changed, not greedy harm
        validate_recipe(bs.recipe(**{"generation.harm_samples.count": 0}))


def engine_evaluation(base, prepared, rec: dict) -> tuple:
    """runner.evaluate_checkpoint on only the harm and over-refusal items of the dev bank (the seeded adapter)."""
    prep = load_prepared(prepared[0], prepared[1], banks=("dev",))
    items = [i for i in prep.banks["dev"] if i["kind"] in ("harm", "overrefusal")]
    session = bs.session(rec)
    unit = base / "unit"
    unit.mkdir(parents=True)
    ledger = RunLedger(unit)
    policy = session.policy(ledger, unit)
    queries, query_sha = runner._query_examples(policy, prep, rec)
    summary = runner.evaluate_checkpoint(session, policy, None, items, queries, query_sha, ledger, unit / "eval",
                                         unit, "init", bs.SEED)
    return prep, items, unit, summary


@pytest.mark.parametrize("count", [3, 1])
def test_evaluate_checkpoint_on_the_c_lean_items_is_not_c_lean(tmp_path, prepared, count):
    rec = bs.recipe(**{"generation.harm_samples.count": count})
    prep, items, unit, summary = engine_evaluation(tmp_path, prepared, rec)
    harm = [i["prompt_id"] for i in items if i["kind"] == "harm"]
    generations = bs.read_jsonl(unit / "eval" / "generations.jsonl")
    assert sorted(g["prompt_id"] for g in generations if g["kind"] == "harm") == sorted(harm)   # greedy harm answers
    samples = bs.read_jsonl(unit / "eval" / "samples.jsonl")
    assert len(samples) == count * len(harm)
    scores = bs.read_jsonl(unit / "eval" / "harm_scores.jsonl")
    assert len(scores) == len(harm) * (1 + count)                                              # harm label scores
    records = bs.read_jsonl(unit / "records.jsonl")
    evaluation = [r for r in records if r["kind"] == "evaluation"]
    assert len(evaluation) == 1 and {"harm", "overrefusal"} <= set(evaluation[0])            # outcomes in records
    assert "harm" in summary and "overrefusal" in summary
    stages = [r["stage"] for r in bs.read_jsonl(unit / "ledger.jsonl")]
    assert "harm_scores" in stages and "arc_utility" in stages
    assert json.loads((unit / "eval" / "summary.json").read_bytes())["harm"]["prompts"] == len(harm)


def test_the_parts_the_lean_job_uses_exist_on_engine_x(tmp_path, prepared):
    assert code_identity()["sha256"] == lej.load_lean_settings()[0]["engine_x"]
    for name in ("query_losses", "greedy_generate", "sample_generate", "preserved_rng", "rng_digest",
                 "lora_fingerprint", "STOP_CAP", "STATE", "QUERY_LOSS_DEFINITION"):
        assert name in en.__all__, name
    assert runner.GENERATION_KINDS == ("safety", "arc_generation", "harm", "overrefusal")
    assert runner.sample_seed(1101, "p", 0) == runner.derive_seed(1101, "harm-sample", "p", 0)
    rec = bs.recipe()
    prep = load_prepared(prepared[0], prepared[1], banks=("dev",))
    session = bs.session(rec)
    ledger = RunLedger(tmp_path)
    policy = session.policy(ledger, tmp_path)
    for item in prep.banks["dev"]:
        if item["kind"] in ("harm", "overrefusal"):
            ids = runner._prompt_ids(policy.codec, item, rec["model"]["max_prompt_tokens"])
            assert ids_sha256(ids) == item["token_sha256"]
    queries, query_sha = runner._query_examples(policy, prep, rec)
    assert [q.row_id for q in queries] == [q["query_id"] for q in prep.query_rows]
    assert query_sha == runner._query_bank_sha256(prep)
    pin = runner.guard_pin(rec)
    assert set(pin) == {"repo_id", "revision", "present", "files"}


def test_sampled_answers_do_not_depend_on_the_other_rows_of_a_float32_batch(tmp_path, prepared):
    """The sampling rule gives each row its own generator (engine.SAMPLING_RULE). On the float32 CPU fixture, one
    prompt's sample is the same alone and inside a batch with other prompts. (On the pod, bfloat16 kernels may make a
    batch-shape difference: UNVERIFIED there, and it does not change the cost.)"""
    rec = bs.recipe()
    prep = load_prepared(prepared[0], prepared[1], banks=("dev",))
    policy = bs.session(rec).policy(RunLedger(tmp_path), tmp_path)
    items = [i for i in prep.banks["dev"] if i["kind"] in ("harm", "overrefusal")]
    prompts = [runner._prompt_ids(policy.codec, i, rec["model"]["max_prompt_tokens"]) for i in items]
    seeds = [runner.sample_seed(bs.SEED, i["prompt_id"], 0) for i in items]
    common = dict(temperature=0.7, max_new_tokens=5, stop_ids=policy.codec.stop_ids, pad_id=policy.codec.pad_id,
                  device="cpu")
    together = en.sample_generate(policy.model, prompts, seeds, batch_size=len(prompts), **common)
    alone = [en.sample_generate(policy.model, [p], [s], batch_size=1, **common)[0] for p, s in zip(prompts, seeds)]
    assert [g.output_ids for g in together] == [g.output_ids for g in alone]
