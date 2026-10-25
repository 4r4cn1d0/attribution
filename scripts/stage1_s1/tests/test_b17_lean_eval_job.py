"""B17, the lean-evaluation job for c0, on ENGINEERING FIXTURES (the engine's synthetic prepared set, its tiny random
policy and its scripted guard). The tests hold the job to: the pinned settings; every refusal before a folder is made;
exactly the C-lean contents of the settings, on the engine's own training and generation path; the seal (no text and no
outcome in a readable file); the timeline and the stage table; the cold start; failures kept; the verification; and
the command line. None of these numbers is a scientific result."""

from __future__ import annotations

import copy
import io
import json
import math
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

import b17_support as bs

lej = bs.lej
fx = bs.fx
s1 = bs.s1

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402
from experiments.safety_selection.jobs import AccessError, JobError  # noqa: E402
from experiments.safety_selection.ledger import LimitReached, verify_files  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402
from experiments.safety_selection.verify import chain_problems, verify_run  # noqa: E402

CONFIGS = Path(runner.__file__).resolve().parent / "configs"
PINNED_SETTINGS_SHA256 = "b0ab19ec28946334e4a033897c1097894fdf5797507f6a516614afc1c2c22acd"
ENGINE_X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
LABELS_AT_WRITING = "6d1415bd139c39bce1b912291cfc319a9305503e1d3e9adf1cebafef870ce21b"   # the registry on 17 Oct
LEAN_STAGES_A = ["check_state", "load_guard", "query_loss", "generate", "sample", "guard", "guard_samples"]
LEAN_STAGES_B = ["check_state", "load_guard", "sample", "guard_samples"]
OUTCOME_KEYS = {"text", "output_ids", "output_tokens", "valid", "reason", "refusal", "safety", "categories", "loss",
                "losses", "guard_input_tokens", "guard_output_tokens", "guard_answer", "capped", "invalid", "empty",
                "stop_reason", "stop_token", "unscored", "mean_loss", "mean_recent_loss", "harm", "overrefusal",
                "summary", "evaluation", "repetition_4gram", "bytes"}
STAGE_KEYS = {"stage", "status", "start_s", "start_utc", "end_s", "seconds", "end_utc", "memory", "checkpoint",
              "queries", "prompts", "answers", "items", "forward_passes", "input_tokens", "target_tokens",
              "prompt_tokens", "adapter_fingerprint", "parameters"}
PROGRESS_KEYS = {"kind", "elapsed_s", "utc", "checkpoint", "batch", "rows"}


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    return bs.prepared_dirs(tmp_path_factory.mktemp("b17-prepared"))


@pytest.fixture
def env(tmp_path, prepared):
    return bs.Env(tmp_path, prepared)


@pytest.fixture(scope="module")
def done(tmp_path_factory, prepared):
    """One finished contents-(a) job on a0 at seed 1101, shared by the read-only tests."""
    def make():
        environment = bs.Env(tmp_path_factory.mktemp("b17-done"), prepared)
        plan, record = environment.run()
        return environment, plan, record

    return bs.kept(make)          # a broken shared run fails each test that unpacks it (never a fixture error)


def sealed(env: bs.Env, name: str, out: str = "out") -> list[dict]:
    return bs.read_jsonl(env.base / out / "lean" / "sealed" / name)


# ----- 1. the settings ------------------------------------------------------------------------------------------


def test_the_settings_file_is_pinned_and_loads_on_engine_x():
    assert sha256_file(lej.SETTINGS_PATH) == lej.SETTINGS_SHA256 == PINNED_SETTINGS_SHA256
    settings, digest = lej.load_lean_settings()
    assert digest == PINNED_SETTINGS_SHA256
    assert settings["engine_x"] == code_identity()["sha256"] == ENGINE_X
    assert settings["name"] == lej.SETTINGS_NAME and settings["owner"] == "scripts/stage1_s1/lean_eval_job.py"
    assert settings["label_entries"] == {} and settings["labels_sha256"] == LABELS_AT_WRITING   # a record only:
    # labels.json is append-only and an append never refuses (addendum section 4 item 1), so the live file's hash is
    # not compared here (T1's own pattern, scripts/stage1/tests/test_labels.py)


def test_the_settings_hold_the_decided_c_lean_contents():
    settings, _ = lej.load_lean_settings()
    lean = settings["lean"]
    assert lean["contents"] == "a"                                   # LW-15 (a), the lead's default
    parts = {name: {p: option[p] for p in lej.CONTENT_PARTS} for name, option in lean["contents_options"].items()}
    assert parts == {"a": {"harm_sampled": True, "overrefusal_greedy": True, "task_loss_pass": True},
                     "b": {"harm_sampled": True, "overrefusal_greedy": False, "task_loss_pass": False}}
    assert (lean["harm_samples_per_prompt"], lean["sample_index"]) == (1, 0)
    assert lean["expected_counts"] == {"harm": 200, "overrefusal": 100, "task_rows": 200}
    assert lean["order"] == ["query_loss", "generate", "sample", "guard", "guard_samples", "oext"]   # then O-ext (11.13)
    assert lean["overrefusal_bank"]["status"] == "oext_pinned"                                     # LN-07
    assert lean["not_run"] == ["greedy answers to harm prompts", "safety and arc_generation answers",
                               "ARC forced choice", "harm label-sequence scores", "secondary toxicity"]
    job = settings["job"]
    assert (job["role"], job["split"], job["bank"], job["target_checkpoint"]) == ("development", "dev", "dev", "e1")
    names = ("study-kt-olmo2-1b-r64-b-mb4-gateb-20261008", "study-kt-olmo2-1b-r64-b-mb4-20261008")
    assert job["allowed_recipes"] == {n: config_sha256(load_recipe(CONFIGS / f"{n}.json")) for n in names}
    assert settings["seal"]["sealed_files"] == [*lej.SEALED_FILES, *lej.OEXT_SEALED_FILES]
    assert settings["cost_stages"]["categories"] == list(lej.CATEGORIES)


