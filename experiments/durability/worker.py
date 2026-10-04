"""The gated pod worker: one host's jobs of a frozen plan, unit by unit, under the safeguards.

``python -m experiments.durability worker --config worker.json`` runs on the pod, with the study
root as its working directory and the engine's pinned environment. It is the 2 October runner
(``run_dev_matrix.py``: the plan's jobs for one host, each the engine's ``calibrate`` for one arm
and one seed) with the calibration loop taken out of the engine and run through ``UnitRunner``, so
that between two units there is an admission lease, an off-pod acknowledgement and a restore check.
The engine, the recipe, the prepared data and the plan are not changed and not reinterpreted.

**Start** (the parent process; it loads no model):

1. the identities the 2 October runner checked: the engine's code identity, the recipe's hash and
   the prepared-data manifest hash against the plan; and, as that runner required of every new
   host, the bootstrap's record that the two-step fixture matched (``fixture_record``);
2. restore: every unit this host's namespace has acknowledged in the destination, and the latest
   snapshots of its registry and catalogue, are placed at their recorded paths. Identical files
   are kept; a different file refuses.

**Run.** Each job in plan order, each in its own process with a fresh engine session, exactly as
``calibrate`` was invoked once per job on 2 October (a session shared by two jobs would change the
second job's recorded asset loads). Inside the job process:

- ``UnitRunner.adopt`` catalogues attempts found in the tree that this runner did not start (a
  tree pulled from a pod that ran plain ``calibrate``), then ``reconcile`` classifies what was lost;
- the tombstones the operator named in the configuration are written, and only those; a lost
  fresh start without one refuses the job, as the engine itself would;
- the units ``<seed>-<arm>-<checkpoint>`` in the recipe's checkpoint order, each a continuation of
  the one before, with the job fields ``calibrate`` uses. Before a unit that has to run: an
  admission lease long enough for it (``unit_seconds`` times ``lease_slack``, plus
  ``acknowledge_seconds``), which arms the pod's stop timer; a keeper thread renews the lease if the
  unit outlasts it. After the unit seals: its acknowledgement in the destination, before the next
  unit. A sealed unit of the same science is reused and acknowledged if it was not yet.

**Finish.** A completion record in the administrative folder (snapshotted off-pod), the lease
released, and the stop timer asked to stop the pod in ``finish_after_seconds``. Nothing is deleted.
On a refusal or failure the record says so and, unless ``stop_on_failure`` is false, the timer is
asked to stop the pod as well: an idle billed pod helps no one.

**Scientific identity.** The job dictionaries are the ones ``calibrate`` builds, and the engine
function called is the same ``run_one``. What differs from a ``calibrate`` run is named in the
README ("Scientific identity of the worker") and checked by the tests: timings and timestamps, and
the spelling of paths (this runner passes absolute paths; the plan's command passed relative ones),
with the hashes of the files that contain them.

The configuration holds no secret: keys and tokens are named by environment variable.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .admission import AdmissionController, AdmissionPolicy, RateCard, StorageDeclaration
from .backup import Vault
from .common import (Clock, DurabilityError, Journal, append_jsonl, iso, read_json, read_jsonl, utc_clock,
                     write_exclusive)
from .engine_units import UnitRunner, UnitSpec
from .gate import DispatchGate

__all__ = ["WorkerConfig", "WorkerRefused", "Services", "Leases", "Worker", "load_config", "build_services",
           "verify_identities", "units_of", "run_job", "measurements", "JOB_ENVIRONMENT"]

# the environment the 2 October runner gave every job (PYTHONPATH is the study root)
JOB_ENVIRONMENT = {"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
                   "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4"}
_CONFIG_KEYS = {"host", "worker", "root", "plan", "out_root", "admin_dir", "scratch", "namespace", "destination",
                "provider", "policy", "planned_rates", "storage", "retention_reserve", "unit_seconds", "lease_slack",
                "acknowledge_seconds", "renew_margin_seconds", "fixture_record", "tombstones", "finish_after_seconds",
                "stop_on_failure", "job_environment", "pod_id_env"}


class WorkerRefused(DurabilityError):
    """The worker did not start or continue: an identity differs, a record is missing, or a
    safeguard refused. Nothing was trained after the refusal."""


@dataclass(frozen=True)
class WorkerConfig:
    """See ``load_config``. Paths are absolute; ``out_root`` and ``prepared`` are the recorded
    layout a restore reproduces."""

    host: str
    worker: str
    root: Path
    plan: Path
    out_root: Path
    admin_dir: Path
    scratch: Path
    namespace: str
    unit_seconds: Mapping[str, float]
    lease_slack: float = 1.5
    acknowledge_seconds: float = 600.0
    renew_margin_seconds: float = 300.0
    fixture_record: Path | None = None
    tombstones: tuple = ()
    finish_after_seconds: float | None = 120.0
    stop_on_failure: bool = True
    job_environment: Mapping[str, str] = field(default_factory=lambda: dict(JOB_ENVIRONMENT))
    raw: Mapping = field(default_factory=dict)


def load_config(source: str | Path | Mapping) -> WorkerConfig:
    """The worker's configuration from a JSON file or a mapping. Required: ``host``, ``root`` (the
    study root, absolute), ``plan`` and ``out_root`` (relative to the root, as the plan's command
    names them), ``unit_seconds`` (planned seconds per checkpoint). An unknown key refuses."""
    data = dict(json.loads(Path(source).read_text(encoding="utf-8")) if not isinstance(source, Mapping) else source)
    unknown = sorted(set(data) - _CONFIG_KEYS)
    missing = sorted({"host", "root", "plan", "out_root", "unit_seconds"} - set(data))
    if unknown or missing:
        raise WorkerRefused(f"the worker configuration has unknown keys {unknown} or lacks {missing}")
    root = Path(data["root"])
    if not root.is_absolute():
        raise WorkerRefused("the study root must be an absolute path")
    host = data["host"]
    seconds = data["unit_seconds"]
    if not (isinstance(seconds, Mapping) and seconds and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 for v in seconds.values())):
        raise WorkerRefused("unit_seconds must give positive planned seconds per checkpoint")
    tombstones = tuple(data.get("tombstones") or ())
    for item in tombstones:
        if not (isinstance(item, Mapping) and set(item) == {"unit", "attempt", "operator", "reason"}
                and isinstance(item["attempt"], int) and all(str(item[k]).strip() for k in ("unit", "operator", "reason"))):
            raise WorkerRefused("a tombstone names its unit, attempt, operator and reason, and nothing else")
    finish = data.get("finish_after_seconds", 120.0)
    fixture = data.get("fixture_record", "BOOTSTRAP-VERIFIED.json")
    return WorkerConfig(
        host=host, worker=data.get("worker", host), root=root, plan=root / data["plan"], out_root=root / data["out_root"],
        admin_dir=root / data.get("admin_dir", f"durability-admin/{host}"),
        scratch=Path(data.get("scratch", f"/tmp/durability-scratch/{host}")), namespace=data.get("namespace", host),
        unit_seconds=dict(seconds), lease_slack=float(data.get("lease_slack", 1.5)),
        acknowledge_seconds=float(data.get("acknowledge_seconds", 600.0)),
        renew_margin_seconds=float(data.get("renew_margin_seconds", 300.0)),
        fixture_record=None if fixture is None else root / fixture, tombstones=tombstones,
        finish_after_seconds=None if finish is None else float(finish),
        stop_on_failure=bool(data.get("stop_on_failure", True)),
        job_environment={**JOB_ENVIRONMENT, **dict(data.get("job_environment") or {})}, raw=data)


@dataclass
class Services:
    """What the worker works with. ``build_services`` makes the real ones from the configuration;
    tests pass fakes. ``shutdown`` is the stop timer's worker side (``finish``), or None."""

    vault: Vault
    controller: AdmissionController
    storage: StorageDeclaration
    retention_reserve: float
    shutdown: object | None = None
    pod: str | None = None
    clock: Clock = utc_clock


