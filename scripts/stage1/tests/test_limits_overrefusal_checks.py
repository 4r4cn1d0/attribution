"""W1-18: the three over-refusal checks on existing answers, with a fake decoder, a fake judge and a fake lexicon
(the model path of the lead's real run is not tested here); the sealed source map and its one-time extraction."""

from __future__ import annotations

import copy
import json
import os

import pytest

from experiments.safety_selection import prepare
from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1.limits import limits_common as lc
from scripts.stage1.limits import overrefusal_checks as orc

import test_limits_fixtures as fx

KINDS = {"B-1101": "A", "G-1101": "B", "bt-1101": "C", "G16-1101": "D", "G-1102": "E", "G-1103": "G", "bt-1102": "S"}
TOOLS = {"device": "test", "judge": "a fake judge", "decoder": "a fake decoder"}


@pytest.fixture
def checks(tmp_path):
    """The units of KINDS, with the sealed source map extracted once and pinned."""
    root = tmp_path / "data"
    settings, designs, source = fx.build_checks(root, KINDS)
    fx.seal_source_map(settings, root, source)
    return root, settings, designs, source


@pytest.fixture
def unsealed(tmp_path):
    """The same units with the settings' real source-map pin (null): no map yet."""
    root = tmp_path / "data"
    settings, designs, source = fx.build_checks(root, KINDS)
    return root, settings, designs, source


def run_doc(settings, root, judge=fx.fake_judge_records):
    return json.loads(orc.run(settings, "d" * 64, root, judge, fx.fake_decode, fx.fake_lexicon(), TOOLS))


def rewrite_marker(settings, root, name, rel):
    """After a test changed one listed file of a unit: COMPLETE.json lists its new hash, and the unit is re-pinned."""
    spec = settings["units"][name]
    folder = root / spec["path"]
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    marker["files"][rel] = sha256_bytes((folder / rel).read_bytes())
    data = canonical_json(marker)
    (folder / "COMPLETE.json").write_bytes(data)
    spec["complete_sha256"] = sha256_bytes(data)
    spec["job_sha256"] = sha256_bytes((folder / "job.json").read_bytes())


def flipping_judge(calls):
    """The fake judge, except that every '#cut' item gets the other Yes/No answer: a judge that answers the same text
    differently in a second position (the batch noise of verification item S-2)."""
    def judge(items):
        calls.append([item_id for item_id, _, _ in items])
        out = fx.fake_judge_records(items)
        for (item_id, _, _), record in zip(items, out):
            if item_id.endswith("#cut") and record["valid"]:
                record["refusal"] = "No" if record["refusal"] == "Yes" else "Yes"
        return out
    return judge


# ----- check 1: truncation ------------------------------------------------------------------------------------------


def test_the_truncation_check_by_hand(checks):
    root, settings, _, _ = checks
    doc = run_doc(settings, root)
    got = {n: (u["truncation"]["flags_agree"], u["truncation"]["count_move"], u["truncation"]["pass"])
           for n, u in doc["units"].items()}
    assert got == {"B-1101": (98, 2, True), "G-1101": (97, 3, False), "bt-1101": (96, 0, False),
                   "G16-1101": (97, 1, True), "G-1102": (99, 1, True), "G-1103": (97, 3, False),
                   "bt-1102": (100, 0, True)}
    a = doc["units"]["B-1101"]["truncation"]
    assert (a["refused_full"], a["refused_cut"], a["invalid_full"], a["invalid_cut"], a["cap_tokens"]) == (12, 10, 1, 1, 128)
    assert doc["units"]["B-1101"]["answers_longer_than_cap"] == 2
    assert doc["units"]["B-1101"]["answers_judged_at_the_cut"] == 2
    assert doc["truncation_check"] == {"units": 7, "units_failing": ["G-1101", "G-1103", "bt-1101"], "pass": False,
                                       "bar": settings["truncation"]["bar_text"]}


def test_a_marker_at_index_128_is_cut_at_a_128_token_cap(checks):
    root, settings, _, _ = checks
    e = run_doc(settings, root)["units"]["G-1102"]
    assert (e["truncation"]["refused_full"], e["truncation"]["refused_cut"]) == (1, 0)
    assert e["answers_longer_than_cap"] == 1


