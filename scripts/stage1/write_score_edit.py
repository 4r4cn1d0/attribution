"""Score-to-edit writer and the A1 removal contract (REQ-14; standard library only; Mac, $0).

One rule for every stage-1 removal arm that comes from a per-row score (SPEC section 1): a float64
score for every training row of the prepared set; the k rows with the largest scores are removed
(global over all rows, never per unit); ties go by the sealed rank of the arm's registry key; the
edit file is written in the engine's own format and parsed back with the engine's own
``parse_edit``. The settings file ``settings/write_score_edit.json`` (pinned by SHA-256 below) fixes
every number and rule.

Commands:

  a1      The A1 contract. Reads the wave-0b attributes unit (its COMPLETE.json pinned by SHA-256 in
          the settings) after the checks of the frozen reading's rankings phase: the unit's own files
          verify; kind attributes, seed 1101, split dev, the sealed anchor bank, the 8 units; engine X;
          recipe S; both checkpoint sources name the pinned retrain. Per row,
          a_i = mean over c in [q, e1] of (cosine_harmful(i, c) - cosine_safe(i, c)) from rows.jsonl
          (the checkpoint_gradsim variant; no other field is read). For each unit, the mean of its
          rows' a_i must equal groups.json's bi_anchored checkpoint_gradsim within 1e-12, or the
          writer refuses. Then the 600 largest a_i are removed.
  scorer  The generic path for a stage-1 scorer output (L1, DataShield-style, Self-Inf-N-style),
          named by its SHA-256 on the command line.

Writes into --out (absent or empty): <arm>_remove600.edit.json (the edit file: row ids only) and
<arm>_selection.json (the text-free record: scores, the selected set, unit scores, token mass,
category mix, per-unit counts, the one-category flag, the consistency check, costs and the effective
settings section). Every input file is hashed and parsed from the same bytes. Prints counts and
hashes only. Exit 0: written; exit 2: refused, nothing written.

Scope: the A1 contract and its golden test are defined on engine X (472fc7f6…); the settings pin X,
so after an engine change (round Y) they refuse until a new pin is made.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from statistics import fmean

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from experiments.safety_selection.ledger import verify_files  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "write_score_edit.json"
SETTINGS_SHA256 = "9fc5f359133e76fd464b13ed34eb13eb74bf25d71edeb0add0c8d8eae992f9b5"
SETTINGS_NAME = "write_score_edit"
RECORD_KIND = "stage1 score selection"


# ----- the A1 contract ------------------------------------------------------------------------------


def check_attributes_unit(folder: Path, unit_cfg: dict, view: s1.PreparedView) -> dict:
    """The attributes unit's checked marker and file hashes (the frozen reading's rankings checks)."""
    complete = folder / "COMPLETE.json"
    if not complete.is_file():
        raise s1.Refusal("the attributes unit has no COMPLETE.json")
    complete_bytes = complete.read_bytes()
    complete_sha256 = sha256_bytes(complete_bytes)
    if complete_sha256 != unit_cfg["complete_sha256"]:
        raise s1.Refusal(f"the attributes unit's COMPLETE.json hashes to {complete_sha256}, "
                         f"the settings pin {unit_cfg['complete_sha256']}")
    problems = verify_files(folder)
    if problems:
        raise s1.Refusal(f"the attributes unit's own files do not verify ({len(problems)} problems)")
    marker = s1.strict_json(complete_bytes)
    listed = marker.get("files") if isinstance(marker.get("files"), dict) else {}
    data: dict[str, bytes] = {}
    for name in ("job.json", "rows.jsonl", "groups.json"):
        data[name] = (folder / name).read_bytes()               # hashed and parsed from these same bytes
        if sha256_bytes(data[name]) != listed.get(name):
            raise s1.Refusal(f"the attributes unit's {name} is not the file COMPLETE.json lists")
    job = s1.strict_json(data["job.json"])
    identity = marker.get("identity") or {}
    checks = {
        "marker kind": marker.get("kind") == unit_cfg["kind"] and marker.get("complete") is True,
        "job kind": job.get("kind") == unit_cfg["kind"],
        "seed": job.get("seed") == unit_cfg["seed"] and marker.get("seed") == unit_cfg["seed"],
        "split": job.get("split") == unit_cfg["split"] and marker.get("split") == unit_cfg["split"],
        "query bank": (job.get("query_bank") == unit_cfg["query_bank"]
                       and marker.get("query_bank") == unit_cfg["query_bank"]
                       and marker.get("query_bank_sha256") == unit_cfg["query_bank_sha256"]),
        "anchor counts": marker.get("anchor_counts") == unit_cfg["anchor_counts"],
        "units": (sorted(job.get("group_ids") or []) == view.units
                  and sorted(marker.get("group_ids") or []) == view.units),
        "checkpoints": marker.get("checkpoints") == unit_cfg["checkpoints"],
        "engine": identity.get("code_sha256") == unit_cfg["code_sha256"],
        "recipe": identity.get("recipe_sha256") == unit_cfg["recipe_sha256"],
        "prepared": identity.get("manifest_sha256") == view.manifest_sha256,
        "sources": all(((marker.get("sources") or {}).get(c) or {}).get("complete_sha256")
                       == unit_cfg["retrain_complete_sha256"] for c in unit_cfg["checkpoints"]),
    }
    failed = sorted(name for name, ok in checks.items() if not ok)
    if failed:
        raise s1.Refusal(f"the attributes unit fails the checks: {', '.join(failed)}")
    files = {name: sha256_bytes(raw) for name, raw in data.items()}
    costs = marker.get("costs")
    return {"complete_sha256": complete_sha256, "files": files, "bytes": data,
            "costs": costs if isinstance(costs, dict) else None}


def a1_scores(rows_bytes: bytes, cfg: dict, view: s1.PreparedView) -> dict[str, float]:
    """a_i for every training row, from rows.jsonl's bytes (cfg: checkpoints, sets, field, record fields)."""
    checkpoints, plus, minus, field = cfg["checkpoints"], cfg["minuend_set"], cfg["subtrahend_set"], cfg["row_field"]
    required, optional = set(cfg["row_record_fields"]), set(cfg["row_record_optional"])
    scores: dict[str, float] = {}
    for number, row in enumerate(s1.iter_jsonl_bytes(rows_bytes, "rows.jsonl"), 1):
        if set(row) != {"row_id", "group_id", "per_checkpoint"}:
            raise s1.Refusal(f"rows.jsonl line {number}: not exactly row_id, group_id, per_checkpoint")
        row_id = row["row_id"]
        if not isinstance(row_id, str) or row_id not in view.tokens or row_id in scores:
            raise s1.Refusal(f"rows.jsonl line {number}: the row id is unknown or repeated")
        if row["group_id"] != view.unit_of[row_id]:
            raise s1.Refusal(f"rows.jsonl line {number}: the group id is not the row's unit")
        per = row["per_checkpoint"]
        if not isinstance(per, dict) or set(per) != set(checkpoints):
            raise s1.Refusal(f"rows.jsonl line {number}: the checkpoints are not {checkpoints}")
        differences = []
        for c in checkpoints:
            sets = per[c]
            if not isinstance(sets, dict) or set(sets) != {plus, minus}:
                raise s1.Refusal(f"rows.jsonl line {number}: checkpoint {c} does not hold the sets {plus}, {minus}")
            values = {}
            for name in (plus, minus):
                record = sets[name]
                if not isinstance(record, dict) or not required <= set(record) <= required | optional:
                    raise s1.Refusal(f"rows.jsonl line {number}: checkpoint {c} set {name} has other fields")
                value = record[field]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise s1.Refusal(f"rows.jsonl line {number}: checkpoint {c} set {name}: {field} is not finite")
                values[name] = float(value)
            differences.append(values[plus] - values[minus])
        scores[row_id] = fmean(differences)
    missing = len(set(view.tokens) - set(scores))
    if missing:
        raise s1.Refusal(f"rows.jsonl misses {missing} training rows")
    return scores


