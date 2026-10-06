# Research focus: diagnose or retrain? Repairing LLM safety after benign fine-tuning

Status, 2 October 2026: exploratory; hypotheses untested; design incomplete; not an adopted protocol or experiment authorization. The separate occurrence-level coupling pilot does not validate this question. Gates and ledger: [EDGE_CHECKS.md](review/EDGE_CHECKS.md).

**Status, 6 October 2026: the user adopted a new direction ("adopt this new path … this is our new direction").** The reasons and the change table are in the [reframing proposal](review/2026-10-06-reframing-proposal.md), which follows the [positioning review](review/2026-10-06-positioning-review.md) and the [problem-validation review](review/2026-10-06-problem-validation.md). It is still exploratory: the design is incomplete and not yet frozen.

## Adopted direction (6 October 2026)

**Working title:** *Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning*

**Question:** when fine-tuning on benign data makes an aligned language model less safe, which data fix restores safety without hurting the task or causing over-refusal, and how much diagnosis is worth paying for before choosing?
- **Fixes:** keep the data; remove a subset or source; add safety data; rewrite or self-distill responses.
- **Diagnostics:** content-classifier scores; representation similarity; training-data attribution (gradient similarity, influence functions); short trial runs.

**What changes from the 2 October version below:**
- **Setting.** The main setting is an aligned model fine-tuned on real benign data that erodes its safety.
  - Content classifiers are *expected* to see little there. This is untested.
  - The erosion may also be diffuse, with no row- or source-level cause for any diagnostic to find. Whether it is localized is a question the kill test must answer.
  - The literature support (Qi et al. 2023; He et al. 2024) must be read in full before it is cited. He et al. chose benign rows specifically to break safety, so it shows that benign rows *can* erode safety, not that ordinary fine-tunes do.
  - Overt injected harmful data (headroom v2) is the anchor or control case, where the classifier should win.
  - Safety-aligned look-alike data (ToxicChat-Het) is an optional middle case.
- **Fixes.** The menu includes additions (safety data) and rewrites, not only removals. Units are data sources or datasets.
- **Outcome.** Broad harm, with over-refusal and task skill as feasibility limits (the F, L, O structure below still applies).
- **Cost.** Charge every diagnostic, the classifier included, its measured cost in full-run equivalents. Report decision value as a function of the ratio between diagnostic cost and run cost, not at one budget.
- **Hypotheses.** Predicting a fix's side effects (over-refusal, lost task skill) better than trial runs at matched compute is co-primary with decision value.
- **Selector.** Fixed-budget successive halving with a feasibility screen. Multi-fidelity BO is only a sensitivity check.
- **Claims.**
  - Do not claim that practitioners ask whether attribution is worth its compute. We found no public evidence that they do; researchers and funders ask it. This is absence of evidence from public sources, not proof.
  - Do not claim that real fixes are "mostly additions". Public incidents show additions, and fine-tuning services push customers toward removal ("fix the data and resubmit"). Both belong on the menu.
  - Do not present round 1 as "classifiers fail": it was a finding about a fixed-size top-K rule.
  - The classifier's cost was about 58 min for 9,788 rows with *eager* attention, roughly 0.6–0.8 of a round-1 job. It is a one-off per dataset, while trial runs grow with the number of fixes on the menu. Measure it again with SDPA.

**Unchanged:**
- frozen rules before outcomes;
- training-seed replication;
- held-out confirmation (the held-out menus must contain sealed contamination);
- "too close to call" reporting;
- full cost accounting;
- the regret estimand D_info below, applied to the new menu.

**Next gates:**
1. A kill test in the benign-erosion setting (about 10–14 runs; requirements in the reframing proposal, section 3a):
   - a two-seed headroom check first;
   - ground truth from seeded removal runs per source;
   - a test of whether the erosion is localized or diffuse;
   - the informative comparison is attribution against representation similarity, because the classifier will rank benign data almost uniformly, so disagreeing with it means little;
   - a pass needs a margin fixed in advance that exceeds the seed spread;
   - time every diagnostic.
