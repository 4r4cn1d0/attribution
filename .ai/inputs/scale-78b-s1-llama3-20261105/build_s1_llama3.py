"""S1 on the Llama manifest (prepared-kt-dolly-llama3, c52a50af...): stage 1's sealed list s1.json (the 48 S-pool rows
with their PKU-safe responses; SHA-256 389c20ad...) as an add edit, written by REQ-7's frozen writer
(scripts/stage1/write_add_edit.py, imported unchanged and pinned by SHA-256) with the Llama codec under the Llama main
recipe's model.max_train_tokens. For Llama-3.1-8B (the 7-8B tier; Part 1 section 14 item 1) and Llama-3.2-1B (stage 2),
which share the manifest and the tokenizer (the check's C6: S1 is per manifest, the same 48 rows re-bound). Mac, $0.

The route (the lead's addendum A3 pattern: a sealed folder with a MANIFEST, this script's SHA-256 in every output, write
guards by directory identity from the first build; REQ-7's rule unchanged):

1. REQ-7's code path is the code path: ``read_list`` reads the sealed list by its pinned SHA-256; ``build`` makes the
   edit with ``s1common.edit_document``, parses it back with the engine's ``parse_edit``, encodes every add row with the
   engine's ``edited_corpus`` under the recipe's max_train_tokens (read from the config, never hard-coded) and returns a
   text-free record. The only things this wrapper supplies are the Llama inputs: the Llama prepared set and codec, the
   Llama main config (74758af1...), and a settings document derived from REQ-7's committed settings (7cf7dd77...) with
   two pins changed (the prepared manifest and the recipe's config_sha256) and its derivation recorded. The frozen
   files (write_add_edit.py, s1common.py, build_s_pool.py, token_accounting.py, the settings) are pinned here and any
   change refuses.
2. The sealed list. ``--list PATH:SHA256`` names it when the lead has the file (its hash must be the pin). Without it,
   the list is recovered from stage 1's committed S1 edit (add_s1.json, 904a0cf1...; a copy of its bytes is the
   ``edit.json`` of every stage-1 S1 unit): the edit is read through the engine's ``parse_edit`` against the OLMo set
   (the text is never printed), its 48 add rows are put back in list order by the committed add-s1 record's
   add_id -> list_id map, and the list document is rebuilt in the writer's own form (build_s_pool.py:373-378,
   canonical JSON). The result is accepted only if it hashes to the sealed pin 389c20ad..., so it IS the sealed list
   byte for byte, and REQ-7's ``read_list`` then reads it by that pin. The recovered list is written under --full-out
   (list/s1.json), a folder named tmp, as every text-bearing stage-1 file is.
3. The edit is parsed back against the Llama set (REQ-7 does this) and must be refused by the engine against the OLMo
   set (the manifest binding; SS/edits.py:117). The OLMo prepared set is read for that check only (ids, no text).
4. Outputs. Under --out (default out/ next to this script; absent or empty): MANIFEST.json (every output's SHA-256, the
   arm, counts, the per-row token counts, the pins, the derived settings' hash; no build time, so a re-run gives the
   same bytes in the same environment), add_edit_record.json (REQ-7's text-free record), the derived settings
   document. Under --full-out (default <repo>/tmp/scale-78b-s1-llama3-20261105; must lie in a folder named tmp; absent
   or empty): edits/add_s1.json (the edit; it holds the 48 rows' text) and list/s1.json when recovered. The kit copies
   the edit into its bundle by the hash the MANIFEST names, as stage 1 did.
5. Write guards. Neither output may lie under a committed sealed folder (SEAL, the anchor list, stage 1's records, the
   three scale-78b folders of 5 Nov 2026), compared as resolved paths and by directory identity (os.path.samefile on
   the deepest existing ancestor and its parents: a case-variant spelling, a symlink, a dotted or relative path refuse);
   the forbidden roots come from this script's own checkout and from --repo. The two outputs must be distinct, not
   nested, and absent or empty; a refusal leaves nothing written (the recovered list is removed again on a later refusal).

Reads from each prepared set ONLY: manifest.json, manifest.sha256; engine/train_rows.jsonl (row_id and token counts;
the text fields are dropped at once by s1common.PreparedView / token_accounting.TokenView); engine/groups.json. Never
banks/, selector/, hidden/, auditor/ or engine/query_rows.jsonl. Prints counts and hashes only.

The script's SHA-256 reaches every output: MANIFEST.json names it; the settings document names it (derived_from); the
record and the edit file carry the settings document's SHA-256 in their provenance (REQ-7's provenance block). Frozen
once committed: a byte change here changes the settings' hash and so the edit's bytes and arm; rebuild into empty
folders after any change, as the sibling sealed folders do.
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                      # <repo>/.ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.edits import EditError, arm_of, parse_edit  # noqa: E402
from scripts.stage1 import build_s_pool as bsp  # noqa: E402  (real_codec, check_output_folders, refusal_state)
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import token_accounting as ta  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402  (REQ-7, imported unchanged)

# ----- pins ---------------------------------------------------------------------------------------------------------

SCRIPT_REL = ".ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py"
OUT_REL = ".ai/inputs/scale-78b-s1-llama3-20261105/out"
FULL_OUT_REL = "tmp/scale-78b-s1-llama3-20261105"
LLAMA_PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-llama3"
LLAMA_MANIFEST_SHA256 = "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"
OLMO_PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-olmo2"
OLMO_MANIFEST_SHA256 = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
LLAMA_MAIN_CONFIG_REL = "experiments/safety_selection/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json"
LLAMA_MAIN_CONFIG_SHA256 = "74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893"   # config_sha256 (Part 1 2.1)
LIST_NAME = "s1"
LIST_ROWS = 48
LIST_SHA256 = "389c20ad00261b1a304d3dd9f14a113a0b05bcec63758262af1b1629d48e0480"              # the sealed list (REQ-6)
LIST_KIND = "stage1 prompt list"                                                                  # wae.LIST_KIND
STAGE1_ADD_S1_RECORD_REL = ".ai/inputs/stage1-commitments-20261016/add-s1/add_edit_record.json"
STAGE1_ADD_S1_RECORD_SHA256 = "311957a442009bbb71995690d9d031cd8dd0a6ced24982ee7655baae927a01ba"
OLMO_S1_EDIT_SHA256 = "904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10"        # stage 1's add_s1.json
OLMO_S1_EDIT_REL = ("tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-" + OLMO_S1_EDIT_SHA256 + "-e1-a1/edit.json")
FROZEN = {"scripts/stage1/write_add_edit.py": "8b866b3d22bd0656bccd8dbb21ccabde3fda2726b85f149711455836928ad27c",
          "scripts/stage1/s1common.py": "930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552",
          "scripts/stage1/build_s_pool.py": "cb2ca385a3917d0f4be041ae08b1e121bc67f82a7fc95165e33550f053f463df",
          "scripts/stage1/token_accounting.py": "b9a51f6fc66fb3011c7448d0869f65848d407fa4d901ba10216312e0a93a6024"}
FROZEN_MODULES = {"scripts/stage1/write_add_edit.py": wae, "scripts/stage1/s1common.py": s1,
                  "scripts/stage1/build_s_pool.py": bsp, "scripts/stage1/token_accounting.py": ta}
STAGE1_SETTINGS_REL = "scripts/stage1/settings/write_add_edit.json"
STAGE1_SETTINGS_SHA256 = "7cf7dd778e4852305d5ed902dfe75b7eece7bc07ffdc353bcf83cc3a7fd8f167"
FORBIDDEN_DIRS = (".ai/inputs/gate-b-sealed-20261008", ".ai/inputs/gate-b-anchors-20261008",
                  ".ai/inputs/stage1-commitments-20261016", ".ai/inputs/scale-78b-sealed-llama3-20261105",
                  ".ai/inputs/scale-78b-r-draws-olmo2-20261105", ".ai/inputs/scale-78b-length-rules-llama3-20261105")
MANIFEST_KIND = "scale-78b S1 add edit (llama3 manifest) manifest"
SETTINGS_FILE = "write_add_edit_llama3.settings.json"
EDIT_FILE = f"add_{LIST_NAME}.json"
REQUIREMENT = ("Part 1 section 14 item 1 (the S-pool and S1: the same 48 S-pool rows, re-bound to the family manifest; "
               "research/experiments/2026-11-05-78b-preregistration-part1.md); the readiness check's C6; REQ-7's rule "
               "(scripts/stage1/write_add_edit.py, unchanged) with the brief's W1-12; the lead's addendum A3 (the sealed "
               "folder pattern)")
ROLE = ("S1 (the 48 S-pool rows with their PKU-safe responses) as an add arm on the Llama manifest: Llama-3.1-8B in the "
        "7-8B tier (under the family's main config, Part 1 section 10) and Llama-3.2-1B in stage 2")
SETTINGS_CHANGED = ("prepared_manifest_sha256", "recipe_sha256", "recipe_use", "owner", "requirement", "derived_from")


def sha256_path(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def rel(path: Path, repo: Path) -> str:
    try:
        return Path(path).resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(Path(path).resolve())


# ----- the frozen code ------------------------------------------------------------------------------------------------


def check_frozen() -> dict[str, str]:
    """The REQ-7 code path is this checkout's committed files, byte for byte: each pinned file hashes to its pin and
    is the file the imported module runs from."""
    out = {}
    for rel_path, pin in FROZEN.items():
        path = REPO / rel_path
        digest = sha256_path(path)
        if digest != pin:
            raise s1.Refusal(f"{rel_path} hashes to {digest}, the pin is {pin}: the frozen writer changed; nothing is built")
        module_file = Path(FROZEN_MODULES[rel_path].__file__).resolve()
        if module_file != path.resolve():
            raise s1.Refusal(f"{rel_path} is imported from {module_file}, not from this checkout")
        out[rel_path] = digest
    return out


# ----- the sealed list ------------------------------------------------------------------------------------------------


def stage1_record(path: Path) -> dict:
    data = path.read_bytes()
    if sha256_bytes(data) != STAGE1_ADD_S1_RECORD_SHA256:
        raise s1.Refusal(f"the committed add-s1 record hashes to {sha256_bytes(data)}, the pin is {STAGE1_ADD_S1_RECORD_SHA256}")
    record = s1.strict_json(data)
    if record.get("list", {}).get("sha256") != LIST_SHA256 or record.get("list", {}).get("name") != LIST_NAME:
        raise s1.Refusal("the committed add-s1 record names another list")
    adds = [e for e in record.get("edits", []) if e.get("edit_kind") == "add"]
    if len(adds) != 1 or adds[0].get("sha256") != OLMO_S1_EDIT_SHA256:
        raise s1.Refusal("the committed add-s1 record names another add edit")
    return record


def recover_list(edit_path: Path, olmo_stub, record: dict) -> bytes:
    """The sealed list's bytes, rebuilt from stage 1's committed S1 edit (through the engine's parse_edit) and the
    record's add_id -> list_id map in the writer's own form; accepted only if it hashes to the sealed pin."""
    try:
        data = Path(edit_path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"the committed S1 edit cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != OLMO_S1_EDIT_SHA256:
        raise s1.Refusal(f"the S1 edit hashes to {sha256_bytes(data)}, the pin is {OLMO_S1_EDIT_SHA256}")
    try:
        edit = parse_edit(data, olmo_stub)
    except EditError as exc:
        raise s1.Refusal(f"the engine refuses the committed S1 edit against the OLMo set ({type(exc).__name__})") from None
    list_id = {row["add_id"]: row["list_id"] for row in record["rows"]}
    rows = sorted(edit.added)                                    # (add id, prompt, response); add-s1-001 .. add-s1-048
    if len(rows) != LIST_ROWS or any(a not in list_id for a, _, _ in rows):
        raise s1.Refusal("the committed S1 edit and its record disagree on the add ids")
    doc = canonical_json({"kind": LIST_KIND, "version": 1, "name": LIST_NAME,
                          "items": [{"id": list_id[a], "prompt": p, "response": r} for a, p, r in rows]})
    if sha256_bytes(doc) != LIST_SHA256:
        raise s1.Refusal(f"the recovered list hashes to {sha256_bytes(doc)}, not to the sealed pin {LIST_SHA256}")
    return doc


# ----- the settings ---------------------------------------------------------------------------------------------------


def derived_settings(base: dict, base_sha256: str, script_sha256: str) -> dict:
    """REQ-7's committed settings with the two pins re-bound to the Llama manifest and the Llama main recipe; the
    derivation recorded. Everything else (the add-id rule, the list row counts, the checks) is REQ-7's."""
    out = copy.deepcopy(base)
    out["prepared_manifest_sha256"] = LLAMA_MANIFEST_SHA256
    out["recipe_sha256"] = LLAMA_MAIN_CONFIG_SHA256
    out["recipe_use"] = ("the Llama main config's model.max_train_tokens for encode_train (Part 1 section 10: add arms run "
                         "under the family's main config; recipe S_78 differs from it only in attribution fields, "
                         "scripts/scale78b/make_recipe_s78.py, so it shares the limit); read, never hard-coded")
    out["owner"] = SCRIPT_REL
    out["requirement"] = REQUIREMENT
    out["derived_from"] = {"path": STAGE1_SETTINGS_REL, "sha256": base_sha256, "changed": list(SETTINGS_CHANGED),
                           "by": SCRIPT_REL, "by_sha256": script_sha256}
    return out


# ----- the guards -----------------------------------------------------------------------------------------------------


def guard_out(out: Path, repo: Path | None = None) -> None:
    """Refuse an output under a committed sealed folder (FORBIDDEN_DIRS) of this script's own checkout (REPO) or of
    --repo. Two comparisons: the resolved paths as strings (this also covers a forbidden folder that does not exist
    yet) and, for each forbidden folder that exists, directory identity (os.path.samefile) between it and the deepest
    existing ancestor of out (out itself when it exists) or any parent of that ancestor. Identity covers a case-variant
    spelling on a case-insensitive filesystem (resolve() keeps the typed case), a symlink and a dotted or relative path.
    (bsp.check_output_folders then refuses an existing non-empty folder and nested outputs.)"""
    out = Path(out).resolve()
    roots = [REPO.resolve()]
    if repo is not None and Path(repo).resolve() not in roots:
        roots.append(Path(repo).resolve())
    anchor = out                                        # the deepest existing ancestor of out (out itself when it exists)
    while not anchor.exists() and anchor.parent != anchor:
        anchor = anchor.parent
    for root in roots:
        for forbidden in FORBIDDEN_DIRS:
            target = (root / forbidden).resolve()
            if out == target or target in out.parents:
                raise s1.Refusal(f"refusing to write under {forbidden}")
            if target.exists() and any(os.path.samefile(p, target) for p in (anchor, *anchor.parents)):
                raise s1.Refusal(f"refusing to write under {forbidden}")


# ----- the build ------------------------------------------------------------------------------------------------------


def build(repo: Path, llama_root: Path, olmo_root: Path, recipe_path: Path, list_path: Path, list_source: dict) -> dict:
    """Everything but the writes. list_path is the sealed list's file (given, or recovered and written under --full-out
    by the caller); REQ-7's read_list reads it by the pin. The manifest names the text files by their place under
    --full-out and by their SHA-256, never by the operator's folder, so two builds give the same manifest bytes."""
    frozen = check_frozen()
    script_sha256 = sha256_file(Path(__file__).resolve())
    base, base_sha256 = s1.load_settings(REPO / STAGE1_SETTINGS_REL, STAGE1_SETTINGS_SHA256, wae.SETTINGS_NAME)
    settings = derived_settings(base, base_sha256, script_sha256)
    settings_bytes = canonical_json(settings)
    settings_sha256 = sha256_bytes(settings_bytes)
    s1.check_settings(settings, wae.SETTINGS_NAME)
    llama = s1.PreparedView(llama_root, LLAMA_MANIFEST_SHA256)
    olmo = s1.PreparedView(olmo_root, OLMO_MANIFEST_SHA256)
    listing = wae.read_list(Path(list_path), LIST_SHA256)             # REQ-7's frozen path, by the sealed pin
    if listing["name"] != LIST_NAME or len(listing["items"]) != LIST_ROWS:
        raise s1.Refusal(f"the sealed list is not {LIST_NAME} with {LIST_ROWS} rows")
    codec = bsp.real_codec(llama_root, {"inputs": {"prepared_manifest_sha256": LLAMA_MANIFEST_SHA256}})
    files, record_files = wae.build(llama_root, listing, [], codec, settings, settings_sha256, recipe_path)
    if set(files) != {EDIT_FILE} or set(record_files) != {wae.RECORD}:
        raise s1.Refusal("REQ-7's writer returned other files than the add edit and its record")
    data, record_bytes = files[EDIT_FILE], record_files[wae.RECORD]
    try:
        edit = parse_edit(data, llama.engine_stub())
    except EditError as exc:
        raise s1.Refusal(f"the engine refuses the edit against the Llama set ({type(exc).__name__})") from None
    if edit.arm != arm_of(data) or len(edit.added) != LIST_ROWS or edit.removed or edit.rewrite:
        raise s1.Refusal("the engine reads the edit differently from what was written")
    try:
        parse_edit(data, olmo.engine_stub())
    except EditError:
        pass
    else:
        raise s1.Refusal("the engine accepted the edit against the OLMo set: the manifest binding failed")
    record = s1.strict_json(record_bytes)
    if record["provenance"]["settings_sha256"] != settings_sha256 or record["list"]["sha256"] != LIST_SHA256:
        raise s1.Refusal("the record does not name this build's settings and list")
    add_entry = record["edits"][0]
    if add_entry["sha256"] != edit.sha256 or add_entry["edit_kind"] != "add":
        raise s1.Refusal("the record's edit entry is not the edit written")
    edit_rel = f"edits/{EDIT_FILE}"                                      # under --full-out (default FULL_OUT_REL)
    manifest = {
        "kind": MANIFEST_KIND, "version": 1,
        "script": {"path": SCRIPT_REL, "sha256": script_sha256, "python": record["provenance"]["python"],
                   "numpy": record["provenance"]["numpy"]},
        "frozen_code": {**frozen, "settings": {"path": STAGE1_SETTINGS_REL, "sha256": base_sha256},
                        "note": "REQ-7's writer and helpers, imported unchanged; the edit's provenance names write_add_edit.py"},
        "settings": {"path": SETTINGS_FILE, "sha256": settings_sha256, "derived_from": STAGE1_SETTINGS_REL,
                     "changed": list(SETTINGS_CHANGED)},
        "engine_identity_sha256": code_identity()["sha256"],
        "prepared": {"llama": {"path": LLAMA_PREPARED_REL, "manifest_sha256": llama.manifest_sha256,
                               "read": dict(llama.file_sha256),
                               "fields_read": "row_id, prompt_tokens, target_tokens; dev unit membership"},
                     "olmo_refusal_check": {"path": OLMO_PREPARED_REL, "manifest_sha256": olmo.manifest_sha256,
                                            "engine_refuses_the_edit": True}},
        "recipe": {"path": LLAMA_MAIN_CONFIG_REL, "config_sha256": LLAMA_MAIN_CONFIG_SHA256,
                   "max_train_tokens": record["max_train_tokens"],
                   "note": "the family's main config (Part 1 section 10: add arms run under it); S_78 shares model.max_train_tokens"},
        "list": {"name": LIST_NAME, "sha256": LIST_SHA256, "rows": LIST_ROWS, "source": list_source},
        "stage1_s1_on_olmo": {"edit_sha256": OLMO_S1_EDIT_SHA256,
                              "record": {"path": STAGE1_ADD_S1_RECORD_REL, "sha256": STAGE1_ADD_S1_RECORD_SHA256},
                              "note": "the same 48 rows on the OLMo manifest 9ed61826 (C6: S1 is per manifest); OLMo-2-7B "
                                      "uses that edit as it stands (scripts/scale78b/s1_olmo2_7b_check.py)"},
        "full_out": {"default": FULL_OUT_REL,
                     "note": "the folder named tmp that --full-out names holds the text files below; they are pinned by "
                             "their SHA-256, not by their place, so this manifest does not record the operator's folder"},
        "files": [{"path": edit_rel, "sha256": edit.sha256, "arm": edit.arm, "edit_kind": "add",
                   "counts": edit.document["counts"], "rows": LIST_ROWS, "tokens": add_entry["tokens"]}],
        "rows": record["rows"],
        "record": {"path": wae.RECORD, "sha256": sha256_bytes(record_bytes)},
        "requirement": REQUIREMENT, "role": ROLE,
        "text": "the edit file and the list hold text and are written under tmp/ only (REQ-7's rule); MANIFEST.json, the "
                "record and the settings hold hashes and counts only"}
    manifest_bytes = canonical_json(manifest)
    texts = [t for item in listing["items"] for t in (item["prompt"], item["response"])]
    for name, blob in ((("MANIFEST.json", manifest_bytes), (SETTINGS_FILE, settings_bytes), (wae.RECORD, record_bytes))):
        if s1._text_hits(blob, texts):
            raise s1.Refusal(f"{name} would hold text")
    return {"out_files": {"MANIFEST.json": manifest_bytes, wae.RECORD: record_bytes, SETTINGS_FILE: settings_bytes},
            "full_files": {EDIT_FILE: data}, "manifest": manifest, "edit": edit, "listing_rows": len(listing["items"])}


def run(repo: Path, llama_root: Path, olmo_root: Path, recipe_path: Path, out: Path, full_out: Path,
        list_spec: str | None, olmo_edit: Path, stage1_record_path: Path) -> dict:
    """Guards, the list (given or recovered), the build, the writes. Returns name -> SHA-256 of every file written."""
    guard_out(out, repo)
    guard_out(full_out, repo)
    full_out = wae.full_out_ok(full_out)                               # REQ-7: text goes under a folder named tmp
    bsp.check_output_folders(full_out, out)
    written: dict[str, str] = {}
    list_written: Path | None = None
    try:
        if list_spec is not None:
            path, _, digest = list_spec.rpartition(":")
            if not path or digest != LIST_SHA256:
                raise s1.Refusal(f"--list is PATH:SHA256 with the sealed pin {LIST_SHA256}")
            list_path, list_source = Path(path), {"kind": "given", "path": rel(Path(path), repo)}
        else:
            olmo_stub = s1.PreparedView(olmo_root, OLMO_MANIFEST_SHA256).engine_stub()
            doc = recover_list(olmo_edit, olmo_stub, stage1_record(stage1_record_path))
            written.update({f"list/{LIST_NAME}.json": v for v in s1.write_new_files(full_out / "list", {f"{LIST_NAME}.json": doc}).values()})
            list_written = full_out / "list" / f"{LIST_NAME}.json"
            list_path = list_written
            list_source = {"kind": "recovered", "from": {"edit_sha256": OLMO_S1_EDIT_SHA256,
                                                        "record": STAGE1_ADD_S1_RECORD_REL,
                                                        "record_sha256": STAGE1_ADD_S1_RECORD_SHA256},
                           "written": f"list/{LIST_NAME}.json",
                           "rule": "the committed S1 edit's 48 add rows (engine parse_edit) in list order by the record's "
                                   "add_id -> list_id map, canonical JSON of {kind, version, name, items}; accepted only "
                                   "because it hashes to the sealed pin"}
        result = build(repo, llama_root, olmo_root, recipe_path, list_path, list_source)
        written.update({f"edits/{k}": v for k, v in s1.write_new_files(full_out / "edits", result["full_files"]).items()})
        written.update(s1.write_new_files(out, result["out_files"]).items())
    except (s1.Refusal, OSError):
        if list_written is not None and list_written.is_file() and sha256_path(list_written) == LIST_SHA256:
            list_written.unlink()                                        # this run's only earlier write
            for folder in (list_written.parent, full_out):
                if folder.is_dir() and not any(folder.iterdir()):
                    folder.rmdir()
        raise
    result["written"] = written
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", type=Path, default=REPO, help="the checkout that holds the inputs (default: this one)")
    parser.add_argument("--llama-prepared", type=Path, default=None, help=f"default <repo>/{LLAMA_PREPARED_REL}")
    parser.add_argument("--olmo-prepared", type=Path, default=None, help=f"default <repo>/{OLMO_PREPARED_REL}")
    parser.add_argument("--recipe", type=Path, default=None, help=f"default <repo>/{LLAMA_MAIN_CONFIG_REL}")
    parser.add_argument("--list", default=None, help=f"PATH:SHA256 of the sealed list (the pin is {LIST_SHA256[:12]}...)")
    parser.add_argument("--olmo-s1-edit", type=Path, default=None,
                        help=f"a copy of stage 1's add_s1.json (hash {OLMO_S1_EDIT_SHA256[:12]}...) to recover the list "
                             f"from when --list is not given; default <repo>/{OLMO_S1_EDIT_REL}")
    parser.add_argument("--stage1-record", type=Path, default=None, help=f"default <repo>/{STAGE1_ADD_S1_RECORD_REL}")
    parser.add_argument("--out", type=Path, default=HERE / "out", help="MANIFEST.json, the record, the settings (absent or empty)")
    parser.add_argument("--full-out", type=Path, default=None,
                        help=f"the edit (text) and the recovered list; default <repo>/{FULL_OUT_REL}; under a folder named tmp")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    full_out = (args.full_out or repo / FULL_OUT_REL)
    folders = [full_out, args.out]
    try:
        result = run(repo, (args.llama_prepared or repo / LLAMA_PREPARED_REL).resolve(),
                     (args.olmo_prepared or repo / OLMO_PREPARED_REL).resolve(),
                     (args.recipe or repo / LLAMA_MAIN_CONFIG_REL).resolve(), args.out.resolve(), full_out,
                     args.list, (args.olmo_s1_edit or repo / OLMO_S1_EDIT_REL).resolve(),
                     (args.stage1_record or repo / STAGE1_ADD_S1_RECORD_REL).resolve())
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} ({bsp.refusal_state(folders)})",
              file=sys.stderr)
        return 2
    m = result["manifest"]
    print(f"built S1 on {LLAMA_MANIFEST_SHA256[:8]}: {result['listing_rows']} rows; arm {m['files'][0]['arm']}; "
          f"max_train_tokens {m['recipe']['max_train_tokens']}; list {m['list']['sha256'][:12]}... ({m['list']['source']['kind']})")
    print(f"script sha256 {m['script']['sha256']}; settings {m['settings']['sha256']}; engine {m['engine_identity_sha256']}")
    for name, digest in sorted(result["written"].items()):
        print(f"  {digest}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
