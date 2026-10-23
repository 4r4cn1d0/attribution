"""B10's fix round (notes/B10-verify.md) on ENGINEERING FIXTURES: the verifier's gap tests (S-6) and gate-folder probe
(S-1); exit 1 once this process wrote anything; the certification binding of every evaluation other than certify
(S-2: the engine, the script's code, the certified settings and the environment); the config hash as a reported
field (S-3); the identity-transform certification point (S-4); the over-refusal bank gate (B-1); and tests for the
verifier's low-risk survivors (N-3). None of these numbers is a scientific result."""

from __future__ import annotations

import copy
import dataclasses
import json
import shutil
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402

from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import canonical_json, ids_sha256, read_json, sha256_file  # noqa: E402
from experiments.safety_selection.ledger import verify_files  # noqa: E402
from experiments.safety_selection.textproc import encode_mc  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

SETTINGS_STAND_IN = "scripts/stage1_s1/tests/b10_transform_fixture.py"   # any pinned repository file
FILE_KEYS = {"transform_sha256": "transform.sha256", "source_adapter_fingerprint": "source.fingerprint",
             "output_adapter_fingerprint": "output.fingerprint", "output_file_sha256": "output.file_sha256"}
UNSAFE = "Safety: Unsafe\nCategories: Violent\nRefusal: No"


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("b10-fixround")
    prepared, manifest = fb.prepared(base)
    one = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", 1102)
    resumed, init = fb.gate_a_resumed(prepared, base / "units" / "1101-a0-e1-a1", 1101)
    units = {1101: resumed, 1102: one}
    recipe_file = base / "recipe.json"
    recipe_file.write_bytes(canonical_json(fb.recipe()))
    externals = {name: fb.transform_entry(name) for name in ("identity", "half_b", "inplace_half_b")}
    externals["file_any"] = fb.transform_entry(None, kind="file", record_keys=dict(FILE_KEYS))
    externals["file_pinned_wrong"] = dict(
        fb.transform_entry(None, kind="file", record_keys={**FILE_KEYS,
                                                            "transform_settings_sha256": "transform.settings_sha256"}),
        settings={"path": SETTINGS_STAND_IN, "sha256": "7" * 64})          # the pin is not the file's hash
    settings = fb.fixture_settings(manifest, units, untuned=init, external_transforms=externals,
                                   recipe__file_sha256=sha256_file(recipe_file))
    regen = {}
    for seed in (1101, 1102):
        ea.regenerate(prepared_dir=prepared, seed=seed, reference_path=units[seed] / "COMPLETE.json",
                      out_root=base / f"regen-{seed}", session=fb.session(), settings=settings)
        regen[seed] = base / f"regen-{seed}" / "run"
    cert = fb.certification(prepared, resumed, settings, base / "certification", source=regen[1101])   # seed 1101
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, units=units, init=init, settings=settings,
                        regen=regen, cert=cert, recipe=recipe_file)


def evaluate(world, out: Path, plan, *, seed: int = 1102, settings=None, certification="world", session=None,
             source: Path | None = None) -> dict:
    settings = settings or world.settings
    cert = world.cert if certification == "world" else certification
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=source or world.regen[seed],
                       reference_path=world.units[seed] / "COMPLETE.json", recipe=fb.recipe(), settings=settings,
                       plan=plan, certification=None if plan.mode == "certify" else cert)
    return ea.evaluate(ctx, out_dir=out, session=session or fb.session())


def cli(world, argv, settings=None, **loader_options) -> int:
    return ea.main([str(a) for a in argv], _settings=settings or world.settings,
                   _loaders=fb.fx.fixture_loaders(**loader_options))


def common(world, seed: int) -> list:
    return ["--prepared", world.prepared, "--recipe", world.recipe, "--reference",
            world.units[seed] / "COMPLETE.json"]


def file_inputs(world, folder: Path, *, seed: int = 1102, scale: float = 0.5, name: str = "file_any",
                settings_sha256: str | None = None) -> dict:
    from safetensors.torch import load_file, save_file

    source = load_file(str(world.regen[seed] / "states" / "e1" / "adapter.safetensors"))
    new = {k: (v * scale if ".lora_B." in k else v) for k, v in source.items()} if scale != 1.0 else dict(source)
    folder.mkdir(parents=True, exist_ok=True)
    adapter = folder / "adapter.safetensors"
    save_file(new, str(adapter))
    record = {"transform": {"sha256": sha256_file(ea.REPO / fb.TRANSFORM_MODULE)},
              "source": {"fingerprint": ea.adapter_fingerprint(source)},
              "output": {"fingerprint": ea.adapter_fingerprint(new), "file_sha256": sha256_file(adapter)}}
    if settings_sha256 is not None:
        record["transform"]["settings_sha256"] = settings_sha256
    path = folder / "record.json"
    path.write_bytes(canonical_json(record))
    return dict(external=name, adapter_file=str(adapter), adapter_sha256=sha256_file(adapter), record_file=str(path),
                record_sha256=sha256_file(path))


