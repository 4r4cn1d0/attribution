"""Ridge with group cross-fitting: the closed form (training-fold weighted standardization,
unpenalized intercept), group-equal weights (duplicated seeds never count as new groups),
zero-variance handling, a fold-leakage counterexample, held-out targets that cannot reach their
own predictions, group-equal fold scores, lambda ties, nested selection and frozen models; the
BLAS-free normal equations against the BLAS closed form at fixture size; extreme finite inputs
whose intermediate arithmetic overflows or underflows refused instead of warned about."""

from __future__ import annotations

import math

import pytest

np = pytest.importorskip("numpy")

from experiments.safety_decision_policy import ridge  # noqa: E402
from experiments.safety_decision_policy.common import PolicyError, VerificationError  # noqa: E402

NAMES = ["x1", "x2", "x3"]
GROUPS = ["a", "a", "a", "b", "c", "c", "d", "e", "e", "f", "f", "f"]
GRID = [0.01, 0.1, 1.0, 10.0, 100.0]


def data():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(len(GROUPS), 3))
    y = X @ np.array([1.0, -2.0, 0.5]) + rng.normal(scale=0.3, size=len(GROUPS))
    return X.tolist(), y.tolist(), list(GROUPS)


def closed_form(X, y, groups, lam, scale_rows=None):
    x, t = np.asarray(X), np.asarray(y)
    w = np.array([1.0 / groups.count(g) for g in groups])
    m = (w @ x) / w.sum()
    sx = np.asarray(scale_rows[0]) if scale_rows else x
    sw = np.asarray(scale_rows[1]) if scale_rows else w
    s = np.sqrt((sw @ (sx - (sw @ sx) / sw.sum()) ** 2) / sw.sum())
    z = (x - m) / s
    b0 = (w @ t) / w.sum()
    beta = np.linalg.solve(z.T @ (w[:, None] * z) + lam * np.eye(x.shape[1]), z.T @ (w * (t - b0)))
    return m, s, b0, beta


def test_fit_is_the_group_weighted_standardized_ridge_with_an_unpenalized_intercept():
    X, y, groups = data()
    model = ridge.fit(X, y, groups, 0.7, NAMES)
    m, s, b0, beta = closed_form(X, y, groups, 0.7)
    assert model.intercept == pytest.approx(b0, rel=1e-12)
    assert model.mean == pytest.approx(tuple(m), rel=1e-12)
    assert model.scale == pytest.approx(tuple(s), rel=1e-12)
    assert model.coef == pytest.approx(tuple(beta), rel=1e-10)
    assert model.predict(X[4]) == pytest.approx(b0 + ((np.asarray(X[4]) - m) / s) @ beta, rel=1e-10)
    with pytest.raises(PolicyError):
        ridge.fit(X, y, groups, 0.0, NAMES)


def test_more_seeds_of_one_group_never_count_as_more_groups():
    X, y, groups = data()
    rows = [i for i, g in enumerate(groups) if g == "b"]
    doubled = ridge.fit(X + [X[i] for i in rows], y + [y[i] for i in rows], groups + ["b"] * len(rows), 1.0, NAMES)
    model = ridge.fit(X, y, groups, 1.0, NAMES)
    assert doubled.coef == pytest.approx(model.coef, rel=1e-10)
    assert doubled.intercept == pytest.approx(model.intercept, rel=1e-12)
    unweighted = ridge.fit(X + [X[i] for i in rows], y + [y[i] for i in rows],
                           [f"row{i}" for i in range(len(X) + len(rows))], 1.0, NAMES)
    assert unweighted.coef != pytest.approx(model.coef, rel=1e-6)  # counterexample: rows treated as groups


def test_a_constant_training_feature_is_inactive_and_ignored_when_predicting():
    X, y, groups = data()
    constant = [[r[0], 5.0, r[2]] for r in X]
    model = ridge.fit(constant, y, groups, 1.0, NAMES)
    assert model.active == (True, False, True) and model.coef[1] == 0.0
    assert model.predict([X[0][0], 1e9, X[0][2]]) == model.predict([X[0][0], 5.0, X[0][2]])


def test_leave_one_group_out_standardizes_on_training_rows_only():
    X, y, groups = data()
    held = [i for i, g in enumerate(groups) if g == "f"]
    for i in held:
        X[i][0] = 50.0  # the held-out group is extreme on x1
    preds = ridge.logo_predictions(X, y, groups, 1.0, NAMES)
    train = [i for i in range(len(X)) if i not in held]
    manual = ridge.fit([X[i] for i in train], [y[i] for i in train], [groups[i] for i in train], 1.0, NAMES)
    assert [preds[i] for i in held] == [manual.predict(X[i]) for i in held]
    # counterexample: scaling with every row (the held-out group included) leaks and changes predictions
    w_all = [1.0 / groups.count(g) for g in groups]
    m, s, b0, beta = closed_form([X[i] for i in train], [y[i] for i in train], [groups[i] for i in train], 1.0,
                                 scale_rows=(X, w_all))
    leaky = b0 + ((np.asarray(X[held[0]]) - m) / s) @ beta
    assert abs(leaky - preds[held[0]]) > 1e-6


def test_held_out_targets_never_reach_their_own_predictions():
    X, y, groups = data()
    changed = list(y)
    for i, g in enumerate(groups):
        if g == "a":
            changed[i] += 100.0
    first = ridge.logo_predictions(X, y, groups, 1.0, NAMES)
    second = ridge.logo_predictions(X, changed, groups, 1.0, NAMES)
    assert [first[i] for i, g in enumerate(groups) if g == "a"] == [second[i] for i, g in enumerate(groups) if g == "a"]
    nested_first = ridge.nested(X, y, groups, GRID, NAMES)
    nested_second = ridge.nested(X, changed, groups, GRID, NAMES)
    assert nested_first["selected_by_fold"]["a"] == nested_second["selected_by_fold"]["a"]
    assert ([nested_first["predictions"][i] for i, g in enumerate(groups) if g == "a"]
            == [nested_second["predictions"][i] for i, g in enumerate(groups) if g == "a"])


