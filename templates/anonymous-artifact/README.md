# Attribution for safety data edits: stage-A and stage-B code and protocols

Code and protocol for a study of whether training-data attribution adds decision value when
choosing which predefined groups of fine-tuning data to remove for safety. This package is
review scaffolding: it contains no datasets, model weights, run outputs, checkpoints or
results, and it makes no empirical or novelty claim.

## Question

In one fixed supervised fine-tuning setting, does adding training-data attribution to a
selector that already uses edit metadata, content-classifier scores and short training runs
improve its choice among removals of predefined data groups, compared with spending
attribution's measured cost on more training runs? In the package documents, `a0` is training
on the unchanged data and a removal arm deletes one predefined group. Documents and configs
refer to the study's planned hypothesis tests as H1 (a development screen) and H2
(matched-cost decision value), and to its planned estimand of attribution's added decision
value as D_info; nothing in this package performs either test or estimates D_info. In stage B,
S- and S+ are the two selection policies that are compared: the same acquisition and choice
algorithm without and with one attribution feature.

## Status

- **Stage-A engine** ([`experiments/safety_selection/`](experiments/safety_selection/README.md)):
  data preparation with leakage controls, resumable LoRA training through several checkpoints,
  checkpoint evaluation (query loss, generation, a pinned guard model, ARC-Easy forced choice),
  guard features of training rows, two checkpoint-gradient attribution variants and a
  whitelisted selector-input view. It defines no endpoint, margin, selector or held-out
  analysis. Its tests use engineering fixtures on CPU (tiny random models, byte-level
  tokenizers, a scripted guard), apart from a CUDA preflight test that runs only on a GPU host.
  Protocol (draft): [safety-selection-v2-protocol.md](research/experiments/safety-selection-v2-protocol.md).
- **Calibration slice** ([`experiments/minimal_safety/`](experiments/minimal_safety/README.md)):
  one small end-to-end a0/removal run that produces engineering evidence only (does the
  pipeline work, what does each stage cost). The stage-A engine reuses its helpers and its
  pinned environment.
