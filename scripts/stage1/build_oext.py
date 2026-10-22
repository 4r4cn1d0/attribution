"""The O-ext bank (lead decisions section 7; REQ-19 fired: O MDE 11.04 pp). Mac, CPU, $0; the lead runs it on the
real files (the PHTest file the lead downloaded and sealed, P with its hidden bank, REQ-6's S-pool, REQ-8's plant rows).
It prints counts and hashes only; it never downloads anything.

1. **Candidates:** the rows of PHTest.csv (SHA-256 pinned; read with the engine's parse_csv_table and the pinned
   header) whose Harmfulness is "harmless" (the settings pin the count, 2,077); the "controversial" rows are never used.
2. **Filters,** in the ruling's order, each on the previous filter's survivors, counted by reason, N after each:
   1. exact duplicates of a normalized prompt: overlap_with_an_existing_or_evaluation_prompt (P's training, query and
      evaluation forms, as ANCH's load_evaluation builds them, every bank and split), overlap_with_an_anchor_prompt,
      overlap_with_an_s_pool_prompt, overlap_with_a_plant_prompt;
   2. near duplicates (character 5-gram Jaccard >= P's max_jaccard, the engine's NEAR_DUPLICATE rule):
      near_duplicate_of_evaluation_prompt_<bank> (dev, selector, hidden), near_duplicate_of_an_anchor_prompt,
      near_duplicate_of_an_s_pool_prompt, near_duplicate_of_a_plant_prompt;
   3. empty_prompt;
   4. generation_prompt_<error>: encode_generation_prompt refuses under REC's max_prompt_tokens (1,536).
3. **Draw:** the sealed order of key oext.phtest (no parts) over all candidate IDs (sorted as strings); walking it, an
   eligible ID whose normalized prompt equals an earlier taken one is skipped (duplicate_within_phtest); the first 400
   taken form the bank. Fewer than 400: stop with counts only (section 7.3: the candidate count, N after each filter,
   the removals by reason and the skipped duplicates are in the stop message). Then, by LN-24 (addendum section 10), the
   lead runs it again with --accept-shortfall, and the bank is all N' eligible prompts (with the dev 100, 100 + N'),
   fixed and recorded before any stage-1 O answer is read; with N' = 0 it refuses (fallback F: the dev 100 only).
4. **Outputs:** the bank (text) under --full-out, inside a folder named tmp: oext_bank.json (ids and prompts in the
   sealed order); a text-free sealed record, oext_record.json, into --out (ids, each prompt's SHA-256, counts by reason,
   per-bank near-duplicate counts and the largest kept score, the input hashes). Both output folders must be absent or
   empty before anything is written.
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
from scripts.stage1 import build_s_pool as bsp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "build_oext.json"
SETTINGS_SHA256 = "fef3e92a657c832262ad798a43e700e2d13f92afaa381e0dcd9e0e04fc1843f8"
SETTINGS_NAME = "build_oext"
RECORD, BANK = "oext_record.json", "oext_bank.json"
STAGES = ("exact_overlap", "near_duplicate", "empty", "generation_prompt")


def read_phtest(path: Path, settings: dict) -> list[dict]:
    from experiments.safety_selection.sources import DataError, parse_csv_table

    spec = settings["phtest"]
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"PHTest cannot be read ({type(exc).__name__})") from None
    try:
        rows, _ = parse_csv_table(data, spec["sha256"], "phtest", spec["header"])
    except DataError as exc:
        raise s1.Refusal(f"the engine's CSV reader refuses PHTest ({type(exc).__name__})") from None
    ids = [r[spec["id_column"]] for r in rows]
    if len(set(ids)) != len(ids) or any(not s1.SAFE_VALUE.match(i) for i in ids):
        raise s1.Refusal("PHTest's IDs are not distinct short ids")
    harmless = [{"id": r[spec["id_column"]], "prompt": r[spec["prompt_column"]]} for r in rows
                if r[spec["label_column"]] == spec["candidate_label"]]
    if len(harmless) != spec["candidates"]:
        raise s1.Refusal(f"PHTest holds {len(harmless)} {spec['candidate_label']} rows, the settings say {spec['candidates']}")
    return harmless


def read_prompts(path: Path, digest: str, kind: str, what: str) -> list[str]:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != kind or not isinstance(doc.get("items"), list):
        raise s1.Refusal(f"{what} is not a {kind!r}")
    return [i["prompt"] for i in doc["items"]]


def run_filters(cands: list[dict], refs: dict[str, list[str]], existing: set[str], by_bank: dict, max_jaccard: float,
                codec, max_prompt_tokens: int) -> dict:
    from experiments.safety_selection.prepare import _NearDuplicates
    from experiments.safety_selection.textproc import encode_generation_prompt, normalize

    exact = {name: {normalize(p) for p in prompts} - {""} for name, prompts in refs.items()}
    near = {f"evaluation_prompt_{bank}": _NearDuplicates(forms) for bank, forms in by_bank.items()}
    near.update({name: _NearDuplicates([(f"{name}-{k}", p) for k, p in enumerate(prompts)])
                 for name, prompts in refs.items()})
    labels = {"anchor": "an_anchor_prompt", "s_pool": "an_s_pool_prompt", "plant": "a_plant_prompt"}
    scores: dict[str, dict] = {}
    rows, counts, n_after = list(cands), {}, {"candidates": len(cands)}
    for stage in STAGES:
        kept, reasons = [], Counter()
        for row in rows:
            prompt, key = row["prompt"], normalize(row["prompt"])
            why = []
            if stage == "exact_overlap":
                if key in existing:
                    why.append("overlap_with_an_existing_or_evaluation_prompt")
                why += [f"overlap_with_{labels[name]}" for name in refs if key in exact[name]]
            elif stage == "near_duplicate":
                scores[key] = {name: index.nearest(prompt)[0] for name, index in near.items()}
                why += [f"near_duplicate_of_{labels.get(name, name)}" for name, v in scores[key].items() if v >= max_jaccard]
            elif stage == "empty":
                if not prompt.strip():
                    why.append("empty_prompt")
            else:
                try:
                    encode_generation_prompt(codec, prompt, max_prompt_tokens)
                except ValueError as exc:
                    why.append(f"generation_prompt_{type(exc).__name__}")
            reasons.update(why)
            if not why:
                kept.append(row)
        counts[stage] = {"removed": len(rows) - len(kept), "by_reason": dict(sorted(reasons.items()))}
        n_after[stage] = len(kept)
        rows = kept
    largest = {name: max((scores[normalize(r["prompt"])][name] for r in rows), default=None) for name in near}
    return {"eligible": rows, "filters": counts, "n_after": n_after, "largest_kept_jaccard": largest}


def draw(cands: list[dict], eligible: list[dict], size: int, accept_shortfall: bool = False,
         result: dict | None = None) -> tuple[list[dict], int]:
    """The sealed walk; a stop (section 7.3) reports the filter counts (run_filters' result) and the skipped
    duplicates, counts only."""
    from experiments.safety_selection.textproc import normalize

    by_id = {r["id"]: r for r in eligible}
    taken, seen, skipped = [], set(), 0
    for rid in s1.sealed_order([r["id"] for r in cands], "oext.phtest"):
        if len(taken) == size:
            break
        row = by_id.get(rid)
        if row is None:
            continue
        key = normalize(row["prompt"])
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        taken.append(row)
    counts = f"candidates {len(cands)}; {bsp.filter_counts(result)}; duplicate_within_phtest_skipped {skipped}"
    if not taken:
        raise s1.Refusal(f"no eligible PHTest prompt: fallback F (the dev 100 only); no O-ext bank ({counts})")
    if len(taken) < size and not accept_shortfall:
        raise s1.Refusal(f"only {len(taken)} eligible PHTest prompts, fewer than {size}: stop with counts only "
                         f"({counts}) (LN-24: run again with --accept-shortfall to fix the bank as all {len(taken)})")
    return taken, skipped


def build(*, phtest_path: Path, prepared_root: Path, anchors_path: Path, s_pool: tuple[Path, str],
          plant: tuple[Path, str], rec_path: Path, codec, settings: dict, settings_sha256: str,
          accept_shortfall: bool = False) -> tuple[dict, dict]:
    from experiments.safety_selection.prepare import read_manifest

    s1.check_settings(settings, SETTINGS_NAME)
    pins = settings["inputs"]
    anch = bsp.load_anch(bsp.engine_root() / pins["anch"]["path"], pins["anch"]["sha256"])
    cands = read_phtest(phtest_path, settings)
    limits = bsp.recipe_limits(rec_path, pins["rec_recipe_sha256"])
    evaluation = bsp.anch_call(anch.load_evaluation, prepared_root, pins["prepared_manifest_sha256"])
    by_bank = bsp.evaluation_by_bank(prepared_root, pins["prepared_manifest_sha256"], anch)
    if [f for b in bsp.BANK_NAMES for f in by_bank[b]] != evaluation["evaluation"]:
        raise s1.Refusal("the per-bank evaluation forms differ from ANCH's evaluation list")
    if evaluation["forms"] != settings["expected_evaluation_forms"]:
        raise s1.Refusal(f"P has {evaluation['forms']} evaluation forms, the settings expect "
                         f"{settings['expected_evaluation_forms']}")
    manifest, _ = read_manifest(prepared_root, pins["prepared_manifest_sha256"])
    max_jaccard = manifest["data_config"]["eligibility"]["near_duplicate"]["max_jaccard"]
    if max_jaccard != settings["max_jaccard"]:
        raise s1.Refusal(f"P's max_jaccard is {max_jaccard}, the settings name {settings['max_jaccard']}")
    refs = {"anchor": bsp.anchor_prompts(anchors_path, pins["anchor_prompts_sha256"], anch),
            "s_pool": read_prompts(*s_pool, "stage1 s-pool", "the S-pool file"),
            "plant": read_prompts(*plant, "stage1 plant rows", "the plant rows file")}
    result = run_filters(cands, refs, evaluation["existing"], by_bank, max_jaccard, codec, limits["max_prompt_tokens"])
    bank, skipped = draw(cands, result["eligible"], settings["bank_size"], accept_shortfall, result)
    shortfall = None if len(bank) == settings["bank_size"] else {
        "eligible": len(bank), "planned": settings["bank_size"], "rule": settings["shortfall_rule"]}
    bank_bytes = canonical_json({"kind": "stage1 o-ext bank", "version": 1,
                                 "source": {k: settings["phtest"][k] for k in ("dataset", "commit", "sha256")},
                                 "items": [{"id": r["id"], "prompt": r["prompt"]} for r in bank]})
    sealed = s1.sealed_record("stage1 o-ext bank, sealed record", bank_bytes, bank, text_fields=("prompt",),
                              keep_fields=("id",))
    record = {"kind": "stage1 o-ext record", "version": 1, "requirement": settings["requirement"],
              "candidates": len(cands), "filter_order": list(STAGES), "n_after_each_filter": result["n_after"],
              "filters": result["filters"], "eligible": len(result["eligible"]),
              "duplicate_within_phtest_skipped": skipped, "bank_size": len(bank), "shortfall": shortfall,
              "near_duplicate": {"max_jaccard": max_jaccard, "evaluation_forms": evaluation["forms"],
                                 "largest_kept_jaccard": result["largest_kept_jaccard"]},
              "bank": sealed,
              "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                          {"phtest": settings["phtest"]["sha256"], "anch": pins["anch"]["sha256"],
                                           "prepared_manifest": pins["prepared_manifest_sha256"],
                                           "anchor_prompts": pins["anchor_prompts_sha256"], "s_pool": s_pool[1],
                                           "plant_rows": plant[1], "rec_recipe": pins["rec_recipe_sha256"]},
                                          settings["label_entries"])}
    record_bytes = canonical_json(record)
    if s1._text_hits(record_bytes, [r["prompt"] for r in cands]):
        raise s1.Refusal("the record would hold text")
    return {BANK: bank_bytes}, {RECORD: record_bytes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for flag in ("--phtest", "--prepared", "--anchors", "--rec", "--full-out", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--s-pool", required=True, help="PATH:SHA256 of REQ-6's s_pool.json")
    parser.add_argument("--plant", required=True, help="PATH:SHA256 of REQ-8's plant_rows.json")
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    parser.add_argument("--accept-shortfall", action="store_true",
                        help="LN-24: after a counts-only stop, fix the bank as all eligible prompts")
    args = parser.parse_args(argv)
    folders = []
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        pairs = []
        for spec in (args.s_pool, args.plant):
            p, _, h = spec.rpartition(":")
            if not p or not s1.HEX64.match(h):
                raise s1.Refusal("--s-pool and --plant are PATH:SHA256")
            pairs.append((Path(p), h))
        folders = bsp.check_output_folders(bsp.full_out_ok(args.full_out), args.out)
        full_out, out_dir = folders
        codec = bsp.real_codec(args.prepared, settings)
        full, record = build(phtest_path=args.phtest, prepared_root=args.prepared, anchors_path=args.anchors,
                             s_pool=pairs[0], plant=pairs[1], rec_path=args.rec, codec=codec, settings=settings,
                             settings_sha256=digest, accept_shortfall=args.accept_shortfall)
        written = s1.write_new_files(full_out, full)
        written.update(s1.write_new_files(out_dir, record))
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} ({bsp.refusal_state(folders)})",
              file=sys.stderr)
        return 2
    doc = s1.strict_json(record[RECORD])
    print(f"candidates {doc['candidates']}; N after each filter {doc['n_after_each_filter']}; bank {doc['bank_size']}")
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
