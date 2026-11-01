"""Part E rev 2 (the lead's one-pass ruling, addendum section 10: LN-10, LN-11, LN-29, LN-07, LN-33, LN-20; REV3
section 7.4; ledger X-1 to X-4): the literal pins of the three selector settings files, the rulings in the pinned
settings, the HB-form screen (LN-20's theta0 and paired forms with Satterthwaite t), the Student t quantiles, the
500-prompt O bank's costs and prompt part, and the swapped planted placement. Synthetic data only."""

from __future__ import annotations

import copy
import dataclasses
import json
import math
from statistics import NormalDist

import numpy as np
import pytest

from experiments.safety_selection.common import sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1.selector import predict as pr
from scripts.stage1.selector import simulate as sm
from scripts.stage1.selector import spec

import selector_fixtures as fx

SPEC_SETTINGS_SHA256 = "b4bd06c35061cea6f52c489946a45ab9a25e01f1bf9e3073b7f208e17d68e510"
SIMULATE_SETTINGS_SHA256 = "4d9e0064828338bcfdd3703c5039fb179dd2ec7f33501cc448cceb94bb8302b9"
PREDICT_SETTINGS_SHA256 = "2d45c3c280ad08c5640bd38b02c201d9db597e5c6599b857ce9ddaed5f516cb0"

O_EXT_S = 400 * (1694.0 + 80.0) / 468.0                     # the 400 PHTest prompts' greedy answers and guard
# notes/l_item_sd_check.out.json (the Gate A a0 task-row tables): the paired per-row SE of each seed pair
PAIR_ROW_SE = (0.0027098209259276795, 0.0026085938432855215, 0.0030948144213433057)
DIGESTS = {"selector_spec": "a" * 64, "selector_simulate": "b" * 64, "selector_predict": "c" * 64}


# ----- literal pins (T1 convention: the module literal, the test literal and the file agree) -------------


def test_the_three_settings_files_have_their_literal_pins():
    for module, literal in ((spec, SPEC_SETTINGS_SHA256), (sm, SIMULATE_SETTINGS_SHA256),
                            (pr, PREDICT_SETTINGS_SHA256)):
        assert module.SETTINGS_SHA256 == literal and sha256_file(module.SETTINGS_PATH) == literal
    assert spec.load()[1] == SPEC_SETTINGS_SHA256 and sm.load()[1] == SIMULATE_SETTINGS_SHA256
    assert pr.load()[1] == PREDICT_SETTINGS_SHA256


def test_the_revised_settings_keep_the_t1_registry_convention():
    for name in ("selector_spec", "selector_simulate", "selector_predict"):
        doc = fx.raw(name)
        assert doc["version"] == 2 and "LN-10" in doc["revision"] and s1.HEX64.match(doc["labels_sha256"])
        assert s1.check_settings(doc, name) is doc
        for key, digest in doc["label_entries"].items():
            assert s1.entry_digest(key) == digest


# ----- the rulings in the pinned settings -----------------------------------------------------------------


def test_a7_is_in_force_with_the_rho_average_and_the_freeze_scope_stays_menu_m_b():      # LN-10, X-1; B-1
    M = fx.raw("selector_simulate")
    assert M["model"]["rho_mode"] == "a7_switch" and sm.rho_grid(M) == [0.0, 0.67]
    assert M["model"]["rho_average_for_rule"] is True
    assert M["model"]["rho_grids"]["default"] == [0.0]                                    # the fallback's grid
    assert "rho_0.67" in M["sensitivities"] and set(M["sensitivities"]) <= set(M["sensitivity_options"])
    assert M["criterion"]["freeze_scope"] == "menu_m_b"


