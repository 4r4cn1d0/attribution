# Perspective Review Report — R3

## Manuscript and reviewer information

- **Manuscript:** *Selective Counterfactual Attribution for Reliable LLM Data Deletion*, research proposal dated 24 September 2026.
- **Reviewed file:** `research/icml-attribution-proposal.md`, 156-line version supplied for this review.
- **Role:** Peer Reviewer 3, cross-disciplinary and practical experiment perspective; statistical decision theory, simulation economics, and deployment utility are the lenses here. This is an adjacent-field assessment, not a claim of personal disciplinary credentials.
- **Provenance:** Same-model role-separated review; exact model configuration and independent runtime/model diversity are unknown. No peer reports were read. No subagents were used.
- **Calibration status:** `NOT_CALIBRATED`

criteria_binding_unavailable

## Overall assessment

**Recommendation: Major Revision of the research plan, followed by a bounded pilot.** This is a proposal-stage judgment. The absence of completed results is not a methodological defect. Any ICML assessment here is informal, not a criterion-bound prediction of acceptance.

**Confidence: 4/5** for the cost-accounting and decision-design concerns; actual attainability of useful savings remains empirical.

The proposal would use attribution predictions, exact retraining audits, and abstention to make decisions about finite deletion effects. Its intended outcome is useful decisions at lower total cost, rather than stronger source rankings alone. This is a worthwhile applied research question with unusually clear limits on what a retain-only reference can establish. The strongest practical features are its recognition of redundant retained support, explicit equivalence decisions, and refusal to substitute an unlearning update for ground truth.

The main unresolved risk is economic: a predictor that is accurate across deletion groups need not reduce variation across seeds for any one group. A seed-specific predictor may also require training or processing another model, making the apparently cheap observations expensive. The proposed correction and audit allocation have close counterparts in prediction-powered inference, multifidelity Monte Carlo, and thresholding bandits; these should be operational baselines before substantial interaction-model engineering. Finally, the average signed effect is useful for recipe-level research but does not directly resolve whether a particular deployed model has been successfully unlearned. I would fund a small learnability and cost screen first, then expand only after the plan identifies a concrete user decision, a cost-positive surrogate, and an advantage over simple statistical alternatives.

## Criterion-bound judgments

No target-criteria authority or binding manifest was provided. The following are informal judgments against the assigned review remit, not venue criteria.

| Dimension | Criterion source | Judgment | Evidence anchors | Rationale | Scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Practical inferential target | Assigned R3 remit; no venue authority | PARTLY_MEETS | equation: line 43; text: line 55, "compare its score with the retain-only reference score" | The reference is soundly motivated, but the operational action and deployed-model target remain separate. | Proposal only | Yes, W3 |
| Total-cost advantage | Assigned R3 remit; no venue authority | PARTLY_MEETS | text: line 63, "If a surrogate C_r tracks the true effect Y_r across seeds" | Cost and within-request correlation are both unresolved. | No measured runtimes or covariance data | Yes, W1 |
| Competing decision procedures | Assigned R3 remit; no venue authority | PARTLY_MEETS | absence: Baselines — expected explicit statistical decision baselines; checked lines 29, 61–69, 98–107 | The stated follow-up has not yet become an experiment comparison. | Targeted primary-source search, not exhaustive novelty adjudication | Yes, W2 and W4 |
| Pilot usefulness | Assigned R3 remit; no venue authority | PARTLY_MEETS | text: line 126, "three seeds are not adequate evidence for tight certification" | Exploratory status is correct; a staged budget and independent continuation are still needed. | Hardware, corpus size, and training duration unspecified | Yes, W5 |

## Strengths

### S1: The retained-support counterfactual is practically meaningful

The proposal correctly distinguishes source deletion from removing all knowledge of a fact. This prevents a system from declaring failure merely because retained sources still support the answer.

**Evidence Anchor:** text: line 35, "a retain-only model can legitimately still answer the fact using the other nine."

