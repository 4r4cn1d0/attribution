"""Every sensitivity's estimate (REV3 3.4): HB, S-a, S-aW, S-b2x, S-0, S-p, S-G, S-A8, S-tok, and S-a's flag."""

from __future__ import annotations

import math

import numpy as np
import pytest

from scripts.stage1.dose_axis import BEYOND
from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import reml, sensitivities as sens, tdist
from scripts.stage1_s1.reading.schema import validate
from scripts.stage1_s1.reading.settings import design

import synth

SEEDS = tuple(range(1102, 1108))


@pytest.fixture(scope="module")
def world():
    doc = synth.make_input(5, "plan_a", with_variants=True, with_token_axis=True)
    inp = validate(doc)
    dsg = design("plan_a")
    table = inp.tables["U"]
    fits = sens.fit_clusters(table, dsg, 100.0, 0.01)
    return {"inp": inp, "dsg": dsg, "table": table, "fits": fits}


def test_hb_has_one_shift_for_all_eight_arms_with_36_residual_df(world):
    fit = sens.fit_one_shift(world["table"], world["dsg"], 100.0, 0.01)
    assert fit.arms == world["dsg"].fit_arms and fit.residual_df == 36.0
    assert sum(fit.residual_df_by_arm.values()) == pytest.approx(36.0)
    est = sens.u_estimates("HB", world["table"], world["dsg"], 100.0, 0.01, world["fits"])
    assert set(est) == {"P1", "P2", "P3", "P4", "P5", "P6"} and est["P1"].form == "HB"
    assert est["P1"].est == pytest.approx(con.paired_mean(world["table"], "R", "A1", SEEDS, 100.0))
    v, df = reml.seed_variance(fit, "R", "A1", 6)
    assert est["P1"].seed_var == pytest.approx(v)


def test_hbc_clusters_share_no_parameter(world):
    fits = world["fits"]
    assert set(fits) == {"full", "removal"} and fits["full"].arms == ("a0", "S1", "S3", "S4")
    assert fits["removal"].arms == ("R", "A1", "L1", "H1") and fits["full"].residual_df == 15.0


def test_s_a_pools_over_eight_arms_with_42_df_and_uses_every_seed(world):
    est = sens.u_estimates("S-a", world["table"], world["dsg"], 100.0, 0.01, world["fits"])
    e = est["P4"]
    assert e.seed_df == 42.0 and e.form.startswith("S-a")
    t = world["table"]
    a0 = np.mean([100 * t[("a0", j)].mean() for j in range(1101, 1108)])
    s1 = np.mean([100 * t[("S1", j)].mean() for j in SEEDS])
    assert e.est == pytest.approx(a0 - s1)                                 # a0_1101 enters S-a (REV3 3.2)
    assert e.est != pytest.approx(con.paired_mean(t, "a0", "S1", SEEDS, 100.0), abs=1e-9)


def test_s_aw_is_welch(world):
    e = sens.u_estimates("S-aW", world["table"], world["dsg"], 100.0, 0.01, world["fits"])["P1"]
    t = world["table"]
    r = np.array([100 * t[("R", j)].mean() for j in range(1101, 1108)])
    a1 = np.array([100 * t[("A1", j)].mean() for j in SEEDS])
    assert e.seed_var == pytest.approx(r.var(ddof=1) / 7 + a1.var(ddof=1) / 6)
    assert e.seed_df == pytest.approx(tdist.welch_df(r.var(ddof=1), 7, a1.var(ddof=1), 6))


def test_s_b2x_has_36_pooled_df_and_the_item_part(world):
    e = sens.u_estimates("S-b2x", world["table"], world["dsg"], 100.0, 0.01, world["fits"])["P5"]
    assert e.seed_df == 36.0 and e.with_item and e.est == pytest.approx(con.paired_mean(world["table"], "S1", "S3", SEEDS, 100.0))


def test_s_0_drops_the_item_part_only(world):
    s0 = sens.u_estimates("S-0", world["table"], world["dsg"], 100.0, 0.01, world["fits"])["P1"]
    primary = con.contrast_fit(world["table"], world["fits"]["removal"], "R", "A1", SEEDS, 100.0, True)
    assert not s0.with_item and s0.item_var == 0.0 and s0.est == primary.est
    assert s0.se == pytest.approx(math.sqrt(primary.seed_var)) and s0.df == pytest.approx(primary.seed_df)
    assert s0.se <= primary.se


