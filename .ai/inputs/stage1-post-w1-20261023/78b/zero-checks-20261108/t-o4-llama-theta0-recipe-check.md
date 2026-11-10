# T-O4: Llama-3.1-8B θ0's recipe against MAIN_F (generation and guard blocks)

Measured 2026-11-08 at about 15:31 UTC by GI XI (GXB T-O4). Command: `.venv/bin/python -I -B` with PLAN-AB §5 C3's
expression (`sha256_bytes(canonical_json(recipe[block]))` after `load_recipe`), over every
`experiments/safety_selection/configs/study-kt-llama31-8b-*.json` at HEAD `3481d85`; exit 0.

| config file | config SHA-256 prefix | generation | guard |
|---|---|---|---|
| study-kt-llama31-8b-r64-b-mb2-20261008.json (LR 1e-4; θ0's unit, P1's table) | c5462c77 | 5ddced7af22b (= 1B pin) | a7f0755b795f (= 1B pin) |
| study-kt-llama31-8b-r64-b5e5-mb2-20261010.json (MAIN_F) | 74758af1 | 5ddced7af22b (= 1B pin) | a7f0755b795f (= 1B pin) |
| study-kt-llama31-8b-r64-g-mb2-20261011.json (G, LR 1e-4) | 442f133f | 5ddced7af22b | a7f0755b795f |
| study-kt-llama31-8b-r64-b-mb1-gc-20261008.json | 75309f61 | 5ddced7af22b | a7f0755b795f |
| study-kt-llama31-8b-r64-b-mb1-gc-eager-20261008.json | 4af1b260 | 5ddced7af22b | a7f0755b795f |
| study-kt-llama31-8b-r64-b-mb4-20261008.json | 7d1c092f | 5ddced7af22b | a7f0755b795f |

1B pins (`scripts/stage1_s1/settings/oext_unit.json` `recipes`): generation `5ddced7af22b968f…`, guard
`a7f0755b795f0ac4…`. **Result:** θ0's recipe `c5462c77…` has the same generation and guard blocks as MAIN_F
`74758af1…`, so Llama's θ0 unit is used for W1-18 (T-O4's condition holds). Only blocks' hashes were read.
