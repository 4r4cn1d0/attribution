"""REQ-17 (the generative model and the pre-outcome simulation), W1-14 and lead decisions L15: synthetic only."""

from __future__ import annotations

import copy
import math

import numpy as np
import pytest

from experiments.safety_selection.common import sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1.selector import simulate as sm
from scripts.stage1.selector import spec

import selector_fixtures as fx


def setup(menu_id="category", convention="C-full", reps=range(8), sim=None, S=None):
    S0, M0, _ = fx.tiny()
    return sm._setup(S or S0, sim or M0, menu_id, convention, reps), (S or S0), (sim or M0)


# ----- settings and labels -------------------------------------------------------------------------------


def test_the_simulate_settings_load_with_their_literal_pin():
    assert sha256_file(sm.SETTINGS_PATH) == sm.SETTINGS_SHA256
    settings, digest = sm.load()
    assert digest == sm.SETTINGS_SHA256 and settings["draws"] == sm.DRAW_KEYS


def test_the_noise_is_the_l15_values_never_the_gate_value():
    M = fx.raw("selector_simulate")
    assert M["model"]["u_seed_sd_pp"] == {"central": 2.65, "high": 3.85}
    bad = copy.deepcopy(M)
    bad["model"]["u_seed_sd_pp"]["central"] = 1.83
    with pytest.raises(s1.Refusal, match="2.65"):
        sm.check(bad)


def test_the_two_appended_labels_have_the_l13_form():
    reg = s1.registry()
    for key in ("selector.seed_shift", "selector.hetero"):
        entry = reg[key]
        assert entry.parts == ("replicate",) and entry.owner == "scripts/stage1/selector/simulate.py"
        assert s1.LABEL_PATTERN.match(entry.label) and not entry.frozen
    raw = fx.raw("selector_simulate")
    assert set(raw["label_entries"]) == {v for v in sm.DRAW_KEYS.values()}


def test_the_rho_grid_is_the_settings_grid_and_nothing_else():
    M = fx.raw("selector_simulate")
    assert sm.rho_grid(M) == [0.0, 0.67]                       # A7 in force (LW-12, LN-10)
    with pytest.raises(s1.Refusal, match="rho grid"):
        sm.rho_grid(M, [0.0, 0.5])
    M["model"]["rho_mode"] = "default"                         # the fallback: rho = 0 only (L15 (1))
    assert sm.rho_grid(M, [0.0]) == [0.0]


def test_the_uo_correlation_comes_from_the_gate_a_seeds():
    M = fx.raw("selector_simulate")
    u, o = M["model"]["uo_correlation"]["gate_a_u_pp"], M["model"]["uo_correlation"]["gate_a_o_pp"]
    du, do = np.array(u) - np.mean(u), np.array(o) - np.mean(o)
    hand = float((du * do).sum() / math.sqrt((du ** 2).sum() * (do ** 2).sum()))
    assert sm.uo_correlation(M) == pytest.approx(hand) and sm.uo_correlation(M) == pytest.approx(-0.4725, abs=1e-4)
    assert np.std(u, ddof=1) == pytest.approx(2.65, abs=0.005)        # the central sigma is these seeds' SD


# ----- draws and common random numbers -------------------------------------------------------------------


def test_a_replicates_draws_do_not_depend_on_its_batch():
    (menu, geom, ctx, d, *_), S, M = setup(reps=range(0, 6))
    (_, _, _, d2, *_), _, _ = setup(reps=range(3, 5))
    for key in ("noise", "shift", "hetero", "winner", "shares", "diag", "uninformative", "sim2"):
        assert np.array_equal(d[key][3:5], d2[key]), key


def test_the_noise_array_has_the_fixed_shape_whatever_the_policy():
    (menu, geom, ctx, d, *_), S, M = setup()
    assert d["noise"].shape == (8, 2 + menu.axis_size(), ctx.max_seeds, len(ctx.phi_grid), len(ctx.psi_grid), 5)
    (m128, g128, c128, d128, *_), _, _ = setup("planted_128", reps=range(2))
    assert d128["noise"].shape[1] == 2 + 254 and d128["diag"].shape == (2, 4800)


