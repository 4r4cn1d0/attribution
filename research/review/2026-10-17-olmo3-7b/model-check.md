# OLMo 3 7B Instruct: model check

**Status: CHECK ONLY. It adopts nothing.** Written 2026-10-17, about 07:15–07:50 UTC (clock checked with `date -u` at 07:41 and 07:43 UTC) by an Opus worker for the main-study lead (GI VI). Read-only work. No repo edit, commit, pod, spend, install or weight download. This file is the only output.

**Why.** A user decision is pending: add OLMo 3 7B Instruct as a third 7–8B model if money allows. It is the first 7–8B model to cut if money is short (after 70B and 32B). This file checks the model: its exact id, its safety training, its architecture and tokenizer, and how well the engine and kits support it.

**Labels.** **R** = read (a URL with the read date, or `path:line`). **M** = measured here (a command I ran; output quoted). **E** = estimate (basis follows). **I** = inference from R or M. All web reads were on 2026-10-17 UTC. Hashes that came through the WebFetch summarizer are marked "(WF)". Re-read them with the Hub API before you pin them.

**Where I read the repo.** The files that the brief names (the re-plan, `research/review/2026-10-17-icml-78b-prep/`, `scripts/cuda_preflight_family.py`, the family tests) are in the main checkout `/Users/spiderishi/Coding/attribution` at HEAD `0294d1b`. The worktree is at `37debcd` and does not have them. I read the main checkout. I did not change it.

## 0. Summary

- **The exact model.** `allenai/Olmo-3-7B-Instruct`. Main today is `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc` (2026-06-25). The weights have not changed since commit `d42dc9de51ee481e02b8a35d8222b86c6d7c5b20` (2025-11-20). Apache-2.0. Not gated. 7,298,011,136 bf16 values in 3 shards (14.60 GB). Released 20 Nov 2025 (R, §1).
- **It has a real safety stage, in SFT and DPO only.** SFT has about 110k safety prompts (CoCoNot, WildGuardMix, WildJailbreak; 5.1% of 2.15 M). DPO has about 26.7k (10.3% of 259,922 pairs). RL has no safety data and no safety reward. The Instruct SFT also starts from the Think SFT checkpoint, which had about 89.6k safety prompts (R, §3).
- **RL lowered its safety score a little.** The paper's 7B "Safety" average: SFT 89.5, DPO 89.9, final 87.6. OLMo-2-7B-Instruct: 91.1. HarmBench refusal: final 94.9, OLMo-2-7B 88.8 (R, paper Tables 26 and 53).
- **The architecture shapes equal OLMo-2-7B's.** 32 layers, hidden 4,096, MLP 11,008, 32 query heads and 32 key/value heads (no grouped-query attention). The LoRA r64 count is the same, 159,907,840 (I). The differences: class `Olmo3ForCausalLM`, sliding-window attention (4,096) in 24 of 32 layers, YaRN RoPE scaling, 65,536 positions, and no padding rows in the embedding (R, §4).
- **The tokenizer is close to OLMo-2's, but not the same.** The BPE merges are byte-identical. The special-token ids are the same. Four added tokens changed (function-call tags). The chat template is completely different: ChatML-style special-token markers, no BOS, and a default system message that is inserted when no system message is given (R and M, §5).
- **Three blockers in the current engine environment and kits** (I, §6):
  1. **Environment.** The pinned lock has transformers 4.56.2. That version has no `olmo3` model code. The model needs transformers ≥ 4.57.0. A new lock is needed for this model only.
  2. **Download patterns.** The chat template is in a separate file, `chat_template.jinja`. The kit patterns do not fetch it. The tokenizer then has no template, and the loader refuses.
  3. **Preflight verdict.** The chat-row check needs padding rows or `<|reserved_special_token_N|>` rows. OLMo 3 has neither. So `chat_rows_distinct` is null and `use_this_recipe` is false on every candidate.
- **No engine `.py` change seems necessary** (I). The codec, the template probe, the assistant-header check and the token audit are generic. They accept this tokenizer once the template file is present. The model needs its own data config, its own prepared set and its own recipes. It cannot reuse the OLMo-2 tokenizer pin, as OLMo-2-7B does.
- **It is a third family, not a third OLMo-2 size.** OLMo 3 has no 1B model. The per-family LR rule needs its own Gate A ladder on it. That is about $8–10 for rung 1 (E, §7).

## 1. Identity of the checkpoint

