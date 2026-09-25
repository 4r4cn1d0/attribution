# R2 — Domain and novelty review

**Manuscript:** *Selective Counterfactual Attribution for Reliable LLM Data Deletion*  
**Reviewed artifact:** `research/icml-attribution-proposal.md`, 24 September 2026  
**Role:** R2 / domain and novelty; training-data attribution, statistical attribution reliability, and unlearning evaluation.  
**Independence:** Fresh reviewer context; peer outputs not read; no subagents used. Model/provider identity unknown in the exposed runtime metadata.  
**Calibration:** `NOT_CALIBRATED`  
criteria_binding_unavailable

This is an informal assessment of an ICML-targeted research proposal, not a criterion-bound venue decision or an estimate of acceptance odds. No implemented algorithm, proved theorem, or experimental results were supplied. Their absence is the proposal's stated stage, not evidence that an experiment failed.

## Overall assessment

**Recommendation: Major Revision of the research plan before committing to its novelty claim.**  
**Confidence: 4/5** — original definitions and methods inspected for the closest overlaps; search is targeted, not exhaustive.

The proposal asks a sensible, narrow question: whether a finite group-deletion effect is practically material, negligible, or unresolved under a fixed training recipe. Its strongest feature is the separation of this statistical target from ownership, model-distribution equality, and universal unlearning certification. It also correctly declines to claim grouping, interactions, or counterfactual prediction as new.

The novelty argument nevertheless remains incomplete. Older Bayesian TDA already treats attribution as uncertain across training randomness and asks which individual explanations are trustworthy. Selective explanation work already routes uncertain cheap explanations to more expensive computation. Most consequentially, existing prediction-powered inference methods supply cheap-prediction correction, adaptive expensive observation, and anytime-valid confidence sequences. The proposed finite-bank correctness theorem appears to be an application of these tools unless additional structure is introduced.

I did not identify a single paper establishing exactly the proposed combination of structured LLM deletion requests, equivalence decisions, and a useful retraining-cost advantage. That leaves a plausible research opportunity, but **novelty is unestablished, not disproved**. The proposal should name the strongest composed baseline and identify an attribution-specific advance over it. Citation refinements are also needed: f-INE already concerns finite subset deletion, and GRASP's claimed confidence protocol is not sufficiently specified in the inspected text to serve as an established request-level guarantee.

## Criterion-bound judgments

| Dimension | Criterion source | Judgment | Evidence anchors | Rationale | Scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Official ICML criteria | No authoritative criteria binding supplied | NOT_ASSESSED | — | No confirmed venue alignment asserted | Informal research assessment only | No |
| Domain positioning | R2 assignment; original papers below | PARTLY_MEETS | `absence: prior-work table — expected statistical and selective attribution antecedents; checked lines 15–29 and 98–107` | Main attribution families recognized; closest inference composition missing | No exhaustive novelty search | Yes, for revising the plan |
| Distinct contribution | R2 assignment; explicit proposed mechanism | PARTLY_MEETS | `equation: proposed-method step 3, line 63, E[C] + E[Y-C]` | Target is precise; novel mechanism and advantage still unspecified | Proposal stage | Yes, for prioritizing the next experiment |

## Strengths

### S1: The estimand prevents several false novelty claims

The project explicitly targets an algorithm-average finite intervention and limits downstream conclusions to declared scores and queries. This supplies a useful basis for deciding which apparent comparisons are actually comparable.

**Evidence Anchor:** text: Formal target and scope, line 45, "This is an algorithm-average finite deletion effect, conditional on the starting checkpoint and training recipe."

### S2: The proposal anticipates the wrapper objection

It requires calibrated strong predictors and a cost advantage, and permits stopping if existing methods suffice. That makes the project falsifiable at the research-planning stage rather than dependent on discovering a favorable ranking metric.

**Evidence Anchor:** text: Baselines, line 105, "Simple calibrated versions of each strong predictor; these are essential to test whether the proposed method contributes beyond a wrapper."

## Strongest findings

### W1: The proposed statistical machinery has a close existing composition

