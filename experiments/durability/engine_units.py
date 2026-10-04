"""The administrative unit runner around the engine's ``runner.run_one``.

Insertion point. ``runner.calibrate`` loops over (seed, arm, checkpoint) and calls ``run_one``
once per unit with one ``Session``; nothing between two units can be hooked without editing the
frozen engine. ``UnitRunner.run`` is that loop written outside the engine: the same job
dictionaries, the same ``<name>-a<n>`` attempt folders, the same ``registry.jsonl`` beside them and
one ``Session`` per process, with three additions between units:

1. **before** a unit: the dispatch gate (every earlier local attempt acknowledged off-pod, a lease
   that covers the unit), then an ``attempt-started`` line in the attempt catalogue, copied off-pod
   before any work starts;
2. **after** a unit seals: its acknowledgement (``backup.Vault.acknowledge``) and snapshots of the
   registry and the catalogue. The next unit does not start before it;
3. **after** a failure: the engine's preserved failed folder is copied as a failure record and the
   exception propagates. A retry is a new attempt folder with the same seed: the same draw.

The **attempt catalogue** (``attempts.jsonl`` in the administrative folder, outside every run
folder) is what survives when directories do not. On start, ``reconcile`` classifies every
catalogued attempt without an outcome: sealed (the process died between the seal and the catalogue
line), failed (the engine left ``error.txt``), else **lost**: its start time, lease and rate are
kept, its cost is recorded as unknown (never zero) and its number is never reused.

**Registry semantics** (``jobs.claim_trajectory``). A fresh start (no ``resume_from``) appends a
claim for (data, training identity, split, arm, seed, role); a second fresh start of that key is
refused while any earlier claim's folder has no ``error.txt``. A continuation claims nothing. So:

- a lost *continuation* is simply rerun as the next attempt from its sealed, reverified
  predecessor;
- a lost *fresh start* still holds its claim, and a killed process cannot write ``error.txt``. The
  engine then refuses the rerun, correctly: nothing here clears, edits or replaces a claim. If
  the restored registry snapshot predates the lost claim, ``reconcile`` appends it again from the
  catalogue (marked reconstructed) so the claim is not silently dropped. The rerun needs an explicit
  ``declare_lost``: an operator-named tombstone, ``error.txt`` with an administrative statement in
  the lost attempt's folder, which is exactly the engine's "preserved failed start" condition. The
  engine's next claim then lists the lost folder under ``retry_after_failures``: the same draw, the
  lost attempt and its cost kept. Without the tombstone ``run`` refuses before launching anything.

Only run-one units are launched here (calibration and trajectory chains). Sealed folders of any
kind made elsewhere can be acknowledged with ``acknowledge_sealed_tree``.

**Trees made without this runner.** A tree written by the engine's own ``calibrate`` (for
example one pulled from a pod that ran without these safeguards) has no catalogue, and its job
files and registry may spell paths relative to the study root. ``adopt`` catalogues what such a
tree holds for the planned units: sealed and failed attempts as they are, and every attempt that
neither sealed nor failed, or that the registry claims but whose folder is missing, as **lost**
with an unknown start and cost. From then on the rules above apply to them. The process must run
with the study root as its working directory, so that the engine's own relative paths resolve.

``before_unit`` and ``after_unit`` are optional callbacks around a unit that has to run (not a
reused one): before the gate is asked, and after the unit's acknowledgement or failure. The pod
worker uses them to obtain a lease for the unit and to keep it alive while the unit runs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from experiments.safety_selection.common import PACKAGE_DIR, code_identity
from experiments.safety_selection.jobs import trajectory_key
from experiments.safety_selection.ledger import COMPLETE, ERROR, STATUS, read_complete
from experiments.safety_selection.prepare import read_manifest

from .backup import Vault
from .common import (Clock, DurabilityError, LostAttemptUnresolved, VerificationFailed, append_jsonl, iso,
                     read_json, read_jsonl, sha256_file, utc_clock, write_exclusive)
from .gate import DispatchGate
from .units import code_unit, failed_run_unit, is_sealed, prepared_unit, run_unit

__all__ = ["UnitSpec", "UnitRunner", "acknowledge_sealed_tree", "TOMBSTONE"]

TOMBSTONE = ("ADMINISTRATIVE TOMBSTONE written by experiments.durability, not an engine traceback.\n"
             "This attempt started and its process was lost before the run sealed or failed; the engine never "
             "wrote this file.\nIt is declared a preserved failed start so that a retry with the same seed (the "
             "same scientific draw) can be registered; the attempt and its cost stay in the attempt catalogue.\n")


@dataclass(frozen=True)
class UnitSpec:
    """One planned run-one unit. ``name`` is its folder stem (attempts are ``<name>-a<n>``);
    ``resume_from`` names the earlier unit of the same plan it continues."""

    name: str
    split: str
    arm: str
    seed: int
    role: str
    target_checkpoint: str
    evaluate_bank: str | None
    resume_from: str | None = None
    planned_seconds: float = 0.0
    allow_hidden: bool = False


def _seal_of(folder: Path) -> tuple[str, str] | None:
    """(unit kind, seal hash) of a local attempt folder that sealed or failed, else None."""
    if (folder / COMPLETE).is_file():
        return "run", sha256_file(folder / COMPLETE)
    if (folder / ERROR).is_file():
        return "failed-run", sha256_file(folder / ERROR)
    return None


class UnitRunner:
    """See the module doc. ``out_root`` and ``prepared_dir`` are used as absolute paths: they are
    the recorded layout a restore must reproduce. ``admin_dir`` holds the catalogue and must lie
    outside every run folder."""

    def __init__(self, *, session, prepared_dir: str | Path, out_root: str | Path, admin_dir: str | Path,
                 vault: Vault, gate: DispatchGate, worker: str, clock: Clock = utc_clock,
                 code_root: str | Path | None = None, before_unit: Callable[[UnitSpec], None] | None = None,
                 after_unit: Callable[[UnitSpec], None] | None = None) -> None:
        self.session, self.vault, self.gate, self.worker, self.clock = session, vault, gate, worker, clock
        self.before_unit, self.after_unit = before_unit, after_unit
        self.prepared_dir, self.out_root = Path(prepared_dir).resolve(), Path(out_root).resolve()
        self.admin_dir = Path(admin_dir).resolve()
        if self.admin_dir == self.out_root or self.out_root in self.admin_dir.parents:
            raise DurabilityError("the administrative folder must lie outside the run folders")
        self.code_root = Path(code_root).resolve() if code_root else PACKAGE_DIR.parent
        self.registry = self.out_root / "registry.jsonl"
        self.catalogue = self.admin_dir / "attempts.jsonl"
        _, self.manifest_sha256 = read_manifest(self.prepared_dir)
        self.code_sha256 = code_identity()["sha256"]

    # ----- catalogue -----------------------------------------------------------------

    def _note(self, event: str, **fields: object) -> None:
        append_jsonl(self.catalogue, {"event": event, "utc": iso(self.clock()), "worker": self.worker, **fields})

    def attempts(self) -> list[dict]:
        """Every catalogued attempt with its latest state: started, sealed, failed, lost (and
        whether a lost one was tombstoned)."""
        out: dict[tuple, dict] = {}
        for row in read_jsonl(self.catalogue):
            key = (row.get("unit"), row.get("attempt"))
            if row["event"] == "attempt-started":
                out[key] = {**row, "state": "started", "tombstoned": False}
            elif row["event"] in ("attempt-sealed", "attempt-failed", "attempt-lost") and key in out:
                out[key].update(state=row["event"][len("attempt-"):], outcome=row)
            elif row["event"] == "attempt-tombstoned" and key in out:
                out[key]["tombstoned"] = True
        return list(out.values())

    def _snapshot(self) -> None:
        """Registry, catalogue and journal off-pod, each as an extension of its last snapshot."""
        for path in (self.registry, self.catalogue, self.vault.journal.path):
            if Path(path).is_file():
                self.vault.snapshot_append(str(Path(path).resolve()))

    # ----- pins, reconciliation ------------------------------------------------------

    def prepare(self) -> None:
        """Acknowledge the pinned inputs once: the prepared data and the engine source."""
        if self.vault.pin("prepared", self.manifest_sha256) is None:
            self.vault.acknowledge(prepared_unit(str(self.prepared_dir), self.vault.source_map))
        if self.vault.require_code and self.vault.pin("code", self.code_sha256) is None:
            self.vault.acknowledge(code_unit(str(self.code_root), self.vault.source_map))

    def reconcile(self) -> list[dict]:
        """Classify every catalogued attempt without an outcome (module doc), restore dropped
        registry claims of lost fresh starts and acknowledge any local sealed or failed attempt
        that is not yet acknowledged. Returns the attempts found lost now."""
        found = []
        for attempt in self.attempts():
            folder = Path(attempt["run_dir"])
            if attempt["state"] == "started":
                seal = _seal_of(folder)
                ident = {"unit": attempt["unit"], "attempt": attempt["attempt"], "run_dir": attempt["run_dir"]}
                if seal and seal[0] == "run" and is_sealed(folder):
                    self._note("attempt-sealed", **ident, complete_sha256=seal[1], recovered=True)
                elif seal and seal[0] == "failed-run":
                    self._note("attempt-failed", **ident, error_type="recorded by the engine", recovered=True)
                else:
                    last = None
                    if (folder / STATUS).is_file():
                        try:
                            last = read_json(folder / STATUS)
                        except ValueError:
                            last = None
                    lost = {**ident, "start_utc": attempt["utc"], "lease": attempt.get("lease"),
                            "rate_per_hour": attempt.get("rate_per_hour"), "currency": attempt.get("currency"),
                            "folder_present": folder.is_dir(),
                            "last_seen_utc": (last or {}).get("updated_utc"),
                            "known_seconds": (last or {}).get("elapsed_s"),
                            "cost": "unknown: the attempt billed from its start until the worker stopped; "
                                    "never zero, never imputed"}
                    self._note("attempt-lost", **lost)
                    found.append(lost)
        claims = {str(Path(row["run_dir"]).resolve()) for row in read_jsonl(self.registry)}
        for attempt in self.attempts():
            if (attempt["state"] == "lost" and attempt["fresh_start"] and attempt.get("key") is not None
                    and str(Path(attempt["run_dir"]).resolve()) not in claims):
                append_jsonl(self.registry, {"key": attempt["key"], "run_dir": attempt["run_dir"],
                                             "replicate_of": None, "retry_after_failures": [],
                                             "utc": attempt["utc"],
                                             "reconstructed_by": "experiments.durability from the attempt catalogue: "
                                                                 "the restored registry snapshot predates this claim"})
                self._note("claim-reconstructed", unit=attempt["unit"], attempt=attempt["attempt"],
                           run_dir=attempt["run_dir"])
        for attempt in self.attempts():
            folder = Path(attempt["run_dir"])
            seal = _seal_of(folder) if attempt["state"] in ("sealed", "failed") else None
            if seal is not None:
                try:
                    self.vault.check_ack(seal[0], str(folder), seal[1])
                except VerificationFailed:
                    make = run_unit if seal[0] == "run" else failed_run_unit
                    self.vault.acknowledge(make(str(folder), self.vault.source_map))
        self._snapshot()
        return found

    def adopt(self, units: Sequence[UnitSpec]) -> list[dict]:
        """Catalogue the attempts of the planned units that exist in the tree, or are claimed in
        its registry, without a catalogue line (module doc). Returns what was adopted."""
        known = {(a["unit"], a["attempt"]) for a in self.attempts()}
        claimed = {str(Path(row["run_dir"]).resolve()): row for row in read_jsonl(self.registry)}
        adopted = []
        for spec in units:
            stem = f"{spec.name}-a"
            numbers = {int(p.name[len(stem):]) for p in self.out_root.glob(stem + "*") if p.name[len(stem):].isdigit()}
            numbers |= {int(Path(d).name[len(stem):]) for d in claimed
                        if Path(d).parent == self.out_root and Path(d).name.startswith(stem)
                        and Path(d).name[len(stem):].isdigit()}
            for number in sorted(numbers):
                if (spec.name, number) in known:
                    continue
                folder = self.out_root / f"{spec.name}-a{number}"
                claim = claimed.get(str(folder))
                fresh = spec.resume_from is None
                ident = {"unit": spec.name, "attempt": number, "run_dir": str(folder)}
                self._note("attempt-started", **ident, fresh_start=fresh, key=(claim or {}).get("key") if fresh else None,
                           lease=None, rate_per_hour=None, currency=None, resume_from=None,
                           adopted="found in the tree without a catalogue line: it was not started by this runner; "
                                   "its start time, lease and rate are unknown")
                seal = _seal_of(folder)
                if seal and seal[0] == "run" and is_sealed(folder):
                    self._note("attempt-sealed", **ident, complete_sha256=seal[1], recovered=True)
                    state = "sealed"
                elif seal and seal[0] == "failed-run":
                    self._note("attempt-failed", **ident, error_type="recorded by the engine", recovered=True)
                    state = "failed"
                else:
                    self._note("attempt-lost", **ident, start_utc=None, lease=None, rate_per_hour=None, currency=None,
                               folder_present=folder.is_dir(), last_seen_utc=None, known_seconds=None,
                               cost="unknown: the attempt ran outside this runner; never zero, never imputed")
                    state = "lost"
                adopted.append({**ident, "state": state, "claimed": claim is not None})
        return adopted

    @staticmethod
    def unresolved(attempt: dict) -> bool:
        """An attempt that ended without the engine sealing it or recording its failure: lost, or
        interrupted in a way that let this runner note the failure but not the engine (a signal).
        If it was a fresh start it may still hold its registry claim, which only a tombstone ends."""
        folder = Path(attempt["run_dir"])
        return (attempt["state"] in ("lost", "failed") and not (folder / ERROR).is_file()
                and not (folder / COMPLETE).is_file())

    def declare_lost(self, unit: str, attempt: int, *, operator: str, reason: str) -> Path:
        """Tombstone a lost attempt (module doc): write the administrative ``error.txt`` in its
        folder, creating the folder when the directory itself was lost. Only a catalogued attempt
        that is lost, or failed without the engine's own failure record, can be declared; a sealed
        folder never."""
        match = [a for a in self.attempts() if (a["unit"], a["attempt"]) == (unit, attempt)]
        if not match or not self.unresolved(match[0]):
            raise DurabilityError(f"{unit} attempt {attempt} is not a catalogued lost attempt")
        if not operator.strip() or not reason.strip():
            raise DurabilityError("a tombstone names its operator and reason")
        folder = Path(match[0]["run_dir"])
        if (folder / COMPLETE).exists():
            raise DurabilityError(f"{folder} is sealed; it is not lost")
        text = (f"{TOMBSTONE}Unit {unit}, attempt {attempt}, started {match[0]['utc']}.\n"
                f"Declared lost by {operator} at {iso(self.clock())}: {reason}\n")
        write_exclusive(folder / ERROR, text.encode("utf-8"))
        self._note("attempt-tombstoned", unit=unit, attempt=attempt, run_dir=str(folder), operator=operator,
                   reason=reason)
        self._snapshot()
        return folder / ERROR

    # ----- units ---------------------------------------------------------------------

    def _job(self, spec: UnitSpec, sealed: dict[str, Path]) -> dict:
        if spec.resume_from is not None and spec.resume_from not in sealed:
            raise DurabilityError(f"{spec.name} continues {spec.resume_from}, which is not an earlier sealed unit "
                                  "of this plan")
        # the keys in the order of the engine's own calibration loop
        return {"kind": "run-one", "split": spec.split, "role": spec.role, "evaluate_bank": spec.evaluate_bank,
                "manifest_sha256": self.manifest_sha256, "recipe_sha256": self.session.recipe_sha256,
                "code_sha256": self.code_sha256, "replicate_of": None, "wall_limit_seconds": None,
                "arm": spec.arm, "seed": spec.seed, "target_checkpoint": spec.target_checkpoint,
                "resume_from": str(sealed[spec.resume_from]) if spec.resume_from else None}

    def _numbers(self, spec: UnitSpec) -> list[int]:
        stem = f"{spec.name}-a"
        folders = [int(p.name[len(stem):]) for p in self.out_root.glob(stem + "*") if p.name[len(stem):].isdigit()]
        catalogued = [a["attempt"] for a in self.attempts() if a["unit"] == spec.name]
        return sorted(set(folders) | set(catalogued))

    def _sealed_attempt(self, spec: UnitSpec, job: dict) -> Path | None:
        """The first sealed attempt of the unit, reused only when its stored job and identities are
        the requested ones; a sealed attempt for other science refuses (as ``calibrate`` does)."""
        from experiments.safety_selection.runner import UNIT_KEYS

        for number in self._numbers(spec):
            folder = self.out_root / f"{spec.name}-a{number}"
            if not is_sealed(folder):
                continue
            stored, identity = read_json(folder / "job.json"), read_complete(folder)["identity"]
            wrong = [key for key in UNIT_KEYS if stored.get(key) != job[key]]
            have, want = stored.get("resume_from"), job["resume_from"]
            if (have is None) != (want is None) or (have is not None and Path(have).resolve() != Path(want).resolve()):
                wrong.append("resume_from")
            wrong += [f"identity.{key}" for key in ("manifest_sha256", "recipe_sha256", "code_sha256")
                      if identity.get(key) != job[key]]
            if wrong:
                raise DurabilityError(f"{folder} is a sealed attempt for different science (differs in {wrong}); "
                                      "it is never reused or mixed")
            return folder
        return None

    def _previous(self) -> list[tuple[str, str, str]]:
        """Every catalogued attempt that sealed or failed and whose folder is on this worker: each
        must be acknowledged before the next unit starts."""
        out = []
        for attempt in self.attempts():
            seal = _seal_of(Path(attempt["run_dir"])) if attempt["state"] in ("sealed", "failed") else None
            if seal is not None:
                out.append((seal[0], attempt["run_dir"], seal[1]))
        return out

    def _launch(self, spec: UnitSpec, job: dict) -> Path:
        from experiments.safety_selection import runner

        lease = self.gate.require(self.worker, self._previous(), spec.planned_seconds)
        fresh = job["resume_from"] is None
        if fresh:
            unresolved = [a for a in self.attempts() if a["unit"] == spec.name and self.unresolved(a)]
            if unresolved:
                raise LostAttemptUnresolved(
                    f"{spec.name}: attempt(s) {[a['attempt'] for a in unresolved]} were lost after claiming the "
                    "trajectory; the registry claim stands until each is declared lost (declare_lost)")
        numbers = self._numbers(spec)
        attempt = (numbers[-1] + 1) if numbers else 1
        folder = self.out_root / f"{spec.name}-a{attempt}"
        key = trajectory_key(self.manifest_sha256, self.session.recipe, spec.split, spec.arm, spec.seed, spec.role)
        ident = {"unit": spec.name, "attempt": attempt, "run_dir": str(folder)}
        self._note("attempt-started", **ident, fresh_start=fresh, key=key if fresh else None, lease=lease.lease,
                   rate_per_hour=lease.rate_per_hour, currency=lease.currency, resume_from=job["resume_from"])
        self._snapshot()   # the attempt is catalogued off-pod before any work
        try:
            runner.run_one(job, prepared_dir=self.prepared_dir, out_dir=folder, session=self.session,
                           allow_hidden=spec.allow_hidden, registry=self.registry)
        except BaseException as exc:
            self._note("attempt-failed", **ident, error_type=type(exc).__name__)
            try:
                if (folder / ERROR).is_file():
                    self.vault.acknowledge(failed_run_unit(str(folder), self.vault.source_map))
                self._snapshot()
            except DurabilityError:
                pass   # the failure record is not off-pod: the gate refuses the next unit
            raise
        self._note("attempt-sealed", **ident, complete_sha256=sha256_file(folder / COMPLETE))
        return folder

    def run(self, units: Sequence[UnitSpec]) -> list[dict]:
        """Run the plan in order (module doc). A sealed unit is reused after its identity check and
        acknowledged if it is not yet; every other unit passes the gate, runs once and is
        acknowledged before the next starts. An engine failure propagates after its record is kept."""
        self.out_root.mkdir(parents=True, exist_ok=True)
        self.admin_dir.mkdir(parents=True, exist_ok=True)
        self.prepare()
        self.reconcile()
        sealed: dict[str, Path] = {}
        report = []
        for spec in units:
            job = self._job(spec, sealed)
            folder = self._sealed_attempt(spec, job)
            reused = folder is not None
            timing = {"launch_seconds": None}
            if not reused and self.before_unit is not None:
                self.before_unit(spec)
            try:
                if folder is None:
                    started = time.monotonic()
                    folder = self._launch(spec, job)
                    timing["launch_seconds"] = time.monotonic() - started
                started = time.monotonic()
                ack = self.vault.acknowledge(run_unit(str(folder), self.vault.source_map))
                self._snapshot()
                timing["acknowledge_seconds"] = time.monotonic() - started
            finally:
                if not reused and self.after_unit is not None:
                    self.after_unit(spec)
            sealed[spec.name] = folder
            report.append({"unit": spec.name, "run_dir": str(folder), "reused": reused, "ack": ack["unit"],
                           "acknowledged_utc": ack["acknowledged_utc"], **timing})
        return report


def acknowledge_sealed_tree(vault: Vault, root: str | Path) -> dict:
    """Acknowledge every sealed run folder directly below a recorded root that is not acknowledged
    yet, dependencies first (a unit whose dependency is not in the vault waits for a later pass).
    For folders sealed by a process this package did not launch. Returns the unit ids and what
    could not be acknowledged (with the error class)."""
    local = vault.source_map.local(str(root))
    pending = sorted(str(Path(str(root)) / p.name) for p in local.iterdir() if (p / COMPLETE).is_file())
    done, failed = [], {}
    progress = True
    while pending and progress:
        progress, later = False, []
        for folder in pending:
            try:
                done.append(vault.acknowledge(run_unit(folder, vault.source_map))["unit"])
                progress = True
                failed.pop(folder, None)
            except DurabilityError as exc:
                failed[folder] = type(exc).__name__
                later.append(folder)
        pending = later
    return {"acknowledged": done, "not_acknowledged": failed}
