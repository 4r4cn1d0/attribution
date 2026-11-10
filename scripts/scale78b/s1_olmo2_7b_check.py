"""S1 for OLMo-2-7B: is stage 1's committed S1 add edit OLMo-2-7B's S1 edit as it stands? Part 1 section 14 item 1 (the
same 48 S-pool rows, re-bound to the family manifest; the check's C6) and the build brief's first S1 question. OLMo-2-7B's
manifest IS stage 1's (prepared-kt-dolly-olmo2, 9ed61826...; Part 1 section 2.1), so the only things that could differ
are the recipe's token limit (encode_train refuses an over-long row) and the writer's environment. Mac, $0.

Measured, not judged:
 (1) the engine's parse_edit accepts the committed edit (add_s1.json, 904a0cf1...) against the OLMo-2-7B family
     manifest;
 (2) every one of its 48 add rows encodes with the OLMo codec under the OLMo-2-7B main recipe's model.max_train_tokens
     (18cc31d7...) to the committed prompt and target token counts (edited_corpus -> encode_train), and under the 1B
     recipe S's limit (ceffe0ef...) to the same; the two limits are printed;
 (3) REQ-7's frozen writer (scripts/stage1/write_add_edit.py, pinned), run again on the sealed list with the OLMo set and
     the 1B recipe S, gives the committed bytes (the frozen path reproduces in this environment); run with the OLMo-2-7B
     main recipe instead, the only differences are named (keys and hashes), so the lead sees what a "7B rebuild" would
     change: the provenance's recipe hash and the settings hash, never a row.
Verdict "equal as it stands" when (1), (2) and (3)'s reproduction hold: nothing is built for OLMo-2-7B; the kit copies
add_s1.json by its hash, as stage 1 did. Otherwise the verdict names what failed and a 7B edit must be built.

The sealed list is read through REQ-7's read_list by its pin (389c20ad...); its bytes come from --list PATH:SHA256 or
are recovered by the sealed Llama build script's recover_list (the committed edit's rows in list order, verified by the
pin) and written under --scratch-tmp (a folder named tmp, absent or empty). Unless --keep, the end of the run removes only
what this run made, decided atomically by its own mkdir: the recovered list's folder, then the scratch folder if this run
created it and it is empty; a folder that existed before the run is never removed, a non-empty one is refused and left as
it was, and --out may not lie under --scratch-tmp (reverify-F RF-1, RF-2): by its spelling before anything is made, and
by directory identity once the scratch folder exists (os.path.samefile on --out's deepest existing ancestor and every
folder above it, so a case variant or another alias of the same folder is refused too; m-verify D1).
Reads: the committed edit's bytes by exact path (refused unless they hash to the pin; through the engine's parse_edit,
the text dropped at once); the committed add-s1 record; the OLMo prepared set (ids and token counts); the two configs.
Prints counts and hashes only; --out writes a text-free record (created once).
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402
from experiments.safety_selection.edits import EditError, edited_corpus, parse_edit  # noqa: E402
from scripts.stage1 import build_s_pool as bsp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402

KIND = "scale-78b S1 check for OLMo-2-7B"
SEALED_BUILDER_REL = ".ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py"
OLMO_PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-olmo2"
OLMO_MANIFEST_SHA256 = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
OLMO_7B_MAIN_CONFIG_REL = "experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json"
OLMO_7B_MAIN_CONFIG_SHA256 = "18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09"
RECIPE_S_1B_REL = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"
RECIPE_S_1B_SHA256 = "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
SCRATCH_REL = "tmp/scale-78b-s1-olmo2-7b-check"
SEAL_EDITS_REL = ".ai/inputs/gate-b-sealed-20261008/out/edits"      # R_d2, R_d3, R_d4: stage 1's --combine-with inputs
VERDICT_EQUAL = "equal as it stands: the committed S1 edit is OLMo-2-7B's S1 edit byte for byte; build nothing for OLMo"
VERDICT_DIFFERS = "differs: a 7B S1 edit must be built"


def load_sealed_builder(repo: Path):
    """The sealed Llama S1 build script (its pins and recover_list), by path."""
    path = repo / SEALED_BUILDER_REL
    spec = importlib.util.spec_from_file_location("build_s1_llama3_for_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recipe_limit(path: Path, pin: str) -> int:
    recipe = load_recipe(path)
    if config_sha256(recipe) != pin:
        raise s1.Refusal(f"{path.name} hashes to {config_sha256(recipe)}, the pin is {pin}")
    return recipe["model"]["max_train_tokens"]


def row_tokens(edit, stub, codec, max_tokens: int) -> dict[str, tuple[int, int]]:
    """Per add id (prompt tokens, target tokens) through the engine's edited_corpus under max_tokens; a refusal of any
    row is returned as the exception's type name (no text)."""
    try:
        encoded = edited_corpus({}, edit, stub, codec, max_tokens)
    except Exception as exc:                                                   # the engine's TooLong / ControlTokenError
        raise s1.Refusal(f"the engine refuses an add row under max_train_tokens {max_tokens} ({type(exc).__name__})") from None
    return {row_id: (ex.n_prompt, ex.n_target) for row_id, ex in encoded.items()}


