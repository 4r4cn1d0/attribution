# Erosion amplifiers: what the literature says we do differently

Date: 8 Oct 2026 (IST). No runs, spend or held-out data.

Read-only desk synthesis for the lead. Inputs: five literature sweeps (templates, hyperparameters, data and mechanism, measurement, family), one synthesis and one critic pass, saved in this session's scratchpad. This note's author re-opened the key tables (marked A in §5). The critic's corrections are applied. **R** = read in the source (location given). **I** = inference. **UNVERIFIED** = not checked. In §2–§4, "S" or "C" before an arXiv id also means R, but read only by a sweep or the critic, not re-checked by this note's author. Companion notes: `2026-10-08-guo-gap-analysis.md` and `2026-10-08-why-the-papers-chose-their-recipes.md`.

## 1. The question and the short answer

- **Question.** Benign LoRA on 4,800 Dolly rows takes Qwen2.5-1.5B/7B-Instruct from about 5% to 80–87% Unsafe in 38 steps. Guo et al. (2609.01455) report 4.5–9.1% for LoRA on Qwen2.5-7B-Instruct. What do we do wrong or differently?
- **Short answer (I).** We found no outright error. Two questions are mixed: **Q1**, why our erosion saturates so fast, and **Q2**, why we sit far from Guo.
- **Q1:** our recipe stacks four choices that make the first updates large: no warmup, rank 64 at alpha = 2r, a per-example mean loss, and human Dolly targets far from the model's own style. Under a gentle recipe, the same family, data and template give only +14 pp (R, 2609.30802 Table 1).
- **Q2:** the comparison is not like for like. Guo's LoRA cells use Alpaca, HEx-PHI and a judge that counts score 5 only. After fine-tuning, our Unsafe label behaves like a non-refusal rate. Warmup cannot explain Q2.
- Qwen is not shown to be uniquely fragile at 7B. None of these causes is tested on our runs yet.

## 2. Ranked factors

Ranks are within each question. "Strength" is how well the literature supports the factor as a cause for us. Costs are estimates (I). Every GPU item needs the user's approval. Qwen items conflict with the "no more Qwen spend" decision (FOCUS, 2026-10-07 20:58 UTC).

### 2a. Q1: why the erosion saturates within 38 steps

