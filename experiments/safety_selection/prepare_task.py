"""Deterministic preparation of the kill test's task data (stdlib only; a tokenizer object is
passed in for the token audit): one Dolly-format source becomes a corpus of equal-size category
units, a set of task rows per category and the imported evaluation banks.

The rule (``TASK_RULE``, recorded in the manifest):

1. render each record's user text (``render_user_text``): the instruction, then a blank line and
   the context when the context is not blank; the response as it is. Nothing is cleaned (citation
   brackets stay);
2. exclude, counted by category and by the FIRST reason in this order (so the counts add up): an empty instruction or response; a forbidden
   substring in any field; a normalized user text equal to an evaluation prompt or ARC form (all
   splits); a near duplicate of an evaluation prompt (``prepare.NEAR_DUPLICATE`` at the config's
   ``max_jaccard``, all splits and kinds), tested on the instruction alone AND on the rendered user
   text, because a long context dilutes the score; then the first row per normalized user text, in
   file order; then the token audit (row at most ``max_train_tokens``, prompt at most
   ``max_prompt_tokens``, no control token);
3. per category, the eligible rows in file order are shuffled with
   ``random.Random(derive_seed(design_seed, 'kt-units', category))``: the first
   ``task_rows_per_category`` are task rows, the next n form the category's unit, the rest are unused
   (their lines are in the auditor file);
4. n is ``rows_per_unit``, unless a category has fewer than ``task_rows_per_category +
   rows_per_unit`` eligible rows: then n = floor((smallest eligible - task rows) / step) * step for
   every unit (``round_down_to`` = step). The realised n is recorded and, when asserted, checked;
5. the corpus is the units; each unit is a development group (opaque id); the held-out partition is
   empty; the query rows are the task rows;
6. the three bank files are copied byte for byte from a prepared-v3 folder after its manifest and
   file hashes verify, and every imported item is re-audited with this tokenizer (a different
   ``token_sha256`` refuses).

Audiences, sealing and determinism are as in ``prepare.py``: the hidden bank file is opened here
only (for the overlap check), messages carry ids and counts only, and the output is a pure
function of the config, the Dolly bytes, the bank-source bytes and the tokenizer.
"""

from __future__ import annotations

import bisect
import json
import random
from collections import Counter
from typing import Any, Sequence

from .common import canonical_json, derive_seed, ids_sha256, jsonl_bytes, opaque_id, sha256_bytes
from .config import TASK_BANK_FILES, config_sha256, validate_task_data_config
from .prepare import (AUDITOR, BANK_FILES, GROUPS, MANIFEST, MANIFEST_SHA, NEAR_DUPLICATE, NORMALIZATION,
                      QUERY_ROWS, SEED_DERIVATION, TRAIN_ROWS, X0_STATIC, _assert_disjoint, _check_expected, _jsonl,
                      _shingles, _summary, _token_audit)
from .sources import DataError, parse_dolly
from .textproc import (BoundaryMismatch, ControlTokenError, NoTargets, TooLong, arc_prompt_forms, build_codec,
                       encode_generation_prompt, encode_mc, encode_train, normalize)

__all__ = ["TASK_RULE", "TASK_QUERY_LOSS_DEFINITION", "REPORT_THRESHOLDS", "render_user_text", "NearIndex",
           "prepare_task", "unit_size"]

TASK_RULE = (
    "kt-task-rule v1: user text = the instruction, then a blank line and the context when the context is "
    "not blank (str.strip() non-empty); the response unchanged; nothing cleaned. Excluded, in order: an "
    "empty instruction or response; a forbidden substring in any field; a normalized user text equal to "
    "any evaluation prompt or ARC form (every bank split); a near duplicate (NEAR_DUPLICATE at "
    "eligibility.near_duplicate.max_jaccard) of any evaluation prompt or form, by the instruction alone or "
    "by the user text; then the first row per normalized user text in file order; then the token audit. "
    "Per category, the eligible rows in file order are shuffled with random.Random(derive_seed(design_seed, "
    "'kt-units', category)): the first task_rows_per_category are task rows (the query rows), the next n "
    "form the unit (one development group), the rest are unused; n = rows_per_unit, or floor((smallest "
    "eligible count - task rows) / round_down_to) * round_down_to for every unit when a category has fewer "
    "than task rows + rows_per_unit eligible rows. Each excluded row is counted once, under its first reason in "
    "this order. The banks are the prepared-v3 bank files, copied byte "
    "for byte and re-audited.")
