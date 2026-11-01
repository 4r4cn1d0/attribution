"""G1 (addendum 34 points 1 and 3): the input builder accepts exactly two O-ext settings pairs, engine X's for every
unit but B+Qi's and engine Y's for B+Qi's, and refuses any other (synthetic kit folders only)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
import synth_kit as sk

from scripts.stage1_s1.reading_input.__main__ import main
from scripts.stage1_s1.reading_input.build import OEXT_SETTINGS, oext_engine
from scripts.stage1_s1.reading_input.sources import load_rules

S1 = Path(__file__).resolve().parents[2]            # scripts/stage1_s1 of the tree under test
X, Y = OEXT_SETTINGS["X"], OEXT_SETTINGS["Y"]
OTHER = ("1" * 64, "2" * 64)


@pytest.fixture(scope="session")
def worlds(tmp_path_factory):
    cache = {}

    def get(reading):
        if reading not in cache:
            cache[reading] = sk.make(tmp_path_factory.mktemp(reading), reading)
        return cache[reading]
    return get


def run(s, tmp_path, capsys):
    out, rec = tmp_path / "tables.json", tmp_path / "sources.json"
    rc = main(s.args(out, rec, overlap=False))
    cap = capsys.readouterr()
    return rc, cap.out, cap.err, out, rec


def refused(s, tmp_path, capsys, match):
    rc, out, err, path, rec = run(s, tmp_path, capsys)
    assert rc == 2 and out == "" and not path.exists() and not rec.exists(), err
    assert err.startswith("REFUSED: ") and re.search(match, err), err
    return err


def oext_folder(s, plan, kind, arm, seed):
    host, i, job = sk.find_job(plan, kind, arm, seed)
    tree = s.kit / "retrieved" / host / "tree"
    return host, i, job, tree, tree / f"job-{i}" / "oext"


def set_pair(s, kind, arm, seed, pair, complete_eval=None):
    """A hash-consistent edit: the O-ext pass's job.json names ``pair``, its COMPLETE.json names job.json's new
    SHA-256 and ``complete_eval`` (default pair[1]) as its O-ext settings; plan.json's outputs and the seal re-taken."""
    plan = s.plan()
    host, i, job, tree, folder = oext_folder(s, plan, kind, arm, seed)
    doc = json.loads((folder / "job.json").read_text())
    doc["settings_sha256"], doc["oext"]["settings_sha256"] = pair
    job_sha = sk.write(folder / "job.json", sk.jbytes(doc))

    def mutate(d):
        d["job_sha256"] = job_sha
        d["oext"]["settings_sha256"] = complete_eval or pair[1]
    sk.recomplete(folder, mutate)
    job["outputs"] = sk._outputs(tree, f"job-{i}/oext")
    sk.seal_block(s.kit, plan, plan["hosts"][host]["block"])
    s.save_plan(plan)


def sha_file(rel: str) -> str:
    return hashlib.sha256((S1 / rel).read_bytes()).hexdigest()


def literal(rel: str, name: str) -> str:
    return re.search(rf'^{name} = "([0-9a-f]{{64}})"', (S1 / rel).read_text(), re.M).group(1)


# ----- the two pairs -------------------------------------------------------------------------------------------------


def test_the_two_pairs_are_the_settings_files_the_runners_and_the_kits_pins():
    assert X == (sha_file("settings/oext_unit.json"), sha_file("settings/oext_eval.json"))
    assert Y == (sha_file("settings/oext_unit_y.json"), sha_file("settings/oext_eval_y.json"))
    assert X == (literal("oext_unit.py", "SETTINGS_SHA256"), literal("oext_eval.py", "SETTINGS_SHA256"))
    assert Y == (literal("oext_unit_y.py", "SETTINGS_SHA256"), literal("oext_unit_y.py", "OEXT_SETTINGS_SHA256"))
    rules, _ = load_rules(sk.REAL_RULES)
    assert X == (rules.S1_CODE["scripts/stage1_s1/settings/oext_unit.json"],
                 rules.S1_CODE["scripts/stage1_s1/settings/oext_eval.json"])
    assert Y == (rules.S1_OEXT_Y["scripts/stage1_s1/settings/oext_unit.json"]["sha256"],
                 rules.S1_OEXT_Y["scripts/stage1_s1/settings/oext_eval.json"]["sha256"])
    assert X[0] != Y[0] and X[1] != Y[1]


@pytest.mark.parametrize("job,engine", [
    ({"kind": "ref_train", "recipe": "bqi"}, "Y"), ({"kind": "ref_train", "recipe": "G"}, "X"),
    ({"kind": "arm", "recipe": "S"}, "X"), ({"kind": "a0_arm", "recipe": "bqi"}, "X"), ({"kind": "o_only"}, "X")])
def test_the_engine_of_a_pass(job, engine):
    assert oext_engine(job) == engine


# ----- accepted ------------------------------------------------------------------------------------------------------