def build_services(config: WorkerConfig, env: Mapping[str, str] | None = None) -> Services:
    """The real destination, provider and admission from the configuration. The pod's id comes from
    the environment RunPod sets (``RUNPOD_POD_ID``); keys and tokens stay in the environment."""
    from .wiring import destination_from, provider_from

    env, raw = os.environ if env is None else env, config.raw
    for name in ("destination", "provider", "policy", "planned_rates", "storage", "retention_reserve"):
        if name not in raw:
            raise WorkerRefused(f"the worker configuration lacks {name}")
    pod = env.get(raw.get("pod_id_env", "RUNPOD_POD_ID"), "").strip()
    if not pod:
        raise WorkerRefused("the pod's id is not in the environment")
    spec = dict(raw["destination"])
    destination = destination_from(spec.pop("spec"), **spec)
    journal = Journal(config.admin_dir / "journal.jsonl")
    vault = Vault(destination, config.namespace, journal=journal, scratch=config.scratch)
    provider = provider_from({**raw["provider"], "worker_pods": {config.worker: pod}, "local_pod_id": pod})
    try:
        policy = AdmissionPolicy(**raw["policy"])
        planned = RateCard(**raw["planned_rates"], as_of_utc=iso(utc_clock()),
                           source="worker configuration: the rates the plan was costed with")
        storage = StorageDeclaration(source_path=str(config.root), destination=destination, **raw["storage"])
    except TypeError as exc:
        raise WorkerRefused(f"the worker configuration is malformed ({exc})") from None
    controller = AdmissionController(config.admin_dir / "reservations.jsonl", provider, policy, planned, journal=journal)
    return Services(vault=vault, controller=controller, storage=storage,
                    retention_reserve=float(raw["retention_reserve"]), shutdown=getattr(provider, "shutdown", None), pod=pod)


