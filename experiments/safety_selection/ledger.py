"""Durable run evidence (stdlib only).

Every job writes one new folder; nothing is overwritten, resumed in place or deleted.

- ``ledger.jsonl``: one record per stage, appended (fsynced) when the stage ends, ok or not:
  device-synchronized wall seconds, UTC start/end, work counters and memory (for CUDA, the
  caching allocator's current and peak bytes since the previous stage record).
- ``progress.jsonl``: fine-grained progress (optimizer steps, evaluation batches).
- ``records.jsonl``: unit results (checkpoints, evaluations, attribution passes).
- ``error.txt``: the traceback of a failure; a failed folder is preserved and never completed.
- ``status.json``: a convenience snapshot, rewritten; not evidence and not hashed.
- ``COMPLETE.json``: written last, only after every check passed, with the SHA-256 of every
  other file. A folder without it, or whose files no longer match it, is not complete.
"""

from __future__ import annotations

import contextlib
import time
from pathlib import Path
from typing import Callable, Iterator

from .common import append_jsonl, read_json, sha256_file, utc_now, write_json

__all__ = ["COMPLETE", "STATUS", "ERROR", "LEDGER", "PROGRESS", "RECORDS", "RunDirError",
           "LimitReached", "create_run_dir", "RunLedger", "artifact_hashes", "write_complete",
           "verify_files", "read_complete"]

COMPLETE = "COMPLETE.json"
STATUS = "status.json"
ERROR = "error.txt"
LEDGER = "ledger.jsonl"
PROGRESS = "progress.jsonl"
RECORDS = "records.jsonl"
_UNHASHED = (COMPLETE, STATUS)


class RunDirError(RuntimeError):
    pass


class LimitReached(RuntimeError):
    """The job's optional wall limit passed; the folder stays incomplete."""


def create_run_dir(path: str | Path) -> Path:
    path = Path(path)
    if path.exists():
        raise RunDirError(f"{path} exists: every job writes a new folder; nothing is replaced")
    path.mkdir(parents=True)
    return path


class RunLedger:
    def __init__(self, run_dir: str | Path, *, sync: Callable[[], None] | None = None,
                 memory: Callable[[], dict] | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 wall_limit_s: float | None = None) -> None:
        self.run_dir = Path(run_dir)
        self.sync = sync or (lambda: None)
        self.memory = memory or (lambda: {})
        self.clock = clock
        self.wall_limit_s = wall_limit_s
        self.last_item = ""
        self.t0 = clock()

    def elapsed(self) -> float:
        return self.clock() - self.t0

    def check(self, what: str) -> None:
        """Cooperative check before a work item: records it and enforces the optional limit."""
        self.last_item = what
        if self.wall_limit_s is not None and self.elapsed() > self.wall_limit_s:
            raise LimitReached(f"wall limit {self.wall_limit_s:g}s passed before {what}")

    def status(self, status: str, **info: object) -> None:
        write_json(self.run_dir / STATUS, {"status": status, "elapsed_s": self.elapsed(),
                                           "updated_utc": utc_now(), **info})

    def _memory(self) -> dict:
        try:
            return self.memory()
        except Exception as exc:  # noqa: BLE001 - a memory probe must not end a run
            return {"error": f"{type(exc).__name__}: {exc}"}

    @contextlib.contextmanager
    def stage(self, name: str, **keys: object) -> Iterator[dict]:
        """Time one stage between device barriers; the yielded dict collects work counters."""
        self.check(f"stage {name}")
        self.sync()
        start = self.elapsed()
        self.status("running", stage=name, **keys)
        record: dict = {"stage": name, **keys, "start_s": start, "start_utc": utc_now()}
        info: dict = {}
        try:
            yield info
            self.sync()
            record["status"] = "ok"
        except BaseException as exc:
            with contextlib.suppress(Exception):
                self.sync()
            record["status"] = ("limit" if isinstance(exc, LimitReached) else
                                "interrupted" if isinstance(exc, KeyboardInterrupt) else "error")
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["last_item"] = self.last_item
            raise
        finally:
            end = self.elapsed()
            record.update(info, end_s=end, seconds=end - start, end_utc=utc_now(),
                          memory=self._memory())
            append_jsonl(self.run_dir / LEDGER, record)
            info["seconds"] = end - start  # the recorded synchronized seconds, for the caller

    def progress(self, kind: str, **fields: object) -> None:
        append_jsonl(self.run_dir / PROGRESS, {"kind": kind, "elapsed_s": self.elapsed(),
                                               "utc": utc_now(), **fields})

    def record(self, kind: str, **fields: object) -> None:
        append_jsonl(self.run_dir / RECORDS, {"kind": kind, **fields})


def artifact_hashes(run_dir: str | Path) -> dict[str, str]:
    root = Path(run_dir)
    return {path.relative_to(root).as_posix(): sha256_file(path)
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.relative_to(root).as_posix() not in _UNHASHED}


def write_complete(run_dir: str | Path, summary: dict) -> dict:
    """The completion marker; call only after every check passed."""
    run_dir = Path(run_dir)
    files = artifact_hashes(run_dir)
    if ERROR in files:
        raise RunDirError("a folder with error.txt is a preserved failure and cannot be completed")
    marker = {"complete": True, "completed_utc": utc_now(), **summary, "files": files}
    write_json(run_dir / COMPLETE, marker)
    return marker


def read_complete(run_dir: str | Path) -> dict | None:
    path = Path(run_dir) / COMPLETE
    if not path.exists():
        return None
    return read_json(path)


def verify_files(run_dir: str | Path) -> list[str]:
    """Problems with a folder's completion evidence (empty list: the files verify)."""
    run_dir = Path(run_dir)
    try:
        marker = read_complete(run_dir)
    except ValueError:
        return [f"{COMPLETE} is unreadable"]
    if marker is None:
        return [f"no {COMPLETE}: the job did not finish every check"]
    if marker.get("complete") is not True or not isinstance(marker.get("files"), dict):
        return [f"{COMPLETE} is malformed"]
    actual = artifact_hashes(run_dir)
    problems = [f"{name} missing or changed since completion"
                for name, digest in sorted(marker["files"].items()) if actual.get(name) != digest]
    problems += [f"{name} added after completion" for name in sorted(actual)
                 if name not in marker["files"]]
    return problems
