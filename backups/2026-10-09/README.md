# Backups of 9 October 2026 (private draft releases)

Each folder holds the records of one private draft release on GitHub: `upload-verification.json` (download-back SHA-256 check, draft and private flags where recorded), `SHA256SUMS`, `manifest.json` and `secret-scan.json`. The local staging copies were moved to the macOS Trash after these records were saved.

| Release tag | What it holds |
|---|---|
| backup-2026-10-09-llama32-1b-recipe-g-seed-1102 | Llama-3.2-1B recipe G seed 1102 e1 (host llama32-1b-g-1102), fine-tune only on the recipe-B probe's untuned unit; the two-seed reading with seed 1101 and Granite (`reading-llama-g-1101-1102-granite.json`, merged Granite summary); pod kept stopped (its adapter is not in the release) |
| backup-2026-10-09-llama32-1b-recipe-g-seed-1103 | INTERIM (--allow-missing: no Granite reading yet; seed 1103 is not read until the user decides the common recipe). Llama-3.2-1B recipe G seed 1103 e1 (host llama32-1b-g-1103), its Granite items and summary, no reading; pod kept stopped |
| backup-2026-10-09-olmo2-1b-g5e5 | INTERIM (no Granite yet). OLMo-2-1B rung 2 (recipe G at LR 5e-5) seed 1101 e1 (host olmo2-1b-g5e5-1101) and its reading without the second judge; pod kept stopped |
| backup-2026-10-09-olmo2-1b-g5e5-seed-1102 | INTERIM (no Granite yet). OLMo-2-1B rung 2 seed 1102 e1 (host olmo2-1b-g5e5-1102) and the two-seed reading without the second judge; pod kept stopped |
| backup-2026-10-09-llama32-1b-g5e5 | INTERIM (no Granite yet). Llama-3.2-1B rung 2 seed 1101 e1 (host llama32-1b-g5e5b-1101, attempt 2) and its reading without the second judge; attempt 1's records (bootstrap failure) and the kit's bootstrap fix; pods kept stopped |
| backup-2026-10-09-olmo2-1b-g5e5-granite | FULL (supersedes the interim olmo2-1b-g5e5): OLMo rung 2 seed 1101 with Granite and the reading with the second judge |
| backup-2026-10-09-olmo2-1b-g5e5-seed-1102-granite | FULL (supersedes the interim olmo2-1b-g5e5-seed-1102): OLMo rung 2 seed 1102 with Granite and the two-seed reading with the second judge |
| backup-2026-10-09-llama32-1b-g5e5-granite | FULL (supersedes the interim llama32-1b-g5e5): Llama rung 2 seed 1101 with Granite and the reading with the second judge |

Model weights (.safetensors) are not in these releases.
