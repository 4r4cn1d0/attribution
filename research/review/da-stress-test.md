# Devil's Advocate stress test

Seat: DA. Target: the research proposal dated 24 September 2026, not a completed experiment. Mode: standard. `NOT_CALIBRATED`. `criteria_binding_unavailable`.

Provenance: this report was committed without reading peer reviews or panel literature notes. Actual model/provider metadata and accountable human identity are unavailable. Role separation does not establish independent errors. No venue-specific criteria were bound; the judgements below concern the proposal's own scientific objectives, not official ICML alignment.

## Criterion judgements

| Criterion | Source | Judgement | Evidence | Scope / decision bearing |
|---|---|---|---|---|
| Specific contribution beyond interval wrapping | Proposal, Recommendation | PARTLY_MEETS | text: L9, "a confidence-interval wrapper alone would be insufficient" | Objective is clear; distinguishing mechanism remains unspecified. Bears on novelty. |
| Useful reduction in retraining | Proposal, working question | NOT_ASSESSED | text: L11, "using substantially fewer retraining runs than direct estimation" | Requires measurements; counterexamples below identify falsifiers. |
| Meaning of a reliable decision | Proposal, Formal target | PARTLY_MEETS | equation: L43, Delta(F,q) | Mean effect is well defined; application must honor that scope. |

The proposal correctly distinguishes finite deletion from infinitesimal influence, equivalence from failure to reject, and retraining from unlearning. Those distinctions prevent several easy but invalid attacks. Its explicit stop criteria are appropriate for a proposal.

## Strongest counter-argument

The project might deliver a statistically valid procedure without discovering anything specific to attribution. Bias-correcting abundant predictions with scarce true outcomes already underlies [prediction-powered inference](https://arxiv.org/html/2301.09633v4), including nonasymptotic bounded-mean intervals. Allocating evaluations according to surrogate accuracy and cost is established in [multifidelity Monte Carlo](https://epubs.siam.org/doi/abs/10.1137/15M1046472). Applying a valid confidence sequence to each fixed request and assigning error budgets summing to delta supplies the proposed simultaneous decision guarantee: an incorrect declaration implies at least one failed interval. [Howard et al.](https://arxiv.org/abs/1810.08240) provide general confidence-sequence machinery. This composition is mathematically useful, but the target theorem alone does not isolate a new attribution mechanism.

Worse, a predictor that accurately separates deletion groups may explain none of the training-seed variation that the proposed correction must remove. An oracle predicting every request's true mean can still give exactly the same sampling variance as direct retraining. Improving source rankings therefore need not advance the proposed cost saving.

The decisive scientific question is whether cheap, seed-specific information predicts the residual variability of exact retraining sufficiently well to repay its construction, development, multiplicity, and validation costs. A second question is whether an average-effect decision changes a defensible downstream action. Neither follows from the motivational redundancy examples. These are prospective vulnerabilities, not allegations that unperformed experiments failed. The project should earn a larger study through a small falsification experiment on these two links.

## Issue list

### CRITICAL

None identified. No decisive contradiction invalidates the stated algorithm-average estimand; missing experimental results are expected at this proposal stage.

### MAJOR

| ID | Problem and impact | Evidence Anchor | Minimum remedy and falsification test | Confidence |
|---|---|---|---|---|
| DA-M1 | **The identified theorem is generic.** Frozen discovery-selected requests remove the original selection problem conditional on discovery; simultaneous valid intervals then give the stated error control by a union bound. The method could remain a repackaging of standard inference even if every experiment succeeds. | text: L69, "the probability of making any incorrect material/negligible-effect declaration is at most delta" | Specify the non-generic contribution before expanding the benchmark. Compare the same predictor under an off-the-shelf residual-correction plus confidence-sequence procedure. If performance and guarantees coincide, abandon the algorithmic novelty claim or establish a substantial empirical contribution instead. | 5/5: direct reduction of the stated theorem; no exhaustive novelty claim. |
| DA-M2 | **Across-request accuracy does not imply within-request variance reduction.** For request j, let Y(j,r)=mu(j)+eta(r), with bounded zero-mean noise, and C(j,r)=mu(j). The predictor is perfect for all request means, yet Var(Y−C)=Var(Y). Repeating its constant predictions cannot reduce uncertainty. A surrogate generated only from one trained checkpoint does not automatically supply the required seed-specific covariate. | text: L63, "If a surrogate C_r tracks the true effect Y_r across seeds" | Define how C_r is generated for a previously unseen seed and price every required training run. Measure within-request residual variance on independent seeds, separately from correlations across requests. Reject the cost-saving premise if strong predictors only explain differences between requests. | 5/5: explicit counterexample; practical prevalence remains unknown. |
| DA-M3 | **Near-threshold auditing can oppose the objective of answering many requests cheaply.** In a noisy mean problem, resolving gap g from a decision boundary commonly requires order 1/g² samples. A bank with many easy requests and a few nearly boundary-valued requests can exhaust the budget on the latter. Uniform/random allocation alone cannot distinguish a new advantage from ordinary adaptive sampling. | text: L62, "Allocate actual retraining to cases near decision thresholds" | Compare against direct retraining with confidence sequences, early stopping, identical reference reuse, and a policy prioritizing expected decisions per unit cost. Include a deliberately mixed easy/hard bank and cap unresolved cases. Count surrogate construction and development runs. Falsifier: the advantage vanishes against this direct adaptive baseline. | 4/5: standard noisy-mean scaling; exact behavior depends on allocation. |
| DA-M4 | **A correct negligible mean can conceal a material effect on every trained model.** Let paired score differences be +0.4 and −0.4 with equal probability. Delta=0, although every paired realization exceeds epsilon=0.1 in magnitude. Thus a valid negligible declaration need not support an action concerning the deployed model. The proposal acknowledges average scope, but its downstream decision use remains underspecified. | text: L45, "This is an algorithm-average finite deletion effect" | Name an action whose loss depends on the mean. Label outputs explicitly as mean-effect declarations and test seed-sign reversals. If the intended action concerns individual models, change the target to an appropriate distributional or conditional quantity and budget its estimation; this is a substantive redesign. | 5/5: bounded mathematical counterexample; relevance depends on intended action. |

Severity here concerns the central proposed contribution; it does not invoke an unverified publication norm. All remedies require author choice; none is represented as accepted or completed.

## Cost check and alternative path

For independent cheap and residual sample streams, Var(mu_hat)=Var(C)/m+Var(Y−C)/n. This is not automatically smaller than direct Var(Y)/k at equal cost. A predictor requiring a fresh full-data training run per seed may have a substantial marginal cost even when its attribution calculation is fast. Shared full-data references and multiple queries per retrained model must be credited equally to direct estimation. No GPU-hour forecast is defensible before timing the specified recipe.

The economical alternative is direct adaptive paired retraining with abstention. A successful attribution method must beat it, not merely beat fixed-budget direct intervals. My role-bound recommendation is to treat the proposal as a falsifiable feasibility study until it demonstrates seed-level variance reduction and a useful action under the stated estimand. This is a DA recommendation, not a panel decision.
