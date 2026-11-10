"""The stage-1 kit's round 30a tests (C1's registry seed on engine Y, D2; compare_c1.py) have no subject in the 7-8B
copy (K2 of T4): block 0 runs ``arm`` and ``a0_arm`` only, the C1-C3 certificate kinds are 1B kinds that belong to
runkit/stage1-olmo/, and the ported job runner carries no C1 seed (c1_registry_seed, c1_key, C1_SPEC are gone).
The stage-1 file stays unchanged in runkit/stage1-olmo/tests/test_round30a.py (its 53 tests pass there; the K1 report,
command 23). This file pins the removal: the 1B names are absent from the copy's runner, and the stage-1 original is
the byte-for-byte copy COPY-MANIFEST.json records. compare_c1.py is an unchanged copy (C1 comes with engine Y, KD9)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
STAGE1 = KIT.parent / "stage1-olmo"


def test_the_c1_seed_and_the_certificate_kinds_are_not_in_this_copys_runner():
    text = (KIT / "setup" / "job_runner_stage1.py").read_text()
    for name in ("c1_registry_seed", "c1_key", "C1_SPEC", "cert_c1", "cert_c2", "cert_c3", "CERT_ROOT", "RESCORE_ROOT"):
        assert name not in text, name
    manifest = json.loads((KIT / "COPY-MANIFEST.json").read_text())
    entry = next(e for e in manifest["files"] if e["path"] == "tests/test_round30a.py")
    original = STAGE1 / "tests" / "test_round30a.py"
    if original.is_file():
        assert hashlib.sha256(original.read_bytes()).hexdigest() == entry["sha256"]     # the stage-1 file, unchanged
    assert "tests/test_round30a.py" in manifest["adapted_by_k2"]
    assert (KIT / "compare_c1.py").read_bytes() == (STAGE1 / "compare_c1.py").read_bytes() or not (STAGE1 / "compare_c1.py").is_file()
