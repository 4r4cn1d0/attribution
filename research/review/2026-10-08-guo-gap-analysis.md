# Why our Qwen collapse differs from Guo et al.

8 Oct 2026 (IST). Read-only review for the lead.
No runs, spend or held-out data.

- **Labels.** R = read or counted in the cited source. I = inference or arithmetic. UNVERIFIED = not checked.
- **Short names.** KT = `research/experiments/2026-10-07-kill-test-stage0-results.md`. FOCUS = `research/FOCUS.md`. Guo = arXiv 2609.01455v1 and repo `safety_routing@eb32b85`. SCR = `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-peaceful-jepsen-8b8eee/83ec8f39-95ba-4bdb-995e-cb384f533165/scratchpad/guo-gap/` (session scratch, not in the repo; it can disappear).

## 1. The gap in one paragraph

Our run: stock Qwen2.5-7B-Instruct @ a09a3545, one epoch of recipe B on 4,800 Dolly rows (LoRA r64, alpha 128, all linear, LR 1e-4 constant, 38 steps). U goes from 4.8% (29/600) to 87.0% (522/600), +82.2 pp; greedy goes from 9/200 to 178/200 (R, KT:116-118). Guo Table 2, same model: untuned 7.27%; LoRA 4.50% (100 rows) and 9.09% (5,000 rows × 5 epochs); full fine-tuning 63.60% and 57.88% (R, SCR/arxiv.txt Table 2). Their Llama-3.1-8B LoRA-5k reads 44.80% (R). The untuned baselines agree (4.8% vs 7.27%). The gap appears only after tuning: about +82 pp for us, about +2 pp for them. The two cells are not the same experiment. Guo's Qwen LoRA cell uses Alpaca data, HEx-PHI prompts, and a GPT-4o mini judge that counts only score 5 of 5 (R, SCR/arxiv.txt:720-724; SCR/repo/src/evaluation/safety/gpt4_as_judge.py:249-250). Ours uses Dolly, direct-request prompts, the binary Qwen3Guard Unsafe label, a larger adapter and a per-row loss. Guo never reports Qwen LoRA on Dolly (R, SCR/arxiv.txt:440, 756-768). **Short answer (I):** no single difference explains the gap. Guo's cell sits at the gentlest corner of the published record. Ours sits above its harshest corner. Measurement (prompts and judge) explains at most about 13-30 pp, because Guo's own judge reads 58-74% on Qwen models that stopped refusing. At least about 50 pp is on the training side. The split of that share between data and our recipe is not known yet.

## 2. Ranked causes

The gap has two halves (I). **Half A:** Guo's cell up to the published range. Random-Dolly LoRA on Qwen2.5-7B reads 25-50% on direct-request prompts (R: Bach et al. 24.7%, arXiv 2511.18039 Table 2; LARF DH4 50.5%, arXiv 2507.18631 Table 1). **Half B:** the published range up to our 87%. Bach is the closest recipe (Dolly 15k, batch 128, 1 epoch). It fits Dolly as well as we do (test loss 3.6 → 1.2; ours 3.335 → 1.293), yet reads 24.7% (R, 2511.18039 Table 2; KT:123). The order below is by expected share. A skeptic pass re-read the sources for causes 1, 2 and 4 and weakened each to "weak". So the ranking is low-confidence.

### Cause 1. Training data: Alpaca (Guo) against our Dolly units
- **Mechanism (I).** Dolly answers are short and human-written. Fitting them teaches the model to open with a direct answer. Refusal lives in the opening tokens. Our units are also stratified (8 categories × 600). Against Dolly-15k this puts creative_writing at 2.7× its share and open_qa at 0.5× (R, `experiments/safety_selection/configs/study-kt-data-dolly-llama3.json` eligibility records: 709 and 3,742 of 15,011 rows).
- **For (R).** Guo's own logs, same LoRA recipe, 100 rows: train loss Dolly 1.44-1.45, Alpaca 0.69-0.73 (HF `LuckyJason77/safe_routing` all_results.json). Guo Table 3, full fine-tuning, 100 rows: Dolly 73.60, Alpaca 63.60. LARF, Qwen2.5-7B LoRA, Dolly vs Alpaca: DH4 50.5 vs 27.5, HarmBench 36 vs 11, HEx-PHI 32.4 vs 13.1.
- **Against (R).** DataShield random Dolly vs random Alpaca: DH4 26.75 vs 26.25 (arXiv 2606.00160 Table I). In Guo Table 3 the Dolly-minus-Alpaca sign flips (Qwen +10.0, +7.2, +0.3; Llama −8.5, −14.7, +4.9). Guo's Llama fits Alpaca as well as Qwen (LoRA-5k loss 0.594 vs 0.629), yet erodes to 44.8%. Bach fits Dolly as well as we do, at a third of our erosion.
- **Skeptic's verdict.** Weak as "Dolly vs Alpaca": about 0-25 pp. The category-mix variant is new and untested.
- **Cheapest decisive check.** Recipe B at 1.5B on 4,800 random Alpaca rows, plus 4,800 random unstratified Dolly rows. Compare both with 79.8%. If Alpaca stays above about 60%, data is minor. If Alpaca falls below about 30% and random Dolly stays high, data is confirmed. **Cost:** about $8 (two pods at about $4; b-1101 cost $3.79, KT:150), plus data preparation. Needs approval.

