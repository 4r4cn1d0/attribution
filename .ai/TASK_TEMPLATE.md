# Bounded assignment

- Task ID and authorized outcome:
- Role: alternatives / implementation / review / response to GPT questions
- Model: claude-opus-5-5; effort: max
- Context supplied and input versions/hashes:
- Owned files and workspace:
- Excluded files and concurrent contributors:
- Deliverable and measurable acceptance criteria:
- Alternatives to consider:
- Invariants and smallest decisive check:
- Permitted execution commands (none unless listed):
- Claude time/turn limits: none, per user instruction; only specify if later requested.
- Combined concurrency and scientific compute budget (separate from Claude limits):
- Previous run (if any; supply its relevant content explicitly):

You are a worker, not the lead. Do not launch other agents. You are not alone in
the codebase; preserve others' edits. Do not modify files outside the assignment.
Do not launch experiments, publish, or provision compute unless explicitly included.

## GPT's questions

1. Which assumption is weakest, and what concrete counterexample could break it?
2. What simpler alternative could achieve the same outcome?
3. Which check distinguishes the approaches, and what result would change your mind?
4. What remains untested or merely assumed?

## Return

Changed files, design choice and alternatives, commands actually run with exit
status, evidence paths, passed/failed/not-tested criteria, answers to each question,
and remaining concerns. Do not claim tests or model metadata you did not observe.

## GPT adjudication (lead only)

For each material objection record: source, exact artifact, finding, decisive check,
observed result, accepted/rejected/unresolved disposition, and reason. Inspect actual
files and outputs before integration; run affected checks after fixes.
