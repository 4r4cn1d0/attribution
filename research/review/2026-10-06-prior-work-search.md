# Prior-work search: has this study been done, and what must we cite?

6 October 2026 (IST). Written by General Implementation, from web and arXiv searches and arXiv abstract pages read on this date. Each paper's details are taken from its abstract or arXiv HTML page, not from a full reading. Read the full paper before citing a specific number.

## 1. Verdict

**Not as we frame it, as far as this search finds.** The parts exist separately:
- attribution that finds unsafe training data, compared with moderation classifiers;
- attribution-guided rewriting;
- attribution benchmarks against simple baselines;
- compute-aware data selection.

We found no study that does all of the following:
- compares attribution with strong cheap selectors (a classifier, short training runs and metadata) as a **decision** among a menu of safety edits (remove, rewrite, add);
- charges each selector's compute at a **matched budget**;
- accounts for **training-seed** variance;
- freezes the choice rule and confirms the choice on **held-out** data;
- reports when the evidence is too weak to choose.

**Limits of this search:**
- It used web search and arXiv. Very recent papers (September–October 2026) and work outside arXiv may be missing.
- Repeat the search before submitting.

## 2. The closest prior work (must cite; read in full)

| Paper | What it does | What it does not do, relative to us |
|---|---|---|
| **Pan, Shi, Zhao and Ma, "Detecting and Filtering Unsafe Training Data via Data Attribution with Denoised Representation"**, [arXiv 2502.11411](https://arxiv.org/abs/2502.11411) (2025; ICML 2026 poster) | **The closest.** Training sets are UltraChat with unsafe ToxicChat and XSTest-Response data injected. Models are Llama-3-8B-Instruct and Gemma-2-9B-it. Attribution (DRA, GradSim, RepSim) is compared with moderation classifiers (OpenAI Moderation, Llama-Guard-3-8B, WildGuard) and GradSafe. They remove the top-K rows, retrain, and measure attack success rate on official test splits. Attribution removal improves safety more in their homogeneous setting. | It reports no compute or cost comparison. It tests removal only, with no rewriting or adding. Its variance is 10 inference runs, not training seeds. It has no short-run or metadata selectors and no decision rule. |
| **Luo, Wang, Chen and Pan, "From Reweighting to Rewriting: Unlocking the Intervention Effects of Influential Samples in Training Data Attribution"**, [arXiv 2609.02771](https://arxiv.org/abs/2609.02771) (September 2026) | Attribution-guided rewriting. Rewriting moves behaviour far more than reweighting or deletion. See our [precedent note](2026-10-05-rewriting-precedent.md). | It does not count selection compute or compare with strong cheap selectors. It states no seed counts. |
| **Hu et al., "GradShield: Alignment Preserving Finetuning"**, [arXiv 2605.14194](https://arxiv.org/abs/2605.14194) (May 2026) | A gradient-based harmfulness score for each fine-tuning row, with adaptive thresholding before training. Attack success rate stays below 6%. | Filtering only. Check whether it compares at matched compute. |
| **Jiao et al., "DATE-LM: Benchmarking Data Attribution Evaluation for Large Language Models"**, [arXiv 2507.09424](https://arxiv.org/abs/2507.09424) (NeurIPS 2025 Datasets and Benchmarks) | Benchmarks attribution on data selection, toxicity and bias filtering, and factual attribution. "No single method dominates", and attribution methods "have trade-offs with simpler baselines". **Our training data (ToxicChat-Het) comes from DATE-LM.** | It scores attribution quality on each task, not decisions with costs charged. |
| **Li, Zhao, Li and Sun, "Do Influence Functions Work on Large Language Models?"**, [arXiv 2409.19998](https://arxiv.org/abs/2409.19998) (2024) | Influence functions "consistently perform poorly", including at harmful-data identification. | Motivates our question. It has no edit decisions. |
| **He, Xia and Henderson, "What is in Your Safe Data? Identifying Benign Data that Breaks Safety"**, [arXiv 2404.01099](https://arxiv.org/abs/2404.01099) (2024) | Gradient and representation matching finds benign rows that break safety: 100 such rows give over 70% unsafe answers, against under 20% for random rows. | Selection for attack or analysis, not a cost-charged choice among fixes. |
| **Coalson, Bae, Carlini and Hong, "IF-Guide: Influence Function-Guided Detoxification of LLMs"**, [arXiv 2506.01790](https://arxiv.org/abs/2506.01790) (NeurIPS 2025) | Token-level influence finds toxic training tokens and suppresses them. It finds that standard record-level influence is ineffective. It uses a small proxy model to save compute. | A detox method, not a decision study. |

### 2a. Already in our earlier notes (FOCUS.md and the [2 October precedent note](2026-10-02-new-safety-attribution-precedent.md)); must cite

- **Weckbecker et al., "Can Data Attribution Filter Out Subliminal Learning? Not Reliably"**, [arXiv 2609.20027](https://arxiv.org/abs/2609.20027), September 2026. Attribution-based filtering helps inconsistently.
- **"Mitigating Emergent Misalignment with Data Attribution"**, [OpenReview](https://openreview.net/forum?id=gN7pWmjiQW), NeurIPS 2025 Mechanistic Interpretability Workshop. Influence-based filtering and retraining.
- **"Where Did It Go Wrong? Attributing Undesirable LLM Behaviors via Representation Gradient Tracing"**, [arXiv 2510.02334](https://arxiv.org/abs/2510.02334), 2025.
- **Bae et al., "Training Data Attribution via Approximate Unrolled Differentiation"** (SOURCE), [arXiv 2405.12186](https://arxiv.org/abs/2405.12186), 2024.
- **"Distributional Training Data Attribution: What do Influence Functions Sample?"**, [arXiv 2506.12965](https://arxiv.org/abs/2506.12965), 2025. Attribution inherits training randomness, which matters for our seed design.
- **Ouyang et al., "ADMIRE-BayesOpt: Accelerated Data MIxture RE-weighting for Language Models with Bayesian Optimization"**, [arXiv 2508.11551](https://arxiv.org/abs/2508.11551), TMLR 2025. The multi-fidelity selector named in FOCUS.md.

## 3. Data filtering and selection for fine-tuning safety (cite as related work)

- **Li et al., "Layer-Aware Representation Filtering: Purifying Finetuning Data to Preserve LLM Safety Alignment"** (LARF), [arXiv 2507.18631](https://arxiv.org/abs/2507.18631), 2025.
- **Zhang et al., "DataShield: Safety-degrading Data Filtering for LLM Benign Instruction Fine-Tuning"**, [arXiv 2606.00160](https://arxiv.org/abs/2606.00160), May 2026.
- **Guan et al., "Benign Samples Matter! Fine-tuning On Outlier Benign Samples Severely Breaks Safety"**, [arXiv 2505.06843](https://arxiv.org/abs/2505.06843), 2025.
- **Shen, Chen, Das and Chen, "SEAL: Safety-enhanced Aligned LLM Fine-tuning via Bilevel Data Selection"**, [arXiv 2410.07471](https://arxiv.org/abs/2410.07471), ICLR 2025.
- **Yang et al., "Self-Distillation Bridges Distribution Gap in Language Model Fine-Tuning"** (SDFT), [arXiv 2402.13669](https://arxiv.org/abs/2402.13669), ACL 2024. The model rewrites the fine-tuning responses, which preserves safety. A precedent for rewrite edits.
- **O'Brien et al., "Deep Ignorance: Filtering Pretraining Data Builds Tamper-Resistant Safeguards into Open-Weight LLMs"**, [arXiv 2508.06601](https://arxiv.org/abs/2508.06601), 2025. Cheap filtering of pretraining data is a strong safety intervention.
- **Dixit, "Filtering Harmful Actions Isn't Enough: Phantom Transfer in Agentic Synthetic-Data-Fine-Tuning"**, [arXiv 2607.10750](https://arxiv.org/abs/2607.10750), July 2026 (single-author preprint). Filtering, and even regeneration, leaves some transferred misalignment.

## 4. Data selection with compute in view (cite for the matched-compute framing)

- **Ivison et al., "Large-Scale Data Selection for Instruction Tuning"**, [arXiv 2503.01807](https://arxiv.org/abs/2503.01807), 2025. Many recent methods fall short of random selection while using more compute. A representation baseline (RDS+) is best and cheaper.
- **Magnusson et al., "DataDecide: How to Predict Best Pretraining Data with Small Experiments"**, [arXiv 2504.11393](https://arxiv.org/abs/2504.11393), ICML 2025. "Decision accuracy" of small runs, and a compute–decision frontier. This is the precedent for **short runs as a selector** and for decision-level evaluation.
- **Nautiyal, "Attribution Without a Second Pass: Inline Per-Sample Gradient Provenance at ~1% Overhead"**, [arXiv 2609.32380](https://arxiv.org/abs/2609.32380), September 2026 (single-author preprint). It claims gradient attribution can be logged during training at about 1% overhead. **This is a risk to our "attribution is expensive" premise:** our accounting must charge the measured cost of whichever method is used.

## 5. Training-data attribution methods and critiques (cite for the methods)

- **Koh and Liang, "Understanding Black-box Predictions via Influence Functions"**, [arXiv 1703.04730](https://arxiv.org/abs/1703.04730), ICML 2017.
- **Pruthi et al., "Estimating Training Data Influence by Tracing Gradient Descent"** (TracIn), [arXiv 2002.08484](https://arxiv.org/abs/2002.08484), NeurIPS 2020.
- **Ilyas et al., "Datamodels: Predicting Predictions from Training Data"**, [arXiv 2202.00622](https://arxiv.org/abs/2202.00622), ICML 2022.
- **Park et al., "TRAK: Attributing Model Behavior at Scale"**, [arXiv 2303.14186](https://arxiv.org/abs/2303.14186), ICML 2023.
- **Grosse et al., "Studying Large Language Model Generalization with Influence Functions"**, [arXiv 2308.03296](https://arxiv.org/abs/2308.03296), 2023 (EK-FAC at LLM scale).
- **Xia et al., "LESS: Selecting Influential Data for Targeted Instruction Tuning"**, [arXiv 2402.04333](https://arxiv.org/abs/2402.04333), ICML 2024.
- **Choe et al., "What is Your Data Worth to GPT? LLM-Scale Data Valuation with Influence Functions"** (LoGra), [arXiv 2405.13954](https://arxiv.org/abs/2405.13954), 2024.
- **Basu, Pope and Feizi, "Influence Functions in Deep Learning Are Fragile"**, [arXiv 2006.14651](https://arxiv.org/abs/2006.14651), ICLR 2021.
- **Bae et al., "If Influence Functions are the Answer, Then What is the Question?"**, [arXiv 2209.05364](https://arxiv.org/abs/2209.05364), NeurIPS 2022.
- **Cheng, Bae, Bullock and Kristofferson, "Training Data Attribution (TDA): Examining Its Adoption & Use Cases"**, [arXiv 2501.12642](https://arxiv.org/abs/2501.12642), 2025. A report on practical use; it frames our "is it worth it?" question.

## 6. Harmful fine-tuning and contamination (cite for the setting and v2)

- **Qi et al., "Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!"**, [arXiv 2310.03693](https://arxiv.org/abs/2310.03693), ICLR 2024.
- **Yang et al., "Shadow Alignment: The Ease of Subverting Safely-Aligned Language Models"**, [arXiv 2310.02949](https://arxiv.org/abs/2310.02949), 2023.
- **Bianchi et al., "Safety-Tuned LLaMAs: Lessons From Improving the Safety of Large Language Models that Follow Instructions"**, [arXiv 2309.07875](https://arxiv.org/abs/2309.07875), ICLR 2024.
- **Huang et al., "Harmful Fine-tuning Attacks and Defenses for Large Language Models: A Survey"**, [arXiv 2409.18169](https://arxiv.org/abs/2409.18169), 2024.
- **Betley et al., "Emergent Misalignment: Narrow finetuning can produce broadly misaligned LLMs"**, [arXiv 2502.17424](https://arxiv.org/abs/2502.17424), ICML 2025. Relevant to v2: narrow harmful data, broad harm measured.
- **Souly et al., "Poisoning Attacks on LLMs Require a Near-constant Number of Poison Samples"**, [arXiv 2510.07192](https://arxiv.org/abs/2510.07192), 2025. Relevant to the injection dose.

## 7. Evaluation variance (cite for the seed design)

- **Fraser, Dawkins, Nejadgholi and Kiritchenko, "Fine-Tuning Lowers Safety and Disrupts Evaluation Consistency"**, [arXiv 2506.17209](https://arxiv.org/abs/2506.17209), 2025.
- **Larsen, "The Instability of Safety: How Random Seeds and Temperature Expose Inconsistent LLM Refusal Behavior"**, [arXiv 2512.12066](https://arxiv.org/abs/2512.12066), 2025.

## 8. Resources used (cite in the methods)

- **Data:**
  - DATE-LM (above);
  - **ToxicChat**, [arXiv 2310.17389](https://arxiv.org/abs/2310.17389);
  - **UltraChat**, [arXiv 2305.14233](https://arxiv.org/abs/2305.14233);
  - **PKU-SafeRLHF**, [arXiv 2406.15513](https://arxiv.org/abs/2406.15513).
- **Evaluation:**
  - **HarmBench**, [arXiv 2402.04249](https://arxiv.org/abs/2402.04249);
  - **StrongREJECT**, [arXiv 2402.10260](https://arxiv.org/abs/2402.10260);
  - **SimpleSafetyTests**, [arXiv 2311.08370](https://arxiv.org/abs/2311.08370);
  - **XSTest**, [arXiv 2308.01263](https://arxiv.org/abs/2308.01263);
  - **OR-Bench**, [arXiv 2405.20947](https://arxiv.org/abs/2405.20947);
  - **ARC**, [arXiv 1803.05457](https://arxiv.org/abs/1803.05457).
- **Models and judges:**
  - **Qwen2.5**, [arXiv 2412.15115](https://arxiv.org/abs/2412.15115) (the policy and the rewrite writer);
  - **Qwen3Guard**, [arXiv 2510.14276](https://arxiv.org/abs/2510.14276);
  - **Granite Guardian**, [arXiv 2412.07724](https://arxiv.org/abs/2412.07724);
  - **LoRA**, [arXiv 2106.09685](https://arxiv.org/abs/2106.09685).

## 8a. Reading order (54 papers; the same order as the Chrome tabs opened on 6 October)

1. **Read first: the closest work.** Pan et al. (DRA); Luo et al.; Weckbecker et al.; Mitigating Emergent Misalignment with Data Attribution; GradShield; DATE-LM.
2. **Why attribution's value is in doubt.** Li et al. (influence functions on LLMs); Ivison et al.; Cheng et al. (TDA use cases); IF-Guide.
3. **Our framing: decisions under a compute budget.** DataDecide; ADMIRE-BayesOpt; Nautiyal (inline attribution); Distributional TDA.
4. **Attribution methods; skim, then read the ones we use.** Koh and Liang; TracIn; Datamodels; TRAK; Grosse et al.; LESS; LoGra; SOURCE; Where Did It Go Wrong?; Basu et al.; Bae et al.
5. **Safety fine-tuning background.** Qi et al.; Shadow Alignment; Safety-Tuned LLaMAs; the harmful fine-tuning survey; He et al.; Benign Samples Matter; LARF; DataShield; SEAL; SDFT; Deep Ignorance; Emergent Misalignment; Souly et al.; Phantom Transfer.
6. **Measurement and seed noise.** Fraser et al.; Larsen.
7. **Resources; cite only.** ToxicChat; UltraChat; PKU-SafeRLHF; HarmBench; StrongREJECT; SimpleSafetyTests; XSTest; OR-Bench; ARC; Qwen2.5; Qwen3Guard; Granite Guardian; LoRA.

## 9. What this means for our claim

- **State the gap precisely.** Pan et al. already show that attribution can beat moderation classifiers at *removing* unsafe data, in nearly our setting. Our new question: does that advantage survive the following?
  - charging compute at a matched budget;
  - strong cheap selectors that include short runs and metadata;
  - training-seed variance;
  - a menu of edits that includes rewriting;
  - held-out confirmation with a frozen choice rule.

  Our study is a stress test of claims like theirs.
- **Do not claim** rewriting, attribution-guided selection, or "attribution beats classifiers" as new (Luo et al.; Pan et al.; GradShield).
- **Watch the cost side.** If inline attribution really costs about 1% (Nautiyal 2026), matched compute favours attribution. The study must use measured costs, not assumed ones.
- **Possible extra baseline:** Pan et al.'s DRA and RepSim are cheap representation methods. They may belong among the "cheap selectors" or among the attribution arms. Decide this before the decision study is frozen.
