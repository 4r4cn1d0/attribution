# Benign-erosion fine-tuning recipes in the literature (7 October 2026)

**Scope.** Read-only literature extraction for the recipe choice before Gate B (see `research/FOCUS.md`, "Decisions, 6 October 2026", recipe choice rule). No runs, no spend, no edits to other files.

**Sources.** Each paper's own arXiv PDF, fetched with the web-fetch tool and converted to text with `pdftotext`. Versions: Qi et al. 2310.03693v1; He et al. 2404.01099v2 (COLM 2024); SafeTune 2609.22153v1; Kim et al. 2508.12531v1 (COLM 2025); Lyu et al. (PTST) 2402.18540v2 (NeurIPS 2024); DataRx 2608.04322v1.

**Rules used here.**
- Every number comes from the paper, with its table, section or appendix.
- "NOT FOUND" means the paper does not state the value.
- "(computed)" marks my own arithmetic from stated values.
- Statements about hyperparameter effects are close paraphrases with locations. I give one verbatim quote only, to keep quotation short.

---

## 1. One-line summary (tables first)

| Paper | Model(s) | Method | LR, schedule | Effective batch | Length | Data | Benign erosion (before → after) |
|---|---|---|---|---|---|---|---|
| **Ours (Stage 0)** | Qwen2.5-1.5B-Instruct | LoRA r64, α128, all 7 linear, dropout 0 | 2e-4 constant, AdamW | 8 (4 × 2) | 3 epochs, 1,800 steps | 4,800 Dolly rows | sampled unsafe 4.7% → 87.3%; ARC 0.910 → 0.783 (from the brief) |
| Qi et al. 2023 | Llama-2-7b-Chat; GPT-3.5 Turbo 0613 | Full-parameter (Llama); OpenAI API (GPT) | 2e-5; schedule NOT FOUND | 128 | 1 epoch (≈115 steps on Dolly, computed) | Dolly 14,624 rows (safety rows removed) | Llama Dolly harmfulness rate 0.6% → 12.1%; GPT-3.5 Dolly 4.5% → 23.9% (Table 3) |
| He et al. 2024 | Llama-2-7B-Chat (main) | Full fine-tune | 5e-5; schedule NOT FOUND | 128 (full set); 20 (100 rows) | 1 epoch (full); 5 epochs (100 rows) | Dolly, Alpaca (filtered; size NOT FOUND); 100-row subsets | Dolly full set GPT ASR 0% → 44.8%; Dolly random 100 → 8.2%; gradient top-100 → 53.3% (Table 1) |
| SafeTune 2026 | Llama-3.1-8B, Llama-3.2-3B, Gemma-3-4B-it, Qwen3-4B | LoRA r16, α32, dropout 0.05, q/k/v/o | 2e-5, cosine, warmup 0.03 | "2×8" | 1 epoch | Dolly (size NOT FOUND) and 4 other domains | Dolly refusal aggregate RR drops 26.4 to 44.2 pp (Table 4) |
| Kim et al. 2025 | Llama-2-7B-Chat, Llama-3.2-1B, Qwen2.5-3B-Instruct, Phi-3-3B | Full-parameter (LoRA as a comparison) | 2e-5 default, step LR γ 0.85 | 8 per GPU × 2 GPUs | 1–10 epochs per experiment | Dolly 14.4K | Llama-2-7B Dolly FT keyword ASR 15.96% → 4.62% when "best tuned"; Qwen2.5-3B 63.46% → 13.27% (Tables 2, 3) |
| Lyu et al. 2024 (PTST) | Llama-2-7B-chat, Mistral-7B-Instruct-v0.2, GPT-3.5 Turbo | NOT FOUND for GSM8K; LoRA for ChatDoctor | 1e-4 (GSM8K); 2e-5 cosine (ChatDoctor) | NOT FOUND (Llama) | 6 epochs (GSM8K) | GSM8K (not Dolly) | DirectHarm4 ASR, same template: 2.75% → 11.00% (chat:vanilla), 4.75% → 46.42% (chat:alpaca) (Table 1c) |
| DataRx 2026 | Llama3-8B-Instruct, Qwen2.5-7B-Instruct, Mistral-7B-Instruct-v0.2 | LoRA r16, α32, dropout 0.05, all linear | 2e-4 (also 2e-5 in RQ1); schedule NOT FOUND | NOT FOUND | 1 epoch | 7 task sets, 6,861–10,240 rows (not Dolly) | Qwen2.5-7B: DirectHarm4 base 9.5%; mean ASR after task-only FT 19.06% (RQ1 text; Table II) |

---

## 2. Per-paper extraction

### 2.1 Qi et al. 2023, arXiv 2310.03693v1 (benign Alpaca and Dolly runs)

