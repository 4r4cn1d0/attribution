"""The thin block controller: one serialized scheduler per study root (stdlib only).

One block, executed or resumed by ``Study.run_block``:

1. **Static** (study level, once): score-groups of the selection split, the selector-view
   export, the frozen relevance table; its fingerprint must equal the configuration pin.
2. **Screen** at the block's first selector seed z0: a0 and every edit to the short
   checkpoint with evaluation, in the block's seeded order.
3. **S+ prerequisites**: a0's attribution states at z0 (``costs.prerequisite_ops``) and the
   attribution passes.
4. **Rankings** of both methods from frozen development models (whitelisted features only)
   and **acquisition transcripts** (``policy.plan_acquisition``, quotes only), written before
   any purchase is executed.
5. **Purchases** of both transcripts, interleaved one purchase at a time starting with the
   block's seeded first policy; a physically complete canonical operation is reused (each
   policy is still charged it).
6. **Choices** from each policy's OWN completed paired full observations, then the **lock**:
   rankings, transcripts, observations, choices, every receipt hash, the outcome definition (and
   the optional S- one-extra-purchase sensitivity, executed before the lock).
7. **Final deployment**: a0 and every chosen arm trained to the full checkpoint on the block's
   fresh final seed and evaluated on the final bank (hidden in confirmation), then the result.
   Every final access, fresh or a reuse of a completed operation, first passes
   ``backend.check_lock``: the lock of this block and configuration, pinned by hash, must
   authorize the arm and the final seed.

Every operation has a canonical spec (``spec.json``; it names its block and configuration) and
numbered attempt folders: a ``started.json`` before the call and an immutable after-call
``receipt.json`` with external synchronized monotonic times, both tagged with the session (one
``run_block`` call, recorded in ``sessions/``) that ran the attempt; a receipt without a backend
result records its engine setup stages as unknown (null), never as zero. Only an explicit validation refusal
before any work (``RequestRefused`` with nothing written in the attempt folder) is recorded as
``refused``: not charged, not counted, and it stops the controller. Every other outcome once
execution started is an attempt: a returned failure, or any exception (an engine error, a failed
write after computing), is a timed ``failed`` attempt with its error preserved, charged, and
retried as the same scientific draw up to ``retry.max_attempts``; then the observation stays
missing (no seed substitution). An attempt interrupted without a receipt is closed on resume with
its known lower bound. Every derived record is write-once: a resume recomputes it and refuses any
difference (changed pins, config, code, record, receipts or cached state). The controller holds an
exclusive ``flock`` on the study root; the engine registry is not concurrency-safe.

A session writes a start record before its first operation and, when it returns or raises, an end
record (``session-<n>-end.json``) with its controller seconds outside attempts by owner: the
controller's timeline is cut at every attempt's external timer and at every change of the step it
serves (``costs`` module doc), so attempts and owner segments tile the session; only a killed
process leaves a session without an end record, whose controller seconds then stay unknown. The
end record's final clock read is where controller timing stops: writing that record, returning and
process exit are outside every controller-timed total (``costs.PHYSICAL_BOUNDARY``).

A block result is ``complete`` (every primary endpoint observed), ``final-incomplete`` (technical
retries exhausted in a final deployment; the endpoints that the completed finals determine are
kept) or ``aborted`` (technical retries exhausted before the lock; each policy's cost incurred up
to the abort is kept, never extrapolated). Its costs (``costs.COST_SCOPES``, ``costs.COST_CONTRACT``)
keep each policy's whole-research ledger and add the selection-plus-one-chosen-model subtotal, the
additional reference and sensitivity research and the deduplicated physical seconds, each with its
completeness. That cost object is a PROVISIONAL snapshot: the result is written inside its session,
before the session's end record, so the snapshot marks that session open, counts its controller
seconds closed so far and is never complete in the physical seconds or in a scope charged that
session. The result is immutable and is never completed afterwards; the authoritative economic
accounting is ``recorded_block_costs``, recomputed read-only from the block's durable records
(attempt receipts, session start and end records, plans, lock), which a missing end record leaves
a lower bound for good. An existing result is returned again only after ``verified_result`` (the
lock rules of ``verify_study``, configuration, outcome definition and final seed); a removed or
changed lock refuses and nothing reruns. ``study_evidence`` is the analysis entrypoint's read-only
view of a study: the verified results with their recorded costs and, for every started block
without a result, its known incurred costs (lower bounds), all from the blocks' own receipts,
sessions, plans and locks.
"""

from __future__ import annotations

import math
import os
import random
import re
import weakref
from fractions import Fraction
from pathlib import Path
from typing import Mapping, Sequence

from .backend import LOCK_KIND, check_lock, lock_authorization
from .common import (LockError, PolicyError, RequestRefused, VerificationError, derive_seed, read_canonical,
                     sha256_file, utc_now, write_once_json)
from .config import (METHODS, MODE_ROLES, check_config, check_feasibility, config_sha256,
                     progression, require_confirmation_ready, validate_config)
from .costs import (COST_CONTRACT, COST_SCOPES, PHYSICAL_BOUNDARY, PRIMARY_COST_SCOPE, STATIC_OPS, Shape,
                    attempt_seconds, attribution_state_ops, block_physical, block_setup_measured, block_setup_seconds,
                    controller_unknown, fixed_charges, make_quoter, physical_seconds, policy_costs, policy_owners,
                    prerequisite_ops, quoted_ledger)
from .features import (TARGETS, attribution_features, merge, method_features, select, short_features,
                       view_features)
from .outcomes import CHANGES, OUTCOME_PIN, identity_contrast, paired_change, rate_contrast
from .policy import Op, choose, full_op, next_purchase, plan_acquisition, rank_edits
from .ridge import RidgeModel

try:
    import fcntl
except ImportError:  # pragma: no cover - POSIX hosts only
    fcntl = None

__all__ = ["STUDY_KIND", "RECEIPT_KIND", "LOCK_KIND", "RESULT_KIND", "SESSION_END_KIND", "SCHEDULE_RULE",
           "ENDPOINTS", "Study", "load_models", "interleave", "verify_study", "verified_result",
           "started_block_costs", "recorded_block_costs", "study_evidence", "SNAPSHOT_NOTE", "RECORDED_SOURCE"]

STUDY_KIND = "safety-decision-policy study"
RECEIPT_KIND = "safety-decision-policy operation receipt"
RESULT_KIND = "safety-decision-policy block result"
SESSION_END_KIND = "safety-decision-policy session end v1"
OWNERS_NOTE = ("controller seconds outside attempts by the step they served: common (static, screen, lock), S- and "
               "S+ (prerequisites, scores, ranking, plan, purchases, choice), final:<arm>, sensitivity; reuse (a "
               "second verification of an artifact this session produced) and result (the block result's own "
               "computation and write) are in no policy's scope")
SNAPSHOT_NOTE = ("PROVISIONAL snapshot, taken inside the session that wrote this result and before that session's end "
                 "record: the session is marked open, its controller seconds closed so far are counted and the result's "
                 "own computation and write are not; the physical seconds and every scope charged that session are "
                 "therefore lower bounds here. The authoritative accounting is recomputed from the durable records "
                 "(controller.recorded_block_costs); this immutable result is never completed afterwards")
RECORDED_SOURCE = ("recorded: recomputed read-only from the block's durable records (every counted attempt receipt, the "
                   "session start and end records, the plans and the lock); a session without its end record leaves "
                   "the physical seconds and every scope charged that session lower bounds")
ABORT_SCOPE = ("incurred up to the abort (every attempt of the attempted fixed-charge operations and the overhead of the "
               "sessions this policy owns): a lower bound, not a standalone cost")
SCHEDULE_RULE = ("random.Random(derive_seed('execution-order', schedule_seed, block)): shuffle the screen "
                 "order, draw the first policy, then shuffle the final-deployment order; purchases alternate "
                 "between policies one purchase at a time from the first policy")
EVALUATION_STAGES = ("query_loss", "generate", "arc_utility", "guard", "secondary_toxicity")
MEASURE_OF = dict(zip(CHANGES, ("safety", "utility", "refusal")))
ENDPOINTS = {
    "Y": "F(A-) - F(A+): the guard's emitted-text Unsafe rate of the two locked choices trained on the block's "
         "fresh final seed, on the final bank",
    "relative_to_a0": "per policy, dF, L and O of its choice against a0 on the same final seed and bank",
    "utility_contrast": "L(S-) - L(S+) = U(A+) - U(A-)",
    "refusal_contrast": "O(S-) - O(S+) = R(A-) - R(A+)",
    "values": "each as raw, missing_label and broader (utility also tie_aware; outcomes.OUTCOME_DEFINITION); "
              "identical arms are exactly 0 by identity (one model); null when a needed final deployment is "
              "missing"}
# Backends (each holds one asset cache, e.g. the engine Session) that already served a run_block call
# in this process: a later session on one of them reuses its loads and is recorded as shared.
_SERVED_BACKENDS: weakref.WeakSet = weakref.WeakSet()


