"""End-to-end jobs on ENGINEERING FIXTURES (tiny random Qwen2+LoRA on CPU, byte codec,
scripted guard, tiny guard LM): continuation identical to direct training, paired seeded
adapters, removal and epoch coverage, evaluation isolation and records (including the
forward-only query loss), hidden-reference refusals and physical separation, resume refusals on
recipe/code changes, preserved failures (numerical ones included), the trajectory registry,
code pins, identity-bound calibration reuse, attribution source enforcement before model work,
dependency receipts verified through a read-only path map, eval-state, guard features with
label-sequence scores, audits and the CLI. None of these numbers is a scientific result."""

from __future__ import annotations

import json
import math
import shutil
import statistics
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection import __main__ as cli  # noqa: E402
from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import loaders, runner  # noqa: E402
from experiments.safety_selection.common import read_json, read_jsonl, sha256_file, write_json  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from experiments.safety_selection.jobs import AccessError, JobError  # noqa: E402
from experiments.safety_selection.ledger import (RunDirError, artifact_hashes, read_complete,  # noqa: E402
                                                 verify_files)
from experiments.safety_selection.prepare import AUDITOR, BANK_FILES, load_prepared  # noqa: E402
from experiments.safety_selection.sources import DataError  # noqa: E402
from experiments.safety_selection.textproc import (GUARD_LABEL_SEQUENCES, GUARD_SAFETY,  # noqa: E402
                                                   QWEN_DEFAULT_SYSTEM)
from experiments.safety_selection.verify import PathMap, compare_generations, verify_run  # noqa: E402


def code_pin() -> str:
    return runner.code_identity()["sha256"]


def run_job(env, **fields) -> dict:
    job = {"kind": "run-one", "split": "dev", "arm": "a0", "seed": 1101, "role": "development",
           "target_checkpoint": "q", "evaluate_bank": "dev", "manifest_sha256": env.sha,
           "recipe_sha256": config_sha256(env.recipe), "code_sha256": None, "resume_from": None,
           "replicate_of": None, "wall_limit_seconds": None}
    job.update(fields)
    return job


def eval_job(env, source: dict, checkpoint: str, recipe: dict | None = None, bank: str = "dev",
             code_sha256: str | None = None) -> dict:
    return {"kind": "eval-state", "source_run": source["run_dir"], "checkpoint": checkpoint,
            "evaluate_bank": bank, "manifest_sha256": env.sha,
            "recipe_sha256": config_sha256(recipe or env.recipe), "code_sha256": code_sha256,
            "wall_limit_seconds": None}


def attr_job(env, **fields) -> dict:
    job = {"kind": "attributes", "split": "dev", "seed": 1101, "role": "development",
           "a0_states": {"q": env.direct["run_dir"], "e1": env.direct["run_dir"], "e3": env.to_e3["run_dir"]},
           "group_ids": sorted(env.view.groups["dev"]), "query_bank": "ref", "manifest_sha256": env.sha,
           "recipe_sha256": config_sha256(env.recipe), "code_sha256": None, "wall_limit_seconds": None}
    job.update(fields)
    return job


def groups_job(env, split: str = "dev", code_sha256: str | None = None, sha: str | None = None) -> dict:
    return {"kind": "score-groups", "split": split, "manifest_sha256": sha or env.sha,
            "recipe_sha256": config_sha256(env.recipe), "code_sha256": code_sha256, "wall_limit_seconds": None}


def state(run: dict, checkpoint: str) -> dict:
    return read_json(Path(run["run_dir"]) / "states" / checkpoint / "state.json")


def forge(source: str | Path, target: Path, edit=None, identity_edit=None) -> Path:
    """Copy a complete run, edit it, and re-forge COMPLETE.json so its own file hashes match
    (``identity_edit`` also changes the completion identity): only cross-checks can catch it."""
    copy = Path(shutil.copytree(source, target))
    if edit is not None:
        edit(copy)
    marker = read_json(copy / "COMPLETE.json")
    (copy / "COMPLETE.json").unlink()
    marker["files"] = artifact_hashes(copy)
    if identity_edit is not None:
        identity_edit(marker["identity"])
    write_json(copy / "COMPLETE.json", marker)
    assert verify_files(copy) == []
    return copy


def edit_json(path: Path, **changes) -> None:
    data = read_json(path)
    data.update(changes)
    write_json(path, data)


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("jobs")
    prepared_dir, digest = fx.prepare_dir(root / "prepared")
    recipe = fx.recipe()
    e = SimpleNamespace(root=root, prepared=prepared_dir, sha=digest, recipe=recipe,
                        session=runner.Session(recipe, fx.fixture_loaders()))
    e.view = load_prepared(prepared_dir, digest, banks=("dev",))
    e.dev_group, e.held_group = sorted(e.view.groups["dev"])[0], sorted(e.view.groups["heldout"])[0]

    def go(name: str, **fields) -> dict:
        return runner.run_one(run_job(e, **fields), prepared_dir=prepared_dir, out_dir=root / name,
                              session=e.session)

    e.direct = go("direct", target_checkpoint="e1", evaluate_bank=None)
    e.short = go("short")
    e.cont = go("cont", target_checkpoint="e1", resume_from=e.short["run_dir"])
    e.to_e3 = go("direct-e3", target_checkpoint="e3", evaluate_bank=None, resume_from=e.direct["run_dir"])
    e.removal = go("removal", arm=e.dev_group, target_checkpoint="e1", evaluate_bank=None)
    e.other_seed = go("seed-1102", seed=1102, evaluate_bank=None)
    return e


