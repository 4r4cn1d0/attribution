"""REQ-7: the add-edit writer (RS B6; W1-12). Mac, CPU, $0; the lead runs it on the real lists.

From a sealed prompt list (the full text file, named by SHA-256; REQ-6's s1.json now, S3's and S4's picks later) it
builds, for list L with n rows:
- **the add edit**: add row j (1-based list position) has the id ``add-<L>-NNN`` (NNN = j with 3 digits), and the list
  item's prompt and response. Texts are never changed, and two byte-identical items with distinct ids are allowed
  (W1-12, for S6).
- **combined edits**: for each remove edit given (``--combine-with NAME=PATH:SHA256``, for example REQ-4's R_d files), the
  same add rows plus that file's removed rows (R+S1), in the file ``<NAME>+<list>.json``. NAME is a plain file-name
  stem (letters, digits, '_', '.', '-'; no '/' and no '..') and no NAME repeats, so every combined edit is written,
  inside --full-out.
Each edit is written in the engine's format (s1.edit_document) and parsed back with the engine's parse_edit; its add
rows are encoded with the engine's edited_corpus under recipe S's max_train_tokens (read from the recipe, never
hard-coded), so an over-long or control-token row refuses and nothing is written. The settings fix each list's row count
(48 for S1, S3 and S4).

Writes the edit files (they hold text) under --full-out, which must lie in a folder named tmp, and a text-free record
(add_edit_record.json) into --out: per edit its SHA-256, arm, kind and counts; per add id the list id, prompt tokens and
target tokens; the token accounting (token_accounting.account) of each edit. Both folders must be absent or empty before
anything is written. Prints counts and hashes only.
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

SETTINGS_PATH = HERE / "settings" / "write_add_edit.json"
SETTINGS_SHA256 = "7cf7dd778e4852305d5ed902dfe75b7eece7bc07ffdc353bcf83cc3a7fd8f167"
SETTINGS_NAME = "write_add_edit"
RECORD = "add_edit_record.json"
LIST_KIND = "stage1 prompt list"
COMBINE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]{0,63}$")   # a plain file-name stem: no '/', no '..'


def check_combine_names(combine: list) -> None:
    """Each --combine-with NAME (the prefix of the file '<NAME>+<list>.json' under --full-out) is a plain file-name
    stem, and no NAME repeats: a repeated NAME would overwrite one combined edit with another, and a path-like NAME
    ('a/b', '../x') would write an edit with text outside --full-out."""
    names = [entry[0] for entry in combine]
    if len(set(names)) != len(names):
        raise s1.Refusal(f"--combine-with repeats a NAME ({len(names) - len(set(names))} repeated of {len(names)})")
    bad = sum(1 for n in names if not isinstance(n, str) or not COMBINE_NAME.match(n) or ".." in n)
    if bad:
        raise s1.Refusal(f"{bad} --combine-with NAME(s) are not plain file-name stems (letters, digits, '_', '.', '-'; "
                         f"no '/' and no '..')")


def read_list(path: Path, digest: str) -> dict:
    """A sealed prompt list {kind, version 1, name, items: [{id, prompt, response}]}, refused unless it hashes to
    digest."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"the list cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"the list hashes to {sha256_bytes(data)}, expected {digest}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != LIST_KIND or doc.get("version") != 1 or \
            not isinstance(doc.get("name"), str) or not isinstance(doc.get("items"), list):
        raise s1.Refusal("not a version-1 stage-1 prompt list")
    items = doc["items"]
    if any(not isinstance(i, dict) or set(i) != {"id", "prompt", "response"} or not isinstance(i["prompt"], str)
           or not isinstance(i["response"], str) or not isinstance(i["id"], str) for i in items):
        raise s1.Refusal("list items must be {id, prompt, response} with text fields")
    if len({i["id"] for i in items}) != len(items):
        raise s1.Refusal("the list repeats an id")
    return {"name": doc["name"], "sha256": digest, "items": items}


def add_id(list_name: str, position: int) -> str:
    return f"add-{list_name}-{position:03d}"


def add_rows(listing: dict, settings: dict) -> list[tuple[str, str, str, str]]:
    """(add id, list id, prompt, response) per list item, in list order; the list's row count is the settings'."""
    spec = settings["lists"].get(listing["name"])
    if spec is None:
        raise s1.Refusal(f"the settings name no list {listing['name']!r}")
    if len(listing["items"]) != spec["rows"]:
        raise s1.Refusal(f"list {listing['name']} holds {len(listing['items'])} rows, the settings say {spec['rows']}")
    return [(add_id(listing["name"], j), item["id"], item["prompt"], item["response"])
            for j, item in enumerate(listing["items"], start=1)]


def encode_adds(document: dict, data: bytes, stub, codec, max_train_tokens: int) -> dict[str, dict]:
    """Every add row through the engine's edited_corpus (parse_edit first); per add id its prompt and target tokens."""
    from experiments.safety_selection.edits import EditError, edited_corpus, parse_edit

    try:
        edit = parse_edit(data, stub)
        encoded = edited_corpus({}, edit, stub, codec, max_train_tokens)
    except (EditError, ValueError) as exc:
        raise s1.Refusal(f"the engine refuses the edit {document['name']!r} ({type(exc).__name__})") from None
    return {row_id: {"prompt_tokens": ex.n_prompt, "target_tokens": ex.n_target} for row_id, ex in encoded.items()}