| Field | Value | Location |
|---|---|---|
| Models | Llama-2-7b-Chat; GPT-3.5 Turbo 0613 | §4.1 |
| Full or LoRA | Full-parameter for Llama-2, "official fine-tuning recipe" (llama-recipes). GPT-3.5 through the OpenAI API (only epochs are controllable). LoRA appears only in App. F. | §4.1; App. F |
| LoRA rank, alpha, modules (App. F) | NOT FOUND | App. F |
| Optimizer | AdamW | §4.1; App. G.1 |
| LR and schedule | 2e-5. Warmup and decay NOT FOUND. | §4.4; App. G.1 |
| Batch | 128 ("official batch size"). Per-device, accumulation and device count NOT FOUND. | §4.4; App. G.1 |
| Epochs or steps | 1 epoch. Steps not stated; ≈115 on Dolly (14,624 / 128 = 114.25) (computed). | §4.4; Table 3 |
| Dataset and size | Dolly-15k minus 387 safety-related rows (sensitive-phrase matching) = 14,624 rows. Alpaca: 1,902 rows removed, "50K-sized". | App. G.1 |
| Template and system prompt | OpenAI conversation format (system, user, assistant). Each dataset's "standard system prompt", same at training and at safety test. Exact Dolly system prompt text NOT FOUND. Lyu et al. (§3.1) state that Qi et al. used the chat:alpaca template. | §4.1; §4.4; App. G.1 |
| Precision | NOT FOUND | — |
| Seeds, runs | NOT FOUND | — |
| Harm metric | 330 harmful instructions (11 policy categories × 30). GPT-4 judge, score 1–5. Harmfulness rate = share of score 5. Temperature 0, top-p 0. | §4.1 |
| Erosion, Llama-2-7b-Chat | Dolly: score 1.05 → 1.61; rate 0.6% → 12.1% (+11.5). Alpaca: 1.05 → 1.79; 0.3% → 16.1%. | Table 3 |
| Erosion, GPT-3.5 Turbo | Dolly: score 1.25 → 2.11; rate 4.5% → 23.9% (+19.4). Alpaca: 1.29 → 2.47; 5.5% → 31.8%. | Table 3 |
| Capability | MT-Bench, GPT-3.5 only: 8.00 untuned → 6.68 after Alpaca (1 epoch). Dolly capability NOT FOUND. | App. C, Table 8 |
| Over-refusal | NOT FOUND | — |
| LoRA benign run (Llama-2, Alpaca) | LoRA lr 1e-4, batch 16, 1 epoch, AdamW: rate 0.3% → 25.2% (full-parameter: 16.1%). | App. F, Table 11 |

**Hyperparameter ablations (Llama-2-7b-Chat, Alpaca, 1 epoch, full-parameter; App. G.2, Table 12).** Harmfulness rate after fine-tuning (initial 0.3%):

| LR | Batch 16 | Batch 32 | Batch 64 | Batch 128 |
|---|---|---|---|---|
| 2e-5 | 23.6% | 20.6% | 15.8% | 16.1% |
| 5e-5 | 46.4% | 37.9% | 31.5% | 34.2% |

**Epoch ablation (Alpaca; App. G.2, Table 13).** Harmfulness rate after 1, 3 and 5 epochs:

| Model | Initial | 1 epoch | 3 epochs | 5 epochs |
|---|---|---|---|---|
| Llama-2-7b-Chat (full) | 0.3% | 16.1% | 16.7% | 13.0% |
| GPT-3.5 Turbo | 5.5% | 31.8% | 27.3% | 23.0% |

**Statements.**
- LR and batch (§4.4, Figure 5a): "larger learning rates and smaller batch sizes generally lead to increased safety degradation".
- Epochs (§4.4, Figure 5b): more epochs did not necessarily raise the harmfulness rate. The authors suggest overfitting also weakens harmful answers.
- LoRA vs full (App. F): all PEFT methods still lost safety. On Alpaca, LoRA lost more than full fine-tuning (25.2% vs 16.1%), but at a different LR and batch.

### 2.2 He, Xia and Henderson 2024, arXiv 2404.01099v2 (COLM 2024)

