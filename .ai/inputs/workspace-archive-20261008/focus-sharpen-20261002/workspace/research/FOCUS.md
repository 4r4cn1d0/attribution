# Research focus: does attribution add decision value for safety data edits?

Status, 2 October 2026: exploratory; hypotheses untested; design incomplete; not an adopted protocol or experiment authorization. The separate occurrence-level coupling pilot does not validate this question. Gates and ledger: [EDGE_CHECKS.md](review/EDGE_CHECKS.md).

## Operative question

In one fixed supervised fine-tuning (SFT) setting, does adding training-data attribution to an existing selector that already uses edit metadata, content-classifier scores and short training runs improve its choice among removals of predefined data groups, compared with spending attribution's full cost on more runs? The primary failure is toxic completions.

## Precedents and scope

DATE-LM benchmarks attribution-based safety filtering with retraining, reliability against safety-aligned distractors, and runtime; *Mitigating Emergent Misalignment with Data Attribution* studies mitigating one behavior while retaining another; and [Weckbecker et al.](https://arxiv.org/abs/2609.20027), a September 2026 preprint, find attribution-based filtering of subliminal learning helps inconsistently. With SOURCE, IF-Guide and cheap-run data selection, a reliability benchmark, safety endpoint, side-effect preservation or cost reporting is not alone a contribution. The candidate is matched-cost decision value beyond strong controls, and when it arises. Sources and limits: [precedent assessment](review/2026-10-02-new-safety-attribution-precedent.md).

Toxicity has existing scorers, but content classifiers are strong there: a demanding test whose null would not cover failures content screening misses. Removals alone match what finite-edit attribution such as SOURCE predicts; replacements, which add new data, are a conditional extension.

## Target

Fix a pre-SFT checkpoint, recipe and training-length rule after removal (fixed steps or epochs; unresolved). The menu holds a0 (unchanged data) and K group removals. Endpoints average over training randomness, fixed prompt distributions and decoding:

- F(a): held-out toxic-completion rate under a frozen scorer.
- L(a) = U(a0) − U(a): loss on a frozen benign-capability evaluation; retaining a harmful behavior never counts as utility.
- O(a) = R(a) − R(a0): increase in refusals of benign prompts.

With tau_L, tau_O ≥ 0, a is feasible if L(a) ≤ tau_L and O(a) ≤ tau_O, so a0 is feasible; a* minimizes F over feasible options. A selector with budget B picks one option. By an evaluation scoring convention, not a safety guarantee or fallback policy (none is specified), an infeasible pick scores F(a0) and counts as a violation; otherwise loss is F(pick). Regret G(B) is expected loss minus F(a*); V(B) is the violation rate; both average over selector executions and menus. This fixed-budget, expected-outcome target gives no per-model, anytime-valid or unlearning guarantee.

## Estimands

Base inputs X0 for every arm: edit size, type and source; strong content-classifier scores for the removed group; short-run observations with uncertainty. The fixed existing selector S is a constrained generic multi-fidelity selector (ADMIRE-BayesOpt or multi-fidelity best-arm style; constrained adaptation unresolved).

**Primary:** D_info(B) = G(S−) − G(S+), for S without and with attribution added to X0; S− spends attribution's measured cost on more runs. F(a*) cancels, so an uncertain optimum affects absolute regret, not this contrast; since regret is nonnegative, D_info ≤ G(S−). It measures practical decision value for S at B, not abstract information. Any claimed arm needs V below a frozen absolute level and non-inferior to its comparator within a frozen margin.

**Conditional, only if a new allocator P is specified before freezing:** the 2×2 {S, P} × {−, +} with identical features and budget, and D_alg(B) = G(S+) − G(P+). P may gain both generically and from attribution; its attribution-dependent part is the interaction [G(P−) − G(P+)] − [G(S−) − G(S+)].

## Hypotheses

- **H1, development screen.** Two matched-capacity, comparably tuned predictors of F, L and O, from X0 with and without attribution, are fit by group cross-fitting to the same full-run outcomes on random development removals. Adding attribution reduces a prespecified selection-relevant loss on held-out groups, such as plug-in regret and feasibility errors on resampled development menus. Global mean-squared error is not the target: information near a decision boundary can matter while it barely moves, and gains on removals that cannot win may be worthless. Gains are empirical model comparisons, not proof of conditional mutual information or causation. The screen is a cost filter, not a logical prerequisite for H2.
- **H2, decision value.** D_info(B) exceeds a frozen practical margin at the primary budget on held-out menus, with V acceptable: an empirical finding, not a new algorithm.
- **H3, allocator (conditional).** D_alg(B) exceeds a frozen margin: an empirical algorithmic advantage in this setting. A method claim also needs a substantive specified difference and the novelty gate.
- **H4, characterization (exploratory).** Where attribution helps or misleads, by edit size, classifier confidence, redundant support and nearness to the feasibility boundary.

One setting passing H2 is a small feasibility finding; held-out transfer plus an H4 account of when attribution matters is a substantial empirical contribution.

## Counterexample and diagnostics

If full-run outcomes are independent of attribution given X0 and attribution costs anything, attribution adds only cost, however strongly it correlates with outcomes marginally, for example by tracking content the classifier already scores. Disagreement is a function of both predictions: a candidate feature or trigger, not information beyond them.

Secondary diagnostics, reported but never gating: each predictor's own proxy in full runs, separating target mismatch from approximation error ([proximal Bregman response](https://arxiv.org/abs/2209.05364)); residuals against other seeds' full-run means; agreement-but-wrong rates; noisy disagreement on dominated removals; constructed nested removals with redundant support. Cheap signals direct validation; they certify nothing.

## Baselines

All arms share menus, calibration labels, X0, total budget and comparable tuning: S−; S+, the closest composed baseline; classifier or attribution ranking confirmed by full runs; uniform or exhaustive retraining. IF-Guide, a different intervention, is optional.

## Splits, replication and freezing

Development data serve calibration, tuning, margins, the screen and headroom checks. Confirmation uses untouched groups, menus, audit prompts and fresh seeds; menus are built without compared predictors, and the whole design is frozen first. A withheld reference retrains confirmatory removals on unseen seeds; near-ties and borderline feasibility stay labelled uncertain, reported both ways. Every frozen confirmatory menu is reported, including those where a0 is best: correctly keeping the data is a real decision. A confirmatory null cannot trigger retuning or redesign reported on the same data; a revised study needs new held-out data. Training seeds, not prompts, replicate F, L and O; selector executions replicate decision quality; separate menus replicate generalization. Attribution inherits its trained model's randomness ([Distributional TDA](https://arxiv.org/abs/2506.12965)); executions sharing a run pool are dependent.

## Costs

Charge setup, attribution construction, calibration, tuning, runs, scoring, selection and audit; report one-off cost first, amortization over a stated number of decisions, and the reference's cost separately. No single-run cost comparison is a gate: attribution may cost more than one run yet inform every removal. If attribution plus minimum required validation exceeds B, B is infeasible for S+.

## Staging

0. Development: measure costs and seed noise; audit the scorer blind, including benign prompts; check and record headroom (a feasible removal beats a0, and G(S−) exceeds the margin).
1. Screen H1 and replay D_info on development menus. Prespecified outcomes: negative if the gain's upper bound falls below the margin; otherwise positive if its lower bound exceeds zero, else inconclusive. The screen must be able to reject the practical edge. A negative constrains this mechanism here, not the project or other attribution methods; inconclusive means extend with new development data or stop.
2. Frozen confirmatory D_info; the 2×2 only if P exists.
3. Conditional: replacements; safety regression under further fine-tuning; other settings.

No benchmark suite or theorem is required.

## Unresolved

Base model; SFT data and grouping; menu size and construction; scorer, prompts and decoding; utility evaluation; classifier; tau_L, tau_O, violation level and margins; selection-relevant loss; attribution method and query set; short runs; S and any P; minimum validation; hardware, cost units and budgets; seeds, executions, menus and screen size. Do not fill these by assumption.