def certify_unit(world, out: Path, seed: int = 1102) -> Path:
    evaluate(world, out, ea.make_plan(world.settings, "certify"), seed=seed)
    return out


def env_session(environment: dict):
    loaders = dataclasses.replace(fb.fx.fixture_loaders(), environment=lambda device: copy.deepcopy(environment))
    return runner.Session(fb.recipe(), loaders)


# ----- S-6: the verifier's gap tests (each kills its surviving mutant) ------------------------------------------


def test_the_gate_fails_when_the_answer_sets_differ(world, tmp_path):
    unit = world.units[1102]
    ref_eval = tmp_path / "ref-eval"
    shutil.copytree(fb.eval_dir(unit), ref_eval)
    rows = (ref_eval / "guard_samples.jsonl").read_text().splitlines()
    rows.remove(next(r for r in rows if json.loads(r).get("safety") != "Unsafe"))
    (ref_eval / "guard_samples.jsonl").write_text("\n".join(rows) + "\n")
    marker = json.loads((unit / "COMPLETE.json").read_bytes())
    marker["files"]["eval/e1/guard_samples.jsonl"] = sha256_file(ref_eval / "guard_samples.jsonl")
    complete = tmp_path / "COMPLETE.json"
    complete.write_bytes(canonical_json(marker))
    doc = fb.fixture_doc(world.manifest, {1102: unit})
    doc["reference_units"]["1102"]["complete_sha256"] = sha256_file(complete)
    doc["certification"]["expected_sampled_answers"] = len(rows)
    settings = ea.settings_from_doc(doc)
    ea.regenerate(prepared_dir=world.prepared, seed=1102, reference_path=complete, out_root=tmp_path / "regen",
                  session=fb.session(), settings=settings)
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=tmp_path / "regen" / "run", reference_path=complete,
                       recipe=fb.recipe(), settings=settings, plan=ea.make_plan(settings, "certify"))
    ea.evaluate(ctx, out_dir=tmp_path / "cert", session=fb.session())
    report = ea.compare_certification(tmp_path / "cert", complete, ref_eval, settings)
    assert report["gate"]["same_answer_set"] is False and report["gate"]["differing_gate_labels"] == 0
    assert report["gate"]["unsafe_equal"] is True and report["verdict"] == "fail"


def test_prefix_mode_checks_an_arc_items_original_encoding(world):
    codec, recipe = fb.fx.fixture_codec(), fb.recipe()
    settings = fb.fixture_settings(world.manifest, {1102: world.units[1102]}, prefix__text_sha256="a" * 64,
                                   prefix__source="ENGINEERING FIXTURE placeholder")
    prefix = {"text": "P", "sha256": "a" * 64, "insert": "P\n\n"}
    labels, texts = ["A", "B"], ["one", "two"]
    good, _ = encode_mc(codec, "q?", labels, texts, 400)
    item = {"kind": "arc_utility", "prompt_id": "a1", "question": "q?", "labels": labels, "texts": texts,
            "answer": "A", "token_sha256": ids_sha256(good)}
    ea.build_prefix(codec, prefix, settings, [item], [], recipe)
    with pytest.raises(ea.Refusal, match="token audit"):
        ea.build_prefix(codec, prefix, settings, [{**item, "token_sha256": "0" * 64}], [], recipe)


def test_prefix_mode_checks_a_task_rows_original_encoding(world):
    from experiments.safety_selection.prepare import load_prepared
    from experiments.safety_selection.sources import DataError

    codec, recipe = fb.fx.fixture_codec(), fb.recipe()
    settings = fb.fixture_settings(world.manifest, {1102: world.units[1102]}, prefix__text_sha256="a" * 64,
                                   prefix__source="ENGINEERING FIXTURE placeholder")
    prefix = {"text": "P", "sha256": "a" * 64, "insert": "P\n\n"}
    row = dict(load_prepared(world.prepared, banks=("dev",)).query_rows[0])
    ea.build_prefix(codec, prefix, settings, [], [row], recipe)
    with pytest.raises(DataError, match="token audit"):
        ea.build_prefix(codec, prefix, settings, [], [{**row, "token_sha256": "0" * 64}], recipe)


