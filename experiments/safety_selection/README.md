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
| `configs/` | | `study-v2-data.json`; `study-v2-recipe-calibration.json` (and a ToxicBERT-secondary variant) |

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

## Not done here

No selector, menu replay, TF-IDF relevance features, acquisition, endpoint, margin, interval or
held-out comparison (stage B). No WildGuard. No parquet conversion. No automatic
batch/precision reduction or device fallback. No CLI wrapper around `prefill_logit_agreement`.
The 2048-token rerun, batch-versus-single agreement and the memory limit are calibration
measurements (via `eval-state` and the session memory preflight), not results here.
