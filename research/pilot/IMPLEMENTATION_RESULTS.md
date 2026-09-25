# Exact attribution pilot: implementation and headroom results

Date: 2026-09-24. Campaign: `20260924T150726Z`.

The implementation is complete for authorized steps 1–3. All 1,440 H1/H2 cells
passed the numerical checks, with no errors or censored cells. The prespecified
B-family gate did **not** pass: maximum oracle variance reduction was 18.48%,
below 20%. All 720 H4 cells were therefore left unrun by design. This is a result
for the completed short-horizon grid, not evidence that longer horizons cannot
have headroom.

## What was built

Claude Opus implemented the adaptive learner, exhaustive marginal attribution,
six ordinary paired couplings, the Bellman co-adapted oracle, noncausal terminal
optimal-transport lower bound, and single-cell JSON CLI. GPT framed and reviewed
the work, constructed independent checks, integrated reviewed files and ran the
measurement orchestration. Sources: [pilot](/Users/spiderishi/Coding/attribution/pilot/README.md).

The ordinary methods are independent continuation, fixed-label shared uniforms,
ordered shared uniforms, maximal action agreement, shared Gumbels, and
full-update-distance transport. The estimand is the conditional effect of
suppressing one observed gradient occurrence while each world's future actions
are regenerated. Momentum/decay/counters still execute at zero gradient weight.
The sign is suppressed minus ordinary; the observed action probability is
metadata, not a multiplier on the conditional effect.

Earlier handoff timeouts were diagnosed with instrumented calls. A successful
run showed prolonged generation before its first edit; this does not prove the
cause of every earlier uninstrumented timeout. The launcher now defaults to no
Claude time or turn cap, following the user's instruction. The correction pass
reported 80 turns and model `claude-opus-5-5`; `max` effort was requested, while
actual internal effort is not reported. Denied exploratory tool calls remain in
the run evidence; permitted tests and independent verification completed the work.

## Frozen design and outcome

[Manifest](/Users/spiderishi/Coding/attribution/research/pilot/headroom-manifest-v1.json), SHA256
`62f7bcc4d85d291bca20234b68fe3c3d287bdc2401afeaa4c1022f7dc1c57999`,
was frozen before measurements. It contains five families, four feedback values,
two learning rates, three initial coordinates, three observed actions, two
suppression strengths and horizons 1, 2, 4. The H4 extension requires at least one
completed nondegenerate B-family cell at H<=2 with at least 20% headroom.

Headroom is `1 - oracle variance / minimum variance over the six ordinary methods`.
Ratios are omitted when that denominator is at most 1e-14. Of 1,440 completed cells,
1,312 are nondegenerate and 128 are degenerate; 544 nondegenerate cells belong to
B1/B2. None of those 544 reached 20%. H1's maximum fractional gain was 6.01e-14,
consistent with numerical equality.

Maximum variance reduction at H2, separating full suppression from the secondary
partial-suppression diagnostic:

| Family | Full suppression, alpha 1 | Partial suppression, alpha 0.25 |
| --- | ---: | ---: |
| A1 | 0.00% | 0.00% |
| A2 | 25.45% | 11.79% |
| A3 | 3.75% | 11.73% |
| B1 | 14.12% | 18.48% |
| B2 | 0.00% | 0.00% |

The group medians are numerically near zero. These maxima describe this fixed
grid; they are not population-level estimates. Two scalar A2 cells exceeded 20%,
but the frozen gate explicitly requires B-family evidence. Scalar oracle gains
do not establish a new practical projected method; the scalar family is the
specified equivalence control for that proposed rule.

The strongest B-family case is B1, beta 8, eta 0.4, theta=(-0.4,0), action 0,
alpha 0.25, H2 ([cell 27f1126e6c329784](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/27f1126e6c329784.json)):
ordinary variance 0.0006185727799506621; oracle variance 0.0005042727717850106;
reduction 18.4780209978%. The strongest full-suppression B case reaches 14.1150400698%
([cell d7fbdd78951f35b0](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/d7fbdd78951f35b0.json)). The scalar maximum
is 25.4452626863% ([cell 24a16ed9956c3de3](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/24a16ed9956c3de3.json)).

