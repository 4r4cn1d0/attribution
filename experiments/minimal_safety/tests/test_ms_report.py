"""Ledger caps, strict and recovering log parsing, cost accounting, matched comparisons and the
blind audit on ENGINEERING FIXTURE records (stdlib only): wrong-step, different-prompt or
missing evaluations never yield comparisons, stopped stages count as spent time only, and no
conclusion is ever generated. Whole-run verification is tested on real tiny runs in
test_ms_run.py."""

from __future__ import annotations

import json

import pytest

from experiments.minimal_safety import report
from experiments.minimal_safety.common import read_jsonl, recover_jsonl, sha256_bytes, write_atomic
from experiments.minimal_safety.ledger import CapExceeded, Ledger

ARMS = ["a0", "rm"]


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_ledger_stage_records_sync_failures_interrupts_and_never_starts_past_the_cap(tmp_path):
    clock, syncs = Clock(), []
    ledger = Ledger(tmp_path, 100, 10**6, clock=clock, sync=lambda: syncs.append(clock.now))
    with ledger.stage("train_short", seed=1, arm="a0") as info:
        clock.now = 4.0
        info["steps"] = 2
    with pytest.raises(RuntimeError):
        with ledger.stage("eval_short", seed=1, arm="a0"):
            clock.now = 5.5
            raise RuntimeError("fixture failure")
    with pytest.raises(KeyboardInterrupt):
        with ledger.stage("train_continue", seed=1, arm="a0") as info:
            ledger.check(0.0, "train_continue step 3", outputs=False)
            info["last_step"] = 3
            clock.now = 7.0
            raise KeyboardInterrupt
    clock.now = 101.0
    with pytest.raises(CapExceeded, match="stage eval_long"):
        with ledger.stage("eval_long", seed=1, arm="a0"):
            pass  # never reached: the entry check raises first and nothing is recorded
    rows = read_jsonl(tmp_path / "ledger.jsonl")
    assert [(r["stage"], r["status"], r["seconds"]) for r in rows] == [
        ("train_short", "ok", 4.0), ("eval_short", "error", 1.5), ("train_continue", "interrupted", 1.5)]
    assert rows[0]["steps"] == 2 and "fixture failure" in rows[1]["error"] and rows[2]["last_step"] == 3
    assert "last_item" not in rows[0] and rows[1]["last_item"] == "stage eval_short"
    assert rows[2]["last_item"] == "train_continue step 3"  # where the interrupted stage was
    assert syncs == [0.0, 4.0, 4.0, 5.5, 5.5, 7.0]  # a barrier before reading the clock at both ends


def test_ledger_caps_wall_time_with_prediction_and_output_size(tmp_path):
    clock = Clock()
    ledger = Ledger(tmp_path, 100, 1000, clock=clock)
    clock.now = 60.0
    ledger.check(39.0, "fits")
    with pytest.raises(CapExceeded, match="predicted"):
        ledger.check(41.0, "next arm")  # never start work the cap cannot accommodate
    clock.now = 101.0
    with pytest.raises(CapExceeded, match="wall cap"):
        ledger.check(0.0, "token", outputs=False)  # fine-grained checks still enforce the wall cap
    clock.now = 0.0
    (tmp_path / "big.bin").write_bytes(b"x" * 2000)
    ledger.check(0.0, "token", outputs=False)  # skips only the directory walk
    with pytest.raises(CapExceeded, match="output cap"):
        ledger.check(0.0, "save")


def test_logs_parse_strictly_and_only_recovery_drops_an_unterminated_final_fragment(tmp_path):
    path = tmp_path / "log.jsonl"
    path.write_bytes(b'{"kind": "ok"}\nNOT_JSON\n')  # a newline-terminated corrupt final line
    for reader in (read_jsonl, recover_jsonl):
        with pytest.raises(ValueError, match="line 2"):
            reader(path)
    path.write_bytes(b'{"kind": "ok"}\n\n{"kind": "ok"}\n')
    with pytest.raises(ValueError, match="line 2"):
        read_jsonl(path)  # blank lines are not skipped either
    path.write_bytes(b'{"kind": "ok"}\n[1, 2]\n')
    with pytest.raises(ValueError, match="not a JSON object"):
        read_jsonl(path)
    torn = '{"kind": "ok"}\n'.encode() + '{"text": "é'.encode()[:-1]  # cut inside a UTF-8 character
    path.write_bytes(torn)
    with pytest.raises(ValueError, match="unterminated"):
        read_jsonl(path)
    rows, fragment = recover_jsonl(path)
    assert rows == [{"kind": "ok"}] and fragment == '{"text": "é'.encode()[:-1]
    missing = tmp_path / "missing.jsonl"
    assert read_jsonl(missing) == [] and recover_jsonl(missing) == ([], b"")


def _row(stage, seconds, seed=None, arm=None, status="ok", **extra):
    return {"stage": stage, "seed": seed, "arm": arm, "status": status, "seconds": seconds,
            "end_s": 0.0, **extra}


