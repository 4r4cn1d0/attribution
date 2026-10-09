"""Granite Guardian 3.3 8B on the pod: the Mac's calling convention, on llama.cpp's CUDA backend.

Rebuilt 9 October 2026 (10:27 UTC, clock checked) from the lead's partial build. Runs in the pod's granite venv (the
judge venv's packages: transformers 5.18.0 for the chat template, llama-cpp-python 0.3.36 built with CUDA from its
pinned sdist).

The calling convention is tmp/family-probe-llama32-1b/second_judge_probe.py's (SHA-256 c51e466c...), step for step:
  - the tokenizer: AutoTokenizer.from_pretrained(<the pinned tokenizer folder>) (ten files pinned by SHA-256);
  - the model: Llama(model_path=<the pinned GGUF>, n_gpu_layers=-1, n_ctx=8192, seed=0, verbose=False,
    logits_all=False); only the GGUF's place differs (the Hub cache on the pod), and the build's backend (CUDA);
  - the input: messages [user: the user turn, assistant: the assistant turn], apply_chat_template(messages,
    guardian_config={"criteria_id": C}, think=False, tokenize=False, add_generation_prompt=True), C a parameter
    ("harm" is the Mac's; "sexual_content" is report-only); when the templated input has more than 8000 tokens
    (tok(text, add_special_tokens=False)), the assistant turn is cut to its first max(1000, int(len * 7000 / n))
    characters and the template applied again (granite_prompt; a test proves its bytes equal the probe's for "harm");
  - the call: llm(text, max_tokens=32, temperature=0.0, top_k=1)["choices"][0]["text"] (greedy);
  - the label: the last "<score> ... </score>" of the output, stripped and lower-cased: "yes" -> Yes, "no" -> No,
    anything else (or no score) -> invalid.
What the screen adds: an invalid label gets ONE retry (llm.reset() first, so the retry evaluates the whole input
afresh rather than reusing the cached prefix); still invalid stays invalid (the drop rule drops it). A call that
raises counts as an invalid attempt; when every call of CONSECUTIVE_ERROR_LIMIT rows in a row raised, the step aborts
instead of labelling rows invalid. A templated input still above n_ctx - 32 tokens after the trim is invalid
(over_limit) without a call. The known-answer check runs the same code on the Mac's 200 known answers before any row;
after its first KA_SPEED_AFTER answers it refuses when their mean time is above KA_MAX_S_PER_ITEM seconds (a CPU
fallback: the round could not end inside its cap). Nothing here prints, logs or stores row, prompt, answer or
judge-output text: records hold ids, labels, counts and SHA-256 only.
"""
from __future__ import annotations

import os
import pathlib
import re
import sys
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402
import screen_rows as R  # noqa: E402
from common import Refusal  # noqa: E402

SCORE = re.compile(r"<score>(.*?)</score>", re.DOTALL)
CALL_ERRORS = (RuntimeError, ValueError, OSError, KeyError, IndexError, TypeError)


def granite_messages(user_turn: str, assistant_turn: str) -> list:
    return [{"role": "user", "content": user_turn}, {"role": "assistant", "content": assistant_turn}]


def render(tok, messages: list, criteria: str):
    return tok.apply_chat_template(messages, guardian_config={"criteria_id": criteria}, think=False,
                                   tokenize=False, add_generation_prompt=True)


def count_tokens(tok, rendered) -> int:
    return len(tok(rendered, add_special_tokens=False)["input_ids"])


def granite_prompt(tok, user_turn: str, assistant_turn: str, criteria: str):
    """(templated input, its token count, trimmed): second_judge_probe's judge() input with criteria C."""
    messages = granite_messages(user_turn, assistant_turn)
    rendered = render(tok, messages, criteria)
    trimmed = False
    if count_tokens(tok, rendered) > P.TRIM_AT_TOKENS:                          # keep within the context window
        trimmed = True
        n = count_tokens(tok, rendered)
        messages[1]["content"] = assistant_turn[: max(P.TRIM_MIN_CHARS, int(len(assistant_turn) * P.TRIM_TO_TOKENS / n))]
        rendered = render(tok, messages, criteria)
    return rendered, count_tokens(tok, rendered), trimmed


def parse_label(generated: str) -> str:
    """The probe's score rule: the last <score>...</score>, stripped, lower-cased; yes/no, else invalid."""
    scores = SCORE.findall(generated)
    value = scores[-1].strip().lower() if scores else None
    return {"yes": "Yes", "no": "No"}.get(value, "invalid")


class GraniteJudge:
    """judge(user turn, assistant turn, criteria) -> {label, attempts, errors, reason, input_tokens, trimmed}."""

    def __init__(self, tok, llm):
        self.tok, self.llm = tok, llm
        self.calls = self.retries = self.errors = 0

    def generate(self, rendered) -> str:
        return self.llm(rendered, max_tokens=P.NEW_TOKENS, temperature=0.0, top_k=1)["choices"][0]["text"]

    def judge(self, user_turn: str, assistant_turn: str, criteria: str) -> dict:
        if criteria not in P.CRITERIA:
            raise ValueError(f"criteria {criteria!r} is not one of {list(P.CRITERIA)}")
        rendered, n, trimmed = granite_prompt(self.tok, user_turn, assistant_turn, criteria)
        result = {"label": "invalid", "attempts": 0, "errors": 0, "reason": "over_limit", "input_tokens": n,
                  "trimmed": trimmed}
        if n > P.INPUT_LIMIT:
            return result
        for attempt in (1, 2):                                   # one retry of an invalid label
            if attempt == 2:
                self.retries += 1
                self.llm.reset()
            result["attempts"] = attempt
            self.calls += 1
            try:
                label = parse_label(self.generate(rendered))
                result["reason"] = None if label != "invalid" else "unparsed"
            except CALL_ERRORS:
                label = "invalid"
                result["errors"] += 1
                result["reason"] = "error"
                self.errors += 1
            result["label"] = label
            if label != "invalid":
                break
        return result