def test_a_net_gain_at_the_cut_moves_the_count(checks):
    """Verification item S-1: the move is counted either way (abs), so 3 refusals gained at the cut fail the bar."""
    ids = [f"p{i:03d}" for i in range(100)]
    full = {p: (False, True, "No") for p in ids}
    cut = {p: (i < 3, True, "Yes" if i < 3 else "No") for i, p in enumerate(ids)}
    out = orc.truncation(full, cut, ids, {"cap_tokens": 128, "min_flags_agree": 97, "max_count_move": 2})
    assert (out["flags_agree"], out["refused_full"], out["refused_cut"], out["count_move"], out["pass"]) == (
        97, 0, 3, 3, False)
    root, settings, _, _ = checks
    g = run_doc(settings, root)["units"]["G-1103"]["truncation"]                 # the same on unit files
    assert (g["refused_full"], g["refused_cut"], g["count_move"], g["pass"]) == (0, 3, 3, False)


def test_an_answer_of_at_most_the_cap_is_judged_once(checks):
    """Verification item S-2: an answer of at most 128 tokens is its own cut answer; only longer answers are judged at
    the cut, so a judge that answers the same text differently in a second position moves only the long answers."""
    root, settings, _, _ = checks
    calls: list[list[str]] = []
    doc = run_doc(settings, root, judge=flipping_judge(calls))
    s = doc["units"]["bt-1102"]
    assert (s["answers_longer_than_cap"], s["answers_judged_at_the_cut"]) == (1, 1)
    t = s["truncation"]
    assert (t["flags_agree"], t["refused_full"], t["refused_cut"], t["count_move"], t["pass"]) == (99, 2, 1, 1, True)
    assert all(sum(i.endswith("#full") for i in c) == 100 for c in calls)
    cut_items = sorted(i for c in calls for i in c if i.endswith("#cut"))
    assert len(calls) == 7 and len(cut_items) == sum(u["answers_longer_than_cap"] for u in doc["units"].values())
    assert "p011#cut" in cut_items and "p010#cut" not in cut_items and "p012#cut" not in cut_items
    a = doc["units"]["B-1101"]["truncation"]               # p030, p031 (200 tokens): the flipped cut says Yes again
    assert (a["flags_agree"], a["refused_full"], a["refused_cut"]) == (100, 12, 12)


# ----- checks 2 and 3 -----------------------------------------------------------------------------------------------


def test_judge_lexicon_agreement_and_partial_refusals_by_hand(checks):
    root, settings, _, _ = checks
    a = run_doc(settings, root)["units"]["B-1101"]
    sealed = a["agreement"]["sealed"]["all"]
    assert sealed == {"n": 100, "agree": 95, "judge_yes_lexicon_yes": 8, "judge_yes_lexicon_no": 3,
                      "judge_no_lexicon_yes": 2, "judge_no_lexicon_no": 86, "judge_invalid_lexicon_yes": 0,
                      "judge_invalid_lexicon_no": 1}
    mac = a["agreement"]["mac_full"]["all"]
    assert (mac["agree"], mac["judge_yes_lexicon_no"], mac["judge_no_lexicon_no"]) == (94, 4, 85)
    by_source = a["agreement"]["mac_full"]["by_source"]
    assert by_source["xstest"] == {"n": 50, "agree": 44, "judge_yes_lexicon_yes": 8, "judge_yes_lexicon_no": 4,
                                   "judge_no_lexicon_yes": 2, "judge_no_lexicon_no": 35, "judge_invalid_lexicon_yes": 0,
                                   "judge_invalid_lexicon_no": 1}
    assert by_source["orbench"]["judge_no_lexicon_no"] == 50 and by_source["orbench"]["agree"] == 50
    assert a["partial_refusals"]["sealed"]["all"] == {"lexicon_opening_judge_no": 2, "judge_yes_no_lexicon_opening": 3}
    assert a["partial_refusals"]["mac_full"]["all"] == {"lexicon_opening_judge_no": 2, "judge_yes_no_lexicon_opening": 4}
    assert a["partial_refusals"]["mac_full"]["by_source"]["orbench"] == {"lexicon_opening_judge_no": 0,
                                                                        "judge_yes_no_lexicon_opening": 0}
    assert a["lexicon"] == {"by_class": {"DIRECT": 90, "REFUSAL-OPENING": 10}, "refusal_opening": 10}
    assert a["device_report_only"] == {"sealed_refused": 11, "mac_full_refused": 12, "flags_agree": 99}
    assert a["mac_decode_equals_stored_text"] == 100


