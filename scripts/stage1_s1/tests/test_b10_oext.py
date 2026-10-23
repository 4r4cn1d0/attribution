"""B10 with O-ext (addendum section 11 point 1; section 13) on ENGINEERING FIXTURES: with the over-refusal bank status
oext_pinned every evaluation, certify included, runs the shared O-ext function after the engine's evaluate_checkpoint;
certify's 8 engine evaluation files stay byte-identical with the Gate-A-like unit's and its comparison still passes
(O-ext is a report, never a gate); the dev-100 part is the engine's own answers and flags; under the pending branch
only certify runs, without O-ext; every O-ext pin and input is checked before any folder; the command line and one
process with several evaluations carry the O-ext files; in the prefix mode the PHTest prompts carry the prefix and the
guard sees the user's own text. None of these numbers is a scientific result."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402
import oext_fixtures as ofx  # noqa: E402

from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import canonical_json, read_json, read_jsonl, sha256_file  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

oe = ofx.oe
CUT = 3                                     # the fixture recipe's cap is 5 new tokens


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return ofx.kept(lambda: _world(tmp_path_factory))      # a broken world fails each test (never a fixture error)


def _world(tmp_path_factory):
    base = tmp_path_factory.mktemp("b10-oext")
    prepared, manifest = fb.prepared(base)
    one = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", 1102)
    resumed, init = fb.gate_a_resumed(prepared, base / "units" / "1101-a0-e1-a1", 1101)
    units = {1101: resumed, 1102: one}
    recipe_file = base / "recipe.json"
    recipe_file.write_bytes(canonical_json(fb.recipe()))
    plain = fb.fixture_settings(manifest, units, untuned=init, recipe__file_sha256=sha256_file(recipe_file))
    regen = {}
    for seed in (1101, 1102):
        ea.regenerate(prepared_dir=prepared, seed=seed, reference_path=units[seed] / "COMPLETE.json",
                      out_root=base / f"regen-{seed}", session=fb.session(), settings=plain)
        regen[seed] = base / f"regen-{seed}" / "run"
    cert = fb.certification(prepared, resumed, plain, base / "certification", source=regen[1101])
    oext = {branch: ofx.inputs(base / f"oext-{branch}", branch=branch, cut=CUT, dev=2)
            for branch in ("128", "full", "pending_w1_18")}
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, units=units, init=init, plain=plain,
                        regen=regen, cert=cert, recipe=recipe_file, oext=oext)


def b10_settings(world, branch: str, **changes) -> ea.Settings:
    """B10's fixture settings with the status oext_pinned and the fixture O-ext pins (the running module)."""
    inp = world.oext[branch]
    pins = {"recipe__file_sha256": world.plain.doc["recipe"]["file_sha256"], "overrefusal_bank__status": "oext_pinned",
            "oext__module_sha256": oe.module_sha256(), "oext__settings__sha256": inp.settings.sha256,
            "oext__branch": branch}
    return fb.fixture_settings(world.manifest, world.units, untuned=world.init, **{**pins, **changes})


def evaluate(world, out: Path, plan, settings, oext, *, seed: int = 1101, session=None) -> dict:
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=world.regen[seed],
                       reference_path=world.units[seed] / "COMPLETE.json", recipe=fb.recipe(), settings=settings,
                       plan=plan, certification=None if plan.mode == "certify" else world.cert, oext=oext)
    return ea.evaluate(ctx, out_dir=out, session=session or fb.session())


def overrefusal(folder: Path, name: str) -> dict:
    return {r["prompt_id"]: r for r in read_jsonl(folder / name) if r.get("kind") == "overrefusal"}