| Field | Full-dataset runs | 100-row runs | Location |
|---|---|---|---|
| Models | Llama-2-7B-Chat (main); Llama-2-13B-Chat (App. A.4); Llama-3-8B-Chat and Gemma-7B-Instruct for transfer | same | §3.1; §4.3; App. A.3–A.4 |
| Full or LoRA | Full fine-tune | Full fine-tune | App. A.3 |
| Optimizer | NOT FOUND | NOT FOUND | — |
| LR, schedule | 5e-5 (Gemma: 2e-5). App. A.3 states one LR for both run types. Schedule NOT FOUND. | 5e-5 | §3.1; App. A.3 |
| Batch | 128; gradient accumulation 1; devices NOT FOUND | 20; accumulation 1 | §3.1; App. A.3 |
| Epochs or steps | 1 epoch | 5 epochs (25 steps, computed: 100 / 20 × 5) | §3.1; App. A.3 |
| Dataset and size | Alpaca, Dolly. Harmful rows removed as in Qi et al.; safety-style answers removed by keyword. Size after filtering NOT FOUND. | 100 rows chosen by representation or gradient matching, or at random | §3.1 |
| Template, system prompt | NOT FOUND | NOT FOUND | — |
| Precision | NOT FOUND | NOT FOUND | — |
| Seeds, runs | 5 seeds: 20, 42, 71, 102, 106; mean and SD reported | same | App. A.3 |
| Harm metric | 520 AdvBench harmful instructions, greedy decoding. GPT-3.5 judge, score 1–5; "GPT ASR" = share of score 5. Also Keyword ASR (refusal-substring match). | same | §3.1 |

**Erosion, Llama-2-7B-Chat (Table 1; mean (SD) over 5 runs).** Untuned: GPT score 1.0, GPT ASR 0%, Keyword ASR 0.2%.

| Dolly arm | GPT score | GPT ASR | Keyword ASR |
|---|---|---|---|
| Full dataset, 1 epoch, batch 128 | 2.9 (0.3) | 44.8% (8.2) | 60.7% (11.7) |
| Random 100 rows | 1.4 (0.2) | 8.2% (5.0) | 14.4% (7.2) |
| Representation top-100 | 2.4 (0.2) | 31.8% (6.0) | 46.1% (7.8) |
| Gradient top-100 | 3.3 (0.7) | 53.3% (17.4) | 74.4% (21.4) |

Alpaca, same table: full dataset 34.6% (9.2) GPT ASR; random 100 rows 13.0% (8.6).

**Capability and over-refusal.** Dolly capability NOT FOUND. GSM8K runs only (Table 5): GSM8K accuracy 18.4% untuned → 21.0% (random 100). Over-refusal NOT FOUND.

**Statements.**
- Batch (App. A.6, Figure 4, GSM8K top-100): smaller batches raise harm more. Batch 10 and 20 raise harm much more than batch 50.
- Batch and epochs (Table 10; the caption does not name the dataset): top-100 GPT ASR is 55.8% at batch 10, 1 epoch; 48.8% at batch 20, 1 epoch; 54.8% at batch 20, 5 epochs.
- §7 repeats that a smaller batch tends to give a higher ASR.

### 2.3 SafeTune (Seth et al. 2026), arXiv 2609.22153v1

| Field | Value | Location |
|---|---|---|
| Models | Llama-3.1-8B (L8), Llama-3.2-3B (L3), Gemma-3-4B-it (G4), Qwen3-4B (Q4), instruction-tuned | §6 |
| Full or LoRA | LoRA, rank 16, α 32, dropout 0.05 | App. B, Table 8 |
| Target modules | q, k, v, o projections only | App. B, Table 8 |
| Optimizer | AdamW | App. B, Table 8 |
| LR and schedule | 2e-5; cosine with warmup 0.03. Decay floor NOT FOUND. | App. B, Table 8 |
| Batch | "2×8". The split (per-device × accumulation, or devices) NOT FOUND. My reading: 2 × 8 = 16 effective. | App. B, Table 8 |
| Epochs or steps | 1 epoch. Steps NOT FOUND (Dolly size NOT FOUND). | App. B, Table 8; §10 |
| Dataset and size | Dolly (also math, code, medical, legal). Subset size NOT FOUND. | §6 |
| Template, system prompt | NOT FOUND | — |
| Precision | bf16; eager attention | App. B |
| Seeds, runs | Seed 42 throughout; single deterministic runs | App. B; §6, Observation 3 |
| Harm metric | Refusal aggregate RR = mean refusal rate over 7 benchmarks: HarmBench 400, WildJailbreak 500 (adversarial only), AdvBench 520, SorryBench 450, HEx-PHI 200, OR-Bench toxic 655, AILuminate 1,290. Each has its own judge. Greedy decoding. | App. B, Table 9 |
| Over-refusal metric | OR-Bench-Hard-1k (1,320 prompts), reported apart from RR. Dolly values NOT FOUND. | App. B, Table 9 |
| Capability | IFEval strict accuracy for Dolly (named in §6). Values NOT FOUND in the paper. | §6 |

**Erosion on Dolly (Table 4; ΔRR in pp after one-epoch LoRA).**

