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
import json
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
    Every kind that needs S_78 (the a0-1101 retrain; A1's attributes pass rep_pass) refuses through
    recipe_s_or_refuse while the pin is None. A filled pin (test-local; no config file is written) is accepted."""
    assert R.RECIPE_S == {"olmo2-7b": None, "llama31-8b": None}
    assert R.S78_KINDS == frozenset({"retrain", "rep_pass"}) and R.S78_KINDS <= set(R.E_KINDS)
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
    assert not list(KIT.glob("*.json.tmp")) and sorted(p.name for p in KIT.glob("*.json")) == [R.BASIS_FILE]


# ----------------------------------------------------------------------------------------------------- test 8
def test_08_kinds():
    for family in R.FAMILIES:
        assert R.upper_m_s(family, 33, "arm") < R.upper_m_s(family, 38, "arm")
        assert R.upper_m_s(family, 38, "a0_arm") == R.upper_m_s(family, 38, "arm")
        assert R.upper_m_s(family, None, "evalonly") == R.upper_m_s(family, 38) - 38 * R.FAMILIES[family]["TRAIN_STEP_MAX_S"]
        assert R.job_record(family, "a0_arm")["steps"] == 38
        assert R.job_record(family, "evalonly")["steps"] is None
        for kind in ("A1", "anchors", "scorer", "B+Qi", "w1_18", "similarity", "transfer_report", "a1_rescore",
                     "cert_c1", "b10_certify", "ref_train", "arm ", ""):
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
        assert R.e_cap_hours(family, "rep_pass") == R.REP_PASS_CAP_H_MAX == 16.5
        assert R.e_cap_hours(family, "retrain") == 4.5
        assert R.e_upper_s(family, "safe_lora", 3)["upper_s"] > R.e_upper_s(family, "safe_lora", 1)["upper_s"]
        assert R.e_upper_s(family, "ref_eval", 3)["upper_s"] - R.e_upper_s(family, "ref_eval", 1)["upper_s"] == pytest.approx(
            2 * R.evalonly_upper_s(family))
        with pytest.raises(R.Refused):
            R.e_upper_s(family, "safe_lora", 0)
        with pytest.raises(R.Refused):
            R.e_upper_s(family, "arm")
    with pytest.raises(R.Refused):
        R.upper_m_s("olmo2-7b", None, "arm")
    with pytest.raises(R.Refused):
        R.upper_m_s("olmo2-7b", 0, "arm")
    assert R.steps_of("remove") == 33 and R.steps_of("add") == 38 and R.steps_of("a0") == 38


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
    # An E kind's job carries its explicit window and no speed scaling (rep_pass needs S_78: test 7b; anchor here).
    anchor = R.job_record(f, "anchor")
    d = R.job_decision(f, slow, slow_ver, anchor, R.e_cap_hours(f, "anchor") * 3600 - R.POD_OVERHEAD_S, 20.0)
    assert d["action"] == "run" and d["requirement_s"] == anchor["start_requirement_s"]
    assert R.e_cap_hours(f, "rep_pass") == 16.5


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
                "T2-m-derive-allcapped-35"}
    assert required <= set(ids)


# ----------------------------------------------------------------------------------------------------- test 14
STDLIB = {"__future__", "argparse", "datetime", "decimal", "hashlib", "json", "math", "os", "pathlib", "re", "sys"}


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
                    root / "k/retrieved/h/tree/round1/hidden/progress.jsonl"):
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


# ------------------------------------------------------------------------------------------ last: no bytecode
def test_16_no_pycache_written_by_this_suite():
    for folder in (KIT, STAGE1, ROOT / "experiments" / "safety_selection"):
        assert not list(folder.rglob("__pycache__")), folder