TASK_QUERY_LOSS_DEFINITION = (
    "the training loss (per-example mean NLL over the response and end-of-turn targets) of each task row: "
    "the query rows of a task data config are the held-back task rows of each category (TASK_RULE), not "
    "reference rows")
REPORT_THRESHOLDS = (0.3, 0.5, 0.7)


def render_user_text(instruction: str, context: str) -> str:
    return f"{instruction}\n\n{context}" if context.strip() else instruction


class NearIndex:
    """Largest character 5-gram Jaccard (``prepare.NEAR_DUPLICATE``) of a text with any indexed
    text, exact for every score at or above ``floor`` and 0.0 below it: Jaccard >= t needs the
    two shingle sets' sizes within a factor 1/t, so only texts in that size window are counted."""

    def __init__(self, texts: Sequence[tuple[str, str]], floor: float = min(REPORT_THRESHOLDS)) -> None:
        self.floor = floor
        sized = sorted(((len(_shingles(normalize(text))), key, _shingles(normalize(text))) for key, text in texts),
                       key=lambda t: (t[0], t[1]))
        self.ids = [key for _, key, _ in sized]
        self.sizes = [size for size, _, _ in sized]
        self.index: dict[str, list[int]] = {}
        for k, (_, _, shingles) in enumerate(sized):
            for shingle in shingles:
                self.index.setdefault(shingle, []).append(k)   # ascending k = ascending size

    def nearest(self, text: str) -> tuple[float, str | None]:
        mine = _shingles(normalize(text))
        n = len(mine)
        low = bisect.bisect_left(self.sizes, self.floor * n)
        high = bisect.bisect_right(self.sizes, n / self.floor)
        if low >= high:
            return 0.0, None
        shared: Counter = Counter()
        for shingle in mine:
            postings = self.index.get(shingle)
            if postings:
                shared.update(postings[bisect.bisect_left(postings, low):bisect.bisect_left(postings, high)])
        best, who = 0.0, None
        for k, inter in shared.items():
            value = inter / (n + self.sizes[k] - inter)
            if value > best or (value == best and who is not None and self.ids[k] < who):
                best, who = value, self.ids[k]
        return (best, who) if best >= self.floor else (0.0, None)


def unit_size(eligible: dict[str, int], rows_per_unit: int, task_rows: int, step: int) -> int:
    """n of TASK_RULE step 4 (refused when no unit of at least one step fits)."""
    smallest = min(eligible.values())
    if smallest >= task_rows + rows_per_unit:
        return rows_per_unit
    n = (smallest - task_rows) // step * step
    if n < step:
        raise DataError(f"the smallest category has {smallest} eligible rows: no unit of {step} rows fits "
                        f"after {task_rows} task rows")
    return n


def _evaluation_forms(items: dict[str, list[dict]]) -> list[tuple[str, str]]:
    """(prompt id, text) of every evaluation prompt and every form of every ARC item, all splits."""
    out = []
    for bank in ("dev", "selector", "hidden"):
        for item in items[bank]:
            out.append((item["prompt_id"], item["prompt"]))
            if item["kind"] in ("arc_generation", "arc_utility"):
                out += [(item["prompt_id"], form) for form in arc_prompt_forms(item["question"], item["labels"],
                                                                                item["texts"])]
    return out


