"""Balance and runway admission, leases, and the storage declaration (stdlib only).

No provider API is assumed here. ``Provider`` is the interface the funded validation must
implement and check against the real service; ``UnconfiguredProvider`` is the
default and refuses every call, so nothing can be admitted on a deployment that has not been
configured. ``runpod_provider.RunPodProvider`` is the real adapter for RunPod; it is built only
from explicit configuration, and it too refuses whatever it cannot confirm (the provider-side
shutdown above all). Whatever a provider raises while admission asks it something is a refusal.
Tests use fakes.

**Admission formula.** With a balance reading ``B`` taken at ``t0`` and admission at ``now``:

    age      = now - t0                          (0 <= age <= max_balance_age)
    horizon  = increment + backup_delay + shutdown_delay
    need     = worker_rate * (age + horizon) * (1 + contingency)
    held     = sum of the reservations of every unreleased lease of another worker
               whose reservation ends after t0
    reserves = sum over every OTHER worker of the retention reserve of its latest lease
               (released and superseded leases included) whose retention window ends after t0
    unleased = sum over liabilities of no leased worker and not this worker:
               (rate * (age + horizon) + fixed_amount) * (1 + contingency)
    available = B - held - reserves - unleased - retention_reserve
    admit  iff  available >= need

``worker_rate`` is the worker's GPU plus storage rate per hour. ``age`` charges what the account
spent since the reading; ``backup_delay`` and ``shutdown_delay`` keep the worker funded through
its last off-pod copy and its provider-side shutdown; ``retention_reserve`` (at least the storage
rates times the declared retention hours) keeps the durable source and the destination alive
after compute stops. Every lease records its reserve and the end of its retention window (the end
of its reservation plus the retention hours), so a second worker cannot spend the first worker's
reserve: one reserve per worker is held, its latest lease's (a renewal replaces, it does not add),
and it stays held after that lease is released or superseded until its window ends, because the
volume still bills. The formula is conservative: a lease's whole reservation is held although part
of it may already be reflected in ``B``.

**Liabilities of leased workers.** A liability that names a worker with an unreleased lease (or
the worker being admitted) is not charged again: its lease is assumed to cover everything that
worker bills. That holds only if the worker's rate card is complete. A second volume or GPU of
that worker that is not in its rate card would be under-counted; the funded validation must check
that the provider's liabilities per worker equal the rate card.

**Fail closed.** Admission is refused when: the provider, a reading or the liability list is
unavailable; the balance is not an explicitly recognized prepaid balance (pod billing totals and
removed spending caps are not balances); a number is missing, negative or non-finite; currencies
differ; a reading is stale or from the future; the provider's current rates differ from the rates
the plan was costed with (a changed rate needs a new plan); the storage declaration fails; the
provider cannot arm a shutdown at the end of the reservation; or the runway is insufficient.

**Serialization.** Reservations live in one append-only ledger read and extended under an
exclusive file lock, so two workers cannot both reserve the same runway. A ledger row that cannot
be read as a lease or a release (malformed, or written by an older format) refuses: admission and
the gate fail closed with ``AdmissionRefused``, never with an unhandled error. A lease expires at
``now + increment``; working past it needs a new admission (a renewal supersedes the worker's
previous lease). Stopping Python does not stop billing: the shutdown at the end of the reservation
is the provider's, armed through ``Provider.arm_shutdown`` before the lease is returned.
"""

from __future__ import annotations

import abc
import datetime as dt
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from .common import (AdmissionRefused, Clock, DurabilityError, Journal, NotConfigured, StorageRefused, append_jsonl,
                     iso, locked, parse_utc, read_jsonl, token, utc_clock)
from .destination import Destination

__all__ = ["BALANCE_KIND", "BalanceReading", "RateCard", "Liability", "Provider", "UnconfiguredProvider",
           "AdmissionPolicy", "StorageDeclaration", "check_storage", "Lease", "AdmissionController"]

BALANCE_KIND = "prepaid-credit-balance"


@dataclass(frozen=True)
class BalanceReading:
    """A balance as the provider reports it. ``kind`` must be ``BALANCE_KIND`` and ``recognized``
    true: someone accountable confirmed that this number is the spendable prepaid balance (not a
    billing total, a spending cap or an estimate)."""

    amount: float
    currency: str
    as_of_utc: str
    source: str
    kind: str
    recognized: bool


