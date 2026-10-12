# Bounded assignment: causal follow-up alternatives

- Task ID and authorized outcome: side-project-cause-20261012. User instructed
  “Establish cause” after discussion of why OLMo-1B's Scheduled-recipe benefit
  was not established in OLMo-7B / Llama-8B.
- Role: first-pass alternatives and causal design challenge; READ ONLY.
- Model: claude-opus-5-5; effort: max.
- Context supplied: shared outcome evidence and scientific limitations below.
  GPT's preferred next design is deliberately not supplied to this first pass.
- Owned files: none. No edits, shell commands, agents, model calls or cloud actions.
- Deliverable: a minimal feasible investigation that can discriminate actual
  explanations, including estimands, independent replication, controls,
  falsification criteria, plausible costs, and what causal claims remain impossible.
- Claude time/turn limits: none, per the user.
- Scientific compute budget: review spends $0. Account currently approximately
  $35.62; about $1.86 of that is separately reserved for ongoing probe recovery.
  Do not treat this balance as approval for a larger-budget experiment.

You are a worker, not the lead. Do not launch agents or Claude/Codex. Do not modify
shared handoffs, prescribe paid overflow, provision pods, train, or publish.

## Shared context

The Side Project paper/workspace is
`.claude/worktrees/peaceful-jepsen-8b8eee/`; its corrected paper is
`writing/side-notes/arxiv/main.tex` within that workspace. Existing results and
registrations are under `research/side-notes/`, especially
`prereg-results-20261011/` and `2026-10-11-prereg-results.md`. Preserve historical
wording in raw records; the corrected paper discloses inconclusiveness/equivalence
limits. These are development results, not a fresh held-out confirmation.

Main recipes/configuration/engine are under `experiments/safety_selection/`.
Constant recipe uses per-example response NLL, constant LR1e-4. Scheduled recipe
uses token-mean NLL, four-step warmup and cosine decay, peak LR1e-4. Data are
4,800 examples, effective batch128, one epoch; approximately38 optimizer steps.

Main erosion means (percentage-point increases in Qwen3Guard Unsafe share):
OLMo-1B45.1→28.8, Llama-1B59.3→57.1, OLMo-7B44.1→50.3,
Llama-8B60.7→59.2 under Constant→Scheduled. Three training seeds per main cell.
1B OLMo-minus-Llama recipe interaction =-.573[-1.019,-.127] logit units;
large-model interaction=+.334[-.487,+1.155]. Do not infer a causal size effect
or reversal from these two significance labels. HarmBench large interaction is
also inconclusive. Qwen's extra results are not the immediate replication target.

Half-LR Constant at7–8B lowers OLMo mean to31.9 (three seeds), Llama to53.25
(two seeds). Their relative LR effects are inconclusive, not equivalent.
OLMo-1B token-mean-only mean41.9 versus Constant45.1 and Scheduled28.8.

Native releases differ: OLMo0425-1B versus1124-7B, Llama3.2-1B versus3.1-8B.
Training-engine identities differ in some existing1B comparisons. OLMo-7B
config selects the OLMo-1B tokenizer. Publisher cards report different native
initial-BOS conventions; inspect actual pinned templates and codec before
concluding this caused an effect. Both old7B recipe arms share that tokenizer.

Representation coverage is now19/24 after recovery, but do not inspect newly
recovered effect values for selecting a hypothesis. The existing13-unit paper
analysis is a harmful-versus-harmless-task mean-separation proxy, observational,
with one or two seeds per cell. It is not a causally validated refusal direction.
The prior paper narrative and family comparison could be overinterpreted.

Existing RunPod kits and frozen units are under `tmp/family-probe-*`; the
operator/cost/recovery records are in `tmp/sp-repr/resume-20261012/`.
No new training is running for this request. Main Gate B is paused; keep it so.

## Questions

1. Which concrete cause can be identified within these constraints, and which
   would require a different matched model series or new interventions?
2. What is the simplest decisive controlled comparison, and what counterexample
   would invalidate it? How do you separate engine/serialization artifacts from
   optimization and alignment history?
3. How should replication, prompt leakage, utility and over-refusal be controlled?
4. What observation would falsify each proposed explanation? What can a small
   diagnostic establish, and what would remain inconclusive?

Return alternatives and exact evidence paths. Do not claim tests or model metadata
you did not observe. No edits or execution commands are permitted.
