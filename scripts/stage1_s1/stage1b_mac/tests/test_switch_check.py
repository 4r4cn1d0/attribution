"""The Self-Inf-N switch check on synthetic settings whose other fields hold sentinels: the two printed lines, every
refusal, the default pin equal to the W1 manifest's entry (read by key), and no sentinel in stdout or stderr."""

from __future__ import annotations

import json

import pytest
import synth_world as sw

from scripts.stage1_s1.stage1b_mac import switch_check as sc


def settings_doc(switch) -> dict:
    return {"kind": "stage1 settings", "name": sc.SETTINGS_NAME, "k": 37,
            "construction_checks": ["l1", "h1", "h2a", "h2b", "datashield", "classifier"],
            "counting": {"scorers": ["a1", "selfinf_n"], "selfinf_n_counts": switch, "rule": sw.SENTINELS["text"]},
            "rules": {"leaf": sw.SENTINELS["leaf"], "unit": sw.SENTINELS["unit"]}}


@pytest.fixture
def settings(tmp_path):
    def make(switch=True, change=None):
        doc = settings_doc(switch)
        if change is not None:
            change(doc)
        path = tmp_path / "settings.json"
        return path, sw.write(path, sw.jbytes(doc))
    return make


def run(capsys, path, digest):
    code = sc.main(["--settings", str(path), "--expect-sha256", digest])
    captured = capsys.readouterr()
    assert not sw.sentinel_hits(captured.out) and not sw.sentinel_hits(captured.err), (captured.out, captured.err)
    return code, captured.out, captured.err


def test_prints_the_pin_and_the_switch_only(settings, capsys):
    path, digest = settings(True)
    assert run(capsys, path, digest) == (0, f"settings sha256 {digest}\nselfinf_n_counts true\n", "")
    path, digest = settings(False)
    assert run(capsys, path, digest) == (0, f"settings sha256 {digest}\nselfinf_n_counts false\n", "")


def refused(capsys, path, digest, message):
    assert run(capsys, path, digest) == (2, "", f"REFUSED: {message}\n")


def test_refuses_a_file_off_its_pin_or_missing(settings, capsys):
    path, digest = settings(True)
    refused(capsys, path, "0" * 64, "the settings file does not hash to its expected SHA-256")
    refused(capsys, path, "xyz", "--expect-sha256 is not 64 lowercase hex")
    refused(capsys, path.with_name("none.json"), digest, "the settings file is missing or not a regular file")


def test_refuses_settings_of_another_name_or_kind(settings, capsys):
    path, digest = settings(True, lambda d: d.update(name="build_plant"))
    refused(capsys, path, digest, "the settings are not the plant-rank report's")
    path, digest = settings(True, lambda d: d.update(kind="other"))
    refused(capsys, path, digest, "the settings are not the plant-rank report's")


def test_refuses_a_missing_or_non_boolean_switch(settings, capsys):
    path, digest = settings(True, lambda d: d["counting"].pop("selfinf_n_counts"))
    refused(capsys, path, digest, "the settings hold no counting.selfinf_n_counts")
    path, digest = settings(True, lambda d: d.pop("counting"))
    refused(capsys, path, digest, "the settings hold no counting.selfinf_n_counts")
    path, digest = settings(1)
    refused(capsys, path, digest, "counting.selfinf_n_counts is not a JSON boolean")
    path, digest = settings("true")
    refused(capsys, path, digest, "counting.selfinf_n_counts is not a JSON boolean")


def test_refuses_a_file_that_is_not_a_json_object(tmp_path, capsys):
    path = tmp_path / "x.json"
    digest = sw.write(path, b"[]")
    refused(capsys, path, digest, "the settings file is not a JSON object")


def test_the_default_pin_is_the_w1_manifests_entry():
    """The report's literal SETTINGS_SHA256 (the default --expect-sha256) is the W1 manifest's entry for its settings
    file, read by key; the settings file itself is not opened here."""
    man1 = json.loads((sw.repo_root() / ".ai/inputs/stage1-commitments-20261016/MANIFEST.json").read_bytes())
    entry = next(e for e in man1["entries"] if e["path"] == "scripts/stage1/settings/report_plant_ranks.json")
    assert entry["role"] == "settings" and entry["sha256"] == sc.SETTINGS_SHA256
    assert sc.SETTINGS_PATH.name == "report_plant_ranks.json" and sc.KEY_PATH == ("counting", "selfinf_n_counts")
