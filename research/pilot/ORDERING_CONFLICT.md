# H=2 ordering conflict: exact example and stronger comparator

Date: 2026-09-25. This is a post hoc analysis of the completed v1 exact grid,
not a new experiment, a new method, or a reversal of the failed B-family gate.
The intervention remains suppression of one selected gradient contribution.

## Why the headline hybrid worked

With two future events, let `p_i` and `q_j` be the two worlds' next-action laws.
If root actions `i,j` are paired, let `C_ij` be the minimum conditional expected
squared difference in their terminal scores with one event remaining. In this
scalar pilot, sorting the two terminal-score laws gives that minimum. The root
oracle minimizes `sum_ij pi_ij C_ij` over plans with marginals `p,q`. All such
plans have the same mean effect, so this also minimizes variance.

If `C` is Monge in a chosen pair of action orders, the CDF coupling in those
orders is root-optimal; terminal-score sorting then completes the H=2 oracle.
In B1 witness `27f1126e6c329784`, every 2x2 interaction of `C` in label order
is negative. Thus label-order CDF at the root plus terminal-score sorting is
exactly oracle-optimal in this case. The ordinary `fixed_label` rule alone loses
at the last step; the hybrid removes that loss. Its variance equals the oracle's
`0.0005042727717850104` within the stored numerical precision. This mechanism
explains the two B1 headline witnesses, not every B1 cell or a globally fixed
schedule over the full grid.

## A same-estimand conflict

The existing full-suppression A2 witness `24a16ed9956c3de3` has horizon 2,
`alpha=1`, and effect `delta=0.00817007862282726`. The suppressed and ordinary
root action probabilities are approximately `(0.959303, 0.039103, 0.001594)`
and `(0.057037, 0.205142, 0.737821)`. Its continuation cost has this 2x2 block:

| | ordinary action 0 | ordinary action 1 |
| --- | ---: | ---: |
| suppressed action 0 | 0.005362076 | 0.001352719 |
| suppressed action 1 | 0.002047392 | 0.006043009 |

The diagonal costs `0.011405085` per unit of equal paired mass; the cross
costs `0.003400111`. The difference is `0.00800497434001909`. The `ordered`
and oracle root plans differ by an exchange of `0.03910329512196352` mass
from the two diagonal cells to the two cross cells, lowering second moment and
variance by `0.000313020874061512`. Its variance is `0.000917152608211529`
versus `ordered`'s `0.001230173482273040`, a `25.45%` reduction. The best of
the six tested root rules followed by terminal sorting, chosen per cell in
hindsight, is an independent root here: variance `0.001196041210794032`.
The oracle reduces that hybrid's variance by `23.32%`. Among all six *common* action
permutations for a CDF root followed by terminal sorting, the best variance is
`0.001206996726574582`, leaving `24.01%` reduction room.

This is the precise conflict: the existing immediate-state `ordered` rule uses
the diagonal pairing for that mass, but the adaptive learner's one-step
continuation makes cross pairing cheaper for the final outcome. It establishes
possibility within the original intervention, not usefulness of a proposed rule.

## Why this does not justify scaling

A CDF root with *different* action orders in the two worlds reproduces this
oracle plan exactly: suppressed order `(2,0,1)`, ordinary order `(2,1,0)`.
Using a shared uniform draw with separate orders still gives each world its
required action probabilities and is an admissible online root coupling.
The orders were selected after seeing `C`; this is an oracle/hindsight
representation, not a cheap way to choose them during training. A read-only
check over all 720 completed H=2 cells found 656 nondegenerate cells; in each,
one of the 36 pairs of separate three-action orders matched the stored oracle
second moment to absolute error at most `1.39e-17` in GPT's calculation. A
separate read-only GPT review reproduced the 656-cell result with a maximum
absolute difference of `1.73e-17`; the small discrepancy reflects floating
summation order. Both checks used each cell's stored oracle continuation cost
and show that the current H=2 grid has no representational gap relative to
hindsight-selected asymmetric CDF couplings.

There is a stronger three-action fact: **some** optimum of any 3×3 root
transport problem is one of those 36 asymmetric CDF plans. A linear cost has
an optimal vertex. Every 3×3 transport vertex has acyclic support, and every
forest in the 3-by-3 row–column graph extends to one of 81 spanning trees.
Each such tree can be put in staircase order by separately permuting its rows
and columns. A feasible plan supported on a staircase is exactly the CDF plan
in those orders. This handles zero probabilities and nonunique optima, but an
arbitrary *mixture* of optimal vertices need not be a CDF plan. Opus supplied
the argument; GPT checked all 81 tree embeddings and 405 weighted tree plans,
and a non-author GPT reviewer found no logical gap. The result does not give a
cheap way to select the orders. The analogous claim fails for four actions.

At RMSE `0.01`, the A2 witness needs about 13 `ordered` pairs, 12 pairs with
the best six-rule hybrid, or 10 oracle pairs under the idealized variance
allocation. That excludes the cost of finding a root order or constructing
the oracle. Exact enumeration is cheap at H=2 in this pilot. No wall-time gain,
prospective order selector, H>=3 result, or method novelty is established.

**Decision:** keep the v1 stop decision. Reopen this coupling direction only
with a specific *cheap, online* rule for choosing the two orders (or another
root plan), plus a fresh prespecified test against ordinary hybrids and a
prospective, costed order selector. The hindsight-selected 36-order envelope
is an oracle benchmark, not a deployable competitor. The test must include
full measured cost. Otherwise close this mechanism in the tested setting and
retain the exact negative result.

Evidence: `research/pilot/diagnostics-v1/MECHANISM.md`, both named raw cell
records in `research/pilot/runs/20260924T150726Z/`, and GPT's reproducible
read-only comparator check `tmp/ordering-conflict/check_permuted_cdf.py` with
`tmp/ordering-conflict/receipt.json`. The six-rule hybrid figures are from the
previously reviewed diagnostic; the 36-order comparator is exploratory here.
The finite K=3 tree verification is in
`tmp/ordering-conflict/check_k3_trees.py` and
`tmp/ordering-conflict/k3-trees-receipt.json`; Opus's full argument and the
non-author review are in the associated handoff evidence recorded by
`.ai/HANDOFF.md`.