def test_at_c_d_zero_and_k_m_both_policies_make_the_same_pick_in_every_replicate():
    """L15 (4): the diagnostic at c_d = 0 and k = M runs the same rule on the same draws as the runs-only policy."""
    (menu, geom, ctx, d, points, G, tr), S, M = setup(reps=range(30))
    obs = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.0), tr["coherent"])
    for point in sm.quality_points(M, geom):
        score = sm.scores(geom, M, d, G, point)
        for rule in ("one_shot", "halving"):
            for b in (2.0, 8.0):
                runs = spec.select(ctx, obs, rule=rule, budget=b)
                diag = spec.select(ctx, obs, rule=rule, budget=b, scores=score, k=menu.M, c_d=0.0)
                assert np.array_equal(runs.pick, diag.pick) and np.array_equal(runs.spent, diag.spent)


def test_the_diagnostic_pass_pairs_with_the_runs_only_pass_exactly():
    S, M, _ = fx.tiny()
    frozen = {"rule": {str(b): "halving" for b in M["grids"]["budgets"]}}
    task = {"spec": S, "sim": M, "menu": "category", "convention": "C-full", "pass": "B", "start": 0, "stop": 10,
            "frozen": frozen, "placement": False}
    out = sm.run_chunk(task)
    for b in M["grids"]["budgets"]:
        for q in ("r=0", "r=1", "uninformative"):
            s = out["sums"][(b, 0.0, q, 8)]
            assert (s.data["d2"] == 0).all(), (b, q)


# ----- the noise model (W1-14) ---------------------------------------------------------------------------


def test_with_zero_noise_the_simulated_pick_is_the_true_best():
    S, M, _ = fx.tiny()
    M = copy.deepcopy(M)
    M["model"]["u_sampling_variance_full_pp2"] = 0.0
    M["model"]["o"]["seed_sd_pp"] = 0.0
    M["model"]["l"]["seed_sd_nats"] = 0.0
    S = copy.deepcopy(S)
    S["screen"]["o_prompt_sd_pp"] = 0.0
    (menu, geom, ctx, d, points, G, tr), _, _ = setup(reps=range(20), sim=M, S=S)
    obs = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(0.0, 0.0), tr["coherent"])
    for rule in ("one_shot", "halving"):
        res = sm.outcome(spec.select(ctx, obs, rule=rule, budget=16.0), tr)
        assert res["found"].all() and (res["regret"] < 1e-9).all()


def test_an_equal_shift_on_every_option_and_keep_leaves_the_pick_unchanged():
    (menu, geom, ctx, d, points, G, tr), S, M = setup(reps=range(20))
    obs = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.0), tr["coherent"])
    shifted = copy.copy(obs)
    shifted.u = obs.u + 7.0
    shifted.keep_u = obs.keep_u + 7.0
    for rule in ("one_shot", "halving"):
        assert np.array_equal(spec.select(ctx, obs, rule=rule, budget=8.0).pick,
                              spec.select(ctx, shifted, rule=rule, budget=8.0).pick)


def _same_seed_correlation(rho: float, reps: int = 1500) -> float:
    S, M, _ = fx.tiny()
    M = copy.deepcopy(M)
    M["model"]["rho_mode"] = "a7_switch"
    (menu, geom, ctx, d, points, G, tr), _, _ = setup(reps=range(reps), sim=M)
    obs = sm.observations(geom, ctx, M, d, G[:1], sm.NoiseCase(2.65, rho), tr["coherent"][None][:1].reshape(-1))
    a, b = obs.u[:, 0, 0, ctx.a1, ctx.c1], obs.u[:, 1, 0, ctx.a1, ctx.c1]
    g = G[0]
    return float(np.corrcoef(a + g[:, 0], b + g[:, 1])[0, 1])


def test_the_shared_seed_shift_couples_options_at_the_same_seed():
    assert abs(_same_seed_correlation(0.0)) < 0.08
    assert _same_seed_correlation(0.67) == pytest.approx(0.67, abs=0.06)


def test_crn_holds_across_rho():
    (menu, geom, ctx, d, points, G, tr), S, M = setup(reps=range(5))
    a = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.0), tr["coherent"])
    b = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.67), tr["coherent"])
    shift = 2.65 * math.sqrt(0.67) * d["shift"]
    train0, train1 = math.sqrt(2.65 ** 2 - 2.314), math.sqrt(0.33 * 2.65 ** 2 - 2.314)
    T = d["noise"][:, 2:, :, ctx.a1, ctx.c1, 0]
    rebuilt = b.u[:len(d["sim2"]), :, :, ctx.a1, ctx.c1] - shift[:, None, :] - (train1 - train0) * T
    assert np.allclose(rebuilt, a.u[:len(d["sim2"]), :, :, ctx.a1, ctx.c1])


