"""The stage-1 kit's round 31 tests (27 Oct 2026; addendum §32 points 1-3; the lead's K1-K6) have, but for K6, no
subject in the 7-8B copy (K3 of T4): K1 (a not-run decision for a released judge launch of block B, after its seal),
K2 (block B's required units, its ref_train units, REJUDGED_PINS["B"], init-block's judge launch over block B's units)
and K5 (the finisher's watch of a moved block-B host) are 1B block-B machinery that belongs to runkit/stage1-olmo/
(stage1_rules.BLOCKS == ("0",) here; REJUDGED_PINS == {"0": ()}; the World of tests/test_stage1_runkit.py has no
_block_b_ready). K6 (launch.py exits non-zero when a host it should create has no pod.json) IS ported, on block 0's
host of both families: tests/test_gated_78b.py::test_k6_launch_exits_non_zero_when_a_host_it_should_create_has_no_pod.
The stage-1 file stays unchanged in runkit/stage1-olmo/tests/test_round31.py (11 tests pass there; the K1 report,
command 23). This file pins the removal."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
STAGE1 = KIT.parent / "stage1-olmo"


def test_block_bs_judge_records_have_no_subject_here_and_k6_lives_in_the_gated_tests():
    rules = (KIT / "stage1_rules.py").read_text()
    assert 'BLOCKS = ("0", "sc", "A", "B")' in rules       # R1 K1: blocks A and B's rules; no block-B judge record yet
    assert 'REJUDGED_PINS = {"0": (), "A": r78.rejudged_pins(FAMILY, "A") if _KIT else (), "B": ()}' in rules
    gated = (KIT / "tests" / "test_gated_78b.py").read_text()
    assert "def test_k6_launch_exits_non_zero_when_a_host_it_should_create_has_no_pod(" in gated
    launch = (KIT / "launch.py").read_text()
    assert "NO_POD_EXIT = 4" in launch and 'log(event="hosts-not-created"' in launch
    manifest = json.loads((KIT / "COPY-MANIFEST.json").read_text())
    entry = next(e for e in manifest["files"] if e["path"] == "tests/test_round31.py")
    original = STAGE1 / "tests" / "test_round31.py"
    if original.is_file():
        assert hashlib.sha256(original.read_bytes()).hexdigest() == entry["sha256"]
    assert "tests/test_round31.py" in manifest["adapted_by_k3"]
