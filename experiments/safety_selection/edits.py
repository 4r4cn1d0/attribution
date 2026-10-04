"""Edit files: the training-data edits of the headroom amendment (stdlib only).

An edit is defined by a file written before training and identified by the SHA-256 of its exact
bytes. A run-one job names it through its arm, ``edit-<sha256>`` (``jobs.py``), and the engine
applies it deterministically; the engine never decides an edit itself. Kinds:

- ``remove``: training row ids that are left out of every epoch (as a group removal does);
- ``rewrite``: row id -> a replacement response; the row keeps its id, its prompt and its place
  in the stream, and is trained on the replacement instead of its own response;
- ``add``: new rows (id ``add-...``, prompt, response) inserted into every epoch by the stated
  position rule (``POSITION_RULE``);
- ``combined``: two or three of the above at once.

What is refused when a file is loaded: bytes whose hash is not the arm's; another prepared
dataset (``manifest_sha256``); an unknown field or kind; a removed or rewritten id that is not a
training row, or that is a member of a held-out group (the edit pool excludes them, so an edit
can never touch held-out material); a row both removed and rewritten; an added id that is not
``add-`` prefixed, repeats, or is a training row; empty text; counts that do not match the
lists. Rewritten and added rows are encoded with the policy's codec exactly as training rows
are (``textproc.encode_train``): over-long or control-token text refuses; a rewritten row's
prompt tokens must equal its audited prompt tokens.

Group-removal arms and a0 do not pass through this module: their jobs, streams and outputs are
exactly what they were before edit files existed (a regression test holds the engine to that).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import canonical_json, sha256_bytes
from .jobs import EDIT_ARM_PREFIX, JobError, is_edit_arm
from .textproc import TrainExample, encode_train

__all__ = ["EditError", "Edit", "EDIT_KIND", "EDIT_VERSION", "EDIT_KINDS", "POSITION_RULE", "ADD_PREFIX",
           "EDIT_FILE", "heldout_members", "edit_bytes", "arm_of", "parse_edit", "load_edit",
           "edited_corpus"]

EDIT_KIND = "safety-selection edit"
EDIT_VERSION = 1
EDIT_KINDS = ("remove", "rewrite", "add", "combined")
ADD_PREFIX = "add-"
EDIT_FILE = "edit.json"     # the copy of the edit file inside a run folder (hashed with the run)
POSITION_RULE = ("each epoch: the retained rows in the shared order of the seed (the full sorted corpus "
                 "shuffled with derive_seed(seed, 'data-order', epoch), removed rows dropped); the added rows, "
                 "sorted by id, shuffled with derive_seed(seed, 'added-order', epoch); added row j of m "
                 "inserted after the floor((j + 1) * n / (m + 1))-th of the n retained rows, so retained rows "
                 "keep their relative order and added rows are spread evenly")
_KEYS = {"kind", "version", "name", "edit_kind", "manifest_sha256", "remove", "rewrite", "add", "position_rule",
         "counts", "provenance"}


class EditError(JobError):
    """An edit file is malformed, is not the arm's, or would touch rows it may not touch."""


def heldout_members(prepared: Any) -> frozenset[str]:
    """Every training row that belongs to a held-out group (outside the edit pool)."""
    return frozenset(row for rows in prepared.groups["heldout"].values() for row in rows)


def edit_bytes(document: dict) -> bytes:
    """The exact bytes of an edit file: canonical JSON, so a document has one hash."""
    return canonical_json(document)


def arm_of(data: bytes) -> str:
    return EDIT_ARM_PREFIX + sha256_bytes(data)


@dataclass(frozen=True)
class Edit:
    sha256: str
    raw: bytes
    document: dict
    removed: frozenset[str]
    rewrite: dict[str, str]                          # row id -> replacement response
    added: tuple[tuple[str, str, str], ...]          # (row id, prompt, response), sorted by id

    @property
    def arm(self) -> str:
        return EDIT_ARM_PREFIX + self.sha256

    @property
    def added_ids(self) -> tuple[str, ...]:
        return tuple(row_id for row_id, _, _ in self.added)

    def summary(self) -> dict:
        return {"edit_sha256": self.sha256, "edit_kind": self.document["edit_kind"], "name": self.document["name"],
                "removed": len(self.removed), "rewritten": len(self.rewrite), "added": len(self.added)}


