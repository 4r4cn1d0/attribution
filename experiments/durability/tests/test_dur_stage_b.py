"""The gated Stage B backend and the study backup on the synthetic ENGINEERING FIXTURE (fake
backend, fake clock). The decisive check (b): a study killed mid-block is restored from the
destination into its recorded root and resumed to completion, every pre-kill record byte-identical,
the lost attempt and its unknown cost kept, and the new attempt numbered after it. Also: a missing
or expired lease and a failed off-pod copy refuse the next operation before any work (recorded by
Stage B as an uncharged refusal that stops the controller); a lost start that still holds its
registry claim refuses until it is declared lost; an unsettled study is not entered; a backend
that already served a block in this process is refused (one block per process); only a refusal can
leave the gate; where the safeguard's time lands in the Stage B cost record; logs name no
operation, arm or choice. Nothing here is a scientific result."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytest.importorskip("numpy")

import dur_fixtures as dur  # noqa: E402
import ss_fixtures as fx  # noqa: E402

from experiments.durability.backup import Vault  # noqa: E402
from experiments.durability.common import DurabilityError, GateRefused, Journal, read_jsonl  # noqa: E402
from experiments.durability.destination import LocalDirectoryDestination  # noqa: E402
from experiments.durability.stage_b import (StudyBackup, declare_lost_attempt, open_attempts,  # noqa: E402
                                            reconcile_claims, run_block_gated, study_attempts)
from experiments.safety_decision_policy.analysis import analyze  # noqa: E402
from experiments.safety_decision_policy.common import (RequestRefused, read_canonical,  # noqa: E402
                                                       read_json_strict)
from experiments.safety_decision_policy.controller import Study, study_evidence  # noqa: E402
from experiments.safety_decision_policy.synthetic import FakeBackend, make_world, prepare_synthetic  # noqa: E402
from experiments.safety_selection.jobs import trajectory_key  # noqa: E402

CONFIGS = Path(__file__).resolve().parents[2] / "safety_decision_policy" / "configs"
WORKER = "worker-1"


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    world = make_world()
    template = read_json_strict(CONFIGS / "example-engineering.json")
    spec = read_json_strict(CONFIGS / "example-dev-fit-spec.json")
    return world, prepare_synthetic(tmp_path_factory.mktemp("development"), world, template=template, spec=spec)


class Site:
    """A worker volume holding one study, an off-pod destination, a fake provider and clock."""

    def __init__(self, base: Path, world, setup) -> None:
        self.base, self.world, self.setup = base.resolve(), world, setup
        self.volume, self.offsite = self.base / "volume", self.base / "offsite"
        self.root = self.volume / "study"
        self.clock = dur.ManualClock()
        self.provider = dur.FakeProvider(self.clock)
        self.volume.mkdir(parents=True)

    def vault(self, destination=None) -> Vault:
        return Vault(destination or LocalDirectoryDestination(self.offsite / "destination"), "study-1",
                     journal=Journal(self.volume / "durability-admin" / "journal.jsonl", self.clock),
                     scratch=self.offsite / "scratch", clock=self.clock, reveal_paths=False, require_code=False)

    def admission(self):
        return dur.admission(self.offsite, self.provider, self.clock)

    def admit(self, seconds: float = 3600.0):
        self.provider.balance = dur.FakeProvider(self.clock).balance
        self.provider.rates = dur.rate_card(self.clock)
        return self.admission().admit(WORKER, seconds, dur.storage(self.volume, self.vault().destination), dur.RESERVE)

    def study(self, backend) -> Study:
        setup = self.setup
        return Study(self.root, config=setup["config"], record=setup["record"], backend=backend,
                     recipe=setup["recipe"], data_config=setup["data_config"], shape=self.world.shape("heldout"),
                     actual_pins=setup["pins"], process_start=backend.clock(), engineering_fixture=True)

    def run(self, inner=None, *, destination=None, block: int = 0):
        """One administrative run-block call; returns (result, inner backend, backup)."""
        inner = inner or FakeBackend(self.world)
        vault = self.vault(destination)
        backup = StudyBackup(vault, self.root)
        result = run_block_gated(self.study, block, inner=inner, backup=backup,
                                 gate=dur.gate_for(vault, self.admission(), self.clock), worker=WORKER)
        return result, inner, backup


def z0_of(setup) -> int:
    return setup["config"]["blocks"]["list"][0]["selector_seed_start"]


def statuses(folder: Path) -> list[str]:
    return [read_canonical(p / "receipt.json")["status"]
            for p in sorted(folder.glob("attempt-*"), key=lambda p: int(p.name[8:]))]


class Dying(FakeBackend):
    """The worker is terminated inside one operation: what survives is the destination as it was
    at that moment (copied aside as ``offsite-at-kill``)."""

    def __init__(self, world, site: Site, target: tuple[str, int]) -> None:
        super().__init__(world)
        self.site, self.target = site, target

    def execute(self, spec, attempt_dir, sources):
        if (spec["op_id"], int(Path(attempt_dir).name.rsplit("-", 1)[1])) == self.target:
            shutil.copytree(self.site.offsite, self.site.base / "offsite-at-kill")
            raise KeyboardInterrupt("ENGINEERING FIXTURE: the worker was terminated")
        return super().execute(spec, attempt_dir, sources)


def test_a_study_killed_mid_block_is_restored_and_resumed_with_the_lost_attempt_kept(tmp_path, synthetic):
    world, setup = synthetic
    site = Site(tmp_path, world, setup)
    site.admit()
    prerequisite = f"full_from_short-a0-{z0_of(setup)}"          # S+'s prerequisite: after the whole screen
    with pytest.raises(KeyboardInterrupt):
        site.run(Dying(world, site, (prerequisite, 1)))
    before = dur.tree_hashes(site.root)
    lost = site.root / "blocks" / "0" / "ops" / prerequisite / "attempt-1"
    shutil.rmtree(site.volume)                                   # the volume is gone
    shutil.rmtree(site.offsite)
    (site.base / "offsite-at-kill").rename(site.offsite)         # only what was off-pod at the kill remains
    site.volume.mkdir()
    assert not site.root.exists()
    report = site.vault().restore()
    restored = dur.tree_hashes(site.root)
    assert all(before[name] == digest for name, digest in restored.items())   # every restored record byte-identical
    receipts = [name for name in restored if name.endswith("receipt.json")]
    assert len(receipts) == len(world.groups["heldout"]) + 1 + 3   # the screen and the three static operations
    # (a started.json is stored with its attempt and, earlier, as the in-flight record: placed once, found once)
    assert report["reused_files"] == len(receipts) and report["restored_files"] == len(restored)
    # the attempt in flight is back as its started.json alone; there is no end record and no result
    assert sorted(p.name for p in lost.iterdir()) == ["started.json"] and open_attempts(site.root) == [lost]
    assert (site.root / "blocks" / "0" / "sessions" / "session-1.json").is_file()
    assert not (site.root / "blocks" / "0" / "sessions" / "session-1-end.json").exists()
    assert not (site.root / "blocks" / "0" / "result.json").exists()
    # resume on a new worker process: nothing restored is pending, the block completes
    site.admit()
    result, inner, backup = site.run()
    assert result["status"] == "complete"
    assert statuses(lost.parent) == ["interrupted", "complete"]        # the lost attempt kept, the next number used
    closed = read_canonical(lost / "receipt.json")
    assert closed["seconds"] is None and closed["session"] == {"block": 0, "number": 1}   # its cost: unknown, not zero
    retried = read_canonical(lost.parent / "attempt-2" / "receipt.json")
    assert retried["session"] == {"block": 0, "number": 2} and retried["spec_sha256"] == closed["spec_sha256"]
    assert (prerequisite, 2) in inner.executed
    assert not [op for op, _ in inner.executed if op.startswith("screen-") or op in ("score_groups", "relevance")]
    after = dur.tree_hashes(site.root)
    assert all(after[name] == digest for name, digest in restored.items())    # the restored records are untouched
    # the lost attempt's cost stays in the Stage B accounting as a lower bound: no margin is formed
    costs = result["costs"]
    assert costs["actual"]["S+"]["timing_complete"] is False
    evidence = study_evidence(site.root, setup["config"])
    analysis = analyze(evidence["results"], setup["config"], evidence["static"], evidence["started"],
                       recorded=evidence["recorded"])
    assert analysis["costs"]["per_block"][0]["cost_margin"] is None
    assert analysis["costs"]["physical_controller_seconds"] is None
    # everything the block wrote is acknowledged off-pod, and a restore of the vault reproduces the study
    assert backup.pending() == {"pins": False, "records": [], "attempts": []}
    mirror = tmp_path / "mirror"
    site.vault().restore(mirror=mirror)
    copy = dur.tree_hashes(mirror / str(site.root).lstrip("/"))
    assert copy == {name: digest for name, digest in after.items() if name != "controller.lock"}


def test_a_missing_or_expired_lease_refuses_the_next_operation_before_any_work(tmp_path, synthetic):
    world, setup = synthetic
    site = Site(tmp_path, world, setup)
    inner = FakeBackend(world)
    with pytest.raises(GateRefused, match="no admission lease"):
        site.run(inner)                                           # never admitted: the block is not entered
    assert inner.executed == [] and not site.root.exists()
    site.admit(seconds=600.0)

    class Slow(FakeBackend):
        """The second operation outlasts the lease."""

        def execute(self, spec, attempt_dir, sources):
            if len(self.executed) == 1:
                site.clock.advance(601.0)
            return super().execute(spec, attempt_dir, sources)

    slow = Slow(world)
    with pytest.raises(RequestRefused, match="dispatch refused before any work"):
        site.run(slow)
    assert len(slow.executed) == 2                                # the third operation never ran
    refused = [p for p in sorted(site.root.glob("**/attempt-*")) if read_canonical(p / "receipt.json")["status"] == "refused"]
    assert len(refused) == 1 and sorted(p.name for p in refused[0].iterdir()) == ["receipt.json", "started.json"]
    assert refused[0].parent.name not in [op for op, _ in slow.executed]
    site.admit()                                                  # a renewed admission
    result, resumed, _ = site.run()
    assert result["status"] == "complete"
    assert statuses(refused[0].parent) == ["refused", "complete"]  # the refusal was no attempt and cost nothing
    for method in ("S-", "S+"):
        assert result["costs"]["actual"][method]["failed_attempt_seconds"] == 0.0


def test_a_failed_off_pod_copy_stops_the_block_at_the_next_operation(tmp_path, synthetic):
    world, setup = synthetic
    site = Site(tmp_path, world, setup)
    site.admit()
    failing = dur.FaultyDestination(site.offsite / "destination", refuse_after=6)
    inner = FakeBackend(world)
    with pytest.raises(RequestRefused, match="off-pod copy failed"):
        site.run(inner, destination=failing)
    ran = len(inner.executed)
    backup = StudyBackup(site.vault(), site.root)
    pending = backup.pending()
    assert ran > 0 and len(pending["attempts"]) == 1            # only the attempt whose copy failed
    with pytest.raises(GateRefused, match="settle it first"):   # the study is not entered while it is unsettled
        site.run(FakeBackend(world))
    assert backup.settle()["attempts"] == len(pending["attempts"])
    result, resumed, _ = site.run()
    assert result["status"] == "complete" and len(resumed.executed) > 0
    assert not set(inner.executed) & set(resumed.executed)        # nothing ran twice


def test_a_lost_start_holding_its_registry_claim_refuses_until_it_is_declared_lost(tmp_path, synthetic):
    world, setup = synthetic
    site = Site(tmp_path, world, setup)
    site.admit()
    recipe, manifest = fx.recipe(), "0" * 64
    screen = f"screen-a0-{z0_of(setup)}"
    lost = site.root / "blocks" / "0" / "ops" / screen / "attempt-1"

    class WithRegistry(FakeBackend):
        """The fake backend with the engine backend's registry attributes."""

        registry, manifest_sha256 = site.root / "registry.jsonl", manifest

        def __init__(self, world_):
            super().__init__(world_)
            self.recipe = recipe

    class KilledInTheScreen(WithRegistry):
        def execute(self, spec, attempt_dir, sources):
            if spec["op_id"] == screen and Path(attempt_dir).name == "attempt-1":
                shutil.copytree(site.offsite, site.base / "offsite-at-kill")
                raise KeyboardInterrupt("ENGINEERING FIXTURE: the worker was terminated")
            return super().execute(spec, attempt_dir, sources)

    with pytest.raises(KeyboardInterrupt):
        site.run(KilledInTheScreen(world))
    shutil.rmtree(site.volume)
    shutil.rmtree(site.offsite)
    (site.base / "offsite-at-kill").rename(site.offsite)
    site.volume.mkdir()
    vault = site.vault()
    vault.restore()
    assert open_attempts(site.root) == [lost] and not (site.root / "registry.jsonl").exists()
    # the engine had claimed the trajectory before it died; the restored registry snapshot predates the claim
    assert reconcile_claims(site.root, registry=site.root / "registry.jsonl", recipe=recipe,
                            manifest_sha256=manifest, vault=vault) == 1
    claim = read_jsonl(site.root / "registry.jsonl")
    assert claim[0]["run_dir"] == str(lost / "run") and "reconstructed_by" in claim[0]
    assert claim[0]["key"] == trajectory_key(manifest, recipe, "heldout", "a0", z0_of(setup), "selector")
    assert reconcile_claims(site.root, registry=site.root / "registry.jsonl", recipe=recipe,
                            manifest_sha256=manifest, vault=vault) == 0     # appended once
    registry = (site.root / "registry.jsonl").read_bytes()
    site.admit()
    StudyBackup(vault, site.root).settle()
    inner = WithRegistry(world)
    with pytest.raises(RequestRefused, match="declare it lost first"):
        site.run(inner)
    assert screen not in [op for op, _ in inner.executed]
    assert statuses(lost.parent) == ["interrupted", "refused"]     # closed by Stage B; the retry was refused uncharged
    backup = StudyBackup(site.vault(), site.root)
    backup.settle()
    with pytest.raises(DurabilityError, match="operator and reason"):
        declare_lost_attempt(backup, lost, operator=" ", reason="x")
    tombstone = declare_lost_attempt(backup, lost, operator="test operator", reason="ENGINEERING FIXTURE: pod lost")
    assert tombstone == lost / "run" / "error.txt" and "ADMINISTRATIVE TOMBSTONE" in tombstone.read_text()
    assert (site.root / "registry.jsonl").read_bytes() == registry  # the claim is never cleared or edited
    with pytest.raises(DurabilityError):                            # a completed attempt is never declared lost
        declare_lost_attempt(backup, study_attempts(site.root)[0], operator="o", reason="r")
    result, resumed, _ = site.run(WithRegistry(world))
    assert result["status"] == "complete" and (screen, 3) in resumed.executed
    assert statuses(lost.parent) == ["interrupted", "refused", "complete"]