def check_consistency(scores: dict[str, float], groups_doc: dict, cfg: dict, view: s1.PreparedView) -> dict:
    """For each unit: the mean of its rows' a_i against groups.json's bi-anchored value (refuse past the
    tolerance)."""
    if groups_doc.get("bi_anchored_sign") != cfg["bi_anchored_sign"]:
        raise s1.Refusal("groups.json states another bi-anchored sign than the settings")
    if cfg["variant"] not in (groups_doc.get("variants") or []):
        raise s1.Refusal(f"groups.json does not list the variant {cfg['variant']}")
    groups = groups_doc.get("groups") or {}
    if sorted(groups) != view.units:
        raise s1.Refusal("groups.json does not hold exactly the prepared set's units")
    tolerance = cfg["consistency"]["abs_tolerance"]
    out = {}
    for unit in view.units:
        value = (groups[unit].get("bi_anchored") or {}).get(cfg["variant"])
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise s1.Refusal(f"groups.json unit {unit}: no finite bi-anchored {cfg['variant']}")
        mean = fmean(scores[row] for row in view.members[unit])
        difference = abs(mean - value)
        if not difference <= tolerance:
            raise s1.Refusal(f"unit {unit}: the mean of its rows' a_i differs from groups.json by {difference:.3e} "
                             f"(tolerance {tolerance:.0e})")
        out[unit] = {"rows_mean": mean, "groups_value": float(value), "abs_difference": difference}
    return out


