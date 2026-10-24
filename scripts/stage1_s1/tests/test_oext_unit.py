"""The O-ext unit runner (scripts/stage1_s1/oext_unit.py; addendum section 20 point 5, section 11 points 1, 7 and 13,
section 13, section 24 point 2; REV4 section 6.3: LN-12, LN-14, LN-19, LN-24; B15 brief Q15) on ENGINEERING FIXTURES:
the pinned settings; the refusals before any folder (the pending branch first); each dev-100 route (the unit's own
answers, the source unit's stored answers under Branch 128, answers generated here) with oext_eval's rules applied
unchanged; theta0 as the policy with its adapter disabled; LN-14's report under Branch 128 only; the folder, its
completion record and the seal (no text and no outcome outside the answer files and oext_eval's summary; stdout holds
counts of prompts and hashes only). None of these numbers is a scientific result."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import oext_unit_fixtures as uf  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection.common import canonical_json, read_json, read_jsonl, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402
from experiments.safety_selection.ledger import verify_files  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.limits import overrefusal_checks as oc  # noqa: E402

ou, oe, ofx = uf.ou, uf.oe, uf.ofx
CUT = uf.CUT
PINNED_SETTINGS_SHA256 = "18957b683abd0452d77a426a1839dd0bf6ac51d3da484f093795d5e9e1ea1aa3"
ENGINE_X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
CONFIGS = Path(en.__file__).resolve().parent / "configs"
RECIPES = {"B": "study-kt-olmo2-1b-r64-b-mb4-20261008", "S": "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008",
           "G": "study-kt-olmo2-1b-r64-g-mb4-20261008"}
OUTCOME_KEYS = {"o", "refused", "invalid", "flags", "share", "changed", "flags_agree", "count_move", "pass",
                "output_tokens", "capped", "empty", "longer_than_cut", "text", "valid", "refusal", "guard_answer"}
DEV_STAGE_KEYS = {"stage", "status", "start_s", "start_utc", "end_s", "seconds", "end_utc", "memory", "checkpoint",
                  "prompts", "prompt_tokens", "max_new_tokens", "items"}


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return uf.kept(lambda: uf.build_world(tmp_path_factory.mktemp("oext-unit")))


def done(world, out: Path, command: str, branch: str, *, loader_options: dict | None = None, **kw) -> dict:
    """A finished pass: (exit 0) its printed brief, its folder and its records."""
    code, stdout, stderr = uf.call(world, uf.argv(world, command, branch, out, **kw), branch,
                                   **(loader_options or {}))
    assert code == 0, stderr
    return {"brief": json.loads(stdout), "stdout": stdout, "out": out, "marker": read_json(out / "COMPLETE.json"),
            "job": read_json(out / "job.json")}


def refused(world, out: Path, command: str, branch: str, match: str, *, settings=None, oext_settings=None,
            args=None, **kw) -> str:
    code, stdout, stderr = uf.call(world, args or uf.argv(world, command, branch, out, **kw), branch,
                                   settings=settings, oext_settings=oext_settings)
    assert code == 2 and stdout == "" and not out.exists(), stderr
    message = json.loads(stderr)["refused"]
    assert match in message, message
    return message


def summary(out: Path, name: str = oe.SUMMARY) -> dict:
    return json.loads((out / name).read_bytes())


def eval_rows(unit: Path, name: str) -> dict:
    return {r["prompt_id"]: r for r in read_jsonl(unit / "eval" / "e1" / name) if r.get("kind") == "overrefusal"}


def restored_policy(world, unit: Path | None, **loader_options):
    """A fresh fixture policy with the unit's e1 state (None: as loaded)."""
    from experiments.safety_selection.ledger import RunLedger, create_run_dir

    session = uf.session(world.recipe, **loader_options)
    run_dir = create_run_dir(world.base / f"scratch-{len(list(world.base.glob('scratch-*')))}")
    policy = session.policy(RunLedger(run_dir), run_dir)
    if unit is not None:
        en.load_state(unit / "states" / "e1", policy.named, None, "cpu")
    return policy