# ----- S-1: the gate folder before any work; exit 1 once anything was written --------------------------------


def gated(world, tmp_path, gate: Path, specs: str = "certify,scale:0.5", seed: int = 1101) -> list:
    return ["run", *common(world, seed), "--seed", seed, "--regen-out", tmp_path / "regen", "--eval-root",
            tmp_path / "eval", "--evaluations", specs, "--gate-reference-eval", gate]


def test_a_gated_run_with_a_wrong_gate_folder_refuses_before_any_training(world, tmp_path):
    (tmp_path / "empty").mkdir()
    assert cli(world, gated(world, tmp_path, tmp_path / "empty")) == 2
    assert not (tmp_path / "regen" / "run").exists(), "exit 2 promises that nothing was trained"
    assert not (tmp_path / "eval").exists()


def test_a_gated_run_with_a_changed_diagnostic_file_refuses_before_any_training(world, tmp_path):
    gate = tmp_path / "gate"
    shutil.copytree(fb.eval_dir(world.units[1101]), gate)
    with (gate / "samples.jsonl").open("a") as handle:
        handle.write("\n")
    assert cli(world, gated(world, tmp_path, gate)) == 2
    assert not (tmp_path / "regen").exists() and not (tmp_path / "eval").exists()
    with pytest.raises(ea.Refusal, match="samples.jsonl is not the Gate A unit's file"):
        ea.run_sequence(prepared_dir=world.prepared, seed=1101, reference_path=world.units[1101] / "COMPLETE.json",
                        regen_root=tmp_path / "regen", eval_root=tmp_path / "eval",
                        plans=[ea.make_plan(world.settings, "certify")], session=fb.session(), settings=world.settings,
                        gate_reference_eval=gate)
    assert not (tmp_path / "regen").exists()


def test_a_failure_after_the_regeneration_exits_1_even_into_existing_empty_folders(world, tmp_path, monkeypatch):
    (tmp_path / "regen").mkdir()
    (tmp_path / "eval").mkdir()

    def refuse(*args, **kwargs):
        raise ea.Refusal("an injected refusal after the certify evaluation")

    monkeypatch.setattr(ea, "compare_certification", refuse)
    assert cli(world, gated(world, tmp_path, fb.eval_dir(world.units[1101]))) == 1
    assert (tmp_path / "regen" / "run" / "COMPLETE.json").is_file()


def test_a_gated_run_never_overwrites_an_earlier_comparison_file(world, tmp_path):
    (tmp_path / "eval").mkdir()
    (tmp_path / "eval" / "1101-certify.compare.json").write_text("{}")         # some earlier unit's binding
    assert cli(world, gated(world, tmp_path, fb.eval_dir(world.units[1101]))) == 2
    assert not (tmp_path / "regen").exists()
    assert (tmp_path / "eval" / "1101-certify.compare.json").read_text() == "{}"


def test_an_old_error_file_does_not_turn_a_refusal_into_exit_1(world, tmp_path):
    (tmp_path / "eval" / "old-unit").mkdir(parents=True)
    (tmp_path / "eval" / "old-unit" / "error.txt").write_text("an earlier failure")
    (tmp_path / "empty").mkdir()
    assert cli(world, gated(world, tmp_path, tmp_path / "empty")) == 2
    assert sorted(p.name for p in (tmp_path / "eval").iterdir()) == ["old-unit"]


# ----- S-2: every evaluation but certify runs under a bound, passing certification ------------------------------


def test_an_evaluation_other_than_certify_needs_a_certification_and_certify_takes_none(world, tmp_path):
    with pytest.raises(ea.Refusal, match="only under a passing certification report"):
        evaluate(world, tmp_path / "x", ea.make_plan(world.settings, "scale", adapter_scale=0.5), certification=None)
    with pytest.raises(ea.Refusal, match="the certify mode takes none"):
        ea.preflight(prepared_dir=world.prepared, source_run=world.regen[1102],
                     reference_path=world.units[1102] / "COMPLETE.json", recipe=fb.recipe(), settings=world.settings,
                     plan=ea.make_plan(world.settings, "certify"), certification=world.cert)
    assert not (tmp_path / "x").exists()
    argv = ["evaluate", *common(world, 1102), "--source-run", world.regen[1102], "--out", tmp_path / "out", "--mode",
            "scale", "--lambda", 0.5]
    assert cli(world, argv) == 2 and not (tmp_path / "out").exists()
    assert cli(world, [*argv, "--certification-report", world.cert[0]]) == 2 and not (tmp_path / "out").exists()
    assert cli(world, [*argv, *fb.cert_args(world.cert)]) == 0 and (tmp_path / "out" / "COMPLETE.json").is_file()


