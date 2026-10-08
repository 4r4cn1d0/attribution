# Current workflow handoff

User request, 2026-09-24: install the pasted collaboration workflow here, keeping
GPT as orchestrator, Opus 5.5 at max effort as implementer, and GPT questioning
Opus and helping red-team. Scope is this project.

## Installation in progress

- GPT authored project role instructions and review/assignment templates.
- Opus was requested as exact model `claude-opus-5-5`, effort `max`, to adapt the
  existing handoff launcher in `tmp/workflow-install/`; actual response pending.
- A fresh GPT reviewer challenged the specification before reading implementation.
- Primary checks: exact model metadata, non-Git staging, explicit capabilities,
  distinct returned-versus-verified status, incomplete outcomes, and durable evidence.
- Original research artifacts are preserved; their hashes are recorded in
  `tmp/workflow-install/research-before.json` for completion verification.

Do not infer a successful live handoff or passing tests from this progress entry.
GPT will replace it with the measured installation result after verification.

## Scientific context

The proposal and novelty/rigor assessment are under `research/`. The current
research direction still needs a narrower contribution and evidence that a cheap
seed-dependent surrogate improves total audit cost. No training study was launched
by this workflow installation.
