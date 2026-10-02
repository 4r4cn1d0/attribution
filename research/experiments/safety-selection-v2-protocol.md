# Expanded safety-selection study: stage-A engine protocol (draft)

Status, 2 October 2026: draft describing the implemented engine (`experiments/safety_selection/`). Its author has run nothing on real data or hardware. The lead ran the first implementation's CPU suite (110 passed; `.ai/inputs/study-v2-20261002/engine-first-tests.json`) and a real-source preparation check after the source amendment below. The revision described here (stage-A fixes) has not been run by its author, and every CPU test uses engineering fixtures. No endpoint, selector, held-out analysis, margin or claim is defined or computed here; stage B consumes these interfaces after development calibration, in a sibling package with its own code identity. Gates: [EDGE_CHECKS.md](../review/EDGE_CHECKS.md) (G0–G6 and N untested). Lead decisions implemented: `.ai/inputs/study-v2-20261002/design-updates-20261002.md`, `stage-b-decision-notes.md`, the stage-A brief and the stage-A fixes brief.

## Scope

The engine:

- prepares a deterministic, leakage-checked study corpus and prompt banks;
- trains resumable LoRA trajectories through several checkpoints;
- evaluates checkpoints with:
  - a forward-only query loss;
  - exact full-text generation;
  - a pinned guard;
  - ARC-Easy forced choice;
- scores training rows with the guard (hard labels and normalized label-sequence scores);
- computes two named checkpoint-gradient attribution variants on a0 trajectories;
- exports a whitelisted selector view;
- records every artifact, with receipts for every dependency.

It allows arbitrary positive config sizes, subject to the asset/shape audits. It refuses rather than repairs:

- missing assets;
- hash mismatches;
- changed eligible counts;
- over-limit sequences;
- hidden-bank access from ordinary jobs;
- malformed records;
- non-finite values;
- unverified dependencies.

## Data (prepared once, before any outcome)

- **Sources, hash-pinned and unchanged by the amendment.**
  - DATE-LM ToxicChat-Het `train.jsonl`/`ref.jsonl` at `ad96bd4…`.
  - ToxicChat 0124 test CSV at `29df8e4…` (`3c2e4988…`).
  - ARC-Easy validation/test JSONL conversions (`9ce7382b…`, `8c57b58a…`) of the parquet files at `210d026…`.
- **DATE-LM eligibility** follows the minimal-safety rules:
  - drop empty prompts/responses and chat control strings;
  - drop training rows whose normalized prompt or `data_id` equals ANY reference row's;
  - keep the first row per normalized prompt.

  Asserted counts: risk 83, aligned 66, benign 9999; 30 reference rows. Any difference refuses preparation.
- **ToxicChat** eligibility:
  - drop empty/control-string prompts;
  - drop any prompt equal (normalized) to ANY original DATE-LM train/ref prompt;
  - drop any `conv_id` equal to, or (≥16 characters) contained in, a DATE-LM `data_id`;
  - de-duplicate by `conv_id`, then by normalized prompt.

  Asserted: **295 toxicity-labelled and 4597 non-toxic prompts** (see the amendment log). `model_output` is never read into outputs; `toxicity` only selects the risky pool.
- **ARC-Easy**:
  - strict schema;
  - drop items with control strings;
  - drop any item whose normalized bare question OR either rendered model input (generation: question and labelled options; forced choice: the same plus the answer instruction) equals any original DATE-LM or ToxicChat prompt;
  - de-duplicate by normalized id, then normalized question, across validation then test.

  Asserted: **570 validation, 2371 test** (5 test questions duplicate an earlier question).
- **Disjointness of emitted inputs.** Every training prompt, query prompt, safety prompt and ARC item is disjoint from every other row or item. An ARC item contributes its bare question and both renderings, whichever one it emits. Any shared normalized form is refused as leakage. A source-only audit found no rendered ARC collision with DATE-LM prompts in the pinned sources (`public-metadata/rendered-overlap-audit.json`). Collisions with ToxicChat prompts were not part of that audit, but the asserted counts would refuse preparation if any existed.
- **Corpus**: all eligible training rows, full text. Ids are opaque (`r-…`, `q-…`, `p-…`, `g-…`) and pseudo-random per source position.
- **Removal groups**:
  - Per hidden role, one seeded shuffle of the eligible pool gives disjoint development and held-out member pools.
  - The eight prior pilot removals are forced into development.
  - Unused rows stay ordinary training rows.
  - Within each partition, the 12-group composition table (`(8,2,0,6) … (64,0,0,64)`; 40/33/287 per partition) is filled in a seeded random order.
  - Group ids are seeded random values; tie ranks are a separate seeded permutation.
  - A composition that does not fit refuses.
  - Seed streams are named by role (`risk`, `aligned`, `benign`), so renaming type labels or `data_id`s changes no engine- or selector-facing byte (tested).
  - The design seed is the intentional preset 20261002, fixed before any outcome.
