"""Couplings: marginals on skewed and process-generated laws, immutable plans, hand plans,
shared-Gumbel masses against independent quadrature, a K = 2 logistic formula and sampled
counts, transport optimality under tiny/offset costs, gap estimates that charge marginal
residuals at the caller's cost scale, the label-matching counterexample and failure paths."""

from __future__ import annotations

import dataclasses
import math
import types
import warnings

import numpy as np
import pytest
from scipy.integrate import IntegrationWarning, quad

from pilot import couplings
from pilot.couplings import (CouplingError, fixed_label, independent, maximal, ordered,
                             shared_gumbel, transport)
from pilot.process import State, canonical_config, probs


def _softmax(logits):
    z = np.exp(np.asarray(logits, dtype=float) - max(logits))
    return tuple((z / z.sum()).tolist())


def _local(name, beta, theta):
    config = canonical_config(name, beta, 0.4)
    return tuple(probs(config, State(theta, (0.0,) * len(theta), 0)).tolist())


LAWS = {
    "skewed3": ((0.7, 0.2, 0.1), (0.05, 0.15, 0.8)),
    "extreme3": ((0.98, 0.01, 0.01), (1e-6, 0.5, 0.5 - 1e-6)),
    "reversed4": ((0.4, 0.3, 0.2, 0.1), (0.1, 0.2, 0.3, 0.4)),
    "softmax5": (_softmax((3.0, -2.0, 0.5, 1.5, -4.0)), _softmax((-1.0, 2.5, 0.0, -3.0, 1.0))),
    "process-B1": (_local("B1", 8.0, (2.0, -1.5)), _local("B1", 8.0, (-0.4, 0.0))),
    "process-A2": (_local("A2", 8.0, (0.9,)), _local("A2", 8.0, (-0.9,))),
}
LAW_CASES = pytest.mark.parametrize(("p", "q"), list(LAWS.values()), ids=list(LAWS))


def _all(p, q):
    k = len(p)
    cost = np.subtract.outer(np.linspace(0.0, 1.0, k), np.cos(np.arange(k))) ** 2
    return [independent(p, q), fixed_label(p, q), ordered(p, q, np.linspace(1.0, -1.0, k), [0.5] * k),
            maximal(p, q), shared_gumbel(p, q), transport(p, q, cost)]


def _second_moment(plan, u, v):
    return math.fsum((np.asarray(plan) * np.subtract.outer(u, v) ** 2).ravel().tolist())


@LAW_CASES
def test_every_coupling_has_the_prescribed_marginals(p, q):
    for c in _all(p, q):
        m = c.matrix
        assert m.shape == (len(p), len(q)) and not m.flags.writeable
        assert max(abs(math.fsum(row) - a) for row, a in zip(m.tolist(), p)) <= 1e-12
        assert max(abs(math.fsum(col) - b) for col, b in zip(m.T.tolist(), q)) <= 1e-12
        assert c.marginal_residual <= 1e-12 and c.min_entry == float(m.min())
        assert c.min_entry >= (-1e-14 if c.method == "transport" else 0.0)
        assert c.seconds >= 0.0
        assert (c.objective is None) == (c.gap_estimate is None) == (c.method != "transport")


@LAW_CASES
def test_plans_cannot_be_made_writable_again(p, q):
    """The residual/objective evidence describes the checked bytes; no view can be reopened."""
    for c in _all(p, q):
        before = c.matrix.tobytes()
        chain = [c.matrix]
        while isinstance(chain[-1].base, np.ndarray):
            chain.append(chain[-1].base)
        assert isinstance(chain[-1].base, bytes)  # immutable backing
        for arr in (*chain, c.matrix.T):
            with pytest.raises(ValueError):
                arr.setflags(write=True)
            with pytest.raises(ValueError):
                arr[...] = 0.0
        with pytest.raises(dataclasses.FrozenInstanceError):
            c.matrix = np.zeros_like(c.matrix)
        assert c.matrix.tobytes() == before and not c.matrix.flags.writeable


def test_hand_plans():
    assert np.array_equal(independent((0.3, 0.7), (0.6, 0.4)).matrix, np.outer((0.3, 0.7), (0.6, 0.4)))
    assert fixed_label((0.5, 0.5), (0.25, 0.75)).matrix.tolist() == [[0.25, 0.25], [0.0, 0.5]]
    # x order by keys (1, 0, 1) is 1, 0, 2 (tie by ID); y order by keys (0, 0, -1) is 2, 0, 1.
    got = ordered((0.2, 0.3, 0.5), (0.5, 0.25, 0.25), (1.0, 0.0, 1.0), (0.0, 0.0, -1.0)).matrix
    assert got == pytest.approx(np.array([[0.2, 0, 0], [0.05, 0, 0.25], [0.25, 0.25, 0]]), abs=1e-15)
    got = maximal((0.5, 0.3, 0.2), (0.2, 0.3, 0.5)).matrix
    assert got == pytest.approx(np.array([[0.2, 0, 0.3], [0, 0.3, 0], [0, 0, 0.2]]), abs=1e-15)
    # K = 2: shared Gumbel is a logistic threshold rule, hence the monotone (maximal) plan.
    got = shared_gumbel((0.7, 0.3), (0.4, 0.6)).matrix
    assert got == pytest.approx(np.array([[0.4, 0.3], [0.0, 0.3]]), abs=1e-15)


