I made no edits and ran no commands; this was read-only. It's a design proposal, not evidence: every throughput figure below is a planning assumption until it's measured on the pod.

## 1. Recommendation

Use **"bank and replay"**:

- **Corpora.** Build one development corpus and one held-out test corpus from separate rows, with separate prompts and seeds. Each holds about 1,050 training rows and a bank of 16 predefined removal groups. The groups are generated before any outcome exists.
- **Retraining.** Retrain every bank removal (plus keeping all data, a0) for 3 full epochs, with matched data order between a removal and a0. The runs are split into seeds the selectors may see and sealed reference seeds they never see.
- **Replay.** Run the existing-style selector with and without attribution offline, at matched total cost, over every 5-group menu drawn from the bank.
- **Two changes are mandatory, not optional.**
  - Batched generation: at the pilot's batch-1 speed, generations alone would take about 26 h at 64 tokens.
  - A safety judge that sees both prompt and response, as the primary scorer. Toxic-BERT measures toxic language, not unsafe compliance.
- **Cost.** About 17 GPU-hours, roughly $5 cumulative; about $7.5 in the pessimistic case, with a hard stop at $8.50.
- **Claims.** Expect at most one held-out "feasibility in this setting" estimate of attribution's decision value (`D_info`). The H1 development screen will probably be inconclusive (16 groups).

## 2. Three ways to do the work, costed from the pilot

Pilot unit rates:
- 0.136 s per batch-1 training step (8.73 s / 64)
- 1.98 s per completion of at most 64 tokens (214.21 s / 108)
- 0.122 s per example gradient (2.93 s / 24)

| | A. Bank and replay (chosen) | B. Live executions on independent corpora | C. Full DATE-LM 10k corpus |
|---|---|---|---|
| Shape | 2 corpora × 16 groups; every removal retrained; selectors replayed offline | 8 corpora (4 dev, 4 test), 4 removals plus a0 each; selectors actually train what they choose | Native 10,163-row mixture, about 8 groups, 2 seeds |
| Training work | about 160 runs × about 3,150 rows ≈ 500k row-steps: **11 h** batched (0.08 s/row assumed), **19 h** at the pilot's 0.136 | about 264 full-run equivalents: **22 h** planned, over 35 h pessimistic | 18 runs × 2 epochs × 10k rows: 8 h batched, 14 h at pilot rate |
| Generation | about 52k completions: 1.5–3 h batched; **about 79 h** at pilot batch-1 rate with 192 tokens | similar per run | small |
| Strength | Many decision instances; selector randomness replicated by seed blocks; sealed reference | Truly independent menus; real costs, no replay assumptions | Directly comparable with DATE-LM |
| Fatal weakness | Only one test bank, so no claim beyond it | Over budget, and only about 3 executions per arm per corpus, so the regret error would be larger than any sensible margin | No selector run pool, no held-out bank, so steps 3–4 can't be done at matched cost |

## 3. Chosen design

### 3.1 What is measured
- **Options.** Each menu has a0 plus 5 removals from one bank; a0 can always be picked and always counts as feasible.
- **Training per option.** Qwen2.5-0.5B-Instruct (pinned), the recipe in 3.2, 3 epochs on the corpus minus the removed group.
- **F(a): failure rate.** Averaged over seeds and a fixed reference prompt set, the share of greedy completions to toxic prompts that a frozen judge J labels *Unsafe*.
  - **Flag for GPT:** "toxic completion" would then mean unsafe compliance, not toxic language. FOCUS lists the scorer as unresolved, so record this explicitly. Toxic-BERT stays as a secondary endpoint.
- **L(a): utility loss.** Change in teacher-forced loss (mean per-token NLL) on held-out benign reference responses, compared with a0. Feasible if L ≤ τ_L, where τ_L = 0.25 × the benign-loss gain that fine-tuning gives over the base model, measured in calibration.
- **O(a): over-refusal.** Change in the judge's refusal rate on benign and borderline-benign prompts, compared with a0. Feasible if O ≤ 0.05.
- **Confirmatory target:** `D_info(B*) = mean[loss(S−) − loss(S+)]` over all frozen test menus, all selector seed blocks and tie-break executions, scored against the sealed reference.
  - An infeasible pick scores F(a0) and counts as a violation. The best feasible option's F cancels out of `D_info`.
  - Secondary measures: violation rate V for each arm, the attribution-free selector's regret G(S−), and `D_info` at a low and a high budget.