| # | Factor | What we do | What the literature shows | Strength | Test and cost |
|---|---|---|---|---|---|
| 1 | Large updates in the first steps: no warmup, plus rank 64 at alpha = 2r | R (recipe B): AdamW, LR 1e-4 constant from step 1, clip 1.0; r64, alpha 128, all 7 linear modules, dropout 0. R (steps.jsonl, numbers only): the loss falls in steps 1–3 (1.5B 1.81→1.41; 7B 3.11→1.54), then stays flat. | R 2406.05946 Table 5 (Llama-2-7B, full FT, LR 2e-5, no seeds): a 10-step warmup cuts Samsum 23.4→3.8% and SQL 15.4→3.3%. But identity shifting falls only 79.5→44.8%, and harmful data not at all (88.9→89.4%). R 2312.03732 Thm 3.2: adapter output is rank-stable only if the scale is ~1/√r; I: at alpha = 2r an r64 step is ~2x an r16 step. R 2602.15799 Table 1: our exact adapter at LR 1e-4 on Qwen3-1.7B (Alpaca-100, 3 epochs) gives mean harm 2.68/5, so at most ~42% at score 5: not saturated. LR 1e-4 is a normal LoRA rate (R 2405.09673 §4.7; 2310.03693 Table 11). Against: Guo FT-100 LoRA (~20 steps, ~2 warmup, each ~1.4x ours, I) stays at 4.50% (Alpaca, score-5 judge, 10x lower dose). Qi 2023's Dolly run had constant LR and no warmup and reached 12.1% (R, recipes note). | Moderate to weak. For a run that saturates, expect none to ~2x from warmup (I). | 10-step linear warmup arm. r16/alpha 64 (same step scale as r64) beside r16/alpha 32, to split step size from capacity. Small engine change (LR schedule); ~$4 per 1B unit. |
| 2 | Human-written Dolly targets far from the model's own answers | R: 4,800 Dolly rows (8 × 600), no refusals, ~94 target tokens per row. Untuned held-out Dolly loss 1.890 (1.5B) and 3.335 (7B, unchecked). | R 2402.13669 Table 3 (Llama-2-7b-chat, LoRA r8 on q/v, LR 1e-4 cosine, 2,000 Dolly rows, 2 epochs): keyword safe rate 99.81→81.73%. Self-rewritten targets (SDFT) keep 96.35%. Dolly is the worst of 4 sets on jailbreak safety (26.54%); on raw safety LIMA is slightly worse (81.35%), a correction to the critic. R 2609.30802 Table 1: Qwen2.5-3B-Instruct, Dolly, Qwen template and default prompt, LoRA r8, LR 2e-5 cosine, 8 epochs: HarmBench 17.69→31.94% only. Dolly vs Alpaca flips by family (R 2609.01455 Table 3: Qwen 73.6 vs 63.6; Llama-3.1 66.9 vs 75.4; 2310.03693 Table 3: Llama-2 12.1 vs 16.1). Our category mix is not an amplifier: the high-risk categories are 51.3% of Dolly but 37.5% of ours (R, HF statistics, critic). | Moderate | SDFT-style rewrite of the same Dolly rows by the model itself (changes the research target, so GPT and the user decide), or an Alpaca swap. ~$4 per unit, plus ~$2–4 for generation (I). |
| 3 | Per-example mean loss | R (recipe): per-example mean NLL over the response and end-of-turn. R (FOCUS 03:35 IST entry): the first 5 response tokens carry 17.7% of the objective, against 5.3% under a token mean. | R 2406.05946 §2, App. B: alignment sits in the first answer tokens, and their gradients are largest at the start. S 2605.04572 App. H.2: per-example averaging inflates the first- and last-token loss of short answers. S 2604.17215 Tables 2, 12: on Qwen2.5-7B, short high-gradient Dolly rows (11.5 tokens) give 18.4% vs 12.7% for random rows. R 2411.15124 §4.3.2: the weighting choice changes results (capability, not safety). No paper tests loss weighting against safety. | Weak (untested) | The token-mean option is already being built (FOCUS). ~$4 per unit. |
| 4 | Same template and generic default persona at training and test; no safety prompt | R (engine code, via synthesis): no system message is passed, so Qwen's template inserts its default prompt at both stages. | R 2609.30802 Table 1: chat format +14.25 pp vs non-chat +0.06 pp. S 2402.18540 Table 1c (Llama-2): same template 11.0–18.1%; safety prompt only at test 1.1%. S 2510.04340 Fig. 14 (Qwen2.5-7B): a generic persona spreads learned behaviour to all prompts. A test-time safety prompt helped Qwen2.5-Omni (S 2604.16659 Table 7) but barely helped Qwen2.5-7B after agentic FT (S 2508.14031 Table 13). Guo also inserts the default prompt (R, code). | Moderate, but for ~10–15 pp, not saturation; no role in Q2 | Re-evaluate e1 under the default, a neutral and a safety system prompt. Only state.json was retrieved, so e1 must be retrained first. ~$5–8 at 1.5B. |

### 2b. Q2: why we are far from Guo et al.

