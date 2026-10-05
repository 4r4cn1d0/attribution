# Integration review: headroom-engine-2-20261005

5 October 2026. Reviewed and integrated by General Implementation. Brief: [headroom-engine-2-20261005](../../briefs/headroom-engine-2-20261005.md) (and an addendum by message: a final rewrite config, the exact CLI lines, the fixture keys, and the e3-only question).

## Scope

- Workspace `tmp/claude-workspaces/headroom-engine-2-20261005/workspace`, a manual copy at `4c4c75b`.
- Against its manifest:
  - 10 files changed: `README.md`, `__main__.py`, `config.py`, `engine.py`, `headroom.py`, `loaders.py`, `textproc.py`, `tests/ss_fixtures.py`, `tests/test_ss_headroom.py`, `scripts/cuda_preflight_headroom.py`;
  - 2 configs added: `study-v3-headroom-pc-20261005.json` and `headroom-rewrite-pc-20261005.json`;
  - 1 config deleted: the never-run draft recipe.
- All are inside the owned paths, and every hash matches the worker's report. The repository's files were unchanged since the copy.

## What it adds

- **Trained chat-token rows** (`model.lora.trainable_tokens`), through PEFT 0.17.1 `trainable_token_indices`.
  - With tied embeddings, one float32 parameter serves both the input and the output side and is counted once: 73,859,072 + 2 × 1,536 = 73,862,144.
  - The rows start from the base model's own rows. They are saved, restored and fingerprinted like every adapter tensor.
- **The positive-control recipe** `study-v3-headroom-pc-20261005`:
  - `config_sha256` `3b50a4e6fe0055f3b4b9ca8e48fe970d62340e3a7dab79d556dc93d5b50155d5`;
  - training identity `b952ed4401153e19cffb60840c636b94cc90beba04ab2490dc3a14b2169f8e7b`.
- **The final rewrite config** `headroom-rewrite-pc-20261005`: the draft's generator and prompts, with its purpose marked frozen.
- **The random-rewrite control:**
  - one rewrites file covers the union of the top and the random 10%;
  - `random-rewrite-10` uses exactly the rows of `random-remove-10`;
  - `build-edits --round 1` writes only the four round-1 files.
- **The preflight** now records each chat-token row against the never-used padding rows. It **asserts** that after two steps the trained rows are no longer bit-identical to any padding row, on the input and the output side.

## Checks run here

| Check | Result |
|---|---|
| Engine suites (`safety_selection`, `minimal_safety`) | 249 passed, 3 CUDA-only skips, exit 0 |
| Stage B | 172 passed, exit 0 |
| Durability | 260 passed, exit 0 (432 with Stage B) |
| Golden regression (group-removal and a0 runs equal the `8dd630c` engine) | passes unchanged |
| Engine code identity | `616d66d0a7d36b806967a25ccc5a0edc402329197942448d8001a1acb726247a`, as reported |

## Review notes

- **The tied-fixture proof covers both directions.**
  - With LoRA alone, the chat tokens' logits stay bit-equal to the padding rows', and greedy decoding never emits `<|im_end|>`.
  - With trained rows, the rows separate on both sides, and generation stops at `<|im_end|>`.
- **The worker's weakest assumption:** in bf16, two optimizer steps at lr 2e-4 might leave a trained row bit-identical to the padding rows. The preflight's assertion settles this on the first pod, before any matrix job.
- **An e3-only calibrate equals the q → e1 → e3 chain at e3 on the fixtures:** the same state fingerprints and byte-identical e3 evaluation files, with and without token rows. Round 1 evaluates e3 only, as the frozen reading does.
- **The old draft rewrite config is kept.** A test checks that the final config equals it except for name and purpose.

Nothing ran on a GPU here.