def test_a_reference_unit_names_its_certification_and_its_overrefusal_bank(world, tmp_path):
    result = evaluate(world, tmp_path / "half", ea.make_plan(world.settings, "scale", adapter_scale=0.5))
    job, marker = read_json(tmp_path / "half" / "job.json"), read_json(tmp_path / "half" / "COMPLETE.json")
    from experiments.safety_selection.prepare import load_prepared

    assert job["certification_report_sha256"] == world.cert[1] == marker["certification_report_sha256"]
    items = sum(i["kind"] == "overrefusal" for i in load_prepared(world.prepared, banks=("dev",)).banks["dev"])
    assert items > 0 and marker["overrefusal_bank"] == {
        "status": "dev100_recipe_cap", "bank": "dev", "overrefusal_items": items,
        "max_new_tokens": fb.recipe()["generation"]["max_new_tokens"]}
    assert result["complete"]
    cert_job = read_json(world.base / "certification" / "cert-unit" / "job.json")
    assert cert_job["certification_report_sha256"] is None


def edited_report(world, tmp_path: Path, change) -> tuple[Path, str]:
    report = json.loads(world.cert[0].read_bytes())
    change(report)
    path = tmp_path / "report.json"
    path.write_bytes(canonical_json(report))
    return path, sha256_file(path)


REPORT_CHANGES = [
    ("kind", lambda r: r.update(kind="other"), "not a B10 certification comparison"),
    ("against", lambda r: r.update(against="untuned"), "not the certify unit's comparison"),
    ("unit mode", lambda r: r.update(unit_mode="external"), "not the certify unit's comparison"),
    ("verdict", lambda r: r.update(verdict="fail"), "did not pass"),
    ("answer set", lambda r: r["gate"].update(same_answer_set=False), "did not pass"),
    ("differing", lambda r: r["gate"].update(differing_gate_labels=1), "did not pass"),
    ("count", lambda r: r["gate"].update(answers_reference=5), "did not pass"),
    ("seed", lambda r: r.update(seed=1102), "certification seed"),
    ("reference", lambda r: r.update(reference_complete_sha256="0" * 64), "certification seed"),
    ("engine", lambda r: r["certified"].update(code_sha256="0" * 64), "another engine"),
    ("code", lambda r: r["certified"].update(script_code_sha256="0" * 64), "other B10 code"),
    ("settings", lambda r: r["certified"].update(certified_settings_sha256="0" * 64), "other certified settings"),
    ("environment", lambda r: r.update(environment={}), "environment fields")]


@pytest.mark.parametrize("what, change, message", REPORT_CHANGES, ids=[c[0] for c in REPORT_CHANGES])
def test_read_certification_refuses_a_report_that_does_not_certify_this_path(world, tmp_path, what, change, message):
    path, digest = edited_report(world, tmp_path, change)
    with pytest.raises(ea.Refusal, match=message):
        ea.read_certification(path, digest, world.settings)


def test_read_certification_reads_the_report_only_by_its_given_hash(world, tmp_path):
    good = ea.read_certification(*world.cert, world.settings)
    assert good["sha256"] == world.cert[1] and good["seed"] == 1101
    assert set(good["environment"]) == set(world.settings.doc["certification"]["environment_fields"])
    with pytest.raises(ea.Refusal, match="hashes to"):
        ea.read_certification(world.cert[0], "0" * 64, world.settings)
    with pytest.raises(ea.Refusal, match="cannot be read"):
        ea.read_certification(tmp_path / "missing.json", world.cert[1], world.settings)


def test_a_certification_survives_uncertified_settings_changes_only(world):
    keep = fb.fixture_settings(world.manifest, world.units, untuned=world.init,
                               recipe__file_sha256=world.settings.doc["recipe"]["file_sha256"],
                               prefix__text_sha256="c" * 64, prefix__source="ENGINEERING FIXTURE placeholder",
                               adapter_scale__planned=[0.5], overrefusal_bank__status="open",
                               external_transforms={"identity": fb.transform_entry("identity")})
    assert keep.sha256 != world.settings.sha256
    assert ea.certified_settings_sha256(keep) == ea.certified_settings_sha256(world.settings)
    assert ea.read_certification(*world.cert, keep)["seed"] == 1101
    for dotted, value in (("regeneration.rule", "another rule text"), ("certification.gate", "another gate text"),
                          ("evaluation.rule", "another evaluation text"),
                          ("certification.environment_fields", ["environment_lock.sha256"])):
        other = fb.fixture_settings(world.manifest, world.units, untuned=world.init,
                                    recipe__file_sha256=world.settings.doc["recipe"]["file_sha256"],
                                    **{dotted.replace(".", "__"): value})
        with pytest.raises(ea.Refusal, match="other certified settings"):
            ea.read_certification(*world.cert, other)