@dataclass(frozen=True)
class RateCard:
    """Hourly rates of one worker: its GPU, its durable source storage and the destination."""

    gpu_per_hour: float
    storage_per_hour: float
    destination_per_hour: float
    currency: str
    as_of_utc: str
    source: str

    @property
    def worker_per_hour(self) -> float:
        return self.gpu_per_hour + self.storage_per_hour

    def rates(self) -> tuple:
        return (self.gpu_per_hour, self.storage_per_hour, self.destination_per_hour, self.currency)


@dataclass(frozen=True)
class Liability:
    """Anything else that draws on the same balance: another pod, a volume, a pending charge.
    ``worker`` names the worker it belongs to (its lease then covers it), else None."""

    name: str
    rate_per_hour: float
    state: str                 # "active" or "pending"
    fixed_amount: float = 0.0
    worker: str | None = None


class Provider(abc.ABC):
    """What admission needs from the compute provider. Implementations belong to the funded
    validation; none is assumed here."""

    @abc.abstractmethod
    def read_balance(self) -> BalanceReading: ...

    @abc.abstractmethod
    def read_rates(self, worker: str) -> RateCard: ...

    @abc.abstractmethod
    def list_liabilities(self) -> list[Liability]: ...

    @abc.abstractmethod
    def confirm_persistent(self, path: str) -> dict:
        """``{"persistent": True, "volume": <id>}`` only when the provider confirms that the path
        is on storage that survives a stop, restart or termination of the worker."""

    @abc.abstractmethod
    def arm_shutdown(self, worker: str, at_utc: str) -> dict:
        """Arm a provider-side stop of the worker at the given time; ``{"armed": True, "at_utc":
        ...}`` when the provider confirms it."""


class UnconfiguredProvider(Provider):
    """The only adapter shipped: every call fails closed."""

    def _refuse(self, *args: object, **kwargs: object):
        raise NotConfigured("the provider adapter is not configured: balance, rates, liabilities, persistence and "
                            "timed shutdown wait for the funded one-worker validation")

    read_balance = read_rates = list_liabilities = confirm_persistent = arm_shutdown = _refuse


@dataclass(frozen=True)
class AdmissionPolicy:
    """The stated margins: how old a reading may be, the delays kept funded after the work, the
    contingency fraction and the retention the reserve must cover."""

    max_balance_age_seconds: float
    max_rate_age_seconds: float
    backup_delay_seconds: float
    shutdown_delay_seconds: float
    contingency_fraction: float
    retention_hours: float
    clock_skew_seconds: float = 5.0


@dataclass(frozen=True)
class StorageDeclaration:
    """The durable source and the independent destination, with the declared facts that cannot be
    checked from inside a worker."""

    source_path: str
    destination: Destination
    required_bytes: int
    destination_independent_of_gpu_account: bool
    destination_retention_days: float
    destination_funding: str           # who pays for the destination and until when (a statement)
    required_retention_days: float


def check_storage(declaration: StorageDeclaration, provider: Provider) -> dict:
    """Refuse unless the provider confirms the source path is persistent, and the destination is
    declared independent of the GPU account, funded and retained long enough, is usable (a probe
    object written, read back and removed) and has the required free space. Returns the record."""
    try:
        confirmation = provider.confirm_persistent(declaration.source_path)
    except Exception as exc:  # noqa: BLE001 - whatever the provider could not answer is not a confirmation
        raise StorageRefused(f"the source is not confirmed persistent: {_why(exc)}") from exc
    if not (isinstance(confirmation, dict) and confirmation.get("persistent") is True and confirmation.get("volume")):
        raise StorageRefused("the provider did not confirm that the source path is on persistent storage")
    source = Path(declaration.source_path)
    if not source.is_dir():
        raise StorageRefused(f"the declared source {source} is not a folder")
    if declaration.destination_independent_of_gpu_account is not True:
        raise StorageRefused("the destination is not declared independent of the GPU account")
    if not isinstance(declaration.destination_funding, str) or not declaration.destination_funding.strip():
        raise StorageRefused("the destination's funding is not declared")
    days, required = declaration.destination_retention_days, declaration.required_retention_days
    if not all(_number(v) and v >= 0 for v in (days, required)) or days < required:
        raise StorageRefused("the destination's declared retention is missing or shorter than required")
    described = declaration.destination.describe()
    location = described.get("location")
    if location is not None:
        inside = Path(location).resolve()
        if inside == source.resolve() or source.resolve() in inside.parents or inside in source.resolve().parents:
            raise StorageRefused("the destination lies inside the source (or the source inside it): not independent")
    try:
        declaration.destination.probe()
        free = declaration.destination.free_bytes()
    except DurabilityError as exc:
        raise StorageRefused(f"the destination is not usable: {exc}") from exc
    if not _number(declaration.required_bytes) or free < declaration.required_bytes:
        raise StorageRefused(f"the destination has {free} free bytes, fewer than the required "
                             f"{declaration.required_bytes}")
    return {"source": {"path": declaration.source_path, "persistent": True, "volume": confirmation["volume"]},
            "destination": {**described, "free_bytes": free, "required_bytes": declaration.required_bytes,
                            "independent_of_gpu_account": True, "retention_days": days,
                            "funding": declaration.destination_funding}}


