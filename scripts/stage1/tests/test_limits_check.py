"""REQ-19 end to end on synthetic Gate A units: the O MDE in both error models, the U8 decider, the NI report,
tau_L, the allow-list, the required f reading and the no-text rule."""

from __future__ import annotations

import copy
import json
import math
import os
import shutil
from fractions import Fraction
from statistics import NormalDist

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1.limits import limits_check as lcheck
from scripts.stage1.limits import limits_common as lc

import test_limits_fixtures as fx

N = NormalDist()
Z975, Z80, Z95 = N.inv_cdf(0.975), N.inv_cdf(0.8), N.inv_cdf(0.95)
# The 100-prompt O design of test_limits_fixtures, worked by hand (cells y(a0, j, p) - y(theta0, p)):
# column sums -1, -1, -3 (x 15), 3, 2, 1 (x 5), 0 (x 76); seed sums -13, -11, -13; total -37; 57 non-zero cells.
# SS_P = 155/3 - 1369/300 = 14131/300; SS_seeds = 459/100 - 1369/300 = 8/300; SS_total = 57 - 1369/300 = 15731/300;
# SS_E = 1592/300. MS_P = 14131/29700 (99 df); MS_E = 199/7425 (198 df); c = (MS_P - MS_E)/3 = 889/5940.
MS_P, MS_E, C = Fraction(14131, 29700), Fraction(199, 7425), Fraction(889, 5940)
SEED_VARIANCE = Fraction(4, 3)                       # the seeds' O 4, 6, 4 pp


@pytest.fixture
def gate_a(tmp_path):
    root = tmp_path / "data"
    return root, fx.build_gate_a(root)


def run_doc(settings, root):
    return json.loads(lcheck.run(settings, "f" * 64, root))


def test_the_o_numbers_by_hand(gate_a):
    root, settings = gate_a
    doc = run_doc(settings, root)
    o = doc["o"]
    assert o["o_pp"] == {"untuned": 17.0, "1101": 4.0, "1102": 6.0, "1103": 4.0}
    assert {n: doc["units"][n]["o_refusals"] for n in doc["units"]} == {"untuned": 17, "1101": 4, "1102": 6, "1103": 4}
    assert o["a0_seed_variance_pp2"] == pytest.approx(float(SEED_VARIANCE), rel=1e-15)
    assert o["a0_seed_sd_pp"] == pytest.approx(math.sqrt(4 / 3), rel=1e-15) and o["a0_seed_df"] == 2
    table = o["planning_table"]
    assert (table["ms_prompts"], table["ms_error"]) == (float(MS_P), float(MS_E))
    assert table["prompt_component_share2"] == float(C) and (table["df_prompts"], table["df_error"]) == (99, 198)
    assert table["grand_mean_pp"] == pytest.approx(100 * -37 / 300, rel=1e-12)
    assert (o["bank"]["planning_prompts"], o["bank"]["f"]) == (100, 1)
    paired = o["per_seed_paired_report_only"]
    assert {n: paired[n]["discordant"] for n in paired} == {"1101": 19, "1102": 19, "1103": 19}
    assert paired["1101"]["paired_se_pp"] == pytest.approx(100 * math.sqrt(19 / 1e4 - 169 / 1e6), rel=1e-12)


def test_both_error_models_and_the_comparator_by_hand(gate_a):
    root, settings = gate_a
    models = run_doc(settings, root)["o"]["error_models"]
    v_prompt = float(C) * 1e4 / 100                                        # 14.966 pp^2
    for plan, J in (("plan_a", 6), ("plan_b", 9)):
        v_seed = float(SEED_VARIANCE) / J
        random_ = models["prompts_random"]["vs_theta0"][plan]
        seed = models["seed_only"]["vs_theta0"][plan]
        assert random_["se_pp"] == pytest.approx(math.sqrt(v_seed + v_prompt), rel=1e-12)
        assert random_["mde_pp"] == pytest.approx((Z975 + Z80) * math.sqrt(v_seed + v_prompt), rel=1e-12)
        assert seed["mde_pp"] == pytest.approx((Z975 + Z80) * math.sqrt(v_seed), rel=1e-12)
        comp = models["seed_only"]["comparator_j_vs_j"][plan]
        assert comp["mde_pp"] == pytest.approx((Z975 + Z80) * math.sqrt(2 * v_seed), rel=1e-12)
        assert comp["t_df"] == 2 * J - 2 and seed["t_df"] == J - 1
        comp_random = models["prompts_random"]["comparator_j_vs_j"][plan]
        assert comp_random["se_pp"] == pytest.approx(math.sqrt(2 * v_seed + v_prompt), rel=1e-12)
    assert models["prompts_random"]["vs_theta0"]["plan_a"]["mde_pp"] == pytest.approx(10.9186, abs=1e-3)
    assert models["seed_only"]["vs_theta0"]["plan_a"]["mde_pp"] == pytest.approx(1.3207, abs=1e-3)
    assert models["seed_only"]["comparator_j_vs_j"]["plan_a"]["mde_t_pp"] == pytest.approx(2.0715, abs=1e-3)


