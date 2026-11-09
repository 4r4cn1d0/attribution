"""KCR §10 tests 1-15 for the 7-8B cap rule (rules_78b.py, derive_78b_basis.py, measured-basis-78b.json), with the
adaptations the T2 brief names: test 10 to the zero Gate B hold (KD4); test 11 to the stage-1 kit's budget.py
KITS_GLOB (read, never edited) and the shared lock tmp/family-probe-budget.lock; test 12 on the function the T4 job
runner calls (job_decision / pod_dry_run); test 14 to what stays frozen now (the engine identity, the stage-1 kit's
rules and budget files by SHA-256, no Gate B import, no __pycache__); test 15 with an audit hook on every open.

Run on the Mac, CPU only, no pod and no network:

    PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_rules_78b.py

Tests that read the 17 measured kits' records (the real tmp/family-probe-sp-* folders of the main checkout) skip
when that root is absent; the basis file carries their values either way. A git check of the working tree is the
lead's separate guard command (RULES-78B.md), not a test here.

The fix round (5 Nov, verify-A's A-V1..A-V6, the addendum's A1, the T4 interface) added tests 05c, 05d, 07b, 10b, 12b
and the A-V6 cases of test 15; tests 3, 7 and 12 changed with the fixes.
"""
from __future__ import annotations

import ast
import datetime as dt
import fnmatch
import hashlib
import importlib.util
import inspect
import json
from fractions import Fraction
import math
import pathlib
import re
import shutil
import sys

import pytest

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE.parent                                   # runkit/stage1-78b
ROOT = KIT.parents[1]                               # the repository root this kit sits in
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))
import rules_78b as R                               # noqa: E402
import derive_78b_basis as D                        # noqa: E402

STAGE1 = ROOT / "runkit" / "stage1-olmo"
# The stage-1 kit files this kit copies helpers from and reads, at fb51421 (M: shasum -a 256; test 14 holds them).
STAGE1_PINS = {"stage1_rules.py": "d52614e42bbde1f28e9a2c8b202306a6707d53312336413b371bc28820630a19",
               "budget.py": "f4760c080159e70371f528b7f0349b695858f7f320956568a02818d6c89963b0"}
MEASURED_ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp")   # the 17 kits (read-only, absolute path)

# KCR §4 and §7 (R: KCR:100, :103, :119, :165-177, :185-188), the review's values.
KCR = {
    "olmo2-7b": {"gen_allcap": 8264, "upper_38": 10565, "req_38": 12365, "req_33": 12243, "measured_upper": 7418,
                 "caps": {1: 4.25, 2: 6.5, 3: 8.5, 4: 10.5}, "guards": {1: 13.86, 2: 18.03, 3: 21.73, 4: 25.43},
                 "spend_1": 5.12, "spend_4": 16.18, "per_arm_4": 4.05, "slowest_job": 6450, "f_pre_max": 8301},
    "llama31-8b": {"gen_allcap": 8510, "upper_38": 10813, "req_38": 12613, "req_33": 12499, "measured_upper": 9736,
                   "caps": {1: 4.5, 2: 7.25, 3: 9.75, 4: 12.5}, "guards": {1: 14.33, 2: 19.41, 3: 24.04, 4: 29.13},
                   "spend_1": 6.27, "spend_4": 20.80, "per_arm_4": 5.20, "slowest_job": 8466, "f_pre_max": 9393},
}


def load_by_path(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def basis() -> dict:
    return R.load_basis()


@pytest.fixture(scope="module")
def stage1():
    """runkit/stage1-olmo/stage1_rules.py loaded by path (never edited; no bytecode written)."""
    assert sys.dont_write_bytecode
    return load_by_path("stage1_rules_under_test", STAGE1 / "stage1_rules.py")


def arms(family, n):
    return R.arm_pod(family, [33] * (n - 1) + [38])


# ----------------------------------------------------------------------------------------------------- test 1
def test_01_golden_numbers_equal_kcr_4_and_7():
    for family, g in KCR.items():
        # KCR's own arithmetic from its printed constants reproduces its printed integers exactly.
        c = R.KCR_PRINTED[family]
        assert round(R.gen_allcap_of(c)) == g["gen_allcap"]
        assert round(R.upper_m_of(c, 38)) == g["upper_38"]
        assert round(R.upper_m_of(c, 38) + R.START_MARGIN_S) == g["req_38"]
        assert round(R.upper_m_of(c, 33) + R.START_MARGIN_S) == g["req_33"]
        # The rule's constants are the exact basis maxima; its requirements are within 1.2 s of KCR's.
        assert abs(R.requirement_s(family, 38) - g["req_38"]) <= 1.2
        assert abs(R.requirement_s(family, 33) - g["req_33"]) <= 1.2
        assert abs(R.measured_upper_s(family) - g["measured_upper"]) <= 0.5 + 1e-6   # KCR prints 7,418 / 9,736
        assert R.measured_upper_s(family) == pytest.approx(1.15 * g["slowest_job"])
        # Caps, guards and spend uppers equal KCR §7 and §8 to the cent (half-up).
        for n in range(1, 5):
            jobs = arms(family, n)
            assert R.cap_hours(jobs) == g["caps"][n], (family, n)
            assert R.cents(R.guard_usd(R.cap_hours(jobs))) == g["guards"][n], (family, n)
        assert R.cents(R.pod_spend_usd(arms(family, 1))) == g["spend_1"]
        assert R.cents(R.pod_spend_usd(arms(family, 4))) == g["spend_4"]
        assert R.cents(R.pod_spend_usd(arms(family, 4)) / 4) == g["per_arm_4"]
    # KCR §7's note: with only 33-step arms the Llama 2-arm cap stays 7.00 h.
    assert R.cap_hours(R.arm_pod("llama31-8b", [33, 33])) == 7.0
    assert R.cap_hours(R.arm_pod("olmo2-7b", [33, 33])) == 6.5
    # KCR:177, block 0: guard $44.85, spend upper $33.30, need $56.06 with the contingency.
    report = R.block0_report()["n"]
    assert [p["cap_hours"] for p in report["pods"]] == [8.5, 12.5]
    assert report["guard_usd"] == 44.85 and report["base_need_usd"] == 44.85
    assert report["spend_upper_usd"] == 33.30 and report["need_usd"] == 56.06
    assert [p["spend_usd"] for p in report["pods"]] == [12.50, 20.80]


def test_01b_golden_table_command_prints_the_same():
    table = R.golden_table()
    for family, g in KCR.items():
        assert table[family]["caps_h"] == g["caps"]
        assert table[family]["guards_usd"] == g["guards"]


# ----------------------------------------------------------------------------------------------------- test 2
def test_02_basis_pin_and_constants(basis, tmp_path):
    assert R.basis_sha256() == R.BASIS_SHA256
    assert basis["kind"] == "measured-basis-78b" and len(basis["units"]) == 17
    changed = tmp_path / "basis.json"
    changed.write_text(json.dumps(basis) + "\n")
    with pytest.raises(R.Refused):
        R.load_basis(changed)
    for family, f in R.FAMILIES.items():
        fam = basis["families"][family]
        assert fam["n_units"] == f["basis_units"] and fam["n_fine_tune_only"] == f["basis_fine_tune_only"]
        for constant, field in R.BASIS_MAXIMA.items():
            assert math.isclose(f[constant], fam[field], rel_tol=0, abs_tol=1e-9), (family, constant)
        units = [u for u in basis["units"] if u["family"] == family]
        smallest = min(u["ledger"]["train_padded_tokens"] / u["ledger"]["train_steps"] for u in units)
        assert abs(f["A0_PADDED_TOKENS_PER_STEP"] - smallest) < 0.01
        # Recompute each maximum from the unit records themselves (not the families block).
        assert f["TRAIN_STEP_MAX_S"] == max(u["ledger"]["train_s_per_step"] for u in units)
        assert f["FIRST_BATCH_MAX_S"] == max(u["first_greedy_batch_s"] for u in units)
        assert f["BATCH_MAX_S"] == max(u["capped32_batch_max_s"] for u in units)
        assert f["EARLY_MAX_S"] == max(u["ledger"]["early_s"] for u in units)
        assert f["OUTSIDE_MAX_S"] == max(u["outside_s"] for u in units)
        assert f["ARM_JOB_MAX_S"] == max(u["outer_job_s"] for u in units if not u["outer_includes_untuned_evaluation"])
        assert f["ARM_JOB_MAX_S"] == KCR[family]["slowest_job"]
        assert f["PRE_TRAINING_S_MAX"] == max(u["preflight"]["training_s"] for u in units)
        assert f["PRE_MS_PER_STEP_MAX"] == max(u["preflight"]["ms_per_step_full"] for u in units)
        # SCORE_ALLCAP >= 3 x the largest scoring time and >= the linear-fit all-capped value.
        assert R.SCORE_ALLCAP_S >= 3 * fam["scoring_max_s"]
        fit = fam["scoring_fit"]
        if family == "llama31-8b":
            assert R.SCORE_ALLCAP_S >= fit["all_capped_total_s"] > 1100
        else:                                   # KCR §4: OLMo's own guard fits are confounded; use Llama's guard slopes
            llama = basis["families"]["llama31-8b"]["scoring_fit"]
            mixed = (llama["all_capped_s"]["guard"] + llama["all_capped_s"]["guard_samples"]
                     + fit["all_capped_s"]["harm_scores"] + fit["fixed_stages_max_s"])
            assert R.SCORE_ALLCAP_S >= mixed > 1000
        # Keys recorded by every unit: engine X, the family's manifest, the GPU, the price, the recipes.
        assert fam["engine_sha256"] == [R.ENGINE_X]
        assert fam["manifest_sha256"] == [R.MANIFESTS[family]]
        assert fam["gpu_name"] == [R.GPU_NAME] and fam["cost_per_hr"] == [R.GPU_PRICE_USD]
        labels = fam["recipe_sha256_by_label"]
        main_label = "b" if family == "olmo2-7b" else "b5e5"
        other_label = "b5e5" if family == "olmo2-7b" else "b"
        assert labels[main_label] == [R.CONFIGS[family]["main"][1]]
        assert labels["g"] == [R.CONFIGS[family]["g"][1]]
        assert labels[other_label] == [R.CONFIGS[family]["other_lr"][1]]


def test_02b_basis_re_derives_byte_for_byte_from_the_measured_root():
    if not MEASURED_ROOT.is_dir() or not (MEASURED_ROOT / D.UNIT_KITS["olmo2-7b"][0]).is_dir():
        pytest.skip("the measured kits are not under this checkout's tmp/")
    data = D.canonical(D.derive(MEASURED_ROOT))
    assert hashlib.sha256(data).hexdigest() == R.BASIS_SHA256
    assert data == R.basis_path().read_bytes()


# ----------------------------------------------------------------------------------------------------- test 3
def test_03_every_measured_unit_is_below_upper_m_38(basis):
    for u in basis["units"]:
        upper = R.upper_m_s(u["family"], 38)
        assert u["outer_job_s"] <= upper, u["unit"]
        own = D.all_capped_s(u, R.SCORE_ALLCAP_S)
        assert own <= upper, (u["unit"], own, upper)
        # The all-capped time at BATCH_MAX and FIRST_BATCH_MAX (not the unit's own batches) stays at or under the
        # bound: the unit's own training, early and outside seconds are at most the family maxima (A-V5: the
        # assertion binds; 0.01 s covers the 4-dp rounding of TRAIN_STEP_MAX x 38 steps).
        at_max = D.all_capped_s({**u, "capped32_batch_max_s": R.FAMILIES[u["family"]]["BATCH_MAX_S"],
                                 "first_greedy_batch_s": R.FAMILIES[u["family"]]["FIRST_BATCH_MAX_S"]},
                                R.SCORE_ALLCAP_S)
        assert at_max <= upper + 0.01, (u["unit"], at_max, upper)
        assert at_max > own - 1e-9, u["unit"]                            # raising the batches to the maxima never lowers it
    # KCR:103: the slowest jobs against the bounds.
    assert R.FAMILIES["olmo2-7b"]["ARM_JOB_MAX_S"] == 6450 < R.upper_m_s("olmo2-7b", 38)
    assert R.FAMILIES["llama31-8b"]["ARM_JOB_MAX_S"] == 8466 < R.upper_m_s("llama31-8b", 38)


# ----------------------------------------------------------------------------------------------------- test 4
def test_04_speed_factor(basis):
    for u in basis["units"]:
        assert R.speed_factor(u["family"], u["preflight"]) == 1.0, u["unit"]
    f = R.FAMILIES["olmo2-7b"]
    base = {"training_s": f["PRE_TRAINING_S_MAX"], "ms_per_step_full": f["PRE_MS_PER_STEP_MAX"]}
    assert R.speed_factor("olmo2-7b", base) == 1.0
    slow = {**base, "training_s": f["PRE_TRAINING_S_MAX"] * 1.1}
    assert math.isclose(R.speed_factor("olmo2-7b", slow), 1.1)
    slow_ms = {**base, "ms_per_step_full": f["PRE_MS_PER_STEP_MAX"] * 1.12}
    assert math.isclose(R.speed_factor("olmo2-7b", slow_ms), 1.12)
    fast = {"training_s": f["PRE_TRAINING_S_MAX"] * 0.5, "ms_per_step_full": f["PRE_MS_PER_STEP_MAX"] * 0.5}
    assert R.speed_factor("olmo2-7b", fast) == 1.0
    req = R.requirement_s("olmo2-7b", 38)
    assert R.requirement_s("olmo2-7b", 38, s_pod=1.1) > req
    assert math.isclose(R.requirement_s("olmo2-7b", 38, s_pod=1.1), 1.1 * R.upper_m_s("olmo2-7b", 38) + 1800)
    assert R.requirement_s("olmo2-7b", 38, s_pod=0.5) == req           # a faster pod never lowers the bound
    assert R.requirement_s("olmo2-7b", 38, s_pod=0.5, s_obs=0.5) == req   # nor do both factors below 1 together
    assert R.requirement_s("olmo2-7b", 38, s_pod=0.9, s_obs=0.95) == req
    with pytest.raises(R.Refused):
        R.speed_factor("olmo2-7b", {**base, "training_s": f["PRE_TRAINING_S_MAX"] * 1.1501})
    assert R.speed_factor("olmo2-7b", {**base, "training_s": f["PRE_TRAINING_S_MAX"] * 1.15}) == pytest.approx(1.15)
    for bad in ({}, {"training_s": 1000.0}, {"ms_per_step_full": 200.0}, {**base, "training_s": 0},
                {**base, "training_s": -5.0}, {**base, "ms_per_step_full": float("nan")},
                {**base, "ms_per_step_full": float("inf")}, {**base, "training_s": None},
                {**base, "training_s": "1000"}, {**base, "training_s": True}, None, []):
        with pytest.raises(R.Refused):
            R.speed_factor("olmo2-7b", bad)


# ----------------------------------------------------------------------------------------------------- test 5
def progress_from(unit: dict, factor: float = 1.0, first_factor: float = 1.0) -> list:
    """Progress rows rebuilt from a basis unit's batch records (elapsed_s cumulative), optionally slowed."""
    rows, t = [{"kind": "train", "step": 38, "elapsed_s": 900.0}], 1000.0
    for series in ("greedy", "sampled"):
        for b in unit["batches"][series]:
            scale = first_factor if (series == "greedy" and b["batch"] == 0) else factor
            t = round(t + b["seconds"] * scale, 3)
            rows.append({"kind": "generate", "batch": b["batch"], "rows": b["rows"], "capped": b["capped"],
                         "output_tokens": b["output_tokens"], "elapsed_s": t})
    return rows


def test_05_in_pod_speed_check(basis):
    for u in basis["units"]:
        assert R.s_obs_from_progress(u["family"], progress_from(u)) == 1.0, u["unit"]
    u = next(x for x in basis["units"] if x["unit"] == "sp-olmo2-7b-1103")
    slow = R.s_obs_from_progress("olmo2-7b", progress_from(u, factor=2.3))
    assert math.isclose(slow, 2.3 * u["capped32_batch_max_s"] / R.FAMILIES["olmo2-7b"]["BATCH_MAX_S"], rel_tol=1e-6)
    assert slow > 2.2 and R.s_obs_defers(slow)
    req = R.requirement_s("olmo2-7b", 33)
    assert R.requirement_s("olmo2-7b", 33, s_obs=slow) > req
    assert math.isclose(R.requirement_s("olmo2-7b", 33, s_obs=slow), slow * R.upper_m_s("olmo2-7b", 33) + 1800)
    assert R.requirement_s("olmo2-7b", 33, s_pod=1.05, s_obs=1.02) == R.requirement_s("olmo2-7b", 33, s_pod=1.05)
    # The first greedy batch is excluded: a 10x slower first batch changes nothing.
    assert R.s_obs_from_progress("olmo2-7b", progress_from(u, first_factor=10.0)) == 1.0
    # 1.10 raises the later arms' requirement but does not defer; above 1.15 defers.
    mild = R.s_obs_from_progress("olmo2-7b", progress_from(u, factor=1.10))
    assert 1.05 < mild <= 1.15 and not R.s_obs_defers(mild)
    assert R.s_obs_defers(1.1501) and not R.s_obs_defers(1.15)
    for bad in ([], None, [{"kind": "train"}], [{"kind": "generate", "batch": 0, "elapsed_s": 5.0}]):
        with pytest.raises(R.Refused):
            R.s_obs_from_progress("olmo2-7b", bad)
    with pytest.raises(R.Refused):
        R.s_obs_from_progress("olmo2-7b", [{"kind": "generate", "batch": 0, "elapsed_s": 1.0, "capped": 1, "rows": 32},
                                           {"kind": "generate", "batch": 1, "elapsed_s": None, "capped": 1, "rows": 32}])


def test_05c_s_obs_refuses_a_drifted_progress_format():
    """A-V1: a present progress file whose generate rows lack ``capped`` or ``rows`` refuses (it must not pass as
    s_obs = 1 and disable KD11); so does a file with no 32-row batch at all (the batch size changed)."""
    ok = [{"kind": "generate", "batch": 0, "elapsed_s": 1.0, "capped": 1, "rows": 32},
          {"kind": "generate", "batch": 1, "elapsed_s": 100.0, "capped": 1, "rows": 32}]
    assert R.s_obs_from_progress("olmo2-7b", ok) == 1.0
    # The verifier's case: a 5,000 s batch in rows without the keys returned 1.0 silently.
    with pytest.raises(R.Refused):
        R.s_obs_from_progress("olmo2-7b", [{"kind": "generate", "batch": 0, "elapsed_s": 1.0},
                                           {"kind": "generate", "batch": 1, "elapsed_s": 5000.0}])
    for drift in ({"capped": 1}, {"rows": 32}, {"capped": None, "rows": 32}, {"capped": 1, "rows": "32"},
                  {"capped": True, "rows": 32}, {"capped": -1, "rows": 32}, {"capped": 1.0, "rows": 32}):
        rows = [dict(ok[0]), {"kind": "generate", "batch": 1, "elapsed_s": 5000.0, **drift}]
        with pytest.raises(R.Refused):
            R.s_obs_from_progress("olmo2-7b", rows)
        rows = [{"kind": "generate", "batch": 0, "elapsed_s": 1.0, **drift}, dict(ok[1])]   # the first row too
        with pytest.raises(R.Refused):
            R.s_obs_from_progress("olmo2-7b", rows)
    # No 32-row batch anywhere: a changed batch size has no basis.
    with pytest.raises(R.Refused):
        R.s_obs_from_progress("olmo2-7b", [{**ok[0], "rows": 16}, {**ok[1], "rows": 16}])
    # 32-row batches present but none capped: nothing slow was seen, s_obs = 1 (not a refusal).
    assert R.s_obs_from_progress("olmo2-7b", [{**ok[0], "capped": 0}, {**ok[1], "capped": 0}]) == 1.0


def test_05d_s_obs_reads_32_row_capped_batches_only(basis):
    """A-V2: KCR:113's 32-row clause. A slow capped short last batch (20 or 24 rows) must not raise s_obs; the same
    slowdown on a capped 32-row batch must."""
    u = next(x for x in basis["units"] if x["unit"] == "sp-olmo2-7b-1103")
    rows = progress_from(u)
    short = [r for r in rows if r["kind"] == "generate" and r["rows"] != R.GENERATION_BATCH]
    assert len(short) == 2 and {r["rows"] for r in short} == {20, 24}      # 468 = 14 x 32 + 20; 600 = 18 x 32 + 24
    for r in short:
        r["capped"] = max(int(r["capped"]), 3)                             # make both short batches capped ones
    # Slow each short batch by 2,000 s (shift it and every later row by the same amount). (rows, batch) names each
    # short batch once: the greedy series ends at batch 14 with 20 rows, the sampled one at batch 18 with 24.
    slowed = [dict(r) for r in rows]
    for s in short:
        idx = next(i for i, r in enumerate(slowed) if r["kind"] == "generate" and r["rows"] == s["rows"]
                   and r["batch"] == s["batch"])
        for r in slowed[idx:]:
            r["elapsed_s"] = round(r["elapsed_s"] + 2000.0, 3)
    gen = [r for r in slowed if r["kind"] == "generate"]
    assert any(b["elapsed_s"] - a["elapsed_s"] > 2000 for a, b in zip(gen, gen[1:]))
    assert R.s_obs_from_progress("olmo2-7b", slowed) == 1.0
    # The same 2,000 s on a capped 32-row batch (not the first greedy one) raises s_obs above the refusal.
    slowed32 = [dict(r) for r in rows]
    idx = next(i for i, r in enumerate(slowed32) if r["kind"] == "generate" and r["rows"] == 32 and r["capped"] > 0
               and r["batch"] > 0)
    for r in slowed32[idx:]:
        r["elapsed_s"] = round(r["elapsed_s"] + 2000.0, 3)
    s = R.s_obs_from_progress("olmo2-7b", slowed32)
    assert s > 2000 / R.FAMILIES["olmo2-7b"]["BATCH_MAX_S"] and R.s_obs_defers(s)
    # D3 (KCR:113's "capped" clause): the same 2,000 s on an UNCAPPED 32-row batch (not the first greedy one) leaves
    # s_obs = 1.0: a slow batch that hit no cap says nothing about the capped-batch maximum.
    uncapped = [dict(r) for r in rows]
    idx = next(i for i, r in enumerate(uncapped) if r["kind"] == "generate" and r["rows"] == 32 and r["batch"] > 0)
    uncapped[idx]["capped"] = 0
    for r in uncapped[idx:]:
        r["elapsed_s"] = round(r["elapsed_s"] + 2000.0, 3)
    assert R.s_obs_from_progress("olmo2-7b", uncapped) == 1.0


def test_05b_s_obs_on_the_real_progress_files():
    if not MEASURED_ROOT.is_dir() or not (MEASURED_ROOT / D.UNIT_KITS["olmo2-7b"][0]).is_dir():
        pytest.skip("the measured kits are not under this checkout's tmp/")
    for family, kits in D.UNIT_KITS.items():
        for kit_name in kits:
            kit = MEASURED_ROOT / kit_name
            host = D.host_of(kit)
            unit = [p for p in (kit / "retrieved" / host.name / "tree" / "round1").iterdir() if "-e1-" in p.name][0]
            rows = D.open_record(unit / "progress.jsonl")
            assert R.s_obs_from_progress(family, rows) == 1.0, kit_name


# ----------------------------------------------------------------------------------------------------- test 6
def test_06_sanity_floor(basis):
    f = R.FAMILIES["olmo2-7b"]
    normal = {"training_s": 1126.35, "ms_per_step_full": 269.0, "untuned_projected_s": 3265.16}
    assert R.requirement_s("olmo2-7b", 38, preflight=normal) == R.requirement_s("olmo2-7b", 38)
    big = {**normal, "untuned_projected_s": 20000.0}
    floor = R.sanity_floor_s("olmo2-7b", big, 38)
    assert floor == 1126.35 + 20000.0 + 1000 + 900 + 1800
    assert R.requirement_s("olmo2-7b", 38, preflight=big) == floor > R.requirement_s("olmo2-7b", 38)
    assert R.requirement_s("olmo2-7b", None, "evalonly", preflight=big) == 20000.0 + 1000 + 900 + 1800
    small = {**normal, "untuned_projected_s": 1.0, "training_s": 1.0}
    assert R.requirement_s("olmo2-7b", 38, preflight=small) == R.requirement_s("olmo2-7b", 38)   # never lowers
    # On every measured pod F_pre is below the requirement (KCR:109: the largest 8,301 s and 9,393 s at 38 steps).
    worst = {}
    for u in basis["units"]:
        fp = R.sanity_floor_s(u["family"], u["preflight"], 38)
        assert fp < R.requirement_s(u["family"], 38), u["unit"]
        worst[u["family"]] = max(worst.get(u["family"], 0.0), fp)
    for family, g in KCR.items():
        assert abs(worst[family] - g["f_pre_max"]) < 1.0
    with pytest.raises(R.Refused):
        R.sanity_floor_s("olmo2-7b", {"training_s": 1000.0}, 38)
    with pytest.raises(R.Refused):
        R.requirement_s("olmo2-7b", 38, preflight={"training_s": 1000.0, "ms_per_step_full": 200.0})
    assert f["EARLY_MAX_S"] < 25                                        # (keeps f used; the floor reads none of it)


# ----------------------------------------------------------------------------------------------------- test 7
def engine_config_sha256():
    """The engine's own config_sha256 (stdlib code under experiments/safety_selection; nothing is written)."""
    assert sys.dont_write_bytecode
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from experiments.safety_selection.config import config_sha256   # noqa: E402
    return config_sha256


def keys_of(family: str, **changes) -> dict:
    """The seven key arguments of check_keys for an arm pod of ``family`` on engine X, with changes."""
    args = {"family": family, "kind": "arm", "recipe_sha256": R.CONFIGS[family]["main"][1],
            "engine_sha256": R.ENGINE_X, "gpu_name": R.GPU_NAME, "manifest_sha256": R.MANIFESTS[family],
            "bank": dict(R.BANK)}
    args.update(changes)
    return args


def test_07_keys(basis):
    sha = engine_config_sha256()
    for family, c in R.CONFIGS.items():
        for label, (path, digest) in c.items():
            assert sha(json.loads((ROOT / path).read_text())) == digest, (family, label)
        main, g, other = c["main"][1], c["g"][1], c["other_lr"][1]
        R.check_keys(**keys_of(family))
        R.check_keys(**keys_of(family, recipe_sha256=g))
        R.check_keys(**keys_of(family, kind="a0_arm", recipe_sha256=g))      # a recipe-G reference unit
        R.check_keys(**keys_of(family, kind="evalonly"))
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, recipe_sha256=other))              # B at the other LR: in the basis, not an arm recipe
        mb4 = ROOT / "experiments/safety_selection/configs" / (
            "study-kt-olmo2-7b-r64-b-mb4-20261008.json" if family == "olmo2-7b" else
            "study-kt-llama31-8b-r64-b-mb4-20261008.json")
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, recipe_sha256=sha(json.loads(mb4.read_text()))))   # the mb4 rung
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, engine_sha256="34bfd288" + "0" * 56))             # another engine (Y)
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, gpu_name="NVIDIA H100 80GB HBM3"))
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, gpu_name="NVIDIA A100-SXM4-80GB "))
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, recipe_sha256=None))
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, kind="similarity"))                 # an unknown kind has no key check
        # A-V3: the prepared manifest and the evaluation bank the basis records are keys too (KCR:147).
        other_family = "llama31-8b" if family == "olmo2-7b" else "olmo2-7b"
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, manifest_sha256=R.MANIFESTS[other_family]))   # the other family's manifest
        for bad_manifest in (None, "", R.MANIFESTS[family][:-1], R.MANIFESTS[family].upper(), R.MANIFESTS[family] + " "):
            with pytest.raises(R.Refused):
                R.check_keys(**keys_of(family, manifest_sha256=bad_manifest))
        for bad_bank in (None, {}, {**R.BANK, "cap_tokens": 1024}, {**R.BANK, "generation_batch": 16},
                         {**R.BANK, "greedy_prompts": 500}, {**R.BANK, "harm_samples": 200},
                         {k: v for k, v in R.BANK.items() if k != "harm_samples"}, {**R.BANK, "extra": 1},
                         {**R.BANK, "cap_tokens": "2048"}, {**R.BANK, "cap_tokens": 2048.0}, list(R.BANK.items())):
            with pytest.raises(R.Refused):
                R.check_keys(**keys_of(family, bank=bad_bank))
    with pytest.raises(R.Refused):
        R.check_keys(**{**keys_of("olmo2-7b"), "family": "olmo3-7b"})
    assert R.ENGINES == {"X": R.ENGINE_X}
    # The bank the rule assumes (BATCHES = 34 at batch 32, cap 2,048) is the one the basis records (M).
    assert R.BANK == {"cap_tokens": 2048, "greedy_prompts": 468, "harm_samples": 600, "generation_batch": 32}
    assert all(basis[k] == v for k, v in R.BANK.items())
    assert basis["batches_per_evaluation"] == R.BATCHES == 34
    assert -(-R.BANK["greedy_prompts"] // R.BANK["generation_batch"]) == R.GREEDY_BATCHES
    assert -(-R.BANK["harm_samples"] // R.BANK["generation_batch"]) == R.SAMPLED_BATCHES
    assert R.CAP_TOKENS == R.BANK["cap_tokens"] and R.GENERATION_BATCH == R.BANK["generation_batch"]
    for family in R.FAMILIES:
        assert basis["families"][family]["manifest_sha256"] == [R.MANIFESTS[family]]


def test_07b_recipe_s78_pins_refuse_until_filled(monkeypatch, tmp_path):
    """Addendum A1: RECIPE_S is null per family until the family's anchor job has run and the maker wrote S_78.
    Every kind that needs S_78 (PP8: the a0-1101 retrain; REQ-3's representation pass rep_pass; A1's attributes pass
    a1_pass; the classifier, PP4) refuses through recipe_s_or_refuse while the pin is None. A filled pin (test-local;
    no config file is written) is accepted."""
    assert R.RECIPE_S == {"olmo2-7b": None, "llama31-8b": None}
    assert R.S78_KINDS == frozenset({"retrain", "rep_pass", "a1_pass", "classifier"}) and R.S78_KINDS <= set(R.E_KINDS)
    docs = {}                                                              # a pod at each family's slowest measured speed
    for family, f in R.FAMILIES.items():
        docs[family] = (fake_preflight_done(tmp_path, training_s=f["PRE_TRAINING_S_MAX"], ms_per_step_full=f["PRE_MS_PER_STEP_MAX"]),
                        fake_verification(cp_training_s=f["PRE_TRAINING_S_MAX"]))
    for family in R.FAMILIES:
        pre, ver = docs[family]
        with pytest.raises(R.Refused):
            R.recipe_s_or_refuse(family)
        for kind in R.S78_KINDS:
            job = R.job_record(family, kind)                               # planning never refuses (M3's need)
            assert job["unmeasured"] and R.e_pod(family, kind)["cap_hours"] > 0
            with pytest.raises(R.Refused):                                 # the runner's gate does
                R.job_decision(family, pre, ver, job, 10 * 3600.0, 20.0)
            with pytest.raises(R.Refused):                                 # the pod's key check does
                R.check_keys(**keys_of(family, kind=kind))
            with pytest.raises(R.Refused):
                R.check_keys(**keys_of(family, kind=kind, recipe_sha256=R.CONFIGS[family]["g"][1]))
        # Kinds that do not need S_78 run under the main config as before.
        arm = R.job_record(family, "arm", 33)
        assert R.job_decision(family, pre, ver, arm, 10 * 3600.0, 20.0)["action"] == "run"
        anchor = R.job_record(family, "anchor")
        assert R.job_decision(family, pre, ver, anchor, 10 * 3600.0, 20.0)["action"] == "run"
    assert R.block0_report()["retrain_pods"]["olmo2-7b"]["cap_hours"] == 4.5    # the money is planned before S_78
    with pytest.raises(R.Refused):
        R.recipe_s_or_refuse("olmo3-7b")
    # A filled pin: a 64-hex config_sha256 is accepted by the refusal function, the gate and the key check.
    s78 = "ab" * 32
    monkeypatch.setitem(R.RECIPE_S, "olmo2-7b", s78)
    assert R.recipe_s_or_refuse("olmo2-7b") == s78
    with pytest.raises(R.Refused):
        R.recipe_s_or_refuse("llama31-8b")                                 # the other family stays null
    for kind in R.S78_KINDS:
        job = R.job_record("olmo2-7b", kind)
        assert R.job_decision("olmo2-7b", *docs["olmo2-7b"], job, 20 * 3600.0, 20.0)["action"] == "run"
        R.check_keys(**keys_of("olmo2-7b", kind=kind, recipe_sha256=s78))
        with pytest.raises(R.Refused):                                     # S_78 kinds run under S_78 only
            R.check_keys(**keys_of("olmo2-7b", kind=kind))
        with pytest.raises(R.Refused):
            R.job_decision("llama31-8b", *docs["llama31-8b"], R.job_record("llama31-8b", kind), 20 * 3600.0, 20.0)
    with pytest.raises(R.Refused):                                         # arms never run under S_78 (P78:99)
        R.check_keys(**keys_of("olmo2-7b", recipe_sha256=s78))
    with pytest.raises(R.Refused):
        R.check_keys(**keys_of("olmo2-7b", kind="a0_arm", recipe_sha256=s78))
    # A pin that is not a config_sha256 refuses too.
    for bad in ("", "AB" * 32, "ab" * 31, "ab" * 32 + "a", 12345, "experiments/safety_selection/configs/x.json"):
        monkeypatch.setitem(R.RECIPE_S, "olmo2-7b", bad)
        with pytest.raises(R.Refused):
            R.recipe_s_or_refuse("olmo2-7b")
    # K1: COPY-MANIFEST.json (the kit copy's file list) sits beside the basis; no config file is ever written here.
    assert not list(KIT.glob("*.json.tmp")) and sorted(p.name for p in KIT.glob("*.json")) == ["COPY-MANIFEST.json", R.BASIS_FILE]


def test_07c_a13_pins_engine_y_bqi_and_the_sealed_sets(monkeypatch, tmp_path):
    """K1 (addendum A13; the re-verifier's D1). ENGINE_Y, RECIPE_G, RECIPE_BQI and the Llama sealed set's MANIFEST
    pin are null until the lead fills each by a recorded step; every kind that needs one refuses until then. Once
    ENGINE_Y is filled, E-capped kinds may run on Y; measured kinds only after KD9 sets Y_MEASURED. B+Qi
    (ref_train_bqi) runs under RECIPE_BQI only: it no longer passes under the main config or G (D1)."""
    assert R.ENGINE_Y is None and R.Y_MEASURED is False and R.ENGINES == {"X": R.ENGINE_X}
    assert R.RECIPE_G == {"olmo2-7b": None, "llama31-8b": None} == R.RECIPE_BQI
    assert R.PINS == {"RECIPE_S": R.RECIPE_S, "RECIPE_G": R.RECIPE_G, "RECIPE_BQI": R.RECIPE_BQI}
    assert R.BQI_KINDS == frozenset({"ref_train_bqi"}) and R.BQI_KINDS <= set(R.E_KINDS)
    assert R.PINNED_RECIPE_KINDS == {"retrain": "RECIPE_S", "rep_pass": "RECIPE_S", "a1_pass": "RECIPE_S",
                                     "classifier": "RECIPE_S", "ref_train_bqi": "RECIPE_BQI",
                                     "ref_train": "RECIPE_G"}        # PP8; R1 K1: recipe G's reference
    # PP7 (D3): the Llama sealed set's pin is FILLED with the committed MANIFEST's SHA-256 (d422fca); both pins are the
    # committed files' hashes (the files are read here: this repository root holds both sets).
    assert R.SEALED_SETS["llama31-8b"]["sha256"] == "2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c"
    assert R.SEALED_SETS["olmo2-7b"]["sha256"] == "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"
    for family in R.FAMILIES:
        manifest = ROOT / R.SEALED_SETS[family]["path"]
        assert manifest.is_file(), f"{family}: the committed sealed set {R.SEALED_SETS[family]['path']} is not in this checkout"
        assert hashlib.sha256(manifest.read_bytes()).hexdigest() == R.SEALED_SETS[family]["sha256"]   # the committed file
        assert R.sealed_set_or_refuse(family) == R.SEALED_SETS[family]
    # A13's pattern still holds for a null pin (test-local): the family refuses, the other family does not fall back.
    monkeypatch.setitem(R.SEALED_SETS["llama31-8b"], "sha256", None)
    with pytest.raises(R.Refused, match="llama31-8b sealed set's MANIFEST pin is null"):
        R.sealed_set_or_refuse("llama31-8b")
    assert R.sealed_set_or_refuse("olmo2-7b") == R.SEALED_SETS["olmo2-7b"]
    for bad in ("", "AB" * 32, "ab" * 31, 7):
        monkeypatch.setitem(R.SEALED_SETS["llama31-8b"], "sha256", bad)
        with pytest.raises(R.Refused):
            R.sealed_set_or_refuse("llama31-8b")
    monkeypatch.setitem(R.SEALED_SETS["llama31-8b"], "sha256", "2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c")
    with pytest.raises(R.Refused):
        R.sealed_set_or_refuse("olmo3-7b")
    y = "34bfd288" + "0" * 56
    docs = {}
    for family, f in R.FAMILIES.items():
        docs[family] = (fake_preflight_done(tmp_path, training_s=f["PRE_TRAINING_S_MAX"], ms_per_step_full=f["PRE_MS_PER_STEP_MAX"]),
                        fake_verification(cp_training_s=f["PRE_TRAINING_S_MAX"]))
        # D1: B+Qi passes under neither the main config nor G while RECIPE_BQI is null; the runner's gate refuses too.
        for recipe in (R.CONFIGS[family]["main"][1], R.CONFIGS[family]["g"][1], "ab" * 32):
            with pytest.raises(R.Refused):
                R.check_keys(**keys_of(family, kind="ref_train_bqi", recipe_sha256=recipe))
        with pytest.raises(R.Refused):
            R.recipe_bqi_or_refuse(family)
        with pytest.raises(R.Refused):
            R.pin_or_refuse("RECIPE_BQI", family)
        with pytest.raises(R.Refused):
            R.pin_or_refuse("RECIPE_G", family)
        with pytest.raises(R.Refused):
            R.pin_or_refuse("RECIPE_X", family)
        assert R.job_record(family, "ref_train_bqi")["unmeasured"]          # planning never refuses (M3's need)
        with pytest.raises(R.Refused):
            R.job_decision(family, *docs[family], R.job_record(family, "ref_train_bqi"), 20 * 3600.0, 20.0)
        # Engine Y while its pin is null: no kind runs on it (as before: test 7).
        for kind in ("arm", "a0_arm", "evalonly", "retrain", "anchor"):
            assert not R.engine_allowed(kind, y) and R.engine_allowed(kind, R.ENGINE_X)
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(family, kind="anchor", engine_sha256=y))
    # The pin-or-refuse form equals recipe_s_or_refuse on RECIPE_S.
    with pytest.raises(R.Refused):
        R.pin_or_refuse("RECIPE_S", "olmo2-7b")
    monkeypatch.setitem(R.RECIPE_S, "olmo2-7b", "ab" * 32)
    assert R.pin_or_refuse("RECIPE_S", "olmo2-7b") == R.recipe_s_or_refuse("olmo2-7b") == "ab" * 32
    # RECIPE_BQI filled (test-local): B+Qi passes under that config only, on X now and on Y once ENGINE_Y is filled.
    bqi = "cd" * 32
    monkeypatch.setitem(R.RECIPE_BQI, "olmo2-7b", bqi)
    assert R.recipe_bqi_or_refuse("olmo2-7b") == bqi
    R.check_keys(**keys_of("olmo2-7b", kind="ref_train_bqi", recipe_sha256=bqi))
    with pytest.raises(R.Refused):
        R.check_keys(**keys_of("olmo2-7b", kind="ref_train_bqi"))                       # the main config: refused
    with pytest.raises(R.Refused):
        R.check_keys(**keys_of("olmo2-7b", recipe_sha256=bqi))                          # an arm under B+Qi: refused
    with pytest.raises(R.Refused, match="OEXT_78B_Y"):                                  # R1 K1: its O-ext on Y
        R.job_decision("olmo2-7b", *docs["olmo2-7b"], R.job_record("olmo2-7b", "ref_train_bqi"), 20 * 3600.0, 20.0)
    engine_y_before = R.ENGINE_Y
    monkeypatch.setattr(R, "ENGINE_Y", "d3" * 32)
    monkeypatch.setitem(R.OEXT_78B_Y, "olmo2-7b", oext_pin("olmo2-7b", "Y"))
    assert R.job_decision("olmo2-7b", *docs["olmo2-7b"], R.job_record("olmo2-7b", "ref_train_bqi"), 20 * 3600.0, 20.0)["action"] == "run"
    monkeypatch.setitem(R.OEXT_78B_Y, "olmo2-7b", None)
    monkeypatch.setattr(R, "ENGINE_Y", engine_y_before)
    with pytest.raises(R.Refused):
        R.recipe_bqi_or_refuse("llama31-8b")                                           # the other family stays null
    for bad in ("", "CD" * 32, "cd" * 31, 7):
        monkeypatch.setitem(R.RECIPE_BQI, "olmo2-7b", bad)
        with pytest.raises(R.Refused):
            R.recipe_bqi_or_refuse("olmo2-7b")
    monkeypatch.setitem(R.RECIPE_BQI, "olmo2-7b", bqi)
    # ENGINE_Y filled: the E-capped kinds outside PP16's X_ONLY_KINDS run on Y; the wrapper kinds never do (PP16);
    # the measured kinds refuse until Y_MEASURED (KD9).
    monkeypatch.setattr(R, "ENGINE_Y", y)
    for kind in R.E_KINDS:
        assert R.engine_allowed(kind, y) is (kind not in R.X_ONLY_KINDS), kind
    for kind in R.MEASURED_KINDS:
        assert not R.engine_allowed(kind, y)
    with pytest.raises(R.Refused, match="the wrapper kinds only, PP16"):
        R.check_keys(**keys_of("olmo2-7b", kind="anchor", engine_sha256=y))                # PP16: anchor runs on X
    R.check_keys(**keys_of("olmo2-7b", kind="safe_lora", engine_sha256=y))
    R.check_keys(**keys_of("olmo2-7b", kind="ref_train_bqi", engine_sha256=y, recipe_sha256=bqi))
    R.check_keys(**keys_of("olmo2-7b", kind="retrain", engine_sha256=y, recipe_sha256="ab" * 32))   # the Y retrain
    for kind in ("arm", "a0_arm", "evalonly"):
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of("olmo2-7b", kind=kind, engine_sha256=y))
    with pytest.raises(R.Refused):
        R.check_keys(**keys_of("olmo2-7b", kind="safe_lora", engine_sha256="34bfd289" + "0" * 56))   # a third engine
    monkeypatch.setattr(R, "Y_MEASURED", True)
    for kind in ("arm", "a0_arm", "evalonly"):
        assert R.engine_allowed(kind, y)
        R.check_keys(**keys_of("olmo2-7b", kind=kind, engine_sha256=y))
    monkeypatch.setattr(R, "Y_MEASURED", 1)                                                # a truthy non-bool is not a pin
    assert not R.engine_allowed("arm", y) and R.engine_allowed("safe_lora", y)
    assert R.ENGINES == {"X": R.ENGINE_X}                                                   # the basis's engines stay X


