"""W1-02 (REQ-27 (b); addendum section 5 item 1; REV3 section 9.3 item 2): the token-axis dose, one pure function.

No randomness, no file input, standard library only. The stage-1 reading (B16, S1) calls ``place``.

**The curve.** Points (0, 0) for a0 and (T_n, G_n) for n = 600, 1,200, 2,400 random rows removed: T_n = the mean removed
mass over the R draws run at dose n (R_600 at seeds 1101-1107; R_1200 and R_2400 at d = 2-4, seeds 1102-1104) and
G_n = the dose's restoration U(a0) - U(R_n) by the primary estimator. The curve is piecewise linear through the four
points in dose order; on each axis T_600 < T_1200 < T_2400 is required.

**Axes** (MSG-04): total row tokens (prompt + target, as trained) is the primary axis (DEFAULT_AXIS); target tokens
(response + end-of-turn) is reported beside it, and rows (PLAN-S section 5.3 item 1) is the third. On the row axis the
dose points are the doses themselves: T_n = n.

**For a filter m** with removed mass T_m and restoration G_m, per axis:
- the token-equivalent random dose T*_m = the first T, from 0 upward, at which the curve reaches G_m (linear inside the
  segment); "0" if G_m <= 0; "beyond the curve" if G_m exceeds every point; and the ratio T*_m / T_m;
- the token-matched contrast Lambda_tok,m = G_m - G_R(T_m), G_R linear between the points; "beyond the curve" if
  T_m > T_2400 (no extrapolation). T_m below T_600 rests on the unmeasured segment from (0, 0) to (T_600, G_600); the
  result says so (``first_segment_only``).
Report only: no label, no alpha claim; the interval is the reading's (LN-38).
"""

from __future__ import annotations

import math
from typing import Mapping

DOSES = (600, 1200, 2400)
AXES = ("total_tokens", "target_tokens", "rows")
DEFAULT_AXIS = "total_tokens"
ZERO, BEYOND = "0", "beyond the curve"


class DoseError(ValueError):
    """An input that the rule does not define."""


def _number(value, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DoseError(f"{what} is not a finite number")
    return float(value)


def curve(masses: Mapping[int, float], restorations: Mapping[int, float]) -> list[tuple[float, float]]:
    """The four curve points (0, 0), (T_600, G_600), (T_1200, G_1200), (T_2400, G_2400), checked."""
    if set(masses) != set(DOSES) or set(restorations) != set(DOSES):
        raise DoseError(f"the curve needs the doses {DOSES} exactly")
    points = [(0.0, 0.0)] + [(_number(masses[n], f"T_{n}"), _number(restorations[n], f"G_{n}")) for n in DOSES]
    if not all(points[i][0] < points[i + 1][0] for i in range(len(points) - 1)):
        raise DoseError("the dose masses must rise strictly from 0 (0 < T_600 < T_1200 < T_2400)")
    return points


def equivalent_dose(points: list[tuple[float, float]], g_m: float):
    """T*_m: the first T from 0 upward where the piecewise-linear curve reaches g_m."""
    g_m = _number(g_m, "G_m")
    if g_m <= 0:
        return ZERO
    if g_m > max(g for _, g in points):
        return BEYOND
    for (t0, g0), (t1, g1) in zip(points, points[1:]):
        if min(g0, g1) <= g_m <= max(g0, g1):
            if g1 == g0:
                return t0
            return t0 + (g_m - g0) / (g1 - g0) * (t1 - t0)
    raise AssertionError("unreachable: a value between 0 and the curve's maximum is reached")


def random_restoration(points: list[tuple[float, float]], t_m: float):
    """G_R(T_m), linear between the points; "beyond the curve" above T_2400."""
    t_m = _number(t_m, "T_m")
    if t_m < 0:
        raise DoseError("a removed mass cannot be negative")
    if t_m > points[-1][0]:
        return BEYOND
    for (t0, g0), (t1, g1) in zip(points, points[1:]):
        if t0 <= t_m <= t1:
            return g0 + (t_m - t0) / (t1 - t0) * (g1 - g0)
    raise AssertionError("unreachable: 0 <= T_m <= T_2400")


def place_on_axis(masses: Mapping[int, float], restorations: Mapping[int, float], t_m: float, g_m: float) -> dict:
    points = curve(masses, restorations)
    t_star = equivalent_dose(points, g_m)
    g_r = random_restoration(points, t_m)
    t_m, g_m = float(t_m), float(g_m)
    ratio = None
    if isinstance(t_star, float) and t_m > 0:
        ratio = t_star / t_m
    elif t_star == ZERO and t_m > 0:
        ratio = 0.0
    return {"curve": [list(p) for p in points], "t_m": t_m, "g_m": g_m, "t_star": t_star, "ratio": ratio,
            "g_random_at_t_m": g_r, "lambda_tok": g_r if g_r == BEYOND else g_m - g_r,
            "first_segment_only": 0 < t_m < points[1][0]}


def place(masses: Mapping[str, Mapping[int, float]], restorations: Mapping[int, float], removed: Mapping[str, float],
          g_m: float) -> dict:
    """W1-02 on all three axes.

    masses: axis -> {600: T_600, 1200: T_1200, 2400: T_2400} (the row axis may be omitted: it is {n: n});
    restorations: {600: G_600, 1200: G_1200, 2400: G_2400}; removed: axis -> T_m (the row axis: the rows removed);
    g_m: the filter's restoration. Returns {"default_axis", "axes": {axis: place_on_axis(...)}}."""
    masses = dict(masses)
    masses.setdefault("rows", {n: n for n in DOSES})
    if set(masses) != set(AXES) or set(removed) != set(AXES):
        raise DoseError(f"place needs the axes {AXES} exactly")
    if {int(k): v for k, v in masses["rows"].items()} != {n: n for n in DOSES}:
        raise DoseError("on the row axis the dose points are the doses themselves")
    return {"default_axis": DEFAULT_AXIS,
            "axes": {axis: place_on_axis(masses[axis], restorations, removed[axis], g_m) for axis in AXES}}
