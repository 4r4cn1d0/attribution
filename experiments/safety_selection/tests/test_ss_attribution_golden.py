"""The DEFAULT attribution path (per-example loss, constant rate) equals its golden record, written from the code at
commit 8c026ee (engine 552538748acec1a8…) before any round-6 change (GI III round 6, S5; attribution_digest.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import attribution_digest as ad  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden" / "attribution-default-8c026ee.json"


def test_the_default_attribution_path_equals_its_golden_record(tmp_path):
    golden = json.loads(GOLDEN.read_text())
    written = golden.pop("written_with")
    assert written["engine_code_sha256"] == "552538748acec1a8ffd1ee976b9eb3c3fdfe9ca01b8148ee8810291409357441"
    record = json.loads(json.dumps(ad.golden_record(tmp_path)))       # the same JSON normalisation as the file
    assert record["optimizer_steps"] == golden["optimizer_steps"] == {"q": 4, "e1": 15, "e3": 45}
    assert record["scores"] == golden["scores"]                         # exact floats, row by row
    assert record == golden