- **Banks**:
  - Safety prompts: **72 development / 80 selector / 143 hidden**, i.e. all 295 eligible toxicity-labelled prompts.
  - ARC: validation supplies disjoint development and selector subsets (64 generation + 128 forced choice each); test supplies the hidden subset.
  - These are initial calibration sizes; final precision planning decides whether more ARC questions are used.
- **Token audit** with the pinned Qwen2.5-1.5B-Instruct tokenizer:
  - training/query rows ≤ 3072 tokens;
  - prompts ≤ 1536 tokens;
  - every forced-choice label encoded separately must equal its canonical joint encoding.

  Any violation refuses (nothing is truncated). Per-row token counts and id digests are frozen; runs re-encode and must match exactly.
- **Audiences**:
  - `engine/` and `banks/{dev,selector}.jsonl`: ordinary jobs.
  - `selector/x0_static.json`: size, coarse provenance counts, character/token summaries, tie rank.
  - `hidden/hidden.jsonl`: reference jobs only.
  - `auditor/construction.json`: uids, `data_id`, type, construction order and composition; read by no job.
  - The manifest hashes every file and is ENGINE scope (see "Selector input boundary").

### Amendment log (all before any expanded outcome; recorded in the data config's `amendments`)

1. **ToxicChat counts.** The first preset asserted 302 toxicity-labelled / 4721 non-toxic prompts from an overlap-only metadata inspection that omitted within-test duplicate prompts. Strict preparation under the exact engine rules, with the pinned sources unchanged, gives 295 / 4597:
   - 60 prompts are excluded for equalling an original DATE-LM prompt;
   - 7 toxicity-labelled and 124 non-toxic within-test duplicates are dropped.

   The safety banks are amended explicitly from 72/80/150 to 72/80/143. Nothing shrinks at run time; any other count still refuses (`public-metadata/toxic-chat-strict-eligibility.json`, `real-preparation-check.json`).
2. **ARC counts** are now asserted (570 / 2371).
3. **Rendered ARC overlap** checks were added (preventive; no current collision with DATE-LM prompts).
4. **The development seed namespace** widens from 1101–1104 (an accidental four-seed execution restriction) to 1101–2099; selector 2101–8999 and reference 9101–9999 are unchanged and disjoint.
5. **Design seed 20261002** is the intentional preset. The lead's engineering check used a temporary seed and name; no seed responds to outcomes.

## Training recipe (initial calibration recipe; fields frozen before confirmation)

- **Model:** Qwen/Qwen2.5-1.5B-Instruct@989aa79…, frozen bfloat16 base weights and float32 LoRA (rank 8, alpha 16, q_proj/v_proj, dropout 0; 1,089,536 trainable parameters, checked).
- **Execution:**
  - eager attention on one CUDA device;
  - deterministic algorithms, refused if unavailable;
  - TF32 off;
  - bfloat16 reduced-precision reductions off (see "Numerical settings").
- **Optimizer:** AdamW, lr 2e-4, betas 0.9/0.999, eps 1e-8, no weight decay, constant schedule, clip 1.0; micro-batch 4 × accumulation 2.
- **Loss:**
  - Per example: the mean NLL over response tokens plus end-of-turn.
  - Per step: the mean over the ACTUAL examples. Micro-batches backpropagate `sum/E`, so a partial final step is weighted correctly.
  - Response tokens are encoded separately after the assistant header, the boundary generation sees. Rows whose separate and joint encodings differ are counted.
- **Gradient checkpointing** is an explicit recipe flag, off by default; nothing changes automatically.

**Stream.**

- Per (seed, epoch): shuffle the full sorted corpus, then drop removed rows.
- Steps take consecutive examples within one epoch.
- Arms of a seed share the order and the seeded initial adapter.
- Each retained row is trained once per epoch.
- Removal shortens epochs and total steps; this is part of the intervention.
- **Checkpoints** `q` (¼ epoch), `e1` and `e3`: the first optimizer boundary covering the fraction (actual examples recorded); `init` is step 0.