### 3.2 Model, data and training policy
- **Training recipe.**
  - LoRA rank 16, α 32, on all attention and MLP projections, dropout 0.
  - AdamW at 2e-4 with 3% warmup then cosine decay; batch 8; fp32 without TF32, deterministic.
  - Response-only, per-example mean loss; 512-token sequences.
- **Fixed epochs (E = 3).** Each epoch shuffles the full corpus by (seed, epoch) and drops removed rows, as in the pilot. Every kept row is seen exactly 3 times, compared with the pilot where the removed rows were seen once or twice in total. Removing rows shortens the run, so a size effect is part of the removal effect; the size feature captures it.
- **Short fidelity.** The epoch-1 checkpoint of the same run (a prefix of it), so a "continuation" costs the remaining 2 epochs.
- **Pools available.** Eligible rows are Benign 9,999, Unsafe 83 and Safety-Aligned 66; the reference file has 30 rows.
  - Split them: dev gets 41 Unsafe and 33 Safety-Aligned, test gets 42 and 33; Benign pools are separate.
  - The mixture is enriched to about 4% Unsafe, against about 1% in the raw data; report this.
- **Why this model and data are adequate, with limits.** The model is the existing pinned asset and is cheap enough for about 160 runs. Results don't transfer to larger models. If calibration finds a floor or ceiling, stop (see 3.10) rather than switch models within this budget.

### 3.3 Groups, menus and splits (generated from frozen seeds before any outcome)
- **Corpus.**
  - Background (never removable): about 436 Benign, 8 Unsafe and 6 Safety-Aligned rows. This is redundant harmful support outside the menu.
  - Bank: 16 groups. Each size is drawn from {16, 32, 64}. Bank Unsafe and Safety-Aligned rows are spread across groups by Dirichlet(0.5) weights; Benign rows fill the rest.
  - Dataset type labels are used for **construction only** and never as features. A feature whitelist is asserted in code.
- **Menus.** All C(16,5) = 4,368 five-group subsets. They share runs, so they are averaged as a finite set and **never treated as independent replicates**.

| Element | Dev | Test (untouched until the design is frozen) |
|---|---|---|
| Groups and rows | Dev pools | Disjoint test pools |
| Seeds | 3 "worlds" (all also scored on reference prompts; for dev analyses, truth for world w comes from the other 2 seeds) | 3 seeds selectors may use plus **3 sealed reference seeds**, all new |
| Toxic prompts: selection / reference | 80 / 200 | 80 / 200, disjoint from dev |
| Refusal prompts (half borderline, half generic benign): selection / reference | 60 / 120 | 60 / 120 |
| Utility loss rows: selection / reference | 100 / 200 | 100 / 200 |

- **Prompt sources.**
  - Toxic prompts come from a pinned public ToxicChat release. They are deduplicated, exact and near-duplicate, against every DATE-LM row, and prompts over 384 tokens are dropped and counted, so no prompt is silently truncated.
  - Borderline prompts come from a pinned XSTest-safe or OR-Bench-hard copy.
  - Fallback if a source is unavailable: unsafe prompts from other subsets of the same pinned DATE-LM repository, or generic benign prompts only, with O reported as insensitive.
  - Shrinking rule if supply is short: reference sets no smaller than 150, selection sets no smaller than 60.

### 3.4 Measurement and audit
- **Judge J.** Qwen3Guard-Gen-4B (pinned) on (prompt as the model received it, full completion), giving *Unsafe* and *Refusal* labels plus label-token probabilities. Toxic-BERT and the refusal regex are kept as diagnostics. Completions are generated first and judged in bulk afterwards, so they can be re-judged later.
  - **Unverified from this workspace:** the license, open access, revision and output format. Check them at setup.
  - Fallback judges: Granite Guardian, or Llama Guard only if access is already authorized. No paid APIs.
- **Same judge for the classifier features.** J also scores every training row for the attribution-free features. This is the strongest construct-matched content screen, and the shared bias favours S− (the baseline), so it is conservative.
- **Length cap: the pilot's prefix problem.** 77 of 108 pilot completions hit the 64-token cap, and 4 prompts were truncated.
  - Start the cap at 192 tokens.
  - Regenerate 100 a0 and base completions at twice the cap. Keep the cap if judge labels agree in at least 95% of cases and no more than 20% of completions hit it; otherwise move to 384.
  - Mark completions that hit the cap, and show auditors exactly the text the judge saw.
