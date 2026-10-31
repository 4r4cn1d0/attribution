# Backups of 31 October 2026

## Gate B's judge outputs (release backup-2026-10-31-gateb-judges)

Made by the lead (General Implementation VIII) at 2026-10-31T13:35 UTC on the user's "Yes, back up" (to "Back up Gate B's judge
outputs so their last two pods can go too?"), with the script `scratchpad/gbj/backup_gateb_judges.py` (it mirrors
`tmp/gate-b-olmo/backup_records_gateb.py`: dry run first, exit 0; a scan of every staged file for the kit's secret
patterns, the token values set at the time and every pod public IP known; gh without RunPod or HF variables; a new tag
and a private repository checked first). Private repository, draft release, download-back hashes OK, the archive's
members equal the inventory (`backup-gateb-judges-20261031/upload-verification.json`).

58 files, 8,521,170 bytes, in `gateb-judges-records.tar.gz`: `tmp/gate-b-olmo/judges/` (the per-arm
judge files and their index); `tmp/judge-pod/gateb-hb-1/` and `gateb-granite-1/` (each launch's result, log, bundle
record and fetched outputs: label caches and run records) without `bundle.tar.gz` (answer text rebuilt from the units
in the Gate B unit backups); `tmp/family-probe-judge/hosts/judge-gateb-*/` without `pod*.json`, `known_hosts` and
`timer-settings.json`. Scan hits 0.

After the verification the two stopped judge pods (`attribution-judge-gateb-hb-1`, `attribution-judge-gateb-granite-1`,
10 GB each) were deleted: GET before (EXITED, name equal), DELETE 204, GET after 404
(`.ai/inputs/stage1-post-w1-20261023/block-b/pod_deletions_gateb_judges_20261031.jsonl`; kit log
`tmp/gate-b-olmo/deletions.jsonl`).

## Stage 1 after block B's seal (release backup-2026-10-31-stage1-block-b)

Made by the lead (General Implementation VIII) at 2026-10-31T18:10–18:12 UTC, right after `seal.py block B`, with the kit's
own `tmp/stage1-olmo/backup_records_stage1.py` (dry run first: exit 0, nothing missing, 0 scan hits; then the real run, exit 0).
Every stage-1 host of `plan.json` (b-20 included), both seal records (A, B), `judges/A/**` and `judges/B/**` with their
`pods/<tag>/` copies: 6,352 files in three archives (units 105.8 MB, records 2.0 MB, edits and analyses 0.7 MB). Private
repository, draft release (https://github.com/4r4cn1d0/attribution/releases/tag/untagged-ca3fd6ce5002afa5c998), download-back
hashes OK, 0 scan hits (HF_TOKEN and RUNPOD_OPERATOR_API_KEY values, 26 pod IPs). Verification files:
`backup-stage1-block-b-20261031/` (manifest.json, SHA256SUMS, secret-scan.json, upload-verification.json). The local staging
(tar files) was deleted after the verification. It supersedes `backup-2026-10-31-stage1-block-b-interim` (every host except b-20).
