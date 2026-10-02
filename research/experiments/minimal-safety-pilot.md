# Minimal safety calibration: protocol, choices and limits

Status, 2 October 2026: the corrected CUDA calibration completed and the real saved-checkpoint control passed. [Results and verification](2026-10-02-minimal-safety-calibration-results.md). The earlier implementation had47passes/two record-logging failures; these were corrected before launch. The first Mac run then failed at gradient transfer; that failure remains preserved and the platform fix is tested. The original local profile below is retained for provenance; the dated Runpod amendment at the end authorizes the cloud execution actually used.

Engineering calibration only: no H1–H4 or novelty gate in [EDGE_CHECKS.md](../review/EDGE_CHECKS.md) has passed. Code and commands: [README](../../experiments/minimal_safety/README.md).

## Purpose

Show that one real a0/removal slice runs end to end on the Mac and measure what each stage
costs: at both calibration seeds, both arms reach short and long checkpoints, produce
traceable per-prompt classifier-proxy outcomes and a finite gradient cosine, within a 900 s
wall cap and 2 GiB of outputs, or leave partial evidence naming the blocking stage. A zero or
reversed proxy difference is a valid outcome and triggers no recipe search.

## Protocol

- **Inputs, frozen before training.** `DataAttributionEval/Toxicity-Bias-Filtering@ad96bd4…`,
  ToxicChat-Het `train.jsonl` (SHA-256 `dcc91989…`) and `ref.jsonl` (`75351ed4…`), refused on
  mismatch. `Qwen/Qwen2.5-0.5B-Instruct@7ae55760…` and `unitary/toxic-bert@4d6c22e7…` from the
  local cache only (offline, safetensors, no remote code). The run copies config, manifest and
  rows, writes every arm's per-step example IDs, and accepts only the reviewed manifest hash.
- **Data.** Before sampling: exclude empty prompts/responses and chat-template control
  strings; exclude training rows whose normalized prompt (lowercase, collapsed whitespace)
  equals any of the 30 reference prompts or whose `data_id` equals a reference `data_id`; keep
  the first row per normalized prompt within each file. With design seed 20261002, sample 96
  Benign, 16 Safety-Aligned and 16 Unsafe training rows, a disjoint 6-row Benign holdout, and
  split eligible reference rows into 4 query, 6 evaluation and the rest untouched (IDs only;
  their text never reaches the runner). Uids and normalized prompts are asserted disjoint
  across all roles. Every exclusion, duplicate and truncation is counted.
- **Arms.** a0 (all 128 rows) and `remove_pc_unsafe8`: an explicit positive control deleting
  8 of the 16 sampled Unsafe rows, drawn by the design seed before any score or outcome.
- **Training.** Seeds 101 and 202. Per seed one adapter (rank 8, alpha 16, q/v projections,
  dropout 0, `lora_A` from a seeded CPU generator, `lora_B = 0`) is restored bit-identically
  for each arm with a fresh AdamW (lr 2e-4 constant, betas 0.9/0.999, no weight decay, clip
  1.0). Batch 1, fp32, eager attention, MPS, 512-token cap with 128 target positions reserved.
  Loss: per-example mean over response tokens plus end-of-turn. Checkpoints at steps 4 and 16
  of one trajectory; the step-4 evaluation cannot change training (verified on CPU in tests).
- **Evaluation** at steps 4, 16 and once on the base model: greedy, 64 new tokens, 6 toxic
  evaluation prompts and 6 benign holdout prompts. CLASSIFIER PROXY: toxic-bert `toxic`
  sigmoid and its rate at ≥ 0.5 on the toxic prompts. DIAGNOSTICS: reference-response NLL
  (toxic and benign), refusal-phrase flag, empty outputs, length, prompt copying.
- **Gradient cosine** per seed at a0 step 16: cosine between the mean LoRA gradient of the 4
  query rows' provided toxic responses and the mean over the 8 removed rows (response-only
  losses, eval mode). Positive means the group locally supports the query responses.
