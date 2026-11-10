# Current manuscript: COLING main and NAACL Findings

13 October 2026. Author-requested working assessment, not an official peer review, an editorial outcome or a calibrated probability. Paper snapshot: `9e0b0ed`. All experimental findings are development evidence.

## Judgment

NAACL Findings is the stronger current fit: a credible candidate, with meaningful rejection risk. COLING main is plausible but borderline. The paper is worth submitting as a bounded empirical model-analysis study. There is no evidence that supports a specific percentage, or a claim of at least 70% acceptance likelihood. Submission eligibility, access to reviewing capacity and committee acceptance are separate questions; this assessment is conditional on receiving review and does not verify the author's account or submission.

## What supports the case

- Six instruct checkpoints, three training seeds in every main Constant/Scheduled cell, matched training rows and recipe comparisons (Sections 2–5, Tables 1–3).
- At the smaller sizes, OLMo's recipe reduction is greater than Llama's and Qwen's, with both interaction intervals excluding zero on Qwen3Guard and HarmBench. This is the strongest evidence for the incremental matched comparison, rather than a new discovery that benign fine-tuning can erode safety.
- Later prospective tests, an inconclusive larger-model replication, judge disagreement and failed predictions are reported rather than hidden. The one-fresh-seed component block controls initialization, training order and evaluation within fixed checkpoints; it is a useful diagnostic, not a general mechanism.
- Explicit screening history, claim status, precision limits and safety/utility tradeoffs support appraisal. Detailed appendix settings and the prepared numerical/configuration artifacts support reproduction of analyses within their stated coverage.

## What could cause rejection

1. **Incremental contribution.** Prior work already studies family heterogeneity, optimization sensitivity and refusal changes. The new OLMo measurements and matched comparisons are useful, but a main-track reviewer may find their conceptual or practical advance too limited. Neither a reusable predictor for a new checkpoint nor a validated refusal-direction mechanism is established.
2. **Limited confirmation.** Safety evaluation uses development prompts; the exact first interaction test was specified after 11 of 12 values were known. Main cells have only three training seeds. Several tests share cells without multiplicity adjustment, and larger-model interactions remain inconclusive or judge-dependent. Honest disclosure does not remove these constraints.
3. **Safety/utility interpretation.** OLMo-1B's lower Unsafe share accompanies greater benign refusal relative to Constant. The component pilot's additional token-weighting reduction also loses ARC answers. Lower erosion is not an established broadly useful safety fix. The fiction comparison has wide margins and changes instruction following.
4. **Artifact scope.** Current release scripts reproduce numbers from saved labels and aggregates, with exact recipe documentation. They do not rerun training, judge inference or representation extraction. These limits must remain visible when adding an anonymous code link.

## Strongest honest contribution

Across six instruct checkpoints, matched benign fine-tuning recipe changes produce model-dependent refusal and compliance outcomes, with cross-judge support for two smaller-model OLMo contrasts, unresolved transfer to larger checkpoints and measurable benign-refusal tradeoffs.

## Official criteria and closest literature checked

ARR's [review form](https://aclrollingreview.org/reviewform) prioritises soundness and reproducibility for Findings; conference recommendations also consider novelty and impact. Its recommendation labels are not admission cutoffs. The [reviewer guidelines](https://aclrollingreview.org/reviewerguidelines) recognise model analyses, reproduction work and negative results as valid contribution types; lack of a new method or a new state-of-the-art score is not inherently disqualifying.

Both calls cover this topic: [COLING 2027](https://2027.coling-iccl.org/calls/main_conference_papers/) lists alignment/security and model analysis; [NAACL 2027](https://2027.naacl.org/calls/main_conference_papers/) explicitly welcomes empirical and reproducibility contributions.

The bounded literature check reopened these primary abstract records (not a new exhaustive full-text survey):

- [Family heterogeneity](https://arxiv.org/abs/2606.28843) [The Heterogeneous Safety Impacts of Benign Multilingual Fine-Tuning, Hawkins et al.]. The abstract reports heterogeneous safety drift across models and languages.
- [Optimisation sensitivity](https://arxiv.org/abs/2508.12531) [Rethinking Safety in LLM Fine-tuning: An Optimization Perspective, Kim et al.]. The abstract studies training hyperparameters and a safety-preserving optimization technique.
- [Mechanistic precedent](https://arxiv.org/abs/2609.01455) [When Safety Routing Breaks: Understanding Alignment Fragility under Benign Fine-Tuning, Guo et al.]. The abstract advances a Fisher-geometric routing account; it is not evidence that this paper's exploratory proxy is causally validated.

Their contents are already discussed in Section 10. The contribution judgment is an inference from the current manuscript and this nearest-literature check, not an assertion that all literature has been searched.

## Review provenance and limits

The user owns the manuscript and requested this private author-side assessment. The lead assistant helped draft it, so its judgment is not independent of the writing process. A fresh native GPT reader, Pauli, received the current PDF's main text and limitations (pages 1–10), component appendix (pages 24–25), the official rubric and scope; it did not receive old venue verdicts. It returned a borderline-to-favourable Findings assessment and a borderline COLING-main assessment. It did not independently recheck literature or reproduce the results. Role separation does not establish independent errors or independent experimental evidence. The lead checked cited source pages and adjudicated the result. Intake declarations passed the peer-review skill's local validator; that does not certify merit.

The [joint commitment FAQ](https://2027.coling-iccl.org/faq/) permits one primary conference and an optional secondary. NAACL can offer main or Findings, while COLING offers main. Secondary consideration is discretionary; there is one final outcome. If NAACL including Findings is the author's real first preference, NAACL primary with COLING secondary is consistent with that preference. The ARR preferred-venue field remains non-binding.

No manuscript change, experiment, submission, account verification or publication occurred as part of the venue assessment. The subsequent user instruction to publish an anonymous code artifact is a separate, explicitly authorised action; its status is recorded separately.
