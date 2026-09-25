# GPT follow-up: challenge the installed Opus handoff

Role: read-only implementation challenge. Model: claude-opus-5-5; effort: max.
You are a bounded worker reporting to GPT. No edits, shell, subagents, or experiments.

Read .ai/claude_handoff.py, .ai/test_claude_handoff.py, AGENTS.md, CLAUDE.md,
and .ai/WORKFLOW.md. GPT is responsible for final verification and integration.

Answer these concrete GPT questions against the actual files, not intentions:

1. Could a zero-exit response containing another model, no model metadata,
   exhausted turn budget, or permission denial still be mistaken for successful
   implementation? Locate the checks and distinguish “returned” from “verified”.
2. Can ROOT, a foreign copy, a symlinked workspace/ancestor, or a forged path be
   accepted as a prepared workspace? Which claims are only procedural rather than
   enforceable boundaries? Do not call the copy a hostile-code sandbox.
3. Do declared “exact” Bash commands really behave as exact CLI rules? Identify
   any mismatch between actual pattern syntax and documentation. Prefer no Bash.
4. If authentication or process startup fails before a model result, what evidence
   survives? If the result is malformed JSON or the wrong JSON type, does the
   launcher exit cleanly with an honest outcome?
5. Is there a simpler implementation that preserves the meaningful guarantees?
   What test result would change your recommendation?
6. Identify any conflict among GPT's instructions, your worker role, and the docs.
   In particular, who may start agents, edit ledgers, integrate changes, and decide
   that work is complete?

Return only material findings with exact locations and a minimal remedy, then
answer the six questions concisely. If no defect is established, say so. Separate
unverified runtime behavior from proven code paths. Limit response to 900 words.
Budget: 8 turns, 600 seconds. No recursive reviews.
