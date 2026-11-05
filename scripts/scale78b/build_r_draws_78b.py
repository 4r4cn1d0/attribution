"""The OLMo random-removal draws d = 11..16 on prepared-kt-dolly-olmo2 (manifest 9ed61826...), for the 12-seed branch
H (b) of the 7-8B tier (ruling 2: R at 1101-1113; d = 14-16 built for completeness, not run). Mac, $0, standard
library plus the engine's edit conventions. P78 section 9.2 item 3.

Route (the same as stage 1's REQ-4, scripts/stage1/build_r_draws.py):

1. The frozen Gate B builder BLD (``build_sealed.py``, SHA-256 80cb8944...) is loaded by path after its SHA-256 check.
   It is never copied or edited.
2. Reproduce first. BLD's own ``draw_r`` and ``edit_file``, with its recorded provenance (SEAL's R_d1 file's, without
   its selection), must give SEAL's ``edits/R_d1..R_d5`` byte for byte (the pinned sealed MANIFEST.json lists each),
   and ``draw_r`` for d = 6..10 must give stage 1's ``r-draws/edits/R_d6..R_d10`` remove lists (the pinned record
   lists each). Any difference refuses and nothing is written.
3. R_d for d = 11..16 by BLD's own ``draw_r`` and ``edit_file`` (75 rows per unit, stream gate-b-random-removal-v1,
   parts (d, g); the sorted union), on the OLMo manifest. The provenance is BLD's recorded block plus
   ``scale78b_wrapper`` (this script's SHA-256, the pinned inputs, the seed 1100 + d, the role).

Reads from the prepared set ONLY what BLD's ``Inputs`` reads: manifest.json; engine/train_rows.jsonl (row_id and
target_tokens; the text is dropped at once and never printed); engine/groups.json. Never writes under a committed
sealed folder: SEAL (.ai/inputs/gate-b-sealed-20261008/), the anchor list (.ai/inputs/gate-b-anchors-20261008/) or
stage 1's records (.ai/inputs/stage1-commitments-20261016/); those folders are resolved from this script's own
checkout (REPO) and from --repo, so a non-default --repo cannot aim --out into them.

Writes into --out (absent or empty; default .ai/inputs/scale-78b-r-draws-olmo2-20261105/out):
  edits/R_d11.json .. edits/R_d16.json
  MANIFEST.json      every file's SHA-256 and arm; the reproduction results; no build time (deterministic)
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
REPO = HERE.parents[1]                      # <repo>/scripts/scale78b/build_r_draws_78b.py
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes, write_atomic  # noqa: E402

SCRIPT_REL = "scripts/scale78b/build_r_draws_78b.py"
OUT_REL = ".ai/inputs/scale-78b-r-draws-olmo2-20261105/out"
FROZEN_BUILDER_SHA256 = "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6"
FROZEN_BUILDER_COMMITTED = ".ai/inputs/gate-b-sealed-20261008/build_sealed.py"
FROZEN_BUILDER_TMP = "tmp/gate-b-sealed/build_sealed.py"
PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-olmo2"
PREPARED_MANIFEST_SHA256 = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
SEAL_DIR_REL = ".ai/inputs/gate-b-sealed-20261008"
SEAL_OUT_REL = ".ai/inputs/gate-b-sealed-20261008/out"
SEAL_MANIFEST_SHA256 = "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"
ANCHORS_DIR_REL = ".ai/inputs/gate-b-anchors-20261008"
STAGE1_DIR_REL = ".ai/inputs/stage1-commitments-20261016"
STAGE1_RDRAWS_REL = ".ai/inputs/stage1-commitments-20261016/r-draws"
STAGE1_RECORD_SHA256 = "c09b20c135b483495987fd9dd2652ef3df31a7bc8fdbfe0581a1d3ce06882b6c"
FORBIDDEN_DIRS = (SEAL_DIR_REL, ANCHORS_DIR_REL, STAGE1_DIR_REL)     # committed sealed folders: never an output
TRAIN_ROWS = "engine/train_rows.jsonl"
GROUPS = "engine/groups.json"

SEAL_DRAWS = (1, 2, 3, 4, 5)
STAGE1_DRAWS = (6, 7, 8, 9, 10)
NEW_DRAWS = (11, 12, 13, 14, 15, 16)
SEED_OFFSET = 1100
SEED_RULE = ("draw d runs at seed 1100 + d (Gate B's wave rule; stage 1's L5 seed map; ruling 2: R at 1101 to the "
             "last method seed, a0 at 1101-1107)")
ROLES = {**{d: "branch H (b): R at 1101-1113 (ruling 2); the 12-seed branch's R partners at 1111-1113" for d in (11, 12, 13)},
         **{d: "built for completeness (P78 section 9.2 item 3: d = 9-16); not run under ruling 2 (no R seed beyond "
               "the last method seed 1113)" for d in (14, 15, 16)}}
REQUIREMENT = ("P78 section 9.2 item 3 (research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md); ruling 2 "
               "(.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md); the readiness plan T7")
MANIFEST_KIND = "scale-78b olmo2 random-removal draws manifest"


class Refusal(Exception):
    """A check failed: nothing is written."""


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def strict_json(data: bytes) -> Any:
    try:
        return json.loads(data)
    except ValueError:
        raise Refusal("a JSON file does not parse") from None


def load_frozen(path: Path, expected_sha256: str = FROZEN_BUILDER_SHA256) -> ModuleType:
    """The frozen Gate B builder, by path, after its SHA-256 check (never copied or edited; as REQ-4 did)."""
    data = path.read_bytes()
    if sha256_bytes(data) != expected_sha256:
        raise Refusal(f"the frozen builder hashes to {sha256_bytes(data)}, the pin is {expected_sha256}")
    spec = importlib.util.spec_from_file_location("scale78b_frozen_build_sealed_r", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen_call(fn, *args):
    try:
        return fn(*args)
    except SystemExit as exc:                                     # BLD's Stop: ids and counts only
        raise Refusal(f"the frozen builder stopped ({exc})") from None


def seal_r_files(seal_out: Path, manifest_sha256: str = SEAL_MANIFEST_SHA256) -> dict[int, dict]:
    manifest_bytes = (seal_out / "MANIFEST.json").read_bytes()
    if sha256_bytes(manifest_bytes) != manifest_sha256:
        raise Refusal(f"the sealed MANIFEST.json hashes to {sha256_bytes(manifest_bytes)}, the pin is {manifest_sha256}")
    listed = {f["path"]: f["sha256"] for f in strict_json(manifest_bytes)["files"]}
    out = {}
    for d in SEAL_DRAWS:
        rel = f"edits/R_d{d}.json"
        if rel not in listed:
            raise Refusal(f"the sealed manifest lists no {rel}")
        data = (seal_out / rel).read_bytes()
        if sha256_bytes(data) != listed[rel]:
            raise Refusal(f"{rel} is not the file the sealed manifest lists")
        out[d] = {"bytes": data, "document": strict_json(data), "sha256": listed[rel]}
    return out


def stage1_r_files(rdraws: Path, record_sha256: str = STAGE1_RECORD_SHA256) -> dict[int, dict]:
    record_bytes = (rdraws / "r_draws_record.json").read_bytes()
    if sha256_bytes(record_bytes) != record_sha256:
        raise Refusal(f"stage 1's r_draws_record.json hashes to {sha256_bytes(record_bytes)}, the pin is {record_sha256}")
    out = {}
    for entry in strict_json(record_bytes)["files"]:
        if entry["family"] != "R":
            continue
        data = (rdraws / entry["file"]).read_bytes()
        if sha256_bytes(data) != entry["sha256"]:
            raise Refusal(f"{entry['file']} is not the file stage 1's record lists")
        out[entry["draw"]] = {"bytes": data, "document": strict_json(data), "sha256": entry["sha256"], "seed": entry["seed"]}
    if set(out) != set(STAGE1_DRAWS) or any(out[d]["seed"] != SEED_OFFSET + d for d in STAGE1_DRAWS):
        raise Refusal("stage 1's record does not list R_d6..R_d10 at seeds 1106-1110")
    return out


def recorded_base(seal: dict[int, dict], inputs: Any) -> dict:
    """BLD's recorded provenance block (SEAL's R_d1 without its selection), checked against the inputs (REQ-4)."""
    base = dict(seal[1]["document"]["provenance"])
    base.pop("selection", None)
    recorded = base.get("inputs") or {}
    if base.get("builder_sha256") != FROZEN_BUILDER_SHA256:
        raise Refusal("the sealed files were not written by the pinned frozen builder")
    if [recorded.get("manifest_sha256")] + [recorded.get(f) for f in (TRAIN_ROWS, GROUPS)] != \
            [inputs.manifest_sha256] + [inputs.file_sha256[f] for f in (TRAIN_ROWS, GROUPS)]:
        raise Refusal("the sealed files were written for another prepared set")
    return base


def frozen_r_file(frozen: ModuleType, inputs: Any, d: int, base: dict, extra: dict | None = None) -> tuple[bytes, list[str], list]:
    """R_d by BLD's draw_r and edit_file, with its own name, selection and provenance (plus extra)."""
    remove, per_unit = frozen_call(frozen.draw_r, inputs, d)
    name = (f"gate-b R_{d}: remove {frozen.R_PER_UNIT} rows of each of the {frozen.UNITS} units at random "
            f"({len(remove)} rows)")
    selection = {"family": "R", "draw": d, "design_seed": frozen.DESIGN_SEED, "stream": frozen.STREAM_R,
                 "rule": frozen.RULE_R, "per_unit": per_unit}
    data, _ = frozen_call(frozen.edit_file, inputs, name, remove, {**base, "selection": selection, **(extra or {})},
                          frozen.EnginePrepared(inputs))
    return data, remove, per_unit


