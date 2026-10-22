"""REQ-15: the SD-600 rewrite writer (PLAN-S:165; PLANF:116; lead decisions L14 (3); the DIFFUSE branch's first arm).
Mac, $0; the lead runs it on P.

    python scripts/stage1/write_sd600.py prompts --prepared P --a1-selection PATH:SHA256 --full-out TMPDIR --out DIR
    python scripts/stage1/write_sd600.py edit --prepared P --recipe S --a1-selection PATH:SHA256
        --answers PATH:SHA256 --answers-record PATH:SHA256 --full-out TMPDIR --out DIR

A1's 600 rows come from A1's text-free selection record (REQ-14's a1_selection.json, pinned in the settings with its edit
file's SHA-256). ``prompts`` writes those rows' stored prompts, in A1's selection order, as the stage-1 prompt list
``sd600`` (REQ-9's input) under --full-out, with a text-free record. ``edit`` reads REQ-9's answers file and record (each
by SHA-256; the record must name the answers file and the sd600 list this command wrote) and, per row, REWRITES the row
with the untuned greedy answer only if the answer ended, ``strip()`` is non-empty and encode_train(prompt, answer,
S.max_train_tokens) accepts it; every other row of the 600 is REMOVED, never truncated, giving one edit (combined when
both lists are non-empty). Removal reasons: capped, empty, too_long (TooLong), control_token (ControlTokenError). There is
no stop rule on k. Before writing, the edit is parsed with the engine's parse_edit and every rewritten row is encoded with
the engine's edited_corpus against the row's audited encoding (its prompt tokens must not change). The record (text-free)
reports k by reason, the category mix (s1common.report_stats), the A1 ranks of the removed rows, and the token accounting.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import token_accounting as ta  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "write_sd600.json"
SETTINGS_SHA256 = "9b02557e1689460eb92a79ab5d945005320a60a9ba52d80d328c494baa823f85"
SETTINGS_NAME = "write_sd600"
LIST_FILE, EDIT_FILE = "sd600.json", "sd600.edit.json"
PROMPTS_RECORD, EDIT_RECORD = "sd600_prompts_record.json", "sd600_record.json"
REASONS = {"TooLong": "too_long", "ControlTokenError": "control_token", "NoTargets": "empty"}


def read_pinned(pair: tuple[Path, str], what: str) -> bytes:
    path, digest = pair
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    return data


def a1_rows(selection: tuple[Path, str], settings: dict, view: s1.PreparedView) -> list[str]:
    """A1's 600 row ids in selection order, from its pinned selection record."""
    pins = settings["a1"]
    if selection[1] != pins["selection_sha256"]:
        raise s1.Refusal(f"the A1 selection record named is {selection[1]}, the settings pin {pins['selection_sha256']}")
    doc = s1.strict_json(read_pinned(selection, "A1's selection record"))
    if doc.get("arm") != "a1" or doc.get("edit", {}).get("sha256") != pins["edit_sha256"]:
        raise s1.Refusal("the selection record is not A1's, or names another edit file")
    order = doc.get("selection_order")
    if not isinstance(order, list) or len(order) != settings["rows"] or sorted(order) != doc.get("selected") \
            or not set(order) <= set(view.tokens):
        raise s1.Refusal(f"A1's selection does not hold {settings['rows']} training rows")
    return order


def prompts(*, prepared_root: Path, selection: tuple[Path, str], settings: dict, settings_sha256: str):
    from experiments.safety_selection.prepare import load_prepared

    s1.check_settings(settings, SETTINGS_NAME)
    view = s1.PreparedView(prepared_root, settings["prepared_manifest_sha256"])
    order = a1_rows(selection, settings, view)
    prepared = load_prepared(prepared_root, settings["prepared_manifest_sha256"])
    listing = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": "sd600",
                              "items": [{"id": r, "prompt": prepared.train_rows[r]["prompt"]} for r in order]})
    record = canonical_json({"kind": "stage1 sd600 prompts record", "version": 1, "rows": len(order), "ids": order,
                             "list_sha256": sha256_bytes(listing),
                             "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                                         {"a1_selection": selection[1],
                                                          "prepared_manifest": view.manifest_sha256},
                                                         settings["label_entries"])})
    if s1._text_hits(record, [prepared.train_rows[r]["prompt"] for r in order]):
        raise s1.Refusal("the record would hold text")
    return {LIST_FILE: listing}, {PROMPTS_RECORD: record}