def _import_banks(config: dict, bank_manifest: bytes, bank_files: dict[str, bytes]) -> tuple[dict, dict]:
    spec = config["banks_from"]
    if sha256_bytes(bank_manifest) != spec["manifest_sha256"]:
        raise DataError("the bank source manifest differs from banks_from.manifest_sha256")
    recorded = json.loads(bank_manifest)["files"]
    if set(bank_files) != set(TASK_BANK_FILES):
        raise DataError(f"the bank import needs exactly {list(TASK_BANK_FILES)}")
    for name in TASK_BANK_FILES:
        digest = sha256_bytes(bank_files[name])
        if digest != spec["files"][name] or recorded.get(name) != digest:
            raise DataError(f"{name}: its hash differs from banks_from or from the source manifest")
    items = {bank: _jsonl(bank_files[BANK_FILES[bank]]) for bank in ("dev", "selector", "hidden")}
    receipt = {"source_manifest_sha256": spec["manifest_sha256"], "files": dict(spec["files"]),
               "items": {bank: dict(sorted(Counter(i["kind"] for i in items[bank]).items())) for bank in items}}
    return items, receipt


def _reaudit(codec, max_prompt: int, items: dict[str, list[dict]]) -> int:
    """Re-encode every imported item; refuse unless each token hash equals the recorded one."""
    differ, failed = 0, 0
    for bank in items.values():
        for item in bank:
            try:
                if item["kind"] == "arc_utility":
                    ids, _ = encode_mc(codec, item["question"], item["labels"], item["texts"], max_prompt)
                else:
                    ids = encode_generation_prompt(codec, item["prompt"], max_prompt)
            except (TooLong, ControlTokenError, BoundaryMismatch):
                failed += 1
                continue
            differ += ids_sha256(ids) != item["token_sha256"]
    if differ or failed:
        raise DataError(f"bank re-audit: {differ} item(s) encode differently and {failed} fail with this tokenizer")
    return sum(len(bank) for bank in items.values())


