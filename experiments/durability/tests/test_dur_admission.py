"""Balance/runway admission, leases, the storage declaration and the dispatch gate with a fake
provider and a manual clock (ENGINEERING FIXTURES; no provider behaviour is asserted): the formula,
every fail-closed input (missing, stale, future-dated, negative, non-finite, unrecognized or
ambiguous balance, currency mismatch, changed or stale rates, unknown liabilities, insufficient
runway, a reserve below the retention floor), reservations serialized across two concurrent
workers, renewal and expiry, a shutdown that cannot be armed, a source that is not confirmed
persistent, a destination that is not independent, too small or not configured, and adapters that
are not configured."""

from __future__ import annotations

import dataclasses
import threading

import pytest

import dur_fixtures as dur

from experiments.durability.admission import (AdmissionPolicy, BalanceReading, Liability, StorageDeclaration,
                                              UnconfiguredProvider, check_storage)
from experiments.durability.common import (AdmissionRefused, GateRefused, Journal, NotConfigured, StorageRefused,
                                           append_jsonl, iso, read_jsonl)
from experiments.durability.destination import LocalDirectoryDestination, UnconfiguredDestination
from experiments.durability.gate import DispatchGate

HOUR = 3600.0
WORKER_RATE = dur.RATES["gpu_per_hour"] + dur.RATES["storage_per_hour"]


class World:
    def __init__(self, tmp_path, balance: float = 100.0) -> None:
        self.base = tmp_path
        self.clock = dur.ManualClock()
        self.provider = dur.FakeProvider(self.clock, balance=balance)
        self.source = tmp_path / "volume"
        self.source.mkdir(parents=True)
        self.destination = LocalDirectoryDestination(tmp_path / "offsite")
        self.controller = dur.admission(tmp_path, self.provider, self.clock)

    def storage(self, **changes) -> StorageDeclaration:
        return dur.storage(self.source, changes.pop("destination", self.destination), **changes)

    def admit(self, worker: str = "worker-1", seconds: float = HOUR, reserve: float = dur.RESERVE, **storage):
        return self.controller.admit(worker, seconds, self.storage(**storage), reserve)

    def reading(self, **changes) -> BalanceReading:
        return dataclasses.replace(self.provider.balance, **changes)


def expected_need(seconds: float, age: float = 0.0) -> float:
    horizon = seconds + dur.POLICY.backup_delay_seconds + dur.POLICY.shutdown_delay_seconds
    return WORKER_RATE * (age + horizon) / HOUR * (1 + dur.POLICY.contingency_fraction)


def test_admission_reserves_the_stated_formula_and_arms_the_provider_shutdown(tmp_path):
    world = World(tmp_path)
    world.clock.advance(60.0)                         # the balance reading is one minute old
    lease = world.admit()
    assert lease.reserved_amount == pytest.approx(expected_need(HOUR, age=60.0))
    assert lease.expires_utc == iso(world.clock.now + dur.dt.timedelta(seconds=HOUR))
    until = world.clock.now + dur.dt.timedelta(seconds=HOUR + 300.0 + 120.0)     # backup and shutdown delays
    assert lease.reserved_until_utc == iso(until) and world.provider.armed == [("worker-1", iso(until))]
    assert world.controller.current_lease("worker-1") == lease
    assert lease.covers(world.clock.now, 3599.0) and not lease.covers(world.clock.now, 3601.0)
    granted = [row for row in Journal(tmp_path / "admin" / "journal.jsonl").read() if row["event"] == "admission-granted"]
    assert granted[0]["need"] == pytest.approx(lease.reserved_amount)
    assert granted[0]["available"] == pytest.approx(100.0 - dur.RESERVE)
    # exactly enough is admitted; one cent less is not
    exact = World(tmp_path / "exact", balance=expected_need(HOUR) + dur.RESERVE)
    assert exact.admit().reserved_amount == pytest.approx(expected_need(HOUR))
    short = World(tmp_path / "short", balance=expected_need(HOUR) + dur.RESERVE - 0.01)
    with pytest.raises(AdmissionRefused, match="insufficient runway"):
        short.admit()
    assert short.provider.armed == [] and read_jsonl(short.controller.ledger) == []