### S2: Abstention is evaluated jointly with utility and cost

Decision coverage, false assurances, and compute appear together, while the stop rule rejects a method that costs as much as direct estimation. That is the appropriate practical evaluation unit.

**Evidence Anchor:** text: line 114, "Fraction of requests receiving a decision, plotted against error and compute."

### S3: Ground truth and training policy are treated as part of the intervention

Restarting from the same checkpoint, pairing randomness, and specifying steps versus epochs prevent an apparent deletion effect from silently changing the training recipe.

**Evidence Anchor:** text: line 94, "Specify fixed steps versus fixed epochs: changing this changes the target."

### S4: Constructed semantics are not assumed to be learned semantics

Requiring evidence that the model learned the dependency protects the redundancy and complementarity experiments from becoming tests of the corpus generator rather than the model.

**Evidence Anchor:** text: line 84, "Only interpret a constructed dependency after showing that the model learned it."

## Weaknesses and minimum remedies

### W1: The cheap sampling unit and its break-even cost are unspecified

**Severity:** Major

**Evidence Anchor:** text: line 63, "combine many cheap predictions with fewer exact paired retraining effects."

**Confidence:** 5/5 — direct control-variate algebra and computational accounting.

For a fixed request/query, a single frozen attribution score repeated across seeds is a constant: `Var(Y_r − C) = Var(Y_r)`. High correlation across different deletion requests does not solve this within-request problem. If obtaining `C_r` instead requires the full-data model, its gradient features, or its trajectory for each new seed, that training and feature extraction belong in the cheap-sample cost. Savings may still exist, particularly across a large request bank, but reduced counts of deletion runs alone would not establish them.

**Minimum remedy:** Specify an executable construction of `C_r`, including exactly which trained checkpoints it needs. Report within-request seed correlation and residual variance separately from between-request prediction quality. Compare first-request total cost, marginal cost after preprocessing, and amortized cost across a prespecified number of requests. Give direct estimation the same reuse of full-data reference models. This operationalizes the cost caveat already present at line 65 rather than treating it as an unacknowledged error.

For an independently developed fixed coefficient `lambda`, independent cheap-only and audit seed samples give the following elementary planning calculation:

```text
estimate = lambda * mean(C on m cheap-only seeds)
           + mean(Y - lambda*C on n audit seeds)
variance = lambda^2 * Var(C)/m + Var(Y - lambda*C)/n
cost     = build_cost + m*cheap_seed_cost + n*paired_audit_cost
```

