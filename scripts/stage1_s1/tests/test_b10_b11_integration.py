"""The B10 + B11 integration test (addendum section 11 point 5; B10 hand-over 13.3 S-5): B10's settings allowlist
B11's Safe LoRA as a "file" external transform with the fifth record key (transform_settings_sha256 ->
provenance.settings_sha256), and B11's outputs pass B10's file path.

1. The pinned entry: the module and settings SHA-256 values are B11's files as they are now; the record keys are
   B11's B10_RECORD_KEYS; the entry is outside B10's certified settings (no new certification).
2. B11's tiny OLMo-2 fixture (b11_fixtures) at default and certify, through B10's _check_external,
   load_adapter_file and check_adapter (the verifier's probe).
3. B10's ENGINEERING FIXTURE world: B11 transforms the regenerated a0 e1 state of the certification seed; B10
   evaluates the certify (K = 0) output as an external file unit, and compare --against a0 passes; the default
   point's output evaluates with its lora_B changed, and compare refuses it as a certification.

The B10 entry in parts 2 and 3 is the pinned one with two changes only: the module SHA-256 is the module that runs
here (so a changed safe_lora.py is still tested by its behaviour) and the settings pin is the tiny refit settings
file's, placed with a copy of the module in a temporary repository root. None of these numbers is a scientific
result."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402
import b11_fixtures as fx11  # noqa: E402
from safetensors.torch import load_file, save_file  # noqa: E402

from experiments.safety_selection.common import canonical_json, read_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402
from scripts.stage1_s1 import safe_lora as sl  # noqa: E402

SL_MODULE = "scripts/stage1_s1/safe_lora.py"
SL_SETTINGS = "scripts/stage1_s1/settings/safe_lora.json"


# ----- 1. the pinned entry ----------------------------------------------------------------------------------------


def test_b10s_settings_allowlist_b11_with_both_current_hashes_and_the_fifth_key():
    settings = ea.load_pinned_settings()
    entry = settings.doc["external_transforms"]["safe_lora"]
    assert entry == {
        "kind": "file", "module": SL_MODULE, "module_sha256": sha256_file(ea.REPO / SL_MODULE), "function": None,
        "settings": {"path": SL_SETTINGS, "sha256": sl.SETTINGS_SHA256},
        "record_keys": {"transform_sha256": "provenance.script_sha256",
                        "source_adapter_fingerprint": "input_adapter.fingerprint",
                        "output_adapter_fingerprint": "output.fingerprint",
                        "output_file_sha256": "output.adapter_sha256",
                        "transform_settings_sha256": "provenance.settings_sha256"},
        "require_lora_a_unchanged": True, "role": "B11 Safe LoRA (REF R.1), file form"}
    assert entry["record_keys"] == sl.B10_RECORD_KEYS
    assert sha256_file(ea.REPO / SL_SETTINGS) == sl.SETTINGS_SHA256 == sl.load_pinned_settings().sha256
    assert sha256_file(Path(sl.__file__).resolve()) == entry["module_sha256"]
    ea._check_external("safe_lora", entry)
    doc = copy.deepcopy(settings.doc)
    doc["external_transforms"] = {}
    assert ea.certified_settings_sha256(settings) == ea.certified_settings_sha256(ea.settings_from_doc(doc))


@pytest.mark.parametrize("change, match", [
    (lambda e: e["record_keys"].pop("transform_settings_sha256"), "transform_settings_sha256"),
    (lambda e: e.update(settings=None), "record_keys"),
    (lambda e: e.update(kind="callable"), "function must name"),
    (lambda e: e.update(module_sha256="33fffd6f"), "module_sha256"),
])
def test_a_changed_entry_refuses(change, match):
    entry = copy.deepcopy(ea.load_pinned_settings().doc["external_transforms"]["safe_lora"])
    change(entry)
    with pytest.raises(ea.Refusal, match=match):
        ea._check_external("safe_lora", entry)


def _entry(settings_sha256: str) -> dict:
    """The pinned entry for this run: the module that runs here and the given settings pin."""
    entry = copy.deepcopy(ea.load_pinned_settings().doc["external_transforms"]["safe_lora"])
    entry["module_sha256"] = sha256_file(Path(sl.__file__).resolve())
    entry["settings"]["sha256"] = settings_sha256
    return entry


def _repo(root: Path, settings_doc: dict) -> str:
    """A temporary repository root holding the module that runs here and the refit settings, at the entry's paths."""
    (root / SL_SETTINGS).parent.mkdir(parents=True)
    shutil.copyfile(Path(sl.__file__).resolve(), root / SL_MODULE)
    data = canonical_json(settings_doc)
    (root / SL_SETTINGS).write_bytes(data)
    return sha256_bytes(data)


