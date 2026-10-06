# Grant evidence dossier: decision value of training-data attribution for safety data edits

A living document, started 5 October 2026 at the user's request: "make sure all of this information is stored somewhere it will help us make the grant proposal good". It collects, in one place, what a proposal needs, and every claim links to its record in this repository.

**Rule for using it:** quote only what the linked records show. Estimates are marked as estimates. Development results are not confirmatory.

## 1. One-paragraph pitch (draft)

Teams that fine-tune language models must constantly decide how to fix training data that teaches bad behaviour: delete examples, rewrite them, or add new ones. Cheap signals exist for choosing:
- safety classifiers;
- short trial runs;
- metadata.

An expensive one exists too: **training-data attribution**, which traces a behaviour back to the examples that caused it. Prior work evaluates attribution by how well it ranks examples, or by how much an edit moves behaviour ([Luo et al. 2026](../review/2026-10-05-rewriting-precedent.md); DATE-LM; IF-Guide). Nobody has asked the practical question: **once its compute is charged, does attribution lead to better fix *decisions* than strong cheap methods?**

We test this with:
- frozen protocols and a finite menu of candidate edits;
- matched compute budgets and full cost accounting;
- confirmation on held-out data with fresh seeds.

Our preliminary results already show that a simple, common rule ("delete the top 10% of rows the safety classifier flags") can make a model *less* safe. The rule removes far more rows than are actually unsafe, including the examples that teach refusal. Choosing *which* fix to make, and how much, is the gap a better selector could fill.

**Grant version (3 sentences; from the [positioning review](../review/2026-10-06-positioning-review.md), 6 October):** Teams that fix fine-tuning data for safety can use cheap signals, such as safety classifiers and short trial runs, or an expensive one, training-data attribution, but no study measures which signal leads to better fixes for the money. Using replicated training runs and held-out confirmation, we will measure how often each signal picks the safest fix that keeps capability and avoids over-refusal, at matched compute, both where classifiers can see the problem and where they cannot. The result will be an open benchmark and a practical rule for when attribution is worth paying for.

### 1a. Why the problem is real (evidence; from the [problem-validation review](../review/2026-10-06-problem-validation.md), 6 October)

**Verdict: partly real.** Teams do fix training data after unsafe behaviour, and they manage the side effects explicitly. But practitioners do not publicly ask whether attribution is worth its compute; researchers and funders ask that. **Do not claim practitioners ask it.**

