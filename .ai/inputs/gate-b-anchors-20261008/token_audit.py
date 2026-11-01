"""Tokenizer-only mirror of the engine's token audit (prepare.py:308-313) on the 128 anchors of the FULL
file, with the prepared set's own tokenizer (offline cache; loaders.load_tokenizer). Counts only."""
import json, sys
from pathlib import Path
REPO = Path("/Users/spiderishi/Coding/attribution"); sys.path.insert(0, str(REPO))
from experiments.safety_selection.loaders import load_tokenizer
from experiments.safety_selection.textproc import build_codec, encode_train, TooLong, ControlTokenError, NoTargets
m = json.loads((REPO / "tmp/kt-prepared/prepared-kt-dolly-olmo2/manifest.json").read_bytes())
tk = m["data_config"]["tokenizer"]
print("tokenizer", tk["repo_id"], tk["revision"][:12], "eot", tk["end_of_turn_token"], "limits", tk["max_train_tokens"], tk["max_prompt_tokens"])
tok, status = load_tokenizer(tk["repo_id"], tk["revision"])
print("snapshot present", status["present"])
codec = build_codec(tok, tk["end_of_turn_token"], [tk["end_of_turn_token"]], tk["end_of_turn_token"])
full = json.loads((REPO / "tmp/gate-b-anchors/anchor_prompts.json").read_bytes())
ok, fails, max_prompt, max_total = 0, {}, 0, 0
for p in full["prompts"]:
    try:
        ex = encode_train(codec, f"anchor-{p['index']}", p["prompt"], p["unsafe_response"], tk["max_train_tokens"])
        if ex.n_prompt > tk["max_prompt_tokens"]:
            raise TooLong("prompt")
        ok += 1; max_prompt = max(max_prompt, ex.n_prompt); max_total = max(max_total, len(ex.input_ids))
    except (TooLong, ControlTokenError, NoTargets) as exc:
        fails[type(exc).__name__] = fails.get(type(exc).__name__, 0) + 1
print(json.dumps({"passed": ok, "failed_by_reason": fails, "max_prompt_tokens": max_prompt, "max_total_tokens": max_total,
                  "harmful_passed": ok >= 64 and not fails}))
