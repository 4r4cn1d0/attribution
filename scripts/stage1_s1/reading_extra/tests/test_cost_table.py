"""The measured cost per arm (cost_table.py; REV4 7.3, 10.1-10.4): every number by hand from the planted ledgers
(C-full = slot / 2,934 s; C-lean: a run is 1 c0, a diagnostic or study cost its seconds / the measured c0, a B10
reference state one lean state = the measured c0 less the frozen lean training price, plus its transform; a ref_eval
point's C-full by REV4:813 = the matched a0 run's slot on the same seed less the frozen C-full training price, plus the
ledger's transform stage, with K5's null beside it, and the per-reference means over seeds; the charging map whole and
split over the reading's arms, the split's denominator and the anchor job named; A1 from w0b-2's frozen values; the
median stage-1 R slot beside 1 FRE); only readable cost ledgers are opened; the bindings and refusals; the runner's
stage names; the frozen lean and C-full training prices; the command line (the file and its SHA-256 only)."""

from __future__ import annotations

import ast
import json
import math
import statistics
from pathlib import Path

import extra_kit as ek
import pytest
import synth_kit as sk

from scripts.stage1_s1.reading.settings import Refusal, design
from scripts.stage1_s1.reading_extra import cost_table as ct

FRE = 2934.0


@pytest.fixture(scope="module")
def kits(tmp_path_factory):
    cache = {}

    def get(reading="plan_a_block_a_only", with_c0=True):
        key = (reading, with_c0)
        if key not in cache:
            cache[key] = ek.cost_kit(tmp_path_factory.mktemp("cost"), reading, with_c0)
        return cache[key]
    return get


def slot_of(plan, slots, kind, arm=None, seed=None):
    for host, h in sorted(plan["hosts"].items()):
        for i, j in enumerate(h["jobs"]):
            if j["kind"] == kind and (arm is None or j.get("arm") == arm) and (seed is None or j.get("seed") == seed):
                return slots[(host, i)]
    raise KeyError((kind, arm, seed))


def test_runs_and_c0_by_hand(kits):
    kit, slots, plan = kits()
    out = ct.table(kit, "plan_a_block_a_only")
    c0 = slot_of(plan, slots, "c0")
    assert out["units"]["c0"]["measured_s"] == c0 and out["units"]["fre_s"] == FRE
    dsg = design("plan_a_block_a_only")
    for arm in dsg.arms:
        rec = out["arms"][arm]
        kind = "a0_arm" if arm == "a0" else "arm"
        want = {str(j): slot_of(plan, slots, kind, arm, j) / FRE for j in dsg.seeds[arm]
                if not (arm in ("a0", "R") and j <= 1103)}
        assert {k: r["c_full_fre"] for k, r in rec["runs"].items()} == want
        assert math.isclose(rec["run"]["c_full_fre_mean"], sum(want.values()) / len(want), rel_tol=1e-12)
        assert rec["run"]["c_lean_c0"] == 1.0
        assert [m["seed"] for m in rec["seeds_not_in_kit"]] == [j for j in dsg.seeds[arm] if str(j) not in want]
        assert all(m["why"].startswith("reused") for m in rec["seeds_not_in_kit"])


def test_the_charges_by_hand(kits):
    kit, slots, plan = kits()
    out = ct.table(kit, "plan_a_block_a_only")
    c0 = slot_of(plan, slots, "c0")
    s = {k: slot_of(plan, slots, k) for k in ("rep_pass", "untuned_answers", "l1_scan", "classifier", "w1_18")}
    want = {"L1": (s["l1_scan"] + s["rep_pass"], s["l1_scan"] + s["rep_pass"] / 2),
            "S3": (s["untuned_answers"] + s["rep_pass"], (s["untuned_answers"] + s["rep_pass"]) / 2),
            "S4": (s["untuned_answers"], s["untuned_answers"] / 2),
            "H1": (0.0, 0.0), "S1": (0.0, 0.0), "A1": (3.04 * 3600, 3.04 * 3600)}
    for arm, (whole, split) in want.items():
        d = out["arms"][arm]["diagnostic"]
        assert math.isclose(d["whole"]["seconds"], whole, abs_tol=1e-9), arm
        assert math.isclose(d["split"]["seconds"], split, abs_tol=1e-9), arm
        assert math.isclose(d["whole"]["c_full_fre"], whole / FRE, abs_tol=1e-12)
        assert math.isclose(d["whole"]["c_lean_c0"], whole / c0, abs_tol=1e-12)
        assert d["whole"]["approximately_zero"] is (whole / FRE < 0.01)
        run = out["arms"][arm]["run"]["c_full_fre_mean"]
        assert math.isclose(out["arms"][arm]["total"]["whole"]["c_full_fre"], run + whole / FRE, rel_tol=1e-12)
        assert math.isclose(out["arms"][arm]["total"]["split"]["c_lean_c0"], 1.0 + split / c0, rel_tol=1e-12)
    assert "diagnostic" not in out["arms"]["R"] and "diagnostic" not in out["arms"]["a0"]
    assert out["arms"]["A1"]["diagnostic"]["retrain_s_reported_apart"] == pytest.approx(0.077 * 3600)
    for k, v in s.items():
        assert out["diagnostics_by_kind"][k]["seconds"] == v and out["diagnostics_by_kind"][k]["jobs"] == 1
    assert out["diagnostics_by_kind"]["c0"]["seconds"] == c0


