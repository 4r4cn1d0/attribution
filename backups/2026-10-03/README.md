# Private research backup — 3 October 2026

Private backup of the local records added since the [2 October backup](../2026-10-02/README.md). The matching private GitHub release is a draft with tag `backup-2026-10-03`. It holds seven archives, `inventory.jsonl` and `SHA256SUMS`, 135 MB in all.

[Open the private draft backup release](https://github.com/4r4cn1d0/attribution/releases/tag/untagged-073d75aaeaec71de282e).

## What it covers

Every file under `tmp/` that was neither in Git nor byte-identical to a file in `backup-2026-10-02`:

- 2537 files are archived here.
- 932 files already in the 2 October backup are not uploaded again.

`inventory.jsonl` lists all 3469 paths with their size, their SHA-256, and the release, asset and member that hold their bytes. Its hash is in `SHA256SUMS` and `manifest.json`.

The archives:

| Asset | Contents |
|---|---|
| `prepared-data-and-deployment-bundles.tar.gz` | The source-check prepared copy and the worker bundles. Includes held-out data as opaque bytes: private reproducibility backup only. |
| `stage-b-and-safeguards-development-records.tar.gz` | Stage B candidate sources, verify copies, synthetic runs and review reproductions, plus the recovery-safeguards source. |
| `study-v2-scientific-and-operational-records.tar.gz` | Calibration outputs, retrieved CUDA and setup receipts, diagnostics, minimal-experiment records, and backup and workflow records. |
| `runpod-pilot-and-pilot-implementation.tar.gz` | RunPod pilot records and pilot implementation logs. |
| `worker-handoff-records.tar.gz` | Delegated-worker handoff records. |
| `research-scoping-and-writing.tar.gz` | Literature sources, scoping, proposal and writing drafts. |
| `public-reference-and-anonymous-export-records.tar.gz` | The public DATE-LM reference clone and the anonymous-export work records. |

## What was left out

- **Access files.** 46 SSH keys, SSH host keys and pod address records were never uploaded. Their paths are in `manifest.json`.
- **A third-party credential.** `tmp/date-lm-reference-20261002/evaluation/GPT_scoring.py` contains an OpenAI key hard-coded upstream (DATE-LM, commit `95c9a6db`). The file is excluded and can be re-fetched from upstream.
- **The pod's SSH public key.** `create-request.json` is archived as `create-request.redacted.json`, with that key removed. `inventory.jsonl` records both hashes.
- **Working copies and copies of earlier assets.** Delegated-worker working copies, restore-check scratch, local copies of the 2 October assets, virtual environments and caches. The reasons are in `manifest.json`.

## Checks

- **Credential scan** (`secret-scan.json`).
  - Pattern rules ran over every file and every nested archive member: 3084 entries in the uploaded archives. It also checked for the project's SSH key material and the 14 pod addresses from the pod records.
  - No credential was found in the uploaded bytes.
  - The remaining matches are a placeholder key in training text and example values in RunPod's published API document.
  - This is a bounded pattern check, not a proof that every possible secret is absent.
  - Held-out files were read only by this automated check, and nothing from them was displayed.
- **Upload check** (`upload-verification.json`). Every asset was downloaded back from GitHub into a new folder. Sizes and SHA-256 matched the manifest and GitHub's asset digests, and `shasum -a 256 -c SHA256SUMS` passed.
- **No independent review.** Unlike the 2 October backup, no separate reviewer has checked this one.

## Restoring

Download every asset, run `shasum -a 256 -c SHA256SUMS`, and extract each archive into a new directory. Paths are relative to the project root.

## Privacy

These assets are **private**. Do not publish this release or change the repository's visibility for submission. The anonymous-review code export is separate and excludes all of this.
