Start scoping the attribution research project in this Implementation task.

The user’s objective is an ICML-level paper combining training-data attribution (Category 3) with faithful evaluation and auditing (Category 4), targeting approximately 4/5 on both novelty and rigor. This is a research target, not an achieved score or an acceptance forecast. GPT remains the orchestrator; Claude Opus 5.5 at max effort handles substantive implementation. Begin the authorized scoping work now and produce concrete research and implementation specifications, rather than stopping at an acknowledgment.

Project context and documents
Work in /Users/spiderishi/Coding/attribution. First read:
- /Users/spiderishi/Coding/attribution/AGENTS.md
- /Users/spiderishi/Coding/attribution/.ai/WORKFLOW.md
- /Users/spiderishi/Coding/attribution/.ai/TASK_TEMPLATE.md
- /Users/spiderishi/Coding/attribution/.ai/HANDOFF.md
- /Users/spiderishi/Coding/attribution/research/strong-candidate-screening.md

The screening document is the main research handoff. Preserve the earlier proposals and reviews, especially research/icml-attribution-proposal.md, research/review/novelty-rigor-assessment.md, and research/review/project3-novelty-rigor.md. They provide history and objections, not validated methods.

Current lead candidate
Working title: “The Price of Faithful Attribution in Adaptive Post-Training.”

Question: Can we estimate a training event’s finite effect on an adaptive learner—when intervening on that event also changes the learner’s future training data—accurately at substantially lower total cost than repeated counterfactual training runs?

Example: an early reasoning update changes the answers a model generates; those answers become later training data; later learning changes again. The target includes that downstream feedback. The initial paper should concern attribution accuracy and cost. Unlearning is a motivating application, not a claim that we can prove universal erasure of knowledge.

This direction is provisional. No candidate has yet demonstrated 4/5 novelty and 4/5 rigor. Scoping must decide whether there is a real, tractable new contribution; it must be willing to reject this mechanism if the evidence is unfavorable.

Initial estimand to formalize
Given a fixed observed training prefix h_t, including the observation at event t, compare ordinary training with an intervention suppressing that event’s learning contribution. Regenerate future observations under each world’s respective learner. For a prespecified bounded terminal behavior score g, target:

Delta_t(h_t) = E[g(Theta_T^suppressed) | h_t] - E[g(Theta_T^ordinary) | h_t].

Specify the intervention precisely: zeroing an observation’s gradient contribution, skipping an entire optimizer step, and deleting all occurrences of a record are different interventions. Explain what happens to momentum, weight decay, schedules, and optimizer counters. Choose one primary definition and keep all baselines aligned to it.

An occurrence-level intervention does not remove a document’s earlier effects on the fixed prefix. A zero effect on one mean behavior score is not distributional unlearning. Include optimizer state, relevant environment state, replay buffers, and all necessary randomness in the formal learning process. Different couplings may be used to estimate the difference of expectations, but each marginal process must remain correct. Do not claim a unique individual counterfactual from an arbitrary coupling.

Closest prior work—read and verify the relevant primary sections
1. Data Attribution in Adaptive Learning: https://arxiv.org/abs/2604.04892
   Already formalizes occurrence-level adaptive intervention, replay-versus-regeneration distinctions, replay-side nonidentifiability, an importance-weighting identification class, sign failures, and feedback-depth approximation bounds. None of those broad ideas is our novelty.
2. Understanding Data Influence in Reinforcement Finetuning / RFT-Inf, NeurIPS 2025:
   https://proceedings.neurips.cc/paper_files/paper/2025/hash/3755a02b1035fbadd5f93a022170e46f-Abstract-Conference.html
   Includes a finite sample-removal target, a first-order estimator, and error analysis. Distinguish its target and assumptions precisely.
3. CROPI, Data-Efficient RLVR via Off-Policy Influence Guidance:
   https://arxiv.org/abs/2510.26491
   Off-policy influence estimates and curriculum data selection already exist.
4. Learning Generalized Gumbel-max Causal Mechanisms, NeurIPS 2021:
   https://arxiv.org/abs/2111.06888
   Learning couplings to reduce counterfactual-effect estimation variance is already established.
5. Anderson, coupled finite-difference sensitivities:
   https://arxiv.org/abs/1109.2890
6. Giles, Multilevel Monte Carlo methods:
   https://arxiv.org/abs/1304.5472

Also consider later citing work and relevant primary literature through the current date. Record searches and exact supporting sections. Do not interpret a missing search result as proof of novelty. The other screened avenues—descendant unlearning, selection-inclusive attribution, and order-dependent unlearning—also have direct precedents; consult the screening note before returning to them.

Candidate mechanism to investigate, not an established solution
For a finite-action, entropy-regularized adaptive learner, investigate coordinating the two worlds’ sampled actions according to the optimizer updates they induce, rather than solely maximizing identical sampled actions. The intended result is an efficiently computable, exactly marginal-preserving coupling that improves the variance–cost tradeoff using the structure of the learning process.

An optimal-transport formulation or a generic learned coupling is not sufficient novelty. Neither is applying standard multilevel or randomized debiasing machinery. Seek a precise training-specific advantage, derived from actual update equations, with explicit dependence on horizon, intervention magnitude, feedback strength, and construction cost. Compare at least two plausible mechanisms, including the simplest paired full-rerun estimator. Do not force a multilevel hierarchy if a simpler method is stronger.

