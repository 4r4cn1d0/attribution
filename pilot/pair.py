"""Paired-world moments of Y = score(suppressed) - score(ordinary) by exhaustive enumeration.

(x, y) = intervention_pair(config, pre_state, action, alpha): x is suppressed, y ordinary.
Every internal pair node takes each world's own probs and its K weight-1 successors, builds a
K x K coupling and recurses depth-first. Nothing is rounded, merged or cached; ordinary
couplings skip only children of exactly zero mass. Supported size: K**(2H) <= 3**8 paired
leaves (K = 3, H <= 4); larger requests raise ValueError from :func:`supported_horizon`,
which callers can run before any enumeration.

* :func:`pair_moments`: one ordinary coupling from ORDINARY_METHODS. 'ordered' sorts actions
  by target (family A) or by the successor's q-coordinate q . U_a(theta) (family B), per world,
  ties by action ID. 'distance' is transport with cost ||theta(U_a(x)) - theta(U_b(y))||**2.
* :func:`oracle`: co-adapted Bellman oracle. Leaf value (g(x) - g(y))**2; at h > 0 all K**2
  child values are computed, then a transport LP with row p(x) and column p(y) minimises their
  expectation. LP optimality is reported as float64 gap estimates, not certified.
* :func:`terminal_ot`: quantile (sorted CDF overlap) coupling of the two exact terminal score
  laws. It is an unrestricted lower bound, NOT an online or co-adapted coupling.

variance = second_moment - mean**2. Negative values no smaller than -1e-14 (roundoff) are
clamped to 0 with the correction reported; more negative values raise FloatingPointError.
"""

from __future__ import annotations

import math
import numbers
import time
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .couplings import (Coupling, distribution, fixed_label, independent, maximal, ordered,
                        shared_gumbel, transport)
from .exact import terminal_law
from .process import Config, State, apply_event, intervention_pair, probs, score

__all__ = [
    "ORDINARY_METHODS", "Diagnostics", "PairMoments", "OracleMoments", "TerminalBound",
    "supported_horizon", "pair_moments", "oracle", "terminal_ot",
]

ORDINARY_METHODS = ("independent", "fixed_label", "ordered", "maximal", "shared_gumbel", "distance")
MAX_PAIR_LEAVES = 3 ** 8
VARIANCE_TOL = 1e-14
TERMINAL_LABEL = "terminal OT lower bound (noncausal; not an online/co-adapted oracle)"

Matrix = tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class Diagnostics:
    """Work actually executed and worst checks. apply_event includes the intervention pair;
    min_entry is None when no plan was built; lp_solves counts transport calls and
    max_gap_estimate is their largest |gap_estimate| (0.0 without LPs; a float64 diagnostic)."""

    seconds: float
    coupling_seconds: float
    internal_nodes: int
    leaves: int
    probs: int
    apply_event: int
    score: int
    couplings: int
    lp_solves: int
    max_marginal_residual: float
    min_entry: float | None
    max_gap_estimate: float


@dataclass(frozen=True)
class PairMoments:
    """Exact moments of Y under one ordinary coupling."""

    method: str
    horizon: int
    mean: float
    second_moment: float
    variance: float
    variance_correction: float
    diagnostics: Diagnostics


@dataclass(frozen=True)
class OracleMoments:
    """Bellman oracle value and root evidence (None at H = 0).

    suboptimality_estimate accumulates the LP gap estimates as gap_estimate(node) + max over
    children (0 at leaves). Were every quantity exact it would bound second_moment - optimum
    from above; it is a float64 diagnostic, not a certificate (see couplings.transport), and
    says nothing about how far below the optimum second_moment may lie. root_p / root_q are
    the suppressed / ordinary root laws, root_cost[a][b] the child oracle values and root_plan
    the chosen root coupling.
    """

    horizon: int
    mean: float
    second_moment: float
    variance: float
    variance_correction: float
    diagnostics: Diagnostics
    suboptimality_estimate: float
    root_p: tuple[float, ...] | None
    root_q: tuple[float, ...] | None
    root_cost: Matrix | None
    root_plan: Matrix | None
    method: str = "oracle"


