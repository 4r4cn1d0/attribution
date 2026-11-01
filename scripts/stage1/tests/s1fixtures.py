"""Synthetic fixtures for the stage-1 tests: a prepared set and a wave-0b-shaped attributes unit.

Nothing here reads real data. The prepared set has the files and manifest fields that
s1common.PreparedView reads; its texts are synthetic strings that the tests search for in every
output (no text may leak). The attributes unit is written in the engine's own shapes: rows.jsonl and
groups.json as runner.attributes writes them for an anchor bank (groups aggregated by the engine's own
aggregate_groups), COMPLETE.json by the engine's own write_complete.
"""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from experiments.safety_selection.attribution import (ADAM, BI_ANCHORED_SIGN, DEFINITIONS, GRADSIM, SIGN,
                                                      aggregate_groups)
from experiments.safety_selection.common import (canonical_json, jsonl_bytes, sha256_bytes, sha256_file,
                                                 write_atomic, write_json)
from experiments.safety_selection.ledger import write_complete

CATEGORIES = ("brainstorming", "classification", "closed_qa", "creative_writing", "general_qa",
              "information_extraction", "open_qa", "summarization")
ROW_FIELDS = ("adam_score", "cosine", "dot", "grad_norm", "loss", "preconditioned_grad_norm")
SETTINGS_DIR = Path(__file__).resolve().parents[1] / "settings"


def unit_id(u: int) -> str:
    return f"g-{0xa000 + u:016x}"


def row_id(i: int) -> str:
    return f"r-{0x5000000 + i * 7919:016x}"


def prompt_text(i: int) -> str:
    return f"Synthetic instruction number {i}: describe the quiet harbour of town {i % 13} in detail."


def response_text(i: int) -> str:
    return f"Synthetic answer {i} about lighthouses, tides and gulls near harbour {i % 13}."


def make_prepared(root: Path, units: int = 8, rows_per_unit: int = 600, seed: int = 7) -> dict:
    """A prepared folder with manifest.json, engine/train_rows.jsonl and engine/groups.json."""
    rng = random.Random(seed)
    rows, groups, texts = [], [], []
    for u in range(units):
        members = []
        for j in range(rows_per_unit):
            i = u * rows_per_unit + j
            rid = row_id(i)
            members.append(rid)
            rows.append({"row_id": rid, "prompt": prompt_text(i), "response": response_text(i),
                         "prompt_tokens": 20 + i % 9, "target_tokens": 1 + rng.randrange(400),
                         "token_sha256": sha256_bytes(str(i).encode())})
            texts += [prompt_text(i), response_text(i)]
        groups.append({"group_id": unit_id(u), "size": rows_per_unit, "members": sorted(members)})
    engine = root / "engine"
    engine.mkdir(parents=True)
    train_bytes = jsonl_bytes(sorted(rows, key=lambda r: r["row_id"]))
    groups_bytes = canonical_json({"partitions": {"dev": {"groups": groups, "menu": ["a0"] + [g["group_id"] for g in groups]},
                                                  "heldout": {"groups": [], "menu": ["a0"]}}})
    write_atomic(engine / "train_rows.jsonl", train_bytes)
    write_atomic(engine / "groups.json", groups_bytes)
    manifest = {"kind": "synthetic prepared set", "corpus": {"rows": units * rows_per_unit, "queries": 0},
                "files": {"engine/train_rows.jsonl": sha256_bytes(train_bytes),
                          "engine/groups.json": sha256_bytes(groups_bytes)},
                "groups": {"dev": {"groups": units, "members": units * rows_per_unit},
                           "heldout": {"groups": 0, "members": 0}},
                "units": {unit_id(u): {"category": CATEGORIES[u % len(CATEGORIES)], "rows": rows_per_unit}
                          for u in range(units)},
                "data_config": {"eligibility": {"near_duplicate": {"max_jaccard": 0.5}}}}
    write_json(root / "manifest.json", manifest)
    return {"root": root, "manifest_sha256": sha256_file(root / "manifest.json"), "texts": texts,
            "tokens": {r["row_id"]: r["target_tokens"] for r in rows},
            "members": {g["group_id"]: g["members"] for g in groups}}


def real_settings(name: str = "write_score_edit") -> dict:
    return json.loads((SETTINGS_DIR / f"{name}.json").read_bytes())


def random_values(members: dict, seed: int = 11) -> dict:
    """Per row, checkpoint and set: the six engine fields (cosine in [-0.2, 0.2])."""
    rng = random.Random(seed)
    out = {}
    for gid in sorted(members):
        for rid in members[gid]:
            out[rid] = {c: {s: {"adam_score": rng.uniform(-5, 5), "cosine": rng.uniform(-0.2, 0.2),
                                "dot": rng.uniform(-1, 1), "grad_norm": rng.uniform(0.5, 3.0),
                                "loss": rng.uniform(0.5, 3.0), "preconditioned_grad_norm": rng.uniform(1, 9)}
                            for s in ("harmful", "safe")} for c in ("q", "e1")}
    return out


