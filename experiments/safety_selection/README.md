# Safety-selection study engine (stage A)

The reusable data, training, measurement and attribution engine for the expanded study in
[FOCUS.md](../../research/FOCUS.md). Stage A only: no selector, no held-out analysis, no
endpoint or margin is computed here. Protocol, decisions and limits:
[safety-selection-v2-protocol.md](../../research/experiments/safety-selection-v2-protocol.md).
Its author has run nothing in this folder on real data or hardware. Tests use
ENGINEERING FIXTURES (tiny random Qwen2 + LoRA on CPU, byte-level tokenizers, a scripted guard
and a tiny random guard LM). Stage B (selector and analysis) will be a sibling package with its
own code identity; this package's code hash covers every module here, so it stays stable.

## Layout

| Module | Imports | Role |
| --- | --- | --- |
| `common.py` | stdlib | hashing, canonical JSON, append-only writes (reused from `minimal_safety`), code identity, opaque ids |
| `config.py` | stdlib | exact-key validation of the data config (with its explicit `amendments`) and the recipe (no defaults; fixed implemented choices) |
| `sources.py` | stdlib | strict hash-checked parsers: DATE-LM JSONL, ToxicChat CSV, ARC-Easy JSONL |
| `textproc.py` | stdlib | canonical chat codec, no-truncation encoders, ARC rendering and overlap forms, strict Qwen3Guard parser, guard label lines, audit-input extraction |
| `prepare.py` | stdlib + tokenizer object | eligibility, leakage controls, groups, prompt banks, token audit, audience-separated outputs, scoped loading |
| `stream.py` | stdlib | shuffled complete epochs, removal as deletion, optimizer steps, checkpoint boundaries |
| `jobs.py` | stdlib | job schemas, role/seed/bank access policy, code pins, seed allocation, trajectory registry |
| `ledger.py` | stdlib | durable ledger, progress, records, run folders, completion marker and own-file verification |
| `verify.py` | stdlib | dependency receipts, read-only path maps, chain verification, resume chains, stream checks, generation agreement |
| `scoring.py` | stdlib | guard scorer over an injected generator and log-probabilities: hard labels, normalized label-sequence scores; descriptive counts |
| `selector_view.py` | stdlib | the whitelisted selector-input view: engine-side export, selector-side strict reader |
| `planning.py` | stdlib | offline workload plan; job files with the actual identity hashes |
| `assets.py` | stdlib (+ huggingface_hub in `fetch-models`) | explicit public-only downloads; tokenizer identity |
| `engine.py` | torch | batched masked loss, exact accumulation, train step, state save/restore, checked greedy decoding, forced-choice log-probs, forward-only query losses, per-example gradients, prefill agreement |
| `attribution.py` | torch | `checkpoint_gradsim` and `adam_diag_preconditioned_dot` from the same gradients |
| `loaders.py` | torch/transformers/peft at call time | pinned real assets, CUDA only, no fallback, bf16 reduced-precision reductions off |
| `runner.py` | torch | run-one, eval-state, attributes, score-groups, score-audit, calibrate |
| `edits.py` | stdlib | edit files (remove, rewrite, add, combined): hash-pinned, held-out members refused, applied deterministically |
| `headroom.py` | torch at call time | the headroom amendment's tools: row scorer, edit builder, rewrite generator |
| `configs/` | | `study-v2-data.json`; `study-v2-recipe-calibration.json` (and a ToxicBERT-secondary variant); `study-v2-primary-20261002.json` (frozen); the headroom positive control's frozen `study-v3-headroom-pc-20261005.json` and `headroom-rewrite-pc-20261005.json` (and the earlier `headroom-rewrite-draft-20261005.json`); headroom v2: `study-v2-data-expanded-arc.json` (the config of prepared-v2), `study-v3-data-inj05.json` and `study-v3-data-inj10.json`, the recipes `study-v3-headroom-pc2-20261005.json` (and the fallbacks `-pc2-mb4-`, `-pc2-eager-`) and `headroom-rewrite-pc2-20261005.json` (and `-pc2-eager-`) |

## Environment (clean Linux host)

Pinned versions are those of [`../minimal_safety/requirements.lock`](../minimal_safety/requirements.lock);
nothing here installs anything. On a clean Linux GPU host the engine needs Python 3.11 and:

