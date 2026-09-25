# Scoping review, questions and dispositions

Date: 2026-09-24. This is an evidence record, not agreement-based validation.
GPT authored the scope, theory, source comparison and pilot/implementation specs.
Prior research and reviews were preserved, including their unresolved objections.

## Routing and first-pass alternatives

GPT's initial options were recorded in `tmp/scoping/gpt-first-pass.md` before any
new Opus output was inspected: full paired continuation; sorted successor
projection/transport; and conditional terminal averaging. Its initial preference
was an exact falsification study, with scalar degeneracy and tail cost as risks.

Opus received `.ai/briefs/scoping-first-pass.md`, based on TASK_TEMPLATE.md, with
the shared screening note and provisional mechanism/known objections, but not
GPT's new preference or draft specifications. Both sides thus had shared prior
framing; this was not blind scientific replication. Opus was asked for two
concrete alternatives, a tiny learner, exact intervention and oracle class,
cost-aware criteria, and answers to:

1. Which assumption is weakest; what counterexample breaks it?
2. What simpler alternative may be as good?
3. What observable check distinguishes the methods and changes the conclusion?
4. What remains unproved, unmeasured or dependent on source verification?

**Actual outcome:** new run `tmp/claude-handoffs/20260924T110611Z-244af48e/`
requested `claude-opus-5-5` and `max`, read-only, at most 6 turns/600 seconds.
The launcher returned `timed_out`, exit 143, empty response, `models_reported: []`.
No actual model identity or effective internal effort was verified. There were
no Opus findings, edited files, or responses to adjudicate. No retry, fallback,
effort reduction or continuation of the older 240-second job occurred.

The requested Opus first-pass alternatives and subsequent cross-model challenge
therefore remain **incomplete**. A concrete follow-up to an actual Opus design
could not be sent. No substantive implementation was dispatched, so no Opus
workspace or integration is claimed. GPT continued the authorized scoping work;
substantive future implementation remains assigned to the required Opus route.

## Non-author GPT review

Reviewer `/root/scope_redteam` was spawned with fresh context (`fork_turns=none`)
and a read-only bounded brief. It read AGENTS.md plus SCOPE.md/THEORY.md, then
PILOT_SPEC.md. It was not an author, did not inspect Opus output, and did not
independently verify literature novelty. Fresh context is not proof of independent
model errors. It checked algebra and ran small independent Python calculations;
it did not execute the pilot or edit files.

| Finding / source | Decisive check | Disposition in current artifacts |
| --- | --- | --- |
| P2, projection horizon ambiguous (reviewer) | At H=1, current successors require zero continuation Jacobians | Accepted. THEORY §4 excludes DF(z0), explicitly uses h-1 factors. Lead reproduced the counterexample below. |
| Scalar equivalence broader than H=1 (reviewer) | Shared scalar projection preserves or reverses both v orderings; interval intersections unchanged | Accepted. THEORY §2 and PILOT §§1,8 make A an all-horizon equivalence control. No scalar novelty claim. |
| Surrogate error must cover reachable pair states (reviewer) | Bellman regret propagation visits later states, not just the initial pair | Accepted. Uniform reachable-pair bound explicit in THEORY §5; tiny-tree row/column residual diagnostic added to PILOT §3. Bound is still not established for the mechanism. |
| P2, sample-count grid can manufacture target-cost ratio (reviewer) | N=1 or an intermediate N may dominate a coarse grid | Accepted. Fresh charged calibration and direct evaluation at selected N now define the practical frontier. Exact-variance allocation is separately labeled diagnostic. |
| P2, uncapped simulation/learned labels (reviewer) | Original diagnostic design required 9,792,000 continuations per method | Accepted. Reduced diagnostic batches and a 24 CPU-hour total stage-2 cap; exact development-label generation included; incomplete cells block proceed. |
| P2, shared Gumbel lacks enumerable joint masses (reviewer) | Derive pair probabilities from exponential races; check marginals/quadrature | Accepted. Analytic piecewise formula added to THEORY §2. Lead high-precision numerical check passed. |
| P2, comparator fast path / statistic unspecified (reviewer) | Identical projected coupling must have identical fast path; Delta=0 is not zero variance | Accepted. Fast-path parity, explicit eligible cells, finite-panel median and matched-batch bootstrap with frontier reselection added to PILOT §§4,8. |
| Generic coupling/DP is not new (source verification + reviewer) | Compare Lorberbom §3/§6 and Moulos §3 against proposed construction | Accepted. Generic lemmas/oracle labeled established or elementary; training-specific theorem is an open obligation. |
| Truncation bias does not imply finite-suppression correction moments (source verification) | Inspect Rege §8 derivative notation; exhibit E[D]=0 with E[D²]=1 | Accepted. No imported finite-suppression theorem and no selected multilevel estimator. |