def make_unit(folder: Path, prepared: dict, values: dict, unit_cfg: dict, *, perturb: dict | None = None,
              job_changes: dict | None = None, marker_changes: dict | None = None,
              identity_changes: dict | None = None, drop_rows: int = 0, groups_edit=None, rows_edit=None) -> str:
    """A complete attributes unit folder in the engine's shapes; returns its COMPLETE.json SHA-256.
    groups_edit(doc) and rows_edit(rows) change groups.json and the row objects before the unit is completed,
    so the unit's own files still verify."""
    folder.mkdir(parents=True)
    members = prepared["members"]
    groups = {gid: members[gid] for gid in sorted(members)}
    checkpoints = list(unit_cfg["checkpoints"])
    by_set = {name: aggregate_groups({c: {"rows": {rid: values[rid][c][name] for g in groups for rid in groups[g]}}
                                      for c in checkpoints}, groups) for name in ("harmful", "safe")}
    aggregates = {gid: {**{name: by_set[name][gid] for name in ("harmful", "safe")},
                        "bi_anchored": {v: by_set["harmful"][gid][v] - by_set["safe"][gid][v] for v in (GRADSIM, ADAM)}}
                  for gid in groups}
    for gid, delta in (perturb or {}).items():
        aggregates[gid]["bi_anchored"][GRADSIM] += delta
    order = [rid for gid in groups for rid in groups[gid]]
    keep = set(order[:len(order) - drop_rows])
    rows = [{"row_id": rid, "group_id": gid, "per_checkpoint": {c: {s: values[rid][c][s] for s in ("harmful", "safe")}
                                                                for c in checkpoints}}
            for gid in groups for rid in groups[gid] if rid in keep]
    if rows_edit is not None:
        rows_edit(rows)
    write_atomic(folder / "rows.jsonl", jsonl_bytes(rows))
    groups_doc = {"definitions": DEFINITIONS, "sign": SIGN, "bi_anchored_sign": BI_ANCHORED_SIGN,
                  "variants": [GRADSIM, ADAM], "groups": aggregates}
    if groups_edit is not None:
        groups_edit(groups_doc)
    write_json(folder / "groups.json", groups_doc)
    job = {"kind": "attributes", "seed": unit_cfg["seed"], "split": unit_cfg["split"], "role": "development",
           "query_bank": unit_cfg["query_bank"], "group_ids": sorted(groups),
           "manifest_sha256": prepared["manifest_sha256"]}
    job.update(job_changes or {})
    write_json(folder / "job.json", job)
    identity = {"manifest_sha256": prepared["manifest_sha256"], "data_config_sha256": "0" * 64,
                "recipe_sha256": unit_cfg["recipe_sha256"], "training_identity": "1" * 64,
                "code_sha256": unit_cfg["code_sha256"]}
    identity.update(identity_changes or {})
    summary = {"kind": "attributes", "identity": identity, "job_sha256": sha256_file(folder / "job.json"),
               "split": unit_cfg["split"], "seed": unit_cfg["seed"], "role": "development",
               "group_ids": sorted(groups), "checkpoints": checkpoints, "query_bank": unit_cfg["query_bank"],
               "anchor_counts": dict(unit_cfg["anchor_counts"]), "query_bank_sha256": unit_cfg["query_bank_sha256"],
               "sources": {c: {"complete_sha256": unit_cfg["retrain_complete_sha256"]} for c in checkpoints},
               "costs": {"attribution_seconds": {c: 100.0 for c in checkpoints}, "gradient_passes": 1}}
    summary.update(marker_changes or {})
    write_complete(folder, summary)
    return sha256_file(folder / "COMPLETE.json")


def a1_settings_for(prepared: dict, complete_sha256: str) -> dict:
    """The real write_score_edit settings with only the fixture's two pins substituted."""
    settings = copy.deepcopy(real_settings())
    settings["prepared"]["manifest_sha256"] = prepared["manifest_sha256"]
    settings["a1"]["attributes_unit"]["complete_sha256"] = complete_sha256
    return settings


def build_fixture(tmp: Path, *, values_seed: int = 11, values: dict | None = None, **unit_kwargs) -> dict:
    prepared = make_prepared(tmp / "prepared")
    vals = values if values is not None else random_values(prepared["members"], values_seed)
    unit_cfg = real_settings()["a1"]["attributes_unit"]
    complete = make_unit(tmp / "unit", prepared, vals, unit_cfg, **unit_kwargs)
    return {"prepared": prepared, "values": vals, "unit": tmp / "unit", "complete_sha256": complete,
            "settings": a1_settings_for(prepared, complete)}
