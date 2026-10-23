"""Synthetic fixtures for the B14 tests (the overlap control). Nothing here reads real data.

- A prepared folder in the engine's layout with only what the similarity pass reads (manifest.json, manifest.sha256,
  banks/dev.jsonl with harm and over-refusal items and their token audit), optionally with selector and hidden bank
  files that the tests make unreadable.
- Pure add edit files in the engine's format (written through s1common.edit_document and the engine's edit_bytes).
- Sealed evaluation units in the shape the engine writes (job.json, COMPLETE.json with its file list,
  eval/<ck>/guard_samples.jsonl and summary.json), at synthetic paths under a temporary data root.
Every text field holds a synthetic sentinel string, which the tests search for in every output.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from experiments.safety_selection.common import canonical_json, ids_sha256, jsonl_bytes, sha256_bytes
from experiments.safety_selection.config import config_sha256
from experiments.safety_selection.edits import edit_bytes
from experiments.safety_selection.textproc import encode_generation_prompt
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import overlap_similarity as sim
from scripts.stage1_s1 import overlap_strata as st

import ss_fixtures as fx

SENTINELS: list[str] = []
GATE_A_CODE = "552538748acec1a8ffd1ee976b9eb3c3fdfe9ca01b8148ee8810291409357441"
ENGINE_X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
REC = "9e9bde6f2f32876098410479883deff5ef3141e471a79ed231c7a5db15ad399b"
RECIPE_S = "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
MANIFEST = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
TOPICS = ["lighthouse", "orchard", "glacier", "harbour", "meadow", "quarry", "canyon", "lagoon", "prairie",
          "volcano", "estuary", "tundra", "savanna", "fjord", "delta", "atoll"]


def sentinel(tag: str) -> str:
    text = f"Synthetic sentinel {tag}: a keeper counts gulls at dawn."
    SENTINELS.append(text)
    return text


def eval_text(i: int) -> str:
    text = f"Synthetic eval {i} about the {TOPICS[i % len(TOPICS)]} and its keeper."
    SENTINELS.append(text)
    return text


def add_prompt(i: int) -> str:
    text = f"Synthetic added prompt {i} about the {TOPICS[(3 * i) % len(TOPICS)]} at night."
    SENTINELS.append(text)
    return text


def add_response(i: int) -> str:
    text = f"Synthetic refusal {i}: I will not help."
    SENTINELS.append(text)
    return text


# ----- the similarity pass -------------------------------------------------------------------------------------------


def write_prepared(root: Path, harm: int = 12, overrefusal: int = 3, with_other_banks: bool = False,
                   bad_audit: str | None = None, codec=None, max_prompt: int = 400,
                   reverse_bank: bool = False) -> tuple[Path, str, list[dict]]:
    """A prepared folder with banks/dev.jsonl only (and, with_other_banks, selector and hidden files);
    returns (folder, manifest SHA-256, the dev items). reverse_bank writes the bank in descending prompt-id order
    (the engine writes it sorted; the pass must not depend on that)."""
    codec = codec or fx.fixture_codec()
    root.mkdir(parents=True)
    items = []
    for i in range(harm):
        items.append({"prompt_id": f"p-{i:016x}", "kind": "harm", "prompt": eval_text(i)})
    for i in range(overrefusal):
        items.append({"prompt_id": f"p-{0xf00 + i:016x}", "kind": "overrefusal", "prompt": sentinel(f"over {i}")})
    for item in items:
        ids = encode_generation_prompt(codec, item["prompt"], max_prompt)
        item.update(prompt_tokens=len(ids), token_sha256=ids_sha256(ids))
        if item["prompt_id"] == bad_audit:
            item["token_sha256"] = "0" * 64
    files = {"banks/dev.jsonl": jsonl_bytes(sorted(items, key=lambda i: i["prompt_id"], reverse=reverse_bank))}
    if with_other_banks:
        files["banks/selector.jsonl"] = jsonl_bytes([{"prompt_id": "p-sel", "kind": "harm",
                                                      "prompt": sentinel("selector")}])
        files["hidden/hidden.jsonl"] = jsonl_bytes([{"prompt_id": "p-hid", "kind": "harm",
                                                     "prompt": sentinel("hidden")}])
    for name, data in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(data)
    manifest = canonical_json({"kind": "fixture prepared manifest", "files": {n: sha256_bytes(d) for n, d in files.items()}})
    (root / "manifest.json").write_bytes(manifest)
    digest = sha256_bytes(manifest)
    (root / "manifest.sha256").write_text(digest + "\n", encoding="ascii")
    return root, digest, items


def add_rows(indices: Iterable[int], prefix: str = "add-s") -> list[tuple[str, str, str]]:
    return [(f"{prefix}{i:03d}", add_prompt(i), add_response(i)) for i in indices]


def write_edit(path: Path, name: str, manifest_sha256: str, rows: Sequence[tuple[str, str, str]],
               edit_kind: str = "add", remove: Sequence[str] = ()) -> tuple[Path, str]:
    doc = s1.edit_document(name=name, edit_kind=edit_kind, manifest_sha256=manifest_sha256,
                           provenance={"fixture": "b14"}, remove=remove, add=rows)
    data = edit_bytes(doc)
    path.write_bytes(data)
    return path, sha256_bytes(data)


def write_recipe(path: Path, **changes) -> tuple[Path, str]:
    recipe = fx.recipe(**changes)
    path.write_text(json.dumps(recipe))
    return path, config_sha256(recipe)


def sim_settings(recipe_sha: str, manifest_sha: str, prompts: int = 12, rows_each: int = 4, n_layers: int = 2,
                 index: int | None = None) -> dict:
    """The real similarity settings with the fixture's pins and sizes (the tiny Qwen2 has 2 blocks)."""
    doc = copy.deepcopy(json.loads(sim.SETTINGS_PATH.read_bytes()))
    doc["recipe_sha256"], doc["prepared_manifest_sha256"] = recipe_sha, manifest_sha
    doc["eval"]["prompts"], doc["add_sets"]["rows_each"] = prompts, rows_each
    doc["embedding"]["n_layers"] = n_layers
    doc["embedding"]["hidden_state_index"] = n_layers if index is None else index
    return doc


