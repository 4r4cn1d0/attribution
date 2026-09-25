# Diagnostics v1: alternatives considered before code

Status: written 2026-09-24 before `pilot/diagnose.py` existed. Seen at this point:
IMPLEMENTATION_RESULTS.md, THEORY.md, PILOT_SPEC.md, the pilot modules and tests, run
metadata/summary/metrics/groups, the three witness records, and the first 14 data rows of
`cells.csv` (A1, beta 0, eta 0.1, H=1). No diagnostic quantity below had been computed.

Question: why do ordinary couplings nearly match the co-adapted oracle at H<=2, and does
the mechanism justify at most one small follow-up study?

## Structural facts the analysis relies on (derivations; each is checked in code or tests)

1. **Last decision.** With one event left the oracle solves 1-D transport of terminal
   scores, whose optimum is the sorted plan. `ordered` sorts by q.U_a(theta) (family B)
   or by v_a (family A, where U_a is increasing in v_a); sigmoid is increasing, so these
   keys order the terminal scores. Hence ordered = oracle = terminal OT at H=1, and the
   `ordered` last-step decision is optimal at H=2.
2. **Two-decision regret identity at H=2.** For method m with root plan pi^m and
   last-step second moments W^m_ab at child pair (a,b), and C_ab = V1*(U_a x, U_b y)
   (the stored `root_cost`),
   E_m[Y^2] - V* = R0(m) + R1(m),  R0 = <pi^m - pi*, C> >= 0,  R1 = sum pi^m_ab (W^m_ab - C_ab) >= 0.
   Means are coupling-invariant, so this is also the variance regret. R0(m) is exactly
   the regret of "m at the root, then sorted at the last step" (fact 1).
3. **Invariances.** R0 is unchanged by adding row-only or column-only terms to C; only 2x2
   interactions C_ab + C_a'b' - C_ab' - C_a'b affect which plan is optimal. With C a
   squared W2 distance between one-step terminal laws, the interaction equals
   -2 * integral (F_a'^-1 - F_a^-1)(G_b'^-1 - G_b^-1) du. If the children are
   stochastically ordered by the sort key in both worlds, C is Monge in that order and
   the sorted root plan is optimal; H=2 headroom is then exactly zero. So positive
   headroom requires a key-order violation (necessary, not sufficient).
4. **K=3 agreement is unique.** A plan with maximal diagonal mass sum_a min(p_a, q_a) is
   unique for K=3 (the two residual supports are disjoint and one has size 1). Maximal
   agreement and any diagonal-maximizing transport plan therefore coincide exactly.
5. **Family A distance = ordered.** Scalar successors (1-eta)theta + eta v_a make squared
   distance a Monge cost in v order, so the distance LP returns the ordered plan.

## Alternatives

| Approach | Tradeoff | Decision |
| --- | --- | --- |
| Stored data only: R0 from stored `root_cost`/root laws, R1 as stored total minus R0 | Cheapest; but R1 becomes a tautological remainder of stored scalars | Kept only as a cross-check |
| Plan differences (L1/TV between method and stored oracle plans) | Easy to show; LP ties and row/column invariance make different plans equally optimal | Not evidence; descriptive only where uniqueness is proved (fact 4) |
| **Exact two-decision decomposition on every completed H=2 cell, all six methods** | Exact, locates loss by decision; needs recomputed plans (~7k small LPs) | **Selected** |
| THEORY section 5 surrogate residual eps via LP | Only an upper bound (2 eps); extra LPs | Rejected; invariant 2x2 interactions carry the same structure |
| Counterfactual dynamics (freeze policy, beta=0 after root, drop unread coordinate) | Separates causes directly but changes marginal laws/estimand | Rejected; use grid beta=0 cells, exact TV and a classification of order failures on the true process |
| Regression/ML of headroom on features | Designed 720-cell grid is not a population; fitting prohibited | Rejected; descriptive group tables |
| Evaluate new rules on v1 cells (THEORY 4 projection, child-mean sorting, hybrids) | Would search the seen grid for winners and contaminate any v2 | Rejected; only R0(m), a term of fact 2, is reported and labeled post hoc |
| High-precision recomputation of all cells | Witnesses already checked at 65 digits | Rejected; independent float64 routes at 1e-12 suffice |
| H=4 or a new sweep | Not authorized; gate failed | Proposal text only |

## Selected minimum analysis (`python -m pilot.diagnose`)

1. Validate inputs: manifest SHA256 must be `62f7bcc4...c57999` and match run metadata;
   every H1/H2 manifest cell has one completed record with `ok` and all checks true and a
   target equal to its manifest entry; H4 targets have no record. Any failure exits 1.
2. H=1: from stored values, max |Var(ordered) - Var(oracle)| and vs terminal OT (fact 1).
3. H=2, every completed cell: recompute root laws, children and last-step laws with the
   public process API; C by merging quantile functions (no LP) vs stored `root_cost`;
   V* by enumerating all 3x3 transport vertices (no solver) vs stored oracle; the stored
   root plan's marginals and cost; each method's plans via the public couplings API and
   an own depth-first enumeration vs stored moments; R0, R1 and their sum vs stored
   (T_m - V*). Tolerance 1e-12 absolute; report actual maxima.
