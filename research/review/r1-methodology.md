# R1 Methodology Review

## Manuscript and reviewer information

- **Manuscript:** *Selective Counterfactual Attribution for Reliable LLM Data Deletion*, proposal dated 24 September 2026.
- **Reviewed file:** [proposal](/Users/spiderishi/Coding/attribution/research/icml-attribution-proposal.md); anchors use its line numbers.
- **Role:** R1 / Peer Reviewer 1, Methodology.
- **Invocation context:** fresh-context subagent `/root/rigor_review`; no peer outputs read.
- **Model / provider:** unknown / unknown; no model identity independently verified.
- **Human accountability:** no accountable human reviewer participated in this report.
- **Scope:** mathematical and statistical design at proposal stage; no experimental results or completed proofs are assumed.
- **Assessment:** informal ICML-oriented research assessment, without official venue-criteria alignment or acceptance probability.

criteria_binding_unavailable

Calibration status: **NOT_CALIBRATED**

## Overall assessment

**Recommendation: Major Revision of the methodology specification before the main study.** This is a proposal-development recommendation, not a publication decision. **Confidence: 4/5**, based on directly checkable mean-estimation algebra and statistical-design arguments; practical LLM surrogate quality remains unknown.

The proposal targets the mean effect of a finite training-data deletion under a declared training recipe and would combine attribution predictions with independent retraining audits. It explicitly proposes, rather than claims to have established, simultaneous decision validity and savings in retraining cost. The estimand is coherent, and the distinction between equivalence and failure to reject is correct. The principal unresolved issue is whether a cheap predictor supplies useful variation across seeds for each fixed request: accurate predictions across requests do not establish this property. Without it, residual correction can reduce exactly to ordinary retraining averages. The safety theorem is plausible using existing confidence sequences, but by itself establishes no computational contribution. The main study also needs a margin-sensitive cost target and a way to evaluate decisions when the reference mean itself is estimated. These are repairable design gaps, not demonstrated errors in an implemented procedure. A focused pilot measuring within-request residual variance and complete marginal costs should precede expanding model size or the baseline roster.

## Strengths

### S1: The finite-deletion estimand is well scoped

**Evidence Anchor**: equation: Formal target and scope, L41–45, definition of `Delta(F,q)`.

Fixing the checkpoint, optimizer, compute policy, and seed distribution makes the expectation interpretable. Shared randomness changes variance, but not the difference of marginal means if each training arm preserves its prescribed marginal law.

### S2: Equivalence and unlearning limitations are stated correctly

**Evidence Anchor**: text: Formal target and scope, L53–55, “Failure to reject a zero-effect null is not evidence of equivalence.”

Requiring the entire interval to lie within the tolerance region supports a negligible-mean-effect declaration. The explicit restriction to declared statistics and queries avoids claiming distributional unlearning from equality of score means.

### S3: The pilot is honestly exploratory

**Evidence Anchor**: text: First two weeks, L126, “three seeds are not adequate evidence for tight certification.”

The proposal does not present its 75-run pilot as certification evidence. Matching interventions and restarting from a fixed checkpoint support a useful feasibility study.

## Weaknesses and minimum remedies

### W1: The seed-specific cheap surrogate is not yet instantiated

**Severity**: Major  
**Confidence**: 5/5 — exact algebra; feasibility remains empirical.  
**Evidence Anchor**: text: Proposed method, L63, “If a surrogate C_r tracks the true effect Y_r across seeds”.

**Problem and consequence.** For fixed \((F,q)\), let \(Y_r\) be the paired deletion effect. If the attribution model supplies only one prediction \(C_r=c(F,q)\), then

\[
c+\frac1n\sum_{i=1}^n(Y_i-c)=\bar Y_n.
\]

The predictor cancels, even if it predicts mean effects perfectly across many different requests. Adding independent surrogate noise cannot help. Useful correction requires positive predictive information about *seed-level deviations within this request*, or an explicitly different model that borrows information across requests under stated assumptions.

