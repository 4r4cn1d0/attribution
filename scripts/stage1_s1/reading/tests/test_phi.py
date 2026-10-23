"""Phi: the graph's weights and edges, its local levels against phi_levels_check.py and phi_planb_check.py, the
largest reachable levels of the statistics review, the update rule, Holm equivalence, order independence, the
IUT nodes (REV3 4.2-4.3; AMD B.2-B.3; LN-05, LN-21)."""

from __future__ import annotations

import itertools
from fractions import Fraction as Fr

import numpy as np
import pytest

from scripts.stage1_s1.reading import phi
from scripts.stage1_s1.reading.settings import Refusal

PLAN_A = ("P1", "P2", "P3", "P4", "P5", "P6")
PLAN_B = ("P1", "P3", "P6")
A = Fr(1, 20)


def pct(graph, kind, c):
    return round(float(phi.levels(graph, A)[(kind, c)]) * 100, 4)


def test_start_weights_and_edges_plan_a():
    g = phi.build_graph(PLAN_A)
    assert sum(g.weights.values()) == 1
    for c in PLAN_A:
        assert g.weights[("U", c)] == Fr(3, 20) and g.weights[("O", c)] == Fr(1, 120) and g.weights[("F", c)] == 0
        u = g.edges[("U", c)]
        assert u[("F", c)] == Fr(1, 2) and u[("O", c)] == Fr(1, 8) and u[("L", c)] == Fr(1, 8)
        assert all(u[("U", o)] == Fr(1, 20) for o in PLAN_A if o != c)
        assert g.edges[("F", c)][("L", c)] == 1 and g.edges[("F", c)][("O", c)] == 0        # LN-05's R1.3 edge
        assert g.edges[("O", c)][("L", c)] == Fr(1, 2) and g.edges[("O", c)][("U", c)] == Fr(1, 2)
        assert g.edges[("L", c)][("O", c)] == Fr(1, 2) and g.edges[("L", c)][("U", c)] == Fr(1, 2)
        assert all(sum(g.edges[(k, c)].values()) == 1 for k in "UOLF")


def test_local_levels_equal_phi_levels_check_r13_column():
    """phi_levels_check.out.txt, 'R1.3 edge' (exact fractions, printed to 4 decimals)."""
    g = phi.build_graph(PLAN_A)
    assert (pct(g, "U", "P1"), pct(g, "O", "P1"), pct(g, "L", "P1"), pct(g, "F", "P1")) == (0.75, 0.0417, 0.0417, 0.0)
    g1 = phi.update(g, ("U", "P1"))
    assert (pct(g1, "F", "P1"), pct(g1, "O", "P1"), pct(g1, "L", "P1"), pct(g1, "U", "P2")) == (0.375, 0.1354, 0.1354, 0.7875)
    g2 = phi.update(g1, ("F", "P1"))
    assert (pct(g2, "O", "P1"), pct(g2, "L", "P1"), pct(g2, "U", "P2")) == (0.1354, 0.5104, 0.7875)
    g3 = phi.update(g1, ("O", "P1"))
    assert (pct(g3, "L", "P1"), pct(g3, "F", "P1")) == (0.2167, 0.4111)
    g4 = phi.update(g2, ("L", "P1"))
    assert pct(g4, "O", "P1") == 0.553
    assert phi.levels(g2, A)[("L", "P1")] == Fr(49, 9600) and phi.levels(g4, A)[("O", "P1")] == Fr(73, 13200)


def test_plan_b_levels_equal_phi_planb_check():
    g = phi.build_graph(PLAN_B)
    assert sum(g.weights.values()) == 1 and all(sum(r.values()) == 1 for r in g.edges.values())
    assert g.weights[("U", "P1")] == Fr(3, 10) and g.weights[("O", "P1")] == Fr(1, 60)
    assert g.edges[("U", "P1")][("U", "P3")] == Fr(1, 8)
    assert (pct(g, "U", "P1"), pct(g, "O", "P1"), pct(g, "L", "P1")) == (1.5, 0.0833, 0.0833)
    g1 = phi.update(g, ("U", "P1"))
    assert (pct(g1, "F", "P1"), pct(g1, "O", "P1"), pct(g1, "L", "P1"), pct(g1, "U", "P3")) == (0.75, 0.2708, 0.2708, 1.6875)
    g2 = phi.update(g1, ("F", "P1"))
    assert (pct(g2, "O", "P1"), pct(g2, "L", "P1")) == (0.2708, 1.0208)


