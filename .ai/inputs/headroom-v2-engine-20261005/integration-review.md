# Integration review: headroom-v2-engine-20261005

5 October 2026. Reviewed and integrated by General Implementation. Brief: [headroom-v2-engine-20261005](../../briefs/headroom-v2-engine-20261005.md). It was built in two parts; the decisions on the Priority A review were folded in before the final report.

## Scope and identity

- **Changes:** 10 files added and 12 changed, all inside `experiments/safety_selection/**` and `scripts/`. Every hash matches the worker's final report, and the repository's files were unchanged since the copy (`3d01441`).
- **Engine code identity:** `0d55658c16b9ef4b31b02740402a1168c3de1156004b1d669219654da4cb7011`.
- **New recipes:** `study-v3-headroom-pc2-20261005` (SDPA, micro-batch 8 × 1), with the fallbacks `-mb4` (SDPA, 4 × 2) and `-eager` (eager, 4 × 2).
- **New rewrite configs:** pc2 and pc2-eager, with a 2,048-token cap.

## Checks run here

| Check | Result |
|---|---|
| Engine suites (`safety_selection`, `minimal_safety`) | 269 passed, 3 CUDA-only skips, exit 0. Includes the golden regression, `test_ss_v3_data` (13) and `test_ss_v3_eval` (6). |
| Stage B | 172 passed, exit 0 |
| Durability | 260 passed, exit 0 |
| Re-preparing `prepared-v3-inj05` here from the pinned sources | manifest `bd1e40df260c07773b387a0cb2af30321a194213149c241007dc7e027e34a76c`, identical to the worker's |
| Re-preparing `prepared-v3-inj10` | manifest `3dee8d75488cd8098b21c4d97494d86135629e223ca8f811bea5c6579b394591`, identical to the worker's |

## What it adds

- **Prepared data v3:** PKU-SafeRLHF unsafe responses (severity ≥ 2), category-balanced over 19 categories and nested (507 ⊂ 1,015).
  - Exact and near-duplicate exclusion against every evaluation prompt (character 5-gram Jaccard ≥ 0.5). For inj10, 1 candidate was skipped.
  - Injected rows are in no group, and their metadata is in the auditor file only.
  - Every earlier output is byte-identical.
- **Banks, split by the engine; counts only:**
  - harm: 200 / 200 / 867;
  - over-refusal, stratified by source: development 50 XSTest + 50 OR-Bench hard; selector the same; hidden 150 + 1,219.
- **Evaluation:**
  - harm: greedy plus 3 sampled answers (T 0.7, seeded per job, prompt and sample; the global RNG is never drawn), Qwen3Guard labels on all, and continuous Unsafe scores;
  - over-refusal: the refusal rate;
  - per-prompt summaries.
- **Edit size k:** set by `--count N` or `--count injection`, recorded in each edit file.
- **Leakage errors** name ids only.

## Review notes

- **The worker's weakest assumption:** sampled answers on CUDA are reproducible only with the same batch shape and GPU type. The preflight compares batched with one-at-a-time sampling. A same-shape repeat on the pod settles determinism, and if it differs, the "deterministic" claim is dropped and the sampled rates are still estimates.
- **The over-refusal split between XSTest and OR-Bench** is joined from the auditor file at analysis time. Evaluation never reads the sources.

Nothing ran on a GPU here.
