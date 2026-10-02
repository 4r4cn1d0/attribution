# Minimal safety calibration (engineering slice)

Before a human audit, copy the blank audit export into a separate labels file: rebuilding a
summary regenerates the blank export. For truncated prompts, reconstruct the actual model
input before judging contextual refusal or helpfulness; the original prompt can contain text
the model did not receive. The dated run note records any such cases and audit preparation.

One real, local, end-to-end a0/removal slice for the question in
[FOCUS.md](../../research/FOCUS.md): data preparation, LoRA training with short and long
checkpoints, classifier-proxy evaluation, a gradient-cosine diagnostic, a stage-cost ledger and
a blind-audit export. It produces **engineering evidence** (does the plumbing work, what does
each stage cost, are outcomes traceable). It is not an H1/H2 test, a headroom or
positive-control result, a DATE-LM replication, a safety certificate or a publishable finding.
Protocol, deviations and limits: [minimal-safety-pilot.md](../../research/experiments/minimal-safety-pilot.md).

## Layout

| Module | Imports | Role |
| --- | --- | --- |
| `data.py` | stdlib | hash-checked raw rows, exclusions, dedupe, leakage checks, frozen manifest, data streams |
| `plan.py` | stdlib | config validation (exact keys, no defaults) and the offline dry run |
| `text.py` | stdlib | token layout, label masking, truncation, refusal and prompt-copy diagnostics |
| `ledger.py` | stdlib | synchronized stage timing, cooperative wall/output caps, `status.json` |
| `report.py` | stdlib | evidence verification, `summary.json`, `report.md`, matched comparisons, costs, blind audit |
| `model.py` | torch | LoRA vector and seeded init, response-only loss, train step, greedy decoding, gradient cosine, asset loading, device checks and CUDA settings |
| `run.py` | torch | the single calibration loop |
| `configs/calibration.json` | | the calibration settings (the only source of settings) |
| `configs/calibration-cuda.json` | | the same settings for one NVIDIA GPU: only `name` and `model.device` differ (tested) |
| `requirements.lock` | | copy of the prepared environment lock (Python 3.11.15) |

## Commands

Run from the project root with the prepared isolated interpreter (or a fresh venv installed
from `requirements.lock`; never the old pilot venv). Placeholders: `<PY>` that interpreter,
`<RAW_TRAIN>`/`<RAW_REF>` the local raw `train.jsonl`/`ref.jsonl` of
`DataAttributionEval/Toxicity-Bias-Filtering@ad96bd4…/data/ToxicChat-Het`, `<PREPARED>` a new
output folder, `<RUN>` a new run folder (e.g. under `tmp/`, which git ignores). Set
`HF_HUB_CACHE=<HF_CACHE>` if the cached model and scorer are not in the default cache.

```sh
CFG=experiments/minimal_safety/configs/calibration.json
<PY> -m pytest -q experiments/minimal_safety/tests                        # CPU, offline
<PY> -m experiments.minimal_safety plan --config $CFG                       # dry run
<PY> -m experiments.minimal_safety prepare --config $CFG --train <RAW_TRAIN> --ref <RAW_REF> --out <PREPARED>
<PY> -m experiments.minimal_safety plan --config $CFG --prepared <PREPARED> # streams, exposure, assets
<PY> -m experiments.minimal_safety run --config $CFG --prepared <PREPARED> --run-dir <RUN> \
    --manifest-sha256 <SHA256 printed by prepare, after reviewing the plan>
<PY> -m experiments.minimal_safety summarize --run-dir <RUN>                # verify; recover after a kill
```

`plan`, `prepare`, `summarize` import only the standard library; `plan` never loads, trains,
scores or downloads. `fetch --config $CFG --out <DIR> --confirm-public-download` is an optional,
explicitly requested public download of the two pinned raw files (hash-checked); nothing calls
it. Exit status: 0 success (`run`/`summarize`: complete), 1 run incomplete (summary still
written), 2 invalid config/data/arguments, unfrozen inputs or an unreadable run folder (nothing
trained). Tests that need torch are skipped when it is missing, the MPS and CUDA hardware tests
without that hardware, and the cached-Qwen tokenizer test when the pinned snapshot is not in
`HF_HUB_CACHE`; a skip is not a pass.

