"""Hashing, canonical JSON, atomic/append-only writes and seed derivation (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

__all__ = ["sha256_bytes", "sha256_file", "canonical_json", "write_atomic", "write_json",
           "append_jsonl", "read_jsonl", "recover_jsonl", "derive_seed"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(obj: Any) -> bytes:
    """Sorted keys, 2-space indent, UTF-8, trailing newline; NaN/inf are rejected."""
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
            + "\n").encode("utf-8")


def write_atomic(path: str | os.PathLike, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_json(path: str | os.PathLike, obj: Any) -> str:
    """Atomically write canonical JSON; returns the SHA-256 of the written bytes."""
    data = canonical_json(obj)
    write_atomic(path, data)
    return sha256_bytes(data)


def append_jsonl(path: str | os.PathLike, obj: Any) -> None:
    """Append one JSON line and fsync, so an interrupted run keeps every finished record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _split_jsonl(path: Path) -> tuple[list[dict], bytes]:
    """Every newline-terminated line parsed as one JSON object, plus the bytes after the last
    newline (never decoded: an interrupted append can end inside a UTF-8 character)."""
    *lines, fragment = path.read_bytes().split(b"\n")
    rows = []
    for number, line in enumerate(lines, start=1):
        try:
            row = json.loads(line.decode("utf-8"))
        except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError, blank lines too
            raise ValueError(f"{path}: line {number} is not valid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}: line {number} is not a JSON object")
        rows.append(row)
    return rows, fragment


def read_jsonl(path: str | os.PathLike) -> list[dict]:
    """Strict JSONL: every line is one JSON object and the file ends with a newline; anything
    else raises ValueError and nothing is skipped. A missing file is empty."""
    path = Path(path)
    if not path.exists():
        return []
    rows, fragment = _split_jsonl(path)
    if fragment:
        raise ValueError(f"{path}: unterminated final line ({len(fragment)} bytes)")
    return rows


def recover_jsonl(path: str | os.PathLike) -> tuple[list[dict], bytes]:
    """Interruption recovery only: as read_jsonl, but an unterminated final fragment (an append
    cut off by the interruption) is returned instead of raising, for the caller to record. A
    malformed newline-terminated line still raises."""
    path = Path(path)
    if not path.exists():
        return [], b""
    return _split_jsonl(path)


def derive_seed(*parts: object) -> int:
    """64-bit integer from SHA-256 of '|'-joined parts: independent named streams per purpose."""
    text = "|".join(str(part) for part in parts)
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
