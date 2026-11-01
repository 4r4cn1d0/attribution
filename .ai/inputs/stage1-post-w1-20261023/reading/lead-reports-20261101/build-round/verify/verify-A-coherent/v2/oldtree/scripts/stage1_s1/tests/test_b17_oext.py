"""B17 with C-lean's O part on the 500-prompt bank (LN-07; addendum section 11 point 13) on ENGINEERING FIXTURES: the
over-refusal greedy answers and their guard records go through the shared O-ext function under the cap branch; its
files are sealed with the rest and no readable file holds an O-ext text or outcome; the record names the O-ext pins;
every O-ext pin and input, and the pending branch, refuse before any folder; the command line takes the O-ext files;
the settings carry the c0 estimate. None of these numbers is a scientific result."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

import b17_support as bs
import oext_fixtures as ofx

lej, fx, s1, oe = bs.lej, bs.fx, bs.s1, ofx.oe

from experiments.safety_selection.common import read_jsonl, sha256_file  # noqa: E402

CUT = 3                                     # the fixture recipe's cap is 5 new tokens
STAGE_KEYS = {"stage", "status", "start_s", "start_utc", "end_s", "seconds", "end_utc", "memory", "checkpoint",
              "queries", "prompts", "answers", "items", "forward_passes", "input_tokens", "target_tokens",
              "prompt_tokens", "adapter_fingerprint", "parameters", "max_new_tokens"}


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    return bs.prepared_dirs(tmp_path_factory.mktemp("b17-oext-prepared"))


def oext_env(base: Path, prepared, branch: str, **changes):
    """A B17 Env whose settings hold C-lean's O-ext part with the fixture O-ext pins (the running module), and the
    fixture O-ext inputs."""
    inp = ofx.inputs(base / "oext", branch=branch, cut=CUT, dev=bs.EXPECTED["overrefusal"])
    pins = {"lean.overrefusal_bank.status": "oext_pinned", "oext.module_sha256": oe.module_sha256(),
            "oext.settings.sha256": inp.settings.sha256, "oext.branch": branch, **changes}
    return bs.Env(base, prepared, **pins), inp


def plan(env, inp, oext="given", out: Path | None = None):
    return lej.prepare_c0_job(env.job(), prepared_dir=env.prepared_dir, recipe_path=env.recipe_path,
                              out_dir=out or env.base / "out", settings=env.settings,
                              settings_sha256=env.settings_sha256,
                              oext=inp.prepared if oext == "given" else oext)


@pytest.fixture(scope="module", params=["128", "full"])
def done(request, tmp_path_factory, prepared):
    def make():
        env, inp = oext_env(tmp_path_factory.mktemp(f"b17-oext-{request.param}"), prepared, request.param)
        p = plan(env, inp)
        record = lej.execute_c0_job(p, bs.session(env.recipe))
        return env, inp, p, record

    return bs.kept(make)          # a broken shared run fails each test that unpacks it (never a fixture error)


def sealed_dir(env) -> Path:
    return env.base / "out" / "lean" / "sealed"


def test_c_lean_holds_the_500_bank_through_the_shared_function(done):
    env, inp, p, record = done
    branch = inp.settings.doc["cap"]["branch"]
    folder = sealed_dir(env)
    assert sorted(x.name for x in folder.iterdir()) == sorted([*lej.SEALED_FILES, *lej.OEXT_SEALED_FILES])
    summary = json.loads((folder / oe.SUMMARY).read_bytes())
    assert summary["branch"] == branch and summary["bank"]["prompts"] == 2 + len(ofx.PHTEST_ROWS)
    assert summary["cap"]["phtest_max_new_tokens"] == (CUT if branch == "128" else 5)
    gens = {g["prompt_id"]: g for g in read_jsonl(folder / "generations.jsonl")}
    guard = {g["prompt_id"]: g for g in read_jsonl(folder / "guard.jsonl")}
    cuts = {g["prompt_id"]: g for g in read_jsonl(folder / oe.GUARD) if g["source"] == "dev100"}
    longer = {pid for pid, g in gens.items() if g["output_tokens"] > CUT}
    assert longer and set(cuts) == longer                     # the lean answers are the dev part, cut by W1-18's rule
    codec = fx.fixture_codec()
    assert all(cuts[pid]["text"] == codec.decode(gens[pid]["output_ids"][:CUT]) for pid in longer)
    if branch == "full":
        refused = sum(g["valid"] and g["refusal"] == "Yes" for g in guard.values())
        assert summary["o"]["by_source"]["dev100"]["refused"] == refused and summary["sensitivity_cut"]
    assert summary["provenance"]["inputs"]["dev100/generations.jsonl"] == sha256_file(folder / "generations.jsonl")
    listed = record["lean_unit"]["sealed_files"]
    assert {name: listed[name]["sha256"] for name in oe.OUTPUT_FILES} == {
        name: sha256_file(folder / name) for name in oe.OUTPUT_FILES}
    subset = record["subset"]
    assert subset["oext_phtest_answers"] == len(ofx.PHTEST_ROWS)
    assert subset["answers"] == 4 + len(ofx.PHTEST_ROWS) and subset["full_evaluation_answers"] == 15 + len(ofx.PHTEST_ROWS)
    assert record["oext"] == {"branch": branch, "settings_sha256": inp.settings.sha256,
                              "module_sha256": oe.module_sha256(), "record_sha256": inp.prepared.bank.record_sha256,
                              "bank_sha256": inp.prepared.bank.bank_sha256,
                              "w1_18_record_sha256": inp.prepared.w1_18.record_sha256,
                              "phtest_prompts": len(ofx.PHTEST_ROWS)}
    assert record["overrefusal_bank"] == "oext_pinned" and "2,400 s" in record["c0_estimate"]
    assert json.loads((env.base / "out" / "lean" / "lean_job.json").read_bytes())["oext"] == record["oext"]
    assert record["provenance"]["inputs"]["oext_record"] == inp.prepared.bank.record_sha256
    assert lej.verify_c0(env.base / "out") == []


def test_the_oext_stages_are_costed_and_hold_no_outcome(done):
    env, _, _, record = done
    lean = env.base / "out" / "lean"
    rows = [r for r in record["stages"] if r["folder"] == "lean"]
    assert [r["stage"] for r in rows][-3:] == list(oe.STAGES)
    assert {r["stage"]: r["category"] for r in rows if r["stage"] in oe.STAGES} == {
        "oext_generate": "greedy_generation", "oext_guard": "judging", "oext_guard_cut": "judging"}
    assert not record["unmapped_stages"]
    seconds = {r["stage"]: r["seconds"] for r in rows}
    per = record["per_answer_seconds"]
    assert per["greedy_oext_phtest"] == seconds["oext_generate"] / len(ofx.PHTEST_ROWS)
    assert per["guard_oext_phtest"] == seconds["oext_guard"] / len(ofx.PHTEST_ROWS)
    for row in read_jsonl(lean / "ledger.jsonl"):
        assert set(row) <= STAGE_KEYS, row["stage"]
    records = read_jsonl(lean / "records.jsonl")
    assert records[-1]["oext_phtest_answers"] == len(ofx.PHTEST_ROWS) and records[-1]["oext_branch"] in ("128", "full")
    texts = [p for _, p in ofx.PHTEST_ROWS]
    texts += [g["text"] for g in read_jsonl(sealed_dir(env) / oe.GENERATIONS)]
    texts += [g[k] for g in read_jsonl(sealed_dir(env) / oe.GUARD) for k in ("text", "guard_answer") if g.get(k)]
    texts = [t for t in texts if len(t) >= 6]
    readable = [x for x in lean.rglob("*") if x.is_file() and "sealed" not in x.relative_to(lean).parts]
    for path in [*readable, env.base / "out" / "c0_record.json"]:
        data = path.read_bytes()
        assert s1._text_hits(data, texts, 6) == 0, path.name
        assert b'"o":' not in data and b"flag_change" not in data and b"longer_than_cut" not in data, path.name


def test_the_text_scan_covers_the_oext_texts(done):
    env, inp, p, _ = done
    texts = lej._texts(p, sealed_dir(env), 1)
    assert all(prompt in texts for _, prompt in ofx.PHTEST_ROWS)
    assert all(g["text"] in texts for g in read_jsonl(sealed_dir(env) / oe.GENERATIONS) if g["text"])
    assert all(g["text"] in texts for g in read_jsonl(sealed_dir(env) / oe.GUARD) if g["text"])


def test_every_oext_pin_input_and_the_pending_branch_refuse_before_any_folder(tmp_path, prepared):
    env, inp = oext_env(tmp_path / "e", prepared, "128")
    cases = [(env, None, "are needed"),
             (oext_env(tmp_path / "m", prepared, "128", **{"oext.module_sha256": "0" * 64})[0], inp.prepared,
              "module is not the one"),
             (oext_env(tmp_path / "s", prepared, "128", **{"oext.settings.sha256": "0" * 64})[0], inp.prepared,
              "not the ones these settings pin"),
             (oext_env(tmp_path / "b", prepared, "128", **{"oext.branch": "full"})[0], inp.prepared,
              "not the ones these settings pin"),
             (bs.Env(tmp_path / "plain", prepared), inp.prepared, "not O-ext"),
             (oext_env(tmp_path / "cb", prepared, "128", **{"lean.contents": "b"})[0], inp.prepared, "not O-ext")]
    for k, (e, oext, match) in enumerate(cases):
        with pytest.raises(s1.Refusal, match=match):
            plan(e, inp, oext=oext, out=tmp_path / f"out-{k}")
        assert not (tmp_path / f"out-{k}").exists()
    pend, pinp = oext_env(tmp_path / "p", prepared, "pending_w1_18")
    with pytest.raises(s1.Refusal, match="pending W1-18"):
        plan(pend, pinp, oext=oe.prepare(pinp.settings), out=tmp_path / "out-pending")
    assert not (tmp_path / "out-pending").exists()
    three = ofx.inputs(tmp_path / "three", branch="128", cut=CUT, dev=3)
    env3 = bs.Env(tmp_path / "e3", prepared, **{"lean.overrefusal_bank.status": "oext_pinned",
                                               "oext.module_sha256": oe.module_sha256(),
                                               "oext.settings.sha256": three.settings.sha256, "oext.branch": "128"})
    with pytest.raises(s1.Refusal, match="dev part is not"):
        plan(env3, three, out=tmp_path / "out-3")


def test_the_settings_hold_the_oext_part_and_the_c0_estimate():
    settings, _ = lej.load_lean_settings()
    assert settings["lean"]["overrefusal_bank"]["status"] == "oext_pinned"
    assert settings["oext"]["module"] == "scripts/stage1_s1/oext_eval.py"
    assert settings["oext"]["module_sha256"] == oe.module_sha256() == sha256_file(bs.PKG_DIR / "oext_eval.py")
    assert settings["oext"]["settings"]["sha256"] == oe.SETTINGS_SHA256 == sha256_file(oe.SETTINGS_PATH)
    assert settings["oext"]["branch"] == oe.load_pinned_settings().doc["cap"]["branch"] == "128"     # 11.7 re-pin
    assert "2,400 s" in settings["c0_estimate"] and "870 s" in settings["c0_estimate"]
    assert "estimate" in settings["c0_estimate"]
    assert {k: settings["cost_stages"]["map"][k] for k in oe.STAGES} == {
        "oext_generate": "greedy_generation", "oext_guard": "judging", "oext_guard_cut": "judging"}
    assert "1,468" in settings["lean"]["share_note"]
    for dotted, value in (("lean.overrefusal_bank.status", "open"), ("oext.branch", "64"),
                          ("oext.module", "scripts/x.py"), ("lean.order", lej.LEAN_ORDER[:-1]),
                          ("c0_estimate", "")):
        doc = bs.settings_doc(**{dotted: value})
        with pytest.raises(s1.Refusal):
            lej.check_lean_settings(doc)


def _cli(argv, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = lej.main([str(a) for a in argv], **kwargs)
    return code, out.getvalue(), err.getvalue()


def test_the_command_line_takes_the_oext_files(tmp_path, prepared, monkeypatch):
    env, inp = oext_env(tmp_path, prepared, "128")
    monkeypatch.setattr(lej, "SETTINGS_PATH", env.settings_path)
    monkeypatch.setattr(lej, "SETTINGS_SHA256", env.settings_sha256)
    base = ["run", "--job", env.job(), "--prepared", env.prepared_dir, "--recipe", env.recipe_path]
    files = ["--oext-bank", inp.bank, "--oext-record", inp.record, "--w1-18-record", inp.w1_18]
    code, stdout, stderr = _cli([*base, "--out", tmp_path / "a", *files], loaders=fx.fixture_loaders(),
                                oext_settings=inp.settings)
    assert code == 0, stderr
    shown = json.loads(stdout)
    assert shown["answers"] == 4 + len(ofx.PHTEST_ROWS) and shown["sealed_files"] == 9
    assert all(prompt not in stdout + stderr for _, prompt in ofx.PHTEST_ROWS)
    code, _, _ = _cli([*base, "--out", tmp_path / "b"], loaders=fx.fixture_loaders(), oext_settings=inp.settings)
    assert code == 2 and not (tmp_path / "b").exists()
    code, _, _ = _cli([*base, "--out", tmp_path / "c", *files[:4]], loaders=fx.fixture_loaders(),
                      oext_settings=inp.settings)
    assert code == 2 and not (tmp_path / "c").exists()                        # W1-18's record is pinned, not given
    code, _, stderr = _cli([*base, "--out", tmp_path / "d"], loaders=fx.fixture_loaders())   # the pinned settings
    assert code == 2 and not (tmp_path / "d").exists()                       # Branch 128 (11.7): the files are needed
    assert "Branch 128: O-ext needs the bank file and its record" in stderr
    code, _, stderr = _cli([*base, "--out", tmp_path / "e", *files], loaders=fx.fixture_loaders())
    assert code == 2 and not (tmp_path / "e").exists()                       # the fixture's W1-18 record is not W1-18's
    assert "the settings pin 608cbb94c0060012e4cd0544fb2b926c7e86a37c69dd8f2759d944faa971eb21" in stderr