def test_the_u8_decider_switch(gate_a):
    root, settings = gate_a
    u8 = run_doc(settings, root)["o"]["u8"]
    assert u8["decider"] == "prompts_random" and u8["opens"] is True and u8["threshold_pp"] == 5.0
    assert u8["decisive_mde_pp"] == pytest.approx(10.9186, abs=1e-3)
    settings["u8_decider"] = "seed_only"
    u8 = run_doc(settings, root)["o"]["u8"]
    assert u8["decider"] == "seed_only" and u8["opens"] is False
    assert u8["decisive_mde_pp"] == pytest.approx(1.3207, abs=1e-3)
    settings["u8_decider"] = "bank_conditional"
    with pytest.raises(s1.Refusal, match="u8_decider"):
        lcheck.run(settings, "f" * 64, root)


def test_the_threshold_is_strict(gate_a):
    root, settings = gate_a
    mde = run_doc(settings, root)["o"]["u8"]["decisive_mde_pp"]
    settings["o_ext_threshold_pp"] = mde
    assert run_doc(settings, root)["o"]["u8"]["opens"] is False                 # "exceeds 5 pp": equal does not open


def test_the_ni_planning_report_by_hand(gate_a):
    root, settings = gate_a
    ni = run_doc(settings, root)["o"]["ni_planning_report_only"]
    assert ni["quantile"] == 0.95 and ni["seeds"] == 6 and ni["decider"] == "prompts_random"
    for P in (100, 500):
        se = math.sqrt(float(SEED_VARIANCE) / 6 + float(C) * 1e4 / P)
        block = ni["by_model"]["prompts_random"][str(P)]
        assert block["se_pp"] == pytest.approx(se, rel=1e-12)
        for tau in (2, 5, 10):
            assert block["p_declared_feasible"][str(tau)] == pytest.approx(N.cdf(tau / se - Z95), rel=1e-12)
        assert block["smallest_tau_o_pp_with_power"] == pytest.approx((Z95 + Z80) * se, rel=1e-12)
    seed_only = ni["by_model"]["seed_only"]["100"]
    assert seed_only["se_pp"] == pytest.approx(math.sqrt(float(SEED_VARIANCE) / 6), rel=1e-12)
    assert ni["by_model"]["prompts_random"]["100"]["smallest_tau_o_pp_with_power"] == pytest.approx(9.6905, abs=1e-3)


def test_tau_l_on_the_synthetic_units(gate_a):
    root, settings = gate_a
    tau = run_doc(settings, root)["tau_l"]
    assert tau["a0_mean_query_loss"] == {"1101": 1.0, "1102": 1.25, "1103": 1.5}
    assert tau["s"] == 0.25 and tau["ddof"] == 1
    assert tau["tau_l"] == pytest.approx(2 * math.sqrt(2) * 0.25, rel=1e-15)
    assert tau["se_6v6"] == pytest.approx(0.25 * math.sqrt(1 / 3), rel=1e-15)
    assert tau["known_answer_check"]["pass"] is True
    assert tau["untuned_mean_query_loss_report_only"] == 2.0
    assert tau["two_df_record"]["df"] == 2


def test_a_known_answer_that_the_data_do_not_give_refuses(gate_a):
    root, settings = gate_a
    s = 0.3
    settings["tau_l"]["known_answer"].update({"s": s, **lcheck.tau_l_numbers_from_s(s)})
    with pytest.raises(s1.Refusal, match="known-answer"):
        lcheck.run(settings, "f" * 64, root)


def test_a_known_answer_off_the_l16_rule_refuses(gate_a):
    root, settings = gate_a
    settings["tau_l"]["known_answer"]["tau_l"] = 2 * 0.25                    # tau_L without the root of two
    with pytest.raises(s1.Refusal, match="L16"):
        lcheck.run(settings, "f" * 64, root)