def load_models(record: dict, config: dict, lists: Mapping[str, list[str]]) -> dict[str, dict[str, RidgeModel]]:
    """The frozen development models of both methods at the configuration's lambdas."""
    entry = next(t for t in record["tables"] if t["table_sha256"] == config["pins"]["development_table_sha256"])
    out = {}
    for method in METHODS:
        key = "S-" if method == "S-" else f"S+/{config['features']['attribution']}"
        out[method] = {}
        for target in TARGETS:
            lam = float(config["predictor"]["selected_lambda"][method][target])
            found = [m for m in entry["fits"][key]["targets"][target]["models"] if m["lambda"] == lam]
            if len(found) != 1:
                raise VerificationError(f"the record holds no {key} {target} model at lambda {lam}")
            model = RidgeModel.from_json(found[0]["model"])
            if list(model.features) != lists[method]:
                raise VerificationError(f"the {key} {target} model uses other features")
            out[method][target] = model
    return out


def interleave(transcripts: Mapping[str, dict], first: str) -> list[tuple[str, dict]]:
    """Purchases of both policies, alternating one purchase at a time from ``first``."""
    queues = {m: list(transcripts[m]["purchases"]) for m in METHODS}
    order, turn = [], first
    while queues["S-"] or queues["S+"]:
        if queues[turn]:
            order.append((turn, queues[turn].pop(0)))
        turn = "S+" if turn == "S-" else "S-"
    return order


def _op(key: list) -> Op:
    return Op(key[0], key[1], key[2])


def _attempts(op_dir: Path) -> list[Path]:
    return sorted((p for p in op_dir.glob("attempt-*") if p.is_dir()), key=lambda p: int(p.name[8:]))


def _closing_receipt(op_id: str, attempt_dir: Path) -> dict:
    """The receipt of an attempt interrupted without an after-call receipt: its known lower bound
    (the last end recorded in its run ledger), its setup unknown, its session tag from started.json."""
    started = read_canonical(attempt_dir / "started.json") if (attempt_dir / "started.json").exists() else {}
    bound = 0.0
    ledger = attempt_dir / "run" / "ledger.jsonl"
    if ledger.exists():
        from experiments.safety_selection.common import recover_jsonl

        rows, _ = recover_jsonl(ledger)
        bound = max((r.get("end_s", 0.0) for r in rows), default=0.0)
    return {"kind": RECEIPT_KIND, "op_id": op_id, "attempt": int(attempt_dir.name[8:]),
            "spec_sha256": started.get("spec_sha256"), "status": "interrupted",
            "start_utc": started.get("start_utc"), "end_utc": None,
            "monotonic_start": started.get("monotonic_start"), "monotonic_end": None,
            "seconds": None, "seconds_lower_bound": bound, "artifact": None, "artifact_sha256": None,
            "error": "interrupted without an after-call receipt; closed on resume",
            "engine_setup_seconds": None, "engine_stage_seconds": None,
            "pid": started.get("pid"), "session": started.get("session")}


def _read_receipts(op_dir: Path) -> list[dict]:
    """Every counted attempt receipt of an operation folder (explicit refusals excluded), read only:
    an attempt without an after-call receipt contributes its closing receipt in memory (a lower
    bound); nothing is written or closed."""
    out = []
    for attempt_dir in _attempts(op_dir):
        path = attempt_dir / "receipt.json"
        receipt = read_canonical(path) if path.exists() else _closing_receipt(op_dir.name, attempt_dir)
        if receipt.get("op_id") != op_dir.name or receipt.get("attempt") != int(attempt_dir.name[8:]):
            raise VerificationError(f"{path} belongs to another operation or attempt")
        if receipt["status"] != "refused":
            out.append(receipt)
    return out


def _session_numbers(folder: Path) -> list[int]:
    """The numbers of a block's session start records (``session-<n>.json``), ascending."""
    if not folder.is_dir():
        return []
    return sorted(int(m.group(1)) for p in folder.iterdir() if (m := re.fullmatch(r"session-(\d+)\.json", p.name)))


def _read_sessions(block_dir: Path) -> list[dict]:
    """The block's session start records, each with ``controller_seconds`` from its end record (None
    without one: a killed process, or the session still running)."""
    folder = block_dir / "sessions"
    out = []
    for number in _session_numbers(folder):
        record = read_canonical(folder / f"session-{number}.json")
        end_path = folder / f"session-{number}-end.json"
        end = read_canonical(end_path) if end_path.exists() else None
        if end is not None and (end.get("kind") != SESSION_END_KIND or end.get("session") != number
                                or end.get("block") != record.get("block")
                                or not isinstance(end.get("controller_seconds"), dict)):
            raise VerificationError(f"{end_path} does not close session {number} of its block")
        out.append({**record, "controller_seconds": None if end is None else end["controller_seconds"]})
    return out


def _flock(path: Path):
    handle = open(path, "a")  # noqa: SIM115 - held for the life of the controller
    if fcntl is not None:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            raise PolicyError(f"another controller holds {path}; execution is serialized") from None
    return handle


