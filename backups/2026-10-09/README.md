# Backups of 9 October 2026 (private draft releases)

Each folder holds the records of one private draft release on GitHub: `upload-verification.json` (download-back SHA-256 check, draft and private flags where recorded), `SHA256SUMS`, `manifest.json` and `secret-scan.json`. The local staging copies were moved to the macOS Trash after these records were saved.

| Release tag | What it holds |
|---|---|
| backup-2026-10-09-llama32-1b-recipe-g-seed-1102 | Llama-3.2-1B recipe G seed 1102 e1 (host llama32-1b-g-1102), fine-tune only on the recipe-B probe's untuned unit; the two-seed reading with seed 1101 and Granite (`reading-llama-g-1101-1102-granite.json`, merged Granite summary); pod kept stopped (its adapter is not in the release) |

Model weights (.safetensors) are not in these releases.
