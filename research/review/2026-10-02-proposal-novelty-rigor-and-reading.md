# Current proposal: novelty, rigor, and reading priorities

Assessment date: 2 October 2026. Scope: `writing/proposals/roger-grosse-research-proposal.md`, “Choosing Training Data Edits for Safer Language Models.” This is a research-scoping assessment, not a conference review or an acceptance prediction. Earlier reviews and the separate occurrence-level coupling pilot remain intact.

## Verdict

The question is coherent and worth investigating. The current proposal does **not yet establish 4/5 novelty and rigor**. My provisional judgments are **2–3/5 for demonstrated distinctiveness of the proposed contribution** and **3/5 for completeness of the research design**. These are qualitative judgments on the user's requested five-point scale, not calibrated ICML scores. There is no completed experiment on this new selection question from which to judge empirical rigor or practical savings.

The proposal's strongest hypothesis is that influence predictions contain useful information about full-run outcomes beyond short-run predictions, their uncertainty, and edit metadata, and that this information improves safety-edit selection after charging its cost. Disagreement is one possible signal to test. It is not itself a demonstrated innovation or a reliability certificate.

## Novelty: occupied ground and remaining question

| Ingredient | Primary antecedent | Implication |
|---|---|---|
| Influence-guided toxicity intervention | Coalson et al., [IF-Guide](https://arxiv.org/abs/2506.01790), NeurIPS 2025 | Influence-based proactive detoxification is already demonstrated in prior work. Its intervention includes an auxiliary suppression objective; it is not identical to our fixed removal/replacement menu. |
| Predicting removal effects through the training process | Bae et al., [SOURCE](https://arxiv.org/abs/2405.12186), 2024 | Approximate unrolling and subset-removal counterfactual evaluation already exist. Finite edits alone are not a distinguishing claim. |
| Targeted instruction-data selection | Xia et al., [LESS](https://proceedings.mlr.press/v235/xia24c.html), ICML 2024 | Optimizer-aware influence features already support targeted data selection. |
| Cheap training experiments directing costly data decisions | Yen et al., [Data Mixture Optimization](https://arxiv.org/abs/2503.21023), 2025; Chen et al., [ADMIRE-BayesOpt](https://arxiv.org/abs/2508.11551), 2025 | Adaptive allocation across model scales or training fidelities is already applied to language-model data mixtures. ADMIRE includes instruction fine-tuning. Their mixture targets differ from constrained finite safety edits, but they are important competing approaches. |
| Accounting for stochastic training | Mlodozeniec et al., [Distributional Training Data Attribution](https://arxiv.org/abs/2506.12965), 2025 | Training-run variability is an established attribution problem. It is distinct from systematic finite-edit approximation error. |
| Cost-efficient selection among biased cheap and expensive evaluations | Poiani et al., [Optimal Multi-Fidelity Best-Arm Identification](https://arxiv.org/abs/2406.03033), NeurIPS 2024; inspected arXiv v2, May 2025 | The abstract allocation problem already has substantial theory. Its known fidelity-bias bounds and distributional assumptions cannot be silently assumed for short SFT runs. |
| Learning when a proxy saves expensive observations | Ma et al., [PROBE](https://arxiv.org/abs/2607.06879), July 2026 preprint | Proxy calibration and best-arm identification are already combined. Its independent Gaussian arms, paired proxy/reward observations, unit marginal variances, and known proxy means are restrictive; it does not directly solve this LLM study. |

The comparison missing from the one-page reference list is particularly important: **ADMIRE-BayesOpt and Data Mixture Optimization** already connect language-model data choices to adaptive experiment allocation. They should enter the literature comparison before claiming a new decision framework.

These sources do not prove that one existing paper solves our complete proposed task. They do show that combining attribution with adaptive validation needs a more specific contribution than the combination's name or interface.

A defensible candidate claim is: **a signal derived from training-data attribution identifies consequential errors in finite-edit predictions and improves constrained intervention choices at lower total cost than a strong generic selector.** This remains a hypothesis. Adding safety constraints, abstention, or confidence intervals does not automatically make it novel.

Two possible paper routes remain open: a distinct method or theoretical result with useful assumptions and measured benefit; or a substantial empirical finding about when attribution changes intervention decisions, supported across settings. A new theorem is not mandatory, but one small-model toxicity result would support feasibility rather than a broad claim.

## Rigor: strengths and obligations

Already strong in the proposal: frozen candidate menus; separate calibration and evaluation data groups; untouched audit prompts; fresh post-selection training seeds; explicit utility and over-refusal constraints; an uncertain retraining reference; complete compute accounting; and a no-influence ablation. These are appropriate commitments for a one-page proposal.

Before a main study, resolve five points:

1. **Define the target and intervention.** For edit a, let theta(a,r) be the result of the specified SFT algorithm on edited data, starting from the same checkpoint with training randomness r. Define expected safety S(a), utility loss L(a), and over-refusal R(a) over stated training, prompt, and decoding distributions. The intended target can be the maximizer of S(a) subject to L(a) <= tau_L and R(a) <= tau_R. This is different from guaranteeing that a particular newly trained model satisfies both limits with high probability. Specify fixed tokens versus epochs, removed-token treatment, and replacement construction. The unchanged-data option is automatically feasible only when the chosen constraint definitions make it so.
2. **Specify the selector and uncertainty claim.** Freeze the acquisition rule, prediction scales, correction procedure, and budget/abstention rule before evaluation. Fixed-budget empirical decision quality is a legitimate first target. A promise of valid decisions during adaptive inspection additionally needs inference valid for that sampling and stopping scheme. Ordinary intervals do not acquire that guarantee through repeated inspection. Close candidates may remain unresolved; a fixed budget does not automatically identify an exact optimum.
3. **Test shared errors.** As an illustrative counterexample, both predictors can score edits A and B as 0.9 and 0.6 while full-run expected safety is 0.2 and 0.8. Disagreement is zero yet the ranking is wrong. This is a constructed example, not an experimental result. Measure agreement-but-wrong cases, normalize predictors to a common target, and replicate some complete runs to separate seed noise from persistent prediction error. Calibration on selected top-ranked edits alone would be biased.
4. **Use the right replication and reference.** Prompts from one trained model are not independent training replicates. Decision-quality uncertainty also needs repeated selector executions, reflecting acquisition randomness and training noise. Held-out menus or source families are needed for generalization beyond one candidate bank. The largest observed reference mean is not a known optimum; account for uncertainty and winner selection when reporting the gap to the best feasible edit. Keep unresolved feasibility visible.
5. **Charge every method fairly.** Include attribution construction, calibration, short runs, full runs, scoring, and final validation. Give alternatives the same candidate menu and calibration labels, and let them spend saved attribution cost on more experiments. Report one-off and amortized costs separately. Keep the withheld exhaustive reference study outside selector access and disclose its cost separately. Blinded scorer checks should include benign cases where refusal is a failure.

The older constant-predictor objection needs careful transport. For a fixed edit, c + mean(Y-c) = mean(Y), so a seed-constant predictor does not reduce this estimator's within-edit variance. It can still help allocate effort **across edits**. This does not invalidate the current allocation hypothesis; a separate claim of residual-variance savings would need a useful seed-dependent proxy.

## The decisive comparisons

First compare the proposed selector with its strongest development-tuned **no-influence version**, keeping short-run outputs, edit metadata, calibration labels, candidate menus, and audit procedures comparable. Match total compute, allowing the alternative to reinvest avoided attribution costs. Measure independently audited safety decision quality together with utility and over-refusal violations across prespecified budgets. Correlation or ranking accuracy alone is insufficient.

Then compare against a strong **generic multifidelity selector supplied with the same influence and short-run predictions**. The first comparison tests whether attribution contributes information. The second tests whether the proposed allocation mechanism adds anything beyond supplying those features to an existing method. A positive first result does not establish a new allocation algorithm.

If gains disappear after cost accounting, the proposed mechanism is unsupported. That result does not establish that every attribution method or the broader project is futile. If gains survive, explain where they arise and test transfer beyond the development menu before expanding claims.

## Reading route

Take the **training-data attribution plus statistical decision-making** route. Optimal-control and universal-unlearning theory are secondary to the current fixed-menu SFT question. The old adaptive-learning reading list becomes central again only if the project returns to adaptive future trajectories.

Read the first three to locate the gap; read four through seven to formulate the study precisely:

| Order | Paper | Focus and question to answer |
|---|---|---|
| 1 | [IF-Guide](https://arxiv.org/abs/2506.01790) | Sections 3–4: which safety intervention and attribution modifications have already been done? What decision does our selector add? |
| 2 | [SOURCE](https://arxiv.org/abs/2405.12186) | Method and counterfactual evaluation: what training intervention does the predictor approximate, and what does subset removal test? |
| 3 | [ADMIRE-BayesOpt](https://arxiv.org/abs/2508.11551) | Sections 3–4 and multifidelity experiments: why would a strong generic allocator need our influence information? Pair with [Data Mixture Optimization](https://arxiv.org/abs/2503.21023), Sections 2–4, on short-run and scale extrapolation. |
| 4 | [If Influence Functions are the Answer, Then What is the Question?](https://arxiv.org/abs/2209.05364) | Understand the discrepancy decomposition and proximal Bregman response target. Is an observed error approximation failure or a different estimand? |
| 5 | [Distributional Training Data Attribution](https://arxiv.org/abs/2506.12965) | Formulation and main results: which training randomness is averaged over, and how does that differ from surrogate bias? |
| 6 | [Optimal Multi-Fidelity Best-Arm Identification](https://arxiv.org/abs/2406.03033) | Sections 2–4: assumptions on bias, acquisition, stopping, and cost. Which assumptions would our experiment actually justify? |
| 7 | [PROBE](https://arxiv.org/abs/2607.06879) | Sections 2–4: proxy/reward pairing and learned residual variance. What has already been proved, and what assumptions prevent direct use here? This is a 2026 preprint. |

Implementation/context follow-ons: [LESS](https://proceedings.mlr.press/v235/xia24c.html) for practical targeted data selection; [Studying LLM Generalization with Influence Functions](https://arxiv.org/abs/2308.03296) before a deeper technical discussion with Roger Grosse. If the chosen method promises adaptive statistical guarantees, also read [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html) and the prediction-powered sequential literature already recorded in the September review.

For each core paper, write five short notes: target quantity, intervention, assumptions, complete cost, and the precise question it leaves unanswered for us. After the first three, the desired output is one distinguishing hypothesis and its strongest counterexample—not a new name for the method.

## Evidence and limitations

GPT reviewed the current proposal and existing review records, rechecked primary sources, and used a bounded non-author GPT reader (`current_proposal_rigor_audit`) for a fresh-context critique of the proposal's statistical coherence. That reader received the proposal and two historical reviews, so this is not blind or independently sourced corroboration. Its findings on estimands, replication, disagreement, and constant-predictor cancellation were adjudicated in this report.

Existing Opus first-pass and follow-up critiques from `tmp/claude-handoffs/20260928T183535Z-441a9de5/` and `tmp/claude-handoffs/20260928T184859Z-4696e3b5/` were retained as prior project context. No new Opus invocation, implementation, training experiment, external correspondence, or publication action occurred for this assessment. This review does not change the proposed method into an adopted protocol.

Retrieval was targeted, not exhaustive. Exact arXiv metadata queries, executed query strings, versions, and returned counts are saved under `tmp/proposal-review-20261002/` as XML and parsed JSON: core (7/7 IDs), MFBO (1/1), and ADMIRE (1/1). Primary HTML/proceedings and targeted web searches supplemented these records. Some OpenReview opens reached a browser challenge; public arXiv versions and indexed primary excerpts supplied the relevant content. Distributional TDA's abstract was rechecked; its HTML full text failed to open in this pass. No theoretical proof or empirical result from another paper was independently reproduced.