- **Stage-B decision-policy package**
  ([`experiments/safety_decision_policy/`](experiments/safety_decision_policy/README.md)): the
  two selection policies, a fixed acquisition schedule and choice rule, a block controller with
  write-once records and a choice lock before any final-bank access, quoted and reconstructed
  cost ledgers, and an analysis of the paired fresh-deployment contrast with its cost margin. It
  is an exploratory finite-menu diagnostic, not a confirmatory test, and it has produced no
  results: its tests and its `simulate` exercise use engineering fixtures only (a synthetic world
  with a fake backend, and the engine's CPU fixtures). It has its own code identity, separate
  from the stage-A engine's.
  Protocol (draft): [safety-selection-v2-decision-protocol.md](research/experiments/safety-selection-v2-decision-protocol.md).
- The initial study is incomplete. There are no held-out results, and no completed
  larger-study evidence is available or included. Configs and documents record development
  decisions dated October 2026; they are not a frozen confirmatory protocol.

## Study plan by stage

Each stage runs under rules that we freeze before we see its outcomes. Status words: done, running, planned, waiting on funding. This section gives no outcome of stage 1 or later.

### The question

Fine-tuning an aligned language model on benign data can make the model less safe ("erosion"). Which data repair restores the most safety for the compute that it uses? A repair must not make the model refuse too many harmless requests ("over-refusal") or lose too much task skill. Repairs that change no data set the bar. Does a paid diagnosis ever beat the same compute spent on more training runs? Does the answer change with the size of the menu and with the model family?

### What the study compares

Data repairs, each a fixed rule written before the runs:
- **R**: remove 600 random rows of the 4,800 training rows.
- **A1**: remove the 600 rows that a training-data attribution score ranks highest (gradient similarity to harmful and safe examples).
- **L1**: remove 600 rows by a representation filter in the style of the published LARF method.
- **H1**: remove the 600 rows with the shortest answers (a free rule).
- **S1, S3, S4**: add 48 safety rows (1% of the data): random public refusals (S1); rows selected in the style of the published DataRx method (S3); the untuned model's own refusals (S4).

Reference points (no data change): a safety instruction in the prompt; the fine-tuned low-rank adaptation (LoRA) adapter, scaled down; a standard training recipe; a constrained loss from prior work; Safe LoRA. A data repair "beats model-level repair" only if it beats every reference point.

Diagnostics, each charged its measured cost: a content classifier, representation similarity, training-data attribution, a free answer-length score, short trial runs.

Measures:
- **U** (primary): the share of unsafe answers (Qwen3Guard judge) over 600 sampled answers to 200 harmful prompts.
- **Judges**: a "harm" sentence needs the HarmBench classifier to agree in sign and in at least half the size; otherwise it says "restored refusal". Granite Guardian is a second, reported judge.
- **O**: the over-refusal share on 500 harmless prompts.
- **L**: the loss on 200 held-out task rows.
- **Cost**: graphics processing unit (GPU) seconds by stage.

### Gate A: is there erosion to repair?
- **Runs**: each model, fine-tuned for one epoch with LoRA on 4,800 Dolly rows (8 categories of 600); 3 seeds; the untuned model.
- **Measures**: the rise in U; whether answers end; task skill.
- **Feeds**: the training recipe, and the go decision for Gate B.
- **Status**: done for OLMo-2-1B-Instruct and Llama-3.2-1B-Instruct.

### Gate B: does the erosion come from a few categories?
- **Runs**: OLMo-2-1B-Instruct. Each arm removes one category of 600 rows, against random removal of 600 rows. Waves: a noise check, a diagnostics pass over all rows, all 8 categories at one seed, then the top categories at 2 more seeds.
- **Measures**: the extra restoration from removing one category, against a floor of 8 percentage points (pp).
- **Feeds**: a verdict (LOCALIZED, DIFFUSE or TOO CLOSE) that selects the later branch. A blinded rule on the noise estimate sets the stage-1 seed count.
- **Status**: done. Its frozen reading set the later branch and the stage-1 seed plan.

### Gate C: do the diagnostics find the category?
- **Runs**: none; each diagnostic's ranking of the 8 categories was sealed before Gate B's main wave.
- **Feeds**: attribution against representation similarity, read only after a LOCALIZED Gate B.
- **Status**: rankings sealed.

### Stage 1: the repair comparison on OLMo-2-1B-Instruct
- **Runs**: the unchanged-data arm (a0) and R at 7 seeds; A1, L1, H1, S1, S3 and S4 at 6 seeds each (44 new runs). The reference points use the same seeds.
- **Measures**: six primary contrasts: A1, L1 and H1 against R; S1 against a0; S3 and S4 against S1. The smallest effect of interest is 5 pp of U. A frozen script gives each contrast one label: better, equivalent, worse or inconclusive. A fixed testing procedure controls false "better" and "worse" claims at about 5%. The over-refusal limit is 5 pp above the untuned model.
- **Feeds**: the headline: each repair's label, over-refusal, task loss and cost.
- **Blocks**: a block starts on a funding event, never on an outcome. Only complete blocks are analysed.
  - Block A: the six repairs at seeds 1102–1104, a0 and R at 1104, and the diagnostics passes. Status: done. Its outcomes stay sealed until block B is complete.
  - Block B: every arm at seeds 1105–1107, and the reference points. Status: running. Its arm runs and first reference runs are done; its last reference runs are running or waiting on funding; its judge runs follow.
- **Judges**: HarmBench and Granite Guardian judge each block in separate GPU jobs.
- **Reading**: after block B, the frozen script reads all blocks together (planned).
- **Secondary, model-based**: a simulated selector predicts what diagnosis is worth against trial runs at equal budget. Predictions committed before Gate B's main wave (done); scored in stage 2 (planned).
- **Human label check**: two blind raters rate about 450 answers. Status: waiting on funding.

### Stage 1b: a planted cause (positive control)
- **Runs**: plant 37 safe, non-refusing answers to harmful prompts in one cell, in menus of 8, 32 and 128 cells. A 3-seed pilot decides on the main sweep.
- **Measures**: how well each diagnostic ranks the planted rows; what trial runs alone pay to find the cell.
- **Status**: planned; waiting on funding.

### Stage 1c: secondary arms
- **Runs**: 3 seeds each, in a fixed order: larger random removals; random removal plus S1; a DataShield-style filter; more format rules; token-matched random removal.
- **Measures**: the random dose that each filter equals.
- **Status**: planned; waiting on funding.

### Stage 2: a second 1B model family
- **Runs**: Llama-3.2-1B-Instruct. A smaller Gate B tests the selector's predictions. The primary contrasts run again, with a margin scaled to this family's erosion.
- **Feeds**: the claim "replicates across two families" (same sign, and a difference below its detectable size).
- **Status**: Gate A done; the rest planned, waiting on funding.

### Stage 3: confirmation
- **Runs**: at most 2 contrasts per family, picked by a frozen rule, on fresh seeds and a sealed, held-out set of 200 harmful prompts.
- **Status**: planned.

### Later: larger models and a second data set
- 7–8B: OLMo-2-7B-Instruct and Llama-3.1-8B-Instruct (probes fixed their learning rates: done), and OLMo 3 7B Instruct if funded. This tier has its own pre-registration (a draft).
- A second benign data set (Alpaca), and a headline check at about 32B (70B if funded).
- **Status**: planned; waiting on funding.

### What this repository contains
- **Stage-A engine** (`experiments/safety_selection/`): an early version of the training, evaluation and attribution engine. Later versions run Gates A, B and C and stage 1.
- **Stage-B decision-policy package** (`experiments/safety_decision_policy/`): from the study's earlier design; selection policies without and with an attribution feature. No stage above runs it; the stage-1 selector is separate code.
- **Calibration slice** (`experiments/minimal_safety/`): engineering evidence only.
- Later-stage code (run kit, reading script, selector, engine updates) will be released at submission.

## Layout

| Path | Contents |
| --- | --- |
| `experiments/safety_selection/` | stage-A engine: modules, `configs/`, `tests/`, README |
| `experiments/safety_decision_policy/` | stage-B decision-policy package: modules, `configs/` (engineering examples), `tests/`, README |
| `experiments/minimal_safety/` | calibration slice: modules, `configs/`, `tests/`, README, `requirements.lock` |
| `research/experiments/safety-selection-v2-protocol.md` | stage-A protocol (draft) |
| `research/experiments/safety-selection-v2-decision-protocol.md` | stage-B decision-policy protocol (draft) |
| [`ARTIFACT_MANIFEST.json`](ARTIFACT_MANIFEST.json) | SHA-256 of every file and how it derives from the development copy |

Python, JSON and lock files are unchanged from the development copies. A few documentation
passages that pointed to internal planning, review or run records, or stated what had been run
during development, were replaced or removed; the manifest lists each change. Module
docstrings, config notes and test docstrings may still name internal records (for example
`public-metadata/…` audit files) or internal review rounds (for example "third review C1")
that are not included.

## Running the tests

Python 3.11 with the pins of
[`experiments/minimal_safety/requirements.lock`](experiments/minimal_safety/requirements.lock)
(the GPU paths need a CUDA build of PyTorch; see each README). From the repository root:

```sh
python -m pytest -q -rs experiments/minimal_safety/tests
python -m pytest -q -rs experiments/safety_selection/tests
python -m pytest -q -rs experiments/safety_decision_policy/tests
```

Stage B also has a synthetic end-to-end exercise on its fake backend (CPU, no data, no model;
its numbers are engineering fixtures, not results). It writes a new folder:

```sh
python -m experiments.safety_decision_policy simulate \
    --config experiments/safety_decision_policy/configs/example-engineering.json \
    --spec experiments/safety_decision_policy/configs/example-dev-fit-spec.json --out <NEW_FOLDER>
```

Each README states which tests skip without particular libraries, hardware or cached assets; a
skip is not a pass. Nothing downloads implicitly: public datasets and models are fetched only
by the explicit `fetch`, `fetch-data` and `fetch-models` commands with
`--confirm-public-download`.

## Third-party data, models and software

The configs pin the exact revisions and file hashes of the public assets the code reads:

- DATE-LM toxicity/bias filtering data, ToxicChat-Het subset
  (`DataAttributionEval/Toxicity-Bias-Filtering`), whose rows its authors report as drawn from
  ToxicChat and UltraChat;
- ToxicChat (`lmsys/toxic-chat`, 0124 test split);
- ARC-Easy from the AI2 Reasoning Challenge (`allenai/ai2_arc`);
- Qwen2.5 Instruct models (`Qwen/Qwen2.5-1.5B-Instruct`, `Qwen/Qwen2.5-0.5B-Instruct`);
- Qwen3Guard (`Qwen/Qwen3Guard-Gen-4B`);
- toxic-bert (`unitary/toxic-bert`).

None of them is redistributed here. Each is governed by its own licence or terms of use, as
stated by its publishers at the pinned revision; use them under those terms and cite the
original works. The software dependencies (PyTorch, Hugging Face Transformers, Tokenizers,
PEFT, Accelerate, safetensors, huggingface_hub, NumPy, pytest and the pinned transitive
dependencies) keep their own licences.

No licence file for this package's own code is included.