def greedy(policy, prompts: list[str], cap: int, *, disabled: bool = False) -> list[list[int]]:
    import contextlib

    from experiments.safety_selection.textproc import encode_generation_prompt

    codec = policy.codec
    ids = [encode_generation_prompt(codec, p, 400) for p in prompts]
    with policy.model.disable_adapter() if disabled else contextlib.nullcontext():
        out = en.greedy_generate(policy.model, ids, max_new_tokens=cap, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                                 device="cpu", batch_size=3)
    return [list(g.output_ids) for g in out]


def dev_prompts(world) -> dict:
    from experiments.safety_selection.prepare import load_prepared

    bank = load_prepared(world.prepared, world.manifest, banks=("dev",)).banks["dev"]
    return {i["prompt_id"]: i["prompt"] for i in bank if i["kind"] == "overrefusal"}


# ----- 1. the settings ----------------------------------------------------------------------------------------------


def test_the_settings_file_is_pinned_canonical_and_loads_on_engine_x():
    assert ou.SETTINGS_SHA256 == PINNED_SETTINGS_SHA256 == sha256_file(ou.SETTINGS_PATH)
    pinned = ou.load_pinned_settings()
    assert pinned.sha256 == PINNED_SETTINGS_SHA256 and canonical_json(pinned.doc) == ou.SETTINGS_PATH.read_bytes()
    doc = pinned.doc
    assert doc["engine_x"] == ENGINE_X and doc["name"] == ou.SETTINGS_NAME and doc["owner"] == ou.OWNER
    with pytest.raises(s1.Refusal, match="hash to"):
        ou.load_pinned_settings(ou.SETTINGS_PATH, "0" * 64)


def test_the_settings_pin_the_shared_oext_function_and_its_settings():
    doc = ou.load_pinned_settings().doc
    assert doc["oext"]["module"] == oe.OWNER and doc["oext"]["module_sha256"] == oe.module_sha256()
    assert doc["oext"]["settings"] == {"path": "scripts/stage1_s1/settings/oext_eval.json",
                                       "sha256": oe.SETTINGS_SHA256}
    assert oe.load_pinned_settings().sha256 == doc["oext"]["settings"]["sha256"]


def test_the_settings_pin_the_stage1_prepared_set_and_recipes_with_one_cap_and_one_judge():
    doc = ou.load_pinned_settings().doc
    b10 = s1.strict_json((ou.HERE / "settings" / "eval_adapter.json").read_bytes())
    assert doc["prepared"] == {**doc["prepared"], "manifest_sha256": b10["prepared"]["manifest_sha256"], "bank": "dev"}
    recipes = {k: load_recipe(CONFIGS / f"{v}.json") for k, v in RECIPES.items()}
    assert doc["recipes"]["allowed"] == {k: config_sha256(r) for k, r in recipes.items()}
    for r in recipes.values():
        assert s1.sha256_bytes(canonical_json(r["generation"])) == doc["recipes"]["generation_sha256"]
        assert s1.sha256_bytes(canonical_json(r["guard"])) == doc["recipes"]["guard_sha256"]
        assert r["generation"]["max_new_tokens"] == 2048            # the Gate A cap (Branch full's cap)
    assert doc["unit"]["checkpoints"] == ["e1"] and doc["untuned"]["access_seed"] == 1101
    assert doc["seal"]["answer_files"] == list(ou.ANSWER_FILES)


@pytest.mark.parametrize("dotted, value", [
    ("version", 2), ("owner", "scripts/stage1_s1/other.py"), ("label_entries", {"x.y": "0" * 64}),
    ("oext.module", "scripts/stage1_s1/eval_adapter.py"), ("oext.settings.path", "x.json"),
    ("oext.module_sha256", "abc"), ("prepared.bank", "selector"), ("prepared.manifest_sha256", None),
    ("recipes.allowed", {}), ("recipes.generation_sha256", "x"), ("unit.role", "reference"),
    ("unit.checkpoints", ["q"]), ("unit.checkpoints", []), ("dev100.source_files", ["COMPLETE.json"]),
    ("dev100.routes.generated", ""), ("untuned.access_seed", 0), ("transfer.state", "run"),
    ("outputs.job_kind", "run-one"), ("ledger.stages", ["generate"]), ("ledger.state_stages", {}),
    ("seal.answer_files", []), ("seal.text_scan_min_chars", 0), ("exit_codes", {"0": "ok"}), ("extra", 1),
])
def test_settings_outside_the_rules_refuse(dotted, value):
    doc = uf.real_doc()
    ofx.set_dotted(doc, dotted, value)
    with pytest.raises(s1.Refusal):
        ou.validate_settings(doc)