def test_jobs_without_a_ledger_and_the_not_pulled_one(kits):
    kit, slots, plan = kits()
    out = ct.table(kit, "plan_a_block_a_only")
    retrain = [j for j in out["jobs"] if j["kind"] == "retrain"]
    assert len(retrain) == 1 and retrain[0]["ledger"] is None and retrain[0]["pulled"] is False
    assert "no cost ledger in the seal" in retrain[0]["why"]
    assert all(j["ledger"]["named_by_plan_outputs"] for j in out["jobs"] if j["ledger"] is not None)


def test_no_c0_leaves_c_lean_empty(kits):
    kit, slots, plan = kits(with_c0=False)
    out = ct.table(kit, "plan_a_block_a_only")
    assert out["units"]["c0"]["measured_s"] is None and "0 complete c0 job(s)" in out["units"]["c0"]["why"]
    assert out["arms"]["S4"]["run"]["c_lean_c0"] is None
    assert out["arms"]["S4"]["diagnostic"]["whole"]["c_lean_c0"] is None
    assert out["arms"]["S4"]["total"]["whole"]["c_lean_c0"] is None


def test_references_and_safe_lora_per_point(kits):
    kit, slots, plan = kits("plan_a")
    out = ct.table(kit, "plan_a")
    assert set(out["references"]) == {"ref-G", "ref-bqi"}
    assert out["references"]["ref-G"]["runs"]["1105"]["c_full_fre"] == slot_of(plan, slots, "ref_train", "G") / FRE
    assert out["references"]["ref-bqi"]["run"]["c_lean_c0"] == 1.0
    assert "training difference" in out["references"]["ref-bqi"]["run"]["c_lean_note"]
    assert "c_lean_note" not in out["arms"]["S1"]["run"]
    lora = [v for k, v in out["b10_references"].items() if k.startswith("safe_lora")][0]
    assert lora["per_point"]["default"]["seconds"] == 100.0 + 100.0
    assert lora["per_point"]["conditional"]["seconds"] == 110.0 + 110.0
    assert lora["per_point"]["certify"]["c_full_fre"] == (120.0 + 120.0) / FRE
    assert lora["a0_regeneration_reported_apart"]["seconds"] == 300.0
    assert lora["a0_regeneration_reported_apart"]["c_lean_c0"] == 300.0 / slot_of(plan, slots, "c0")
    ev = [v for k, v in out["b10_references"].items() if k.startswith("ref_eval")][0]
    assert ev["seconds"] == slot_of(plan, slots, "ref_eval") and ev["includes_a0_regeneration"] is True
    assert set(ev["per_point"]) == {"scale:0.9", "scale:0.75", "scale:0.5", "prefix"}
    assert all(p["seconds"] is not None and p["alternative_k5"]["seconds"] is None for p in ev["per_point"].values())
    assert "K8" in ev["per_point_c_full_why"] and "K5" in ev["per_point_c_full_why"]


def _job(plan, kind, seed=None):
    return next((h, i) for h, rec in sorted(plan["hosts"].items()) for i, j in enumerate(rec["jobs"])
                if j["kind"] == kind and (seed is None or j["seed"] == seed))


