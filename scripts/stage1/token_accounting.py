"""Token accounting of stage-1 edits (W1-01's base; addendum §5 item 1; standard library only).

T1's PreparedView keeps target tokens only. ``TokenView`` keeps, per training row, its prompt_tokens and target_tokens
(target = response + end-of-turn tokens; total = prompt + target), its unit and category; the text fields are dropped at
once. The manifest must hash to the pinned value and the files read must hash to the manifest's values.

``account(view, ...)`` gives an edit's token accounting without text: the rows removed, rewritten and added; their
target and total tokens; each as a share of P's corpus totals; the same per unit and per category; the edited corpus's
rows and its optimizer steps, steps = ceil(rows / rows_per_step) (rows_per_step = micro_batch x grad_accum of the
recipe; 128 for recipe B and S). Shares are always against P's totals, never the edited corpus. A rewritten row reports
its tokens before (P's) and after (the caller's count of the new encoding). Added rows' token counts come from the
add writer's sealed record (REQ-7).

Interface for the lead's Parts E and F: ``TokenView(root, manifest_sha256)`` with ``.prompt_tokens``, ``.target_tokens``
and ``.total_tokens`` (row id -> int), ``.units``, ``.members``, ``.category``; ``account(...)`` returns a plain dict
(documented in its docstring); ``steps(rows, rows_per_step)``.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Iterable, Mapping

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1.s1common import GROUPS, TRAIN_ROWS, Refusal, iter_jsonl, strict_json  # noqa: E402

STEPS_RULE = "steps = ceil(rows / rows_per_step), rows_per_step = micro_batch x grad_accum (128 for recipe B and S)"


def steps(rows: int, rows_per_step: int) -> int:
    if isinstance(rows, bool) or not isinstance(rows, int) or rows < 1 or rows_per_step < 1:
        raise Refusal("steps need a positive row count and a positive rows-per-step")
    return math.ceil(rows / rows_per_step)


def _count(value, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Refusal(f"{what} is not a non-negative integer")
    return value


class TokenView:
    """Row ids, prompt and target tokens, units and categories of a prepared set; no text is kept."""

    def __init__(self, root: str | Path, manifest_sha256: str):
        root = Path(root)
        manifest_bytes = (root / "manifest.json").read_bytes()
        self.manifest_sha256 = sha256_bytes(manifest_bytes)
        if self.manifest_sha256 != manifest_sha256:
            raise Refusal(f"the prepared manifest hashes to {self.manifest_sha256}, expected {manifest_sha256}")
        manifest = strict_json(manifest_bytes)
        self.file_sha256 = {}
        for name in (TRAIN_ROWS, GROUPS):
            digest = sha256_file(root / name)
            if digest != manifest["files"].get(name):
                raise Refusal(f"{name} hashes to {digest}, the manifest names another file")
            self.file_sha256[name] = digest
        self.prompt_tokens: dict[str, int] = {}
        self.target_tokens: dict[str, int] = {}
        for row in iter_jsonl(root / TRAIN_ROWS):
            row_id, prompt, target = row.get("row_id"), row.get("prompt_tokens"), row.get("target_tokens")
            row.clear()
            if not isinstance(row_id, str) or row_id in self.target_tokens:
                raise Refusal("the training row ids are not distinct strings")
            if _count(prompt, f"row {row_id} prompt_tokens") < 1 or _count(target, f"row {row_id} target_tokens") < 1:
                raise Refusal(f"row {row_id} has no positive token counts")
            self.prompt_tokens[row_id], self.target_tokens[row_id] = prompt, target
        self.total_tokens = {r: self.prompt_tokens[r] + self.target_tokens[r] for r in self.target_tokens}
        if len(self.target_tokens) != manifest["corpus"]["rows"]:
            raise Refusal("the training rows disagree with the manifest's row count")
        partitions = strict_json((root / GROUPS).read_bytes())["partitions"]
        if partitions["heldout"]["groups"] != [] or manifest["groups"]["heldout"]["members"] != 0:
            raise Refusal("the held-out partition is not empty")
        self.members = {g["group_id"]: sorted(g["members"]) for g in partitions["dev"]["groups"]}
        self.category = {gid: unit["category"] for gid, unit in manifest["units"].items()}
        self.units = sorted(self.members)
        if set(self.units) != set(self.category):
            raise Refusal("the dev groups and the manifest's units differ")
        seen: set[str] = set()
        for gid in self.units:
            if len(set(self.members[gid])) != len(self.members[gid]):
                raise Refusal(f"unit {gid} lists a row twice")
            if seen & set(self.members[gid]):
                raise Refusal(f"unit {gid} shares rows with another unit")
            seen |= set(self.members[gid])
        if seen != set(self.target_tokens):
            raise Refusal("the units do not partition the training rows")
        self.unit_of = {row: gid for gid in self.units for row in self.members[gid]}

    def totals(self) -> dict:
        return {"rows": len(self.target_tokens), "target_tokens": sum(self.target_tokens.values()),
                "total_tokens": sum(self.total_tokens.values())}


def _block(view: TokenView, rows: list[str], totals: dict) -> dict:
    target = sum(view.target_tokens[r] for r in rows)
    total = sum(view.total_tokens[r] for r in rows)
    by_unit = {g: {"rows": 0, "target_tokens": 0, "total_tokens": 0} for g in view.units}
    for r in rows:
        u = by_unit[view.unit_of[r]]
        u["rows"] += 1
        u["target_tokens"] += view.target_tokens[r]
        u["total_tokens"] += view.total_tokens[r]
    by_category: dict[str, dict] = {}
    for g, u in by_unit.items():
        c = by_category.setdefault(view.category[g], {"rows": 0, "target_tokens": 0, "total_tokens": 0})
        for k in c:
            c[k] += u[k]
    return {"rows": len(rows), "target_tokens": target, "total_tokens": total,
            "share_of_rows": len(rows) / totals["rows"], "share_of_target_tokens": target / totals["target_tokens"],
            "share_of_total_tokens": total / totals["total_tokens"], "by_unit": by_unit,
            "by_category": dict(sorted(by_category.items()))}


def account(view: TokenView, *, removed: Iterable[str] = (), rewritten: Mapping[str, Mapping[str, int]] | None = None,
            added: Mapping[str, Mapping[str, int]] | None = None, rows_per_step: int = 128) -> dict:
    """The token accounting of one edit.

    removed: training row ids. rewritten: row id -> {"prompt_tokens", "target_tokens"} of the new encoding.
    added: add id -> {"prompt_tokens", "target_tokens"} (from REQ-7's sealed record).
    Returns {"corpus": P's totals, "removed": block, "rewritten": {"before": block, "after": {...}},
    "added": {...}, "edited_corpus": {"rows", "target_tokens", "total_tokens", "steps"}, "steps_rule"}; a block holds
    rows, target and total tokens, their shares of P's totals, and the same by unit and by category."""
    totals = view.totals()
    removed = list(removed)
    rewritten = dict(rewritten or {})
    added = dict(added or {})
    for name, rows in (("removed", removed), ("rewritten", list(rewritten))):
        if len(set(rows)) != len(rows) or not set(rows) <= set(view.target_tokens):
            raise Refusal(f"the {name} rows are not distinct training rows")
    if set(removed) & set(rewritten):
        raise Refusal("a row is both removed and rewritten")
    if set(added) & set(view.target_tokens):
        raise Refusal("an added id is a training row id")
    out: dict = {"corpus": totals, "removed": _block(view, removed, totals), "steps_rule": STEPS_RULE,
                 "rows_per_step": rows_per_step}
    after_target = after_total = 0
    for row, counts in rewritten.items():
        p, t = _count(counts.get("prompt_tokens"), f"rewrite {row}"), _count(counts.get("target_tokens"), f"rewrite {row}")
        if p != view.prompt_tokens[row]:
            raise Refusal(f"rewrite {row}: its prompt tokens differ from P's (a rewrite keeps the prompt)")
        if t < 1:
            raise Refusal(f"rewrite {row}: the new encoding has no target tokens")
        after_target += t
        after_total += p + t
    out["rewritten"] = {"before": _block(view, list(rewritten), totals),
                        "after": {"rows": len(rewritten), "target_tokens": after_target, "total_tokens": after_total}}
    add_target = add_total = 0
    for row, counts in added.items():
        p, t = _count(counts.get("prompt_tokens"), f"add {row}"), _count(counts.get("target_tokens"), f"add {row}")
        if p < 1 or t < 1:
            raise Refusal(f"add {row} has no positive token counts")
        add_target += t
        add_total += p + t
    out["added"] = {"rows": len(added), "target_tokens": add_target, "total_tokens": add_total,
                    "share_of_target_tokens": add_target / totals["target_tokens"],
                    "share_of_total_tokens": add_total / totals["total_tokens"]}
    rows = totals["rows"] - len(removed) + len(added)
    target = (totals["target_tokens"] - out["removed"]["target_tokens"] - out["rewritten"]["before"]["target_tokens"]
              + after_target + add_target)
    total = (totals["total_tokens"] - out["removed"]["total_tokens"] - out["rewritten"]["before"]["total_tokens"]
             + after_total + add_total)
    out["edited_corpus"] = {"rows": rows, "target_tokens": target, "total_tokens": total,
                            "steps": steps(rows, rows_per_step)}
    return out