def verify_identities(config: WorkerConfig) -> dict:
    """What the 2 October runner asserted before any job, as a refusal instead of an assertion: the
    engine's code identity, the recipe's hash and the prepared-data manifest hash equal the plan's;
    and the bootstrap recorded that the two-step fixture matched on this host."""
    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.config import config_sha256, load_recipe
    from experiments.safety_selection.prepare import read_manifest

    plan = read_json(config.plan)
    if config.host not in plan.get("assignments", {}):
        raise WorkerRefused(f"the plan assigns nothing to host {config.host!r}")
    prepared = config.root / plan["prepared_path"]
    recipe = load_recipe(config.root / plan["recipe_path"])
    units_of({"seed": 0, "arm": "a0"}, recipe, config.unit_seconds)      # a planned time for every checkpoint, or refuse
    found = {"engine_sha256": code_identity()["sha256"],
             "recipe_sha256": config_sha256(recipe),
             "manifest_sha256": read_manifest(prepared)[1]}       # recomputed by the engine, not only read
    wrong = sorted(key for key, value in found.items() if value != plan[key])
    if (prepared / "manifest.sha256").read_text().strip() != plan["manifest_sha256"]:   # the 2 October check itself
        wrong.append("manifest.sha256 file")
    if wrong:
        raise WorkerRefused(f"this host's {wrong} differ from the frozen plan: nothing is run")
    if config.fixture_record is not None:
        try:
            exact = read_json(config.fixture_record).get("fixture_exact") is True
        except (OSError, ValueError):
            exact = False
        if not exact:
            raise WorkerRefused("the bootstrap's record of the exact two-step fixture is missing on this host")
    return {**found, "fixture_record": None if config.fixture_record is None else str(config.fixture_record)}


