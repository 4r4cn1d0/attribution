"""Addendum section 4.5: the two T1 settings files are pinned by literal SHA-256 (REQ-8's future build_plant.py loads
its settings with BUILD_PLANT_SHA256)."""

from __future__ import annotations

from experiments.safety_selection.common import sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1 import write_score_edit as wse

BUILD_PLANT_SHA256 = "06f70d98af8ac16d79067863142a408f0e65862463305975579f075763f8687e"
WRITE_SCORE_EDIT_SHA256 = "9fc5f359133e76fd464b13ed34eb13eb74bf25d71edeb0add0c8d8eae992f9b5"
SETTINGS = s1.HERE / "settings"


def test_the_settings_files_are_the_t1_ones():
    assert sha256_file(SETTINGS / "build_plant.json") == BUILD_PLANT_SHA256
    assert sha256_file(SETTINGS / "write_score_edit.json") == WRITE_SCORE_EDIT_SHA256
    assert wse.SETTINGS_SHA256 == WRITE_SCORE_EDIT_SHA256 and wse.SETTINGS_PATH == SETTINGS / "write_score_edit.json"


def test_both_settings_files_load_with_their_literal_pins():
    assert s1.load_settings(SETTINGS / "build_plant.json", BUILD_PLANT_SHA256, "build_plant")[1] == BUILD_PLANT_SHA256
    assert s1.load_settings(SETTINGS / "write_score_edit.json", WRITE_SCORE_EDIT_SHA256,
                            "write_score_edit")[1] == WRITE_SCORE_EDIT_SHA256
