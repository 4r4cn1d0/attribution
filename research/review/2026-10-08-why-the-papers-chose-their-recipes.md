# Note: how Qi, He and Guo chose their benign fine-tuning recipes

**Date:** 8 Oct 2026 (IST). Read-only desk check by a GI III helper: arXiv HTML and the public repositories, fetched with curl. No runs, no spend, no held-out data. **R** = read in the source (location given). **I** = inference. **UNVERIFIED** = not checked. The exact numeric settings from code are in GI II's companion note `2026-10-08-exact-recipes-from-code.md`.

## 1. Where each setting came from

**Qi et al. 2023 (2310.03693): chosen to look like a careful practitioner.**
- Llama-2 (R §4.4): by default 1 epoch, batch 128, LR 2e-5. The paper says this follows the "officially recommended guidelines".
  - The code is llama-recipes (R llama2/README.md). The Dolly notebook runs 2 GPUs × 64, LR 2e-5, 1 epoch (R llama2/tier3-benign-dolly.ipynb).
  - llama-recipes' own config defaults differ: LR 1e-4, batch 4, 3 epochs (R llama2/configs/training.py). The paper cites no "official" source (UNVERIFIED).
  - I: batch 128 and LR 2e-5 match Stanford Alpaca's published 7B recipe, which used 3 epochs.
  - The scheduler steps once per epoch, so a 1-epoch run has a constant LR and no warmup (R finetuning.py l.240; train_utils.py l.151).
- GPT-3.5 (R §4.1): only epochs can be set, and they used 1.
- LoRA (App. F): benign runs used the officially recommended LoRA settings, LR 1e-4, batch 16, 1 epoch. The rank is not given; the repo default is r8, alpha 32, q/v only, dropout 0.05 (R configs/peft.py; whether they used it is UNVERIFIED).
- **The argument** (R §3.2, §4.4): well-meaning users trust the model's alignment. The official recipe is the good-faith baseline. A higher LR or a smaller batch counts as careless tuning.

**He et al. 2024 (2404.01099): no reason stated.**
- 100-row subsets: LR 5e-5, batch 20, 5 epochs. Full set: batch 128, 1 epoch. The paper calls these "default", with no source and no user model (R §3.1, App. A.3).
- The repository is a fork of Qi's code (R). I: the subset recipe is Qi's harmful-data attack recipe (5e-5, 5 epochs, batch 10; Qi §4.2) with the batch doubled.
- Conflicts (UNVERIFIED): full-set LR 5e-5 in the paper vs 2e-5 in the code; the script runs 20 per GPU on 2 GPUs (40 in total) while the paper says 20.
- **The argument:** find which data breaks safety, not copy users. Small batches suit their one-step-per-example selection (App. A.6).

**Guo, Chen et al. 2026 (2609.01455): no reason stated.**
- Full fine-tune: 5 epochs, LR 5e-5, batch 20. This is He's subset recipe (R §4.1; I: copied).
- LoRA: LR 2e-4, batch 32, r32, alpha 64, 5 epochs (R §4.1). The code comments add cutoff 512, cosine schedule, warmup 0.1 (R src/experiment/finetuning_pipeline.py); LoRA dropout 0.05, all linear layers, loss on the response only (R finetuning_pipeline_lora.py).
- These are **not** LLaMA-Factory's shipped examples. Today those are LoRA r8 (alpha 2r), LR 1e-4, 3 epochs, batch 8; full LR 1e-5 (R examples/*qwen3*.yaml at HEAD; the examples at the time of their runs are UNVERIFIED).
- **The argument** (R §2.1, §4.1): practitioners adapt models with benign data; Alpaca and Dolly are widely used. I: they needed a strong collapse to study the mechanism. Full SFT on 5,000 rows cuts Llama MMLU from 68.6 to 28.0 (Table 2).

## 2. Sensitivity results in the papers

- **Qi Table 12** (Alpaca, Llama-2, full, 1 epoch), harmfulness rate:

  | LR | Batch 16 | 32 | 64 | 128 |
  |---|---|---|---|---|
  | 2e-5 | 23.6% | 20.6% | 15.8% | 16.1% |
  | 5e-5 | 46.4% | 37.9% | 31.5% | 34.2% |

  - Epochs 1/3/5 (Table 13): Llama 16.1/16.7/13.0%; GPT-3.5 31.8/27.3/23.0%. More epochs did not raise harm.
  - LoRA vs full (Table 11): 25.2% vs 16.1%, at different LR and batch. No rank sweep.
- **He:** batch 10/20/50 (Fig. 4): batch 50 is much lower. Table 10, bottom-100 subset, 1 epoch: 23.5% at batch 10 vs 7.3% at batch 20. No LR sweep, no LoRA.
- **Guo:** only data size (100 to 5,000 rows at 5 epochs) and method. Table 2, 100 → 5,000 rows: Llama LoRA 2.4 → 44.8%; Qwen LoRA 4.5 → 9.1%; full Llama 75.4 → 71.2%, full Qwen 63.6 → 57.9%. No LR, epoch or rank sweep.

## 3. Consequences for our study (all I)

- Only Qi argues for a "typical user" setting, and only for full fine-tuning of Llama-2 and for the OpenAI API. He's and Guo's recipes descend from Qi's *attack* recipe (Qi → He → Guo). Matching them gives comparability, not realism.
- No paper sweeps the LoRA rank, so our rank-16 test is new evidence.
- **The Guo gap is not explained by strength.** Guo's Qwen2.5-7B LoRA (r32, all linear, peak LR 2e-4, about 785 steps) stayed at 9.1% unsafe. Ours reached 87% after 38 steps at LR 1e-4 with r64. Their recipe is stronger in LR and steps. So rank alone is unlikely to explain the gap. Differences still to check: dropout 0.05 vs 0; cutoff 512 vs 3,072 tokens; Alpaca vs Dolly; template; judge (GPT-4o mini vs Qwen3Guard) and prompts (HEx-PHI vs our bank); generation cap 512 vs 2,048. Our loss is already on the response only, as theirs is.
- Every paper finds more erosion at a higher LR and a smaller batch. A defensible design: a practitioner anchor (a tool's shipped defaults, e.g. LLaMA-Factory r8, LR 1e-4, cosine) plus a dose axis (steps × LR) to find where partial erosion starts.