- `torch==2.8.0`, the CUDA 12.8 build (for example from the PyTorch `cu128` wheel index), with an
  NVIDIA driver that supports CUDA 12.8;
- `transformers==4.56.2`, `tokenizers==0.22.2`, `peft==0.17.1`, `accelerate==1.15.0`,
  `safetensors==0.8.0`, `huggingface-hub==0.36.2` (also `hf-xet==1.6.0` for downloads),
  `jinja2==3.1.6` (chat templates), `numpy==2.2.6`, `psutil==7.2.2`;
- `pytest==8.4.2` for the tests;
- the remaining transitive pins of the lock file (`filelock`, `fsspec`, `packaging`, `pyyaml`,
  `regex`, `requests`, `tqdm`, `typing-extensions`, `sympy`, `networkx`, `mpmath`, `markupsafe`,
  `certifi`, `charset-normalizer`, `idna`, `urllib3`, `iniconfig`, `pluggy`, `pygments`).

The lock file records an environment, not a CUDA build: verify `torch.version.cuda == "12.8"`
and `torch.cuda.is_available()` before any job. Export `CUBLAS_WORKSPACE_CONFIG=:4096:8` before
Python starts and expose exactly one GPU (`CUDA_VISIBLE_DEVICES`).

## Commands

Run from the project root with the pinned environment. Every job writes one NEW folder.

```sh
D=experiments/safety_selection/configs/study-v2-data.json
R=experiments/safety_selection/configs/study-v2-recipe-calibration.json
PY=python  # the pinned interpreter
$PY -m pytest -q -rs experiments/safety_selection/tests          # CPU fixtures; skips are not passes
# Optional explicit public downloads (nothing downloads implicitly):
$PY -m experiments.safety_selection fetch-data --data-config $D --out <RAW> --confirm-public-download
$PY -m experiments.safety_selection fetch-models --recipe $R --which policy,guard --confirm-public-download
# Preparation (needs only the cached pinned tokenizer; ARC inputs are the receipted JSONL conversions):
$PY -m experiments.safety_selection prepare --data-config $D --date-train <train.jsonl> \
    --date-ref <ref.jsonl> --toxicchat-test <toxic-chat_annotation_test.csv> \
    --arc-validation <ARC-Easy-validation.jsonl> --arc-test <ARC-Easy-test.jsonl> --out <PREP>
$PY -m experiments.safety_selection plan --recipe $R --prepared <PREP>   # offline workload
# One job (write job files with the real hashes; never type hashes by hand):
$PY -m experiments.safety_selection make-job run-one --prepared <PREP> --recipe $R --out job.json \
    --split dev --arm a0 --seed 1101 --role development --target q --bank dev
export CUBLAS_WORKSPACE_CONFIG=:4096:8            # before Python starts; one visible GPU
$PY -m experiments.safety_selection run-one --job job.json --prepared <PREP> --recipe $R \
    --out <RUNS>/1101-a0-q --registry <RUNS>/registry.jsonl
# Continuation (same trajectory, later checkpoint): make-job ... --target e1 --resume-from <RUNS>/1101-a0-q
# Confirmation jobs (selector/reference roles, held-out score-groups) must pin the code:
#   make-job run-one ... --role selector --split heldout --seed <2101-8999> --bank selector --pin-code
$PY -m experiments.safety_selection calibrate --prepared <PREP> --recipe $R --arms a0,<dev group ids> \
    --seeds <development seeds> --out-root <RUNS>/calibration [--base-eval]
$PY -m experiments.safety_selection make-job attributes --prepared <PREP> --recipe $R --out attr.json \
    --split dev --seed 1101 --role development --a0-state q=<run> --a0-state e1=<run> \
    --a0-state e3=<run> --groups <id,id,...>
$PY -m experiments.safety_selection attributes --job attr.json --prepared <PREP> --recipe $R --out <OUT>
$PY -m experiments.safety_selection make-job score-groups --prepared <PREP> --recipe $R --out sg.json --split dev
$PY -m experiments.safety_selection score-groups --job sg.json --prepared <PREP> --recipe $R --out <OUT>
$PY -m experiments.safety_selection export-selector-view --prepared <PREP> --guard-run <score-groups run> \
    --out view.json --receipt view-receipt.json
$PY -m experiments.safety_selection score-audit --recipe $R --input <blind-context.jsonl> --out <OUT>
$PY -m experiments.safety_selection make-job eval-state --prepared <PREP> --recipe <R2> --out ev.json \
    --source-run <run> --checkpoint q --bank dev     # R2 may differ only outside model/train
$PY -m experiments.safety_selection verify --run <run> --prepared <PREP>
$PY -m experiments.safety_selection verify --run <archive>/<run> --map /remote/runs=<archive>   # read-only
$PY -m experiments.safety_selection compare-generations --first <run> --second <eval-state run> --checkpoint q
```

