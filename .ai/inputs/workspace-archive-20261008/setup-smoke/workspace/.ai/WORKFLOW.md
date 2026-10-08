# GPT-orchestrated Opus implementation and red teaming

Project-specific installation requested on 2026-09-24. GPT stays in charge of the
task; Opus implements; GPT questions, verifies, and integrates the result. Project
instructions are persisted in `AGENTS.md`, using [Codex's instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
This does not switch the main task's model or change other projects.

## Roles and evidence loop

1. **Frame:** GPT identifies the desired outcome, constraints, current evidence,
   simpler alternatives, and measurable acceptance criteria.
2. **Challenge the design:** for substantial work, GPT and Opus develop first-pass
   options before seeing one another's preferred solution where practical. A fresh
   context does not prove independent errors; record the context actually supplied.
3. **Implement:** GPT sends Opus a bounded brief with owned files, a prepared copy,
   exact inputs, permitted commands, and a time/turn budget. Workers do not recurse.
4. **Question:** GPT inspects the real diff/output and sends specific objections:
   “Why is this better than the simpler alternative?”, “Which assumption fails in
   this counterexample?”, and “What observed result would change your conclusion?”
   Opus responds with reasoning, evidence, or corrected files.
5. **Red-team:** a non-author GPT worker reviews substantive code, proofs, or study
   designs. Supply the artifact and success criteria; avoid supplying a preferred
   verdict. GPT's audit of its own design is not a non-author review of that design.
6. **Resolve and verify:** GPT adjudicates each material objection, runs appropriate
   checks, and integrates only reviewed changes. Follow-up reviews target changed
   claims or unresolved findings. Stop at satisfied acceptance criteria or a concrete
   blocker, not an arbitrary number of debate rounds.

Simple questions and trivial edits need no multi-model ceremony. The lead controls
combined concurrency (normally at most one Opus implementer plus one GPT reviewer)
and explicit per-assignment budgets. Do not launch duplicate work while a worker is
running. A time/turn cap is not a hard dollar or token cap.

## Fixed routing

- Orchestrator, integration, verification, and native reviewers: GPT/Codex.
- Implementation and Claude-side design/challenge work: `claude-opus-5-5`.
- Claude effort: `max`, explicitly requested through CLI and child environment.
- No alias-based routing, fallback model, effort downgrade, or silent retry.
- A runtime response must report the requested model (or a dated snapshot of that
  model). Missing/mismatched routing is not verified success. Requested effort is
  recorded separately; CLI acceptance alone does not prove effective internal effort.

The launcher uses the existing Claude subscription login. It removes API/provider
overrides only from its child environment, does not rewrite credentials or account
settings, and does not enable paid overflow. Availability/quota errors are surfaced.

## Commands

```bash
# Inspect a prepared brief without a model call.
python3 .ai/claude_handoff.py --brief .ai/briefs/task.md --mode review \
  --max-turns 8 --timeout 600 --dry-run

# Read-only Opus design/review response.
python3 .ai/claude_handoff.py --brief .ai/briefs/task.md --mode review \
  --max-turns 8 --timeout 600

# Prepare an isolated copy; works without Git and creates no repository.
python3 .ai/claude_handoff.py --prepare-workspace task-001

# Opus implementation in the returned workspace.
python3 .ai/claude_handoff.py --brief .ai/briefs/task.md --mode implement \
  --workspace tmp/claude-workspaces/task-001/workspace --max-turns 20 --timeout 900

# A follow-up question/fix: include the previous response and concrete objections
# in the new brief. A provenance link does not resume or inherit a conversation.
python3 .ai/claude_handoff.py --brief .ai/briefs/followup.md --mode review \
  --parent-run tmp/claude-handoffs/RUN_ID --max-turns 6 --timeout 600

# Offline checks; no model calls.
python3 .ai/test_claude_handoff.py
```

Review tools are Read/Glob/Grep; implementation adds Edit/Write. Shell commands need
explicit narrow `--allow-bash` rules; GPT normally runs tests itself. No permission
bypass is enabled. CLI restrictions are defense in depth, not a claim that brief
ownership or staged copies form a security sandbox against malicious code.

Prepared copies exclude runtime outputs, Git internals, dependencies, environment
files, and symlinks. Record and deliberately transfer any needed excluded input;
do not silently operate on incomplete context. The original project remains the
integration target. Before copying an edited file back, compare its current hash
with the prepared manifest; resolve concurrent changes rather than overwriting.
The manifest provides provenance, not automatic authorization or security.

## Records and research scope

Each invocation stores its brief, request, response, report, and errors under
`tmp/claude-handoffs/`; implementation copies live under `tmp/claude-workspaces/`.
Preserve useful verified findings in `.ai/HANDOFF.md`, with material objections and
their outcomes. Permission denial, timeout, model mismatch, or incomplete work must
remain visible. A successful model response is not a verified implementation.

This installation configures the collaboration workflow. It does not launch the
attribution training pilot or turn the existing proposal into an established result.
Later substantive requests are executed under their actual scope. Keep research
models, data splits, samplers, and stopping rules separate from assistant routing.
