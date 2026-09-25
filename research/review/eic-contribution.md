# EIC / contribution-strength review

## Reviewer identity and status

Journal-Fit Reviewer seat; remit: contribution strength, coherence, and research strategy. Target: the 24 September 2026 **proposal**, not a completed submission. This report was committed without reading peer reports or panel literature notes. Model/provider metadata and accountable human identity are unknown; role separation does not establish independent errors.

`NOT_CALIBRATED`

`criteria_binding_unavailable`

The criteria-consumer schema/tool artifacts and binding manifest were unavailable. Public ICML guidance informs this advisory assessment; no validated venue-alignment claim or acceptance probability is made.

## Role-bound recommendation

**Major Revision of the research design; proceed with a bounded pilot.** This is not a conference rejection recommendation. The question is useful and responsibly scoped, but the specific contribution beyond existing inference machinery remains unresolved. Missing completed results are appropriate at this stage; missing specifications needed to test the cost-saving mechanism are actionable now. Overall confidence: **3/5**, reflecting a focused literature check rather than exhaustive novelty verification.

## Criterion-oriented judgements

| Dimension | Source | Judgement and proposal evidence | Rationale, uncertainty, decision bearing |
|---|---|---|---|
| Contribution specificity | Author’s Recommendation | PARTLY_MEETS; text: L11 “using substantially fewer retraining runs than direct estimation” | Clear objective; mechanism insufficiently specified. Yes: W1–W2. |
| Claim–experiment coherence | Author’s Formal target and Primary measurements | MEETS as design direction; equation: L43, Delta(F,q) | Interventions and threshold decisions match the estimand. Results unassessed. Positive bearing. |
| Originality | Author’s candidate-gap claim | PARTLY_MEETS; text: L29 “It does not establish that no prior work solves it.” | Appropriate uncertainty; statistical comparators incomplete. Yes: W1. |
| Submission readiness | Proposal maturity statement | NOT_ASSESSED; text: L3 “This is a proposed project” | No completed-paper score inferred. No negative bearing. |

## Summary assessment

The project would estimate a defined training-algorithm average deletion effect, make material/negligible/abstain declarations, and spend retraining effort where cheap attribution predictions need validation. This is a more consequential objective than improving attribution rankings alone. Its planned comparisons can test whether apparently good attribution produces unreliable practical decisions, while retaining a faithful intervention target.

The present novelty case is strongest as a research question, weaker as a proposed new algorithm. Existing prediction-powered inference already combines predictions with measured residuals; active statistical inference already chooses expensive observations using predictive uncertainty. Their existence does not establish that this deletion problem is solved. It does mean that adding residual correction, selective sampling, and stopping safeguards needs a specific justification or substantial empirical insight.

ICML’s public instructions recognize useful combinations and empirical understanding as originality, and separate soundness from impact. A new theorem or attribution method is therefore not a prerequisite. The proposal should preserve an empirical-discovery route even if an existing statistical construction provides the best remedy. [ICML reviewer instructions](https://icml.cc/Conferences/2026/ReviewerInstructions).

## Strengths

### S1: The intervention and decision target are unusually clear

**Evidence Anchor:** text: Formal target, L45, “This is an algorithm-average finite deletion effect”; L53, “Failure to reject a zero-effect null is not evidence of equivalence.”

This separates attribution magnitude, joint interventions, and equivalence decisions. It prevents several plausible but uninformative success claims.

### S2: Evaluation rewards useful decisions and exposes trivial abstention

**Evidence Anchor:** text: Primary measurements, L114, “Fraction of requests receiving a decision, plotted against error and compute.”

Together with strong calibrated comparators and intervention-family stratification, this can make the contribution interpretable to researchers choosing an audit strategy.

### S3: The proposal contains real falsification criteria

**Evidence Anchor:** text: First two weeks, L132, “Pivot or stop if strong existing methods already solve the problem”.

Learnability checks, estimand consistency, and a pilot explicitly described as exploratory reduce the risk of mistaking an experimental artifact for a contribution.

## Weaknesses

### W1: Statistical novelty has not yet been differentiated

**Severity:** Major

**Evidence Anchor:** absence: Proposed method and Baselines, L57–69 and L98–105 — expected explicit comparison with prediction-powered and active statistical inference; checked method steps, theorem targets, baseline list, literature-gap paragraph L29

**Confidence:** 4/5 — directly checked primary sources; equivalence to the full proposed system remains unproved.

**Impact:** The residual identity is established machinery in [Prediction-Powered Inference, §1.3](https://arxiv.org/html/2301.09633v4), and [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html) allocates costly measurements while maintaining inferential validity. Sequential PPI also exists, although its stated asymptotic time-uniform guarantee must not be equated with the proposed finite-sample guarantee. [Anytime-valid PPI](https://arxiv.org/abs/2505.18000).

**Minimum remedy:** Add these as explicit methodological comparators and identify the unresolved deletion-specific obstacle: for example, obtaining informative seed-level surrogates or optimizing decisions across requests. A rigorously demonstrated useful combination remains a valid contribution; novelty must not rest on the residual identity alone.

### W2: The proposed source of cheaper evidence is unspecified

**Severity:** Major

**Evidence Anchor:** text: Proposed method, L63, “If a surrogate C_r tracks the true effect Y_r across seeds”.

**Confidence:** 4/5 — direct dependency of the stated efficiency claim.

**Impact:** The proposal does not identify what varies cheaply with each fresh seed, what training is required to obtain it, or what costs are shared across requests. A predictor constant across validation seeds cannot reduce within-request seed variance through residual subtraction. Accurate rankings across deletion groups do not establish this needed covariance. This is a missing design specification, not evidence that the mechanism fails.

**Minimum remedy:** Specify one computable C_r, its coupling to Y_r, and per-seed versus amortized costs. Make residual variance and total cost the pilot’s first efficiency checks against direct paired retraining. Cross-request borrowing would require its own assumptions and validation.

### W3: The title gives the deletion application more weight than the main estimand supports

**Severity:** Minor

**Evidence Anchor:** text: Title, L1, “Reliable LLM Data Deletion”.

**Confidence:** 4/5 — the formal scope expressly limits its claims.

**Impact:** A material deletion effect is not evidence that an unlearning procedure successfully matches retain-only retraining. The body recognizes this distinction, so the concern is framing rather than an invalid target.

**Minimum remedy:** Center the eventual title and abstract on reliable deletion-effect decisions, or make a separately specified unlearning-compatibility audit central to the evidence.

## Viable paper routes and author questions

A **methodological route** would demonstrate that a specified combination produces substantially more reliable decisions at equal total cost than strong existing inference procedures. An **empirical-insight route** would establish a reproducible, practically important mismatch between accepted attribution metrics and deletion decisions, explain its conditions, and show how available inference tools change conclusions. The latter needs strong controls and transfer evidence, but no invented methodological novelty. Neither route is guaranteed by the present proposal.

The decisive questions are: What inexpensive seed-level signal enables W2’s variance reduction? What remains unsolved after applying W1’s closest comparators? If the failure mode is robust but a standard inference method fixes it, will the project retain that empirical contribution? These answers determine the appropriate study, before expanding the baseline and model list.