def test_the_screen_uses_the_hb_form_with_the_l_item_sd():                                # LN-10, LN-20, X-2
    S = fx.raw("selector_spec")
    assert S["screen"]["se_form"] == "hb" and set(S["screen"]["se_form_options"]) == set(spec.SE_FORMS)
    assert S["screen"]["l_item_sd_nats"] == pytest.approx(sum(PAIR_ROW_SE) / 3, rel=1e-15)
    assert S["screen"]["l_item_sd_nats"] / 0.002374850619448416 == pytest.approx(1.1809, abs=1e-4)
    assert S["screen"]["tau_l_reference"] == "a0" and S["screen"]["upper_quantile"] == 0.95


def test_the_o_planning_values_are_at_the_500_prompt_bank():                              # LN-10, X-3; LN-07
    S = fx.raw("selector_spec")
    bank = S["o_bank"]
    assert (bank["dev_prompts"], bank["bank_prompts"]) == (100, 500)
    assert [conv["o_prompts"] for _, conv in spec._conventions(S)] == [500, 500, 500]
    for convention in ("C-full", "C-lean"):
        ctx = spec.context(S, "category", convention)
        assert ctx.o_prompts == 500 and ctx.o_prompt_sd == pytest.approx(4.1 * math.sqrt(0.2))
    assert S["screen"]["o_prompt_sd_pp"] == 4.1 and S["limits"]["o_theta0_pp"] == 17.0      # dev-100 planning values
    assert spec.o_prompt_sd(fx.dev100(), "C-lean") == pytest.approx(4.1)                  # LN-07's fallback form


def test_both_conventions_hold_the_500_bank_and_1_fre_stays_2934_s():                     # LN-33, LN-07
    S = fx.raw("selector_spec")
    assert bank_price(S) == pytest.approx((1694.0 + 80.0) / 468.0)
    assert spec.o_bank_seconds(S, "C-full") == pytest.approx(O_EXT_S)
    full = spec.cost_model(S, "C-full")
    assert full.unit == 2934.0 and full.full * full.unit == pytest.approx(2934.0 + O_EXT_S)
    assert full.full == pytest.approx(1.5168, abs=1e-4)                                    # about 0.52 FRE more
    lean = spec.cost_model(S, "C-lean")
    assert lean.unit == pytest.approx(870.0 + O_EXT_S) and lean.unit / full.unit == pytest.approx(0.8133, abs=1e-4)
    D = fx.dev100()
    assert spec.cost_model(D, "C-full").full == pytest.approx(1.0) and spec.cost_model(D, "C-lean").unit == 870.0


def bank_price(S: dict) -> float:
    return S["o_bank"]["greedy_s_per_prompt"] + S["o_bank"]["guard_s_per_answer"]


def test_the_planted_placement_is_swapped_to_row_auc_primary():                           # LN-29, LW-11
    P = fx.raw("selector_predict")
    assert (P["placement"]["planted_primary"], P["placement"]["planted_secondary"]) == ("row_auc", "top_k_hit")
    assert "row AUC (plant rows against Dolly rows, primary" in P["placement"]["rule"].replace("empirical ", "")


def test_the_two_stale_notes_are_corrected_and_the_pick_stays_unpaired():                  # LN-11, X-4
    S = fx.raw("selector_spec")
    assert "PLAN-S:102, the model in force" not in S["pick"]["rule"]
    assert "Seeds are not paired" in S["pick"]["rule"] and "LN-11" in S["pick"]["rule"]
    note = S["screen"]["tau_l_reference_note"]
    assert "to GPT" not in note and "LW-07" in note
    ctx = fx.context(fx.custom_menu(2))
    obs = fx.exact_obs(ctx, np.array([[48.0, 50.0]]))
    obs.u[0, 0, 1] = 46.0                                     # seed 1 of option 0 lower than seed 0
    obs.keep_u = np.array([[50.0, 52.0, 54.0]])
    state = spec.State.empty(1, 2, ctx.max_seeds)
    state.level[0, :, :2] = ctx.c1
    est = spec.estimates(ctx, spec._full_view(obs, ctx), state)
    assert est["g_raw"][0, 0] == pytest.approx(52.0 - 47.0)    # unpaired: keep's 3 seeds against the option's 2
    assert est["g_raw"][0, 0] != pytest.approx(((50.0 - 48.0) + (52.0 - 46.0)) / 2)        # not the paired mean