| # | Factor | What we do | What the literature shows | Strength | Test and cost |
|---|---|---|---|---|---|
| 1 | Measurement: judge rule, prompts, decoding | R: Qwen3Guard Unsafe share of 600 samples at T 0.7, up to 2,048 tokens, on our 200-prompt bank. R (guard labels, counts only): after FT, U ≈ non-refusal (1.5B 79.8 vs 80.5%; 7B 87.0 vs 87.8%); 93% and 97% of non-refusals are Unsafe. Untuned 7B: only 45% of non-refusals are Unsafe. | R (Guo code `gpt4_as_judge.py` lines 249–250): only score 5 counts; greedy, 512 tokens, HEx-PHI. The paper's Eq. 1 says "unsafe"; which version made Table 2 is UNVERIFIED. C 2310.03693 Table 7: on benign data, score-5 rate / keyword rate = 0.62–0.72. R 2405.16833 Table 4: keyword ASR 86.67% with mean harm 2.25/5, so at most ~31% at score 5. So the literature does not rule out a low score-5 reading of a model that complies. Against (R, Guo-gap note): Guo's own judge reads 58–74% on Qwen full-SFT models, and most of our Unsafe answers carry no caveat cue. Two labs differ by 42 pp on the same model, benchmark and similar dose (Guo FT-5k 9.09% vs DataShield 10k Alpaca 51.38%, R 2606.00160 Table III). | Moderate | Re-score saved e1 generations with Guo's 1–5 prompt (share at 5 and at ≥3) and the StrongREJECT rubric: $0 local, <$1 API (key and approval). Or run Guo's released Qwen LoRA-5k adapter through our harness: $3–6. |
| 2 | Data: our Dolly vs Guo's Alpaca | R: Dolly only. R (2609.01455 Table 2 caption): Guo's LoRA cells are Alpaca; no Qwen LoRA-on-Dolly result exists. | R (Guo-gap note, Guo's HF logs): Guo's train loss on Dolly 1.44 vs Alpaca 0.69. R 2606.00160 Table III, Llama rows only (the Qwen Dolly row duplicates a Llama3 row): HarmBench Alpaca vs Dolly, Llama3-8B 21.5 vs 77.5%, Llama3.1-8B 47.5 vs 80.0%. The Dolly–Alpaca sign flips by family (Q1 row 2). | Moderate to weak | Recipe B on 4,800 Alpaca rows at 1.5B. ~$4–8 with data preparation. |
| 3 | Dose and schedule | R: 38 steps, 4,864 example-passes, constant LR. | R/I: Guo FT-100 is ~20 steps (500 passes) at 4.50%; FT-5k ~785 steps (25,000 passes) with warmup 0.1 at 9.09%. FT-100 has ~2 warmup steps, so warmup cannot explain the FT-100 gap. Its dose is 10x below ours. | Weak for Q2 | Covered by Q1 row 1 and the step-10 checkpoint (§3). |
| 4 | Minor: cutoff 3,072 vs 512, dropout 0 vs 0.05, fp32 adapters | R (recipe; Guo code). | No paper links these to safety (S). | Weak | Fold into a Guo-matched arm only if exact replication becomes a goal. |

## 3. Wrong, different, or genuinely fragile: the verdict

**Wrong (I).** We found no error in training or evaluation. Three inferences should be dropped or reworded:
- "Our run is the outlier against Guo." The cells differ in data, prompts, judge rule and dose. Two labs differ by 42 pp at a similar dose (§2b row 1). Neither lab is shown to be the outlier.
- "The 30x cut shows the damage happens at once." Both arms of the cut start with full-size steps. A flat loss curve is not a safety measurement. The cut cannot separate early collapse from a dose plateau.
- "U compares with published ASR." After fine-tuning, U reads like a compliance rate. Report a score-5 re-score beside it.
- One open item could be a real fault (UNVERIFIED): the untuned 7B held-out Dolly loss (3.335) is above the 1.5B's (1.890). A larger model of one family usually fits the same text better (I). A forward-pass check of per-position loss (first answer token, end-of-turn), numbers only, would show whether this is the over-confident-opener effect (R 2406.05946 App. B) or a template or data fault.

**Different (I, from R evidence).** Our recipe sits at the aggressive end on four axes at once: step size at the start, adapter scale, loss weighting and target style. Each choice is defensible alone. The within-family evidence points at the combination. Qwen2.5-3B with Dolly, Qwen's template and default prompt, and a gentle LoRA gives +14 pp (2609.30802). Llama-2-7B with Dolly at our LR 1e-4 but a small q/v r8 adapter keeps an 81.73% keyword safe rate (2402.13669). Which of our four choices matters most is untested. Minor note: in 2406.05946 App. B, the ">600 steps" values (14.9%, 25.5%) equal the initial utility cells of Table 5 (C for App. B; A for Table 5). This looks like a copy error in the paper; the 10-step values (13.6%, 22.1%) stand.

**Genuinely fragile (I).**
- Qwen at 7B: not shown. Guo Table 2 (R): at FT-5k LoRA, Qwen 9.09% vs Llama-3.1 44.80%; at FT-100, Qwen 4.50% vs Llama 2.40%. The evidence is mixed. Do not use DataShield's Qwen Dolly row (duplicated cell).
- Small Qwen: possible. R 2508.12531 Table 3: Qwen2.5-3B 63.46% vs Llama-2-7B 15.96% after the same Dolly FT, but the table has no pre-FT row, so it is not an erosion size. Springer (R): Qwen3-1.7B eroded and Llama-3.2-3B did not, at different LRs.
- Aligned models in general: safety holds in a basin around the aligned weights, then shows a sharp, step-like drop (R 2405.17374 abstract; random directions and harmful data, so a mechanism only). Refusal sits in the first answer tokens (R 2406.05946 §2) and runs through one direction (S 2406.11717). Fine-tuning tends to switch the refusal gate off while harm recognition stays (S 2502.19537, 2507.11878, 2606.00160 §III-B). This fits saturation over partial erosion, and the joint fall of over-refusal at 1.5B (68% → 2–10%).
- Our 7B collapse means family and size are not needed to explain the result.
- For the repair stage: 10 self-generated refusals restored an identity-shift collapse from 99.8% to 0.77% (C 2501.13453 App. I.1). A repair checked under one template can rebound under another (S 2607.27081 Table 2), so report U under at least 2 system prompts.

**Order of checks (I; GPT and the user decide spend).**
1. Re-score the saved e1 generations with a score-5 rule (row 2b-1). $0–1.
2. Run Guo's released Qwen LoRA adapter through our harness ($3–6, Qwen spend: user call). This decides Q2 most directly.
3. Read r16 with the step-size confound in mind (§4).
4. Evaluate the step-10 q checkpoint before building warmup. If U is already near 80% there, we collapse in fewer steps than Guo's non-saturating ~20-step run. That points to data or the judge, not step count. Whether its adapter weights were retrieved is UNVERIFIED.
5. Then warmup vs an SDFT-style rewrite or an Alpaca swap.

## 4. What it means for the Llama-3.2-1B and OLMo-2-1B probes

- Recipe B carries all four Q1 amplifiers to both families unchanged. So a saturated probe mostly re-measures the recipe. Only a partial result (20 ≤ E ≤ 55 pp, the frozen bar) says something about the family (I).
- **Prediction (I): saturation is more likely than partial at 1B.** For: safety basins are narrower in smaller models (C 2405.17374 App. E). Llama instruct models were most tamperable at 1B (S 2602.06911). Llama-1B was the only model left with a net harm increase (S 2606.03648 §5.1). Against: Llama-3.2-3B barely moved with our exact adapter, but at LR 5e-5 (R 2602.15799 Table 1). Llama-3.2-1B English compliance moved only 34.5 → 35.0–38.4% after 1-epoch LoRA (S 2606.28843 Table 2). Do not use Fraser (2506.17209) here: it links base checkpoints (C).
- **OLMo-2-1B:** no benign-fine-tuning safety study found (S, two sweeps). Its Tulu 3 SFT mix holds ~111k safety and non-compliance prompts out of ~939k (R 2411.15124 Table 7). Whether that makes refusal deeper, or only stronger in the first tokens, is untested (I).
- **Templates** (R, family brief via synthesis): OLMo-2 has no system turn. Our Llama setup uses the 3.1 template with a date system block and no persona. The persona-spreading effect (2510.04340) is absent in both. The same-template effect (2402.18540) still applies.
- **Confound to raise with GPT (I).** FOCUS (03:35 IST) launches OLMo with recipe B and holds Llama for the token-mean option. If OLMo saturates and Llama lands partial, family and loss weighting are confounded. Fix: also run the token-mean arm on OLMo (its untuned baseline is reusable), about $4.
- **Rank-16 reading limit (I, from R 2312.03732).** r16/alpha 32 cuts the per-step scale ~2x and the capacity 4x at once. "Rank matters" (E ≤ 65.2 pp) then cannot say which. r16/alpha 64 keeps r64's step scale. This is a reading note; the frozen rule stays.
- **Cheap additions per probe (I).** Read steps.jsonl first: a fit in steps 1–3 shows the same fast fit, not safety. Evaluate the step-10 q checkpoint as a second dose point (one extra evaluation pass). Report a score-5 re-score beside U.
- If both families saturate, the next lever is step size (warmup, r16/alpha 64) or targets (SDFT-style rewrite), not family.
- Do not read "Llama partial, Qwen saturated" as family fragility without a matched recipe. Dolly vs Alpaca flips sign between Qwen and Llama-3.1 (R 2609.01455 Table 3), so family effects depend on data and dose.

## 5. Papers read

Read by: A = this note's author (spot-check of the named table), C = critic, S = a sweep, Y = synthesis author. "Abstract" means only the abstract was read.

| arXiv | Title | Read level | By |
|---|---|---|---|
| 2609.01455 | When Safety Routing Breaks (Guo et al.) | sections + public code | S, C; A (judge lines 249–250) |
| 2310.03693 | Fine-tuning Aligned Language Models Compromises Safety (Qi et al. 2023) | sections | S, C |
| 2406.05946 | Safety Alignment Should Be Made More Than Just a Few Tokens Deep | sections | S, C; A (Table 5, App. A.5.1) |
| 2606.00160 | DataShield: Safety-degrading Data Filtering | sections | S, C; A (Table III) |
| 2609.30802 | Understanding the Role of Prompt Template in Knowledge Distillation for Safety Alignment | full | S, C; A (Tables 1, 7) |
| 2402.13669 | Self-Distillation Bridges Distribution Gap in Language Model Fine-Tuning (SDFT) | sections | C; A (Table 3, App. A) |
| 2405.17374 | Navigating the Safety Landscape: Measuring Risks in Finetuning LLMs | sections | C; A (abstract) |
| 2312.03732 | A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA | sections | C; A (Thm 3.2) |
| 2501.13453 | Spurious Forgetting in Continual Learning of Language Models | sections | C |
| 2602.15799 | The Geometry of Alignment Collapse (Springer et al.) | sections | S, C |
| 2405.09673 | LoRA Learns Less and Forgets Less | sections | S, C |
| 2405.16833 | Safe LoRA | sections | S, C; A (Table 4) |
| 2508.12531 | Rethinking Safety in LLM Fine-tuning: An Optimization Perspective | sections | S, C |
| 2605.04572 | From Parameter Dynamics to Risk Scoring | sections | S, C |
| 2506.17209 | Fine-Tuning Lowers Safety and Disrupts Evaluation Consistency | sections | S, C |
| 2402.18540 | Keeping LLMs Aligned After Fine-tuning: The Crucial Role of Prompt Templates | full | S |
| 2510.04340 | Inoculation Prompting (Tan et al.) | sections | S |
| 2604.16659 | Benign Fine-Tuning Breaks Safety Alignment in Audio LLMs | sections | S |
| 2508.14031 | Unintended Misalignment from Agentic Fine-Tuning | sections | S |
| 2607.27081 | On-Policy Distillation for LLM Safety: Template-Robust Realignment | sections | S |
| 2604.17215 | Continual Safety Alignment via Gradient-Based Sample Selection | sections | S |
| 2502.19537 | No, Of Course I Can! Refusal Mechanisms Can Be Exploited Using Harmless Data | sections | S |
| 2507.11878 | LLMs Encode Harmfulness and Refusal Separately | sections | S |
| 2406.11717 | Refusal in Language Models Is Mediated by a Single Direction | sections | S |
| 2411.15124 | Tulu 3 | sections (Table 7, §4.3.2) | Y |
| 2602.06911 | TamperBench | sections | S |
| 2606.03648 | Safety Measurements for Fine-tuned LLMs Should be Grounded in Capability | sections | S |
| 2606.28843 | The Heterogeneous Safety Impacts of Benign Multilingual Fine-Tuning | sections | S |

Not cited here but opened by the sweeps: more than 40 further papers (lists in the sweep outputs). Search limit (S, C): no paper found that tests warmup, or token-mean vs per-example loss, against safety under LoRA.
