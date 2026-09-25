"""Mechanism diagnostic: quantile W2 and solver-free vertex optima against the transport LP; the
stochastic-order/Monge route to an optimal sorted root and its real A2 counterexample; K=3
uniqueness of maximal agreement and a K=4 counterexample; a tied-key example showing that the rules
other than fixed_label are not relabelling-equivariant; the two-decision regret identity on live
cells against pilot.pair; and rejection of inconsistent run directories, stored variances and
headroom summaries before anything is written."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import shutil

import numpy as np
import pytest

from pilot import diagnose, headroom
from pilot.couplings import maximal, ordered, transport
from pilot.pair import ORDINARY_METHODS, oracle, pair_moments
from pilot.process import apply_event, canonical_config, initial_state, intervention_pair, probs, score


def _setup(structure, beta, eta, c, action, alpha):
    config = canonical_config(structure, beta, eta)
    return config, initial_state(config, (c,) + (0.0,) * (config.dim - 1)), action, alpha


def _plan_cost(plan, cost):
    return math.fsum((np.asarray(plan) * np.asarray(cost)).ravel().tolist())


LAWS = {  # p on atoms s, q on atoms t
    "plain": ((0.2, 0.5, 0.3), (0.1, 0.9, 0.4), (0.3, 0.3, 0.4), (0.3, 0.0, 0.7)),
    "tied-atoms": ((0.5, 0.25, 0.25), (0.2, 0.2, 0.6), (0.4, 0.4, 0.2), (0.5, 0.1, 0.5)),
    "zero-mass": ((0.0, 0.6, 0.4), (0.3, 0.1, 0.2), (0.25, 0.25, 0.5), (0.0, 1.0, 0.5)),
    "skewed": ((0.98, 0.01, 0.01), (0.5, 0.49, 0.51), (1e-6, 0.5, 0.5 - 1e-6), (0.2, 0.8, 0.6)),
}


@pytest.mark.parametrize(("p", "s", "q", "t"), list(LAWS.values()), ids=list(LAWS))
def test_quantile_w2_equals_lp_and_vertex_optimum(p, s, q, t):
    cost = np.subtract.outer(s, t) ** 2
    value = diagnose.w2_squared(p, s, q, t)
    assert abs(value - transport(p, q, cost).objective) <= 1e-12
    assert abs(value - diagnose.vertex_minimum(p, q, cost)) <= 1e-12
    plan = diagnose.sorted_plan(p, s, q, t)
    assert np.abs(plan.sum(axis=1) - p).max() <= 1e-15 and np.abs(plan.sum(axis=0) - q).max() <= 1e-15
    assert plan.min() >= 0.0 and abs(_plan_cost(plan, cost) - value) <= 1e-15


def test_vertex_minimum_matches_transport_on_random_costs_and_rejects_infeasible_laws():
    rng = np.random.default_rng(20260924)
    for _ in range(25):
        p, q = rng.dirichlet(np.ones(3)), rng.dirichlet(np.ones(3))
        cost = rng.normal(size=(3, 3)) * 10.0 ** rng.integers(-6, 2)
        scale = max(1.0, float(np.abs(cost).max()))
        assert abs(diagnose.vertex_minimum(p, q, cost) - transport(p, q, cost).objective) <= 1e-12 * scale
    with pytest.raises(ValueError, match="no feasible"):
        diagnose.vertex_minimum((0.5, 0.5, 0.0), (0.2, 0.2, 0.2), np.zeros((3, 3)))


def test_order_status_classifies_order_failures():
    uniform = (1 / 3, 1 / 3, 1 / 3)
    lo = (uniform, (0.1, 0.2, 0.3))
    assert diagnose.order_status(lo, (uniform, (0.15, 0.25, 0.35))) == "ordered"
    # Every action's atom is higher, but hi puts its mass on its lowest atom: equal weights would be ordered.
    assert diagnose.order_status(((0.2, 0.3, 0.5), (0.1, 0.2, 0.3)), ((0.8, 0.1, 0.1), (0.11, 0.21, 0.31))) == "weights"
    # Action 1's atom drops from 0.2 to 0.05: a same-action atom is reversed (a pattern, not a cause).
    assert diagnose.order_status(lo, (uniform, (0.15, 0.05, 0.35))) == "atoms"


def _tilted(atoms, lam):
    w = np.exp(lam * np.asarray(atoms))
    return w / w.sum()


def test_stochastically_ordered_children_make_the_sorted_root_optimal():
    """Children tilted by increasing lambda on increasing atoms are first-order ordered, so their
    W2 cost is Monge in child order and sorting the root is optimal for every root law."""
    rng = np.random.default_rng(7)
    for _ in range(20):
        worlds = []
        for _world in range(2):
            base = np.sort(rng.uniform(0.0, 1.0, 3))  # child i: atoms shifted up by 0.05 i, tilt increasing
            laws = [(_tilted(base, lam), base + 0.05 * i) for i, lam in enumerate(np.sort(rng.normal(0.0, 3.0, 3)))]
            assert all(diagnose.order_status(laws[i], laws[i + 1]) == "ordered" for i in range(2))
            worlds.append(laws)
        cost = np.array([[diagnose.w2_squared(*u, *v) for v in worlds[1]] for u in worlds[0]])
        assert diagnose.monge_violation(cost, range(3), range(3)) <= 1e-15
        for _law in range(5):
            p, q = rng.dirichlet(np.ones(3)), rng.dirichlet(np.ones(3))
            plan = ordered(p, q, (0.0, 1.0, 2.0), (0.0, 1.0, 2.0)).matrix
            assert _plan_cost(plan, cost) <= diagnose.vertex_minimum(p, q, cost) + 1e-12


def test_a2_feedback_reverses_child_order_and_makes_key_sorting_suboptimal():
    """Real counterexample (A2 witness parameters): with every successor atom comonotone, policy
    feedback alone breaks the stochastic order of the children, C is not Monge in target order
    and the 'ordered' root decision loses; its last decision is still optimal (fact 1)."""
    config, pre, action, alpha = _setup("A2", 8.0, 0.4, -0.4, 1, 1.0)
    tree = diagnose.build_tree(config, pre, action, alpha)
    C = diagnose.continuation_costs(tree)
    order = [int(i) for i in np.argsort(config.targets, kind="stable")]
    statuses = [diagnose.order_status((law[order[i]], atoms[order[i]]), (law[order[i + 1]], atoms[order[i + 1]]))
                for law, atoms in ((tree.P, tree.s), (tree.Q, tree.t)) for i in range(2)]
    assert "weights" in statuses and "atoms" not in statuses
    assert diagnose.monge_violation(C, order, order) > 1e-6
    v_star = diagnose.vertex_minimum(tree.px, tree.py, C)
    terms = diagnose.method_terms("ordered", tree, C, v_star)
    assert terms.r0 > 1e-5 and abs(terms.r1) <= 1e-15


def _vertices(p, q):
    """Every basic feasible plan of the 3 x 3 transportation polytope (independent enumeration)."""
    rows = np.zeros((6, 9))
    for n, (a, b) in enumerate(itertools.product(range(3), range(3))):
        rows[a, n] = rows[3 + b, n] = 1.0
    rhs, out = np.concatenate((p, q)), []
    for support in itertools.combinations(range(9), 5):
        m = rows[:, support]
        if np.linalg.matrix_rank(m) < 5:
            continue
        x = np.linalg.lstsq(m, rhs, rcond=None)[0]
        if x.min() >= -1e-12 and np.abs(m @ x - rhs).max() <= 1e-12:
            plan = np.zeros(9)
            plan[list(support)] = x
            out.append(plan.reshape(3, 3))
    return out


def test_k3_diagonal_maximizing_plan_is_unique_but_not_for_k4():
    rng = np.random.default_rng(11)
    for _ in range(25):
        p, q = rng.dirichlet(np.ones(3)), rng.dirichlet(np.ones(3))
        best = math.fsum(np.minimum(p, q).tolist())
        optimal = [v for v in _vertices(p, q) if np.trace(v) >= best - 1e-12]
        assert optimal and all(np.abs(v - maximal(p, q).matrix).max() <= 1e-12 for v in optimal)
    # K = 4 with residual supports {0, 1} and {2, 3}: two different plans keep the whole diagonal.
    p, q = (0.3, 0.3, 0.2, 0.2), (0.2, 0.2, 0.3, 0.3)
    one, two = np.diag([0.2] * 4), np.diag([0.2] * 4)
    one[0, 2] = one[1, 3] = two[0, 3] = two[1, 2] = 0.1
    for plan in (one, two, maximal(p, q).matrix):
        assert np.allclose(plan.sum(axis=1), p, atol=1e-15) and np.allclose(plan.sum(axis=0), q, atol=1e-15)
        assert np.trace(plan) == pytest.approx(0.8, abs=1e-15)
    assert np.abs(one - two).max() == pytest.approx(0.1) and np.abs(one - maximal(p, q).matrix).max() > 0.04


def test_tied_keys_make_ordered_depend_on_action_labels():
    """Dropping fixed_label does not leave a relabelling-equivariant set: 'ordered' breaks key ties by
    action ID, so swapping labels 0 and 1 in both worlds and mapping back changes its plan."""
    p, q, keys, swap = (0.2, 0.3, 0.5), (0.4, 0.4, 0.2), (0.0, 0.0, 1.0), [1, 0, 2]
    plan = ordered(p, q, keys, keys).matrix
    relabelled = ordered(*([v[i] for i in swap] for v in (p, q, keys, keys))).matrix
    back = relabelled[np.ix_(swap, swap)]  # swap is its own inverse
    assert np.abs(plan - [[0.2, 0.0, 0.0], [0.2, 0.1, 0.0], [0.0, 0.3, 0.2]]).max() <= 1e-15
    assert np.abs(back - [[0.1, 0.1, 0.0], [0.0, 0.3, 0.0], [0.3, 0.0, 0.2]]).max() <= 1e-15
    assert np.abs(plan - back).max() == pytest.approx(0.3, abs=1e-15)


LIVE = {
    "B1-beta8-alpha0.25": ("B1", 8.0, 0.4, -0.4, 0, 0.25),
    "B1-beta8-theta0-alpha1": ("B1", 8.0, 0.4, 0.0, 0, 1.0),
    "A2-beta8": ("A2", 8.0, 0.4, -0.4, 1, 1.0),
    "A3-beta3-alpha0.25": ("A3", 3.0, 0.4, 0.0, 0, 0.25),
    "B1-beta0": ("B1", 0.0, 0.4, -0.4, 0, 0.25),
    "B2-beta8": ("B2", 8.0, 0.1, 0.4, 2, 1.0),
}


def _maximal_then_ordered(config, x, y):
    """E[Y**2] of maximal at the root and 'ordered' at the last step, enumerated without the tree."""
    def expand(state):
        return probs(config, state), [apply_event(config, state, a) for a in range(3)]

    def keys(states):
        return list(config.targets) if config.family == "A" else [s.theta[0] for s in states]

    (px, xs), (py, ys) = expand(x), expand(y)
    total = []
    for a, b in itertools.product(range(3), range(3)):
        mass = maximal(px, py).matrix[a, b]
        if mass == 0.0:
            continue
        (pu, us), (pv, vs) = expand(xs[a]), expand(ys[b])
        plan = ordered(pu, pv, keys(us), keys(vs)).matrix
        d = np.subtract.outer([score(config, u) for u in us], [score(config, v) for v in vs])
        total.append(mass * math.fsum((plan * d * d).ravel().tolist()))
    return math.fsum(total)


@pytest.mark.parametrize("cell", list(LIVE.values()), ids=list(LIVE))
def test_two_decision_identity_against_live_pair_and_oracle(cell):
    args = _setup(*cell)
    config = args[0]
    tree = diagnose.build_tree(*args)
    C = diagnose.continuation_costs(tree)
    v_star = diagnose.vertex_minimum(tree.px, tree.py, C)
    best = oracle(*args, 2)
    assert abs(v_star - best.second_moment) <= 1e-12
    assert np.abs(C - np.array(best.root_cost)).max() <= 1e-12
    assert _plan_cost(best.root_plan, C) == pytest.approx(v_star, abs=1e-12)
    terms = {}
    for method in ORDINARY_METHODS:
        tm = diagnose.method_terms(method, tree, C, v_star)
        reference = pair_moments(method, *args, 2)
        assert abs(tm.second_moment - reference.second_moment) <= 1e-12
        assert abs(tm.mean - reference.mean) <= 1e-12
        assert tm.r0 >= -1e-12 and tm.r1 >= -1e-12
        assert abs(tm.r0 + tm.r1 - (reference.second_moment - best.second_moment)) <= 1e-12
        terms[method] = tm
    assert abs(terms["ordered"].r1) <= 1e-12  # the terminal-score sort is the last-step oracle
    # R0(m) is the whole regret of 'm at the root, sorted at the last step' (independent enumeration).
    x, y = intervention_pair(config, args[1], args[2], args[3])
    assert abs(_maximal_then_ordered(config, x, y) - v_star - terms["maximal"].r0) <= 1e-12
    if config.family == "A":  # scalar successors: squared distance is Monge in target order
        assert np.abs(terms["distance"].root - terms["ordered"].root).max() <= 1e-12
    if cell[1] == 0.0:  # beta 0: no action-probability change anywhere, maximal keeps actions equal
        assert np.array_equal(tree.px, tree.py) and all(np.array_equal(u, v) for u, v in zip(tree.P, tree.Q))
        assert terms["maximal"].agree_mass == pytest.approx(1.0, abs=1e-15)


@pytest.mark.parametrize("structure", ["A1", "A2", "A3", "B1", "B2"])
def test_h1_ordered_attains_the_oracle(structure):
    args = _setup(structure, 8.0, 0.4, 0.4, 2, 1.0)
    assert abs(pair_moments("ordered", *args, 1).second_moment - oracle(*args, 1).second_moment) <= 1e-12


# ----------------------------------------------------------------------------- run directories

CELLS = [
    {"family": "B1", "beta": 8, "eta": 0.4, "initial_coordinate": -0.4, "action": 0, "alpha": 0.25, "H": 2,
     "cell_id": "00000000000000a1"},
    {"family": "B1", "beta": 8, "eta": 0.4, "initial_coordinate": -0.4, "action": 0, "alpha": 0.25, "H": 1,
     "cell_id": "00000000000000a2"},
    {"family": "B1", "beta": 0, "eta": 0.4, "initial_coordinate": -0.4, "action": 0, "alpha": 0.25, "H": 2,
     "cell_id": "00000000000000a3"},
    {"family": "B1", "beta": 8, "eta": 0.4, "initial_coordinate": -0.4, "action": 0, "alpha": 0.25, "H": 4,
     "cell_id": "00000000000000a4"},
]


@pytest.fixture(scope="module")
def records():
    out = {}
    for cell in CELLS[:3]:
        result = headroom.run(cell["family"], float(cell["beta"]), float(cell["eta"]),
                              float(cell["initial_coordinate"]), cell["action"], float(cell["alpha"]), cell["H"])
        out[cell["cell_id"]] = {"target": dict(cell), "status": "completed", "result": result}
    return out


def _make_run(tmp_path, records, edit=None):
    """research/pilot/{manifest, runs/R/...} under tmp_path; `edit(cells, records)` may corrupt it."""
    cells, recs = json.loads(json.dumps(CELLS)), json.loads(json.dumps(records))
    if edit is not None:
        edit(cells, recs)
    root = tmp_path / "research" / "pilot"
    run_dir = root / "runs" / "R"
    run_dir.mkdir(parents=True)
    manifest = root / diagnose.MANIFEST_NAME
    manifest.write_text(json.dumps({"cells": cells}))
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    sources = {k: v for k, v in diagnose._source_hashes().items() if not k.endswith("diagnose.py")}
    (run_dir / "metadata.json").write_text(json.dumps({"manifest_sha256": digest, "source_hashes": sources}))
    for cid, record in recs.items():
        (run_dir / f"{cid}.json").write_text(json.dumps(record))
    return run_dir, digest


def _run(run_dir, digest, out):
    return diagnose.run(run_dir, out, expected_sha256=digest, witnesses=("00000000000000a1",))


def test_run_writes_checked_outputs(tmp_path, records):
    run_dir, digest = _make_run(tmp_path, records)
    out = tmp_path / "diag"
    report = _run(run_dir, digest, out)
    assert report["ok"] is True and all(c["passed"] for c in report["checks"].values())
    assert sorted(p.name for p in out.iterdir()) == sorted(diagnose.OUTPUTS)
    saved = json.loads((out / "diagnostics.json").read_text())
    assert saved["h2"]["cells"] == 2 and saved["inputs"]["records"] == 3
    roles = {e["cell_id"]: e["roles"] for e in saved["examples"]}
    assert roles == {"00000000000000a1": ["witness"], "00000000000000a2": ["control: H1 twin of 00000000000000a1"],
                     "00000000000000a3": ["control: beta 0 of 00000000000000a1"]}
    assert (out / "h2_cells.csv").read_text().count("\n") == 3  # header and two H=2 cells


def test_tampered_stored_moment_fails_and_writes_nothing(tmp_path, records):
    def tamper(cells, recs):
        recs["00000000000000a1"]["result"]["ordinary"]["maximal"]["second_moment"] += 1e-9

    run_dir, digest = _make_run(tmp_path, records, tamper)
    out = tmp_path / "diag"
    report = _run(run_dir, digest, out)
    assert report["ok"] is False and not out.exists()
    assert not report["checks"]["method_second_moment_vs_stored"]["passed"]
    assert not report["checks"]["decomposition_vs_stored_regret"]["passed"]


def _drop(cid):
    return lambda cells, recs: recs.pop(cid)


def _set(cid, path, value):
    def edit(cells, recs):
        node = recs[cid]
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return edit


def _add(cid, path, delta):
    def edit(cells, recs):
        node = recs[cid]
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] += delta
    return edit


def _extra_h4_record(cells, recs):
    recs["00000000000000a4"] = dict(recs["00000000000000a1"], target=dict(CELLS[3]))


def _stray_record(cells, recs):
    recs["00000000000000ff"] = recs["00000000000000a1"]


def _degenerate_claim(cells, recs):
    """Flag the H=2 record degenerate with null ratios: well typed, but its best variance is > 1e-14."""
    head = recs["00000000000000a1"]["result"]["headroom"]
    head.update(dict.fromkeys(diagnose.RATIOS), nondegenerate=False)


def _terminal_shift(field, delta):
    """Shift one stored terminal-OT moment, keeping its variance and headroom copy consistent."""
    def edit(cells, recs):
        result = recs["00000000000000a1"]["result"]
        block = result["terminal_lower_bound"]
        block[field] += delta
        block["variance"] = result["headroom"]["terminal_lower_bound_variance"] = (
            block["second_moment"] - block["mean"] * block["mean"])
    return edit


@pytest.mark.parametrize(("edit", "message"), [
    (_drop("00000000000000a3"), "missing record"),
    (_set("00000000000000a1", ("status",), "censored"), "status"),
    (_set("00000000000000a1", ("result", "ok"), False), "not ok"),
    (_set("00000000000000a1", ("result", "checks", "oracle_le_every_ordinary"), False), "not ok"),
    (_set("00000000000000a1", ("target", "beta"), 3), "target differs"),
    (_set("00000000000000a1", ("result", "cell", "eta"), 0.1), "stored cell differs"),
    (_extra_h4_record, "unexpected record"),
    (_stray_record, "not in the manifest"),
    (_set("00000000000000a1", ("result", "ordinary", "maximal", "variance"), float("nan")), "ordinary.maximal.variance"),
    (_set("00000000000000a2", ("result", "oracle", "second_moment"), float("inf")), "oracle.second_moment"),
    (_set("00000000000000a1", ("result", "marginal_truth", "delta"), True), "marginal_truth.delta"),
    (_set("00000000000000a1", ("result", "headroom", "nondegenerate"), "false"), "headroom.nondegenerate"),
    (_set("00000000000000a1", ("result", "headroom", "best_ordinary_method"), "oracle"), "best_ordinary_method"),
    (_set("00000000000000a1", ("result", "headroom", "oracle_variance_reduction"), None), "oracle_variance_reduction"),
], ids=["missing", "status", "not-ok", "failed-check", "target", "stored-cell", "h4-record", "stray",
        "nan-variance", "h1-infinite-moment", "bool-as-number", "string-flag", "unknown-best-method", "null-ratio"])
def test_inconsistent_run_directories_are_rejected(tmp_path, records, edit, message):
    run_dir, digest = _make_run(tmp_path, records, edit)
    with pytest.raises(ValueError, match=message):
        _run(run_dir, digest, tmp_path / "diag")
    assert not (tmp_path / "diag").exists()


@pytest.mark.parametrize(("edit", "check"), [
    # The three reviewed mutations, each previously accepted with every check passing.
    (_set("00000000000000a1", ("result", "headroom", "oracle_variance"), 0.0), "stored_headroom_vs_oracle_and_terminal"),
    (_set("00000000000000a1", ("result", "headroom", "best_ordinary_method"), "independent"),
     "stored_best_variance_vs_six_methods"),
    (_set("00000000000000a1", ("result", "ordinary", "distance", "variance"), 0.0), "stored_variance_vs_moments"),
    # Other stored summaries the outputs use, at H=2 ...
    (_add("00000000000000a1", ("result", "headroom", "best_ordinary_variance"), 1e-9),
     "stored_best_variance_vs_six_methods"),
    (_add("00000000000000a1", ("result", "headroom", "terminal_lower_bound_variance"), 1e-9),
     "stored_headroom_vs_oracle_and_terminal"),
    (_add("00000000000000a1", ("result", "oracle", "variance"), 1e-9), "stored_variance_vs_moments"),
    (_degenerate_claim, "stored_nondegenerate_and_ratios"),
    (_add("00000000000000a1", ("result", "headroom", "oracle_variance_reduction"), 1e-9),
     "stored_nondegenerate_and_ratios"),
    (_add("00000000000000a1", ("result", "marginal_truth", "action_probability"), 1e-9), "action_probability_vs_stored"),
    (_terminal_shift("mean", 1e-9), "oracle_and_terminal_mean_vs_delta"),
    (_terminal_shift("second_moment", 1e-9), "terminal_second_moment_vs_quantile_merge"),
    # ... and at H=1, whose summaries are reported from stored values.
    (_add("00000000000000a2", ("result", "headroom", "oracle_variance_reduction"), 1e-9),
     "stored_nondegenerate_and_ratios"),
    (_add("00000000000000a2", ("result", "ordinary", "ordered", "variance"), 1e-9), "stored_variance_vs_moments"),
    (_set("00000000000000a2", ("result", "headroom", "best_ordinary_method"), "independent"),
     "stored_best_variance_vs_six_methods"),
], ids=["oracle-variance-0", "best-method-independent", "distance-variance-0", "best-variance", "terminal-variance",
        "oracle-block-variance", "degenerate-claim", "headroom-ratio", "action-probability", "terminal-mean",
        "terminal-second-moment", "h1-headroom-ratio", "h1-ordered-variance", "h1-best-method"])
def test_inconsistent_stored_summaries_fail_and_write_nothing(tmp_path, records, edit, check):
    run_dir, digest = _make_run(tmp_path, records, edit)
    out = tmp_path / "diag"
    report = _run(run_dir, digest, out)
    assert report["ok"] is False and not out.exists()
    assert not report["checks"][check]["passed"]


def test_stored_summaries_allow_ties_at_the_minimum_only(records):
    """v1 takes the first listed of tied methods; any method at the minimum is accepted as best,
    one above it is not, and v1's own record reproduces within the summary tolerance."""
    def errors(result):
        worst = diagnose._Worst()
        diagnose._stored_summaries(result, worst)
        return worst.values

    result = json.loads(json.dumps(records["00000000000000a1"]["result"]))
    assert max(errors(result).values()) <= diagnose.SUMMARY_TOL
    variances = {m: result["ordinary"][m]["variance"] for m in ORDINARY_METHODS}
    best, worse = result["headroom"]["best_ordinary_method"], max(variances, key=variances.get)
    tied = next(m for m in ORDINARY_METHODS if m not in (best, worse))
    result["ordinary"][tied] = dict(result["ordinary"][best], method=tied)
    result["headroom"]["best_ordinary_method"] = tied
    assert max(errors(result).values()) <= diagnose.SUMMARY_TOL
    result["headroom"]["best_ordinary_method"] = worse
    assert errors(result)["stored_best_variance_vs_six_methods"] > 1e-6


def test_manifest_hash_and_output_location_are_enforced(tmp_path, records, capsys):
    run_dir, digest = _make_run(tmp_path, records)
    with pytest.raises(ValueError, match="SHA256"):
        diagnose.run(run_dir, tmp_path / "diag", expected_sha256="0" * 64)
    with pytest.raises(ValueError, match="must not be"):
        _run(run_dir, digest, run_dir / "diag")
    meta = json.loads((run_dir / "metadata.json").read_text())
    (run_dir / "metadata.json").write_text(json.dumps(dict(meta, manifest_sha256="1" * 64)))
    with pytest.raises(ValueError, match="metadata"):
        _run(run_dir, digest, tmp_path / "diag")
    shutil.rmtree(run_dir)
    assert diagnose.main(["--input", str(run_dir), "--output", str(tmp_path / "diag")]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False
