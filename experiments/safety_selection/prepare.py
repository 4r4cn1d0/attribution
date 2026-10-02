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
composition) is never opened by engine or selector commands. Seed streams are named by
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
from .config import BANKS, PARTITIONS, ROLES, config_sha256, validate_data_config
from .sources import DataError, LeakageError, parse_arc, parse_date_lm, parse_toxicchat
from .textproc import (BoundaryMismatch, ControlTokenError, NoTargets, TooLong, arc_prompt_forms,
                       build_codec, encode_generation_prompt, encode_mc, encode_train, normalize,
                       render_arc_generation, render_arc_mc)

__all__ = ["MANIFEST", "MANIFEST_SHA", "TRAIN_ROWS", "QUERY_ROWS", "GROUPS", "BANK_FILES",
           "X0_STATIC", "AUDITOR", "RECEIPT", "HiddenAccessError", "RawInputs", "prepare",
           "write_prepared", "Prepared", "read_manifest", "read_verified", "load_prepared",
           "read_raw_inputs"]

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


def prepare(config: dict, raw: RawInputs, tokenizer: Any, tokenizer_identity: dict) -> dict[str, bytes]:
    """Every prepared file as bytes (relative path -> content), including the manifest.
    Pure and deterministic for one config, raw input and tokenizer."""
    validate_data_config(config)
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

    def prompt_key(row: dict) -> str:
        return f"{row['source']}:{row.get('record', row.get('line'))}"

    items: dict[str, list[dict]] = {bank: [] for bank in BANKS}
    prompt_source: dict[str, dict] = {}
    for bank in BANKS:
        for kind, row in bank_rows[bank]:
            pid = opaque_id("p", derive_seed(seed, "prompt-id", prompt_key(row)))
            if kind == "safety":
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
    _assert_disjoint(train_ok, ref_ok, items)

    eot = config["tokenizer"]["end_of_turn_token"]
    codec = build_codec(tokenizer, eot, [eot], eot)  # stop and pad ids are unused by the audit
    pairs = ([{"id": row_id[r["uid"]], "prompt": r["prompt"], "response": r["response"]} for r in train_ok]
             + [{"id": query_id[r["uid"]], "prompt": r["prompt"], "response": r["response"]} for r in ref_ok])
    token_info, token_summary = _token_audit(codec, config["tokenizer"], pairs,
                                             [i for bank in BANKS for i in items[bank]])

    files: dict[str, bytes] = {}
    train_out = sorted(({"row_id": row_id[r["uid"]], "prompt": r["prompt"], "response": r["response"],
                         **token_info[row_id[r["uid"]]]} for r in train_ok), key=lambda r: r["row_id"])
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

    files[AUDITOR] = canonical_json({
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
                problems.append(f"{key[:60]!r} in {seen[key]} and {where}")
            else:
                seen[key] = where

    for row in train:
        add([normalize(row["prompt"])], "train")
    for row in ref:
        add([normalize(row["prompt"])], "query")
    for bank in BANKS:
        for item in items[bank]:
            forms = [normalize(item["prompt"])]
            if item["kind"] != "safety":
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
