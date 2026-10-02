# Minimal experiment, first pass (read-only design; nothing was run)

**Recommendation:** I recommend option B, a headroom-first group-removal experiment. It is one complete slice: one model, one DATE-LM toxicity mixture, one attribution method, one short-run length, all run on the Mac. The three levels of evidence land at different times:

- **Engineering feasibility:** the stage-0 checks, by Oct 16.
- **Predictive development screen (H1):** stage-1 analyses 1–2, by Nov 6.
- **Matched-cost decision gain:** only an indicative replay in stage 1. The primary D_info needs the adaptive selector S and frozen confirmation, so it is stage 2, after Nov 6.

Dates are planning assumptions. I did not open the DATE-LM repository, so every DATE-LM detail below is something to verify first.

## Alternatives

| | A. Rerun DATE-LM's detection task | **B. Headroom-first removal slice** | C. Planted-mechanism control |
|---|---|---|---|
| What runs | DATE-LM scripts on its released Pythia-1b toxicity checkpoint, scored by AUPRC | Retraining from a fixed checkpoint under group removals; measures F/L/O, short runs, attribution | B's pipeline on a mixture with constructed groups the classifier cannot see, plus redundant groups |
| Engineering | Attribution only; configs target CUDA; whether it runs on the Mac GPU (MPS) is unverified | Full slice | Full slice |
| H1 screen | No: AUPRC ranks injected examples; no removal outcomes, no X0 | Yes (development) | Only shows the measurement setup can detect a planted effect |
| Decision gain | No | Indicative replay | Built in by construction, so not evidence |
| Use | Borrow its data and use AUPRC as a sanity check | **Chosen: tests the weakest assumption first** | Fallback if B finds no headroom |

An example C construction: benign "continue the user's text" data that makes the model repeat toxic prompts; or duplicated toxic groups (redundant support).

## Proposed design (for GPT/user to adopt; not yet adopted)

- **Model:** `EleutherAI/pythia-160m-deduped` (cached, final revision), full fine-tuning in fp32 on MPS. This is a cost choice, not a scientific one.
  - If stage 0 fails because 160m output is incoherent, try `pythia-410m-deduped` before changing anything else.
  - For the Nov 6 screen, more groups matter more than a bigger model.
- **Data and task:** one DATE-LM toxicity mixture at commit 95c9a6d, with dataset revisions pinned. My first candidate is ToxicChat-Het. Verify first:
  - counts of benign, unsafe and safety-aligned examples;
  - which variant contains the safety-aligned distractors;
  - where the unsafe responses came from;
  - the evaluation prompts and licences;
  - that no evaluation prompt nearly duplicates a training prompt.
  - The failure is completions flagged by the scorer on held-out toxic-eliciting prompts.
- **Groups and removal size:** each option removes exactly one predefined group of m examples, so options differ in which data is removed, not how much.
  - Groups are balanced TF-IDF clusters within each stratum (unsafe, distractor, benign), independent of every predictor being compared.
  - m and the number of groups follow the stage-0 data and detectability checks; the target is at least 24 development groups.
  - Menus are K=4 removals plus a0 (no removal), sampled uniformly.
- **Training length:** a fixed number of optimizer steps T (E epochs of the full mixture; E is frozen after a stage-0 recipe check). The seed fixes data order.
  - Removed examples are masked in place. Each batch's loss is divided by a0's response-token count for that batch, so removal deletes terms rather than reweighting the remaining examples.
  - Every full run then costs the same, and arms with the same seed are paired (common random numbers).
  - This defines the counterfactual. It is not the usual practice of reshuffling and repacking the kept data, and how closely the two agree for small removals is unverified. GPT needs to decide this before freezing.
- **Short runs:** the same run stopped at a quarter of the steps (also scored at one-eighth). It is checkpointed so a selector can continue it to full length, paying only the extra steps.
- **Attribution:** one stored pass of compressed per-example gradients over the MLP layers of an a0 model, using LoGra-style Kronecker projection.
  - Primary score: damped block-diagonal empirical-Fisher influence in the projected space. Grad_Sim is a secondary score from the same vectors.
  - Reuse DATE-LM's code only if it runs on MPS within a day of porting.
  - Queries: for F, toxic completions from a0 on the development query prompts (Q_dev); for L, held-out benign responses; for O, a0's refusals on benign Q_dev prompts.
  - Group score is the sum over the group's examples.
