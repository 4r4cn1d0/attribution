"""Joint action laws (couplings) of two categorical laws: p on rows, q on columns.

Every constructor returns a :class:`Coupling` whose matrix is checked after construction,
independently of how it was built: max |row or column sum - marginal| <= 1e-12 and every
entry >= -1e-14, else :class:`CouplingError`. Plans are never clipped or renormalised. The
checked matrix is backed by immutable bytes: NumPy refuses to make it or any view of it
writable again, so the recorded evidence keeps describing it. Marginals must be equal-length,
finite, nonnegative 1-D vectors summing to 1 within 1e-12; invalid inputs raise ``TypeError``
or ``ValueError``.

Numerical domain of :func:`shared_gumbel`: strictly positive p and q with
max/min ratio <= 1e100 in each vector; anything else is rejected, not approximated.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import linprog

__all__ = [
    "Coupling", "CouplingError", "distribution", "independent", "fixed_label", "ordered",
    "maximal", "shared_gumbel", "transport",
]

SUM_TOL = 1e-12       # allowed |sum(p) - 1| of an input marginal
RESIDUAL_TOL = 1e-12  # allowed max |row/column sum - marginal| of a plan
MIN_ENTRY = -1e-14    # smallest allowed plan entry
LP_TOL = 1e-10        # HiGHS primal/dual feasibility tolerance (its supported minimum)
GUMBEL_MAX_RATIO = 1e100


class CouplingError(FloatingPointError):
    """A plan failed its solver status, marginal or sign check."""


@dataclass(frozen=True, eq=False)
class Coupling:
    """A checked K x K plan (read-only, bytes-backed array) and its construction evidence.

    `seconds` is wall time of construction plus checks. `objective` (sum cost * plan in the
    caller's units) and `gap_estimate` (a float64 duality-gap diagnostic, not a certificate;
    see :func:`transport`) are set by :func:`transport` only.
    """

    method: str
    matrix: NDArray[np.float64]
    marginal_residual: float
    min_entry: float
    seconds: float
    objective: float | None = None
    gap_estimate: float | None = None


def _real_vector(name: str, value: object) -> NDArray[np.float64]:
    try:
        raw = np.asarray(value)
    except ValueError as exc:  # ragged nesting
        raise ValueError(f"{name} must be a flat sequence of numbers") from exc
    if raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must contain real numbers, got dtype {raw.dtype}")
    arr = raw.astype(np.float64)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError(f"{name} must be a non-empty 1-D sequence, got shape {arr.shape}")
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} must be finite, got {arr.tolist()}")
    return arr


def distribution(name: str, value: object) -> NDArray[np.float64]:
    """Validated float64 probability vector (never renormalised)."""
    arr = _real_vector(name, value)
    if (arr < 0.0).any():
        raise ValueError(f"{name} must be nonnegative, got {arr.tolist()}")
    total = math.fsum(arr.tolist())
    if abs(total - 1.0) > SUM_TOL:
        raise ValueError(f"{name} must sum to 1 within {SUM_TOL}, got {total!r}")
    return arr


def _pair(p: object, q: object) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    p, q = distribution("p", p), distribution("q", q)
    if len(p) != len(q):
        raise ValueError(f"p and q must have equal length, got {len(p)} and {len(q)}")
    return p, q


def _finish(method: str, matrix: NDArray[np.float64], p: NDArray[np.float64],
            q: NDArray[np.float64], start: float, objective: float | None = None,
            gap: float | None = None) -> Coupling:
    matrix = np.array(matrix, dtype=np.float64)
    if matrix.shape != (len(p), len(q)) or not np.isfinite(matrix).all():
        raise CouplingError(f"{method}: invalid plan {matrix.tolist()}")
    rows = [math.fsum([*row, -a]) for row, a in zip(matrix.tolist(), p.tolist())]
    cols = [math.fsum([*col, -b]) for col, b in zip(matrix.T.tolist(), q.tolist())]
    residual = max(abs(r) for r in rows + cols)  # exact differences, rounded once
    min_entry = float(matrix.min())
    if not (residual <= RESIDUAL_TOL and min_entry >= MIN_ENTRY):
        raise CouplingError(f"{method}: marginal residual {residual:.3e} (tol {RESIDUAL_TOL}) or "
                            f"minimum entry {min_entry:.3e} (tol {MIN_ENTRY}) failed")
    # An owning array's write flag can be set again; one over immutable bytes cannot.
    frozen = np.frombuffer(matrix.tobytes(), dtype=np.float64).reshape(matrix.shape)
    return Coupling(method, frozen, residual, min_entry, time.perf_counter() - start,
                    objective, gap)


def independent(p: object, q: object) -> Coupling:
    """pi = p outer q."""
    start = time.perf_counter()
    p, q = _pair(p, q)
    return _finish("independent", np.outer(p, q), p, q, start)


def _tiles(p: NDArray[np.float64], order: NDArray[np.intp]) -> tuple[NDArray, NDArray]:
    ends = np.cumsum(p[order])
    start, end = np.empty_like(p), np.empty_like(p)
    start[order] = np.concatenate(([0.0], ends[:-1]))
    end[order] = ends
    return start, end


def _overlap(method: str, p: NDArray[np.float64], q: NDArray[np.float64],
             order_p: NDArray[np.intp], order_q: NDArray[np.intp], start: float) -> Coupling:
    """pi[a, b] = |I_a intersect J_b|; I and J tile [0, 1] with lengths p, q in the given orders."""
    sp, ep = _tiles(p, order_p)
    sq, eq = _tiles(q, order_q)
    matrix = np.maximum(0.0, np.minimum(ep[:, None], eq[None, :]) - np.maximum(sp[:, None], sq[None, :]))
    return _finish(method, matrix, p, q, start)


def fixed_label(p: object, q: object) -> Coupling:
    """Shared uniform through both inverse CDFs in label order 0, 1, ..., K-1."""
    start = time.perf_counter()
    p, q = _pair(p, q)
    order = np.arange(len(p))
    return _overlap("fixed_label", p, q, order, order, start)


def ordered(p: object, q: object, keys_p: object, keys_q: object) -> Coupling:
    """Shared uniform with each world's actions ordered by ascending key, ties by action ID.

    The two orders are independent; with one scalar key per world this is monotone transport.
    """
    start = time.perf_counter()
    p, q = _pair(p, q)
    kp, kq = _real_vector("keys_p", keys_p), _real_vector("keys_q", keys_q)
    if len(kp) != len(p) or len(kq) != len(q):
        raise ValueError(f"keys must match the marginals' length {len(p)}")
    return _overlap("ordered", p, q, np.argsort(kp, kind="stable"), np.argsort(kq, kind="stable"),
                    start)


def maximal(p: object, q: object) -> Coupling:
    """Diagonal min(p, q) plus residual outer product / residual total (diagonal if p == q)."""
    start = time.perf_counter()
    p, q = _pair(p, q)
    diag = np.minimum(p, q)
    rest_p, rest_q = p - diag, q - diag
    total = math.fsum(rest_p.tolist())
    matrix = np.diag(diag)
    if total > 0.0:  # zero residual: the diagonal alone is the plan
        matrix = matrix + np.outer(rest_p, rest_q) / total
    return _finish("maximal", matrix, p, q, start)


def _gumbel_off_diagonal(p: list[float], q: list[float], i: int, j: int) -> float:
    """P(world p picks i, world q picks j), i != j, by the piecewise analytic integral."""
    lo, hi = p[j] / p[i], q[j] / q[i]
    if hi <= lo:
        return 0.0
    others = [k for k in range(len(p)) if k != i and k != j]
    cuts = sorted(c for c in ((p[k] / p[i]) / (q[k] / q[j]) for k in others) if lo < c < hi)
    grid = [lo, *cuts, hi]
    # The denominator is continuous and linear between cuts, so its endpoint values suffice.
    denom = [math.fsum([1.0, r, *(max(p[k] / p[i], r * q[k] / q[j]) for k in others)]) for r in grid]
    return math.fsum((b - a) / (da * db) for a, b, da, db in zip(grid, grid[1:], denom, denom[1:]))


def shared_gumbel(p: object, q: object) -> Coupling:
    """Joint law of argmax(log p + G) and argmax(log q + G) for one shared Gumbel vector G."""
    start = time.perf_counter()
    p, q = _pair(p, q)
    for name, v in (("p", p), ("q", q)):
        if not (v > 0.0).all():
            raise ValueError(f"shared_gumbel supports strictly positive {name} only, got {v.tolist()}")
        if v.max() / v.min() > GUMBEL_MAX_RATIO:
            raise ValueError(f"shared_gumbel supports max/min {name} ratio <= {GUMBEL_MAX_RATIO:g}")
    k, pl, ql = len(p), p.tolist(), q.tolist()
    matrix = np.empty((k, k))
    for i in range(k):
        for j in range(k):
            matrix[i, j] = (1.0 / math.fsum(max(pl[m] / pl[i], ql[m] / ql[i]) for m in range(k))
                            if i == j else _gumbel_off_diagonal(pl, ql, i, j))
    return _finish("shared_gumbel", matrix, p, q, start)


def transport(p: object, q: object, cost: object) -> Coupling:
    """Minimum-expected-cost plan by scipy linprog(method='highs'), with a gap estimate.

    Row minima, then column minima, are subtracted and the result is divided by its maximum
    (when positive). On plans with exactly the marginals p and q this changes the objective by
    a constant and a positive factor only, so the optimal plans are unchanged, while tiny or
    offset costs no longer fall below the solver's tolerances. The last column constraint is
    implied by the others and is dropped.

    `gap_estimate` is `objective` minus the Lagrangian lower bound at HiGHS's duals, in the
    caller's units. With row/column potentials u, v and reduced costs s = cost - u - v it is

        s.plan - sum(min(s, 0) * min(p_a, q_b)) + u.(row sums - p) + v.(column sums - q).

    The last two terms charge the plan's marginal residuals (up to 1e-12) at the scale of the
    potentials, which large costs magnify. In exact arithmetic, gap_estimate >= objective - the
    cost of every plan whose marginals are exactly p and q, and a negative value means the
    objective lies at least that far below all of them. It is a float64 diagnostic, not a
    certificate: rounding is not accounted for (of order 1e-16 * K * the cost range in the
    reduction, reduced costs and sums, and 1e-16 * max |cost| in `objective` itself); nothing
    bounds how far below the optimum `objective` may lie; and if p and q have different exact
    sums no such plan exists, so the inequality is vacuous.
    """
    start = time.perf_counter()
    p, q = _pair(p, q)
    k = len(p)
    try:
        raw = np.asarray(cost)
    except ValueError as exc:
        raise ValueError("cost must be a rectangular K x K array") from exc
    if raw.dtype.kind not in "iuf" or raw.shape != (k, k):
        raise ValueError(f"cost must be a real {k} x {k} array, got {raw.dtype} {raw.shape}")
    c = raw.astype(np.float64)
    if not np.isfinite(c).all():
        raise ValueError("cost must be finite")
    row_min = c.min(axis=1)
    reduced = c - row_min[:, None]
    col_min = reduced.min(axis=0)
    reduced = reduced - col_min[None, :]
    scale = float(reduced.max())
    if scale > 0.0:
        reduced = reduced / scale
    else:
        scale = 1.0  # every feasible plan is optimal
    a_eq = np.zeros((2 * k - 1, k * k))
    for a in range(k):
        a_eq[a, a * k:(a + 1) * k] = 1.0
    for b in range(k - 1):
        a_eq[k + b, b::k] = 1.0
    b_eq = np.concatenate((p, q[:-1]))
    res = linprog(reduced.ravel(), A_eq=a_eq, b_eq=b_eq, bounds=(0.0, None), method="highs",
                  options={"primal_feasibility_tolerance": LP_TOL,
                           "dual_feasibility_tolerance": LP_TOL})
    eqlin = getattr(res, "eqlin", None)
    if res.status != 0 or res.x is None or eqlin is None or getattr(eqlin, "marginals", None) is None:
        raise CouplingError(f"transport: HiGHS failed (status {res.status}): {res.message}")
    x = np.asarray(res.x, dtype=np.float64)
    y = np.asarray(eqlin.marginals, dtype=np.float64)
    if (x.shape != (k * k,) or y.shape != (2 * k - 1,)
            or not (np.isfinite(x).all() and np.isfinite(y).all())):
        raise CouplingError(f"transport: malformed or non-finite solver output {x.shape}, {y.shape}")
    plan = x.reshape(k, k)
    # In exact arithmetic cost = row_min + col_min + scale * (A^T y + red). A plan with marginals
    # exactly p and q has entries in [0, min(p_a, q_b)], so it costs at least row_min.p +
    # col_min.q + scale * lower. primal - lower = red.x - sum(min(red, 0) min(p, q)) + y.(A x - b)
    # charges the plan's residuals in reduced units; row_min and col_min charge the rest.
    red = reduced.ravel() - a_eq.T @ y
    lower = math.fsum([*(b_eq * y).tolist(),
                       *(np.minimum(red, 0.0) * np.minimum.outer(p, q).ravel()).tolist()])
    primal = math.fsum((reduced.ravel() * x).tolist())
    row_res = np.array([math.fsum([*row, -a]) for row, a in zip(plan.tolist(), p.tolist())])
    col_res = np.array([math.fsum([*col, -b]) for col, b in zip(plan.T.tolist(), q.tolist())])
    gap = math.fsum([scale * (primal - lower), *(row_min * row_res).tolist(),
                     *(col_min * col_res).tolist()])
    objective = math.fsum((c * plan).ravel().tolist())
    return _finish("transport", plan, p, q, start, objective, gap)