# ----- Student t quantiles ---------------------------------------------------------------------------------


# published quantiles (10 significant digits)
T95 = {1: 6.313751515, 2: 2.919985580, 3: 2.353363435, 4: 2.131846786, 5: 2.015048373, 10: 1.812461123,
       30: 1.697260887, 120: 1.657650899}
T90 = {1: 3.077683537, 2: 1.885618083, 5: 1.475884049, 30: 1.310415025}


def test_the_exact_t_quantiles_match_the_published_values():
    for q, table in ((0.95, T95), (0.90, T90)):
        df = np.array(list(table), float)
        assert spec.t_quantile_exact(q, df) == pytest.approx(np.array(list(table.values())), abs=2e-9)
        assert spec.t_quantile_exact(q, np.array([np.inf]))[0] == pytest.approx(NormalDist().inv_cdf(q), abs=1e-15)
    t = spec.t_quantile_exact(0.95, np.array([1.0, 1.7, 3.3, 25.0, 400.0, 9999.0]))
    assert spec.t_upper_tail(t, np.array([1.0, 1.7, 3.3, 25.0, 400.0, 9999.0])) == pytest.approx(0.05, abs=1e-12)
    big = spec.t_quantile_exact(0.95, np.array([2e4, 1e7]))                       # the series branch
    assert big[0] == pytest.approx(1.644853627 + (1.644853627 ** 3 + 1.644853627) / 4 / 2e4, abs=1e-8)
    assert big[1] == pytest.approx(NormalDist().inv_cdf(0.95), abs=1e-6)
    with pytest.raises(s1.Refusal):
        spec.t_quantile_exact(0.95, np.array([0.5]))
    with pytest.raises(s1.Refusal):
        spec.t_quantile_exact(0.4, np.array([3.0]))


def test_the_interpolated_t_table_is_within_1e_7_of_the_exact_quantile():
    rng = np.random.default_rng(20261017)
    df = np.concatenate([1 + rng.exponential(3, 500), 10 ** rng.uniform(0, 6, 500), [1.0, 2.0, 5.0, 1e9]])
    for q in (0.95, 0.90):
        exact = spec.t_quantile_exact(q, df)
        assert spec.t_quantile(q, 1 / df) == pytest.approx(exact, rel=1e-7)
    assert spec.t_quantile(0.95, np.array([0.0]))[0] == pytest.approx(NormalDist().inv_cdf(0.95), abs=1e-15)
    with pytest.raises(s1.Refusal, match="df below 1"):
        spec.t_quantile(0.95, np.array([1.5]))


def test_the_satterthwaite_df_of_a_seed_part_and_a_known_item_part():
    est, v_seed, df_seed, item = np.array([0.0]), np.array([2.0]), np.array([3]), 6.0
    upper = spec._hb_upper(est, [(v_seed, df_seed)], item, 0.95)
    df = (2.0 + 6.0) ** 2 / (2.0 ** 2 / 3)
    assert upper[0] == pytest.approx(spec.t_quantile_exact(0.95, np.array([df]))[0] * math.sqrt(8.0), rel=1e-7)
    no_item = spec._hb_upper(est, [(v_seed, df_seed)], 0.0, 0.95)
    assert no_item[0] == pytest.approx(spec.t_quantile_exact(0.95, np.array([3.0]))[0] * math.sqrt(2.0), rel=1e-7)
    assert spec._hb_upper(est, [(v_seed, np.array([0]))], item, 0.95)[0] == np.inf          # no seed df: no bound
    zero = spec._hb_upper(est, [(np.array([0.0]), np.array([1]))], item, 0.95)[0]            # no seed variance
    assert zero == pytest.approx(NormalDist().inv_cdf(0.95) * math.sqrt(6.0), rel=1e-12)


