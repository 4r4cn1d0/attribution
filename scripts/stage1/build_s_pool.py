"""REQ-6: the S-pool and its prompt lists (RS B5; PLAN-S:145-147, :171; addendum L8-L11, section 3 (1); W1-11).
Mac, CPU, $0; the lead runs it on the real files. It prints counts and hashes only.

Reads, each checked before use:
- ANCH, the pinned Gate C anchor builder (.ai/inputs/gate-b-anchors-20261008/make_anchor_prompts.py, SHA-256 in the
  settings), loaded by path and never run as a script: its data-config check (load_config), its PKU reader
  (read_sources: the engine's parse_pku after the config's file pins) and its evaluation form set (load_evaluation:
  every bank of P, all splits, every ARC form, as L9 (1) asks).
- the data config (study-v3-data-inj05.json), P (its manifest), the full anchor prompt list (78467c97...) and REC (the
  recipe; its max_train_tokens and max_prompt_tokens are read, never hard-coded), all pinned in the settings; the
  lexicon through lexicon_pin (REQ-1).

Candidate (L8): a PKU response with is_safe true whose lexicon class is REFUSAL-OPENING, in a record whose other
response has is_safe false. Candidate order: the config's source order, then line, then response index (ANCH's).
Candidate id: ANCH's uid, "<source>:<line as 6 digits>:<response index>".

Filters, in order; each runs on the previous filter's survivors and N is reported after each:
1. empty text: empty_prompt, empty_response (strip() is empty);
2. control_string: a forbidden substring (the config's and P's eligibility lists) in the prompt or the response;
3. exact overlap: overlap_with_an_existing_or_evaluation_prompt (the normalized prompt equals a training, query or
   evaluation form of P; ANCH's label), overlap_with_an_anchor_prompt (one of the 128 anchor prompts);
4. near duplicate: near_duplicate_of_evaluation_prompt (character 5-gram Jaccard >= the config's
   injection.near_duplicate.max_jaccard with an evaluation form of P; counted per bank, dev, selector and hidden),
   near_duplicate_of_anchor_prompt (the same with an anchor prompt);
5. encode_train_<error>: encode_train(prompt, response) refuses under REC's max_train_tokens;
6. generation_prompt_<error>: encode_generation_prompt(prompt) refuses under REC's max_prompt_tokens (section 3 (1));
7. duplicate_prompt: not the first candidate of its normalized prompt, in candidate order.
Within one filter a row counts under every reason of that filter that it meets; it is removed once.

Lists (sealed orders over the S-pool's ids): S1 = the first 48 by s1.order; the S3 subset = the first 1,000 by
s3.subset (overlap with S1 allowed and counted, L10); the S4 candidates = the S-pool minus S1 by s4.order, the first
512 (L11; REQ-9 keeps the first 48 that pass).
Stop with counts only (nothing written) if N < 1,000 after the last filter (section 3 (1)), or if the S-pool cannot fill
S1, the S3 subset, S4 and REQ-8's 37 decoy rows (which come from the S-pool rows outside S1, the S3 subset and S4); the
stop message carries the candidate count, N after each filter and each filter's removals by reason. Before anything is
written, both output folders must be absent or empty (so a refusal never leaves a partial output).

Report only (L8): the candidates (and the S-pool rows) whose record's safer_response_id, and separately
better_response_id, names the other response; both read by the row's line from the same hash-checked bytes after
parse_pku; a value that is not the integer 0 or 1 refuses. W1-11: every S-pool row's source file, line, response index
and companion (other) response index are in the record. L10: |S1 & S3 subset| beside 48 x 1,000 / N.

Writes text only under --full-out (which must lie in a folder named tmp): s_pool.json, s1.json, s3_subset.json,
s4_candidates.json and s3_safe.pool.json (REQ-3's pool: the S3 subset, then S1's rows outside it; L10 (2)); and a text-free
record, s_pool_record.json, into --out. No Qwen3Guard or other classifier filters the pool.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import lexicon_pin  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "build_s_pool.json"
SETTINGS_SHA256 = "6080487c8efa6682259ecd977f517a151a8e8aecf80d7aea45e6a23911a943a4"
SETTINGS_NAME = "build_s_pool"
RECORD = "s_pool_record.json"
POOL_FILE, S3_POOL = "s_pool.json", "s3_safe.pool.json"
LIST_FILES = {"s1": "s1.json", "s3_subset": "s3_subset.json", "s4_candidates": "s4_candidates.json"}
BANK_NAMES = ("dev", "selector", "hidden")
FILTERS = ("empty", "control_string", "exact_overlap", "near_duplicate", "encode_train", "generation_prompt",
           "first_per_prompt")


# ----- pinned inputs ------------------------------------------------------------------------------------------


def engine_root() -> Path:
    """The checkout that holds the engine package (the repository on the Mac; the workspace when a test tool runs a
    copy of scripts/stage1): pinned repository files are read from here."""
    import experiments.safety_selection as engine

    return Path(engine.__file__).resolve().parents[2]


def load_anch(path: Path, expected_sha256: str):
    """ANCH by path after its SHA-256 check (never copied, edited or run as a script)."""
    try:
        digest = sha256_file(path)
    except OSError as exc:
        raise s1.Refusal(f"ANCH cannot be read ({type(exc).__name__})") from None
    if digest != expected_sha256:
        raise s1.Refusal(f"ANCH hashes to {digest}, the settings pin {expected_sha256}")
    spec = importlib.util.spec_from_file_location("stage1_pinned_anch", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def anch_call(function, *args):
    """An ANCH function; its Stop (a SystemExit with a counts-only message) becomes a Refusal."""
    try:
        return function(*args)
    except SystemExit as exc:
        raise s1.Refusal(f"ANCH stopped: {exc}") from None


def recipe_limits(rec_path: Path, expected_sha256: str) -> dict:
    from experiments.safety_selection.config import config_sha256, load_recipe

    recipe = load_recipe(rec_path)
    if config_sha256(recipe) != expected_sha256:
        raise s1.Refusal(f"REC hashes to {config_sha256(recipe)}, the settings pin {expected_sha256}")
    model = recipe["model"]
    return {"max_train_tokens": model["max_train_tokens"], "max_prompt_tokens": model["max_prompt_tokens"],
            "repo_id": model["repo_id"], "revision": model["revision"]}


def anchor_prompts(path: Path, expected_sha256: str, anch) -> list[str]:
    data = path.read_bytes()
    if sha256_bytes(data) != expected_sha256:
        raise s1.Refusal(f"the anchor prompt list hashes to {sha256_bytes(data)}, the settings pin {expected_sha256}")
    anch_call(anch.validate_list, data)
    return [p["prompt"] for p in s1.strict_json(data)["prompts"]]


def evaluation_by_bank(prepared_root: Path, manifest_sha256: str, anch) -> dict[str, list[tuple[str, str]]]:
    """Every evaluation form of P per bank, by ANCH's own loop (load_prepared with every bank, the hidden one allowed),
    checked equal, in order, to ANCH's load_evaluation list."""
    from experiments.safety_selection.prepare import load_prepared
    from experiments.safety_selection.textproc import arc_prompt_forms

    prepared = load_prepared(prepared_root, manifest_sha256, banks=BANK_NAMES, allow_hidden=True)
    out = {}
    for bank in BANK_NAMES:
        forms = []
        for item in prepared.banks[bank]:
            if item["kind"].startswith("arc_"):
                forms += [(item["prompt_id"], f) for f in dict.fromkeys(
                    arc_prompt_forms(item["question"], item["labels"], item["texts"]))]
            else:
                forms.append((item["prompt_id"], item["prompt"]))
        out[bank] = forms
    return out


