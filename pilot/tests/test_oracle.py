"""Pair enumeration, co-adapted Bellman oracle and terminal OT bound: H0/H1 hand results, pair
means against the separately enumerated marginal Delta, oracle <= every ordinary coupling,
terminal OT <= oracle with equality at H1 (fixed tolerance; gap estimates are never slack),
zero-variance cells, the single-cell CLI and its size guard before any enumeration."""

from __future__ import annotations

import dataclasses
import itertools
import json
import math

import numpy as np
import pytest

from pilot import headroom
from pilot.exact import attribution
from pilot.pair import ORDINARY_METHODS, oracle, pair_moments, supported_horizon, terminal_ot
from pilot.process import apply_event, canonical_config, initial_state, intervention_pair, probs, score

R2 = 1.0 / math.sqrt(2.0)
# (structure, beta, eta, initial coordinate, zero-based observed action, alpha, H)
CELLS = {
    "A1-beta0-H2": ("A1", 0.0, 0.4, 0.4, 0, 1.0, 2),
    "A2-beta8-H2": ("A2", 8.0, 0.1, -0.4, 2, 1.0, 2),
    "A3-beta3-H2-alpha0.25": ("A3", 3.0, 0.4, 0.0, 0, 0.25, 2),
    "B1-beta8-H2": ("B1", 8.0, 0.4, 0.4, 1, 1.0, 2),
    "B2-beta0-H2": ("B2", 0.0, 0.1, 0.0, 2, 1.0, 2),
    "B2-beta8-H1": ("B2", 8.0, 0.4, -0.4, 0, 1.0, 1),
    "B1-beta3-H3": ("B1", 3.0, 0.4, 0.0, 2, 1.0, 3),
}


def _cell(structure, beta, eta, c, action, alpha, H):
    config = canonical_config(structure, beta, eta)
    return config, initial_state(config, (c,) + (0.0,) * (config.dim - 1)), action, alpha, H


def _sigmoid(t):
    return 1.0 / (1.0 + math.exp(-t))


def _hand_a(structure, beta, eta, c, action):
    """Family A by hand (mu = decay = 0): suppressed x0 = c, ordinary y0 = (1-eta)c + eta v."""
    phi, v = (-1.0, 0.0, 1.0), {"A1": (-1.0, 0.0, 1.0), "A2": (0.0, 1.0, -1.0), "A3": (1.0, 0.0, -1.0)}[structure]

    def law(theta):
        z = [math.exp(beta * f * theta) for f in phi]
        return [w / sum(z) for w in z], [_sigmoid((1.0 - eta) * theta + eta * va) for va in v]

    x0, y0 = c, (1.0 - eta) * c + eta * v[action]
    return law(x0), law(y0), _sigmoid(x0) - _sigmoid(y0)


def _quantile_cost(pa, sa, pb, sb):
    """Integral over u in (0, 1) of (F^-1(u) - G^-1(u))**2, by merging the two sorted CDFs."""
    orders = [sorted(range(len(s)), key=s.__getitem__) for s in (sa, sb)]
    cums = [np.cumsum([p[i] for i in order]) for p, order in zip((pa, pb), orders)]
    total, prev = [], 0.0
    for cut in sorted(set(cums[0].tolist()) | set(cums[1].tolist())):
        mid = 0.5 * (prev + cut)
        i, j = (min(int(np.searchsorted(cum, mid, side="right")), len(cum) - 1) for cum in cums)
        total.append((cut - prev) * (sa[orders[0][i]] - sb[orders[1][j]]) ** 2)
        prev = cut
    return math.fsum(total)


