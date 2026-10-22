"""W1-02: the token-axis dose (pure function; values by hand)."""

from __future__ import annotations

import pytest

from scripts.stage1 import dose_axis as da

T = {600: 60_000.0, 1200: 120_000.0, 2400: 240_000.0}
TT = {600: 50_000.0, 1200: 100_000.0, 2400: 200_000.0}
G = {600: 2.0, 1200: 4.0, 2400: 6.0}


def axes(t_total, t_target, rows):
    return {"total_tokens": t_total, "target_tokens": t_target, "rows": rows}


def test_interpolation_equals_hand_values():
    out = da.place({"total_tokens": T, "target_tokens": TT}, G, axes(90_000, 75_000, 900), 3.0)
    tot = out["axes"]["total_tokens"]
    assert tot["t_star"] == 90_000.0                                   # 60,000 + (3 - 2) / (4 - 2) x 60,000
    assert tot["ratio"] == 1.0 and tot["g_random_at_t_m"] == 3.0 and tot["lambda_tok"] == 0.0
    assert out["axes"]["target_tokens"]["t_star"] == 75_000.0
    first = da.place({"total_tokens": T, "target_tokens": TT}, G, axes(30_000, 30_000, 300), 1.5)["axes"]
    assert first["total_tokens"]["t_star"] == 45_000.0 and first["total_tokens"]["ratio"] == 1.5
    assert first["total_tokens"]["g_random_at_t_m"] == 1.0 and first["total_tokens"]["lambda_tok"] == 0.5
    assert first["total_tokens"]["first_segment_only"] is True and tot["first_segment_only"] is False


def test_the_first_crossing_on_a_non_monotone_curve():
    g = {600: 4.0, 1200: 2.0, 2400: 6.0}
    out = da.place({"total_tokens": T, "target_tokens": TT}, g, axes(1, 1, 1), 3.0)["axes"]["total_tokens"]
    assert out["t_star"] == 45_000.0                                   # on (0, 0)-(60,000, 4), not on (120,000, 2)-(240,000, 6)
    assert da.equivalent_dose(da.curve(T, g), 5.0) == 120_000.0 + 3.0 / 4.0 * 120_000.0


def test_no_restoration_gives_zero_and_above_every_point_is_beyond():
    for g_m in (0.0, -1.5):
        out = da.place({"total_tokens": T, "target_tokens": TT}, G, axes(50_000, 40_000, 500), g_m)["axes"]["total_tokens"]
        assert out["t_star"] == da.ZERO and out["ratio"] == 0.0
    out = da.place({"total_tokens": T, "target_tokens": TT}, G, axes(50_000, 40_000, 500), 6.5)["axes"]["total_tokens"]
    assert out["t_star"] == da.BEYOND and out["ratio"] is None
    assert da.equivalent_dose(da.curve(T, G), 6.0) == 240_000.0          # equal to the top point is on the curve


def test_no_extrapolation_past_t_2400():
    out = da.place({"total_tokens": T, "target_tokens": TT}, G, axes(240_001, 200_000, 2400), 3.0)["axes"]
    assert out["total_tokens"]["lambda_tok"] == da.BEYOND and out["total_tokens"]["g_random_at_t_m"] == da.BEYOND
    assert out["target_tokens"]["lambda_tok"] == -3.0                  # exactly T_2400 is on the curve: 3 - 6
    assert da.place_on_axis(T, G, 240_000.0, 3.0)["lambda_tok"] == -3.0


def test_t_m_zero_gives_lambda_equal_to_g_m():
    out = da.place({"total_tokens": T, "target_tokens": TT}, G, axes(0, 0, 0), 2.5)["axes"]
    assert all(out[a]["lambda_tok"] == 2.5 and out[a]["g_random_at_t_m"] == 0.0 for a in da.AXES)
    assert out["total_tokens"]["ratio"] is None and out["total_tokens"]["first_segment_only"] is False


def test_the_row_axis_gives_the_row_doses_exactly():
    for n in da.DOSES:
        out = da.place({"total_tokens": T, "target_tokens": TT}, G, axes(1, 1, n), G[n])["axes"]["rows"]
        assert out["t_star"] == float(n) and out["lambda_tok"] == 0.0 and out["ratio"] == 1.0
    with pytest.raises(da.DoseError, match="the doses themselves"):
        da.place({"total_tokens": T, "target_tokens": TT, "rows": {600: 600, 1200: 1201, 2400: 2400}}, G,
                 axes(1, 1, 1), 1.0)


def test_the_default_axis_is_total_row_tokens():
    assert da.DEFAULT_AXIS == "total_tokens" and da.AXES[0] == "total_tokens"
    assert da.place({"total_tokens": T, "target_tokens": TT}, G, axes(1, 1, 1), 1.0)["default_axis"] == "total_tokens"


@pytest.mark.parametrize("masses, restorations", [
    ({600: 60.0, 1200: 50.0, 2400: 240.0}, G),                           # not rising
    ({600: 0.0, 1200: 120.0, 2400: 240.0}, G),                           # not above 0
    ({600: 60.0, 1200: 120.0}, G),                                       # a dose missing
    (T, {600: 1.0, 1200: float("nan"), 2400: 3.0}),                      # not finite
    (T, {600: 1.0, 1200: True, 2400: 3.0}),                              # not a number
])
def test_undefined_inputs_refuse(masses, restorations):
    with pytest.raises(da.DoseError):
        da.place_on_axis(masses, restorations, 10.0, 1.0)


def test_a_negative_mass_and_a_missing_axis_refuse():
    with pytest.raises(da.DoseError, match="negative"):
        da.place_on_axis(T, G, -1.0, 1.0)
    with pytest.raises(da.DoseError, match="the axes"):
        da.place({"total_tokens": T}, G, axes(1, 1, 1), 1.0)
