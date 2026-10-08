# Backups of 8 October 2026 (private draft releases)

Each folder holds the records of one private draft release on GitHub: `upload-verification.json` (download-back SHA-256 check, draft and private flags where recorded), `SHA256SUMS`, `manifest.json` and `secret-scan.json`. The local staging copies were moved to the macOS Trash after these records were saved.

| Release tag | What it holds |
|---|---|
| backup-2026-10-08-qwen-r16 | Qwen2.5-1.5B rank-16 test (pod r16-1101; pod deleted after this backup) |
| backup-2026-10-08-olmo2-1b-probe | OLMo-2-1B probe: untuned unit and seed 1101 e1, readings, Granite |
| backup-2026-10-08-olmo2-1b-gate-a-seed-1102 | Gate A seed 1102 (fine-tune only) |
| backup-2026-10-08-olmo2-1b-gate-a-seed-1103 | Gate A seed 1103 (fine-tune only) |
| backup-2026-10-08-olmo2-1b-gate-a | The formal Gate A result (gate-a-olmo2-1b.json, merged Granite summary, gate_a_olmo.py) with the probe records |
| backup-2026-10-08-olmo2-1b-recipe-g | OLMo-2-1B recipe G (token-mean loss, warmup-cosine), seed 1101 e1, fine-tune only on the probe's untuned unit; reading with Granite (`reading-olmo-g.json`, merged Granite summary); pod olmo2-1b-g-1101 kept stopped |
| backup-2026-10-08-llama32-1b-probe | Llama-3.2-1B probe (recipe B): untuned unit and seed 1101 e1, the reading with Granite (`reading-llama.json`), Granite items and summary; pod llama32-1b-1101 kept stopped |
| backup-2026-10-08-llama32-1b-recipe-g | Llama-3.2-1B recipe G (token-mean loss, warmup-cosine), seed 1101 e1 (host llama32-1b-g5-1101), fine-tune only on the recipe-B probe's untuned unit; the reading with Granite (`reading-llama-g-granite.json`, merged Granite summary `second-judge-merged-g.json`); pod llama32-1b-g5-1101 kept stopped (its adapter is not in the release) |
| backup-2026-10-08-olmo2-1b-recipe-g-seed-1102 | OLMo-2-1B recipe G seed 1102 e1 (host olmo2-1b-g-1102), fine-tune only on the probe's untuned unit; two-seed reading with seed 1101 and Granite (`reading-olmo-g-1101-1102-granite.json`, merged Granite summary); pod kept stopped (its adapter is not in the release) |
| backup-2026-10-08-olmo2-1b-recipe-g-seed-1103 | OLMo-2-1B recipe G seed 1103 e1 (host olmo2-1b-g-1103), fine-tune only on the probe's untuned unit; two-seed reading with seed 1101 and Granite (`reading-olmo-g-1101-1103-granite.json`, merged Granite summary); also `gate-a-olmo-G.json`, the formal three-seed Gate A read at recipe G; pod kept stopped (its adapter is not in the release) |

Model weights (.safetensors) are not in these releases; the OLMo adapters remain on the stopped pods olmo2-1b-1101, -1102 and -1103.
