"""Student t tails and quantiles, Welch df (standard library only; scalars).

The regularized incomplete beta I_x(a, b) is evaluated by the continued fraction of Numerical Recipes
(Lentz's method), with the symmetry switch at x = (a + 1)/(a + b + 2). Then for T with df degrees of freedom
P(|T| > t) = I_x(df/2, 1/2) with x = df/(df + t^2). Quantiles come from bisection on the tail, to 1e-12.
Checked in the tests against table values (t(0.95, 5) = 2.015048, the review's 4.330 at 0.99625 and 5 df, the
normal limit 1.959964 at large df).
"""

from __future__ import annotations

import math

_EPS = 1e-15
_FPMIN = 1e-300
_MAX_IT = 10000


def _betacf(a: float, b: float, x: float) -> float:
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < _FPMIN:
        d = _FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, _MAX_IT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = 1.0 + aa / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = 1.0 + aa / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < _EPS:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """The regularized incomplete beta function I_x(a, b) for a, b > 0 and 0 <= x <= 1."""
    if not (a > 0 and b > 0):
        raise ValueError("betainc needs a > 0 and b > 0")
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lfront = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lfront) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lfront) * _betacf(b, a, 1.0 - x) / b


def _check_df(df: float) -> float:
    if not (isinstance(df, (int, float)) and math.isfinite(df) and df > 0):
        raise ValueError("the degrees of freedom must be a positive finite number")
    return min(float(df), 1e7)


def t_two_sided(t: float, df: float) -> float:
    """P(|T| > |t|)."""
    df = _check_df(df)
    if not math.isfinite(t):
        return 0.0
    if t == 0.0:
        return 1.0
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def t_sf(t: float, df: float) -> float:
    """The upper tail P(T > t)."""
    two = t_two_sided(t, df)
    return two / 2.0 if t > 0 else 1.0 - two / 2.0


def t_cdf(t: float, df: float) -> float:
    """P(T <= t)."""
    return 1.0 - t_sf(t, df)


def t_quantile(p: float, df: float) -> float:
    """The p-quantile of Student t (bisection to 1e-12 on the tail)."""
    df = _check_df(df)
    if not (0.0 < p < 1.0):
        raise ValueError("a quantile needs 0 < p < 1")
    if p == 0.5:
        return 0.0
    if p < 0.5:
        return -t_quantile(1.0 - p, df)
    lo, hi = 0.0, 1.0
    while t_sf(hi, df) > 1.0 - p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_sf(mid, df) > 1.0 - p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12 * max(1.0, hi):
            break
    return 0.5 * (lo + hi)


def welch_df(v1: float, n1: int, v2: float, n2: int) -> float:
    """The Welch-Satterthwaite df of s1^2/n1 + s2^2/n2."""
    a, b = v1 / n1, v2 / n2
    denominator = (a * a) / (n1 - 1) + (b * b) / (n2 - 1)
    if denominator <= 0.0:
        return float("inf")
    return (a + b) ** 2 / denominator