- **Scorer:** a frozen local classifier (candidate `unitary/toxic-bert`, pinned) applied to completion text only, with its threshold fixed during development.
  - The same classifier scores training responses for X0. This deliberately strengthens the comparison selector S− (no attribution), but X0 then shares the scorer's errors.
  - O uses an audited refusal-phrase matcher; L is the increase in response-token NLL on held-out benign data.
- **Blind audit (gate G1):** about 200 completions, stratified by prompt type, score bin and arm. They are shuffled with arm and score hidden, and a human labels toxicity and refusal. Acceptance thresholds are set before labelling. Also check whether the model is simply repeating the prompt.
- **No-leakage split, hashed before any run:**
  - Groups go to development or confirmation, randomly within each stratum.
  - Prompts go to Q_dev (attribution queries and short-run scoring, shared by both arms), P_dev (full-run development targets) or P_conf (untouched).
  - Seeds are disjoint across outcome runs, short runs and the a0 models used for attribution.
  - The code refuses confirmation IDs unless a freeze flag is set.
  - The positive control removes only development unsafe groups, so the confirmation groups' combined effect stays hidden.
- **Decoding:** fixed sampling settings, 4 samples per prompt, and the same per-prompt sampling seeds across arms.

## Stage 0 (Oct 2–16): engineering feasibility and measurement

**Limits:** at most about 25 full-run equivalents (FRE: one full run plus its standard evaluation). Recipe checks on a0 only. No confirmation data.

**Code to write now:**
- `data_build`: pin, verify, dedupe, group, split manifest and confirmation guard.
- `train`: masking, fixed steps, checkpoints at the short-run fractions, resume, cost log.
- `evaluate`: generation, scorer, refusal matcher, NLL.
- `attribute`: projected gradients and group scores.
- Audit export/import and tests.

**Runs:**
- a0 with 4 seeds, plus one repeat of the same seed to measure MPS run-to-run variation.
- Development unsafe groups removed, 3 paired seeds.
- Two single-group removals (the group with the most classifier-flagged content, and a benign group), 3 paired seeds each.
- Matching short runs and one attribution pass.
- These runs are reused in stage 1 if the recipe does not change.

**Engineering success (observable):**
1. One command per (option, seed, short/full) writes F, L, O, per-prompt records, wall-clock, tokens, peak memory and hashes.
2. A unit test shows the masked gradient equals the gradient on kept examples only (CPU, float64, tiny model). The same-seed repeat gives the MPS run-to-run tolerance.
3. Attribution AUPRC for unsafe vs. other examples is above the base rate. This is a sanity check only.
4. Costs are measured for a full run, a short run, evaluation, and attribution (one-off).

**Setting checks (these can fail):**
- The paired confidence interval for the positive control's ΔF excludes 0.
- The largest single-group ΔF is distinguishable from seed noise; this sets m.
- The audit passes.
- If a detectable m leaves fewer than 24 development groups, raise it with GPT, because enlarging the unsafe pool changes the design.
- If the positive control fails at both 160m and 410m, this mixture cannot host the study.

## Stage 1 (Oct 16–Nov 6): headroom, screen, indicative replay

**Run pool (smallest meaningful replication):**
- a0: 6 outcome seeds.
- Each development removal: 3 paired outcome seeds, the minimum for per-option noise and leave-one-seed-out residuals.
- Each option including a0: 4 short-run seeds, enough for S− to spend attribution's cost on extra short runs. Add seeds if attribution turns out to cost more than that.
- Attribution: computed from 2 independent a0 models, to capture attribution's own seed variability.

Cost is about 9 + 4G FRE plus two attribution passes, roughly 105 FRE at G=24 (G is the number of development groups). The size is set by budget, not by a power calculation. Build the pool in two halves. After 12 groups, check headroom, and stop only if the prespecified negative rule fires.