def test_ref_eval_points_have_rev4_813s_c_full_value(kits):
    """D1 (verifier round 2; the lead's R4.2): each ref_eval point's C-full cost = the matched a0 run's measured slot
    on the same seed - the frozen C-full training price (219.7 s) + the job ledger's transform stage, over 2,934 s
    (reading K8), with K5's "null: not stated" beside it; the a0 run is named."""
    kit, slots, plan = kits("plan_a")
    out = ct.table(kit, "plan_a")
    c0 = slot_of(plan, slots, "c0")
    ev = [v for k, v in out["b10_references"].items() if k.startswith("ref_eval")][0]
    assert ev["seed"] == 1105
    a0 = slot_of(plan, slots, "a0_arm", "a0", 1105)
    host, i = _job(plan, "a0_arm", 1105)
    want = a0 - 219.7 + 0.0
    for p in ("scale:0.9", "scale:0.75", "scale:0.5", "prefix"):
        rec = ev["per_point"][p]
        assert math.isclose(rec["seconds"], want, abs_tol=1e-9) and math.isclose(rec["c_full_fre"], want / FRE,
                                                                                   rel_tol=1e-12)
        assert rec["approximately_zero"] is False
        basis = rec["c_full_basis"]
        assert basis["a0_run"] == {"seed": 1105, "host": host, "index": i, "slot_s": a0}
        assert basis["full_training_s"] == 219.7 == out["units"]["full_training_s"] and basis["transform_s"] == 0.0
        assert math.isclose(basis["seconds_over_c0"], want / c0, rel_tol=1e-12) and "1 FRE" in basis["units"]
        assert "REV4:813" in basis["rule"] and "why" not in basis and "Safe LoRA only" in basis["transform_basis"]
        assert rec["alternative_k5"] == {"seconds": None, "c_full_fre": None, "why": ct.K5_NULL["why"]}
        assert "not stated" in rec["alternative_k5"]["why"] and "K5" in rec["alternative_k5"]["why"]
        assert rec["c_lean_seconds"] == c0 - 220.0 and rec["c_lean_c0"] == (c0 - 220.0) / c0     # K6 unchanged
    assert not math.isclose(want, ev["seconds"]) and ev["seconds"] == slot_of(plan, slots, "ref_eval")
    assert "K8" in out["readings"] and "REV4:813" in out["readings"]["K8"] and "REV4:774" in out["readings"]["K8"]
    assert any(r.startswith("REV4:774") for r in out["rule"])


def test_ref_eval_c_full_adds_the_ledgers_transform_stage(tmp_path):
    kit, slots, plan = ek.cost_kit(tmp_path, "plan_a")
    host, i = _job(plan, "ref_eval")
    _rewrite(kit, plan, host, i, fn=lambda d: d["stages_s"].update(transform=7.5))
    out = ct.table(kit, "plan_a")
    a0 = slot_of(plan, slots, "a0_arm", "a0", 1105)
    ev = [v for k, v in out["b10_references"].items() if k.startswith("ref_eval")][0]
    for rec in ev["per_point"].values():
        assert math.isclose(rec["seconds"], a0 - 219.7 + 7.5, abs_tol=1e-9)
        assert rec["c_full_basis"]["transform_s"] == 7.5


def test_a_ref_eval_point_without_an_a0_run_on_its_seed_is_null(tmp_path):
    """A ref_eval job at a seed whose a0 run is not in the stage-1 ledgers (1103: reused from Gate A) gets no C-full
    value, with the reason; its C-lean value (K6) stays; the per-reference mean lists the seed."""
    kit, slots, plan = ek.cost_kit(tmp_path, "plan_a")
    host, i = _job(plan, "ref_eval")
    plan["hosts"][host]["jobs"][i]["seed"] = 1103
    _rewrite(kit, plan, host, i, fn=lambda d: d.update(seed=1103))
    out = ct.table(kit, "plan_a")
    ev = [v for k, v in out["b10_references"].items() if k.startswith("ref_eval")][0]
    assert ev["seed"] == 1103 and "1103" not in out["arms"]["a0"]["runs"]
    for rec in ev["per_point"].values():
        assert rec["seconds"] is None and rec["c_full_fre"] is None and rec["approximately_zero"] is None
        assert rec["c_full_basis"]["a0_run"] is None and "seed 1103" in rec["c_full_basis"]["why"]
        assert "seconds_over_c0" not in rec["c_full_basis"] and rec["c_lean_c0"] is not None
        assert rec["alternative_k5"]["seconds"] is None
    per = out["b10_per_reference"]["ref_eval"]["prefix"]
    assert per["seeds"] == ["1103"] and per["jobs"] == 1 and per["c_full_fre_mean"] is None
    assert per["c_full_fre_min"] is None and per["seeds_without_c_full_fre"] == ["1103"]
    assert per["c_lean_c0_mean"] == ev["per_point"]["prefix"]["c_lean_c0"] and per["seeds_without_c_lean_c0"] == []