The audit cost includes everything required to obtain both observations. If samples overlap, account for their covariance rather than applying this independent-sample formula. Compare with `Var(Y)/n_direct` at the same total cost. Count preprocessing and exact development labels as well as validation audits. Cost-aware allocation across fidelity levels is established methodology; the unresolved contribution is a useful instance and advantage for this deletion problem. [Peherstorfer, Willcox, and Gunzburger, 2016](https://dspace.mit.edu/entities/publication/f104683d-44c4-40ec-bd06-47502c5c0bfd).

### W2: The strongest simple statistical baselines are not yet executable comparisons

**Severity:** Major

**Evidence Anchor:** absence: Baselines — expected explicit PPI/control-variate and multifidelity allocation comparators; checked lines 29, 61–69, 98–107, 128–130

**Confidence:** 4/5 — primary-source comparison of the proposed estimator and sampling design.

The proposal acknowledges this literature gap at line 29. It nevertheless schedules interaction-aware development before resolving whether standard statistical machinery already delivers the desired improvement. The displayed residual correction is the mean-estimation construction in prediction-powered inference; learning a scalar weight has a direct PPI++ counterpart. This is not evidence that the entire application lacks novelty, but it changes the first comparator to beat. [PPI, §1.3](https://arxiv.org/html/2301.09633v3); [PPI++, §6.1 and Example 6.1](https://arxiv.org/html/2311.01453v2).

**Minimum remedy:** Implement the small comparator set below with identical features, training information, request bank, error target, and compute accounting. Separate gains from the predictor, residual correction, and allocation. Do not equate PPI++'s asymptotic efficiency result with the proposed finite-sample simultaneous sequential guarantee.

| Comparator | Concrete role in this experiment |
|---|---|
| Direct paired mean plus a bounded-mean confidence sequence | Same stopping and multiplicity rules; no attribution overhead. |
| Fixed-weight residual correction, including `lambda = 0` and `lambda = 1` | Reveals whether the main gain is simply an ordinary control variate. |
| Development-tuned scalar control variate / PPI++ mean estimator | Adapts to unhelpful predictions; freeze tuning before a finite-sample validation experiment. |
| Two-fidelity cost-aware sample allocation | Uses development estimates of covariance and cost to choose cheap versus exact samples. |
| Direct thresholding allocation | Tests whether smart retraining allocation alone captures the gain. |

For adaptive acquisition, *Active Statistical Inference* already combines predictions with budgeted acquisition of informative exact labels. Its estimand and sampling assumptions must be translated to seeds within requests; pooling unrelated requests would not automatically certify each request. [Zrnic and Candès, ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html). Time-uniform bounded-mean inference is also established infrastructure. [Howard et al., 2021](https://arxiv.org/abs/1810.08240).

### W3: Recipe-average effect decisions and deployed-model unlearning decisions remain different products

**Severity:** Major

**Evidence Anchor:** equation: line 43 — algorithm-average signed deletion effect

**Confidence:** 4/5 — decision-target analysis; deployment requirements are unspecified.

The stated effect is mathematically clear, and line 45 correctly limits its interpretation. The operational story still needs a choice. A negligible average signed effect can coexist with material effects in individual seeds: a hypothetical `+0.3` in half the seeds and `−0.3` in the other half has mean zero. It therefore cannot alone justify treating a particular model's deletion as behaviorally immaterial. Nor does an accurate estimate of the full-minus-retain effect directly validate the score of a particular unlearned model without the appropriate retain reference and its uncertainty.

**Minimum remedy:** Identify the user and action: for example, a model developer deciding which requests need expensive behavioral auditing, or a researcher estimating a recipe's average sensitivity. State that an effect declaration concerns that action and target. For the downstream study, predefine whether the unlearned model is fixed or averaged over randomness and give it a separate compatibility estimand and joint uncertainty calculation. Preserve direct retain-only references in evaluation even when deploying a surrogate. Counterfactual output matching is already central to Datamodel Matching, making reference-quality assessment a plausible incremental contribution. [Georgiev et al., *Attribute-to-Delete*](https://arxiv.org/abs/2410.23232).

If deployment is the intended headline, add a seed-heterogeneity diagnostic and a prespecified absolute-effect or tail-risk target as a separate analysis. Do not silently replace the signed-mean estimand. A negligible measured effect should not be presented as a decision that a source need not be removed.

### W4: Near-threshold auditing does not automatically optimize the stated decision-coverage objective

**Severity:** Major

**Evidence Anchor:** text: line 62, "Allocate actual retraining to cases near decision thresholds"

**Confidence:** 4/5 — pure-exploration and finite-budget decision framing.

Resolving every difficult request and maximizing the number of correct decisions at fixed cost are different objectives. Near-boundary means can consume most of the budget while remaining undecided; easier requests may deliver more decisions per run. In thresholding bandits, distance to the threshold governs problem difficulty, and APT supplies a strong simple allocation comparator. Its fixed-budget classification guarantee is not itself the proposal's abstention guarantee. [Locatelli, Gutzeit, and Carpentier, ICML 2016, §2](https://proceedings.mlr.press/v48/locatelli16.pdf).

**Minimum remedy:** Choose the primary objective before allocation development. Compare uniform allocation, direct APT-style allocation, and a simple development-estimated cost-to-decision ordering, all using the same valid declaration rule. Adapt the comparator to the two boundaries `−epsilon` and `+epsilon`; label the adaptation rather than claiming the original theorem directly applies. Freeze the request bank and disclose the fraction near either boundary. Report per-family decision coverage so success on easy requests cannot conceal universal abstention on structured or targeted deletions.

### W5: The 75-run screen is sensible exploration but does not budget the next decision-bearing step

**Severity:** Major

**Evidence Anchor:** text: line 126, "24 deletion configurations with three paired seeds, giving approximately 75 training runs"

**Confidence:** 4/5 — experimental budget and effective replication analysis.

The arithmetic is correct: `3 × (24 + 1) = 75`. The authors explicitly acknowledge that this is not certification. The unresolved planning risk is spending nearly all initial effort across configurations before establishing a cost-positive within-request surrogate, while fresh-seed correction, predictor development, and ground-truth evaluation still need additional runs. Shared full-data references also induce dependence among request errors. Seventy-five trainings are only three independent seed observations for each request, not seventy-five replicates of its mean.

**Minimum remedy:** Stage the spend, with a runtime gate and separate discovery, tuning, and fresh-seed evaluation budgets. Use the small screen below before committing to 24 configurations. Select later seed counts from the decision margin, residual variability, multiplicity, and chosen interval procedure; treat pilot variance estimates as uncertain. Ground-truth classification in the eventual comparison needs its own uncertainty or a sufficiently precise independent reference. A calendar promise cannot be assessed without tokens, update steps, hardware, feature extraction costs, and the number of baseline training jobs; no GPU-hour estimate is inferred here.

## Detailed practical comments

### Assumptions and controls

The explicit assumptions are a fixed checkpoint and recipe, bounded scores, independent validation seeds, a frozen request bank, and an effect threshold chosen in advance. The key implicit assumption is access to cheaply observable features that predict *seed-to-seed* effects for a fixed request. A second is that the number of requests is large enough to amortize preprocessing. Both can be tested before a broad benchmark.

The existing data controls are appropriate. Make the following operational choices explicit in the experiment manifest:

| Control | Purpose |
|---|---|
| Hold out complete entities and all aliases, paraphrases, premises, decoys, and corresponding queries together | Prevents a nominal source-family split from leaking semantically equivalent material into development. |
| Generate attribution-selected groups using discovery seeds, then freeze them | Makes fresh-seed auditing assess the selected request without selecting it again from validation outcomes. |
| Match random deletions on token count, exposure, and source-size profile as well as document count | Separates source structure from the amount of training signal removed. |
| Fix answer length, option ordering policy, and alternative prompts before validation | Tests semantic effects without letting format or prompt selection dominate. |
| Evaluate all queries affected by one deletion run as a correlated batch | Exploits real computational reuse without counting queries as independent training replications. |
| Retain unchanged-model and refusal-only controls | Shows whether the downstream audit can distinguish genuine reference compatibility from simple suppression. |

If there is insufficient budget for complementarity, conflict, natural text, and larger models, keep the first study narrow. Each extension should answer a specific remaining generalization question rather than satisfy a model-size checklist.

### A cheap pilot that can kill the proposed mechanism

This is a proposed screening protocol, not an experiment already performed or a powered confirmation.

1. **Gate 0: Learnability and timing.** On the smallest planned model, time one full-data run, one deletion run, and the chosen predictor's feature construction. Those runs may count toward the next stage if their settings were frozen. Measure checkpoint/feature storage too. Stop expansion if target facts are not learned or measured costs exceed the available budget.
2. **Gate 1: Fifteen-run mechanism screen.** Use four fixed requests: unique-support deletion, one-member deletion from a redundant family, full-family deletion, and a matched irrelevant-source deletion. Three full-data seeds plus four deleted-data runs per seed total 15 trainings. Measure `C_r`, `Y_r`, raw and residual within-request variance, and all costs. Begin with fixed coefficients and a simple gradient predictor; do not fit an interaction model first.
3. **Cheap falsification controls.** Replace `C_r` with a request-specific constant, then shuffle its seed pairing. If improvement survives these controls, investigate request-level pooling, reuse of outcomes, or an evaluation artifact before claiming variance reduction. Also compare direct estimation with the same full-data-reference reuse. Report uncertainty rather than declaring a weak correlation estimate conclusive.
4. **Gate 2: Independent continuation only if justified.** Freeze a coefficient and protocol, choose four analogous requests on held-out entity/source families, and use four fresh seeds: another 20 trainings, for 35 total before optional predictor-training jobs. This remains a falsification and feasibility screen; four seeds cannot establish nominal error rates. Check whether the cost model and residual advantage survive the new seeds and families.
5. **Gate 3: Budgeted main-study decision.** Continue only if the measured cost/covariance range supports useful savings over tuned control variates and direct allocation under the intended request-bank size. Reserve independent evaluation budget and choose the later seed count before scaling configurations or models. If the interval procedure cannot decide at realistic margins within budget, narrow the claim or stop.

The quickest decisive negative result is that the implemented predictor is constant across seeds or costs too much even under optimistic plausible variance reduction. An inconclusive small sample is a reason to constrain further spending, not proof that every surrogate must fail. A positive pilot licenses a larger study; it does not establish the proposed guarantee or algorithmic novelty.

### Practical impact and broader implications

The most credible immediate user is a developer running repeated behavioral audits for a controlled adaptation pipeline with available data and checkpoints. A reusable request bank and many queries per deletion may make the economics favorable. A one-off request against inaccessible pretraining data is outside the demonstrated workflow.

The valuable output is an explicit, scoped statement of behavioral compatibility or insufficient evidence. Source owners should not receive stronger assurances than the selected queries and tolerance support. Show coverage separately for unusual and structured requests, because otherwise a low overall error rate could be achieved while systematically declining precisely the requests that motivate the work. These are reporting and product-scope implications, not claims of legal certification.

## Cross-disciplinary reading priorities

All sources below were checked through primary papers, official proceedings, or the authors' institutional repository on 24 September 2026. This targeted search is not an exhaustive novelty review.

1. [Prediction-Powered Inference — Angelopoulos et al., 2023](https://arxiv.org/html/2301.09633v3): mean correction and assumptions for the labeled/unlabeled sampling units.
2. [PPI++ — Angelopoulos, Duchi, and Zrnic](https://arxiv.org/html/2311.01453v2): tuned mean-estimation baseline and the distinction between asymptotic efficiency and finite-sample certification.
3. [Optimal Model Management for Multifidelity Monte Carlo Estimation — Peherstorfer, Willcox, and Gunzburger, 2016](https://dspace.mit.edu/entities/publication/f104683d-44c4-40ec-bd06-47502c5c0bfd): explicit cost/correlation allocation. Repository abstract inspected; linked technical-report PDF retrieval failed.
4. [An Optimal Algorithm for the Thresholding Bandit Problem — Locatelli, Gutzeit, and Carpentier, 2016](https://proceedings.mlr.press/v48/locatelli16.pdf): simple allocation comparator and boundary-gap difficulty.
5. [Active Statistical Inference — Zrnic and Candès, 2024](https://proceedings.mlr.press/v235/zrnic24a.html): budgeted acquisition informed by prediction uncertainty; proceedings abstract inspected.
6. [Time-Uniform, Nonparametric, Nonasymptotic Confidence Sequences — Howard et al., 2021](https://arxiv.org/abs/1810.08240): sequential inference infrastructure; abstract and author description inspected.

## Questions for the authors

1. What concrete action does a material, negligible, or abstaining declaration change, and is the target a training recipe or a particular deployed model?
2. How is one new `C_r` computed, and which training/feature costs does it incur before any deletion-specific audit?
3. What request-bank size and reuse pattern should define the primary cost comparison: first request, a fixed batch, or an ongoing service?
4. What total measured training budget remains for independent validation and reference estimation after the initial pilot and baseline construction?

## Minor issues

No additional copyedit-level issues are material to this practical review.
