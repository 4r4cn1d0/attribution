"""REQ-5: the length and format rules (H1, H2a, H2b, the L8 octiles and their category-matched controls; standard
library only; Mac, $0; the lead runs it on P, counts only).

**One length order** (L7): all training rows by (target_tokens ascending, then the sealed rank of registry key
length.order over all row ids). Octile k = positions 600k .. 600k + 599 (k = 0..7), eight removal files. H1 = octile 0's
file (the 600 rows with the fewest target tokens); H2b = octile 7's file (the most). H1 under recipe bt reuses H1's file.

**The eight L8 controls** (L7), all built now: for octile k and each category c (c = the category's unit group id), a
sealed sample of n_k,c rows of c's rows outside octile k (key l8.control, parts (k, c)); if n_k,c > |c| - n_k,c, all of
c's rows outside octile k plus a sealed sample of 2 n_k,c - |c| rows of c's own rows inside octile k (key
l8.control_fill, parts (k, c)); never from another category. The record states, per control and category, the rows
shared with octile k. The stage-1 text fixes which control runs (the best octile's).

**H2a** (L6): the response is split with str.splitlines() (CRLF, U+2028 and the other line breaks count) and each line is
tested with re.match against ITEM, MARKUP and FENCE (the settings pin the three patterns, the threshold and the splitter).
A row is an H2a row if at least 2 lines match ITEM, or at least 1 line matches MARKUP or holds FENCE (three backticks).
If n >= 600: a sealed sample of 600 of them (key h2a.sample); else all n plus a sealed sample of 600 - n of the other rows
(key h2a.fill). The response text is read in memory only, to flag rows; it is never written or printed.

Writes into --out (absent or empty): edits/octile_<k>.json, edits/control_<k>.json, edits/h2a.json (row ids only) and
length_rules_record.json (text-free: cut points, category counts, H2a's n and branch counts, the token accounting).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import token_accounting as ta  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "build_length_rules.json"
SETTINGS_SHA256 = "3800e52ae3c7f4fd2c886f14ba973b814c98b735d4d166f50a7fc133358de5b3"
SETTINGS_NAME = "build_length_rules"
RECORD = "length_rules_record.json"


# ----- H2a (L6) -------------------------------------------------------------------------------------


def h2a_rule(settings: dict):
    """The H2a predicate from the pinned patterns: text -> (is_h2a, item_lines, markup_lines, fence_lines)."""
    rule = settings["h2a"]
    item, markup, fence = re.compile(rule["item"]), re.compile(rule["markup"]), rule["fence"]
    threshold = rule["item_threshold"]

    def classify(text: str) -> tuple[bool, int, int, int]:
        lines = text.splitlines()
        items = sum(1 for line in lines if item.match(line))
        marks = sum(1 for line in lines if markup.match(line))
        fences = sum(1 for line in lines if fence in line)
        return items >= threshold or marks >= 1 or fences >= 1, items, marks, fences
    return classify


def response_flags(prepared: Path, view: s1.PreparedView, classify) -> dict[str, bool]:
    """Each training row's H2a flag; the response text is dropped at once (P's file hash is checked first)."""
    if sha256_file(prepared / s1.TRAIN_ROWS) != view.file_sha256[s1.TRAIN_ROWS]:
        raise s1.Refusal("train_rows.jsonl changed after the view read it")
    flags = {}
    for row in s1.iter_jsonl(prepared / s1.TRAIN_ROWS):
        rid, text = row.get("row_id"), row.get("response")
        row.clear()
        if rid not in view.tokens or not isinstance(text, str) or rid in flags:
            raise s1.Refusal("a training row has no known id or no response string")
        flags[rid] = classify(text)[0]
    if set(flags) != set(view.tokens):
        raise s1.Refusal("the training rows changed between the two reads")
    return flags


# ----- the length order, octiles and controls (L7) ---------------------------------------------------


def length_order(view: s1.PreparedView, key: str) -> list[str]:
    rank = s1.sealed_rank(view.tokens, key)
    return sorted(view.tokens, key=lambda r: (view.tokens[r], rank[r]))


def octiles(order: list[str], size: int, count: int) -> list[list[str]]:
    if len(order) != size * count:
        raise s1.Refusal(f"{len(order)} rows do not make {count} octiles of {size}")
    return [order[size * k:size * (k + 1)] for k in range(count)]


def control(view: s1.PreparedView, octile: list[str], k: int, key: str, fill_key: str) -> tuple[list[str], dict]:
    """The category-matched control of octile k (L7): exact category counts, the fill from inside the octile."""
    inside = set(octile)
    rows, table = [], {}
    for g in view.units:
        members = view.members[g]
        n = sum(1 for r in members if r in inside)
        outside = [r for r in members if r not in inside]
        if n <= len(outside):
            picked, fill = s1.sealed_sample(outside, n, key, k, g), []
        else:
            fill = s1.sealed_sample([r for r in members if r in inside], n - len(outside), fill_key, k, g)
            picked = list(outside)
        rows += picked + fill
        table[g] = {"category": view.category[g], "rows": n, "from_outside": len(picked), "fill_from_inside": len(fill),
                    "shared_with_octile": len(fill)}
    if len(set(rows)) != len(octile):
        raise s1.Refusal(f"control {k} does not hold as many distinct rows as its octile")
    return sorted(rows), table


# ----- build ----------------------------------------------------------------------------------------


def build(prepared: Path, settings: dict, settings_sha256: str) -> dict[str, bytes]:
    s1.check_settings(settings, SETTINGS_NAME)
    pins = settings["prepared"]
    view = s1.PreparedView(prepared, pins["manifest_sha256"])
    view.check_shape(pins["rows"], pins["units"], pins["rows_per_unit"])
    tokens = ta.TokenView(prepared, pins["manifest_sha256"])
    prov = s1.provenance(Path(__file__).resolve(), settings_sha256,
                         {"prepared_manifest": view.manifest_sha256,
                          "prepared_train_rows": view.file_sha256[s1.TRAIN_ROWS]}, settings["label_entries"])
    files, records = {}, []

    def add(rel: str, name: str, remove: list[str], role: str, extra: dict) -> None:
        doc = s1.edit_document(name=name, edit_kind="remove", manifest_sha256=view.manifest_sha256, remove=remove,
                               provenance={**prov, "role": role, **extra})
        data, edit = s1.checked_edit(doc, view.engine_stub())
        files[rel] = data
        records.append({"file": rel, "sha256": edit.sha256, "arm": edit.arm, "role": role, **extra,
                        "tokens": ta.account(tokens, removed=remove)})

    lo = settings["length"]
    order = length_order(view, lo["key"])
    parts = octiles(order, lo["octile_size"], lo["octiles"])
    cuts = [{"octile": k, "first_target_tokens": view.tokens[p[0]], "last_target_tokens": view.tokens[p[-1]]}
            for k, p in enumerate(parts)]
    for k, part in enumerate(parts):
        role = {0: "octile 0 = H1 (primary arm P3)", len(parts) - 1: f"octile {len(parts) - 1} = H2b (secondary)"}.get(
            k, f"octile {k} (L8, secondary)")
        add(f"edits/octile_{k}.json", f"stage-1 length octile {k} of 8: remove the rows at positions {lo['octile_size'] * k}-"
            f"{lo['octile_size'] * (k + 1) - 1} of the target-length order", sorted(part), role,
            {"octile": k, "by_category": {view.category[g]: sum(1 for r in view.members[g] if r in set(part))
                                          for g in view.units}})
    cc = settings["controls"]
    for k, part in enumerate(parts):
        rows, table = control(view, part, k, cc["key"], cc["fill_key"])
        add(f"edits/control_{k}.json", f"stage-1 L8 control {k}: category-matched random rows for octile {k}", rows,
            f"control of octile {k} (secondary; the stage-1 text fixes which control runs)", {"octile": k, "table": table})
    h = settings["h2a"]
    flags = response_flags(prepared, view, h2a_rule(settings))
    marked = sorted(r for r, f in flags.items() if f)
    n, want = len(marked), h["rows"]
    if n >= want:
        chosen, branch = s1.sealed_sample(marked, want, h["sample_key"]), {"branch": "sample", "sampled": want, "fill": 0}
    else:
        rest = sorted(r for r, f in flags.items() if not f)
        chosen = marked + s1.sealed_sample(rest, want - n, h["fill_key"])
        branch = {"branch": "fill", "sampled": 0, "fill": want - n}
    add("edits/h2a.json", "stage-1 H2a: remove 600 rows whose response holds list or markup lines (L6 rule)",
        sorted(chosen), "H2a (secondary)", {"n_h2a_rows": n, **branch})
    record = {"kind": "stage1 length and format rules", "version": 1, "requirement": settings["requirement"],
              "cut_points": cuts, "h1": "edits/octile_0.json", "h2b": f"edits/octile_{len(parts) - 1}.json",
              "h1_under_recipe_bt": "reuses edits/octile_0.json", "files": records, "provenance": prov}
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
        files = build(args.prepared.resolve(), settings, digest)
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