def refusal_cases():
    nan, inf = float("nan"), float("inf")
    stale = iso(dur.T0 - dur.dt.timedelta(seconds=121))
    future = iso(dur.T0 + dur.dt.timedelta(seconds=60))
    return {
        "provider not configured": (lambda w: setattr(w.controller, "provider", UnconfiguredProvider()), "not confirmed"),
        "balance unavailable": (lambda w: setattr(w.provider, "balance", NotConfigured("no balance")), "unavailable"),
        "no balance reading": (lambda w: setattr(w.provider, "balance", None), "no balance reading"),
        "a billing total is not a balance": (
            lambda w: setattr(w.provider, "balance", w.reading(kind="pod-billing-total")), "ambiguous"),
        "unrecognized balance": (lambda w: setattr(w.provider, "balance", w.reading(recognized=False)), "ambiguous"),
        "negative balance": (lambda w: setattr(w.provider, "balance", w.reading(amount=-1.0)), "negative"),
        "non-finite balance": (lambda w: setattr(w.provider, "balance", w.reading(amount=nan)), "non-finite"),
        "infinite balance": (lambda w: setattr(w.provider, "balance", w.reading(amount=inf)), "non-finite"),
        "balance as text": (lambda w: setattr(w.provider, "balance", w.reading(amount="100")), "missing"),
        "stale balance": (lambda w: setattr(w.provider, "balance", w.reading(as_of_utc=stale)), "stale"),
        "future-dated balance": (lambda w: setattr(w.provider, "balance", w.reading(as_of_utc=future)), "future"),
        "balance without a timestamp": (lambda w: setattr(w.provider, "balance", w.reading(as_of_utc="noon")),
                                        "no usable timestamp"),
        "another currency": (lambda w: setattr(w.provider, "balance", w.reading(currency="EUR")), "currency"),
        "changed GPU rate": (lambda w: setattr(w.provider, "rates", dur.rate_card(w.clock, gpu_per_hour=1.7)),
                             "changed rate"),
        "changed storage rate": (lambda w: setattr(w.provider, "rates", dur.rate_card(w.clock, storage_per_hour=0.03)),
                                 "changed rate"),
        "non-finite rate": (lambda w: setattr(w.provider, "rates", dur.rate_card(w.clock, gpu_per_hour=nan)), "rate"),
        "stale rates": (lambda w: setattr(w.provider, "rates", dur.rate_card(
            w.clock, as_of_utc=iso(dur.T0 - dur.dt.timedelta(hours=2)))), "stale"),
        "rates unavailable": (lambda w: setattr(w.provider, "rates", NotConfigured("no rates")), "unavailable"),
        "liabilities unavailable": (lambda w: setattr(w.provider, "liabilities", None), "liabilities is unavailable"),
        "liability with an unknown state": (
            lambda w: setattr(w.provider, "liabilities", [Liability("pod", 1.0, "unknown")]), "liability"),
        "liability with a negative rate": (
            lambda w: setattr(w.provider, "liabilities", [Liability("pod", -1.0, "active")]), "liability"),
        "shutdown cannot be armed": (lambda w: setattr(w.provider, "arm", NotConfigured("no shutdown")),
                                     "shutdown can be armed"),
        "shutdown armed for another time": (
            lambda w: setattr(w.provider, "arm", {"armed": True, "at_utc": iso(dur.T0)}), "did not confirm a shutdown"),
        "source not confirmed persistent": (
            lambda w: setattr(w.provider, "persistent", {"persistent": False, "volume": None}), "persistent"),
    }


@pytest.mark.parametrize("name", sorted(refusal_cases()))
def test_admission_fails_closed_on_missing_stale_ambiguous_or_changed_inputs(tmp_path, name):
    world = World(tmp_path)
    change, why = refusal_cases()[name]
    change(world)
    with pytest.raises(AdmissionRefused, match=why):
        world.admit()
    assert read_jsonl(world.controller.ledger) == []                  # nothing was reserved
    assert world.controller.current_lease("worker-1") is None
    refused = Journal(tmp_path / "admin" / "journal.jsonl").read()[-1]
    assert refused["event"] == "admission-refused" and refused["worker"] == "worker-1"


