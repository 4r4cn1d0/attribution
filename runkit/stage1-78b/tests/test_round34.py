"""The stage-1 kit's round 34 tests (B14's similarity pass on theta0, block "sim": its pins, plan, runner step, record,
light check and record-done) have no subject in the 7-8B copy (K2 of T4): the similarity kind is a 1B kind that
belongs to runkit/stage1-olmo/ (stage1_rules.BLOCKS == ("0",) here), and the ported runner, finisher and record-done
path carry no similarity step (similarity_record, similarity_args, SIM_* are gone; the finisher's similarity_check is
gone). The stage-1 file stays unchanged in runkit/stage1-olmo/tests/test_round34.py (63 tests pass there; the K1
report, command 23). This file pins the removal."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
STAGE1 = KIT.parent / "stage1-olmo"


def test_the_similarity_pass_is_not_in_this_copys_runner_or_finisher():
    runner = (KIT / "setup" / "job_runner_stage1.py").read_text()
    finisher = (KIT / "finisher.py").read_text()
    rules = (KIT / "stage1_rules.py").read_text()
    for name in ("similarity_record", "similarity_args", "similarity_pins", "SIM_SCRIPT", "SIM_ADD_SETS", "overlap_similarity"):
        assert name not in runner, name
    assert "similarity_check" not in finisher and "similarity_record_problem" not in finisher
    assert "SIM_SCRIPT" not in rules and '"sim"' not in rules.split("BLOCKS_1B")[0]
    manifest = json.loads((KIT / "COPY-MANIFEST.json").read_text())
    entry = next(e for e in manifest["files"] if e["path"] == "tests/test_round34.py")
    original = STAGE1 / "tests" / "test_round34.py"
    if original.is_file():
        assert hashlib.sha256(original.read_bytes()).hexdigest() == entry["sha256"]
    assert "tests/test_round34.py" in manifest["adapted_by_k2"]