@dataclass(frozen=True)
class TerminalBound:
    """Unrestricted terminal-score transport; see TERMINAL_LABEL."""

    horizon: int
    mean: float
    second_moment: float
    variance: float
    variance_correction: float
    diagnostics: Diagnostics
    label: str = TERMINAL_LABEL


class _Tally:
    def __init__(self) -> None:
        self.start = time.perf_counter()
        self.coupling_seconds = 0.0
        self.nodes = self.leaves = self.probs = self.score = self.couplings = self.lps = 0
        self.apply = 2  # the intervention pair
        self.residual = self.gap = 0.0
        self.min_entry: float | None = None

    def expand(self, config: Config, state: State) -> tuple[NDArray[np.float64], tuple[State, ...]]:
        p = distribution("probs", probs(config, state))
        self.probs += 1
        self.apply += config.n_actions
        return p, tuple(apply_event(config, state, a, 1.0) for a in range(config.n_actions))

    def leaf(self, config: Config, x: State, y: State) -> float:
        self.leaves += 1
        self.score += 2
        return score(config, x) - score(config, y)

    def record(self, c: Coupling) -> Coupling:
        self.couplings += 1
        self.coupling_seconds += c.seconds
        self.residual = max(self.residual, c.marginal_residual)
        self.min_entry = c.min_entry if self.min_entry is None else min(self.min_entry, c.min_entry)
        if c.gap_estimate is not None:
            self.lps += 1
            self.gap = max(self.gap, abs(c.gap_estimate))
        return c

    def diagnostics(self) -> Diagnostics:
        return Diagnostics(time.perf_counter() - self.start, self.coupling_seconds, self.nodes,
                           self.leaves, self.probs, self.apply, self.score, self.couplings, self.lps,
                           self.residual, self.min_entry, self.gap)


def supported_horizon(config: Config, H: int) -> int:
    """H as an int if K**(2H) <= MAX_PAIR_LEAVES paired leaves, else TypeError / ValueError.

    Cheap for any H: at most 32 factors of K are multiplied, already over the limit for every
    K >= 2, so callers can validate before starting exponential work.
    """
    if not isinstance(config, Config):
        raise TypeError(f"expected a Config, got {type(config).__name__}")
    if not isinstance(H, numbers.Integral) or isinstance(H, bool):
        raise TypeError(f"H must be an integer, got {H!r}")
    if H < 0:
        raise ValueError(f"H must be >= 0, got {H}")
    if config.n_actions ** (2 * min(int(H), 16)) > MAX_PAIR_LEAVES:
        raise ValueError(f"unsupported size: K**(2H) paired leaves with K = {config.n_actions}, "
                         f"H = {H} exceeds {MAX_PAIR_LEAVES}")
    return int(H)


def _setup(config: Config, pre_state: State, action: int, alpha: float, H: int) -> tuple[int, State, State]:
    horizon = supported_horizon(config, H)
    x, y = intervention_pair(config, pre_state, action, alpha)
    return horizon, x, y


def _variance(mean: float, second: float) -> tuple[float, float]:
    variance = second - mean * mean
    if variance >= 0.0:
        return variance, 0.0
    if variance < -VARIANCE_TOL:
        raise FloatingPointError(f"variance {variance:.3e} is below the roundoff tolerance -{VARIANCE_TOL}")
    return 0.0, -variance


def _matrix(values: NDArray[np.float64]) -> Matrix:
    return tuple(tuple(row) for row in values.tolist())


def _ordinary(method: str, config: Config, px: NDArray[np.float64], py: NDArray[np.float64],
              xs: tuple[State, ...], ys: tuple[State, ...]) -> Coupling:
    if method == "independent":
        return independent(px, py)
    if method == "fixed_label":
        return fixed_label(px, py)
    if method == "maximal":
        return maximal(px, py)
    if method == "shared_gumbel":
        return shared_gumbel(px, py)
    if method == "ordered":
        if config.family == "A":
            return ordered(px, py, config.targets, config.targets)
        return ordered(px, py, [float(np.dot(config.q, s.theta)) for s in xs],
                       [float(np.dot(config.q, s.theta)) for s in ys])
    cost = [[math.fsum((a - b) ** 2 for a, b in zip(u.theta, v.theta)) for v in ys] for u in xs]
    return transport(px, py, cost)  # "distance"