def build_edits(view: s1.PreparedView, tokens: ta.TokenView, rows: list[tuple[str, str, str, str]], list_name: str,
                combine: list[tuple[str, frozenset]], codec, max_train_tokens: int, provenance: dict) -> tuple[dict, list, dict]:
    """(file name -> bytes, record entries, per add id its tokens) for the add edit and each combined edit."""
    stub = view.engine_stub()
    add = [(a, p, r) for a, _, p, r in rows]
    files, entries = {}, []
    plans = [(f"add_{list_name}.json", "add", f"stage1 {list_name}: add the list's {len(add)} rows", frozenset())]
    plans += [(f"{name}+{list_name}.json", "combined", f"stage1 {name}+{list_name}: {name}'s {len(removed)} removed "
               f"rows and the {len(add)} rows of {list_name}", removed) for name, removed in combine]
    counts = None
    for file_name, kind, title, removed in plans:
        doc = s1.edit_document(name=title, edit_kind=kind, manifest_sha256=view.manifest_sha256, remove=removed,
                               add=add, provenance={**provenance, "list": list_name})
        data, edit = s1.checked_edit(doc, stub)
        per_add = encode_adds(doc, data, stub, codec, max_train_tokens)
        counts = counts or per_add
        files[file_name] = data
        entries.append({"file": file_name, "sha256": sha256_bytes(data), "arm": edit.arm, "edit_kind": kind,
                        "counts": doc["counts"], "tokens": ta.account(tokens, removed=sorted(removed), added=per_add)})
    return files, entries, counts


def build(prepared_root: Path, listing: dict, combine: list[tuple[str, Path, str]], codec, settings: dict,
          settings_sha256: str, recipe_path: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    from experiments.safety_selection.config import config_sha256, load_recipe

    s1.check_settings(settings, SETTINGS_NAME)
    check_combine_names(combine)
    recipe = load_recipe(recipe_path)
    if config_sha256(recipe) != settings["recipe_sha256"]:
        raise s1.Refusal(f"the recipe hashes to {config_sha256(recipe)}, the settings pin {settings['recipe_sha256']}")
    max_train_tokens = recipe["model"]["max_train_tokens"]
    view = s1.PreparedView(prepared_root, settings["prepared_manifest_sha256"])
    tokens = ta.TokenView(prepared_root, settings["prepared_manifest_sha256"])
    rows = add_rows(listing, settings)
    removals = []
    for name, path, digest in combine:
        try:
            data = Path(path).read_bytes()
        except OSError as exc:
            raise s1.Refusal(f"remove edit {name} cannot be read ({type(exc).__name__})") from None
        if sha256_bytes(data) != digest:
            raise s1.Refusal(f"remove edit {name} hashes to {sha256_bytes(data)}, expected {digest}")
        from experiments.safety_selection.edits import EditError, parse_edit
        try:
            edit = parse_edit(data, view.engine_stub())
        except EditError as exc:
            raise s1.Refusal(f"the engine refuses remove edit {name} ({type(exc).__name__})") from None
        if edit.document["edit_kind"] != "remove":
            raise s1.Refusal(f"{name} is not a remove edit")
        removals.append((name, edit.removed))
    inputs = {"list": listing["sha256"], "prepared_manifest": view.manifest_sha256, "recipe": settings["recipe_sha256"],
              **{f"remove_{name}": digest for name, _, digest in combine}}
    prov = s1.provenance(Path(__file__).resolve(), settings_sha256, inputs, settings["label_entries"])
    files, entries, per_add = build_edits(view, tokens, rows, listing["name"], removals, codec, max_train_tokens, prov)
    record = {"kind": "stage1 add-edit record", "version": 1, "requirement": settings["requirement"],
              "list": {"name": listing["name"], "sha256": listing["sha256"], "rows": len(rows)},
              "add_id_rule": settings["add_id_rule"], "max_train_tokens": max_train_tokens,
              "rows": [{"add_id": a, "list_id": lid, **per_add[a]} for a, lid, _, _ in rows],
              "edits": entries, "provenance": prov}
    record_bytes = canonical_json(record)
    if s1._text_hits(record_bytes, [t for _, _, p, r in rows for t in (p, r)]):
        raise s1.Refusal("the record would hold text")
    return files, {RECORD: record_bytes}


def full_out_ok(path: Path) -> Path:
    path = path.resolve()
    if "tmp" not in path.parts:
        raise s1.Refusal("--full-out must lie in a folder named tmp: edit files with text are written only under tmp/")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True, help="recipe S (for max_train_tokens)")
    parser.add_argument("--list", required=True, help="PATH:SHA256 of the sealed prompt list")
    parser.add_argument("--combine-with", action="append", default=[], help="NAME=PATH:SHA256 of a remove edit")
    parser.add_argument("--full-out", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    from scripts.stage1 import build_s_pool as bsp

    folders = []
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        path, _, sha = args.list.rpartition(":")
        listing = read_list(Path(path), sha)
        combine = []
        for spec in args.combine_with:
            name, _, rest = spec.partition("=")
            p, _, h = rest.rpartition(":")
            if not name or not p or not s1.HEX64.match(h):
                raise s1.Refusal("each --combine-with is NAME=PATH:SHA256")
            combine.append((name, Path(p), h))
        check_combine_names(combine)
        folders = bsp.check_output_folders(full_out_ok(args.full_out), args.out)
        full_out, out_dir = folders
        codec = bsp.real_codec(args.prepared, {"inputs": {"prepared_manifest_sha256": settings["prepared_manifest_sha256"]}})
        files, record = build(args.prepared, listing, combine, codec, settings, digest, args.recipe)
        written = s1.write_new_files(full_out, files)
        written.update(s1.write_new_files(out_dir, record))
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} ({bsp.refusal_state(folders)})",
              file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