**Severity:** Major  
**Evidence Anchor:** equation: Proposed method, lines 63–69, residual estimator E[C] + E[Y-C] and finite-bank sequential correctness target  
**Confidence:** 5/5 — inspected original algorithm, assumptions, and confidence-sequence construction.

The named statistical follow-up is central to the method, not peripheral future reading. [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html) (ICML 2024) allocates costly observations using prediction information for valid inference. [Prediction-Powered E-Values](https://arxiv.org/html/2502.04294) (ICML 2025; Theorem 2.1, Proposition 2.3, Algorithm 1) supplies prediction correction, adaptive observation probabilities, and confidence sequences under its stated bounds. For a frozen bank, applying valid per-target sequences with allocated error budgets already gives the proposed simultaneous declaration guarantee by a union bound. This last statement is the reviewer's mathematical inference, not a theorem claimed about deletion by either paper.

The application architecture is also anticipated by [Selective Explanations](https://arxiv.org/html/2405.19562) (NeurIPS 2024, §§3–4): uncertain amortized explanations receive extra Monte Carlo computation, and an optimized mixture improves explanation quality. Its demonstrated target is feature attribution/MSE, not the proposal's finite-deletion mean guarantee. It is therefore an adjacent architectural collision, not a complete prior solution.

**Minimum remedy:** Implement and name the composition “strong deletion predictor + existing active/anytime-valid prediction-powered inference” as the novelty baseline. Specify exactly which additional algorithmic step or deletion-specific result improves it. The generic correctness theorem alone does not distinguish this proposal from that construction. The proposal itself already acknowledges that ordinary concentration or a wrapper is insufficient; this finding concretizes that concern.

### W2: A missing TDA uncertainty paper occupies much of the reliability motivation

**Severity:** Major  
**Evidence Anchor:** absence: prior-work positioning — expected Bayesian TDA's original mean-effect and significance analysis; checked Recommendation, prior-work table, and Baselines, lines 5–29 and 98–107  
**Confidence:** 5/5 — inspected original §3 definitions and §4.2 experiments plus official proceedings metadata.

[Nguyen, Seo, and Oh, *A Bayesian Approach To Analysing Training Data Attribution In Deep Learning*](https://proceedings.neurips.cc/paper_files/paper/2023/hash/ca774047bc3b46cc81e53ead34cd5d5a-Abstract-Conference.html) (NeurIPS 2023) is unusually close to “when is attribution reliable enough?” Its [§3](https://arxiv.org/html/2305.19765) treats leave-one-out effects as random variables, estimates their means and variances, and uses significance tests at train–test-pair level; §4.2 compares noisy ground truth and approximate estimates. It recommends trusting influence only where the signal survives training noise.

This is not the same full problem: the proposal adds structured groups, practical equivalence tolerances, joint decision control, and a cheaper audit objective. But “uncertainty-aware/request-specific attribution reliability” is not an untouched gap, and merely extending from one point to a group is already addressed elsewhere.

**Minimum remedy:** Add this as a central antecedent and phrase the contribution as a cost-efficient extension to a specified intervention-and-decision regime. Explain why its direct repeated-training/significance approach, extended to groups and equivalence decisions, is insufficient for the intended operating budget.

### W3: The f-INE distinction needs to be expressed in estimands, not finite versus functional

**Severity:** Minor  
**Evidence Anchor:** text: prior-work table, line 19, "Distinguish inference about a specified finite deletion effect from its influence functional"
**Confidence:** 5/5 — inspected original Definitions 2.1–2.5 and the single-run estimator.

[f-INE](https://arxiv.org/html/2510.10510) already defines an intervention deleting a specified subset and contrasts the distributions induced by training with and without it. Its target is a hypothesis-testing trade-off function, with a signed Gaussian-influence specialization. It is not merely an infinitesimal influence functional. [Its proceedings version](https://openreview.net/pdf?id=TwkcMNACXo) confirms ICLR 2026 status.

**Minimum remedy:** Say “a bounded mean contrast with practical-equivalence decisions, rather than distributional distinguishability summarized by f/Gaussian influence.” Explain which output from f-INE can be calibrated to that mean target. A distributional score can disagree with a mean-effect decision for a valid reason; such disagreement would not establish attribution failure. The proposal's formal target is already careful, so this is a positioning correction rather than a refutation.

### W4: GRASP's confidence-protocol description is stronger than the inspected specification

**Severity:** Minor  
**Evidence Anchor:** text: prior-work table, line 22, "a confidence-based development-protocol selection procedure"
**Confidence:** 4/5 — inspected full HTML, Appendix C, and occurrences of confidence/protocol language; code not audited.

[GRASP](https://arxiv.org/html/2606.06892) claims a finite lower-confidence-bound selection protocol in its abstract and limitations. Appendix C says configurations are chosen from finite development families and frozen. I did not find an explicit statistical selection rule, confidence radius, error level, or coverage theorem for that claimed protocol in the inspected version. Its clearly documented mathematical bounds concern geometry/sketch error and ranking conditions.

**Minimum remedy:** Write “claims lower-confidence-bound protocol selection; development-only freezing is documented” until the actual rule is located in a version or code artifact. Do not infer that it already establishes calibrated deletion-effect intervals, nor claim novelty merely because its paper uses a different confidence target. The existing interaction-aware subset predictor is the substantiated overlap.

## Overlap matrix

“Not established here” means not established by the inspected paper, not proof that no related result exists. Results below remain the authors' reports; none were reproduced.

| Work and publication status | Verified overlap and primary locus | Same target/method or adjacent? | Residual distinction |
|---|---|---|---|
| [Attribute-to-Delete / DMM](https://proceedings.iclr.cc/paper_files/paper/2025/file/7c799b09cc40973ceaa47da50131dc63-Paper-Conference.pdf), ICLR 2025 | [§§2–4](https://arxiv.org/html/2410.23232): predictive attribution simulates retain-only outputs; oracle matching trains the unlearned model. KLoM evaluates point-specific output distributions against a retain-only reference. | Same counterfactual object; adjacent algorithmic objective. | DMM is a deletion mechanism plus evaluation, not the proposed three-way finite-mean audit with selective retraining cost. Do not reduce its overlap to “attribution helps unlearning.” |
| [f-INE](https://openreview.net/pdf?id=TwkcMNACXo), ICLR 2026 | Finite-subset interventions under training randomness; distinguishability functional and scalable single-run approximation. | Same intervention; different estimand. | Practical mean tolerance and valid selective inference remain distinct; see W3. |
| [GGDA](https://arxiv.org/html/2410.09940), 2024 preprint; [ATTRIB workshop poster at NeurIPS 2024](https://neurips.cc/virtual/2024/105343) | §3 defines group/property attribution; §4 generalizes influence functions, TracIn, and TRAK. | Same grouping infrastructure. | No demonstrated request-level equivalence audit. Do not label the workshop item as NeurIPS main-track proceedings. |
| [GRASP](https://arxiv.org/html/2606.06892), 2026 preprint | §3 and Appendices B–C: subset interactions, feature sketches, frozen development selection, retraining fidelity evaluation. | Same predictor building block. | Calibrated mean-deletion decisions and audit cost are not established here; confidence claim qualified in W4. |
| [Trajectory faithfulness](https://arxiv.org/html/2605.18814), 2026 preprint | §§2–4: TSLOO omits an example at one update; AdamW-influence and a per-sample update-error proxy. | Adjacent intervention and usable diagnostic. | TSLOO on a recorded trajectory differs from deleting every occurrence and averaging complete training runs. An error-proxy correlation is not an interval coverage guarantee. |
| [Bayesian TDA](https://arxiv.org/html/2305.19765), NeurIPS 2023 | Mean/variance of LOO effects and statistical significance of particular train–test pairs. | Close reliability target. | No selective retraining-cost algorithm or specified group-equivalence control; see W2. |
| [Selective Explanations](https://arxiv.org/html/2405.19562), [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/647af5f6b2538524f6c047c1d9170fd9-Paper-Conference.pdf) | §§3–4 and Appendix C: uncertainty routing, optimized cheap/expensive combination, computation/coverage trade-off. | Adjacent method architecture; feature-attribution experiments. | Does not establish the proposed algorithm-average deletion mean inference. |
| [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html), ICML 2024; [Prediction-Powered E-Values](https://proceedings.mlr.press/v267/csillag25a.html), ICML 2025 | Active costly measurements and statistical inference; the latter explicitly supplies sequential confidence construction. | Directly reusable generic inference machinery. | A deletion-specific cost-saving mechanism or empirical discovery would need to come from this project. |
| [Athena: Probabilistic Verification of Machine Unlearning](https://www.princeton.edu/~pmittal/publications/machine-unlearning-pets22.pdf), PoPETs 2022 | Hypothesis-testing verification through planted backdoors. | Adjacent verification objective and access model. | Does not estimate a natural group's finite mean-deletion effect; verification is already a mature separate objective. Abstract/metadata checked; not treated as a core method collision. |
| [Auditing of Unlearning Algorithms](https://arxiv.org/html/2607.05898), 2026 preprint | §§4–5 and Appendix F: subset-based auditor, controlled testing of an unlearning-parameter lower bound, abstention on uncertain batches. | Adjacent selective audit with a stronger distributional target. | Falsifying an unlearning guarantee differs from affirming negligible mean change. Its calibrated/selective audit vocabulary is not novel to this proposal. |

## Actual novelty residual and nearest competing combination

**Residual:** the specific research problem of economically deciding practical finite effects for structured and attribution-selected LLM deletions under a declared recipe. At present this is a useful problem formulation and experimental program. An original estimator or nontrivial new theorem has not been identified.

**Nearest competing combination (reviewer synthesis, not an existing named paper):** use an existing interaction-aware/datamodel predictor in the declared score units; apply existing active prediction-powered confidence sequences to paired retraining outcomes for each frozen request; allocate finite-bank error budgets; return the same material/negligible/undecided categories when intervals cross the declared boundaries. Use a selective explanation/error-proxy heuristic only to guide expenditure where its assumptions permit. Include direct paired retraining as a fallback. This composition already expresses almost the entire proposed interface.

The minimum defensible change is to make that composition the explicit starting baseline and then isolate **one** advantage peculiar to deletion experiments. Candidate directions, not established novelty claims, include exploiting the vector of query outcomes yielded by one expensive retrain, or deriving and testing a cost-allocation rule that exploits shared full-data references and structured request dependencies. Each needs another targeted literature check; generic multitask allocation or control variates should not be renamed as novel attribution machinery.

A defensible empirical route is also possible: demonstrate a reproducible decision failure that survives matched estimands, then show why a carefully specified remedy gives better decision coverage at equal *total* cost than the composed baseline. Simply observing unreliable scores, training-seed variation, redundant support, or rank-versus-magnitude disagreement would not suffice as the distinctive discovery.

## Questions for the authors

1. What exact step in the proposed algorithm is absent from “existing deletion predictor + existing active prediction-powered confidence sequences”?
2. Is the central promised result an algorithmic improvement, a deletion-specific cost theorem, or a new empirical failure phenomenon? Which one would remain if generic confidence construction were treated as infrastructure?
3. What precise statistical object will each f-INE/trajectory-based baseline predict, and how will comparisons avoid interpreting a different estimand as an error?

## Scope and provenance

Search date: 24 September 2026. Original-paper full text inspected for DMM, f-INE, GGDA, GRASP, trajectory faithfulness, Bayesian TDA, Selective Explanations, Prediction-Powered E-Values, and Auditing of Unlearning Algorithms. Official proceedings checked where linked. Active Statistical Inference's proceedings and original-paper search text were inspected; Athena was a bounded verification-context check, not a full technical review. Searches included training-data attribution with confidence intervals, calibration, conformal methods, confidence sequences, selective explanations, Bayesian uncertainty, and unlearning hypothesis-testing/equivalence verification.

The review did not audit every secondary citation in the proposal, reproduce claims, inspect all repositories, or establish absence of competing work. In particular, the proposal's high-level descriptions of DMM, GGDA, and trajectory faithfulness are supported; the material corrections are under-positioning Bayesian/selective antecedents, the f-INE distinction, and the qualification of GRASP's confidence claim.