def test_script_code_sha256_ignores_the_settings_literal_and_nothing_else(tmp_path):
    text = Path(ea.__file__).read_text()
    other_literal = tmp_path / "a.py"
    other_literal.write_text(text.replace(ea.SETTINGS_SHA256, "1" * 64))
    assert ea.script_code_sha256(other_literal) == ea.script_code_sha256()
    other_code = tmp_path / "b.py"
    other_code.write_text(text + "\n# one more line\n")
    assert ea.script_code_sha256(other_code) != ea.script_code_sha256()
    twice = tmp_path / "c.py"
    twice.write_text(text + f'\nSETTINGS_SHA256 = "{ea.SETTINGS_SHA256}"\n')
    with pytest.raises(ea.Refusal, match="exactly once"):
        ea.script_code_sha256(twice)


def resealed_copy(unit: Path, folder: Path, change_job=None, change_rows=None) -> Path:
    copy_dir = folder / "unit"
    shutil.copytree(unit, copy_dir)
    if change_job is not None:
        job = json.loads((copy_dir / "job.json").read_bytes())
        change_job(job)
        (copy_dir / "job.json").write_bytes(canonical_json(job))
    if change_rows is not None:
        path = copy_dir / "eval" / "e1" / "guard_samples.jsonl"
        path.write_text("\n".join(change_rows(path.read_text().splitlines())) + "\n")
    fb.reseal(copy_dir)
    assert verify_files(copy_dir) == []                                    # its own files verify again
    return copy_dir


@pytest.mark.parametrize("what, change, message", [
    ("engine", lambda j: j.update(code_sha256="0" * 64), "another engine"),
    ("script", lambda j: j.update(script_sha256="0" * 64), "another B10 script or settings"),
    ("reference", lambda j: j.update(reference_complete_sha256="f" * 64), "not evaluated against the pinned")])
def test_compare_refuses_a_self_consistent_unit_of_another_engine_script_or_reference(world, tmp_path, what, change,
                                                                                      message):
    unit = certify_unit(world, tmp_path / "cert")
    copied = resealed_copy(unit, tmp_path / "copy", change_job=change)
    with pytest.raises(ea.Refusal, match=message):
        ea.compare_certification(copied, world.units[1102] / "COMPLETE.json", fb.eval_dir(world.units[1102]),
                                 world.settings)
    assert ea.compare_certification(unit, world.units[1102] / "COMPLETE.json", fb.eval_dir(world.units[1102]),
                                    world.settings)["verdict"] == "pass"


def test_compare_refuses_a_unit_that_repeats_an_answer(world, tmp_path):
    unit = certify_unit(world, tmp_path / "cert")
    copied = resealed_copy(unit, tmp_path / "copy", change_rows=lambda rows: rows + rows[:1])
    with pytest.raises(ea.Refusal, match="repeats an answer id"):
        ea.compare_certification(copied, world.units[1102] / "COMPLETE.json", fb.eval_dir(world.units[1102]),
                                 world.settings)


def test_a_lambda_zero_unit_of_another_seed_is_not_compared_with_the_untuned_unit(world, tmp_path):
    evaluate(world, tmp_path / "zero", ea.make_plan(world.settings, "scale", adapter_scale=0.0), seed=1102)
    with pytest.raises(ea.Refusal, match="seed is not the untuned unit's"):
        ea.compare_certification(tmp_path / "zero", world.init / "COMPLETE.json", fb.eval_dir(world.init, "init"),
                                 world.settings, against="untuned")


ENV_A = {"device": "cpu", "deterministic_algorithms": True, "packages": {"torch": "2.8.0", "peft": "0.17.1"},
         "torch_threads": 8, "cuda": {"capability": "8.0", "driver": "NVRM 580.126.16", "env": {
             "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0"}}}