def test_costs_are_incremental_and_stopped_stages_are_spent_not_completed():
    plan = {"seeds": [1], "arms": ARMS, "long_steps": 4}
    ledger = [_row("load_model", 5.0), _row("init_adapter", 0.5, 1),
              _row("train_short", 2.0, 1, "a0"), _row("eval_short", 3.0, 1, "a0"),
              _row("train_continue", 6.0, 1, "a0"), _row("eval_long", 3.0, 1, "a0"),
              _row("attribution", 1.5, 1, "a0"), _row("train_short", 2.5, 1, "rm"),
              _row("eval_short", 3.0, 1, "rm"), _row("train_continue", 6.5, 1, "rm"),
              _row("eval_long", 9.0, 1, "rm", status="cap", error="CapExceeded: fixture")]
    ledger[-1]["end_s"] = 42.0
    costs = report.stage_costs(ledger, plan)
    a0, rm = costs["per_arm"]["1/a0"], costs["per_arm"]["1/rm"]
    assert a0["full_run_train"] == 8.0  # 2 + 6: steps 1..4 once, short eval excluded
    assert a0["full_run"] == 11.0 and a0["selector_path"] == 14.0 and a0["seconds_per_step"] == 2.0
    assert rm["full_run_train"] == 9.0 and rm["eval_long"] is None
    assert rm["full_run"] is None and rm["selector_path"] is None  # incomplete: no total
    assert costs["per_seed"]["1"] == {"init_adapter": 0.5, "attribution": 1.5}
    assert costs["one_off"]["load_model"] == 5.0
    assert [(r["stage"], r["status"], r["seconds"]) for r in costs["stopped"]] == [
        ("eval_long", "cap", 9.0)] and costs["stopped_seconds"] == 9.0
    assert costs["sum_of_stage_seconds"] == 42.0 and costs["outside_stages_s"] == 0.0


def _plan():
    exposed = {"a0": {"removed_seen": {"short": 1, "long": 1}}, "first_divergence_step": 2}
    unexposed = {"a0": {"removed_seen": {"short": 0, "long": 0}}, "first_divergence_step": None}
    return {"arms": ARMS, "seeds": [1, 2], "short_steps": 2, "long_steps": 4,
            "streams": {"1": exposed, "2": unexposed}}


def _ev(seed, arm, ckpt, step, p_toxic, uids=("ref:00001", "train:00009")):
    return {"kind": "eval", "seed": seed, "arm": arm, "checkpoint": ckpt, "step": step,
            "toxic": {"n": 1, "proxy_rate": float(p_toxic >= 0.5), "mean_p_toxic": p_toxic},
            "benign": {"mean_nll": 1.0, "refusal_flags": 0}, "toxic_ref_nll_mean": 2.0,
            "completion_digests": {u: sha256_bytes(f"{arm} {u}".encode())[:16] for u in uids}}


def test_only_planned_step_same_prompt_pairs_are_compared():
    evals = {(str(s), arm, ckpt): _ev(s, arm, ckpt, step, 0.9 if arm == "a0" else 0.1)
             for s in (1, 2) for arm in ARMS for ckpt, step in (("short", 2), ("long", 4))}
    evals[("1", "a0", "short")]["step"] = evals[("1", "rm", "short")]["step"] = 3  # equal, WRONG
    evals[("2", "rm", "short")] = _ev(2, "rm", "short", 2, 0.1, uids=("ref:00002", "train:00009"))
    del evals[("2", "rm", "long")]
    prints = {k: "same adapter" for k in evals}
    rows, unmatched = report.matched_comparisons(evals, _plan(), prints)
    assert [(r["seed"], r["checkpoint"]) for r in rows] == [(1, "long")]
    row = rows[0]  # a dramatic FIXTURE difference is still only a described number
    assert row["delta_toxic_proxy_rate"] == -1.0 and row["sign"] == "rm minus a0"
    assert row["identical_completions"] == 0 and row["data_identical"] is False
    reasons = {(u["seed"], u["checkpoint"]): " ".join(u["reasons"]) for u in unmatched}
    assert "step 3, planned 2" in reasons[(1, "short")]
    assert "different prompts" in reasons[(2, "short")]
    assert "rm has no verified evaluation" in reasons[(2, "long")]


def test_data_identical_pairs_report_whether_their_adapters_match():
    evals = {("2", arm, "short"): _ev(2, arm, "short", 2, 0.5) for arm in ARMS}
    plan = {**_plan(), "seeds": [2]}
    rows, _ = report.matched_comparisons(evals, plan, {("2", "a0", "short"): "x",
                                                       ("2", "rm", "short"): "y"})
    assert rows[0]["data_identical"] is True and rows[0]["adapters_identical"] is False


def test_blind_audit_hides_arm_seed_and_scores(tmp_path):
    records = []
    for seed, arm, completion in ((1, "a0", "toxic fixture"), (1, "rm", "calm fixture"),
                                  (2, "a0", "toxic fixture")):
        cases = [{"uid": "ref:00001", "role": "eval", "prompt": "fixture toxic prompt",
                  "completion": completion, "p_toxic": 0.9, "toxic_flag": True,
                  "refusal_flag": False, "copy_flag": False, "empty": False, "stopped": True,
                  "new_tokens": 3}]
        rel = f"completions/{seed}-{arm}-short.jsonl"
        write_atomic(tmp_path / rel, "".join(json.dumps(c) + "\n" for c in cases).encode())
        records.append({"seed": seed, "arm": arm, "checkpoint": "short", "step": 2, "file": rel})
    audit = report.export_audit(tmp_path, records, 3)
    blind = read_jsonl(tmp_path / "audit" / "blind.jsonl")
    mapping = read_jsonl(tmp_path / "audit" / "mapping.jsonl")
    assert audit["items"] == len(blind) == 2 and audit["cases"] == 3  # unique (prompt, completion)
    assert all(set(item) == {"audit_id", "prompt", "completion", "label_toxic", "label_refusal",
                             "label_prompt_copy", "notes"} for item in blind)
    assert {c["arm"] for m in mapping for c in m["cases"]} == set(ARMS)