def edit(*, prepared_root: Path, recipe_path: Path, selection: tuple[Path, str], answers: tuple[Path, str],
         answers_record: tuple[Path, str], codec, settings: dict, settings_sha256: str, original=None):
    """``original(row_id) -> TrainExample``: the row's audited encoding (default: the engine's verified example)."""
    from experiments.safety_selection import runner
    from experiments.safety_selection.config import config_sha256, load_recipe
    from experiments.safety_selection.edits import EditError, edited_corpus, parse_edit
    from experiments.safety_selection.prepare import load_prepared
    from experiments.safety_selection.textproc import encode_train

    s1.check_settings(settings, SETTINGS_NAME)
    recipe = load_recipe(recipe_path)
    if config_sha256(recipe) != settings["recipe_sha256"]:
        raise s1.Refusal(f"recipe S hashes to {config_sha256(recipe)}, the settings pin {settings['recipe_sha256']}")
    max_train = recipe["model"]["max_train_tokens"]
    view = s1.PreparedView(prepared_root, settings["prepared_manifest_sha256"])
    order = a1_rows(selection, settings, view)
    rec = s1.strict_json(read_pinned(answers_record, "REQ-9's record"))
    entry = (rec.get("lists") or {}).get("sd600") if isinstance(rec, dict) else None
    if rec.get("kind") != "stage1 untuned answers record" or not isinstance(entry, dict):
        raise s1.Refusal("REQ-9's record holds no sd600 list")
    if entry.get("answers_file_sha256") != answers[1]:
        raise s1.Refusal("REQ-9's record names another answers file")
    doc = s1.strict_json(read_pinned(answers, "REQ-9's answers file"))
    items = {i["id"]: i for i in doc.get("items", [])}
    if doc.get("list") != "sd600" or [i["id"] for i in doc.get("items", [])] != order:
        raise s1.Refusal("the answers are not REQ-9's answers to A1's 600 rows in selection order")
    prepared = load_prepared(prepared_root, settings["prepared_manifest_sha256"])
    rows_rec = {r["id"]: r for r in entry["rows"]}
    rewrite, removed, reasons = {}, [], {}
    for rid in order:
        answer, prompt = items[rid]["answer"], prepared.train_rows[rid]["prompt"]
        if items[rid]["prompt"] != prompt:
            raise s1.Refusal(f"row {rid}: REQ-9 answered another prompt than the stored one")
        if not items[rid]["ended"] or rows_rec[rid]["capped"]:
            reasons[rid] = "capped"
        elif not answer.strip():
            reasons[rid] = "empty"
        else:
            try:
                encode_train(codec, rid, prompt, answer, max_train)
                rewrite[rid] = answer
                continue
            except ValueError as exc:
                reasons[rid] = REASONS.get(type(exc).__name__, f"encode_train_{type(exc).__name__}")
        removed.append(rid)
    kind = "combined" if removed and rewrite else ("rewrite" if rewrite else "remove")
    document = s1.edit_document(name=f"stage1 SD-600: rewrite {len(rewrite)} of A1's 600 rows with the untuned greedy "
                                     f"answer, remove {len(removed)}", edit_kind=kind,
                                manifest_sha256=view.manifest_sha256, remove=removed, rewrite=rewrite,
                                provenance={"a1_selection": selection[1], "answers": answers[1], "rule": settings["rule"]})
    data, parsed = s1.checked_edit(document, view.engine_stub())
    if original is None:
        def original(rid):
            return runner._verified_example(codec, rid, prepared.train_rows[rid], recipe)
    corpus = {rid: original(rid) for rid in rewrite}
    try:
        stub = view.engine_stub()
        stub_with_rows = type("Prepared", (), {"manifest_sha256": stub.manifest_sha256, "groups": stub.groups,
                                               "train_rows": {r: prepared.train_rows[r] for r in view.tokens}})()
        encoded = edited_corpus(corpus, parse_edit(data, stub_with_rows), stub_with_rows, codec, max_train)
    except (EditError, ValueError) as exc:
        raise s1.Refusal(f"the engine refuses the SD-600 edit ({type(exc).__name__})") from None
    tokens = ta.TokenView(prepared_root, settings["prepared_manifest_sha256"])
    rewritten_counts = {r: {"prompt_tokens": tokens.prompt_tokens[r], "target_tokens": encoded[r].n_target} for r in rewrite}
    rank = {r: k for k, r in enumerate(order, start=1)}
    record = {"kind": "stage1 sd600 record", "version": 1, "requirement": settings["requirement"], "edit_kind": kind,
              "edit": {"file": EDIT_FILE, "sha256": sha256_bytes(data), "arm": parsed.arm},
              "rewritten": sorted(rewrite), "removed": sorted(removed), "k_removed": len(removed),
              "k_by_reason": dict(sorted(Counter(reasons.values()).items())),
              "removed_a1_ranks": sorted(rank[r] for r in removed),
              "stats": s1.report_stats(view, removed=removed, rewritten=sorted(rewrite), flag_share=settings["category_flag_share"]),
              "tokens": ta.account(tokens, removed=removed, rewritten=rewritten_counts),
              "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                          {"a1_selection": selection[1], "answers": answers[1],
                                           "answers_record": answers_record[1], "prepared_manifest": view.manifest_sha256,
                                           "recipe": settings["recipe_sha256"]}, settings["label_entries"])}
    record_bytes = canonical_json(record)
    if s1._text_hits(record_bytes, list(rewrite.values()) + [prepared.train_rows[r]["prompt"] for r in order]):
        raise s1.Refusal("the record would hold text")
    return {EDIT_FILE: data}, {EDIT_RECORD: record_bytes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p1, p2 = sub.add_parser("prompts"), sub.add_parser("edit")
    for p in (p1, p2):
        p.add_argument("--prepared", type=Path, required=True)
        p.add_argument("--a1-selection", required=True, help="PATH:SHA256")
        p.add_argument("--full-out", type=Path, required=True)
        p.add_argument("--out", type=Path, required=True)
        p.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    p2.add_argument("--recipe", type=Path, required=True, help="recipe S")
    p2.add_argument("--answers", required=True, help="PATH:SHA256 of REQ-9's answers_sd600.json")
    p2.add_argument("--answers-record", required=True, help="PATH:SHA256 of REQ-9's record")
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)

        def pair(spec):
            path, _, sha = spec.rpartition(":")
            if not path or not s1.HEX64.match(sha):
                raise s1.Refusal("each input is PATH:SHA256")
            return Path(path), sha
        from scripts.stage1.build_s_pool import full_out_ok, real_codec

        full_out = full_out_ok(args.full_out)
        if args.command == "prompts":
            full, record = prompts(prepared_root=args.prepared, selection=pair(args.a1_selection), settings=settings,
                                   settings_sha256=digest)
        else:
            codec = real_codec(args.prepared, {"inputs": {"prepared_manifest_sha256": settings["prepared_manifest_sha256"]}})
            full, record = edit(prepared_root=args.prepared, recipe_path=args.recipe, selection=pair(args.a1_selection),
                                answers=pair(args.answers), answers_record=pair(args.answers_record), codec=codec,
                                settings=settings, settings_sha256=digest)
        written = s1.write_new_files(full_out, full)
        written.update(s1.write_new_files(args.out.resolve(), record))
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