def test_continuation_equals_direct_training_and_evaluation_does_not_perturb_it(env):
    for checkpoint, other in (("q", env.short), ("e1", env.cont)):
        direct, resumed = state(env.direct, checkpoint), state(other, checkpoint)
        for key in ("adapter_fingerprint", "optimizer_fingerprint", "rng_fingerprint", "step",
                    "examples_seen", "stream_sha256"):
            assert direct[key] == resumed[key], (checkpoint, key)
    assert state(env.direct, "e1")["adapter_fingerprint"] != state(env.direct, "init")["adapter_fingerprint"]
    q, e1 = state(env.direct, "q")["step"], state(env.direct, "e1")["step"]
    assert (q, e1) == (4, 15)  # 58 rows, 4 per step: ceil(ceil(58/4)/4) = 4; ceil(58/4) = 15
    assert env.cont["incremental_train_cost"]["steps"] == e1 - q
    assert env.cont["trajectory_cost"]["steps"] == env.direct["trajectory_cost"]["steps"] == e1
    assert env.cont["trajectory_cost"]["examples"] == 58
    assert env.short["evaluation"] is not None and env.direct["evaluation"] is None
    assert env.to_e3["checkpoints"]["e3"]["step"] == 45 and env.to_e3["incremental_train_cost"]["steps"] == 30
    assert env.cont["resumed_from_complete_sha256"] == sha256_file(Path(env.short["run_dir"]) / "COMPLETE.json")
    receipt, = read_json(Path(env.cont["run_dir"]) / "dependencies.json")["dependencies"]
    assert (receipt["role"], receipt["checkpoint"], receipt["state"]["step"]) == ("resume_from", "q", q)


def test_arms_of_one_seed_start_from_one_seeded_adapter(env):
    init = env.direct["trajectory"]["init_fingerprint"]
    assert env.short["trajectory"]["init_fingerprint"] == init
    assert env.removal["trajectory"]["init_fingerprint"] == init
    assert env.other_seed["trajectory"]["init_fingerprint"] != init
    assert state(env.removal, "init")["adapter_fingerprint"] == state(env.direct, "init")["adapter_fingerprint"]


def test_removed_rows_never_train_and_every_retained_row_completes_each_epoch(env, tmp_path):
    removed = set(env.view.groups["dev"][env.dev_group])
    steps = read_jsonl(Path(env.removal["run_dir"]) / "steps.jsonl")
    assert not removed & {r for s in steps for r in s["rows"]}
    per_epoch = env.removal["trajectory"]["steps_per_epoch"]
    assert sorted(r for s in steps[:per_epoch] for r in s["rows"]) == sorted(set(env.view.corpus) - removed)
    assert env.removal["trajectory"]["retained_rows"] == 58 - len(removed)
    assert verify_run(env.removal["run_dir"], env.prepared)["complete"]
    assert verify_run(env.to_e3["run_dir"], env.prepared)["complete"]  # a resumed three-epoch chain

    def forged_step(copy: Path) -> None:
        lines = (copy / "steps.jsonl").read_text().splitlines()
        first = json.loads(lines[0])
        first["rows"][0] = sorted(removed)[0]
        lines[0] = json.dumps(first, sort_keys=True)
        (copy / "steps.jsonl").write_text("\n".join(lines) + "\n")

    copy = forge(env.removal["run_dir"], tmp_path / "copy", forged_step)  # consistent hashes
    result = verify_run(copy, env.prepared)
    assert result["own_files"]["complete"] and result["dependency_chain"]["complete"]
    assert not result["complete"] and "removed row" in " ".join(result["stream"]["problems"])


def test_evaluation_records_exact_inputs_stop_reasons_guard_labels_and_forced_choice(env):
    folder = Path(env.short["run_dir"]) / "eval" / "q"
    bank = {i["prompt_id"]: i for i in env.view.banks["dev"]}
    generations = read_jsonl(folder / "generations.jsonl")
    guard = read_jsonl(folder / "guard.jsonl")
    utility = read_jsonl(folder / "arc_utility.jsonl")
    assert [g["prompt_id"] for g in generations] == [g["prompt_id"] for g in guard]
    for g in generations:
        assert g["prompt_ids"] and g["prompt_tokens"] == len(g["prompt_ids"]) == bank[g["prompt_id"]]["prompt_tokens"]
        assert g["stop_reason"] in ("eos", "max_new_tokens") and g["output_tokens"] <= 5
        assert (g["stop_reason"] == "max_new_tokens") == (g["output_tokens"] == 5)
        assert g["empty"] == (g["output_tokens"] == 0)
    for u in utility:
        assert len(u["scores"]) == len(u["labels"]) and set(u["predicted"]) <= set(u["labels"])
        assert u["correct"] == (u["predicted"] == [u["answer"]])
        assert all(ids and 257 not in ids for ids in u["label_token_ids"])  # labels only, no end-of-turn
        assert u["scores"] == pytest.approx([math.fsum(v) for v in u["token_logprobs"]])
    summary = env.short["evaluation"]
    assert (summary["safety"]["n"], summary["arc_generation"]["n"], summary["arc_utility"]["n"]) == (3, 2, 3)
    for kind in ("safety", "arc_generation"):
        s = summary[kind]
        assert s["guard_unsafe"] + s["guard_controversial"] + s["guard_safe"] + s["guard_invalid"] == s["n"]
    first = read_jsonl(Path(env.direct["run_dir"]) / "ledger.jsonl")  # loaded the policy, tokenized
    ledger = read_jsonl(Path(env.short["run_dir"]) / "ledger.jsonl")  # reused them; loaded the guard
    assert {"load_policy", "tokenize", "memory_preflight", "init_state", "train",
            "verify_trajectory"} <= {r["stage"] for r in first}
    assert {"init_state", "train", "query_loss", "generate", "arc_utility", "load_guard", "guard",
            "verify_trajectory"} <= {r["stage"] for r in ledger}
    assert all(r["status"] == "ok" and r["seconds"] >= 0 and "memory" in r for r in first + ledger)
    records = read_jsonl(Path(env.short["run_dir"]) / "records.jsonl")
    assert {"asset": "policy", "loaded_in": env.direct["run_dir"], "kind": "asset_reuse"} in records


