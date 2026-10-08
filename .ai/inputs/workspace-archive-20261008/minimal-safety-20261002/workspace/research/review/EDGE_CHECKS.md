# Edge checks: rigor and novelty gates

Initialized 2 October 2026 for [FOCUS.md](../FOCUS.md). A gate names the evidence a claim needs. Passing one authorizes no experiment; failing one does not end the project. No gate is established, which is not evidence of failure. Nothing here predicts novelty scores, ICML outcomes or positive results.

## Claim gates

| Gate | Claim unlocked | Evidence required | If negative or inconclusive |
|---|---|---|---|
| G0 Frozen design | "The study tests X" | Dated frozen design before confirmatory data | Call the work exploratory |
| G1 Measurement | Any effect estimate | Blinded scorer audit including benign prompts; seed noise; measured costs | Repair measurement first |
| G2 Development headroom | "Room to improve over S−" | Development estimate of G(S−), with uncertainty, relative to the practical margin; record whether a0 is best | Revise only in development; retain every confirmatory menu |
| G3 Screen (H1) | "Attribution improves selection-relevant prediction in development" | Matched-capacity, comparably tuned predictors from X0 with versus without attribution; same outcomes; held-out groups; prespecified selection-relevant loss with feasibility | Negative constrains this mechanism here; inconclusive means extend or stop; neither proves attribution useless |
| G4 Decision value (H2) | "Attribution improves S's edit choice at matched cost" | D_info above margin; V under the absolute level and non-inferior; repeated executions on held-out menus, prompts, seeds; full costs | Report the null; a revised study needs new held-out data |
| G5 Allocator (H3) | "P beats S here" | Frozen 2×2 with identical inputs and budget; D_alg above its margin; interaction for the attribution-dependent part | No algorithmic claim |
| G6 Generalization | Claims at the tested level | Unseen menus for menu generalization; new settings for setting transfer; H4 tested out of sample | Restrict scope; significance also depends on magnitude, explanation and novelty |
| N Novelty | "New", "first", "a new method" | Current register with dated primary sources and exact-versus-adjacent overlap; composed baseline run; for a method, a substantive specified difference | State overlap; drop the claim |

Closest composed baseline: S+, existing attribution plus X0 in a constrained generic multi-fidelity selector. No cheap signal certifies an unvalidated edit.

## Overlap register

Unmarked rows: [2 October assessment](2026-10-02-proposal-novelty-rigor-and-reading.md). †: GPT checked the [dated source note](2026-10-02-new-safety-attribution-precedent.md); access/version limits apply. Opus received summaries; its outside-workspace reads were denied. Exact means component overlap; adjacent means related targets or assumptions. Missing overlap is not proof of absence.

| Source | Overlap | Not found in what was read |
|---|---|---|
| [SOURCE](https://arxiv.org/abs/2405.12186), 2024 | Exact: finite removal-effect prediction | Decision value at matched cost |
| [IF-Guide](https://arxiv.org/abs/2506.01790), NeurIPS 2025 | Exact: influence-guided detoxification (other intervention) | Menu selection under side-effect limits |
| [DATE-LM](https://arxiv.org/abs/2507.09424) † | Exact: attribution-based safety filtering with retraining; reliability against safety-aligned distractors; runtime | Matched-cost value beyond short runs and classifiers |
| [Mitigating Emergent Misalignment with Data Attribution](https://openreview.net/pdf?id=gN7pWmjiQW), 2025 workshop version † | Exact: mitigating one behavior while retaining another | Unknown: indexed excerpts only; full-paper overlap not excluded |
| [Weckbecker et al.](https://arxiv.org/abs/2609.20027), September 2026 preprint, v1 † | Exact: attribution-based filtering of subliminal learning; inconsistent benefit | As DATE-LM |
| [ADMIRE-BayesOpt](https://arxiv.org/abs/2508.11551); [Data Mixture Optimization](https://arxiv.org/abs/2503.21023), 2025 | Exact: cheap runs guiding costly data choices | Constrained safety edits; attribution's added value |
| [Multi-fidelity best-arm identification](https://arxiv.org/abs/2406.03033), NeurIPS 2024, v2 (May 2025) inspected; [PROBE](https://arxiv.org/abs/2607.06879), July 2026 preprint, v1 read 24 September | Exact: allocation theory; proxy calibration within best-arm identification | Bias and Gaussian assumptions unverified here |
| [Distributional TDA](https://arxiv.org/abs/2506.12965), 2025 | Adjacent: training randomness | Systematic finite-edit error |
| [LESS](https://proceedings.mlr.press/v235/xia24c.html), ICML 2024 | Exact: influence-based targeted data selection | Safety edits under constraints |

## Checkpoint-triggered review

Triggers: before freezing G0; after the screen; before confirmation or external text; claim changes; exact overlap. Check claims against gate status; one average-model target, X0 and tuning across arms; splits, with the reference hidden; replication per claim, with uncertain optima and feasibility shown; full costs; current register. Log each review in the ledger.

## Weekly literature watch

Mondays at 09:00 local time: search primary preprints/proceedings and citations of listed sources for related safety attribution and adaptive data selection. Record queries, dates, returned counts, versions and access limits. Classify overlap; review exact matches. Empty results do not establish absence.

## Evidence ledger

Append-only. To correct an entry, add a dated row that cites it; never edit or delete earlier rows.

| ID | Date | Statement | Status | Evidence |
|---|---|---|---|---|
| E1 | 2026-10-02 | Operative question and estimands | Drafted, not frozen; G0 unmet | FOCUS.md |
| E2 | 2026-10-02 | H1–H4 | Untested | None |
| E3 | 2026-10-02 | Attribution and short runs share bias | Untested; only a constructed example exists | FOCUS.md; 2 October assessment |
| E4 | 2026-10-02 | Headroom, scorer validity, seed noise, costs, hardware, model, budgets, sample sizes | Unknown, unmeasured or unresolved | None |
| E5 | 2026-10-02 | A distinct proposed selection rule | Not specified | None |
| E6 | 2026-10-02 | Novelty | Unestablished; targeted search only; provisional 2–3/5 distinctiveness and 3/5 design completeness are qualitative | 2 October assessment |
| E7 | 2026-10-02 | Occurrence-level coupling pilot | Different estimand; failed its prespecified gate; not evidence on this question | research/pilot/IMPLEMENTATION_RESULTS.md |
| E8 | 2026-10-02 | ICML acceptance or a 4/5 rating | No guarantee; unknown | None |
| E9 | 2026-10-02 | Refines E6: closest safety precedents added (†) | Overlap recorded; not independently retrieved | Precedent assessment |
| E10 | 2026-10-02 | Refines E1–E2: toxicity, removals only, classifier in X0, H1 as development screen | Drafted, not frozen | FOCUS.md |
| E11 | 2026-10-02 | Gates G0–G6 and N | Untested, not failed | None |
| E12 | 2026-10-02 | Clarifies E6 | Earlier ratings concern the pre-revision proposal; this focus remains untested and unrated | Archived proposal; FOCUS.md |
