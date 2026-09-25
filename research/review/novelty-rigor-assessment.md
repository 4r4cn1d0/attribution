# Novelty and rigor assessment

**Proposal:** *Selective Counterfactual Attribution for Reliable LLM Data Deletion*  
**Review date:** 24 September 2026  
**Assessment:** Major revision of the research design before a main study. This is an advisory proposal review, not a conference decision.

The question is useful, but the current design has **unestablished novelty and an unresolved cost-saving mechanism**. The initial recommendation was too optimistic about the space left by existing statistical methods. The appropriate next investment is a bounded feasibility study, not the full proposed benchmark. Nothing reviewed establishes that the research direction is impossible or that a completed paper would be rejected.

The strongest existing parts are the explicit finite-deletion estimand, the distinction between equivalence and failure to reject, and the requirement to test against retain-only retraining. The main weaknesses are substantive: much of the inference architecture already exists; the cheap predictor may provide no relevant variance reduction; and the deployment interpretation needs tightening. These conclusions trace to the five role-separated reports linked below. No LLM training experiments were run for this review.

## 1. Novelty: what is already occupied

| Proposed ingredient | Closest verified antecedent | Consequence for this project |
|---|---|---|
| Attribution reliability under training randomness | [Bayesian TDA, NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/hash/ca774047bc3b46cc81e53ead34cd5d5a-Abstract-Conference.html) studies distributions, means, and uncertainty of leave-one-out effects. | Uncertainty in individual attribution estimates is an existing research problem. |
| Correcting a cheap prediction using expensive outcomes | [PPI++](https://arxiv.org/html/2311.01453v2) supplies prediction-plus-residual mean estimation and optimized weighting. | The identity E[C] + E[Y−C] is infrastructure, not an original estimator. |
| Selectively acquiring expensive evidence | [Active Statistical Inference, ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html). | Uncertainty-directed auditing needs an explicit comparison with existing acquisition procedures. |
| Sequential validity with predictive assistance | [Prediction-Powered E-Values, ICML 2025](https://proceedings.mlr.press/v267/csillag25a.html). | Adding sequential validity does not by itself differentiate the method. Exact assumptions still matter. |
| Sending uncertain cheap explanations to expensive computation | [Selective Explanations, NeurIPS 2024](https://arxiv.org/html/2405.19562). | The architecture has an antecedent; its feature-attribution target differs from finite deletion effects. |
| Finite-subset interventions under random training | [f-INE, ICLR 2026](https://openreview.net/pdf?id=TwkcMNACXo). | Distinguish a bounded mean contrast from distributional distinguishability. Finite deletion itself is not the distinction. |
| Attribution predicting retain-only behavior | [Attribute-to-Delete / Datamodel Matching, ICLR 2025](https://arxiv.org/abs/2410.23232). | Attribution-assisted unlearning and counterfactual output prediction are established. |
| Shared vector observations and cost/correlation allocation | [MultiPPI, ICLR 2026](https://arxiv.org/abs/2603.27414) estimates linear functionals from jointly observed subsets, allowing non-additive costs. | Merely sharing reference models or query vectors is not an established novelty claim. |
| Adaptively relying less on a bad proxy | [R-AutoEval+, NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/hash/e8e81e35728f7559e42ceb265e104d36-Abstract-Conference.html). | Safe proxy fallback has an antecedent. Its finite-sample reliability and asymptotic efficiency results must be distinguished. |

**Closest composed baseline:** an existing group/deletion predictor, existing prediction-powered sequential inference, an error budget across the fixed request bank, and direct retraining when prediction is unhelpful. This is a construction inferred from the literature, not a claim that a single published paper already solves the full proposed task. It reproduces most of the proposed interface.

The residual opportunity is to demonstrate something consequential about **the cost of reliable decisions for structured LLM deletions**, beyond that composition. Grouping, redundancy, abstention, confidence intervals, or strong attribution rankings alone do not establish the contribution. See R2-W1–W2 and EIC-W1.

A post-commit check further narrows the proposed cost-theory route. [PROBE](https://arxiv.org/abs/2607.06879), a July 2026 preprint, already learns proxy correlation and certifies residual variance for best-arm identification, under restrictive independent bivariate-Gaussian assumptions with known proxy means. MultiPPI's observation model also accommodates shared-cost vectors. Joint threshold decisions for dependent retraining outputs may still pose a useful problem, but these sources do not establish that it is novel. The [R2 addendum](/Users/spiderishi/Coding/attribution/research/review/r2-late-literature-addendum.md) records exact versus adjacent overlap.

Two citation corrections also matter. f-INE already covers finite subsets; compare its actual estimand fairly. GRASP documents interaction-aware prediction and development freezing, but the inspected version's claimed lower-confidence-bound protocol was not located as an explicit statistical rule with a coverage theorem. This review does not treat that claim as an established deletion-audit guarantee. See R2-W3–W4.

## 2. Rigor: the decisive mathematical check

For a fixed deletion request and query, write the seed-specific exact effect as Y_r and the cheap prediction as C_r. If the predictor gives the same score c for every seed, then

\[
\widehat\Delta=c+\frac{1}{n}\sum_{r=1}^{n}(Y_r-c)=\bar Y_n.
\]

**The prediction cancels exactly.** A predictor could know every request's true mean and still provide no reduction in the sampling variance of this estimator. Good prediction across requests does not imply useful prediction of seed-to-seed deviations within a request. This is an algebraic counterexample, not an observed failure of an implemented method. It is independently identified in EIC-W2, R1-W1, R3-W1, and DA-M2.

The design therefore needs an executable, inexpensive C_r that varies informatively with the training seed. If C_r needs a newly trained full-data model, feature bank, or trajectory, charge those costs. Sharing those artifacts across requests may help, but give direct retraining the same reuse. A constant predictor could still help allocate effort across requests; the cancellation refutes the claimed residual-variance mechanism for that predictor, not every possible allocation benefit.

For a development-frozen coefficient beta, n paired observations, and N independent cheap-only observations from the same seed distribution,

\[
\widehat\Delta=\beta\bar C_N+\overline{Y-\beta C}_n,
\qquad
\operatorname{Var}(\widehat\Delta)=\frac{a}{n}+\frac{b}{N},
\]

where a = Var(Y−beta C) and b = beta² Var(C). If paired and cheap-only costs are c_P and c_C, then under a continuous allocation and excluding setup cost,

\[
\min_{c_Pn+c_CN=B}\operatorname{Var}(\widehat\Delta)
=\frac{(\sqrt{a c_P}+\sqrt{b c_C})^2}{B}.
\]

Compare this with direct estimation's Var(Y)c_Y/B. This standard multifidelity calculation is a useful screening condition; it is not a new result, a stopping-time bound, or evidence that an LLM surrogate will work. Overlapping samples need covariance terms; shared models need bank-level cost accounting. The [arithmetic receipt](/Users/spiderishi/Coding/attribution/research/review/arithmetic-checks.json) contains illustrative calculations only. See R1-W3 and R3-W1.

## 3. What a valid guarantee must say

The proposed signed mean effect is coherent. A conservative finite-bank construction is also available from established tools: freeze requests, queries, tolerances, predictors, and coefficients using discovery data; use fresh validation seeds; build bounded confidence sequences for the cheap and residual expectations; and allocate error budgets summing to delta. Cross-request independence is not necessary for a union bound. Adaptive within-request seed selection requires a justified sampling design, not merely the phrase “fresh seeds.”

For interval [L_j,t, U_j,t], declare positive material effect if L_j,t > epsilon_j, negative material effect if U_j,t < −epsilon_j, and negligible mean effect if the whole interval lies inside [−epsilon_j, epsilon_j]. Otherwise abstain. This can establish

\[
P(\text{any false declaration over the declared bank and stopping times})\leq\delta.
\]

That is a useful safety baseline, but its generic derivation is not the novel theorem. Ordinary fixed-sample/asymptotic PPI++ intervals do not automatically become finite-sample, anytime-valid intervals by repeated inspection or cross-fitting. See R1-W2 and DA-M1; [confidence-sequence foundations](https://arxiv.org/abs/1810.08240).

For a methodological paper, a more substantive target would relate **total training cost** to residual variance, prediction cost, reuse across requests, and distance from the decision boundaries. Near-boundary requests can remain expensive or unresolved. Prioritizing them is not automatically optimal for maximizing the number of decisions at a fixed budget. Compare with equally adaptive direct retraining, not just uniform allocation. See R1-W3, R3-W4, and DA-M3.

## 4. Claims the experiments must keep separate

**Mean effect versus a particular model.** Effects +0.4 and −0.4 with equal probability have mean zero, although each realization is material at tolerance 0.1. The existing proposal acknowledges its mean scope; this is not a contradiction. It is a reason to specify an action for which that mean is useful and to center the title on deletion-effect auditing. A particular unlearned model needs a separately defined compatibility comparison. See EIC-W3, R3-W3, R1-W5, and DA-M4.

**Exact retraining versus an exact expectation.** A retrained model is one observation, not the ground-truth mean. Small reference averages also have uncertainty. Reserve independent reference seeds for a smaller evaluation bank; retain unresolved labels where the reference interval crosses a boundary. Test whole-bank false-declaration rates using repeated full audits in a cheap setting with known or highly precise expectations. Average per-query coverage is a different quantity. See R1-W4.

**Replication versus repeated prompts.** One retraining yields a vector of query outcomes. Those outcomes are useful, but they are not independent training replicates. Shared full-data references also induce dependence across deletion groups. Evaluate costs in training jobs and measured GPU hours, with feature construction, development labels, and reference-oracle evaluation separately disclosed. See R1-W4–W5 and R3-W1/W5.

**Different estimands versus method failure.** A valid singleton, trajectory-local, or distributional attribution score need not predict the same finite-group signed mean. A mismatch can reflect the target rather than a bad approximation. Calibrate comparable methods to the same target; keep diagnostic mismatches explicitly separate. See R2-W3 and R2's overlap matrix.

## 5. A defensible paper route and falsification study

A better working question is: **When does training-data attribution actually reduce the total cost of reliable deletion-effect audits?** This is a candidate research direction, not a newly verified gap.

There are two legitimate routes. A methodological paper needs a concrete seed-dependent surrogate or allocation improvement, with a meaningful advantage over the strongest statistical composition. An empirical-insight paper could establish a consequential, reproducible failure of accepted attribution evaluation, explain when it occurs, and show how an existing method changes practical conclusions. ICML explicitly permits originality through useful combinations and empirical understanding; a new theorem is not a universal prerequisite. [Official reviewer instructions](https://icml.cc/Conferences/2026/ReviewerInstructions). This resolves the difference in emphasis between R1's method-focused theorem recommendation and EIC's broader contribution assessment.

For the method route, the minimum initial comparator set is direct paired retraining with early stopping and shared references; fixed and development-tuned control variates; an existing prediction-powered sequential procedure; and uniform versus cost-aware direct allocation. Add attribution sophistication only after those comparisons expose a specific unresolved problem. Use the same estimand, predictors where applicable, decision rule, information access, and total-cost accounting. See R3-W2 and R2-W1.

Where the proposed improvement uses joint observations, adaptive proxy weights, or learned residual variance, include the relevant MultiPPI, R-AutoEval+, or PROBE mechanism from the addendum. Do not transfer their guarantees outside their assumptions; use them to define a strong comparison and to identify the exact extension, if any.

The following is R3's proposed feasibility screen, not a powered validation or a commitment to run it:

1. Time the smallest model's full-data training, deletion training, and predictor construction; verify that target facts were learned.
2. Freeze four requests: unique support, one member of a redundant family, its whole family, and an irrelevant matched deletion. Three seeds require 15 training runs including shared full-data references. Measure within-request residual variance and all costs.
3. Use constant-predictor and shuffled-seed controls. Apparent within-request variance gains surviving these controls need an explanation before being credited to the proposed mechanism.
4. If the screen is promising, freeze tuning and continue on analogous held-out source families with four fresh seeds: 20 more runs, for 35 before additional predictor-development costs. This remains a feasibility screen; these seed counts cannot establish nominal error rates.
5. Size a main study using observed variability, practical margins, the chosen interval procedure, multiplicity, and the remaining independent evaluation budget.

Proceed only if the measured mechanism supports useful savings over strong direct and generic inference baselines, or if the study exposes a substantial empirical phenomenon worth a different paper. Stop the estimator route if the surrogate is effectively constant, too expensive, or no better than an existing composition at equal total cost. Do not treat an inconclusive small sample as proof that every possible surrogate fails. See R3-W5 and DA-M2–M3.

## 6. Review disposition and traceability

All four primary seats recommend substantial research-plan revision followed by a bounded pilot. DA identifies four Major concerns and **no Critical findings**. No DA Critical finding is therefore left unadjudicated. The synthesis accepts DA-M1/M2 as precise novelty/feasibility objections, DA-M3 as an allocation-comparator requirement, and DA-M4 as a scope requirement rather than an invalidation of the stated mean estimand. Overlap across these model-generated reports is corroboration of the arguments, not five statistically independent votes.

The following source-ordered checklist records the principal revision obligations; it does not represent author acceptance or a work-priority ranking:

| Source findings | Transported severity | Revision needed | Evidence that would resolve it |
|---|---|---|---|
| EIC-W1; R2-W1/W2 | Major | Establish the distinct scientific contribution against PPI, active inference, Bayesian TDA, and selective explanations. | Explicit closest composed baseline and a testable distinguishing claim. |
| EIC-W2; R1-W1; R3-W1; DA-M2 | Major | Instantiate the seed-dependent surrogate and its complete costs. | Executable definition, within-request residual variance, and matched total-cost comparison. |
| EIC-W3 | Minor | Align title and application wording with mean-effect auditing. | Claims consistently match the formal target, or a separate unlearning target is specified. |
| R1-W2 | Major | Specify the estimator, sampling streams, multiplicity, and stopping rule. | A complete validity argument under explicit assumptions. |
| R1-W3; R3-W4; DA-M3 | Major | Establish useful decision efficiency beyond safety. | Cost/margin analysis or compelling empirical advantage against equally adaptive direct estimation. |
| R1-W4; R3-W5 | Major | Separate pilot, tuning, validation, and uncertain reference estimation. | Budgeted protocol with correct replication units and whole-bank error evaluation. |
| R1-W5 | Minor | Define seed coupling and the downstream unlearning comparison. | Correct arm marginals and a precisely stated downstream replication unit. |
| R2-W3/W4 | Minor | Correct f-INE and qualify GRASP positioning. | Primary-source comparison in matching statistical terms. |
| R3-W3; DA-M4 | Major | Identify a defensible action for a mean-effect declaration. | Explicit use case plus seed-heterogeneity checks or a justified revised target. |

## 7. Sources, execution, and limitations

The search covers targeted primary papers and official proceedings available on 24 September 2026. It is not an exhaustive proof of novelty. Claims about published methods remain unreplicated unless the review explicitly gives a mathematical derivation. Recent preprints are distinguished from conference publications in the detailed reports. No acceptance probability is assigned.

This review adapts the [academic-paper-reviewer skill](/Users/spiderishi/.agents/skills/academic-paper-reviewer/SKILL.md) to a research proposal. Its canonical full-contract/provenance schemas and builder were absent from the searched installation, so this is **NOT_CALIBRATED**, with **criteria_binding_unavailable**, and is not a replay-validated formal review package. Public ICML criteria are contextual guidance. All agents used inherited model routing; no cross-model or accountable-human reviewer diversity is claimed. Shared filesystem access means peer-report access isolation was instructed and self-reported, not technically enforced.

- [EIC: contribution strength](/Users/spiderishi/Coding/attribution/research/review/eic-contribution.md)
- [R1: mathematical and statistical rigor](/Users/spiderishi/Coding/attribution/research/review/r1-methodology.md)
- [R2: attribution novelty and overlap matrix](/Users/spiderishi/Coding/attribution/research/review/r2-novelty.md)
- [R2: supplemental cost-allocation literature check](/Users/spiderishi/Coding/attribution/research/review/r2-late-literature-addendum.md)
- [R3: practical cost and falsification study](/Users/spiderishi/Coding/attribution/research/review/r3-practical.md)
- [DA: strongest counterarguments](/Users/spiderishi/Coding/attribution/research/review/da-stress-test.md)
- [Supplementary literature notes](/Users/spiderishi/Coding/attribution/research/review/root-literature-notes.md)
- [Execution disclosure](/Users/spiderishi/Coding/attribution/research/review/execution-record.json)

The reviewed proposal remains unchanged. No revision, experimental result, or theoretical guarantee is represented as completed by this assessment.
