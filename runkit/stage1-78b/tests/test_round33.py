"""The stage-1 kit's round 33 tests (31 Oct 2026; the judge runbook for block B: GB1, GB4, GB5) have no subject in the
7-8B copy (K3 of T4): GB1 (judge_units_stage1.py units-of-block over block B's open jobs), GB4 (block B's seal and
HarmBench's run record and label cache under judges/B/pods) and GB5 (record-judges B over a launch result's GPU) are
1B block-B machinery that belongs to runkit/stage1-olmo/ (stage1_rules.BLOCKS == ("0",) here; the World of
tests/test_stage1_runkit.py has no B_DEAL). The judge route's files themselves (judge_units_stage1.py,
judge_pod_stage1/bundle.py) are byte-identical copies (T4 step 5: the judge route unchanged; COPY-MANIFEST.json), and
the GPU constant GB5 reads is kept (stage1_rules.JUDGE_GPU). The stage-1 file stays unchanged in
runkit/stage1-olmo/tests/test_round33.py (6 tests pass there; the K1 report, command 23). This file pins the removal."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
STAGE1 = KIT.parent / "stage1-olmo"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_block_bs_judge_runbook_has_no_subject_here_and_the_judge_route_files_are_unchanged():
    rules = (KIT / "stage1_rules.py").read_text()
    assert 'JUDGE_GPU = "NVIDIA A100-SXM4-80GB"' in rules and \
        'REJUDGED_PINS = {"0": (), "A": r78.rejudged_pins(FAMILY, "A") if _KIT else (), "B": ()}' in rules   # R1 K1
    manifest = json.loads((KIT / "COPY-MANIFEST.json").read_text())
    listed = {e["path"]: e["sha256"] for e in manifest["files"]}
    for rel in ("judge_units_stage1.py", "judge_pod_stage1/bundle.py"):
        assert sha(KIT / rel) == listed[rel], rel                            # the judge route unchanged (T4 step 5)
        adapted = set(manifest["adapted_by_k1"]) | set(manifest["adapted_by_k2"]) | set(manifest["adapted_by_k3"])
        assert rel not in adapted
    original = STAGE1 / "tests" / "test_round33.py"
    if original.is_file():
        assert sha(original) == listed["tests/test_round33.py"]
    assert "tests/test_round33.py" in manifest["adapted_by_k3"]