- **Blind audit (gate G1).** Draw a stratified sample of about 240 dev items, oversampling cases where the judges disagree, with recorded sampling weights. Hide arm, seed and scores; show the exact model-visible prompt.
  - Pass thresholds, fixed before labelling: sensitivity at least 0.80, specificity at least 0.90, refusal κ at least 0.7.
  - Execution need not wait for the labels. GPT may make a pass labelled **model-assisted**; a human packet is exported for the user after execution.
  - Until a human audit passes, every F claim is worded as "judge-assessed". If it fails, F conclusions are downgraded to proxy-only.

### 3.5 Attribution method
- **The pilot cosine is not suitable as the primary method.**
  - It is scale-free, while removal effects grow with group size.
  - It uses only the final checkpoint and ignores Adam.
  - Its queries are the benchmark's reference responses, not the model's own failures.
  - It has only a safety direction, nothing for utility or refusal.
  - Keep it as a diagnostic only.
- **Primary method (an existing LESS/TracIn-style method).** For each candidate row, sum over the 3 epoch-end checkpoints of the deployed a0: LR × ⟨mean query gradient, Adam-preconditioned row gradient⟩. Sum these over the group, giving the first-order predicted change in query loss if the group is removed.
  - There are three query directions:
    - Failure: the deployed a0's own judge-flagged unsafe completions on **selection** prompts.
    - Utility: benign selection reference responses.
    - Refusal: borderline selection prompts paired with a fixed refusal text.
  - Attribution uses only the a0 checkpoints and optimizer moments of seeds selectors may see.
- **Excluded from confirmation:**
  - SOURCE and EK-FAC: the effort and dependency risk are too high for this pass.
  - DataInf: avoided to prevent shopping for a method.
  - DRA: unverified here, and it does the classifier's job. Record this as a scope limit, per the DRA baseline check.

### 3.6 Selector, matching and baselines
- **S (the same for both arms).** A generic constrained multi-fidelity selector built from standard parts: prior-guided successive halving with Gaussian fusion.
  - **Prior.** Ridge regression predicts the full-run changes in F, L and O from features. Predictions are out-of-fold by group in dev and trained on all dev data for test. The prior's spread is the out-of-fold residual.
  - **Short-run observation.** Modelled as a + b × (true full-run change) + noise; a, b and the noise level are fitted on dev and shared by both arms. Each observation is paired with the deployed a0 on the same seed.
  - **Allocation.** Short-run the options with the best prior among those likely feasible, then continue the best by posterior to full training.
  - **Pick.** The best posterior change in F among options with P(feasible) ≥ p_feas; otherwise a0.
  - **Final training.** Keep the cost of training the final pick in reserve unless that option is already fully trained.
- **Features.**
  - Without attribution (X0): log size; judge Σ P(unsafe); judge count with P(unsafe) ≥ 0.5; judge refusal count; Toxic-BERT Σ.
  - With attribution: X0 plus the 3 attribution sums, standardized within the bank.
- **Matched tuning.** Both arms get an identical 64-setting grid (ridge λ, prior inflation, p_feas, split between screening and continuation, pick threshold). Each arm is tuned separately with the same procedure on dev replay at B*.
- **Auxiliary baselines** (replay only, no extra GPU time):
  - Rank by judge, then confirm the top options with full runs.
  - Rank by attribution, then confirm the top options with full runs.
  - A flat-prior selector.
  - Exhaustive single-seed retraining.

### 3.7 Costs and budgets
- **Shared by both arms (reported, not part of the budget gap).** a0's training and evaluation (the deployed model), judge scoring of the menu's rows, setup.
- **Charged within the budget.**
  - Attribution, for the attribution arm only: the menu's rows × 3 checkpoints, plus the query gradients.
  - Short runs: 1 epoch plus a selection evaluation, about 0.4 of a full run.
  - Continuations: about 0.7 of a full run.
  - Final training and one evaluation.
- **Prerequisite sensitivity.** Repeat the comparison with attribution also paying for one full a0 retraining, as if its checkpoints had not been saved.
- **Budgets.**
  - **B\*** = 5 short runs + final training ≈ 3 full runs. It is defined without reference to attribution and frozen before outcomes. At B\*, attribution costs about 0.5 of a full run, so the attribution-free arm can short-run all 5 options while the attribution arm can afford about 3.
  - Low = 2 short runs + final; high = 5 short runs + 2 continuations + final.
- **Rounding check.** Report each arm's unused budget. Also run a sensitivity where the attribution-free arm is allowed to round up one extra short run.

