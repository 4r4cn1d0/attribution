"""Fakes and builders for the recovery-safeguard tests (ENGINEERING FIXTURES): a fake provider
with scripted readings, a manual clock, faulty destinations, and a small "pod" with real sealed
engine units made by the engine's CPU fixtures. None of this stands for a provider's real
behaviour or for a scientific result."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from experiments.durability.admission import (BALANCE_KIND, AdmissionController, AdmissionPolicy, BalanceReading,
                                              Provider, RateCard, StorageDeclaration)
from experiments.durability.backup import Vault
from experiments.durability.common import Journal, TransferError, iso, sha256_file
from experiments.durability.destination import LocalDirectoryDestination
from experiments.durability.gate import DispatchGate

T0 = dt.datetime(2026, 10, 3, 12, 0, 0, tzinfo=dt.timezone.utc)
RATES = {"gpu_per_hour": 1.6, "storage_per_hour": 0.02, "destination_per_hour": 0.01, "currency": "USD"}
POLICY = AdmissionPolicy(max_balance_age_seconds=120.0, max_rate_age_seconds=3600.0, backup_delay_seconds=300.0,
                         shutdown_delay_seconds=120.0, contingency_fraction=0.25, retention_hours=72.0)
RESERVE = (RATES["storage_per_hour"] + RATES["destination_per_hour"]) * POLICY.retention_hours


class ManualClock:
    """A clock the test moves."""

    def __init__(self, now: dt.datetime = T0) -> None:
        self.now = now

    def __call__(self) -> dt.datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += dt.timedelta(seconds=seconds)


def rate_card(clock, **changes) -> RateCard:
    return RateCard(**{**RATES, "as_of_utc": iso(clock()), "source": "fake rate card", **changes})


class FakeProvider(Provider):
    """Scripted provider answers. Each attribute is the answer, or an exception to raise."""

    def __init__(self, clock, *, balance: float = 100.0) -> None:
        self.clock = clock
        self.balance = BalanceReading(balance, "USD", iso(clock()), "fake provider", BALANCE_KIND, True)
        self.rates = rate_card(clock)
        self.liabilities: object = []
        self.persistent: object = {"persistent": True, "volume": "fake-volume-1"}
        self.arm: object = None            # None: confirm the requested time
        self.armed: list[tuple[str, str]] = []

    @staticmethod
    def _answer(value):
        if isinstance(value, Exception):
            raise value
        return value

    def read_balance(self):
        return self._answer(self.balance)

    def read_rates(self, worker):
        return self._answer(self.rates)

    def list_liabilities(self):
        return self._answer(self.liabilities)

    def confirm_persistent(self, path):
        return self._answer(self.persistent)

    def arm_shutdown(self, worker, at_utc):
        if self.arm is not None:
            return self._answer(self.arm)
        self.armed.append((worker, at_utc))
        return {"armed": True, "at_utc": at_utc}


class FaultyDestination(LocalDirectoryDestination):
    """A directory destination with one scripted fault: ``truncate``/``corrupt`` the n-th upload,
    refuse every upload (or every one after the first n), call ``on_upload`` at each upload (a
    destination that takes time), ``crash_on`` an area of ``put_new`` (a process dying at that write) or a
    small reported ``free``."""

    def __init__(self, root, *, truncate: int | None = None, corrupt: int | None = None,
                 crash_on: str | None = None, free: int | None = None, refuse_uploads: bool = False,
                 refuse_after: int | None = None, on_upload=None) -> None:
        super().__init__(root)
        self.on_upload = on_upload
        self.truncate, self.corrupt, self.crash_on, self.free = truncate, corrupt, crash_on, free
        self.refuse_uploads, self.refuse_after = refuse_uploads, refuse_after
        self.uploads = 0

    def free_bytes(self) -> int:
        return super().free_bytes() if self.free is None else self.free

    def upload(self, source, key):
        self.uploads += 1
        if self.on_upload is not None:
            self.on_upload()
        if self.refuse_uploads or (self.refuse_after is not None and self.uploads > self.refuse_after):
            raise TransferError("ENGINEERING FIXTURE: the destination refuses uploads")
        super().upload(source, key)
        path = self._path(key)
        if self.truncate == self.uploads:
            path.write_bytes(path.read_bytes()[:-1])
        if self.corrupt == self.uploads:
            data = bytearray(path.read_bytes())
            data[0] ^= 0xFF
            path.write_bytes(bytes(data))

    def put_new(self, key, data):
        if self.crash_on is not None and f"/{self.crash_on}/" in key:
            raise KeyboardInterrupt(f"ENGINEERING FIXTURE: the process died before writing {self.crash_on}")
        return super().put_new(key, data)


def make_vault(base: Path, namespace: str = "worker-1", *, destination=None, clock=None, **options) -> Vault:
    """A vault over ``base/destination`` with its journal and scratch folder under ``base/admin``."""
    destination = destination or LocalDirectoryDestination(base / "destination")
    kwargs = {"clock": clock} if clock is not None else {}
    return Vault(destination, namespace, journal=Journal(base / "admin" / "journal.jsonl", **kwargs),
                 scratch=base / "admin" / "scratch", **kwargs, **options)


def storage(source: Path, destination, **changes) -> StorageDeclaration:
    fields = {"source_path": str(source), "destination": destination, "required_bytes": 1 << 20,
              "destination_independent_of_gpu_account": True, "destination_retention_days": 30.0,
              "destination_funding": "ENGINEERING FIXTURE: a local directory, no cost",
              "required_retention_days": 14.0}
    return StorageDeclaration(**{**fields, **changes})


def admission(base: Path, provider, clock, journal=None) -> AdmissionController:
    return AdmissionController(base / "admission" / "reservations.jsonl", provider, POLICY, rate_card(clock),
                               journal=journal or Journal(base / "admin" / "journal.jsonl", clock), clock=clock)


def gate_for(vault: Vault, controller: AdmissionController, clock) -> DispatchGate:
    return DispatchGate(vault, controller.current_lease, journal=vault.journal, clock=clock)


def tree_hashes(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): sha256_file(p) for p in sorted(folder.rglob("*")) if p.is_file()}


def run_job(sha: str, recipe: dict, **fields) -> dict:
    """A development run-one job on the engine fixtures (dev split, a0, seed 1101, checkpoint q)."""
    from experiments.safety_selection.config import config_sha256

    job = {"kind": "run-one", "split": "dev", "arm": "a0", "seed": 1101, "role": "development",
           "target_checkpoint": "q", "evaluate_bank": "dev", "manifest_sha256": sha,
           "recipe_sha256": config_sha256(recipe), "code_sha256": None, "resume_from": None, "replicate_of": None,
           "wall_limit_seconds": None}
    job.update(fields)
    return job
