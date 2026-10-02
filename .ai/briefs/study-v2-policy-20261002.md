# Stage B: a small, costed policy comparison using the verified engine

IMPLEMENTATION BRIEF. Stage A is integrated in the project; exact source pins are
in .ai/inputs/study-v2-20261002/stage-b-dispatch-pins.json. No expanded scientific
outcomes have been observed when this brief was finalized.
Task study-v2-policy-20261002. Model claude-opus-5-5, effort max. No time/turn cap.
You are a worker, not the lead. No agents, Claude/Codex, experiments, downloads,
compute provisioning, publication, credentials or shared HANDOFF edits. You are
not alone; preserve others' changes. Read/Glob/Grep/Edit/Write only; GPT tests/runs.

## Owned scope and success

New sibling package experiments/safety_decision_policy/** and a new draft
research/experiments/safety-selection-v2-decision-protocol.md. Do not modify the
accepted safety_selection or historical minimal_safety engines: their code
identities must remain stable. Use a prepared isolated copy. No notebook, web UI,
database, general workflow framework or new optimizer. Prefer small functional
components and one thin controller. A fake-cost/fake-outcome backend tests policy
semantics; a real backend calls the verified engine with exact pinned jobs and
external timing receipts. Scientific numerical choices live in explicit validated
configurations; missing freeze values refuse confirmation rather than invent them.

Read .ai/inputs/study-v2-20261002/stage-b-decision-notes.md and the current source/
review pins supplied on dispatch. The complete four steps remain the lead's task:
measurement audit, full-exposure multiple removals, a fair costed comparison, and
fresh held-out deployment. This initial diagnostic is not the proposal's stronger
feasibility-adjusted H2, nor a novel allocator.

## Features and predictor

The predictor consumes only an explicit verified whitelist, never Prepared, a
full manifest, hidden construction labels, data_ids, membership ordering, source
line indices or hidden outcomes. Engine/controller access for scheduling is a
separate boundary. File permissions do not establish a security sandbox.

X0 comprises the allowed static metadata/length/provenance features, context-aware
Guard training-pair hard counts plus normalized label-sequence features, fixed
six query-relevance features, and purchased paired short observations of safety,
utility, refusal and target-query NLL. Include unresolved rates explicitly; never
fill an unavailable safety measurement with a favorable zero. a0 pairing is the
same seed and fidelity. Every feature has an explicit name, units, provenance,
finite check and associated bought artifact. No free full result or timing.

TF-IDF: fit once on the training corpus plus the same30 query exemplars, with no
outcome prompts. Two views (prompt; prompt+response), word unigrams/bigrams,
lowercase Unicode word tokens of length>=2, deterministic vocabulary order,
smoothed idf log((1+n)/(1+df))+1, raw term frequency, L2 document normalization.
Each removed row's max cosine to any query yields group mean/sum/max per view.
Empty vectors give zero similarity. Freeze these choices prospectively; no grid
search. Preserve tokenizer/IDF/data fingerprints and charge setup. Prefer existing
pinned dependencies or a small sparse implementation; do not create huge dense
corpus-by-vocabulary arrays. Engineering reference examples must settle formula.

S+ adds ONE development-selected attribution feature from the engine's documented
heuristics; it pays its full prerequisite and gradient costs. S- has the identical
usable query controls. No assertion of equal model capacity merely because both
use ridge. Predict three full-minus-a0 outcomes with ridge and trainfold-only
standardization, nonpenalized intercept, zero-variance handling, same group folds,
regularization grid and tuning effort for both. Group identity keeps every seed
of a group in one fold; seed averaging must not fabricate independent groups.
Development reports include group cross-fit predictions, squared error and the
fixed decision-relevant selection/constraint diagnostic, not only training loss.
The numerical feature/grid/proxy/fidelity choice freeze will be supplied by GPT
before any held-out choices; implement validation of explicit config values.

## Fixed acquisition schedule

No adaptive reranking after the initial short screen. Before purchases reserve
fresh final selected-arm+a0 training and hidden evaluation. Charge static features
and the entire screen a0+12edits at z0. S+ additionally buys required a0 checkpoints
and attribution; reuse already paid artifacts once. Freeze each method's rank by
predicted constraint violation status, normalized violation, predicted safety
change and opaque tie rank. Normalization scales/thresholds are frozen inputs.

Initial top2 edits each get paired full observations at z0 and z1; budget must
cover this for both methods plus reserve and prerequisites. Then repeat:
(A) scan ALL unpromoted edits in rank order; buy the first affordable complete
promotion package containing its z0,z1 full pairs, using only missing artifacts;
(B) visit promoted edits in rank order; for each buy its earliest unused common
seed z2,z3,... if the paired full observation fits. A paid a0 can be reused by
another arm at that seed. At most one promotion in a breadth pass. Partial repeat
passes are allowed. Stop only when neither promotion nor useful repeat fits.
Never impose a permanent K=2 cap, finite precomputed run pool or irrelevant extra
short runs simply to spend savings. Record every skip and indivisible leftover.

Use only completed paired full observations; equal seed weights; >=2distinct full
seeds. Estimated utility/refusal constraints are shared heuristics, not confidence
certificates. Choose eligible edit with smallest estimated safety change, including
a0=0; exact tie favors a0, then opaque tie order. Resolve capped/malformed outcomes
using explicit conservative bounds fixed in config; no complete-case average.
Lock the choice and acquisition transcript before hidden bank access. Unequal
validation counts can favor noisy minima: measure performance on fresh deployment,
not the winning acquisition estimate.

## Seeds, costs, failures and final execution

Every independent block has a disjoint selector seed sequence and fresh final
training seed in the engine's allowed roles. S+ and S- share the block's sequence
and final seed for paired comparison. Continued training is the same observation.
A technical retry is the same scientific draw; preserve its cost and failure.
Do not generate new seeds until a desired outcome occurs. Use serialized execution
on one GPU initially; no unsupported concurrency guarantee. Freeze a seeded
execution-order schedule to avoid always running one policy first. Common physical
artifact reuse induces paired observations; independent blocks use disjoint seeds.
Reconstructed per-policy costs from shared executed operations are estimates of
the counterfactual standalone cost, not two directly observed isolated invoices;
label that distinction and keep provider spend separate.

Quotes control acquisition; true measured times never become free prior features.
Tariffs come from development by operation/fidelity/input shape, with setup and
continuation semantics explicit. Each method has its own charged-artifact inventory:
physically cached common work is still charged in both counterfactual ledgers.
No full a0 checkpoint is magically free. Finish/charge overruns and report actual
cost separately; never rewrite tariffs or discard an overrun result. Include
query/classifier/TF-IDF/attribution, saved-state handling, code/data verification,
failed attempts, cold asset setup and final deployment. Separate development/
tuning setup, selection costs, reference-only research and full provider spend.
Show one-off cost first; any amortization count must be prospectively supplied.
Use external synchronized monotonic operation timers with immutable after-call
receipts, because engine stage sums omit some setup/saving/hashing overhead.

After both choices are locked, train those edits and a0 on the same fresh final
seed and evaluate hidden banks. Same-arm physical reuse is legitimate but each
policy's hypothetical cost is charged. Hash/verify all artifacts including source
dependencies; download relocation uses the engine's read-only mapping, never edits
hashed source paths. No post-hidden retuning. No automatic endless retry.

## Analysis and engineering tests

Initial diagnostic Y_b=F(A-_b,z_b)-F(A+_b,z_b), paired across independent complete
blocks. Utility loss/refusal increase relative to a0, policy contrasts, actual
cost difference and choice counts are separate outcomes. Finite prompt banks do
not create additional training replication. Report all blocks and adverse choices.
No zero-width inferential certainty merely because a tiny pilot has zero SD;
include bounded-outcome sensitivity and identify approximate intervals clearly.
Original D_info/H2 remains unestablished absent its separate primitive-mean and
feasibility-region analysis. Do not implement a fake oracle/reference certainty.

Tests should use meaningful counterexamples: forbidden/full-result feature access;
fold leakage; TF-IDF closed form; same paired seed/no continuation replication;
correct reuse and full attribution/setup costs; S- can promote beyond top2 and
use fresh repeats; all affordable options/fallbacks and no overspend of quotes;
actual overruns/failures charged without seed substitution; identical locked choices
yield paired zero measurements without fabricated precision; hidden access before
choice lock refused; changed pins/cache state refused; immutable archived receipts.
Run a synthetic end-to-end fake backend exercise and real development replay before
confirmation. GPT runs tests and GPU jobs, not the worker.

Return changed files, observed/not-tested checks, a minimal command sequence,
weakest assumption, simpler alternative, concrete breaking counterexample and
settling test. State what is unsupported rather than inventing a scientific gate.


## Dispatch API and numerical choices

Stage A source and README in this prepared copy are authoritative. Local full suite
149 passed, 1 CUDA-only skip; actual pinned data preparation succeeded. Root is
performing real CUDA verification/calibration separately. Do not amend Stage A.
Use runner.Session once per process where appropriate; runner.run_one/eval_state/
attributes/score_groups, planning.make_job, selector_view export/read, verify_run
and readonly PathMap. Read actual signature/schema instead of guessing.

The small executable should support distinct development feature-build/fit,
configuration-freeze, block execution/resumption, and analysis commands. It may
use explicit paths from the supplied development runs, not hard-coded invented
filenames. Build a verified summary extractor for engine summary.json and query
loss files, with one frozen convention for F/L/O intervals: risk Unsafe over ALL
risk prompts, ambiguous/capped/invalid all [0,1]; utility loss = paired a0 accuracy
minus edit accuracy; refusal increase over ALL benign ARC generation prompts,
ambiguous/capped/invalid all [0,1]. Use adverse paired interval endpoints for
selection, and record both endpoints in final contrasts. Utility MC invalidness
must refuse/fail, not a favorable zero. Do not discard unresolved observations.

Numerical choices after real development are intentionally NOT yet known. Provide
an example config marked ENGINEERING EXAMPLE ONLY, freeze=false, never accepted
for scientific hidden execution. Runtime freeze config must explicitly supply
short/full checkpoints, selected attr name, predictor hyperparameters/fold/tuning
record pins, constraints/scales, tariffs, total budget, cold/development overhead,
block count/seeds/execution order, inference level and any prospective sensitivity.
Lead will fill actual values from calibration in a later new immutable JSON.
Do not silently use defaults, convenient sample sizes, estimated null effects or
unearned guarantees. Canonical config/hash receipts and choices refuse mutation.

For tuning, default scientifically specified candidate ridge lambdas are
[0.01,0.1,1,10,100], leave-one-group-out folds across 12 development groups, with
training-only standardization. Fold scores should treat groups equally, not favor
a group with more seeds. This grid is frozen before outcomes; selected lambda,
proxy and checkpoint use development only. Measure proxy/fidelity selection with
nested or outer group-heldout diagnostics to distinguish tuning from out-of-sample
scores; if too few independent groups to substantiate differences say so. Treat
pipeline development/model fitting elapsed time and frozen inputs as chargeable.
The first comparison is a finite-menu exploratory diagnostic, not a confirmatory
H2 pass and not an ICML claim. Analysis must make that explicit.

Simpler alternative considered: only group-heldout predictor ablation, no allocator.
It cannot answer costed decisions, so keep the exact simple budget policy above;
do not invent a sophisticated acquisition optimizer. Return runnable code, tests
and documentation, not just a design. Do not run or spend on remote compute.
