"""Gate B sealed files for OLMo-2-1B on prepared-kt-dolly-olmo2: one pinned build, on the Mac.

Spec: research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md, section 1, "Sealed
files" (revision 2). Anchors are NOT built here (they need model generations).

Standard library only. The seeds come from the engine's own ``derive_seed`` and the edit files
from the engine's own edit-file code (``experiments/safety_selection/edits.py``: EDIT_KIND,
EDIT_VERSION, POSITION_RULE, edit_bytes, arm_of, parse_edit), imported from the checkout that
holds this script. Every edit file is checked with the engine's ``parse_edit`` before anything
is written.

Reads from the prepared set ONLY: manifest.json; engine/train_rows.jsonl (row_id and
target_tokens of each row; no text is kept or printed); engine/groups.json (unit membership).
It never opens banks/, selector/, hidden/, auditor/ or engine/query_rows.jsonl.

Writes into --out (default: out/ next to this script). The folder must not exist or must be
empty. Nothing is written unless every check passes. If a length bin has too few rows for a
matched draw, the build STOPS and reports (no improvised fallback).

  edits/R_d<d>.json          d = 1..5: random removal, 75 rows of each unit (600 rows)
  edits/M_<gid>_d<d>.json    d = 1, 2, each unit: 600 rows of the other 7 units, length-matched
  edits/unit_<gid>.json      each unit: removal of all 600 rows of the unit (completeness)
  gate_c_sample.json         200 rows of each unit (Gate C)
  unit_table.json            counts per unit and per removal file (no text)
  MANIFEST.json              SHA-256 of every file above and of this script; inputs; engine
                             identity; build time (UTC). The only file that is not deterministic.

Choices the spec leaves open, fixed here and recorded in every file they affect:
  * in derive_seed(20261008, "gate-b-length-matched-v2", d, u, b): u is the matched unit's group
    id (as g in the R rule) and b is the 0-based bin index (0 = [1, 8), ..., 6 = [256, inf));
  * the Gate C sample lists each unit's 200 rows sorted by row id (the draw is a set);
  * a removal file's rows are the sorted union of its draws (as the R rule says), for M too.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import inspect
import json
import random
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]                      # <repo>/tmp/gate-b-sealed/build_sealed.py
sys.path.insert(0, str(REPO))

import experiments.minimal_safety.common as _ms_common                     # noqa: E402
from experiments.safety_selection.common import (canonical_json, code_identity, derive_seed,  # noqa: E402
                                                 sha256_bytes, write_atomic)
from experiments.safety_selection.edits import (EDIT_KIND, EDIT_VERSION, POSITION_RULE,  # noqa: E402
                                                arm_of, edit_bytes, parse_edit)

# ----- pinned inputs and constants ----------------------------------------------------------------

PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-olmo2"
PREPARED_MANIFEST_SHA256 = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
TRAIN_ROWS = "engine/train_rows.jsonl"
GROUPS = "engine/groups.json"
SPEC_REL = "research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md"
SPEC_SECTION = "section 1, Sealed files (revision 2)"
BUILDER_REL = "tmp/gate-b-sealed/build_sealed.py"

DESIGN_SEED = 20261008
STREAM_R = "gate-b-random-removal-v1"
STREAM_M = "gate-b-length-matched-v2"
STREAM_C = "gate-c-unit-sample-v1"
R_DRAWS = (1, 2, 3, 4, 5)
R_PER_UNIT = 75
M_DRAWS = (1, 2)
C_PER_UNIT = 200
UNITS = 8
ROWS_PER_UNIT = 600
BIN_EDGES = (1, 8, 16, 32, 64, 128, 256)    # bin b = [BIN_EDGES[b], BIN_EDGES[b + 1]); the last is open
FIRST_K = 5
SHORT_BELOW = 16

POOL_RULE = "every training row that is not a member of a held-out group"
RULE_R = ("for each unit g in ascending group-id order, random.Random(derive_seed(20261008, "
          "'gate-b-random-removal-v1', d, g)).sample(sorted(members_g), 75); remove = the sorted union")
RULE_M = ("target-length bins [1, 8), [8, 16), [16, 32), [32, 64), [64, 128), [128, 256), [256, inf) on "
          "target_tokens; for each bin b, random.Random(derive_seed(20261008, 'gate-b-length-matched-v2', d, u, b))"
          ".sample(sorted(rows of the other 7 units in bin b), n_u,b), n_u,b = unit u's rows in bin b; "
          "remove = the sorted union")
RULE_M_KEYS = ("u = the matched unit's group id; b = the 0-based bin index in ascending order of the lower edge "
               "(0 = [1, 8), ..., 6 = [256, inf)); a bin with n_u,b = 0 draws nothing")
RULE_C = ("per unit g, random.Random(derive_seed(20261008, 'gate-c-unit-sample-v1', g)).sample(sorted(members_g), "
          "200); each unit's rows are listed sorted by row id")
RULE_UNIT = "every member of the unit (the same rows the engine's group-removal arm of that group id removes)"
DEF_FIRST5 = ("mean over rows of min(5, target_tokens) / target_tokens: the share of a row's loss weight on its "
              "first 5 target tokens under the per-example-mean loss, averaged over rows")
DEF_SHORT = "share of rows with target_tokens < 16"


class Stop(SystemExit):
    """A check failed: nothing is written."""


def stop(message: str) -> None:
    raise Stop(f"STOP: {message} (nothing written)")


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def seed_of(*parts: object) -> int:
    """The engine's derive_seed, cross-checked against the prepared manifest's stated formula."""
    value = derive_seed(*parts)
    text = "|".join(str(part) for part in parts)
    if value != int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big"):
        stop(f"the engine's derive_seed disagrees with the stated formula for {parts!r}")
    return value


def bin_of(tokens: int) -> int:
    for b in range(len(BIN_EDGES) - 1, -1, -1):
        if tokens >= BIN_EDGES[b]:
            return b
    stop(f"a row has target_tokens {tokens} < {BIN_EDGES[0]}")
    raise AssertionError


def bin_range(b: int) -> list:
    return [BIN_EDGES[b], BIN_EDGES[b + 1] if b + 1 < len(BIN_EDGES) else None]


def first5(tokens: int) -> float:
    return min(FIRST_K, tokens) / tokens


# ----- inputs ---------------------------------------------------------------------------------------


class Inputs:
    def __init__(self, root: Path):
        manifest_bytes = (root / "manifest.json").read_bytes()
        self.manifest_sha256 = sha256_bytes(manifest_bytes)
        if self.manifest_sha256 != PREPARED_MANIFEST_SHA256:
            stop(f"prepared manifest is {self.manifest_sha256}, expected {PREPARED_MANIFEST_SHA256}")
        manifest = json.loads(manifest_bytes)
        self.seed_derivation = manifest["seed_derivation"]
        self.file_sha256 = {}
        for rel in (TRAIN_ROWS, GROUPS):
            data_sha = sha256_path(root / rel)
            if data_sha != manifest["files"][rel]:
                stop(f"{rel} hashes to {data_sha}, the manifest says {manifest['files'][rel]}")
            self.file_sha256[rel] = data_sha
        # Training rows: row_id and target_tokens only; the text fields are dropped at once.
        self.tokens: dict[str, int] = {}
        with open(root / TRAIN_ROWS, encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                row_id, tokens = row["row_id"], row["target_tokens"]
                del row
                if not isinstance(row_id, str) or row_id in self.tokens:
                    stop("training row ids are not distinct strings")
                if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 1:
                    stop(f"row {row_id} has target_tokens {tokens!r}")
                self.tokens[row_id] = tokens
        if len(self.tokens) != manifest["corpus"]["rows"]:
            stop("the training rows disagree with the manifest's row count")
        partitions = json.loads((root / GROUPS).read_bytes())["partitions"]
        if partitions["heldout"]["groups"] != [] or manifest["groups"]["heldout"]["members"] != 0:
            stop("the held-out partition is not empty: the edit pool would need it excluded")
        self.members = {g["group_id"]: sorted(g["members"]) for g in partitions["dev"]["groups"]}
        self.category = {gid: unit["category"] for gid, unit in manifest["units"].items()}
        self.units = sorted(self.members)
        if len(self.units) != UNITS or set(self.units) != set(self.category):
            stop("the dev groups and the manifest's units differ")
        seen: set[str] = set()
        for gid in self.units:
            rows = self.members[gid]
            if len(rows) != ROWS_PER_UNIT or len(set(rows)) != ROWS_PER_UNIT or seen & set(rows):
                stop(f"unit {gid} does not hold {ROWS_PER_UNIT} distinct rows of its own")
            seen |= set(rows)
        if seen != set(self.tokens):
            stop("the units do not partition the training rows")
        self.unit_of = {row: gid for gid in self.units for row in self.members[gid]}


class EnginePrepared:
    """What the engine's parse_edit reads of a prepared set: row ids, held-out groups, manifest hash."""

    def __init__(self, inputs: Inputs):
        self.manifest_sha256 = inputs.manifest_sha256
        self.train_rows = dict.fromkeys(inputs.tokens)
        self.groups = {"dev": dict(inputs.members), "heldout": {}}