- **Tokenization.** The template head and user text are encoded together and every frozen
  prompt is checked against the tokenizer's canonical chat-template encoding before training
  (any difference stops the run). The earlier separate encoding gave `train:10158` one token
  too many (354 vs 353; a leading newline). The root preflight measured this, not me, and the
  frozen streams do not sample that row. Prepared data and hashes are unchanged.
- **Costs and caps.** Synchronized per-stage wall times, tokens, memory, versions and hashes.
  Cooperative cap checks run at every stage entry, before each work item (weight load, step,
  token, NLL, classifier batch, gradient, save) and once after the last unit. One operation
  in progress can overrun; the run is then incomplete with the overshoot recorded. No arm is
  shortened. Stopped stages are reported as spent time, not as completed units.
- **Completion.** `complete` requires the runner's own end record without a stop reason, both
  caps, recomputed frozen hashes and every planned unit verified against its evidence (stage,
  record, planned step, file hash, prompt and role sets, initial adapter, trained IDs).
  Comparisons use only pairs where both arms verified at the planned step on the same
  prompts; the summary's conclusion field is fixed text.

## Choices and deviations

- **Removal semantics** follow GPT's adjudication: rows are deleted and kept rows move
  forward (no masking), at fixed steps. Arms share a per-epoch order of the full set, so
  differences come from the removal; at fixed steps the removal arm sees more retained rows.
- **Exposure is small at calibration fidelity.** By step 16, a0 has used 16 of 128 rows; the
  expected number of removal-group rows it has seen is 1. A hypergeometric calculation gives
  about 0.33 per seed that it has seen none by step 16, and about 0.77 by step 4. The frozen
  plan (GPT's preflight) has seed 101 seeing 1/2 removal rows by steps 4/16 (first data
  divergence at step 1) and seed 202 seeing 0/1 (first divergence at step 9). So seed 202's
  arms share data, initial adapter and a fresh optimizer through step 8, and their step-4
  adapters should be bit-identical. The report checks this for every such pair. If they
  differ, the cause must be investigated (an implementation difference, or numerical
  nondeterminism), not assumed to be measured MPS noise. A real contrast needs a longer,
  separately frozen development profile (proposed, not launched; see next steps). I did not
  pick seeds or reorder data to force exposure.
- **Enrichment.** Raw training data are 98.40% Benign, 0.65% Safety-Aligned and 0.95% Unsafe;
  the calibration set is 75%, 12.5% and 12.5% (about 13× Unsafe and 19× Safety-Aligned). The
  manifest records the exact figures.
- **Stricter than asked.** Dedupe is by normalized prompt, not by (prompt, response) pair.
  `data_id` overlap with reference rows is excluded conservatively; if IDs turn out to be
  per-file row numbers, this over-excludes harmlessly (counted). Control-string rows are excluded.
- **Added diagnostics.** The reference-response NLL and the single base evaluation (run last,
  so it never takes time from an arm) are cheap context for reading a null proxy; they are
  not endpoints.
- **Fixed priors, not tuned.** lr 2e-4, clip 1.0, 512/128 token budget, 64 new tokens, the 0.5
  threshold and the refusal patterns. None is selected on outcomes.
- **Not done.** No masked fixed-denominator training, projections, Fisher/Hessian or
  LESS/SOURCE; no AUPRC or predictive-accuracy claim; no paid APIs or cloud.

## Analysis limits

Two seeds, six toxic prompts and greedy decoding support descriptions, not inference: no
p-value, power, headroom, positive-control or H1/H2 claim. Sixteen batch-1 steps are a timing
and plumbing fidelity, not converged fine-tuning. toxic-bert is an unvalidated proxy here and
the blind audit is pending (a person, before opening the mapping, with thresholds fixed first).
The cosine shares its seed's a0 model with the outcomes it sits beside: a correlated
development feature, not an out-of-seed predictor. Type labels set composition and the
positive control only, never a predictor. A negative here does not show that the mixture
cannot host the study.

## What would change the plan

