"""Section 9.4's overlap control: HB-C of the halves with S-p beside it (REV4 9.4; addendum 11 point 11, 24 point 4,
32 point 4, 33; LN-26, LN-35, LN-37; D-4). Synthetic data only. Checks: the pinned rule text and readings; the
governing contrasts (a0 - m, addendum 33 point 1) and the report-only primary orientation; all prompts equal the
primary reading's numbers; agreement with an independent reference (halves_reference.py, no B16 fit or contrast
code); S-p equal to B14's printed S-p; hand cases under plan B; every branch of the "holds" rule; the halves bound to
B14's strata and report by SHA-256 and B14's split rule (addendum 33 point 3), both ways; an empty and a one-prompt
lower half; the block-A-only suffix; report only; a small seeded simulation of the lower half's interval coverage and
of the false "holds" rate."""

from __future__ import annotations

import copy
import math
from fractions import Fraction as F

import numpy as np
import pytest

import halves_reference as ref
import halves_synth as hs
import synth
from scripts.stage1_s1 import overlap_strata as b14
from scripts.stage1_s1.reading import overlap
from scripts.stage1_s1.reading.reading import read
from scripts.stage1_s1.reading.schema import b14_sha256, validate
from scripts.stage1_s1.reading.settings import Refusal, design, settings

RULE_94 = ("Each evaluation prompt's highest similarity to the add set (theta0 embeddings). \"Holds\" = the add contrast "
           "on the lower-similarity half has the same sign as on all prompts and its 90% interval excludes 0; else the "
           "text says \"not shown on the less similar half\".")
NOT_SHOWN, HOLDS = "not shown on the less similar half", "holds on the less similar half"
BLOCK_A = " [block A only (3 seeds per method arm)]"
EFFECT_LOWER = {"S1": 6.0, "S3": 9.0, "S4": 4.0}
EFFECT_HIGHER = {"S1": 10.0, "S3": 14.0, "S4": 8.0}
GOV = {"plan_a": ["a0-S1", "a0-S3", "a0-S4"], "plan_a_block_a_only": ["a0-S1", "a0-S3", "a0-S4"], "plan_b": ["a0-S1", "a0-S4"]}


def doc_with_halves(seed: int, reading: str, eff_lower=None, eff_higher=None, tie_block=0, shared=True, sims=None):
    """A synthetic input whose full-corpus U cells follow the halves world, with the overlap block built from B14's
    own strata and a B14-format report. ``shared``: one similarity for every add set, else one per add set."""
    rng = np.random.default_rng(1000 + seed)
    doc = synth.make_input(seed, reading)
    dsg = design(reading)
    if sims is None:
        sims = {m: hs.similarity(rng, tie_block=tie_block) for m in ("S1", "S3", "S4")}
        if shared:
            sims = {m: sims["S1"] for m in sims}
    mask = np.zeros(200, bool)
    mask[hs.positions(b14.split_halves(sims["S1"])["lower"])] = True
    arms = tuple(a for a in hs.FULL if a in dsg.arms)
    cells = hs.world_cells(rng, dsg, mask, eff_lower or EFFECT_LOWER, eff_higher or EFFECT_HIGHER, arms=arms)
    hs.with_world(doc, cells)
    doc["overlap"] = hs.overlap_block(doc, sims)
    return doc


@pytest.fixture(scope="module")
def plan_a_out():
    doc = doc_with_halves(1, "plan_a", shared=False)
    return doc, read(doc)


# ----- the rule, the readings, the contrasts ------------------------------------------------------------------------


def test_the_settings_hold_section_9_4s_text_and_the_readings():
    o = settings()["overlap"]
    assert o["rule"] == "REV4 9.4 (LN-26, adopted as written; W1 text): " + RULE_94
    assert o["interval"] == 0.9 and o["texts"] == {"holds": HOLDS, "not_shown": NOT_SHOWN}
    assert o["comparator"] == "a0" and o["report_only"] == "primary" and "addendum 33 point 1" in o["comparator_rule"]
    assert o["min_prompts"] == 2 and o["s_p_label"] == "S-p sensitivity"
    assert o["sign_tolerance_pp"] == 1e-9 and o["check_tolerance_pp"] == 1e-9
    assert o["seed_plans"] == {"plan_a": "d1_plan_a", "plan_a_block_a_only": "block_a_only", "plan_b": "plan_b"}
    assert "10-23%" in o["stop_rates"] and "6-13%" in o["stop_rates"] and "about 9%" in o["stop_rates"]
    assert "HB-C" in o["model"] and "LN-35" in o["model"] and "D-4" in o["model"] and "LN-37" in o["s_p"]


def test_the_governing_and_report_only_contrasts_per_reading():
    cfg = settings()
    a, b = design("plan_a"), design("plan_b")
    assert overlap.contrasts(a, cfg) == (("a0-S1", "a0", "S1"), ("a0-S3", "a0", "S3"), ("a0-S4", "a0", "S4"))
    assert overlap.contrasts(design("plan_a_block_a_only"), cfg) == overlap.contrasts(a, cfg)
    assert overlap.contrasts(b, cfg) == (("a0-S1", "a0", "S1"), ("a0-S4", "a0", "S4"))
    assert overlap.contrasts(a, cfg, "primary") == (("P4", "a0", "S1"), ("P5", "S1", "S3"), ("P6", "S1", "S4"))
    assert overlap.contrasts(b, cfg, "primary") == (("P6", "S1", "S4"),)
    with pytest.raises(Refusal):
        overlap.contrasts(a, cfg, "R")


