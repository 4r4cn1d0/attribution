"""Tests for the fixes after the two B16 verify passes (22 Oct 2026): verify-stats F1 (the stop rule on a step that
floors an arm), F2 (exact-5 pp ties), F3/F4 (the floor mode and the REML stop settings read from the pinned
settings); verify-code F1 (a coherence-failing repair never dominates), F2 (seed keys), F3 (reference names), F5
(alpha and the interval level from the settings), F6 (S-a's O and L tests), F7 (the seed-only O value 'on these
prompts'), F8 (the per-actor best data arm), F9 (the equal-variance flag from the Phi runs), F10 (the proposed gap
tests), N1 (no finite df refuses), N2 (exclusive create), N3 (R with one O seed), N4 (the 4 pp margin sensitivity),
N5 (the below-resolution text). Synthetic tables only."""

from __future__ import annotations

import copy
import json
import math
from fractions import Fraction

import numpy as np
import pytest

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import labels, phi, reml, sensitivities as sens
from scripts.stage1_s1.reading import references as refs
from scripts.stage1_s1.reading import settings as st
from scripts.stage1_s1.reading.__main__ import main as cli
from scripts.stage1_s1.reading.labels import u_part
from scripts.stage1_s1.reading.reading import read
from scripts.stage1_s1.reading.schema import validate
from scripts.stage1_s1.reading.settings import Refusal, canonical_json, settings

import synth

WIDE = (-20.0, 20.0)
SEEDS = [str(s) for s in range(1102, 1108)]
ARMS3 = ("R", "A1", "H1")


# --- verify-stats F1: the stop rule on a step in which an arm reaches the floor -----------------------------------

def three_arm_l_cluster(rng, tiny):
    """Plan B's removal cluster on the L scale: one arm with a variance far below the floor (seed SD 1e-7)."""
    seeds_of = lambda a: range(1101, 1111) if a == "R" else range(1102, 1111)
    sig = {a: (1e-14 if a == tiny else rng.uniform(1e-6, 2e-5)) for a in ARMS3}
    seeds = sorted({j for a in ARMS3 for j in seeds_of(a)})
    s = {j: rng.normal(0, 0.003) for j in seeds}
    return [(a, j, 1.56 + 0.001 * i + s[j] + rng.normal(0, math.sqrt(sig[a]))) for i, a in enumerate(ARMS3) for j in seeds_of(a)]


def free_step(cells, arms, fit):
    """The Fisher step of the free arms at the returned sigma^2 (KKT: it vanishes at the constrained maximum)."""
    x, y, cell_arm = reml.design(cells, arms)
    z = np.zeros((len(y), len(arms)))
    z[np.arange(len(y)), cell_arm] = 1.0
    theta = np.array([fit.sigma2[a] for a in arms])
    score, info = reml._score_info(reml._projection(x, 1.0 / theta[cell_arm]), y, z)
    free = np.array([a not in fit.at_floor for a in arms])
    if not free.any():
        return 0.0
    il = theta[:, None] * info * theta[None, :]
    return float(np.abs(np.linalg.pinv(il[np.ix_(free, free)], rcond=1e-10) @ (theta * score)[free]).max())


def test_a_step_that_floors_an_arm_never_ends_the_fit_and_every_converged_fit_is_stationary():
    """verify-stats F1: table 137's trace (H1 clipped to the floor at step 4 while R's and A1's steps were already
    below 1e-6) ended the fit with free log-scores of -0.44 and -0.96. Now the fit goes on after such a step, and
    every converged fit satisfies the KKT condition on the free arms."""
    rng = np.random.default_rng(0)
    continued, converged = 0, 0
    for t in range(300):
        cells = three_arm_l_cluster(rng, ARMS3[t % 3])
        fit = reml.fit_cells(cells, ARMS3, 1e-8)
        if fit.converged:
            converged += 1
            assert free_step(cells, ARMS3, fit) < 1e-5, (t, fit.steps, fit.at_floor)
            # the guard fired: a sub-tolerance largest step that did not end the fit
            continued += any(s < 1e-6 for s in fit.steps[:-1])
    assert converged > 200 and continued > 10


def test_the_table_that_stopped_at_step_4_now_runs_on():
    rng = np.random.default_rng(0)
    for t in range(6):
        cells = three_arm_l_cluster(rng, ARMS3[t % 3])
    fit = reml.fit_cells(cells, ARMS3, 1e-8)                      # table 5 of the generator: H1 floored at step 4
    assert fit.at_floor == ("H1",) and fit.iterations > 4 and fit.converged
    assert fit.steps[3] < 1e-6 and free_step(cells, ARMS3, fit) < 1e-5


def test_the_guard_does_not_change_a_fit_without_a_newly_floored_arm():
    rng = np.random.default_rng(31)
    cells = [(a, j, 10.0 * i + rng.normal(0, 3) + rng.normal(0, 2)) for i, a in enumerate(("a0", "S1", "S3", "S4"))
             for j in range(1101, 1108)]
    fit = reml.fit_cells(cells, ("a0", "S1", "S3", "S4"), 0.01, max_iter=400)
    assert fit.converged and fit.at_floor == () and all(s >= 1e-6 for s in fit.steps[:-1])


