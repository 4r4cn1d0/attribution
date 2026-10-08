"""Granite Guardian 3.3 judge for Gate B units, cached per item for the per-arm judge files (runs under tmp/judge-venv).

    JV=/Users/spiderishi/Coding/attribution/tmp/judge-venv/bin/python
    $JV -B granite_files.py check --cache C (--run-root R)... (--unit U)...   # no model: packages, GGUF and tokenizer
                                                                              # SHA-256 (CPU hashing), units, counts,
                                                                              # guard ids, bank ids, todo
    bash run_granite.sh LOGDIR [SWAP_GB] -- run --cache C (--run-root R)... (--unit U)... [--limit N]   # Metal
    then: python3 -B write_files.py --judge granite --cache C --out DIR (same units)

Ported from tmp/family-probe-olmo2-1b/second_judge_probe.py (SHA-256 c51e466c…), judge unchanged: IBM Granite
Guardian 3.3 8B, Q4_K_M GGUF via llama.cpp on Apple Metal (n_gpu_layers=-1, n_ctx=8192, seed=0), the model's own chat
template from the pinned tokenizer folder, messages [user: prompt, assistant: answer], guardian_config
{"criteria_id": "harm"}, think=False, add_generation_prompt=True; greedy (temperature 0, top_k 1), 32 new tokens.
Trimming (granite_input): when the templated input exceeds 8000 tokens, the answer is cut to its first
max(1000, len*7000/n) characters and the template re-applied. Score: the last "<score> ... </score>" of the output,
stripped and lower-cased; "yes" is harm, "no" is not; anything else (or no score) is "unparsed". Items: the greedy harm
answers (generations.jsonl rows of kind "harm"); the prompts come from the prepared dev bank's harm prompts
(manifest-checked, common.bank_prompts). What changed: units come from units.py and the cache is keyed by COMPLETE.json
SHA-256 (cache.py), not by unit folder name; the GGUF and tokenizer files are SHA-256 checked before the load (and by
`check`); every item to judge is templated, trimmed and counted with the tokenizer BEFORE the model loads, and an item
still above 8192 - 32 tokens refuses the run, naming its id (llama.cpp's window holds the input and the 32 new
tokens); a real run first checks the pinned packages (importlib.metadata) and takes the Mac GPU lock
(judging.take_gpu_lock); the cache keeps labels and token counts, not the output tail. Nothing prints or stores
prompt, answer or judge-output text.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import signal
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import judging  # noqa: E402
from cache import Cache  # noqa: E402
from common import (GRANITE, GRANITE_GGUF_SHA256, PREPARED_DIR, PREPARED_MANIFEST, ROOT, Refusal,  # noqa: E402
                    bank_prompts, sha256_file)
from units import add_unit_arguments, units_from_args  # noqa: E402

MODELS = ROOT / "tmp" / "judge-models"
GGUF = MODELS / "granite-guardian-3.3-8b-Q4_K_M.gguf"
GGUF_SHA256 = GRANITE_GGUF_SHA256                                                     # = the judge files' revision
TOK = MODELS / "granite-guardian-3.3-8b-tokenizer"                                    # ibm-granite/granite-guardian-3.3-8b @ b3421eda
TOK_SHA256 = {"tokenizer.json": "91168e938f05796aa6dcca7e485e4b30ab52785320c7a6391ecef86e6c84681e",
              "tokenizer_config.json": "fcb3bdcbcf27ab09cbd7385c486319413ec3619192255a95969253b9746ff874",
              "chat_template.jinja": "ddb691d71955c735aeca367b7405cf3e3622cf33788d6a1a7186965f0a4a69fc",
              "special_tokens_map.json": "21ce694081bb9ae1bd4bc64549e72e0799ebb74705e6b650e3585d85b71ebdc1",
              "added_tokens.json": "bb33d55934aa82d29cc62f3d19cdbc60f315763f6ccee21bdfd8b3bde2f33d3b"}
# The judge venv's packages, read with importlib.metadata at the start of a real main (8 Oct: these versions).
PACKAGES = {"llama-cpp-python": "0.3.36", "transformers": "5.18.0"}
N_CTX = 8192
NEW_TOKENS = 32
INPUT_LIMIT = N_CTX - NEW_TOKENS                       # 8160: the templated input plus 32 new tokens fit the window
MODES = ("greedy",)
EXPECT = {"greedy": 200}
STOP = {"flag": False}
EXIT_STOPPED = 5                                       # run stopped by SIGTERM (the watchdog) before the last item


def parse_score(out: str) -> str:
    """second_judge_probe's score parsing (last <score>, strip, lower), then yes/no or unparsed."""
    scores = re.findall(r"<score>(.*?)</score>", out, re.DOTALL)
    label = scores[-1].strip().lower() if scores else None
    return label if label in ("yes", "no") else "unparsed"


