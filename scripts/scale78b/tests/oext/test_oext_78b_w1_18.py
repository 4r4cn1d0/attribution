"""The w1_18 command (the 7-8B W1-18 check per family; DES E2, DESO2 item 37, GXB O4): the unchanged
scripts/stage1/limits/overrefusal_checks.py main() run with the family's settings file, on W1-18's own ENGINEERING
FIXTURES (synthetic units, a fake decoder, a fake judge; the model path is not tested, as in the 1B tests). Parity:
the record equals the 1B main's byte for byte. The record's provenance names the family settings' SHA-256, which the
family's O-ext settings pin, so oext_eval reads that record, and a record made under other settings refuses. The
family's derived settings take synthetic units at the family's own unit paths. None of these numbers is a
scientific result."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import oext78_fixtures as f
import test_limits_fixtures as tf

w, oe, ofx = f.w, f.oe, f.ofx
w1 = oe.w1_18
KINDS = {"B-1101": "A", "G-1101": "B", "bt-1102": "S"}
TOOLS = {"device": "test", "judge": "a fake judge", "decoder": "a fake decoder"}


@pytest.fixture
def fake_tools(monkeypatch):
    seen = {}

    def tools(doc, device, ledger_dir, guard_batch_size=None):
        seen.update(device=device, guard_batch_size=guard_batch_size)
        return tf.fake_judge_records, tf.fake_decode, TOOLS

    monkeypatch.setattr(w1, "real_tools", tools)
    return seen


def checks_family(tmp_path: Path, settings: dict) -> tuple[f.Family, Path, str]:
    fam = f.Family(tmp_path / "fam")
    fam.manifest = settings["prepared"]["manifest_sha256"]
    fam.branch = oe.PENDING
    path, digest = fam.put("limits_overrefusal_checks", settings)
    return fam, path, digest


def test_the_wrapper_gives_the_1b_record_byte_for_byte(tmp_path, fake_tools, monkeypatch, capsys):
    root = tmp_path / "data"
    settings, _, source = tf.build_checks(root, KINDS)
    tf.seal_source_map(settings, root, source)
    fam, path, digest = checks_family(tmp_path, settings)
    code, out, err = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w"), "--data-root",
                                     str(root), "--device", "cuda", "--guard-batch-size", "4"])
    assert code == 0, err[-300:]
    assert fake_tools == {"device": "cuda", "guard_batch_size": 4}
    monkeypatch.setattr(w1, "SETTINGS_SHA256", digest)
    assert w1.main(["--out", str(tmp_path / "d"), "--data-root", str(root), "--device", "cuda",
                    "--guard-batch-size", "4", "--settings", str(path)]) == 0
    wrapped = (tmp_path / "w" / w1.OUTPUT).read_bytes()
    assert wrapped == (tmp_path / "d" / w1.OUTPUT).read_bytes()
    assert sorted(p.name for p in (tmp_path / "w").iterdir()) == [w1.OUTPUT]
    doc = json.loads(wrapped)
    assert doc["provenance"]["settings_sha256"] == digest and doc["provenance"]["script"] == \
        "scripts/stage1/limits/overrefusal_checks.py"
    assert not any(t in out + err for t in tf.SENTINELS)
    assert w1.SETTINGS_SHA256 == digest                      # (set here by monkeypatch; the wrapper restored its own)


def test_the_wrapper_restores_w1_18s_globals(tmp_path, fake_tools):
    root = tmp_path / "data"
    settings, _, _ = tf.build_checks(root, {"B-1101": "A"})
    fam, _, _ = checks_family(tmp_path, settings)
    before = (w1.SETTINGS_PATH, w1.SETTINGS_SHA256)
    code, _, _ = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w"), "--data-root",
                                 str(root)])
    assert code == 0 and (w1.SETTINGS_PATH, w1.SETTINGS_SHA256) == before
    assert w1.SETTINGS_SHA256 == "bfa9a56fd0522de066cb04b6f84b99dffda54fbe4b297dc3e4c7f07961c4a41b"


def test_the_records_provenance_is_the_family_settings_hash_and_oext_eval_reads_it(tmp_path, fake_tools):
    """GXB O4 and P2 section 4.2: each family's branch is read from its own record. The family's record names the
    family's W1-18 settings; the family's O-ext settings pin that hash, so oext_eval.read_w1_18 takes the record and
    gives the branch it implies; a record made under the 1B settings, or under the other family's, refuses."""
    root = tmp_path / "data"
    settings, _, _ = tf.build_checks(root, {"B-1101": "A", "G16-1101": "D"})        # both pass the bar
    fam, _, digest = checks_family(tmp_path, settings)
    code, _, err = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w"), "--data-root",
                                   str(root)])
    assert code == 0, err
    record = tmp_path / "w" / w1.OUTPUT
    doc = json.loads(record.read_bytes())
    assert doc["provenance"]["settings_sha256"] == digest == fam.files["limits_overrefusal_checks"][1]
    assert doc["truncation_check"]["pass"] is True
    eval_doc = ofx.settings_doc(branch="128", cut=128, w1_18_sha256=f.sha(record))
    eval_doc["cap"]["w1_18"]["settings_sha256"] = digest
    got = oe.read_w1_18(oe.settings_from_doc(eval_doc), record)
    assert (got.record_sha256, got.passed, got.units) == (f.sha(record), True, 2)
    full = copy.deepcopy(eval_doc)
    full["cap"]["branch"] = "full"
    with pytest.raises(f.s1.Refusal, match="so the branch is 128, not full"):
        oe.read_w1_18(oe.settings_from_doc(full), record)
    other = copy.deepcopy(eval_doc)
    other["cap"]["w1_18"]["settings_sha256"] = "bfa9a56fd0522de066cb04b6f84b99dffda54fbe4b297dc3e4c7f07961c4a41b"
    with pytest.raises(f.s1.Refusal, match="not made under the pinned W1-18 settings"):
        oe.read_w1_18(oe.settings_from_doc(other), record)