A strict outer deadline is optional: send SIGINT first (the runner records the interrupt,
writes `runner_end.json` and its summary), then SIGKILL after a grace period; after a kill, run
`summarize`, which reports the run as interrupted.

## CUDA profile (one NVIDIA GPU)

`configs/calibration-cuda.json` is the frozen recipe with `model.device` `cuda` and its own
`name`, nothing else. It shares dataset and design with `calibration.json`, so copy the reviewed
`<PREPARED>` folder and reuse its manifest hash (preparing again elsewhere can change the hash:
the manifest records the Python version). Expects Linux with exactly one visible NVIDIA GPU; a
CUDA build of `torch==2.8.0` with the other `requirements.lock` pins unchanged (that lock
was frozen on macOS with Python 3.11.15; retain the actual Linux package freeze and hardware
metadata with each run); and the pinned
snapshots already in the Hugging Face cache (the runner never downloads).

```sh
export CUBLAS_WORKSPACE_CONFIG=:4096:8   # before Python starts; :16:8 is also accepted
export CUDA_VISIBLE_DEVICES=0            # only if the host shows more than one GPU
CFG=experiments/minimal_safety/configs/calibration-cuda.json
<PY> -m pytest -q -rs experiments/minimal_safety/tests  # the two CUDA tests must pass, not skip
<PY> -m experiments.minimal_safety plan --config $CFG --prepared <PREPARED>
<PY> -m experiments.minimal_safety run --config $CFG --prepared <PREPARED> --run-dir <RUN> \
    --manifest-sha256 <SHA256 of the reviewed manifest>
<PY> -c 'import json, sys; from experiments.minimal_safety.model import adapter_difference as d; print(json.dumps(d(*sys.argv[1:])))' \
    <RUN>/adapters/202-a0-step4.safetensors <RUN>/adapters/202-remove_pc_unsafe8-step4.safetensors
```

Before loading anything, the runner refuses (run incomplete, exit 1; use a new `<RUN>`) unless
`CUBLAS_WORKSPACE_CONFIG` is `:4096:8` or `:16:8`, `TORCH_ALLOW_TF32_CUBLAS_OVERRIDE` is unset
(or `0`) and CUDA shows exactly one device. It then turns on deterministic algorithms (an operation
without a deterministic CUDA implementation raises; it does not warn), cuDNN determinism without
benchmarking, and float32 matmuls without TF32 in cuBLAS and cuDNN, and refuses if these do not
read back. `frozen/assets.json` (`environment.cuda`) records the GPU, compute capability,
multiprocessors, memory, CUDA runtime, cuDNN, driver line, these settings and the environment
variables that can change them. Stages are timed between `torch.cuda.synchronize()` barriers;
each ledger stage records PyTorch caching-allocator bytes at its end and the peak since the
previous stage record (not device-wide use). Evaluation and the gradient cosine restore the CPU
and CUDA RNG states.

Limits. CUDA, MPS and CPU kernels differ: no cross-device numerical equality is claimed, so never
pair CUDA artifacts with MPS or CPU runs, and never reuse timings across devices. The settings
target bitwise repeatability for identical inputs on one GPU and software stack; the real-model
check is the data-identical pair (seed 202 at step 4, per `plan --prepared`). Both arms start
from the same adapter and train on the same rows, so the last command should print
`"bitwise_identical": true` with fingerprints equal to the two step-4 checkpoint records in
`records.jsonl`, and either file compared with `<RUN>/adapters/202-init.safetensors` should
differ (training moved it). If the pair differs, investigate an implementation difference or
nondeterminism before reading the run. Provider time (setup, downloads, tests, cleanup) is outside
the 900 s scientific cap. This is engineering evidence only: it cannot show attribution decision
value, novelty, a safety benefit or ICML readiness.

