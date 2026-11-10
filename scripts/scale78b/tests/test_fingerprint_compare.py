"""T6b: the fingerprint comparison on the 1B pair (Gate B's a0@1101 retrain, wave 0b, against its Gate A reference; FOCUS
2026-10-16T13:21 UTC: "fingerprint trigger false") and on tampered copies. The real units are read on this Mac through the
script's reader only (COMPLETE.json and states/<c>/state.json: hashes, flags and a step count; no evaluation file, no
text); the tests skip where the folders are absent. Tampered copies hold only those record files, never a weight."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.safety_selection.common import sha256_bytes
from scripts.scale78b import fingerprint_compare as fc

ROOT = Path(__file__).resolve().parents[3]
MAIN = Path("/Users/spiderishi/Coding/attribution")
REFERENCE = MAIN / "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1"      # Gate A a0-1101
RETRAIN = MAIN / "tmp/gate-b-olmo/retrieved/w0b-2/tree/round1/1101-a0-e1-a1"                           # Gate B's retrain
OLMO_7B_1101 = MAIN / "tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-e1-a1"
LLAMA_8B_1101 = MAIN / "tmp/family-probe-sp-llama31-8b-b5e5-1101/retrieved/sp-llama31-8b-b5e5-1101/tree/round1/1101-a0-e1-a1"
# The frozen Gate B reading's C-7 pins (scripts/gate_b_reading.py:168-169) and the retrain's COMPLETE.json SHA-256 that
# FOCUS records for wave 0b ("retrain d154f23f…").
P1101_ADAPTER = {"q": "322d737a2e0177c85b798ac779e42e637b6617cfd842455c3e1bdf4586008660",
                 "e1": "aad79060c52304ecd1b3d0a24b26281da7d147b0fc4a2754ba3a9b323bfae1ec"}
RETRAIN_COMPLETE_PREFIX = "d154f23f"
REFERENCE_COMPLETE_PREFIX = "8f0fa83a"           # the Gate A a0-1101 pin (gate_b_reading.GATE_A_PINS; test_noise_reading.A0_KEYS)
SIDE_ABBREVIATIONS = {OLMO_7B_1101: {"q": "3c7344c1", "e1": "9d5d5d8b"}, LLAMA_8B_1101: {"q": "ac05caca", "e1": "ee44580d"}}

needs_pair = pytest.mark.skipif(not (REFERENCE.is_dir() and RETRAIN.is_dir()),
                                reason="the Gate A a0-1101 unit and Gate B's wave-0b retrain are not on this Mac")


def copy_records(source: Path, dest: Path, change=None) -> Path:
    """A unit folder holding only COMPLETE.json and states/<c>/state.json, with ``change(doc, name)`` applied to each
    record (name is "COMPLETE.json" or "states/<c>/state.json"); no weight file is copied."""
    dest.mkdir(parents=True)
    marker = json.loads((source / "COMPLETE.json").read_bytes())
    if change is not None:
        change(marker, "COMPLETE.json")
    (dest / "COMPLETE.json").write_text(json.dumps(marker, sort_keys=True))
    for c in fc.CHECKPOINTS:
        state_path = source / "states" / c / "state.json"
        if state_path.is_file():
            state = json.loads(state_path.read_bytes())
            if change is not None:
                change(state, f"states/{c}/state.json")
            (dest / "states" / c).mkdir(parents=True)
            (dest / "states" / c / "state.json").write_text(json.dumps(state, sort_keys=True))
    return dest


def set_fingerprint(doc: dict, name: str, checkpoint: str, kind: str, value) -> None:
    if name == "COMPLETE.json":
        doc["checkpoints"][checkpoint][kind] = value
    elif name == f"states/{checkpoint}/state.json":
        doc[kind] = value


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", "-B", str(ROOT / "scripts/scale78b/fingerprint_compare.py"), *args],
                          capture_output=True, text=True, cwd=str(ROOT), env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def no_long_strings(obj, limit: int = 300) -> None:
    """The record holds paths, hashes, verdict words and short rule text only."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert len(str(k)) <= 64
            no_long_strings(v, limit)
    elif isinstance(obj, list):
        for v in obj:
            no_long_strings(v, limit)
    elif isinstance(obj, str):
        assert len(obj) <= limit, obj[:40]


# ----- the 1B pair --------------------------------------------------------------------------------------------------


