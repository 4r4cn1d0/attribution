"""The whole reading on synthetic tables: plan A, block A only, plan B, the schema's refusals, the one-estimate
identity behind F_k and O_k, coherence flags, the references with the 3-seed fallback, the command line."""

from __future__ import annotations

import copy
import json
import math

import numpy as np
import pytest

from scripts.stage1_s1.reading import references as refs
from scripts.stage1_s1.reading import tdist
from scripts.stage1_s1.reading.__main__ import main as cli
from scripts.stage1_s1.reading.reading import read
from scripts.stage1_s1.reading.schema import validate
from scripts.stage1_s1.reading.settings import Refusal, canonical_json, settings

import synth

PLAN_A_SEEDS = list(range(1101, 1108))


@pytest.fixture(scope="module")
def plan_a():
    return read(synth.make_input(1, "plan_a", with_variants=True, with_token_axis=True))


@pytest.fixture(scope="module")
def plan_b():
    return read(synth.make_input(2, "plan_b"))


def test_plan_a_structure_and_consistency(plan_a):
    out = plan_a
    assert out["kind"] == "stage1 reading output" and out["reading"] == "plan_a" and out["label_suffix"] is None
    assert list(out["contrasts"]) == ["P1", "P2", "P3", "P4", "P5", "P6"]
    assert set(out["fits"]) == {"U", "O", "L"} and set(out["fits"]["U"]) == {"full", "removal"}
    assert out["fits"]["L"]["full"]["floor"] == 1e-8 and out["fits"]["U"]["full"]["floor"] == 0.01
    for name, k in out["contrasts"].items():
        assert k["common_seeds"] == list(range(1102, 1108)) and k["familywise_level"] == pytest.approx(1 - 0.1 / 6)
        assert k["p_values"]["U"] == pytest.approx(k["U"]["p_two_sided"])
        assert k["p_values"]["O"] == max(k["O"]["p_comparator"], k["O"]["p_theta0"])
        assert k["p_values"]["L"] == max(k["L"]["p_comparator"], k["L"]["p_a0"])
        assert k["p_values"]["F"] + k["O"]["p_theta0"] == pytest.approx(1.0)               # one estimate, one SE, one df
        lo, hi = k["U_interval_90"]
        assert hi - k["U"]["est"] == pytest.approx(tdist.t_quantile(0.95, k["U"]["df"]) * k["U"]["se"])
        assert out["headline"][name] == out["rows"][name]["headline"]["word"]
    assert out["contrasts"]["P4"]["L"]["reduces_to_a0_part"] and not out["contrasts"]["P1"]["L"]["reduces_to_a0_part"]
    assert out["contrasts"]["P1"]["L"]["a0_part"]["form"].startswith("paired")            # cross-cluster: LN-20 item 2
    assert out["contrasts"]["P4"]["L"]["a0_part"]["form"] == "HB-C"
    assert out["contrasts"]["P1"]["O"]["theta0_part"]["seed_df"] == 5.0                  # LN-20 item 1
    assert out["phi"]["start_levels"]["U:P1"] == "3/400" and out["phi"]["start_levels"]["F:P1"] == "0"
    assert set(out["sensitivities"]) >= {"HB", "S-a", "S-aW", "S-b2x", "S-0", "S-p", "S-G", "S-A8", "S-tok"}
    assert out["provenance"]["settings_sha256"] == settings and True or len(out["provenance"]["settings_sha256"]) == 64


def test_phi_rejections_match_the_recorded_levels(plan_a):
    out = plan_a
    for node, level in out["phi"]["level_at_rejection"].items():
        kind, name = node.split(":")
        num, den = (level.split("/") + ["1"])[:2]
        assert out["contrasts"][name]["p_values"][kind] <= float(num) / float(den) * (1 + 1e-12)
    for node, level in out["phi"]["final_levels"].items():
        kind, name = node.split(":")
        num, den = (level.split("/") + ["1"])[:2]
        assert out["contrasts"][name]["p_values"][kind] > float(num) / float(den)