def test_admission_refuses_bad_requests_reserves_and_storage_declarations(tmp_path):
    world = World(tmp_path)
    for seconds in (0, -5.0, float("nan"), None):
        with pytest.raises(AdmissionRefused, match="increment"):
            world.admit(seconds=seconds)
    with pytest.raises(AdmissionRefused, match="retention reserve"):
        world.admit(reserve=dur.RESERVE - 0.01)                       # below the storage rates over 72 h
    with pytest.raises(AdmissionRefused, match="retention reserve"):
        world.admit(reserve=None)
    bad = dur.admission(tmp_path / "bad", world.provider, world.clock)
    bad.policy = AdmissionPolicy(120.0, 3600.0, 300.0, 120.0, float("nan"), 72.0)    # no stated contingency
    with pytest.raises(AdmissionRefused, match="margin"):
        bad.admit("worker-1", HOUR, world.storage(), dur.RESERVE)
    cases = {"independent": {"destination_independent_of_gpu_account": False},
             "funding": {"destination_funding": "  "},
             "retention": {"destination_retention_days": 7.0},
             "free bytes": {"required_bytes": 1 << 60},
             "not a folder": {"source_path": str(tmp_path / "missing")},
             "inside the source": {"destination": LocalDirectoryDestination(world.source / "backup")},
             "not usable": {"destination": UnconfiguredDestination("object-store")}}
    for why, change in cases.items():
        with pytest.raises(AdmissionRefused, match=why):
            world.admit(**change)
        with pytest.raises(StorageRefused):
            check_storage(world.storage(**change), world.provider)
    with pytest.raises(StorageRefused, match="not confirmed persistent"):
        check_storage(world.storage(), UnconfiguredProvider())
    assert read_jsonl(world.controller.ledger) == [] and world.provider.armed == []
    record = check_storage(world.storage(), world.provider)
    assert record["source"]["volume"] == "fake-volume-1" and record["destination"]["independent_of_gpu_account"] is True
    assert not list((tmp_path / "offsite").rglob("probe-*"))          # the probe object is removed


def test_other_reservations_and_unleased_liabilities_reduce_the_runway(tmp_path):
    need = expected_need(HOUR)
    world = World(tmp_path, balance=2 * need + 2 * dur.RESERVE + 0.01)
    first = world.admit("worker-1")
    second = world.admit("worker-2")                                  # holds worker-1's reservation and reserve
    assert first.reserved_amount == pytest.approx(need) and second.reserved_amount == pytest.approx(need)
    with pytest.raises(AdmissionRefused, match="insufficient runway"):
        world.admit("worker-3")
    # a liability of no leased worker draws on the same balance through the horizon; worker-1's own pod does not
    horizon = HOUR + 420.0
    extra = World(tmp_path / "extra", balance=need + dur.RESERVE + 0.5 * horizon / HOUR * 1.25 + 7.0 * 1.25 - 0.01)
    extra.provider.liabilities = [Liability("stray pod", 0.5, "active"), Liability("pending charge", 0.0, "pending", 7.0),
                                  Liability("worker-1 pod", 1.6, "active", worker="worker-1")]
    with pytest.raises(AdmissionRefused, match="insufficient runway"):
        extra.admit("worker-1")
    extra.provider.balance = extra.reading(amount=extra.provider.balance.amount + 0.02)
    assert extra.admit("worker-1").reserved_amount == pytest.approx(need)


def test_a_second_worker_cannot_spend_the_first_worker_s_retention_reserve(tmp_path):
    """Review finding B. Each lease records its retention reserve and the end of its retention
    window. With room for both computes but only ONE reserve, the second worker is refused:
    worker-1's volume still needs its reserve after its compute stops."""
    need = expected_need(HOUR)
    world = World(tmp_path, balance=2 * need + dur.RESERVE + 0.01)
    first = world.admit("worker-1")
    assert first.retention_reserve == pytest.approx(dur.RESERVE)
    window = dur.dt.timedelta(seconds=HOUR + 420.0) + dur.dt.timedelta(hours=dur.POLICY.retention_hours)
    assert first.retention_until_utc == iso(world.clock.now + window)
    with pytest.raises(AdmissionRefused, match="insufficient runway"):
        world.admit("worker-2")
    world.provider.balance = world.reading(amount=2 * need + 2 * dur.RESERVE)
    second = world.admit("worker-2")
    granted = [row for row in Journal(tmp_path / "admin" / "journal.jsonl").read() if row["event"] == "admission-granted"]
    assert granted[-1]["held_reserves"] == pytest.approx(dur.RESERVE)
    assert granted[-1]["held_reservations"] == pytest.approx(need) and second.retention_reserve == pytest.approx(dur.RESERVE)


