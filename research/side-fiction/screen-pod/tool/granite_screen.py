"""Granite Guardian 3.3 8B on the screen's rows, through the lead's Granite pod backend (the row loop only).

Rewritten 9 October 2026 (17:11 UTC, clock checked): ONE Granite-on-CUDA backend. This module holds no prompt, parse,
model load or build code. Every call is the lead's generic entry point granite_pod.judge_triples (scripts/
gate_b_mac_judges/pod/granite_pod.py, commit 2694bd0, pinned by SHA-256), given one GraniteSession for the whole step, so
the files are checked once, the tokenizer's fingerprint is checked before the model loads, and the model loads once:
  - the input: granite_files.granite_input(tok, user_text, response, criteria_id): messages [user, assistant], the
    pinned chat template with guardian_config {"criteria_id": C}, think=False, add_generation_prompt=True, the
    second_judge_probe trim above 8,000 tokens; criteria_id "harm" (its bytes pinned by the lead and by the screen's
    byte-identity test) and "sexual_content" (report only);
  - the triple: (row id, user turn, response): the user turn is the engine's instruction-blank-line-context rule
    (screen_rows.user_turn_of), the response the assistant turn;
  - the call and the label: the lead's (32 new tokens, temperature 0, top_k 1; granite_files.parse_score: the last
    <score>, yes/no, else unparsed), mapped to Yes/No/invalid (screen_rows.granite_label).
What the screen adds (SCREEN-SPEC section 2: "invalid after one retry"): an unparsed label gets ONE retry, a second
judge_triples call of the same triple. The lead's API has no reset hook, so llama.cpp may reuse the cached prefix on the
retry. Still unparsed stays invalid (the drop rule drops it). A call that raises ends the step (exit 1; no row is
labelled invalid for an error), and an input above 8,160 tokens refuses the step before the model loads (the lead's
precheck; the bundle builder already refuses such a round). Order: per row, harm then sexual_content, so the second
call can reuse the conversation's prefix (the speed stop's token ratio assumes it). Records hold ids, labels, counts
and SHA-256 only (judge_triples returns no text); nothing here prints or stores row, prompt or judge-output text.
"""
from __future__ import annotations

import pathlib
import sys
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402  (also puts the lead's modules on sys.path)
import screen_rows as R  # noqa: E402
import granite_pod  # noqa: E402  (the lead's backend: judge_triples, GraniteSession)


def judge_row(session, row, criteria: str, stop):
    """One (row, criteria) through the lead's judge_triples, with one retry of an unparsed label. Returns the cache
    fields, or None when stop() said so before a call (nothing is recorded; the item is judged again on a resume)."""
    triple = (row.row_id, row.user_turn, row.assistant_turn)
    for attempt in (1, 2):
        got = granite_pod.judge_triples([triple], criteria, session=session, stop=stop)
        if not got:
            return None
        ((ident, label, input_sha256, input_tokens, trimmed),) = got
        if ident != row.row_id:
            raise RuntimeError("judge_triples returned another id than the triple's")
        if label != "unparsed":
            break
    return {"label": R.granite_label(label), "attempts": attempt, "reason": "unparsed" if label == "unparsed" else None,
            "input_sha256": input_sha256, "input_tokens": input_tokens, "trimmed": trimmed}


def screen(session, rows: list, cache, stop, log, limit: int | None = None, every: int = 100,
           clock=time.time) -> dict:
    """Granite harm, then sexual_content, on each row in order. Resumable: a cached (row, criteria) is not judged
    again, after its ids and hashes are checked."""
    todo, cached = [], 0
    chosen = R.selected(rows, limit)
    for row in chosen:
        for criteria in P.CRITERIA:
            entry = cache.get((row.row_id, criteria))
            if entry is not None:
                R.check_against(entry, row, "granite cache")
                cached += 1
            else:
                todo.append((row, criteria))
    log(event="plan", step="granite", cached=cached, todo=len(todo), rows=len(chosen))
    t0, n, stopped, retries = clock(), 0, False, 0
    for row, criteria in todo:
        if stop():
            stopped = True
            log(event="stopping_on_signal", step="granite", judged=n)
            break
        res = judge_row(session, row, criteria, stop)
        if res is None:
            stopped = True
            log(event="stopping_on_signal", step="granite", judged=n)
            break
        cache.append({"row_id": row.row_id, "source": row.source, "line": row.line, "criteria": criteria,
                      "response_sha256": row.response_sha256, "user_sha256": row.user_sha256, **res})
        n += 1
        retries += res["attempts"] - 1
        if n % every == 0 or n == len(todo):
            el = clock() - t0
            log(event="progress", step="granite", judged=n, of=len(todo), sec_per_item=round(el / n, 3),
                eta_min=round(el / n * (len(todo) - n) / 60, 1))
    return {"judged": n, "cached": cached, "todo": len(todo), "stopped": stopped, "calls": n + retries,
            "retries": retries}
