# Pending bounded resume and interrupted-cost follow-up

Dispatch only after current cost-scope call returns and its actual artifacts are
checked. Exact claude-opus-5-5, max effort, no time/turn cap. Same isolated copy;
owned safety_decision_policy/** and its decision protocol only. Worker rules:
no agents/Claude/Codex/shell/cloud/sharedHANDOFF; preserve concurrent work.

Non-author review of immutable second snapshot identified two residual paths.
Read the supplied finalized stage-b-review-second.md and subsequent cost-call
report/checks. Inspect whether the cost amendment already resolves any part;
change only remaining material issues, preserving prior fixes.

1. run_block's early existing result.json return must verify the result/config,
   lock content and lock hash before returning hidden-derived results. A completed
   block with its lock removed or corrupted must refuse on re-entry, just like
   ensure_op and verify_study. Cover final-incomplete cached results too as
   applicable; do not rerun completed scientific work or overwrite evidence.
2. Analysis must retain paid receipts from started blocks without result.json.
   Current CLI passes only started IDs; present/results-only aggregation drops
   their known paid work and physical_controller_seconds. Read explicit validated
   receipt evidence, include known incurred costs as lower bounds with unresolved
   future/timing unknowns, and keep all configured endpoints missing-bounded.
   Never label an interrupted block complete or replace its seed. Preserve the
   amended selection/chosen-model vs reference research scopes; no unknown zero.

Add narrow regressions using the actual public resume/analyze paths. Return the
weakest assumption, better simpler alternative, breaking counterexample and check
that settles it. Root will run tests and get targeted non-author verification.
Further exact findings/evidence will be appended before dispatch. No gratuitous
refactoring or new scientific scope.

Second review is now finalized: .ai/inputs/study-v2-20261002/stage-b-review-second.md.
Root reproduced both on the stable second source with a new synthetic fixture:
stage-b-second-review-reproduction.json. Cachedresult returned after deleting
lock, while verify_study correctly refused; removing one result from analysis
dropped9400knownphysicalseconds (19351to9951), while retaining that block as
started-without-result. Include analysis entrypoint validation in R1, not just
run_block. No real scientific data was altered; the original fixtures remain.

## Prospective interpretation clarification (no new estimator or workload)

Read research/experiments/2026-10-02-inference-interpretation-amendment.md when
root copies it for this follow-up. Preserve numerical estimators and six-way
allocation; make labels/protocol unambiguous: t-based resolution/cost gates are
working-assumption exploratory statements, not nominal guaranteed practical
benefit. Confidence-level bounded endpoint claims require existing family
Hoeffding bounds with measurement/missing-block bounds. Cost is unbounded and
model-dependent, so no assured joint-six-way or distribution-free economicclaim.
No request to growNuntilbounds pass, addtheory, or change the primarymeasure.