### 3.8 Keeping the reference out of the replay
- The replay reads only features and outcomes from the seeds selectors may see. Its picks are written and hashed before a separate scorer opens the sealed reference file.
- Selection prompts and reference prompts are disjoint, and so are the two sets of seeds. This is asserted in code.
- Priors, the short-run model and hyperparameters come from dev only.
- The test bank is generated at the start, but no test unit runs until the frozen-design hash exists.

### 3.9 Replication, intervals and decision rules
- **What counts as a replicate.**
  - Training seeds replicate F, L and O; options are paired within a seed.
  - Prompts are a crossed effect, not training replicates.
  - Selector seed blocks replicate the information the selector had (deployed a0, its matched runs, its attribution).
  - Menus and executions are averaged, not counted as samples.
  - Bank-level n = 1.
- **Interval.** A two-level bootstrap: reference seed blocks × prompts for the truth, crossed with the 3 selector seed blocks. Three blocks is a crude interval, so also report each block's `D_info` and whether the signs agree.
- **Decision rule (90% interval, margin 2 points of unsafe rate).** Positive if the lower bound is above 2 points; negative if the upper bound is below 2 points; otherwise inconclusive.
  - Feasibility: V ≤ 10% for each arm, and the attribution arm's violation rate exceeds the baseline's by at most 5 points (upper bound).
  - Near-ties and borderline feasibility are reported both ways.
- **Precision check before freezing.** Project the test interval width from dev variance components. If it is wider than 4 points, the frozen design must state "likely inconclusive".

### 3.10 Phases, freezing and stop rules
1. **Setup.** Tests and asset checks. Throughput microbenchmarks. Determinism: rerunning one epoch and one evaluation must give bitwise-identical adapters and completions. Then pick the scale level from a frozen table: nominal size; then N = 800; then 12 groups; then stop and report.
2. **Measurement calibration (step 1)**, on the dev corpus:
   - **Runs.** Base model; a0; remove all bank Unsafe rows; remove all Unsafe rows. Two seeds each; the a0 runs are reused later.
   - **Judge, cap and τ_L.** Settle the judge, length cap and τ_L.
   - **Positive-control gate.**
     - If removing all bank Unsafe rows lowers F by at least 10 points on both seeds, proceed.
     - Otherwise, if removing *all* Unsafe rows does, set the background to 0 Unsafe and rebuild.
     - Otherwise, try once with E = 5.
     - If that also fails, **stop**. Also stop if base F ≥ 0.6 (ceiling) or the judge fails to parse more than 1% of items.
3. **Development (steps 2–3).**
   - Run the dev bank and its attribution.
   - Headroom: G(S−) with its interval.
   - H1 screen: plug-in regret and feasibility errors with and without attribution.
   - Tuning.
   - The redundancy diagnostic: remove A, B, and A∪B.
   - **Freeze (G0):** record the hash of the code, configuration, budgets, margins and test seeds.
4. **Test (step 4).** Run the test bank, attribution and replay; then unseal the reference and score. Report every menu, including those where keeping all data (a0) is best.
- **What runs regardless.** If the development stage shows no headroom, the test still runs, as the user authorized. Its claim is declared beforehand as a replication of headroom on fresh data. Only a measurement or setting failure stops the work before the test.
- **Budget rules.** Track a meter of pod uptime × rate plus disk. Stop launching new work at a projected $8.50. Download artifacts at the end of each phase. Use on-demand A5000 GPUs only, and never mix GPU types.

## 4. Choices calibration settles (no user approval needed)
These can be settled in setup and calibration without the user:
- the length cap
- 4B or 0.6B judge (keep the 0.6B if it agrees with the 4B on at least 95% of items)
- background Unsafe dose and E
- τ_L
- generation batch size
- the N, G and seeds scale level
- the test split between prompts and seeds that minimizes projected interval width, chosen from a frozen short list

None of these may use removal outcomes, except the frozen positive-control and dose rules.

## 5. Minimal modules
Proposed as a new package, `experiments/edit_selection/`:

| File | Role |
|---|---|
| reused `data.py`, `text.py`, `ledger.py`, `common.py`, parts of `model.py` | hashing, deduplication, encoding, timing, LoRA vector |
| `pools.py` (stdlib only) | disjoint row and prompt pools, near-duplicate checks, manifest |
| `banks.py` (stdlib only) | frozen group and menu generator; never reads scores |
| `train.py` | batched LoRA training, matched data order, epoch checkpoints and optimizer moments |
| `generate.py` | deterministic left-padded batched greedy generation; batched utility loss |
| `judge.py` | judge, Toxic-BERT and regex; bulk scoring and parsing |
| `attribution.py` | Adam-preconditioned group sums, 3 directions; pilot cosine as a diagnostic |
| `jobs.py` | idempotent units, verification, budget meter |
| `replay.py`, `analysis.py`, `audit.py` | selectors and baselines; screen, headroom, `D_info` bootstrap, costs; blind export |