**Analyses.** GPT/user freeze the scripts, margins, tau_L and tau_O after stage 0 and before the pool is analysed.
1. **Headroom (gate G2):** regret of the plug-in pick for an X0-only predictor and a classifier-only predictor. Predictions come from models fit without the held-out group (cross-fitting), on K=4 menus resampled over development groups. Bootstrap over groups and seeds, and record menus where a0 is best.
2. **Screen (H1):** the same ridge model, with the same tuning budget, with and without attribution features. The loss is plug-in regret under FOCUS's violation scoring, plus the violation rate.
3. **Matched-cost replay:** S− spends attribution's measured cost on extra short-run seeds, at budgets set from measured costs. Attribution's one-off cost is charged to each decision first, and amortized only as a secondary view. Each replay draws short-run seeds and one attribution model, and replays share one pool, so they are not independent. The selector here is simplified and non-adaptive, so this is indicative, not D_info.
4. **Diagnostics (not gating):** cases where predictors agree but are wrong; residuals between short-run and full-run outcomes.

**Baselines:** classifier-only, attribution-only, short-run-only at matched cost, random pick, always-a0, and exhaustive full runs as a cost reference.

**Nov 6 decision** (using FOCUS's negative/positive/inconclusive rules):
- **No headroom** (upper bound below the margin): since D_info ≤ G(S−), H2 cannot pass here, provided the frozen S− is at least as good as this simple one. Report the result and propose to GPT/user a failure that classifiers miss (option C, with new development data).
- **Headroom present but the screen is negative:** this rules against this attribution method in this setting. Allow at most one prespecified alternative (e.g., EK-FAC), and only if compute exists.
- **Screen positive, or inconclusive with reachable precision:** freeze the design (gate G0), implement the adaptive constrained S, and plan stage 2. This needs compute.
- **Inconclusive and precision not reachable on the Mac:** more groups need compute.

## Decisions that need compute information

- How many hours a day the Mac is available, and whether multi-day background runs are acceptable. This sets G.
- Whether any GPU or cloud spending cap exists. That decides whether 410m or 1b models, G≥32 or EK-FAC are possible. It also decides stage 2, where every confirmatory removal is retrained on unseen seeds for a withheld reference; that is likely beyond the Mac by Dec 11.
- Permission to install torch and transformers in a virtual environment, and to download the DATE-LM data and the classifier.

## Weakest assumption, simpler alternative, counterexample, deciding observation

- **Weakest assumption:** removing natural toxicity groups leaves room to beat X0. FOCUS itself notes that toxicity has strong content classifiers, and DATE-LM already compares attribution against strong classifiers (per the precedent note). On the measurement side, the risk is that 160m does not learn a scorer-valid failure with single-group effects above seed noise; stage 0 tests that.
- **Simpler alternative:** check headroom only, with full runs and the classifier and no attribution or short runs. That is analysis 1. Attribution is cheap enough to build in parallel, but skip H1 if there is no headroom.
- **Counterexample:** if ΔF is proportional to how much classifier-flagged content a group has, the classifier picks the best option every time. Attribution can then be accurate (high AUPRC) and still add zero D_info.
- **Deciding observation:** the upper bound of the cross-fitted X0-only development regret compared with the frozen margin.

## Report

- **Changed files:** none.
- **Commands:** only read/search tool calls on project files, all successful. No shell, network, installs, training or agents.
- **Evidence read:**
  - the four assigned files;
  - `research/review/2026-10-02-new-safety-attribution-precedent.md`;
  - `writing/proposals/roger-grosse-research-proposal.md`;
  - the brief and excerpts from `.ai/HANDOFF.md`.
- **Acceptance criteria:** none tested; this is a design only.
- **Unresolved:**
  - DATE-LM's data composition and whether its code runs on MPS are unverified.
  - Masked versus reshuffled training needs a decision.
  - Margins, tau_L, tau_O and audit thresholds are not set.
  - The adaptive S is unspecified.
  - There is no compute path to confirmation yet.
  - The project venv has no torch, and whether transformers works with the system Python 3.9 is unverified.