def test_a_backend_that_already_served_a_block_in_this_process_is_refused(tmp_path, synthetic):
    """Review finding C. Stage B decides whether a session's setup was measured by whether its
    backend object already served a block. A new gated wrapper around a warm inner backend would
    look fresh, and unmeasured setup would be labelled measured: so the entrypoint refuses, before
    anything is written. One block per process."""
    world, setup = synthetic
    site = Site(tmp_path, world, setup)
    inner = FakeBackend(world)
    site.admit()
    site.run(inner, block=0)
    first = read_canonical(site.root / "blocks" / "0" / "sessions" / "session-1.json")
    assert first["process_shared_with_an_earlier_block"] is False       # the fresh process, measured
    site.admit()
    before = dur.tree_hashes(site.root)
    with pytest.raises(GateRefused, match="one block per process"):
        site.run(inner, block=1)                                        # the same warm backend again
    assert not (site.root / "blocks" / "1").exists() and dur.tree_hashes(site.root) == before
    assert len(inner.executed) == len(set(inner.executed))
    # a new wrapper does not launder it either: two backends over one engine session are one asset cache
    class Session:
        pass

    shared = Session()
    one, two = FakeBackend(world), FakeBackend(world)
    one.session = two.session = shared
    other = Site(tmp_path / "other", world, setup)
    other.admit()
    other.run(one, block=0)
    other.admit()
    with pytest.raises(GateRefused, match="one block per process"):
        other.run(two, block=1)
    # nor does a backend that Stage B itself already ran ungated in this process
    plain = FakeBackend(world)
    study = Site(tmp_path / "plain", world, setup)
    ungated = study.study(plain)
    try:
        ungated.run_block(0)
    finally:
        ungated.close()
    study.admit()
    StudyBackup(study.vault(), study.root).settle()
    with pytest.raises(GateRefused, match="one block per process"):
        study.run(plain, block=1)
    result, _, _ = study.run(FakeBackend(world), block=1)               # a fresh process's backend runs it
    assert result["status"] == "complete"
    record = read_canonical(study.root / "blocks" / "1" / "sessions" / "session-1.json")
    assert record["process_shared_with_an_earlier_block"] is False


