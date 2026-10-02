I've built the package, config, README, tests and protocol note, but I haven't run any of it. I only had file read/write tools, so nothing has been executed: no tests, no Python, no data preparation, no calibration. Every pass/fail below is still to be observed when you run it.

## Changed files (all new; no existing file modified)
- **Package** in `experiments/minimal_safety/`:
  - Code: `__init__.py`, `__main__.py`, `common.py`, `data.py`, `plan.py`, `text.py`, `ledger.py`, `report.py`, `model.py`, `run.py`. Everything except `model.py` and `run.py` uses only the standard library.
  - Config: `configs/calibration.json`.
  - Lock: `requirements.lock`, a verbatim copy of the supplied `environment.lock`.
  - `README.md`.
- **Tests** in `experiments/minimal_safety/tests/`: `conftest.py` (fixtures, all labelled ENGINEERING FIXTURE), `test_ms_data.py`, `test_ms_text.py`, `test_ms_report.py`, `test_ms_plan.py`, `test_ms_model.py`, `test_ms_run.py`.
- **Protocol note**: `research/experiments/minimal-safety-pilot.md`.
- I didn't create `experiments/__init__.py`, to stay inside the owned path; `experiments` therefore imports as a namespace package.

While tracing the code by hand I found and fixed four bugs:
- A successful run would have been reported as interrupted, because the last `status.json` still said "running".
- The check that decides whether the next arm fits the time cap included the attribution stage in a0's measured time, so it over-predicted.
- One test assertion could fail falsely, because a reference row also has `data_id` `r-2`.
- A file's final newline was counted as a blank line.

## Commands (project root; `<…>` are root-local paths)
```sh
CFG=experiments/minimal_safety/configs/calibration.json
<PY> -m pytest -q experiments/minimal_safety/tests
<PY> -m experiments.minimal_safety plan --config $CFG
<PY> -m experiments.minimal_safety prepare --config $CFG --train <RAW_TRAIN> --ref <RAW_REF> --out <PREPARED>
<PY> -m experiments.minimal_safety plan --config $CFG --prepared <PREPARED>
<PY> -m experiments.minimal_safety run --config $CFG --prepared <PREPARED> --run-dir <RUN> --manifest-sha256 <HASH from prepare, after review>
<PY> -m experiments.minimal_safety summarize --run-dir <RUN>
```
- `<PY>` is the prepared venv's interpreter.
- Set `HF_HUB_CACHE=<HF_CACHE>` if the cached model and scorer are not in the default cache.
- Put `<PREPARED>` and `<RUN>` under `tmp/`, which git ignores.
- Torch tests skip if torch is missing; a skip is not a pass.

## Acceptance criteria: all not tested
- **Brief items 1–7:** implemented. The main loop is `run.py:101`; the data rules are in `data.py:170`; the sampler is `data.py:308`; the cosine aggregation is `model.py:227`; matched comparisons and costs are `report.py:64` and `report.py:95`.
- **Brief item 8 tests, all written:**
  - leakage detection and raw-hash mismatch
  - label masking, truncation and no-target rejection
  - removed rows never sampled
  - identical adapter initialization within a seed (tiny random Qwen2, nothing downloaded)
  - the step-4 evaluation leaves training bit-identical
  - cosine sign, normalization and cosine-of-means aggregation
  - incremental vs total costs
  - incomplete or step-mismatched outputs produce no comparison
  - the dry run in a subprocess with sockets blocked and no heavy imports
  - two end-to-end tiny runs, one of them stopped by the time cap

## Decisions for you
1. **The arms will often be identical at this length.** With 128 rows, 8 removed and batch 1, the chance that a0 has seen none of the removed rows is about 0.77 per seed by step 4 and about 0.33 by step 16. In those cases the two arms train on identical data, and any difference only measures MPS nondeterminism. `plan --prepared` reports the exact exposure before launch. I recommend keeping 4/16 steps for this cost-measurement run and not picking seeds to force exposure.
2. **toxic-bert safetensors at the pinned revision is unverified.** If the snapshot has none, the run stops at `load_scorer` by design. `plan` lists the cached files first.
3. **The `data_id` exclusion may over-exclude.** If ref IDs are per-file row numbers, the rule removes some training rows harmlessly; the count is in the manifest.
4. **Recipe values are fixed in advance, not tuned:** lr 2e-4 constant, gradient clip 1.0, a 512-token cap with 128 reserved for the response, 64 new tokens, and a 0.5 classifier threshold.

## Known risks
- A few transformers/peft calls are unexercised against the real Qwen model:
  - Passing `logits_to_keep` through the LoRA wrapper. A shape check raises rather than silently computing a wrong loss.
  - `torch_dtype`. Float32 is asserted after loading.
  - The chat-template split. Only the real run exercises it.
- **Time cap.** MPS decoding speed is unmeasured and dominates the budget: 9 evaluations × 768 tokens. If it is slow, seed 202 ends up marked incomplete rather than being shortened. A stage with no internal cap check, such as model loading, can overrun the 900 s cap by its own length.
- **Early timings.** The first steps include MPS warm-up; use the per-step log to get warm medians.

## Answers to the four questions
- **Weakest assumption:** that this endpoint can move at all. A safety-tuned 0.5B model, 16 single-example steps (about one removed row expected), and 6 greedy prompts will likely give identical or base-like completions. For the study itself, the weakest assumption is that removal effects rise above seed noise in ways that toxic-bert scores don't already rank.
- **Simpler alternative:** measure only the teacher-forced NLL of held-out toxic responses. It is cheaper, continuous and needs no classifier. I kept generation because F is defined on completions and its cost is the main unknown; the NLL is included as a diagnostic.
- **Concrete counterexample:** a seed whose first 16 samples contain no removed row. A difference of zero is then guaranteed whatever those 8 rows do. Similarly, a high cosine for the Unsafe group can just reflect prompt similarity on a model that is still close to base; DATE-LM's safety-aligned distractors exist for exactly this case.
- **Observations that would change the plan:**
  - an arm costing more than about 225 s
  - the classifier proxy at 0/6 or 6/6 for both base and a0
  - data-identical arms that differ on MPS
  - blind-audit labels that disagree with toxic-bert
  - any stage that blocks the run

## Next 3 steps (depend on the measurements; not promises)
1. **By 6 Oct:** run the tests and the calibration (at most 900 s), then have a person label the blind export (about 1 hour).
2. **6–16 Oct:** freeze a development profile with training length T of at least one epoch, then run a0 and the positive control at 3+ seeds each. Cost ≈ 9 × (T·c_step + 2·c_eval), where c_step is the measured seconds per step and c_eval the measured seconds per evaluation.
3. **16 Oct–6 Nov:** only if the positive control beats seed noise at an affordable T, build 12–24 predefined groups and run the X0-only headroom check before any attribution screen. Cost ≈ S·(1+G)·(T·c_step + c_eval) + S·G·m·c_grad, where S is seeds, G groups, m rows per group and c_grad the measured seconds per example gradient.

I didn't use the ICML 2027 date because it isn't verified.