@pytest.mark.parametrize("cell", list(CELLS.values()), ids=list(CELLS))
def test_pair_oracle_and_terminal_bound_agree_with_marginal_truth(cell):
    args = _cell(*cell)
    H = cell[-1]
    truth = attribution(*args)
    s, o = truth.suppressed, truth.ordinary
    best, lower = oracle(*args), terminal_ot(*args)
    slack = 1e-12  # fixed: a float64 gap estimate is not a certificate and never widens it
    for method in ORDINARY_METHODS:
        r = pair_moments(method, *args)
        assert r.method == method and r.horizon == H
        assert abs(r.mean - truth.delta) <= 1e-10
        assert r.variance >= 0.0 and r.variance_correction <= 1e-14
        assert r.variance == pytest.approx(r.second_moment - r.mean ** 2, abs=1e-14)
        d = r.diagnostics
        assert d.max_marginal_residual <= 1e-12 and d.min_entry >= -1e-14
        assert d.score == 2 * d.leaves and d.probs == 2 * d.internal_nodes == 2 * d.couplings
        assert d.lp_solves == (d.couplings if method == "distance" else 0)
        assert best.second_moment <= r.second_moment + slack
        if method == "independent":  # product of the two marginal path laws
            assert d.leaves == 9 ** H and d.internal_nodes == (9 ** H - 1) // 8
            assert r.second_moment == pytest.approx(
                s.second_moment - 2.0 * s.mean * o.mean + o.second_moment, abs=1e-12)
    assert abs(best.mean - truth.delta) <= 1e-10 and abs(lower.mean - truth.delta) <= 1e-10
    assert lower.second_moment <= best.second_moment + 1e-12
    if H == 1:
        assert best.second_moment == pytest.approx(lower.second_moment, abs=slack)
    d = best.diagnostics
    assert d.internal_nodes == d.lp_solves == (9 ** H - 1) // 8 and d.leaves == 9 ** H
    assert d.apply_event == 2 + 6 * d.internal_nodes and d.score == 2 * d.leaves
    assert d.max_marginal_residual <= 1e-12 and d.min_entry >= -1e-14
    assert abs(best.suboptimality_estimate) <= 1e-12 and d.max_gap_estimate <= 1e-12
    assert best.variance >= 0.0 and lower.variance >= 0.0


@pytest.mark.parametrize("structure", ["A1", "B1"])
def test_h0_hand_results(structure):
    args = _cell(structure, 3.0, 0.4, 0.4, 2, 1.0, 0)
    if structure == "A1":
        d = _sigmoid(0.4) - _sigmoid(0.6 * 0.4 + 0.4 * 1.0)
    else:  # phi_2 = (1, 1)/sqrt(2), r_2 = 0.5, q = e1
        residual = 0.4 * R2 - 0.5
        d = _sigmoid(0.4) - _sigmoid(0.4 - 0.4 * residual * R2)
    results = [pair_moments(m, *args) for m in ORDINARY_METHODS] + [oracle(*args), terminal_ot(*args)]
    for r in results:
        assert r.mean == pytest.approx(d, abs=1e-15)
        assert r.second_moment == pytest.approx(d * d, abs=1e-15)
        assert r.variance == 0.0 and r.variance_correction == 0.0
    best = results[-2]
    assert best.root_plan is None and best.root_cost is None and best.suboptimality_estimate == 0.0
    assert (best.diagnostics.internal_nodes, best.diagnostics.leaves, best.diagnostics.min_entry) == (0, 1, None)


@pytest.mark.parametrize(("structure", "beta", "action"), [("A2", 8.0, 1), ("A1", 0.0, 2), ("A3", 3.0, 0)])
def test_h1_oracle_by_hand(structure, beta, action):
    (px, s), (py, t), _ = _hand_a(structure, beta, 0.4, 0.4, action)
    args = _cell(structure, beta, 0.4, 0.4, action, 1.0, 1)
    best = oracle(*args)
    assert best.root_p == pytest.approx(px, rel=1e-13) and best.root_q == pytest.approx(py, rel=1e-13)
    cost, plan = np.array(best.root_cost), np.array(best.root_plan)
    assert cost == pytest.approx(np.subtract.outer(s, t) ** 2, abs=1e-15)
    assert plan.sum(axis=1) == pytest.approx(px, abs=1e-12)
    assert plan.sum(axis=0) == pytest.approx(py, abs=1e-12)
    assert math.fsum((plan * cost).ravel().tolist()) == pytest.approx(best.second_moment, abs=1e-16)
    manual = _quantile_cost(px, s, py, t)
    assert best.second_moment == pytest.approx(manual, abs=1e-13)
    assert terminal_ot(*args).second_moment == pytest.approx(manual, abs=1e-13)
    independent = math.fsum(px[a] * py[b] * (s[a] - t[b]) ** 2 for a in range(3) for b in range(3))
    assert pair_moments("independent", *args).second_moment == pytest.approx(independent, abs=1e-14)
    # Family A: sorting by target orders both worlds' successor scores, so at H = 1 the
    # ordinary 'ordered' baseline already attains the oracle (no novelty from label order).
    assert pair_moments("ordered", *args).second_moment == pytest.approx(best.second_moment, abs=1e-13)