# ----- the draws ------------------------------------------------------------------------------------


def draw_r(inputs: Inputs, d: int) -> tuple[list[str], list[dict]]:
    rows, per_unit = [], []
    for gid in inputs.units:                                       # ascending group id
        seed = seed_of(DESIGN_SEED, STREAM_R, d, gid)
        picked = random.Random(seed).sample(sorted(inputs.members[gid]), R_PER_UNIT)
        rows.extend(picked)
        per_unit.append({"group_id": gid, "category": inputs.category[gid], "seed": seed, "rows": len(picked)})
    if len(set(rows)) != R_PER_UNIT * UNITS:
        stop(f"R_{d} does not hold {R_PER_UNIT * UNITS} distinct rows")
    return sorted(rows), per_unit


def bin_pools(inputs: Inputs) -> dict[str, dict[int, list[str]]]:
    """unit -> bin -> sorted rows of that unit in that bin."""
    pools = {gid: {b: [] for b in range(len(BIN_EDGES))} for gid in inputs.units}
    for row, tokens in inputs.tokens.items():
        pools[inputs.unit_of[row]][bin_of(tokens)].append(row)
    return {gid: {b: sorted(rows) for b, rows in bins.items()} for gid, bins in pools.items()}


def shortfalls(inputs: Inputs, pools: dict) -> list[dict]:
    out = []
    for u in inputs.units:
        for b in range(len(BIN_EDGES)):
            need = len(pools[u][b])
            have = sum(len(pools[v][b]) for v in inputs.units if v != u)
            if have < need:
                out.append({"unit": u, "category": inputs.category[u], "bin": b, "range": bin_range(b),
                            "need": need, "available": have})
    return out


