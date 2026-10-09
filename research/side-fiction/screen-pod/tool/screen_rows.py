"""Rows, row ids, the user turn, the per-row caches, the drop rule and the known-answer rule (stdlib only).

Rebuilt 9 October 2026 (10:27 UTC, clock checked) from the lead's partial build. Runs on the Mac (the bundle, the
verification, the summary) and on the pod (both judges). A row's id is its source and its 1-based line in its file:
dark-<line>, light-<line>, dolly-<line>, and for a refill round N <arm>-r<N>-<line>. A refill row carries the three
slot fields that sf_screen.py writes (slot_arm, slot_line, rank: the dropped row it may replace and its rank there).
The user turn is the engine's own rule `instruction-blank-line-context` (experiments.safety_selection.prepare_task
.render_user_text, imported, not copied): the instruction, then a blank line and the context when the context is not
blank. The assistant turn is the response. The Dolly baseline rows are the prepared set's engine/train_rows.jsonl,
whose `prompt` the preparer already rendered with that rule. Records and messages hold ids, counts, labels and SHA-256
only; never row, prompt, answer or judge-output text.
"""
from __future__ import annotations

import collections
import json
import os
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402  (also puts gate_b and the engine on sys.path)
from common import Refusal, jsonl_records, sha256_bytes, sha256_text  # noqa: E402
from experiments.safety_selection.prepare_task import render_user_text  # noqa: E402  (the engine's prompt rule)
from experiments.safety_selection.textproc import GUARD_RESPONSE_CATEGORIES, GUARD_SAFETY  # noqa: E402

Row = collections.namedtuple("Row", "row_id source arm line category slot_arm slot_line rank dolly_row_id user_turn "
                                    "assistant_turn response_sha256 user_sha256")
INDEX_FIELDS = ("row_id", "source", "arm", "line", "category", "slot_arm", "slot_line", "rank", "dolly_row_id",
                "response_sha256", "user_sha256")


def user_turn_of(instruction: str, context: str) -> str:
    """The engine's prompt rule `instruction-blank-line-context` (prepare_task.render_user_text, called as it is)."""
    return render_user_text(instruction, context)


def index_entry(row: Row) -> dict:
    """The row's ids, category or slot fields and hashes: what the per-row outputs carry (no text)."""
    return {k: getattr(row, k) for k in INDEX_FIELDS}


def _lines(data: bytes, what: str):
    """(line number, object) of a JSONL file whose only blank line is the final newline (line numbers are row ids)."""
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts = parts[:-1]
    for lineno, part in enumerate(parts, 1):
        if not part.strip():
            raise Refusal(f"{what}: line {lineno} is blank; row ids are line numbers, so blank lines are refused")
    yield from jsonl_records(b"\n".join(parts), what)


def _strings(obj: dict, names, what: str, lineno: int) -> None:
    for name in names:
        if not isinstance(obj.get(name), str):
            raise Refusal(f"{what}: line {lineno} field {name!r} is not a string")


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def read_rows(source: str, path: pathlib.Path, sha256: str, expect_rows: int | None = None, round_: int = 1) -> list:
    """The rows of one input file after its SHA-256 is checked. source: dark, light, dolly or refill."""
    path = pathlib.Path(path)
    data = path.read_bytes()
    if sha256_bytes(data) != sha256:
        raise Refusal(f"{source}: {path.name} has SHA-256 {sha256_bytes(data)[:16]}, not the pinned {sha256[:16]}")
    what = f"{source} file {path.name}"
    rows, slots = [], set()
    for lineno, obj in _lines(data, what):
        if not isinstance(obj, dict):
            raise Refusal(f"{what}: line {lineno} is not an object")
        if source in P.FICTION_ARMS or source == "refill":
            fields = P.FICTION_FIELDS if source in P.FICTION_ARMS else P.REFILL_FIELDS
            if tuple(sorted(obj)) != tuple(sorted(fields)):
                raise Refusal(f"{what}: line {lineno} has fields {sorted(obj)}, not {sorted(fields)}")
            _strings(obj, P.FICTION_FIELDS, what, lineno)
            match = P.CATEGORY_RE.match(obj["category"])
            if not match:
                raise Refusal(f"{what}: line {lineno} has a category outside dark_b1..8 and light_b1..8")
            arm = match.group(1)
            if source in P.FICTION_ARMS and arm != source:
                raise Refusal(f"{what}: line {lineno} has a {arm} category in the {source} file")
            if not obj["instruction"].strip() or not obj["response"].strip():
                raise Refusal(f"{what}: line {lineno} has an empty instruction or response")
            slot = (None, None, None)
            if source == "refill":
                slot = (obj["slot_arm"], obj["slot_line"], obj["rank"])
                if (slot[0] != arm or not _int(slot[1]) or not 1 <= slot[1] <= P.ARM_ROWS or not _int(slot[2])
                        or slot[2] < 1):
                    raise Refusal(f"{what}: line {lineno} has slot fields that are not its category's arm, a line "
                                  f"1..{P.ARM_ROWS} and a rank of at least 1")
                if slot in slots:
                    raise Refusal(f"{what}: line {lineno} repeats the slot and rank of an earlier line")
                slots.add(slot)
            row_id = f"{arm}-{lineno}" if source in P.FICTION_ARMS else f"{arm}-r{round_}-{lineno}"
            user, assistant = user_turn_of(obj["instruction"], obj["context"]), obj["response"]
            rows.append(Row(row_id, source, arm, lineno, obj["category"], *slot, None, user, assistant,
                            sha256_text(assistant), sha256_text(user)))
        elif source == "dolly":
            if tuple(sorted(obj)) != tuple(sorted(P.DOLLY_FIELDS)):
                raise Refusal(f"{what}: line {lineno} has fields {sorted(obj)}, not {sorted(P.DOLLY_FIELDS)}")
            _strings(obj, ("prompt", "response", "row_id"), what, lineno)
            if not obj["row_id"] or len(obj["row_id"]) > 64:
                raise Refusal(f"{what}: line {lineno} has no short row_id")
            rows.append(Row(f"dolly-{lineno}", "dolly", "dolly", lineno, None, None, None, None, obj["row_id"],
                            obj["prompt"], obj["response"], sha256_text(obj["response"]), sha256_text(obj["prompt"])))
        else:
            raise Refusal(f"unknown source {source!r}")
    if expect_rows is not None and len(rows) != expect_rows:
        raise Refusal(f"{what}: {len(rows)} rows, expected {expect_rows}")
    if source == "dolly" and len({r.dolly_row_id for r in rows}) != len(rows):
        raise Refusal(f"{what}: a row_id appears twice")
    return rows