# ----- the rule ---------------------------------------------------------------------------------------------


def uid(row: dict) -> str:
    return f"{row['source']}:{row['line']:06d}:{row['response_index']}"


def candidates_of(rows: list[dict], classify, wanted: str = "REFUSAL-OPENING") -> list[dict]:
    """L8's candidates in candidate order: safe, of lexicon class wanted (REFUSAL-OPENING; REQ-8 asks DIRECT), and the
    record's other response unsafe."""
    by_record = {}
    for row in rows:
        by_record.setdefault((row["source"], row["line"]), {})[row["response_index"]] = row
    out = []
    for row in rows:
        other = by_record[(row["source"], row["line"])].get(1 - row["response_index"])
        if row["safe"] and other is not None and not other["safe"] and classify(row["response"]) == wanted:
            out.append({**row, "companion_index": other["response_index"]})
    return out


def record_ids(source_bytes: dict[str, bytes], rows: list[dict]) -> dict[str, dict]:
    """L8 / W1-11: the safer and better response ids of each row's record, read by line from the hash-checked bytes."""
    from experiments.safety_selection.sources import _jsonl_lines

    by_line = {}
    for source, data in source_bytes.items():
        lines, _ = _jsonl_lines(data, source)
        for number, line in lines:
            by_line[(source, number)] = line
    out = {}
    for row in rows:
        line = by_line.get((row["source"], row["line"]))
        if line is None:
            raise s1.Refusal(f"{uid(row)}: its line is not in the source file")
        obj = s1.strict_json(line)
        ids = {}
        for field in ("safer_response_id", "better_response_id"):
            value = obj.get(field)
            if type(value) is not int or value not in (0, 1):                # a bool or a float such as 1.0 refuses
                raise s1.Refusal(f"{uid(row)}: {field} is not the integer 0 or 1")
            ids[field] = value
        for index in (row["response_index"], row["companion_index"]):
            if type(index) is not int or index not in (0, 1):
                raise s1.Refusal(f"{uid(row)}: a response index is not the integer 0 or 1")
        if obj.get(f"is_response_{row['companion_index']}_safe") is not False:
            raise s1.Refusal(f"{uid(row)}: the companion response is not marked unsafe in the bytes")
        out[uid(row)] = ids
    return out


