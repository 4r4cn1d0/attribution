"""The stage-1 kit's round 35 tests (the plant pilot, block "P": its tables, plan, sealed edit record, the runner's
plant fingerprint record, record-done's plant units, the seal, the blinding of the edit's name) have no subject in
the 7-8B copy (K2 of T4): block P is a 1B block that belongs to runkit/stage1-olmo/ (stage1_rules.BLOCKS == ("0",)
here; PLANT_ARMS is empty), and the ported runner carries no plant fingerprint record (plant_fingerprint_record is
gone; K6's a0 fingerprint record stays and is tested in test_stage1_runner.py). The blinding rule itself (no edit
field, no U value, no answer text in a readable record) is tested at block 0 in test_kit_78b_runner.py. The stage-1
file stays unchanged in runkit/stage1-olmo/tests/test_round35.py (27 tests pass there). This file pins the removal."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
STAGE1 = KIT.parent / "stage1-olmo"


def test_the_plant_pilot_is_not_in_this_copy_and_plant_arms_is_empty():
    runner = (KIT / "setup" / "job_runner_stage1.py").read_text()
    assert "plant_fingerprint_record" not in runner and "PLANT_ARMS" not in runner
    assert "a0_fingerprint_record" in runner                                   # K6 stays (block A's reference phase)
    rules = (KIT / "stage1_rules.py").read_text()
    assert "PLANT_ARMS = frozenset()" in rules and '"P"' in rules.split("BLOCKS_1B")[1].split("\n")[0]
    manifest = json.loads((KIT / "COPY-MANIFEST.json").read_text())
    entry = next(e for e in manifest["files"] if e["path"] == "tests/test_round35.py")
    original = STAGE1 / "tests" / "test_round35.py"
    if original.is_file():
        assert hashlib.sha256(original.read_bytes()).hexdigest() == entry["sha256"]
    assert "tests/test_round35.py" in manifest["adapted_by_k2"]