class Study:
    """A study root bound to one frozen configuration, record, backend and set of pins."""

    def __init__(self, root: str | Path, *, config: dict, record: dict, backend, recipe: dict,
                 data_config: Mapping, shape: Shape, actual_pins: Mapping[str, str],
                 process_start: float, engineering_fixture: bool = False) -> None:
        validate_config(config)
        if engineering_fixture:
            if not getattr(backend, "engineering_fixture", False):
                raise PolicyError("engineering_fixture is allowed only with the synthetic fake backend")
        else:
            require_confirmation_ready(config)
        self.checks = check_config(config, recipe=recipe, data_config=data_config, record=record,
                                   actual_pins=actual_pins)
        self.feasibility = check_feasibility(config, shape)
        self.root, self.config, self.record, self.backend = Path(root).resolve(), config, record, backend
        self.data_config, self.shape, self.process_start = data_config, shape, process_start
        self.config_sha256 = config_sha256(config)
        self.short, self.full = config["fidelity"]["short"], config["fidelity"]["full"]
        self.quote = make_quoter(config["tariffs"], shape, self.short, self.full)
        self.roles = MODE_ROLES[config["mode"]]
        self.lists = method_features(config["features"]["x0"], config["features"]["attribution"])
        self.models = load_models(record, config, self.lists)
        self.constraints = config["constraints"]
        self.max_attempts = config["retry"]["max_attempts"]
        self._evaluations: dict = {}
        self._session_mark: float = process_start
        self._session: dict | None = None        # {"block", "number"} of the current run_block call
        self._session_start: float = process_start
        self._owner: str | None = None           # the step the running controller segment serves
        self._mark: float = process_start        # where the running controller segment began
        self._segments: dict[str, float] = {}    # closed controller seconds of the session by owner
        self._blocks_run: set[int] = set()
        self.root.mkdir(parents=True, exist_ok=True)
        self._handle = _flock(self.root / "controller.lock")
        self.pins = {**dict(actual_pins), "config_sha256": self.config_sha256}
        try:
            write_once_json(self.root / "study.json", {"kind": STUDY_KIND, "pins": self.pins,
                                                        "outcome_definition": config["outcome_definition"],
                                                        "mode": config["mode"], "status": config["status"]})
        except BaseException:
            self._handle.close()
            raise

    def close(self) -> None:
        self._handle.close()

    # ----- operations -----------------------------------------------------------------

    def spec(self, op: Op, block: int | None, lock_sha256: str | None = None) -> dict:
        split, role, bank = self.roles["selection"]
        out = {"op_id": op.op_id, "kind": op.kind, "arm": op.arm or None, "seed": op.seed if op.seed >= 0 else None,
               "block": block, "config_sha256": self.config_sha256, "split": split, "role": role, "bank": None,
               "target": None, "depends_on": {}, "group_ids": None, "lock_sha256": None}
        if op.kind == "screen":
            out.update(bank=bank, target=self.short)
        elif op.kind == "full_from_short":
            out.update(bank=bank, target=self.full, depends_on={"resume_from": Op("screen", op.arm, op.seed).op_id})
        elif op.kind == "full_from_init":
            out.update(bank=bank, target=self.full)
        elif op.kind == "extend":
            out.update(target=self.shape.last_attribution(),
                       depends_on={"resume_from": full_op(op.arm, op.seed, op.seed).op_id})
        elif op.kind == "attribution":
            states = attribution_state_ops(self.shape, self.short, self.full, op.seed)
            out.update(group_ids=list(self.shape.edits),
                       depends_on={f"a0_state:{c}": o.op_id for c, o in states.items()})
        elif op.kind == "final":
            if lock_sha256 is None:
                raise LockError("a final operation needs the hash of the choice lock")
            split, role, bank = self.roles["final"]
            out.update(split=split, role=role, bank=bank, target=self.full, lock_sha256=lock_sha256)
        elif op.kind == "score_groups":
            out.update(role=None)
        elif op.kind == "export_view":
            out.update(role=None, depends_on={"guard_run": "score_groups"})
        elif op.kind == "relevance":
            out.update(role=None, split=None)
        else:
            raise PolicyError(f"unknown operation kind {op.kind!r}")
        return out

    def _op_dir(self, op_id: str, block: int | None) -> Path:
        if op_id in {o.op_id for o in STATIC_OPS}:
            return self.root / "static" / op_id
        if block is None:
            raise PolicyError(f"{op_id} needs a block")
        return self.root / "blocks" / str(block) / "ops" / op_id

    def receipts(self, op_id: str, block: int | None) -> list[dict]:
        """Every counted attempt receipt of an operation (explicit refusals excluded); an attempt
        interrupted without a receipt is closed now with its known lower bound."""
        op_dir = self._op_dir(op_id, block)
        for attempt_dir in _attempts(op_dir):
            if not (attempt_dir / "receipt.json").exists():
                write_once_json(attempt_dir / "receipt.json", _closing_receipt(op_id, attempt_dir))
        return _read_receipts(op_dir)

    def _switch(self, owner: str | None) -> str | None:
        """Close the running controller segment (charged to the step it served) and start one for
        ``owner`` (None: none); returns the previous owner."""
        now = self.backend.clock()
        previous = self._owner
        if previous is not None:
            self._segments[previous] = self._segments.get(previous, 0.0) + (now - self._mark)
        self._owner, self._mark = owner, now
        return previous

    def ensure_op(self, op: Op, block: int | None, *, lock: tuple[Path, str] | None = None) -> dict | None:
        """The complete receipt of an operation (verified), executing or retrying it if needed;
        None after ``retry.max_attempts`` counted attempts without completion. A final-bank
        operation needs the valid lock even to reuse a completed attempt."""
        spec = self.spec(op, block, lock_sha256=lock[1] if lock else None)
        check_lock(spec, {"lock": str(lock[0])} if lock else {})
        op_dir = self._op_dir(op.op_id, block)
        spec_sha = write_once_json(op_dir / "spec.json", spec)
        executed = False
        while True:
            receipts = self.receipts(op.op_id, block)
            done = [r for r in receipts if r["status"] == "complete"]
            if done:
                # a repeated verification of an artifact this session produced (another step's shared
                # operation) is charged to no policy; a standalone policy would not repeat it
                reuse = not executed and self._session is not None and done[0].get("session") == self._session
                previous = self._switch("reuse") if reuse else None
                try:
                    self.backend.verify(done[0], spec)
                finally:
                    if reuse:
                        self._switch(previous)
                return done[0]
            if len(receipts) >= self.max_attempts:
                return None
            sources = self._sources(spec, block, lock)
            attempt = max((int(p.name[8:]) for p in _attempts(op_dir)), default=0) + 1
            attempt_dir = op_dir / f"attempt-{attempt}"
            attempt_dir.mkdir(parents=True)
            self.backend.sync()
            start, start_utc = self.backend.clock(), utc_now()
            if self._owner is not None:   # the controller segment ends where the attempt's timer starts
                self._segments[self._owner] = self._segments.get(self._owner, 0.0) + (start - self._mark)
            self._mark = start
            executed = True
            write_once_json(attempt_dir / "started.json", {"op_id": op.op_id, "attempt": attempt,
                                                           "spec_sha256": spec_sha, "start_utc": start_utc,
                                                           "monotonic_start": start, "pid": os.getpid(),
                                                           "session": self._session})
            status, result, error = "failed", None, None
            try:
                result = self.backend.execute(spec, attempt_dir, sources)
                status = result.get("status")
                if status not in ("complete", "failed"):
                    status, error = "failed", f"backend returned status {status!r}"
                elif status == "failed":
                    error = result.get("error")
            except RequestRefused as exc:
                error = f"{type(exc).__name__}: {exc}"
                if all(p.name == "started.json" for p in attempt_dir.iterdir()):
                    status = "refused"
                    raise
                error += " (raised after the attempt wrote files: a failed attempt)"
            except Exception as exc:  # noqa: BLE001 - after execution started: a charged, counted failure
                error = f"{type(exc).__name__}: {exc} (raised after execution started: a failed attempt)"
            except BaseException:
                status, error = "interrupted", "interrupted during the operation"
                raise
            finally:
                self.backend.sync()
                end = self.backend.clock()
                if status != "refused":               # a counted attempt's [start, end] is its own receipt;
                    self._mark = end                  # an uncounted refusal stays controller time
                recorded = isinstance(result, dict)   # otherwise the setup stages inside are unknown, not zero
                done_result = result if recorded and status == "complete" else {}
                write_once_json(attempt_dir / "receipt.json", {
                    "kind": RECEIPT_KIND, "op_id": op.op_id, "attempt": attempt, "spec_sha256": spec_sha,
                    "status": status, "start_utc": start_utc, "end_utc": utc_now(), "monotonic_start": start,
                    "monotonic_end": end, "seconds": end - start,
                    "artifact": (result.get("artifact") if recorded else None),
                    "artifact_sha256": done_result.get("artifact_sha256"), "error": error,
                    "engine_setup_seconds": (result.get("engine_setup_seconds", {}) if recorded else None),
                    "engine_stage_seconds": (result.get("engine_stage_seconds", {}) if recorded else None),
                    "pid": os.getpid(), "session": self._session})

    def _complete(self, op_id: str, block: int | None) -> dict:
        done = [r for r in self.receipts(op_id, block) if r["status"] == "complete"]
        if not done:
            raise VerificationError(f"dependency {op_id} is not complete")
        return done[0]

    def _sources(self, spec: dict, block: int | None, lock: tuple[Path, str] | None) -> dict:
        out: dict = {}
        for name, dep in spec["depends_on"].items():
            artifact = self._complete(dep, block)["artifact"]
            if name.startswith("a0_state:"):
                out.setdefault("a0_states", {})[name.split(":", 1)[1]] = artifact
            else:
                out[name] = artifact
        if lock is not None:
            out["lock"] = str(lock[0])
        return out

    # ----- static -------------------------------------------------------------------

    def ensure_static(self) -> tuple:
        receipts = {}
        for op in STATIC_OPS:
            receipt = self.ensure_op(op, None)
            if receipt is None:
                raise VerificationError(f"static operation {op.op_id} failed {self.max_attempts} times; the study "
                                        "cannot proceed (no substitute features)")
            receipts[op.op_id] = receipt
        view, relevance, pins = self.backend.static_inputs(receipts["export_view"], receipts["relevance"],
                                                           self.roles["selection"][0])
        if pins["fingerprint_sha256"] != self.config["pins"]["relevance_fingerprint_sha256"]:
            raise VerificationError("the relevance table does not reproduce the frozen development fingerprint")
        if tuple(view.menu[1:]) != self.shape.edits:
            raise VerificationError("the selector view menu differs from the offline plan's edits")
        return receipts, view, relevance

    # ----- block --------------------------------------------------------------------

    def _block_dir(self, block: int) -> Path:
        return self.root / "blocks" / str(block)

    def _schedule(self, block: int) -> dict:
        rng = random.Random(derive_seed("execution-order", self.config["blocks"]["schedule_seed"], block))
        screen = ["a0", *self.shape.edits]
        rng.shuffle(screen)
        first = rng.choice(list(METHODS))
        schedule = {"block": block, "screen_order": screen, "first_policy": first,
                    "final_order_key": rng.getrandbits(64), "rule": SCHEDULE_RULE}
        write_once_json(self._block_dir(block) / "schedule.json", schedule)
        return schedule

    def _session_receipt(self, block: int) -> None:
        """Record this run_block call as the block's next session; its attempts carry its tag. A
        call whose backend (asset cache) already served a run_block call in this process records a
        zero-length shared session: the time since then is other work, never this block's setup."""
        folder = self._block_dir(block) / "sessions"
        folder.mkdir(parents=True, exist_ok=True)
        number = max(_session_numbers(folder), default=0) + 1
        self.backend.sync()
        now = self.backend.clock()
        shared = bool(self._blocks_run) or self.backend in _SERVED_BACKENDS
        start = now if shared else self._session_mark
        write_once_json(folder / f"session-{number}.json", {
            "block": block, "session": number, "pid": os.getpid(), "utc": utc_now(), "monotonic_start": start,
            "monotonic_end": now, "seconds": now - start, "process_shared_with_an_earlier_block": shared,
            "blocks_already_run_by_this_controller": sorted(self._blocks_run),
            "scope": "process start, imports, pin checks and session creation before the block's first "
                     "operation (zero-length when the backend's asset cache already served a run_block call "
                     "in this process; a block none of whose sessions started a fresh process has unmeasured "
                     "setup and lower-bound costs: run one block per process); asset loads inside engine "
                     "operations come from their ledgers; the controller seconds after this record are in the "
                     f"session's end record ({SESSION_END_KIND})"})
        self._session_mark = now
        self._session = {"block": block, "number": number}
        self._session_start = now
        self._segments, self._owner, self._mark = {}, "common", now
        self._blocks_run.add(block)
        try:
            _SERVED_BACKENDS.add(self.backend)
        except TypeError:  # pragma: no cover - a backend without weak references: per-controller tracking only
            pass

    def _end_session(self, block: int, exit_note: str, quiet: bool = False) -> None:
        """Close the running controller segment and write the session's end record (controller
        seconds by owner, ``OWNERS_NOTE``). On an exception exit a failed write is not raised over the
        original error; the session's controller seconds then stay unknown (lower bounds)."""
        try:
            self._switch(None)
            number = self._session["number"]
            write_once_json(self._block_dir(block) / "sessions" / f"session-{number}-end.json", {
                "kind": SESSION_END_KIND, "block": block, "session": number, "pid": os.getpid(), "utc": utc_now(),
                "monotonic_start": self._session_start, "monotonic_end": self._mark,
                "seconds": self._mark - self._session_start, "exit": exit_note[:300],
                "controller_seconds": dict(sorted(self._segments.items())), "owners": OWNERS_NOTE,
                "scope": "the session from its start record's end: attempts (their own receipts) and these "
                         "controller seconds tile it"})
        except Exception:
            if not quiet:
                raise
        finally:
            self._session, self._owner = None, None

    def _session_records(self, block: int) -> list[dict]:
        """The block's session records with their controller seconds by owner: from each end record;
        for this controller's running session the segments closed so far, marked ``open`` (its end
        record does not exist yet: counted, and a lower bound like a missing end record)."""
        out = []
        for record in _read_sessions(self._block_dir(block)):
            if record["controller_seconds"] is None and self._session == {"block": block, "number": record["session"]}:
                record = {**record, "controller_seconds": dict(sorted(self._segments.items())), "open": True}
            out.append(record)
        return out

    def _result(self, block: int, result: dict) -> dict:
        write_once_json(self._block_dir(block) / "result.json", result)
        return result

    def run_block(self, block: int) -> dict:
        """Execute or resume one block (see module doc); returns its immutable result. An existing
        result is returned only after ``verified_result``: nothing reruns or is rewritten, and a
        removed or changed lock refuses."""
        if not 0 <= block < self.config["blocks"]["count"]:
            raise PolicyError(f"block {block} is not configured")
        if (self._block_dir(block) / "result.json").exists():
            return verified_result(self.root, block, config_sha256=self.config_sha256,
                                   final_seed=self.config["blocks"]["list"][block]["final_seed"], pins=self.pins)
        self._session_receipt(block)
        try:
            result = self._execute(block)
        except BaseException as exc:
            self._end_session(block, f"{type(exc).__name__}: {exc}", quiet=True)
            raise
        self._end_session(block, "returned")
        return result

    def _execute(self, block: int) -> dict:
        prog = progression(self.config, self.data_config, block)
        z0, final_seed = prog.at(0), self.config["blocks"]["list"][block]["final_seed"]
        static_receipts, view, relevance = self.ensure_static()
        static_values, ties = view_features(view)
        schedule = self._schedule(block)
        base = {"kind": RESULT_KIND, "block": block, "mode": self.config["mode"],
                "config_status": self.config["status"], "config_sha256": self.config_sha256,
                "outcome_definition": OUTCOME_PIN,
                "seeds": {"screen": z0, "progression": {"start": prog.start, "stride": prog.stride, "last": prog.last},
                          "final": final_seed}}
        screen = {}
        for arm in schedule["screen_order"]:
            receipt = self.ensure_op(Op("screen", arm, z0), block)
            if receipt is None:
                return self._result(block, {**base, "status": "aborted", "stage": "screen",
                                            "reason": f"screen of {arm} exhausted {self.max_attempts} technical "
                                                      "attempts; no substitute seed or imputed feature",
                                            "costs": self._abort_costs(block, z0)})
            screen[arm] = self._evaluation(Op("screen", arm, z0), block)
        short = {g: paired_change(screen[g], screen["a0"]) for g in self.shape.edits}
        self._switch("S+")                   # S+'s prerequisites, attribution passes and scores
        prereq = prerequisite_ops(self.shape, self.short, self.full, z0)
        attr_op = Op("attribution", "", z0)
        for op in [*prereq, attr_op]:
            if self.ensure_op(op, block) is None:
                return self._result(block, {**base, "status": "aborted", "stage": "S+ prerequisite",
                                            "reason": f"S+ prerequisite {op.op_id} exhausted {self.max_attempts} "
                                                      "technical attempts",
                                            "costs": self._abort_costs(block, z0)})
        attr_spec = self.spec(attr_op, block)
        a0_states = {c: self._complete(dep, block)["artifact"] for c, dep in
                     ((name.split(":", 1)[1], dep) for name, dep in attr_spec["depends_on"].items())}
        scores = attribution_features(self.backend.attribution_scores(self._complete(attr_op.op_id, block),
                                                                      attr_spec, a0_states))
        self._switch("common")
        rows = {"S-": {g: merge(static_values[g], relevance[g], short_features(short[g])) for g in self.shape.edits}}
        rows["S+"] = {g: merge(rows["S-"][g], scores[g]) for g in self.shape.edits}
        rankings, transcripts, charges = {}, {}, {}
        for method in METHODS:
            self._switch(method)             # its predictions, ranking and acquisition plan
            predictions = {g: {t: self.models[method][t].predict(select(rows[method][g], self.lists[method], g))
                               for t in TARGETS} for g in self.shape.edits}
            ranking = rank_edits(predictions, ties, self.constraints)
            rankings[method] = {"method": method, "features": self.lists[method],
                                "inputs": {g: {n: rows[method][g][n] for n in self.lists[method]} for g in self.shape.edits},
                                "ranking": ranking}
            write_once_json(self._block_dir(block) / f"ranking-{method}.json", rankings[method])
            charges[method] = fixed_charges(method, self.quote, self.shape, self.config["tariffs"],
                                            self.short, self.full, z0)
            fixed = sum((c["quote"] for c in charges[method]), Fraction(0))
            available = Fraction(self.config["budget"]["total_quote_seconds"]) - fixed
            owned = {op for c in charges[method] for op in c["ops"]}
            transcripts[method] = plan_acquisition(ranking=[r["edit"] for r in ranking], available=available,
                                                   quote=self.quote, seed_at=prog.at, owned=owned, screen_seed=z0)
            write_once_json(self._block_dir(block) / f"plan-{method}.json",
                            {"method": method, "charges": [{"category": c["category"], "quote": float(c["quote"]),
                                                            "ops": [o.op_id for o in c["ops"]]} for c in charges[method]],
                             "transcript": transcripts[method]})
        for method, purchase in interleave(transcripts, schedule["first_policy"]):
            self._switch(method)
            for key in purchase["op_keys"]:
                self.ensure_op(_op(key), block)
        owned = {m: {_op(k) for p in transcripts[m]["purchases"] for k in p["op_keys"]}
                 | {op for c in charges[m] for op in c["ops"]} for m in METHODS}
        choices = {}
        for method in METHODS:
            self._switch(method)             # reads its own observations (evaluations cached per step)
            choices[method] = self._choose(owned[method], block, ties)
        sensitivity = None
        if "s_minus_one_extra_purchase" in self.config["analysis"]["sensitivity"]:
            self._switch("sensitivity")
            sensitivity = self._extra_purchase(block, transcripts["S-"], rankings["S-"], owned["S-"], prog, z0, ties)
        self._switch("common")
        lock = {"kind": LOCK_KIND, "block": block, "pins": self.pins, "outcome_definition": OUTCOME_PIN,
                "seeds": base["seeds"], "schedule": schedule,
                "static_receipts": {k: self._receipt_sha(k, None) for k in static_receipts},
                "methods": {m: {"ranking": rankings[m], "transcript": transcripts[m],
                                "charges": [{"category": c["category"], "quote": float(c["quote"]),
                                             "ops": [o.op_id for o in c["ops"]]} for c in charges[m]],
                                "choice": choices[m]} for m in METHODS},
                "sensitivity": sensitivity,
                "receipts": self._block_receipt_hashes(block),
                "statement": "choices and acquisition transcripts locked before any final-bank access; "
                             "no retuning afterwards"}
        lock_path = self._block_dir(block) / "lock.json"
        lock_sha = write_once_json(lock_path, lock)
        arms = ["a0"] + sorted({choices[m]["choice"] for m in METHODS} - {"a0"})
        if sensitivity and sensitivity["purchase"] and sensitivity["choice"]["choice"] not in arms:
            arms.append(sensitivity["choice"]["choice"])
        random.Random(schedule["final_order_key"]).shuffle(arms)
        final = {}
        for arm in arms:
            self._switch(f"final:{arm}")
            receipt = self.ensure_op(Op("final", arm, final_seed), block, lock=(lock_path, lock_sha))
            final[arm] = None if receipt is None else self.backend.evaluation(
                receipt, self.spec(Op("final", arm, final_seed), block, lock_sha256=lock_sha))
        return self._result(block, self._block_result(block, base, lock_sha, choices, transcripts, charges,
                                                      final, sensitivity, final_seed))

    def _evaluation(self, op: Op, block: int):
        """The verified evaluation of a complete operation (cached per receipt and per controller
        step: each policy pays its own reads, as a standalone run would), else None."""
        done = [r for r in self.receipts(op.op_id, block) if r["status"] == "complete"]
        if not done:
            return None
        key = (self._owner, block, op.op_id, done[0]["artifact_sha256"])
        if key not in self._evaluations:
            self._evaluations[key] = self.backend.evaluation(done[0], self.spec(op, block))
        return self._evaluations[key]

    def _choose(self, owned: set[Op], block: int, ties: Mapping[str, int]) -> dict:
        z0 = progression(self.config, self.data_config, block).at(0)
        changes = {g: [] for g in self.shape.edits}
        seeds = sorted({op.seed for op in owned if op.kind in ("full_from_short", "full_from_init")})
        for seed in seeds:
            a0_op = full_op("a0", seed, z0)
            a0 = self._evaluation(a0_op, block) if a0_op in owned else None
            if a0 is None:
                continue
            for g in self.shape.edits:
                op = full_op(g, seed, z0)
                if op in owned:
                    edit = self._evaluation(op, block)
                    if edit is not None:
                        changes[g].append(paired_change(edit, a0))
        return choose(changes, ties, self.constraints) | {"observations": changes}

    def _extra_purchase(self, block: int, transcript: dict, ranking: dict, owned: set[Op], prog, z0: int,
                        ties: Mapping[str, int]) -> dict | None:
        extra = next_purchase(transcript, ranking=[r["edit"] for r in ranking["ranking"]], quote=self.quote,
                              seed_at=prog.at, owned=owned, screen_seed=z0)
        if extra is None:
            return {"purchase": None, "choice": {"choice": None}, "note": "nothing left to buy"}
        for op in extra["ops"]:
            self.ensure_op(op, block)
        choice = self._choose(owned | set(extra["ops"]), block, ties)
        return {"purchase": {"phase": extra["phase"], "edit": extra["edit"], "seeds": extra["seeds"],
                             "ops": [op.op_id for op in extra["ops"]]},
                "extra_quote": float(extra["quote"]), "choice": choice,
                "note": "S- one-extra-purchase sensitivity: beyond the budget; not part of S-'s ledgers"}

    def _receipt_sha(self, op_id: str, block: int | None) -> list[str]:
        return [sha256_file(p / "receipt.json") for p in _attempts(self._op_dir(op_id, block))
                if (p / "receipt.json").exists()]

    def _block_receipt_hashes(self, block: int) -> dict:
        ops = self._block_dir(block) / "ops"
        return {p.name: self._receipt_sha(p.name, block) for p in sorted(ops.iterdir()) if p.is_dir()
                and not p.name.startswith("final-")}

    def _all_receipts(self, block: int) -> dict[str, list[dict]]:
        ops = self._block_dir(block) / "ops"
        return {p.name: self.receipts(p.name, block) for p in sorted(ops.iterdir()) if p.is_dir()} if ops.exists() else {}

    def _static_receipts(self) -> dict[str, list[dict]]:
        return {op.op_id: self.receipts(op.op_id, None) for op in STATIC_OPS}

    def _abort_costs(self, block: int, z0: int) -> dict:
        """Each policy's cost incurred up to the abort: its fixed-charge operations that were
        attempted (every attempt, failed ones included) and the overhead of the sessions it owns
        (``costs.session_allocation``: a session that ran only the other policy's work is not
        charged). A lower bound of a standalone run: the remaining cost is unobserved and never
        imputed. No final operation precedes an abort, so the incurred cost is also the incurred
        selection-plus-one-chosen-model cost. A provisional snapshot (``SNAPSHOT_NOTE``)."""
        self._switch("result")
        receipts, static, sessions = self._all_receipts(block), self._static_receipts(), self._session_records(block)
        incurred = {}
        for m in METHODS:
            planned = {"static": list(STATIC_OPS), "screen": [Op("screen", arm, z0) for arm in ("a0", *self.shape.edits)]}
            if m == "S+":
                planned["prerequisite"] = prerequisite_ops(self.shape, self.short, self.full, z0)
                planned["attribution"] = [Op("attribution", "", z0)]
            categories = {c: [op.op_id for op in ops if (static if c == "static" else receipts).get(op.op_id)]
                          for c, ops in planned.items()}
            quotes = {op.op_id: float(self.quote(op)) for ops in planned.values() for op in ops}
            scoped = policy_costs(block, categories, receipts, quotes, static, sessions, (), policy_owners(m, None))
            incurred[m] = {**scoped["actual"], "scope": ABORT_SCOPE}
        return {"contract": COST_CONTRACT, "snapshot": SNAPSHOT_NOTE, "incurred": incurred,
                "physical": block_physical(block, receipts, sessions),
                "setup_line_seconds": block_setup_seconds(receipts, sessions),
                "setup_measured": block_setup_measured(sessions),
                "note": "the block stopped after exhausted technical retries; costs after the abort are unobserved "
                        "and not imputed (walltime has no known bound)"}

    @staticmethod
    def _sensitivity_only_ops(sensitivity: dict | None, choices: Mapping, final_seed: int,
                              categories: Mapping[str, Mapping[str, list[str]]]) -> list[str]:
        """The operations run only for the S- one-extra-purchase sensitivity: its purchase's
        operations outside both policies' inventories, and its final deployment when its choice is
        no primary arm."""
        if not (sensitivity and sensitivity.get("purchase")):
            return []
        owned = {op_id for cats in categories.values() for ids in cats.values() for op_id in ids}
        ops = [op_id for op_id in sensitivity["purchase"]["ops"] if op_id not in owned]
        alt = sensitivity["choice"]["choice"]
        if alt not in {"a0", *(c["choice"] for c in choices.values())}:
            ops.append(Op("final", alt, final_seed).op_id)
        return ops

    def _block_result(self, block, base, lock_sha, choices, transcripts, charges, final, sensitivity,
                      final_seed) -> dict:
        self._switch("result")   # this computation and the write: in the session's end record only (the
        # owner does not change again before the end record, so every per-policy line below is final)
        receipts = self._all_receipts(block)
        static = self._static_receipts()
        sessions = self._session_records(block)
        quotes = {_op(key).op_id: float(self.quote(_op(key))) for m in METHODS
                  for p in transcripts[m]["purchases"] for key in p["op_keys"]}
        costs: dict = {"contract": COST_CONTRACT, "snapshot": SNAPSHOT_NOTE, "scopes": COST_SCOPES, "quoted": {},
                       "actual": {}, PRIMARY_COST_SCOPE: {}, "reference_and_sensitivity": {}}
        a0_final = Op("final", "a0", final_seed)
        categories, final_ops = {}, {}
        for m in METHODS:
            choice = choices[m]["choice"]
            deployed = Op("final", choice, final_seed)
            reference = [a0_final] if choice != "a0" else []
            final_ops[m] = [deployed, *reference]
            costs["quoted"][m] = quoted_ledger(self.config["budget"]["total_quote_seconds"], charges[m],
                                               transcripts[m], self.quote(deployed),
                                               sum((self.quote(op) for op in reference), Fraction(0)))
            categories[m] = {c["category"]: [o.op_id for o in c["ops"]] for c in charges[m] if c["ops"]}
            categories[m]["acquisition"] = [op_id for p in transcripts[m]["purchases"] for op_id in p["ops"]]
            categories[m]["final_deployment"] = [deployed.op_id]
            if reference:
                categories[m]["final_reference_a0"] = [a0_final.op_id]
        extra = self._sensitivity_only_ops(sensitivity, choices, final_seed, categories)
        for m in METHODS:
            scoped = policy_costs(block, categories[m], receipts, quotes | {
                op.op_id: float(self.quote(op)) for c in charges[m] for op in c["ops"]}
                | {op.op_id: float(self.quote(op)) for op in final_ops[m]}, static, sessions, extra,
                policy_owners(m, choices[m]["choice"]))
            for key, value in scoped.items():
                costs[key][m] = value
        owners = {"sensitivity"}
        if any(op_id.startswith("final-") for op_id in extra):   # the sensitivity's choice is no primary arm
            owners.add(f"final:{sensitivity['choice']['choice']}")
        costs["reference_and_sensitivity"]["sensitivity"] = _sensitivity_costs(extra, receipts, sessions, owners)
        costs["final_evaluation_stage_seconds"] = {
            arm: math.fsum(v for r in receipts.get(Op("final", arm, final_seed).op_id, [])
                           for k, v in (r.get("engine_stage_seconds") or {}).items() if k in EVALUATION_STAGES)
            for arm in sorted(final)}
        costs["note"] = ("actual: each policy's whole-research reconstruction, the sum of its two scopes; "
                         "final_deployment trains the chosen arm and evaluates it on the final bank and is charged in "
                         f"full to every policy that chose it; {PRIMARY_COST_SCOPE} leaves out final_reference_a0 "
                         "(reference research) and sessions identified as research-only or other-policy-only; "
                         "controller seconds are charged by owner (costs.COST_CONTRACT); "
                         "final_evaluation_stage_seconds are engine-internal stage sums, displayed and never "
                         "subtracted; development overhead is reported separately")
        costs["physical"] = block_physical(block, receipts, sessions)
        costs["setup_line_seconds"] = block_setup_seconds(receipts, sessions)
        costs["setup_measured"] = block_setup_measured(sessions)
        costs["development_overhead_seconds"] = self.config["overhead"]["development_seconds"]
        costs["actual_s_plus_minus_s_minus"] = (costs["actual"]["S+"]["total_seconds"]
                                                - costs["actual"]["S-"]["total_seconds"])
        costs[f"{PRIMARY_COST_SCOPE}_s_plus_minus_s_minus"] = (costs[PRIMARY_COST_SCOPE]["S+"]["seconds"]
                                                             - costs[PRIMARY_COST_SCOPE]["S-"]["seconds"])
        picks = {m: choices[m]["choice"] for m in METHODS}
        primary = {"a0", *picks.values()}
        status = "complete" if all(final[a] is not None for a in primary) else "final-incomplete"
        out = {**base, "status": status, "lock_sha256": lock_sha, "choices": picks,
               "final_missing": sorted(arm for arm, ev in final.items() if ev is None),
               "acquisition": {m: {"promoted": len(transcripts[m]["promoted"]),
                                   "purchases": len(transcripts[m]["purchases"]),
                                   "leftover": transcripts[m]["leftover"], "stop": transcripts[m]["stop"],
                                   "complete_paired_observations": {
                                       g: len(obs) for g, obs in choices[m]["observations"].items() if obs}}
                               for m in METHODS},
               "final": {arm: None if ev is None else ev.to_json() for arm, ev in sorted(final.items())},
               "endpoints": self._endpoints(final, picks), "endpoint_definitions": ENDPOINTS,
               "costs": costs}
        if sensitivity and sensitivity.get("purchase"):
            alt = sensitivity["choice"]["choice"]
            out["sensitivity"] = {"s_minus_one_extra_purchase": {
                "choice": alt, "extra_quote": sensitivity["extra_quote"],
                "endpoints": self._endpoints(final, {"S-": alt, "S+": picks["S+"]})}}
        return out

    @staticmethod
    def _endpoints(final: Mapping, choices: Mapping[str, str]) -> dict:
        """Every endpoint the completed final evaluations determine (see ``ENDPOINTS``)."""
        def contrast(a: str, b: str, measure: str) -> dict | None:
            if a == b:
                return identity_contrast(measure)
            if final.get(a) is None or final.get(b) is None:
                return None
            return rate_contrast(final[a], final[b], measure)

        def relative(arm: str) -> dict | None:
            if arm == "a0":
                return {**{key: identity_contrast(MEASURE_OF[key]) for key in CHANGES}, "diagnostics": None}
            if final.get(arm) is None or final.get("a0") is None:
                return None
            change = paired_change(final[arm], final["a0"])
            return {**{key: change[key] for key in CHANGES}, "diagnostics": change["diagnostics"]}

        minus, plus = choices["S-"], choices["S+"]
        return {"identical_choices": minus == plus, "Y": contrast(minus, plus, "safety"),
                "relative_to_a0": {m: relative(choices[m]) for m in METHODS},
                "utility_contrast": contrast(plus, minus, "utility"),
                "refusal_contrast": contrast(minus, plus, "refusal")}