def _transform(monkeypatch, settings_doc: dict, folder: Path, point: str, *, adapter: Path, seed: str,
               aligned: Path, base: Path) -> dict:
    """B11's command line (the file form) under the given settings; returns the plan arguments for B10."""
    holder = folder.parent / f"settings-{folder.name}"
    holder.mkdir()
    path, digest = fx11.write_settings_file(holder, settings_doc)
    monkeypatch.setattr(sl, "SETTINGS_PATH", path)
    monkeypatch.setattr(sl, "SETTINGS_SHA256", digest)
    assert sl.main(["transform", "--point", point, "--adapter", str(adapter), "--seed", seed, "--aligned", str(aligned),
                    "--base", str(base), "--out", str(folder)]) == 0
    adapter_file, record_file = folder / "adapter.safetensors", folder / "safe_lora_record.json"
    return dict(external="safe_lora", adapter_file=str(adapter_file), adapter_sha256=sha256_file(adapter_file),
                record_file=str(record_file), record_sha256=sha256_file(record_file))


# ----- 2. B11's tiny OLMo-2 through B10's file checks --------------------------------------------------------------


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    return fx11.build_tiny(tmp_path_factory.mktemp("b10b11-tiny"))


def _b10_settings(entry: dict) -> ea.Settings:
    doc = fb.real_doc()
    doc["external_transforms"] = {"safe_lora": entry}
    doc["overrefusal_bank"]["status"] = "open"      # the file checks under "open" (O-ext pending refuses them; B10 O-ext)
    return ea.settings_from_doc(doc)


@pytest.mark.parametrize("point, changed_b", [("certify", 0), ("default", 5)])
def test_b11s_tiny_outputs_pass_b10s_file_checks(tiny, tmp_path, monkeypatch, point, changed_b):
    root = tmp_path / "repo"
    digest = _repo(root, tiny.doc)
    monkeypatch.setattr(ea, "REPO", root)
    settings = _b10_settings(_entry(digest))
    work = tmp_path / "work"
    work.mkdir()
    args = _transform(monkeypatch, tiny.doc, work / point, point, adapter=tiny.state_dir, seed=fx11.SEED,
                      aligned=tiny.aligned, base=tiny.base)
    plan = ea.make_plan(settings, "external", **args)
    tensors, record, fields = ea.load_adapter_file(plan, settings, tiny.fingerprint)
    assert fields["transform_settings_sha256"] == digest == record["provenance"]["settings_sha256"]
    assert fields["transform_sha256"] == sha256_file(root / SL_MODULE)
    out, counts = ea.check_adapter(tensors, tiny.adapter, require_lora_a_unchanged=True)
    assert (counts["tensors"], counts["changed_lora_a"], counts["changed_lora_b"]) == (28, 0, changed_b)
    assert (counts["fingerprint"] == tiny.fingerprint) is (point == "certify")
    assert counts["fingerprint"] == fields["output_adapter_fingerprint"]
    with pytest.raises(ea.Refusal, match="source adapter is not"):
        ea.load_adapter_file(plan, settings, "0" * 64)


def test_a_record_of_other_settings_or_another_module_refuses(tiny, tmp_path, monkeypatch):
    root = tmp_path / "repo"
    digest = _repo(root, tiny.doc)
    monkeypatch.setattr(ea, "REPO", root)
    other = copy.deepcopy(tiny.doc)
    other["transform"]["points"]["default"]["k"] = 4
    work = tmp_path / "other"
    work.mkdir()
    args = _transform(monkeypatch, other, work / "k4", "default", adapter=tiny.state_dir, seed=fx11.SEED,
                      aligned=tiny.aligned, base=tiny.base)
    settings = _b10_settings(_entry(digest))                          # the allowlisted settings are tiny.doc's
    with pytest.raises(ea.Refusal, match="other settings than safe_lora's pinned ones"):
        ea.load_adapter_file(ea.make_plan(settings, "external", **args), settings, tiny.fingerprint)
    moved = dict(_entry(digest), module_sha256="0" * 64)
    with pytest.raises(ea.Refusal, match="another transform than the allowlisted safe_lora"):
        ea.load_adapter_file(ea.make_plan(_b10_settings(moved), "external", **args), _b10_settings(moved),
                             tiny.fingerprint)