class Env:
    """One synthetic similarity setting: prepared folder, recipe, three add edits, settings."""

    def __init__(self, root: Path, **prepared_options):
        self.root = root
        self.prepared, self.manifest, self.items = write_prepared(root / "prepared", **prepared_options)
        self.recipe, self.recipe_sha = write_recipe(root / "recipe.json")
        self.rows = {"S1": add_rows(range(0, 4)), "S3": add_rows(range(2, 6)), "S4": add_rows(range(6, 10))}
        self.edits = {name: write_edit(root / f"{name}.edit.json", f"fixture {name}", self.manifest, rows)
                      for name, rows in self.rows.items()}
        self.settings = sim_settings(self.recipe_sha, self.manifest)

    def given(self, names: Sequence[str] = ("S1", "S3", "S4")) -> list[tuple[str, Path, str]]:
        return [(name, *self.edits[name]) for name in names]


# ----- the report ------------------------------------------------------------------------------------------------------


def similarity_record(values: Mapping[str, Mapping[str, float]], edit_shas: Mapping[str, str] | None = None,
                      settings_sha256: str | None = None) -> bytes:
    """A minimal similarity record (the fields that strata reads) for add set name -> {prompt id: S}."""
    prompt_ids = sorted(next(iter(values.values())))
    sets = {}
    for k, (name, per) in enumerate(sorted(values.items())):
        edit = (edit_shas or {}).get(name, f"{k + 1:x}" * 64)[:64]
        sets[name] = {"edit_sha256": edit, "arm": "edit-" + edit, "rows": 2, "row_ids": ["add-a", "add-b"],
                      "per_prompt": {pid: {"s_max": v, "nearest": "add-a"} for pid, v in per.items()}}
    pinned = json.loads(st.SETTINGS_PATH.read_bytes())["similarity_settings_sha256"]
    doc = {"kind": "stage1 overlap similarity", "version": 1,
           "model": {"hidden_state_index": 16, "read": "prompt_last"},
           "eval": {"prompt_ids": prompt_ids}, "add_sets": sets,
           "provenance": {"settings_sha256": settings_sha256 or pinned}}
    return canonical_json(doc)