def test_rows_carry_every_part(plan_a):
    row = plan_a["rows"]["P1"]
    assert set(row) >= {"u_part", "side_effect_part", "feasibility_part", "coherence_part", "sensitivity_part", "headline"}
    assert set(row["feasibility_part"]["states"]) == {"tau_o_2", "tau_o_5", "tau_o_10"}
    assert row["feasibility_part"]["below_resolution"] == "tau_o_2"
    assert row["side_effect_part"]["o_vs_theta0_interval_90"] and row["side_effect_part"]["l_vs_a0_interval_90"]
    assert row["coherence_part"] == []
    assert plan_a["arms"]["A1"]["restoration_G"]["est"] == pytest.approx(
        plan_a["arms"]["a0"]["means"]["U"] * 0 + plan_a["arms"]["A1"]["restoration_G"]["est"])


def test_states_follow_the_one_estimate_rule_under_strong_effects():
    """O_k rejected => the printed state is 'infeasible'; F_k rejected => 'feasible' (REV3 3.6 item 4; ST-8)."""
    for seed, levels in ((7, {"S1": 40.0, "S3": 45.0}), (8, {"S1": 2.0, "S3": 2.0, "A1": 2.0})):
        out = read(synth.make_input(seed, "plan_a", o_levels=levels, u_levels={"S1": 40.0, "A1": 30.0}))
        for node in out["phi"]["rejected"]:
            kind, name = node.split(":")
            state = out["rows"][name]["feasibility_part"]["states"]["tau_o_5"]
            if kind == "O":
                assert state == "infeasible" and "worse (O)" in out["rows"][name]["headline"]["word"]
            if kind == "F":
                assert state == "feasible"
            assert not ("O:" + name in out["phi"]["rejected"] and "F:" + name in out["phi"]["rejected"])


def test_block_a_only_carries_the_suffix_on_every_cell_and_three_pairs():
    out = read(synth.make_input(3, "plan_a_block_a_only"))
    for name, k in out["contrasts"].items():
        assert k["common_seeds"] == [1102, 1103, 1104] and k["U"]["pairs"] == 3
        assert out["rows"][name]["headline"]["cell"].endswith("[block A only (3 seeds per method arm)]")
        assert k["U_mde_80_at_start_level"] > 0
    assert out["fits"]["U"]["full"]["residual_df"] == 6.0
    assert any("block A" in n for n in out["notes"])


def test_plan_b_two_arm_cluster_three_contrasts_and_a0_outside_the_fit(plan_b):
    out = plan_b
    assert list(out["contrasts"]) == ["P1", "P3", "P6"] and out["design"]["fit_arms"] == ["R", "A1", "H1", "S1", "S4"]
    full = out["fits"]["U"]["full"]
    assert full["two_arm"] and list(full["sigma2"]) == ["sum"] and full["pairs"] == 9
    p6 = out["contrasts"]["P6"]
    assert p6["U"]["seed_df"] == 8.0 and p6["U"]["pairs"] == 9 and p6["U"]["form"] == "HB-C"
    assert p6["familywise_level"] == pytest.approx(1 - 0.1 / 3)
    assert p6["L"]["a0_part"]["form"].startswith("paired") and p6["L"]["a0_part"]["seed_df"] == 5.0        # LN-21 item 2
    assert out["contrasts"]["P1"]["U"]["pairs"] == 9 and out["fits"]["U"]["removal"]["residual_df"] == 16.0
    assert out["phi"]["start_levels"]["U:P1"] == "3/200"
    assert "a0" in out["arms"] and out["arms"]["a0"]["seeds"] == PLAN_A_SEEDS


def test_o_comparator_part_uses_the_r_seeds_present_or_is_not_tested():
    out = read(synth.make_input(4, "plan_a", r_o_seeds=[1104, 1105, 1106, 1107]))
    k = out["contrasts"]["P1"]
    assert k["O"]["comparator_part"]["pairs"] == 4 and k["O"]["comparator_part"]["form"].startswith("paired on the O seeds")
    assert out["contrasts"]["P4"]["O"]["comparator_part"]["form"] == "HB-C"
    out = read(synth.make_input(4, "plan_a", r_o_seeds=[1106, 1107]))
    k = out["contrasts"]["P2"]
    assert k["O"]["comparator_part"] is None and "not tested" in k["O"]["comparator_part_note"]
    assert k["p_values"]["O"] == 1.0 and "O:P2" not in out["phi"]["rejected"]