def test_plan_a_output_structure(plan_a_out):
    _, out = plan_a_out
    oc = out["overlap_control"]
    assert oc["computed"] and oc["rule"].endswith(RULE_94) and oc["comparator"] == "a0" and oc["interval"] == 0.9
    assert list(oc["contrasts"]) == GOV["plan_a"] and list(oc["report_only_contrasts"]) == ["P4", "P5", "P6"]
    assert oc["add_sets_in_no_contrast"] == [] and oc["label_suffix"] is None
    assert set(oc["fits"]) == {"all", "S1 lower", "S1 higher", "S3 lower", "S3 higher", "S4 lower", "S4 higher"}
    for name, k in oc["contrasts"].items():
        assert k["role"].startswith("governing") and k["comparator"] == "a0" and k["add_set"] == k["repair"]
        assert k["common_seeds"] == list(range(1102, 1108))
        assert sum(k["half_sizes"][h] for h in ("lower", "higher")) == 200 == k["half_sizes"]["all"]
        assert k["verdict"]["model"] == "HB-C" and k["s_p_verdict"]["role"] == "S-p sensitivity"
        assert k["verdict"]["text"] in (HOLDS, NOT_SHOWN)
        assert k["s_p_differs"] == (k["verdict"]["holds"] != k["s_p_verdict"]["holds"])
        assert k["prereg_start_differs"] == (k["verdict"]["holds"] != k["prereg_start_verdict"]["holds"])
        assert k["verdict"]["fits_converged"] == (oc["fits"]["all"]["full"]["converged"]
                                                  and oc["fits"][f"{k['repair']} lower"]["full"]["converged"])
        for h in ("all", "lower", "higher"):
            assert k["halves"][h]["HB-C"]["estimate"]["form"] == "HB-C"
            assert k["halves"][h]["S-p"]["estimate"]["form"] == "S-p paired t"
            assert k["halves"][h]["HB-C"]["estimate"]["est"] == pytest.approx(k["halves"][h]["paired_mean_pp"], abs=1e-12)
    for name, k in oc["report_only_contrasts"].items():
        assert k["role"].startswith("report only")
    p4, g1 = oc["report_only_contrasts"]["P4"], oc["contrasts"]["a0-S1"]
    assert p4["same_contrast_as"] == "a0-S1" and oc["report_only_contrasts"]["P5"]["same_contrast_as"] is None
    for h in ("all", "lower", "higher"):
        for form in ("HB-C", "S-p"):
            a, b = p4["halves"][h][form], g1["halves"][h][form]
            assert a["interval_90"] == b["interval_90"] and {k: v for k, v in a["estimate"].items() if k != "name"} == \
                {k: v for k, v in b["estimate"].items() if k != "name"}
    assert p4["verdict"] == g1["verdict"]
    assert oc["fits"]["S3 lower"]["full"]["arms"] == ["a0", "S1", "S3", "S4"] and oc["fits"]["S3 lower"]["full"]["starts"] == 16


@pytest.mark.parametrize("reading", ["plan_a", "plan_a_block_a_only", "plan_b"])
def test_on_all_prompts_the_halves_equal_the_primary_reading(reading):
    """a0 - m on all prompts is the reading's restoration G_m (its HB-C form); the report-only P_k on all prompts is
    the primary U contrast; S-p on all prompts is the S-p sensitivity's."""
    out = read(doc_with_halves(2, reading))
    oc = out["overlap_control"]
    for name, k in oc["contrasts"].items():
        g = out["arms"][k["repair"]]
        for key in ("est", "se", "df", "seed_var", "seed_df", "item_var", "item_q"):
            assert k["halves"]["all"]["HB-C"]["estimate"][key] == g["restoration_G"][key], (name, key)
        assert k["halves"]["all"]["HB-C"]["interval_90"] == g["restoration_interval_90"]
    for name, k in oc["report_only_contrasts"].items():
        a, p = k["halves"]["all"]["HB-C"], out["contrasts"][name]
        for key in ("est", "se", "df", "seed_var", "seed_df", "item_var", "item_q"):
            assert a["estimate"][key] == p["U"][key], (name, key)
        assert a["interval_90"] == p["U_interval_90"]
        s = out["sensitivities"]["S-p"][name]
        assert k["halves"]["all"]["S-p"]["interval_90"] == s["interval_90"]
    rec = oc["fits"]["all"]["full"]
    assert rec == {key: out["fits"]["U"]["full"][key] for key in rec}


# ----- the independent reference ---------------------------------------------------------------------------------------