# ----- the HB-form screen through the replay and the simulation ----------------------------------------------


def _labels(ctx: spec.Context, seeds: int = 4) -> dict:
    def entry(j: int, u: float, l: float) -> dict:
        return {"seed_index": j, "u_prompts": {f"p{i:03d}": u for i in range(12)},
                "o_prompts": {f"o{i:03d}": 0 for i in range(10)}, "l_rows": {"t000": l, "t001": l}}
    return {"kind": spec.LABELS_KIND, "version": spec.LABELS_VERSION, "menu": ctx.menu.id,
            "samples_per_prompt": ctx.cost.samples_per_prompt,
            "keep": {"samples_per_prompt": ctx.keep_samples_per_prompt,
                     "seeds": [entry(j, 0.5, 0.0002 * j) for j in range(ctx.menu.keep_seeds)]},
            "options": {oid: {"coherent": True,
                              "seeds": [entry(j, 0.5 - 0.02 * i, 0.001 * i + 0.0005 * j + 0.0003 * (j % 2))
                                        for j in range(seeds)]} for i, oid in enumerate(ctx.menu.ids)},
            "reference_r": {"seeds": [entry(j, 0.5, 0.003 + 0.0005 * j) for j in range(3)]}}


def test_the_replay_l_report_uses_the_paired_hb_form_against_both_references():             # S-7 under hb
    S = fx.raw("selector_spec")
    ctx = spec.context(S, "category", "C-full")
    out = spec.replay(S, "category", "C-full", "halving", 16.0, _labels(ctx, seeds=ctx.max_seeds))
    report, seeds = out["l_upper_nats"], out["full_seeds"]
    candidates = {oid for oid, n in seeds.items() if n >= 2}
    assert candidates and set(report["a0"]) == set(report["r"]) == candidates
    assert max(seeds.values()) > 3                            # some option has more seeds than keep
    arms = {"a0": [0.0002 * j for j in range(3)], "r": [0.003 + 0.0005 * j for j in range(3)]}
    item = ctx.l_item_sd ** 2
    for name, arm in arms.items():
        for i, oid in enumerate(ctx.menu.ids):
            if oid not in candidates:
                continue
            common = min(seeds[oid], 3)
            d = np.array([0.001 * i + 0.0005 * j + 0.0003 * (j % 2) - arm[j] for j in range(common)])
            v = d.var(ddof=1) / common
            df = (common - 1) * (v + item) ** 2 / v ** 2
            hand = d.mean() + spec.t_quantile_exact(0.95, np.array([df]))[0] * math.sqrt(v + item)
            assert report[name][oid] == pytest.approx(hand, abs=1e-10), (name, oid)


def test_the_simulated_o_bank_term_is_the_prompt_part_at_the_bank():
    S, M, _ = fx.tiny()
    for settings, sd in ((S, 4.1 * math.sqrt(0.2)), (fx.dev100(S), 4.1)):
        menu, geom, ctx, d, points, G, tr = sm._setup(settings, M, "category", "C-lean", range(4))
        assert ctx.o_prompt_sd == pytest.approx(sd)
        seed_only = dataclasses.replace(ctx, o_error_model="seed_only")
        a = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.0), tr["coherent"])
        b = sm.observations(geom, seed_only, M, d, G, sm.NoiseCase(2.65, 0.0), tr["coherent"])
        bank = np.tile(d["noise"][:, 2:2 + menu.M, 0, ctx.a1, ctx.c1, 4], (len(points), 1))     # (P x R, M)
        assert np.allclose(a.o - b.o, sd * bank[:, :, None])


