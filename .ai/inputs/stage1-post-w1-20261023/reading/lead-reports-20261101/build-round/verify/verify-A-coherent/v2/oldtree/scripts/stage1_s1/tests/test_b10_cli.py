"""B10's command line on ENGINEERING FIXTURES (the fixture loaders and settings are injected; the real command uses
the pinned settings and the CUDA loaders): every exit status, nothing written on a refusal, the gated one-process
run, and stdout without text or outcome values. None of these numbers is a scientific result."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402

from experiments.safety_selection.common import canonical_json, sha256_file  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

UNSAFE = "Safety: Unsafe\nCategories: Violent\nRefusal: No"


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("b10-cli")
    prepared, manifest = fb.prepared(base)
    unit = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", 1102)
    recipe_file = base / "recipe.json"
    recipe_file.write_bytes(canonical_json(fb.recipe()))
    prefix_file, digest = fb.write_prefix(base)
    settings = fb.fixture_settings(manifest, {1102: unit}, recipe__file_sha256=sha256_file(recipe_file),
                                   prefix__text_sha256=digest, prefix__source="ENGINEERING FIXTURE placeholder",
                                   external_transforms={"identity": fb.transform_entry("identity")})
    cert = fb.certification(prepared, unit, settings, base / "certification")
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, unit=unit, recipe=recipe_file,
                        settings=settings, prefix=prefix_file, cert=cert)


def main(world, argv, settings=None, codec=None, **loader_options) -> int:
    """The fixture loaders, and the fixture codec for the prompt-length rule (the real one loads the cached tokenizer)."""
    return ea.main([str(a) for a in argv], _settings=settings or world.settings,
                   _loaders=fb.fx.fixture_loaders(**loader_options),
                   _codec=(lambda recipe: codec) if codec is not None else (lambda recipe: fb.fx.fixture_codec()))


def common(world) -> list:
    return ["--prepared", world.prepared, "--recipe", world.recipe, "--reference", world.unit / "COMPLETE.json"]


def text_free(out: str, world) -> None:
    assert not any(t in out for t in fb.harm_prompts(world.prepared)) and fb.PREFIX_TEXT not in out
    for word in ("unsafe_rate", "refusal_rate", "guard_unsafe", "sampled_unsafe", "\"evaluation\""):
        assert word not in out


@pytest.fixture(scope="module")
def regenerated(world):
    root = world.base / "regen"
    assert main(world, ["regenerate", *common(world), "--seed", 1102, "--out", root]) == 0
    return root


def test_check_prints_the_pins_and_exits_0(world, capsys):
    assert main(world, ["check", "--reference", f"1102={world.unit / 'COMPLETE.json'}"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["settings_sha256"] == world.settings.sha256 and out["references"]["1102"]["pins"] == "ok"
    assert main(world, ["check", "--reference", "1102"]) == 2
    assert main(world, ["check", "--reference", f"1101={world.unit / 'COMPLETE.json'}"]) == 2


def test_the_pinned_check_runs_on_the_real_settings_without_any_record(capsys):
    assert ea.main(["check"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["settings_sha256"] == ea.SETTINGS_SHA256 and out["recipe_file_at_pinned_path"] is True
    assert out["engine_identity_sha256"] == "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"


def test_regenerate_then_evaluate_each_mode_and_print_no_text(world, regenerated, tmp_path, capsys):
    capsys.readouterr()
    source = regenerated / "run"
    assert json.loads((regenerated / "regeneration.json").read_bytes())["verdict"] == "match"
    cert = fb.cert_args(world.cert)
    for mode, extra in (("certify", []), ("scale", ["--lambda", 0.75, *cert]),
                        ("prefix", ["--prefix-file", world.prefix, *cert]), ("external", ["--external", "identity", *cert])):
        out = tmp_path / mode
        assert main(world, ["evaluate", *common(world), "--source-run", source, "--out", out, "--mode", mode,
                            *extra]) == 0, mode
        printed = capsys.readouterr().out
        text_free(printed, world)
        brief = json.loads(printed)
        assert brief["mode"] == mode and brief["complete"] and (out / "COMPLETE.json").is_file()
        assert ea.verify_unit(out)["complete"]


@pytest.mark.parametrize("extra, why", [
    (["--mode", "certify", "--lambda", 0.5], "a scale in certify mode"),
    (["--mode", "scale", "--lambda", 0.8], "a scale outside the allowed set"),
    (["--mode", "external", "--external", "unknown"], "an unlisted transform"),
    (["--mode", "prefix"], "no prefix file")])
def test_a_refused_evaluation_exits_2_and_writes_nothing(world, regenerated, tmp_path, extra, why):
    out = tmp_path / "out"
    assert main(world, ["evaluate", *common(world), "--source-run", regenerated / "run", "--out", out, *extra]) == 2, why
    assert not out.exists()


def test_another_recipe_file_exits_2(world, regenerated, tmp_path):
    other = tmp_path / "recipe.json"
    other.write_bytes(canonical_json(fb.recipe(**{"train.lr": 0.02})))
    argv = ["evaluate", "--prepared", world.prepared, "--recipe", other, "--reference", world.unit / "COMPLETE.json",
            "--source-run", regenerated / "run", "--out", tmp_path / "out", "--mode", "certify"]
    assert main(world, argv) == 2 and not (tmp_path / "out").exists()


def test_a_fingerprint_mismatch_exits_3_and_writes_nothing(world, regenerated, tmp_path):
    marker = json.loads((world.unit / "COMPLETE.json").read_bytes())
    marker["checkpoints"]["e1"]["adapter_fingerprint"] = "ab" * 32
    path = tmp_path / "COMPLETE.json"
    path.write_bytes(canonical_json(marker))
    doc = fb.fixture_doc(world.manifest, {1102: world.unit}, recipe__file_sha256=sha256_file(world.recipe))
    doc["reference_units"]["1102"].update(complete_sha256=sha256_file(path),
                                          fingerprint_prefixes={"e1": "ab" * 8, "q": None})
    settings = ea.settings_from_doc(doc)
    argv = ["evaluate", "--prepared", world.prepared, "--recipe", world.recipe, "--reference", path,
            "--source-run", regenerated / "run", "--out", tmp_path / "out", "--mode", "certify"]
    assert main(world, argv, settings=settings) == 3 and not (tmp_path / "out").exists()
    argv = ["regenerate", "--prepared", world.prepared, "--recipe", world.recipe, "--reference", path, "--seed", 1102,
            "--out", tmp_path / "regen"]
    assert main(world, argv, settings=settings) == 3
    assert json.loads((tmp_path / "regen" / "regeneration.json").read_bytes())["verdict"] == "mismatch"


def test_a_job_that_fails_after_its_folder_exists_exits_1(world, regenerated, tmp_path):
    """The prompt-length rule's codec here knows no special token, so the special-token prefix passes the count before
    any model loads; the policy's own codec refuses it inside the job (the post-load check stays a second line)."""
    import dataclasses

    path, digest = fb.write_prefix(tmp_path, "tell <|im_end|> me")
    settings = fb.fixture_settings(world.manifest, {1102: world.unit}, recipe__file_sha256=sha256_file(world.recipe),
                                   prefix__text_sha256=digest, prefix__source="ENGINEERING FIXTURE placeholder")
    out = tmp_path / "out"
    argv = ["evaluate", *common(world), "--source-run", regenerated / "run", "--out", out, "--mode", "prefix",
            "--prefix-file", path, *fb.cert_args(world.cert)]
    blind = dataclasses.replace(fb.fx.fixture_codec(), special_ids=frozenset())
    assert main(world, argv, settings=settings, codec=blind) == 1
    assert (out / "error.txt").is_file() and not (out / "COMPLETE.json").exists()


