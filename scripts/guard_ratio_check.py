"""Worst-case Qwen3Guard tokens per policy token, per family tokenizer (review fix 1, lead decision 1; standalone,
offline, outside the engine's code identity). Prints ids and numbers only, never token text.

    python scripts/guard_ratio_check.py --guard DIR --policy NAME=DIR [--policy NAME=DIR ...] [--repeat 8]

For every policy vocabulary id that is not a special id, the id repeated --repeat times is decoded and re-encoded
with the guard tokenizer; the ratio is guard tokens / --repeat (a run of one token is the worst case for a
degenerate, capped answer). The budget is (guard.max_input_tokens - template - prompt) / max_new_tokens, by default
(8192 - 391 - 400) / 2048 = 3.61 guard tokens per answer token (the brief's Qwen bound uses 3.00). An answer over the
budget can exceed the guard's input limit; such an answer is recorded as not scored ("guard input over limit") in a
recipe with generation.guard_over_limit, and the reading bounds U both ways.
"""
import argparse
import json
from fractions import Fraction
from pathlib import Path


def ratios(policy, guard, repeat: int) -> list[tuple[int, Fraction]]:
    special = set(getattr(policy, "all_special_ids", ()))
    special |= {int(i) for i, t in (getattr(policy, "added_tokens_decoder", {}) or {}).items() if getattr(t, "special", False)}
    ids = [i for i in range(len(policy)) if i not in special]
    texts = [policy.decode([i] * repeat, skip_special_tokens=False, clean_up_tokenization_spaces=False) for i in ids]
    encoded = guard(texts, add_special_tokens=False)["input_ids"]
    return [(i, Fraction(len(e), repeat)) for i, e in zip(ids, encoded)]


def report(name: str, values: list[tuple[int, Fraction]], budget: Fraction, qwen_bound: Fraction) -> dict:
    ordered = sorted(values, key=lambda v: (-v[1], v[0]))
    worst = ordered[0][1]
    return {"family": name, "ids_checked": len(values), "max_ratio": float(worst),
            "ids_above_qwen_bound_3": sum(r > qwen_bound for _, r in values),
            "ids_above_budget": sum(r > budget for _, r in values),
            "top10": [[i, float(r)] for i, r in ordered[:10]],
            "worst_case_answer_can_exceed_limit": worst > budget}


def main(argv=None) -> int:
    from transformers import AutoTokenizer
    ap = argparse.ArgumentParser()
    ap.add_argument("--guard", required=True)
    ap.add_argument("--policy", action="append", required=True, help="NAME=DIR")
    ap.add_argument("--repeat", type=int, default=8)
    ap.add_argument("--limit", type=int, default=8192)
    ap.add_argument("--template", type=int, default=391)
    ap.add_argument("--prompt", type=int, default=400)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    a = ap.parse_args(argv)
    budget = Fraction(a.limit - a.template - a.prompt, a.max_new_tokens)
    guard = AutoTokenizer.from_pretrained(a.guard)
    out = {"guard": str(Path(a.guard)), "repeat": a.repeat, "budget_guard_tokens_per_answer_token": float(budget),
           "families": []}
    for spec in a.policy:
        name, folder = spec.split("=", 1)
        policy = AutoTokenizer.from_pretrained(folder)
        out["families"].append({"tokenizer": folder, **report(name, ratios(policy, guard, a.repeat), budget, Fraction(3))})
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
