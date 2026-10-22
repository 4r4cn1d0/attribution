# Backups and local clean-up, 22 Oct 2026 (the lead, GI VI)

**Authority:** the user, GI VI chat, 22 Oct: "can you be more memory efficien locally theres the attribution project folder is taking 64 gb" and "just put it all on github whatever is needed for the paper but not locally right now everything"; then "I emptied the Trash".

## 1. The private draft release `backup-2026-10-22-local-tmp`

- [Open the private draft release](https://github.com/4r4cn1d0/attribution/releases/tag/untagged-5d96d57f7a4830193ffe) (a draft has an "untagged" link).
- **All 190 entries of the main checkout's `tmp/`**: 191 assets plus `manifest.json` and `SHA256SUMS`, 5,892,188,009 bytes (5.49 GiB), packed one `.tar.gz` per entry. The venv is skipped; it is rebuilt from `tmp/minimal-experiment-20261002/environment.lock`.
- **Left out on purpose:** 454 files are listed in `backup-tmp-20261022/manifest.json` with their reasons: 404 by name (mostly `.DS_Store`, plus `known_hosts`, key and env files), 48 holding an SSH public key, 2 holding a private key. Nine files from the "trash" entries hold only an SSH public key. They are in the extra asset `tmp--public-key-matches.tar.gz` (`supplement.json`; downloaded back and checked). Private keys and `known_hosts` are not backed up; they belong to pods that no longer exist.
- **Checks** (`backup-tmp-20261022/upload-verification.json`): the repository was private before and after; the release is a draft; all 191 assets were downloaded back one at a time, and each SHA-256 matched.
- **Restore:** download an asset, check it against `SHA256SUMS`, and run `tar -xzf` from the repository root (join `.partNN` files with `cat` first; none were needed this time).

## 2. What left the Mac

- **80 `tmp/` entries** (old pilots, finished staging folders, superseded probe units; each in the verified release) were moved to the Trash: `backup-tmp-20261022/trashed.json` (2.7 GB; the user empties it). The 35 entries that the next steps or the tests read stay. So do the 75 that other sessions own (the GPT lead's side paper and grants, the Side Project): they are backed up and were not moved. `tmp/` went from 7.1 GB to 4.4 GB.
- **Five cached models** (28 GB; no test or current script loads them) were moved to the Trash after their repo ids, revisions and file lists were recorded in `hf-cache-moved-to-trash.json`; the user emptied that Trash. They are public, and can be fetched again at the same revisions. The model cache went from 42 GB to 15 GB (Qwen3Guard-Gen-4B for W1-18 and the OLMo-2-0425-1B base for the Safe LoRA check stay).
- The local tar files were deleted once every asset was verified.

The tool is `backup-tmp-20261022/backup_tmp.py` (prepare, upload, verify, trash, clean-stage; resumable).