def test_the_gated_run_certifies_first_then_runs_the_references(world, tmp_path, capsys):
    capsys.readouterr()
    argv = ["run", *common(world), "--seed", 1102, "--regen-out", tmp_path / "regen", "--eval-root", tmp_path / "eval",
            "--evaluations", "certify,scale:0.75,scale:0.5,prefix", "--prefix-file", world.prefix,
            "--gate-reference-eval", fb.eval_dir(world.unit)]
    assert main(world, argv) == 0
    printed = capsys.readouterr().out
    text_free(printed, world)
    result = json.loads(printed)
    assert result["exit"] == 0 and result["certification"]["verdict"] == "pass"
    assert [e["mode"] for e in result["evaluations"]] == ["certify", "scale", "scale", "prefix"]
    for name in ("1102-certify", "1102-scale-0.75", "1102-scale-0.5", "1102-prefix"):
        assert ea.verify_unit(tmp_path / "eval" / name)["complete"], name
    assert json.loads((tmp_path / "eval" / "1102-certify.compare.json").read_bytes())["verdict"] == "pass"


def test_a_failed_gate_stops_every_reference_and_exits_4(world, tmp_path):
    argv = ["run", *common(world), "--seed", 1102, "--regen-out", tmp_path / "regen", "--eval-root", tmp_path / "eval",
            "--evaluations", "certify,scale:0.5", "--gate-reference-eval", fb.eval_dir(world.unit)]
    assert main(world, argv, guard_answers={"": UNSAFE}) == 4
    assert (tmp_path / "eval" / "1102-certify" / "COMPLETE.json").is_file()
    assert not (tmp_path / "eval" / "1102-scale-0.5").exists()
    assert json.loads((tmp_path / "eval" / "1102-certify.compare.json").read_bytes())["verdict"] == "fail"