- Measured cost: if one 16-step arm with both evaluations takes more than about a quarter of the
  cap, local development at useful scale needs fewer prompts or tokens per evaluation, or
  compute.
- Floor or ceiling: if base and a0 completions are almost never, or almost always, flagged on
  the evaluation prompts, the thresholded rate cannot show a change on these prompts. This
  does not show that removal cannot affect behaviour: continuous scores and reference NLLs
  can still move under a flat rate. Read those, then change the prompts or endpoint before
  groups are built.
- Nondeterminism: if data-identical arms (seed 202 through step 8) end with different
  adapters, first look for an implementation difference between the arms. If none, treat it
  as numerical nondeterminism: paired comparisons then need CPU or deterministic settings, or
  same-seed repeats, and their cost should be measured first.
- Audit: if blind labels disagree often with toxic-bert, repair measurement (G1) first.

## Next steps (estimates depend on the measurements; none is a promise)

Only step 1 is authorized. Steps 2 and 3 are **proposed, unlaunched profiles**. Each needs its
own frozen design and GPT/user approval. Before any H1 study, measurement validity (the blind
audit against toxic-bert) and the practical margins must be fixed. This calibration alone
authorizes none of these runs.

1. **By 6 October: execute and read the calibration.** GPT runs the tests and the
   calibration. Record the complete or blocking stage, `seconds_per_step` (c_step, from warm
   per-step medians), evaluation seconds for 12 prompts (c_eval), attribution seconds per seed
   (c_grad per example), load time, memory, exposure, adapter identity of data-identical pairs,
   identical-completion counts, the proxy floor or ceiling, and the continuous scores and NLLs.
   A person labels the blind export. Cost: one run of at most 900 s, plus about 1 hour of
   audit.
2. **6–16 October (proposed, unlaunched): measurement-only development profile, frozen before
   running.** Choose the training length T and mixture from the measured c_step, for example
   at least one full epoch so every removal is exposed. Train a0 and the same positive control
   at the same 3 seeds: 3 + 3 = 6 runs, each evaluated at a short and a long checkpoint, so
   cost ≈ 6 × (T·c_step + 2·c_eval). If step 1 shows data-identical arms with differing
   adapters that no implementation difference explains, add one same-seed a0 repeat per seed
   to measure run-to-run variation: 9 runs, ≈ 9 × (T·c_step + 2·c_eval). This is still
   development, not a powered test.
3. **16 October–6 November (proposed, unlaunched): bounded development decision.** Proceed
   only if step 2 shows a positive-control difference beyond seed noise at affordable T, and
   the audit supports the measurement. Then build 12 groups (target 24) without any compared
   predictor and estimate X0-only headroom (G2) before any attribution screen (H1). The screen
   uses the same selector with and without attribution, with S− reinvesting attribution's
   measured cost. Cost ≈ S·(1+G)·(T·c_step + c_eval) + S·G·m·c_grad, with m rows per group
   and c_grad the measured per-example gradient time. If step 2 is negative or this exceeds
   local means, record that and return the compute-or-redesign decision to GPT and the user;
   a negative here does not end the project. The ICML 2027 date is unverified and sets no
   step here.

## Authorized platform amendment — 2026-10-02

The user subsequently requested Runpod and explicitly set a $10 total cloud-spend limit. This supersedes the original local-only/no-paid-compute restriction for this calibration alone. The MPS run failed after101.88s at gradient transfer; its incomplete artifacts remain preserved. All arms and both seeds will run freshly on one NVIDIA RTX A5000 with explicit calibration-cuda.json, same pinned model/scorer, same prepared data, fp32/eager, LoRA,4/16steps and900s scientific process cap. No local/GPU mixed comparison. Linux Python3.12.3 replaces local3.11.15; torch2.8.0+cu128 and pinned scientific libraries, four CPU threads, TF32 disabled and strict determinism are recorded. GPU rental, setup, dependency retry, download, tests, idle and cleanup time all count toward the same allowance; stage timing alone is not billing cost. The first GPU pass remains engineering calibration, not an H1/H2/H3 test or a safety/novelty finding.
