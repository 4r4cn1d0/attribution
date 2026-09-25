# Project 3: proposal-stage novelty and rigor assessment

Assessment date: 2026-09-24. Target: ICML 2027. Input: the original Influence-Based Proactive Alignment & Unlearning Verification proposal and the critique pasted by the user. This is an advisory assessment of an idea, not a conference review or acceptance forecast. No model-training experiments have been run.

## Verdict

| Dimension | Score / 5 | Interpretation |
|---|---:|---|
| Novelty as specified | 2 | Substantial overlap; a distinct technical result has not been defined. |
| Demonstrated mathematical rigor | 1.5 | Relevant mathematical ingredients, but no operator definition, theorem, assumptions, or proof; the unrestricted local-to-global inference fails. |

The scores are coarse judgments, not calibrated measurements or official ICML scales. The pasted critique is broadly correct. Naming a dual-space operator does not establish novelty, and a proposed theorem is not an established result. This does not prove that every precise version of the proposed operator has already been published.

## Closest verified precedents

| Proposed ingredient | Primary source | Overlap and boundary |
|---|---|---|
| Proactive influence-based suppression of toxic behavior | [IF-Guide, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/715dbde23573722874c20e25cfe91ac3-Abstract-Conference.html) | Token-level training-data influence guides suppression during pretraining/fine-tuning. This directly overlaps with the proactive detoxification motivation, but is not an exact deletion certificate. |
| Influence-based LLM unlearning | [Unified Parameter-Efficient Unlearning for LLMs / LLMEraser, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/8d537430e55a283a97e9b6e682e994a3-Abstract-Conference.html) | Influence-based instance-wise parameter adjustments in PEFT LLMs already exist. |
| Dual-space robust unlearning | [PRISM, ICLR 2026](https://arxiv.org/abs/2509.23362) | Representation and parameter smoothness address jailbreak/relearning robustness. These are not exactly the proposal's parameter-influence/output-KL spaces; shared terminology alone is not proof of equivalence. |
| Formal removal guarantees | [Certified Data Removal, ICML 2020](https://proceedings.mlr.press/v119/guo20c.html); [Certified Unlearning for Neural Networks, ICML 2025](https://proceedings.mlr.press/v267/koloskova25a.html) | The claim that no formal verification framework exists is too broad. Guarantees must be compared by target, assumptions, cost, and utility. |
| Robustness to subsequent learning | [SAM-based robust unlearning, ICML 2025](https://proceedings.mlr.press/v267/fan25e.html); [Invariant LLM Unlearning, ICML 2025](https://proceedings.mlr.press/v267/wang25en.html) | Resistance to relearning and unrelated downstream fine-tuning already has direct precedents. |
| Tighter practical certification | [Less Noise, Same Certificate, March 2026 preprint](https://arxiv.org/abs/2603.03172) | Retain sensitivity tightens noise calibration for certified unlearning. Any proposed sensitivity-based certificate needs a direct comparison. This is not presented here as a verified conference publication. |
| Influence under training randomness | [f-INE, ICLR 2026](https://arxiv.org/abs/2510.10510) | Hypothesis-testing-based influence explicitly accounts for randomized training. Adding training-seed uncertainty is not itself a new contribution. |
| Hidden residual information after apparent unlearning | [Auditing Language Model Unlearning via Information Decomposition, EACL 2026](https://arxiv.org/abs/2601.15111) | Representation-based auditing of residual information and reconstruction risk already exists. An audit must add more than observing that suppression can leave information behind. |

Important correction to an overly compressed comparison: the neural-network certification paper's Definition 2.1 permits a retain-only *certifying algorithm*. Its main choice applies unlearning/postprocessing to the retain-only trained model. That is not automatically the same target as the original, unprocessed training algorithm on retained data. See [Section 2 and the theoretical analysis](https://arxiv.org/html/2506.06985v1). A proposal must fix its comparator rather than moving between them.

## Mathematical checks

### Local influence cannot certify a finite deletion without further conditions

Here is a concrete counterexample constructed for this assessment, not a claimed novel research theorem. Let the forget-set weight be w in [0,1], and train by exact global minimization of

\[
L_w(\theta)=(\theta^2-1)^2+3w\theta^2.
\]

The first term is retained loss and the second is weighted forget loss. Break ties by selecting the nonnegative minimizer. Substituting z=theta^2 >= 0 gives the quadratic z^2+(3w-2)z+1, so

\[
\theta(w)=\sqrt{\max(0,1-3w/2)}.
\]

For every w >= 2/3, theta(w)=0. Thus every local derivative in this forget-weight direction vanishes at full data w=1 (one-sided on the stated domain, or ordinary derivatives after extending the same formula). The full-data Hessian is 2 and the forget-loss gradient is zero: even the usual local inverse-Hessian influence calculation returns zero.

Use a Bernoulli predictor with p_theta(y=1)=sigmoid(theta^2). Its output law is exactly unchanged under every sufficiently small perturbation of w near 1. Local KL is therefore exactly zero, not merely zero to first order.

Deleting the forget data means w=0. Now theta=1, and the output probability changes from 0.5 to sigmoid(1), approximately 0.7311. Both retained-only minimizers, +1 and -1, have this same output. Output total variation is approximately 0.2311; parameter-law TV is 1 for the deterministic chosen training rule. These are different quantities.

This refutes the unrestricted implication from local parameter/behavioral insensitivity to finite-deletion equivalence. It does not demonstrate how often this occurs in LLMs, nor refute a theorem with sufficient global conditions or full-path information. The solution path changes regime away from the original model, precisely what a local certificate misses.

A separate, simpler trap: for normalized, smooth distributions with suitable common support,

\[
\left.\frac{d}{dt}D_{KL}(p_\theta\Vert p_{\theta+tv})\right|_{t=0}
=-\sum_y\left.\frac{d}{dt}p_{\theta+tv}(y)\right|_{t=0}=0.
\]

Thus the first derivative of this KL is generically zero even when v is nonzero. Its usual leading term is quadratic in v through Fisher information. Using that derivative as a forgetting indicator would be invalid.

### Deletion and capability suppression require separate targets

A strong, useful target is a specified divergence between the laws of U(A(D),D_f) and A(D\D_f), with A including initialization, optimizer, data order, stopping, and randomness. The proposal currently does not define this target or its guarantee level. A finite prompt-average score, model-law indistinguishability, and absence of recoverable knowledge are not interchangeable.

Retained examples may teach the same facts as deleted examples. Consequently a retain-only model can possess the capability legitimately under the deletion target. Refusal on a prompt is also insufficient to demonstrate dataset deletion.

### Downstream robustness is not automatically a new theorem

Let P and Q be full model-state distributions and K a common randomized downstream procedure. Standard data processing gives

\[
\operatorname{TV}(PK,QK)\leq\operatorname{TV}(P,Q).
\]

The same postprocessing preserves event-based (epsilon,delta) indistinguishability. If a proposal already assumes a sufficiently strong full-state guarantee, proving preservation under this common procedure is not the main missing result.

Auxiliary data must be fixed/common, independent with a common law, or covered by an appropriate joint-distribution guarantee. Optimizer state or cached data exposed downstream must also be covered; a guarantee on model weights alone does not cover untracked state. Behavioral equality on a prompt sample is insufficient for white-box fine-tuning. Common re-exposure can restore a capability in both models while relative indistinguishability remains intact.

## A defensible project revision

Candidate question, with novelty still unestablished:

> Can an affordable audit detect when alignment makes local attribution appear negligible while finite deletion still changes a model's behavior relative to retain-only retraining?

Use controlled SFT from a shared checkpoint first. Separate uniquely supported facts from facts also supported by retained data. Define the desired comparison after the same specified alignment or continuation procedure in both training worlds. The hidden-information and randomness-aware influence precedents above require direct methodological comparison before claiming this question itself is new.

Two possible contribution types remain open: a computable finite-deletion bound with estimation and remainder errors, or a reproducible empirical finding and audit that improves failure detection at a measured cost. Neither is established by this review.

Decisive requirements before a larger study:

1. Specify the operator, units, input/output spaces, training intervention, randomness, access, and comparator. For a theorem, state exactly which prompt/attack/update class it covers.
2. Make the proposed guarantee survive finite-deletion counterexamples, or explicitly restrict its scope. A bound depending on unknown global constants or the unknown retrained model may be unusable.
3. Validate against actual retain-only retraining, with multiple training seeds and uncertainty. Compare both starting models under identical downstream procedures.
4. Compare against simpler loss, gradient, influence, output-KL, and established unlearning/audit baselines. Hold out facts, prompts, and attack development data; report false passes and abstentions as well as average performance.
5. Measure the forgetting–utility–compute trade-off. Include attribution construction, stored trajectories, audits, and retraining in cost. MMLU/GSM8K alone cannot establish universal absence of utility degradation.

For the audit route, abandon the extra machinery if it does not improve held-out failure detection over cheaper baselines at comparable false-pass rates and total cost. For the theorem route, abandon or revise a certificate that is vacuous at relevant deletion sizes. These are proposed decision criteria, not experimental outcomes.

A theorem is not mandatory for an ICML contribution. The verified [ICML 2026 reviewer guidance](https://icml.cc/Conferences/2026/ReviewerInstructions) explicitly values new insights and well-motivated combinations. This review does not assume the unpublished details of ICML 2027 policy or forecast acceptance.

## Retrieval and review provenance

Targeted, non-exhaustive primary-source lookup on 2026-09-24 using web search plus arXiv, conference proceedings, and OpenReview. Queries included the exact IF-Guide, LLMEraser, PRISM, and Certified Unlearning titles; LLM unlearning influence certificate alignment Fisher KL finite deletion; and unlearning influence certificate 2026. Abstract/proceedings pages support broad overlap claims, not equivalence of uninspected algorithms. Full-text sections were examined for PRISM and the neural-network certification comparator. OpenReview direct requests returned a browser challenge; PRISM's arXiv v2 metadata independently reports ICLR 2026 acceptance.

GPT constructed the counterexample, checked its numerical values with a small standard-library calculation, and obtained a separate fresh-context GPT mathematical review. The reviewer verified the global-minimizer derivation and postprocessing statement and supplied the parameter/output-law and auxiliary-information qualifications incorporated above. This is not evidence of LLM experimental performance.

Opus was separately assigned the original proposal without the pasted evaluator scores or GPT's preferred result, through the pinned project launcher. The request pinned `claude-opus-5-5` and `max`, but timed out at its 420-second limit with exit 143, an empty response, and no reported model identity. Evidence: `tmp/claude-handoffs/20260924T103751Z-707bf88e/`. There is no Opus verdict or completed cross-model questioning round for this assessment. No retry, fallback model, or effort downgrade was used. The conclusions above rest on the primary-source checks and GPT mathematical review, not cross-model agreement.