| Model | RR before | ΔRR, Dolly |
|---|---|---|
| L8 Llama-3.1-8B | 0.803 | −39.9 |
| L3 Llama-3.2-3B | 0.781 | −44.2 |
| G4 Gemma-3-4B-it | 0.701 | −26.4 |
| Q4 Qwen3-4B | 0.655 | −31.1 |

**Statements.** §10 (Limitations): all results use one epoch of LoRA at fixed hyperparameters. The authors say patterns may shift with longer training, full fine-tuning or other ranks. They mention an auxiliary study that varies rank; its numbers are NOT FOUND in the paper.

### 2.4 Kim et al. 2025, arXiv 2508.12531v1 (COLM 2025), "Rethinking Safety in LLM Fine-tuning: An Optimization Perspective"

| Field | Value | Location |
|---|---|---|
| Models | Llama-2-7B-Chat, Llama-3.2-1B(-Instruct), Qwen2.5-3B-Instruct, Phi-3-3B (the text says "five" but lists four) | §4.1; App. A.2 |
| Full or LoRA | Full-parameter (§4.5 compares LoRA against full-parameter fine-tuning). LoRA rank, alpha, modules NOT FOUND. | §4.5 |
| Optimizer | AdamW; weight decay 0 | §4.1; App. A.2 |
| LR and schedule | 2e-5 default; step LR scheduler, γ 0.85 (step interval NOT FOUND) | §4.1; App. A.2 |
| Batch | "batch size as 8" default; 8 per GPU on 2 GPUs (16 effective, computed); default accumulation 1 | App. A.2; §4.1 |
| Epochs or steps | 1–10 epochs, per experiment. Epochs of the "FT" rows NOT FOUND. | App. A.2 |
| Dataset and size | Dolly 14.4K; Alpaca 49.8K; ORCA 15K and 50K subsamples | Table 1 |
| Template, system prompt | NOT FOUND | — |
| Precision | NOT FOUND | — |
| Seeds, runs | NOT FOUND | — |
| Hardware, time | 2 × RTX A6000; about 45 min per Dolly epoch | App. A.2 |
| Harm metric | AdvBench 520: keyword-match ASR, and GPT-4o judge score 1–5. Also SafetyInstruct, RealToxicityPrompts, WildJailbreak. | §3.1; §4.1 |
| "Best tuned" hyperparameter values | NOT FOUND | — |

**Erosion and its reduction on Dolly (keyword ASR on AdvBench).** Pre-fine-tuning ASR NOT FOUND.

| Model | FT | Best tuned | LoRA | Grad clip | EMA | Location |
|---|---|---|---|---|---|---|
| Llama-2-7B-Chat | 15.96 | 4.62 | 3.72 | 9.62 | 2.70 (Table 2); 2.50 (Tables 3, 4) | Tables 2–4 |
| Qwen2.5-3B-Instruct | 63.46 | 13.27 | — | — | 3.08 | Table 3 |
| Phi-3-3B | 49.04 | 18.27 | — | — | 1.54 | Table 3 |

**Capability (Dolly).**
- MT-Bench, Llama-2-7B-Chat: FT 4.46; best tuned 4.89; EMA 4.33 (Table 2). Table 1 lists 3.88 for the Dolly FT model.
- WildJailbreak benign prompts (higher is better; an over-refusal proxy): Llama FT 80.48 → best tuned 74.76. Qwen FT 88.57 → best tuned 80.00 (Table 3).
- TruthfulQA: Llama 32.58 → 37.22; Qwen 32.45 → 42.61 (Table 3).

**Grid in Figure 2 (legend values; per-point ASR NOT FOUND as numbers).**
- Llama-2-7B-Chat: batch 16, 64, 256; LR 1e-5, 2e-5, 5e-5; accumulation 1, 5, 10, 20.
- Llama-3.2-1B: batch 16, 32; LR 2e-6, 5e-7, 2e-7, 2e-8; accumulation 1, 5, 10, 20.

**Statements.**
- Abstract: hyperparameter choice (LR, batch, gradient steps) cuts unsafe responses from 16% to about 5% (keyword match), with utility kept.
- §3.2, batch and LR: a small batch with a large LR can push the model out of its "safety basin".
- §3.2, accumulation (Figure 2c, 2f): more gradient accumulation lowers ASR and keeps utility.
- §3.2, epochs (Figure 3): at a high LR (5e-5) the epoch count matters little. At a lower LR, ASR falls from 15.56% to 8.56%.
- §4.5 (Table 4): LoRA cuts safety loss a lot compared with full-parameter fine-tuning. Gradient clipping also helps.

### 2.5 Lyu et al. 2024 (PTST), arXiv 2402.18540v2 (NeurIPS 2024)

