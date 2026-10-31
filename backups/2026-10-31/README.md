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
