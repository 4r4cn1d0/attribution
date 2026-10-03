"""Stage B: the gated backend and the study backup (no Stage B file is changed).

Insertion point. ``Study.ensure_op`` (controller.py) reaches the backend at fixed places: ``sync()``
then ``clock()`` before an attempt, ``execute(spec, attempt_dir, sources)`` after it wrote
``started.json``, ``sync()``/``clock()`` and the after-call ``receipt.json``, then ``verify()`` of
the completed attempt. ``run-block`` builds ``EngineBackend`` directly, so an administrative
entrypoint (``run_block_gated``) builds ``GatedBackend(EngineBackend(...))`` instead. The wrapper
has the backend interface and delegates everything; it adds:

- ``execute``: **before any work** (only ``started.json`` exists in the attempt folder) the gate:
  every attempt of the study that has a receipt is acknowledged off-pod, the worker's lease is
  valid, and no lost start still holds this trajectory's registry claim; then ``started.json`` of
  the new attempt goes off-pod. Any of these failing, for whatever reason (an unreadable ledger or
  an unexpected error included), raises Stage B's ``RequestRefused``, which the controller records
  as a refusal: not an attempt, not charged, and it stops the controller. Nothing but a refusal can
  leave the gate: any other exception would be recorded by Stage B as a charged failed attempt.
- ``sync`` (before an attempt) and ``verify`` (right after one): **settle**: copy and acknowledge
  every attempt whose ``receipt.json`` exists, the new write-once records and the registry
  snapshot. Settling never raises into the controller (an exception there could leave an empty
  attempt folder that Stage B would later count as an interrupted attempt); a failed settle makes
  the next ``execute`` refuse.

**Where the safeguard's time goes.** The controller cuts its timeline at the backend clock, which
is untouched here, so every safeguard second inside a session is in the Stage B cost record, in
one of two places:

- **inside the attempt's own timer.** The controller reads ``start = clock()`` before it calls
  ``execute`` and ``end = clock()`` after it returns. The gate check (acknowledgement and ledger
  reads) and the off-pod copy of ``started.json``, which run at the top of ``execute``, are
  therefore part of the attempt's measured ``seconds``: operation time, charged to every policy
  that uses the operation and compared with its quote in the overrun list. It is small (reads and
  one small file) but it is not zero and it is not controller time;
- **in the controller seconds of the step that owns the operation** (``common``, ``S-``, ``S+``,
  ``final:<arm>``): the settle before an attempt's timer starts (``sync``) and right after the
  attempt (``verify``), which is where the copy and restore check of an operation's output run.
  The session's very first ``sync`` precedes the start record's clock read, so what it settles
  (``study.json`` of a new study; nothing else when the study was settled beforehand) is in the
  session's start record, charged as session setup.

Either way the copy of an operation is charged like the operation, once, and nothing is hidden.
The alternative (a clock that pauses during administrative work) would keep safeguard time out of
the policy costs but silently contradicts Stage B's statement that its timers tile the session; it
is not implemented. This is a cost-accounting decision for the lead (README, "Open decisions").
The settle after ``run_block`` returns (result, session end record) is outside the session.

**One block per process.** Stage B decides whether a session's setup was measured by whether its
backend object already served a block in this process. A new ``GatedBackend`` around a warm inner
backend would look fresh, and unmeasured setup would be labelled measured. ``run_block_gated``
therefore refuses, before anything is written, an inner backend (or its engine ``Session``) that
already served a block in this process: one block per process, the project's rule.

**Units.** An operation attempt is a unit once its after-call ``receipt.json`` exists, whatever its
status (failed and interrupted attempts are the kept record of lost work and its cost); when its
``run/`` is a sealed engine folder it is restore-verified as one, dependencies included. The
write-once records (``study.json``, specs, schedules, session records, rankings, plans, locks,
results, and ``started.json`` of attempts in flight) go one by one as records; ``registry.jsonl`` as
append-only snapshots. ``controller.lock`` is not evidence. Logs name units by opaque ids only:
Stage B folder names contain arm ids, and final-operation names reveal the chosen arms.

**Restore and resume.** ``Vault.restore`` puts the study back at its recorded root. An attempt that
was in flight comes back as ``started.json`` alone; Stage B's own resume closes it as an
interrupted attempt with its known lower bound (its cost is kept as unknown, never zero) and runs
the next attempt number: the same draw. With the real engine, a lost fresh start still holds its
registry claim: ``reconcile_claims`` re-appends a claim the restored snapshot predates, and the
attempt must be declared lost (``declare_lost_attempt``) before the gate lets its trajectory start
again; nothing here clears a claim.
"""