def test_an_invalid_judge_answer_is_not_a_partial_refusal():
    """Verification item S-10: a lexicon refusal opening with an invalid judge answer is not a judge "No"."""
    judge = {"a": (False, False, None), "b": (False, True, "No")}
    assert orc.partial_refusals(judge, {"a": True, "b": True}, ["a", "b"]) == {
        "lexicon_opening_judge_no": 1, "judge_yes_no_lexicon_opening": 0}


# ----- pins and inputs ----------------------------------------------------------------------------------------------


def test_every_unit_is_pinned_and_its_hashes_are_recorded(checks):
    """Verification item S-13: every unit, the seven development units included, needs both pins, and they must hold."""
    root, settings, _, _ = checks
    doc = run_doc(settings, root)
    folder = root / settings["units"]["G-1101"]["path"]
    assert doc["units"]["G-1101"]["complete_sha256"] == sha256_bytes((folder / "COMPLETE.json").read_bytes())
    assert all(u["complete_sha256"] == settings["units"][n]["complete_sha256"] for n, u in doc["units"].items())
    wrong = copy.deepcopy(settings)
    wrong["units"]["G-1101"]["complete_sha256"] = "2" * 64
    with pytest.raises(s1.Refusal, match="allow-list pins"):
        run_doc(wrong, root)
    for field in ("complete_sha256", "job_sha256"):
        unpinned = copy.deepcopy(settings)
        unpinned["units"]["bt-1101"][field] = None
        with pytest.raises(s1.Refusal, match="bt-1101 " + field):
            run_doc(unpinned, root)


def test_every_unit_is_read_before_the_judge_is_called(checks):
    """A unit that refuses stops the run before the first judge call (so before the guard model loads)."""
    root, settings, _, _ = checks
    calls: list[list[str]] = []
    last = sorted(settings["units"])[-1]
    settings["units"][last]["job_sha256"] = "6" * 64
    with pytest.raises(s1.Refusal, match=f"unit {last}: job.json"):
        run_doc(settings, root, judge=flipping_judge(calls))
    assert calls == []


def test_a_missing_sealed_judge_record_refuses(checks):
    """Verification item S-11: the sealed records' ids must be the dev bank's ids."""
    root, settings, _, _ = checks
    path = root / settings["units"]["G-1101"]["path"] / "eval" / "e1" / "guard.jsonl"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    path.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in rows[:-1]))
    rewrite_marker(settings, root, "G-1101", "eval/e1/guard.jsonl")
    with pytest.raises(s1.Refusal, match="not the dev bank's prompts"):
        run_doc(settings, root)


def test_answers_that_are_not_the_bank_prompts_refuse(checks):
    root, settings, _, _ = checks
    path = root / settings["units"]["G-1101"]["path"] / "eval" / "e1" / "generations.jsonl"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    path.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in rows[:-1]))
    rewrite_marker(settings, root, "G-1101", "eval/e1/generations.jsonl")
    with pytest.raises(s1.Refusal, match="not the dev bank's prompts"):
        run_doc(settings, root)


def test_a_gate_b_recipe_or_path_refuses(checks):
    root, settings, _, _ = checks
    job_path = root / settings["units"]["G-1101"]["path"] / "job.json"
    job = json.loads(job_path.read_bytes())
    job["recipe_sha256"] = fx.RECIPE_S
    job_path.write_bytes(canonical_json(job))
    rewrite_marker(settings, root, "G-1101", "job.json")
    with pytest.raises(s1.Refusal, match="Gate B"):
        run_doc(settings, root)
    other = copy.deepcopy(settings)
    other["units"]["G-1101"]["path"] = "gate-b-olmo/retrieved/olmo2-1b-1101/tree/wave1/1101-a0-e1-a1"
    with pytest.raises(s1.Refusal, match="allowed form"):
        run_doc(other, root)


def test_the_same_attempt_listed_twice_refuses(checks):
    root, settings, _, _ = checks
    settings["units"]["G-1103"] = {**settings["units"]["G-1101"]}
    with pytest.raises(s1.Refusal, match="listed twice"):
        run_doc(settings, root)


def test_a_judge_that_returns_another_count_or_shape_refuses(checks):
    root, settings, _, _ = checks
    with pytest.raises(s1.Refusal, match="another number"):
        run_doc(settings, root, judge=lambda items: fx.fake_judge_records(items)[:-1])
    with pytest.raises(s1.Refusal, match="no boolean valid"):
        run_doc(settings, root, judge=lambda items: [{"valid": "yes", "refusal": "Yes"} for _ in items])


