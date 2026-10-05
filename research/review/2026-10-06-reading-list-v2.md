# Reading list v2: data fixes for benign fine-tuning erosion, and what diagnosis is worth

6 October 2026 (IST). Written by an Opus 5.5 worker at the user's request. It covers the **proposed** reframed question, which is not yet adopted. This is read-only research: this file is the only change, and nothing was committed.

> **Proposed question.** When fine-tuning on benign data makes an aligned model less safe, which data fix restores safety without hurting the task or causing over-refusal (keep the data; remove a subset or source; add safety data; rewrite or self-distill responses)? How much diagnosis is worth paying for before choosing: classifier scores, representation similarity, gradient attribution or influence functions, or short trial runs?

**How this was checked.**
- 17 web searches and 22 page reads, all on 6 October 2026.
- **Metadata.** Every arXiv paper below was checked against arXiv's own metadata through the arXiv export API, which serves the same title, authors, date and comments as the abstract page. Batch calls covered about 160 IDs, and every listed ID resolved to the expected title.
- **Venues.** A venue comes from the arXiv comment field when the comment states one. Otherwise it comes from Semantic Scholar's venue field, marked "(S2)". Earlier project notes supply a few, as marked.
- **Full texts.** Nine papers were read in full through a fetch tool that summarizes the page with a small model. The survey's HTML was read directly as text. Treat every number from these reads as "reported", and check it in the PDF before citing it.
- The section "What could not be verified" lists everything else.

---

## Novelty verdict (Task 1)

### Verdict

**The reframed question is still novel as a combination, but its novelty is narrower than before.**

- No paper found compares **data** fixes of different types (keep, remove, add, rewrite) for safety erosion from benign fine-tuning in one design.
- No paper found charges diagnosis cost against extra trial runs, or reports results as a function of the ratio between diagnosis cost and run cost.
- No paper found evaluates fixes at the **decision level**: choose one fix by a frozen rule, then confirm it on held-out menus with fresh training seeds, with over-refusal and task skill as hard limits.
- Each part exists separately. Since the positioning review, two parts moved from "not found" to "partly done":
  - **Comparing fixes for safety drift** on safety, capability and over-refusal, with costs and a guide for choosing. This is SafeTune (August 2026), and it covers model-level fixes only.
  - **Comparing ways to add safety data**, with over-refusal measured. This is DataRx (August 2026).
- **The least-covered part is the co-primary hypothesis**: predicting a fix's over-refusal before training. The nearest precedent is persona vectors, which flag training data that will shift a trait.

