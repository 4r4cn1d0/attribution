"""The selector-input view (stdlib only): the ONLY engine output a stage-B predictor or selector
should receive.

Why a view. The prepared manifest (and ``Prepared``) is engine scope: its data config holds the
design seed and the composition table, and replaying the seeded construction from them (with
the public sources) recovers every opaque group's hidden composition. Engine and auditor code
may read it; prediction must not. ``export_selector_view`` (engine side) reads the
hash-verified prepared files and a complete ``score-groups`` run of the same data and writes a
fixed whitelist per group of one split: the static metadata of ``selector/x0_static.json``
(size, tie rank, coarse provenance counts, character and token summaries) and the measured
guard features (hard-label counts and label-sequence score summaries); plus the split's menu.
Anything not whitelisted is dropped. Its receipt (manifest hash, source file hashes, guard run
and identities) is a separate engine/auditor file, never a selector input. ``read_selector_view``
(selector side) refuses unknown or missing keys at every level, non-canonical bytes (duplicate
keys, NaN or infinity), inconsistent sizes or menus, and a hash other than the expected one;
it returns a read-only ``SelectorView``. The view's bytes do not change when hidden type labels
and ``data_id`` values are renamed (tested).

Limits. This is an experimental information boundary, not filesystem security: a process with
file access can open anything, and stage B enforces its own feature matrix separately. Coarse
provenance (ToxicChat versus UltraChat) and size are allowed metadata by design; together with
the published composition table they identify the mixed and benign-only families and leave the
pure groups as unsafe-versus-aligned pairs. That is a property of the frozen design, shared by
both compared selectors, not a leak through this view.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .common import canonical_json, read_json, sha256_bytes, sha256_file, write_atomic
from .config import PARTITIONS
from .ledger import COMPLETE, read_complete, verify_files
from .prepare import GROUPS, X0_STATIC, read_manifest, read_verified

__all__ = ["VIEW_KIND", "SelectorViewError", "SelectorView", "validate_view", "build_selector_view",
           "export_selector_view", "read_selector_view"]

VIEW_KIND = "safety-selection selector view"
RECEIPT_KIND = "selector view receipt (engine/auditor side; never a selector input)"
STATIC_KEYS = ("size", "tie_rank", "provenance", "chars", "response_chars", "tokens", "target_tokens")
SUMMARY_KEYS = ("sum", "mean", "min", "max")
GUARD_KEYS = ("size", "guard_invalid", "guard_unsafe", "guard_controversial", "guard_safe",
              "guard_refusal_yes", "guard_refusal_no", "label_scores")
LABEL_KEYS = ("safe", "unsafe", "controversial")
LABEL_SUMMARY_KEYS = ("sum", "mean", "max")


class SelectorViewError(ValueError):
    pass


@dataclass(frozen=True)
class SelectorView:
    """Read-only selector input: one split's menu and whitelisted per-group features."""

    split: str
    menu: tuple[str, ...]
    groups: Mapping[str, Mapping[str, Any]]
    sha256: str


def _exact(obj: object, keys: tuple[str, ...], where: str) -> dict:
    if not isinstance(obj, dict):
        raise SelectorViewError(f"{where}: expected an object")
    if set(obj) != set(keys):
        raise SelectorViewError(f"{where}: missing {sorted(set(keys) - set(obj))}, "
                                f"unknown {sorted(set(obj) - set(keys))}")
    return obj


