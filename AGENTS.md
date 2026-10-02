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

The user authorized a private GitHub repository on 2026-09-25. Continue using
launcher-prepared isolated copies for Opus implementation; Git adoption alone does
not change the launcher's workspace contract. GPT integrates reviewed files only
and checks for concurrent edits. A separate Git worktree is also an option after
adapting the launcher explicitly. Do not publish or change repository visibility
as a side effect of unrelated work.

## Research discipline

Current question: does training-data attribution improve finite safety-data edit
decisions beyond short training runs, edit metadata and strong content classifiers,
after charging its cost? Use `research/FOCUS.md` and
`research/review/EDGE_CHECKS.md`, the current
`writing/proposals/roger-grosse-research-proposal.md`, and the latest dated reviews.
Novelty, useful incremental information and practical benefit remain hypotheses.
The older `research/icml-attribution-proposal.md`, coupling pilot and its reviews
describe historical work; do not silently restore that earlier scope.
Preserve prior review artifacts. Do not treat their model agreement as independent
evidence or overwrite them to make a new result appear consistent.

Recheck primary literature and rigor when the contribution changes, before a main
experiment, after consequential results and before submission. Follow the review
checkpoints in `.ai/WORKFLOW.md`. Separate information gains, decision gains after
costs and any new allocator's gains against a generic method with identical inputs.
A negative or inconclusive result constrains that mechanism; it does not by itself
end the project. Weekly reviews are bounded checks, not permission to train, spend,
publish or change scope.

Use primary literature for novelty claims. Separate hypotheses, derivations,
measurements, and conclusions. For experiments, specify estimands, replication,
leakage controls, baselines, compute cost, and stopping criteria. Development
assistant model choices must not silently alter experimental model specifications.
Workflow installation alone does not authorize the proposed training study.

Record active scope, routing evidence, verification, and unresolved objections in
`.ai/HANDOFF.md`; only the GPT lead maintains it. Never claim model identity,
effective effort, test success, or review independence beyond observed evidence.
