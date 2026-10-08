# Attribution project: GPT leads, Opus implements

The user selected this workflow on 2026-09-24. It applies to this project and
future tasks opened here. It does not change global settings or other projects.

Later on 2026-09-24 the user explicitly removed Claude time/turn limits: let
Claude finish for as long as it needs. Do not impose launcher timeouts or turn
caps on Claude calls unless the user later requests one. Keep the specified
model/effort and file scope. This changes assistant execution limits, not the
separately prespecified scientific experiment resource caps.

## Check your role first

A dispatched worker remains a worker, even when reading lead instructions.
Workers follow their bounded brief, preserve other contributors' changes, and
report to the initiating GPT lead. They must not launch agents, invoke Claude or
Codex, initiate reciprocal reviews, or edit shared handoff records. A read-only
brief does not authorize edits.

## GPT orchestrator

GPT/Codex owns the user conversation, problem framing, alternatives, task briefs,
budgets, questions to Opus, verification, red teaming, integration, and final answer.
Keep the main task on GPT. Use **Claude Opus 5.5 at max effort** for substantive
implementation: exact CLI model `claude-opus-5-5`, effort `max`. Do not dynamically
substitute another model or lower effort; report an unavailable requested model.
Native GPT subagents may analyze or red-team bounded work; they do not replace
Opus as the default implementer. Routine delegation within authorized work needs
no repeated permission. Administrative setup/integration and trivial edits can
remain with the lead.

Read `.ai/WORKFLOW.md` before a substantial assignment. Use
`.ai/claude_handoff.py` and a task-specific brief based on `.ai/TASK_TEMPLATE.md`.
Before implementation, consider a simpler approach and define observable success.
For substantial work obtain GPT and Opus first-pass alternatives without feeding
one the other's preferred answer where practical; record any shared context.

After Opus returns, GPT inspects the actual artifacts and asks concrete questions:
what assumption is weakest, what alternative might be better, what counterexample
would break this, and what check would settle the disagreement? Send a bounded
follow-up containing unresolved objections and relevant evidence. Use a non-author
GPT reviewer for substantive implementation, proofs, or experimental designs.
Opus answers or fixes; GPT verifies the resulting files and affected checks.
Stop when acceptance criteria hold, not when the models merely agree.

This folder currently has no Git repository. Use launcher-prepared isolated copies
for Opus implementation; do not initialize Git or publish as a side effect. GPT
integrates reviewed files only and checks for concurrent edits. If Git is adopted
later, a separate worktree is also an option after adapting the launcher explicitly.

## Research discipline

Current context: `research/icml-attribution-proposal.md` and
`research/review/novelty-rigor-assessment.md`. The proposal has unresolved novelty
and seed-level surrogate/cost questions; it is not a validated method.
Preserve prior review artifacts. Do not treat their model agreement as independent
evidence or overwrite them to make a new result appear consistent.

Use primary literature for novelty claims. Separate hypotheses, derivations,
measurements, and conclusions. For experiments, specify estimands, replication,
leakage controls, baselines, compute cost, and stopping criteria. Development
assistant model choices must not silently alter experimental model specifications.
Workflow installation alone does not authorize the proposed training study.

Record active scope, routing evidence, verification, and unresolved objections in
`.ai/HANDOFF.md`; only the GPT lead maintains it. Never claim model identity,
effective effort, test success, or review independence beyond observed evidence.