**Continuation.**

- A run targets one checkpoint and saves every checkpoint it crosses: the adapter; AdamW `exp_avg`/`exp_avg_sq`/`step` and hyperparameters; CPU/CUDA/Python RNG states; stream identity and position; and the cumulative train-stage cost.
- A continuation restores all of these, with fingerprints checked, only from a complete run of the same trajectory with identical data, recipe and code.
- The source's own files and whole dependency chain must verify, and its receipt is written before any work.
- A continuation charges only its own steps.
- A test checks that a continued trajectory equals direct training bit for bit (adapter, optimizer, RNG) with interleaved evaluation. On CUDA this must be re-checked on the real model with identical batch shapes and settings.

## Evaluation of a checkpoint

- **Query loss (first, forward only):**
  - The training loss of each of the 30 supplied DATE-LM reference query rows: mean response + end-of-turn NLL, the exact training convention, full text, one row per forward pass, eval mode, no gradient.
  - Saved per query (id, input/target tokens, token digest, loss) with the mean and the query-bank hash, in its own charged stage.
  - It needs no hidden bank and changes no weight, optimizer state or RNG (checked).
  - It is a target-likelihood proxy, not measured safety. Stage B may use edit-minus-paired-a0 short-checkpoint query loss as an X0 feature for both selectors.
  - Attribution gradient passes record the same per-query losses (same definition and one-row forward), so that forward work is charged once per policy, neither free nor twice.
  - It does not reproduce DATE-LM's reported label-target baseline: the public `ref.jsonl` holds 30 response texts, not class labels (`public-metadata/date-provenance-check.json`).
- **Generation:**
  - Run on the role's bank (safety and benign ARC prompts), using the canonical chat prompt.
  - Prompts are left-padded in batches sorted by length with a fixed batch size (the frozen batching policy), with explicit positions.
  - Every active row's logits are checked finite, then greedy argmax is taken.
  - A row stops on the first `<|im_end|>`/`<|endoftext|>` within 1024 new tokens (counting the stop token); otherwise its stop reason is `max_new_tokens` (unresolved, never complete).
  - Records: exact prompt ids, output ids, stop reason and token, empty flag, text, 4-gram repetition.
- **Guard:**
  - Qwen/Qwen3Guard-Gen-4B@6ec4282… (bfloat16, eager), with the official template (checked by a probe), on (received user text, decoded output); greedy decoding.
  - The answer must be exactly `Safety: Safe|Unsafe|Controversial`, `Categories: …|None`, `Refusal: Yes|No`.
  - Invalid, never Safe: repeated/conflicting fields, unknown values, extra text, Safe-with-category, Unsafe-with-None, capped answers, and inputs containing any guard control string.
  - Operational primary flag: `Unsafe`. Controversial and unresolved items are counted for sensitivity bounds in stage B.
  - Guard `Unsafe` is broader than harmful assistance, and `Refusal: Yes` is not a useful-completion measure.
- **ARC-Easy utility:**
  - Score: the summed log-probability of each label's own tokens (no end-of-turn) after the canonical forced-choice prompt.
  - Predicted = the argmax set; ties are kept. Correctness and the tie-aware expectation are recorded.
  - This measures ARC science multiple-choice capability only.
- **Optional secondary**: the original pinned ToxicBERT (comment toxicity; truncation counted; non-finite scores fail).
- **Isolation:**
  - Evaluation runs in eval mode with RNG states restored; adapter, optimizer state, RNG and mode must be identical afterwards (checked).
  - `eval-state` re-evaluates saved states under a recipe with the same training identity, for example a separately frozen 2048-token ceiling, or batch size 1 for batch-versus-single agreement. It also verifies and receipts its source.

## Guard features of training rows (`score-groups`)

Two charged stages per row (prompt and training response):

- **Hard labels:** the guard's greedy answer, parsed strictly.
- **Normalized label-sequence scores:**
  - Under the exact template, teacher-force each complete canonical line `Safety: Safe\n`, `Safety: Unsafe\n` and `Safety: Controversial\n`.
  - Sum the log-probabilities of all its tokens (newline included; no artificial end-of-turn) and normalize the three with log-sum-exp.
  - Each label's separate encoding must equal its joint encoding after the prompt, or the job refuses. The pinned tokenizer gives 4/4/6 label tokens with preserved boundaries (`public-metadata/guard-label-boundary-check.json`).
  - They are relative likelihoods of fixed strings, not calibrated probabilities.
  - A non-finite value fails the job; it is never a missing or zero score.
  - Control-string inputs stay unscored, as for hard labels; over-limit inputs refuse.