def test_the_2x_option_is_drawn_by_its_label_and_is_never_keep():
    (menu, geom, ctx, d, points, G, tr), S, M = setup(reps=range(4000))
    expected = [int(s1.numpy_generator("selector.hetero", r).integers(menu.M)) for r in range(5)]
    assert d["hetero"][:5].tolist() == expected and set(d["hetero"].tolist()) <= set(range(menu.M))
    base = sm.observations(geom, ctx, M, d, G[:1], sm.NoiseCase(2.65, 0.0), tr["coherent"])
    het = sm.observations(geom, ctx, M, d, G[:1], sm.NoiseCase(2.65, 0.0, True), tr["coherent"])
    assert np.array_equal(base.keep_u, het.keep_u)
    rows = np.arange(len(d["hetero"]))
    noise = het.u[rows, d["hetero"], 0, ctx.a1, ctx.c1] - (48.27777777777778 - G[0, rows, d["hetero"]])
    assert np.std(noise) == pytest.approx(2.0 * 2.65, rel=0.06)
    other = (d["hetero"] + 1) % menu.M
    plain = het.u[rows, other, 0, ctx.a1, ctx.c1] - (48.27777777777778 - G[0, rows, other])
    assert np.std(plain) == pytest.approx(2.65, rel=0.06)


def test_a_lean_run_has_the_lean_sampling_variance():
    (menu, geom, ctx, d, points, G, tr), S, M = setup("category", "C-lean", reps=range(4000))
    obs = sm.observations(geom, ctx, M, d, G[:1], sm.NoiseCase(2.65, 0.0), tr["coherent"])
    noise = obs.u[:, 0, 0, ctx.a1, ctx.c1] - (48.27777777777778 - G[0, :, 0])
    assert np.var(noise) == pytest.approx(2.65 ** 2 + 2 * 2.314, rel=0.08)
    keep = obs.keep_u[:, 0] - 48.27777777777778
    assert np.var(keep) == pytest.approx(2.65 ** 2, rel=0.08)


def test_o_noise_follows_the_error_model_and_the_uo_correlation():
    (menu, geom, ctx, d, points, G, tr), S, M = setup(reps=range(6000))
    bank = 4.1 * math.sqrt(100 / 500)                          # the dev-100 prompt part scaled to the 500 bank
    assert ctx.o_prompts == 500 and ctx.o_prompt_sd == pytest.approx(bank)
    obs = sm.observations(geom, ctx, M, d, G[:1], sm.NoiseCase(2.65, 0.0), tr["coherent"])
    o = obs.o[:, 0, 0] - 4.666666666666667
    assert np.var(o) == pytest.approx(1.15 ** 2 + bank ** 2, rel=0.08)
    u = obs.u[:, 0, 0, ctx.a1, ctx.c1] - (48.27777777777778 - G[0, :, 0])
    seed_part = o - bank * d["noise"][:, 2, 0, ctx.a1, ctx.c1, 4]
    assert np.corrcoef(u, seed_part)[0, 1] == pytest.approx(sm.uo_correlation(M), abs=0.05)


# ----- the prior, the effects and the truth --------------------------------------------------------------


def test_the_effect_shapes_have_the_same_total():
    (menu, geom, ctx, d, points, G, tr), S, M = setup(reps=range(50))
    M2 = copy.deepcopy(M)
    M2["prior"]["category"]["sizes_pp"] = [8.0]
    pts = sm.prior_points(M2, geom)
    G2 = sm.true_effects(geom, d, pts, M2)
    assert [p[0] for p in pts] == ["one_winner", "spread"]
    assert np.allclose(G2.sum(axis=2), 8.0) and ((G2[0] > 0).sum(axis=1) == 1).all()


def test_planted_effects_follow_the_37_row_leaf_at_every_m():
    for menu_id, M in (("planted_8", 8), ("planted_32", 32), ("planted_128", 128)):
        (menu, geom, ctx, d, points, G, tr), S, Msim = setup(menu_id, reps=range(40))
        assert (geom.leaf_rows[d["leaf"]] == 37).all()
        cells = sm.planted_cell(geom, d["leaf"])
        assert (G[0, np.arange(40), cells] == 10.0).all() and (G[0].sum(axis=1) == 10.0).all()
    assert np.array_equal(setup("planted_8", reps=range(40))[0][3]["leaf"],
                          setup("planted_128", reps=range(40))[0][3]["leaf"])