from __future__ import annotations

import contextlib
import weakref
from pathlib import Path
from typing import Callable

from experiments.safety_decision_policy.common import RequestRefused
from experiments.safety_selection.jobs import trajectory_key
from experiments.safety_selection.ledger import COMPLETE, ERROR

from .backup import Vault
from .common import (DurabilityError, GateRefused, VerificationFailed, append_jsonl, iso, path_id, read_json,
                     read_jsonl, sha256_file, write_exclusive)
from .engine_units import TOMBSTONE
from .gate import DispatchGate
from experiments.safety_selection.prepare import read_manifest

from .units import attempt_unit, code_identity_of, code_unit, prepared_unit, record_unit

__all__ = ["RUN_KINDS", "study_records", "study_attempts", "open_attempts", "StudyBackup", "GatedBackend",
           "reconcile_claims", "declare_lost_attempt", "run_block_gated"]

RUN_KINDS = ("screen", "full_from_short", "full_from_init", "extend", "final")
_RECORD_GLOBS = ("study.json", "static/*/spec.json", "blocks/*/schedule.json", "blocks/*/ranking-*.json",
                 "blocks/*/plan-*.json", "blocks/*/lock.json", "blocks/*/result.json",
                 "blocks/*/sessions/session-*.json", "blocks/*/ops/*/spec.json")
_ATTEMPT_GLOBS = ("static/*/attempt-*", "blocks/*/ops/*/attempt-*")
# Inner backends, and their engine Sessions (the asset caches), that already served a gated block
# in this process. A new GatedBackend around one of them would look fresh to Stage B.
_SERVED: weakref.WeakSet = weakref.WeakSet()


def _warm(inner) -> list:
    """The objects of an inner backend that carry loaded state across blocks: itself and its
    engine ``Session`` (None for a fake or read-only backend)."""
    return [obj for obj in (inner, getattr(inner, "session", None)) if obj is not None]


def _already_served(inner) -> bool:
    """Whether the inner backend or its session served a block in this process: through this
    module, or directly through Stage B (its own record of served backends). An object that cannot
    be weakly referenced cannot be tracked, so it cannot be shown fresh: it counts as served."""
    from experiments.safety_decision_policy import controller

    stage_b = getattr(controller, "_SERVED_BACKENDS", ())
    for obj in _warm(inner):
        try:
            weakref.ref(obj)
        except TypeError:
            return True
        if obj in _SERVED or obj in stage_b:
            return True
    return False


def _attempt_dirs(root: Path) -> list[Path]:
    return sorted(p for pattern in _ATTEMPT_GLOBS for p in root.glob(pattern) if p.is_dir())


def study_attempts(root: Path) -> list[Path]:
    """Attempt folders whose after-call receipt exists: units."""
    return [p for p in _attempt_dirs(root) if (p / "receipt.json").is_file()]


def open_attempts(root: Path) -> list[Path]:
    """Attempt folders with ``started.json`` and no receipt: in flight, or lost with their process."""
    return [p for p in _attempt_dirs(root) if (p / "started.json").is_file() and not (p / "receipt.json").exists()]


def study_records(root: Path) -> list[str]:
    """The study's write-once record files (relative names), with ``started.json`` of every
    attempt still in flight."""
    names = {p.relative_to(root).as_posix() for pattern in _RECORD_GLOBS for p in root.glob(pattern) if p.is_file()}
    names |= {(p / "started.json").relative_to(root).as_posix() for p in open_attempts(root)}
    return sorted(names)