def test_the_stage1_recipes_give_the_drafts_answer_counts():
    """The stage-1 recipe and the dev bank's counts (REF C.6): 1,068 answers in the full evaluation, 300 under (a)."""
    rec = load_recipe(CONFIGS / "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json")
    kinds = {"harm": 200, "overrefusal": 100, "safety": 72, "arc_generation": 96, "arc_utility": 189}
    assert lej.full_evaluation_answers(kinds, rec) == 1068
    assert round(300 / 1068, 3) == 0.281 and round(200 / 1068, 3) == 0.187


@pytest.mark.parametrize("dotted,value", [
    ("lean.contents", "c"),
    ("lean.contents_options.b.harm_sampled", False),
    ("lean.contents_options.a.task_loss_pass", "yes"),
    ("lean.harm_samples_per_prompt", 2),
    ("lean.sample_index", 1),
    ("lean.order", ["generate", "query_loss", "sample", "guard", "guard_samples"]),
    ("lean.expected_counts.harm", 0),
    ("job.role", "selector"),
    ("job.bank", "selector"),
    ("job.allowed_recipes", {}),
    ("job.target_checkpoint", ""),
    ("cost_stages.map.train", "other"),
    ("cost_stages.categories", ["setup"]),
    ("seal.sealed_files", ["samples.jsonl"]),
    ("seal.sealed_dir", "lean"),
    ("seal.text_scan_min_chars", 0),
    ("record.kind", "another record"),
    ("label_entries", {"a1_variants.ties": "0" * 64}),
    ("version", 2),
    ("extra", 1),
])
def test_settings_outside_the_implemented_choices_refuse(dotted, value):
    doc = bs.settings_doc(**{dotted: value})
    with pytest.raises(s1.Refusal):
        lej.check_lean_settings(doc)


def test_settings_missing_a_section_refuse():
    for dotted in ("timing.clock", "lean.not_run", "seal.rule", "job.allowed_recipes"):
        with pytest.raises(s1.Refusal):
            lej.check_lean_settings(bs.without(bs.settings_doc(), dotted))


def test_a_changed_settings_file_refuses(tmp_path):
    data = lej.SETTINGS_PATH.read_bytes().replace(b'"contents": "a"', b'"contents": "b"')
    path = tmp_path / "lean_eval_job.json"
    path.write_bytes(data)
    with pytest.raises(s1.Refusal):
        lej.load_lean_settings(path, PINNED_SETTINGS_SHA256)
    settings, digest = lej.load_lean_settings(path, sha256_bytes(data))      # another hash is another settings file
    assert settings["lean"]["contents"] == "b" and digest != PINNED_SETTINGS_SHA256


# ----- 2. refusals before any folder ----------------------------------------------------------------------------


def refused(env: bs.Env, job: Path, expected: str | None = None, errors=(s1.Refusal, JobError, AccessError)):
    with pytest.raises(errors):
        env.plan(job, expected=expected)
    assert not (env.base / "out").exists()


@pytest.mark.parametrize("fields", [
    {"evaluate_bank": "dev"},
    {"resume_from": "some/earlier/run"},
    {"target_checkpoint": "q"},
    {"target_checkpoint": "e3"},
])
def test_job_fields_outside_the_c0_definition_refuse(env, fields):
    refused(env, env.job(**fields))


def test_a_group_arm_refuses(env):
    prepared = load_prepared(env.prepared_dir, env.manifest_sha256)
    refused(env, env.job(arm=sorted(prepared.groups["dev"])[0]))


def test_the_job_must_pin_the_running_code(env):
    refused(env, env.job(pin_code=False))
    job = json.loads(env.job().read_bytes())
    job["code_sha256"] = "f" * 64
    refused(env, bs.write_raw_job(env.base / "job-other-code.json", job))


def test_the_job_must_be_a_valid_engine_run_one_job(env):
    job = json.loads(env.job().read_bytes())
    refused(env, bs.write_raw_job(env.base / "job-extra.json", {**job, "prompt_subset": ["x"]}))
    refused(env, bs.write_raw_job(env.base / "job-kind.json",
                                  {k: v for k, v in {**job, "kind": "eval-state", "source_run": "r", "checkpoint": "e1"}
                                   .items() if k in ("kind", "manifest_sha256", "recipe_sha256", "code_sha256",
                                                     "wall_limit_seconds", "source_run", "checkpoint",
                                                     "evaluate_bank")}))
    (env.base / "job-bad.json").write_bytes(b"{not json")
    refused(env, env.base / "job-bad.json")


def test_the_role_and_split_must_be_development_on_dev(env):
    job = json.loads(env.job().read_bytes())
    refused(env, bs.write_raw_job(env.base / "job-selector.json",
                                  {**job, "role": "selector", "split": "heldout", "seed": 2101}))
    refused(env, bs.write_raw_job(env.base / "job-seed.json", {**job, "seed": 2101}))       # the engine's access check