Sentences to use, each backed by a primary source:
- Model developers change training data when models misbehave. During Claude Opus 4's development, Anthropic restored an omitted fine-tuning dataset and added a targeted counter-dataset ([system card](https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf)). Ai2 removed post-training content after tracing a wrong claim to it ([OLMoTrace](https://allenai.org/blog/olmotrace)).
- Fine-tuning services screen customer data with content classifiers and block unsafe models, but they report harm categories rather than rows. Microsoft's message is "Please review your training data set and resubmit the job" ([Foundry docs](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/fine-tuning-safety-evaluation), checked on 6 October). The customer must find what to fix.
- Fixes have side effects that teams manage. Meta ran repeated experiments to balance violations against false refusals in Llama 3's safety data ([arXiv 2407.21783](https://arxiv.org/abs/2407.21783)). Google said tuning made Gemini refuse harmless prompts ([blog](https://blog.google/products/gemini/gemini-image-generation-issue/)).
- Content screening is not enough: benign-looking data can implant harmful behaviour that input-level monitors miss ([Anthropic](https://alignment.anthropic.com/2026/introspection-adapters/)).
- Anthropic chose its pretraining safety filter partly on cost, and lists influence functions as future work ([post](https://alignment.anthropic.com/2025/pretraining-data-filtering/), checked on 6 October). Attribution's cost and reliability at scale remain open problems ([arXiv 2407.14981](https://arxiv.org/abs/2407.14981); [arXiv 2501.12642](https://arxiv.org/abs/2501.12642)).

**What the evidence implies for the design** (recommendations; not yet decided):
- the most real form of the problem is "which data fix, and how much diagnosis to buy first", especially for harmful data that looks benign;
- put additions on the menu;
- count costs in full-run equivalents;
- consider leading with side-effect prediction.

## 2. Research question and novelty

- **Question** ([FOCUS.md](../FOCUS.md)): in a fixed fine-tuning setting, does adding attribution to a selector that already uses metadata, classifier scores and short runs improve its choice among data edits, compared with spending attribution's full cost on more runs? The primary failure measured is unsafe completions.
- **What exists already** (cite, do not claim):
  - rewriting as a safety data edit, and attribution-guided selection of rows to rewrite: Luo et al. 2026, arXiv 2609.02771;
  - attribution for safety filtering: DATE-LM;
  - "about 3% safety data" (Safety-Tuned LLaMAs, Bianchi et al.);
  - harmful fine-tuning breaks safety with few examples (Qi et al. 2023);
  - **the closest prior work:** attribution beats moderation classifiers at *removing* unsafe training data, in nearly our setting (UltraChat with injected ToxicChat). It reports no compute comparison, no rewriting and no training seeds. Pan et al., arXiv 2502.11411, ICML 2026.
  - gradient-based filtering of harmful fine-tuning rows (GradShield, arXiv 2605.14194, 2026);
  - influence functions do poorly at finding harmful data (Li et al., arXiv 2409.19998).
  - The full search and citation list (6 October 2026) is in the [prior-work search](../review/2026-10-06-prior-work-search.md).
- **Our distinct contribution:**
  - a matched-cost decision evaluation against strong cheap selectors;
  - finite menus with held-out confirmation;
  - reporting when evidence is too weak to choose.

  See the overlap table in the [precedent note](../review/2026-10-05-rewriting-precedent.md).
- **The open gap, stated precisely** ([positioning review](../review/2026-10-06-positioning-review.md), 6 October). No paper compares spending compute on attribution with spending the same compute on more pilot runs of the candidate edits, especially with training seeds, side-effect limits and held-out menus.
- **The motivation:** prior results disagree by the kind of data.
  - Attribution beats WildGuard on homogeneous data (Pan et al.).
  - With safety-aligned look-alikes (our ToxicChat-Het), attribution's detection drops sharply while classifiers are unaffected (DATE-LM).
  - A practitioner cannot know in advance which case they are in.
- **ADOPTED direction** (6 October, by the user; [FOCUS.md](../FOCUS.md) updated; see the [reframing proposal](../review/2026-10-06-reframing-proposal.md)). Working title: *Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning*.
  - the main setting becomes benign fine-tuning that erodes an aligned model's safety, where content classifiers are expected to see little (untested; the erosion may be diffuse);
  - the fixes include adding safety data;
  - over-refusal and task skill are limits;
  - value is reported as a function of the diagnostic-to-run cost ratio;
  - v2 becomes the anchor;
  - target: ICML 2027, if funded by early November.
- **Planned framing:**
  - **Claim now** (grant, workshop): attribution as a decision input at matched compute.
  - **Build toward:** "how many training runs attribution is worth", across kinds of data (overt, look-alike, benign-looking degrading).
  - **Pre-register as secondary:** whether attribution predicts an edit's side effects, such as over-refusal.

## 3. Preliminary results (development evidence; two seeds)

| Finding | Evidence |
|---|---|
| **Small group removals do not move safety** in a safety-tuned model. With 12 single-group removals (0.08–0.63% of rows) on Qwen2.5-1.5B-Instruct, every arm stayed within seed noise. | [dev-matrix-002 results](../experiments/2026-10-04-dev-matrix-002-results.md): 78/78 units verified |
| **A base model fine-tuned on ChatGPT-written data is already fairly safe.** a0 gave 12.5 of 72 unsafe answers. The data teach caution. | [round-1 results](../experiments/2026-10-05-headroom-round-1-results.md) |
| **A fixed-size "remove the top-flagged 10%" rule backfired.** Removing the judge's top 1,015 rows raised unsafe answers from 12.5 to 24.0, with both seeds above both baseline seeds. The editable pool held only 43 harmful-answer rows (and 33 refusal rows), so the rule mostly removed rows that were not unsafe, probably including protective refusals. **State this as a finding about fixed-size top-K rules, not about classifiers.** A threshold rule ("remove only rows judged Unsafe") is untested. | Round-1 results; round-1 amendment (pool composition); positioning review |
| **Targeted rewriting was the best edit.** It gave 11.5 against random rewriting's 19.0, a gap of 7.5 with every seed separated; a second judge gives 8.0. | Round-1 results, second-judge note |
| **The measurement is robust to the choice of judge.** Granite Guardian 3.3 agrees with Qwen3Guard on 92.5% of 720 answers (Cohen's κ 0.80) and ranks the arms in the same order. | Round-1 results; `.ai/inputs/headroom-20261005/second-judge-summary.json` |
| **Seed noise is large and mostly a shared shift** (R = 3.3). With 2 seeds × 72 prompts, the minimum detectable difference is about 14 of 72. About 5 seeds are needed for about 9. | Round-1 results, noise analysis; `.ai/inputs/headroom-20261005/noise-analysis.json` |
| **The endpoint was narrow.** Most "unsafe" answers were sexual-content compliance (ToxicChat). v2 adds broad harm banks. | Round-1 results |
| **A contaminated setting gives real headroom (v2 calibration; 1 seed).** Adding 507 unsafe PKU-SafeRLHF responses (5% of the original 10,148 training rows) makes a0 74.5% unsafe on the 200-prompt development harm bank (76.3% over 600 sampled answers). Capability and over-refusal stay healthy: ARC 0.84, 2% over-refusal, and answers end. | [v2 work plan log](../experiments/2026-10-05-headroom-v2-workplan.md), 5 Oct 20:58 UTC |
| **A fix that removes the harm can break helpfulness (v2 positive control; 2 seeds).** Rewriting the classifier's top-507 rows cut unsafe answers from 79% to 10.5% (−68.8 pp vs no fix; −70.5 pp vs random rewriting; 95% bootstrap intervals exclude 0), with ARC unchanged. But refusals of harmless XSTest prompts rose from 1% to 44%, and of OR-Bench-hard prompts from 1% to 66%, failing the frozen no-damage rule. The classifier found 93% of the injected rows, so the hard part was choosing a fix that does not over-correct, not finding rows. Second judge pending. | [v2 results](../experiments/2026-10-06-headroom-v2-results.md) |
| **Base models often ship untrained chat tokens.** Qwen2.5-1.5B's `<|im_start|>`/`<|im_end|>` rows are identical to unused rows, as are OLMo's output rows. We fixed this by training the two rows. | [token check](../../.ai/inputs/headroom-engine-20261005/base-token-check.json); work plan |

**Interpretation for reviewers:** edits *can* move safety a lot here, in both directions, and a common fixed-size rule can choose a harmful edit. That is exactly the situation in which decision value can exist. Do not present round 1 as "classifiers fail" (see the row above).

## 4. Methodological strengths (what reviewers will value)

- **Frozen protocols before outcomes:** the amendment freezes, dated, with ledger entries in [EDGE_CHECKS.md](../review/EDGE_CHECKS.md).
- **Held-out protections:**
  - groups, prompts and outcomes stay unread until confirmation;
  - new evaluation banks are split by the engine before anyone reads them;
  - near-duplicate leakage is excluded (character 5-gram Jaccard ≥ 0.5).
- **Engine-verified reproducibility:**
  - a two-step A100 fixture must match bit for bit across hosts;
  - every unit is checked by the engine's `verify` (dependency chain and data stream);
  - golden regressions keep old runs byte-identical when the engine changes.
- **Full cost accounting:** every attempt counts, including failures. Budgets have a reserve rule and an automatic budget guard.
- **Durability:**
  - in-pod stop timers with leases;
  - results copied off immediately;
  - private backups verified by download-back;
  - secret scans.
- **Two independent safety judges,** and over-refusal measured with XSTest and OR-Bench in v2.

## 5. Infrastructure already built (reduces the grant's risk)

- **Engine** (`experiments/safety_selection`):
  - data preparation with token audits and held-out splits;
  - training with resume exactness, attribution scaffolding, edit files (remove, rewrite, add, combined), a row scorer, a rewrite generator and an edit builder;
  - multi-sample evaluation with continuous scores;
  - A100 preflights.
- **Selector framework (Stage B)** with its cost contract: `experiments/safety_decision_policy`.
- **Durability package:** stop timers, leases, gated workers, backups (`experiments/durability`).
- **Run kits:** launch, orchestration, finisher and budget guard (records under `.ai/inputs/`).
- **Tests:** engine 269, Stage B 172, durability 260, all passing at the latest integration.
- **An anonymous artifact** for review ([docs/anonymous-artifact.md](../../docs/anonymous-artifact.md)).

## 6. Data, models and licences

- **Training data:**
  - DATE-LM ToxicChat-Het (10,148 rows);
  - v2 adds PKU-SafeRLHF unsafe responses (CC BY-NC 4.0; 507 or 1,015 rows over 19 harm categories).
- **Evaluation:**
  - HarmBench (MIT), StrongREJECT (MIT), SimpleSafetyTests (CC BY 2.0) and OR-Bench (CC BY 4.0);
  - XSTest (CC BY 4.0);
  - ToxicChat and ARC-Easy.

  Each is pinned by commit and SHA-256: [sources manifest](../../.ai/inputs/headroom-v2/sources-manifest.json); candidates and licences in the [candidates note](../review/2026-10-05-data-and-judge-candidates.md).
- **Models:**
  - policy: Qwen2.5-1.5B base (Apache-2.0);
  - judges: Qwen3Guard-Gen-4B and Granite Guardian 3.3 8B (Apache-2.0);
  - rewrite writer: Qwen2.5-7B-Instruct.
- **Planned replication:** fully open models (Olmo 3 7B, OLMo-2 1B; Apache-2.0, open pretraining data).
- **Ethics (a commitment to state in applications):**
  - do not publish the generated harmful answers; release scores, code and protocols;
  - use the CC BY-NC components for non-commercial research only, with attribution.

## 7. Measured costs (the basis for any budget)

| Item | Measured |
|---|---|
| dev-matrix-002 (78 units, 13 A100 hosts) | about $60 in total, about $53 of it training jobs ([results](../experiments/2026-10-04-dev-matrix-002-results.md)) |
| Headroom round 1 (10 jobs, the lead's scores and rewrites, restarts) | about $42.3 ([results](../experiments/2026-10-05-headroom-round-1-results.md)) |
| One 1.5B job (large adapter, 3 epochs, e3 evaluation) | 72–102 minutes on one A100 at $1.59/h, so about $2–2.7 |
| Row scoring (9,788 rows, eager attention) | about 1 hour |
| Rewrite generation (1,947 rows, 7B, eager attention) | 1.81 h measured (3.35 s per row attempted, $1.48 per 1,000 rows); 3.19 h including the lost first attempt ([cost ledger](../costs/2026-10-06-cost-ledger.md)) |
| Row scoring (9,788 rows, Qwen3Guard-Gen-4B, eager attention) | 58 min (0.358 s per row, $0.158 per 1,000 rows; cost ledger) |
| One v2 training job (1.5B, rank-64 LoRA, 3 epochs, v2 bank evaluation at e3) | about $3.96 per pod: setup 10.6 min, preflight 20.1, training 67.6, evaluation 47.7 (cost ledger) |
| All GPU spend, 2–5 October | $153.48 over 48 pods; failed attempts $30.61 and idle $8.27 (cost ledger) |
| Local second judge (720 answers, M4 Mac) | about 1.7 hours (file timestamps), free |

**Efficiency fixes in v2,** to be measured on the validation pod: SDPA attention, micro-batch 8 × 1, a pre-built environment, light result copies, parallel finishing.

## 8. Budget tiers (estimates; scaled from section 7)

| Tier | Ask | Content |
|---|---|---|
| Lean | about $5–6k | Qwen 1.5B main study (2 settings), OLMo-2 1B replication, a partial 7B check, a human audit sample |
| **Recommended** | **about $14k** | + full Olmo 3 7B replication, a 32B scale check, 2 attribution methods, about 1,000 human-labelled answers, conference travel |
| Ideal | about $22k | 2 settings at 7B, 3 model families, more seeds and annotation |

**Recommended line items:**
- setup $500, headroom checks $400, Qwen main study $1,000, OLMo-2 replication $500;
- Olmo 3 7B replication $2,500, 32B check $800, attribution $600;
- human annotation $800, API judge sample $200, storage $100, contingency 25% (about $1,850);
- AI tools $800–1,200, travel about $3,000.

**Notes:**
- Salary is not included; ask for it separately if the funder allows.
- **Why not giant models:** one setting needs about 150–300 full runs. At 32B–70B each run costs $40–300, and the study would lose its statistical power. A big model is used only for a final scale check.
- **Seeds:** the noise analysis gives the ideal counts: about 5 per key arm for confirmation, and about 3 per candidate edit in development.

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Too little headroom: the model is already safe | The contaminated setting (v2); calibrate the injection size until a0 is at least 40% unsafe |
| The cheap classifier is unbeatable, so attribution looks useless | Menus deliberately include cases where cheap signals mislead (round 1's deletion backfire); a null is reported honestly |
| Seed noise | 5 or more seeds, sampled answers, more prompts; power planned from measured variance |
| A narrow or judge-specific measure | Broad harm banks, two judges, an over-refusal set, a human-labelled sample |
| Compute runs out | Budget guard and reserve; free tiers (Modal, Kaggle); local Mac for evaluation; staged gates |
| Leakage between training and test | Exact and near-duplicate exclusion; engine-made splits; held-out data never read |

## 10. Timeline and milestones (draft)

1. **Headroom v2 positive control** (now, within the current balance): calibration, then targeted against random rewrite.
2. **Design and freeze the decision study:** menus, selectors, costs, margins.
3. **Development stage:** true effects of about 20–40 candidate edits × about 3 seeds; attribution and short-run signals.
4. **Held-out confirmation:** fresh seeds and menus on the hidden banks.
5. **Replication** on a fully open model (Olmo 3 7B, or OLMo-2 1B).
6. **Paper:** ICML/ACL main track, or a workshop first. Release the code, data and protocol.

## 11. Funders and free compute to check (current calls must be verified)

- **AI-safety funders:** Open Philanthropy, Long-Term Future Fund, Manifund. **Superseded on 6 October: see 11c.** The LTFF has closed (replaced by the EA Funds Transformative AI Fund), and Coefficient Giving (formerly Open Philanthropy) passed its career-development funding to BlueDot.
- **Compute:**
  - Modal Academic Grant (up to $10k). **Not running as of 6 October:** "We are not currently running a credit grant program" (FAQ check);
  - NAIRR Pilot (US);
  - Google TPU Research Cloud;
  - cloud research credits;
  - RunPod referral bonuses;
  - free tiers: Modal $30/month, Kaggle about 30 GPU-hours/week, Colab.

### 11a. BlueDot Rapid Grants (was the user's first target)

> **Eligible (corrected 6 October).** The user is based in the US and was only travelling in India. BlueDot's list of countries it cannot pay (which includes India) does not apply. This is the best fast cash option: up to $20k, a 15-minute form, and about 5 working days according to BlueDot's November 2025 blog (FAQ-reported).

What BlueDot's grant pages said when checked on 5 October 2026. **Check the current call before applying.**

- **Who:** "people taking a promising next step in AI safety". Approval is more likely for BlueDot course participants, alumni and facilitators, and for people active in the AI-safety community.
- **How much:** up to **$20,000**.
- **What it pays for:** compute, tools, research time and access, and conference travel.
- **Application:** a short form (about 15 minutes) that asks for the plan and the budget. No formal data is required.
- **Payment and reporting:**
  - payment is a lump sum after a claim through BlueDot's portal (their blog suggests upfront payment is the default; confirm);
  - a short completion report is due within 60 days of the end;
  - material changes need written approval first.

**What to have before applying:**

| Item | Status (5 October 2026) |
|---|---|
| Eligibility angle (BlueDot course or AI-safety community involvement) | **The user to fill in** |
| One-paragraph pitch | Drafted, section 1 |
| Preliminary results | Have them (section 3). v2's "the setting works" result would be the strongest addition. |
| Plan and milestones | Section 10 |
| Itemized budget from measured costs | Tiers in section 8; v2 gives the real cost per job |
| Evidence that we can deliver (engine, tests, frozen protocols, backups) | Section 5 |
| Safety relevance | Section 1: a wrong data fix can make a model less safe, as round 1 showed |
| Risks and honest limits | Section 9 |
| Ethics and licences (do not publish harmful answers; CC BY-NC data for non-commercial research only) | Section 6 |
| Deliverables | Section 12 |

**Recommendation (General Implementation, 5 October 2026):**
1. Apply after v2's result, because a working contaminated setting is the strongest single line to add.
2. Ask for about **$5–10k for the next concrete phase:** the decision study's development stage, plus AI tools. That is a better fit for a rapid grant than the whole study, and a follow-up request is easier once that phase delivers. The $14k tier also fits under the cap.

Sources:
- [BlueDot Rapid Grants](https://bluedot.org/grants/rapid);
- [BlueDot grants](https://bluedot.org/grants);
- [BlueDot blog: Rapid grants for BlueDot projects](https://bluedot.org/blog/rapid-grants-for-bluedot-projects);
- [EA Forum: $50,000 in rapid grants](https://forum.effectivealtruism.org/posts/9AxDSiEsTabyBp3yi/we-ve-given-out-usd50-000-in-rapid-grants-now-we-want-to).

### 11b. Thinking Machines Lab: Tinker credits (checked 6 October 2026 IST)

- **Safety Research Grants** (posted 24 August 2026):
  - **Award:** up to $50,000 in Tinker credits.
  - **Who:** individuals, independent researchers and students can apply.
  - **Topics:** two of them fit this study closely: "Building classifiers for hazardous data at scale" and "Safety-relevant generalization from narrow fine-tuning".
  - **Proposal:** a 1-page summary plus CVs.
  - **Judged on:** relevance, feasibility, construct validity, and simplicity and generality.
  - **Deadline: 25 September. It has passed,** and no later round is announced.
  - **Terms:**
    - credits expire 12 months after provisioning;
    - published work must be CC BY 4.0 or under an approved open-source licence;
    - Thinking Machines gets a non-exclusive licence to the work product;
    - read the publication-approval clause before applying.
- **Tinker Research Grants** (announced 29 October 2025): from $5,000 in credits; rolling review with an answer in about a week. **Check that they are still open.**
- **What Tinker would and would not do for us:**
  - **It would do the training and sampling.** It trains LoRA on hosted open-weight models, with no pods, stop timers or GPU shortages.
    - Price: Qwen3-8B training costs $0.44 per million tokens; sampling costs $0.60.
    - **Estimate:** one of our jobs trains on about 18M tokens, so about $8 per job on an 8B model. Our 1.5B model on RunPod costs about $3.5–4 per job.
  - **It would not run attribution.** The API returns losses and per-token log-probabilities, never per-example parameter gradients. Attribution would run on downloaded adapters on a pod or the Mac, and its compute would be charged separately (the study does this anyway).
  - **Other limits:**
    - Qwen2.5-1.5B is not offered, so moving changes the model and needs a new headroom check;
    - it trains LoRA only: there is no trained chat-token row;
    - it makes no statement on training determinism, so our bit-exact fixture checks would become seed-based checks;
    - the judges must run elsewhere;
    - credits can only be spent on Tinker.
- **Use:** a training and sampling backend for the decision study, if credits come. Attribution and judges stay on pods or the Mac.

Sources:
- [Safety Research Grants](https://thinkingmachines.ai/news/safety-research-grants/);
- [How to apply](https://thinkingmachines.ai/news/safety-research-grants/apply/);
- [Terms](https://thinkingmachines.ai/legal/safety-research-grants-terms/);
- [Tinker Research and Teaching Grants](https://thinkingmachines.ai/blog/tinker-research-and-teaching-grants);
- [Tinker docs](https://tinker-docs.thinkingmachines.ai/llms-full.txt).

### 11c. Funding update for a US-based independent researcher (6 October; FAQ subagent, from the funders' own pages; corrected for location the same day)

The user is based in the US and was travelling in India in October 2026. An earlier version of this section wrongly assumed an India-based applicant. General Implementation spot-checked two points: BlueDot's list of countries it cannot pay (which includes India) and the EA Funds Transformative AI Fund page. The India restriction does not apply.

**Cash, in rough order of speed:**
1. **BlueDot Rapid Grant:** up to $20k, a 15-minute form, about 5 working days (their blog, FAQ-reported). Compute and tools are allowed. See 11a for the checklist and the eligibility angle.
2. **GTR AI Safety Fund** (gtr-foundation.org): no geographic focus; first feedback within 7 days; a 1–3 page proposal plus CV. Amounts are not stated.
3. **Manifund:** money arrives within days once someone funds you.
4. **EA Funds Transformative AI Fund** ([page](https://funds.effectivealtruism.org/funds/transformative-ai); it replaced the LTFF): always open; typically $10k–150k, but "as low as $1,000"; first decision in about 6–8 weeks (FAQ-reported). Ask whether they can expedite.
5. **Mercor AI Safety Fund:** for US and UK applicants, but it pays the researcher's institution. Check whether an independent researcher can apply through a fiscal sponsor.
6. **Lightcone Commons:** can pay, but slowly. Late applications are answered by about 23 January 2027.

**Credits:**
- **TML Tinker Research Grant:** "starting at $5,000"; rolling; "aim to respond within a week".
  - The form asks for a university and lab affiliation; whether it accepts independent researchers is unverified.
  - Credits cannot be transferred and expire after 1 year. The smallest dense models are Qwen3.5-4B and Qwen3-8B. There are no per-example gradients.
  - **Possible term risks** (if the safety-grant terms apply; unverified): CC BY 4.0 publication, pre-publication approval, and a perpetual licence. CC BY 4.0 clashes with CC BY-NC PKU-SafeRLHF data, and the acceptable-use policy may cover training on unsafe responses.
  - TML's August 2026 call mentions harm arising "accidentally from ordinary downstream fine-tuning", which fits the adopted setting.
- **Lambda Research Grant:** up to $5k of credits (available to a US-based applicant).
- **Anthropic External Researcher Access:** $1k of API credits; reviewed on the first Monday of each month (next: 2 November).
- **Google TPU Research Cloud:** free TPUs, but the code would need porting.
- The AWS, Google Cloud research and NVIDIA academic programs need an academic affiliation.

**Closed or not open:**
- the LTFF (replaced by the TAI Fund);
- Coefficient Giving's Technical AI Safety RFP (closed 15 April 2025; its career-development funding went to BlueDot on 4 September 2026);
- Modal credits (not running);
- the UK AISI programmes, the CAIS compute cluster and the FMF AI Safety Fund;
- Schmidt Sciences (no unsolicited proposals);
- SFF (individuals need a fiscal sponsor).

**AIAF = AI Alignment Foundation:** rolling, and mostly in kind (an engineering team plus compute). No amounts are stated; low fit.

**Overlapping funding:** no program publishes a rule against it. Disclose every other application, and keep separate budget lines: Tinker credits for training and sampling; cash for attribution GPUs, judges and subscriptions.

**Tax:** as a US person, the user fills in a W-9 (for example for TML), and grants are likely taxable income. Check with a tax adviser.

**Suggested order this week:**
1. BlueDot Rapid Grant (fast cash; use the dossier's pitch and the staged kill-test budget).
2. The Tinker form (state independent status; ask about the terms and the acceptable-use policy).
3. A GTR proposal.
4. A Manifund page.
5. EA Funds (ask about expediting).
6. The Anthropic credits form before 2 November.
7. Lambda.
8. Mercor, if a fiscal sponsor works.
9. AIAF, optional.

**Outlook:** if BlueDot approves within about a week, funding by early November is plausible, and **ICML 2027 is realistic again**. NeurIPS 2027 stays the fallback.

**Unverified:**
- whether Tinker research grants have their own terms or accept independents;
- AIAF's amounts;
- GTR's amounts;
- whether Mercor accepts independents through a fiscal sponsor.

FAQ holds the full list of about 50 sources.

## 12. Deliverables to promise

- the paper, including any null;
- open code, the frozen protocols and the evaluation protocol as a reusable benchmark;
- data release within licence terms (CC BY-NC components with attribution);
- cost accounting that others can reuse.

## Sources inside this repository

- research question: `research/FOCUS.md`;
- precedent: `research/review/2026-10-05-rewriting-precedent.md`;
- results: `research/experiments/2026-10-04-dev-matrix-002-results.md`, `research/experiments/2026-10-05-headroom-round-1-results.md`;
- next design: `research/experiments/2026-10-05-headroom-v2-amendment-draft.md`, `research/experiments/2026-10-05-headroom-v2-workplan.md`;
- data and judges: `research/review/2026-10-05-data-and-judge-candidates.md`;
- ledger: `research/review/EDGE_CHECKS.md`;
- backups: `backups/2026-10-04/`, `backups/2026-10-05/`.
