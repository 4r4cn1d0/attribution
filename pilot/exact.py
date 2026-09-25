"""Exact terminal-score law and conditional attribution by exhaustive path enumeration.

From a start state, all K**H action paths of the next H events are enumerated. Each
transition takes its action probabilities from ``probs`` at its own state and applies the
event with ``apply_event`` at weight 1; a leaf's mass is the product of the probabilities
along its path. Nothing is rounded, pruned or merged and sums use ``math.fsum``, so the
leaves are the exact law of the terminal score up to the float64 arithmetic of
:mod:`pilot.process`. Time and memory grow as K**H.
"""

from __future__ import annotations

import math
import numbers
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray

from .process import Config, State, apply_event, intervention_pair, probs, score

__all__ = ["Leaf", "OperationCounts", "TerminalLaw", "Attribution", "terminal_law", "attribution"]

_SUM_TOL = 1e-12  # shared local and terminal probability-mass acceptance tolerance


class Leaf(NamedTuple):
    """One enumerated future: action path, its probability mass, terminal state and score."""

    path: tuple[int, ...]
    mass: float
    state: State
    score: float


@dataclass(frozen=True)
class OperationCounts:
    """Numbers of process calls actually executed."""

    probs: int = 0
    apply_event: int = 0
    score: int = 0

    def __add__(self, other: OperationCounts) -> OperationCounts:
        if not isinstance(other, OperationCounts):
            return NotImplemented
        return OperationCounts(self.probs + other.probs, self.apply_event + other.apply_event,
                               self.score + other.score)


@dataclass(frozen=True)
class TerminalLaw:
    """Law of the score after `horizon` further events; leaves are in lexicographic path order.

    mass = fsum(masses), mean = fsum(mass * score), second_moment = fsum(mass * score**2).
    The moments are not renormalised by `mass`, which equals 1 up to rounding.
    """

    horizon: int
    leaves: tuple[Leaf, ...]
    mass: float
    mean: float
    second_moment: float
    operations: OperationCounts


@dataclass(frozen=True)
class Attribution:
    """Effect of suppressing an observed event, conditional on that event having occurred.

    delta = suppressed.mean - ordinary.mean. `action_probability` is the pre-event policy
    probability of `action`; it is metadata and is never multiplied into delta.
    `operations` covers the intervention pair, the metadata probs call and both laws.
    """

    delta: float
    suppressed: TerminalLaw
    ordinary: TerminalLaw
    action: int
    alpha: float
    action_probability: float
    operations: OperationCounts


def _horizon(H: object) -> int:
    if not isinstance(H, numbers.Integral) or isinstance(H, bool):
        raise TypeError(f"H must be an integer, got {H!r}")
    if H < 0:
        raise ValueError(f"H must be >= 0, got {H}")
    return int(H)


def _check(config: object, state: object) -> None:
    if not isinstance(config, Config):
        raise TypeError(f"expected a Config, got {type(config).__name__}")
    if not isinstance(state, State):
        raise TypeError(f"expected a State, got {type(state).__name__}")
    if len(state.theta) != config.dim:
        raise ValueError(f"state dimension {len(state.theta)} != config dimension {config.dim}")


def _finite(name: str, value: float) -> float:
    if not math.isfinite(value):
        raise FloatingPointError(f"non-finite {name} {value}")
    return value


def _distribution(p: NDArray[np.float64]) -> tuple[float, ...]:
    values = tuple(p.tolist())
    if not (all(math.isfinite(x) and x >= 0.0 for x in values)
            and abs(math.fsum(values) - 1.0) <= _SUM_TOL):
        raise FloatingPointError(f"probs returned an invalid distribution {values}")
    return values


def terminal_law(config: Config, post_event_state: State, H: int) -> TerminalLaw:
    """Exact law of the score after H further weight-1 events from `post_event_state`.

    All K**H paths are kept and each transition uses probs() at its own state. H = 0 gives
    the single leaf ((), 1.0, post_event_state, score(post_event_state)).
    """
    horizon = _horizon(H)
    _check(config, post_event_state)
    n_probs = n_apply = n_score = 0
    frontier: list[tuple[tuple[int, ...], float, State]] = [((), 1.0, post_event_state)]
    for _ in range(horizon):
        expanded = []
        for path, mass, state in frontier:
            p = _distribution(probs(config, state))
            n_probs += 1
            for a, p_a in enumerate(p):
                expanded.append((path + (a,), mass * p_a, apply_event(config, state, a, 1.0)))
                n_apply += 1
        frontier = expanded
    leaves = []
    for path, mass, state in frontier:
        s = score(config, state)
        n_score += 1
        leaves.append(Leaf(path, _finite("mass", mass), state, _finite("score", s)))
    total_mass = _finite("mass", math.fsum(leaf.mass for leaf in leaves))
    if abs(total_mass - 1.0) > _SUM_TOL:
        raise FloatingPointError(f"terminal mass {total_mass} differs from 1 by more than {_SUM_TOL}")
    return TerminalLaw(
        horizon=horizon,
        leaves=tuple(leaves),
        mass=total_mass,
        mean=_finite("mean", math.fsum(leaf.mass * leaf.score for leaf in leaves)),
        second_moment=_finite("second moment",
                              math.fsum(leaf.mass * leaf.score * leaf.score for leaf in leaves)),
        operations=OperationCounts(n_probs, n_apply, n_score),
    )


def attribution(config: Config, pre_state: State, action: int, alpha: float, H: int) -> Attribution:
    """Exact conditional attribution of the observed event `action` taken at `pre_state`.

    intervention_pair gives the suppressed (weight 1 - alpha) and ordinary (weight 1)
    post-event states; each world's terminal law is then enumerated independently.
    """
    horizon = _horizon(H)
    _check(config, pre_state)
    suppressed_state, ordinary_state = intervention_pair(config, pre_state, action, alpha)
    action_probability = _distribution(probs(config, pre_state))[int(action)]
    suppressed = terminal_law(config, suppressed_state, horizon)
    ordinary = terminal_law(config, ordinary_state, horizon)
    pair_and_metadata = OperationCounts(probs=1, apply_event=2)
    return Attribution(
        delta=_finite("delta", suppressed.mean - ordinary.mean),
        suppressed=suppressed,
        ordinary=ordinary,
        action=int(action),
        alpha=float(alpha),
        action_probability=action_probability,
        operations=pair_and_metadata + suppressed.operations + ordinary.operations,
    )