def draw_m(inputs: Inputs, pools: dict, u: str, d: int) -> tuple[list[str], list[dict]]:
    rows, per_bin = [], []
    for b in range(len(BIN_EDGES)):
        need = len(pools[u][b])
        pool = sorted(row for v in inputs.units if v != u for row in pools[v][b])
        seed = seed_of(DESIGN_SEED, STREAM_M, d, u, b)
        picked = random.Random(seed).sample(pool, need)
        rows.extend(picked)
        per_bin.append({"bin": b, "range": bin_range(b), "n": need, "pool": len(pool), "seed": seed})
    if len(set(rows)) != ROWS_PER_UNIT or any(inputs.unit_of[r] == u for r in rows):
        stop(f"M_{u},{d} is not {ROWS_PER_UNIT} distinct rows outside the unit")
    return sorted(rows), per_bin


def draw_c(inputs: Inputs) -> list[dict]:
    out = []
    for gid in inputs.units:
        seed = seed_of(DESIGN_SEED, STREAM_C, gid)
        picked = random.Random(seed).sample(sorted(inputs.members[gid]), C_PER_UNIT)
        out.append({"group_id": gid, "category": inputs.category[gid], "seed": seed, "rows": sorted(picked)})
    return out


# ----- documents ------------------------------------------------------------------------------------