def prepare_task(config: dict, dolly: bytes, bank_manifest: bytes, bank_files: dict[str, bytes], tokenizer: Any,
                 tokenizer_identity: dict) -> dict[str, bytes]:
    """Every prepared file as bytes (relative path -> content), including the manifest."""
    validate_task_data_config(config)
    src, units, elig = config["source"], config["units"], config["eligibility"]
    seed, categories = config["design_seed"], src["categories"]
    forbidden, limit = elig["forbidden_substrings"], elig["near_duplicate"]["max_jaccard"]
    limits = config["tokenizer"]
    eot = limits["end_of_turn_token"]
    codec = build_codec(tokenizer, eot, [eot], eot)

    rows, receipt = parse_dolly(dolly, src["sha256"], "dolly", categories)
    items, bank_receipt = _import_banks(config, bank_manifest, bank_files)
    bank_receipt["reaudited_items"] = _reaudit(codec, limits["max_prompt_tokens"], items)
    forms = _evaluation_forms(items)
    exact = {normalize(text) for _, text in forms} - {""}
    floor = min(min(REPORT_THRESHOLDS), limit)            # exact at the configured limit, even below 0.3
    near = NearIndex(forms, floor)

    reasons = {c: Counter() for c in categories}
    near_counts = {"instruction": Counter(), "user_text": Counter()}
    passed = []
    for row in rows:
        user = render_user_text(row["instruction"], row["context"])
        why = []
        if not row["instruction"].strip():
            why.append("empty_instruction")
        if not row["response"].strip():
            why.append("empty_response")
        if any(s in row[field] for field in ("instruction", "context", "response", "category") for s in forbidden):
            why.append("control_string")
        if normalize(user) in exact:
            why.append("evaluation_prompt_overlap")
        if not why:
            scores = {"instruction": near.nearest(row["instruction"])[0], "user_text": near.nearest(user)[0]}
            for which, score in scores.items():
                for t in REPORT_THRESHOLDS:
                    near_counts[which][str(t)] += score >= t
            if max(scores.values()) >= limit:
                why.append("near_duplicate_of_evaluation_prompt")
        if why:
            reasons[row["category"]][why[0]] += 1            # the first reason in rule order: totals add up
        else:
            passed.append({**row, "user": user})
    seen, kept, duplicates = set(), [], Counter()
    for row in passed:
        key = normalize(row["user"])
        if key in seen:
            duplicates[row["category"]] += 1
        else:
            seen.add(key)
            kept.append(row)
    eligible_rows: dict[str, list[dict]] = {c: [] for c in categories}
    for row in kept:
        try:
            example = encode_train(codec, "candidate", row["user"], row["response"], limits["max_train_tokens"])
            if example.n_prompt > limits["max_prompt_tokens"]:
                raise TooLong("prompt over the limit")
        except (TooLong, ControlTokenError, NoTargets) as exc:
            reasons[row["category"]][f"token_audit_{type(exc).__name__}"] += 1
            continue
        eligible_rows[row["category"]].append(row)

    expected = elig["expected"]
    _check_expected(receipt["records_by_category"], expected["records"], "Dolly records")
    eligible = {c: len(eligible_rows[c]) for c in categories}
    _check_expected(eligible, expected["eligible"], "Dolly eligible rows")
    task_n, step = units["task_rows_per_category"], units["round_down_to"]
    n = unit_size(eligible, units["rows_per_unit"], task_n, step)
    _check_expected({"rows_per_unit": n}, {"rows_per_unit": expected["rows_per_unit"]}, "units")

    unit_rows, task_rows, unused, unit_of = {}, [], {}, {}
    for category in categories:
        order = list(eligible_rows[category])
        random.Random(derive_seed(seed, "kt-units", category)).shuffle(order)
        gid = opaque_id("g", derive_seed(seed, "unit-id", category))
        task_rows += order[:task_n]
        unit_rows[gid] = order[task_n:task_n + n]
        unused[category] = sorted(r["line"] for r in order[task_n + n:])
        unit_of[gid] = category
    row_id = {r["line"]: opaque_id("r", derive_seed(seed, "row-id", f"dolly:{r['line']}"))
              for rs in unit_rows.values() for r in rs}
    query_id = {r["line"]: opaque_id("q", derive_seed(seed, "query-id", f"dolly:{r['line']}")) for r in task_rows}
    all_ids = list(row_id.values()) + list(query_id.values()) + list(unit_rows) + [
        i["prompt_id"] for bank in items.values() for i in bank]
    if len(set(all_ids)) != len(all_ids):
        raise DataError("internal: opaque identifier collision")
    train = [{"uid": f"dolly:{r['line']}", "prompt": r["user"], "response": r["response"], "line": r["line"]}
             for rs in unit_rows.values() for r in rs]
    queries = [{"uid": f"dolly:{r['line']}", "prompt": r["user"], "response": r["response"], "line": r["line"]}
               for r in task_rows]
    _assert_disjoint(train, queries, items)

    task_index = NearIndex([(query_id[r["line"]], r["user"]) for r in task_rows], floor)
    near_task = Counter(unit_of[gid] for gid, rs in unit_rows.items() for r in rs
                        if task_index.nearest(r["user"])[0] >= limit)

    pairs = ([{"id": row_id[r["line"]], "prompt": r["prompt"], "response": r["response"]} for r in train]
             + [{"id": query_id[r["line"]], "prompt": r["prompt"], "response": r["response"]} for r in queries])
    token_info, token_summary = _token_audit(codec, limits, pairs, [])

    files: dict[str, bytes] = {}
    files[TRAIN_ROWS] = jsonl_bytes(sorted(({"row_id": row_id[r["line"]], "prompt": r["prompt"],
                                             "response": r["response"], **token_info[row_id[r["line"]]]}
                                            for r in train), key=lambda r: r["row_id"]))
    files[QUERY_ROWS] = jsonl_bytes(sorted(({"query_id": query_id[r["line"]], "prompt": r["prompt"],
                                             "response": r["response"], **token_info[query_id[r["line"]]]}
                                            for r in queries), key=lambda r: r["query_id"]))
    for name in TASK_BANK_FILES:
        files[name] = bank_files[name]
    ids = sorted(unit_rows)
    ranks = list(ids)
    random.Random(derive_seed(seed, "tie-ranks", "dev")).shuffle(ranks)
    groups = [{"group_id": gid, "size": len(unit_rows[gid]),
               "members": sorted(row_id[r["line"]] for r in unit_rows[gid])} for gid in ids]
    files[GROUPS] = canonical_json({"partitions": {"dev": {"groups": groups, "menu": ["a0"] + ids},
                                                   "heldout": {"groups": [], "menu": ["a0"]}}})
    x0 = []
    unit_table = {}
    for gid in ids:
        info = [token_info[row_id[r["line"]]] for r in unit_rows[gid]]
        tokens = _summary([i["prompt_tokens"] + i["target_tokens"] for i in info])
        x0.append({"group_id": gid, "size": len(unit_rows[gid]), "tie_rank": ranks.index(gid),
                   "provenance": {"Dolly-15k": len(unit_rows[gid])},
                   "chars": _summary([len(r["user"]) + len(r["response"]) for r in unit_rows[gid]]),
                   "response_chars": _summary([len(r["response"]) for r in unit_rows[gid]]),
                   "tokens": tokens, "target_tokens": _summary([i["target_tokens"] for i in info])})
        unit_table[gid] = {"category": unit_of[gid], "rows": len(unit_rows[gid]), "tokens": tokens}
    files[X0_STATIC] = canonical_json({
        "kind": "selector-facing static unit features (no category)",
        "schema": {"size": "rows removed", "tie_rank": "seeded rank independent of membership",
                   "provenance": "source counts", "chars": "user text+response characters",
                   "response_chars": "response characters", "tokens": "prompt+target tokens",
                   "target_tokens": "response+end-of-turn tokens"},
        "partitions": {"dev": x0, "heldout": []}})
    files[AUDITOR] = canonical_json({
        "kind": "AUDITOR ONLY: Dolly lines and categories; never read by engine or selector commands",
        "rows": {row_id[r["line"]]: {"line": r["line"], "category": unit_of[gid], "unit": gid}
                 for gid, rs in unit_rows.items() for r in rs},
        "queries": {query_id[r["line"]]: {"line": r["line"], "category": r["category"]} for r in task_rows},
        "units": unit_of, "unused_lines": unused})
    per_category = {c: {"records": receipt["records_by_category"][c],
                        "excluded_by_reason": dict(sorted(reasons[c].items())),
                        "duplicate_user_text_dropped": duplicates[c], "eligible": eligible[c], "task": task_n,
                        "unit": n, "unused": len(unused[c]), "unit_rows_near_task_rows": near_task[c]}
                    for c in categories}
    manifest = {
        "kind": "safety-selection prepared manifest",
        "data_config": config, "data_config_sha256": config_sha256(config),
        "normalization": NORMALIZATION, "seed_derivation": SEED_DERIVATION,
        "task_rule": TASK_RULE, "near_duplicate_rule": NEAR_DUPLICATE,
        "query_loss_definition": TASK_QUERY_LOSS_DEFINITION,
        "source": {"sha256": src["sha256"], "license": src["license"], **receipt},
        "eligibility": {"by_category": per_category, "expected_counts": "matched",
                        "near_duplicates_at_or_above": {k: dict(sorted(v.items())) for k, v in near_counts.items()},
                        "unit_rows_near_task_rows": sum(near_task.values())},
        "rows_per_unit": n, "units": unit_table,
        "corpus": {"rows": len(train), "queries": len(queries)},
        "groups": {"dev": {"groups": len(groups), "members": len(train), "menu_options": len(ids) + 1},
                   "heldout": {"groups": 0, "members": 0, "menu_options": 1}},
        "banks": {bank: dict(sorted(Counter(i["kind"] for i in items[bank]).items())) for bank in items},
        "bank_import": bank_receipt,
        "seed_namespaces": config["seed_namespaces"], "tokenizer": tokenizer_identity,
        "token_audit": token_summary,
        "scopes": {"engine": [TRAIN_ROWS, QUERY_ROWS, GROUPS, BANK_FILES["dev"], BANK_FILES["selector"]],
                   "selector": [X0_STATIC], "reference": [BANK_FILES["hidden"]], "auditor": [AUDITOR]},
        "files": {name: sha256_bytes(data) for name, data in sorted(files.items())}}
    manifest_bytes = canonical_json(manifest)
    files[MANIFEST] = manifest_bytes
    files[MANIFEST_SHA] = (sha256_bytes(manifest_bytes) + "\n").encode("ascii")
    return files
