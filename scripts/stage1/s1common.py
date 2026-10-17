"""Stage-1 shared seed, selection and record helpers (REQ-2; standard library only).

This is the only module under ``scripts/stage1`` that draws random numbers. A draw is named by a
KEY of the seed-label registry ``labels.json``, never by a label string:
``seed = derive_seed(20261008, label, *parts)``, with the engine's own ``derive_seed``. A key with
the wrong number of parts, an unknown key and a frozen Gate B label refuse.

Shared rules (one implementation for every stage-1 builder and writer):

- ``sealed_order`` / ``sealed_rank``: ``random.Random(seed).shuffle(sorted(ids))``; the rank of an id
  is its position in that order.
- ``sealed_sample``: ``random.Random(seed).sample(sorted(ids), n)`` (the form of Gate B's R rule).
- ``select_top``: sort by (score descending, sealed rank) and take k. NaN, infinity, a bool, a
  missing or an extra id, and k outside 1..n refuse. To take the smallest scores, the caller
  negates them; the orientation is never implicit.
- ``PreparedView``: what a writer reads of the prepared set without text (row ids, target tokens,
  unit membership, categories), as the sealed Gate B build reads it.
- ``edit_document`` / ``checked_edit``: edit files in the engine's own format, parsed back with the
  engine's own ``parse_edit`` before anything is written.
- ``sealed_record``: a text-free record of text-bearing items (ids, SHA-256 of each text field,
  allowed scalar fields, counts by reason, the full file's SHA-256 and byte length). Its bytes are
  scanned for every text value before it is returned.
- ``check_settings`` / ``load_settings``: a settings file names the registry entries it uses
  (``label_entries``: key -> SHA-256 of canonical_json({key: entry})); it refuses only when one of THOSE
  entries is missing or changed, so an append to labels.json never breaks a frozen settings file.
  ``labels_sha256`` stays in each file as the record of the registry it was written on.
- ``provenance``: the script's, this module's and the settings' SHA-256, the used entries' digests (never
  the whole registry's hash, so an append never changes an output's bytes), every input's SHA-256, the
  engine identity and the Python and numpy versions.
- ``report_stats``, ``jaccard_matrix``, ``write_new_files``.

Messages carry ids, counts and hashes only, never row, prompt, answer, anchor or lexicon text.
This file is frozen at the T1 commit; later shared needs go into a new module.
"""

from __future__ import annotations

import importlib.metadata
import json
import math
import platform
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable, Iterator, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import (canonical_json, code_identity, derive_seed,  # noqa: E402
                                                 sha256_bytes, sha256_file, write_atomic)
from experiments.safety_selection.edits import (EDIT_KIND, EDIT_VERSION, POSITION_RULE, Edit,  # noqa: E402
                                                arm_of, edit_bytes, parse_edit)

__all__ = ["Refusal", "DESIGN_SEED", "LABELS_PATH", "Label", "strict_json", "iter_jsonl", "iter_jsonl_bytes",
           "load_registry", "registry", "label", "labels_sha256", "entry_digest", "seed", "sealed_order", "sealed_rank", "sealed_sample",
           "numpy_generator", "check_scores", "select_top", "boundary_ties", "PreparedView", "EngineStub",
           "edit_document", "checked_edit", "sealed_record", "report_stats", "jaccard_matrix", "rel",
           "provenance", "check_settings", "load_settings", "write_new_files"]

DESIGN_SEED = 20261008
LABELS_PATH = HERE / "labels.json"
LABEL_PATTERN = re.compile(r"^stage1-[a-z0-9]+(-[a-z0-9]+)*-v[1-9][0-9]*$")
KEY_PATTERN = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
OWNER_PATTERN = re.compile(r"^scripts/stage1/[a-z0-9_]+(/[a-z0-9_]+)*\.py$")
PART_PATTERN = re.compile(r"^[A-Za-z0-9_.:+\-]{1,160}$")
SAFE_VALUE = re.compile(r"^[A-Za-z0-9_.:+/\-]{1,160}$")
ENTRY_KEYS = frozenset({"base_seed", "id_domain", "label", "named_in", "owner", "parts", "use"})
REGISTRY_KEYS = frozenset({"base_seed", "frozen_reused", "kind", "labels", "pattern", "rule", "version"})
REGISTRY_KIND = "stage1 seed-label registry"
SETTINGS_KIND = "stage1 settings"
TRAIN_ROWS = "engine/train_rows.jsonl"
GROUPS = "engine/groups.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Refusal(Exception):
    """A check failed; nothing is written. The message holds ids, counts and hashes only."""