2. A design revision of the sections below, then a freeze.

**Decisions, 6 October 2026 (evening IST; the user agreed):**
- **The kill test decides, by its own rules.** If Stage 0 or Gate B fails, take the fallback below rather than adjust the design until something passes. The size and spending rules are in the [kill-test design draft](experiments/2026-10-06-kill-test-design-DRAFT.md).
- **The agreed fallback, if the erosion is diffuse (Gate B) or absent after the ladder:** the paper becomes *choosing a data fix under its side effects at a fixed compute budget*. The question: which fix (keep, add a safety mix, rewrite or self-distill) restores safety within the over-refusal and task-skill limits, and can a cheap signal predict a fix's side effects better than trial runs at the same compute? This keeps co-primary side-effect prediction and the cost accounting. It does not need a localized cause. v2's over-refusal result (1/50 → 22/50 XSTest-safe refusals in both seeds) is its development motivation.
- **Write the paper around one plain headline.** Keep the estimand machinery in the protocol and the appendix.
- **Contact the authors of the benign-erosion papers early** (Qi et al.; He et al.), with the Stage 0 result, about the expected size and localization of the erosion at small scale.
- **Apply for funding now:** BlueDot first, $6,000 (the [draft](grant/2026-10-06-bluedot-application-DRAFT.md)), then the other funders in the grant dossier, §11c.

**Target venue:** ICML 2027 (deadline estimated at about 22 January 2027; not yet official), if about $3–5k of funding arrives by early November. Otherwise NeurIPS 2027.

## Operative question (2 October 2026 version; superseded on 6 October by the adopted direction above)

The sections below are the 2 October design. They still define the estimands, the protocol and the cost rules, but the setting, menu, endpoint and selector are replaced as listed above. A full revision follows the kill test.

In one fixed supervised fine-tuning (SFT) setting, does adding training-data attribution to an existing selector that already uses edit metadata, content-classifier scores and short training runs improve its choice among removals of predefined data groups, compared with spending attribution's full cost on more runs? The primary failure is toxic completions.

## Precedents and scope

