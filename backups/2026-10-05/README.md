# Private research backup: 5 October 2026 (headroom positive control, round 1)

These are the records of round 1, in the private draft release `backup-2026-10-05`. [Open the private draft backup release](https://github.com/4r4cn1d0/attribution/releases/tag/untagged-2945ff2a4227c846d5ce).

- **`headroom-round1-units.tar.gz`:** every retrieved unit tree, **without model states** (`.safetensors`). It holds the results, evaluation files, receipts, ledgers and the lead host's scores and rewrites.
- **`headroom-round1-records.tar.gz`:** orchestration records. Pod address files, `known_hosts` and timer settings are left out.
- **`headroom-round1-edits-analyses.tar.gz`:**
  - the four round-1 edit files and the early copies;
  - the decisions log, the results table, and the noise and regrade analyses;
  - the plan and the recorded A100 fixture.
- **`inventory.jsonl`** lists all 601 files with their SHA-256. `SHA256SUMS` and `manifest.json` cover the assets.
- **Checks:**
  - **Secret scan:** it found no credential pattern, none of this run's pod IP addresses and no SSH key material (`secret-scan.json`).
  - **Download-back check:** every asset was downloaded back and matched its size and SHA-256 (`upload-verification.json`).
- **Not included:**
  - The model states. Six units' states (about 18 GB) remain only on the laptop under `tmp/headroom-20261005/retrieved/`. The rewrite units' states were not copied, and their pods were deleted.
  - The prepared data, including the hidden bank, and any secret.

Results write-up: `research/experiments/2026-10-05-headroom-round-1-results.md`.

These assets are **private**. They include model outputs to unsafe prompts; do not publish them.
