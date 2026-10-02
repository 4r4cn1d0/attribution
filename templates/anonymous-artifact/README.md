# Attribution for safety data edits: stage-A code and protocol

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
(matched-cost decision value); nothing in this package performs either test.

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
- **Stage B** (selector, menus and held-out analysis) is not part of this package.
- The initial study is incomplete. There are no held-out results, and no completed
  larger-study evidence is available or included. Configs and documents record development
  decisions dated October 2026; they are not a frozen confirmatory protocol.

## Layout

| Path | Contents |
| --- | --- |
| `experiments/safety_selection/` | stage-A engine: modules, `configs/`, `tests/`, README |
| `experiments/minimal_safety/` | calibration slice: modules, `configs/`, `tests/`, README, `requirements.lock` |
| `research/experiments/safety-selection-v2-protocol.md` | stage-A protocol (draft) |
| [`ARTIFACT_MANIFEST.json`](ARTIFACT_MANIFEST.json) | SHA-256 of every file and how it derives from the development copy |

Python, JSON and lock files are unchanged from the development copies. A few documentation
passages that pointed to internal planning or run records, or stated what had been run during
development, were replaced or removed; the manifest lists each change. Module docstrings, config notes and test docstrings may still name
internal records (for example `public-metadata/…` audit files) that are not included.

## Running the tests

Python 3.11 with the pins of
[`experiments/minimal_safety/requirements.lock`](experiments/minimal_safety/requirements.lock)
(the GPU paths need a CUDA build of PyTorch; see each README). From the repository root:

```sh
python -m pytest -q -rs experiments/minimal_safety/tests
python -m pytest -q -rs experiments/safety_selection/tests
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