def test_a_reference_runs_only_in_the_certification_units_environment(world, tmp_path, monkeypatch):
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=world.regen[1101],
                       reference_path=world.units[1101] / "COMPLETE.json", recipe=fb.recipe(), settings=world.settings,
                       plan=ea.make_plan(world.settings, "certify"))
    ea.evaluate(ctx, out_dir=tmp_path / "cert", session=env_session(ENV_A))
    report = ea.compare_certification(tmp_path / "cert", world.units[1101] / "COMPLETE.json",
                                      fb.eval_dir(world.units[1101]), world.settings)
    env = report["environment"]
    assert env["environment.cuda.driver"] == "NVRM 580.126.16" and env["environment.packages.peft"] == "0.17.1"
    assert env["environment.cuda.env.CUBLAS_WORKSPACE_CONFIG"] == ":4096:8" and env["environment_lock.sha256"] is None
    assert env["environment.cuda.name"] is None and not any("torch_threads" in k for k in env)
    path = tmp_path / "cert-a.json"
    path.write_bytes(canonical_json(report))
    cert_a = (path, sha256_file(path))
    plan = ea.make_plan(world.settings, "scale", adapter_scale=0.5)
    same = {**copy.deepcopy(ENV_A), "torch_threads": 2}                          # outside the pinned fields
    same["cuda"]["env"]["CUDA_VISIBLE_DEVICES"] = "3"
    assert evaluate(world, tmp_path / "ok", plan, certification=cert_a, session=env_session(same))["complete"]
    other = copy.deepcopy(ENV_A)
    other["cuda"]["driver"] = "NVRM 570.00"
    with pytest.raises(ea.Refusal, match=r"environment.cuda.driver"):
        evaluate(world, tmp_path / "other", plan, certification=cert_a, session=env_session(other))
    assert not (tmp_path / "other").exists()
    with pytest.raises(ea.Refusal, match=r"differs from the certification unit's"):        # the default fixture env
        evaluate(world, tmp_path / "plain", plan, certification=cert_a)
    monkeypatch.setattr(runner, "lock_record", lambda device, cwd: ({"name": "environment-linux.lock",
                                                                      "sha256": "a" * 64}, b"x"))
    with pytest.raises(ea.Refusal, match=r"environment_lock.sha256"):
        evaluate(world, tmp_path / "lock", plan, certification=cert_a, session=env_session(same))
    assert not (tmp_path / "lock").exists() and not (tmp_path / "plain").exists()


def test_a_run_without_a_certification_refuses_before_any_training(world, tmp_path):
    argv = ["run", *common(world, 1102), "--seed", 1102, "--regen-out", tmp_path / "regen", "--eval-root",
            tmp_path / "eval", "--evaluations", "certify,scale:0.5"]
    assert cli(world, argv) == 2 and not (tmp_path / "regen").exists()
    # a gated run at a seed other than the certification seed (1101) does not certify the references by itself
    gate = fb.eval_dir(world.units[1102])
    assert cli(world, [*argv, "--gate-reference-eval", gate]) == 2 and not (tmp_path / "regen").exists()
    other_cert = tmp_path / "missing.json"
    assert cli(world, [*argv, "--certification-report", other_cert, "--certification-report-sha256", "0" * 64]) == 2
    assert not (tmp_path / "regen").exists()


def test_runs_take_the_given_report_or_their_own_gate_at_the_certification_seed(world, tmp_path, capsys):
    argv = ["run", *common(world, 1102), "--seed", 1102, "--regen-out", tmp_path / "r1", "--eval-root",
            tmp_path / "e1", "--evaluations", "scale:0.5", *fb.cert_args(world.cert)]
    assert cli(world, argv) == 0
    assert read_json(tmp_path / "e1" / "1102-scale-0.5" / "job.json")["certification_report_sha256"] == world.cert[1]
    capsys.readouterr()
    argv = ["run", *common(world, 1101), "--seed", 1101, "--regen-out", tmp_path / "r2", "--eval-root",
            tmp_path / "e2", "--evaluations", "certify,scale:0.0", "--gate-reference-eval",
            fb.eval_dir(world.units[1101])]
    assert cli(world, argv) == 0
    printed = json.loads(capsys.readouterr().out)
    own = printed["certification"]["report_sha256"]
    assert own == sha256_file(tmp_path / "e2" / "1101-certify.compare.json") != world.cert[1]
    assert read_json(tmp_path / "e2" / "1101-scale-0" / "job.json")["certification_report_sha256"] == own


# ----- S-3: the recipe's config hash is reported, the training identity required -------------------------------