# ----- 3. B10's world: an evaluation of B11's outputs and the comparison against a0 --------------------------------


def _snapshot(folder: Path, tensors: dict) -> Path:
    folder.mkdir(parents=True)
    save_file({k: v.contiguous() for k, v in sorted(tensors.items())}, str(folder / "model.safetensors"))
    return folder


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("b10b11-world")
    prepared, manifest = fb.prepared(base)
    resumed, init = fb.gate_a_resumed(prepared, base / "units" / "1101-a0-e1-a1", 1101)
    units = {1101: resumed}
    recipe_file = base / "recipe.json"
    recipe_file.write_bytes(canonical_json(fb.recipe()))
    settings = fb.fixture_settings(manifest, units, untuned=init, recipe__file_sha256=sha256_file(recipe_file))
    ea.regenerate(prepared_dir=prepared, seed=1101, reference_path=resumed / "COMPLETE.json",
                  out_root=base / "regen-1101", session=fb.session(), settings=settings)
    regen = base / "regen-1101" / "run"
    cert = fb.certification(prepared, resumed, settings, base / "certification", source=regen)
    # B11's snapshots for the fixture policy: the aligned model is the policy's base model (stored in bfloat16, as the
    # real Instruct model is); the unaligned model is it minus a seeded change of each adapted weight (float32)
    model = fb.fx.tiny_lora_model().get_base_model()
    weights = {k.replace(".base_layer.", "."): v.detach().clone() for k, v in model.state_dict().items()
               if k.endswith("_proj.weight") or k.endswith("_proj.base_layer.weight")}   # PEFT's names, unwrapped
    generator = torch.Generator().manual_seed(7)
    unaligned = {k: v - 0.05 * torch.randn(v.shape, generator=generator) for k, v in weights.items()}
    aligned_dir = _snapshot(base / "aligned" / fx11.commit("b10-aligned"), {k: v.to(torch.bfloat16) for k, v in weights.items()})
    base_dir = _snapshot(base / "unaligned" / fx11.commit("b10-unaligned"), unaligned)
    state = regen / "states" / "e1"
    source = load_file(str(state / "adapter.safetensors"))
    doc = copy.deepcopy(fx11.real_doc())
    doc["adapter"].update(modules=["q_proj", "v_proj"], blocks=2, rank=2, lora_alpha=4, matrices=4,
                          parameters=sum(t.numel() for t in source.values()),
                          accepted={"1101": {"fingerprint": sl.adapter_fingerprint(source)}})
    doc["models"]["aligned"].update(revision=aligned_dir.name, files=fx11.snapshot_pins(aligned_dir))
    pins = fx11.snapshot_pins(base_dir)
    doc["models"]["unaligned"].update(revision=base_dir.name, files=pins, total_bytes=sum(p["bytes"] for p in pins),
                                      stored_dtype=fx11.stored_counts(base_dir),
                                      hub_files=[{"rfilename": p["file"], "size": p["bytes"], "lfs_sha256": p["sha256"],
                                                  "git_blob_id": fx11.git_blob_id((base_dir / p["file"]).read_bytes())}
                                                 for p in pins])
    doc["transform"]["points"]["default"]["k"] = 2
    doc["transform"]["points"]["conditional"]["k"] = 1
    return fb.namespace(base=base, prepared=prepared, units=units, settings=settings, regen=regen, cert=cert,
                        manifest=manifest, init=init, recipe=recipe_file, state=state, source=source,
                        aligned=aligned_dir, unaligned=base_dir, sl_doc=doc)


def _world_settings(world, digest: str) -> ea.Settings:
    return fb.fixture_settings(world.manifest, world.units, untuned=world.init,
                               recipe__file_sha256=world.settings.doc["recipe"]["file_sha256"],
                               external_transforms={"safe_lora": _entry(digest)})


def _evaluate(world, settings, plan, out: Path) -> dict:
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=world.regen, reference_path=world.units[1101] / "COMPLETE.json",
                       recipe=fb.recipe(), settings=settings, plan=plan, certification=world.cert)
    return ea.evaluate(ctx, out_dir=out, session=fb.session())


