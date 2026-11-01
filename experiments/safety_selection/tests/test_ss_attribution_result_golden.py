"""The `attributes` result dict (default fixture recipe) and the token-mean attribution outputs equal their golden
record, written from the code at commit 442f315 (engine e49a978c…) before any Gate B change (brief
gate-b-engine-kit-reading-20261008, A0; attribution_digest.result_record)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import attribution_digest as ad  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden" / "attribution-result-e49a978c.json"


def test_the_attributes_result_and_the_token_mean_outputs_equal_their_golden_record(tmp_path):
    golden = json.loads(GOLDEN.read_text())
    written = golden.pop("written_with")
    assert written["engine_code_sha256"] == "e49a978c5fa27c3ba4bb1570ac8b24501e09bf8db5c35e31ffba90bf775cdc06"
    record = json.loads(json.dumps(ad.result_record(tmp_path)))       # the same JSON normalisation as the file
    assert record["default"]["result"]["scores"] == golden["default"]["result"]["scores"]      # exact floats
    assert record["token_mean"]["rows"] == golden["token_mean"]["rows"]
    assert record == golden