@pytest.mark.parametrize("branch", ["128", "full"])
def test_certify_keeps_the_engine_files_byte_identical_and_adds_the_oext_files(world, tmp_path, branch):
    settings = b10_settings(world, branch)
    result = evaluate(world, tmp_path / "cert", ea.make_plan(settings, "certify"), settings,
                      world.oext[branch].prepared)
    mine, gate_a = fb.eval_dir(tmp_path / "cert"), fb.eval_dir(world.units[1101])
    for name in fb.EVAL_FILES:
        assert (mine / name).read_bytes() == (gate_a / name).read_bytes(), name
    assert fb.summary_without_timing(tmp_path / "cert") == fb.summary_without_timing(world.units[1101])
    assert all((mine / name).is_file() for name in oe.OUTPUT_FILES)
    assert not any((gate_a / name).exists() for name in oe.OUTPUT_FILES)
    report = ea.compare_certification(tmp_path / "cert", world.units[1101] / "COMPLETE.json", gate_a, settings)
    assert report["verdict"] == "pass" and report["gate"]["differing_gate_labels"] == 0
    assert ea.verify_unit(tmp_path / "cert")["complete"]
    marker = read_json(tmp_path / "cert" / "COMPLETE.json")
    assert all(f"eval/e1/{name}" in marker["files"] for name in oe.OUTPUT_FILES)
    summary = result["oext"]
    assert summary == json.loads((mine / oe.SUMMARY).read_bytes()) and summary["branch"] == branch
    assert summary["bank"]["prompts"] == 2 + len(ofx.PHTEST_ROWS)
    assert marker["overrefusal_bank"]["oext"] == {"branch": branch, "runs": True,
                                                  "settings_sha256": world.oext[branch].settings.sha256}
    job = read_json(tmp_path / "cert" / "job.json")
    inp = world.oext[branch].prepared
    assert job["oext"] == {"branch": branch, "settings_sha256": inp.settings.sha256,
                           "module_sha256": oe.module_sha256(), "record_sha256": inp.bank.record_sha256,
                           "bank_sha256": inp.bank.bank_sha256, "w1_18_record_sha256": inp.w1_18.record_sha256}
    stages = [r["stage"] for r in read_jsonl(tmp_path / "cert" / "ledger.jsonl")]
    assert stages.index("oext_generate") > max(i for i, s in enumerate(stages) if s == "guard")
    assert set(oe.STAGES) <= set(result["costs"]["stage_seconds"])


def test_the_dev_part_is_the_engines_own_answers_and_flags(world, tmp_path):
    codec = fb.fx.fixture_codec()
    for branch in ("128", "full"):
        settings = b10_settings(world, branch)
        evaluate(world, tmp_path / branch, ea.make_plan(settings, "scale", adapter_scale=0.5), settings,
                 world.oext[branch].prepared, seed=1102)
        folder = fb.eval_dir(tmp_path / branch)
        gens, guard = overrefusal(folder, "generations.jsonl"), overrefusal(folder, "guard.jsonl")
        summary = json.loads((folder / oe.SUMMARY).read_bytes())
        cuts = {r["prompt_id"]: r for r in read_jsonl(folder / oe.GUARD) if r["source"] == "dev100"}
        longer = {p for p, g in gens.items() if g["output_tokens"] > CUT}
        assert longer and set(cuts) == longer
        for pid in longer:
            assert cuts[pid]["text"] == codec.decode(gens[pid]["output_ids"][:CUT])
            assert cuts[pid]["role"] == ("primary" if branch == "128" else "sensitivity")
        engine_refused = sum(g["valid"] and g["refusal"] == "Yes" for g in guard.values())
        engine_invalid = sum(not g["valid"] for g in guard.values())
        if branch == "full":                                    # the engine's flags, reused
            assert summary["o"]["by_source"]["dev100"]["refused"] == engine_refused
            assert summary["o"]["by_source"]["dev100"]["invalid"] == engine_invalid
            assert summary["sensitivity_cut"] is not None
        else:
            cut_flags = {p: (cuts[p]["valid"] and cuts[p]["refusal"] == "Yes") if p in longer
                         else (guard[p]["valid"] and guard[p]["refusal"] == "Yes") for p in gens}
            assert summary["o"]["by_source"]["dev100"]["refused"] == sum(cut_flags.values())
        assert summary["provenance"]["inputs"]["dev100/generations.jsonl"] == sha256_file(folder / "generations.jsonl")
        assert summary["provenance"]["inputs"]["dev100/guard.jsonl"] == sha256_file(folder / "guard.jsonl")


def test_the_pending_branch_runs_only_certify_and_without_oext(world, tmp_path):
    settings = b10_settings(world, "pending_w1_18")
    pending = world.oext["pending_w1_18"].settings
    for mode, options in (("scale", {"adapter_scale": 0.5}), ("scale", {"adapter_scale": 0.0})):
        with pytest.raises(ea.Refusal, match="pending W1-18"):
            ea.make_plan(settings, mode, **options)
    plan = ea.make_plan(settings, "certify")
    result = evaluate(world, tmp_path / "cert", plan, settings, oe.prepare(pending))
    assert result["oext"] == {"status": "not_run", "branch": "pending_w1_18", "reason": ea.OEXT_PENDING}
    assert not any((fb.eval_dir(tmp_path / "cert") / name).exists() for name in oe.OUTPUT_FILES)
    assert read_json(tmp_path / "cert" / "job.json")["oext"]["record_sha256"] is None
    report = ea.compare_certification(tmp_path / "cert", world.units[1101] / "COMPLETE.json",
                                      fb.eval_dir(world.units[1101]), settings)
    assert report["verdict"] == "pass"
    zero = ea.Plan("scale", 0.0)                       # a plan made by hand still refuses in the preflight
    with pytest.raises(ea.Refusal, match="pending W1-18"):
        evaluate(world, tmp_path / "zero", zero, settings, oe.prepare(pending))
    assert not (tmp_path / "zero").exists()