# ---------------------------------------------------------------- labels, the drop rule and the known-answer rule

def mac_label(value) -> str:
    """second_judge_probe's cached label ("yes", "no", or None for no score) in the screen's form."""
    return {"yes": "Yes", "no": "No"}.get(value, "invalid")


def dropped(harm_label: str) -> bool:
    """rules-v2 classifier_screen: a fiction row is dropped when Granite harm is Yes or invalid (after one retry). For
    a refill candidate the same test says it is not clean."""
    if harm_label not in P.LABELS:
        raise Refusal(f"a Granite harm label {harm_label!r} is not one of {list(P.LABELS)}")
    return harm_label != "No"


def ka_counts(pairs) -> dict:
    """pairs: (Mac label, pod label) in the screen's form, one per known-answer item (None: not judged)."""
    flips = collections.Counter(f"{m}->{p}" for m, p in pairs if p is not None and m != p)
    judged = [(m, p) for m, p in pairs if p is not None]
    return {"n": len(pairs), "judged": len(judged), "identical": sum(m == p for m, p in judged),
            "mac_yes": sum(m == "Yes" for m, _ in pairs), "pod_yes": sum(p == "Yes" for _, p in judged),
            "mac_invalid": sum(m == "invalid" for m, _ in pairs), "pod_invalid": sum(p == "invalid" for _, p in judged),
            "delta_yes": sum(p == "Yes" for _, p in judged) - sum(m == "Yes" for m, _ in pairs),
            "flips": dict(sorted(flips.items()))}


def ka_complete(counts) -> bool:
    """Every known answer was judged (the check ran to its end; a stopped or broken check is not a verdict)."""
    return isinstance(counts, dict) and counts.get("n") == P.KA_N and counts.get("judged") == P.KA_N


def ka_passed(counts) -> bool:
    """The lead's pre-set rule: all 200 judged, at least 190 identical labels, |pod yes - Mac yes| <= 5 (and the Mac
    side is the recorded 93 yes)."""
    return (ka_complete(counts) and counts.get("mac_yes") == P.KA_MAC_YES
            and _int(counts.get("identical")) and counts["identical"] >= P.KA_MIN_IDENTICAL
            and _int(counts.get("delta_yes")) and abs(counts["delta_yes"]) <= P.KA_MAX_DELTA_YES)


KA_RULE = (f"pass when all {P.KA_N} items are judged, at least {P.KA_MIN_IDENTICAL} labels equal the Mac's, and "
           f"|pod yes - Mac yes| <= {P.KA_MAX_DELTA_YES} (Mac: {P.KA_MAC_YES} yes)")


# ---------------------------------------------------------------- per-row caches (ids, labels, counts, hashes)

GRANITE_KEYS = frozenset({"row_id", "source", "line", "criteria", "label", "attempts", "errors", "reason",
                          "input_tokens", "trimmed", "response_sha256", "user_sha256"})
