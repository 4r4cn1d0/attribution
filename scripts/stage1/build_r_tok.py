"""W1-03: R_tok, token-matched random removal for A1, L1 and H1 (built under addendum §6.5; standard library only; Mac,
$0; the lead runs it on P once the arm's removal file exists).

For arm m with removal file F_m (an engine remove edit, named by SHA-256) and removed token mass T_m on the settings'
axis (default: total row tokens = prompt + target; the alternative: target tokens), and draw d (2, 3, 4; at seed
1100 + d): per unit g in ascending group-id order, walk g's members in the sealed order of registry key
random_removal.rtok with parts (m, d, g); add rows while the unit's mass stays below T_m / 8; at the row whose mass
crosses T_m / 8, keep it only if that brings the unit's mass closer to T_m / 8 (a tie keeps it), and stop. A unit whose
whole mass is below T_m / 8 refuses. This keeps R's per-unit stratification and changes only the dose. The removal is
the sorted union. A secondary arm at 3 seeds, one-sided bounds only; it never enters P1–P6.

Timing: H1's file exists after REQ-5; A1's is committed (`.ai/inputs/stage1-commitments-20261016/a1/a1_remove600.edit.json`,
5c0e53b7…, pinned in the settings); L1's comes after REQ-10's pod output. The same frozen code builds all three.

  python scripts/stage1/build_r_tok.py --prepared P --arm a1 --removal PATH:SHA256 --out OUT

Writes into OUT (absent or empty): edits/R_tok_<arm>_d<d>.json for each draw and r_tok_record.json (text-free: T_m,
the per-unit targets and masses, rows, the token accounting). Prints counts and hashes only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import token_accounting as ta  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "build_r_tok.json"
SETTINGS_SHA256 = "76155178e39d910aab97517fe22e3693c57ec8129f8ba38818ccab850ab4bb77"
SETTINGS_NAME = "build_r_tok"
RECORD = "r_tok_record.json"


def read_removal(path: Path, digest: str, view: s1.PreparedView) -> list[str]:
    """The arm's removal: an engine edit file of kind remove for P, named by SHA-256."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"the removal file cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"the removal file hashes to {sha256_bytes(data)}, expected {digest}")
    _, edit = s1.checked_edit(s1.strict_json(data), view.engine_stub())
    if edit.document["edit_kind"] != "remove" or edit.rewrite or edit.added:
        raise s1.Refusal("the removal file is not a remove-only edit")
    return sorted(edit.removed)


def token_matched(view: ta.TokenView, removed: list[str], arm: str, d: int, axis: str, key: str) -> tuple[list[str], dict]:
    """The R_tok rule (module doc): the sorted removal and its per-unit table."""
    tokens = {"total_tokens": view.total_tokens, "target_tokens": view.target_tokens}[axis]
    mass_m = sum(tokens[r] for r in removed)
    target = mass_m / len(view.units)
    rows, table = [], []
    for g in view.units:
        if sum(tokens[r] for r in view.members[g]) < target:
            raise s1.Refusal(f"unit {g} holds less than T_m / {len(view.units)} on the {axis} axis")
        mass, picked = 0, []
        for r in s1.sealed_order(view.members[g], key, arm, d, g):
            after = mass + tokens[r]
            if after >= target:
                if abs(after - target) <= abs(mass - target):
                    picked.append(r)
                    mass = after
                break
            picked.append(r)
            mass = after
        rows += picked
        table.append({"group_id": g, "category": view.category[g], "rows": len(picked), "mass": mass, "target": target,
                      "seed": s1.seed(key, arm, d, g)})
    return sorted(rows), {"axis": axis, "arm_mass": mass_m, "unit_target": target, "units": table}


def build(prepared: Path, arm: str, removal: tuple[Path, str], settings: dict, settings_sha256: str) -> dict[str, bytes]:
    s1.check_settings(settings, SETTINGS_NAME)
    if arm not in settings["arms"]:
        raise s1.Refusal(f"no arm {arm!r} in the settings")
    spec = settings["arms"][arm]
    pin = spec.get("removal_sha256")
    if pin is not None and removal[1] != pin:
        raise s1.Refusal(f"arm {arm}: the settings pin the removal file {pin}")
    view = s1.PreparedView(prepared, settings["prepared_manifest_sha256"])
    tokens = ta.TokenView(prepared, settings["prepared_manifest_sha256"])
    removed = read_removal(removal[0], removal[1], view)
    if len(removed) != spec["rows"]:
        raise s1.Refusal(f"arm {arm}: the removal holds {len(removed)} rows, the settings say {spec['rows']}")
    prov = s1.provenance(Path(__file__).resolve(), settings_sha256,
                         {"prepared_manifest": view.manifest_sha256, f"removal_{arm}": removal[1]}, settings["label_entries"])
    files, records = {}, []
    for d in settings["draws"]:
        remove, table = token_matched(tokens, removed, arm, d, settings["axis"], settings["key"])
        name = f"stage-1 R_tok for {spec['name']} draw {d}: per unit, random rows up to the arm's token mass / 8 ({len(remove)} rows)"
        doc = s1.edit_document(name=name, edit_kind="remove", manifest_sha256=view.manifest_sha256, remove=remove,
                               provenance={**prov, "arm": arm, "draw": d, "rule": settings["rule"], "table": table})
        data, edit = s1.checked_edit(doc, view.engine_stub())
        rel = f"edits/R_tok_{arm}_d{d}.json"
        files[rel] = data
        records.append({"file": rel, "sha256": edit.sha256, "arm": edit.arm, "draw": d,
                        "seed": settings["seed_offset"] + d, "table": table,
                        "tokens": ta.account(tokens, removed=remove)})
    record = {"kind": "stage1 token-matched random removal", "version": 1, "requirement": settings["requirement"],
              "arm": arm, "removal_sha256": removal[1], "arm_tokens": ta.account(tokens, removed=removed),
              "files": records, "provenance": prov}
    files[RECORD] = canonical_json(record)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--removal", required=True, help="PATH:SHA256 of the arm's remove edit")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        path, _, sha = args.removal.rpartition(":")
        files = build(args.prepared.resolve(), args.arm, (Path(path), sha), settings, digest)
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