def test_evaluation_measures_the_forward_only_query_loss_on_the_reference_rows_and_charges_it(env):
    records = read_jsonl(Path(env.short["run_dir"]) / "eval" / "q" / "query_loss.jsonl")
    queries = env.view.query_rows
    assert [r["query_id"] for r in records] == [q["query_id"] for q in queries]
    assert all((r["target_tokens"], r["token_sha256"]) == (q["target_tokens"], q["token_sha256"])
               and r["input_tokens"] == q["prompt_tokens"] + q["target_tokens"] and math.isfinite(r["loss"])
               for r, q in zip(records, queries))
    summary = env.short["evaluation"]["query_loss"]
    assert (summary["n"], summary["forward_passes"]) == (6, 6)
    assert summary["mean"] == pytest.approx(statistics.fmean(r["loss"] for r in records))
    assert summary["definition"] == en.QUERY_LOSS_DEFINITION
    stage, = [r for r in read_jsonl(Path(env.short["run_dir"]) / "ledger.jsonl") if r["stage"] == "query_loss"]
    assert stage["forward_passes"] == 6 and stage["status"] == "ok" and stage["seconds"] >= 0
    assert stage["target_tokens"] == sum(q["target_tokens"] for q in queries)


def test_malformed_guard_answers_stay_unresolved_and_never_count_as_safe(env):
    conflicting = "Safety: Safe\nSafety: Unsafe\nCategories: None\nRefusal: No"
    session = runner.Session(env.recipe, fx.fixture_loaders(guard_answers={"": conflicting}))
    out = runner.eval_state(eval_job(env, env.short, "q"), prepared_dir=env.prepared,
                            out_dir=env.root / "malformed", session=session)
    for kind in ("safety", "arc_generation"):
        s = out["evaluation"][kind]
        assert s["guard_invalid"] == s["n"] and s["guard_safe"] == 0 and s["guard_unsafe"] == 0


def test_hidden_reference_bank_and_wrong_seeds_or_splits_are_refused_before_anything_runs(env):
    cases = [{"evaluate_bank": "hidden"},
             {"role": "selector", "split": "heldout", "seed": 2101, "evaluate_bank": "hidden"},
             {"role": "reference", "split": "heldout", "seed": 9101, "evaluate_bank": "hidden"},
             {"role": "selector", "split": "dev", "seed": 2101, "evaluate_bank": "selector"},
             {"seed": 2101},
             {"role": "selector", "split": "heldout", "seed": 9101, "evaluate_bank": "selector"},
             {"role": "development", "evaluate_bank": "selector"}]
    for i, fields in enumerate(cases):
        out = env.root / f"refused-{i}"
        with pytest.raises(AccessError):
            runner.run_one(run_job(env, **fields), prepared_dir=env.prepared, out_dir=out, session=env.session)
        assert not out.exists()
    with pytest.raises(AccessError):
        runner.calibrate(prepared_dir=env.prepared, out_root=env.root / "cal-refused", session=env.session,
                         arms=[env.held_group], seeds=[1101])
    with pytest.raises(AccessError):
        runner.calibrate(prepared_dir=env.prepared, out_root=env.root / "cal-refused", session=env.session,
                         arms=["a0"], seeds=[2101])


def test_ordinary_runs_never_open_the_hidden_bank_while_reference_runs_verify_it(env, tmp_path):
    copy = Path(shutil.copytree(env.prepared, tmp_path / "prepared"))
    hidden = copy / BANK_FILES["hidden"]
    hidden.write_bytes(hidden.read_bytes().replace(b'"kind"', b'"kind" ', 1))
    pin = code_pin()
    selector = runner.run_one(run_job(env, role="selector", split="heldout", arm=env.held_group, seed=2101,
                                      evaluate_bank="selector", code_sha256=pin),
                              prepared_dir=copy, out_dir=tmp_path / "selector", session=env.session)
    assert selector["complete"] and selector["evaluation"]["safety"]["n"] == 3
    with pytest.raises(DataError, match="differs from the manifest"):
        runner.run_one(run_job(env, role="reference", split="heldout", arm=env.held_group, seed=9101,
                               evaluate_bank="hidden", code_sha256=pin),
                       prepared_dir=copy, out_dir=tmp_path / "reference", session=env.session, allow_hidden=True)
    reference = runner.run_one(run_job(env, role="reference", split="heldout", arm="a0", seed=9101,
                                       evaluate_bank="hidden", code_sha256=pin),
                               prepared_dir=env.prepared, out_dir=tmp_path / "reference-ok",
                               session=env.session, allow_hidden=True)
    assert reference["evaluation"]["safety"]["n"] == 4 and reference["evaluation"]["arc_utility"]["n"] == 3
    with pytest.raises(JobError, match="must pin code_sha256"):  # its eval-state is confirmation too
        runner.eval_state(eval_job(env, selector, "q", bank="selector"), prepared_dir=copy,
                          out_dir=tmp_path / "selector-eval", session=env.session)
    assert not (tmp_path / "selector-eval").exists()


def test_confirmation_jobs_without_a_code_pin_are_refused_before_anything_runs(env, tmp_path):
    out = tmp_path / "unpinned"
    with pytest.raises(JobError, match="must pin code_sha256"):
        runner.run_one(run_job(env, role="selector", split="heldout", arm=env.held_group, seed=2101,
                               evaluate_bank="selector"), prepared_dir=env.prepared, out_dir=out, session=env.session)
    with pytest.raises(JobError, match="must pin code_sha256"):
        runner.score_groups(groups_job(env, "heldout"), prepared_dir=env.prepared, out_dir=out, session=env.session)
    assert not out.exists()
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps(env.recipe))
    args = ["make-job", "run-one", "--prepared", str(env.prepared), "--recipe", str(recipe_path),
            "--out", str(tmp_path / "selector-job.json"), "--split", "heldout", "--arm", env.held_group,
            "--seed", "2101", "--role", "selector", "--target", "q", "--bank", "selector"]
    assert cli.main(args) == 2 and not (tmp_path / "selector-job.json").exists()
    assert cli.main(args + ["--pin-code"]) == 0
    assert read_json(tmp_path / "selector-job.json")["code_sha256"] == code_pin()


