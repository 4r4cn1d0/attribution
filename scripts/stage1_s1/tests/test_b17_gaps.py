"""B17 fix round, on ENGINEERING FIXTURES: tests that close the gaps the B17 verification found (notes/B17-verify.md,
S1, S2, S4 and S5). Each test kills one or more mutants that survived the first suite: the pairing of answers with
their prompts and seeds, the batch sizes, the device barrier of the lean ledger, the training time in the lean wall
limit, unmapped stages, the scan lists, the sign of the process age, JSON-escaped texts in readable files, and the
edit-arm fingerprint rule. None of these numbers is a scientific result."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout

import pytest

import b17_support as bs

lej = bs.lej
fx = bs.fx
s1 = bs.s1

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import canonical_json, ids_sha256  # noqa: E402
from experiments.safety_selection.ledger import LEDGER, LimitReached  # noqa: E402


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    return bs.prepared_dirs(tmp_path_factory.mktemp("b17-gaps-prepared"))


def spy_generation(monkeypatch) -> dict:
    """Replaces the engine's two generation functions with spies. ``sample_generate`` calls ``greedy_generate``
    inside it, so a greedy call made while a sample call runs is not recorded as a greedy call of its own."""
    calls: dict[str, list[dict]] = {"greedy_generate": [], "sample_generate": []}
    inside = []
    greedy, sample = en.greedy_generate, en.sample_generate

    def greedy_spy(model, prompts, *args, **kwargs):
        if not inside:
            calls["greedy_generate"].append({"prompts": [list(p) for p in prompts], "kwargs": dict(kwargs)})
        return greedy(model, prompts, *args, **kwargs)

    def sample_spy(model, prompts, seeds, *args, **kwargs):
        calls["sample_generate"].append({"prompts": [list(p) for p in prompts], "seeds": list(seeds),
                                         "kwargs": dict(kwargs)})
        inside.append(True)
        try:
            return sample(model, prompts, seeds, *args, **kwargs)
        finally:
            inside.pop()

    monkeypatch.setattr(en, "greedy_generate", greedy_spy)
    monkeypatch.setattr(en, "sample_generate", sample_spy)
    return calls


# ----- pairing and batching (S4) -----------------------------------------------------------------------------


def test_each_answer_is_made_from_its_own_prompt_and_seed(tmp_path, prepared, monkeypatch):
    """On the fixture a sampled answer depends on its seed only, so equal answers cannot show the pairing. The spy
    shows it: the k-th prompt given to the generator is the k-th item's audited tokens, with that item's seed."""
    env = bs.Env(tmp_path, prepared)
    calls = spy_generation(monkeypatch)
    plan, _ = env.run()
    assert len(plan.harm) >= 2 and len({i["token_sha256"] for i in plan.harm}) == len(plan.harm)
    assert len(calls["sample_generate"]) == 1 and len(calls["greedy_generate"]) == 1
    sample = calls["sample_generate"][0]
    assert [ids_sha256(p) for p in sample["prompts"]] == [i["token_sha256"] for i in plan.harm]
    assert sample["seeds"] == [runner.sample_seed(bs.SEED, i["prompt_id"], 0) for i in plan.harm]
    greedy = calls["greedy_generate"][0]
    assert [ids_sha256(p) for p in greedy["prompts"]] == [i["token_sha256"] for i in plan.overrefusal]
    rows = bs.read_jsonl(env.base / "out" / "lean" / "sealed" / "samples.jsonl")
    assert [(r["prompt_id"], r["seed"]) for r in rows] == [(i["prompt_id"], s)
                                                          for i, s in zip(plan.harm, sample["seeds"], strict=True)]


def test_generation_uses_the_recipes_batch_size(tmp_path, prepared, monkeypatch):
    rec = bs.recipe(**{"generation.batch_size": 3})
    env = bs.Env(tmp_path, prepared, rec=rec)
    calls = spy_generation(monkeypatch)
    env.run()
    assert [c["kwargs"]["batch_size"] for c in calls["greedy_generate"]] == [3]
    assert [c["kwargs"]["batch_size"] for c in calls["sample_generate"]] == [3]


# ----- timing (S4) -----------------------------------------------------------------------------------------


class TrainingJumpClock:
    """A clock that jumps 1,000 s at the end of training (its third call is the train_end mark), so training takes
    1,000 s on the job's clock and the gap between training and the lean evaluation is 1 s."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return float(self.calls) + (1000.0 if self.calls >= 3 else 0.0)


