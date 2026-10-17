"""Counts only: how the OLMo 3 prompt wrapper shifts Dolly prompt and row token counts (proxy: the cached OLMo-2
tokenizer, whose merges and base ids OLMo 3 shares; the 4 function-tag tokens are single tokens in OLMo 3, so the
system block is 3 tokens shorter there). Prints no text."""
import json, os, sys, collections
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, "/Users/spiderishi/Coding/attribution")
from transformers import AutoTokenizer
from huggingface_hub import snapshot_download
from experiments.safety_selection.prepare_task import render_user_text
p = snapshot_download("allenai/OLMo-2-0425-1B-Instruct", revision="48d788eca847d4d7548f375ad03d3c9312f6139e", local_files_only=True)
tok = AutoTokenizer.from_pretrained(p, local_files_only=True)
SYS = "<|im_start|>system\nYou are a helpful function-calling AI assistant. You do not currently have access to any functions. <functions></functions><|im_end|>\n"
FUNC_FIX = 3   # <functions></functions>: 5 tokens in OLMo-2's vocabulary, 2 added tokens in OLMo 3's
def ids(x):
    return x["input_ids"] if hasattr(x, "keys") else x
deltas = collections.Counter(); newly_prompt = newly_row = 0; near = collections.Counter()
max_r2 = max_r3 = 0; n = 0
for line in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(line); n += 1
    user = render_user_text(r["instruction"], r["context"]) if "context" in r else r["instruction"]
    p2 = len(ids(tok.apply_chat_template([{"role": "user", "content": user}], tokenize=True, add_generation_prompt=True)))
    p3 = len(tok.encode(SYS + "<|im_start|>user\n" + user + "<|im_end|>\n<|im_start|>assistant\n", add_special_tokens=False)) - FUNC_FIX
    resp = len(tok.encode(r["response"], add_special_tokens=False))
    r2, r3 = p2 + resp + 1, p3 + resp + 1
    deltas[p3 - p2] += 1
    if p2 <= 1536 < p3: newly_prompt += 1
    if r2 <= 3072 < r3: newly_row += 1
    if p2 <= 1536: near[min((1536 - p2) // 8, 6)] += 1   # margin bins of 8 tokens, last bin = 48+
    if p2 <= 1536 and r2 <= 3072:
        max_r2 = max(max_r2, r2); max_r3 = max(max_r3, r3)
print(json.dumps({"rows": n, "prompt_delta_counts": dict(sorted(deltas.items())), "newly_over_prompt_limit": newly_prompt,
                  "newly_over_row_limit": newly_row, "max_row_tokens_within_limits_olmo2": max_r2, "same_rows_olmo3_proxy": max_r3,
                  "olmo2_prompt_margin_bins_of_8": dict(sorted(near.items()))}))
