# Minimal implementation plan

Status: specification only, 2026-09-24. No pilot package, estimator benchmark or
training study has been implemented. The bounded numerical checks recorded in
ANALYTIC_CHECKS.json verify scoping equations, not the proposed cost advantage.

## 1. Next task and ownership

The next implementation should be a CPU exactness/headroom harness, delivered in
small steps. GPT owns scientific decisions, source checks, briefs, review,
verification and integration. Claude `claude-opus-5-5` with requested effort `max`
owns substantive code in a launcher-prepared isolated copy. No model substitution.
The first-pass Opus scoping call did not return; REVIEW.md records the limitation.

This plan is not authorization to run all conditional studies now. Do not create
an entire framework up front. Implement task A below, verify it, then B; do not
fit neural couplings or launch a model study before the previous gate warrants it.
No Git initialization or publishing as a side effect.

## 2. Minimal files and contracts

Proposed package `pilot/` (does not yet exist):

| File | Responsibility / interface |
| --- | --- |
| `process.py` | Immutable config and complete state; `probs(state)`, `successors(state, weight=1)`, `apply_event(state, action, weight)`, `score(state)`; no RNG inside deterministic maps |
| `couplings.py` | `joint(p,q,successors,context)->JointPlan`; independent, CDF overlap, shared-Gumbel analytic masses, maximal, distance-LP, projected rule; validate nonnegativity/marginals |
| `exact.py` | `terminal_law(start,H)` and `pair_moments(x,y,H,policy)`; history-keyed/depth-first traversal; `oracle(x,y,H)` returns value, optimizer plans, residuals and construction ledger |
| `run.py` | Fixed-seed manifest runner; independent calibration/evaluation streams; biased replay/truncation; strict stage/cell resource caps; output atomic records |
| `costs.py` | Explicit operation counters and timing/storage ledger; separate setup, reference calculation, per-request and online costs |
| `learned.py` | Only after headroom: development-state generation, pair-cost fitting, frozen predictor, exact coupling interface; no test reference access |
| `configs/core.json` | Literal grid, splits, target, RNG IDs, caps and gate version; hash before execution |
| `tests/` | Small mathematical fixtures and cross-implementation checks, not tests that merely duplicate code |

JointPlan contains joint matrix, method/algorithm version, marginal residuals,
any solve/rounding gap, candidate-update count and construction cost. Complete
state contains theta, momentum, absolute counter and config identity. No replay
buffer exists in the specified toy; adding one changes the state contract.

A random source exposes independent per-round uniforms or exponentials, with
explicit sharing inside a coupling. Do not rely on two mutable RNGs consuming
the same number of calls by accident. Store seed lineage by factual run, prefix,
calibration batch, evaluation batch and continuation. Stop-after-time logic must
not retain only short trajectories.

## 3. Dependencies and reproducibility

CPU implementation needs Python, NumPy, an LP solver with residual/duality output
(provisionally SciPy/HiGHS), and mpmath for small high-precision fixtures. The
current lead environment exposes Python 3.9, NumPy and mpmath; SciPy was not
available at inspection. No dependencies were installed in this scoping pass.
Use a local isolated environment and pin versions/BLAS/thread counts when code is
implemented. Do not silently depend on a user's global packages. A small learned
network may use PyTorch later; ridge-only comparison is insufficient if the
prespecified strong learned comparator remains incomplete.

Expected reference precision is float64, checked on a small set with 50-digit
arithmetic. Stable softmax and analytic Gumbel masses must handle beta=8 without
underflow assumptions. If more extreme logits need special arithmetic, report
this and its cost. Rounding/merging states to reduce the oracle tree changes the
reference and must not happen without an explicit approximation specification.

## 4. Bounded tasks and acceptance

| Task | Opus-owned files | Observable completion / GPT verification |
| --- | --- | --- |
| A: process + marginal truth | `pilot/process.py`, `pilot/exact.py` marginal portion, `pilot/tests/test_process.py`, `pilot/tests/test_marginal.py` | H=0 and H=1 hand formulas; alpha=0 identical worlds; weight-zero versus skipped-step momentum fixture; exact H=2 enumeration with high precision; manifest indexing and state restoration |
| B: paired coupling/oracle | `pilot/couplings.py`, pair/oracle portions of `pilot/exact.py`, `pilot/tests/test_couplings.py`, `pilot/tests/test_oracle.py` | Local row/column laws; joint Gumbel formula vs independent quadrature and sampled counts; pair means vs independent marginal truth; scalar all-horizon equality; H=1 terminal-OT; oracle no worse than feasible couplings; LP gaps; h-1 Jacobian fixture |
| C: falsification runner | `pilot/run.py`, `pilot/costs.py`, `pilot/configs/core.json`, `pilot/tests/test_accounting.py` | Complete schema; all tail and candidate work charged; zero/biased cases; cell caps recorded; grid/timing-panel counts; conservative precision decisions; no performance study before GPT acceptance of A/B |
| D: conditional learned comparison | `pilot/learned.py`, `pilot/tests/test_splits.py`, dev-only config | No descendant leakage; include exact label-generation cost; comparable inputs; same fast path for an identical projected coupling; full matched-precision protocol under cap |

