# Bounded assignment: attribution scope, first-pass alternatives

- Task ID: scope-20260924-first-pass. Authorized outcome: independent design alternatives for a small exact feasibility study; no training runs.
- Role: alternatives, read-only. Model: claude-opus-5-5; effort: max.
- Shared context: AGENTS.md, .ai/WORKFLOW.md, research/strong-candidate-screening.md. Both GPT and Opus receive the same provisional candidate and objections in the screening note. GPT's new first-pass preference has not been supplied. Input hashes are recorded by the lead in tmp/scoping/context-hashes.json.
- Owned files: none. Return the answer in the final response. Do not edit .ai/HANDOFF.md or any research files.
- Deliverable: at most 1,500 words: two mathematically concrete candidate mechanisms and a simplest paired-rerun comparator, one exact tiny learner, a primary occurrence suppression definition, a coupling-class-specific oracle, one achievable theorem target with explicit obstacles, and proceed/revise/stop criteria.
- Measurable acceptance: equations for updates and marginal-preserving couplings; finite suppression distinguished from infinitesimal influence; all remaining optimizer work and coupling fitting/construction included in cost. Identify a plausible reason the proposed mechanism will fail.
- Alternatives: coordinating actions by induced training update is provisional. Generic optimal transport, learned coupling, or multilevel machinery is not itself sufficient novelty. Consider a simpler approach and reject the provisional mechanism if appropriate.
- Invariants: target is E[g(final suppressed)|observed prefix through event t] minus E[g(final ordinary)|same prefix]. Future observations regenerated separately under each learner. Suppressing an occurrence does not remove prior effects of the record. Pick precise handling of optimizer counters, momentum, regularization and weight decay. No universal unlearning claim.
- Exact pilot: small categorical adaptive learner with bounded g and enumerable terminal distribution; stable and self-reinforcing regimes, intervention magnitude and horizon sweeps. Baselines: independent/common randomness/maximal action agreement, strong learned coupling, oracle; fixed-log and truncation as biased alternatives. Oracle must state co-adapted vs unrestricted path coupling, objective, and computational cost. Include replication, data split, marginal checks, exact bias, MSE and total cost.
- Nearest work (do not claim to have verified sections you did not read): Data Attribution in Adaptive Learning (2604.04892), RFT-Inf NeurIPS 2025, CROPI (2510.26491), Learning Generalized Gumbel-max Causal Mechanisms (2111.06888), Anderson (1109.2890), Giles (1304.5472). The lead verifies sources separately.
- Permitted commands: none. Read/Glob/Grep only. No agents or CLI invocations, no experiments, no internet tools.
- Budget: at most 6 turns / 600 seconds. Return a concise answer; do not spend the budget reading unrelated history. Wave: this one Opus call alongside GPT source verification. Earlier timed-out ideation calls are NOT resumed or retried.

You are a worker, not the lead. You are not alone in the codebase; preserve others' edits. Do not launch agents, invoke Claude/Codex, edit shared handoff records, publish, provision compute, or substitute a model.

## GPT's questions
1. Which assumption is weakest, and what concrete counterexample breaks it?
2. What simpler alternative might be as good?
3. Which observable check would distinguish the mechanisms and change your conclusion?
4. What remains unproved, unmeasured, or dependent on source verification?

Return alternatives and answers, actual read-only actions, not-tested criteria, and remaining concerns. Do not claim model metadata or tests you did not observe.
