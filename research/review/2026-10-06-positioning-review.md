# Positioning review: how this study stands apart from prior work

6 October 2026 (IST). This is a read-only review by an Opus 5.5 subagent at the user's request. General Implementation checked it and saved it here. The subagent read full texts through an extraction tool. Treat each number as "reported", and check it against the PDF before citing.

## 0. What General Implementation checked (after the review)

| Claim in the review | Check | Result |
|---|---|---|
| Round 1 removed 1,015 rows, far more than the unsafe rows; 40 harmful rows sat in held-out groups | [Round-1 amendment](../experiments/2026-10-05-headroom-amendment-draft.md), lines 42–55 | **Confirmed.** The edit pool held 43 of the 83 harmful-answer rows and 33 of the 66 refusal rows. The other 40 and 33 sat in held-out groups. remove-10 removed 1,015 rows. |
| Round 1's scorer judged the row's own (prompt, response) pair | `experiments/safety_selection/headroom.py` (`score_rows`, `SCORE_FIELD`) | **Confirmed:** "normalized Unsafe label-sequence score of the row's own (prompt, response)". This answers the review's first unresolved question. |
| DATE-LM: attribution drops in the heterogeneous setting; classifiers do not | [DATE-LM HTML](https://arxiv.org/html/2507.09424v2), toxicity/bias filtering | **Confirmed.** The paper says: "data attribution methods exhibit a significant drop in detection performance under the Heterogeneous setting … whereas SOTA LLM classifiers … are largely unaffected". Rep-Sim drops from 0.759 to 0.597 AUPRC; WildGuard stays at 0.817. Even in the homogeneous setting, the classifiers' AUPRC (0.78–0.83) was above attribution's (about 0.70). |
| Xiao and Aranguri: dollar costs ($30 / $320 / about $500) and an 85% reduction from removal by source | [arXiv 2602.11079](https://arxiv.org/abs/2602.11079) abstract | **Partly checked.** The current title is "Probe-Based Data Attribution: Discovering and Mitigating Undesirable Behaviors in LLM Post-Training". The abstract says probe attribution is "over 10 times cheaper" than gradient attribution and LLM-judge baselines. It reports filtering −63% and label switching −78%. The dollar figures and the 85% were not checked against the body. |
| The v2 confirmation menus have no contamination | [v2 amendment](../experiments/2026-10-05-headroom-v2-amendment-draft.md), line 32 | **Confirmed by design:** "All injected rows are in the editable pool. None is in a held-out group." This matters for the decision study, not for the v2 positive control. |

## 1. Bottom line (the review's)

1. **The open gap is narrow but real.** No paper, in any domain, compares spending compute on attribution with spending the same compute on more pilot runs of the candidate edits. That comparison is still open when it also has training seeds, feasibility limits and held-out menus. Every other part of the design is at least partly done.
2. **Prior work disagrees by the kind of data, and that is the best motivation.**
   - Pan et al.: attribution (DRA) beats WildGuard after removal on homogeneous data.
   - DATE-LM: with safety-aligned look-alikes (our ToxicChat-Het), attribution's detection drops sharply, while classifiers barely change.
   - A practitioner cannot know in advance which kind of data they have.
3. **v2 is FOCUS.md's constructed failure case for choosing which rows to edit.** Qwen3Guard should flag the overt PKU-SafeRLHF answers almost perfectly. Keep v2 as the positive control for whether edits work, and as an anchor where the classifier is enough (expected D_info ≈ 0).
4. **The grant's "classifier-guided deletion backfired" claim is fragile.** A fixed-size top-K (1,015 rows) far exceeds the 43 editable unsafe rows, so any top-K ranker probably removes the protective refusal data. Reword it as a finding about fixed-size top-K rules. (Done in the dossier on 6 October.)
5. **The cost premise is partly the wrong way round.**
   - Our 4B judge took about 1 hour to score 9,788 rows; one training job takes 72–102 minutes.
   - Xiao and Aranguri report the LLM judge costing more than LESS and probe attribution.
   - Charge every signal its measured cost, and report a cost–regret curve.
6. **A better headline:** "how many training runs attribution is worth, in each kind of data". Pre-register a secondary hypothesis on side effects (over-refusal), which content classifiers cannot see.

## 2. Novelty map (component by component)

| Component | Status | Closest evidence |
|---|---|---|
| Decision framing with regret | Partly done | DataDecide §2.3: decision accuracy against FLOPs. It has no regret, constraints, attribution or safety. |
| S+ vs S− at matched compute (S− buys more runs) | **Not found** | Ivison et al. §4.3 charges selection FLOPs against training on more data. Xiao and Aranguri give dollars per ranking method. None spends attribution's cost on pilot runs instead. |
| Cheap inputs: classifier, short runs, metadata | Partly done | **Classifier baselines:** Pan, DATE-LM, GradShield, DataShield, Xiao and Aranguri. **Short runs as selectors:** DataDecide and ADMIRE-BayesOpt, for pretraining mixtures only. **Na et al.** (2410.15661) estimate removals by training on parts and merging. **Metadata:** Xiao and Aranguri, removal by source. The three together, for safety edits: not found. |
| Menu with keep-the-data (a0), removals, rewrites, additions | Partly done | Luo (delete, upweight, aligned or opposed rewrite); Xiao and Aranguri (filter, label switch, source removal); Infusion (2602.09987). Choosing among edit types with a0 as a valid option: not found. |
| Feasibility limits on utility and over-refusal | Partly done | GradShield's threshold meets safety and utility targets but does not measure over-refusal. Luo Table 2: influence-selected aligned rewriting raised WJB-harmful from 0.792 to 0.880, but XSTest fell from 0.516 to 0.252. This is reported as a trade-off, not a constraint. |
| Training-seed replication | Partly done | Weckbecker (10 seeds) and GradShield (5 seeds, one task). The closest comparisons replicate inference runs or prompts, not training runs. |
| Frozen rule; held-out menus, groups, prompts, seeds | Not found | Procedural: adds credibility, little novelty on its own. |
| "Too close to call" reporting | Not found | Procedural. |
| Full cost accounting with setup and amortization | Partly done | Costs are reported in many papers (Xiao and Aranguri, GradShield, LARF and DataShield, DATE-LM, Bergson). No decision comparison charges setup cost and spreads it over decisions. |

**Pan et al.** reported ASR, on homogeneous data only, from one training run, with no compute reported:

| Data | No filter | WildGuard filter | DRA filter |
|---|---|---|---|
| ToxicChat | 33.3 | 29.0 | 26.0 |
| XSTest-Response | 73.0 | 50.0 | 43.0 |

With our round-1 seed noise (an SD of about 5 of 72, about 7 points), a 3-point gap from one training run is not informative.

## 3. Contribution statements (ranked)

- **B1, the most defensible claim; for the grant and a workshop paper.** Prior work scores attribution by how well it ranks unsafe training data, usually from one training run and without charging its compute. We test attribution as an input to a decision. At matched total compute, does adding it to a selector that already uses classifier scores, representation similarity and short pilot runs pick better fixes (keep, remove or rewrite)? The fixes must stay within utility and over-refusal limits, with fresh training seeds and held-out menus. We report where it helps, where it hurts, and where the evidence cannot separate the options.
- **B2, the most interesting to main-track reviewers; build the study so it can be claimed.** We measure what attribution is worth in compute: how many extra pilot or full runs a selector without attribution needs to choose as well. We map this across kinds of data that differ in what classifiers can see (overt, look-alike, benign-looking), including after its setup cost is spread over many decisions.
- **B3, the most novel and possibly null; pre-register as secondary.** Classifiers find what to fix but cannot say what a fix will break. Does attribution predict an edit's side effects (over-refusal, lost capability) well enough to change which edit is chosen, compared with pilot runs at matched compute?

| | Defensibility | Main-track interest | Safety-workshop interest |
|---|---|---|---|
| B1 | 1st | 3rd | 2nd |
| B2 | 2nd | 1st | 3rd |
| B3 | 3rd | 2nd | 1st |

## 4. The five strongest reviewer objections, and what makes each answer hold

1. **"Pan, DATE-LM and Xiao and Aranguri did this."**
   - **Answer:** they compare rankings or single filtering runs. None charges attribution against pilot runs. Their conclusions disagree by the kind of data.
   - **Needs:** a seed-replicated copy of Pan's comparison on homogeneous and heterogeneous data, and one documented case where the better ranker makes the worse decision.
2. **"Just an evaluation protocol."**
   - **Answer:** papers like DataDecide, Ivison and DATE-LM changed practice. Ours adds the answer plus a released table of menus × seeds × outcomes × costs.
   - **Needs:** at least 3 kinds of data, runs saved for each, the released table, and a simple selector.
3. **"One setting, one small model, underpowered."**
   - **Answer:** at least 5 seeds per option, and 150–300 runs per kind of data at about $4 each. Generality comes from the kinds of data, a second model family and a 7B check of the ranking.
   - **Needs:** a minimum detectable difference stated from v2's noise.
4. **"The classifier finds injected data trivially, and where it cannot, classifiers already win."**
   - **Answer:** v2 is the D ≈ 0 anchor. The informative cases are where cheap signals err:
     - benign-looking degrading data: DataShield says LlamaGuard, MD-Judge and OpenAI Moderation miss it. In GradShield's Identity-Shift, LlamaGuard's ASR is 0.53 against GradShield's 0.01;
     - mixed contamination;
     - edits that differ in side effects.
   - **Needs:** classifier precision and recall for each kind of data, a rule fixed in advance, and every kind of data reported.
5. **"Compute matching is arbitrary; inline attribution costs about 0."**
   - **Answer:** report the whole curve at measured costs, with the classifier charged too. Nautiyal's 1% covers training overhead only, not queries or scoring, and reports near-zero LDS for LoRA fine-tuning. EK-FAC and SOURCE cost several training runs (Bergson).
   - **Needs:** measured costs including setup, and the break-even number of decisions N*.

**Also expect "your selector S decides the result".** Make the main selector fixed-budget successive halving with a feasibility screen, and use Bayesian optimization only as a sensitivity check.

## 5. Design changes, in priority order (subagent's cost estimates at about $4 per full run)

1. **Smallest decisive checks first ($0–15):**
   - classifier recall and precision on v2's injected rows (from the auditor file, after the lead's selection is final);
   - Qwen3Guard against RepSim/DRA against LoRA gradient similarity on an existing a0 checkpoint: rank correlation, top-K overlap and timings.

   **These are the go/no-go for the expensive study.**
2. **Fix the strawman (about $25):**
   - add a threshold rule that removes only rows judged Unsafe;
   - reword the grant claim (done 6 October).
3. **Kinds of data (about $800–1,000 each, with confirmation):**
   - R1: v2, the anchor;
   - R2: ToxicChat-Het with the harmful rows editable;
   - R3: benign-looking degrading data (Identity-Shift style; not chosen with the attribution family being tested);
   - R4 (optional): mixed.

   The confirmation menus need sealed contamination drawn by the same rule. **In v2 as drafted, the held-out groups have none.**
4. **Cost curves and amortization (about $80 per kind for pilot runs):**
   - replay at 5–6 budgets;
   - report runs saved and N*;
   - use different seeds for pilots and outcomes, because the shared seed shift (R = 3.3) would leak into the pilots.
5. **Cheap and expensive attribution:** RepSim, DRA and LARF-style filters as cheap, charged at their cost. Gradient attribution at two prices: inline LoRA TracIn-style, and EK-FAC or SOURCE through Bergson.
6. **A seed-replicated Pan replication (about $250 per setting):** 4 arms × 16 seeds. Detecting Pan's 3-point gap would need about 80 seeds per arm; the 7-point gap needs about 16. **This is the cheapest publishable result.**
7. **Selector P:** spend pilot runs where the classifier and attribution disagree.
8. **Realistic metadata (free):** source, generator and length, with contamination spread over several sources.
9. **A second model family and scale ($1.5–2k):** OLMo-2-1B on two kinds of data, and a 7B check of 3–5 options.

**Budget (estimates):**
- items 1–7 for three kinds of data: **about $3–3.5k**;
- with item 9 and a human audit: **about $5.5–7k**;
- with $14–20k: a fourth kind of data (emergent misalignment or more benign-looking data) and more seeds;
- **the current balance covers only items 1–2.**

## 6. Kill criteria

| Finding | Consequence | Cheapest check |
|---|---|---|
| A paper already charges attribution against more pilot runs | The core gap is gone (B2 and B3 may survive) | Search again before submitting; read Jaburi et al. in full and DATE-LM App. D.9 |
| Attribution's ranking ≈ the classifier's or RepSim's in every kind of data | No information to add | Item 1 |
| S− regret is within the margin in every kind of data | No room; publish a short negative | Replay on the development tables |
| Pilot runs on separate seeds reach ≥ 90% decision accuracy at ≤ 1/3 of a run per option | Attribution can win only if almost free | Correlate pilots with full runs |
| Best and second-best options cannot be separated in most menus | Selectors cannot be compared affordably | v2 plus the first development table |
| Held-out menus have no contamination | The confirmation tests different data | The v2 design (confirmed: they have none) |
| The threshold removal rule does not backfire | Drop the backfire pitch | Item 2 |
| EK-FAC or SOURCE costs more than one decision's budget | Limit claims to cheap attribution | Item 1 timings |

## 7. Positioning statements

**Introduction paragraph:** Training-data attribution is increasingly proposed for curating fine-tuning data for safety. In homogeneous data, it finds unsafe examples better than moderation classifiers do (Pan et al.). When the data contain safety-aligned look-alikes, it does worse (DATE-LM). It can also guide edits that change behaviour more than deletion does (Luo et al.). These studies ask whether attribution ranks examples well. Practitioners ask a different question: is a fix chosen with attribution better than one chosen by spending the same compute on cheaper evidence, such as classifier scores, representation similarity and short pilot runs? And fixes can cost capability or cause over-refusal. Existing evaluations rarely charge compute. They replicate inference rather than training, and they do not count keeping the data as a valid choice. We test attribution as an input to a choice among data edits under limits on utility and over-refusal. We use matched total compute, training-seed replication, held-out menus and an explicit "too close to call" result. Across kinds of data that differ in what classifiers can see, we measure how many training runs attribution is worth, and when.

**Grant (3 sentences):** Teams that fix fine-tuning data for safety can use cheap signals, such as safety classifiers and short trial runs, or an expensive one, training-data attribution, but no study measures which signal leads to better fixes for the money. Using replicated training runs and held-out confirmation, we will measure how often each signal picks the safest fix that keeps capability and avoids over-refusal, at matched compute, both where classifiers can see the problem and where they cannot. The result will be an open benchmark and a practical rule for when attribution is worth paying for.

## 8. Papers to add to the citation list (from the review)

- **Xiao and Aranguri**, "Probe-Based Data Attribution: Discovering and Mitigating Undesirable Behaviors in LLM Post-Training", [arXiv 2602.11079](https://arxiv.org/abs/2602.11079), 2026. The closest on costs and edit types.
- **Jaburi et al.**, "Mitigating Emergent Misalignment with Data Attribution" (already listed). Attribution filtering matched or beat WildGuard (as reported by Bergson §6.2).
- **Bergson**, an open-source attribution library, [arXiv 2606.11660](https://arxiv.org/abs/2606.11660), 2026.
- **Concept Influence**, [arXiv 2602.14869](https://arxiv.org/abs/2602.14869), 2026.
- **Infusion**, [arXiv 2602.09987](https://arxiv.org/abs/2602.09987).
- **Na et al.**, [arXiv 2410.15661](https://arxiv.org/abs/2410.15661).
- **IProX**, [arXiv 2602.17835](https://arxiv.org/abs/2602.17835).
- Multi-indicator weighting with in-context-learning proxies, [arXiv 2605.09665](https://arxiv.org/abs/2605.09665).
- In-Run Data Shapley (ID not checked).

## 9. Limits of the review (the subagent's own list)

- **Not verified:**
  - Jaburi et al.'s full text (OpenReview showed a bot check);
  - Distributional TDA beyond its abstract;
  - DATE-LM App. D.9;
  - Luo's exact XSTest metric;
  - LARF's timings (from a search snippet only);
  - TRAK's compute figure and In-Run Data Shapley (from memory);
  - Pan et al.'s venue. General Implementation found it listed as an ICML 2026 poster on the ICML site.
- **Still open:** whether the decision study's confirmation menus will contain contamination. For v2 they do not, by design.
