# Bounded implementation: attribution project handoff launcher

User asks for GPT as orchestrator, Claude Opus 5.5 at max effort as implementer,
and GPT questioning Opus and helping red-team. Implement workflow support only;
do not run scientific experiments or edit research.

You are an Opus worker, not the lead. You are not alone in this workspace.
Preserve others' changes. No agent spawning, Claude/Codex invocation, commits,
external communication, dependency installation, or shell execution.

Your working directory is a staging folder. Read base_handoff.py and base_tests.py.
Own ONLY new claude_handoff.py and test_claude_handoff.py in this staging folder.
GPT will review and install them as .ai/claude_handoff.py and
.ai/test_claude_handoff.py, with ROOT = Path(__file__).resolve().parents[1].
Do not modify the base files or any other paths. Return tests for GPT to run;
do not claim you ran them.

Adapt the existing small launcher rather than introducing a framework:

1. Pin default and accepted model to claude-opus-5-5 and effort to max. Never
   silently choose an alias, fallback model, or different effort. Document the
   constants so an explicit later user change is possible. Keep existing child-only
   environment cleanup, recursion guard, subscription auth check, safe/restricted
   mode, limited tools, no MCP/plugins, and bounded timeout/turn behavior.
2. Support this NON-GIT project. Git metadata is optional; lack of a repository is
   not an error and must not trigger git initialization. Read-only review operates
   in ROOT. Implementation must reject ROOT and all unprepared workspaces.
3. Add --prepare-workspace NAME (without --brief) to copy the project to a unique
   ROOT/tmp/claude-workspaces/<NAME>/workspace directory. Use a restrictive name
   validator, reject existing destinations/symlinks, exclude tmp, .git, caches,
   environments, node_modules, .env files and symlinks. Record a manifest OUTSIDE
   the worker workspace containing the source root and original file hashes.
   Do not recursively copy previous workspaces. Use this manifest to verify
   --mode implement --workspace PATH belongs to this project's prepared copies.
   The manifest is audit metadata, not a security boundary against malicious code.
4. Keep launch review versus implementation capabilities explicit. Review has only
   Read/Glob/Grep; implementation adds Edit/Write; shell requires exact --allow-bash
   commands. No permission bypasses. GPT normally runs checks separately.
5. Preserve per-run brief, command, timeout, response, stderr, requested model/effort,
   actual reported modelUsage, and status in ROOT/tmp/claude-handoffs. A successful
   CLI response with a missing model identity, a different model identity, a budget
   exhaustion subtype, or is_error must not be labeled verified success. Permit an
   exact requested ID or its clearly dated snapshot; reject extra routed models.
   Surface permission denials as incomplete, not verified implementation completion.
   Record requested effort separately from model-reported evidence (do not claim
   the API confirms effective effort when it does not). No silent retries.
6. Add --parent-run PATH as an optional provenance link for follow-up questioning.
   It need not resume a session; the lead supplies required prior context in the
   new brief. Never auto-approve/integrate edits. Return changed-file hash summary
   for a prepared workspace so GPT can inspect changes. Handle non-GIT metadata,
   invalid/non-object JSON, process interruption, and missing tool gracefully.
7. Offline stdlib unittest coverage for meaningful boundaries: exact routing,
   capability split, recursion/env isolation, non-GIT operation, staging exclusion,
   main/unprepared rejection, model mismatch/missing metadata/errors/denials,
   timeout path if feasible. Tests must not call a real model or depend on Git,
   installed CLI or user's auth. Keep implementation reasonably small and clear.

Acceptance: useful launcher for this project, bounded worker roles, exact model
request with observable routing evidence, isolated copies for implementation,
read-only reviews, preserved diagnostics, offline tests passing after GPT runs them.

Also answer these GPT questions in your return report:
- What is the simplest alternative, and why adapt the existing launcher?
- Which parts are enforced by the CLI versus only by the task brief?
- What failure would most plausibly make a successful-looking handoff misleading?
- Which claimed properties require a live smoke check rather than unit tests?

Budget: 20 turns, 900 seconds. Do not spawn workers. Return changed files, check
instructions, limitations, and concrete objections. GPT will challenge your answer.