# ----------------------------------------------------------------------------------------------------- test 8
def test_08_kinds():
    for family in R.FAMILIES:
        assert R.upper_m_s(family, 33, "arm") < R.upper_m_s(family, 38, "arm")
        assert R.upper_m_s(family, 38, "a0_arm") == R.upper_m_s(family, 38, "arm")
        assert R.upper_m_s(family, None, "evalonly") == R.upper_m_s(family, 38) - 38 * R.FAMILIES[family]["TRAIN_STEP_MAX_S"]
        assert R.job_record(family, "a0_arm")["steps"] == 38
        assert R.job_record(family, "evalonly")["steps"] is None
        for kind in ("A1", "anchors", "scorer", "B+Qi", "similarity", "transfer_report", "a1_rescore",
                     "cert_c1", "b10_certify", "arm ", ""):           # R1 K1: w1_18 and ref_train are kinds now
            with pytest.raises(R.Refused):
                R.check_kind(kind)
            with pytest.raises(R.Refused):
                R.job_record(family, kind, 33)
        for kind in R.E_KINDS:
            job = R.job_record(family, kind)
            assert job["unmeasured"] and job["upper_s"] > 0
            with pytest.raises(R.Refused):
                R.upper_m_s(family, 38, kind)
            with pytest.raises(R.Refused):
                R.measured_upper_s(family, kind)
            e = R.e_upper_s(family, kind)
            assert e["basis"].startswith("E:") and len(e["basis"]) > 40
            cap = R.e_cap_hours(family, kind)
            assert cap * 3600 >= R.POD_OVERHEAD_S + e["upper_s"] + R.START_MARGIN_S
            assert cap * 3600 < R.POD_OVERHEAD_S + e["upper_s"] + R.START_MARGIN_S + R.CAP_STEP_S
            with pytest.raises(R.Refused):                              # KD6: an E kind runs alone
                R.cap_hours([job, R.job_record(family, "arm", 33)])
            assert R.cap_hours([job]) == cap
        # PP8: a1_pass carries A1's 16.5 h cap; rep_pass (REQ-3) takes the 1B 3,600 s x 2.3 x 1.5 = 12,420 s:
        # 48 min + 12,420 s + 30 min = 17,100 s = 4.75 h exactly.
        assert R.e_cap_hours(family, "a1_pass") == R.A1_PASS_CAP_H_MAX == 16.5
        assert R.e_upper_s(family, "a1_pass")["upper_s"] == 16.5 * 3600 - 48 * 60 - 1800
        assert R.e_upper_s(family, "rep_pass")["upper_s"] == pytest.approx(12420.0)   # 1.5 x 2.3 x 3,600 (binary float)
        assert R.e_cap_hours(family, "rep_pass") == 4.75 and R.STAGE1_1B_ESTIMATES_S["rep_pass"] == 3600.0
        assert R.e_cap_hours(family, "rep_pass") < R.e_cap_hours(family, "a1_pass")
        assert "REQ-3" in R.e_upper_s(family, "rep_pass")["basis"] and "A1" in R.e_upper_s(family, "a1_pass")["basis"]
        assert R.e_cap_hours(family, "retrain") == 4.5
        assert R.e_upper_s(family, "safe_lora", 3)["upper_s"] > R.e_upper_s(family, "safe_lora", 1)["upper_s"]
        assert R.e_upper_s(family, "ref_eval", 3)["upper_s"] - R.e_upper_s(family, "ref_eval", 1)["upper_s"] == pytest.approx(
            2 * (R.evalonly_upper_s(family) + R.oext_term_s(family)))    # R1 K1: each point carries its O-ext pass
        with pytest.raises(R.Refused):
            R.e_upper_s(family, "safe_lora", 0)
        with pytest.raises(R.Refused):
            R.e_upper_s(family, "arm")
    with pytest.raises(R.Refused):
        R.upper_m_s("olmo2-7b", None, "arm")
    with pytest.raises(R.Refused):
        R.upper_m_s("olmo2-7b", 0, "arm")
    assert R.steps_of("remove") == 33 and R.steps_of("add") == 38 and R.steps_of("a0") == 38


def test_08b_job_record_refuses_a_bad_n_points_for_every_kind():
    """D2: RULES-78B.md says job_record refuses n_points < 1; it did so for E kinds only (through e_upper_s). Now
    every kind refuses a non-positive or non-integer n_points at the top of job_record."""
    for family in R.FAMILIES:
        for kind, steps in (("arm", 33), ("a0_arm", 38), ("evalonly", None), ("anchor", None), ("ref_eval", None)):
            assert R.job_record(family, kind, steps)["n_points"] == 1
            for bad in (0, -1, 1.0, True, None, "1"):
                with pytest.raises(R.Refused):
                    R.job_record(family, kind, steps, n_points=bad)
        assert R.job_record(family, "ref_eval", n_points=3)["n_points"] == 3


def test_08c_block0_tables_and_jobs():
    """K1: N's layout per family (ruling 11; Part 1 §3.1) from the kit block: R_1-R_3 at 1101-1103 on both families
    (R_d at 1100 + d), a0 at 1103 on Llama-3.1-8B only (ruling 8); the one pod's cap equals KCR §7's (8.5 h / 12.5 h)
    and n_pods()'s; every arm is 33 steps, a0 38."""
    assert R.block0_runs("olmo2-7b") == [("R", 1101), ("R", 1102), ("R", 1103)]
    assert R.block0_runs("llama31-8b") == [("R", 1101), ("R", 1102), ("R", 1103), ("a0", 1103)]
    assert R.R_SEED_BASE == 1100 and R.BLOCK0_R_DRAWS == (1, 2, 3) and R.A0_SEED_1103 == 1103
    pods = {p["family"]: p for p in R.n_pods()}
    for family in R.FAMILIES:
        jobs = R.block0_jobs(family)
        assert [(j["kind"], j["arm"], j["seed"], j["steps"]) for j in jobs] == [
            ("a0_arm" if a == "a0" else "arm", a, s, 38 if a == "a0" else 33) for a, s in R.block0_runs(family)]
        assert R.cap_hours(jobs) == R.KIT[family]["block0"]["cap_hours"] == pods[family]["cap_hours"]
        assert R.KIT[family]["block0"]["host"] == pods[family]["host"] == f"{family}-0-1"
        assert R.arm_count(jobs) == len(jobs) <= R.MAX_ARMS_PER_POD_78B
        assert R.KIT[family]["rec"] == R.CONFIGS[family]["main"] and R.KIT[family]["probe_key"] == family
        assert R.KIT[family]["manifest_sha256"] == R.MANIFESTS[family]
        assert R.KIT[family]["base_model"]["revision"] is None                   # null until the lead pins it
        assert R.KIT[family]["volume_gb"] == R.VOLUME_GB == 50 and R.KIT[family]["max_arms_per_pod"] == R.MAX_ARMS_PER_POD_78B
        assert R.kit_of(family) is R.KIT[family]
    assert R.cap_hours(R.block0_jobs("olmo2-7b")) == 8.5 and R.cap_hours(R.block0_jobs("llama31-8b")) == 12.5
    with pytest.raises(R.Refused):
        R.block0_runs("olmo3-7b")
    with pytest.raises(R.Refused):
        R.kit_of("olmo2-1b")


# ----------------------------------------------------------------------------------------------------- test 9
def test_09_cap_structure_and_copied_helpers(stage1):
    f = "olmo2-7b"
    one = R.arm_pod(f, [38])
    assert R.cap_hours(one) == R.hours(R.round_up_s(R.POD_OVERHEAD_S + R.requirement_s(f, 38)))   # j < k: nothing before k
    two = R.arm_pod(f, [33, 38])
    worst = max(R.POD_OVERHEAD_S + R.requirement_s(f, 33),
                R.POD_OVERHEAD_S + R.measured_upper_s(f) + R.requirement_s(f, 38))
    assert R.cap_hours(two) == R.hours(R.round_up_s(worst))
    assert R.round_up_s(15245) == 15300 and R.round_up_s(15300) == 15300 and R.round_up_s(15300.0000001) == 15300
    assert R.round_up_s(15300.001) == 16200 and R.round_up_s(1) == 900
    assert R.pod_sizes(8) == [4, 4] and R.pod_sizes(6) == [3, 3] and R.pod_sizes(5) == [3, 2]
    assert R.pod_sizes(20) == [4] * 5 and R.pod_sizes(14) == [4, 4, 3, 3] and R.pod_sizes(1) == [1]
    with pytest.raises(R.Refused):
        R.cap_hours(R.arm_pod(f, [33] * 5))
    # D7: a0_arm and evalonly count toward KD2's 4 as arms do (4 arms + either refuses; 3 arms + either is fine).
    with pytest.raises(R.Refused):
        R.cap_hours(R.arm_pod(f, [33] * 4 + [38], ["arm"] * 4 + ["a0_arm"]))
    with pytest.raises(R.Refused):
        R.cap_hours(R.arm_pod(f, [33] * 4) + [R.job_record(f, "evalonly")])
    assert R.cap_hours(R.arm_pod(f, [33] * 3 + [38], ["arm"] * 3 + ["a0_arm"])) == 10.5
    assert R.cap_hours(R.arm_pod(f, [33] * 3) + [R.job_record(f, "evalonly")]) > 0
    assert R.arm_count(R.arm_pod(f, [33] * 3 + [38], ["arm"] * 3 + ["a0_arm"])) == 4
    assert R.arm_count(R.arm_pod(f, [33] * 3) + [R.job_record(f, "evalonly")]) == 4
    with pytest.raises(R.Refused):
        R.cap_hours([])
    with pytest.raises(R.Refused):
        R.cap_hours(R.arm_pod(f, [33]) + R.arm_pod("llama31-8b", [33]))
    assert R.MAX_ARMS_PER_POD_78B == 4 == stage1.MAX_ARMS_PER_POD
    # The copied helpers equal the stage-1 kit's on the same inputs.
    for seconds in (0, 1, 899.999999, 900, 900.0000001, 15245, 15300, 15300.001, 37497.5, 44700.7, 123456.789):
        assert R.round_up_s(seconds) == stage1.round_up_s(seconds)
    for usd in (0, 2.675, 2.665, 44.85, 56.0625, 25.425, 19.425, 109.335, 0.005, 0.015, 1e-9, 12.4975, 20.7956):
        assert R.cents(usd) == stage1.cents(usd)
    for n in range(1, 41):
        assert R.pod_sizes(n) == stage1.pod_sizes(n)
    for cap in (4.25, 6.5, 8.5, 10.5, 12.5, 16.5, 0.25):
        assert R.guard_usd(cap) == stage1.guard_usd(cap)
        assert R.hours(cap * 3600) == stage1.hours(cap * 3600)
    launches = [[{"cap_hours": 8.5, "spend_usd": 12.50}, {"cap_hours": 12.5, "spend_usd": 20.80}],
                [{"cap_hours": 4.5, "spend_usd": 6.80}],
                [{"cap_hours": 16.5, "spend_usd": 28.64}, {"cap_hours": 3.0, "spend_usd": 4.46}],
                [{"cap_hours": 2.0, "judge": True}]]
    for k in range(1, len(launches) + 1):
        for factor in (1.0, 1.25):
            assert R.funding_need_usd(launches[:k], factor) == stage1.funding_need_usd(launches[:k], factor)
    assert R.funding_need_usd(launches[:1], 1.25)["need_usd"] == 56.06
    for remaining, need in ((None, 1.0), (10.0, 10.0), (9.999, 10.0), (1e9, 1.0)):
        assert R.gate(remaining, need) == stage1.gate(remaining, need)
    assert (R.RESERVE_USD, R.PLANNING_PRICE_USD, R.RATE_USD, R.CONTINGENCY_FACTOR, R.MAX_PRICE_USD, R.CAP_STEP_S,
            R.START_MARGIN_S) == (stage1.RESERVE_USD, stage1.PLANNING_PRICE_USD, stage1.RATE_USD,
                                  stage1.CONTINGENCY_FACTOR, stage1.MAX_PRICE_USD, stage1.CAP_STEP_S,
                                  stage1.START_MARGIN_S)
    assert R.POD_OVERHEAD_S == 48 * 60 and stage1.POD_OVERHEAD_S == 42 * 60       # KCR §4: the one deliberate difference


