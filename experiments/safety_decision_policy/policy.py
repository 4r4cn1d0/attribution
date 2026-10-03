"""The compared selection policy: frozen ranking, fixed acquisition schedule and choice (pure
functions of their inputs; stdlib only). S- and S+ run this same code; only their feature lists,
frozen predictors and charged prerequisites differ. This is a specified simple policy, not an
optimal or new allocator.

Operations are canonical (``Op``): the same artifact is always produced by the same physical
operation whichever policy buys it, so a physically shared run is one counterfactual purchase
in each policy's own inventory. A full observation of (arm, seed) is the continuation of the
screen run when the seed is the screen seed z0 (one trajectory: the same observation, never a
second seed), otherwise a fresh run from the seeded adapter.

Ranking (``RANK_RULE``): after the screen (and S+'s attribution), edits are ordered once by
(1) predicted violation status, (2) normalized violation, (3) predicted safety change, (4) the
opaque tie rank. Nothing reranks afterwards.

Acquisition (``ACQUISITION_RULE``), on quotes only (measured times and outcomes never enter):
the top two edits each buy paired full observations at z0 and z1 (missing artifacts only; the
budget must cover them, otherwise the configuration is infeasible and refused). Then passes
repeat: (A) breadth scans every unpromoted edit in rank order and buys the first whose whole
z0/z1 package fits (at most one promotion per pass); (B) repetition visits every promoted edit
in rank order and buys its earliest unused seed z2, z3, ... when the paired observation fits
(a paid a0 at that seed is reused; partial passes allowed). It stops only after a pass in which
nothing fit. Every scan, skip and the indivisible leftover are recorded. No short run is bought
after the ranking and there is no fixed pool or cap: the seed sequence is the block's whole
disjoint progression in its namespace, and its exhaustion is recorded.

Choice (``CHOICE_RULE``): completed paired full observations owned by the policy only, equal
seed weights, adverse endpoints (``outcomes.adverse``: the upper end of the missing-label interval
of dF and O, the exact unique-argmax L); an edit is eligible with >= 2 distinct seeds and estimated
utility loss and refusal increase at most their thresholds (shared heuristics, not confidence
certificates); the smallest estimated safety change wins, a0 counts as exactly 0, exact ties go
to a0 and then to the opaque tie rank. Raw and broader-sensitivity means are recorded beside each
estimate and never choose. Unequal observation counts can favor noisy minima: performance is
measured on fresh final deployments, never by the winning acquisition estimate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Mapping, Sequence

from .common import PolicyError
from .outcomes import CHANGES, adverse

__all__ = ["RANK_RULE", "ACQUISITION_RULE", "CHOICE_RULE", "MIN_FULL_SEEDS", "Op", "full_op",
           "rank_edits", "InfeasibleBudget", "plan_acquisition", "next_purchase", "choose"]

MIN_FULL_SEEDS = 2
RANK_RULE = ("rank edits once by (1) predicted violation (utility loss > tau_L or refusal increase > "
             "tau_O), (2) normalized violation max(0,(pL-tau_L)/s_L) + max(0,(pO-tau_O)/s_O), "
             "(3) predicted safety change ascending, (4) opaque view tie rank; no reranking")
ACQUISITION_RULE = ("top two edits buy paired full observations at z0 and z1 (missing artifacts only); "
                    "then repeat passes of (A) breadth: first unpromoted edit in rank order whose whole "
                    "z0/z1 package fits, at most one per pass, and (B) repetition: each promoted edit in "
                    "rank order buys its earliest unused seed z2, z3, ... if the paired full observation "
                    "fits (paid a0 reused); stop after a pass with no purchase; quotes only; every skip "
                    "and the leftover recorded; no short runs after ranking; no pool or cap")
CHOICE_RULE = ("own completed paired full observations only; equal seed weights; adverse endpoints (upper "
               "missing-label endpoint of dF and O, exact unique-argmax L); eligible: >= 2 distinct seeds, "
               "mean utility loss <= tau_L and mean refusal increase <= tau_O; smallest mean safety change "
               "wins; a0 = 0 exactly; ties: a0, then tie rank; raw and broader means recorded, never choosing")
FULL_KINDS = ("full_from_short", "full_from_init")


class InfeasibleBudget(PolicyError):
    """The budget cannot buy the initial top-two packages: the configuration is refused."""


@dataclass(frozen=True, order=True)
class Op:
    """A canonical physical operation. ``seed`` is -1 and ``arm`` empty for study-level static
    operations; ``arm`` is empty for attribution."""

    kind: str
    arm: str
    seed: int

    @property
    def op_id(self) -> str:
        if self.seed < 0:
            return self.kind
        return f"{self.kind}-{self.arm}-{self.seed}" if self.arm else f"{self.kind}-{self.seed}"


def full_op(arm: str, seed: int, screen_seed: int) -> Op:
    return Op("full_from_short" if seed == screen_seed else "full_from_init", arm, seed)


def rank_edits(predictions: Mapping[str, Mapping[str, float]], tie_ranks: Mapping[str, int],
               constraints: Mapping[str, float]) -> list[dict]:
    """Every edit in frozen rank order with the quantities that ordered it."""
    tau_l, tau_o = constraints["tau_utility_loss"], constraints["tau_refusal_increase"]
    s_l, s_o = constraints["scale_utility_loss"], constraints["scale_refusal_increase"]
    if s_l <= 0 or s_o <= 0:
        raise PolicyError("normalization scales must be positive")
    if set(predictions) != set(tie_ranks):
        raise PolicyError("predictions and tie ranks cover different edits")
    rows = []
    for gid, p in predictions.items():
        over_l, over_o = p["utility_loss"] - tau_l, p["refusal_increase"] - tau_o
        rows.append({"edit": gid, "violates": over_l > 0 or over_o > 0,
                     "normalized_violation": max(0.0, over_l / s_l) + max(0.0, over_o / s_o),
                     "predicted": {key: p[key] for key in CHANGES}, "tie_rank": tie_ranks[gid]})
    rows.sort(key=lambda r: (r["violates"], r["normalized_violation"], r["predicted"]["safety_change"],
                             r["tie_rank"]))
    for i, row in enumerate(rows):
        row["rank"] = i
    return rows


def _money(value: Fraction) -> float:
    return float(value)


def plan_acquisition(*, ranking: Sequence[str], available: Fraction, quote: Callable[[Op], Fraction],
                     seed_at: Callable[[int], int | None], owned: frozenset[Op] | set[Op],
                     screen_seed: int) -> dict:
    """The complete acquisition transcript of one policy (deterministic; see module doc).
    ``available`` is the quoted budget left after every fixed charge and the final reserve;
    ``seed_at(k)`` is the block's k-th selector seed or None when the progression is exhausted."""
    if seed_at(0) != screen_seed:
        raise PolicyError("the seed sequence must start with the screen seed z0")
    z0, z1 = seed_at(0), seed_at(1)
    if z1 is None:
        raise InfeasibleBudget("the seed sequence has no second seed z1")
    owned = set(owned)
    rank_of = {e: i for i, e in enumerate(ranking)}
    spent: list[Fraction] = []
    purchases: list[dict] = []
    events: list[dict] = []
    promoted: list[str] = []
    next_index: dict[str, int] = {}
    planned: dict[str, list[int]] = {e: [] for e in ranking}

    def remaining() -> Fraction:
        return available - sum(spent, Fraction(0))

    def package(edit: str, seeds: Sequence[int]) -> tuple[list[Op], Fraction]:
        ops: list[Op] = []
        for z in seeds:
            for op in (full_op(edit, z, screen_seed), full_op("a0", z, screen_seed)):
                if op not in owned and op not in ops:
                    ops.append(op)
        return ops, sum((quote(op) for op in ops), Fraction(0))

    def buy(phase: str, edit: str, seeds: Sequence[int], ops: list[Op], cost: Fraction) -> None:
        if cost > remaining():
            raise AssertionError("internal: purchase above the remaining quote")
        spent.append(cost)
        owned.update(ops)
        planned[edit].extend(seeds)
        purchases.append({"step": len(purchases), "phase": phase, "edit": edit, "seeds": list(seeds),
                          "ops": [op.op_id for op in ops], "op_keys": [[op.kind, op.arm, op.seed] for op in ops],
                          "quote": _money(cost), "remaining_after": _money(remaining())})

    for edit in ranking[:2]:
        ops, cost = package(edit, [z0, z1])
        if cost > remaining():
            raise InfeasibleBudget(f"the initial package of rank {rank_of[edit]} edit {edit} costs "
                                   f"{float(cost):.6g} but only {float(remaining()):.6g} is available")
        buy("initial", edit, [z0, z1], ops, cost)
        promoted.append(edit)
        next_index[edit] = 2
    passes, last_quotes = 0, []
    while True:
        passes += 1
        progress, scanned, bought, last_quotes = False, [], None, []
        for edit in ranking:
            if edit in promoted:
                continue
            ops, cost = package(edit, [z0, z1])
            ok = cost <= remaining()
            scanned.append({"edit": edit, "rank": rank_of[edit], "quote": _money(cost), "affordable": ok})
            if ok:
                buy("breadth", edit, [z0, z1], ops, cost)
                promoted.append(edit)
                next_index[edit] = 2
                bought, progress = edit, True
                break
            last_quotes.append(cost)
        events.append({"pass": passes, "phase": "breadth", "scanned": scanned, "promoted": bought,
                       "remaining_after": _money(remaining())})
        visits = []
        for edit in sorted(promoted, key=rank_of.__getitem__):
            k = next_index[edit]
            z = seed_at(k)
            if z is None:
                visits.append({"edit": edit, "seed_index": k, "seed": None, "quote": None,
                               "bought": False, "reason": "seed sequence exhausted"})
                continue
            ops, cost = package(edit, [z])
            ok = cost <= remaining()
            if ok:
                buy("repeat", edit, [z], ops, cost)
                next_index[edit] = k + 1
                progress = True
            else:
                last_quotes.append(cost)
            visits.append({"edit": edit, "seed_index": k, "seed": z, "quote": _money(cost), "bought": ok,
                           "reason": None if ok else "unaffordable"})
        events.append({"pass": passes, "phase": "repeat", "visits": visits,
                       "remaining_after": _money(remaining())})
        if not progress:
            break
    cheapest = min(last_quotes) if last_quotes else None
    return {"available": _money(available), "spent": _money(sum(spent, Fraction(0))),
            "leftover": _money(remaining()),
            "stop": {"reason": "no affordable promotion package or repeat" if cheapest is not None
                     else "every edit promoted and every promoted edit's seed sequence exhausted",
                     "cheapest_unaffordable_quote": None if cheapest is None else _money(cheapest),
                     "indivisible_leftover": cheapest is not None},
            "passes": passes, "purchases": purchases, "events": events, "promoted": promoted,
            "planned_seeds": {e: planned[e] for e in ranking if planned[e]},
            "owned_ops": sorted(op.op_id for op in owned), "rule": ACQUISITION_RULE}


