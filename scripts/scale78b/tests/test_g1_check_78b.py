"""The Llama G1 $0 check's driver: the frozen G1 code reads the family-probe layout without an adapter; parity on a
Gate B wave-0a unit whose G1 status is recorded (R_1 at 1101: gate_b_verdict.json R_G1_failed []) and on Gate A's
1101 a0 unit (the family-probe reading's recorded answers-end counts 600 / 2 / 42 / 34); a short-answer TOO CLOSE maps
to a G1 failure; the output is text-free. Reads units on this Mac through the frozen functions only (counts and
aggregates); skipped, with the reason, where they are absent."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.scale78b import g1_check_78b as g1
from scripts.scale78b import noise_reading as nr

ROOT = Path(__file__).resolve().parents[3]
MAIN = Path("/Users/spiderishi/Coding/attribution")
GATE_A = MAIN / "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1"
GATE_A_READING = MAIN / "tmp/family-probe-olmo2-1b/reading-olmo.json"
R1 = MAIN / ("tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/"
             "1101-edit-f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd-e1-a1")
VERDICT = ROOT / "research/experiments/2026-10-16-gate-b-wave0-outputs/gate_b_verdict.json"
needs_units = pytest.mark.skipif(not (GATE_A.is_dir() and R1.is_dir()), reason="the Gate A and wave-0a units are not on this Mac")


def write_units(tmp_path: Path, units: list, name="units.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps({"kind": g1.INPUTS_KIND, "version": 1, "units": units}))
    return path


def test_g1_from_the_answers_end_verdict():
    assert g1.g1_of("pass") == {"answers_end": "pass", "G1": "pass", "G1_failure_kind": None}
    assert g1.g1_of("too close") == {"answers_end": "too close", "G1": "fail", "G1_failure_kind": "short-answer TOO CLOSE"}
    assert g1.g1_of("fail") == {"answers_end": "fail", "G1": "fail", "G1_failure_kind": "FAIL"}
    with pytest.raises(SystemExit):
        g1.g1_of("missing")


def test_the_frozen_bar_reads_63_of_600_with_43_short_as_too_close_so_g1_fails():
    """FOCUS's Llama a0-1102 counts (63 of 600 screen failures, 7 capped, 43 short): the frozen answers_end_bar."""
    bars = json.loads(nr.FR.DEFAULT_BARS.read_text())
    bar = nr.FR.answers_end_bar({"sampled": {"n": 600, "capped": 7, "incoherent": 63, "short_only": 43}}, bars)
    assert bar["status"] == "too close" and bar["without_short"] == {"n": 557, "incoherent": 20}
    assert g1.g1_of(bar["status"])["G1"] == "fail"
    assert nr.FR.answers_end_bar({"sampled": {"n": 600, "capped": 6, "incoherent": 42, "short_only": 20}}, bars)["status"] == "pass"
    assert nr.FR.answers_end_bar({"sampled": {"n": 600, "capped": 7, "incoherent": 63, "short_only": 0}}, bars)["status"] == "fail"
    assert nr.FR.answers_end_bar({"sampled": {"n": 600, "capped": 31, "incoherent": 10, "short_only": 0}}, bars)["status"] == "fail"


