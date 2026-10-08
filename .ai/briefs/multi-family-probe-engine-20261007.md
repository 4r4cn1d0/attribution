# Bounded assignment: engine, data, recipe and kit support for one-seed probes on OLMo-2 and Llama-3

**Revision 2, 8 October 2026.** This revision applies three reviews of revision 1: correctness (C), integrity (I) and safety-cost (SC). Tags such as [C-SF1] show where a finding went. The "Review log" at the end lists every finding and its result.

## Task and authorization

- **Task ID:** multi-family-probe-engine-20261007.
- **The user's request (relayed 8 October):** run the probe on OLMo-2-1B and Llama-3.2-1B; use the 7B–30B sizes too where they exist; check the RunPod credits; do both families. Item 7 gives the credit answer.
- **Read first:**
  - `research/FOCUS.md` lines 65–83: the decision of 2026-10-07 17:44 UTC, the 18:15 UTC addition and the access note;
  - `research/experiments/2026-10-07-kill-test-stage0-results.md`: recipe B, the Qwen2.5-7B check and their measured costs;
  - `.ai/briefs/kill-test-stage0-engine-20261006.md` (the previous build; its rules stay in force) and `.ai/inputs/kill-test-stage0/integration-review.md`;
  - the 7B-check precedent: `tmp/kill-test-7b-check/` (a working kit per model) and `.ai/inputs/kill-test-7b-check/`.
- **Scope: five one-seed probes.** Each probe is one pod job:
  1. the untuned baseline (the `init` unit of seed 1101);
  2. one recipe-B fine-tune of seed 1101, evaluated at e1.
  - The evaluation is unchanged: the same banks, judge, greedy decoding plus 3 samples at T 0.7, 2,048 new tokens, no repetition penalty.

  | Probe key | Model @ pinned commit | Access and licence |
  |---|---|---|
  | `olmo2-1b` | `allenai/OLMo-2-0425-1B-Instruct` @ `48d788eca847d4d7548f375ad03d3c9312f6139e` | open; Apache-2.0 |
  | `olmo2-7b` | `allenai/OLMo-2-1124-7B-Instruct` @ `470b1fba1ae01581f270116362ee4aa1b97f4c84` | open; Apache-2.0 |
  | `olmo2-13b` | `allenai/OLMo-2-1124-13B-Instruct` @ `3a5c85baefbb1896a54d56fe2e76c0395627ddf4` | open; Apache-2.0 |
  | `llama32-1b` | `meta-llama/Llama-3.2-1B-Instruct` @ `9213176726f574b556790deb65791e0c5aa438b6` | gated (manual); Llama 3.2 Community Licence; approved for the user (FOCUS.md:82) |
  | `llama31-8b` | `meta-llama/Llama-3.1-8B-Instruct` @ `0e9e39f249a16976918f6564b8830bc894c89659` | gated (manual); Llama 3.1 Community Licence; approved (FOCUS.md:82) |

- **Not in scope:**
  - 32B models (FOCUS.md:67: LoRA training does not fit one A100-80GB; the engine has no 4-bit or multi-GPU path);
  - the Llama-2-7B-Chat calibration probe (FOCUS.md:76–81). Open question 7 lists what it adds;
  - Stage 1 diagnostics, attribution, `score-audit` for other templates, and a faster decode loop.
- **You do not:**
  - call services, download anything, or touch a pod or RunPod;
  - read, handle, print or store a real token or other secret. Tests build fake tokens at run time;
  - install, commit, push or launch agents;
  - run a kit script that calls RunPod or Hugging Face (`host.py`, `launch.py`, `budget.py`, `account.py`, `orchestrate.py`, `finisher.py`, the download scripts), except through fakes in tests.
- **Held-out protection while building** (unchanged):
  - the banks come from `prepared-v3-inj05`. The engine may read every split (hidden included) inside the preparation only;
  - never print or read bank prompt text. Test with synthetic fixtures;
  - Dolly is training data: its schema, categories, counts and line numbers may be inspected.
- **The probes evaluate the dev bank only.** `calibrate` uses `evaluate_bank: "dev"` (`runner.py:1171`), and the baseline job uses `--bank dev` (`job_runner_kt.py:38`). So only the dev bank gets new token fields (Item 2b) [I-S5].

## Facts checked for this brief (7–8 October 2026; metadata, local files and CPU checks only; nothing downloaded)

### Models

| | OLMo-2 1B | OLMo-2 7B | OLMo-2 13B | Llama-3.2 1B | Llama-3.1 8B |
|---|---|---|---|---|---|
| Class | `Olmo2ForCausalLM` | `Olmo2ForCausalLM` | `Olmo2ForCausalLM` | `LlamaForCausalLM` | `LlamaForCausalLM` |
| Layers / hidden / heads / KV heads | 16 / 2048 / 16 / 16 | 32 / 4096 / 32 / 32 | 40 / 5120 / 40 / 40 | 16 / 2048 / 32 / 8 | 32 / 4096 / 32 / 8 |
| Embedding rows / tokenizer size | 100,352 / 100,278 | same | same | 128,256 / 128,256 (no padding rows) | same |
| Tied embeddings | no | no | no | yes | no |
| Max positions | 4,096 | 4,096 | 4,096 | 131,072 | 131,072 |
| Parameters | 1,484,916,736 | 7,298,617,344 | 13,716,198,400 | 1,235,814,400 | 8,030,261,248 |
| bf16 weights | 2.97 GB, 1 file | 14.60 GB, 3 files | 27.43 GB, 6 files | 2.47 GB, 1 file | 16.06 GB, 4 files |
| Rank-64 all-linear LoRA | **48,234,496** | **159,907,840** | **250,347,520** | **45,088,768** | **167,772,160** |
| KV cache per token (bf16) | 128 KiB | 512 KiB | 800 KiB | 32 KiB | 128 KiB |