def test_fold_scores_weight_groups_equally_and_lambda_ties_go_to_the_larger_lambda():
    score, per_group = ridge.cv_score([0.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0, 1.0], ["a", "a", "a", "b"])
    assert per_group == {"a": 1.0, "b": 0.0} and score == 0.5
    constant = [[1.0, 2.0, 3.0]] * 6
    tuned = ridge.tune(constant, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], ["a", "a", "b", "b", "c", "c"], GRID, NAMES)
    assert len({r["score"] for r in tuned["results"]}) == 1 and tuned["selected"] == 100.0
    with pytest.raises(PolicyError):
        ridge.logo_predictions(constant[:2], [0.0, 1.0], ["a", "a"], 1.0, NAMES)


@pytest.mark.parametrize("n_groups, seeds, p", [(6, 3, 22), (5, 3, 22), (3, 2, 20), (12, 3, 25)])
def test_blas_free_normal_equations_match_the_blas_closed_form_at_fixture_sizes(n_groups, seeds, p):
    """At the development fixtures' shapes (synthetic table, one of its folds, the engine CPU
    fixture, a 12-group table; more features than rows included) the elementwise Gram matrix and
    right-hand side give the coefficients of the closed form, whose matrix products go through
    BLAS: the host comparison for any BLAS floating-point warning raised in ``closed_form``."""
    rng = np.random.default_rng(n_groups * 100 + p)
    rows = n_groups * seeds
    groups = [f"g{i // seeds}" for i in range(rows)]
    x = rng.normal(size=(rows, p)) * rng.uniform(0.01, 100.0, size=p)
    y = x[:, :3] @ np.array([0.01, -0.02, 0.005]) + rng.normal(scale=0.1, size=rows)
    names = [f"x{i}" for i in range(p)]
    for lam in (0.01, 1.0):
        model = ridge.fit(x.tolist(), y.tolist(), groups, lam, names)
        m, s, b0, beta = closed_form(x.tolist(), y.tolist(), groups, lam)
        assert np.isfinite(beta).all()
        assert model.coef == pytest.approx(tuple(beta), rel=1e-8, abs=1e-10)
        assert model.intercept == pytest.approx(b0, rel=1e-9, abs=1e-13)
        assert all(math.isfinite(v) for v in (*model.coef, *model.mean, *model.scale))


def test_extreme_finite_inputs_that_overflow_or_underflow_intermediates_are_refused():
    groups = [f"g{i}" for i in range(6)]
    y = [0.1, -0.2, 0.3, 0.0, 0.5, -0.1]
    squares = [[1e200 if i % 2 else -1e200, float(i)] for i in range(6)]    # (x - mean)^2 overflows
    with pytest.raises(PolicyError, match="overflow"):
        ridge.fit(squares, y, groups, 1.0, ["x1", "x2"])
    sums = [[1.5e308, float(i)] for i in range(5)] + [[1.4e308, 5.0]]       # the weighted mean overflows
    with pytest.raises(PolicyError, match="overflow"):
        ridge.fit(sums, y, groups, 1.0, ["x1", "x2"])
    signs = [1.0 if i % 2 else -1.0 for i in range(6)]                      # Z'W(y - b0) overflows
    with pytest.raises(PolicyError, match="overflow"):
        ridge.fit([[s] for s in signs], [s * 1e308 for s in signs], groups, 1.0, ["x1"])
    tiny = [[0.0 if i % 2 else 1e-200, float(i)] for i in range(6)]         # active, its SD underflows to 0
    with pytest.raises(PolicyError, match="underflows"):
        ridge.fit(tiny, y, groups, 1.0, ["x1", "x2"])
    big = [[1e150 * (i - 2.5), float(i)] for i in range(6)]                 # huge but representable: fine
    model = ridge.fit(big, y, groups, 1.0, ["x1", "x2"])
    assert all(math.isfinite(v) for v in (*model.coef, *model.mean, *model.scale, model.intercept))


def test_overflowing_predictions_scores_and_variances_are_refused_not_returned():
    model = ridge.RidgeModel.from_json({"features": ["x"], "lambda": 1.0, "mean": [0.0], "scale": [1.0],
                                        "active": [True], "coef": [2.0], "intercept": 0.0, "training_rows": 2,
                                        "training_groups": 2, "objective": "fixture"})
    assert model.predict([1.0]) == 2.0
    with pytest.raises(PolicyError):
        model.predict([1e308])                       # 2e308 is not a finite prediction
    with pytest.raises(PolicyError):
        ridge.cv_score([0.0, 0.0], [1e200, 1e200], ["a", "b"])
    with pytest.raises(PolicyError):
        ridge.weighted_variance([1e200, -1e200], ["a", "b"])


def test_frozen_models_round_trip_and_refuse_malformed_records():
    X, y, groups = data()
    model = ridge.fit(X, y, groups, 10.0, NAMES)
    again = ridge.RidgeModel.from_json(model.to_json())
    assert again == model and again.predict(X[3]) == model.predict(X[3])
    bad = model.to_json()
    bad["coef"] = bad["coef"][:-1]
    with pytest.raises(VerificationError):
        ridge.RidgeModel.from_json(bad)
    with pytest.raises(VerificationError):
        ridge.RidgeModel.from_json({**model.to_json(), "extra": 1})
    with pytest.raises(PolicyError):
        model.predict(X[3][:2])
