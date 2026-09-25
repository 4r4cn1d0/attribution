# Smallest decisive pilot

Status: prespecified study design, not an executed experiment. Date: 2026-09-24.
Definitions and algorithms are in THEORY.md. Freeze a machine-readable manifest
and its hash before measurements; any change creates a new version and explains
which results were already visible. Run stages in order and stop at failed gates.

## 1. Purpose and primary estimand

Estimate the fixed-prefix, single-occurrence gradient-suppression Delta in SCOPE.md,
with future data regenerated in each world. All scores use suppressed minus
ordinary. Primary endpoint is complete cost at RMSE <=0.01 on a [0,1] score;
0.02 and 0.005 are secondary precision targets. Exact terminal-law enumeration
supplies reference expectations for the tiny systems. It is an exhaustive
finite sum evaluated numerically, not exact symbolic real arithmetic.

First reject indexing/marginal bugs. Then ask whether a practical method beats
the strongest baseline at matched error. An oracle's variance gain is only
headroom. Scalar family A is an all-horizon **equivalence control**, not a place
to claim the projected method is novel. Family B is the first genuine separation
test. Entropy regularizes selection, as defined in THEORY.md; this is a toy
adaptive learner, not a small PPO implementation.

## 2. Fixed configurations and staged resource limits

K=3 actions; offsets b=0; mu=lambda=0; constant eta. Main g= sigmoid(theta) for
A and sigmoid(e1^T theta) for B. Conditional prefixes in the core use t=1:
initialize the stated theta, observe each action a_t in {1,2,3}, and compare
w_t=1 with w_t=1-alpha. alpha=1 is primary full suppression; alpha=0.25 is a
separate finite downweighting diagnostic, never pooled as the same estimand.
Every observed action has positive probability. Report per-prefix results and
weight them by the original p_(theta0)(a_t) for a prespecified slot-level summary.

| Factor | Confirmatory values |
| --- | --- |
| A1 aligned | phi=(-1,0,1), v=(-1,0,1) |
| A2 misordered | phi=(-1,0,1), v=(0,1,-1) |
| A3 opposed | phi=(-1,0,1), v=(1,0,-1) |
| B1 rotated features | phi=((1,0),(0,1),(1,1)/sqrt(2)), r=(1,-1,0.5) |
| B2 nearly collinear | phi=((1,0),(1,0.2)/sqrt(1.04),(1,-0.2)/sqrt(1.04)), r=(-1,0,1) |
| Feedback beta | 0, 1, 3, 8 |
| Learning rate eta | 0.1, 0.4 |
| Future horizon H | 1, 2, 4 |
| Initial theta | -0.4, 0, 0.4 for A; (-0.4,0),(0,0),(0.4,0) for B |
| Intervention | every a_t; alpha=1 primary, 0.25 secondary |

The full grid has 2,160 conditional targets, 1,080 at full suppression. Display
all cells, including degenerate and zero-effect cases. Family A1's mean map at
zero has derivative 1-eta+(2/3)eta beta: beta=1 is locally stable and beta=3,8
locally self-reinforcing. Label other cells by computed local Jacobian spectra
and trajectories; beta alone is not a universal stability label.

**Stage 0, no estimator fitting:** 12 deterministic unit/analytic checks plus
all H=1 cells; then H=2. Count runtime and pair-tree memory before extending to
H=4. At H=4 and K=3 a worst-case pair tree has 6,561 leaves and 820 internal
nodes; there are 720 such target cells, hence <=590,400 internal oracle solves
before reuse. Use depth-first recursion without merging rounded states.

**Stage 1, exact headroom:** finish H=4 only within a cumulative 8 CPU-hour and
8 GiB RSS planning cap. Cap each cell at 60 seconds initially. A cap hit is an
explicit censored/unavailable cell, not a zero or a dropped failure. If headroom
already fails at H<=2, stop there and record the narrower conclusion. H=6,8
are conditional scaling extensions for marginal enumeration and simulation only;
no H=8 paired oracle is budgeted.

**Stage 2, practical fitting/timing:** only after headroom warrants it, fit the
learned comparator and evaluate repeated estimators. Preselect a 72-target timing
panel: structures A1,B1,B2 x beta {1,8} x eta {0.1,0.4} x H {2,4} x all three
observed actions, theta0=0, alpha=1. These cells may not be replaced after seeing
performance. Report exact variance/error metrics across the full completed grid;
the timing panel tests operational frontier and uncertainty. Stage 2 has a total
24 CPU-hour / 8 GiB cap including development-label enumeration, fitting,
calibration and simulation (fitting itself remains capped at 4 hours). Process all
panel cells round-robin in a frozen order so a cap produces an incomplete balanced
comparison, not selectively missing losing cells. No practical proceed verdict
is permitted if required cells or mandatory comparators are incomplete.

