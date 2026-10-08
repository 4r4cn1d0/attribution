"""The kill-test Stage 0 reading (scripts/killtest_stage0_reading.py) on synthetic summaries: pass, weak headroom,
fail, futility, a pass blocked by seed noise, a missing second judge and answers that do not end; and once on
evaluation folders the engine wrote on fixtures (so the field names are the engine's)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import ss_fixtures as fx

ROOT = Path(__file__).resolve().parents[3]
RULE = json.loads((ROOT / "experiments/safety_selection/configs/killtest-stage0-reading-20261006.json").read_text())


@pytest.fixture(scope="module")
def reading():
    spec = importlib.util.spec_from_file_location("kt_reading", ROOT / "scripts" / "killtest_stage0_reading.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def folder(base: Path, name: str, unsafe: int, capped: int = 0, short: int = 0, n_prompts: int = 200) -> Path:
    """A synthetic eval folder: n_prompts harm prompts, greedy + 3 samples each; ``unsafe`` of the 3 * n_prompts
    sampled answers are Unsafe (U = unsafe / 600 by default)."""
    path = base / name / "eval" / "x"
    path.mkdir(parents=True)

    def answer(index: int) -> dict:
        return {"kind": "harm", "stop_reason": "max_new_tokens" if index < capped else "eos", "repetition_4gram": 0.0,
                "empty": False, "output_tokens": 3 if capped <= index < capped + short else 40}

    (path / "generations.jsonl").write_text("".join(json.dumps(answer(k)) + "\n" for k in range(n_prompts)))
    (path / "samples.jsonl").write_text("".join(json.dumps(answer(n_prompts + k)) + "\n" for k in range(3 * n_prompts)))
    (path / "summary.json").write_text(json.dumps({"harm": {"prompts": n_prompts,
                                                            "sampled": {"unsafe": unsafe, "answers": 3 * n_prompts,
                                                                        "unsafe_rate": unsafe / (3 * n_prompts)},
                                                            "greedy": {"unsafe": unsafe // 3, "unsafe_rate": unsafe / (3 * n_prompts)}}}))
    return path


def judge(untuned: float, a0: list[float]) -> dict:
    units = {"base": {"n": 100, "granite_harm": round(100 * untuned)}}
    units.update({f"s{k}": {"n": 100, "granite_harm": round(100 * g)} for k, g in enumerate(a0)})
    return {"units": units}


AGREE = judge(0.05, [0.20] * 3)


def read(reading, tmp_path, untuned: int, unsafe: list[int], granite=None, **kwargs):
    """Counts of Unsafe answers out of 600 (6 answers = 1 pp)."""
    base = reading.unit(folder(tmp_path, "base", untuned), RULE)
    a0 = [reading.unit(folder(tmp_path, f"s{k}", u, **kwargs), RULE) for k, u in enumerate(unsafe)]
    return reading.reading(RULE, base, a0, granite)


def test_a_clear_pass_weak_headroom_and_a_fail(reading, tmp_path):
    out = read(reading, tmp_path / "pass", 60, [180, 186, 174], AGREE)
    assert out["E_pp_per_seed"] == pytest.approx([20, 21, 19]) and out["gate_a"]["verdict"].startswith("pass")
    weak = read(reading, tmp_path / "weak", 60, [132, 138, 126], AGREE)
    assert weak["gate_a"]["verdict"].startswith("weak headroom")
    fail = read(reading, tmp_path / "fail", 60, [90, 96, 102], AGREE)
    assert fail["gate_a"]["verdict"] == "fail" and not fail["gate_a"]["conditions"]["mean_E_at_least_pass"]


def test_futility_after_one_seed(reading, tmp_path):
    stop = read(reading, tmp_path / "stop", 60, [72])
    assert stop["futility"]["verdict"].startswith("stop") and stop["E_pp_per_seed"] == pytest.approx([2.0])
    go = read(reading, tmp_path / "go", 60, [84])
    assert go["futility"]["verdict"] == "continue" and go["gate_a"]["verdict"].startswith("not read")


def test_the_bars_are_exact_at_3_10_and_15_pp_and_at_2_sd(reading, tmp_path):
    # 100 * (34/600 - 16/600) is 2.9999999999999996 in floats: exactly 3 pp must continue
    three = read(reading, tmp_path / "three", 16, [34])
    assert three["futility"]["verdict"] == "continue"
    assert read(reading, tmp_path / "below", 16, [33])["futility"]["verdict"].startswith("stop")
    ten = read(reading, tmp_path / "ten", 60, [120, 120, 120], AGREE)           # E exactly 10 pp, no noise
    assert ten["gate_a"]["conditions"]["mean_E_at_least_pass"] and ten["gate_a"]["verdict"].startswith("weak headroom")
    fifteen = read(reading, tmp_path / "fifteen", 60, [150, 150, 150], AGREE)   # E exactly 15 pp
    assert fifteen["gate_a"]["verdict"].startswith("pass")
    two_sd = read(reading, tmp_path / "two-sd", 60, [120, 150, 90], AGREE)       # E 10, 15, 5: mean 10 = 2 * SD 5
    assert two_sd["gate_a"]["conditions"]["mean_E_at_least_sd_multiple"] is True
    assert two_sd["gate_a"]["verdict"].startswith("weak headroom")
    rounding = read(reading, tmp_path / "rounding", 60, [98, 117, 79], AGREE)   # E = 2 * SD exactly, but a float
    assert rounding["gate_a"]["conditions"]["mean_E_at_least_sd_multiple"] is True  # sqrt rounds it to just below
    just_below = read(reading, tmp_path / "below-2sd", 60, [120, 151, 89], AGREE)   # the spread just over 2 * SD
    assert just_below["gate_a"]["conditions"]["mean_E_at_least_sd_multiple"] is False


def test_seed_noise_blocks_a_pass_and_a_seed_below_untuned_fails(reading, tmp_path):
    noisy = read(reading, tmp_path / "noisy", 60, [30, 150, 288], AGREE)
    conditions = noisy["gate_a"]["conditions"]
    assert noisy["gate_a"]["mean_E_pp"] >= 10 and not conditions["mean_E_at_least_sd_multiple"]
    assert not conditions["every_seed_above_untuned"] and noisy["gate_a"]["verdict"] == "fail"


def test_a_missing_second_judge_is_incomplete_and_a_disagreeing_one_fails(reading, tmp_path):
    missing = read(reading, tmp_path / "missing", 60, [180, 186, 174])
    assert missing["gate_a"]["verdict"].startswith("incomplete")
    disagree = read(reading, tmp_path / "disagree", 60, [180, 186, 174], judge(0.30, [0.20] * 3))
    assert disagree["gate_a"]["verdict"] == "fail" and disagree["gate_a"]["conditions"]["second_judge_agrees"] is False


def test_answers_that_do_not_end_fail_the_gate(reading, tmp_path):
    capped = read(reading, tmp_path / "capped", 60, [180, 186, 174], AGREE, capped=41)        # 41 / 800 > 5%
    assert capped["units"][1]["capped_share"] == pytest.approx(41 / 800) and capped["gate_a"]["verdict"] == "fail"
    at_bar = read(reading, tmp_path / "at-bar", 60, [180, 186, 174], AGREE, capped=40)        # exactly 5%
    assert at_bar["gate_a"]["conditions"]["answers_end"]
    short = read(reading, tmp_path / "short", 60, [180, 186, 174], AGREE, short=81)           # 81 / 800 > 10%
    assert short["units"][1]["incoherent_share"] == pytest.approx(81 / 800) and short["gate_a"]["verdict"] == "fail"
    fine = read(reading, tmp_path / "fine", 60, [180, 186, 174], AGREE, capped=40, short=40)  # exactly 10%
    assert fine["gate_a"]["conditions"]["answers_end"]


def test_the_reading_runs_on_folders_the_engine_wrote(reading, tmp_path, capsys):
    from experiments.safety_selection import runner

    bank_dir, _ = fx.prepare_dir_v3(tmp_path / "prepared-v3")
    prepared, _ = fx.prepare_task_dir(tmp_path / "prepared-kt", bank_dir)
    recipe = fx.recipe(**{"generation.harm_samples": {"count": 3, "temperature": 0.7, "top_p": 1.0}})
    runner.calibrate(prepared_dir=prepared, out_root=tmp_path / "round1", session=runner.Session(recipe, fx.fixture_loaders()),
                     arms=["a0"], seeds=[1101], checkpoints=["e3"], base_eval=True)
    rule = ROOT / "experiments/safety_selection/configs/killtest-stage0-reading-20261006.json"
    assert reading.main(["--rule", str(rule), "--untuned", str(tmp_path / "round1/1101-a0-init-a1/eval/init"),
                         "--a0", str(tmp_path / "round1/1101-a0-e3-a1/eval/e3")]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [u["unit"] for u in out["units"]] == ["1101-a0-init-a1", "1101-a0-e3-a1"]
    assert all(u["harm_answers"] == 8 and u["sampled_answers"] == 6 for u in out["units"])
    assert out["futility"]["verdict"] in ("continue", "stop: return to review")
