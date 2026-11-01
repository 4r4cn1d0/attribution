"""The O-ext unit runner's fix round (notes/oext-unit-verify-code.json finding 1, 2 and 5; notes/oext-unit-verify-spec.json
own mutants) on ENGINEERING FIXTURES: every guard line a verifier mutant removed without a test failing is held here.
The unit and the source unit: the saved state's adapter fingerprint at the plan, another bank, missing dev answers,
the source's manifest, recipe and training identity. Between the plan and the pass: the state file and the stored dev
answers re-hashed, the restored adapter compared. The seal of the completion record, the recipe's guard_over_limit
rule on generated dev answers, theta0's dev-bank access, and an unexpected error in the plan (exit 2, no folder). None
of these numbers is a scientific result."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import oext_unit_fixtures as uf  # noqa: E402

from experiments.safety_selection.common import (canonical_json, jsonl_bytes, read_json, read_jsonl,  # noqa: E402
                                                 sha256_file)
from experiments.safety_selection.config import config_sha256  # noqa: E402

ou, oe, ofx = uf.ou, uf.oe, uf.ofx


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return uf.kept(lambda: uf.build_world(tmp_path_factory.mktemp("oext-unit-fix")))


def refused(world, out: Path, branch: str, match: str, *, settings=None, args=None, **kw) -> str:
    code, stdout, stderr = uf.call(world, args or uf.argv(world, "run", branch, out, **kw), branch, settings=settings)
    assert code == 2 and stdout == "" and not out.exists(), stderr
    message = json.loads(stderr)["refused"]
    assert match in message, message
    return message


def failed(world, out: Path, branch: str, match: str, *, settings=None, **kw) -> str:
    code, stdout, stderr = uf.call(world, uf.argv(world, "run", branch, out, **kw), branch, settings=settings)
    assert code == 1 and stdout == "", stderr
    message = json.loads(stderr)["error"]
    assert match in message, message
    assert (out / "error.txt").is_file() and not (out / "COMPLETE.json").exists()
    return message


def copy_unit(world, kind: str, dest: Path) -> Path:
    shutil.copytree(world.units[kind], dest)
    return dest


def swap_state(unit: Path, donor: Path) -> None:
    shutil.rmtree(unit / "states" / "e1")
    shutil.copytree(donor / "states" / "e1", unit / "states" / "e1")


def after_plan(monkeypatch, hook) -> None:
    """``hook(plan)`` runs after the plan (every check passed) and before the pass."""
    real = ou.prepare_plan

    def planned(*args, **kwargs):
        plan = real(*args, **kwargs)
        hook(plan)
        return plan

    monkeypatch.setattr(ou, "prepare_plan", planned)


def rewrite_json(path: Path, change) -> None:
    doc = json.loads(path.read_bytes())
    change(doc)
    path.write_bytes(canonical_json(doc))


# ----- the unit at the plan (finding 1 d, e; finding 2) -------------------------------------------------------------


def test_a_unit_whose_saved_state_is_another_adapters_refuses_at_the_plan(world, tmp_path):
    """Finding 2: a unit with another unit's e1 state and COMPLETE.json resealed is refused before any folder (exit 2),
    not after the model is loaded."""
    unit = copy_unit(world, "regen", tmp_path / "unit")
    swap_state(unit, world.units["evaluated"])
    uf.reseal(unit)
    refused(world, tmp_path / "a", "full", "saved e1 state's adapter fingerprint is not the one", run=unit)
    refused(world, tmp_path / "b", "128", "saved e1 state's adapter fingerprint is not the one", run=unit,
            source=world.units["source"])


def test_a_unit_that_evaluated_another_bank_refuses(world, tmp_path):
    unit = copy_unit(world, "evaluated", tmp_path / "unit")
    rewrite_json(unit / "job.json", lambda job: job.update(evaluate_bank="selector"))
    uf.reseal(unit)
    refused(world, tmp_path / "a", "128", "the unit evaluated the selector bank", run=unit)


def test_a_dev_evaluated_unit_that_lists_no_dev_answers_refuses(world, tmp_path):
    for k, name in enumerate(("generations.jsonl", "guard.jsonl")):
        unit = copy_unit(world, "evaluated", tmp_path / f"unit{k}")
        (unit / "eval" / "e1" / name).unlink()
        uf.reseal(unit)
        refused(world, tmp_path / f"o{k}", "128", "lists no dev answers or judge records", run=unit)


# ----- the source unit (finding 1 b, c; verify-spec own mutants) -----------------------------------------------------


def test_a_source_unit_on_another_manifest_refuses(world, tmp_path):
    source = copy_unit(world, "source", tmp_path / "source")
    rewrite_json(source / "job.json", lambda job: job.update(manifest_sha256="0" * 64))
    rewrite_json(source / "COMPLETE.json", lambda m: (m["files"].update({"job.json": sha256_file(source / "job.json")}),
                                                      m.update(job_sha256=sha256_file(source / "job.json"))))
    refused(world, tmp_path / "a", "128", "differs in ['manifest_sha256']", run=world.units["regen"], source=source)


def test_a_source_unit_outside_the_allowed_recipes_refuses(world, tmp_path):
    source = copy_unit(world, "source", tmp_path / "source")
    rewrite_json(source / "COMPLETE.json", lambda m: m["identity"].update(recipe_sha256="0" * 64))
    refused(world, tmp_path / "a", "128", "not made under an allowed recipe", run=world.units["regen"], source=source)
    # the same source passes once its recipe is allowed (the refusal is the allow-list's, nothing else)
    settings = uf.settings_for(world, "128", recipes__allowed={"fixture": config_sha256(world.recipe), "x": "0" * 64})
    code, _, stderr = uf.call(world, uf.argv(world, "run", "128", tmp_path / "b", run=world.units["regen"],
                                             source=source), "128", settings=settings)
    assert code == 0, stderr


def test_a_source_unit_of_another_training_identity_refuses(world, tmp_path):
    source = copy_unit(world, "source", tmp_path / "source")
    rewrite_json(source / "COMPLETE.json", lambda m: m["identity"].update(training_identity="0" * 64))
    refused(world, tmp_path / "a", "128", "not made under an allowed recipe", run=world.units["regen"], source=source)


# ----- between the plan and the pass (finding 1 a, f) ----------------------------------------------------------------


def test_a_state_file_changed_after_the_plan_is_caught_before_the_load(world, tmp_path, monkeypatch):
    unit = copy_unit(world, "regen", tmp_path / "unit")
    after_plan(monkeypatch, lambda plan: swap_state(unit, world.units["evaluated"]))
    failed(world, tmp_path / "out", "full", "changed after its dependency receipt was written", run=unit)


def test_the_restored_state_must_be_the_checked_units_adapter(world, tmp_path, monkeypatch):
    """The last guard: with the receipt check bypassed, a swapped state is still never evaluated as the unit's."""
    from experiments.safety_selection import runner

    unit = copy_unit(world, "regen", tmp_path / "unit")
    monkeypatch.setattr(runner, "_same_state", lambda state_dir, receipt: None)
    after_plan(monkeypatch, lambda plan: swap_state(unit, world.units["evaluated"]))
    failed(world, tmp_path / "out", "full", "the restored state is not the checked unit's adapter", run=unit)