The reviewer's H=1 fixture uses beta=0, eta=1, q=e1, two actions with
phi1=e1,r1=0.4 and phi2=(1,1)/sqrt(2),r2=1. From zero, suppress action2, giving
x0=0 and y0=(1,1)/sqrt(2). Correctly coupling the next terminal coordinates
gives zero variance; including the extra mean Jacobian produces variance
0.005051497728033068 for sigmoid g. It is a regression counterexample outside
the main K=3 grid, not a measured proposed-method advantage.

## Verification by the lead

`python3 tmp/scoping/analytic_checks.py` completed with exit 0 and **12 passed
checks**. Receipt: `research/scoping/ANALYTIC_CHECKS.json`, with script hash.
Checks cover scalar order equivalence and marginal sums, four feedback-derivative
values, the indexing counterexample, an H=2 pair/marginal expectation identity,
zero-gradient optimizer semantics, grid/tree arithmetic, a locally expansive B
mean map, and shared-Gumbel masses versus 50-digit quadrature. They do not verify
an implemented pilot, an efficiency theorem or a speedup.

The source receipts preserve fetched primary PDFs and their hashes under
`tmp/scoping/sources/`. Direct full access to the nonlocal RL PDF failed; the
prior-art table labels the narrower indexed material actually inspected.
All pre-existing context files matched the initial snapshot before the final
handoff append. No earlier proposal or review was rewritten.

## Remaining objections and decision

* No novel training-specific variance–cost result; the candidate might be only a
  useful application of standard coupling. The exact headroom test must settle
  feasibility before stronger claims.
* No measurement of oracle headroom, practical MSE/cost or learned-baseline fit.
  Full probability/all-action gradient access may eliminate scalability.
* The stated finite grid and proof obligations do not establish generality for
  LLM post-training or distributional unlearning.
* Forward-citation coverage is incomplete, one nearby full text remains access
  limited, and a native generalized-Gumbel comparator remains conditional work.
* The Opus contribution/challenge loop is incomplete because the bounded call
  returned no response. Agreement across models is not claimed.

Decision: **revise the contribution; proceed only to the bounded CPU exactness and
headroom tasks**, with no substantial training study. The artifacts give concrete
specifications and falsification criteria, not a finished-paper narrative.

## Targeted disposition pass

The non-author reviewer read the revised passages and the numerical receipt. It
marked the earlier indexing, scalar equivalence, uniform-error, Gumbel, resource,
learned-fast-path and statistic findings resolved, while flagging one remaining
P2: mandatory calibration overcharged analytically deterministic estimators.
For H=2, depth-2 terminal averaging computes the entire expectation and needs
one enumeration, not 256 calibration copies plus another evaluation.

GPT accepted this objection and added a structural-determinism exception in
PILOT §6: no variance calibration when determinism follows from the algorithm
(full terminal averaging or identical diagonally coupled worlds), with every
branch/evaluation charged and the result included in the practical frontier.
The exception cannot use test oracle variances. This final documentation fix was
checked by the lead, not sent through another redundant review loop. In the H=2,
K=3 case there are 3+9=12 successor evaluations per world for direct tree
integration; its zero Monte Carlo variance follows from summing all paths.

No unresolved reviewer finding is concealed; scientific feasibility, novelty and
the absent Opus contribution remain open as stated above. The reviewer did not
rerun the lead's checks or audit their implementation in the disposition pass.
