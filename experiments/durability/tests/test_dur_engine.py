"""The administrative unit runner on the engine's ENGINEERING FIXTURES (tiny random model on CPU).

The decisive checks: (a) a complete sealed chain whose source is removed is restored from the
destination into the recorded layout, reverified without any path map and continued, with every
sealed file byte-identical before and after; (c) no next unit launches without the previous unit's
acknowledgement or without a valid lease. Also: a lost attempt and its unknown cost are kept and
its number is never reused; a lost fresh start keeps its registry claim (re-appended when the
restored snapshot predates it) until it is explicitly declared lost, and the retry is the same
draw; an engine failure is kept as a failure record; folders sealed elsewhere are acknowledged in
dependency order. Nothing here is a scientific result or a cloud guarantee."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import dur_fixtures as dur  # noqa: E402
import ss_fixtures as fx  # noqa: E402

from experiments.durability.backup import verify_in_place  # noqa: E402
from experiments.durability.common import (GateRefused, LostAttemptUnresolved, TransferError,  # noqa: E402
                                           VerificationFailed, read_json, read_jsonl, sha256_file)
from experiments.durability.engine_units import UnitRunner, UnitSpec, acknowledge_sealed_tree  # noqa: E402
from experiments.safety_selection import jobs, runner  # noqa: E402
from experiments.safety_selection.verify import verify_run  # noqa: E402

WORKER = "worker-1"
Q = UnitSpec("1101-a0-q", "dev", "a0", 1101, "development", "q", "dev", planned_seconds=60.0)
E1 = UnitSpec("1101-a0-e1", "dev", "a0", 1101, "development", "e1", "dev", resume_from="1101-a0-q",
              planned_seconds=60.0)
E3 = UnitSpec("1101-a0-e3", "dev", "a0", 1101, "development", "e3", None, resume_from="1101-a0-e1",
              planned_seconds=60.0)


class Pod:
    """One worker: a durable volume (``workspace``), an off-pod destination, a fake provider and
    an admission ledger. ``runner()`` is what a (re)started worker process builds."""

    def __init__(self, base: Path, *, balance: float = 100.0) -> None:
        self.base = base.resolve()
        self.workspace = self.base / "volume" / "workspace"
        self.out_root, self.admin = self.workspace / "calibration-001", self.workspace / "durability-admin"
        self.offsite = self.base / "offsite"
        self.clock = dur.ManualClock()
        self.provider = dur.FakeProvider(self.clock, balance=balance)
        self.recipe = fx.recipe()
        self.prepared, self.sha = fx.prepare_dir(self.workspace / "prepared")

    def vault(self, destination=None):
        from experiments.durability.backup import Vault
        from experiments.durability.common import Journal
        from experiments.durability.destination import LocalDirectoryDestination

        return Vault(destination or LocalDirectoryDestination(self.offsite / "destination"), WORKER,
                     journal=Journal(self.admin / "journal.jsonl", self.clock), scratch=self.offsite / "scratch",
                     clock=self.clock)

    def admission(self):
        return dur.admission(self.offsite, self.provider, self.clock)

    def admit(self, seconds: float = 3600.0):
        self.workspace.mkdir(parents=True, exist_ok=True)
        vault = self.vault()
        return self.admission().admit(WORKER, seconds, dur.storage(self.workspace, vault.destination), dur.RESERVE)

    def runner(self, *, destination=None, loaders=None) -> UnitRunner:
        vault = self.vault(destination)
        return UnitRunner(session=runner.Session(self.recipe, loaders or fx.fixture_loaders()),
                          prepared_dir=self.prepared, out_root=self.out_root, admin_dir=self.admin, vault=vault,
                          gate=dur.gate_for(vault, self.admission(), self.clock), worker=WORKER, clock=self.clock)


def kill_at(monkeypatch, pod: Pod, target: str, claim: bool = False):
    """The worker dies while the unit with this target checkpoint runs: no failure record, no
    catalogue outcome. What survives off-pod is the destination as it was at that moment (copied
    aside as ``offsite-at-kill``). With ``claim`` the dying run had already registered its
    trajectory (the engine claims a fresh start before training)."""
    real = runner.run_one

    def dying(job, **kwargs):
        if job["target_checkpoint"] != target:
            return real(job, **kwargs)
        if claim:
            jobs.claim_trajectory(kwargs["registry"],
                                  jobs.trajectory_key(pod.sha, pod.recipe, job["split"], job["arm"], job["seed"],
                                                      job["role"]), str(kwargs["out_dir"]), None)
        shutil.copytree(pod.offsite, pod.base / "offsite-at-kill")
        raise KeyboardInterrupt("ENGINEERING FIXTURE: the worker was terminated")

    monkeypatch.setattr(runner, "run_one", dying)


def lose_the_pod(pod: Pod) -> None:
    """The volume is gone; only what had reached the destination when the worker died remains."""
    shutil.rmtree(pod.base / "volume")
    shutil.rmtree(pod.offsite)
    (pod.base / "offsite-at-kill").rename(pod.offsite)


def test_a_sealed_chain_is_restored_after_its_source_is_removed_and_continued(tmp_path, monkeypatch):
    pod = Pod(tmp_path)
    pod.admit()
    kill_at(monkeypatch, pod, "e3")
    with pytest.raises(KeyboardInterrupt):
        pod.runner().run([Q, E1, E3])
    monkeypatch.undo()
    sealed = {name: dur.tree_hashes(pod.out_root / name) for name in ("1101-a0-q-a1", "1101-a0-e1-a1")}
    prepared_before = dur.tree_hashes(pod.prepared)
    assert not (pod.out_root / "1101-a0-e3-a1").exists()
    lose_the_pod(pod)
    assert not pod.workspace.exists()
    # restore into the recorded layout: the same absolute paths, no receipt rewritten, no path map
    vault = pod.vault()
    code_files = len(vault.pin("code", runner.code_identity()["sha256"]).files)
    report = vault.restore()
    assert report["units"] == 4                                       # prepared, code, q, e1
    assert report["reused_files"] == code_files and report["restored_files"] > 0   # only the source tree was still there
    for name, before in sealed.items():
        assert dur.tree_hashes(pod.out_root / name) == before          # byte-identical, COMPLETE.json and receipts
    assert dur.tree_hashes(pod.prepared) == prepared_before
    check = verify_in_place(pod.out_root / "1101-a0-e1-a1", pod.prepared)
    assert check["path_map"] == [] and check["stream"]["checked"] is True
    assert check["dependency_chain"]["dependencies"][0]["recorded"] == str(pod.out_root / "1101-a0-q-a1")
    # continue: the restarted worker reuses the sealed units and gives the lost work a new attempt
    restarted = pod.runner()
    done = restarted.run([Q, E1, E3])
    assert [(d["unit"], d["reused"]) for d in done] == [("1101-a0-q", True), ("1101-a0-e1", True),
                                                       ("1101-a0-e3", False)]
    e3 = pod.out_root / "1101-a0-e3-a2"                                 # attempt 1 was lost: its number is kept
    assert done[2]["run_dir"] == str(e3) and verify_run(e3, pod.prepared)["complete"]
    assert read_json(e3 / "job.json")["resume_from"] == str(pod.out_root / "1101-a0-e1-a1")
    for name, before in sealed.items():
        assert dur.tree_hashes(pod.out_root / name) == before          # still byte-identical after the continuation
    attempts = {(a["unit"], a["attempt"]): a for a in restarted.attempts()}
    lost = attempts["1101-a0-e3", 1]
    assert lost["state"] == "lost" and lost["outcome"]["cost"].startswith("unknown")
    assert lost["outcome"]["start_utc"] and lost["outcome"]["rate_per_hour"] == pytest.approx(1.62)
    assert lost["outcome"]["folder_present"] is False and lost["lease"]
    assert attempts["1101-a0-e3", 2]["state"] == "sealed"
    assert [attempts[key]["state"] for key in (("1101-a0-q", 1), ("1101-a0-e1", 1))] == ["sealed", "sealed"]
    vault = pod.vault()
    assert vault.check_ack("run", str(e3), sha256_file(e3 / "COMPLETE.json"))["verification"]["folders"] == 3
    # a continuation claims no trajectory: one claim, from the fresh start, never touched
    assert [row["run_dir"] for row in read_jsonl(pod.out_root / "registry.jsonl")] == [str(pod.out_root / "1101-a0-q-a1")]


def test_a_lost_fresh_start_keeps_its_claim_until_it_is_declared_lost(tmp_path, monkeypatch):
    pod = Pod(tmp_path)
    pod.admit()
    kill_at(monkeypatch, pod, "q", claim=True)
    with pytest.raises(KeyboardInterrupt):
        pod.runner().run([Q])
    monkeypatch.undo()
    lost_dir = pod.out_root / "1101-a0-q-a1"
    assert [row["run_dir"] for row in read_jsonl(pod.out_root / "registry.jsonl")] == [str(lost_dir)]
    lose_the_pod(pod)
    pod.vault().restore()
    assert not (pod.out_root / "registry.jsonl").exists()        # the last snapshot predates the lost claim
    restarted = pod.runner()
    policy_loads = []
    restarted.session.loaders = fx.fixture_loaders(on_policy_load=lambda: policy_loads.append(1))
    with pytest.raises(LostAttemptUnresolved):
        restarted.run([Q])
    assert not policy_loads and not (pod.out_root / "1101-a0-q-a2").exists()    # nothing was launched
    claims = read_jsonl(pod.out_root / "registry.jsonl")
    assert [row["run_dir"] for row in claims] == [str(lost_dir)] and "reconstructed_by" in claims[0]
    registry_before = (pod.out_root / "registry.jsonl").read_bytes()
    # the engine itself refuses the rerun while the claim has no failure record
    with pytest.raises(jobs.JobError, match="already started"):
        jobs.claim_trajectory(pod.out_root / "registry.jsonl", claims[0]["key"], str(pod.out_root / "x"), None)
    assert (pod.out_root / "registry.jsonl").read_bytes() == registry_before
    with pytest.raises(Exception, match="operator and reason"):
        restarted.declare_lost("1101-a0-q", 1, operator="", reason="")
    tombstone = restarted.declare_lost("1101-a0-q", 1, operator="test operator",
                                       reason="ENGINEERING FIXTURE: the pod was terminated")
    assert tombstone == lost_dir / "error.txt" and "ADMINISTRATIVE TOMBSTONE" in tombstone.read_text()
    done = pod.runner().run([Q])
    assert done[0]["run_dir"] == str(pod.out_root / "1101-a0-q-a2") and not done[0]["reused"]
    registry = (pod.out_root / "registry.jsonl").read_bytes()
    assert registry.startswith(registry_before)                   # claims are appended, never cleared
    assert read_jsonl(pod.out_root / "registry.jsonl")[-1]["retry_after_failures"] == [str(lost_dir)]   # the same draw
    states = {(a["unit"], a["attempt"]): (a["state"], a["tombstoned"]) for a in pod.runner().attempts()}
    assert states == {("1101-a0-q", 1): ("lost", True), ("1101-a0-q", 2): ("sealed", False)}


def test_no_unit_launches_without_the_previous_acknowledgement_or_a_valid_lease(tmp_path):
    pod = Pod(tmp_path)
    with pytest.raises(GateRefused, match="no admission lease"):
        pod.runner().run([Q])                                       # never admitted
    assert not list(pod.out_root.glob("1101-*"))
    pod.admit(seconds=600.0)
    pod.clock.advance(590.0)                                        # 10 s left, the unit plans 60 s
    with pytest.raises(GateRefused, match="renewed admission"):
        pod.runner().run([Q])
    pod.clock.advance(60.0)
    with pytest.raises(GateRefused, match="expired"):
        pod.runner().run([Q])
    assert not list(pod.out_root.glob("1101-*"))
    pod.provider.balance = dur.FakeProvider(pod.clock).balance      # a fresh reading for the renewal
    pod.provider.rates = dur.rate_card(pod.clock)
    pod.admit()
    # q seals, but its copy cannot reach the destination: there is no acknowledgement
    broken = dur.FaultyDestination(pod.offsite / "destination", refuse_uploads=True)
    pod.runner().prepare()
    with pytest.raises(TransferError):
        pod.runner(destination=broken).run([Q, E1])
    q = pod.out_root / "1101-a0-q-a1"
    assert read_json(q / "status.json")["status"] == "complete" and (q / "COMPLETE.json").is_file()
    assert not (pod.out_root / "1101-a0-e1-a1").exists()
    again = pod.runner(destination=broken)
    with pytest.raises(TransferError):                              # a restart retries the copy first; still no e1
        again.run([Q, E1])
    assert not (pod.out_root / "1101-a0-e1-a1").exists()
    assert [a["unit"] for a in again.attempts()] == ["1101-a0-q"]
    # the gate itself: a sealed folder and a sender-side "complete" status are not an acknowledgement
    with pytest.raises(GateRefused, match="not acknowledged"):
        again.gate.require(WORKER, again._previous(), 60.0)
    with pytest.raises(VerificationFailed):
        again.vault.check_ack("run", str(q), sha256_file(q / "COMPLETE.json"))
    refusals = [row for row in again.vault.journal.read() if row["event"] == "dispatch-refused"]
    assert refusals and "not acknowledged" in refusals[-1]["reason"]
    # with the destination back, q is acknowledged first and only then does e1 start
    done = pod.runner().run([Q, E1])
    assert [(d["unit"], d["reused"]) for d in done] == [("1101-a0-q", True), ("1101-a0-e1", False)]
    events = [(row["event"], row.get("path")) for row in pod.vault().journal.read() if row["event"] == "unit-acknowledged"]
    assert [path for _, path in events][-2:] == [str(q), str(pod.out_root / "1101-a0-e1-a1")]


def test_an_engine_failure_is_kept_as_a_failure_record_and_retried_as_the_same_draw(tmp_path):
    pod = Pod(tmp_path)
    pod.admit()
    with pytest.raises(RuntimeError, match="injected guard failure"):
        pod.runner(loaders=fx.fixture_loaders(guard_fails=True)).run([Q])
    failed = pod.out_root / "1101-a0-q-a1"
    assert (failed / "error.txt").is_file() and not (failed / "COMPLETE.json").exists()
    vault = pod.vault()
    ack = vault.check_ack("failed-run", str(failed), sha256_file(failed / "error.txt"))
    assert ack["verification"]["folders"] == 0 and ack["unit_kind"] == "failed-run"    # bytes only: not a result
    done = pod.runner().run([Q])
    assert done[0]["run_dir"] == str(pod.out_root / "1101-a0-q-a2")
    states = [(a["attempt"], a["state"]) for a in pod.runner().attempts()]
    assert states == [(1, "failed"), (2, "sealed")]
    claims = read_jsonl(pod.out_root / "registry.jsonl")
    assert claims[-1]["retry_after_failures"] == [str(failed)] and claims[0]["key"]["seed"] == 1101
    assert read_json(pod.out_root / "1101-a0-q-a2" / "job.json")["seed"] == 1101    # the same seed: the same draw
    logged = (pod.admin / "journal.jsonl").read_text()
    assert "injected guard failure" not in logged and "RuntimeError" not in logged   # logs carry no error text


def test_folders_sealed_elsewhere_are_acknowledged_in_dependency_order(tmp_path):
    pod = Pod(tmp_path)
    session = runner.Session(pod.recipe, fx.fixture_loaders())
    runner.calibrate(prepared_dir=pod.prepared, out_root=pod.out_root, session=session, arms=["a0"], seeds=[1101],
                     checkpoints=["q", "e1"])
    vault = pod.vault()
    UnitRunner(session=session, prepared_dir=pod.prepared, out_root=pod.out_root, admin_dir=pod.admin, vault=vault,
               gate=None, worker=WORKER, clock=pod.clock).prepare()
    report = acknowledge_sealed_tree(vault, pod.out_root)
    assert len(report["acknowledged"]) == 2 and report["not_acknowledged"] == {}
    order = [row["path"] for row in vault.journal.read() if row["event"] == "unit-acknowledged"][-2:]
    assert order == [str(pod.out_root / "1101-a0-q-a1"), str(pod.out_root / "1101-a0-e1-a1")]   # q before e1
    assert acknowledge_sealed_tree(vault, pod.out_root)["not_acknowledged"] == {}
