"""Rows, row ids, the user turn, the per-row caches, the drop rule and the known-answer gate's block (stdlib only).

Rebuilt 9 October 2026 (10:27 UTC, clock checked) from the lead's partial build. Runs on the Mac (the bundle, the
verification, the summary) and on the pod (both judges). A row's id is its source and its 1-based line in its file:
dark-<line>, light-<line>, dolly-<line>, and for a refill round N <arm>-r<N>-<line>. A refill row carries the three
slot fields that sf_screen.py writes (slot_arm, slot_line, rank: the dropped row it may replace and its rank there).
The user turn is the engine's own rule `instruction-blank-line-context` (experiments.safety_selection.prepare_task
.render_user_text, imported, not copied): the instruction, then a blank line and the context when the context is not
blank. The assistant turn is the response. The Dolly baseline rows are the prepared set's engine/train_rows.jsonl,
whose `prompt` the preparer already rendered with that rule. Records and messages hold ids, counts, labels and SHA-256
only; never row, prompt, answer or judge-output text.

Revised 9 October 2026 (17:11 UTC, clock checked) for the lead's Granite backend: the screen's own known-answer counts
are gone (the lead's pod job runs the gate: granite_pod.known_answer_verdict); what stays here is reading its block:
the rule over the block's counts (the lead's thresholds, which the bundle builder checks equal KA_MIN_IDENTICAL and
KA_MAX_DELTA_YES) and a recount of those counts from the block's own differing prompt ids and flips against the
reference's Mac labels. A Granite cache record now holds the SHA-256 of the exact text the model received
(judge_triples' input_sha256) instead of an error count: a call that raises ends the step (no row is labelled invalid
for an error), and an input over the token limit refuses the whole step before the model loads (the lead's precheck).
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


# ---------------------------------------------------------------- labels, the drop rule, the smoke-run selection

def granite_label(lead_label: str) -> str:
    """granite_files.parse_score's label (yes, no, unparsed) in the screen's form (Yes, No, invalid)."""
    if lead_label not in P.LEAD_LABELS:
        raise Refusal(f"a Granite label {lead_label!r} is not one of {list(P.LEAD_LABELS)}")
    return P.LEAD_LABELS[lead_label]


def dropped(harm_label: str) -> bool:
    """rules-v2 classifier_screen: a fiction row is dropped when Granite harm is Yes or invalid (after one retry). For
    a refill candidate the same test says it is not clean."""
    if harm_label not in P.LABELS:
        raise Refusal(f"a Granite harm label {harm_label!r} is not one of {list(P.LABELS)}")
    return harm_label != "No"


def selected(rows: list, limit: int | None) -> list:
    """The rows a run screens: every row, or with a limit the first `limit` rows of each source (a smoke run)."""
    if limit is None:
        return list(rows)
    taken: dict = {}
    out = []
    for row in rows:
        if taken.get(row.source, 0) < limit:
            taken[row.source] = taken.get(row.source, 0) + 1
            out.append(row)
    return out


# ---------------------------------------------------------------- the known-answer gate's block (the lead's gate)

KA_RULE = (f"the lead's gate (granite_pod.known_answer_verdict): pass when all {P.KA_N} items are judged, at least "
           f"{P.KA_MIN_IDENTICAL} labels equal the Mac's, and |pod yes - Mac yes| <= {P.KA_MAX_DELTA_YES} (Mac: "
           f"{P.KA_MAC_YES} yes); an unparsed label differs")
KA_COUNT_KEYS = ("n", "judged", "identical", "mac_yes", "pod_yes", "delta_yes", "pod_unparsed")
FLIP_KEYS = ("no->unparsed", "no->yes", "yes->no", "yes->unparsed")


def ka_rule_passes(counts) -> bool:
    """The lead's rule over a block's counts: all n = 200 judged, at least 190 identical, |pod yes - Mac yes| <= 5, and
    the Mac side the reference's 93 yes."""
    return (isinstance(counts, dict) and counts.get("n") == P.KA_N and counts.get("judged") == P.KA_N
            and counts.get("mac_yes") == P.KA_MAC_YES and _int(counts.get("identical"))
            and counts["identical"] >= P.KA_MIN_IDENTICAL and _int(counts.get("delta_yes"))
            and abs(counts["delta_yes"]) <= P.KA_MAX_DELTA_YES)


def ka_recount(block, mac_labels: dict) -> dict:
    """The gate block's counts recomputed from its own differing prompt ids and flips against the reference's Mac
    labels {prompt id: yes/no} (ids and labels only); refuses a block whose counts, ids and flips disagree. pod_yes and
    delta_yes are recounted only when every item was judged (else they are None). Returns the recounted counts."""
    differing = block.get("differing_prompt_ids") if isinstance(block, dict) else None
    flips = block.get("flips") if isinstance(block, dict) else None
    judged = block.get("judged") if isinstance(block, dict) else None
    if not (isinstance(differing, list) and isinstance(flips, dict) and _int(judged) and 0 <= judged <= len(mac_labels)
            and set(flips) <= set(FLIP_KEYS) and all(_int(v) and v > 0 for v in flips.values())):
        raise Refusal("the known-answer block has no readable judged count, differing ids or flips")
    if len(set(differing)) != len(differing) or set(differing) - set(mac_labels):
        raise Refusal("the known-answer block names a differing id twice, or one outside the reference")
    for mac in ("yes", "no"):
        from_mac = sum(v for k, v in flips.items() if k.startswith(f"{mac}->"))
        if from_mac != sum(mac_labels[pid] == mac for pid in differing):
            raise Refusal("the known-answer block's flips do not match its differing ids")
    mac_yes = sum(label == "yes" for label in mac_labels.values())
    pod_yes = (mac_yes - flips.get("yes->no", 0) - flips.get("yes->unparsed", 0) + flips.get("no->yes", 0)
               if judged == len(mac_labels) else None)
    counts = {"n": len(mac_labels), "judged": judged, "identical": judged - len(differing), "mac_yes": mac_yes,
              "pod_yes": pod_yes, "delta_yes": None if pod_yes is None else pod_yes - mac_yes,
              "pod_unparsed": flips.get("yes->unparsed", 0) + flips.get("no->unparsed", 0)}
    wrong = sorted(k for k, v in counts.items() if v is not None and block.get(k) != v)
    if wrong:
        raise Refusal(f"the known-answer block's counts {wrong} differ from their recount from its own ids and flips")
    return counts


# ---------------------------------------------------------------- per-row caches (ids, labels, counts, hashes)

GRANITE_KEYS = frozenset({"row_id", "source", "line", "criteria", "label", "attempts", "reason", "input_tokens",
                          "input_sha256", "trimmed", "response_sha256", "user_sha256"})
GRANITE_REASONS = (None, "unparsed")
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
          and r["label"] in P.LABELS and r["reason"] in GRANITE_REASONS and r["attempts"] in (1, 2)
          and _int(r["input_tokens"]) and r["input_tokens"] >= 0 and _hex64(r["input_sha256"])
          and isinstance(r["trimmed"], bool) and ((r["label"] == "invalid") == (r["reason"] is not None))
          and (r["attempts"] == 2 or r["label"] != "invalid"))
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