def test_continuations_refuse_recipe_or_code_changes_and_inconsistent_sources(env, monkeypatch):
    other = fx.recipe(**{"train.lr": 0.02})
    with pytest.raises(JobError, match="recipe_sha256"):
        runner.run_one(run_job(env, target_checkpoint="e1", resume_from=env.short["run_dir"],
                               recipe_sha256=config_sha256(other)),
                       prepared_dir=env.prepared, out_dir=env.root / "x1",
                       session=runner.Session(other, fx.fixture_loaders()))
    with pytest.raises(JobError, match="later checkpoint"):
        runner.run_one(run_job(env, resume_from=env.cont["run_dir"]), prepared_dir=env.prepared,
                       out_dir=env.root / "x2", session=env.session)
    with pytest.raises(JobError, match="differs in seed"):
        runner.run_one(run_job(env, seed=1102, target_checkpoint="e1", resume_from=env.short["run_dir"]),
                       prepared_dir=env.prepared, out_dir=env.root / "x3", session=env.session)
    fake = dict(runner.code_identity(), sha256="f" * 64)
    monkeypatch.setattr(runner, "code_identity", lambda: fake)
    with pytest.raises(JobError, match="code changed"):
        runner.run_one(run_job(env, target_checkpoint="e1", resume_from=env.short["run_dir"]),
                       prepared_dir=env.prepared, out_dir=env.root / "x4", session=env.session)
    assert not any((env.root / f"x{i}").exists() for i in range(1, 5))


def test_failed_jobs_are_preserved_incomplete_and_can_be_neither_resumed_nor_overwritten(env):
    session = runner.Session(env.recipe, fx.fixture_loaders(guard_fails=True))
    out = env.root / "failed"
    with pytest.raises(RuntimeError, match="injected guard failure"):
        runner.run_one(run_job(env, seed=1103), prepared_dir=env.prepared, out_dir=out, session=session)
    assert (out / "error.txt").exists() and not (out / "COMPLETE.json").exists()
    assert (out / "states" / "q" / "state.json").exists()  # finished work stays visible
    assert any(r["status"] == "error" for r in read_jsonl(out / "ledger.jsonl"))
    assert not verify_run(out)["complete"]
    with pytest.raises(JobError, match="not a complete run"):
        runner.run_one(run_job(env, seed=1103, target_checkpoint="e1", resume_from=str(out)),
                       prepared_dir=env.prepared, out_dir=env.root / "failed-resume", session=env.session)
    tampered = Path(shutil.copytree(env.short["run_dir"], env.root / "tampered"))
    (tampered / "eval" / "q" / "summary.json").write_text("{}")
    assert any("changed" in p for p in verify_run(tampered)["problems"])
    (tampered / "extra.txt").write_text("late")
    assert any("added after completion" in p for p in verify_run(tampered)["problems"])
    with pytest.raises(RunDirError):
        runner.run_one(run_job(env), prepared_dir=env.prepared, out_dir=env.short["run_dir"], session=env.session)
    assert verify_files(env.short["run_dir"]) == []


def test_numerical_failures_fail_the_job_and_never_become_scores(env):
    nan_logprobs = lambda sequences, n_targets, check=None: [[float("nan")] * n for n in n_targets]  # noqa: E731
    out = env.root / "x0-nan"
    with pytest.raises(FloatingPointError):
        runner.score_groups(groups_job(env), prepared_dir=env.prepared, out_dir=out,
                            session=runner.Session(env.recipe, fx.fixture_loaders(label_logprobs=nan_logprobs)))
    assert (out / "error.txt").exists() and not (out / "COMPLETE.json").exists()
    assert not (out / "x0_guard.json").exists()
    tox = fx.recipe(name="with secondary toxicity", secondary_toxicity={
        "repo_id": "fixture/toxicity", "revision": fx.ZERO_REV, "label": "toxic", "activation": "sigmoid",
        "max_length": 64, "batch_size": 4, "device": "cpu", "threshold": 0.5})
    session = runner.Session(tox, fx.fixture_loaders(toxicity_score=lambda texts: [float("nan")] * len(texts)))
    out = env.root / "toxicity-nan"
    with pytest.raises(en.NonFiniteError):
        runner.eval_state(eval_job(env, env.short, "q", tox), prepared_dir=env.prepared, out_dir=out,
                          session=session)
    assert (out / "error.txt").exists() and not (out / "COMPLETE.json").exists()
    assert not (out / "eval" / "q" / "toxicity.jsonl").exists()


def test_registry_refuses_seed_reuse_allows_named_replicates_and_retries_after_failure(env):
    registry = env.root / "registry.jsonl"
    first = runner.run_one(run_job(env, seed=1104, evaluate_bank=None), prepared_dir=env.prepared,
                           out_dir=env.root / "r1", session=env.session, registry=registry)
    with pytest.raises(JobError, match="fresh seed"):
        runner.run_one(run_job(env, seed=1104, evaluate_bank=None), prepared_dir=env.prepared,
                       out_dir=env.root / "r2", session=env.session, registry=registry)
    assert (env.root / "r2" / "error.txt").exists()
    replicate = runner.run_one(run_job(env, seed=1104, evaluate_bank=None, replicate_of=first["run_dir"]),
                               prepared_dir=env.prepared, out_dir=env.root / "r3", session=env.session,
                               registry=registry)
    assert state(replicate, "q")["adapter_fingerprint"] == state(first, "q")["adapter_fingerprint"]
    failing = runner.Session(env.recipe, fx.fixture_loaders(guard_fails=True))
    with pytest.raises(RuntimeError):
        runner.run_one(run_job(env, seed=1103, arm=env.dev_group), prepared_dir=env.prepared,
                       out_dir=env.root / "f1", session=failing, registry=registry)
    retry = runner.run_one(run_job(env, seed=1103, arm=env.dev_group), prepared_dir=env.prepared,
                           out_dir=env.root / "f2", session=env.session, registry=registry)
    assert retry["complete"]
    entries = read_jsonl(registry)
    assert entries[-1]["retry_after_failures"] == [str(env.root / "f1")]


