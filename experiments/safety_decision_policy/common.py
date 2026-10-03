"""Shared helpers of the stage-B decision-policy package (stdlib only).

Hashing, canonical JSON, atomic writes, strict JSONL and named seed streams are the engine's
(``experiments.safety_selection.common``, itself reusing ``minimal_safety``). Importing them
does not change the engine's code identity, which hashes only the engine's own source files.
This module adds this package's own code identity, write-once records (identical bytes are
accepted on resume, different bytes refuse), a strict canonical reader, finite-number checks
and the package's error types.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from experiments.safety_selection.common import (append_jsonl, canonical_json, derive_seed,
                                                 read_json, read_jsonl, sha256_bytes, sha256_file,
                                                 utc_now, write_atomic)
from experiments.safety_selection.common import code_identity as engine_code_identity

__all__ = ["PolicyError", "VerificationError", "LockError", "RequestRefused", "LockRefused",
           "append_jsonl", "canonical_json", "derive_seed", "read_json", "read_jsonl", "sha256_bytes",
           "sha256_file", "utc_now", "write_atomic", "engine_code_identity", "policy_code_identity",
           "write_once", "write_once_json", "read_canonical", "read_json_strict", "finite", "PACKAGE_DIR"]

PACKAGE_DIR = Path(__file__).resolve().parent


class PolicyError(ValueError):
    """An invalid configuration, input or request: nothing was run or written."""


class VerificationError(RuntimeError):
    """An artifact, pin, receipt or cached state does not verify."""


class LockError(PermissionError):
    """Hidden-bank access before the choice lock, or a change to an immutable record."""


class RequestRefused(PolicyError):
    """A backend refused an operation by explicit validation before any work ran. The only
    exception the controller does not charge or count as an attempt; any other exception
    raised once execution started is a timed, charged and counted failed attempt."""


class LockRefused(LockError, RequestRefused):
    """Final-bank access without a valid choice lock of the same block and configuration that
    authorizes the operation's arm and seed (refused before any work)."""


def policy_code_identity() -> dict:
    """SHA-256 of every source file of this package (tests and configs excluded)."""
    files = {f"safety_decision_policy/{path.name}": sha256_file(path)
             for path in sorted(PACKAGE_DIR.glob("*.py"))}
    return {"files": files, "sha256": sha256_bytes(canonical_json(files))}


def write_once(path: str | Path, data: bytes) -> str:
    """Create an immutable file atomically and exclusively; returns its SHA-256. An existing
    file with identical bytes is accepted (an idempotent resume); different bytes refuse."""
    path = Path(path)
    if path.exists():
        if path.read_bytes() != data:
            raise LockError(f"{path} exists with different content; immutable records are never replaced")
        return sha256_bytes(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(tmp, path)
    except FileExistsError:
        if path.read_bytes() != data:
            raise LockError(f"{path} appeared with different content; immutable records are never "
                            "replaced") from None
    finally:
        tmp.unlink(missing_ok=True)
    return sha256_bytes(data)


def write_once_json(path: str | Path, obj: Any) -> str:
    return write_once(path, canonical_json(obj))


def _refuse_constant(name: str) -> None:
    raise VerificationError(f"non-finite number {name} in a canonical record")


def read_canonical(path: str | Path, expected_sha256: str | None = None) -> Any:
    """A canonical JSON record: the expected hash (if given), no NaN or infinity, no duplicate
    keys or other formatting (re-encoding must reproduce the exact bytes)."""
    data = Path(path).read_bytes()
    digest = sha256_bytes(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise VerificationError(f"{path}: sha256 {digest} differs from the pinned {expected_sha256}")
    try:
        obj = json.loads(data, parse_constant=_refuse_constant)
    except ValueError as exc:
        raise VerificationError(f"{path} is not valid JSON: {exc}") from exc
    if canonical_json(obj) != data:
        raise VerificationError(f"{path} is not canonical JSON (duplicate keys or other formatting)")
    return obj


def _no_duplicates(pairs: list) -> dict:
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        raise VerificationError(f"duplicate keys {sorted(k for k in set(keys) if keys.count(k) > 1)}")
    return dict(pairs)


def read_json_strict(path: str | Path) -> Any:
    """A hand-written JSON input (configuration draft, fit spec, runs index): any formatting, but
    duplicate keys, NaN and infinity refuse."""
    try:
        return json.loads(Path(path).read_bytes(), object_pairs_hook=_no_duplicates,
                          parse_constant=_refuse_constant)
    except ValueError as exc:
        raise VerificationError(f"{path} is not valid JSON: {exc}") from exc


def finite(value: object, where: str) -> float:
    """A finite real number (never a bool, None or a string)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise PolicyError(f"{where}: expected a finite number, got {value!r}")
    return float(value)