def reproduce(frozen: ModuleType, inputs: Any, base: dict, seal: dict, stage1: dict) -> dict:
    out = {"sealed": {}, "stage1_r_draws": {}}
    for d in SEAL_DRAWS:
        data, remove, _ = frozen_r_file(frozen, inputs, d, base)
        if remove != seal[d]["document"]["remove"]:
            raise Refusal(f"R_{d}: the frozen builder's draw differs from the sealed remove list")
        if data != seal[d]["bytes"]:
            raise Refusal(f"R_{d}: the frozen builder's file differs from the sealed bytes")
        out["sealed"][f"edits/R_d{d}.json"] = {"sha256": seal[d]["sha256"], "rows": len(remove), "byte_identical": True}
    for d in STAGE1_DRAWS:
        remove, _ = frozen_call(frozen.draw_r, inputs, d)
        if remove != stage1[d]["document"]["remove"]:
            raise Refusal(f"R_{d}: the frozen builder's draw differs from stage 1's remove list")
        out["stage1_r_draws"][f"edits/R_d{d}.json"] = {"sha256": stage1[d]["sha256"], "rows": len(remove),
                                                        "remove_list_equal": True}
    return out


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


def build(repo: Path, frozen_path: Path, prepared: Path, seal_out: Path, rdraws: Path) -> dict[str, Any]:
    """Every output file (nothing is written here)."""
    script_sha256 = sha256_path(Path(__file__).resolve())
    frozen = load_frozen(frozen_path)
    inputs = frozen_call(frozen.Inputs, prepared)
    if inputs.manifest_sha256 != PREPARED_MANIFEST_SHA256:
        raise Refusal("the frozen builder's inputs are not the pinned OLMo prepared set")
    seal = seal_r_files(seal_out)
    stage1 = stage1_r_files(rdraws)
    base = recorded_base(seal, inputs)
    reproduced = reproduce(frozen, inputs, base, seal, stage1)
    identity = code_identity()["sha256"]
    wrapper = {"script": SCRIPT_REL, "script_sha256": script_sha256,
               "inputs": {"frozen_builder": FROZEN_BUILDER_SHA256, "prepared_manifest": inputs.manifest_sha256,
                          "sealed_manifest": SEAL_MANIFEST_SHA256, "stage1_r_draws_record": STAGE1_RECORD_SHA256},
               "engine_identity_sha256": identity, "requirement": REQUIREMENT, "seed_rule": SEED_RULE}
    files: dict[str, bytes] = {}
    records: list[dict] = []
    for d in NEW_DRAWS:
        data, remove, per_unit = frozen_r_file(frozen, inputs, d, base,
                                               {"scale78b_wrapper": {**wrapper, "seed": SEED_OFFSET + d, "role": ROLES[d]}})
        rel = f"edits/R_d{d}.json"
        files[rel] = data
        records.append({"path": rel, "family": "R", "draw": d, "seed": SEED_OFFSET + d, "role": ROLES[d],
                        "rows": len(remove), "per_unit": per_unit, "arm": "edit-" + sha256_bytes(data),
                        "sha256": sha256_bytes(data), "bytes": len(data)})
    manifest = {"kind": MANIFEST_KIND, "version": 1,
                "script": {"path": SCRIPT_REL, "sha256": script_sha256, "python": sys.version.split()[0]},
                "frozen_builder": {"path": FROZEN_BUILDER_TMP, "committed_copy": FROZEN_BUILDER_COMMITTED,
                                   "sha256": FROZEN_BUILDER_SHA256,
                                   "used": "Inputs, draw_r(inputs, d), edit_file, EnginePrepared and the R constants"},
                "prepared": {"root": PREPARED_REL, "manifest_sha256": inputs.manifest_sha256,
                             "read": {TRAIN_ROWS: inputs.file_sha256[TRAIN_ROWS], GROUPS: inputs.file_sha256[GROUPS]},
                             "fields_read": "row_id, target_tokens; dev unit membership"},
                "reproduction": {"sealed": {"dir": SEAL_OUT_REL, "manifest_sha256": SEAL_MANIFEST_SHA256,
                                            "files": reproduced["sealed"]},
                                 "stage1_r_draws": {"dir": STAGE1_RDRAWS_REL, "record_sha256": STAGE1_RECORD_SHA256,
                                                    "files": reproduced["stage1_r_draws"]}},
                "engine_identity_sha256": identity, "seed_map": {"offset": SEED_OFFSET, "rule": SEED_RULE},
                "roles": {str(d): ROLES[d] for d in NEW_DRAWS}, "requirement": REQUIREMENT,
                "earlier_draws": {"d = 1-5": SEAL_OUT_REL, "d = 6-10": STAGE1_RDRAWS_REL},
                "files": records}
    files["MANIFEST.json"] = canonical_json(manifest)
    return {"files": files, "manifest": manifest, "records": records}