def test_in_force_one_shot_schedule_hand_values():
    """The 500-bank C-full costs: at B = 8 one-shot screens all 8 options and can promote one finalist."""
    ctx = fx.context(fx.custom_menu(8))
    evaluation = 2623.2 + O_EXT_S
    screen = (91.1 + 219.7 + 0.25 * evaluation) / 2934.0
    full = (91.1 + 219.7 + evaluation) / 2934.0
    promote = 0.75 * evaluation / 2934.0 + full
    assert ctx.screen_cost == pytest.approx(screen) and ctx.promote_cost(1) == pytest.approx(promote)
    g = np.array([[0, 0, 0, 0, 0, 0, 9.0, 0]])
    sel = spec.select(ctx, fx.exact_obs(ctx, 50.0 - g), rule="one_shot", budget=8.0)
    n_s = min(8, math.floor((8.0 - promote) / screen + 1e-9))
    n_f = min(n_s, 2, math.floor((8.0 - n_s * screen) / promote + 1e-9))
    assert (n_s, n_f) == (8, 1)
    extra = math.floor((8.0 - n_s * screen - n_f * promote) / full + 1e-9)
    assert sel.spent[0] == pytest.approx(n_s * screen + n_f * promote + extra * full)
    assert sel.full_seeds.sum() == 2 + extra and (sel.pick == 6).all()
    nothing = spec.select(ctx, fx.exact_obs(ctx, 50.0 - g), rule="one_shot", budget=2.0)
    assert (nothing.pick == spec.KEEP).all() and nothing.spent[0] == 0.0                   # B = 2 < 2 full runs


# ----- checks that refuse ------------------------------------------------------------------------------------


@pytest.mark.parametrize("change,message", [
    (lambda S: S["cost_conventions"]["C-full"].update({"o_prompts": 300}), "o_prompts"),
    (lambda S: S["cost_conventions"]["C-lean"]["variants"]["b"].update({"o_part": "training"}), "o_part"),
    (lambda S: S["cost_conventions"]["C-lean"]["variants"]["a"].update({"unit_s": 870.0}), "only C-full"),
    (lambda S: S["cost_conventions"]["C-full"].pop("unit_s"), "only C-full"),
    (lambda S: S["cost_conventions"]["C-full"].update({"unit_s": 2900.0}), "job slot"),
    (lambda S: S["o_bank"].update({"bank_prompts": 100}), "dev and bank"),
    (lambda S: S["o_bank"].update({"greedy_s_per_prompt": 0.0}), "price"),
    (lambda S: S["screen"].update({"l_item_sd_nats": -0.001}), "L item SD"),
    (lambda S: S["screen"].update({"se_form": "hb_paired"}), "switch"),
    (lambda S: S["screen"].update({"se_form_options": ["hb", "pooled_residuals"]}), "switch"),
])
def test_the_spec_check_refuses_a_bad_bank_cost_or_screen_setting(change, message):
    S = fx.raw("selector_spec")
    spec.check(S)
    change(S)
    with pytest.raises(s1.Refusal, match=message):
        spec.check(S)


def test_the_predict_check_refuses_a_placement_without_both_statistics():
    P = fx.raw("selector_predict")
    pr.check(P)
    for primary, secondary in (("row_auc", "row_auc"), ("top_k_hit", "spearman_rho")):
        bad = copy.deepcopy(P)
        bad["placement"].update({"planted_primary": primary, "planted_secondary": secondary})
        with pytest.raises(s1.Refusal, match="planted placement"):
            pr.check(bad)


# ----- the predictions document under the in-force settings -------------------------------------------------


@pytest.fixture(scope="module")
def built_doc() -> dict:
    S, M, P = fx.tiny()
    return json.loads(pr.build(S, M, P, DIGESTS))