## What a run does

1. **Freeze.** Refuses a non-empty run folder (no resume) and a manifest whose hash differs
   from `--manifest-sha256`; copies config, manifest and rows to `frozen/` and writes the exact
   per-step example IDs of every arm (`plan.json`) before any model is loaded.
2. **Assets.** Pinned snapshot folders only: `local_files_only=True`, `trust_remote_code=False`,
   safetensors only, `HF_HUB_OFFLINE=1`; float32, eager attention; no model or device fallback.
   The trainable count must equal 540,672 (rank-8 q/v LoRA on Qwen2.5-0.5B-Instruct).
3. **Inputs.** Tokenizes every row (truncations recorded), after checking that every frozen
   prompt encodes exactly like the tokenizer's own chat template (any difference stops the
   run), and scores all training responses with toxic-bert (the removal group's content
   scores; descriptive).
4. **Per seed** (101 then 202): one seeded adapter (`lora_B = 0`) is saved; each arm restores
   it (fingerprint checked), builds a fresh AdamW, trains steps 1–4, checkpoints, evaluates,
   continues to step 16, checkpoints, evaluates. After a0, the gradient cosine is computed on
   the a0 step-16 model. Then the optional base evaluation (adapter `B = 0`) runs last.
5. **End and summary.** A final cap check, then `runner_end.json` (stop reason, elapsed time),
   written only by a runner that ended rather than being killed. Then `summary.json` and
   `report.md`, always, with status `complete` or `incomplete`, plus `audit/blind.jsonl` and
   the separate `audit/mapping.jsonl`.

## Completion and verification

`summarize` (run by the runner itself and by the CLI) recomputes, never reprints. A run is
`complete` only if `runner_end.json` exists with no stop reason and an elapsed time inside the
wall cap; the outputs are inside the byte cap; the frozen config, manifest, rows and plan match
`frozen/hashes.json`; no stage failed; and every planned unit verifies: one successful stage
and exactly one record each for loading, tokenization (role sizes), input scores (exactly the
training rows), each seed's initial adapter (step 0, file hash), each arm start (that
adapter's fingerprint), each checkpoint (planned step, file hash, initial fingerprint, trained
IDs equal to the frozen stream), each evaluation (planned step, file hash, exactly the frozen
evaluation and holdout prompt IDs and roles) and each attribution (a0 step 16, frozen query
and group IDs, finite cosine). A missing record fails its unit. Without `runner_end.json` the
run is recovered as interrupted: an unterminated final line of a log is dropped and listed;
any other malformed line, or any torn line once the runner ended, is reported as corruption.
Per-evaluation `completions/*.jsonl` files are always parsed strictly.

## Definitions

- **Arms.** `a0` keeps all 128 calibration rows; `remove_pc_unsafe8` deletes a predefined
  positive-control group of 8 Unsafe rows (drawn by the design seed before any score or outcome
  exists; not attribution-selected).
- **Sampler.** Batch 1. Each epoch shuffles the full calibration set with a (seed, epoch) stream
  and the removal arm drops the removed rows, so arms share order and removal deletes rows
  (kept rows move forward) rather than masking steps. At fixed steps removal therefore changes
  which retained rows are seen. `plan` reports how many removal-group rows a0 sees by each
  checkpoint and the first step where the arms' data differ. Up to that step the arms share
  data, initial adapter and a fresh optimizer, so their adapters should be bit-identical; the
  report flags any such pair whose adapters differ, to be investigated as an implementation
  difference or numerical nondeterminism, not assumed to be device noise.
- **Tokens.** The template head and the user text are encoded together, so a merge across
  that join is the template's own (a user message starting with a newline merges with the
  head's final newline; the root preflight check measured one extra token from the earlier
  separate encoding for prepared row `train:10158`, which the frozen streams do not sample).
  The response is encoded separately after the assistant header, which is the boundary
  generation sees; the preflight found no prepared response starting with whitespace, and the
  run counts them in its tokenization record.
