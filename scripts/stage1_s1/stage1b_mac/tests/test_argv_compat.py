"""The runner's command lines against the W1 scripts' own parsers (report_plant_ranks.main, score_datashield.main,
score_l1_larf.main: their argparse runs before their settings load, which is patched here to stop with a refusal), the
file-name constants against the W1 modules' constants, and the three scripts' W1 manifest entries (by key)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import synth_world as sw

from scripts.stage1 import report_plant_ranks as rpr
from scripts.stage1 import representation_pass as rp
from scripts.stage1 import s1common as s1
from scripts.stage1 import score_classifier as scl
from scripts.stage1 import score_datashield as sds
from scripts.stage1 import score_l1_larf as sl1
from scripts.stage1_s1.stage1b_mac import construction_checks as cc

REPO = sw.repo_root()                      # the workspace (a mutation copy holds scripts/stage1_s1 only)

H = {name: name[0] * 64 for name in ("rows", "summary", "l1_scan", "classifier", "record", "plant", "decoy", "l1", "datashield")}
POD = {"rows": (Path("/k/job-0/representation/representation_rows.jsonl"), H["rows"]),
       "summary": (Path("/k/job-0/representation/representation_pass.json"), H["summary"]),
       "l1_scan": (Path("/k/job-1/l1-scan/l1_scan.json"), H["l1_scan"]),
       "classifier": (Path("/k/job-2/classifier/classifier_scores.json"), H["classifier"])}
PINNED = {"plant_record": (Path("/r/record.json"), H["record"]), "plant_pool": (Path("/p/a.json"), H["plant"]),
          "decoy_pool": (Path("/p/b.json"), H["decoy"])}


@pytest.fixture
def parsed(monkeypatch):
    """Patches s1common.load_settings (the first call after each W1 parser) to record the call and stop."""
    calls = []

    def stop(path, expected, name):
        calls.append((Path(path).name, expected, name))
        raise s1.Refusal("stop here: the argv parsed")
    monkeypatch.setattr(s1, "load_settings", stop)
    return calls


def test_the_scorer_commands_parse_with_the_w1_parsers(parsed, capsys):
    cmds = cc.scorer_commands(REPO, Path("/prep"), POD, Path("/o/plant-x"), l1_given=False, datashield_given=False)
    assert list(cmds) == ["datashield", "l1"]
    assert cmds["datashield"][0] == str(REPO / cc.DATASHIELD_SCRIPT) and cmds["l1"][0] == str(REPO / cc.L1_SCRIPT)
    assert sds.main(cmds["datashield"][1:]) == 2                      # parsed; stopped at the settings load
    assert sl1.main(cmds["l1"][1:]) == 2
    assert [c[2] for c in parsed] == [sds.SETTINGS_NAME, sl1.SETTINGS_NAME]
    assert "REFUSED: stop here" in capsys.readouterr().err
    assert cmds["l1"][1] == "score" and cmds["l1"][-2:] == ["--out", "/o/plant-x/l1"]
    assert cmds["datashield"][-2:] == ["--out", "/o/plant-x/datashield"]
    assert cc.scorer_commands(REPO, Path("/prep"), POD, Path("/o/plant-x"), l1_given=True, datashield_given=False).keys() == {"datashield"}
    assert cc.scorer_commands(REPO, Path("/prep"), POD, Path("/o/plant-x"), l1_given=True, datashield_given=True) == {}


def test_the_report_command_parses_with_the_w1_parser_and_carries_no_counted(parsed, capsys):
    argv = cc.report_command(REPO, Path("/prep"), PINNED, POD, (Path("/o/l1.json"), H["l1"]),
                             (Path("/o/ds.json"), H["datashield"]), Path("/o/plant-x"))
    assert argv[0] == str(REPO / cc.REPORT_SCRIPT) and "--counted" not in argv
    assert rpr.main(argv[1:]) == 2
    assert parsed == [("report_plant_ranks.json", rpr.SETTINGS_SHA256, rpr.SETTINGS_NAME)]
    assert "REFUSED: stop here" in capsys.readouterr().err
    pairs = dict(zip(argv[1::2], argv[2::2]))
    assert pairs["--plant-record"] == f"/r/record.json:{H['record']}" and pairs["--classifier"].endswith(H["classifier"])
    assert pairs["--l1"] == f"/o/l1.json:{H['l1']}" and pairs["--datashield"] == f"/o/ds.json:{H['datashield']}"
    assert pairs["--rows"].endswith(H["rows"]) and pairs["--summary"].endswith(H["summary"])
    assert pairs["--out"] == "/o/plant-x/report"
    with pytest.raises(SystemExit):                                   # a malformed line does not parse
        rpr.main(argv[1:-2])


def test_the_file_names_are_the_w1_modules_constants():
    assert cc.REPORT_OUT == rpr.OUTPUT and cc.DATASHIELD_OUT == sds.OUTPUT and cc.L1_OUT == sl1.SCORES_FILE
    assert cc.SCAN_FILE == sl1.SCAN_FILE and cc.CLASSIFIER_OUT == scl.OUTPUT
    assert (cc.ROWS_FILE, cc.SUMMARY_FILE) == (rp.ROWS_FILE, rp.SUMMARY_FILE)
    assert cc.STEP_OUT == {"datashield": sds.OUTPUT, "l1": sl1.SCORES_FILE, "report": rpr.OUTPUT}
    assert cc.POD_INPUTS["rows"][1] == "representation" and cc.POD_INPUTS["l1_scan"][1] == "l1-scan"


def test_the_w1_manifest_pins_the_three_scripts_and_their_settings_literals():
    """MAN1 by key: the three scripts and the helpers are code entries, each module's literal SETTINGS_SHA256 is the
    manifest's entry for its settings file, and every entry of the roles the runner checks names a SHA-256 (no
    settings file is opened here)."""
    man1 = json.loads((REPO / ".ai/inputs/stage1-commitments-20261016/MANIFEST.json").read_bytes())
    entries = {e["path"]: e for e in man1["entries"]}
    assert len(entries) == len(man1["entries"])                        # no path is listed twice
    for rel in cc.MESSAGE_SOURCES:
        assert entries[rel]["role"] == "code" and s1.HEX64.match(entries[rel]["sha256"])
    for module, rel in ((rpr, "scripts/stage1/settings/report_plant_ranks.json"),
                        (sds, "scripts/stage1/settings/score_datashield.json"),
                        (sl1, "scripts/stage1/settings/score_l1_larf.json")):
        assert entries[rel]["role"] == "settings" and entries[rel]["sha256"] == module.SETTINGS_SHA256
    checked = [e for e in man1["entries"] if e["path"].startswith(cc.W1_PREFIX) and e["role"] in cc.W1_ROLES]
    assert len(checked) >= 60 and all(s1.HEX64.match(e["sha256"]) for e in checked)
    assert {e["path"] for e in checked} >= {*cc.MESSAGE_SOURCES, "scripts/stage1/labels.json",
                                            "scripts/stage1/build_plant.py", "scripts/stage1/representation_pass.py"}


def test_the_value_free_messages_of_the_real_w1_scripts():
    """On the real pinned scripts (code; read here as text): the literal refusals are whitelisted, the f-string ones
    (a cell, a row id, a hash) are not, and no whitelisted line holds a brace."""
    sources = {rel: (REPO / rel).read_bytes() for rel in cc.MESSAGE_SOURCES}
    messages = cc.value_free_messages(sources)
    assert "REFUSED: the rows file is not the one REQ-3's summary names (nothing written)" in messages
    assert "REFUSED: REQ-8's placement, rerun here, differs from the plant record's cell sizes (nothing written)" in messages
    assert "REFUSED: the scan file is not an L1 layer scan (nothing written)" in messages
    assert "REFUSED: the training rows disagree with the manifest's row count (nothing written)" in messages
    assert "REFUSED: FileNotFoundError (nothing written)" in messages
    assert not any("has no scored row" in m or "hashes to" in m or "{" in m or "}" in m for m in messages)
    assert all(m.startswith("REFUSED: ") and m.endswith(" (nothing written)") for m in messages)


def test_the_runner_defaults_name_the_repository_rules_and_the_pod(capsys):
    assert cc.RULES.relative_to(cc.REPO) == Path("runkit/stage1-olmo/stage1_rules.py")
    assert (REPO / "runkit" / "stage1-olmo" / "stage1_rules.py").is_file()
    assert cc.PLANT_WORD == "plant" and cc.SEAL_KIND == "stage1 block seal"
    with pytest.raises(SystemExit):                                   # a missing required option: argparse exits
        cc.main(["--kit", "/x"])