## 3. Reference computations and oracle

Enumerate each world's K^H action histories with products of its own conditional
probabilities. Compute masses, g values, means and second moments; use compensated
sums. For selected H<=2 fixtures verify with 50-digit arithmetic and independent
hand formulas. Never round states to make trees merge. Exact symbolic equality or
history keys may be used for caching, with cache construction charged separately.

Enumerate paired trees for each explicit coupling to compute E[Y], E[Y^2], and
Var(Y), and solve the co-adapted Bellman transport recursion of THEORY.md. Report
LP primal marginal residuals and duality gap, plus the unrestricted terminal-OT
lower bound separately. Show oracle construction time/storage independently of
online sampling cost. It cannot peek at future random draws. The finite expected
score and pair second moment are the objective; state meeting time is not.

Shared-Gumbel joint action probabilities must be computed by the analytic
piecewise integral in THEORY.md, then cross-checked against sampled joint counts;
two marginal softmax vectors alone do not specify them. For the surrogate-theory
diagnostic, solve min_(row r,column c) max_ab |Q*_ab-C_ab-r_a-c_b| on the tiny
oracle trees. Compare twice the sum of uniform reachable-pair residual bounds
against actual oracle regret. Record diagnostic LP cost separately. A loose bound
is evidence against that proof route, not a measured estimator improvement.

## 4. Baselines, information and adaptation rules

| Method | Fully specified comparison |
| --- | --- |
| Independent full continuations | pi_ab=p_x(a)p_y(b), all H optimizer updates and terminal evaluation in each world |
| Fixed-label common uniforms | Inverse categorical CDF using identical fresh U each round and action order 1,2,3 |
| Shared Gumbel | Identical independent per-action Gumbels across worlds at each round; use each world's logits |
| Ordered common uniforms | A: sort by v. B: sort by the main terminal coordinate of the current successor; also report 6 fixed action permutations, selected only on development cost/error |
| Maximal action agreement | Diagonal min(p_x,p_y); residual product divided by total residual mass; identical states use diagonal; zero residual handled explicitly |
| Full-update distance | Exact small transportation LP with cost ||U_a(x)-U_b(y)||^2; diagnostic generic OT baseline |
| Proposed projected rule | Mean-dynamics terminal direction and sorted overlap from THEORY §4, with h-1 continuation Jacobians; zero direction/ties deterministic |
| Terminal averaging | Replace last one or two sampled rounds by exact single-world conditional means in both worlds, pairing earlier rounds with the development-selected common-randomness method; include all branch updates |
| Strong learned coupling | Fit a pair-state continuation-cost predictor on development configurations; at each step minimize its KxK predicted terminal cost using an exact marginal-constrained LP. Include the proposed score cost as an available feature/candidate so “learned” is not artificially weaker |
| Co-adapted oracle | Bellman minimum terminal square difference, with full construction cost reported |

The learned comparator is a design of a strong baseline, not a claimed replication
of Lorberbom's released code. Use input (x,y,p_x,p_y,eta,beta,h,action successors,q)
and features including their differences, products, gradients and the projected
cost. If it selects the unfitted projected cost itself, execute the same sorted
fast path and record a tie; do not manufacture a gain by forcing that baseline
through an LP. Targets are exact Bellman continuation costs **on development states only**.
Fit ridge quadratic regression and a two-hidden-layer width-32 tanh network;
choose by development validation cost–MSE. Budget at most 4 CPU-hours total fitting
and 10 initialization seeds, with actual work charged, including all exact
development-label generation and validation inside the overall stage-2 cap.
At least compare prediction
with the unfitted projected feature and report fit residuals. Freeze before test.
If fitting fails, report that mandatory baseline incomplete and withhold a proceed
decision. A later native Gadget-2 replication is desirable before a paper claim;
do not pretend uncorrected Sinkhorn has exact marginals.

## 5. Biased alternatives and finite versus local effects

**Fixed log:** draw an ordinary future log conditional on h_t and replay it through
both learners, recomputing gradients at each altered state. Average over logs for
this conditional experiment. A single realized fixed-log effect is a different
conditional object; display its distribution, not its value as Delta's truth.