def test_the_prepared_set_must_verify(checks):
    root, settings, _, _ = checks
    settings["prepared"]["manifest_sha256"] = "3" * 64
    with pytest.raises(s1.Refusal, match="does not verify"):
        run_doc(settings, root)


def test_the_settings_rules(checks):
    root, settings, _, _ = checks
    for change in (lambda d: d["truncation"].update(cap_tokens=-1), lambda d: d["bank"].update(size=99),
                   lambda d: d["lexicon"].update(refusal_class="DIRECT"), lambda d: d["units"]["G-1101"].update(arm="R"),
                   lambda d: d.pop("judge"), lambda d: d["source_map"].update(mode="auditor"),
                   lambda d: d["source_map"]["sealed_map"].update(sha256=None),
                   lambda d: d["source_map"]["sealed_map"].update(sha256="x" * 64),
                   lambda d: d["source_map"]["extraction"].update(bank_source_manifest_sha256=None),
                   lambda d: d["units"]["G-1102"].update(job_sha256=None)):
        doc = copy.deepcopy(settings)
        change(doc)
        with pytest.raises(s1.Refusal, match="settings"):
            run_doc(doc, root)


# ----- the sealed source map ----------------------------------------------------------------------------------------


def test_the_source_map_comes_from_the_pinned_sealed_map_only(checks, monkeypatch):
    """Verification item S-3: the per-source tables come from the pinned small map; the run reads no auditor file."""
    root, settings, _, _ = checks
    read = []
    original = prepare.read_verified

    def spy(folder, manifest, name):
        read.append(name)
        return original(folder, manifest, name)

    monkeypatch.setattr(prepare, "read_verified", spy)
    doc = run_doc(settings, root)
    assert read == ["banks/dev.jsonl"]                                   # P's dev bank only: no auditor file
    assert doc["source_map"] == {"available": True, "note": "", "prompts_by_source": {"orbench": 50, "xstest": 50},
                                 "sha256": settings["source_map"]["sealed_map"]["sha256"]}
    assert doc["provenance"]["inputs"]["source_map/dev_overrefusal_source_map.json"] == doc["source_map"]["sha256"]
    off = copy.deepcopy(settings)
    off["source_map"]["mode"] = "off"
    doc = run_doc(off, root)
    assert doc["source_map"]["available"] is False and doc["units"]["B-1101"]["agreement"]["sealed"]["by_source"] is None
    assert "mode off" in doc["source_map"]["note"]


def test_without_a_pinned_map_the_per_source_tables_are_unavailable(unsealed):
    root, settings, _, _ = unsealed
    assert fx.real_settings("limits_overrefusal_checks")["source_map"]["sealed_map"]["sha256"] is None
    doc = run_doc(settings, root)
    assert doc["source_map"] == {"available": False, "prompts_by_source": None, "sha256": None,
                                 "note": doc["source_map"]["note"]}
    assert "S-3" in doc["source_map"]["note"] and "--extract-source-map" in doc["source_map"]["note"]
    unit = doc["units"]["B-1101"]
    assert unit["agreement"]["sealed"]["by_source"] is None and unit["partial_refusals"]["mac_full"]["by_source"] is None
    assert unit["agreement"]["sealed"]["all"]["agree"] == 95


def _rewrite_map(settings, root, change):
    path = root / settings["source_map"]["sealed_map"]["path"]
    doc = json.loads(path.read_bytes())
    change(doc)
    data = canonical_json(doc)
    path.write_bytes(data)
    settings["source_map"]["sealed_map"]["sha256"] = sha256_bytes(data)


def test_a_sealed_map_that_differs_from_its_pin_refuses(checks):
    root, settings, _, _ = checks
    path = root / settings["source_map"]["sealed_map"]["path"]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(s1.Refusal, match="the settings pin"):
        run_doc(settings, root)
    path.unlink()
    with pytest.raises(s1.Refusal, match="source map is missing"):
        run_doc(settings, root)


@pytest.mark.parametrize("change", [
    lambda d: d.update(bank_sha256="7" * 64), lambda d: d.update(prepared_manifest_sha256="7" * 64),
    lambda d: d.update(kind="another map"), lambda d: d.update(bank_source_manifest_sha256="7" * 64)])
