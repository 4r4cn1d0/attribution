"""B10's acceptance of an a0 state on ENGINEERING FIXTURES: the pinned Gate A reference is read only by its pinned
SHA-256 and only if it is the a0 e1 unit of that seed on the pinned data and recipe; a regenerated state whose q or
e1 fingerprint (or stream, steps or init state) differs is recorded as a mismatch and is never evaluated; a source
that is incomplete, of another recipe or another seed refuses before any folder. None of these numbers is a
scientific result."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402

from experiments.safety_selection.common import canonical_json, read_json, sha256_file  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("b10-regen")
    prepared, manifest = fb.prepared(base)
    one = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", 1102)
    resumed, init = fb.gate_a_resumed(prepared, base / "units" / "1101-a0-e1-a1", 1101)
    units = {1101: resumed, 1102: one}
    settings = fb.fixture_settings(manifest, units, untuned=init)
    regen = base / "regen"
    ea.regenerate(prepared_dir=prepared, seed=1102, reference_path=one / "COMPLETE.json", out_root=regen,
                  session=fb.session(), settings=settings)
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, units=units, init=init, settings=settings,
                        source=regen / "run")


def tampered(world, tmp_path: Path, seed: int, change) -> tuple[Path, ea.Settings]:
    """A copy of a Gate-A-like COMPLETE.json with one field changed, pinned by its new SHA-256."""
    marker = copy.deepcopy(json.loads((world.units[seed] / "COMPLETE.json").read_bytes()))
    change(marker)
    path = tmp_path / "COMPLETE.json"
    path.write_bytes(canonical_json(marker))
    doc = fb.fixture_doc(world.manifest, world.units, untuned=world.init)
    doc["reference_units"][str(seed)]["complete_sha256"] = sha256_file(path)
    doc["reference_units"][str(seed)]["fingerprint_prefixes"] = {
        "e1": marker["checkpoints"]["e1"]["adapter_fingerprint"][:16], "q": None}
    return path, ea.settings_from_doc(doc)


def preflight(world, reference: Path, settings, source=None, recipe=None):
    return ea.preflight(prepared_dir=world.prepared, source_run=source or world.source, reference_path=reference,
                        recipe=recipe or fb.recipe(), settings=settings, plan=ea.make_plan(settings, "certify"))


CHANGES = {
    "e1 fingerprint": lambda m: m["checkpoints"]["e1"].update(adapter_fingerprint="ab" * 32),
    "q fingerprint": lambda m: m["checkpoints"]["q"].update(adapter_fingerprint="cd" * 32),
    "q step": lambda m: m["checkpoints"]["q"].update(step=m["checkpoints"]["q"]["step"] + 1),
    "stream": lambda m: m["trajectory"].update(stream_sha256="ef" * 32),
    "init state": lambda m: m["trajectory"].update(init_fingerprint="01" * 32),
    "retained rows": lambda m: m["trajectory"].update(retained_rows=1),
}
DIFFERING = {"e1 fingerprint": "checkpoints.e1.adapter_fingerprint", "q fingerprint": "checkpoints.q.adapter_fingerprint",
             "q step": "checkpoints.q.step", "stream": "trajectory.stream_sha256",
             "init state": "trajectory.init_fingerprint", "retained rows": "trajectory.retained_rows"}


@pytest.mark.parametrize("what", sorted(CHANGES))
def test_a_mismatch_is_recorded_and_the_state_is_never_evaluated(world, tmp_path, what):
    path, settings = tampered(world, tmp_path, 1102, CHANGES[what])
    record = ea.regenerate(prepared_dir=world.prepared, seed=1102, reference_path=path, out_root=tmp_path / "regen",
                           session=fb.session(), settings=settings)
    assert record["verdict"] == "mismatch" and record["comparison"]["differing"] == [DIFFERING[what]]
    assert read_json(tmp_path / "regen" / "regeneration.json")["verdict"] == "mismatch"
    with pytest.raises(ea.Mismatch, match="never evaluated"):
        preflight(world, path, settings, source=tmp_path / "regen" / "run")
    with pytest.raises(ea.Mismatch):
        preflight(world, path, settings)                         # the fixture's good regeneration, same tampered pin


def test_the_optimizer_fingerprint_is_reported_not_required(world, tmp_path):
    path, settings = tampered(world, tmp_path, 1102,
                              lambda m: m["checkpoints"]["e1"].update(optimizer_fingerprint="99" * 32))
    ctx = preflight(world, path, settings)
    assert ctx.report["equal"] and ctx.report["report_only"]["checkpoints.e1.optimizer_fingerprint"] is False


@pytest.mark.parametrize("what, change, message", [
    ("another seed", lambda m: m["trajectory"].update(seed=1103), "a0 development trajectory"),
    ("another arm", lambda m: m["trajectory"].update(arm="edit-" + "0" * 64), "a0 development trajectory"),
    ("not complete", lambda m: m.update(complete=False), "not a complete run-one"),
    ("another kind", lambda m: m.update(kind="eval-state"), "not a complete run-one"),
    ("another checkpoint", lambda m: m.update(target_checkpoint="e3"), "not an e1 unit"),
    ("another manifest", lambda m: m["identity"].update(manifest_sha256="0" * 64), "identity differs"),
    ("another training identity", lambda m: m["identity"].update(training_identity="0" * 64), "identity differs"),
    ("no q state", lambda m: m["checkpoints"].pop("q"), "holds no q adapter fingerprint")])
def test_a_reference_that_is_not_the_pinned_gate_a_unit_refuses(world, tmp_path, what, change, message):
    path, settings = tampered(world, tmp_path, 1102, change)
    with pytest.raises(ea.Refusal, match=message):
        ea.read_reference(path, 1102, settings)


def test_the_reference_is_read_only_by_its_pin(world, tmp_path):
    s = world.settings
    with pytest.raises(ea.Refusal, match="hashes to"):
        ea.read_reference(world.units[1101] / "COMPLETE.json", 1102, s)          # another unit's bytes
    with pytest.raises(ea.Refusal, match="no Gate A reference unit is pinned"):
        ea.read_reference(world.units[1102] / "COMPLETE.json", 1104, s)
    with pytest.raises(ea.Refusal, match="cannot be read"):
        ea.read_reference(tmp_path / "missing.json", 1102, s)
    doc = fb.fixture_doc(world.manifest, world.units, untuned=world.init)
    doc["reference_units"]["1102"]["fingerprint_prefixes"]["e1"] = "f" * 16
    with pytest.raises(ea.Refusal, match="does not start with the pinned prefix"):
        ea.read_reference(world.units[1102] / "COMPLETE.json", 1102, ea.settings_from_doc(doc))
    assert ea.read_reference(world.units[1102] / "COMPLETE.json", 1102, s)["seed"] == 1102
    assert ea.read_untuned(world.init / "COMPLETE.json", s)["seed"] == 1101
    with pytest.raises(ea.Refusal, match="hashes to"):
        ea.read_untuned(world.units[1101] / "COMPLETE.json", s)


def test_a_source_of_another_seed_than_its_reference_refuses(world):
    with pytest.raises(ea.Refusal, match="hashes to"):
        preflight(world, world.units[1101] / "COMPLETE.json", world.settings)    # the source is seed 1102


def test_a_source_whose_files_changed_refuses_before_any_folder(world, tmp_path):
    import shutil

    copy_dir = tmp_path / "run"
    shutil.copytree(world.source, copy_dir)
    with (copy_dir / "steps.jsonl").open("a") as handle:
        handle.write("\n")
    with pytest.raises(ea.Refusal, match="not usable"):
        preflight(world, world.units[1102] / "COMPLETE.json", world.settings, source=copy_dir)


def test_a_recipe_other_than_the_pinned_one_refuses(world, tmp_path):
    with pytest.raises(ea.Refusal, match="not the one the settings pin"):
        preflight(world, world.units[1102] / "COMPLETE.json", world.settings, recipe=fb.recipe(**{"train.lr": 0.02}))
    with pytest.raises(ea.Refusal, match="not the one the settings pin"):
        ea.regenerate(prepared_dir=world.prepared, seed=1102, reference_path=world.units[1102] / "COMPLETE.json",
                      out_root=tmp_path / "regen", session=fb.session(fb.recipe(**{"train.lr": 0.02})),
                      settings=world.settings)
    assert not (tmp_path / "regen").exists()
    tokens = fb.recipe(**{"model.lora.trainable_tokens": ["<|im_end|>"]})
    doc = fb.fixture_doc(world.manifest, world.units, untuned=world.init, recipe_=tokens)
    with pytest.raises(ea.Refusal, match="trained token rows"):
        ea.check_recipe(tokens, ea.settings_from_doc(doc))


def test_another_prepared_set_refuses(world, tmp_path):
    other, _ = fb.fx.prepare_dir_v3(tmp_path / "other")
    with pytest.raises(ea.Refusal, match="not the pinned one"):
        ea.preflight(prepared_dir=other, source_run=world.source, reference_path=world.units[1102] / "COMPLETE.json",
                     recipe=fb.recipe(), settings=world.settings, plan=ea.make_plan(world.settings, "certify"))


def test_a_regeneration_never_overwrites(world, tmp_path):
    (tmp_path / "regen").mkdir()
    (tmp_path / "regen" / "x").write_text("x")
    with pytest.raises(ea.Refusal, match="not empty"):
        ea.regenerate(prepared_dir=world.prepared, seed=1102, reference_path=world.units[1102] / "COMPLETE.json",
                      out_root=tmp_path / "regen", session=fb.session(), settings=world.settings)


def test_the_fingerprint_report_reads_a_missing_field_as_unequal(world):
    marker = json.loads((world.units[1102] / "COMPLETE.json").read_bytes())
    same = ea.fingerprint_report(marker, marker, world.settings)
    assert same["equal"] and not same["differing"]
    for path in (("trajectory", "stream_sha256"), ("checkpoints", "e1"), ("identity", "training_identity")):
        for side in ("candidate", "reference"):
            other = copy.deepcopy(marker)
            node = other
            for key in path[:-1]:
                node = node[key]
            node.pop(path[-1])
            pair = (other, marker) if side == "candidate" else (marker, other)
            report = ea.fingerprint_report(*pair, world.settings)
            assert not report["equal"] and report["differing"], (path, side)
    both = copy.deepcopy(marker)
    both["trajectory"].pop("stream_sha256")
    assert not ea.fingerprint_report(both, both, world.settings)["equal"]          # missing on both sides


def test_the_regeneration_record_is_text_free_and_names_its_inputs(world):
    record = read_json(world.source.parent / "regeneration.json")
    assert record["kind"] == ea.REGEN_KIND and record["seed"] == 1102 and record["verdict"] == "match"
    assert record["run_complete_sha256"] == sha256_file(world.source / "COMPLETE.json")
    assert record["job_sha256"] == sha256_file(world.source.parent / "job.json")
    assert record["provenance"]["inputs"]["reference_complete"] == sha256_file(world.units[1102] / "COMPLETE.json")
    assert record["provenance"]["settings_sha256"] == world.settings.sha256
    assert record["train_cost"]["steps"] > 0 and "train" in record["stage_seconds"]
    data = (world.source.parent / "regeneration.json").read_text()
    assert not any(t in data for t in fb.harm_prompts(world.prepared))


def train_only(world, out: Path, **fields) -> Path:
    from experiments.safety_selection import runner
    from experiments.safety_selection.planning import make_job

    out.parent.mkdir(parents=True, exist_ok=True)
    job = make_job("run-one", prepared_dir=world.prepared, recipe=fb.recipe(), pin_code=False,
                   out=out.parent / f"{out.name}-job.json", wall_limit_seconds=None, split="dev", seed=1102,
                   role="development", evaluate_bank=None, resume_from=None, replicate_of=None, **fields)
    runner.run_one(job, prepared_dir=world.prepared, out_dir=out, session=fb.session())
    return out


def test_a_source_that_is_not_an_a0_run_or_holds_no_e1_state_refuses(world, tmp_path):
    from experiments.safety_selection.prepare import load_prepared

    group = sorted(load_prepared(world.prepared).groups["dev"])[0]
    removal = train_only(world, tmp_path / "group", arm=group, target_checkpoint="e1")
    with pytest.raises(ea.Refusal, match="not the pinned a0 development run-one") as caught:
        preflight(world, world.units[1102] / "COMPLETE.json", world.settings, source=removal)
    assert not isinstance(caught.value, ea.Mismatch)
    early = train_only(world, tmp_path / "q", arm="a0", target_checkpoint="q")
    with pytest.raises(ea.Refusal, match="holds no saved e1 state") as caught:
        preflight(world, world.units[1102] / "COMPLETE.json", world.settings, source=early)
    assert not isinstance(caught.value, ea.Mismatch)
