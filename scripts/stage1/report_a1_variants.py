"""A1 report-only variants (W1-04; addendum §5 item 2; Draft C R7.4; standard library only; Mac, $0).

From the same wave-0b attributes unit as A1, after the same input checks (T1's own check_attributes_unit, read-only):

- (a) one-shot score stability: per row a_i^q = cosine_H(i, q) − cosine_S(i, q) and a_i^e1 likewise. Reported:
  the Spearman ρ of a^q against a^e1 over all training rows (average ranks for ties); the top-600 set of each,
  with its Jaccard against the other and against A1's T1 set; the mean identity (a^q + a^e1) / 2 = T1's a_i
  (within 1e-12, or the report refuses).
- (b) V1, Adam-preconditioned: the same bi-anchored score with adam_score in place of the cosine, the mean over
  q and e1. Reported: its top-600 set and its Jaccard with A1 and with each comparison set given (L1, H1, the
  classifier, as each exists); the Spearman ρ of its 8 unit means against A1's unit means. It is called
  "Adam-preconditioned", never "LESS".

Consistency guards (the report refuses past them): each unit's mean of a^q (a^e1) equals groups.json's
harmful-minus-safe mean_cosine at that checkpoint within 1e-12; each unit's sum of the adam differences at a
checkpoint equals groups.json's harmful-minus-safe adam_sum there within 1e-9 of the sum of absolute terms.

Report only: never an arm, no edit file. The T1 A1 contract does not change; A1's set comes from T1's own
build_a1. Top-600 sets: s1common.select_top with registry key a1_variants.ties, part = the variant name.

  python scripts/stage1/report_a1_variants.py --prepared P --unit U --out OUT [--compare NAME=PATH:SHA256 ...]

A comparison file is a stage-1 selection record (its "selected" list) or an engine edit file (its "remove"
list), named by SHA-256. Its name is a short id ([a-z0-9_], at most 40) other than a1 and the variant names; its set
holds exactly k distinct training rows; a manifest_sha256 in it must be the prepared set's; an unreadable file refuses. Writes OUT/a1_variants.json (absent or empty folder). Prints counts and hashes only.
Exit 0: written; exit 2: refused, nothing written. Defined on engine X (the settings pin it).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from statistics import fmean

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import write_score_edit as wse  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "report_a1_variants.json"
SETTINGS_SHA256 = "d6979c9785b4d312147c2ff53fb834a02f65035428629019bcc0a0c7faeee5c6"
SETTINGS_NAME = "report_a1_variants"
RECORD_KIND = "stage1 A1 report-only variants"
COMPARE_NAME = re.compile(r"^[a-z0-9_]{1,40}$")


# ----- statistics -----------------------------------------------------------------------------------


def average_ranks(values: dict[str, float]) -> dict[str, float]:
    """1-based ranks, ties given the mean of the positions they occupy."""
    order = sorted(values, key=lambda k: values[k])
    ranks: dict[str, float] = {}
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in order[i:j + 1]:
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(x: dict[str, float], y: dict[str, float]) -> float | None:
    """Spearman's ρ: the Pearson correlation of the average ranks over the common keys; None (undefined) when a side
    is constant. Different ids on the two sides refuse."""
    if set(x) != set(y) or len(x) < 2:
        raise s1.Refusal("Spearman ρ needs the same 2 or more ids on both sides")
    rx, ry = average_ranks(x), average_ranks(y)
    keys = sorted(x)
    mx, my = fmean(rx[k] for k in keys), fmean(ry[k] for k in keys)
    sxy = math.fsum((rx[k] - mx) * (ry[k] - my) for k in keys)
    sxx = math.fsum((rx[k] - mx) ** 2 for k in keys)
    syy = math.fsum((ry[k] - my) ** 2 for k in keys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb)


# ----- the variants ---------------------------------------------------------------------------------


def variant_values(rows_bytes: bytes, cfg: dict, view: s1.PreparedView) -> dict[str, dict[str, dict]]:
    """Per row: the harmful-minus-safe difference of each checkpoint's cosine and adam_score
    ({row: {"cosine": {c: d}, "adam_score": {c: d}}}), with T1's row checks."""
    checkpoints, plus, minus = cfg["checkpoints"], cfg["minuend_set"], cfg["subtrahend_set"]
    required, optional = set(cfg["row_record_fields"]), set(cfg["row_record_optional"])
    out: dict[str, dict] = {}
    for number, row in enumerate(s1.iter_jsonl_bytes(rows_bytes, "rows.jsonl"), 1):
        if set(row) != {"row_id", "group_id", "per_checkpoint"}:
            raise s1.Refusal(f"rows.jsonl line {number}: not exactly row_id, group_id, per_checkpoint")
        row_id = row["row_id"]
        if not isinstance(row_id, str) or row_id not in view.tokens or row_id in out:
            raise s1.Refusal(f"rows.jsonl line {number}: the row id is unknown or repeated")
        if row["group_id"] != view.unit_of[row_id]:
            raise s1.Refusal(f"rows.jsonl line {number}: the group id is not the row's unit")
        per = row["per_checkpoint"]
        if not isinstance(per, dict) or set(per) != set(checkpoints):
            raise s1.Refusal(f"rows.jsonl line {number}: the checkpoints are not {checkpoints}")
        diffs: dict[str, dict] = {"cosine": {}, "adam_score": {}}
        for c in checkpoints:
            sets = per[c]
            if not isinstance(sets, dict) or set(sets) != {plus, minus}:
                raise s1.Refusal(f"rows.jsonl line {number}: checkpoint {c} does not hold the sets {plus}, {minus}")
            for field in diffs:
                values = []
                for name in (plus, minus):
                    record = sets[name]
                    if not isinstance(record, dict) or not required <= set(record) <= required | optional:
                        raise s1.Refusal(f"rows.jsonl line {number}: checkpoint {c} set {name} has other fields")
                    value = record[field]
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                        raise s1.Refusal(f"rows.jsonl line {number}: checkpoint {c} set {name}: {field} is not finite")
                    values.append(float(value))
                diffs[field][c] = values[0] - values[1]
        out[row_id] = diffs
    missing = len(set(view.tokens) - set(out))
    if missing:
        raise s1.Refusal(f"rows.jsonl misses {missing} training rows")
    return out