# ----- strict JSON -----------------------------------------------------------------------------------


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise Refusal(f"a JSON object repeats the key {key!r}")
        out[key] = value
    return out


def _no_constant(name: str) -> Any:
    raise Refusal(f"a JSON value is {name} (NaN and infinity are refused)")


def _finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise Refusal("a JSON number overflows to infinity (refused)")
    return value


def strict_json(data: bytes | str) -> Any:
    """JSON with no repeated key in any object and no NaN or infinity (also not an overflowing literal such
    as 1e999)."""
    try:
        return json.loads(data, object_pairs_hook=_no_duplicates, parse_constant=_no_constant,
                          parse_float=_finite_float)
    except ValueError:
        raise Refusal("the bytes are not valid JSON") from None


def iter_jsonl_bytes(data: bytes, name: str) -> Iterator[dict]:
    """Each line of JSONL bytes as a strict JSON object; a blank or invalid line refuses (by line number)."""
    for number, line in enumerate(data.splitlines(), 1):
        if not line.strip():
            raise Refusal(f"{name}: line {number} is blank")
        try:
            value = strict_json(line)
        except Refusal:
            raise Refusal(f"{name}: line {number} is not one strict JSON value") from None
        if not isinstance(value, dict):
            raise Refusal(f"{name}: line {number} is not a JSON object")
        yield value


def iter_jsonl(path: str | Path) -> Iterator[dict]:
    """iter_jsonl_bytes over a file's bytes."""
    return iter_jsonl_bytes(Path(path).read_bytes(), Path(path).name)


# ----- the seed-label registry ------------------------------------------------------------------------


@dataclass(frozen=True)
class Label:
    key: str
    label: str
    parts: tuple[str, ...]
    owner: str
    frozen: bool
    digest: str                 # SHA-256 of canonical_json({key: entry}): what a settings file pins


def load_registry(path: str | Path = LABELS_PATH) -> dict[str, Label]:
    """The checked registry: keys and labels unique, every stage-1 label in the pattern, no '|'."""
    doc = strict_json(Path(path).read_bytes())
    if not isinstance(doc, dict) or set(doc) != REGISTRY_KEYS:
        raise Refusal("labels.json does not hold exactly the registry keys")
    if doc["kind"] != REGISTRY_KIND or doc["version"] != 1 or doc["base_seed"] != DESIGN_SEED:
        raise Refusal("labels.json is not a version-1 stage-1 registry on base seed 20261008")
    if doc["pattern"] != LABEL_PATTERN.pattern:
        raise Refusal("labels.json states another label pattern than the code checks")
    out: dict[str, Label] = {}
    seen: set[str] = set()
    for section, frozen in (("labels", False), ("frozen_reused", True)):
        entries = doc[section]
        if not isinstance(entries, dict) or not entries:
            raise Refusal(f"labels.json section {section} is not a non-empty object")
        for key, entry in entries.items():
            if not KEY_PATTERN.match(key) or key in out:
                raise Refusal(f"registry key {key!r} is malformed or repeated")
            if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
                raise Refusal(f"registry entry {key} does not hold exactly {sorted(ENTRY_KEYS)}")
            name, parts = entry["label"], entry["parts"]
            if entry["base_seed"] != DESIGN_SEED:
                raise Refusal(f"registry entry {key} is not on base seed {DESIGN_SEED}")
            if not isinstance(name, str) or "|" in name or name in seen:
                raise Refusal(f"registry entry {key}: the label is not a distinct string without '|'")
            if not frozen and not LABEL_PATTERN.match(name):
                raise Refusal(f"registry entry {key}: the label is not in the stage-1 pattern")
            if frozen and LABEL_PATTERN.match(name):
                raise Refusal(f"registry entry {key}: a frozen reused label cannot be a stage-1 label")
            if not (isinstance(parts, list) and all(isinstance(p, str) and p for p in parts)
                    and len(set(parts)) == len(parts)):
                raise Refusal(f"registry entry {key}: parts must be distinct non-empty names")
            if not isinstance(entry["owner"], str) or not OWNER_PATTERN.match(entry["owner"]):
                raise Refusal(f"registry entry {key}: the owner is not one scripts/stage1 Python file")
            for field in ("id_domain", "named_in", "use"):
                if not isinstance(entry[field], str) or not entry[field].strip():
                    raise Refusal(f"registry entry {key}: {field} is empty")
            seen.add(name)
            out[key] = Label(key, name, tuple(parts), entry["owner"], frozen,
                             sha256_bytes(canonical_json({key: entry})))
    return out