**Single closest work: Xiao and Aranguri, [arXiv 2602.11079](https://arxiv.org/abs/2602.11079).**
- It is the only paper found that does both of the following:
  - it prices several diagnosis methods for one safety failure caused by training data;
  - it applies more than one data fix (filtering, label switching, removal by source).
- It does not use trial runs as a rival. It does not match compute, does not add data, does not use training seeds or held-out decisions, and does not study erosion from benign fine-tuning.

**Closest on choosing a fix: SafeTune, [arXiv 2609.22153](https://arxiv.org/abs/2609.22153).** From its title alone, it is the paper a reviewer is most likely to cite as "this was done".

### The closest works, and what each one lacks

| Work | What overlaps with the reframed question | What it lacks |
|---|---|---|
| **Xiao and Aranguri** [2602.11079](https://arxiv.org/abs/2602.11079) (2026) | Probe attribution is reported as more than 10 times cheaper than gradient attribution and an LLM judge. Fixes: filtering (−63%), label switching (−78%) and removal by source. Dollar costs per method (about $30, $320 and $500; from a search snippet). | No trial-run rival; no matched compute; no add fix; no training seeds; no held-out decisions. The failure comes from post-training data, not a user's benign fine-tune. |
| **SafeTune**, Seth et al. [2609.22153](https://arxiv.org/abs/2609.22153) (Aug 2026) | Unifies four repair paradigms: post-hoc weight recovery, safety-constrained fine-tuning, unlearning, and inference-time steering. Fine-tuning domains: math, code, Dolly, medical, legal. Measures safety, capability and over-refusal (OR-Bench Hard-1k). Reports wall-clock time per paradigm (recovery in under a minute; constrained fine-tuning 1–3 h). Gives a guide to choosing a fix. | **Data fixes are excluded by design.** No diagnosis arm; no matched compute. One deterministic run per method (one seed, greedy decoding). "Feasible" means access (training control, editable weights), not limits on over-refusal or task skill. |
| **DataShield**, Zhang et al. [2606.00160](https://arxiv.org/abs/2606.00160) (May 2026) | A filter for benign-erosion rows. Its Table IV gives scoring cost for 10,000 Alpaca rows: LARF 0.17 h, DataShield 0.50 h, bi-anchoring 3.5 h, GradSafe 6.5 h, SEAL 40 h. Baselines: a guard model, LARF, bi-anchoring, SEAL, GradSafe and random rows. | Cost is never charged against runs. Removal is the only fix. Over-refusal is not measured. No training seeds (the random baseline is averaged over 3 draws). |
| **GradShield**, Hu et al. [2605.14194](https://arxiv.org/abs/2605.14194) (May 2026) | The filter threshold is set to meet a safety tolerance and a utility tolerance: the nearest precedent for frozen feasibility limits. Scoring adds about 25% overhead. 5 seeds on Identity-Shift. Baselines include LlamaGuard and OpenAI Moderation. | No over-refusal measure; no matched compute; removal is the only fix; single runs outside Identity-Shift. |
| **DataRx**, Zhang et al. [2608.04322](https://arxiv.org/abs/2608.04322) (Aug 2026) | Chooses which safety rows to add. It compares random mixing, paraphrased and self-distilled safety data, and several selectors. It sweeps the task-to-safety ratio (about 50:1 to 1000:1) and measures XSTest over-refusal with Qwen3Guard-Gen-8B. Safety gains come with more over-refusal. | No remove fix; no cost; no training seeds; no decision rule. |
| **Luo et al.** [2609.02771](https://arxiv.org/abs/2609.02771) (Sep 2026) | Rewriting beats deletion and reweighting for influence-selected rows. Safety rewriting worsened XSTest over-refusal. | No cost; no seeds; no cheap selectors (see the [precedent note](2026-10-05-rewriting-precedent.md)). |
| **Pan et al.** [2502.11411](https://arxiv.org/abs/2502.11411) (2025; ICML 2026 per earlier notes) | Attribution beats moderation classifiers at removing injected unsafe rows. | One training run; no cost; removal only; injected data, not erosion from benign data. This is our anchor case. |
| **Vishnubhotla et al.** [2606.03648](https://arxiv.org/abs/2606.03648) (Jun 2026) | Argues that "[anchoring fine-tuning to a specific capability goal is essential](https://arxiv.org/abs/2606.03648)" for comparing mitigations. Shows that judges misrate incoherent outputs, and that conclusions change with the benchmark and the judge. | Compares one mitigation (SafeLoRA). No cost and no seeds. Its safety set has no over-refusal test. |

### What each paper reports on cost, decisions, over-refusal and seeds

Rows are papers read in full in this pass unless marked.

| Work | Fixes compared | Cost reported | Cost charged against runs, or compute matched | Trial-run rival | Decision rule with limits | Over-refusal measured | Training seeds |
|---|---|---|---|---|---|---|---|
| SafeTune | about 50 model-level repairs | wall-clock per method | no | no | qualitative, by access | yes (OR-Bench Hard-1k) | 1 |
| Xiao and Aranguri (earlier notes) | filtering, label switching, removal by source | dollars, H100-hours | no | no | no | not checked | not checked |
| DataShield 2606.00160 | removal | scoring hours (Table IV) | no | no | no | no | none stated |
| GradShield | removal | about 25% overhead | no | no | threshold meets safety and utility tolerances | no | 5 (one task) |
| DataRx | adding (7 ways) | no | no | no | no | yes (XSTest) | none stated |
| Safety at One Shot [2601.01887](https://arxiv.org/abs/2601.01887) | a one-example patch against 7 defenses | GPU-hours (0.02 h for the patch; 1.33–2.45 h for two baselines) | no | no | no | no benchmark | none stated |
| SafeTuneBed [2506.00676](https://arxiv.org/abs/2506.00676) | LoRA, Lisa, Vaccine, SafeLoRA | about 200 GPU-hours in total | no | no | no | no | 3 |
| Cross-risk [2510.07968](https://arxiv.org/abs/2510.07968) | 13 defenses × 9 risks | no | a benign control with matched learning rate, steps and batch size | no | no | yes (exaggerated safety) | 5 runs (seed type unclear) |
| Luo et al. (earlier note) | deletion, reweighting, rewriting | not stated | no | no | no | yes (XSTest) | not stated |
| Pan et al. (earlier notes) | removal | no | no | no | no | not checked | 1 training run |

**Training-time defenses** (Vaccine, Lisa, Booster, Antidote, SafeLoRA, safety-layer freezing, PTST) were verified on arXiv but not read in full. No search result showed any of them compared at matched compute or against extra runs. The survey, SafeTuneBed and SafeTune re-run several of them, and none of those three matches compute. Search snippets show that this family reports overhead as clock time and GPU memory (for example 0.05 h for Surgery and 0.20 h for Antibody).

**The closest things to "trial runs as diagnosis"** all differ from our use:
- ForgetFilter and SQSD score rows with signals taken from a training run. They work at the row level and are not compared at matched cost.
- DataDecide and ADMIRE-BayesOpt use small runs, but for pretraining mixtures.
- Llama 3 chose its safety-mix ratio by repeated runs. That is a practitioner's trial-run selector, never compared with diagnosis.

### The survey's evaluation practice (arXiv 2409.18169, v6; ACM Computing Surveys, 2026)

The survey's HTML was read directly as text.
- **Metrics.** Two metrics are standard: harmful score (lower is better) and fine-tune accuracy (higher is better). They test the two goals that a defense must resist the attack and keep task performance (sections 2 and 4.2).
- **Benign tasks (its Table 6) and how they score task skill:**
  - SST2, AGNews and GSM8K: accuracy by string matching;
  - Dialogue summary (SAMSum): ROUGE-1 F1;
  - AlpacaEval and Alpaca: helpfulness from a GPT-4 judge;
  - ChatDoctor: BERTScore;
  - OpenOrca: ARC accuracy.
- **Harmful data and test prompts (its Table 5):** BeaverTails, DecodingTrust, PureBad, HEx-PHI, HH-RLHF, DirectHarm4, GSM-Danger and AdvBench.
- **Over-refusal:** the terms "over-refusal" and "false refusal" do not appear anywhere in the text.
- **Seeds:** "seed" appears only in the sense of seed papers for its literature search. There is no guidance on training seeds or variance.
- **Cost:** overhead appears only as a future direction: "[Most existing defenses increase the memory/computation overhead compared to SFT](https://arxiv.org/html/2409.18169v6)". Nothing recommends matched compute or charging a defense's cost against extra runs.
- **Its own statistics** use one model (Llama2-7B), SST2 with a harmful ratio, and one fixed small learning rate.

**Does any work charge defense cost against extra runs? None found.** Papers report cost as overhead or as scoring time. Nobody converts it into the number of runs that the same compute could have bought. Ivison et al. come nearest: they charge selection compute against training on more data, for instruction tuning, not safety.

### What could make reviewers say "this was done", and the answer to each

1. **"SafeTune already compares safety-drift fixes on safety, capability and over-refusal, with costs and a guide."**
   - Answer: it has no data fixes, no diagnosis arm, one seed and no matched compute.
   - Action: cite it prominently and state what it cannot answer.
2. **"Xiao and Aranguri already priced diagnosis and compared data fixes."**
   - Answer: it has no trial-run rival, no add fix, no seeds and no held-out decisions, and it does not study benign fine-tuning.
3. **"Adding a little safety data is known to work."** Bianchi et al. (3%), the Llama 3 mix sweeps, Eiras et al., DataRx (1%), behaviour-aware sampling (0.5%) and Safety at One Shot (one example) all show this.
   - Answer: they show that adding works on average. They do not show when it fails, what it costs in over-refusal, or whether diagnosis would choose a better fix.
   - Action: make "add a fixed small safety mix" the default arm that diagnosis must beat.
4. **"Filters already beat classifiers on benign-looking data."** DataShield, GradShield, LARF and SQSD show this.
   - Answer: they compare rankings or single filtering runs, with one seed, no cost against runs, and no over-refusal.
5. **"Hyperparameters alone fix most erosion."** Kim et al. report that better choices cut unsafe answers from 16% to about 5%.
   - Answer: include a safer training recipe under "keep the data", or show the erosion at the recipe practitioners actually use.
6. **"Compute-aware data decisions already exist."** DataDecide and Ivison et al. do this.
   - Answer: they cover pretraining or instruction tuning, with no safety and no side-effect limits.
7. **"Defense benchmarks exist."** SafeTuneBed uses 3 seeds; TamperBench sweeps hyperparameters.
   - Answer: they rank defenses on fixed metrics. They do not charge for diagnosis or choose fixes under limits.

### Risks to the reframing (beyond prior work)

1. **The erosion may be too small at our scale.**
   - Evidence:
     - SafeTuneBed's summary suggests little erosion in its benign regime (check this in the PDF);
     - Kim et al. say "poor optimization choices, rather than inherent trade-offs, often cause safety problems" ([2508.12531](https://arxiv.org/abs/2508.12531));
     - Khan et al. find that benign fine-tuning changes measured safety in ways that disagree across instruments.
   - **Smallest decisive check:** run benign LoRA fine-tunes of Qwen2.5-1.5B-Instruct on 2–3 standard tasks at a common recipe, with 3 or more seeds, and compare the safety drop with seed noise. If the drop is within the noise, the main setting fails.
2. **Cheap model-level repairs may beat every data fix.**
   - Evidence: Safety at One Shot costs about 0.02 GPU-hours; SafeTune's post-hoc recovery runs in under a minute; PTST costs nothing.
   - Action: limit the claim to users who can change only the data. Fine-tuning services that tell customers to fix the data are this case (see the problem-validation note). Alternatively, add one cheap model-level repair as a reference arm.
3. **The decision may be trivial.** If adding 1–3% safety data is always feasible and close to best, diagnosis is worth nothing. That is a valid result, but the study must be able to detect it cheaply. Run the default add arm early.
4. **Added data may hide the problem instead of removing it.**
   - Evidence: Dubiński et al. show that dilution, and benign training afterwards, can hide misalignment that returns on prompts resembling the training context ([2604.25891](https://arxiv.org/abs/2604.25891)).
   - Action: include such prompts in the held-out evaluation.
5. **Judges fail on incoherent outputs.**
   - Evidence: Vishnubhotla et al. found that models fine-tuned on restricted-format tasks (ARC, BoolQ) give incoherent answers to safety prompts, which judges can misread.
   - Action: prefer free-form tasks, or score coherence before scoring harm.
6. **The way the data are built can bias the comparison.**
   - Evidence: He et al. choose degrading rows by gradient and representation matching; Guan et al. choose them by Self-Inf-N influence.
   - Risk: if the benign-erosion data are built with a signal from the same family as a diagnosis arm, that arm has a home advantage.
   - Action: build the data another way, for example identity-shift data, NOICE-style formats, or natural task data.
7. **Over-refusal can swing widely.**
   - Evidence: López-Ávila et al. report that refusal data raised XSTest over-refusal from 2% to 74%.
   - Action: the over-refusal limit will bind often, so fix its threshold before the first run.
8. **Two papers share a name.** "DataShield" is both [2606.00160](https://arxiv.org/abs/2606.00160) and [2607.15081](https://arxiv.org/abs/2607.15081). Cite each one by its ID.

---

## Reading groups (Task 2)

**Legend:**
- **NEW** means the paper is not in the [6 October prior-work list](2026-10-06-prior-work-search.md).
- **★** means read it in full first.
- **(S2)** means the venue comes from Semantic Scholar metadata only.
- Each line gives the authors, the exact arXiv title, the arXiv ID, the year and the venue, then why the paper matters for the reframed question.

**Totals:**
- 134 entries: 98 in seven reading groups, plus 36 cite-only entries.
- Kept 59 of the 62 earlier entries, added 75, dropped 3 (see "Changes from the 6 October list").

### Group 1. Read first: the closest work (8 papers; 3 NEW)

1. ★ Xiao and Aranguri, "Probe-Based Data Attribution: Discovering and Mitigating Undesirable Behaviors in LLM Post-Training", [2602.11079](https://arxiv.org/abs/2602.11079), 2026, preprint. **The single closest work.** It prices diagnosis methods and applies three data fixes, but has no trial-run rival, no add fix and no seeds.
2. ★ **NEW** Seth et al., "SafeTune: A Unified Faithful Library for Auditing and Repairing Safety Drift in Fine-Tuned LLMs", [2609.22153](https://arxiv.org/abs/2609.22153), 2026, preprint. It compares many drift repairs after benign domain fine-tuning, with capability, over-refusal and cost. It has no data fixes and uses one seed. It is the likeliest "this was done" citation.
3. ★ Zhang et al., "DataShield: Safety-degrading Data Filtering for LLM Benign Instruction Fine-Tuning", [2606.00160](https://arxiv.org/abs/2606.00160), 2026, preprint. A benign-erosion filter whose scoring-cost table runs from 0.17 h (LARF) to 40 h (SEAL). It prices diagnosis, but never against runs.
4. ★ **NEW** Zhang et al., "DataRx: Missingness-Aware Sampling for Safer Large Language Model Task-Specific Fine-Tuning", [2608.04322](https://arxiv.org/abs/2608.04322), 2026, preprint. It chooses which safety rows to add, compares paraphrase and self-distill variants, and measures over-refusal on XSTest. This is the add fix's trade-off, measured.
5. ★ Hu et al., "GradShield: Alignment Preserving Finetuning", [2605.14194](https://arxiv.org/abs/2605.14194), 2026, preprint. Its threshold meets a safety tolerance and a utility tolerance, which is the nearest precedent for frozen feasibility limits. It uses 5 seeds on one task and measures no over-refusal.
6. **NEW** Vishnubhotla et al., "Safety Measurements for Fine-tuned LLMs Should be Grounded in Capability", [2606.03648](https://arxiv.org/abs/2606.03648), 2026, preprint. It argues that fixes must be compared at a fixed task-skill goal, and that judge or benchmark choice can flip conclusions. This supports task skill as a limit.
7. Luo et al., "From Reweighting to Rewriting: Unlocking the Intervention Effects of Influential Samples in Training Data Attribution", [2609.02771](https://arxiv.org/abs/2609.02771), 2026, preprint. Rewriting beats deletion; safety rewriting raised over-refusal. The rewrite fix is not ours to claim.
8. Pan et al., "Detecting and Filtering Unsafe Training Data via Data Attribution with Denoised Representation", [2502.11411](https://arxiv.org/abs/2502.11411), 2025, ICML 2026 (per earlier notes). Attribution beats moderation classifiers at removing injected unsafe rows. This is the anchor case: one run, no cost.

### Group 2. The problem: benign fine-tuning erodes safety, and why (12 papers; 9 NEW)

1. ★ Qi et al., "Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!", [2310.03693](https://arxiv.org/abs/2310.03693), 2023, ICLR 2024 (S2). The founding result: benign data (Alpaca, Dolly) and identity-shift data erode safety. It is also the source of HEx-PHI. It defines the main setting.
2. ★ **NEW** Kim et al., "Rethinking Safety in LLM Fine-tuning: An Optimization Perspective", [2508.12531](https://arxiv.org/abs/2508.12531), 2025, preprint. Better learning rate, batch size and steps cut unsafe answers from 16% to about 5%, and EMA keeps safety. It defines the "keep the data with a safer recipe" baseline and the headroom risk.
3. ★ **NEW** Qi et al., "Safety Alignment Should Be Made More Than Just a Few Tokens Deep", [2406.05946](https://arxiv.org/abs/2406.05946), 2024, ICLR 2025 (S2). Shallow alignment explains why a few rows can erode safety. A fine-tuning loss that constrains the first tokens is a rival fix.
4. ★ **NEW** Lyu et al., "Keeping LLMs Aligned After Fine-tuning: The Crucial Role of Prompt Templates", [2402.18540](https://arxiv.org/abs/2402.18540), 2024, NeurIPS 2024. Prompt templates decide much of the erosion on GSM8K, ChatDoctor and OpenOrca. PTST is a near-free rival fix. The paper is also the source of DirectHarm4 and GSM-Danger.
5. **NEW** Hsiung et al., "Why LLM Safety Guardrails Collapse After Fine-tuning: A Similarity Analysis Between Alignment and Fine-tuning Datasets", [2506.05346](https://arxiv.org/abs/2506.05346), 2025, ACL (S2). High similarity to the alignment data predicts erosion: a cheap dataset-level representation diagnosis.
6. **NEW** Khan et al., "Safety Drift After Fine-Tuning: Evidence from High-Stakes Domains", [2604.24902](https://arxiv.org/abs/2604.24902), 2026, preprint. Across 100 models, benign domain fine-tunes change safety in "[heterogeneous, and often contradictory](https://arxiv.org/abs/2604.24902)" ways. This is real-world evidence and a measurement warning.
7. **NEW** Halawi et al., "Covert Malicious Finetuning: Challenges in Safeguarding LLM Adaptation", [2406.20053](https://arxiv.org/abs/2406.20053), 2024, ICML (S2). Data that look harmless to monitors still teach harm. Here classifiers cannot see the cause, so deeper diagnosis could pay.
8. **NEW** Kazdan et al., "No, of Course I Can! Deeper Fine-Tuning Attacks That Bypass Token-Level Safety Mechanisms", [2502.19537](https://arxiv.org/abs/2502.19537), 2025, preprint. Harmless-looking refuse-then-comply data break safety. This gives a benign-looking construction that does not depend on an attribution method.
9. **NEW** Davies et al., "Fundamental Limitations in Pointwise Defences of LLM Finetuning APIs", [2502.14828](https://arxiv.org/abs/2502.14828), 2025, NeurIPS (S2). Row-by-row screening cannot catch attacks built from benign rows. This bounds what any row-level diagnosis can do.
10. **NEW** Arditi et al., "Refusal in Language Models Is Mediated by a Single Direction", [2406.11717](https://arxiv.org/abs/2406.11717), 2024, NeurIPS (S2). The refusal direction is the basis for cheap representation diagnostics, including predicting over-refusal.
11. Betley et al., "Emergent Misalignment: Narrow finetuning can produce broadly misaligned LLMs", [2502.17424](https://arxiv.org/abs/2502.17424), 2025, ICML 2025 for an earlier version (S2 lists Nature). Narrow fine-tuning can cause broad harm, which widens what erosion means.
12. Yang et al., "Shadow Alignment: The Ease of Subverting Safely-Aligned Language Models", [2310.02949](https://arxiv.org/abs/2310.02949), 2023, preprint. A few malicious rows subvert alignment. This is background for the overt anchor.

### Group 3. The fix menu: add, rewrite, self-distill, reframe (18 papers; 14 NEW)

**3a. Adding safety data: how much, which rows, and what it can hide**

1. ★ Bianchi et al., "Safety-Tuned LLaMAs: Lessons From Improving the Safety of Large Language Models that Follow Instructions", [2309.07875](https://arxiv.org/abs/2309.07875), 2023, ICLR 2024 (S2). About 3% safety rows (a few hundred) help, and too many cause exaggerated safety. The dose and over-refusal trade-off appears in one paper.
2. ★ **NEW** Eiras et al., "Do as I do (Safely): Mitigating Task-Specific Fine-tuning Risks in Large Language Models", [2406.10288](https://arxiv.org/abs/2406.10288), 2024, ICLR 2025. Safety data written in the task's own format restore safety. The authors call it "[more effective and efficient than existing baselines](https://arxiv.org/abs/2406.10288)". This is the strongest add arm to beat.
3. **NEW** Grattafiori et al., "The Llama 3 Herd of Models", [2407.21783](https://arxiv.org/abs/2407.21783), 2024, technical report. Meta chose the safety-mix ratio by repeated runs that trade violations against false refusals. Practitioners use trial runs for exactly this choice.
4. ★ **NEW** Dubiński et al., "Conditional misalignment: common interventions can hide emergent misalignment behind contextual triggers", [2604.25891](https://arxiv.org/abs/2604.25891), 2026, preprint. Dilution, and benign training afterwards, hide misalignment that returns on training-like prompts. Added data can mask a problem instead of fixing it.
5. **NEW** Zhang et al., "Safety at One Shot: Patching Fine-Tuned LLMs with A Single Instance", [2601.01887](https://arxiv.org/abs/2601.01887), 2026, preprint. One safety example restores safety after harmful fine-tuning, at about 0.02 GPU-hours as reported. It was not tested on benign-only erosion. This is a near-free rival.
6. **NEW** Pham et al., "Preventing Catastrophic Forgetting: Behavior-Aware Sampling for Safer Language Model Fine-Tuning", [2510.21885](https://arxiv.org/abs/2510.21885), 2025, preprint. Choosing safety rows by refusal behaviour and harm-category diversity gives up to 41% less harm with 0.5% added data. Which rows you add matters.
7. **NEW** Wang et al., "Mitigating Fine-tuning based Jailbreak Attack with Backdoor Enhanced Safety Alignment", [2402.14968](https://arxiv.org/abs/2402.14968), 2024, venue not confirmed. A few safety rows are tied to a secret prompt. This add fix also needs control of the serving prompt.
8. **NEW** Wang et al., "Persona Features Control Emergent Misalignment", [2506.19823](https://arxiv.org/abs/2506.19823), 2025, preprint. Model diffing with sparse autoencoders finds misaligned-persona features, and a few hundred benign rows restore alignment. This pairs a cheap diagnosis with an add fix.

**3b. Rewriting, self-distillation and reframing**

9. ★ Yang et al., "Self-Distillation Bridges Distribution Gap in Language Model Fine-Tuning", [2402.13669](https://arxiv.org/abs/2402.13669), 2024, ACL 2024. The model rewrites task responses in its own words and keeps helpfulness and safety. This is the baseline rewrite fix.
10. ★ **NEW** López-Ávila et al., "Safety for Whom? Boundary-Aware Self-Distillation for Controlled LLM Safety Refusal", [2609.04482](https://arxiv.org/abs/2609.04482), 2026, preprint. Refusal data raised XSTest over-refusal from 2% to 74%, and responses from the target model itself lowered it. Over-refusal side effects are large and depend on the fix.
11. **NEW** Ren et al., "I Learn Better If You Speak My Language: Understanding the Superior Performance of Fine-Tuning Large Language Models with LLM-Generated Responses", [2402.11192](https://arxiv.org/abs/2402.11192), 2024, EMNLP 2024. It explains why model-generated responses train better: the mechanism behind self-distill fixes.
12. **NEW** Fu et al., "Reducing the Safety Tax in LLM Safety Alignment with On-Policy Self-Distillation", [2605.15239](https://arxiv.org/abs/2605.15239), 2026, preprint. On-policy self-distillation for safety, aimed at the capability cost. It is a stronger self-distill variant.
13. **NEW** Manoranjan et al., "SHARD: Safe and Helpful Alignment via Self-Reframing Distillation", [2606.15517](https://arxiv.org/abs/2606.15517), 2026, EMNLP 2026. Self-reframed responses improve helpfulness while keeping safety: a rewrite that targets over-refusal.
14. **NEW** Liu et al., "Robustifying Safety-Aligned Large Language Models through Clean Data Curation", [2405.19358](https://arxiv.org/abs/2405.19358), 2024, preprint. A data-curation framework that revises training text to resist harmful fine-tuning. It is an early rewrite-type fix.
15. **NEW** Tan et al., "Inoculation Prompting: Eliciting traits from LLMs during training can suppress them at test-time", [2510.04340](https://arxiv.org/abs/2510.04340), 2025, under review at ICLR 2026. Reframing the training prompts suppresses a learned trait. This is the prompt-reframe fix.
16. **NEW** Wichers et al., "Inoculation Prompting: Instructing LLMs to misbehave at train-time improves test-time alignment", [2510.05024](https://arxiv.org/abs/2510.05024), 2025, preprint. A parallel result in the same fix family.
17. Rosser et al., "Infusion: Shaping Model Behavior by Editing Training Data via Influence Functions", [2602.09987](https://arxiv.org/abs/2602.09987), 2026, preprint. Influence-guided data edits: the attribution-heavy end of the rewrite family.
18. Dixit, "Filtering Harmful Actions Isn't Enough: Phantom Transfer in Agentic SDF", [2607.10750](https://arxiv.org/abs/2607.10750), 2026, single-author preprint. Filtering and regeneration leave some transferred misalignment, which limits both remove and rewrite fixes.

### Group 4. Diagnosis signals for the remove fix: selectors and filters (14 papers; 7 NEW)

1. ★ Jiao et al., "DATE-LM: Benchmarking Data Attribution Evaluation for Large Language Models", [2507.09424](https://arxiv.org/abs/2507.09424), 2025, NeurIPS 2025 Datasets and Benchmarks. With safety-aligned look-alikes, attribution's detection drops while classifiers hold. This is the middle case, and the source of our ToxicChat-Het data.
2. ★ He, Xia and Henderson, "What is in Your Safe Data? Identifying Benign Data that Breaks Safety", [2404.01099](https://arxiv.org/abs/2404.01099), 2024, venue not confirmed (COLM 2024 likely). Bi-anchoring finds benign rows that break safety. It is a diagnosis arm, and a construction-bias risk if it is used to build the data.
3. ★ Li et al., "Layer-Aware Representation Filtering: Purifying Finetuning Data to Preserve LLM Safety Alignment", [2507.18631](https://arxiv.org/abs/2507.18631), 2025, EMNLP (S2). A filter that uses representations only, with no gradients. It is the cheapest strong filter in DataShield's cost table.
4. Guan et al., "Benign Samples Matter! Fine-tuning On Outlier Benign Samples Severely Breaks Safety", [2505.06843](https://arxiv.org/abs/2505.06843), 2025, ICML (S2). 100 Self-Inf-N outliers from benign data break safety, and most mitigations fail. It gives both a diagnosis signal and a way to build erosion data.
5. **NEW** Wang et al., "From Parameter Dynamics to Risk Scoring : Quantifying Sample-Level Safety Degradation in LLM Fine-tuning", [2605.04572](https://arxiv.org/abs/2605.04572), 2026, ICML 2026. It scores rows by parameter drift during fine-tuning and compares with bi-anchoring, Self-Inf-N and LARF. Its signal comes from training, so it is close to a trial run.
6. **NEW** Zhao et al., "Learning and Forgetting Unsafe Examples in Large Language Models", [2312.12736](https://arxiv.org/abs/2312.12736), 2023, ICML 2024. ForgetFilter removes rows that are forgotten fast under later safety training. This is another signal like a trial run.
7. **NEW** Bach et al., "Continual Safety Alignment via Gradient-Based Sample Selection", [2604.17215](https://arxiv.org/abs/2604.17215), 2026, ACL (S2). High-gradient rows cause more drift, and filtering them preserves alignment. The gradient-norm signal is cheap.
8. **NEW** Goel et al., "Learning to Stay Safe: Adaptive Regularization Against Safety Degradation during Fine-Tuning", [2602.17546](https://arxiv.org/abs/2602.17546), 2026, preprint. It sets a judge-based critic beside an activation-based risk predictor: two diagnosis families in one paper.
9. ★ **NEW** Chen et al., "Persona Vectors: Monitoring and Controlling Character Traits in Language Models", [2507.21509](https://arxiv.org/abs/2507.21509), 2025, preprint. Activation directions predict trait shifts from training data before training. This is the nearest precedent for our co-primary hypothesis (predicting side effects).
10. **NEW** Wu et al., "DataShield: Uncovering Risky Fine-Tuning Data Across LLMs Through Consensus Subspace Alignment", [2607.15081](https://arxiv.org/abs/2607.15081), 2026, preprint. Representation subspaces shared by several aligned LLMs give a cheap signal that transfers across models. This is a different paper from 2606.00160.
11. Shen et al., "SEAL: Safety-enhanced Aligned LLM Fine-tuning via Bilevel Data Selection", [2410.07471](https://arxiv.org/abs/2410.07471), 2024, ICLR 2025 (S2). Bilevel data selection: the most expensive filter in DataShield's table (40 h).
12. **NEW** Choi et al., "Safety-Aware Fine-Tuning of Large Language Models", [2410.10014](https://arxiv.org/abs/2410.10014), 2024, NeurIPS 2024 Safe Generative AI workshop. Subspace scoring removes harmful rows. It is a simple representation baseline.
13. Weckbecker et al., "Can Data Attribution Filter Out Subliminal Learning? Not Reliably", [2609.20027](https://arxiv.org/abs/2609.20027), 2026, preprint. Attribution filtering of benign-looking trait carriers helps inconsistently over 10 seeds. This is evidence on the hard case.
14. Jaburi et al., "Mitigating Emergent Misalignment with Data Attribution", [OpenReview gN7pWmjiQW](https://openreview.net/forum?id=gN7pWmjiQW), 2025, NeurIPS 2025 Mechanistic Interpretability workshop. Attribution filtering matched or beat WildGuard on emergent misalignment.

### Group 5. Deciding under a budget, and measuring well (15 papers; 7 NEW)

1. ★ Magnusson et al., "DataDecide: How to Predict Best Pretraining Data with Small Experiments", [2504.11393](https://arxiv.org/abs/2504.11393), 2025, ICML 2025. Decision accuracy of small runs plotted against compute. It is the template for trial runs as a selector, scored at the decision level.
2. ★ Ivison et al., "Large-Scale Data Selection for Instruction Tuning", [2503.01807](https://arxiv.org/abs/2503.01807), 2025, preprint. Selection compute is charged against training on more data, and many methods lose to random. It is the nearest compute-matched precedent.
3. ★ **NEW** Dodge et al., "Fine-Tuning Pretrained Language Models: Weight Initializations, Data Orders, and Early Stopping", [2002.06305](https://arxiv.org/abs/2002.06305), 2020, preprint. Seeds swing fine-tuning results, and stopping poor runs early saves compute. This is evidence that short trial runs carry information.
4. **NEW** Dodge et al., "Show Your Work: Improved Reporting of Experimental Results", [1909.03004](https://arxiv.org/abs/1909.03004), 2019, EMNLP (S2). It reports the expected best result as a function of budget, which is the form our cost-ratio curves should take.
5. **NEW** Jamieson and Talwalkar, "Non-stochastic Best Arm Identification and Hyperparameter Optimization", [1502.07943](https://arxiv.org/abs/1502.07943), 2015, AISTATS (S2). Successive halving: the trial-run selector.
6. **NEW** Li et al., "Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization", [1603.06560](https://arxiv.org/abs/1603.06560), 2016, JMLR 2018. Budgeted successive halving across brackets, useful as a sensitivity check for the trial-run arm.
7. Cheng et al., "Training Data Attribution (TDA): Examining Its Adoption & Use Cases", [2501.12642](https://arxiv.org/abs/2501.12642), 2025, report. Attribution costs about as much as pretraining but is plausible for fine-tuning now. It frames the question "is diagnosis worth it?".
8. **NEW** Goyal et al., "Scaling Laws for Data Filtering -- Data Curation cannot be Compute Agnostic", [2404.07177](https://arxiv.org/abs/2404.07177), 2024, CVPR 2024. The best filter depends on the compute budget, which supports reporting by cost ratio.
9. Chen et al., "ADMIRE-BayesOpt: Accelerated Data MIxture RE-weighting for Language Models with Bayesian Optimization", [2508.11551](https://arxiv.org/abs/2508.11551), 2025, TMLR (S2). Multi-fidelity mixture selection is an alternative trial-run selector. (The first author is corrected; see the last section.)
10. Na et al., "Scalable Data Ablation Approximations for Language Models through Modular Training and Merging", [2410.15661](https://arxiv.org/abs/2410.15661), 2024, EMNLP 2024. It estimates removals by training on parts of the data and merging. This is a cheap substitute for trial runs.
11. **NEW** Khaddaj et al., "Small-to-Large Generalization: Data Influences Models Consistently Across Scale", [2505.16260](https://arxiv.org/abs/2505.16260), 2025, ICLR 2025. Small models predict data effects on larger ones. This supports the 1.5B-to-7B check and proxy diagnosis.
12. Nautiyal, "Attribution Without a Second Pass: Inline Per-Sample Gradient Provenance at ~1% Overhead", [2609.32380](https://arxiv.org/abs/2609.32380), 2026, single-author preprint. It claims near-free gradient provenance: the low-price end of attribution.
13. Fraser et al., "Fine-Tuning Lowers Safety and Disrupts Evaluation Consistency", [2506.17209](https://arxiv.org/abs/2506.17209), 2025, LLMSEC 2025 workshop. Across 5 fine-tuning seeds, harmfulness bands overlap. This justifies repeats with training seeds.
14. Larsen, "The Instability of Safety: How Random Seeds and Temperature Expose Inconsistent LLM Refusal Behavior", [2512.12066](https://arxiv.org/abs/2512.12066), 2025, preprint. 18–28% of harmful prompts flip across seeds and temperatures. This justifies several samples per prompt.
15. **NEW** Bouthillier et al., "Accounting for Variance in Machine Learning Benchmarks", [2103.03098](https://arxiv.org/abs/2103.03098), 2021, MLSys (S2). It shows which sources of variance to randomize when comparing methods.

### Group 6. Rival defenses, and how defenses are evaluated (13 papers; 12 NEW)

1. ★ Huang et al., "Harmful Fine-tuning Attacks and Defenses for Large Language Models: A Survey", [2409.18169](https://arxiv.org/abs/2409.18169), 2024, ACM Computing Surveys (2026). It records the field's default practice: two metrics, no over-refusal, no seeds, and overhead only as future work.
2. ★ **NEW** Qi et al., "On Evaluating the Durability of Safeguards for Open-Weight LLMs", [2412.07097](https://arxiv.org/abs/2412.07097), 2024, ICLR 2025 (S2). Small changes in the evaluation setup, reportedly including seeds, reverse defense claims. This is why we need seeds and frozen rules.
3. ★ **NEW** Hossain et al., "SafeTuneBed: A Toolkit for Benchmarking LLM Safety Alignment in Fine-Tuning", [2506.00676](https://arxiv.org/abs/2506.00676), 2025, preprint. It runs LoRA, Lisa, Vaccine and SafeLoRA on seven tasks in benign, 5% and 30% harmful regimes, with 3 seeds and no cost matching.
4. **NEW** Hossain et al., "TamperBench: Systematically Stress-Testing LLM Safety Under Fine-Tuning and Tampering", [2602.06911](https://arxiv.org/abs/2602.06911), 2026, KDD (S2). A unified tamper benchmark with hyperparameter sweeps per attack. It is mostly adversarial, not benign.
5. **NEW** Meng et al., "One Risk Down, Another Up: Cross-Risk Interactions Induced by LLM Defenses", [2510.07968](https://arxiv.org/abs/2510.07968), 2025, preprint. 77.1% of cross-risk tests show significant shifts, including exaggerated safety. It uses a benign control with a matched training budget, which is a precedent for side-effect limits.
6. **NEW** Huang et al., "Vaccine: Perturbation-aware Alignment for Large Language Models against Harmful Fine-tuning Attack", [2402.01109](https://arxiv.org/abs/2402.01109), 2024, NeurIPS 2024. An alignment-stage defense. It needs control of alignment, so it is outside a data-fix menu.
7. **NEW** Huang et al., "Lisa: Lazy Safety Alignment for Large Language Models against Harmful Fine-tuning Attack", [2405.18641](https://arxiv.org/abs/2405.18641), 2024, NeurIPS 2024. A fine-tuning-stage defense that keeps returning to alignment data: a training-time form of adding safety data.
8. **NEW** Huang et al., "Booster: Tackling Harmful Fine-tuning for Large Language Models via Attenuating Harmful Perturbation", [2409.01586](https://arxiv.org/abs/2409.01586), 2024, ICLR (S2). An alignment-stage defense, included for completeness of the rival set.
9. **NEW** Hsu et al., "Safe LoRA: the Silver Lining of Reducing Safety Risks when Fine-tuning Large Language Models", [2405.16833](https://arxiv.org/abs/2405.16833), 2024, NeurIPS 2024. It projects LoRA updates toward a safety-aligned subspace. It is a cheap model-level reference arm.
10. **NEW** Li et al., "Safety Layers in Aligned Large Language Models: The Key to LLM Security", [2408.17003](https://arxiv.org/abs/2408.17003), 2024, ICLR 2025. It freezes a few safety-critical layers during fine-tuning: the safety-layer family.
11. **NEW** Peng et al., "Shape it Up! Restoring LLM Safety during Finetuning", [2505.17196](https://arxiv.org/abs/2505.17196), 2025, NeurIPS 2025. Guard-model scores reweight training within each response. A classifier diagnosis is used inside training.
12. **NEW** Huang et al., "Antidote: Post-fine-tuning Safety Alignment for Large Language Models against Harmful Fine-tuning", [2408.09600](https://arxiv.org/abs/2408.09600), 2024, ICML 2025. A post-fine-tuning repair that removes harmful weights and leaves the data unchanged.
13. **NEW** Bhardwaj et al., "Language Models are Homer Simpson! Safety Re-Alignment of Fine-tuned Language Models through Task Arithmetic", [2402.11746](https://arxiv.org/abs/2402.11746), 2024, ACL (S2). It adds a safety vector back to the weights: a sub-minute model-level fix.

### Group 7. Attribution methods and critiques: skim, then read the ones you use (18 papers; 0 NEW)

1. ★ Li et al., "Do Influence Functions Work on Large Language Models?", [2409.19998](https://arxiv.org/abs/2409.19998), 2024, EMNLP (S2). Influence functions perform poorly, including at finding harmful data. This is the skeptic's baseline.
2. ★ Xia et al., "LESS: Selecting Influential Data for Targeted Instruction Tuning", [2402.04333](https://arxiv.org/abs/2402.04333), 2024, ICML 2024. LoRA gradient similarity is the practical gradient arm, and it was strong in Xiao and Aranguri.
3. ★ Quirke et al., "Bergson: An Open Source Library for Data Attribution", [2606.11660](https://arxiv.org/abs/2606.11660), 2026, preprint. It prices the expensive arm: EK-FAC and SOURCE cost several training runs.
4. Koh and Liang, "Understanding Black-box Predictions via Influence Functions", [1703.04730](https://arxiv.org/abs/1703.04730), 2017, ICML 2017. The original influence functions.
5. Pruthi et al., "Estimating Training Data Influence by Tracing Gradient Descent", [2002.08484](https://arxiv.org/abs/2002.08484), 2020, NeurIPS 2020. TracIn is cheap when LoRA checkpoints are saved.
6. Park et al., "TRAK: Attributing Model Behavior at Scale", [2303.14186](https://arxiv.org/abs/2303.14186), 2023, ICML (S2). Attribution with random projections.
7. Grosse et al., "Studying Large Language Model Generalization with Influence Functions", [2308.03296](https://arxiv.org/abs/2308.03296), 2023, report. EK-FAC influence at LLM scale.
8. Choe et al., "What is Your Data Worth to GPT? LLM-Scale Data Valuation with Influence Functions", [2405.13954](https://arxiv.org/abs/2405.13954), 2024, NeurIPS (S2). LoGra uses low-rank gradient projection.
9. Bae et al., "Training Data Attribution via Approximate Unrolled Differentiation", [2405.12186](https://arxiv.org/abs/2405.12186), 2024. SOURCE; a NeurIPS 2024 version exists under a shorter title (see "What could not be verified").
10. Li et al., "Where Did It Go Wrong? Attributing Undesirable LLM Behaviors via Representation Gradient Tracing", [2510.02334](https://arxiv.org/abs/2510.02334), 2025, preprint. Representation-gradient tracing for undesirable behaviours.
11. Ilyas et al., "Datamodels: Predicting Predictions from Training Data", [2202.00622](https://arxiv.org/abs/2202.00622), 2022, ICML 2022 (per earlier notes). Attribution by retraining: trial runs used as attribution.
12. Basu et al., "Influence Functions in Deep Learning Are Fragile", [2006.14651](https://arxiv.org/abs/2006.14651), 2020, ICLR 2021. Influence estimates are fragile in deep networks.
13. Bae et al., "If Influence Functions are the Answer, Then What is the Question?", [2209.05364](https://arxiv.org/abs/2209.05364), 2022, NeurIPS (S2). What influence functions actually estimate.
14. Mlodozeniec et al., "Distributional Training Data Attribution: What do Influence Functions Sample?", [2506.12965](https://arxiv.org/abs/2506.12965), 2025, NeurIPS (S2). Attribution inherits training randomness, which matters for the seed design.
15. Coalson et al., "IF-GUIDE: Influence Function-Guided Detoxification of LLMs", [2506.01790](https://arxiv.org/abs/2506.01790), 2025, NeurIPS 2025. Token-level influence works where record-level influence fails, and a proxy model cuts the cost.
16. Wang et al., "Data Shapley in One Training Run", [2406.11011](https://arxiv.org/abs/2406.11011), 2024, ICLR 2025. Valuation during the run at small overhead: another near-free attribution price point.
17. Kowal et al., "Concept Influence: Leveraging Interpretability to Improve Performance and Efficiency in Training Data Attribution", [2602.14869](https://arxiv.org/abs/2602.14869), 2026, preprint. Attribution built on interpretability, at lower cost.
18. Chen et al., "Influence-Preserving Proxies for Gradient-Based Data Selection in LLM Fine-tuning", [2602.17835](https://arxiv.org/abs/2602.17835), 2026, preprint. Proxy models cut the cost of gradient-based selection. Earlier notes call it IProX.

### Group 8. Cite only: datasets, benchmarks, judges and models (36 entries; 23 NEW)

**Benign tasks, and how this literature scores task skill**

1. **NEW** Taori et al., Stanford Alpaca, [GitHub](https://github.com/tatsu-lab/stanford_alpaca), 2023 (no arXiv). General instructions, scored for helpfulness by an LLM judge. Qi et al., He et al. and DataShield use it.
2. **NEW** Databricks, databricks-dolly-15k, [dataset page](https://huggingface.co/datasets/databricks/databricks-dolly-15k), 2023 (no arXiv). General instructions, used in the same way.
3. **NEW** Cobbe et al., "Training Verifiers to Solve Math Word Problems" (GSM8K), [2110.14168](https://arxiv.org/abs/2110.14168), 2021. Math, scored by final-answer accuracy. PTST, GradShield, SafeTuneBed and DataRx use it.
4. **NEW** Gliwa et al., "SAMSum Corpus: A Human-annotated Dialogue Dataset for Abstractive Summarization", [1911.12237](https://arxiv.org/abs/1911.12237), 2019, Workshop on New Frontiers in Summarization. Dialogue summaries, scored by ROUGE-1 F1.
5. **NEW** Socher et al., "Recursive Deep Models for Semantic Compositionality Over a Sentiment Treebank" (SST-2), [ACL Anthology D13-1170](https://aclanthology.org/D13-1170/), 2013, EMNLP 2013. Sentiment, scored by accuracy. It is the survey's default task.
6. **NEW** Zhang et al., "Character-level Convolutional Networks for Text Classification" (AG News), [1509.01626](https://arxiv.org/abs/1509.01626), 2015, NeurIPS (S2). Topic classification, scored by accuracy.
7. **NEW** Dubois et al., "AlpacaFarm: A Simulation Framework for Methods that Learn from Human Feedback", [2305.14387](https://arxiv.org/abs/2305.14387), 2023, NeurIPS 2023. The origin of AlpacaEval: win rate from an LLM judge.
8. **NEW** Dubois et al., "Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators", [2404.04475](https://arxiv.org/abs/2404.04475), 2024, COLM 2024. A win rate corrected for response length.
9. **NEW** Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", [2306.05685](https://arxiv.org/abs/2306.05685), 2023, NeurIPS 2023 Datasets and Benchmarks. Multi-turn helpfulness; SafeTuneBed's utility metric.
10. **NEW** Hendrycks et al., "Measuring Massive Multitask Language Understanding", [2009.03300](https://arxiv.org/abs/2009.03300), 2020, ICLR 2021. MMLU, a general capability check.
11. **NEW** Li et al., "ChatDoctor: A Medical Chat Model Fine-Tuned on a Large Language Model Meta-AI (LLaMA) Using Medical Domain Knowledge", [2303.14070](https://arxiv.org/abs/2303.14070), 2023. Medical dialogue, scored by BERTScore in the survey. It is a PTST task.
12. Clark et al., "Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge", [1803.05457](https://arxiv.org/abs/1803.05457), 2018. Our current benign check. Its restricted answer format risks incoherent safety answers (Vishnubhotla et al.).
13. Ding et al., "Enhancing Chat Language Models by Scaling High-quality Instructional Conversations" (UltraChat), [2305.14233](https://arxiv.org/abs/2305.14233), 2023, EMNLP (S2). The base data of DATE-LM's toxicity setting.

**Harmful data and safety benchmarks**

14. Lin et al., "ToxicChat: Unveiling Hidden Challenges of Toxicity Detection in Real-World User-AI Conversation", [2310.17389](https://arxiv.org/abs/2310.17389), 2023, EMNLP Findings 2023. The look-alike middle case (ToxicChat-Het).
15. Ji et al., "PKU-SafeRLHF: Towards Multi-Level Safety Alignment for LLMs with Human Preference", [2406.15513](https://arxiv.org/abs/2406.15513), 2024, ACL 2025. The overt injected anchor.
16. **NEW** Ji et al., "BeaverTails: Towards Improved Safety Alignment of LLM via a Human-Preference Dataset", [2307.04657](https://arxiv.org/abs/2307.04657), 2023, NeurIPS 2023. The survey's standard harmful data, and its moderation judge.
17. **NEW** Zou et al., "Universal and Transferable Adversarial Attacks on Aligned Language Models" (AdvBench), [2307.15043](https://arxiv.org/abs/2307.15043), 2023. Common harmful prompts.
18. Mazeika et al., "HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal", [2402.04249](https://arxiv.org/abs/2402.04249), 2024, ICML (S2).
19. Souly et al., "A StrongREJECT for Empty Jailbreaks", [2402.10260](https://arxiv.org/abs/2402.10260), 2024, NeurIPS (S2).
20. Vidgen et al., "SimpleSafetyTests: a Test Suite for Identifying Critical Safety Risks in Large Language Models", [2311.08370](https://arxiv.org/abs/2311.08370), 2023.
21. **NEW** Xie et al., "SORRY-Bench: Systematically Evaluating Large Language Model Safety Refusal", [2406.14598](https://arxiv.org/abs/2406.14598), 2024, ICLR 2025. 44 refusal categories; Fraser et al. and Vishnubhotla et al. use it.
22. **NEW** Wang et al., "Do-Not-Answer: A Dataset for Evaluating Safeguards in LLMs", [2308.13387](https://arxiv.org/abs/2308.13387), 2023. Prompts organized by a risk taxonomy.

HEx-PHI comes from Qi et al. 2023 (group 2), and DirectHarm4 and GSM-Danger from Lyu et al. (group 2).

**Over-refusal**

23. Röttger et al., "XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models", [2308.01263](https://arxiv.org/abs/2308.01263), 2023, NAACL 2024. 250 safe prompts and 200 unsafe contrast prompts; the standard small test.
24. Cui et al., "OR-Bench: An Over-Refusal Benchmark for Large Language Models", [2405.20947](https://arxiv.org/abs/2405.20947), 2024, ICML 2025. Its Hard-1k set is SafeTune's over-refusal test.
25. **NEW** An et al., "Automatic Pseudo-Harmful Prompt Generation for Evaluating False Refusals in Large Language Models" (PHTest), [2409.00598](https://arxiv.org/abs/2409.00598), 2024.
26. **NEW** Shi et al., "Navigating the OverKill in Large Language Models" (OKTest), [2401.17633](https://arxiv.org/abs/2401.17633), 2024, ACL (S2).
27. **NEW** Brahman et al., "The Art of Saying No: Contextual Noncompliance in Language Models" (CoCoNot), [2407.12043](https://arxiv.org/abs/2407.12043), 2024, NeurIPS 2024 Datasets and Benchmarks. It includes a contrast set for over-refusal.
28. **NEW** Zhang et al., "FalseReject: A Resource for Improving Contextual Safety and Mitigating Over-Refusals in LLMs via Structured Reasoning", [2505.08054](https://arxiv.org/abs/2505.08054), 2025, COLM 2025.
29. **NEW** Jiang et al., "WildTeaming at Scale: From In-the-Wild Jailbreaks to (Adversarially) Safer Language Models" (WildJailbreak), [2406.18510](https://arxiv.org/abs/2406.18510), 2024, NeurIPS (S2). It includes benign prompts that look adversarial.

**Judges, and the classifier-score diagnosis**

30. **NEW** Han et al., "WildGuard: Open One-Stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs", [2406.18495](https://arxiv.org/abs/2406.18495), 2024, NeurIPS 2024. It detects both harm and refusal. Pan et al. and Jaburi et al. compare against it.
31. **NEW** Inan et al., "Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations", [2312.06674](https://arxiv.org/abs/2312.06674), 2023. The Llama Guard family is GradShield's baseline and DataRx's judge.
32. Zhao et al., "Qwen3Guard Technical Report", [2510.14276](https://arxiv.org/abs/2510.14276), 2025. Our judge; DataRx also uses Qwen3Guard-Gen-8B.
33. Padhi et al., "Granite Guardian", [2412.07724](https://arxiv.org/abs/2412.07724), 2024. Our second judge.

**Models and training**

34. Qwen Team, "Qwen2.5 Technical Report", [2412.15115](https://arxiv.org/abs/2412.15115), 2024.
35. **NEW** Team OLMo, "2 OLMo 2 Furious", [2501.00656](https://arxiv.org/abs/2501.00656), 2024, COLM 2025 (short version). The planned second model family.
36. Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models", [2106.09685](https://arxiv.org/abs/2106.09685), 2021, ICLR (S2).

---

## URLs in reading order

```text
===== Group 1. Read first: the closest work =====
https://arxiv.org/abs/2602.11079
https://arxiv.org/abs/2609.22153
https://arxiv.org/abs/2606.00160
https://arxiv.org/abs/2608.04322
https://arxiv.org/abs/2605.14194
https://arxiv.org/abs/2606.03648
https://arxiv.org/abs/2609.02771
https://arxiv.org/abs/2502.11411
===== Group 2. The problem: benign fine-tuning erodes safety, and why =====
https://arxiv.org/abs/2310.03693
https://arxiv.org/abs/2508.12531
https://arxiv.org/abs/2406.05946
https://arxiv.org/abs/2402.18540
https://arxiv.org/abs/2506.05346
https://arxiv.org/abs/2604.24902
https://arxiv.org/abs/2406.20053
https://arxiv.org/abs/2502.19537
https://arxiv.org/abs/2502.14828
https://arxiv.org/abs/2406.11717
https://arxiv.org/abs/2502.17424
https://arxiv.org/abs/2310.02949
===== Group 3. The fix menu: add, rewrite, self-distill, reframe =====
https://arxiv.org/abs/2309.07875
https://arxiv.org/abs/2406.10288
https://arxiv.org/abs/2407.21783
https://arxiv.org/abs/2604.25891
https://arxiv.org/abs/2601.01887
https://arxiv.org/abs/2510.21885
https://arxiv.org/abs/2402.14968
https://arxiv.org/abs/2506.19823
https://arxiv.org/abs/2402.13669
https://arxiv.org/abs/2609.04482
https://arxiv.org/abs/2402.11192
https://arxiv.org/abs/2605.15239
https://arxiv.org/abs/2606.15517
https://arxiv.org/abs/2405.19358
https://arxiv.org/abs/2510.04340
https://arxiv.org/abs/2510.05024
https://arxiv.org/abs/2602.09987
https://arxiv.org/abs/2607.10750
===== Group 4. Diagnosis signals for the remove fix: selectors and filters =====
https://arxiv.org/abs/2507.09424
https://arxiv.org/abs/2404.01099
https://arxiv.org/abs/2507.18631
https://arxiv.org/abs/2505.06843
https://arxiv.org/abs/2605.04572
https://arxiv.org/abs/2312.12736
https://arxiv.org/abs/2604.17215
https://arxiv.org/abs/2602.17546
https://arxiv.org/abs/2507.21509
https://arxiv.org/abs/2607.15081
https://arxiv.org/abs/2410.07471
https://arxiv.org/abs/2410.10014
https://arxiv.org/abs/2609.20027
https://openreview.net/forum?id=gN7pWmjiQW
===== Group 5. Deciding under a budget, and measuring well =====
https://arxiv.org/abs/2504.11393
https://arxiv.org/abs/2503.01807
https://arxiv.org/abs/2002.06305
https://arxiv.org/abs/1909.03004
https://arxiv.org/abs/1502.07943
https://arxiv.org/abs/1603.06560
https://arxiv.org/abs/2501.12642
https://arxiv.org/abs/2404.07177
https://arxiv.org/abs/2508.11551
https://arxiv.org/abs/2410.15661
https://arxiv.org/abs/2505.16260
https://arxiv.org/abs/2609.32380
https://arxiv.org/abs/2506.17209
https://arxiv.org/abs/2512.12066
https://arxiv.org/abs/2103.03098
===== Group 6. Rival defenses, and how defenses are evaluated =====
https://arxiv.org/abs/2409.18169
https://arxiv.org/abs/2412.07097
https://arxiv.org/abs/2506.00676
https://arxiv.org/abs/2602.06911
https://arxiv.org/abs/2510.07968
https://arxiv.org/abs/2402.01109
https://arxiv.org/abs/2405.18641
https://arxiv.org/abs/2409.01586
https://arxiv.org/abs/2405.16833
https://arxiv.org/abs/2408.17003
https://arxiv.org/abs/2505.17196
https://arxiv.org/abs/2408.09600
https://arxiv.org/abs/2402.11746
===== Group 7. Attribution methods and critiques (skim) =====
https://arxiv.org/abs/2409.19998
https://arxiv.org/abs/2402.04333
https://arxiv.org/abs/2606.11660
https://arxiv.org/abs/1703.04730
https://arxiv.org/abs/2002.08484
https://arxiv.org/abs/2303.14186
https://arxiv.org/abs/2308.03296
https://arxiv.org/abs/2405.13954
https://arxiv.org/abs/2405.12186
https://arxiv.org/abs/2510.02334
https://arxiv.org/abs/2202.00622
https://arxiv.org/abs/2006.14651
https://arxiv.org/abs/2209.05364
https://arxiv.org/abs/2506.12965
https://arxiv.org/abs/2506.01790
https://arxiv.org/abs/2406.11011
https://arxiv.org/abs/2602.14869
https://arxiv.org/abs/2602.17835
===== Group 8. Cite only: datasets, benchmarks, judges and models =====
https://github.com/tatsu-lab/stanford_alpaca
https://huggingface.co/datasets/databricks/databricks-dolly-15k
https://arxiv.org/abs/2110.14168
https://arxiv.org/abs/1911.12237
https://aclanthology.org/D13-1170/
https://arxiv.org/abs/1509.01626
https://arxiv.org/abs/2305.14387
https://arxiv.org/abs/2404.04475
https://arxiv.org/abs/2306.05685
https://arxiv.org/abs/2009.03300
https://arxiv.org/abs/2303.14070
https://arxiv.org/abs/1803.05457
https://arxiv.org/abs/2305.14233
https://arxiv.org/abs/2310.17389
https://arxiv.org/abs/2406.15513
https://arxiv.org/abs/2307.04657
https://arxiv.org/abs/2307.15043
https://arxiv.org/abs/2402.04249
https://arxiv.org/abs/2402.10260
https://arxiv.org/abs/2311.08370
https://arxiv.org/abs/2406.14598
https://arxiv.org/abs/2308.13387
https://arxiv.org/abs/2308.01263
https://arxiv.org/abs/2405.20947
https://arxiv.org/abs/2409.00598
https://arxiv.org/abs/2401.17633
https://arxiv.org/abs/2407.12043
https://arxiv.org/abs/2505.08054
https://arxiv.org/abs/2406.18510
https://arxiv.org/abs/2406.18495
https://arxiv.org/abs/2312.06674
https://arxiv.org/abs/2510.14276
https://arxiv.org/abs/2412.07724
https://arxiv.org/abs/2412.15115
https://arxiv.org/abs/2501.00656
https://arxiv.org/abs/2106.09685
```

---

## What could not be verified

1. **Non-arXiv entries that were not opened.** These are Alpaca (GitHub), Dolly (Hugging Face page), SST-2 (ACL Anthology) and Jaburi et al. (OpenReview). The earlier review hit a bot check on OpenReview. A search result confirms the workshop listing and the author list. No arXiv version was found.
2. **Venues from Semantic Scholar only.** These are marked "(S2)" in the groups. The venue name is reliable, but the year was not checked for:
   - Li et al. (influence functions; EMNLP);
   - LoGra (NeurIPS);
   - StrongREJECT (NeurIPS);
   - Hsiung et al. (ACL);
   - Bach et al. (ACL 2026);
   - TamperBench (KDD 2026);
   - OKTest (ACL).
3. **Venues from earlier project notes, not re-checked here:** Pan et al. (ICML 2026) and Datamodels (ICML 2022). He et al.'s venue (likely COLM 2024) rests on memory and an OpenReview search hit, so it is marked "not confirmed".
4. **No venue found:** Wang et al.'s backdoor safety alignment (2402.14968), Kazdan et al., and most 2026 preprints.
5. **Facts taken from fetch-tool summaries.** These are small-model summaries of each HTML page. Check every one in the PDF before citing:
   - **SafeTune:** one deterministic run per method; wall-clock costs; no data-level fixes; "feasible" defined by access. The summary also gave an internal title, "SafeTune: A Modular Framework for Fixing Safety Drift in Fine-Tuned LLMs", which differs from the arXiv listing. Cite the listing title.
   - **DataShield (2606.00160):** the Table IV cost figures; the baseline list.
   - **GradShield:** the 25% overhead; 5 seeds on Identity-Shift; the safety and utility tolerances; no over-refusal measure.
   - **DataRx:** the ratio range; the XSTest judge; task accuracy within about 2 points; the paraphrase and self-distill arms.
   - **Safety at One Shot:** 0.02 GPU-hours; its baseline list.
   - **SafeTuneBed:** 3 seeds; about 200 GPU-hours; little erosion in the benign regime.
   - **Vishnubhotla et al.:** SafeLoRA only; the judge failures.
   - **Cross-risk:** the matched control. Its 5 runs may use decoding seeds rather than training seeds.
6. **Facts from search snippets only:**
   - Xiao and Aranguri's dollar costs (about $30, $320 and $500);
   - the overheads of Surgery (0.05 h) and Antibody (0.20 h);
   - the sentence in Qi et al.'s durability paper about seeds alone breaking defenses;
   - the survey's ACM issue (volume 58, issue 13, October 2026);
   - an earlier workshop version of SafeTuneBed;
   - SOURCE's NeurIPS 2024 title ("Training Data Attribution via Approximate Unrolling");
   - Semantic Scholar's Nature listing for Emergent Misalignment;
   - the earlier title of Xiao and Aranguri's v2 ("In-the-Wild Model Organisms: …").
7. **Facts from earlier project notes, not re-read in this pass:**
   - the Llama 3 safety-mix details and the Persona Features re-alignment claim (problem-validation note);
   - the numbers for He et al., DATE-LM, Pan et al., Weckbecker et al., Fraser et al., Larsen, Bergson, Nautiyal, Ivison et al. and DataDecide (prior-work list and positioning review).
8. **Titles seen in search results and not verified, so not listed:**
   - Self-Mined Hardness (2605.03226);
   - Semantic Loss Guided SFT (2412.06843);
   - RefusalGuard (2605.01913);
   - Just Enough Shifts (2507.04250);
   - over-refusal representation intervention (2511.19009);
   - benign fine-tuning in audio LLMs (2604.16659);
   - SafeSteer (2606.02530);
   - Multilingual Safety Alignment via Self-Distillation (2605.02971);
   - DART (2604.16845);
   - the reasoning-model safety study (2505.15404).
9. **Limits of the search:**
   - It ran 17 searches, mostly over arXiv.
   - Papers from September and October 2026, OpenReview submissions still under review, and non-English work may be missing.
   - "Not found" means "not found by this search". Repeat the search before any submission.

---

## Changes from the 6 October list

**Counts.** Kept 59 of 62. Added 75 (all NEW entries above). Dropped 3:
- O'Brien et al., Deep Ignorance ([2508.06601](https://arxiv.org/abs/2508.06601)). It is about filtering pretraining data, not about fixing fine-tuning data.
- Souly et al., poisoning with a near-constant number of samples ([2510.07192](https://arxiv.org/abs/2510.07192)). It is about poisoning dose. Cite it only if the anchor's injection dose is discussed.
- Song et al., multi-indicator selection weights ([2605.09665](https://arxiv.org/abs/2605.09665)). It is general data selection, with no safety or decision content.

**Corrections to the earlier list** (from arXiv metadata):
- ADMIRE-BayesOpt's first author is **Shengzhuang Chen**, not "Ouyang".
- Phantom Transfer's exact title is "Filtering Harmful Actions Isn't Enough: Phantom Transfer in Agentic **SDF**".
- In-Run Data Shapley is "Data Shapley in One Training Run", [2406.11011](https://arxiv.org/abs/2406.11011), ICLR 2025. Its ID had not been checked before.
- The eight additions after the positioning review (section 8b) are now verified by ID and title. The arXiv title behind "IProX" is "Influence-Preserving Proxies for Gradient-Based Data Selection in LLM Fine-tuning".
- Two different "DataShield" papers exist (2606.00160 and 2607.15081). Cite them by ID.
- Venues found that the earlier list lacked: LARF (EMNLP, S2), Benign Samples Matter (ICML, S2), Distributional TDA (NeurIPS, S2), Na et al. (EMNLP 2024), and the survey (ACM Computing Surveys).

**Verified on arXiv but not added** (low relevance to the reframed question):
- Jain et al. ([2407.10264](https://arxiv.org/abs/2407.10264), NeurIPS 2024), Wei et al. ([2402.05162](https://arxiv.org/abs/2402.05162), ICML 2024) and Peng et al. ([2405.17374](https://arxiv.org/abs/2405.17374), NeurIPS 2024): mechanism and landscape studies.
- RepNoise ([2405.14577](https://arxiv.org/abs/2405.14577)), Rosati et al. on immunization ([2402.16382](https://arxiv.org/abs/2402.16382)), Panacea ([2501.18100](https://arxiv.org/abs/2501.18100)), AsFT ([2506.08473](https://arxiv.org/abs/2506.08473)), Antibody ([2603.00498](https://arxiv.org/abs/2603.00498), ICLR 2026), Surgery ([2602.05228](https://arxiv.org/abs/2602.05228)) and TRACE ([2607.16242](https://arxiv.org/abs/2607.16242)): defenses aimed mainly at harmful fine-tuning.
- One Step to the Side ([2605.14605](https://arxiv.org/abs/2605.14605)): adaptive attacks.
- Chance-constrained fine-tuning ([2609.29960](https://arxiv.org/abs/2609.29960)): a constraint method. Read it if the feasibility rule needs a formal model.
- MMSAFE ([2609.22144](https://arxiv.org/abs/2609.22144), EMNLP 2026): a multilingual filter.
- VLGuard ([2402.02207](https://arxiv.org/abs/2402.02207)): vision-language models.
- Self-Synthesized Rehearsal ([2403.01244](https://arxiv.org/abs/2403.01244), ACL 2024).
- Single-vector ablation for false refusal ([2410.03415](https://arxiv.org/abs/2410.03415), ICLR 2025).
- FAB ([2505.16567](https://arxiv.org/abs/2505.16567)): dormant behaviours triggered by fine-tuning.
- Data attribution of emergent misalignment with persona features ([2608.11025](https://arxiv.org/abs/2608.11025)) and TAME ([2609.16754](https://arxiv.org/abs/2609.16754)).
