# Stage A: verified-source corrections and bounded review fixes

Task study-v2-engine-fixes-20261002. Implementation and response to GPT questions.
Exact model claude-opus-5-5; effort max; NO time or turn cap. Same prepared workspace
and ownership: experiments/safety_selection/** and its draft protocol only. You
are a worker, not the lead. No agents/Claude/Codex, shell, experiments, downloads,
cloud resources, credentials, publication, or HANDOFF edits. Read/Glob/Grep/Edit/
Write only. You are not alone; preserve other edits. GPT executes tests and
integrates. This brief will be dispatched only after your first implementation
returns. Read the first report and the copied review/source receipts supplied by
the lead; no claim of test success based on either model's agreement.

User removed the financial cap for the four-step study. Still no expanded GPU
run or held-out outcome exists. Do not reintroduce the old pilot limits. Stage B
will be a sibling package with its own code identity, keeping this engine stable.

## Actual source correction, before any outcomes

The earlier metadata inspection omitted WITHIN-bank prompt duplicates. Actual
strict preparation gives295 risky and4597 non-toxic ToxicChat rows, after60 DATE
prompt exclusions and7/124 within-bank duplicate prompts. Change the expected
counts and prospective safety bank sizes to72dev/80selector/143hidden. Preserve
the original source SHA/revisions and explicitly document the correction; do not
silently shrink at runtime. ARC has570 eligible validation and2371 eligible test
questions after5 test duplicates. DATE remains10,148 train/30query rows. All
24groups fit and the prior8removed rows remain development-only. Lead real-source
preparation passed after this explicit amendment. Its temporary seed/name are
engineering check choices; keep one intentional preset design seed and record it,
not a silent response to outcomes (none exist). Update presets/docs/tests.

Root also checked all raw DATE train/ref data_ids: zero duplicates. Both rendered
ARC prompt forms versus all original DATE prompts: zero current collisions.
Receipts are copied under .ai/inputs/study-v2-20261002/public-metadata/.

## Concrete corrections required before acceptance

1. **Finite inference and gradients.** Engine greedy decoding applies argmax to
   unchecked logits. Root's CPU fixture with all-NaN logits returns token0/EOS,
   disguising numerical failure as a completed answer. Check all active rows'
   logits before prefill/decode argmax; NaN or infinity must raise. Root also
   reproduced infinite CE with finite nonzero gradient: logits[-Inf,theta],
   target0 give infinite loss but gradient1. Reject nonfinite losses before
   example_gradient autograd, and nonfinite teacher-forced scores before ranking.
   Preserve failed attempts; do not turn them into safe/empty/capped observations.
   Add actual numeric regressions, not string assertions.
2. **Calibration reuse must bind the requested science.** _attempt accepts any
   hash-valid folder whose name matches seed/arm/checkpoint. A call using the same
   output root with a new generation ceiling, data manifest or recipe can return
   old outcomes as successful reused units. Check the complete stored job/identity
   against current manifest, recipe, code, split/role/arm/seed/checkpoint/eval bank
   before reuse; fail on mismatch. Test wrong identities and valid reuse. Do not
   rewrite old folders to match a new config.
3. **Attribution source identity and receipts.** _a0_source returns source code
   without enforcing the common training implementation. Checkpoint q from codeA
   and e1/e3 from codeB can be combined under an unchanged recipe/seed/init. Enforce
   current/common source code as promised; retain source completion/state hashes,
   source path/code, adapter/optimizer fingerprints and optimizer step for every
   checkpoint in persisted output. Existing info collected then discarded does
   not establish provenance. Test a cross-code checkpoint rejection before model
   work and inspect source-state checks (checkpoint/stream/Adam step).
4. **Portable dependency verification.** Downloaded jobs keep absolute remote
   resume/source paths. Add a read-only path-prefix map or archive-root resolver
   to verification; never mutate the hashed job. Verify dependencies for run-one
   resumes, eval-state source_run and attributes a0_states, with pinned source
   receipts, not only each folder's own hashes. Distinguish own-files verification
   from complete dependency-chain verification. Test an archived remote tree and
   a missing/changed source. Relative paths alone require the original CWD layout
   and do not repair existing absolute paths.
5. **Rendered prompt overlap.** Eligibility/disjointness checks currently compare
   bare ARC questions while model input uses rendered question/choices/instruction.
   Check bare question AND both renderings against original source prompts and
   actual emitted prompts across banks. Add the reviewer's collision fixture.
   This is preventive: no collision exists in current pinned sources.
6. **Selector view.** The full engine manifest carries construction seed and group
   compositions; replaying construction recovers hidden labels. Engine/auditor
   access is fine, but a selector must receive only a verified whitelist. Provide
   an explicit selector-input reader/export (metadata and measured classifier
   features only), with unknown keys refused and no Prepared/full manifest passed
   to prediction. Explain/test the boundary, including hidden-label renaming.
   This is an experimental information boundary, not filesystem security. Stage B
   will enforce its feature matrix separately.
7. **Seed allocation.** Replace set(range(first,last+1)) with interval membership
   over excluded seeds. Allocating one seed in a billion-wide valid namespace
   must not allocate billions of integers. Preserve determinism and distinctness.

## Strong content baseline feature support

Add continuous guard class scores for score-groups, rather than rely only on hard
class labels. Under the EXACT official template for the full prompt/response,
teacher-force the three complete canonical strings "Safety: Safe\n",
"Safety: Unsafe\n", "Safety: Controversial\n". Verify joint tokenization boundaries,
sum log probabilities over all label-string target tokens (no artificial EOS),
and normalize the three sequence likelihoods with log-sum-exp. Call them
normalized label-sequence scores, not calibrated probabilities. Preserve all
three scores, validity and per-group summaries; no benchmark label or source ID
enters features. Explicitly charge these passes. Ordinary response evaluation
need not buy these optional feature passes. Numeric failure is fatal, not a
missing/zero confidence. Control-string/length failures keep their explicit
unresolved semantics. Test prefix boundaries, normalization and nonfinite inputs.

## Costs and remaining contracts

One additional information-control requirement from a bounded non-author design
review, accepted by the lead before outcomes: S- must be able to use the same30
query exemplars as S+. Stage B will add six frozen lexical TF-IDF relevance
features to BOTH inputs (outside this engine). In this engine add a forward-only
query-loss measurement at each evaluated checkpoint: per-row and mean response
NLL over the SAME30 ref queries, with the exact training normalization/EOS
convention, no truncation/gradients. Save query/row identities, target-token counts,
per-row losses and aggregate; explicitly time/charge the forward passes and
verify no RNG/weight/optimizer perturbation. This allows both methods to use
edit-minus-paired-a0 SHORT-checkpoint query loss as an X0 feature. It is a target
likelihood proxy, not measured safety. Include it in ordinary development and
selector evaluation outputs and the matching eval-state interface. It needs no
hidden prompt bank. Do not implement the TF-IDF selector or new acquisition logic
here. Tests must establish the objective equals direct response-only NLL and
nonfinite values fail. Query forward work already purchased or legitimately
shared with gradients is charged once per policy, not made free or double-counted.

Stage ledger sums/trajectory_cost are not total purchased-operation cost: setup,
data verification, checkpoint saving and final hashing may lie outside stages.
Document that distinction and retain source receipts. Stage B will time each
operation outside the engine call and write immutable external receipts after
completion, plus separately charge session setup and failed attempts. Do not
label stage sums as complete policy cost. The cloud supervisor will record whole
process/billable time separately. If a minimal engine hook is necessary for this,
state it explicitly; do not build a new allocator or cloud controller.

Same-seed technical retries remain the same scientific draw and incur every
attempt's cost. The registry is serialized by the lead's one-GPU scheduler; do
not claim concurrency safety it does not implement. Require explicit code pins
for frozen confirmation while permitting explicit development convenience.

Batch-versus-singleton bf16 outputs need not be bitwise equal. Verify masks and
positions against tolerant logits and inspect any first greedy divergence; freeze
the batching policy. Exact resume comparisons require identical batch shapes and
numerical settings. The reused minimal_safety configure_cuda freezes TF32 and
float32 settings but does not record/control bf16 reduced-precision accumulation.
In the NEW loader, explicitly set/read back
torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False and record
that value in environment/identity; do not edit the historical engine. Explain
the limited numerical guarantee and test the new flag on the real CUDA preflight.
Keep the Adam feature a heuristic: fixed-epoch removal is
not the fixed-step renormalized mean-objective intervention; do not insert a
centered correction as a supposed general fix. It omits changing batches, Adam
state, clipping and future trajectories; unequal checkpoint sums are not an
integral or finite-removal theorem.

## Success and concrete questions

Deliver bounded fixes/tests/docs, list every changed file, and answer:
1. Which of these counterexamples falsifies an existing guarantee, versus a
   concern already prevented by a higher-level contract? Point to that contract.
2. What is the weakest remaining assumption for interpreting a safety change?
3. What simpler implementation preserves the actual experimental guarantee?
4. Which test or measured calibration would change your recommendation?
5. What remains untested without real CUDA and the public assets?

GPT runs affected tests, real-source preparation and the CUDA checks. Acceptance
requires the concrete invariant tests and source audit, not author confidence.
No fabricated pass counts or model/effort attestation.

## First implementation has now returned; lead checks and decisions

Read .ai/inputs/study-v2-20261002/opus-engine-first-report.md. The first stable
full CPU suite passed110tests in5.46s (receipt engine-first-tests.json). This
establishes only those tested engineering cases; the concrete counterexamples
above remain. Pycache and prior input/report files were deliberately made/copied
by GPT; do not count them as your edits or remove others' evidence. No GPU work.

Your report correctly identifies small removal-dose headroom as uncertain. Keep
that as a calibration question, not a new dose-response acceptance gate. The
coarse UltraChat/ToxicChat construction mapping is supported by DATE-LM Appendix
D.2/Table9 (new date-provenance-check.json); it is not a fresh rowwise source audit.
Our actual public ref.jsonl contains30 response texts, not single class labels.
Do not claim this objective reproduces DATE-LM's reported label-target baseline.
Equal checkpoint weighting remains an explicitly heuristic sum, not integration.
Strict contradictory Guard outputs remain unresolved, never forced Safe.

The preset development namespace1101–1104 is an accidental four-seed execution
restriction, not a justified scientific sample-size cap. Widen it to1101–2099,
keeping the selector/reference namespaces disjoint. Final selected n remains a
prospective lead decision from development precision/workload; do not claim all
namespace seeds must run. Update tests/docs to distinguish allowed seed ranges
from actual planned/calibrated seeds. Do not impose a new scientific cap.

Real CUDA checks will be run by GPT after these fixes. Ensure documentation lists
pinned dependencies needed in a clean Linux torch2.8/CUDA12.8 environment; no
installer or dependency changes outside your owned package. No execute permission
is added by this note.