def provenance_differences(a: dict, b: dict) -> list[str]:
    """Dotted keys at which two edit documents differ (values are hashes or version strings; rows are compared too)."""
    out = []

    def walk(x, y, path):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                walk(x.get(k), y.get(k), f"{path}.{k}" if path else k)
        elif x != y:
            out.append(path)
    walk(a, b, "")
    return out


def check(repo: Path, olmo_root: Path, edit_path: Path, record_path: Path, recipe_7b: Path, recipe_s: Path,
          scratch: Path, list_spec: str | None, seal_edits: Path, made: list[Path] | None = None) -> dict:
    """The measurement (module doc). ``made``, when given, receives every folder this call itself created (the
    recovered list's folder scratch/list, appended right after its atomic mkdir), so the caller removes only those."""
    B = load_sealed_builder(repo)
    frozen = B.check_frozen() if Path(B.REPO).resolve() == repo.resolve() else {k: sha256_bytes((repo / k).read_bytes()) for k in B.FROZEN}
    record = B.stage1_record(record_path)
    data = Path(edit_path).read_bytes()
    if sha256_bytes(data) != B.OLMO_S1_EDIT_SHA256:
        raise s1.Refusal(f"the S1 edit hashes to {sha256_bytes(data)}, the pin is {B.OLMO_S1_EDIT_SHA256}")
    view = s1.PreparedView(olmo_root, OLMO_MANIFEST_SHA256)
    stub = view.engine_stub()
    try:
        edit = parse_edit(data, stub)                                                      # (1)
    except EditError as exc:
        raise s1.Refusal(f"the engine refuses the committed S1 edit against the OLMo-2-7B manifest ({type(exc).__name__})") from None
    accepted = edit.document["manifest_sha256"] == OLMO_MANIFEST_SHA256 and len(edit.added) == B.LIST_ROWS
    codec = bsp.real_codec(olmo_root, {"inputs": {"prepared_manifest_sha256": OLMO_MANIFEST_SHA256}})
    limit_7b, limit_s = recipe_limit(recipe_7b, OLMO_7B_MAIN_CONFIG_SHA256), recipe_limit(recipe_s, RECIPE_S_1B_SHA256)
    committed = {r["add_id"]: (r["prompt_tokens"], r["target_tokens"]) for r in record["rows"]}
    under_7b, under_s = row_tokens(edit, stub, codec, limit_7b), row_tokens(edit, stub, codec, limit_s)   # (2)
    equal_7b = sum(1 for k, v in under_7b.items() if committed.get(k) == v)
    equal_s = sum(1 for k, v in under_s.items() if committed.get(k) == v)
    longest = max(p + t + 1 for p, t in under_7b.values())                                   # prompt + target + eos
    # (3) the frozen writer on the sealed list, the OLMo set and recipe S: the committed bytes?
    scratch = wae.full_out_ok(scratch)
    bsp.check_output_folders(scratch)
    if list_spec is not None:
        path, _, digest = list_spec.rpartition(":")
        if not path or digest != B.LIST_SHA256:
            raise s1.Refusal(f"--list is PATH:SHA256 with the sealed pin {B.LIST_SHA256}")
        list_path, list_source = Path(path), "given"
    else:
        doc = B.recover_list(edit_path, stub, record)
        # RF-1 (reverify-F): the list folder is this call's only if this call's mkdir made it (atomic: another run's
        # folder raises FileExistsError and is refused, never written into and never removed by this run).
        try:
            (scratch / "list").mkdir(parents=True)
        except FileExistsError:
            raise s1.Refusal(f"{scratch / 'list'} exists: a sealed output never overwrites") from None
        if made is not None:
            made.append(scratch / "list")
        s1.write_new_files(scratch / "list", {"s1.json": doc})
        list_path, list_source = scratch / "list" / "s1.json", "recovered (build_s1_llama3.recover_list; verified by the pin)"
    listing = wae.read_list(list_path, B.LIST_SHA256)
    base, base_sha = s1.load_settings(repo / B.STAGE1_SETTINGS_REL, B.STAGE1_SETTINGS_SHA256, wae.SETTINGS_NAME)
    # Stage 1 built add_s1.json in one run with the combined edits R_d2+s1, R_d3+s1 and R_d4+s1, so the provenance block
    # that every file of that run shares names the three remove edits (the record's provenance.inputs remove_<NAME>);
    # the same three SEAL files, pinned by the record's hashes, are passed here so the frozen writer sees the same inputs.
    combine = [(key[len("remove_"):], seal_edits / f"{key[len('remove_'):]}.json", digest)
               for key, digest in sorted(record["provenance"]["inputs"].items()) if key.startswith("remove_")]
    files_s, _ = wae.build(olmo_root, listing, combine, codec, base, base_sha, recipe_s)
    rebuilt_s = sha256_bytes(files_s["add_s1.json"])
    reproduced = rebuilt_s == B.OLMO_S1_EDIT_SHA256
    settings_7b = copy.deepcopy(base)
    settings_7b["recipe_sha256"] = OLMO_7B_MAIN_CONFIG_SHA256
    settings_7b_sha = sha256_bytes(canonical_json(settings_7b))
    files_7b, _ = wae.build(olmo_root, listing, combine, codec, settings_7b, settings_7b_sha, recipe_7b)
    doc_s, doc_7b = s1.strict_json(files_s["add_s1.json"]), s1.strict_json(files_7b["add_s1.json"])
    diffs = provenance_differences(doc_s, doc_7b)
    rows_equal_across_recipes = doc_s["add"] == doc_7b["add"]
    equal_as_is = accepted and equal_7b == B.LIST_ROWS and equal_s == B.LIST_ROWS and reproduced and rows_equal_across_recipes
    return {"kind": KIND, "version": 1,
            "rule": "Part 1 section 14 item 1; the readiness check's C6; REQ-7's rule (scripts/stage1/write_add_edit.py)",
            "family": {"name": "olmo2-7b", "manifest_sha256": OLMO_MANIFEST_SHA256,
                       "main_config": {"path": OLMO_7B_MAIN_CONFIG_REL, "config_sha256": OLMO_7B_MAIN_CONFIG_SHA256,
                                       "max_train_tokens": limit_7b}},
            "stage1": {"edit_sha256": B.OLMO_S1_EDIT_SHA256, "edit_path": str(Path(edit_path).resolve()),
                       "record": {"path": B.STAGE1_ADD_S1_RECORD_REL, "sha256": B.STAGE1_ADD_S1_RECORD_SHA256},
                       "recipe_s_1b": {"path": RECIPE_S_1B_REL, "config_sha256": RECIPE_S_1B_SHA256, "max_train_tokens": limit_s},
                       "list_sha256": B.LIST_SHA256, "list_source": list_source,
                       "combine_with": [{"name": n, "path": f"{SEAL_EDITS_REL}/{n}.json", "sha256": d} for n, _, d in combine]},
            "frozen_code": frozen, "engine_identity_sha256": code_identity()["sha256"],
            "python": sys.version.split()[0],
            "checks": {"1_parse_edit_accepts_against_the_family_manifest": accepted,
                       "2_rows_with_the_committed_token_counts_under_the_7b_limit": {"equal": equal_7b, "of": B.LIST_ROWS},
                       "2_rows_with_the_committed_token_counts_under_the_1b_recipe_s_limit": {"equal": equal_s, "of": B.LIST_ROWS},
                       "2_longest_row_tokens_with_eos": longest,
                       "3_frozen_writer_reproduces_the_committed_bytes": {"rebuilt_sha256": rebuilt_s, "committed_sha256": B.OLMO_S1_EDIT_SHA256,
                                                                          "equal": reproduced},
                       "3_rebuild_under_the_7b_main_recipe": {"sha256": sha256_bytes(files_7b["add_s1.json"]),
                                                              "differs_from_the_committed_edit_at": diffs,
                                                              "add_rows_identical": rows_equal_across_recipes,
                                                              "settings_sha256_used": settings_7b_sha}},
            "verdict": VERDICT_EQUAL if equal_as_is else VERDICT_DIFFERS, "equal_as_it_stands": equal_as_is}


