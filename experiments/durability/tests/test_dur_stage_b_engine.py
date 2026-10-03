"""The gated backend around the REAL ``EngineBackend`` on the engine's ENGINEERING FIXTURES (tiny
random model on CPU; the Stage B engine test's development record and configuration are reused):
a whole confirmation-mode block runs through the gate, every operation attempt is acknowledged
after its sealed engine folder, its dependencies in other attempts, the pinned prepared data and
the engine source verify in a fresh tree with the stream checked, and the restored copy passes
Stage B's own ``verify_study``. Then the registry semantics with the real engine: a worker killed
inside a fresh start that had claimed its trajectory is restored, the claim is re-appended, the
gate refuses the retry until the attempt is declared lost, and the engine then registers the retry
as the same draw. Nothing here is a scientific result or evidence about a cloud."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")
pytest.importorskip("numpy")

STAGE_B_TESTS = Path(__file__).resolve().parents[2] / "safety_decision_policy" / "tests"
if str(STAGE_B_TESTS) not in sys.path:
    sys.path.insert(0, str(STAGE_B_TESTS))

import dur_fixtures as dur  # noqa: E402
import ss_fixtures as fx  # noqa: E402
from test_dp_engine import env  # noqa: E402,F401 - the Stage B engine fixture (module scoped)

from experiments.durability.backup import Vault  # noqa: E402
from experiments.durability.common import Journal, read_jsonl  # noqa: E402
from experiments.durability.destination import LocalDirectoryDestination  # noqa: E402
from experiments.durability.stage_b import (StudyBackup, declare_lost_attempt, open_attempts,  # noqa: E402
                                            reconcile_claims, run_block_gated, study_attempts)
from experiments.safety_decision_policy.backend import EngineBackend  # noqa: E402
from experiments.safety_decision_policy.common import RequestRefused, read_canonical  # noqa: E402
from experiments.safety_decision_policy.controller import Study, verify_study  # noqa: E402
from experiments.safety_selection import jobs, runner  # noqa: E402
from experiments.safety_selection.common import PACKAGE_DIR  # noqa: E402
from experiments.safety_selection.verify import PathMap  # noqa: E402

WORKER = "worker-1"


class Site:
    def __init__(self, base: Path, env) -> None:  # noqa: F811
        self.base, self.env = base.resolve(), env
        self.volume, self.offsite = self.base / "volume", self.base / "offsite"
        self.root = self.volume / "study"
        self.clock = dur.ManualClock()
        self.provider = dur.FakeProvider(self.clock)
        self.volume.mkdir(parents=True)

    def vault(self) -> Vault:
        return Vault(LocalDirectoryDestination(self.offsite / "destination"), "study-1",
                     journal=Journal(self.volume / "durability-admin" / "journal.jsonl", self.clock),
                     scratch=self.offsite / "scratch", clock=self.clock, reveal_paths=False)

    def backup(self) -> StudyBackup:
        return StudyBackup(self.vault(), self.root, prepared_dir=self.env.prepared, code_root=PACKAGE_DIR.parent)

    def admit(self):
        controller = dur.admission(self.offsite, self.provider, self.clock)
        return controller.admit(WORKER, 3600.0, dur.storage(self.volume, self.vault().destination), dur.RESERVE)

    def engine(self, cls=EngineBackend):
        """A worker process's backend: its own engine Session (one block per process)."""
        return cls(prepared_dir=self.env.prepared, recipe=self.env.recipe,
                   session=runner.Session(self.env.recipe, fx.fixture_loaders()),
                   registry=self.root / "registry.jsonl")

    def study(self, backend) -> Study:
        return Study(self.root, config=self.env.config, backend=backend, process_start=backend.clock(),
                     **self.env.kwargs)

    def run(self, inner=None):
        backup = self.backup()
        backup.settle()                          # the separate administrative step before a block
        gate = dur.gate_for(backup.vault, dur.admission(self.offsite, self.provider, self.clock), self.clock)
        return run_block_gated(self.study, 0, inner=inner or self.engine(), backup=backup, gate=gate, worker=WORKER)


