"""Part E fix round (notes/partE-verify.md): the tests that kill the verifier's surviving mutants V01-V16 (most
from notes/partE-verify-proposed-tests.py, reviewed; the Delta test made stronger), and the tests of the fixes
for B-1 (one rule and one k per (menu, M, B)), S-7 (both L references), S-8 (the replay's sample counts), S-10
(k under the A7 rho average), S-11 (inputs found by hint and prefix), N-1 (c* none and non-monotone) and N-3
(option cost). Synthetic only; draws only through s1common or test-only numpy generators."""

from __future__ import annotations

import copy
import json
import math
from statistics import NormalDist

import numpy as np
import pytest

from experiments.safety_selection.common import sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1.selector import predict as pr
from scripts.stage1.selector import simulate as sm
from scripts.stage1.selector import spec

import selector_fixtures as fx

DIGESTS = {"selector_spec": "a" * 64, "selector_simulate": "b" * 64, "selector_predict": "c" * 64}
CONVENTIONS = ["C-full", "C-lean"]


@pytest.fixture(scope="module")
def built_doc() -> dict:
    S, M, P = fx.tiny()
    return json.loads(pr.build(S, M, P, DIGESTS))


# ----- the ledger against a trial-by-trial count (S-4: V01, V02) ----------------------------------------


def _oracle_cost(ctx: spec.Context, state: spec.State) -> np.ndarray:
    """A final state's cost counted trial by trial in seconds (not through spec.ledger_cost)."""
    c, out = ctx.cost, np.zeros(state.level.shape[0])
    for b, a, j in zip(*np.nonzero((state.level >= 0) | state.low)):
        if state.low[b, a, j]:
            out[b] += c.setup + ctx.phi_grid[ctx.screen_phi] * c.training + ctx.psi_grid[ctx.screen_psi] * c.evaluation
        level = state.level[b, a, j]
        if level >= 0:
            out[b] += c.setup + c.training + ctx.psi_grid[level] * c.evaluation + (c.extra_full if level == ctx.c1 else 0.0)
    return out / c.unit


@pytest.mark.parametrize("case", ["phi_half", "c_lean_b"])
def test_the_ledger_equals_a_trial_by_trial_count(case):                          # kills V01, V02
    S = fx.raw("selector_spec")
    convention = "C-full"
    if case == "phi_half":
        S["trials"].update({"phi_grid": [0.5, 1.0], "screen_phi": 0.5})
    else:
        S["cost_conventions"]["C-lean"]["contents"] = "b"
        convention = "C-lean"
    # under C-lean (b) with the 500-prompt bank a full run is (480 + 1,906.2) / 480 = 4.97 c0, so larger budgets
    budgets, runs_from = ((4.0, 8.0, 13.0), 8.0) if case == "phi_half" else ((12.0, 24.0, 40.0), 24.0)
    for nested, rules in ((False, ("one_shot", "halving")), (True, ("bisection",))):
        menu = fx.custom_menu(8, nested=nested)
        ctx = spec.context(S, menu.id, convention, menu=menu)
        obs = fx.noisy_obs(ctx, np.linspace(0, 6, menu.axis_size())[None, :].repeat(3, 0), np.random.default_rng(5))
        for rule in rules:
            for budget in budgets:
                sel = spec.select(ctx, obs, rule=rule, budget=budget)
                assert (sel.spent <= budget + 1e-9).all()
                assert sel.spent == pytest.approx(_oracle_cost(ctx, sel.state), abs=1e-12), (case, rule, budget)
                if budget >= runs_from:
                    assert (sel.spent > 0).all() and ((sel.state.low.any() if case == "phi_half" else True))


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