def test_largest_reachable_levels_equal_the_statistics_review():
    """stat_review_phi_maxlevels_out.txt: U 1.229%, O 0.302%, L 0.776%, F 0.639% (F_k and O_k never both reject)."""
    g0 = phi.build_graph(PLAN_A)
    best = {}
    for target in "UOLF":
        mx = Fr(0)
        for choice in itertools.product((0, 1), repeat=6):            # 0: F_k rejected, 1: O_k rejected
            if (target == "O" and choice[0] == 0) or (target == "F" and choice[0] == 1):
                continue
            g = g0
            for k, c in enumerate(PLAN_A):
                for kind in "UOLF":
                    if (kind, c) == (target, "P1"):
                        continue
                    if kind == "F" and choice[k] == 1:
                        continue
                    if kind == "O" and choice[k] == 0:
                        continue
                    g = phi.update(g, (kind, c))
            mx = max(mx, g.weights[(target, "P1")])
        best[target] = round(float(mx * A) * 100, 3)
    assert best == {"U": 1.229, "O": 0.302, "L": 0.776, "F": 0.639}
    g = g0
    for n in (("U", "P2"), ("U", "P3"), ("U", "P4"), ("U", "P5"), ("U", "P6")):
        g = phi.update(g, n)
    assert round(float(g.weights[("U", "P1")] * A) * 100, 3) == 0.984


def test_the_routine_equals_holm_on_a_holm_graph():
    rng = np.random.default_rng(41)
    nodes = tuple(("H", f"n{i}") for i in range(6))
    g = phi.holm_graph(nodes)
    phi.check_graph(g)
    for _ in range(1500):
        p = {n: float(v) for n, v in zip(nodes, rng.uniform(0, 0.12, 6) ** 2)}
        assert set(phi.run(g, p, A).rejected) == phi.holm(p, 0.05)


def test_rejections_do_not_depend_on_the_order():
    rng = np.random.default_rng(42)
    g = phi.build_graph(PLAN_A)
    for _ in range(60):
        p = {n: float(v) for n, v in zip(g.nodes, rng.uniform(0, 0.02, len(g.nodes)) ** 1.5)}
        ours = set(phi.run(g, p, A).rejected)
        current, rejected = g, set()
        order = list(g.nodes)
        rng.shuffle(order)
        while True:                                                       # a random candidate each time
            lv = phi.levels(current, A)
            cand = [n for n in order if n in current.nodes and p[n] <= float(lv[n])]
            if not cand:
                break
            j = cand[rng.integers(len(cand))]
            rejected.add(j)
            current = phi.update(current, j)
        assert rejected == ours


def test_update_rule_hand_case_and_a_zero_denominator():
    nodes = (("A", "1"), ("B", "1"), ("C", "1"))
    g = phi.Graph(nodes, {nodes[0]: Fr(1, 2), nodes[1]: Fr(1, 2), nodes[2]: Fr(0)},
                  {nodes[0]: {nodes[1]: Fr(1), nodes[2]: Fr(0)}, nodes[1]: {nodes[0]: Fr(1), nodes[2]: Fr(0)},
                   nodes[2]: {nodes[0]: Fr(1, 2), nodes[1]: Fr(1, 2)}})
    g1 = phi.update(g, nodes[0])
    assert g1.weights[nodes[1]] == 1 and g1.weights[nodes[2]] == 0
    assert g1.edges[nodes[1]][nodes[2]] == 0                                # (0 + 1 * 0) / (1 - 1 * 1): a zero denominator gives 0
    assert g1.edges[nodes[2]][nodes[1]] == (Fr(1, 2) + Fr(1, 2) * 1) / (1 - Fr(1, 2) * 0)


def test_run_rejects_at_the_boundary_and_records_levels():
    g = phi.build_graph(PLAN_A)
    p = {n: 1.0 for n in g.nodes}
    p[("U", "P1")] = 0.0075                                                 # exactly the start level
    out = phi.run(g, p, A)
    assert out.rejected == (("U", "P1"),) and out.level_at_rejection[("U", "P1")] == Fr(3, 400)
    assert out.final_levels[("F", "P1")] == Fr(3, 800) and out.start_levels[("F", "P1")] == 0
    p[("U", "P1")] = 0.0076
    assert phi.run(g, p, A).rejected == ()


def test_iut_and_the_f_o_exclusion():
    assert phi.iut(0.01, 0.2) == 0.2 and phi.iut(0.3, 0.001) == 0.3
    rng = np.random.default_rng(43)
    from scripts.stage1_s1.reading.contrast import Estimate
    for _ in range(500):
        e = Estimate("x", "f", float(rng.normal(5, 3)), float(abs(rng.normal(1.5, 0.5)) + 0.05), 5.0, 1.0, 5.0, 0.0, 0.0, 6, 500, False)
        p_theta, p_f = e.p_upper(5.0), e.p_lower(5.0)
        assert p_theta + p_f == pytest.approx(1.0, abs=1e-12)
        assert not (p_theta <= 0.05 and p_f <= 0.05)


def test_refusals():
    g = phi.build_graph(PLAN_A)
    with pytest.raises(Refusal):
        phi.run(g, {n: 0.5 for n in g.nodes[:-1]}, A)
    bad = {n: 0.5 for n in g.nodes}
    bad[("U", "P1")] = 1.5
    with pytest.raises(Refusal):
        phi.run(g, bad, A)
    with pytest.raises(Refusal):
        phi.build_graph(["P1"])
    broken = phi.Graph(g.nodes, dict(g.weights), {n: dict(r) for n, r in g.edges.items()})
    broken.edges[("U", "P1")][("F", "P1")] = Fr(1)
    with pytest.raises(Refusal):
        phi.check_graph(broken)
