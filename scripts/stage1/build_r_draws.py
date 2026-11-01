"""REQ-4: the random-removal draws of stage 1 (standard library only; Mac, $0; the lead runs it on P).

1. **Reproduce first.** The frozen Gate B builder (.ai/inputs/gate-b-sealed-20261008/build_sealed.py, SHA-256 pinned)
   is loaded by path, never copied or edited. For d = 1..5 its own draw (draw_r) and its own edit writer, with its own
   provenance, must give byte-for-byte the sealed files edits/R_d<d>.json listed in the sealed MANIFEST.json (SHA-256
   pinned); any difference refuses and nothing is written.
2. **R_d for d = 6..10** (seed layout D1, addendum §6.2: R at 1101–1107, so d = 6, 7; plan B, LW-31: R at 1101–1110, so
   d = 8, 9, 10 as well; outcome-free, so all are built now). Each is the frozen builder's own draw_r and edit format
   (75 rows per unit, gate-b-random-removal-v1, parts (d, g)); the provenance names the frozen builder's SHA-256 and this
   wrapper's and settings' SHA-256. Draw d runs at seed 1100 + d; the seed map (L5) is pinned in the settings and in
   every edit's provenance (seed and seed_rule: in stage1_wrapper for R_d, at the top level for R_1200 and R_2400).
3. **R_1200 and R_2400** (PLAN-S:159; L5): per unit g (ascending group id), a sealed sample of 150 (300) of g's sorted
   members by registry key random_removal.r1200 (r2400) with parts (d, g), the form of Gate B's R rule; remove = the
   sorted union; draws d = 2, 3, 4 at seeds 1102–1104. Each is an independent draw (not nested in R_600).
R+S1 (R_d with S1's 48 add rows, d = 2..4) is written by REQ-7's add writer from these files.

Writes into --out (absent or empty): edits/<name>.json (row ids only) and r_draws_record.json (text-free: each file's
SHA-256, arm, draw, seed, per-unit counts and the token accounting of token_accounting.account). Prints counts and
hashes only.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import token_accounting as ta  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "build_r_draws.json"
SETTINGS_SHA256 = "71fdcf32601cef4858b78c7c02702874df1a76e7ea4b05718078f84799758954"
SETTINGS_NAME = "build_r_draws"
RECORD = "r_draws_record.json"


def load_frozen(path: Path, expected_sha256: str) -> ModuleType:
    """The frozen Gate B builder, by path, after its SHA-256 check (never copied or edited)."""
    data = path.read_bytes()
    if sha256_bytes(data) != expected_sha256:
        raise s1.Refusal(f"the frozen builder hashes to {sha256_bytes(data)}, the pin is {expected_sha256}")
    spec = importlib.util.spec_from_file_location("stage1_frozen_build_sealed", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recorded_base(sealed_dir: Path, inputs, builder_sha256: str) -> dict:
    """The frozen builder's recorded provenance block (from the sealed R_d1 file, without its selection), checked
    against the current inputs; the byte reproduction of R_d1..5 then proves it is the block the builder writes."""
    base = dict(s1.strict_json((sealed_dir / "edits" / "R_d1.json").read_bytes())["provenance"])
    base.pop("selection", None)
    recorded = base.get("inputs") or {}
    if base.get("builder_sha256") != builder_sha256:
        raise s1.Refusal("the sealed files were not written by the pinned frozen builder")
    files = (s1.TRAIN_ROWS, s1.GROUPS)
    if [recorded.get("manifest_sha256")] + [recorded.get(f) for f in files] != \
            [inputs.manifest_sha256] + [inputs.file_sha256[f] for f in files]:
        raise s1.Refusal("the sealed files were written for another prepared set")
    return base


def frozen_r_file(frozen: ModuleType, inputs, d: int, base: dict, extra: dict | None = None) -> tuple[bytes, list[str], list]:
    """R_d by the frozen builder's draw_r and edit_file, with its own name, selection and provenance (plus extra)."""
    remove, per_unit = frozen.draw_r(inputs, d)
    name = (f"gate-b R_{d}: remove {frozen.R_PER_UNIT} rows of each of the {frozen.UNITS} units at random "
            f"({len(remove)} rows)")
    selection = {"family": "R", "draw": d, "design_seed": frozen.DESIGN_SEED, "stream": frozen.STREAM_R,
                 "rule": frozen.RULE_R, "per_unit": per_unit}
    data, _ = frozen.edit_file(inputs, name, remove, {**base, "selection": selection, **(extra or {})},
                               frozen.EnginePrepared(inputs))
    return data, remove, per_unit


