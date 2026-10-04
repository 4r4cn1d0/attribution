"""The gated pod worker on the engine's ENGINEERING FIXTURES (tiny random model on CPU; a folder as
the destination; a fake provider; no pod, key or request).

The decisive check is scientific identity: for the same arm, seed, prepared data and recipe, the
worker's sealed folders equal the engine's own ``calibrate``, except in fields that two
``calibrate`` runs differ in themselves (timings and timestamps, and the hashes of the files that
hold them) and, against the plan's command with relative paths, in how paths are spelled. Both
sets are measured here, not assumed. The rest: the identities checked before anything runs;
restore and continuation after a kill between units and in the middle of one; refusal without a
lease and without an acknowledgement; a tree made by plain ``calibrate`` taken over; tombstones
only as the operator named them; the lease kept alive; the finishing stop through the timer.

Nothing here is a scientific result or a statement about RunPod or GitHub."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import dur_fixtures as dur  # noqa: E402
import ss_fixtures as fx  # noqa: E402

from experiments.durability import worker as wk  # noqa: E402
from experiments.durability.admission import AdmissionController  # noqa: E402
from experiments.durability.backup import Vault  # noqa: E402
from experiments.durability.common import (AdmissionRefused, Journal, LostAttemptUnresolved, TransferError,  # noqa: E402
                                           read_json, read_jsonl)
from experiments.durability.destination import LocalDirectoryDestination  # noqa: E402
from experiments.safety_selection import jobs, runner  # noqa: E402
from experiments.safety_selection.common import code_identity  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402
from experiments.safety_selection.prepare import load_prepared, read_manifest  # noqa: E402
from experiments.safety_selection.verify import verify_run  # noqa: E402

HOST = "dev05"
UNIT_SECONDS = {"q": 60.0, "e1": 60.0, "e3": 60.0}


class FakeShutdown:
    """The stop timer's worker side, as far as the worker's finish needs it."""

    def __init__(self) -> None:
        self.finished: list[tuple] = []
        self.fail = False

    def finish(self, worker, pod, after_seconds, reason):
        if self.fail:
            raise RuntimeError("ENGINEERING FIXTURE: the timer does not answer")
        self.finished.append((worker, pod, after_seconds, reason))
        return {"finishing": True, "pod": pod, "stop_at_utc": "later"}


class Study:
    """A study root as the bootstrap leaves it on a pod's volume: prepared data, the recipe, the
    plan and the fixture record; and outside it the off-pod destination and a fake provider."""

    def __init__(self, base: Path, *, jobs_for_host: list | None = None, balance: float = 100.0) -> None:
        self.base = base.resolve()
        self.root = self.base / "volume" / "study"
        self.offsite = self.base / "offsite"
        self.clock = dur.ManualClock()
        self.provider = dur.FakeProvider(self.clock, balance=balance)
        self.shutdown = FakeShutdown()
        self.jobs_for_host = jobs_for_host
        self.destination = None
        self.last_error: BaseException | None = None
        self.build_root()

    def build_root(self) -> None:
        """What the bundles and the bootstrap put on a fresh volume (always the same bytes)."""
        fx.prepare_dir(self.root / "prepared-v2")
        (self.root / "configs").mkdir(parents=True, exist_ok=True)
        recipe_path = self.root / "configs" / "recipe.json"
        recipe_path.write_text(json.dumps(fx.recipe(), indent=1))
        manifest_sha = read_manifest(self.root / "prepared-v2")[1]
        if self.jobs_for_host is None:
            group = sorted(load_prepared(self.root / "prepared-v2", manifest_sha).groups["dev"])[0]
            self.jobs_for_host = [{"seed": 1101, "arm": group}, {"seed": 1102, "arm": "a0"}]
        plan = {"engine_sha256": code_identity()["sha256"], "recipe_sha256": config_sha256(load_recipe(recipe_path)),
                "recipe_path": "configs/recipe.json", "prepared_path": "prepared-v2", "manifest_sha256": manifest_sha,
                "assignments": {HOST: self.jobs_for_host, "dev06": [{"seed": 1101, "arm": "a0"}]}}
        (self.root / "plan.json").write_text(json.dumps(plan, indent=1))
        (self.root / "BOOTSTRAP-VERIFIED.json").write_text(json.dumps({"fixture_exact": True}))

    def config(self, **changes) -> wk.WorkerConfig:
        data = {"host": HOST, "root": str(self.root), "plan": "plan.json", "out_root": "dev-matrix-002",
                "unit_seconds": UNIT_SECONDS, "scratch": str(self.base / "scratch"), **changes}
        return wk.load_config(data)

    def services(self) -> wk.Services:
        destination = self.destination or LocalDirectoryDestination(self.offsite / "destination")
        admin = self.root / "durability-admin" / HOST
        journal = Journal(admin / "journal.jsonl", self.clock)
        vault = Vault(destination, HOST, journal=journal, scratch=self.base / "scratch", clock=self.clock)
        controller = AdmissionController(admin / "reservations.jsonl", self.provider, dur.POLICY, dur.rate_card(self.clock),
                                         journal=journal, clock=self.clock)
        return wk.Services(vault=vault, controller=controller, storage=dur.storage(self.root, destination),
                           retention_reserve=dur.RESERVE, shutdown=self.shutdown, pod="pod-1", clock=self.clock)

    def worker(self, loaders=None, **changes) -> wk.Worker:
        config = self.config(**changes)

        def job(index: int) -> int:                    # a fresh engine session per job, as a new process has
            session = lambda c: runner.Session(load_recipe(c.root / "configs" / "recipe.json"),  # noqa: E731
                                               loaders() if loaders else fx.fixture_loaders())
            try:
                wk.job_main(config, index, services=self.services(), session_factory=session)
                return 0
            except BaseException as exc:  # noqa: BLE001 - a job process reports failure by its exit status
                self.last_error = exc
                return 1

        return wk.Worker(config, services=self.services(), run_job_process=job)

    def units(self) -> list[str]:
        out = self.root / "dev-matrix-002"
        return sorted(p.name for p in out.iterdir() if p.is_dir()) if out.is_dir() else []

    def outcome(self) -> dict:
        records = sorted((self.root / "durability-admin" / HOST).glob("worker-outcome-*.json"))
        return read_json(records[-1])

    def lose_the_volume(self, keep_offsite_as_of: Path | None = None) -> None:
        shutil.rmtree(self.base / "volume")
        if keep_offsite_as_of is not None:
            shutil.rmtree(self.offsite)
            keep_offsite_as_of.rename(self.offsite)
        shutil.rmtree(self.base / "scratch", ignore_errors=True)


@pytest.fixture
def study(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)                           # the worker changes directory; undone after the test
    return Study(tmp_path)


# ----- scientific identity ----------------------------------------------------------------------


def snapshot(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def leaves(value, path: str = "") -> dict[str, object]:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            out.update(leaves(item, f"{path}/{key}"))
        return out
    if isinstance(value, list):
        out = {}
        for index, item in enumerate(value):
            out.update(leaves(item, f"{path}[{index}]"))
        return out
    return {path: value}


def generalise(path: str) -> str:
    """A leaf's path with list positions and file names inside hashed-file tables left out, so that
    'the same field' is the same in every unit and every line."""
    import re

    return re.sub(r"\[\d+\]", "[*]", path)


def differences(first: dict[str, bytes], second: dict[str, bytes]) -> dict[tuple[str, str], list]:
    """Every differing leaf of two trees as {(file, generalised leaf path): [(a, b), ...]}. JSON and
    JSON-lines files are compared leaf by leaf; any other file as a whole."""
    assert sorted(first) == sorted(second), "the two trees do not hold the same files"
    out: dict[tuple[str, str], list] = {}
    for name in sorted(first):
        if first[name] == second[name]:
            continue
        generic = "/".join(part if not part.endswith(("-a1", "-a2")) else "<unit>" for part in name.split("/"))
        if name.endswith(".json"):
            a, b = leaves(json.loads(first[name])), leaves(json.loads(second[name]))
        elif name.endswith(".jsonl"):
            rows_a, rows_b = first[name].splitlines(), second[name].splitlines()
            assert len(rows_a) == len(rows_b), f"{name}: another number of lines"
            a = leaves([json.loads(row) for row in rows_a])
            b = leaves([json.loads(row) for row in rows_b])
        else:
            out.setdefault((generic, "<bytes>"), []).append((len(first[name]), len(second[name])))
            continue
        assert list(a) == list(b), f"{name}: another structure"
        for path in a:
            if a[path] != b[path]:
                out.setdefault((generic, generalise(path)), []).append((a[path], b[path]))
    return out


def chain_names(job: dict) -> list[str]:
    return [f"{job['seed']}-{job['arm']}-{name}-a1" for name in ("q", "e1", "e3")]


def test_the_workers_sealed_folders_equal_calibrates_except_where_calibrate_differs_from_itself(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    study = Study(tmp_path)
    job = study.jobs_for_host[0]
    names = chain_names(job)
    out_root = study.root / "dev-matrix-002"

    def calibrate(prepared, out) -> dict[str, bytes]:
        """The engine's own loop for this job, then the tree set aside so that the next run writes
        the very same paths."""
        session = runner.Session(load_recipe(study.root / "configs" / "recipe.json"), fx.fixture_loaders())
        os.chdir(study.root)
        runner.calibrate(prepared_dir=prepared, out_root=out, session=session, arms=[job["arm"]], seeds=[job["seed"]])
        tree = snapshot(out_root)
        shutil.rmtree(out_root)
        return tree

    first = calibrate(study.root / "prepared-v2", out_root)                 # absolute paths
    second = calibrate(study.root / "prepared-v2", out_root)                # the same again
    relative = calibrate("prepared-v2", "dev-matrix-002")                   # as the plan's command spells them

    report = study.worker().run()                                           # both jobs; the first is compared
    assert report["complete"] is True
    worker = {name: data for name, data in snapshot(out_root).items() if name.split("/")[0] in names + ["registry.jsonl"]}
    worker_units = {name: data for name, data in worker.items() if name != "registry.jsonl"}
    units = lambda tree: {name: data for name, data in tree.items() if name != "registry.jsonl"}  # noqa: E731

    # 1. what two calibrate runs differ in between themselves: the engine's own run-to-run variation
    own = differences(units(first), units(second))
    volatile = set(own)
    assert volatile, "two calibrate runs were byte-identical: the comparison below would be empty"
    timing_words = ("seconds", "_s", "utc", "sha256", "files/", "elapsed")
    assert all(any(word in path for word in timing_words) for _, path in volatile), sorted(volatile)

    # 2. the worker against calibrate with the same absolute paths: nothing outside that variation
    against_absolute = differences(units(first), worker_units)
    assert set(against_absolute) <= volatile, sorted(set(against_absolute) - volatile)

    # 3. the worker against the plan's own spelling (relative paths): additionally only how paths are
    #    spelled, each resolving to the same place, and the hashes of the two files that hold them
    against_relative = differences(units(relative), worker_units)
    extra = set(against_relative) - volatile
    spelled = {("<unit>/job.json", "/resume_from"), ("<unit>/assets.json", "/loaded_in/policy"),
               ("<unit>/assets.json", "/loaded_in/guard"), ("<unit>/dependencies.json", "/dependencies[*]/path"),
               ("<unit>/COMPLETE.json", "/resumed_from"), ("<unit>/records.jsonl", "[*]/loaded_in"),
               ("<unit>/records.jsonl", "[*]/done_in"), ("<unit>/records.jsonl", "[*]/from_run")}
    hashed = {("<unit>/COMPLETE.json", "/job_sha256"), ("<unit>/COMPLETE.json", "/files/job.json"),
              ("<unit>/COMPLETE.json", "/files/assets.json"), ("<unit>/dependencies.json", "/dependencies[*]/job_sha256")}
    assert extra <= spelled | hashed, sorted(extra - spelled - hashed)
    for key in extra & spelled:
        for was, now in against_relative[key]:
            assert Path(now).is_absolute() and (study.root / was).resolve() == Path(now).resolve(), (key, was, now)

    # 4. what must be equal is equal: every saved state and every evaluation output, byte for byte
    exact = [name for name in worker_units if name.endswith(".safetensors") or "/eval/" in f"/{name}"
             and not name.endswith("summary.json")]
    assert len([n for n in exact if n.endswith(".safetensors")]) >= 9 and len(exact) > 9
    for name in exact:
        assert first[name] == worker_units[name] == relative[name], name
    for name in names:                                                       # and the engine verifies each folder
        assert verify_run(out_root / name, study.root / "prepared-v2")["complete"]

    # 5. the registry: one claim for the fresh start, the same key; only the time and the spelling differ
    claims = [json.loads(row) for row in worker["registry.jsonl"].splitlines()]
    theirs = [json.loads(row) for row in first["registry.jsonl"].splitlines()]
    mine = [row for row in claims if row["key"]["arm"] == job["arm"] and row["key"]["seed"] == job["seed"]]
    assert len(mine) == len(theirs) == 1 and {k: v for k, v in mine[0].items() if k != "utc"} == {
        k: v for k, v in theirs[0].items() if k != "utc"}
    assert len(claims) == 2                                                  # the second job's own fresh start


# ----- the identities checked before anything runs ----------------------------------------------


def test_the_worker_refuses_a_host_whose_engine_recipe_data_or_fixture_differ_from_the_plan(study):
    plan = read_json(study.root / "plan.json")
    cases = {"engine_sha256": "engine", "recipe_sha256": "recipe", "manifest_sha256": "manifest"}
    for key in cases:
        (study.root / "plan.json").write_text(json.dumps({**plan, key: "0" * 64}))
        with pytest.raises(wk.WorkerRefused, match=f"{key}.*differ from the frozen plan"):
            study.worker().run()
    (study.root / "plan.json").write_text(json.dumps(plan))
    (study.root / "BOOTSTRAP-VERIFIED.json").write_text(json.dumps({"fixture_exact": False}))
    with pytest.raises(wk.WorkerRefused, match="exact two-step fixture is missing"):
        study.worker().run()
    (study.root / "BOOTSTRAP-VERIFIED.json").unlink()
    with pytest.raises(wk.WorkerRefused, match="exact two-step fixture is missing"):
        study.worker().run()
    (study.root / "BOOTSTRAP-VERIFIED.json").write_text(json.dumps({"fixture_exact": True}))
    with pytest.raises(wk.WorkerRefused, match="assigns nothing to host"):
        study.worker(host="dev99").run()
    assert study.units() == [] and study.services().vault.acknowledged_units() == []  # nothing ran, nothing was acknowledged
    outcomes = sorted((study.root / "durability-admin" / HOST).glob("worker-outcome-*.json"))
    assert len(outcomes) == 5 and all(read_json(path)["complete"] is False for path in outcomes)
    assert len(study.shutdown.finished) == 6             # an idle billed pod helps no one: the timer is asked to stop it
    for bad in ({"surprise": 1}, {"root": "relative"}, {"unit_seconds": {}}, {"unit_seconds": {"q": 0}},
                {"tombstones": [{"unit": "x"}]}, {"tombstones": [{"unit": "x", "attempt": 1, "operator": "", "reason": "r"}]}):
        with pytest.raises(wk.WorkerRefused):
            study.config(**bad)
    with pytest.raises(wk.WorkerRefused, match="no planned time for checkpoints"):
        study.worker(unit_seconds={"q": 60.0}).run()
    assert study.worker(stop_on_failure=False, unit_seconds={"q": 60.0}).config.stop_on_failure is False


def test_a_dev_only_plan_is_enforced_as_calibrate_enforces_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    study = Study(tmp_path, jobs_for_host=[{"seed": 2101, "arm": "a0"}])        # a selector seed
    with pytest.raises(wk.WorkerRefused):
        study.worker().run()
    assert isinstance(study.last_error, jobs.AccessError) and "not a development seed" in str(study.last_error)
    other = Study(tmp_path / "other", jobs_for_host=[{"seed": 1101, "arm": "g-0000000000000000"}])
    with pytest.raises(wk.WorkerRefused):
        other.worker().run()
    assert "not a development group" in str(other.last_error) and study.units() == other.units() == []


# ----- the safeguards between units ---------------------------------------------------------------


def test_the_worker_runs_both_jobs_with_a_lease_and_an_acknowledgement_for_every_unit_and_then_asks_for_the_stop(study):
    outcome = study.worker().run()
    first, second = study.jobs_for_host
    expected = sorted(chain_names(first) + chain_names(second))
    assert outcome["complete"] is True and study.units() == expected
    vault = study.services().vault
    acknowledged = {unit.root for unit in vault.acknowledged_units() if unit.kind == "run"}
    assert acknowledged == {str(study.root / "dev-matrix-002" / name) for name in expected}
    reports = [job["report"] for job in outcome["jobs"]]
    assert [[u["unit"] for u in r["units"]] for r in reports] == [[n[:-3] for n in chain_names(first)],
                                                                  [n[:-3] for n in chain_names(second)]]
    assert all(u["reused"] is False and u["launch_seconds"] > 0 and u["acknowledge_seconds"] > 0
               for r in reports for u in r["units"])
    assert reports[0]["admissions"][0]["why"] == "before the unit"       # (the test's clock stands still: one lease covers all)
    # each job ran in its own engine session: both loaded the model afresh, as two calibrate processes do
    for job in (first, second):
        assets = read_json(study.root / "dev-matrix-002" / chain_names(job)[0] / "assets.json")
        assert assets["loaded_in"]["policy"].endswith(chain_names(job)[0])
    # the finish: a record, the lease released, the timer asked to stop the pod (never a deletion)
    assert study.shutdown.finished == [(HOST, "pod-1", 120.0, "the host's jobs are complete and acknowledged")]
    assert study.services().controller.current_lease(HOST) is None
    record = study.outcome()
    assert record["complete"] is True and record["stop"]["finishing"] is True and record["host"] == HOST
    events = [row["event"] for row in read_jsonl(study.root / "durability-admin" / HOST / "worker.jsonl")]
    assert events[0] == "worker-started" and events[-1] == "worker-finished" and events.count("job-finished") == 2
    # what the records say about time and cost (the validation's report)
    report = wk.measurements(study.root / "durability-admin" / HOST)
    assert len(report["units"]) == 6 and set(report["by_checkpoint"]) == {"q", "e1", "e3"}
    assert all(u["run_seconds"] > 0 and u["copy_seconds"] > 0 and u["restore_check_seconds"] > 0 and u["bytes"] > 0
               for u in report["units"])
    assert report["rate_per_hour"] == pytest.approx(1.62) and 0 < report["safeguard_fraction"] < 1
    worst = report["by_checkpoint"]["e3"]
    assert worst["units"] == 2 and worst["cost_per_unit"] == pytest.approx(
        max((u["run_seconds"] + u["acknowledge_seconds"]) * 1.62 / 3600 for u in report["units"] if u["checkpoint"] == "e3"))
    assert report["admissions"] == 1 and report["timer"] is None and report["restores"][0]["units"] == 0
    # run again (the pod was started once more): nothing is retrained, everything is reused
    before = {name: dur.tree_hashes(study.root / "dev-matrix-002" / name) for name in expected}
    again = study.worker().run()
    assert all(u["reused"] is True and u["launch_seconds"] is None for job in again["jobs"] for u in job["report"]["units"])
    assert {name: dur.tree_hashes(study.root / "dev-matrix-002" / name) for name in expected} == before
    assert len(study.shutdown.finished) == 2


def test_without_a_lease_nothing_is_trained(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    study = Study(tmp_path, balance=0.5)                 # the balance does not cover a unit
    with pytest.raises(wk.WorkerRefused, match="job 0 ended with status 1"):
        study.worker().run()
    assert isinstance(study.last_error, AdmissionRefused) and "insufficient runway" in str(study.last_error)
    assert study.units() == [] and not (study.root / "dev-matrix-002" / "registry.jsonl").exists()
    outcome = study.outcome()
    assert outcome["complete"] is False and outcome["jobs"][0]["exit"] == 1 and len(outcome["jobs"]) == 1
    assert study.shutdown.finished and study.shutdown.finished[0][3] == "the worker refused or failed"
    study.provider.balance = type(study.provider.balance)(100.0, "USD", dur.iso(study.clock()), "fake provider",
                                                          study.provider.balance.kind, True)
    assert study.worker().run()["complete"] is True      # funded: the same command now runs


def test_without_an_acknowledgement_the_next_unit_does_not_start(study, monkeypatch):
    study.destination = dur.FaultyDestination(study.offsite / "destination")
    first = study.jobs_for_host[0]
    q, e1, _ = chain_names(first)
    real = runner.run_one

    def then_the_destination_fails(job, **kwargs):       # the unit seals; its copy cannot leave the pod
        result = real(job, **kwargs)
        study.destination.refuse_uploads = True
        return result

    monkeypatch.setattr(runner, "run_one", then_the_destination_fails)
    with pytest.raises(wk.WorkerRefused):
        study.worker().run()
    monkeypatch.undo()
    monkeypatch.chdir(study.base)
    assert isinstance(study.last_error, TransferError)
    out = study.root / "dev-matrix-002"
    assert (out / q / "COMPLETE.json").is_file() and not (out / e1).exists()         # q sealed; e1 never began
    assert [u.root for u in study.services().vault.acknowledged_units() if u.kind == "run"] == []
    study.destination = None                             # the destination answers again
    outcome = study.worker().run()
    units = outcome["jobs"][0]["report"]["units"]
    assert [(u["unit"], u["reused"]) for u in units] == [(q[:-3], True), (e1[:-3], False), (chain_names(first)[2][:-3], False)]


def test_a_lease_that_is_about_to_end_is_renewed_while_the_unit_runs(study):
    config, services = study.config(), study.services()
    log_rows: list = []
    leases = wk.Leases(services, config, lambda event, **fields: log_rows.append((event, fields)))
    spec = wk.UnitSpec("1101-a0-q", "dev", "a0", 1101, "development", "q", "dev", planned_seconds=600.0)
    assert leases.need(spec) == 600.0 * 1.5 + 600.0
    leases.ensure(spec)
    first = services.controller.current_lease(HOST)
    leases.ensure(spec)                                  # still covered: no second admission
    assert len(leases.admissions) == 1 and services.controller.current_lease(HOST).lease == first.lease
    leases._current = spec
    study.clock.advance(1500.0 - 301.0)
    assert leases.extend_if_needed() is False            # more than the margin is left
    study.clock.advance(2.0)
    study.provider.balance = type(study.provider.balance)(100.0, "USD", dur.iso(study.clock()), "fake provider",
                                                          study.provider.balance.kind, True)
    assert leases.extend_if_needed() is True             # the unit outlasted its lease: renewed
    renewed = services.controller.current_lease(HOST)
    assert renewed.lease != first.lease and renewed.expires_utc > first.expires_utc
    assert leases.admissions[-1]["why"] == "the unit outlasted its lease"
    study.clock.advance(1000.0)
    study.provider.balance = type(study.provider.balance)(0.01, "USD", dur.iso(study.clock()), "fake provider",
                                                          study.provider.balance.kind, True)
    assert leases.extend_if_needed() is False            # refused: the unit keeps the stop time it has
    assert log_rows[-1][0] == "lease-renewal-refused" and "insufficient runway" in log_rows[-1][1]["reason"]
    leases.before_unit(spec) if False else None
    leases._current = None
    assert leases.extend_if_needed() is False            # no unit in hand: nothing to renew


# ----- restore and continuation --------------------------------------------------------------------


def kill_job_at(monkeypatch, study: Study, target: str, claim: bool = False) -> None:
    """The pod dies while the unit with this target checkpoint runs (as test_dur_engine does it):
    no failure record, no catalogue outcome; what is off-pod is what was there at that moment."""
    real = runner.run_one

    def dying(job, **kwargs):
        if job["target_checkpoint"] != target:
            return real(job, **kwargs)
        if claim:
            sha = read_manifest(study.root / "prepared-v2")[1]
            jobs.claim_trajectory(kwargs["registry"], jobs.trajectory_key(sha, fx.recipe(), job["split"], job["arm"],
                                                                         job["seed"], job["role"]), str(kwargs["out_dir"]), None)
        shutil.copytree(study.offsite, study.base / "offsite-at-kill")
        raise KeyboardInterrupt("ENGINEERING FIXTURE: the pod was lost")

    monkeypatch.setattr(runner, "run_one", dying)


def test_a_pod_lost_in_the_middle_of_a_unit_is_restored_on_a_fresh_volume_and_continued(study, monkeypatch):
    first = study.jobs_for_host[0]
    q, e1, e3 = chain_names(first)
    kill_job_at(monkeypatch, study, "e3")
    with pytest.raises(wk.WorkerRefused):
        study.worker().run()
    monkeypatch.undo()
    monkeypatch.chdir(study.base)
    out = study.root / "dev-matrix-002"
    sealed = {name: dur.tree_hashes(out / name) for name in (q, e1)}
    study.lose_the_volume(keep_offsite_as_of=study.base / "offsite-at-kill")
    assert not study.root.exists()
    study.build_root()                                   # a fresh pod: the bundles and the bootstrap again
    outcome = study.worker().run()
    assert outcome["complete"] is True and outcome["restore"]["units"] == 4 and outcome["restore"]["restored_files"] > 0
    for name, before in sealed.items():
        assert dur.tree_hashes(out / name) == before     # byte-identical, receipts included
    units = outcome["jobs"][0]["report"]["units"]
    assert [(u["unit"], u["reused"]) for u in units] == [(q[:-3], True), (e1[:-3], True), (e3[:-3], False)]
    assert units[2]["run_dir"] == str(out / (e3[:-1] + "2"))           # attempt 1 was lost: its number is kept
    assert verify_run(out / (e3[:-1] + "2"), study.root / "prepared-v2")["complete"]
    catalogue = read_jsonl(study.root / "durability-admin" / HOST / "attempts.jsonl")
    lost = [row for row in catalogue if row["event"] == "attempt-lost"]
    assert [(row["unit"], row["attempt"]) for row in lost] == [(e3[:-3], 1)] and lost[0]["cost"].startswith("unknown")
    assert len(read_jsonl(out / "registry.jsonl")) == 2                 # one claim per job; the continuation claimed nothing


def test_a_pod_lost_between_two_units_is_restored_and_continued_without_a_lost_attempt(study, monkeypatch):
    first = study.jobs_for_host[0]
    q, e1, e3 = chain_names(first)
    real = wk.Leases.before_unit

    def dying(self, spec):                               # the pod dies after q's acknowledgement, before e1 begins
        if spec.target_checkpoint == "e1":
            shutil.copytree(study.offsite, study.base / "offsite-at-kill")
            raise KeyboardInterrupt("ENGINEERING FIXTURE: the pod was lost")
        return real(self, spec)

    monkeypatch.setattr(wk.Leases, "before_unit", dying)
    with pytest.raises(wk.WorkerRefused):
        study.worker().run()
    monkeypatch.undo()
    monkeypatch.chdir(study.base)
    out = study.root / "dev-matrix-002"
    before = dur.tree_hashes(out / q)
    study.lose_the_volume(keep_offsite_as_of=study.base / "offsite-at-kill")
    study.build_root()
    outcome = study.worker().run()
    units = outcome["jobs"][0]["report"]["units"]
    assert [(u["unit"], u["reused"], Path(u["run_dir"]).name) for u in units] == [(q[:-3], True, q), (e1[:-3], False, e1),
                                                                                (e3[:-3], False, e3)]
    assert dur.tree_hashes(out / q) == before
    assert not [row for row in read_jsonl(study.root / "durability-admin" / HOST / "attempts.jsonl") if row["event"] == "attempt-lost"]


def test_a_lost_fresh_start_waits_for_the_tombstone_the_operator_named(study, monkeypatch):
    first = study.jobs_for_host[0]
    q = chain_names(first)[0]
    kill_job_at(monkeypatch, study, "q", claim=True)
    with pytest.raises(wk.WorkerRefused):
        study.worker().run()
    monkeypatch.undo()
    monkeypatch.chdir(study.base)
    with pytest.raises(wk.WorkerRefused):                # restarted without a tombstone: refused, nothing launched
        study.worker().run()
    assert isinstance(study.last_error, LostAttemptUnresolved)
    out = study.root / "dev-matrix-002"
    assert not (out / (q[:-1] + "2")).exists()
    wrong = [{"unit": chain_names(first)[1][:-3], "attempt": 1, "operator": "test operator", "reason": "another unit"}]
    with pytest.raises(wk.WorkerRefused):                # a tombstone for something else changes nothing
        study.worker(tombstones=wrong).run()
    named = [{"unit": q[:-3], "attempt": 1, "operator": "test operator", "reason": "ENGINEERING FIXTURE: the pod was lost"}]
    outcome = study.worker(tombstones=named).run()
    report = outcome["jobs"][0]["report"]
    assert report["tombstones"] == [{"unit": q[:-3], "attempt": 1}] and report["units"][0]["run_dir"] == str(out / (q[:-1] + "2"))
    assert "ADMINISTRATIVE TOMBSTONE" in (out / q / "error.txt").read_text() and "test operator" in (out / q / "error.txt").read_text()
    claims = read_jsonl(out / "registry.jsonl")
    retry = [row for row in claims if row["run_dir"] == str(out / (q[:-1] + "2"))]
    assert retry and retry[0]["retry_after_failures"] == [str(out / q)]              # the same draw, the lost attempt kept
    again = study.worker(tombstones=named).run()         # the tombstone stays in the configuration: applied once only
    assert again["jobs"][0]["report"]["tombstones"] == []


def test_a_tree_made_by_plain_calibrate_is_taken_over_acknowledged_and_continued(study, monkeypatch):
    """A host that ran the 2 October way (calibrate with relative paths, no catalogue, no vault) and
    was lost while e3 ran: its sealed units are adopted and acknowledged, the unfinished attempt is
    kept as lost with an unknown cost, and the chain continues as the next attempt."""
    first = study.jobs_for_host[0]
    q, e1, e3 = chain_names(first)
    out = study.root / "dev-matrix-002"
    real = runner.run_one

    def dying(job, **kwargs):
        if job["target_checkpoint"] != "e3":
            return real(job, **kwargs)
        Path(kwargs["out_dir"]).mkdir(parents=True)      # the folder exists, half written, when the pod is lost
        (Path(kwargs["out_dir"]) / "job.json").write_text(json.dumps(job))
        raise KeyboardInterrupt("ENGINEERING FIXTURE: the pod was lost")

    monkeypatch.setattr(runner, "run_one", dying)
    os.chdir(study.root)
    session = runner.Session(load_recipe(study.root / "configs" / "recipe.json"), fx.fixture_loaders())
    with pytest.raises(KeyboardInterrupt):
        runner.calibrate(prepared_dir="prepared-v2", out_root="dev-matrix-002", session=session, arms=[first["arm"]],
                         seeds=[first["seed"]])
    monkeypatch.undo()
    monkeypatch.chdir(study.base)
    assert read_json(out / e1 / "job.json")["resume_from"] == f"dev-matrix-002/{q}"   # relative, as calibrate wrote it
    before = {name: dur.tree_hashes(out / name) for name in (q, e1)}
    outcome = study.worker().run()
    report = outcome["jobs"][0]["report"]
    assert [(u["unit"], u["reused"], Path(u["run_dir"]).name) for u in report["units"]] == [
        (q[:-3], True, q), (e1[:-3], True, e1), (e3[:-3], False, e3[:-1] + "2")]
    assert {(a["unit"], a["attempt"], a["state"]) for a in report["adopted"]} == {
        (q[:-3], 1, "sealed"), (e1[:-3], 1, "sealed"), (e3[:-3], 1, "lost")}
    assert {name: dur.tree_hashes(out / name) for name in (q, e1)} == before          # the adopted units are untouched
    acknowledged = {Path(u.root).name for u in study.services().vault.acknowledged_units() if u.kind == "run"}
    assert {q, e1, e3[:-1] + "2"} <= acknowledged
    catalogue = read_jsonl(study.root / "durability-admin" / HOST / "attempts.jsonl")
    lost = [row for row in catalogue if row["event"] == "attempt-lost"]
    assert [(row["unit"], row["attempt"]) for row in lost] == [(e3[:-3], 1)] and "outside this runner" in lost[0]["cost"]
    claims = read_jsonl(out / "registry.jsonl")
    assert [row["run_dir"] for row in claims][0] == f"dev-matrix-002/{q}" and len(claims) == 2   # no claim was added twice


def test_the_finish_still_records_when_the_timer_does_not_answer(study):
    study.shutdown.fail = True
    outcome = study.worker().run()
    assert outcome["complete"] is True and outcome["stop"]["finishing"] is False and "RuntimeError" in outcome["stop"]["reason"]
    assert study.outcome()["complete"] is True
    quiet = study.worker(finish_after_seconds=None).run()
    assert quiet["stop"] is None


def test_a_host_pulled_to_the_laptop_is_ingested_restored_on_a_fresh_pod_and_continued(study, monkeypatch, capsys):
    """The retry path for a host of a run made without the safeguards: its tree, pulled to the
    operator's machine, goes into the vault with ``ingest`` (path maps, nothing rewritten); a fresh
    pod's worker restores it at the recorded paths and continues the chain."""
    from experiments.durability.__main__ import main as cli
    from experiments.safety_selection.common import PACKAGE_DIR

    first = study.jobs_for_host[0]
    q, e1, e3 = chain_names(first)
    os.chdir(study.root)                                 # the pod, 2 October way: calibrate, relative paths, q only
    session = runner.Session(load_recipe(study.root / "configs" / "recipe.json"), fx.fixture_loaders())
    runner.calibrate(prepared_dir="prepared-v2", out_root="dev-matrix-002", session=session, arms=[first["arm"]],
                     seeds=[first["seed"]], checkpoints=["q"])
    monkeypatch.chdir(study.base)
    pulled = study.base / "laptop" / "retrieved" / HOST
    shutil.copytree(study.root / "dev-matrix-002", pulled / "dev-matrix-002")
    shutil.copytree(study.root / "prepared-v2", pulled / "prepared-v2")
    sealed = dur.tree_hashes(pulled / "dev-matrix-002" / q)
    study.lose_the_volume()                              # the pod and its volume are gone; the laptop has the copy
    out, code = study.root / "dev-matrix-002", PACKAGE_DIR.parent
    assert cli(["ingest", "--destination", str(study.offsite / "destination"), "--namespace", HOST,
                "--scratch", str(study.base / "laptop" / "scratch"), "--journal", str(study.base / "laptop" / "journal.jsonl"),
                "--map", f"{out}={pulled / 'dev-matrix-002'}", "--map", f"{study.root / 'prepared-v2'}={pulled / 'prepared-v2'}",
                "--prepared", str(study.root / "prepared-v2"), "--code", str(code), "--run", str(out / q)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["registries"] == [f"{out}/registry.jsonl"] and len(report["acknowledged"]) == 3
    study.build_root()                                   # a fresh pod: bundles and bootstrap, then the worker
    outcome = study.worker().run()
    assert outcome["restore"]["units"] == 3 and outcome["restore"]["append_files"] >= 1
    units = outcome["jobs"][0]["report"]["units"]
    assert [(u["unit"], u["reused"], Path(u["run_dir"]).name) for u in units] == [(q[:-3], True, q), (e1[:-3], False, e1),
                                                                                (e3[:-3], False, e3)]
    assert dur.tree_hashes(out / q) == sealed            # the pulled unit, byte for byte, at its recorded path
    claims = read_jsonl(out / "registry.jsonl")
    assert claims[0]["run_dir"] == f"dev-matrix-002/{q}" and len(claims) == 2          # the pod's own claim came back too
    assert verify_run(out / e3, study.root / "prepared-v2")["complete"]