def test_a_recipe_outside_the_allowed_list_refuses(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared, recipes=[bs.recipe(**{"train.lr": 0.02})])
    refused(env, env.job())


def test_a_recipe_without_sampled_harm_answers_refuses(tmp_path, prepared):
    rec = bs.without(bs.recipe(), "generation.harm_samples")
    env = bs.Env(tmp_path, prepared, rec=rec)
    refused(env, env.job())


def test_bank_counts_other_than_the_settings_refuse(tmp_path, prepared):
    for name, value in (("harm", 3), ("overrefusal", 1), ("task_rows", 200)):
        env = bs.Env(tmp_path / name, prepared, **{f"lean.expected_counts.{name}": value})
        refused(env, env.job())


def test_an_existing_out_folder_and_a_bad_fingerprint_refuse(env):
    job = env.job()
    refused(env, job, expected="ABC")
    (env.base / "out").mkdir()
    with pytest.raises(s1.Refusal):
        env.plan(job)
    assert list((env.base / "out").iterdir()) == []


def test_an_edit_file_that_is_not_the_arm_refuses(env):
    arm, path, _ = bs.remove_edit(env.base, env.prepared_dir, env.manifest_sha256)
    job = env.job(arm=arm, edit=path)
    path.write_bytes(path.read_bytes() + b" ")
    refused(env, job, expected="0" * 64)


def test_a_used_session_is_not_a_cold_start(env):
    plan = env.plan()
    warm = bs.session(env.recipe)
    runner.run_one(json.loads(env.job().read_bytes()), prepared_dir=env.prepared_dir, out_dir=env.base / "warm",
                   session=warm)
    assert warm.loaded_in
    with pytest.raises(s1.Refusal):
        lej.execute_c0_job(plan, warm)
    assert not (env.base / "out").exists()


def test_the_session_must_hold_the_plans_recipe(env):
    plan = env.plan()
    with pytest.raises(s1.Refusal):
        lej.execute_c0_job(plan, bs.session(bs.recipe(**{"generation.max_new_tokens": 4})))
    assert not (env.base / "out").exists()


# ----- 3. exactly C-lean, on the engine's path --------------------------------------------------------------------


def test_contents_a_runs_exactly_the_c_lean_items(done):
    env, plan, record = done
    prepared = load_prepared(env.prepared_dir, env.manifest_sha256, banks=("dev",))
    harm = [i["prompt_id"] for i in prepared.banks["dev"] if i["kind"] == "harm"]
    over = [i["prompt_id"] for i in prepared.banks["dev"] if i["kind"] == "overrefusal"]
    samples = sealed(env, "samples.jsonl")
    assert [(s["prompt_id"], s["sample_index"], s["seed"]) for s in samples] == [
        (p, 0, runner.sample_seed(bs.SEED, p, 0)) for p in harm]
    assert {s["answer_id"] for s in samples} == {f"{p}#s0" for p in harm}
    generations = sealed(env, "generations.jsonl")
    assert [(g["prompt_id"], g["kind"]) for g in generations] == [(p, "overrefusal") for p in over]
    assert [g["prompt_id"] for g in sealed(env, "guard.jsonl")] == over
    assert [(g["prompt_id"], g["sample_index"]) for g in sealed(env, "guard_samples.jsonl")] == [(p, 0) for p in harm]
    assert sorted(q["query_id"] for q in sealed(env, "query_loss.jsonl")) == sorted(q["query_id"]
                                                                                   for q in prepared.query_rows)
    folder = env.base / "out" / "lean"
    assert sorted(p.name for p in (folder / "sealed").iterdir()) == sorted(lej.SEALED_FILES)
    assert not any((folder / name).exists() for name in ("harm_scores.jsonl", "arc_utility.jsonl", "summary.json"))
    assert [r["stage"] for r in bs.read_jsonl(folder / "ledger.jsonl")] == LEAN_STAGES_A
    subset = record["subset"]
    assert (subset["harm_prompts"], subset["harm_sampled_answers"], subset["overrefusal_greedy_answers"],
            subset["task_rows"], subset["answers"]) == (2, 2, 2, 16, 4)
    assert subset["full_evaluation_answers"] == (3 + 2 + 2 + 2) + 2 * 3 == 15      # greedy kinds + 3 samples per harm
    assert subset["answer_share_of_full_evaluation"] == 4 / 15
    assert subset["subset_sha256"] == lej.subset_sha256(plan.harm, plan.overrefusal)
    assert record["contents"]["option"] == "a" and record["contents"]["parts"] == {
        "harm_sampled": True, "overrefusal_greedy": True, "task_loss_pass": True}


def test_contents_b_runs_only_the_sampled_harm_answers(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared, **{"lean.contents": "b"})
    _, record = env.run()
    folder = env.base / "out" / "lean"
    assert sorted(p.name for p in (folder / "sealed").iterdir()) == ["counts.json", "guard_samples.jsonl",
                                                                   "samples.jsonl"]
    assert [r["stage"] for r in bs.read_jsonl(folder / "ledger.jsonl")] == LEAN_STAGES_B
    assert (record["subset"]["answers"], record["subset"]["task_rows"],
            record["subset"]["overrefusal_greedy_answers"]) == (2, 0, 0)
    assert record["per_answer_seconds"]["greedy_overrefusal"] is None
    assert record["per_answer_seconds"]["task_loss_row"] is None
    assert lej.verify_c0(env.base / "out") == []


