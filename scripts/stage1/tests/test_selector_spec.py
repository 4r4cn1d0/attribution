"""REQ-16 (the selector spec, one code path) and W1-13 (the feasibility screen's switches): synthetic cases only."""

from __future__ import annotations

import copy
import math
from statistics import NormalDist

import numpy as np
import pytest

from experiments.safety_selection.common import sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1.selector import simulate as sm
from scripts.stage1.selector import spec

import selector_fixtures as fx

C_FULL_SCREEN = (91.1 + 219.7 + 0.25 * 2623.2) / 2934.0
C_FULL_PROMOTE = 0.75 * 2623.2 / 2934.0 + 1.0


# ----- settings, objects and costs -----------------------------------------------------------------------


def test_the_spec_settings_load_with_their_literal_pin():
    assert sha256_file(spec.SETTINGS_PATH) == spec.SETTINGS_SHA256
    settings, digest = spec.load()
    assert digest == spec.SETTINGS_SHA256 and settings["name"] == "selector_spec"


def test_a_changed_settings_byte_refuses(tmp_path):
    data = bytearray(spec.SETTINGS_PATH.read_bytes())
    data[-3] = ord(" ") if data[-3] != ord(" ") else ord("\t")
    path = tmp_path / "selector_spec.json"
    path.write_bytes(bytes(data))
    with pytest.raises(s1.Refusal, match="hash to"):
        spec.load(path)


def test_the_menus_are_the_brief_objects():
    S = fx.raw("selector_spec")
    category = spec.menu_from(S, "category")
    assert category.M == 8 and not category.nested and category.keep.kind == "keep" and category.keep_seeds == 3
    assert all(o.kind == "removal" and o.dose == 600 and o.cost_fre == 1.0 for o in category.options)
    method = spec.menu_from(S, "method")
    assert {o.kind for o in method.options} == {"removal", "add"} and method.keep_seeds == 6
    sizes = {m: spec.menu_from(S, m) for m in ("planted_8", "planted_32", "planted_128")}
    assert [sizes[m].M for m in sizes] == [8, 32, 128] and all(x.nested for x in sizes.values())
    assert sum(o.dose for o in sizes["planted_128"].options) == 4800
    assert [o.dose for o in sizes["planted_128"].options[:4]] == [37, 38, 37, 38]
    assert sizes["planted_8"].axis_size() == 14 and category.axis_size() == 8


def test_cost_model_hand_values():
    S = fx.raw("selector_spec")
    full = spec.cost_model(S, "C-full")
    assert full.unit == pytest.approx(2934.0) and full.full == pytest.approx(1.0)
    assert full.trial(1.0, 0.25) == pytest.approx(C_FULL_SCREEN)
    assert full.topup(0.25, 1.0) == pytest.approx(0.75 * 2623.2 / 2934.0) and full.topup(1.0, 1.0) == 0.0
    lean = spec.cost_model(S, "C-lean")
    assert lean.unit == pytest.approx(870.0) and lean.samples_per_prompt == 1
    assert lean.training / lean.unit == pytest.approx(0.2529, abs=1e-4)
    S["cost_conventions"]["C-lean"]["contents"] = "b"
    b = spec.cost_model(S, "C-lean")
    assert b.unit == pytest.approx(480.0) and b.full == pytest.approx(1.0 + 390.0 / 480.0)
    assert b.topup(0.25, 1.0) == pytest.approx((0.75 * 245.0 + 390.0) / 480.0)


def test_the_tie_order_is_the_sealed_order_of_the_registry_key():
    menu = fx.custom_menu(6)
    order = s1.sealed_order(menu.ids, "selector.ties")
    rank = spec.tie_rank(menu)
    assert [menu.ids[i] for i in np.argsort(rank)] == order


# ----- the rules and their budgets -----------------------------------------------------------------------