@LAW_CASES
def test_same_law_is_diagonal(p, q):
    del q
    k = len(p)
    for c in (fixed_label(p, p), maximal(p, p), shared_gumbel(p, p), ordered(p, p, range(k), range(k))):
        assert np.count_nonzero(c.matrix - np.diag(np.diag(c.matrix))) == 0
        assert np.diag(c.matrix) == pytest.approx(np.array(p), rel=0.0, abs=1e-15)
    assert maximal(p, p).matrix.tolist() == np.diag(p).tolist()


def _quad_off_diagonal(p, q, i, j):
    """P(i, j), i != j, as the exponential-race integral over r = E_j / E_i in (lo, hi) of
    (1 + r + sum_k max(p_k/p_i, r q_k/q_j))**-2, by numerical quadrature in t = log r (the range
    can span many decades) with the max() kinks as breakpoints. Non-convergence fails the test."""
    lo, hi = p[j] / p[i], q[j] / q[i]
    if hi <= lo:
        return 0.0
    others = [k for k in range(len(p)) if k not in (i, j)]

    def integrand(t):
        r = math.exp(t)
        return r / (1.0 + r + sum(max(p[k] / p[i], r * q[k] / q[j]) for k in others)) ** 2

    a, b = math.log(lo), math.log(hi)
    kinks = sorted({t for t in (math.log(p[k] / p[i]) - math.log(q[k] / q[j]) for k in others) if a < t < b})
    with warnings.catch_warnings():
        warnings.simplefilter("error", IntegrationWarning)
        out = quad(integrand, a, b, points=kinks or None, epsabs=1e-14, epsrel=1e-12, limit=500,
                   full_output=1)
    assert len(out) == 3, f"reference quadrature did not converge: {out[3:]}"
    value, abserr, _ = out
    assert abserr <= 1e-12, f"reference quadrature error estimate {abserr:.2e} is too large"
    return value


@LAW_CASES
def test_shared_gumbel_matches_independent_quadrature(p, q):
    pi = shared_gumbel(p, q).matrix
    for i in range(len(p)):
        assert pi[i, i] == pytest.approx(1.0 / sum(max(p[k] / p[i], q[k] / q[i]) for k in range(len(p))),
                                         rel=1e-14)
        for j in range(len(p)):
            if i != j:
                assert abs(pi[i, j] - _quad_off_diagonal(p, q, i, j)) <= 1e-10


@pytest.mark.parametrize(("p", "q"), [LAWS["skewed3"], ((0.5, 0.3, 0.2), (0.2, 0.3, 0.5)),
                                      LAWS["reversed4"]])
def test_shared_gumbel_matches_fixed_seed_sampled_counts(p, q):
    n, k = 400_000, len(p)
    g = np.random.default_rng(20260924).gumbel(size=(n, k))
    a, b = np.argmax(np.log(p) + g, axis=1), np.argmax(np.log(q) + g, axis=1)
    counts = np.zeros((k, k))
    np.add.at(counts, (a, b), 1.0)
    pi = shared_gumbel(p, q).matrix
    assert np.all(np.abs(counts / n - pi) <= 5.0 * np.sqrt(pi * (1.0 - pi) / n) + 1e-12)


def test_transport_matches_monotone_plan_under_tiny_and_offset_costs():
    p, q = (0.15, 0.6, 0.25), (0.5, 0.1, 0.4)
    u, v = np.array([0.1, 0.9, 0.4]), np.array([0.3, 0.0, 0.7])
    monotone = ordered(p, q, u, v).matrix
    base = _second_moment(monotone, u, v)
    cost = np.subtract.outer(u, v) ** 2
    for factor, offset in ((1.0, 0.0), (1e-13, 0.0), (1e-11, 0.75), (1e6, -3.0)):
        c = transport(p, q, factor * cost + offset)
        assert c.matrix == pytest.approx(monotone, abs=1e-12)  # strictly convex cost: unique optimum
        assert c.objective == pytest.approx(factor * base + offset, rel=1e-12, abs=1e-12 * factor)
        # Reduced-problem gap (scales with factor) plus the charge for 2K marginal residuals at
        # potentials of size |offset| + O(K * factor).
        allowance = 6.0 * (abs(offset) + 10.0 * factor) * c.marginal_residual
        assert abs(c.gap_estimate) <= 1e-12 * factor + allowance


