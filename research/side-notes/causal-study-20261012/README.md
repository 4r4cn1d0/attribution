# Component intervention pilot — 12 October 2026

This prospective follow-up asks which component of the Scheduled recipe changes
the unsafe-answer share at the pinned OLMo1B and OLMo7B checkpoints. The original
Scheduled recipe changed both response weighting and learning-rate timing.

The remaining balance funds **one fresh seed block,1121, with six units**:

- A: each training response has equal weight; constant learning rate1e-4.
- C: equal response weights; four-step warmup/cosine, peak learning rate1e-4.
- D: each response token has equal weight; the same warmup/cosine schedule.

All comparisons stop at one epoch/38 optimizer updates. C−A isolates the schedule
package under equal response weights. D−C isolates weighting under that schedule.
D−A is exactly their sum. The direct differences between these components at1B
and7B can diagnose why the combined recipe behaves differently in this block.
Lower unsafe-answer share is favorable. Practical point differences of5percentage
points are reported descriptively; they do not establish equivalence or population
significance. Warmup versus cosine and average rate versus timing remain bundled.

## What the funded block can establish

Each arm starts from the same seeded adapter within a checkpoint, with a new
optimizer and process. The actual training row order, applied learning rates and
measured objective reduction are checked against the frozen intervention. Model,
tokenizer, prepared manifest, generation, judge and numeric engine remain fixed.
The600 sampled safety answers and original benign over-refusal/ARC measures are
retained. The query NLL uses the same example-mean evaluation reduction for all
arms and is conservatively a task-learning indicator, not a proved held-out
utility measure. Indiscriminate refusal can cause a safety-share reduction; it
does not establish useful selective safety.

There is only one independent training seed. Results are conditional on these
checkpoints, this seed and the known development bank. No population confidence
interval, p-value, parameter-count law, or refusal-direction mediation claim is
licensed. Historical outcomes are not pooled. Independent fresh-seed confirmation
is required before generalizing an apparent explanation of the earlier pattern.

## Frozen resource and failure rules

Two pods may run in parallel:1B capped at4hours and7B at6.5hours, each at no more
than$1.85/hour. Their total maximum GPU commitment is$19.425. The shared account
guard retains$12 for$1.85646 of unfinished-probe recovery, up to$4 of later judge
work, approximately$4.50 of storage over the operating window and a buffer.
Latest pre-build account read: about$35.01, with no running GPU. Storage continues
to reduce this balance. Every actual launch passes a fresh account admission.

Caps include setup, engineering preflight, training, evaluation and retrieval.
These are fixed budget caps, not guaranteed completion times. Before each arm,
admission requires3600seconds at1B or6600seconds at7B plus300seconds, based on
historical upper scenarios. Per-unit ledger caps are4200/7200seconds. The operator
does not apply the old single-family worst-case all-capped-generation projection
rule to this newly registered batch. Original kits and their scientific rules
are untouched.

Arm order is randomized once before outcomes:1B D,A,C;7B C,D,A (random seed20261012).
No arm selection, paid automatic relaunch, outcome-dependent continuation or
extra seed is allowed in this pilot. Failures and unstarted units remain visible;
an incomplete block prevents the registered component comparison. Outputs and
states are fetched before each confirmed stop, subject to the hard cap. Failed
retrieval leaves the remote data on the stopped volume; no volume is deleted.

Main attribution Gate B stays paused. This pilot does not change paper results or
original registrations. The user authorized GPT implementation for this study
after Opus5.5/max was unavailable until15October, and authorized use of the remaining
balance with probe-recovery funding separate. Protocol and implementation hashes,
non-author review and launch receipts are recorded before any new outcomes.