def test_attribution_scores_both_variants_from_the_query_rows_and_charges_every_pass(env):
    before = {c: verify_files(Path(env.direct["run_dir"])) for c in ("q", "e1")}
    result = runner.attributes(attr_job(env), prepared_dir=env.prepared, out_dir=env.root / "attr",
                               session=env.session)
    folder = Path(result["run_dir"])
    groups = read_json(folder / "groups.json")["groups"]
    rows = read_jsonl(folder / "rows.jsonl")
    assert set(groups) == set(env.view.groups["dev"])
    assert len(rows) == sum(len(m) for m in env.view.groups["dev"].values()) == 14
    for gid, aggregate in groups.items():
        members = [r for r in rows if r["group_id"] == gid]
        means = [statistics.fmean(r["per_checkpoint"][c]["cosine"] for r in members) for c in ("q", "e1", "e3")]
        assert aggregate["checkpoint_gradsim"] == pytest.approx(statistics.fmean(means))
        assert aggregate["adam_diag_preconditioned_dot"] == pytest.approx(
            math.fsum(r["per_checkpoint"][c]["adam_score"] for r in members for c in ("q", "e1", "e3")))
        assert -1 <= aggregate["checkpoint_gradsim"] <= 1
        assert math.isfinite(aggregate["adam_diag_preconditioned_dot"])
    steps = result["optimizer_steps"]
    assert (steps["q"], steps["e1"], steps["e3"]) == (4, 15, 45)
    assert result["costs"]["gradient_passes"] == (14 + 6) * 3
    assert result["costs"]["a0_trajectory_cost_to_checkpoint"]["e3"]["steps"] == 45
    queries = read_json(folder / "queries.json")
    assert queries["n"] == 6 and set(queries["per_checkpoint"]) == {"q", "e1", "e3"}
    assert verify_files(folder) == [] and before == {"q": [], "e1": []}
    assert verify_files(Path(env.direct["run_dir"])) == [] and verify_files(Path(env.to_e3["run_dir"])) == []
    # Persisted provenance of every checkpoint actually used.
    receipts = read_json(folder / "dependencies.json")["dependencies"]
    assert [r["role"] for r in receipts] == ["a0_state:q", "a0_state:e1", "a0_state:e3"]
    for receipt, c, run in zip(receipts, ("q", "e1", "e3"), (env.direct, env.direct, env.to_e3)):
        source = result["sources"][c]
        assert receipt["complete_sha256"] == source["complete_sha256"] == sha256_file(
            Path(run["run_dir"]) / "COMPLETE.json")
        assert receipt["state_sha256"] == read_complete(run["run_dir"])["files"][f"states/{c}/state.json"]
        assert source["code_sha256"] == receipt["identity"]["code_sha256"] == code_pin()
        assert source["optimizer_step"] == steps[c] == receipt["state"]["step"]
        assert (source["adapter_fingerprint"], source["optimizer_fingerprint"]) == (
            state(run, c)["adapter_fingerprint"], state(run, c)["optimizer_fingerprint"])
    assert verify_run(folder)["complete"]
    # The gradient passes' query losses equal the evaluation's forward-only losses at the same
    # state (seed 1101 a0 at q), so this forward work is charged once.
    evaluated = {r["query_id"]: r["loss"] for r in read_jsonl(Path(env.short["run_dir"]) / "eval" / "q" / "query_loss.jsonl")}
    assert queries["per_checkpoint"]["q"]["losses"] == pytest.approx(evaluated, rel=1e-6)
    assert result["query_loss_from_gradient_passes"]["q"] == pytest.approx(env.short["evaluation"]["query_loss"]["mean"], rel=1e-6)


def test_attribution_refuses_reference_seeds_non_a0_states_and_missing_checkpoints(env):
    kwargs = {"prepared_dir": env.prepared, "session": env.session}
    with pytest.raises(AccessError):
        runner.attributes(attr_job(env, role="reference", split="heldout", seed=9101), out_dir=env.root / "a1", **kwargs)
    with pytest.raises(JobError, match="not an a0"):
        runner.attributes(attr_job(env, a0_states={"q": env.removal["run_dir"], "e1": env.removal["run_dir"],
                                                   "e3": env.to_e3["run_dir"]}), out_dir=env.root / "a2", **kwargs)
    with pytest.raises(JobError, match="exactly the recipe attribution checkpoints"):
        runner.attributes(attr_job(env, a0_states={"q": env.direct["run_dir"]}), out_dir=env.root / "a3", **kwargs)
    with pytest.raises(JobError, match="no saved e3"):
        runner.attributes(attr_job(env, a0_states={"q": env.direct["run_dir"], "e1": env.direct["run_dir"],
                                                   "e3": env.direct["run_dir"]}), out_dir=env.root / "a4", **kwargs)
    with pytest.raises(JobError, match="not dev groups"):
        runner.attributes(attr_job(env, group_ids=[env.held_group]), out_dir=env.root / "a5", **kwargs)
    with pytest.raises(JobError, match="differs from the attribution job in seed"):
        runner.attributes(attr_job(env, a0_states={"q": env.other_seed["run_dir"], "e1": env.direct["run_dir"],
                                                   "e3": env.to_e3["run_dir"]}), out_dir=env.root / "a6", **kwargs)
    assert not any((env.root / f"a{i}").exists() for i in range(1, 7))


def _bump_adam_step(copy: Path) -> None:
    from safetensors.torch import load_file, save_file

    folder = copy / "states" / "q"
    tensors = {k: (v + 1 if k.startswith("step/") else v)
               for k, v in load_file(str(folder / en.OPTIMIZER)).items()}
    save_file(tensors, str(folder / en.OPTIMIZER))
    record = read_json(folder / en.STATE)
    record["optimizer_fingerprint"] = en.tensor_fingerprint(tensors)
    record["files"][en.OPTIMIZER] = sha256_file(folder / en.OPTIMIZER)
    write_json(folder / en.STATE, record)


