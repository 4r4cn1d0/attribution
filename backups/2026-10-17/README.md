# Backups of 17 October 2026 (IST): the Mac-only model weights and states

Made by the main-study lead (General Implementation VI) on 16–17 Oct UTC (upload 21:19–22:44 UTC; download check to 01:04 UTC). Times are UTC; the folder and tag use the IST date, as on 16 Oct.

**Authority:** the user's "go ahead" in the FAQ chat on 17 Oct IST, relayed by FAQ to the lead, for this upload only. It changes the backup rule for this one release: the Gate B backup tool still never stages model weights.

## The private draft release `backup-2026-10-17-mac-weights`

[Open the private draft release](https://github.com/4r4cn1d0/attribution/releases/tag/untagged-375079dc1cd63ea5ad1d) (a draft has an "untagged" link).

- **86 files, 25,895,406,987 bytes (24.12 GiB)**, plus `manifest.json` and `SHA256SUMS` as assets (88 in all).
  - 20 recovered probe adapters: `tmp/sp-repr/out/*/<unit>/states/e1/adapter.safetensors` (8.41 GB).
  - 66 causal-pilot 1121 state files: `tmp/cause-study-20261012/combined/cause/units/{olmo1b,olmo7b}-{A,C,D}-1121/states/{init,q,e1}/` adapter, optimizer, RNG and `state.json` files (17.49 GB). The `prefetch/` hard links to the same files are not uploaded.
- Each asset name is the repository-relative source path with `/` replaced by `__`. `manifest.json` maps each asset to its path, bytes and SHA-256.
- **Checks** (`backup-mac-weights-20261017/upload-verification.json`): the repository was private before the upload, after the upload and at the end; the release is a draft; every asset was downloaded back one at a time and its SHA-256 matched (6 first attempts failed on the network and passed on retry; no hash ever differed); gh ran with no RunPod or Hugging Face variables; 0 secret-scan hits and no IP address in the manifest, notes and the 18 `state.json` files.
- **Not included:** the public Granite GGUF (it can be downloaded again), and the states that exist only on stopped pods: the OLMo Gate A recipe-B seed-1102 adapter (`attribution-probe-olmo2-1b-1102`) and the Gate B w0b-2 retrain's q and e1 states (`attribution-gateb-w0b-2`). Backing those up needs a pod start and the user's go.
- **The Mac copies stay.** Nothing was deleted. The staging folder `tmp/gi-vi-weights-backup/stage/` holds hard links only (no extra disk space).

The script `backup-mac-weights-20261017/upload_weights.py` made the release (prepare, upload, verify; resumable).
