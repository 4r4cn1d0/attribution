# Choosing Training Data Edits for Safer Language Models

Research proposal for discussion | September 2026

**Question.** Given a measurable safety failure and a fixed menu of post-training data removals or replacements, can we identify the edit that most improves safety on held-out examples, subject to limits on utility loss and over-refusal, without fully retraining every candidate?

**Motivation and prior work.** SOURCE predicts data-removal effects through approximate unrolled differentiation [1]; IF-Guide already uses influence-based interventions to reduce toxicity [2]; distributional attribution studies effects across stochastic training runs [3]. I want to investigate when these tools support a reliable intervention decision. Finite group edits can invalidate local approximations, and uncertainty across training seeds does not capture systematic prediction error. I propose testing whether attribution-specific error signals improve how validation compute is allocated. A useful result would require better edit choices at matched total compute; novelty remains to be established.

**Working hypothesis and approach.** Disagreement between influence-based predictions and short training continuations may identify edits whose apparent safety benefit or utility cost is unreliable. I propose using these signals to allocate a limited number of complete post-training runs, correcting candidate estimates as evidence arrives. The selector would distinguish training variability from surrogate error, retain the unchanged-data option, and report when its budget cannot resolve the decision. The decisive comparison is the same selector without influence scores, given the same calibration edits and total compute budget. I would also measure how often both predictors agree yet misrank unseen edits.

**First experiment.** I would start with one small open-weight model, a fixed supervised fine-tuning recipe, and one prespecified failure mode, such as toxic responses. I would freeze the candidate menu, utility and over-refusal limits before evaluation. Edits would span group removals and replacements at different sizes. Runs would restart from the same pre-SFT checkpoint, with a fixed schedule and treatment of removed tokens. Randomly sampled calibration edits and evaluation edits would use separate underlying data groups. Selectors could access validation prompts; final comparisons would use untouched audit prompts and fresh training seeds after each selector commits to an edit. Blinded checks of sampled outputs would audit the safety scorer.

**Comparisons and success criteria.** Selection baselines would include random and toxicity-based rankings, influence/SOURCE rankings, uniform or adaptive retraining, and generic multi-fidelity selection using short and full runs. Selectors would share a candidate menu and compute budget; IF-Guide would provide a separate end-to-end toxicity baseline. An exhaustive, repeated-retraining study of the small menu would provide an uncertain reference for the best feasible edit. I would measure the safety gap to that reference, utility and over-refusal constraint violations, uncertainty calibration and total compute. Scoring, calibration, short runs and final validation would all count; shared reference-study costs would be reported separately and its results withheld from selectors. Success requires a better decision-quality-versus-compute trade-off than the strongest baseline. If selective validation adds no benefit after overhead, the proposed method is unsupported.

**Preparation and guidance sought.** I have completed a separate toy pilot on occurrence-level attribution and variance reduction; it did not establish data-edit selection or practical savings. I am now scoping this study. I would value your view on whether the finite-edit error problem offers a substantive gap beyond existing attribution and adaptive evaluation methods, and which smallest experiment would most convincingly test it.

**Selected references**

[1] Bae et al. (2024). [Training Data Attribution via Approximate Unrolled Differentiation](https://arxiv.org/abs/2405.12186).

[2] Coalson et al. (2025). [IF-Guide: Influence Function-Guided Detoxification of LLMs](https://arxiv.org/abs/2506.01790).

[3] Mlodozeniec et al. (2025). [Distributional Training Data Attribution: What do Influence Functions Sample?](https://arxiv.org/abs/2506.12965)