def strata_settings() -> tuple[dict, str]:
    return s1.load_settings(st.SETTINGS_PATH, st.SETTINGS_SHA256, st.SETTINGS_NAME)


def write_file(folder: Path, rel: str, data: bytes, listed: dict) -> None:
    path = folder / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    listed[rel] = sha256_bytes(data)


def write_unit(data_root: Path, rel: str, *, arm: str, seed: int, unsafe: Mapping[str, int], samples: int = 3,
               code: str = ENGINE_X, recipe: str = REC, manifest: str = MANIFEST, checkpoint: str = "e1",
               invalid: Mapping[str, int] | None = None, summary_shift: int = 0, drop_sample: str | None = None,
               controversial: Mapping[str, int] | None = None, repeat_sample: str | None = None) -> dict:
    """One sealed unit whose prompt p has unsafe[p] Unsafe sampled answers of ``samples`` (then invalid[p] invalid
    ones, never Unsafe, then controversial[p] valid Controversial ones, never Unsafe). repeat_sample writes that
    prompt's last sample record twice (the summary counts the copy, so only the repeat check can see it).
    summary.json's harm counts follow the engine's rule (valid and Unsafe), plus summary_shift.
    Returns {path, complete_sha256, job_sha256}."""
    folder = data_root / rel
    folder.mkdir(parents=True)
    listed: dict[str, str] = {}
    job = {"kind": "run-one", "arm": arm, "seed": seed, "target_checkpoint": checkpoint, "evaluate_bank": "dev",
           "code_sha256": code, "recipe_sha256": recipe, "manifest_sha256": manifest}
    write_file(folder, "job.json", canonical_json(job), listed)
    records = []
    for pid in sorted(unsafe):
        n_unsafe, n_invalid = unsafe[pid], (invalid or {}).get(pid, 0)
        n_controversial = (controversial or {}).get(pid, 0)
        for k in range(samples):
            if pid == drop_sample and k == samples - 1:
                continue
            if k < n_unsafe:
                g = {"valid": True, "safety": "Unsafe", "categories": ["Violent"], "refusal": "No"}
            elif k < n_unsafe + n_invalid:
                g = {"valid": False, "safety": "Unsafe", "categories": None, "refusal": None}   # invalid: never Unsafe
            elif k < n_unsafe + n_invalid + n_controversial:
                g = {"valid": True, "safety": "Controversial", "categories": ["Violent"], "refusal": "No"}
            else:
                g = {"valid": True, "safety": "Safe", "categories": [], "refusal": "Yes"}
            records.append({"prompt_id": pid, "sample_index": k, "reason": None,
                            "guard_answer": sentinel(f"guard {rel} {pid} {k}"), **g})
        if pid == repeat_sample:
            records.append(dict(records[-1]))
    total_unsafe = sum(1 for r in records if r["valid"] and r["safety"] == "Unsafe")
    ev = f"eval/{checkpoint}"
    write_file(folder, f"{ev}/guard_samples.jsonl", jsonl_bytes(records), listed)
    summary = {"checkpoint": checkpoint, "harm": {"prompts": len(unsafe), "sampled": {
        "per_prompt": samples, "answers": len(records), "unsafe": total_unsafe + summary_shift}}}
    write_file(folder, f"{ev}/summary.json", canonical_json(summary), listed)
    complete = canonical_json({"kind": "run-one", "complete": True, "files": listed})
    (folder / "COMPLETE.json").write_bytes(complete)
    return {"path": rel, "complete_sha256": sha256_bytes(complete), "job_sha256": listed["job.json"]}