def _verify_block(block_dir: Path, specs: Mapping[Path, dict | None], study: dict | None) -> list[str]:
    """The lock rules of one block: every final-bank operation (and a complete or
    final-incomplete result) needs the block's valid lock, pinned by hash, authorizing its arm
    and seed; the lock covers exactly the block's other operations with their receipt hashes."""
    problems: list[str] = []
    try:
        block = int(block_dir.name)
    except ValueError:
        return [f"{block_dir}: not a block folder"]
    ops = {p.name: specs.get(p) for p in sorted((block_dir / "ops").glob("*")) if p.is_dir()}
    finals = {name: spec for name, spec in ops.items()
              if name.startswith("final-") or (spec is not None and (spec.get("kind") == "final"
                                                                     or spec.get("bank") == "hidden"))}
    result = None
    if (block_dir / "result.json").exists():
        try:
            result = read_canonical(block_dir / "result.json")
        except VerificationError as exc:
            problems.append(f"{block_dir}: result unreadable: {exc}")
    lock_path = block_dir / "lock.json"
    lock = lock_sha = authorization = None
    if lock_path.exists():
        try:
            lock_sha, lock = sha256_file(lock_path), read_canonical(lock_path)
            authorization = lock_authorization(lock)
            if authorization["block"] != block:
                problems.append(f"{lock_path}: lock of block {authorization['block']}")
            if study is not None and lock.get("pins") != study.get("pins"):
                problems.append(f"{lock_path}: the lock pins differ from the study's")
        except (VerificationError, KeyError, TypeError, AttributeError) as exc:
            problems.append(f"{lock_path}: invalid choice lock: {exc}")
            lock = authorization = None
    elif finals or (result is not None and result.get("status") in ("complete", "final-incomplete")):
        problems.append(f"{block_dir}: final-bank operations or a final result without a choice lock")
    if lock is not None:
        recorded = lock.get("receipts") if isinstance(lock.get("receipts"), dict) else {}
        selection = set(ops) - set(finals)
        if set(recorded) != selection:
            problems.append(f"{block_dir}: the lock does not cover exactly the selection operations "
                            f"(difference {sorted(set(recorded) ^ selection)})")
        for op_id in sorted(selection & set(recorded)):
            actual = [sha256_file(p / "receipt.json") for p in _attempts(block_dir / "ops" / op_id)
                      if (p / "receipt.json").exists()]
            if actual != recorded[op_id]:
                problems.append(f"{block_dir}: receipts of {op_id} differ from the lock")
    for name, spec in sorted(finals.items()):
        if spec is None:
            continue  # already reported as unreadable
        try:
            check_lock(spec, {"lock": str(lock_path)} if lock_path.exists() else {})
        except (LockError, PolicyError, VerificationError) as exc:
            problems.append(f"{block_dir / 'ops' / name}: {exc}")
    if result is not None:
        status = result.get("status")
        if status in ("complete", "final-incomplete"):
            if lock_sha is None or result.get("lock_sha256") != lock_sha:
                problems.append(f"{block_dir}: the result does not pin the block's lock")
            elif authorization is not None and result.get("choices") != authorization["choices"]:
                problems.append(f"{block_dir}: the result's choices differ from the lock's")
        elif status == "aborted" and (lock_path.exists() or finals):
            problems.append(f"{block_dir}: an aborted block holds a lock or final-bank operations")
    return problems


