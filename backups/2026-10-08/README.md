# Backups of 8 October 2026 (private draft releases)

Each folder holds the records of one private draft release on GitHub: `upload-verification.json` (download-back SHA-256 check, draft and private flags where recorded), `SHA256SUMS`, `manifest.json` and `secret-scan.json`. The local staging copies were moved to the macOS Trash after these records were saved.

| Release tag | What it holds |
|---|---|
| backup-2026-10-08-qwen-r16 | Qwen2.5-1.5B rank-16 test (pod r16-1101; pod deleted after this backup) |
| backup-2026-10-08-olmo2-1b-probe | OLMo-2-1B probe: untuned unit and seed 1101 e1, readings, Granite |
| backup-2026-10-08-olmo2-1b-gate-a-seed-1102 | Gate A seed 1102 (fine-tune only) |
| backup-2026-10-08-olmo2-1b-gate-a-seed-1103 | Gate A seed 1103 (fine-tune only) |
| backup-2026-10-08-olmo2-1b-gate-a | The formal Gate A result (gate-a-olmo2-1b.json, merged Granite summary, gate_a_olmo.py) with the probe records |

Model weights (.safetensors) are not in these releases; the OLMo adapters remain on the stopped pods olmo2-1b-1101, -1102 and -1103.