_REGISTRY: dict[str, Label] | None = None


def registry() -> dict[str, Label]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = load_registry(LABELS_PATH)
    return _REGISTRY


def label(key: str) -> Label:
    """The registry entry of a key; an unknown key raises KeyError."""
    return registry()[key]


def labels_sha256() -> str:
    """The whole registry file's SHA-256 (a record only; nothing refuses on it)."""
    return sha256_file(LABELS_PATH)


def entry_digest(key: str) -> str:
    """SHA-256 of canonical_json({key: entry}) of one registry entry; an unknown key raises KeyError."""
    return label(key).digest


def seed(key: str, *parts: object) -> int:
    """derive_seed(20261008, label, *parts) for a stage-1 key; a part is an int or a short id string."""
    entry = label(key)
    if entry.frozen:
        raise Refusal(f"key {key} is a frozen Gate B label: only its frozen builder draws with it")
    if len(parts) != len(entry.parts):
        raise Refusal(f"key {key} takes the parts {list(entry.parts)}; {len(parts)} were given")
    for part in parts:
        ok = (isinstance(part, int) and not isinstance(part, bool)) or (
            isinstance(part, str) and PART_PATTERN.match(part) is not None)
        if not ok:
            raise Refusal(f"key {key}: a part is not an int or a short id string")
    return derive_seed(DESIGN_SEED, entry.label, *parts)


# ----- draws -----------------------------------------------------------------------------------------


def _sorted_ids(ids: Iterable[str], what: str) -> list[str]:
    items = list(ids)
    if not all(isinstance(i, str) for i in items):
        raise Refusal(f"{what}: every id must be a string")
    out = sorted(set(items))
    if len(out) != len(items):
        raise Refusal(f"{what}: {len(items) - len(out)} repeated ids")
    return out


def sealed_order(ids: Iterable[str], key: str, *parts: object) -> list[str]:
    """random.Random(seed(key, *parts)).shuffle(sorted(ids))."""
    out = _sorted_ids(ids, f"sealed order {key}")
    random.Random(seed(key, *parts)).shuffle(out)
    return out


def sealed_rank(ids: Iterable[str], key: str, *parts: object) -> dict[str, int]:
    """The position of each id in sealed_order."""
    return {row: position for position, row in enumerate(sealed_order(ids, key, *parts))}


def sealed_sample(ids: Iterable[str], n: int, key: str, *parts: object) -> list[str]:
    """random.Random(seed(key, *parts)).sample(sorted(ids), n), in draw order (Gate B's R rule form)."""
    pool = _sorted_ids(ids, f"sealed sample {key}")
    if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= len(pool):
        raise Refusal(f"sealed sample {key}: n = {n!r} is outside 0..{len(pool)}")
    return random.Random(seed(key, *parts)).sample(pool, n)


def numpy_generator(key: str, *parts: object) -> Any:
    """numpy.random.default_rng(seed(key, *parts)) (numpy is imported only here, only when asked)."""
    import numpy

    return numpy.random.default_rng(seed(key, *parts))