def test_the_familys_derived_settings_take_units_at_the_familys_paths(tmp_path, fake_tools):
    """The derived settings/limits_overrefusal_checks__olmo2-7b.json with only its pins replaced by synthetic ones (the
    prepared set's manifest, each unit's two pins, the source-map extraction pin): its path pattern admits the family's
    four unit paths (RK KIT a0_units), and the record lists exactly theta0 and a0 1101-1103."""
    real = json.loads((f.mk.SETTINGS_DIR / f.mk.file_name("limits_overrefusal_checks", f.FAMILY)).read_bytes())
    root = tmp_path / "data"
    synthetic, _, _ = tf.build_checks(root, {"B-1101": "A"})                # the bank and P at the same path as OLMo's
    assert synthetic["prepared"]["path"] == real["prepared"]["path"]
    doc = copy.deepcopy(real)
    doc["prepared"]["manifest_sha256"] = synthetic["prepared"]["manifest_sha256"]
    doc["source_map"]["extraction"]["bank_source_manifest_sha256"] = \
        synthetic["source_map"]["extraction"]["bank_source_manifest_sha256"]
    for (name, spec), kind in zip(sorted(doc["units"].items()), "ADGS"):
        design = tf.checks_unit_design(kind)
        gens = [{"prompt_id": pid, "kind": "overrefusal", "output_ids": design[pid], "text": tf.fake_decode(design[pid]),
                 "stop_reason": "eos"} for pid in tf.O_IDS]
        sealed = tf.fake_judge_records([(pid, "", tf.fake_decode(design[pid])) for pid in tf.O_IDS])
        guard = [{"prompt_id": pid, "kind": "overrefusal", **{k: v for k, v in r.items() if k != "item_id"}}
                 for pid, r in zip(tf.O_IDS, sealed)]
        pins = tf.write_unit(root, spec["path"], seed=spec["seed"], checkpoint=spec["checkpoint"],
                             identity={**tf.GATE_A_IDENTITY, "recipe_sha256": "c" * 64}, guard=guard, generations=gens)
        spec.update(complete_sha256=pins["complete_sha256"], job_sha256=pins["job_sha256"])
    fam, _, digest = checks_family(tmp_path, doc)
    code, _, err = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w"), "--data-root",
                                   str(root)])
    assert code == 0, err[-400:]
    record = json.loads((tmp_path / "w" / w1.OUTPUT).read_bytes())
    assert sorted(record["units"]) == ["a0-1101", "a0-1102", "a0-1103", "untuned"]
    assert {n: u["path"] for n, u in record["units"].items()} == {n: s["path"] for n, s in doc["units"].items()}
    assert record["units"]["untuned"]["checkpoint"] == "init" and record["provenance"]["settings_sha256"] == digest


def test_theta0s_null_job_pin_refuses_in_the_wrapper_and_in_the_1b_check(tmp_path, fake_tools):
    """On an all-null copy (the pre-fill state, whatever the committed pins hold after T-O2 step 1: OR1)."""
    pins = json.loads(f.mk.PINS_PATH.read_bytes())
    for fam_pins in pins["families"].values():
        fam_pins["units"]["untuned"]["job_sha256"] = None
        fam_pins["w1_18"] = {"branch": "pending_w1_18", "record_sha256": None, "record_path": None,
                             "full_reason": None}
    pins_path, sdir = tmp_path / "pins.json", tmp_path / "null-settings"
    pins_path.write_bytes(f.mk.dumps(pins))
    assert f.call(f.mk.main, ["--pins", str(pins_path), "--settings-dir", str(sdir), "--records-root", str(tmp_path)])[0] == 0
    real = json.loads((sdir / f.mk.file_name("limits_overrefusal_checks", f.FAMILY)).read_bytes())
    assert real["units"]["untuned"]["job_sha256"] is None
    with pytest.raises(f.s1.Refusal, match="unit untuned job_sha256"):
        w1.check_content(real)
    fam, _, _ = checks_family(tmp_path, real)
    fam.waits = [{"pin": "THETA0_JOB", "event": f.mk.EVENTS["THETA0_JOB"], "where": ["families.x.units.untuned"],
                  "roles": ["limits_overrefusal_checks"]}]
    code, _, err = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w")])
    assert code == 2 and "the pin THETA0_JOB is null" in err and not (tmp_path / "w").exists()
    fam.waits = []
    code, _, err = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w")])
    assert code == 2 and "job_sha256" in err and not (tmp_path / "w").exists()
