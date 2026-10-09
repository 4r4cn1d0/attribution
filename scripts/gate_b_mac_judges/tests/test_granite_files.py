"""Granite-specific tests (fake judge, synthetic units). They run under pytest (minimal venv) and also without pytest
under tmp/judge-venv, which has llama_cpp and no pytest:

    PYTHONDONTWRITEBYTECODE=1 tmp/judge-venv/bin/python -B tests/test_granite_files.py BASETEMP

Neither path imports llama_cpp or transformers: the judge, the tokenizer and the model are fakes, and granite_files
imports the real ones only inside load_granite_tokenizer() and load_granite_model(), which no test calls. Patches are
made by hand (no pytest monkeypatch) and undone in `finally`.

Revised 9 October 2026 (15:29 UTC, clock checked): granite_files takes the criterion as a parameter (criteria_id,
default "harm"). The default's bytes are pinned against the 8 October function (_granite_input_8oct below, its source
pinned by SHA-256) on fixtures with a fake tokenizer here, and with the real tokenizer under tmp/judge-venv; another
criterion (sexual_content) reaches the template and the token check.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import inspect
import io
import json
import pathlib
import re
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


# granite_files.granite_input as of 8 October 2026 (granite_files.py SHA-256 3b533f51..., lines 80 to 93), verbatim
# but for its name: the frozen reference of the default criterion's bytes.
def _granite_input_8oct(tok, prompt: str, answer: str):
    """The judge's input under second_judge_probe's template and trimming rule: (text, input tokens, trimmed)."""
    messages = [{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}]
    text = tok.apply_chat_template(messages, guardian_config={"criteria_id": "harm"}, think=False,
                                   tokenize=False, add_generation_prompt=True)
    trimmed = False
    n = len(tok(text, add_special_tokens=False)["input_ids"])
    if n > 8000:                                                               # keep within the context window
        trimmed = True
        messages[1]["content"] = answer[: max(1000, int(len(answer) * 7000 / n))]
        text = tok.apply_chat_template(messages, guardian_config={"criteria_id": "harm"}, think=False,
                                       tokenize=False, add_generation_prompt=True)
        n = len(tok(text, add_special_tokens=False)["input_ids"])
    return text, n, trimmed


GRANITE_INPUT_8OCT_SHA256 = "048309ab7df5c1e5c185a8a8ae1d4930ece8d0658292c002346c37826e0b581f"   # its source then
FIXTURES = [(f"{MARK_P} short", f"{MARK_A} short"), (f"{MARK_P} two\nlines \u00e9\u4e2d", f"{MARK_A} x\n\n y  "),
            (MARK_P, MARK_A + " word" * 9000), ("", ""), (f"{MARK_P}  ", f"{MARK_A}\t ")]


class _AsDefault(ast.NodeTransformer):
    """criteria_id read as its default, "harm"."""

    def visit_Name(self, node):
        if node.id == "criteria_id" and isinstance(node.ctx, ast.Load):
            return ast.copy_location(ast.Constant("harm"), node)
        return node


def _body(fn: ast.FunctionDef) -> list:
    return [ast.dump(s) for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]


def test_the_default_criterion_is_the_8_october_prompt_builder():
    """granite_input's default ("harm") is the 8 October function: the frozen copy's source has the pinned SHA-256;
    the current function with criteria_id read as "harm" has the frozen copy's syntax tree; and on fixtures (a fake
    tokenizer; the real one under the judge venv: test_pod_tokenizer_gives_the_mac_prompt_bytes) the bytes, the token
    count and the trim flag are equal with no criterion, "harm" by position and criteria_id="harm"."""
    src = inspect.getsource(_granite_input_8oct).replace("def _granite_input_8oct(", "def granite_input(", 1)
    assert hashlib.sha256(src.encode("utf-8")).hexdigest() == GRANITE_INPUT_8OCT_SHA256
    tree = ast.parse(pathlib.Path(granite_files.__file__).read_text(encoding="utf-8"))
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    now, frozen = fns["granite_input"], ast.parse(src).body[0]
    assert [a.arg for a in now.args.args] == ["tok", "prompt", "answer", "criteria_id"]
    assert ast.literal_eval(now.args.defaults[-1]) == "harm" and len(now.args.defaults) == 1
    assert _body(_AsDefault().visit(now)) == _body(frozen)
    for name in ("granite_precheck",):
        assert fns[name].args.args[-1].arg == "criteria_id" and ast.literal_eval(fns[name].args.defaults[-1]) == "harm"
    judge = fns["granite_judge"].args
    assert judge.kwonlyargs[-1].arg == "criteria_id" and ast.literal_eval(judge.kw_defaults[-1]) == "harm"
    tok = FakeTok()
    for prompt, answer in FIXTURES:
        want = _granite_input_8oct(tok, prompt, answer)
        for got in (granite_files.granite_input(tok, prompt, answer),
                    granite_files.granite_input(tok, prompt, answer, "harm"),
                    granite_files.granite_input(tok, prompt, answer, criteria_id="harm")):
            assert got[0].encode("utf-8") == want[0].encode("utf-8") and got[1:] == want[1:]


class CriteriaTok(FakeTok):
    """FakeTok for one criterion: the template names it ("CRITERION:prompt|answer")."""

    def __init__(self, criteria):
        self.criteria = criteria

    def apply_chat_template(self, messages, guardian_config=None, think=None, tokenize=None, add_generation_prompt=None):
        assert guardian_config == {"criteria_id": self.criteria} and think is False and tokenize is False
        assert add_generation_prompt is True and [m["role"] for m in messages] == ["user", "assistant"]
        return self.criteria + ":" + messages[0]["content"] + "|" + messages[1]["content"]


def test_another_criterion_reaches_the_template_and_the_token_check():
    """criteria_id="sexual_content" goes to the template (guardian_config) in granite_input, the token check before
    the model loads (an input that fits under "harm" but not under the longer criterion refuses) and the judge."""
    tok = CriteriaTok("sexual_content")
    text, n, trimmed = granite_files.granite_input(tok, f"{MARK_P} q", f"{MARK_A} a", "sexual_content")
    assert text.startswith("sexual_content:") and n == len(text) and trimmed is False
    long = granite_files.granite_input(tok, MARK_P, MARK_A + " w" * 6000, "sexual_content")    # the trim's template too
    assert long[2] is True and long[0].startswith("sexual_content:") and long[1] == len(long[0]) <= 8000
    P = judging.Pair
    edge = P("hostA/round1/u greedy prompt p-009 sample None", "z" * (8160 - 1 - len(MARK_A) - 5), MARK_A)
    assert granite_files.granite_precheck(CriteriaTok("harm"), [edge])["input_tokens_max"] == 8160
    try:
        granite_files.granite_precheck(tok, [edge], criteria_id="sexual_content")
        raise AssertionError("not refused")
    except Refusal as e:
        assert "p-009" in str(e) and MARK_A not in str(e)
    events = []

    def fake_model():
        events.append("model")

        def llm(text, max_tokens, temperature, top_k):
            assert (max_tokens, temperature, top_k) == (32, 0.0, 1) and text.startswith("sexual_content:")
            return {"choices": [{"text": "<score> yes </score>"}]}
        return llm
    ok = P("hostA/round1/u greedy prompt p-001 sample None", f"{MARK_P} q", f"{MARK_A} a")
    with contextlib.redirect_stdout(io.StringIO()):
        judge = granite_files.granite_judge([ok], pins=lambda: None, load_tokenizer=lambda: tok, load_model=fake_model,
                                            criteria_id="sexual_content")
    assert judge(ok.prompt, ok.answer)["label"] == "yes" and events == ["model"]


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


def test_pod_tokenizer_gives_the_mac_prompt_bytes(tmp_path):
    """Under tmp/judge-venv only (transformers 5.18.0; CPU, no model, offline): the Mac folder's ten pinned files copied
    as the bundle copies them, loaded by granite_pod.load_tokenizer_at, give granite_files' own loader's templated
    bytes, token counts and trim flags for fixtures (synthetic text), and the pinned Mac fingerprint (9 Oct 2026)."""
    import os
    import shutil
    try:
        version = judging.metadata.version("transformers")
    except judging.metadata.PackageNotFoundError:
        version = None
    if version != "5.18.0" or not granite_files.TOK.is_dir():
        try:
            import pytest
        except ImportError:
            return
        pytest.skip("not the judge venv, or the Mac has no Granite tokenizer folder")
    sys.path.insert(0, str(HERE.parent / "pod"))
    import granite_pod
    saved = {k: os.environ.get(k) for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    try:
        assert granite_pod.verify_tokenizer_dir(granite_files.TOK) == {n: d for n, (_, d) in granite_pod.TOK_FILES.items()}
        copy = pathlib.Path(tmp_path) / "granite-tokenizer"
        copy.mkdir()
        for name in granite_pod.TOK_FILES:
            shutil.copyfile(granite_files.TOK / name, copy / name)
        mac, pod = granite_files.load_granite_tokenizer(), granite_pod.load_tokenizer_at(copy)
        assert (granite_pod.tokenizer_fingerprint(mac) == granite_pod.tokenizer_fingerprint(pod)
                == granite_pod.MAC_TOKENIZER_FINGERPRINT)
        fixtures = FIXTURES
        for prompt, answer in fixtures:
            a, b = granite_files.granite_input(mac, prompt, answer), granite_pod.granite_input(pod, prompt, answer)
            assert a[0].encode("utf-8") == b[0].encode("utf-8") and a[1:] == b[1:]
            frozen = _granite_input_8oct(mac, prompt, answer)               # the default is the 8 October bytes
            for got in (a, granite_files.granite_input(mac, prompt, answer, "harm")):
                assert got[0].encode("utf-8") == frozen[0].encode("utf-8") and got[1:] == frozen[1:]
        assert granite_files.granite_input(mac, *fixtures[2])[2] is True
        # another criterion (the Side Project's screen): the template's own text for it, a different input
        harm = granite_files.granite_input(mac, *fixtures[0])
        sexual = granite_files.granite_input(mac, *fixtures[0], "sexual_content")
        assert sexual[0] != harm[0] and sexual[1] != harm[1] and "Sexual content refers to" in sexual[0]
        assert "Sexual content refers to" not in harm[0]
        template = (granite_files.TOK / "chat_template.jinja").read_text()
        bank = re.search(r"criteria_bank = \(\{(.*?)\}\)", template, re.S)
        assert tuple(re.findall(r'^\s*"([a-z_]+)":', bank.group(1), re.M)) == granite_pod.GRANITE_CRITERIA
        # judge_triples on the pod's loader (a copy of the ten files) gives granite_files' bytes for both criteria
        seen = []

        def llm(text, max_tokens, temperature, top_k):
            seen.append(text)
            return {"choices": [{"text": "<score> no </score>"}]}
        session = granite_pod.GraniteSession(copy, pathlib.Path(tmp_path) / "none.gguf", load_model=lambda p: llm,
                                             check=lambda t, g: {"tokenizer_files": {}, "gguf_sha256": "0" * 64},
                                             require_fingerprint=granite_pod.MAC_TOKENIZER_FINGERPRINT)
        with contextlib.redirect_stdout(io.StringIO()):
            for criteria in ("harm", "sexual_content"):
                seen.clear()
                got = session.judge_triples([(i, p, a) for i, (p, a) in enumerate(fixtures)], criteria)
                for (p, a), text, res in zip(fixtures, seen, got):
                    want = granite_files.granite_input(mac, p, a, criteria)
                    assert text.encode("utf-8") == want[0].encode("utf-8") and res[3:] == want[1:]
                    assert res[2] == hashlib.sha256(want[0].encode("utf-8")).hexdigest() and res[1] == "no"
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


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
