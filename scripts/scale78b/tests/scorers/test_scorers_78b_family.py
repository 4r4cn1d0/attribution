"""The family refusals (the brief's item 4): with each family's committed settings, the wrapper accepts the family's own
prepared manifest and main recipe and refuses the other family's; a command whose pin is still null refuses by naming
the event that fills it; a changed 1B script refuses; the whole command line runs for a Mac kind on the real prepared
set (ids, counts and hashes only; no text is read into any message). The prepared sets are the git-ignored copies under
tmp/kt-prepared/ (manifest and engine files); the tests skip when they are absent."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.scale78b import make_scorer_settings_78b as mk
from scripts.scale78b import scorers_78b as sw
from scripts.stage1 import s1common as s1

REPO = Path(__file__).resolve().parents[4]
PINS, _ = mk.load_pins()
PREPARED = {f: REPO / PINS["families"][f]["prepared_path_on_the_mac"] for f in mk.FAMILIES}
MAIN_RECIPE = {f: REPO / PINS["families"][f]["main_recipe"]["path"] for f in mk.FAMILIES}
OTHER = {"olmo2-7b": "llama31-8b", "llama31-8b": "olmo2-7b"}
needs_prepared = pytest.mark.skipif(not all((p / "manifest.json").is_file() for p in PREPARED.values()),
                                    reason="the prepared sets are not under tmp/kt-prepared/")


def settings(script: str, family: str) -> dict:
    return json.loads((mk.SETTINGS_DIR / mk.file_name(script, family)).read_bytes())


@needs_prepared
@pytest.mark.parametrize("family", mk.FAMILIES)
def test_the_prepared_copies_are_the_pinned_manifests(family):
    assert sha256_file(PREPARED[family] / "manifest.json") == PINS["families"][family]["manifest_sha256"]
    assert sha256_file(PREPARED[family] / "manifest.json") != PINS["families"][OTHER[family]]["manifest_sha256"]


@needs_prepared
@pytest.mark.parametrize("family", mk.FAMILIES)
@pytest.mark.parametrize("kind", ["l1_score", "add_edit", "s_pool"])
def test_the_preflight_accepts_the_familys_manifest_and_refuses_the_others(kind, family):
    doc = settings(sw.KINDS[kind][1], family)
    argv = (["score"] if kind == "l1_score" else []) + ["--prepared", str(PREPARED[family])]
    checked = sw.preflight(kind, doc, argv)
    assert checked["prepared_manifest"] == PINS["families"][family]["manifest_sha256"] and checked["family"] == family
    with pytest.raises(s1.Refusal, match="not this family's prepared set") as exc:
        sw.preflight(kind, doc, (["score"] if kind == "l1_score" else []) + ["--prepared", str(PREPARED[OTHER[family]])])
    assert PINS["families"][family]["manifest_sha256"] in str(exc.value) and PINS["families"][OTHER[family]]["manifest_sha256"] in str(exc.value)


@needs_prepared
@pytest.mark.parametrize("family", mk.FAMILIES)
def test_score_edit_scorer_accepts_the_familys_manifest_and_refuses_the_others(family):
    doc = settings("write_score_edit", family)
    assert sw.preflight("score_edit", doc, ["scorer", "--prepared", str(PREPARED[family])])["command"] == "scorer"
    with pytest.raises(s1.Refusal, match="not this family's prepared set"):
        sw.preflight("score_edit", doc, ["scorer", "--prepared", str(PREPARED[OTHER[family]])])


@pytest.mark.parametrize("family", mk.FAMILIES)
def test_untuned_answers_accepts_the_familys_main_recipe_and_refuses_the_others(family):
    doc = settings("make_untuned_answers", family)
    rec = str(MAIN_RECIPE[family])
    checked = sw.preflight("untuned_answers", doc, ["--recipe", rec, "--recipe-s", rec, "--list", "s4=x:" + "0" * 64, "--out", "o"])
    assert checked["--recipe"] == checked["--recipe-s"] == PINS["families"][family]["main_recipe"]["config_sha256"]
    with pytest.raises(s1.Refusal, match="--recipe hashes to"):
        sw.preflight("untuned_answers", doc, ["--recipe", str(MAIN_RECIPE[OTHER[family]]), "--recipe-s", rec, "--out", "o"])
    with pytest.raises(s1.Refusal, match="--recipe-s hashes to"):
        sw.preflight("untuned_answers", doc, ["--recipe", rec, "--recipe-s", str(MAIN_RECIPE[OTHER[family]]), "--out", "o"])


@needs_prepared
@pytest.mark.parametrize("family", mk.FAMILIES)
def test_the_null_pins_refuse_by_naming_their_event(family):
    p = str(PREPARED[family])
    rec = str(MAIN_RECIPE[family])
    with pytest.raises(s1.Refusal, match="anchor job"):
        sw.preflight("rep_pass", settings("representation_pass", family), ["--prepared", p, "--recipe", rec, "--anchors", "a", "--out", "o"])
    with pytest.raises(s1.Refusal, match="anchor job"):
        sw.preflight("classifier", settings("score_classifier", family), ["--prepared", p, "--recipe", rec, "--anchors", "a", "--out", "o"])
    with pytest.raises(s1.Refusal, match="anchor job"):
        sw.preflight("l1_scan", settings("score_l1_larf", family), ["scan", "--prepared", p, "--recipe", rec, "--anchors", "a", "--out", "o"])
    with pytest.raises(s1.Refusal, match="a0-1101") as exc:
        sw.preflight("score_edit", settings("write_score_edit", family), ["a1", "--unit", "u", "--prepared", p, "--out", "o"])
    assert "6 pin(s)" in str(exc.value)                                   # complete, retrain complete, recipe, bank, bank sha, code
    nulls = dict(sw.null_pins(settings("score_l1_larf", family), "scan"))
    assert set(nulls) == {"pins.anchor_bank_sha256", "scan.first_block"} and "layer rule" in nulls["scan.first_block"]
    assert sw.null_pins(settings("score_l1_larf", family), "score") == []            # the Mac score needs neither
    assert set(dict(sw.null_pins(settings("representation_pass", family), "rep_pass"))) == {"pins.anchor_bank_sha256", "pins.recipe_sha256"}
    assert sw.null_pins(settings("write_score_edit", family), "scorer") == []
    assert sw.null_pins(settings("make_untuned_answers", family), "untuned_answers") == []     # runs before the anchor job


def synthetic_scores(prepared: Path, manifest_sha256: str, out: Path) -> tuple[Path, str]:
    """A scorer output over the real training row ids (ids only; no text is read)."""
    view = s1.PreparedView(prepared, manifest_sha256)
    rng = random.Random(11)
    doc = {"kind": "stage1 scorer output", "version": 1, "scorer": "l1", "manifest_sha256": view.manifest_sha256,
           "orientation": "descending: high = remove", "scores": {r: rng.uniform(-1, 1) for r in view.tokens},
           "costs": {"scan": {"scan_seconds": 0.0}}, "provenance": {"script_sha256": "1" * 64, "settings_sha256": "2" * 64}}
    data = canonical_json(doc)
    path = out / "l1_scores.json"
    path.write_bytes(data)
    return path, sha256_bytes(data)


@needs_prepared
@pytest.mark.parametrize("family", mk.FAMILIES)
def test_the_command_line_runs_a_mac_kind_on_the_familys_set_and_refuses_the_others(family, tmp_path, capsys):
    scores, sha = synthetic_scores(PREPARED[family], PINS["families"][family]["manifest_sha256"], tmp_path)
    out = tmp_path / "out"
    code = sw.main(["score_edit", "--family", family, "scorer", "--name", "l1", "--scores", str(scores), "--scores-sha256", sha,
                    "--prepared", str(PREPARED[family]), "--out", str(out)])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    names = sorted(p.name for p in out.iterdir())
    assert names == ["l1_remove600.edit.json", "l1_selection.json", sw.WRAPPER_RECORD]
    edit = json.loads((out / "l1_remove600.edit.json").read_bytes())
    assert edit["counts"] == {"remove": 600, "rewrite": 0, "add": 0} and edit["manifest_sha256"] == PINS["families"][family]["manifest_sha256"]
    record = json.loads((out / sw.WRAPPER_RECORD).read_bytes())
    assert record["scorer_kind"] == "score_edit" and record["family"] == family and record["command"] == "scorer"
    assert record["exit_code"] == code == 0                                # the record carries the process exit code (C5)
    assert record["settings"]["file"] == f"scripts/scale78b/settings/write_score_edit__{family}.json"
    assert record["stage1_script"]["sha256"] == sw.STAGE1_CODE["scripts/stage1/write_score_edit.py"]
    assert record["checked"]["prepared_manifest"] == PINS["families"][family]["manifest_sha256"]
    selection = json.loads((out / "l1_selection.json").read_bytes())
    assert selection["provenance"]["settings_sha256"] == record["settings"]["sha256"]
    # the other family's command line on this set refuses before anything is written
    out2 = tmp_path / "out2"
    code2 = sw.main(["score_edit", "--family", OTHER[family], "scorer", "--name", "l1", "--scores", str(scores), "--scores-sha256", sha,
                     "--prepared", str(PREPARED[family]), "--out", str(out2)])
    err = capsys.readouterr().err
    assert code2 == 2 and "not this family's prepared set" in err and not out2.exists()


@needs_prepared
def test_the_command_line_refuses_a_pod_kind_whose_pin_is_null(tmp_path, capsys):
    out = tmp_path / "out"
    code = sw.main(["rep_pass", "--family", "olmo2-7b", "--prepared", str(PREPARED["olmo2-7b"]), "--recipe", str(MAIN_RECIPE["olmo2-7b"]),
                    "--anchors", str(tmp_path / "none.json"), "--out", str(out)])
    err = capsys.readouterr().err
    assert code == 2 and "anchor job" in err and "pins.anchor_bank_sha256" in err and not out.exists()
    for lead in ([], ["scan"]):                                           # the subcommand may be left out or given
        code = sw.main(["l1_scan", "--family", "llama31-8b", *lead, "--prepared", str(PREPARED["llama31-8b"]), "--recipe",
                        str(MAIN_RECIPE["llama31-8b"]), "--anchors", str(tmp_path / "none.json"), "--out", str(out)])
        assert code == 2 and "anchor job" in capsys.readouterr().err
    code = sw.main(["l1_scan", "--family", "llama31-8b", "score", "--prepared", str(PREPARED["llama31-8b"]), "--out", str(out)])
    assert code == 2 and "runs the subcommand scan" in capsys.readouterr().err
    assert sw.with_subcommand("score_edit", ["a1", "--unit", "u"]) == ["a1", "--unit", "u"]
    assert sw.with_subcommand("l1_score", ["--prepared", "p"]) == ["score", "--prepared", "p"]
    assert sw.with_subcommand("rep_pass", ["--prepared", "p"]) == ["--prepared", "p"]


def test_the_command_line_refuses_its_own_settings_flag_and_an_unknown_family(capsys):
    assert sw.main(["s3_score", "--family", "olmo2-7b", "--rows", "r:" + "0" * 64, "--settings", "x.json"]) == 2
    assert "--settings is the wrapper's" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        sw.main(["s3_score", "--family", "olmo3-7b", "--rows", "r:" + "0" * 64])
    with pytest.raises(s1.Refusal, match="unknown kind"):
        sw.run_kind("rep_pas", "olmo2-7b", [])


def test_a_changed_1b_script_or_index_refuses(monkeypatch, tmp_path):
    from scripts.stage1 import score_s3_datarx as s3

    monkeypatch.setitem(sw.STAGE1_CODE, "scripts/stage1/score_s3_datarx.py", "0" * 64)
    with pytest.raises(s1.Refusal, match="byte for byte"):
        sw.check_stage1_code(s3)
    monkeypatch.undo()
    assert sw.check_stage1_code(s3) == sw.STAGE1_CODE["scripts/stage1/score_s3_datarx.py"]
    with pytest.raises(s1.Refusal, match="scorers_78b.py pins"):
        sw.load_pins_index(sw.PINS_FILE, "0" * 64)
    bad = tmp_path / "PINS-78B.json"
    bad.write_bytes(b'{"kind": "x"}')
    with pytest.raises(s1.Refusal, match="not a scale78b scorer settings index"):
        sw.load_pins_index(bad, sha256_file(bad))


def test_flag_value_and_command_of():
    assert sw.flag_value(["--prepared", "p", "--out", "o"], "--prepared") == "p"
    assert sw.flag_value(["--prepared=p2"], "--prepared") == "p2" and sw.flag_value(["--out", "o"], "--prepared") is None
    assert sw.command_of("score_edit", ["a1", "--unit", "u"]) == "a1" and sw.command_of("rep_pass", ["--x"]) == "rep_pass"
    with pytest.raises(s1.Refusal, match="leading subcommand"):
        sw.command_of("l1_scan", ["--prepared", "p"])
