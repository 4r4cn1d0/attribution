# Bounded assignment

- Task ID and authorized outcome: bluedot-budget-alternatives-20261013. The user wants a BlueDot grant application, selected a different total from the older$6,000 but gave no amount, and instructed not to submit anything. Independently propose defensible budget alternatives and a recommended local-draft scope.
- Role: alternatives / read-only budget review. You are not the lead.
- Model: claude-opus-5-5; effort:max. No time or turn caps.
- Context supplied: current draft `research/grant/2026-10-13-bluedot-application-DRAFT.md`; old grant draft `research/grant/2026-10-06-bluedot-application-DRAFT.md` sections3/6; the current `research/FOCUS.md`; frozen `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` section9; `runkit/gate-b-olmo/gateb_rules.py` cost functions/constants; `runkit/gate-b-olmo/plan_tool.py` worst_path_need; `research/review/2026-10-11-novelty-rigor-update.md`; and `.ai/inputs/bluedot-budget-20261013/primary-price-notes.md`. These shared sources include past planning suggestions; you are not given GPT's current preferred alternative.
- Owned files/workspace: read-only, no edits. Original project root supplied by launcher.
- Excluded: secrets, data rows/prompts/answers/anchors, hidden or selector.jsonl files; unrelated projects; personal details beyond supplied fields. Do not read credential files or infer academic affiliation from West Lafayette.
- Deliverable: compare a narrowly costed next-phase request with a broader direct-cost request; give exact arithmetic, source or assumption for every item, what each funds/does not establish, and required applicant inputs. Flag cost thresholds versus real spending, completed jobs, cross-project storage, and unsupported human/time quotes. Do not pad a total or invent a study design to exhaust funding.
- Observable success: a defensible grant amount can be proposed for user review without promising an unpriced confirmatory study; current factual uncertainties and remaining personal choices are explicit; no false identity/background/publication/novelty/measurement claims.
- Alternatives: develop your own first-pass options; choose based on scope and evidence.
- Invariants: current frozen GateB rules stay fixed; grant preparation is not experiment or spending authorization; no submission, public release, GitHub mutation, service call, download, account mutation or other agent.
- Permitted commands: none. Read/Glob/Grep only through the launcher.
- Combined concurrency: one Opus call; scientific compute budget:$0.
- Previous run:none for this task.

You are a bounded worker and are not alone in the codebase. Preserve others' changes. Do not invoke agents/Claude/Codex, edit shared handoff records, or recurse.

## GPT questions

1. Which cost/scope assumption is weakest and which concrete counterexample would break the recommendation?
2. What simpler ask could achieve a useful outcome?
3. What source/quote/design check would settle the disagreement?
4. What remains assumed rather than measured?

## Return

Budget alternatives with arithmetic, recommendation and unresolved questions; actual checks and source paths read; routing/effort only as observed; no fabricated test results or credentials.