class StudyBackup:
    """Off-pod copies of one Stage B study tree (module doc). ``prepared_dir`` (and the engine
    source) are acknowledged first when the study runs the real engine. The vault must not reveal
    paths in its logs."""

    def __init__(self, vault: Vault, root: str | Path, *, prepared_dir: str | Path | None = None,
                 code_root: str | Path | None = None) -> None:
        if vault.reveal_paths:
            raise DurabilityError("a Stage B vault must not log recorded paths: folder names reveal chosen arms")
        self.vault, self.root = vault, Path(root).resolve()
        self.prepared_dir = None if prepared_dir is None else Path(prepared_dir).resolve()
        self.code_root = None if code_root is None else Path(code_root).resolve()
        self._stored: set[str] = set()
        self._acknowledged: set[str] = set()
        self._latest: Path | None = None
        self._pinned = False

    def _pins_ready(self) -> bool:
        if not self._pinned:
            local = self.vault.source_map.local
            prepared = self.prepared_dir is None or self.vault.pin(
                "prepared", read_manifest(local(str(self.prepared_dir)))[1]) is not None
            code = self.code_root is None or self.vault.pin(
                "code", code_identity_of(local(str(self.code_root)))["sha256"]) is not None
            self._pinned = prepared and code
        return self._pinned

    def _pins(self) -> None:
        if self._pins_ready():
            return
        if self.prepared_dir is not None:
            self.vault.acknowledge(prepared_unit(str(self.prepared_dir), self.vault.source_map))
        if self.code_root is not None:
            self.vault.acknowledge(code_unit(str(self.code_root), self.vault.source_map))
        self._pinned = True

    def _record_stored(self, name: str) -> bool:
        if name in self._stored:
            return True
        try:
            self.vault.check_ack("record", str(self.root), sha256_file(self.root / name), name)
        except VerificationFailed:
            return False
        self._stored.add(name)
        return True

    def _seal(self, attempt: Path) -> tuple[str, str, str]:
        return "attempt", str(attempt), sha256_file(attempt / "receipt.json")

    def _is_acknowledged(self, attempt: Path) -> bool:
        if str(attempt) in self._acknowledged:
            return True
        try:
            self.vault.check_ack(*self._seal(attempt))
        except VerificationFailed:
            return False
        self._acknowledged.add(str(attempt))
        return True

    def pending(self) -> dict:
        """What is on the worker and not yet acknowledged off-pod: the pinned inputs, record files
        and receipted attempts."""
        return {"pins": not self._pins_ready(),
                "records": [n for n in study_records(self.root) if not self._record_stored(n)],
                "attempts": [str(p) for p in study_attempts(self.root) if not self._is_acknowledged(p)]}

    def previous(self) -> list[tuple[str, str, str]]:
        """For the gate: every receipted attempt not known to be acknowledged, and the latest one
        again (its acknowledgement is read back from the destination at every dispatch)."""
        attempts = study_attempts(self.root)
        check = [p for p in attempts if str(p) not in self._acknowledged]
        if self._latest is not None and self._latest in attempts and self._latest not in check:
            check.append(self._latest)
        return [self._seal(p) for p in check]

    def open_attempt(self, attempt_dir: str | Path) -> None:
        """Put the new attempt's ``started.json`` off-pod before its work starts, so the attempt
        survives as a catalogued, lost attempt if the worker disappears."""
        attempt_dir = Path(attempt_dir).resolve()
        name = (attempt_dir / "started.json").relative_to(self.root).as_posix()
        self.vault.acknowledge(record_unit(str(self.root), name, self.vault.source_map))
        self._stored.add(name)
        self._latest = attempt_dir
        self.vault.journal.append("attempt-open", namespace=self.vault.namespace, path_sha256=path_id(str(attempt_dir)))

    def settle(self) -> dict:
        """Copy and acknowledge everything pending, then snapshot the registry and the journal.
        Raises on failure."""
        self._pins()
        pending = self.pending()
        for name in pending["records"]:
            self.vault.acknowledge(record_unit(str(self.root), name, self.vault.source_map))
            self._stored.add(name)
        for attempt in pending["attempts"]:
            self.vault.acknowledge(attempt_unit(attempt, self.vault.source_map))
            self._acknowledged.add(attempt)
        for path in (self.root / "registry.jsonl", Path(self.vault.journal.path).resolve()):
            if path.is_file():
                self.vault.snapshot_append(str(path))
        return {"records": len(pending["records"]), "attempts": len(pending["attempts"])}


