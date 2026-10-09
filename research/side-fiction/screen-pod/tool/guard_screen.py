"""Qwen3Guard-Gen-4B on the pod through the engine's own GuardScorer (descriptive only; it never drops a row).

Kept from the lead's partial build (9 October 2026); reviewed 10:27 UTC (clock checked). Runs in the pod's guard venv
(the engine's requirements.lock versions over the image's torch 2.8.0) with the shipped engine code on sys.path. The
scorer is built exactly as an engine run builds it: experiments.safety_selection.loaders.real_loaders(),
prepare_device(recipe) (configure_cuda: deterministic cuBLAS, which needs CUBLAS_WORKSPACE_CONFIG exported by
screen_run.sh, TF32 off, one GPU; bfloat16 reduced-precision reductions off), then guard(recipe, ledger, "cuda") with
recipe B's guard block (Qwen/Qwen3Guard-Gen-4B at the engine's pinned revision 6ec42827..., bfloat16, sdpa, 128 new
tokens, batch 8, input limit 8192). Response moderation: GuardScorer.score([(row id, user turn, assistant turn)]), with
over-limit inputs recorded as not scored. Each record keeps the safety label, the categories and the refusal flag (the
engine's strict three-line parse), the token counts and the stop reason; the guard's answer text is never kept. Rows go
to the scorer in chunks of QWEN_CHUNK (the engine batches 8 inside a chunk, sorted by length), so the cache grows chunk
by chunk and a SIGTERM stops at the next generation batch.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402
import screen_rows as R  # noqa: E402
from common import Refusal, sha256_bytes  # noqa: E402

REASON_CODES = {"guard answer reached max_new_tokens": "capped", "guard input over limit; not scored": "over_limit",
                "control string in guard input; not scored": "control_string"}


class StopNow(Exception):
    """A SIGTERM arrived during a chunk: the chunk's results are dropped (it is judged again on a resume)."""


def load_recipe(engine_root: pathlib.Path) -> dict:
    path = pathlib.Path(engine_root) / P.RECIPE_REL
    data = path.read_bytes()
    if sha256_bytes(data) != P.RECIPE_SHA256:
        raise Refusal("the recipe config does not have its pinned SHA-256")
    recipe = json.loads(data)
    if recipe.get("guard") != P.QWEN_GUARD_SPEC:
        raise Refusal("the recipe's guard block is not the pinned Qwen3Guard spec")
    return recipe


def load_guard(engine_root: pathlib.Path, ledger_dir: pathlib.Path):      # the real scorer; never called by tests
    from experiments.safety_selection.ledger import RunLedger
    from experiments.safety_selection.loaders import real_loaders
    recipe = load_recipe(engine_root)
    loaders = real_loaders()
    device = loaders.prepare_device(recipe)
    ledger = RunLedger(ledger_dir)
    guard = loaders.guard(recipe, ledger, device)
    return guard, {"device": device, "environment": loaders.environment(device)}


def qwen_entry(row, g: dict) -> dict:
    valid = bool(g.get("valid"))
    stop = g.get("guard_stop_reason")
    return {"row_id": row.row_id, "source": row.source, "line": row.line, "response_sha256": row.response_sha256,
            "user_sha256": row.user_sha256, "valid": valid,
            "reason": None if valid else REASON_CODES.get(g.get("reason"), "unparsed"),
            "safety": g.get("safety") if valid else None,
            "categories": list(g.get("categories") or []) if valid else None,
            "refusal": g.get("refusal") if valid else None,
            "guard_input_tokens": g.get("guard_input_tokens"), "guard_output_tokens": g.get("guard_output_tokens"),
            "guard_stop_reason": stop if stop in (None, "eos", "max_new_tokens") else "other",
            "control_strings": len(g.get("control_strings") or [])}


def screen(guard, rows: list, cache, stop, log, limit: int | None = None, chunk: int = P.QWEN_CHUNK,
           clock=time.time) -> dict:
    todo, cached = [], 0
    chosen = R.selected(rows, limit)
    for row in chosen:
        entry = cache.get((row.row_id,))
        if entry is not None:
            R.check_against(entry, row, "qwen3guard cache")
            cached += 1
        else:
            todo.append(row)
    log(event="plan", step="qwen", cached=cached, todo=len(todo), rows=len(chosen))

    def check(_what):
        if stop():
            raise StopNow

    t0, n, stopped = clock(), 0, False
    for start in range(0, len(todo), chunk):
        part = todo[start:start + chunk]
        try:
            check("chunk")
            scored = guard.score([(row.row_id, row.user_turn, row.assistant_turn) for row in part], check=check,
                                 over_limit_unscored=True)
        except StopNow:
            stopped = True
            log(event="stopping_on_signal", step="qwen", judged=n)
            break
        if len(scored) != len(part) or [g.get("item_id") for g in scored] != [row.row_id for row in part]:
            raise RuntimeError("the guard returned records for other rows than it was given")
        for row, g in zip(part, scored):
            cache.append(qwen_entry(row, g))
        n += len(part)
        el = clock() - t0
        log(event="progress", step="qwen", judged=n, of=len(todo), sec_per_item=round(el / n, 3),
            eta_min=round(el / n * (len(todo) - n) / 60, 1))
    return {"judged": n, "cached": cached, "todo": len(todo), "stopped": stopped}