def test_a_reserve_is_held_once_per_worker_through_renewal_and_release_until_its_window_ends(tmp_path):
    """Review finding B, renewal and release. A renewal replaces the worker's reserve (it is not
    held twice); a released or superseded lease's reserve stays held until its retention window
    ends, because the volume still bills; after that it is free again."""
    need = expected_need(HOUR)

    def refresh(world, amount):
        world.provider.balance = dur.FakeProvider(world.clock, balance=amount).balance
        world.provider.rates = dur.rate_card(world.clock)

    # (1) worker-1 renews: worker-2 then holds ONE reserve of worker-1 and only its live reservation
    world = World(tmp_path / "renewal", balance=100.0)
    world.admit("worker-1")
    world.clock.advance(600.0)
    refresh(world, 100.0)
    renewed = world.admit("worker-1")                                 # supersedes the first lease
    refresh(world, 2 * need + 2 * dur.RESERVE - 0.01)
    with pytest.raises(AdmissionRefused, match="insufficient runway"):
        world.admit("worker-2")
    refresh(world, 2 * need + 2 * dur.RESERVE + 0.01)                 # two reserves in all, not three
    assert world.admit("worker-2").reserved_amount == pytest.approx(need)
    granted = Journal(tmp_path / "renewal" / "admin" / "journal.jsonl").read()[-1]
    assert granted["held_reserves"] == pytest.approx(dur.RESERVE) and granted["held_reservations"] == pytest.approx(need)
    # a worker renewing itself is charged its own reserve once
    world.clock.advance(60.0)
    refresh(world, 2 * need + 2 * dur.RESERVE + 0.01)
    assert world.admit("worker-1").retention_reserve == pytest.approx(dur.RESERVE)
    assert renewed.lease not in [lease.lease for lease in world.controller._leases().values()]
    # (2) worker-1 is released: its compute reservation is free at once, its reserve is not
    world = World(tmp_path / "release", balance=100.0)
    lease = world.admit("worker-1")
    world.controller.release(lease.lease, "the worker was stopped")
    refresh(world, need + 2 * dur.RESERVE - 0.01)
    with pytest.raises(AdmissionRefused, match="insufficient runway"):
        world.admit("worker-2")                                       # the stopped worker's volume still bills
    refresh(world, need + 2 * dur.RESERVE + 0.01)
    assert world.admit("worker-2").reserved_amount == pytest.approx(need)
    # (3) after the retention window has ended the reserve is no longer held
    world = World(tmp_path / "expired", balance=100.0)
    lease = world.admit("worker-1")
    world.controller.release(lease.lease, "the worker was stopped")
    world.clock.advance(HOUR + 420.0 + dur.POLICY.retention_hours * HOUR + 1.0)
    refresh(world, need + dur.RESERVE + 0.01)
    assert world.admit("worker-2").reserved_amount == pytest.approx(need)


def test_an_unreadable_reservation_ledger_fails_closed_as_a_refusal(tmp_path):
    """Review finding B. A ledger row that is not a well-formed lease or release (malformed, or of
    an older format without the reserve) refuses admission and dispatch as ``AdmissionRefused`` /
    ``GateRefused``; it never escapes as a bare TypeError, which Stage B would record as a charged
    failed attempt."""
    old_format = {"event": "lease", "lease": "abc", "worker": "worker-9", "granted_utc": iso(dur.T0),
                  "expires_utc": iso(dur.T0), "reserved_until_utc": iso(dur.T0), "reserved_amount": 1.0,
                  "currency": "USD", "rate_per_hour": 1.62, "balance_as_of_utc": iso(dur.T0)}
    rows = {"an older lease format": old_format,
            "an unknown field": {**old_format, "retention_reserve": 1.0, "retention_until_utc": iso(dur.T0), "x": 1},
            "a timestamp that is not one": {**old_format, "retention_reserve": 1.0, "retention_until_utc": "later"},
            "a negative reserve": {**old_format, "retention_reserve": -1.0, "retention_until_utc": iso(dur.T0)},
            "an unknown event": {"event": "note", "text": "hello"}}
    for index, (name, row) in enumerate(rows.items()):
        world = World(tmp_path / str(index))
        append_jsonl(world.controller.ledger, row)
        with pytest.raises(AdmissionRefused, match="ledger is unreadable"):
            world.admit()
        with pytest.raises(AdmissionRefused, match="ledger is unreadable"):
            world.controller.current_lease("worker-1")
        vault = dur.make_vault(tmp_path / str(index), clock=world.clock)
        gate = DispatchGate(vault, world.controller.current_lease, journal=vault.journal, clock=world.clock)
        with pytest.raises(GateRefused, match="AdmissionRefused"):
            gate.require("worker-1")
        assert world.provider.armed == [], name
    world = World(tmp_path / "torn")
    world.controller.ledger.parent.mkdir(parents=True, exist_ok=True)
    world.controller.ledger.write_bytes(b'{"event": "lease", "lea')     # an append cut off mid-line
    with pytest.raises(AdmissionRefused, match="ledger is unreadable"):
        world.admit()
    # anything unexpected while the gate checks is a refusal too
    gate = DispatchGate(dur.make_vault(tmp_path / "boom"), lambda worker: 1 / 0,
                        journal=Journal(tmp_path / "boom" / "j.jsonl"))
    with pytest.raises(GateRefused, match="ZeroDivisionError"):
        gate.require("worker-1")