| Field | GSM8K (main) | ChatDoctor | OpenOrca | Location |
|---|---|---|---|---|
| Model | Llama-2-7B-chat (also Mistral-7B-Instruct-v0.2; GPT-3.5 Turbo through the API) | Llama-2-7B-chat | Llama-2-7B-chat | §3.1–3.3; App. F.1 |
| Full or LoRA | NOT FOUND | LoRA (rank NOT FOUND) | NOT FOUND | App. F.1 |
| Optimizer | NOT FOUND | NOT FOUND | NOT FOUND | — |
| LR, schedule | 1e-4 (chosen on helpfulness) | peak 2e-5, cosine | 2e-5 | §3.1; App. F.1 |
| Batch | NOT FOUND (Llama); GPT-3.5 API chose batch 4, LR multiplier 2 | NOT FOUND | NOT FOUND | §3.2 |
| Epochs | 6 | 3 | 1 | §3.1; App. F.1 |
| Data | GSM8K | ChatDoctor (100k conversations) | 600K sampled from OpenOrca | App. F.1 |
| Template | 5 templates: text:vanilla, text:alpaca, chat:vanilla, chat:alpaca, chat:llama (Llama-2 safety system prompt) | chat templates only | chat templates only | §3.1; Table 9 |
| Precision | NOT FOUND | | | — |
| Seeds | 3 training seeds (GSM8K) | 5 decoding seeds | NOT FOUND | §3.1; Table 4 |
| Hardware | 8 × A100 | | | App. F.1 |

**Erosion (Table 1c, DirectHarm4 ASR, GSM8K, Llama-2-7B-chat; mean (SD) over 3 seeds).**

| Train → test template | Untuned | Fine-tuned |
|---|---|---|
| chat:vanilla → chat:vanilla | 2.75% | 11.00% (0.82) |
| chat:alpaca → chat:alpaca | 4.75% | 46.42% (2.09) |
| chat:llama → chat:llama | 0.00% | 18.08% (2.49) |
| PTST: chat:vanilla → chat:llama | 0.00% | 1.08% (0.12) |

**Capability.** GSM8K exact match 20.32% → 33.39% (chat:vanilla; Table 1a). AlpacaEval win rate (Table 8, LR 2e-5): untuned 82.92%; after Alpaca, LoRA 26.53% and full 26.32%.

**Statement.** §3.2 ("PTST beats early stopping", Figure 2a, GSM8K 1–6 epochs): without PTST, helpfulness and ASR both generally rise with longer training.

### 2.6 DataRx (Zhang et al. 2026), arXiv 2608.04322v1

| Field | Value | Location |
|---|---|---|
| Models | Llama3-8B-Instruct, Qwen2.5-7B-Instruct, Mistral-7B-Instruct-v0.2 | §IV-A |
| Full or LoRA | LoRA on all linear layers; rank 16, scaling factor 32, dropout 0.05 | §IV-A |
| Optimizer | NOT FOUND | — |
| LR and schedule | 2e-4 (main); RQ1 also uses 2e-5. Schedule NOT FOUND. | §IV-A; RQ1 |
| Batch | NOT FOUND | — |
| Epochs | 1 | §IV-A |
| Dataset and size | Not Dolly. GSM8K 7,168; MATH 7,168; HellaSwag 10,240; WinoGrande 10,240; MedQA 9,216; DocBlocks 6,861; Magicoder 10,000 training rows | Table I |
| Template, system prompt | NOT FOUND | — |
| Precision, seeds | NOT FOUND | — |
| Harm metric | DirectHarm4, HarmBench, HEx-PHI; Llama-Guard-3-8B judge; deterministic decoding; ASR = mean of the three | §IV-A |
| Erosion | Base DirectHarm4 ASR: Llama3 12.75%, Qwen2.5 9.5%, Mistral 65.5% (RQ1). Mean ASR after task-only fine-tuning: Llama3 20.24%, Qwen2.5 19.06%, Mistral 78.75% (Table II, last column). Base mean ASR over the three benchmarks: figure only, NOT FOUND as a number. | RQ1; Table II |
| Capability | Task accuracy per task (Table II). Higher LR generally gave higher task accuracy (RQ1, Figure 2). | RQ1; Table II |
| Over-refusal | XSTest, judged by Qwen3Guard-Gen-8B (Figures 6–8, GSM8K setting). Numbers figure only. | §V |

**Statement.** RQ1, observation 2: a raise in LR from 2e-5 to 2e-4 widens the safety gap for all three models and most tasks.

---

## 3. What our engine allows

Checked in `experiments/safety_selection/config.py` (`validate_recipe`) and in the runner.