def _count(value: object, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SelectorViewError(f"{where}: expected a non-negative integer")
    return value


def _number(value: object, where: str, allow_null: bool = False) -> float | None:
    if value is None and allow_null:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SelectorViewError(f"{where}: expected a finite number")
    return float(value)


def _validate_static(entry: object, where: str) -> int:
    entry = _exact(entry, STATIC_KEYS, where)
    size = _count(entry["size"], f"{where}.size")
    _count(entry["tie_rank"], f"{where}.tie_rank")
    provenance = entry["provenance"]
    if not (isinstance(provenance, dict) and provenance and all(isinstance(k, str) and k for k in provenance)):
        raise SelectorViewError(f"{where}.provenance: expected source names with counts")
    if sum(_count(v, f"{where}.provenance") for v in provenance.values()) != size:
        raise SelectorViewError(f"{where}.provenance: counts must sum to size")
    for key in ("chars", "response_chars", "tokens", "target_tokens"):
        summary = _exact(entry[key], SUMMARY_KEYS, f"{where}.{key}")
        for stat in SUMMARY_KEYS:
            _number(summary[stat], f"{where}.{key}.{stat}")
    return size


def _validate_guard(entry: object, where: str) -> int:
    entry = _exact(entry, GUARD_KEYS, where)
    size = _count(entry["size"], f"{where}.size")
    hard = [_count(entry[k], f"{where}.{k}") for k in ("guard_invalid", "guard_unsafe",
                                                        "guard_controversial", "guard_safe")]
    if sum(hard) != size:
        raise SelectorViewError(f"{where}: hard-label counts must sum to size")
    refusal = _count(entry["guard_refusal_yes"], where) + _count(entry["guard_refusal_no"], where)
    if refusal != size - hard[0]:
        raise SelectorViewError(f"{where}: refusal counts must cover the valid hard labels")
    scores = _exact(entry["label_scores"], ("scored", "unscored", *LABEL_KEYS), f"{where}.label_scores")
    scored = _count(scores["scored"], f"{where}.label_scores.scored")
    if scored + _count(scores["unscored"], f"{where}.label_scores.unscored") != size:
        raise SelectorViewError(f"{where}.label_scores: scored and unscored must sum to size")
    for label in LABEL_KEYS:
        summary = _exact(scores[label], LABEL_SUMMARY_KEYS, f"{where}.label_scores.{label}")
        _number(summary["sum"], f"{where}.label_scores.{label}.sum")
        for stat in ("mean", "max"):
            value = _number(summary[stat], f"{where}.label_scores.{label}.{stat}", allow_null=True)
            if (value is None) != (scored == 0):
                raise SelectorViewError(f"{where}.label_scores.{label}.{stat}: null exactly when no row is scored")
    return size


def validate_view(view: object) -> dict:
    """Raise SelectorViewError unless ``view`` is exactly the whitelisted schema."""
    view = _exact(view, ("kind", "split", "menu", "groups"), "view")
    if view["kind"] != VIEW_KIND:
        raise SelectorViewError(f"view.kind must be {VIEW_KIND!r}")
    if view["split"] not in PARTITIONS:
        raise SelectorViewError(f"view.split must be one of {PARTITIONS}")
    groups = view["groups"]
    if not isinstance(groups, dict) or not groups:
        raise SelectorViewError("view.groups: expected a non-empty object")
    if view["menu"] != ["a0", *sorted(groups)]:
        raise SelectorViewError("view.menu must be 'a0' followed by the sorted group ids")
    for gid, group in groups.items():
        if not (isinstance(gid, str) and gid.startswith("g-")):
            raise SelectorViewError(f"view.groups: {gid!r} is not an opaque group id")
        group = _exact(group, ("static", "guard"), f"groups.{gid}")
        if _validate_static(group["static"], f"groups.{gid}.static") != _validate_guard(
                group["guard"], f"groups.{gid}.guard"):
            raise SelectorViewError(f"groups.{gid}: static and guard sizes differ")
    return view


def build_selector_view(prepared_dir: str | Path, guard_run: str | Path) -> tuple[bytes, dict]:
    """(view bytes, receipt) for the split of a complete score-groups run (engine side: the
    manifest is read here and never placed in the view)."""
    guard_run = Path(guard_run)
    problems = verify_files(guard_run)
    if problems:
        raise SelectorViewError(f"guard run {guard_run} is not complete: {problems[:3]}")
    job, marker = read_json(guard_run / "job.json"), read_complete(guard_run)
    if job.get("kind") != "score-groups":
        raise SelectorViewError(f"{guard_run} is not a score-groups run")
    split = job["split"]
    manifest, digest = read_manifest(prepared_dir, job["manifest_sha256"])
    if marker["identity"]["manifest_sha256"] != digest:
        raise SelectorViewError("the guard run was not computed on these prepared data")
    static = json.loads(read_verified(prepared_dir, manifest, X0_STATIC))["partitions"][split]
    menu = json.loads(read_verified(prepared_dir, manifest, GROUPS))["partitions"][split]["menu"]
    guard = read_json(guard_run / "x0_guard.json")
    if guard.get("split") != split:
        raise SelectorViewError("the guard features are for another split")
    by_id = {entry["group_id"]: entry for entry in static}
    if set(by_id) != set(guard["groups"]):
        raise SelectorViewError("the guard features cover other groups than the prepared split")
    groups = {gid: {"static": {key: by_id[gid][key] for key in STATIC_KEYS},
                    "guard": {key: guard["groups"][gid][key] for key in GUARD_KEYS}}
              for gid in sorted(by_id)}
    view = validate_view({"kind": VIEW_KIND, "split": split, "menu": menu, "groups": groups})
    data = canonical_json(view)
    receipt = {"kind": RECEIPT_KIND, "view_sha256": sha256_bytes(data), "split": split,
               "manifest_sha256": digest, "x0_static_sha256": manifest["files"][X0_STATIC],
               "groups_sha256": manifest["files"][GROUPS], "guard_run": str(guard_run),
               "guard_run_resolved": str(guard_run.resolve()),
               "guard_run_complete_sha256": sha256_file(guard_run / COMPLETE),
               "guard_identity": marker["identity"]}
    return data, receipt


def export_selector_view(prepared_dir: str | Path, guard_run: str | Path, out: str | Path,
                         receipt_out: str | Path) -> dict:
    """Write the view and its receipt as new files (never replaced); returns the receipt."""
    data, receipt = build_selector_view(prepared_dir, guard_run)
    for path in (out, receipt_out):
        if Path(path).exists():
            raise FileExistsError(f"{path} exists; selector views are never replaced")
    write_atomic(out, data)
    write_atomic(receipt_out, canonical_json(receipt))
    return receipt


def _refuse_constant(name: str) -> None:
    raise SelectorViewError(f"non-finite number {name} in a selector view")


def _frozen(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _frozen(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_frozen(item) for item in value)
    return value


def read_selector_view(path: str | Path, expected_sha256: str | None = None) -> SelectorView:
    """The selector-side reader: exact canonical bytes, the expected hash, the whitelisted
    schema; returns read-only data (no manifest, no ``Prepared``, no file paths)."""
    data = Path(path).read_bytes()
    digest = sha256_bytes(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise SelectorViewError(f"selector view sha256 {digest} differs from the expected {expected_sha256}")
    try:
        view = json.loads(data, parse_constant=_refuse_constant)
    except ValueError as exc:
        raise SelectorViewError(f"selector view is not valid JSON: {exc}") from exc
    try:
        canonical = canonical_json(view)
    except ValueError as exc:
        raise SelectorViewError(f"selector view is not canonical JSON: {exc}") from exc
    if canonical != data:
        raise SelectorViewError("selector view bytes are not canonical JSON (duplicate keys or "
                                "other formatting)")
    validate_view(view)
    return SelectorView(view["split"], tuple(view["menu"]), _frozen(view["groups"]), digest)