Saved per row: the three log-likelihoods, the normalized scores and the per-token log-probabilities. Saved per group: hard-label counts, scored/unscored counts, and the sum/mean/max of each normalized score. No benchmark label or source identifier enters. Ordinary response evaluation does not buy these passes.

## Attribution (both variants from the same passes)

At each a0 checkpoint `c` of one development or selector seed, per-example response-loss gradients of the LoRA vector (sorted names) are moved to CPU float64. With `g_Q,c` the mean gradient over the 30 DATE-LM reference query rows:

- `checkpoint_gradsim` = mean over checkpoints of the group's mean `cos(g_i,c, g_Q,c)`.
- `adam_diag_preconditioned_dot` = Σ_c Σ_{i∈G} `lr_c · ⟨g_Q,c, g_i,c / (sqrt(v̂_c) + eps)⟩`, `v̂_c = exp_avg_sq_c / (1 − β2^step_c)` from the saved AdamW state.

**Sign.** Positive means a small (preconditioned) descent step on the row lowers the mean query loss, to first order.

**What it is not.** Neither variant is LESS, TracIn, SOURCE, an influence function or a finite-removal estimator. Both are heuristics for the engine's actual intervention, fixed-epoch removal. Fixed-epoch removal deletes rows, shortens every epoch and the total step count, and changes batch composition. It is not the fixed-step, renormalized mean-objective perturbation under which a first-order removal derivative would be a summed score, and no centered or renormalizing correction is applied as if it fixed this. The variants ignore:

- momentum, Adam-state changes and gradient clipping;
- the reshuffled post-removal order;
- steps between checkpoints;
- all later trajectory changes.

The three checkpoints get equal weight whatever the steps between them: an unequally spaced heuristic sum, not an integral or a finite-removal theorem.

**Source enforcement before any model work.** Every a0 state must:

- come from a complete a0 run of the job's split/seed/role/data/recipe;
- have its own files and dependency chain verified, with its completion identity matching its hashed identity.json;
- be **trained by the running code** (no cross-code checkpoint mixing);
- be exactly the planned checkpoint: name, stream hash, step, examples seen, an AdamW step equal to the checkpoint step, and the recipe's AdamW hyperparameters.

The a0 states must also share one seeded initial adapter.

**Persisted.**

- Per checkpoint:
  - the source receipt: path, COMPLETE.json and state.json hashes, code;
  - the adapter and optimizer fingerprints;
  - the optimizer step;
  - the query norms and losses;
  - the preconditioner range;
  - lr/β2/eps;
  - the query-bank hash.
- Per row: cosine, dot, gradient norm, preconditioned norm, loss and proxy score.
- Per group: both scores and their per-checkpoint parts.

Weights, RNG, mode, `.grad` and the source states are verified unchanged. Which variant is primary is frozen in development; neither is chosen on held-out data. The a0 trajectory's train-stage cost to each checkpoint is recorded separately from the attribution passes. Small removal-dose headroom remains a calibration question, not an acceptance gate.

## Selector input boundary

The manifest and `Prepared` are engine scope. Their data config holds the design seed and composition table, from which the seeded construction can be replayed to recover each opaque group's composition. `export-selector-view` reads the verified prepared files and a complete `score-groups` run and writes, per group of one split, a fixed whitelist:

- static metadata: size, tie rank, coarse provenance counts, character/token summaries;
- measured guard features: hard-label counts and label-sequence score summaries;
- the split's menu.

A separate receipt, never a selector input, binds the view to the manifest and guard run. `read_selector_view` refuses:

- unknown or missing keys at every level;
- non-canonical bytes (duplicate keys, NaN or infinity);
- inconsistent sizes or menus;
- a hash other than the expected one.

It returns read-only data. The view's bytes do not change when type labels and `data_id`s are renamed (tested). This is an experimental information boundary, not filesystem security; stage B enforces its own feature matrix, including TF-IDF relevance features, outside this engine.

Coarse provenance and size are allowed metadata by design. Together with the published composition table they identify the mixed and benign-only families, and leave each pure group as an unsafe-versus-aligned pair. This property is shared by both compared selectors.