# ----- the shared removal path ----------------------------------------------------------------------


def removal_files(view: s1.PreparedView, arm: dict, scores: dict[str, float], settings: dict, settings_sha256: str,
                  inputs: dict[str, str], extra: dict) -> dict[str, bytes]:
    """The edit file and the selection record of one arm (SPEC section 1)."""
    selected = s1.select_top(scores, arm["k"], arm["ties"], expected_ids=view.tokens)
    prov = s1.provenance(Path(__file__).resolve(), settings_sha256, inputs, settings["label_entries"])
    document = s1.edit_document(name=arm["edit_name"], edit_kind="remove", manifest_sha256=view.manifest_sha256,
                                remove=selected,
                                provenance={**prov, "arm": arm["arm"], "rule": arm["rule"], "k": arm["k"],
                                            "ties_key": arm["ties"]})
    data, edit = s1.checked_edit(document, view.engine_stub())
    if edit.removed != frozenset(selected) or len(edit.removed) != arm["k"]:
        raise s1.Refusal(f"the {arm['arm']} edit does not remove exactly the {arm['k']} selected rows")
    record = {"kind": RECORD_KIND, "version": 1, "arm": arm["arm"], "requirement": arm["requirement"],
              "rule": arm["rule"], "orientation": arm["orientation"], "k": arm["k"], "ties_key": arm["ties"],
              "edit": {"file": arm["outputs"]["edit"], "sha256": edit.sha256, "arm": edit.arm, "bytes": len(data)},
              "selected": sorted(selected), "selection_order": selected,
              "boundary": s1.boundary_ties(scores, selected),
              "scores": dict(sorted(scores.items())),
              "unit_scores": {u: fmean(scores[r] for r in view.members[u]) for u in view.units},
              "stats": s1.report_stats(view, removed=selected, flag_share=arm["category_flag_share"]),
              "jaccard_set": "selected", "settings_section": arm, "provenance": prov, **extra}
    return {arm["outputs"]["edit"]: data, arm["outputs"]["record"]: canonical_json(record)}


def view_of(prepared: Path, settings: dict) -> s1.PreparedView:
    pins = settings["prepared"]
    view = s1.PreparedView(prepared, pins["manifest_sha256"])
    view.check_shape(pins["rows"], pins["units"], pins["rows_per_unit"])
    return view