def next_purchase(transcript: dict, *, ranking: Sequence[str], quote: Callable[[Op], Fraction],
                  seed_at: Callable[[int], int | None], owned: frozenset[Op] | set[Op],
                  screen_seed: int) -> dict | None:
    """The single purchase the schedule would make next if the leftover were raised just enough
    (the S- one-extra-purchase sensitivity): the first unpromoted edit's package in rank order,
    else the first promoted edit's next seed. None if nothing remains to buy."""
    owned, promoted = set(owned), list(transcript["promoted"])
    rank_of = {e: i for i, e in enumerate(ranking)}
    z0, z1 = seed_at(0), seed_at(1)

    def package(edit: str, seeds: Sequence[int]) -> dict:
        ops: list[Op] = []
        for z in seeds:
            for op in (full_op(edit, z, screen_seed), full_op("a0", z, screen_seed)):
                if op not in owned and op not in ops:
                    ops.append(op)
        cost = sum((quote(op) for op in ops), Fraction(0))
        return {"edit": edit, "seeds": list(seeds), "ops": ops, "quote": cost}

    for edit in ranking:
        if edit not in promoted:
            return {"phase": "breadth", **package(edit, [z0, z1])}
    for edit in sorted(promoted, key=rank_of.__getitem__):
        z = seed_at(2 + sum(1 for p in transcript["purchases"] if p["edit"] == edit and p["phase"] == "repeat"))
        if z is not None:
            return {"phase": "repeat", **package(edit, [z])}
    return None


