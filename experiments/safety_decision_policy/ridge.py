"""Ridge regression with group cross-fitting.

Fitting uses numpy (the pinned 2.2.6, imported only when fitting). Prediction from a frozen
model is pure Python with ``math.fsum``: ranking from a frozen, hash-pinned record calls no BLAS.
The record's coefficients themselves come from a numpy fit (see Numerics).

Model, one per target: minimize ``sum_i w_i (y_i - b0 - z_i . beta)^2 + lambda ||beta||^2`` with

- ``w_i = 1 / n_g(i)``, ``n_g`` the rows of row i's group: every group carries total weight 1,
  so several seeds of one group never count as several independent groups;
- ``z_ij = (x_ij - m_j) / s_j``, ``m_j`` and ``s_j`` the weighted mean and weighted population
  SD of feature j over the TRAINING rows only. A feature constant over the training rows
  (max == min) is inactive: coefficient 0, ignored when predicting;
- ``b0`` unpenalized (the weighted mean of y, because z is weighted-centered);

solved as ``(Z'WZ + lambda I) beta = Z'W (y - b0)``.

Numerics: the Gram matrix and right-hand side are elementwise numpy reductions, not a BLAS
matrix product, so floating-point status flags raised inside a BLAS matmul do not reach the
fit's error checks. In the lead's verification of the second stage-B snapshot such matmul
warnings appeared only in the tests' BLAS reference calculations, not in production fitting;
their root cause is not established. Standardization, Gram and right-hand side run with numpy overflow, invalid and
divide errors raised: an extreme finite input whose intermediate arithmetic overflows refuses
(PolicyError) instead of warning, an active feature whose weighted SD underflows to zero refuses,
and every mean, scale, intercept, Gram entry, right-hand side, coefficient, prediction, squared
error and variance must be finite. With lambda > 0 the system is positive definite and is solved
by ``numpy.linalg.solve``, which still runs numpy's linked LAPACK/BLAS: a fitted record is NOT
claimed to be bitwise independent of the BLAS/LAPACK build (cross-build identity has not been
verified); the frozen record is pinned by hash instead.

Cross-fitting: leave-one-group-out folds (all rows of a group, i.e. all its seeds, in one fold).
A fold's score is the mean squared error over its rows; the CV score is the mean over folds, so
groups count equally whatever their number of seeds. Lambda: the smallest CV score, exact ties
to the larger lambda. Nested cross-fitting selects lambda inside each outer fold from inner
leave-one-group-out folds of the remaining groups only, refits on them and predicts the outer
group: an out-of-sample score of the tuned procedure, unlike the optimistic CV score of the
selected lambda.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from statistics import fmean
from typing import Sequence

from .common import PolicyError, VerificationError, finite

__all__ = ["RidgeModel", "group_weights", "fit", "logo_predictions", "cv_score", "tune", "nested",
           "weighted_variance"]


@dataclass(frozen=True)
class RidgeModel:
    features: tuple[str, ...]
    lam: float
    mean: tuple[float, ...]
    scale: tuple[float, ...]
    active: tuple[bool, ...]
    coef: tuple[float, ...]
    intercept: float
    training_rows: int
    training_groups: int

    def predict(self, x: Sequence[float]) -> float:
        if len(x) != len(self.features):
            raise PolicyError(f"expected {len(self.features)} feature values, got {len(x)}")
        try:
            value = self.intercept + math.fsum(c * (v - m) / s for c, v, m, s, a in
                                               zip(self.coef, x, self.mean, self.scale, self.active) if a)
        except (OverflowError, ValueError) as exc:
            raise PolicyError(f"the prediction overflows ({exc}); refused") from None
        if not math.isfinite(value):
            raise PolicyError("non-finite prediction (an extreme finite input overflowed); refused")
        return value

    def to_json(self) -> dict:
        return {"features": list(self.features), "lambda": self.lam, "mean": list(self.mean),
                "scale": list(self.scale), "active": list(self.active), "coef": list(self.coef),
                "intercept": self.intercept, "training_rows": self.training_rows,
                "training_groups": self.training_groups,
                "objective": "sum_i w_i (y_i - b0 - z_i.beta)^2 + lambda ||beta||^2; w_i = 1/rows of "
                             "its group; z standardized on the training rows; b0 unpenalized"}

    @staticmethod
    def from_json(data: dict) -> RidgeModel:
        keys = {"features", "lambda", "mean", "scale", "active", "coef", "intercept", "training_rows",
                "training_groups", "objective"}
        if not isinstance(data, dict) or set(data) != keys:
            raise VerificationError("malformed ridge model")
        p = len(data["features"])
        if not all(len(data[k]) == p for k in ("mean", "scale", "active", "coef")):
            raise VerificationError("ridge model vectors differ in length")
        if not all(isinstance(a, bool) for a in data["active"]):
            raise VerificationError("ridge model active flags must be booleans")
        model = RidgeModel(tuple(data["features"]), finite(data["lambda"], "lambda"),
                           tuple(finite(v, "mean") for v in data["mean"]),
                           tuple(finite(v, "scale") for v in data["scale"]), tuple(data["active"]),
                           tuple(finite(v, "coef") for v in data["coef"]),
                           finite(data["intercept"], "intercept"), int(data["training_rows"]),
                           int(data["training_groups"]))
        if any(s <= 0 for s, a in zip(model.scale, model.active) if a):
            raise VerificationError("an active feature needs a positive scale")
        return model


def _numpy():
    try:
        import numpy
    except ImportError as exc:  # pragma: no cover - the pinned environment has numpy
        raise PolicyError("fitting needs numpy (pinned numpy==2.2.6)") from exc
    return numpy


def group_weights(groups: Sequence[str]) -> list[float]:
    counts = Counter(groups)
    return [1.0 / counts[g] for g in groups]


def weighted_variance(y: Sequence[float], groups: Sequence[str]) -> float:
    """Population variance of y with group-equal weights."""
    w = group_weights(groups)
    total = math.fsum(w)
    try:
        mean = math.fsum(wi * yi for wi, yi in zip(w, y)) / total
        value = math.fsum(wi * (yi - mean) ** 2 for wi, yi in zip(w, y)) / total
    except (OverflowError, ValueError) as exc:
        raise PolicyError(f"the target variance overflows ({exc}); refused") from None
    if not math.isfinite(value):
        raise PolicyError("non-finite target variance; refused")
    return value


def fit(X: Sequence[Sequence[float]], y: Sequence[float], groups: Sequence[str], lam: float,
        features: Sequence[str]) -> RidgeModel:
    if not (isinstance(lam, (int, float)) and not isinstance(lam, bool) and lam > 0 and math.isfinite(lam)):
        raise PolicyError("lambda must be a positive finite number")
    if not X or len(X) != len(y) or len(y) != len(groups):
        raise PolicyError("X, y and groups must be non-empty and of equal length")
    np = _numpy()
    x = np.asarray(X, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != len(features):
        raise PolicyError("X columns differ from the feature names")
    t = np.asarray(y, dtype=np.float64)
    if not (np.isfinite(x).all() and np.isfinite(t).all()):
        raise PolicyError("non-finite training values")
    w = np.asarray(group_weights(groups), dtype=np.float64)
    active = x.max(axis=0) > x.min(axis=0)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            total = w.sum()
            mean = (w[:, None] * x).sum(axis=0) / total
            centered = x - mean
            sd = np.sqrt((w[:, None] * centered ** 2).sum(axis=0) / total)
            if np.any(sd[active] <= 0):
                raise PolicyError("an active feature's weighted SD underflows to zero (extreme finite scale); refused")
            scale = np.where(active, sd, 1.0)
            z = centered[:, active] / scale[active]
            b0 = float((w * t).sum() / total)
            zw = w[:, None] * z
            gram = (zw[:, :, None] * z[:, None, :]).sum(axis=0) + float(lam) * np.eye(z.shape[1])
            rhs = (zw * (t - b0)[:, None]).sum(axis=0)
    except FloatingPointError as exc:
        raise PolicyError(f"ridge fit: an intermediate overflowed or became undefined ({exc}); extreme finite "
                          "inputs are refused") from None
    for name, value in (("mean", mean), ("scale", scale), ("intercept", b0), ("Gram matrix", gram),
                        ("right-hand side", rhs)):
        if not np.isfinite(value).all():
            raise PolicyError(f"ridge fit: non-finite {name}; refused")
    coef = np.zeros(x.shape[1])
    if z.shape[1]:
        coef[active] = np.linalg.solve(gram, rhs)
    if not np.isfinite(coef).all():
        raise PolicyError("ridge fit: non-finite coefficients; refused")
    return RidgeModel(tuple(features), float(lam), tuple(float(v) for v in mean),
                      tuple(float(v) for v in scale), tuple(bool(a) for a in active),
                      tuple(float(v) for v in coef), b0, len(y), len(set(groups)))


def logo_predictions(X: Sequence[Sequence[float]], y: Sequence[float], groups: Sequence[str],
                     lam: float, features: Sequence[str]) -> list[float]:
    """Out-of-fold predictions: each group predicted by a model fit without any of its rows
    (standardization included)."""
    if len(set(groups)) < 2:
        raise PolicyError("leave-one-group-out needs at least two groups")
    preds: list[float | None] = [None] * len(y)
    for held in sorted(set(groups)):
        train = [i for i, g in enumerate(groups) if g != held]
        model = fit([X[i] for i in train], [y[i] for i in train], [groups[i] for i in train], lam, features)
        for i, g in enumerate(groups):
            if g == held:
                preds[i] = model.predict(X[i])
    return [float(p) for p in preds]


def cv_score(y: Sequence[float], preds: Sequence[float], groups: Sequence[str]) -> tuple[float, dict[str, float]]:
    """(mean over groups of each group's mean squared error, per-group scores)."""
    try:
        per_group = {g: fmean((y[i] - preds[i]) ** 2 for i in range(len(y)) if groups[i] == g)
                     for g in sorted(set(groups))}
        score = fmean(per_group.values())
    except (OverflowError, ValueError) as exc:
        raise PolicyError(f"a squared error overflows ({exc}); refused") from None
    if not math.isfinite(score):
        raise PolicyError("non-finite cross-validation score; refused")
    return score, per_group


def tune(X: Sequence[Sequence[float]], y: Sequence[float], groups: Sequence[str],
         grid: Sequence[float], features: Sequence[str]) -> dict:
    results = []
    for lam in grid:
        preds = logo_predictions(X, y, groups, lam, features)
        score, per_group = cv_score(y, preds, groups)
        results.append({"lambda": float(lam), "score": score, "per_group": per_group, "predictions": preds})
    best = min(results, key=lambda r: (r["score"], -r["lambda"]))
    return {"results": results, "selected": best["lambda"], "selected_score": best["score"]}


def nested(X: Sequence[Sequence[float]], y: Sequence[float], groups: Sequence[str],
           grid: Sequence[float], features: Sequence[str]) -> dict:
    """Outer leave-one-group-out with lambda chosen by inner leave-one-group-out only."""
    if len(set(groups)) < 3:
        raise PolicyError("nested cross-fitting needs at least three groups")
    preds: list[float | None] = [None] * len(y)
    chosen = {}
    for held in sorted(set(groups)):
        train = [i for i, g in enumerate(groups) if g != held]
        tx, ty, tg = [X[i] for i in train], [y[i] for i in train], [groups[i] for i in train]
        lam = tune(tx, ty, tg, grid, features)["selected"]
        chosen[held] = lam
        model = fit(tx, ty, tg, lam, features)
        for i, g in enumerate(groups):
            if g == held:
                preds[i] = model.predict(X[i])
    score, per_group = cv_score(y, [float(p) for p in preds], groups)
    return {"predictions": [float(p) for p in preds], "selected_by_fold": chosen, "score": score,
            "per_group": per_group}
