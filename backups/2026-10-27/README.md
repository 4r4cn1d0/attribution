# Backup of 27 October 2026: stage 1 through block A's seal (one private draft release)

Made by the lead (General Implementation VII) at 2026-10-27T14:12 UTC with the stage-1 kit's `backup_records_stage1.py --tag
backup-2026-10-27-stage1-block-a` (B15 rounds 30 and 30a, `62b89bd`), run from `tmp/stage1-olmo/` after `seal.py block A`.

- **Dry run first:** exit 0; 2,089 files; nothing missing or oversize; 0 scan hits.
- **The real run:** exit 0; private repository; draft release; download-back hashes OK; 2,089 files.
- **Scan:** the kit's `secret_scan.py` patterns, 9 recorded pod IPs, and the values of `HF_TOKEN` and `RUNPOD_OPERATOR_API_KEY`: 0 hits (`secret-scan.json`).
- **What it holds:** the records and sealed units of every stage-1 host so far (S1-0 `s10-1`; block A `a-1`…`a-11`, with a-5, a-6, a-7 listed as moved; the cert pod `cert-1`), the seal `seals/block-A.json` (`6c6267c8…`) with every file it lists at the seal's SHA-256, the judge files `judges/A/**`, the edits, the pack receipts. No model states (they stay on the stopped pods' volumes).

[Open the private draft release](https://github.com/4r4cn1d0/attribution/releases/tag/untagged-0477856a65c5b862da0a) (a draft has an "untagged" link).

| Asset | Bytes |
|---|---|
| stage1-block-a-units.tar.gz | 35,711,287 |
| stage1-block-a-records.tar.gz | 383,428 |
| stage1-block-a-edits-analyses.tar.gz | 373,172 |
| inventory.jsonl | 344,777 |
| manifest.json | 24,268 |
| secret-scan.json | 492 |
| SHA256SUMS | 458 |

Files here: `upload-verification.json`, `secret-scan.json` and `SHA256SUMS` (copies of the release's own; hashes and names only).