def test_every_policy_spends_the_trial_by_trial_count_over_random_menus():
    """REQ-16's budget property with an independent oracle: the spend is the trial-by-trial count, never above B."""
    rng = np.random.default_rng(20261018)
    for trial in range(60):
        S = _random_settings(rng)
        nested = bool(rng.integers(0, 2))
        M = int(2 ** rng.integers(1, 6)) if nested else int(rng.integers(1, 25))
        menu = fx.custom_menu(M, nested=nested, prefix=f"q{trial}")
        ctx = spec.context(S, menu.id, "C-full", menu=menu)
        obs = fx.noisy_obs(ctx, rng.uniform(0, 10, (4, menu.axis_size())), rng)
        budget = float(rng.uniform(0, 24))
        for rule in ["one_shot", "halving"] + (["bisection"] if nested else []):
            k, c_d = int(rng.integers(1, M + 1)), float(rng.uniform(0, budget + 1))
            for kwargs in ({}, {"scores": rng.standard_normal((4, M)), "k": k, "c_d": c_d}):
                sel = spec.select(ctx, obs, rule=rule, budget=budget, **kwargs)
                paid = kwargs.get("c_d", 0.0) if (sel.state is not None or sel.spent.any()) else 0.0
                oracle = paid + (_oracle_cost(ctx, sel.state) if sel.state is not None else 0.0)
                assert sel.spent == pytest.approx(oracle, abs=1e-9), (trial, rule, budget, kwargs.keys())
                assert (sel.spent <= budget + 1e-9).all()


# ----- the pick, the rules and the noise model (S-5: V05, V09, V12, V14, V15, V16) ----------------------