@needs_pair
def test_the_1b_pair_is_equal_on_all_four_fingerprints_and_matches_the_frozen_readings_pins():
    retrain, reference = fc.read_unit(RETRAIN, "retrain"), fc.read_unit(REFERENCE, "reference")
    assert retrain["complete_sha256"].startswith(RETRAIN_COMPLETE_PREFIX)
    assert reference["complete_sha256"].startswith(REFERENCE_COMPLETE_PREFIX)
    record = fc.compare(retrain, reference)
    assert record["verdict"] == fc.EQUAL and (record["equal"], record["of"]) == (4, 4)
    assert [line["verdict"] for line in record["fingerprints"]] == [fc.EQUAL] * 4
    assert record["compared"] == ["q adapter_fingerprint", "q optimizer_fingerprint", "e1 adapter_fingerprint",
                                  "e1 optimizer_fingerprint"]
    for c in fc.CHECKPOINTS:                                      # the frozen reading's C-7 pins (adapter) hold
        assert retrain["fingerprints"][c]["adapter_fingerprint"] == P1101_ADAPTER[c]
        assert reference["fingerprints"][c]["adapter_fingerprint"] == P1101_ADAPTER[c]
    assert retrain["state_records_checked"] == ["q", "e1"]        # the light pull left the state records
    assert record["identity"]["training_identity"]["verdict"] == fc.EQUAL
    assert record["identity"]["manifest_sha256"]["verdict"] == fc.EQUAL
    assert record["identity"]["recipe_sha256"]["verdict"] == fc.DIFFERS      # recipe S against recipe B, by design
    no_long_strings(record)


@needs_pair
def test_the_cli_prints_hashes_and_verdicts_only_and_writes_the_record_once(tmp_path):
    out = tmp_path / "records" / "fingerprints.json"
    done = run_cli("--retrain", str(RETRAIN), "--reference", str(REFERENCE), "--expect-adapter", f"q={P1101_ADAPTER['q'][:8]}",
                   "--expect-adapter", f"e1={P1101_ADAPTER['e1']}", "--out", str(out))
    assert done.returncode == 0, done.stderr
    lines = done.stdout.splitlines()
    assert sum(1 for l in lines if " equal " in l and "_fingerprint " in l) == 4      # one line per compared fingerprint
    assert any(l.startswith("verdict: equal (4 of 4") for l in lines)
    assert all(len(l) <= 220 for l in lines if not l.startswith("record "))     # hashes and verdict words; the record line holds --out's path
    record = json.loads(out.read_bytes())
    assert record["kind"] == fc.KIND and record["verdict"] == fc.EQUAL
    assert record["expected_reference_adapter_prefixes"] == {"q": P1101_ADAPTER["q"][:8], "e1": P1101_ADAPTER["e1"]}
    assert f"record {sha256_bytes(out.read_bytes())}" in done.stdout
    no_long_strings(record)
    again = run_cli("--retrain", str(RETRAIN), "--reference", str(REFERENCE), "--out", str(out))
    assert again.returncode == 2 and "created once" in again.stderr      # never replaced
    assert json.loads(out.read_bytes()) == record


@needs_pair
def test_a_tampered_copy_of_the_retrain_differs_on_that_fingerprint_alone(tmp_path):
    other = "0" * 64

    def tamper(doc, name):
        set_fingerprint(doc, name, "e1", "adapter_fingerprint", other)
    fake = copy_records(RETRAIN, tmp_path / "retrain-tampered", tamper)
    record = fc.compare(fc.read_unit(fake, "retrain"), fc.read_unit(REFERENCE, "reference"))
    assert record["verdict"] == fc.DIFFERS and (record["equal"], record["of"]) == (3, 4)
    verdicts = {(l["checkpoint"], l["kind"]): l["verdict"] for l in record["fingerprints"]}
    assert verdicts == {("q", "adapter_fingerprint"): fc.EQUAL, ("q", "optimizer_fingerprint"): fc.EQUAL,
                        ("e1", "adapter_fingerprint"): fc.DIFFERS, ("e1", "optimizer_fingerprint"): fc.EQUAL}
    done = run_cli("--retrain", str(fake), "--reference", str(REFERENCE))
    assert done.returncode == 1 and "verdict: differs (3 of 4" in done.stdout
    # the optimizer alone differing is a difference too (ruling 10 names adapter and optimizer)
    fake2 = copy_records(RETRAIN, tmp_path / "retrain-optimizer",
                         lambda doc, name: set_fingerprint(doc, name, "q", "optimizer_fingerprint", other))
    assert fc.compare(fc.read_unit(fake2, "retrain"), fc.read_unit(REFERENCE, "reference"))["verdict"] == fc.DIFFERS


@needs_pair
def test_a_copy_whose_records_are_untouched_is_equal_to_the_original(tmp_path):
    fake = copy_records(RETRAIN, tmp_path / "retrain-copy")
    assert fc.compare(fc.read_unit(fake, "retrain"), fc.read_unit(REFERENCE, "reference"))["verdict"] == fc.EQUAL


@needs_pair
def test_a_unit_whose_state_record_disagrees_with_complete_json_refuses(tmp_path):
    def only_state(doc, name):
        if name == "states/q/state.json":
            doc["adapter_fingerprint"] = "1" * 64
    fake = copy_records(RETRAIN, tmp_path / "disagree", only_state)
    with pytest.raises(fc.Refusal, match="disagrees"):
        fc.read_unit(fake, "retrain")
    done = run_cli("--retrain", str(fake), "--reference", str(REFERENCE))
    assert done.returncode == 2 and "nothing written" in done.stderr