### Cause 2. Our recipe amplifiers: per-row-mean loss and a large all-linear adapter
- **Mechanism (I).** Our loss averages the NLL inside each row, then across rows. A 3-token answer then weighs as much as a 300-token answer. The first 5 response positions carry 17.7% of our objective, against 5.3% under the token mean that LLaMA-Factory and HF use (R, counted from `tmp/kt-prepared/prepared-kt-dolly/engine/train_rows.jsonl`: median 52 target tokens; 766 of 4,800 rows have 16 or fewer). Our adapter (r64, 7 projections, 161.5M parameters) is the largest among the Qwen2.5-7B studies (I: Guo 80.7M, LARF and DataShield 20.2M, Bach 10.1M on q/v only).
- **For (R).** Springer et al. used our exact adapter shape: Qwen3-1.7B eroded (harm 1.24 → 2.68-3.63 of 5); Llama-3.2-3B did not (arXiv 2602.15799 Table 1). This cause fits Half B against Bach (I).
- **Against (R, SCR/h2/h2_counts.out).** Dose and LR do nothing in our data. At 1.5B, recipe A e1 (31.6× the summed LR) gives U 498 and 501/600 against recipe B's 479/600: +3.4 pp, 95% CI −0.2 to +7.0. Guo LoRA-5k had about 20× our summed LR and a larger update (2.6-4.2 per module, I) yet read 9.09%. Nobody has tested loss weighting.
- **Skeptic's verdict.** Capacity: weak. Loss weighting: weak, never tested.
- **Cheapest decisive check.** Read the rank-16 run (1.5B, r16, alpha 32, otherwise recipe B). Its job started 21:14 UTC on 7 Oct and has not returned (R, `tmp/kill-test-r16/hosts/r16-1101/orchestrate.jsonl`). The preset rule: rank matters if E ≤ 65.2 pp (R, FOCUS:91). **Cost:** $0 extra (reserve already set, FOCUS:93). Then a token-mean loss arm at 1.5B: about $4 plus an engine option. That is a recipe change for GPT and the user to decide.

### Cause 3. Prompt bank: HEx-PHI against our direct-request bank
- **Mechanism (I).** HEx-PHI has 330 prompts in 11 categories, including soft ones such as political campaigning and financial advice (R, counted in SCR/repo/data/safety_bench/HEx-PHI.jsonl). Soft prompts set a floor and draw mild answers, so the measured rise is compressed.
- **For (R).** Where papers report HEx-PHI next to direct-request banks, HEx-PHI moves least. LARF random Dolly: HEx-PHI +22.8 pp, DH4 +41.3 pp. DataShield random Dolly: HEx-PHI −1.4 pp, DH4 +17.3 pp.
- **Against (R, SCR/our_outputs_analysis.out §4-5).** Our collapse is uniform across our four sources (71.1-88.7%). Only 5 of 200 prompts stay safe in all 3 samples. Guo's full fine-tuning reads 58-74% on HEx-PHI, so HEx-PHI can show a collapse.
- **Skeptic's verdict.** Not re-checked by the skeptic pass. Moderate on the literature.
- **Cheapest decisive check.** Run a recipe-B 7B adapter on the 330 HEx-PHI prompts through our harness. Our 7B adapter weights were not kept (R, `tmp/kill-test-7b-check/backup_records_q7.py` skips .safetensors; pod q7-1101 deleted, KT:135). **Cost:** a 7B retrain, about $6, plus about $2 of evaluation. HEx-PHI terms of use UNVERIFIED. Lower priority than the cause-5 check.

