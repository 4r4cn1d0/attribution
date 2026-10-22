"""W1-05: the untuned-refusal strata from the untuned unit's greedy answers, and the pinned lexicon loader."""

from __future__ import annotations

import copy
import json
import shutil

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1.limits import limits_common as lc
from scripts.stage1.limits import untuned_refusal_strata as strata

import test_limits_fixtures as fx


@pytest.fixture
def untuned(tmp_path):
    root = tmp_path / "data"
    return root, fx.build_untuned(root)


def run_doc(settings, root, lexicon=None):
    return json.loads(strata.run(settings, "e" * 64, root, fx.fake_lexicon() if lexicon is None else lexicon))


def test_the_strata_by_hand(untuned):
    root, settings = untuned
    doc = run_doc(settings, root)
    assert doc["by_bank"]["harm"] == {"prompts": 200, "refusal_opening": 30,
                                      "by_class": {"DIRECT": 170, "REFUSAL-OPENING": 30}}
    assert doc["by_bank"]["overrefusal"] == {"prompts": 100, "refusal_opening": 12,
                                             "by_class": {"DIRECT": 87, "EMPTY": 1, "REFUSAL-OPENING": 12}}
    per = doc["per_prompt"]
    assert len(per) == 300 and not any(pid.startswith("s") for pid in per)          # the safety rows are not read
    assert per["h000"] == {"bank": "harm", "class": "REFUSAL-OPENING", "refusal_opening": True}
    assert per["h030"]["refusal_opening"] is False and per["p011"]["refusal_opening"] is True
    assert per["p099"] == {"bank": "overrefusal", "class": "EMPTY", "refusal_opening": False}
    assert doc["unit"]["complete_sha256"] == settings["unit"]["complete_sha256"]


def test_only_the_greedy_answers_are_read_and_no_text_is_written(untuned, monkeypatch):
    root, settings = untuned
    read = []
    original = lc.fields_of

    def spy(data, name, fields, kinds=None):
        read.append(name)
        return original(data, name, fields, kinds)

    monkeypatch.setattr(lc, "fields_of", spy)
    data = strata.run(settings, "e" * 64, root, fx.fake_lexicon())
    assert read == ["untuned generations.jsonl"]
    assert lc.text_hits(data, fx.SENTINELS) == 0 and b"SYN-REF" not in data
    assert data == strata.run(settings, "e" * 64, root, fx.fake_lexicon())


def test_the_settings_fix_the_greedy_file_the_banks_and_the_class(untuned):
    root, settings = untuned
    for change in (lambda d: d["answers"].update(file="samples.jsonl"), lambda d: d["answers"].update(mode="sampled"),
                   lambda d: d["answers"].update(banks={"harm": 200}),
                   lambda d: d["lexicon"].update(refusal_class="CAVEAT-OPENING"),
                   lambda d: d["unit"].update(checkpoint="e1"), lambda d: d["unit"].update(seed=1102)):
        doc = copy.deepcopy(settings)
        change(doc)
        with pytest.raises(s1.Refusal, match="settings"):
            strata.run(doc, "e" * 64, root, fx.fake_lexicon())


def test_a_wrong_unit_pin_or_a_missing_answer_refuses(untuned):
    root, settings = untuned
    doc = copy.deepcopy(settings)
    doc["unit"]["complete_sha256"] = "1" * 64
    with pytest.raises(s1.Refusal, match="allow-list pins"):
        strata.run(doc, "e" * 64, root, fx.fake_lexicon())
    folder = root / settings["unit"]["path"]
    path = folder / "eval" / "init" / "generations.jsonl"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    path.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in rows if r["prompt_id"] != "p050"))
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    marker["files"]["eval/init/generations.jsonl"] = sha256_bytes(path.read_bytes())
    (folder / "COMPLETE.json").write_bytes(canonical_json(marker))
    settings["unit"]["complete_sha256"] = sha256_bytes((folder / "COMPLETE.json").read_bytes())
    with pytest.raises(s1.Refusal, match="not"):
        strata.run(settings, "e" * 64, root, fx.fake_lexicon())


def test_a_record_that_would_hold_answer_text_refuses(untuned):
    root, settings = untuned
    settings["use"] = "SYN-REF " + fx.sentinel("greedy h000")    # the text of a greedy answer in a written field
    with pytest.raises(s1.Refusal, match="text values"):
        strata.run(settings, "e" * 64, root, fx.fake_lexicon())