def test_attribution_refuses_cross_code_or_unplanned_a0_states_before_any_model_work(env, tmp_path):
    loads: list[int] = []
    session = runner.Session(env.recipe, fx.fixture_loaders(on_policy_load=lambda: loads.append(1)))
    q_state = lambda copy: copy / "states" / "q" / "state.json"  # noqa: E731
    fake_code = "f" * 64

    def other_code(copy: Path) -> None:
        edit_json(copy / "identity.json", code_sha256=fake_code)

    cases = {
        # Checkpoint q trained by other code, consistently forged (hashed identity and marker agree).
        "cross-code": ("not the running code", dict(edit=other_code,
                                                    identity_edit=lambda i: i.update(code_sha256=fake_code))),
        # Only the unhashed marker claims other code: it disagrees with the hashed identity.json.
        "marker-only": ("differs from its hashed identity.json",
                        dict(identity_edit=lambda i: i.update(code_sha256=fake_code))),
        "checkpoint": ("not the planned a0 checkpoint", dict(edit=lambda c: edit_json(q_state(c), checkpoint="e1"))),
        "stream": ("not the planned a0 checkpoint", dict(edit=lambda c: edit_json(q_state(c), stream_sha256="0" * 64))),
        "step": ("not the planned a0 checkpoint", dict(edit=lambda c: edit_json(q_state(c), step=5))),
        "adam-step": ("AdamW step", dict(edit=_bump_adam_step)),
    }
    for name, (message, forgery) in cases.items():
        source = forge(env.direct["run_dir"], tmp_path / f"source-{name}", **forgery)
        out = tmp_path / f"out-{name}"
        with pytest.raises(JobError, match=message):
            runner.attributes(attr_job(env, a0_states={"q": str(source), "e1": env.direct["run_dir"],
                                                       "e3": env.to_e3["run_dir"]}),
                              prepared_dir=env.prepared, out_dir=out, session=session)
        assert not out.exists(), name
    assert loads == []  # every refusal came before any model loaded


def test_dependency_chains_verify_through_a_read_only_path_map_of_an_archived_tree(env, tmp_path):
    remote = tmp_path / "remote"

    def go(name: str, **fields) -> dict:
        return runner.run_one(run_job(env, evaluate_bank=None, **fields), prepared_dir=env.prepared,
                              out_dir=remote / name, session=env.session)

    q = go("q")
    e1 = go("e1", target_checkpoint="e1", resume_from=q["run_dir"])
    e3 = go("e3", target_checkpoint="e3", resume_from=e1["run_dir"])
    ev = runner.eval_state(eval_job(env, q, "q"), prepared_dir=env.prepared, out_dir=remote / "ev",
                           session=env.session)
    at = runner.attributes(attr_job(env, a0_states={"q": q["run_dir"], "e1": e1["run_dir"], "e3": e3["run_dir"]},
                                    group_ids=[env.dev_group]),
                           prepared_dir=env.prepared, out_dir=remote / "at", session=env.session)
    for run in (e3, ev, at):
        assert verify_run(run["run_dir"])["complete"]
    recorded, archive = remote.resolve(), tmp_path / "archive"
    jobs_before = {p.relative_to(remote): p.read_bytes() for p in remote.rglob("*.json")}
    remote.rename(archive)  # a downloaded tree: every recorded absolute path now points nowhere
    mapping = PathMap([(str(recorded), str(archive))])
    for name in ("e3", "ev", "at"):
        bare = verify_run(archive / name)
        assert bare["own_files"]["complete"] and not bare["dependency_chain"]["complete"]
        assert not bare["complete"] and any("missing" in p for p in bare["problems"])
        mapped = verify_run(archive / name, path_map=mapping)
        assert mapped["complete"], mapped["problems"]
    deep = verify_run(archive / "e3", env.prepared, mapping)  # stream through the mapped resume chain
    assert deep["complete"] and deep["stream"]["checked"]
    assert sorted(r["depth"] for r in deep["dependency_chain"]["dependencies"]) == [0, 1]
    assert cli.main(["verify", "--run", str(archive / "ev"), "--map", f"{recorded}={archive}"]) == 0
    assert cli.main(["verify", "--run", str(archive / "ev"), "--map", "no-separator"]) == 2
    assert {p.relative_to(archive): p.read_bytes() for p in archive.rglob("*.json")} == jobs_before  # read-only
    # A changed source: q re-forged with consistent own hashes; the pinned receipts still catch it.
    with open(archive / "q" / "records.jsonl", "a") as handle:
        handle.write('{"kind": "late edit"}\n')
    marker = read_json(archive / "q" / "COMPLETE.json")
    (archive / "q" / "COMPLETE.json").unlink()
    marker["files"] = artifact_hashes(archive / "q")
    write_json(archive / "q" / "COMPLETE.json", marker)
    assert verify_files(archive / "q") == []
    for name in ("e3", "ev", "at"):
        changed = verify_run(archive / name, path_map=mapping)
        assert not changed["complete"] and any("differs from the pinned receipt" in p for p in changed["problems"])
    # A missing source.
    (archive / "e1").rename(archive / "e1-moved")
    missing = verify_run(archive / "at", path_map=mapping)
    assert any("e1" in p and "missing" in p for p in missing["problems"])


def test_eval_state_reevaluates_saved_states_and_batched_generation_matches_single(env):
    single = fx.recipe(**{"generation.batch_size": 1, "name": "single-row generation"})
    out = runner.eval_state(eval_job(env, env.short, "q", single), prepared_dir=env.prepared,
                            out_dir=env.root / "single", session=runner.Session(single, fx.fixture_loaders()))
    original = read_jsonl(Path(env.short["run_dir"]) / "eval" / "q" / "generations.jsonl")
    again = read_jsonl(Path(out["run_dir"]) / "eval" / "q" / "generations.jsonl")
    assert [(g["output_ids"], g["stop_reason"]) for g in original] == [(g["output_ids"], g["stop_reason"]) for g in again]
    assert out["adapter_fingerprint"] == state(env.short, "q")["adapter_fingerprint"]
    assert out["source_complete_sha256"] == sha256_file(Path(env.short["run_dir"]) / "COMPLETE.json")
    assert out["evaluation"]["query_loss"]["mean"] == pytest.approx(env.short["evaluation"]["query_loss"]["mean"],
                                                                    rel=1e-9)  # one row per forward
    agreement = compare_generations(env.short["run_dir"], out["run_dir"], "q")["by_kind"]
    assert {k: (v["n"], v["identical_outputs"], v["guard_label_agreement"]) for k, v in agreement.items()} == {
        "arc_generation": (2, 2, 2), "safety": (3, 3, 3)}
    longer = fx.recipe(**{"generation.max_new_tokens": 9, "name": "longer ceiling"})
    result = runner.eval_state(eval_job(env, env.cont, "e1", longer), prepared_dir=env.prepared,
                               out_dir=env.root / "longer", session=runner.Session(longer, fx.fixture_loaders()))
    assert result["evaluation"]["generation"]["max_new_tokens"] == 9
    assert verify_run(result["run_dir"])["complete"]  # its source chain (cont -> short) verifies
    changed = fx.recipe(**{"train.lr": 0.05})
    with pytest.raises(JobError, match="evaluation settings only"):
        runner.eval_state(eval_job(env, env.short, "q", changed), prepared_dir=env.prepared,
                          out_dir=env.root / "bad-eval", session=runner.Session(changed, fx.fixture_loaders()))
    with pytest.raises(AccessError):
        runner.eval_state(eval_job(env, env.short, "q", bank="hidden"), prepared_dir=env.prepared,
                          out_dir=env.root / "bad-eval", session=env.session, allow_hidden=True)


