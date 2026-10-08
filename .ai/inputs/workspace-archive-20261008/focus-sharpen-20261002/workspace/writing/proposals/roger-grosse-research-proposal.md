# When Does Training-Data Attribution Help Choose Safety Data Edits?

Research proposal for discussion | revised October 2026

**Question.** A fine-tuned language model shows a measurable safety failure, and we can remove one of several predefined fine-tuning data groups. Given short training runs, edit metadata and a strong content classifier, does training-data attribution still help pick the removal that most reduces the failure within side-effect limits, at equal total compute?

**Prior work.** SOURCE predicts removal effects [1]; IF-Guide uses influence to reduce toxicity [2]. DATE-LM benchmarks attribution for safety filtering with retraining, safety-aligned distractors and runtime [3]; attribution has been used to mitigate emergent misalignment while retaining another behavior [4]; and attribution-based filtering of subliminal learning helped inconsistently [5]. Cheap runs already guide costly data choices [6]. A reliability benchmark, safety endpoint, side-effect preservation or cost reporting is not alone a contribution. A candidate gap, pending full verification, is matched-compute decision value beyond strong cheap controls, and when it arises.

**Hypothesis.** Attribution may carry information about full-training outcomes that these controls miss. Or it may add only cost: if outcomes are independent of it given those controls, correlation with outcomes does not help. Agreement is no certificate: if two groups each teach the failure, removing one can fool attribution and short runs alike while full training relearns it.

**First study.** One small open-weight model, one fixed supervised fine-tuning recipe restarted from one checkpoint, toxic completions as the single failure, and removals only, with replacements a possible extension. Each removal's target is its effect on held-out failure rate, averaged over training seeds, prompts and sampling, within prespecified limits on benign-utility loss and over-refusal; these govern average effects, not each trained model. Development and confirmation use separate data groups, menus, prompts and seeds; a withheld reference retrains every confirmatory removal repeatedly.

**Decisive comparisons.** First, an existing constrained multi-fidelity selector with and without attribution, both given metadata, classifier scores and short runs; the attribution-free version reinvests the saved cost in extra runs. This measures practical decision value at that budget. Second, only if I propose a new allocator, a two-by-two comparison with the generic selector, each with and without attribution, on identical inputs and budget; a win shows an empirical algorithmic advantage, not by itself a new method. Selectors run repeatedly at fixed budgets, pay all costs, and must keep constraint violations below a prespecified level; margins are fixed beforehand.

**First check.** On development data, I would compare equally flexible, comparably tuned predictors using those controls with and without attribution, on a prespecified selection-relevant loss, such as regret and feasibility errors on held-out data groups, not average error. A screen sized to detect a practical gain can rule it out cheaply; a negative or inconclusive result would constrain this mechanism, not show that attribution cannot help. Model, compute and sample sizes remain open; my earlier toy pilot tests a different question.

**Guidance sought.** Is matched-compute decision value the right first test, and which attribution method best matches finite removal outcomes here?

**References**

[1] Bae et al. (2024). [SOURCE](https://arxiv.org/abs/2405.12186).

[2] Coalson et al. (2025). [IF-Guide](https://arxiv.org/abs/2506.01790).

[3] Jiao et al. (2025). [DATE-LM](https://arxiv.org/abs/2507.09424).

[4] *Mitigating Emergent Misalignment with Data Attribution*. OpenReview.

[5] Weckbecker et al. (2026). [Can Data Attribution Filter Out Subliminal Learning? Not Reliably](https://arxiv.org/abs/2609.20027).

[6] Chen et al. (2025). [ADMIRE-BayesOpt](https://arxiv.org/abs/2508.11551).