# ----- selection -------------------------------------------------------------------------------------


def check_scores(scores: Mapping[str, Any], expected_ids: Iterable[str] | None = None) -> dict[str, float]:
    """Finite real scores for distinct string ids (a bool, NaN or infinity refuses); with expected_ids,
    the ids must be exactly those."""
    if not isinstance(scores, Mapping) or not scores:
        raise Refusal("the scores are not a non-empty mapping")
    out: dict[str, float] = {}
    bad = 0
    for row, value in scores.items():
        if not isinstance(row, str):
            raise Refusal("a scored id is not a string")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            bad += 1
            continue
        out[row] = float(value)
    if bad:
        raise Refusal(f"{bad} scores are not finite real numbers (NaN, infinity, a bool or not a number)")
    if expected_ids is not None:
        expected = set(expected_ids)
        missing, extra = len(expected - set(out)), len(set(out) - expected)
        if missing or extra:
            raise Refusal(f"the scored ids are not the expected ids ({missing} missing, {extra} extra)")
    return out


def select_top(scores: Mapping[str, Any], k: int, key: str, *parts: object,
               expected_ids: Iterable[str] | None = None) -> list[str]:
    """The k ids with the largest scores, in selection order; ties by the sealed rank of key."""
    checked = check_scores(scores, expected_ids)
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= len(checked):
        raise Refusal(f"k = {k!r} is outside 1..{len(checked)}")
    rank = sealed_rank(checked, key, *parts)
    return sorted(checked, key=lambda row: (-checked[row], rank[row]))[:k]


def boundary_ties(scores: Mapping[str, float], selected: Sequence[str]) -> dict:
    """How many ids share the k-th selected score, inside and outside the selection."""
    kth = scores[selected[-1]]
    inside = set(selected)
    tied = [row for row, value in scores.items() if value == kth]
    return {"kth_score": kth, "tied_selected": sum(r in inside for r in tied),
            "tied_not_selected": sum(r not in inside for r in tied)}


# ----- the prepared set without text -----------------------------------------------------------------


class PreparedView:
    """Row ids, target tokens, unit membership and categories of a prepared set. The manifest must hash to
    the pinned value and the two files read must hash to the manifest's values. Of each training row only
    row_id and target_tokens are kept; the text fields are dropped at once. Nothing else is opened."""

    def __init__(self, root: str | Path, manifest_sha256: str):
        root = Path(root)
        manifest_bytes = (root / "manifest.json").read_bytes()
        self.manifest_sha256 = sha256_bytes(manifest_bytes)
        if self.manifest_sha256 != manifest_sha256:
            raise Refusal(f"the prepared manifest hashes to {self.manifest_sha256}, expected {manifest_sha256}")
        manifest = strict_json(manifest_bytes)
        self.file_sha256: dict[str, str] = {}
        for name in (TRAIN_ROWS, GROUPS):
            digest = sha256_file(root / name)
            if digest != manifest["files"].get(name):
                raise Refusal(f"{name} hashes to {digest}, the manifest names another file")
            self.file_sha256[name] = digest
        self.tokens: dict[str, int] = {}
        for row in iter_jsonl(root / TRAIN_ROWS):
            row_id, tokens = row.get("row_id"), row.get("target_tokens")
            row.clear()
            if not isinstance(row_id, str) or row_id in self.tokens:
                raise Refusal("the training row ids are not distinct strings")
            if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 1:
                raise Refusal(f"row {row_id} has no positive integer target_tokens")
            self.tokens[row_id] = tokens
        if len(self.tokens) != manifest["corpus"]["rows"]:
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
            rows = self.members[gid]
            if len(set(rows)) != len(rows) or seen & set(rows):
                raise Refusal(f"unit {gid} does not hold distinct rows of its own")
            seen |= set(rows)
        if seen != set(self.tokens):
            raise Refusal("the units do not partition the training rows")
        self.unit_of = {row: gid for gid in self.units for row in self.members[gid]}

    def check_shape(self, rows: int, units: int, rows_per_unit: int) -> None:
        if (len(self.tokens), len(self.units)) != (rows, units) or any(
                len(self.members[g]) != rows_per_unit for g in self.units):
            raise Refusal(f"the prepared set is not {units} units of {rows_per_unit} rows ({rows} rows)")

    def engine_stub(self) -> "EngineStub":
        return EngineStub(self.manifest_sha256, dict.fromkeys(self.tokens), {"dev": dict(self.members), "heldout": {}})


