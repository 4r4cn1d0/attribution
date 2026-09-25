"""Core tests for pilot.exact: manual H = 0 / H = 1 formulas, exhaustive enumeration,
intervention semantics, input validation and an independent 50-digit mpmath reference."""

from __future__ import annotations

import dataclasses
import itertools
import math

import mpmath
import numpy as np
import pytest

from pilot.exact import OperationCounts, attribution, terminal_law
from pilot.process import State, apply_event, canonical_config, intervention_pair, probs, score

R2 = 1.0 / math.sqrt(2.0)
A1 = canonical_config("A1", 3.0, 0.4, mu=0.5, weight_decay=0.1, offsets=(0.1, -0.2, 0.0))
B1 = canonical_config("B1", 3.0, 0.4, mu=0.5, weight_decay=0.1, q=(0.6, 0.8))
A1_START = State((0.2,), (0.05,), 2)
B1_START = State((0.2, -0.1), (0.05, -0.02), 2)
CASES = pytest.mark.parametrize(("config", "start"), [(A1, A1_START), (B1, B1_START)], ids=["A1", "B1"])


def _dot(u, v):
    return sum(x * y for x, y in zip(u, v))


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def _check_h1(law, p, thetas, momenta, scores, counter):
    assert [leaf.path for leaf in law.leaves] == [(0,), (1,), (2,)]
    for leaf, p_a, theta, momentum, s in zip(law.leaves, p, thetas, momenta, scores):
        assert leaf.mass == pytest.approx(p_a, rel=1e-13)
        assert leaf.state.theta == pytest.approx(theta, rel=1e-13, abs=1e-15)
        assert leaf.state.momentum == pytest.approx(momentum, rel=1e-13, abs=1e-15)
        assert leaf.state.counter == counter
        assert leaf.score == pytest.approx(s, rel=1e-13)
    assert law.mass == pytest.approx(1.0, abs=1e-14)
    assert law.mean == pytest.approx(sum(a * b for a, b in zip(p, scores)), rel=1e-13)
    assert law.second_moment == pytest.approx(sum(a * b * b for a, b in zip(p, scores)), rel=1e-13)
    assert law.operations == OperationCounts(probs=1, apply_event=3, score=3)


@CASES
def test_h0_is_the_supplied_state(config, start):
    law = terminal_law(config, start, 0)
    (leaf,) = law.leaves
    assert leaf.path == () and leaf.mass == 1.0 and leaf.state is start
    assert leaf.score == pytest.approx(_sigmoid(_dot(config.q, start.theta)), rel=1e-14)
    assert (law.horizon, law.mass, law.mean) == (0, 1.0, leaf.score)
    assert law.second_moment == leaf.score * leaf.score
    assert law.operations == OperationCounts(probs=0, apply_event=0, score=1)


def test_h1_manual_formulas_family_a():
    beta, eta, mu, decay, offsets = 3.0, 0.4, 0.5, 0.1, (0.1, -0.2, 0.0)
    phi, targets, theta, m = (-1.0, 0.0, 1.0), (-1.0, 0.0, 1.0), 0.2, 0.05
    z = [math.exp(beta * phi[a] * theta + offsets[a]) for a in range(3)]
    p = [x / sum(z) for x in z]
    m1 = [mu * m + (theta - targets[a]) for a in range(3)]
    t1 = [(1.0 - eta * decay) * theta - eta * m1[a] for a in range(3)]
    s = [_sigmoid(t) for t in t1]
    law = terminal_law(A1, A1_START, 1)
    _check_h1(law, p, [(t,) for t in t1], [(x,) for x in m1], s, A1_START.counter + 1)