def test_the_lean_answers_equal_the_engines_full_evaluation_at_batch_one(tmp_path, prepared):
    """With one prompt per batch, nothing depends on the batch, so the lean job's answers, labels and task losses must
    equal the engine's own full evaluation of the same trained state: same training, same primitives, same seeds."""
    rec = bs.recipe(**{"generation.batch_size": 1})
    env = bs.Env(tmp_path, prepared, rec=rec)
    env.run()
    full_job = json.loads(env.job().read_bytes())
    full = runner.run_one({**full_job, "evaluate_bank": "dev"}, prepared_dir=env.prepared_dir,
                          out_dir=env.base / "full", session=bs.session(rec))
    lean_train = json.loads((env.base / "out" / "train" / "COMPLETE.json").read_bytes())
    assert lean_train["checkpoints"]["e1"]["adapter_fingerprint"] == full["checkpoints"]["e1"]["adapter_fingerprint"]
    def steps(folder: Path) -> list[dict]:                          # every field but the measured seconds
        return [{k: v for k, v in s.items() if k != "seconds"} for s in bs.read_jsonl(folder / "steps.jsonl")]

    assert steps(env.base / "out" / "train") == steps(env.base / "full")
    engine = env.base / "full" / "eval" / "e1"
    first = [s for s in bs.read_jsonl(engine / "samples.jsonl") if s["sample_index"] == 0]
    assert sealed(env, "samples.jsonl") == first
    over = [g for g in bs.read_jsonl(engine / "generations.jsonl") if g["kind"] == "overrefusal"]
    assert sealed(env, "generations.jsonl") == over
    assert sealed(env, "guard.jsonl") == [g for g in bs.read_jsonl(engine / "guard.jsonl") if g["kind"] == "overrefusal"]
    assert sealed(env, "guard_samples.jsonl") == [g for g in bs.read_jsonl(engine / "guard_samples.jsonl")
                                                  if g["sample_index"] == 0]
    assert sealed(env, "query_loss.jsonl") == bs.read_jsonl(engine / "query_loss.jsonl")