def lies_in(out: Path, scratch: Path) -> bool:
    """True when ``out`` is or lies under the EXISTING folder ``scratch`` by directory identity (m-verify D1): the
    deepest existing ancestor of ``out`` (``out`` itself when it exists) and every folder above it are compared with
    ``scratch`` by os.path.samefile, so another spelling of the same folder (a case variant on a case-insensitive file
    system, a firmlink or a symbolic link) is caught where a string comparison is not."""
    node = Path(os.path.abspath(out))
    while not node.exists() and node != node.parent:
        node = node.parent
    return any(os.path.samefile(folder, scratch) for folder in (node, *node.parents))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--olmo-prepared", type=Path, default=None, help=f"default <repo>/{OLMO_PREPARED_REL}")
    parser.add_argument("--edit", type=Path, default=None, help="a copy of stage 1's add_s1.json (default: the sealed builder's default path)")
    parser.add_argument("--stage1-record", type=Path, default=None)
    parser.add_argument("--recipe-7b", type=Path, default=None, help=f"default <repo>/{OLMO_7B_MAIN_CONFIG_REL}")
    parser.add_argument("--recipe-s", type=Path, default=None, help=f"default <repo>/{RECIPE_S_1B_REL}")
    parser.add_argument("--list", default=None, help="PATH:SHA256 of the sealed list (else recovered)")
    parser.add_argument("--scratch-tmp", type=Path, default=None, help=f"default <repo>/{SCRATCH_REL} (under tmp; absent or empty)")
    parser.add_argument("--keep", action="store_true", help="keep the scratch folder (the recovered list) after the check")
    parser.add_argument("--out", type=Path, default=None, help="the text-free record (created once)")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    B = load_sealed_builder(repo)
    scratch = (args.scratch_tmp or repo / SCRATCH_REL).resolve()
    # RF-2 (reverify-F): the record must outlive the cleanup, so --out may not lie in (or be) the scratch folder.
    if args.out is not None:
        out = args.out.resolve()
        if out == scratch or scratch in out.parents:
            print(f"REFUSED: --out {args.out} lies under --scratch-tmp {scratch}, which the cleanup removes", file=sys.stderr)
            return 2
    # F-1 (verify-F) and RF-1 (reverify-F): the cleanup removes only what this run made, decided atomically. The scratch
    # folder is this run's only if this run's mkdir created it (FileExistsError: it existed, or another run made it
    # first). The cleanup removes the folders this run made inside it (the recovered list, `made`), then the scratch
    # folder only if this run created it and it is empty; anything another party put there stays. A scratch folder that
    # existed before this run is never removed (a non-empty one is refused by check_output_folders and stays as it was).
    made: list[Path] = []
    created = False
    try:
        if args.out is not None and args.out.exists():
            raise s1.Refusal(f"--out {args.out} exists: the record is created once")
        scratch = wae.full_out_ok(scratch)              # under a folder named tmp, checked before anything is created
        try:
            scratch.mkdir(parents=True)
            created = True
        except FileExistsError:
            created = False
        if args.out is not None and lies_in(args.out, scratch):   # RF-2 by identity (m-verify D1), before any data
            print(f"REFUSED: --out {args.out} lies under --scratch-tmp {scratch} (the same folder by identity), which the "
                  "cleanup removes", file=sys.stderr)
            return 2
        result = check(repo, (args.olmo_prepared or repo / OLMO_PREPARED_REL).resolve(),
                       (args.edit or repo / B.OLMO_S1_EDIT_REL).resolve(),
                       (args.stage1_record or repo / B.STAGE1_ADD_S1_RECORD_REL).resolve(),
                       (args.recipe_7b or repo / OLMO_7B_MAIN_CONFIG_REL).resolve(),
                       (args.recipe_s or repo / RECIPE_S_1B_REL).resolve(), scratch, args.list, repo / SEAL_EDITS_REL,
                       made)
        data = canonical_json(result)
        if args.out is not None:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with open(args.out, "xb") as handle:
                handle.write(data)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__}", file=sys.stderr)
        return 2
    finally:
        if not args.keep:
            for folder in reversed(made):
                if folder.is_dir() and not folder.is_symlink():
                    shutil.rmtree(folder)
            if created:
                try:
                    scratch.rmdir()                       # only when empty: another party's files are never removed
                except OSError:
                    print(f"note: {scratch} was created by this run but holds files it did not write; left as it is",
                          file=sys.stderr)
    c = result["checks"]
    print(f"(1) parse_edit accepts the committed S1 edit against {OLMO_MANIFEST_SHA256[:8]}: {c['1_parse_edit_accepts_against_the_family_manifest']}")
    print(f"(2) rows with the committed token counts: {c['2_rows_with_the_committed_token_counts_under_the_7b_limit']['equal']} of 48 under the 7B "
          f"main recipe's limit {result['family']['main_config']['max_train_tokens']}; "
          f"{c['2_rows_with_the_committed_token_counts_under_the_1b_recipe_s_limit']['equal']} of 48 under recipe S's "
          f"{result['stage1']['recipe_s_1b']['max_train_tokens']}; longest row {c['2_longest_row_tokens_with_eos']} tokens")
    r3 = c["3_frozen_writer_reproduces_the_committed_bytes"]
    print(f"(3) frozen writer on the sealed list + OLMo set + recipe S: {r3['rebuilt_sha256']} == committed {r3['committed_sha256']}: {r3['equal']}")
    r4 = c["3_rebuild_under_the_7b_main_recipe"]
    print(f"    under the 7B main recipe: {r4['sha256']}; add rows identical {r4['add_rows_identical']}; differs at {r4['differs_from_the_committed_edit_at']}")
    print(f"verdict: {result['verdict']}")
    if args.out is not None:
        print(f"record {sha256_bytes(data)} {args.out}")
    return 0 if result["equal_as_it_stands"] else 1


if __name__ == "__main__":
    sys.exit(main())