def test_one_shot_schedule_hand_values():
    ctx = fx.context(fx.custom_menu(8))
    g = np.array([[0, 0, 0, 0, 0, 0, 9.0, 0]])
    sel = spec.select(ctx, fx.exact_obs(ctx, 50.0 - g), rule="one_shot", budget=4.0)
    n_s = math.floor((4.0 - C_FULL_PROMOTE) / C_FULL_SCREEN)
    assert n_s == 7
    assert sel.spent[0] == pytest.approx(n_s * C_FULL_SCREEN + C_FULL_PROMOTE)
    assert sel.full_seeds.sum() == 2


def test_one_shot_caps_its_finalists_and_spends_the_rest_on_their_seeds():
    ctx = fx.context(fx.custom_menu(8))
    assert ctx.one_shot_finalists == 2
    g = np.arange(8.0)[None, :]
    sel = spec.select(ctx, fx.exact_obs(ctx, 50.0 - g), rule="one_shot", budget=16.0)
    seeds = sel.full_seeds[0]
    assert (seeds >= 2).sum() == 2 and seeds.sum() > 4                      # 2 finalists, the rest as seeds
    leftover = 16.0 - 8 * C_FULL_SCREEN - 2 * C_FULL_PROMOTE
    assert seeds.sum() == 4 + math.floor(leftover + 1e-9)
    assert sel.spent[0] <= 16.0 + 1e-9 and (sel.pick == 7).all()


def test_halving_schedule_hand_values():
    ctx = fx.context(fx.custom_menu(8))
    sizes, total = spec.halving_schedule(ctx, 4)
    top_half = 0.25 * 2623.2 / 2934.0
    assert sizes == [4, 2, 1, 1]
    assert total == pytest.approx(4 * C_FULL_SCREEN + 2 * top_half + 2 * top_half + 1.0)
    assert spec.halving_schedule(ctx, 5)[1] > 4.0
    sel = spec.select(ctx, fx.exact_obs(ctx, np.full((1, 8), 50.0)), rule="halving", budget=4.0)
    assert sel.spent[0] == pytest.approx(total)
    assert spec.halving_schedule(ctx, 16)[0] == [16, 8, 4, 2, 1]


def test_bisection_plan_hand_values():
    ctx = fx.context(fx.custom_menu(8, nested=True))
    t, total = spec.bisection_plan(ctx, 4.0)
    assert t == 1 and total == pytest.approx(6 * C_FULL_SCREEN + C_FULL_PROMOTE)
    assert spec.bisection_plan(ctx, 1.0) == (0, 0.0)


def _random_settings(rng: np.random.Generator) -> dict:
    S = fx.raw("selector_spec")
    conv = S["cost_conventions"]["C-full"]
    conv.update({"setup_s": float(rng.uniform(1, 300)), "training_s": float(rng.uniform(10, 2000)),
                 "evaluation_s": float(rng.uniform(10, 3000)), "extra_full_s": float(rng.choice([0.0, 300.0]))})
    psi = sorted(set(np.round(rng.uniform(0.05, 0.95, rng.integers(0, 3)), 2).tolist())) + [1.0]
    phi = sorted(set(np.round(rng.uniform(0.2, 0.9, rng.integers(0, 2)), 2).tolist())) + [1.0]
    S["trials"].update({"psi_grid": psi, "phi_grid": phi, "screen_psi": float(rng.choice(psi)),
                        "screen_phi": float(rng.choice(phi)), "max_seeds": int(rng.integers(2, 9))})
    return S