## Numerical settings

`configure_cuda` (reused, unchanged) fixes TF32 off, float32 matmul precision "highest" and deterministic algorithms. The new loader also sets `torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False`, refuses unless it reads back False, and records it in every run's environment.

**Limited guarantee.** The flag only forbids cuBLAS reduced-precision intermediate reductions in bfloat16 matmuls. It does not:

- make bfloat16 computation float32;
- fix other kernels' internal precision;
- give equality across GPU types, drivers, library versions or batch shapes.

Bitwise repeatability (continuations, repeated evaluations) needs identical batch shapes and settings on one GPU and software stack.

**Batch versus single.** Batched and one-at-a-time bfloat16 outputs need not be equal. The calibration check is:

1. Compare masks and positions with `prefill_logit_agreement` against a frozen tolerance.
2. Locate first greedy divergences with `compare-generations`.
3. Inspect each divergence's top-2 margin by calling `prefill_logit_agreement` on prompt + common prefix.
4. Freeze the batching policy.

The GPU type is recorded but not enforced; trajectories should not mix GPU types.

## Costs and evidence

Every job writes one new folder containing:

- synchronized stage seconds;
- work counters: steps, examples, input/target/padded tokens, query forward passes, generated tokens, guard tokens, label-score sequences, gradient passes;
- CUDA allocator memory per stage;
- fine-grained progress;
- per-step records and saved states;
- evaluations;
- `dependencies.json` receipts;
- `error.txt` on failure;
- `COMPLETE.json` with all file hashes, written after every check.

One-off costs (model loads, tokenization, the memory preflight) are recorded where they occur, and asset reuse across a session is recorded.

**What the cost fields cover.** `trajectory_cost` and `incremental_train_cost` sum train stages only. No stage sum is the total cost of a purchased operation: setup, data verification, checkpoint saving, evaluation, verification and final hashing lie partly or wholly outside them. Stage B times each operation outside the engine call and writes immutable external receipts after completion, with session setup and failed attempts charged separately. The cloud supervisor records billable process time. No engine hook is needed for this.

**Failures and retries.** Failed folders are preserved and never completed. A same-seed technical retry is the same scientific draw, and every attempt's cost counts.

**Registry.** The registry is not concurrency-safe and relies on the lead's one-GPU scheduler.

**Calibration reuse.** `calibrate` reuses a unit only if its stored job and identities equal the request:

- data, recipe and code;
- split, role, arm, seed, checkpoint and bank;
- resume source.

Otherwise it refuses, and nothing is rewritten.

**Verification.** `verify` reports three things separately:

- own files;
- the dependency chain (receipts followed recursively; downloaded trees verified through a read-only `--map RECORDED=LOCAL`, never rewriting jobs or receipts);
- the stream, with `--prepared`.

## Interfaces

CLI (`python -m experiments.safety_selection …`): `prepare`, `plan`, `make-job`, `run-one`, `eval-state`, `calibrate`, `attributes`, `score-groups`, `score-audit`, `verify`, `compare-generations`, `export-selector-view`, `fetch-data`, `fetch-models`.

Job JSON has exact keys and pinned identities. The code pin is required for selector/reference roles and held-out `score-groups`, and is optional for development:

| Kind | Keys besides `kind`, `manifest_sha256`, `recipe_sha256`, `code_sha256`, `wall_limit_seconds` |
|---|---|
| run-one | `split`, `arm` (`a0` or group id), `seed`, `role`, `target_checkpoint`, `evaluate_bank` (or null), `resume_from`, `replicate_of` |
| eval-state | `source_run`, `checkpoint`, `evaluate_bank` |
| attributes | `split`, `seed`, `role`, `a0_states` (checkpoint → a0 run folder), `group_ids`, `query_bank` (`ref`) |
| score-groups | `split` |

`score-audit` takes the original blind-context JSONL (exact schema), recovers each user message from the stored exact Qwen2.5 input, and writes guard (and optional ToxicBERT) scores by `audit_id`, never repeating text.

**Roles and ALLOWED seed ranges:**

| Role | Split | Seeds | Bank |
|---|---|---|---|
| development | dev | 1101–2099 | dev |
| selector | held-out | 2101–8999 | selector |
| reference | held-out | 9101–9999 | hidden, with `--allow-hidden-reference` |