def variant_scores(values: dict[str, dict], variants: dict) -> dict[str, dict[str, float]]:
    """Each variant's per-row score: the mean over its checkpoints of its field's difference."""
    return {name: {row: fmean(v[spec["field"]][c] for c in spec["checkpoints"]) for row, v in values.items()}
            for name, spec in variants.items()}


def check_groups(values: dict[str, dict], groups_doc: dict, cfg: dict, report_cfg: dict,
                 view: s1.PreparedView) -> dict:
    """The per-checkpoint guards against groups.json (cosine means within 1e-12; adam sums within 1e-9 of the
    sum of absolute terms)."""
    groups = groups_doc.get("groups") or {}
    if sorted(groups) != view.units:
        raise s1.Refusal("groups.json does not hold exactly the prepared set's units")
    plus, minus = cfg["minuend_set"], cfg["subtrahend_set"]
    cos_tol, adam_rel = report_cfg["checkpoint_cosine_tolerance"], report_cfg["checkpoint_adam_relative_tolerance"]
    out: dict[str, dict] = {}
    for unit in view.units:
        members = view.members[unit]
        out[unit] = {}
        for c in cfg["checkpoints"]:
            try:
                parts = {s: groups[unit][s]["per_checkpoint"][c] for s in (plus, minus)}
                group_cos = parts[plus]["mean_cosine"] - parts[minus]["mean_cosine"]
                group_adam = parts[plus]["adam_sum"] - parts[minus]["adam_sum"]
            except (KeyError, TypeError):
                raise s1.Refusal(f"groups.json unit {unit}: no per-checkpoint {c} parts for both sets") from None
            mean_cos = fmean(values[r]["cosine"][c] for r in members)
            sum_adam = math.fsum(values[r]["adam_score"][c] for r in members)
            scale = math.fsum(abs(values[r]["adam_score"][c]) for r in members) + abs(group_adam)
            d_cos, d_adam = abs(mean_cos - group_cos), abs(sum_adam - group_adam)
            if not d_cos <= cos_tol:
                raise s1.Refusal(f"unit {unit} checkpoint {c}: the rows' mean cosine difference differs from groups.json "
                                 f"by {d_cos:.3e}")
            if not d_adam <= adam_rel * scale:
                raise s1.Refusal(f"unit {unit} checkpoint {c}: the rows' adam sum differs from groups.json by {d_adam:.3e}")
            out[unit][c] = {"cosine_abs_difference": d_cos, "adam_abs_difference": d_adam, "adam_scale": scale}
    return out