def run_filters(cands: list[dict], *, forbidden: list[str], existing: set[str], anchors: list[str],
                evaluation: dict[str, list[tuple[str, str]]], max_jaccard: float, codec, limits: dict,
                stages: tuple[str, ...] = FILTERS) -> dict:
    """The filters in order (all seven by default; REQ-8 runs the first six): the survivors, counts by reason per filter, N after each filter, and per bank the
    largest near-duplicate score of a survivor (no id, no text)."""
    from experiments.safety_selection.prepare import _NearDuplicates
    from experiments.safety_selection.textproc import encode_generation_prompt, encode_train, normalize

    anchor_set = {normalize(a) for a in anchors} - {""}
    near = {bank: _NearDuplicates(forms) for bank, forms in evaluation.items()}
    near_anchor = _NearDuplicates([(f"anchor-{k:03d}", a) for k, a in enumerate(anchors)])
    scores: dict[str, dict] = {}

    def reasons_of(stage: str, row: dict) -> list[str]:
        prompt, response = row["prompt"], row["response"]
        if stage == "empty":
            return [r for r, bad in (("empty_prompt", not prompt.strip()), ("empty_response", not response.strip())) if bad]
        if stage == "control_string":
            return ["control_string"] if any(s in t for t in (prompt, response) for s in forbidden) else []
        if stage == "exact_overlap":
            key = normalize(prompt)
            return [r for r, bad in (("overlap_with_an_existing_or_evaluation_prompt", key in existing),
                                     ("overlap_with_an_anchor_prompt", key in anchor_set)) if bad]
        if stage == "near_duplicate":
            key = normalize(prompt)
            if key not in scores:
                scores[key] = {bank: index.nearest(prompt)[0] for bank, index in near.items()}
                scores[key]["anchors"] = near_anchor.nearest(prompt)[0]
            out = [f"near_duplicate_of_evaluation_prompt_{bank}" for bank in near if scores[key][bank] >= max_jaccard]
            return out + (["near_duplicate_of_anchor_prompt"] if scores[key]["anchors"] >= max_jaccard else [])
        if stage == "encode_train":
            try:
                encode_train(codec, uid(row), prompt, response, limits["max_train_tokens"])
            except ValueError as exc:
                return [f"encode_train_{type(exc).__name__}"]
            return []
        if stage == "generation_prompt":
            try:
                encode_generation_prompt(codec, prompt, limits["max_prompt_tokens"])
            except ValueError as exc:
                return [f"generation_prompt_{type(exc).__name__}"]
            return []
        raise AssertionError(stage)

    rows, counts, n_after = list(cands), {}, {"candidates": len(cands)}
    for stage in stages:
        kept, reasons = [], Counter()
        if stage == "first_per_prompt":
            seen = set()
            for row in rows:
                key = normalize(row["prompt"])
                if key in seen:
                    reasons["duplicate_prompt"] += 1
                else:
                    seen.add(key)
                    kept.append(row)
        else:
            for row in rows:
                why = reasons_of(stage, row)
                reasons.update(why)
                if not why:
                    kept.append(row)
        counts[stage] = {"removed": len(rows) - len(kept), "by_reason": dict(sorted(reasons.items()))}
        n_after[stage] = len(kept)
        rows = kept
    largest = {}
    for name in list(near) + ["anchors"]:
        values = [scores[normalize(r["prompt"])][name] for r in rows]
        largest[name] = max(values) if values else None
    return {"pool": rows, "filters": counts, "n_after": n_after, "largest_kept_jaccard": largest}