@pytest.mark.parametrize("reading", ["", "   ", None, 1])
def test_an_empty_f_reading_refuses(gate_a, reading):
    root, settings = gate_a
    settings["f"]["reading"] = reading
    with pytest.raises(s1.Refusal, match="reading of f"):
        lcheck.run(settings, "f" * 64, root)


def test_f_other_than_one_or_missing_refuses(gate_a):
    root, settings = gate_a
    for value in (0.5, 2, True):
        doc = copy.deepcopy(settings)
        doc["f"]["value"] = value
        with pytest.raises(s1.Refusal, match="f = 1"):
            lcheck.run(doc, "f" * 64, root)
    doc = copy.deepcopy(settings)
    del doc["f"]
    with pytest.raises(s1.Refusal, match="reading of f"):
        lcheck.run(doc, "f" * 64, root)


def test_the_mde_must_be_two_sided(gate_a):
    root, settings = gate_a
    settings["mde"]["sides"] = 1
    with pytest.raises(s1.Refusal, match="two-sided"):
        lcheck.run(settings, "f" * 64, root)


def test_a_fifth_or_a_missing_unit_refuses(gate_a):
    root, settings = gate_a
    extra = copy.deepcopy(settings)
    extra["units"]["1104"] = {**extra["units"]["1103"], "seed": 1104}
    with pytest.raises(s1.Refusal, match="exactly the units"):
        lcheck.run(extra, "f" * 64, root)
    missing = copy.deepcopy(settings)
    del missing["units"]["1103"]
    with pytest.raises(s1.Refusal, match="exactly the units"):
        lcheck.run(missing, "f" * 64, root)
    wrong = copy.deepcopy(settings)
    wrong["units"]["1102"]["seed"] = 1105
    with pytest.raises(s1.Refusal, match="allow-list entry 1102"):
        lcheck.run(wrong, "f" * 64, root)


@pytest.mark.parametrize("field", ["complete_sha256", "job_sha256", "summary_sha256", "query_loss_sha256"])
def test_a_file_that_differs_from_its_allow_list_pin_refuses(gate_a, field):
    root, settings = gate_a
    settings["units"]["1102"][field] = "0" * 64
    with pytest.raises(s1.Refusal, match="allow-list pins"):
        lcheck.run(settings, "f" * 64, root)


def test_a_gate_b_unit_path_refuses(gate_a):
    """A unit that passes every other check but sits under a Gate B tree is refused by the path rule."""
    root, settings = gate_a
    src = root / settings["units"]["1102"]["path"]
    gate_b = "gate-b-olmo/retrieved/olmo2-1b-gateb-1102/tree/wave0a/1102-a0-e1-a1"
    shutil.copytree(src, root / gate_b)
    settings["units"]["1102"]["path"] = gate_b
    with pytest.raises(s1.Refusal, match="not in the allowed form"):
        lcheck.run(settings, "f" * 64, root)


def test_a_unit_on_another_recipe_refuses(gate_a):
    root, settings = gate_a
    spec = settings["units"]["1103"]
    job_path = root / spec["path"] / "job.json"
    job = json.loads(job_path.read_bytes())
    job["recipe_sha256"] = fx.RECIPE_S
    job_path.write_bytes(canonical_json(job))
    fx.resettle(settings, root, "1103")
    with pytest.raises(s1.Refusal, match="recipe_sha256"):
        lcheck.run(settings, "f" * 64, root)


def test_a_path_that_leaves_the_data_root_refuses(gate_a):
    root, settings = gate_a
    settings["units"]["1101"]["path"] = "family-probe-olmo2-1b/../family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1"
    with pytest.raises(s1.Refusal, match="allowed form"):
        lcheck.run(settings, "f" * 64, root)


def test_a_missing_file_refuses(gate_a):
    root, settings = gate_a
    (root / settings["units"]["1103"]["path"] / "eval" / "e1" / "query_loss.jsonl").unlink()
    with pytest.raises(s1.Refusal, match="sealed check"):
        lcheck.run(settings, "f" * 64, root)
    (root / settings["units"]["1101"]["path"] / "COMPLETE.json").unlink()
    with pytest.raises(s1.Refusal, match="missing"):
        lcheck.run(settings, "f" * 64, root)


def test_a_file_not_listed_by_complete_json_refuses(gate_a):
    root, settings = gate_a
    folder = root / settings["units"]["1102"]["path"]
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    del marker["files"]["eval/e1/guard.jsonl"]
    data = canonical_json(marker)
    (folder / "COMPLETE.json").write_bytes(data)
    settings["units"]["1102"]["complete_sha256"] = sha256_bytes(data)
    with pytest.raises(s1.Refusal, match="does not list"):
        lcheck.run(settings, "f" * 64, root)