def test_hbc_of_the_halves_agrees_with_the_independent_reference():
    """Every governing and report-only contrast x half on 16 seeded inputs (plan A and block A only), where B16's fit
    met its tolerance. (1) Started at B16's governing sigma^2, the reference's own optimizer stays there (to 1e-5
    relative): B16's point is a constrained REML maximum on the half; at that point the reference's estimate (1e-9 pp),
    SE and df (1e-5 relative), interval ends (1e-4 pp) and verdict agree, and S-p agrees to 1e-9 pp. (2) Started by
    REV4 3.2's start rule (computed by the reference), it reaches B16's pre-registered start's own end point in at
    least 90% of the fits."""
    compared, floored, same_from_rule = 0, 0, 0
    for seed in range(16):
        reading = "plan_a" if seed % 4 else "plan_a_block_a_only"
        doc = doc_with_halves(10 + seed, reading, shared=seed % 2 == 0)
        out = read(doc)["overlap_control"]
        inp = validate(doc)
        dsg = design(reading)
        cluster = list(dsg.cluster_arms("full"))
        for name, k in list(out["contrasts"].items()) + list(out["report_only_contrasts"].items()):
            idx_of = {"all": np.arange(200), "lower": inp.overlap["add_sets"][k["repair"]]["lower"],
                      "higher": inp.overlap["add_sets"][k["repair"]]["higher"]}
            r_half = {}
            for h, idx in idx_of.items():
                fit = out["fits"]["all" if h == "all" else f"{k['repair']} {h}"]["full"]
                b = k["halves"][h]["HB-C"]
                args = (inp.tables["U"], cluster, dsg.seeds, k["comparator"], k["repair"], idx, 0.01)
                r = ref.contrast_reference(*args, "cluster", start=fit["sigma2"])
                r_half[h] = r
                assert b["estimate"]["est"] == pytest.approx(r["est"], abs=1e-9)
                s = ref.contrast_reference(*args, "paired")
                assert k["halves"][h]["S-p"]["interval_90"] == pytest.approx([s["lower"], s["upper"]], abs=1e-9)
                if not fit["converged"]:
                    continue
                compared += 1
                floored += bool(fit["at_floor"])
                for arm in cluster:
                    assert fit["sigma2"][arm] == pytest.approx(r["sigma2"][arm], rel=1e-5, abs=1e-7), (seed, name, h, arm)
                assert b["estimate"]["se"] == pytest.approx(r["se"], rel=1e-5)
                assert b["estimate"]["df"] == pytest.approx(r["df"], rel=1e-5)
                assert b["interval_90"][0] == pytest.approx(r["lower"], abs=1e-4)
                assert b["interval_90"][1] == pytest.approx(r["upper"], abs=1e-4)
                rule = ref.contrast_reference(*args, "cluster")
                pre = fit["prereg_start"]["sigma2"]
                if all(rule["sigma2"][a] == pytest.approx(pre[a], rel=1e-4, abs=1e-6) for a in cluster):
                    same_from_rule += 1
            if all(out["fits"][key]["full"]["converged"] for key in ("all", f"{k['repair']} lower")):
                assert k["verdict"]["holds"] == ref.verdict_reference(r_half["all"]["est"], r_half["lower"])
    assert compared >= 150 and floored >= 20 and same_from_rule >= 0.9 * compared, (compared, floored, same_from_rule)


def test_s_p_is_b14s_printed_s_p_for_the_governing_contrasts():
    """B14's report (built by B14's own contrast(): exact fractions, its own t) prints a0 - m on m's halves; B16's
    S-p of the governing a0 - m equals it on every half (addendum 33 point 1)."""
    for reading in ("plan_a", "plan_b"):
        doc = doc_with_halves(3, reading, shared=False)
        out = read(doc)["overlap_control"]
        for name, k in out["contrasts"].items():
            theirs_all = doc["overlap"]["report"]["add_sets"][k["repair"]]["contrasts"]
            for h in ("all", "lower", "higher"):
                theirs, ours = theirs_all[h], k["halves"][h]["S-p"]
                assert ours["estimate"]["est"] == pytest.approx(theirs["estimate"], rel=1e-12, abs=1e-12)
                assert ours["estimate"]["seed_var"] == pytest.approx(theirs["v_seed"], rel=1e-10)
                assert ours["estimate"]["item_var"] == pytest.approx(theirs["v_prompt"], rel=1e-10, abs=1e-12)
                assert ours["estimate"]["df"] == pytest.approx(theirs["df"], rel=1e-10)
                assert ours["interval_90"] == pytest.approx([theirs["lower"], theirs["upper"]], rel=1e-9, abs=1e-9)
            b14_holds = doc["overlap"]["report"]["add_sets"][k["repair"]]["verdict"]["holds"]
            assert k["s_p_verdict"]["holds"] == b14_holds


def test_plan_b_a0_contrasts_are_the_paired_form_because_a0_is_outside_the_fit():
    out = read(doc_with_halves(4, "plan_b"))["overlap_control"]
    assert list(out["contrasts"]) == ["a0-S1", "a0-S4"] and out["add_sets_in_no_contrast"] == []
    assert list(out["report_only_contrasts"]) == ["P6"]
    for k in out["contrasts"].values():
        assert k["common_seeds"] == list(range(1102, 1108))
        for h in ("all", "lower", "higher"):
            hb, sp = k["halves"][h]["HB-C"], k["halves"][h]["S-p"]
            assert hb["estimate"]["form"] == "paired (J - 1 df; LN-20 item 2)"
            assert hb["interval_90"] == sp["interval_90"] and hb["estimate"]["seed_df"] == 5.0
        assert k["verdict"]["holds"] == k["s_p_verdict"]["holds"]