| Field | Value | Label, source |
|---|---|---|
| Hugging Face id | `allenai/Olmo-3-7B-Instruct` | R, https://huggingface.co/api/models/allenai/Olmo-3-7B-Instruct |
| Main commit today | `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc`, 2026-06-25T21:41:37Z, "Update the number of parameters (#13)" (README only) | R, same API (`sha`) and https://huggingface.co/api/models/allenai/Olmo-3-7B-Instruct/commits/main (the two agree) |
| Weights commit | `d42dc9de51ee481e02b8a35d8222b86c6d7c5b20`, 2025-11-20T00:35:15Z, "Upload checkpoint from step 450" | R, commits list |
| Weights unchanged since then | The three shard LFS SHA-256 values and sizes are the same at `d42dc9de…` and at main. So are `tokenizer.json`, `tokenizer_config.json`, `vocab.json`, `merges.txt`, `special_tokens_map.json` and `chat_template.jinja` (git blob ids) | R (WF), https://huggingface.co/api/models/allenai/Olmo-3-7B-Instruct/tree/main and `/tree/d42dc9de…` |
| Changes after the weights | `config.json`: `beta_fast` 32 → 32.0 and `beta_slow` 1 → 1.0 (commit `51c1f0b2…`, 2025-11-26); `generation_config.json`: sampling defaults and `do_sample` added; `model.safetensors.index.json` +4 bytes; README and citation | R, commit pages `51c1f0b2…`, `48683dfc…`; tree diff |
| Shard SHA-256 (LFS) | `e7bd4c8ba52177a815aee5929cb458a116a65799688d3e51402500a1cb77023c` (4,969,984,976 B); `ea92aa0499a2ca02400e5d87324009e172bdbfb9809f2ac501485d8224382328` (4,981,161,496 B); `d50f95e4f2ec5fc4fbce6217cbf54fd1d700928b05e5550c8ee08bf4ba948925` (4,644,917,240 B) | R (WF), tree API; identical in both tree reads |
| Total weight bytes | 14,596,063,712 B (14.60 GB). OLMo-2-7B: 14.61 GB | M (my sum); R, `78b-kit-cap-rule.md` §9 |
| Values | 7,298,011,136 (BF16) | R, API `safetensors.total`; M: my per-layer arithmetic gives exactly this number (§4) |
| Licence | Apache-2.0. The card says the model is "intended for research and educational use" under Ai2's Responsible Use Guidelines. The card names no third-party terms | R, API `cardData`; https://huggingface.co/allenai/Olmo-3-7B-Instruct |
| Gated | No (`gated: false`, `private: false`, `disabled: false`) | R, API |
| Repo created | 2025-11-19T20:49:53Z | R, API |
| Announcement | 20 Nov 2025 (Ai2 blog) | R, https://allenai.org/blog/olmo3 |
| Report | "Olmo 3", Team Olmo, arXiv 2512.13961; v1 15 Dec 2025, v2 14 Apr 2026 | R, https://arxiv.org/abs/2512.13961 |
| Parent | `allenai/Olmo-3-7B-Instruct-DPO`; RL data `allenai/Dolci-Instruct-RL-7B` | R, API `cardData` |
| Transformers | "Olmo 3 is supported in transformers 4.57.0 or higher"; `config.json` was saved with 4.57.1 | R, model card; `config.json` |
| Downloads, likes | 475,609; 159 | R, API |

## 2. The OLMo 3 7B family on the Hub

All are under `allenai`, Apache-2.0, not gated where I checked. Every 7B checkpoint I checked has 7,298,011,136 values and class `Olmo3ForCausalLM`.

| Stage | Instruct line | Think line | Label, source |
|---|---|---|---|
| Base (pretrain → midtrain → long context) | `allenai/Olmo-3-1025-7B` (sha `a81bae42db3975be1671e27b9c9a56da1a9f980f`; tokenizer has no BOS token) | same base | R, https://huggingface.co/api/models/allenai/Olmo-3-1025-7B |
| SFT | `allenai/Olmo-3-7B-Instruct-SFT` (sha `e1452fc572d51966ff4aaeb25118b891eb93e549`; data `Dolci-Instruct-SFT`, `Dolci-Instruct-SFT-Tool-Use-SA`) | `allenai/Olmo-3-7B-Think-SFT` | R, API pages |
| DPO | `allenai/Olmo-3-7B-Instruct-DPO` (sha `b33130b7de49f0c2553b5c2b3bc8409ff3e627d1`) | `allenai/Olmo-3-7B-Think-DPO` | R, API pages |
| RL (final) | **`allenai/Olmo-3-7B-Instruct`** (sha above) | `allenai/Olmo-3-7B-Think` (sha `d97e442d7cc678210054dbcc9b440894d62c89a4`) | R, API pages |
| RL from base (no SFT) | `Olmo-3-7B-RL-Zero-{General, IF, Math, Code, Mix}`, `Olmo-3.1-7B-RL-Zero-{Code, Math}` | — | R, https://huggingface.co/api/models?author=allenai&search=Olmo-3&limit=200 and `&filter=olmo3` |