DATE-LM benchmarks attribution-based safety filtering with retraining, reliability against safety-aligned distractors, and runtime; *Mitigating Emergent Misalignment with Data Attribution* studies mitigating one behavior while retaining another; and [Weckbecker et al.](https://arxiv.org/abs/2609.20027), a September 2026 preprint, find attribution-based filtering of subliminal learning helps inconsistently. With SOURCE, IF-Guide and cheap-run data selection, a reliability benchmark, safety endpoint, side-effect preservation or cost reporting is not alone a contribution. The candidate is matched-cost decision value beyond strong controls, and when it arises. Sources and limits: [precedent assessment](review/2026-10-02-new-safety-attribution-precedent.md).

Toxicity has existing scorers and strong content classifiers. A null would not cover failures content screening misses. Removals alone match what finite-edit attribution such as SOURCE predicts; replacements, which add new data, are a conditional extension.

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

One setting passing H2 is a feasibility finding. A substantive empirical contribution would also need meaningful gains, reproducibility, a tested explanation and distinctiveness. New menus test menu generalization; new settings test setting transfer.

## Counterexample and diagnostics

Constructed failure case: cheap evidence already lets S select the best feasible option. Redundant attribution cannot improve that choice and consumes compute. Conditional redundancy alone does not prove this for an implemented selector: a redundant transformation may help it use information. Disagreement is a function of both predictions: a candidate feature or trigger, not information beyond them.

Secondary diagnostics, reported but never gating: each predictor's own proxy in full runs, separating target mismatch from approximation error ([proximal Bregman response](https://arxiv.org/abs/2209.05364)); residuals against other seeds' full-run means; agreement-but-wrong rates; noisy disagreement on dominated removals; constructed nested removals with redundant support. Cheap signals direct validation; they certify nothing.

## Baselines

Compare S−; S+, the closest composed baseline; classifier or attribution ranking confirmed by full runs; uniform or exhaustive retraining. Match menus, permitted calibration data, budget and tuning effort. S/P receive X0; auxiliary baselines may skip unused inputs and reinvest their costs. IF-Guide is optional.

## Splits, replication and freezing

Development data serve calibration, tuning, margins, the screen and headroom checks. Confirmation uses untouched groups, menus, audit prompts and fresh seeds; menus are built without compared predictors, and the whole design is frozen first. A withheld reference retrains confirmatory removals on unseen seeds; near-ties and borderline feasibility stay labelled uncertain, reported both ways. Every frozen confirmatory menu is reported, including those where a0 is best: correctly keeping the data is a real decision. A confirmatory null cannot trigger retuning or redesign reported on the same data; a revised study needs new held-out data. Training seeds, not prompts, replicate F, L and O; selector executions replicate decision quality; separate menus replicate generalization. Attribution inherits its trained model's randomness ([Distributional TDA](https://arxiv.org/abs/2506.12965)); executions sharing a run pool are dependent.

## Costs

Charge setup, attribution, calibration, tuning, selection, runs (including the chosen edit's final training), scoring and audit. Report one-off cost first; amortize over stated decisions. Extra reference-study cost is separate. No single-run cost comparison is a gate: attribution may cost more than one run yet inform every removal. If attribution plus minimum required validation exceeds B, B is infeasible for S+.

## Staging

0. Development: measure costs and seed noise; audit the scorer blind, including benign prompts; estimate G(S−) and its uncertainty against the practical margin. Record whether a0 or a removal is best; either can provide headroom over S−.
1. Screen H1 and replay D_info on development menus, with separate margins for their different units. For each gain, prespecify: negative if its upper bound is below its margin; positive if its lower bound exceeds its margin; otherwise inconclusive. Feasibility depends on attainable precision and measured cost. A negative constrains this mechanism here; inconclusive means collect new development data or stop.
2. Frozen confirmatory D_info; the 2×2 only if P exists.
3. Conditional: replacements; safety regression under further fine-tuning; other settings.

## Unresolved

Base model; SFT data and grouping; menu size and construction; scorer, prompts and decoding; utility evaluation; classifier; tau_L, tau_O, violation level and margins; selection-relevant loss; attribution method and query set; short runs; S and any P; minimum validation; hardware, cost units and budgets; seeds, executions, menus and screen size. Do not fill these by assumption.

## Dated initial-study amendment, 2 October 2026

The user has now authorized the four-step initial study and removed its prior financial cap. The opening status and unresolved list above describe the proposal before this authorization; the confirmatory protocol is still not frozen. Follow the new engine/protocol and dated design review as they are verified, while preserving earlier artifacts.

For this initial study, use **Qwen3Guard-labelled unsafe response rate** as the proposed operational primary endpoint, with ToxicBERT comment toxicity, model-assisted material-harm assessments, benign task correctness and refusal reported separately. This is an explicit measurement-scope amendment; these constructs are not interchangeable. The two fresh-context model-assisted audits do not replace human validation. [Audit](experiments/2026-10-02-measurement-audit.md); [design adjudication](review/2026-10-02-study-v2-design-adjudication.md).

In X0, "edit type" means the permitted operation (here, removal), never the benchmark's hidden Unsafe/Safety-Aligned/Benign label. Raw data IDs reveal these labels and must not enter the selector. Group IDs are opaque. Held-out removal member pools exclude the first pilot's eight previously removed rows, which are assigned to development. Test members still appear in common baseline training; their removal outcomes, selector seeds and final evaluation prompts are held out.

The proposed implementation expands to a pinned1.5B model, complete training text (all original conversations fit3072tokens), multiple full-epoch checkpoints, context-aware scoring, and ARC-Easy capability checks. These are design choices, not empirical success or a guarantee of adequate power. Current novelty and safety-effect hypotheses remain unproved. A null or inconclusive initial comparison leaves the project active.
