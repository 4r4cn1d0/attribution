"""W1-01 (REQ-27 (a); addendum section 5 item 1; REV3 section 9.3 item 1): the token accounting of every stage-1 arm.
Mac, $0, report only; the lead runs it on the real edit files. It prints counts and hashes only.

    python scripts/stage1/report_token_accounting.py --prepared P --edit NAME=PATH:SHA256 ... \
        [--record PATH:SHA256 ...] [--selected NAME=PATH:SHA256 ...] --out DIR

Every ``--edit`` is one arm's edit file (R_d, R_1200, R_2400, R+S1, H1, H2a, H2b, the octiles and controls, A1, L1,
DataShield-style, Self-Inf-N-style, S1, S3, S4, SD-600, the plant edits, R_tok), read by SHA-256 and parsed by the
engine's own parse_edit against P (manifest pinned by the settings). Every ``--selected`` is a scored-only set (the
content classifier's top 600: ``stage1 classifier scores``; or a ``stage1 score selection``): reported as the rows
it would remove, labelled "scored only (no edit file)".

Per arm, by token_accounting.account: the rows removed, rewritten and added; their target tokens (response +
end-of-turn) and total row tokens (prompt + target); each as a share of P's corpus totals (never the edited corpus's);
the same per unit and per category; the edited corpus's rows, tokens and optimizer steps, ceil(rows / 128).

An edit that adds or rewrites rows holds text, and its new rows' token counts are not in P, so the writer's text-free
record must name the edit file by SHA-256 (``--record``): REQ-7's ``stage1 add-edit record`` (per-add counts: the whole
account is recomputed and must equal the record's), the ``stage1 plant record`` and the ``stage1 sd600 record`` (an
aggregate account: the added block and the rewritten rows' "after" counts come from the record; the removed and
"before" blocks and the edited corpus are recomputed and must equal the record's). A remove-only edit needs no record.
The edit text is read in memory only, to parse the file; the output holds ids, counts and hashes.
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

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import token_accounting as ta  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "report_token_accounting.json"
SETTINGS_SHA256 = "e32a5a8e12c3fcfe3fed1b406176a7d88400808d6d2c53ca0ab690d53e26da9e"
SETTINGS_NAME = "report_token_accounting"
OUTPUT = "token_accounting.json"
ARM_NAME = re.compile(r"^[A-Za-z0-9_.+\-]{1,80}$")


def read_pinned(path: Path, digest: str, what: str) -> bytes:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    return data


def record_index(records: list[tuple[bytes, str]], settings: dict) -> dict[str, dict]:
    """edit SHA-256 -> {"tokens": the writer's account, "per_add": per add id counts or None, "record": SHA-256}."""
    kinds = settings["record_kinds"]
    index: dict[str, dict] = {}

    def put(sha: str, tokens: dict, per_add, record_sha: str) -> None:
        if sha in index:
            raise s1.Refusal(f"two records name the edit {sha}")
        index[sha] = {"tokens": tokens, "per_add": per_add, "record": record_sha}
    for data, digest in records:
        doc = s1.strict_json(data)
        kind = doc.get("kind") if isinstance(doc, dict) else None
        if kind == kinds["add"]:
            per_add = {r["add_id"]: {"prompt_tokens": r["prompt_tokens"], "target_tokens": r["target_tokens"]}
                       for r in doc["rows"]}
            for entry in doc["edits"]:
                put(entry["sha256"], entry["tokens"], per_add, digest)
        elif kind == kinds["plant"]:
            for entry in doc["edits"]:
                put(entry["sha256"], entry["tokens"], None, digest)
        elif kind == kinds["sd600"]:
            put(doc["edit"]["sha256"], doc["tokens"], None, digest)
        else:
            raise s1.Refusal(f"a --record is not one of the writer records {sorted(kinds.values())}")
    return index


def _same(name: str, part: str, ours, theirs) -> None:
    if ours != theirs:
        raise s1.Refusal(f"arm {name}: the writer record's {part} differs from the recomputation")


def edit_account(name: str, view: ta.TokenView, edit, entry: dict | None, rows_per_step: int) -> tuple[dict, str]:
    """(the arm's account, where its added and rewritten counts come from)."""
    removed, rewritten, added = sorted(edit.removed), sorted(edit.rewrite), list(edit.added_ids)
    if not rewritten and not added:
        return ta.account(view, removed=removed, rows_per_step=rows_per_step), "P only (a remove-only edit)"
    if entry is None:
        raise s1.Refusal(f"arm {name} adds or rewrites rows: a --record must name its edit file")
    theirs = entry["tokens"]
    _same(name, "rows per step", rows_per_step, theirs.get("rows_per_step"))
    if entry["per_add"] is not None and not rewritten:
        if not set(added) <= set(entry["per_add"]):
            raise s1.Refusal(f"arm {name}: an added id has no count in the add-edit record")
        ours = ta.account(view, removed=removed, added={a: entry["per_add"][a] for a in added},
                          rows_per_step=rows_per_step)
        _same(name, "account", ours, theirs)
        return ours, "the add-edit record's per-row counts (recomputed)"
    ours = ta.account(view, removed=removed, rows_per_step=rows_per_step)
    before = ta.account(view, removed=rewritten, rows_per_step=rows_per_step)["removed"]
    _same(name, "removed block", ours["removed"], theirs["removed"])
    _same(name, "rewritten 'before' block", before, theirs["rewritten"]["before"])
    after, add = theirs["rewritten"]["after"], theirs["added"]
    _same(name, "rewritten row count", len(rewritten), after["rows"])
    _same(name, "added row count", len(added), add["rows"])
    corpus = ours["corpus"]
    rows = corpus["rows"] - len(removed) + len(added)
    edited = {"rows": rows,
              "target_tokens": corpus["target_tokens"] - ours["removed"]["target_tokens"] - before["target_tokens"]
              + after["target_tokens"] + add["target_tokens"],
              "total_tokens": corpus["total_tokens"] - ours["removed"]["total_tokens"] - before["total_tokens"]
              + after["total_tokens"] + add["total_tokens"],
              "steps": ta.steps(rows, rows_per_step)}
    _same(name, "edited corpus", edited, theirs["edited_corpus"])
    ours.update(rewritten={"before": before, "after": after}, added=add, edited_corpus=edited)
    return ours, "the writer record's aggregate account (cross-checked)"


def selected_set(doc: dict, settings: dict) -> list[str]:
    kinds = settings["selected_kinds"]
    if doc.get("kind") == kinds["classifier"]:
        return list(doc["selection"]["selected"])
    if doc.get("kind") == kinds["selection"]:
        return list(doc["selected"])
    raise s1.Refusal(f"a --selected file is not one of {sorted(kinds.values())}")


def build(*, prepared_root: Path, edits: dict[str, tuple[Path, str]], records: list[tuple[Path, str]],
          selected: dict[str, tuple[Path, str]], settings: dict, settings_sha256: str) -> dict[str, bytes]:
    from experiments.safety_selection.edits import EditError, parse_edit

    s1.check_settings(settings, SETTINGS_NAME)
    if not edits and not selected:
        raise s1.Refusal("no arm was named")
    names = list(edits) + list(selected)
    if len(set(names)) != len(names) or not all(ARM_NAME.match(n) for n in names):
        raise s1.Refusal("arm names must be distinct short ids")
    manifest = settings["prepared_manifest_sha256"]
    view = ta.TokenView(prepared_root, manifest)
    stub = s1.PreparedView(prepared_root, manifest).engine_stub()
    rows_per_step = settings["rows_per_step"]
    index = record_index([(read_pinned(p, d, "a --record file"), d) for p, d in records], settings)
    arms, texts, used = {}, [], set()
    for name, (path, digest) in edits.items():
        data = read_pinned(path, digest, f"arm {name}'s edit file")
        try:
            edit = parse_edit(data, stub)
        except EditError as exc:
            raise s1.Refusal(f"the engine refuses arm {name}'s edit file ({type(exc).__name__})") from None
        texts += list(edit.rewrite.values()) + [t for _, p, r in edit.added for t in (p, r)]
        entry = index.get(digest)
        account, source = edit_account(name, view, edit, entry, rows_per_step)
        if entry is not None:
            used.add(digest)
        arms[name] = {"source": "edit file", "file_sha256": digest, "arm": edit.arm,
                      "edit_kind": edit.document["edit_kind"], "record_sha256": entry["record"] if entry else None,
                      "counts_from": source, "tokens": account}
    for name, (path, digest) in selected.items():
        rows = selected_set(s1.strict_json(read_pinned(path, digest, f"arm {name}'s selection")), settings)
        arms[name] = {"source": "scored only (no edit file)", "file_sha256": digest, "arm": None, "edit_kind": None,
                      "record_sha256": None, "counts_from": "P only (the rows it would remove)",
                      "tokens": ta.account(view, removed=sorted(rows), rows_per_step=rows_per_step)}
    inputs = {"prepared_manifest": manifest, **{f"edit_{n}": d for n, (_, d) in edits.items()},
              **{f"selected_{n}": d for n, (_, d) in selected.items()},
              **{f"record_{i}": d for i, (_, d) in enumerate(records)}}
    doc = {"kind": settings["output_kind"], "version": 1, "requirement": settings["requirement"],
           "corpus": view.totals(), "rows_per_step": rows_per_step, "steps_rule": ta.STEPS_RULE,
           "arms": dict(sorted(arms.items())), "unused_record_entries": len(set(index) - used),
           "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256, inputs, settings["label_entries"])}
    data = canonical_json(doc)
    if s1._text_hits(data, texts):
        raise s1.Refusal("the report would hold edit text")
    return {OUTPUT: data}


def _pair(spec: str, what: str) -> tuple[Path, str]:
    path, _, sha = spec.rpartition(":")
    if not path or not s1.HEX64.match(sha):
        raise s1.Refusal(f"{what} is PATH:SHA256")
    return Path(path), sha


def _named(specs: list[str], what: str) -> dict[str, tuple[Path, str]]:
    out = {}
    for spec in specs:
        name, sep, rest = spec.partition("=")
        if not sep or name in out:
            raise s1.Refusal(f"{what} is NAME=PATH:SHA256, one per name")
        out[name] = _pair(rest, what)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--edit", action="append", default=[], help="NAME=PATH:SHA256 (repeatable)")
    parser.add_argument("--record", action="append", default=[], help="PATH:SHA256 (repeatable)")
    parser.add_argument("--selected", action="append", default=[], help="NAME=PATH:SHA256 (repeatable)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        files = build(prepared_root=args.prepared, edits=_named(args.edit, "--edit"),
                      records=[_pair(r, "--record") for r in args.record], selected=_named(args.selected, "--selected"),
                      settings=settings, settings_sha256=digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