**Truncation:** define an autonomous ordinary reference path y for all H rounds.
The hybrid x regenerates its own observations for L rounds, coupled to y using
fixed-label common uniforms. Afterwards feed y's observations to x, while x still
executes all remaining updates. Use L in {0,1,2,H}, deduplicated and clipped to H.
This defines one explicit joint-policy-dependent biased approximation. At L=0 it
is fixed-log replay; at L=H the x marginal is fully regenerated. It is not silently
identified with the cited paper's different hybrid-law definition. Enumerate the
hybrid paired tree and measure its actual bias.

For adjacent L, couple four worlds by one fresh common uniform per round with
each autonomous action generated from its own law; copy only the stipulated
reference-tail observations. Define D_L=Y_L-Y_prev. Report E[D_L], Var(D_L),
E[D_L^2] and all four-world/tail costs on H<=2 first, H=4 only within the cap.
No multilevel speedup claim is required; this checks whether a hierarchy is worth
considering. Record the base level. No inference from mean bias to second moment.

**Local derivative:** exact or independently checked differentiation of the same
fully regenerated finite sum at w_t=1, multiplied by -alpha. Measure its finite
effect error. Fixed-log derivatives are a separately labeled proxy. RFT-Inf/CROPI
native scores are estimand-mismatched; follow PRIOR_ART.md's proxy rules rather
than mislabeling their native cosine/gradient scores as unbiased Delta estimates.

## 6. Replication, leakage and uncertainty

Develop on separate beta {0.5,2,6}, eta {0.15,0.3}, initial coordinates {-0.25,0.25}
and H {1,2,3}, with the same declared structural families. Split complete initial
configurations and all their descendant states together, 70/30 fit/validation by
fixed seed 20260924. Descendants from a held-out test prefix must never enter fit,
normalization, early stopping or hyperparameter selection. Deduplicate exact state
keys across splits where feasible and report collisions. Prespecified g and q are
inputs to the algorithm, not permission to tune using test oracle labels.

For each timing-panel target use 30 independent diagnostic estimator batches at
N in {1,16,64}; fresh continuation randomness within and across batches. Use the
same batch seed labels across methods for paired error comparison, with method
namespaced RNG streams and explicitly shared uniforms inside each paired run.
Estimate MSE about enumerated Delta, variance, signed bias and 95% intervals over
the independent batches; also report the exact V/N prediction where available.
The MSE batch bootstrap resamples whole batches, not individual correlated worlds.
Report pointwise coverage of nominal 95% confidence intervals: bounded Hoeffding
intervals for Y in [-1,1] as a guaranteed but conservative reference, and studentized
intervals as a diagnostic. Do not use a normal interval at N=16 as a validity proof.

**Matched-precision protocol:** additionally run 30 independent end-to-end batches
per target/method. A prespecified structural-determinism exception applies first:
if terminal averaging covers all H remaining rounds, or identical worlds are
kept identical by diagonal coupling, the estimator is analytically deterministic.
Execute it once with no variance-calibration draws, charge all branching and
evaluation work, and include its actual cost in the practical baseline frontier.
This exception cannot be triggered by inspecting test oracle variances. In
particular the depth-2 averaging baseline at H=2 needs one full enumeration,
not 257 repetitions. Timing repeats may measure clock noise but are not necessary
estimator work and must not be charged as repeated scientific estimation.

For methods without such a structural certificate, each batch uses 256 fresh paired calibration samples,
sets N=max(1,ceil(1.25 sample_variance / 0.01^2)), capped at 4096, then discards
those calibration samples and estimates Delta using N new pairs. The 1.25 factor
is a prespecified allocation margin, not a confidence bound. Charge calibration
to every batch's complete cost. Exact V/N (and any known bias) conditional on the
chosen N determines achieved MSE; aggregate across the independent calibration
batches. If the target is missed, mark it unreached rather than increasing N
after seeing test error. Secondary precision targets use analytic frontiers only
unless the total cap allows their prespecified direct confirmation.

Show a separate **oracle-allocation** frontier using max(1,ceil(V/0.01^2)) and
exact bias adjustment, with explicit label that variance was supplied by reference
enumeration. It does not support the practical proceed criterion. This avoids
claiming a gain caused by a coarse N grid or ignoring cheap N=1 competitors.

An additional dependence check uses 20 independent factual training runs, collecting
prefixes at t=2 and t=4, with full state restored. Summaries across these interventions
use run-level cluster bootstrap, never treating two prefixes from one run as two
independent training replications. Keep conditional Monte Carlo error distinct from
variation across training runs/configurations. Main grid summaries are descriptive
finite-grid summaries, not an inference to an unspecified population of tasks.

