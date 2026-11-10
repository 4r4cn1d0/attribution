"""Fix round 3 of track E (verify-E D1, C4, C5; the lead's ruling PP2): the two untuned-answers calls per pod, end to
end through the wrapper's command line on a synthetic family built from the 1B fixtures (the engine's tiny model, the 1B
test's chunk generator, a 40-prompt S4 list, a 10-prompt S3 list). The S4 dose fallback fires in the S4 call, and the S3
call's outputs (s3_orig.pool.json and the record's pool hashes) survive it; the stage-1 kit's J6 completeness check
(runkit/stage1-olmo/stage1_rules.py s3_orig_pin) accepts them. A call with the S4 list beside another list or a loss
refuses before anything runs. Fewer kept than the smallest dose exits 3 and the wrapper record carries that exit code.
A doses refusal after the 1B pass is reported as such (the 1B outputs written, the doses not; exit 2). flag_value takes
the last occurrence of a repeated flag, as argparse does. No text is printed; the records are scanned for the fixtures'
texts. CPU only."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.scale78b import make_scorer_settings_78b as mk  # noqa: E402
from scripts.scale78b import scorers_78b as sw  # noqa: E402
from scripts.stage1 import make_untuned_answers as mua  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

import ss_fixtures as sfx  # noqa: E402
import test_make_untuned_answers as tmua  # noqa: E402
from test_s4_doses_78b import synthetic_pass  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
LOADERS = "experiments.safety_selection.loaders.real_loaders"
FAMILY = "fixture-1b"
recipe_files = tmua.recipe_files          # the 1B untuned-answers fixture recipes (REC = S, batch size 4)
PINS, _ = mk.load_pins()
MAIN_RECIPE_OLMO = REPO / PINS["families"]["olmo2-7b"]["main_recipe"]["path"]
TEXTS = (tmua.REFUSAL, tmua.DIRECT, "Synthetic question", "Synthetic safe answer")


# ----- the synthetic family -------------------------------------------------------------------------------------------


def install_family(root: Path, monkeypatch, rec: dict, keep: int, sizes: list[int]) -> dict:
    """A settings folder holding one family, fixture-1b: make_untuned_answers__fixture-1b.json is the 1B test's settings
    (the fixture recipe as REC and S, chunk 4, keep ``keep`` on a 40-prompt S4 list, an S3 list of 10) plus the committed
    OLMo-2-7B file's doses block with its sizes replaced by ``sizes`` (names s4, s4_96, s4_192 in that order) and a family
    block; the wrapper's SETTINGS_DIR, PINS_FILE, PINS_FILE_SHA256 and FAMILIES point at it for the test."""
    base = json.loads((mk.SETTINGS_DIR / mk.file_name("make_untuned_answers", "olmo2-7b")).read_bytes())
    doc = tmua.settings_for(rec, keep=keep, s3_size=10)
    names = {str(n): name for n, name in zip(sizes, ("s4", "s4_96", "s4_192"))}
    doc["doses"] = {**copy.deepcopy(base["doses"]), "sizes": list(sizes), "names": names,
                    "files": {k: f"dose_{v}.json" for k, v in names.items()}}
    doc["family_78b"] = {"family": FAMILY, "model": "the engine's tiny fixture model", "waits": {},
                         "note": "a synthetic family for the two-calls test (fix round 3, D1); never a run"}
    data = mk.dumps(doc)
    settings_dir = root / "settings"
    settings_dir.mkdir()
    name = mk.file_name("make_untuned_answers", FAMILY)
    (settings_dir / name).write_bytes(data)
    index = mk.index_bytes({name: data}, "0" * 64)
    (settings_dir / mk.INDEX_NAME).write_bytes(index)
    monkeypatch.setattr(sw, "SETTINGS_DIR", settings_dir)
    monkeypatch.setattr(sw, "PINS_FILE", settings_dir / mk.INDEX_NAME)
    monkeypatch.setattr(sw, "PINS_FILE_SHA256", sha256_bytes(index))
    monkeypatch.setattr(sw, "FAMILIES", (FAMILY,))
    return {"settings": doc, "settings_sha256": sha256_bytes(data), "sizes": list(sizes)}


def fake_generation(monkeypatch) -> None:
    """The engine's fixture loaders (the tiny model) and the 1B test's chunk generator (about one refusal in three), so
    the S4 keep path runs through the 1B main()."""
    monkeypatch.setattr(LOADERS, lambda: sfx.fixture_loaders())
    original = mua.run
    monkeypatch.setattr(mua, "run", lambda **kw: original(**{**kw, "generate": tmua.FakeGenerator(sfx.fixture_codec())}))