def test_per_reference_means_over_seeds(tmp_path):
    """The lead's R4.2: a per-reference mean over seeds (reading K8), per B10 kind and point, with min and max."""
    kit, slots, plan = ek.cost_kit(tmp_path, "plan_a", extra_ref_eval_seeds=(1106,))
    out = ct.table(kit, "plan_a")
    c0 = slot_of(plan, slots, "c0")
    evs = {v["seed"]: v for k, v in out["b10_references"].items() if k.startswith("ref_eval")}
    assert set(evs) == {1105, 1106}
    per = out["b10_per_reference"]
    assert set(per) == {"ref_eval", "safe_lora"} and set(per["ref_eval"]) == set(ct.REF_EVAL_MENU)
    vals = {j: (slot_of(plan, slots, "a0_arm", "a0", j) - 219.7) / FRE for j in (1105, 1106)}
    assert not math.isclose(vals[1105], vals[1106])                   # the kit tells the mean from either value
    for p, name in (("scale:0.9", "adapter scaling 0.9"), ("scale:0.75", "adapter scaling 0.75"),
                    ("scale:0.5", "adapter scaling 0.5"), ("prefix", "SP")):
        rec = per["ref_eval"][p]
        assert rec["seeds"] == ["1105", "1106"] and rec["jobs"] == 2 and rec["menu_name"].startswith(name)
        for j in (1105, 1106):
            assert math.isclose(evs[j]["per_point"][p]["c_full_fre"], vals[j], rel_tol=1e-12)
        assert math.isclose(rec["c_full_fre_mean"], (vals[1105] + vals[1106]) / 2, rel_tol=1e-12)
        assert math.isclose(rec["c_full_fre_min"], min(vals.values()), rel_tol=1e-12)
        assert math.isclose(rec["c_full_fre_max"], max(vals.values()), rel_tol=1e-12)
        assert rec["seeds_without_c_full_fre"] == [] and rec["seeds_without_c_lean_c0"] == []
        assert math.isclose(rec["c_lean_c0_mean"], (c0 - 220.0) / c0, rel_tol=1e-12)
        assert rec["c_lean_c0_min"] == rec["c_lean_c0_max"] == rec["c_lean_c0_mean"]
    lora = per["safe_lora"]
    assert set(lora) == {"default", "conditional", "certify"} and lora["default"]["seeds"] == ["1105"]
    assert lora["default"]["c_full_fre_mean"] == (100.0 + 100.0) / FRE and lora["default"]["menu_name"] == "Safe LoRA default"
    assert math.isclose(lora["certify"]["c_lean_c0_mean"], (120.0 + c0 - 220.0) / c0, rel_tol=1e-12)


def test_two_ref_eval_jobs_at_one_seed_refuse(tmp_path):
    kit, slots, plan = ek.cost_kit(tmp_path, "plan_a", extra_ref_eval_seeds=(1105,))
    with pytest.raises(Refusal, match="ref_eval at 1105: two complete jobs with a ledger"):
        ct.table(kit, "plan_a")


def test_the_full_training_price_is_the_selector_specs_and_rev4s_median():
    """REV4:813's "minus training" under C-full: the frozen C-full training price, the median training of R_1-R_3
    (REV4:804-806), as selector_spec.json's C-full convention holds it; not the lean 220 s."""
    assert ct.FULL_TRAINING_S == 219.7 == statistics.median((220.4, 219.7, 216.0))
    assert ct.FULL_TRAINING_S != ct.LEAN_TRAINING_S
    spec_path = sk.TREE / "scripts" / "stage1" / "settings" / "selector_spec.json"
    if not spec_path.is_file():
        pytest.skip("the selector spec is not in this tree")
    full = json.loads(spec_path.read_text())["cost_conventions"]["C-full"]
    assert full["training_s"] == ct.FULL_TRAINING_S and "median training of R_1-R_3" in full["stages"]


def test_the_kits_rules_behind_k8():
    """The kit runs each ref_eval job on block B's own a0 run at its seed, and its ledger's transform stage is Safe
    LoRA's timing only (so a ref_eval ledger's is 0)."""
    rules = sk.TREE / "runkit" / "stage1-olmo" / "stage1_rules.py"
    runner = sk.TREE / "runkit" / "stage1-olmo" / "setup" / "job_runner_stage1.py"
    if not rules.is_file() or not runner.is_file():
        pytest.skip("the kit is not in this tree")
    text = rules.read_text()
    assert 'SECOND_PHASE_KINDS = ("ref_eval", "safe_lora")' in text and "on block B's own a0 runs" in text
    runner_text = runner.read_text()
    assert "the transform stage is safe_lora_timing.json seconds.total" in runner_text
    assert '("-b10-run", "greedy_generation")' in runner_text and 'step.get("transform_seconds_total")' in runner_text


def test_k3_names_the_split_denominator_and_the_anchor_job(kits):
    """The lead's R4.2: K3's split denominator names DataShield-style; REV4:796's anchor job is named in the output."""
    kit, slots, plan = kits()
    out = ct.table(kit, "plan_a_block_a_only")
    k3 = out["readings"]["K3"]
    assert "DataShield-style" in k3 and "REQ-12" in k3 and "anchor job" in k3 and "charging.anchor_job" in k3
    ch = out["charging"]
    assert ch["split_denominator"] == ct.SPLIT_DENOMINATOR and "DataShield-style" in ch["split_denominator"]
    assert "upper" in ch["split_denominator"]
    anchor = ch["anchor_job"]
    assert anchor == ct.ANCHOR_JOB and "anchor-1" in anchor["what"] and "64 harmful + 64 safe" in anchor["what"]
    assert anchor["charged_here"] is None and "REV4:796" in anchor["why"] and "A1" in anchor["serves"]
    assert "L1" in anchor["serves"] and "2.2 min" in anchor["why"]
    assert ch["map"] == {"L1": ["l1_scan", "rep_pass"], "S3": ["untuned_answers", "rep_pass"], "S4": ["untuned_answers"]}


