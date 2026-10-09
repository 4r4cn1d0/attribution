"""Granite: the prompt bytes against second_judge_probe.py (the Mac's judge venv and tokenizer, offline), the call
convention, the retry and invalid rules, the known-answer loop and the screen loop (fakes; no model)."""
from __future__ import annotations

import ast
import json
import os
import pathlib
import subprocess

import pytest
from conftest import HERE, TOOL, P, R, needs_real
from common import Refusal
import granite_screen as G

JUDGE_PY = P.ROOT / "tmp/judge-venv/bin/python"
TOK = P.ROOT / "tmp/judge-models/granite-guardian-3.3-8b-tokenizer"


def _parity(rows: int) -> dict:
    done = subprocess.run([str(JUDGE_PY), "-I", "-B", str(HERE / "granite_parity_helper.py"), "--tool", str(TOOL),
                           "--probe", str(P.SECOND_JUDGE_PROBE), "--rows", str(rows)], capture_output=True, text=True,
                          timeout=900, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                                            "HOME": os.environ.get("HOME", "/tmp")}, cwd="/")
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


@needs_real
@pytest.mark.skipif(not (JUDGE_PY.is_file() and TOK.is_dir() and P.SECOND_JUDGE_PROBE.is_file()),
                    reason="the Mac's judge venv, Granite tokenizer or second_judge_probe.py is absent")
def test_prompt_bytes_and_calls_equal_second_judge_probe_with_the_real_tokenizer():
    """The real template (transformers 5.18.0, the pinned tokenizer folder) through both code paths: synthetic
    fixtures (one trimmed), 300 real rows of each arm and the 200 known answers give identical bytes."""
    out = _parity(300)
    assert out["probe_sha256"] == P.SECOND_JUDGE_PROBE_SHA256
    assert out["versions"] == {"Jinja2": "3.1.6", "tokenizers": "0.23.2", "transformers": "5.18.0"}
    assert out["tokenizer_matches_pins"] is True
    assert out["init_kwargs_equal"] and out["init_kwargs"] == ["logits_all", "model_path", "n_ctx", "n_gpu_layers",
                                                               "seed", "verbose"]
    assert out["call_kwargs_equal"] and out["label_parse_equal"]
    assert out["fixtures"] == out["fixtures_identical"] == 6 and out["fixtures_trimmed"] >= 1
    assert out["real_rows"] == out["real_rows_identical"] == 600
    assert out["ka_items"] == out["ka_inputs_equal"] == out["ka_identical"] == 200
    assert out["sexual_matches_template"] == out["sexual_differs_from_harm"] == 6


def test_probe_file_is_the_pinned_convention():
    if not P.SECOND_JUDGE_PROBE.is_file():
        pytest.skip("second_judge_probe.py is absent")
    import hashlib
    assert hashlib.sha256(P.SECOND_JUDGE_PROBE.read_bytes()).hexdigest() == P.SECOND_JUDGE_PROBE_SHA256
    olmo = P.ROOT / "tmp/family-probe-olmo2-1b/second_judge_probe.py"          # the run that labelled the known answers
    if olmo.is_file():
        assert hashlib.sha256(olmo.read_bytes()).hexdigest() == P.SECOND_JUDGE_PROBE_SHA256


def test_structural_convention_matches_the_probe_source():
    """Without the tokenizer: the probe's literal call arguments, read from its syntax tree, are the screen's."""
    if not P.SECOND_JUDGE_PROBE.is_file():
        pytest.skip("second_judge_probe.py is absent")
    tree = ast.parse(P.SECOND_JUDGE_PROBE.read_text(encoding="utf-8"))
    skip = object()

    def lit(v):
        try:
            return ast.literal_eval(v)
        except ValueError:
            return skip
    calls = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.keywords:
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            calls.setdefault(name, []).append({k.arg: lit(k.value) for k in node.keywords if lit(k.value) is not skip})
    assert {"n_gpu_layers": P.N_GPU_LAYERS, "n_ctx": P.N_CTX, "seed": P.SEED, "verbose": False,
            "logits_all": False} == calls["Llama"][0]
    assert {"max_tokens": P.NEW_TOKENS, "temperature": 0.0, "top_k": 1} == calls["llm"][0]
    assert len(calls["apply_chat_template"]) == 2 and all(
        c == {"guardian_config": {"criteria_id": "harm"}, "think": False, "tokenize": False,
              "add_generation_prompt": True} for c in calls["apply_chat_template"])
    assert calls["tok"] == [{"add_special_tokens": False}] * 2
    src = P.SECOND_JUDGE_PROBE.read_text(encoding="utf-8")
    assert "> 8000" in src and "max(1000, int(len(answer) * 7000 / n))" in src
    assert r're.findall(r"<score>(.*?)</score>", out, re.DOTALL)' in src