ZERO_CELLS = {
    "A1-alpha0": ("A1", 8.0, 0.4, 0.4, 1, 0.0, 2),
    "B2-alpha0": ("B2", 8.0, 0.4, 0.4, 1, 0.0, 2),
    "A1-zero-gradient": ("A1", 3.0, 0.4, 0.0, 1, 1.0, 2),  # theta0 = target: identical worlds
    "B2-zero-gradient": ("B2", 3.0, 0.4, 0.0, 1, 1.0, 2),  # phi . theta0 = r = 0
}


@pytest.mark.parametrize("cell", list(ZERO_CELLS.values()), ids=list(ZERO_CELLS))
def test_identical_worlds_give_zero_variance(cell):
    args = _cell(*cell)
    assert attribution(*args).delta == 0.0
    for method in ("fixed_label", "ordered", "maximal", "shared_gumbel"):
        r = pair_moments(method, *args)
        assert (r.mean, r.second_moment, r.variance) == (0.0, 0.0, 0.0)
        assert r.diagnostics.leaves == 3 ** cell[-1]  # the diagonal plan visits only matched pairs
    assert pair_moments("distance", *args).second_moment <= 1e-15
    assert pair_moments("independent", *args).variance > 1e-6
    best, lower = oracle(*args), terminal_ot(*args)
    # LP vertices may carry +-1e-17 off-diagonal mass, so the oracle is zero only to roundoff.
    assert abs(best.mean) <= 1e-15 and abs(best.second_moment) <= 1e-15 and best.variance <= 1e-15
    assert (lower.mean, lower.second_moment) == (0.0, 0.0)


_CELLS3 = [(a, b) for a in range(3) for b in range(3)]


def _brute_transport(p, q, cost):
    """LP optimum without a solver: minimum over all basic feasible plans (rank-5 supports)."""
    rows = np.zeros((6, 9))
    for i, (a, b) in enumerate(_CELLS3):
        rows[a, i] = rows[3 + b, i] = 1.0
    rhs, best = np.concatenate((p, q)), math.inf
    for support in itertools.combinations(range(9), 5):
        m = rows[:, support]
        if np.linalg.matrix_rank(m) < 5:
            continue
        x = np.linalg.lstsq(m, rhs, rcond=None)[0]
        if np.abs(m @ x - rhs).max() <= 1e-12 and x.min() >= -1e-12:
            best = min(best, math.fsum(xi * cost[_CELLS3[s][0]][_CELLS3[s][1]] for xi, s in zip(x, support)))
    return best


def _brute_oracle(config, x, y, h):
    if h == 0:
        return (score(config, x) - score(config, y)) ** 2
    xs, ys = ([apply_event(config, s, a) for a in range(3)] for s in (x, y))
    cost = [[_brute_oracle(config, u, v, h - 1) for v in ys] for u in xs]
    return _brute_transport(probs(config, x), probs(config, y), cost)


@pytest.mark.parametrize("cell", [CELLS["A2-beta8-H2"], CELLS["B1-beta8-H2"], CELLS["A3-beta3-H2-alpha0.25"]])
def test_h2_oracle_matches_solver_free_bellman_recursion(cell):
    args = _cell(*cell)
    config, pre, action, alpha, H = args
    reference = _brute_oracle(config, *intervention_pair(config, pre, action, alpha), H)
    assert oracle(*args).second_moment == pytest.approx(reference, abs=1e-12)


def test_unsupported_or_invalid_requests_are_rejected():
    config, pre, action, alpha, _ = _cell("A1", 1.0, 0.4, 0.0, 0, 1.0, 0)
    with pytest.raises(ValueError, match="unsupported"):
        oracle(config, pre, action, alpha, 5)
    with pytest.raises(ValueError, match="unsupported"):
        terminal_ot(config, pre, action, alpha, 5)
    with pytest.raises(ValueError):
        pair_moments("proposed", config, pre, action, alpha, 1)
    with pytest.raises(TypeError):
        oracle(config, pre, action, alpha, 1.0)
    with pytest.raises(ValueError):
        pair_moments("maximal", config, pre, action, alpha, -1)
    with pytest.raises(ValueError):
        oracle(config, pre, 3, alpha, 1)