def _fresh(spec: dict) -> bool:
    """A run operation that starts a trajectory (no ``resume_from``): the engine registers a claim."""
    return spec.get("kind") in RUN_KINDS and "resume_from" not in (spec.get("depends_on") or {})


class GatedBackend:
    """A Stage B backend that dispatches an operation only through the gate (module doc).
    ``needs_seconds(spec)`` optionally gives an operation's planned seconds for the lease check."""

    def __init__(self, inner, backup: StudyBackup, gate: DispatchGate, worker: str, *,
                 needs_seconds: Callable[[dict], float] | None = None) -> None:
        self.inner, self.backup, self.gate, self.worker = inner, backup, gate, worker
        self.needs_seconds = needs_seconds or (lambda spec: 0.0)
        self._blocked: str | None = None
        self._inside_attempt = False

    def __getattr__(self, name: str):
        return getattr(self.inner, name)

    def clock(self) -> float:
        return self.inner.clock()

    def _settle(self) -> None:
        try:
            self.backup.settle()
            self._blocked = None
        except DurabilityError as exc:
            self._blocked = type(exc).__name__

    def sync(self) -> None:
        self.inner.sync()
        if self._inside_attempt:     # the barrier that ends an attempt's timer: nothing is added there
            self._inside_attempt = False
            return
        self._settle()

    def verify(self, receipt: dict, spec: dict) -> None:
        self._settle()
        return self.inner.verify(receipt, spec)

    def _claim_guard(self, spec: dict) -> None:
        registry = getattr(self.inner, "registry", None)
        if registry is None or not _fresh(spec):
            return
        key = trajectory_key(self.inner.manifest_sha256, self.inner.recipe, spec["split"], spec["arm"], spec["seed"],
                             spec["role"])
        live = [row for row in read_jsonl(registry)
                if row["key"] == key and not (Path(row["run_dir"]) / ERROR).exists()]
        if live:
            raise GateRefused("an earlier start of this trajectory holds its registry claim without a failure "
                              "record (a lost attempt); declare it lost first: the claim is never cleared here")

    def execute(self, spec: dict, attempt_dir, sources) -> dict:
        self._inside_attempt = True
        try:
            if self._blocked is not None:
                raise GateRefused(f"the last off-pod copy failed ({self._blocked})")
            self.gate.require(self.worker, self.backup.previous(), self.needs_seconds(spec))
            self._claim_guard(spec)
            self.backup.open_attempt(attempt_dir)
        except RequestRefused:
            raise
        except Exception as exc:  # noqa: BLE001 - only a refusal may leave the gate (module doc)
            raise RequestRefused(f"{spec['op_id']}: dispatch refused before any work: "
                                 f"{exc if isinstance(exc, DurabilityError) else type(exc).__name__}") from exc
        return self.inner.execute(spec, attempt_dir, sources)


def reconcile_claims(root: str | Path, *, registry: str | Path, recipe: dict, manifest_sha256: str,
                     vault: Vault) -> int:
    """After a restore with the real engine: append again the registry claim of every attempt in
    flight that started a trajectory and whose claim the restored registry snapshot predates
    (marked reconstructed). Returns how many were appended. Claims are never removed."""
    claims = {row["run_dir"] for row in read_jsonl(registry)}
    count = 0
    for attempt in open_attempts(Path(root)):
        spec, run = read_json(attempt.parent / "spec.json"), str(attempt / "run")
        if _fresh(spec) and run not in claims:
            started = read_json(attempt / "started.json")
            append_jsonl(registry, {
                "key": trajectory_key(manifest_sha256, recipe, spec["split"], spec["arm"], spec["seed"], spec["role"]),
                "run_dir": run, "replicate_of": None, "retry_after_failures": [], "utc": started.get("start_utc"),
                "reconstructed_by": "experiments.durability from the attempt's started.json: the restored registry "
                                    "snapshot predates this claim"})
            vault.journal.append("claim-reconstructed", namespace=vault.namespace, path_sha256=path_id(str(attempt)))
            count += 1
    return count