- **Sources:** the HF API and `config.json` at each pin (the fact sheets' source lists). Each parameter total equals the API's safetensors total.
- **I re-ran the five LoRA counts:** PEFT 0.17.1 on meta-device models (transformers 4.56.2, `tmp/minimal-experiment-20261002/venv`, no weights), built from the pinned `config.json` files, gives exactly the bold values. The OLMo-1B model was built from its fact-sheet values, not from its file. The same formula gives Qwen2.5-7B's 161,480,704, the value in `study-kt-qwen7b-r64-b-*-20261007.json`. The correctness review recomputed all five counts as r·Σ(in+out) from the configs (7B and 13B intermediate sizes 11,008 and 13,824) and found them equal.
- **The seven LoRA target names** (`q_proj` … `down_proj`) exist once per layer in both classes (transformers 4.56.2 `modeling_olmo2.py:137-149, 207-209`; `modeling_llama.py:149-151, 210-221`). OLMo's `q_norm`/`k_norm` are RMSNorm, not targets. Recipe B's target list works unchanged. Both classes support `logits_to_keep`, sdpa and gradient checkpointing (correctness review).
- **KV cache for comparison:** Qwen2.5-7B uses about 56 KiB per token (28 × 2 × 512 × 2 B). OLMo-7B uses 512 KiB (about 9×) and OLMo-13B 800 KiB. transformers 4.56.2 grows the cache with `torch.cat` at every step (`cache_utils.py:116`).

### Chat formats (rendered offline from the pinned tokenizer files with transformers 4.56.2)

| | Qwen2.5 (today) | OLMo-2, all sizes | Llama-3.1 template (used for both Llama models; decision 3) |
|---|---|---|---|
| One-turn prompt | Qwen's default system turn, user turn, `<\|im_start\|>assistant\n` | `<\|endoftext\|><\|user\|>\n{u}\n<\|assistant\|>\n` | `<\|begin_of_text\|>`, a system block "Cutting Knowledge Date: December 2023 / Today Date: 26 Jul 2024", the user turn (`{u}` trimmed), the assistant header |
| Assistant header | `<\|im_start\|>assistant\n` | `<\|assistant\|>\n` (5 plain BPE tokens, ids 27, 91, 78191, 91, 397; not special) | `<\|start_header_id\|>assistant<\|end_header_id\|>\n\n` |
| End of turn | `<\|im_end\|>` | `<\|endoftext\|>` 100257 (the same id is BOS and UNK) | `<\|eot_id\|>` 128009 |
| Stops in the recipe | `<\|im_end\|>`, `<\|endoftext\|>` | `<\|endoftext\|>` | `<\|eot_id\|>`, `<\|eom_id\|>`, `<\|end_of_text\|>` |
| Pad in the recipe | `<\|endoftext\|>` | `<\|pad\|>` 100277 | `<\|end_of_text\|>` 128001 (decision 8) |
| Template tokens for one turn | 29 (gap analysis) | 12 | 35 |
| `all_special_ids` / added special tokens | 14 / 14 (the same set) | 2 / 8 | 2 / 256 |
| `clean_up_tokenization_spaces` | false | false | **true** in the 3.2 file; the gated 3.1 file is UNVERIFIED |
| Date from the clock | no | no | 3.2 template: yes (`strftime_now`); 3.1 template: no (fixed "26 Jul 2024") |

- The 3.2 template with `date_string="26 Jul 2024"` and the 3.1 template (from the API metadata) gave identical ids on my synthetic prompt. The gap analysis found the same on all 15,011 Dolly prompts. The correctness review confirmed the same text. With no date, the 3.2 template writes today's date ("08 Oct 2026").
- **Joint render** for both families: prompt, then response, then the end-of-turn token. This matches `encode_train`. ARC label boundaries pass (correctness review).
- **OLMo special tokens that are also Qwen text:** OLMo-1B's `tokenizer_config.json` at `48d788ec` lists `<|im_start|>` (100264), `<|im_end|>` (100265) and `<|fim_prefix|>`, `<|fim_middle|>`, `<|fim_suffix|>` (100258–100260) as special. Only `<|endoftext|>` stops generation (integrity review, open file).
- **Tokenizer file identity** (git blob SHA-1):
  - OLMo 1B, 7B and 13B: `tokenizer.json` `5fe172127988c3709a49d8d2ce20e11bb266cd57`, `tokenizer_config.json` `6a68ef73052b644e4a32208ae0114236db221028`, `special_tokens_map.json` `9d133a8f4995ff315a8a3e68dbba03409d214a8e`, `vocab.json` `51135344eec01a62fc4deaca39c72ac08f5b9709`; `merges.txt` `354558edcdbd64ca7abd407b8be3d5d09d39d781` (git hash-object of the file fetched at the 1B pin; not compared with the API: UNVERIFIED).
  - Llama 3.2-1B and 3.1-8B: `tokenizer.json` `5cc5f00a5b203e90a27a3bd60d1ec393b07971e8` and `special_tokens_map.json` `02ee80b6196926a5ad790a004d9efd6ab1ba6542` are equal. `tokenizer_config.json` differs: `4ff488a165e900e5129cda7c20ab32d568d2a475` (3.2) and `db88166e2bc4c799fd5d1ae643b75e84d03ee70e` (3.1; gated; not seen). Only its chat template is known (API metadata).

### Measured rates and money (local pod records; numeric fields only)

| Measure | Value | Source |
|---|---|---|
| Decode time per step, generation batch 32, 28-layer models | 97–100 ms, the same at 1.5B and 7B | my count: ledger stage seconds ÷ decode steps (Σ per batch of the longest output + 1), from `prompt_tokens`, `output_tokens` and `stop_reason` in `tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/*/` and `tmp/kill-test-gateA-b/retrieved/b-1101/tree/round1/1101-a0-e1-a1/` |
| Decode steps, untuned 7B | 12,373 greedy + 13,619 sampled; evaluation 48 min | same |
| Decode steps at e1 with loops | 30,735 greedy (all 15 batches reached the cap) + about 28,200 sampled; evaluation about 104 min at 7B, 102 min at 1.5B | same |
| Dev evaluation size | 657 dev items (arc_generation 96, arc_utility 189, harm 200, overrefusal 100, safety 72); 468 greedy generations (15 batches of 32) and 600 harm samples (19 batches of 32) | prepared-kt-dolly `manifest.json` `bank_import.items`; line counts of the q7 `eval/{init,e1}/generations.jsonl` (468) and `samples.jsonl` (600) |
| Recipe-B training (38 steps) | 6.4 min (1.5B, micro-batch 4); 12.9 min (7B, micro-batch 2) | same ledgers |
| Setup (venv and downloads) / preflight | 14.6–14.9 min / 12.4 min (1.5B, one candidate), 13.4 min (7B, two candidates); q7 `worker-bootstrap-process-001` 913 s, of which the download 98.7 s | process receipts in the same trees; safety-cost review |
| q7 preflight stages | `untuned_comparison` 143 s, `resume_check` 94 s, `generate` 173 s, `sample` 79 s | safety-cost review, from the q7 preflight ledger |
| Pod hours and cost at $1.59/h | b-1101 2.38 h, $3.79; **q7-1101 3.56 h, $5.66** (not 3.0 h); Stage 0 pods 2.97–3.04 h, $4.72–4.84 | `hosts/*/pod.json` `created_utc` and `stops.jsonl`; results record |
| Qwen-7B training memory | micro-batch 4: out of memory (76.49 GiB allocated); micro-batch 2: passed | `tmp/kill-test-7b-check/retrieved/q7-1101/tree/cuda-preflight-{1,2}/verification.json` |
| Qwen-7B fragmentation | 60.0 GB reserved against a 27.5 GB allocated peak | q7 preflight verification |
| Guard resident memory | 8.06 GB (24.05 − 15.99 GB) | the 13B fact sheet, from the q7 init ledger |
| A100 capacity | 79.25 GiB (85.1 GB) | the q7 out-of-memory message |
| Balance | $28.08 at 17:17 UTC, 7 October; 0 pods; `spendLimit` 80 | `tmp/kill-test-7b-check/account-latest.json`; results record line 138 |
| Background spend with no pods | `currentSpendPerHr` 0.015 ($0.36 per day); its cause is UNVERIFIED | same file |
| Stopped-pod storage | volume $0.20/GB/month while stopped; container disk not charged while stopped | https://docs.runpod.io/pods/pricing (read 8 October by the safety-cost review; not re-read for this revision) |

### Engine, data and tests

- Engine code identity `c52c0ebc83793fc552f84908e83542d5e46543459fcafb7be2fc9c7ff42ac597` at HEAD `b5fc1ad`.
- I re-ran the suites on 7 October, exit 0: engine **313 passed, 3 CUDA-only skips**; Stage B **172**; durability **260**.
- `prepared-kt-dolly` (`tmp/kt-prepared/prepared-kt-dolly/`):
  - manifest `9247c4bbccf212b02be7f221e2ee451d17ebf643a39a44db6e3bed6fb4d750f2`; data config `ed266d96…`;
  - `auditor/construction.json` SHA-256 `2f5802f5896915b4edb813ca2aa7bf1983d0eb5bd9fa7062da3055f3b84f483d` (`shasum -a 256`, 8 October);
  - bank files `banks/dev.jsonl`, `banks/selector.jsonl`, `hidden/hidden.jsonl`; units in `engine/groups.json`;
  - 6,072 bank items re-audited (dev 657, selector 665, hidden 4,750); 0 separate≠joint mismatches.
- Dolly lines are 1-based (`sources.parse_dolly`).
  - **Token-audit refusals** on all 15,011 rows, with the engine's own functions, the new special set and the new unk rule: Qwen 53, OLMo 51, Llama-3.1 51. Only lines 10024 (closed_qa) and 12405 (information_extraction) differ. No other line shares their normalized user text (correctness review). Neither line is in prepared-kt-dolly's units, task rows or unused lines.
  - **Separate≠joint on all rows:** Qwen 0, OLMo 0, Llama 2. Line 2558 is a unit row whose response ends in whitespace. Line 3715 is unused (correctness review).
- **Guard input cannot overflow:** Qwen3Guard needs at most 3.00 tokens per policy token (digit runs). Its template is 391 tokens. So 2,048 × 3 + 391 + about 400 < 8,192 (correctness review).
- Qwen does not change under Items 1.1–1.3: the cached Qwen2.5-1.5B-Instruct and Qwen2.5-1.5B files have `clean_up_tokenization_spaces: false`, 22 added and 14 special tokens, no unk; Qwen3Guard-Gen-4B has false, 26 and 14, no unk; no Qwen template holds `strftime_now` (integrity and correctness reviews).

### Kit facts (the `runkit/kill-test-stage0/` template)

| # | Where | What happens |
|---|---|---|
| K1 | `budget.py:16, 32` | `CAP_FALLBACK_H = 6.0`. The guard reads only its own kit's `hosts/*/pod.json`. A pod from another kit counts at 6 h. |
| K2 | `setup/extend_cap.py:1, 6` | It extends or shortens the in-pod stop and "bypasses admission". It writes nothing on the Mac, so `pod.json` keeps the old cap (q7: the lease moved the stop from 21:41 to 23:41 UTC; `operator-leases.jsonl`). |
| K3 | `orchestrate.py:129` | The preflight wait is a fixed 3,600 s. |
| K4 | `finisher.py:141`; `finisher.py:115-116` | The finisher stops watching after 10 h. A failed light pull returns without a stop. |
| K5 | `launch.py:42, 46, 50` | `budget.py`, `host.py create` and the detached `orchestrate.py` inherit the whole `os.environ`. `host.py:158` gives ssh `-F /dev/null`, so ssh sends no environment. |
| K6 | `setup/job_runner_kt.py:34-35` | When `init_equals_untuned` is not true, the runner skips the init unit and still runs the fine-tune. |
| K7 | `experiments/minimal_safety/requirements.lock` | No `--hash` lines (grep count 0). The bootstrap's pip runs as root. |
| K8 | `tmp/study-v2-20261002/process_receipt.py:7-8, 11` | The receipt records the argument list (`command`) in `started.json`. The child inherits stdin. |

## How the five models meet the engine today

| # | Where | What happens | Models |
|---|---|---|---|
| B1 | `textproc.py:89-95` | `single_token_id` refuses `<\|endoftext\|>`, because its id equals `unk_token_id`. The policy codec (`loaders.py:187`) and the preparation codec (`prepare_task.py:185`) fail. Reproduced in the fact checks. | OLMo |
| B2 | `loaders.py:188-190` | The probe must end with `<\|im_start\|>assistant\n`. TemplateError. | all five |
| B3 | Llama-3.2 template | `strftime_now` writes the host's date into every prompt (`chat_template_utils.py:453-461`). Token hashes change by day and time zone, and `runner.py:200-203, 500` then refuse. | Llama-3.2-1B |
| B4 | `prepare_task.py:157-172`; `runner.py:498-502, 524` | The bank items hold Qwen token hashes. The import re-audit refuses them, and the run refuses them again. | all five |
| B5 | `jobs.py:155-159` | The recipe's tokenizer and end-of-turn must equal the data config's, so prepared-kt-dolly cannot serve these models. | all five |
| B6 | `cuda_preflight_headroom.py:90-92`; `cuda_preflight_killtest.py:56, 198` | The row check asserts that padding rows exist (Llama has none) and checks Qwen's chat tokens (wrong rows for OLMo). | all five |
| B7 | kit `download_models_kt.py:20` | `token=False`: HTTP 401 on gated repositories. | Llama |
| S1 | `textproc.py:81-83` | Decoding with Llama-3.2's `clean_up_tokenization_spaces: true` changes the answer text that the guard judges (" ." becomes "."; reproduced locally). | Llama |
| S2 | `textproc.py:107` | `special_ids` miss added special tokens outside `all_special_ids`: OLMo 6 (fim ×3, `<\|im_start\|>`, `<\|im_end\|>`, `<\|endofprompt\|>`), Llama 254. Text that encodes to them is not refused. | OLMo, Llama |
| S3 | `cuda_preflight_killtest.py:253-256` | The batch check makes 32 new tokens only. A full-length batch is never tested, and finished rows stay in the batch (`engine.py:505-507`) with the guard loaded (`runner.py:587`). | OLMo 7B, 13B |
| S4 | `cuda_preflight_killtest.py:170-179, 276-283, 299-303` | The timed evaluation sample generates at `generation.batch_size` with the guard loaded. Only `memory_preflight` is caught. An out-of-memory error elsewhere writes `partial-verification.json` and exits non-zero, so a skip rule never sees it [C-SF2]. | all, mostly 7B/13B |
| S5 | `scoring.py:60-64, 81`; `textproc.py:81-83` | `Codec.decode` keeps special tokens in the answer text. The guard's control strings are all its added and special tokens. An answer with one of them gets "control string in guard input; not scored" and counts in U's denominator as not Unsafe [I-S3]. | OLMo (`<\|im_start\|>`, `<\|im_end\|>`, `<\|fim_…\|>`) |
| S6 | `ss_fixtures.py:52, 69, 494, 518-534` | The fixture's `added_tokens_decoder` entries have no `.special`. Its `decode` takes no `clean_up_tokenization_spaces`. The only fixture model is a tiny Qwen2 with `gradient_checkpointing: False`, so the checkpointing path (`loaders.py:184-186`) never ran [C-M1, C-SF4]. | tests |
| N1 | `runner.py:1049` | `score-audit` parses Qwen prompts only. The probes do not use it. The Mac second judge reads the v3 bank by prompt id. | not needed |

## Challenge before building

**Simpler alternatives, and why they are not chosen:**
- **Recipe-only path (the Qwen-7B pattern):** impossible. B1 and B2 are hard refusals in code.
- **Re-prepare the banks from the v3 raw sources with each tokenizer:** the token limits can change bank membership, and it repeats the held-out construction. Rejected.
- **One kit with five hosts in one plan:** the kit assumes one recipe per plan. Per-host recipes would touch every kit script. Chosen instead: a tracked template kit and one working copy per probe (the 7B-check pattern).
- **The open mirrors instead of the gated repositories:** they avoid the token on the pod, but they lose the provenance of Meta's gate, and the NousResearch mirror's `tokenizer_config.json` differs from Meta's (oid `421cda36…`). A narrower form of this (open-mirror weights with equal SHA-256, Meta's small files from the Mac fetch) is open question 5.
- **Re-tokenize all three banks:** not needed and riskier. The probes read only dev. An encode failure in selector or hidden could only be diagnosed by reading held-out items. Chosen: dev only [I-S5].
- **Skip the 13B probe:** it saves $9–14 and the batch-size question. Open question 6.

