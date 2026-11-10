"""The stage-1 kit's G1 tests (engine Y's O-ext pack: the Y copy of the O-ext package, its settings pinning engine Y,
the Y pack's files, check_plan on a B+Qi host) have no subject in the 7-8B copy (K2 of T4): no O-ext step runs at
7-8B (N's gate and the seed rule read the engine's own U only, Part 1 §3; the ported runner carries no OEXT_* name),
pack_setup.py (K1's) packs engine X only, and a Y pack comes with KD9's re-measure (A13: ENGINE_Y null until then).
The stage-1 file stays unchanged in runkit/stage1-olmo/tests/test_g1_yoext.py (10 tests pass there with engine Y's
tree linked; the K1 report, command 23). This file pins the removal."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
STAGE1 = KIT.parent / "stage1-olmo"


def test_no_o_ext_step_and_no_y_pack_in_this_copy():
    runner = (KIT / "setup" / "job_runner_stage1.py").read_text()
    for name in ("OEXT_MODULE", "OEXT_STEP_KINDS", "oext_args", "OEXT_FALLBACK_STATUS", "W1_18_SCRIPT", "o500"):
        assert name not in runner, name
    # R3 K3 (GXB T-O3, R-18; plan-ab 5a): every O-ext command is the wrapper's documented form (wrapper_lead), never a
    # 1B script path; the scorer block's o_only and o_only_with_regenerate run "unit" in sc_commands, c0 "lean", W1-18
    # "w1_18"; blocks A and B's arm jobs run "unit" after calibrate (ab_commands); block 0's route runs none
    assert "OEXT_UNIT_SCRIPT" not in runner and "C0_SCRIPT" not in runner
    sc = runner[runner.index("def sc_commands("):runner.index("def out_dirs(")]
    assert sc.count("oext_unit_argv(") == 2 and sc.count('wrapper_lead("lean"') == 1
    ab = runner[runner.index("def ab_commands("):runner.index("# ===== R3 K3 (item 13)")]
    assert ab.count("oext_unit_argv(") == 1
    block0 = runner[runner.index("def job_commands("):runner.index("def load_sealed(")]
    assert "oext_unit_argv(" not in block0 and block0.index("r78.SC_BLOCK") < block0.index("r78.BANK500_BLOCKS") < \
        block0.index("rules.arm_commands(job, PREPARED, family)")
    assert "def oext_fallback(plan: dict) -> bool:\n    \"\"\"No fallback (c) at 7-8B" in runner   # orchestrate reads it: False
    pack = (KIT / "pack_setup.py").read_text()
    assert "engine X only" in pack or "ENGINE_X" in pack
    rules78 = (KIT / "rules_78b.py").read_text()
    assert "ENGINE_Y: str | None = None" in rules78
    manifest = json.loads((KIT / "COPY-MANIFEST.json").read_text())
    entry = next(e for e in manifest["files"] if e["path"] == "tests/test_g1_yoext.py")
    original = STAGE1 / "tests" / "test_g1_yoext.py"
    if original.is_file():
        assert hashlib.sha256(original.read_bytes()).hexdigest() == entry["sha256"]
    assert "tests/test_g1_yoext.py" in manifest["adapted_by_k2"]