def test_no_policy_ever_spends_more_than_b():
    """Property test over random menus, costs, trial grids, budgets, k and c_d (REQ-16)."""
    rng = np.random.default_rng(20261017)
    for trial in range(120):
        S = _random_settings(rng)
        nested = bool(rng.integers(0, 2))
        M = int(2 ** rng.integers(1, 6)) if nested else int(rng.integers(1, 25))
        menu = fx.custom_menu(M, nested=nested, prefix=f"p{trial}")
        ctx = spec.context(S, menu.id, "C-full", menu=menu)
        n = 6
        obs = fx.noisy_obs(ctx, rng.uniform(0, 10, (n, menu.axis_size())), rng)
        budget = float(rng.uniform(0, 24))
        rules = ["one_shot", "halving"] + (["bisection"] if nested else [])
        for rule in rules:
            sel = spec.select(ctx, obs, rule=rule, budget=budget)
            assert (sel.spent <= budget + 1e-9).all(), (trial, rule, budget, sel.spent.max())
            k = int(rng.integers(1, M + 1))
            c_d = float(rng.uniform(0, budget + 1))
            diag = spec.select(ctx, obs, rule=rule, budget=budget, scores=rng.standard_normal((n, M)), k=k, c_d=c_d)
            assert (diag.spent <= budget + 1e-9).all(), (trial, rule, budget, k, c_d, diag.spent.max())


def test_the_ledger_counts_every_trial():
    ctx = fx.context(fx.custom_menu(4))
    state = spec.State.empty(1, 4, ctx.max_seeds)
    state.level[0, 0, 0] = ctx.screen_psi
    state.level[0, 1, 0:2] = ctx.c1
    assert spec.ledger_cost(ctx, state)[0] == pytest.approx(C_FULL_SCREEN + 2.0)


def test_c_d_is_charged_and_a_short_remainder_picks_keep():
    ctx = fx.context(fx.custom_menu(8))
    g = np.array([[0, 0, 9.0, 0, 0, 0, 0, 0]])
    obs = fx.exact_obs(ctx, 50.0 - g)
    scores = g.copy()
    full = spec.select(ctx, obs, rule="halving", budget=8.0, scores=scores, k=8, c_d=0.0)
    paid = spec.select(ctx, obs, rule="halving", budget=8.0, scores=scores, k=8, c_d=1.5)
    runs = spec.select(ctx, obs, rule="halving", budget=6.5)
    assert paid.spent[0] == pytest.approx(1.5 + runs.spent[0]) and paid.spent[0] <= 8.0
    assert paid.spent[0] != pytest.approx(full.spent[0])
    short = spec.select(ctx, obs, rule="halving", budget=4.0, scores=scores, k=8, c_d=2.5)
    assert (short.pick == spec.KEEP).all() and short.spent[0] == pytest.approx(2.5)
    unaffordable = spec.select(ctx, obs, rule="halving", budget=2.0, scores=scores, k=8, c_d=3.0)
    assert (unaffordable.pick == spec.KEEP).all() and unaffordable.spent[0] == 0.0


def test_a_diagnostic_bisection_runs_as_halving_on_the_top_k():
    ctx = fx.context(fx.custom_menu(8, nested=True))
    g = np.zeros((1, 8))
    g[0, 5] = 9.0
    obs = fx.exact_obs(ctx, 50.0 - sm.tree_sums(g, 8))
    scores = -np.arange(8.0)[None, :]
    scores[0, 5] = 100.0
    sel = spec.select(ctx, obs, rule="bisection", budget=8.0, scores=scores, k=2)
    assert sel.rule == "halving"
    assert set(np.nonzero(sel.full_seeds[0])[0]) <= {0, 5}
    assert (sel.pick == 5).all()


# ----- the pick ------------------------------------------------------------------------------------------


def _state_with(ctx: spec.Context, seeds: list[int]) -> spec.State:
    state = spec.State.empty(1, ctx.menu.M, ctx.max_seeds)
    for i, n in enumerate(seeds):
        state.level[0, i, :n] = ctx.c1
    return state


def _view(ctx: spec.Context, obs: spec.Observations) -> object:
    return spec._full_view(obs, ctx)


def test_the_pick_needs_two_full_run_seeds():
    ctx = fx.context(fx.custom_menu(3))
    obs = fx.exact_obs(ctx, np.array([[40.0, 45.0, 50.0]]))
    keep = np.ones(1, bool)
    assert (spec.pick(ctx, _view(ctx, obs), _state_with(ctx, [1, 2, 0]), keep) == 1).all()
    assert (spec.pick(ctx, _view(ctx, obs), _state_with(ctx, [1, 1, 0]), keep) == spec.KEEP).all()
    assert (spec.pick(ctx, _view(ctx, obs), _state_with(ctx, [2, 2, 0]), keep) == 0).all()