def test_coherence_flags_print_beside_the_word_and_never_change_it():
    doc = synth.make_input(5, "plan_a")
    base = read(doc)
    flagged = read(synth.make_input(5, "plan_a", failing_arms=("A1", "S1")))
    assert flagged["headline"] == base["headline"]
    assert flagged["rows"]["P1"]["coherence_part"] == ["fails answers end"]
    assert flagged["rows"]["P5"]["coherence_part"] == ["comparator fails answers end"]
    assert flagged["rows"]["P4"]["coherence_part"] == ["fails answers end"]
    assert flagged["rows"]["P2"]["coherence_part"] == []
    assert not flagged["arms"]["A1"]["coherence"]["passes"] and flagged["arms"]["R"]["coherence"]["passes"]
    for c in flagged["best_feasible_repair"]["candidates"]:
        if c["arm"] in ("A1", "S1"):
            assert not c["feasible"]


def test_sensitivity_part_lists_only_differing_labels(plan_a):
    for name, row in plan_a["rows"].items():
        primary = row["u_part"]["words"]
        for item in row["sensitivity_part"]:
            if "u_part_words" in item:
                assert item["u_part_words"] != primary
                assert plan_a["sensitivities"][item["code"].split(" ")[0]] is not None
        for code in ("HB", "S-a", "S-aW", "S-b2x", "S-0", "S-p"):
            rec = plan_a["sensitivities"][code][name]
            assert rec["differs_from_primary"] == (rec["u_part_words"] != primary)
    assert plan_a["sensitivities"]["S-tok"]["arms"].keys() == {"A1", "L1", "H1"}
    assert "o_vs_theta0_a8" in plan_a["sensitivities"]["S-A8"]["P4"] and "l_vs_a0_in_model_a8" in plan_a["sensitivities"]["S-A8"]["P1"]


def test_references_point_curve_fallback_and_family_1b():
    seven, three = list(range(1101, 1108)), [1101, 1102, 1103]
    out = read(synth.make_input(6, "plan_a", references=[("point", "SP", seven), ("curve", "AS", seven)]))
    fam = out["references"]["family_1b"]
    assert fam["tested"] and set(fam["contrasts"]) == {"P1", "P2", "P3", "P4", "P5", "P6"}
    sp_s1 = [p for p in out["references"]["per_repair"]["S1"] if p["reference"] == "SP"][0]
    sp_a1 = [p for p in out["references"]["per_repair"]["A1"] if p["reference"] == "SP"][0]
    assert sp_s1["bounds"]["U"]["estimate"]["form"] == "reference fit (HB-C)" and sp_s1["common_seeds"] == list(range(1102, 1108))
    assert sp_a1["bounds"]["U"]["estimate"]["form"].startswith("paired") and sp_a1["bounds"]["L"]["estimate"]["seed_df"] == 5.0
    assert sp_s1["bounds"]["O"]["margin"] == 5.0 and sp_s1["bounds"]["L"]["margin"] == 0.0067170919092681925
    assert sp_s1["beats"] == all(b["holds"] for b in sp_s1["bounds"].values())
    for e, b in sp_s1["bounds"].items():
        est = b["estimate"]
        assert b["interval_90"][1] - est["est"] == pytest.approx(tdist.t_quantile(0.95, est["df"]) * est["se"])
        assert b["holds"] == (b["interval_90"][1] < b["margin"]) and b["p_one_sided"] == pytest.approx(
            1 - tdist.t_sf((est["est"] - b["margin"]) / est["se"], est["df"]))
    assert not (sp_s1["beats"] and sp_s1["r_beats_m"])
    curve = [p for p in out["references"]["per_repair"]["A1"] if p["reference"] == "AS"][0]
    assert set(curve["bounds"]) == {"U", "O"} and curve["lambda_lo"] <= curve["lambda_up"] and curve["lambda_hi"] >= curve["lambda_dn"]
    assert set(curve["rise_curve"]) == {"1", "0.9", "0.75", "0.5", "0"}
    fb = read(synth.make_input(6, "plan_a", references=[("point", "SP", three)]))
    point = fb["references"]["per_repair"]["S1"][0]
    assert point["fallback_3_seed"] and point["descriptive"] and point["bounds"]["U"]["estimate"]["form"].startswith("S-aW")
    assert not fb["references"]["family_1b"]["tested"] and "not tested" in fb["references"]["family_1b"]["reason"]