def test_b10_c_lean_is_the_lean_state_not_the_full_evaluation(kits):
    """D1 (verifier round 1): under C-lean a B10 state is one lean state (the measured c0 less the frozen lean training
    price) plus its transform, never the measured full evaluation / c0 (REV4:813, :825; reading K6)."""
    kit, slots, plan = kits("plan_a")
    out = ct.table(kit, "plan_a")
    c0 = slot_of(plan, slots, "c0")
    lean = c0 - 220.0
    assert out["units"]["c0"]["lean_state_s"] == lean and out["units"]["c0"]["lean_training_s"] == 220.0
    lora = [v for k, v in out["b10_references"].items() if k.startswith("safe_lora")][0]
    for k, p in enumerate(("default", "conditional", "certify")):
        rec = lora["per_point"][p]
        assert rec["seconds"] == 2 * (100.0 + 10 * k)
        assert math.isclose(rec["c_lean_seconds"], 100.0 + 10 * k + lean, abs_tol=1e-9)
        assert math.isclose(rec["c_lean_c0"], (100.0 + 10 * k + lean) / c0, rel_tol=1e-12)
    slot = slot_of(plan, slots, "safe_lora")
    assert lora["seconds"] == slot and lora["c_full_fre"] == slot / FRE and lora["c_lean_why"] is None
    assert math.isclose(lora["c_lean_seconds"], slot - (100.0 + 110.0 + 120.0) + 3 * lean, abs_tol=1e-9)
    assert math.isclose(lora["c_lean_c0"], lora["c_lean_seconds"] / c0, rel_tol=1e-12)
    ev = [v for k, v in out["b10_references"].items() if k.startswith("ref_eval")][0]
    assert ev["c_lean_seconds"] is None and ev["c_lean_c0"] is None and "per point only" in ev["c_lean_why"]
    for rec in ev["per_point"].values():
        assert rec["c_lean_seconds"] == lean and math.isclose(rec["c_lean_c0"], lean / c0, rel_tol=1e-12)
    for rec in (lora, ev, *lora["per_point"].values()):
        if rec["seconds"] is not None and rec["c_lean_c0"] is not None:
            assert not math.isclose(rec["c_lean_c0"], rec["seconds"] / c0, rel_tol=1e-9)
    assert not {"ref_eval", "safe_lora"} & set(out["diagnostics_by_kind"])
    cert = out["diagnostics_by_kind"]["b10_certify"]
    assert cert["seconds"] == slot_of(plan, slots, "b10_certify") and cert["c_lean_c0"] == cert["seconds"] / c0
    assert cert["c_lean_basis"] == ct.BY_KIND_BASIS and "study cost" in ct.BY_KIND_BASIS
    assert "K6" in out["readings"] and "K7" in out["readings"]


def test_b10_c_lean_needs_a_lean_state(tmp_path):
    kit, slots, plan = ek.cost_kit(tmp_path, "plan_a")
    host, i = next((h, i) for h, rec in sorted(plan["hosts"].items()) for i, j in enumerate(rec["jobs"])
                   if j["kind"] == "c0")
    _rewrite(kit, plan, host, i, fn=lambda d: d.update(slot_s=200.0))
    out = ct.table(kit, "plan_a")
    assert out["units"]["c0"]["measured_s"] == 200.0 and out["units"]["c0"]["lean_state_s"] is None
    assert "not above the frozen lean training price" in out["units"]["c0"]["lean_state_why"]
    for rec in out["b10_references"].values():
        assert rec["c_lean_c0"] is None and all(p["c_lean_c0"] is None for p in rec["per_point"].values())
        assert rec["c_full_fre"] == rec["seconds"] / FRE
    lora = [v for k, v in out["b10_references"].items() if k.startswith("safe_lora")][0]
    assert lora["c_lean_why"] == "no lean state (units.c0)"


def test_b10_c_lean_without_c0(kits):
    kit, slots, plan = kits("plan_a", with_c0=False)
    out = ct.table(kit, "plan_a")
    assert out["units"]["c0"]["lean_state_s"] is None
    lora = [v for k, v in out["b10_references"].items() if k.startswith("safe_lora")][0]
    assert lora["c_lean_c0"] is None and lora["c_lean_why"] == "no measured c0"
    assert all(p["c_lean_c0"] is None and p["c_full_fre"] is not None for p in lora["per_point"].values())


