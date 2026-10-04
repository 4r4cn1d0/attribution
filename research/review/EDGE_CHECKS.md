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
| [Luo et al.](https://arxiv.org/abs/2609.02771), September 2026 preprint; HTML read 5 October 2026 | Exact: influence-guided response rewriting for safety refusal and abstention; deletion and reweighting weak; attribution-selected rows beat random, TRAK and probe selection ([note](2026-10-05-rewriting-precedent.md)) | Strong cheap selectors (classifier, short runs); selection cost at matched compute; finite menus with held-out confirmation and seeds |
| [ADMIRE-BayesOpt](https://arxiv.org/abs/2508.11551); [Data Mixture Optimization](https://arxiv.org/abs/2503.21023), 2025 | Exact: cheap runs guiding costly data choices | Constrained safety edits; attribution's added value |
| [Multi-fidelity best-arm identification](https://arxiv.org/abs/2406.03033), NeurIPS 2024, v2 (May 2025) inspected; [PROBE](https://arxiv.org/abs/2607.06879), July 2026 preprint, v1 read 24 September | Exact: allocation theory; proxy calibration within best-arm identification | Bias and Gaussian assumptions unverified here |
| [Distributional TDA](https://arxiv.org/abs/2506.12965), 2025 | Adjacent: training randomness | Systematic finite-edit error |
| [LESS](https://proceedings.mlr.press/v235/xia24c.html), ICML 2024 | Exact: influence-based targeted data selection | Safety edits under constraints |
| [DRA](https://arxiv.org/html/2502.11411v2), v2 October 2025 | Exact: attribution-based filtering, strong classifier comparisons and retrained safety | Matched-cost added value over short-run selection not established by this read; [source note](2026-10-02-dra-baseline-check.md) |

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
| E13 | 2026-10-02 | Further refines E6/E9: DRA comparison required for main-study baseline choice | Exact component overlap; no new novelty conclusion | [DRA check](2026-10-02-dra-baseline-check.md) |
| E14 | 2026-10-02 | Refines E4: bounded CUDA pipeline, one same-data checkpoint control and calibration-specific costs measured | Engineering pass only; scorer validity, useful headroom, H1–H4 and novelty remain untested | [First Runpod calibration](../experiments/2026-10-02-minimal-safety-calibration-results.md) |
| E15 | 2026-10-02 | Refines E4/E14: two blinded model-assisted audits completed on50unique pilot pairs; original scorer flags same3harmful prefixes, fromoneprompt;77/108generations capped | Measurement limitations characterized; human validation and G1 remain unmet; no expanded effect estimate | [Measurement audit](../experiments/2026-10-02-measurement-audit.md) |
| E16 | 2026-10-02 | User authorizes four-step initialstudy and removes$10cap; explicit proposed endpoint amendment to classifier-defined unsafe responses; full-text, leakage and matched-cost design changes under implementation | Design reviewed, not frozen or tested; H1–H4/N remain unestablished | [Design adjudication](2026-10-02-study-v2-design-adjudication.md); FOCUS amendment |
| E17 | 2026-10-02 | Expanded engine verified locally149tests/CUDA150tests; full pinned corpus preparation passes; exact two-step fresh-process and cross-host numerical fixtures; full-data development underway | Engineering evidence, not H1/H2 or novelty. Original micro4 memory failure preserved; micro2/accum4 keeps effective8/full text. No held-out outcomes | .ai/inputs/study-v2-20261002/engine-integration-verification.json; .ai/HANDOFF.md |
| E18 | 2026-10-02 | Clarifies E16 operational F: emitted-text Unsafe flags and missing-label uncertainty separated from broader cap/Controversial sensitivity; exact unique-argmax U separated from tie sensitivity | Prospective pre-heldout amendment awaiting StageB implementation/tests; no safety/ICML claim | [Outcome amendment](../experiments/2026-10-02-outcome-definition-amendment.md) |
| E19 | 2026-10-02 | StageA primary recipe and 13-arm × 2-seed development matrix frozen; full retained-corpus three-epoch exposure, 2048-token emitted-text endpoint | Development executing; no selector/hidden outcomes; StageB/N/cost tariff not frozen | [StageA freeze](../experiments/2026-10-02-stage-a-freeze.md) |
| E20 | 2026-10-02 | All31 calibration and cap-sensitivity run archives verified; doubling1024to2048 preserves original prefixes/EOS and Unsafe counts in15 paired cells | Calibration-specific truncation evidence, not uncensored-output validity | .ai/HANDOFF.md; tmp/study-v2-20261002/cap-comparison-complete.json |
| E21 | 2026-10-02 | Blinded posttraining100-pair/20-prompt audit and nine-output contrast assessment characterize policy-boundary disagreements | Classifier-defined diagnostic only; favorable audited flag changes do not demonstrate material-harm reduction; new-recipe transfer audit pending | [Measurement audit](../experiments/2026-10-02-measurement-audit.md); [Transfer plan](../experiments/2026-10-02-measurement-transfer-plan.md) |
| E22 | 2026-10-02 | Cost scope separates selection plus one chosen model from extra research reference; inference separates working-normal exploration from bounded confidence claims | Amendments before hidden access; implementation verification pending; no cost saving or assured benefit established | [Cost amendment](../experiments/2026-10-02-cost-scope-amendment.md); [Inference amendment](../experiments/2026-10-02-inference-interpretation-amendment.md) |
| E23 | 2026-10-04 | dev-matrix-002 executed: 13 arms × 2 seeds on A100s under the recovery safeguards; 78/78 units verified; no single-group removal (0.08–0.63% of rows) clearly moves e3 unsafe counts (arm means 18.5–22.5 against a0 19.0; within-arm seed gaps up to 6); ARC 0.849–0.878; no benign refusals | Descriptive development evidence for G2 only: little headroom for these edits in this setting; no attribution, selector or held-out outcome | [Results](../experiments/2026-10-04-dev-matrix-002-results.md); private release backup-2026-10-04 |
| E24 | 2026-10-05 | Headroom amendment drafted: base `Qwen2.5-1.5B` with rank-64 all-linear LoRA (user); edits of 2.5–10% (user); remove, rewrite, random and add arms in a development positive control before any decision-study menu | Draft for review; not frozen; authorizes no run; rewriting and attribution-guided selection are precedent (Luo et al.), not claims | [Amendment draft](../experiments/2026-10-05-headroom-amendment-draft.md); [Precedent](2026-10-05-rewriting-precedent.md) |
| E25 | 2026-10-05 | Engine support for the headroom amendment integrated behind draft recipe options: base recipe (rank-64 all-linear LoRA, 73,859,072 parameters), edit files (remove, rewrite, add, combined), row scorer, edit builder, rewrite generator, A100 fixture script. Group-removal and a0 runs equal the `8dd630c` engine's golden digest, which the original engine reproduces independently. Edit arms are refused when they name held-out members or run on the held-out split | Engineering verification on CPU fixtures only; nothing ran on a GPU. Engine code identity is now `b1df9a29…`, so dev-matrix-002 continuations need the archived engine. Whether the base model learned `<|im_end|>` is unverified (reported untrained in Qwen2.5 base models) | [Integration review](../../.ai/inputs/headroom-engine-20261005/integration-review.md); [Brief](../../.ai/briefs/headroom-engine-20261005.md) |