def build_a1(prepared: Path, unit_dir: Path, settings: dict, settings_sha256: str) -> dict[str, bytes]:
    """Every output file of the A1 contract (nothing is written here)."""
    s1.check_settings(settings, SETTINGS_NAME)
    cfg = settings["a1"]
    view = view_of(prepared, settings)
    unit = check_attributes_unit(unit_dir, cfg["attributes_unit"], view)
    scores = a1_scores(unit["bytes"]["rows.jsonl"], cfg, view)
    consistency = check_consistency(scores, s1.strict_json(unit["bytes"]["groups.json"]), cfg, view)
    inputs = {"prepared_manifest": view.manifest_sha256, "prepared_train_rows": view.file_sha256[s1.TRAIN_ROWS],
              "prepared_groups": view.file_sha256[s1.GROUPS], "attributes_complete": unit["complete_sha256"],
              **{f"attributes_{name.split('.')[0]}": digest for name, digest in unit["files"].items()}}
    extra = {"consistency": {"rule": cfg["consistency"]["rule"], "abs_tolerance": cfg["consistency"]["abs_tolerance"],
                             "units": consistency},
             "attributes_unit": {"complete_sha256": unit["complete_sha256"], "files": unit["files"]},
             "costs": unit["costs"]}
    return removal_files(view, cfg, scores, settings, settings_sha256, inputs, extra)


def read_scorer_output(path: Path, expected_sha256: str, name: str, settings: dict,
                       view: s1.PreparedView) -> tuple[dict[str, float], dict]:
    """A stage-1 scorer output named by its SHA-256, in the schema of the settings."""
    data = path.read_bytes()
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise s1.Refusal(f"the scorer output hashes to {digest}, expected {expected_sha256}")
    schema = settings["scorer_output"]
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or sorted(doc) != schema["keys"]:
        raise s1.Refusal("the scorer output does not hold exactly the schema's keys")
    if (doc["kind"], doc["version"], doc["scorer"]) != (schema["kind"], schema["version"], name):
        raise s1.Refusal(f"not a version-{schema['version']} scorer output of {name}")
    if doc["manifest_sha256"] != view.manifest_sha256:
        raise s1.Refusal("the scorer output was made for another prepared set")
    if doc["orientation"] != settings["scorers"][name]["orientation"]:
        raise s1.Refusal("the scorer output states another orientation than the settings")
    prov = doc["provenance"]
    if not isinstance(prov, dict) or not all(isinstance(prov.get(k), str) and s1.HEX64.match(prov[k])
                                             for k in schema["provenance_required"]):
        raise s1.Refusal("the scorer output's provenance does not name its code and settings by SHA-256")
    if not isinstance(doc["costs"], dict):
        raise s1.Refusal("the scorer output has no costs object")
    return s1.check_scores(doc["scores"], view.tokens), {"sha256": digest, "provenance": prov, "costs": doc["costs"]}


def build_scorer(prepared: Path, name: str, scores_path: Path, scores_sha256: str, settings: dict,
                 settings_sha256: str) -> dict[str, bytes]:
    """Every output file of one scorer's removal arm (nothing is written here)."""
    s1.check_settings(settings, SETTINGS_NAME)
    if name not in settings["scorers"]:
        raise s1.Refusal(f"no scorer {name!r} in the settings")
    view = view_of(prepared, settings)
    scores, source = read_scorer_output(scores_path, scores_sha256, name, settings, view)
    inputs = {"prepared_manifest": view.manifest_sha256, "prepared_train_rows": view.file_sha256[s1.TRAIN_ROWS],
              "prepared_groups": view.file_sha256[s1.GROUPS], "scorer_output": source["sha256"]}
    return removal_files(view, settings["scorers"][name], scores, settings, settings_sha256, inputs,
                         {"scorer_output": source})


# ----- command line ---------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    a1 = sub.add_parser("a1", help="the A1 removal contract")
    a1.add_argument("--unit", type=Path, required=True, help="the wave-0b attributes unit folder")
    scorer = sub.add_parser("scorer", help="a stage-1 scorer output's removal arm")
    scorer.add_argument("--name", required=True)
    scorer.add_argument("--scores", type=Path, required=True)
    scorer.add_argument("--scores-sha256", required=True)
    for p in (a1, scorer):
        p.add_argument("--prepared", type=Path, required=True, help="the prepared set (manifest pinned)")
        p.add_argument("--out", type=Path, required=True, help="output folder (absent or empty)")
        p.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        if args.command == "a1":
            files = build_a1(args.prepared.resolve(), args.unit.resolve(), settings, digest)
        else:
            files = build_scorer(args.prepared.resolve(), args.name, args.scores.resolve(), args.scores_sha256,
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