def declare_lost_attempt(backup: StudyBackup, attempt_dir: str | Path, *, operator: str, reason: str) -> Path:
    """Tombstone the engine folder of a Stage B attempt whose process was lost: write the
    administrative ``error.txt`` in its ``run/``, which is the engine's preserved-failed-start
    condition. Only an attempt in flight (``started.json``, no receipt) or one Stage B already
    closed as interrupted qualifies, and never one whose run sealed. The registry claim stays; the
    next claim lists this folder under ``retry_after_failures``. The tombstone goes off-pod with
    the attempt (or, when the closed attempt was already acknowledged, as a record of its own)."""
    vault, attempt_dir = backup.vault, Path(attempt_dir).resolve()
    receipt = attempt_dir / "receipt.json"
    if not (attempt_dir / "started.json").is_file() or (
            receipt.exists() and read_json(receipt).get("status") != "interrupted"):
        raise DurabilityError("only an attempt in flight or closed as interrupted can be declared lost")
    if (attempt_dir / "run" / COMPLETE).exists():
        raise DurabilityError("the attempt's run folder is sealed; it is not lost")
    if not operator.strip() or not reason.strip():
        raise DurabilityError("a tombstone names its operator and reason")
    text = f"{TOMBSTONE}Declared lost by {operator} at {iso(vault.clock())}: {reason}\n"
    write_exclusive(attempt_dir / "run" / ERROR, text.encode("utf-8"))
    vault.journal.append("attempt-tombstoned", namespace=vault.namespace, path_sha256=path_id(str(attempt_dir)),
                         operator=operator, reason=reason)
    if receipt.exists() and backup._is_acknowledged(attempt_dir):
        name = (attempt_dir / "run" / ERROR).relative_to(backup.root).as_posix()
        vault.acknowledge(record_unit(str(backup.root), name, vault.source_map))
    return attempt_dir / "run" / ERROR


def run_block_gated(study_factory: Callable[[GatedBackend], object], block: int, *, inner, backup: StudyBackup,
                    gate: DispatchGate, worker: str, needs_seconds: Callable[[dict], float] | None = None) -> dict:
    """The administrative entrypoint for one block: refuse unless the study is settled and the
    lease valid, run ``Study.run_block(block)`` on the gated backend, then settle what the block
    wrote last (its result and session end record). ``study_factory(backend)`` builds the ``Study``
    exactly as ``run-block`` does, with the gated backend in place of the engine backend.

    The study must be settled *before* this call, in a separate administrative step
    (``StudyBackup.settle``): time spent here before the block starts would enter the session's
    start record. One block per process: an inner backend, or its engine ``Session``, that already
    served a block in this process is refused before anything is written (module doc)."""
    if _already_served(inner):
        raise GateRefused("this backend (or its engine session) already served a block in this process, or cannot "
                          "be tracked: its setup would be unmeasured but labelled measured; run one block per process")
    unsettled = backup.pending()
    if unsettled["pins"] or unsettled["records"] or unsettled["attempts"]:
        raise GateRefused("the study holds pinned inputs, records or attempts that are not off-pod; settle it first")
    gate.require(worker, backup.previous())
    backend = GatedBackend(inner, backup, gate, worker, needs_seconds=needs_seconds)
    study = study_factory(backend)
    for obj in _warm(inner):
        _SERVED.add(obj)
    try:
        result = study.run_block(block)
    except BaseException:
        study.close()
        with contextlib.suppress(DurabilityError):   # keep the controller's own error; the gate refuses later
            backup.settle()
        raise
    study.close()
    backup.settle()
    return result