def common_provenance(inputs: Inputs, builder_sha256: str, derive_seed_source_sha256: str) -> dict:
    return {"builder": BUILDER_REL, "builder_sha256": builder_sha256,
            "spec": f"{SPEC_REL}, {SPEC_SECTION}",
            "inputs": {"prepared": PREPARED_REL, "manifest_sha256": inputs.manifest_sha256,
                       TRAIN_ROWS: inputs.file_sha256[TRAIN_ROWS], GROUPS: inputs.file_sha256[GROUPS],
                       "fields_read": "row_id and target_tokens of each training row; dev unit membership"},
            "derive_seed": {"function": "experiments.minimal_safety.common.derive_seed "
                                        "(re-exported by experiments.safety_selection.common)",
                            "source_sha256": derive_seed_source_sha256, "formula": inputs.seed_derivation},
            "pool": {"rule": POOL_RULE, "training_rows": len(inputs.tokens), "pool_rows": len(inputs.tokens),
                     "heldout_members_excluded": 0}}


def edit_file(inputs: Inputs, name: str, remove: list[str], provenance: dict,
              engine_prepared: EnginePrepared) -> tuple[bytes, str]:
    doc = {"kind": EDIT_KIND, "version": EDIT_VERSION, "name": name, "edit_kind": "remove",
           "manifest_sha256": inputs.manifest_sha256, "remove": sorted(remove), "rewrite": [], "add": [],
           "position_rule": POSITION_RULE, "counts": {"remove": len(remove), "rewrite": 0, "add": 0},
           "provenance": provenance}
    data = edit_bytes(doc)
    edit = parse_edit(data, engine_prepared)                       # the engine's own checks
    if edit.removed != frozenset(remove) or edit.arm != arm_of(data) or edit.document != doc:
        stop(f"the engine reads {name!r} differently from what was written")
    return data, arm_of(data)


def removal_stats(inputs: Inputs, removed: list[str]) -> dict:
    removed_set = set(removed)
    gone = [inputs.tokens[r] for r in removed]
    rest = [t for r, t in inputs.tokens.items() if r not in removed_set]
    by_unit = {gid: 0 for gid in inputs.units}
    for r in removed:
        by_unit[inputs.unit_of[r]] += 1
    return {"rows_removed": len(gone), "token_mass_removed": sum(gone),
            "first5_share_removed": round(sum(map(first5, gone)) / len(gone), 6),
            "short_share_removed": round(sum(t < SHORT_BELOW for t in gone) / len(gone), 6),
            "rows_kept": len(rest), "first5_share_kept": round(sum(map(first5, rest)) / len(rest), 6),
            "rows_removed_by_unit": by_unit}


def unit_rows(inputs: Inputs, pools: dict) -> list[dict]:
    out = []
    for gid in inputs.units:
        ts = [inputs.tokens[r] for r in inputs.members[gid]]
        out.append({"group_id": gid, "category": inputs.category[gid], "rows": len(ts), "token_mass": sum(ts),
                    "median_target_tokens": statistics.median(ts),
                    "first5_share": round(sum(map(first5, ts)) / len(ts), 6),
                    "short_share": round(sum(t < SHORT_BELOW for t in ts) / len(ts), 6),
                    "short_rows": sum(t < SHORT_BELOW for t in ts),
                    "rows_by_bin": [len(pools[gid][b]) for b in range(len(BIN_EDGES))]})
    return out


# ----- build ----------------------------------------------------------------------------------------