def test_ln14s_bar_is_read_at_w1_18s_rates_at_400_prompts():
    """Addendum section 24 point 2: at n = 400, at least 388 of 400 flags agree and the refused count moves by at
    most 8 (the pinned O-ext settings' bar, W1-18's 97 and 2 per 100)."""
    bar = oe.load_pinned_settings().doc["transfer"]["bar"]
    ids = [f"p{k:03d}" for k in range(400)]

    def flags(refused):
        return {i: (r, True, "Yes" if r else "No") for i, r in zip(ids, refused)}

    full = flags([k < 40 for k in range(400)])
    for moved, agree_expected, passes in ((8, 392, True), (9, 391, False)):
        cut = flags([k < 40 - moved for k in range(400)])
        out = oe.transfer_bar(full, cut, ids, bar)
        assert (out["flags_agree"], out["count_move"], out["pass"]) == (agree_expected, moved, passes)
    swap = flags([(k < 40 and k >= 6) or (40 <= k < 46) for k in range(400)])       # 12 disagree, no move
    assert oe.transfer_bar(full, swap, ids, bar)["pass"] is True                       # 388 agree
    swap = flags([(k < 40 and k >= 7) or (40 <= k < 47) for k in range(400)])       # 14 disagree
    assert oe.transfer_bar(full, swap, ids, bar)["pass"] is False                      # 386 agree


# ----- 2. refusals before any folder ----------------------------------------------------------------------------------


def test_the_real_settings_refuse_under_the_pending_branch(world, tmp_path):
    """The committed O-ext settings are pending W1-18 (section 13): every command refuses before any folder."""
    for command, kw in (("run", {"untuned": True, "checkpoint": None}), ("transfer", {"untuned": True,
                                                                                         "checkpoint": None})):
        args = uf.argv(world, command, "128", tmp_path / command, **kw)
        code, stdout, stderr = uf.call(world, args, "128", settings=ou.load_pinned_settings(),
                                       oext_settings=oe.load_pinned_settings())
        assert code == 2 and stdout == "" and not (tmp_path / command).exists()
        assert "pending W1-18 (addendum section 13): no O-ext pass runs" in json.loads(stderr)["refused"]


def test_the_pending_branch_refuses_even_with_fixture_inputs(world, tmp_path):
    for k, command in enumerate(("run", "transfer")):        # refused first, before any input is read
        refused(world, tmp_path / f"o{k}", command, "pending", "no O-ext pass runs", untuned=True, checkpoint=None)


def test_the_state_options_follow_the_rules(world, tmp_path):
    u = world.units
    refused(world, tmp_path / "a", "run", "128", "needs --checkpoint", run=u["evaluated"], checkpoint=None)
    args = uf.argv(world, "run", "128", tmp_path / "b", untuned=True, checkpoint=None) + ["--checkpoint", "e1"]
    refused(world, tmp_path / "b", "run", "128", "takes no --checkpoint", args=args)
    refused(world, tmp_path / "c", "run", "128", "takes no --checkpoint", untuned=True, checkpoint=None,
            source=u["source"])
    refused(world, tmp_path / "d", "transfer", "128", "never --run", run=u["evaluated"])


def test_ln14_runs_under_branch_128_only(world, tmp_path):
    for k, branch in enumerate(("full", "full_reason")):
        refused(world, tmp_path / f"t{k}", "transfer", branch, "Branch 128 only", untuned=True, checkpoint=None)


def test_the_dev100_source_belongs_to_branch_128_and_a_train_only_unit(world, tmp_path):
    u = world.units
    refused(world, tmp_path / "a", "run", "128", "--dev100-source is needed", run=u["regen"])
    refused(world, tmp_path / "b", "run", "full", "Branch 128 only", run=u["regen"], source=u["source"])
    refused(world, tmp_path / "c", "run", "128", "holds its own dev-100 answers", run=u["evaluated"],
            source=u["source"])


