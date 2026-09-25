# Selective Counterfactual Attribution for Reliable LLM Data Deletion

Research recommendation, 24 September 2026. This is a proposed project, not a claim of established novelty or experimental success. Compute and researcher preferences are not yet specified; the plan assumes a small academic GPU budget and prioritizes controlled fine-tuning over full pretraining.

## Recommendation

Investigate **when a training-data attribution estimate is reliable enough to support a particular deletion decision**. Build a method that predicts the counterfactual effect of deleting a source group, attaches an uncertainty interval validated against real retraining, and abstains when evidence is inadequate.

The intended contribution combines training-data attribution (topic 3) with faithful evaluation (topic 4). Unlearning is the downstream application. A strong submission would establish a specific failure mode, develop a computationally useful remedy, and demonstrate reliable decisions at lower retraining cost. A generic attribution benchmark, another group-summed influence score, or a confidence-interval wrapper alone would be insufficient.

Working question: **Can we obtain reliable, selective predictions of the effects of structured and attribution-selected deletions, using substantially fewer retraining runs than direct estimation?**

## Why the obvious versions are already occupied

| Prior work | Relevant existing contribution | Required distinction |
|---|---|---|
| [DATE-LM](https://arxiv.org/abs/2507.09424), 2025 | LLM attribution evaluation across data selection, toxicity/bias, and facts; includes counterfactual factual setups and deletion/retraining experiments. | Do not claim the first causal or retraining-based LLM attribution evaluation. Focus on reliability of individual deletion decisions, selection effects, and uncertainty. |
| [Attribute-to-Delete / Datamodel Matching](https://arxiv.org/abs/2410.23232), ICLR 2025 | Uses attribution to predict retain-only model outputs and trains an unlearned model toward those predictions. | Audit whether a predicted counterfactual is trustworthy for a particular request; do not present attribution-to-unlearning as new. |
| [f-INE](https://arxiv.org/abs/2510.10510), ICLR 2026 | Defines influence through hypothesis testing under training randomness and gives a scalable estimator. | Distinguish inference about a specified finite deletion effect from its influence functional; compare uncertainty and decision quality fairly. |
| [Generalized Group Data Attribution](https://arxiv.org/abs/2410.09940), 2024 | General group attribution framework and computational improvements. | Grouping is infrastructure, not the novelty. |
| [GUDA](https://arxiv.org/abs/2601.22651), 2026 | Uses unlearning to approximate group counterfactuals for diffusion attribution. | Do not use unlearning as an unquestioned ground-truth oracle when evaluating unlearning. |
| [GRASP](https://arxiv.org/abs/2606.06892), 2026 preprint | Interaction-aware subset prediction, feature sketches, and a confidence-based development-protocol selection procedure. | The proposed target is a request-level decision guarantee and selective validation cost, not subset prediction or interaction awareness alone. |
| [ProxySPEX](https://arxiv.org/abs/2505.17495), 2025 | Includes nonlinear datamodels and redundant/synergistic training-data interactions. | Do not claim that modeling interactions is itself new. |
| [How Faithful Is Trajectory-Based Data Attribution?](https://arxiv.org/abs/2605.18814), 2026 preprint | Analyzes attribution error, addresses AdamW mismatch, and derives an error proxy. | Include optimizer-aware methods and error proxies; distinguish a practical decision audit from another approximation-error taxonomy. |
| [HANKER](https://arxiv.org/abs/2502.18810), 2025 | Expands unlearning audits and studies redundancy between forget and retain knowledge. | Redundancy is a controlled stressor, not a standalone discovery. |

Additional relevant work: [STRIDE](https://arxiv.org/abs/2606.05165) uses steering operators and sparse recovery for scalable attribution; [DataDignity](https://arxiv.org/abs/2605.05687) studies source-support retrieval and explicitly distinguishes its scores from definitive causal responsibility; [Auditing Language Model Unlearning via Information Decomposition](https://arxiv.org/abs/2601.15111) examines residual information in representations. These are different targets and should not be collapsed into a single leaderboard without explanation.

The searched literature supports this as a candidate gap. It does not establish that no prior work solves it. A focused follow-up on selective inference, prediction-powered inference, multifidelity estimation, and sequential experimental design is necessary before claiming algorithmic novelty.

## The motivating example

A fabricated fact appears in ten paraphrased training documents. Deleting one document may have almost no effect, while deleting all ten can matter substantially. A small leave-one-out effect can be correct; the error is treating it as evidence about a different, joint intervention.

Conversely, if a deletion request concerns only one source, a retain-only model can legitimately still answer the fact using the other nine. Knowledge recall alone cannot distinguish failure to delete that source from legitimate learning from retained sources. Evaluate the unlearned model against the defined retain-only reference.

A third case is answer suppression: a model refuses a direct question while other prompts or output probabilities still differ from the retain-only reference. Refusal is an experimental control, not proof of successful deletion.

## Formal target and scope

Fix an initial checkpoint, training algorithm A, optimizer, compute policy, and seed distribution. Let D be the controlled training corpus and F a deletion group. For a fixed query/answer pair q, choose a bounded output statistic s_q(theta), such as a probability over prespecified answer options. Define

    Delta(F, q) = E_r[ s_q(A(D; r)) - s_q(A(D \ F; r)) ].

This is an algorithm-average finite deletion effect, conditional on the starting checkpoint and training recipe. It is not a unique reconstruction of the causal history of a particular sampled model, an infinitesimal upweighting derivative, or a percentage of creative ownership.

Choose a practical effect threshold epsilon before inspecting test results. Return an interval C(F,q) and one of three decisions:

1. The deletion has a material effect, with its supported sign.
2. The deletion has a negligible effect within the chosen tolerance.
3. Evidence is insufficient at the available budget.

The second decision requires an interval wholly inside [-epsilon, epsilon]. Failure to reject a zero-effect null is not evidence of equivalence.

For an unlearned model, compare its score with the retain-only reference score. Report compatibility with that reference on the declared query set and tolerances. Matching score means does not establish equality of model distributions, erase arbitrary hidden information, or certify every future generation.

## Proposed method: a starting design to test

Use a two-stage system: cheap prediction, then selective independent validation.

1. **Predict candidate deletion effects.** Build a group-aware predictor using a strong attribution baseline and, where justified, interactions. This component should exploit existing methods rather than claim to reinvent them.
2. **Choose informative audits.** Allocate actual retraining to cases near decision thresholds, large or unfamiliar groups, and regions where development data show large approximation error. Compare this allocation with uniform and random allocation at the same total cost.
3. **Estimate and correct prediction error.** A concrete route is multifidelity residual estimation: combine many cheap predictions with fewer exact paired retraining effects. If a surrogate C_r tracks the true effect Y_r across seeds, estimate E[Y] using E[C] + E[Y-C]. Account for uncertainty in both estimates. Learn any scaling coefficient on independent development data or cross-fit it.
4. **Keep inference valid under selection.** Freeze a finite request bank using discovery data, then validate on fresh training seeds. For adaptive stopping, use valid time-uniform intervals; for multiple requests and queries, account for multiplicity. A later extension could allow an evolving request stream with an explicit error budget.
5. **Abstain when necessary.** Do not extrapolate a guarantee from random deletions to arbitrary targeted deletions without assumptions. A new group may need its own audit evidence. If the surrogate does not reduce residual variance enough to repay its cost, use direct estimation or report insufficient evidence.

The hard contribution is a useful cost-reliability tradeoff: obtaining many correct decisions with substantially less retraining. Standard concentration bounds by themselves are not an ICML contribution. Neither is a method that achieves low error by abstaining on everything.

One possible theorem target, not an established result: for a fixed finite request/query bank, bounded statistics, independent validation seeds, and a valid sequential construction, the probability of making any incorrect material/negligible-effect declaration is at most delta. A second target would characterize the conditions under which residual correction reduces training cost. Distribution-free guarantees for arbitrary unseen deletion groups must not be asserted.

## Experimental design

### Controlled data

Construct a modest corpus of fictional entities and facts so target knowledge is deliberately introduced during the controlled stage. Randomize entity names and labels; verify the initial checkpoint's behavior. Include four regimes:

- Unique support: one source supplies a fact.
- Redundancy: the same fact appears in 2, 5, or 10 independently phrased documents.
- Complementarity: two source groups provide separate premises required to answer a query.
- Conflict: source groups support competing answers, with controlled exposure counts.

Cross answer format with semantics and include matched decoys. A recent preprint, [Form Over Content in Gradient-Based Data Attribution Methods](https://arxiv.org/abs/2609.19589), makes answer format a particularly relevant control. Use a second natural-text corpus with controlled replacements to test whether findings survive beyond synthetic templates.

Ground truth comes from retraining interventions, not from the corpus generator's declaration that a source is relevant. Only interpret a constructed dependency after showing that the model learned it. Distinct dependencies should not be pooled to hide failures on difficult regimes.

### Deletion requests

Use matched-size random deletions, single-source deletions, complete paraphrase-family deletions, and attribution-selected top-k groups. Separate development and test requests by entity/source family. Report calibration and error for each family, including a held-out family as an empirical stress test.

### Models and retraining

Start with a roughly 100M–500M parameter language model, using full updates on the controlled corpus. A larger 1B–3B experiment can establish transfer if compute permits. An optional 7B–8B parameter-efficient experiment is supporting evidence about that adaptation procedure only.

For every reference deletion run, restart from the same pre-adaptation checkpoint. Pair seeds and shared example ordering where possible to reduce variance, while ensuring both arms follow the declared training policy. Specify fixed steps versus fixed epochs: changing this changes the target. Include a sensitivity check for the alternative policy.

Never call an unlearning update an exact retrain, nor extrapolate fine-tuning findings to all pretraining documents. A small model trained from scratch can provide a clean supplementary provenance test.

### Baselines

- Random, lexical retrieval, and representation similarity for diagnostic comparisons.
- Gradient similarity/LESS, TRAK, and EK-FAC where computationally feasible.
- Linear datamodels, a group-aware baseline, and an interaction-aware baseline such as GRASP.
- f-INE and an optimizer-aware trajectory method when compatible implementations are available.
- Direct paired-retraining confidence intervals, plus uniform-budget and random-budget audit allocation.
- Simple calibrated versions of each strong predictor; these are essential to test whether the proposed method contributes beyond a wrapper.

As a downstream unlearning experiment, compare retain-only retraining, an unchanged model, a refusal-only control, gradient ascent with retain regularization, and representative modern unlearning methods. Include a DMM-style counterfactual predictor if feasible. Match utility and disclose all compute costs.

### Primary measurements

- Finite-deletion effect error and sign error, stratified by intervention family.
- Empirical interval coverage and interval width.
- False material-effect and false negligible-effect declarations.
- Fraction of requests receiving a decision, plotted against error and compute.
- Actual retraining count, GPU hours, storage, and the cost of cheap predictor construction.
- For unlearning: divergence from the retain-only reference on held-out prompts, utility on retained knowledge, and appropriate extraction or relearning stress tests.

Report rank correlation/LDS and source retrieval scores as secondary metrics. They cannot by themselves validate an effect magnitude or a threshold decision. Compute uncertainty over independent training runs and source groups; thousands of paraphrases do not constitute thousands of independent models.

## First two weeks and stop criteria

This is a planning target, not a measured runtime estimate.

**Days 1–3:** Inspect the closest method implementations, pin the estimand and compute policy, build unique-support/redundancy data, and time one training run. Verify learnability before expanding the corpus.

**Days 4–7:** Use about 24 deletion configurations with three paired seeds, giving approximately 75 training runs including three full-data references. This is an exploratory experiment for effect size and cost; three seeds are not adequate evidence for tight certification. Compare simple attribution, a strong gradient baseline, and direct deletion effects.

**Days 8–10:** Add an interaction-aware predictor and test whether strong source rankings or LDS can coexist with wrong practical deletion decisions. Check whether the result survives equal compute, consistent optimizer assumptions, and semantically matched decoys.

**Days 11–14:** Prototype independent residual correction and audit allocation. Measure whether it beats an ordinary interval/calibration baseline at equal cost. Use findings to determine the main study's seed count and scale.

Continue only if there is a reproducible decision failure under a defensible target, and the remedy improves the fraction of correct decisions at equal cost. Pivot or stop if strong existing methods already solve the problem, if the result depends on comparing different estimands, if synthetic facts are not learned, or if the audit costs essentially as much as direct retraining without adding useful information.

The most convincing headline figure would show decision error versus fraction of requests answered at fixed compute, alongside results under random, redundant, and attribution-selected deletions. A reduction in false assurances with useful decision coverage is more valuable than a marginal gain in source retrieval.

## Why not prioritize the other original ideas

Copyright percentages conflate a chosen allocation rule with causal effect and require a much sharper technical target before becoming a sound ML project. A universal claim of zero future influence cannot be justified by finite empirical tests. Broad multimodal attribution at massive pretraining scale introduces several expensive problems before the scientific claim is isolated. A human-facing contestability UI can be useful later, but the core research question here can be evaluated without a user study.

## Retrieval provenance

Scope: targeted novelty reconnaissance, not a systematic or exhaustive review. Access date: 24 September 2026. Sources: arXiv API plus web searches locating original arXiv papers, official proceedings/OpenReview pages, and author-maintained repositories. Preprint results are treated as authors' claims, not independently reproduced findings.

Reproducible broad API request:

    Endpoint: https://export.arxiv.org/api/query
    search_query=(ti:"data attribution" OR ti:"unlearning evaluation") AND submittedDate:[202501010000 TO 202609242359]
    max_results=30
    sortBy=submittedDate
    sortOrder=descending

The API reported 73 results; the newest 30 were retrieved and parsed with the paper-lookup skill's arxiv_atom.py. This was an intentional bound; the remaining 43 were not fetched. Targeted title and concept searches supplemented that page, including older foundational work.

Representative supplementary queries: `DATE-LM data attribution evaluation LLMs benchmark 2025 arxiv`; `"data attribution" "confidence intervals"`; `"data attribution" "conformal"`; `"training data attribution" "hypothesis testing"`; `"data attribution" "interactions" datamodels`; `"unlearning" "Datamodel Matching"`; `"unlearning" "redundant" "language models" evaluation`.

Some explicitly versioned HTML requests returned unavailable/error pages; accessible original-paper versions, abstracts, and proceedings were used instead. Full text was inspected for the central comparisons with DATE-LM, f-INE, GRASP, DataDignity, and the causal-unlearning-testing perspective. Several secondary references were assessed from abstracts only. Raw API output and parsed metadata accompany this memo.