def build(out: Path) -> None:
    if out.exists() and any(out.iterdir()):
        stop(f"{out} exists and is not empty: a sealed build never overwrites")
    builder_sha256 = sha256_path(Path(__file__).resolve())
    if derive_seed is not _ms_common.derive_seed or not inspect.isfunction(derive_seed):
        stop("experiments.safety_selection.common.derive_seed is not the minimal-safety function")
    source_lines, first_line = inspect.getsourcelines(derive_seed)
    derive_seed_source_sha256 = sha256_bytes("".join(source_lines).encode("utf-8"))
    derive_seed_file = Path(inspect.getsourcefile(derive_seed)).resolve()

    inputs = Inputs(REPO / PREPARED_REL)
    engine_prepared = EnginePrepared(inputs)
    pools = bin_pools(inputs)
    short = shortfalls(inputs, pools)
    if short:
        lines = "\n".join(f"  unit {s['unit']} ({s['category']}) bin {s['bin']} {s['range']}: needs {s['need']}, "
                          f"the other 7 units hold {s['available']}" for s in short)
        stop(f"length-matched draw impossible in {len(short)} bin(s):\n{lines}\n")
    base = common_provenance(inputs, builder_sha256, derive_seed_source_sha256)

    files: dict[str, bytes] = {}
    records: list[dict] = []
    stats: list[dict] = []

    def add_edit(rel: str, name: str, remove: list[str], selection: dict, record: dict) -> None:
        data, arm = edit_file(inputs, name, remove, {**base, "selection": selection}, engine_prepared)
        files[rel] = data
        records.append({"path": rel, "role": "edit", "arm": arm, **record})
        stats.append({"path": rel, "arm": arm, **record, **removal_stats(inputs, remove)})

    for d in R_DRAWS:
        remove, per_unit = draw_r(inputs, d)
        add_edit(f"edits/R_d{d}.json", f"gate-b R_{d}: remove {R_PER_UNIT} rows of each of the {UNITS} units at "
                 f"random ({len(remove)} rows)", remove,
                 {"family": "R", "draw": d, "design_seed": DESIGN_SEED, "stream": STREAM_R, "rule": RULE_R,
                  "per_unit": per_unit}, {"family": "R", "draw": d})
    for u in inputs.units:
        for d in M_DRAWS:
            remove, per_bin = draw_m(inputs, pools, u, d)
            by_unit = {v: sum(inputs.unit_of[r] == v for r in remove) for v in inputs.units if v != u}
            add_edit(f"edits/M_{u}_d{d}.json", f"gate-b M_u,{d} for unit {u} ({inputs.category[u]}): remove "
                     f"{len(remove)} rows of the other 7 units, length-matched to the unit", remove,
                     {"family": "M", "draw": d, "matched_unit": u, "matched_category": inputs.category[u],
                      "design_seed": DESIGN_SEED, "stream": STREAM_M, "rule": RULE_M, "keys": RULE_M_KEYS,
                      "length_field": "target_tokens", "per_bin": per_bin, "rows_by_source_unit": by_unit},
                     {"family": "M", "draw": d, "unit": u, "category": inputs.category[u]})
    for u in inputs.units:
        add_edit(f"edits/unit_{u}.json", f"gate-b unit removal {u} ({inputs.category[u]}): remove all "
                 f"{ROWS_PER_UNIT} rows of the unit", list(inputs.members[u]),
                 {"family": "unit", "unit": u, "category": inputs.category[u], "rule": RULE_UNIT},
                 {"family": "unit", "unit": u, "category": inputs.category[u]})

    sample = draw_c(inputs)
    if any(len(set(s["rows"])) != C_PER_UNIT or not set(s["rows"]) <= set(inputs.members[s["group_id"]])
           for s in sample):
        stop("the Gate C sample is not 200 distinct members per unit")
    files["gate_c_sample.json"] = canonical_json(
        {"kind": "gate-c unit sample", "version": 1, "manifest_sha256": inputs.manifest_sha256,
         "design_seed": DESIGN_SEED, "stream": STREAM_C, "rule": RULE_C, "per_unit": C_PER_UNIT,
         "rows": C_PER_UNIT * UNITS, "units": sample, "provenance": base})
    records.append({"path": "gate_c_sample.json", "role": "gate-c sample", "rows": C_PER_UNIT * UNITS})

    every = list(inputs.tokens.values())
    files["unit_table.json"] = canonical_json(
        {"kind": "gate-b unit table", "version": 1, "manifest_sha256": inputs.manifest_sha256,
         "definitions": {"token_mass": "sum of target_tokens", "first5_share": DEF_FIRST5,
                         "short_share": DEF_SHORT, "first5_share_kept": "first5_share of the rows a removal keeps",
                         "bins": [bin_range(b) for b in range(len(BIN_EDGES))]},
         "all_rows": {"rows": len(every), "token_mass": sum(every),
                      "first5_share": round(sum(map(first5, every)) / len(every), 6),
                      "short_share": round(sum(t < SHORT_BELOW for t in every) / len(every), 6)},
         "units": unit_rows(inputs, pools), "removal_files": stats, "provenance": base})
    records.append({"path": "unit_table.json", "role": "counts"})
    for record in records:
        record["sha256"] = sha256_bytes(files[record["path"]])
        record["bytes"] = len(files[record["path"]])

    try:
        head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = None
    identity = code_identity()
    manifest = {
        "kind": "gate-b sealed files manifest", "version": 1,
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "builder": {"path": BUILDER_REL, "sha256": builder_sha256, "python": sys.version.split()[0],
                    "executable": sys.executable},
        "spec": {"path": SPEC_REL, "section": SPEC_SECTION, "sha256_at_build": sha256_path(REPO / SPEC_REL)},
        "prepared": {"root": PREPARED_REL, "manifest_sha256": inputs.manifest_sha256,
                     "read": {TRAIN_ROWS: inputs.file_sha256[TRAIN_ROWS], GROUPS: inputs.file_sha256[GROUPS]},
                     "fields_read": "row_id, target_tokens; dev unit membership",
                     "never_opened": ["banks/", "selector/", "hidden/", "auditor/", "engine/query_rows.jsonl"]},
        "engine": {"code_identity_sha256": identity["sha256"], "git_head": head,
                   "derive_seed": {"file": str(derive_seed_file.relative_to(REPO)),
                                   "lines": [first_line, first_line + len(source_lines) - 1],
                                   "file_sha256": sha256_path(derive_seed_file),
                                   "source_sha256": derive_seed_source_sha256,
                                   "reexported_by": "experiments/safety_selection/common.py"},
                   "edit_conventions": {"file": "experiments/safety_selection/edits.py",
                                        "file_sha256": identity["files"]["safety_selection/edits.py"],
                                        "used": "EDIT_KIND, EDIT_VERSION, POSITION_RULE, edit_bytes (canonical "
                                                "JSON), arm_of (edit-<SHA-256 of the bytes>), parse_edit"}},
        "choices": {"m_seed_keys": RULE_M_KEYS, "gate_c_order": "each unit's 200 rows sorted by row id",
                    "remove_lists": "sorted union of the draws"},
        "not_built": "anchors (they need model generations)",
        "files": records}
    files["MANIFEST.json"] = canonical_json(manifest)

    out.mkdir(parents=True, exist_ok=True)
    for rel, data in files.items():
        write_atomic(out / rel, data)
    for rel, data in files.items():                               # read back
        if sha256_path(out / rel) != sha256_bytes(data):
            stop(f"{rel} did not read back as written")

    print(f"built {len(files)} files into {out}")
    print(f"builder sha256 {builder_sha256}; engine {identity['sha256']}; prepared {inputs.manifest_sha256}")
    print(f"MANIFEST.json sha256 {sha256_bytes(files['MANIFEST.json'])}")
    for record in records:
        print(f"  {record['sha256']}  {record['path']}" + (f"  arm {record['arm']}" if "arm" in record else ""))
    print("unit table (counts only):")
    for row in unit_rows(inputs, pools):
        print(f"  {row['group_id']}  {row['category']:<24} rows {row['rows']}  tokens {row['token_mass']:>7}  "
              f"median {row['median_target_tokens']:>6}  first5 {row['first5_share']:.3f}  "
              f"short<16 {row['short_share']:.3f}  bins {row['rows_by_bin']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=HERE / "out", help="output folder (must be absent or empty)")
    args = parser.parse_args(argv)
    build(args.out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
