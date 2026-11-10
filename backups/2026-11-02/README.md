# Backups of 2 November 2026

## Stage 1b's pilot (release backup-2026-11-02-stage1b-pilot)

Made by the lead (General Implementation IX) at 2026-11-02T03:26-03:28 UTC, after pilot block P (host p-1:
verified-and-stopped, record-done, sealed `f12fb5e7…`), with the kit's own `tmp/stage1-olmo/backup_records_stage1.py`
(dry run first: nothing missing, nothing oversize, 0 scan hits over 6,618 files, "upload"; then the real run, exit 0).
Every host of `plan.json`, p-1 of block P included, the three seal records (A, B, P) and the judge files of blocks A
and B: 6,618 files in three archives (units 108.6 MB, records 2.3 MB, edits and analyses 0.8 MB). Private repository,
draft release (https://github.com/4r4cn1d0/attribution/releases/tag/untagged-a2cfcbcc794bdc449b96), download-back
hashes OK, 0 scan hits (HF_TOKEN and RUNPOD_OPERATOR_API_KEY values, 27 pod IPs). Verification files and the run
log: `backup-stage1b-pilot-20261102/`. The local staging was deleted after the verification. It supersedes
`backup-2026-11-01-stage1-after-reading` for the kit's records.