## Verification and numerical limits

The final project suite passed 126 tests. Non-author GPT review closed four
findings with 16 targeted checks: original-cost residual accounting in solver
diagnostics; immutable coupling matrices; convergent independent shared-Gumbel
quadrature; and rejection of oversized horizons before enumeration. Earlier
independent checks included 60-digit marginal fixtures, finite-vertex transport
solutions, Bellman recursion, and actual operation counters.

A final non-author check independently recomputed all six baselines and the oracle
for the three leading witnesses above using 65-digit direct process equations,
finite transport vertices and numerical shared-Gumbel quadrature, without importing
production code. Every baseline variance differed by less than 3.37e-18; the largest
headroom-ratio difference was 1.03e-15. The independent gate audit also matched all
counts. [Witness verification receipt](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/independent-witness-checks.json).

Across the measured grid, maximum pair-mean error was 3.12e-16, maximum local
marginal residual 4.58e-16, and maximum marginal-law mass error 2.22e-16. No negative
plan entry or variance correction was observed. The largest absolute accumulated
oracle gap estimate was 1.34e-17. All ordering checks passed with their fixed 1e-12
tolerance; diagnostics cannot widen that tolerance.

These are exhaustive finite sums evaluated in float64, not exact symbolic real
arithmetic. `gap_estimate` and `suboptimality_estimate` are numerical, one-sided
diagnostics; they are not certified error bounds. Acceptance includes an
additional oracle-gap diagnostic check at 1e-12, adopted before measurement. This
was a correctness check, not a change to the frozen headroom gate. Input laws and
plans are checked without clipping or renormalization.

## Cost and reproducibility

The campaign used four worker processes, a pinned Python 3.11 environment and
single-thread BLAS environment settings. Total charged child-plus-parent CPU
was 763.934 seconds (12.73 CPU minutes), including per-cell interpreter/import
startup and verification orchestration. Maximum completed-child RSS was 71.16 MiB.
The frozen experiment limits were 60 seconds per cell, 8 CPU-hours and 8 GiB aggregate
RSS planning capacity; no limit was reached. The user's removal of Claude limits
did not change these scientific experiment limits.

Construction timings under this four-worker run sum to 0.926 seconds for marginal
truth and 12.434 seconds for the oracle. These are reference-construction wall
timings, not online-estimator or matched-precision benchmarks. Full terminal
marginal enumeration gives a deterministic zero-variance reference and is
reported separately; it is excluded only from the explicitly paired-coupling
headroom ratio, not from any future practical cost comparison.

Source hashes remained unchanged throughout measurement. The runner passed five
separate fake-cell failure checks, including failed process creation, timeout,
source modification and an exited parent with a descendant holding output pipes.
The RSS guard is a conservative post-completion planning check, not a hard OS
memory limit. No training, learned coupling, proposed coupling or practical
matched-cost experiment was performed.

- [Run summary](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/summary.json) and [source/runtime metadata](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/metadata.json)
- [All 2,160 cells, including 720 unrun targets](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/cells.csv)
- [Family/horizon/suppression summaries](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/groups.csv)
- [480 complete action-probability-weighted slot summaries](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/slots.csv)
- [Machine-readable metrics](/Users/spiderishi/Coding/attribution/research/pilot/runs/20260924T150726Z/metrics.json)

Slot variances are probability-weighted *conditional* variances, not unconditional
variances of a random-action mixture. Individual cell files retain method moments,
operation counts, diagnostics and timing. Prior research and review artifacts are
preserved.

The appropriate next research step is to reconsider the candidate or formulate
a justified new pilot version. The current short-horizon results do not clear the
prespecified extension gate and do not establish practical speedup or novelty.