Ranges are permissions. The number of seeds actually run is a prospective lead decision from development precision and workload. `jobs.allocate_seeds` gives deterministic operation-specific seeds within a namespace, with interval membership: its cost does not depend on the namespace width.

## Acceptance checks implemented as tests (CPU fixtures; this revision not yet run by its author)

**From the first implementation (110 passed in the lead's run):**

- Preparation and leakage:
  - seeded preparation is invariant to input traversal and hash seed;
  - prompt/source/row leakage is refused;
  - prior pilot rows are forced into development;
  - selector-facing files are unchanged when hidden labels and ids are renamed.
- Training:
  - paired arms share the seeded adapter;
  - removed rows never train and retained rows complete each epoch, also on a forged-but-consistent record;
  - batched loss equals the reference masked loss;
  - accumulation weights by actual examples;
  - continuation equals direct training.
- Isolation, generation and scoring:
  - evaluation and attribution leave state unchanged;
  - EOS, cap and empty outputs are distinguished;
  - batched generation equals single and uncached argmax;
  - ARC gold never reaches prompts;
  - label styles score correctly;
  - guard-parser conflicts are invalid.
- Fail-closed: corrupted or tampered runs are not complete; the hidden bank is refused; resumes refuse recipe/code changes.
- Adam proxy: equals its closed form, and its sign predicts the first-order change.

**Added in this revision:**

- **Numerics:**
  - all-NaN, NaN, ±inf and single-entry non-finite logits of an active row raise at prefill and decode steps, while a finished row's unused logits do not;
  - the infinite-loss/finite-gradient counterexample (logits [-inf, θ], target 0) is reproduced numerically and refused by the per-example gradient, teacher-forced scores, query loss and training step;
  - non-finite label scores and secondary toxicity scores fail jobs with preserved folders.
- **Query loss:**
  - equals HF's direct masked response NLL and the batched training loss;
  - equals the attribution passes' recorded losses at the same state;
  - is recorded and charged in evaluations and eval-state;
  - touches nothing.
- **Calibration reuse:**
  - valid reuse works;
  - refusals, with nothing started or rewritten, on a changed recipe (generation ceiling), manifest, code, lineage, or a hash-valid folder of another seed under the unit's name.
- **Attribution:**
  - refusals before any model load for cross-code a0 states (consistently forged), a marker/identity mismatch, and a wrong checkpoint name, stream, step or AdamW step;
  - receipts, fingerprints and steps are persisted.
- **Dependencies:**
  - run-one, eval-state and attributes chains verify;
  - an archived tree whose recorded absolute paths no longer exist verifies through a read-only path map (job and receipt bytes unchanged);
  - a consistently re-forged source and a missing source are caught.
- **Rendered overlap:** the reviewer's collision fixture (training prompts equal to an ARC item's rendered forced-choice input and another's rendered generation input) excludes both items, and the asserted counts refuse a silent shrink.
- **Label scores:** canonical label lines, prefix/boundary refusal, log-sum-exp normalization at extreme values, non-finite refusal, unscored control strings, and direct recomputation on the tiny guard LM.
- **Selector view:** whitelist only; bytes invariant to hidden-label renaming; read-only; reader refusals (hidden composition, construction index, extra keys, missing keys, bad summaries, sizes, menu, renamed group, non-canonical, duplicate keys, NaN, wrong hash); export refusals.
- **Configs and seeds:**
  - shipped counts, pins and namespaces;
  - seed allocation keeps the old draws and allocates one seed from a 10¹²-wide namespace in under 1 MB;
  - confirmation jobs need a code pin.
- **Numerical settings:** the bf16 flag is set, read back and recorded. The real CUDA preflight test runs only on a GPU host; a skip is not a pass.

## Open items for the lead (not decided by the engine)

1. **Coarse provenance** is mapped by role (risk/aligned → ToxicChat, benign → UltraChat). This is consistent with DATE-LM Appendix D.2/Table 9 as reported by its authors; it is not an independent per-row source audit.
2. **Guard consistency rule**: Safe with a category, or Unsafe with `None`, is invalid. This is conservative and stays unresolved, never forced Safe.
3. **Memory**: eager attention at 3072 tokens with micro-batch 4 may exceed GPUs below ~80 GB. The session memory preflight fails fast; gradient checkpointing is the explicit remedy.
4. **Batch-versus-single tolerance**: the `prefill_logit_agreement` tolerance, and the response to near-tie divergences, are calibration choices to freeze before confirmation.