For a concrete disjoint-sample implementation, with development-frozen \(\beta\), \(n\) paired \((Y_i,C_i)\), and \(N\) independent cheap \(C'_i\) from the same seed law,

\[
\hat\Delta=\beta\bar C'_N+\overline{(Y-\beta C)}_n,\qquad
\operatorname{Var}(\hat\Delta)=
\frac{\operatorname{Var}(Y-\beta C)}n+
\frac{\beta^2\operatorname{Var}(C)}N.
\]

This calculation is conditional on development data; overlapping samples require their covariance terms. Residual mean correction and this variance decomposition are established PPI machinery, not a new theorem. [PPI, supplementary mean-estimation derivation](https://www.stat.ubc.ca/~john/papers/AngelopoulosScience2023.pdf)

**Minimum remedy.** Specify executable \(C_r\), its inputs, and how it is obtained without the deleted-data retrain. If it needs a fresh full-data model for each seed, charge that training cost and explain sharing across requests. Measure within-request residual variance, not only cross-request correlation/LDS. Include constant-surrogate and shuffled-seed-surrogate controls. Retain direct estimation when prediction contributes no useful signal.

### W2: The proposed guarantee needs a complete sampling and stopping construction

**Severity**: Major  
**Confidence**: 4/5 — standard confidence-sequence reasoning.  
**Evidence Anchor**: absence: Proposed method, L61–69 — expected a specified estimator, dependence structure, error allocation, and stopping rule; checked Formal target, Proposed method, Models and retraining, and Primary measurements.

**Problem and consequence.** “Fresh seeds,” multiplicity control, and time-uniform intervals are appropriate requirements, but their combination is not yet an algorithm. Ordinary fixed-sample PPI intervals cannot simply be repeatedly inspected. Standard PPI++ power-tuning results also use asymptotic theory; cross-fitting alone does not establish finite-sample, time-uniform validity. [PPI++, Theorem 1 and §6](https://arxiv.org/html/2311.01453v2)

**Minimum remedy.** Condition on discovery data that freeze all \(K\) request/query pairs, statistics, tolerances, predictors, coefficients, and error weights. One conservative construction uses separate bounded confidence sequences for \(E[\beta C]\) and \(E[Y-\beta C]\), each at error \(\delta/(2K)\), and sums their intervals. Clip/bound the surrogate and coefficient, and account for both streams. Existing empirical-Bernstein confidence sequences provide the required finite-sample building blocks. [Howard et al., Definition (1) and Theorem 4](https://arxiv.org/html/1810.08240v5)

With simultaneous intervals \([L_{j,t},U_{j,t}]\), declare positive material effect only when \(L_{j,t}>\epsilon_j\), negative material effect when \(U_{j,t}<-\epsilon_j\), and negligible effect when \([L_{j,t},U_{j,t}]\subseteq[-\epsilon_j,\epsilon_j]\); otherwise abstain. A union bound then proves

\[
P(\text{any incorrect declaration for any }j,t)\leq\delta.
\]

Cross-request independence is unnecessary for this union bound. Reusing full-data controls is legitimate, but adaptive allocation must preserve each request's prespecified iid seed-stream prefixes, or use a separately justified sampling correction. Selecting favorable seeds after seeing their cheap outputs is a different sampling design. Freeze coefficients on separate pilot data for the first implementation; any sequential cross-fitting extension needs its own proof.

### W3: Safety alone does not establish the proposed cost advantage

**Severity**: Major  
**Confidence**: 4/5 — cost/variance algebra and threshold-testing design.  
**Evidence Anchor**: text: Proposed method, L69, “A second target would characterize the conditions under which residual correction reduces training cost.”

**Problem and consequence.** A simultaneous confidence guarantee can be obtained by direct retraining plus a union bound. To answer the actual research question, the main theorem/experiment must connect declaration coverage to compute, including predictor construction and the distance of each effect from its threshold. Prior multifidelity work already optimizes evaluation counts using costs and cross-model correlations. [Peherstorfer, Willcox, and Gunzburger, §§2–3](https://kiwi.oden.utexas.edu/papers/multi-fidelity-monte-carlo-peherstorfer-willcox-gunzburger.pdf)

For the disjoint design in W1, write \(a=\operatorname{Var}(Y-\beta C)\), \(b=\beta^2\operatorname{Var}(C)\), paired cost \(c_P\), cheap-only cost \(c_C\), and budget \(B=c_Pn+c_CN\). Ignoring integer constraints and setup cost, direct minimization gives

\[
\min_{n,N}\operatorname{Var}(\hat\Delta)
=\frac{(\sqrt{a c_P}+\sqrt{b c_C})^2}{B}.
\]

Thus even variance reduction must beat the direct benchmark \(\sigma_Y^2c_Y/B\) at equal cost. This is a diagnostic calculation, not a finite-sample stopping-time theorem. Fixed bank-wide shared controls require the corresponding bank-level cost accounting.

**Minimum remedy.** Define \(m_j=\big||\Delta_j|-\epsilon_j\big|\). A nontrivial result should bound the cost to declare requests with \(m_j>0\), in terms of residual variance, cheap variance, their ranges, \(K,\delta\), and pilot/setup costs, and identify a regime of strict improvement over equally adaptive direct retraining. No uniform finite-cost guarantee exists at arbitrarily small margins under the present assumptions. For scale, a fixed-time Hoeffding radius for \(Y\in[-1,1]\) is \(\sqrt{2\log(2K/\delta)/n}\); this is a conservative reference, not a necessary seed count.

Choosing \(\epsilon\) in advance is necessary but not sufficient: justify its practical scale, preregister sensitivity values, and report the empirical margin distribution. Auditing requests nearest the threshold may consume the most runs per decision. Clarify whether allocation maximizes answered requests or prioritizes difficult/high-value requests; compare with a direct sequential baseline pursuing the same objective.

### W4: The evaluation must distinguish a retraining realization from the reference mean

**Severity**: Major  
**Confidence**: 4/5 — estimand/measurement alignment.  
**Evidence Anchor**: absence: Primary measurements, L111–118 — expected a protocol accounting for reference-mean uncertainty and repeated-panel error evaluation; checked Formal target, Controlled data, Primary measurements, and First two weeks.

**Problem and consequence.** Exact retraining produces \(Y_r\), not exact \(\Delta\). Labeling coverage or false decisions against a small reference average can make a sound interval look wrong, or conceal false assurances. Shared control seeds also correlate errors across request/query cells. Average per-query coverage is not the proposed probability of *any* false declaration.

**Minimum remedy.** Reserve independent reference seeds for a smaller evaluation bank and attach simultaneous uncertainty to reference means. Treat cases whose oracle interval crosses the decision boundary as unresolved rather than certainly correct/incorrect. Use a cheap setting with known expectations, or extensive simulation, to test whole-bank error under repeated complete experimental replications; report that separately from empirical LLM error. Resample at the seed-vector/source-family level where appropriate, not individual paraphrases. Report reference-oracle evaluation costs separately from, and alongside, deployment audit costs. This is an evaluation-protocol requirement, not a demand for completed results in the proposal.

### W5: Pairing and the downstream unlearning estimand need operational definitions

**Severity**: Minor  
**Confidence**: 4/5 — coupling and expectation identities.  
**Evidence Anchor**: text: Models and retraining, L94, “Pair seeds and shared example ordering where possible to reduce variance”.

**Problem and consequence.** Identical integer seeds do not ensure useful positive covariance after deletion changes batching and random-number consumption. For score variables \(X,Z\), \(\operatorname{Var}(X-Z)=\operatorname{Var}(X)+\operatorname{Var}(Z)-2\operatorname{Cov}(X,Z)\); pairing helps only when covariance is favorable. Each arm must still have the intended training distribution.

**Minimum remedy.** Publish the shuffle/dropout/batching coupling, marginal training policy, and paired-versus-independent variance check. For the downstream experiment, choose explicitly between a fixed unlearned model's score minus \(E[s(A(D\setminus F;r))]\), and an average over both training and unlearning randomness. These require different replication units. The proposal already acknowledges that means do not certify distributional unlearning; for illustration, a Bernoulli-\(1/2\) score and a constant \(1/2\) score have equal means but different distributions.

## Minimum theorem package and pilot decision

The simultaneous safety result in W2 is a necessary baseline. The minimum additional substantive result is an *instance-dependent, cost-aware declaration bound* for one specified estimator/allocation procedure, including an explicit improvement condition and a safe direct-estimation fallback. It must describe nonzero margins, surrogate randomness, pilot estimation, all model-training costs, and shared-reference accounting. Merely reproving unbiasedness or applying a union bound would not distinguish the method.

Before broad experiments, test two or three fixed requests using enough pilot seeds to assess whether a computable \(C_r\) reduces residual variance at a favorable total cost. The exploratory three-seed study can reveal gross failures, but is too unstable to establish a covariance-driven cost advantage. Expand only after this mechanism works. A recent multi-task PPI preprint also retains within-task correction while borrowing cross-task structure; its relevance deserves follow-up if that becomes the proposed remedy. [Emmenegger et al., abstract](https://arxiv.org/html/2605.29249v1)

## Criterion-bound judgements

These use the assigned methodology remit and the skill's general quality rubric, not official ICML criteria.

| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Estimand coherence | R1 assignment; quality rubric, argument coherence | MEETS | equation: L43; text: L45 | Target and exclusions are explicit. | Downstream operational target remains open. | Yes, supports proceeding. |
| Statistical validity specification | R1 assignment; quality rubric, methodological rigor | PARTLY_MEETS | absence: W2 anchor | Correct safeguards are identified but not instantiated. | No implemented method to audit. | Yes, requires specification. |
| Compute feasibility | R1 assignment; quality rubric, evidence sufficiency | PARTLY_MEETS | text: L63; text: L69 | Useful variance reduction is a testable condition, not yet demonstrated. | Pilot/runtime evidence absent by design. | Yes, first feasibility gate. |
| Evaluation design | R1 assignment; quality rubric, methodological rigor | PARTLY_MEETS | absence: W4 anchor | Appropriate endpoints; reference uncertainty unspecified. | Proposal stage. | Yes, fix before main study. |
| Empirical statistical reporting | R1 assignment; quantitative reporting scope | NOT_ASSESSED | text: L3 | No empirical statistical claims are reported. | Inapplicable to unperformed experiments. | No. |

## Arithmetic receipts and detailed scope checks

no_recomputable_statistics: No reported test statistics, p-values, means/SDs of measured samples, or degrees of freedom meet the bounded recomputation procedures; checked the complete proposal.

The planning count is internally consistent: \(24\times3+3=75\) training runs, assuming one full-data reference per seed is shared across configurations. This does not establish runtime. No observed p-hacking, omitted negative results, or overstated completed theorem is alleged. Data learnability, held-out families, matched decoys, and fixed-steps versus fixed-epochs sensitivity are appropriate planned controls. Code/data reproducibility cannot yet be assessed.

## Questions for the authors

1. What exact seed-dependent surrogate can be computed cheaply enough to reduce the total cost for one fixed deletion request?
2. What primary tolerance, query-bank size, familywise error level, and maximum budget define a successful practical demonstration?
3. Is the downstream target compatibility of one released unlearned model with a retraining mean, or compatibility of randomized unlearning and retraining procedures?

## Source-access disclosure

Primary statistical sources were independently browsed on 24 September 2026. PPI supplementary mean-estimation formulas, PPI++ asymptotic/power-tuning sections, Howard et al.'s confidence-sequence definitions and bounded-data theorem, and the multifidelity paper's formulation were inspected. The new multi-task PPI source was inspected for its abstract only; its proofs were not audited. Some initial arXiv/MIT download URLs failed; accessible primary copies linked above were used. No claim of exhaustive statistical-literature coverage is made.