def test_a_truly_infeasible_pick_scores_zero_and_is_a_violation():
    S, M, _ = fx.tiny()
    M = copy.deepcopy(M)
    M["model"]["true_effects"]["o_pp"]["per_option"] = {"brainstorming": 40.0}
    (menu, geom, ctx, d, points, G, tr), _, _ = setup(reps=range(4), sim=M)
    i = menu.ids.index("brainstorming")
    assert not tr["feasible"][:, i, :].any() and tr["feasible"][:, (i + 1) % 8, :].all()
    sel = spec.Selection(np.full((tr["G"].shape[0], 3), i), np.zeros(tr["G"].shape[0]), np.zeros((1, 8)), "x")
    res = sm.outcome(sel, tr)
    assert (res["g"] == 0).all() and res["violation"].all()
    assert (tr["V"] == np.where(np.arange(8) == i, -np.inf, tr["G"]).max(axis=1)[:, None]).all()


def test_tree_sums_give_each_group_the_sum_of_its_cells():
    G = np.arange(8.0)[None, :]
    axis = sm.tree_sums(G, 8)
    assert axis[0, :8].tolist() == G[0].tolist()
    assert axis[0, 8:].tolist() == [6.0, 22.0, 1.0, 5.0, 9.0, 13.0]   # nodes 2..7


# ----- diagnostic quality (L15 (6)) ----------------------------------------------------------------------


def _category(reps=3000, shape="spread"):
    (menu, geom, ctx, d, points, G, tr), S, M = setup(reps=range(reps))
    p = [i for i, pt in enumerate(points) if pt[0] == shape][0]
    return menu, geom, ctx, d, G[p:p + 1], M


def test_r_zero_gives_the_true_best():
    menu, geom, ctx, d, G, M = _category(200)
    score = sm.scores(geom, M, d, G, {"kind": "rs", "r": 0.0})
    assert np.array_equal(score.argmax(axis=1), G[0].argmax(axis=1))


@pytest.mark.parametrize("r", [0.5, 1.0, 2.0, 4.0])
def test_the_score_correlation_is_about_one_over_root_one_plus_r_squared(r):
    menu, geom, ctx, d, G, M = _category(3000)
    score = sm.scores(geom, M, d, G, {"kind": "rs", "r": r})
    g = G[0] - G[0].mean(axis=1, keepdims=True)
    s = score - score.mean(axis=1, keepdims=True)
    pooled = float((g * s).sum() / math.sqrt((g ** 2).sum() * (s ** 2).sum()))
    assert pooled == pytest.approx(1 / math.sqrt(1 + r * r * 7 / 8), abs=0.03)


def test_uninformative_hits_the_best_at_about_one_over_m():
    menu, geom, ctx, d, G, M = _category(4000, "one_winner")
    score = sm.scores(geom, M, d, G, {"kind": "uninformative"})
    hit = (score.argmax(axis=1) == G[0].argmax(axis=1)).mean()
    assert hit == pytest.approx(1 / 8, abs=0.02)


def test_sim2_picks_the_true_best_half_the_time():
    menu, geom, ctx, d, G, M = _category(4000, "one_winner")
    score = sm.scores(geom, M, d, G, {"kind": "sim2", "p_best": 0.5})
    assert (score.argmax(axis=1) == G[0].argmax(axis=1)).mean() == pytest.approx(0.5, abs=0.03)


def test_the_planted_row_model():
    (menu, geom, ctx, d, points, G, tr), S, M = setup("planted_128", reps=range(400))
    cells = sm.planted_cell(geom, d["leaf"])
    null = sm.scores(geom, M, d, G, {"kind": "row_auc", "auc": 0.5})
    assert (null.argmax(axis=1) == cells).mean() < 0.05
    strong = sm.scores(geom, M, d, G, {"kind": "row_auc", "auc": 0.9})
    assert (strong.argmax(axis=1) == cells).mean() > 0.95
    place = sm.placement_values(geom, ctx, M, d, G, strong, [1, 4], {"kind": "row_auc", "auc": 0.9})
    assert place["row_auc"].mean() == pytest.approx(0.9, abs=0.01) and place["top_k_hit"][1].mean() > 0.95