# ----------------------------------------------------------------------------------------------------- test 10
def test_10_zero_hold_guard(monkeypatch):
    assert R.GATE_B_HOLD_USD == 0
    assert R.GATE_B_HOLD_REASON == ("Gate B closed 23 Oct (FOCUS 'GATE B CLOSED', recorded 2026-10-23T05:26 UTC); "
                                    "its last judge pods deleted 31 Oct")
    for cap in (4.25, 6.5, 8.5, 10.5, 4.5, 7.25, 9.75, 12.5, 16.5, 21.0):
        exact = R.cents(R.RESERVE_USD + R.GATE_B_HOLD_USD + cap * R.PLANNING_PRICE_USD)
        assert R.launch_allowed(exact, cap)                            # exactly at $6 + the need
        assert not R.launch_allowed(R.cents(exact - 0.01), cap)        # one cent below
        assert R.launch_allowed(exact + 0.01, cap)
    assert R.launch_allowed(44.85, 21.0) and not R.launch_allowed(44.84, 21.0)    # block 0's two pods
    assert R.cents(R.guard_usd(10.5)) == 25.43
    monkeypatch.setattr(R, "GATE_B_HOLD_USD", 83.91)                   # a non-zero hold enters the guard and the floor
    assert R.cents(R.guard_usd(10.5)) == 109.34
    assert R.launch_allowed(109.34, 10.5) and not R.launch_allowed(109.33, 10.5)
    assert R.price_allowed(1.79) and R.price_allowed(10.0) and not R.price_allowed(10.01)
    assert not R.price_allowed(None) and not R.price_allowed(float("nan")) and not R.price_allowed("1.79")


def test_10b_guard_refuses_a_bad_balance_or_cap():
    """A-V4: a non-finite or non-numeric balance, cap or price raises Refused (the rule's own refusal), never a
    decimal or type error from inside the arithmetic."""
    assert R.launch_allowed(44.85, 21.0) and not R.launch_allowed(44.84, 21.0)
    for bad in (float("nan"), float("inf"), -float("inf"), None, "44.85", True, [44.85], {"usd": 44.85}):
        with pytest.raises(R.Refused):
            R.launch_allowed(bad, 21.0)
        with pytest.raises(R.Refused):
            R.launch_allowed(44.85, bad)
        with pytest.raises(R.Refused):
            R.launch_allowed(44.85, 21.0, price=bad)


# ----------------------------------------------------------------------------------------------------- test 11
def budget_text() -> str:
    return (STAGE1 / "budget.py").read_text(encoding="utf-8")


def test_11_cross_kit_counting(tmp_path):
    name = R.WORKING_COPY_PREFIX + "olmo2-7b-0"
    assert R.WORKING_COPY_PREFIX == "family-probe-s78-" and name == "family-probe-s78-olmo2-7b-0"
    glob_line = re.search(r"^KITS_GLOB = \((.*)\)", budget_text(), re.M)
    patterns = [p.strip().strip('"') for p in glob_line.group(1).split(",") if p.strip()]
    assert "family-probe-*" in patterns and "gate-b-olmo*" in patterns and "stage1-olmo*" in patterns
    assert any(fnmatch.fnmatch(name, p) for p in patterns)
    assert any(fnmatch.fnmatch(R.WORKING_COPY_PREFIX + "llama31-8b-A", p) for p in patterns)
    assert re.search(r'^LOCK_NAME = "family-probe-budget.lock"$', budget_text(), re.M)
    assert R.LOCK_NAME == "family-probe-budget.lock"
    # Functional: the stage-1 kit's budget.py, unchanged, inside a 7-8B working copy named by KD7 finds Gate B's and
    # stage 1's hosts/*/pod.json beside it, and the stage-1 kit's copy finds the 7-8B pod; one lock path for both.
    tmp = tmp_path / "tmp"
    s78 = tmp / name
    (s78 / "hosts" / "olmo2-7b-0-1").mkdir(parents=True)
    for kit in ("gate-b-olmo", "stage1-olmo"):
        (tmp / kit / "hosts" / "h1").mkdir(parents=True)
    (tmp / "gate-b-olmo" / "hosts" / "h1" / "pod.json").write_text(json.dumps(
        {"id": "pod-gateb", "cap_stop_utc": "2026-11-06T12:00:00+00:00"}))
    (tmp / "stage1-olmo" / "hosts" / "h1" / "pod.json").write_text(json.dumps(
        {"id": "pod-stage1", "cap_stop_utc": "2026-11-06T13:00:00+00:00"}))
    (s78 / "hosts" / "olmo2-7b-0-1" / "pod.json").write_text(json.dumps(
        {"id": "pod-s78", "cap_stop_utc": "2026-11-06T14:00:00+00:00"}))
    (s78 / "hosts" / "olmo2-7b-0-1" / "cap-override.json").write_text(json.dumps({"stop_at_utc": "2026-11-06T15:00:00Z"}))
    for folder in (s78, tmp / "stage1-olmo"):
        for file in ("budget.py", "stage1_rules.py"):
            shutil.copy(STAGE1 / file, folder / file)
    sys.modules.pop("stage1_rules", None)
    b78 = load_by_path("budget_in_s78_copy", s78 / "budget.py")
    assert set(p.name for p in b78.kit_folders()) == {name, "gate-b-olmo", "stage1-olmo"}
    caps = b78.caps_by_pod_id()
    assert set(caps) == {"pod-gateb", "pod-stage1", "pod-s78"}
    assert caps["pod-s78"] == "2026-11-06T15:00:00+00:00"              # the later cap-override wins
    assert b78.HERE.parent / b78.LOCK_NAME == tmp / "family-probe-budget.lock"
    sys.modules.pop("stage1_rules", None)
    b1 = load_by_path("budget_in_stage1_copy", tmp / "stage1-olmo" / "budget.py")
    assert "pod-s78" in b1.caps_by_pod_id() and b1.HERE.parent / b1.LOCK_NAME == tmp / "family-probe-budget.lock"
    assert b1.KITS_GLOB == b78.KITS_GLOB and b1.LOCK_NAME == R.LOCK_NAME
    sys.modules.pop("stage1_rules", None)


# ----------------------------------------------------------------------------------------------------- test 12
TRAINING_S, MS_FULL, UNTUNED_S = 1126.3526134664812, 269.0282543626381, 3265.1618277494795   # the real 1103 values (M)


def fake_preflight_done(tmp_path, **changes) -> dict:
    """A PREFLIGHT-DONE.json with the keys the 17 measured files hold (M: none holds untuned_projected_s)."""
    doc = {"utc": "2026-11-20T10:00:00+00:00", "ok": True, "folder": "cuda-preflight-1", "cap_remaining_s": 43472.86,
           "generation_batch": 32, "init_equals_untuned": True, "ms_per_step_full": MS_FULL, "overhead_s": 1000,
           "projected_job_upper_s": 41077.72497615558, "training_s": TRAINING_S, "verification_sha256": "cd" * 32,
           "tried": [{"exit": 0, "folder": "cuda-preflight-1"}]}
    doc.update(changes)
    doc = {k: v for k, v in doc.items() if v is not ...}
    path = tmp_path / "PREFLIGHT-DONE.json"
    path.write_text(json.dumps(doc, allow_nan=True))
    return json.loads(path.read_text())


def fake_verification(**changes) -> dict:
    """The preflight's verification.json, the blocks the rule reads (cap_projection) and a few it does not."""
    cp = {"batches_capped": 34, "e1_upper_s": 19025.68618134455, "margin_s": 900, "overhead_measured_s": 21.38,
          "overhead_s": 1000, "projected_job_upper_s": 41077.72497615558, "training_s": TRAINING_S,
          "untuned_projected_s": UNTUNED_S, "untuned_upper_s": 19025.68618134455}
    doc = {"cap_projection": cp, "generation_batch": 32, "generation_memory_ok": True,
           "full_length": {"batch": 32, "max_new_tokens": 2048, "ms_per_step_full": MS_FULL},
           "manifest_sha256": R.MANIFESTS["olmo2-7b"], "recipe_sha256": R.CONFIGS["olmo2-7b"]["main"][1]}
    for key, value in changes.items():
        if key.startswith("cp_"):
            if value is ...:
                cp.pop(key[3:], None)
            else:
                cp[key[3:]] = value
        elif value is ...:
            doc.pop(key, None)
        else:
            doc[key] = value
    return doc


def test_12_job_runner_dry_run(tmp_path):
    f = "olmo2-7b"
    pre, ver = fake_preflight_done(tmp_path), fake_verification()
    assert "untuned_projected_s" not in pre                              # as in the 17 measured files
    jobs = R.arm_pod(f, [33, 33, 33, 38])
    fields = R.preflight_fields(pre, ver)
    assert fields == {"training_s": TRAINING_S, "ms_per_step_full": MS_FULL, "untuned_projected_s": UNTUNED_S}
    assert R.speed_factor(f, fields) == 1.0
    run = R.pod_dry_run(f, pre, ver, jobs, remaining_s=30000.0, free_gb=20.0)
    assert [d["action"] for d in run] == ["run", "run", "run", "defer"] and run[3]["reason"] == "remaining"
    assert run[0]["requirement_s"] == R.requirement_s(f, 33) and run[3]["requirement_s"] == R.requirement_s(f, 38)
    assert run[1]["remaining_s"] == pytest.approx(30000.0 - R.measured_upper_s(f))
    assert [d["action"] for d in R.pod_dry_run(f, pre, ver, jobs, 50000.0, 20.0)] == ["run"] * 4
    assert [d["action"] for d in R.pod_dry_run(f, pre, ver, jobs, 12000.0, 20.0)] == ["defer"] * 4
    # A slow pod scales the requirement.
    slow = fake_preflight_done(tmp_path, training_s=1202.0527407700815 * 1.1)
    slow_ver = fake_verification(cp_training_s=1202.0527407700815 * 1.1)
    d = R.job_decision(f, slow, slow_ver, jobs[0], 20000.0, 20.0)
    assert math.isclose(d["s_pod"], 1.1) and math.isclose(d["requirement_s"], 1.1 * R.upper_m_s(f, 33) + 1800)
    # s_obs above 1.15 defers every later arm; at 1.10 it only raises the requirement.
    d = R.job_decision(f, pre, ver, jobs[1], 50000.0, 20.0, s_obs=1.2)
    assert d["action"] == "defer" and d["reason"] == "s_obs"
    d = R.job_decision(f, pre, ver, jobs[1], 50000.0, 20.0, s_obs=1.10)
    assert d["action"] == "run" and math.isclose(d["requirement_s"], 1.10 * R.upper_m_s(f, 33) + 1800)
    # D6: the returned ``s`` is max(1, s_pod, s_obs), the factor the requirement used.
    assert d["s"] == 1.10 and d["s_pod"] == 1.0 and d["s_obs"] == 1.10
    d = R.job_decision(f, slow, slow_ver, jobs[0], 50000.0, 20.0, s_obs=1.05)
    assert math.isclose(d["s"], 1.1) and math.isclose(d["s"], max(1.0, d["s_pod"], d["s_obs"]))
    assert R.job_decision(f, pre, ver, jobs[0], 50000.0, 20.0, s_obs=0.5)["s"] == 1.0
    # D5: the first deferral defers every later job, even one whose own requirement would fit (a 38-step arm before a
    # 33-step arm, with a remaining time between their requirements: the 33-step arm fits alone but is deferred).
    pair = R.arm_pod(f, [38, 33])
    between = (R.requirement_s(f, 33) + R.requirement_s(f, 38)) / 2
    assert R.requirement_s(f, 33) < between < R.requirement_s(f, 38)
    assert R.job_decision(f, pre, ver, pair[1], between, 20.0)["action"] == "run"
    run = R.pod_dry_run(f, pre, ver, pair, between, 20.0)
    assert [(d["action"], d["reason"]) for d in run] == [("defer", "remaining"), ("defer", "earlier job deferred")]
    # Missing or bad PREFLIGHT-DONE fields refuse.
    for changes in ({"training_s": ...}, {"ms_per_step_full": ...}, {"training_s": None},
                    {"ms_per_step_full": float("nan")}, {"training_s": "1126"}, {"training_s": True},
                    {"training_s": 1202.0527407700815 * 1.16}):
        bad = fake_preflight_done(tmp_path, **changes)
        with pytest.raises(R.Refused):
            R.job_decision(f, bad, ver, jobs[0], 50000.0, 20.0)
    for bad_doc in (None, [], "PREFLIGHT-DONE.json", 1126.35):
        with pytest.raises(R.Refused):
            R.job_decision(f, bad_doc, ver, jobs[0], 50000.0, 20.0)
    # The free-space check (KD5) refuses below the threshold and on a missing reading.
    with pytest.raises(R.Refused):
        R.job_decision(f, pre, ver, jobs[0], 50000.0, R.FREE_SPACE_MIN_GB - 0.01)
    with pytest.raises(R.Refused):
        R.job_decision(f, pre, ver, jobs[0], 50000.0, None)
    assert R.job_decision(f, pre, ver, jobs[0], 50000.0, R.FREE_SPACE_MIN_GB)["action"] == "run"
    assert R.free_space_ok(49.0) and not R.free_space_ok(float("nan")) and R.VOLUME_GB == 50
    # No remaining time known: never fits (Gate B's rule).
    assert R.job_decision(f, pre, ver, jobs[0], None, 20.0)["action"] == "defer"
    # An E kind's job carries its explicit window and no speed scaling (a1_pass needs S_78: test 7b; anchor here).
    anchor = R.job_record(f, "anchor")
    d = R.job_decision(f, slow, slow_ver, anchor, R.e_cap_hours(f, "anchor") * 3600 - R.POD_OVERHEAD_S, 20.0)
    assert d["action"] == "run" and d["requirement_s"] == anchor["start_requirement_s"]
    assert R.e_cap_hours(f, "a1_pass") == 16.5 and R.e_cap_hours(f, "rep_pass") == 4.75    # PP8


def test_12b_job_decision_takes_the_verification_document(tmp_path):
    """The T4 interface (verify-A's job 4): untuned_projected_s lives only in the preflight's verification.json
    cap_projection block (M: none of the 17 PREFLIGHT-DONE.json files holds it), so job_decision and pod_dry_run take
    both documents explicitly and refuse on a missing document, block or field. There is no fallback to a
    PREFLIGHT-DONE.json field of that name, and the two documents must describe one preflight (training_s equal)."""
    f = "olmo2-7b"
    pre, ver = fake_preflight_done(tmp_path), fake_verification()
    job = R.arm_pod(f, [33])[0]
    assert R.job_decision(f, pre, ver, job, 50000.0, 20.0)["action"] == "run"
    assert R.preflight_fields(pre, ver)["untuned_projected_s"] == UNTUNED_S
    # The sanity floor reads it: a large value binds through job_decision.
    big = fake_verification(cp_untuned_projected_s=30000.0)
    d = R.job_decision(f, pre, big, job, 60000.0, 20.0)
    assert d["requirement_s"] == R.sanity_floor_s(f, R.preflight_fields(pre, big), 33) > R.requirement_s(f, 33)
    # Missing document, block or field refuses.
    for bad_ver in (None, {}, [], "verification.json", {"cap_projection": None}, {"cap_projection": []},
                    {"cap_projection": {}}, fake_verification(cp_untuned_projected_s=...),
                    fake_verification(cp_untuned_projected_s=None), fake_verification(cp_untuned_projected_s=float("nan")),
                    fake_verification(cp_untuned_projected_s="3265"), fake_verification(cp_untuned_projected_s=True),
                    fake_verification(cap_projection=...)):
        with pytest.raises(R.Refused):
            R.preflight_fields(pre, bad_ver)
        with pytest.raises(R.Refused):
            R.job_decision(f, pre, bad_ver, job, 50000.0, 20.0)
        with pytest.raises(R.Refused):
            R.pod_dry_run(f, pre, bad_ver, [job], 50000.0, 20.0)
    # No fallback: a PREFLIGHT-DONE.json that carries the field does not stand in for the verification document.
    with_field = fake_preflight_done(tmp_path, untuned_projected_s=UNTUNED_S)
    with pytest.raises(R.Refused):
        R.preflight_fields(with_field, fake_verification(cp_untuned_projected_s=...))
    with pytest.raises(R.Refused):
        R.job_decision(f, with_field, None, job, 50000.0, 20.0)
    # The two documents must be one preflight's: cap_projection.training_s equals PREFLIGHT-DONE training_s.
    with pytest.raises(R.Refused):
        R.preflight_fields(pre, fake_verification(cp_training_s=TRAINING_S * 1.01))
    with pytest.raises(R.Refused):
        R.preflight_fields(pre, fake_verification(cp_training_s=...))
    assert R.preflight_fields(pre, fake_verification(cp_training_s=TRAINING_S + 1e-9))["training_s"] == TRAINING_S
    # The signature is explicit: the verification document is positional and required.
    with pytest.raises(TypeError):
        R.job_decision(f, pre, job, 50000.0, 20.0)                        # the old five-argument call
    with pytest.raises(TypeError):
        R.preflight_fields(pre)
    with pytest.raises(TypeError):
        R.pod_dry_run(f, pre, [job], 50000.0, 20.0)


# ----------------------------------------------------------------------------------------------------- test 13
def test_13_mutation_spec_is_well_formed():
    spec = json.loads((HERE / "mutation_spec_rules_78b.json").read_text())
    assert spec["kind"] == "stage1-78b mutants" and len(spec["mutants"]) >= 10
    ids = [m["id"] for m in spec["mutants"]]
    assert len(ids) == len(set(ids))
    for m in spec["mutants"]:
        assert (KIT / m["file"]).is_file(), m["id"]
        assert m["find"] and m["replace"] != m["find"] and m["describes"]
        # (Whether each find text occurs exactly once in its file is the runner's own check: it reports a mutant that
        # does not as INVALID. Checking it here would let a mutated source fail this test and mask the real tests.)
    required = {"T2-m-margin-1.0", "T2-m-33-batches", "T2-m-first-batch-dropped", "T2-m-score-3x-nongen",
                "T2-m-outside-ledger-end", "T2-m-s-no-floor", "T2-m-s-pod-only", "T2-m-start-margin-removed",
                "T2-m-overhead-42", "T2-m-round-down", "T2-m-floor-min", "T2-m-j-le-k",
                # the fix round's mutants (A-V1..A-V6, the RECIPE_S refusal, the job_decision missing-field refusal)
                "T2-m-s-obs-missing-keys-pass", "T2-m-s-obs-no-32-row-check-off", "T2-m-s-obs-rows-filter-off",
                "T2-m-keys-manifest-any", "T2-m-keys-bank-any", "T2-m-launch-no-finite", "T2-m-recipe-s-none-passes",
                "T2-m-s78-kinds-empty", "T2-m-keys-s78-any-recipe", "T2-m-preflight-untuned-fallback",
                "T2-m-verification-optional", "T2-m-derive-place-off", "T2-m-derive-create-wildcard",
                "T2-m-derive-allcapped-35",
                # K1: the re-verifier's D1-D7 and the addendum's A13 pins
                "K1-m-bqi-pin-off", "K1-m-pin-none-passes", "K1-m-n-points-unchecked", "K1-m-s-obs-uncapped-counts",
                "K1-m-derive-unit-place-loose", "K1-m-dry-run-no-cascade", "K1-m-decision-s-pod-only",
                "K1-m-counted-drops-a0", "K1-m-engine-y-measured-any", "K1-m-engine-y-e-kinds-off",
                "K1-m-engine-y-null-passes", "K1-m-sealed-set-null-passes", "K1-m-block0-llama-no-a0",
                # fix-K-core: D1 (both MANIFEST forms; V-H17 re-targeted), D2 (idle storage), PP7 (the pin), PP8 (kinds)
                "FK-m-s78-kinds-no-classifier", "FK-m-s78-kinds-no-a1-pass", "FK-m-rep-pass-takes-a1-window",
                "FK-m-rep-pass-no-size-factor", "FK-m-a1-pass-takes-rep-pass-cap", "FK-m-scorer-kinds-no-a1-pass",
                "FK-m-r-edits-any-family", "FK-m-r-edits-seed-unchecked", "FK-m-r-edits-duplicate-passes",
                "FK-m-r-edits-missing-passes", "FK-m-edit-entry-any-path", "FK-m-edit-entry-role-edit-only",
                "FK-m-llama-pin-null", "FK-m-idle-running-rate", "FK-m-idle-not-in-report", "FK-m-idle-per-pod-only",
                # K4a: PP16 (X_ONLY_KINDS first), DK-3 (the kit's stage1_rules kind sets), PP14 (the idle-storage pods)
                "K4-m-x-only-off", "K4-m-x-only-any-engine", "K4-m-x-only-after-y", "K4-m-x-only-plus-retrain",
                "K4-m-x-only-drop-anchor", "K4-m-x-only-drop-c0", "K4-m-unitless-plus-a1-pass", "K4-m-diag-no-a1-pass",
                "K4-m-idle-no-retrain-pods", "K4-m-idle-no-scorer-pods", "K4-m-idle-all-n-only",
                # round 4b: PP17 (o_only_with_regenerate in regenerate's place), D4 (one state definition), PP18 (c0)
                "K4-m-x-only-drop-o-only-with-regenerate", "K4bf-m-state-no-c0", "K4bf-m-state-no-regen",
                "K4bf-m-idle-one-pod-per-kind", "K4bf-m-scorer-kinds-no-regen", "K4bf-m-regenerate-kind-back",
                "K4bf-m-unitless-no-c0",
                # R1 K1 (8 Nov): blocks A and B's rules layer
                "K1R-m-block-a-no-r5", "K1R-m-b9-seeds-1109", "K1R-m-b-r-at-first-seed", "K1R-m-b-a0-two-seeds",
                "K1R-m-r-d6-from-seal", "K1R-m-null-method-edit-accepted", "K1R-m-stopped-keeps-l1",
                "K1R-m-stop-drop-off", "K1R-m-gate-hash-unchecked", "K1R-m-gate-null-passes",
                "K1R-m-gate-c-both-families", "K1R-m-gate-family-unchecked", "K1R-m-deal-p1", "K1R-m-deal-seed-major",
                "K1R-m-deal-5-per-pod", "K1R-m-sr78-deal-n-for-ab", "K1R-m-dose-38", "K1R-m-rows-check-skipped",
                "K1R-m-steps-floor", "K1R-m-s4-top-range-off", "K1R-m-sr78-dose-38", "K1R-m-train-scale-missing-passes",
                "K1R-m-requirements-drop-padded", "K1R-m-sr78-job-record-drops-padded", "K1R-m-oext-x1",
                "K1R-m-oext-a0-arm-off", "K1R-m-oext-measured-ignored", "K1R-m-oext-measured-upper-no-term",
                "K1R-m-requirements-drop-oext", "K1R-m-decision-drop-oext", "K1R-m-oext-refs-off",
                "K1R-m-oext-batches-12", "K1R-m-block0-gets-oext", "K1R-m-block-job-no-oext",
                "K1R-m-check-keys-oext-bank-any", "K1R-m-check-keys-oext-kind-any", "K1R-m-w1-18-not-first",
                "K1R-m-w1-18-c-both", "K1R-m-w1-18-one-record", "K1R-m-w1-18-not-x-only", "K1R-m-w1-18-cap-no-factor",
                "K1R-m-branch-switch-allowed", "K1R-m-branch-128-by-default", "K1R-m-bank500-block0-arms",
                "K1R-m-bank500-no-record-passes", "K1R-m-flag-dropped-on-c0", "K1R-m-dev100-on-theta0",
                "K1R-m-seed-key-seed-only", "K1R-m-n-units-not-listed", "K1R-m-n-regen-without-edit",
                "K1R-m-acceptance-against-side", "K1R-m-n-units-null-passes", "K1R-m-n-units-path-loose",
                "K1R-m-rejudged-no-theta0", "K1R-m-rejudged-null-passes", "K1R-m-sr78-rejudged-a-empty",
                "K1R-m-anchor-any-exit-1", "K1R-m-anchor-crash-is-stop", "K1R-m-anchor-job-done-unchecked",
                "K1R-m-stopped-plans-l1-scan", "K1R-m-main-retrain-without-stop", "K1R-m-stopped-retrain-any-recipe",
                "K1R-m-stopped-retrain-needs-s", "K1R-m-stop-order-anchor-needed", "K1R-m-decision-stopped-retrain-s",
                "K1R-m-sc-recipe-stopped-s", "K1R-m-sr78-retrain-job-stopped-s", "K1R-m-ref-train-any-recipe",
                "K1R-m-ref-train-decision-unpinned", "K1R-m-oext-script-1b", "K1R-m-sr78-blocks-no-b",
                "K1R-m-plan-b-from-gate", "K1R-m-plan-b-review-plans", "K1R-m-plan-b-sr2-hashes-optional",
                "K1R-m-plan-b-codes-no-review", "K1R-m-plan-b-ignores-gate-families",
                "K1R-m-oext-y-null-passes", "K1R-m-oext-y-before-engine-y", "K1R-m-bqi-decision-no-oext-y",
                # R1 K1 fix round (8 Nov): the verifier's K1V-1..K1V-13 and GXB's fourth to sixth sets
                "K1V-m-stop-kind-old", "K1V-m-stop-value-old", "K1V-m-stop-field-old", "K1V-m-stop-unread-passes",
                "K1V-m-stop-read-unchecked", "K1V-m-stop-exit-type", "K1V-m-dose-192-adds-top", "K1V-m-dose-97-191-192",
                "K1V-m-dose-96-adds-top", "K1V-m-dose-48-top", "K1V-m-dose-below-48-passes",
                "K1V-m-dose-top-pin-rows-unchecked", "K1V-m-plan-b-reason-unchecked", "K1V-m-plan-b-basis-any-option",
                "K1V-m-plan-b-hashes-without-sr2", "K1V-m-plan-b-no-option", "K1V-m-review-plans-a",
                "K1V-m-gate-version-type", "K1V-m-bank500-unpinned-bytes", "K1V-m-flags-unpinned",
                "K1V-m-branch-version-type", "K1V-m-branch-switch-branch-only", "K1V-m-oext-kinds-no-branch",
                "K1V-m-n-units-import-raises", "K1V-m-rejudged-malformed-unnamed", "K1V-m-missing-arm-passes",
                "K1V-m-block0-new-keys", "K1V-m-index-any-family", "K1V-m-index-count-any", "K1V-m-index-no-wrapper",
                "K1V-m-index-not-checked", "K1V-m-y-pin-engine-x", "K1V-m-check-keys-y-reads-x",
                "K1V-m-edit-pin-any-suffix", "K1V-m-files-form-any-dir", "K1V-m-n-units-keys-loose",
                "K1V-m-n-units-r-only"}
    assert required <= set(ids)
    assert len([i for i in ids if i.startswith("K1R-m-")]) >= 79
    assert len([i for i in ids if i.startswith("K1V-m-")]) >= 37
    kf = {"KF-m-sigma-a-plan-any", "KF-m-sigma-a-threshold", "KF-m-sigma-a-unchecked-value",
          "KF-m-sigma-a-null-without-sr2", "KF-m-pool-plan-any", "KF-m-sigma-f-plan-any",
          "KF-m-gate-c-no-sigma-f", "KF-m-gate-b-sigma-f-any", "KF-m-index-old-name", "KF-m-index-y-as-x",
          "KF-m-w1-18-records-many", "KF-m-w1-18-record-any-form", "KF-m-w1-18-folder-any",
          "KF-m-stop-needed-unchecked", "KF-m-stop-of-unchecked", "KF-m-stop-index-range",
          "KF-m-stop-jobdone-form", "KF-m-top-pin-any-arms", "KF-m-branch-texts",
          "KF-m-stop-read-jobdone-optional"}   # R1 K1 follow-up
    assert kf <= set(ids) and len(kf) == 20
    assert {"KF2-m-no-review-ceiling", "KF2-m-ceiling-factor-h", "KF2-m-ceiling-ge"} <= set(ids)   # GXB R-29