def test_labels_that_disagree_with_summary_json_refuse(gate_a):
    root, settings = gate_a
    spec = settings["units"]["1101"]
    path = root / spec["path"] / "eval" / "e1" / "summary.json"
    summary = json.loads(path.read_bytes())
    summary["overrefusal"]["refusals"] = 5
    path.write_bytes(canonical_json(summary))
    fx.resettle(settings, root, "1101")
    with pytest.raises(s1.Refusal, match="disagree with summary.json"):
        lcheck.run(settings, "f" * 64, root)


def test_a_mean_that_differs_from_summary_json_refuses(gate_a):
    root, settings = gate_a
    spec = settings["units"]["1102"]
    path = root / spec["path"] / "eval" / "e1" / "summary.json"
    summary = json.loads(path.read_bytes())
    summary["query_loss"]["mean"] = 1.2500000000000002
    path.write_bytes(canonical_json(summary))
    fx.resettle(settings, root, "1102")
    with pytest.raises(s1.Refusal, match="mean query loss"):
        lcheck.run(settings, "f" * 64, root)


def test_an_invalid_judge_answer_counts_as_not_refused(gate_a):
    root, settings = gate_a
    spec = settings["units"]["1103"]
    path = root / spec["path"] / "eval" / "e1" / "guard.jsonl"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    for row in rows:
        if row["prompt_id"] == "p030":                       # not refused by seed 1103; an invalid "Yes"
            row.update({"valid": False, "refusal": "Yes"})
    path.write_bytes(b"".join(json.dumps(r, sort_keys=True).encode() + b"\n" for r in rows))
    fx.resettle(settings, root, "1103")
    doc = run_doc(settings, root)
    assert doc["units"]["1103"]["o_refusals"] == 4 and doc["units"]["1103"]["o_invalid"] == 1


def test_different_prompt_or_task_ids_refuse(gate_a):
    root, settings = gate_a
    spec = settings["units"]["1103"]
    path = root / spec["path"] / "eval" / "e1" / "query_loss.jsonl"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[0]["query_id"] = "q-other"
    path.write_bytes(b"".join(json.dumps(r, sort_keys=True).encode() + b"\n" for r in rows))
    fx.resettle(settings, root, "1103")
    with pytest.raises(s1.Refusal, match="same task rows"):
        lcheck.run(settings, "f" * 64, root)


def test_eval_with_another_checkpoint_folder_refuses(gate_a):
    root, settings = gate_a
    (root / settings["units"]["1101"]["path"] / "eval" / "q").mkdir()
    with pytest.raises(s1.Refusal, match="eval/ does not hold exactly"):
        lcheck.run(settings, "f" * 64, root)


def test_only_labels_and_losses_are_read_and_no_text_is_written(gate_a, monkeypatch):
    root, settings = gate_a
    read = []
    original = lc.fields_of

    def spy(data, name, fields, kinds=None):
        read.append((name, tuple(fields)))
        return original(data, name, fields, kinds)

    monkeypatch.setattr(lc, "fields_of", spy)
    data = lcheck.run(settings, "f" * 64, root)
    assert read and all(name.endswith(("guard.jsonl", "query_loss.jsonl")) for name, _ in read)
    assert {fields for _, fields in read} == {("prompt_id", "valid", "refusal"), ("query_id", "loss")}
    assert lc.text_hits(data, fx.SENTINELS) == 0
    assert data == lcheck.run(settings, "f" * 64, root)                   # deterministic


def test_the_command_writes_once_and_prints_no_text(gate_a, tmp_path, monkeypatch, capsys):
    root, settings = gate_a
    path = tmp_path / "limits_check.json"
    path.write_bytes(canonical_json(settings))
    monkeypatch.setattr(lcheck, "SETTINGS_SHA256", sha256_bytes(path.read_bytes()))
    out = tmp_path / "out"
    assert lcheck.main(["--out", str(out), "--data-root", str(root), "--settings", str(path)]) == 0
    printed = capsys.readouterr()
    written = (out / "limits_check.json").read_bytes()
    assert written == lcheck.run(settings, sha256_bytes(path.read_bytes()), root)
    assert lc.text_hits((printed.out + printed.err).encode(), fx.SENTINELS) == 0 and "U8 opens: True" in printed.out
    assert lcheck.main(["--out", str(out), "--data-root", str(root), "--settings", str(path)]) == 2
    assert "not empty" in capsys.readouterr().err