@pytest.mark.parametrize("change", [
    lambda d: d.update(steps=[s for s in d["steps"] if not s["name"].endswith("-evaluate-certify")]),
    lambda d: d.update(steps=d["steps"] + [s for s in d["steps"] if s["name"].endswith("-transform-default")]),
], ids=["a missing evaluate step", "a second transform step"])
def test_a_safe_lora_point_without_its_own_steps_refuses(tmp_path, change):
    kit, slots, plan = ek.cost_kit(tmp_path, "plan_a")
    host, i = next((h, i) for h, rec in sorted(plan["hosts"].items()) for i, j in enumerate(rec["jobs"])
                   if j["kind"] == "safe_lora")
    _rewrite(kit, plan, host, i, fn=change)
    with pytest.raises(Refusal, match="does not name one transform and one evaluate step of each point"):
        ct.table(kit, "plan_a")


def test_the_median_stage1_r_slot_is_printed_beside_fre(kits):
    """D2 (verifier round 1): REV4:632's median of all stage-1 R arms, beside the fixed 1 FRE (reading K7)."""
    for reading in ("plan_a_block_a_only", "plan_a"):
        kit, slots, plan = kits(reading)
        out = ct.table(kit, reading)
        r = [slots[(h, i)] for h, rec in sorted(plan["hosts"].items()) for i, j in enumerate(rec["jobs"])
             if j["kind"] == "arm" and j["arm"] == "R"]
        beside = out["units"]["fre_beside"]
        assert out["units"]["fre_s"] == FRE and beside["r_runs"] == len(r) == len(out["arms"]["R"]["runs"])
        assert beside["median_slot_s"] == statistics.median(r) and beside["median_slot_fre"] == statistics.median(r) / FRE
        assert "never re-estimated" in beside["report_only"] and "REV4:632" in beside["rule"]
        if len(r) > 2:
            assert not math.isclose(statistics.median(r), statistics.fmean(r))     # the kit tells median from mean


def test_the_split_counts_only_the_readings_arms(kits):
    """The verifier's note 3: under plan B (no L1, no S3) S4 alone uses the untuned answers."""
    kit, slots, plan = kits("plan_b")
    out = ct.table(kit, "plan_b")
    s4 = out["arms"]["S4"]["diagnostic"]
    untuned = slot_of(plan, slots, "untuned_answers")
    assert s4["kinds"] == {"untuned_answers": {"jobs": 1, "shared_with": ["S4"]}}
    assert s4["whole"]["seconds"] == untuned and s4["split"]["seconds"] == untuned
    assert not {"L1", "S3"} & set(out["arms"]) and out["diagnostics_by_kind"]["rep_pass"]["jobs"] == 1
    assert out["arms"]["A1"]["diagnostic"]["whole"]["seconds"] == 3.04 * 3600


def test_a_kind_with_no_complete_job_is_not_zero(tmp_path):
    """The verifier's note 5: a charged kind whose jobs all crashed prints no seconds, and its arm no charge."""
    kit, slots, plan = ek.cost_kit(tmp_path)
    host, i = next((h, i) for h, rec in sorted(plan["hosts"].items()) for i, j in enumerate(rec["jobs"])
                   if j["kind"] == "l1_scan")
    plan["hosts"][host]["jobs"][i]["status"] = "crashed"
    (kit / "plan.json").write_bytes(sk.jbytes(plan))
    out = ct.table(kit, "plan_a_block_a_only")
    k = out["diagnostics_by_kind"]["l1_scan"]
    assert k["seconds"] is None and k["approximately_zero"] is None and k["jobs"] == 0 and "no complete job" in k["why"]
    l1 = out["arms"]["L1"]
    assert l1["diagnostic"]["whole"] is None and l1["diagnostic"]["split"] is None
    assert "l1_scan" in l1["diagnostic"]["why"] and l1["total"] == {"whole": None, "split": None}
    assert out["arms"]["S3"]["diagnostic"]["whole"]["seconds"] == (slot_of(plan, slots, "untuned_answers") +
                                                                   slot_of(plan, slots, "rep_pass"))


def test_mac_arms_carry_the_note(kits):
    kit, slots, plan = kits()
    out = ct.table(kit, "plan_a_block_a_only")
    for arm in ("H1", "S1"):
        d = out["arms"][arm]["diagnostic"]
        assert d["note"] == ct.MAC_NOTE and d["whole"]["seconds"] == 0.0 and d["kinds"] == {}
    assert "note" not in out["arms"]["L1"]["diagnostic"]


