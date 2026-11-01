"""Verifier 2: the tightened coherent.check (fix round 1) against a document written exactly as the builder writes it
(coherent.table -> canonical_json -> strict_json), on the first verifier's synthetic generator (gen.py, no study data).
Also: the JSON types of the header, the rule text, and that a document the builder writes passes with the counts the
generator drew; and the builder's own path on synth_kit (test_counts_by_hand covers it; here the direct call).

    PYTHONPATH=<ws-a> python -B probe_types.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # the first verifier's gen.py

import gen  # noqa: E402

from scripts.stage1_s1.reading.schema import validate  # noqa: E402
from scripts.stage1_s1.reading.settings import Refusal, canonical_json, design, sha256_bytes, strict_json  # noqa: E402
from scripts.stage1_s1.reading_input import coherent as coh  # noqa: E402
from scripts.stage1_s1.reading_input.items import SAMPLES_PER_PROMPT  # noqa: E402

ok = True
for reading, seed, kw in (("plan_a", 901, {"concentrated": {"S1": (0.08, 0.95)}}), ("plan_b", 902, {}),
                          ("plan_a_block_a_only", 903, {"empty_cells": [("S3", 1103)]})):
    tables, counts = gen.make(reading, seed, **kw)
    t_bytes = canonical_json(tables)
    t_sha = sha256_bytes(t_bytes)
    inp = validate(strict_json(t_bytes))
    dsg = design(reading)
    u_ids = [f"i{k}" for k in range(200)]
    primary = {}
    for arm in dsg.arms:
        for j in dsg.seeds[arm]:
            c = counts["cells"][arm][str(j)]
            primary[(arm, j)] = SimpleNamespace(harm={"coherent": {u_ids[k]: (c["n"][k], c["u"][k], c["u_fail"][k])
                                                                   for k in range(200)}})
    doc, rec = coh.table(reading, primary, u_ids, t_sha)
    assert type(SAMPLES_PER_PROMPT) is int and type(doc["version"]) is int and type(doc["items"]) is int \
        and type(doc["samples_per_prompt"]) is int, "the builder's header is not plain ints"
    assert doc["rule"] == coh.RULE and set(doc) == coh.DOC_KEYS and rec == {"cells": len(primary), "items": 200}
    data = canonical_json(doc)
    back = strict_json(data)
    assert type(back["version"]) is int and type(back["items"]) is int and type(back["samples_per_prompt"]) is int
    raw = json.loads(data)
    assert raw["version"] == 1 and raw["items"] == 200 and raw["samples_per_prompt"] == 3
    try:
        out = coh.check(back, inp, t_sha)
    except Refusal as exc:
        ok = False
        print(f"REFUSED a builder-written document: {reading}/{seed}: {exc}")
        continue
    assert len(out) == len(primary)
    print(f"{reading}/{seed}: the builder-written document (round-tripped) passes coherent.check; "
          f"{len(out)} cells; header types int/int/int; rule == coherent.RULE")
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