def read_comparison(spec: str, view: s1.PreparedView) -> tuple[str, dict]:
    """NAME=PATH:SHA256 -> (name, {"sha256", "kind", "selected"}); a selection record or an engine edit file."""
    try:
        name, rest = spec.split("=", 1)
        path, digest = rest.rsplit(":", 1)
    except ValueError:
        raise s1.Refusal("a comparison is NAME=PATH:SHA256") from None
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"comparison {name}: the file cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"comparison {name}: the file hashes to {sha256_bytes(data)}, expected {digest}")
    doc = s1.strict_json(data)
    if isinstance(doc, dict) and isinstance(doc.get("selected"), list):
        kind, selected = "selection record", doc["selected"]
    elif isinstance(doc, dict) and isinstance(doc.get("remove"), list):
        kind, selected = "edit file", doc["remove"]
    else:
        raise s1.Refusal(f"comparison {name}: neither a selection record nor an edit file")
    if "manifest_sha256" in doc and doc["manifest_sha256"] != view.manifest_sha256:
        raise s1.Refusal(f"comparison {name}: made for another prepared set")
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= set(view.tokens):
        raise s1.Refusal(f"comparison {name}: the set is not distinct training rows")
    return name, {"sha256": digest, "kind": kind, "selected": sorted(selected)}


# ----- the report -----------------------------------------------------------------------------------