@dataclass(frozen=True)
class EngineStub:
    """What the engine's parse_edit reads of a prepared set (the pattern of the sealed Gate B build)."""
    manifest_sha256: str
    train_rows: dict
    groups: dict


# ----- edit files ------------------------------------------------------------------------------------


def edit_document(*, name: str, edit_kind: str, manifest_sha256: str, provenance: dict,
                  remove: Iterable[str] = (), rewrite: Mapping[str, str] | None = None,
                  add: Iterable[tuple[str, str, str]] = ()) -> dict:
    """An edit document in the engine's format: sorted lists, counts, the engine's position rule."""
    remove = sorted(remove)
    rewrite_items = [{"row_id": r, "response": text} for r, text in sorted((rewrite or {}).items())]
    add_items = [{"row_id": r, "prompt": p, "response": t} for r, p, t in sorted(add)]
    return {"kind": EDIT_KIND, "version": EDIT_VERSION, "name": name, "edit_kind": edit_kind,
            "manifest_sha256": manifest_sha256, "remove": remove, "rewrite": rewrite_items, "add": add_items,
            "position_rule": POSITION_RULE,
            "counts": {"remove": len(remove), "rewrite": len(rewrite_items), "add": len(add_items)},
            "provenance": provenance}


def checked_edit(document: dict, stub: Any) -> tuple[bytes, Edit]:
    """The edit file's bytes, parsed back with the engine's own parse_edit; any difference refuses."""
    data = edit_bytes(document)
    try:
        edit = parse_edit(data, stub)
    except Exception as exc:                                    # the engine's EditError, by type name only
        raise Refusal(f"the engine refuses the edit {document.get('name')!r} ({type(exc).__name__})") from None
    if edit.document != document or edit.arm != arm_of(data):
        raise Refusal(f"the engine reads the edit {document.get('name')!r} differently from what was written")
    return data, edit


# ----- text-free records -----------------------------------------------------------------------------


def _text_hits(data: bytes, texts: Iterable[str], min_chars: int = 6) -> int:
    """How many text values of at least min_chars characters appear in data, raw or JSON-escaped."""
    hits = 0
    for text in texts:
        if len(text) < min_chars:
            continue
        forms = {text.encode("utf-8"), json.dumps(text, ensure_ascii=False)[1:-1].encode("utf-8"),
                 json.dumps(text, ensure_ascii=True)[1:-1].encode("ascii")}
        hits += any(form in data for form in forms)
    return hits


def sealed_record(kind: str, full_file: bytes, items: Sequence[Mapping[str, Any]], *,
                  text_fields: Sequence[str], keep_fields: Sequence[str]) -> dict:
    """A text-free record of text-bearing items. Each text field becomes <field>_sha256; each kept field
    must be None, a bool, an int, a finite float or a short id string; any other field refuses. The record's
    canonical bytes are scanned for every text value (6 characters or more) before it is returned."""
    text_fields, keep_fields = tuple(text_fields), tuple(keep_fields)
    if set(text_fields) & set(keep_fields):
        raise Refusal("a field cannot be both a text field and a kept field")
    out_items, texts = [], []
    for position, item in enumerate(items):
        unknown = set(item) - set(text_fields) - set(keep_fields)
        if unknown:
            raise Refusal(f"item {position} holds {len(unknown)} fields that are neither text nor kept")
        record: dict[str, Any] = {}
        for field in keep_fields:
            if field not in item:
                continue
            value = item[field]
            ok = value is None or isinstance(value, (bool, int)) or (
                isinstance(value, float) and math.isfinite(value)) or (
                isinstance(value, str) and SAFE_VALUE.match(value) is not None)
            if not ok:
                raise Refusal(f"item {position}: kept field {field} is not a scalar or a short id string")
            record[field] = value
        for field in text_fields:
            if field not in item:
                continue
            value = item[field]
            if not isinstance(value, str):
                raise Refusal(f"item {position}: text field {field} is not a string")
            record[f"{field}_sha256"] = sha256_bytes(value.encode("utf-8"))
            texts.append(value)
        out_items.append(record)
    doc = {"kind": kind, "version": 1,
           "full_file": {"sha256": sha256_bytes(full_file), "bytes": len(full_file)},
           "n_items": len(out_items), "items": out_items}
    if "reason" in keep_fields:
        doc["counts_by_reason"] = dict(sorted(Counter(str(i.get("reason")) for i in items).items()))
    if _text_hits(canonical_json(doc), texts):
        raise Refusal("the record would hold item text")
    return doc