def units_of(job: Mapping, recipe: dict, unit_seconds: Mapping[str, float]) -> list[UnitSpec]:
    """One job's chain as the engine's ``calibrate`` lays it out: every checkpoint of the recipe
    after the seeded adapter, in order, each continuing the one before."""
    from experiments.safety_selection.config import INIT, checkpoint_names

    names = [name for name in checkpoint_names(recipe) if name != INIT]
    missing = sorted(set(names) - set(unit_seconds))
    if missing:
        raise WorkerRefused(f"unit_seconds has no planned time for checkpoints {missing}")
    specs: list[UnitSpec] = []
    for name in names:
        specs.append(UnitSpec(name=f"{job['seed']}-{job['arm']}-{name}", split="dev", arm=job["arm"], seed=job["seed"],
                              role="development", target_checkpoint=name, evaluate_bank="dev",
                              resume_from=specs[-1].name if specs else None,
                              planned_seconds=float(unit_seconds[name])))
    return specs


def _check_job(job: Mapping, prepared_dir: Path) -> None:
    """The access checks ``calibrate`` makes before anything runs: a development seed, and a0 or a
    development group."""
    from experiments.safety_selection.config import seed_namespace
    from experiments.safety_selection.jobs import AccessError
    from experiments.safety_selection.prepare import load_prepared, read_manifest

    manifest, manifest_sha = read_manifest(prepared_dir)
    if seed_namespace(manifest["data_config"], job["seed"]) != "development":
        raise AccessError(f"seed {job['seed']} is not a development seed")
    if job["arm"] != "a0" and job["arm"] not in load_prepared(prepared_dir, manifest_sha).groups["dev"]:
        raise AccessError(f"{job['arm']} is not a development group; calibration never touches held-out groups")


class Leases:
    """The worker's lease for the unit in hand: admitted before the unit, renewed while it runs.
    ``need(spec)`` is the lease a unit asks for; ``ensure`` admits when the current lease does not
    cover it; ``extend_if_needed`` renews a lease that is about to end (the keeper thread calls it
    while a unit runs, and tests call it directly)."""

    def __init__(self, services: Services, config: WorkerConfig, log: Callable[..., None]) -> None:
        self.services, self.config, self.log = services, config, log
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._current: UnitSpec | None = None
        self.admissions: list[dict] = []

    def need(self, spec: UnitSpec) -> float:
        return spec.planned_seconds * self.config.lease_slack + self.config.acknowledge_seconds

    def _admit(self, seconds: float, why: str, unit: str) -> None:
        started = time.monotonic()
        lease = self.services.controller.admit(self.config.worker, seconds, self.services.storage,
                                               self.services.retention_reserve)
        record = {"unit": unit, "why": why, "lease": lease.lease, "seconds": seconds, "expires_utc": lease.expires_utc,
                  "reserved_until_utc": lease.reserved_until_utc, "admission_seconds": time.monotonic() - started}
        self.admissions.append(record)
        self.log("lease", **record)

    def ensure(self, spec: UnitSpec) -> None:
        """Admit before a unit unless the current lease already covers it. A refusal propagates:
        the unit does not start."""
        lease = self.services.controller.current_lease(self.config.worker)
        if lease is None or not lease.covers(self.services.clock(), self.need(spec)):
            self._admit(self.need(spec), "before the unit", spec.name)

    def extend_if_needed(self) -> bool:
        """Renew when less than ``renew_margin_seconds`` of the lease is left. True: renewed. A
        refused renewal is logged and the unit runs on to the stop time it already has."""
        spec = self._current
        lease = self.services.controller.current_lease(self.config.worker)
        if spec is None or lease is None or lease.covers(self.services.clock(), self.config.renew_margin_seconds):
            return False
        try:
            self._admit(max(spec.planned_seconds * (self.config.lease_slack - 1.0), 2 * self.config.renew_margin_seconds)
                        + self.config.acknowledge_seconds, "the unit outlasted its lease", spec.name)
            return True
        except Exception as exc:  # noqa: BLE001 - the unit keeps the stop time it has
            self.log("lease-renewal-refused", unit=spec.name, reason=f"{type(exc).__name__}: {exc}"[:300])
            return False

    def before_unit(self, spec: UnitSpec) -> None:
        self.ensure(spec)
        self._current = spec
        self._stop.clear()
        self._thread = threading.Thread(target=self._keep, daemon=True)
        self._thread.start()

    def after_unit(self, spec: UnitSpec) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=600)
        self._current, self._thread = None, None

    def _keep(self) -> None:
        while not self._stop.wait(min(30.0, max(1.0, self.config.renew_margin_seconds / 4))):
            try:
                self.extend_if_needed()
            except Exception:  # noqa: BLE001 - the keeper never ends the unit
                pass