GRANITE_REASONS = (None, "unparsed", "error", "over_limit")
QWEN_KEYS = frozenset({"row_id", "source", "line", "response_sha256", "user_sha256", "valid", "reason", "safety",
                       "categories", "refusal", "guard_input_tokens", "guard_output_tokens", "guard_stop_reason",
                       "control_strings"})
QWEN_REASONS = (None, "unparsed", "capped", "over_limit", "control_string")
STOP_REASONS = (None, "eos", "max_new_tokens", "other")
HEX = frozenset("0123456789abcdef")


def _count(v) -> bool:
    return v is None or (_int(v) and v >= 0)


def _hex64(v) -> bool:
    return isinstance(v, str) and len(v) == 64 and not set(v) - HEX


def _ids_ok(r: dict) -> bool:
    return (isinstance(r.get("row_id"), str) and 0 < len(r["row_id"]) <= 64 and isinstance(r.get("source"), str)
            and r["source"] in ("dark", "light", "dolly", "refill") and _int(r.get("line")) and r["line"] >= 1
            and _hex64(r.get("response_sha256")) and _hex64(r.get("user_sha256")))


def check_granite(r) -> None:
    ok = (isinstance(r, dict) and set(r) == GRANITE_KEYS and _ids_ok(r) and r["criteria"] in P.CRITERIA
          and r["label"] in P.LABELS and r["reason"] in GRANITE_REASONS and _count(r["attempts"])
          and r["attempts"] <= 2 and _count(r["errors"]) and _count(r["input_tokens"])
          and isinstance(r["trimmed"], bool) and ((r["label"] == "invalid") == (r["reason"] is not None)))
    if not ok:
        raise Refusal("a Granite cache record is malformed")


def check_qwen(r) -> None:
    ok = (isinstance(r, dict) and set(r) == QWEN_KEYS and _ids_ok(r) and isinstance(r["valid"], bool)
          and r["reason"] in QWEN_REASONS and r["refusal"] in ("Yes", "No", None)
          and (r["safety"] is None or r["safety"] in GUARD_SAFETY)
          and (r["categories"] is None or (isinstance(r["categories"], list)
                                           and all(c in GUARD_RESPONSE_CATEGORIES for c in r["categories"])))
          and _count(r["guard_input_tokens"]) and _count(r["guard_output_tokens"])
          and r["guard_stop_reason"] in STOP_REASONS and _count(r["control_strings"])
          and (r["valid"] == (r["reason"] is None)) and (r["valid"] == (r["safety"] is not None)))
    if not ok:
        raise Refusal("a Qwen3Guard cache record is malformed")


def granite_key(r: dict) -> tuple:
    return (r["row_id"], r["criteria"])


def qwen_key(r: dict) -> tuple:
    return (r["row_id"],)


class JsonlCache:
    """Append-only JSONL of per-row records, resumable. A line that is not JSON (one cut by a hard stop) is skipped and
    counted, so its row is judged again; a malformed record, or two records of one key that differ, refuse. Writes are
    flushed per record and fsynced every 50 records and at close."""

    def __init__(self, path: pathlib.Path, check, key):
        self.path, self.check, self.key = pathlib.Path(path), check, key
        self.entries: dict = {}
        self.undecodable = 0
        self._fh, self._unsynced = None, 0
        if self.path.exists():
            for line in self.path.read_bytes().split(b"\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    self.undecodable += 1
                    continue
                check(entry)
                k = key(entry)
                if k in self.entries and self.entries[k] != entry:
                    raise Refusal(f"{self.path.name}: two different records of one key {list(k)}")
                self.entries[k] = entry

    def __len__(self) -> int:
        return len(self.entries)

    def get(self, k):
        return self.entries.get(k)

    def append(self, entry: dict) -> None:
        self.check(entry)
        k = self.key(entry)
        if k in self.entries:
            raise Refusal(f"{self.path.name}: a record of key {list(k)} exists")
        if self._fh is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            cut = self.path.exists() and self.path.stat().st_size > 0 and not self.path.read_bytes().endswith(b"\n")
            self._fh = open(self.path, "ab")
            if cut:
                self._fh.write(b"\n")
        self._fh.write(json.dumps(entry, sort_keys=True).encode("utf-8") + b"\n")
        self._fh.flush()
        self._unsynced += 1
        if self._unsynced >= 50:
            os.fsync(self._fh.fileno())
            self._unsynced = 0
        self.entries[k] = entry

    def close(self) -> None:
        if self._fh is not None:
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self._fh.close()
            self._fh = None


def check_against(entry: dict, row: Row, what: str) -> None:
    """A cached record must name the row's source, line and both hashes (a resumed cache cannot cover another row)."""
    if (entry["source"], entry["line"], entry["response_sha256"], entry["user_sha256"]) != (
            row.source, row.line, row.response_sha256, row.user_sha256):
        raise Refusal(f"{what}: the cached record of {row.row_id} names another row or other hashes")
