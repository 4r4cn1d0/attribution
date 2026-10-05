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
- **Added later the same day, at the user's choice: `headroom-round1-a0-e3-adapters.tar`** (591 MB, sha256 `4c58fdd33a18ab66…`).
  - It holds the two a0 final (e3) adapters, their RNG states and `state.json`, and the units' `COMPLETE.json`.
  - Each file was checked against its unit's `COMPLETE.json` before packing, and the archive was checked again after downloading it back (`a0-adapters-manifest.json`).
  - All other round-1 model states (69 files, about 18 GB) were then **deleted** at the user's instruction. The a0 adapters also remain on the laptop.
- **Not included:**
  - The other model states: deleted as above. The rewrite units' states were never copied, and their pods were deleted.
  - The prepared data, including the hidden bank, and any secret.

Results write-up: `research/experiments/2026-10-05-headroom-round-1-results.md`.

These assets are **private**. They include model outputs to unsafe prompts; do not publish them.