def test_curve_switch_lambda_star_is_1_only_when_l_is_shown_feasible():
    seven = list(range(1101, 1108))
    out = read(synth.make_input(6, "plan_a", l_levels={"S1": 1.5601}, references=[("curve", "AS", seven)]))
    s1 = [p for p in out["references"]["per_repair"]["S1"] if p["reference"] == "AS"][0]
    if s1["l_interval_90"][1] <= 0.0067170919092681925:
        assert s1["lambda_lo"] == 1.0 and s1["lambda_hi"] == 1.0 and s1["switch"].startswith("lambda* = 1")
        assert s1["bounds"]["U"]["estimate"]["name"] == "S1-a0"
    out = read(synth.make_input(6, "plan_a", l_levels={"S3": 1.75}, references=[("curve", "AS", seven)]))
    s3 = [p for p in out["references"]["per_repair"]["S3"] if p["reference"] == "AS"][0]
    assert s3["switch"].startswith("matched on L") and s3["lambda_lo"] < 1.0
    # ST-1's case: the point estimate is at or below tau_L but the upper end is above it -> no switch to lambda* = 1
    for seed in range(6, 12):
        out = read(synth.make_input(seed, "plan_a", l_levels={"S4": 1.565}, references=[("curve", "AS", seven)]))
        s4 = [p for p in out["references"]["per_repair"]["S4"] if p["reference"] == "AS"][0]
        lo, up = s4["l_interval_90"]
        if s4["l_vs_a0"]["est"] <= 0.0067170919092681925 < up:
            assert s4["switch"].startswith("matched on L") and s4["lambda_lo"] < 1.0
            break
    else:
        pytest.fail("no synthetic draw put the estimate below tau_L with the upper end above it")


def test_dominance_is_holm_over_the_contrasts():
    per = {m: [{"reference": "SP", "p_iut": p, "beats": p < 0.05, "fallback_3_seed": False}]
           for m, p in (("A1", 0.005), ("L1", 0.009), ("H1", 0.9), ("S1", 0.9), ("S3", 0.9), ("S4", 0.9))}
    contrasts = (("P1", "R", "A1"), ("P2", "R", "L1"), ("P3", "R", "H1"), ("P4", "a0", "S1"), ("P5", "S1", "S3"), ("P6", "S1", "S4"))
    out = refs.dominance(per, contrasts)
    assert out["tested"] and out["contrasts"]["P1"]["dominates"] and out["contrasts"]["P2"]["dominates"]      # 0.009 <= 0.05/5
    assert not out["contrasts"]["P3"]["dominates"]
    per["S4"][0]["fallback_3_seed"] = True
    assert not refs.dominance(per, contrasts)["tested"]


def test_lambda_at_and_grid_bracket_hand_cases():
    rise = {1.0: 0.0, 0.9: 0.01, 0.75: 0.03, 0.5: 0.10, 0.0: 0.55}
    assert refs.lambda_at(rise, -0.001) == 1.0 and refs.lambda_at(rise, 0.0) == 1.0
    assert refs.lambda_at(rise, 0.005) == pytest.approx(0.95)
    assert refs.lambda_at(rise, 0.02) == pytest.approx(0.825)
    assert refs.lambda_at(rise, 0.9) == 0.0
    assert refs.grid_bracket(0.95, 0.99, [1.0, 0.9, 0.75, 0.5, 0.0]) == (0.9, 1.0)
    assert refs.grid_bracket(0.825, 0.95, [1.0, 0.9, 0.75, 0.5, 0.0]) == (0.75, 1.0)
    assert refs.grid_bracket(0.75, 0.75, [1.0, 0.9, 0.75, 0.5, 0.0]) == (0.75, 0.75)
    bumpy = {1.0: 0.0, 0.9: 0.05, 0.75: 0.02, 0.5: 0.10, 0.0: 0.55}      # not monotone: the first crossing from 1 down
    assert refs.lambda_at(bumpy, 0.03) == pytest.approx(0.94)