def test_the_predictions_record_the_rev2_model_costs_and_screen(built_doc):
    model = built_doc["model"]
    assert model["rho_grid"] == [0.0, 0.67] and model["rho_average_for_rule"] is True
    assert model["se_form"] == "hb" and "rho_0.67" in model["sensitivities"]
    for menu_id, block in built_doc["menus"].items():
        full, lean = block["conventions"]["C-full"], block["conventions"]["C-lean"]
        assert full["costs_in_c0"]["unit_seconds"] == 2934.0
        assert full["costs_in_c0"]["full_run"] == pytest.approx((2934.0 + O_EXT_S) / 2934.0, abs=1e-9)
        assert lean["costs_in_c0"]["unit_seconds"] == pytest.approx(870.0 + O_EXT_S, abs=1e-6)
        assert lean["costs_in_c0"]["full_run"] == pytest.approx(1.0)
        for conv in (full, lean):
            assert conv["screen"] == {"o_prompts": 500, "o_prompt_sd_pp": pytest.approx(4.1 * math.sqrt(0.2)),
                                      "l_item_sd_nats": pytest.approx(sum(PAIR_ROW_SE) / 3)}
            assert conv["costs_in_c0"]["o_bank_seconds"] == pytest.approx(O_EXT_S, abs=1e-6)
            for cell in conv["budgets"].values():
                assert set(cell["runs_only"]["by_rho"]) == {"0.67"} and "rho_0.67" in cell["sensitivities"]
    assert built_doc["menus"]["planted_8"]["placement"]["statistic"] == {"primary": "row_auc",
                                                                         "secondary": "top_k_hit"}


def test_the_in_force_rule_choice_is_the_equal_weight_rho_average():                       # LN-10 (ambitious)
    S, M, _ = fx.tiny()
    M["replicates"] = {"rule_choice": 20, "diagnostic": 10, "sensitivity": 10, "chunk": M["replicates"]["chunk"]}
    crit = sm.reduce_crit(sm.run_pass(S, M, "category", "C-full", "A", 20))
    res = sm.simulate(S, M, "category", "C-full", placement=False)
    for b in M["grids"]["budgets"]:
        for r in res["rules"]:
            averaged = float(np.mean([crit[(rho, float(b), r)] for rho in (0.0, 0.67)], axis=0).mean())
            assert res["rule_choice"][str(float(b))]["table"][r]["mean"] == pytest.approx(averaged, abs=1e-12)


def test_the_rho_067_sensitivity_runs_at_rho_067():                                       # A7's sensitivity
    S, M, _ = fx.tiny()
    frozen = {"rule": {str(b): "halving" for b in M["grids"]["budgets"]},
              "k": {f"{b:g}|{c:g}": 8 for b in M["grids"]["budgets"] for c in M["grids"]["c_d_grid"]}}
    out = sm.run_chunk({"spec": S, "sim": M, "menu": "category", "convention": "C-full", "pass": "C", "start": 0,
                        "stop": 20, "frozen": frozen, "placement": False})
    menu, geom, ctx, d, points, G, tr = sm._setup(S, M, "category", "C-full", range(20))
    differs = False
    for rho_case, rho in (("rho_0.67", 0.67), ("sigma_high", 0.0)):
        sigma = 2.65 if rho_case == "rho_0.67" else 3.85
        obs = sm.observations(geom, ctx, M, d, G, sm.NoiseCase(sigma, rho), tr["coherent"])
        for b in M["grids"]["budgets"]:
            direct = sm.outcome(spec.select(ctx, obs, rule="halving", budget=float(b)), tr)["g"]
            got = out["sums"][(rho_case, float(b), "runs", "halving")].data["g"]
            assert got == pytest.approx(direct.reshape(len(points), 20, -1).sum(axis=1), abs=1e-9)
            if rho_case == "rho_0.67":
                at_zero = sm.outcome(spec.select(ctx, sm.observations(geom, ctx, M, d, G, sm.NoiseCase(2.65, 0.0),
                                                                       tr["coherent"]), rule="halving",
                                                 budget=float(b)), tr)["g"]
                differs = differs or not np.allclose(direct, at_zero)
    assert differs


