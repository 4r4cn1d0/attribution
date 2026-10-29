"""B10's adapter changes on ENGINEERING FIXTURES: the adapter scale (lora_B times lambda, lora_A kept, lambda = 0 exact
zeros), the external hook as an allowlisted callable and as a transformed adapter file with its record, and every
refusal of a bad transform. None of these numbers is a scientific result."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402

from experiments.safety_selection.common import canonical_json, read_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

SETTINGS_STAND_IN = "scripts/stage1_s1/tests/b10_transform_fixture.py"   # any pinned repository file
FUNCTIONS = ("identity", "half_b", "zero_b", "change_a", "nan_b", "float64", "bad_shape", "missing_key",
             "long_record", "no_record")


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("b10-transforms")
    prepared, manifest = fb.prepared(base)
    unit = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", 1102)
    externals = {name: fb.transform_entry(name) for name in FUNCTIONS}
    externals["keep_a"] = fb.transform_entry("change_a", require_a=True)
    externals["no_function"] = fb.transform_entry("not_there")
    externals["no_interface"] = fb.transform_entry("identity", module="scripts/stage1_s1/tests/b10_fixtures.py")
    externals["file_half"] = fb.transform_entry(None, kind="file", require_a=True, record_keys={
        "transform_sha256": "transform.sha256", "source_adapter_fingerprint": "source.fingerprint",
        "output_adapter_fingerprint": "output.fingerprint", "output_file_sha256": "output.file_sha256"})
    externals["file_pinned"] = dict(fb.transform_entry(None, kind="file", require_a=True, record_keys={
        "transform_sha256": "transform.sha256", "source_adapter_fingerprint": "source.fingerprint",
        "output_adapter_fingerprint": "output.fingerprint", "output_file_sha256": "output.file_sha256",
        "transform_settings_sha256": "transform.settings_sha256"}),
        settings={"path": SETTINGS_STAND_IN, "sha256": sha256_file(ea.REPO / SETTINGS_STAND_IN)})
    settings = fb.fixture_settings(manifest, {1102: unit}, external_transforms=externals)
    regen = base / "regen"
    ea.regenerate(prepared_dir=prepared, seed=1102, reference_path=unit / "COMPLETE.json", out_root=regen,
                  session=fb.session(), settings=settings)
    cert = fb.certification(prepared, unit, settings, base / "certification", source=regen / "run")
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, unit=unit, settings=settings,
                        source=regen / "run", cert=cert)


def run(world, out: Path, plan, settings=None) -> dict:
    settings = settings or world.settings
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=world.source, reference_path=world.unit / "COMPLETE.json",
                       recipe=fb.recipe(), settings=settings, plan=plan,
                       certification=None if plan.mode == "certify" else world.cert)
    return ea.evaluate(ctx, out_dir=out, session=fb.session())


def source_tensors(world) -> dict:
    from safetensors.torch import load_file

    return load_file(str(world.source / "states" / "e1" / "adapter.safetensors"))


def same_eval(a: Path, b: Path) -> bool:
    return all((fb.eval_dir(a) / n).read_bytes() == (fb.eval_dir(b) / n).read_bytes() for n in fb.EVAL_FILES)


# ----- the scale ------------------------------------------------------------------------------------------------


def test_scale_adapter_multiplies_lora_b_only_and_zero_is_exact_zeros():
    a = torch.randn(4, 6, generator=torch.Generator().manual_seed(1))
    b = torch.randn(8, 4, generator=torch.Generator().manual_seed(2))
    b[0, 0] = -0.75
    adapter = {"m.lora_A.default.weight": a, "m.lora_B.default.weight": b}
    out, record = ea.scale_adapter(adapter, 0.75)
    assert torch.equal(out["m.lora_B.default.weight"], b * 0.75) and out["m.lora_A.default.weight"] is a
    assert record["lambda"] == 0.75 and record["lora_b_matrices"] == 1 and record["max_abs_norm_ratio_error"] < 1e-6
    zero, _ = ea.scale_adapter(adapter, 0.0)
    assert zero["m.lora_B.default.weight"].numpy().tobytes() == torch.zeros(8, 4).numpy().tobytes()   # +0.0, not -0.0
    half, _ = ea.scale_adapter(adapter, 0.5)
    assert torch.equal(half["m.lora_B.default.weight"] * 2, b)                                      # exact in float32


def test_scale_evaluates_the_scaled_adapter_and_records_it(world, tmp_path):
    result = run(world, tmp_path / "half", ea.make_plan(world.settings, "scale", adapter_scale=0.5))
    transform = read_json(tmp_path / "half" / "transform.json")
    source = source_tensors(world)
    b_names = [n for n in source if ".lora_B." in n]
    assert transform["counts"]["changed_lora_b"] == len(b_names) and transform["counts"]["changed_lora_a"] == 0
    expected, _ = ea.scale_adapter(source, 0.5)
    assert transform["transformed_adapter_fingerprint"] == ea.adapter_fingerprint(expected)
    assert result["evaluated_adapter_fingerprint"] == ea.adapter_fingerprint(expected) != result["source_adapter_fingerprint"]
    assert read_json(tmp_path / "half" / "job.json")["adapter_scale"] == 0.5
    assert "adapter_transform" in read_json(tmp_path / "half" / "COMPLETE.json")["costs"]["stage_seconds"]
    assert not same_eval(tmp_path / "half", world.unit)


def test_the_plan_enforces_one_change_per_evaluation(world):
    s = world.settings
    for bad in (dict(mode="certify", adapter_scale=0.5), dict(mode="scale", adapter_scale=1.0),
                dict(mode="scale", adapter_scale=0.6), dict(mode="scale", adapter_scale=float("nan")),
                dict(mode="scale", adapter_scale=True), dict(mode="scale", adapter_scale=0.5, external="identity"),
                dict(mode="certify", prefix_file="x"), dict(mode="external", external="identity", adapter_scale=0.5),
                dict(mode="external", external="unknown"), dict(mode="external"),
                dict(mode="external", external="identity", adapter_file="f"),
                dict(mode="external", external="file_half"), dict(mode="prefix"),      # the SP text is pinned now
                dict(mode="merge")):
        mode = bad.pop("mode")
        with pytest.raises(ea.Refusal):
            ea.make_plan(s, mode, **bad)
    assert ea.make_plan(s, "certify").label == "certify"
    assert ea.make_plan(s, "scale", adapter_scale=0.75).label == "scale-0.75"
    assert ea.make_plan(s, "scale", adapter_scale=0).adapter_scale == 0.0
    assert ea.make_plan(s, "external", external="identity").label == "external-identity"


# ----- the callable hook ----------------------------------------------------------------------------------------


def test_an_identity_transform_evaluates_exactly_like_certify(world, tmp_path):
    run(world, tmp_path / "cert", ea.make_plan(world.settings, "certify"))
    result = run(world, tmp_path / "ident", ea.make_plan(world.settings, "external", external="identity"))
    assert same_eval(tmp_path / "ident", tmp_path / "cert") and same_eval(tmp_path / "cert", world.unit)
    transform = read_json(tmp_path / "ident" / "transform.json")
    assert transform["counts"]["changed_lora_a"] == transform["counts"]["changed_lora_b"] == 0
    assert result["evaluated_adapter_fingerprint"] == result["source_adapter_fingerprint"]
    assert transform["record"] == {"op": "identity", "seed": 1102, "source": result["source_adapter_fingerprint"],
                                   "lora_scale": 2.0}
    job = read_json(tmp_path / "ident" / "job.json")
    assert job["external"]["module_sha256"] == sha256_file(ea.REPO / fb.TRANSFORM_MODULE)


def test_a_callable_half_b_equals_the_scale_half(world, tmp_path):
    run(world, tmp_path / "scale", ea.make_plan(world.settings, "scale", adapter_scale=0.5))
    run(world, tmp_path / "hook", ea.make_plan(world.settings, "external", external="half_b"))
    assert same_eval(tmp_path / "hook", tmp_path / "scale")


@pytest.mark.parametrize("name, message", [
    ("nan_b", "NaN or infinity"), ("float64", "not float32"), ("bad_shape", "shape differs"),
    ("missing_key", "exactly the source adapter's tensors"), ("long_record", "longer than 200"),
    ("no_record", "did not return"), ("keep_a", "changed .* lora_A")])
def test_a_bad_transform_fails_the_job_and_never_evaluates(world, tmp_path, name, message):
    out = tmp_path / name
    with pytest.raises(ea.Refusal, match=message):
        run(world, out, ea.make_plan(world.settings, "external", external=name))
    assert (out / "error.txt").is_file() and not (out / "COMPLETE.json").exists() and not (out / "eval").exists()


@pytest.mark.parametrize("name, message", [("no_function", "has no function"),
                                           ("no_interface", "does not state the interface")])
def test_a_callable_without_its_function_or_interface_refuses_before_any_folder(world, tmp_path, name, message):
    with pytest.raises(ea.Refusal, match=message):
        run(world, tmp_path / name, ea.make_plan(world.settings, "external", external=name))
    assert not (tmp_path / name).exists()


def test_a_transform_module_with_other_bytes_refuses_before_any_folder(world, tmp_path):
    entry = dict(world.settings.doc["external_transforms"]["identity"], module_sha256="0" * 64)
    settings = fb.fixture_settings(world.manifest, {1102: world.unit},
                                   external_transforms={**world.settings.doc["external_transforms"], "identity": entry})
    with pytest.raises(ea.Refusal, match="hashes to"):
        run(world, tmp_path / "x", ea.make_plan(settings, "external", external="identity"), settings)
    assert not (tmp_path / "x").exists()


def test_check_adapter_counts_byte_changes_and_refuses_other_names():
    a = torch.ones(2, 3)
    source = {"m.lora_A.default.weight": a, "m.lora_B.default.weight": torch.zeros(3, 2)}
    signed = {"m.lora_A.default.weight": a.clone(), "m.lora_B.default.weight": -torch.zeros(3, 2)}
    _, counts = ea.check_adapter(signed, source, require_lora_a_unchanged=True)
    assert (counts["changed_lora_a"], counts["changed_lora_b"]) == (0, 1)                 # -0.0 is a byte change
    with pytest.raises(ea.Refusal, match="neither a lora_A nor a lora_B"):
        ea.check_adapter({"m.other": a}, {"m.other": a}, require_lora_a_unchanged=False)
    with pytest.raises(ea.Refusal, match="not float32"):
        ea.check_adapter({**source, "m.lora_A.default.weight": [1.0]}, source, require_lora_a_unchanged=False)


def test_check_record_accepts_short_json_and_refuses_text_and_non_finite_values():
    assert ea.check_record({"a": [1, 2.5, None, True, "short"], "b": {"c": "x" * 200}}, "r")
    for bad in ({"a": "x" * 201}, {"a": float("inf")}, {"a": object()}, ["not", "an", "object"], {"k" * 201: 1},
                {"a": [float("nan")]}):
        with pytest.raises(ea.Refusal):
            ea.check_record(bad, "r")
    with pytest.raises(ea.Refusal, match="larger than"):
        ea.check_record({f"k{i}": "y" * 150 for i in range(8000)}, "r")


# ----- the file hook --------------------------------------------------------------------------------------------


def file_inputs(world, folder: Path, *, tamper=None) -> dict:
    from safetensors.torch import save_file

    source = source_tensors(world)
    half = {k: (v * 0.5 if ".lora_B." in k else v) for k, v in source.items()}
    folder.mkdir(parents=True, exist_ok=True)
    adapter = folder / "adapter.safetensors"
    save_file(half, str(adapter))
    record = {"transform": {"sha256": sha256_file(ea.REPO / fb.TRANSFORM_MODULE)},
              "source": {"fingerprint": ea.adapter_fingerprint(source)},
              "output": {"fingerprint": ea.adapter_fingerprint(half), "file_sha256": sha256_file(adapter)},
              "counts": {"mapped": 4}}
    if tamper is not None:
        tamper(record)
    path = folder / "record.json"
    path.write_bytes(canonical_json(record))
    return dict(external="file_half", adapter_file=str(adapter), adapter_sha256=sha256_file(adapter),
                record_file=str(path), record_sha256=sha256_file(path))


def test_a_transformed_adapter_file_with_its_record_evaluates_like_the_scale(world, tmp_path):
    run(world, tmp_path / "scale", ea.make_plan(world.settings, "scale", adapter_scale=0.5))
    run(world, tmp_path / "file", ea.make_plan(world.settings, "external", **file_inputs(world, tmp_path / "in")))
    assert same_eval(tmp_path / "file", tmp_path / "scale")
    transform = read_json(tmp_path / "file" / "transform.json")
    assert transform["record"]["file_record"]["counts"] == {"mapped": 4}
    assert read_json(tmp_path / "file" / "job.json")["external"]["kind"] == "file"


@pytest.mark.parametrize("tamper, message", [
    (lambda r: r["transform"].update(sha256="1" * 64), "another transform"),
    (lambda r: r["source"].update(fingerprint="2" * 64), "not this regenerated a0 state"),
    (lambda r: r["output"].update(file_sha256="3" * 64), "another output file"),
    (lambda r: r["output"].update(fingerprint="4" * 64), "not the record's output adapter"),
    (lambda r: r.pop("source"), "holds no source.fingerprint")])
def test_a_file_whose_record_does_not_hold_refuses_before_any_folder(world, tmp_path, tamper, message):
    inputs = file_inputs(world, tmp_path / "in", tamper=tamper)
    with pytest.raises(ea.Refusal, match=message):
        run(world, tmp_path / "out", ea.make_plan(world.settings, "external", **inputs))
    assert not (tmp_path / "out").exists()


def test_a_file_or_record_with_other_bytes_refuses(world, tmp_path):
    inputs = file_inputs(world, tmp_path / "in")
    for key in ("adapter_sha256", "record_sha256"):
        with pytest.raises(ea.Refusal, match="hashes to"):
            run(world, tmp_path / "out", ea.make_plan(world.settings, "external", **{**inputs, key: "5" * 64}))
    assert not (tmp_path / "out").exists()


def test_the_callable_receives_a_text_free_context(world, tmp_path):
    recipe = fb.recipe()
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=world.source, reference_path=world.unit / "COMPLETE.json",
                       recipe=recipe, settings=world.settings, plan=ea.make_plan(world.settings, "external",
                                                                                external="identity"),
                       certification=world.cert)
    context = ea.transform_context(ctx, recipe, fb.namespace(identity={"snapshot": "/snap"}), None)
    assert context == {"interface": ea.TRANSFORM_INTERFACE, "name": "identity",
                       "source": {"run": str(world.source), "checkpoint": "e1", "seed": 1102,
                                  "adapter_fingerprint": ctx.source_fingerprint},
                       "model": {"repo_id": "fixture/tiny", "revision": "0" * 40, "architecture": "Qwen2ForCausalLM"},
                       "lora": {"r": 2, "alpha": 4, "scale": 2.0, "target_modules": ["q_proj", "v_proj"]},
                       "policy_snapshot": "/snap", "settings": None}
    assert json.loads(json.dumps(context)) == context
    assert sha256_bytes(canonical_json(context))


def test_a_file_transform_with_pinned_settings_needs_its_settings_hash_in_the_record(world, tmp_path):
    pin = sha256_file(ea.REPO / SETTINGS_STAND_IN)

    def stamp(value):
        return lambda r: r["transform"].update(settings_sha256=value)

    inputs = file_inputs(world, tmp_path / "ok", tamper=stamp(pin))
    run(world, tmp_path / "out", ea.make_plan(world.settings, "external", **{**inputs, "external": "file_pinned"}))
    assert read_json(tmp_path / "out" / "transform.json")["record"]["fields"]["transform_settings_sha256"] == pin
    for value, message in ((None, "holds no transform.settings_sha256"), ("6" * 64, "other settings")):
        bad = file_inputs(world, tmp_path / f"bad-{value}", tamper=stamp(value))
        with pytest.raises(ea.Refusal, match=message):
            run(world, tmp_path / f"x-{value}", ea.make_plan(world.settings, "external",
                                                             **{**bad, "external": "file_pinned"}))
        assert not (tmp_path / f"x-{value}").exists()