def test_the_category_placement_statistic_is_a_spearman_rho():
    menu, geom, ctx, d, G, M = _category(400, "spread")
    score = sm.scores(geom, M, d, G, {"kind": "rs", "r": 0.0})
    rho = sm.placement_values(geom, ctx, M, d, G, score, [1], {"kind": "rs", "r": 0.0})["spearman_rho"]
    assert rho.shape == (400,) and (np.abs(rho) <= 1 + 1e-12).all() and rho.mean() > 0.1
    a = np.array([[1.0, 2.0, 3.0, 4.0]])
    assert sm._spearman(a, a)[0] == pytest.approx(1.0) and sm._spearman(a, -a)[0] == pytest.approx(-1.0)


# ----- the frozen choices and the Monte Carlo SE ---------------------------------------------------------


def test_the_rule_choice_follows_the_criterion_with_ties_to_the_simpler_rule():
    rng = np.random.default_rng(1)
    base = rng.normal(5, 1, 4000)
    crit = {"one_shot": base, "halving": base + 1.0, "bisection": base + 1.0}
    out = sm.choose_rule(crit, ["one_shot", "halving", "bisection"], 2.0)
    assert out["chosen"] == "halving" and out["table"]["bisection"]["ties_best"]
    crit = {"one_shot": base + 0.001 * rng.normal(size=4000), "halving": base + 0.5, "bisection": base}
    out = sm.choose_rule(crit, ["one_shot", "halving", "bisection"], 2.0)
    assert out["chosen"] == "halving" and out["best_by_mean"] == "halving"
    noisy = {"one_shot": base, "halving": base + 0.01 + rng.normal(0, 1, 4000)}
    out = sm.choose_rule(noisy, ["one_shot", "halving"], 2.0)
    assert out["chosen"] == "one_shot" and all(v["mc_se"] > 0 for v in out["table"].values())
    assert max(v["paired_difference_mc_se"] for v in out["table"].values()) > 0


def test_the_k_choice_ties_to_the_larger_k():
    rng = np.random.default_rng(2)
    base = rng.normal(5, 1, 3000)
    per_k = np.stack([base, base + 1.0, base + 1.0, base], axis=1)
    out = sm.choose_k(per_k, [1, 2, 4, 8], 2.0)
    assert out["chosen"] == 4 and out["best_by_mean"] == 2
    per_k = np.stack([base + 2.0, base, base, base], axis=1)
    assert sm.choose_k(per_k, [1, 2, 4, 8], 2.0)["chosen"] == 1


def test_the_criterion_weights_every_prior_point_and_tau_equally():
    g = np.array([[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]] * 1)              # P = 2 points x R = 1 row, 3 tau points
    res = {"g": g}
    assert sm.criterion_values(res, 2, np.full(3, 1 / 3))[0] == pytest.approx(3.0)
    g = np.array([[0.0, 0.0, 0.0], [6.0, 6.0, 6.0]])
    assert sm.criterion_values({"g": g}, 2, np.full(3, 1 / 3))[0] == pytest.approx(3.0)


def test_simulate_reports_the_monte_carlo_se_and_freezes_the_criterion_rule():
    S, M, _ = fx.tiny()
    res = sm.simulate(S, M, "category", "C-full")
    for b, choice in res["rule_choice"].items():
        assert choice["chosen"] in ("one_shot", "halving")
        assert all(v["mc_se"] == v["mc_se"] for v in choice["table"].values())
        recomputed = sm.choose_rule({r: np.zeros(1) + choice["table"][r]["mean"] for r in choice["table"]},
                                    ["one_shot", "halving"], 2.0)
        assert choice["best_by_mean"] == recomputed["best_by_mean"]
    assert res["n_a"] == 40 and res["n_b"] == 20 and set(res["frozen"]["rule"]) == {"2.0", "4.0", "8.0"}