4. Covariates: root total variation, displacement, K=3 diagonal agreement of the oracle
   root plan, key-order Monge violation of C, and each world's adjacent children in key
   order classified as ordered / order failure with comonotone atoms (probability-driven)
   / order failure with non-comonotone atoms (geometry-driven).
5. Summaries for the whole H=2 grid by structure x alpha x beta, and a Monge-vs-headroom
   cross-tab (fact 3 predicts zero headroom where Monge holds).
6. Oracle-allocation bound: max(1, ceil(V/e^2)) for best ordinary and oracle at RMSE
   0.01/0.02/0.005, with zero overhead; it bounds practical gain from above.
7. Record inputs/hashes, wall and CPU seconds, and peak RSS. No timing claims.

## Focused examples and controls (rule fixed now, before any diagnostic output)

The three witnesses were selected after v1 as maxima (named in the brief). Controls are
every completed H=2 cell differing from a witness in exactly one factor: beta (the other
three values, including 0), structure (B1<->B2; A2 -> A1, A3) or alpha (the other value),
plus the witness's H=1 twin. All H=2 cells also enter the grid summaries; none are dropped.
Everything here is a post hoc diagnosis of v1 and cannot serve as fresh confirmation.

Conventions preserved: conditional estimand; suppressed minus ordinary; zero-based actions;
`intervention_pair`; full `State` through `apply_event`; plans used as checked, never
renormalized; no fitting, no new horizons, no prior files modified.

## Addendum: additions made after seeing the first diagnostic output

Everything above was fixed before any diagnostic number existed. After the first run
showed that `fixed_label` was root-optimal in most B1 headroom cells, and that no
headroom cell had stochastically ordered children, I added the following. They are
properties of the same H=2 trees or re-summaries of stored variances. None evaluates a
new coupling rule, and none changes the example/control rule above.

1. Whether each world's three children are totally stochastically ordered (necessarily in
   child-mean order), with an identity check that C is then Monge in that order.
2. The Monge violation of C in child-mean order, and whether label order (or its
   reverse in both worlds) equals child-mean order. There is an identity check that
   label-order Monge implies an optimal `fixed_label` root.
3. The oracle's remaining reduction over the best root rule followed by terminal sorting,
   restricted to the five relabelling-equivariant rules (all except `fixed_label`).
4. From stored variances only, the headroom against those five single rules. This is a
   labelling-sensitivity diagnostic, not a re-evaluation of the frozen gate.
5. A compact per-example table.

## Clarification, 2026-09-24, after review

The text above is kept as first written. Review found five statements in it broader than
the analysis supports. They are corrected here; no plan step or v1 value changed.

1. **Allocation (step 6).** "Zero overhead; it bounds practical gain from above" is too
   broad. N = max(1, ceil(V/e²)) counts averages of independent unbiased paired samples
   with known V. Comparing the best ordinary coupling with the oracle assumes the same
   admissible (co-adapted) class, equal cost per pair and negligible setup. The ratio bounds
   the sample-count gain only in that setting. It bounds nothing about other estimators
   (exact enumeration, Rao-Blackwellisation), wall time, or methods with different per-pair
   or setup costs.
2. **Order classes (step 4).** "Probability-driven" and "geometry-driven" are descriptive
   labels, not causes. 'weights' means every same-action atom is comonotone, so equal
   weights would restore the order. 'atoms' means some same-action atom is reversed. It
   does not isolate a causal effect of geometry from changing probabilities.
3. **Addendum items 3 and 4.** The five rules other than `fixed_label` are not
   relabelling-equivariant. `ordered` breaks key ties by action ID; a tied-key test shows
   its plan changing under a label swap. `distance` keeps the LP's pick among tied optima,
   so only its optimal value and optimal set are equivariant. The subset is now named
   "without fixed_label" in code and outputs. It is a descriptive sensitivity check. It
   neither drops `fixed_label` from the v1 comparator nor reopens the gate.
4. **Best root rule followed by terminal sorting (addendum item 3).** It is chosen per cell
   in hindsight. That makes it an envelope, not a selection policy or a fresh evaluation.
   The results of single fixed schedules are reported separately.
5. **Vertices (step 3).** "All 3x3 transport vertices" is imprecise. The code enumerates the
   81 candidate bases and keeps the feasible basic solutions; how many are feasible, and
   how many are distinct, depends on the marginals.

Input validation (step 1) now also checks, for every H1/H2 record, stored variances against
pilot.pair's convention and the headroom block against pilot.headroom's definitions. At
H=2 it recomputes the oracle and terminal-OT means, the terminal-OT second moment and the
action probability. Non-finite or mistyped stored values are rejected.


### Lead wording closure, 2026-09-24

A final review separates sample count from computational cost: the paired-average
sample-count bound needs the estimator/coupling-class assumptions, but equal costs
are needed only to translate counts into a runtime comparison. The equal-cost
assumption above is sufficient for that interpretation, not necessary for the
sample-count arithmetic. MECHANISM.md also now states that crossing CDFs and
measured Monge failure are separate observations, terminal OT is outside the
allowed co-adapted online class rather than unimplementable offline, and longer
horizons remain untested. These are wording corrections; no numbers changed.
