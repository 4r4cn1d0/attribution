"""L1, L13 (7), addendum section 4.1: labels.json is append-only after T1. An appended entry changes no frozen
settings check and no output byte; a changed entry that a settings file names refuses."""

from __future__ import annotations

import json

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1 import write_score_edit as wse

import s1fixtures as fx
from test_t1_pins import BUILD_PLANT_SHA256, SETTINGS, WRITE_SCORE_EDIT_SHA256
from test_write_score_edit import GOLDEN_A1_SHA256

APPENDED = {"base_seed": 20261008, "id_domain": "synthetic ids", "label": "stage1-zz-append-probe-v1",
            "named_in": "a test-only append", "owner": "scripts/stage1/zz_append_probe.py", "parts": [],
            "use": "shows that an append changes no frozen output"}


def registry_copy(tmp_path, change=None):
    doc = json.loads(s1.LABELS_PATH.read_bytes())
    doc["labels"]["zz.append_probe"] = APPENDED
    if change is not None:
        change(doc)
    path = tmp_path / "labels-appended.json"
    path.write_bytes(canonical_json(doc))
    return path


def use_registry(monkeypatch, path):
    monkeypatch.setattr(s1, "LABELS_PATH", path)
    monkeypatch.setattr(s1, "_REGISTRY", None)


def load_both():
    s1.load_settings(SETTINGS / "write_score_edit.json", WRITE_SCORE_EDIT_SHA256, "write_score_edit")
    s1.load_settings(SETTINGS / "build_plant.json", BUILD_PLANT_SHA256, "build_plant")


def test_an_appended_entry_changes_no_frozen_check_or_output(tmp_path, monkeypatch):
    fix = fx.build_fixture(tmp_path / "f")
    before = wse.build_a1(fix["prepared"]["root"], fix["unit"], fix["settings"], "f" * 64)
    path = registry_copy(tmp_path)
    use_registry(monkeypatch, path)
    assert "zz.append_probe" in s1.registry() and s1.labels_sha256() == sha256_bytes(path.read_bytes())
    load_both()
    after = wse.build_a1(fix["prepared"]["root"], fix["unit"], fix["settings"], "f" * 64)
    assert after == before
    rec = json.loads(after["a1_selection.json"])
    assert sha256_bytes(canonical_json({"scores": rec["scores"], "selected": rec["selected"]})) == GOLDEN_A1_SHA256


@pytest.mark.parametrize("key,refused", [("a1.ties", "write_score_edit"), ("l1.ties", "write_score_edit"),
                                         ("plant.leaf", "build_plant"), ("plant.r600", "build_plant")])
def test_a_changed_named_entry_refuses(tmp_path, monkeypatch, key, refused):
    def change(doc):
        doc["labels"][key]["use"] = doc["labels"][key]["use"] + " (changed)"
    use_registry(monkeypatch, registry_copy(tmp_path, change))
    pin = WRITE_SCORE_EDIT_SHA256 if refused == "write_score_edit" else BUILD_PLANT_SHA256
    with pytest.raises(s1.Refusal, match="missing or changed"):
        s1.load_settings(SETTINGS / f"{refused}.json", pin, refused)
    other = "build_plant" if refused == "write_score_edit" else "write_score_edit"
    other_pin = BUILD_PLANT_SHA256 if other == "build_plant" else WRITE_SCORE_EDIT_SHA256
    s1.load_settings(SETTINGS / f"{other}.json", other_pin, other)          # an entry it does not name: no refusal


def test_a_removed_named_entry_refuses(tmp_path, monkeypatch):
    use_registry(monkeypatch, registry_copy(tmp_path, lambda doc: doc["labels"].pop("a1.ties")))
    with pytest.raises(s1.Refusal, match="missing or changed"):
        s1.load_settings(SETTINGS / "write_score_edit.json", WRITE_SCORE_EDIT_SHA256, "write_score_edit")