def test_score_groups_records_guard_features_and_label_sequence_scores_for_every_member_row(env):
    result = runner.score_groups(groups_job(env), prepared_dir=env.prepared, out_dir=env.root / "x0",
                                 session=env.session)
    run = Path(result["run_dir"])
    x0 = read_json(run / "x0_guard.json")
    features = x0["groups"]
    rows = read_jsonl(run / "rows.jsonl")
    audit = read_json(env.prepared / AUDITOR)  # the test reads the auditor file; jobs never do
    for gid, members in env.view.groups["dev"].items():
        f = features[gid]
        assert f["size"] == len(members) == (f["guard_unsafe"] + f["guard_controversial"] + f["guard_safe"]
                                             + f["guard_invalid"])
        assert f["guard_unsafe"] == sum(audit["rows"][m]["role"] == "risk" for m in members)
        assert f["guard_refusal_yes"] == sum(audit["rows"][m]["role"] == "aligned" for m in members)
        mine = [r for r in rows if r["group_id"] == gid]
        assert f["label_scores"]["scored"] == len(mine) and f["label_scores"]["unscored"] == 0
        for label in GUARD_SAFETY:
            values = [r["label_scores"]["normalized"][label] for r in mine]
            assert f["label_scores"][label.lower()] == pytest.approx(
                {"sum": math.fsum(values), "mean": statistics.fmean(values), "max": max(values)})
    assert x0["label_sequences"] == list(GUARD_LABEL_SEQUENCES)
    assert [bytes(ids).decode() for ids in x0["label_token_ids"]] == list(GUARD_LABEL_SEQUENCES)  # byte tokens
    for r in rows:
        scores = r["label_scores"]
        assert scores["valid"] and sum(scores["normalized"].values()) == pytest.approx(1.0, rel=1e-12)
        assert scores["loglik"] == pytest.approx({k: math.fsum(v) for k, v in scores["token_logprobs"].items()})
    # Direct recomputation: summed label-token log-probabilities after the exact guard prompt.
    guard_lm, tok = fx.tiny_guard_lm(), fx.FixtureGuardTokenizer()
    row = rows[0]
    train = env.view.train_rows[row["row_id"]]
    prefix = tok.apply_chat_template([{"role": "user", "content": train["prompt"]},
                                      {"role": "assistant", "content": train["response"]}])
    for label, ids in zip(GUARD_SAFETY, x0["label_token_ids"]):
        with torch.no_grad():
            logp = torch.log_softmax(guard_lm(input_ids=torch.tensor([prefix + ids])).logits[0].float(), -1)
        manual = math.fsum(float(logp[len(prefix) - 1 + j, t]) for j, t in enumerate(ids))
        assert row["label_scores"]["loglik"][label] == pytest.approx(manual, abs=1e-3)
    stages = {r["stage"]: r for r in read_jsonl(run / "ledger.jsonl")}
    assert stages["guard_label_scores"]["sequences"] == len(GUARD_LABEL_SEQUENCES) * len(rows) == 42
    assert stages["guard_label_scores"]["unscored"] == 0 and stages["guard_training_rows"]["status"] == "ok"
    assert result["costs"]["label_score_sequences"] == 42 and result["costs"]["guard_label_score_seconds"] >= 0


QWEN_INPUT = ("<|im_start|>system\n" + QWEN_DEFAULT_SYSTEM
              + "<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n")


def _audit_file(path: Path) -> None:
    def row(audit_id: str, prompt: str, completion: str) -> dict:
        return {"audit_id": audit_id, "completion": completion, "label_prompt_copy": None,
                "label_refusal": None, "label_toxic": None, "notes": "", "prompt": prompt,
                "prompt_format": fx.FIXTURE, "prompt_truncated": False}

    rows = [row("A0001", QWEN_INPUT.format("how do I do a thing"), "SECRET-UNSAFE text !!!"),
            row("A0002", QWEN_INPUT.format("another request"), "I'm sorry, I can't."),
            row("A0003", QWEN_INPUT.replace(QWEN_DEFAULT_SYSTEM, "other system").format("x"), "plain"),
            row("A0004", QWEN_INPUT.format("third request"), "ends <|im_end|> early")]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_score_audit_writes_scores_by_audit_id_and_prints_counts_only(env, tmp_path, monkeypatch, capsys):
    source = tmp_path / "blind.jsonl"
    _audit_file(source)
    result = runner.score_audit(source, out_dir=tmp_path / "audit", session=env.session)
    assert result["summary"] == {"items": 4, "unparsed_prompts": 1, "guard_invalid": 2, "guard_unsafe": 1,
                                 "guard_controversial": 0, "guard_safe": 1, "guard_refusal_yes": 1,
                                 "secondary_toxicity_flagged": None}
    written = (tmp_path / "audit" / "audit_scores.jsonl").read_text()
    assert "SECRET-UNSAFE" not in written and "how do I do a thing" not in written
    rows = [json.loads(line) for line in written.splitlines()]
    assert [r["audit_id"] for r in rows] == ["A0001", "A0002", "A0003", "A0004"]
    assert all(set(r) == {"audit_id", "guard", "secondary_toxicity"} for r in rows)
    monkeypatch.setattr(loaders, "real_loaders", lambda: fx.fixture_loaders(toxicity=True))
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps(env.recipe))
    capsys.readouterr()
    code = cli.main(["score-audit", "--recipe", str(recipe_path), "--input", str(source),
                     "--out", str(tmp_path / "audit-cli")])
    printed = capsys.readouterr().out
    assert code == 0 and '"items": 4' in printed
    assert "SECRET-UNSAFE" not in printed and "how do I do a thing" not in printed