def run_job(config: WorkerConfig, index: int, *, services: Services, session) -> dict:
    """One job of the host's plan in this process (module doc). ``session`` is the engine session
    for the plan's recipe. Returns the job's report; refusals and engine failures propagate."""
    plan = read_json(config.plan)
    job = plan["assignments"][config.host][index]
    prepared_dir = config.root / plan["prepared_path"]
    if session.recipe_sha256 != plan["recipe_sha256"]:
        raise WorkerRefused("the engine session was built for another recipe than the plan's")
    _check_job(job, prepared_dir)
    specs = units_of(job, session.recipe, config.unit_seconds)
    log = _logger(config, services.clock)
    leases = Leases(services, config, log)
    gate = DispatchGate(services.vault, services.controller.current_lease, journal=services.vault.journal,
                        clock=services.clock)
    runner = UnitRunner(session=session, prepared_dir=prepared_dir, out_root=config.out_root, admin_dir=config.admin_dir,
                        vault=services.vault, gate=gate, worker=config.worker, clock=services.clock,
                        before_unit=leases.before_unit, after_unit=leases.after_unit)   # the code pin: the engine as imported
    config.out_root.mkdir(parents=True, exist_ok=True)
    config.admin_dir.mkdir(parents=True, exist_ok=True)
    runner.prepare()                 # the pinned inputs first: adopted units are acknowledged against them
    adopted = runner.adopt(specs)
    lost = runner.reconcile()
    declared = []
    for item in config.tombstones:
        match = [a for a in runner.attempts() if (a["unit"], a["attempt"]) == (item["unit"], item["attempt"])]
        if match and runner.unresolved(match[0]) and not match[0]["tombstoned"]:
            runner.declare_lost(item["unit"], item["attempt"], operator=item["operator"], reason=item["reason"])
            declared.append({"unit": item["unit"], "attempt": item["attempt"]})
    log("job-started", job=index, arm=job["arm"], seed=job["seed"], units=[s.name for s in specs],
        adopted=len(adopted), lost_now=len(lost), tombstones=declared)
    units = runner.run(specs)
    report = {"job": index, "arm": job["arm"], "seed": job["seed"], "units": units, "admissions": leases.admissions,
              "adopted": adopted, "tombstones": declared}
    log("job-finished", job=index, units=[{k: u[k] for k in ("unit", "reused", "launch_seconds", "acknowledge_seconds")}
                                          for u in units])
    return report


def _logger(config: WorkerConfig, clock: Clock) -> Callable[..., None]:
    def log(event: str, **fields: object) -> None:
        append_jsonl(config.admin_dir / "worker.jsonl", {"event": event, "utc": iso(clock()), "host": config.host, **fields})
    return log


def _real_session(config: WorkerConfig):
    from experiments.safety_selection import runner
    from experiments.safety_selection.config import load_recipe
    from experiments.safety_selection.loaders import real_loaders

    plan = read_json(config.plan)
    return runner.Session(load_recipe(config.root / plan["recipe_path"]), real_loaders())


