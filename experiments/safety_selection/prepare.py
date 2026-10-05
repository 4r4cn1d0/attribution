"""Deterministic preparation of the full-text corpus, removal groups and prompt banks
(stdlib only; a tokenizer object is passed in for the token audit).

Order of work, all before any outcome exists:

1. parse the pinned DATE-LM train/ref JSONL, ToxicChat 0124 test CSV and ARC-Easy
   validation/test JSONL (hash-checked, strict);
2. eligibility, using the minimal-safety rules for DATE-LM (empty/control-string rows;
   training rows sharing a normalized prompt or ``data_id`` with ANY reference row; first row
   per normalized prompt), then ToxicChat and ARC exclusion against ALL original DATE-LM
   prompts and source identifiers (an ARC item is compared by its bare question AND both
   rendered model inputs), de-duplication by source id and normalized prompt, and refusal
   unless every asserted eligible count matches the data config exactly;
3. removal groups: disjoint development/held-out member pools per hidden role (forced prior
   pilot removals go to development), slots filled in a seeded random construction order,
   opaque random group ids and seeded tie ranks independent of membership;
4. prompt banks: development, selector-facing and hidden-reference safety prompts from the
   toxicity-labelled ToxicChat pool; disjoint ARC generation/utility subsets (validation for
   development and selector, test for hidden);
5. a token audit with the pinned tokenizer: every training/query row, generation prompt and
   forced-choice prompt plus label must fit its limit (refused otherwise, never cut);
6. frozen outputs separated by audience (below), with a manifest of all hashes.

Audiences. ``engine/`` (opaque row ids, full text, groups) and ``banks/{dev,selector}.jsonl``
are what ordinary runs read. ``selector/x0_static.json`` holds the only static per-group
features (size, coarse provenance, character/token length summaries, tie rank). The hidden
reference bank lives in ``hidden/`` and is opened only by explicit reference jobs.
``auditor/construction.json`` (raw uids, ``data_id``, type labels, construction order and
composition) is never opened by engine or selector commands.

Headroom v2 (optional data-config sections, ``config.py``; without them nothing here changes):
the ``harm`` and ``overrefusal`` banks (``EVAL_BANK_RULE``) are split into the existing
development, selector and hidden files as items of those kinds, and harmful PKU-SafeRLHF rows are
injected into the training corpus (``INJECTION_RULE``) as ordinary editable rows outside every
group. Existing rows, ids, groups and items are computed exactly as without the sections. The
injected rows' source, categories and severity are written to the auditor file only. Seed streams are named by
composition roles, not raw type strings, so renaming hidden labels changes no engine- or
selector-facing byte. The manifest itself is ENGINE scope: its data config holds the design
seed and composition table, from which the seeded construction can be replayed to recover
each opaque group's composition; a selector receives only the whitelisted view of
``selector_view.py``, never ``Prepared`` or the manifest.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from typing import Any, Sequence

from .common import (canonical_json, derive_seed, ids_sha256, jsonl_bytes, opaque_id, sha256_bytes,
                     write_atomic)
from .config import BANKS, EVAL_BANK_KINDS, PARTITIONS, ROLES, config_sha256, validate_data_config
from .sources import (DataError, LeakageError, parse_arc, parse_csv_table, parse_date_lm, parse_pku,
                      parse_toxicchat)
from .textproc import (BoundaryMismatch, ControlTokenError, NoTargets, TooLong, arc_prompt_forms,
                       build_codec, encode_generation_prompt, encode_mc, encode_train, normalize,
                       render_arc_generation, render_arc_mc)

__all__ = ["MANIFEST", "MANIFEST_SHA", "TRAIN_ROWS", "QUERY_ROWS", "GROUPS", "BANK_FILES",
           "X0_STATIC", "AUDITOR", "RECEIPT", "HiddenAccessError", "RawInputs", "prepare",
           "write_prepared", "Prepared", "read_manifest", "read_verified", "load_prepared",
           "read_raw_inputs", "read_extra_sources", "INJECTION_RULE", "EVAL_BANK_RULE", "NEAR_DUPLICATE"]

MANIFEST = "manifest.json"
MANIFEST_SHA = "manifest.sha256"
RECEIPT = "prepare_receipt.json"  # environment and code identity; outside the manifest hash
TRAIN_ROWS = "engine/train_rows.jsonl"
QUERY_ROWS = "engine/query_rows.jsonl"
GROUPS = "engine/groups.json"
BANK_FILES = {"dev": "banks/dev.jsonl", "selector": "banks/selector.jsonl",
              "hidden": "hidden/hidden.jsonl"}
X0_STATIC = "selector/x0_static.json"
AUDITOR = "auditor/construction.json"
NORMALIZATION = "str.lower() then collapse all whitespace runs to one space (' '.join(s.split()))"
SEED_DERIVATION = ("int.from_bytes(sha256('|'.join(parts)).digest()[:8], 'big') seeding "
                   "random.Random; named by design seed and purpose (and role, partition)")
OVERLAP_FORMS = ("normalized prompts; an ARC item contributes its bare question and BOTH rendered "
                 "model inputs (generation and forced choice), whichever one it emits")
EVAL_BANK_RULE = (
    "EVAL_BANK_RULE v2: per bank (harm, then overrefusal), each source in the configured order and its records in file "
    "order: a record is a candidate if every 'keep' field has an allowed value; it is excluded if its "
    "prompt is empty, contains a forbidden substring, or its normalized prompt equals any original "
    "DATE-LM train or ref prompt, any ToxicChat prompt, or any form of any ARC item (bare question, "
    "generation and forced-choice renderings); then the first record per normalized prompt is kept "
    "across both banks (harm first); then a prompt over the token limit is excluded. A bank without "
    "'per_source' quotas: the eligible pool, sorted by (source order, record), is shuffled with "
    "random.Random(derive_seed(design_seed, 'eval-bank', bank)); the first 'dev' items are development, "
    "the next 'selector' items selector, and the rest hidden. A bank with 'per_source' quotas: each "
    "source's eligible records, in record order, are shuffled with random.Random(derive_seed(design_seed, "
    "'eval-bank', bank, source)); its first quota 'dev' items are development, the next quota "
    "'selector' items selector, and the rest hidden")
NEAR_DUPLICATE = (
    "character 5-gram Jaccard similarity (the sets of 5-character substrings of the normalized texts; a "
    "text shorter than 5 characters is its own single shingle) of at least injection.near_duplicate.max_jaccard "
    "with any evaluation prompt: every harm and over-refusal bank item (all splits), every ToxicChat bank "
    "item (all splits) and every form of every ARC bank item (bare question and both renderings)")
NEAR_DUPLICATE_REPORT_THRESHOLDS = (0.3, 0.5, 0.7)
INJECTION_RULE = (
    "candidates: every response of the injection sources (files in the configured order, records in "
    "line order, response 0 then 1) marked unsafe (is_response_i_safe false) with severity level >= "
    "min_severity; excluded: an empty prompt or response, a forbidden substring in either, or a "
    "normalized prompt equal to any original DATE-LM train or ref prompt, any ToxicChat prompt, any "
    "form of any ARC item, or any prompt of any eval-bank source file (every record, kept or not); "
    "then the first candidate per normalized prompt; its category is the first harm category marked "
    "true in the dataset's own key order; each category's candidates (in candidate order) are "
    "shuffled with random.Random(derive_seed(design_seed, 'injection-order', category)); the order "
    "takes one candidate per category per round, categories in the dataset's key order, skipping "
    "exhausted categories; walking that order, a candidate is skipped and counted if its row does not "
    "pass the token audit (at most max_train_tokens row tokens and max_prompt_tokens prompt tokens, no "
    "control token) or if its normalized prompt is a near duplicate of an evaluation prompt (NEAR_DUPLICATE); "
    "the first 'count' accepted candidates are injected. The order does not "
    "depend on 'count', so a smaller injection is a prefix of a larger one.")


class HiddenAccessError(PermissionError):
    """An ordinary job tried to open the hidden reference bank."""


@dataclass(frozen=True)
class RawInputs:
    date_train: bytes
    date_ref: bytes
    toxicchat_test: bytes
    arc_validation: bytes
    arc_test: bytes


def read_raw_inputs(paths: dict[str, str | Path]) -> RawInputs:
    return RawInputs(**{name: Path(paths[name]).read_bytes() for name in RawInputs.__annotations__})


def read_extra_sources(config: dict, root: str | Path) -> dict[str, bytes]:
    """The bytes of every ``extra_sources`` file, read from ``root`` / its ``local`` path."""
    return {name: (Path(root) / spec["local"]).read_bytes()
            for name, spec in config.get("extra_sources", {}).items()}


def _round_robin(by_category: dict[str, list], order: Sequence[str]) -> list:
    """One item per category per round, categories in ``order``, exhausted ones skipped."""
    queues = {c: list(by_category.get(c, [])) for c in order}
    out, depth = [], max((len(q) for q in queues.values()), default=0)
    for k in range(depth):
        out += [queues[c][k] for c in order if k < len(queues[c])]
    return out


def _forbidden_found(texts: Sequence[str], forbidden: Sequence[str]) -> bool:
    return any(s in text for text in texts for s in forbidden)


def _eval_banks(config: dict, extra: dict[str, bytes], other: set[str], codec, forbidden: Sequence[str]
                ) -> tuple[dict[str, list[tuple[str, dict]]], dict, dict, set[str]]:
    """(bank -> [(kind, row)], manifest summary, source receipts, normalized prompts of every
    record of every bank source) by ``EVAL_BANK_RULE``."""
    spec_all, seed = config["eval_banks"], config["design_seed"]
    max_prompt = config["tokenizer"]["max_prompt_tokens"]
    out: dict[str, list[tuple[str, dict]]] = {bank: [] for bank in BANKS}
    summary, receipts, every_prompt, kept_prompts = {}, {}, set(), set()
    for kind in EVAL_BANK_KINDS:
        spec = spec_all[kind]
        reasons, by_source, pool = Counter(), Counter(), []
        for order, name in enumerate(spec["sources"]):
            src = config["extra_sources"][name]
            rows, receipts[name] = parse_csv_table(extra[name], src["sha256"], name, src["header"])
            for row in rows:
                prompt = row[src["prompt_field"]]
                every_prompt.add(normalize(prompt))
                if any(row[field] not in allowed for field, allowed in src["keep"].items()):
                    reasons["not_kept_by_filter"] += 1
                    continue
                why = []
                if not prompt.strip():
                    why.append("empty_prompt")
                if _forbidden_found([prompt], forbidden):
                    why.append("control_string")
                if normalize(prompt) in other:
                    why.append("overlap_with_training_reference_toxicchat_or_arc")
                if why:
                    reasons.update(why)
                    continue
                if normalize(prompt) in kept_prompts:
                    reasons["duplicate_prompt"] += 1
                    continue
                kept_prompts.add(normalize(prompt))
                try:
                    encode_generation_prompt(codec, prompt, max_prompt)
                except (TooLong, ControlTokenError, BoundaryMismatch) as exc:
                    reasons[f"token_audit_{type(exc).__name__}"] += 1
                    continue
                by_source[name] += 1
                pool.append((order, row["record"], {
                    "source": name, "record": row["record"], "prompt": prompt,
                    "source_id": row[src["id_field"]] if src["id_field"] else None,
                    "category": row[src["category_field"]] if src["category_field"] else None}))
        _check_expected({"eligible": len(pool)}, {"eligible": spec["expected_eligible"]}, f"{kind} bank")
        quotas = spec.get("per_source")
        strata = ([(f"{kind}", [r for _, _, r in sorted(pool, key=lambda t: (t[0], t[1]))],
                    spec["dev"], spec["selector"])] if quotas is None else
                  [(name, [r for _, _, r in sorted(pool, key=lambda t: t[1]) if r["source"] == name],
                    quotas[name]["dev"], quotas[name]["selector"]) for name in spec["sources"]])
        parts = {bank: [] for bank in BANKS}
        for name, rows, n_dev, n_selector in strata:
            if n_dev + n_selector >= len(rows):
                raise DataError(f"the {kind} bank ({name}) needs more than {n_dev + n_selector} eligible "
                                f"prompts for a non-empty hidden part; have {len(rows)}")
            stream = derive_seed(seed, "eval-bank", kind) if quotas is None else derive_seed(seed, "eval-bank", kind, name)
            random.Random(stream).shuffle(rows)
            parts["dev"] += rows[:n_dev]
            parts["selector"] += rows[n_dev:n_dev + n_selector]
            parts["hidden"] += rows[n_dev + n_selector:]
        for bank in BANKS:
            out[bank] += [(kind, row) for row in parts[bank]]
        summary[kind] = {"eligible": len(pool), "eligible_by_source": dict(sorted(by_source.items())),
                         "excluded_by_reason": dict(sorted(reasons.items())),
                         "split": {bank: len(parts[bank]) for bank in BANKS},
                         "split_by_source": {bank: dict(sorted(Counter(r["source"] for r in parts[bank]).items()))
                                             for bank in BANKS}}
    return out, summary, receipts, every_prompt


def _shingles(text: str) -> frozenset[str]:
    """The character 5-grams of a normalized text (a shorter text is its own single shingle)."""
    return frozenset({text}) if len(text) < 5 else frozenset(text[i:i + 5] for i in range(len(text) - 4))


class _NearDuplicates:
    """Largest character 5-gram Jaccard similarity of a text with any of the evaluation texts
    (``NEAR_DUPLICATE``), via an inverted shingle index; returns the score and the matching id."""

    def __init__(self, texts: Sequence[tuple[str, str]]) -> None:
        self.ids, self.sizes, self.index = [], [], {}
        for key, text in texts:
            shingles = _shingles(normalize(text))
            self.ids.append(key)
            self.sizes.append(len(shingles))
            for shingle in shingles:
                self.index.setdefault(shingle, []).append(len(self.ids) - 1)

    def nearest(self, text: str) -> tuple[float, str | None]:
        shingles = _shingles(normalize(text))
        shared: Counter = Counter()
        for shingle in shingles:
            shared.update(self.index.get(shingle, ()))
        best, who = 0.0, None
        for k, inter in shared.items():
            value = inter / (len(shingles) + self.sizes[k] - inter)
            if value > best or (value == best and who is not None and self.ids[k] < who):
                best, who = value, self.ids[k]
        return best, who


def _injection(config: dict, extra: dict[str, bytes], forbidden_prompts: set[str], codec,
               forbidden: Sequence[str], evaluation: Sequence[tuple[str, str]]) -> tuple[list[dict], dict, dict, dict]:
    """(injected rows in injection order, manifest summary, source receipts, auditor near-duplicate
    report) by ``INJECTION_RULE``; ``evaluation`` is (prompt id, text) of every evaluation prompt form."""
    spec, seed = config["injection"], config["design_seed"]
    limits = config["tokenizer"]
    candidates, receipts, order_of_categories = [], {}, None
    for name in spec["sources"]:
        src = config["extra_sources"][name]
        rows, receipts[name] = parse_pku(extra[name], src["sha256"], name)
        if order_of_categories is None:
            order_of_categories = receipts[name]["category_order"]
        elif receipts[name]["category_order"] != order_of_categories:
            raise DataError(f"{name}: harm categories differ in name or order from the first source")
        candidates += [r for r in rows if not r["safe"] and r["severity"] >= spec["min_severity"]]
    reasons, kept = Counter(), []
    for row in candidates:
        why = []
        if not row["prompt"].strip():
            why.append("empty_prompt")
        if not row["response"].strip():
            why.append("empty_response")
        if _forbidden_found([row["prompt"], row["response"]], forbidden):
            why.append("control_string")
        if normalize(row["prompt"]) in forbidden_prompts:
            why.append("overlap_with_an_existing_or_evaluation_prompt")
        if not row["categories"]:
            why.append("no_harm_category")
        reasons.update(why)
        if not why:
            kept.append(row)
    kept, duplicates = _first_per_key(kept, lambda r: normalize(r["prompt"]), lambda r: r["categories"][0])
    _check_expected({"candidates": len(candidates), "eligible": len(kept)}, spec["expected"], "injection")
    by_category: dict[str, list[dict]] = {}
    for row in kept:
        by_category.setdefault(row["categories"][0], []).append(row)
    for category, rows in by_category.items():
        random.Random(derive_seed(seed, "injection-order", category)).shuffle(rows)
    order = _round_robin(by_category, order_of_categories)
    near, limit = _NearDuplicates(evaluation), spec["near_duplicate"]["max_jaccard"]
    chosen, skipped, walked = [], Counter(), []
    for row in order:
        if len(chosen) == spec["count"]:
            break
        score, match = near.nearest(row["prompt"])
        uid = f"{row['source']}:{row['line']:06d}:{row['response_index']}"
        walked.append({"uid": uid, "max_jaccard": score, "nearest_prompt_id": match})
        if score >= limit:
            skipped[f"NearDuplicate:{row['categories'][0]}"] += 1
            walked[-1]["skipped"] = "near_duplicate"
            continue
        try:
            example = encode_train(codec, "candidate", row["prompt"], row["response"], limits["max_train_tokens"])
            if example.n_prompt > limits["max_prompt_tokens"]:
                raise TooLong(f"prompt has {example.n_prompt} tokens")
        except (TooLong, ControlTokenError, NoTargets) as exc:
            skipped[f"{type(exc).__name__}:{row['categories'][0]}"] += 1
            walked[-1]["skipped"] = type(exc).__name__
            continue
        chosen.append(row)
    if len(chosen) != spec["count"]:
        raise DataError(f"injection needs {spec['count']} rows; only {len(chosen)} pass the token audit")
    realised = Counter(r["categories"][0] for r in chosen)
    summary = {"rule": INJECTION_RULE, "sources": list(spec["sources"]), "min_severity": spec["min_severity"],
               "percent": spec["percent"], "count": spec["count"], "candidates": len(candidates),
               "excluded_by_reason": dict(sorted(reasons.items())),
               "duplicate_prompt_dropped_by_category": duplicates, "eligible": len(kept),
               "eligible_by_category": {c: len(by_category.get(c, [])) for c in order_of_categories},
               "token_audit_skipped": dict(sorted(skipped.items())),
               "injected_by_category": {c: realised[c] for c in order_of_categories},
               "injected_by_severity": dict(sorted(Counter(str(r["severity"]) for r in chosen).items())),
               "category_order": order_of_categories,
               "near_duplicate": {"rule": NEAR_DUPLICATE, "max_jaccard": limit, "walked": len(walked),
                                  "skipped": sum(w.get("skipped") == "near_duplicate" for w in walked),
                                  "walked_at_or_above": {str(t): sum(w["max_jaccard"] >= t for w in walked)
                                                         for t in NEAR_DUPLICATE_REPORT_THRESHOLDS}}}
    report = {"rule": NEAR_DUPLICATE, "max_jaccard": limit, "walked": walked}
    return chosen, summary, receipts, report


def _date_eligibility(rows: list[dict], forbidden: Sequence[str], ref_prompts: set[str] | None,
                      ref_ids: set[str] | None) -> tuple[list[dict], dict]:
    """The minimal-safety rules: empty prompt/response, control strings and (for training
    rows) a normalized prompt or ``data_id`` shared with any reference row."""
    kept, reasons, excluded = [], Counter(), 0
    for row in rows:
        why = []
        if not row["prompt"].strip():
            why.append("empty_prompt")
        if not row["response"].strip():
            why.append("empty_response")
        if any(s in row["prompt"] or s in row["response"] for s in forbidden):
            why.append("control_string")
        if ref_prompts is not None and normalize(row["prompt"]) in ref_prompts:
            why.append("ref_prompt_overlap")
        if ref_ids is not None and row["data_id"] in ref_ids:
            why.append("ref_data_id_overlap")
        reasons.update(why)
        if why:
            excluded += 1
        else:
            kept.append(row)
    return kept, {"rows": excluded, "by_reason": dict(sorted(reasons.items()))}


def _first_per_key(rows: list[dict], key, label) -> tuple[list[dict], dict]:
    """Keep the first row (input order) per key; count the dropped rows by label."""
    seen: set = set()
    kept, dropped = [], Counter()
    for row in rows:
        k = key(row)
        if k in seen:
            dropped[label(row)] += 1
        else:
            seen.add(k)
            kept.append(row)
    return kept, dict(sorted(dropped.items()))


def _check_expected(actual: dict, expected: dict, what: str) -> None:
    wrong = {k: {"actual": actual.get(k), "expected": v} for k, v in expected.items()
             if v is not None and actual.get(k) != v}
    if wrong:
        raise DataError(f"{what}: eligible counts differ from the data config (refusing rather "
                        f"than resizing): {wrong}")


def _toxicchat_eligibility(rows: list[dict], forbidden: Sequence[str], date_prompts: set[str],
                           date_ids: set[str], min_chars: int) -> tuple[list[dict], dict]:
    blob = "\n".join(sorted(date_ids))
    kept, reasons, excluded = [], Counter(), 0
    for row in rows:
        why = []
        prompt, conv = row["prompt"], row["conv_id"]
        if not prompt.strip():
            why.append("empty_prompt")
        if any(s in prompt for s in forbidden):
            why.append("control_string")
        if normalize(prompt) in date_prompts:
            why.append("date_lm_prompt_overlap")
        if conv in date_ids or (len(conv) >= min_chars and conv in blob):
            why.append("date_lm_source_id_overlap")
        reasons.update(why)
        if why:
            excluded += 1
        else:
            kept.append(row)
    label = lambda r: f"toxicity_{r['toxicity']}"  # noqa: E731
    kept, by_id = _first_per_key(kept, lambda r: r["conv_id"].strip().lower(), label)
    kept, by_prompt = _first_per_key(kept, lambda r: normalize(r["prompt"]), label)
    return kept, {"excluded": {"rows": excluded, "by_reason": dict(sorted(reasons.items()))},
                  "duplicate_source_id_dropped": by_id, "duplicate_prompt_dropped": by_prompt}


def _arc_eligibility(rows: dict[str, list[dict]], forbidden: Sequence[str],
                     other_prompts: set[str]) -> tuple[dict[str, list[dict]], dict]:
    """Validation then test: control strings; overlap of the normalized bare question, or of
    either rendered model input (generation, forced choice), with any original DATE-LM or
    ToxicChat prompt; then first item per normalized id and per normalized question across
    both splits."""
    kept, reasons, excluded = [], Counter(), 0
    for split in ("validation", "test"):
        for row in rows[split]:
            why = []
            if any(s in text for text in (row["question"], *row["labels"], *row["texts"])
                   for s in forbidden):
                why.append("control_string")
            bare, generation, forced = arc_prompt_forms(row["question"], row["labels"], row["texts"])
            if bare in other_prompts:
                why.append("cross_source_prompt_overlap")
            if generation in other_prompts or forced in other_prompts:
                why.append("cross_source_rendered_overlap")
            reasons.update(why)
            if why:
                excluded += 1
            else:
                kept.append(row)
    kept, by_id = _first_per_key(kept, lambda r: r["arc_id"].strip().lower(), lambda r: r["source"])
    kept, by_question = _first_per_key(kept, lambda r: normalize(r["question"]), lambda r: r["source"])
    out = {split: [r for r in kept if r["source"] == f"arc-{split}"] for split in ("validation", "test")}
    return out, {"excluded": {"rows": excluded, "by_reason": dict(sorted(reasons.items()))},
                 "duplicate_source_id_dropped": by_id, "duplicate_question_dropped": by_question}


def _build_groups(config: dict, pools: dict[str, list[str]], role_of: dict[str, str]) -> dict:
    """Member pools, slot filling, opaque ids and tie ranks. ``pools`` are sorted uids."""
    seed, spec = config["design_seed"], config["groups"]
    composition = spec["composition"]
    need = {role: sum(row[1 + i] for row in composition) for i, role in enumerate(ROLES)}
    forced = sorted(set(spec["forced_dev_uids"]))
    forced_set = set(forced)
    missing = [u for u in forced if u not in role_of]
    if missing:
        raise DataError(f"forced development uids are not eligible training rows: {missing}")
    members: dict[str, dict[str, list[str]]] = {p: {} for p in PARTITIONS}
    unused: dict[str, list[str]] = {}
    for role in ROLES:
        forced_here = [u for u in forced if role_of[u] == role]
        if len(forced_here) > need[role]:
            raise DataError(f"{len(forced_here)} forced {role} rows exceed the {need[role]} "
                            f"development {role} slots")
        rest = [u for u in pools[role] if u not in forced_set]
        random.Random(derive_seed(seed, "member-pool", role)).shuffle(rest)
        extra = need[role] - len(forced_here)
        if extra + need[role] > len(rest):
            raise DataError(f"composition needs {need[role]} {role} rows per partition "
                            f"({2 * need[role]} total, {len(forced_here)} forced) but only "
                            f"{len(rest) + len(forced_here)} are eligible; refusing to shrink")
        members["dev"][role] = forced_here + rest[:extra]
        members["heldout"][role] = rest[extra:extra + need[role]]
        unused[role] = sorted(rest[extra + need[role]:])
    partitions = {}
    for part in PARTITIONS:
        order = list(range(len(composition)))
        random.Random(derive_seed(seed, "construction-order", part)).shuffle(order)
        fill = {role: list(members[part][role]) for role in ROLES}
        for role in ROLES:
            random.Random(derive_seed(seed, "slot-fill", part, role)).shuffle(fill[role])
        ids = random.Random(derive_seed(seed, "group-ids", part))
        built = []
        for index in order:
            taken = {role: [fill[role].pop() for _ in range(composition[index][1 + i])]
                     for i, role in enumerate(ROLES)}
            built.append({"group_id": opaque_id("g", ids.getrandbits(64)),
                          "construction_index": index, "composition": composition[index],
                          "members_by_role": {r: sorted(v) for r, v in taken.items()}})
        if any(fill[role] for role in ROLES):
            raise DataError("internal: partition members left after filling every slot")
        ranks = sorted(g["group_id"] for g in built)
        random.Random(derive_seed(seed, "tie-ranks", part)).shuffle(ranks)
        for g in built:
            g["tie_rank"] = ranks.index(g["group_id"])
        partitions[part] = built
    return {"partitions": partitions, "member_pools": members, "unused": unused, "forced": forced}


def _build_banks(config: dict, toxic: list[dict], arc: dict[str, list[dict]]) -> dict[str, list]:
    """(kind, source row) per bank, in allocation order; sizes are exact or refused."""
    seed, spec = config["design_seed"], config["banks"]
    out: dict[str, list] = {bank: [] for bank in BANKS}
    pool = sorted(toxic, key=lambda r: r["record"])
    random.Random(derive_seed(seed, "safety-banks")).shuffle(pool)
    need = sum(spec["safety"][bank] for bank in BANKS)
    if need > len(pool):
        raise DataError(f"safety banks need {need} eligible toxicity-labelled prompts, have {len(pool)}")
    start = 0
    for bank in BANKS:
        out[bank] += [("safety", row) for row in pool[start:start + spec["safety"][bank]]]
        start += spec["safety"][bank]
    for split in ("validation", "test"):
        items = sorted(arc[split], key=lambda r: r["line"])
        random.Random(derive_seed(seed, "arc-banks", split)).shuffle(items)
        start = 0
        for bank in BANKS:
            if spec["arc"][bank]["split"] != split:
                continue
            for kind in ("generation", "utility"):
                n = spec["arc"][bank][kind]
                if start + n > len(items):
                    raise DataError(f"ARC {split}: banks need more than {len(items)} eligible items")
                out[bank] += [(f"arc_{kind}", row) for row in items[start:start + n]]
                start += n
    return out


def _quantile(values: list[int], q: float) -> int:
    """Nearest-rank quantile."""
    ordered = sorted(values)
    return ordered[max(1, math.ceil(q * len(ordered))) - 1]


def _length_summary(values: list[int]) -> dict:
    return {"n": len(values), "max": max(values), "mean": fmean(values),
            "p50": _quantile(values, 0.5), "p90": _quantile(values, 0.9),
            "p99": _quantile(values, 0.99), "over_1024": sum(v > 1024 for v in values),
            "over_2048": sum(v > 2048 for v in values)}


def _summary(values: list[int]) -> dict:
    return {"sum": sum(values), "mean": fmean(values), "min": min(values), "max": max(values)}


def _token_audit(codec, limits: dict, pairs: list[dict], items: list[dict]) -> tuple[dict, dict]:
    """Per-id token facts and a summary. Raises DataError listing every refused sequence."""
    max_train, max_prompt = limits["max_train_tokens"], limits["max_prompt_tokens"]
    info, problems, mismatched, leading = {}, [], [], 0
    for row in pairs:
        try:
            ex = encode_train(codec, row["id"], row["prompt"], row["response"], max_train)
        except (TooLong, ControlTokenError, NoTargets) as exc:
            problems.append(f"{row['id']}: {type(exc).__name__}: {exc}")
            continue
        info[row["id"]] = {"prompt_tokens": ex.n_prompt, "target_tokens": ex.n_target,
                           "token_sha256": ids_sha256(ex.input_ids)}
        if codec.conversation_ids(row["prompt"], row["response"])[:len(ex.input_ids)] != list(ex.input_ids):
            mismatched.append(row["id"])
        leading += row["response"][:1].isspace()
    for item in items:
        try:
            if item["kind"] == "arc_utility":
                prompt, targets = encode_mc(codec, item["question"], item["labels"], item["texts"],
                                            max_prompt)
                info[item["prompt_id"]] = {"prompt_tokens": len(prompt),
                                           "label_tokens": [len(t) for t in targets],
                                           "token_sha256": ids_sha256(prompt)}
            else:
                ids = encode_generation_prompt(codec, item["prompt"], max_prompt)
                info[item["prompt_id"]] = {"prompt_tokens": len(ids), "token_sha256": ids_sha256(ids)}
        except (TooLong, ControlTokenError, BoundaryMismatch) as exc:
            problems.append(f"{item['prompt_id']}: {type(exc).__name__}: {exc}")
    if problems:
        raise DataError(f"token audit refused {len(problems)} sequence(s); nothing is truncated: "
                        + "; ".join(problems[:10]))
    totals = [info[r["id"]]["prompt_tokens"] + info[r["id"]]["target_tokens"] for r in pairs]
    summary = {"pairs": _length_summary(totals),
               "separate_vs_joint_encoding_mismatches": len(mismatched),
               "mismatched_ids": sorted(mismatched)[:50],
               "responses_with_leading_whitespace": leading,
               "generation_prompt_max_tokens": max((info[i["prompt_id"]]["prompt_tokens"] for i in items),
                                                   default=0)}
    return info, summary


def prepare(config: dict, raw: RawInputs, tokenizer: Any, tokenizer_identity: dict,
            extra: dict[str, bytes] | None = None) -> dict[str, bytes]:
    """Every prepared file as bytes (relative path -> content), including the manifest.
    Pure and deterministic for one config, raw input (and ``extra`` source bytes by name, which
    the headroom-v2 sections need) and tokenizer."""
    validate_data_config(config)
    v3 = "injection" in config
    if v3 and set(extra or {}) != set(config["extra_sources"]):
        raise DataError(f"the extra sources {sorted(config['extra_sources'])} are needed, "
                        f"got {sorted(extra or {})}")
    if not v3 and extra:
        raise DataError("extra source bytes were given but the data config names no extra source")
    src, elig = config["sources"], config["eligibility"]
    forbidden = elig["forbidden_substrings"]
    seed, roles = config["design_seed"], config["roles"]
    role_of_type = {roles[r]: r for r in ROLES}

    train, train_blank = parse_date_lm(raw.date_train, src["date_lm"]["train_sha256"], "train",
                                       set(role_of_type))
    ref, ref_blank = parse_date_lm(raw.date_ref, src["date_lm"]["ref_sha256"], "ref", set(role_of_type))
    ref_prompts = {normalize(r["prompt"]) for r in ref} - {""}
    ref_ids = {r["data_id"] for r in ref}
    train_ok, train_excluded = _date_eligibility(train, forbidden, ref_prompts, ref_ids)
    train_ok, train_dupes = _first_per_key(train_ok, lambda r: normalize(r["prompt"]),
                                           lambda r: role_of_type[r["type"]])
    ref_ok, ref_excluded = _date_eligibility(ref, forbidden, None, None)
    ref_ok, ref_dupes = _first_per_key(ref_ok, lambda r: normalize(r["prompt"]),
                                       lambda r: role_of_type[r["type"]])
    by_role = Counter(role_of_type[r["type"]] for r in train_ok)
    _check_expected({r: by_role[r] for r in ROLES}, elig["expected"]["train"], "DATE-LM train")
    _check_expected({"ref": len(ref_ok)}, {"ref": elig["expected"]["ref"]}, "DATE-LM ref")

    tc_rows, tc_receipt = parse_toxicchat(raw.toxicchat_test, src["toxicchat"]["sha256"],
                                          src["toxicchat"]["header"])
    date_prompts = {normalize(r["prompt"]) for r in train + ref} - {""}
    date_ids = {r["data_id"] for r in train + ref}
    tc_ok, tc_summary = _toxicchat_eligibility(tc_rows, forbidden, date_prompts, date_ids,
                                               elig["min_source_id_substring_chars"])
    tc_counts = {"toxic": sum(r["toxicity"] == 1 for r in tc_ok),
                 "nontoxic": sum(r["toxicity"] == 0 for r in tc_ok)}
    _check_expected(tc_counts, elig["expected"]["toxicchat"], "ToxicChat test")

    arc_raw, arc_blank = {}, {}
    for split, data in (("validation", raw.arc_validation), ("test", raw.arc_test)):
        arc_raw[split], arc_blank[split] = parse_arc(data, src["arc_easy"][f"{split}_jsonl_sha256"], split)
    other_prompts = date_prompts | ({normalize(r["prompt"]) for r in tc_rows} - {""})
    arc_ok, arc_summary = _arc_eligibility(arc_raw, forbidden, other_prompts)
    arc_counts = {split: len(arc_ok[split]) for split in ("validation", "test")}
    _check_expected(arc_counts, elig["expected"]["arc"], "ARC-Easy")

    # Opaque ids: pseudo-random per source position, carrying no type, order or data_id.
    row_id = {r["uid"]: opaque_id("r", derive_seed(seed, "row-id", r["uid"])) for r in train_ok}
    query_id = {r["uid"]: opaque_id("q", derive_seed(seed, "query-id", r["uid"])) for r in ref_ok}
    role_of = {r["uid"]: role_of_type[r["type"]] for r in train_ok}
    pools = {role: sorted(u for u in role_of if role_of[u] == role) for role in ROLES}
    grouping = _build_groups(config, pools, role_of)
    bank_rows = _build_banks(config, [r for r in tc_ok if r["toxicity"] == 1], arc_ok)
    eot = config["tokenizer"]["end_of_turn_token"]
    codec = build_codec(tokenizer, eot, [eot], eot)  # stop and pad ids are unused by the audit
    injected: list[dict] = []
    if v3:
        arc_forms = {form for split in ("validation", "test") for r in arc_raw[split]
                     for form in arc_prompt_forms(r["question"], r["labels"], r["texts"])}
        other = date_prompts | ({normalize(r["prompt"]) for r in tc_rows} - {""}) | arc_forms
        new_banks, bank_summary, bank_receipts, bank_source_prompts = _eval_banks(config, extra, other, codec,
                                                                                  forbidden)
        for bank in BANKS:
            bank_rows[bank] += new_banks[bank]
        evaluation = []
        for bank in BANKS:
            for kind, row in bank_rows[bank]:
                pid = opaque_id("p", derive_seed(seed, "prompt-id", f"{row['source']}:{row.get('record', row.get('line'))}"))
                if kind.startswith("arc_"):
                    evaluation += [(pid, form) for form in dict.fromkeys(
                        arc_prompt_forms(row["question"], row["labels"], row["texts"]))]
                else:
                    evaluation.append((pid, row["prompt"]))
        injected, injection_summary, injection_receipts, near_report = _injection(
            config, extra, other | bank_source_prompts, codec, forbidden, evaluation)
        for position, row in enumerate(injected):
            row["uid"] = f"{row['source']}:{row['line']:06d}:{row['response_index']}"
            row["position"] = position
            row_id[row["uid"]] = opaque_id("r", derive_seed(seed, "row-id", row["uid"]))

    def prompt_key(row: dict) -> str:
        return f"{row['source']}:{row.get('record', row.get('line'))}"

    def eval_item(bank: str, kind: str, row: dict, pid: str) -> dict:
        prompt_source[pid] = {"bank": bank, "kind": kind, "source": row["source"], "record": row["record"],
                              "source_id": row["source_id"], "category": row["category"]}
        return {"prompt_id": pid, "kind": kind, "prompt": row["prompt"]}

    items: dict[str, list[dict]] = {bank: [] for bank in BANKS}
    prompt_source: dict[str, dict] = {}
    for bank in BANKS:
        for kind, row in bank_rows[bank]:
            pid = opaque_id("p", derive_seed(seed, "prompt-id", prompt_key(row)))
            if kind in EVAL_BANK_KINDS:
                item = eval_item(bank, kind, row, pid)
            elif kind == "safety":
                item = {"prompt_id": pid, "kind": kind, "prompt": row["prompt"]}
                prompt_source[pid] = {"bank": bank, "kind": kind, "source": "toxicchat",
                                      "record": row["record"], "conv_id": row["conv_id"],
                                      "toxicity": row["toxicity"], "jailbreaking": row["jailbreaking"]}
            else:
                item = {"prompt_id": pid, "kind": kind, "question": row["question"],
                        "labels": row["labels"], "texts": row["texts"]}
                if kind == "arc_utility":
                    item["answer"] = row["answer"]
                    item["prompt"] = render_arc_mc(row["question"], row["labels"], row["texts"])
                else:
                    item["prompt"] = render_arc_generation(row["question"], row["labels"], row["texts"])
                prompt_source[pid] = {"bank": bank, "kind": kind, "source": row["source"],
                                      "line": row["line"], "arc_id": row["arc_id"]}
            items[bank].append(item)

    all_ids = list(row_id.values()) + list(query_id.values()) + list(prompt_source) + [
        g["group_id"] for part in PARTITIONS for g in grouping["partitions"][part]]
    if len(set(all_ids)) != len(all_ids):
        raise DataError("internal: opaque identifier collision")
    _assert_disjoint(train_ok + injected, ref_ok, items)

    pairs = ([{"id": row_id[r["uid"]], "prompt": r["prompt"], "response": r["response"]} for r in train_ok]
             + [{"id": row_id[r["uid"]], "prompt": r["prompt"], "response": r["response"]} for r in injected]
             + [{"id": query_id[r["uid"]], "prompt": r["prompt"], "response": r["response"]} for r in ref_ok])
    token_info, token_summary = _token_audit(codec, config["tokenizer"], pairs,
                                             [i for bank in BANKS for i in items[bank]])

    files: dict[str, bytes] = {}
    train_out = sorted(({"row_id": row_id[r["uid"]], "prompt": r["prompt"], "response": r["response"],
                         **token_info[row_id[r["uid"]]]} for r in train_ok + injected), key=lambda r: r["row_id"])
    files[TRAIN_ROWS] = jsonl_bytes(train_out)
    query_out = sorted(({"query_id": query_id[r["uid"]], "prompt": r["prompt"], "response": r["response"],
                         **token_info[query_id[r["uid"]]]} for r in ref_ok), key=lambda r: r["query_id"])
    files[QUERY_ROWS] = jsonl_bytes(query_out)
    for bank in BANKS:
        files[BANK_FILES[bank]] = jsonl_bytes(sorted(({**i, **token_info[i["prompt_id"]]} for i in items[bank]),
                                                     key=lambda i: i["prompt_id"]))

    rows_by_uid = {r["uid"]: r for r in train_ok}
    provenance_labels = sorted(set(config["provenance"].values()))
    groups_out, x0_out, auditor_groups = {}, {}, {}
    for part in PARTITIONS:
        built = sorted(grouping["partitions"][part], key=lambda g: g["group_id"])
        groups_out[part] = {"groups": [], "menu": ["a0"] + [g["group_id"] for g in built]}
        x0_out[part] = []
        for g in built:
            uids = sorted(u for role in ROLES for u in g["members_by_role"][role])
            members = sorted(row_id[u] for u in uids)
            groups_out[part]["groups"].append({"group_id": g["group_id"], "size": len(members),
                                               "members": members})
            prov = Counter(config["provenance"][role_of[u]] for u in uids)
            info = [token_info[row_id[u]] for u in uids]
            x0_out[part].append({
                "group_id": g["group_id"], "size": len(members), "tie_rank": g["tie_rank"],
                "provenance": {label: prov[label] for label in provenance_labels},
                "chars": _summary([len(rows_by_uid[u]["prompt"]) + len(rows_by_uid[u]["response"])
                                   for u in uids]),
                "response_chars": _summary([len(rows_by_uid[u]["response"]) for u in uids]),
                "tokens": _summary([i["prompt_tokens"] + i["target_tokens"] for i in info]),
                "target_tokens": _summary([i["target_tokens"] for i in info])})
            counts = g["composition"][1:]
            auditor_groups[g["group_id"]] = {
                "partition": part, "construction_index": g["construction_index"],
                "composition": dict(zip(["size", *ROLES], g["composition"])),
                "family": "+".join(r for r, n in zip(ROLES[:2], counts[:2]) if n) or "benign-only",
                "tie_rank": g["tie_rank"],
                "members": {role: sorted(row_id[u] for u in g["members_by_role"][role]) for role in ROLES}}
    files[GROUPS] = canonical_json({"partitions": groups_out})
    files[X0_STATIC] = canonical_json({
        "kind": "selector-facing static group features (no hidden labels)",
        "schema": {"size": "rows removed", "tie_rank": "seeded rank independent of membership",
                   "provenance": "coarse source counts", "chars": "prompt+response characters",
                   "response_chars": "response characters", "tokens": "prompt+target tokens",
                   "target_tokens": "response+end-of-turn tokens"},
        "partitions": x0_out})

    auditor_v3 = {} if not v3 else {"injected": {
        row_id[r["uid"]]: {"uid": r["uid"], "source": r["source"], "line": r["line"],
                           "response_index": r["response_index"], "position": r["position"],
                           "category": r["categories"][0], "categories": r["categories"],
                           "severity": r["severity"]} for r in injected},
        "injection_near_duplicates": near_report}
    files[AUDITOR] = canonical_json({
        **auditor_v3,
        "kind": "AUDITOR ONLY: hidden construction labels; never read by engine or selector commands",
        "rows": {row_id[u]: {"uid": u, "data_id": r["data_id"], "type": r["type"], "role": role_of[u],
                             "line": r["line"]} for u, r in sorted(rows_by_uid.items())},
        "queries": {query_id[r["uid"]]: {"uid": r["uid"], "data_id": r["data_id"], "type": r["type"]}
                    for r in ref_ok},
        "groups": auditor_groups,
        "member_pools": {part: {role: sorted(row_id[u] for u in grouping["member_pools"][part][role])
                                for role in ROLES} for part in PARTITIONS},
        "unused_by_role": {role: [row_id[u] for u in grouping["unused"][role]] for role in ROLES},
        "forced_dev": {u: row_id[u] for u in grouping["forced"]},
        "prompts": prompt_source})

    manifest = {
        "kind": "safety-selection prepared manifest",
        "data_config": config,
        "data_config_sha256": config_sha256(config),
        "normalization": NORMALIZATION,
        "overlap_forms": OVERLAP_FORMS,
        "seed_derivation": SEED_DERIVATION,
        "sources": {
            "date_lm": {"train": {"sha256": src["date_lm"]["train_sha256"], "rows": len(train),
                                  "blank_lines": train_blank},
                        "ref": {"sha256": src["date_lm"]["ref_sha256"], "rows": len(ref),
                                "blank_lines": ref_blank}},
            "toxicchat": {"sha256": src["toxicchat"]["sha256"], **tc_receipt},
            "arc_easy": {split: {"sha256": src["arc_easy"][f"{split}_jsonl_sha256"],
                                 "rows": len(arc_raw[split]), "blank_lines": arc_blank[split]}
                         for split in ("validation", "test")}},
        "eligibility": {
            "date_lm": {"train_excluded": train_excluded, "ref_excluded": ref_excluded,
                        "train_prompt_duplicates_dropped": train_dupes,
                        "ref_prompt_duplicates_dropped": ref_dupes,
                        "eligible_train_by_role": {r: by_role[r] for r in ROLES},
                        "eligible_ref": len(ref_ok)},
            "toxicchat": {**tc_summary, "eligible": tc_counts},
            "arc_easy": {**arc_summary, "eligible": arc_counts},
            "expected_counts": "matched"},
        "corpus": {"rows": len(train_out), "queries": len(query_out)},
        "groups": {part: {"groups": len(groups_out[part]["groups"]),
                          "members": sum(g["size"] for g in groups_out[part]["groups"]),
                          "menu_options": len(groups_out[part]["menu"])} for part in PARTITIONS},
        "unused_member_rows_by_role": {role: len(grouping["unused"][role]) for role in ROLES},
        "banks": {bank: dict(sorted(Counter(i["kind"] for i in items[bank]).items())) for bank in BANKS},
        "seed_namespaces": config["seed_namespaces"],
        "tokenizer": tokenizer_identity,
        "token_audit": token_summary,
        "scopes": {"engine": [TRAIN_ROWS, QUERY_ROWS, GROUPS, BANK_FILES["dev"], BANK_FILES["selector"]],
                   "selector": [X0_STATIC], "reference": [BANK_FILES["hidden"]], "auditor": [AUDITOR]},
        "files": {name: sha256_bytes(data) for name, data in sorted(files.items())},
    }
    if v3:
        manifest["corpus"]["injected_rows"] = len(injected)
        manifest["headroom_v2"] = {
            "extra_sources": {name: {"sha256": spec["sha256"], "license": spec["license"],
                                     **{**bank_receipts, **injection_receipts}[name]}
                              for name, spec in sorted(config["extra_sources"].items())},
            "eval_banks": {"rule": EVAL_BANK_RULE, **bank_summary},
            "injection": injection_summary}
    manifest_bytes = canonical_json(manifest)
    files[MANIFEST] = manifest_bytes
    files[MANIFEST_SHA] = (sha256_bytes(manifest_bytes) + "\n").encode("ascii")
    return files


def _assert_disjoint(train: list[dict], ref: list[dict], items: dict[str, list[dict]]) -> None:
    """No emitted model input repeats across roles or items (normalized): training and query
    prompts, safety prompts, and for every ARC item its bare question AND both renderings
    (generation and forced choice) besides the prompt it actually emits. One item's own forms
    never collide with each other; any form shared by two rows or items is leakage."""
    seen: dict[str, str] = {}
    problems = []

    def add(texts: Sequence[str], where: str) -> None:
        for key in dict.fromkeys(texts):  # distinct forms of one row or item
            if key in seen:
                problems.append(f"{seen[key]} and {where} share a normalized prompt")
            else:
                seen[key] = where

    for i, row in enumerate(train):
        add([normalize(row["prompt"])], f"train/{row.get('uid', i)}")
    for i, row in enumerate(ref):
        add([normalize(row["prompt"])], f"query/{row.get('uid', i)}")
    for bank in BANKS:
        for item in items[bank]:
            forms = [normalize(item["prompt"])]
            if item["kind"] in ("arc_generation", "arc_utility"):
                forms += arc_prompt_forms(item["question"], item["labels"], item["texts"])
            add(forms, f"{bank}/{item['kind']}/{item['prompt_id']}")
    if problems:
        raise LeakageError(f"{len(problems)} prompt leakage problem(s): " + "; ".join(problems[:10]))


def write_prepared(out_dir: str | Path, files: dict[str, bytes], receipt: dict) -> str:
    """Write every file; refuse to replace different existing content (prepared data are
    frozen). The receipt is written only alongside a new manifest. Returns the manifest hash."""
    out = Path(out_dir)
    for name, data in files.items():
        path = out / name
        if path.exists() and path.read_bytes() != data:
            raise DataError(f"{path} exists with different content; prepared data are frozen")
    fresh = not (out / MANIFEST).exists()
    for name, data in sorted(files.items()):
        if name != MANIFEST and name != MANIFEST_SHA:
            write_atomic(out / name, data)
    write_atomic(out / MANIFEST, files[MANIFEST])
    write_atomic(out / MANIFEST_SHA, files[MANIFEST_SHA])
    if fresh:
        write_atomic(out / RECEIPT, canonical_json(receipt))
    return files[MANIFEST_SHA].decode("ascii").strip()


def read_manifest(root: str | Path, expected_sha256: str | None = None) -> tuple[dict, str]:
    root = Path(root)
    data = (root / MANIFEST).read_bytes()
    digest = sha256_bytes(data)
    recorded = (root / MANIFEST_SHA).read_text(encoding="ascii").strip()
    if digest != recorded:
        raise DataError(f"manifest sha256 {digest} differs from its frozen hash {recorded}")
    if expected_sha256 is not None and digest != expected_sha256:
        raise DataError(f"manifest sha256 {digest} differs from the pinned {expected_sha256}")
    return json.loads(data), digest


def read_verified(root: str | Path, manifest: dict, name: str) -> bytes:
    """The bytes of one prepared file after its manifest hash verifies."""
    data = (Path(root) / name).read_bytes()
    if sha256_bytes(data) != manifest["files"][name]:
        raise DataError(f"{name} differs from the manifest hash")
    return data


_verified = read_verified


def _jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode("utf-8").split("\n") if line]


@dataclass
class Prepared:
    root: Path
    manifest: dict
    manifest_sha256: str
    train_rows: dict[str, dict]
    query_rows: list[dict]
    groups: dict[str, dict[str, list[str]]]
    menus: dict[str, list[str]]
    banks: dict[str, list[dict]]

    @property
    def data_config(self) -> dict:
        return self.manifest["data_config"]

    @property
    def corpus(self) -> list[str]:
        return sorted(self.train_rows)

    def removed_rows(self, split: str, arm: str) -> list[str]:
        if arm == "a0":
            return []
        if arm not in self.groups[split]:
            raise DataError(f"{arm} is not a {split} group")
        return list(self.groups[split][arm])

    def group_of(self, group_id: str) -> str:
        for split in PARTITIONS:
            if group_id in self.groups[split]:
                return split
        raise DataError(f"unknown group {group_id}")


def load_prepared(root: str | Path, expected_sha256: str | None = None,
                  banks: Sequence[str] = (), allow_hidden: bool = False) -> Prepared:
    """Verified engine view: manifest, training/query rows, groups and the requested banks.
    The hidden bank is refused before anything is read unless ``allow_hidden``; the auditor
    file is never read here."""
    for bank in banks:
        if bank not in BANKS:
            raise DataError(f"unknown bank {bank!r}")
        if bank == "hidden" and not allow_hidden:
            raise HiddenAccessError("the hidden reference bank needs an explicit reference job")
    root = Path(root)
    manifest, digest = read_manifest(root, expected_sha256)
    train = _jsonl(_verified(root, manifest, TRAIN_ROWS))
    queries = _jsonl(_verified(root, manifest, QUERY_ROWS))
    groups_raw = json.loads(_verified(root, manifest, GROUPS))["partitions"]
    groups = {part: {g["group_id"]: g["members"] for g in groups_raw[part]["groups"]}
              for part in PARTITIONS}
    menus = {part: groups_raw[part]["menu"] for part in PARTITIONS}
    rows = {r["row_id"]: r for r in train}
    if len(rows) != len(train) or len(rows) != manifest["corpus"]["rows"]:
        raise DataError("training rows file disagrees with the manifest")
    for part in PARTITIONS:
        for gid, members in groups[part].items():
            if not set(members) <= set(rows):
                raise DataError(f"group {gid} names rows outside the corpus")
    loaded = {bank: _jsonl(_verified(root, manifest, BANK_FILES[bank])) for bank in banks}
    return Prepared(root, manifest, digest, rows, queries, groups, menus, loaded)