def _texts(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EditError(f"{where}: expected non-empty text")
    return value


def parse_edit(data: bytes, prepared: Any) -> Edit:
    """Check an edit file's content against the prepared data (module doc)."""
    try:
        import json

        doc = json.loads(data)
    except ValueError:
        raise EditError("the edit file is not JSON") from None
    if not isinstance(doc, dict) or set(doc) != _KEYS:
        raise EditError(f"the edit file must have exactly the keys {sorted(_KEYS)}")
    if doc["kind"] != EDIT_KIND or doc["version"] != EDIT_VERSION:
        raise EditError(f"not a {EDIT_KIND} of version {EDIT_VERSION}")
    if doc["edit_kind"] not in EDIT_KINDS:
        raise EditError(f"edit_kind must be one of {EDIT_KINDS}")
    _texts(doc["name"], "name")
    if doc["manifest_sha256"] != prepared.manifest_sha256:
        raise EditError("the edit was written for another prepared dataset (manifest_sha256)")
    if doc["position_rule"] != POSITION_RULE:
        raise EditError("the edit states another position rule than the one the engine implements")
    if not isinstance(doc["provenance"], dict):
        raise EditError("provenance must be an object (the hashes of the edit's inputs)")
    remove, rewrite, add = doc["remove"], doc["rewrite"], doc["add"]
    if not (isinstance(remove, list) and all(isinstance(r, str) for r in remove)):
        raise EditError("remove must be a list of row ids")
    if remove != sorted(set(remove)):
        raise EditError("remove must list distinct row ids in sorted order")
    if not (isinstance(rewrite, list) and all(isinstance(r, dict) and set(r) == {"row_id", "response"} for r in rewrite)):
        raise EditError("rewrite must be a list of {row_id, response}")
    if [r["row_id"] for r in rewrite] != sorted({r["row_id"] for r in rewrite}):
        raise EditError("rewrite must list distinct row ids in sorted order")
    if not (isinstance(add, list) and all(isinstance(r, dict) and set(r) == {"row_id", "prompt", "response"} for r in add)):
        raise EditError("add must be a list of {row_id, prompt, response}")
    if [r["row_id"] for r in add] != sorted({r["row_id"] for r in add}):
        raise EditError("add must list distinct row ids in sorted order")
    counts = doc["counts"]
    if counts != {"remove": len(remove), "rewrite": len(rewrite), "add": len(add)}:
        raise EditError("counts do not match the lists")
    present = [name for name, items in (("remove", remove), ("rewrite", rewrite), ("add", add)) if items]
    expected = {"remove": ["remove"], "rewrite": ["rewrite"], "add": ["add"]}.get(doc["edit_kind"])
    if expected is not None and present != expected:
        raise EditError(f"an edit of kind {doc['edit_kind']} holds exactly that list, non-empty (it holds {present})")
    if doc["edit_kind"] == "combined" and len(present) < 2:
        raise EditError("a combined edit holds at least two of remove, rewrite and add")
    training, heldout = set(prepared.train_rows), heldout_members(prepared)
    touched = list(remove) + [r["row_id"] for r in rewrite]
    unknown = sorted(set(touched) - training)
    if unknown:
        raise EditError(f"{len(unknown)} named rows are not training rows (first: {unknown[0]})")
    forbidden = sorted(set(touched) & heldout)
    if forbidden:
        raise EditError(f"{len(forbidden)} named rows are members of held-out groups: the edit pool excludes "
                        "them (refused; nothing was trained)")
    if set(remove) & {r["row_id"] for r in rewrite}:
        raise EditError("a row cannot be both removed and rewritten")
    for item in rewrite:
        _texts(item["response"], f"rewrite {item['row_id']}.response")
    for item in add:
        if not item["row_id"].startswith(ADD_PREFIX) or item["row_id"] in training:
            raise EditError(f"added row {item['row_id']!r} must be named {ADD_PREFIX}... and must not be a training row")
        _texts(item["prompt"], f"add {item['row_id']}.prompt")
        _texts(item["response"], f"add {item['row_id']}.response")
    if not (remove or rewrite or add):
        raise EditError("an edit that changes nothing is a0, not an edit")
    return Edit(sha256=sha256_bytes(data), raw=data, document=doc, removed=frozenset(remove),
                rewrite={r["row_id"]: r["response"] for r in rewrite},
                added=tuple((r["row_id"], r["prompt"], r["response"]) for r in add))


def load_edit(path: str | Path, arm: str, prepared: Any) -> Edit:
    """The edit file a job names, refused unless its bytes hash to the arm."""
    if not is_edit_arm(arm):
        raise EditError(f"{arm!r} is not an edit arm")
    data = Path(path).read_bytes()
    if arm_of(data) != arm:
        raise EditError(f"{path} does not hash to the arm {arm}: the file changed, or it is another edit")
    return parse_edit(data, prepared)


def edited_corpus(corpus: dict[str, TrainExample], edit: Edit, prepared: Any, codec: Any,
                  max_tokens: int) -> dict[str, TrainExample]:
    """The training examples an edit arm trains on: the verified corpus with each rewritten row
    re-encoded (same prompt, the replacement response) and each added row encoded. The corpus
    passed in is not changed. Removed rows stay in the mapping; the stream never draws them."""
    out = dict(corpus)
    for row_id, response in sorted(edit.rewrite.items()):
        original = corpus[row_id]
        example = encode_train(codec, row_id, prepared.train_rows[row_id]["prompt"], response, max_tokens)
        if example.input_ids[:example.n_prompt] != original.input_ids[:original.n_prompt]:
            raise EditError(f"{row_id}: the rewritten row's prompt tokens differ from its audited prompt tokens")
        out[row_id] = example
    for row_id, prompt, response in edit.added:
        out[row_id] = encode_train(codec, row_id, prompt, response, max_tokens)
    return out