# ------------------------------------------------------------------------------------------------ fakes

class FakeTok:
    """apply_chat_template renders a marked string; one token per character (so trimming can be driven)."""

    def __init__(self):
        self.renders = []

    def apply_chat_template(self, messages, guardian_config=None, think=None, tokenize=None,
                            add_generation_prompt=None):
        self.renders.append((guardian_config, think, tokenize, add_generation_prompt))
        return f"[{guardian_config['criteria_id']}]U:{messages[0]['content']}|A:{messages[1]['content']}"

    def __call__(self, text, add_special_tokens=True):
        assert add_special_tokens is False
        return {"input_ids": list(range(len(text)))}


class FakeLLM:
    def __init__(self, outputs):
        self.outputs, self.calls, self.resets = list(outputs), [], 0

    def __call__(self, text, **kw):
        self.calls.append((text, kw))
        out = self.outputs.pop(0)
        if isinstance(out, BaseException):
            raise out
        return {"choices": [{"text": out}]}

    def reset(self):
        self.resets += 1


@pytest.mark.parametrize("out,label", [("<score> yes </score>", "Yes"), ("<score>No</score>", "No"),
                                       ("<score> no </score> then <score> yes </score>", "Yes"),
                                       ("<score> maybe </score>", "invalid"), ("no score", "invalid"), ("", "invalid"),
                                       ("<score>\n yes\n</score>", "Yes")])
def test_label_parse(out, label):
    assert G.parse_label(out) == label


def test_judge_calls_with_the_probe_arguments_and_criteria():
    tok, llm = FakeTok(), FakeLLM(["<score> yes </score>", "<score> no </score>"])
    j = G.GraniteJudge(tok, llm)
    assert j.judge("U", "A", "harm")["label"] == "Yes"
    assert j.judge("U", "A", "sexual_content")["label"] == "No"
    assert [c[1] for c in llm.calls] == [{"max_tokens": 32, "temperature": 0.0, "top_k": 1}] * 2
    assert [c[0] for c in llm.calls] == ["[harm]U:U|A:A", "[sexual_content]U:U|A:A"]
    assert all(r[1:] == (False, False, True) for r in tok.renders)
    with pytest.raises(ValueError):
        j.judge("U", "A", "violence")


def test_one_retry_after_reset_then_invalid():
    llm = FakeLLM(["garbage", "<score> no </score>"])
    j = G.GraniteJudge(FakeTok(), llm)
    res = j.judge("U", "A", "harm")
    assert res == {"label": "No", "attempts": 2, "errors": 0, "reason": None, "input_tokens": len("[harm]U:U|A:A"),
                   "trimmed": False}
    assert llm.resets == 1 and j.retries == 1 and j.calls == 2
    llm = FakeLLM(["garbage", "still garbage"])
    res = G.GraniteJudge(FakeTok(), llm).judge("U", "A", "harm")
    assert (res["label"], res["attempts"], res["reason"]) == ("invalid", 2, "unparsed")
    llm = FakeLLM([RuntimeError("boom"), ValueError("ctx")])
    res = G.GraniteJudge(FakeTok(), llm).judge("U", "A", "harm")
    assert (res["label"], res["attempts"], res["errors"], res["reason"]) == ("invalid", 2, 2, "error")


def test_trim_rule_and_over_limit(monkeypatch):
    tok = FakeTok()
    rendered, n, trimmed = G.granite_prompt(tok, "U", "A" * 9000, "harm")
    assert trimmed and rendered == "[harm]U:U|A:" + "A" * max(1000, int(9000 * 7000 / (9000 + 12)))
    assert n == len(rendered)
    monkeypatch.setattr(P, "INPUT_LIMIT", 100)
    llm = FakeLLM([])
    res = G.GraniteJudge(tok, llm).judge("U", "A" * 200, "harm")
    assert (res["label"], res["attempts"], res["reason"]) == ("invalid", 0, "over_limit") and llm.calls == []


class Stepper:
    def __init__(self, step=0.1):
        self.t, self.step = 1000.0, step

    def __call__(self):
        self.t += self.step
        return self.t


def _ka_items(n=10):
    return [(f"p-{i:03d}", f"{i:064x}", f"prompt {i}", f"answer {i}") for i in range(n)]