@needs_pair
def test_an_incomplete_unit_a_missing_checkpoint_and_a_malformed_fingerprint_refuse(tmp_path):
    def incomplete(doc, name):
        if name == "COMPLETE.json":
            doc["complete"] = False
    with pytest.raises(fc.Refusal, match="complete"):
        fc.read_unit(copy_records(RETRAIN, tmp_path / "incomplete", incomplete), "retrain")

    def no_q(doc, name):
        if name == "COMPLETE.json":
            del doc["checkpoints"]["q"]
    with pytest.raises(fc.Refusal, match="no checkpoint 'q'"):
        fc.read_unit(copy_records(RETRAIN, tmp_path / "no-q", no_q), "retrain")
    for bad in ("ABCDEF" + "0" * 58, "0" * 63, None, 7):
        def malformed(doc, name, bad=bad):
            set_fingerprint(doc, name, "e1", "optimizer_fingerprint", bad)
        with pytest.raises(fc.Refusal, match="64 lower-case hex"):
            fc.read_unit(copy_records(RETRAIN, tmp_path / f"bad-{str(bad)[:3]}", malformed), "retrain")
    error = copy_records(RETRAIN, tmp_path / "error")
    (error / "error.txt").write_text("x")
    with pytest.raises(fc.Refusal, match="error.txt"):
        fc.read_unit(error, "retrain")
    with pytest.raises(fc.Refusal, match="not a folder"):
        fc.read_unit(tmp_path / "absent", "retrain")


@needs_pair
def test_expect_adapter_pins_the_reference_to_the_registered_unit(tmp_path):
    reference = fc.read_unit(REFERENCE, "reference")
    assert fc.check_expect(reference, fc.parse_expect([f"q={P1101_ADAPTER['q'][:8]}", f"e1={P1101_ADAPTER['e1'][:12]}"]))
    with pytest.raises(fc.Refusal, match="not the registered reference"):
        fc.check_expect(reference, fc.parse_expect(["q=00000000"]))
    for spec in ("q=abcdef1", "e1=ABCDEF12", "init=" + "0" * 8, "q", "q=" + "0" * 65):
        with pytest.raises(fc.Refusal, match="expect-adapter"):
            fc.parse_expect([spec])
    with pytest.raises(fc.Refusal, match="repeats"):
        fc.parse_expect(["q=" + "0" * 8, "q=" + "1" * 8])
    done = run_cli("--retrain", str(RETRAIN), "--reference", str(REFERENCE), "--expect-adapter", "q=00000000")
    assert done.returncode == 2 and "not the registered reference" in done.stderr


@needs_pair
def test_out_is_never_inside_a_unit_and_the_same_folder_refuses(tmp_path):
    fake = copy_records(RETRAIN, tmp_path / "unit")
    for out in (fake / "record.json", fake / "states" / "q" / "x.json"):
        done = run_cli("--retrain", str(fake), "--reference", str(REFERENCE), "--out", str(out))
        assert done.returncode == 2 and "inside a unit" in done.stderr and not out.exists()
    # by directory identity: a symlink to the unit
    link = tmp_path / "link"
    link.symlink_to(fake)
    done = run_cli("--retrain", str(fake), "--reference", str(REFERENCE), "--out", str(link / "deeper" / "record.json"))
    assert done.returncode == 2 and "inside a unit" in done.stderr
    same = run_cli("--retrain", str(fake), "--reference", str(fake))
    assert same.returncode == 2 and "same folder" in same.stderr
    via_link = run_cli("--retrain", str(fake), "--reference", str(link))
    assert via_link.returncode == 2 and "same folder" in via_link.stderr


# ----- the 7-8B side units (the references of ruling 10) --------------------------------------------------------------


@pytest.mark.parametrize("unit", sorted(SIDE_ABBREVIATIONS, key=str))
def test_the_side_units_carry_the_preregistered_adapter_abbreviations(unit, tmp_path):
    if not unit.is_dir():
        pytest.skip(f"{unit.parent.parent.parent.parent.name} is not on this Mac")
    reference = fc.read_unit(unit, "reference")
    expect = fc.parse_expect([f"{c}={p}" for c, p in SIDE_ABBREVIATIONS[unit].items()])
    assert fc.check_expect(reference, expect) == SIDE_ABBREVIATIONS[unit]
    assert reference["identity"]["code_sha256"].startswith("472fc7f6")      # engine X (P78:60)
    copy = copy_records(unit, tmp_path / "retrain-copy")                   # a retrain that reproduced the side unit
    record = fc.compare(fc.read_unit(copy, "retrain"), reference, expect)
    assert record["verdict"] == fc.EQUAL and record["identity"]["code_sha256"]["verdict"] == fc.EQUAL
    done = run_cli("--retrain", str(copy), "--reference", str(unit),
                   *sum([["--expect-adapter", f"{c}={p}"] for c, p in SIDE_ABBREVIATIONS[unit].items()], []))
    assert done.returncode == 0 and "verdict: equal (4 of 4" in done.stdout
    shutil.rmtree(copy)