def build_report(prepared: Path, unit_dir: Path, settings: dict, settings_sha256: str, a1_settings: dict,
                 a1_settings_sha256: str, comparisons: list[str] = ()) -> dict[str, bytes]:
    """The report file (nothing is written here)."""
    s1.check_settings(settings, SETTINGS_NAME)
    s1.check_settings(a1_settings, wse.SETTINGS_NAME)
    cfg, rc = a1_settings["a1"], settings["report"]
    view = wse.view_of(prepared, a1_settings)
    unit = wse.check_attributes_unit(unit_dir, cfg["attributes_unit"], view)
    values = variant_values(unit["bytes"]["rows.jsonl"], cfg, view)
    groups_doc = s1.strict_json(unit["bytes"]["groups.json"])
    guards = check_groups(values, groups_doc, cfg, rc, view)
    scores = variant_scores(values, rc["variants"])
    a1_files = wse.build_a1(prepared, unit_dir, a1_settings, a1_settings_sha256)        # T1's own A1 path
    a1_record = json.loads(a1_files[cfg["outputs"]["record"]])
    a1_scores, a1_set = a1_record["scores"], a1_record["selected"]
    identity = max(abs((scores["q"][r] + scores["e1"][r]) / 2 - a1_scores[r]) for r in view.tokens)
    if not identity <= rc["mean_identity_tolerance"]:
        raise s1.Refusal(f"(a^q + a^e1) / 2 differs from T1's a_i by {identity:.3e}")
    k, key = rc["k"], rc["ties"]
    top = {name: s1.select_top(scores[name], k, key, name, expected_ids=view.tokens) for name in rc["variants"]}
    others = dict(read_comparison(spec, view) for spec in comparisons)
    if len(others) != len(comparisons):
        raise s1.Refusal("two comparisons share one name")
    reserved = {"a1", *rc["variants"]}
    if any(n in reserved or not COMPARE_NAME.match(n) for n in others):
        raise s1.Refusal("a comparison name is reserved (a1 or a variant name) or not a short id [a-z0-9_]")
    if any(len(o["selected"]) != k for o in others.values()):
        raise s1.Refusal(f"a comparison set does not hold exactly k = {k} rows")
    sets = {**{name: sorted(sel) for name, sel in top.items()}, "a1": sorted(a1_set),
            **{name: o["selected"] for name, o in others.items()}}
    unit_means = {name: {u: fmean(scores[name][r] for r in view.members[u]) for u in view.units} for name in scores}
    a1_unit_means = {u: fmean(a1_scores[r] for r in view.members[u]) for u in view.units}
    record = {
        "kind": RECORD_KIND, "version": 1, "role": rc["role"], "requirement": settings["requirement"],
        "rows": len(view.tokens), "k": k, "ties_key": key,
        "spearman_none_means": "undefined: one side is constant",
        "stability": {"spearman_q_e1": spearman(scores["q"], scores["e1"]),
                      "jaccard_top_q_e1": jaccard(top["q"], top["e1"]),
                      "jaccard_top_q_a1": jaccard(top["q"], a1_set), "jaccard_top_e1_a1": jaccard(top["e1"], a1_set),
                      "mean_identity_max_abs_difference": identity},
        "adam_preconditioned_v1": {"name": rc["variants"]["adam"]["name"],
                                   "jaccard_top_with": {n: jaccard(top["adam"], s) for n, s in sorted(sets.items())
                                                        if n != "adam"},
                                   "spearman_unit_means_with_a1": spearman(unit_means["adam"], a1_unit_means)},
        "unit_means": {**unit_means, "a1": a1_unit_means},
        "top_sets": {name: sorted(sel) for name, sel in top.items()},
        "boundary": {name: s1.boundary_ties(scores[name], top[name]) for name in top},
        "jaccard_matrix": s1.jaccard_matrix(sets),
        "comparisons": {n: {"sha256": o["sha256"], "kind": o["kind"]} for n, o in sorted(others.items())},
        "a1_set": {"source": "T1 write_score_edit.build_a1", "record_sha256": sha256_bytes(a1_files[cfg["outputs"]["record"]]),
                   "edit_sha256": sha256_bytes(a1_files[cfg["outputs"]["edit"]])},
        "groups_guards": guards,
        "attributes_unit": {"complete_sha256": unit["complete_sha256"], "files": unit["files"]},
        "settings_section": rc,
        "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                    {"prepared_manifest": view.manifest_sha256,
                                     "attributes_complete": unit["complete_sha256"],
                                     **{f"attributes_{n.split('.')[0]}": d for n, d in unit["files"].items()},
                                     "a1_settings": a1_settings_sha256,
                                     **{f"compare_{n}": o["sha256"] for n, o in others.items()}},
                                    settings["label_entries"])}
    return {rc["outputs"]["record"]: canonical_json(record)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--unit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compare", action="append", default=[], help="NAME=PATH:SHA256 (repeatable)")
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        pin = settings["a1_settings"]
        a1_settings, a1_digest = s1.load_settings(s1.REPO / pin["path"], pin["sha256"], wse.SETTINGS_NAME)
        files = build_report(args.prepared.resolve(), args.unit.resolve(), settings, digest, a1_settings, a1_digest,
                             args.compare)
        written = s1.write_new_files(args.out.resolve(), files)
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    print(f"wrote {len(written)} file into {args.out}")
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