@needs_units
def test_parity_on_a_gate_b_wave_0a_unit_and_a_gate_a_unit(tmp_path):
    doc = g1.run(write_units(tmp_path, [{"id": "R1-1101", "family": "olmo2-1b", "path": str(R1)},
                                        {"id": "gate-a-1101", "family": "olmo2-1b", "path": str(GATE_A)}]), ["test"])
    by_id = {u["id"]: u for u in doc["units"]}
    verdict = json.loads(VERDICT.read_text())["result"]
    assert verdict["R_G1_failed"] == [] and verdict["diffuse"]["G1_failed_arms"] == []   # the recorded G1 statuses: pass
    assert by_id["R1-1101"]["G1"] == "pass" and by_id["R1-1101"]["answers_end"] == "pass"
    assert by_id["R1-1101"]["arm"] == "edit" and by_id["R1-1101"]["seed"] == 1101
    assert by_id["R1-1101"]["complete_sha256"] == "391d067ca6569a04721b059da2bca2c7ee5d109de560362895198a0d40ac5f0f"
    gate_a = by_id["gate-a-1101"]
    assert gate_a["G1"] == "pass" and gate_a["arm"] == "a0" and gate_a["code_sha256"] == nr.GB.ENGINE_GATE_A
    assert gate_a["complete_sha256"] == nr.GB.GATE_A_PINS["1101"]["complete_sha256"]
    if GATE_A_READING.is_file():                                      # the family-probe reading's own record of this unit
        recorded = json.loads(GATE_A_READING.read_text())["bars_read"]["answers_end"]["per_seed"][0]
        assert {k: gate_a["sampled"][k] for k in ("n", "capped", "incoherent", "short_only")} == \
            {k: recorded[k] for k in ("n", "capped", "incoherent", "short_only")}
        assert gate_a["sampled"]["without_short"] == recorded["without_short"]
    assert doc["by_family"] == {"olmo2-1b": {"units": 2, "G1_pass": 2, "G1_fail": 0, "failed_ids": []}}
    assert doc["frozen_sha256"] == nr.FROZEN_SHA256 and doc["bars_sha256"] == nr.FR.FROZEN_BARS[nr.GB.BARS_NAME]


@needs_units
def test_the_record_is_text_free_and_written_once(tmp_path):
    units = write_units(tmp_path, [{"id": "R1-1101", "family": "olmo2-1b", "path": str(R1)}])
    out = tmp_path / "out.json"
    cmd = [sys.executable, "-I", "-B", str(ROOT / "scripts/scale78b/g1_check_78b.py"), "--units", str(units), "--out", str(out)]
    run = subprocess.run(cmd, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    doc = json.loads(out.read_text())
    assert out.read_bytes() == nr.GB.canonical(doc) and doc["kind"] == g1.OUTPUT_KIND

    def text_free(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k != "U" and not str(k).startswith("U_"), path
                text_free(v, path + "/" + str(k))
        elif isinstance(obj, list):
            for v in obj:
                text_free(v, path)
        elif isinstance(obj, str):
            assert len(obj) <= 260 and "\n" not in obj, path          # paths, ids, hashes, the rule's one line
    text_free(doc)
    assert doc["command"][0] == "g1_check_78b.py" and doc["units"][0]["G1"] == "pass"
    again = subprocess.run(cmd, capture_output=True, text=True)
    assert again.returncode != 0 and "written once" in again.stderr


@needs_units
def test_refusals(tmp_path):
    with pytest.raises(SystemExit, match="training identity is not llama31-8b's"):
        g1.run(write_units(tmp_path, [{"id": "x", "family": "llama31-8b", "path": str(GATE_A)}], "a.json"), [])
    with pytest.raises(SystemExit, match="family must be one of"):
        g1.run(write_units(tmp_path, [{"id": "x", "family": "qwen25-7b", "path": str(GATE_A)}], "b.json"), [])
    with pytest.raises(SystemExit, match="listed twice"):
        g1.run(write_units(tmp_path, [{"id": "x", "family": "olmo2-1b", "path": str(GATE_A)},
                                      {"id": "x", "family": "olmo2-1b", "path": str(GATE_A)}], "c.json"), [])
    with pytest.raises(SystemExit, match="not a unit folder"):
        g1.run(write_units(tmp_path, [{"id": "x", "family": "olmo2-1b", "path": str(tmp_path)}], "d.json"), [])
    with pytest.raises(SystemExit, match="not a scale-78b g1 check inputs file"):
        bad = tmp_path / "e.json"
        bad.write_text(json.dumps({"kind": "other", "version": 1, "units": []}))
        g1.run(bad, [])
