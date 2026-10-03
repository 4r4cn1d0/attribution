"""The real EngineBackend end to end on the engine's ENGINEERING FIXTURES (tiny random Qwen2 +
LoRA on CPU, byte codec, scripted guard, tiny guard LM): development calibration runs, guard
features, the selector view, attribution and the relevance table feed the development table and
record through the verified readers; one confirmation-mode block then runs through the engine API
(make_job with the pinned code, run_one/attributes/score_groups in one Session, the registry),
with the choice lock before the reference-role hidden evaluation; a relocated tree verifies
read-only through a path map. None of these numbers is a scientific result."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")
pytest.importorskip("numpy")

import ss_fixtures as fx  # noqa: E402

from experiments.safety_decision_policy.backend import EngineBackend  # noqa: E402
from experiments.safety_decision_policy.common import (LockError, PolicyError, VerificationError,  # noqa: E402
                                                       canonical_json, engine_code_identity, policy_code_identity,
                                                       read_canonical, read_json, read_json_strict, sha256_file,
                                                       write_once)
from experiments.safety_decision_policy.config import EXAMPLE_STATUS, FROZEN_STATUS, check_feasibility  # noqa: E402
from experiments.safety_decision_policy.controller import Study, verify_study  # noqa: E402
from experiments.safety_decision_policy.costs import shape_from_plan  # noqa: E402
from experiments.safety_decision_policy.development import INDEX_KIND, build_table, fit_record  # noqa: E402
from experiments.safety_decision_policy.features import TARGETS  # noqa: E402
from experiments.safety_decision_policy.outcomes import OUTCOME_PIN, read_evaluation  # noqa: E402
from experiments.safety_decision_policy.policy import Op  # noqa: E402
from experiments.safety_decision_policy.tfidf import build_relevance  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from experiments.safety_selection.planning import build_plan  # noqa: E402
from experiments.safety_selection.selector_view import export_selector_view  # noqa: E402
from experiments.safety_selection.verify import PathMap  # noqa: E402

CONFIGS = Path(__file__).resolve().parents[1] / "configs"
SEEDS = [1101, 1102]


def _job(sha: str, recipe: dict, **fields) -> dict:
    return {"manifest_sha256": sha, "recipe_sha256": config_sha256(recipe), "code_sha256": None,
            "wall_limit_seconds": None, **fields}


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("engine")
    prepared, sha = fx.prepare_dir(root / "prepared")
    recipe = fx.recipe()
    session = runner.Session(recipe, fx.fixture_loaders())
    groups = json.loads((prepared / "engine" / "groups.json").read_text())["partitions"]["dev"]["menu"][1:]
    arms = ["a0", *groups]
    calibration = runner.calibrate(prepared_dir=prepared, out_root=root / "calibration", session=session,
                                   arms=arms, seeds=SEEDS, checkpoints=["q", "e3"])
    units = {(u["seed"], u["arm"], u["checkpoint"]): u["run_dir"] for u in calibration["units"]}
    guard_run = runner.score_groups(_job(sha, recipe, kind="score-groups", split="dev"), prepared_dir=prepared,
                                    out_dir=root / "guard-dev", session=session)["run_dir"]
    view = export_selector_view(prepared, guard_run, root / "view-dev.json", root / "view-dev-receipt.json")
    attribution = {}
    for seed in SEEDS:
        job = _job(sha, recipe, kind="attributes", split="dev", seed=seed, role="development", group_ids=groups,
                   query_bank="ref", a0_states={"q": units[seed, "a0", "q"], "e1": units[seed, "a0", "e3"],
                                                "e3": units[seed, "a0", "e3"]})
        attribution[seed] = runner.attributes(job, prepared_dir=prepared, out_dir=root / f"attr-{seed}",
                                              session=session)["run_dir"]
    data, relevance = build_relevance(prepared, sha)
    write_once(root / "relevance.json", data)
    index = {"kind": INDEX_KIND, "split": "dev", "short_checkpoint": "q", "full_checkpoint": "e3",
             "selector_view": {"path": str(root / "view-dev.json"), "sha256": view["view_sha256"]},
             "relevance": {"path": str(root / "relevance.json"), "sha256": relevance["table_sha256"]},
             "seeds": SEEDS,
             "runs": {fid: {arm: {str(s): units[s, arm, ckpt] for s in SEEDS} for arm in arms}
                      for fid, ckpt in (("short", "q"), ("full", "e3"))},
             "attribution": {str(s): attribution[s] for s in SEEDS}, "path_map": []}
    table = build_table(index, prepared_dir=prepared, recipe=recipe)
    table_sha = write_once(root / "table.json", canonical_json(table))
    record = fit_record([(table, table_sha)], read_json_strict(CONFIGS / "example-dev-fit-spec.json"))
    record_sha = write_once(root / "record.json", canonical_json(record))
    entry = record["tables"][0]
    attr = entry["selection"]["attribution"]
    pins = {"engine_code_sha256": engine_code_identity()["sha256"],
            "policy_code_sha256": policy_code_identity()["sha256"], "manifest_sha256": sha,
            "recipe_sha256": config_sha256(recipe), "development_table_sha256": table_sha,
            "development_record_sha256": record_sha,
            "relevance_fingerprint_sha256": record["relevance_fingerprint_sha256"]}
    config = read_json_strict(CONFIGS / "example-engineering.json")
    config.update(status=FROZEN_STATUS, freeze=True, pins=pins, outcome_definition=dict(OUTCOME_PIN),
                  name="ENGINEERING FIXTURE test configuration",
                  purpose="ENGINEERING FIXTURE: exercises the engine backend on CPU fixtures; not scientific")
    config["features"]["attribution"] = attr
    config["predictor"]["development_groups"] = len(entry["groups"])
    config["predictor"]["selected_lambda"] = {
        "S-": {t: entry["fits"]["S-"]["targets"][t]["selected_lambda"] for t in TARGETS},
        "S+": {t: entry["fits"][f"S+/{attr}"]["targets"][t]["selected_lambda"] for t in TARGETS}}
    config["blocks"] = {"count": 1, "schedule_seed": 7,
                        "list": [{"block": 0, "selector_seed_start": 2101, "selector_seed_stride": 1, "final_seed": 9101}]}
    config["analysis"]["sensitivity"] = []
    shape = shape_from_plan(build_plan(recipe, prepared), "heldout", recipe)
    config["budget"]["total_quote_seconds"] = 10 ** 9
    feasible = check_feasibility(config, shape)["S+"]
    config["budget"]["total_quote_seconds"] = feasible["fixed_including_reserve"] + feasible["worst_initial_top_two"] + 1500
    data_config = json.loads((prepared / "manifest.json").read_text())["data_config"]
    study_root = root / "study"
    backend = EngineBackend(prepared_dir=prepared, recipe=recipe, session=session, registry=study_root / "registry.jsonl")
    kwargs = {"record": record, "recipe": recipe, "data_config": data_config, "shape": shape, "actual_pins": pins}
    study = Study(study_root, config=config, backend=backend, process_start=backend.clock(), **kwargs)
    try:
        result = study.run_block(0)
    finally:
        study.close()
    return SimpleNamespace(root=root, prepared=prepared, sha=sha, recipe=recipe, session=session, units=units,
                           table=table, record=record, config=config, kwargs=kwargs, backend=backend,
                           study_root=study_root, result=result)


def test_the_development_table_and_record_come_from_verified_engine_runs(env):
    assert len(env.table["rows"]) == 3 * len(SEEDS) and env.table["seeds"] == SEEDS
    row = env.table["rows"][0]
    short_run = Path(row["artifacts"]["short"]["edit"]["run"])
    assert row["artifacts"]["short"]["edit"]["complete_sha256"] == sha256_file(short_run / "COMPLETE.json")
    assert env.record["tables"][0]["selection"]["attribution"] in ("checkpoint_gradsim", "adam_diag_preconditioned_dot")
    run = env.units[1101, "a0", "q"]
    expect = {"split": "dev", "arm": "a0", "seed": 1101, "role": "development", "checkpoint": "q", "bank": "dev",
              "manifest_sha256": env.sha, "recipe_sha256": config_sha256(env.recipe),
              "code_sha256": engine_code_identity()["sha256"]}
    assert read_evaluation(run, expect=expect, prepared_dir=env.prepared).seed == 1101
    with pytest.raises(VerificationError):
        read_evaluation(run, expect={**expect, "seed": 1102}, prepared_dir=env.prepared)
    with pytest.raises(VerificationError):
        read_evaluation(run, expect={**expect, "checkpoint": "e3"}, prepared_dir=env.prepared)


def test_a_tampered_engine_summary_is_refused(env, tmp_path):
    copy = Path(shutil.copytree(env.units[1101, "a0", "q"], tmp_path / "copy"))
    summary = copy / "eval" / "q" / "summary.json"
    data = read_json(summary)
    data["safety"]["guard_unsafe"] += 1
    summary.write_text(json.dumps(data))
    expect = {"split": "dev", "arm": "a0", "seed": 1101, "role": "development", "checkpoint": "q", "bank": "dev",
              "manifest_sha256": env.sha, "recipe_sha256": config_sha256(env.recipe),
              "code_sha256": engine_code_identity()["sha256"]}
    with pytest.raises(VerificationError):
        read_evaluation(copy, expect=expect)


def test_a_confirmation_block_runs_through_the_engine_with_the_lock_before_hidden_evaluation(env):
    assert env.result["status"] == "complete"
    ops = env.study_root / "blocks" / "0" / "ops"
    lock_sha = sha256_file(env.study_root / "blocks" / "0" / "lock.json")
    code = engine_code_identity()["sha256"]
    finals = sorted(ops.glob("final-*"))
    assert finals
    for folder in finals:
        assert read_canonical(folder / "spec.json")["lock_sha256"] == lock_sha
        job = read_json(folder / "attempt-1" / "job.json")
        assert (job["split"], job["role"], job["evaluate_bank"], job["seed"], job["code_sha256"]) == (
            "heldout", "reference", "hidden", 9101, code)
    for folder in ops.glob("screen-*"):
        job = read_json(folder / "attempt-1" / "job.json")
        assert (job["role"], job["evaluate_bank"], job["target_checkpoint"], job["code_sha256"]) == (
            "selector", "selector", "q", code)
    attribution = read_json(next(ops.glob("attribution-*")) / "attempt-1" / "job.json")
    recorded = ops.resolve()
    assert attribution["role"] == "selector" and set(attribution["a0_states"]) == {"q", "e1", "e3"}
    assert attribution["a0_states"]["q"] == str(recorded / "screen-a0-2101" / "attempt-1" / "run")
    assert attribution["a0_states"]["e3"] == str(recorded / "full_from_short-a0-2101" / "attempt-1" / "run")
    lock = read_canonical(env.study_root / "blocks" / "0" / "lock.json")
    assert {m: lock["methods"][m]["choice"]["choice"] for m in ("S-", "S+")} == env.result["choices"]
    assert verify_study(env.study_root, EngineBackend(prepared_dir=env.prepared, recipe=env.recipe))["complete"]


def test_examples_and_lockless_final_access_are_refused_with_the_engine(env, tmp_path):
    example = {**env.config, "status": EXAMPLE_STATUS, "freeze": False}
    with pytest.raises(PolicyError):
        Study(tmp_path / "study", config=example, backend=env.backend, process_start=0.0, **env.kwargs)
    study = Study(tmp_path / "other", config=env.config, backend=env.backend, process_start=0.0, **env.kwargs)
    spec = study.spec(Op("final", "a0", 9101), 0, lock_sha256="0" * 64)
    study.close()
    (tmp_path / "attempt-1").mkdir()
    with pytest.raises(LockError):
        env.backend.execute(spec, tmp_path / "attempt-1", {})
    assert not (tmp_path / "attempt-1" / "run").exists()


def test_a_registry_refusal_after_a_killed_process_is_a_bounded_charged_failure(env, tmp_path):
    """A trajectory left live by a killed engine process (no error.txt) makes the engine refuse a
    fresh start: fail-closed, recorded as a timed technical failure of the same draw and retried
    only up to the bound; the registry is never cleared and no fresh seed is drawn."""
    from experiments.safety_selection.common import append_jsonl
    from experiments.safety_selection.jobs import trajectory_key

    root, killed = tmp_path / "study", tmp_path / "killed-run"
    killed.mkdir()
    root.mkdir()
    registry = root / "registry.jsonl"
    append_jsonl(registry, {"key": trajectory_key(env.sha, env.recipe, "heldout", "a0", 2101, "selector"),
                            "run_dir": str(killed), "replicate_of": None, "retry_after_failures": [],
                            "utc": "2026-10-02T00:00:00Z"})
    before = registry.read_bytes()
    backend = EngineBackend(prepared_dir=env.prepared, recipe=env.recipe, session=env.session, registry=registry)
    study = Study(root, config=env.config, backend=backend, process_start=backend.clock(), **env.kwargs)
    try:
        assert study.ensure_op(Op("screen", "a0", 2101), 0) is None
        assert study.ensure_op(Op("screen", "a0", 2101), 0) is None   # exhausted: no third attempt
    finally:
        study.close()
    folder = root / "blocks" / "0" / "ops" / "screen-a0-2101"
    receipts = [read_canonical(p / "receipt.json") for p in sorted(folder.glob("attempt-*"))]
    assert [r["status"] for r in receipts] == ["failed", "failed"]
    assert all("already started" in r["error"] and r["seconds"] > 0 for r in receipts)
    assert registry.read_bytes() == before


def test_a_relocated_study_verifies_read_only_through_a_path_map(env, tmp_path):
    archive = Path(shutil.copytree(env.study_root, tmp_path / "archive"))
    before = {p.relative_to(archive): sha256_file(p) for p in sorted(archive.rglob("*")) if p.is_file()}
    recorded = env.study_root.resolve()  # receipts hold resolved absolute paths
    hidden = env.study_root.with_name("study-moved-away")
    env.study_root.rename(hidden)
    try:
        mapped = EngineBackend(prepared_dir=env.prepared, recipe=env.recipe,
                               path_map=PathMap([(recorded, archive)]))
        assert verify_study(archive, mapped)["complete"]
        unmapped = EngineBackend(prepared_dir=env.prepared, recipe=env.recipe)
        assert not verify_study(archive, unmapped)["complete"]
    finally:
        hidden.rename(env.study_root)
    after = {p.relative_to(archive): sha256_file(p) for p in sorted(archive.rglob("*")) if p.is_file()}
    assert after == before
