"""The off-pod destination (stdlib only).

A destination is a key space of immutable objects, reachable independently of the GPU account:

- ``upload`` writes a *staging* object (the only kind that may be overwritten or discarded);
- ``commit`` moves a staged object to its final key atomically and exclusively: an existing
  identical object is reused, a different one is a ``CollisionError`` and is never replaced;
- ``put_new`` creates a small final object exclusively (manifests, acknowledgements);
- ``sha256`` hashes the bytes *as stored* (read back), never the sender's copy;
- ``free_bytes`` and ``probe`` check capacity and permissions before anything is admitted.

``LocalDirectoryDestination`` is a directory: what the local tests and a mounted volume use.
``github_destination.GitHubReleaseDestination`` stores objects as release assets of a private
GitHub repository; it is built only from explicit configuration (``wiring.destination_from``) and
refuses every call without its token. ``UnconfiguredDestination`` is the default for anything
remote that was not configured: each call raises ``NotConfigured``, so nothing can be acknowledged
by accident. No adapter holds or records credentials.
"""

from __future__ import annotations

import abc
import errno
import os
import shutil
from pathlib import Path

from .common import (CapacityError, CollisionError, NotConfigured, TransferError, relative_name, sha256_file,
                     token, write_exclusive)

__all__ = ["Destination", "LocalDirectoryDestination", "UnconfiguredDestination", "STAGING", "is_staging"]

STAGING = "staging/"


def is_staging(key: str) -> bool:
    """A staging object: ``staging/...`` or ``<namespace>/staging/...``."""
    return "staging" in key.split("/")[:2]


class Destination(abc.ABC):
    """See the module doc. Keys are normalized relative POSIX names."""

    @abc.abstractmethod
    def describe(self) -> dict:
        """Kind and location for records (never a credential)."""

    @abc.abstractmethod
    def free_bytes(self) -> int: ...

    @abc.abstractmethod
    def probe(self) -> None:
        """Write, read back and remove a probe object; raises when the destination is unusable."""

    @abc.abstractmethod
    def upload(self, source: Path, key: str) -> None: ...

    @abc.abstractmethod
    def commit(self, staged: str, final: str) -> bool: ...

    @abc.abstractmethod
    def put_new(self, key: str, data: bytes) -> bool: ...

    @abc.abstractmethod
    def exists(self, key: str) -> bool: ...

    @abc.abstractmethod
    def read(self, key: str) -> bytes: ...

    @abc.abstractmethod
    def sha256(self, key: str) -> tuple[str, int]: ...

    @abc.abstractmethod
    def download(self, key: str, target: Path) -> None: ...

    @abc.abstractmethod
    def list(self, prefix: str) -> list[str]: ...

    @abc.abstractmethod
    def discard(self, key: str) -> None:
        """Remove a staging object (final objects are never removed)."""


def _io(exc: OSError, what: str) -> Exception:
    if exc.errno in (errno.ENOSPC, errno.EDQUOT):
        return CapacityError(f"{what}: the destination is full ({exc.strerror})")
    return TransferError(f"{what}: {type(exc).__name__}: {exc.strerror or exc}")


class LocalDirectoryDestination(Destination):
    """A directory as the destination (local tests; a mounted volume)."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        return self.root / relative_name(key)

    def describe(self) -> dict:
        return {"kind": "local-directory", "location": str(self.root)}

    def free_bytes(self) -> int:
        self.root.mkdir(parents=True, exist_ok=True)
        return shutil.disk_usage(self.root).free

    def probe(self) -> None:
        key = f"{STAGING}probe-{token()}"
        path = self._path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"probe")
            if path.read_bytes() != b"probe":
                raise TransferError(f"{self.root}: the probe object read back differently")
            path.unlink()
        except OSError as exc:
            raise _io(exc, f"{self.root}: destination probe") from exc

    def upload(self, source: Path, key: str) -> None:
        if not is_staging(key):
            raise TransferError(f"{key}: uploads go to the staging area only")
        target = self._path(key)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(source, "rb") as reader, open(target, "wb") as writer:
                shutil.copyfileobj(reader, writer, 1 << 20)
                writer.flush()
                os.fsync(writer.fileno())
        except OSError as exc:
            raise _io(exc, f"upload of {key}") from exc

    def commit(self, staged: str, final: str) -> bool:
        source, target = self._path(staged), self._path(final)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(source, target)
            except FileExistsError:
                if sha256_file(source) != sha256_file(target):
                    raise CollisionError(f"{final} already holds different bytes; the staged copy is kept at "
                                         f"{staged}") from None
                source.unlink()
                return False
            source.unlink()
            return True
        except OSError as exc:
            raise _io(exc, f"commit of {final}") from exc

    def put_new(self, key: str, data: bytes) -> bool:
        try:
            return write_exclusive(self._path(key), data)
        except OSError as exc:
            raise _io(exc, f"write of {key}") from exc

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def read(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except OSError as exc:
            raise _io(exc, f"read of {key}") from exc

    def sha256(self, key: str) -> tuple[str, int]:
        path = self._path(key)
        try:
            return sha256_file(path), path.stat().st_size
        except OSError as exc:
            raise _io(exc, f"hash of {key}") from exc

    def download(self, key: str, target: Path) -> None:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self._path(key), target)
        except OSError as exc:
            raise _io(exc, f"download of {key}") from exc

    def list(self, prefix: str) -> list[str]:
        base = self.root / prefix.rstrip("/") if prefix else self.root
        if not base.is_dir():
            return []
        return sorted(p.relative_to(self.root).as_posix() for p in base.rglob("*")
                      if p.is_file() and not (p.name.startswith(".") and p.name.endswith(".tmp")))

    def discard(self, key: str) -> None:
        if not is_staging(key):
            raise TransferError(f"{key}: only staging objects are ever removed")
        self._path(key).unlink(missing_ok=True)


class UnconfiguredDestination(Destination):
    """A remote destination that has not been configured and validated: every call fails closed."""

    def __init__(self, kind: str = "remote") -> None:
        self.kind = kind

    def _refuse(self, *args: object, **kwargs: object):
        raise NotConfigured(f"the {self.kind} destination adapter is not configured; remote destinations wait for "
                            "the funded one-worker validation")

    def describe(self) -> dict:
        return {"kind": f"{self.kind} (not configured)", "location": None}

    free_bytes = probe = upload = commit = put_new = exists = read = sha256 = download = list = discard = _refuse
