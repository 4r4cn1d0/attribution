"""End-to-end runner on ENGINEERING FIXTURES (tiny random Qwen2, byte codec, '!'-counting
scorer, synthetic rows; CPU). Checks plumbing, completion semantics and evidence verification
only: nothing here is a result."""

from __future__ import annotations

import json
import shutil

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

from experiments.minimal_safety import data, report  # noqa: E402
from experiments.minimal_safety import model as tm  # noqa: E402
from experiments.minimal_safety.common import (read_jsonl, sha256_bytes, sha256_file,  # noqa: E402
                                               write_atomic, write_json)
from experiments.minimal_safety.run import Calibration, RunError, execute  # noqa: E402

ARM = "remove_fixture2"
STAGES = {"load_model", "load_scorer", "tokenize", "input_classifier", "init_adapter", "train_short",
          "eval_short", "train_continue", "eval_long", "attribution", "eval_base"}
EFFECT_WORDS = ("significant", "reduced", "reduces", "improve", "effective", "safer", "works")


class ManualClock:
    """Deterministic fake clock that moves only when a test moves it."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _copy(completed_run, tmp_path):
    config, source, _ = completed_run
    run_dir = tmp_path / "run"
    shutil.copytree(source, run_dir)
    return config, run_dir


def test_end_to_end_fixture_run_is_complete_and_traceable(completed_run):
    config, run_dir, summary = completed_run
    assert summary["status"] == "complete", (summary["stop_reason"], summary["problems"])
    assert summary["termination"] == "runner ended" and summary["problems"] == []
    assert summary["recovered_fragments"] == [] and summary["identity"]["frozen_verified"]
    assert json.loads((run_dir / report.END_FILE).read_text())["stop_reason"] is None
    assert summary["conclusion"] == report.CONCLUSION
    assert {(r["seed"], r["checkpoint"]) for r in summary["comparisons"]["rows"]} == {
        (1, "short"), (1, "long"), (2, "short"), (2, "long")}
    assert all(v["identical_across_arms"] for v in summary["init_identity"].values())
    for row in summary["comparisons"]["rows"]:
        if row["data_identical"]:  # same data, initial adapter and fresh optimizer on CPU
            assert row["adapters_identical"] is True
            assert row["identical_completions"] == row["compared_completions"]

    plan = json.loads((run_dir / "frozen" / "plan.json").read_text())
    removed = set(plan["removal_uids"])
    for seed in config["train"]["seeds"]:
        for arm in ("a0", ARM):
            stream = plan["streams"][str(seed)][arm]["uids"]
            steps = read_jsonl(run_dir / "steps" / f"{seed}-{arm}.jsonl")
            assert [s["uid"] for s in steps] == stream and [s["step"] for s in steps] == [1, 2, 3, 4]
            if arm != "a0":
                assert not removed & {s["uid"] for s in steps}
    checkpoints = {(c["seed"], c["arm"], c["checkpoint"]): c for c in summary["checkpoints"]}
    for seed in config["train"]["seeds"]:
        for arm in ("a0", ARM):
            short, long_ = checkpoints[(seed, arm, "short")], checkpoints[(seed, arm, "long")]
            assert long_["uids"][:2] == short["uids"] and len(long_["uids"]) == 4  # short inside long
            assert short["fingerprint"] != long_["fingerprint"]
            assert short["init_fingerprint"] == checkpoints[(seed, "init", "init")]["fingerprint"]
            for c in (short, long_):
                assert sha256_file(run_dir / c["file"]) == c["sha256"]

    for item in summary["attribution"]:
        assert -1.0 <= item["cosine_of_means"] <= 1.0 and item["definition"] == tm.COSINE_DEFINITION
        assert set(item["group_uids"]) == removed and len(item["query_uids"]) == 2
    evals = {(str(e["seed"]), e["arm"], e["checkpoint"]) for e in summary["evals"]}
    assert ("base", "base", "base") in evals and len(evals) == 9
    for e in summary["evals"]:
        cases = read_jsonl(run_dir / e["file"])
        assert [c["role"] for c in cases] == ["eval", "eval", "holdout", "holdout"]
        assert all(0.0 <= c["p_toxic"] <= 1.0 and c["new_tokens"] <= 4 for c in cases)
    ledger = read_jsonl(run_dir / "ledger.jsonl")
    assert {r["stage"] for r in ledger} == STAGES and all(r["status"] == "ok" for r in ledger)
    costs = summary["costs"]
    arm_costs = costs["per_arm"][f"1/{ARM}"]
    assert arm_costs["full_run_train"] == pytest.approx(arm_costs["train_short"] + arm_costs["train_continue"])
    assert costs["stopped"] == [] and all(v["init_adapter"] is not None and v["attribution"] is not None
                                          for v in costs["per_seed"].values())
    blind = read_jsonl(run_dir / "audit" / "blind.jsonl")
    assert blind and all("arm" not in b and "seed" not in b and "p_toxic" not in b for b in blind)
    text = (run_dir / "report.md").read_text()
    assert text.startswith("# Minimal safety calibration")
    assert "| seed | adapter init | attribution (a0 long) |" in text  # per-seed costs rendered
    assert report.CONCLUSION.lower() in text.lower()
    assert not any(word in text.lower() for word in EFFECT_WORDS)
    assert json.loads((run_dir / "status.json").read_text())["status"] == "complete"
    again = report.summarize(run_dir)  # a later re-summary reaches the same verdict
    assert (again["status"], again["termination"], again["problems"]) == ("complete", "runner ended", [])


def _records(run_dir, edit):
    """Rewrite records.jsonl through edit(record) -> record, or None to drop it."""
    path = run_dir / "records.jsonl"
    rows = [r for r in map(edit, read_jsonl(path)) if r is not None]
    write_atomic(path, "".join(json.dumps(r) + "\n" for r in rows).encode())


def _is(record, **keys):
    return all(record.get(k) == v for k, v in keys.items())


def _drop(**keys):
    return lambda run_dir: _records(run_dir, lambda r: None if _is(r, **keys) else r)


def _set(fields, **keys):
    return lambda run_dir: _records(run_dir, lambda r: {**r, **fields} if _is(r, **keys) else r)


def _swap_a_prompt(run_dir):
    """Evaluate one arm on a different prompt set, with a consistent file hash."""
    keys = {"kind": "eval", "seed": 1, "arm": ARM, "checkpoint": "short"}
    record = next(r for r in read_jsonl(run_dir / "records.jsonl") if _is(r, **keys))
    cases = read_jsonl(run_dir / record["file"])
    cases[0]["uid"] = "ref:99999"
    payload = "".join(json.dumps(c) + "\n" for c in cases).encode()
    write_atomic(run_dir / record["file"], payload)
    digests = {c["uid"]: sha256_bytes(c["completion"].encode())[:16] for c in cases}
    _set({"sha256": sha256_bytes(payload), "completion_digests": digests}, **keys)(run_dir)


def _retrain_other_row(run_dir):
    path = run_dir / "steps" / "1-a0.jsonl"
    steps = read_jsonl(path)
    steps[0]["uid"] = "train:99999"
    write_atomic(path, "".join(json.dumps(s) + "\n" for s in steps).encode())


def _edit_plan(run_dir):
    path = run_dir / "frozen" / "plan.json"
    write_json(path, {**json.loads(path.read_text()), "audit_shuffle_seed": 999})


TAMPERS = {  # name: (tamper, problem prefix, (seed, checkpoint) that must not be compared)
    "missing checkpoint record": (_drop(kind="checkpoint", seed=1, arm="a0", checkpoint="short"),
                                  "1/a0/short", ("1", "short")),
    "equal wrong steps": (_set({"step": 3}, kind="eval", seed=1, checkpoint="short"),
                          "1/a0/short", ("1", "short")),
    "different prompt set": (_swap_a_prompt, f"1/{ARM}/short", ("1", "short")),
    "trained other rows": (_retrain_other_row, "1/a0/short", ("1", "short")),
    "other initial adapter": (_set({"init_fingerprint": "0" * 64}, kind="arm_start", seed=2, arm=ARM),
                              f"2/{ARM}/short", ("2", "long")),
    "missing initial adapter": (_drop(kind="checkpoint", seed=2, arm="init"), "2/init", ("2", "short")),
    "missing attribution": (_drop(kind="attribution", seed=1), "1/attribution", None),
    "missing input scores": (_drop(kind="content_scores"), "input classifier", None),
    "missing tokenization": (_drop(kind="tokenization"), "tokenization", None),
    "altered frozen plan": (_edit_plan, "frozen/plan.json", None),
}


@pytest.mark.parametrize("name", sorted(TAMPERS))
def test_missing_wrong_or_altered_evidence_is_incomplete_and_not_compared(name, completed_run, tmp_path):
    _, run_dir = _copy(completed_run, tmp_path)
    tamper, prefix, pair = TAMPERS[name]
    tamper(run_dir)
    summary = report.summarize(run_dir)
    assert summary["status"] == "incomplete" and summary["stop_reason"] is None
    assert any(p.startswith(prefix) for p in summary["problems"]), summary["problems"]
    if pair is not None:
        assert pair not in {(str(r["seed"]), r["checkpoint"]) for r in summary["comparisons"]["rows"]}
    if name == "altered frozen plan":
        assert not summary["identity"]["frozen_verified"]
        assert summary["comparisons"]["rows"] == [] and summary["evals"] == []
        assert summary["audit"]["items"] == 0 and summary["audit"]["cases"] == 0
    assert summary["conclusion"] == report.CONCLUSION


def test_caught_interrupt_ends_the_runner_incomplete_with_spent_cost_visible(
        tmp_path, prepared, tiny_loader, monkeypatch):
    config, prep_dir, digest = prepared
    real, calls = tm.train_step, []

    def interrupt_third_step(*args, **kwargs):
        calls.append(1)
        if len(calls) == 3:  # seed 1, a0: the first step after the short checkpoint
            raise KeyboardInterrupt
        return real(*args, **kwargs)

    monkeypatch.setattr(tm, "train_step", interrupt_third_step)
    run_dir = tmp_path / "run"
    summary = execute(config, prep_dir, run_dir, digest, tiny_loader)
    assert summary["status"] == "incomplete" and summary["termination"] == "runner ended"
    assert summary["stop_reason"] == "interrupted (KeyboardInterrupt)"
    stopped = summary["costs"]["stopped"]
    assert [(r["stage"], r["seed"], r["arm"], r["status"], r["first_step"], r["last_step"])
            for r in stopped] == [("train_continue", 1, "a0", "interrupted", 3, None)]
    assert stopped[0]["last_item"] == "train_continue step 3 (seed 1, a0)" and stopped[0]["seconds"] >= 0
    a0 = summary["costs"]["per_arm"]["1/a0"]
    assert a0["train_short"] is not None and a0["train_continue"] is None and a0["full_run"] is None
    assert [s["step"] for s in read_jsonl(run_dir / "steps" / "1-a0.jsonl")] == [1, 2]
    assert not any(p.startswith("1/a0/short") for p in summary["problems"])  # finished units verify
    assert any(p.startswith("1/a0/long") for p in summary["problems"])
    assert summary["comparisons"]["rows"] == []
    text = (run_dir / "report.md").read_text()
    assert "Spent on stopped stages" in text and "train_continue (seed 1, arm a0): interrupted" in text
    assert json.loads((run_dir / "status.json").read_text())["status"] == "incomplete"


def test_killed_run_is_recovered_incomplete_and_torn_logs_are_never_silently_accepted(
        completed_run, tmp_path):
    _, run_dir = _copy(completed_run, tmp_path)
    end = (run_dir / report.END_FILE).read_bytes()
    (run_dir / report.END_FILE).unlink()  # killed before the runner could record its end
    write_json(run_dir / "status.json", {"status": "running", "stage": "eval_base", "elapsed_s": 12.0})
    for name in ("records.jsonl", "ledger.jsonl"):
        with open(run_dir / name, "ab") as handle:
            handle.write(b'{"kind": "eval", "seed": "ba')  # an append cut off by the kill
    summary = report.summarize(run_dir)
    assert summary["status"] == "incomplete" and summary["stop_reason"].startswith("interrupted")
    assert summary["termination"].startswith("recovered")
    assert sorted(r["file"] for r in summary["recovered_fragments"]) == ["ledger.jsonl", "records.jsonl"]
    assert summary["problems"] == [] and len(summary["comparisons"]["rows"]) == 4
    assert "PARTIAL RUN" in summary["comparisons"]["basis"]
    (run_dir / report.END_FILE).write_bytes(end)  # once the runner ended, logs must be intact
    strict = report.summarize(run_dir)
    assert strict["status"] == "incomplete" and strict["recovered_fragments"] == []
    assert any("corrupt log records.jsonl" in p and "unterminated" in p for p in strict["problems"])
    assert strict["comparisons"]["rows"] == []
    with open(run_dir / "records.jsonl", "ab") as handle:
        handle.write(b'"x": 1}\nNOT_JSON\n')  # newline-terminated corruption: never recoverable
    (run_dir / report.END_FILE).unlink()
    assert any("corrupt log records.jsonl" in p for p in report.summarize(run_dir)["problems"])


def test_cap_stops_before_an_arm_and_only_matched_pairs_are_compared(
        tmp_path, prepared, tiny_loader, monkeypatch):
    config, prep_dir, digest = prepared
    clock, train_arm = ManualClock(), Calibration.train_arm

    def hundred_seconds_per_arm(self, *args):
        step = train_arm(self, *args)
        clock.now += 100.0
        return step

    monkeypatch.setattr(Calibration, "train_arm", hundred_seconds_per_arm)
    capped = json.loads(json.dumps(config))
    capped["caps"]["wall_seconds"] = 250  # seed 1 fits (200 s); seed 2's a0 would end at 300 s
    summary = execute(capped, prep_dir, tmp_path / "capped", digest, tiny_loader, clock=clock)
    assert summary["status"] == "incomplete" and summary["stop_reason"].startswith("cap:")
    assert "seed 2 arm a0" in summary["stop_reason"] and "predicted 100.0s" in summary["stop_reason"]
    assert {(r["seed"], r["checkpoint"]) for r in summary["comparisons"]["rows"]} == {
        (1, "short"), (1, "long")}
    assert {(u["seed"], u["checkpoint"]) for u in summary["comparisons"]["unmatched"]} == {
        (2, "short"), (2, "long")}
    assert not (tmp_path / "capped" / "steps" / "2-a0.jsonl").exists()  # no partial arm started
    assert any(p.startswith("base/base/base") for p in summary["problems"])
    assert json.loads((tmp_path / "capped" / "status.json").read_text())["status"] == "incomplete"
    assert summary["conclusion"] == report.CONCLUSION


def test_final_check_makes_a_run_whose_last_unit_overran_the_cap_incomplete(
        tmp_path, prepared, tiny_loader, monkeypatch):
    config, prep_dir, digest = prepared
    clock = ManualClock()
    # Stand-in for a last unit that cannot be interrupted and ends far past the 600 s cap.
    monkeypatch.setattr(Calibration, "run", lambda self: setattr(clock, "now", 10_000.0))
    summary = execute(config, prep_dir, tmp_path / "run", digest, tiny_loader, clock=clock)
    assert summary["status"] == "incomplete" and summary["termination"] == "runner ended"
    assert summary["stop_reason"].startswith("cap:") and "completion" in summary["stop_reason"]
    assert any("over the 600 s wall cap" in p for p in summary["problems"])


def test_summary_rechecks_both_caps_from_the_recorded_evidence(completed_run, tmp_path):
    config, run_dir = _copy(completed_run, tmp_path)
    end = json.loads((run_dir / report.END_FILE).read_text())
    write_json(run_dir / report.END_FILE, {**end, "elapsed_s": config["caps"]["wall_seconds"] + 1.0})
    over_time = report.summarize(run_dir)
    assert over_time["status"] == "incomplete" and any("wall cap" in p for p in over_time["problems"])
    write_json(run_dir / report.END_FILE, end)
    with open(run_dir / "padding.bin", "wb") as handle:
        handle.truncate(config["caps"]["output_bytes"] + 1)  # sparse file: no real disk use
    over_size = report.summarize(run_dir)
    assert over_size["status"] == "incomplete" and any("byte cap" in p for p in over_size["problems"])


def test_unfrozen_or_reused_inputs_are_refused(tmp_path, prepared, tiny_loader):
    config, prep_dir, digest = prepared
    with pytest.raises(data.DataError, match="pinned"):
        execute(config, prep_dir, tmp_path / "a", "0" * 64, tiny_loader)
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "previous.txt").write_text("an earlier run")
    with pytest.raises(RunError, match="never resumed"):
        execute(config, prep_dir, tmp_path / "b", digest, tiny_loader)
    other = json.loads(json.dumps(config))
    other["design"]["benign_holdout"] = 3
    with pytest.raises(RunError, match="different dataset/design"):
        execute(other, prep_dir, tmp_path / "c", digest, tiny_loader)