def prompt_list(root: Path, name: str, n: int, with_response: bool = False) -> tuple[Path, str]:
    items = [{"id": f"c-{name}-{i:03d}", "prompt": f"Synthetic question {i}: how are tides measured in harbour {i % 7}?",
              **({"response": f"Synthetic safe answer {i} about tide tables."} if with_response else {})} for i in range(n)]
    data = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": name, "items": items})
    path = root / f"{name}.json"
    path.write_bytes(data)
    return path, sha256_bytes(data)


def stage1_rules():
    """runkit/stage1-olmo/stage1_rules.py (standard library only), read-only, by path."""
    spec = importlib.util.spec_from_file_location("stage1_rules_read_by_track_e", REPO / "runkit" / "stage1-olmo" / "stage1_rules.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_text_free(*paths: Path) -> None:
    for path in paths:
        data = path.read_bytes()
        for text in TEXTS:
            assert text.encode() not in data, path.name


def common_argv(rec_path: Path, s_path: Path) -> list[str]:
    return ["untuned_answers", "--family", FAMILY, "--recipe", str(rec_path), "--recipe-s", str(s_path)]


# ----- D1: the two calls, the fallback in the second, the S3 outputs survive -------------------------------------------


def test_two_calls_the_s4_fallback_fires_and_the_s3_outputs_survive(recipe_files, tmp_path, monkeypatch, capsys):
    rec_path, s_path, rec = recipe_files
    install_family(tmp_path, monkeypatch, rec, keep=30, sizes=[2, 4, 30])      # 30 keeps are out of reach on 40 prompts
    fake_generation(monkeypatch)
    s3 = prompt_list(tmp_path, "s3", 10, with_response=True)
    s1_list = prompt_list(tmp_path, "s1", 5, with_response=True)
    s4 = prompt_list(tmp_path, "s4", 40)
    job = tmp_path / "job-0"
    # call 1: the S3 list with the losses (PP2)
    out1 = job / "untuned"
    code1 = sw.main(common_argv(rec_path, s_path) + ["--list", f"s3={s3[0]}:{s3[1]}", "--loss", f"s1={s1_list[0]}:{s1_list[1]}",
                                                     "--loss", f"s3_safe={s3[0]}:{s3[1]}", "--out", str(out1)])
    printed1 = capsys.readouterr()
    assert code1 == 0, printed1.err
    files1 = sorted(p.name for p in out1.iterdir())
    assert files1 == ["answers_s3.json", "s3_orig.pool.json", "untuned_answers_record.json", "wrapper_78b_record.json"]
    record1 = json.loads((out1 / mua.RECORD).read_bytes())
    pool_sha = sha256_file(out1 / "s3_orig.pool.json")
    assert record1["complete"] is True and record1["lists"]["s3"]["answered"] == 10
    assert record1["lists"]["s3"]["s3_orig_pool_sha256"] == pool_sha == record1["full_files"]["s3_orig.pool.json"]
    assert set(record1["loss"]) == {"s1", "s3_safe"} and len(record1["loss"]["s1"]["rows"]) == 5
    wrapper1 = json.loads((out1 / sw.WRAPPER_RECORD).read_bytes())
    assert wrapper1["exit_code"] == code1 == 0 and wrapper1["doses"] is None
    assert wrapper1["checked"]["lists"] == ["s3"] and wrapper1["checked"]["losses"] == ["s1", "s3_safe"]
    # call 2: the S4 list alone; fewer than the top dose are kept, so the 1B code exits 3 and the fallback fires
    out2 = job / "untuned-s4"
    code2 = sw.main(common_argv(rec_path, s_path) + ["--list", f"s4={s4[0]}:{s4[1]}", "--out", str(out2)])
    printed2 = capsys.readouterr()
    assert code2 == 0, printed2.err
    record2 = json.loads((out2 / mua.RECORD).read_bytes())
    kept = record2["lists"]["s4"]["kept"]
    assert record2["complete"] is False and record2["lists"]["s4"]["answered"] == 40 and 4 <= kept < 30
    assert sorted(p.name for p in out2.iterdir()) == ["answers_s4.json", "doses", "untuned_answers_record.json", "wrapper_78b_record.json"]
    assert sorted(p.name for p in (out2 / "doses").iterdir()) == ["dose_s4.json", "dose_s4_96.json", "dose_s4_top.json", "s4_doses_record.json"]
    dose_record = json.loads((out2 / "doses" / "s4_doses_record.json").read_bytes())
    assert dose_record["fallback_fired"] is True and dose_record["kept"] == kept and dose_record["top_dose"] == "s4_top"
    top = json.loads((out2 / "doses" / "dose_s4_top.json").read_bytes())
    assert [i["id"] for i in top["items"]] == [r["id"] for r in record2["lists"]["s4"]["rows"] if r["kept"]]
    assert [i["id"] for i in json.loads((out2 / "doses" / "dose_s4.json").read_bytes())["items"]] == [i["id"] for i in top["items"]][:2]
    wrapper2 = json.loads((out2 / sw.WRAPPER_RECORD).read_bytes())
    assert wrapper2["exit_code"] == code2 == 0 and wrapper2["checked"]["lists"] == ["s4"] and wrapper2["checked"]["losses"] == []
    assert wrapper2["doses"] == {"kept": kept, "fallback_fired": True, "top_dose": "s4_top"}
    # the S3 call's outputs are untouched by the S4 call and its fallback
    assert sorted(p.name for p in out1.iterdir()) == files1
    assert sha256_file(out1 / "s3_orig.pool.json") == pool_sha == record1["lists"]["s3"]["s3_orig_pool_sha256"]
    # the stage-1 kit's J6 completeness check accepts the S3 call's record and pool (names and hashes only)
    kit = tmp_path / "kit"
    tree = kit / "retrieved" / "host-a" / "tree" / "job-0" / "untuned"
    tree.mkdir(parents=True)
    outputs = {}
    for name in ("untuned_answers_record.json", "s3_orig.pool.json"):
        (tree / name).write_bytes((out1 / name).read_bytes())
        outputs[f"job-0/untuned/{name}"] = sha256_file(out1 / name)
    plan = {"hosts": {"host-a": {"jobs": [{"kind": "untuned_answers", "status": "complete", "outputs": outputs}]}}}
    pin = stage1_rules().s3_orig_pin(plan, kit)
    assert pin["sha256"] == pool_sha and pin["record"]["sha256"] == outputs["job-0/untuned/untuned_answers_record.json"]
    # nothing printed or recorded holds text
    for printed in (printed1, printed2):
        for text in TEXTS:
            assert text not in printed.out + printed.err
    assert_text_free(out1 / mua.RECORD, out1 / sw.WRAPPER_RECORD, out2 / mua.RECORD, out2 / sw.WRAPPER_RECORD,
                     out2 / "doses" / "s4_doses_record.json")


def test_fewer_kept_than_the_smallest_dose_exits_3_and_the_wrapper_record_says_so(recipe_files, tmp_path, monkeypatch, capsys):
    rec_path, s_path, rec = recipe_files
    install_family(tmp_path, monkeypatch, rec, keep=30, sizes=[20, 25, 30])
    fake_generation(monkeypatch)
    s4 = prompt_list(tmp_path, "s4", 40)
    out = tmp_path / "untuned-s4"
    code = sw.main(common_argv(rec_path, s_path) + ["--list", f"s4={s4[0]}:{s4[1]}", "--out", str(out)])
    printed = capsys.readouterr()
    assert code == mua.EXIT_FEW == 3, printed.err
    record = json.loads((out / mua.RECORD).read_bytes())
    assert record["complete"] is False and record["lists"]["s4"]["kept"] < 20
    assert sorted(p.name for p in out.iterdir()) == ["answers_s4.json", "untuned_answers_record.json", "wrapper_78b_record.json"]
    wrapper = json.loads((out / sw.WRAPPER_RECORD).read_bytes())
    assert wrapper["exit_code"] == 3 and wrapper["doses"] == {"kept": record["lists"]["s4"]["kept"], "fallback_fired": True}
    assert "top_dose" not in wrapper["doses"]                                # no dose was written
    assert_text_free(out / mua.RECORD, out / sw.WRAPPER_RECORD)


# ----- PP2: the S4 list runs alone ------------------------------------------------------------------------------------


def test_the_s4_list_beside_another_list_or_a_loss_refuses_before_anything_runs(tmp_path, capsys):
    assert sw.check_untuned_calls(["--list", "s3=a:x", "--loss", "s1=b:y", "--loss", "s3_safe=a:x"]) == {"lists": ["s3"], "losses": ["s1", "s3_safe"]}
    assert sw.check_untuned_calls(["--list", "s4=a:x", "--out", "o"]) == {"lists": ["s4"], "losses": []}
    assert sw.check_untuned_calls(["--list=s4=a:x"]) == {"lists": ["s4"], "losses": []}
    assert sw.check_untuned_calls(["--list", "s3=a:x", "--list", "sd600=c:z"]) == {"lists": ["s3", "sd600"], "losses": []}
    for argv in (["--list", "s4=a:x", "--list", "s3=b:y"], ["--list", "s3=b:y", "--list=s4=a:x"],
                 ["--list", "s4=a:x", "--loss", "s1=b:y"], ["--list", "s4=a:x", "--list", "sd600=c:z"]):
        with pytest.raises(s1.Refusal, match="runs alone in its own call"):
            sw.check_untuned_calls(argv)
    # the preflight refuses it before any recipe is read (a bogus recipe path never gets as far as a load)
    doc = json.loads((mk.SETTINGS_DIR / mk.file_name("make_untuned_answers", "olmo2-7b")).read_bytes())
    with pytest.raises(s1.Refusal, match="PP2"):
        sw.preflight("untuned_answers", doc, ["--recipe", "none", "--recipe-s", "none", "--list", "s4=a:" + "0" * 64,
                                              "--list", "s3=b:" + "0" * 64, "--out", "o"])
    # the whole command line: exit 2, nothing written
    out = tmp_path / "out"
    code = sw.main(["untuned_answers", "--family", "olmo2-7b", "--recipe", str(MAIN_RECIPE_OLMO), "--recipe-s", str(MAIN_RECIPE_OLMO),
                    "--list", "s4=a:" + "0" * 64, "--list", "s3=b:" + "0" * 64, "--loss", "s1=c:" + "0" * 64, "--out", str(out)])
    err = capsys.readouterr().err
    assert code == 2 and "runs alone in its own call" in err and "(nothing written)" in err and not out.exists()


# ----- C4: a doses refusal after the 1B pass has written ---------------------------------------------------------------


def test_a_doses_refusal_after_the_pass_names_the_written_1b_outputs_and_exits_2(tmp_path, monkeypatch, capsys):
    out = tmp_path / "untuned-s4"

    def stub_run_main(module, argv, settings_path, settings_sha256, pool_pins=None):
        synthetic_pass(out, n_kept=192)                                   # the 1B main() has written its outputs ...
        (out / "answers_s4.json").write_bytes(b'{"kind": "stage1 untuned answers", "version": 1, "list": "s4", "items": []}')
        return 0                                                          # ... but the answers are not the record's file
    monkeypatch.setattr(sw, "run_main", stub_run_main)
    code = sw.main(["untuned_answers", "--family", "olmo2-7b", "--recipe", str(MAIN_RECIPE_OLMO), "--recipe-s", str(MAIN_RECIPE_OLMO),
                    "--list", "s4=a:" + "0" * 64, "--out", str(out)])
    err = capsys.readouterr().err
    assert code == 2
    assert err.startswith("REFUSED after the 1B pass: the 1B outputs are written in ") and str(out) in err
    assert "the doses were not written" in err and "not the file the record names" in err and "(nothing written)" not in err
    assert sorted(p.name for p in out.iterdir()) == ["answers_s4.json", "s4.json", "untuned_answers_record.json"]   # no doses, no wrapper record
    assert issubclass(sw.DosesRefusal, s1.Refusal)


# ----- C5: flag_value on a repeated flag -----------------------------------------------------------------------------


def test_flag_value_takes_the_last_occurrence_as_argparse_does():
    assert sw.flag_value(["--prepared", "a", "--prepared", "b"], "--prepared") == "b"
    assert sw.flag_value(["--prepared", "a", "--prepared=c"], "--prepared") == "c"
    assert sw.flag_value(["--prepared=c", "--prepared", "a"], "--prepared") == "a"
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared")
    assert parser.parse_args(["--prepared", "a", "--prepared", "b"]).prepared == "b"      # the 1B scripts' parsing
    assert sw.named_values(["--list", "s4=a:x", "--list=s3=b:y", "--loss", "s1=c:z"], "--list") == ["s4", "s3"]
    assert sw.named_values(["--out", "o"], "--list") == []


# ----- RV-E-1 (reverify-E, round 4 track M): an abbreviated flag cannot bypass PP2 -------------------------------------


H = "0" * 64


@pytest.mark.parametrize("argv", [
    ["--li", "s4=a:" + H, "--list", "s3=b:" + H, "--out", "o"],             # the re-verifier's bypass: both lists, one call
    ["--list", "s4=a:" + H, "--lo", "s1=c:" + H, "--out", "o"],             # a loss beside S4 under an abbreviation
    ["--list", "s4=a:" + H, "--ou", "o"],                                   # --out unseen: no doses step, no wrapper record
    ["--li=s4=a:" + H, "--list=s3=b:" + H, "--out", "o"],                   # the '=' forms
    ["--list", "s3=b:" + H, "--loss=s1=c:" + H, "--lo=s3_safe=d:" + H, "--out", "o"],
    ["--list", "s4=a:" + H, "--out", "o", "--set", "x.json"],               # a prefix of the wrapper's own --settings
    ["--list", "s4=a:" + H, "--out", "o", "--", "--list", "s3=b:" + H],     # a bare '--' later in the line
])
def test_rv_e_1_an_abbreviated_or_unknown_flag_refuses_in_the_preflight_before_any_check(argv):
    doc = json.loads((mk.SETTINGS_DIR / mk.file_name("make_untuned_answers", "olmo2-7b")).read_bytes())
    with pytest.raises(s1.Refusal, match="RV-E-1"):
        sw.preflight("untuned_answers", doc, ["--recipe", "none", "--recipe-s", "none"] + argv)


def test_rv_e_1_the_whole_command_line_with_li_lo_ou_exits_2_and_writes_nothing(tmp_path, capsys):
    for k, abbreviated in enumerate((["--li", "s4=a:" + H, "--list", "s3=b:" + H, "--out"],
                                     ["--list", "s4=a:" + H, "--lo", "s1=c:" + H, "--out"],
                                     ["--list", "s4=a:" + H, "--ou"])):
        out = tmp_path / f"out{k}"
        code = sw.main(["untuned_answers", "--family", "olmo2-7b", "--recipe", str(MAIN_RECIPE_OLMO),
                        "--recipe-s", str(MAIN_RECIPE_OLMO)] + abbreviated + [str(out)])
        err = capsys.readouterr().err
        assert code == 2 and "RV-E-1" in err and "(nothing written)" in err and not out.exists(), abbreviated
    # the full names still pass the flag check (and reach PP2's own refusal or pass it)
    sw.check_flag_names("untuned_answers", "untuned_answers",
                        ["--recipe", "r", "--recipe-s=r", "--list", "s3=b:" + H, "--loss", "s1=c:" + H, "--out", "o"])
    assert sw.check_untuned_calls(["--list", "s4=a:" + H, "--out", "o"]) == {"lists": ["s4"], "losses": []}


def test_rv_e_1_every_kinds_other_flags_and_the_wrappers_own_refuse():
    for kind, argv, bad in (("rep_pass", ["--prepared", "p", "--pool-pins", "x"], "--pool-pins"),
                            ("rep_pass", ["--prepared", "p", "--rec", "r"], "--rec"),
                            ("l1_scan", ["scan", "--prepared", "p", "--anch", "a"], "--anch"),
                            ("l1_score", ["score", "--prepared", "p", "--recipe", "r"], "--recipe"),
                            ("classifier", ["--prepared", "p", "--reci=r"], "--reci"),
                            ("s3_score", ["--rows", "a", "--settings", "s"], "--settings"),
                            ("score_edit", ["a1", "--unit", "u", "--name", "n"], "--name"),
                            ("score_edit", ["scorer", "--scores-sha", "x"], "--scores-sha"),
                            ("add_edit", ["--prepared", "p", "--full", "t"], "--full"),
                            ("s_pool", ["--prepared", "p", "--re", "r"], "--re")):
        command = sw.command_of(kind, sw.with_subcommand(kind, argv))
        with pytest.raises(s1.Refusal, match=f"'{bad}' is not one of the 1B script's full flag names"):
            sw.check_flag_names(kind, command, argv)


def test_rv_e_1_the_allowed_names_are_the_1b_parsers_long_flags_less_the_wrappers_own(monkeypatch):
    """ALLOWED_FLAGS against the 1B scripts' own parsers (captured at parse_args, so nothing runs): every long flag of
    each command, without --help and the wrapper's --settings and --pool-pins. A 1B parser change shows here."""
    class Captured(Exception):
        pass

    def capture(self, args=None, namespace=None):
        raise Captured(self)
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", capture)

    def long_flags(parser) -> set:
        return {o for a in parser._actions for o in a.option_strings if o.startswith("--")} - {"--help", "--settings", "--pool-pins"}
    found = {}
    for kind, (module_name, *_rest) in sw.KINDS.items():
        module = __import__(module_name, fromlist=["main"])
        with pytest.raises(Captured) as info:
            module.main([])
        parser = info.value.args[0]
        subs = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
        if subs:
            for name, sub in subs[0].choices.items():
                found[name] = long_flags(sub)
        else:
            found[kind] = long_flags(parser)
    commands = {c for kind, entry in sw.KINDS.items() for c in ((entry[4] or kind).split("|"))}
    assert set(sw.ALLOWED_FLAGS) == commands
    assert {c: set(found[c]) for c in commands} == {c: set(v) for c, v in sw.ALLOWED_FLAGS.items()}
