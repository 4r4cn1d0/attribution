"""Shared pieces of the recovery safeguards (stdlib only).

- **Errors.** Every safeguard fails closed with a ``DurabilityError`` subclass; a real provider
  or remote-storage adapter that has not been configured raises ``NotConfigured``.
- **Journal.** An append-only, fsynced JSONL log that is outcome-blind by construction: a record
  may hold only whitelisted keys (identifiers, paths, hashes, sizes, statuses, timings) and short
  scalar values, so a metric, prompt, completion or policy choice cannot be logged by accident.
- **Exclusive writes.** ``write_exclusive`` publishes a file atomically and never replaces one:
  identical bytes are reused, different bytes are a ``CollisionError``.
- **Recorded paths.** Sealed evidence records absolute paths of the machine that produced it.
  ``SourceMap`` translates a recorded path to where the bytes are now and, unlike the engine's
  first-match ``PathMap``, refuses a path that two prefixes claim.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import math
import os
import secrets
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable, Iterator

from experiments.safety_selection.common import (append_jsonl, canonical_json, read_json, read_jsonl,
                                                 sha256_bytes, sha256_file)
from experiments.safety_selection.verify import PathMap

try:
    import fcntl
except ImportError:  # pragma: no cover - POSIX hosts only
    fcntl = None

__all__ = ["DurabilityError", "NotConfigured", "TransferError", "CollisionError", "CapacityError",
           "VerificationFailed", "GateRefused", "AdmissionRefused", "StorageRefused", "ProviderError", "RestoreError",
           "PathAmbiguity", "BlindnessError", "LostAttemptUnresolved", "Clock", "utc_clock", "iso", "parse_utc",
           "token", "Journal", "JOURNAL_KEYS", "check_blind", "write_exclusive", "locked", "recorded_path",
           "relative_name", "path_id", "SourceMap", "append_jsonl", "canonical_json", "read_json", "read_jsonl",
           "sha256_bytes", "sha256_file"]


class DurabilityError(RuntimeError):
    """A safeguard refused or failed; nothing was acknowledged, admitted or dispatched."""


class NotConfigured(DurabilityError):
    """A real provider or remote-storage adapter is not configured (it fails closed)."""


class TransferError(DurabilityError):
    """A copy did not arrive intact (partial, corrupt, changed at the source or an I/O error)."""


class CollisionError(DurabilityError):
    """The same name already holds different bytes; both are preserved and nothing is replaced."""


class CapacityError(DurabilityError):
    """The destination has too little free space for the copy (or reported a full disk)."""


class VerificationFailed(DurabilityError):
    """The source is not sealed, or the restored copy does not verify."""


class GateRefused(DurabilityError):
    """No dispatch: an acknowledgement or a valid admission lease is missing."""


class AdmissionRefused(DurabilityError):
    """Balance/runway admission failed closed (missing, stale, ambiguous or insufficient inputs)."""


class StorageRefused(DurabilityError):
    """The durable source or the independent destination was not confirmed."""


class ProviderError(DurabilityError):
    """The provider answered in a shape or with a value this code does not know, or a meaning was
    not confirmed: nothing is derived from it."""


class RestoreError(DurabilityError):
    """A restore would have replaced different bytes, or the stored copy is incomplete."""


class PathAmbiguity(DurabilityError):
    """A recorded path is not absolute and normalized, or more than one mapping claims it."""


class BlindnessError(DurabilityError):
    """A log record carried a field or value an outcome-blind log may not hold."""


class LostAttemptUnresolved(DurabilityError):
    """A lost fresh start still holds its trajectory claim; it must be declared lost explicitly."""


Clock = Callable[[], dt.datetime]


def utc_clock() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(moment: dt.datetime) -> str:
    if moment.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return moment.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds")


def parse_utc(text: object) -> dt.datetime:
    """An aware timestamp from ISO text; anything else (naive, malformed, not a string) raises."""
    if not isinstance(text, str):
        raise ValueError("timestamp is not a string")
    moment = dt.datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise ValueError("timestamp has no timezone")
    return moment.astimezone(dt.timezone.utc)


def token() -> str:
    return secrets.token_hex(8)


# What an outcome-blind log may hold: identifiers, paths, hashes, sizes, statuses and timings.
JOURNAL_KEYS = frozenset({
    "event", "utc", "namespace", "worker", "unit", "unit_kind", "label", "attempt", "status", "reason",
    "error_type", "files", "bytes", "copied_files", "copied_bytes", "content_sha256", "seal_sha256",
    "manifest_sha256", "code_sha256", "recipe_sha256", "path", "path_sha256", "seconds", "copy_seconds",
    "verify_seconds", "folders", "run_one_stream_checked", "snapshot_sha256", "sequence", "lease", "expires_utc",
    "start_utc", "end_utc", "last_seen_utc", "known_seconds", "needs_seconds", "token", "operator", "units",
    "records", "attempts", "restored_files", "reused_files", "destination", "kind", "location", "block",
    "amount", "currency", "rate_per_hour", "reserved_amount", "reserved_until_utc", "balance_as_of_utc",
    "available", "need", "increment_seconds", "problems", "retention_reserve", "retention_until_utc",
    "held_reservations", "held_reserves"})
_MAX_TEXT = 400


def _blind_value(key: str, value: object, depth: int = 0) -> None:
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BlindnessError(f"{key}: non-finite number")
        return
    if isinstance(value, str):
        if len(value) > _MAX_TEXT:
            raise BlindnessError(f"{key}: text of {len(value)} characters does not belong in an outcome-blind log")
        return
    if depth < 2 and isinstance(value, (list, tuple)):
        for item in value:
            _blind_value(key, item, depth + 1)
        return
    if depth < 2 and isinstance(value, dict):
        check_blind(value, depth + 1)
        return
    raise BlindnessError(f"{key}: values of type {type(value).__name__} are not logged")


def check_blind(record: dict, depth: int = 0) -> dict:
    """Refuse a log record with a key outside ``JOURNAL_KEYS`` or a value that is not a short
    scalar (or a shallow list/dict of them)."""
    unknown = sorted(set(record) - JOURNAL_KEYS)
    if unknown:
        raise BlindnessError(f"fields {unknown} are not allowed in an outcome-blind log")
    for key, value in record.items():
        _blind_value(key, value, depth)
    return record


class Journal:
    """Append-only outcome-blind log (one fsynced JSON line per event), kept outside every sealed
    folder: the verifier rejects files added to one."""

    def __init__(self, path: str | Path, clock: Clock = utc_clock) -> None:
        self.path, self.clock = Path(path), clock

    def append(self, event: str, **fields: object) -> dict:
        record = check_blind({"event": event, "utc": iso(self.clock()), **fields})
        append_jsonl(self.path, record)
        return record

    def read(self) -> list[dict]:
        return read_jsonl(self.path)


def write_exclusive(path: str | Path, data: bytes) -> bool:
    """Publish ``data`` at ``path`` atomically and exclusively (a fsynced temporary file, then a
    hard link, which fails if the name exists). True: created. False: the name already held the
    identical bytes (an idempotent retry). Different bytes raise ``CollisionError``; the existing
    file is never replaced."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{token()}.tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(tmp, path)
        return True
    except FileExistsError:
        if path.read_bytes() == data:
            return False
        raise CollisionError(f"{path} exists with different content; immutable records are never replaced") from None
    finally:
        os.unlink(tmp)