@pytest.mark.parametrize("sign", [-1.0, 1.0], ids=["cost-minus-2**48", "cost-plus-2**48"])
def test_transport_gap_estimate_charges_marginal_residuals_in_callers_units(sign):
    """Review counterexample. Row 0 has mass exactly 2**-48 at cost sign * 2**48 per unit and all
    other costs are 0, so every plan with marginals exactly p and q costs `sign`. All reduced
    costs vanish and HiGHS (scipy 1.17.1) drops the row-0 mass, below its 1e-10 tolerance; the
    residual 2**-48 passes the 1e-12 check and the plan costs 0. The old reduced-cost gap, 0,
    'certified' 0 - (-1) <= 0. The estimate now charges the residual: +1 flags an objective 1
    above every such plan; -1 says the objective lies at least 1 below them (the dual side
    cannot say how far below in general)."""
    p, q = (2.0 ** -48, 0.5, 0.5 - 2.0 ** -48), (0.25, 0.25, 0.5)
    c = transport(p, q, [[sign * 2.0 ** 48] * 3, [0.0] * 3, [0.0] * 3])
    assert c.marginal_residual == 2.0 ** -48 and c.objective == 0.0  # pinned solver's dropped-mass plan
    assert c.gap_estimate == pytest.approx(c.objective - sign, abs=1e-12)  # >= objective - optimum


def test_label_matching_counterexample():
    """Uniform actions with terminal scores (0, 1) versus (1, 0): label matching gives second
    moment 1, crossing gives 0. Scalar sorting finds the crossing; it is an ordinary baseline."""
    p = q = (0.5, 0.5)
    u, v = (0.0, 1.0), (1.0, 0.0)
    assert _second_moment(fixed_label(p, q).matrix, u, v) == 1.0
    assert _second_moment(maximal(p, q).matrix, u, v) == 1.0
    assert _second_moment(ordered(p, q, u, v).matrix, u, v) == 0.0
    ot = transport(p, q, np.subtract.outer(u, v) ** 2)
    assert abs(ot.objective) <= 1e-15
    assert ot.matrix == pytest.approx(np.array([[0, 0.5], [0.5, 0]]), abs=1e-15)


def _fake(x, status=0):
    return types.SimpleNamespace(status=status, message="fake", x=None if x is None else np.array(x),
                                 eqlin=types.SimpleNamespace(marginals=np.zeros(3)))


@pytest.mark.parametrize("result", [
    _fake(None, status=2),
    _fake([0.25, 0.25, 0.25, 0.25], status=1),
    _fake([0.5 + 1e-9, 0.0, 0.0, 0.5]),
    _fake([0.5 + 1e-13, -1e-13, -1e-13, 0.5 + 1e-13]),
    _fake([0.5, 0.0, 0.0, math.nan]),
], ids=["infeasible", "iteration-limit", "residual", "negative-mass", "nan"])
def test_transport_rejects_failed_or_wrong_solutions(monkeypatch, result):
    monkeypatch.setattr(couplings, "linprog", lambda *args, **kwargs: result)
    with pytest.raises(CouplingError):
        transport((0.5, 0.5), (0.5, 0.5), [[0.0, 1.0], [1.0, 0.0]])


BAD_LAWS = [((0.5, 0.6), ValueError), ((1.2, -0.2), ValueError), ((math.nan, 1.0), ValueError),
            ((0.5, 0.5 + 1e-9), ValueError), ((), ValueError), (((0.5, 0.5),), ValueError),
            ([[0.5], [0.5, 0.0]], ValueError), (("a", "b"), TypeError), ((True, False), TypeError)]


@pytest.mark.parametrize(("bad", "error"), BAD_LAWS)
def test_invalid_marginals_are_rejected(bad, error):
    good = (0.5, 0.5)
    for build in (independent, fixed_label, maximal, shared_gumbel,
                  lambda p, q: ordered(p, q, (0, 1), (0, 1)),
                  lambda p, q: transport(p, q, [[0.0, 1.0], [1.0, 0.0]])):
        with pytest.raises(error):
            build(bad, good)
        with pytest.raises(error):
            build(good, bad)


def test_invalid_shapes_keys_costs_and_gumbel_domain_are_rejected():
    p = (0.5, 0.5)
    with pytest.raises(ValueError):
        independent((1.0,), p)
    with pytest.raises(ValueError, match="strictly positive"):
        shared_gumbel((1.0, 0.0), p)
    with pytest.raises(ValueError, match="ratio"):
        shared_gumbel((1.0 - 1e-120, 1e-120), p)
    for keys in ((0.0, math.nan), (0.0, 1.0, 2.0), ("a", "b")):
        with pytest.raises((ValueError, TypeError)):
            ordered(p, p, keys, (0.0, 1.0))
    for cost in ([[0.0, 1.0, 2.0], [1.0, 0.0, 2.0]], [[0.0, math.inf], [1.0, 0.0]], [["a", "b"], ["c", "d"]]):
        with pytest.raises(ValueError):
            transport(p, p, cost)