def test_s_p_is_the_paired_t_with_5_df(world):
    e = sens.u_estimates("S-p", world["table"], world["dsg"], 100.0, 0.01, world["fits"])["P2"]
    assert e.seed_df == 5.0 and e.pairs == 6
    d = np.array([100 * (world["table"][("R", j)].mean() - world["table"][("L1", j)].mean()) for j in SEEDS])
    assert e.seed_var == pytest.approx(d.var(ddof=1) / 6)


def test_s_g_refits_hbc_on_each_variant(world):
    out = sens.variant_estimates(world["inp"].variants, world["dsg"], 100.0, 0.01)
    assert set(out) == {"coherent", "g3_unscored_unsafe", "g3_controversial_unsafe"}
    for v, ests in out.items():
        assert set(ests) == {"P1", "P2", "P3", "P4", "P5", "P6"} and ests["P1"].form == f"S-G {v}"
        table = world["inp"].variants[v]
        assert ests["P4"].est == pytest.approx(con.paired_mean(table, "a0", "S1", SEEDS, 100.0))


def test_s_a8_uses_the_reml_variance_over_j_for_theta0(world):
    inp, dsg = world["inp"], world["dsg"]
    fits_o = sens.fit_clusters(inp.tables["O"], dsg, 100.0, 0.01)
    a8 = con.contrast_theta0_a8(inp.tables["O"], fits_o["full"], "S1", SEEDS, inp.theta0_o, 100.0)
    ln20 = con.contrast_theta0(inp.tables["O"], "S1", SEEDS, inp.theta0_o, 100.0)
    assert a8.est == pytest.approx(ln20.est) and a8.item_var == pytest.approx(ln20.item_var)
    assert a8.seed_var == pytest.approx(fits_o["full"].sigma2["S1"] / 6) and ln20.seed_df == 5.0


def test_equal_variance_flag():
    a = con.Estimate("x", "S-a", 3.0, 1.0, 42.0, 1.0, 42.0, 0.0, 0.0, 6, 200, False)        # p ~ 0.004
    w = con.Estimate("x", "S-aW", 3.0, 1.6, 6.0, 2.56, 6.0, 0.0, 0.0, 6, 200, False)         # p ~ 0.1
    assert sens.equal_variance_flag(a, w, 0.0075) and not sens.equal_variance_flag(w, a, 0.0075)


def test_s_tok_point_estimate_and_common_seed_interval(world):
    inp, dsg, t = world["inp"], world["dsg"], world["table"]
    out = sens.token_axis(t, dsg, 100.0, inp.token_axis)
    assert out["common_seeds"] == [1102, 1103, 1104] and len(out["curve"]) == 4 and out["curve"][0] == [0.0, 0.0]
    g600 = con.paired_mean(t, "a0", "R", tuple(range(1101, 1108)), 100.0)
    assert out["curve"][1] == pytest.approx([60000.0, g600])
    rec = out["arms"]["A1"]
    g_m = con.paired_mean(t, "a0", "A1", SEEDS, 100.0)
    t_m, (t0, g0), (t1, g1) = 70000.0, out["curve"][1], out["curve"][2]
    g_r = g0 + (t_m - t0) / (t1 - t0) * (g1 - g0)
    assert rec["g_m"] == pytest.approx(g_m) and rec["lambda_tok"] == pytest.approx(g_m - g_r)
    assert rec["df"] == 2 and len(rec["per_seed_lambda_tok"]) == 3 and not rec["first_segment_only"]
    half = tdist.t_quantile(0.95, 2) * rec["se_common_seeds"]
    assert rec["interval_90"] == pytest.approx([g_m - g_r - half, g_m - g_r + half])
    far = dict(inp.token_axis)
    far["removed"] = {"H1": 300000.0}
    assert sens.token_axis(t, dsg, 100.0, far)["arms"]["H1"]["lambda_tok"] == BEYOND