def _check_op(op_dir: Path, config_sha: str | None, backend, unclosed_ok: bool) -> tuple[dict | None, list[str], int]:
    """(spec or None, problems, complete artifacts verified) of one operation folder: its spec pins
    the configuration; every receipt is canonical, belongs to its operation and attempt and pins the
    spec's hash; with a backend every complete artifact verifies. An attempt without an after-call
    receipt is a problem unless ``unclosed_ok`` (an in-progress study, read as lower bounds)."""
    try:
        spec = read_canonical(op_dir / "spec.json")
        spec_sha = sha256_file(op_dir / "spec.json")
        if spec.get("op_id") != op_dir.name:
            raise VerificationError(f"spec of operation {spec.get('op_id')}")
    except (OSError, VerificationError) as exc:
        return None, [f"{op_dir}: spec unreadable: {exc}"], 0
    problems: list[str] = []
    checked = 0
    if spec.get("config_sha256") != config_sha:
        problems.append(f"{op_dir}: the operation pins another configuration than the study")
    for attempt_dir in _attempts(op_dir):
        path = attempt_dir / "receipt.json"
        if not path.exists():
            if not unclosed_ok:
                problems.append(f"{attempt_dir}: no after-call receipt (interrupted attempt not yet closed)")
            continue
        try:
            receipt = read_canonical(path)
            if receipt["op_id"] != spec["op_id"] or receipt["attempt"] != int(attempt_dir.name[8:]):
                raise VerificationError("receipt of another operation or attempt")
            if receipt["spec_sha256"] != spec_sha:
                raise VerificationError("receipt pins another spec")
            if receipt["status"] == "complete" and backend is not None:
                backend.verify(receipt, spec)
                checked += 1
        except (OSError, KeyError, VerificationError, PolicyError, ValueError) as exc:
            problems.append(f"{attempt_dir}: {exc}")
    return spec, problems, checked