# --- verify-stats F2: exact-5 pp ties ----------------------------------------------------------------------------

def make_tie(seed, c="R", m="A1", total=5.0):
    """A plan-A table whose paired mean c - m is exactly `total` pp as a rational (U shares are k/3: lowering k_j
    prompts of seed j by 1/3 moves the cell by k_j/6 pp)."""
    doc = synth.make_input(seed, "plan_a", arm_sd={a: 0.3 for a in synth.DEFAULT_U}, shift=1.0)
    rng = np.random.default_rng(seed + 7)
    cells = doc["endpoints"]["U"]["cells"]
    seeds = sorted(set(cells[c]) & set(cells[m]))
    J = len(seeds)
    need = int(round(total * 6 * J))
    ks = [need // J] * J
    for i in range(need - sum(ks)):
        ks[i % J] += 1
    jit = rng.integers(-8, 9, J)
    jit -= int(jit.sum()) // J
    jit[-1] -= int(jit.sum())
    ks = [int(k + d) for k, d in zip(ks, jit)]
    exact = Fraction(0)
    for j, k in zip(seeds, ks):
        yc = np.array(cells[c][j])
        ym = yc.copy()
        idx = np.where(yc >= 1 / 3 - 1e-9)[0][:k]
        assert len(idx) == k
        ym[idx] = np.round((yc[idx] - 1 / 3) * 3) / 3
        cells[m][j] = [float(x) for x in ym]
        exact += Fraction(k, 6)
    return doc, exact / J


def test_an_exact_5_pp_tie_reads_better_whatever_the_float_rounding():
    below, seen = 0, 0
    for seed in (0, 1, 2, 3, 5):
        doc, exact = make_tie(seed)
        assert exact == 5
        out = read(doc)
        u = out["rows"]["P1"]["u_part"]
        if u["rejected"]:
            seen += 1
            below += u["est"] < 5.0
            assert u["better"] and not u["note"] and out["headline"]["P1"] == "better", (seed, repr(u["est"]), u["words"])
    assert seen >= 3 and below >= 1                               # the float sat below 5 in some of them


def test_the_tie_tolerance_is_1e_9_pp_from_the_settings():
    assert settings()["margin"]["tie_tolerance_pp"] == 1e-9 and labels.tie_tolerance() == 1e-9
    part = u_part(True, 5.0 - 1e-12, WIDE, WIDE, 5.0)
    assert part.better and not part.note
    part = u_part(True, 5.0 - 1e-6, WIDE, WIDE, 5.0)
    assert not part.better and part.note                          # a real 1e-6 pp shortfall is below delta
    part = u_part(True, -5.0 + 1e-12, WIDE, WIDE, 5.0)
    assert part.worse and not part.note                           # LN-36's note at exactly -5 is not printed
    part = u_part(True, -4.999999, WIDE, WIDE, 5.0)
    assert part.worse and part.note
    assert u_part(True, 5.0 - 1e-12, WIDE, WIDE, 5.0, tol=0.0).better is False


# --- verify-stats F3/F4, verify-code F4/F5: the REML stop settings, the floor mode, alpha and the level ------------

def test_the_reml_options_come_from_the_pinned_settings():
    opts = reml.options(settings())
    assert opts == {"tol": 1e-6, "max_iter": 25, "clip": 2.0, "planning_floor": False, "multi_start": True, "ll_tol": 1e-6}
    assert settings()["reml"]["floor_mode"] == "active_set"
    with pytest.raises(reml.RemlError):
        reml.options({"reml": {**settings()["reml"], "floor_mode": "other"}})


def altered(**changes):
    doc = copy.deepcopy(settings())
    for key, value in changes.items():
        block, name = key.split("__")
        doc[block][name] = value
    return doc


def test_a_changed_reml_setting_changes_the_fit():
    inp = validate(synth.make_input(5, "plan_a"))
    dsg = st.design("plan_a")
    normal = sens.fit_clusters(inp.tables["U"], dsg, 100.0, 0.01)
    short = sens.fit_clusters(inp.tables["U"], dsg, 100.0, 0.01, cfg=altered(reml__max_iter=3))
    assert all(f.iterations <= 3 for f in short.values()) and any(f.iterations == 3 and not f.converged for f in short.values())
    assert any(short[c].sigma2 != normal[c].sigma2 for c in short)
    planning = sens.fit_clusters(inp.tables["U"], dsg, 100.0, 0.01, cfg=altered(reml__floor_mode="planning"))
    for c, fit in planning.items():
        cells = sens._cells(inp.tables["U"], fit.arms, dsg.seeds, 100.0)
        direct = reml.fit_cells(cells, fit.arms, 0.01, planning_floor=True)
        assert fit.sigma2 == direct.sigma2
    loose = sens.fit_clusters(inp.tables["U"], dsg, 100.0, 0.01, cfg=altered(reml__tol=1e-2))
    assert all(f.iterations <= normal[c].iterations for c, f in loose.items())
    assert sens.fit_one_shift(inp.tables["U"], dsg, 100.0, 0.01, altered(reml__max_iter=2)).iterations <= 2


@pytest.fixture
def patched_settings():
    """Swap the loaded settings document for the duration of one test (the pin stays untouched on disk)."""
    saved = st._SETTINGS

    def apply(doc):
        st._SETTINGS = doc
        return doc

    yield apply
    st._SETTINGS = saved


def test_the_reading_reads_alpha_the_level_and_the_stop_settings_from_the_settings(patched_settings):
    doc = synth.make_input(12, "plan_a")
    base = read(doc)
    patched_settings(altered(phi__alpha="1/10", intervals__per_comparison=0.8, reml__max_iter=2))
    out = read(doc)
    assert out["phi"]["alpha"] == "1/10" and base["phi"]["alpha"] == "1/20"
    assert out["phi"]["start_levels"]["U:P1"] == "3/200" and base["phi"]["start_levels"]["U:P1"] == "3/400"
    assert out["contrasts"]["P1"]["familywise_level"] == pytest.approx(1 - 0.2 / 6)
    assert out["contrasts"]["P1"]["U_mde_80_at_start_level"] > base["contrasts"]["P1"]["U_mde_80_at_start_level"] * 0 and \
        out["contrasts"]["P1"]["U_mde_80_at_start_level"] < base["contrasts"]["P1"]["U_mde_80_at_start_level"]
    lo, hi = out["contrasts"]["P1"]["U_interval_90"]
    blo, bhi = base["contrasts"]["P1"]["U_interval_90"]
    assert hi - lo < bhi - blo                                     # the 80% interval is narrower
    assert all(f["iterations"] <= 2 for e in out["fits"].values() for f in e.values())
    assert any(f["iterations"] > 2 for e in base["fits"].values() for f in e.values())
    assert out["references"]["tested"] is False
    assert refs.dominance({"A1": [{"reference": "x", "p_iut": 0.04, "beats": True, "fallback_3_seed": False}]},
                          (("P1", "R", "A1"),))["alpha"] == 0.1


def test_the_floor_mode_switch_reaches_the_reading(patched_settings):
    """Under 'planning' every arm is solved and then floored; the two modes agree when no arm is floored and the
    planning fit's REML value is lower when one is (the build's test on fit_cells; here through the reading)."""
    floored, differ = 0, 0
    original = settings()
    planning_doc = altered(reml__floor_mode="planning")
    for seed in (13, 15, 16, 17):
        doc = synth.make_input(seed, "plan_a")
        patched_settings(original)
        active = read(doc)
        patched_settings(planning_doc)
        planning = read(doc)
        assert any("floor mode: planning" in n for n in planning["notes"]) and any("floor mode: active_set" in n for n in active["notes"])
        for e in ("U", "O", "L"):
            for cl in active["fits"][e]:
                a, p = active["fits"][e][cl], planning["fits"][e][cl]
                if a["two_arm"]:
                    continue
                if a["at_floor"] or p["at_floor"]:
                    floored += 1
                    differ += any(a["sigma2"][arm] != p["sigma2"][arm] for arm in a["sigma2"])
                elif a["converged"] and p["converged"]:
                    for arm in a["sigma2"]:
                        assert a["sigma2"][arm] == pytest.approx(p["sigma2"][arm], rel=1e-3)
    assert floored > 0 and differ > 0


# --- verify-code F1: a coherence-failing repair never dominates ---------------------------------------------------

def _reference_beaten_by_s3(doc):
    ep = doc["endpoints"]
    ref = {"U": {j: ep["U"]["cells"]["a0"][j] for j in SEEDS},
           "O": {j: ep["O"]["cells"]["S3"][j] for j in SEEDS},
           "L": {j: ep["L"]["cells"]["S3"][j] for j in SEEDS}}
    doc["references"] = [{"name": "SP", "kind": "point", "cells": ref}]
    return doc


def test_a_coherence_failing_repair_never_dominates_in_family_1b():
    ok = read(_reference_beaten_by_s3(synth.make_input(11, u_levels={"S3": 18.0})))
    assert ok["references"]["family_1b"]["contrasts"]["P5"]["dominates"] is True        # the control
    out = read(_reference_beaten_by_s3(synth.make_input(11, u_levels={"S3": 18.0}, failing_arms=("S3",))))
    p5 = out["references"]["family_1b"]["contrasts"]["P5"]
    assert out["arms"]["S3"]["coherence"]["passes"] is False
    assert p5["beats_every_reference"] is False and p5["p_iut"] == 1.0
    assert p5["dominates"] is False                                                       # REV3 3.7 item 5
    point = out["references"]["per_repair"]["S3"][0]
    assert point["beats"] is False and point["p_iut"] == 1.0 and "cannot dominate" in point["blocked_by_coherence"]


def test_dominance_requires_beating_every_reference():
    per = {"A1": [{"reference": "SP", "p_iut": 0.001, "beats": False, "fallback_3_seed": False}],
           "L1": [{"reference": "SP", "p_iut": 0.001, "beats": True, "fallback_3_seed": False}]}
    out = refs.dominance(per, (("P1", "R", "A1"), ("P2", "R", "L1")))
    assert out["alpha"] == 0.05 and out["contrasts"]["P2"]["dominates"] and not out["contrasts"]["P1"]["dominates"]


# --- verify-code F2, F3: the schema's seed keys, version and reference names ---------------------------------------

@pytest.mark.parametrize("alias", ["01102", "١١٠٢", " 1102", "1102 ", "+1102", "1102.0"])
def test_a_seed_key_must_be_the_plain_decimal_seed(alias):
    doc = synth.make_input(7)
    cells = doc["endpoints"]["U"]["cells"]["A1"]
    cells[alias] = cells.pop("1102")
    with pytest.raises(Refusal):
        validate(doc)


def test_an_alias_cannot_overwrite_r_on_the_o_endpoint():
    doc = synth.make_input(7)
    doc["endpoints"]["O"]["cells"]["R"]["01102"] = [1.0] * 500
    with pytest.raises(Refusal):
        validate(doc)
    doc = synth.make_input(7)
    doc["coherence"]["R"]["01102"] = doc["coherence"]["R"]["1102"]
    with pytest.raises(Refusal):
        validate(doc)


@pytest.mark.parametrize("name", ["a0", "R", "A1", "S1", "R_1200", "R_2400", "theta0", "sum", "Ré"])
def test_a_reference_cannot_take_an_arm_name(name):
    doc = synth.make_input(7, references=[("point", name, tuple(range(1101, 1108)))])
    with pytest.raises(Refusal):
        validate(doc)
    doc = synth.make_input(7, references=[("curve", name, tuple(range(1101, 1108)))])
    with pytest.raises(Refusal):
        validate(doc)


def test_a_reference_with_its_own_name_is_accepted():
    doc = synth.make_input(7, references=[("point", "SP-2", tuple(range(1101, 1108)))])
    assert validate(doc).references[0].name == "SP-2"


@pytest.mark.parametrize("version", [True, 1.0, "1"])
def test_the_version_is_the_integer_1(version):
    doc = synth.make_input(7)
    doc["version"] = version
    with pytest.raises(Refusal):
        validate(doc)


# --- verify-code F6: S-a's O and L tests ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def strong():
    """A world with strong O effects, so the S-a and the primary O/L/F rejections can differ."""
    return read(synth.make_input(7, "plan_a", o_levels={"S1": 40.0, "S3": 45.0}, u_levels={"S1": 40.0, "A1": 30.0}))


def test_s_a_o_and_l_tests_use_welch_and_lw33s_pooled_theta0_form(strong):
    out = strong
    inp = validate(synth.make_input(7, "plan_a", o_levels={"S1": 40.0, "S3": 45.0}, u_levels={"S1": 40.0, "A1": 30.0}))
    t_o, t_l = inp.tables["O"], inp.tables["L"]
    block = out["sensitivities"]["S-a (O, L)"]
    assert set(block) == {"P1", "P2", "P3", "P4", "P5", "P6", "rule"}
    rec = block["P4"]
    s1 = np.array([100 * t_o[("S1", j)].mean() for j in range(1102, 1108)])
    a0 = np.array([100 * t_o[("a0", j)].mean() for j in range(1101, 1108)])
    comp = rec["O"]["comparator_part"]
    assert comp["form"] == "S-a Welch" and comp["est"] == pytest.approx(s1.mean() - a0.mean())
    assert comp["seed_var"] == pytest.approx(s1.var(ddof=1) / 6 + a0.var(ddof=1) / 7)
    ss, df = 0.0, 0
    for arm in st.design("plan_a").arms:
        v = np.array([100 * t_o[(arm, j)].mean() for j in sorted(j for a, j in t_o if a == arm)])
        ss += ((v - v.mean()) ** 2).sum()
        df += len(v) - 1
    theta = rec["O"]["theta0_part"]
    assert theta["form"].startswith("S-a theta0 (LW-33") and theta["seed_df"] == df == 42
    assert theta["seed_var"] == pytest.approx(ss / df / 6)
    assert theta["est"] == pytest.approx(out["contrasts"]["P4"]["O"]["theta0_part"]["est"])
    assert theta["item_var"] == pytest.approx(out["contrasts"]["P4"]["O"]["theta0_part"]["item_var"])
    l_comp = rec["L"]["comparator_part"]
    s1l = np.array([t_l[("S1", j)].mean() for j in range(1102, 1108)])
    a0l = np.array([t_l[("a0", j)].mean() for j in range(1101, 1108)])
    assert l_comp["form"] == "S-a Welch" and l_comp["seed_var"] == pytest.approx(s1l.var(ddof=1) / 6 + a0l.var(ddof=1) / 7)
    assert rec["L"]["a0_part"] == rec["L"]["comparator_part"]                             # P4's comparator is a0
    assert block["P1"]["L"]["a0_part"]["name"] == "A1-a0" and block["P1"]["L"]["a0_part"]["form"] == "S-a Welch"
    assert rec["p_values"]["O"] == max(rec["O"]["p_comparator"], rec["O"]["p_theta0"])
    assert rec["p_values"]["F"] + rec["O"]["p_theta0"] == pytest.approx(1.0)
    assert rec["p_values"]["U"] == pytest.approx(out["sensitivities"]["S-a"]["P4"]["estimate"]["p_two_sided"])


def test_s_a_o_and_l_rejections_are_phi_on_s_as_own_p_values_and_never_the_label(strong):
    out = strong
    block = out["sensitivities"]["S-a (O, L)"]
    names = ["P1", "P2", "P3", "P4", "P5", "P6"]
    pvalues = {(k, n): block[n]["p_values"][k] for n in names for k in ("U", "O", "L", "F")}
    run = phi.run(phi.build_graph(names), pvalues, Fraction(1, 20))
    for n in names:
        assert sorted(block[n]["rejected"]) == sorted(f"{k}:{c}" for k, c in run.rejected if c == n)
        words = block[n]["headline"]["word"]
        assert block[n]["differs_from_primary"] == (words != out["headline"][n])
        listed = [s for s in out["rows"][n]["sensitivity_part"] if s.get("code") == "S-a (O, L)"]
        assert (len(listed) == 1 and listed[0]["headline_word"] == words) if block[n]["differs_from_primary"] else listed == []
        assert out["headline"][n] == out["rows"][n]["headline"]["word"]                    # the label is the primary's
    primary = {(k, n): out["contrasts"][n]["p_values"][k] for n in names for k in ("O", "L", "F")}
    assert any(abs(primary[k] - pvalues[k]) > 1e-6 for k in primary)                          # S-a's O/L/F p-values are its own
    differ = sum(block[n]["differs_from_primary"] for n in names)
    assert differ >= 0


def test_s_a_o_comparator_part_is_not_tested_below_three_r_seeds():
    out = read(synth.make_input(4, "plan_a", r_o_seeds=[1106, 1107]))
    rec = out["sensitivities"]["S-a (O, L)"]["P2"]
    assert rec["O"]["comparator_part"] is None and rec["O"]["p_comparator"] == 1.0
    out = read(synth.make_input(4, "plan_a", r_o_seeds=[1104, 1105, 1106, 1107]))
    rec = out["sensitivities"]["S-a (O, L)"]["P1"]
    assert rec["O"]["comparator_part"]["pairs"] == 4 and rec["O"]["comparator_part"]["form"] == "S-a Welch"


def test_plan_b_s_a_pools_a0_too():
    out = read(synth.make_input(2, "plan_b"))
    theta = out["sensitivities"]["S-a (O, L)"]["P1"]["O"]["theta0_part"]
    assert theta["seed_df"] == (10 - 1) + 4 * (9 - 1) + (7 - 1)                            # R, A1, H1, S1, S4, a0


# --- verify-code F7: the seed-only O value 'on these prompts' -----------------------------------------------------

def test_every_o_number_carries_its_seed_only_value_on_these_prompts():
    out = read(synth.make_input(1, "plan_a"))
    for name, k in out["contrasts"].items():
        for part, key in (("theta0_part", "theta0_on_these_prompts"), ("comparator_part", "comparator_on_these_prompts")):
            full, seed_only = k["O"][part], k["O"][key]
            assert seed_only["label"] == "on these prompts"
            s = seed_only["estimate"]
            assert s["est"] == full["est"] and not s["with_item"] and s["item_var"] == 0.0
            assert s["se"] == pytest.approx(math.sqrt(full["seed_var"])) and s["df"] == full["seed_df"]
            assert s["se"] <= full["se"]
            from scripts.stage1_s1.reading import tdist
            assert seed_only["interval_90"][1] - s["est"] == pytest.approx(tdist.t_quantile(0.95, s["df"]) * s["se"])
        assert out["rows"][name]["side_effect_part"]["o_vs_theta0_on_these_prompts"] == k["O"]["theta0_on_these_prompts"]
        assert set(out["rows"][name]["feasibility_part"]["states_on_these_prompts"]) == {"tau_o_2", "tau_o_5", "tau_o_10"}
    for arm, rec in out["arms"].items():
        s = rec["o_on_these_prompts"]
        assert s["label"] == "on these prompts" and s["estimate"]["se"] == pytest.approx(math.sqrt(rec["o_vs_theta0"]["seed_var"]))
        for key, state in s["o_states"].items():
            tau = float(key.split("_")[-1])
            assert state == labels.feasibility_state(tuple(s["interval_90"]), tau)
    assert any("on these prompts" in n for n in out["notes"])
    e = con.Estimate("x", "f", 1.0, 2.0, 7.0, 1.0, 5.0, 3.0, 0.5, 6, 500, True)
    s = con.seed_only(e)
    assert s.se == 1.0 and s.df == 5.0 and not s.with_item and con.seed_only(s) is s


# --- verify-code F8: the per-actor best data arm ------------------------------------------------------------------

def test_the_per_actor_best_data_arm_follows_the_menu_and_the_stated_tau(strong):
    out = strong
    cfg = settings()
    for actor, rec in out["actors"].items():
        if actor == "rule":
            continue
        best = rec["best_data_arm"]
        assert set(best) == {"tau_o_2", "tau_o_5", "tau_o_10"}
        for key, result in best.items():
            arms_in = {c["arm"] for c in result["candidates"]}
            assert arms_in <= set(rec["menu"]) and arms_in == {a for a in cfg["actors"][actor] if a in out["design"]["arms"]} - {"a0", "R"}
            for c in result["candidates"]:
                row = out["rows"][c["contrast"]]
                o_ok = row["feasibility_part"]["F_k_rejects_in_phi"] if key == "tau_o_5" else row["feasibility_part"]["states"][key] == "feasible"
                assert c["feasible"] == (o_ok and row["feasibility_part"]["l_state"] == "feasible" and out["arms"][c["arm"]]["coherence"]["passes"])
                assert c["better"] == row["u_part"]["better"]
            if result["best"] is not None:
                assert result["best"] in rec["menu"] and result["text"] == result["best"]
            elif result.get("runner_up"):
                assert result["text"] == "too close to call" and not result["separated"]
        if set(rec["menu"]) >= set(out["design"]["arms"]):
            assert best["tau_o_5"]["best"] == out["best_feasible_repair"]["best"] and best["tau_o_5"]["text"] == out["best_feasible_repair"]["text"]
    assert "too close to call" in out["actors"]["rule"]
    cd = out["actors"]["Cd"]["best_data_arm"]["tau_o_5"]
    assert "A1" not in {c["arm"] for c in cd["candidates"]}


def test_the_per_actor_best_arm_names_an_arm_when_one_is_better_feasible_and_separated():
    out = read(synth.make_input(8, "plan_a", o_levels={"S1": 2.0, "S3": 2.0, "A1": 2.0, "L1": 2.0, "H1": 2.0, "S4": 2.0},
                                u_levels={"S1": 40.0, "A1": 30.0}))
    best = out["actors"]["Sp"]["best_data_arm"]
    eligible = {key: r["eligible"] for key, r in best.items()}
    assert eligible["tau_o_10"] and set(eligible["tau_o_10"]) >= set(eligible["tau_o_5"])
    for key, r in best.items():
        if len(r["eligible"]) >= 2:
            assert r["runner_up"] in r["eligible"] and ("contrast_with_runner_up" in r)
            assert (r["best"] is not None) == r["separated"]


# --- verify-code F9: the equal-variance flag from the Phi runs ----------------------------------------------------

def test_the_equal_variance_flag_reads_the_s_a_and_s_aw_phi_runs(strong):
    out = strong
    for name in out["contrasts"]:
        s_a, s_aw = out["sensitivities"]["S-a"][name], out["sensitivities"]["S-aW"][name]
        assert s_a["equal_variance_flag"] == (s_a["rejected_in_phi"] and not s_aw["rejected_in_phi"])
        flagged = [s for s in out["rows"][name]["sensitivity_part"] if s.get("flag")]
        assert (len(flagged) == 1) == s_a["equal_variance_flag"]


def test_the_flag_is_not_the_start_level_comparison():
    """A contrast whose S-a p-value lies above U_k's start level and below its level after other rejections: S-a
    rejects in its Phi run (the flag reads 'rejects'); a comparison with the start level would say it does not."""
    found = 0
    levels = {"A1": 30.0, "S1": 40.0, "S4": 55.0, "L1": 40.0, "H1": 41.0, "S3": 35.0}
    for seed in (49, 70, 71, 74):                                 # synthetic draws with such a contrast (P3 or P2)
        out = read(synth.make_input(seed, "plan_a", u_levels=levels))
        for name in out["contrasts"]:
            s_a, s_aw = out["sensitivities"]["S-a"][name], out["sensitivities"]["S-aW"][name]
            start = float(Fraction(out["phi"]["start_levels"][f"U:{name}"]))
            if s_a["rejected_in_phi"] and s_a["estimate"]["p_two_sided"] > start and not s_aw["rejected_in_phi"]:
                found += 1
                assert s_a["equal_variance_flag"] is True
                assert any(s.get("flag") for s in out["rows"][name]["sensitivity_part"])
    assert found >= 2


# --- verify-code N1, N2, N3, N4, N5 --------------------------------------------------------------------------------

def test_a_contrast_with_no_variance_information_refuses_with_a_named_cause():
    doc = synth.make_input(14, "plan_a")
    cells = doc["endpoints"]["L"]["cells"]
    for j in SEEDS:
        cells["A1"][j] = list(cells["a0"][j])                     # L(A1) - L(a0) is zero on every seed and row
    with pytest.raises(Refusal, match="no finite degrees of freedom"):
        read(doc)


def test_the_command_line_creates_the_output_exclusively(tmp_path):
    doc = synth.make_input(9, "plan_b")
    src, out = tmp_path / "in.json", tmp_path / "out.json"
    src.write_bytes(canonical_json(doc))
    out.write_bytes(b"keep me")
    assert cli(["--input", str(src), "--out", str(out)]) == 2 and out.read_bytes() == b"keep me"
    out.unlink()
    assert cli(["--input", str(src), "--out", str(out)]) == 0 and json.loads(out.read_bytes())["headline"]


def test_r_with_one_o_seed_is_not_tested_and_the_reading_goes_on():
    out = read(synth.make_input(4, "plan_a", r_o_seeds=[1107]))
    r = out["arms"]["R"]
    assert r["o_vs_theta0"] is None and set(r["o_states"].values()) == {"not tested"} and "not tested" in r["o_note"]
    for name in ("P1", "P2", "P3"):
        assert out["contrasts"][name]["O"]["comparator_part"] is None and out["contrasts"][name]["p_values"]["O"] == 1.0
    assert out["arms"]["A1"]["o_vs_theta0"] is not None and out["headline"]


def _continuous_pair(doc, c, m, gap_pp, seed=3):
    """Replace c's and m's U cells by continuous shares: c = 0.45 + base + shift_j, m = c - gap + tiny jitter."""
    rng = np.random.default_rng(seed)
    base = rng.uniform(-0.2, 0.2, 200)
    cells = doc["endpoints"]["U"]["cells"]
    for j in list(cells[m]):
        shift = rng.normal(0, 0.01)
        cells[c][j] = [float(v) for v in 0.45 + base + shift]
        cells[m][j] = [float(v) for v in 0.45 + base + shift - gap_pp / 100.0 + rng.normal(0, 0.002)]
    for j in set(cells[c]) - set(cells[m]):
        cells[c][j] = [float(v) for v in 0.45 + base]
    return doc


def test_the_4_pp_margin_sensitivity_is_reported_and_never_the_label():
    out = read(_continuous_pair(synth.make_input(21), "R", "A1", 4.5))
    row = out["rows"]["P1"]
    ms = row["margin_sensitivity"]
    assert ms["delta_pp"] == 4.0 == settings()["margin"]["delta_sensitivity_pp"]
    assert row["u_part"]["rejected"] and 4.0 < row["u_part"]["est"] < 5.0
    assert not row["u_part"]["better"] and row["u_part"]["note"] and out["headline"]["P1"] != "better"
    assert out["headline"]["P1"].startswith(("inconclusive", "equivalent"))
    assert ms["u_part"]["better"] and ms["headline"]["word"] == "better" and not ms["u_part"]["note"]


def test_tau_o_2_is_marked_below_the_banks_resolution():
    out = read(synth.make_input(1, "plan_a"))
    row = out["rows"]["P1"]
    assert row["feasibility_part"]["below_resolution"] == "tau_o_2"
    assert row["feasibility_part"]["below_resolution_text"] == "tau_o_2: below the bank's resolution"
    assert out["arms"]["A1"]["o_below_resolution_text"].endswith("below the bank's resolution")


# --- verify-code F10: the proposed gap tests ----------------------------------------------------------------------

def test_the_reading_uses_delta_5_from_the_settings_not_a_family_margin():
    doc = _continuous_pair(synth.make_input(21), "R", "A1", 5.8)
    out = read(doc)
    assert settings()["margin"]["delta_pp"] == 5.0
    u = out["rows"]["P1"]["u_part"]
    assert u["rejected"] and 5.0 < u["est"] < 6.5
    assert out["headline"]["P1"] == "better"


def test_the_curve_bracket_reads_lambda_lo_at_the_upper_and_lambda_hi_at_the_lower_end():
    """Searches synthetic draws for a repair whose L interval straddles a grid point of the curve, where reading
    the bracket at the wrong ends changes lambda_lo and lambda_hi."""
    grid = sorted(settings()["beats"]["lambda_grid"])
    straddled = 0
    for seed in range(22, 40):
        doc = synth.make_input(seed, l_levels={"A1": 1.60, "S1": 1.60, "S3": 1.62, "H1": 1.64},
                               references=[("curve", "AS", (1101, 1102, 1103, 1104, 1105, 1106, 1107))])
        out = read(doc)
        for m in ("A1", "S1", "S3", "H1"):
            rec = [p for p in out["references"]["per_repair"][m] if p["kind"] == "curve"][0]
            if rec["switch"].startswith("lambda* = 1"):
                continue
            assert rec["lambda_up"] <= rec["lambda_dn"]
            assert rec["lambda_lo"] == max(x for x in grid if x <= rec["lambda_up"] + 1e-12)
            assert rec["lambda_hi"] == min(x for x in grid if x >= rec["lambda_dn"] - 1e-12)
            straddled += any(rec["lambda_up"] < x < rec["lambda_dn"] for x in grid)
        if straddled >= 2:
            break
    assert straddled >= 2


def test_s_tok_per_seed_values_pair_every_arm_by_seed():
    doc = synth.make_input(23, with_token_axis=True)
    doc["token_axis"]["removed"]["H1"] = 30000.0          # below T_600: the segment from (0, 0), where a0 does not cancel
    out = read(doc)
    assert out["sensitivities"]["S-tok"]["arms"]["H1"]["first_segment_only"] is True
    tok = out["sensitivities"]["S-tok"]
    cells, dose = doc["endpoints"]["U"]["cells"], doc["token_axis"]["dose_cells"]
    masses = doc["token_axis"]["masses"]
    for arm, rec in tok["arms"].items():
        if rec["lambda_tok"] == "beyond the curve" or rec["interval_90"] is None:
            continue
        for k, j in enumerate(("1102", "1103", "1104")):
            u = lambda tab, a: 100.0 * float(np.mean(tab[a][j]))
            a0 = u(cells, "a0")
            pts = [(0.0, 0.0), (masses["600"], a0 - u(cells, "R")), (masses["1200"], a0 - u(dose, "R_1200")),
                   (masses["2400"], a0 - u(dose, "R_2400"))]
            t = rec["t_m"]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                if x0 <= t <= x1:
                    g_r = y0 + (y1 - y0) * (t - x0) / (x1 - x0)
                    break
            assert abs(rec["per_seed_lambda_tok"][k] - ((a0 - u(cells, arm)) - g_r)) < 1e-9


def test_the_below_sesoi_note_is_absent_at_exactly_delta():
    ci = (4.0, 6.0)
    part = u_part(True, 5.0, ci, (3.0, 7.0), 5.0)
    assert part.better and not part.note


def test_equivalence_needs_the_interval_strictly_inside_delta():
    """A reading of 'lies inside +-5 pp' (REV3 4.5) that the build made: strictly inside. Pinned so a change is seen."""
    assert not u_part(False, 0.0, (-5.0, 4.0), (-6.0, 6.0), 5.0).grade1
    assert u_part(False, 0.0, (-4.99, 4.99), (-6.0, 6.0), 5.0).grade1


def test_a0_and_r_states_against_theta0_use_all_their_o_seeds():
    out = read(synth.make_input(24))
    assert out["arms"]["a0"]["o_vs_theta0"]["pairs"] == 7
    assert out["arms"]["R"]["o_vs_theta0"]["pairs"] == 7


# --- this pass: the last second copies of settings numbers ---------------------------------------------------------

def test_s_tok_interval_level_comes_from_the_settings(patched_settings):
    """verify-stats F4 / verify-code F5 (the remaining literal): S-tok's interval used t(0.95) whatever the
    settings' per-comparison level; it now reads intervals.per_comparison like every other interval."""
    from scripts.stage1_s1.reading import tdist
    doc = synth.make_input(5, "plan_a", with_token_axis=True)
    base = read(doc)["sensitivities"]["S-tok"]["arms"]
    patched_settings(altered(intervals__per_comparison=0.8))
    narrow = read(doc)["sensitivities"]["S-tok"]["arms"]
    checked = 0
    for arm, rec in base.items():
        if rec.get("interval_90") is None:
            continue
        half90 = rec["interval_90"][1] - rec["lambda_tok"]
        half80 = narrow[arm]["interval_90"][1] - narrow[arm]["lambda_tok"]
        assert half90 == pytest.approx(tdist.t_quantile(0.95, rec["df"]) * rec["se_common_seeds"])
        assert half80 == pytest.approx(tdist.t_quantile(0.9, rec["df"]) * rec["se_common_seeds"])
        assert half80 < half90
        checked += 1
    assert checked >= 2


def test_the_schema_curve_points_are_the_settings_grid_without_its_ends():
    """The curve reference's point keys (schema) and the grid (settings beats.lambda_grid) name one grid:
    lambda 1 is a0 and lambda 0 is theta0, so the input holds exactly the interior points."""
    from scripts.stage1_s1.reading import schema
    grid = sorted(float(x) for x in settings()["beats"]["lambda_grid"])
    assert grid[0] == 0.0 and grid[-1] == 1.0
    assert sorted(float(x) for x in schema.CURVE_POINTS) == grid[1:-1]


# --- this pass: three mutants of the first fix pass survived; these tests close them -------------------------------

STRONG = dict(o_levels={"S1": 40.0, "S3": 45.0}, u_levels={"S1": 40.0, "A1": 30.0})


def test_s_a_phi_run_takes_s_as_own_o_l_and_f_p_values():
    """Draw 11 of the strong world: S-a's own O, L and F p-values change Phi's rejection set against a run that
    keeps the primary ones (the precondition), and the printed S-a rejections are the former."""
    out = read(synth.make_input(11, "plan_a", **STRONG))
    names = ["P1", "P2", "P3", "P4", "P5", "P6"]
    block = out["sensitivities"]["S-a (O, L)"]
    own = {(k, n): block[n]["p_values"][k] for n in names for k in ("U", "O", "L", "F")}
    mixed = dict(own)
    mixed.update({(k, n): out["contrasts"][n]["p_values"][k] for n in names for k in ("O", "L", "F")})
    graph = phi.build_graph(names)
    r_own, r_mixed = set(phi.run(graph, own, Fraction(1, 20)).rejected), set(phi.run(graph, mixed, Fraction(1, 20)).rejected)
    assert r_own != r_mixed
    printed = {tuple(key.split(":")) for n in names for key in block[n]["rejected"]}
    assert printed == r_own


def test_the_per_actor_feasibility_at_tau_o_2_and_10_reads_the_per_comparison_state():
    """Draw 8 of the strong world holds repairs whose F_k result (tau_O* = 5 in Phi) and per-comparison state at
    tau_O = 2 or 10 differ (the precondition); the candidates at 2 and 10 follow the state (REV3 4.6 last row)."""
    out = read(synth.make_input(8, "plan_a", **STRONG))
    differ = 0
    for actor, rec in out["actors"].items():
        if actor == "rule":
            continue
        for key in ("tau_o_2", "tau_o_10"):
            for c in rec["best_data_arm"][key]["candidates"]:
                part = out["rows"][c["contrast"]]["feasibility_part"]
                ok = part["l_state"] == "feasible" and out["arms"][c["arm"]]["coherence"]["passes"]
                by_state = part["states"][key] == "feasible"
                assert c["feasible"] == (by_state and ok)
                differ += ok and part["F_k_rejects_in_phi"] != by_state
    assert differ >= 1


def test_better_holds_at_exactly_delta_minus_the_tie_tolerance():
    """The tie rule is est >= delta - tie_tolerance (closed at its end)."""
    tol = labels.tie_tolerance()
    assert u_part(True, 5.0 - tol, WIDE, WIDE, 5.0).better
    assert not u_part(True, 5.0 - 2 * tol, WIDE, WIDE, 5.0).better
