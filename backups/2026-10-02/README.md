# Preserved research backup — 2 October 2026

Private backup of the work available after the Runpod credit-depletion incident.
The matching private GitHub release uses tag `backup-2026-10-02` and holds eleven
archive assets plus `SHA256SUMS`. This repository stores the source, research
records and manifest; large runtime archives stay out of Git history.

Five calibration archives contain31 previously verified completed calibration/
evaluation runs. The backup also contains prepared data and public source copies,
the original pilot evidence, operational and verification records, and three
unintegrated StageB source snapshots. Candidate03 has not been tested or accepted;
its presence is preservation, not scientific endorsement. No new development
matrix or heldout results are claimed: those unsynced matrix artifacts were lost.

`manifest.json` gives archive size, SHA256, provenance and status. `SHA256SUMS`
can be checked with `shasum -a 256 -c SHA256SUMS` after downloading every asset.
The credential-pattern scan found no matches in1128 archive files. This is a
bounded pattern check, not a formal proof that every possible secret is absent.

Extract archives into a new directory, preserving their paths. The five
calibration archives have remote-relative paths and need separate host folders.
Their per-host verification reports and receipts are in the operational archive;
prepared-v1 and the unchanged engine support read-only PathMap verification.
Do not merge same-named per-host paths blindly or rewrite raw scientific receipts.

These assets are PRIVATE. Raw logs, paths, machine metadata, prepared data and
unreviewed drafts are excluded from the separate anonymous-review code export.
Do not publish this backup or change its repository visibility for submission.