def test_x_units_on_x_and_bqi_on_y_are_accepted(worlds, tmp_path, capsys):
    s = worlds("plan_a")
    plan = s.plan()
    for kind, arm, seed, pair in (("ref_train", "bqi", 1105, Y), ("ref_train", "G", 1106, X), ("arm", "S1", 1105, X),
                                  ("o_only", "a0", 1101, X), ("o_only", "theta0", None, X)):
        *_, folder = oext_folder(s, plan, kind, arm, seed)
        doc = json.loads((folder / "job.json").read_text())
        assert (doc["settings_sha256"], doc["oext"]["settings_sha256"]) == pair
        assert json.loads((folder / "COMPLETE.json").read_text())["oext"]["settings_sha256"] == pair[1]
    assert sk.find_job(plan, "ref_train", "bqi", 1105)[2]["engine"] == "Y"
    rc, out, err, path, rec = run(s, tmp_path, capsys)
    assert rc == 0, err
    record = json.loads(rec.read_text())
    bqi = record["references"]["ref-bqi 1105"]["o"][0]
    assert bqi["folder"].startswith("ref-bqi 1105 O-ext") and "job.json" in bqi["files"]


# ----- refused -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind,arm,seed,pair,match", [
    ("arm", "S1", 1103, Y, r"S1 1103 O-ext .*its O-ext settings are engine Y's pair; a unit of engine X needs engine X's"),
    ("arm", "S1", 1103, (X[0], Y[1]), r"its O-ext settings are not an accepted pair; a unit of engine X"),
    ("arm", "S1", 1103, (Y[0], X[1]), r"its O-ext settings are not an accepted pair; a unit of engine X"),
    ("arm", "S1", 1103, OTHER, r"its O-ext settings are not an accepted pair; a unit of engine X"),
    ("o_only", "a0", 1101, Y, r"a0 1101 O-ext .*engine Y's pair; a unit of engine X"),
    ("o_only", "theta0", None, Y, r"theta0 O-ext .*engine Y's pair; a unit of engine X"),
])
def test_a_block_a_pass_with_another_pair_is_refused(worlds, tmp_path, capsys, kind, arm, seed, pair, match):
    s = sk.copy(worlds("plan_a_block_a_only"), tmp_path / "w")
    set_pair(s, kind, arm, seed, pair)
    refused(s, tmp_path, capsys, match)


@pytest.mark.parametrize("arm,seed,pair,match", [
    ("bqi", 1106, X, r"ref-bqi 1106 O-ext .*engine X's pair; a unit of engine Y needs engine Y's"),
    ("bqi", 1106, (Y[0], X[1]), r"ref-bqi 1106 O-ext .*not an accepted pair; a unit of engine Y"),
    ("G", 1106, Y, r"ref-G 1106 O-ext .*engine Y's pair; a unit of engine X"),
])
def test_a_reference_pass_with_another_pair_is_refused(worlds, tmp_path, capsys, arm, seed, pair, match):
    s = sk.copy(worlds("plan_a"), tmp_path / "w")
    set_pair(s, "ref_train", arm, seed, pair)
    refused(s, tmp_path, capsys, match)


def test_the_completion_record_must_repeat_job_jsons_o_ext_settings(worlds, tmp_path, capsys):
    s = sk.copy(worlds("plan_a_block_a_only"), tmp_path / "w")
    set_pair(s, "arm", "H1", 1104, X, complete_eval=Y[1])
    refused(s, tmp_path, capsys, r"H1 1104 O-ext .*COMPLETE.json's oext.settings_sha256 is not job.json's")
    set_pair(s, "arm", "H1", 1104, X)                  # back to engine X's pair: accepted
    assert run(s, tmp_path, capsys)[0] == 0


@pytest.mark.parametrize("kind,arm,seed,engine,match", [
    ("ref_train", "bqi", 1107, "X", r"ref-bqi 1107: plan.json records engine 'X'; this unit's O-ext pass is engine Y's"),
    ("arm", "A1", 1105, "Y", r"A1 1105: plan.json records engine 'Y'; this unit's O-ext pass is engine X's"),
    ("ref_train", "G", 1105, None, r"ref-G 1105: plan.json records engine 'None'; this unit's O-ext pass is engine X's"),
])
def test_plan_json_must_record_the_passs_engine(worlds, tmp_path, capsys, kind, arm, seed, engine, match):
    s = sk.copy(worlds("plan_a"), tmp_path / "w")
    plan = s.plan()
    sk.find_job(plan, kind, arm, seed)[2]["engine"] = engine
    s.save_plan(plan)
    refused(s, tmp_path, capsys, match)


@pytest.mark.parametrize("field,value", [("oext", Y[1]), ("engine", "Y")])
def test_a_b10_unit_must_name_engine_xs_o_ext_settings(worlds, tmp_path, capsys, field, value):
    s = sk.copy(worlds("plan_a"), tmp_path / "w")
    plan = s.plan()
    host, i, job = sk.find_job(plan, "ref_eval", seed=1106)
    if field == "engine":
        job["engine"] = value
    else:
        unit = next(u for u in job["units"] if u["unit"].endswith("prefix"))
        folder = s.kit / "retrieved" / host / "tree" / unit["unit"]
        doc = json.loads((folder / "job.json").read_text())
        doc["oext"]["settings_sha256"] = value
        job_sha = sk.write(folder / "job.json", sk.jbytes(doc))
        unit["complete_sha256"] = sk.recomplete(folder, lambda d: d.update(job_sha256=job_sha))
        job["complete_sha256"] = job["units"][0]["complete_sha256"]
        sk.seal_block(s.kit, plan, "B")
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"a B10 unit runs on engine X and names engine X's O-ext settings")