# ----- hand cases under plan B (a0 - S4: the paired form on 6 pairs; P6: the two-arm cluster on 9 pairs) ----------------


def plan_b_doc(s4_lower_by_seed, b_lower=None):
    """Plan B with a0 = 2/3 on every prompt; S1 = 2/3 except one higher-half prompt (150) whose share moves with the
    seed (so a0 - S1 has a seed variance on all prompts); S4 on the lower half (positions 0-99) = 2/3 - a_j - b_p (a_j
    by seed, b_p by prompt), on the higher half 1/3. Every add set's lower half is positions 0-99."""
    doc = synth.make_input(5, "plan_b")
    dsg = design("plan_b")
    b_lower = b_lower if b_lower is not None else [F(0)] * 100
    for j in dsg.seeds["a0"]:
        doc["endpoints"]["U"]["cells"]["a0"][str(j)] = [2 / 3] * 200
    for j in dsg.seeds["S1"]:
        doc["endpoints"]["U"]["cells"]["S1"][str(j)] = [2 / 3] * 150 + [(j % 3) / 3] + [2 / 3] * 49
        a = s4_lower_by_seed[j - 1102]
        doc["endpoints"]["U"]["cells"]["S4"][str(j)] = [float(F(2, 3) - a - b_lower[p]) for p in range(100)] + [1 / 3] * 100
    sims = {m: {hs.pid(i): (0.1 if i < 100 else 0.9) for i in range(200)} for m in ("S1", "S3", "S4")}
    doc["overlap"] = hs.overlap_block(doc, sims)
    return doc


def test_hand_case_plan_b_constant_differences():
    """D(j, p) on the lower half = a_j in thirds [1, 1, 0, 2, 1, 1, 1, 0, 1] / 3, so no item part. a0 - S4 (seeds
    1102-1107): mean 100/3 pp, s^2 = (2/5) x 10^4/9, df 5. P6 = S1 - S4 (9 pairs, report only): mean 800/27 pp,
    s^2 = (13/36) x 10^4/9, df 8. Intervals at t(0.95, 5) = 2.015048 and t(0.95, 8) = 1.859548."""
    a = [F(k, 3) for k in (1, 1, 0, 2, 1, 1, 1, 0, 1)]
    out = read(plan_b_doc(a))["overlap_control"]
    g = out["contrasts"]["a0-S4"]["halves"]["lower"]["HB-C"]
    v = float(F(2, 5) * F(10 ** 4, 9) / 6)
    assert g["estimate"]["est"] == pytest.approx(100 / 3, abs=1e-9) and g["estimate"]["df"] == 5.0
    assert g["estimate"]["se"] == pytest.approx(math.sqrt(v), rel=1e-12) and g["estimate"]["item_var"] == pytest.approx(0, abs=1e-9)
    assert g["interval_90"] == pytest.approx([100 / 3 - 2.0150483726691575 * math.sqrt(v), 100 / 3 + 2.0150483726691575 * math.sqrt(v)], abs=1e-6)
    assert out["contrasts"]["a0-S4"]["verdict"]["holds"] and out["contrasts"]["a0-S4"]["verdict"]["text"] == HOLDS
    k = out["report_only_contrasts"]["P6"]
    low = k["halves"]["lower"]["HB-C"]
    lam, v6 = F(800, 27), F(13, 36) * F(10 ** 4, 9) / 9
    t8 = 1.8595480375228421
    assert low["estimate"]["est"] == pytest.approx(float(lam), abs=1e-9) and low["estimate"]["df"] == 8.0
    assert low["estimate"]["se"] == pytest.approx(math.sqrt(float(v6)), rel=1e-12)
    assert low["interval_90"] == pytest.approx([float(lam) - t8 * math.sqrt(float(v6)), float(lam) + t8 * math.sqrt(float(v6))], abs=1e-6)
    assert low["interval_90"][0] == pytest.approx(17.21356, abs=1e-4)
    assert out["fits"]["S4 lower"]["full"]["two_arm"] and out["fits"]["S4 lower"]["full"]["pairs"] == 9
    assert k["verdict"] == {"holds": True, "text": HOLDS, "sign_all": 1, "sign_lower": 1, "model": "HB-C", "fits_converged": True,
                            "reason": "same sign as on all prompts and the 90% interval excludes 0"}


