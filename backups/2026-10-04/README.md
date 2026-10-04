# Private research backup — 4 October 2026 (dev-matrix-002)

The verified results of the development-matrix run of 4 October 2026, in the private draft release `backup-2026-10-04`.

[Open the private draft backup release](https://github.com/4r4cn1d0/attribution/releases/tag/untagged-c9c14f324928c236d4a7).

- **Thirteen per-host archives**, about 80 MB each. They hold every verified unit (78 of 78 passed the engine's `verify`), the job receipts, and each host's bootstrap and A100-fixture verification.
- **One records archive.** It holds the logs, the orchestration records (pod IP addresses and ports removed) and the results tables.
- **`inventory.jsonl`** lists every file with its SHA-256, and `SHA256SUMS` covers the assets.
- **Checks.**
  - The scan of all 1,979 files found no credential pattern, none of this run's pod IP addresses and no SSH key material (`secret-scan.json`).
  - Every asset was downloaded back and matched its size and SHA-256 (`upload-verification.json`).
- **Results write-up:** `research/experiments/2026-10-04-dev-matrix-002-results.md`. The run scripts are in `.ai/inputs/study-v2-20261004/run-scripts/`.

These assets are **private**. They include model outputs to unsafe prompts; do not publish them.