@pytest.mark.parametrize("route", ["unit_eval", "source_unit"])
def test_stored_dev_answers_changed_after_the_plan_are_caught(world, tmp_path, monkeypatch, route):
    if route == "unit_eval":
        root = copy_unit(world, "evaluated", tmp_path / "unit")
        kw = {"run": root}
    else:
        root = copy_unit(world, "source", tmp_path / "source")
        kw = {"run": world.units["regen"], "source": root}
    path = root / "eval" / "e1" / "guard.jsonl"
    rows = read_jsonl(path)

    def change(plan):
        rows[0]["guard_stop_reason"] = "changed"           # still a valid JSONL file
        path.write_bytes(jsonl_bytes(rows))

    after_plan(monkeypatch, change)
    failed(world, tmp_path / "out", "128", "changed since its COMPLETE.json was written", **kw)


def test_stored_dev_answers_changed_while_read_are_caught(world, tmp_path, monkeypatch):
    unit = copy_unit(world, "evaluated", tmp_path / "unit")
    path = unit / "eval" / "e1" / "guard.jsonl"
    real = oe.dev_answers_from_eval

    def reading(folder, items):
        rows = read_jsonl(path)
        rows[0]["guard_stop_reason"] = "changed"
        path.write_bytes(jsonl_bytes(rows))
        return real(folder, items)

    monkeypatch.setattr(oe, "dev_answers_from_eval", reading)
    failed(world, tmp_path / "out", "128", "changed while they were read", run=unit)


# ----- the seal of the completion record (finding 1 g) ---------------------------------------------------------------


def test_the_completion_record_is_scanned_for_texts(world, tmp_path):
    text = ofx.PHTEST_ROWS[0][1]
    settings = uf.settings_for(world, "128", seal__rule=text)         # the record holds settings seal.rule
    assert len(text) >= settings.doc["seal"]["text_scan_min_chars"]
    failed(world, tmp_path / "out", "128", "the completion record would hold a prompt", settings=settings,
           untuned=True, checkpoint=None)


# ----- generated dev answers and theta0 (finding 1 h; untuned access) ------------------------------------------------


def test_generated_dev_answers_follow_the_recipes_guard_over_limit_rule(world, tmp_path):
    from experiments.safety_selection.scoring import GUARD_OVER_LIMIT

    tiny = uf.recipe(**{"guard.max_input_tokens": 2})
    assert tiny["generation"]["guard_over_limit"] == "unscored"
    rec_file = tmp_path / "tiny.json"
    rec_file.write_bytes(canonical_json(tiny))
    settings = ou.settings_from_doc(uf.settings_doc(world.manifest, world.oext["full"].settings.sha256, tiny))
    out = tmp_path / "out"
    code, _, stderr = uf.call(world, uf.argv(world, "run", "full", out, untuned=True, checkpoint=None,
                                             recipe_file=rec_file), "full", settings=settings)
    assert code == 0, stderr
    guard = read_jsonl(out / ou.DEV_DIR / ou.DEV_GUARD)
    assert guard and all(g["valid"] is False and g["reason"] == GUARD_OVER_LIMIT for g in guard)
    assert read_json(out / "job.json")["dev100_route"] == "generated"


def test_theta0s_dev_bank_access_is_checked(world, tmp_path):
    settings = uf.settings_for(world, "128", untuned__access_seed=9101)      # a reference seed
    refused(world, tmp_path / "a", "128", "namespace reference", settings=settings, untuned=True, checkpoint=None)


# ----- an unexpected error in the plan (finding 5) -------------------------------------------------------------------


@pytest.mark.parametrize("error", [KeyError("generation"), TypeError("not a dict")])
def test_an_unexpected_error_in_the_plan_refuses_with_exit_2_and_no_folder(world, tmp_path, monkeypatch, error):
    def broken(*args, **kwargs):
        raise error

    monkeypatch.setattr(ou, "check_recipe", broken)
    out = tmp_path / "out"
    code, stdout, stderr = uf.call(world, uf.argv(world, "run", "128", out, untuned=True, checkpoint=None), "128")
    assert code == 2 and stdout == "" and not out.exists(), stderr
    assert json.loads(stderr)["refused"].startswith(f"unexpected {type(error).__name__}")
