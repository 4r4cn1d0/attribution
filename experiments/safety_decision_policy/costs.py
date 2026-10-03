"""Quotes, fixed charges, the budget feasibility check and the two cost ledgers (stdlib only).

**Quotes** control acquisition. A quote is a frozen linear tariff of pre-run work counts only
(never an outcome or a measured time), in exact rational arithmetic so that budget comparisons
do not drift:

| operation | quote |
|---|---|
| screen (init -> short, evaluate) | call_overhead.screen + train_per_example * examples(short) + evaluation.selection |
| full_from_short (continue short -> full, evaluate) | call_overhead + train_per_example * (examples(full) - examples(short)) + evaluation.selection |
| full_from_init (init -> full, evaluate) | call_overhead + train_per_example * examples(full) + evaluation.selection |
| extend (a0 full -> last attribution checkpoint, no evaluation) | call_overhead + train_per_example * (examples(last) - examples(full)) |
| attribution | call_overhead + attribution_per_gradient_pass * gradient passes |
| final (init -> full, final evaluation) | call_overhead + train_per_example * examples(full) + evaluation.final |
| score_groups | call_overhead + score_groups_per_row * member rows |
| export_view, relevance | call_overhead |
| cold setup (per policy per block) | cold_setup |

``examples(c)`` is the arm's cumulative examples at checkpoint c from the engine's offline plan
(seed-independent; removal shortens every epoch). Continuation semantics: a continuation is
charged only its own segment plus its own call. Call overheads are where job setup, dependency
verification, state saving and completion hashing are priced; cold setup prices the session's
asset loading, corpus tokenization and memory preflight.

**Fixed charges** per policy and block, before any acquisition: cold setup, the static features
(score-groups, view export, relevance table), the whole screen (a0 and every edit at z0), the
final reserve (the most expensive edit's final deployment plus a0's) and, for S+ only, the
attribution prerequisites (a0's full continuation at z0, plus an extension when an attribution
checkpoint lies beyond the full checkpoint) and the attribution passes. Physically shared work
is charged in BOTH policies' counterfactual ledgers; no artifact is free.

**Actual ledger**: reconstructed per policy from the external after-call receipts of the
physical operations in its own inventory (every attempt, failed ones included), with the
engine's setup stages (asset loading, tokenization, memory preflight) moved from the operation
that recorded them to its session's overhead, which is charged to the policies that own the
session (below). This is an ESTIMATE of each policy's counterfactual standalone cost from shared
executed operations, not two directly observed isolated invoices; the provider's billing record
stays separate and authoritative.

**Cost scopes** (``COST_SCOPES``; the 2 October 2026 cost-scope amendment). ``policy_costs`` splits a
policy's whole-research ledger into the selection-plus-one-chosen-model subtotal
(``PRIMARY_COST_SCOPE``) and the additional reference research, which add up to it. The
chosen-model final is charged in full to every policy that chose it, also when two policies share
one physical a0 run.

**Session overhead** (``COST_CONTRACT``, since v2 of 3 October 2026; ``session_allocation``). A session is
one ``run_block`` call; every attempt receipt carries its tag. Its overhead is its start record
(process start to the block's start), the engine setup stages recorded inside its attempts and
its controller seconds outside attempts by owner (the session's end record): ``common`` (static,
screen, lock), ``S-`` and ``S+`` (each policy's prerequisites, scores, ranking, plan, purchases and
choice), ``final:<arm>``, ``sensitivity``, and two owners charged to no policy: ``reuse`` (a second
verification of an artifact this session already produced) and ``result`` (the block result's own
computation). The engine loads each asset once per process, so a session's overhead is shared
whenever it ran work of the policy's scope. Only a session in a fresh process that no later
session of the block shared, and that ran none of the scope's operations, leaves the scope: as
the policy's research when it ran the policy's reference or sensitivity work, otherwise as
``other_policy`` overhead, which is in neither of the policy's scopes (each physical second stays
once in ``block_physical``). Nothing leaves any scope when an attempt or a session record cannot
be attributed. Within the other sessions, controller seconds go to their owner's scope.

**Completeness** is computed per scope with its reasons, never zero-filled: an included attempt
without an after-call time, a block whose setup was not measured (no session started a fresh
process), a session charged to the scope without its end record (a killed process), attempts
outside the recorded sessions, and a timed attempt outside the scope without its engine setup
record (an exception: its time may hold setup that later work of the scope in the same session
reused) make that scope a lower bound. Physical completeness is separate: a fully timed exception
leaves the physical seconds complete and only the reconstruction incomplete.

**Authoritative accounting** (``COST_CONTRACT`` v3, 3 October 2026). The economic accounting of a
block is recomputed, read only, from its durable records: every counted attempt receipt, the session
start and end records, the plans and the lock (``controller.recorded_block_costs``, used by the
analysis entrypoint). The cost object inside a block result is a PROVISIONAL snapshot: the result is
written inside a session, before that session's end record exists, so the snapshot holds the
session's controller seconds closed so far and marks the session ``open``. An open session counts
for completeness exactly like a session without its end record (its own reason), so a snapshot is
flagged wherever the recomputation would be if the end record were never written, and neither a
snapshot nor a block whose session lost its end record yields a complete physical total or a
complete scope charged that session. The scientific result is never rewritten.

**Logging boundary** (``PHYSICAL_BOUNDARY``). Controller-timed seconds cover, per session, the
interval from the process start (the start record's ``monotonic_start``; zero-length in a shared
process) to the final clock read of the session (the end record's ``monotonic_end``): the start
record, the attempts (their receipts) and the owner segments (the end record) tile it, every second
once, the block result's own computation and write included (owner ``result``). A record cannot
time its own write, so what follows that clock read is outside every controller-timed total by
construction and is covered only by external process or provider records.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations
from typing import Callable, Mapping, Sequence

from .common import PolicyError
from .policy import Op, full_op

__all__ = ["Shape", "shape_from_plan", "make_quoter", "prerequisite_ops", "attribution_state_ops",
           "fixed_charges", "reserve_quote", "feasibility", "quoted_ledger", "actual_ledger",
           "attempt_seconds", "engine_setup_seconds", "block_setup_seconds", "block_setup_measured",
           "physical_seconds", "block_physical", "session_allocation", "policy_costs", "policy_owners",
           "SETUP_STAGES", "STATIC_OPS", "OP_KINDS", "REFERENCE_CATEGORIES", "PRIMARY_COST_SCOPE", "COST_SCOPES",
           "COST_CONTRACT", "UNCHARGED_OWNERS", "PHYSICAL_BOUNDARY", "controller_unknown"]

SETUP_STAGES = ("load_policy", "load_guard", "load_secondary_toxicity", "tokenize", "memory_preflight")
STATIC_OPS = (Op("score_groups", "", -1), Op("export_view", "", -1), Op("relevance", "", -1))
OP_KINDS = ("screen", "full_from_short", "full_from_init", "extend", "attribution", "final",
            "score_groups", "export_view", "relevance")
REFERENCE_CATEGORIES = ("final_reference_a0",)
PRIMARY_COST_SCOPE = "selection_plus_chosen_model"
COST_CONTRACT = ("stage-B block costs v3 (3 October 2026): session overhead (start record, engine setup stages, "
                 "controller seconds by owner from the session end record) charged by session and owner, sessions "
                 "that ran only other-policy work outside the policy's scopes, completeness and reasons per scope "
                 "and for the physical seconds; the authoritative accounting is recomputed from the durable records "
                 "(attempt receipts, session start and end records, plans, lock), the cost object inside a block "
                 "result is a provisional snapshot taken before its session's end record, and a session without its "
                 "end record leaves the physical seconds and every scope charged that session lower bounds; "
                 "controller-timed seconds run from each process start to its session's final clock read (the end "
                 "record's own write and everything after it are outside, by construction)")
PHYSICAL_BOUNDARY = (
    "controller-timed seconds: per session, from the process start (the start record's monotonic_start; zero-length "
    "when the process is shared) to the session's final clock read (the end record's monotonic_end); the start "
    "record, the attempts (their receipts) and the controller segments by owner (the end record) tile that interval, "
    "every second once, the block result's computation and write included (owner 'result'). Outside every "
    "controller-timed total, by construction: interpreter start-up before the process start mark; after the final "
    "clock read, assembling and writing the end record itself, returning, releasing the study lock and process exit "
    "(a record cannot time its own write); for a killed process everything after its last durable record (its "
    "controller seconds are unknown and the scopes charged that session are lower bounds); in a shared process the "
    "gap between one session's end and the next session's start; and a re-entry that only returns an existing "
    "result (no session). Only external process or provider records cover these; provider billing stays separate "
    "and authoritative")
UNCHARGED_OWNERS = ("reuse", "result")   # controller seconds in the physical total only
COST_SCOPES = {
    PRIMARY_COST_SCOPE: (
        "per policy, selection plus ONE freshly trained and audited chosen model: static features, the screen, S+ "
        "prerequisites and attribution, acquisition, every failed attempt and retry, the full chosen-model final "
        "operation (training and its frozen evaluation suite, charged in full to each policy also when the choice is "
        "a0 and the run is physically shared), the overhead of every session that ran any of these operations (or "
        "none at all) and the common, own-method and chosen-final controller seconds; excludes the extra reference a0 "
        "final of an edit choice and sessions identifiable from receipts as research-only or other-policy-only; not an "
        "exact training-only deployment cost"),
    "reference_and_sensitivity": (
        "additional research: per policy the extra reference a0 final when it chose an edit, its controller seconds, "
        "and the overhead of sessions that ran its research work and none of its selection-plus-chosen-model work; "
        "per block the S- one-extra-purchase sensitivity operations and controller seconds (in neither policy's "
        "ledger); the final operations' engine evaluation-stage sums are displayed, never subtracted, and need not "
        "partition the external timer"),
    "research_total": (
        "total research expenditure: per policy the whole-research reconstruction (the sum of the two scopes above: "
        "every operation it uses, the extra reference a0 final included, never the overhead of sessions that ran only "
        "the other policy's work), each artifact paid once per hypothetical policy; physically every counted attempt, "
        "session start record and measured controller second of the block once (block_physical; the result's own "
        "computation and write are in its session end record only, never in the result's snapshot); study-level "
        "static work and development/tuning are added "
        "in the analysis, provider billing stays separate; per-policy costs are counterfactual reconstructions, not "
        "invoices"),
}
_UNMEASURED = "the block's setup was not measured (no session started a fresh process; a shared process reused loads)"
_UNTIMED = "an included attempt lacks its after-call time (its lower bound is kept)"
_UNKNOWN_CONTROLLER = ("a session charged here ended without its end record (a killed process): its controller "
                       "seconds are unknown")
_OPEN_SESSION = ("a session charged here was still running when this snapshot was taken (its end record did not "
                 "exist yet): its controller seconds closed so far are counted, the rest is unknown here and is in "
                 "the session's end record (the accounting recomputed from the durable records holds it)")
_UNATTRIBUTED = ("an attempt or session record cannot be attributed to this block's recorded sessions: no session "
                 "overhead is excluded and that session's controller seconds are unknown")
_HIDDEN = ("a timed attempt outside this scope has no engine setup record (an exception): its time may hold setup "
           "that later work of this scope in the same session reused")


@dataclass(frozen=True)
class Shape:
    """Pre-run work counts of one split (no outcome, no measured time)."""

    checkpoints: tuple[str, ...]
    examples: Mapping[str, Mapping[str, int]]
    attribution_checkpoints: tuple[str, ...]
    attribution_passes: int
    score_rows: int
    edits: tuple[str, ...]

    def index(self, checkpoint: str) -> int:
        return self.checkpoints.index(checkpoint)

    def last_attribution(self) -> str:
        return max(self.attribution_checkpoints, key=self.index)


def shape_from_plan(plan: dict, split: str, recipe: dict) -> Shape:
    """A Shape from ``planning.build_plan`` output (the engine's offline plan)."""
    prefix = f"{split}/"
    options = {key[len(prefix):]: value for key, value in plan["options"].items() if key.startswith(prefix)}
    if "a0" not in options:
        raise PolicyError(f"the offline plan has no {split}/a0 option")
    names = ["init"] + [c["name"] for c in recipe["train"]["checkpoints"]]
    examples = {arm: {name: int(opt["checkpoints"][name]["examples_seen"]) for name in names}
                for arm, opt in options.items()}
    return Shape(tuple(names), examples, tuple(recipe["attribution"]["checkpoints"]),
                 int(plan["attribution_per_seed"][split]["gradient_passes"]),
                 int(plan["score_groups_per_split"][split]["guard_generations"]),
                 tuple(sorted(arm for arm in options if arm != "a0")))


def _f(value: float) -> Fraction:
    return Fraction(value)


def make_quoter(tariffs: Mapping, shape: Shape, short: str, full: str) -> Callable[[Op], Fraction]:
    """The frozen quote of one canonical operation (exact)."""
    tpe = _f(tariffs["train_per_example"])
    selection, final = _f(tariffs["evaluation"]["selection"]), _f(tariffs["evaluation"]["final"])
    overhead = {kind: _f(tariffs["call_overhead"][kind]) for kind in OP_KINDS}
    last = shape.last_attribution()

    def examples(arm: str, checkpoint: str) -> int:
        return shape.examples[arm][checkpoint]

    def quote(op: Op) -> Fraction:
        if op.kind not in overhead:
            raise PolicyError(f"no tariff for operation kind {op.kind!r}")
        base = overhead[op.kind]
        if op.kind == "screen":
            return base + tpe * examples(op.arm, short) + selection
        if op.kind == "full_from_short":
            return base + tpe * (examples(op.arm, full) - examples(op.arm, short)) + selection
        if op.kind == "full_from_init":
            return base + tpe * examples(op.arm, full) + selection
        if op.kind == "extend":
            return base + tpe * (examples(op.arm, last) - examples(op.arm, full))
        if op.kind == "attribution":
            return base + _f(tariffs["attribution_per_gradient_pass"]) * shape.attribution_passes
        if op.kind == "final":
            return base + tpe * examples(op.arm, full) + final
        if op.kind == "score_groups":
            return base + _f(tariffs["score_groups_per_row"]) * shape.score_rows
        return base

    return quote


def attribution_state_ops(shape: Shape, short: str, full: str, z0: int) -> dict[str, Op]:
    """Which a0 operation's run folder holds each attribution checkpoint's state at z0: the
    screen run up to the short checkpoint, the full continuation up to the full checkpoint, the
    extension beyond it."""
    out = {}
    for checkpoint in shape.attribution_checkpoints:
        i = shape.index(checkpoint)
        if i <= shape.index(short):
            out[checkpoint] = Op("screen", "a0", z0)
        elif i <= shape.index(full):
            out[checkpoint] = full_op("a0", z0, z0)
        else:
            out[checkpoint] = Op("extend", "a0", z0)
    return out


def prerequisite_ops(shape: Shape, short: str, full: str, z0: int) -> list[Op]:
    """S+'s a0 operations beyond the common screen that the attribution passes need."""
    last = shape.index(shape.last_attribution())
    if last <= shape.index(short):
        return []
    ops = [full_op("a0", z0, z0)]
    if last > shape.index(full):
        ops.append(Op("extend", "a0", z0))
    return ops


def reserve_quote(quote: Callable[[Op], Fraction], shape: Shape) -> Fraction:
    worst_edit = max((quote(Op("final", e, 0)) for e in shape.edits), default=Fraction(0))
    return worst_edit + quote(Op("final", "a0", 0))


def fixed_charges(method: str, quote: Callable[[Op], Fraction], shape: Shape, tariffs: Mapping,
                  short: str, full: str, z0: int) -> list[dict]:
    """The policy's charges before acquisition, in order (the reserve last)."""
    if method not in ("S-", "S+"):
        raise PolicyError(f"unknown method {method!r}")
    screen = [Op("screen", arm, z0) for arm in ("a0", *shape.edits)]
    charges = [{"category": "cold_setup", "ops": [], "quote": _f(tariffs["cold_setup"])},
               {"category": "static", "ops": list(STATIC_OPS)},
               {"category": "screen", "ops": screen}]
    if method == "S+":
        charges.append({"category": "prerequisite", "ops": prerequisite_ops(shape, short, full, z0)})
        charges.append({"category": "attribution", "ops": [Op("attribution", "", z0)]})
    for charge in charges:
        if "quote" not in charge:
            charge["quote"] = sum((quote(op) for op in charge["ops"]), Fraction(0))
    charges.append({"category": "reserve_final", "ops": [], "quote": reserve_quote(quote, shape)})
    return charges


def feasibility(method: str, quote: Callable[[Op], Fraction], shape: Shape, tariffs: Mapping,
                short: str, full: str, budget: float) -> dict:
    """Whether the budget covers the fixed charges, the reserve and the WORST initial top-two
    package over every possible ordered pair of edits (quotes do not depend on seed values)."""
    charges = fixed_charges(method, quote, shape, tariffs, short, full, 0)
    fixed = sum((c["quote"] for c in charges), Fraction(0))
    owned = {op for c in charges for op in c["ops"]}
    pairs = list(permutations(shape.edits, 2)) or [(e,) for e in shape.edits]
    worst = Fraction(0)
    for pair in pairs:
        ops = {op for e in pair for z in (0, 1) for op in (full_op(e, z, 0), full_op("a0", z, 0))} - owned
        worst = max(worst, sum((quote(op) for op in ops), Fraction(0)))
    available = _f(budget) - fixed
    return {"method": method, "fixed_including_reserve": float(fixed),
            "available_for_acquisition": float(available), "worst_initial_top_two": float(worst),
            "feasible": worst <= available,
            "charges": [{"category": c["category"], "quote": float(c["quote"])} for c in charges]}


def quoted_ledger(budget: float, charges: Sequence[dict], transcript: dict | None, chosen: Fraction | None,
                  reference: Fraction | None) -> dict:
    """The policy's quoted ledger: fixed charges, acquisition, and the final reserve's use by the
    chosen-model final and (an edit choice) the extra reference a0 final. The reserve was fixed for
    the worst-case two final runs before any choice and no choice releases it."""
    fixed = [c for c in charges if c["category"] != "reserve_final"]
    reserve = next(c["quote"] for c in charges if c["category"] == "reserve_final")
    spent_fixed = sum((c["quote"] for c in fixed), Fraction(0))
    acquisition = _f(transcript["spent"]) if transcript is not None else Fraction(0)
    out = {"budget": float(budget),
           "charges": [{"category": c["category"], "ops": [op.op_id for op in c["ops"]],
                        "quote": float(c["quote"])} for c in charges],
           "acquisition_spent": float(acquisition),
           "acquisition_leftover": None if transcript is None else transcript["leftover"],
           "reserve_final": float(reserve)}
    if chosen is not None:
        reference = reference or Fraction(0)
        used = chosen + reference
        out.update(final_used=float(used), reserve_unused=float(reserve - used),
                   total_quoted_used=float(spent_fixed + acquisition + used),
                   chosen_model_quote=float(chosen), reference_quote=float(reference),
                   selection_plus_chosen_model_quoted=float(spent_fixed + acquisition + chosen))
    return out


def engine_setup_seconds(receipt: dict) -> float:
    return math.fsum((receipt.get("engine_setup_seconds") or {}).values())


def attempt_seconds(receipt: dict, net_of_setup: bool) -> tuple[float, bool]:
    """(seconds, timing complete) of one attempt receipt; an interrupted attempt without an
    after-call receipt contributes its recorded lower bound and marks the timing incomplete."""
    setup = engine_setup_seconds(receipt) if net_of_setup else 0.0
    if receipt.get("seconds") is None:
        return max(0.0, (receipt.get("seconds_lower_bound") or 0.0) - setup), False
    return receipt["seconds"] - setup, True


def block_setup_seconds(block_receipts: Mapping[str, Sequence[dict]], session_receipts: Sequence[dict]) -> float:
    """The block's physical setup line: the engine's setup stages inside any of its operations plus
    its sessions' start records (process start, imports, session creation). Each policy is charged
    only the sessions it owns (``session_allocation``)."""
    return (math.fsum(engine_setup_seconds(r) for attempts in block_receipts.values() for r in attempts)
            + math.fsum(s["seconds"] for s in session_receipts))


def block_setup_measured(session_receipts: Sequence[dict]) -> bool:
    """Whether the block's setup was measured: one of its sessions started a process that had run no
    block before. A later block of a shared process reuses the loaded assets; its own setup is then
    unknown and its costs are lower bounds (never an invented zero)."""
    return any(s.get("process_shared_with_an_earlier_block") is False for s in session_receipts)


def physical_seconds(receipts: Mapping[str, Sequence[dict]]) -> tuple[float, bool]:
    """Every counted attempt of the given operations once (physical work deduplicated; an attempt
    without an after-call time contributes its lower bound) and whether every attempt was timed."""
    parts = [attempt_seconds(r, net_of_setup=False) for attempts in receipts.values() for r in attempts]
    return math.fsum(p[0] for p in parts), all(p[1] for p in parts)


def actual_ledger(categories: Mapping[str, Sequence[str]], receipts: Mapping[str, Sequence[dict]],
                  quotes: Mapping[str, float], static_receipts: Mapping[str, Sequence[dict]],
                  overhead: Mapping) -> dict:
    """A policy's reconstructed counterfactual whole-research cost: per category the external
    seconds of every attempt of its operations (failed attempts included and subtotalled), net of
    the engine's setup stages, plus the overhead of the sessions it owns (``overhead``: its
    ``setup_seconds`` and ``controller_seconds`` lines, ``setup_complete`` and the overhead's
    ``incomplete_because`` reasons; ``session_allocation``). Static operations are study-level
    physical work charged in full to every policy of every block. Incomplete (a lower bound, with
    its reasons) when an attempt lacks its after-call time or an overhead reason applies."""
    out: dict = {"categories": {}, "overruns": [], "failed_attempt_seconds": 0.0}
    total = []
    for category, op_ids in categories.items():
        seconds, failed, timed = [], [], True
        for op_id in op_ids:
            static = category == "static"
            attempts = (static_receipts if static else receipts).get(op_id, [])
            if not attempts:
                raise PolicyError(f"no receipt for charged operation {op_id}")
            op_seconds = []
            for receipt in attempts:
                net, complete = attempt_seconds(receipt, net_of_setup=not static)
                timed = timed and complete
                op_seconds.append(net)
                if receipt["status"] != "complete":
                    failed.append(net)
            seconds.extend(op_seconds)
            actual = math.fsum(op_seconds)
            if op_id in quotes and actual > quotes[op_id]:
                out["overruns"].append({"op": op_id, "quote": quotes[op_id], "actual": actual,
                                        "attempts": len(attempts)})
        out["categories"][category] = {"seconds": math.fsum(seconds), "operations": len(op_ids),
                                       "failed_attempt_seconds": math.fsum(failed), "timing_complete": timed}
        out["failed_attempt_seconds"] += math.fsum(failed)
        total.extend(seconds)
    reasons = list(overhead["incomplete_because"])
    if not all(v["timing_complete"] for v in out["categories"].values()) and _UNTIMED not in reasons:
        reasons.append(_UNTIMED)
    out.update(setup_seconds=overhead["setup_seconds"], controller_seconds=overhead["controller_seconds"],
               setup_complete=bool(overhead["setup_complete"]),
               total_seconds=math.fsum([*total, overhead["setup_seconds"], overhead["controller_seconds"]]),
               timing_complete=not reasons, incomplete_because=reasons,
               scope="reconstructed counterfactual standalone estimate from shared executed operations (external "
                     "after-call receipts, every attempt) and the overhead of the sessions this policy owns; not an "
                     "isolated invoice; provider billing is separate")
    return out


def controller_unknown(record: Mapping) -> str | None:
    """Why a session record's controller seconds are not final, else None: it has no end record
    (``controller_seconds`` None: a killed process), or it is the still-running session of a result
    snapshot (``open``: its segments closed so far are counted, the rest is not in the snapshot)."""
    if record.get("controller_seconds") is None:
        return _UNKNOWN_CONTROLLER
    return _OPEN_SESSION if record.get("open") else None


def _tag(receipt: Mapping) -> tuple | None:
    """(block, session number) of an attempt's session tag; None when untagged."""
    tag = receipt.get("session")
    return (tag.get("block"), tag.get("number")) if isinstance(tag, dict) else None


def _session_work(block: int, block_receipts: Mapping[str, Sequence[dict]],
                  static_receipts: Mapping[str, Sequence[dict]], session_records: Sequence[dict]) -> dict | None:
    """Session number -> (the operations it ran, the engine setup seconds recorded inside its block
    attempts). Static attempts run in a session of this block count as its work; they are charged
    gross in their category, so their setup stages stay there. None when a session record lacks a
    distinct number or a counted attempt lacks a session tag of these records."""
    numbers = [s.get("session") for s in session_records]
    if not numbers or not all(isinstance(n, int) and not isinstance(n, bool) for n in numbers) \
            or len(set(numbers)) != len(numbers):
        return None
    work: dict[int, tuple[set, list]] = {n: (set(), []) for n in numbers}
    for op_id, attempts in block_receipts.items():
        for receipt in attempts:
            tag = _tag(receipt)
            if tag is None or tag[0] != block or not isinstance(tag[1], int) or tag[1] not in work:
                return None
            work[tag[1]][0].add(op_id)
            work[tag[1]][1].append(engine_setup_seconds(receipt))
    for op_id, attempts in static_receipts.items():
        for receipt in attempts:
            tag = _tag(receipt)
            if tag is None or (tag[0] == block and (not isinstance(tag[1], int) or tag[1] not in work)):
                return None
            if tag[0] == block:
                work[tag[1]][0].add(op_id)
    return work


def session_allocation(block: int, block_receipts: Mapping[str, Sequence[dict]],
                       static_receipts: Mapping[str, Sequence[dict]], session_records: Sequence[dict], *,
                       own: set[str], reference: set[str], sensitivity: set[str],
                       owners: Mapping[str, Sequence[str]]) -> dict:
    """One policy's share of the block's session overhead (module doc). ``own``: the operations of its
    selection-plus-one-chosen-model scope; ``reference``: its extra reference a0 final;
    ``sensitivity``: the block's sensitivity-only operations; ``owners``: the controller owners of its
    ``primary`` and ``research`` scopes (``policy_owners``). Every session record carries its
    ``controller_seconds`` by owner, None when its end record is missing; a snapshot's still-running
    session carries the segments closed so far and ``open`` (``controller_unknown``): counted, and
    flagged like a missing end record.

    A session in a fresh process that no later session of the block shared (a later ``run_block``
    call of one process could reuse its loads) and that ran none of ``own`` leaves the subtotal with
    its whole overhead (start record, setup stages, controller seconds of the charged owners): to the
    policy's research when it ran ``reference`` or ``sensitivity`` work, else as ``other_policy``
    overhead, in neither scope of this policy. Every other session is charged its setup in the
    subtotal and its controller seconds by owner. Returns the lines of both scopes, the excluded
    sessions and the completeness reasons of the subtotal (``primary``), the research scope and the
    whole-research ledger (``whole``)."""
    primary_owners, research_owners = set(owners["primary"]), set(owners["research"])
    inside, research_ops = own | reference, (reference | sensitivity) - own
    work = _session_work(block, block_receipts, static_receipts, session_records)
    lines: dict[str, list[float]] = {key: [] for key in ("primary_setup", "primary_controller", "session_setup",
                                                         "session_controller", "owner_controller", "other")}
    excluded: dict[str, list[int]] = {"research": [], "other_policy": []}
    reasons: dict[str, list[str]] = {"primary": [], "research": [], "whole": []}

    def flag(reason: str, *scopes: str) -> None:
        for scope in scopes:
            if reason not in reasons[scope]:
                reasons[scope].append(reason)

    if not block_setup_measured(session_records):
        flag(_UNMEASURED, "primary", "whole")
    kinds: dict[int, str] = {}
    if work is None:   # nothing attributable: every session in the subtotal, nothing excluded
        lines["primary_setup"].append(block_setup_seconds(block_receipts, session_records))
        for record in session_records:
            known = record.get("controller_seconds") or {}
            lines["primary_controller"] += [v for o, v in known.items() if o in primary_owners]
            lines["owner_controller"] += [v for o, v in known.items() if o in research_owners]
        flag(_UNATTRIBUTED, "primary", "research", "whole")
    else:
        records = {s["session"]: s for s in session_records}
        shared = {n: records[n].get("process_shared_with_an_earlier_block") is not False for n in work}
        for n in sorted(work):
            ops, setups = work[n]
            setup = math.fsum([records[n]["seconds"], *setups])
            known = records[n].get("controller_seconds") or {}
            unknown = controller_unknown(records[n])
            alone = not shared[n] and not any(shared[k] for k in work if k > n)
            if alone and ops and not ops & own:
                kinds[n] = "research" if ops & research_ops else "other_policy"
                excluded[kinds[n]].append(n)
                charged = [v for o, v in known.items() if o not in UNCHARGED_OWNERS]
                if kinds[n] == "other_policy":
                    lines["other"] += [setup, *charged]
                    continue
                lines["session_setup"].append(setup)
                lines["session_controller"] += charged
                if unknown:
                    flag(unknown, "research", "whole")
                continue
            kinds[n] = "included"
            lines["primary_setup"].append(setup)
            lines["primary_controller"] += [v for o, v in known.items() if o in primary_owners]
            lines["owner_controller"] += [v for o, v in known.items() if o in research_owners]
            if unknown:
                flag(unknown, "primary", "whole", *(("research",) if research_owners else ()))
    for op_id, attempts in block_receipts.items():
        for receipt in attempts:
            if receipt.get("seconds") is None or receipt.get("engine_setup_seconds") is not None:
                continue   # untimed (flagged where charged) or with its setup composition recorded
            kind = "included" if work is None else kinds[_tag(receipt)[1]]
            if op_id not in own and kind == "included":
                flag(_HIDDEN, "primary")
            if op_id not in inside and kind in ("included", "research"):
                flag(_HIDDEN, "whole", *(("research",) if kind == "research" else ()))
    return {"identifiable": work is not None,
            "primary": {"setup_seconds": math.fsum(lines["primary_setup"]),
                        "controller_seconds": math.fsum(lines["primary_controller"])},
            "research": {"setup_seconds": math.fsum(lines["session_setup"]),
                         "controller_seconds": math.fsum([*lines["session_controller"], *lines["owner_controller"]]),
                         "session_seconds": math.fsum([*lines["session_setup"], *lines["session_controller"]]),
                         "sessions": excluded["research"]},
            "other_policy": {"seconds": math.fsum(lines["other"]), "sessions": excluded["other_policy"]},
            "incomplete_because": reasons}


def block_physical(block: int, block_receipts: Mapping[str, Sequence[dict]], session_records: Sequence[dict]) -> dict:
    """The block's physical controller-timed seconds, every second once: its counted attempts (an
    attempt without an after-call time at its lower bound), its sessions' start records and their
    measured controller seconds of every owner (static work is study level and added by the
    analysis). Complete only when every attempt was timed and ran in a recorded session of the block
    whose end record holds its controller seconds; a snapshot's still-running session (``open``)
    contributes the segments closed so far and leaves the seconds a lower bound
    (``PHYSICAL_BOUNDARY`` names what no controller timer covers)."""
    attempts, timed = physical_seconds(block_receipts)
    numbers = {s.get("session") for s in session_records}
    controller = [s.get("controller_seconds") for s in session_records]
    reasons = []
    if not timed:
        reasons.append(_UNTIMED)
    reasons.extend(dict.fromkeys(why for why in map(controller_unknown, session_records) if why))
    tags = [_tag(r) for receipts in block_receipts.values() for r in receipts]
    if any(tag is None or tag[0] != block or tag[1] not in numbers for tag in tags):
        reasons.append(_UNATTRIBUTED)
    start = math.fsum(s["seconds"] for s in session_records)
    known = math.fsum(v for c in controller if c for v in c.values())
    return {"attempt_seconds": attempts, "session_start_seconds": start, "controller_seconds": known,
            "seconds": math.fsum([attempts, start, known]), "timing_complete": not reasons,
            "incomplete_because": reasons}


def policy_owners(method: str, choice: str | None) -> dict[str, list[str]]:
    """The controller owners charged to a policy: common work, its own method and its chosen final in
    the selection-plus-one-chosen-model scope; the a0 final in its research when it chose an edit."""
    primary = {"common", method} | ({f"final:{choice}"} if choice is not None else set())
    return {"primary": sorted(primary), "research": ["final:a0"] if choice not in (None, "a0") else []}


def policy_costs(block: int, categories: Mapping[str, Sequence[str]], receipts: Mapping[str, Sequence[dict]],
                 quotes: Mapping[str, float], static_receipts: Mapping[str, Sequence[dict]],
                 session_records: Sequence[dict], sensitivity_only: Sequence[str],
                 owners: Mapping[str, Sequence[str]]) -> dict:
    """One policy's whole-research ledger (``actual``) and its two cost scopes, which add up to it:
    ``categories`` name its operations (``final_reference_a0`` only for an edit choice);
    ``sensitivity_only`` are the block's operations run only for the S- sensitivity; ``owners``
    (``policy_owners``) name the controller seconds charged to each scope. Sessions that ran only
    the other policy's work are in neither scope (``excluded_other_policy_overhead``)."""
    own = {op_id for c, ids in categories.items() if c not in REFERENCE_CATEGORIES for op_id in ids}
    reference = {op_id for c in REFERENCE_CATEGORIES for op_id in categories.get(c, ())}
    share = session_allocation(block, receipts, static_receipts, session_records, own=own, reference=reference,
                               sensitivity=set(sensitivity_only), owners=owners)
    primary, research, reasons = share["primary"], share["research"], share["incomplete_because"]
    ledger = actual_ledger(categories, receipts, quotes, static_receipts, {
        "setup_seconds": primary["setup_seconds"] + research["setup_seconds"],
        "controller_seconds": primary["controller_seconds"] + research["controller_seconds"],
        "setup_complete": block_setup_measured(session_records), "incomplete_because": reasons["whole"]})
    ledger["excluded_other_policy_overhead"] = share["other_policy"]
    selection = {c: v for c, v in ledger["categories"].items() if c not in REFERENCE_CATEGORIES}
    extra = {c: v for c, v in ledger["categories"].items() if c in REFERENCE_CATEGORIES}
    scope_reasons = {}
    for scope, cats in (("primary", selection), ("research", extra)):
        scope_reasons[scope] = list(reasons[scope])
        if not all(v["timing_complete"] for v in cats.values()) and _UNTIMED not in scope_reasons[scope]:
            scope_reasons[scope].append(_UNTIMED)
    reference_seconds = math.fsum(v["seconds"] for v in extra.values())
    subtotal = {"seconds": math.fsum([*(v["seconds"] for v in selection.values()), primary["setup_seconds"],
                                      primary["controller_seconds"]]),
                "categories": {c: v["seconds"] for c, v in selection.items()},
                "setup_seconds": primary["setup_seconds"], "controller_seconds": primary["controller_seconds"],
                "failed_attempt_seconds": math.fsum(v["failed_attempt_seconds"] for v in selection.values()),
                "excluded_session_overhead": {"identifiable": share["identifiable"],
                                              "research": {"seconds": research["session_seconds"],
                                                           "sessions": research["sessions"]},
                                              "other_policy": share["other_policy"]},
                "timing_complete": not scope_reasons["primary"], "incomplete_because": scope_reasons["primary"]}
    research_scope = {"seconds": math.fsum([reference_seconds, research["setup_seconds"],
                                            research["controller_seconds"]]),
                      "reference_a0_seconds": reference_seconds if extra else None,
                      "research_session_seconds": research["session_seconds"],
                      "setup_seconds": research["setup_seconds"], "controller_seconds": research["controller_seconds"],
                      "failed_attempt_seconds": math.fsum(v["failed_attempt_seconds"] for v in extra.values()),
                      "timing_complete": not scope_reasons["research"],
                      "incomplete_because": scope_reasons["research"]}
    return {"actual": ledger, PRIMARY_COST_SCOPE: subtotal, "reference_and_sensitivity": research_scope}