def other_config_source(world, out: Path) -> tuple[Path, dict]:
    from experiments.safety_selection.config import config_sha256, training_identity
    from experiments.safety_selection.planning import make_job

    pinned = fb.recipe()
    variant = fb.recipe(**{"generation.max_new_tokens": pinned["generation"]["max_new_tokens"] + 1})
    assert config_sha256(variant) != config_sha256(pinned) and training_identity(variant) == training_identity(pinned)
    out.parent.mkdir(parents=True, exist_ok=True)
    job = make_job("run-one", prepared_dir=world.prepared, recipe=variant, pin_code=True,
                   out=out.parent / f"{out.name}-job.json", wall_limit_seconds=None, split="dev", arm="a0", seed=1102,
                   role="development", target_checkpoint="e1", evaluate_bank=None, resume_from=None,
                   replicate_of=None)
    runner.run_one(job, prepared_dir=world.prepared, out_dir=out, session=fb.session(variant))
    return out, variant


def strict_settings(world, **changes) -> ea.Settings:
    return fb.fixture_settings(world.manifest, world.units, untuned=world.init,
                               recipe__file_sha256=world.settings.doc["recipe"]["file_sha256"],
                               regeneration__compare_identity=["manifest_sha256", "recipe_sha256", "training_identity"],
                               regeneration__report_identity=[], **changes)


def test_a_source_under_another_evaluation_config_with_the_same_training_identity_is_accepted(world, tmp_path):
    source, _ = other_config_source(world, tmp_path / "other-config")
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=source,
                       reference_path=world.units[1102] / "COMPLETE.json", recipe=fb.recipe(), settings=world.settings,
                       plan=ea.make_plan(world.settings, "certify"))
    assert ctx.report["equal"] and ctx.report["report_only"]["identity.recipe_sha256"] is False
    ea.evaluate(ctx, out_dir=tmp_path / "cert", session=fb.session())                 # the pinned recipe evaluates
    for name in fb.EVAL_FILES:
        assert (fb.eval_dir(tmp_path / "cert") / name).read_bytes() == (
            fb.eval_dir(world.units[1102]) / name).read_bytes(), name
    strict = strict_settings(world)
    with pytest.raises(ea.Refusal, match=r"differs in \['recipe_sha256'\]") as caught:
        ea.preflight(prepared_dir=world.prepared, source_run=source, reference_path=world.units[1102] / "COMPLETE.json",
                     recipe=fb.recipe(), settings=strict, plan=ea.make_plan(strict, "certify"))
    assert not isinstance(caught.value, ea.Mismatch)


def test_a_reference_under_another_config_with_the_same_training_identity_is_accepted(world, tmp_path):
    marker = json.loads((world.units[1102] / "COMPLETE.json").read_bytes())
    marker["identity"]["recipe_sha256"] = "0" * 64
    path = tmp_path / "COMPLETE.json"
    path.write_bytes(canonical_json(marker))
    for make in (lambda **c: fb.fixture_settings(world.manifest, world.units, untuned=world.init, **c),
                 lambda **c: strict_settings(world, **c)):
        settings = make()
        doc = copy.deepcopy(settings.doc)
        doc["reference_units"]["1102"]["complete_sha256"] = sha256_file(path)
        settings = ea.settings_from_doc(doc)
        if "recipe_sha256" in settings.doc["regeneration"]["compare_identity"]:
            with pytest.raises(ea.Refusal, match="identity differs"):
                ea.read_reference(path, 1102, settings)
        else:
            assert ea.read_reference(path, 1102, settings)["seed"] == 1102


# ----- S-4: the identity transform (Safe LoRA at K = 0) certifies against a0 -----------------------------------


def test_an_identity_transform_unit_certifies_against_a0_and_a_changing_one_does_not(world, tmp_path):
    evaluate(world, tmp_path / "k0", ea.make_plan(world.settings, "external", external="identity"), seed=1101)
    report = ea.compare_certification(tmp_path / "k0", world.units[1101] / "COMPLETE.json",
                                      fb.eval_dir(world.units[1101]), world.settings)
    assert report["verdict"] == "pass" and report["unit_mode"] == "external"
    path = tmp_path / "k0.json"
    path.write_bytes(canonical_json(report))
    with pytest.raises(ea.Refusal, match="not the certify unit's comparison"):        # not the binding certification
        ea.read_certification(path, sha256_file(path), world.settings)
    evaluate(world, tmp_path / "half", ea.make_plan(world.settings, "external", external="half_b"), seed=1101)
    with pytest.raises(ea.Refusal, match="identity transform"):
        ea.compare_certification(tmp_path / "half", world.units[1101] / "COMPLETE.json",
                                 fb.eval_dir(world.units[1101]), world.settings)
    evaluate(world, tmp_path / "file-k0", ea.make_plan(world.settings, "external",
                                                       **file_inputs(world, tmp_path / "in", seed=1101, scale=1.0)),
             seed=1101)
    assert ea.compare_certification(tmp_path / "file-k0", world.units[1101] / "COMPLETE.json",
                                    fb.eval_dir(world.units[1101]), world.settings)["verdict"] == "pass"