def lists_of(pool_ids: list[str], settings: dict) -> dict[str, list[str]]:
    sizes = settings["lists"]
    s1_ids = s1.sealed_order(pool_ids, "s1.order")[:sizes["s1"]["size"]]
    s3_ids = s1.sealed_order(pool_ids, "s3.subset")[:sizes["s3_subset"]["size"]]
    rest = sorted(set(pool_ids) - set(s1_ids))
    s4_ids = s1.sealed_order(rest, "s4.order")[:sizes["s4_candidates"]["size"]]
    return {"s1": s1_ids, "s3_subset": s3_ids, "s4_candidates": s4_ids}


def filter_counts(result: dict | None) -> str:
    """The counts a stop reports (section 3 (1): N after each filter; REC rule 26): the candidate count, N after each
    filter in order and each filter's removals by reason. Counts only, no id and no text."""
    if result is None:
        return "filter counts not available"
    by_reason = {stage: counts["by_reason"] for stage, counts in result["filters"].items()}
    return f"N after each filter {result['n_after']}; removed by reason {by_reason}"


def check_sizes(n: int, lists: dict[str, list[str]], settings: dict, result: dict | None = None) -> dict:
    """The stop rule (section 3 (1); the brief's stop count with REQ-8's decoy rows). The stop message carries the
    filter counts (run_filters' result) beside N, the short lists and the decoy room."""
    sizes = settings["lists"]
    short = {name: len(lists[name]) for name in lists if len(lists[name]) < sizes[name]["size"]}
    outside = n - len(set().union(*map(set, lists.values())))
    need = settings["decoy_rows"]
    if n < settings["min_pool"] or short or outside < need:
        raise s1.Refusal(f"the S-pool cannot fill its lists: N = {n} (min_pool {settings['min_pool']}), short lists "
                         f"{short}, {outside} rows outside S1, the S3 subset and S4 for {need} decoy rows; "
                         f"{filter_counts(result)} (counts only; nothing written)")
    return {"rows_outside_the_lists": outside, "decoy_rows_needed": need}


def check_output_folders(*folders: Path) -> list[Path]:
    """Every output folder absent or empty, no two the same or nested, before the first write: a refusal after this
    check and before the writes leaves nothing written, and write_new_files then never refuses after a write."""
    out = [Path(f).resolve() for f in folders]
    for folder in out:
        if folder.is_file() or (folder.is_dir() and any(folder.iterdir())):
            raise s1.Refusal(f"{folder} exists and is not empty: a sealed output never overwrites")
    for i, a in enumerate(out):
        for b in out[i + 1:]:
            if a == b or a in b.parents or b in a.parents:
                raise s1.Refusal("the output folders must be distinct and not nested")
    return out


def refusal_state(folders) -> str:
    """What a refusal left behind, for the REFUSED line: the output folders were absent or empty before the first
    write (check_output_folders), so every file now under them is this run's. Counts only."""
    left = sum(1 for d in folders if Path(d).exists() for p in Path(d).rglob("*") if p.is_file())
    return "nothing written" if left == 0 else f"{left} files left under the output folders"


# ----- the build --------------------------------------------------------------------------------------------


