"""The execution boundary between the controller and the engine.

A backend executes one canonical operation spec per call and reads verified results back:

- ``clock()`` / ``sync()``: the external monotonic timer and the device barrier the controller
  calls before reading it (the engine Session's synchronization hook);
- ``execute(spec, attempt_dir, sources)``: run one physical operation in a new attempt folder;
  returns ``{"status": "complete"|"failed", "artifact", "artifact_sha256", "error",
  "engine_setup_seconds"}``. Only an explicit validation refusal before any work raises
  ``RequestRefused`` (the lock check, a read-only backend, ``make_job``'s job validation): nothing
  ran and nothing is charged. Every other failure once execution started (an engine error,
  including a trajectory-registry refusal after a killed process, a failed export or write) is a
  preserved technical failure: charged, counted, and retried only as the same scientific draw;
- ``verify(receipt, spec)``: the artifact still verifies (own files, dependency chain and
  stream, identity pins, coordinates, and the hash pinned in the receipt);
- ``evaluation(receipt, spec)`` and ``attribution_scores(receipt, spec, a0_states)``: verified
  reads (``outcomes``);
- ``static_inputs(view_receipt, relevance_receipt, split)``: the whitelisted selector view and
  the relevance features, read by the predictor-side strict readers with pinned hashes.

``EngineBackend`` calls the verified engine API only (``planning.make_job`` with the actual
manifest, recipe and pinned code hashes; ``runner.run_one/attributes/score_groups`` in one
``Session``; ``export_selector_view``; ``verify_run``; a read-only ``PathMap`` for relocated
trees, never editing recorded paths). Final operations evaluate the role's final bank and are
refused unless they run under a valid choice lock (``check_lock``). The engine registry is
shared by the whole study and relies on one serialized scheduler.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Mapping

from experiments.safety_selection.common import recover_jsonl
from experiments.safety_selection.config import config_sha256 as engine_config_sha256
from experiments.safety_selection.jobs import JobError
from experiments.safety_selection.planning import make_job
from experiments.safety_selection.prepare import read_manifest
from experiments.safety_selection.selector_view import export_selector_view, read_selector_view
from experiments.safety_selection.verify import PathMap, verify_run

from .common import (LockRefused, RequestRefused, VerificationError, engine_code_identity, read_canonical,
                     read_json, sha256_file, write_once, write_once_json)
from .costs import SETUP_STAGES
from .outcomes import Evaluation, read_attribution, read_evaluation
from .tfidf import build_relevance, read_relevance

__all__ = ["RUN_KINDS", "LOCK_KIND", "lock_authorization", "check_lock", "engine_stage_seconds_of",
           "engine_setup_seconds_of", "EngineBackend"]

RUN_KINDS = ("screen", "full_from_short", "full_from_init", "extend", "final")
FINAL_KIND = "final"
LOCK_KIND = "safety-decision-policy choice lock"
_METHODS = ("S-", "S+")


def lock_authorization(lock: Mapping) -> dict:
    """What a choice lock authorizes: its block, configuration hash, final seed, both choices and
    the final arms (a0, both choices and the executed sensitivity's choice). Malformed refuses."""
    if not isinstance(lock, Mapping) or lock.get("kind") != LOCK_KIND:
        raise VerificationError("not a choice lock")
    methods = lock.get("methods")
    if not (isinstance(methods, Mapping) and set(methods) == set(_METHODS)):
        raise VerificationError("a choice lock needs exactly the choices of S- and S+")
    choices = {m: methods[m]["choice"]["choice"] for m in _METHODS}
    if not all(isinstance(c, str) and c for c in choices.values()):
        raise VerificationError("a choice lock needs both choices")
    arms = {"a0", *choices.values()}
    sensitivity = lock.get("sensitivity")
    if sensitivity and sensitivity.get("purchase"):
        arms.add(sensitivity["choice"]["choice"])
    return {"block": lock["block"], "config_sha256": lock["pins"]["config_sha256"],
            "final_seed": lock["seeds"]["final"], "choices": choices, "arms": sorted(arms)}


def check_lock(spec: dict, sources: Mapping[str, str]) -> dict | None:
    """Final-bank access (a final operation, or any spec naming the hidden bank) only under the
    choice lock of the same block and configuration whose hash the spec pins and which authorizes
    the spec's arm and final seed; returns its authorization. Refused before any work."""
    if spec["kind"] != FINAL_KIND and spec.get("bank") != "hidden":
        return None
    lock, expected = sources.get("lock"), spec.get("lock_sha256")
    if not lock or not expected:
        raise LockRefused(f"{spec['op_id']}: final-bank access before the choice lock is refused")
    if not Path(lock).is_file() or sha256_file(lock) != expected:
        raise LockRefused(f"{spec['op_id']}: the choice lock is missing or differs from its pinned hash")
    try:
        authorization = lock_authorization(read_canonical(lock, expected))
    except (VerificationError, KeyError, TypeError, AttributeError) as exc:
        raise LockRefused(f"{spec['op_id']}: malformed choice lock: {exc}") from None
    wrong = []
    if spec["kind"] != FINAL_KIND:
        wrong.append("only a final operation may access the final bank")
    if authorization["block"] != spec.get("block"):
        wrong.append(f"lock of block {authorization['block']}, operation of block {spec.get('block')}")
    if authorization["config_sha256"] != spec.get("config_sha256"):
        wrong.append("lock and operation pin different configurations")
    if authorization["final_seed"] != spec.get("seed"):
        wrong.append(f"lock final seed {authorization['final_seed']}, operation seed {spec.get('seed')}")
    if spec.get("arm") not in authorization["arms"]:
        wrong.append(f"arm {spec.get('arm')} is not authorized by the lock {authorization['arms']}")
    if wrong:
        raise LockRefused(f"{spec['op_id']}: {'; '.join(wrong)}")
    return authorization


def engine_stage_seconds_of(run_dir: Path) -> dict[str, float]:
    """Seconds of every stage recorded in a run folder's ledger, summed by stage name
    (informational: the external receipt is the authoritative operation time)."""
    path = Path(run_dir) / "ledger.jsonl"
    if not path.exists():
        return {}
    rows, _ = recover_jsonl(path)
    out: dict[str, float] = {}
    for row in rows:
        if isinstance(row.get("stage"), str) and isinstance(row.get("seconds"), (int, float)):
            out[row["stage"]] = out.get(row["stage"], 0.0) + float(row["seconds"])
    return out


def engine_setup_seconds_of(run_dir: Path) -> dict[str, float]:
    """The engine's setup stages (asset loading, corpus tokenization, memory preflight)."""
    return {k: v for k, v in engine_stage_seconds_of(run_dir).items() if k in SETUP_STAGES}


class EngineBackend:
    """The verified engine (see module doc). ``session`` may be None for read-only use."""

    def __init__(self, *, prepared_dir: str | Path, recipe: dict, session=None,
                 registry: str | Path | None = None, path_map: PathMap | None = None) -> None:
        self.prepared = Path(prepared_dir)
        self.recipe = recipe
        self.session = session
        self.registry = None if registry is None else Path(registry)
        self.path_map = path_map or PathMap()
        _, self.manifest_sha256 = read_manifest(self.prepared)
        self.recipe_sha256 = engine_config_sha256(recipe)
        self.code_sha256 = engine_code_identity()["sha256"]

    @property
    def pins(self) -> dict:
        return {"manifest_sha256": self.manifest_sha256, "recipe_sha256": self.recipe_sha256,
                "code_sha256": self.code_sha256}

    def clock(self) -> float:
        return time.monotonic()

    def sync(self) -> None:
        if self.session is not None:
            self.session.sync()

    def _complete(self, run: Path) -> dict:
        return {"status": "complete", "artifact": str(run), "artifact_sha256": sha256_file(run / "COMPLETE.json"),
                "error": None, "engine_setup_seconds": engine_setup_seconds_of(run),
                "engine_stage_seconds": engine_stage_seconds_of(run)}

    @staticmethod
    def _failed(run: Path, exc: Exception) -> dict:
        return {"status": "failed", "artifact": str(run) if run.exists() else None, "artifact_sha256": None,
                "error": f"{type(exc).__name__}: {exc}", "engine_setup_seconds": engine_setup_seconds_of(run),
                "engine_stage_seconds": engine_stage_seconds_of(run)}

    def _job(self, kind: str, spec: dict, attempt_dir: Path, **fields: object) -> dict:
        """The validated job file; the engine's job validation refuses before any work."""
        try:
            return make_job(kind, prepared_dir=self.prepared, recipe=self.recipe, pin_code=True,
                            out=attempt_dir / "job.json", wall_limit_seconds=None, **fields)
        except JobError as exc:
            raise RequestRefused(f"{spec['op_id']}: the engine refused the job before any work: {exc}") from exc

    def execute(self, spec: dict, attempt_dir: Path, sources: Mapping[str, object]) -> dict:
        if self.session is None or self.registry is None:
            raise RequestRefused("a read-only engine backend cannot execute operations")
        check_lock(spec, sources)
        from experiments.safety_selection import runner

        attempt_dir, kind = Path(attempt_dir), spec["kind"]
        run = attempt_dir / "run"
        if kind in RUN_KINDS:
            job = self._job("run-one", spec, attempt_dir, split=spec["split"], arm=spec["arm"], seed=spec["seed"],
                            role=spec["role"], target_checkpoint=spec["target"], evaluate_bank=spec["bank"],
                            resume_from=sources.get("resume_from"), replicate_of=None)
            engine_call, extra = runner.run_one, {"allow_hidden": spec["bank"] == "hidden", "registry": self.registry}
        elif kind == "attribution":
            job = self._job("attributes", spec, attempt_dir, split=spec["split"], seed=spec["seed"], role=spec["role"],
                            a0_states=dict(sources["a0_states"]), group_ids=list(spec["group_ids"]), query_bank="ref")
            engine_call, extra = runner.attributes, {}
        elif kind == "score_groups":
            job = self._job("score-groups", spec, attempt_dir, split=spec["split"])
            engine_call, extra = runner.score_groups, {}
        elif kind == "export_view":
            view, receipt = attempt_dir / "view.json", attempt_dir / "view-receipt.json"
            try:
                out = export_selector_view(self.prepared, sources["guard_run"], view, receipt)
            except Exception as exc:  # noqa: BLE001 - work started: a charged technical failure
                return self._failed(run, exc)
            return {"status": "complete", "artifact": str(view), "artifact_sha256": out["view_sha256"],
                    "error": None, "engine_setup_seconds": {}}
        elif kind == "relevance":
            try:
                data, receipt = build_relevance(self.prepared, self.manifest_sha256)
                digest = write_once(attempt_dir / "relevance.json", data)
                write_once_json(attempt_dir / "relevance-receipt.json", receipt)
            except Exception as exc:  # noqa: BLE001 - work started: a charged technical failure
                return self._failed(run, exc)
            return {"status": "complete", "artifact": str(attempt_dir / "relevance.json"),
                    "artifact_sha256": digest, "error": None, "engine_setup_seconds": {}}
        else:
            raise RequestRefused(f"unknown operation kind {kind!r}")
        try:
            engine_call(job, prepared_dir=self.prepared, out_dir=run, session=self.session, **extra)
        except Exception as exc:  # noqa: BLE001 - any engine failure once running, registry refusals included
            return self._failed(run, exc)
        return self._complete(run)

    def _local(self, receipt: dict) -> Path:
        return self.path_map.resolve(receipt["artifact"])

    def verify(self, receipt: dict, spec: dict) -> None:
        artifact = self._local(receipt)
        if spec["kind"] in ("export_view", "relevance"):
            if not artifact.is_file() or sha256_file(artifact) != receipt["artifact_sha256"]:
                raise VerificationError(f"{artifact} differs from its receipt")
            return
        report = verify_run(artifact, self.prepared, self.path_map)
        if not report["complete"]:
            raise VerificationError(f"{artifact} does not verify: {report['problems'][:3]}")
        if sha256_file(artifact / "COMPLETE.json") != receipt["artifact_sha256"]:
            raise VerificationError(f"{artifact}: COMPLETE.json differs from the receipt (changed or replaced)")
        job, marker = read_json(artifact / "job.json"), read_json(artifact / "COMPLETE.json")
        identity = {k: marker["identity"][k] for k in ("manifest_sha256", "recipe_sha256", "code_sha256")}
        if identity != self.pins:
            raise VerificationError(f"{artifact} was produced under other pins {identity}")
        expected = {"kind": {"attribution": "attributes", "score_groups": "score-groups"}.get(spec["kind"], "run-one"),
                    "split": spec["split"]}
        if spec["kind"] in RUN_KINDS:
            expected.update(arm=spec["arm"], seed=spec["seed"], role=spec["role"],
                            target_checkpoint=spec["target"], evaluate_bank=spec["bank"])
        elif spec["kind"] == "attribution":
            expected.update(seed=spec["seed"], role=spec["role"])
        wrong = {k: [job.get(k), v] for k, v in expected.items() if job.get(k) != v}
        if wrong:
            raise VerificationError(f"{artifact} is not the operation {spec['op_id']}: {wrong}")

    def evaluation(self, receipt: dict, spec: dict) -> Evaluation:
        ev = read_evaluation(self._local(receipt),
                             expect={"split": spec["split"], "arm": spec["arm"], "seed": spec["seed"],
                                     "role": spec["role"], "checkpoint": spec["target"], "bank": spec["bank"],
                                     **self.pins},
                             prepared_dir=self.prepared, path_map=self.path_map)
        if ev.source["complete_sha256"] != receipt["artifact_sha256"]:
            raise VerificationError(f"{spec['op_id']}: evaluation folder differs from its receipt")
        return ev

    def attribution_scores(self, receipt: dict, spec: dict, a0_states: Mapping[str, str]) -> dict:
        scores, digest = read_attribution(self._local(receipt),
                                          expect={"split": spec["split"], "seed": spec["seed"], "role": spec["role"],
                                                  "group_ids": list(spec["group_ids"]), **self.pins},
                                          a0_states=dict(a0_states), prepared_dir=self.prepared,
                                          path_map=self.path_map)
        if digest != receipt["artifact_sha256"]:
            raise VerificationError(f"{spec['op_id']}: attribution folder differs from its receipt")
        return scores

    def static_inputs(self, view_receipt: dict, relevance_receipt: dict, split: str):
        view = read_selector_view(self._local(view_receipt), view_receipt["artifact_sha256"])
        if view.split != split:
            raise VerificationError(f"the selector view is of split {view.split}, not {split}")
        relevance, pins = read_relevance(self._local(relevance_receipt), relevance_receipt["artifact_sha256"], split)
        return view, relevance, pins