Known objections that the scope must address
- Feedback depth is not computational depth. After L regenerated rounds, measuring terminal behavior may still require T-L optimizer updates at altered parameters. Factual cached gradients generally cannot replace these updates.
- A bound on mean truncation bias does not establish a bound on coupled correction second moments.
- Assuming global contraction and plugging it into a standard theorem is unlikely to be enough new theory. Explain whether assumptions permit meaningful self-reinforcing learning.
- Coupling overhead, full probability access, optimizer work, generation, terminal evaluation, checkpoint storage, and any fitting/calibration cost must be counted.
- Distinguish finite suppression from infinitesimal influence. Do not silently change the target to make a baseline or proof work.
- Exact finite-action theory does not establish an arbitrary-LLM guarantee.
- Replication must respect dependence among interventions from the same training run. No tuning on held-out evaluation queries or treating a noisy retrain as exact truth.

Smallest decisive pilot to scope
Design a tiny categorical adaptive learner whose short-horizon terminal law can be enumerated exactly. Sweep feedback strength, intervention size, horizon, and reward/feature structure, including stable and self-reinforcing regimes.

Compare independent full reruns, common-randomness paired reruns, maximal action-agreement coupling, a strong learned-coupling baseline, the proposed practical mechanism, and an oracle coupling under an explicitly specified finite-state objective and admissible coupling class. Include fixed-log and truncated attribution as biased alternatives and report their actual bias. Explain how any RFT-Inf/CROPI comparison is aligned to the same estimand; otherwise label it as a proxy comparison.

Specify marginal-correctness checks, exact bias, repeated-estimator MSE, relevant correction moments, confidence/uncertainty reporting, and the complete cost–accuracy frontier. If the oracle has no meaningful advantage, ordinary coupling already matches it, or tail optimizer work erases savings, that should be a stop/pivot result for this mechanism. An oracle’s variance advantage is not a practical speedup.

Define measurable proceed/revise/stop criteria before measurements. Recommend a minimum practically useful improvement and justify it; do not present a chosen threshold as a conference rule. Scope later small-model experiments only conditionally on this pilot passing. The user has not specified compute; use one GPU as a provisional planning assumption and provide CPU-first and one-GPU budget scenarios without assuming hardware availability.

Deliverables for this scoping pass
Create /Users/spiderishi/Coding/attribution/research/scoping/ and produce:
1. SCOPE.md: research question, exact target, assumptions, exclusions, candidate contribution, alternatives, and a candid proceed/revise/stop recommendation.
2. PRIOR_ART.md: source-verified claim-by-claim comparison, what is already known, the precise possible gap, search coverage, and unresolved overlaps.
3. THEORY.md: definitions, candidate theorem statements with proof obligations, counterexamples/failure regimes, and a clear separation between derivations, conjectures, and established results.
4. PILOT_SPEC.md: finite-state setup, exact enumeration plan, baseline definitions, parameter grid, estimands, metrics, replication, leakage controls, full cost accounting, and falsification criteria.
5. IMPLEMENTATION_PLAN.md: minimal modules/interfaces, dependencies, correctness checks, output schemas, CPU/GPU resource estimates with assumptions, and bounded implementation tasks with file ownership.
6. REVIEW.md: GPT’s concrete questions to Opus, any actual responses, non-author review findings, dispositions, and remaining objections.

Keep the documents cohesive and proportional. Do not invent results or write a finished-paper narrative. Analytical checks needed for scoping are appropriate; this assignment is not authorization for a substantial training study, paid compute provisioning, or publication. Avoid scaffolding an entire system before selecting the estimand and feasibility test.

Workflow and handoff
Follow the existing project workflow. GPT owns framing, source verification, alternatives, questions, review, and integration. Use exact claude-opus-5-5 with max effort through .ai/claude_handoff.py for bounded Opus design/implementation work; no model substitution or effort downgrade. Use isolated prepared workspaces for substantive implementation and preserve others’ edits.

The earlier Opus ideation call in tmp/claude-handoffs/20260924T104712Z-2f5d74b9/ timed out at 240 seconds without a response or returned model metadata. It contributed no scientific result. Do not silently retry that failed job or claim a completed cross-model review. A new, bounded scoping assignment is authorized; report its actual outcome and routing evidence. If Opus cannot return, continue useful GPT-owned scoping and clearly identify which requested implementation/review work remains incomplete.

For substantial design work, obtain GPT and Opus alternatives before supplying one side with the other’s preferred answer where practical, then question assumptions, simpler alternatives, counterexamples, and decisive tests. Use a non-author GPT reviewer for the theory/experimental design. Agreement is not evidence; resolve objections through sources, mathematics, or a specified check. Avoid redundant reviewer loops.

This Implementation task may maintain the scoping records and append its status to .ai/HANDOFF.md as the GPT lead for this phase. Preserve existing entries. The research task is 01a0d2a2-99b1-70a0-8337-4fbaa3f95ebf; no need to create another task or recurring automation.

Start by inspecting the existing context and identifying the hardest unresolved novelty and feasibility questions. Complete the scoping artifacts and report a concrete recommendation, evidence, and remaining gaps. Ask only for missing information that materially blocks a decision; proceed with explicitly labeled assumptions where possible.