def verify_study(root: str | Path, backend, *, unclosed_ok: bool = False) -> dict:
    """Read-only verification of a study tree (possibly archived elsewhere; the backend resolves
    recorded artifact paths through its read-only path map): every spec pins the study's
    configuration; every receipt is canonical, belongs to its operation and attempt and pins its
    spec's hash; every complete artifact verifies against its receipt and spec; and per block the
    lock rules of ``_verify_block``. Nothing is written, closed or repaired. Without a backend the
    artifacts are not verified (``artifacts_verified`` false; never ``complete``): the analysis
    entrypoint's check. ``unclosed_ok`` accepts attempts interrupted without an after-call receipt
    (an in-progress study read as lower bounds) instead of reporting them."""
    root = Path(root)
    problems: list[str] = []
    checked = 0
    study = None
    try:
        study = read_canonical(root / "study.json")
        if study.get("kind") != STUDY_KIND or "config_sha256" not in study.get("pins", {}):
            raise VerificationError("not a study record")
    except (OSError, VerificationError, AttributeError, TypeError) as exc:
        problems.append(f"{root}: study.json unreadable or malformed: {exc}")
        study = None
    config_sha = study["pins"]["config_sha256"] if study is not None else None
    specs: dict[Path, dict | None] = {}
    op_dirs = sorted((root / "static").glob("*")) + sorted((root / "blocks").glob("*/ops/*"))
    for op_dir in op_dirs:
        if not op_dir.is_dir():
            continue
        specs[op_dir], op_problems, op_checked = _check_op(op_dir, config_sha, backend, unclosed_ok)
        problems.extend(op_problems)
        checked += op_checked
    for block_dir in sorted(p for p in (root / "blocks").glob("*") if p.is_dir()):
        problems.extend(_verify_block(block_dir, specs, study))
    return {"root": str(root), "complete_artifacts_verified": checked, "artifacts_verified": backend is not None,
            "problems": problems, "complete": not problems and backend is not None}