def job_main(config: WorkerConfig, index: int, *, services: Services | None = None, session_factory=None) -> dict:
    """The job process: the study root as working directory, then ``run_job``. Writes the job's
    report next to the catalogue."""
    os.chdir(config.root)
    services = services or build_services(config)
    report = run_job(config, index, services=services, session=(session_factory or _real_session)(config))
    path = config.admin_dir / f"job-report-{index}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


class Worker:
    """The parent process (module doc). ``run_job_process(index)`` starts one job and returns its
    exit status; by default it is a new ``worker-job`` process of this interpreter."""

    def __init__(self, config: WorkerConfig, services: Services | None = None,
                 run_job_process: Callable[[int], int] | None = None, config_path: str | Path | None = None) -> None:
        self.config, self._services, self.config_path = config, services, config_path
        self.run_job_process = run_job_process or self._spawn
        self.log = _logger(config, (services.clock if services else utc_clock))

    @property
    def services(self) -> Services:
        if self._services is None:
            self._services = build_services(self.config)
        return self._services

    def _spawn(self, index: int) -> int:
        if self.config_path is None:
            raise WorkerRefused("a job process needs the configuration file's path")
        env = {**os.environ, **self.config.job_environment, "PYTHONPATH": str(self.config.root)}
        return subprocess.run([sys.executable, "-m", "experiments.durability", "worker-job", "--config",
                               str(self.config_path), "--job-index", str(index)], cwd=self.config.root, env=env,
                              check=False).returncode

    def _record(self, outcome: dict) -> Path:
        """The completion (or refusal) record: a new numbered file, never a replacement, and the
        worker's own log off-pod with it when the destination answers."""
        number = len(list(self.config.admin_dir.glob("worker-outcome-*.json"))) + 1
        path = self.config.admin_dir / f"worker-outcome-{number:03d}.json"
        write_exclusive(path, (json.dumps(outcome, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        try:
            for name in ("worker.jsonl",):
                self.services.vault.snapshot_append(str(self.config.admin_dir / name))
        except Exception:  # noqa: BLE001 - the record stays on the volume; the acknowledgements are what counts
            pass
        return path

    def _stop(self, why: str) -> dict | None:
        services, after = self.services, self.config.finish_after_seconds
        if after is None or services.shutdown is None or services.pod is None:
            return None
        try:
            lease = services.controller.current_lease(self.config.worker)
            if lease is not None:
                services.controller.release(lease.lease, why)
            return services.shutdown.finish(self.config.worker, services.pod, after, why)
        except Exception as exc:  # noqa: BLE001 - the deadline the timer already has still stands
            return {"finishing": False, "reason": f"{type(exc).__name__}: {exc}"[:300]}

    def run(self) -> dict:
        config = self.config
        config.admin_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(config.root)
        started = self.services.clock()
        outcome: dict = {"kind": "durability worker outcome v1", "host": config.host, "started_utc": iso(started),
                         "complete": False, "jobs": []}
        try:
            outcome["identities"] = verify_identities(config)
            restore_started = time.monotonic()
            outcome["restore"] = {**self.services.vault.restore(), "seconds": time.monotonic() - restore_started}
            self.log("worker-started", identities=outcome["identities"], restore=outcome["restore"])
            jobs = read_json(config.plan)["assignments"][config.host]
            for index in range(len(jobs)):
                status = self.run_job_process(index)
                report_path = config.admin_dir / f"job-report-{index}.json"
                report = read_json(report_path) if status == 0 and report_path.is_file() else None
                outcome["jobs"].append({"job": index, "exit": status, "report": report})
                if status != 0 or report is None:
                    raise WorkerRefused(f"job {index} ended with status {status}: the later jobs are not started")
            outcome["complete"] = True
        except BaseException as exc:
            outcome["refused"] = f"{type(exc).__name__}: {exc}"[:500]
            outcome["finished_utc"] = iso(self.services.clock())
            if config.stop_on_failure:
                outcome["stop"] = self._stop("the worker refused or failed")
            self.log("worker-refused", reason=outcome["refused"])
            outcome["record"] = str(self._record(outcome))
            raise
        outcome["finished_utc"] = iso(self.services.clock())
        outcome["stop"] = self._stop("the host's jobs are complete and acknowledged")
        self.log("worker-finished", jobs=len(outcome["jobs"]), stop=outcome["stop"])
        outcome["record"] = str(self._record(outcome))
        return outcome


def measurements(admin_dir: str | Path, timer_dir: str | Path | None = None) -> dict:
    """What one host's records say about time and cost, for the one-pod validation: per unit the
    training-and-evaluation time (the engine's ``run_one``), the off-pod copy and the restore check,
    the admission time; the worker's hourly rate as admission recorded it; the stop timer's lateness
    from its own attempt records. Reads the administrative folder (and the timer's folder) only."""
    admin = Path(admin_dir)
    journal = read_jsonl(admin / "journal.jsonl") if (admin / "journal.jsonl").is_file() else []
    acks = {row.get("path"): row for row in journal if row.get("event") == "unit-acknowledged" and row.get("unit_kind") == "run"}
    grants = [row for row in journal if row.get("event") == "admission-granted"]
    rate = grants[-1]["rate_per_hour"] if grants else None
    units, admissions = [], []
    for path in sorted(admin.glob("job-report-*.json")):
        report = read_json(path)
        admissions += report.get("admissions", [])
        for unit in report["units"]:
            if unit["reused"]:
                continue
            ack = acks.get(unit["run_dir"], {})
            units.append({"unit": unit["unit"], "checkpoint": unit["unit"].rsplit("-", 1)[-1],
                          "run_seconds": unit["launch_seconds"], "acknowledge_seconds": unit["acknowledge_seconds"],
                          "copy_seconds": ack.get("copy_seconds"), "restore_check_seconds": ack.get("verify_seconds"),
                          "bytes": ack.get("bytes"), "files": ack.get("files")})
    admission_seconds = sum(a["admission_seconds"] for a in admissions)
    run = sum(u["run_seconds"] for u in units)
    safeguard = sum(u["acknowledge_seconds"] for u in units) + admission_seconds
    by_checkpoint: dict[str, list] = {}
    for unit in units:
        by_checkpoint.setdefault(unit["checkpoint"], []).append(unit)
    summary = {name: {"units": len(rows), "max_run_seconds": max(r["run_seconds"] for r in rows),
                      "max_acknowledge_seconds": max(r["acknowledge_seconds"] for r in rows),
                      "cost_per_unit": None if rate is None else max(
                          (r["run_seconds"] + r["acknowledge_seconds"]) * rate / 3600.0 for r in rows)}
               for name, rows in sorted(by_checkpoint.items())}
    timer = None
    attempts = Path(timer_dir) / "stop-attempts.jsonl" if timer_dir is not None else None
    if attempts is not None and attempts.is_file():
        rows = read_jsonl(attempts)
        accepted = [row for row in rows if row.get("accepted")]
        timer = {"attempts": len(rows), "first_accepted_method": accepted[0]["method"] if accepted else None,
                 "seconds_after_stop_time": accepted[0]["seconds_after_stop_time"] if accepted else None}
    restores = [row for row in journal if row.get("event") == "restore"]
    return {"units": units, "by_checkpoint": summary, "admissions": len(admissions), "admission_seconds": admission_seconds,
            "rate_per_hour": rate, "run_seconds": run, "safeguard_seconds": safeguard,
            "safeguard_fraction": None if not units else safeguard / (run + safeguard),
            "restores": [{"seconds": row.get("seconds"), "bytes": row.get("bytes"), "units": row.get("units")} for row in restores],
            "timer": timer}