def test_the_lean_training_price_is_the_selector_specs():
    spec_path = sk.TREE / "scripts" / "stage1" / "settings" / "selector_spec.json"
    if not spec_path.is_file():
        pytest.skip("the selector spec is not in this tree")
    lean = json.loads(spec_path.read_text())["cost_conventions"]["C-lean"]
    assert lean["contents"] == "a" and lean["variants"]["a"]["training_s"] == ct.LEAN_TRAINING_S
    assert lean["variants"]["b"]["training_s"] == ct.LEAN_TRAINING_S


def test_only_readable_cost_ledgers_are_opened(kits, monkeypatch):
    kit, slots, plan = kits()
    opened = []
    real = Path.read_bytes

    def spy(self):
        opened.append(self)
        return real(self)
    monkeypatch.setattr(Path, "read_bytes", spy)
    ct.table(kit, "plan_a_block_a_only")
    names = {p.name for p in opened if str(p).startswith(str(kit))}
    assert names == {"plan.json", "block-A.json", "cost-ledger.json"}
    assert not any(ek.SENTINEL in real(p).decode(errors="ignore") for p in opened if str(p).startswith(str(kit)))


def _rewrite(kit: Path, plan: dict, host: str, i: int, fn=None, cls=None, seal=True, plan_digest=True):
    """Change job I of HOST's ledger (fn on its document) and/or its seal class; re-take the hashes asked for."""
    path = kit / "retrieved" / host / "tree" / f"job-{i}" / "cost-ledger.json"
    if fn is not None:
        doc = json.loads(path.read_text())
        fn(doc)
        path.write_bytes(sk.jbytes(doc))
    if plan_digest:
        plan["hosts"][host]["jobs"][i]["outputs"][f"job-{i}/cost-ledger.json"] = sk.sha(path.read_bytes())
    block = plan["hosts"][host]["block"]
    if seal:
        ek.seal(kit, plan, block)
    if cls is not None:
        seal_path = kit / "seals" / f"block-{block}.json"
        doc = json.loads(seal_path.read_text())
        for f in doc["files"]:
            if f["host"] == host and f["path"] == f"job-{i}/cost-ledger.json":
                f["class"] = cls
        data = sk.jbytes(doc)
        seal_path.write_bytes(data)
        plan["seals"][block]["sha256"] = sk.sha(data)
    (kit / "plan.json").write_bytes(sk.jbytes(plan))


@pytest.mark.parametrize("change,match", [
    (dict(cls="sealed"), "does not class its cost ledger readable"),
    (dict(fn=lambda d: d.update(arm="S3")), "its arm differ"),
    (dict(fn=lambda d: d.update(index=9)), "its index differ"),
    (dict(fn=lambda d: d["stages_s"].pop("transform")), "not the runner's 8 stages"),
    (dict(fn=lambda d: d.update(slot_s=-1.0)), "slot_s is negative"),
    (dict(fn=lambda d: d.update(slot_s=True)), "slot_s is not a finite number"),
    (dict(fn=lambda d: d.update(kind="x")), "is not a version-1 'stage1 cost ledger'"),
    (dict(fn=lambda d: d["steps"].append({"seconds": 1.0})), "its steps are not named"),
    (dict(fn=lambda d: d.update(slot_s=1.0), seal=False, plan_digest=False), "hashes to"),
    (dict(fn=lambda d: d.update(slot_s=2.0), plan_digest=False), "plan.json and block A's seal name two SHA-256"),
])
def test_ledger_refusals(tmp_path, change, match):
    kit, slots, plan = ek.cost_kit(tmp_path)
    host, i = next((h, i) for h, rec in sorted(plan["hosts"].items()) for i, j in enumerate(rec["jobs"])
                   if j["kind"] == "arm" and j["arm"] == "S1")
    _rewrite(kit, plan, host, i, **change)
    with pytest.raises(Refusal, match=match):
        ct.table(kit, "plan_a_block_a_only")


def test_a_complete_job_without_a_ledger_refuses(tmp_path):
    kit, slots, plan = ek.cost_kit(tmp_path)
    (kit / "retrieved" / "a-1" / "tree" / "job-1" / "cost-ledger.json").unlink()
    ek.seal(kit, plan, "A")
    (kit / "plan.json").write_bytes(sk.jbytes(plan))
    with pytest.raises(Refusal, match="a-1 job 1: a complete, pulled job whose cost ledger is not in block A's seal"):
        ct.table(kit, "plan_a_block_a_only")