def test_only_a_refusal_leaves_the_gate_whatever_goes_wrong_in_it(tmp_path, synthetic, monkeypatch):
    """An unexpected error while the gate works (here: the copy of started.json raising a plain
    RuntimeError at the third operation) is still an uncharged refusal before any work. Anything
    else would be recorded by Stage B as a charged failed attempt."""
    world, setup = synthetic
    site = Site(tmp_path, world, setup)
    site.admit()
    real, calls = StudyBackup.open_attempt, []

    def flaky(self, attempt_dir):
        calls.append(attempt_dir)
        if len(calls) == 3:
            raise RuntimeError("ENGINEERING FIXTURE: an unexpected error inside the gate")
        return real(self, attempt_dir)

    monkeypatch.setattr(StudyBackup, "open_attempt", flaky)
    inner = FakeBackend(world)
    with pytest.raises(RequestRefused, match="RuntimeError"):
        site.run(inner)
    assert len(inner.executed) == 2
    refused = Path(calls[2])
    assert read_canonical(refused / "receipt.json")["status"] == "refused"
    assert sorted(p.name for p in refused.iterdir()) == ["receipt.json", "started.json"]
    monkeypatch.undo()
    result, _, _ = site.run()
    assert result["status"] == "complete"
    assert all(result["costs"]["actual"][m]["failed_attempt_seconds"] == 0.0 for m in ("S-", "S+"))