Remove these limits: `MAX_TRAIN_EXAMPLES = 128`, the fixed two arms, batch 1, decoding one prompt at a time with a cap check per token, the CPU-only scorer rule, the 900 s cap (replace with per-phase dollar caps) and the fixed attribution settings.

## 6. Critical failures, counterexample and the check that settles each
- **Null by construction (main risk).** Example: groups A and B each hold 8 Unsafe rows and the background holds 8 more. If 8 rows already saturate F, removing A leaves the behaviour fully relearned. First-order additive attribution and the guard counts would both still favour A, so they agree and are both wrong. Every regret is then about 0 and `D_info` ≈ 0 whatever attribution knows.
  - **Settled by:** the calibration positive-control and dose gate (6 runs, about 30 min, about $0.14). The A, B, A∪B diagnostic then measures the additivity error.
- **Mismatched scorer.** Toxic-BERT flagged only 1 of 8 Unsafe training rows, and every pilot evaluation flagged the same 1 of 6 prompts.
  - **Settled by:** comparing the change in Toxic-BERT's rate with the change in the judge's rate between a0 and remove-all-Unsafe, plus the audit.
- **Leakage gives a false positive.** For example, attribution computed on a reference seed's a0 would share that seed's noise with the truth.
  - **Settled by:** seed and prompt disjointness checks and the sealed-hash order.
- **Budget rounding gives a false positive.** The attribution-free arm's saved budget may be too small to buy a whole run.
  - **Settled by:** reporting unused budget and the rounding-up sensitivity.
- **Nondeterminism, or slower-than-planned throughput.**
  - **Settled by:** the setup checks and the scale table.

## 7. What one test can and cannot claim
- **If positive:** "In this setting, on one held-out bank with fresh seeds and prompts, adding this attribution to this selector lowered judge-assessed regret at B\* by X, with violation rate Y." That is a feasibility finding.
- **If negative or inconclusive:** it constrains this method, selector and setting only.
- **Never claimed:**
  - transfer to other banks, corpora, models or scorers
  - human-validated safety, unless the audit passes
  - superiority over DRA or SOURCE
  - an allocator contribution or novelty, or any ICML judgement
  - guarantees for individual trained models
- **Status of the other hypotheses.** H1 is expected to be inconclusive (16 dev groups); H4 is exploratory.

## 8. Decisions for you or the user, and open concerns
1. Should the primary endpoint be judge-assessed unsafe compliance, with Toxic-BERT secondary? I recommend yes.
2. Using new public assets: the judge, ToxicChat prompts and XSTest or OR-Bench. Their access and licensing are unverified from here.
3. The margins (2 points, V ≤ 10%, 5-point non-inferiority) are my choices, not derived from evidence.
4. Should the test run even if the development stage shows no headroom? I recommend yes, at about $2.
5. The human audit happens after execution, so G1 stays unmet until then.
6. With one test bank there is no interval across banks. A higher budget would best buy a second test corpus, but it would have to reuse the 42 test Unsafe rows, so it would be only partly independent.

## 9. Report
- **Changed files:** none.
- **Commands run:** none; file reads only. I did not open `blind-context.jsonl` or any audit files.
- **Evidence read:**
  - `research/FOCUS.md`
  - `research/review/EDGE_CHECKS.md`
  - `research/review/2026-10-02-dra-baseline-check.md`
  - `research/review/2026-10-02-new-safety-attribution-precedent.md`
  - `research/review/2026-10-02-proposal-novelty-rigor-and-reading.md`
  - `research/experiments/minimal-safety-pilot.md`
  - `research/experiments/2026-10-02-minimal-safety-calibration-results.md`
  - `.ai/inputs/study-v2-20261002/pilot-report.md`
  - `.ai/inputs/study-v2-20261002/pilot-verification.json`
  - `experiments/minimal_safety/{README.md,data.py,model.py,run.py,text.py,plan.py,report.py,configs/calibration-cuda.json}`
  - `tmp/runpod-pilot-20261002/retrieved/run-cuda-001/frozen/manifest.json`, for the pool counts
- **Acceptance:** this is a design deliverable; nothing was tested.
