# OLMo 3 7B Instruct: engine and kit compatibility, and memory (CHECK)

**Status: CHECK ONLY. It adopts nothing.** Written 2026-10-17 at about 07:45 UTC (clock checked with `date -u`) by an Opus worker for the main-study lead (GI VI). Read-only work on the repository: no repo edit, commit, pod, spend, install or weight download. The only new files are this note and `calc/` beside it.

**Context.** A user decision is pending in the lead's chat: add OLMo 3 7B Instruct as a third 7–8B model if funded, and cut it first among the 7–8B models if money is short (after 70B and 32B). This note answers one part: what the engine and the kits need for a new family, and whether the OLMo-2-7B memory setting carries over.

**Labels.** **R** = read in a source (path:line or URL with read date). **M** = measured number from the records or from a count I ran (source given). **E** = estimate (basis given). **I** = inference. **U** = unverified; it needs a check before use.

**Sources.**
- HF = Hugging Face pages for `allenai/Olmo-3-7B-Instruct`, read 17 Oct 2026 about 07:25–07:40 UTC through WebFetch (a summarizer returns the content, so the bytes are not hashed here): `…/raw/main/config.json`, `…/raw/main/tokenizer_config.json`, `…/raw/main/chat_template.jinja`, `…/raw/main/generation_config.json`, the model card `https://huggingface.co/allenai/Olmo-3-7B-Instruct`, and the API `https://huggingface.co/api/models/allenai/Olmo-3-7B-Instruct` (main = `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc`, lastModified 2026-06-25).
- Code = the main checkout `/Users/spiderishi/Coding/attribution` at `0294d1b` (branch `stageb-costs-and-recovery-safeguards-20261003`). SS = `experiments/safety_selection`. PRE = `scripts/cuda_preflight_family.py` (SHA-256 `b142f3fd5a06…`). FPK = `runkit/family-probe/`. LOCK = `experiments/minimal_safety/requirements.lock` (`f55693d69f24…`).
- VENV = `tmp/minimal-experiment-20261002/venv` (transformers 4.56.2). T457 = a local uv cache copy of transformers 4.57.6, `~/.cache/uv/archive-v0/lQSxF5l04VtSNhpm/transformers` (not a project environment; read as code only).
- LEDG = `tmp/family-probe-sp-olmo2-7b-b-seed1103/retrieved/sp-olmo2-7b-1103/tree/round1/1103-a0-e1-a1/ledger.jsonl`; VER = `tmp/family-probe-sp-olmo2-7b-b-seed1103/hosts/sp-olmo2-7b-1103/verification.json`. I read only memory, seconds, counts and ids from them.
- CAP = `research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md` (`9884bd17df46…`). XL = `…/32b-70b-design.md`. EYD = `…/engine-round-Y-design.md`. RP = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md` (`e876829866d9…`). CK = `research/experiments/2026-10-17-stage1-review-b-rulings/check-endpoints-anchors-models.md` §5 (an earlier OLMo 3 fact sheet). BRIEF = `.ai/briefs/stage1-commitments-build-20261016.md`.

---

## 0. Summary

1. **The pinned environment cannot load OLMo 3.** VENV's transformers 4.56.2 has `olmo`, `olmo2` and `olmoe` only; no file in it names `olmo3` (M: `grep -rl olmo3` gives 0 files). Every lock in the project pins 4.56.2 (M). The card says OLMo 3 needs 4.57.0 or higher (R, HF card). The class `Olmo3ForCausalLM` exists in 4.57.6 and is a thin subclass of `Olmo2ForCausalLM` (R, T457 `models/olmo3/modular_olmo3.py`). So OLMo 3 needs **its own lock** with transformers 4.57.x. A global upgrade would change the environment of every engine-X unit (I).
2. **On the minimal path, no engine code changes (I).** The loader, codec, training loss and generation loop are generic: `AutoModelForCausalLM`, a class-name check, `lm.model`, `lm.lm_head`, `logits_to_keep`, a key/value cache passed back (R, SS/loaders.py:144-200; SS/engine.py:222-245, 528-564). The template has no clock call and no BOS (R, HF template). So OLMo 3 does not by itself need engine round Y. It needs new files: a lock, recipe configs, a data config, a prepared set, a new preflight script and a kit entry.
3. **One blocker in the existing preflight (I, from R).** OLMo 3 has 100,278 embedding rows and 100,278 tokenizer entries, so it has no padding rows, and it has no `<|reserved_special_token_N|>` rows (R, HF config and tokenizer_config). The family preflight then finds no comparison rows, sets `chat_rows_distinct` to null, and `use_this_recipe` becomes false for every candidate (R, PRE:94-104, 229-243). T4 forbids editing PRE (it ships in the Gate B bundle). So OLMo 3 needs a **new preflight script** with its own comparison rows (for example the seven unused `<|extra_id_N|>` rows).
4. **Two silent-gap risks in file lists (R).** OLMo 3 keeps its chat template in `chat_template.jinja`, not in `tokenizer_config.json` (R, HF API file list and tokenizer_config). The kit download patterns (FPK/probes.py:17), the Mac tokenizer fetch list (FPK/fetch_tokenizers_mac.py:27-41), the engine's own fetch patterns and its tokenizer-identity list (SS/assets.py:25-28) do not include that file. A missing template fails loudly at the first `apply_chat_template` (I), but the prepared manifest would not record the template's blob. The per-row token hashes still pin the exact ids (R, SS/runner.py:200-205).
5. **The codec choices (I, from R).** End of turn `<|endoftext|>` (the template ends the final assistant turn with `eos_token`; config eos 100257); stops `<|endoftext|>` and `<|im_end|>` (generation_config lists 100265 and 100257); pad `<|pad|>` (100277); header `<|im_start|>assistant\n`. **The template adds a default "function-calling" system message** when no system turn is given (R, HF template and card). The engine renders one user turn only (R, SS/textproc.py:68-77), so with engine X every OLMo 3 prompt carries that system message. Engine X did the same for Qwen2.5's default system message (R, SS/textproc.py:299-317). Stripping it is an engine change.
6. **The prepared set depends on the tokenizer, so OLMo 3 needs its own (R).** The data config names the tokenizer and end token; a recipe whose tokenizer differs refuses (R, SS/jobs.py:241-244). **A $0 proxy count: no Dolly row crosses a token limit under the OLMo 3 wrapper.** The wrapper adds 23–24 tokens to every prompt (M, `calc/limit_margin_out.txt`, OLMo-2 BPE as the proxy). No Dolly row and no dev-bank item holds the four new tag tokens (M, counts). So the units should equal `prepared-kt-dolly-olmo2`'s (E). The real tokenizer decides (U).
7. **Memory: micro-batch 2 × accumulation 64 carries over for Dolly (E).** OLMo 3 has the same shape as OLMo-2-7B: 32 layers, hidden 4,096, MLP 11,008, 32 query and 32 key/value heads (R, HF config). Its 7,298,011,136 values reproduce exactly from that shape (I, `calc/memory_calc_out.txt`); the LoRA r64 count is 159,907,840, as for OLMo-2-7B. Estimated training peak 61.6 GB allocated, about 64.4 GB reserved (75.6% of the 85.09 GB card). Generation: about 61.6 GB allocated; the reserved peak stays at the card's edge as for OLMo-2-7B (99.3%, M). **mb1 × acc128 is not needed** for Dolly. It would be needed only for rows longer than about 2,700 tokens (E). At two rows of 3,072 tokens (the recipe limit), mb2 would need about 81.0 GB allocated and 83.8 GB reserved (98.4%): not safe (E).
8. **The real memory risk is generation, not training (E/I).** OLMo-2-7B already generates at 99.3% reserved with 204 allocator retries in the full-length check (M, VER). OLMo 3 adds about 0.40 GB of key/value cache per 32-row batch (E). The preflight's `generation_memory_ok` check on the first pod decides (R, PRE:21-26, 256-267).

---

## 1. Facts: OLMo 3 7B Instruct against OLMo-2-7B

| | OLMo 3 7B Instruct | OLMo-2-1124-7B-Instruct (the 7–8B plan) |
|---|---|---|
| Id @ revision | `allenai/Olmo-3-7B-Instruct` @ `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc` (R, HF API) | `allenai/OLMo-2-1124-7B-Instruct` @ `470b1fba…` (R, SS/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json) |
| Licence, gate | Apache-2.0, not gated (R, HF API) | Apache-2.0, not gated |
| Class | `Olmo3ForCausalLM`, model type `olmo3` (R, HF config) | `Olmo2ForCausalLM` |
| Shape | 32 layers, hidden 4,096, MLP 11,008, 32 heads, 32 key/value heads, untied head, RMS eps 1e-6 (R, HF config) | Same layers, hidden, MLP and heads (R, CAP §2) |
| Embedding rows | 100,278 (R, HF config `vocab_size`) | 100,352: 74 padding rows (M, VER `comparison_kind` padding, 74 rows) |
| Values | 7,298,011,136 bf16 (R, HF API); 14.60 GB in 3 shards (R, CK §5.1) | about the same; load allocated 15.24 GB with LoRA (M, LEDG `load_policy`) |
| Attention | sliding window 4,096 on 24 of 32 layers (3 sliding, then 1 full); RoPE theta 500,000; YaRN (factor 8, original 8,192) on the full layers only (R, HF config; T457 modular_olmo3.py:330-345) | full attention on all layers |
| Positions | 65,536 (R, HF config) | 4,096 |
| Tokens | eos 100257 `<|endoftext|>`; pad 100277 `<|pad|>`; `<|im_start|>` 100264 and `<|im_end|>` 100265 special; 22 added tokens 100256–100277 (R, HF tokenizer_config) | same ids for these four; the 4 tag tokens below are `<|extra_id_N|>` there (M, local OLMo-2-1B tokenizer, `calc/count_wrapper_out.txt` and my listing) |
| New added tokens | `<functions>`, `</functions>`, `<function_calls>`, `</function_calls>` at 100266–100269, **not** flagged special (R, HF tokenizer_config) | — |
| Chat template | in `chat_template.jinja`; ChatML tags; default system message; final assistant turn ends with `eos_token`, earlier ones with `<|im_end|>\n`; no BOS; no date call; no `<think>` (R, HF template) | inside tokenizer_config; `<|endoftext|><|user|>\n…\n<|assistant|>\n`; BOS first |
| Generation config | eos ids [100265, 100257]; sampling defaults T 0.6, top-p 0.95 (R, HF generation_config) | — |
| transformers | "supported in transformers 4.57.0 or higher" (R, HF card); config written by 4.57.1 (R, HF config) | runs on the pinned 4.56.2 (R, LOCK:29) |

**Consequence (I).** Our sequences never reach the sliding window. Training rows are at most 3,072 tokens and generation at most 1,536 + 2,048 = 3,584 (R, recipe `max_train_tokens`, `max_prompt_tokens`, `max_new_tokens`). In 4.57.6 a sliding layer keeps every token while fewer than 4,095 are cached, and the sliding mask equals the causal mask below the window (R, T457 `cache_utils.py:170-207`; `masking_utils.py:222-249`). So in every engine use OLMo 3 runs as a full-attention model, with YaRN on 8 of 32 layers.

---

## 2. What a new family needs, item by item

| # | Item | Engine file? | What OLMo 3 needs | Blocking? |
|---|---|---|---|---|
| 1 | **transformers version** | no (the engine hashes `.py` files only; R, SS/common.py:28-36) | a separate lock with transformers 4.57.x | yes |
| 2 | **Family codec** (template, end of turn, stops, pad, header) | no; recipe fields | the values in §2.2 | no |
| 3 | **Recipe configs** | no; new config files | `study-kt-olmo3-7b-r64-b-<rung>-<date>.json` per ladder candidate | no |
| 4 | **Data config + prepared set + token audit** | no; new config, new prepared folder | `study-kt-data-dolly-olmo3.json`; `prepared-kt-dolly-olmo3` | yes (needs the tokenizer files on the Mac) |
| 5 | **CUDA preflight** | no; a script outside the identity | a new script (PRE refuses OLMo 3) | yes |
| 6 | **Expected fixture** | no; kit record | recorded fresh by the first OLMo 3 host | no |
| 7 | **Kit** (downloads, lock path, cap rule, Mac fetch) | no | `chat_template.jinja` in every file list; the new lock path; an OLMo 3 cap basis | yes |
| 8 | **Engine code** | — | none on the minimal path; optional round-Y items in §2.7 | no |

### 2.1 transformers version and the lock

- **M.** VENV: `transformers-4.56.2.dist-info`; `models/` holds `olmo`, `olmo2`, `olmoe`; `models/auto/configuration_auto.py` has no `olmo3` entry; `grep -rl olmo3` over the package gives 0 files.
- **M.** LOCK:29, the pod lock `tmp/gate-b-olmo/retrieved/w0b-2/tree/environment-linux.lock`:44 and `tmp/minimal-experiment-20261002/environment.lock`:29 all pin `transformers==4.56.2`. The Gate B kit pins Gate A's pod lock by hash (R, `runkit/gate-b-olmo/gateb_rules.py:75`, `7e0dd998…`).
- **R.** T457 registers `("olmo3", "Olmo3Config")` and `("olmo3", "Olmo3ForCausalLM")` (`models/auto/configuration_auto.py:291`, `modeling_auto.py:721`). `Olmo3ForCausalLM(Olmo2ForCausalLM): pass`; the only model changes are the sliding layers and the two rotary embeddings (`modular_olmo3.py:330-427`).
- **R.** transformers 4.57.6 asks for huggingface-hub ≥0.34,<1.0, tokenizers ≥0.22,≤0.23 and safetensors ≥0.4.3, the same bounds as 4.56.2 (T457 METADATA:27-34; VENV METADATA:27-34). LOCK has hub 0.36.2, tokenizers 0.22.2, safetensors 0.8.0, torch 2.8.0 (LOCK:7, 24-27). PEFT 0.17.1 states no transformers bound (VENV `peft-0.17.1.dist-info/METADATA`:30).
- **I.** So the OLMo 3 lock can be LOCK with one changed line. `pip check` should pass. Whether PEFT 0.17.1 runs correctly with 4.57.x is **U**.
- **R.** 4.57.6 still accepts `torch_dtype=` with a deprecation warning (T457 `modeling_utils.py:4629-4670`), so the loader's call works (SS/loaders.py:158-161).
- **Where it lives (I).** A Gate B pack bundles every `.lock` under `experiments/minimal_safety/` and `experiments/safety_selection/`, and refuses any uncommitted file under `experiments/` or `scripts/` (R, XL §3 citing `runkit/gate-b-olmo/pack_setup.py:195-200, 220-223`). So before Gate B's last kit pod the OLMo 3 lock belongs in the new kit's folder (for example under `runkit/`) or in this draft folder, not under `experiments/`.
- **Environment record (I).** The engine records package versions in every run (R, `experiments/minimal_safety/model.py:411-430`). OLMo 3 units will therefore carry another environment than the engine-X units. That is fine within the family (its own a0 and R arms), but OLMo 3 needs its own reference unit for the environment rule (as CAP and the 7–8B draft use a0-1101 per family).

### 2.2 The family codec

How the engine builds prompts (R): the codec renders `[{"role": "user", "content": text}]` with the generation prompt, and the training example is those ids + the separately encoded response + the end-of-turn id (SS/textproc.py:68-77, 173-183). `build_codec` refuses a template that calls `strftime_now`, needs the end token in the stops, and treats every special id and every added token flagged special as a control token (SS/textproc.py:102-133). The loader then checks the assistant header (SS/textproc.py:139-151; SS/loaders.py:187-188).

| Field | OLMo 3 value (proposed) | Basis |
|---|---|---|
| `architecture` | `Olmo3ForCausalLM` | R, HF config; the loader compares the class name (SS/loaders.py:162-163) |
| `revision` | `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc` | R, HF API |
| `model.tokenizer` | leave out (its own snapshot) | I: OLMo-2's tokenizer has another template and other added tokens, so the 7B precedent (1B tokenizer pin) does not apply |
| `end_of_turn_token` | `<|endoftext|>` | R, HF template: the final assistant turn ends with `eos_token`, and eos is `<|endoftext|>`; config `eos_token_id` 100257. **Which token the model really emits is U** (see D-O2) |
| `stop_tokens` | `["<|endoftext|>", "<|im_end|>"]` | R, HF generation_config `eos_token_id` [100265, 100257] |
| `pad_token` | `<|pad|>` | R, HF config `pad_token_id` 100277 |
| `assistant_header` | `<|im_start|>assistant\n` | R, HF template; equal to the engine's default (SS/textproc.py:136), but explicit is clearer |
| `attn_implementation` | `sdpa` | as the OLMo-2-7B recipe (R) |

- **`single_token_id` (I).** `<|endoftext|>` is also OLMo 3's unknown token (R, HF tokenizer_config `unk_token`). The engine already allows exactly this case for OLMo-2 (R, SS/textproc.py:90-99).
- **Header check (I).** Without the generation prompt the render ends `…<|im_start|>user\n<<probe>><|im_end|>\n`; with it, `<|im_start|>assistant\n` follows (R, HF template). So the check passes.
- **The default system message.** With no system turn the template emits `<|im_start|>system\nYou are a helpful function-calling AI assistant. You do not currently have access to any functions. <functions></functions><|im_end|>\n` (R, HF template; the card lists the same default). The engine has no system turn, so every OLMo 3 prompt carries it (I). This is a choice about the model's input, so it is for GPT or the user (D-O1). The engine-X precedent is Qwen2.5, whose template also added a default system message (R, SS/textproc.py:299-317).
- **The new tag tokens are not control tokens (I).** `<functions>` and the other three are added tokens without the special flag (R, HF tokenizer_config), so `has_special` does not refuse text that holds them. Text holding them would silently encode to those ids. Counts: 0 of 15,011 Dolly rows and 0 of 657 dev-bank items hold any of the four tags or `<|extra_id` (M, counts only, run in this session). The family data configs forbid `<|` and `|||` (R, `study-kt-data-dolly-olmo2.json` `forbidden_substrings`); `<functions>` does not start with `<|`. Proposed: add `<function` and `</function` to OLMo 3's forbidden list (D-O6). By the counts this changes no Dolly row and no dev item.
- **Chat tokens the preflight will see (I).** The joint render of a probe turn and a reply holds `<|im_start|>`, `<|im_end|>` and the final `<|endoftext|>` (R, HF template). OLMo-2-7B had only `<|endoftext|>` (M, VER `chat_tokens`).

### 2.3 Recipe configs

- A new family needs new recipe files: recipe B with the model fields of §2.2, `expected_trainable_parameters` 159,907,840 (I: the formula of `test_ss_family_recipes.py` and my arithmetic, `calc/memory_calc_out.txt`), and its LR rung (1e-4 first, by the per-family rule).
- **Test interaction (R).** `test_ss_family_recipes.py` asserts exactly twenty files match `study-kt-*-r64-b-*-20261008.json` and lists the families in `LADDERS`, `COUNTS` and `FAMILY` (lines 20-49). An OLMo 3 recipe with another date suffix does not break that test (I). Its own checks belong in a new test file.
- **T4 / KD8 (R, CAP §5; XL D15).** A new file under `SS/configs/` is not an engine file, but a Gate B recovery re-pack would bundle it, and an uncommitted one blocks the pack. Before Gate B's last kit pod: keep drafts here, or commit by explicit path with the lead's consent.

### 2.4 Data config, prepared set and token audit

**Does the prepared Dolly set depend on the tokenizer? Yes (R).**
- The task data config holds `tokenizer` {repo_id, revision, end_of_turn_token, max_train_tokens, max_prompt_tokens} (R, SS/config.py:374-380).
- The builder builds a codec from that tokenizer and end token (R, SS/prepare_task.py:250-252), runs the token audit (row ≤ 3,072, prompt ≤ 1,536, no control token; R, :15-17, 361), retokenizes the dev bank (R, :256-263), and writes each row's `token_sha256` and the tokenizer identity into the manifest (R, :428-429).
- A job refuses a recipe whose (repo, revision, end token) differs from the data config's (R, SS/jobs.py:241-244). The runner re-encodes every training row and refuses a different hash (R, SS/runner.py:200-205); the evaluation checks every prompt's hash (R, EYD citing SS/runner.py:574-578).
- So OLMo 3 needs `study-kt-data-dolly-olmo3.json` and its own prepared folder. The OLMo-2 data config is the model: `exclude_lines` [10024, 12405], `construction_sha256` `2f5802f5…`, dev-only `retokenize` (R, `test_ss_family_recipes.py:102-118`).

**Will the units stay the same? Probably yes (E).**
- The OLMo 3 wrapper is 35 tokens against OLMo-2's 11, so every prompt grows by 23 or 24 tokens (M, `calc/limit_margin_out.txt`: 11,650 rows +24, 3,361 rows +23). The basis is the cached OLMo-2-1B tokenizer as a proxy, with the three-token saving of the single `<functions>` tags in OLMo 3 applied.
- Under that proxy **0 rows newly exceed the 1,536 prompt limit and 0 newly exceed the 3,072 row limit** (M, same file). No row within the limits has an OLMo-2 prompt within 48 tokens of 1,536 (M: all 14,962 such rows are in the "48 or more" bin).
- The proxy is exact only if OLMo 3's base vocabulary equals OLMo-2's. `merges.txt` is identical and the special ids match, but the `vocab.json` and `tokenizer.json` blobs differ (R, CK §5.1). **U** until the real tokenizer runs.
- If the units equal OLMo-2's, the `construction_sha256` assertion holds and the edit files can hold the same row lists. But the Gate B sealed edit files bind to the OLMo-2 manifest (R, 7–8B draft citing SS/edits.py:117), and the frozen sealed builder refuses other manifests (R, 7–8B draft, BLD:60-61). So OLMo 3 needs the same separate writer as Llama (I).
- Longest training row (E): 2,114 (M, `prepared-kt-dolly-olmo2/manifest.json` token_audit) + 24 = **about 2,138 tokens**. Longest dev generation prompt: 320 (M, dev bank `prompt_tokens`) + 24 = about 344.

**Tokenizer identity gap (R, I).** The manifest's tokenizer record lists only `TOKENIZER_FILES` = tokenizer.json, tokenizer_config.json, vocab.json, merges.txt, special_tokens_map.json, added_tokens.json (R, SS/assets.py:27-28, 87-95). OLMo 3's template is in `chat_template.jinja`, so the manifest would not name the template's blob. The token hashes per row still pin the result, and every run records `chat_template_sha256` (R, SS/loaders.py:189-199). Fix without an engine change: record the jinja blob in the Mac fetch receipt and in the data config's amendment text (I; D-O8).

**Mac side (R, I).** transformers 4.56.2 can build the OLMo 3 tokenizer for preparation. `AutoTokenizer` uses `tokenizer_class` (here `GPT2Tokenizer`) and asks `AutoConfig` only when it is absent (R, VENV `models/auto/tokenization_auto.py:1061-1081`), and 4.56.2 reads `chat_template.jinja` (R, VENV `tokenization_utils_base.py:40, 1958`). Jinja2 is 3.1.6 on the Mac and on the pod (M, LOCK:10; pod lock:10). So the Mac preparation should give the pod's ids; the pod's per-row check refuses if not (I).

### 2.5 CUDA preflight and the expected fixture

- **Blocker (I, from R).** `comparison_rows` uses padding rows when the model has more rows than the tokenizer, else `<|reserved_special_token_N|>` rows, else none (R, PRE:94-104). OLMo 3 has 100,278 rows and (I) 100,278 tokenizer entries (100,256 base + 22 added, R, HF tokenizer_config), and no reserved-token rows. So the kind is "none", `chat_rows_distinct` is null, and `use_this_recipe` = all parts True is false (R, PRE:229-243). Every OLMo 3 candidate would be refused.
- **T4 (R).** PRE ships in the Gate B bundle (R, CAP §5 citing pack_setup.py:48). Editing it is forbidden until Gate B's last kit pod (R, BRIEF:65). So: a **new** script, for example `cuda_preflight_olmo3.py`, that imports PRE's helpers (as PRE imports the kill-test preflight's) and adds a comparison rule for OLMo 3.
- **Comparison rows for the new script (I; D-O4).** Candidates: the seven unused `<|extra_id_N|>` rows (100256, 100270–100275; R, HF tokenizer_config). On 5 Oct a range read found that in OLMo 3 7B **Base** the output rows of `<|im_start|>`/`<|im_end|>` point the same way as the unused rows (cosine 1.000) (R, `research/experiments/2026-10-05-headroom-v2-workplan.md:19`). PRE tests **bit identity** (R, PRE:113-114). Untrained rows may be parallel without being bit-identical, so a cosine or distance rule fits better. The rule must be fixed before the first pod. The four tag rows and `<|endofprompt|>` could be added to the checked set (I).
- **BOS record.** It runs only when prompts start with the BOS id (R, PRE:478-479). OLMo 3 prompts start with `<|im_start|>`, so it is skipped (I).
- **Tokenizer check.** With no `model.tokenizer` field, `tokenizer_ok` is true by rule (R, PRE:118-137).
- **Expected fixture.** The first host of a working kit records its verification as `expected-fixture-probe.json`; later hosts must equal it in `source`, `script_sha256`, `manifest_sha256`, `recipe_sha256`, `training_identity`, `test_rows` and two resume fields (R, FPK/orchestrate.py:223-231; FPK/plan_tool.py:133-134; FPK/setup/job_runner_probe.py:110-114). All of these change for OLMo 3 (new script, manifest, recipe, token hashes; I). So OLMo 3 gets its **own fixture, recorded on its first pod**; nothing carries over from OLMo-2-7B.

### 2.6 The kit

- **Download patterns (R).** `WEIGHTS` = `*.json`, `*.safetensors`, `merges.txt`, `vocab.json`, `tokenizer*`, `LICENSE`, `README.md` (FPK/probes.py:17). It does not match `chat_template.jinja`. The engine's own fetch has the same list (SS/assets.py:25-26). Add the file by name for OLMo 3 (I). Weight pins: the SHA-256 of the 3 shards from the Hub's file metadata (an S0 step, as XL §7 describes; not done here).
- **Mac tokenizer fetch (R).** `fetch_tokenizers_mac.py` has fixed families and blob pins (lines 27-41). OLMo 3 needs an entry with `chat_template.jinja` and the user's download approval (R, CK §5.1, "a new sealed preparation, whose tokenizer download needs the user").
- **Lock path (R).** Both kits pack `experiments/minimal_safety/requirements.lock` (FPK/pack_setup.py:87, 138; `runkit/gate-b-olmo/pack_setup.py:228, 260`), and the bootstrap installs torch 2.8.0 cu128 and then that file (FPK/setup/bootstrap_hr.sh:6-9). The OLMo 3 kit must pack its own lock instead (I).
- **No gated-token path** is needed: the repository is not gated (R, HF API). This is simpler than Llama (R, CAP §5 route (i)).
- **Disk (E).** Policy 14.60 GB + guard 8.84 GB, as OLMo-2-7B (R, CAP §9). The 60 GB container disk is enough.
- **Cap rule (R, I).** CAP's M-cap keys on an allow-list of recipe hashes and refuses any other recipe (CAP §4). OLMo 3's first pod needs an explicit cap. Proposed (E): OLMo-2-7B's M-cap values as a provisional basis (same shape and per-step work), with CAP's speed factor and in-pod check; then OLMo 3's own measured basis. Answer length does not break this, because the bound already assumes every batch reaches the cap (R, CAP §4).
- **Which kit (I; D-O7).** T4 names "kit file" (R, BRIEF:65). `runkit/family-probe/` is Gate A's kit, and Gate B pins Gate A's fixture path (R, `gateb_rules.py:95`). Editing it during Gate B is a T4 question for the lead. CAP's route (ii) or a new folder avoids the question. Use a `family-probe-` working-copy prefix so Gate B's guard sees the cap (R, CAP KD7).

### 2.7 T4 and engine round Y

- **T4 (R, BRIEF:65):** no engine file, Gate B pinned script, kit file or sealed file changes until Gate B's last kit pod.
- **The minimal OLMo 3 path touches none of them (I).** It adds a lock, configs, a data config, a prepared folder, a new preflight script, a kit entry or folder, and tests. The engine identity (29 `.py` files) stays X. Three conditions: the configs, script and tests wait outside `experiments/` and `scripts/` (or are committed by explicit path with consent; KD8/D15); PRE stays unedited; and the family-probe kit is not edited without the lead's T4 reading.
- **But engine X is certified only under 4.56.2 (I).** Running X's code under 4.57.x is a new environment. It needs its own checks (§4, checks 3 and 4). These are not engine changes, so they need not wait for round Y; they need an install approval.
- **Optional round-Y items (I).** Only if the lead wants them: (a) a codec option for a system turn, to strip or replace OLMo 3's default system message (SS/textproc.py, SS/config.py); (b) `chat_template.jinja` in `TOKENIZER_FILES` and `MODEL_PATTERNS` (SS/assets.py). EYD limits Y's edits to jobs, runner, `__main__`, config, engine and README (R, EYD §3.1 item 4). `textproc.py` and `assets.py` are outside that list, so either item widens Y's file list (D-O8). Recommended: neither (I); keep the default system message and record the jinja blob outside the engine.

---

## 3. Memory at micro-batch 2 × accumulation 64 on an A100-SXM4-80GB

**Measured basis (M; LEDG and VER, OLMo-2-7B seed 1103, recipe B mb2, sdpa, no checkpointing, generation batch 32, cap 2,048; card 85,093,777,408 bytes = 85.09 GB).**

| Stage | Allocated | Reserved |
|---|---|---|
| load_policy (weights + LoRA) | 15.24 GB | 15.26 GB |
| memory_preflight (2 longest rows × 2,114 tokens) | peak 59.23 GB | 61.10 GB |
| train | peak 61.11 GB | 63.85 GB |
| load_guard | 24.68 GB | 64.63 GB |
| generate | peak 61.22 GB | **84.49 GB (99.3%)** |
| full-length check (32 × (320 + 2,048) tokens, optimizer and guard resident) | peak 66.63 GB | 84.49 GB (99.3%), **204 allocator retries** |

**Model (E).**
- Training activation per token = (59.23 − 15.30) GB / 4,228 tokens = **10.39 MB per token, 324.7 KB per token per layer** (I: arithmetic; XL §4 found 325 KB). The memory preflight uses the real `micro_batch` longest rows (R, SS/runner.py:182), so the length that matters is the data's longest row, not the 3,072 limit.
- Key/value cache per token = 2 × 32 layers × 32 heads × 128 × 2 bytes = **524,288 bytes (0.5 MiB)**, the same for both models (I from R, HF config).
- OLMo 3 deltas: embedding rows −74 (−1.2 MB, I); the longest row +24 tokens (E, §2.4); each prompt +24 tokens (E). Same layer structure (`Olmo3DecoderLayer = Olmo2DecoderLayer`, R, T457 modular_olmo3.py). Two masks and two rotary tables per forward instead of one: a few MB (I).

**Estimates for OLMo 3 (E; `calc/memory_calc_out.txt`).**

| Case | Allocated | Reserved | Share of the card |
|---|---|---|---|
| Training, mb2, longest row about 2,138 (Dolly) | 61.6 GB | about 64.4 GB | 75.6% |
| Training, mb2, two rows at the 3,072 limit | 81.0 GB | about 83.8 GB | 98.4% (not safe) |
| Training, mb1 × acc128, one row at 3,072 | 49.1 GB | — | 57.7% |
| Training, mb4, longest row 2,138 | 106 GB | — | no fit |
| Generation, real batches | 61.6 GB (+0.40 GB) | at the edge, as OLMo-2-7B | allocated 72.4% |
| Full-length check | 67.0 GB (+0.40 GB) | at the edge; more retries likely (I) | allocated 78.8% |

**Verdict (E).**
- **mb2 × acc64 carries over for Dolly.** The training peak has about 20 GB of margin. mb2 stays below 90% reserved for rows up to about **2,726 tokens** (E). Dolly's longest row is about 2,138 (E).
- **mb1 × acc128 is not needed.** It would matter only for a data set with rows longer than about 2,700 tokens (for example a later Alpaca set; its row lengths are U). It would also cost time: training is overhead-bound per micro-batch (R, XL §4.1), so doubling the micro-batches could add about 5–15 min per arm (E).
- **mb4 fails** as it did for both 7–8B models (R, CAP §6). Drop it from the OLMo 3 ladder (I).
- **Generation is the edge.** Reserved memory already sat at 99.3% for OLMo-2-7B; its allocated peak was 23.9 GB below the card. The reserve fills with cached training blocks (I, from M: reserved 63.85 GB after training and 84.49 GB in generation, while allocated peaked at 61.22 GB). OLMo 3 adds 0.40 GB of allocated cache per batch (E). Allocator retries free cached blocks, so an out-of-memory error needs real fragmentation, not only more cache (I). Neither mb1 nor checkpointing changes the generation cache (I).
- **Uncertainty (U).** transformers 4.57's mask and cache code could change the peaks a little. The per-token model is one measured point, scaled linearly. The first pod's preflight measures all of this.
- **Proposed ladder (I; D-O5):** `mb2`, then `mb1-gc` (training fallback), then `mb2-g16` (generation fallback; batch 16 gives other greedy answers, a recipe deviation for GPT; R, XL §3). An environment-only fallback for the generation edge: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. The engine records that variable and does not refuse it (R, `experiments/minimal_safety/model.py:53-56`). CAP §6 rejected it for OLMo-2-7B because it breaks the match with the measured records; OLMo 3 runs in a new environment anyway, so that reason is weaker there (I; D-O9).

**Time (E, brief).** Decode steps at batch 32 cost about 3.6–3.8 ms per layer on every measured model (R, XL §5). OLMo 3 has the same 32 layers, so about 116 ms per capped step, as OLMo-2-7B (E). The extra mask and rotary work per step, the 4.57 code path, and OLMo 3's answer lengths are U.

---

## 4. Smallest decisive checks, in order

1. **Done, $0:** the proxy count of §2.4 (0 rows cross a limit; delta 23–24 tokens; 0 tag tokens in Dolly or the dev bank; M).
2. **$0, needs the user's approval for the tokenizer download (no weights):** fetch tokenizer.json, tokenizer_config.json, special_tokens_map.json, vocab.json, merges.txt and **chat_template.jinja** at `6e5971d9…`. Run `scripts/family_codec_check.py` in VENV with `--end '<|endoftext|>' --stop '<|endoftext|>' --stop '<|im_end|>' --pad '<|pad|>' --header '<|im_start|>assistant\n' --dolly …` (counts and line numbers only). Then prepare `prepared-kt-dolly-olmo3` and confirm `construction_sha256` = `2f5802f5…`.
3. **$0, needs an install approval:** a separate Mac venv with the OLMo 3 lock. Run `pip check`, the engine's CPU suite (record any golden test that differs under 4.57; U), and a new tiny-`Olmo3ForCausalLM` test like `test_ss_family_models.py` (LoRA count, B = 0 equality, checkpointing, left-padded batch = one at a time) with the sliding window at or above the test length. Keep the test outside `experiments/` until Gate B's last kit pod.
4. **First OLMo 3 pod (the rung-1 probe in block 0):** the new preflight. Read `memory_ok`, `generation_memory_ok`, allocator retries, peaks, ms per step, the end-of-turn log-probability record and the comparison-row verdict. Read the untuned unit's counts of stops on `<|endoftext|>` against `<|im_end|>` (ids only).

---

## 5. Decisions needed

- **D-O1 [GPT or USER] System message:** keep OLMo 3's default "function-calling" system message (engine X as it is; the Qwen2.5 precedent; disclose it) **(recommended, I)**, or strip it (a codec change in round Y). This also decides where a safety-prompt reference goes for OLMo 3 (U: how B10 inserts its prefix was not read here).
- **D-O2 [LEAD, GPT] End-of-turn target:** `<|endoftext|>` (the template's final-turn token) with both stops **(recommended, I)**. If check 4 shows the untuned model ends mostly with `<|im_end|>`, the target trains a different end token than the model uses. The choice must be fixed before the first fine-tune.
- **D-O3 [LEAD] The lock:** which 4.57.x (4.57.1 wrote the config, R; 4.57.6 is in the local uv cache, M), other pins unchanged, stored outside `experiments/minimal_safety` and `experiments/safety_selection` before Gate B's last kit pod.
- **D-O4 [LEAD] Comparison-row rule** of the new preflight (the `<|extra_id_N|>` rows; a cosine or distance threshold, not bit identity), fixed before the first pod.
- **D-O5 [LEAD; GPT for g16] Ladder:** `mb2`, `mb1-gc`, `mb2-g16`.
- **D-O6 [LEAD] Forbidden substrings:** add `<function` and `</function` (no Dolly or dev change by the counts).
- **D-O7 [LEAD] T4 reading:** a new kit or CAP route (ii) (recommended), or an entry in `runkit/family-probe/` during Gate B; and KD8/D15 for the new configs and script.
- **D-O8 [LEAD] Round Y scope:** add nothing for OLMo 3 (recommended), or add the system-turn option and the jinja file lists (this widens EYD's file list).
- **D-O9 [LEAD] Allocator setting** for OLMo 3's environment only: none at first (recommended), `expandable_segments` as the fallback if `generation_memory_ok` fails.

## 6. Alternatives considered

1. **Global upgrade to transformers 4.57.x for all families.** One lock, but it changes the environment of the reused engine-X units and of Gate B's frozen path. Rejected (I).
2. **Pin OLMo-2's tokenizer for OLMo 3** (the 7B → 1B precedent). It would feed OLMo 3 a template it was not trained on; PRE's tokenizer check would also refuse it (different template; R, PRE:118-137). Rejected (I).
3. **mb1 × acc128 from the start.** Safer only for long rows that Dolly does not have; slower and unlike the other 7–8B recipes. Rejected for Dolly (E).
4. **Edit PRE to accept "no comparison rows".** Smallest code change, but PRE is a Gate B bundled file (T4), and it would drop the chat-row check for OLMo 3. Rejected (I).
5. **Wait for round Y and put all OLMo 3 support in it.** No engine change is needed, and Y's certification pods do not cover a new environment. Rejected (I).

## 7. Limits

- The HF facts come through WebFetch's summarizer; the bytes are not hashed. The S0 pins (blob ids, shard SHA-256) are not done.
- The tokenizer proxy (OLMo-2-1B's BPE) is exact only if the base vocabularies match (U).
- No OLMo 3 code ran: not the tokenizer, not the model, not the engine under 4.57. T457 is a uv cache copy read as code, not a project environment.
- The memory model is one measured point (OLMo-2-7B, 2 × 2,114 tokens) scaled linearly. The generation reserve at the card's edge is a fragmentation effect that arithmetic cannot predict.
- I did not read how the safety-prompt reference (B10) builds its prompts, the family-probe reading's handling of a new probe key, or Alpaca's row lengths.

## 8. Commands run (all exit 0 unless stated)

- `date -u` (07:24, 07:42, 07:44 UTC). `git rev-parse`, `git branch`, `git status --porcelain -- experiments scripts` (empty) in the main checkout. `shasum -a 256` of PRE, LOCK, CAP and RP.
- `ls`, `grep`, `sed`, `wc` reads of the files cited above, and `python3 -I` reads of configs, manifests, LEDG and VER (keys, numbers and ids only).
- `grep -rl olmo3` over VENV's transformers (0 files); reads of T457's `models/olmo3/modular_olmo3.py`, `cache_utils.py`, `masking_utils.py`, `integrations/sdpa_attention.py`, `modeling_utils.py` and both METADATA files.
- One failing `python3 -I` call (exit 1: my script indexed a string as a dict; it printed key names only).
- Counts only: tag strings in the Dolly source and in `prepared-kt-dolly-olmo2/banks/dev.jsonl`; max `prompt_tokens` per dev kind.
- `calc/count_wrapper.py`, `calc/limit_margin.py` (VENV python `-I`, offline, the cached OLMo-2-1B tokenizer; counts only) and `calc/memory_calc.py` (stdlib). Outputs: `calc/*_out.txt`. No new `.pyc` file appeared under the main checkout's `experiments/` or `scripts/` (M: `find -newermt`). Re-run them with `-I -B`.
- WebFetch: the six HF pages listed under Sources. Nothing was downloaded to disk.