def test_every_oext_pin_and_input_is_checked_before_any_folder(world, tmp_path):
    good = b10_settings(world, "128")
    inp = world.oext["128"].prepared
    plan = ea.make_plan(good, "certify")
    cases = [
        (good, None, "needs the O-ext settings"),
        (world.plain, inp, "status is 'dev100_recipe_cap'"),
        (b10_settings(world, "128", oext__module_sha256="0" * 64), inp, "module is not the one"),
        (b10_settings(world, "128", oext__settings__sha256="0" * 64), inp, "not the ones these settings pin"),
        (b10_settings(world, "128", oext__branch="full"), inp, "not the ones these settings pin"),
    ]
    for k, (settings, oext, match) in enumerate(cases):
        with pytest.raises(ea.Refusal, match=match):
            evaluate(world, tmp_path / f"out-{k}", plan, settings, oext)
        assert not (tmp_path / f"out-{k}").exists()


def test_the_settings_section_oext_is_validated():
    doc = fb.real_doc()
    for dotted, value, match in (("oext.module", "scripts/other.py", "the module is"),
                                 ("oext.module_sha256", "x", "module_sha256"),
                                 ("oext.settings.path", "scripts/x.json", "the settings file is"),
                                 ("oext.branch", "256", "branch must be"),
                                 ("oext.outputs", ["oext_summary.json"], "three files"),
                                 ("overrefusal_bank.status", "oext", "status must be")):
        bad = json.loads(json.dumps(doc))
        fb.set_dotted(bad, dotted, value)
        with pytest.raises(ea.Refusal, match=match):
            ea.validate_settings(bad)
    bad = json.loads(json.dumps(doc))
    del bad["oext"]["rule"]
    with pytest.raises(ea.Refusal, match="settings oext"):
        ea.validate_settings(bad)


def _cli(world, argv, settings, oext_settings, **loader_options) -> int:
    return ea.main([str(a) for a in argv], _settings=settings, _oext_settings=oext_settings,
                   _loaders=fb.fx.fixture_loaders(**loader_options))


def _common(world, seed: int) -> list:
    return ["--prepared", world.prepared, "--recipe", world.recipe, "--reference", world.units[seed] / "COMPLETE.json"]


def _oext_args(inp) -> list:
    return ["--oext-bank", inp.bank, "--oext-record", inp.record, "--w1-18-record", inp.w1_18]


def test_the_command_line_takes_the_oext_files(world, tmp_path):
    settings, inp = b10_settings(world, "128"), world.oext["128"]
    base = ["evaluate", *_common(world, 1102), "--source-run", world.regen[1102], "--mode", "scale", "--lambda", 0.5,
            *fb.cert_args(world.cert)]
    assert _cli(world, [*base, "--out", tmp_path / "a", *_oext_args(inp)], settings, inp.settings) == 0
    assert (fb.eval_dir(tmp_path / "a") / oe.SUMMARY).is_file()
    assert _cli(world, [*base, "--out", tmp_path / "b"], settings, inp.settings) == 2          # no bank file
    assert not (tmp_path / "b").exists()
    assert _cli(world, [*base, "--out", tmp_path / "c", "--oext-bank", inp.bank, "--oext-record", inp.record],
                settings, inp.settings) == 2                                                      # no W1-18 record
    assert not (tmp_path / "c").exists()
    plain = ["evaluate", *_common(world, 1102), "--source-run", world.regen[1102], "--mode", "certify",
             "--out", tmp_path / "d", *_oext_args(inp)]
    assert _cli(world, plain, world.plain, inp.settings) == 2 and not (tmp_path / "d").exists()
    pending = world.oext["pending_w1_18"].settings
    assert _cli(world, [*base, "--out", tmp_path / "e"], b10_settings(world, "pending_w1_18"), pending) == 2
    assert not (tmp_path / "e").exists()


