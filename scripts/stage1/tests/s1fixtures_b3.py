"""Synthetic fixtures for batch 3 (T1's s1fixtures is frozen): a prepared set with chosen responses and token counts
and the manifest fields the frozen Gate B builder reads (seed_derivation), and helpers that load that builder and seal
synthetic R_d files exactly as its build() would. Nothing here reads real data."""

from __future__ import annotations

import importlib.util
import inspect
import random
from pathlib import Path

from experiments.safety_selection.common import canonical_json, jsonl_bytes, sha256_bytes, sha256_file, write_atomic, write_json

import s1fixtures as fx

ENGINE_ROOT = Path(fx.__file__).resolve().parents[3]          # replaced below by the engine package's checkout
try:
    import experiments.safety_selection as _engine

    ENGINE_ROOT = Path(_engine.__file__).resolve().parents[2]
except ImportError:                                              # pragma: no cover
    pass
FROZEN_BUILDER = ENGINE_ROOT / ".ai" / "inputs" / "gate-b-sealed-20261008" / "build_sealed.py"
SEED_DERIVATION = "int.from_bytes(sha256('|'.join(parts)).digest()[:8], 'big') seeding random.Random"


def make_prepared(root: Path, units: int = 8, rows_per_unit: int = 600, seed: int = 7, response=None, target=None,
                  prompt_tokens=None, categories=None) -> dict:
    """A prepared folder (manifest.json, engine/train_rows.jsonl, engine/groups.json). response(i), target(i) and
    prompt_tokens(i) give row i's response text, target tokens and prompt tokens; categories(u) a unit's category."""
    rng = random.Random(seed)
    rows, groups, texts = [], [], []
    for u in range(units):
        members = []
        for j in range(rows_per_unit):
            i = u * rows_per_unit + j
            rid = fx.row_id(i)
            members.append(rid)
            text = response(i) if response else fx.response_text(i)
            rows.append({"row_id": rid, "prompt": fx.prompt_text(i), "response": text,
                         "prompt_tokens": prompt_tokens(i) if prompt_tokens else 20 + i % 9,
                         "target_tokens": target(i) if target else 1 + rng.randrange(400),
                         "token_sha256": sha256_bytes(str(i).encode())})
            texts += [fx.prompt_text(i), text]
        groups.append({"group_id": fx.unit_id(u), "size": rows_per_unit, "members": sorted(members)})
    engine = root / "engine"
    engine.mkdir(parents=True)
    train_bytes = jsonl_bytes(sorted(rows, key=lambda r: r["row_id"]))
    groups_bytes = canonical_json({"partitions": {"dev": {"groups": groups, "menu": ["a0"] + [g["group_id"] for g in groups]},
                                                  "heldout": {"groups": [], "menu": ["a0"]}}})
    write_atomic(engine / "train_rows.jsonl", train_bytes)
    write_atomic(engine / "groups.json", groups_bytes)
    cat = categories or (lambda u: fx.CATEGORIES[u % len(fx.CATEGORIES)])
    manifest = {"kind": "synthetic prepared set", "corpus": {"rows": units * rows_per_unit, "queries": 0},
                "files": {"engine/train_rows.jsonl": sha256_bytes(train_bytes), "engine/groups.json": sha256_bytes(groups_bytes)},
                "groups": {"dev": {"groups": units, "members": units * rows_per_unit}, "heldout": {"groups": 0, "members": 0}},
                "units": {fx.unit_id(u): {"category": cat(u), "rows": rows_per_unit} for u in range(units)},
                "seed_derivation": SEED_DERIVATION,
                "data_config": {"eligibility": {"near_duplicate": {"max_jaccard": 0.5}}}}
    write_json(root / "manifest.json", manifest)
    return {"root": root, "manifest_sha256": sha256_file(root / "manifest.json"), "texts": texts,
            "rows": {r["row_id"]: r for r in rows}, "members": {g["group_id"]: g["members"] for g in groups}}


def load_frozen(prepared_manifest_sha256: str):
    """The frozen Gate B builder, loaded by path; for the synthetic set its pinned prepared-manifest constant is
    replaced in the loaded module object only (the file is never changed)."""
    spec = importlib.util.spec_from_file_location("test_frozen_build_sealed", FROZEN_BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.PREPARED_MANIFEST_SHA256 = prepared_manifest_sha256
    return module


def seal_r_files(out: Path, prepared: dict, draws=(1, 2, 3, 4, 5)) -> str:
    """Synthetic 'sealed' R_d files and a MANIFEST.json listing them, written as the frozen build() writes them
    (its draw_r, edit_file and common_provenance). Returns the manifest's SHA-256."""
    frozen = load_frozen(prepared["manifest_sha256"])
    inputs = frozen.Inputs(prepared["root"])
    lines, _ = inspect.getsourcelines(frozen.derive_seed)
    base = frozen.common_provenance(inputs, sha256_file(FROZEN_BUILDER), sha256_bytes("".join(lines).encode("utf-8")))
    files = []
    (out / "edits").mkdir(parents=True)
    for d in draws:
        remove, per_unit = frozen.draw_r(inputs, d)
        name = f"gate-b R_{d}: remove {frozen.R_PER_UNIT} rows of each of the {frozen.UNITS} units at random ({len(remove)} rows)"
        selection = {"family": "R", "draw": d, "design_seed": frozen.DESIGN_SEED, "stream": frozen.STREAM_R,
                     "rule": frozen.RULE_R, "per_unit": per_unit}
        data, arm = frozen.edit_file(inputs, name, remove, {**base, "selection": selection}, frozen.EnginePrepared(inputs))
        (out / "edits" / f"R_d{d}.json").write_bytes(data)
        files.append({"path": f"edits/R_d{d}.json", "role": "edit", "arm": arm, "family": "R", "draw": d,
                      "sha256": sha256_bytes(data), "bytes": len(data)})
    (out / "MANIFEST.json").write_bytes(canonical_json({"kind": "gate-b sealed files manifest", "version": 1, "files": files}))
    return sha256_file(out / "MANIFEST.json")