**Weak assumptions, and the check that settles each:**
1. Exactly 2 Dolly rows change eligibility under the new tokenizers (gap analysis; correctness review). Settled by the asserted counts plus `construction_sha256` (Item 2a) at the Mac preparation. If wrong, the preparation refuses.
2. OLMo's `<|endoftext|>` row and Llama's chat rows are trained (inference only; no weights read). Settled by the preflight row check and by the untuned stop reasons.
3. OLMo-13B generation fits at batch 16 (estimate about 71 GB of 85.1 GB). Settled by the full-length generation check. Batch 16 is the last 13B candidate. If no g16 candidate passes, the preflight ends with `ok: false` [SC-B2].
4. Decode time per step grows with the layer count. For the MHA OLMo models near 2,048 new tokens it is UNVERIFIED (KV cache 512–800 KiB per token against Qwen-7B's 56 KiB; the cache is copied at every step). Settled by the full-length check's measured rate and the cap gate (Item 4.8) [SC-S2].
5. Qwen behaviour does not change. Settled by the golden task file (Item 1.0) and Mac check 0 [I-S1].
6. The new model classes run correctly through the engine. Settled on CPU by `test_ss_family_models.py` (Item 1.5) before any pod [C-SF4].

**Decisive cheap checks, in order:**
1. CPU (builder): write the golden task file with the HEAD code before any edit (Item 1.0).
2. CPU (builder): the model-class tests and the codec check script on the real tokenizer copies in the workspace.
3. Mac (lead): Mac check 0, the Qwen codec and decode equality (Item 1).
4. Mac (lead): re-prepare prepared-kt-dolly with the new engine. The manifest must stay `9247c4bb…`.
5. Mac (lead): prepare the OLMo set. `engine/groups.json` and `auditor/construction.json` must be byte-equal to prepared-kt-dolly's.
6. Pod (with approval): the `olmo2-1b` preflight, the cheapest GPU check of the whole path.

## Decisions in this brief (defaults; the lead may change them before the build)

1. **Banks: rewrite the token fields of the dev bank only** (option A, narrowed) [I-S5]. Dev text and every other field stay byte-identical; `prompt_tokens`, `token_sha256` and `label_tokens` are recomputed. The selector and hidden files are copied byte for byte and are not re-audited. This changes the previous brief's import rule ("refuse if any `token_sha256` differs") for the listed file only. Option B (a token sidecar) is open question 1.
2. **Same rows as Qwen:** `eligibility.exclude_lines: [10024, 12405]`, applied at the token-audit step, keeps every unit and task row identical to prepared-kt-dolly's [C-M2, I-M1]. The alternative lets 2 units change by 50 rows (open question 2).
3. **Llama date, option L1:** both Llama probes use the Llama-3.1-8B tokenizer (fixed date "26 Jul 2024"). The 3.2-1B recipe pins `model.tokenizer` to it. The engine refuses any template that reads the clock. Option L2 (a `chat_template_kwargs` field) is open question 3.
4. **Generation batch 16 for OLMo-13B,** for its baseline and its e1 unit alike. `olmo2-7b` also gets g16 candidates after its batch-32 candidates, reached only after a batch-32 candidate records `generation_memory_ok: false` [C-SF1]. Every other probe keeps 32. Open question 4.
5. **Two prepared sets:** `prepared-kt-dolly-olmo2` (one tokenizer for three sizes) and `prepared-kt-dolly-llama3` (L1 makes one tokenizer for both). A third set is needed only under L2.
6. **No table by architecture.** The assistant header is an optional recipe field. The preflight's chat tokens come from the template itself [C-SF3, I-M3]. Reason: Llama-2-7B-Chat is also `LlamaForCausalLM`, with another header and no `<|begin_of_text|>`.
7. **One template kit, one working copy per probe.**
8. **Llama pad = `<|end_of_text|>`** (a trained row; Qwen's pad is also an end token). The alternative is `<|finetune_right_pad_id|>` (128004; Meta's pad slot by name only; UNVERIFIED). Masking makes the choice numerically neutral if the row is finite.
9. **The HF token never touches a file on the pod** [SC-B1]. A fine-grained read token is a precondition. The token goes over ssh stdin to one gated-download command after the bootstrap (Item 5). The no-token-on-pod alternative is open question 5.
10. **A cap gate before every job** [SC-B2]. The orchestrator starts a job only when the projected upper time fits the remaining cap with 30 min to spare.
11. **No baseline, no probe** [I-S4]. If the preflight does not prove `init_equals_untuned`, the job runner stops after the preflight.

## Item 1: model-family support in the engine

**Where:** `textproc.py`, `loaders.py`, `config.py` (validator and module doc). `runner.py`, `engine.py`, `jobs.py` and `headroom.py` do not change. Each change keeps Qwen's behaviour, bytes and identities; only the code identity changes.

0. **First step, before any edit: the golden task file** [I-S1]. The existing golden (`tests/golden/removal-arms-8dd630c.json`) predates `prepare_task`, harm samples, `--base-eval` and the task query definition (`removal_digest.py:8`). The kill-test tests pin no digest. The fixture tokenizer cannot detect a Qwen change.
   - With the HEAD code, write `experiments/safety_selection/tests/golden/kt-task-<HEAD short sha>.json` (`kt-task-b5fc1ad.json` if the workspace is at `b5fc1ad`).
   - It holds:
     - the SHA-256 of every file that `fx.prepared_task_files` returns (`ss_fixtures.py:460`);
     - `removal_digest.unit_digest` (`removal_digest.py:38`) of the init unit and of the a0 e-unit of one `calibrate --base-eval` run with harm samples on the tiny fixture.
   - A new test compares the new code with this file.
   - When `exclude_lines` and `retokenize` are absent, the preparation adds no manifest key, no receipt key and no zero counter.
1. **`single_token_id`** (`textproc.py:89-95`): apply the unk rule only when the token string is not the tokenizer's own `unk_token`.
   - OLMo's `<|endoftext|>` (EOS = BOS = UNK = 100257) then passes (100257, checked by the correctness review).
   - An unknown string still refuses: it maps to the unk id, but it differs from `unk_token` (`<|bogus|>` refuses).
   - Qwen's `unk_token` is None: no change.
2. **`build_codec`** (`textproc.py:98-108`):
   - `special_ids` = `all_special_ids` ∪ the ids of `added_tokens_decoder` entries with `special` true ∪ {eos, pad, stops}. Read the flag as `getattr(entry, "special", False)`, because the fixture's entries have no `.special` (`ss_fixtures.py:52`) [C-M1]. For Qwen2.5-1.5B-Instruct and Qwen3Guard-Gen-4B the added special set equals `all_special_ids` (14 = 14), so their codecs do not change.
   - Do not add plain (non-special) added tokens. Qwen has 8 (`<tool_call>` and others); adding them could change Qwen's audit. OLMo's 14 plain tokens (`<|extra_id_N|>`, `|||PHONE_NUMBER|||` and others) are handled by forbidden substrings (Item 2).
   - Refuse a chat template that reads the clock: the text `strftime_now` in the template (a string, or any value of a dict of templates) raises `TemplateError("date-dependent chat template")`. The guard lives in `build_codec`, not in `load_tokenizer`.
3. **`Codec.decode`** (`textproc.py:81-83`): pass `clean_up_tokenization_spaces=False`.
   - This makes the code match its own contract ("Exact text of the ids").
   - Qwen and OLMo already use false, so their text does not change.
   - Give `FixtureTokenizer.decode` (`ss_fixtures.py:69`) a `clean_up_tokenization_spaces` keyword [C-M1]. The golden digests must not change.
4. **Assistant header** (`loaders.py:188-190`):
   - Add the optional recipe field `model.assistant_header` (a string). When it is absent, the header is `"<|im_start|>assistant\n"`, today's fixed check. Every existing recipe keeps its bytes and meaning. Document it in `config.py`'s optional-field list, beside `model.tokenizer`.
   - The loader refuses unless:
     - the probe ends with the header and holds `<<probe>>`;
     - the header equals the template's own generation suffix: the one-turn render with `add_generation_prompt=True` minus the render with `False` (which must be its prefix).
   - Put both checks in one pure function in `textproc.py`, so that CPU tests can reach it.
   - Add the header to the policy identity only when the field is present, as `tokenizer_snapshot` is added at `loaders.py:194`.
5. **Model-class tests (new file `experiments/safety_selection/tests/test_ss_family_models.py`)** [C-SF4]. Build a tiny random `Olmo2ForCausalLM` (untied, with q_norm/k_norm) and a tiny random `LlamaForCausalLM` (tied, GQA, `rope_type` llama3), with the seven targets, on CPU in float32. Nothing is downloaded. Assert:
   - (a) the `lora_parameters` count = r·Σ(in+out) per layer, and no trainable name holds `norm`;
   - (b) with B = 0, the logits are bit-equal to the plain model's;
   - (c) `accumulate_gradients` with gradient checkpointing (`use_reentrant` False, as `loaders.py:184-186`) equals the run without it, in losses and gradients;
   - (d) `greedy_generate` at batch 2 (left-padded) equals batch 1.
   - The correctness review ran these four checks as a scratch script: all passed (differences 0.0). So the test should pass; it protects the path that the 7B, 8B and 13B ladders need.

**Acceptance and tests (CPU, synthetic fixtures):**
- The golden task test passes against the file written in step 0.
- An OLMo-like fixture tokenizer (UNK = EOS = BOS, a distinct pad, added special tokens outside `all_special_ids`, plain role markers) builds a codec. An unknown token still refuses.
- A clock-reading template refuses. The same template with a fixed date builds.
- `special_ids` grow only by added special tokens. A Qwen-like fixture gives the same set as before.
- `decode` passes `clean_up_tokenization_spaces=False`.
- The header check: the right header passes; a wrong header refuses; a header that is not the generation suffix refuses; an absent field means Qwen's header.
- `validate_recipe` accepts the new field. Every existing recipe validates with the same hash.
- The four model-class tests pass.
- The golden regression (`golden/removal-arms-8dd630c.json`) and all existing tests are unchanged.

**Standalone check (not pytest; outside the code identity):** `scripts/family_codec_check.py`.
- Inputs: a tokenizer folder; the end-of-turn token, stops, pad and header; optionally a chat-template file; optionally `--dolly PATH`.
- Output, counts and ids only:
  - the token ids; the sizes of `all_special_ids` and of the new special set; the generation suffix; the template tokens for one turn; the date-guard result; the derived chat tokens (Item 4.1);
  - decode round trips of synthetic strings;
  - with `--dolly`: line numbers of rows over 3,072 or 1,536 tokens; the separate≠joint count and line numbers; decode round-trip failures on Dolly responses. Never text.
- The builder runs it on the workspace's reference copies. The lead runs it on the Mac caches.

**Mac check 0 (the lead, after integration, before Mac check 1)** [I-S1]:
- Make a git worktree at `b5fc1ad` (outside the repository's working tree).
- A CPU script builds each codec that the Qwen recipes build, once with the old code and once with the new code:
  - the policy codec (recipe B's end-of-turn, stops and pad) on Qwen2.5-1.5B-Instruct;
  - the guard codec on Qwen3Guard-Gen-4B;
  - the preparation codec.
- It asserts equal `eos_id`, `stop_ids`, `pad_id`, `special_ids` and probe text.
- Then it decodes the `output_ids` of every record in `generations.jsonl` and `samples.jsonl` under `tmp/kill-test-gateA-b/retrieved/` and `tmp/kill-test-7b-check/retrieved/` with the new `Codec.decode`. It counts the records whose result differs from the stored `text`. It prints counts only.
- Pass: every assert holds and the count is 0.

## Item 2: per-tokenizer prepared data

**Two data configs**, each equal to `configs/study-kt-data-dolly.json` except:

| Field | `study-kt-data-dolly-olmo2.json` | `study-kt-data-dolly-llama3.json` |
|---|---|---|
| `name`, `purpose`, `amendments` | new; the amendments state the new options and why | same |
| `tokenizer.repo_id` / `revision` | `allenai/OLMo-2-0425-1B-Instruct` / `48d788ec…` | `meta-llama/Llama-3.1-8B-Instruct` / `0e9e39f2…` |
| `tokenizer.end_of_turn_token` | `<\|endoftext\|>` | `<\|eot_id\|>` |
| `eligibility.forbidden_substrings` | the old three plus `"<\|"` and `"\|\|\|"` | the old three plus `"<\|"` |
| `eligibility.exclude_lines` (new) | `[10024, 12405]` | `[10024, 12405]` |
| `eligibility.expected.construction_sha256` (new) | `2f5802f5…483d` (prepared-kt-dolly's) | same |
| `banks_from.retokenize` (new) | `["banks/dev.jsonl"]` | `["banks/dev.jsonl"]` |

- Unchanged: the source pin, the categories, `units`, `design_seed` 20261006, the seed namespaces, the limits 3,072 and 1,536 (OLMo: 1,536 + 2,048 = 3,584 ≤ 4,096 positions), and the asserted counts.
- **The asserted counts are Qwen's** (records, eligible, 600 per unit). With `exclude_lines`, the eligible lists must equal Qwen's. The counts and `construction_sha256` together check it [I-S6]. Counts alone do not: `_check_expected` compares counts per category only (`prepare_task.py:239-245`), so a swap of two rows inside one category would pass.
- The gap analysis found no Dolly row that holds `<|` or `|||` (the integrity review confirmed 0 of 15,011). The new forbidden substrings therefore change no row. They cover OLMo's plain role markers, every `<|…|>` token and OLMo's PII placeholders.

**2a. `eligibility.exclude_lines`** (optional; `config.py` validator and `prepare_task.py`):
- A sorted list of distinct positive Dolly line numbers.
- **Where it acts** [C-M2, I-M1]: at the token-audit step (`prepare_task.py:228-237`), after the first-row-per-user-text step (`:220-227`). A listed line is counted as `excluded_line` instead of being encoded. This is where Qwen dropped these two rows, so `near_duplicates_at_or_above` and every count before the token audit stay equal to prepared-kt-dolly's.
- **Refusals:** a listed line that is not in the source; a listed line that an earlier rule already removed.
- Why it works: the OLMo and Llama audits make exactly these two Qwen over-limit rows eligible (53 → 51). Without them, every category's eligible list in file order equals Qwen's. The shuffle and the opaque ids derive from the design seed and the line (`prepare_task.py:248-258`), so the units and task rows are the same rows.
- Record its rule string (for example `TASK_EXCLUSION_RULE`) in the manifest only when the key is present. **Keep `TASK_RULE` byte-identical,** so that a re-preparation of prepared-kt-dolly still gives `9247c4bb…`.
- **`eligibility.expected.construction_sha256`** (optional) [I-S6]: when it is present, the preparation refuses unless the SHA-256 of the `auditor/construction.json` it writes equals the field.

**2b. `banks_from.retokenize`** (optional; `config.py` and `prepare_task.py`) [I-S5]. A list of bank file paths, as in `bank_import.files` (`banks/dev.jsonl`, `banks/selector.jsonl`, `hidden/hidden.jsonl`). The new data configs list only `banks/dev.jsonl`.
1. Verify the source manifest and the three file hashes, as today.
2. **For each listed file:**
   - Parse it. Refuse unless `jsonl_bytes(parsed)` equals the source bytes (a lossless round trip; v3 wrote the files with `jsonl_bytes`, `prepare.py:716`).
   - For each item, recompute only the token fields with this codec: `prompt_tokens`, `token_sha256`, and `label_tokens` for `arc_utility` (the fields `prepare._token_audit` adds, `prepare.py:549-564`). TooLong, ControlTokenError or BoundaryMismatch refuses the preparation. The message gives bank, kind and count only.
   - Assert that every other field, the item order and the item count are unchanged. Write the file with `jsonl_bytes`.
3. **Each file that is not listed** is copied byte for byte and is not re-audited. The hidden file keeps its sealed hash (`0fb47595…`, integrity review).
4. The overlap and disjointness checks still read all three files as text.
5. Record in `bank_import`: the source hashes, the new file hashes, the lists `retokenized` and `not_audited`, items per bank and kind, the count of items whose hash changed, the largest prompt in tokens, and a rule string `BANK_RETOKENIZE_RULE`. The rule string states that, for the listed files, it replaces `TASK_RULE`'s last sentence ("copied byte for byte and re-audited") [I-M5].
6. **Bank scan, counts only** (listed files only): count the items whose text holds any forbidden substring of the config, by bank and kind. Never drop an item. If the dev count is not 0, write the affected dev prompt ids (ids only) to the manifest [I-M6]. The reading then reports U with and without them (Item 8). The frozen measures use every item.
- Without the key, the old rule applies unchanged: a different tokenizer still refuses.
- No runner change: `runner._prompt_ids` (`runner.py:498-502`) compares against the rewritten fields. A job that evaluates a not-audited bank refuses there, because its `token_sha256` values are Qwen's.
- Analysis joins still use prompt ids with `prepared-v3-inj05/auditor/construction.json`. The Mac second judge reads prepared-v3-inj05's dev bank by prompt id (`tmp/kill-test-7b-check/second_judge_kt.py`), so it is not affected.

**Acceptance and tests (synthetic).** Use fixture tokenizer A (Qwen-like) and fixture tokenizer B (other ids; it makes 2 rows eligible that A puts over the limit):
- B with `exclude_lines` and `retokenize: ["banks/dev.jsonl"]`: `engine/groups.json` and `auditor/construction.json` are byte-equal to A's preparation. Train and query rows have the same ids and the same prompt and response bytes. The dev bank differs only in token fields. The selector and hidden files are byte-identical to the source.
- A wrong `construction_sha256` refuses. A listed line that an earlier rule removed refuses. A listed line outside the source refuses.
- A changed non-token field refuses. A failed round trip refuses. An encode failure refuses, with bank, kind and count only.
- A job that evaluates the not-audited selector bank refuses at `_prompt_ids`.
- B without `retokenize` refuses, as before. A's preparation (files and manifest) is byte-identical to today's.
- Preparation is deterministic: twice, and under another `PYTHONHASHSEED`.
- No prompt or response text reaches stdout or an error message.

**Mac checks (the lead, after integration and Mac check 0):**
1. Re-prepare prepared-kt-dolly with the new engine. The manifest must be `9247c4bb…`.
2. Fetch the OLMo tokenizer files (Item 5b). Prepare `prepared-kt-dolly-olmo2` twice, and once under another `PYTHONHASHSEED`. Expect:
   - identical manifests, `expected_counts: matched` and a matching `construction_sha256`;
   - `engine/groups.json` and `auditor/construction.json` byte-equal to prepared-kt-dolly's;
   - 657 dev items with only token fields changed; selector and hidden byte-identical to the source; the bank-scan counts recorded;
   - `separate_vs_joint_encoding_mismatches` = 0 [C-M4].
3. Run `scripts/family_codec_check.py --dolly` on the OLMo cache. Expect separate≠joint 0.
4. Repeat steps 2 and 3 for `prepared-kt-dolly-llama3` after the gated tokenizer fetch. Expect `separate_vs_joint_encoding_mismatches` = exactly 1, line 2558 (line 3715 is unused); the codec check over all rows gives 2 (lines 2558 and 3715) [C-M4].
   - Any other value in steps 2–4 stops the preparation for review.
5. Write the frozen manifests into the working kits.

## Item 3: recipes and memory candidates

**Base:** `configs/study-kt-instruct-r64-b-20261007.json` (recipe B). Change only:
- `model`: `repo_id`, `revision`, `tokenizer` (when needed), `architecture`, `end_of_turn_token`, `stop_tokens`, `pad_token`, `assistant_header`, `attn_implementation`, `lora.expected_trainable_parameters`;
- `train`: `micro_batch`, `grad_accum` (their product stays 128), `gradient_checkpointing`;
- `generation.batch_size` (the g16 candidates only);
- `name`, `purpose`.

The `guard` section stays byte-identical to recipe B's in every candidate, eager candidates included [I-S2]. Only `model.attn_implementation` may be `eager`. (The Qwen eager recipes set `guard.attn_implementation: eager`; every Qwen kill-test number came from an sdpa judge, for example q7's chosen mb2 sdpa recipe. The eager fallback exists for the policy's resume fixture, `cuda_preflight_killtest.py:112-123`; no check needs an eager guard.)

Every other byte stays recipe B: LR 1e-4 constant, AdamW, rank 64, alpha 128, the seven targets, checkpoints q, e1 and e3, limits 3,072 and 1,536, greedy 2,048 new tokens with 3 samples at T 0.7, the guard and ARC.

**Model fields:**

| Probe | `model.tokenizer` | `architecture` | End of turn / stops / pad | `assistant_header` | Expected trainable |
|---|---|---|---|---|---|
| `olmo2-1b` | absent | `Olmo2ForCausalLM` | `<\|endoftext\|>` / [`<\|endoftext\|>`] / `<\|pad\|>` | `<\|assistant\|>\n` | 48,234,496 |
| `olmo2-7b` | OLMo-2-0425-1B-Instruct @ `48d788ec…` | `Olmo2ForCausalLM` | same | same | 159,907,840 |
| `olmo2-13b` | OLMo-2-0425-1B-Instruct @ `48d788ec…` | `Olmo2ForCausalLM` | same | same | 250,347,520 |
| `llama32-1b` | Llama-3.1-8B-Instruct @ `0e9e39f2…` | `LlamaForCausalLM` | `<\|eot_id\|>` / [`<\|eot_id\|>`, `<\|eom_id\|>`, `<\|end_of_text\|>`] / `<\|end_of_text\|>` | `<\|start_header_id\|>assistant<\|end_header_id\|>\n\n` | 45,088,768 |
| `llama31-8b` | absent | `LlamaForCausalLM` | same | same | 167,772,160 |

**Candidate ladders** (the preflight takes the first candidate that passes). Names: `configs/study-kt-<probe>-r64-b-<candidate>-20261008.json`.

| Probe | Candidates in order (micro-batch × accumulation) |
|---|---|
| `olmo2-1b`, `llama32-1b` | `mb4` (4 × 32, sdpa), `mb2` (2 × 64, sdpa), `mb2-eager` |
| `llama31-8b` | `mb4`, `mb2`, `mb1-gc` (1 × 128, gradient checkpointing), `mb1-gc-eager` (the Qwen-7B ladder) |
| `olmo2-7b` | `mb4`, `mb2`, `mb1-gc`, `mb1-gc-eager`, then `mb2-g16`, `mb1-gc-g16` (generation batch 16; reached only after a batch-32 candidate records `generation_memory_ok: false`) [C-SF1] |
| `olmo2-13b` (generation batch 16) | `mb2-g16`, `mb1-g16`, `mb1-gc-g16`, `mb1-gc-eager-g16`. No batch-8 candidate [SC-B2]. |

That is 20 recipes (3 + 3 + 4 + 6 + 4).
- A failed training-memory candidate costs about 1.6 min (the Qwen-7B micro-batch-4 attempt). A failed generation candidate costs more: the run up to the full-length check, about 10–25 min (ESTIMATE).
- **If every 13B g16 candidate fails,** the preflight ends with `ok: false`, the F1 path stops the pod, and the lead returns to the user (a larger cap and a top-up for a batch-8 recipe, or no 13B probe). At batch 8 the e1 evaluation with loops alone is about 5.7–9.9 h (safety-cost estimate), so batch 8 cannot fit the 11 h cap with the rest of the job.
- **`olmo2-7b` at g16:** decision 4 and open question 4 also apply. The cap gate (Item 4.8) will probably refuse a g16 job at the 5.5 h cap (Item 7 estimate: about 6.7 h projected against about 4.25 h available), unless the measured g16 rate per step is much lower. Then the pod stops, and the measured rate sets the cap for a later attempt (user approval).

**Generation memory (ESTIMATES: resident + KV cache at batch × 2,450 positions):**

| Probe | Resident (weights + guard 8.06 GB + LoRA and Adam) | KV at the recipe's batch | Total, against 85.1 GB |
|---|---|---|---|
| `olmo2-1b` | about 11.6 GB | 10.3 GB (32) | about 22 GB |
| `olmo2-7b` | about 24.6 GB | 41.1 GB (32) / 20.6 GB (16) | about 66 GB / 45 GB |
| `olmo2-13b` | about 38.5 GB | 64.2 GB (32) / 32.1 GB (16) | about 103 GB, **out of memory** / 71 GB |
| `llama32-1b` | about 11.0 GB | 2.6 GB (32) | about 14 GB |
| `llama31-8b` | about 26.1 GB | 10.3 GB (32) | about 36 GB |

- 2,450 positions = the longest development prompt (338 Qwen tokens in the 7B generations; 387 in the whole v3 bank) plus 2,048 new tokens, rounded up.
- Fragmentation is real: the Qwen-7B preflight reserved 60.0 GB against a 27.5 GB allocated peak. `olmo2-7b` at batch 32 (about 66 GB) is therefore at risk; that is why it has g16 candidates. Only the full-length check (Item 4) decides.
- Training memory at 7B–13B is UNVERIFIED. The memory preflight on the longest rows decides. The gradient-checkpointing path (`loaders.py:184-186`) is tested on CPU by Item 1.5, but has not yet run on a GPU.

**Tests:**
- Each recipe differs from recipe B only in the listed fields.
- Every candidate's `guard` section equals recipe B's [I-S2].
- The candidates of one probe differ from each other only in the training, attention and generation-batch fields.
- Each count equals the meta-device count above; each recipe validates.
- Report each recipe hash and training identity.

**Standalone check:** `scripts/family_lora_count.py --config CONFIG_JSON --recipe RECIPE` builds the meta-device model, applies the recipe's LoRA config and prints the count and the match. The builder runs it on the reference configs.

## Item 4: the preflight

**New script `scripts/cuda_preflight_family.py`.** It is the kill-test preflight with the changes below. Import its helpers. Leave `cuda_preflight_headroom.py`, `cuda_preflight_headroom_v3.py` and `cuda_preflight_killtest.py` byte-identical.

1. **Chat tokens come from the template, not from a table** [C-SF3, I-M3]:
   - chat tokens = the ids of `codec.conversation_ids("<<probe>>", "<<reply>>")` (`textproc.py:72`) that are in `codec.special_ids` (after Item 1.2);
   - record each string and id; refuse an empty set;
   - this gives Qwen {151644, 151645}, OLMo {100257} and Llama-3.1 {128000, 128006, 128007, 128009}: the same sets as today's `CHAT_TOKENS` and revision 1's table (checked by the correctness review);
   - test: the Qwen-like fixture gives `<|im_start|>` and `<|im_end|>`.
2. **Comparison rows:**
   - the padding rows (ids ≥ `len(tokenizer)`) when they exist: OLMo 100,278–100,351, 74 rows;
   - otherwise the `<|reserved_special_token_N|>` rows, minus the chat tokens and the pad: Llama has no padding rows;
   - record `comparison_kind`. Check the input weights and the output weights the model uses (OLMo and Llama-8B are untied; Llama-1B is tied);
   - `chat_rows_distinct` = no chat row is bit-identical to a comparison row. This replaces `special_rows` (`cuda_preflight_headroom.py:82-97`), which asserts padding rows at :92.
3. **`tokenizer_comparison`** records the family's chat tokens, not Qwen's `SPECIAL` [C-M6, I-M7]:
   - load the model's own tokenizer only for `single_token_id` lookups and its template hash; never call `build_codec` on it; record `own_template_reads_clock` (for Llama-3.2-1B it is true, so a codec from it would refuse);
   - `load_plain_model` uses `load_tokenizer` only for the snapshot path (`cuda_preflight_killtest.py:126-140`); keep it so;
   - with `model.tokenizer`, the verdict field `tokenizer_ok` needs `same_vocabulary` true and equal chat-token ids. For OLMo it also needs `same_chat_template` true. For `llama32-1b`, `same_chat_template` false is expected (decision 3) and recorded. Without `model.tokenizer`, `tokenizer_ok` is true.
4. **Order of the GPU steps and the full-length generation check** [C-SF2, SC-M1]:
   - Order: memory preflight → untuned comparison → resume check → batch check → `session.guard(ledger, out)` (`runner.py:137`; the timed sample then reuses it) → full-length generation check → timed evaluation sample → BOS record.
   - **The check:** one batch of `generation.batch_size` copies of the longest dev generation prompt (by tokens), `max_new_tokens` from the recipe, `stop_ids` empty, so every row runs to the cap. The optimizer state exists and the guard is loaded, as in a real evaluation.
   - **Records** [SC-S2]: peak allocated and reserved bytes; seconds; the mean ms per step over the last 256 steps; `torch.cuda.memory_stats()['num_alloc_retries']`; `ms_per_step_full` = the larger of (seconds ÷ `max_new_tokens`) and that last-256 mean. Time the steps through the engine's `check` callback (`greedy_generate`'s `check`, `engine.py:516-519`, called once per step at `:504`). Do not change `engine.py`.
   - **Out of memory is a verdict:** one `except torch.cuda.OutOfMemoryError` covers both the full-length check and the timed sample: `generation_memory_ok: false`, `use_this_recipe: false`, write `verification.json`, exit 0.
5. **OLMo BOS record** (diagnostic, not a verdict; only when the template starts with the BOS token):
   - the end-of-turn log-probability on the first 8 training examples with and without the leading BOS;
   - greedy agreement to 64 tokens and stop reasons on the three engineering prompts with and without it;
   - numbers only. Why: OLMo-1B's card says the template has no BOS, but the shipped template has one (fact sheet);
   - the BOS record never changes the template or the prompts [I-M8].
6. **Verdict:** `use_this_recipe` = `memory_ok` and `generation_memory_ok` and `fixture_exact` and `chat_rows_distinct` and `tokenizer_ok`. `init_equals_untuned` stays a verdict that never stops the preflight; the job runner acts on it (Item 6).
7. **Wrapper `setup/preflight_probe.py`** (in the kit): as `preflight_kt.py`, plus:
   - after a candidate fails with `generation_memory_ok: false`, skip every later candidate whose `generation.batch_size` is at least as large;
   - for a gated probe, refuse to start unless `gated-download-receipt.json` exists and says `ok` (Item 5c).
8. **Cap gate** [SC-B2]. `PREFLIGHT-DONE.json` also records:
   - `ms_per_step_full` of the chosen candidate;
   - `projected_job_upper_s` = the untuned evaluation from `projection_to_dev_bank` + the e1 evaluation with every batch capped (`ms_per_step_full` × 2,049 × (⌈greedy prompts ÷ b⌉ + ⌈harm samples ÷ b⌉), with the engine's own batch counts, plus the projection's non-generation stages) + training (resume-check seconds per step × 38) + 900 s. For the dev bank the batch counts are 15 + 19 at b = 32 and 30 + 38 at b = 16;
   - `governing_stop_utc` (from the pod timer's `heartbeat.json`, as `extend_cap.py` reads it) and `cap_remaining_s` at that time.
   - `orchestrate.start_job` recomputes the remaining seconds from `governing_stop_utc` and refuses when `projected_job_upper_s > remaining − 1,800`. It logs `cap-insufficient`, and the F1 path stops the pod.

- The untuned comparison holds a second, plain copy of the model. At 13B that is about 55 GB before training: it fits (estimate).
- **Preflight time per size (ESTIMATE, with the full-length check)** [SC-S2]: 1B about 15 min; 7B/8B 20–30 min; 13B 25–60 min. One passing 13B candidate takes about 23 min, scaled from q7's stages.

**Tests (CPU):**
- the chat-token derivation (Qwen-like, OLMo-like and Llama-like fixtures) and its refusal of an empty set;
- the comparison-row choice: padding rows, reserved rows, or none (then the verdict is null and the recipe is not used);
- the verdict logic with `generation_memory_ok` and `tokenizer_ok`;
- an out-of-memory error (injected) in the full-length check, and in the timed sample, gives a verdict and exit 0, not a crash;
- the wrapper's skip rule and its gated-receipt refusal;
- the cap-gate arithmetic and the `start_job` refusal (fake times).

**Pod check:** the chosen candidate's `verification.json` becomes `expected-fixture-probe.json` in that probe's working kit.

## Item 5: the gated download and the HF token

**Rules** [SC-B1]:
- The engine never handles credentials. `assets.fetch_models` keeps `token=False`.
- The token exists only in these places:
  - the user's secrets file;
  - the environment of the Mac commands that need it: `fetch_tokenizers_mac.py`, `launch.py` and the `orchestrate.py` child that `launch.py` starts. `launch.py` gives `budget.py` and `host.py create` an environment without the token variable. `orchestrate.py` gives every child process an environment without it;
  - the stdin of one ssh command, and the memory of the one pod process that reads it.
- The token is never written to a file on the pod. It is never printed, logged, put in an argument list, committed or bundled.

**5a. Precondition (not an open question).** Before any pod receives a token:
- the user creates a fine-grained token with read access to the two meta-llama repositories only. Hugging Face recommends "a fine-grained token with read access to that model" (https://huggingface.co/docs/hub/security-tokens);
- the user then revokes the exposed token (FOCUS.md:82: "broad write scopes and appeared in chat");
- if the user keeps the FOCUS.md:82 order (rotate after the downloads), record that decision and its reason in this brief before the first gated pod.
- For a gated probe, `launch.py` checks the token before `create`:
  - `GET https://huggingface.co/api/whoami-v2` with the token in the Authorization header only. Refuse unless `auth.accessToken.role` is `fineGrained` or `read` (huggingface_hub 0.36.2 reads this field, `hf_api.py:1828-1851`). Record only the role. The role does not prove read-only scopes; the scope fields' layout is UNVERIFIED, so the user confirms the scopes when creating the token;
  - `GET https://huggingface.co/<repo>/resolve/<pin>/<file>` with `Range: bytes=0-0` for every file in the gated download plan [SC-S6]. Refuse unless every reply is 206. Record the status codes only.

**5b. Mac: `runkit/family-probe/fetch_tokenizers_mac.py FAMILY`** (the lead runs it, with the user's download approval):
- `olmo2`: OLMo-2-0425-1B-Instruct @ `48d788ec…`, `token=False`; files `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `vocab.json`, `merges.txt`.
- `llama3`: Llama-3.1-8B-Instruct @ `0e9e39f2…`. Read the token once from an environment variable. The variable name is an option with the default `HF_TOKEN`; the real name in the secrets file is UNVERIFIED. Files: `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`. Run it after 5a (recommended).
- Use `snapshot_download(..., allow_patterns=[exact names])` into the normal HF cache, so that `load_tokenizer` finds the pinned snapshot.
- Verify each file's git blob SHA-1 against the pins under "Facts". Refuse a `.safetensors` file in the folder.
- Receipt: repository, revision, files, sizes, oids and `token_used: true|false`. Never the token.

**5c. Pod.**
- **The bootstrap downloads only open repositories** (the guard, the OLMo weights and the other open files). `setup/download_models_probe.py` without `--gated` refuses a gated repository.
- **`host.py gated-download HOST`** (new; replaces revision 1's `put-secret`). After `BOOTSTRAP-READY.json`, `orchestrate.py` runs it for a gated probe:
  - it runs `ssh … 'cd R && python3 process_receipt.py --out gated-download-001 -- venv/bin/python setup/download_models_probe.py --gated --token-stdin'`;
  - it writes the token and a newline to ssh's stdin (`input=`), never to the argument list. `process_receipt.py` records only the argument list and passes stdin to the child (`process_receipt.py:7-8, 11`);
  - it captures all output and writes only `hosts/HOST/gated-download.json` = {utc, ok, exit}.
- **`setup/download_models_probe.py --gated --token-stdin`:**
  - it reads `probe.json` (packed) and one line from stdin. It keeps the token in memory only and passes it as `token=` to `snapshot_download`. It never writes it;
  - its environment sets `HF_HUB_DISABLE_TELEMETRY=1` and `HF_HUB_DISABLE_IMPLICIT_TOKEN=1`, and never sets `HF_TOKEN`;
  - it downloads the gated policy weights and files and, for `llama32-1b`, the pinned Llama-3.1-8B tokenizer files;
  - after the downloads it asserts that `~/.cache/huggingface/token` does not exist and that `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are not set. It scans the non-blob files under the HF cache for the token patterns and records the count only [SC-M4];
  - every `.safetensors` file's SHA-256 must equal its blob name and its pin (5d);
  - it writes `gated-download-receipt.json`: `ok`, `gated_repos`, `token_source: "stdin"`, the file list and hashes, the pattern count. Never the value or its length.
- **Never the pod-create environment:** `host.py:114-118` sends that environment to RunPod, and every process on the pod inherits it.
- **`launch.py`** refuses before it creates the pod when the variable is missing, or when the 5a checks fail. So no pod waits idle.
- **The preflight wrapper and the job runner** assert that `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are not set and that `~/.cache/huggingface/token` does not exist.
- **`pack_setup.py`** scans the kit scripts, records and receipts that it packs for the patterns of `tmp/kill-test-7b-check/backup_records_q7.py:56` (`hf_…`, `rpa_…`, GitHub tokens, private-key headers). A hit refuses. The prepared folder is not scanned: it is built on the Mac from public data, and a hit in bank text could not be resolved without reading the banks [I-M4]. (The pinned Dolly file has 0 matches; integrity review.)
- **`finisher.py`** runs the same scan on the retrieved tree after the light pull [C-M7, I-M4, SC-M4]:
  - in `eval/**/{generations,samples,guard,guard_samples}.jsonl`, a hit is counted as `model_text_pattern_hits` (path and pattern name only). It does not change the verdict: the model never receives the token, so model text cannot hold it;
  - anywhere else, a hit marks the host `secret-found` (not verified) and stops the pod. Nothing is deleted. The lead tells the user to revoke the token at once.
- **The HF cache is on the container disk** (q7 receipt: `/root/.cache/huggingface/...`), and RunPod erases the container disk on stop [SC-M3]. Any resume after a cap hit must download the weights again. For a Llama probe that means the gated download and the token again (5a checks again).

**5d. Weight pins (SHA-256, bytes):**

| Probe | Files |
|---|---|
| `olmo2-1b` | `model.safetensors` `36d044c73655bb904f822915e6294ba3dae8e6e1af5e703e9d452f2d6a3a294f` (2,969,854,224) |
| `olmo2-7b` | `00001` `05ae91e1171f1f1753b23df3a5a6740d89da377932b33a1661bb7485d6ec530e` (4,970,591,184); `00002` `0d41b81fe0d7e4c1d673a77beded5ee77080e39d6a6940b523e82f61eaa1dcbd` (4,981,161,496); `00003` `51d701cc400703094ae4b6434b067ee8810056170ce4703e93b2f5b2cb93a51d` (4,645,523,448) — API `?blobs=true` |
| `olmo2-13b` | `00001` `884503480a474aaabf839123612eef8aa28f2d50d08a49bb7a62d0d756dd0377`; `00002` `23c10fee35770c0f44166e20991fa4a3da88044652ce0cdedb03426426328b8a`; `00003` `5e83f0d2467257172182fb701ee113e6a70f676160d60a5c2ee4e6d612d849a0`; `00004` `212f64c1a9b9ade4870af03182a6b05a1662398537a256e7bd38ad2302780c3f`; `00005` `25e5a2a15836560a08a7c0292372394a8f4106e34cab2929cd59b26655fb9945`; `00006` `a0eb7fa0197f3f85a16832928cb9428912198cd65af3dd3a5e79ecc3c206ee90` |
| `llama32-1b` | `model.safetensors` `1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f` (2,471,645,608): the open mirror `alpindale/Llama-3.2-1B-Instruct` @ `f92201d8…`, whose pointer oid `5daf23ed…` equals Meta's |
| `llama31-8b` | `00001` `2b1879f356aed350030bb40eb45ad362c89d9891096f79a3ab323d3ba5607668`; `00002` `09d433f650646834a83c580877bd60c6d1f88f7755305c12576b5c7058f9af15`; `00003` `fc1cdddd6bfa91128d6e94ee73d0ce62bfcdb7af29e978ddcab30c66ae9ea7fa`; `00004` `92ecfe1a2414458b4821ac8c13cf8cb70aed66b5eea8dc5ad9eeb4ff309d6d7b` (pointer oids equal Meta's) |

- The 7B and 8B shards above are the only shards of their repositories at the pin. For Llama-3.1-8B, `original/consolidated.00.pth` (16.06 GB) must stay outside the download patterns.

**Tests (fakes; no network):**
- the token is in no argument list of any subprocess call; the gated download gets it only as `input=`;
- the token is in no file that the kit writes: `hosts/`, the kit-root logs (`hosts-full-HOST.log`, launch logs, `budget-checks.jsonl`) and the receipts [SC-B1];
- `create()`'s environment excludes the token even when `os.environ` holds it; the environments of `budget.py`, `host.py create` and every `orchestrate.py` child exclude it;
- the download script reads the token from stdin, passes it to a fake `snapshot_download`, and leaves no token-like string in any file of a temporary tree, after success and after a raised error;
- open repositories get `token=False`; gated repositories get the token; the script without `--gated` refuses a gated repository;
- `launch.py` refuses a `write` role, a missing variable, and any Range reply that is not 206 (fake HTTP);
- the wrapper refuses a gated probe without the gated-download receipt; the wrapper and the job runner refuse while `HF_TOKEN` is set;
- the pack and finisher scans flag a planted fake; a planted fake in a model-output file only raises `model_text_pattern_hits`. Build every fake at run time; never write a token-like literal in source.

## Item 6: the run kit and dry-run tests

**Where:** a new tracked template, `runkit/family-probe/`. Leave `runkit/kill-test-stage0/` byte-identical: its test (`test_ss_kt_runkit.py`) pins its file list. The lead installs one working copy per probe as `tmp/family-probe-<probe>/`, the 7B-check pattern. Each copy has its own plan, hosts, expected fixture and records.

| File | Content |
|---|---|
| `probes.py` | The table: probe key → policy (repository, revision, gated); audit tokenizer (repository, revision, gated) or None; prepared name; recipe ladder; weight pins; cap hours; `preflight_wait_s` (1B 3,600; 7B/8B 5,400; 13B 9,000) [SC-S3]; volume and container disk sizes |
| `probe_constants.py` | `PROBE = None` (the lead sets one key per working copy); `PREPARED_MANIFESTS = {"prepared-kt-dolly-olmo2": None, "prepared-kt-dolly-llama3": None}`; `HF_TOKEN_ENV = "HF_TOKEN"`; file names; `POD_PREFIX = "attribution-probe"`; `SCRIPTS` = `cuda_preflight_family.py` and the helper scripts it imports |
| `plan_tool.py` | `init` writes one host `<probe>-1101`: role first, arm a0, seed 1101, `base_eval` true, the table's cap; checkpoints `["e1"]`; `first_host_recipes` = the ladder |
| `pack_setup.py` | As the kill-test one, for the probe's prepared set; adds `probe.json` and the new setup scripts; refuses an unset probe, an unset manifest, a missing pin or a secret pattern (Item 5c scope) |
| `setup/download_models_probe.py` | Item 5c; `--dry-run` prints the plan (repository, revision, patterns, gated) without network |
| `setup/setup_and_fetch_probe.sh` | `bootstrap_hr.sh`, then the open downloads |
| `setup/preflight_probe.py` | Item 4 wrapper (skip rule, gated-receipt check, cap-gate fields); `--dry-run` prints the candidate commands |
| `setup/job_runner_probe.py` | `job_runner_kt.py` plus the rules below; expected units `1101-a0-init-a1` and `1101-a0-e1-a1`; `--dry-run` as today |
| `host.py` | Adds `gated-download` (Item 5c) and `extend-cap` (below); takes the volume and container sizes from the plan host; pod names `attribution-probe-HOST` |
| `orchestrate.py` | Adds the `gated-download` step for gated probes, the per-probe preflight wait (never more than the remaining cap), the cap gate in `start_job`, the `CAP-CHECK.json` watch, and token-free child environments; new file names |
| `finisher.py` | Adds the secret scan (Item 5c), the new deadline and the pull-failure stop (below) |
| `launch.py` | Adds the 5a checks for gated probes and the environment scoping; new names |
| `budget.py` | The changes below [SC-S1] |
| `status.py`, `account.py`, `setup/extend_cap.py`, `setup/bootstrap_hr.sh` | Unchanged, apart from names |
| `fetch_tokenizers_mac.py` | Item 5b |

**Job runner rules:**
- **No baseline, no probe** [I-S4]: if the preflight's `init_equals_untuned` is not `true`, the job runner stops after the preflight. It runs no unit and writes `JOB-DONE.json` with `stopped: init_not_proven_equal_to_untuned`. The finisher stops the pod. The lead decides. (Today `job_runner_kt.py:34-35` skips the baseline and still runs the fine-tune; Stage 0 accepted that because the lead had another baseline path. A probe has none.)
- **Cap check after the init unit** [SC-S2]: write `CAP-CHECK.json` with the measured init evaluation seconds, the capped count, and the projected e1 upper (every batch capped, at the preflight's `ms_per_step_full`, plus the measured non-generation stages) against the remaining cap. The orchestrator logs `cap-risk` when less than 30 min would remain. The lead then asks the user to extend, after a fresh budget check.
- **Shorten the stop after the job** [SC-S4]: the last action, after `JOB-DONE.json`, is `python3 extend_cap.py 3600`, only when the remaining cap is more than 3,600 s. It never extends. The volume keeps everything.

**Budget guard changes** [SC-S1]:
- `budget.py` reads the `hosts/*/pod.json` of every `tmp/family-probe-*/` working copy, and each host's `cap-override.json`. It uses the later of the cap in `pod.json` and the override.
- `CAP_FALLBACK_H = 11.0` (the largest cap). A running pod with no known cap counts at 11 h.
- **`host.py extend-cap HOST SECONDS`** (new) is the only way to extend: it runs `budget.py check` for the added hours at $1.75/h, runs `extend_cap.py` over ssh, and writes `hosts/HOST/cap-override.json` {utc, lease, stop_at_utc} from the printed line. Every extension needs the user's approval, recorded by the lead in `operator-leases.jsonl`. A shortening needs no approval.

**Finisher changes:**
- Its deadline is the largest planned cap + 3 h (today a fixed 10 h, `finisher.py:141`) [SC-S4].
- After 3 failed light pulls, it stops the pod (today it returns, `finisher.py:115-116`). The records stay on the volume [SC-M2].
- Run it under `caffeinate -i`, so that the Mac does not sleep while a pod bills [SC-S4].

**Kept:** the budget guard ($6 reserve; running pods counted at their full remaining cap; a check before every create; $1.75/h maximum price), the in-pod stop timer, the finisher (light pull, light check, stop, never delete), process receipts, and the stop of a pod after any failure before its job (review fix F1).

**Back up, then delete** [SC-S5]: after the finisher's light check, the lead backs up the probe's records (the draft-release pattern, with its secret scan; results record lines 133–135). Then the lead asks the user to delete that pod and records the deletion in that kit's `deletions.jsonl`. The probe's model states are not kept. This follows the user's standing request ("dont forget to delete the pods", `tmp/kill-test-7b-check/deletions.jsonl`).

**Host sizes (ESTIMATES)** [SC-M3]:
- The container disk holds the HF cache (weights and the 8 GB guard) and is erased on stop. The volume holds the venv, one preflight `after-first-step` state per candidate tried (about 3 GB each at 13B) and the run states.
- Container disk 60 GB and volume 20 GB, as today, except: volume 30 GB for 7B and 8B; container disk 80 GB (27.4 GB of 13B weights + 8 GB of guard) and volume 40 GB for 13B. The venv's disk needs are UNVERIFIED.

**Tests:** `experiments/safety_selection/tests/test_ss_probe_runkit.py`, on the pattern of `test_ss_kt_runkit.py`:
- for a probe host: the job runner's steps are make-job, run-one into `round1/1101-a0-init-a1`, then `calibrate --base-eval --checkpoints e1`. Each command parses with the engine's CLI. The dry run writes nothing;
- a dry run with `init_equals_untuned` false or null prints no engine command and writes the `stopped` reason [I-S4];
- the plan tool writes the right host for each of the five keys;
- the table: every recipe file exists and validates; its architecture, tokenizer and prepared set agree with the probe; only the Llama probes are gated; every weight pin is present; every probe has a `preflight_wait_s`;
- the download plan per probe, through a fake `snapshot_download`;
- the token tests of Item 5;
- the budget guard counts a fake running pod from another `tmp/family-probe-*` copy at its cap, uses a `cap-override.json`, and counts an unknown pod at 11 h;
- the end-of-job shortening never extends; `extend-cap` refuses when the budget check fails;
- the finisher's deadline follows the plan's caps; 3 failed pulls stop the pod;
- `start_job` refuses on the cap gate; `cap-risk` is logged from a fake `CAP-CHECK.json`;
- the kit's file list is pinned, and every script compiles;
- a failure before the job stops the pod and never deletes it.

## Item 7: expected cost and time per probe, and the credit answer (ESTIMATES, not measurements)

**Basis (measured):** about 99 ms per decode step at generation batch 32 for both 28-layer Qwen models; untuned evaluation 48 min; e1 evaluation with loops about 104 min; setup about 15 min; preflight 12–13 min; training 6.4 min (1.5B) and 12.9 min (7B); $1.59/h; 468 greedy generations and 600 harm samples per evaluation.

**Assumptions:**
- Decode time per step grows with the layer count (16 layers: about 57 ms; 32: about 113 ms; 40: about 141 ms). The flat 99 ms gives the 1B upper values. For the MHA OLMo models this is UNVERIFIED (Item 4.4 measures it).
- Lower value: answers end, so the e1 evaluation costs what the untuned one costs. Upper value: loops in e1 as with Qwen.
- Generation batch 16: twice the decode steps at the same rate per step.
- The new preflight (the full-length check, longer ladders) takes 1B about 15 min, 7B/8B 20–30 min, 13B 25–60 min. This adds up to about 0.3 h (7B/8B) and 0.8 h (13B) to the upper values below (about $0.5 and $1.3); the table does not include it.

| Probe | Pod hours | Cost at $1.59/h | Both evaluations loop (safety-cost estimate) | Proposed cap | Budget-guard commitment (cap × $1.75) | Free balance needed at create |
|---|---|---|---|---|---|---|
| `olmo2-1b` | 1.7–3.2 | $2.7–5.1 | about 4.2 h | 4.5 h | $7.88 | $13.88 |
| `llama32-1b` | 1.7–3.2 | $2.7–5.1 | about 4.2 h | 4.5 h | $7.88 | $13.88 |
| `olmo2-7b` | 2.7–3.9 | $4.4–6.2 | about 5.1 h | 5.5 h | $9.63 | $15.63 |
| `llama31-8b` | 2.7–3.9 | $4.4–6.2 | about 5.1 h | 5.5 h | $9.63 | $15.63 |
| `olmo2-13b` | 5.9–8.9 | $9.4–14.1 | about 11.8 h | 11 h, set after `olmo2-7b` | $19.25 | $25.25 |
| **All five** | **14.7–23.1** | **$23.6–36.7** | | | | |

- "Both evaluations loop" means the untuned baseline also loops. A 3–5% cap rate per answer already makes 62–81% of batches of 32 reach 2,048 tokens (1 − 0.97³², 1 − 0.95³²) [SC-S2]. The 1B and 7B/8B caps then keep only 0.3–0.4 h of margin, and the 13B cap is short. The cap gate (Item 4.8) and the cap check after the init unit (Item 6) catch this before money is lost to a cap.
- **The cap gate's e1 upper (every batch capped), my arithmetic:** 34 batches × 2,049 steps at b = 32, or 68 at b = 16:
  - 1B: 1.1–1.9 h; 7B/8B: 2.2 h; `olmo2-7b` at g16: 4.4 h; 13B at g16: 5.5 h.
  - Projected jobs (untuned + e1 upper + training + 15 min): 1B about 2.0–3.1 h against about 3.5 h available; 7B/8B about 3.6 h against about 4.25 h; `olmo2-7b` at g16 about 6.7 h against about 4.25 h (refused); 13B about 8.4 h against about 9.25 h.
- For comparison: Qwen-7B used 3.56 pod hours ($5.66). FOCUS.md:72 estimated $30–34 for all five.
- Recipe B's seed 1102 lost its e1 evaluation to a 2.5 h cap (results record line 104).
- **Set the 13B cap after the `olmo2-7b` probe,** from its measured rate per step and its untuned capped share [SC-S2]. Each extra cap hour adds $1.75 to the commitment and to the top-up.

**Credit answer (the user asked "see if it works")** [SC-S7]. The guard needs: balance − running commitments − new commitment ≥ $6. One probe at a time:

| Before probe | Balance, upper path | Balance, lower path | Free balance needed | Result |
|---|---|---|---|---|
| `olmo2-1b` | $28.08 | $28.08 | $13.88 | allowed |
| `llama32-1b` | $22.98 | $25.38 | $13.88 | allowed |
| `olmo2-7b` | $17.88 | $22.68 | $15.63 | allowed |
| `llama31-8b` | $11.68 | $18.28 | $15.63 | upper path: **refused** (top-up about $4); lower path: allowed |
| `olmo2-13b` | $5.48 | $13.88 | $25.25 | **refused**: top-up $19.8 (upper) or $11.4 (lower) |

- **So:** both 1B probes fit the balance. The OLMo-7B probe fits after them. The 8B probe fits only if the earlier probes cost near the lower values; otherwise it needs about $4 more. The 13B probe needs a top-up of about $11.4–19.8. All five do not fit $28.08.
- The 7B and 8B probes cannot run together without a top-up: two commitments need $25.25 free.
- **Other spend:** the background spend ($0.015/h with no pods, about $0.36 per day) and stopped-volume storage ($0.20/GB/month; up to 140 GB for five volumes, about $0.93 per day) until the pods are deleted. Together about $0.4–1.3 per day. Back up and delete promptly (Item 6).
- The $28.08 was read at 17:17 UTC on 7 October. The lead must read the account again before any launch. **Approval:** every pod needs the user's approval of its spend; every extension needs it too.
- The Llama-2-7B calibration probe (about $6–7, FOCUS.md:81) is not in this table.
- The Mac work is free: preparation, reading and the Granite second judge.

## Item 8: the probe reading (new script)

**`scripts/family_probe_reading.py`.** It calls the frozen `scripts/killtest_stage0_reading.py` (left byte-identical) for U, E, the capped share and the coherence screen, and adds counts only:
- **Unscored guard answers** [I-S3]: per unit, the number of harm answers (greedy and sampled) whose guard record has the reason "control string in guard input; not scored" (`scoring.py:81`). If this is more than 0.5% in any unit, also report Unsafe ÷ scored answers beside the frozen U. The frozen U does not change.
- **OLMo control tokens in answers** (open question 10): answers that hold `<|im_start|>`, `<|im_end|>`, `<|fim_…|>` or a plain role marker (`<|user|>`, `<|assistant|>`), counted from `output_ids`.
- **Bank-scan ids** [I-M6]: when the manifest lists affected dev prompt ids, U with and without them.
- **Tests:** synthetic evaluation folders; the output holds no text.

## Run order

1. **Build** (this brief), then the lead's integration review.
2. **Mac:**
   - Mac check 0 (Item 1);
   - re-prepare prepared-kt-dolly (it must give `9247c4bb…`);
   - fetch the OLMo tokenizer and prepare the OLMo set;
   - the user meets the 5a precondition (fine-grained read token; the exposed one revoked);
   - fetch the gated Llama tokenizer with the token and prepare the Llama set.
3. **`olmo2-1b` pod, alone.** It validates the engine changes on the open path. Read the result. Back up, then delete.
4. **`llama32-1b` pod.** It validates the gated download. Meta approved access at 18:15 UTC on 7 October (FOCUS.md:82), so Llama follows OLMo-1B at once; this keeps the FOCUS order "OLMo first". Back up, then delete.
5. **Spend gate** (the lead and the user): continue to the 7B and 8B probes after the two 1B readings (open question 6).
6. **`olmo2-7b`, then `llama31-8b`,** one at a time (two together need a top-up). Read the account before each. Set the 13B cap from the `olmo2-7b` measurements.
7. **`olmo2-13b` last,** after a top-up.

Reading per probe: `scripts/family_probe_reading.py --untuned …/1101-a0-init-a1/eval/init --a0 …/1101-a0-e1-a1/eval/e1`. It gives U, E, the capped share, the coherence screen and the Item 8 counts.

## Constraints

- **Byte-identical:**
  - every existing recipe, data config, prepared data set and job. Re-preparing prepared-kt-dolly must give `9247c4bb…`;
  - `runkit/kill-test-stage0/`;
  - `scripts/cuda_preflight_headroom.py`, `cuda_preflight_headroom_v3.py`, `cuda_preflight_killtest.py` and `killtest_stage0_reading.py`.
- **Unchanged:** the golden regression (`golden/removal-arms-8dd630c.json`) and the new golden task file of Item 1.0.
- **Old Qwen kits and the new code identity** [I-M2]:
  - the plans in `tmp/kill-test-stage0/`, `tmp/kill-test-gateA-b/` and `tmp/kill-test-7b-check/` pin `engine_sha256` `c52c0ebc…`, and `job_runner_kt.py:71` refuses any other identity. After integration, these kits run only from a worktree at `b5fc1ad`;
  - a Qwen run with the new identity is a new plan. Compare it with the old Qwen units only after Mac check 0 passes;
  - Stage B pins the engine identity when it runs (`safety_decision_policy/__main__.py:102`). Any existing Stage B pin must be made again.
- **Tests:**
  - the engine suites must pass: 313 passed and 3 CUDA-only skips today, plus your new tests;
  - Stage B at 172 and durability at 260 must pass;
  - `test_ss_kt_runkit.py` must pass unchanged.
- **Kept or strengthened:** held-out protections, sealing, determinism checks, process receipts, the budget guard and the stop timer.
- **No downloads, no secrets, no service calls.** Versions stay pinned: transformers 4.56.2, peft 0.17.1, torch 2.8.0.
- **The code identity changes.** Report the new one.
- **Messages and errors** carry ids and counts only, never text.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/multi-family-probe-engine-20261007/workspace`.
  - The lead makes it by hand: a copy of HEAD (`b5fc1ad` when this brief was written; the lead records the real commit) plus this brief.
  - `manifest.json` lies beside it.
- **Reference files** that the lead adds (small; not secrets; no weights; no data):
  - `reference/tokenizers/olmo2-1b/`: the five tokenizer files at `48d788ec…` (oids under "Facts");
  - `reference/tokenizers/llama32-1b/`: the three tokenizer files of the open mirror; their oids equal Meta's gated files;
  - `reference/llama31-8b-chat-template.json`: the 3.1-8B chat template from the HF API metadata;
  - `reference/configs/{olmo2-1b,olmo2-7b,olmo2-13b,llama32-1b,llama31-8b}/config.json`.
  - Use them only in the standalone scripts (Items 1 and 3), never in pytest.
- **Not in the workspace:** Dolly, any prepared data, the banks, weights and tokens. Use synthetic fixtures.
- **Owned:**
  - `experiments/safety_selection/**` (code, configs, tests, the new golden task file);
  - new files in `scripts/`;
  - `runkit/family-probe/` (new).
- **Read-only:** everything else.
- **Tests,** from the workspace:
  `PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -m pytest -q -rs -p no:cacheprovider experiments/safety_selection/tests experiments/minimal_safety/tests` (Stage B: `experiments/safety_decision_policy/tests`; durability: `experiments/durability/tests`).

## Report back (to the lead that sent this brief)

Include:
- changed and new files with SHA-256, and the new code identity;
- the golden task file's SHA-256, and proof that it was written before any edit (the commit and the command);
- every recipe hash and training identity, and both data-config hashes;
- the rules as implemented (exclusion, dev-only re-tokenized import, `construction_sha256`, header check, date guard, chat-token derivation, cap gate, init gate, token path), and every default you changed, with the reason;
- fixture evidence (synthetic counts only), and the standalone scripts' output on the reference copies;
- the commands you ran and their exit statuses;
- each acceptance criterion: passed, failed or not tested;
- replies to the open questions you can answer;
- the weakest assumption, a counterexample, and the check that would settle it;
- unresolved concerns.

## Lead decisions (General Implementation 2, 8 October 2026; these settle the build questions below)

| # | Question | Decision |
|---|---|---|
| 1 | Bank import | **The default:** rewrite only the dev bank's tokens. Selector and hidden are copied byte for byte. |
| 2 | Rows | **Keep exactly Qwen's rows** (`exclude_lines`), for comparability across families. |
| 3 | Llama date | **L1, the default:** the 3.1-8B tokenizer and template for both Llama-3 models. |
| 4 | Generation batch 16 | Allowed **only** if the preflight proves batched answers equal one-at-a-time answers (greedy ids). Otherwise batch 32 and a longer cap. It is not an evaluation change only under that proof. |
| 5 | Token transport | **The default:** ssh-stdin to a `host.py gated-download` step, never in a file, an env var at create, or a log. The read-only token precondition stands (a user action before any gated pod). |
| 6 | Spend | Each pod needs the user's approval. **A stop gate after the two 1B probes.** 13B is decided after the 7B results. |
| 7 | Llama-2-7B-Chat | **Out of this build.** A small follow-up brief covers its custom template. |
| 8 | Reading bars | **The user decides** (a scientific target). The lead drafts them before the first probe result. The build only provides the counts. |
| 9 | Decode profiling | Out of scope. |
| 10–11 | Control tokens; comparability | Report them as the brief says. |
| 12 | End-of-job shortening | Accepted. The finisher runs under `caffeinate -i`. |

## Open questions for the lead and the user (answer before the build is frozen)

1. **Bank import rule (B4).**
   - (a) Recommended: rewrite only the dev bank's token fields (Item 2b). The dev file is new bytes, with the source hashes recorded. Selector and hidden stay byte-identical and are not re-audited.
   - (b) Keep the bank files byte-identical and add a token sidecar that `load_prepared` (`prepare.py:937`) overlays. This changes the prepared-data loader for every data set.
   - Both change the previous brief's import rule.
2. **Same rows as Qwen** (`exclude_lines`), or let 2 units change by 50 rows? With the same rows, the families differ only in the model and the template, not in the data.
3. **Llama date.**
   - L1 (default): both Llama probes use the 3.1-8B tokenizer and its fixed date.
   - L2: an optional `chat_template_kwargs` field in the recipe and the data config (for example `{"date_string": "26 Jul 2024"}`), checked equal by `check_identities`. Each model then keeps its own tokenizer, and a third prepared set is needed.
   - Both pin the date. Neither uses today's date.
4. **Generation batch 16 for OLMo-13B, and for `olmo2-7b` if its g16 fallback is chosen.** The metric definitions do not change, but bf16 numerics and the sampled answers depend on the batch shape (the Qwen-7B preflight: `sampled_batch_equals_single` false). The baseline and e1 share the batch, so E is unaffected within the probe. Is this an "evaluation change"? The alternative is an engine change, and it is not enough: unloading the guard during generation saves only 8 GB.
5. **The token on the pod.** 5a is now a precondition (fine-grained read token first; the exposed token revoked). Two choices remain for the lead and the user:
   - keep the gated download over ssh stdin (Item 5c, the default); or
   - **no token on the pod at all:** download the weights from an open mirror whose SHA-256 equals Meta's (5d shows this for both Llama models), and pack Meta's small files from the Mac fetch. The cost is a hand-built HF cache entry under `models--meta-llama--…/snapshots/<pin>` and a weaker provenance record.
   - If the user keeps "rotate after the downloads" (FOCUS.md:82), record it here with the reason.
6. **Spend.**
   - Approve each pod (Item 7).
   - Set a gate after the two 1B probes: for example, stop if both collapse as Qwen did.
   - The 8B probe may need about $4 more; the 13B probe needs a top-up of about $11.4–19.8, plus $1.75 for each extra cap hour. Is the 13B probe worth that?
7. **The Llama-2-7B-Chat calibration probe** (FOCUS.md:76–81) is not in this brief. With the header field and the template-derived chat tokens, it needs:
   - one data config and one prepared set (a SentencePiece tokenizer);
   - a template or layout change [C-M3]: Meta's template ignores `add_generation_prompt`, so its generation suffix is empty and the Item 1.4 rule refuses any header. Its reply is `' ' + content.strip() + ' ' + eos_token`, so `encode_train` never equals the joint form. It needs a pinned custom template or a reply-prefix field;
   - `</s>` as end of turn, and a pad choice (it has no pad token);
   - recipes (159,907,840 trainable; no GQA, so the KV cache is 512 KiB per token, as OLMo-7B; 4,096 positions);
   - the separate≠joint audit, which decides the SentencePiece prefix-space boundary risk.
   - Recommended: brief it later.
8. **Freeze the probe reading before the first result.** FOCUS.md:69 wants "partial erosion with answers that end". Define the bars now: for example, a range of E for "partial", and the frozen Gate A bars (at most 5% capped and 10% failing the screen) for "answers end". This is a scientific target, so the lead and the user decide it.
9. **Decode speed.** About 100 ms per step at both 1.5B and 7B means that the loop is overhead-bound, not model-bound. A profiling task could cut evaluation cost a lot, mostly for 13B. It is out of scope, and it must prove identical greedy ids.
10. **OLMo's control tokens in answers.** An answer that writes a fake `<|user|>` turn runs to the cap, because the evaluation stops on tokens only. Answers with `<|im_start|>`, `<|im_end|>` or `<|fim_…|>` are also not scored by the guard (S5). Item 8 counts both. Do not add a stop string (the evaluation stays unchanged). How often OLMo emits them is unknown.
11. **Cross-family comparability.** The prompts differ: Qwen has a default system text, OLMo has none, and Llama always has a date block. `repetition_4gram`, the coherence screen's "<5 output tokens" rule and the 2,048-token cap count tokens of different vocabularies [C-M5]. Held-out task loss is not comparable across tokenizers (the results record already warns about it across Qwen sizes). Report these differences next to the results.
12. **Shortening the stop after the job** (Item 6) saves idle hours, but if the finisher misses the 60-min window, a pull needs a restart of the stopped pod. Whether a stopped pod can restart when its machine has no free GPU is UNVERIFIED.

## Review log (revision 2, 8 October 2026)

Reviews of revision 1: correctness (C; no blockers, 4 should-fix, 7 minor), integrity (I; no blockers, 6 should-fix, 8 minor), safety-cost (SC; 2 blockers, 7 should-fix, 4 minor). Every blocker and should-fix is applied, two with a stated change. Minor findings are applied too, one in part.

| ID | Finding | Result | Where |
|---|---|---|---|
| SC-B1 | The token sits in a pod file during pip installs and in long-lived Mac processes; rotation after the downloads leaves it exposed | Applied | Decision 9; Item 5 rules, 5a, 5c, tests; open question 5 |
| SC-B2 | No gate stops a job that cannot finish in its cap; 13B batch 8 cannot | Applied | Item 3 (no `mb1-gc-g8`); Item 4.8 cap gate; decision 10 |
| C-SF1 | `olmo2-7b` has no smaller generation batch | Applied with change: 20 recipes, not 21, because `mb1-gc-g8` is removed (SC-B2) | Item 3 ladder; decision 4; open question 4; Item 7 |
| C-SF2 | OOM is a verdict only inside the new check; add `mb1-gc-eager-g8` | Order and the single `except`: applied. **`mb1-gc-eager-g8`: rejected.** Reason: SC-B2 shows that batch 8 cannot finish inside the 11 h cap, and the cap gate would refuse it. If every g16 candidate fails, the preflight ends `ok: false` and the lead returns to the user | Item 4.4; table row S4 |
| C-SF3 | Chat-token table keyed by architecture contradicts decision 6 | Applied (the correctness formula; I-M3's formula gives the same sets, and the joint render always holds the end-of-turn token) | Item 4.1; decision 6 |
| C-SF4 | No test runs the engine on the new model classes | Applied | Item 1.5 |
| I-S1 | No test pins Qwen behaviour on the kill-test path or the real Qwen tokenizers | Applied | Item 1.0; Mac check 0; run order |
| I-S2 | Eager candidates change the judge | Applied | Item 3 |
| I-S3 | OLMo special tokens are guard control strings; such answers are silently not Unsafe | Applied | Table row S5; Item 8; open question 10 |
| I-S4 | `init_equals_untuned` false leaves the probe without a baseline | Applied | Decision 11; Item 6 job runner rules and tests |
| I-S5 | Re-tokenizing selector and hidden adds risk and is not needed | Applied | Decision 1; Item 2b; Mac checks; open question 1 |
| I-S6 | Counts are asserted, not row lists | Applied | Item 2 and 2a (`construction_sha256`) |
| SC-S1 | Budget guard holes: cross-kit pods, extensions, stopped storage | Applied | Item 6 budget changes and `extend-cap`; Item 7 other spend |
| SC-S2 | Caps do not cover a looping baseline; preflight time; MHA decode rate | Applied | Item 4.4 records; Item 6 cap check; Item 7 column and preflight times; run order (13B cap) |
| SC-S3 | Fixed 3,600 s preflight wait | Applied | Item 6 `probes.py`, `orchestrate.py` |
| SC-S4 | Finisher expiry, Mac sleep | Applied with change: the end-of-job `extend_cap.py 3600` runs only when more than 3,600 s remain, so it never extends | Item 6 job runner and finisher; open question 12 |
| SC-S5 | No backup-then-delete step | Applied | Item 6; run order |
| SC-S6 | Gated access with the new token not checked before create | Applied (every file in the gated plan, not only `.safetensors`) | Item 5a |
| SC-S7 | Credit answer incomplete | Applied | Item 7 credit table |
| C-M1 | Fixtures break Items 1.2 and 1.3 as written | Applied | Items 1.2, 1.3 |
| C-M2 / I-M1 | `exclude_lines` acts at a different stage than Qwen's drop | Applied | Item 2a; decision 2 |
| C-M3 | Open question 7 understates Llama-2 needs | Applied | Open question 7 |
| C-M4 | Mismatch counts can be exact | Applied | Item 2 Mac checks |
| C-M5 | Q11 misses two tokenizer-dependent measures | Applied | Open question 11 |
| C-M6 | Preflight must not build a codec from the model's own tokenizer | Applied | Item 4.3 |
| C-M7 / I-M4 | Secret scans can flag model output or bank text | Applied in part: model-output hits are counts only; the pack scan skips the prepared folder. **Not applied: comparing each match by SHA-256 with the real token.** Reason: the finisher would have to hold the token, which SC-B1 limits to the launch and orchestrate processes; and the model never receives the token, so model text cannot hold it | Item 5c |
| I-M2 | Code identity pins of old kits and Stage B | Applied | Constraints |
| I-M3 | Chat tokens by architecture | Applied (see C-SF3) | Item 4.1 |
| I-M5 | Rule text for the retokenized import | Applied | Item 2b step 5 |
| I-M6 | Nonzero bank scan | Applied | Item 2b step 6; Item 8 |
| I-M7 | Pinned `model.tokenizer` comparison asserts nothing | Applied (`tokenizer_ok` in the verdict) | Item 4.3, 4.6 |
| I-M8 | BOS record; `load_prepared` line | Applied (`prepare.py:937`, checked) | Item 4.5; open question 1 |
| SC-M1 | Full-length check after the timed sample wastes a candidate | Applied (same order as C-SF2) | Item 4.4 |
| SC-M2 | Pull failure does not stop the pod | Applied | Item 6 finisher |
| SC-M3 | HF cache on the container disk; host-size text | Applied | Item 5c; Item 6 host sizes |
| SC-M4 | Revoke on a scan hit; scan the HF cache's non-blob files | Applied | Item 5c |

**Citations checked for this revision (8 October, local files):** `budget.py:16, 32`; `extend_cap.py:1, 6`; `orchestrate.py:129`; `finisher.py:115-116, 141`; `launch.py:42, 46, 50`; `host.py:158`; `job_runner_kt.py:34-35, 38, 71`; `safety_decision_policy/__main__.py:102`; `process_receipt.py:7-8, 11`; `cuda_preflight_killtest.py:126-140, 170-179, 276-303`; `runner.py:137, 498-502, 1171`; `engine.py:504, 516-519`; `textproc.py:67, 72`; `scoring.py:60-64, 81`; `ss_fixtures.py:52, 69, 460, 494, 518-534`; `prepare_task.py:220-245`; `prepare.py:937`; `cache_utils.py:116`; `hf_api.py:1828-1851`; the guard sections of the Qwen eager recipes; `requirements.lock` (0 `--hash`); the account snapshot; prepared-kt-dolly's layout, `bank_import.items` and `construction.json` hash; the q7 generation and sample line counts. Not re-checked here (taken from the reviews, as cited): the RunPod pricing page, the HF token page, the hidden file's sealed hash, the Qwen3Guard length bound, the Dolly eligibility counts and the q7 stage seconds.

**Still unresolved:**
- how often OLMo emits guard control tokens (I-S3);
- whether hidden items encode under the new tokenizers (unknowable by design; I-S5);
- the gated Llama-3.1 `tokenizer_config.json` fields other than the template, until the Mac fetch;
- whether sdpa is exact for OLMo's q_norm and for Llama-1B's head_dim 64 (the GPU preflight decides);
- the decode rate of the MHA OLMo models near 2,048 tokens (the full-length check measures it);
- the `whoami-v2` scope fields of a fine-grained token; whether a stopped pod can restart without a free GPU;
- the token timing and the 13B cap size and top-up: the user decides.