def test_a_tie_with_keep_goes_to_keep():
    ctx = fx.context(fx.custom_menu(2))
    obs = fx.exact_obs(ctx, np.array([[50.0, 51.0]]))         # option 0 exactly at keep's U: G = 0
    keep = np.ones(1, bool)
    assert (spec.pick(ctx, _view(ctx, obs), _state_with(ctx, [2, 2]), keep) == spec.KEEP).all()
    obs = fx.exact_obs(ctx, np.array([[49.999, 51.0]]))
    assert (spec.pick(ctx, _view(ctx, obs), _state_with(ctx, [2, 2]), keep) == 0).all()


def test_ties_between_options_go_to_the_sealed_tie_order():
    menu = fx.custom_menu(4)
    ctx = fx.context(menu)
    obs = fx.exact_obs(ctx, np.full((1, 4), 45.0))
    first = int(np.argmin(ctx.tie_rank))
    assert (spec.pick(ctx, _view(ctx, obs), _state_with(ctx, [2, 2, 2, 2]), np.ones(1, bool)) == first).all()


def test_keep_is_never_dropped_by_top_k():
    ctx = fx.context(fx.custom_menu(4))
    obs = fx.exact_obs(ctx, np.full((1, 4), 53.0))           # every option is worse than keep
    scores = np.array([[5.0, 4.0, 3.0, 2.0]])                 # every option scores above keep's G of 0
    avail, keep_kept = spec.diagnostic_filter(scores, 2, ctx.tie_rank)
    assert keep_kept.all() and avail.sum() == 2
    sel = spec.select(ctx, obs, rule="halving", budget=8.0, scores=scores, k=2)
    assert (sel.pick == spec.KEEP).all()


def test_top_k_keeps_the_highest_scores_with_sealed_ties():
    ctx = fx.context(fx.custom_menu(5))
    avail, _ = spec.diagnostic_filter(np.array([[1.0, 3.0, 2.0, 3.0, 0.0]]), 2, ctx.tie_rank)
    assert np.nonzero(avail[0])[0].tolist() == [1, 3]
    avail, _ = spec.diagnostic_filter(np.array([[1.0, 1.0, 1.0, 1.0, 1.0]]), 1, ctx.tie_rank)
    assert np.nonzero(avail[0])[0].tolist() == [int(np.argmin(ctx.tie_rank))]


def test_shrinkage_moves_estimates_toward_the_menu_mean():
    g = np.array([[10.0, 2.0, 0.0, -2.0]])
    v = np.full((1, 4), 4.0)
    members = np.ones((1, 4), bool)
    out = spec.shrink(g, v, members)
    mu = g.mean()
    tau2 = max(0.0, g.var(ddof=1) - 4.0)
    assert out == pytest.approx(mu + tau2 / (tau2 + 4.0) * (g - mu))
    assert (np.abs(out - mu) < np.abs(g - mu)).all()
    assert spec.shrink(g, np.zeros((1, 4)), members) == pytest.approx(g)        # no noise: no shrinkage
    assert spec.shrink(g, v, np.array([[True, False, False, False]])) == pytest.approx(g)


def test_shrinkage_changes_the_pick_against_keep():
    """Raw estimates favour an option, but the shrunk best falls below keep: the pick is keep."""
    ctx = fx.context(fx.custom_menu(4))
    u = np.array([[49.5, 50.5, 50.5, 50.5]])                    # raw G: +0.5, -0.5, -0.5, -0.5; tau^2 = 0
    rng_free = fx.exact_obs(ctx, u)
    rng_free.keep_u = np.array([[48.0, 50.0, 52.0]])             # keep's mean 50, residual variance 4
    state = _state_with(ctx, [2, 2, 2, 2])
    view = _view(ctx, rng_free)
    est = spec.estimates(ctx, view, state)
    assert est["g_raw"][0, 0] == pytest.approx(0.5) and est["g_shrunk"][0, 0] == pytest.approx(-0.25)
    assert (spec.pick(ctx, view, state, np.ones(1, bool)) == spec.KEEP).all()