def test_hand_case_plan_b_with_an_item_part():
    """D(j, p) = a_j + b_p on the lower half, a_j in thirds [1, 1, 0, 1, 0, 0, 1, 0, 1] / 3, b_p = 1/3 on 50 of its
    100 prompts: MS_E = 0. a0 - S4 on 6 seeds: MS_P = 6 x 100 x (1/6)^2 / 99; P6 on 9 seeds: MS_P = 25/99.
    V_item = MS_P / (100 J) x 10^4; q = V_item^2 / 99; df = V^2 / (V_seed^2 / (J - 1) + q)."""
    a = [F(k, 3) for k in (1, 1, 0, 1, 0, 0, 1, 0, 1)]
    b = [F(1, 3) if p % 2 else F(0) for p in range(100)]
    out = read(plan_b_doc(a, b))["overlap_control"]
    for est, J, a_used in ((out["contrasts"]["a0-S4"]["halves"]["lower"]["HB-C"]["estimate"], 6, a[:6]),
                           (out["report_only_contrasts"]["P6"]["halves"]["lower"]["HB-C"]["estimate"], 9, a)):
        ms_p = F(J * 100, 36) / 99
        v_item = ms_p / (100 * J) * 10 ** 4
        q = v_item ** 2 / 99
        mean_a = sum(a_used) / J
        v_seed = sum((x - mean_a) ** 2 for x in a_used) / (J - 1) * 10 ** 4 / J
        v = v_seed + v_item
        assert est["est"] == pytest.approx(float((mean_a + F(1, 6)) * 100), abs=1e-9)
        assert est["item_var"] == pytest.approx(float(v_item), rel=1e-9) and est["item_q"] == pytest.approx(float(q), rel=1e-9)
        assert est["seed_var"] == pytest.approx(float(v_seed), rel=1e-9)
        assert est["se"] == pytest.approx(math.sqrt(float(v)), rel=1e-9)
        assert est["df"] == pytest.approx(float(v * v / (v_seed * v_seed / (J - 1) + q)), rel=1e-9)


# ----- the "holds" rule, every branch ---------------------------------------------------------------------------------


def lower_rec(est, lo, hi):
    return {"computable": True, "estimate": {"est": est}, "interval_90": [lo, hi]}


TEXTS = {"holds": HOLDS, "not_shown": NOT_SHOWN}


@pytest.mark.parametrize("all_mean, lower, holds, reason", [
    (4.0, lower_rec(3.0, 0.5, 5.5), True, "same sign as on all prompts and the 90% interval excludes 0"),
    (-4.0, lower_rec(-3.0, -5.5, -0.5), True, "same sign as on all prompts and the 90% interval excludes 0"),
    (4.0, lower_rec(-3.0, -5.5, -0.5), False, "the sign differs from the all-prompt estimate's (or a sign is 0)"),
    (-4.0, lower_rec(3.0, 0.5, 5.5), False, "the sign differs from the all-prompt estimate's (or a sign is 0)"),
    (4.0, lower_rec(3.0, -0.1, 6.1), False, "the 90% interval contains 0"),
    (4.0, lower_rec(3.0, 0.0, 6.0), False, "the 90% interval contains 0"),                 # an end at exactly 0
    (-4.0, lower_rec(-3.0, -6.0, 0.0), False, "the 90% interval contains 0"),
    (4.0, lower_rec(3.0, -math.inf, math.inf), False, "the 90% interval contains 0"),     # an unbounded interval
    (1e-12, lower_rec(3.0, 0.5, 5.5), False, "the sign differs from the all-prompt estimate's (or a sign is 0)"),
    (0.0, lower_rec(3.0, 0.5, 5.5), False, "the sign differs from the all-prompt estimate's (or a sign is 0)"),
    (4.0, lower_rec(1e-12, -1.0, 1.0), False, "the sign differs from the all-prompt estimate's (or a sign is 0)"),
    (2e-9, lower_rec(3.0, 0.5, 5.5), True, "same sign as on all prompts and the 90% interval excludes 0"),
])
def test_every_branch_of_the_holds_rule(all_mean, lower, holds, reason):
    v = overlap.verdict(all_mean, lower, TEXTS, 1e-9)
    assert v["holds"] is holds and v["reason"] == reason and v["text"] == (HOLDS if holds else NOT_SHOWN)


def test_a_lower_half_that_is_not_computable_is_not_shown():
    v = overlap.verdict(4.0, {"computable": False, "reason": "the half holds no prompt"}, TEXTS, 1e-9)
    assert v == {"holds": False, "text": NOT_SHOWN, "sign_all": 1, "sign_lower": None,
                 "reason": "the lower-similarity half is not computable (the half holds no prompt)"}


def test_the_rule_end_to_end_holds_and_not_shown():
    """Plan A: a large add effect on both halves holds; with the effect only on the higher half, a0 - S1's lower half
    is not shown (its true value is 0)."""
    held = read(doc_with_halves(6, "plan_a", {"S1": 15.0, "S3": 15.0, "S4": 15.0}, {"S1": 15.0, "S3": 15.0, "S4": 15.0}))
    k = held["overlap_control"]["contrasts"]["a0-S1"]
    assert k["verdict"]["holds"] and k["verdict"]["sign_all"] == 1 and k["halves"]["lower"]["HB-C"]["interval_90"][0] > 0
    flat = read(doc_with_halves(6, "plan_a", {"S1": 0.0, "S3": 0.0, "S4": 0.0}, {"S1": 25.0, "S3": 25.0, "S4": 25.0}))
    k = flat["overlap_control"]["contrasts"]["a0-S1"]
    assert k["halves"]["all"]["paired_mean_pp"] > 5 and not k["verdict"]["holds"] and k["verdict"]["text"] == NOT_SHOWN