def test_known_answer_loop_counts_and_entries(monkeypatch):
    monkeypatch.setattr(P, "KA_N", 10)
    items = _ka_items(10)
    mac = {pid: ("Yes" if i % 3 == 0 else "No") for i, (pid, *_) in enumerate(items)}

    class J:
        calls = retries = errors = 0

        def judge(self, u, a, c):
            assert c == "harm"
            i = int(a.split()[1])
            return {"label": "Yes" if i % 3 == 0 or i == 4 else "No", "attempts": 1, "errors": 0, "reason": None,
                    "input_tokens": 9, "trimmed": False}
    logs = []
    counts, entries, stopped, per = G.known_answer(J(), items, mac, lambda: False, lambda **k: logs.append(k),
                                                   clock=Stepper(0.1))
    assert not stopped and counts["judged"] == 10 and counts["identical"] == 9 and counts["flips"] == {"No->Yes": 1}
    assert set(entries[0]) == {"prompt_id", "answer_sha256", "mac", "pod", "attempts", "errors", "reason",
                               "input_tokens", "trimmed"}
    assert per == pytest.approx(0.1, abs=0.02)


def test_known_answer_stops_on_signal_and_refuses_without_gpu_speed():
    items = _ka_items(10)
    mac = {pid: "No" for pid, *_ in items}

    class J:
        calls = retries = errors = 0

        def judge(self, u, a, c):
            return {"label": "No", "attempts": 1, "errors": 0, "reason": None, "input_tokens": 9, "trimmed": False}
    n = {"k": 0}

    def stop():
        n["k"] += 1
        return n["k"] > 4
    counts, entries, stopped, _ = G.known_answer(J(), items, mac, stop, lambda **k: None, clock=Stepper(0.1))
    assert stopped and counts["judged"] == 4 and counts["n"] == 10 and len(entries) == 4
    with pytest.raises(Refusal, match="not running on the GPU"):
        G.known_answer(J(), items, mac, lambda: False, lambda **k: None, clock=Stepper(P.KA_MAX_S_PER_ITEM + 1))


def test_screen_loop_resumes_and_aborts_on_consecutive_errors(tmp_path):
    from conftest import fiction_row, sha, write_jsonl
    path = write_jsonl(tmp_path / "dark.jsonl", [fiction_row("dark", 1, i) for i in range(6)])
    rows = R.read_rows("dark", path, sha(path.read_bytes()), 6)
    cache = R.JsonlCache(tmp_path / "g.jsonl", R.check_granite, R.granite_key)

    class J:
        calls = retries = errors = 0

        def judge(self, u, a, c):
            self.calls += 1
            return {"label": "No", "attempts": 1, "errors": 0, "reason": None, "input_tokens": 9, "trimmed": False}
    j = J()
    res = G.screen(j, rows[:3], cache, lambda: False, lambda **k: None)
    assert res["judged"] == 6 and j.calls == 6
    res = G.screen(j, rows, cache, lambda: False, lambda **k: None)
    assert (res["cached"], res["judged"]) == (6, 6) and len(cache) == 12
    order = [(e["row_id"], e["criteria"]) for e in cache.entries.values()]
    assert order[:2] == [("dark-1", "harm"), ("dark-1", "sexual_content")]

    class Broken(J):
        def judge(self, u, a, c):
            return {"label": "invalid", "attempts": 2, "errors": 2, "reason": "error", "input_tokens": 9,
                    "trimmed": False}
    cache2 = R.JsonlCache(tmp_path / "g2.jsonl", R.check_granite, R.granite_key)
    with pytest.raises(RuntimeError, match="every Granite call raised"):
        G.screen(Broken(), rows, cache2, lambda: False, lambda **k: None)
    assert len(cache2) == 2 * P.CONSECUTIVE_ERROR_LIMIT
    assert len(G.selected(rows, 2)) == 2 and len(G.selected(rows, None)) == 6


def test_load_llm_uses_the_probe_constructor(monkeypatch):
    import sys
    import types
    seen = {}

    class L:
        def __init__(self, **kw):
            seen.update(kw)
    monkeypatch.setitem(sys.modules, "llama_cpp", types.SimpleNamespace(Llama=L))
    G.load_llm(pathlib.Path("/x/model.gguf"))
    assert seen == {"model_path": "/x/model.gguf", "n_gpu_layers": -1, "n_ctx": 8192, "seed": 0, "verbose": False,
                    "logits_all": False}