# ----- the feasibility screen (W1-13) --------------------------------------------------------------------


def _screened(ctx: spec.Context, o: float, l: float, keep_l: list[float] | None = None) -> np.ndarray:
    obs = fx.exact_obs(ctx, np.array([[45.0]]), o=o, l=l)
    obs.keep_o = np.array([[4.0, 6.0, 4.0]])
    obs.o = np.array([[[o - 1.0, o + 1.0] + [0.0] * (ctx.max_seeds - 2)]])
    obs.l = np.array([[[l - 0.001, l + 0.001] + [0.0] * (ctx.max_seeds - 2)]])
    if keep_l is not None:
        obs.keep_l = np.array([keep_l])
    state = _state_with(ctx, [2])
    est = spec.estimates(ctx, _view(ctx, obs), state)
    return spec.feasibility(ctx, _view(ctx, obs), est["full"], est["n_full"])[0, 0]


def _o_upper(ctx: spec.Context, o: float) -> float:
    z = NormalDist().inv_cdf(ctx.upper_quantile)
    pooled = ((-1.0) ** 2 * 2 + ((4 - 14 / 3) ** 2 + (6 - 14 / 3) ** 2 + (4 - 14 / 3) ** 2)) / (1 + 2)
    prompt = ctx.o_prompt_sd ** 2 if ctx.o_error_model == "prompts_random" else 0.0
    return o - ctx.o_theta0 + z * math.sqrt(pooled / 2 + prompt)


def test_the_o_screen_both_ways_with_hand_values():
    ctx = fx.context(fx.custom_menu(1))
    for tau_index, tau in enumerate(ctx.tau_o):
        o_edge = ctx.o_theta0 + tau - (_o_upper(ctx, 0.0) + ctx.o_theta0) + 0.0
        assert _screened(ctx, o_edge - 0.01, 0.0)[tau_index]
        assert not _screened(ctx, o_edge + 0.01, 0.0)[tau_index]


def test_an_o_infeasible_candidate_is_never_picked():
    ctx = fx.context(fx.custom_menu(2))
    obs = fx.exact_obs(ctx, np.array([[40.0, 45.0]]))
    obs.o[:, 0, :] = 40.0                                     # far above theta0 + every tau_O
    pick = spec.pick(ctx, _view(ctx, obs), _state_with(ctx, [2, 2]), np.ones(1, bool))
    assert (pick == 1).all()


def test_the_quantile_switch_flips_a_boundary_case():
    ctx95 = fx.context(fx.custom_menu(1))
    ctx90 = fx.context(fx.custom_menu(1), upper_quantile=0.90)
    o = (ctx95.o_theta0 + 5.0) - (_o_upper(ctx95, 0.0) + ctx95.o_theta0) + 0.2
    assert not _screened(ctx95, o, 0.0)[1] and _screened(ctx90, o, 0.0)[1]


def test_the_prompt_part_switch():
    ctx_pr = fx.context(fx.custom_menu(1))
    ctx_so = fx.context(fx.custom_menu(1), o_error_model="seed_only")
    o = ctx_pr.o_theta0 + 2.0 - 3.0                            # 1 pp below the tau_O = 2 limit on the estimate
    assert not _screened(ctx_pr, o, 0.0)[0] and _screened(ctx_so, o, 0.0)[0]