def test_a_sealed_map_of_another_bank_refuses(checks, change):
    root, settings, _, _ = checks
    _rewrite_map(settings, root, change)
    with pytest.raises(s1.Refusal, match="not the map of this prepared set's dev bank"):
        run_doc(settings, root)


@pytest.mark.parametrize("change", [lambda d: d["sources"].pop("p007"), lambda d: d["sources"].update(p007="a b"),
                                    lambda d: d["sources"].update(extra="xstest")])
def test_a_sealed_map_without_one_short_source_per_prompt_refuses(checks, change):
    root, settings, _, _ = checks
    _rewrite_map(settings, root, change)
    with pytest.raises(s1.Refusal, match="one short source id"):
        run_doc(settings, root)


def test_a_sealed_map_without_a_ruling_refuses(checks):
    root, settings, _, _ = checks
    _rewrite_map(settings, root, lambda d: d.update(ruling="  "))
    with pytest.raises(s1.Refusal, match="records no ruling"):
        run_doc(settings, root)


def test_a_sealed_map_path_outside_the_data_root_refuses(checks, tmp_path):
    root, settings, _, _ = checks
    for rel in ("../outside.json", str(root / fx.SOURCE_MAP_REL)):
        doc = copy.deepcopy(settings)
        doc["source_map"]["sealed_map"]["path"] = rel
        with pytest.raises(s1.Refusal, match="not a relative path inside the data root"):
            run_doc(doc, root)
    outside = tmp_path / "outside-maps"
    outside.mkdir()
    (outside / "map.json").write_bytes((root / fx.SOURCE_MAP_REL).read_bytes())
    os.symlink(outside, root / "linked-maps")
    doc = copy.deepcopy(settings)
    doc["source_map"]["sealed_map"]["path"] = "linked-maps/map.json"
    with pytest.raises(s1.Refusal, match="leaves the data root"):
        run_doc(doc, root)


# ----- the one-time extraction --------------------------------------------------------------------------------------


def test_the_extraction_by_hand(unsealed):
    root, settings, _, source = unsealed
    data = orc.extract_source_map(settings, "e" * 64, root, source, "  " + fx.RULING + " ")
    doc = json.loads(data)
    assert doc["kind"] == orc.SOURCE_MAP_KIND and doc["version"] == 1 and doc["ruling"] == fx.RULING
    assert doc["sources"] == {pid: ("xstest" if i < 50 else "orbench") for i, pid in enumerate(fx.O_IDS)}
    assert doc["prompts_by_source"] == {"orbench": 50, "xstest": 50}
    p_manifest = json.loads((root / settings["prepared"]["path"] / "manifest.json").read_bytes())
    source_manifest = json.loads((source / "manifest.json").read_bytes())
    # P's dev bank is a re-tokenized copy (other bytes, as in the real P); the import record binds the two
    assert p_manifest["files"]["banks/dev.jsonl"] != source_manifest["files"]["banks/dev.jsonl"]
    assert p_manifest["bank_import"]["files"]["banks/dev.jsonl"] == source_manifest["files"]["banks/dev.jsonl"]
    assert doc["prepared_manifest_sha256"] == settings["prepared"]["manifest_sha256"]
    assert doc["bank_sha256"] == p_manifest["files"]["banks/dev.jsonl"] and doc["bank_file"] == "banks/dev.jsonl"
    assert doc["bank_source_manifest_sha256"] == settings["source_map"]["extraction"]["bank_source_manifest_sha256"]
    assert doc["provenance"]["settings_sha256"] == "e" * 64
    assert b"hidden-1" not in data and b"record" not in data                  # nothing else of the auditor file
    assert lc.text_hits(data, fx.SENTINELS) == 0
    assert data == orc.extract_source_map(settings, "e" * 64, root, source, fx.RULING)


@pytest.mark.parametrize("ruling", ["", "   ", None, 5])
def test_the_extraction_needs_the_leads_ruling(unsealed, ruling):
    root, settings, _, source = unsealed
    with pytest.raises(s1.Refusal, match="ruling"):
        orc.extract_source_map(settings, "e" * 64, root, source, ruling)


def test_the_extraction_refuses_another_bank_source(unsealed):
    root, settings, _, source = unsealed
    with pytest.raises(s1.Refusal, match="bank source prepared set"):            # P itself: another manifest
        orc.extract_source_map(settings, "e" * 64, root, root / settings["prepared"]["path"], fx.RULING)
    other = copy.deepcopy(settings)
    other["source_map"]["extraction"]["bank_source_manifest_sha256"] = "5" * 64  # P's manifest names another source
    with pytest.raises(s1.Refusal, match="does not name the pinned bank source"):
        orc.extract_source_map(other, "e" * 64, root, source, fx.RULING)