def test_h1_manual_formulas_family_b():
    beta, eta, mu, decay, q = 3.0, 0.4, 0.5, 0.1, (0.6, 0.8)
    phi, targets = ((1.0, 0.0), (0.0, 1.0), (R2, R2)), (1.0, -1.0, 0.5)
    theta, m = (0.2, -0.1), (0.05, -0.02)
    z = [math.exp(beta * _dot(phi[a], theta)) for a in range(3)]
    p = [x / sum(z) for x in z]
    m1 = [tuple(mu * m[i] + (_dot(phi[a], theta) - targets[a]) * phi[a][i] for i in range(2))
          for a in range(3)]
    t1 = [tuple((1.0 - eta * decay) * theta[i] - eta * m1[a][i] for i in range(2)) for a in range(3)]
    s = [_sigmoid(_dot(q, t)) for t in t1]
    _check_h1(terminal_law(B1, B1_START, 1), p, t1, m1, s, B1_START.counter + 1)


@pytest.mark.parametrize("H", range(6))
@CASES
def test_enumerates_all_3_pow_h_paths_with_unit_mass(config, start, H):
    law = terminal_law(config, start, H)
    assert law.horizon == H and len(law.leaves) == 3 ** H
    assert [leaf.path for leaf in law.leaves] == list(itertools.product(range(3), repeat=H))
    assert law.mass == pytest.approx(1.0, abs=1e-12)
    assert law.mean == math.fsum(leaf.mass * leaf.score for leaf in law.leaves)
    assert 0.0 < law.second_moment <= law.mean < 1.0
    assert law.operations == OperationCounts(
        probs=(3 ** H - 1) // 2, apply_event=(3 ** (H + 1) - 3) // 2, score=3 ** H)
    for leaf in law.leaves:  # replay: every step uses its own state's probs and weight 1
        state, mass = start, 1.0
        for a in leaf.path:
            mass *= float(probs(config, state)[a])
            state = apply_event(config, state, a, 1.0)
        assert (leaf.mass, leaf.state, leaf.score) == (mass, state, score(config, state))
        assert leaf.state.counter == start.counter + H


@pytest.mark.parametrize("H", range(4))
@CASES
def test_alpha_zero_gives_zero_delta(config, start, H):
    for action in range(3):
        result = attribution(config, start, action, 0.0, H)
        assert result.delta == 0.0
        assert result.suppressed == result.ordinary


def test_delta_is_conditional_suppressed_minus_ordinary():
    result = attribution(A1, A1_START, 2, 1.0, 2)
    suppressed, ordinary = intervention_pair(A1, A1_START, 2, 1.0)
    assert result.suppressed == terminal_law(A1, suppressed, 2)
    assert result.ordinary == terminal_law(A1, ordinary, 2)
    assert result.delta == result.suppressed.mean - result.ordinary.mean
    assert result.action_probability == float(probs(A1, A1_START)[2])
    assert (result.action, result.alpha) == (2, 1.0)
    assert result.operations == OperationCounts(probs=1 + 2 * 4, apply_event=2 + 2 * 12, score=2 * 9)


def test_inputs_are_unchanged_and_results_are_immutable():
    before = (B1_START.theta, B1_START.momentum, B1_START.counter)
    law = terminal_law(B1, B1_START, 2)
    result = attribution(B1, B1_START, 1, 0.5, 2)
    assert (B1_START.theta, B1_START.momentum, B1_START.counter) == before
    assert all(leaf.state is not B1_START and leaf.state.counter == 4 for leaf in law.leaves)
    leaf = law.leaves[0]
    assert isinstance(law.leaves, tuple) and isinstance(leaf.state.theta, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        leaf.state.theta = (0.0, 0.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        law.mean = 0.0
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.delta = 0.0
    with pytest.raises(AttributeError):
        leaf.mass = 0.0


@pytest.mark.parametrize("action", range(3))
def test_weight_zero_still_decays_and_advances(action):
    config = canonical_config("A1", 3.0, 0.1, mu=0.9, weight_decay=0.1)
    pre = State((0.2,), (0.3,), 5)
    for post in (apply_event(config, pre, action, 0.0),
                 intervention_pair(config, pre, action, 1.0)[0],
                 attribution(config, pre, action, 1.0, 0).suppressed.leaves[0].state):
        assert post.momentum == pytest.approx((0.27,), abs=1e-15)
        assert post.theta == pytest.approx((0.171,), abs=1e-15)
        assert post.counter == 6


@pytest.mark.parametrize(("H", "error"), [(-1, ValueError), (1.0, TypeError), (True, TypeError),
                                          ("2", TypeError), (None, TypeError)])
def test_invalid_horizon_is_rejected(H, error):
    with pytest.raises(error):
        terminal_law(A1, A1_START, H)
    with pytest.raises(error):
        attribution(A1, A1_START, 0, 1.0, H)


def test_invalid_config_or_state_is_rejected():
    with pytest.raises(TypeError):
        terminal_law("A1", A1_START, 1)
    with pytest.raises(TypeError):
        terminal_law(A1, (0.2,), 1)
    with pytest.raises(ValueError):
        terminal_law(A1, B1_START, 0)
    with pytest.raises(TypeError):
        attribution(A1, (0.2,), 0, 1.0, 1)
    with pytest.raises(ValueError):
        attribution(B1, A1_START, 0, 1.0, 1)


@pytest.mark.parametrize(("action", "alpha", "error"), [
    (3, 1.0, ValueError), (-1, 1.0, ValueError), (1.0, 1.0, TypeError), (True, 1.0, TypeError),
    (0, 1.5, ValueError), (0, -0.1, ValueError), (0, math.nan, ValueError), (0, True, TypeError),
])
def test_invalid_action_or_alpha_is_rejected(action, alpha, error):
    with pytest.raises(error):
        attribution(A1, A1_START, action, alpha, 1)


def test_non_finite_numerics_raise():
    start = State((10.0,), (0.0,), 0)
    huge_beta = canonical_config("A1", 1e308, 0.4)
    huge_decay = canonical_config("A1", 1.0, 1.0, weight_decay=1e308)
    with np.errstate(all="ignore"):
        with pytest.raises(FloatingPointError):
            terminal_law(huge_beta, start, 1)
        with pytest.raises(FloatingPointError):
            attribution(huge_beta, start, 0, 1.0, 0)
        with pytest.raises(ValueError, match="finite"):
            terminal_law(huge_decay, start, 1)


@pytest.mark.parametrize(("mass_error", "H"), [(5e-10, 1), (8e-13, 2)])
def test_rejects_local_or_accumulated_probability_mass_error(monkeypatch, mass_error, H):
    # The second fixture passes the local guard but fails after two rounds.
    monkeypatch.setattr("pilot.exact.probs", lambda config, state:
                        np.array([1 / 3, 1 / 3, 1 / 3 + mass_error]))
    with pytest.raises(FloatingPointError):
        terminal_law(A1, A1_START, H)


# Independent reference: the documented process re-derived from its formulas in 50-digit
# mpmath arithmetic. It never calls pilot.process or pilot.exact.
def _ref_spec(name, beta, eta, mu=0.0, weight_decay=0.0, offsets=(0.0, 0.0, 0.0), q=None):
    mpf, r = mpmath.mpf, 1 / mpmath.sqrt(2)
    family, phi, targets = {"A1": ("A", [[-1], [0], [1]], [-1, 0, 1]),
                            "B1": ("B", [[1, 0], [0, 1], [r, r]], [1, -1, 0.5])}[name]
    q = [1] + [0] * (len(phi[0]) - 1) if q is None else q
    return {"family": family, "phi": [[mpf(x) for x in row] for row in phi],
            "targets": [mpf(x) for x in targets], "beta": mpf(beta), "eta": mpf(eta),
            "mu": mpf(mu), "decay": mpf(weight_decay), "offsets": [mpf(x) for x in offsets],
            "q": [mpf(x) for x in q]}


def _ref_step(spec, theta, m, a, w):
    phi_a, t_a = spec["phi"][a], spec["targets"][a]
    if spec["family"] == "A":
        grad = [theta[0] - t_a]
    else:
        residual = mpmath.fsum(x * y for x, y in zip(phi_a, theta)) - t_a
        grad = [residual * x for x in phi_a]
    m = [spec["mu"] * mi + w * gi for mi, gi in zip(m, grad)]
    return [(1 - spec["eta"] * spec["decay"]) * ti - spec["eta"] * mi for ti, mi in zip(theta, m)], m


def _ref_policy(spec, theta):
    z = [mpmath.exp(spec["beta"] * mpmath.fsum(x * y for x, y in zip(row, theta)) + o)
         for row, o in zip(spec["phi"], spec["offsets"])]
    return [x / mpmath.fsum(z) for x in z]


def _ref_leaves(spec, theta, m, h, path, mass):
    if h == 0:
        x = mpmath.fsum(qi * ti for qi, ti in zip(spec["q"], theta))
        return [(path, mass, 1 / (1 + mpmath.exp(-x)))]
    leaves = []
    for a, p_a in enumerate(_ref_policy(spec, theta)):
        leaves += _ref_leaves(spec, *_ref_step(spec, theta, m, a, 1), h - 1, path + (a,), mass * p_a)
    return leaves


REF_CASES = {
    # Required: beta 3, eta 0.4, zero pre-momentum, observed action 2 (zero-based), alpha 1, H 2.
    "A1": ("A1", (0.2,), (0.0,), {}, 1.0, 2),
    "B1": ("B1", (0.2, -0.1), (0.0, 0.0), {}, 1.0, 2),
    # Extra: pre-momentum, momentum, weight decay, offsets or q, and partial suppression.
    "A1-momentum": ("A1", (0.2,), (0.05,),
                    {"mu": 0.5, "weight_decay": 0.1, "offsets": (0.1, -0.2, 0.0)}, 0.5, 3),
    "B1-momentum": ("B1", (0.2, -0.1), (0.05, -0.02),
                    {"mu": 0.5, "weight_decay": 0.1, "q": (0.6, 0.8)}, 0.5, 2),
}


@pytest.mark.parametrize("case", list(REF_CASES.values()), ids=list(REF_CASES))
def test_matches_independent_50_digit_reference(case):
    name, theta, momentum, options, alpha, H = case
    beta, eta, action = 3.0, 0.4, 2
    config = canonical_config(name, beta, eta, **options)
    result = attribution(config, State(theta, momentum, 0), action, alpha, H)
    with mpmath.workdps(50):
        spec = _ref_spec(name, beta, eta, **options)
        theta0, m0 = [mpmath.mpf(x) for x in theta], [mpmath.mpf(x) for x in momentum]
        p_action = _ref_policy(spec, theta0)[action]
        worlds = [_ref_leaves(spec, *_ref_step(spec, theta0, m0, action, w), H, (), mpmath.mpf(1))
                  for w in (1 - mpmath.mpf(alpha), mpmath.mpf(1))]
        means = [mpmath.fsum(p * s for _, p, s in leaves) for leaves in worlds]
        seconds = [mpmath.fsum(p * s * s for _, p, s in leaves) for leaves in worlds]
        delta = means[0] - means[1]
    for law, leaves, mean, second in zip((result.suppressed, result.ordinary), worlds, means, seconds):
        assert [leaf.path for leaf in law.leaves] == [path for path, _, _ in leaves]
        for leaf, (_, p, s) in zip(law.leaves, leaves):
            assert abs(leaf.mass - float(p)) <= 1e-12 and abs(leaf.score - float(s)) <= 1e-12
        assert abs(law.mean - float(mean)) <= 1e-10
        assert abs(law.second_moment - float(second)) <= 1e-10
    assert abs(result.delta - float(delta)) <= 1e-10
    assert abs(result.action_probability - float(p_action)) <= 1e-12
    # Scaling delta by the action probability would move it far outside the tolerance.
    assert abs(float(delta)) * (1.0 - float(p_action)) > 1e-6