def _why(exc: Exception) -> str:
    """A refusal's reason from a provider error: our own errors by message, anything else by class."""
    return str(exc) if isinstance(exc, DurabilityError) else type(exc).__name__


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


@dataclass(frozen=True)
class Lease:
    """Permission to dispatch work on one worker until ``expires_utc``; the reservation runs to
    ``reserved_until_utc`` (the backup and shutdown delays), when the provider stops the worker.
    ``retention_reserve`` stays set aside for the worker's storage until ``retention_until_utc``,
    also after the lease is released or superseded."""

    lease: str
    worker: str
    granted_utc: str
    expires_utc: str
    reserved_until_utc: str
    reserved_amount: float
    currency: str
    rate_per_hour: float
    balance_as_of_utc: str
    retention_reserve: float
    retention_until_utc: str

    def covers(self, now: dt.datetime, needs_seconds: float = 0.0) -> bool:
        return now + dt.timedelta(seconds=needs_seconds) <= parse_utc(self.expires_utc)


class AdmissionController:
    """Admission over one shared reservation ledger (module doc). ``planned_rates``: the rates the
    work plan was costed with; the provider's current rates must equal them."""

    def __init__(self, ledger: str | Path, provider: Provider, policy: AdmissionPolicy, planned_rates: RateCard, *,
                 journal: Journal, clock: Clock = utc_clock) -> None:
        self.ledger, self.provider, self.policy = Path(ledger), provider, policy
        self.planned_rates, self.journal, self.clock = planned_rates, journal, clock
        self._lock = self.ledger.with_name(self.ledger.name + ".lock")

    # ----- ledger --------------------------------------------------------------------

    def _ledger(self) -> list[tuple[Lease, bool]]:
        """Every lease in the ledger, in order, with whether it was released. A row that is not a
        well-formed lease or release makes the whole ledger unreadable: ``AdmissionRefused``."""
        entries: dict[str, list] = {}
        try:
            for row in read_jsonl(self.ledger):
                if row.get("event") == "lease":
                    lease = Lease(**{k: v for k, v in row.items() if k != "event"})
                    texts = (lease.lease, lease.worker, lease.currency)
                    amounts = (lease.reserved_amount, lease.rate_per_hour, lease.retention_reserve)
                    if not all(isinstance(t, str) and t for t in texts) or not all(_number(a) and a >= 0 for a in amounts):
                        raise ValueError("a lease with a missing name or amount")
                    for stamp in (lease.granted_utc, lease.expires_utc, lease.reserved_until_utc,
                                  lease.retention_until_utc, lease.balance_as_of_utc):
                        parse_utc(stamp)
                    entries[lease.lease] = [lease, False]
                elif row.get("event") == "release" and isinstance(row.get("lease"), str):
                    if row["lease"] in entries:
                        entries[row["lease"]][1] = True
                else:
                    raise ValueError("a row that is neither a lease nor a release")
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise AdmissionRefused(f"the reservation ledger is unreadable ({type(exc).__name__}): nothing is "
                                   "admitted or dispatched on it") from None
        return [(lease, released) for lease, released in entries.values()]

    def _leases(self) -> dict[str, Lease]:
        """Every unreleased lease in the ledger, by lease id."""
        return {lease.lease: lease for lease, released in self._ledger() if not released}

    def current_lease(self, worker: str) -> Lease | None:
        """The worker's latest unreleased lease (it may have expired: see ``Lease.covers``)."""
        with locked(self._lock):
            mine = [lease for lease in self._leases().values() if lease.worker == worker]
        return max(mine, key=lambda lease: lease.granted_utc, default=None)

    def release(self, lease: str, reason: str) -> None:
        with locked(self._lock):
            if lease in self._leases():
                append_jsonl(self.ledger, {"event": "release", "lease": lease, "reason": reason,
                                           "utc": iso(self.clock())})
        self.journal.append("lease-released", lease=lease, reason=reason)

    # ----- admission -----------------------------------------------------------------

    def _refuse(self, worker: str, why: str) -> None:
        self.journal.append("admission-refused", worker=worker, reason=why[:380])
        raise AdmissionRefused(why)

    def _inputs(self, worker: str, increment_seconds: float, now: dt.datetime) -> tuple:
        policy = self.policy
        margins = (policy.max_balance_age_seconds, policy.max_rate_age_seconds, policy.backup_delay_seconds,
                   policy.shutdown_delay_seconds, policy.contingency_fraction, policy.retention_hours,
                   policy.clock_skew_seconds)
        if not all(_number(v) and v >= 0 for v in margins):
            self._refuse(worker, "the admission policy has a missing, negative or non-finite margin")
        if not _number(increment_seconds) or increment_seconds <= 0:
            self._refuse(worker, "the planned increment of work is missing or not positive")
        try:
            balance = self.provider.read_balance()
            rates = self.provider.read_rates(worker)
            liabilities = self.provider.list_liabilities()
        except Exception as exc:  # noqa: BLE001 - an unreadable provider is no input (a real adapter can fail in many ways)
            self._refuse(worker, f"provider inputs are unavailable: {_why(exc)}")
        if not isinstance(balance, BalanceReading):
            self._refuse(worker, "no balance reading")
        if balance.kind != BALANCE_KIND or balance.recognized is not True:
            self._refuse(worker, f"the balance reading is not an explicitly recognized {BALANCE_KIND} "
                                 f"(kind {balance.kind!r}): ambiguous, so not a balance")
        if not _number(balance.amount) or balance.amount < 0:
            self._refuse(worker, "the balance is missing, negative or non-finite")
        if not isinstance(rates, RateCard):
            self._refuse(worker, "no rate reading")
        for card in (rates, self.planned_rates):
            values = (card.gpu_per_hour, card.storage_per_hour, card.destination_per_hour)
            if not all(_number(v) and v >= 0 for v in values) or card.gpu_per_hour <= 0:
                self._refuse(worker, "a rate is missing, negative, non-finite or zero for the GPU")
        if not (balance.currency and balance.currency == rates.currency == self.planned_rates.currency):
            self._refuse(worker, "the balance and the rates are not in one stated currency")
        if rates.rates() != self.planned_rates.rates():
            self._refuse(worker, "the provider's rates differ from the rates the plan was costed with: a changed "
                                 "rate needs a new plan")
        ages = {}
        for name, stamp, limit in (("balance", balance.as_of_utc, policy.max_balance_age_seconds),
                                   ("rate", rates.as_of_utc, policy.max_rate_age_seconds)):
            try:
                ages[name] = (now - parse_utc(stamp)).total_seconds()
            except ValueError:
                self._refuse(worker, f"the {name} reading has no usable timestamp")
            if ages[name] < -policy.clock_skew_seconds:
                self._refuse(worker, f"the {name} reading is dated in the future")
            if ages[name] > limit:
                self._refuse(worker, f"the {name} reading is stale ({ages[name]:.0f} s old, limit {limit:.0f} s)")
        if not isinstance(liabilities, list) or not all(isinstance(item, Liability) for item in liabilities):
            self._refuse(worker, "the list of account liabilities is unavailable")
        for item in liabilities:
            if item.state not in ("active", "pending") or not all(
                    _number(v) and v >= 0 for v in (item.rate_per_hour, item.fixed_amount)):
                self._refuse(worker, "a liability has an unknown state or a missing, negative or non-finite amount")
        return balance, rates, liabilities, max(ages["balance"], 0.0)

    def admit(self, worker: str, increment_seconds: float, storage: StorageDeclaration,
              retention_reserve: float) -> Lease:
        """Grant a lease for ``increment_seconds`` of work on ``worker`` or raise
        ``AdmissionRefused`` (module doc). ``retention_reserve``: the amount set aside to keep the
        durable source and the destination alive after compute stops; it must cover the storage
        rates over the policy's retention hours. A renewal supersedes the worker's previous lease."""
        now = self.clock()
        try:
            storage_record = check_storage(storage, self.provider)
        except StorageRefused as exc:
            self._refuse(worker, f"storage is not confirmed: {exc}")
        with locked(self._lock):
            balance, rates, liabilities, age = self._inputs(worker, increment_seconds, now)
            policy = self.policy
            floor = (rates.storage_per_hour + rates.destination_per_hour) * policy.retention_hours
            if not _number(retention_reserve) or retention_reserve < floor:
                self._refuse(worker, f"the retention reserve is missing or below the storage rates over "
                                     f"{policy.retention_hours:g} h ({floor:.4f} {rates.currency})")
            horizon = increment_seconds + policy.backup_delay_seconds + policy.shutdown_delay_seconds
            factor = 1.0 + policy.contingency_fraction
            need = rates.worker_per_hour * (age + horizon) / 3600.0 * factor
            try:
                ledger = self._ledger()
            except AdmissionRefused as exc:
                self._refuse(worker, str(exc))
            leases = {lease.lease: lease for lease, released in ledger if not released}
            others = [lease for lease in leases.values() if lease.worker != worker]
            if any(lease.currency != rates.currency for lease, _ in ledger if lease.worker != worker):
                self._refuse(worker, "another worker's reservation is in another currency")
            as_of = parse_utc(balance.as_of_utc)
            held = math.fsum(lease.reserved_amount for lease in others if parse_utc(lease.reserved_until_utc) > as_of)
            # one retention reserve per other worker: its latest lease's, released or not, until its window ends
            latest: dict[str, Lease] = {}
            for lease, _ in ledger:
                if lease.worker != worker and (lease.worker not in latest
                                               or lease.granted_utc >= latest[lease.worker].granted_utc):
                    latest[lease.worker] = lease
            reserves = math.fsum(lease.retention_reserve for lease in latest.values()
                                 if parse_utc(lease.retention_until_utc) > as_of)
            leased_workers = {lease.worker for lease in others}
            unleased = math.fsum((item.rate_per_hour * (age + horizon) / 3600.0 + item.fixed_amount) * factor
                                 for item in liabilities if item.worker != worker and item.worker not in leased_workers)
            available = balance.amount - held - reserves - unleased - retention_reserve
            if not (math.isfinite(available) and math.isfinite(need)) or available < need:
                self._refuse(worker, f"insufficient runway: {available:.4f} {rates.currency} available after "
                                     f"reservations, every worker's retention reserve and liabilities; {need:.4f} "
                                     "needed")
            until = now + dt.timedelta(seconds=horizon)
            try:
                armed = self.provider.arm_shutdown(worker, iso(until))
            except Exception as exc:  # noqa: BLE001 - without a confirmed shutdown there is no lease
                self._refuse(worker, f"no provider-side shutdown can be armed: {_why(exc)}")
            if not (isinstance(armed, dict) and armed.get("armed") is True and armed.get("at_utc") == iso(until)):
                self._refuse(worker, "the provider did not confirm a shutdown at the end of the reservation")
            lease = Lease(lease=token(), worker=worker, granted_utc=iso(now),
                          expires_utc=iso(now + dt.timedelta(seconds=increment_seconds)), reserved_until_utc=iso(until),
                          reserved_amount=need, currency=rates.currency, rate_per_hour=rates.worker_per_hour,
                          balance_as_of_utc=balance.as_of_utc, retention_reserve=float(retention_reserve),
                          retention_until_utc=iso(until + dt.timedelta(hours=policy.retention_hours)))
            for old in [lease_id for lease_id, held_lease in leases.items() if held_lease.worker == worker]:
                append_jsonl(self.ledger, {"event": "release", "lease": old, "reason": "superseded by a renewal",
                                           "utc": iso(now)})
            append_jsonl(self.ledger, {"event": "lease", **asdict(lease)})
        self.journal.append("admission-granted", worker=worker, lease=lease.lease, expires_utc=lease.expires_utc,
                            reserved_until_utc=lease.reserved_until_utc, reserved_amount=need,
                            currency=rates.currency, rate_per_hour=rates.worker_per_hour,
                            balance_as_of_utc=balance.as_of_utc, available=available, need=need,
                            held_reservations=held, held_reserves=reserves, retention_reserve=lease.retention_reserve,
                            retention_until_utc=lease.retention_until_utc,
                            increment_seconds=increment_seconds, destination=storage_record["destination"]["kind"])
        return lease