# ---------------------------------------------------------------- the real assets (never called by the tests)

def load_tokenizer(folder: pathlib.Path):
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(folder)


def load_llm(gguf: pathlib.Path):
    from llama_cpp import Llama
    return Llama(model_path=str(gguf), n_gpu_layers=P.N_GPU_LAYERS, n_ctx=P.N_CTX, seed=P.SEED, verbose=False,
                 logits_all=False)


# ---------------------------------------------------------------- the known-answer check and the screen

def known_answer(judge: GraniteJudge, ka_items, mac_labels: dict, stop, log, clock=time.time) -> tuple:
    """ka_items: (prompt id, answer SHA-256, user turn, assistant turn), sorted by prompt id as the Mac judged them.
    Returns (counts, per-item entries, stopped, seconds per item). Entries hold ids, labels and counts only. Refuses
    when the first KA_SPEED_AFTER answers took more than KA_MAX_S_PER_ITEM seconds each on average."""
    pairs, entries, t0 = [], [], clock()
    for k, (pid, answer_sha, user_turn, assistant_turn) in enumerate(ka_items, 1):
        if stop():
            log(event="stopping_on_signal", step="ka", judged=k - 1)
            rest = [(mac_labels[p], None) for p, *_ in ka_items[k - 1:]]
            return R.ka_counts(pairs + rest), entries, True, _per_item(clock() - t0, k - 1)
        res = judge.judge(user_turn, assistant_turn, "harm")
        pairs.append((mac_labels[pid], res["label"]))
        entries.append({"prompt_id": pid, "answer_sha256": answer_sha, "mac": mac_labels[pid], "pod": res["label"],
                        "attempts": res["attempts"], "errors": res["errors"], "reason": res["reason"],
                        "input_tokens": res["input_tokens"], "trimmed": res["trimmed"]})
        el = clock() - t0
        if k == P.KA_SPEED_AFTER and el / k > P.KA_MAX_S_PER_ITEM:
            log(event="progress", step="ka", judged=k, of=len(ka_items), sec_per_item=round(el / k, 3))
            raise Refusal(f"the first {k} known answers took {el / k:.1f} s each (limit {P.KA_MAX_S_PER_ITEM} s): "
                          "llama.cpp is not running on the GPU, so the round could not end inside its cap")
        if k % 50 == 0 or k == len(ka_items):
            log(event="progress", step="ka", judged=k, of=len(ka_items), sec_per_item=round(el / k, 3),
                eta_min=round(el / k * (len(ka_items) - k) / 60, 1))
    return R.ka_counts(pairs), entries, False, _per_item(clock() - t0, len(ka_items))


def _per_item(seconds: float, n: int):
    return round(seconds / n, 4) if n else None


def selected(rows: list, limit: int | None) -> list:
    """The rows a run screens: every row, or with a limit the first `limit` rows of each source (a smoke run)."""
    if limit is None:
        return list(rows)
    taken: dict = {}
    out = []
    for row in rows:
        if taken.get(row.source, 0) < limit:
            taken[row.source] = taken.get(row.source, 0) + 1
            out.append(row)
    return out


def screen(judge: GraniteJudge, rows: list, cache, stop, log, limit: int | None = None, every: int = 200,
           clock=time.time) -> dict:
    """Granite harm, then sexual_content, on each row in order (the second call reuses the cached prefix of the
    conversation). Resumable: a cached (row, criteria) is not judged again, after its ids and hashes are checked."""
    todo, cached = [], 0
    chosen = selected(rows, limit)
    for row in chosen:
        for criteria in P.CRITERIA:
            entry = cache.get((row.row_id, criteria))
            if entry is not None:
                R.check_against(entry, row, "granite cache")
                cached += 1
            else:
                todo.append((row, criteria))
    log(event="plan", step="granite", cached=cached, todo=len(todo), rows=len(chosen))
    t0, n, stopped, consecutive = clock(), 0, False, 0
    for row, criteria in todo:
        if stop():
            stopped = True
            log(event="stopping_on_signal", step="granite", judged=n)
            break
        res = judge.judge(row.user_turn, row.assistant_turn, criteria)
        cache.append({"row_id": row.row_id, "source": row.source, "line": row.line, "criteria": criteria,
                      "label": res["label"], "attempts": res["attempts"], "errors": res["errors"],
                      "reason": res["reason"], "input_tokens": res["input_tokens"], "trimmed": res["trimmed"],
                      "response_sha256": row.response_sha256, "user_sha256": row.user_sha256})
        n += 1
        if criteria == P.CRITERIA[-1]:
            raised = all((cache.get((row.row_id, c)) or {}).get("errors", 0)
                         == (cache.get((row.row_id, c)) or {}).get("attempts", -1) > 0 for c in P.CRITERIA)
            consecutive = consecutive + 1 if raised else 0
            if consecutive >= P.CONSECUTIVE_ERROR_LIMIT:
                raise RuntimeError(f"every Granite call raised on {consecutive} rows in a row; the step stops rather "
                                   "than label rows invalid")
        if n % every == 0 or n == len(todo):
            el = clock() - t0
            log(event="progress", step="granite", judged=n, of=len(todo), sec_per_item=round(el / n, 3),
                eta_min=round(el / n * (len(todo) - n) / 60, 1))
    return {"judged": n, "cached": cached, "todo": len(todo), "stopped": stopped, "calls": judge.calls,
            "retries": judge.retries, "errors": judge.errors}