def test_shrinkage_can_reorder_options_and_the_pick_follows_it():                 # kills V05
    ctx = fx.context(fx.custom_menu(4))
    obs = fx.exact_obs(ctx, np.array([[47.0, 47.4, 50.0, 50.0]]))
    obs.keep_u = np.array([[47.0, 50.0, 53.0]])
    obs.u[0] += np.array([1.0, -1.0] * (ctx.max_seeds // 2))[None, :, None, None]
    state = spec.State.empty(1, 4, ctx.max_seeds)
    for i, n in enumerate([2, 8, 2, 2]):
        state.level[0, i, :n] = ctx.c1
    view = spec._full_view(obs, ctx)
    est = spec.estimates(ctx, view, state)
    assert est["g_raw"][0, 0] > est["g_raw"][0, 1] and est["g_shrunk"][0, 1] > est["g_shrunk"][0, 0]
    assert (spec.pick(ctx, view, state, np.ones(1, bool)) == 1).all()


def test_a_psi_trial_has_the_subsample_variance():                              # kills V09
    S, M, _ = fx.tiny()
    menu, geom, ctx, d, points, G, tr = sm._setup(S, M, "category", "C-full", range(4000))
    obs = sm.observations(geom, ctx, M, d, G[:1], sm.NoiseCase(2.65, 0.0), tr["coherent"])
    noise = obs.u[:, 0, 0, ctx.a1, 0] - (48.27777777777778 - G[0, :, 0])           # psi = 0.25, seed 0
    assert np.var(noise) == pytest.approx(2.65 ** 2 - 2.314 + 2.314 / 0.25, rel=0.08)


def test_the_rules_visit_the_options_in_the_sealed_tie_order():                 # kills V12
    S = fx.raw("selector_spec")
    ctx = spec.context(S, "category", "C-full")
    for position, expect_found in ((int(np.argmax(ctx.tie_rank)), False), (int(np.argmin(ctx.tie_rank)), True)):
        g = np.zeros((1, 8))
        g[0, position] = 9.0
        pick = spec.select(ctx, fx.exact_obs(ctx, 50.0 - g), rule="one_shot", budget=4.0).pick[0, 0]
        assert (pick == position) == expect_found       # 7 of 8 screened at B = 4 at the dev-100 costs; 3 of 8 at
        # the 500-bank costs (rev 2), where this probe no longer tells the orders apart: test_selector_rev2 sets the order


def test_halving_leftover_goes_only_to_options_with_two_seeds():                # kills V14
    ctx = fx.context(fx.custom_menu(8), settings=fx.dev100())                  # the dev-100 hand costs
    g = np.arange(8.0)[None, :]
    sel = spec.select(ctx, fx.exact_obs(ctx, 50.0 - g), rule="halving", budget=8.0)
    sizes, total = spec.halving_schedule(ctx, 8)
    assert sizes == [8, 4, 2, 1]
    extra = math.floor(8.0 - total + 1e-9)
    assert extra >= 2                                                           # a round robin would split it
    assert sorted(sel.full_seeds[0].tolist()) == [0] * 6 + [1, 2 + extra]


def test_shrinkage_pools_every_option_with_one_full_run_seed():                 # kills V16
    ctx = fx.context(fx.custom_menu(4))
    obs = fx.exact_obs(ctx, np.array([[46.0, 48.0, 50.0, 52.0]]))
    obs.keep_u = np.array([[47.0, 50.0, 53.0]])
    obs.u[0] += np.array([1.5, -1.5] * (ctx.max_seeds // 2))[None, :, None, None]
    state = spec.State.empty(1, 4, ctx.max_seeds)
    for i, n in enumerate([1, 2, 1, 2]):
        state.level[0, i, :n] = ctx.c1
    est = spec.estimates(ctx, spec._full_view(obs, ctx), state)
    assert not np.isclose(est["g_shrunk"][0, 0], est["g_raw"][0, 0])                # a 1-seed option is shrunk too


def test_the_category_placement_carries_the_wave_1_seed_noise():                # kills V15
    S, M, _ = fx.tiny()
    menu, geom, ctx, d, points, G, tr = sm._setup(S, M, "category", "C-full", range(400))
    p = [i for i, pt in enumerate(points) if pt[0] == "spread"][0]
    score = sm.scores(geom, M, d, G[p:p + 1], {"kind": "rs", "r": 0.0})
    rho = sm.placement_values(geom, ctx, M, d, G[p:p + 1], score, [1], {"kind": "rs", "r": 0.0})["spearman_rho"]
    assert rho.mean() < 0.95 and np.quantile(rho, 0.05) < 0.6


# ----- the prediction assembly (S-1: V06, V07, V13; S-2: V08) -------------------------------------------


def test_delta_is_the_diagnostic_minus_the_frozen_rule_on_the_same_replicates():   # kills V06
    """With as many rule-choice as diagnostic replicates, E_G(diagnostic) - Delta is the frozen runs-only rule's
    E_G at every (c_d, quality) point: Delta has the sign and the pairing of the definition."""
    S, M, _ = fx.tiny()
    M["replicates"].update({"rule_choice": 20, "diagnostic": 20, "sensitivity": 20})
    res = sm.simulate(S, M, "category", "C-full", placement=False)
    tau_o = spec.context(S, "category", "C-full").tau_o
    checked = 0
    for b in M["grids"]["budgets"]:
        block = pr.cell_block(res, M, tau_o, float(b))
        frozen = block["runs_only"]["frozen_rule"]
        for tau, by_tau in block["diagnostic"]["by_tau_o"].items():
            runs = block["runs_only"]["by_rule"][frozen][tau]["E_G"]["mean"]
            for q, curve in by_tau["by_quality"].items():
                for e_g, delta in zip(curve["E_G"], curve["Delta"]):
                    assert e_g - delta == pytest.approx(runs, abs=1e-8), (b, tau, q)
                    checked += abs(delta) > 1e-6
    assert checked > 0                                                          # some Delta is not 0


def test_the_delta_curves_are_read_at_the_frozen_k():                           # kills V07
    S, M, _ = fx.tiny()
    res = sm.simulate(S, M, "category", "C-full", placement=False)
    tau_o = spec.context(S, "category", "C-full").tau_o
    for b in M["grids"]["budgets"]:
        block = pr.cell_block(res, M, tau_o, float(b))
        for t, tau in enumerate(tau_o):
            for q, curve in block["diagnostic"]["by_tau_o"][f"{tau:g}"]["by_quality"].items():
                for i, c in enumerate(M["grids"]["c_d_grid"]):
                    k = res["frozen"]["k"][f"{float(b):g}|{float(c):g}"]
                    s = res["sums_b"][(float(b), float(c), q, k)]
                    assert curve["k"][i] == k
                    assert curve["Delta"][i] == pytest.approx((s.data["d"][:, t] / s.n).mean(), abs=1e-8)


def test_k_is_chosen_on_the_equal_weight_quality_average():                     # kills V08
    S, M, _ = fx.tiny()
    M["model"]["rho_average_for_rule"] = False          # at rho = 0 only: the sums below are kept at rho = 0
    frozen = {"rule": {str(b): "one_shot" for b in M["grids"]["budgets"]}}
    out = sm.run_chunk({"spec": S, "sim": M, "menu": "category", "convention": "C-full", "pass": "B", "start": 0,
                        "stop": 20, "frozen": frozen, "placement": False})
    n_tau = 3
    names = [sm.quality_name(q) for q in sm.quality_points(M, sm.geometry(S, spec.menu_from(S, "category")))]
    for b in M["grids"]["budgets"]:
        for c in M["grids"]["c_d_grid"]:
            per_k = out["crit"][(b, float(c))].mean(axis=0)
            for ki, k in enumerate(sm.k_grid(8)):
                expected = np.mean([(out["sums"][(b, float(c), q, k)].data["g"] / 20).mean(axis=0).sum() / n_tau
                                    for q in names])
                assert per_k[ki] == pytest.approx(expected, abs=1e-9)


def test_the_monte_carlo_se_is_the_sd_over_root_n():                            # kills V13
    values = np.array([1.0, 2.0, 3.0, 4.0])
    out = pr._metric(np.array([[values.sum()]]), np.array([[(values ** 2).sum()]]), 4, ["p"], 0)
    assert out["mc_se_bound"] == pytest.approx(values.std(ddof=1) / 2.0)
    hits = pr._bernoulli(np.array([[3.0]]), 4, ["p"], 0)
    assert hits["mc_se_bound"] == pytest.approx(math.sqrt(0.75 * 0.25 / 4))


# ----- the A7 switch (S-3: V10, V11; S-10) ---------------------------------------------------------------


def _a7(M: dict, average: bool) -> dict:
    M = copy.deepcopy(M)
    M["model"]["rho_mode"] = "a7_switch"
    M["model"]["rho_average_for_rule"] = average
    return M


def test_the_rule_choice_table_is_the_rho_average_under_a7():                   # kills V10
    S, M, _ = fx.tiny()
    M = _a7(M, True)
    M["replicates"] = {"rule_choice": 20, "diagnostic": 10, "sensitivity": 10, "chunk": M["replicates"]["chunk"]}
    crit = sm.reduce_crit(sm.run_pass(S, M, "category", "C-full", "A", 20))
    res = sm.simulate(S, M, "category", "C-full", placement=False)
    for b in M["grids"]["budgets"]:
        for r in res["rules"]:
            averaged = float(np.mean([crit[(rho, float(b), r)] for rho in (0.0, 0.67)], axis=0).mean())
            assert res["rule_choice"][str(float(b))]["table"][r]["mean"] == pytest.approx(averaged, abs=1e-12)


def test_pass_a_runs_at_the_settings_rho():                                     # kills V11
    S, M, _ = fx.tiny()
    out = sm.run_chunk({"spec": S, "sim": M, "menu": "category", "convention": "C-full", "pass": "A", "start": 0,
                        "stop": 20, "frozen": None, "placement": False})
    menu, geom, ctx, d, points, G, tr = sm._setup(S, M, "category", "C-full", range(20))
    obs = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.0), tr["coherent"])
    for b in M["grids"]["budgets"]:
        for rule in ("one_shot", "halving"):
            direct = sm.outcome(spec.select(ctx, obs, rule=rule, budget=float(b)), tr)["g"]
            got = out["sums"][(0.0, float(b), rule)].data["g"]
            assert got == pytest.approx(direct.reshape(len(points), 20, -1).sum(axis=1), abs=1e-9)


def test_under_the_a7_average_k_is_chosen_on_the_rho_average():                 # S-10
    S, M, _ = fx.tiny()
    reps = 20
    frozen = {"rule": {str(b): "halving" for b in M["grids"]["budgets"]}}
    results = {}
    for average in (False, True):
        results[average] = sm.run_chunk({"spec": S, "sim": _a7(M, average), "menu": "category", "convention": "C-full",
                                         "pass": "B", "start": 0, "stop": reps, "frozen": frozen, "placement": False})
    M7 = _a7(M, True)
    menu, geom, ctx, d, points, G, tr = sm._setup(S, M7, "category", "C-full", range(reps))
    qpoints = sm.quality_points(M7, geom)
    tau_w = np.full(len(ctx.tau_o), 1.0 / len(ctx.tau_o))
    ks = sm.k_grid(menu.M)
    q_scores = [sm.scores(geom, M7, d, G, q) for q in qpoints]
    differs = False
    for b in M["grids"]["budgets"]:
        for c in M["grids"]["c_d_grid"]:
            per_rho = {}
            for rho in (0.0, 0.67):
                obs = sm.observations(geom, ctx, M7, d, G, sm.NoiseCase(2.65, rho), tr["coherent"])
                per_rho[rho] = np.zeros((reps, len(ks)))
                for score in q_scores:
                    for ki, k in enumerate(ks):
                        res = sm.outcome(spec.select(ctx, obs, rule="halving", budget=float(b), scores=score, k=k,
                                                     c_d=float(c)), tr)
                        per_rho[rho][:, ki] += sm.criterion_values(res, len(points), tau_w) / len(qpoints)
            assert results[False]["crit"][(float(b), float(c))] == pytest.approx(per_rho[0.0], abs=1e-10)
            averaged = (per_rho[0.0] + per_rho[0.67]) / 2
            assert results[True]["crit"][(float(b), float(c))] == pytest.approx(averaged, abs=1e-10)
            differs = differs or not np.allclose(per_rho[0.0], per_rho[0.67])
    assert differs                                                              # rho changes some outcome
    assert set(results[True]["sums"]) == set(results[False]["sums"])
    for key, s in results[True]["sums"].items():                                 # the Delta sums stay at rho = 0
        assert np.array_equal(s.data["g"], results[False]["sums"][key].data["g"])


# ----- one rule and one k per (menu, M, B) cell (B-1) ----------------------------------------------------


def test_one_rule_and_one_k_per_menu_m_b_cell_under_both_conventions(built_doc):
    differ = 0
    for menu_id, block in built_doc["menus"].items():
        assert block["freeze_scope"] == "menu_m_b"
        full, lean = block["conventions"]["C-full"]["budgets"], block["conventions"]["C-lean"]["budgets"]
        assert set(full) == set(lean)
        for b in full:
            for conv in (full, lean):
                assert conv[b]["frozen_over_conventions"] == CONVENTIONS
            assert full[b]["runs_only"]["frozen_rule"] == lean[b]["runs_only"]["frozen_rule"]
            assert full[b]["diagnostic"]["frozen_k"] == lean[b]["diagnostic"]["frozen_k"]
            choice = full[b]["runs_only"]["rule_choice"]
            assert choice == lean[b]["runs_only"]["rule_choice"] and choice["conventions"] == CONVENTIONS
            for row in choice["table"].values():
                by = row["mean_by_convention"]
                assert set(by) == set(CONVENTIONS)
                assert row["mean"] == pytest.approx((by["C-full"] + by["C-lean"]) / 2, rel=1e-8, abs=1e-9)
                differ += by["C-full"] != by["C-lean"]
            for k_choice in full[b]["diagnostic"]["k_choice"].values():
                assert k_choice["conventions"] == CONVENTIONS
                for row in k_choice["table"].values():
                    by = row["mean_by_convention"]
                    assert row["mean"] == pytest.approx((by["C-full"] + by["C-lean"]) / 2, rel=1e-8, abs=1e-9)
                    differ += by["C-full"] != by["C-lean"]
    assert differ > 0                                                           # the average is not trivial


def test_the_per_convention_switch_chooses_on_each_conventions_own_criterion():
    S, M, _ = fx.tiny()
    pooled = sm.simulate_menu(S, M, "category", CONVENTIONS)
    own_settings = copy.deepcopy(M)
    own_settings["criterion"]["freeze_scope"] = "menu_m_b_convention"
    own = sm.simulate_menu(S, own_settings, "category", CONVENTIONS)
    for c in CONVENTIONS:
        single = sm.simulate(S, M, "category", c, placement=False)
        assert own[c]["frozen"] == single["frozen"] and own[c]["frozen_over"] == [c]
        assert pooled[c]["frozen_over"] == CONVENTIONS and pooled[c]["frozen"] is pooled[CONVENTIONS[0]]["frozen"]
        for b, choice in own[c]["rule_choice"].items():
            for r, row in choice["table"].items():        # pass A does not depend on the frozen choices
                assert pooled[c]["rule_choice"][b]["table"][r]["mean_by_convention"][c] == pytest.approx(
                    row["mean"], abs=1e-12)
    with pytest.raises(s1.Refusal, match="freeze_scope"):
        bad = copy.deepcopy(M)
        bad["criterion"]["freeze_scope"] = "per_cell"
        sm.simulate_menu(S, bad, "category", CONVENTIONS)


def test_the_simulate_settings_name_the_freeze_scope_and_every_rho_grid_holds_zero():
    M = fx.raw("selector_simulate")
    assert M["criterion"]["freeze_scope"] == "menu_m_b" and set(M["criterion"]["freeze_scope_options"]) == set(
        sm.FREEZE_SCOPES)
    for path, value in ((("criterion", "freeze_scope"), "per_cell"), (("model", "rho_grids"), {"default": [0.0],
                                                                                                "a7_switch": [0.67]})):
        bad = copy.deepcopy(M)
        bad[path[0]][path[1]] = value
        with pytest.raises(s1.Refusal):
            sm.check(bad)


# ----- the replay: both L references (S-7) and the sample counts (S-8) ----------------------------------


def _labels(ctx: spec.Context, *, seeds: int = 4, samples: int | None = None, keep_samples: int | None = None,
            reference: bool = True) -> dict:
    def entry(j: int, u: float, l: float) -> dict:
        return {"seed_index": j, "u_prompts": {f"p{i:03d}": u for i in range(12)},
                "o_prompts": {f"o{i:03d}": 0 for i in range(10)}, "l_rows": {"t000": l, "t001": l}}
    doc = {"kind": spec.LABELS_KIND, "version": spec.LABELS_VERSION, "menu": ctx.menu.id,
           "samples_per_prompt": ctx.cost.samples_per_prompt if samples is None else samples,
           "keep": {"samples_per_prompt": ctx.keep_samples_per_prompt if keep_samples is None else keep_samples,
                    "seeds": [entry(j, 0.5, 0.0002 * j) for j in range(ctx.menu.keep_seeds)]},
           "options": {oid: {"coherent": True,
                             "seeds": [entry(j, 0.5 - 0.02 * i, 0.001 * i + 0.0005 * j) for j in range(seeds)]}
                       for i, oid in enumerate(ctx.menu.ids)}}
    if reference:
        doc["reference_r"] = {"seeds": [entry(j, 0.5, 0.003 + 0.0005 * j) for j in range(3)]}
    return doc


def test_the_replay_reports_the_l_bound_against_both_references():             # S-7
    S = fx.raw("selector_spec")
    S["screen"]["se_form"] = "pooled_residuals"        # the hand form below; the hb form: test_selector_rev2.py
    ctx = spec.context(S, "category", "C-full")
    labels = _labels(ctx)
    out = spec.replay(S, "category", "C-full", "halving", 8.0, labels)
    report = out["l_upper_nats"]
    assert report["reference_in_force"] == "a0" and report["tau_l_nats"] == ctx.tau_l
    seeds = out["full_seeds"]
    candidates = {oid for oid, n in seeds.items() if n >= 2}
    assert candidates and set(report["a0"]) == set(report["r"]) == candidates
    z = NormalDist().inv_cdf(ctx.upper_quantile)
    l_of = {oid: [0.001 * i + 0.0005 * j for j in range(seeds[oid])] for i, oid in enumerate(ctx.menu.ids)}
    arms = {"a0": [0.0002 * j for j in range(3)], "r": [0.003 + 0.0005 * j for j in range(3)]}
    for name, arm in arms.items():
        ss = sum(((np.array(v) - np.mean(v)) ** 2).sum() for v in l_of.values() if len(v) >= 2)
        ss += ((np.array(arm) - np.mean(arm)) ** 2).sum()
        df = sum(len(v) - 1 for v in l_of.values() if len(v) >= 2) + len(arm) - 1
        for oid in candidates:
            n = len(l_of[oid])
            hand = np.mean(l_of[oid]) - np.mean(arm) + z * math.sqrt(ss / df * (1 / n + 1 / len(arm)))
            assert report[name][oid] == pytest.approx(hand, abs=1e-12), (name, oid)
    without = spec.replay(S, "category", "C-full", "halving", 8.0, _labels(ctx, reference=False))
    assert without["l_upper_nats"]["r"] is None and set(without["l_upper_nats"]["a0"]) == candidates


def test_a_replay_refuses_labels_with_another_sample_count():                  # S-8
    S = fx.raw("selector_spec")
    full = spec.context(S, "category", "C-full")
    lean = spec.context(S, "category", "C-lean")
    assert (full.cost.samples_per_prompt, lean.cost.samples_per_prompt, lean.keep_samples_per_prompt) == (3, 1, 3)
    labels = _labels(full)
    assert spec.replay(S, "category", "C-full", "one_shot", 4.0, labels)["spent"] > 0
    with pytest.raises(s1.Refusal, match="samples per prompt"):
        spec.replay(S, "category", "C-lean", "one_shot", 4.0, labels)            # a lean replay of full evaluations
    assert spec.replay(S, "category", "C-lean", "one_shot", 4.0, _labels(lean))["spent"] > 0
    for samples, keep_samples in ((1, 1), (True, 3), (3.0, 3), (3, None)):
        bad = _labels(full, samples=samples, keep_samples=keep_samples)
        if keep_samples is None:
            del bad["keep"]["samples_per_prompt"]
        with pytest.raises(s1.Refusal, match="samples per prompt"):
            spec.replay(S, "category", "C-full", "one_shot", 4.0, bad)
    old = _labels(full)
    old["version"] = 1
    with pytest.raises(s1.Refusal, match="version-2"):
        spec.replay(S, "category", "C-full", "one_shot", 4.0, old)
    settings = copy.deepcopy(S)
    settings["saved_labels"]["version"] = 1
    with pytest.raises(s1.Refusal, match="saved labels"):
        spec.check(settings)


# ----- inputs (S-11), c* (N-1), option cost (N-3) ------------------------------------------------------


def test_check_inputs_resolves_an_unpinned_input_by_its_hint_and_prefix(tmp_path):
    for name, data in (("u1", b"a\n"), ("u2", b"b\n")):
        p = tmp_path / "tmp" / "gate-b-olmo" / "w" / name / "ledger.jsonl"
        p.parent.mkdir(parents=True)
        p.write_bytes(data)
    digest = sha256_bytes(b"b\n")
    entry = {"id": "led", "path": None, "path_hint": "tmp/gate-b-olmo/w/<the unit of R_2>/ledger.jsonl",
             "sha256_prefix": digest[:16], "gate_b_value": True}
    rows = pr.check_inputs({"inputs": [entry]}, tmp_path, resolve=True)
    assert [(r["path"], r["sha256"]) for r in rows] == [("tmp/gate-b-olmo/w/u2/ledger.jsonl", digest)]
    assert pr.check_inputs({"inputs": [entry]}, tmp_path)[0]["status"].startswith("unpinned")
    cases = [({"sha256_prefix": "0" * 16}, "0 files"), ({"gate_b_value": False}, "Gate B"),
             ({"sha256_prefix": digest[:8]}, "prefix"), ({"path_hint": "/x/<y>/ledger.jsonl"}, "relative")]
    for change, message in cases:
        with pytest.raises(s1.Refusal, match=message):
            pr.check_inputs({"inputs": [{**entry, **change}]}, tmp_path, resolve=True)
    twin = tmp_path / "tmp" / "gate-b-olmo" / "w" / "u3" / "ledger.jsonl"
    twin.parent.mkdir()
    twin.write_bytes(b"b\n")
    with pytest.raises(s1.Refusal, match="2 files"):
        pr.check_inputs({"inputs": [entry]}, tmp_path, resolve=True)


def test_every_input_of_the_pinned_settings_has_a_path_and_a_full_sha256():   # S-11
    for entry in fx.raw("selector_simulate")["inputs"]:
        assert entry["path"] and not entry["path"].startswith("/") and s1.HEX64.match(entry["sha256"]), entry["id"]
        if entry["path"].startswith(pr.GATE_B_WAVE_PREFIXES):
            assert entry["gate_b_value"] is True, entry["id"]


def test_c_star_none_still_reports_a_later_crossing_as_non_monotone():         # N-1
    grid = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]
    out = pr.c_star(grid, [-0.1, -0.2, 0.3, -0.1, -0.2, -0.3])
    assert out["kind"] == "none" and out["non_monotone"] is True
    assert pr.c_star(grid, [-0.1] * 6)["non_monotone"] is False


def test_an_option_cost_other_than_one_fre_refuses():                          # N-3
    S = fx.raw("selector_spec")
    assert spec.menu_from(S, "category").options[0].cost_fre == 1.0
    S["menus"]["category"]["options"][0]["cost_fre"] = 1.5
    with pytest.raises(s1.Refusal, match="one full run"):
        spec.menu_from(S, "category")