def _cli(capsys, *argv):
    code = headroom.main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def test_headroom_cli_nondegenerate_cell(capsys):
    code, out = _cli(capsys, "--structure", "B1", "--beta", "8", "--eta", "0.4", "--theta0", "0.4",
                     "--action", "1", "--alpha", "1", "--H", "1")
    assert code == 0 and out["ok"] is True and all(out["checks"].values())
    assert set(out["ordinary"]) == set(ORDINARY_METHODS)
    assert out["cell"]["theta0"] == [0.4, 0.0] and out["cell"]["action_indexing"] == "zero-based"
    truth = attribution(*_cell("B1", 8.0, 0.4, 0.4, 1, 1.0, 1))
    assert out["marginal_truth"]["delta"] == truth.delta
    assert out["headroom"]["nondegenerate"] is True
    assert isinstance(out["headroom"]["oracle_variance_reduction"], float)
    assert out["oracle"]["root_plan"] is not None and out["numerics"]["max_marginal_residual"] <= 1e-12
    assert out["checks"]["oracle_gap_estimates"] is True and out["numerics"]["max_gap_estimate"] <= 1e-12
    assert abs(out["numerics"]["oracle_suboptimality_estimate"]) <= 1e-12


def test_headroom_cli_zero_variance_and_failures(capsys):
    code, out = _cli(capsys, "--family", "A1", "--beta", "8", "--eta", "0.4", "--theta0", "0.4",
                     "--action", "1", "--alpha", "0", "--H", "2")
    assert code == 0 and out["ok"] is True
    assert out["headroom"]["nondegenerate"] is False
    assert out["headroom"]["oracle_variance_reduction"] is None
    code, out = _cli(capsys, "--structure", "A1", "--beta", "1", "--eta", "2", "--theta0", "0",
                     "--action", "0", "--alpha", "1", "--H", "1")
    assert code == 1 and out["ok"] is False and "eta" in out["error"]
    with pytest.raises(SystemExit) as info:
        headroom.main(["--structure", "C9", "--beta", "1", "--eta", "0.4", "--theta0", "0",
                       "--action", "0", "--alpha", "1", "--H", "1"])
    assert info.value.code == 2


def test_headroom_rejects_unsupported_horizon_before_any_enumeration(monkeypatch, capsys):
    """--H 100 used to enumerate 3**100 marginal paths before the pair size guard ran."""
    calls = []

    def forbidden(name):
        def call(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"{name} started before the size guard")
        return call

    for name in ("attribution", "pair_moments", "oracle", "terminal_ot"):
        monkeypatch.setattr(headroom, name, forbidden(name))
    for H in ("5", "100", str(10 ** 18)):  # the guard never forms K**(2H) for huge H
        code, out = _cli(capsys, "--structure", "B1", "--beta", "8", "--eta", "0.4", "--theta0", "0.4",
                         "--action", "1", "--alpha", "1", "--H", H)
        assert code == 1 and out["ok"] is False
        assert out["error"].startswith("ValueError: unsupported size")
    with pytest.raises(ValueError, match="unsupported"):
        headroom.run("A1", 1.0, 0.4, 0.0, 0, 1.0, 5)
    assert calls == []
    config = _cell("A1", 1.0, 0.4, 0.0, 0, 1.0, 0)[0]
    assert supported_horizon(config, 4) == 4  # the CLI's largest supported cell (3**8 paired leaves)


def test_headroom_gap_estimates_never_widen_ordering_checks(monkeypatch):
    """An oracle above every ordinary coupling fails even with a large suboptimality estimate."""
    real = headroom.oracle

    def inflated(*args):
        best = real(*args)
        return dataclasses.replace(best, second_moment=best.second_moment + 1.0, suboptimality_estimate=2.0)

    monkeypatch.setattr(headroom, "oracle", inflated)
    out = headroom.run("B1", 8.0, 0.4, 0.4, 1, 1.0, 1)
    checks = out["checks"]
    assert not checks["oracle_le_every_ordinary"] and not checks["h1_oracle_equals_terminal"]
    assert not checks["oracle_gap_estimates"] and checks["terminal_le_oracle"] and out["ok"] is False
