# Qi et al. constrained SFT as the B+Qi reference: settings, the "no warmup" decision, engine build, cost

Written 2026-10-16 from about 21:00 UTC (17 Oct IST; clock checked with `date -u` at 21:21 and 21:23 UTC) by an Opus worker for the main-study lead (General Implementation VI). Read-only on the repository: no code change, no commit, no pod, no spend, no message. I did not open `rows.jsonl`, `groups.json`, `selector.jsonl`, `hidden/` or a held-out file. This file has no rows, prompts, answers or anchor text.

**Labels.** **P** = read in the paper, arXiv 2406.05946 v1 (the only version), read as page images: pp. 1–11 and 16–25 (all text and appendix pages; pp. 12–15 are the reference list, not read). **C** = read in the official code: [github.com/Unispac/shallow-vs-deep-alignment](https://github.com/Unispac/shallow-vs-deep-alignment), commit `fb1749e3a9af…` (23 Apr 2025), MIT licence (GitHub API), read as text to stdout (no file saved, nothing run). **R** = read in this repository at HEAD `d79f641` (`path:line`). **I** = my inference or estimate; its basis follows it. **UNVERIFIED** = not checked.

**Hashes of the repository files I used (SHA-256, first 16):** FOCUS `23e3da8f893e8135`; engine.py `f0b8e290141d5a56` (equal to the code hash in the w0b-2 retrain unit's `identity.json`, so the engine I read is the certified one); config.py `db130e3c9ea4508a`; runner.py `36e266314e73a0a9`; recipe S `study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json` `464708c91cd4c297`.

**Gate B values I saw (for REQ-21 (m)).** I read cost and timing records only: (1) the stage seconds in the ledgers of the three wave-0a arms (`tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/*/ledger.jsonl`); (2) the ledger and `steps.jsonl` of the wave-0b retrain unit a0@1101 (`…/w0b-2/tree/round1/1101-a0-e1-a1/`): per-step seconds, token counts of steps 1–3, and the training loss of steps 1–6 and 38. That retrain's adapter fingerprints equal Gate A's P1101 (FOCUS 13:21 UTC entry), so these losses are Gate A values. I read no U, O, task loss, ranking or score of any Gate B arm.

---

## 0. Summary

### 0.1 Answers to the brief

| Question | Answer | Source |
|---|---|---|
| What is the loss? | Per answer token t: (2/β_t) · softplus(β_t · Δ_t), with Δ_t = log π_aligned(y_t \| x, y_<t) − log π_θ(y_t \| x, y_<t). Summed over the answer tokens. Its gradient is ordinary cross-entropy times a weight w_t = 2σ(β_t Δ_t). The weight is 1 at the start. It falls when the fine-tuned model gives the target token more probability than the aligned model. | P: Eq. 3–5, p. 8–9; App. D, Eq. 6–11, 19 |
| Is it a KL? | No. It is a log-ratio on the observed target token only. The RL reading in App. D.3 has a token-wise KL; Eq. 3 is a lower-bound surrogate that drops that KL term. Only the reference log-probability of each target token is needed. | P: Eq. 23, 28–31, pp. 23–25 |
| β per position | t = 1: 0.5. t = 2…5: 2.0. t > 5: 0.1. The code builds it as base 0.1, ×5 for the first token, ×20 for tokens 2–5. | P: §4.2, p. 9; Table 3 caption. C: `finetune.py` arguments; `get_beta_list` |
| Reference model | The initial aligned model, fixed. For us: OLMo-2-0425-1B-Instruct at revision `48d788ec…`, which is recipe B's LoRA base with the adapter off. No new download. | P: §4.1; C: reference computed once from the initial model |
| Positions | Answer tokens only. t = 1 is the first answer token after the chat template's assistant marker. The end-of-sequence token is a target and is the last t. The prompt has no loss. | C: the Llama-2 collator masks up to the end of the `[/INST]` marker; the EOS is in the target. R: `textproc.py:173-183` (our targets are the response plus `<\|endoftext\|>`) |
| Anchor, safety or augmentation data | None. Constrained SFT uses only the fine-tuning data. The safety-recovery augmentation (§3) is a separate method; combining the two gave no consistent gain (Table 6). | P: §4.2; App. C, p. 19. C: the `soft_sft` path passes no anchor set |
| Benign-data settings | AdamW (β1 0.5, β2 0.999); LR 2e-5 (Llama-2-7B-Chat), 5e-6 (Gemma-1.1-7B-IT); batch 64; 3 epochs; full fine-tuning; **a linear LR warmup over the first 10 steps for constrained SFT**. 3 rounds per cell. | P: App. A.5.1, A.5.3, pp. 17–18. C: README commands |
| What "without warmup" removes | **Exactly one thing: the 10-step linear learning-rate warmup.** Not a β ramp, not data, not a KL schedule. The loss, the β values and the reference stay. | P: App. A.5.1, p. 17; App. C, p. 19. C: `use_warmup` sets HF `warmup_steps = 10` |
| Engine work | One new optional recipe key, a weighted per-token loss in `engine.py`, one extra no-gradient forward per micro-batch with the adapter disabled, extra step logging, two guards, tests and mutants, a new recipe file, and a certificate X → X′. About 0.5–1 day of build plus one fix round (I). | §5 |
| Cost | About **1.03–1.05 FRE per seed** under C-full and **about 1.2–1.3 FRE** under C-lean (I). Six seeds: about 6.3 FRE, about $11 at $1.79/h, about $13.4 with the 1.25 contingency (I). The certificate pod: about $1–1.5 (I). | §6 |

### 0.2 Findings for the lead

- **FQ1. The decision removes the LR warmup only.** Qi et al. use a linear learning-rate warmup over the first 10 optimizer steps for constrained SFT (P: App. A.5.1, p. 17). In the code this is HF's `warmup_steps = 10` (C: `finetune.py`). Under HF's schedule the first optimizer step runs at LR 0 (R: `engine.py:261-280` states the same HF convention). The authors give the reason: at step 1, Δ = 0 and w = 1, so the first steps are plain cross-entropy steps and can break alignment before the constraint acts (P: App. A.5.1; App. C).
- **FQ2. The paper's headline benign result mixes two changes.** Table 3's "Standard SFT" numbers equal Table 5's SFT column *without* warmup. Table 3's "Constrained SFT" numbers equal Table 5's constrained column *with* warmup (I: the numbers match cell by cell). On benign data the loss alone (no warmup) helped on SQL Create Context only: Samsum 23.4 → 23.1, SQL 15.4 → 2.0, GSM8k 3.3 → 3.1 (ASR %, Llama-2-7B-Chat; P: Table 5, p. 20). Warmup alone gave 3.8, 3.3 and 2.9. This confirms SPEC F4. The FAQ's "their Table 9" (FOCUS:70; paper draft decision 22) is Table 5 in arXiv v1.
- **FQ3. Two more of Qi's optimizer settings are absent from B+Qi, and the 9 Oct decision does not name them.** They are absent because B+Qi sits on recipe B. (a) AdamW β1 = 0.5 for every fine-tuning run (P: App. A.5.1). The code's comment says a smaller first momentum makes the optimizer respect the constraint more (C: `finetune.py`). (b) In the code only: no `lr_scheduler_type` is passed, so HF's default linear decay to zero applies after the warmup (I: the transformers default; README pins transformers 4.40.2). Recipe B keeps β1 = 0.9 and a constant LR. **Why this matters (I):** with bias-corrected Adam, the step-1 gradient (which is unconstrained, w = 1) still holds about 47%, 30% and 16% of the momentum at steps 2, 3 and 5 when β1 = 0.9; with β1 = 0.5 it holds 33%, 14% and 3%. Our loss already plateaus by step 2–3 of 38 (R: PLAN-S §1 item 3). So B+Qi as decided is the weakest form of the method. This is a second, independent reason to expect B+Qi near recipe B.
- **FQ4. Faithful baseline against isolated loss: a consequential trade-off.** Recipe G + the loss ("G+Qi") is closer to the released code than B+Qi: G has a token-mean loss, a linear warmup and a decay to zero (R: the G config; C: token mean, warmup, HF linear decay). B+Qi isolates the loss on the main recipe, as the 9 Oct proposal intended (FOCUS:148). Our own `bt` run found that the schedule, not the loss weighting, carries recipe G's lower erosion (R: FOCUS:198; one seed, development evidence). An ICML reviewer may say that B+Qi is not Qi et al.'s method. The decision is the user's (9 Oct item (10)); I do not change it. Options are in §8.
- **FQ5. A 10-step warmup has no faithful transfer to a 38-step run (I).** Qi's benign runs have more than 600 steps (P: App. B, p. 19), so 10 steps are under about 1.7% of a run. In our run, 10 steps are 26%. A proportional warmup is under one step, and under HF's convention a one-step warmup only moves step 1 to LR 0. This supports the decision to leave warmup out.
- **FQ6. Task-loss risk (I).** The constraint holds the first 5 answer tokens near the untuned model. The held-out task loss counts those tokens. Under recipe B's per-example mean the first 5 answer tokens carry 17.7% of the objective (R: PLAN-S §1 item 8). So B+Qi's held-out task loss may sit between the untuned model's and a0's, and may pass τ_L. Qi's own Llama GSM8k utility fell from 41.7 to 37.4 (P: Table 3). Write this as a prediction risk.
- **FQ7. Record corrections.** (a) FOCUS:70 and the paper draft (decision 22; risk 18; CITE-CHECK 25) say "Table 9": it is Table 5 in arXiv v1 (the ICLR numbering is UNVERIFIED). (b) CITE-CHECK 25 asks for the paper's own term: the paper says "Constrained SFT" (Table 3) and a "token-wise constrained objective" (§4.1 heading). (c) RS B12's note "Qi's loss also needs the aligned model's token probabilities" is confirmed: it needs only the log-probability of each target token, from one forward of the model already loaded.

---

## 1. The method in the paper (P)

### 1.1 Objective and its reading

- **Standard SFT** (Eq. 1, p. 5): minimise the summed negative log-likelihood of the answer tokens. π_θ starts at π_aligned.
- **Constrained objective** (Eq. 3, p. 8): minimise, over the data, −Σ_{t=1}^{|y|} (2/β_t) · log σ(β_t · [log π_θ(y_t | x, y_<t) − log π_aligned(y_t | x, y_<t)]).
- **Equivalent form** (Eq. 4, p. 8; Eq. 9–11, p. 20): Σ_t 1{t ≤ |y|} · (2/β_t) · S(β_t Δ_t), with S(z) = log(1 + e^z) and Δ_t = log π_aligned − log π_θ on the target token.
- **Gradient** (Eq. 5, p. 9; Eq. 19, p. 22): w_t · (−∇ log π_θ(y_t | …)), with w_t = 2σ(β_t Δ_t). At the start π_θ = π_aligned, so w_t = 1 and the gradient equals cross-entropy's. The factor 2/β_t is there so that the gradient size matches cross-entropy while w_t has not fallen (P: footnote 6, p. 9).
- **Limits.** Small β_t: the token loss is cross-entropy plus a θ-free constant, (2/β_t) log 2 + log π_aligned (Theorem 1, Eq. 12–13, p. 21). Large β_t: the token loss tends to 2 · max(Δ_t, 0) (Theorem 2, p. 21). That limit is 0 only when π_θ = π_aligned on the data's support (Theorem 3, p. 22).
- **What the weight does (I, from Eq. 5).** It only scales each token's cross-entropy gradient. It never pulls a token back toward the reference. It stops rewarding further increases of the target token's probability once the fine-tuned model already exceeds the aligned model there. For a target token that the fine-tuned model under-predicts (Δ > 0), w > 1.
- **Reduction.** Eq. 3 sums over the tokens of each sequence and takes the expectation over sequences. There is no 1/|y| factor. (The code differs; §2.)

Weight w_t = 2σ(β_t Δ_t) at a few values of Δ_t (I; computed). Δ_t = −1 means the fine-tuned model gives the target token e ≈ 2.7 times the aligned model's probability.

| β_t (positions) | Δ = 0 | Δ = −0.5 | Δ = −1 | Δ = −2 | Δ = −4 |
|---|---|---|---|---|---|
| 0.5 (t = 1) | 1.000 | 0.876 | 0.755 | 0.538 | 0.238 |
| 2.0 (t = 2–5) | 1.000 | 0.538 | 0.238 | 0.036 | 0.001 |
| 0.1 (t > 5) | 1.000 | 0.975 | 0.950 | 0.900 | 0.803 |

So tokens 2–5 are held tightly, the first token less so, and later tokens are almost plain cross-entropy.

### 1.2 Settings (P: §4.2, p. 9; App. A, pp. 16–18)

| Item | Value |
|---|---|
| Models | Llama-2-7B-Chat; Gemma-1.1-7B-IT |
| β_t | 0.5 (t = 1); 2.0 (t = 2–5); 0.1 (t > 5) |
| Optimizer | AdamW, β1 0.5, β2 0.999 (all fine-tuning runs, SFT and constrained) |
| Learning rate | 2e-5 (Llama); 5e-6 (Gemma) |
| Batch | 64 |
| Epochs | 25 for the three attacks; 3 for the three benign sets (Samsum, SQL Create Context, GSM8k) |
| Warmup | linear LR warmup over the first 10 steps, for constrained SFT (A.5.1). Table 5 also reports SFT with the same warmup |
| Parameters | full fine-tuning (I: no LoRA is mentioned; the code is full-parameter with DeepSpeed ZeRO-2) |
| Compute | 4 × A100-80GB or 4 × H100-80GB nodes (A.1) |
| Safety evaluation | HEx-PHI (330 harmful instructions), GPT-4 judge, ASR = share of score 5; decoding top-p 0.6, temperature 0.9 (A.2) |
| Rounds | 3 per cell; Table 3 gives mean ± std |

### 1.3 Results that bear on B+Qi

**Table 3 (p. 10), benign rows, Llama-2-7B-Chat** (initial → SFT → constrained; ASR % and utility, mean ± std over 3 rounds):

| Data | ASR | Utility |
|---|---|---|
| Samsum (ROUGE-1) | 1.5 → 23.4 ± 2.5 → 3.2 ± 0.8 | 25.5 → 51.7 ± 0.5 → 50.1 ± 0.2 |
| SQL Create Context (ROUGE-1) | 1.5 → 15.4 ± 1.4 → 3.2 ± 0.8 | 14.9 → 99.1 ± 0.2 → 98.5 ± 0.1 |
| GSM8k (accuracy) | 1.5 → 3.3 ± 0.4 → 2.0 ± 0.5 | 25.5 → 41.7 ± 0.4 → 37.4 ± 0.3 |

Gemma's benign SFT barely erodes (ASR 2.0, 2.8, 2.9 after SFT), so its benign rows say little about protection.

**Table 5 (p. 20): the warmup ablation, Llama-2-7B-Chat** (no std given). Columns: SFT / SFT + warmup / constrained / constrained + warmup.

| Data | ASR % | Utility |
|---|---|---|
| Samsum | 23.4 / 3.8 / 23.1 / 3.2 | 51.7 / 51.9 / 50.2 / 50.1 |
| SQL Create Context | 15.4 / 3.3 / 2.0 / 3.2 | 99.1 / 99.1 / 98.6 / 98.5 |
| GSM8k | 3.3 / 2.9 / 3.1 / 2.0 | 41.7 / 41.6 / 37.2 / 37.4 |
| Harmful Examples (attack) | 88.9 / 89.4 / 29.1 / 4.6 | — |
| Identity Shifting (attack) | 79.5 / 44.8 / 69.6 / 8.1 | — |

- The authors conclude that warmup makes constrained SFT more consistently safe and that most of the gain comes from the objective (P: App. C, p. 19). That holds for the attacks. On benign data it holds for SQL only. On Samsum, warmup alone does the work.
- The SQL difference between the loss alone (2.0) and both (3.2) is within about 1.5 of Table 3's std of 0.8 (I), so the two are not distinguishable.

**Table 4 (p. 19): the β ablation** (I: these runs use warmup, because the "biased β" column equals Table 3's constrained column cell by cell). Uniform β = 0.1 fails on Harmful Examples (86.2%) but gives benign ASR 3.9 / 3.3 / 4.0, close to SFT + warmup. Uniform β = 2.0 is safe, but GSM8k utility collapses to 2.1%. So on benign data, the per-position design matters less than the warmup.

**App. B (pp. 18–19).** In benign SFT the first answer tokens have much larger gradient norms (Fig. 5). After only 10 SFT steps, ASR is already 13.6% (SQL) and 22.1% (Samsum), against 14.9% and 25.5% after the full run of more than 600 steps. So in their setting most benign erosion happens in the first 10 steps. (These full-run numbers differ slightly from Table 3's 15.4 and 23.4; the paper does not say why.)

---

## 2. The official code (C)

Repository `Unispac/shallow-vs-deep-alignment`, commit `fb1749e` (23 Apr 2025), MIT licence. README pins transformers 4.40.2 and trl 0.8.1. UNVERIFIED: that this commit produced the arXiv v1 tables (the commit is dated after ICLR 2025).

- **Reference log-probabilities are precomputed once.** Before training, the trainer runs the initial model (the same object as the policy, before any step) over the whole training set, in order, and stores each row's per-token log-probabilities. It then deletes the reference model (`trainer.py`, `get_train_dataloader`, about lines 670–727; `_inner_training_loop`, about lines 1381–1383).
- **Loss as implemented.** Per real target token: weight = 2(1 − σ(β_t(log π_θ − log π_ref))) = 2σ(β_t Δ_t), detached from the graph, floored at 1e-3, times −log π_θ. The step loss is the mean over all real target tokens of the per-device batch (`soft_sft_loss`, about lines 896–937; `get_batch_loss_metrics`, about lines 939–998). Consequences: (1) the gradient equals Eq. 5, except that the weight never falls below 1e-3; (2) the logged loss is a weighted NLL, not Eq. 3's value (Eq. 3's value carries the large constant (2/β_t) log 2 per token); (3) the reduction is a token mean over each device's batch, not Eq. 3's per-sequence sum.
- **β construction.** `beta = 0.1`, `first_token_bias_factor = 5`, `bias_factor = 20`, `bias_length = 5`; positions count from the first target token; a row shorter than 5 targets takes the first entries of the prefix list (`get_beta_list`).
- **Positions.** The Llama-2 collator sets every label up to the end of the `[/INST]` marker to the ignore index, so only answer tokens count. The string format appends the end-of-sequence token to the answer, so it is a target (`llama2.py`, `CustomDataCollator`; `LlamaStringConverter`).
- **Warmup and schedule.** `use_warmup=True` sets `warmup_steps = 10` (`finetune.py`, about lines 120–121). The README uses `use_warmup=True` for both the SFT and the constrained commands. No `lr_scheduler_type` is passed, so HF's default "linear" schedule applies: warmup, then a linear decay to zero (I: transformers default).
- **Optimizer.** β1 = 0.5 for every run that is not the augmentation experiment (`finetune.py`, about lines 110–118); the comment ties it to respecting the constraint. β2 and weight decay are HF defaults (0.999 and 0; I).
- **Other.** 16 rows per device × 4 devices = 64; DeepSpeed ZeRO-2; bf16; `max_seq_length` 512; dropout disabled. SQL Create Context uses every fifth training row, 20% of the split (`get_finetuning_data.py`, about lines 117–118).

---

## 3. What "B+Qi without warmup" removes, keeps and changes

The decision: "B+Qi runs without Qi et al.'s warmup" (user, 9 Oct 19:37 UTC, item (10); FOCUS:125), on the lead's proposal "Qi et al.'s constrained loss on recipe B without their warmup, so the arm isolates the loss; recipe G already covers the schedule" (FOCUS:148).

### 3.1 Removed by the decision
- The 10-step linear LR warmup (P: A.5.1; C: `warmup_steps = 10`). Nothing else.

### 3.2 Kept (the method itself)
- The token-wise loss (Eq. 3–5), its β_t per position, the fixed reference π_aligned = the untuned model, answer-token positions with the end-of-turn token included, and no extra data.

### 3.3 Different because B+Qi sits on recipe B (not named by the decision)

| Item | Qi et al. (P or C) | B+Qi on recipe B (R: recipe S config) | Expected effect (I) |
|---|---|---|---|
| LR schedule | 10-step linear warmup; linear decay to 0 (C only) | constant 1e-4 from step 1 | the unconstrained first steps run at the peak LR |
| AdamW β1 | 0.5 | 0.9 | step 1's unconstrained gradient stays in the momentum for about 5–10 steps (FQ3) |
| LR | 2e-5 (full fine-tuning, 7B) | 1e-4 (LoRA r 64) | LoRA usually needs a larger LR; not comparable directly |
| Batch, length of run | 64; 3 epochs, more than 600 steps | 128 (4 × 32); 1 epoch, 38 steps | erosion is front-loaded in both (App. B; our loss plateau by step 2–3) |
| Parameters | full, bf16 | LoRA r 64, α 128, 7 modules; base bf16, adapter fp32 | — |
| Reduction | token mean over each device's batch (C); a per-sequence sum in Eq. 3 (P) | recipe B's per-example mean of the token terms, then the mean over the step's rows | keeps recipe B's weighting, so only the token loss changes |
| Weight floor | 1e-3 (C only) | proposed: 1e-3, as the code | tiny |
| Reference precision | bf16 forward of the initial model | the same engine forward with the adapter disabled; fp32 log-softmax (R: `engine.py:218-245`) | exact Δ = 0 at step 1 (§5.3) |
| Max length | 512 (C) | 3,072 (rows over it excluded; R: `textproc.py:181-182`) | none for β (only t ≤ 5 is special) |
| Rounds | 3 | 6 seeds (RS A9) | — |

### 3.4 Why the decision is defensible, and what it costs
- **For it.** It isolates the loss: recipe G already carries a warmup-and-decay schedule, and our `bt` run puts G's reduction on its schedule (FOCUS:198). A 10-step warmup has no faithful transfer to a 38-step run (FQ5).
- **Against it (I).** It is the weakest form of the method (FQ3). The paper's own benign evidence for the loss alone is one dataset of three (FQ2). A reviewer may call the arm a strawman. So the arm must be named and described as "Qi et al.'s token-wise constrained loss on recipe B (no warmup)", with the deviation table, and never as "Qi et al.'s method".

---

## 4. Proposed B+Qi settings for the stage-1 pre-registration

| Item | Proposed value | Source or reason |
|---|---|---|
| Name | "B+Qi: recipe B with Qi et al.'s token-wise constrained loss, no warmup" | FOCUS:125, :148; paper draft decision 22 |
| Base recipe | the stage-1 arm recipe (recipe S's training identity) with only `train.loss` and the new constraint key changed | R: recipe S config; "isolates the loss" |
| π_aligned | OLMo-2-0425-1B-Instruct `48d788ec…`, the LoRA base with the adapter disabled | P §4.1; R config `model` |
| Reference log-probs | computed online in each micro-batch, under no gradient, with the adapter disabled (§5.3) | I: exact, resume-safe, cheap |
| Positions t | t = 1 is the first response token after `<\|assistant\|>\n`; the end-of-turn `<\|endoftext\|>` is the last t | R: `textproc.py:173-183`; config `model.assistant_header` |
| β_t | 0.5 (t = 1); 2.0 (t = 2–5); 0.1 (t > 5); a row with n ≤ 5 targets takes the first n values | P §4.2; C `get_beta_list` |
| Token term | w_t · NLL_t with w_t = max(2σ(β_t Δ_t), 1e-3), w_t detached; Δ_t = NLL_θ,t − NLL_ref,t | C (the gradient equals P Eq. 5 apart from the floor) |
| Row loss | l_i = (1/n_i) Σ_t w_it · NLL_it | recipe B's per-example mean |
| Step objective | (1/E) Σ_i l_i over the step's actual rows | recipe B (R: `engine.py:283-302`) |
| Optimizer and schedule | recipe B: AdamW (0.9, 0.999), eps 1e-8, weight decay 0, LR 1e-4 constant, no warmup, clip 1.0 | FOCUS:125 item (10); R config |
| Data, steps | the 4,800 Dolly rows; 38 steps; one epoch; read at e1 | as a0 |
| Seeds | 6. Proposed 1101–1106, so every seed pairs with an a0 seed on the same init and data order (I: B+Qi has no scorer built on a0-1101, so the method-arm rule "never 1101" does not apply; the lead decides) | RS A9; PLAN-S §4.3 |
| Evaluation | the same as every arm (U, HB, O, task loss, ARC, opening lexicon) | PLAN-S §7 |
| Logged extras | plain per-example NLL; the weighted objective; the mean w at t = 1, t = 2–5 and t > 5; the share of floored tokens; max \|Δ\| at step 1; reference seconds | I: certificate and the binding check (§8) |
| Second family (stage 2) | the same settings; π_aligned = Llama-3.2-1B-Instruct (its LoRA base) | no base-model download (unlike Safe LoRA) |

Deviation table: §3.3 holds every row (SPEC §9 template).

---

## 5. Mapping to the engine (`experiments/safety_selection`)

### 5.1 Where recipe B's loss lives today (R)
- **Config.** Recipe B has no `train.loss_weighting` key, so the objective is the per-example mean; `train.loss` must equal the fixed text `LOSS` (`config.py:102-103`; validation `config.py:529-541`). The only optional weighting is `"token_mean"` (`config.py:33-36`, `:539-540`). `train.lr_schedule` is `"constant"` (recipe S config).
- **Engine.** `_target_nll` returns each row's float32 per-target-token NLL from one right-padded forward, with chunked head recompute under gradient (`engine.py:222-245`). `example_losses` takes each row's mean (`:248-253`). `accumulate_gradients` backpropagates (Σ_i l_i)/E per micro-batch, or the token-mean variant (`:283-302`). `train_step` clips, checks finiteness and steps (`:306-325`).
- **Runner.** `_train_segment` calls `en.train_step` with the weighting (`runner.py:538-539`) and writes `steps.jsonl` with `loss`, `example_losses`, the pre-clip norm, seconds and LR (`:547-552`).
- **LoRA init.** A from the seed's stream, B zero, so the seeded model computes exactly what the base model computes (`engine.py:123-126`).
- **Identity.** A run's `identity.json` hashes every file of `safety_selection` and `minimal_safety` (R: the w0b-2 retrain unit's `identity.json`, `code_sha256`). Any engine change gives a new engine identity X′.
- **Attribution.** The attribution job assumes the plain objective when it weights rows by their share of the step (`runner.py:961-964`; `attribution.py:35`).

### 5.2 What must be built (B12)
1. **Config (`config.py`).** One new optional key, for example `train.token_constraint` = {form "qi2024-tokenwise", beta_first 0.5, beta_early 2.0, early_positions 5 (t = 2…5), beta_rest 0.1, weight_floor 0.001, reference "base model, adapter disabled"}. A new fixed `train.loss` text for it. Validation of exact values. A recipe without the key keeps its bytes, hash and meaning (the module's own rule, `config.py:12-13`). Refuse it with `model.lora.trainable_tokens` (PEFT's disable path for token rows is untested). Decide whether it may combine with `"token_mean"` (needed only for a G+Qi option; §8).
2. **Engine (`engine.py`).** A function that, per micro-batch: (a) runs `_target_nll` under `torch.no_grad()` inside the PEFT model's `disable_adapter()` context to get NLL_ref per target token; (b) runs `_target_nll` with gradient to get NLL_θ; (c) forms Δ = NLL_θ.detach() − NLL_ref, the β list by position, w = max(2σ(βΔ), floor), detached; (d) forms l_i = mean_t(w · NLL_θ) and backpropagates (Σ_i l_i)/E. `accumulate_gradients` and `train_step` gain the constraint argument and return the plain per-example NLL as `example_losses` (unchanged meaning), the weighted step objective, and the w summaries.
3. **Runner (`runner.py`).** Pass the constraint to `train_step`; add the new step fields to `steps.jsonl`; record the reference forward's seconds inside the train stage (PLAN-S §8 needs costs by stage). The attribution job refuses a recipe with the constraint (a guard and a test).
4. **Recipe file.** For example `study-kt-olmo2-1b-r64-bq-…json` (name the lead's): the stage-1 arm recipe with the two `train` changes only.
5. **Stage-1 kit (B15).** Run B+Qi as an ordinary arm job with its own recipe hash; at most 4 arms per pod (FOCUS 9 Oct item (1)).
6. **Tests.** (a) β by position, with rows of 1–5 targets and the end-of-turn token. (b) With reference = policy, Δ = 0, w = 1 and the gradient equals recipe B's (bitwise on a CPU toy model). (c) With all β near 0 (for example 1e-6), the gradient equals recipe B's at every step to tolerance. (d) With large β, the exact token loss (2/β)S(βΔ) tends to 2 · max(Δ, 0) (a helper used only in tests). (e) Raising a target token's probability lowers w. (f) The floor binds where 2σ(βΔ) < 1e-3. (g) The adapter is enabled again after the reference pass, and the reference pass creates no gradients. (h) Old recipes keep their hashes. (i) A resume reproduces the same steps.
7. **Mutants (the project's mutation-runner rule: a mutant is killed only by a real test failure; an error is an invalid run).** Δ with the wrong sign; β counted from the prompt start; β shifted by one position; w not detached; the reference computed with the adapter on (then B+Qi equals recipe B); the floor as a ceiling; the row normaliser Σw instead of n_i. (The adapter left disabled for the policy forward is already caught by the "LoRA parameters without gradients" check, `engine.py:314-316`.)
8. **Certificate X → X′ (RS D5).** The full engine test suite on X′. On one pod: (a) recipe B a0@1101 train-only on X′ reproduces X's q and e1 adapter fingerprints (as the w0b-2 retrain did on X); this keeps the Gate A a0 and Gate B R units reusable. (b) B+Qi at one seed, train-only, twice: equal fingerprints. (c) Step 1 of B+Qi on the real model: max |Δ| ≈ 0 and a gradient equal to recipe B's step 1 to tolerance.
9. **Timing.** Merge only after Gate B's last kit pod, with any other engine change, under one certificate (R: PLANF §2.4 S4–S5).

### 5.3 The reference: three ways, and the choice
- **(A) Online, per micro-batch, adapter disabled (proposed).** One extra forward per micro-batch. With B = 0 at init, PEFT's LoRA output adds an exact zero, so the step-1 policy equals the reference and Δ = 0 (I: from PEFT's LoRA forward and `engine.py:123-126`; the certificate checks it on the GPU, because kernel choice under gradient and no gradient may differ). No new artifact. Resume-safe.
- **(B) Precompute per run before step 1, in the run's own micro-batch order.** The same cost and numbers as (A). It needs a stored file per run and a resume rule. No gain.
- **(C) Precompute once per row, shared by all seeds** (the code's way). It saves about 5 × 75–110 s over 6 seeds (about 0.15 FRE in total; I). But the batch layout differs from training, so step-1 Δ is only near 0, the bitwise certificate test is lost, and a new sealed file appears. Not worth it.

---

## 6. Cost

### 6.1 Measured basis (R)
- a0 training at 4,800 rows, 38 steps: **244.7 s** (6.4 s per step), the w0b-2 retrain ledger; 245 s in Gate A's ledger (PLAN-S §1 item 6).
- Removal arms at 4,200 rows, 33 steps: training **216.0–220.4 s**; whole job slot **43.4–49.0 min** (wave 0a; recost notes). Generation (greedy plus sampled) is about 2,060–2,380 s of each.
- FRE proxy (I): the median wave-0a removal-arm slot, 48.9 min ≈ 2,935 s. The true 1 FRE is the median stage-1 R-arm time (PLAN-S §8), not measured yet.

### 6.2 Per seed
- **Reference forward (I):** forward only, no backward, no chunk recompute. A LoRA training step is about 2–3 forwards (the backward goes through every layer for the activations; the head chunks are recomputed). So the reference costs about 0.30–0.45 of the training time: **about 73–110 s per arm**.
- **C-full:** a B+Qi arm = an a0 arm + the reference ≈ the R arm + 26 s (38 against 33 steps) + 73–110 s ≈ **1.03–1.05 FRE**. Generation length moves an arm by about ±6% (43.4 to 49.0 min across wave 0a), so a single arm may read 0.97–1.11 FRE. If B+Qi keeps more refusal openings, its answers to harm prompts are shorter and its generation is cheaper (I).
- **C-lean (I):** a lean R arm ≈ 220 s training + about 230–300 s for 200 sampled answers and their judging + load ≈ 465–545 s. B+Qi adds about 100–135 s: **about 1.18–1.29 FRE** under C-lean. The measured c0 (PLAN-S §8) replaces this estimate.
- So B+Qi's extra cost over a0 is small (about 0.04–0.05 FRE under C-full). It has no scoring cost.

### 6.3 Six seeds (I)
- About 6.2–6.3 FRE ≈ 5.1 arm-hours ≈ $9.2 at $1.79/h; with two pods' overhead (≤ 26 min each, measured) ≈ $10.8; × 1.25 contingency ≈ **$13.4**. RS A9 said about $12.

### 6.4 Build and certificate (I)
- Build: config, engine, runner, recipe, tests and mutants: about 4–8 h for the builder, plus one review and fix round (RS B12 said 0.5–1.5 days; round 5's token-mean option took 1.5 h, and this change is larger).
- Certificate pod D5: overhead ≤ 26 min + three train-only jobs of about 5–7 min ≈ 45–50 min ≈ **$1.3–1.5**.

---

## 7. Predictions and risks to write before the freeze (I)
- **Q-P1 (SPEC F4, extended by FQ3).** B+Qi's erosion E lies nearer recipe B's than recipe G's. Basis: no warmup, β1 0.9, a constant peak LR, and a fit that is mostly done by step 2–3.
- **Q-P2.** If B+Qi reduces E at all, the refusal-opening drop (frozen lexicon `bbbc71e9…`) shrinks more than the unsafe share among direct answers. Basis: the constraint acts only on the first 5 answer tokens, the "opening switch" of the two-layer account (FOCUS:145).
- **Q-P3.** B+Qi's held-out task loss is above a0's; it may pass τ_L (FQ6).
- **Q-P4.** No stated direction for over-refusal O.
- **Reporting rule (unchanged).** B+Qi is a model-level reference with no novelty claim (FOCUS 8 Oct item (4)). A data repair "dominates" only if it beats the references on U, O and task loss together (FOCUS:153).

---

## 8. Options for the lead, and the smallest decisive check

| Option | What | Extra cost (I) | For | Against |
|---|---|---|---|---|
| **(a) As decided (default)** | B+Qi = recipe B + the loss, no warmup, β1 0.9; 6 seeds | — | isolates the loss on the main recipe; the user's decision | weakest form; may read as a strawman (FQ3–FQ4) |
| (b) Add G+Qi, 3 seeds, secondary | recipe G + the loss (token mean, 4-step warmup, cosine decay) | about 3.2 FRE, about $6–7; the constraint must also accept `"token_mean"` (a small change) | the closest analogue of the released code; answers the strawman objection | one more arm; G+Qi against G confounds nothing new, but it is not on the main recipe |
| (c) Faithful optimizer in (b) | (b) with `train.betas` [0.5, 0.999] | no code (betas are config values, `config.py:556-559`) | matches P A.5.1 | changes two things against G |
| (d) Add Qi's warmup to B+Qi | 10-step linear warmup on recipe B | none in code (`warmup_constant` exists) | the published schedule | reverses the user's decision; 26% of the run; confounded with G's schedule effect |

**Smallest decisive check, outcome-free (I).** In the D5 certificate run, log the mean weight w on t = 2–5 at every step. If it falls below about 0.5 by step 3, the constraint binds and B+Qi is a real test of the loss. If it stays near 1 for most of the 38 steps, B+Qi equals recipe B by construction, and the lead can drop or change the arm before the freeze without seeing U, O or task loss. The lead should state in the pre-registration that this training-only diagnostic was seen (it is a training statistic, not an outcome; I).

---

## 9. Open items

| # | Item | Default proposed | Who |
|---|---|---|---|
| 1 | B+Qi as decided (no warmup, β1 0.9, constant LR) | keep; name it as in §4; add §3.3 to the deviation table; add FQ3 to F4's prediction risk | User (FYI; 9 Oct item (10) stands) |
| 2 | A faithful secondary (G+Qi, 3 seeds) | offer it; the user decides; if yes, build the token-mean path now | User |
| 3 | B+Qi seeds | 1101–1106, paired with a0 | Lead |
| 4 | Weight floor | 1e-3, as the code | Lead |
| 5 | The binding check in D5 (§8) | log w; decide before the freeze | Lead |
| 6 | Record corrections (FQ7) | FOCUS:70 and the paper draft: "Table 9" → "Table 5 (arXiv v1)"; CITE-CHECK 25's term | Lead (FOCUS); the FAQ chat (paper) |
| 7 | The ICLR 2025 camera-ready may change tables or settings | read it before citing table numbers (I did not open OpenReview; the brief allows arxiv.org) | Lead |

---

## 10. Process

- **Commands run (all exit 0):** `date -u` (three times); `git branch`, `git log`, `git rev-parse` on the main checkout (read-only); `grep`, `sed`, `wc`, `ls`, `find`, `shasum` on the records and code named above; `python3 -I` reads of the recipe JSON files, the wave-0a and w0b-2 ledgers and the w0b-2 retrain's `steps.jsonl` and `identity.json`; `python3 -I` arithmetic for the weight table, the momentum shares and the costs; `curl` to stdout of the GitHub API (tree listing, commit, licence) and of five raw files of the official repository (README, `finetune.py`, `trainer/trainer.py` parts, `models/model_families/llama2.py` parts, `datasets/utils/get_finetuning_data.py` parts), piped to `grep` or `sed`; `mkdir -p` of this folder.
- **Web reads:** the arXiv abstract page; the arXiv HTML through the fetch tool (a summary, used only for the section list); the arXiv PDF through the fetch tool, which cached it in this session's tool-results folder; I read pp. 1–11 and 16–25 as page images.
- **Files written:** this file only. Another worker's files in this folder (`tau_l_check.py`, `tau_l_check.out.json`) were not opened or changed.
- **Not done:** no code; no test run; no pod; no OpenReview or ICLR page; no check of the installed PEFT version's `disable_adapter` and LoRA forward (the exact-zero argument in §5.3 is from PEFT's design; the certificate checks it); no reading of pp. 12–15 (references).
- **Limits:** costs marked (I) rest on three removal arms and one retrain; the reference-forward share (0.30–0.45 of training) is an estimate, measured in D5. The code reading covers the files named; the HF default decay is inferred, not run.