def test_a_caveat_opening_is_not_a_refusal_opening(untuned):
    """Verification item S-9: the stratum is REFUSAL-OPENING only; a CAVEAT-OPENING answer is not in it."""
    root, settings = untuned
    caveat = lc.Lexicon(lambda text, sensitivity=False: "CAVEAT-OPENING", "x", "y", "a" * 64, "b" * 64, False,
                        ("CAVEAT-OPENING", "DIRECT", "EMPTY", "REFUSAL-OPENING"))
    doc = run_doc(settings, root, caveat)
    assert doc["by_bank"]["harm"]["refusal_opening"] == 0 and doc["by_bank"]["overrefusal"]["refusal_opening"] == 0
    assert doc["by_bank"]["overrefusal"]["by_class"] == {"CAVEAT-OPENING": 100}
    assert doc["per_prompt"]["h000"] == {"bank": "harm", "class": "CAVEAT-OPENING", "refusal_opening": False}


def test_a_class_outside_the_settings_list_refuses(untuned):
    root, settings = untuned
    odd = lc.Lexicon(lambda text, sensitivity=False: "OTHER", "x", "y", "a" * 64, "b" * 64, False,
                     ("CAVEAT-OPENING", "DIRECT", "EMPTY", "REFUSAL-OPENING"))
    with pytest.raises(s1.Refusal, match="class that the settings do not list"):
        strata.run(settings, "e" * 64, root, odd)


# ----- the pinned lexicon -----------------------------------------------------------------------------------------


def lexicon_copy(tmp_path, change_json: bool = False, change_py: bool = False) -> dict:
    spec = copy.deepcopy(fx.real_settings("limits_untuned_strata")["lexicon"])
    src = next(found for found in map(lc._lexicon_files, spec["candidates"]) if found)   # the first copy present, as load_lexicon
    folder = tmp_path / "lex"
    folder.mkdir()
    json_path, py_path = folder / "lexicon.json", folder / "lexicon.py"
    shutil.copyfile(src[0], json_path)
    shutil.copyfile(src[1], py_path)
    json_path.chmod(0o644)
    py_path.chmod(0o644)
    if change_json:
        json_path.write_bytes(json_path.read_bytes() + b" ")
    if change_py:
        py_path.write_bytes(py_path.read_bytes() + b"\n# a changed byte\n")
    spec["candidates"] = [{"json": str(json_path), "classifier": str(py_path)}]
    return spec


def test_the_real_lexicon_loads_by_its_pins_and_classifies_into_the_listed_classes(untuned):
    root, settings = untuned
    lex = lc.load_lexicon(settings["lexicon"])
    assert (lex.json_sha256, lex.classifier_sha256) == ("bbbc71e9eebb62876430ffb5e0f54113c3818984b8369924b7bd2212c4c1ca17",
                                                        "5a27dd040b74aa23fe09ac4dc95fb5913a4ccd327a67bb3caf5e667ff0432d1b")
    assert lex.label("") == "EMPTY"
    doc = json.loads(strata.run(settings, "e" * 64, root, lex))
    assert sum(b["prompts"] for b in doc["by_bank"].values()) == 300
    assert {v["class"] for v in doc["per_prompt"].values()} <= set(lex.classes)
    assert doc["lexicon"]["json_sha256"] == lex.json_sha256
    data = strata.run(settings, "e" * 64, root, lex)
    assert lc.text_hits(data, fx.SENTINELS) == 0


def test_a_changed_lexicon_byte_refuses(tmp_path):
    for kwargs in ({"change_json": True}, {"change_py": True}):
        sub = tmp_path / ("j" if "change_json" in kwargs else "p")
        sub.mkdir()
        with pytest.raises(s1.Refusal, match="differ from their pins"):
            lc.load_lexicon(lexicon_copy(sub, **kwargs))
    spec = lexicon_copy(tmp_path)
    assert lc.load_lexicon(spec).label("") == "EMPTY"                      # an unchanged copy loads
    spec["candidates"] = [{"json": str(tmp_path / "none.json"), "classifier": str(tmp_path / "none.py")}]
    with pytest.raises(s1.Refusal, match="no lexicon copy"):
        lc.load_lexicon(spec)


def test_the_command_writes_the_strata_and_prints_counts_only(untuned, tmp_path, monkeypatch, capsys):
    root, settings = untuned
    path = tmp_path / "limits_untuned_strata.json"
    path.write_bytes(canonical_json(settings))
    monkeypatch.setattr(strata, "SETTINGS_SHA256", sha256_bytes(path.read_bytes()))
    out = tmp_path / "out"
    assert strata.main(["--out", str(out), "--data-root", str(root), "--settings", str(path)]) == 0
    printed = capsys.readouterr()
    assert (out / "untuned_refusal_strata.json").is_file()
    assert lc.text_hits((printed.out + printed.err).encode(), fx.SENTINELS) == 0
    assert "harm: 200 prompts" in printed.out
    assert strata.main(["--out", str(tmp_path / "o2"), "--data-root", str(tmp_path / "nothing")]) == 2
    assert not (tmp_path / "o2").exists()