def test_a_block_through_the_gate_acknowledges_every_engine_attempt_with_its_chain(tmp_path, env):  # noqa: F811
    site = Site(tmp_path, env)
    site.admit()
    result = site.run()
    assert result["status"] == "complete"
    backup = site.backup()
    assert backup.pending() == {"pins": False, "records": [], "attempts": []}
    acks = [read_canonical_json(p) for p in (site.offsite / "destination" / "study-1" / "acks").glob("*.json")]
    attempts = [a for a in acks if a["unit_kind"] == "attempt"]
    assert len(attempts) == len(study_attempts(site.root))
    engine = [a for a in attempts if a["verification"]["folders"]]     # attempts whose run/ is a sealed engine folder
    assert len(engine) >= len(list(site.root.glob("blocks/0/ops/*/attempt-*/run/COMPLETE.json")))
    assert max(a["verification"]["run_one_stream_checked"] for a in engine) >= 2   # a continuation and its source
    assert max(a["verification"]["folders"] for a in engine) >= 3      # an attribution run with its a0 states
    assert all(a["pins"]["manifest_sha256"] == env.sha for a in engine)
    assert {a["unit_kind"] for a in acks} == {"attempt", "record", "prepared", "code"}
    # the stored copy, restored elsewhere in the recorded layout, passes Stage B's own verification
    mirror = tmp_path / "mirror"
    site.vault().restore(mirror=mirror)
    relocated = EngineBackend(prepared_dir=env.prepared, recipe=env.recipe,
                              path_map=PathMap([(site.root, mirror / str(site.root).lstrip("/"))]))
    assert verify_study(mirror / str(site.root).lstrip("/"), relocated)["complete"]
    registry = site.root / "registry.jsonl"
    assert (mirror / str(registry).lstrip("/")).read_bytes() == registry.read_bytes()


def read_canonical_json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def test_a_killed_fresh_start_is_restored_declared_lost_and_retried_as_the_same_draw(tmp_path, env):  # noqa: F811
    site = Site(tmp_path, env)
    site.admit()
    screen = "screen-a0-2101"
    lost = site.root / "blocks" / "0" / "ops" / screen / "attempt-1"

    class Killed(EngineBackend):
        """The worker dies inside the a0 screen after the engine registered the trajectory."""

        def execute(self, spec, attempt_dir, sources):
            if spec["op_id"] != screen:
                return super().execute(spec, attempt_dir, sources)
            jobs.claim_trajectory(self.registry, jobs.trajectory_key(self.manifest_sha256, self.recipe, spec["split"],
                                                                     spec["arm"], spec["seed"], spec["role"]),
                                  str(Path(attempt_dir) / "run"), None)
            shutil.copytree(site.offsite, site.base / "offsite-at-kill")
            raise KeyboardInterrupt("ENGINEERING FIXTURE: the worker was terminated")

    with pytest.raises(KeyboardInterrupt):
        site.run(site.engine(Killed))
    shutil.rmtree(site.volume)
    shutil.rmtree(site.offsite)
    (site.base / "offsite-at-kill").rename(site.offsite)
    site.volume.mkdir()
    vault = site.vault()
    vault.restore()
    assert open_attempts(site.root) == [lost]
    claims_before = read_jsonl(site.root / "registry.jsonl")
    assert str(lost / "run") not in [row["run_dir"] for row in claims_before]      # the snapshot predates the claim
    assert reconcile_claims(site.root, registry=site.root / "registry.jsonl", recipe=env.recipe,
                            manifest_sha256=env.sha, vault=vault) == 1
    kept = (site.root / "registry.jsonl").read_bytes()
    with pytest.raises(RequestRefused, match="declare it lost first"):
        site.run()
    assert (site.root / "registry.jsonl").read_bytes() == kept and not (lost.parent / "attempt-2" / "run").exists()
    declare_lost_attempt(site.backup(), lost, operator="test operator", reason="ENGINEERING FIXTURE: pod lost")
    result = site.run()
    assert result["status"] == "complete"
    receipts = [read_canonical(p / "receipt.json")["status"] for p in sorted(lost.parent.glob("attempt-*"))]
    assert receipts == ["interrupted", "refused", "complete"]
    registry = (site.root / "registry.jsonl").read_bytes()
    assert registry.startswith(kept)                                               # claims appended, none cleared
    retry = [row for row in read_jsonl(site.root / "registry.jsonl") if row["run_dir"] == str(lost.parent / "attempt-3" / "run")]
    assert retry[0]["retry_after_failures"] == [str(lost / "run")]                 # the same draw, the lost start kept
    assert verify_study(site.root, EngineBackend(prepared_dir=env.prepared, recipe=env.recipe))["complete"]
    assert site.backup().pending() == {"pins": False, "records": [], "attempts": []}