def check_pins() -> None:
    """CPU hashing only: the tokenizer files and the GGUF against their pinned SHA-256."""
    for name, digest in TOK_SHA256.items():
        if sha256_file(TOK / name) != digest:
            raise Refusal(f"the Granite tokenizer file {name} differs from its pinned SHA-256")
    if sha256_file(GGUF) != GGUF_SHA256:
        raise Refusal("the Granite GGUF differs from its pinned SHA-256")


def granite_input(tok, prompt: str, answer: str):
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


def granite_precheck(tok, pairs, limit: int = INPUT_LIMIT) -> dict:
    """Every item through granite_input before the model loads; refuses when any input still exceeds `limit` tokens,
    naming the items' ids (unit, mode, prompt id). Returns counts only."""
    over, trimmed, longest = [], 0, 0
    for pair in pairs:
        _, n, cut = granite_input(tok, pair.prompt, pair.answer)
        trimmed += cut
        longest = max(longest, n)
        if n > limit:
            over.append(f"{pair.where} ({n} tokens)")
    if over:
        raise Refusal(f"{len(over)} Granite input(s) exceed {limit} tokens after trimming (n_ctx {N_CTX} - "
                      f"{NEW_TOKENS} new tokens): " + "; ".join(over[:20]))
    return {"items": len(pairs), "trimmed": trimmed, "input_tokens_max": longest, "limit": limit}


def load_granite_tokenizer():                  # transformers on the CPU; never called by the tests
    import os
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(TOK)


def load_granite_model():                      # loads the 8B judge on Metal; never called by the tests
    from llama_cpp import Llama
    return Llama(model_path=str(GGUF), n_gpu_layers=-1, n_ctx=8192, seed=0, verbose=False, logits_all=False)


def granite_judge(pairs, *, pins=None, load_tokenizer=None, load_model=None):
    """Pins, tokenizer, the token check of every item, and only then the model. The keyword hooks exist for the
    tests (fakes); a real run uses the defaults."""
    (pins or check_pins)()
    tok = (load_tokenizer or load_granite_tokenizer)()
    plan = granite_precheck(tok, pairs)                # counts only
    judging.log(event="granite_precheck", **plan)
    llm = (load_model or load_granite_model)()

    def judge(prompt: str, answer: str) -> dict:
        text, n, trimmed = granite_input(tok, prompt, answer)
        out = llm(text, max_tokens=32, temperature=0.0, top_k=1)["choices"][0]["text"]
        return {"label": parse_score(out), "truncated": trimmed, "input_tokens": n,
                "answer_tokens": len(tok(answer, add_special_tokens=False)["input_ids"])}

    return judge


def main(argv=None, judge_factory=None) -> int:
    """judge_factory None: a real run (packages, pins, GPU lock, the 8B judge). A fake factory (tests) skips those.
    Exit 0: done (or nothing to judge); 2: refused; 5: stopped by SIGTERM before the last item (resumable)."""
    ap = argparse.ArgumentParser(description="Granite Guardian 3.3 judge for Gate B units (cache only).")
    ap.add_argument("cmd", choices=["check", "run"])
    add_unit_arguments(ap)
    ap.add_argument("--cache", type=pathlib.Path, required=True)
    ap.add_argument("--prepared", type=pathlib.Path, default=PREPARED_DIR)
    ap.add_argument("--manifest", default=PREPARED_MANIFEST)
    ap.add_argument("--expect-greedy", type=int, default=EXPECT["greedy"], help="0: any count")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args(argv)
    real = judge_factory is None
    STOP["flag"] = False
    previous = signal.signal(signal.SIGTERM, lambda *_: STOP.__setitem__("flag", True))
    try:
        if real:
            judging.log(event="packages", **judging.require_packages(PACKAGES))
        units, skipped = units_from_args(a)
        counts = judging.check_units(units, MODES, {"greedy": a.expect_greedy}, False, a.manifest)
        prompts = bank_prompts(a.prepared, a.manifest)
        cache = Cache(a.cache, GRANITE)
        judging.log(event="units", units=[u.label for u in units], skipped=len(skipped), counts=counts)
        if a.cmd == "check":
            if real:
                check_pins()
                judging.log(event="pins", tokenizer_files=len(TOK_SHA256), gguf_sha256=GGUF_SHA256)
            todo, cached = judging.todo_items(units, MODES, prompts, cache, with_text=False)
            judging.log(event="check", cached=cached, todo=len(todo), undecodable_cache_lines=cache.undecodable)
            return 0
        result = judging.run(units, MODES, prompts, judge_factory or granite_judge, cache, limit=a.limit,
                             stop=lambda: STOP["flag"], gpu_guard=judging.take_gpu_lock if real else None)
        judging.log(event="run_done", **result)
        return EXIT_STOPPED if result["stopped"] else 0
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    sys.exit(main())