def check_reproduction(frozen: ModuleType, inputs, base: dict, sealed_dir: Path, sealed_manifest_sha256: str,
                       draws: list[int]) -> dict:
    """For each d: the frozen builder's R_d bytes equal the sealed file, which the pinned sealed manifest lists."""
    manifest_bytes = (sealed_dir / "MANIFEST.json").read_bytes()
    if sha256_bytes(manifest_bytes) != sealed_manifest_sha256:
        raise s1.Refusal(f"the sealed MANIFEST.json hashes to {sha256_bytes(manifest_bytes)}, the pin is "
                         f"{sealed_manifest_sha256}")
    listed = {f["path"]: f["sha256"] for f in s1.strict_json(manifest_bytes)["files"]}
    out = {}
    for d in draws:
        rel = f"edits/R_d{d}.json"
        sealed = (sealed_dir / rel).read_bytes()
        if listed.get(rel) != sha256_bytes(sealed):
            raise s1.Refusal(f"{rel} is not the file the sealed manifest lists")
        data, remove, _ = frozen_r_file(frozen, inputs, d, base)
        if s1.strict_json(sealed)["remove"] != remove:
            raise s1.Refusal(f"R_{d}: the frozen builder's draw differs from the sealed remove list")
        if data != sealed:
            raise s1.Refusal(f"R_{d}: the frozen builder's file differs from the sealed bytes")
        out[str(d)] = {"sha256": sha256_bytes(sealed), "rows": len(remove), "byte_identical": True}
    return out


def dose_draw(view: s1.PreparedView, key: str, per_unit: int, d: int) -> tuple[list[str], list[dict]]:
    """Per unit (ascending group id) a sealed sample of per_unit members by key, parts (d, g); the sorted union."""
    rows, table = [], []
    for g in view.units:
        picked = s1.sealed_sample(view.members[g], per_unit, key, d, g)
        rows += picked
        table.append({"group_id": g, "category": view.category[g], "seed": s1.seed(key, d, g), "rows": len(picked)})
    if len(set(rows)) != per_unit * len(view.units):
        raise s1.Refusal(f"{key} draw {d} does not hold distinct rows")
    return sorted(rows), table


def build(prepared: Path, frozen_path: Path, sealed_dir: Path, settings: dict, settings_sha256: str) -> dict[str, bytes]:
    """Every output file (nothing is written here)."""
    s1.check_settings(settings, SETTINGS_NAME)
    pins = settings["inputs"]
    frozen = load_frozen(frozen_path, pins["frozen_builder_sha256"])
    try:
        inputs = frozen.Inputs(prepared)                         # the frozen builder's own checks of P
    except SystemExit as exc:                                    # its Stop: ids and counts only
        raise s1.Refusal(f"the frozen builder refuses the prepared set ({exc})") from None
    view = s1.PreparedView(prepared, pins["prepared_manifest_sha256"])
    tokens = ta.TokenView(prepared, pins["prepared_manifest_sha256"])
    base = recorded_base(sealed_dir, inputs, pins["frozen_builder_sha256"])
    reproduced = check_reproduction(frozen, inputs, base, sealed_dir, pins["sealed_manifest_sha256"],
                                    settings["reproduce"]["draws"])
    wrapper = s1.provenance(Path(__file__).resolve(), settings_sha256,
                            {"prepared_manifest": view.manifest_sha256, "frozen_builder": pins["frozen_builder_sha256"],
                             "sealed_manifest": pins["sealed_manifest_sha256"]}, settings["label_entries"])
    files: dict[str, bytes] = {}
    records = []
    seed_of, seed_rule = settings["seed_map"]["offset"], settings["seed_map"]["rule"]
    for d in settings["frozen_r"]["draws"]:
        # L5: the seed map (draw d at seed 1100 + d) in each edit's provenance; here in the wrapper's own block
        data, remove, per_unit = frozen_r_file(frozen, inputs, d, base,
                                               {"stage1_wrapper": {**wrapper, "seed": seed_of + d, "seed_rule": seed_rule}})
        rel = f"edits/R_d{d}.json"
        files[rel] = data
        records.append({"file": rel, "sha256": sha256_bytes(data), "arm": "edit-" + sha256_bytes(data), "family": "R",
                        "draw": d, "seed": seed_of + d, "role": settings["frozen_r"]["roles"][str(d)],
                        "per_unit": per_unit, "tokens": ta.account(tokens, removed=remove)})
    for family, spec in settings["doses"].items():
        for d in spec["draws"]:
            remove, table = dose_draw(view, spec["key"], spec["per_unit"], d)
            name = (f"stage-1 {family} draw {d}: remove {spec['per_unit']} rows of each of the {len(view.units)} "
                    f"units at random ({len(remove)} rows)")
            doc = s1.edit_document(name=name, edit_kind="remove", manifest_sha256=view.manifest_sha256, remove=remove,
                                   provenance={**wrapper, "family": family, "draw": d, "seed": seed_of + d,
                                               "seed_rule": seed_rule, "rule": spec["rule"], "per_unit": table})
            data, edit = s1.checked_edit(doc, view.engine_stub())
            rel = f"edits/{family}_d{d}.json"
            files[rel] = data
            records.append({"file": rel, "sha256": edit.sha256, "arm": edit.arm, "family": family, "draw": d,
                            "seed": seed_of + d, "role": spec["role"], "per_unit": table,
                            "tokens": ta.account(tokens, removed=remove)})
    record = {"kind": "stage1 random-removal draws", "version": 1, "requirement": settings["requirement"],
              "reproduction": reproduced, "files": records, "seed_map": settings["seed_map"],
              "provenance": wrapper}
    files[RECORD] = canonical_json(record)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        pins = settings["inputs"]
        files = build(args.prepared.resolve(), s1.REPO / pins["frozen_builder"], s1.REPO / pins["sealed_dir"],
                      settings, digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    print(f"wrote {len(written)} files into {args.out}")
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
