"""B10's CPU equivalence test (the certification plan's CPU part, D2) on ENGINEERING FIXTURES: a deterministic
train-only regeneration equals a Gate-A-like a0 unit's q and e1 fingerprints, in Gate A's two forms (one job from
init; the init unit and an e1 continuation); the certify evaluation of the regenerated e1 state writes the Gate-A-like
unit's evaluation files byte for byte (and the engine's own eval-state's), so U is reproduced exactly; the comparison
passes, and fails on one changed guard label; lambda = 0 reproduces the untuned unit. None of these numbers is a
scientific result."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402

from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import read_json, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

UNSAFE = "Safety: Unsafe\nCategories: Violent\nRefusal: No"


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("b10-world")
    prepared, manifest = fb.prepared(base)
    one = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", 1102)
    resumed, init = fb.gate_a_resumed(prepared, base / "units" / "1101-a0-e1-a1", 1101)
    settings = fb.fixture_settings(manifest, {1101: resumed, 1102: one}, untuned=init)
    cert = fb.certification(prepared, resumed, settings, base / "certification")          # seed 1101
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, units={1101: resumed, 1102: one},
                        init=init, settings=settings, cert=cert)


def regenerate(world, root: Path, seed: int, settings=None) -> dict:
    return ea.regenerate(prepared_dir=world.prepared, seed=seed, reference_path=world.units[seed] / "COMPLETE.json",
                         out_root=root, session=fb.session(), settings=settings or world.settings)


def certify(world, source: Path, out: Path, settings=None, session=None, plan=None) -> dict:
    settings = settings or world.settings
    plan = plan or ea.make_plan(settings, "certify")
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=source,
                       reference_path=world.units[read_json(source / "job.json")["seed"]] / "COMPLETE.json",
                       recipe=fb.recipe(), settings=settings, plan=plan,
                       certification=None if plan.mode == "certify" else world.cert)
    return ea.evaluate(ctx, out_dir=out, session=session or fb.session())


@pytest.mark.parametrize("seed", [1101, 1102], ids=["resumed-form", "one-job-form"])
def test_the_regeneration_matches_the_gate_a_record_and_certify_reproduces_its_files_byte_for_byte(world, tmp_path, seed):
    record = regenerate(world, tmp_path / "regen", seed)
    assert record["verdict"] == "match" and record["comparison"]["equal"] and not record["comparison"]["differing"]
    for name in ("q", "e1"):
        pair = record["comparison"]["adapter_fingerprints"][name]
        assert pair["candidate"] == pair["reference"] is not None
    assert record["comparison"]["report_only"] == {"checkpoints.q.optimizer_fingerprint": True,
                                                   "checkpoints.e1.optimizer_fingerprint": True,
                                                   "identity.recipe_sha256": True}
    run = tmp_path / "regen" / "run"
    job = read_json(run / "job.json")
    assert job["evaluate_bank"] is None and job["code_sha256"] is not None and job["replicate_of"] is None
    assert not (run / "eval").exists() and not list(tmp_path.rglob("registry.jsonl"))       # train-only, no claim
    assert json.loads((tmp_path / "regen" / "regeneration.json").read_bytes()) == record
    result = certify(world, run, tmp_path / "cert")
    assert result["complete"] and result["mode"] == "certify" and result["adapter_scale"] == 1.0
    assert result["evaluated_adapter_fingerprint"] == result["source_adapter_fingerprint"]
    mine, gate_a = fb.eval_dir(tmp_path / "cert"), fb.eval_dir(world.units[seed])
    for name in fb.EVAL_FILES:
        assert (mine / name).read_bytes() == (gate_a / name).read_bytes(), name
    assert fb.summary_without_timing(tmp_path / "cert") == fb.summary_without_timing(world.units[seed])
    report = ea.compare_certification(tmp_path / "cert", world.units[seed] / "COMPLETE.json", gate_a, world.settings)
    assert report["verdict"] == "pass"
    assert report["gate"] == {"answers_reference": 6, "answers_unit": 6, "expected_answers": 6, "same_answer_set": True,
                              "differing_gate_labels": 0, "gate_fields": ["valid", "safety"], "unsafe_equal": True}
    d = report["diagnostics"]
    assert d["sampled"] == {"n": 6, "identical_outputs": 6, "identical_seeds": 6}
    assert d["task_loss"]["bitwise_equal"] == d["task_loss"]["n"] == 16 and d["task_loss"]["max_abs_difference"] == 0
    assert d["greedy_guard_agreement"]["agree"] == d["greedy_guard_agreement"]["n"] == 9
    assert all(v["identical_outputs"] == v["n"] for v in d["greedy"].values())
    assert ea.verify_unit(tmp_path / "cert")["complete"]


def test_certify_equals_the_engines_own_eval_state_of_the_regenerated_state(world, tmp_path):
    regenerate(world, tmp_path / "regen", 1102)
    run = tmp_path / "regen" / "run"
    certify(world, run, tmp_path / "cert")
    recipe = fb.recipe()
    job = {"kind": "eval-state", "source_run": str(run), "checkpoint": "e1", "evaluate_bank": "dev",
           "manifest_sha256": world.manifest, "recipe_sha256": config_sha256(recipe), "code_sha256": None,
           "wall_limit_seconds": None}
    out = runner.eval_state(job, prepared_dir=world.prepared, out_dir=tmp_path / "engine", session=fb.session())
    for name in fb.EVAL_FILES:
        assert (fb.eval_dir(tmp_path / "cert") / name).read_bytes() == (fb.eval_dir(Path(out["run_dir"])) / name).read_bytes()


def test_one_process_regeneration_then_certify_also_reproduces_the_files(world, tmp_path):
    session = fb.session()
    ea.regenerate(prepared_dir=world.prepared, seed=1102, reference_path=world.units[1102] / "COMPLETE.json",
                  out_root=tmp_path / "regen", session=session, settings=world.settings)
    certify(world, tmp_path / "regen" / "run", tmp_path / "cert", session=session)
    for name in fb.EVAL_FILES:
        assert (fb.eval_dir(tmp_path / "cert") / name).read_bytes() == (fb.eval_dir(world.units[1102]) / name).read_bytes()


def test_the_comparison_fails_when_one_guard_label_differs(world, tmp_path):
    regenerate(world, tmp_path / "regen", 1102)
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=tmp_path / "regen" / "run",
                       reference_path=world.units[1102] / "COMPLETE.json", recipe=fb.recipe(),
                       settings=world.settings, plan=ea.make_plan(world.settings, "certify"))
    folder = fb.eval_dir(world.units[1102])
    texts = [json.loads(line)["text"] for name in ("samples.jsonl", "generations.jsonl")
             for line in (folder / name).read_text().splitlines()]
    # the scripted guard maps an answer that CONTAINS a key to a literal answer: key one sampled answer only
    sampled = [json.loads(line)["text"] for line in (folder / "samples.jsonl").read_text().splitlines()]
    scored = [json.loads(line)["valid"] for line in (folder / "guard_samples.jsonl").read_text().splitlines()]
    keys = [t for t, ok in zip(sampled, scored) if ok and t and sum(t in other for other in texts) == 1]
    assert keys, "the fixture needs one sampled answer that no other answer contains"
    ea.evaluate(ctx, out_dir=tmp_path / "cert", session=fb.session(guard_answers={keys[0]: UNSAFE}))
    report = ea.compare_certification(tmp_path / "cert", world.units[1102] / "COMPLETE.json", folder, world.settings)
    assert report["verdict"] == "fail" and report["gate"]["differing_gate_labels"] == 1
    assert report["gate"]["unsafe_equal"] is False and report["diagnostics"]["sampled"]["identical_outputs"] == 6


def test_the_comparison_refuses_a_reference_file_that_is_not_the_gate_a_units(world, tmp_path):
    regenerate(world, tmp_path / "regen", 1102)
    certify(world, tmp_path / "regen" / "run", tmp_path / "cert")
    copy = tmp_path / "ref-eval"
    shutil.copytree(fb.eval_dir(world.units[1102]), copy)
    rows = (copy / "guard_samples.jsonl").read_text().splitlines()
    record = json.loads(rows[0])
    record["safety"] = "Unsafe" if record["safety"] != "Unsafe" else "Safe"
    rows[0] = json.dumps(record)
    (copy / "guard_samples.jsonl").write_text("\n".join(rows) + "\n")
    with pytest.raises(ea.Refusal, match="not the Gate A unit's file"):
        ea.compare_certification(tmp_path / "cert", world.units[1102] / "COMPLETE.json", copy, world.settings)
    (copy / "guard_samples.jsonl").unlink()
    with pytest.raises(ea.Refusal, match="missing"):
        ea.compare_certification(tmp_path / "cert", world.units[1102] / "COMPLETE.json", copy, world.settings)


def test_the_comparison_needs_the_expected_answer_count(world, tmp_path):
    settings = fb.fixture_settings(world.manifest, world.units, untuned=world.init,
                                   certification__expected_sampled_answers=600)
    regenerate(world, tmp_path / "regen", 1102, settings=settings)
    certify(world, tmp_path / "regen" / "run", tmp_path / "cert", settings=settings)
    report = ea.compare_certification(tmp_path / "cert", world.units[1102] / "COMPLETE.json",
                                      fb.eval_dir(world.units[1102]), settings)
    assert report["verdict"] == "fail" and report["gate"]["differing_gate_labels"] == 0
    with pytest.raises(ea.Refusal, match="another B10 script or settings"):      # compared under other settings
        ea.compare_certification(tmp_path / "cert", world.units[1102] / "COMPLETE.json",
                                 fb.eval_dir(world.units[1102]), world.settings)


def test_lambda_zero_reproduces_the_untuned_unit(world, tmp_path):
    regenerate(world, tmp_path / "regen", 1101)
    plan = ea.make_plan(world.settings, "scale", adapter_scale=0.0)
    certify(world, tmp_path / "regen" / "run", tmp_path / "zero", plan=plan)
    mine, untuned = fb.eval_dir(tmp_path / "zero"), fb.eval_dir(world.init, "init")
    for name in fb.EVAL_FILES:
        assert (mine / name).read_bytes() == (untuned / name).read_bytes(), name
    report = ea.compare_certification(tmp_path / "zero", world.init / "COMPLETE.json", untuned, world.settings,
                                      against="untuned")
    assert report["verdict"] == "pass" and report["against"] == "untuned"
    with pytest.raises(ea.Refusal, match="not a certification unit"):
        ea.compare_certification(tmp_path / "zero", world.units[1101] / "COMPLETE.json",
                                 fb.eval_dir(world.units[1101]), world.settings)


def test_a_certify_unit_is_not_compared_with_the_untuned_unit(world, tmp_path):
    regenerate(world, tmp_path / "regen", 1101)
    certify(world, tmp_path / "regen" / "run", tmp_path / "cert")
    with pytest.raises(ea.Refusal, match="lambda = 0"):
        ea.compare_certification(tmp_path / "cert", world.init / "COMPLETE.json", fb.eval_dir(world.init, "init"),
                                 world.settings, against="untuned")


def test_the_unit_records_its_source_reference_settings_and_script(world, tmp_path):
    regenerate(world, tmp_path / "regen", 1102)
    certify(world, tmp_path / "regen" / "run", tmp_path / "cert")
    unit = tmp_path / "cert"
    job, marker = read_json(unit / "job.json"), read_json(unit / "COMPLETE.json")
    assert ea.validate_job(job) == job and job["mode"] == "certify" and job["seed"] == 1102
    assert job["reference_complete_sha256"] == sha256_file(world.units[1102] / "COMPLETE.json")
    assert job["settings_sha256"] == world.settings.sha256
    assert job["script_sha256"] == sha256_file(Path(ea.__file__))
    assert marker["kind"] == ea.JOB_KIND and marker["source_complete_sha256"] == sha256_file(
        tmp_path / "regen" / "run" / "COMPLETE.json")
    identity = read_json(unit / "identity.json")
    assert identity["b10"]["settings_sha256"] == world.settings.sha256 and identity["b10"]["mode"] == "certify"
    deps = read_json(unit / "dependencies.json")["dependencies"]
    assert [d["role"] for d in deps] == ["source_run"] and deps[0]["checkpoint"] == "e1"
    stages = marker["costs"]["stage_seconds"]
    assert {"restore_state", "query_loss", "generate", "sample", "guard", "guard_samples", "harm_scores"} <= set(stages)
    assert "train" not in stages and "adapter_transform" not in stages
