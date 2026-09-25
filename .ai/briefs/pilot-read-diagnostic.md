# Bounded read-tool diagnostic

Role: read-only. Model claude-opus-5-5, effort max. Budget 3 turns / 120 seconds.
No prior job is resumed. You are a worker, not the lead. No agents, shell, edits,
or other file reads. Preserve other contributors' files.

Use Read exactly once on .ai/TASK_TEMPLATE.md. Then return only its first line.
Acceptance: actual Read succeeds and the first line is returned. If it fails,
report the exact failure briefly. Do not investigate further.