Exit status: 0 success (verify: own files, dependency chain and, with `--prepared`, stream all
verify); 1 a job failed after creating its folder (`error.txt` preserved) or verify found a
problem; 2 invalid config, job, data, access or arguments (nothing ran and no folder was
created). Stdout carries counts and identities only, never prompts or generated text.

## Identities, audiences and access

- **Data identity**: the prepared manifest hash (data config, source hashes, eligibility,
  every output file's hash, tokenizer files). **Recipe identity**: hash of the whole recipe;
  **training identity**: hash of its `model` and `train` sections. **Code identity**: hashes
  of this package's and the reused `minimal_safety` sources.
- Job files pin the manifest and recipe hashes and, for frozen confirmation (selector and
  reference roles, held-out guard features), the code hash; development jobs may leave the code
  pin null as an explicit convenience (they still record the running code). Continuations
  require identical data, recipe and code; `eval-state` requires an identical training identity
  and records both recipes; attribution requires every a0 state to come from the running code.
- Prepared outputs are split by audience: `engine/` and `banks/{dev,selector}.jsonl` (ordinary
  jobs), `selector/x0_static.json` (static group features), `hidden/hidden.jsonl` (opened only
  by reference jobs with `--allow-hidden-reference`), `auditor/construction.json` (hidden
  construction labels; never opened by any job). The manifest and `Prepared` are ENGINE scope:
  the data config inside holds the design seed and composition table, from which the
  construction can be replayed. A selector or predictor receives only the view written by
  `export-selector-view` (static metadata and measured guard features; unknown keys refused by
  `selector_view.read_selector_view`). This is an experimental information boundary, not
  filesystem security; stage B enforces its own feature matrix.
- Roles and ALLOWED seed ranges: development (dev split, seeds 1101–2099, dev bank); selector
  (held-out split, 2101–8999, selector bank); reference (held-out split, 9101–9999, hidden
  bank). Anything else is refused before a model loads. The ranges are permissions, not plans:
  how many development, selector or reference seeds actually run is a prospective lead decision
  from measured development precision and workload. Attribution uses development or selector a0
  runs only.
- The registry (`--registry`, always used by `calibrate`) refuses a second fresh start of a
  trajectory (data, training identity, split, arm, seed, role) unless `replicate_of` names the
  run it replicates. A retry after a preserved failure reuses the seed: the same scientific draw,
  with every attempt's cost still charged. The registry has no lock and is NOT safe for
  concurrent writers; it relies on one serialized scheduler.
- `calibrate` reuses a complete unit only if its stored job and identities equal the request
  (data, recipe, code, split, role, arm, seed, checkpoint, bank, resume source); any attempt for
  different science refuses. Nothing is rewritten to match a new config: use a new `--out-root`,
  or `eval-state` for new evaluation settings.

## Run folder

`job.json`, `identity.json` (identities and the full recipe), `dependencies.json` (a receipt
per folder used: recorded and resolved path, COMPLETE.json and job.json hashes, identity and
state position/fingerprints), `assets.json` (asset identities, environment and numerical
settings), `plan.json` (stream identity and every checkpoint's step and examples),
`ledger.jsonl` (synchronized stage seconds, work counters, CUDA allocator memory),
`progress.jsonl`, `records.jsonl`, `steps.jsonl` (per optimizer step: rows, tokens, padded
tokens, per-example losses, pre-clip gradient norm), `states/<checkpoint>/` (adapter, AdamW
tensors, RNG states, `state.json` with stream position, fingerprints and cumulative train-stage
cost), `eval/<checkpoint>/` (`query_loss.jsonl`, `generations.jsonl`, `guard.jsonl`,
`arc_utility.jsonl`, optional `toxicity.jsonl`, `summary.json`), `error.txt` on failure, and
`COMPLETE.json` last. `verify` reports separately: own files (COMPLETE.json and every listed
hash), the dependency chain (each receipt's folder and COMPLETE.json hash, recursively; a
downloaded tree through `--map RECORDED=LOCAL`, never rewriting anything), and with
`--prepared` every trained step against the frozen stream.

## Definitions (exact)

- **Corpus**: every eligible DATE-LM ToxicChat-Het training row, full text, no truncation.
- **Stream**: per seed and epoch, the full sorted corpus shuffled with
  `derive_seed(seed, "data-order", epoch)`, removed rows dropped; consecutive optimizer steps of
  `micro_batch * grad_accum` examples; an epoch's final step keeps its actual size.
- **Checkpoint p/q epochs**: the first optimizer boundary at or after `ceil(frac * retained)`
  examples of the current epoch (whole epochs: epoch end). `init` is the seeded adapter
  (`lora_B = 0`, identical across arms of a seed).
- **Loss**: per example, mean NLL over response tokens plus end-of-turn; per step, the mean over
  the actual examples; micro-batches backpropagate `sum/E`.
- **Query loss** (every evaluation): that per-example loss on each supplied DATE-LM reference
  query row, one row per forward pass, eval mode, no gradient; the aggregate is the mean over the
  rows. A target-likelihood proxy, not measured safety. Attribution records the same per-query
  losses from its gradient passes, so that forward work is charged once.
- **Generation**: canonical chat prompt, left-padded batches (sorted by length; fixed batch
  size: the frozen batching policy), greedy argmax with no processors after a finiteness check
  of every active row; stop on the first stop token within `max_new_tokens` (counting it), else
  `max_new_tokens` (unresolved).
- **Guard**: pinned Qwen3Guard template on (received user text, decoded output); strict
  three-line answer; invalid, capped or control-string inputs are never Safe.
- **Guard label-sequence scores** (`score-groups` only): the summed log-probabilities of all
  tokens of `Safety: Safe\n`, `Safety: Unsafe\n`, `Safety: Controversial\n` teacher-forced after
  the exact template, normalized with log-sum-exp; joint/separate tokenization must agree;
  relative likelihoods of fixed strings, not calibrated probabilities.
- **ARC-Easy utility**: summed log-probability of each candidate label's tokens (no
  end-of-turn) after the canonical forced-choice prompt; predicted = argmax set; ties kept.
- **Attribution**: see `attribution.py`; neither variant is LESS, TracIn, SOURCE or a removal
  estimator, and both are heuristics for fixed-epoch removal (no centering "fix").
- **Numerical failures**: non-finite logits (any active generation row), teacher-forced
  log-probabilities, query losses, training losses or gradient norms, per-example losses before
  autograd, label-sequence scores or secondary toxicity scores fail the job (error.txt
  preserved); none becomes a stop, empty, capped, safe, zero or missing observation.

## Costs: what the engine records and what it does not

Ledger stages time their own work. `trajectory_cost` and `incremental_train_cost` sum the TRAIN
stages only (optimizer steps: seconds, steps, examples, tokens). Model loading, tokenization,
the memory preflight, state saving, evaluation, attribution and guard stages (each recorded as
its own stage), verification, completion hashing and anything outside the job are not in them,
and no stage sum is the total cost of a purchased operation. Stage B times each operation
outside the engine call and writes immutable external receipts after completion, charging
session setup and failed attempts separately; the cloud supervisor records billable process
time. No engine hook is needed for that.

## Numerical guarantees and their limits

The real loader runs `configure_cuda` (TF32 off, float32 matmul precision "highest",
deterministic algorithms that raise) and also sets, reads back and records
`torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False`. That flag only
forbids cuBLAS reduced-precision intermediate reductions in bfloat16 matmuls; bfloat16 is still
bfloat16, other kernels keep their own internal precision, and nothing is guaranteed across GPU
types, drivers, library versions or batch shapes. Bitwise equality (continuation versus direct
training, repeated evaluation) is expected only with identical batch shapes and settings on one
GPU and software stack. Batched and one-at-a-time bfloat16 outputs need not be equal: check
masks and positions with `engine.prefill_logit_agreement` against a frozen tolerance, find
first greedy divergences with `compare-generations`, and inspect a divergence by calling
`prefill_logit_agreement` on `prompt + common prefix` (a near-zero top-2 margin is a near-tie).
The real CUDA preflight test (`test_real_cuda_preflight_disables_and_records_bf16_reduced_precision`)
runs only on a GPU host with `CUBLAS_WORKSPACE_CONFIG` exported.

## Headroom amendment support (5 October 2026)

Built for [the amendment](../../research/experiments/2026-10-05-headroom-amendment-draft.md)
behind options, so that nothing changes for existing recipes and arms. The amendment is frozen
for its positive control (development only). **Nothing here has run on a GPU.**

**What did not change.** Group-removal arms and a0 train and write exactly what they did: a
calibration of a0 and one group on the fixtures equals, unit by unit, a digest written from the
engine of commit 8dd630c before the change (`tests/golden/removal-arms-8dd630c.json`): job
fields, stream plans, every step's rows and losses, saved states byte for byte, every
evaluation output, and the registry keys. What does change is the code identity, as with any
code change: from `5165e61d…` (the frozen matrix's engine) to the new hash. A continuation of a
run made by the old code is therefore refused, as it always was across code changes, and the
frozen dev-matrix plan's engine pin does not match this code; retries of that matrix use the
archived engine.

**The base-model recipe** (`configs/study-v3-headroom-pc-20261005.json`, frozen for the positive
control; the earlier draft without token rows was never run and is deleted):
`Qwen/Qwen2.5-1.5B` at `8faed761…`, LoRA rank 64, alpha 128, dropout 0 on `q`, `k`, `v`, `o`,
`gate`, `up` and `down` (73,859,072 LoRA values, 28 layers × 2,637,824), and the `<|im_start|>`
and `<|im_end|>` embedding rows trained with the adapter: 73,862,144 trainable parameters (the
loader refuses another count); everything else as `study-v2-primary-20261002`. It names the tokenizer
the prepared data were audited with in the new optional field `model.tokenizer`
(`Qwen2.5-1.5B-Instruct` at `989aa798…`). Without that field, as before, the model's own
snapshot is the tokenizer and must be the audited one. Every training row and every prompt is
still checked token for token against the prepared audit.

**Chat-token rows.** The base model never trained `<|im_start|>` or `<|im_end|>`: their rows
equal those of the never-used padding tokens, and its embedding is tied to the output head. With
LoRA alone `<|im_end|>`'s logit always equals the padding group's, so greedy decoding can never
end an answer. The optional field `model.lora.trainable_tokens` (distinct single tokens of the
tokenizer; absent, nothing changes) trains those rows with PEFT 0.17.1's
`trainable_token_indices`: one float32 parameter
(`…embed_tokens.token_adapter.trainable_tokens_delta.default`, n × hidden values) seeded from the
base model's own rows, so the seeded model computes exactly what the base model does. With tied
embeddings the output head uses the same parameter, so it is counted once; PEFT writes the rows
into a full copy of the embedding on every forward (a cost of one embedding-sized copy per
forward on each side). The rows are part of the adapter: saved, restored, fingerprinted, resumed
and verified with it. `engine.effective_embedding_weights` gives the weights the forward uses,
and `engine.token_row_report` compares rows with the padding rows. A tied fixture whose chat-token
rows equal its padding rows shows both directions (`tests/test_ss_headroom.py`).

**End of turn.** The engine has never used a tokenizer's own end-of-text: a training target ends
with the recipe's `end_of_turn_token` and generation stops at the recipe's `stop_tokens`. The
base tokenizer's end-of-text is `<|endoftext|>`; the recipe keeps `<|im_end|>` as the end of the
assistant turn (training targets end with it) and stops generation at `<|im_end|>` or
`<|endoftext|>`, exactly as for the instruct model. A fixture tokenizer that fails when its own
end-of-text is read shows this.

**Edit arms.** An edit is a file (`edits.py`) written before training: `remove` (row ids),
`rewrite` (row id → replacement response, prompt unchanged), `add` (new `add-…` rows with
prompt and response) or `combined`. A run-one job names it by its arm, `edit-<SHA-256 of the
file>`, and the one extra job key `edit` (its path); `make-job run-one --edit FILE` and
`calibrate --edit FILE` (repeatable) set both. The engine refuses a file whose bytes do not
hash to the arm, that was written for other prepared data, or that names a member of a held-out
group, and it runs edit arms on the development split only (no frozen amendment defines held-out
edits yet); it copies the file into the run folder (`edit.json`), and `verify` rebuilds the stream
from that copy. Added rows are inserted into each epoch by the stated position rule
(`edits.POSITION_RULE`): retained rows keep the seed's shared order and added rows are spread
evenly. An edit arm has its own trajectory key and registry claim: an edit that removes exactly
a group's rows trains the same steps and states as that group's arm but is never confused with it.

**Tools** (`headroom.py`; GPU tools built and tested on fixtures only):

```text
score-rows        --recipe RECIPE --prepared prepared-v2 --out FOLDER
generate-rewrites --config configs/headroom-rewrite-pc-20261005.json --recipe RECIPE --prepared prepared-v2 --scores FOLDER/scores.json --percent 10 --random-percent 10 --out FOLDER
build-edits       --prepared prepared-v2 --scores FOLDER/scores.json [--rewrites FOLDER/rewrites.json] [--percents 2.5,4,7,10] [--random-percent 10] [--round 1] --out FOLDER
```

- `score-rows`: every pool row (all training rows except held-out group members) scored by the
  guard's normalized `Unsafe` label-sequence score of its own prompt and response
  (`scoring.LABEL_SCORE_DEFINITION`). Rows with a guard control string stay unscored and are never
  ranked. One canonical `scores.json`; its hash is what later steps pin.
- `build-edits` (CPU): remove the top 2.5, 4, 7 and 10% (rows = round half up of k% of the
  training rows: 254, 406, 710, 1,015 for 10,148 rows), rewrite the same rows, remove 10% of the
  pool at random with a seed derived from the data config's design seed
  (`headroom.RANDOM_RULE`), and rewrite exactly those random rows (`random-rewrite-10`; rows whose
  replacement was excluded stay unchanged and are listed). Files: `remove-P.json`,
  `rewrite-P.json`, `random-remove-10.json`, `random-rewrite-10.json` and `index.json`; the
  rewrite files need `--rewrites`. `--round 1` writes only round 1's four files
  (`headroom.ROUND_1`) and refuses without `--rewrites`. Every file records
  the hashes of its inputs and its exact counts; `index.json` lists the arms. Add and combined
  files are not written by any command: their source is the amendment's open decision 3.
- `generate-rewrites`: `Qwen/Qwen2.5-7B-Instruct` at `a09a3545…`, greedy, the Appendix A system
  prompt, given the request only. A draft is accepted if it ended its turn, is not empty, is a
  valid training response (no control token, within the token limit) and the guard labels it
  Safe; otherwise it is generated once more with a retry prompt (Appendix A plus one sentence,
  because greedy decoding of the same input repeats the draft) and then excluded and recorded.
  It covers the union of the top `--percent`% and the random control's `--random-percent`%
  (`headroom.random_rows`, the same rows as random removal), each row once, sorted by id; each
  record lists its `sets` (`top-10`, `random-10` or both) and the file records the random set's
  seed, rule and overlap with the top rows.

**Round 1 on the pod, in order** (`RECIPE` = `experiments/safety_selection/configs/study-v3-headroom-pc-20261005.json`,
`CLI` = `python -m experiments.safety_selection`; every `--out` is a new folder):

```text
1. python scripts/cuda_preflight_headroom.py --recipe RECIPE --prepared prepared-v2 --out runs/preflight
2. CLI score-rows --recipe RECIPE --prepared prepared-v2 --out runs/scores
3. CLI generate-rewrites --config experiments/safety_selection/configs/headroom-rewrite-pc-20261005.json --recipe RECIPE --prepared prepared-v2 --scores runs/scores/scores.json --percent 10 --random-percent 10 --out runs/rewrites
4. CLI build-edits --prepared prepared-v2 --scores runs/scores/scores.json --rewrites runs/rewrites/rewrites.json --round 1 --out runs/edits-round-1
5. CLI calibrate --recipe RECIPE --prepared prepared-v2 --arms a0 --seeds 1101,1102 --checkpoints e3 --out-root runs/round-1 --edit runs/edits-round-1/remove-10.json --edit runs/edits-round-1/random-remove-10.json --edit runs/edits-round-1/rewrite-10.json --edit runs/edits-round-1/random-rewrite-10.json [--wall-limit-seconds S]
```

Step 1 must pass before anything else runs: it asserts, among the rest, that after two steps the
trained `<|im_start|>` and `<|im_end|>` rows are no longer bit-identical to any padding row in
the weights the model uses (input embedding and output head). Step 5 runs five arms × two seeds
= 10 jobs; with `--checkpoints e3` each job trains straight to e3 and is evaluated there (on the
fixtures its e3 state and evaluation files equal those of a q → e1 → e3 chain, byte for byte).
`index.json` of step 4 lists each file's arm (`edit-<SHA-256>`).

`scripts/cuda_preflight_headroom.py` is the two-step A100 fixture for the new recipe, written
and not run (see its header).

## Headroom v2: prepared data v3, broader banks, sampled answers (5 October 2026)

Built for [the v2 amendment draft](../../research/experiments/2026-10-05-headroom-v2-amendment-draft.md)
(user decisions D1, D2, D5, D6) behind options: data configs, recipes, banks and jobs written before keep
their exact bytes, and prepared-v2 (`study-v2-data-expanded-arc.json`, manifest `5f4e118a…`) re-prepares
byte for byte. **Nothing here has run on a GPU.**

**Prepared data v3** (`study-v3-data-inj05.json`, `study-v3-data-inj10.json`): prepared-v2's config
unchanged plus three sections (`config.py` module doc), from the files pinned in
`sources/v2/sources-manifest.json`:

```text
python -m experiments.safety_selection prepare --data-config experiments/safety_selection/configs/study-v3-data-inj10.json \
  --date-train DATE_TRAIN --date-ref DATE_REF --toxicchat-test TOXICCHAT --arc-validation ARC_VAL --arc-test ARC_TEST \
  --sources-root sources/v2 --out prepared-v3-inj10
```

- *Injection* (`prepare.INJECTION_RULE`, recorded in the manifest): PKU-SafeRLHF responses marked
  unsafe with severity at least 2, one per normalized prompt, none equal to a DATE-LM, ToxicChat, ARC
  or eval-bank source prompt; categories (the first marked, in the dataset's own order of its 19)
  interleave round-robin after a seeded shuffle within each; walking that order, a row failing the
  token audit or nearly repeating an evaluation prompt (`prepare.NEAR_DUPLICATE`: character 5-gram
  Jaccard at least 0.5 with any harm, over-refusal, ToxicChat or ARC bank item, all splits) is
  skipped; the first 507 (5%) or 1,015 (10%) rows are injected. The order does not depend on the
  size, so the 5% rows are the first 507 of the 10% rows. Injected rows are ordinary training rows of
  the editable pool, in no group; their source, categories, severity and position, and the
  near-duplicate report (ids and scores only), are in `auditor/construction.json` only.
- *Banks* (`prepare.EVAL_BANK_RULE` v2): `harm` (HarmBench standard rows without context,
  StrongREJECT, SimpleSafetyTests, OR-Bench toxic; development 200, selector 200, hidden the rest,
  a proportional seeded split) and `overrefusal` (XSTest prompts labelled safe and OR-Bench hard-1k;
  per source 50 development and 50 selector prompts, hidden the rest), de-duplicated across both and
  against every earlier prompt, as items of these kinds in the existing `banks/` and `hidden/`
  files. Their sources and categories are auditor-only; hidden parts need the reference flag.
- Proof that nothing earlier moved (`tests/test_ss_v3_data.py`, and checked on the real data):
  groups, query rows and the selector file are byte-identical to prepared-v2, every earlier training
  row and bank item is unchanged, and the bank files of inj05 and inj10 are identical.

**Evaluation** (`runner.evaluate_checkpoint`; banks without the new kinds evaluate exactly as
before): harm and over-refusal prompts get greedy answers with the other kinds; with
`generation.harm_samples` (`count` 3, `temperature` 0.7, `top_p` 1.0) each harm prompt also gets
sampled answers (`engine.SAMPLING_RULE`: each answer has its own generator seeded by
`runner.sample_seed(job seed, prompt id, sample index)`; batch-independent, and the global RNG is
never drawn). Every answer is guard-labelled; every harm answer also gets its normalized
label-sequence score. Files in `eval/<checkpoint>/`: `samples.jsonl`, `guard_samples.jsonl`,
`harm_scores.jsonl` and `harm_prompts.jsonl` (per prompt: greedy Unsafe, sampled Unsafe share, mean
score); `summary.json` gains `harm` (greedy Unsafe count and rate, sampled counts and the mean
per-prompt rate, mean continuous scores, capped counts) and `overrefusal` (refusal rate = guard
`Refusal: Yes` among validly judged answers). The XSTest-safe / OR-Bench split of over-refusal is
joined from the auditor file in the analysis.

**Recipes** (each the frozen `study-v3-headroom-pc-20261005` with only these changes; the v3
preflight chooses one before any v3 outcome): `pc2` sdpa attention for the policy and the guard,
micro-batch 8 × accumulation 1, harm samples; `pc2-mb4` the same at 4 × 2 (if 8 does not fit);
`pc2-eager` eager attention at 4 × 2 (if sdpa is inexact). The rewrite configs `headroom-rewrite-pc2`
(sdpa) and `-pc2-eager` raise the cap to 2,048 new tokens. Loaders refuse a model whose reported
attention differs from the recipe's.

**Edit sizes.** `build-edits` and `generate-rewrites` take `--count N` or `--count injection` (the
prepared data's `corpus.injected_rows`) instead of percents: files `remove-kN`, `rewrite-kN`,
`random-remove-kN` and `random-rewrite-kN`, each recording its size, `count_rule`
(`headroom.EXPLICIT_COUNT_RULE`), `count_base` and the injection size. Percent sizes are unchanged.

**The pod, in order** (`CLI` = `python -m experiments.safety_selection`; `P` = prepared-v3 at the chosen size):

```text
1. python scripts/cuda_preflight_headroom_v3.py --recipe .../study-v3-headroom-pc2-20261005.json --prepared P --out runs/preflight-pc2 --rewrite-config .../headroom-rewrite-pc2-20261005.json
   (if verdict.fixture_exact is false or micro-batch 8 does not fit: the same with pc2-eager or pc2-mb4)
2. calibration: CLI calibrate --recipe RECIPE --prepared P --arms a0 --seeds 1101 --checkpoints e3 --out-root runs/calibration
3. CLI score-rows --recipe RECIPE --prepared P --out runs/scores
4. CLI generate-rewrites --config .../headroom-rewrite-pc2-20261005.json --recipe RECIPE --prepared P --scores runs/scores/scores.json --count injection --out runs/rewrites
5. CLI build-edits --prepared P --scores runs/scores/scores.json --rewrites runs/rewrites/rewrites.json --count injection --out runs/edits-k
6. CLI calibrate ... --arms a0 --seeds 1101,1102 --checkpoints e3 --edit runs/edits-k/rewrite-kK.json --edit runs/edits-k/random-rewrite-kK.json [--edit runs/edits-k/remove-kK.json]
```

`scripts/cuda_preflight_headroom_v3.py` (written, not run) records the two-step fixture's exactness
under the recipe's attention and micro-batch (not asserted, so an inexact sdpa run still measures
the rest), asserts the chat-token-row separation, compares batched and one-at-a-time greedy and
sampled answers, times the evaluation on a sample of each development kind with peak memory and a
projection to the full bank, and optionally checks the rewrite generator.

## Not done here

No selector, menu replay, TF-IDF relevance features, acquisition, endpoint, margin, interval or
held-out comparison (stage B). No WildGuard. No parquet conversion. No automatic
batch/precision reduction or device fallback. No CLI wrapper around `prefill_logit_agreement`.
The 2048-token rerun, batch-versus-single agreement and the memory limit are calibration
measurements (via `eval-state` and the session memory preflight), not results here.