def test_safeguard_time_in_a_session_lands_in_the_attempt_timers_and_the_owners_controller_seconds(tmp_path, synthetic):
    """Review finding D: where the safeguard's time is in the Stage B cost record. A destination
    whose every upload takes one fake second shows the split: the copy of ``started.json`` at the
    top of ``execute`` is inside the attempt's own timer (operation seconds, one upload each); the
    settle before the timer and in ``verify`` is controller time of the step that owns the
    operation; the session's very first settle (``study.json``) precedes the start record's clock
    read. Every such second is recorded once, and it enters the policy costs."""
    world, setup = synthetic
    reference_site = Site(tmp_path / "reference", world, setup)
    reference_site.admit()
    reference, _, _ = reference_site.run()
    site = Site(tmp_path / "slow", world, setup)
    site.admit()
    inner = FakeBackend(world)

    def one_second() -> None:
        inner.now += 1.0

    destination = dur.FaultyDestination(site.offsite / "destination", on_upload=one_second)
    result, _, _ = site.run(inner, destination=destination)
    assert result["choices"] == reference["choices"]

    def seconds(root: Path) -> dict:
        return {p.relative_to(root).as_posix(): read_canonical(p)["seconds"]
                for p in sorted(root.glob("**/attempt-*/receipt.json"))}

    slow, plain = seconds(site.root), seconds(reference_site.root)
    assert slow.keys() == plain.keys() and len(slow) > 10
    for name in slow:                                   # one upload (started.json) inside every attempt's timer
        assert slow[name] == pytest.approx(plain[name] + 1.0), name
    sessions = site.root / "blocks" / "0" / "sessions"
    start, end = read_canonical(sessions / "session-1.json"), read_canonical(sessions / "session-1-end.json")
    plain_end = read_canonical(reference_site.root / "blocks" / "0" / "sessions" / "session-1-end.json")
    assert start["seconds"] == 1.0                      # study.json, settled by the session's first sync
    controller = end["controller_seconds"]
    assert sum(plain_end["controller_seconds"].values()) == 0.0
    assert controller["common"] > 0 and controller["S+"] > 0 and controller.get("result", 0.0) == 0.0
    assert end["seconds"] == pytest.approx(sum(slow.values()) + sum(controller.values()))   # every second once
    for method in ("S-", "S+"):                         # and it is in the policy costs
        assert result["costs"]["actual"][method]["total_seconds"] > reference["costs"]["actual"][method]["total_seconds"]
        assert result["costs"]["actual"][method]["controller_seconds"] > 0
    assert len(result["costs"]["actual"]["S-"]["overruns"]) >= len(reference["costs"]["actual"]["S-"]["overruns"])


def test_logs_and_acknowledgements_name_no_operation_arm_or_choice(tmp_path, synthetic):
    world, setup = synthetic
    site = Site(tmp_path, world, setup)
    site.admit()
    result, inner, _ = site.run()
    assert result["status"] == "complete"
    logged = (site.volume / "durability-admin" / "journal.jsonl").read_text() + "".join(
        p.read_text() for p in (site.offsite / "destination" / "study-1" / "acks").glob("*.json"))
    forbidden = [*world.groups["heldout"], "final-", "screen-", "full_from", "attribution-", "ranking", "plan-S",
                 "choice", str(site.root)]
    assert [word for word in forbidden if word in logged] == []
    assert '"unit-acknowledged"' in logged and set(result["choices"].values()) <= {"a0", *world.groups["heldout"]}
    with pytest.raises(DurabilityError, match="must not log recorded paths"):
        StudyBackup(dur.make_vault(tmp_path / "other"), site.root)
    # the manifests, which a restore needs, do hold the paths: they are stored payload, not logs
    manifests = "".join(p.read_text() for p in (site.offsite / "destination" / "study-1" / "manifests").glob("*.json"))
    assert str(site.root) in manifests