def test_two_workers_cannot_both_reserve_the_same_runway(tmp_path):
    world = World(tmp_path, balance=expected_need(HOUR) + dur.RESERVE + 0.5)    # room for one worker only
    barrier, outcomes = threading.Barrier(2), {}

    def worker(name: str) -> None:
        controller = dur.admission(tmp_path, world.provider, world.clock)       # each worker: its own process view
        barrier.wait()
        try:
            outcomes[name] = controller.admit(name, HOUR, world.storage(), dur.RESERVE)
        except AdmissionRefused as exc:
            outcomes[name] = exc

    threads = [threading.Thread(target=worker, args=(f"worker-{n}",)) for n in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    granted = [name for name, outcome in outcomes.items() if not isinstance(outcome, Exception)]
    refused = [outcome for outcome in outcomes.values() if isinstance(outcome, Exception)]
    assert len(granted) == 1 and len(refused) == 1 and "insufficient runway" in str(refused[0])
    leases = [row for row in read_jsonl(world.controller.ledger) if row["event"] == "lease"]
    assert [row["worker"] for row in leases] == granted and len(world.provider.armed) == 1


def test_a_lease_expires_a_renewal_supersedes_it_and_the_gate_needs_both_ack_and_lease(tmp_path):
    world = World(tmp_path)
    vault = dur.make_vault(tmp_path, clock=world.clock)
    gate = DispatchGate(vault, world.controller.current_lease, journal=vault.journal, clock=world.clock)
    with pytest.raises(GateRefused, match="no admission lease"):
        gate.require("worker-1")
    first = world.admit(seconds=600.0)
    assert gate.require("worker-1", needs_seconds=600.0) == first
    with pytest.raises(GateRefused, match="does not cover"):
        gate.require("worker-1", needs_seconds=601.0)
    with pytest.raises(GateRefused, match="not acknowledged"):       # a previous unit without its acknowledgement
        gate.require("worker-1", previous=[("run", "/workspace/calibration-001/1101-a0-q-a1", "0" * 64)])
    world.clock.advance(601.0)
    with pytest.raises(GateRefused, match="expired"):
        gate.require("worker-1")
    with pytest.raises(AdmissionRefused, match="stale"):             # a renewal needs a fresh balance reading
        world.admit()
    world.provider.balance = dur.FakeProvider(world.clock).balance
    world.provider.rates = dur.rate_card(world.clock)
    second = world.admit()
    assert gate.require("worker-1") == second and world.controller.current_lease("worker-1") == second
    rows = read_jsonl(world.controller.ledger)
    assert [row["event"] for row in rows] == ["lease", "release", "lease"] and rows[1]["lease"] == first.lease
    assert len(world.provider.armed) == 2                            # the shutdown was re-armed for the new end
    world.controller.release(second.lease, "the worker was stopped")
    with pytest.raises(GateRefused, match="no admission lease"):
        gate.require("worker-1")
    refusals = [row["reason"] for row in vault.journal.read() if row["event"] == "dispatch-refused"]
    assert len(refusals) == 5


def test_adapters_that_are_not_configured_refuse_every_call():
    provider = UnconfiguredProvider()
    for call in (provider.read_balance, lambda: provider.read_rates("w"), provider.list_liabilities,
                 lambda: provider.confirm_persistent("/workspace"), lambda: provider.arm_shutdown("w", "t")):
        with pytest.raises(NotConfigured, match="funded one-worker validation"):
            call()
    destination = UnconfiguredDestination("object-store")
    for call in (destination.free_bytes, destination.probe, lambda: destination.exists("k"),
                 lambda: destination.put_new("k", b"")):
        with pytest.raises(NotConfigured, match="funded one-worker validation"):
            call()