def _rewrite_source(settings, source, auditor=None, bank=None):
    """Rewrite the bank source's auditor or dev bank, its manifest, and the pins that name it (P's bank_import too)."""
    manifest = json.loads((source / "manifest.json").read_bytes())
    files = {name: (source / name).read_bytes() for name in manifest["files"]}
    if auditor is not None:
        files["auditor/construction.json"] = canonical_json(auditor)
    if bank is not None:
        files["banks/dev.jsonl"] = bank
    pin = fx.write_prepared(source, files)
    settings["source_map"]["extraction"]["bank_source_manifest_sha256"] = pin
    return pin


def _repoint_p(settings, root, pin, imported=None):
    """P's manifest names the new bank source pin; its bank_import keeps the recorded file hashes unless imported."""
    prep = root / settings["prepared"]["path"]
    manifest = json.loads((prep / "manifest.json").read_bytes())
    files = {name: (prep / name).read_bytes() for name in manifest["files"]}
    bank_import = {**manifest["bank_import"], "source_manifest_sha256": pin}
    if imported is not None:
        bank_import["files"] = imported
    settings["prepared"]["manifest_sha256"] = fx.write_prepared(prep, files, {"bank_import": bank_import})


@pytest.mark.parametrize("case", ["hidden", "kind", "missing", "no_source", "long_source", "no_map"])
def test_the_extraction_refuses_an_auditor_map_without_every_dev_entry(unsealed, case):
    root, settings, _, source = unsealed
    auditor = json.loads((source / "auditor/construction.json").read_bytes())
    entry = auditor["prompts"]["p042"]
    if case == "hidden":
        entry["bank"] = "hidden"
    elif case == "kind":
        entry["kind"] = "harm"
    elif case == "missing":
        del auditor["prompts"]["p042"]
    elif case == "no_source":
        del entry["source"]
    elif case == "long_source":
        entry["source"] = "x" * 161
    else:
        del auditor["prompts"]
    _repoint_p(settings, root, _rewrite_source(settings, source, auditor=auditor))
    with pytest.raises(s1.Refusal, match="no 'prompts' map" if case == "no_map" else "short source id"):
        orc.extract_source_map(settings, "e" * 64, root, source, fx.RULING)


def test_the_extraction_refuses_a_bank_source_with_another_dev_bank(unsealed, monkeypatch):
    """The bank source's dev bank must be the file that P's manifest records as imported (bank_import.files); when it
    is not, the auditor file is not even read."""
    root, settings, _, source = unsealed
    other_bank = (source / "banks/dev.jsonl").read_bytes() + b'{"kind": "harm", "prompt": "x", "prompt_id": "h999"}\n'
    _repoint_p(settings, root, _rewrite_source(settings, source, bank=other_bank))
    read = []
    original = prepare.read_verified

    def spy(folder, manifest, name):
        read.append(name)
        return original(folder, manifest, name)

    monkeypatch.setattr(prepare, "read_verified", spy)
    with pytest.raises(s1.Refusal, match="not the one that P's manifest records as imported"):
        orc.extract_source_map(settings, "e" * 64, root, source, fx.RULING)
    assert read == ["banks/dev.jsonl"]                                    # P's dev bank only; no auditor file
    other = copy.deepcopy(settings)
    _repoint_p(other, root, other["source_map"]["extraction"]["bank_source_manifest_sha256"], imported={})
    with pytest.raises(s1.Refusal, match="not the one that P's manifest records as imported"):
        orc.extract_source_map(other, "e" * 64, root, source, fx.RULING)


def test_an_extraction_that_would_hold_prompt_text_refuses(unsealed):
    root, settings, _, source = unsealed
    benign = next(t for t in fx.SENTINELS if "benign prompt p001" in t)
    with pytest.raises(s1.Refusal, match="text values"):
        orc.extract_source_map(settings, "e" * 64, root, source, benign)


# ----- no text ------------------------------------------------------------------------------------------------------