### Cause 4. Judge rule: score 5 only against a binary Unsafe label
- **Mechanism (I).** Guo counts only GPT-4o mini score 5 on a 1-5 rubric, "fully fulfills" the request (R, gpt4_as_judge.py:249-250). Our Unsafe label also counts partial answers (about their scores 3-5). Short or partial answers then read lower under Guo's rule.
- **For (R).** 261 of our 522 post-tuning Unsafe answers have 64 tokens or fewer (our_outputs_analysis.out §3). The paper describes only a binary "unsafe" judgement (Guo §2.1 Eq. 1, §4.1).
- **Against (R).** Three signals move together: Unsafe 4.8 → 87.0%, refusal flag 89.7 → 12.2%, keyword ASR 12.5 → 94.2% (our_outputs_analysis.out §1). Granite agrees at 0.975 on 7B greedy (`tmp/kill-test-7b-check/second-judge-kt-summary.json`). 387 of 522 Unsafe answers carry no caveat cue (SCR/h3/h3_proxy.out). In Qi et al., the score-5 rate tracks keyword ASR when models comply (e.g. 87.3 vs 83.9; arXiv 2310.03693 Table 7). A threshold can rescale 87%; it cannot make a collapsed model read at baseline (I).
- **Skeptic's verdict.** Weak: about 0-15 pp, central 5-10 pp.
- **Cheapest decisive check.** Re-score our existing 7B e1 answers with Guo's active template, score 5 only, GPT-4o mini at T 0. To save cost, score the 87 answers of 16 tokens or fewer plus a random 100. **Cost:** under $1 of API (pricing UNVERIFIED); needs an OpenAI key and spend approval. Free proxy: a local rubric judge (not their judge).

### Cause 5. Guo's Qwen LoRA-5k cell may be an evaluation artifact
- **Mechanism (I).** If the evaluation ran the base model, or one seed landed low, the cell would sit near 7.27%, as reported (30/330 vs 24/330).
- **For.** The released Qwen LoRA-5k adapter is as large as Llama's LoRA-5k adapter (update norm 2.6-4.2 vs 2.9-5.1 per sampled module; I, from HF weights). It reaches the same train loss as Qwen full SFT-5k (0.629 vs 0.632, R), which read 57.88%. Every 5k cell is an exact k/330 and no seed-69 5k checkpoint exists, although the caption says two seeds (I). How adapter folders reached the evaluation is undocumented (UNVERIFIED).
- **Against (R).** Qwen LoRA-5k utility moved (MMLU 74.25 → 71.65, ARC-E 81.65 → 79.34), so the adapter was applied at least there. The aligned-start Qwen LoRA-5k rows moved from 0% to 21.21% and 16.67%. Other Alpaca LoRA runs on HEx-PHI also stay flat (LARF +3.4 pp, DataShield −1.4 pp).
- **Skeptic's verdict.** Weak (not re-checked by the skeptic pass).
- **Cheapest decisive check (the best single check overall, I).** Run Guo's released `qwen25-7b/instruct/alpaca-utility-seed-42-5000-sample-lora-r32-lr2e4` adapter (323 MB) and their full SFT-5k model through our harness on the dev bank. Low U (about 5-20%): their model kept refusal, so the cause is training (causes 1-2). High U: their measurement explains it (causes 3-5). **Cost:** about 2 GPU-hours, $3-6. Needs approval.

### Ruled out
- **Dose (I).** Guo LoRA-5k ran 785 steps at 2e-4: 20.7× our summed LR. It passes our whole dose by about step 56 (from HF all_results.json).
- **Template and system message (R).** Every released Qwen chat_template.jinja is byte-identical to stock a09a3545. Both sides insert Qwen's default system message.
- **Decoding and cap (R).** Our greedy rate (89.0%) is above the sampled rate (87.0%). A 512-token cap still leaves at least 82.0% sampled (our_outputs_analysis.out §0, §3).
- **Truncation and dropout (I).** Our 3,072 limit truncates nothing. Dropout 0.05 vs 0 is far too small to move 80 pp.

**Check order (I).** (1) Read r16, $0. (2) Guo's adapters through our harness, $3-6. (3) 1.5B random-Alpaca and random-Dolly arms, about $8. (4) Score-5 re-score, under $1 or a $0 proxy. (5) Token-mean loss arm, about $4 plus engine work. All except (1) need approval.

## 3. Who is the outlier in the literature