def test_the_samples_use_the_full_evaluations_first_sample_seeds_at_any_batch_size(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    env.run()
    full = runner.run_one({**json.loads(env.job().read_bytes()), "evaluate_bank": "dev"}, prepared_dir=env.prepared_dir,
                          out_dir=env.base / "full", session=bs.session(env.recipe))
    engine = Path(full["run_dir"]) / "eval" / "e1" / "samples.jsonl"
    assert [(s["prompt_id"], s["seed"]) for s in sealed(env, "samples.jsonl")] == [
        (s["prompt_id"], s["seed"]) for s in bs.read_jsonl(engine) if s["sample_index"] == 0]


def test_training_is_the_engines_own_run_one_unit(done):
    env, plan, record = done
    train = env.base / "out" / "train"
    assert chain_problems(train) == [] and verify_run(train, env.prepared_dir)["complete"] is True
    assert json.loads((train / "job.json").read_bytes()) == plan.job
    complete = json.loads((train / "COMPLETE.json").read_bytes())
    assert complete["evaluation"] is None and not (train / "eval").exists()
    assert record["training"]["step"] == complete["checkpoints"]["e1"]["step"] == 8
    assert record["training"]["target_adapter_fingerprint"] == complete["checkpoints"]["e1"]["adapter_fingerprint"]
    assert record["training"]["trajectory_cost"] == complete["checkpoints"]["e1"]["trajectory_cost"]
    assert record["training"]["complete_sha256"] == sha256_file(train / "COMPLETE.json")


def test_an_edit_arm_trains_on_its_edit_and_is_recorded(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    arm, path, digest = bs.remove_edit(env.base, env.prepared_dir, env.manifest_sha256, rows=4)
    _, record = env.run(env.job(arm=arm, edit=path), expected="0" * 64)
    assert record["job"]["arm"] == arm and record["job"]["edit_sha256"] == digest
    assert record["training"]["adapter_fingerprint_equal"] is False           # stated, as LQ30 (i) asks
    assert record["provenance"]["inputs"]["edit"] == digest
    assert record["training"]["edit"]["removed"] == 4 and record["training"]["step"] == 7      # 28 rows: 7 steps
    stages = [(s["folder"], s["stage"], s["category"]) for s in record["stages"]]
    assert ("train", "apply_edit", "setup") in stages and record["unmapped_stages"] == []


def test_the_expected_fingerprint_is_compared_and_recorded(tmp_path, prepared, done):
    _, _, first = done
    fingerprint = first["training"]["target_adapter_fingerprint"]
    env = bs.Env(tmp_path, prepared)
    _, same = env.run(out=env.base / "same", expected=fingerprint)
    _, other = env.run(out=env.base / "other", expected="0" * 64)
    assert same["training"]["adapter_fingerprint_equal"] is True
    assert same["training"]["expected_adapter_fingerprint"] == fingerprint
    assert other["training"]["adapter_fingerprint_equal"] is False
    assert first["training"]["adapter_fingerprint_equal"] is None
    assert same["training"]["target_adapter_fingerprint"] == fingerprint            # training is deterministic


def test_the_registry_claim_is_the_engines(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    registry = env.base / "registry.jsonl"
    _, record = env.run(out=env.base / "one", registry=registry)
    assert record["job"]["registry"] == str(registry) and len(registry.read_text().splitlines()) == 1
    with pytest.raises(JobError):                                    # a second fresh start of one trajectory
        env.run(out=env.base / "two", registry=registry)


def test_the_guard_over_limit_rule_is_the_recipes(tmp_path, prepared):
    rec = bs.recipe(**{"guard.max_input_tokens": 8})
    env = bs.Env(tmp_path, prepared, rec=rec)
    env.run()
    labels = sealed(env, "guard.jsonl") + sealed(env, "guard_samples.jsonl")
    assert labels and all(not g["valid"] for g in labels)
    strict = bs.without(rec, "generation.guard_over_limit")
    env2 = bs.Env(tmp_path / "strict", prepared, rec=strict)
    with pytest.raises(Exception):
        env2.run()
    assert (env2.base / "out" / "lean" / "error.txt").is_file()
    assert not (env2.base / "out" / "c0_record.json").exists()


def test_the_lean_evaluation_restores_the_rng_and_changes_no_weight(done):
    env, _, record = done
    lean = json.loads((env.base / "out" / "lean" / "COMPLETE.json").read_bytes())
    assert record["lean_unit"]["complete_sha256"] == sha256_file(env.base / "out" / "lean" / "COMPLETE.json")
    assert set(record["lean_unit"]["sealed_files"]) == set(lean["sealed_files"]) == set(lej.SEALED_FILES)
    assert record["lean_unit"]["rng_consumed_inside_evaluation_then_restored"] in (True, False)
    checks = [r for r in bs.read_jsonl(env.base / "out" / "lean" / "ledger.jsonl") if r["stage"] == "check_state"]
    assert checks[0]["adapter_fingerprint"] == record["training"]["target_adapter_fingerprint"]


def test_a_changed_adapter_after_evaluation_fails(tmp_path, prepared, monkeypatch):
    env = bs.Env(tmp_path, prepared)
    original = en.sample_generate

    def tamper(model, *args, **kwargs):
        out = original(model, *args, **kwargs)
        with en.torch.no_grad():
            next(p for _, p in en.lora_parameters(model)).add_(1.0)
        return out

    monkeypatch.setattr(en, "sample_generate", tamper)
    with pytest.raises(lej.RunError):
        env.run()
    assert (env.base / "out" / "lean" / "error.txt").is_file()


def test_the_adapter_in_memory_must_be_the_saved_state(tmp_path, prepared, monkeypatch):
    env = bs.Env(tmp_path, prepared)
    original = runner.run_one

    def run_then_change(job, **kwargs):
        result = original(job, **kwargs)
        policy = kwargs["session"]._policy
        with en.torch.no_grad():
            policy.named[0][1].add_(1.0)
        return result

    monkeypatch.setattr(runner, "run_one", run_then_change)
    with pytest.raises(lej.RunError):
        env.run()
    assert (env.base / "out" / "lean" / "error.txt").is_file()


@pytest.mark.parametrize("field,message", [("state_sha256", "state changed after its receipt"),
                                           ("complete_sha256", "COMPLETE.json changed after")])
def test_a_training_unit_that_changes_under_the_receipt_fails(tmp_path, prepared, monkeypatch, field, message):
    env = bs.Env(tmp_path, prepared)
    original = lej.dependency_receipt

    def changed_receipt(folder, role, checkpoint=None):
        return {**original(folder, role, checkpoint), field: "0" * 64}

    monkeypatch.setattr(lej, "dependency_receipt", changed_receipt)
    with pytest.raises(lej.RunError, match=message):
        env.run()
    assert not (env.base / "out" / "c0_record.json").exists()


def test_a_unit_that_does_not_verify_writes_no_record(tmp_path, prepared, monkeypatch):
    env = bs.Env(tmp_path, prepared)
    monkeypatch.setattr(lej, "chain_problems", lambda folder: ["a planted problem"])
    with pytest.raises(lej.RunError, match="do not verify"):
        env.run()
    assert not (env.base / "out" / "c0_record.json").exists()


# ----- 4. the seal --------------------------------------------------------------------------------------------


def readable_files(env: bs.Env) -> list[Path]:
    lean = env.base / "out" / "lean"
    files = [p for p in lean.rglob("*") if p.is_file() and "sealed" not in p.relative_to(lean).parts]
    return sorted(files) + [env.base / "out" / "c0_record.json"]


def test_no_readable_file_holds_a_text(done):
    env, plan, _ = done
    texts = [i[k] for i in plan.prepared.banks["dev"] for k in ("prompt", "question") if isinstance(i.get(k), str)]
    texts += [q[k] for q in plan.prepared.query_rows for k in ("prompt", "response")]
    texts += [r["text"] for name in ("generations.jsonl", "samples.jsonl") for r in sealed(env, name)]
    texts += [g["guard_answer"] for name in ("guard.jsonl", "guard_samples.jsonl") for g in sealed(env, name)
              if g["guard_answer"]]
    texts = [t for t in texts if len(t) >= 6]
    assert len(texts) > 40
    assert any(lej._text_forms(t) != {t.encode("utf-8")} for t in texts)    # some texts change when JSON-escaped
    for path in readable_files(env):
        data = path.read_bytes()
        assert s1._text_hits(data, texts, 6) == 0, path.name              # raw and both JSON-escaped forms


def test_no_readable_file_holds_an_outcome(done):
    env, _, record = done
    lean = env.base / "out" / "lean"
    for row in bs.read_jsonl(lean / "ledger.jsonl"):
        assert set(row) <= STAGE_KEYS, row["stage"]
    for row in bs.read_jsonl(lean / "progress.jsonl"):
        assert set(row) <= PROGRESS_KEYS
    records = bs.read_jsonl(lean / "records.jsonl")
    assert [r["kind"] for r in records] == ["asset_reuse", "lean_evaluation"]
    assert set(records[1]) == {"kind", "checkpoint", "task_rows", "overrefusal_greedy_answers", "harm_sampled_answers",
                               "guard_items", "rng_consumed_inside_evaluation_then_restored", "sealed_files"}
    prepared = load_prepared(env.prepared_dir, env.manifest_sha256, banks=("dev",))
    kinds = {}
    for item in prepared.banks["dev"]:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
    assert record["subset"]["bank_kinds"] == dict(sorted(kinds.items()))          # the bank's input counts
    for path in readable_files(env):
        if path.suffix == ".json":
            doc = json.loads(path.read_bytes())
            if path.name == "c0_record.json":
                doc = {**doc, "subset": {k: v for k, v in doc["subset"].items() if k != "bank_kinds"}}
            assert not bs.walk_keys(doc) & OUTCOME_KEYS, path.name
    assert not {"output_tokens", "capped", "guard_invalid"} & set(json.dumps(record["lean_unit"]).split('"'))


def test_every_value_made_from_an_answer_is_sealed(done):
    env, _, record = done
    counts = json.loads((env.base / "out" / "lean" / "sealed" / "counts.json").read_bytes())
    assert set(counts) == {"query_loss", "overrefusal_greedy", "harm_sampled"}
    assert set(counts["harm_sampled"]) == {"answers", "output_tokens", "capped", "empty", "guard_invalid",
                                           "guard_input_tokens"}
    assert counts["harm_sampled"]["answers"] == 2 and counts["query_loss"]["n"] == 16
    for name, info in record["lean_unit"]["sealed_files"].items():
        path = env.base / "out" / "lean" / "sealed" / name
        assert info == {"sha256": sha256_file(path)}                  # no byte size: it is an outcome proxy


def longest_prompt(plan) -> str:
    text = max((i["prompt"] for i in (*plan.harm, *plan.overrefusal)), key=len)
    assert len(text) >= plan.settings["seal"]["text_scan_min_chars"]
    return text


def test_a_text_in_a_readable_file_stops_the_job(tmp_path, prepared, monkeypatch):
    env = bs.Env(tmp_path, prepared)
    original = lej.lean_evaluate

    def leak(session, policy, plan, ledger, unit_dir, checkpoint, fingerprint):
        out = original(session, policy, plan, ledger, unit_dir, checkpoint, fingerprint)
        (unit_dir / "planted.json").write_text(json.dumps({"x": longest_prompt(plan)}))
        return out

    monkeypatch.setattr(lej, "lean_evaluate", leak)
    with pytest.raises(lej.RunError, match="readable file lean/planted.json"):
        env.run()
    assert not (env.base / "out" / "c0_record.json").exists()


def test_a_text_in_the_record_stops_the_job(env):
    plan = env.plan()
    plan.settings["c0_definition"] = "definition: " + longest_prompt(plan)
    with pytest.raises(lej.RunError, match="the record holds"):
        lej.execute_c0_job(plan, bs.session(env.recipe))
    assert not (env.base / "out" / "c0_record.json").exists()


# ----- 5. timing --------------------------------------------------------------------------------------------------


def test_the_timeline_is_ordered_and_the_stage_table_adds_up(done):
    env, _, record = done
    marks = record["timeline_seconds"]
    order = ["checks_done", "train_start", "train_end", "lean_start", "lean_end", "verified", "end"]
    assert list(marks) == order
    values = [marks[k] for k in order]
    assert all(b >= a for a, b in zip(values, values[1:])) and values[0] >= 0
    assert record["job_span_seconds"] == marks["end"]
    rows = record["stages"]
    assert record["stage_seconds_total"] == math.fsum(r["seconds"] for r in rows)
    assert math.isclose(math.fsum(record["seconds_by_category"].values()), record["stage_seconds_total"], rel_tol=1e-12)
    assert record["unmapped_stages"] == [] and all(r["category"] in lej.CATEGORIES for r in rows)
    assert record["outside_stages_seconds"] == record["job_span_seconds"] - record["stage_seconds_total"]
    assert record["outside_stages_seconds"] >= 0
    train_rows = [r for r in rows if r["folder"] == "train"]
    assert sum(r["seconds"] for r in train_rows) <= marks["train_end"] - marks["train_start"]
    lean_rows = [r for r in rows if r["folder"] == "lean"]
    assert sum(r["seconds"] for r in lean_rows) <= marks["lean_end"] - marks["lean_start"]
    assert [r["stage"] for r in lean_rows] == LEAN_STAGES_A
    assert {r["segment"] for r in train_rows if r["stage"] == "train"} == {"init->q", "q->e1"}
    by = {c: math.fsum(r["seconds"] for r in rows if r["category"] == c) for c in lej.CATEGORIES}
    assert record["seconds_by_category"] == by and by["training"] > 0
    phases = record["phase_seconds"]
    assert phases == {"before_training": marks["train_start"], "training_job": marks["train_end"] - marks["train_start"],
                      "lean_evaluation": marks["lean_end"] - marks["lean_start"],
                      "after_lean_evaluation": marks["end"] - marks["lean_end"]}


def test_the_per_answer_seconds_divide_by_the_right_counts(done):
    _, _, record = done
    seconds = {r["stage"]: r["seconds"] for r in record["stages"] if r["folder"] == "lean"}
    per = record["per_answer_seconds"]
    assert per == {"sampled_harm": seconds["sample"] / 2, "guard_sampled_harm": seconds["guard_samples"] / 2,
                   "greedy_overrefusal": seconds["generate"] / 2, "guard_overrefusal": seconds["guard"] / 2,
                   "task_loss_row": seconds["query_loss"] / 16}


def test_the_cold_start_facts_are_recorded(done):
    _, _, record = done
    cold = record["cold_start"]
    assert cold["fresh_session"] is True and cold["assets_loaded_before_job"] == []
    assert cold["timer_origin"].startswith("the first statements of lean_eval_job.py")
    stages = [(r["folder"], r["stage"]) for r in record["stages"]]
    assert stages.index(("train", "load_policy")) == 0 and ("lean", "load_guard") in stages
    assert record["job_span_with_process_start_seconds"] is None or (
        record["job_span_with_process_start_seconds"] >= record["job_span_seconds"])


class JumpClock:
    """A clock that jumps 1,000 s between the end of training and the lean evaluation's start."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return float(self.calls) + (1000.0 if self.calls >= 4 else 0.0)


def test_the_job_wall_limit_covers_the_lean_evaluation(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    plan = env.plan(env.job(wall_limit_seconds=500))
    with pytest.raises(LimitReached):
        lej.execute_c0_job(plan, bs.session(env.recipe), origin=0.0, origin_utc_epoch=0.0, clock=JumpClock())
    assert (env.base / "out" / "train" / "COMPLETE.json").is_file()            # training ran inside the limit
    assert (env.base / "out" / "lean" / "error.txt").is_file()
    assert not (env.base / "out" / "c0_record.json").exists()


def test_the_process_age_reads_field_22_after_the_command_name():
    stat = "4242 (a (strange) name) S " + " ".join(str(k) for k in range(4, 22)) + " 2000 23 24 25"
    assert lej._process_age(stat, "100.5 50.25\n", 100) == pytest.approx(80.5)
    assert lej._read_process_age() is None or lej._read_process_age() > 0


# ----- 6. failures and verification ------------------------------------------------------------------------------


def test_a_guard_failure_keeps_the_error_and_writes_no_record(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    with pytest.raises(RuntimeError):
        env.run(loaders={"guard_fails": True})
    out = env.base / "out"
    assert (out / "train" / "COMPLETE.json").is_file() and (out / "lean" / "error.txt").is_file()
    assert not (out / "c0_record.json").exists() and not (out / "lean" / "COMPLETE.json").exists()
    assert lej.verify_c0(out) == ["no c0_record.json: the job did not finish"]
    status = json.loads((out / "lean" / "status.json").read_bytes())
    assert status["status"] == "failed"


def test_verify_passes_and_finds_every_change(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    env.run()
    out = env.base / "out"
    assert lej.verify_c0(out) == []

    def changed(path: Path, data: bytes | None) -> list[str]:
        before = path.read_bytes() if path.exists() else None
        if data is None:
            path.unlink()
        else:
            path.write_bytes(data)
        problems = lej.verify_c0(out)
        if before is None:
            path.unlink()
        else:
            path.write_bytes(before)
        return problems

    sample = out / "lean" / "sealed" / "samples.jsonl"
    assert changed(sample, sample.read_bytes() + b"\n")
    assert changed(sample, None)
    state = out / "train" / "states" / "e1" / "adapter.safetensors"
    assert changed(state, state.read_bytes()[:-1] + b"\0")
    assert changed(out / "extra.txt", b"x")
    assert changed(out / "lean" / "sealed" / "extra.jsonl", b"{}\n")
    record = out / "c0_record.json"
    doc = json.loads(record.read_bytes())
    other = copy.deepcopy(doc)
    other["lean_unit"]["sealed_files"]["samples.jsonl"]["sha256"] = "0" * 64
    assert changed(record, canonical_json(other))
    other = copy.deepcopy(doc)
    other["training"]["complete_sha256"] = "0" * 64
    assert changed(record, canonical_json(other))
    assert changed(record, b"not json")
    assert changed(record, canonical_json({**doc, "kind": "another"}))
    receipt = out / "lean" / "source_receipt.json"
    assert changed(receipt, receipt.read_bytes().replace(b'"', b"'", 1))
    assert lej.verify_c0(out) == []


# ----- 7. the command line ----------------------------------------------------------------------------------------


def cli(argv: list[str], **kwargs) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = lej.main(argv, **kwargs)
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def cli_env(env, monkeypatch):
    monkeypatch.setattr(lej, "SETTINGS_PATH", env.settings_path)
    monkeypatch.setattr(lej, "SETTINGS_SHA256", env.settings_sha256)
    return env


def args(env: bs.Env, job: Path, out: Path) -> list[str]:
    return ["run", "--job", str(job), "--prepared", str(env.prepared_dir), "--recipe", str(env.recipe_path),
            "--out", str(out)]


def test_the_command_line_runs_verifies_and_prints_no_text(cli_env):
    env = cli_env
    out = env.base / "cli"
    code, stdout, stderr = cli(args(env, env.job(), out), loaders=fx.fixture_loaders())
    assert code == 0, stderr
    shown = json.loads(stdout)
    assert shown["ok"] is True and shown["record_sha256"] == sha256_file(out / "c0_record.json")
    assert (shown["contents"], shown["answers"], shown["sealed_files"]) == ("a", 4, 6)
    record = json.loads((out / "c0_record.json").read_bytes())
    marks = record["timeline_seconds"]
    assert set(marks) == {"imports_done", "plan_checked", "session_ready", "checks_done", "train_start", "train_end",
                          "lean_start", "lean_end", "verified", "end"}                 # canonical JSON sorts the keys
    assert marks["imports_done"] <= marks["plan_checked"] <= marks["session_ready"] <= marks["checks_done"] <= \
        marks["train_start"] <= marks["end"] == record["job_span_seconds"]
    assert record["phase_seconds"]["before_training"] == marks["train_start"]
    assert record["cold_start"]["process_age_at_origin_seconds"] == lej._PROCESS_AGE_AT_ORIGIN
    prepared = load_prepared(env.prepared_dir, env.manifest_sha256, banks=("dev",))
    for item in prepared.banks["dev"]:
        assert item.get("prompt", "\x00") not in stdout + stderr
    code, stdout, _ = cli(["verify", "--out", str(out)])
    assert code == 0 and json.loads(stdout) == {"ok": True, "problems": 0, "messages": []}


def test_the_command_line_refuses_with_exit_2_and_makes_no_folder(cli_env):
    env = cli_env
    out = env.base / "cli"
    code, stdout, stderr = cli(args(env, env.job(evaluate_bank="dev"), out), loaders=fx.fixture_loaders())
    assert code == 2 and not out.exists() and json.loads(stderr)["ok"] is False and stdout == ""
    code, _, _ = cli(args(env, env.job(), out) + ["--expect-adapter-fingerprint", "xyz"], loaders=fx.fixture_loaders())
    assert code == 2 and not out.exists()


def test_the_command_line_refuses_changed_settings(cli_env, monkeypatch):
    env = cli_env
    monkeypatch.setattr(lej, "SETTINGS_SHA256", "0" * 64)
    code, _, stderr = cli(args(env, env.job(), env.base / "cli"), loaders=fx.fixture_loaders())
    assert code == 2 and "Refusal" in stderr and not (env.base / "cli").exists()


def test_the_command_line_reports_a_failure_with_exit_1(cli_env):
    env = cli_env
    out = env.base / "cli"
    code, stdout, stderr = cli(args(env, env.job(), out), loaders=fx.fixture_loaders(guard_fails=True))
    assert code == 1 and stdout == "" and json.loads(stderr)["ok"] is False
    assert (out / "lean" / "error.txt").is_file()
    code, stdout, _ = cli(["verify", "--out", str(out)])
    assert code == 1 and json.loads(stdout)["problems"] == 1


def test_a_warm_session_refusal_from_the_command_path_is_exit_2(cli_env, monkeypatch):
    env = cli_env
    original = runner.Session

    class Warm(original):
        def __init__(self, recipe, loaders):
            super().__init__(recipe, loaders)
            self.loaded_in["policy"] = "an earlier job"

    monkeypatch.setattr(runner, "Session", Warm)
    code, _, stderr = cli(args(env, env.job(), env.base / "cli"), loaders=fx.fixture_loaders())
    assert code == 2 and "not a cold start" in stderr and not (env.base / "cli").exists()


# ----- 8. the record's identities -----------------------------------------------------------------------------------


def test_the_record_names_its_inputs_and_settings(done):
    env, plan, record = done
    assert record["kind"] == lej.RECORD_KIND and record["version"] == 1
    prov = record["provenance"]
    assert prov["settings_sha256"] == env.settings_sha256 and prov["label_entries"] == {}
    assert prov["inputs"] == {"job": plan.job_sha256, "recipe": sha256_file(env.recipe_path),
                              "prepared_manifest": env.manifest_sha256}
    assert prov["engine_identity_sha256"] == ENGINE_X
    job = record["job"]
    assert (job["arm"], job["seed"], job["target_checkpoint"], job["recipe_sha256"], job["code_sha256"]) == (
        "a0", bs.SEED, "e1", config_sha256(env.recipe), ENGINE_X)
    assert job["recipe_name"] == "fixture-0" and job["edit_sha256"] is None
    lean_job = json.loads((env.base / "out" / "lean" / "lean_job.json").read_bytes())
    assert lean_job["harm_prompts"] == [i["prompt_id"] for i in plan.harm]
    assert lean_job["overrefusal_prompts"] == [i["prompt_id"] for i in plan.overrefusal]
    assert lean_job["subset_sha256"] == record["subset"]["subset_sha256"]
    receipt = json.loads((env.base / "out" / "lean" / "source_receipt.json").read_bytes())
    assert receipt["complete_sha256"] == record["training"]["complete_sha256"] and receipt["checkpoint"] == "e1"
    assets = json.loads((env.base / "out" / "lean" / "assets.json").read_bytes())
    assert assets["guard"] == {"fixture": fx.FIXTURE} and assets["policy"]["fixture"] == fx.FIXTURE
    assert verify_files(env.base / "out" / "lean") == []