# ----------------------------------------------------------------------------------------------------- test 14
STDLIB = {"__future__", "argparse", "datetime", "decimal", "fractions", "hashlib", "json", "math", "os", "pathlib",
          "re", "sys"}                                   # R1 K1 (GXB R-29): fractions for the exact review ceiling


def imports_of(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            out.append(node.module or "")
    return out


def test_14_what_stays_frozen_now():
    assert sys.dont_write_bytecode
    # (a) The engine identity is still X (the engine's own code_identity over the files in this checkout).
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from experiments.safety_selection.common import code_identity   # noqa: E402
    assert code_identity()["sha256"] == R.ENGINE_X
    # (b) The stage-1 kit files this kit reads are unchanged against HEAD (their SHA-256 at fb51421).
    for file, digest in STAGE1_PINS.items():
        assert hashlib.sha256((STAGE1 / file).read_bytes()).hexdigest() == digest, file
    # (c) rules_78b.py and derive_78b_basis.py import stdlib only; nothing from the Gate B kit; no sys.path edits.
    for file in ("rules_78b.py", "derive_78b_basis.py"):
        names = imports_of(KIT / file)
        assert names and set(n.split(".")[0] for n in names) <= STDLIB, (file, names)
        assert not any("gate" in n.lower() for n in names)
        source = (KIT / file).read_text(encoding="utf-8")
        assert "sys.path" not in source
        tree = ast.parse(source)
        code = [line.split("#", 1)[0] for line in source.splitlines()[len(ast.get_docstring(tree).splitlines()) + 1:]]
        assert not any("gate-b-olmo" in line or "gateb" in line for line in code), file   # code, not the docstring
    # (d) No bytecode folder in this kit or in the stage-1 kit (the suite runs with -B / dont_write_bytecode).
    for folder in (KIT, STAGE1):
        assert not list(folder.rglob("__pycache__")), folder


# ----------------------------------------------------------------------------------------------------- test 15
OPENED: list[str] = []
WATCH = {"on": False}


def _audit(event, args):
    if WATCH["on"] and event == "open" and args and isinstance(args[0], (str, bytes, pathlib.Path)):
        OPENED.append(str(args[0]))


sys.addaudithook(_audit)


def fake_kit(root: pathlib.Path, family: str, kit_name: str, host: str, *, batch_s: float = 200.0,
             first_s: float = 250.0, train_s: float = 880.0, outer_min: float = 110.0, traps: bool = True) -> pathlib.Path:
    """A synthetic kit folder of the measured layout, numbers only, with trap files that must stay unopened."""
    kit = root / kit_name
    hostdir = kit / "hosts" / host
    tree = kit / "retrieved" / host / "tree"
    unit = tree / "round1" / "1101-a0-e1-a1"
    unit.mkdir(parents=True)
    hostdir.mkdir(parents=True)
    mem = {"cuda_allocated_bytes": 1, "cuda_peak_allocated_bytes": 26000000000, "cuda_peak_reserved_bytes": 82000000000,
           "cuda_reserved_bytes": 1, "peak_rss_bytes": 1, "rss_bytes": 1}

    def row(stage, start, seconds, **extra):
        return {"stage": stage, "start_s": start, "end_s": start + seconds, "seconds": seconds, "status": "ok",
                "start_utc": "2026-11-20T10:00:00+00:00", "end_utc": "2026-11-20T10:00:01+00:00", "memory": mem, **extra}

    t, ledger, progress = 8.0, [], []
    for stage, seconds, extra in (("load_policy", 7.0, {"trainable_parameters": 159907840, "attn_implementation": "sdpa"}),
                                  ("tokenize", 4.0, {"rows": 4800, "tokens": 996635, "max_tokens": 2114}),
                                  ("memory_preflight", 3.0, {"examples": 2, "max_tokens": 2114, "mean_loss": 2.6}),
                                  ("init_state", 3.0, {"seed": 1101})):
        ledger.append(row(stage, t, seconds, **extra)); t += seconds
    for steps, first in ((10, 1), (28, 11)):
        seconds = train_s * steps / 38
        ledger.append(row("train", t, seconds, steps=steps, first_step=first, last_step=first + steps - 1, examples=steps * 128,
                          input_tokens=steps * 26000, padded_tokens=steps * 38400, target_tokens=steps * 11000, segment="s"))
        t += seconds
        progress.append({"kind": "train", "step": first + steps - 1, "elapsed_s": t, "epoch": 0, "examples_seen": 0,
                         "mean_recent_loss": 1.5, "segment": "s", "utc": "x"})
    ledger.append(row("load_guard", t, 3.0, parameters=4022468096)); t += 3.0
    ledger.append(row("query_loss", t, 20.0, forward_passes=200, input_tokens=45000, queries=200, target_tokens=21000)); t += 20.0
    gen_start = t
    for i in range(15):
        seconds = first_s if i == 0 else batch_s
        t += seconds
        progress.append({"kind": "generate", "batch": i, "rows": 32 if i < 14 else 20, "capped": 2, "checkpoint": "e1",
                         "output_tokens": 6000, "elapsed_s": t, "utc": "x"})
    ledger.append(row("generate", gen_start, t - gen_start, capped=30, output_tokens=90000, prompt_tokens=19600, prompts=468))
    smp_start = t
    for i in range(19):
        t += batch_s if i < 5 else 40.0
        progress.append({"kind": "generate", "batch": i, "rows": 32 if i < 18 else 24, "capped": 1 if i < 5 else 0,
                         "checkpoint": "e1", "output_tokens": 2000, "elapsed_s": t, "utc": "x"})
    ledger.append(row("sample", smp_start, t - smp_start, answers=600, capped=5, output_tokens=38000))
    for stage, seconds, extra in (("arc_utility", 11.0, {"questions": 189, "sequences": 757, "tokens": 55766}),
                                  ("guard", 70.0, {"guard_input_tokens": 280000, "guard_output_tokens": 6200, "invalid": 0, "items": 468}),
                                  ("guard_samples", 80.0, {"invalid": 0, "items": 600}),
                                  ("harm_scores", 90.0, {"answers": 800, "unscored": 0}),
                                  ("verify_trajectory", 0.02, {"steps_verified": 38})):
        ledger.append(row(stage, t, seconds, **extra)); t += seconds
    outer_s = outer_min * 60
    assert outer_s > t
    (unit / "ledger.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ledger))
    (unit / "progress.jsonl").write_text("".join(json.dumps(r) + "\n" for r in progress))
    create = dt.datetime(2026, 11, 20, 9, 0, tzinfo=dt.timezone.utc)
    stop = create + dt.timedelta(seconds=outer_s + 1800)
    (hostdir / "finished.json").write_text(json.dumps({"utc": stop.isoformat(), "status": "verified-and-stopped",
                                                        "outer_exit": 0, "outer_elapsed_min": outer_min, "stop_confirmed": True}))
    (hostdir / "create-result.json").write_text(json.dumps({"utc": create.isoformat(), "status": 201,
                                                             "pod": {"costPerHr": 1.79, "id": "fakepod", "volumeInGb": 50}}))
    (hostdir / "create-intent.json").write_text(json.dumps({"utc": create.isoformat(), "cap_hours": 8.5,
                                                             "request_without_env": {"gpuTypeIds": [R.GPU_NAME]}}))
    (hostdir / "verification.json").write_text(json.dumps({
        "recipe_sha256": R.CONFIGS[family]["main"][1], "manifest_sha256": R.MANIFESTS[family],
        "training_identity": "ab" * 32, "elapsed_s": 1000.0, "generation_memory_ok": True,
        "environment": {"cuda": {"name": R.GPU_NAME, "total_memory_bytes": 85093777408}},
        "cap_projection": {"training_s": 1100.0, "untuned_projected_s": 3200.0, "e1_upper_s": 19000.0,
                           "projected_job_upper_s": 41000.0, "overhead_measured_s": 21.0, "batches_capped": 34},
        "full_length": {"ms_per_step_full": 260.0, "seconds": 340.0, "num_alloc_retries": 0,
                        "peak_reserved_bytes": 84000000000, "peak_allocated_bytes": 66000000000}}))
    (tree / "BOOTSTRAP-READY.json").write_text(json.dumps({"utc": "2026-11-20T09:06:00+00:00", "ok": True,
                                                             "engine_sha256": R.ENGINE_X}))
    (tree / "PREFLIGHT-DONE.json").write_text(json.dumps({"utc": "2026-11-20T09:30:00+00:00", "ok": True,
                                                            "training_s": 1100.0, "ms_per_step_full": 260.0,
                                                            "projected_job_upper_s": 41000.0, "tried": [{"exit": 0}]}))
    (tree / "JOB-DONE.json").write_text(json.dumps({"utc": "2026-11-20T11:00:00+00:00", "ok": True, "host": host}))
    if traps:
        for trap in ("round1/1101-a0-e1-a1/eval/answers.jsonl", "round1/1101-a0-e1-a1/generations.jsonl",
                     "round1/1101-a0-e1-a1/samples.jsonl", "round1/1101-a0-e1-a1/prompts.jsonl",
                     "round1/1101-a0-e1-a1/states/e1/state.json", "round1/1101-a0-e1-a1/COMPLETE.json",
                     "round1/1101-a0-e1-a1/job.json", "round1/registry.jsonl", "selector.jsonl", "hidden/bank.json"):
            p = tree / trap
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("THIS TEXT MUST NEVER BE OPENED\n")
        (hostdir / "ssh").mkdir()
        (hostdir / "ssh" / "id_ed25519").write_text("SECRET\n")
        (hostdir / "stops.jsonl").write_text('{"text": "not allow-listed"}\n')
        (kit / "generations.jsonl").write_text("TRAP\n")
    return kit


def opened_under(root: pathlib.Path) -> list[pathlib.Path]:
    return [pathlib.Path(p) for p in OPENED if str(root) in p]


def test_15_derivation_privacy(tmp_path):
    root = tmp_path / "tmp"
    kit_o = fake_kit(root, "olmo2-7b", "family-probe-sp-olmo2-7b-fake", "sp-olmo2-7b-9101")
    kit_l = fake_kit(root, "llama31-8b", "family-probe-sp-llama31-8b-fake", "sp-llama31-8b-9101", batch_s=210.0)
    OPENED.clear()
    WATCH["on"] = True
    try:
        basis = D.derive(root, kits={"olmo2-7b": ("family-probe-sp-olmo2-7b-fake",),
                                     "llama31-8b": ("family-probe-sp-llama31-8b-fake",)})
    finally:
        WATCH["on"] = False
    opened = opened_under(root)
    assert opened, "the audit hook saw no open"
    for p in opened:
        assert p.name in D.ALLOWED_NAMES, p
        assert not any(part in D.FORBIDDEN_PARTS for part in p.parts), p
    for trap in ("generations.jsonl", "samples.jsonl", "prompts.jsonl", "answers.jsonl", "state.json", "selector.jsonl",
                 "bank.json", "id_ed25519", "stops.jsonl", "COMPLETE.json", "job.json", "registry.jsonl"):
        assert not any(p.name == trap for p in opened), trap
    D.check_strings(basis)                                             # no string longer than a hash, none with text
    text = json.dumps(basis)
    assert "NEVER" not in text and "SECRET" not in text and "TRAP" not in text
    unit = basis["units"][0]
    assert unit["first_greedy_batch_s"] == 250.0 and unit["capped32_batch_max_s"] == 210.0
    assert unit["ledger"]["train_steps"] == 38 and unit["outside_s"] > 0
    # The gate itself: a trap name and a forbidden part refuse before any open.
    OPENED.clear()
    WATCH["on"] = True
    try:
        for bad in (kit_o / "generations.jsonl", kit_o / "retrieved/sp-olmo2-7b-9101/tree/round1/1101-a0-e1-a1/eval/answers.jsonl",
                    kit_o / "hosts/sp-olmo2-7b-9101/ssh/id_ed25519", kit_o / "retrieved/x/tree/selector.jsonl",
                    kit_o / "hidden/ledger.jsonl", kit_o / "hosts/sp-olmo2-7b-9101/stops.jsonl"):
            with pytest.raises(D.RecordRefused):
                D.open_record(bad)
    finally:
        WATCH["on"] = False
    assert not opened_under(root)
    # A-V6: the nine names exactly, each in its own place (hosts/<host>/, retrieved/<host>/tree/, .../tree/round1/<unit>/);
    # a create-*.json of another name, or an allowed name in another folder, refuses before any open.
    host, tree = kit_o / "hosts/sp-olmo2-7b-9101", kit_o / "retrieved/sp-olmo2-7b-9101/tree"
    unit = tree / "round1/1101-a0-e1-a1"
    for good in (host / "verification.json", host / "finished.json", host / "create-intent.json", host / "create-result.json",
                 tree / "BOOTSTRAP-READY.json", tree / "PREFLIGHT-DONE.json", tree / "JOB-DONE.json",
                 unit / "ledger.jsonl", unit / "progress.jsonl"):
        assert D.check_path(good) == good
    assert D.ALLOWED_NAMES == frozenset(D.PLACE_OF) and len(D.ALLOWED_NAMES) == 9
    OPENED.clear()
    WATCH["on"] = True
    try:
        for bad in (host / "create-secrets.json", host / "create-intent.json.bak", host / "create-.json",
                    tree / "cuda-preflight-1/verification.json", tree / "verification.json", unit / "verification.json",
                    host / "ledger.jsonl", host / "progress.jsonl", host / "PREFLIGHT-DONE.json", host / "JOB-DONE.json",
                    tree / "ledger.jsonl", tree / "round1/ledger.jsonl", unit / "PREFLIGHT-DONE.json",
                    unit / "finished.json", kit_o / "finished.json", kit_o / "hosts/finished.json",
                    kit_o / "retrieved/sp-olmo2-7b-9101/finished.json", kit_o / "retrieved/sp-olmo2-7b-9101/BOOTSTRAP-READY.json",
                    tree / "round1/1101-a0-e1-a1/sub/ledger.jsonl", pathlib.Path("verification.json"),
                    pathlib.Path("hosts/verification.json"),
                    # in place, but a forbidden part names the kit root, the host or the unit folder
                    root / "units/family-probe-sp-x/hosts/h/finished.json", root / "k/hosts/eval/verification.json",
                    root / "k/retrieved/samples/tree/PREFLIGHT-DONE.json", tree / "round1/samples/ledger.jsonl",
                    root / "k/retrieved/h/tree/round1/hidden/progress.jsonl",
                    # D4: the unit place needs retrieved/<host>/tree/round1/<unit>/ exactly (tree and retrieved parts)
                    root / "k/round1/u/ledger.jsonl", root / "k/other/h/tree/round1/u/progress.jsonl",
                    root / "k/retrieved/h/other/round1/u/ledger.jsonl", root / "k/retrieved/h/tree/other/u/ledger.jsonl"):
            with pytest.raises(D.RecordRefused):
                D.check_path(bad)
            with pytest.raises(D.RecordRefused):
                D.open_record(bad)
    finally:
        WATCH["on"] = False
    assert not opened_under(root)
    # KD9: an extra unit joins the basis and is listed with its engine.
    extra = fake_kit(root, "olmo2-7b", "family-probe-s78-olmo2-7b-y1", "olmo2-7b-y-1", traps=False, batch_s=230.0)
    basis2 = D.derive(root, extra=[("olmo2-7b", extra)],
                      kits={"olmo2-7b": ("family-probe-sp-olmo2-7b-fake",), "llama31-8b": ("family-probe-sp-llama31-8b-fake",)})
    assert basis2["families"]["olmo2-7b"]["n_units"] == 2 and basis2["families"]["olmo2-7b"]["batch_max_s"] == 230.0
    with pytest.raises(D.RecordRefused):
        D.check_strings({"note": "a sentence with several words in it"})
    with pytest.raises(D.RecordRefused):
        D.check_strings({"h": "x" * 65})


def test_15b_derivation_on_the_measured_root_opens_allow_listed_names_only():
    if not MEASURED_ROOT.is_dir() or not (MEASURED_ROOT / D.UNIT_KITS["olmo2-7b"][0]).is_dir():
        pytest.skip("the measured kits are not under this checkout's tmp/")
    OPENED.clear()
    WATCH["on"] = True
    try:
        basis = D.derive(MEASURED_ROOT)
    finally:
        WATCH["on"] = False
    opened = opened_under(MEASURED_ROOT)
    assert len(opened) >= 17 * 9
    for p in opened:
        assert p.name in D.ALLOWED_NAMES, p
        assert not any(part in D.FORBIDDEN_PARTS for part in p.parts), p
    D.check_strings(basis)


# ----------------------------------------------------------------------- the fix round (fix-K-core): D1, D2, PP7, PP8
LLAMA_PIN = "2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c"
GATEB_PIN = "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"
# N's three R edits in each committed set (M: shasum -a 256 of the files, 5 Nov 2026; the MANIFEST's arm strings).
REAL_R_EDITS = {
    "llama31-8b": {1: "5cdedf22c1002ef1c6d0322d44c253ef57580ddb1dda85e8119a8b3842dc29b4",
                   2: "8f9f3cd5027d9268b28e3cf4189987a820b26a6d6d77fbe83ea0ad145944bb95",
                   3: "edbc111b2ff3a446ae195a79f0e5965c9a82fa744266d57c9c15e4c4c775dd2e"},
    "olmo2-7b": {1: "f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd",
                 2: "913b73606ff64c104751e3f86bd3b69838a27686720a92858c08f4cf087d8060",
                 3: "cd8d3328c48957ed0a164a8775ca2695a3d77d51865fd32c2ee53aded939502b"},
}


def gateb_form(r_draws=(1, 2, 3), m_draws=(1, 2), units=2) -> dict:
    """A synthetic MANIFEST in Gate B's form: role "edit" on every edit; R_d by draw; M-family edits with draws 1-2 of
    their own (the trap D1 and V-H17 name); unit edits without a draw; two non-edit entries outside edits/."""
    files = [{"role": "edit", "family": "R", "draw": d, "arm": f"edit-{('%02x' % d) * 32}", "path": f"edits/R_d{d}.json",
              "sha256": ("%02x" % d) * 32, "bytes": 19410} for d in r_draws]
    for u in range(units):
        files.append({"role": "edit", "family": "unit", "unit": f"g-{u:016x}", "category": "open_qa",
                      "arm": f"edit-{('a%d' % u) * 32}", "path": f"edits/unit_g-{u:016x}.json", "sha256": ("a%d" % u) * 32,
                      "bytes": 17980})
        for d in m_draws:
            files.append({"role": "edit", "family": "M", "draw": d, "unit": f"g-{u:016x}", "category": "open_qa",
                          "arm": f"edit-{('b%d' % (u * 2 + d)) * 32}", "path": f"edits/M_g-{u:016x}_d{d}.json",
                          "sha256": ("b%d" % (u * 2 + d)) * 32, "bytes": 20176})
    files += [{"role": "counts", "path": "unit_table.json", "sha256": "c" * 64, "bytes": 10},
              {"role": "gate-c sample", "path": "gate_c_sample.json", "sha256": "d" * 64, "bytes": 10, "rows": 3}]
    return {"kind": "gate-b sealed files manifest (synthetic)", "version": 1, "files": files}


def llama_form(r_draws=range(1, 17), units=2, seed_offset=1100) -> dict:
    """A synthetic MANIFEST in the committed Llama set's form: descriptive role strings (never "edit"), a seed on each R
    entry, same_rows_as, unit entries at role "unit removal", a top-level roles map."""
    role = {d: ("block 0 (N): R_1-R_3 at 1101-1103 (P78 section 3; ruling 11, N's layout)" if d <= 3
                else "block A: R_4, R_5 at 1104-1105 (the readiness plan T4 step 3)" if d <= 5 else "later blocks")
            for d in r_draws}
    files = [{"role": role[d], "family": "R", "draw": d, "seed": seed_offset + d, "arm": f"edit-{('%02x' % d) * 32}",
              "path": f"edits/R_d{d}.json", "sha256": ("%02x" % d) * 32, "bytes": 19400, "rows": 600,
              "same_rows_as": {"file": None, "note": "synthetic"}} for d in r_draws]
    files += [{"role": "unit removal", "family": "unit", "unit": f"g-{u:016x}", "category": "open_qa",
               "arm": f"edit-{('a%d' % u) * 32}", "path": f"edits/unit_g-{u:016x}.json", "sha256": ("a%d" % u) * 32,
               "bytes": 17980, "rows": 300, "same_rows_as": {"file": None}} for u in range(units)]
    return {"kind": "scale-78b sealed llama3 files manifest (synthetic)", "version": 1, "files": files,
            "roles": {str(d): role[d] for d in r_draws}}


def test_17_pp8_the_s78_kinds_and_their_caps(tmp_path):
    """PP8 (PP3, PP4): S78_KINDS = {retrain, rep_pass, a1_pass, classifier}; each refuses at the runner's gate and the
    pod's key check while RECIPE_S is null and runs under S_78 only once filled; a1_pass carries A1's 16.5 h cap at
    most, rep_pass its own E cap (the 1B 1 h estimate x 2.3 x 1.5 = 4.75 h); the scorer table and the labels name both."""
    assert R.S78_KINDS == frozenset({"retrain", "rep_pass", "a1_pass", "classifier"})
    assert "a1_pass" in R.E_KINDS and "rep_pass" in R.E_KINDS and "a1_pass" not in R.MEASURED_KINDS
    assert R.SCORER_KINDS == ("untuned_answers", "o_only", "o_only_with_regenerate", "anchor", "rep_pass", "a1_pass",
                              "l1_scan", "classifier", "c0")                # PP17: no standalone regenerate kind
    assert "regenerate" not in R.E_KINDS and "regenerate" not in R.KIND_LABELS and "regenerate" not in R.SC_KINDS
    assert set(R.S78_KINDS) - {"retrain"} <= set(R.SCORER_KINDS)
    assert set(R.KIND_LABELS) >= set(R.SCORER_KINDS) | {"retrain"}
    assert "REQ-3" in R.KIND_LABELS["rep_pass"] and "A1" in R.KIND_LABELS["a1_pass"] and "16.5 h" in R.KIND_LABELS["a1_pass"]
    for label in R.KIND_LABELS.values():
        assert label and len(label) < 160
    for family, f in R.FAMILIES.items():
        pre = fake_preflight_done(tmp_path, training_s=f["PRE_TRAINING_S_MAX"], ms_per_step_full=f["PRE_MS_PER_STEP_MAX"])
        ver = fake_verification(cp_training_s=f["PRE_TRAINING_S_MAX"])
        assert R.e_cap_hours(family, "a1_pass") == 16.5 and R.e_cap_hours(family, "rep_pass") == 4.75
        assert R.e_cap_hours(family, "classifier") == 3.25
        for kind in ("rep_pass", "a1_pass", "classifier"):
            job = R.job_record(family, kind)
            assert job["unmeasured"] and job["counted"] == 0
            assert R.e_pod(family, kind)["cap_hours"] == R.e_cap_hours(family, kind)       # priced before S_78 (M3)
            with pytest.raises(R.Refused, match="recipe S_78"):
                R.job_decision(family, pre, ver, job, 20 * 3600.0, 20.0)
            with pytest.raises(R.Refused):                                                 # the main config: not S_78
                R.check_keys(**keys_of(family, kind=kind))
            with pytest.raises(R.Refused):
                R.check_keys(**keys_of(family, kind=kind, recipe_sha256=R.CONFIGS[family]["g"][1]))
        for kind in ("l1_scan", "anchor", "untuned_answers", "o_only", "o_only_with_regenerate", "c0"):   # X, main
            assert R.job_decision(family, pre, ver, R.job_record(family, kind), 20 * 3600.0, 20.0)["action"] == "run"
            R.check_keys(**keys_of(family, kind=kind))
    report = R.block0_report()
    for family in R.FAMILIES:
        pods = report["scorer_pods"][family]
        assert set(pods) == set(R.SCORER_KINDS)
        assert pods["a1_pass"]["cap_hours"] == 16.5 and pods["a1_pass"]["need_usd_alone"] == 45.66
        assert pods["rep_pass"]["cap_hours"] == 4.75 and pods["rep_pass"]["need_usd_alone"] == 18.49
        assert pods["rep_pass"]["guard_usd"] == 14.79                                       # $6 + 4.75 x $1.85
    assert R.main(["e-caps"]) == 0


def test_17b_pp8_the_s78_kinds_run_under_s78_once_filled(monkeypatch, tmp_path):
    f = "olmo2-7b"
    c = R.FAMILIES[f]
    pre = fake_preflight_done(tmp_path, training_s=c["PRE_TRAINING_S_MAX"], ms_per_step_full=c["PRE_MS_PER_STEP_MAX"])
    ver = fake_verification(cp_training_s=c["PRE_TRAINING_S_MAX"])
    s78 = "ef" * 32
    monkeypatch.setitem(R.RECIPE_S, f, s78)
    for kind in R.S78_KINDS:
        R.check_keys(**keys_of(f, kind=kind, recipe_sha256=s78))
        with pytest.raises(R.Refused):
            R.check_keys(**keys_of(f, kind=kind))
        d = R.job_decision(f, pre, ver, R.job_record(f, kind), 20 * 3600.0, 20.0)
        assert d["action"] == "run" and d["requirement_s"] == R.job_record(f, kind)["start_requirement_s"]
    with pytest.raises(R.Refused):                                                         # the other family stays null
        R.job_decision("llama31-8b", pre, ver, R.job_record("llama31-8b", "classifier"), 20 * 3600.0, 20.0)
    with pytest.raises(R.Refused):                                                         # l1_scan never runs under S_78
        R.check_keys(**keys_of(f, kind="l1_scan", recipe_sha256=s78))


def test_18_d1_the_sealed_edit_entries_in_both_committed_forms():
    """D1: block0_r_edits reads N's R edits from a MANIFEST in Gate B's form (role "edit"; M-family edits with draws
    1-2 of their own) and in the committed Llama set's form (descriptive roles, a seed per R entry); an entry is R_d by
    family "R" AND draw d, never by draw alone; a wrong seed, a duplicate draw or a missing draw refuses; the two
    non-edit entries and paths outside edits/ never count."""
    for man in (gateb_form(), llama_form()):
        out = R.block0_r_edits(man)
        assert sorted(out) == [1, 2, 3]
        for d, e in out.items():
            assert e == {"draw": d, "seed": 1100 + d, "arm": f"edit-{('%02x' % d) * 32}", "path": f"edits/R_d{d}.json",
                         "sha256": ("%02x" % d) * 32}
        edits = [e for e in man["files"] if R.sealed_edit_entry(e)]
        assert all(e["path"].startswith("edits/") for e in edits)
        assert {e["family"] for e in edits} <= {"R", "M", "unit"}
        assert not any(R.sealed_edit_entry(e) for e in man["files"] if e.get("path") in ("unit_table.json", "gate_c_sample.json"))
    gb = gateb_form()
    assert sum(1 for e in gb["files"] if R.sealed_edit_entry(e)) == 3 + 2 + 4           # R, unit, M (2 units x 2 draws)
    assert sum(1 for e in gb["files"] if R.sealed_edit_entry(e) and e["family"] == "M" and e["draw"] == 1) == 2
    assert sum(1 for e in llama_form()["files"] if R.sealed_edit_entry(e)) == 16 + 2
    # by draw alone, Gate B's form would hold three entries for draw 1 (R_d1 and two M edits): block0_r_edits must not
    assert len([e for e in gb["files"] if e.get("draw") == 1]) == 3
    assert R.block0_r_edits(gb)[1]["path"] == "edits/R_d1.json"
    # the Llama form's seed must be 1100 + d
    bad = llama_form()
    bad["files"][0]["seed"] = 1102
    with pytest.raises(R.Refused, match="seed 1102, not 1101"):
        R.block0_r_edits(bad)
    # a duplicate draw refuses (an extra R_d1 at another path)
    dup = gateb_form()
    dup["files"].append({**dup["files"][0], "path": "edits/R_d1_again.json", "sha256": "e" * 64})
    with pytest.raises(R.Refused, match="two R_d1"):
        R.block0_r_edits(dup)
    # a stray entry at an R draw outside edits/ (a sample file) is not an edit entry and does not duplicate R_d1
    stray = gateb_form()
    stray["files"].append({"role": "sample", "family": "R", "draw": 1, "arm": "edit-" + "f" * 64, "path": "samples/R_d1.json",
                           "sha256": "f" * 64})
    assert R.block0_r_edits(stray)[1]["sha256"] == "01" * 32
    # a missing draw refuses, with the draws named
    with pytest.raises(R.Refused, match=r"no R edit for draw\(s\) \[3\]"):
        R.block0_r_edits(gateb_form(r_draws=(1, 2)))
    with pytest.raises(R.Refused, match=r"no R edit for draw\(s\) \[2, 3\]"):
        R.block0_r_edits(llama_form(r_draws=(1, 4, 5)))
    with pytest.raises(R.Refused):
        R.block0_r_edits({"files": "none"})
    # entries without a family, a non-hex sha256, a bool draw or an empty role are never edit entries
    for e in ({"role": "edit", "draw": 1, "arm": "edit-x", "path": "edits/R_d1.json", "sha256": "01" * 32},
              {"role": "edit", "family": "R", "draw": 1, "arm": "edit-x", "path": "edits/R_d1.json", "sha256": "0g" * 32},
              {"role": "", "family": "R", "draw": 1, "arm": "edit-x", "path": "edits/R_d1.json", "sha256": "01" * 32},
              {"role": "edit", "family": "R", "draw": 1, "arm": "", "path": "edits/R_d1.json", "sha256": "01" * 32},
              {"role": "edit", "family": "R", "draw": 1, "arm": "edit-x", "path": "edits/../R_d1.json", "sha256": "01" * 32},
              "edits/R_d1.json", None):
        assert not R.sealed_edit_entry(e)
    one = {"files": [{"role": "edit", "family": "R", "draw": True, "arm": "edit-x", "path": "edits/R_d1.json", "sha256": "01" * 32}]}
    with pytest.raises(R.Refused, match="no R edit"):
        R.block0_r_edits(one, (1,))


def test_18b_d1_the_committed_sets_by_pin():
    """The real-set test (D1): each family's committed MANIFEST hashes to its pin, and block 0's R_d1-R_d3 resolve to
    the committed edit files by arm, seed and SHA-256 (the files are hashed; no row is read)."""
    for family, pin in (("llama31-8b", LLAMA_PIN), ("olmo2-7b", GATEB_PIN)):
        path = ROOT / R.SEALED_SETS[family]["path"]
        assert path.is_file(), f"{family}: {R.SEALED_SETS[family]['path']} is not in this checkout (d422fca for Llama)"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == pin == R.SEALED_SETS[family]["sha256"]
        man = json.loads(path.read_text(encoding="utf-8"))
        out = R.block0_r_edits(man)
        assert {d: e["sha256"] for d, e in out.items()} == REAL_R_EDITS[family]
        assert {d: e["seed"] for d, e in out.items()} == {1: 1101, 2: 1102, 3: 1103}
        for d, e in out.items():
            assert e["arm"] == f"edit-{REAL_R_EDITS[family][d]}" and e["path"] == f"edits/R_d{d}.json"
            edit = path.parent / e["path"]
            assert hashlib.sha256(edit.read_bytes()).hexdigest() == e["sha256"]
            doc = json.loads(edit.read_text(encoding="utf-8"))                     # one key read: the prepared set
            assert doc.get("manifest_sha256") == R.MANIFESTS[family]
    llama = json.loads((ROOT / R.SEALED_SETS["llama31-8b"]["path"]).read_text(encoding="utf-8"))
    assert not any(e.get("role") == "edit" for e in llama["files"])                  # the form D1 describes
    assert llama["roles"]["1"].startswith("block 0 (N): R_1-R_3 at 1101-1103")
    gateb = json.loads((ROOT / R.SEALED_SETS["olmo2-7b"]["path"]).read_text(encoding="utf-8"))
    assert sum(1 for e in gateb["files"] if e.get("family") == "M" and e.get("draw") in (1, 2)) == 16   # the M trap


def test_19_d2_the_idle_storage_line():
    """D2 (KD5; Part 1 §12; KCR:161): about $0.33 per day per stopped 50 GB pod that keeps its states, at $0.20 per GB
    per month; N's two pods $0.67 per day, $20 per month; in block0_report."""
    one = R.idle_storage(1)
    assert one["usd_per_pod_day"] == 0.33 == R.cents(50 * 0.20 / 30) and one["usd_per_day"] == 0.33
    assert one["usd_per_month"] == 10.0 and one["volume_gb"] == 50 and one["usd_per_gb_month"] == 0.20
    two = R.idle_storage(2)
    assert two["usd_per_day"] == 0.67 and two["usd_per_month"] == 20.0 and two["n_pods_kept"] == 2
    assert R.idle_storage(10)["usd_per_month"] == 100.0                               # KCR:161's "10 such pods, about $100"
    assert R.idle_storage(0)["usd_per_day"] == 0.0
    assert two["basis"].startswith("E:") and "KCR:161" in two["basis"] and "counted in no guard" in two["basis"]
    for bad in (-1, 1.5, True, None):
        with pytest.raises(R.Refused):
            R.idle_storage(bad)
    report = R.block0_report()
    assert report["idle_storage"] == two
    assert R.IDLE_STORAGE_USD_PER_GB_MONTH == 0.20 and R.IDLE_DAYS_PER_MONTH == 30 and R.VOLUME_GB == 50


def test_20_pp16_the_wrapper_kinds_run_on_engine_x_only_whatever_engine_y_holds(monkeypatch, tmp_path):
    """PP16 (PP4 enforced; the core re-verifier's DK-4): X_ONLY_KINDS is the lead's list, engine_allowed checks it
    first, so once ENGINE_Y is filled (test-local here) and even after KD9's Y_MEASURED, every wrapper kind refuses
    on Y (and on a third engine) at engine_allowed and at the pod's key check, and runs on X. The retrain and a1_pass
    (the engine's own jobs; ruling 10, A13) run on Y once it is filled."""
    assert R.X_ONLY_KINDS == frozenset({"untuned_answers", "o_only", "o_only_with_regenerate", "anchor", "rep_pass",
                                        "l1_scan", "classifier", "c0", "w1_18"})   # PP16 with PP17's kind; R1 K1's w1_18
    assert R.X_ONLY_KINDS <= set(R.E_KINDS) and not R.X_ONLY_KINDS & {"retrain", "a1_pass"}
    assert R.ENGINE_Y is None                                                   # the committed pin stays null
    y, third = "d3" * 32, "34bfd289" + "0" * 56
    s78 = "ef" * 32
    for setting in ((None, False), (y, False), (y, True)):
        monkeypatch.setattr(R, "ENGINE_Y", setting[0])
        monkeypatch.setattr(R, "Y_MEASURED", setting[1])
        for kind in sorted(R.X_ONLY_KINDS):
            assert R.engine_allowed(kind, R.ENGINE_X), kind
            assert not R.engine_allowed(kind, y) and not R.engine_allowed(kind, third), (kind, setting)
    monkeypatch.setattr(R, "ENGINE_Y", y)
    monkeypatch.setattr(R, "Y_MEASURED", False)
    monkeypatch.setitem(R.RECIPE_S, "olmo2-7b", s78)
    for kind in sorted(R.X_ONLY_KINDS):
        recipe = s78 if kind in R.S78_KINDS else R.CONFIGS["olmo2-7b"]["main"][1]
        R.check_keys(**keys_of("olmo2-7b", kind=kind, recipe_sha256=recipe))                # X: runs
        with pytest.raises(R.Refused, match="the wrapper kinds only, PP16"):
            R.check_keys(**keys_of("olmo2-7b", kind=kind, recipe_sha256=recipe, engine_sha256=y))
    for kind in ("retrain", "a1_pass"):                                         # the engine's own jobs: Y once filled
        assert R.engine_allowed(kind, y) and R.engine_allowed(kind, R.ENGINE_X)
        R.check_keys(**keys_of("olmo2-7b", kind=kind, recipe_sha256=s78, engine_sha256=y))
    assert "(engine X; PP4)" in R.KIND_LABELS["l1_scan"]


def test_21_dk3_the_kits_stage1_rules_kind_sets_hold_the_pp3_kinds():
    """The core re-verifier's DK-3, as round 4b's D8 and PP18 settle it: rep_pass and the classifier are unitless (no
    unit of their own), a1_pass is NOT (it writes the engine's attributes unit, recorded by its COMPLETE.json and the
    engine's verify, as the 1B kit's a1_rescore), c0 is unitless (PP18: its outputs are hashed under its job folder);
    all three scorer kinds are diagnostic kinds (C1, PP3). Loaded by path from the committed kit folder (no family)."""
    kit_rules = load_by_path("stage1_rules_78b_kit_dk3", KIT / "stage1_rules.py")
    try:
        for kind in ("rep_pass", "a1_pass", "classifier"):
            assert (kind in kit_rules.UNITLESS_KINDS) is (kind != "a1_pass"), kind
            assert kind in kit_rules.DIAG_KINDS, kind
        assert kit_rules.UNITLESS_KINDS == frozenset({"untuned_answers", "rep_pass", "l1_scan", "classifier", "anchor",
                                                      "o_only", "c0"})
        assert kit_rules.DIAG_KINDS == ("rep_pass", "a1_pass", "untuned_answers", "l1_scan", "classifier")
        assert kit_rules.FAMILY is None and kit_rules.r78 is R
    finally:
        sys.modules.pop("stage1_rules_78b_kit_dk3", None)


def test_22_pp14_an_idle_storage_line_for_every_block0_pod_that_keeps_states():
    """PP14 with round 4b's one definition (the core verifier's D4): block 0's need prints an idle-storage line for
    every pod that keeps states after its job: N's two pods (D2's line), and per family every pod of SC_STATE_KINDS
    the scorer block plans (the retrain, a1_pass, one o_only_with_regenerate pod per reused a0 seed (PP17: OLMo
    1101-1103, Llama 1101-1102), c0), and the total; about $0.33 per stopped 50 GB pod per day (KCR:161), counted in
    no guard. The scorer block's sc_pod reads the same constant."""
    report = R.block0_report()
    pods = report["idle_storage_pods"]
    per_family = {"olmo2-7b": (1101, 1102, 1103), "llama31-8b": (1101, 1102)}
    want = ["N olmo2-7b-0-1", "N llama31-8b-0-1"]
    for fam, seeds in per_family.items():
        want += [f"retrain {fam}", f"scorer {fam} a1_pass"] + [f"scorer {fam} o_only_with_regenerate {s}" for s in seeds]
        want += [f"scorer {fam} c0"]
    assert [p["pod"] for p in pods] == want and len(want) == 13
    assert all(p["usd_per_day"] == 0.33 and p["usd_per_month"] == 10.0 and p["why"] for p in pods)
    assert list(R.SC_STATE_KINDS) == ["retrain", "a1_pass", "o_only_with_regenerate", "c0"]
    assert R.IDLE_SCORER_KINDS == {k: v for k, v in R.SC_STATE_KINDS.items() if k != "retrain"}
    assert set(R.IDLE_SCORER_KINDS) <= set(R.SCORER_KINDS) and set(R.SC_STATE_KINDS) <= set(R.SC_KINDS)
    for fam in R.FAMILIES:                                      # the scorer block's printout reads the same constant
        for kind in R.SC_KINDS:
            assert R.sc_pod(fam, kind)["idle_storage"]["keeps_states"] is (kind in R.SC_STATE_KINDS), (fam, kind)
    assert report["idle_storage_all"] == R.idle_storage(13)
    assert report["idle_storage_all"]["usd_per_day"] == 4.33 and report["idle_storage_all"]["usd_per_month"] == 130.0
    assert report["idle_storage"] == R.idle_storage(2)                          # D2's N block, unchanged
    lines = R.idle_storage_lines(report)
    assert len(lines) == 1 + 11 + 1
    assert lines[0].startswith("idle storage (KD5; E, KCR:161): about $0.33 per day per stopped 50 GB pod")
    assert "N's 2 pods kept stopped: $0.67 per day, about $20.00 per month; counted in no guard" in lines[0]
    for line, pod in zip(lines[1:12], want[2:]):
        assert line.startswith(f"idle storage {pod} (KD5, PP14; E, KCR:161): ")
        assert line.endswith("about $0.33 per day, about $10.00 per month while kept stopped; counted in no guard")
    assert "q and e1 states" in lines[1] and "q and e1 states" in lines[2] and "regenerated a0 unit" in lines[3]
    assert "OUT/train" in lines[6]
    assert lines[12] == ("idle storage block 0 in all (KD5, PP14; E): 13 pods if every pod above is kept stopped: "
                         "$4.33 per day, about $130.00 per month; counted in no guard")


# ==================================================================================== R1 K1: blocks A and B (8 Nov)
def hx(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def oext_pin(family: str, engine: str = "X", bank: str | None = None) -> dict:
    """A synthetic OEXT_78B[F] (engine X) or OEXT_78B_Y[F] (engine Y) record in GXB R-5's form: the wrapper and the
    family's own index for its engine among the files, by path and SHA-256."""
    index = f"scripts/scale78b/settings/OEXT-78B{'-Y' if engine == 'Y' else ''}__{family}.json"   # Track O's names
    return {"files": {R.OEXT_WRAPPER_78B: hx("wrapper"), index: hx(f"index-{family}-{engine}")},
            "inputs": {"oext_bank": bank or hx("b"), "oext_record": hx("r")}}


def kit_copy(tmp_path: pathlib.Path, family: str, block: str):
    """stage1_rules.py in a KD7 working copy (tmp/family-probe-s78-<family>-<block>/); it imports this rules_78b."""
    folder = tmp_path / f"family-probe-s78-{family}-{block}"
    folder.mkdir(parents=True)
    shutil.copy2(KIT / "stage1_rules.py", folder / "stage1_rules.py")
    name = f"sr78_k1_{family}_{block}".replace("-", "_")
    try:
        module = load_by_path(name, folder / "stage1_rules.py")
    finally:
        sys.modules.pop(name, None)
    assert module.r78 is R and module.FAMILY == family
    return module


def preflight_pair(family: str) -> tuple[dict, dict]:
    """A PREFLIGHT-DONE.json document and its verification.json for ``family`` at 0.9 x the slowest measured preflight
    (s_pod = 1), in fake_preflight_done's and fake_verification's forms (the runner's gate reads parsed documents)."""
    training = 0.9 * R.FAMILIES[family]["PRE_TRAINING_S_MAX"]
    done = {"utc": "2026-11-20T10:00:00+00:00", "ok": True, "folder": "cuda-preflight-1", "generation_batch": 32,
            "ms_per_step_full": 0.9 * R.FAMILIES[family]["PRE_MS_PER_STEP_MAX"], "overhead_s": 1000,
            "training_s": training, "verification_sha256": "cd" * 32}
    return done, fake_verification(cp_training_s=training)


def test_23_k1_the_block_table_tests_run_here_too(tmp_path):
    """The rules mutation runner runs this file only, so every test of test_block_tables_78b.py (each takes at most
    tmp_path and monkeypatch, no parameters) also runs here, each in its own folder and monkeypatch context."""
    bt = load_by_path("test_block_tables_78b_via_rules", HERE / "test_block_tables_78b.py")
    try:
        names = sorted(n for n in dir(bt) if n.startswith("test_") and callable(getattr(bt, n)))
        assert len(names) >= 19
        for name in names:
            fn = getattr(bt, name)
            params = set(inspect.signature(fn).parameters)
            assert params <= {"tmp_path", "monkeypatch"}, name
            with pytest.MonkeyPatch.context() as mp:
                kwargs = {}
                if "tmp_path" in params:
                    (tmp_path / name).mkdir()
                    kwargs["tmp_path"] = tmp_path / name
                if "monkeypatch" in params:
                    kwargs["monkeypatch"] = mp
                fn(**kwargs)
    finally:
        sys.modules.pop("test_block_tables_78b_via_rules", None)


def test_24_o1_every_arm_trains_ceil_rows_over_128_steps():
    """GXB O1 (ruled): steps = ceil(rows / 128) of the arm's training rows, derived from its edit's resulting row
    count; a named arm whose derived steps differ from RK's STEPS refuses (33 removal, 38 add and a0, 39 for S4_96 and
    S4_192); S4_top takes ceil((4,800 + n) / 128). The named steps are RK's STEPS."""
    assert R.ROWS_PER_STEP == 128 and R.BASE_ROWS == 4800
    assert R.STEPS == {"remove": 33, "add": 38, "a0": 38, "dose": 39}
    assert R.ARM_STEPS == {"R": 33, "A1": 33, "L1": 33, "H1": 33, "S1": 38, "S3": 38, "S4": 38, "S4_96": 39,
                           "S4_192": 39, "a0": 38}
    for arm in R.ARM_STEPS:
        edit = R.ARM_EDIT[arm]
        rows = 4800 if edit is None else R.arm_training_rows(arm, edit[1])
        assert R.arm_steps(arm, rows) == R.ARM_STEPS[arm] == -(-rows // 128), arm
    assert [R.arm_steps("s4_top", 4800 + n) for n in (48, 64, 65, 191)] == [38, 38, 39, 39]
    with pytest.raises(R.Refused, match="RK names 39"):
        R.arm_steps("S4_96", 4848)
    with pytest.raises(R.Refused, match="RK names 33"):
        R.arm_steps("A1", 4352)                                          # ceil(4,352 / 128) = 34
    with pytest.raises(R.Refused, match="unknown arm"):
        R.arm_steps("S5", 4800)


def test_25_kd2_the_pod_layout_and_train_scales_input():
    """Part 2 §2.4 (KD2) and §2.1: at most 4 counted arms per pod, arms interleaved across pods within a block, mixed
    33/38/39-step pods with each arm's own steps in its cap; train_scale's input per arm (the edit's padded tokens per
    step) reaches the cap's requirement (requirements() reads the job's own count, not 1)."""
    for family in R.FAMILIES:
        pods = R.deal_ab(R.block_runs_78b(family, None, "A"))
        assert [len(p) for p in pods] == [4, 4, 4, 3, 3, 3]
        assert [p[0] for p in pods] == [("A1", 1102), ("A1", 1103), ("A1", 1104), ("L1", 1102), ("L1", 1103),
                                        ("L1", 1104)]                    # interleaved: A1's seeds on three pods
        a0 = R.FAMILIES[family]["A0_PADDED_TOKENS_PER_STEP"]
        job = R.job_record(family, "arm", 33, "H1", 1102, a0 * 1.5, oext=True)
        assert job["padded_tokens_per_step"] == a0 * 1.5
        assert R.requirements([job])[0] == pytest.approx(R.requirement_s(family, 33, "arm", 1.0, 1.0, None, a0 * 1.5,
                                                                          True))
        assert R.requirements([job])[0] > R.requirements([R.job_record(family, "arm", 33, oext=True)])[0]
        mixed = [R.job_record(family, "arm", s, oext=True) for s in (33, 38, 39)]
        assert [j["steps"] for j in mixed] == [33, 38, 39]
        assert R.requirements(mixed)[2] - R.requirements(mixed)[1] == pytest.approx(R.FAMILIES[family]["TRAIN_STEP_MAX_S"])
    with pytest.raises(R.Refused, match="one arm twice"):
        R.deal_ab([("S1", 1105), ("S1", 1106), ("S1", 1107), ("S1", 1108), ("S1", 1109)])


def test_26_the_oext_cap_term_x15_until_measured(monkeypatch):
    """DESO item 24 (a), (b); Part 2 §4.3; GXB O12: the in-job O-ext term (13 PHTest batches at the cap, half the
    scoring allowance, the early and outside time: 3,959 s OLMo, 4,061 s Llama) x 1.5 until measured, in the arm's cap
    (arm, a0_arm, ref_train) and the references' E caps. 4 arms per pod: 17.25 h / 19.25 h; four-pod need $167.06 /
    $185.56 (Part 2 §4.3's table). Block 0's arms carry no term (N's caps stay 8.5 h / 12.5 h). A measured value
    replaces the 1.5 x term by a recorded step."""
    want = {"olmo2-7b": (3958.904, 17.25, 167.06, 10.5), "llama31-8b": (4061.446, 19.25, 185.56, 12.5)}
    for family, (pass_s, cap, need, plain) in want.items():
        assert R.oext_pass_of(R.FAMILIES[family]) == pytest.approx(pass_s)
        assert R.oext_term_s(family) == pytest.approx(1.5 * pass_s) and R.OEXT_TERM_FACTOR == 1.5
        jobs = R.arm_pod(family, [33, 33, 33, 38], oext=True)
        assert R.cap_hours(jobs) == cap and R.cap_hours(R.arm_pod(family, [33, 33, 33, 38])) == plain
        assert all(j["oext"] is True for j in jobs)
        assert jobs[0]["measured_upper_s"] == pytest.approx(R.measured_upper_s(family) + R.oext_term_s(family))
        assert jobs[0]["spend_upper_s"] == jobs[0]["measured_upper_s"]
        assert jobs[0]["upper_s"] == pytest.approx(R.upper_m_s(family, 33) + R.oext_term_s(family))
        pods = [{"cap_hours": cap, "spend_usd": 0.0}] * 4
        assert R.funding_need_usd([pods], R.CONTINGENCY_FACTOR)["need_usd"] == need
        assert R.cap_hours(R.block0_jobs(family)) == R.KIT[family]["block0"]["cap_hours"]   # N: no O-ext step
        assert not any(j.get("oext") for j in R.block0_jobs(family))
        assert not {"oext", "padded_tokens_per_step"} & set(R.block0_jobs(family)[0])   # GXB R-3
        for kind in ("a0_arm", "ref_train"):
            assert R.job_record(family, kind, oext=True)["upper_s"] == pytest.approx(
                R.job_record(family, kind)["upper_s"] + R.oext_term_s(family))
        with pytest.raises(R.Refused, match="carries no in-job O-ext step"):
            R.job_record(family, "evalonly", oext=True)
        with pytest.raises(R.Refused, match="E-capped kind"):
            R.job_record(family, "o_only", oext=True)
        with pytest.raises(R.Refused, match="True or False"):
            R.job_record(family, "arm", 33, oext=1)
        for kind, per in (("ref_eval", 2), ("safe_lora", 2)):           # the references: one term per point
            assert R.e_upper_s(family, kind, 2)["upper_s"] - R.e_upper_s(family, kind, 1)["upper_s"] == pytest.approx(
                R.evalonly_upper_s(family) + R.oext_term_s(family))
            assert "O-ext" in R.e_upper_s(family, kind)["basis"]
        bqi = R.e_upper_s(family, "ref_train_bqi")["upper_s"]
        monkeypatch.setitem(R.OEXT_TERM_MEASURED_S, family, 1000.0)
        assert R.oext_term_s(family) == 1000.0                          # measured: x 1
        assert R.e_upper_s(family, "ref_train_bqi")["upper_s"] == pytest.approx(bqi - 1.5 * pass_s + 1000.0)
        assert R.cap_hours(R.arm_pod(family, [33, 33, 33, 38], oext=True)) < cap
        for bad in (0.0, -1.0, float("nan"), "1000"):
            monkeypatch.setitem(R.OEXT_TERM_MEASURED_S, family, bad)
            with pytest.raises(R.Refused):
                R.oext_term_s(family)
        monkeypatch.setitem(R.OEXT_TERM_MEASURED_S, family, None)
    assert R.OEXT_TERM_MEASURED_S == {"olmo2-7b": None, "llama31-8b": None}


def test_26b_the_runner_gate_keeps_the_oext_term():
    """job_decision (the pod's gate) and pod_dry_run take the job's own O-ext term and padded tokens: an O-ext arm's
    requirement on the pod is the planned requirement at s = 1, not the arm's without the term."""
    for family in R.FAMILIES:
        done, ver = preflight_pair(family)
        job = R.job_record(family, "arm", 33, "H1", 1102, R.FAMILIES[family]["A0_PADDED_TOKENS_PER_STEP"] * 1.1, oext=True)
        d = R.job_decision(family, done, ver, job, 10 ** 6, 100.0)
        assert d["requirement_s"] == pytest.approx(max(job["start_requirement_s"],
                                                       R.sanity_floor_s(family, R.preflight_fields(done, ver), 33)))
        assert d["requirement_s"] > R.requirement_s(family, 33) + R.oext_term_s(family)


def test_27_check_keys_takes_the_oext_bank_as_a_second_pin(monkeypatch):
    """SCOUT §1.3; Part 2 §4.3: a job with an O-ext step names its O-ext bank; check_keys holds it against OEXT_78B's
    inputs.oext_bank (null refuses), and a kind without an O-ext step names none."""
    family = "olmo2-7b"
    R.check_keys(**keys_of(family))                                     # no O-ext bank named: as before
    with pytest.raises(R.Refused, match="O-ext bank pin is null"):
        R.check_keys(**keys_of(family), oext_bank=hx("bank"))
    monkeypatch.setitem(R.OEXT_78B, family, oext_pin(family, "X", bank=hx("bank")))
    R.check_keys(**keys_of(family), oext_bank=hx("bank"))
    R.check_keys(**keys_of(family, kind="a0_arm"), oext_bank=hx("bank"))
    with pytest.raises(R.Refused, match="not olmo2-7b's pinned O-ext bank"):
        R.check_keys(**keys_of(family), oext_bank=hx("other"))
    with pytest.raises(R.Refused, match="names no O-ext bank"):
        R.check_keys(**keys_of(family, kind="evalonly"), oext_bank=hx("bank"))
    assert R.OEXT_BANK_KINDS == R.BANK500_KINDS | {"arm", "a0_arm"}


def test_28_the_w1_18_kind_one_pod_one_record_per_family(monkeypatch):
    """DES E2; DESO2 item 37; GXB O4: w1_18 is a single-job E kind (alone on its pod), X only, the scorer block's first
    O job (refused once a 500-bank job is planned), one pod with one check and one record per family; under [C]
    OLMo-2-7B's units only. Its E cap is 2.25 h ($10.16 guard), inside Part 2 §4.2's 2-3 h."""
    assert "w1_18" in R.E_KINDS and "w1_18" in R.SC_KINDS and "w1_18" in R.X_ONLY_KINDS
    assert R.SC_KIND_PINS["w1_18"] == ("W1_18_78B",) and R.W1_18_78B is None
    for family in R.FAMILIES:
        assert R.e_cap_hours(family, "w1_18") == 2.25 and R.e_pod(family, "w1_18")["guard_usd"] == 10.16
        with pytest.raises(R.Refused, match="runs alone"):
            R.cap_hours([R.job_record(family, "w1_18"), R.job_record(family, "arm", 33)])
        assert not R.engine_allowed("w1_18", "d3" * 32)
    b, c = R.w1_18_plan("B"), R.w1_18_plan("C")
    assert b["families"] == ("olmo2-7b", "llama31-8b") and c["families"] == ("olmo2-7b",)
    assert b["records"] == {"olmo2-7b": "overrefusal_checks__olmo2-7b.json", "llama31-8b": "overrefusal_checks__llama31-8b.json"}
    assert b["n_units"] == 7 and c["n_units"] == 4 and set(c["records"]) == {"olmo2-7b"}
    assert [u["unit"] for u in b["units"]["olmo2-7b"]] == ["untuned", 1101, 1102, 1103]
    assert [u["unit"] for u in b["units"]["llama31-8b"]] == ["untuned", 1101, 1102]
    assert all(u["complete_sha256"] == R.KIT[f]["a0_units"][u["unit"]]["complete_sha256"]
               for f in b["families"] for u in b["units"][f])
    with pytest.raises(R.Refused, match="not B or C"):
        R.w1_18_plan("A")
    assert R.w1_18_host_problem("olmo2-7b") is None and "olmo2-7b's scorer-block copy" in R.w1_18_host_problem("llama31-8b")
    assert R.w1_18_first_problem(["anchor", "untuned_answers"]) is None
    for kind in ("o_only", "o_only_with_regenerate", "c0"):
        assert "first O job" in R.w1_18_first_problem(["anchor", kind])
    assert R.sc_needed_pins("w1_18", "X") == ("W1_18_78B",)
    with pytest.raises(R.Refused, match="W1_18_78B waits for"):
        R.sc_pins_or_refuse("olmo2-7b", "w1_18", "X", pins78_doc())
    route = w1_18_route()                                # R2 K2 (GXB R-20, R-32): Track O's {files, side_units}
    monkeypatch.setattr(R, "W1_18_78B", route)
    assert R.sc_pins_or_refuse("olmo2-7b", "w1_18", "X", pins78_doc())["W1_18_78B"] == route
    monkeypatch.setattr(R, "W1_18_78B", {"files": {}, "side_units": route["side_units"]})
    with pytest.raises(R.Refused, match="not a .files"):
        R.sc_pin_values("olmo2-7b", pins78_doc())


def w1_18_route() -> dict:
    """R2 K2 (GXB R-20, R-32): a W1_18_78B pin in Track O's maker's form, both families, from KIT a0_units."""
    files = {R.W1_18_SCRIPT: hx("w")}
    units = {}
    for family in R.FAMILIES:
        files[f"scripts/scale78b/settings/OEXT-78B-W1__{family}.json"] = hx(f"w1-index-{family}")
        files[f"scripts/scale78b/settings/limits_overrefusal_checks__{family}.json"] = hx(f"w1-settings-{family}")
        units[family] = {("untuned" if k == "untuned" else f"a0-{k}"): {
            "path": u["path"][len("tmp/"):], "complete_sha256": u["complete_sha256"], "job_sha256": u["job_sha256"]}
            for k, u in R.KIT[family]["a0_units"].items()}
    return {"files": files, "side_units": units}


def pins78_doc() -> dict:
    """The scorer layer's committed pins_78b.json (its null pins as committed)."""
    return json.loads((ROOT / "scripts" / "scale78b" / "settings" / "pins_78b.json").read_text())


def branch_doc(family, branch="full", source="default", record=None) -> dict:
    return {"kind": R.BRANCH_RECORD_KIND, "version": 1, "family": family, "branch": branch, "source": source,
            "w1_18_record_sha256": record, "utc": "2026-11-12T10:00:00Z", "recorded_by": "GI XI"}


def test_29_the_branch_record_the_500_bank_kinds_and_the_flags(monkeypatch):
    """Part 2 §4.2; DES E2; DESO item 9; K1V-5: BRANCHES ("full", "128"), Branch full by default; each family's branch
    is read only from its pinned branch record (BRANCH_78B[family] = {path, sha256}, null until W1-18's record-done);
    every 500-bank job (o_only, o_only_with_regenerate, c0, the references, ref_train, and arm and a0_arm in blocks A
    and B, never block 0) refuses before the pin, and with bytes that are not the pinned record; 128 only from that
    family's W1-18 record; the branch never switches; under 128 every O-ext command takes --w1-18-record and the
    regenerated units --dev100-source."""
    assert R.BRANCHES == ("full", "128") and R.BRANCH_DEFAULT == "full"
    assert R.BRANCH_78B == {"olmo2-7b": None, "llama31-8b": None}
    assert R.BANK500_KINDS == frozenset({"o_only", "o_only_with_regenerate", "c0", "ref_eval", "safe_lora", "ref_train",
                                         "ref_train_bqi"})
    assert not R.bank500_job("arm", "0") and not R.bank500_job("a0_arm", "0") and not R.bank500_job("anchor", "sc")
    assert R.bank500_job("arm", "A") and R.bank500_job("a0_arm", "B") and R.bank500_job("o_only", "sc")
    f = "llama31-8b"
    full = json.dumps(branch_doc(f)).encode()
    for kind, block in (("o_only", "sc"), ("c0", "sc"), ("arm", "A"), ("ref_eval", "B")):
        assert "waits for llama31-8b's branch record (BRANCH_78B" in R.bank500_problem(f, kind, block, full)
    assert R.bank500_problem(f, "arm", "0", None) is None
    pin_of_item(monkeypatch, R.BRANCH_78B, f, full)
    for kind, block in (("o_only", "sc"), ("c0", "sc"), ("arm", "A"), ("ref_eval", "B")):
        assert R.bank500_problem(f, kind, block, full) is None
    assert "not the pinned one" in R.bank500_problem(f, "o_only", "sc", json.dumps(branch_doc(f, "128", "w1_18",
                                                                                              hx("w1"))).encode())
    assert "not the pinned one" in R.bank500_problem(f, "o_only", "sc", None)
    other = json.dumps(branch_doc("olmo2-7b")).encode()
    pin_of_item(monkeypatch, R.BRANCH_78B, f, other)
    assert "not the pinned one" in R.bank500_problem(f, "o_only", "sc", other)            # another family's record
    assert R.branch_record_problem(branch_doc(f, "128", "w1_18", hx("w1")), f) is None
    assert R.branch_record_problem(branch_doc(f, "full", "w1_18", hx("w1")), f) is None   # the bar failed: full
    assert "names its W1-18 record" in R.branch_record_problem(branch_doc(f, "128", "w1_18"), f)
    assert "default record is Branch full" in R.branch_record_problem(branch_doc(f, "128", "default"), f)
    assert "default record is Branch full" in R.branch_record_problem(branch_doc(f, "full", "default", hx("w1")), f)
    assert R.branch_record_problem({**branch_doc(f), "branch": "64"}, f)
    assert R.branch_record_problem({**branch_doc(f), "source": "lead"}, f)
    assert R.branch_record_problem({**branch_doc(f), "version": True}, f)
    # never switched: the pinned record is the old one
    monkeypatch.setitem(R.BRANCH_78B, f, None)
    assert R.branch_switch_problem(f, branch_doc(f)) is None                        # no record yet: the first one
    b128 = branch_doc(f, "128", "w1_18", hx("w1"))
    data128 = json.dumps(b128).encode()
    pin_of_item(monkeypatch, R.BRANCH_78B, f, data128)
    assert R.branch_switch_problem(f, b128, data128) is None
    for new in (branch_doc(f), branch_doc(f, "128", "w1_18", hx("w2")), {**b128, "source": "default"},
                {**b128, "family": "olmo2-7b"}):
        assert "never switched" in R.branch_switch_problem(f, new, data128), new
    with pytest.raises(R.Refused, match="do not hash"):
        R.branch_switch_problem(f, b128, full)
    # the flags, from the pinned record only
    assert R.oext_flags(f, "c0", data128)["w1_18_record"] == hx("w1")
    for kind in ("c0", "o_only", "o_only_with_regenerate", "arm", "a0_arm"):
        assert R.oext_flags(f, kind, data128)["w1_18_record"] == hx("w1")
    assert R.oext_flags(f, "o_only_with_regenerate", data128, regenerated=True)["dev100_source"] is True
    assert R.oext_flags(f, "o_only", data128)["dev100_source"] is False              # theta0 is never regenerated
    with pytest.raises(R.Refused, match="no O-ext step"):
        R.oext_flags(f, "anchor", data128)
    with pytest.raises(R.Refused, match="do not hash"):
        R.oext_flags(f, "o_only", full)
    pin_of_item(monkeypatch, R.BRANCH_78B, f, full)
    assert R.oext_flags(f, "o_only_with_regenerate", full, regenerated=True) == {"w1_18_record": None,
                                                                                   "dev100_source": False}
    monkeypatch.setitem(R.BRANCH_78B, f, None)
    with pytest.raises(R.Refused, match="BRANCH_78B\\['llama31-8b'\\] is null"):
        R.oext_flags(f, "o_only", full)


def test_29b_every_oext_kind_refuses_its_job_while_oext_78b_or_the_branch_record_is_null(monkeypatch):
    """GXB R-4 (K1V-10): until K3 wires `oext_78b.py <command> --family F`, no test asserts an O-ext command line;
    instead every scorer-block O-ext kind (c0, o_only, o_only_with_regenerate) refuses to build its job while
    OEXT_78B or the family's branch record (BRANCH_78B) is null, and w1_18 while its own route pin W1_18_78B is null
    (I: T-O2 fills OEXT_78B and the branch only after the W1-18 pod, so W1-18 cannot wait on them)."""
    f = "olmo2-7b"
    oext = oext_pin(f)
    monkeypatch.setitem(R.C0_SOURCE, f, {"complete_sha256": hx("c"), "e1_fingerprint": hx("e")})
    units = {"o_only": (None, None), "c0": ("R", 1101), "o_only_with_regenerate": ("a0", 1102)}
    for o, b in ((None, None), (oext, None), (None, {"path": "records/branch.json", "sha256": hx("br")})):
        monkeypatch.setitem(R.OEXT_78B, f, o)
        monkeypatch.setitem(R.BRANCH_78B, f, b)
        for kind, (arm, seed) in units.items():
            want = ([] if o else ["OEXT_78B"]) + ([] if b else ["BRANCH_78B"])
            with pytest.raises(R.Refused, match=" ".join(f"{p} waits for" for p in want[:1])):
                R.sc_pins_or_refuse(f, kind, "X", pins78_doc(), arm, seed)
            missing = [p for p, _ in R.sc_missing_pins(f, kind, "X", pins78_doc(), arm, seed)]
            assert set(want) <= set(missing), (kind, missing)
    monkeypatch.setitem(R.OEXT_78B, f, oext)
    monkeypatch.setitem(R.BRANCH_78B, f, {"path": "records/branch.json", "sha256": hx("br")})
    for kind, (arm, seed) in units.items():
        R.sc_pins_or_refuse(f, kind, "X", pins78_doc(), arm, seed)
    with pytest.raises(R.Refused, match="W1_18_78B waits for"):
        R.sc_pins_or_refuse(f, "w1_18", "X", pins78_doc())
    monkeypatch.setitem(R.BRANCH_78B, f, {"path": "/abs.json", "sha256": hx("br")})
    with pytest.raises(R.Refused, match="BRANCH_78B\\['olmo2-7b'\\] is not a .path, sha256. pin"):
        R.sc_pin_values(f, pins78_doc())


def n_units_doc(family: str) -> dict:
    out = {}
    for arm, seed in R.block0_runs(family):
        u = {"path": f"tmp/family-probe-s78-{family}-0/retrieved/{family}-0-1/tree/round1/{seed}-{arm}-e1-a1",
             "complete_sha256": hx(f"n-{family}-{arm}-{seed}"), "job_sha256": hx(f"job-{family}-{arm}-{seed}")}
        if arm == "R":
            u["edit_sha256"] = hx(f"edit-{family}-{seed}")
        out[R.unit_key(arm, seed)] = u
    return out


def test_30_the_seed_key_olmo_n_r1101_and_side_a0_1101(tmp_path, monkeypatch):
    """GXB's seed key: o_only_with_regenerate and every unit input are keyed by (arm, seed), not seed alone. On
    OLMo-2-7B N's R_1101 and the side unit a0-1101 share seed 1101: two units, two keys, two input sets, two pins."""
    units = R.sc_units("olmo2-7b", "o_only_with_regenerate")
    assert [(u["arm"], u["seed"], u["source"]) for u in units] == [
        ("a0", 1101, "side"), ("a0", 1102, "side"), ("a0", 1103, "side"), ("R", 1101, "n"), ("R", 1102, "n"),
        ("R", 1103, "n")]
    assert [(u["arm"], u["seed"], u["source"]) for u in R.sc_units("llama31-8b", "o_only_with_regenerate")] == [
        ("a0", 1101, "side"), ("a0", 1102, "side"), ("R", 1101, "n"), ("R", 1102, "n"), ("R", 1103, "n"),
        ("a0", 1103, "n")]                                            # 6 + 6 = 12; with theta0's 2 o_only: 14 pods
    assert R.sc_unit_source("olmo2-7b", "o_only_with_regenerate", "R", 1101) == "n"
    assert R.sc_unit_source("olmo2-7b", "o_only_with_regenerate", "a0", 1101) == "side"
    assert R.sc_unit_source("llama31-8b", "o_only_with_regenerate", "a0", 1103) == "n"
    for bad in (("R", 1104), ("a0", 1104), ("H1", 1101), ("R", None)):
        with pytest.raises(R.Refused, match="not one of its units"):
            R.sc_unit_source("olmo2-7b", "o_only_with_regenerate", *bad)
    assert R.SC_ARMS == {"o_only_with_regenerate": ("a0", "R")} and R.SC_ARM["o_only_with_regenerate"] == "a0"
    assert R.sc_needed_pins("o_only_with_regenerate", "X", "olmo2-7b", "R", 1101) == ("OEXT_78B", "BRANCH_78B",
                                                                                        "N_UNITS")
    assert R.sc_needed_pins("o_only_with_regenerate", "X", "olmo2-7b", "a0", 1101) == ("OEXT_78B", "BRANCH_78B")
    for arm, seed in (("R", 1102), ("R", 1103), ("a0", 1103)):                    # K1V-7: Llama's N a0-1103 too
        assert "N_UNITS" in R.sc_needed_pins("o_only_with_regenerate", "X", "llama31-8b", arm, seed), (arm, seed)
    for seed in (1101, 1102):
        assert "N_UNITS" not in R.sc_needed_pins("o_only_with_regenerate", "X", "llama31-8b", "a0", seed)
    sr = kit_copy(tmp_path, "olmo2-7b", "sc")
    side, n = sr.sc_input_names("o_only_with_regenerate", 1101, "a0"), sr.sc_input_names("o_only_with_regenerate", 1101, "R")
    assert side == ("side_complete:a0:1101", "oext_bank", "oext_record") == sr.sc_input_names("o_only_with_regenerate", 1101)
    assert n == ("n_complete:R:1101", "regen_edit:R:1101", "oext_bank", "oext_record")
    values = R.sc_pin_values("olmo2-7b", pins78_doc())
    assert sr.sc_input_pins("o_only_with_regenerate", pins78_doc(), values, 1101, "R") == {
        "n_complete:R:1101": None, "regen_edit:R:1101": None, "oext_bank": None, "oext_record": None}
    assert sr.sc_input_pins("o_only_with_regenerate", pins78_doc(), values, 1101, "a0")["side_complete:a0:1101"] == \
        R.KIT["olmo2-7b"]["a0_units"][1101]["complete_sha256"]
    monkeypatch.setitem(R.N_UNITS, "olmo2-7b", n_units_doc("olmo2-7b"))
    values = R.sc_pin_values("olmo2-7b", pins78_doc())
    pins_n = sr.sc_input_pins("o_only_with_regenerate", pins78_doc(), values, 1101, "R")
    pins_side = sr.sc_input_pins("o_only_with_regenerate", pins78_doc(), values, 1101, "a0")
    assert pins_n["n_complete:R:1101"] == hx("n-olmo2-7b-R-1101") and pins_n["regen_edit:R:1101"] == hx("edit-olmo2-7b-1101")
    assert pins_side["side_complete:a0:1101"] != pins_n["n_complete:R:1101"]
    assert set(pins_n) & set(pins_side) == {"oext_bank", "oext_record"}
    llama = kit_copy(tmp_path / "l", "llama31-8b", "sc")
    assert llama.sc_input_names("o_only_with_regenerate", 1103, "a0") == ("n_complete:a0:1103", "oext_bank", "oext_record")


def test_31_n_units_are_null_pins_that_refuse_until_block_0s_record_done(monkeypatch):
    """DES E5; Part 2 §4.5: N_UNITS[family] is null until block 0's record-done and a recorded lead step; N's
    regenerations refuse until then (sc_pins_or_refuse names N_UNITS and its event); a filled pin holds exactly N's
    units under block 0's working copy."""
    assert R.N_UNITS == {"olmo2-7b": None, "llama31-8b": None}
    monkeypatch.setitem(R.OEXT_78B, "olmo2-7b", oext_pin("olmo2-7b"))
    monkeypatch.setitem(R.BRANCH_78B, "olmo2-7b", {"path": "records/branch.json", "sha256": hx("br")})
    with pytest.raises(R.Refused, match="N_UNITS waits for block 0 \\(N\\)"):
        R.sc_pins_or_refuse("olmo2-7b", "o_only_with_regenerate", "X", pins78_doc(), "R", 1102)
    R.sc_pins_or_refuse("olmo2-7b", "o_only_with_regenerate", "X", pins78_doc(), "a0", 1102)   # the side unit runs
    with pytest.raises(R.Refused, match="is null"):
        R.n_unit_or_refuse("olmo2-7b", "R", 1101)
    with pytest.raises(R.Refused, match="not one of olmo2-7b's N units"):
        R.n_unit_or_refuse("olmo2-7b", "a0", 1103)
    doc = n_units_doc("olmo2-7b")
    assert R.n_units_problem(doc, "olmo2-7b") is None
    monkeypatch.setitem(R.N_UNITS, "olmo2-7b", doc)
    assert R.n_unit_or_refuse("olmo2-7b", "R", 1101)["complete_sha256"] == hx("n-olmo2-7b-R-1101")
    R.sc_pins_or_refuse("olmo2-7b", "o_only_with_regenerate", "X", pins78_doc(), "R", 1102)
    bad = {k: dict(v) for k, v in doc.items()}
    bad["R-1101"]["path"] = "tmp/family-probe-s78-olmo2-7b-sc/x"
    assert "is not under" in R.n_units_problem(bad, "olmo2-7b")
    assert "keys are not N's units" in R.n_units_problem({k: v for k, v in doc.items() if k != "R-1103"}, "olmo2-7b")
    assert "must hold exactly" in R.n_units_problem({**doc, "R-1101": {k: v for k, v in doc["R-1101"].items()
                                                                       if k != "edit_sha256"}}, "olmo2-7b")
    assert "keys are not N's units" in R.n_units_problem(n_units_doc("llama31-8b"), "olmo2-7b")
    monkeypatch.setitem(R.N_UNITS, "olmo2-7b", bad)
    with pytest.raises(R.Refused, match="not N's unit record"):
        R.sc_pin_values("olmo2-7b", pins78_doc())


def test_32_rejudged_a_seven_per_family_with_ns_entries_null(tmp_path, monkeypatch):
    """Part 2 §6; DESO item 26: block A re-judges N's units, the reused a0 units and theta0: OLMo 3 + 3 + 1, Llama
    4 + 2 + 1; N's entries are null until N runs (a judge launch refuses through rejudged_or_refuse); the side units
    and theta0 carry their COMPLETE.json and job.json pins (M); block B and block 0 have none."""
    for family, (n, side) in (("olmo2-7b", (3, 3)), ("llama31-8b", (4, 2))):
        pins = R.rejudged_pins(family, "A")
        assert len(pins) == 7 == n + side + 1
        assert [p["complete_sha256"] is None for p in pins] == [True] * n + [False] * (side + 1)
        assert all(p["path"] is None and p["arm"] is None and p["job_sha256"] is None for p in pins[:n])
        assert [(p["seed"], p["target"]) for p in pins[:n]] == [(s, "e1") for _, s in R.block0_runs(family)]
        assert pins[-1]["name"] == "theta0 (untuned)" and pins[-1]["target"] == "init"
        for p in pins[n:]:
            assert set(p) == {"name", "arm", "seed", "target", "path", "complete_sha256", "job_sha256"}
            assert len(p["job_sha256"]) == 64 and p["path"].startswith("tmp/family-probe-sp-")
        with pytest.raises(R.Refused, match="wait for block 0 \\(N\\)"):
            R.rejudged_or_refuse(family, "A")
        assert R.rejudged_pins(family, "B") == () == R.rejudged_pins(family, "0")
        monkeypatch.setitem(R.N_UNITS, family, n_units_doc(family))
        filled = R.rejudged_or_refuse(family, "A")
        assert filled[0]["arm"] == f"edit-{hx(f'edit-{family}-1101')}" and filled[0]["path"].startswith(
            f"tmp/family-probe-s78-{family}-0/")
        assert len({p["complete_sha256"] for p in filled}) == 7
        sr = kit_copy(tmp_path / family, family, "A")
        assert sr.REJUDGED_PINS["A"] == filled and sr.REJUDGED_PINS["B"] == () == sr.REJUDGED_PINS["0"]
        monkeypatch.setitem(R.N_UNITS, family, None)
    for family in R.FAMILIES:                                   # the job.json pins re-measured (no answer file opened)
        for key, unit in R.KIT[family]["a0_units"].items():
            folder = MEASURED_ROOT.parent / unit["path"]
            if not (folder / "job.json").is_file():
                continue
            assert hashlib.sha256((folder / "job.json").read_bytes()).hexdigest() == unit["job_sha256"], (family, key)
            assert hashlib.sha256((folder / "COMPLETE.json").read_bytes()).hexdigest() == unit["complete_sha256"]


def gate_doc(**changes) -> dict:
    doc = {"kind": R.GATE_RECORD_KIND, "version": 1, "option": "B", "families": ["olmo2-7b", "llama31-8b"],
           "provisional_plan": "A", "sigma_F_plan": None, "noise_reading_sha256": hx("noise"), "balance_usd": 300.0,
           "utc": "2026-11-20T10:00:00Z", "recorded_by": "GI XI"}
    doc.update(changes)
    return doc


def plan_b_doc(**changes) -> dict:
    doc = {"kind": R.PLAN_B_RECORD_KIND, "version": 1, "plan": "H", "sr2_adopted": True, "sr2_reason": None,
           "plan_basis": "sigma_A", "sigma_A_pp": 7.25, "blinded_sigma_output_sha256": hx("bs-out"), "blinded_sigma_inputs_sha256": hx("bs-in"),
           "utc": "2026-12-01T10:00:00Z", "recorded_by": "GI XI"}
    doc.update(changes)
    return doc


def pin_of(monkeypatch, name: str, data: bytes) -> None:
    monkeypatch.setattr(R, name, {"path": f"records/{name.lower()}.json", "sha256": hashlib.sha256(data).hexdigest()})


def pin_of_item(monkeypatch, table: dict, family: str, data: bytes) -> None:
    """A per-family {path, sha256} pin of ``data`` (test-local)."""
    monkeypatch.setitem(table, family, {"path": f"records/{family}-record.json",
                                        "sha256": hashlib.sha256(data).hexdigest()})


def test_33_o14_gate_78b_is_null_and_block_a_reads_its_families_only(monkeypatch):
    """GXB O14 (corrected, second set): GATE_78B (the gate record's path and SHA-256; option, families, N's
    provisional plan, the noise reading's output hash, the balance) is null until the gate; block A's init reads its
    families only (block A is the same in every plan) and refuses before the fill; under [C] Llama runs no block."""
    assert R.GATE_78B is None and R.GATE_KEYS == ("kind", "version", "option", "families", "provisional_plan",
                                                  "sigma_F_plan", "noise_reading_sha256", "balance_usd", "utc",
                                                  "recorded_by")
    data = json.dumps(gate_doc()).encode()
    with pytest.raises(R.Refused, match="GATE_78B is null: it waits for ruling 9's gate"):
        R.block_init_or_refuse("A", "olmo2-7b", data)
    pin_of(monkeypatch, "GATE_78B", data)
    a = R.block_init_or_refuse("A", "llama31-8b", data)
    assert a["families"] == ("olmo2-7b", "llama31-8b") and a["plan"] is None and a["option"] == "B"
    with pytest.raises(R.Refused, match="reads nothing"):
        R.block_init_or_refuse("sc", "olmo2-7b", data)
    c = json.dumps(gate_doc(option="C", families=["olmo2-7b"], provisional_plan="H", sigma_F_plan="B9")).encode()
    pin_of(monkeypatch, "GATE_78B", c)
    assert R.block_init_or_refuse("A", "olmo2-7b", c)["families"] == ("olmo2-7b",)
    with pytest.raises(R.Refused, match="llama31-8b runs no block A"):
        R.block_init_or_refuse("A", "llama31-8b", c)
    with pytest.raises(R.Refused, match="do not hash"):
        R.block_init_or_refuse("A", "olmo2-7b", data)
    for change, match in (({"option": "C"}, "option C runs"), ({"families": ["llama31-8b"], "option": "C"}, "runs"),
                          ({"provisional_plan": "B10"}, "provisional plan"), ({"noise_reading_sha256": None}, "noise"),
                          ({"balance_usd": -1}, "negative"), ({"balance_usd": "300"}, "finite"),
                          ({"kind": "gate"}, "kind"), ({"utc": ""}, "utc"), ({"extra": 1}, "exactly"),
                          ({"plan": "A"}, "exactly")):
        assert match in (R.gate_record_problem(gate_doc(**change)) or ""), change
    assert R.gate_record_problem(gate_doc(provisional_plan="review")) is None
    bad = json.dumps(gate_doc(provisional_plan="B10")).encode()
    pin_of(monkeypatch, "GATE_78B", bad)
    with pytest.raises(R.Refused, match="is not 'stage1-78b gate record'"):
        R.block_init_or_refuse("A", "olmo2-7b", bad)
    monkeypatch.setattr(R, "GATE_78B", {"path": "/abs/gate.json", "sha256": hashlib.sha256(bad).hexdigest()})
    with pytest.raises(R.Refused, match="not a .path, sha256. pin"):
        R.block_init_or_refuse("A", "olmo2-7b", bad)


def test_33b_o14_plan_b_78b_gives_block_bs_plan_and_review_plans_nothing(monkeypatch):
    """GXB O14 (corrected): PLAN_B_78B (block B's plan record: blinded_sigma.py's output and inputs-file SHA-256s,
    whether SR-2 is adopted, the plan A, B9, H (b) or review) is null until block A's record-done and blinded_sigma.py;
    block B's init reads its plan from it (never the gate's provisional plan), refuses before the fill, and a
    "review" plan plans nothing; block B still needs the gate's families."""
    assert R.PLAN_B_78B is None and R.PLAN_B_CODES == ("A", "B9", "H", "review")
    gate = json.dumps(gate_doc(provisional_plan="A")).encode()
    plan_b = json.dumps(plan_b_doc(plan="H")).encode()
    with pytest.raises(R.Refused, match="GATE_78B is null"):
        R.block_init_or_refuse("B", "olmo2-7b", gate, plan_b)
    pin_of(monkeypatch, "GATE_78B", gate)
    with pytest.raises(R.Refused, match="PLAN_B_78B is null: it waits for block A's record-done and blinded_sigma"):
        R.block_init_or_refuse("B", "olmo2-7b", gate, plan_b)
    pin_of(monkeypatch, "PLAN_B_78B", plan_b)
    got = R.block_init_or_refuse("B", "llama31-8b", gate, plan_b)
    assert got["plan"] == "H" and got["sr2_adopted"] is True                     # N's provisional "A" is not read
    with pytest.raises(R.Refused, match="do not hash to PLAN_B_78B"):
        R.block_init_or_refuse("B", "olmo2-7b", gate, json.dumps(plan_b_doc(plan="A")).encode())
    with pytest.raises(R.Refused, match="do not hash to PLAN_B_78B"):
        R.block_init_or_refuse("B", "olmo2-7b", gate, None)
    no = dict(sr2_adopted=False, sr2_reason="simulation_reading", plan_basis="sigma_pool_N", sigma_A_pp=None,
              blinded_sigma_output_sha256=None, blinded_sigma_inputs_sha256=None)
    review_gate = json.dumps(gate_doc(provisional_plan="review")).encode()
    review = json.dumps(plan_b_doc(**no, plan="review")).encode()
    pin_of(monkeypatch, "GATE_78B", review_gate)
    pin_of(monkeypatch, "PLAN_B_78B", review)
    with pytest.raises(R.Refused, match="plans nothing"):
        R.block_init_or_refuse("B", "olmo2-7b", review_gate, review)
    pin_of(monkeypatch, "GATE_78B", gate)
    no_sr2 = json.dumps(plan_b_doc(**no, plan="A")).encode()
    pin_of(monkeypatch, "PLAN_B_78B", no_sr2)
    assert R.block_init_or_refuse("B", "olmo2-7b", gate, no_sr2) == {
        "block": "B", "family": "olmo2-7b", "option": "B", "families": ("olmo2-7b", "llama31-8b"), "plan": "A",
        "sr2_adopted": False, "plan_basis": "sigma_pool_N"}
    c_gate = json.dumps(gate_doc(option="C", families=["olmo2-7b"], sigma_F_plan="A")).encode()
    pin_of(monkeypatch, "GATE_78B", c_gate)
    with pytest.raises(R.Refused, match="llama31-8b runs no block B"):
        R.block_init_or_refuse("B", "llama31-8b", c_gate, no_sr2)
    for change, match in (({"plan": "B10"}, "plan"), ({"sr2_adopted": 1}, "true or false"),
                          ({"blinded_sigma_output_sha256": None}, "must be a SHA-256"),
                          ({"blinded_sigma_inputs_sha256": None}, "must be a SHA-256"),
                          ({"sr2_reason": "simulation_reading"}, "sr2_reason is null"),
                          ({"plan_basis": "sigma_pool_N"}, "plan_basis is sigma_A"),
                          ({"kind": "plan"}, "kind"), ({"recorded_by": " "}, "recorded_by"), ({"extra": 1}, "exactly")):
        assert match in (R.plan_b_record_problem(plan_b_doc(**change)) or ""), change
    assert R.plan_b_record_problem(plan_b_doc()) is None


def test_33c_k6_plan_b_without_sr2_names_its_reason_and_basis_and_carries_no_blinded_sigma_hash(monkeypatch):
    """GXB K-6 (K1V-3): without SR-2, PLAN_B_78B's record names the reason (the blinding test not verified, or the
    simulation's reading) and the plan's basis: N's sigma_pool under [B], the chosen family's sigma_F under [C]; both
    blinded_sigma.py hashes are null (refused if given). With SR-2: no reason, basis sigma_A, both hashes required."""
    assert R.SR2_REASONS == ("blinding_test_not_verified", "simulation_reading")
    assert R.PLAN_BASES == {"adopted": "sigma_A", "B": "sigma_pool_N", "C": "sigma_F"}
    no = dict(sr2_adopted=False, sigma_A_pp=None, blinded_sigma_output_sha256=None, blinded_sigma_inputs_sha256=None)
    for reason in R.SR2_REASONS:
        for basis, option in (("sigma_pool_N", "B"), ("sigma_F", "C")):
            doc = plan_b_doc(**no, sr2_reason=reason, plan_basis=basis)
            assert R.plan_b_record_problem(doc) is None and R.plan_b_record_problem(doc, option) is None
            other = "C" if option == "B" else "B"
            assert "basis without SR-2" in R.plan_b_record_problem(doc, other)
    for change, match in (({"sr2_reason": None}, "sr2_reason is one of"), ({"sr2_reason": "lead"}, "sr2_reason is one of"),
                          ({"plan_basis": "sigma_A"}, "sigma_pool_N ([B]) or sigma_F ([C])"),
                          ({"blinded_sigma_output_sha256": hx("o")}, "must be null"),
                          ({"blinded_sigma_inputs_sha256": hx("i")}, "must be null")):
        doc = plan_b_doc(**{**no, "sr2_reason": "simulation_reading", "plan_basis": "sigma_pool_N", **change})
        assert match in (R.plan_b_record_problem(doc) or ""), change
    assert R.plan_b_record_problem(plan_b_doc()) is None
    gate_c = json.dumps(gate_doc(option="C", families=["olmo2-7b"], sigma_F_plan="B9")).encode()
    pin_of(monkeypatch, "GATE_78B", gate_c)
    bad = json.dumps(plan_b_doc(**no, sr2_reason="blinding_test_not_verified", plan_basis="sigma_pool_N")).encode()
    pin_of(monkeypatch, "PLAN_B_78B", bad)
    with pytest.raises(R.Refused, match="under option C the plan's basis without SR-2 is sigma_F"):
        R.block_init_or_refuse("B", "olmo2-7b", gate_c, bad)
    good = json.dumps(plan_b_doc(**no, sr2_reason="blinding_test_not_verified", plan_basis="sigma_F", plan="B9")).encode()
    pin_of(monkeypatch, "PLAN_B_78B", good)
    got = R.block_init_or_refuse("B", "olmo2-7b", gate_c, good)
    assert (got["plan"], got["sr2_adopted"], got["plan_basis"]) == ("B9", False, "sigma_F")


def test_33d_r1_block_a_refuses_under_a_review_provisional_plan(monkeypatch):
    """GXB R-1 (P1 §6.1): under a "review" provisional plan there is no 7-8B primary family and the user decides the
    next step, so block A's init refuses; nothing starts by default. Other provisional plans let block A plan."""
    review = json.dumps(gate_doc(provisional_plan="review")).encode()
    pin_of(monkeypatch, "GATE_78B", review)
    for family in R.FAMILIES:
        with pytest.raises(R.Refused, match="provisional plan is 'review'.*the user decides"):
            R.block_init_or_refuse("A", family, review)
    for plan in R.PLAN_CODES:
        data = json.dumps(gate_doc(provisional_plan=plan)).encode()
        pin_of(monkeypatch, "GATE_78B", data)
        assert R.block_init_or_refuse("A", "olmo2-7b", data)["families"] == ("olmo2-7b", "llama31-8b")


HARMFUL = "harmful prompt 7 (8 of 64) does not encode (encode_train: too long); the list needs a reviewed new version"
# The fourth set's record form as Track S's reader takes it, copied by hand (R: B/ws-s/scripts/scale78b/blinded_sigma.py
# :69-70 STOP_KINDS, STOP_RECORD_KIND; :218-235 check_anchor_stop reads kind, family, stop_kind and exit_code; its
# test fixture adds version, job_done_sha256 and counts, test_blinded_sigma.py:191-192).
TRACK_S_STOP_FORM = {"kind": "scale-78b anchor stop",
                     "stop_kinds": {"safe_anchors_below_64": 3, "harmful_prompt_does_not_encode": 1},
                     "read_keys": ("kind", "family", "stop_kind", "exit_code"),
                     "fixture_keys": ("kind", "version", "family", "stop_kind", "exit_code", "job_done_sha256", "counts")}


def track_s_accepts(doc: dict, family: str) -> bool:
    """Track S's check_anchor_stop on a parsed record, restated from its literal form above."""
    kinds = TRACK_S_STOP_FORM["stop_kinds"]
    return (isinstance(doc, dict) and doc.get("kind") == TRACK_S_STOP_FORM["kind"] and doc.get("family") == family
            and doc.get("stop_kind") in kinds and type(doc.get("exit_code")) is int
            and doc["exit_code"] == kinds[doc["stop_kind"]])


def stop_family(monkeypatch, family: str, stop: str = "few") -> bytes:
    """Pin a family's stop record and read it through anchor_stop_or_refuse (K1V-6), test-locally."""
    done = hx(f"job-done-{family}")
    doc = (R.anchor_stop_record(family, 3, None, done, {"kept": 60, "needed": 64}) if stop == "few"
           else R.anchor_stop_record(family, 1, HARMFUL, done))
    data = json.dumps(doc).encode()
    monkeypatch.setattr(R, "_ANCHOR_STOPS_READ", {})
    pin_of_item(monkeypatch, R.ANCHOR_STOP, family, data)
    R.anchor_stop_or_refuse(family, data, done)
    return data


def test_34_o6_a_stop_only_from_the_anchor_scripts_own_signal():
    """GXB O6, item 14, fourth set: a stop is recorded only from exit 3 (fewer than 64 safe anchors) or exit 1 with the
    AnchorJobError message "harmful prompt ... does not encode" (R: scripts/make_anchor_answers.py:121); any other exit
    or message is a crash. The record is text-free, in the fourth set's form: kind "scale-78b anchor stop", family,
    stop_kind safe_anchors_below_64 or harmful_prompt_does_not_encode, exit code, JOB-DONE.json SHA-256 and the stop
    line's ids and counts; it must name the anchor job's JOB-DONE.json."""
    source = (ROOT / "scripts" / "make_anchor_answers.py").read_text()
    assert "EXIT_FEW = 3" in source and "class AnchorJobError(SystemExit)" in source
    assert 'raise AnchorJobError(f"harmful prompt {k} ({k + 1} of {n_harmful}) does not encode ({failure}); "' in source
    assert '"the list needs a reviewed new version")' in source
    assert R.anchor_exit_kind(0) == "complete" and R.anchor_exit_kind(3) == "safe_anchors_below_64"
    assert R.anchor_exit_kind(1, HARMFUL) == "harmful_prompt_does_not_encode"
    assert R.anchor_exit_kind(1, HARMFUL + "\n") == "harmful_prompt_does_not_encode"
    for code, message in ((1, None), (1, "the prompt list's SHA-256 is not the pinned value"),
                          (1, "prompt 3 (4 of 128) does not encode as a generation prompt (ValueError); the list needs "
                              "a reviewed new version"), (2, HARMFUL), (137, None), (-9, None), (None, None),
                          (True, HARMFUL), (1, "x" + HARMFUL), (4, None)):
        assert R.anchor_exit_kind(code, message) == "crash", (code, message)
    done = hx("job-done")
    few = R.anchor_stop_record("olmo2-7b", 3, None, done, {"kept": 61, "needed": 64, "drops": {"capped": 3}})
    assert few == {"kind": "scale-78b anchor stop", "version": 1, "family": "olmo2-7b",
                   "stop_kind": "safe_anchors_below_64", "exit_code": 3, "job_done_sha256": done,
                   "counts": {"kept": 61, "needed": 64}}
    pair = R.anchor_stop_record("llama31-8b", 1, HARMFUL, done)
    assert pair["stop_kind"] == "harmful_prompt_does_not_encode" and pair["exit_code"] == 1
    assert pair["counts"] == {"prompt_index": 7, "position": 8, "of": 64}
    assert "encode_train" not in json.dumps(pair) and "too long" not in json.dumps(pair)     # text-free
    for args in ((0, None, done, None), (1, "boom", done, None), (2, HARMFUL, done, None)):
        with pytest.raises(R.Refused, match="crash rule applies"):
            R.anchor_stop_record("olmo2-7b", *args)
    for counts in (None, {"kept": 64, "needed": 64}, {"kept": 10, "needed": 32}, {"kept": "10", "needed": 64}):
        with pytest.raises(R.Refused, match="counts line"):
            R.anchor_stop_record("olmo2-7b", 3, None, done, counts)
    with pytest.raises(R.Refused, match="JOB-DONE"):
        R.anchor_stop_record("olmo2-7b", 3, None, "x", {"kept": 1, "needed": 64})
    with pytest.raises(R.Refused, match="ids do not fit"):
        R.anchor_stop_record("olmo2-7b", 1, HARMFUL.replace("(8 of 64)", "(9 of 64)"), done)
    assert R.anchor_stop_problem(few, "olmo2-7b", done) is None and R.anchor_stop_problem(pair, "llama31-8b") is None
    assert "names JOB-DONE.json" in R.anchor_stop_problem(few, "olmo2-7b", hx("other job"))
    assert R.anchor_stop_problem(few, "llama31-8b")
    for bad in ({**few, "exit_code": 1}, {**few, "exit_code": True}, {**pair, "exit_code": True},
                {**few, "version": True}, {**few, "kind": "stage1-78b anchor stop"},
                {**few, "stop_kind": "few_safe"}, {**few, "counts": {"kept": 64, "needed": 64}}):
        assert R.anchor_stop_problem(bad, bad["family"]), bad
    assert R.anchor_stop_problem({**pair, "counts": {"prompt_index": 7, "position": 7, "of": 64}}, "llama31-8b")
    assert R.ANCHOR_STOP == {"olmo2-7b": None, "llama31-8b": None}


def test_34b_the_stop_record_form_is_the_one_track_s_reads():
    """GXB fourth set: one record form, written by K2's writer on K1's anchor_stop_record and read by Track S's
    blinded_sigma.py. K1's kind, field names and stop values equal Track S's literal (TRACK_S_STOP_FORM, copied from
    blinded_sigma.py:69-70), its field set equals Track S's fixture's, and Track S's check accepts both K1 records
    (and refuses K1's records of round 1's old form)."""
    assert R.ANCHOR_STOP_KIND == TRACK_S_STOP_FORM["kind"]
    assert R.ANCHOR_STOPS == TRACK_S_STOP_FORM["stop_kinds"]
    assert R.ANCHOR_STOP_KEYS == TRACK_S_STOP_FORM["fixture_keys"]
    assert set(TRACK_S_STOP_FORM["read_keys"]) <= set(R.ANCHOR_STOP_KEYS)
    done = hx("job-done")
    for family, rec in (("olmo2-7b", R.anchor_stop_record("olmo2-7b", 3, None, done, {"kept": 1, "needed": 64})),
                        ("llama31-8b", R.anchor_stop_record("llama31-8b", 1, HARMFUL, done))):
        assert track_s_accepts(json.loads(json.dumps(rec)), family) and R.anchor_stop_problem(rec, family) is None
    old = {"kind": "stage1-78b anchor stop", "version": 1, "family": "olmo2-7b", "stop": "few_safe", "exit_code": 3,
           "job_done_sha256": done, "line": {"kept": 1, "needed": 64}}
    assert not track_s_accepts(old, "olmo2-7b") and R.anchor_stop_problem(old, "olmo2-7b")


def test_34c_k1v6_a_family_is_stopped_only_after_its_pinned_record_is_read(monkeypatch):
    """K1V-6: a pinned ANCHOR_STOP marks the family stopped only after anchor_stop_or_refuse read the record at the
    pin and checked its kind, family, stop_kind, exit code (and JOB-DONE.json); before that, and for bytes that do not
    hash to the pin or a record of another family, it refuses (never the normal route by default)."""
    f = "olmo2-7b"
    done = hx("job-done")
    rec = R.anchor_stop_record(f, 3, None, done, {"kept": 2, "needed": 64})
    data = json.dumps(rec).encode()
    monkeypatch.setattr(R, "_ANCHOR_STOPS_READ", {})
    assert not R.family_stopped(f)
    with pytest.raises(R.Refused, match="ANCHOR_STOP\\['olmo2-7b'\\] is null"):
        R.anchor_stop_or_refuse(f, data, done)
    pin_of_item(monkeypatch, R.ANCHOR_STOP, f, data)
    with pytest.raises(R.Refused, match="has not been read at the pin"):
        R.family_stopped(f)
    with pytest.raises(R.Refused, match="has not been read"):
        R.block_runs_78b(f, None, "A")
    with pytest.raises(R.Refused, match="do not hash"):
        R.anchor_stop_or_refuse(f, data + b" ", done)
    with pytest.raises(R.Refused, match="names JOB-DONE.json"):
        R.anchor_stop_or_refuse(f, data, hx("other"))
    with pytest.raises(R.Refused, match="has not been read"):
        R.family_stopped(f)
    other = json.dumps(R.anchor_stop_record("llama31-8b", 3, None, done, {"kept": 2, "needed": 64})).encode()
    pin_of_item(monkeypatch, R.ANCHOR_STOP, f, other)
    with pytest.raises(R.Refused, match="is not 'scale-78b anchor stop'"):
        R.anchor_stop_or_refuse(f, other, done)
    pin_of_item(monkeypatch, R.ANCHOR_STOP, f, data)
    assert R.anchor_stop_or_refuse(f, data, done) == rec and R.family_stopped(f)
    assert len(R.block_runs_78b(f, None, "A")) == 12
    pin_of_item(monkeypatch, R.ANCHOR_STOP, f, json.dumps({**rec, "counts": {"kept": 3, "needed": 64}}).encode())
    with pytest.raises(R.Refused, match="has not been read"):               # a re-pinned record must be read again
        R.family_stopped(f)


def test_35_a_stopped_family_s78_kinds_refuse_for_good_and_the_retrain_runs_under_main_f(monkeypatch):
    """DESO2 item 36 (1), (2); AM1 changes 2, 5, 13 (DESO3 V1); GXB O6, item 14: once a family's stop record is
    pinned and read, rep_pass, l1_scan, the classifier, a1_pass (and the anchor job) refuse for good there (at the key
    check, the runner's gate, the pins and the order), the a0-1101 retrain is planned under MAIN_F (recipe "B") without
    RECIPE_S or a complete anchor job, on Y with ENGINE_Y (filled when that retrain is prepared), and the X retrain
    under MAIN_F after the Y one. An unstopped family refuses a main-config retrain."""
    f, main = "olmo2-7b", R.CONFIGS["olmo2-7b"]["main"][1]
    with pytest.raises(R.Refused, match="recipe S_78"):
        R.check_keys(**keys_of(f, kind="retrain", recipe_sha256=main))        # unstopped: S_78 only
    assert R.sc_recipe(f, "retrain") == "S" and R.sc_needed_pins("retrain", "Y", f) == ("RECIPE_S", "ENGINE_Y")
    assert "after anchor" in R.sc_order_problem("retrain", [], f)
    stop_family(monkeypatch, f)
    assert R.family_stopped(f) and not R.family_stopped("llama31-8b")
    for kind in ("rep_pass", "l1_scan", "classifier", "a1_pass", "anchor"):
        recipe = R.CONFIGS[f]["main"][1]
        with pytest.raises(R.Refused, match="never runs on that family"):
            R.check_keys(**keys_of(f, kind=kind, recipe_sha256=recipe))
        with pytest.raises(R.Refused, match="never runs on that family"):
            R.sc_pins_or_refuse(f, kind, "X", pins78_doc())
        assert "never runs" in R.sc_order_problem(kind, ["anchor", "retrain", "untuned_answers"], f)
        with pytest.raises(R.Refused, match="never runs"):
            R.job_decision(f, *preflight_pair(f), R.job_record(f, kind), 10 ** 6, 100.0)
    monkeypatch.setitem(R.RECIPE_S, f, "ab" * 32)                     # even with S_78 filled, never
    with pytest.raises(R.Refused, match="never runs"):
        R.check_keys(**keys_of(f, kind="rep_pass", recipe_sha256="ab" * 32))
    monkeypatch.setitem(R.RECIPE_S, f, None)
    y = "d3" * 32
    monkeypatch.setattr(R, "ENGINE_Y", y)
    R.check_keys(**keys_of(f, kind="retrain", recipe_sha256=main, engine_sha256=y))      # MAIN_F on Y
    for recipe in (R.CONFIGS[f]["g"][1], "ab" * 32):
        with pytest.raises(R.Refused, match="main config only"):
            R.check_keys(**keys_of(f, kind="retrain", recipe_sha256=recipe, engine_sha256=y))
    assert R.sc_recipe(f, "retrain") == "B" and R.sc_recipe(f, "untuned_answers") == "B"
    assert R.sc_needed_pins("retrain", "Y", f) == ("ENGINE_Y",) and R.sc_needed_pins("retrain", "X", f) == ()
    assert R.sc_order_problem("retrain", [], f) is None                     # the stop record replaces the anchor job
    assert R.sc_pins_or_refuse(f, "retrain", "Y", pins78_doc())["ENGINE_Y"] == y
    assert R.sc_engine_problem("retrain", "X", ()) and R.sc_engine_problem("retrain", "X", ("Y",)) is None
    d = R.job_decision(f, *preflight_pair(f), R.job_record(f, "retrain"), 10 ** 6, 100.0)
    assert d["action"] == "run"                                             # RECIPE_S null, yet the MAIN_F retrain runs
    monkeypatch.setattr(R, "ENGINE_Y", None)
    with pytest.raises(R.Refused, match="ENGINE_Y waits for .*main-config \\(MAIN_F\\) retrain is prepared"):
        R.sc_pins_or_refuse(f, "retrain", "Y", pins78_doc())
    assert R.sc_pins_or_refuse("llama31-8b", "anchor", "X", pins78_doc()) is not None      # the other family: normal
    monkeypatch.setitem(R.ANCHOR_STOP, f, {"path": "/abs.json", "sha256": hx("stop")})
    with pytest.raises(R.Refused, match="not a .path, sha256. pin"):
        R.family_stopped(f)


def test_35b_a_stopped_familys_kit_copy_plans_the_main_f_retrain(tmp_path, monkeypatch):
    """The kit copy's retrain_job: on a stopped family (its record read at the pin) it plans recipe "B" (MAIN_F) with
    RECIPE_S null; unstopped, it still refuses while RECIPE_S is null."""
    sr = kit_copy(tmp_path, "llama31-8b", "sc")
    with pytest.raises(R.Refused, match="not written yet"):
        sr.retrain_job()
    stop_family(monkeypatch, "llama31-8b", "harmful")
    job = sr.retrain_job()
    assert job["kind"] == "retrain" and job["recipe"] == "B" and job["seed"] == 1101 and job["unmeasured"]


def test_36_ref_train_runs_under_recipe_g_only():
    """Part 2 §3.2; P2FV D6: ref_train (recipe G's reference, the 1B form) is a measured kind, 38 steps, counted, under
    RECIPE_G only (null refuses at the key check and the runner's gate); the main config never passes for it."""
    assert "ref_train" in R.MEASURED_KINDS and "ref_train" in R.COUNTED_KINDS and R.G_KINDS == frozenset({"ref_train"})
    for family in R.FAMILIES:
        job = R.job_record(family, "ref_train", oext=True)
        assert job["steps"] == 38 and job["counted"] == 1 and not job["unmeasured"]
        for recipe in (R.CONFIGS[family]["main"][1], R.CONFIGS[family]["g"][1]):
            with pytest.raises(R.Refused, match="RECIPE_G for .* is null"):
                R.check_keys(**keys_of(family, kind="ref_train", recipe_sha256=recipe))
        with pytest.raises(R.Refused, match="RECIPE_G"):
            R.job_decision(family, *preflight_pair(family), job, 10 ** 6, 100.0)


def test_36b_ref_train_takes_its_filled_recipe_g_pin_only(monkeypatch):
    for family in R.FAMILIES:
        g = R.CONFIGS[family]["g"][1]
        monkeypatch.setitem(R.RECIPE_G, family, g)
        R.check_keys(**keys_of(family, kind="ref_train", recipe_sha256=g))
        with pytest.raises(R.Refused, match="RECIPE_G only"):
            R.check_keys(**keys_of(family, kind="ref_train", recipe_sha256=R.CONFIGS[family]["main"][1]))
        assert R.job_decision(family, *preflight_pair(family), R.job_record(family, "ref_train", oext=True), 10 ** 6, 100.0)["action"] == "run"


def test_37_the_oext_scripts_are_track_os_wrapper():
    """GXB B-3; PLAN-AB item 5d: OEXT_UNIT_SCRIPT, C0_SCRIPT and W1_18_SCRIPT are Track O's one wrapper
    scripts/scale78b/oext_78b.py (its unit, lean and w1_18 commands); the 1B scripts are not named."""
    assert R.OEXT_UNIT_SCRIPT == R.C0_SCRIPT == R.W1_18_SCRIPT == R.OEXT_WRAPPER_78B == "scripts/scale78b/oext_78b.py"
    assert R.OEXT_WRAPPER_COMMANDS == {"o_only": "unit", "o_only_with_regenerate": "unit", "c0": "lean", "w1_18": "w1_18"}
    assert R.oext_form_problem(oext_pin("olmo2-7b")) is None


def test_37b_oext_78b_y_is_a_null_pin_per_family_for_bqis_oext_on_y(monkeypatch):
    """GXB T-O3; DESO2 item 24 (c): OEXT_78B_Y[family] (the Y variant of OEXT_78B's files, the 1B oext_unit_y.json
    form) is null per family; B+Qi's O-ext on Y refuses until it is filled, which comes after ENGINE_Y and the
    family's RECIPE_BQI; a filled value has OEXT_78B's form."""
    assert R.OEXT_78B_Y == {"olmo2-7b": None, "llama31-8b": None}
    for family in R.FAMILIES:
        rec = oext_pin(family, "Y")
        with pytest.raises(R.Refused, match="OEXT_78B_Y.* is null: .*ENGINE_Y and the family's RECIPE_BQI filled"):
            R.oext_y_or_refuse(family)
        monkeypatch.setitem(R.OEXT_78B_Y, family, rec)
        with pytest.raises(R.Refused, match="filled before ENGINE_Y"):
            R.oext_y_or_refuse(family)
        monkeypatch.setattr(R, "ENGINE_Y", "d3" * 32)
        with pytest.raises(R.Refused, match="filled before ENGINE_Y"):
            R.oext_y_or_refuse(family)                                   # RECIPE_BQI still null
        monkeypatch.setitem(R.RECIPE_BQI, family, "cd" * 32)
        assert R.oext_y_or_refuse(family) is rec
        monkeypatch.setitem(R.OEXT_78B_Y, family, {"files": {}, "inputs": rec["inputs"]})
        with pytest.raises(R.Refused, match="not OEXT_78B's form"):
            R.oext_y_or_refuse(family)
        done, ver = preflight_pair(family)
        monkeypatch.setitem(R.OEXT_78B_Y, family, None)
        with pytest.raises(R.Refused, match="OEXT_78B_Y"):
            R.job_decision(family, done, ver, R.job_record(family, "ref_train_bqi"), 10 ** 6, 100.0)
        monkeypatch.setitem(R.OEXT_78B_Y, family, rec)
        assert R.job_decision(family, done, ver, R.job_record(family, "ref_train_bqi"), 10 ** 6, 100.0)["action"] == "run"
        monkeypatch.setattr(R, "ENGINE_Y", None)
    assert "OEXT_78B_Y" in R.SC_PIN_EVENTS


def test_37c_r5_one_oext_index_per_family_and_engine(monkeypatch):
    """GXB R-5 (sixth set): OEXT_78B[F] (engine X) and OEXT_78B_Y[F] (engine Y) each pin exactly one O-ext index, their
    own family's for their own engine, beside the wrapper's pin; another family's or engine's index, two indexes, none,
    or no wrapper refuses. A fill of one family's pin leaves the other family's form untouched."""
    for family in R.FAMILIES:
        other = [f for f in R.FAMILIES if f != family][0]
        assert R.oext_form_problem(oext_pin(family, "X"), family, "X") is None
        assert R.oext_form_problem(oext_pin(family, "Y"), family, "Y") is None
        assert "not " + family in R.oext_form_problem(oext_pin(other, "X"), family, "X") or \
            "is " + other in R.oext_form_problem(oext_pin(other, "X"), family, "X")
        assert "for engine Y, not" in R.oext_form_problem(oext_pin(family, "Y"), family, "X")
        assert "for engine X, not" in R.oext_form_problem(oext_pin(family, "X"), family, "Y")
        two = oext_pin(family)
        two["files"].update(oext_pin(other)["files"])
        assert "2 O-ext index file(s)" in R.oext_form_problem(two, family, "X")
        none = {"files": {R.OEXT_WRAPPER_78B: hx("w")}, "inputs": oext_pin(family)["inputs"]}
        assert "0 O-ext index file(s)" in R.oext_form_problem(none, family, "X")
        nowrap = oext_pin(family)
        nowrap["files"].pop(R.OEXT_WRAPPER_78B)
        assert "do not pin the wrapper" in R.oext_form_problem(nowrap, family, "X")
        assert R.oext_form_problem(oext_pin(other, "Y")) is None              # the form alone: no family named
        monkeypatch.setitem(R.OEXT_78B, family, oext_pin(other))
        with pytest.raises(R.Refused, match="GXB R-5"):
            R.sc_pin_values(family, pins78_doc())
        monkeypatch.setitem(R.OEXT_78B, family, oext_pin(family))
        assert R.sc_pin_values(family, pins78_doc())["OEXT_78B"] == oext_pin(family)
        assert R.OEXT_78B[other] is None                                       # fill once per family (T-O2)
        monkeypatch.setitem(R.OEXT_78B, family, None)
    monkeypatch.setattr(R, "ENGINE_Y", "d3" * 32)
    monkeypatch.setitem(R.RECIPE_BQI, "llama31-8b", "cd" * 32)
    monkeypatch.setitem(R.OEXT_78B_Y, "llama31-8b", oext_pin("llama31-8b", "X"))
    with pytest.raises(R.Refused, match="for engine X, not llama31-8b's for engine Y"):
        R.oext_y_or_refuse("llama31-8b")
    monkeypatch.setitem(R.OEXT_78B_Y, "llama31-8b", oext_pin("llama31-8b", "Y", bank=hx("ybank")))
    R.check_keys(**keys_of("llama31-8b", kind="ref_train_bqi", recipe_sha256="cd" * 32, engine_sha256="d3" * 32),
                 oext_bank=hx("ybank"))                                        # engine Y reads its own pin
    with pytest.raises(R.Refused, match="not llama31-8b's pinned O-ext bank"):
        R.check_keys(**keys_of("llama31-8b", kind="ref_train_bqi", recipe_sha256="cd" * 32, engine_sha256="d3" * 32),
                     oext_bank=hx("b"))


def test_39_k1v7_the_verifiers_surviving_probes(monkeypatch):
    """K1V-7: the checks the verifier's probes found untested: an edit pin's .json suffix; W1_18_78B's scripts/ prefix;
    the gate's int version; an N unit with an extra key (and Llama's N a0-1103 needing N_UNITS: test_30; the stop
    record's int exit code: test_34; the branch switch's source and W1-18 hash: test_29)."""
    monkeypatch.setitem(R.METHOD_EDITS["olmo2-7b"], "A1", {"path": "tmp/a1.edit.txt", "sha256": hx("a1"), "rows": 600})
    with pytest.raises(R.Refused, match="plain relative .json path"):
        R.run_edit("olmo2-7b", "A1", 1102)
    for files in ({"experiments/w.py": hx("w")}, {"tmp/scripts/w.py": hx("w")}, {"scripts/../w.py": hx("w")}):
        assert "under scripts/" in R.files_form_problem({"files": files})
    assert R.files_form_problem({"files": {R.W1_18_SCRIPT: hx("w")}}) is None
    for version in (True, 1.0, "1"):
        assert "kind and version" in R.gate_record_problem(gate_doc(version=version))
        assert "kind and version" in R.plan_b_record_problem(plan_b_doc(version=version))
    doc = n_units_doc("olmo2-7b")
    doc["R-1102"] = {**doc["R-1102"], "note": "extra"}
    assert "must hold exactly" in R.n_units_problem(doc, "olmo2-7b")
    llama = n_units_doc("llama31-8b")
    llama["a0-1103"] = {**llama["a0-1103"], "edit_sha256": hx("e")}           # an a0 unit holds no edit
    assert "must hold exactly" in R.n_units_problem(llama, "llama31-8b")


def test_40_k1v8_a_malformed_n_units_pin_refuses_at_use_never_at_import(tmp_path, monkeypatch):
    """K1V-8: a malformed N_UNITS pin never breaks an import of the kit's stage1_rules (block 0, sc and A copies
    import; REJUDGED_PINS["A"] keeps N's entries null); it refuses at use, with a clear message, in
    rejudged_or_refuse (the judge launch) and sc_pin_values (the scorer block's planning)."""
    bad = n_units_doc("olmo2-7b")
    bad.pop("R-1103")
    monkeypatch.setitem(R.N_UNITS, "olmo2-7b", bad)
    for block in ("0", "sc", "A"):
        sr = kit_copy(tmp_path / block, "olmo2-7b", block)
        assert [p["complete_sha256"] for p in sr.REJUDGED_PINS["A"][:3]] == [None] * 3
    with pytest.raises(R.Refused, match="N_UNITS\\['olmo2-7b'\\] is not N's unit record: its keys are not N's units"):
        R.rejudged_or_refuse("olmo2-7b", "A")
    with pytest.raises(R.Refused, match="is not N's unit record"):
        R.sc_pin_values("olmo2-7b", pins78_doc())
    assert R.rejudged_pins("olmo2-7b", "B") == ()


def test_41_k1v9_a_unit_is_named_by_arm_and_seed_and_a_missing_arm_refuses(tmp_path):
    """K1V-9 (GXB's seed key): sc_unit_input_names / sc_unit_input_pins name o_only_with_regenerate's unit by (arm,
    seed) and refuse a missing arm or a pair that is not one of its units. The seed-only form remains only at the four
    call sites K2 and K3 own (the runner :466, :483; the pack :432; the planner :1306), listed here so that no new
    caller uses it; when they move, this test's list shrinks (a K2/K3 acceptance item)."""
    sr = kit_copy(tmp_path, "olmo2-7b", "sc")
    with pytest.raises(ValueError, match="the arm is missing"):
        sr.sc_unit_input_names("o_only_with_regenerate", None, 1101)
    with pytest.raises(ValueError, match="not one of its units"):
        sr.sc_unit_input_names("o_only_with_regenerate", "R", 1104)
    assert sr.sc_unit_input_names("o_only_with_regenerate", "R", 1101) == (
        "n_complete:R:1101", "regen_edit:R:1101", "oext_bank", "oext_record")
    assert sr.sc_unit_input_names("o_only_with_regenerate", "a0", 1101) == (
        "side_complete:a0:1101", "oext_bank", "oext_record")
    assert sr.sc_unit_input_names("o_only", "theta0", None) == ("oext_bank", "oext_record")
    values = R.sc_pin_values("olmo2-7b", pins78_doc())
    with pytest.raises(ValueError, match="the arm is missing"):
        sr.sc_unit_input_pins("o_only_with_regenerate", pins78_doc(), values, None, 1101)
    assert set(sr.sc_unit_input_pins("o_only_with_regenerate", pins78_doc(), values, "R", 1101)) == {
        "n_complete:R:1101", "regen_edit:R:1101", "oext_bank", "oext_record"}
    assert seed_only_calls() == R16_SEED_ONLY_CALLS


# GXB R-16's seed-only call sites (K3's files; the list is empty by K3's end): (file, the call's line). R2 K2 moved the
# planner's (plan_tool.py) to the strict form (GXB R-31).
R16_SEED_ONLY_CALLS = {("pack_setup.py", "rules.sc_input_pins(kind, pins78(), values, seed)"),
                       ("setup/job_runner_stage1.py", 'rules.sc_input_names(job["kind"], job.get("seed"))'),
                       ("setup/job_runner_stage1.py", 'rules.sc_input_names(job["kind"], job.get("seed"))#2')}
SEED_ONLY_ARGS = {"sc_input_names": 3, "sc_input_pins": 5}     # positional slots up to and including arm


def seed_only_calls() -> set:
    """KR3: every call of sc_input_names / sc_input_pins in every non-test .py file of the kit, by any prefix or
    name, that passes no arm (fewer positional arguments than the arm's slot and no arm= keyword); any other
    reference to those names outside a call (an alias) is reported too. stage1_rules.py's own calls pass the arm."""
    out, seen = set(), {}
    for path in sorted(KIT.rglob("*.py")):
        rel = path.relative_to(KIT).as_posix()
        if rel.startswith("tests/"):
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
                if name in SEED_ONLY_ARGS:
                    calls.add(id(f))
                    if len(node.args) < SEED_ONLY_ARGS[name] and not any(k.arg == "arm" for k in node.keywords):
                        text = ast.get_source_segment(source, node)
                        n = seen.get((rel, text), 0) + 1
                        seen[(rel, text)] = n
                        out.add((rel, text if n == 1 else f"{text}#{n}"))
        for node in ast.walk(tree):
            name = node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else None
            if name in SEED_ONLY_ARGS and id(node) not in calls and not isinstance(getattr(node, "ctx", None), ast.Store):
                out.add((rel, f"reference {name} at line {node.lineno}"))
    return out


def test_41b_kr3_the_seed_only_scan_sees_every_kit_file_and_any_call_form(tmp_path):
    """KR3: the scan reads every non-test .py file of the kit (not a fixed list) and any call form (a bare name, an
    alias prefix, a keyword arm); it finds a new seed-only caller in a file test_41's old list did not read."""
    found = seed_only_calls()
    assert found == R16_SEED_ONLY_CALLS
    files = {rel for rel, _ in found}
    assert files == {"pack_setup.py", "setup/job_runner_stage1.py"}               # R2 K2: plan_tool.py moved
    probe = ast.parse("import stage1_rules as r\nr.sc_input_names('o_only_with_regenerate', 1101)\n"
                      "sc_input_pins(k, p, v, 1101)\nr.sc_input_names(k, 1101, arm='R')\nf = r.sc_input_pins\n")
    kinds = []
    for node in ast.walk(probe):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
            if name in SEED_ONLY_ARGS:
                kinds.append(len(node.args) < SEED_ONLY_ARGS[name] and not any(k.arg == "arm" for k in node.keywords))
    assert kinds == [True, True, False]
    n_py = len([p for p in KIT.rglob("*.py") if not p.relative_to(KIT).as_posix().startswith("tests/")])
    assert n_py >= 20                                                 # launch.py, host.py, budget.py, ... included


# Block 0's plan.json at 3481d85 (M, 8 Nov 2026: r1-k1-scratch/plan0.py on `git archive 3481d85 runkit/stage1-78b`, the
# World of tests/test_stage1_runkit.py, a real init-block 0, the clock fixed at 2026-11-08T00:00:00+00:00, the tmp
# path replaced by "<TMP>"): its byte count and SHA-256 per family. GXB R-3 holds K1's block 0 to these bytes.
BLOCK0_PLAN_3481D85 = {"olmo2-7b": (14106, "263e2541dc556209ae27441cc0ca94ca328010490b971bb5bf8a077de63915bf"),
                       "llama31-8b": (14605, "ceff076129ba87a17c6ff38f450d5fb81a8dfd30762ec3e0b9c6f1082a578555")}


def test_42_r3_block_0s_plan_json_is_3481d85s_byte_for_byte(tmp_path, monkeypatch):
    """GXB R-3 (K1V-13): the two new job keys (oext, padded_tokens_per_step) are written only on block A and B jobs;
    block 0's plan.json (a real init through the kit's own test World, the clock fixed, the tmp path normalised) is
    byte for byte the one 3481d85's kit writes."""
    runkit = load_by_path("test_stage1_runkit_for_r3", HERE / "test_stage1_runkit.py")
    try:
        for family, (size, digest) in BLOCK0_PLAN_3481D85.items():
            root = tmp_path / family
            root.mkdir()
            with pytest.MonkeyPatch.context() as mp:
                w = runkit.World(root, mp, family)
                mp.setattr(w.mac, "utc", lambda: "2026-11-08T00:00:00+00:00")
                w.init()
                data = (w.root / "plan.json").read_bytes().replace(str(root).encode(), b"<TMP>")
                assert (len(data), hashlib.sha256(data).hexdigest()) == (size, digest), family
                assert b'"oext"' not in data and b'"padded_tokens_per_step"' not in data
                for name in runkit.MODULES:
                    sys.modules.pop(name, None)
    finally:
        sys.modules.pop("test_stage1_runkit_for_r3", None)
    assert sys.modules.get("rules_78b") is R or "rules_78b" not in sys.modules


def test_43_r24_block_bs_plan_is_the_plan_its_basis_gives(monkeypatch):
    """GXB R-24 (KR1): PLAN_B_78B's plan equals the plan its basis gives by P1 §6.1: basis sigma_A the plan of the
    sigma_A_pp the record carries (4.5 / 6.0 pp thresholds); basis sigma_pool_N the gate's provisional plan; basis
    sigma_F (only under [C]) the sigma_F plan the gate records under [C]. Any other plan refuses (about $198 of runs, E:
    H (b)'s 47 per family against plan A's 23)."""
    for sigma, plan in ((0.0, "A"), (4.5, "A"), (4.51, "B9"), (6.0, "B9"), (6.01, "H"), (10.7, "H"), (12, "review")):
        assert R.plan_for_sigma(sigma) == plan
        assert R.plan_b_record_problem(plan_b_doc(sigma_A_pp=sigma, plan=plan)) is None
        for other in {"A", "B9", "H", "review"} - {plan}:
            assert "GXB R-24" in R.plan_b_record_problem(plan_b_doc(sigma_A_pp=sigma, plan=other)), (sigma, other)
    for bad in (None, float("nan"), -0.1, True, "5.0"):
        assert "sigma_A_pp is blinded_sigma.py's sigma_A" in R.plan_b_record_problem(plan_b_doc(sigma_A_pp=bad))
        with pytest.raises(R.Refused):
            R.plan_for_sigma(bad)
    sr = load_by_path("stage1_rules_plan_r24", KIT / "stage1_rules.py")
    try:
        for sigma in (0.0, 3.0, 4.5, 4.500001, 5.2, 6.0, 6.5, 10.7066):
            assert sr.plan_code_for(sigma) == R.plan_for_sigma(sigma)     # one seed rule below the ceiling
        assert sr.plan_code_for(20.0) == "H" and R.plan_for_sigma(20.0) == "review"   # R-29: RK adds the ceiling
    finally:
        sys.modules.pop("stage1_rules_plan_r24", None)
    no = dict(sr2_adopted=False, sr2_reason="simulation_reading", sigma_A_pp=None, blinded_sigma_output_sha256=None,
              blinded_sigma_inputs_sha256=None)
    assert "sigma_A_pp is null" in R.plan_b_record_problem(plan_b_doc(**{**no, "sigma_A_pp": 5.0},
                                                                      plan_basis="sigma_pool_N"))
    # basis sigma_pool_N ([B]): the gate's provisional plan
    for provisional in ("A", "B9", "H"):
        gate = json.dumps(gate_doc(provisional_plan=provisional)).encode()
        pin_of(monkeypatch, "GATE_78B", gate)
        for plan in ("A", "B9", "H"):
            data = json.dumps(plan_b_doc(**no, plan=plan, plan_basis="sigma_pool_N")).encode()
            pin_of(monkeypatch, "PLAN_B_78B", data)
            if plan == provisional:
                assert R.block_init_or_refuse("B", "olmo2-7b", gate, data)["plan"] == plan
            else:
                with pytest.raises(R.Refused, match="not the gate's provisional plan"):
                    R.block_init_or_refuse("B", "olmo2-7b", gate, data)
    # basis sigma_F ([C]): the gate's sigma_F plan, not its provisional plan
    gate_c = json.dumps(gate_doc(option="C", families=["olmo2-7b"], provisional_plan="A", sigma_F_plan="H")).encode()
    pin_of(monkeypatch, "GATE_78B", gate_c)
    for plan in ("A", "B9", "H"):
        data = json.dumps(plan_b_doc(**no, plan=plan, plan_basis="sigma_F")).encode()
        pin_of(monkeypatch, "PLAN_B_78B", data)
        if plan == "H":
            assert R.block_init_or_refuse("B", "olmo2-7b", gate_c, data)["plan"] == "H"
        else:
            with pytest.raises(R.Refused, match="not the gate's sigma_F plan"):
                R.block_init_or_refuse("B", "olmo2-7b", gate_c, data)
    # basis sigma_A: the plan of the sigma_A the record carries, whatever the gate's provisional plan
    data = json.dumps(plan_b_doc(plan="B9", sigma_A_pp=5.5)).encode()
    pin_of(monkeypatch, "GATE_78B", json.dumps(gate_doc(provisional_plan="H")).encode())
    pin_of(monkeypatch, "PLAN_B_78B", data)
    assert R.block_init_or_refuse("B", "olmo2-7b", json.dumps(gate_doc(provisional_plan="H")).encode(), data)["plan"] == "B9"
    # the gate's sigma_F_plan: required under [C], null under [B]
    assert "under [C] sigma_F_plan" in R.gate_record_problem(gate_doc(option="C", families=["olmo2-7b"]))
    assert "under [C] sigma_F_plan" in R.gate_record_problem(gate_doc(option="C", families=["olmo2-7b"],
                                                                      sigma_F_plan="B10"))
    assert "under [B] sigma_F_plan is null" in R.gate_record_problem(gate_doc(sigma_F_plan="A"))
    assert R.gate_record_problem(gate_doc(option="C", families=["olmo2-7b"], sigma_F_plan="review")) is None


def test_44_r22_track_os_index_names_and_r21_the_w1_18_record_folder():
    """GXB R-22: the O-ext index names are Track O's, scripts/scale78b/settings/OEXT-78B__<F>.json (engine X) and
    OEXT-78B-Y__<F>.json (engine Y); K1's earlier oext_index__ name is no index. GXB R-21: one entry, the family's
    W1-18 record, may sit directly under .ai/inputs/stage1-post-w1-20261023/78b/w1-18/; every other entry stays under
    scripts/."""
    for family in R.FAMILIES:
        x = oext_pin(family, "X")
        assert f"scripts/scale78b/settings/OEXT-78B__{family}.json" in x["files"]
        assert f"scripts/scale78b/settings/OEXT-78B-Y__{family}.json" in oext_pin(family, "Y")["files"]
        old = {"files": {R.OEXT_WRAPPER_78B: hx("w"), f"scripts/scale78b/settings/oext_index__{family}__X.json": hx("i")},
               "inputs": x["inputs"]}
        assert "0 O-ext index file(s)" in R.oext_form_problem(old, family, "X")
        near = {"files": {R.OEXT_WRAPPER_78B: hx("w"), f"scripts/scale78b/settings/OEXT-78B__{family}__X.json": hx("i")},
                "inputs": x["inputs"]}                   # R2 K2 (R-33): a candidate off the standard name is no index
        assert "1 O-ext index file(s)" in R.oext_form_problem(near, family, "X")
        rec = f"{R.W1_18_RECORD_DIR}overrefusal_checks__{family}.json"
        with_rec = {"files": {**x["files"], rec: hx("rec")}, "inputs": x["inputs"]}
        assert R.oext_form_problem(with_rec, family, "X") is None and R.oext_form_problem(with_rec) is None
        two = {"files": {**with_rec["files"], f"{R.W1_18_RECORD_DIR}other.json": hx("rec2")}, "inputs": x["inputs"]}
        assert "at most the one W1-18 record" in R.oext_form_problem(two)
        for bad in (f"{R.W1_18_RECORD_DIR}sub/w.json", f"{R.W1_18_RECORD_DIR}w.txt", f"{R.W1_18_RECORD_DIR}../w.json"):
            doc = {"files": {**x["files"], bad: hx("rec")}, "inputs": x["inputs"]}
            assert "W1-18 record directly under" in R.oext_form_problem(doc), bad
        for bad in (".ai/inputs/stage1-post-w1-20261023/78b/other/w.json", "tmp/w1-18/w.json"):
            doc = {"files": {**x["files"], bad: hx("rec")}, "inputs": x["inputs"]}
            assert "not a plain relative path under scripts/" in R.oext_form_problem(doc), bad
        bad_digest = {"files": {**x["files"], rec: "nothex"}, "inputs": x["inputs"]}
        assert "is not a SHA-256" in R.oext_form_problem(bad_digest)


def test_45_kr2_kr7_kr8_the_stop_records_and_the_branchs_remaining_checks(monkeypatch):
    """KR2: the stop record's needed == 64, of == 64, the prompt_index range and the job_done_sha256 form; KR7: the
    "s4_top" in dose_arms guard (a filled s4_top pin of other rows does not refuse where no s4_top runs) and the branch
    record's utc / recorded_by check; KR8: anchor_stop_or_refuse always needs the anchor job's JOB-DONE.json SHA-256."""
    done = hx("job-done")
    few = R.anchor_stop_record("olmo2-7b", 3, None, done, {"kept": 10, "needed": 64})
    pair = R.anchor_stop_record("olmo2-7b", 1, HARMFUL, done)
    for counts in ({"kept": 10, "needed": 63}, {"kept": 10, "needed": 65}):
        assert "its counts are not {kept < 64, needed 64}" in R.anchor_stop_problem({**few, "counts": counts}, "olmo2-7b")
    for counts in ({"prompt_index": 7, "position": 8, "of": 63}, {"prompt_index": 64, "position": 65, "of": 64},
                   {"prompt_index": -1, "position": 0, "of": 64}):
        assert "its counts are not {prompt_index, position, of 64}" in R.anchor_stop_problem({**pair, "counts": counts},
                                                                                             "olmo2-7b"), counts
    for bad in ("x", "A" * 64, None, 7):
        assert "job_done_sha256 is not a SHA-256" in R.anchor_stop_problem({**few, "job_done_sha256": bad}, "olmo2-7b")
    data = json.dumps(few).encode()
    pin_of_item(monkeypatch, R.ANCHOR_STOP, "olmo2-7b", data)
    monkeypatch.setattr(R, "_ANCHOR_STOPS_READ", {})
    for bad in (None, "x"):
        with pytest.raises(R.Refused, match="JOB-DONE.json SHA-256 is required"):
            R.anchor_stop_or_refuse("olmo2-7b", data, bad)
    with pytest.raises(TypeError):
        R.anchor_stop_or_refuse("olmo2-7b", data)                           # no default: the argument is required
    assert not R._ANCHOR_STOPS_READ
    monkeypatch.setitem(R.ANCHOR_STOP, "olmo2-7b", None)
    # KR7 (1): a filled s4_top pin of other rows is ignored where the kept count forms no s4_top
    monkeypatch.setitem(R.METHOD_EDITS["olmo2-7b"], "s4_top", {"path": "tmp/top.json", "sha256": hx("top"), "rows": 120})
    for kept, n in ((48, 23), (96, 26), (192, 29), (250, 29)):
        assert len(R.block_runs_78b("olmo2-7b", "A", "B", dose_seeds=3, kept=kept)) == n, kept
    # KR7 (2): the branch record's utc and recorded_by
    for key in ("utc", "recorded_by"):
        for bad in ("", "  ", None, 7):
            doc = {**branch_doc("olmo2-7b"), key: bad}
            assert "utc and recorded_by must be non-empty texts" in R.branch_record_problem(doc, "olmo2-7b"), (key, bad)


def test_46_r29_the_review_ceiling_on_sigma_a_equals_noise_readings_seed_rule(monkeypatch):
    """GXB R-29: P1 §6.4 applies §6.1's whole rule to sigma_A, the review ceiling included. RK's plan_for_sigma equals
    scripts/scale78b/noise_reading.py's seed_rule (loaded by path, read only; its outcome "review" or the plan) on the
    same sigma values, on both sides of each boundary: 4.5, 6.0 and the three ceilings 2 x 5 / factor (7.0388, 9.2721,
    10.7066 pp; only H (b)'s fires). PLAN_B_78B on basis sigma_A then says "review" above 10.7066 pp and refuses any
    other plan there."""
    assert R.PLAN_MDE_FACTORS == {"A": "1.4207", "B9": "1.0785", "H": "0.9340"} and R.SESOI_PP == 5
    nr = load_by_path("noise_reading_for_r29", ROOT / "scripts" / "scale78b" / "noise_reading.py")
    try:
        assert {k: str(v) for k, v in nr.MDE_FACTOR.items()} == R.PLAN_MDE_FACTORS and nr.SESOI_PP == R.SESOI_PP
        values = ["0", "3.2", "4.5", "4.5000001", "4.4999999", "6.0", "5.9999999", "6.0000001", "7.0388", "7.0389",
                  "9.2721", "9.2722", "10.7066", "10.70663", "10.70664", "10.7067", "11.5", "25",
                  "10.7066381", "10.7066382"]                    # within 1e-6 of H (b)'s exact ceiling 10 / 0.9340
        for text in values:
            want = nr.seed_rule([(Fraction(text) ** 2,)], 4)
            want = "review" if want["review"] else want["plan"]
            assert R.plan_for_sigma(float(text)) == want, (text, want)
        assert R.plan_for_sigma(10.7066381) == "H" and R.plan_for_sigma(10.7066382) == "review"
        assert {k: round(float(v), 4) for k, v in nr.CEILING_SIGMA_PP.items()} == {"A": 7.0388, "B9": 9.2721,
                                                                                   "H": 10.7066}
    finally:
        sys.modules.pop("noise_reading_for_r29", None)
    gate = json.dumps(gate_doc(provisional_plan="H")).encode()
    pin_of(monkeypatch, "GATE_78B", gate)
    for sigma, plan in ((10.7066, "H"), (10.7067, "review"), (14.0, "review")):
        assert R.plan_b_record_problem(plan_b_doc(sigma_A_pp=sigma, plan=plan)) is None
        for other in {"A", "B9", "H", "review"} - {plan}:
            assert "GXB R-24" in R.plan_b_record_problem(plan_b_doc(sigma_A_pp=sigma, plan=other)), (sigma, other)
    data = json.dumps(plan_b_doc(sigma_A_pp=11.0, plan="review")).encode()
    pin_of(monkeypatch, "PLAN_B_78B", data)
    with pytest.raises(R.Refused, match="block B's plan is 'review'.*plans nothing"):
        R.block_init_or_refuse("B", "olmo2-7b", gate, data)


def test_38_every_new_k1_pin_is_null_and_names_its_event():
    """A13's pattern for every pin R1 K1 adds: GATE_78B, N_UNITS, W1_18_78B, ANCHOR_STOP (null = no stop), the O-ext
    term's measured value, and the null method edits; each refusal names the event that fills it."""
    assert R.GATE_78B is None and R.PLAN_B_78B is None and R.W1_18_78B is None
    assert R.N_UNITS == {"olmo2-7b": None, "llama31-8b": None} == R.ANCHOR_STOP == R.OEXT_TERM_MEASURED_S
    for family in R.FAMILIES:
        assert {a for a, v in R.METHOD_EDITS[family].items() if v is None} == {"A1", "L1", "S3", "S4", "S4_96",
                                                                               "S4_192", "s4_top"}
    for pin in ("N_UNITS", "W1_18_78B", "ENGINE_Y"):
        assert R.SC_PIN_EVENTS[pin] and "recorded" in R.SC_PIN_EVENTS[pin] or "fills" in R.SC_PIN_EVENTS[pin]
    assert "AM1" in R.SC_PIN_EVENTS["ENGINE_Y"] and "main-config (MAIN_F) retrain" in R.SC_PIN_EVENTS["ENGINE_Y"]
    assert "blinded_sigma.py" in R.PLAN_B_EVENT and "before block B" in R.PLAN_B_EVENT
    assert "ruling 9's gate" in R.GATE_EVENT and set(R.METHOD_EDIT_EVENTS) == {"A1", "L1", "S3", "S4", "S4_96",
                                                                               "S4_192", "s4_top"}


# ------------------------------------------------------------------------------------------ last: no bytecode
def test_16_no_pycache_written_by_this_suite():
    for folder in (KIT, STAGE1, ROOT / "experiments" / "safety_selection"):
        assert not list(folder.rglob("__pycache__")), folder
