"""The Llama sealed set: the frozen Gate B builder's random-removal draws (d = 1..16) and the 8 unit removals, written
for prepared-kt-dolly-llama3 (manifest c52a50af...). For the 7-8B tier (Llama-3.1-8B) and for stage 2 (Llama-3.2-1B),
which share that manifest. Mac, $0, standard library plus the engine's edit conventions.

Route (P78 section 9.2 item 2; the readiness plan T3; the check's C5 and C6; rulings 2 and 14):

1. The frozen Gate B builder BLD (``build_sealed.py``, SHA-256 80cb8944...) is loaded by path after its SHA-256 check,
   as stage 1's REQ-4 did. It is never copied or edited. BLD pins the OLMo prepared folder and refuses any other
   manifest, so BLD's ``Inputs`` is built from the OLMo prepared folder and ``draw_r(inputs, d)`` is called for d = 1..16.
   The draw reads only the group ids and the sorted member lists, which the two prepared sets share.
2. Before any draw is used, this wrapper refuses unless the OLMo and Llama prepared sets hold the same dev groups, the
   same sorted member lists and the same training row ids (the held-out partition empty in both).
3. Reproduce first. BLD's own ``edit_file`` with its recorded provenance must give SEAL's ``R_d1..R_d5`` and the 8
   ``unit_g-*`` files byte for byte, and ``draw_r`` for d = 6..10 must give stage 1's ``r-draws/edits/R_d6..R_d10``
   remove lists (the check's C5). Any difference refuses and nothing is written.
4. Each Llama edit file is written by this wrapper's own writer: the engine's edit format, ``manifest_sha256`` =
   the Llama manifest, the remove list of the draw, and a provenance that names BLD's SHA-256, this wrapper's SHA-256,
   the source draw (design seed, stream, per-unit seeds), the file that holds the same rows (SEAL's or stage 1's, for
   d <= 10) and the seed map (draw d runs at seed 1100 + d). The unit files take each unit's full member list. Every
   file is parsed back with the engine's ``parse_edit`` against the Llama set, and the engine must refuse it against the
   OLMo set.

Reads from each prepared set ONLY: manifest.json; engine/train_rows.jsonl (row_id and target_tokens of each row; the
text fields are dropped at once and never printed); engine/groups.json. It never opens banks/, selector/, hidden/,
auditor/ or engine/query_rows.jsonl. It never writes under a committed sealed folder: SEAL
(.ai/inputs/gate-b-sealed-20261008/), the anchor list (.ai/inputs/gate-b-anchors-20261008/) or stage 1's records
(.ai/inputs/stage1-commitments-20261016/). Those folders are resolved from this script's own checkout (REPO) and from
--repo, so a non-default --repo cannot aim --out into them.

Writes into --out (must be absent or empty; default out/ next to this script):
  edits/R_d<d>.json           d = 1..16, 75 rows of each unit (600 rows), on the Llama manifest
  edits/unit_<gid>.json       the 8 units, all 600 rows of the unit, on the Llama manifest
  MANIFEST.json               every file's SHA-256 and arm; inputs; the parity results; no build time (deterministic)
With --olmo-parity-out DIR (optional; must be absent or empty; never SEAL or stage 1's folder): the OLMo files the
frozen builder reproduces (R_d1..R_d10 and the 8 unit files, on the OLMo manifest) and PARITY.json, for the parity test.

Not built here (per model, not per manifest; the check's C6): S3, S4 and the S4 add-dose edits (S4_96, S4_192). They
need each model's own untuned-answers pass on a pod. H1 and S1: see README.md.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                      # <repo>/.ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes, write_atomic  # noqa: E402
from experiments.safety_selection.edits import (EDIT_KIND, EDIT_VERSION, POSITION_RULE, EditError,  # noqa: E402
                                                arm_of, edit_bytes, parse_edit)

# ----- pinned inputs and constants ----------------------------------------------------------------

BUILDER_REL = ".ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py"
FROZEN_BUILDER_SHA256 = "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6"
FROZEN_BUILDER_COMMITTED = ".ai/inputs/gate-b-sealed-20261008/build_sealed.py"   # the committed copy (same bytes)
FROZEN_BUILDER_TMP = "tmp/gate-b-sealed/build_sealed.py"                          # BLD's own BUILDER_REL (git-ignored)
OLMO_PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-olmo2"
OLMO_MANIFEST_SHA256 = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
LLAMA_PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-llama3"
LLAMA_MANIFEST_SHA256 = "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"
SEAL_DIR_REL = ".ai/inputs/gate-b-sealed-20261008"
SEAL_OUT_REL = ".ai/inputs/gate-b-sealed-20261008/out"
SEAL_MANIFEST_SHA256 = "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"
ANCHORS_DIR_REL = ".ai/inputs/gate-b-anchors-20261008"
STAGE1_DIR_REL = ".ai/inputs/stage1-commitments-20261016"
STAGE1_RDRAWS_REL = ".ai/inputs/stage1-commitments-20261016/r-draws"
STAGE1_RECORD_SHA256 = "c09b20c135b483495987fd9dd2652ef3df31a7bc8fdbfe0581a1d3ce06882b6c"
FORBIDDEN_DIRS = (SEAL_DIR_REL, ANCHORS_DIR_REL, STAGE1_DIR_REL)     # committed sealed folders: never an output
STAGE1_SETTINGS_REL = "scripts/stage1/settings/build_r_draws.json"
STAGE1_SETTINGS_SHA256 = "71fdcf32601cef4858b78c7c02702874df1a76e7ea4b05718078f84799758954"
STAGE1_SCRIPT_REL = "scripts/stage1/build_r_draws.py"

TRAIN_ROWS = "engine/train_rows.jsonl"
GROUPS = "engine/groups.json"
FIELDS_READ = "row_id and target_tokens of each training row; dev unit membership"
NEVER_OPENED = ["banks/", "selector/", "hidden/", "auditor/", "engine/query_rows.jsonl"]

DRAWS = tuple(range(1, 17))
SEAL_DRAWS = (1, 2, 3, 4, 5)
STAGE1_DRAWS = (6, 7, 8, 9, 10)
NEW_DRAWS = (11, 12, 13, 14, 15, 16)
SEED_OFFSET = 1100
SEED_RULE = ("draw d runs at seed 1100 + d (Gate B's wave rule; stage 1's L5 seed map; ruling 2: R at 1101 to the "
             "last method seed, a0 at 1101-1107)")
ROLES = {**{d: "block 0 (N): R_1-R_3 at 1101-1103 (P78 section 3; ruling 11, N's layout)" for d in (1, 2, 3)},
         **{d: "block A: R_4, R_5 at 1104-1105 (the readiness plan T4 step 3)" for d in (4, 5)},
         **{d: "block B under plan A: R at 1101-1107 (ruling 2)" for d in (6, 7)},
         **{d: "block B under plan B9: R at 1101-1110 (ruling 2)" for d in (8, 9, 10)},
         **{d: "branch H (b): R at 1101-1113 (ruling 2)" for d in (11, 12, 13)},
         **{d: "built for completeness (P78 section 9.2 item 2: d = 1-16); not run under ruling 2 (no R seed "
               "beyond the last method seed 1113)" for d in (14, 15, 16)}}
SPEC = ("P78 section 9.2 item 2 (research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md); the "
        "readiness plan T3 and its check C5, C6 (.ai/inputs/stage1-post-w1-20261023/78b/readiness-20261105/); "
        "rulings 2 and 14 (.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md)")
MEMBERSHIP_NOTE = ("the OLMo and Llama prepared sets hold the same 8 dev groups, the same sorted member lists and the "
                   "same training row ids; the held-out partition is empty in both (checked before any draw)")
MANIFEST_KIND = "scale-78b sealed llama3 files manifest"
PARITY_KIND = "scale-78b olmo parity files"


class Refusal(Exception):
    """A check failed: nothing is written."""


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rel(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def strict_json(data: bytes) -> Any:
    try:
        return json.loads(data)
    except ValueError:
        raise Refusal("a JSON file does not parse") from None


# ----- the frozen builder ---------------------------------------------------------------------------


def load_frozen(path: Path, expected_sha256: str = FROZEN_BUILDER_SHA256) -> ModuleType:
    """The frozen Gate B builder, by path, after its SHA-256 check (never copied or edited; as REQ-4 did)."""
    data = path.read_bytes()
    if sha256_bytes(data) != expected_sha256:
        raise Refusal(f"the frozen builder hashes to {sha256_bytes(data)}, the pin is {expected_sha256}")
    spec = importlib.util.spec_from_file_location("scale78b_frozen_build_sealed", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen_call(fn, *args):
    """A frozen-builder call; its Stop (a SystemExit) becomes a Refusal (ids and counts only)."""
    try:
        return fn(*args)
    except SystemExit as exc:
        raise Refusal(f"the frozen builder stopped ({exc})") from None


# ----- the Llama prepared set (row ids, target tokens, membership; no text) ---------------------------


class PreparedView:
    """What this wrapper reads of a prepared set: the manifest (pinned), row_id and target_tokens of each training row
    (the text fields are dropped at once), the dev unit membership and categories. The pattern of BLD's Inputs."""

    def __init__(self, root: Path, manifest_sha256: str):
        manifest_bytes = (root / "manifest.json").read_bytes()
        self.manifest_sha256 = sha256_bytes(manifest_bytes)
        if self.manifest_sha256 != manifest_sha256:
            raise Refusal(f"the prepared manifest hashes to {self.manifest_sha256}, expected {manifest_sha256}")
        manifest = strict_json(manifest_bytes)
        self.file_sha256: dict[str, str] = {}
        for name in (TRAIN_ROWS, GROUPS):
            digest = sha256_path(root / name)
            if digest != manifest["files"].get(name):
                raise Refusal(f"{name} hashes to {digest}, the manifest names another file")
            self.file_sha256[name] = digest
        self.tokens: dict[str, int] = {}
        with open(root / TRAIN_ROWS, encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                row_id, tokens = row.get("row_id"), row.get("target_tokens")
                row.clear()
                del row
                if not isinstance(row_id, str) or row_id in self.tokens:
                    raise Refusal("the training row ids are not distinct strings")
                if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 1:
                    raise Refusal(f"row {row_id} has no positive integer target_tokens")
                self.tokens[row_id] = tokens
        if len(self.tokens) != manifest["corpus"]["rows"]:
            raise Refusal("the training rows disagree with the manifest's row count")
        partitions = strict_json((root / GROUPS).read_bytes())["partitions"]
        if partitions["heldout"]["groups"] != [] or manifest["groups"]["heldout"]["members"] != 0:
            raise Refusal("the held-out partition is not empty: the edit pool would need it excluded")
        self.members = {g["group_id"]: sorted(g["members"]) for g in partitions["dev"]["groups"]}
        self.category = {gid: unit["category"] for gid, unit in manifest["units"].items()}
        self.units = sorted(self.members)
        if set(self.units) != set(self.category):
            raise Refusal("the dev groups and the manifest's units differ")
        seen: set[str] = set()
        for gid in self.units:
            rows = self.members[gid]
            if len(set(rows)) != len(rows) or seen & set(rows):
                raise Refusal(f"unit {gid} does not hold distinct rows of its own")
            seen |= set(rows)
        if seen != set(self.tokens):
            raise Refusal("the units do not partition the training rows")
        self.unit_of = {row: gid for gid in self.units for row in self.members[gid]}

    def engine_stub(self) -> "EngineStub":
        return EngineStub(self.manifest_sha256, dict.fromkeys(self.tokens), {"dev": dict(self.members), "heldout": {}})


class EngineStub:
    """What the engine's parse_edit reads of a prepared set (the pattern of BLD's EnginePrepared)."""

    def __init__(self, manifest_sha256: str, train_rows: dict, groups: dict):
        self.manifest_sha256 = manifest_sha256
        self.train_rows = train_rows
        self.groups = groups


def check_membership(olmo: Any, llama: PreparedView) -> dict:
    """Refuse unless both prepared sets hold the same groups, member lists and row ids. Counts only."""
    if list(olmo.units) != list(llama.units):
        raise Refusal("the two prepared sets' dev groups differ (group ids)")
    for gid in olmo.units:
        if list(olmo.members[gid]) != list(llama.members[gid]):
            raise Refusal(f"the two prepared sets' member lists differ for unit {gid}")
    if dict(olmo.category) != dict(llama.category):
        raise Refusal("the two prepared sets' unit categories differ")
    if set(olmo.tokens) != set(llama.tokens):
        raise Refusal("the two prepared sets' training row ids differ")
    differ = sum(1 for r, t in olmo.tokens.items() if llama.tokens[r] != t)
    return {"units": len(olmo.units), "rows_per_unit": sorted({len(olmo.members[g]) for g in olmo.units}),
            "training_rows": len(olmo.tokens), "group_ids_equal": True, "member_lists_equal": True,
            "categories_equal": True, "row_ids_equal": True, "heldout_members": 0,
            "rows_whose_target_tokens_differ": differ, "note": MEMBERSHIP_NOTE}


# ----- the earlier files (SEAL, stage 1): their remove lists, pinned ---------------------------------


def seal_files(seal_out: Path, manifest_sha256: str = SEAL_MANIFEST_SHA256) -> dict[str, dict]:
    """SEAL's R_d1..R_d5 and unit files: bytes, remove list and SHA-256, each listed by the pinned MANIFEST.json."""
    manifest_bytes = (seal_out / "MANIFEST.json").read_bytes()
    if sha256_bytes(manifest_bytes) != manifest_sha256:
        raise Refusal(f"the sealed MANIFEST.json hashes to {sha256_bytes(manifest_bytes)}, the pin is {manifest_sha256}")
    listed = {f["path"]: f["sha256"] for f in strict_json(manifest_bytes)["files"]}
    out = {}
    for path, digest in listed.items():
        if not (path.startswith("edits/R_d") or path.startswith("edits/unit_")):
            continue
        data = (seal_out / path).read_bytes()
        if sha256_bytes(data) != digest:
            raise Refusal(f"{path} is not the file the sealed manifest lists")
        doc = strict_json(data)
        out[path] = {"bytes": data, "remove": list(doc["remove"]), "sha256": digest, "document": doc}
    if {p for p in out if p.startswith("edits/R_d")} != {f"edits/R_d{d}.json" for d in SEAL_DRAWS}:
        raise Refusal("the sealed manifest does not list exactly R_d1..R_d5")
    return out


def stage1_files(rdraws: Path, record_sha256: str = STAGE1_RECORD_SHA256) -> dict[str, dict]:
    """Stage 1's R_d6..R_d10 (REQ-4): bytes, remove list and SHA-256, each listed by the pinned r_draws_record.json."""
    record_bytes = (rdraws / "r_draws_record.json").read_bytes()
    if sha256_bytes(record_bytes) != record_sha256:
        raise Refusal(f"stage 1's r_draws_record.json hashes to {sha256_bytes(record_bytes)}, the pin is {record_sha256}")
    record = strict_json(record_bytes)
    out = {}
    for entry in record["files"]:
        if entry["family"] != "R":
            continue
        path, digest = entry["file"], entry["sha256"]
        data = (rdraws / path).read_bytes()
        if sha256_bytes(data) != digest:
            raise Refusal(f"{path} is not the file stage 1's record lists")
        doc = strict_json(data)
        out[path] = {"bytes": data, "remove": list(doc["remove"]), "sha256": digest, "document": doc,
                     "seed": entry["seed"], "draw": entry["draw"]}
    if set(out) != {f"edits/R_d{d}.json" for d in STAGE1_DRAWS}:
        raise Refusal("stage 1's record does not list exactly R_d6..R_d10 in family R")
    seed_map = record.get("seed_map") or {}
    if seed_map.get("offset") != SEED_OFFSET or any(out[f"edits/R_d{d}.json"]["seed"] != SEED_OFFSET + d
                                                     for d in STAGE1_DRAWS):
        raise Refusal("stage 1's seed map is not 'draw d at seed 1100 + d'")
    return out


def recorded_base(seal: dict[str, dict], inputs: Any, builder_sha256: str = FROZEN_BUILDER_SHA256) -> dict:
    """The frozen builder's recorded provenance block (SEAL's R_d1 without its selection), checked against the
    current OLMo inputs; the byte reproduction of R_d1..5 then proves it is the block the builder writes (REQ-4)."""
    base = dict(seal["edits/R_d1.json"]["document"]["provenance"])
    base.pop("selection", None)
    recorded = base.get("inputs") or {}
    if base.get("builder_sha256") != builder_sha256:
        raise Refusal("the sealed files were not written by the pinned frozen builder")
    if [recorded.get("manifest_sha256")] + [recorded.get(f) for f in (TRAIN_ROWS, GROUPS)] != \
            [inputs.manifest_sha256] + [inputs.file_sha256[f] for f in (TRAIN_ROWS, GROUPS)]:
        raise Refusal("the sealed files were written for another prepared set")
    return base


# ----- the frozen builder's own OLMo files (the parity check) ----------------------------------------


def frozen_r_file(frozen: ModuleType, inputs: Any, d: int, base: dict, extra: dict | None = None) -> tuple[bytes, list[str], list]:
    """R_d by the frozen builder's draw_r and edit_file, with its own name, selection and provenance (plus extra)."""
    remove, per_unit = frozen_call(frozen.draw_r, inputs, d)
    name = (f"gate-b R_{d}: remove {frozen.R_PER_UNIT} rows of each of the {frozen.UNITS} units at random "
            f"({len(remove)} rows)")
    selection = {"family": "R", "draw": d, "design_seed": frozen.DESIGN_SEED, "stream": frozen.STREAM_R,
                 "rule": frozen.RULE_R, "per_unit": per_unit}
    data, _ = frozen_call(frozen.edit_file, inputs, name, remove, {**base, "selection": selection, **(extra or {})},
                          frozen.EnginePrepared(inputs))
    return data, remove, per_unit


def frozen_unit_file(frozen: ModuleType, inputs: Any, u: str, base: dict) -> tuple[bytes, list[str]]:
    """unit_<u> by the frozen builder's edit_file, with its own name, selection and provenance (BLD lines 358-362)."""
    remove = list(inputs.members[u])
    name = f"gate-b unit removal {u} ({inputs.category[u]}): remove all {frozen.ROWS_PER_UNIT} rows of the unit"
    selection = {"family": "unit", "unit": u, "category": inputs.category[u], "rule": frozen.RULE_UNIT}
    data, _ = frozen_call(frozen.edit_file, inputs, name, remove, {**base, "selection": selection},
                          frozen.EnginePrepared(inputs))
    return data, remove


def stage1_wrapper_block(repo: Path, d: int) -> dict:
    """The stage1_wrapper provenance block REQ-4 wrote, re-derived with stage 1's own s1common.provenance on the
    committed REQ-4 script and settings (both pinned). Byte equality with stage 1's files then holds when the
    environment matches REQ-4's run (Python and numpy versions); the differing fields otherwise are those two."""
    settings_bytes = (repo / STAGE1_SETTINGS_REL).read_bytes()
    if sha256_bytes(settings_bytes) != STAGE1_SETTINGS_SHA256:
        raise Refusal("stage 1's build_r_draws settings are not the pinned file")
    settings = strict_json(settings_bytes)
    from scripts.stage1 import s1common as s1   # read-only import of the committed stage-1 helpers
    block = s1.provenance(repo / STAGE1_SCRIPT_REL, STAGE1_SETTINGS_SHA256,
                          {"prepared_manifest": OLMO_MANIFEST_SHA256, "frozen_builder": FROZEN_BUILDER_SHA256,
                           "sealed_manifest": SEAL_MANIFEST_SHA256}, settings["label_entries"])
    return {**block, "seed": settings["seed_map"]["offset"] + d, "seed_rule": settings["seed_map"]["rule"]}


def reproduce_olmo(frozen: ModuleType, inputs: Any, base: dict, seal: dict, stage1: dict, repo: Path,
                   with_stage1_wrapper: bool) -> tuple[dict[str, bytes], dict]:
    """The frozen builder's OLMo files: R_d1..R_d5 and the unit files must equal SEAL's bytes (refuse otherwise);
    R_d6..R_d10 must equal stage 1's remove lists (refuse otherwise), and their bytes are compared too."""
    files: dict[str, bytes] = {}
    parity = {"sealed": {}, "stage1_r_draws": {}}
    for d in SEAL_DRAWS:
        path = f"edits/R_d{d}.json"
        data, remove, _ = frozen_r_file(frozen, inputs, d, base)
        if remove != seal[path]["remove"]:
            raise Refusal(f"R_{d}: the frozen builder's draw differs from the sealed remove list")
        if data != seal[path]["bytes"]:
            raise Refusal(f"R_{d}: the frozen builder's file differs from the sealed bytes")
        files[path] = data
        parity["sealed"][path] = {"sha256": sha256_bytes(data), "rows": len(remove), "byte_identical": True}
    for u in inputs.units:
        path = f"edits/unit_{u}.json"
        data, remove = frozen_unit_file(frozen, inputs, u, base)
        if path not in seal:
            raise Refusal(f"the sealed manifest lists no {path}")
        if remove != seal[path]["remove"]:
            raise Refusal(f"unit {u}: the member list differs from the sealed remove list")
        if data != seal[path]["bytes"]:
            raise Refusal(f"unit {u}: the frozen builder's file differs from the sealed bytes")
        files[path] = data
        parity["sealed"][path] = {"sha256": sha256_bytes(data), "rows": len(remove), "byte_identical": True}
    for d in STAGE1_DRAWS:
        path = f"edits/R_d{d}.json"
        extra = {"stage1_wrapper": stage1_wrapper_block(repo, d)} if with_stage1_wrapper else None
        data, remove, _ = frozen_r_file(frozen, inputs, d, base, extra)
        if remove != stage1[path]["remove"]:
            raise Refusal(f"R_{d}: the frozen builder's draw differs from stage 1's remove list (C5)")
        theirs = dict(stage1[path]["document"])
        mine = strict_json(data)
        theirs_wo, mine_wo = dict(theirs), dict(mine)
        theirs_wo["provenance"] = {k: v for k, v in theirs["provenance"].items() if k != "stage1_wrapper"}
        mine_wo["provenance"] = {k: v for k, v in mine["provenance"].items() if k != "stage1_wrapper"}
        entry = {"sha256": sha256_bytes(data), "stage1_sha256": stage1[path]["sha256"], "rows": len(remove),
                 "remove_list_equal": True, "equal_without_stage1_wrapper": theirs_wo == mine_wo,
                 "byte_identical": data == stage1[path]["bytes"], "stage1_wrapper_rederived": with_stage1_wrapper}
        if not entry["equal_without_stage1_wrapper"]:
            raise Refusal(f"R_{d}: the frozen builder's document differs from stage 1's outside stage1_wrapper")
        if with_stage1_wrapper and not entry["byte_identical"]:
            a, b = theirs["provenance"].get("stage1_wrapper", {}), mine["provenance"].get("stage1_wrapper", {})
            entry["differing_stage1_wrapper_fields"] = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        files[path] = data
        parity["stage1_r_draws"][path] = entry
    return files, parity


# ----- the Llama writer ------------------------------------------------------------------------------


def llama_edit(name: str, remove: list[str], provenance: dict, llama: PreparedView, olmo_stub: Any) -> tuple[bytes, str]:
    """An edit file on the Llama manifest, parsed back with the engine's parse_edit against the Llama set; the engine
    must refuse it against the OLMo set (manifest_sha256)."""
    doc = {"kind": EDIT_KIND, "version": EDIT_VERSION, "name": name, "edit_kind": "remove",
           "manifest_sha256": llama.manifest_sha256, "remove": sorted(remove), "rewrite": [], "add": [],
           "position_rule": POSITION_RULE, "counts": {"remove": len(remove), "rewrite": 0, "add": 0},
           "provenance": provenance}
    data = edit_bytes(doc)
    try:
        edit = parse_edit(data, llama.engine_stub())
    except EditError as exc:
        raise Refusal(f"the engine refuses {name!r} against the Llama set ({type(exc).__name__})") from None
    if edit.removed != frozenset(remove) or edit.arm != arm_of(data) or edit.document != doc:
        raise Refusal(f"the engine reads {name!r} differently from what was written")
    try:
        parse_edit(data, olmo_stub)
    except EditError:
        pass
    else:
        raise Refusal(f"the engine accepted {name!r} against the OLMo set: the manifest binding failed")
    return data, arm_of(data)


def guard_out(out: Path, repo: Path | None = None) -> None:
    """Refuse an output under a committed sealed folder (FORBIDDEN_DIRS) of this script's own checkout (REPO) or of
    --repo, and a folder that exists and is not empty. The forbidden roots come from REPO first, so a non-default --repo
    cannot aim --out into this checkout's SEAL or stage-1 folder. Two comparisons: the resolved paths as strings (this
    also covers a forbidden folder that does not exist yet) and, for each forbidden folder that exists, directory
    identity (os.path.samefile) between it and the deepest existing ancestor of out (out itself when it exists) or any
    parent of that ancestor. Identity covers a case-variant spelling on a case-insensitive filesystem (resolve() keeps
    the typed case), a symlink and a dotted or relative path."""
    out = out.resolve()
    roots = [REPO.resolve()]
    if repo is not None and repo.resolve() not in roots:
        roots.append(repo.resolve())
    anchor = out                                        # the deepest existing ancestor of out (out itself when it exists)
    while not anchor.exists() and anchor.parent != anchor:
        anchor = anchor.parent
    for root in roots:
        for forbidden in FORBIDDEN_DIRS:
            target = (root / forbidden).resolve()
            if out == target or target in out.parents:
                raise Refusal(f"refusing to write under {forbidden}")
            if target.exists() and any(os.path.samefile(p, target) for p in (anchor, *anchor.parents)):
                raise Refusal(f"refusing to write under {forbidden}")
    if out.exists() and any(out.iterdir()):
        raise Refusal(f"{out} exists and is not empty: a sealed build never overwrites")


def build(repo: Path, frozen_path: Path, olmo_root: Path, llama_root: Path, seal_out: Path, rdraws: Path,
          llama_manifest_sha256: str = LLAMA_MANIFEST_SHA256, olmo_parity: bool = False) -> dict[str, Any]:
    """Every output file (nothing is written here): {"files": {rel: bytes}, "parity_files": {rel: bytes}, ...}."""
    builder_sha256 = sha256_path(Path(__file__).resolve())
    frozen = load_frozen(frozen_path)
    inputs = frozen_call(frozen.Inputs, olmo_root)                 # BLD's own checks of the OLMo prepared set
    if inputs.manifest_sha256 != OLMO_MANIFEST_SHA256:
        raise Refusal("the frozen builder's inputs are not the pinned OLMo prepared set")
    llama = PreparedView(llama_root, llama_manifest_sha256)
    membership = check_membership(inputs, llama)
    seal = seal_files(seal_out)
    stage1 = stage1_files(rdraws)
    base = recorded_base(seal, inputs)
    olmo_files, parity = reproduce_olmo(frozen, inputs, base, seal, stage1, repo, with_stage1_wrapper=olmo_parity)
    olmo_stub = frozen.EnginePrepared(inputs)

    pool = {"rule": frozen.POOL_RULE, "training_rows": len(llama.tokens), "pool_rows": len(llama.tokens),
            "heldout_members_excluded": 0}
    common = {"builder": BUILDER_REL, "builder_sha256": builder_sha256,
              "frozen_builder": {"path": FROZEN_BUILDER_TMP, "committed_copy": FROZEN_BUILDER_COMMITTED,
                                 "sha256": FROZEN_BUILDER_SHA256, "spec": base["spec"],
                                 "used": "Inputs on the OLMo prepared folder; draw_r(inputs, d); the R and unit rules"},
              "inputs": {"prepared": LLAMA_PREPARED_REL, "manifest_sha256": llama.manifest_sha256,
                         TRAIN_ROWS: llama.file_sha256[TRAIN_ROWS], GROUPS: llama.file_sha256[GROUPS],
                         "fields_read": FIELDS_READ},
              "drawn_on": dict(base["inputs"]), "membership_check": MEMBERSHIP_NOTE,
              "derive_seed": dict(base["derive_seed"]), "pool": pool,
              "seed_map": {"offset": SEED_OFFSET, "rule": SEED_RULE}, "spec": SPEC}

    files: dict[str, bytes] = {}
    records: list[dict] = []
    for d in DRAWS:
        remove, per_unit = frozen_call(frozen.draw_r, inputs, d)
        path = f"edits/R_d{d}.json"
        if d in SEAL_DRAWS:
            same = {"file": f"{SEAL_OUT_REL}/{path}", "sha256": seal[path]["sha256"], "remove_list_equal": True}
        elif d in STAGE1_DRAWS:
            same = {"file": f"{STAGE1_RDRAWS_REL}/{path}", "sha256": stage1[path]["sha256"], "remove_list_equal": True}
        else:
            same = {"file": None, "note": "a new draw of the frozen builder's stream; no earlier file holds it"}
        if same["file"] is not None:
            earlier = seal[path]["remove"] if d in SEAL_DRAWS else stage1[path]["remove"]
            if remove != earlier:
                raise Refusal(f"R_{d}: the draw differs from the earlier file's remove list")
        name = (f"scale-78b R_{d} (prepared-kt-dolly-llama3): remove {frozen.R_PER_UNIT} rows of each of the "
                f"{frozen.UNITS} units at random ({len(remove)} rows); the frozen Gate B builder's draw_r(d = {d})")
        provenance = {**common, "selection": {"family": "R", "draw": d, "design_seed": frozen.DESIGN_SEED,
                                              "stream": frozen.STREAM_R, "rule": frozen.RULE_R, "per_unit": per_unit},
                      "same_rows_as": same, "seed": SEED_OFFSET + d, "role": ROLES[d]}
        data, arm = llama_edit(name, remove, provenance, llama, olmo_stub)
        files[path] = data
        records.append({"path": path, "role": ROLES[d], "family": "R", "draw": d, "seed": SEED_OFFSET + d,
                        "rows": len(remove), "same_rows_as": same, "arm": arm, "sha256": sha256_bytes(data),
                        "bytes": len(data)})
    for u in llama.units:
        path = f"edits/unit_{u}.json"
        remove = list(llama.members[u])
        if remove != seal[path]["remove"]:
            raise Refusal(f"unit {u}: the member list differs from the sealed unit file")
        name = (f"scale-78b unit removal {u} ({llama.category[u]}) (prepared-kt-dolly-llama3): remove all "
                f"{len(remove)} rows of the unit")
        provenance = {**common, "selection": {"family": "unit", "unit": u, "category": llama.category[u],
                                              "rule": frozen.RULE_UNIT},
                      "same_rows_as": {"file": f"{SEAL_OUT_REL}/{path}", "sha256": seal[path]["sha256"],
                                       "remove_list_equal": True},
                      "role": "unit removal (TC does not run, ruling 6; kept for completeness and for stage 2)"}
        data, arm = llama_edit(name, remove, provenance, llama, olmo_stub)
        files[path] = data
        records.append({"path": path, "role": "unit removal", "family": "unit", "unit": u,
                        "category": llama.category[u], "rows": len(remove),
                        "same_rows_as": provenance["same_rows_as"], "arm": arm, "sha256": sha256_bytes(data),
                        "bytes": len(data)})

    identity = code_identity()
    manifest = {
        "kind": MANIFEST_KIND, "version": 1,
        "builder": {"path": BUILDER_REL, "sha256": builder_sha256, "python": sys.version.split()[0]},
        "frozen_builder": {"path": FROZEN_BUILDER_TMP, "committed_copy": FROZEN_BUILDER_COMMITTED,
                           "loaded_from": rel(frozen_path, repo), "sha256": FROZEN_BUILDER_SHA256,
                           "used": "Inputs (on the OLMo prepared folder), draw_r(inputs, d) for d = 1-16, "
                                   "edit_file and EnginePrepared for the OLMo parity check, and the constants "
                                   "DESIGN_SEED, STREAM_R, R_PER_UNIT, UNITS, ROWS_PER_UNIT, RULE_R, RULE_UNIT, "
                                   "POOL_RULE"},
        "prepared": {"drawn_on": {"root": OLMO_PREPARED_REL, "manifest_sha256": inputs.manifest_sha256,
                                  "read": {TRAIN_ROWS: inputs.file_sha256[TRAIN_ROWS],
                                           GROUPS: inputs.file_sha256[GROUPS]}},
                     "written_for": {"root": LLAMA_PREPARED_REL, "manifest_sha256": llama.manifest_sha256,
                                     "read": {TRAIN_ROWS: llama.file_sha256[TRAIN_ROWS],
                                              GROUPS: llama.file_sha256[GROUPS]}},
                     "fields_read": FIELDS_READ, "never_opened": NEVER_OPENED},
        "membership_check": membership,
        "parity": {"sealed": {"dir": SEAL_OUT_REL, "manifest_sha256": SEAL_MANIFEST_SHA256,
                              "files": parity["sealed"]},
                   "stage1_r_draws": {"dir": STAGE1_RDRAWS_REL, "record_sha256": STAGE1_RECORD_SHA256,
                                      "files": {p: {k: v for k, v in e.items()
                                                    if k not in ("byte_identical", "stage1_wrapper_rederived",
                                                                 "differing_stage1_wrapper_fields", "sha256")}
                                                for p, e in parity["stage1_r_draws"].items()}}},
        "engine": {"code_identity_sha256": identity["sha256"], "derive_seed": dict(base["derive_seed"]),
                   "edit_conventions": {"file": "experiments/safety_selection/edits.py",
                                        "file_sha256": identity["files"]["safety_selection/edits.py"],
                                        "used": "EDIT_KIND, EDIT_VERSION, POSITION_RULE, edit_bytes (canonical "
                                                "JSON), arm_of (edit-<SHA-256 of the bytes>), parse_edit"}},
        "seed_map": {"offset": SEED_OFFSET, "rule": SEED_RULE},
        "roles": {str(d): ROLES[d] for d in DRAWS},
        "serves": ["Llama-3.1-8B (the 7-8B tier)", "Llama-3.2-1B (stage 2): the same manifest c52a50af"],
        "not_built": "S3, S4 and the S4 add-dose edits (S4_96, S4_192) are per model, not per manifest (the check's "
                     "C6): they need each model's untuned-answers pass on a pod. H1 and S1: see README.md.",
        "files": records}
    files["MANIFEST.json"] = canonical_json(manifest)

    parity_files: dict[str, bytes] = {}
    if olmo_parity:
        parity_files = dict(olmo_files)
        parity_files["PARITY.json"] = canonical_json(
            {"kind": PARITY_KIND, "version": 1, "builder": {"path": BUILDER_REL, "sha256": builder_sha256},
             "frozen_builder_sha256": FROZEN_BUILDER_SHA256, "prepared_manifest_sha256": inputs.manifest_sha256,
             "sealed": {"dir": SEAL_OUT_REL, "manifest_sha256": SEAL_MANIFEST_SHA256, "files": parity["sealed"]},
             "stage1_r_draws": {"dir": STAGE1_RDRAWS_REL, "record_sha256": STAGE1_RECORD_SHA256,
                                "files": parity["stage1_r_draws"]},
             "note": "R_d1-R_d5 and the unit files: the frozen builder's own bytes (SEAL's). R_d6-R_d10: the frozen "
                     "builder's own bytes with REQ-4's stage1_wrapper block re-derived by stage 1's s1common.provenance "
                     "on the committed REQ-4 script and settings; byte_identical says whether they equal stage 1's."})
    return {"files": files, "parity_files": parity_files, "manifest": manifest, "records": records}


def write_files(out: Path, files: dict[str, bytes]) -> dict[str, str]:
    out.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        write_atomic(out / name, data)
    digests = {}
    for name, data in files.items():                               # read back
        digests[name] = sha256_path(out / name)
        if digests[name] != sha256_bytes(data):
            raise Refusal(f"{name} did not read back as written")
    return digests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", type=Path, default=REPO, help="the checkout that holds the inputs (default: this one)")
    parser.add_argument("--frozen-builder", type=Path, default=None,
                        help=f"BLD's path (default <repo>/{FROZEN_BUILDER_COMMITTED}; the same bytes as "
                             f"<repo>/{FROZEN_BUILDER_TMP})")
    parser.add_argument("--out", type=Path, default=HERE / "out", help="output folder (must be absent or empty)")
    parser.add_argument("--olmo-parity-out", type=Path, default=None,
                        help="also write the frozen builder's reproduced OLMo files here (absent or empty)")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    frozen_path = (args.frozen_builder or repo / FROZEN_BUILDER_COMMITTED).resolve()
    try:
        guard_out(args.out, repo)
        if args.olmo_parity_out is not None:
            guard_out(args.olmo_parity_out, repo)
            if args.olmo_parity_out.resolve() == args.out.resolve():
                raise Refusal("--olmo-parity-out must differ from --out")
        before = sha256_path(frozen_path)
        result = build(repo, frozen_path, repo / OLMO_PREPARED_REL, repo / LLAMA_PREPARED_REL, repo / SEAL_OUT_REL,
                       repo / STAGE1_RDRAWS_REL, olmo_parity=args.olmo_parity_out is not None)
        written = write_files(args.out.resolve(), result["files"])
        parity_written = {}
        if args.olmo_parity_out is not None:
            parity_written = write_files(args.olmo_parity_out.resolve(), result["parity_files"])
        after = sha256_path(frozen_path)
        if before != after or after != FROZEN_BUILDER_SHA256:
            raise Refusal(f"the frozen builder's bytes changed during the build ({after})")
    except Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    print(f"built {len(written)} files into {args.out}")
    print(f"builder sha256 {result['manifest']['builder']['sha256']}; frozen builder {FROZEN_BUILDER_SHA256}; "
          f"engine {result['manifest']['engine']['code_identity_sha256']}")
    print(f"drawn on {OLMO_MANIFEST_SHA256}; written for {LLAMA_MANIFEST_SHA256}")
    print(f"MANIFEST.json sha256 {written['MANIFEST.json']}")
    for record in result["records"]:
        print(f"  {record['sha256']}  {record['path']}  arm {record['arm']}  rows {record['rows']}"
              + (f"  seed {record['seed']}" if "seed" in record else ""))
    if parity_written:
        print(f"parity: {len(parity_written)} OLMo files into {args.olmo_parity_out}")
        for name, digest in sorted(parity_written.items()):
            print(f"  {digest}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