def test_the_lean_limit_charges_the_training_time(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    plan = env.plan(env.job(wall_limit_seconds=500))
    with pytest.raises(LimitReached):
        lej.execute_c0_job(plan, bs.session(env.recipe), origin=0.0, origin_utc_epoch=0.0, clock=TrainingJumpClock())
    assert (env.base / "out" / "train" / "COMPLETE.json").is_file()
    assert (env.base / "out" / "lean" / "error.txt").is_file()
    assert not (env.base / "out" / "c0_record.json").exists()


def test_the_lean_ledger_uses_the_sessions_device_hooks(tmp_path, prepared, monkeypatch):
    env = bs.Env(tmp_path, prepared)
    made = []
    original = lej.RunLedger

    def capture(*args, **kwargs):
        made.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(lej, "RunLedger", capture)
    session = bs.session(env.recipe)
    lej.execute_c0_job(env.plan(), session)
    assert len(made) == 1                                   # the engine's run_one makes its own ledger, not this one
    assert made[0].get("sync") is session.sync and made[0].get("memory") is session.memory


def test_the_process_age_is_added_to_the_span(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    record = lej.execute_c0_job(env.plan(), bs.session(env.recipe), process_age_at_origin=5.0)
    assert record["cold_start"]["process_age_at_origin_seconds"] == 5.0
    assert record["job_span_with_process_start_seconds"] == record["job_span_seconds"] + 5.0


def test_an_unmapped_stage_is_listed_not_dropped(tmp_path):
    folder = tmp_path / "unit"
    folder.mkdir()
    (folder / LEDGER).write_text("".join(json.dumps(r) + "\n" for r in (
        {"stage": "train", "status": "ok", "seconds": 1.0, "segment": "init->q"},
        {"stage": "a_new_stage", "status": "ok", "seconds": 2.0})))
    rows = lej.stage_table(folder, "train", {"train": "training"})
    assert rows == [{"folder": "train", "stage": "train", "status": "ok", "seconds": 1.0, "category": "training",
                     "segment": "init->q"},
                    {"folder": "train", "stage": "a_new_stage", "status": "ok", "seconds": 2.0,
                     "category": "unmapped"}]


# ----- the scan (S2, S4) -----------------------------------------------------------------------------------


def test_the_scan_list_holds_every_answer_guard_and_task_row_text(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    plan, _ = env.run()
    sealed = env.base / "out" / "lean" / "sealed"
    texts = set(lej._texts(plan, sealed, 1))
    found = 0
    for name, field in (("generations.jsonl", "text"), ("samples.jsonl", "text"), ("guard.jsonl", "guard_answer"),
                        ("guard_samples.jsonl", "guard_answer")):
        for row in bs.read_jsonl(sealed / name):
            if row[field]:
                assert row[field] in texts, name
                found += 1
    assert found > 0
    for q in plan.prepared.query_rows:
        assert q["prompt"] in texts and q["response"] in texts
    bank_texts = [item[key] for item in plan.prepared.banks["dev"] for key in ("prompt", "question")
                  if isinstance(item.get(key), str) and item[key]]
    assert bank_texts and all(t in texts for t in bank_texts)


TRICKY = ["a plain text of some length", 'a "quoted" text of some length', "two lines\nof text, long enough",
          "a back\\slash in a long text", "café au lait, with an accent", "tab\tseparated text here",
          'café "au lait"\non two lines, with an accent']       # escaped AND non-ASCII: only one form matches


@pytest.mark.parametrize("text", TRICKY)
def test_the_scan_finds_a_text_raw_and_json_escaped(text):
    forms = [text.encode("utf-8"), canonical_json({"x": text}), json.dumps({"x": text}, ensure_ascii=True).encode(),
             json.dumps({"x": text}, ensure_ascii=False).encode("utf-8")]
    for data in forms:
        assert lej._text_hits(b"prefix " + data + b" suffix", [text]) == 1
        assert lej._text_hits(data, [text]) == s1._text_hits(data, [text], 1)      # the forms of s1common's scan
    assert lej._text_hits(b"nothing here", [text]) == 0


def test_a_json_escaped_text_in_a_readable_file_stops_the_job(tmp_path, prepared, monkeypatch):
    env = bs.Env(tmp_path, prepared)
    original = lej.lean_evaluate
    planted = {}

    def leak(session, policy, plan, ledger, unit_dir, checkpoint, fingerprint):
        out = original(session, policy, plan, ledger, unit_dir, checkpoint, fingerprint)
        rows = bs.read_jsonl(unit_dir / "sealed" / "guard_samples.jsonl")
        text = next(r["guard_answer"] for r in rows if r["guard_answer"]
                    and len(r["guard_answer"]) >= plan.settings["seal"]["text_scan_min_chars"])
        data = canonical_json({"x": text})
        assert text.encode("utf-8") not in data                 # the raw form is not in the file: only the escape
        (unit_dir / "planted.json").write_bytes(data)
        planted["done"] = True
        return out

    monkeypatch.setattr(lej, "lean_evaluate", leak)
    with pytest.raises(lej.RunError, match="readable file lean/planted.json"):
        env.run()
    assert planted == {"done": True} and not (env.base / "out" / "c0_record.json").exists()


# ----- the edit-arm fingerprint rule (S5) ------------------------------------------------------------------


def test_an_edit_arm_without_an_expected_fingerprint_refuses(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    arm, path, _ = bs.remove_edit(env.base, env.prepared_dir, env.manifest_sha256)
    job = env.job(arm=arm, edit=path)
    with pytest.raises(s1.Refusal, match="expect-adapter-fingerprint"):
        env.plan(job)
    assert not (env.base / "out").exists()
    assert env.plan(job, expected="0" * 64).expected_fingerprint == "0" * 64
    assert env.plan(env.job(), out=env.base / "out-a0").expected_fingerprint is None      # a0: optional


def test_an_edit_arm_rerun_states_that_training_matched(tmp_path, prepared):
    env = bs.Env(tmp_path, prepared)
    arm, path, _ = bs.remove_edit(env.base, env.prepared_dir, env.manifest_sha256)
    _, first = env.run(env.job(arm=arm, edit=path), out=env.base / "first", expected="0" * 64)
    fingerprint = first["training"]["target_adapter_fingerprint"]
    _, again = env.run(env.job(arm=arm, edit=path), out=env.base / "again", expected=fingerprint)
    assert first["training"]["adapter_fingerprint_equal"] is False
    assert again["training"]["adapter_fingerprint_equal"] is True
    assert again["training"]["expected_adapter_fingerprint"] == fingerprint


def test_the_command_line_refuses_an_edit_arm_without_the_fingerprint(tmp_path, prepared, monkeypatch):
    env = bs.Env(tmp_path, prepared)
    monkeypatch.setattr(lej, "SETTINGS_PATH", env.settings_path)
    monkeypatch.setattr(lej, "SETTINGS_SHA256", env.settings_sha256)
    arm, path, _ = bs.remove_edit(env.base, env.prepared_dir, env.manifest_sha256)
    out = env.base / "cli"
    argv = ["run", "--job", str(env.job(arm=arm, edit=path)), "--prepared", str(env.prepared_dir), "--recipe",
            str(env.recipe_path), "--out", str(out)]
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = lej.main(argv, loaders=fx.fixture_loaders())
    assert code == 2 and not out.exists() and stdout.getvalue() == ""
    assert "expect-adapter-fingerprint" in json.loads(stderr.getvalue())["error"]
