"""The decisive check: engine Y's own Y2 code (imported by path from engine Y's workspace, in a child process that
imports nothing else; tests/ycheck.py) accepts the file write_c3_subsample.py writes for the development role, through
the job check, the file checks, the dev-only access rule, the membership and field checks against the opened dev bank,
the token check of every item, eval-state's checks, and a whole development run-one on the tiny CPU fixtures that
evaluates exactly the 16 listed items; and refuses the file when one id is changed (to an id outside the bank, or to
the bank's 17th id), when one byte changes under the same bank id, and when its source is renamed hidden (the
development role is dev-only). Synthetic prepared data only."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes

import c3fixtures as cx
from c3guard import guarded

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")


@pytest.fixture(scope="module")
def p17(tmp_path_factory):
    """A synthetic P whose dev bank holds 17 items (5 harm, 4 over-refusal, 3 safety, 3 arc_utility, 2 arc_generation)."""
    return cx.build_p(tmp_path_factory.mktemp("c3y-p17"), harm=5, over=4)


@pytest.fixture(scope="module")
def checked(p17, tmp_path_factory):
    """Guarded (c3guard): the writer's output and engine Y's verdict on it and on its altered copies."""
    def make():
        folder, sha = p17
        work = tmp_path_factory.mktemp("c3y-work")
        data, record = cx.build(folder, sha)
        doc = json.loads(data)
        lines = cx.dev_lines(folder)
        good_bank, good = cx.write_doc(work / "tmp" / "c3.json", data)
        stranger = copy.deepcopy(doc)
        stranger["items"][3]["prompt_id"] = "p-0000000000000000"
        stranger_bank, stranger_path = cx.write_doc(work / "tmp" / "stranger.json", stranger)
        neighbour = copy.deepcopy(doc)
        neighbour["items"][3]["prompt_id"] = lines[16]["prompt_id"]       # in the dev bank, other fields
        neighbour_bank, neighbour_path = cx.write_doc(work / "tmp" / "neighbour.json", neighbour)
        flipped = data.replace(b'"version": 1\n}', b'"version": 1 \n}')
        assert flipped != data
        _, flipped_path = cx.write_doc(work / "tmp" / "flipped.json", flipped)
        hidden = copy.deepcopy(doc)
        manifest = json.loads((folder / "manifest.json").read_bytes())
        hidden["source"] = {**hidden["source"], "bank": "hidden",
                            "bank_file_sha256": manifest["files"]["hidden/hidden.jsonl"]}
        hidden_bank, hidden_path = cx.write_doc(work / "tmp" / "hidden.json", hidden)
        cases = [{"name": "written", "file": str(good), "bank": good_bank, "run": True, "out_dir": str(work / "run")},
                 {"name": "stranger_id", "file": str(stranger_path), "bank": stranger_bank},
                 {"name": "neighbour_id", "file": str(neighbour_path), "bank": neighbour_bank},
                 {"name": "flipped_byte", "file": str(flipped_path), "bank": good_bank},
                 {"name": "hidden_source", "file": str(hidden_path), "bank": hidden_bank}]
        return {"y": cx.run_ycheck(work / "y", folder, sha, cases), "doc": doc, "lines": lines, "bank": good_bank,
                "record": json.loads(record), "data": data}

    return guarded("checked", make)


def test_engine_y_is_imported_by_path_and_alone(checked):
    y = checked["y"]
    assert Path(y["jobs_file"]).is_relative_to(cx.ENGINE_Y_ROOT.resolve())
    assert y["all_experiments_modules_in_engine_y"] is True
    assert y["engine_y_identity"] == cx.EXPECTED_ENGINE_Y


def test_engine_y_accepts_the_written_file_for_the_development_role(checked):
    case = checked["y"]["cases"]["written"]
    assert case["ok"] is True, case
    first16 = [i["prompt_id"] for i in checked["lines"][:16]]
    assert case["ids"] == first16
    assert case["view_banks"] == [checked["bank"]]
    expected: dict[str, int] = {}
    for item in checked["lines"][:16]:
        expected[item["kind"]] = expected.get(item["kind"], 0) + 1
    assert case["counts"] == expected and sum(expected.values()) == 16
    assert case["source"]["bank"] == "dev"


def test_a_development_run_one_evaluates_exactly_the_16_listed_items(checked):
    case = checked["y"]["cases"]["written"]
    assert case["ok"] is True, case
    gen = [i for i, k in zip(case["ids"], case["kinds"]) if k in ("safety", "arc_generation", "harm", "overrefusal")]
    arc = [i for i, k in zip(case["ids"], case["kinds"]) if k == "arc_utility"]
    assert case["generated_ids"] == gen and case["arc_ids"] == arc
    assert len(gen) + len(arc) == 16
    assert checked["lines"][16]["prompt_id"] not in case["generated_ids"] + case["arc_ids"]
    sub = case["complete_bank_subsample"]
    assert sub["bank"] == checked["bank"] == checked["record"]["subsample"]["bank"]
    assert sub["counts"] == checked["record"]["subsample"]["counts"]
    assert sub["source"] == checked["record"]["source"] and sub["draw"] == checked["record"]["draw"]


@pytest.mark.parametrize("name, error, match", [
    ("stranger_id", "JobError", "is not in the dev bank"),
    ("neighbour_id", "JobError", "(ITEM3_ID): fields"),
    ("flipped_byte", "JobError", "SHA-256 differs from the bank"),
    ("hidden_source", "AccessError", "dev-sourced bank subsample only"),
])
def test_engine_y_refuses_the_file_with_one_id_or_byte_or_its_source_changed(checked, name, error, match):
    case = checked["y"]["cases"][name]
    assert case["ok"] is False, case
    assert case["error_type"] == error and match.replace("ITEM3_ID", checked["lines"][16]["prompt_id"]) \
        in case["message"], case


def test_the_record_names_the_file_engine_y_checked(checked):
    rec = checked["record"]
    assert rec["subsample"]["file_sha256"] == sha256_bytes(checked["data"])
    assert rec["subsample"]["bank"] == checked["bank"]
    assert canonical_json(checked["doc"]) == checked["data"]