# ----- statistics ------------------------------------------------------------------------------------


def report_stats(view: PreparedView, *, removed: Iterable[str] = (), rewritten: Iterable[str] = (),
                 added_tokens: Mapping[str, int] | None = None, flag_share: float = 0.5) -> dict:
    """Removed, rewritten and added rows: counts, token mass (target tokens), counts per unit and per
    category, and the one-category flag (at least flag_share of the removed rows in one category)."""
    removed, rewritten = list(removed), list(rewritten)
    for name, rows in (("removed", removed), ("rewritten", rewritten)):
        if len(set(rows)) != len(rows) or not set(rows) <= set(view.tokens):
            raise Refusal(f"the {name} rows are not distinct training rows")
    if set(removed) & set(rewritten):
        raise Refusal("a row is both removed and rewritten")

    def per(rows: list[str]) -> tuple[dict, dict]:
        by_unit = {g: 0 for g in view.units}
        for row in rows:
            by_unit[view.unit_of[row]] += 1
        by_category: Counter = Counter({view.category[g]: 0 for g in view.units})
        for g, n in by_unit.items():                       # summed: two units may share a category
            by_category[view.category[g]] += n
        return by_unit, dict(sorted(by_category.items()))

    out: dict[str, Any] = {"training_rows": len(view.tokens),
                           "training_token_mass": sum(view.tokens.values())}
    if removed:
        by_unit, by_category = per(removed)
        units_of = {c: sorted(g for g in view.units if view.category[g] == c) for c in by_category}
        top = max(by_category, key=lambda c: (by_category[c], c))
        share = by_category[top] / len(removed)
        out["removed"] = {"rows": len(removed), "token_mass": sum(view.tokens[r] for r in removed),
                          "mean_target_tokens": fmean(view.tokens[r] for r in removed),
                          "by_unit": by_unit, "by_category": by_category,
                          "largest_category": {"category": top, "units": units_of[top], "share": share,
                                               "flag_share": flag_share, "flag": share >= flag_share},
                          "flagged_categories": [{"category": c, "units": units_of[c], "share": by_category[c] / len(removed)}
                                                 for c in sorted(by_category)
                                                 if by_category[c] / len(removed) >= flag_share]}
        out["kept_rows"] = len(view.tokens) - len(removed)
    if rewritten:
        by_unit, by_category = per(rewritten)
        out["rewritten"] = {"rows": len(rewritten), "token_mass_before": sum(view.tokens[r] for r in rewritten),
                            "by_unit": by_unit, "by_category": by_category}
    if added_tokens:
        values = list(added_tokens.values())
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in values):
            raise Refusal("an added row has no positive integer token count")
        out["added"] = {"rows": len(values), "token_mass": sum(values)}
    out["mean_target_tokens_all"] = fmean(view.tokens.values())
    return out