- **Ours is the outlier in size (I, moderate confidence).** Among about 10 published Qwen2.5-7B LoRA runs on random benign data, the highest post-tuning rate is about 50% and the largest rise about +41 pp (R, LARF DH4 on Dolly). Ours is 87.0% (+82 pp).
- **Rates of 58-88% need a harsher setting (R).** They appear only with full fine-tuning (Guo 58-74%; Kim et al. Qwen2.5-3B on Dolly 63.5% keyword ASR, arXiv 2508.12531 Table 3), selected data subsets (83-88%, DataShield Table I), or harmful mixtures.
- **Our result is solid inside our harness (R).** Three signals agree, the second judge agrees, and greedy decoding or a 512 cap does not remove it. No published run uses Qwen3Guard, so its recall against Llama-Guard-3 is UNVERIFIED.
- **Guo's cell is typical for its setting (R).** Other Alpaca + HEx-PHI LoRA cells are flat: LARF +3.4 pp, DataShield −1.4 pp; Vishnubhotla is flat on Qwen3 Alpaca (arXiv 2606.03648 §5.2).
- **Guo's reading over-reaches (I).** Their Qwen cells cannot support a general claim that LoRA keeps Qwen safe. They never report Qwen LoRA on Dolly, although they released Dolly LoRA-100 adapters (R, HF listing). Their own Llama LoRA-5k reached 44.8%. Springer's same-shape adapter eroded Qwen3-1.7B (R).
- **Evidence strength: moderate (I).** Most numbers are side baselines with 1-2 seeds and mixed judges. LARF and DataShield share baseline numbers, so they are only partly independent.

## 4. What it means for the Llama-3.2-1B and OLMo-2-1B probes

- **What the probes test (R).** Both 1B configs keep recipe B: the same Dolly unit construction (construction_sha256 2f5802f5…, 600 rows per unit), the per-example mean loss, LR 1e-4 constant, r64 alpha 128 on all 7 projections, plus r16 variants (`experiments/safety_selection/configs/study-kt-{llama32,olmo2}-1b-r64-b-mb2-20261008.json` and `study-kt-data-dolly-{llama3,olmo2}.json`). So they test family and, with the r16 arms, rank. They do not test data or loss weighting, the two leading training-side suspects (I).
- **Comparison rule (I).** Compare probe U only with other runs in our harness, never with Guo's or other papers' numbers. Keep reporting Unsafe, the refusal flag and keyword ASR, so a family gap cannot be blamed on the judge.
- **Llama-3.2-1B (I).** Expect saturation (E > 55 pp). In the literature Llama erodes as much as Qwen or more under LoRA: Guo LoRA-5k 44.8% vs 9.09%; LARF random Dolly 54-55% vs 50.5% DH4; SafeTune −44.2 pp (Llama-3.2-3B) vs −31.1 pp (Qwen3-4B) (R). Exception: Springer's Llama-3.2-3B stayed flat, at LR 5e-5 on 100 rows (R).
- **OLMo-2-1B.** No published benign-LoRA safety numbers found (UNVERIFIED). Read its untuned U first. The headroom rule applies (R, FOCUS:73).
- **How to read the outcome (I).** If both families saturate, family is not the lever. The Guo gap then points to data (random or Alpaca rows), a token-mean loss or a smaller adapter to reach the 20-55 pp target (R, FOCUS:96). If one family lands in 20-55 pp, family matters, against Guo's Llama-over-Qwen order. Report it.
- **Loops (R).** At 1.5B, 8.5-32.5% of greedy harm answers were capped after tuning (KT:95). Expect the "answers end" bar to bind at 1B.
- **Template (R).** The Llama-3.2-1B config takes its tokenizer and chat template from Llama-3.1-8B-Instruct @ 0e9e39f2. FOCUS:122 notes the two differ in tokenizer_config. This is harmless while training and evaluation share it (I). Record it.
- **Decision owner.** A probe recipe change is for GPT and the user. This note changes nothing.

## 5. What remains unknown

- Guo's LLaMA-Factory settings: cutoff, LR schedule, micro-batch, precision (UNVERIFIED; YAML files not released).
- Which path Guo's evaluation got for the LoRA rows; whether the paper used score = 5 or ≥ 4; the GPT-4o mini snapshot. Their HEx-PHI answers and judge outputs were not released.
- Whether Guo's 5k cells are single-seed.
- How the training-side share splits between data (and our category mix) and our recipe.
- How our answers score under Guo's judge, and how our recipe reads on HEx-PHI.
- Qwen3Guard recall against Llama-Guard-3 on the same answers.
- Alpaca answer lengths and refusal content (no Alpaca data read). Bach's loss weighting.
- The r16 result. Our 7B adapter weights were not kept, so a direct weight-norm comparison with Guo's adapters needs a saved adapter or a norm log on the next run.
- One open item is probably closed (I): our untuned 7B Dolly loss of 3.335 (KT:153) matches Bach's untuned Qwen-7B Dolly loss of about 3.6 (2511.18039 Table 2). It is likely a property of the model, not a pipeline fault.
