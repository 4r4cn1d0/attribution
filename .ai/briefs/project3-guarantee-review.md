# Bounded assignment

- Task ID and authorized outcome: Project 3 proposal-stage mathematical review for an ICML 2027 target.
- Role: alternatives and mathematical review; not implementation.
- Model: claude-opus-5-5; effort: max.
- Context supplied: the original proposal below, without another evaluator's scores or verdict. GPT is independently checking primary literature.
- Owned files: none. Read-only assignment; return your analysis in the response.
- Excluded: all file edits, experiments, external calls, other project reviews.
- Deliverable: at most 600 words, one explicit mathematical counterexample, a precise narrower research question, and rigor score out of 5 with justification. Do not assert literature novelty without sources.
- Alternatives: a computable finite-deletion certificate, or an empirical audit distinguishing behavior suppression from deletion effects.
- Smallest decisive check: test whether a vanishing local influence or behavioral KL condition proves the claimed deletion property.
- Permitted execution commands: none. No need for tools or file exploration.
- Limit: 4 turns, 420 seconds. One Opus review call; GPT works on literature concurrently.

You are a worker, not the lead. Do not launch other agents, Claude, or Codex. You are not alone in the codebase; preserve others' edits. Do not modify any files, launch experiments, publish, or provision compute.

## Original proposal

Project 3: Influence-Based Proactive Alignment & Unlearning Verification.
Study how SFT or RLHF changes pre-existing parametric knowledge. Define a Dual-Space Influence Operator mapping training-data influence simultaneously in weight space through gradient trajectories and behavior space through KL divergence of output distributions. Derive a Zero-Influence Boundary Condition identifying when a training subset has been functionally purged from a network's capacity across all activation pathways. Minimize the metric during mini-alignment to remove toxicity or copyrighted data without degrading MMLU/GSM8K performance.

## Questions

1. What must be defined before this can be a theorem? Which weakest assumption admits a concrete counterexample?
2. How do training-data deletion, capability suppression, and distributional indistinguishability differ?
3. Is robustness under subsequent fine-tuning necessarily a new guarantee, or can it follow from a standard contraction/data-processing argument? Specify the access assumptions.
4. Give the smallest defensible contribution and a decisive falsification check. Distinguish a theorem you can establish here from a conjecture requiring work.

Return analysis only. Do not claim novelty or tests you did not verify.