def test_an_empty_and_a_one_prompt_lower_half_are_not_computable():
    flat = {hs.pid(i): 0.5 for i in range(200)}                          # every S equal: B14 puts all 200 above
    doc = doc_with_halves(7, "plan_a", sims={"S1": flat, "S3": flat, "S4": flat})
    assert doc["overlap"]["strata"]["add_sets"]["S1"]["lower"] == []
    assert doc["overlap"]["report"]["add_sets"]["S1"]["cells_u_pp"]["a0"]["1102"]["lower"] is None
    out = read(doc)["overlap_control"]
    k = out["contrasts"]["a0-S1"]
    assert k["half_sizes"] == {"all": 200, "lower": 0, "higher": 200}
    assert k["halves"]["lower"]["HB-C"] == {"computable": False, "reason": "the half holds no prompt"}
    assert not k["verdict"]["holds"] and k["verdict"]["reason"].startswith("the lower-similarity half is not computable")
    one = {hs.pid(i): (0.1 if i == 7 else 0.5) for i in range(200)}
    out = read(doc_with_halves(7, "plan_a", sims={"S1": one, "S3": one, "S4": one}))["overlap_control"]
    k = out["contrasts"]["a0-S1"]
    assert k["half_sizes"]["lower"] == 1 and not k["halves"]["lower"]["HB-C"]["computable"]
    assert "fewer than 2" in k["halves"]["lower"]["HB-C"]["reason"] and not k["verdict"]["holds"]
    assert k["verdict"]["fits_converged"] is False and out["fits"]["S1 lower"]["fitted"] is False


def test_ties_at_the_boundary_go_to_the_higher_half():
    doc = doc_with_halves(8, "plan_a", tie_block=9)
    sizes = read(doc)["overlap_control"]["contrasts"]["a0-S1"]["half_sizes"]
    assert sizes["lower"] < 100 and sizes["lower"] + sizes["higher"] == 200
    assert doc["overlap"]["strata"]["add_sets"]["S1"]["ties_at_boundary"] == 9


def test_a_block_a_only_reading_carries_its_suffix():
    """Addendum 33 point 4 (C10): every verdict text of a block-A-only reading carries the design's suffix; plan A's
    carry none."""
    oc = read(doc_with_halves(9, "plan_a_block_a_only"))["overlap_control"]
    assert oc["label_suffix"] == "block A only (3 seeds per method arm)"
    for k in list(oc["contrasts"].values()) + list(oc["report_only_contrasts"].values()):
        for v in ("verdict", "s_p_verdict", "prereg_start_verdict"):
            assert k[v]["text"] in (HOLDS + BLOCK_A, NOT_SHOWN + BLOCK_A)
    oc = read(doc_with_halves(9, "plan_a"))["overlap_control"]
    assert all(k["verdict"]["text"] in (HOLDS, NOT_SHOWN) for k in oc["contrasts"].values())


# ----- report only; absent block ----------------------------------------------------------------------------------------


def test_the_block_is_report_only_and_absent_without_its_input():
    doc = doc_with_halves(9, "plan_a")
    with_block = read(doc)
    without = copy.deepcopy(doc)
    del without["overlap"]
    plain = read(without)
    assert plain["overlap_control"]["computed"] is False and "not computed" in plain["overlap_control"]["reason"]
    for key in plain:
        if key != "overlap_control":
            assert plain[key] == with_block[key], key


# ----- the halves bound to B14's sealed records (addendum 33 point 3): refusals and acceptance ---------------------------


@pytest.fixture(scope="module")
def good():
    return doc_with_halves(11, "plan_a", shared=False)


@pytest.fixture(scope="module")
def tied():
    return doc_with_halves(12, "plan_a", tie_block=7)


def mutate(doc, fn, rehash=False):
    d = copy.deepcopy(doc)
    fn(d["overlap"])
    if rehash:
        hs.rehash(d["overlap"])
    return d


def swap_halves(o, m="S1"):
    """The verifier's swap: lower and higher exchanged in the strata, and the cells_u_pp labels with them."""
    s = o["strata"]["add_sets"][m]
    s["lower"], s["higher"] = s["higher"], s["lower"]
    for arm in o["report"]["add_sets"][m]["cells_u_pp"].values():
        for cell in arm.values():
            cell["lower"], cell["higher"] = cell["higher"], cell["lower"]


def _set(path, value):
    def fn(o):
        node = o
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return fn


def _move_one(o):
    s = o["strata"]["add_sets"]["S3"]
    s["lower"] = sorted(s["lower"] + s["higher"][:1])
    s["higher"] = s["higher"][1:]
    s["lower_n"], s["higher_n"] = len(s["lower"]), len(s["higher"])
    o["report"]["add_sets"]["S3"]["half_sizes"] = {"all": 200, "lower": len(s["lower"]), "higher": len(s["higher"])}