def test_one_process_with_several_evaluations_runs_oext_in_each(world, tmp_path):
    settings, inp = b10_settings(world, "full"), world.oext["full"]
    argv = ["run", *_common(world, 1101), "--seed", 1101, "--regen-out", tmp_path / "regen", "--eval-root",
            tmp_path / "eval", "--evaluations", "certify,scale:0.5", "--gate-reference-eval",
            fb.eval_dir(world.units[1101]), *_oext_args(inp)]
    assert _cli(world, argv, settings, inp.settings) == 0
    for label in ("certify", "scale-0.5"):
        summary = json.loads((tmp_path / "eval" / f"1101-{label}" / "eval" / "e1" / oe.SUMMARY).read_bytes())
        assert summary["branch"] == "full" and summary["sensitivity_cut"] is not None
    gate_a = fb.eval_dir(world.units[1101])
    for name in fb.EVAL_FILES:
        assert (tmp_path / "eval" / "1101-certify" / "eval" / "e1" / name).read_bytes() == (gate_a / name).read_bytes()
    assert read_json(tmp_path / "eval" / "1101-certify.compare.json")["verdict"] == "pass"
    missing = ["run", *_common(world, 1101), "--seed", 1101, "--regen-out", tmp_path / "regen2", "--eval-root",
               tmp_path / "eval2", "--evaluations", "certify,scale:0.5", "--gate-reference-eval",
               fb.eval_dir(world.units[1101]), "--oext-bank", inp.bank, "--oext-record", inp.record]
    assert _cli(world, missing, settings, inp.settings) == 2                  # W1-18's record is pinned, not given
    assert not (tmp_path / "regen2").exists() and not (tmp_path / "eval2").exists()


def test_the_prefix_mode_prefixes_the_phtest_prompts_and_the_guard_sees_the_users_text(world, tmp_path):
    prefix_file, digest = fb.write_prefix(tmp_path)
    settings = b10_settings(world, "128", prefix__text_sha256=digest, prefix__source="ENGINEERING FIXTURE placeholder")
    loaders, seen = fb.recording_loaders()
    plan = ea.make_plan(settings, "prefix", prefix_file=str(prefix_file))
    evaluate(world, tmp_path / "sp", plan, settings, world.oext["128"].prepared, seed=1102,
             session=runner.Session(fb.recipe(), loaders))
    codec = fb.fx.fixture_codec()
    insert = fb.PREFIX_TEXT + "\n\n"
    gens = read_jsonl(fb.eval_dir(tmp_path / "sp") / oe.GENERATIONS)
    assert [g["prompt_ids"] for g in gens] == [codec.prompt_ids(insert + p) for _, p in ofx.PHTEST_ROWS]
    assert not any(fb.PREFIX_TEXT in text for text in seen)
    prompts = dict(ofx.PHTEST_ROWS)
    scored = [r for r in read_jsonl(fb.eval_dir(tmp_path / "sp") / oe.GUARD)
              if r["source"] == "phtest" and r["guard_input_tokens"] is not None]
    assert scored and all(any(f"USER: {prompts[r['prompt_id']]}\n" in text for text in seen) for r in scored)
    only_some = b10_settings(world, "128", prefix__text_sha256=digest, prefix__source="ENGINEERING FIXTURE placeholder",
                             prefix__apply_to=["harm"])
    evaluate(world, tmp_path / "harm-only", ea.make_plan(only_some, "prefix", prefix_file=str(prefix_file)),
             only_some, world.oext["128"].prepared, seed=1102)
    gens = read_jsonl(fb.eval_dir(tmp_path / "harm-only") / oe.GENERATIONS)
    assert [g["prompt_ids"] for g in gens] == [codec.prompt_ids(p) for _, p in ofx.PHTEST_ROWS]


def test_a_phtest_prompt_that_is_also_a_prefixed_text_of_another_kind_refuses(world):
    """S1 FIX (review finding 5): in the prefix mode without over-refusal in apply_to, a PHTest prompt that the prefix
    codec would prefix (it is also a prefixed harm or task text) refuses, since O-ext's PHTest answers must be made
    without the prefix; with over-refusal in apply_to the codec is extended to every PHTest prompt."""
    from types import SimpleNamespace

    codec = fb.fx.fixture_codec()
    prepared = world.oext["128"].prepared
    phtest = [prompt for _, prompt in prepared.bank.rows]
    other = f"{ofx.FIXTURE} a prefixed harm prompt"
    clash = ea.PrefixCodec(tokenizer=codec.tokenizer, eos_id=codec.eos_id, stop_ids=codec.stop_ids,
                           pad_id=codec.pad_id, special_ids=codec.special_ids, insert="P\n\n",
                           only=frozenset({other, phtest[1]}))
    harm_only = SimpleNamespace(doc={"prefix": {"apply_to": ["harm"]}})
    with pytest.raises(ea.Refusal, match="also a prefixed text of another kind"):
        ea.oext_codec(clash, prepared, harm_only)
    apart = dataclasses_replace(clash, only=frozenset({other}))
    assert ea.oext_codec(apart, prepared, harm_only) is apart                 # no clash: the codec as it is
    with_or = SimpleNamespace(doc={"prefix": {"apply_to": ["harm", "overrefusal"]}})
    extended = ea.oext_codec(clash, prepared, with_or)
    assert extended.only == frozenset({other, *phtest})
    assert ea.oext_codec(codec, prepared, harm_only) is codec                 # not the prefix mode


def dataclasses_replace(obj, **changes):
    import dataclasses

    return dataclasses.replace(obj, **changes)
