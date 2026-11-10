"""Verifier scratch: real_codec's codec vs the pod's policy codec, on the recipe's own tokenizer (offline).
Synthetic text only. Prints ids, sets and verdict class names; no list/bank text is read."""
import json, sys
from pathlib import Path
WS = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(WS))
from experiments.safety_selection.config import load_recipe, tokenizer_of
from experiments.safety_selection.loaders import load_tokenizer
from experiments.safety_selection.textproc import build_codec, encode_generation_prompt, encode_train

RECIPES = {"olmo2-7b": "experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json",
           "llama31-8b": "experiments/safety_selection/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json"}

def verdict(fn):
    try:
        fn(); return "ok"
    except ValueError as e:
        return type(e).__name__

for fam, p in RECIPES.items():
    recipe = load_recipe(WS / p)
    m = recipe["model"]
    tok, _ = load_tokenizer(*tokenizer_of(recipe))
    end = m["end_of_turn_token"]
    mac = build_codec(tok, end, [end], end)                         # build_s_pool.real_codec's arguments
    pod = build_codec(tok, end, m["stop_tokens"], m["pad_token"])   # loaders.py:187's arguments
    base = frozenset(int(i) for i in tok.all_special_ids)
    from experiments.safety_selection.textproc import added_special_ids
    added = added_special_ids(tok)
    print(fam, "tokenizer", tokenizer_of(recipe)[1][:12], type(tok).__name__)
    print("  eos mac/pod", mac.eos_id, pod.eos_id, " stops mac/pod", mac.stop_ids, pod.stop_ids, " pad mac/pod", mac.pad_id, pod.pad_id)
    print("  |special| mac/pod", len(mac.special_ids), len(pod.special_ids), " pod - mac:", sorted(pod.special_ids - mac.special_ids),
          " mac - pod:", sorted(mac.special_ids - pod.special_ids))
    for t in [*m["stop_tokens"], m["pad_token"]]:
        i = tok.convert_tokens_to_ids(t)
        print(f"  token {t!r} id {i}: in all_special_ids {i in base}; in added-special {i in added}")
    # synthetic texts that hold each stop / pad token literally
    for t in sorted({*m["stop_tokens"], m["pad_token"], end}):
        text = f"Synthetic filler words then {t} and more filler."
        g = (verdict(lambda: encode_generation_prompt(mac, text, m["max_prompt_tokens"])),
             verdict(lambda: encode_generation_prompt(pod, text, m["max_prompt_tokens"])))
        tr = (verdict(lambda: encode_train(mac, "x", "Synthetic question?", text, m["max_train_tokens"])),
              verdict(lambda: encode_train(pod, "x", "Synthetic question?", text, m["max_train_tokens"])))
        print(f"  text with {t!r}: generation mac/pod {g}; train mac/pod {tr}")
    # lengths: identical by construction (prompt_ids, encode, eos_id); spot check
    for n in (10, 700, 1600):
        text = " ".join(["word"] * n)
        a = len(mac.prompt_ids(text)); b = len(pod.prompt_ids(text))
        ta = len(encode_train(mac, "x", "q", text, 10**9).input_ids); tb = len(encode_train(pod, "x", "q", text, 10**9).input_ids)
        print(f"  {n} words: prompt_ids mac/pod {a}/{b}; train ids mac/pod {ta}/{tb}")