## 7. Metrics and full cost frontier

For every target/method report exact reference means, Delta, expectation, bias,
variance, second moment, analytic MSE b^2+V/N, repeated-estimator MSE, and target
precision reached/not reached. Also report sign error for |Delta|>=0.01, effect
size, and zero-effect cells separately. Avoid unstable relative error near zero.

Cost ledger includes: prefix/checkpoint creation and restore; every probability
vector and random draw; every candidate gradient/Jacobian/mean-rollout step;
actual optimizer updates in both worlds; transport construction/solve/sampling;
generation or environment reward work; terminal evaluations; fitting and
validation; compiled/warmup time; caching, storage bytes and peak RSS. Show
unamortized single-request totals and amortization at 10 and 100 prespecified
requests. Do not choose request count after seeing break-even. Share factual
prefix costs consistently but display both included and common-cost-excluded totals.

Show measured CPU seconds and operation counts separately. Synthetic ratios of
generation:update cost {0.1,1,10} are sensitivity calculations, not hardware
measurements. No artificial sleep-based “speedup.” Compare each method to the
per-cell strongest baseline frontier as well as the development-selected baseline.
For stochastic work use independent calibration costs; wall-clock stopping must
not silently censor expensive trajectories and bias the estimator.

## 8. Prespecified decisions

For all ratio summaries, a nondegenerate cell has best ordinary paired-estimator
variance >1e-14 and a positive, achieved baseline cost at the requested precision.
Delta=0 is **not** a reason to exclude a cell. Zero-variance baseline cells are
reported separately, with ties and actual minimum costs; unmet-precision or
censored cells prevent a full-panel proceed verdict. The primary ratio in a cell
is (minimum achieved full baseline cost)/(proposed achieved full cost), and the
summary is the unweighted median across the fixed B panel's eligible cells.

1. **Correctness gate:** masses within 1e-12, local marginal residual <=1e-12,
   nonnegative masses to 1e-14, selected high-precision expectation differences
   <=1e-10, pair mean equals marginal Delta within 1e-10. A violated check pauses
   the study for diagnosis; never renormalize a wrong sampler into an apparent win.
2. **Headroom stop:** if co-adapted oracle variance improves <20% over the best
   ordinary coupling on every completed nondegenerate B cell, stop this mechanism
   in this domain. If all headroom is confined to H=1 or disappears under ordered
   CRN, revise rather than claiming adaptive advantage. Oracle ties at zero variance
   are exact ties. A minimum-possible-cost oracle frontier is an optimistic bound,
   with its assumptions displayed, not a measured practical method.
3. **Practical proceed:** on the fixed B timing panel at alpha=1, require >=2x
   median reduction in full measured cost at RMSE 0.01 against the strongest
   ordinary/learned/terminal-averaging frontier, lower 95% paired batch interval
   >1.25x, improvement in at least 75% of nondegenerate B panel cells, and no
   >2x cost regression in more than 10% of those cells. Include a locally expansive
   regime. Report exclusions/zero-variance ties before ratios. Novelty gate below
   must also pass. Use the matched-precision calibration protocol, and bootstrap
   whole matched batches within each fixed cell, recomputing the frontier and
   finite-panel median each time; this measures Monte Carlo uncertainty, not
   generalization to other learners. If precision is not reachable under the fixed budget, report
   unresolved; do not extrapolate a pass from variance alone.
4. **Revise:** clear oracle headroom but practical cost/fitting misses the gate;
   restrict scope and attempt one separately budgeted redesign, never tune on test
   results and reuse the same grid as fresh confirmation. Stop the hierarchy if
   full optimizer-tail cost eliminates its benefit.
5. **Novelty gate:** identify a training-specific bound or mechanism beyond sorted
   transport, generic learning, and Bellman regret. Verify it against the remaining
   overlaps in PRIOR_ART.md. A practical win without this supports an engineering
   result, not the targeted novel-method paper.

Twofold is a proposed minimum because extra state access, estimator maintenance
and coupling construction need a useful margin beyond modest variance changes.
The 20% headroom screen is deliberately weaker and only avoids spending on a
negligible oracle opportunity. Both are engineering choices, not ICML rules.
No observed pilot result is recorded here. Larger-model experiments remain
conditional and require a separate frozen model/data/optimizer/evaluation spec.