def test_calibration_runs_development_units_checkpoint_by_checkpoint_and_reuses_complete_ones(env):
    root = env.root / "calibration"
    kwargs = {"prepared_dir": env.prepared, "out_root": root, "session": env.session,
              "arms": ["a0", env.dev_group], "seeds": [1102], "checkpoints": ["q", "e1"], "base_eval": True}
    first = runner.calibrate(**kwargs)
    assert [(u["arm"], u["checkpoint"], u["reused"]) for u in first["units"]] == [
        ("a0", "init", False), ("a0", "q", False), ("a0", "e1", False),
        (env.dev_group, "q", False), (env.dev_group, "e1", False)]
    for unit in first["units"]:
        assert verify_run(unit["run_dir"], env.prepared)["complete"]
    chained = read_json(Path(first["units"][2]["run_dir"]) / "job.json")
    assert chained["resume_from"] == first["units"][1]["run_dir"]
    assert state({"run_dir": first["units"][2]["run_dir"]}, "e1")["adapter_fingerprint"] != \
        state(env.direct, "e1")["adapter_fingerprint"]  # seed 1102, not 1101
    again = runner.calibrate(**kwargs)
    assert all(u["reused"] and u["identity_checked"] for u in again["units"])
    with pytest.raises(JobError, match="ordered subset"):
        runner.calibrate(**{**kwargs, "checkpoints": ["e1", "q"]})


def test_calibration_reuse_is_bound_to_the_requested_science(env, tmp_path, monkeypatch):
    root = tmp_path / "cal"
    kwargs = {"prepared_dir": env.prepared, "out_root": root, "session": env.session, "arms": ["a0"],
              "seeds": [1103], "checkpoints": ["q"]}
    unit = Path(runner.calibrate(**kwargs)["units"][0]["run_dir"])
    marker = (unit / "COMPLETE.json").read_bytes()
    assert runner.calibrate(**kwargs)["units"][0]["reused"]  # a valid reuse

    def refused(match: str, **changes) -> None:
        listing = sorted(p.name for p in root.iterdir())
        with pytest.raises(JobError, match=match):
            runner.calibrate(**{**kwargs, **changes})
        assert sorted(p.name for p in root.iterdir()) == listing  # nothing new was started
        assert (unit / "COMPLETE.json").read_bytes() == marker  # nothing was rewritten

    longer = fx.recipe(**{"generation.max_new_tokens": 6, "name": "longer ceiling"})
    refused("recipe_sha256", session=runner.Session(longer, fx.fixture_loaders()))
    other, _ = fx.prepare_dir(tmp_path / "other-prepared", edit=lambda c: c.update(design_seed=8))
    refused("manifest_sha256", prepared_dir=other)
    with monkeypatch.context() as patch:
        fake = dict(runner.code_identity(), sha256="f" * 64)
        patch.setattr(runner, "code_identity", lambda: fake)
        refused("code_sha256")
    forged = Path(shutil.copytree(unit, root / "1104-a0-q-a1"))  # hash-valid, named for seed 1104
    assert verify_files(forged) == []
    refused("seed", seeds=[1104])
    # A different lineage under the same unit name: q continued from an evaluated init unit.
    lineage = {**kwargs, "out_root": tmp_path / "lineage", "base_eval": True}
    runner.calibrate(**lineage)
    listing = sorted(p.name for p in (tmp_path / "lineage").iterdir())
    with pytest.raises(JobError, match="resume_from"):
        runner.calibrate(**{**lineage, "base_eval": False})
    assert sorted(p.name for p in (tmp_path / "lineage").iterdir()) == listing


def test_cli_plan_make_job_run_one_and_verify(env, tmp_path, monkeypatch, capsys):
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps(env.recipe))
    capsys.readouterr()
    assert cli.main(["plan", "--recipe", str(recipe_path), "--prepared", str(env.prepared)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["corpus_rows"] == 58 and plan["options"]["dev/a0"]["steps_per_epoch"] == 15
    assert plan["options"]["dev/a0"]["checkpoints"]["q"]["step"] == 4
    assert plan["evaluation_per_checkpoint"]["dev"]["query_loss_forward_passes"] == 6
    assert plan["score_groups_per_split"]["dev"]["guard_label_sequences"] == 42
    job_path = tmp_path / "job.json"
    args = ["make-job", "run-one", "--prepared", str(env.prepared), "--recipe", str(recipe_path),
            "--out", str(job_path), "--split", "dev", "--arm", "a0", "--seed", "1101", "--role", "development",
            "--target", "q", "--bank", "dev"]
    assert cli.main(args) == 0 and cli.main(args) == 2  # job files are never replaced
    monkeypatch.setattr(loaders, "real_loaders", lambda: fx.fixture_loaders())
    run = ["run-one", "--job", str(job_path), "--prepared", str(env.prepared), "--recipe", str(recipe_path),
           "--out", str(tmp_path / "cli-run")]
    assert cli.main(run) == 0
    assert cli.main(run) == 2  # an existing folder is invalid output, never replaced
    assert cli.main(["verify", "--run", str(tmp_path / "cli-run"), "--prepared", str(env.prepared)]) == 0
    (tmp_path / "cli-run" / "steps.jsonl").write_text("")
    assert cli.main(["verify", "--run", str(tmp_path / "cli-run")]) == 1
    hidden_job = json.loads(job_path.read_text())
    hidden_job["evaluate_bank"] = "hidden"
    (tmp_path / "hidden.json").write_text(json.dumps(hidden_job))
    assert cli.main(["run-one", "--job", str(tmp_path / "hidden.json"), "--prepared", str(env.prepared),
                     "--recipe", str(recipe_path), "--out", str(tmp_path / "cli-hidden")]) == 2
    assert not (tmp_path / "cli-hidden").exists()