def _shift_cell(by):
    def fn(o):
        o["report"]["add_sets"]["S4"]["cells_u_pp"]["S4"]["1107"]["lower"] += by
    return fn


REFUSED_AS_SENT = {                                     # edits without new hashes: the SHA-256 binding refuses each
    "the verifier's swap": swap_halves,
    "a strata number": _set(("strata", "add_sets", "S1", "boundary"), 0.5),
    "a report value": _shift_cell(1e-6),
    "a report half size": _set(("report", "add_sets", "S1", "half_sizes", "lower"), 99),
    "an upper-case hash": _set(("strata_sha256",), "A" * 64),
    "a short hash": _set(("report_sha256",), "b" * 63),
    "an extra key": lambda o: o.update(extra=1),
    "no report": lambda o: o.pop("report"),
    "a report field B16 does not read": _set(("report", "requirement"), "edited"),
    "a strata field B16 does not read": _set(("strata", "requirement"), "edited"),
}
REFUSED_REHASHED = {                                    # edits re-hashed throughout: the split rule or the U table refuses
    "the swap with ties (lower above floor(n/2))": None,
    "one prompt moved into the lower half": _move_one,
    "lower_n not the half's count": _set(("strata", "add_sets", "S1", "lower_n"), 99),
    "k not floor(n/2)": _set(("strata", "add_sets", "S1", "k"), 99),
    "lower_max at the boundary": lambda o: o["strata"]["add_sets"]["S1"].update(lower_max=o["strata"]["add_sets"]["S1"]["boundary"]),
    "higher_min not the boundary": lambda o: o["strata"]["add_sets"]["S1"].update(higher_min=1.0),
    "no tie at the boundary": _set(("strata", "add_sets", "S1", "ties_at_boundary"), 0),
    "a prompt id repeated across halves": lambda o: o["strata"]["add_sets"]["S1"]["higher"].append(o["strata"]["add_sets"]["S1"]["lower"][0]),
    "an add set missing from the strata": lambda o: o["strata"]["add_sets"].pop("S3"),
    "an add set missing from the report": lambda o: o["report"]["add_sets"].pop("S3"),
    "another seed plan": _set(("report", "seed_plan"), "block_a_only"),
    "other seeds": _set(("report", "seeds"), [1102, 1103, 1104]),
    "the report's ties": _set(("report", "add_sets", "S4", "ties_at_boundary"), 2),
    "the report's arm": _set(("report", "add_sets", "S4", "arm"), "edit-" + "9" * 64),
    "199 prompt ids": lambda o: o["strata"].update(prompt_ids=o["strata"]["prompt_ids"][:-1]),
    "a cells_u_pp value off by 1e-6": _shift_cell(1e-6),
    "cells_u_pp swapped halves": lambda o: o["report"]["add_sets"]["S3"]["cells_u_pp"]["a0"]["1104"].update(
        lower=o["report"]["add_sets"]["S3"]["cells_u_pp"]["a0"]["1104"]["higher"],
        higher=o["report"]["add_sets"]["S3"]["cells_u_pp"]["a0"]["1104"]["lower"]),
    "cells_u_pp at seed 1101": lambda o: o["report"]["add_sets"]["S1"]["cells_u_pp"]["a0"].update(
        {"1101": o["report"]["add_sets"]["S1"]["cells_u_pp"]["a0"]["1102"]}),
    "a strata kind": _set(("strata", "kind"), "stage1 overlap report"),
}


@pytest.mark.parametrize("case", sorted(REFUSED_AS_SENT))
def test_an_edited_block_is_refused_by_its_sha256(good, case):
    with pytest.raises(Refusal):
        validate(mutate(good, REFUSED_AS_SENT[case]))


@pytest.mark.parametrize("case", sorted(REFUSED_REHASHED))
def test_a_rehashed_edit_is_refused_by_the_split_rule_or_the_u_table(good, tied, case):
    if case.startswith("the swap with ties"):
        doc = mutate(tied, lambda o: swap_halves(o, "S1"), rehash=True)
    else:
        doc = mutate(good, REFUSED_REHASHED[case], rehash=True)
    with pytest.raises(Refusal):
        validate(doc)


def test_a_report_made_on_another_strata_record_is_refused(good):
    """The report's own strata_sha256 must name the embedded strata record (re-hashing the report alone)."""
    doc = copy.deepcopy(good)
    doc["overlap"]["report"]["strata_sha256"] = "c" * 64
    doc["overlap"]["report_sha256"] = b14_sha256(doc["overlap"]["report"])
    with pytest.raises(Refusal):
        validate(doc)


def test_a_swap_rehashed_throughout_prints_sha256_that_differ_from_b14s(good):
    """Without ties both halves hold 100 prompts, so a swap re-hashed throughout (strata, the report's strata_sha256
    and cells_u_pp, both fields) satisfies the split's counts and the U table; it cannot keep B14's SHA-256, and the
    output prints them for the lead to compare with B14's sealed values (the binding of addendum 33 point 3)."""
    doc = mutate(good, swap_halves, rehash=True)
    inp = validate(doc)
    assert inp.overlap["strata_sha256"] != good["overlap"]["strata_sha256"]
    assert inp.overlap["report_sha256"] != good["overlap"]["report_sha256"]
    out = read(doc)["overlap_control"]
    assert out["report_sha256"] == doc["overlap"]["report_sha256"] != good["overlap"]["report_sha256"]