One implementer at a time; each brief narrows the broad module ownership above.
Workers are not alone, preserve other edits, do not recurse, and never edit shared
handoff or scoping records. A non-author GPT reviewer examines substantive code
and fixtures; GPT asks concrete unresolved questions and verifies fixes.

Use `.ai/claude_handoff.py --prepare-workspace <task-name>` before code work, then
invoke it with the task-specific brief, `--mode implement`, explicit workspace,
turn/time caps and only necessary shell permissions. Suggested budgets: A/B each
12 turns/900 seconds; C/D each 16 turns/1200 seconds, one call at a time. These
are development-assistant caps, not experimental compute guarantees. If the exact
model does not return or routing metadata is missing, preserve the report and
surface the gap rather than silently retrying or routing to a substitute.

Before integration compare each destination hash with the prepared manifest.
New owned files must still be absent; changed existing files must still match.
Resolve concurrent edits explicitly. Copy only reviewed files. GPT runs affected
checks and updates `.ai/HANDOFF.md`. No claim of effective internal effort unless
the runtime actually reports it.

## 5. Output schemas

Use JSON/JSONL for manifests and receipts, CSV or Parquet for tidy measurements.
One target record: `schema_version, config_hash, family, split, seed_block,
prefix_id, t, H, state_hash, action_t, alpha, g_id, theta/optimizer config,
reference_mean_suppressed, reference_mean_ordinary, delta, numeric_tolerance`.

One method/batch record: target key plus `method_version, coupling_class,
fit_run_id, calibration_seed, evaluation_seed, N_calibration, N_evaluation,
mean, exact_bias, exact_variance, second_moment, mse, ci_method, ci_low, ci_high,
coverage, achieved_precision, stage_status, reason_if_incomplete`.

One cost record: `setup_seconds, reference_seconds, fit_label_seconds, fit_seconds,
calibration_seconds, online_seconds, probability_vectors, random_variates,
gradient_evaluations, jacobian_products, optimizer_updates, generated_observations,
terminal_evaluations, transport_solves, coupling_samples, bytes_written,
checkpoint_bytes, peak_rss_bytes, hardware, threads, dependency_lock_hash`.
Store counts for hypothetical generation/update ratios separately from measurements.

One gate record: `gate_version, complete_cells, censored_cells, numeric_failures,
eligible_cells, zero_variance_cells, cost_ratios, uncertainty_method,
proceed_revise_stop, supporting_record_ids, unresolved_overlaps`.

## 6. CPU-first and conditional GPU budgets

**CPU-first:** H=4,K=3 has at most 820 oracle LP nodes per target and 590,400
such solves across that grid slice. At an assumed 1–20 ms per solve this alone
takes roughly 10 minutes–3.3 hours; tree overhead, other horizons and exact
method-moment enumeration add cost. These are planning calculations, not timing
measurements. Preflight the actual first cells. Stage 1 cap is 8 CPU-hours/8 GiB;
stage 2 cap is 24 CPU-hours/8 GiB, including a maximum 4 fitting hours and exact
development labels. Declare incomplete if capped. No GPU is needed. Estimated
disk allowance: 2 GiB for manifests, numeric tables and selected trees, excluding
paper downloads; no automatic retention of every sampled trajectory.

**One-GPU scenario, only if pilot and novelty gates pass:** first use a small
categorical neural learner (roughly 1–10M parameters, finite K<=8); assume one
24 GiB GPU for planning, verify memory/access before scheduling. Budget a 30-minute
throughput/memory calibration and at most 8 GPU-hours for an initial feasibility
check, with full paired continuations and exact batch denominator/optimizer rules.
This checks whether all-action gradients destroy the toy advantage; it is not an
LLM guarantee. CPU-only continuation is possible at reduced model size.

A later language-model pilot needs a separate specification of model, tokenizer,
data licenses/splits, optimizer, finite candidate-generation mechanism, behavior
score and reference uncertainty. Do not transfer assistant model choices into it.
For scale intuition only, 8 independent training-seed blocks x 2 prefixes x 8
counterfactual continuation pairs x 2 worlds =256 continuation runs. At an assumed
0.25 GPU-hour each, that is 64 GPU-hours **before** prefix training, evaluation,
coupling fit and storage. This formula exposes that one GPU does not mean a small
study. No such cost or study is authorized or measured here; if budget cannot
support reference replication, narrow the experiment rather than treating noisy
retraining as truth.