| Setting | Allowed | Where enforced |
|---|---|---|
| `train.lr_schedule` | `"constant"` only. No warmup, no cosine. | `config.py` line 487, `_fixed(..., "constant", ...)` |
| `train.optimizer` | `"AdamW"` only | `config.py` line 486 |
| `train.lr`, `eps`, `max_grad_norm` | any positive number | `config.py` lines 488–490 |
| `train.weight_decay` | ≥ 0 | `config.py` lines 491–492 |
| `train.micro_batch`, `train.grad_accum` | integers ≥ 1; effective batch = product | `config.py` lines 482–483 |
| Batching | consecutive rows of one epoch's order; the last step of an epoch keeps its actual size; steps never cross epochs | `config.BATCHING`; `stream.py` (`steps_per_epoch` = ceil(rows / effective batch)) |
| `train.checkpoints` | named epoch fractions `[num, den]`, strictly increasing; a job trains only to its target checkpoint | `config.py` lines 411–426; `stream.py` `checkpoint()`; `runner.py` (`target_checkpoint`) |
| `model.lora.r`, `alpha` | integers ≥ 1 | `config.py` lines 472–473 |
| `model.lora.dropout` | `0.0` only | `config.py` line 474 |
| `model.lora.target_modules` | any list of module names | `config.py` line 475 |
| `model.lora.expected_trainable_parameters` | must match the engine's count | `config.py` line 476 |
| Precision | base bf16, trainable fp32 only | `config.py` lines 452–453 |
| Template | Qwen2.5 chat template with a user turn only; the template supplies Qwen's default system message. Same at training and test. | `textproc.py` (`Codec.conversation_ids`, `QWEN_DEFAULT_SYSTEM`) |

The runner also assumes a constant LR. It refuses an a0 state whose saved AdamW LR differs from `train.lr` (`runner.py` about lines 817–821). The Adam-preconditioned attribution reads the LR from the checkpoint's optimizer state (`runner.py` about line 874).

---

## 4. Where our recipe differs, and what likely drives the near-saturation

| Setting | Ours | Literature | Evidence on direction | My weight |
|---|---|---|---|---|
| Optimizer steps × LR | 1,800 steps at 2e-4 (e3); 600 at e1 | Qi Dolly ≈115 steps (computed) at 2e-5 full; SafeTune 1 epoch at 2e-5 LoRA; DataRx 1 epoch at 2e-4 LoRA | Higher LR → more erosion: Qi Table 12; Kim §3.2, Fig. 3; DataRx RQ1. Longer training → more erosion: PTST Fig. 2a. | **High** |
| Effective batch | 8 | 16 (SafeTune, Kim, Qi-LoRA), 20 (He 100-row), 128 (Qi, He full) | Smaller batch → more erosion: Qi Table 12 (lr 5e-5: 46.4% at 16 vs 34.2% at 128); He App. A.6; Kim §3.2 (accumulation) | **High**. Ours is the smallest in every paper read. |
| Epochs | 3 passes over 4,800 rows | 1 in Qi, He (full), SafeTune, DataRx | Mixed. Qi Table 13: flat over 1–5 epochs (full FT, lr 2e-5). PTST Fig. 2a and Kim Fig. 3: depends on LR. | Medium. Our e1 vs e3 will measure it. |
| LoRA rank and modules | r64, all 7 linear, 73.9M trainable | r16 q/k/v/o (SafeTune); r16 all linear (DataRx); α/r = 2 in all three | No paper here isolates rank. LoRA vs full conflicts: Kim Table 4 (LoRA safer); Qi Table 11 (LoRA worse, but at its own LR and batch). | Low to medium; no direct evidence |
| LR schedule | constant | cosine + 3% warmup (SafeTune); step γ 0.85 (Kim) | No paper here isolates the schedule. A decay lowers the mean LR. | Low |
| LoRA dropout | 0 | 0.05 (SafeTune, DataRx) | No evidence here | Low |
| Gradient clip | 1.0 | Kim: clipping helps (Table 4); others NOT FOUND | Already on | — |
| Model family (not a recipe setting) | Qwen2.5-1.5B-Instruct | Kim Table 3: under the same FT recipe, Qwen2.5-3B reaches 63.46% vs 15.96% for Llama-2-7B | Qwen models may erode more easily | Explains part of the size |
| Harm metric (not a recipe setting) | 3 sampled answers at T 0.7 | Greedy or T 0 in Qi, He, SafeTune, DataRx | Sampling likely gives higher unsafe rates than greedy | Explains part of the size |

**Conclusion.** The two strongest levers are total update (many small-batch steps at 2e-4) and the small effective batch of 8. Three epochs probably add to it, but the evidence is mixed. The literature gives no direct test of rank 64 vs 16. Part of the 87.3% likely comes from the Qwen family and from sampled decoding. A recipe change does not remove those parts.

---

## 5. Two candidate literature-matched LoRA recipes