def choose(changes: Mapping[str, Sequence[dict]], tie_ranks: Mapping[str, int],
           constraints: Mapping[str, float]) -> dict:
    """The policy's locked choice from its own completed paired full changes (edit -> one
    ``outcomes.paired_change`` per seed); every menu edit appears, possibly with none."""
    tau_l, tau_o = constraints["tau_utility_loss"], constraints["tau_refusal_increase"]
    if set(changes) != set(tie_ranks):
        raise PolicyError("choose needs every menu edit (possibly with no observation)")
    rows = []
    for edit in sorted(changes, key=tie_ranks.__getitem__):
        obs = list(changes[edit])
        seeds = [c["seed"] for c in obs]
        if len(set(seeds)) != len(seeds):
            raise PolicyError(f"{edit}: one observation per seed (a continuation is not a new seed)")
        means = raw = broader = None
        reasons = []
        if obs:
            ends = [adverse(c) for c in obs]
            means = {key: math.fsum(e[key] for e in ends) / len(ends) for key in CHANGES}
            raw = {key: math.fsum(c[key]["raw"] for c in obs) / len(obs) for key in CHANGES}
            broader = {key: math.fsum(c[key]["broader"][1] for c in obs) / len(obs) for key in CHANGES}
        if len(obs) < MIN_FULL_SEEDS:
            reasons.append(f"{len(obs)} complete paired full seed(s); eligibility needs >= {MIN_FULL_SEEDS}")
        else:
            if means["utility_loss"] > tau_l:
                reasons.append("estimated utility loss above tau_utility_loss")
            if means["refusal_increase"] > tau_o:
                reasons.append("estimated refusal increase above tau_refusal_increase")
        rows.append({"edit": edit, "seeds": sorted(seeds), "n": len(obs), "adverse_means": means,
                     "raw_means": raw, "broader_adverse_means": broader,
                     "eligible": not reasons, "reasons": reasons, "tie_rank": tie_ranks[edit]})
    candidates = [("a0", 0.0, 0, -1)] + [(r["edit"], r["adverse_means"]["safety_change"], 1, r["tie_rank"])
                                         for r in rows if r["eligible"]]
    best = min(candidates, key=lambda c: (c[1], c[2], c[3]))
    return {"choice": best[0], "estimate": best[1], "estimates": rows, "rule": CHOICE_RULE}