def build(*, config_path: Path, sources_root: Path, prepared_root: Path, anchors_path: Path, rec_path: Path,
          codec, settings: dict, settings_sha256: str) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """(full files with text, record files without text); nothing is written here."""
    s1.check_settings(settings, SETTINGS_NAME)
    pins = settings["inputs"]
    anch = load_anch(engine_root() / pins["anch"]["path"], pins["anch"]["sha256"])
    config, config_sha = anch_call(anch.load_config, config_path, pins["data_config"]["sha256"])
    limits = recipe_limits(rec_path, pins["rec_recipe_sha256"])
    sources = anch_call(anch.read_sources, config, sources_root)
    source_bytes = {}
    for name in config["injection"]["sources"]:
        spec = config["extra_sources"][name]
        data = (Path(sources_root) / spec["local"]).read_bytes()
        if sha256_bytes(data) != spec["sha256"]:
            raise s1.Refusal(f"{name}: the bytes changed after the reader's check")
        source_bytes[name] = data
    evaluation = anch_call(anch.load_evaluation, prepared_root, pins["prepared_manifest_sha256"])
    by_bank = evaluation_by_bank(prepared_root, pins["prepared_manifest_sha256"], anch)
    if [f for bank in BANK_NAMES for f in by_bank[bank]] != evaluation["evaluation"]:
        raise s1.Refusal("the per-bank evaluation forms differ from ANCH's evaluation list")
    expected_forms = settings["expected_evaluation_forms"]
    if evaluation["forms"] != expected_forms:
        raise s1.Refusal(f"P has {evaluation['forms']} evaluation forms, the settings expect {expected_forms} (L9 (2))")
    anchors = anchor_prompts(anchors_path, pins["anchor_prompts_sha256"], anch)
    lexicon = lexicon_pin.load()
    max_jaccard = config["injection"]["near_duplicate"]["max_jaccard"]
    if max_jaccard != settings["max_jaccard"]:
        raise s1.Refusal(f"the config's max_jaccard is {max_jaccard}, the settings name {settings['max_jaccard']}")
    forbidden = sorted(set(config["eligibility"]["forbidden_substrings"]) | set(evaluation["forbidden"]))

    cands = candidates_of(sources["rows"], lexicon.classify)
    ids_by_row = record_ids(source_bytes, cands)
    result = run_filters(cands, forbidden=forbidden, existing=evaluation["existing"], anchors=anchors,
                         evaluation=by_bank, max_jaccard=max_jaccard, codec=codec, limits=limits)
    pool = result["pool"]
    pool_ids = [uid(r) for r in pool]
    lists = lists_of(pool_ids, settings)
    room = check_sizes(len(pool), lists, settings, result)

    by_id = {uid(r): r for r in pool}
    pool_doc = {"kind": "stage1 s-pool", "version": 1,
                "items": [{"id": uid(r), "prompt": r["prompt"], "response": r["response"], "source": r["source"],
                           "line": r["line"], "response_index": r["response_index"],
                           "companion_index": r["companion_index"]} for r in pool]}
    full = {POOL_FILE: canonical_json(pool_doc)}
    for name, ids in lists.items():
        full[LIST_FILES[name]] = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": name,
                                                 "items": [{"id": i, "prompt": by_id[i]["prompt"],
                                                            "response": by_id[i]["response"]} for i in ids]})
    s3_pool_ids = lists["s3_subset"] + [i for i in lists["s1"] if i not in set(lists["s3_subset"])]
    full[S3_POOL] = canonical_json({"kind": "stage1 text pool", "version": 1, "name": "s3_safe",
                                    "items": [{"id": i, "prompt": by_id[i]["prompt"], "response": by_id[i]["response"]}
                                              for i in s3_pool_ids]})

    def l8(rows: list[dict]) -> dict:
        return {field: sum(1 for r in rows if ids_by_row[uid(r)][field] == r["companion_index"])
                for field in ("safer_response_id", "better_response_id")}
    n = len(pool)
    items = [{**{k: v for k, v in item.items()}} for item in pool_doc["items"]]
    sealed = s1.sealed_record("stage1 s-pool, sealed record", full[POOL_FILE], items,
                              text_fields=("prompt", "response"),
                              keep_fields=("id", "source", "line", "response_index", "companion_index"))
    record = {
        "kind": "stage1 s-pool record", "version": 1, "requirement": settings["requirement"],
        "candidates": len(cands), "n_after_each_filter": result["n_after"], "filters": result["filters"],
        "filter_order": list(FILTERS), "pool_rows": n,
        "near_duplicate": {"max_jaccard": max_jaccard, "config_key": "injection.near_duplicate.max_jaccard",
                           "evaluation_forms": evaluation["forms"],
                           "forms_per_bank": {b: len(by_bank[b]) for b in BANK_NAMES},
                           "largest_kept_jaccard": result["largest_kept_jaccard"]},
        "report_only_l8": {"candidates": l8(cands), "s_pool": l8(pool),
                           "rule": "rows whose record's safer_response_id (better_response_id) names the other "
                                   "response; read by line from the hash-checked bytes after parse_pku"},
        "lists": {name: {"file": LIST_FILES[name], "sha256": sha256_bytes(full[LIST_FILES[name]]), "ids": ids}
                  for name, ids in lists.items()},
        "s3_pool": {"file": S3_POOL, "name": "s3_safe", "sha256": sha256_bytes(full[S3_POOL]), "items": len(s3_pool_ids),
                    "s1_rows_outside_the_subset": len(s3_pool_ids) - len(lists["s3_subset"])},
        "overlaps_l10": {"s1_and_s3_subset": len(set(lists["s1"]) & set(lists["s3_subset"])),
                         "expected_s1_and_s3_subset": len(lists["s1"]) * len(lists["s3_subset"]) / n,
                         "s1_and_s4_candidates": len(set(lists["s1"]) & set(lists["s4_candidates"]))},
        "room": room, "limits": limits,
        "full_files": {name: sha256_bytes(data) for name, data in sorted(full.items())},
        "s_pool_sealed": sealed,
        "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                    {"anch": pins["anch"]["sha256"], "data_config": config_sha,
                                     "prepared_manifest": evaluation["manifest_sha256"],
                                     "anchor_prompts": pins["anchor_prompts_sha256"], "rec_recipe": pins["rec_recipe_sha256"],
                                     **{f"source_{k}": v for k, v in sorted(sources["hashes"].items())},
                                     "lexicon_json": lexicon_pin.identity()["lexicon_json_sha256"]},
                                    settings["label_entries"])}
    record_bytes = canonical_json(record)
    texts = [t for r in pool for t in (r["prompt"], r["response"])]
    if s1._text_hits(record_bytes, texts):
        raise s1.Refusal("the record would hold text")
    return full, {RECORD: record_bytes}