def test_the_u_items_must_follow_the_strata_prompt_order(good):
    doc = copy.deepcopy(good)
    perm = np.random.default_rng(0).permutation(200)
    for arm, by_seed in doc["endpoints"]["U"]["cells"].items():
        for seed, values in by_seed.items():
            by_seed[seed] = [values[i] for i in perm]
    with pytest.raises(Refusal):
        validate(doc)


def test_the_schema_accepts_b14s_records_and_rounding_below_tolerance(good, tied):
    for doc in (good, tied):
        inp = validate(doc)
        assert set(inp.overlap["add_sets"]) == {"S1", "S3", "S4"}
        assert inp.overlap["strata_sha256"] == b14_sha256(doc["overlap"]["strata"]) == doc["overlap"]["report"]["strata_sha256"]
        assert inp.overlap["report_sha256"] == b14_sha256(doc["overlap"]["report"])
        for m, block in inp.overlap["add_sets"].items():
            ids = doc["overlap"]["strata"]["add_sets"][m]["lower"]
            assert block["lower"].tolist() == sorted(int(p[1:]) for p in ids) and len(block["lower"]) <= 100
    validate(mutate(good, _shift_cell(1e-12), rehash=True))
    assert len(validate(tied).overlap["add_sets"]["S1"]["lower"]) < 100


def test_plan_b_needs_its_own_seed_plan_and_add_arms(good):
    doc = doc_with_halves(12, "plan_b")
    assert set(doc["overlap"]["report"]["add_sets"]) == {"S1", "S4"} and doc["overlap"]["report"]["seed_plan"] == "plan_b"
    assert doc["overlap"]["report"]["strata_add_sets_not_in_plan"] == ["S3"]
    validate(doc)
    bad = copy.deepcopy(doc)
    bad["overlap"] = copy.deepcopy(good["overlap"])                      # plan A's records in a plan-B reading
    with pytest.raises(Refusal):
        validate(bad)
    assert sorted(doc["overlap"]["report"]["add_sets"]["S4"]["cells_u_pp"]["S4"]) == [str(j) for j in range(1102, 1108)]


# ----- a small seeded simulation (the larger one: sim_halves.py) --------------------------------------------------------


def simulate(reps, eff_lower, eff_higher, seed):
    """Coverage of the lower half's 90% interval (HB-C and S-p) of a0 - m at the true lower-half value, and the
    'holds' rate, in the halves world with prompts drawn afresh (plan A)."""
    rng = np.random.default_rng(seed)
    dsg, cfg = design("plan_a"), settings()
    truth = {f"a0-{m}": eff_lower[m] for m in ("S1", "S3", "S4")}
    cover = {(n, f): 0 for n in truth for f in ("HB-C", "S-p")}
    holds = {n: 0 for n in truth}
    for _ in range(reps):
        split = b14.split_halves(hs.similarity(rng))
        lower, higher = np.array(hs.positions(split["lower"])), np.array(hs.positions(split["higher"]))
        mask = np.zeros(200, bool)
        mask[lower] = True
        table = hs.world_cells(rng, dsg, mask, eff_lower, eff_higher)
        ov = {"strata_sha256": "a" * 64, "report_sha256": "b" * 64,
              "add_sets": {m: {"lower": lower, "higher": higher} for m in ("S1", "S3", "S4")}}
        out = overlap.read_halves(ov, dsg, table, 100.0, 0.01, cfg)
        for n, k in out["contrasts"].items():
            for f in ("HB-C", "S-p"):
                lo, hi = k["halves"]["lower"][f]["interval_90"]
                cover[(n, f)] += lo <= truth[n] <= hi
            holds[n] += k["verdict"]["holds"]
    return {key: v / reps for key, v in cover.items()}, {n: v / reps for n, v in holds.items()}


def test_small_simulation_coverage_and_false_holds():
    """60 replicates per world (binomial SE of a 90% coverage about 3.9 points; the larger run is sim_halves.py).
    World 1: the add effect is 6 pp on both halves, so a0 - m holds often and every lower-half interval covers its
    truth near 90%. World 2: no effect on the lower half and 12 pp on the higher one (all prompts +6 pp): the false
    'holds' rate stays near 5%."""
    cover, holds = simulate(60, {"S1": 6.0, "S3": 6.0, "S4": 6.0}, {"S1": 6.0, "S3": 6.0, "S4": 6.0}, 20261027)
    for key, c in cover.items():
        assert 0.75 <= c <= 1.0, (key, c)
    assert min(holds.values()) >= 0.45
    cover, holds = simulate(60, {"S1": 0.0, "S3": 0.0, "S4": 0.0}, {"S1": 12.0, "S3": 12.0, "S4": 12.0}, 20261028)
    for key, c in cover.items():
        assert 0.75 <= c <= 1.0, (key, c)
    assert max(holds.values()) <= 0.17