@contextlib.contextmanager
def locked(path: str | Path) -> Iterator[None]:
    """An exclusive advisory lock on ``path`` (blocking), released on exit: serializes readers and
    writers of one ledger across processes and threads."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+b") as handle:
        if fcntl is None:  # pragma: no cover - POSIX hosts only
            raise NotConfigured("file locking is unavailable on this platform; reservations cannot be serialized")
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def recorded_path(path: str | Path) -> str:
    """A recorded location as a normalized absolute POSIX path; a relative path, ``..`` or a
    redundant component is ambiguous and refused."""
    text = str(path)
    pure = PurePosixPath(text)
    if not pure.is_absolute() or ".." in pure.parts or str(pure) != os.path.normpath(text) or text != str(pure):
        raise PathAmbiguity(f"{text!r} is not a normalized absolute recorded path")
    return text


def relative_name(name: str) -> str:
    """A file name inside a unit: relative, normalized, no ``..``."""
    pure = PurePosixPath(name)
    if not name or pure.is_absolute() or ".." in pure.parts or str(pure) != name or name in (".", ""):
        raise PathAmbiguity(f"{name!r} is not a normalized relative file name")
    return name


def path_id(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


class SourceMap:
    """Where recorded paths are now: ``(recorded prefix, local prefix)`` pairs (none: every path is
    where it was recorded). Strict: a recorded path that two prefixes contain, or two recorded
    prefixes sharing one local prefix, raise ``PathAmbiguity``. Nothing is ever rewritten."""

    def __init__(self, pairs: Iterable[tuple[str | Path, str | Path]] = ()) -> None:
        self.pairs = [(PurePosixPath(recorded_path(old)), Path(new)) for old, new in pairs]
        local = [str(new.resolve()) for _, new in self.pairs]
        if len(set(local)) != len(local):
            raise PathAmbiguity("two recorded prefixes map to one local folder")

    def local(self, recorded: str | Path) -> Path:
        path = PurePosixPath(recorded_path(recorded))
        matches = [(old, new) for old, new in self.pairs if path.is_relative_to(old)]
        if len(matches) > 1:
            raise PathAmbiguity(f"{path} is claimed by {len(matches)} mapped prefixes: {[str(o) for o, _ in matches]}")
        if not matches:
            return Path(str(path))
        old, new = matches[0]
        return new / path.relative_to(old)

    def engine_map(self) -> PathMap:
        """The same pairs as the engine's read-only ``PathMap`` (verification only)."""
        return PathMap([(str(old), new) for old, new in self.pairs])