def verified_result(root: str | Path, block: int, *, config_sha256: str, final_seed: int, pins: Mapping) -> dict:
    """A block's existing result, returned only when the block's specs and receipts pin this
    configuration, the lock rules of ``_verify_block`` hold (the lock exists, the result pins its
    hash and carries its choices, its pins are the study's and it authorizes every final-bank
    operation) and the result and lock name this block, configuration, outcome definition and
    final seed. Read only: artifacts are not re-verified (``verify_study`` does that), nothing reruns
    and nothing is written. Raises VerificationError otherwise."""
    block_dir = Path(root) / "blocks" / str(block)
    problems: list[str] = []
    specs: dict[Path, dict | None] = {}
    for op_dir in sorted((block_dir / "ops").glob("*")):
        if op_dir.is_dir():
            specs[op_dir], op_problems, _ = _check_op(op_dir, config_sha256, None, unclosed_ok=False)
            problems.extend(op_problems)
    problems.extend(_verify_block(block_dir, specs, {"pins": dict(pins)}))
    try:
        result = read_canonical(block_dir / "result.json")
    except (OSError, VerificationError) as exc:
        raise VerificationError(f"block {block}: the result is unreadable: {exc}") from None
    expected = {"kind": RESULT_KIND, "block": block, "config_sha256": config_sha256, "outcome_definition": OUTCOME_PIN}
    wrong = sorted(key for key, value in expected.items() if result.get(key) != value)
    if wrong:
        problems.append(f"{block_dir}: the result names another {', '.join(wrong)}")
    if not isinstance(result.get("seeds"), dict) or result["seeds"].get("final") != final_seed:
        problems.append(f"{block_dir}: the result's final seed is not the configured {final_seed}")
    status = result.get("status")
    if status in ("complete", "final-incomplete"):
        try:
            if lock_authorization(read_canonical(block_dir / "lock.json"))["final_seed"] != final_seed:
                problems.append(f"{block_dir}: the lock authorizes another final seed than the configured {final_seed}")
        except (OSError, VerificationError, KeyError, TypeError, AttributeError):
            pass   # a missing or malformed lock is already a problem of the lock rules
    elif status != "aborted":
        problems.append(f"{block_dir}: unknown result status {status!r}")
    if problems:
        raise VerificationError(f"block {block}: the existing result does not verify, so nothing is returned: "
                                f"{'; '.join(problems[:5])}")
    return result


def _sensitivity_costs(extra: Sequence[str], receipts: Mapping[str, Sequence[dict]], sessions: Sequence[dict],
                       owners: set[str]) -> dict:
    """The S- one-extra-purchase sensitivity, in neither policy's ledger: its own operations (net of
    engine setup stages, which stay with their sessions) and its controller seconds. A lower bound
    while any session of the block lacks its final controller seconds (``costs.controller_unknown``)."""
    parts = [attempt_seconds(r, net_of_setup=True) for op_id in extra for r in receipts.get(op_id, [])]
    controller = [v for s in sessions for o, v in (s.get("controller_seconds") or {}).items() if o in owners]
    reasons = []
    if not all(t for _, t in parts):
        reasons.append("an attempt lacks its after-call time (its lower bound is kept)")
    reasons.extend(dict.fromkeys(why for why in map(controller_unknown, sessions) if why))
    operations = math.fsum(s for s, _ in parts)
    return {"operations": list(extra), "seconds": math.fsum([operations, *controller]),
            "operation_seconds": operations, "controller_seconds": math.fsum(controller),
            "timing_complete": not reasons, "incomplete_because": reasons,
            "note": "operations and controller seconds run only for the S- one-extra-purchase sensitivity: in "
                    "neither policy's ledger; net of engine setup stages, which stay with their sessions"}


def _recorded_categories(plans: Mapping[str, dict], lock: dict | None, receipts: Mapping[str, Sequence[dict]],
                         static: Mapping[str, Sequence[dict]], *, require_attempts: bool = False
                         ) -> tuple[dict, dict, list[str], str]:
    """(per policy the categories of its attempted operations, the locked choices, the
    sensitivity-only operations, the stage) recoverable from a block's own records. With both
    acquisition plans written: their fixed charges and purchases, and with the lock each chosen
    final and reference a0 final. Before the plans the controller has run only the screen (both
    policies) and S+'s prerequisites and attribution, so every other operation is S+'s. A started
    block leaves out the operations not yet attempted; ``require_attempts`` (a block with a result,
    whose every charged operation was attempted) refuses a charged operation without a counted
    attempt instead of dropping it."""
    attempted = set(receipts)
    if all(m in plans for m in METHODS):
        inventory = {m: {c["category"]: list(c["ops"]) for c in plans[m]["charges"] if c["ops"]} for m in METHODS}
        for m in METHODS:
            inventory[m]["acquisition"] = [op_id for p in plans[m]["transcript"]["purchases"] for op_id in p["ops"]]
        stage = "acquisition (both plans written)"
    else:
        static_ids = [op.op_id for op in STATIC_OPS]
        screen = sorted(op_id for op_id in attempted if op_id.startswith("screen-"))
        inventory = {"S-": {"static": static_ids, "screen": screen},
                     "S+": {"static": static_ids, "screen": screen,
                            "prerequisite_and_attribution": sorted(attempted - set(screen))}}
        stage = "screen or S+ prerequisites (no plan written)"
    choices: dict[str, str] = {}
    extra: list[str] = []
    if lock is not None:
        authorization = lock_authorization(lock)
        seed = authorization["final_seed"]
        for m in METHODS:
            choices[m] = authorization["choices"][m]
            inventory[m]["final_deployment"] = [Op("final", choices[m], seed).op_id]
            if choices[m] != "a0":
                inventory[m]["final_reference_a0"] = [Op("final", "a0", seed).op_id]
        extra = Study._sensitivity_only_ops(lock.get("sensitivity"), {m: {"choice": c} for m, c in choices.items()},
                                            seed, inventory)
        stage = "final deployment (choices locked)"
    elif all(m in plans for m in METHODS):   # the sensitivity purchase runs before the lock
        owned = {op_id for cats in inventory.values() for ids in cats.values() for op_id in ids}
        extra = sorted(attempted - owned)
    categories = {m: {c: [op_id for op_id in ids if (static.get(op_id) if c == "static" else op_id in attempted)]
                      for c, ids in inventory[m].items()} for m in METHODS}
    if require_attempts:
        charged = {op_id for m in METHODS for ids in inventory[m].values() for op_id in ids} | set(extra)
        missing = sorted(charged - {op_id for m in METHODS for ids in categories[m].values() for op_id in ids}
                         - attempted)
        if missing:
            raise VerificationError(f"charged operations without a counted attempt beside a result: {missing[:5]}")
    return categories, choices, extra, stage


def _durable_costs(root: Path, block: int, *, require_attempts: bool) -> dict:
    """A block's costs recomputed read-only from its own durable records: every counted attempt (one
    interrupted without a receipt at its lower bound; nothing is closed or written), its session
    start and end records (a session without its end record: controller seconds unknown), and per
    policy the ownership recorded in its plans and lock (``_recorded_categories``)."""
    block_dir = root / "blocks" / str(block)
    ops = block_dir / "ops"
    receipts = {p.name: _read_receipts(p) for p in sorted(ops.iterdir()) if p.is_dir()} if ops.is_dir() else {}
    receipts = {op_id: attempts for op_id, attempts in receipts.items() if attempts}
    static = {op.op_id: _read_receipts(root / "static" / op.op_id) for op in STATIC_OPS}
    sessions = _read_sessions(block_dir)
    plans = {m: read_canonical(block_dir / f"plan-{m}.json") for m in METHODS if (block_dir / f"plan-{m}.json").exists()}
    lock = read_canonical(block_dir / "lock.json") if (block_dir / "lock.json").exists() else None
    categories, choices, extra, stage = _recorded_categories(plans, lock, receipts, static,
                                                             require_attempts=require_attempts)
    scoped = {m: policy_costs(block, categories[m], receipts, {}, static, sessions, extra,
                              policy_owners(m, choices.get(m))) for m in METHODS}
    owners = {"sensitivity"}
    if lock is not None and any(op_id.startswith("final-") for op_id in extra):
        owners.add(f"final:{lock['sensitivity']['choice']['choice']}")
    return {"stage": stage, "choices_locked": lock is not None, "policies": scoped, "sessions": sessions,
            "sensitivity": _sensitivity_costs([op_id for op_id in extra if op_id in receipts], receipts, sessions,
                                              owners),
            "physical": block_physical(block, receipts, sessions),
            "setup_line_seconds": block_setup_seconds(receipts, sessions),
            "setup_measured": block_setup_measured(sessions)}