def _pair(method: str, config: Config, x: State, y: State, h: int, tally: _Tally) -> tuple[float, float]:
    """(E[Y], E[Y**2]) below pair node (x, y) with h rounds left."""
    if h == 0:
        d = tally.leaf(config, x, y)
        return d, d * d
    tally.nodes += 1
    px, xs = tally.expand(config, x)
    py, ys = tally.expand(config, y)
    plan = tally.record(_ordinary(method, config, px, py, xs, ys)).matrix
    first, second = [], []
    for a, b in zip(*np.nonzero(plan)):
        m1, m2 = _pair(method, config, xs[a], ys[b], h - 1, tally)
        first.append(float(plan[a, b]) * m1)
        second.append(float(plan[a, b]) * m2)
    return math.fsum(first), math.fsum(second)


def pair_moments(method: str, config: Config, pre_state: State, action: int, alpha: float,
                 H: int) -> PairMoments:
    """Exact E[Y], E[Y**2] and Var(Y) under the ordinary coupling `method`."""
    if method not in ORDINARY_METHODS:
        raise ValueError(f"unknown method {method!r}; expected one of {ORDINARY_METHODS}")
    tally = _Tally()
    horizon, x, y = _setup(config, pre_state, action, alpha, H)
    mean, second = _pair(method, config, x, y, horizon, tally)
    variance, correction = _variance(mean, second)
    return PairMoments(method, horizon, mean, second, variance, correction, tally.diagnostics())


def _bellman(config: Config, x: State, y: State, h: int, tally: _Tally):
    """(V, mean under the chosen plans, suboptimality estimate, root evidence or None)."""
    if h == 0:
        d = tally.leaf(config, x, y)
        return d * d, d, 0.0, None
    tally.nodes += 1
    px, xs = tally.expand(config, x)
    py, ys = tally.expand(config, y)
    children = [[_bellman(config, u, v, h - 1, tally)[:3] for v in ys] for u in xs]
    cost = np.array([[c[0] for c in row] for row in children])
    plan = tally.record(transport(px, py, cost))
    means = np.array([[c[1] for c in row] for row in children])
    mean = math.fsum((plan.matrix * means).ravel().tolist())
    estimate = plan.gap_estimate + max(c[2] for row in children for c in row)
    return plan.objective, mean, estimate, (px, py, cost, plan.matrix)


def oracle(config: Config, pre_state: State, action: int, alpha: float, H: int) -> OracleMoments:
    """Co-adapted Bellman oracle: minimum E[Y**2] over couplings using only current states."""
    tally = _Tally()
    horizon, x, y = _setup(config, pre_state, action, alpha, H)
    second, mean, estimate, root = _bellman(config, x, y, horizon, tally)
    variance, correction = _variance(mean, second)
    px, py, cost, plan = root if root is not None else (None,) * 4
    return OracleMoments(
        horizon, mean, second, variance, correction, tally.diagnostics(), estimate,
        None if px is None else tuple(px.tolist()), None if py is None else tuple(py.tolist()),
        None if cost is None else _matrix(cost), None if plan is None else _matrix(plan))


def terminal_ot(config: Config, pre_state: State, action: int, alpha: float, H: int) -> TerminalBound:
    """Minimum E[Y**2] over ALL couplings of the two exact terminal score laws (sorted overlap)."""
    tally = _Tally()
    horizon, x, y = _setup(config, pre_state, action, alpha, H)
    laws = [terminal_law(config, s, horizon) for s in (x, y)]
    scores = [[leaf.score for leaf in law.leaves] for law in laws]
    plan = tally.record(ordered(*([leaf.mass for leaf in law.leaves] for law in laws), *scores)).matrix
    diff = np.subtract.outer(*scores)
    mean = math.fsum((plan * diff).ravel().tolist())
    second = math.fsum((plan * diff * diff).ravel().tolist())
    for law in laws:
        tally.nodes += law.operations.probs
        tally.leaves += len(law.leaves)
        tally.probs += law.operations.probs
        tally.apply += law.operations.apply_event
        tally.score += law.operations.score
    variance, correction = _variance(mean, second)
    return TerminalBound(horizon, mean, second, variance, correction, tally.diagnostics())