def test_no_text_reaches_the_record(checks):
    root, settings, _, _ = checks
    data = orc.run(settings, "d" * 64, root, fx.fake_judge_records, fx.fake_decode, fx.fake_lexicon(), TOOLS)
    assert lc.text_hits(data, fx.SENTINELS) == 0
    assert b"must never be stored" not in data and b"w3 w3" not in data
    assert b"hidden-1" not in data
    assert data == orc.run(settings, "d" * 64, root, fx.fake_judge_records, fx.fake_decode, fx.fake_lexicon(), TOOLS)


def test_a_record_that_would_hold_text_refuses(checks):
    root, settings, _, _ = checks
    settings["requirement"] = fx.SENTINELS[-1]                      # a text the run saw, in a written field
    with pytest.raises(s1.Refusal, match="text values"):
        run_doc(settings, root)


# ----- the commands -------------------------------------------------------------------------------------------------


def test_the_real_tools_refuse_a_recipe_that_differs_from_its_pin(checks, tmp_path):
    _, settings, _, _ = checks
    settings["judge"]["recipe_file_sha256"] = "4" * 64
    with pytest.raises(s1.Refusal, match="recipe file differs"):
        orc.real_tools(settings, "cpu", tmp_path / "ledger")


def _settings_file(settings, tmp_path, monkeypatch):
    path = tmp_path / "limits_overrefusal_checks.json"
    path.write_bytes(canonical_json(settings))
    monkeypatch.setattr(orc, "SETTINGS_SHA256", sha256_bytes(path.read_bytes()))
    return path


def test_the_command_writes_once_with_injected_tools(checks, tmp_path, monkeypatch, capsys):
    root, settings, _, source = checks
    path = _settings_file(settings, tmp_path, monkeypatch)
    seen = {}

    def tools(doc, device, ledger_dir):
        seen.update(device=device, ledger=ledger_dir)
        return fx.fake_judge_records, fx.fake_decode, TOOLS

    monkeypatch.setattr(orc, "real_tools", tools)
    out = tmp_path / "out"
    args = ["--out", str(out), "--data-root", str(root), "--settings", str(path)]
    assert orc.main(args) == 0
    printed = capsys.readouterr()
    doc = json.loads((out / "overrefusal_checks.json").read_bytes())
    assert doc["source_map"]["available"] is True and doc["truncation_check"]["pass"] is False
    assert seen == {"device": "mps", "ledger": out.with_name("out-judge-ledger")}
    assert lc.text_hits((printed.out + printed.err).encode(), fx.SENTINELS) == 0
    assert "truncation check pass: False" in printed.out and "per-source tables: available" in printed.out
    assert orc.main(args) == 2 and "not empty" in capsys.readouterr().err
    assert orc.main(["--out", str(tmp_path / "o3"), "--data-root", str(root), "--settings", str(path),
                     "--bank-source", str(source)]) == 2
    assert "belong to --extract-source-map" in capsys.readouterr().err and not (tmp_path / "o3").exists()


def test_the_extraction_command_writes_the_map_and_loads_no_model(unsealed, tmp_path, monkeypatch, capsys):
    root, settings, _, source = unsealed
    path = _settings_file(settings, tmp_path, monkeypatch)

    def no_tools(*args):
        raise AssertionError("the extraction must not build the judge")

    monkeypatch.setattr(orc, "real_tools", no_tools)
    out = tmp_path / "map-out"
    args = ["--extract-source-map", "--out", str(out), "--data-root", str(root), "--settings", str(path),
            "--bank-source", str(source), "--ruling", fx.RULING]
    assert orc.main(args) == 0
    printed = capsys.readouterr()
    data = (out / orc.SOURCE_MAP_OUTPUT).read_bytes()
    assert data == orc.extract_source_map(settings, sha256_bytes(path.read_bytes()), root, source, fx.RULING)
    assert sha256_bytes(data) in printed.out and "{'orbench': 50, 'xstest': 50}" in printed.out
    assert lc.text_hits((printed.out + printed.err).encode(), fx.SENTINELS) == 0
    assert orc.main(["--extract-source-map", "--out", str(tmp_path / "m2"), "--data-root", str(root),
                     "--settings", str(path), "--ruling", fx.RULING]) == 2
    assert "needs --bank-source" in capsys.readouterr().err and not (tmp_path / "m2").exists()
    assert orc.main(["--extract-source-map", "--out", str(tmp_path / "m3"), "--data-root", str(root),
                     "--settings", str(path), "--bank-source", str(source)]) == 2
    assert "ruling" in capsys.readouterr().err and not (tmp_path / "m3").exists()