def test_the_hb_form_equals_the_hand_two_arm_variance():
    ctx = fx.context(fx.custom_menu(1), se_form="hb", o_error_model="seed_only")
    obs = fx.exact_obs(ctx, np.array([[45.0]]))
    obs.o = np.array([[[3.0, 7.0] + [0.0] * (ctx.max_seeds - 2)]])
    obs.l = np.array([[[0.002, 0.006] + [0.0] * (ctx.max_seeds - 2)]])
    obs.keep_l = np.array([[0.0, 0.001, 0.002]])
    state = _state_with(ctx, [2])
    view = _view(ctx, obs)
    est = spec.estimates(ctx, view, state)
    z = NormalDist().inv_cdf(0.95)
    l_upper = (0.004 - 0.001) + z * math.sqrt(np.var([0.002, 0.006], ddof=1) / 2 + np.var([0, 0.001, 0.002], ddof=1) / 3)
    edge = ctx.tau_l - l_upper
    ok = spec.feasibility(ctx, view, est["full"], est["n_full"])[0, 0]
    assert ok.all() == (edge >= 0)
    ctx_tight = fx.context(fx.custom_menu(1), se_form="hb", o_error_model="seed_only")
    obs.l = obs.l + (ctx_tight.tau_l - l_upper) + 1e-6
    est = spec.estimates(ctx_tight, view, state)
    assert not spec.feasibility(ctx_tight, _view(ctx_tight, obs), est["full"], est["n_full"])[0, 0].any()


def test_the_tau_l_reference_switch():
    ctx_a0 = fx.context(fx.custom_menu(1))
    ctx_r = fx.context(fx.custom_menu(1), tau_l_reference="r")
    obs = fx.exact_obs(ctx_a0, np.array([[45.0]]))
    obs.l = np.array([[[0.010, 0.010] + [0.0] * (ctx_a0.max_seeds - 2)]])
    obs.keep_l = np.array([[0.0, 0.0001, -0.0001]])
    obs.ref_l = np.array([[0.0099, 0.0100, 0.0101]])            # a dose-matched R arm with the same loss
    state = _state_with(ctx_a0, [2])
    for ctx, expected in ((ctx_a0, False), (ctx_r, True)):
        view = _view(ctx, obs)
        est = spec.estimates(ctx, view, state)
        assert spec.feasibility(ctx, view, est["full"], est["n_full"])[0, 0].all() == expected


def test_a_coherence_failure_is_never_picked():
    ctx = fx.context(fx.custom_menu(2))
    coherent = np.array([[False, True]])
    obs = fx.exact_obs(ctx, np.array([[40.0, 45.0]]), coherent=coherent)
    assert (spec.pick(ctx, _view(ctx, obs), _state_with(ctx, [2, 2]), np.ones(1, bool)) == 1).all()
    off = fx.context(fx.custom_menu(2), coherence_gate=False)
    assert (spec.pick(off, _view(off, obs), _state_with(off, [2, 2]), np.ones(1, bool)) == 0).all()


# ----- zero noise, replay and the one code path ----------------------------------------------------------


@pytest.mark.parametrize("rule,nested", [("one_shot", False), ("halving", False), ("bisection", True)])
def test_with_zero_noise_the_pick_is_the_true_best(rule, nested):
    M = 8
    ctx = fx.context(fx.custom_menu(M, nested=nested))
    for best in range(M):
        g = np.full((1, M), 1.0)
        g[0, best] = 6.0
        axis = sm.tree_sums(g, M) if nested else g
        sel = spec.select(ctx, fx.exact_obs(ctx, 50.0 - axis), rule=rule, budget=16.0)
        assert (sel.pick == best).all(), (rule, best)


def _labels(ctx: spec.Context, u_by_option: dict, seeds: dict, prompts: int = 12) -> dict:
    def seed_entry(j, u):
        return {"seed_index": j, "u_prompts": {f"p{i:03d}": u / 100.0 for i in range(prompts)},
                "o_prompts": {f"o{i:03d}": 0 for i in range(10)}, "l_rows": {f"t{i:03d}": 0.0 for i in range(5)}}
    return {"kind": spec.LABELS_KIND, "version": spec.LABELS_VERSION, "menu": ctx.menu.id,
            "samples_per_prompt": ctx.cost.samples_per_prompt,
            "keep": {"samples_per_prompt": ctx.keep_samples_per_prompt,
                     "seeds": [seed_entry(j, 50.0) for j in range(ctx.menu.keep_seeds)]},
            "options": {oid: {"coherent": True, "seeds": [seed_entry(j, u_by_option[oid]) for j in range(seeds[oid])]}
                        for oid in u_by_option}}