def test_halving_finds_one_large_winner_with_probability_rising_to_one():
    S, M, _ = fx.tiny()
    M = copy.deepcopy(M)
    M["prior"]["category"] = {"shapes": ["one_winner"], "sizes_pp": [20.0], "rule": "test"}
    M["model"]["l"]["seed_sd_nats"] = 0.0                      # no L seed noise: the rule, not the L screen, is tested
    (menu, geom, ctx, d, points, G, tr), _, _ = setup(reps=range(300), sim=M)
    obs = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.0), tr["coherent"])
    found = [sm.outcome(spec.select(ctx, obs, rule="halving", budget=b), tr)["found"][:, 2].mean()
             for b in (2.0, 4.0, 8.0, 16.0)]
    assert all(later >= earlier - 0.05 for earlier, later in zip(found, found[1:]))
    assert found[0] < 0.3 and found[-1] > 0.95


def test_the_run_does_not_depend_on_the_number_of_workers_or_its_repetition():
    S, M, _ = fx.tiny()
    a = sm.run_pass(S, M, "planted_8", "C-lean", "A", 40)
    b = sm.run_pass(S, M, "planted_8", "C-lean", "A", 40, workers=2)            # 2 chunks in 2 processes
    for key in a[0]["crit"]:
        assert np.array_equal(np.concatenate([p["crit"][key] for p in a]), np.concatenate([p["crit"][key] for p in b]))
    sa, sb = sm.reduce_sums(a), sm.reduce_sums(b)
    assert all(np.array_equal(sa[k].data["g"], sb[k].data["g"]) for k in sa)


# ----- the switches behind the defaults ------------------------------------------------------------------


def test_the_2df_parameter_posterior_draws_per_replicate_from_its_label():
    S, M, _ = fx.tiny()
    M = copy.deepcopy(M)
    M["model"]["parameter_uncertainty"]["mode"] = "posterior_2df"
    (menu, geom, ctx, d, points, G, tr), _, _ = setup(reps=range(3000), sim=M)
    expected = s1.numpy_generator("selector.params", 7).chisquare(2, size=2)
    assert np.array_equal(d["params"][7], expected)
    obs = sm.observations(geom, ctx, M, d, G[:1], sm.NoiseCase(2.65, 0.0), tr["coherent"])
    scale = 0.002374850619448416 * np.sqrt(2.0 / d["params"][:, 1])
    assert np.allclose(obs.l[:, 0, 0], scale * d["noise"][:, 2, 0, ctx.a1, ctx.c1, 3])
    (_, _, _, d_fixed, *_), _, _ = setup(reps=range(3))
    assert d_fixed["params"] is None


def test_a_phi_trial_sees_the_effect_scaled_by_phi():
    S, M, _ = fx.tiny()
    S = copy.deepcopy(S)
    S["trials"].update({"phi_grid": [0.5, 1.0], "screen_phi": 0.5})
    M = copy.deepcopy(M)
    M["model"]["u_sampling_variance_full_pp2"] = 0.0
    M["model"]["l"]["seed_sd_nats"] = 0.0                      # no L seed noise: the L screen passes every option
    (menu, geom, ctx, d, points, G, tr), _, _ = setup(reps=range(4), sim=M, S=S)
    obs = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(0.0, 0.0), tr["coherent"])
    rows = G.reshape(-1, menu.M)
    assert np.allclose(obs.u[:, :, 0, 0, -1], 48.27777777777778 - 0.5 * rows)
    assert np.allclose(obs.u[:, :, 0, 1, -1], 48.27777777777778 - rows)
    sel = spec.select(ctx, obs, rule="one_shot", budget=8.0)
    assert sel.spent.max() <= 8.0 + 1e-9 and sm.outcome(sel, tr)["found"].all()


def test_the_rho_average_is_used_only_when_the_settings_say_so():
    S, M, _ = fx.tiny()
    M = copy.deepcopy(M)
    M["model"]["rho_mode"] = "a7_switch"
    M["replicates"] = {"rule_choice": 20, "diagnostic": 10, "sensitivity": 10, "chunk": M["replicates"]["chunk"]}
    parts = sm.run_pass(S, M, "category", "C-full", "A", 20)
    crit = sm.reduce_crit(parts)
    assert {key[0] for key in crit} == {0.0, 0.67}
    M["model"]["rho_average_for_rule"] = True
    res = sm.simulate(S, M, "category", "C-full", placement=False)
    for b in M["grids"]["budgets"]:
        per_rule = {r: np.mean([crit[(rho, float(b), r)] for rho in (0.0, 0.67)], axis=0) for r in res["rules"]}
        assert res["rule_choice"][str(float(b))]["chosen"] == sm.choose_rule(per_rule, res["rules"], 2.0)["chosen"]