Both recipes use only fields the engine accepts today. Fields not listed stay as in `study-kt-instruct-r64-mb4-20261006.json`. Both keep checkpoints `q` [1,4], `e1` [1,1] and `e3` [3,1], so `attribution.checkpoints` does not change. A job trains only to its target checkpoint.

### 5.1 Recipe A: closest to SafeTune's LoRA-on-Dolly settings

| JSON field | Now | Recipe A | Why |
|---|---|---|---|
| `name` | `study-kt-instruct-r64-mb4-20261006` | new name, e.g. `study-kt-instruct-r16qkvo-safetune-<date>` | new identity |
| `purpose` | Stage 0 text | new text that cites SafeTune App. B, Table 8 | record the source |
| `model.lora.r` | 64 | **16** | SafeTune Table 8 |
| `model.lora.alpha` | 128 | **32** | SafeTune Table 8 |
| `model.lora.target_modules` | 7 modules | **`["q_proj","k_proj","v_proj","o_proj"]`** | SafeTune Table 8 |
| `model.lora.expected_trainable_parameters` | 73,859,072 | **4,358,144** (computed: 16 × 28 layers × (3,072 + 1,792 + 1,792 + 3,072)) | the engine checks it; confirm at preflight |
| `model.lora.dropout` | 0.0 | 0.0 (no change) | engine allows 0.0 only; SafeTune uses 0.05 (deviation) |
| `train.micro_batch` | 4 | 4 (no change) | |
| `train.grad_accum` | 2 | **4** | effective 16 = SafeTune "2×8" read as 16 |
| `train.lr` | 0.0002 | **0.00002** | SafeTune Table 8 (peak LR) |
| `train.lr_schedule` | constant | constant (no change) | engine allows constant only; SafeTune uses cosine with 3% warmup (deviation) |

Steps (computed from `stream.py`): 300 per epoch. `q` = step 75, `e1` = step 300, `e3` = step 900.

- **Match to SafeTune:** `e1`, the one-epoch point.
- **Optional match:** `e3`. If SafeTune used the full Dolly (size NOT FOUND), `e3` sees a similar number of rows (14,400).
- **Constant LR note:** a constant 2e-5 gives more total update than a cosine schedule with a 2e-5 peak. A mean-matched alternative is 1e-5. I chose the peak value as the closer literal match.
- **Training time, estimate:** `e1` ≈ 7 min; `e3` ≈ 20 min. Basis: 20 min for 3,600 micro-batches of 4 → 1,200 micro-batches per epoch. Training only, at micro-batch 4. Excludes loading, generation, judging and attribution. The smaller adapter may be slightly faster (not measured).

### 5.2 Recipe B: Qi et al. adapted to LoRA (1 epoch, large effective batch)

| JSON field | Now | Recipe B | Why |
|---|---|---|---|
| `name` | as now | new name, e.g. `study-kt-instruct-r64-b128-qi-<date>` | new identity |
| `purpose` | Stage 0 text | new text that cites Qi §4.4, App. F and G.1 | record the source |
| `model.lora.*` | r64, α128, all 7, 73,859,072 | no change | Qi's LoRA rank and modules are NOT FOUND, so B changes only the optimizer side |
| `train.micro_batch` | 4 | 4 (no change) | |
| `train.grad_accum` | 2 | **32** | effective 128 = Qi's "official batch size" |
| `train.lr` | 0.0002 | **0.0001** | Qi's own LoRA benign LR (App. F). Qi's 2e-5 is a full-parameter value. |
| `train.lr_schedule` | constant | constant (no change) | Qi's schedule NOT FOUND |

Steps (computed): 4,800 / 128 = 37.5, so 38 steps per epoch, and the last step has 64 rows. `q` = step 10, `e1` = step 38, `e3` = step 114.

- **Match to Qi, one epoch:** `e1`.
- **Match to Qi, steps and rows seen:** `e3`. It has 114 steps and 14,400 rows; Qi's Dolly run had ≈115 steps (computed) and 14,624 rows.
- **Equal-step variant:** `grad_accum` 30 gives effective 120 and 40 equal steps per epoch.
- **Training time, estimate:** `e1` ≈ 7 min; `e3` ≈ 20 min. Same basis as recipe A: the micro-batch count does not change with accumulation.

### 5.3 Dose comparison (rough proxy)

LR × optimizer steps is a rough proxy for the maximum drift under Adam. It is my heuristic, not from the papers. It is comparable only between runs with the same adapter.

| Run | Adapter | LR × steps |
|---|---|---|
| Current e3 | r64 all-linear | 2e-4 × 1,800 = 0.36 |
| Current e1 | r64 all-linear | 2e-4 × 600 = 0.12 |
| Recipe B e3 | r64 all-linear | 1e-4 × 114 = 0.0114 |
| Recipe B e1 | r64 all-linear | 1e-4 × 38 = 0.0038 |
| Recipe A e3 | r16 q/k/v/o | 2e-5 × 900 = 0.018 |
| Recipe A e1 | r16 q/k/v/o | 2e-5 × 300 = 0.006 |

