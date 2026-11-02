"""What the stage-1b Mac tools share: a refusal with a fixed message, SHA-256 helpers, reads that name no value, the
PATH:SHA256 form, an exclusive create, and the command-line frame (exit 2 on a refusal; any other error prints its
type only, since its message may hold a value). Standard library only.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Refusal(Exception):
    """A fixed message: it names no value of any file read."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_hex64(value) -> bool:
    return isinstance(value, str) and bool(HEX64.match(value))


def read_bytes(path: Path, what: str) -> bytes:
    """The file's bytes; a missing file, a folder or a symbolic link refuses (the message names the role only)."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise Refusal(f"{what} is missing or not a regular file")
    try:
        return path.read_bytes()
    except OSError:
        raise Refusal(f"{what} cannot be read") from None


def read_pinned(path: Path, expected: str, what: str) -> bytes:
    """The file's bytes, refused unless they hash to ``expected`` (the message names no hash)."""
    data = read_bytes(path, what)
    if not is_hex64(expected) or sha256_bytes(data) != expected:
        raise Refusal(f"{what} does not hash to its expected SHA-256")
    return data


class _RepeatedKey(Exception):
    """A JSON object repeats a key (json.loads would keep the last value; s1common.strict_json refuses it too)."""


def _no_repeats(pairs: list) -> dict:
    doc = {}
    for key, value in pairs:
        if key in doc:
            raise _RepeatedKey()
        doc[key] = value
    return doc


def json_object(data: bytes, what: str) -> dict:
    """A JSON object parsed in memory, no key repeated in any object; anything else refuses (the message names the
    role only)."""
    try:
        doc = json.loads(data, object_pairs_hook=_no_repeats)
    except _RepeatedKey:
        raise Refusal(f"{what} repeats a key") from None
    except ValueError:
        raise Refusal(f"{what} is not JSON") from None
    if not isinstance(doc, dict):
        raise Refusal(f"{what} is not a JSON object")
    return doc


def hashed_pair(spec: str, what: str) -> tuple[Path, str]:
    """PATH:SHA256 -> (Path, sha256); any other form refuses."""
    path, _, digest = str(spec).rpartition(":")
    if not path or not HEX64.match(digest):
        raise Refusal(f"{what} is PATH:SHA256")
    return Path(path), digest


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def module_hashes() -> dict[str, str]:
    """This package's modules by SHA-256 (for a record's provenance)."""
    return {p.name: sha256_bytes(p.read_bytes()) for p in sorted(HERE.glob("*.py"))}


def write_exclusive(path: Path, data: bytes, what: str) -> str:
    """An exclusive create (never an overwrite); returns the SHA-256 of the bytes read back."""
    path = Path(path)
    try:
        with open(path, "xb") as handle:
            handle.write(data)
    except FileExistsError:
        raise Refusal(f"{what} exists: it is written once") from None
    digest = sha256_bytes(path.read_bytes())
    if digest != sha256_bytes(data):
        raise Refusal(f"{what} did not read back as written")
    return digest


def run_frame(produce, argv=None) -> int:
    """``produce(argv)`` returns the exit code (0, or 1 for a stated outcome). A Refusal prints its fixed message and
    exits 2; any other exception prints its type only and exits 2."""
    try:
        return produce(argv)
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - its message may hold a value: print the type only
        print(f"REFUSED: an unexpected {type(exc).__name__} (its message is withheld: it may hold a value)",
              file=sys.stderr)
        return 2