def test_two_runs_of_one_cell_refuse(tmp_path):
    kit, slots, plan = ek.cost_kit(tmp_path)
    host, i = next((h, i) for h, rec in sorted(plan["hosts"].items()) for i, j in enumerate(rec["jobs"])
                   if j["kind"] == "arm" and j["arm"] == "H1" and j["seed"] == 1103)
    other = next((h, k) for h, rec in sorted(plan["hosts"].items()) for k, j in enumerate(rec["jobs"])
                 if j["kind"] == "arm" and j["arm"] == "H1" and j["seed"] == 1102)
    plan["hosts"][other[0]]["jobs"][other[1]]["seed"] = 1103
    _rewrite(kit, plan, other[0], other[1], fn=lambda d: d.update(seed=1103))
    with pytest.raises(Refusal, match="H1 at 1103: two complete runs with a ledger"):
        ct.table(kit, "plan_a_block_a_only")


def test_the_stage_names_are_the_runners():
    runner = sk.TREE / "runkit" / "stage1-olmo" / "setup" / "job_runner_stage1.py"
    if not runner.is_file():
        pytest.skip("the kit's job runner is not in this tree")
    tree = ast.parse(runner.read_text())
    values = {t.id: node.value for node in tree.body if isinstance(node, ast.Assign) for t in node.targets
              if isinstance(t, ast.Name)}
    assert ast.literal_eval(values["LEDGER_STAGES"]) == ct.LEDGER_STAGES
    assert ast.literal_eval(values["LEDGER_FILE"]) == ct.LEDGER_FILE
    seal = (sk.TREE / "runkit" / "stage1-olmo" / "seal.py").read_text()
    assert '"*cost-ledger*.json"' in seal
    rules = (sk.TREE / "runkit" / "stage1-olmo" / "stage1_rules.py").read_text()
    assert "FRE_S = 2934 " in rules


def test_the_pinned_rule_texts_are_rev4s():
    rev4 = (sk.TREE / "research" / "experiments" / "2026-10-17-stage1-preregistration-rev3" /
            "stage1-preregistration-rev4.md")
    if not rev4.is_file():
        pytest.skip("the pre-registration is not in this tree")
    text = rev4.read_text()
    for needle in ("**1 FRE = 2,934 s**", '"≈ 0" only below 0.01 FRE', "A1 is priced only from the wave-0b ledger",
                   "each scorer that uses the shared representation pass is charged the whole pass, with the shared "
                   "split as a second number", "the diagnostics took 3.04 h against a frozen upper of 2.0 h; the "
                   "retrain 0.077 h", "REQ-3 and REQ-10 for L1", "REQ-9 for S3 and S4",
                   "fixed at W1-P and never re-estimated; the median of all stage-1 R arms is reported beside it "
                   "(LW-16).", "**C-full:** §7.3. For an evaluation-only reference: the same minus training, plus its "
                   "transform.", "| One evaluation-only state | 0.93 FRE | 0.75 c0 |",
                   "| a0 adapter regeneration, per seed | 0.094 FRE (0.077 h measured) | 0.32 c0 | $0.14 (3 seeds "
                   "$0.41); a study cost |", "The c0 column is in the dev-100 form",
                   "**Lean prices** are frozen at W1-P from the three wave-0a ledgers (LW-16).",
                   "| B+Qi, 6 seeds | 6.2–6.3 FRE | 6.7–6.9 c0 |",
                   "report every arm in the menu with its label, O, L and cost under both conventions",
                   "| Sp | every arm; SP, adapter scaling, Safe LoRA, recipe G, B+Qi, B↓LR |",
                   "Every pool filter, untuned-answer generation, anchor job and scorer is charged in full",
                   "| R_1, 1101 | 2,910 | 220.4 |", "| R_2, 1102 | 2,906 | 219.7 |", "| R_3, 1103 | 2,573 | 216.0 |",
                   "Pod overhead: 18.9 min on w0a-1 and 26.0 min on anchor-1."):
        assert needle in text, needle
    lines = text.splitlines()
    for number, start in ((632, "- **1 FRE = 2,934 s**"), (813, "- **C-full:** §7.3."), (823, "| a0 adapter"),
                          (825, "| One evaluation-only state"), (827, "| B+Qi, 6 seeds"), (636, "- **Lean prices**"),
                          (774, "  Rules (RB R3.2"), (770, "  | Sp |"), (796, "- Every pool filter"),
                          (805, "| R_2, 1102 |"), (808, "- Each ledger's `generate` stage")):
        assert lines[number - 1].startswith(start), number


def test_command_line(kits, tmp_path, capsys):
    kit, slots, plan = kits()
    out = tmp_path / "cost.json"
    args = ["--kit", str(kit), "--reading", "plan_a_block_a_only", "--out", str(out)]
    assert ct.main(args) == 0
    assert capsys.readouterr().out == f"wrote {out} sha256 {sk.sha(out.read_bytes())}\n"
    doc = json.loads(out.read_text())
    assert doc["provenance"]["kit"]["plan_sha256"] == sk.sha((kit / "plan.json").read_bytes())
    assert ct.main(args) == 2 and "cost.json exists" in capsys.readouterr().err