def test_replay_and_simulation_call_the_same_function(monkeypatch):
    calls = []
    original = spec.select

    def spy(*args, **kwargs):
        calls.append(kwargs.get("rule"))
        return original(*args, **kwargs)

    monkeypatch.setattr(spec, "select", spy)
    S, M, _ = fx.tiny()
    task = {"spec": S, "sim": M, "menu": "category", "convention": "C-full", "pass": "A", "start": 0, "stop": 3,
            "frozen": None, "placement": False}
    sm.run_chunk(task)
    simulated = len(calls)
    assert simulated > 0
    ctx = spec.context(S, "category", "C-full")
    labels = _labels(ctx, {oid: 50.0 for oid in ctx.menu.ids}, {oid: 2 for oid in ctx.menu.ids})
    spec.replay(S, "category", "C-full", "one_shot", 2.0, labels)
    assert len(calls) == simulated + 1


def test_a_replay_equals_the_simulation_row_by_row():
    S, M, _ = fx.tiny()
    menu, geom, ctx, d, points, G, tr = sm._setup(S, M, "category", "C-full", range(6))
    obs = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.0), tr["coherent"])
    batch = spec.select(ctx, obs, rule="halving", budget=8.0)
    for row in range(obs.n):
        one = spec.Observations(**{k: (None if v is None else v[row:row + 1]) for k, v in vars(obs).items()})
        assert (spec.select(ctx, one, rule="halving", budget=8.0).pick == batch.pick[row]).all()


def test_replay_refuses_a_trial_the_saved_design_lacks():
    S = fx.raw("selector_spec")
    ctx = spec.context(S, "category", "C-full")
    labels = _labels(ctx, {oid: 50.0 for oid in ctx.menu.ids[:2]}, {oid: 1 for oid in ctx.menu.ids[:2]})
    with pytest.raises(s1.Refusal, match="not replayable"):
        spec.replay(S, "category", "C-full", "one_shot", 8.0, labels)


def test_a_replay_psi_trial_reads_the_sealed_prompt_sample():
    S = fx.raw("selector_spec")
    ctx = spec.context(S, "category", "C-full")
    oid = ctx.menu.ids[0]
    labels = _labels(ctx, {oid: 50.0}, {oid: 1}, prompts=20)
    values = {f"p{i:03d}": (i % 5) / 4.0 for i in range(20)}
    labels["options"][oid]["seeds"][0]["u_prompts"] = values
    obs = spec.observations_from_labels(ctx, labels)
    chosen = s1.sealed_sample(sorted(values), 5, "selector.psi", oid, 0, "0.25")
    assert obs.u[0, 0, 0, ctx.a1, 0] == pytest.approx(100.0 * np.mean([values[p] for p in chosen]))
    assert obs.u[0, 0, 0, ctx.a1, ctx.c1] == pytest.approx(100.0 * np.mean(list(values.values())))
    assert np.isnan(obs.u[0, 1]).all() and obs.keep_u.shape == (1, 3)


def test_the_replay_output_holds_ids_and_numbers_only():
    S = fx.raw("selector_spec")
    ctx = spec.context(S, "category", "C-full")
    u = {oid: 50.0 - 2.0 * i for i, oid in enumerate(ctx.menu.ids)}
    labels = _labels(ctx, u, {oid: 4 for oid in ctx.menu.ids})
    out = spec.replay(S, "category", "C-full", "halving", 8.0, labels)
    assert out["spent"] <= 8.0 + 1e-9
    assert set(out["pick_by_tau_o"]) == {"2", "5", "10"}
    assert all(v in ctx.menu.ids + [ctx.menu.keep.id] for v in out["pick_by_tau_o"].values())