def test_the_command_refuses_another_settings_file_and_absent_units(gate_a, tmp_path, capsys):
    root, settings = gate_a
    path = tmp_path / "other.json"
    path.write_bytes(canonical_json(settings))
    assert lcheck.main(["--out", str(tmp_path / "o1"), "--data-root", str(root), "--settings", str(path)]) == 2
    assert "hash to" in capsys.readouterr().err and not (tmp_path / "o1").exists()
    empty = tmp_path / "empty"
    empty.mkdir()
    assert lcheck.main(["--out", str(tmp_path / "o2"), "--data-root", str(empty)]) == 2      # the real settings
    assert "REFUSED" in capsys.readouterr().err and not (tmp_path / "o2").exists()


# ----- the verifier's added cases (verification items S-4, S-6, S-7, S-8, S-12) -----------------------------------


def test_f_one_needs_all_100_prompts():
    """S-4: f = 1 means all 100 dev over-refusal prompts; units that hold 99 refuse."""
    settings = fx.real_settings("limits_check")
    ids = [f"p{i:03d}" for i in range(99)]
    flags = {n: {p: (False, True) for p in ids} for n in ("untuned", "1101", "1102", "1103")}
    with pytest.raises(s1.Refusal, match="100 over-refusal prompt ids"):
        lcheck.o_block(flags, settings)


def _rewrite_summary(settings, root, name, change):
    spec = settings["units"][name]
    path = root / spec["path"] / "eval" / spec["checkpoint"] / "summary.json"
    summary = json.loads(path.read_bytes())
    change(summary)
    path.write_bytes(canonical_json(summary))
    fx.resettle(settings, root, name)


def test_another_query_bank_refuses(gate_a):
    """S-6: every unit's summary.json must name the pinned task bank."""
    root, settings = gate_a
    _rewrite_summary(settings, root, "1101", lambda s: s["query_loss"].update(query_bank_sha256="0" * 64))
    with pytest.raises(s1.Refusal, match="pinned query bank"):
        lcheck.run(settings, "f" * 64, root)


def test_a_complete_json_mean_that_differs_refuses(gate_a):
    """S-7: the recomputed mean must equal COMPLETE.json's recorded mean too (as tau_l_check.py asserts)."""
    root, settings = gate_a
    spec = settings["units"]["1101"]
    path = root / spec["path"] / "COMPLETE.json"
    marker = json.loads(path.read_bytes())
    marker["evaluation"]["query_loss"]["mean"] = 1.0000000000000002
    data = canonical_json(marker)
    path.write_bytes(data)
    spec["complete_sha256"] = sha256_bytes(data)
    with pytest.raises(s1.Refusal, match="mean query loss"):
        lcheck.run(settings, "f" * 64, root)


def test_an_overrefusal_n_that_differs_refuses(gate_a):
    """S-8: summary.json's overrefusal.n must equal the number of judged over-refusal records."""
    root, settings = gate_a
    _rewrite_summary(settings, root, "1102", lambda s: s["overrefusal"].update(n=101))
    with pytest.raises(s1.Refusal, match="disagree with summary.json"):
        lcheck.run(settings, "f" * 64, root)


def test_a_unit_behind_a_symlink_out_of_the_data_root_refuses(tmp_path):
    """S-12: a unit folder that resolves outside the data root refuses (the path rule alone does not catch it)."""
    outside = tmp_path / "outside"
    settings = fx.build_gate_a(outside)
    root = tmp_path / "data"
    root.mkdir()
    for top in {spec["path"].split("/")[0] for spec in settings["units"].values()}:
        os.symlink(outside / top, root / top)
    with pytest.raises(s1.Refusal, match="leaves the data root"):
        lcheck.run(settings, "f" * 64, root)


def test_the_record_carries_the_recorded_two_df_simulation(gate_a):
    """N-2: W1-16 item 8's simulated failure rates are copied from the settings into the record (report only)."""
    root, settings = gate_a
    record = run_doc(settings, root)["tau_l"]["two_df_record"]
    assert record["simulated_failure_rates_report_only"] == settings["tau_l"]["two_df_simulated"]
    bad = copy.deepcopy(settings)
    bad["tau_l"]["two_df_simulated"]["one_sided_90_bound"].pop("unconditional")
    with pytest.raises(s1.Refusal, match="two_df_simulated"):
        lcheck.run(bad, "f" * 64, root)
