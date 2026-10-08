"""Granite-specific tests (fake judge, synthetic units). They run under pytest (minimal venv) and also without pytest
under tmp/judge-venv, which has llama_cpp and no pytest:

    PYTHONDONTWRITEBYTECODE=1 tmp/judge-venv/bin/python -B tests/test_granite_files.py BASETEMP

Neither path imports llama_cpp or transformers: the judge, the tokenizer and the model are fakes, and granite_files
imports the real ones only inside load_granite_tokenizer() and load_granite_model(), which no test calls. Patches are
made by hand (no pytest monkeypatch) and undone in `finally`.
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import synth  # noqa: E402
from synth import MANIFEST, MARK_A, MARK_P  # noqa: E402

import granite_files  # noqa: E402
import judging  # noqa: E402
import write_files  # noqa: E402
from common import GRANITE, Refusal  # noqa: E402


def test_parse_score_rule():
    f = granite_files.parse_score
    assert f("<score> yes </score>") == "yes"
    assert f("<think></think><score> No </score>") == "no"
    assert f("<score> no </score> then <score>YES</score>") == "yes"           # the last score counts
    assert f("<score>\nyes\n</score>") == "yes"                                # DOTALL, stripped
    assert f("no score at all") == "unparsed"
    assert f("<score> maybe </score>") == "unparsed"
    assert f("<score> yes") == "unparsed"


def test_granite_run_check_and_file(tmp_path):
    retrieved = tmp_path / "retrieved"
    prepared = synth.make_bank(tmp_path)
    synth.make_unit(retrieved, "hostA", "1101-a0-e1-a1")
    synth.make_unit(retrieved, "hostA", "1101-a0-init-a1", target="init", completed_utc="2026-10-08T00:00:00+00:00")
    cache, out, calls = tmp_path / "gr.jsonl", tmp_path / "out", {}
    base = ["--run-root", str(retrieved), "--prepared", str(prepared), "--manifest", MANIFEST, "--cache", str(cache),
            "--expect-greedy", "3"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        assert granite_files.main(["check", *base], judge_factory=synth.fake_factory({}, {})) == 0
        assert not cache.exists()
        labels = {("greedy", "p-001", None): "yes", ("greedy", "p-002", None): "unparsed"}
        assert granite_files.main(["run", *base], judge_factory=synth.fake_factory(labels, calls)) == 0
        assert calls == {"factory": 1, "pairs": 6, "judged": 6}
        assert granite_files.main(["run", *base], judge_factory=synth.fake_factory(labels, calls)) == 0
        assert calls["judged"] == 6                                            # resumed: nothing new
        assert write_files.main(["--judge", "granite", "--cache", str(cache), "--out", str(out),
                                 "--run-root", str(retrieved)]) == 0
    text = buf.getvalue()
    assert MARK_P not in text and MARK_A not in text
    docs = [json.loads(p.read_bytes()) for p in sorted(out.glob("granite--*.json"))]
    assert len(docs) == 2 and all(d["sampled"] is None and d["judge"] == GRANITE for d in docs)
    assert all(d["greedy"] == {"n": 3, "harm": 1, "unparsed": 1} for d in docs)
    recs = [json.loads(x) for x in cache.read_bytes().split(b"\n") if x.strip()]
    assert {r["mode"] for r in recs} == {"greedy"} and all(r["sample_index"] is None for r in recs)
    assert MARK_A.encode() not in cache.read_bytes() and MARK_P.encode() not in cache.read_bytes()


def test_granite_pins_and_lazy_imports():
    assert granite_files.GGUF.name == "granite-guardian-3.3-8b-Q4_K_M.gguf"
    assert granite_files.TOK.name == "granite-guardian-3.3-8b-tokenizer"
    assert granite_files.MODES == ("greedy",)
    assert "llama_cpp" not in sys.modules and "transformers" not in sys.modules


class FakeTok:
    """One token per character of the templated text; the template joins the two contents with "|"."""

    def apply_chat_template(self, messages, guardian_config=None, think=None, tokenize=None, add_generation_prompt=None):
        assert guardian_config == {"criteria_id": "harm"} and think is False and tokenize is False
        assert add_generation_prompt is True and [m["role"] for m in messages] == ["user", "assistant"]
        return messages[0]["content"] + "|" + messages[1]["content"]

    def __call__(self, text, add_special_tokens=True):
        assert add_special_tokens is False
        return {"input_ids": [0] * len(text)}


def _pairs():
    P = judging.Pair
    where = "hostA/round1/u greedy prompt {} sample None"
    ok = P(where.format("p-001"), f"{MARK_P} short", f"{MARK_A} short")
    long_answer = P(where.format("p-002"), MARK_P, MARK_A + "x" * 9000)                 # trimmed, then within the window
    too_long = P(where.format("p-003"), MARK_P + "y" * 9000, f"{MARK_A} a")              # the prompt alone is too long
    edge = P(where.format("p-004"), "z" * (8160 - 1 - len(MARK_A)), MARK_A)              # exactly 8192 - 32 tokens
    over = P(where.format("p-005"), "z" * (8161 - 1 - len(MARK_A)), MARK_A)              # one token more
    return ok, long_answer, too_long, edge, over


def test_granite_precheck_names_items_over_the_window():
    ok, long_answer, too_long, edge, over = _pairs()
    tok = FakeTok()
    assert granite_files.INPUT_LIMIT == 8192 - 32
    plan = granite_files.granite_precheck(tok, [ok, long_answer, edge])
    # long_answer and edge both take the trim branch (> 8000); edge's short answer is not cut, so it stays at 8160
    assert plan["items"] == 3 and plan["trimmed"] == 2 and plan["input_tokens_max"] == 8160
    text, n, trimmed = granite_files.granite_input(tok, long_answer.prompt, long_answer.answer)
    assert trimmed and n <= 8000 and n == len(text)                          # long_answer is cut to fit
    for bad in ([ok, too_long], [edge, over]):
        try:
            granite_files.granite_precheck(tok, bad)
            raise AssertionError("not refused")
        except Refusal as e:
            msg = str(e)
            assert "1 Granite input(s) exceed 8160 tokens" in msg and bad[1].where in msg
            assert MARK_P not in msg and MARK_A not in msg


def test_granite_judge_checks_every_item_before_the_model_loads():
    ok, long_answer, too_long, _, _ = _pairs()
    events = []

    def fake_model():
        events.append("model")

        def llm(text, max_tokens, temperature, top_k):
            assert (max_tokens, temperature, top_k) == (32, 0.0, 1)
            return {"choices": [{"text": "<think></think><score> Yes </score>" if "short" in text else "<score>no</score>"}]}
        return llm
    hooks = dict(pins=lambda: events.append("pins"), load_tokenizer=lambda: (events.append("tok"), FakeTok())[1],
                 load_model=fake_model)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            granite_files.granite_judge([ok, too_long], **hooks)
            raise AssertionError("not refused")
        except Refusal as e:
            assert "p-003" in str(e)
        assert events == ["pins", "tok"]                                     # the model never loaded
        judge = granite_files.granite_judge([ok, long_answer], **hooks)
    assert events == ["pins", "tok", "pins", "tok", "model"]
    r1, r2 = judge(ok.prompt, ok.answer), judge(long_answer.prompt, long_answer.answer)
    assert r1["label"] == "yes" and r1["truncated"] is False and r1["input_tokens"] == len(ok.prompt) + 1 + len(ok.answer)
    assert r2["label"] == "no" and r2["truncated"] is True and r2["answer_tokens"] == len(long_answer.answer)
    assert MARK_P not in buf.getvalue() and MARK_A not in buf.getvalue()


def test_granite_real_main_checks_packages_pins_and_gpu_lock(tmp_path):
    retrieved = tmp_path / "retrieved"
    prepared = synth.make_bank(tmp_path)
    synth.make_unit(retrieved, "hostA", "1101-a0-e1-a1")
    cache = tmp_path / "gr.jsonl"
    base = ["--run-root", str(retrieved), "--prepared", str(prepared), "--manifest", MANIFEST, "--cache", str(cache),
            "--expect-greedy", "3"]
    saved = (judging.require_packages, judging.take_gpu_lock, granite_files.check_pins, granite_files.granite_judge)
    events = []

    def bad_pins():
        raise Refusal("the Granite GGUF differs from its pinned SHA-256")

    def held():
        events.append("lock")
        raise Refusal("fake: the GPU lock is held")
    out, err = io.StringIO(), io.StringIO()
    try:
        judging.require_packages = lambda pins: (events.append(("packages", tuple(sorted(pins)))), {})[1]
        granite_files.check_pins = lambda: events.append("pins")
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            assert granite_files.main(["check", *base]) == 0                 # L7: a real check hashes the pins
            assert events == [("packages", ("llama-cpp-python", "transformers")), "pins"]
            granite_files.check_pins = bad_pins
            assert granite_files.main(["check", *base]) == 2
            assert "differs from its pinned SHA-256" in err.getvalue()
            events.clear()
            judging.take_gpu_lock = held                                     # M3: the lock comes before the factory
            granite_files.granite_judge = lambda pairs: events.append("factory")
            assert granite_files.main(["run", *base]) == 2
            assert events == [("packages", ("llama-cpp-python", "transformers")), "lock"]
            assert not cache.exists() or cache.read_bytes() == b""
    finally:
        (judging.require_packages, judging.take_gpu_lock, granite_files.check_pins, granite_files.granite_judge) = saved
    assert MARK_P not in out.getvalue() + err.getvalue() and MARK_A not in out.getvalue() + err.getvalue()


def test_granite_main_returns_5_when_stopped_by_sigterm(tmp_path):
    """SIGTERM (the watchdog) while an item is judged: the run stops after it, exit 5; a second run resumes, exit 0."""
    import os
    import signal
    retrieved = tmp_path / "retrieved"
    prepared = synth.make_bank(tmp_path)
    synth.make_unit(retrieved, "hostA", "1101-a0-e1-a1")
    cache, calls = tmp_path / "gr.jsonl", {}
    base = ["--run-root", str(retrieved), "--prepared", str(prepared), "--manifest", MANIFEST, "--cache", str(cache),
            "--expect-greedy", "3"]
    before = signal.getsignal(signal.SIGTERM)

    def term_on_first(prompt, ans):
        if calls["judged"] == 1:
            os.kill(os.getpid(), signal.SIGTERM)
        return {}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        assert granite_files.main(["run", *base], judge_factory=synth.fake_factory({}, calls, extra=term_on_first)) == 5
        assert calls["judged"] == 1 and signal.getsignal(signal.SIGTERM) == before
        assert len([x for x in cache.read_bytes().split(b"\n") if x.strip()]) == 1
        assert granite_files.main(["run", *base], judge_factory=synth.fake_factory({}, calls)) == 0
        assert calls["judged"] == 3
    done = [json.loads(x) for x in buf.getvalue().splitlines() if '"run_done"' in x]
    assert [d["stopped"] for d in done] == [True, False]
    assert MARK_P not in buf.getvalue() and MARK_A not in buf.getvalue()


def test_judge_venv_has_the_granite_pins():
    """Under tmp/judge-venv: the pinned versions are the installed ones (importlib.metadata only)."""
    try:
        judging.metadata.version("llama-cpp-python")
    except judging.metadata.PackageNotFoundError:
        try:
            import pytest
        except ImportError:
            return
        pytest.skip("not the judge venv")
    assert judging.require_packages(granite_files.PACKAGES) == granite_files.PACKAGES


if __name__ == "__main__":                       # no pytest in tmp/judge-venv
    base = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if base:
        base.mkdir(parents=True, exist_ok=True)
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        with tempfile.TemporaryDirectory(dir=base) as d:
            try:
                fn(pathlib.Path(d)) if fn.__code__.co_argcount else fn()
                print(f"PASS {name}")
            except Exception as e:                # names the test and the error type only
                failed += 1
                print(f"FAIL {name}: {type(e).__name__}")
    print(json.dumps({"passed": len(tests) - failed, "failed": failed,
                      "llama_cpp_imported": "llama_cpp" in sys.modules, "transformers_imported": "transformers" in sys.modules}))
    sys.exit(1 if failed or "llama_cpp" in sys.modules else 0)