def write_files(out: Path, files: dict[str, bytes]) -> dict[str, str]:
    out.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        write_atomic(out / name, data)
    digests = {}
    for name, data in files.items():
        digests[name] = sha256_path(out / name)
        if digests[name] != sha256_bytes(data):
            raise Refusal(f"{name} did not read back as written")
    return digests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--frozen-builder", type=Path, default=None,
                        help=f"BLD's path (default <repo>/{FROZEN_BUILDER_COMMITTED})")
    parser.add_argument("--out", type=Path, default=None, help=f"output folder (default <repo>/{OUT_REL}; absent or empty)")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    frozen_path = (args.frozen_builder or repo / FROZEN_BUILDER_COMMITTED).resolve()
    out = (args.out or repo / OUT_REL).resolve()
    try:
        guard_out(out, repo)
        before = sha256_path(frozen_path)
        result = build(repo, frozen_path, repo / PREPARED_REL, repo / SEAL_OUT_REL, repo / STAGE1_RDRAWS_REL)
        written = write_files(out, result["files"])
        if sha256_path(frozen_path) != before or before != FROZEN_BUILDER_SHA256:
            raise Refusal("the frozen builder's bytes changed during the build")
    except Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    print(f"built {len(written)} files into {out}")
    print(f"script sha256 {result['manifest']['script']['sha256']}; frozen builder {FROZEN_BUILDER_SHA256}; "
          f"engine {result['manifest']['engine_identity_sha256']}; prepared {PREPARED_MANIFEST_SHA256}")
    print(f"reproduced: sealed R_d1-R_d5 byte for byte; stage 1 R_d6-R_d10 remove lists equal")
    print(f"MANIFEST.json sha256 {written['MANIFEST.json']}")
    for record in result["records"]:
        print(f"  {record['sha256']}  {record['path']}  arm {record['arm']}  rows {record['rows']}  seed {record['seed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