Both candidates are 10–100 times gentler than the current recipe on this proxy.

---

## 6. Engine changes either recipe would need

**None for recipes A and B as written above.** Both use constant LR, dropout 0, AdamW and supported fields.

An exact SafeTune match would need two changes that the validator now refuses:

1. **Cosine schedule with 3% warmup.** This needs:
   - a schedule field in `config.py`;
   - a scheduler in `engine.py`, saved and restored with the optimizer state;
   - a change to the runner's a0-state check, which compares the saved LR with `train.lr` (`runner.py` about 817–821);
   - a decision on which LR the Adam-preconditioned attribution uses (`runner.py` about 874).

   **Main cost:** with a decaying schedule, the `e1` checkpoint of a 3-epoch run is not equal to a 1-epoch run. Each training length then needs its own run. A constant LR keeps `e1` and `e3` in one run.
2. **LoRA dropout 0.05.** This needs a change to `config.py` line 474. Dropout also makes per-row gradients random, and that affects the attribution variants.

**Recommendation:** do not change the engine for this decision. Record the two deviations in the recipe `purpose`.

---

## 7. Concerns and open decisions for GPT

1. **The rule names the candidates.** The recipe choice rule (FOCUS.md, 6 October) names only `e1` and `e3` of `study-kt-instruct-r64-mb4-20261006` as candidates. A switch to recipe A or B changes that rule. It needs the user's agreement and a new Gate A with 3 seeds at the new recipe.
2. **Simplest option first.** `e1` of the current recipe already matches DataRx's LR (2e-4) and epoch count (1), with a larger rank and a smaller batch. Its results for seeds 1102 and 1103 are pending. If `e1` qualifies under the rule, no switch is needed.
3. **Risk of too little erosion.** A and B are much gentler (Section 5.3). Qi's Llama-2 Dolly erosion was +11.5 pp, which is below our E ≥ 15 pp threshold. SafeTune's Dolly drops (26–44 pp RR) and Kim's Qwen2.5-3B result (63.46%) suggest that a gentle recipe can still erode a lot. But their metrics differ from ours. A one-seed dose check of A or B (e1 and e3 in one run) would show the size before a 3-seed commitment. That needs the user's go for spend.
4. **Data size differs.** Qi and probably SafeTune used the whole of Dolly; we use 4,800 rows. "1 epoch" therefore means about a third of their steps and rows. The `e3` points of A and B match rows seen, not epochs.
5. **Confounds that a recipe change cannot fix:** the Qwen family's fragility (Kim Table 3), and sampled decoding against greedy decoding in the literature.

---

## 8. Everything NOT FOUND

- **Qi et al.:** LR schedule and warmup; per-device batch, accumulation, devices; precision; seeds and number of runs; exact Dolly system prompt text; LoRA rank, alpha and modules (App. F); Dolly capability; over-refusal.
- **He et al.:** optimizer; LR schedule; template and system prompt; precision; dataset sizes after filtering; Dolly capability; over-refusal; device count.
- **SafeTune:** Dolly subset size, and so the step count; meaning of the "2×8" split; template and system prompt; cosine decay floor; IFEval and OR-Bench-Hard values for Dolly; numbers of the rank study.
- **Kim et al.:** pre-fine-tuning ASR; "best tuned" hyperparameter values; epochs of the FT rows; LoRA rank, alpha and modules; template; precision; seeds; per-point values of Figures 2–3; step interval of the LR scheduler.
- **PTST:** batch size and full-vs-LoRA for the Llama GSM8K runs; optimizer; precision; LoRA rank for ChatDoctor.
- **DataRx:** batch size; optimizer; LR schedule; template; precision; seeds; base mean ASR as a number; over-refusal values.

---

## Method record

- Commands run (all exit 0):
  - `pdftotext -layout` on each fetched PDF;
  - `pdftotext` without layout for DataRx;
  - `grep` and `sed` reads of the extracted text;
  - `grep` and `sed` reads of `config.py`, `stream.py`, `runner.py`, `engine.py` and `textproc.py`;
  - one `python3` arithmetic check for the LoRA counts and step counts.
- LoRA count check: r64 all-linear = 1,154,048 × 64 = 73,859,072. This matches the recipe's asserted count. The attention-only figure uses the same architecture split: hidden 1536; k/v output 256; MLP 8960; 28 layers.
- PDFs saved by the fetch tool sit in this session's `tool-results` folder. The extracted text sits in the session scratchpad. Neither folder is in the repository.