# ----- B-1: the over-refusal bank gate --------------------------------------------------------------------------


def test_an_open_overrefusal_bank_runs_only_certification_points(world, tmp_path):
    settings = fb.fixture_settings(world.manifest, world.units, untuned=world.init,
                                   recipe__file_sha256=world.settings.doc["recipe"]["file_sha256"],
                                   overrefusal_bank__status="open", prefix__text_sha256="c" * 64,
                                   prefix__source="ENGINEERING FIXTURE placeholder",
                                   external_transforms=world.settings.doc["external_transforms"])
    for mode, options in (("prefix", {"prefix_file": "p.txt"}), ("scale", {"adapter_scale": 0.5}),
                          ("scale", {"adapter_scale": 0.75}), ("external", {"external": "identity"})):
        with pytest.raises(ea.Refusal, match="over-refusal bank is open"):
            ea.make_plan(settings, mode, **options)
    assert ea.make_plan(settings, "certify").mode == "certify"
    zero = ea.make_plan(settings, "scale", adapter_scale=0.0)
    with pytest.raises(ea.Refusal, match="over-refusal bank is open"):
        evaluate(world, tmp_path / "half-file", ea.make_plan(settings, "external", **file_inputs(
            world, tmp_path / "half-in", scale=0.5)), settings=settings)
    assert not (tmp_path / "half-file").exists()
    evaluate(world, tmp_path / "k0-file", ea.make_plan(settings, "external", **file_inputs(
        world, tmp_path / "k0-in", scale=1.0)), settings=settings)
    evaluate(world, tmp_path / "zero", zero, settings=settings)
    assert read_json(tmp_path / "zero" / "COMPLETE.json")["overrefusal_bank"]["status"] == "open"
    real = ea.settings_from_doc(dict(fb.real_doc(), overrefusal_bank=dict(fb.real_doc()["overrefusal_bank"],
                                                                          status="open")))
    with pytest.raises(ea.Refusal, match="over-refusal bank is open"):
        ea.make_plan(real, "scale", adapter_scale=0.5)
    assert ea.make_plan(real, "scale", adapter_scale=0.0).adapter_scale == 0.0
    pinned = ea.load_pinned_settings()                    # addendum 11.1 and 13: oext_pinned, the branch pending
    assert pinned.doc["overrefusal_bank"]["status"] == "oext_pinned" and pinned.doc["oext"]["branch"] == "pending_w1_18"
    for mode, options in (("scale", {"adapter_scale": 0.5}), ("scale", {"adapter_scale": 0.0})):
        with pytest.raises(ea.Refusal, match="pending W1-18"):
            ea.make_plan(pinned, mode, **options)
    assert ea.make_plan(pinned, "certify").mode == "certify"
    assert cli(world, ["run", *common(world, 1102), "--seed", 1102, "--regen-out", tmp_path / "regen", "--eval-root",
                       tmp_path / "eval", "--evaluations", "scale:0.5", *fb.cert_args(world.cert)],
               settings=settings) == 2
    assert not (tmp_path / "regen").exists()


# ----- N-3: the verifier's low-risk survivors -------------------------------------------------------------------


def test_a_file_transforms_settings_file_is_hashed_when_it_is_used(world, tmp_path):
    inputs = file_inputs(world, tmp_path / "in", name="file_pinned_wrong", settings_sha256="7" * 64)
    with pytest.raises(ea.Refusal, match="settings hashes to"):
        evaluate(world, tmp_path / "out", ea.make_plan(world.settings, "external", **inputs))
    assert not (tmp_path / "out").exists()


def test_a_callable_gets_copies_of_the_source_tensors(world, tmp_path):
    from safetensors.torch import load_file

    result = evaluate(world, tmp_path / "inplace", ea.make_plan(world.settings, "external", external="inplace_half_b"))
    source = load_file(str(world.regen[1102] / "states" / "e1" / "adapter.safetensors"))
    counts = read_json(tmp_path / "inplace" / "transform.json")["counts"]
    assert counts["changed_lora_b"] == sum(".lora_B." in n for n in source) and counts["changed_lora_a"] == 0
    expected, _ = ea.scale_adapter(source, 0.5)
    assert result["evaluated_adapter_fingerprint"] == ea.adapter_fingerprint(expected)
    assert result["source_adapter_fingerprint"] == ea.adapter_fingerprint(source)