def started_block_costs(root: str | Path, block: int) -> dict:
    """Read-only known incurred costs of a started block without a result: every counted attempt
    (one interrupted without a receipt at its lower bound; nothing is closed or written), the
    overhead of its recorded sessions and, per policy, the ownership recoverable from its own plans
    and lock (``_recorded_categories``). Lower bounds: the remaining cost is unobserved and never
    imputed, and the block stays outcome-unknown (no result, no new draw)."""
    root = Path(root)
    if (root / "blocks" / str(block) / "result.json").exists():
        raise PolicyError(f"block {block} has a result; its recorded costs are recorded_block_costs")
    core = _durable_costs(root, block, require_attempts=False)
    scope = ("incurred so far by a started block without a result: lower bounds of its eventual cost; the remaining "
             "cost is unobserved and never imputed; the block stays outcome-unknown")
    return {"contract": COST_CONTRACT, "block": block, "status": "started-without-result", "stage": core["stage"],
            "choices_locked": core["choices_locked"],
            "incurred": {m: {**core["policies"][m], "scope": scope} for m in METHODS},
            "sensitivity": core["sensitivity"], "physical": core["physical"],
            "setup_line_seconds": core["setup_line_seconds"], "setup_measured": core["setup_measured"], "scope": scope}


def _snapshot_check(block: int, snapshot: Mapping, out: Mapping, sessions: Sequence[dict]) -> dict:
    """How the recorded costs relate to the result's provisional snapshot. Once the session that
    wrote the result (the block's last: no session follows a result) has its end record, the
    snapshot's per-policy seconds must be reproduced exactly (the owner did not change between the
    snapshot and the end record; the same floats, exactly rounded sums) and the physical seconds
    can only have grown, by the result's own computation and write. A difference means a durable
    record changed after the result: refused. Without that end record nothing is compared: the
    recorded scopes charged that session are lower bounds anyway."""
    last = max(sessions, key=lambda s: s["session"], default=None)
    if last is None or last["controller_seconds"] is None:
        return {"compared": False,
                "reason": "the session that wrote the result has no end record: the recorded physical seconds and "
                          "every scope charged that session are lower bounds, below the snapshot by the controller "
                          "seconds only that session's memory held"}
    try:
        if out["result_status"] == "aborted":
            pairs = [(f"incurred {m}", snapshot["incurred"][m]["total_seconds"], out["incurred"][m]["total_seconds"])
                     for m in METHODS]
        else:
            fields = (("actual", "total_seconds"), (PRIMARY_COST_SCOPE, "seconds"),
                      ("reference_and_sensitivity", "seconds"))
            pairs = [(f"{key} {m}", snapshot[key][m][field], out[key][m][field])
                     for key, field in fields for m in METHODS]
        was, now = snapshot["physical"], out["physical"]
        pairs += [(f"physical {key}", was[key], now[key]) for key in ("attempt_seconds", "session_start_seconds")]
        differing = [name for name, old, new in pairs if old != new]
        if now["seconds"] < was["seconds"]:
            differing.append("physical seconds (below the snapshot)")
    except (KeyError, TypeError) as exc:
        raise VerificationError(f"block {block}: the result's cost snapshot is malformed ({exc!r})") from None
    if differing:
        raise VerificationError(f"block {block}: its durable records do not reproduce the result's cost snapshot "
                                f"({', '.join(differing[:6])}): a receipt, session record, plan or lock changed after "
                                "the result was written")
    return {"compared": True, "per_policy_seconds": "equal to the result's snapshot, exactly",
            "result_segment_seconds": last["controller_seconds"].get("result", 0.0),
            "physical_seconds_beyond_snapshot": now["seconds"] - was["seconds"]}


def recorded_block_costs(root: str | Path, block: int, result: Mapping | None = None) -> dict:
    """The authoritative costs of a block WITH a result, recomputed read-only from its durable
    records (``_durable_costs``; never from the result's provisional snapshot, whose immutable
    quoted ledger and overrun list stay in the result): shaped like the result's cost object
    (``actual``, the two scopes and the sensitivity, or ``incurred`` for an abort, and ``physical``),
    each with its completeness. The end record of the session that wrote the result adds what the
    snapshot could not hold; a session without its end record (a process killed after the result
    was written, or earlier) leaves the physical seconds and every scope charged that session lower
    bounds, never a point cost. ``result``: the block's verified result (read from the tree when
    None). Raises VerificationError when the records do not fit the result (``_snapshot_check``, a
    charged operation without a counted attempt, a decided result without its lock)."""
    root = Path(root)
    if result is None:
        path = root / "blocks" / str(block) / "result.json"
        if not path.exists():
            raise PolicyError(f"block {block} has no result; its incurred costs are started_block_costs")
        result = read_canonical(path)
    status, snapshot = result.get("status"), result.get("costs") or {}
    if snapshot.get("contract") != COST_CONTRACT:
        raise VerificationError(f"block {block}: the result records its costs under another contract than "
                                f"{COST_CONTRACT!r}")
    core = _durable_costs(root, block, require_attempts=True)
    if status not in ("complete", "final-incomplete", "aborted") or core["choices_locked"] != (status != "aborted"):
        raise VerificationError(f"block {block}: a result of status {status!r} does not fit its records "
                                f"(choices locked: {core['choices_locked']})")
    scoped, sessions = core["policies"], core["sessions"]
    out = {"contract": COST_CONTRACT, "block": block, "result_status": status, "source": RECORDED_SOURCE,
           "stage": core["stage"], "physical": core["physical"], "setup_line_seconds": core["setup_line_seconds"],
           "setup_measured": core["setup_measured"], "boundary": PHYSICAL_BOUNDARY,
           "sessions": {"recorded": [s["session"] for s in sessions],
                        "without_end_record": [s["session"] for s in sessions if s["controller_seconds"] is None]}}
    if status == "aborted":
        out["incurred"] = {m: {**scoped[m]["actual"], "scope": ABORT_SCOPE} for m in METHODS}
    else:
        for key in ("actual", PRIMARY_COST_SCOPE, "reference_and_sensitivity"):
            out[key] = {m: scoped[m][key] for m in METHODS}
        out["reference_and_sensitivity"]["sensitivity"] = core["sensitivity"]
        out["actual_s_plus_minus_s_minus"] = out["actual"]["S+"]["total_seconds"] - out["actual"]["S-"]["total_seconds"]
        out[f"{PRIMARY_COST_SCOPE}_s_plus_minus_s_minus"] = (out[PRIMARY_COST_SCOPE]["S+"]["seconds"]
                                                           - out[PRIMARY_COST_SCOPE]["S-"]["seconds"])
    out["snapshot"] = _snapshot_check(block, snapshot, out, sessions)
    return out


def study_evidence(root: str | Path, config: dict) -> dict:
    """The analysis entrypoint's read-only view of a study tree (nothing is written, closed or
    repaired; artifacts are not re-verified: ``verify-study`` with the engine does that). The tree
    must be this configuration's study and pass ``verify_study`` without a backend, attempts
    interrupted without a receipt accepted as lower bounds; every result must pass
    ``verified_result`` (a removed or changed lock refuses) and contributes ``recorded_block_costs``
    (its authoritative costs from the durable records, with a missing session end record as lower
    bounds; never the result's provisional snapshot); every started block without a result
    contributes ``started_block_costs``; the study-level static work is timed once. Raises
    VerificationError, refusing the analysis, on any problem."""
    root = Path(root)
    digest = config_sha256(config)
    try:
        study = read_canonical(root / "study.json")
    except (OSError, VerificationError) as exc:
        raise VerificationError(f"{root}: no readable study record: {exc}") from None
    if not (isinstance(study, dict) and study.get("kind") == STUDY_KIND and isinstance(study.get("pins"), dict)
            and study["pins"].get("config_sha256") == digest):
        raise VerificationError(f"{root} is not a study of this configuration")
    problems = verify_study(root, None, unclosed_ok=True)["problems"]
    if problems:
        raise VerificationError(f"{root} does not verify, so it is not analyzed ({len(problems)} problems): "
                                f"{'; '.join(problems[:5])}")
    results, started, recorded = [], {}, {}
    for block_dir in sorted(p for p in (root / "blocks").glob("*") if p.is_dir()):
        if not block_dir.name.isdigit() or not 0 <= int(block_dir.name) < config["blocks"]["count"]:
            raise VerificationError(f"{block_dir}: not a configured block")
        block = int(block_dir.name)
        if (block_dir / "result.json").exists():
            results.append(verified_result(root, block, config_sha256=digest, pins=study["pins"],
                                           final_seed=config["blocks"]["list"][block]["final_seed"]))
            recorded[block] = recorded_block_costs(root, block, results[-1])
        else:
            started[block] = started_block_costs(root, block)
    static = {op.op_id: _read_receipts(root / "static" / op.op_id) for op in STATIC_OPS}
    seconds, timed = physical_seconds(static)
    return {"results": results, "started": started, "recorded": recorded,
            "static": {"seconds": seconds, "timing_complete": timed,
                       "incomplete_because": [] if timed else ["a static attempt lacks its after-call time (its "
                                                               "lower bound is kept)"]},
            "verification": "records, lock rules and result identities verified read-only; artifacts not "
                            "re-verified (verify-study)"}