def full_out_ok(path: Path) -> Path:
    path = path.resolve()
    if "tmp" not in path.parts:
        raise s1.Refusal("--full-out must lie in a folder named tmp: text is written only under tmp/")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True, help="the folder the config's local paths start from")
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True, help="the full anchor prompt list (with text)")
    parser.add_argument("--rec", type=Path, required=True, help="REC, the recipe")
    parser.add_argument("--full-out", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    folders = []
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        folders = check_output_folders(full_out_ok(args.full_out), args.out)
        full_out, out_dir = folders
        codec = real_codec(args.prepared, settings)
        full, record = build(config_path=args.config, sources_root=args.sources, prepared_root=args.prepared,
                             anchors_path=args.anchors, rec_path=args.rec, codec=codec, settings=settings,
                             settings_sha256=digest)
        written = s1.write_new_files(full_out, full)
        written.update(s1.write_new_files(out_dir, record))
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} ({refusal_state(folders)})",
              file=sys.stderr)
        return 2
    doc = s1.strict_json(record[RECORD])
    print(f"candidates {doc['candidates']}; N after each filter {doc['n_after_each_filter']}")
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


def real_codec(prepared_root: Path, settings: dict):
    """P's own tokenizer (offline cache), as the anchor token audit builds it."""
    from experiments.safety_selection.loaders import load_tokenizer
    from experiments.safety_selection.prepare import read_manifest
    from experiments.safety_selection.textproc import build_codec

    manifest, _ = read_manifest(prepared_root, settings["inputs"]["prepared_manifest_sha256"])
    tk = manifest["data_config"]["tokenizer"]
    tok, _ = load_tokenizer(tk["repo_id"], tk["revision"])
    return build_codec(tok, tk["end_of_turn_token"], [tk["end_of_turn_token"]], tk["end_of_turn_token"])


if __name__ == "__main__":
    sys.exit(main())