- There is no `Olmo-3.1-7B-Instruct`. The 3.1 refresh exists for the 32B models and two 7B RL-Zero models only (R, the two listings). Two other 2026 repos are not OLMo 3: `allenai/Olmo-Hybrid-*-7B` (a different model line; SFT and DPO only seen) and `allenai/olmo-3-tokenizer-instruct-release` (a separate tokenizer repo whose `vocab.json` and `tokenizer.json` differ from the model's; do not use it for this model) (R, https://huggingface.co/api/models?author=allenai&search=olmo&sort=createdAt&direction=-1&limit=40; its tree API).
- **Metadata slip (R):** the Instruct-DPO card metadata names `allenai/Dolci-Think-DPO-7B` as its data. The paper (§5.3) and the final model's card name Dolci Instruct DPO. I trust the paper.
- **Why Instruct and not Think (I):** Think writes long reasoning traces. Ai2 evaluates it with up to 32,768 new tokens (R, paper Table 15 caption). The engine caps answers at 2,048 tokens, so most Think answers would be cut. Instruct is "tuned to produce shorter, more direct responses" (R, paper §1).
- **32B note (I):** if OLMo 3 is added at 7B, `allenai/Olmo-3.1-32B-Instruct` uses the same new environment. The 32B design rejected it only for "new environment and a different family" (R, `32b-70b-design.md`:45). That reason becomes weaker if the OLMo 3 lock exists anyway.

## 3. Post-training pipeline and the safety stage

Source: the OLMo 3 report v2 (the PDF from https://arxiv.org/pdf/2512.13961v2, read page by page), the model cards, and the Dolci dataset cards. I read only card text and tables. I opened no dataset row.

**Pipeline (R, paper §2.2, Fig. 2; §5).** Base → Instruct SFT → Instruct DPO → Instruct RL (RLVR) = Olmo 3 Instruct. The Instruct SFT run **starts from the Olmo 3 Think SFT checkpoint**, as a "warm-start" (R, §5.2.2).

| Stage | Safety data? | Numbers | Label, source |
|---|---|---|---|
| Think SFT (the warm start) | Yes | CoCoNot 10,227; WildGuardMix 38,315; WildJailbreak 41,100 (7B counts) of 2,268,468 prompts | R, paper Table 17 |
| Instruct SFT | **Yes** | CoCoNot 10,957; WildGuardMix 49,373; WildJailbreak 49,965 = 110,295 of 2,152,112 (5.1%) | R, paper Table 30 (category "Safety"); the same counts on https://huggingface.co/datasets/allenai/Dolci-Instruct-SFT |
| Instruct DPO | **Yes** | CoCoNot 2,203; WildGuardMix 12,037; WildJailbreak 12,431 = 26,671 of 259,922 (10.3%). Pairs come from delta learning (chosen from Qwen3-32B, rejected from Qwen3-0.6B, thinking off) and a "delta-aware" GPT-4.1 judge pipeline | R, paper Table 30, §5.3.1; https://huggingface.co/datasets/allenai/Dolci-Instruct-DPO |
| Instruct RL | **No** dedicated safety data or reward | 171,950 prompts: precise instruction following, math, code, general chat (Tulu 3 SFT 18,955; WildChat 18,761; Multi-Subject RLVR 12,234). Rewards: verifiers, and an LM judge for chat quality | R, paper Table 20 ("Used in Instruct RL" column), §4.4.1, §5.4 |

- **What "safety data" means here (I).** The three sources are the Tülu 3 safety and non-compliance sets. The paper cites them as Brahman et al. 2024, Han et al. 2024 and Jiang et al. 2024 under the category "Safety" (R, Table 30). So the model learned to refuse in SFT and DPO. RL then optimized other skills with no safety term. The general-chat RL prompts may hold some harmful requests, but the paper does not say so.
- **Safety scores by stage, 7B Instruct (R, paper v2 Table 26, mean of 3 runs).** Safety average: SFT 89.5, DPO 89.9, **final 87.6**. Baselines in the same table: OLMo 2 7B Instruct 91.1; Qwen 3 8B 78.4; Granite 3.3 8B 74.3.
- **The model card shows other numbers (R).** Card: SFT 89.2, DPO 90.2, final 87.3, OLMo 2 7B 93.1, Qwen 3 8B 78.0. The blog also shows 87.3. I think the card shows the v1 numbers. Cite the paper v2 table, and say which one you use.
- **Per benchmark, final 7B Instruct against OLMo-2-7B-Instruct (R, paper Table 53).** HarmBench 94.9 vs 88.8; DoAnythingNow 75.2 vs 92.0; WildJailbreak harmful 69.1 vs 76.8; WildGuard-Test 99.6 vs 99.2; XSTest 93.2 vs 93.9; StrongReject 88.1 vs 89.4. Over the stages HarmBench rose (87.7 → 94.3 → 94.9), and the jailbreak sets fell (DAN 90.0 → 82.9 → 75.2; WildJailbreak harmful 80.9 → 72.5 → 69.1).
- **The safety suite (R, paper App. A.8.2).** Development: HarmBench, DoAnythingNow, XSTest, WildGuard-Test, WildJailbreak-Test, TrustLLM-JailbreakTrigger. Held out: Toxigen, StrongReject, WMDP, BBQ. Most are scored with the WildGuard classifier, at temperature 0.7 and top-p 0.95.
- **What this means for the study (I).**
  - Direct harmful requests are refused at least as often as on OLMo-2-7B (HarmBench 94.9 against 88.8). So the untuned harm rate U is probably low, as on OLMo-2-7B (U 1.83%, FOCUS 10 Oct 16:40 UTC), and erosion has room to show. This is a prediction, not a measurement.
  - The final checkpoint already went through a non-safety RL stage that lowered the safety average by 2.3 points. That is a small published example of the study's question. The paper does not call it erosion.
  - OLMo 2 Instruct also had safety data in SFT. The OLMo 3 Instruct SFT mix "builds upon our OLMo 2 Instruct mixture" (R, §5.2). So the two OLMo models are a "same lab, newer data and recipe" contrast. They are not a "with against without safety training" contrast.

## 4. config.json against OLMo-2-7B-Instruct

Sources: https://huggingface.co/allenai/Olmo-3-7B-Instruct/raw/main/config.json and https://huggingface.co/allenai/OLMo-2-1124-7B-Instruct/raw/main/config.json (R). OLMo-2-7B main is still `470b1fba1ae01581f270116362ee4aa1b97f4c84`, the revision that the recipes pin (R, its API page; `configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json`).

| Field | OLMo-2-1124-7B-Instruct | Olmo-3-7B-Instruct | Matters for the engine? |
|---|---|---|---|
| `architectures`, `model_type` | `Olmo2ForCausalLM`, `olmo2` | `Olmo3ForCausalLM`, `olmo3` | Yes: needs transformers ≥ 4.57.0 (§6, B1) |
| Layers, hidden, MLP | 32, 4,096, 11,008 | 32, 4,096, 11,008 | Same shapes |
| Query / key-value heads | 32 / 32 (MHA) | 32 / 32 (MHA) | Same KV cache: 524,288 B per token in bf16 (M, arithmetic) |
| `vocab_size` (embedding rows) | 100,352 (74 padding rows above the 100,278 tokens) | **100,278** (0 padding rows) | Yes: the preflight chat-row check (§6, B3) |
| `tie_word_embeddings` | false | false | — |
| `max_position_embeddings` | 4,096 | 65,536 | No: jobs use ≤ 1,536 + 2,048 = 3,584 tokens |
| RoPE | θ 500,000, no scaling | θ 500,000; **YaRN**: factor 8.0, original 8,192, `attention_factor` 1.2079, `beta_fast` 32.0, `beta_slow` 1.0 | Static frequencies, applied at every length; needs YaRN support in the library (I) |
| Attention pattern | full in all layers | **sliding window 4,096** in 24 layers, full in every 4th layer (`layer_types`) | No effect on outputs at ≤ 4,096 tokens; no memory saving either (I) |
| `rms_norm_eps` | 1e-6 | 1e-6 | — |
| `eos_token_id` (config) | 100257 | 100257 | — |
| `generation_config.json` eos | (not read) | `[100265, 100257]` (`<|im_end|>`, `<|endoftext|>`); sampling 0.6 / 0.95; 32,768 new tokens | The engine ignores this file; its own loop decodes (I, `engine.py`:536-562) |
| `pad_token_id` | 100277 | 100277 | — |
| `use_cache` | false | false | No: the engine passes `use_cache=True` (R, `engine.py`:536, 561) |
| Values (Hub) | 7,298,617,344 | 7,298,011,136 | The difference is exactly 2 × 74 × 4,096 (M, arithmetic) |
| `transformers_version` | 4.47.0.dev0 | 4.57.1 | — |

**Arithmetic check (M, `python3 -I` on the Mac, no weights).** Per layer: 4·4096² + 3·4096·11008 + 4·4096 (post-attention, post-MLP, q_norm, k_norm) = 202,391,552. Thirty-two layers + 2 × vocab × 4,096 + 4,096 gives 7,298,617,344 for vocab 100,352 and 7,298,011,136 for vocab 100,278. Both equal the Hub counts. So the OLMo 3 embedding has exactly 100,278 rows and the blocks have the OLMo-2 shapes. LoRA r64 on the seven targets: 64 × 32 × (4·8,192 + 2·15,104 + 15,104) = **159,907,840**. That equals the OLMo-2-7B recipe count (R, `test_ss_family_recipes.py`:24). It still needs the meta-device check (`scripts/family_lora_count.py`), which needs transformers ≥ 4.57 (I).

**Memory (I).** The shapes and the KV cache are the same as OLMo-2-7B's. Sliding windows do not shorten a sequence of ≤ 3,584 tokens. So expect the OLMo-2-7B memory: micro-batch 2 × accumulation 64, generation at about 99% of the card's memory reserved, 204 allocator retries in the full-length check (R, `78b-kit-cap-rule.md` §6). The OLMo-2-7B ladder (mb4 out of memory, mb2 passed) is the right prior. Only a preflight measures it.

## 5. Tokenizer and chat template

Sources: https://huggingface.co/allenai/Olmo-3-7B-Instruct/raw/main/tokenizer_config.json, `/raw/main/chat_template.jinja`, the tree API (R); the local OLMo-2-0425-1B-Instruct snapshot `48d788ec…` in `~/.cache/huggingface/hub` (M). The OLMo-2-7B recipes use this 1B snapshot as their tokenizer (R, recipe `model.tokenizer`).

**Byte identity against the OLMo-2 tokenizer (M).** I computed git blob ids of the local OLMo-2 files with `git hash-object` and compared them with the Hub tree's `oid` values for OLMo 3:

| File | OLMo-2 1B (local) | OLMo 3 7B Instruct (Hub) | Same? |
|---|---|---|---|
| `merges.txt` | 916,646 B, `354558ed…` | 916,646 B, `354558ed…` | **Yes** |
| `special_tokens_map.json` | 581 B, `9d133a8f…` | 581 B, `9d133a8f…` | **Yes** |
| `vocab.json` | 1,611,056 B, `51135344…` | 1,611,055 B, `9c2954b1…` | No |
| `tokenizer.json` | 7,137,177 B, `5fe17212…` | 7,137,175 B, `54b3f7c4…` | No |
| `tokenizer_config.json` | 4,884 B (has `chat_template`) | 4,318 B (no `chat_template` key) | No |
| `chat_template.jinja` | — | 2,613 B | New file |

**Added tokens (R for OLMo 3, M for OLMo-2).** Both have 22 added tokens, ids 100256–100277. So both tokenizers have 100,278 tokens (I).

| Id | OLMo-2 | OLMo 3 Instruct | Special flag |
|---|---|---|---|
| 100257 | `<|endoftext|>` | same | special; BOS = EOS = UNK in both `tokenizer_config.json` files |
| 100258–100260 | FIM tokens | same | special |
| 100261–100263 | `|||PHONE_NUMBER|||` and two other PII tags | same | not special |
| 100264, 100265 | `<|im_start|>`, `<|im_end|>` | same | special |
| **100266–100269** | `<|extra_id_1|>` … `<|extra_id_4|>` | **`<functions>`, `</functions>`, `<function_calls>`, `</function_calls>`** | not special in both |
| 100270–100275 | `<|extra_id_5|>` … `<|extra_id_10|>` | renamed `<|extra_id_1|>` … `<|extra_id_6|>` | not special |
| 100276, 100277 | `<|endofprompt|>`, `<|pad|>` | same | special |

- The renames explain the 1-byte `vocab.json` difference (the four function tags have the same total length as the four old names; `<|extra_id_10|>` → `<|extra_id_6|>` is one character shorter) (I).
- The base BPE (ids 0–100255) should be the same, because the merges are identical. Plain text then tokenizes the same, except text that contains a function tag (I).
- **Risk (I).** The function tags are added tokens that are not flagged special. The tokenizer still matches them inside plain text. The codec's control-token check counts only special ids (`textproc.py`:116-133, 173-181), so a data row with a literal `<functions>` would encode to one hidden control id without a refusal. The OLMo-2 data config handled the same risk for `|||PHONE_NUMBER|||` with the forbidden substring `|||` (R, `study-kt-data-dolly-olmo2.json` amendment 1). For OLMo 3, add `<function` and `</function` to the forbidden substrings.
- The paper says the Instruct tokenizer was extended "with dedicated special tokens" for these tags (R, §5.2.1). The released file marks them not special (R, `tokenizer_config.json`). Trust the file.
- Other `tokenizer_config.json` fields (R): `tokenizer_class` `GPT2Tokenizer`, `model_max_length` 65,536, `clean_up_tokenization_spaces` false, `add_prefix_space` false; no `add_bos_token` key.

**Chat template structure (R; I describe it and do not paste it).**

| Part | OLMo-2 (1B snapshot, used by the OLMo-2-7B recipes) | OLMo 3 7B Instruct |
|---|---|---|
| Where | `chat_template` key in `tokenizer_config.json` (508 characters) | separate `chat_template.jinja` (2,613 bytes) |
| Start | BOS `<|endoftext|>` | **no BOS** |
| Role markers | plain text `<|system|>\n`, `<|user|>\n`, `<|assistant|>\n` (not special tokens; each message ends with a newline) | special tokens: `<|im_start|>` + role + `\n` … `<|im_end|>\n` (ChatML style) |
| Roles | system, user, assistant | system, user, assistant, environment; `tool` renders as `environment` |
| Default system message | none | **Yes, when no message has role `system`**: one `<|im_start|>system` block that says the model is a helpful function-calling assistant and that it has no functions, followed by an empty `<functions></functions>` pair. With tools, the block lists the tools as JSON inside `<functions>` tags |
| End of an assistant turn | eos_token (`<|endoftext|>`) on every assistant turn; a newline after it unless the turn is last | `<|im_end|>\n` if the turn is **not** last; **eos_token (`<|endoftext|>`) if it is last** |
| Generation prompt | `<|assistant|>\n` | `<|im_start|>assistant\n` (the same string as Qwen's header) |
| Function calls | — | inside `<function_calls>` … `</function_calls>`, as `name(key=json, …)` lines |
| Clock or date | no | no (`strftime_now` absent) |
| `<think>` tags | no | no |

- The Ai2 tokenizer repo states the same end-of-turn rule: each message ends with `<|im_end|>`, and a final assistant message ends with `<|endoftext|>` instead (R, https://huggingface.co/allenai/olmo-3-tokenizer-instruct-release/raw/main/README.md). So in SFT data, a one-turn answer ends with `<|endoftext|>` (I).
- **What the engine's one-turn prompt becomes (I).** The engine renders `[{"role": "user", …}]` with `add_generation_prompt=True` (R, `textproc.py`:68-72). Under OLMo 3 the result is: the default system block, then `<|im_start|>user\n` + text + `<|im_end|>\n`, then `<|im_start|>assistant\n`. Every prompt therefore carries the default system block. It is about 25 tokens (E: two short sentences plus about 7 marker and tag tokens; not tokenized here, because no tokenizer library is installed on the Mac). The OLMo-2 overhead is about 10 tokens (E).

## 6. Fit with the engine and the kits

### 6.1 What works without change (I, from the code)

- **Recipe validation** accepts any architecture string, end-of-turn token, stop tokens, pad token and assistant header (R, `config.py`:483-514). The loader checks that the loaded class name equals the recipe's `architecture` (R, `loaders.py`:162-163). `"Olmo3ForCausalLM"` passes once the class exists.
- **Codec** (R, `textproc.py`:90-133). `<|endoftext|>` is the OLMo 3 unknown token too; `single_token_id` already accepts the tokenizer's own unknown token (the OLMo-2 case). `<|im_end|>`, `<|endoftext|>` and `<|pad|>` are single special tokens. The template does not read the clock.
- **Assistant-header check** (R, `textproc.py`:139-151). The probe render ends with `<|im_start|>assistant\n`. The render with the generation prompt minus the render without it is exactly that header. The default system block is the same in both renders, so it does not break the check.
- **Token audit** (R, `prepare.py`:539-575). It works with any codec. The separate-against-joint comparison includes the last target token (`prepare.py`:551). The joint render ends a final assistant turn with `<|endoftext|>`. So with end-of-turn `<|endoftext|>` the counts stay meaningful. With `<|im_end|>`, every row would count as a mismatch (I). That is a count, not a refusal.
- **Chat-token derivation** (R, `cuda_preflight_family.py`:85-91). The joint render's special ids would be `<|im_start|>` 100264, `<|im_end|>` 100265 and `<|endoftext|>` 100257 (I). The function tags are not special, so they are not chat tokens.
- **BOS record** (R, `cuda_preflight_family.py`:478-489). It runs only when prompts start with BOS. The OLMo 3 template has no BOS, so there is no record. That is correct for this model.
- **Generation.** The engine passes `use_cache=True` and explicit `position_ids` with left padding (R, `engine.py`:536-562). With sequences under the 4,096 window, sliding layers act like full layers (I). The left-padding and batch checks of the preflight still apply. At OLMo-2-7B, greedy batch-32 answers already differed from one-at-a-time answers (R, `32b-70b-design.md` §3), so expect the same here.
- **LoRA targets.** `Olmo3` keeps the OLMo-2 module names (`q_proj` … `down_proj`) and the `q_norm`/`k_norm` layers (I: the model is derived from OLMo-2 in transformers; R, transformers doc https://huggingface.co/docs/transformers/model_doc/olmo3, "an improvement on OLMo2"). Confirm with the meta-device count.

### 6.2 Blockers (each fails loudly; none fails silently, as far as I can see)

| # | Blocker | Evidence | Fix (needs approval) |
|---|---|---|---|
| **B1** | **No `olmo3` code in the pinned transformers.** `AutoModelForCausalLM` cannot load the model under 4.56.2 (and the loaders use `trust_remote_code=False`) | R: lock `experiments/minimal_safety/requirements.lock`:29 (`transformers==4.56.2`); the 7B fixture's environment records 4.56.2 (M, `tmp/family-probe-sp-olmo2-7b-g-seed1103/expected-fixture-probe.json` `environment.packages`); `configuration_olmo3.py` is 404 at tag v4.56.2 and present at v4.57.0 (R, raw.githubusercontent.com/huggingface/transformers/{v4.56.2,v4.57.0}/src/transformers/models/olmo3/configuration_olmo3.py); the card asks for ≥ 4.57.0 | A **separate lock for OLMo 3 only**, with transformers 4.57.1 (the version that saved the checkpoint) and, if possible, the same torch 2.8.0, peft 0.17.1 and tokenizers 0.22.2. Compatibility of that set is not verified. Do not move the frozen Gate B lock. The kits pack and install `experiments/minimal_safety/requirements.lock` (R, `runkit/family-probe/pack_setup.py`:87, 138), so the kit must pack a different lock for this model. Run the CPU test suite under the new lock before any pod |
| **B2** | **The chat template file is not downloaded.** The kit patterns are `*.json`, `*.safetensors`, `merges.txt`, `vocab.json`, `tokenizer*`, `LICENSE`, `README.md` (no `*.jinja`); the Mac fetch takes three exact tokenizer files | R: `runkit/family-probe/probes.py`:17-18; `runkit/family-probe/setup/download_models_probe.py`:85 (`allow_patterns`); `runkit/family-probe/fetch_tokenizers_mac.py`:27. OLMo 3's `tokenizer_config.json` has no `chat_template` key (R) | Add `chat_template.jinja` to this model's patterns and to the Mac fetch list. Without it, the template probe fails before any training (I) |
| **B3** | **The preflight verdict is false on every candidate.** `comparison_rows` uses padding rows (embedding rows > tokenizer length) or `<|reserved_special_token_N|>` rows. OLMo 3 has 100,278 rows for 100,278 tokens and no reserved-token names. So it returns "none", `chat_rows_distinct` is null, and `use_this_recipe` needs every part to be `True` | R: `cuda_preflight_family.py`:94-104, 106-115, 242; M/I: §4 arithmetic and §5 token list | Choose a rule: (a) compare against the unused `<|extra_id_1|>`…`<|extra_id_6|>` rows (ids 100270–100275; never in the template, so probably untrained, I); or (b) a recorded lead waiver for this model. The script ships in the Gate B bundle (R, `78b-kit-cap-rule.md` §5, T4), so do not edit it before Gate B's last kit pod; add a new file or wait |

### 6.3 New files that the model needs (I; all are added files, no engine `.py` edit)

1. **Data config** `study-kt-data-dolly-olmo3.json`, modelled on the OLMo-2 one (R, `configs/study-kt-data-dolly-olmo2.json`): the OLMo 3 snapshot as the tokenizer; end-of-turn `<|endoftext|>`; forbidden substrings = the OLMo-2 list (`<|`, `|||` and the three Qwen markers) plus `<function` and `</function`; `banks_from.retokenize` of the dev bank. **It cannot reuse `exclude_lines` [10024, 12405] and `construction_sha256` blindly.** The default system block adds about 15 tokens per prompt over OLMo-2 (E, §5), so rows near the 1,536-token prompt limit or the 3,072-token row limit may drop. Then the expected `construction_sha256` fails and the preparation refuses. That refusal is the safe outcome; it then needs an amendment like OLMo-2's (lead decision 2 precedent).
2. **Prepared set** `prepared-kt-dolly-olmo3` (new token hashes for every unit and bank item, because the template differs). For stage 3, engine round Y's hidden subsample needs a third tokenizer file. Round Y already plans "one file per tokenizer family" (R, `engine-round-Y-design.md`:139), so the change is one more file, and the shared-id draw must pass the audit under the OLMo 3 tokenizer too.
3. **Recipes** `study-kt-olmo3-7b-r64-b-{mb4,mb2,…}-<date>.json`: recipe B with `repo_id` `allenai/Olmo-3-7B-Instruct`, the pinned revision, `architecture` `Olmo3ForCausalLM`, no `model.tokenizer` field (the model's own snapshot), end-of-turn `<|endoftext|>`, stop tokens [`<|endoftext|>`, `<|im_end|>`], pad `<|pad|>`, `assistant_header` `<|im_start|>assistant\n`, `expected_trainable_parameters` 159,907,840, sdpa. Use a new date in the name. The family recipe test globs `*-r64-b-*-20261008.json` and asserts exactly twenty recipes (R, `test_ss_family_recipes.py`:39-42).
4. **Tests.** A tiny `Olmo3ForCausalLM` case (sliding window and YaRN) beside the OLMo-2 and Llama cases (R, `test_ss_family_models.py`:24-52). It must skip under the 4.56.2 lock. An OLMo-3-like codec fixture: special ChatML markers, a default system message with non-special tags, a final-turn eos that differs from the mid-turn `<|im_end|>`, no BOS, no padding rows. New entries in `LADDERS`, `COUNTS` and `FAMILY` (R, `test_ss_family_recipes.py`:20-26).
5. **Kit entry.** A `probes.py` row: open repo (no token needed), the three shard pins from §1 (after a direct API re-read), `audit_tokenizer` None, `chat_template.jinja` in the patterns (B2), the new lock (B1), a 60 GB container disk and a volume as for OLMo-2-7B.
6. **Cap rule.** The 7–8B M-cap rule refuses any recipe not on its allow-list (R, `78b-kit-cap-rule.md` §4). OLMo 3 needs its own measured basis. The first pods (Gate A) give it. Until then, use the OLMo-2-7B basis as a prior, because the shapes are the same (I).

## 7. What adding it means for the study (short; E and I)

- **A third family, 7B only.** OLMo 3 comes in 7B and 32B only (R, arXiv abstract). It gives no 1B replication and no cross-scale claim. It does give a third 7–8B family, with the same architecture shapes as OLMo-2-7B and newer post-training data. That helps a reviewer who asks whether a finding holds beyond two families (I).
- **Gate A first.** The per-family LR rule picks the highest of 1e-4, 5e-5, 2e-5 that gives partial erosion. That needs OLMo 3's own Gate A ladder. Rung 1 (1e-4) at two seeds: one a0 pod with the untuned evaluation (OLMo-2-7B: 114.6 min job + about 30 min overhead ≈ 2.4 h ≈ $4.3) and one fine-tune-only pod (91 min + 30 min ≈ 2.0 h ≈ $3.6), so about **$8–10** with a preflight ladder (E: measured OLMo-2-7B times, R, `78b-kit-cap-rule.md` §3, at $1.79/h). If rung 1 saturates, rung 2 costs about $7 more (E). Add a smoke run of the new lock (E: a few dollars if done on the first Gate A pod).
- **Per-arm cost after Gate A (E).** Same shapes as OLMo-2-7B, so about the OLMo-2-7B 4-per-pod cost, $2.9–3.5 per arm (R, `78b-kit-cap-rule.md` §8). Answer lengths may differ: the Instruct DPO used length control for shorter answers (R, §5.3), but RL ran with 8K-token responses (R, §5.4.1). The capped-batch count sets the time, so only a measurement settles it.
- **Calendar (I).** B1–B3, the data config, the prepared set and the tests are $0 builder work. The configs and the preflight script fall under T4 (no change before Gate B's last kit pod) and Gate B's pack rule (it refuses uncommitted files under `experiments/` or `scripts/`; R, `78b-kit-cap-rule.md` §5). So the OLMo 3 Gate A can start only after that pod, or with explicit-path commits that the lead approves (the KD8 pattern).
- **Cut order unchanged.** It stays the first 7–8B model to cut. No other plan depends on it.

## 8. Smallest decisive checks

1. **$0, Mac, no weights (after approval of a separate venv; I installed nothing).** With transformers 4.57.1 in a separate venv: load `config.json` and the tokenizer files (`chat_template.jinja` included); run `scripts/family_lora_count.py` (expect `Olmo3ForCausalLM`, 159,907,840) and `scripts/family_codec_check.py` with `--end '<|endoftext|>' --stop '<|endoftext|>' --stop '<|im_end|>' --pad '<|pad|>' --header '<|im_start|>assistant\n'` and the Dolly file (row and prompt limits, separate-against-joint mismatches, round trip). This settles the prompt overhead, the rows that drop, and the template probe. Reading tokenizer files is allowed by the brief; installing the venv is not, so this needs the lead's approval.
2. **$0, Mac.** Run the existing CPU tests under the new lock. This shows whether engine X behaves the same under transformers 4.57.1 on the OLMo-2 and Llama tiny models.
3. **First pod (inside OLMo 3 Gate A).** The family preflight with a fixed B3 rule: memory ladder (expect mb2), template and tokenizer checks, and the untuned answers' stop reasons. The stop reasons show which token the untuned model emits at the end of a one-turn answer, `<|im_end|>` or `<|endoftext|>`. That evidence supports decision D3 below.

## 9. Decisions needed

- **D1 (user, pending).** Add OLMo 3 7B Instruct as a third 7–8B model, if funded; first 7–8B cut if money is short. Nothing here argues against it on technical grounds. The cost is the builder work in §6 and about $8–10 for Gate A before any block (E).
- **D2 (lead; KD8-like).** A separate environment lock for OLMo 3 only (recommended), against moving every model to a new lock (that breaks the frozen Gate B environment). Also: cross-family comparisons that involve OLMo 3 then carry a library-version difference. State it as a limit.
- **D3 (lead, then GPT; it touches the experimental model's input).** End-of-turn token for training: `<|endoftext|>` (recommended; it matches the template's final-turn rule and the joint-render audit), with both stop tokens. The alternative `<|im_end|>` makes every row a separate-against-joint mismatch.
- **D4 (lead, then GPT).** Keep the template's default system block in every prompt (recommended: it is the model's documented default, as Qwen's default system message was for Qwen). The alternative needs a new recipe field for an explicit system message, which is an engine change.
- **D5 (lead).** The B3 rule: unused `<|extra_id_N|>` rows as comparison rows, or a recorded waiver. Where it lives under T4: a new preflight file, or after Gate B's last kit pod.
- **D6 (lead).** Revision pin: main `6e5971d9…` (recommended: the weights, tokenizer and template equal those of `d42dc9de…`; `config.json` differs only by two int-to-float changes). Re-read the shard SHA-256 values with the Hub API directly before pinning, because mine came through a summarizer.
- **D7 (lead).** Which safety number to quote for the model: the paper v2 table (87.6, recommended) or the card (87.3).

## 10. Limits

- I loaded no tokenizer and no model. The Mac has no transformers or tokenizers package in the project venv or the system Python (M: `ModuleNotFoundError`). Token counts in §5 and §6 are E.
- Hashes, counts and file lists from the Hub API came through the WebFetch summarizer (WF). Cross-checks passed where I could make them: the `merges.txt` and `special_tokens_map.json` blob ids equal my local `git hash-object` values; the main sha is the same in two API reads; the shard hashes are the same in two tree reads; the parameter count equals my arithmetic.
- I did not see the full chat template text. The summarizer gave its control flow and short literals (R, two reads). The end-of-turn rule agrees with Ai2's tokenizer README.
- I read the report sections that matter for safety (§2.2, §4.2.1 Table 17, §4.4.1–4.4.2 Table 20, §5.1–5.5, App. A.8.2 Tables 52–55). I did not read all of App. A.7.
- Whether transformers 4.57.1, torch 2.8.0, peft 0.17.1 and tokenizers 0.22.2 install together is not verified.
- No OLMo 3 unit has run in this project. Every time, memory and cost statement for it is E, borrowed from OLMo-2-7B because the shapes are the same.

## 11. Commands actually run (all read-only; exit 0 unless noted)

- `ls`, `find`, `wc -l`, `grep`, `sed -n`, `git rev-parse`, `git log`, `git status --short` on the worktree and the main checkout (to find and read the named files). One `find` over the disk and the home folder for a transformers install ran past 120 s and moved to the background; when I read its output it had printed only `.venv` (from the `ls` part of the same command) and no transformers folder. I did not wait for it to finish.
- `python3 -I -c …` to print the OLMo-2-7B recipe `model` block, the OLMo-2 data config fields, the fixture's field names and numbers (no answers, prompts or rows), and the local OLMo-2 `tokenizer_config.json` special tokens and template.
- `git hash-object`, `shasum -a 256`, `stat` on the local OLMo-2 tokenizer files.
- `.venv/bin/python -I -c …` (package versions: all absent) and `python3 -I -c "import tokenizers"` (exit 1, `ModuleNotFoundError`).
- `python3 -I` arithmetic for the parameter, LoRA and KV-cache counts (§4).
- `date -u` (07:41:30 and 07:43:04 UTC).
- WebFetch reads (2026-10-17): the Hub API pages for `Olmo-3-7B-Instruct` (model, commits, tree at main and at `d42dc9de…`, two commit pages), `-SFT`, `-DPO`, `Olmo-3-1025-7B`, `Olmo-3-7B-Think`, `OLMo-2-1124-7B-Instruct`, `olmo-3-tokenizer-instruct-release` (tree, README); the model listings; raw `config.json`, `generation_config.json`, `tokenizer_config.json`, `chat_template.jinja`; the model card; the Dolci SFT, DPO and RL dataset cards (text only); arXiv abs, HTML (first 190k characters had no post-training sections) and the v2 PDF (read pages 2–4, 38–40, 45–46, 53–62, 115–117); the transformers olmo3 doc page; the transformers source at tags v4.56.2 (404) and v4.57.0; the Ai2 blog post.