def test_b10_evaluates_b11s_certify_output_and_it_certifies_against_a0(world, tmp_path, monkeypatch):
    root = tmp_path / "repo"
    digest = _repo(root, world.sl_doc)
    monkeypatch.setattr(ea, "REPO", root)
    settings = _world_settings(world, digest)
    work = tmp_path / "b11"
    work.mkdir()
    args = _transform(monkeypatch, world.sl_doc, work / "certify", "certify", adapter=world.state, seed="1101",
                      aligned=world.aligned, base=world.unaligned)
    assert (work / "certify" / "adapter.safetensors").read_bytes() == (world.state / "adapter.safetensors").read_bytes()
    _evaluate(world, settings, ea.make_plan(settings, "external", **args), tmp_path / "k0")
    transform = read_json(tmp_path / "k0" / "transform.json")
    assert transform["external"] == "safe_lora" and transform["counts"]["changed_lora_b"] == 0
    assert transform["record"]["fields"]["transform_settings_sha256"] == digest
    assert transform["transformed_adapter_fingerprint"] == transform["source_adapter_fingerprint"]
    report = ea.compare_certification(tmp_path / "k0", world.units[1101] / "COMPLETE.json",
                                      fb.eval_dir(world.units[1101]), settings)
    assert report["verdict"] == "pass" and report["unit_mode"] == "external"


def test_b10_evaluates_b11s_default_output_and_compare_refuses_it_as_a_certification(world, tmp_path, monkeypatch):
    root = tmp_path / "repo"
    digest = _repo(root, world.sl_doc)
    monkeypatch.setattr(ea, "REPO", root)
    settings = _world_settings(world, digest)
    work = tmp_path / "b11"
    work.mkdir()
    args = _transform(monkeypatch, world.sl_doc, work / "default", "default", adapter=world.state, seed="1101",
                      aligned=world.aligned, base=world.unaligned)
    record = json.loads((work / "default" / "safe_lora_record.json").read_bytes())
    assert len(record["output"]["replaced_lora_b"]) == 2
    result = _evaluate(world, settings, ea.make_plan(settings, "external", **args), tmp_path / "k2")
    transform = read_json(tmp_path / "k2" / "transform.json")
    assert (transform["counts"]["changed_lora_a"], transform["counts"]["changed_lora_b"]) == (0, 2)
    assert result["evaluated_adapter_fingerprint"] == record["output"]["fingerprint"]
    with pytest.raises(ea.Refusal, match="identity transform"):
        ea.compare_certification(tmp_path / "k2", world.units[1101] / "COMPLETE.json",
                                 fb.eval_dir(world.units[1101]), settings)


# ----- 4. the K = 0 point as on the 1101 reference pod (block-B pre-flight G10; addendum section 34 point 7) ----------


def test_the_k0_point_runs_through_b10s_command_line_and_certifies_and_the_default_point_does_not(
        world, tmp_path, monkeypatch):
    """The kit's safe_lora job at 1101 with points certify and default, in its order: per point B11's transform
    command, then B10's evaluate command (--mode external, the file and its record by SHA-256, under the certification
    report), each in a new process; then B10's compare command: K = 0 passes against a0 (exit 0), the default point
    refuses as a certification (exit 2, nothing written)."""
    root = tmp_path / "repo"
    digest = _repo(root, world.sl_doc)
    monkeypatch.setattr(ea, "REPO", root)
    settings = _world_settings(world, digest)
    work = tmp_path / "b11"
    work.mkdir()
    reference = world.units[1101] / "COMPLETE.json"
    for point, verdict_exit in (("certify", 0), ("default", 2)):
        args = _transform(monkeypatch, world.sl_doc, work / point, point, adapter=world.state, seed="1101",
                          aligned=world.aligned, base=world.unaligned)
        out = tmp_path / f"eval-{point}"
        argv = ["evaluate", "--prepared", world.prepared, "--recipe", world.recipe, "--source-run", world.regen,
                "--reference", reference, "--out", out, "--mode", "external", "--external", "safe_lora",
                "--adapter-file", args["adapter_file"], "--adapter-sha256", args["adapter_sha256"],
                "--adapter-record", args["record_file"], "--adapter-record-sha256", args["record_sha256"],
                *fb.cert_args(world.cert)]
        assert ea.main([str(a) for a in argv], _settings=settings, _loaders=fb.fx.fixture_loaders()) == 0, point
        assert ea.verify_unit(out)["complete"]
        compare = tmp_path / f"compare-{point}.json"
        argv = ["compare", "--unit", out, "--reference", reference, "--reference-eval", fb.eval_dir(world.units[1101]),
                "--out", compare]
        assert ea.main([str(a) for a in argv], _settings=settings) == verdict_exit, point
        if point == "certify":
            report = json.loads(compare.read_bytes())
            assert report["verdict"] == "pass" and report["unit_mode"] == "external"
        else:
            assert not compare.exists()