def jaccard_matrix(named_sets: Mapping[str, Iterable[str]]) -> dict:
    """Pairwise Jaccard |A ∩ B| / |A ∪ B| of named non-empty id sets, with sizes and intersections."""
    sets = {name: set(ids) for name, ids in named_sets.items()}
    if not sets or any(not s for s in sets.values()):
        raise Refusal("every named set must be non-empty")
    names = sorted(sets)
    return {"names": names, "sizes": {n: len(sets[n]) for n in names},
            "intersection": {a: {b: len(sets[a] & sets[b]) for b in names} for a in names},
            "jaccard": {a: {b: len(sets[a] & sets[b]) / len(sets[a] | sets[b]) for b in names} for a in names}}


# ----- provenance, settings and writing --------------------------------------------------------------


def rel(path: str | Path) -> str:
    """A path relative to the repository root when it lies inside it, else the absolute path."""
    path = Path(path).resolve()
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def _numpy_version() -> str | None:
    try:
        return importlib.metadata.version("numpy")
    except importlib.metadata.PackageNotFoundError:
        return None


def provenance(script: str | Path, settings_sha256: str, inputs: Mapping[str, str],
               label_entries: Mapping[str, str]) -> dict:
    """The block every stage-1 output carries: the script's, this module's and the settings' SHA-256, the
    digests of the registry entries the settings use (not the whole registry's hash, so an append to
    labels.json never changes an output), every input's SHA-256, the engine identity and the Python and
    numpy versions."""
    for name, digest in list(inputs.items()) + list(label_entries.items()):
        if not isinstance(digest, str) or not HEX64.match(digest):
            raise Refusal(f"{name} is not named by a SHA-256")
    return {"script": rel(script), "script_sha256": sha256_file(script),
            "s1common_sha256": sha256_file(Path(__file__).resolve()),
            "label_entries": dict(sorted(label_entries.items())),
            "settings_sha256": settings_sha256, "inputs": dict(sorted(inputs.items())),
            "engine_identity_sha256": code_identity()["sha256"],
            "python": platform.python_version(), "numpy": _numpy_version()}


def check_settings(doc: Any, name: str) -> dict:
    """A parsed settings document of this name, whose named registry entries are unchanged (an appended
    entry never refuses), on this engine identity."""
    if not isinstance(doc, dict) or doc.get("kind") != SETTINGS_KIND or doc.get("name") != name:
        raise Refusal(f"not the stage-1 settings {name!r}")
    record = doc.get("labels_sha256")
    if not isinstance(record, str) or not HEX64.match(record):
        raise Refusal(f"settings {name}: no SHA-256 record of the registry it was written on")
    entries = doc.get("label_entries")
    if not isinstance(entries, dict) or not all(isinstance(v, str) and HEX64.match(v) for v in entries.values()):
        raise Refusal(f"settings {name}: label_entries is not an object of SHA-256 digests")
    reg = registry()
    changed = sorted(key for key, digest in entries.items() if key not in reg or reg[key].digest != digest)
    if changed:
        raise Refusal(f"settings {name}: {len(changed)} registry entries it names are missing or changed "
                      f"(first: {changed[0]})")
    identity = code_identity()["sha256"]
    if doc.get("engine_x") != identity:
        raise Refusal(f"settings {name}: written for engine {doc.get('engine_x')}, this engine is {identity}")
    return doc


def load_settings(path: str | Path, expected_sha256: str, name: str) -> tuple[dict, str]:
    """The settings file, refused unless its bytes hash to expected_sha256 (then check_settings)."""
    data = Path(path).read_bytes()
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise Refusal(f"settings {name} hash to {digest}, expected {expected_sha256}")
    return check_settings(strict_json(data), name), digest


def write_new_files(out_dir: str | Path, files: Mapping[str, bytes]) -> dict[str, str]:
    """Write every file into an absent or empty folder, then read each back; returns name -> SHA-256."""
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise Refusal(f"{out} exists and is not empty: a sealed output never overwrites")
    out.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        write_atomic(out / name, data)
    digests = {}
    for name, data in files.items():
        digests[name] = sha256_file(out / name)
        if digests[name] != sha256_bytes(data):
            raise Refusal(f"{name} did not read back as written")
    return digests