- **Loss.** Per example, mean next-token NLL over response tokens plus the end-of-turn token
  (example weighting). Prompt and template tokens are unlabelled. Long user text is cut from
  its end with `min(len(target), 128)` positions reserved for the target; the template is never
  cut; long responses are cut last. Constant learning rate, so steps 1–4 are exactly the short run.
- **Evaluation.** Greedy decoding (no logits processors), 64 new tokens, stop at
  `<|im_end|>`/`<|endoftext|>`; only generated tokens are scored. Evaluation runs in eval mode
  under `no_grad` with RNG state and train mode restored, so it cannot change training.
  CLASSIFIER PROXY: sigmoid of toxic-bert's `toxic` logit and the share ≥ 0.5 on the toxic
  evaluation prompts. DIAGNOSTICS: teacher-forced NLL of the reference responses (toxic and
  benign), a refusal-phrase flag, empty outputs, generated length and 5-gram prompt copying.
- **Gradient cosine.** `cos(mean_q g_q, mean_z g_z)` over the explicit LoRA parameter vector
  (float64), with `g` the gradient of one example's response-only loss at the a0 step-16 model
  in eval mode (RNG state restored, as in evaluation); `q` are the query reference rows with
  their provided toxic responses, `z` the removal group. A cosine of means, not a mean of
  cosines. Positive means a small descent step
  on the group's loss would, to first order, also lower the query responses' loss. Zero or
  non-finite gradients are rejected. It is a noncausal description from the same seed's model,
  not SOURCE, LESS, an influence function or a removal-effect prediction.
- **Costs.** Stage seconds with a device barrier at both ends (`ledger.jsonl`).
  `full_run_train = train_short + train_continue`; `full_run` adds `eval_long`;
  `selector_path` also adds `eval_short`; one-off and per-seed (adapter initialization,
  attribution) stages are reported separately. Stages stopped by a cap, error or interrupt are
  listed as spent time with their progress, never as completed units or inside totals. Train
  stages include their checkpoint write; `steps/*.jsonl` has per-step seconds without it (use
  warm medians: the first steps include device warm-up).
- **Caps.** 900 s scientific wall time and 2 GiB output (cached assets excluded). Cooperative
  checks run at every stage entry and before each work item: model weight loading and LoRA
  wrapping, classifier batch, optimizer step, generation prompt pass and each further token,
  teacher-forced NLL, per-example gradient and file save; once more after the last unit; and
  again in `summarize` from the recorded elapsed time and the output size. An arm is not
  started if the previous arm's measured time would pass the cap; arms are never shortened.
  One operation already in progress (a weight load, a forward/backward pass, a decoding step,
  a classifier batch, a checkpoint write, or the tokenization stage, which has no per-row
  checks) can still finish past the cap; that run is then incomplete, with the overshoot
  visible. A stopped stage records the last work item it checked (`last_item`).

## Outputs (`<RUN>/`)

`frozen/` (config, manifest, rows, plan, hashes, assets with cached blob IDs and versions),
`status.json`, `ledger.jsonl`, `records.jsonl`, `steps/<seed>-<arm>.jsonl`,
`adapters/*.safetensors`, `completions/<seed>-<arm>-<ckpt>.jsonl`, `runner_end.json`, `audit/`,
`summary.json`, `report.md`, and `error.txt` on failure. Comparisons are descriptive
removal-minus-a0 differences for (seed, checkpoint) pairs where both arms verified at the
planned step on the same prompts; the `conclusion` field is fixed text. The manual blind audit
is pending until a person labels it.

## Verified first CUDA run — 2 October 2026

The A5000 profile passed80tests with one MPS-only skip and completed the full calibration in256.13seconds process time. The actual seed202 short adapter pair matches bitwise and differs from initialization. The pod was deleted after artifact retrieval. Measurements and remaining scientific limits are in the [dated result note](../../research/experiments/2026-10-02-minimal-safety-calibration-results.md). This supersedes the author's original untested-platform status; it does not validate the safety scorer or the paper's hypothesis.
