# The Price of Faithful Attribution in Adaptive Post-Training

Scoping date: 2026-09-24. Status: proposed feasibility study, no performance result.
Lead: GPT in the Implementation task. The approximately 4/5 novelty and 4/5 rigor
objective is a research target, not a score achieved or an acceptance forecast.

## Recommendation

**Revise the proposed contribution; proceed only to a small CPU feasibility gate.**
The target, adaptive feedback distinction, learned variance-reducing couplings,
and transport-based coupling oracles already have direct precedents. No new
training-specific efficiency theorem or measured speedup has been established.
Do not start an LLM training study on the strength of this scope.

The useful next deliverable is an exact finite-horizon comparison that can reject
the mechanism. In a scalar affine learner, sorting actions by induced updates
reduces to standard quantile common randomness. A gain over action-label matching
alone would therefore be inadequate. Require comparison with ordered common
randomness, a learned coupling, and a terminal-variance oracle.

## Question and target

Can a cheaply constructed coupling of two adaptive training continuations estimate
one occurrence's finite effect at materially lower **complete cost at matched MSE**
than the strongest ordinary paired continuations?

Use state S_j immediately **after** update j. At event t, h_t includes all observed
interactions through Z_t, the pre-update state S_(t-1), and any realized randomness
needed to reconstruct it. Condition on a positive-probability prefix. Clone this
state and apply the ordinary or suppressed contribution to the same observed Z_t.
Subsequently generate observations with each world's own transition kernel.
For the prespecified score 0 <= g <= 1, estimate

    Delta_t(h_t) = E[g(Theta_T^suppressed) | h_t]
                - E[g(Theta_T^ordinary) | h_t].

T is the final update index; H=T-t is the number of future updates. Future seeds
are integrated out, not fixed by conditioning on the original run's entire seed.
If a state is only partly observed, a posterior over hidden state would be needed;
the pilot instead assumes the full simulator state is available.

**Primary intervention:** zero this occurrence's data-loss gradient contribution
inside an otherwise executed optimizer step. Batch denominator and all other
sample contributions remain fixed. Momentum, second moments where applicable,
weight decay, regularizers, scheduler and step counter evolve using that zeroed
gradient. This is neither a skipped step nor deletion of every record occurrence.
THEORY.md gives the exact pilot optimizer; Adam, PPO advantage recomputation and
batch normalization are outside it until separately specified.

The general state includes parameters, optimizer statistics, counters, schedules,
environment state and replay buffers. Random sources must have their correct
conditional law in each world. The tiny pilot has deterministic rewards, no replay
buffer and no persistent environment state. Coupling chooses a joint simulator for
variance reduction; it does not identify a unique individual counterfactual.

## Candidate contribution and alternatives

| Option | Concrete construction | Present assessment |
| --- | --- | --- |
| Full paired continuation | Independent draws, shared uniforms/Gumbels, or maximal action agreement; run both tails completely | Required simple reference, unbiased with correct marginal kernels |
| Update-based transport | Compute action-conditioned successor states and couple nearby updates, with scalar sorted overlap or a small quadratic-cost transport solve | Useful diagnostic; generic OT and scalar sorting are established ingredients |
| Terminal-sensitive update matching | Project successor updates onto a direction computed from the learner's mean update Jacobian, then match probability intervals in that order | Provisional practical mechanism; future-noise terms and construction cost may defeat it |
| Conditional terminal averaging | Enumerate the last one or two rounds instead of sampling them | Strong simpler variance-reduction comparator; no novelty claimed |
| Feedback truncation / multilevel | Regenerate only part of the data stream but still update altered parameters through T | Biased diagnostic first; no hierarchy selected |

A possible gap is a **training-equation-derived** guarantee that an inexpensive
terminal-sensitive construction approximates the variance-optimal co-adapted
coupling well enough to repay its overhead, including a stated noncontracting
feedback regime. That gap is unfilled. Merely proving correct marginals or fitting
a better coupling is insufficient. The generic oracle/regret identities in
THEORY.md organize the work; they are not proposed scientific novelty.

## Success and exclusion boundaries

The initial gate requires numerical marginal correctness, exact enumeration,
independent seed blocks, held-out configurations, and complete cost reporting.
PILOT_SPEC.md defines thresholds before measurements, including a proposed 2x
practically useful cost improvement and a stricter distinction between oracle
headroom and achievable speedup. Thresholds are project decisions, not conference
rules. Stop this mechanism if ordinary coupling matches the oracle or overhead
consumes the gain; this does not rule out every attribution estimator.

No claim of global knowledge erasure follows from one zero mean score. Earlier
effects of a record remain in the fixed prefix. Finite suppression is not an
infinitesimal derivative. Finite-action theory does not imply an arbitrary-LLM
guarantee. Faithfulness here means accuracy for the stated intervention and score;
reasoning faithfulness would require an additional validated behavioral target.

CPU-first implementation is the next bounded task described in IMPLEMENTATION_PLAN.md.
One GPU is only a conditional planning scenario, with no assumed hardware access.
No paid provisioning, publication, substantial training, or entire framework
scaffolding is authorized by this scoping pass. Prior proposals and reviews remain
historical evidence and are preserved.

## Reading order

PRIOR_ART.md records source locations and remaining novelty uncertainty;
THEORY.md fixes definitions and proof obligations; PILOT_SPEC.md fixes the
falsification study; IMPLEMENTATION_PLAN.md breaks it into small owned tasks;
REVIEW.md records actual review evidence and dispositions.
