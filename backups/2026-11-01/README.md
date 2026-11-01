# Backups of 1 November 2026

## Stage 1 after the reading (release backup-2026-11-01-stage1-after-reading)

Made by the lead (General Implementation VIII) at 2026-11-01T21:41-21:43 UTC, right after the stage-1 reading, with the
kit's own `tmp/stage1-olmo/backup_records_stage1.py` (dry run first: nothing missing, 0 scan hits, "upload"; then the
real run, exit 0). Every host of `plan.json`, the similarity host `sim-1` of block sim included, both seal records (A, B)
and the judge files of blocks A and B: 6,419 files in three archives (units 105.9 MB, records 2.1 MB, edits and analyses
0.7 MB). Private repository, draft release
(https://github.com/4r4cn1d0/attribution/releases/tag/untagged-50b4df786a1cd3efbc00), download-back hashes OK, 0 scan
hits (HF_TOKEN and RUNPOD_OPERATOR_API_KEY values, 26 pod IPs). Verification files and the run log:
`backup-stage1-after-reading-20261101/`. The local staging (tar files) was deleted after the verification. It
supersedes `backup-2026-10-31-stage1-block-b` for the kit's records.

## The lead's local-only items (release backup-2026-11-01-local-after-reading)

Made by the lead at 2026-11-01T21:43 UTC with `backup-local-20261101/backup_local.py` (it imports the kit tool's scan,
pod-IP, token-value and gh functions; dry run first: 4,842 files, 0 scan hits). Four archives:
- `hlc-draw-sealed-20261101.tar.gz`: LN-31's sealed draw `tmp/hlc/draw-20261101/` (the key and the weights; packed by
  bytes, never opened; the only other copy is local and git-ignored);
- `hlc-inputs.tar.gz`: the restored LN-31 inputs `tmp/hlc-inputs/` (the 9 Oct key and the prepared-v3 members, each
  pinned by SHA-256 in FOCUS);
- `lead-notes-stage1-integrate-20261017.tar.gz`: the lead's integration notes of 17-27 Oct (worktree
  kind-hawking-a6ce04, `tmp/claude-workspaces/stage1-integrate-20261017/notes/`; ADD:428's evidence
  `b16-verify-stats.json` `65fe90c3…` and `b16-fix.json` `4090118e…` among them);
- `build-rounds-scratch-20261101.tar.gz`: the 1 Nov build rounds' scratch (reports, reviewers' evidence and synthetic
  dry-run worlds; the ws-* worktrees left out, their code is committed).
Private repository, draft release (https://github.com/4r4cn1d0/attribution/releases/tag/untagged-4644160e795fdc510a66),
download-back hashes OK. 13 symlinks were left out (scaffolding). Verification files: `backup-local-20261101/`. The
local staging was deleted after the verification.
