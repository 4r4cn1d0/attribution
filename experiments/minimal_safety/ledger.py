"""Synchronized per-stage wall-time ledger, resource caps and run status (stdlib only).

``stage()`` calls ``sync()`` (a device barrier, e.g. ``torch.mps.synchronize``) before reading
the clock at both ends, so asynchronous device work is charged to the stage that issued it.
Every finished, failed, capped or interrupted stage is appended to ``ledger.jsonl``
immediately (with whatever progress it recorded) and ``status.json`` is rewritten atomically,
so an interruption leaves visible, partial evidence. ``check()`` raises :class:`CapExceeded`
before work that would pass the wall or output-size cap; every stage checks on entry, callers
check before each work item, and nobody shrinks an arm's workload to fit. Checks are
cooperative: an operation already running (a model load, one forward pass) can finish past the
cap, and the caller's recorded elapsed time then shows the overshoot.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import resource
import sys
import time
from pathlib import Path
from typing import Callable, Iterator

from .common import append_jsonl, write_json

__all__ = ["CapExceeded", "Ledger", "output_bytes", "peak_rss_bytes"]


class CapExceeded(RuntimeError):
    """The wall-time or output-size cap would be exceeded."""


def peak_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)  # macOS bytes, Linux KiB


def output_bytes(run_dir: str | Path) -> int:
    return sum(p.stat().st_size for p in Path(run_dir).rglob("*") if p.is_file())


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class Ledger:
    def __init__(self, run_dir: str | Path, wall_cap_s: float, byte_cap: int,
                 clock: Callable[[], float] = time.monotonic, sync: Callable[[], None] | None = None,
                 memory: Callable[[], dict] | None = None) -> None:
        self.run_dir = Path(run_dir)
        self.wall_cap_s = float(wall_cap_s)
        self.byte_cap = int(byte_cap)
        self.clock = clock
        self.sync = sync or (lambda: None)
        self.memory = memory or (lambda: {"peak_rss_bytes": peak_rss_bytes()})
        self.path = self.run_dir / "ledger.jsonl"
        self.last_item = ""  # the last work item checked: where a stopped stage was
        self.t0 = clock()

    def elapsed(self) -> float:
        return self.clock() - self.t0

    def output_bytes(self) -> int:
        return output_bytes(self.run_dir)

    def check(self, predicted_s: float = 0.0, what: str = "", outputs: bool = True) -> None:
        """Raise CapExceeded unless ``predicted_s`` more seconds fit the wall cap and the outputs
        are within the byte cap. ``outputs=False`` skips only the directory walk, for
        fine-grained checks (per token, per batch); stage entries, saves and the final check
        include it."""
        self.last_item = what
        elapsed = self.elapsed()
        if elapsed + predicted_s > self.wall_cap_s:
            raise CapExceeded(f"wall cap {self.wall_cap_s:g}s before {what}: elapsed {elapsed:.1f}s"
                              f" + predicted {predicted_s:.1f}s")
        if not outputs:
            return
        size = self.output_bytes()
        if size > self.byte_cap:
            raise CapExceeded(f"output cap {self.byte_cap} bytes before {what}: {size} written")

    def status(self, status: str, **info: object) -> None:
        write_json(self.run_dir / "status.json",
                   {"status": status, "elapsed_s": self.elapsed(), "updated_utc": _utc(), **info})

    def _memory(self) -> dict:
        try:
            return self.memory()
        except Exception as exc:  # noqa: BLE001 - memory probes must not end a run
            return {"error": f"{type(exc).__name__}: {exc}"}

    @contextlib.contextmanager
    def stage(self, name: str, **keys: object) -> Iterator[dict]:
        """Time one stage; the yielded dict collects extra fields (steps, tokens, progress, ...).
        A stage never starts past a cap: the entry check raises before anything is recorded."""
        self.check(0.0, f"stage {name}")
        self.sync()
        start = self.elapsed()
        self.status("running", stage=name, **keys)
        record: dict = {"stage": name, **keys, "start_s": start, "start_utc": _utc()}
        info: dict = {}
        try:
            yield info
            self.sync()
            record["status"] = "ok"
        except BaseException as exc:
            with contextlib.suppress(Exception):
                self.sync()
            record["status"] = ("cap" if isinstance(exc, CapExceeded) else
                                "interrupted" if isinstance(exc, KeyboardInterrupt) else "error")
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["last_item"] = self.last_item
            raise
        finally:
            end = self.elapsed()
            record.update(info, end_s=end, seconds=end - start, memory=self._memory())
            append_jsonl(self.path, record)