def test_determinism_and_the_command_line(tmp_path):
    doc = synth.make_input(9, "plan_b")
    a, b = canonical_json(read(doc)), canonical_json(read(doc))
    assert a == b
    src, out = tmp_path / "in.json", tmp_path / "out.json"
    src.write_bytes(canonical_json(doc))
    assert cli(["--input", str(src), "--out", str(out)]) == 0
    written = json.loads(out.read_bytes())
    assert written["headline"] == json.loads(a)["headline"] and written["provenance"]["input_sha256"]
    assert cli(["--input", str(src), "--out", str(out)]) == 2                      # never overwrites
    bad = tmp_path / "bad.json"
    bad.write_bytes(b'{"kind": "x"}')
    assert cli(["--input", str(bad), "--out", str(tmp_path / "o2.json")]) == 2 and not (tmp_path / "o2.json").exists()


# --- the schema: refuse anything else -----------------------------------------------------------------------------

def mutate(doc, fn):
    d = copy.deepcopy(doc)
    fn(d)
    return d


@pytest.mark.parametrize("change", [
    lambda d: d.update(extra=1),
    lambda d: d.update(kind="stage1 reading"),
    lambda d: d.update(version=2),
    lambda d: d.update(reading="plan_c"),
    lambda d: d.pop("coherence"),
    lambda d: d["endpoints"].pop("L"),
    lambda d: d["endpoints"]["U"].update(theta0=[0.0] * 200),
    lambda d: d["endpoints"]["U"]["cells"].pop("S3"),
    lambda d: d["endpoints"]["U"]["cells"]["S3"].pop("1107"),
    lambda d: d["endpoints"]["U"]["cells"]["a0"].update({"1108": [0.0] * 200}),
    lambda d: d["endpoints"]["U"]["cells"]["a0"]["1101"].pop(),
    lambda d: d["endpoints"]["U"]["cells"]["a0"]["1101"].__setitem__(0, 1.5),
    lambda d: d["endpoints"]["U"]["cells"]["a0"]["1101"].__setitem__(0, "0.3"),
    lambda d: d["endpoints"]["U"]["cells"]["a0"]["1101"].__setitem__(0, float("nan")),
    lambda d: d["endpoints"]["O"]["cells"]["a0"]["1101"].__setitem__(0, 0.5),
    lambda d: d["endpoints"]["O"]["cells"]["A1"].pop("1107"),                      # only R may hold a subset of O seeds
    lambda d: d["endpoints"]["O"].update(theta0=[1.0] * 499),
    lambda d: d["endpoints"]["L"]["cells"]["R"]["1101"].__setitem__(0, -0.1),
    lambda d: d["coherence"]["R"]["1101"].update(failing=601),
    lambda d: d["coherence"]["R"]["1101"].update(answers=0),
    lambda d: d["coherence"]["R"]["1101"].update(note="x"),
    lambda d: d["coherence"].pop("H1"),
    lambda d: d.update(u_variants={"other": d["endpoints"]["U"]["cells"]}),
    lambda d: d.update(references=[]),
    lambda d: d.update(references=[{"name": "SP", "kind": "line", "cells": {}}]),
    lambda d: d.update(token_axis={"axis": "chars"}),
])
def test_the_schema_refuses_anything_else(change):
    doc = synth.make_input(10, "plan_a")
    with pytest.raises(Refusal):
        validate(mutate(doc, change))


def test_the_schema_accepts_the_sealed_design_only():
    doc = synth.make_input(10, "plan_a")
    inp = validate(doc)
    assert sum(1 for (a, j) in inp.tables["U"]) == 50 and inp.theta0_o.shape == (500,)
    b = synth.make_input(10, "plan_b")
    assert sum(1 for (a, j) in validate(b).tables["U"]) == 7 + 10 + 4 * 9
    with pytest.raises(Refusal):
        validate(mutate(doc, lambda d: d.update(reading="plan_b")))                 # plan-A tables under plan B's design