def test_a_replay_refuses_keep_or_reference_seed_indices_that_are_not_0_to_k():
    """The paired hb screen pairs an option's seed j with the reference arm's seed j."""
    S = fx.raw("selector_spec")
    ctx = spec.context(S, "category", "C-full")
    assert spec.replay(S, "category", "C-full", "halving", 8.0, _labels(ctx, seeds=ctx.max_seeds))["spent"] > 0
    for arm in ("keep", "reference_r"):
        bad = _labels(ctx, seeds=ctx.max_seeds)
        for entry in bad[arm]["seeds"]:
            entry["seed_index"] += 1                       # seeds 1..3: no seed 0
        with pytest.raises(s1.Refusal, match="seed indices are not 0"):
            spec.replay(S, "category", "C-full", "halving", 8.0, bad)


# ----- two rev-1 kills that the rev-2 settings made blind (the finish pass; shards 5 and 2 of the rev-2 run) ---


def test_the_pick_needs_two_full_run_seeds_when_the_screen_admits_one():          # kills E-pick-one-full-seed
    """Under hb (in force) a one-seed option has no bound, so the screen drops it before the pick's seed check
    runs; under the pooled_residuals fallback the screen admits it and only pick.min_full_run_seeds stops it."""
    for se_form, admitted in (("pooled_residuals", True), ("hb", False)):
        ctx = fx.context(fx.custom_menu(3), se_form=se_form)
        view = spec._full_view(fx.exact_obs(ctx, np.array([[40.0, 45.0, 50.0]])), ctx)
        state = spec.State.empty(1, 3, ctx.max_seeds)
        state.level[0, 0, 0] = state.level[0, 1, 0] = ctx.c1                      # options 0 and 1: one seed each
        est = spec.estimates(ctx, view, state)
        assert spec.feasibility(ctx, view, est["full"], est["n_full"])[0, :2].all() == admitted
        assert (spec.pick(ctx, view, state, np.ones(1, bool)) == spec.KEEP).all()   # a one-seed option is never picked
        state.level[0, 0, 1] = ctx.c1                                               # a second seed: option 0 (G = 10)
        assert (spec.pick(ctx, view, state, np.ones(1, bool)) == 0).all()


def test_the_rules_visit_a_compact_view_in_the_sealed_tie_order():                   # kills V12 at the rev-2 costs
    """A compact view holds the available options in tie order, whatever the menu order. The rev-1 probe (one-shot
    at B = 4 on the category menu) screened 7 of 8 at the dev-100 costs and screens 3 of 8 at the 500-bank costs,
    where the sealed order's first and last options no longer tell the two orders apart; this test sets the order."""
    tie = np.array([5, 2, 7, 0, 3, 6, 1, 4])                                         # not the menu order
    ctx = dataclasses.replace(fx.context(fx.custom_menu(8)), tie_rank=tie)
    obs = fx.exact_obs(ctx, 50.0 - np.arange(8.0)[None, :])
    view = spec._compact(obs, ctx, np.ones((1, 8), bool))
    assert view.index[0].tolist() == np.argsort(tie).tolist() == [3, 6, 1, 4, 7, 0, 5, 2]
    assert view.u[0, :, 0, ctx.a1, ctx.c1].tolist() == (50.0 - np.arange(8.0))[view.index[0]].tolist()
    part = spec._compact(obs, ctx, np.array([[True, False, True, True, False, True, False, True]]))
    assert part.index[0].tolist() == [3, 7, 0, 5, 2] and part.m == 5 and part.tie.tolist() == [0, 1, 2, 3, 4]
    sel = spec.select(ctx, obs, rule="one_shot", budget=4.0)                        # 3 of 8 screened, 1 finalist
    screened = sel.view.index[0][sel.state.level[0, :, 0] >= 0]
    assert sorted(screened.tolist()) == [1, 3, 6] and len(screened) == 3