def test_a_source_unit_must_be_the_regenerated_units_source(world, tmp_path):
    u = world.units
    refused(world, tmp_path / "a", "run", "128", "differs in ['seed']", run=u["regen"], source=u["evaluated"])
    fake = tmp_path / "fake-source"
    shutil.copytree(u["source"], fake)
    marker = json.loads((fake / "COMPLETE.json").read_bytes())
    marker["checkpoints"]["e1"]["adapter_fingerprint"] = "f" * 64
    (fake / "COMPLETE.json").write_bytes(canonical_json(marker))
    refused(world, tmp_path / "b", "run", "128", "adapter fingerprint is not the regenerated unit's", run=u["regen"],
            source=fake)


def test_a_source_unit_is_read_by_its_complete_json(world, tmp_path):
    u = world.units
    part = tmp_path / "part"                                # packed in part: only the required files
    for rel in ("COMPLETE.json", "job.json", "eval/e1/generations.jsonl", "eval/e1/guard.jsonl"):
        (part / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(u["source"] / rel, part / rel)
    out = tmp_path / "ok"
    code, _, stderr = uf.call(world, uf.argv(world, "run", "128", out, run=u["regen"], source=part), "128")
    assert code == 0, stderr
    tampered = tmp_path / "tampered"
    shutil.copytree(part, tampered)
    rows = (tampered / "eval/e1/generations.jsonl").read_bytes()
    (tampered / "eval/e1/generations.jsonl").write_bytes(rows + b"\n")
    refused(world, tmp_path / "a", "run", "128", "not the ones its COMPLETE.json lists", run=u["regen"],
            source=tampered)
    extra = tmp_path / "extra"
    shutil.copytree(part, extra)
    (extra / "eval/e1/more.jsonl").write_text("{}\n")
    refused(world, tmp_path / "b", "run", "128", "not the ones its COMPLETE.json lists", run=u["regen"], source=extra)
    missing = tmp_path / "missing"
    shutil.copytree(part, missing)
    (missing / "eval/e1/guard.jsonl").unlink()
    refused(world, tmp_path / "c", "run", "128", "lacks ['eval/e1/guard.jsonl']", run=u["regen"], source=missing)
    jobless = tmp_path / "jobless"
    shutil.copytree(part, jobless)
    job = json.loads((jobless / "job.json").read_bytes())
    job["arm"] = "edit-" + "0" * 64
    (jobless / "job.json").write_bytes(canonical_json(job))
    marker = json.loads((jobless / "COMPLETE.json").read_bytes())
    marker["files"]["job.json"] = sha256_file(jobless / "job.json")
    (jobless / "COMPLETE.json").write_bytes(canonical_json(marker))
    refused(world, tmp_path / "d", "run", "128", "job.json is not the one", run=u["regen"], source=jobless)
    marker["job_sha256"] = sha256_file(jobless / "job.json")
    (jobless / "COMPLETE.json").write_bytes(canonical_json(marker))
    refused(world, tmp_path / "e", "run", "128", "differs in ['arm']", run=u["regen"], source=jobless)


def test_a_unit_must_verify_and_be_the_recipes_on_this_engine(world, tmp_path):
    u = world.units
    broken = tmp_path / "broken"
    shutil.copytree(u["evaluated"], broken)
    (broken / "eval/e1/generations.jsonl").write_bytes(b"")
    refused(world, tmp_path / "a", "run", "128", "the unit is not usable", run=broken)
    other = uf.recipe(**{"arc.batch_size": 2})               # another config, the same training identity
    rec_file = tmp_path / "other.json"
    rec_file.write_bytes(canonical_json(other))
    settings = uf.settings_for(world, "128", recipes__allowed={"fixture": config_sha256(world.recipe),
                                                               "other": config_sha256(other)})
    refused(world, tmp_path / "b", "run", "128", "not the unit's own recipe", run=u["evaluated"], recipe_file=rec_file,
            settings=settings)
    engine = tmp_path / "engine"
    shutil.copytree(u["evaluated"], engine)
    ident = json.loads((engine / "identity.json").read_bytes())
    ident["code_sha256"] = "0" * 64
    (engine / "identity.json").write_bytes(canonical_json(ident))
    marker = json.loads((engine / "COMPLETE.json").read_bytes())
    marker["identity"]["code_sha256"] = "0" * 64
    (engine / "COMPLETE.json").write_bytes(canonical_json(marker))
    uf.reseal(engine)
    refused(world, tmp_path / "c", "run", "128", "another engine", run=engine)
    nostate = tmp_path / "nostate"
    shutil.copytree(u["evaluated"], nostate)
    job = json.loads((nostate / "job.json").read_bytes())
    job["target_checkpoint"] = "q"
    (nostate / "job.json").write_bytes(canonical_json(job))
    uf.reseal(nostate)
    refused(world, tmp_path / "d", "run", "128", "differs in ['target_checkpoint']", run=nostate)


def test_the_recipe_and_the_prepared_set_are_the_pinned_ones(world, tmp_path):
    u = world.units
    refused(world, tmp_path / "a", "run", "128", "not one of the settings' allowed recipes", run=u["evaluated"],
            settings=uf.settings_for(world, "128", recipes__allowed={"x": "0" * 64}))
    refused(world, tmp_path / "b", "run", "128", "generation block", run=u["evaluated"],
            settings=uf.settings_for(world, "128", recipes__generation_sha256="0" * 64))
    refused(world, tmp_path / "c", "run", "128", "guard block", run=u["evaluated"],
            settings=uf.settings_for(world, "128", recipes__guard_sha256="0" * 64))
    refused(world, tmp_path / "d", "run", "128", "not the pinned one", run=u["evaluated"],
            settings=uf.settings_for(world, "128", prepared__manifest_sha256="0" * 64))
    three = ofx.inputs(tmp_path / "dev3", branch="128", cut=CUT, dev=3)      # the same bank and W1-18 bytes
    refused(world, tmp_path / "e", "run", "128", "over-refusal prompts", untuned=True, checkpoint=None,
            oext_settings=three.settings,
            settings=uf.settings_for(world, "128", oext__settings__sha256=three.settings.sha256))


def test_the_oext_pins_and_inputs_are_checked(world, tmp_path):
    u = world.units
    refused(world, tmp_path / "a", "run", "128", "O-ext settings are not the ones", run=u["evaluated"],
            settings=uf.settings_for(world, "128", oext__settings__sha256="0" * 64))
    refused(world, tmp_path / "b", "run", "128", "O-ext module is not the one", run=u["evaluated"],
            settings=uf.settings_for(world, "128", oext__module_sha256="0" * 64))
    args = uf.argv(world, "run", "128", tmp_path / "c", run=u["evaluated"])
    _, other, _ = ofx.bank_files(tmp_path / "other-bank", ofx.PHTEST_ROWS[:4])      # another record's bytes
    args[args.index("--oext-record") + 1] = str(other)
    refused(world, tmp_path / "c", "run", "128", "bank record hashes to", args=args)
    args = uf.argv(world, "run", "128", tmp_path / "d", run=u["evaluated"])
    args[args.index("--w1-18-record") + 1] = str(world.oext["full"].w1_18)
    refused(world, tmp_path / "d", "run", "128", "W1-18's record hashes to", args=args)


def test_an_existing_out_folder_refuses_and_is_untouched(world, tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep.txt").write_text("x")
    code, stdout, stderr = uf.call(world, uf.argv(world, "run", "128", out, untuned=True, checkpoint=None), "128")
    assert code == 2 and stdout == "" and "never replaces" in json.loads(stderr)["refused"]
    assert sorted(p.name for p in out.iterdir()) == ["keep.txt"]


# ----- 3. the routes ------------------------------------------------------------------------------------------------


def test_branch_128_on_a_dev_evaluated_unit_cuts_its_own_answers(world, tmp_path):
    unit = world.units["evaluated"]
    r = done(world, tmp_path / "out", "run", "128", run=unit)
    s, out, codec = summary(r["out"]), r["out"], uf.fx.fixture_codec()
    assert r["brief"]["dev100_route"] == "unit_eval" and s["branch"] == "128" and s["route"] == \
        world.oext["128"].settings.doc["routes"]["128"]
    assert s["cap"] == {"cut_tokens": CUT, "dev100_answers_max_new_tokens": 8, "phtest_max_new_tokens": CUT}
    gens = eval_rows(unit, "generations.jsonl")
    cuts = {g["prompt_id"]: g for g in read_jsonl(out / oe.GUARD) if g["form"] == "cut"}
    longer = {p for p, g in gens.items() if g["output_tokens"] > CUT}
    assert longer and set(cuts) == longer
    for pid in longer:
        assert cuts[pid]["text"] == codec.decode(gens[pid]["output_ids"][:CUT])
    assert s["provenance"]["inputs"]["dev100/generations.jsonl"] == sha256_file(unit / "eval/e1/generations.jsonl")
    phtest = [g["output_ids"] for g in read_jsonl(out / oe.GENERATIONS)]
    assert phtest == greedy(restored_policy(world, unit), [p for _, p in ofx.PHTEST_ROWS], CUT)
    assert not (out / ou.DEV_DIR).exists()
    marker = r["marker"]
    assert marker["dev100_inputs"] == {"dev100/generations.jsonl": sha256_file(unit / "eval/e1/generations.jsonl"),
                                       "dev100/guard.jsonl": sha256_file(unit / "eval/e1/guard.jsonl")}
    assert marker["unit"]["complete_sha256"] == sha256_file(unit / "COMPLETE.json")
    assert marker["adapter_fingerprint"] == read_json(unit / "COMPLETE.json")["checkpoints"]["e1"]["adapter_fingerprint"]


def test_branch_full_on_a_dev_evaluated_unit_reuses_its_flags(world, tmp_path):
    unit = world.units["evaluated"]
    r = done(world, tmp_path / "out", "run", "full", run=unit)
    s = summary(r["out"])
    assert s["branch"] == "full" and s["cap"]["phtest_max_new_tokens"] == 8 and s["sensitivity_cut"] is not None
    stored = eval_rows(unit, "guard.jsonl")
    refused_ = sum(g["valid"] and g["refusal"] == "Yes" for g in stored.values())
    assert s["o"]["by_source"]["dev100"]["refused"] == refused_ and s["o"]["by_source"]["dev100"]["prompts"] == 2
    phtest = [g["output_ids"] for g in read_jsonl(r["out"] / oe.GENERATIONS)]
    assert phtest == greedy(restored_policy(world, unit), [p for _, p in ofx.PHTEST_ROWS], 8)


def test_branch_128_on_a_regenerated_unit_cuts_the_source_units_stored_answers(world, tmp_path):
    regen, source = world.units["regen"], world.units["source"]
    fp = read_json(regen / "COMPLETE.json")["checkpoints"]["e1"]["adapter_fingerprint"]
    assert fp == read_json(source / "COMPLETE.json")["checkpoints"]["e1"]["adapter_fingerprint"]   # LN-12 accept
    r = done(world, tmp_path / "out", "run", "128", run=regen, source=source)
    out, codec = r["out"], uf.fx.fixture_codec()
    assert r["brief"]["dev100_route"] == "source_unit" and r["job"]["dev100_source"] == str(source)
    gens = eval_rows(source, "generations.jsonl")
    cuts = {g["prompt_id"]: g["text"] for g in read_jsonl(out / oe.GUARD) if g["form"] == "cut"}
    assert cuts == {p: codec.decode(g["output_ids"][:CUT]) for p, g in gens.items() if g["output_tokens"] > CUT}
    marker = r["marker"]
    assert marker["dev100_source"]["complete_sha256"] == sha256_file(source / "COMPLETE.json")
    assert marker["dev100_source"]["files"] == {rel: sha256_file(source / rel) for rel in
                                                ("job.json", "eval/e1/generations.jsonl", "eval/e1/guard.jsonl")}
    deps = read_json(out / "dependencies.json")["dependencies"]
    assert [d["role"] for d in deps] == ["oext_state", "dev100_source"]
    phtest = [g["output_ids"] for g in read_jsonl(out / oe.GENERATIONS)]
    assert phtest == greedy(restored_policy(world, regen), [p for _, p in ofx.PHTEST_ROWS], CUT)


def test_branch_full_on_a_regenerated_unit_generates_the_dev100_at_the_recipes_cap(world, tmp_path):
    regen = world.units["regen"]
    r = done(world, tmp_path / "out", "run", "full", run=regen)
    out = r["out"]
    assert r["brief"]["dev100_route"] == "generated"
    prompts = dev_prompts(world)
    rows = read_jsonl(out / ou.DEV_DIR / ou.DEV_GENERATIONS)
    assert [g["prompt_id"] for g in rows] == list(prompts) and all(g["kind"] == "overrefusal" for g in rows)
    assert [g["output_ids"] for g in rows] == greedy(restored_policy(world, regen), list(prompts.values()), 8)
    guard = read_jsonl(out / ou.DEV_DIR / ou.DEV_GUARD)
    assert [g["prompt_id"] for g in guard] == list(prompts)
    s = summary(out)
    assert s["o"]["by_source"]["dev100"]["refused"] == sum(g["valid"] and g["refusal"] == "Yes" for g in guard)
    assert s["provenance"]["inputs"]["dev100/generations.jsonl"] == sha256_file(out / ou.DEV_DIR / ou.DEV_GENERATIONS)
    stages = [x for x in read_jsonl(out / "ledger.jsonl") if x["stage"] in ou.DEV_STAGES]
    assert [x["stage"] for x in stages] == list(ou.DEV_STAGES) and stages[0]["max_new_tokens"] == 8
    assert all(set(x) <= DEV_STAGE_KEYS for x in stages)


@pytest.mark.parametrize("branch", ["128", "full"])
def test_theta0_is_the_policy_with_its_adapter_disabled(world, tmp_path, branch):
    r = done(world, tmp_path / "out", "run", branch, untuned=True, checkpoint=None,
             loader_options={"perturb": True})
    out = r["out"]
    prompts = dev_prompts(world)
    policy = restored_policy(world, None, perturb=True)
    base_dev = greedy(policy, list(prompts.values()), 8, disabled=True)
    rows = read_jsonl(out / ou.DEV_DIR / ou.DEV_GENERATIONS)
    assert [g["output_ids"] for g in rows] == base_dev
    cap = CUT if branch == "128" else 8
    texts = [p for _, p in ofx.PHTEST_ROWS]
    base_ph = greedy(policy, texts, cap, disabled=True)
    assert [g["output_ids"] for g in read_jsonl(out / oe.GENERATIONS)] == base_ph
    assert greedy(policy, texts, cap) != base_ph or greedy(policy, list(prompts.values()), 8) != base_dev
    assert r["job"]["state"] == "untuned" and r["job"]["run"] is None and r["brief"]["dev100_route"] == "generated"
    assert r["marker"]["adapter_fingerprint"] == en.lora_fingerprint(policy.named)       # unchanged by the pass
    state = [x for x in read_jsonl(out / "ledger.jsonl") if x["stage"] == "untuned_state"]
    assert len(state) == 1 and state[0]["adapter"] == "disabled"


def test_ln14_is_theta0s_phtest_at_the_full_cap_judged_full_and_cut(world, tmp_path):
    r = done(world, tmp_path / "out", "transfer", "128", untuned=True, checkpoint=None,
             loader_options={"perturb": True})
    out = r["out"]
    s = summary(out, oe.TRANSFER_SUMMARY)
    assert s["kind"] == oe.TRANSFER_KIND and s["branch"] == "128" and s["cap"] == {"cut_tokens": CUT,
                                                                                   "phtest_max_new_tokens": 8}
    assert s["bar"]["bar"] == {"min_flags_agree": 97, "max_count_move": 2, "per_prompts": 100}
    policy = restored_policy(world, None, perturb=True)
    gens = read_jsonl(out / oe.TRANSFER_GENERATIONS)
    assert [g["output_ids"] for g in gens] == greedy(policy, [p for _, p in ofx.PHTEST_ROWS], 8, disabled=True)
    names = {p.name for p in out.iterdir()}
    assert set(oe.TRANSFER_FILES) <= names and not names & set(oe.OUTPUT_FILES) and ou.DEV_DIR not in names
    assert r["brief"]["dev100_route"] is None and r["brief"]["prompts"] == {"phtest": len(ofx.PHTEST_ROWS)}
    assert r["marker"]["summary_file"] == {oe.TRANSFER_SUMMARY: sha256_file(out / oe.TRANSFER_SUMMARY)}
    # a report only: the O-ext settings (and their branch) are unchanged whatever the bar says
    assert world.oext["128"].settings.doc["cap"]["branch"] == "128"
    assert oe.load_pinned_settings().doc["cap"]["branch"] == oe.PENDING


# ----- 4. the folder and the seal -----------------------------------------------------------------------------------


def _all_texts(world, out: Path) -> list[str]:
    texts = list(dev_prompts(world).values()) + [p for _, p in ofx.PHTEST_ROWS]
    for rel in ou.ANSWER_FILES:
        if (out / rel).is_file():
            texts += [row[f] for row in read_jsonl(out / rel) for f in ("text", "guard_answer")
                      if isinstance(row.get(f), str)]
    return [t for t in texts if len(t) >= 6]


@pytest.mark.parametrize("command, branch, kind", [("run", "128", "evaluated"), ("run", "full", "regen"),
                                                   ("transfer", "128", "untuned")])
def test_the_folder_verifies_and_no_text_or_outcome_leaves_the_answer_files(world, tmp_path, command, branch, kind):
    kw = {"untuned": True, "checkpoint": None} if kind == "untuned" else {"run": world.units[kind]}
    r = done(world, tmp_path / "out", command, branch, **kw)
    out, marker = r["out"], r["marker"]
    assert verify_files(out) == []
    for rel, digest in {**marker["answer_files"], **marker["summary_file"]}.items():
        assert marker["files"][rel] == digest == sha256_file(out / rel)
    assert set(marker["answer_files"]) == {rel for rel in ou.ANSWER_FILES if (out / rel).is_file()}
    assert r["job"]["kind"] == ou.JOB_KIND and r["job"]["oext"]["branch"] == branch
    assert r["job"]["settings_sha256"] == uf.settings_for(world, branch).sha256
    texts = _all_texts(world, out)
    for path in out.rglob("*"):
        rel = path.relative_to(out).as_posix()
        if path.is_file() and rel not in ou.ANSWER_FILES:
            assert not s1._text_hits(path.read_bytes(), texts), rel
    assert not s1._text_hits(r["stdout"].encode(), texts)

    def keys(node, found):
        if isinstance(node, dict):
            for k, v in node.items():
                found.add(k)
                keys(v, found)
        elif isinstance(node, list):
            for v in node:
                keys(v, found)
        return found

    printed = keys(r["brief"], set())
    assert not printed & OUTCOME_KEYS
    assert set(r["brief"]) == {"ok", "kind", "command", "state", "branch", "dev100_route", "prompts",
                               "phtest_max_new_tokens", "files", "complete_sha256", "out"}
    assert r["brief"]["complete_sha256"] == sha256_file(out / "COMPLETE.json")
    result = {k: marker[k] for k in ("prompts", "cap", "unit", "dev100_source", "answer_files", "summary_file")}
    assert not keys(result, set()) & OUTCOME_KEYS


def test_a_failure_after_the_folder_is_kept_and_never_completed(world, tmp_path):
    out = tmp_path / "out"
    code, stdout, stderr = uf.call(world, uf.argv(world, "run", "128", out, untuned=True, checkpoint=None), "128",
                                   fail_guard=True)
    assert code == 1 and stdout == "" and "injected judge failure" in json.loads(stderr)["error"]
    assert (out / "error.txt").is_file() and not (out / "COMPLETE.json").exists()


def test_the_scan_refuses_a_text_outside_the_answer_files(world, tmp_path, monkeypatch):
    real = oe.evaluate_oext

    def leaky(**kw):
        result = real(**kw)
        (Path(kw["run_dir"]) / "note.json").write_text(json.dumps({"p": ofx.PHTEST_ROWS[0][1]}))
        return result

    monkeypatch.setattr(oe, "evaluate_oext", leaky)
    out = tmp_path / "out"
    code, _, stderr = uf.call(world, uf.argv(world, "run", "128", out, run=world.units["evaluated"]), "128")
    assert code == 1 and "note.json holds a prompt" in json.loads(stderr)["error"]
    assert not (out / "COMPLETE.json").exists()


def test_w1_18s_cut_is_the_one_the_settings_bind():
    """The cut applied under Branch 128 is oext_eval's (W1-18's check_one_unit rule); its length is W1-18's
    truncation.cap_tokens in the pinned settings."""
    w_doc, _ = s1.load_settings(oc.SETTINGS_PATH, oc.SETTINGS_SHA256, oc.SETTINGS_NAME)
    assert oe.load_pinned_settings().doc["cap"]["cut_tokens"] == w_doc["truncation"]["cap_tokens"] == 128
    codec = uf.fx.fixture_codec()
    ids = codec.encode("abcdef")
    assert oe.cut_text(codec.decode, ids, CUT) == codec.decode(ids[:CUT]) and oe.cut_text(codec.decode, ids, 99) is None
