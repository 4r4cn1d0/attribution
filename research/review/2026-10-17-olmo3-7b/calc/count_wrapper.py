import os, sys, json
os.environ["HF_HUB_OFFLINE"]="1"; os.environ["TRANSFORMERS_OFFLINE"]="1"
from transformers import AutoTokenizer
from huggingface_hub import snapshot_download
p = snapshot_download("allenai/OLMo-2-0425-1B-Instruct", revision="48d788eca847d4d7548f375ad03d3c9312f6139e", local_files_only=True)
tok = AutoTokenizer.from_pretrained(p, local_files_only=True)
added = {int(k): (v.content, v.special) for k, v in tok.added_tokens_decoder.items()}
print("olmo2 len(tokenizer)", len(tok), "added", len(added))
print("olmo2 im tokens:", {i: c for i, (c, s) in added.items() if "im_" in c}, "special flags:", {c: s for i, (c, s) in added.items() if "im_" in c})
X = "Placeholder text for counting."
own = tok.apply_chat_template([{"role": "user", "content": X}], tokenize=True, add_generation_prompt=True)
own = own["input_ids"] if hasattr(own, "keys") else own
base = tok.encode(X, add_special_tokens=False)
print("olmo2 wrapper tokens (own template):", len(own) - len(base))
sys_text = "<|im_start|>system\nYou are a helpful function-calling AI assistant. You do not currently have access to any functions. <functions></functions><|im_end|>\n"
user_open, user_close, gen = "<|im_start|>user\n", "<|im_end|>\n", "<|im_start|>assistant\n"
n = lambda s: len(tok.encode(s, add_special_tokens=False))
w3 = n(sys_text) + n(user_open) + n(user_close) + n(gen)
print("olmo3-style wrapper tokens (olmo2 BPE, im tokens as added tokens):", w3, "system block alone:", n(sys_text))
print("functions tags tokens in olmo2:", n("<functions></functions>"))
