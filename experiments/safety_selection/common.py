"""Shared helpers (stdlib only).

Hashing, canonical JSON, atomic and append-only writes, strict JSONL readers and named seed
streams are imported unchanged from the minimal-safety engine, whose contracts fit: canonical
JSON rejects NaN/inf, appends are fsynced, readers never skip a line, and ``derive_seed`` gives
an independent 64-bit stream per purpose. This module adds the code identity that resumes must
match, opaque identifiers and single-line JSON encoding.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Iterable

from experiments.minimal_safety.common import (append_jsonl, canonical_json, derive_seed,
                                               read_jsonl, recover_jsonl, sha256_bytes,
                                               sha256_file, write_atomic, write_json)

__all__ = ["append_jsonl", "canonical_json", "derive_seed", "read_jsonl", "recover_jsonl",
           "sha256_bytes", "sha256_file", "write_atomic", "write_json", "code_identity",
           "opaque_id", "utc_now", "json_line", "jsonl_bytes", "ids_sha256", "read_json"]

PACKAGE_DIR = Path(__file__).resolve().parent
REUSED_DIR = PACKAGE_DIR.parent / "minimal_safety"
# The minimal-safety modules this package imports, directly or transitively.
REUSED_MODULES = ("__init__.py", "common.py", "data.py", "ledger.py", "model.py", "plan.py", "text.py")


def code_identity() -> dict:
    """SHA-256 of every engine source file (tests excluded) and of the reused minimal-safety
    modules. Continuations refuse a different identity; other jobs record theirs."""
    files = {f"safety_selection/{path.name}": sha256_file(path) for path in sorted(PACKAGE_DIR.glob("*.py"))}
    files.update({f"minimal_safety/{name}": sha256_file(REUSED_DIR / name) for name in REUSED_MODULES})
    return {"files": files, "sha256": sha256_bytes(canonical_json(files))}


def opaque_id(prefix: str, value: int) -> str:
    """``prefix-<16 hex>`` from a 64-bit integer drawn from a named seed stream."""
    return f"{prefix}-{value:016x}"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def json_line(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def jsonl_bytes(rows: Iterable[Any]) -> bytes:
    return b"".join(json_line(row) for row in rows)


def ids_sha256(ids: Iterable[int]) -> str:
    """Digest of a token-id sequence (comma-separated decimal), used to pin tokenization."""
    return sha256_bytes(",".join(str(int(i)) for i in ids).encode("ascii"))


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_bytes())