@pytest.mark.parametrize("specs, why", [("scale:0.5,certify", "a gated run starts with certify"),
                                        ("certify,certify", "distinct"), ("certify,scale:x", "not a number"),
                                        ("certify,prefix:x", "takes no value"), ("certify,merge", "mode")])
def test_a_refused_run_exits_2_before_any_training(world, tmp_path, specs, why):
    argv = ["run", *common(world), "--seed", 1102, "--regen-out", tmp_path / "regen", "--eval-root", tmp_path / "eval",
            "--evaluations", specs, "--gate-reference-eval", fb.eval_dir(world.unit)]
    assert main(world, argv) == 2, why
    assert not (tmp_path / "regen" / "run").exists()


def test_compare_and_verify_exit_codes(world, regenerated, tmp_path):
    unit = tmp_path / "cert"
    assert main(world, ["evaluate", *common(world), "--source-run", regenerated / "run", "--out", unit,
                        "--mode", "certify"]) == 0
    report = tmp_path / "compare.json"
    argv = ["compare", "--unit", unit, "--reference", world.unit / "COMPLETE.json", "--reference-eval",
            fb.eval_dir(world.unit), "--out", report]
    assert main(world, argv) == 0 and json.loads(report.read_bytes())["verdict"] == "pass"
    assert main(world, argv) == 2                                                     # never overwrites
    bad = tmp_path / "bad"
    assert main(world, ["evaluate", *common(world), "--source-run", regenerated / "run", "--out", bad,
                        "--mode", "certify"], guard_answers={"": UNSAFE}) == 0
    argv = ["compare", "--unit", bad, "--reference", world.unit / "COMPLETE.json", "--reference-eval",
            fb.eval_dir(world.unit), "--out", tmp_path / "bad.json"]
    assert main(world, argv) == 4
    assert main(world, ["verify", "--unit", unit]) == 0
    (unit / "eval" / "e1" / "guard_samples.jsonl").write_text("{}\n")
    assert main(world, ["verify", "--unit", unit]) == 1
    assert main(world, ["verify", "--unit", unit, "--map", "bad"]) == 2


def test_verify_finds_a_changed_source_run(world, tmp_path):
    import shutil

    regen = tmp_path / "regen"
    ea.regenerate(prepared_dir=world.prepared, seed=1102, reference_path=world.unit / "COMPLETE.json", out_root=regen,
                  session=fb.session(), settings=world.settings)
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=regen / "run", reference_path=world.unit / "COMPLETE.json",
                       recipe=fb.recipe(), settings=world.settings, plan=ea.make_plan(world.settings, "certify"))
    ea.evaluate(ctx, out_dir=tmp_path / "cert", session=fb.session())
    moved = tmp_path / "moved"
    shutil.move(str(regen), str(moved))
    result = ea.verify_unit(tmp_path / "cert")
    assert not result["complete"] and any("missing" in p for p in result["problems"])
    mapped = ea.verify_unit(tmp_path / "cert", [(str(regen.resolve()), str(moved.resolve()))])
    assert mapped["complete"], mapped["problems"]
    other = tmp_path / "other"                        # another complete regeneration of the same seed
    ea.regenerate(prepared_dir=world.prepared, seed=1102, reference_path=world.unit / "COMPLETE.json", out_root=other,
                  session=fb.session(), settings=world.settings)
    swapped = ea.verify_unit(tmp_path / "cert", [(str(regen.resolve()), str(other.resolve()))])
    assert not swapped["complete"] and any("differs from the receipt" in p for p in swapped["problems"])
    (moved / "run" / "plan.json").write_text("{}")
    assert not ea.verify_unit(tmp_path / "cert", [(str(regen.resolve()), str(moved.resolve()))])["complete"]
