# Backups of 16 October 2026 (one private draft release; the Side Project branch on GitHub)

Made by a General Implementation V worker (step 4, backups; status report D11). Times are UTC. The folder and tag use the IST date (16 Oct). The release was made on 15 Oct UTC, 20:25:53. Earlier tags used the UTC date.

## 1. The private draft release

| Release tag | What it holds |
|---|---|
| backup-2026-10-16-post-1010-records | Records that no earlier release holds. This is (a) every record made after the last release (`backup-2026-10-10-gateb-anchor`, 10 Oct 13:58) and (b) some older records that were never released. 8,074 files, 495.9 MB before compression, 10 assets. No model weights or states. |

[Open the private draft release](https://github.com/4r4cn1d0/attribution/releases/tag/untagged-61b92ec27d8a76f6ed8c) (a draft has an "untagged" link).

The folder `backup-post-1010-records-20261016/` holds the records of this release: `upload-verification.json`, `SHA256SUMS`, `manifest.json` and `secret-scan.json`, as in 2026-10-09. The manifest gives the counts for each source, the time filter and the exclusions. `inventory.jsonl` (path, bytes, SHA-256 and source time of each file) is a release asset. It is not copied here.

**Assets (one tar.gz for each group):**

| Asset | Files | Before compression | Contents |
|---|---|---|---|
| `post1010-main-kits.tar.gz` | 443 | 23.6 MB | `tmp/gate-b-olmo`: only the changes after the anchor release (plan.json with `w0a-1`, operator-actions.jsonl, the packed-gateb receipts, the anchor finisher log). A file with the same SHA-256 in the anchor release is not staged again, so the anchor text is not in this release. The released probe kits (OLMo-2-1B, Llama-3.2-1B): their records changed after their own last release, less one hour (the 11–12 Oct adapter-recovery restarts). **Not released before:** the Llama-3.2-1B Gate A seed kits `family-probe-llama32-1b-b5e5-seed1102` and `-seed1103` (status report risk 1). The anchor release's own records (`tmp/backup-stage-gateb-anchor-assets`, without its tar.gz files). |
| `post1010-side-kits.tar.gz` | 3,754 | 241.8 MB | All 40 `tmp/family-probe-sp-*` kits: 7–8B rungs (OLMo-2-7B, Llama-3.1-8B) and the half-LR runs, replication, Qwen 1.5B and 7B, fiction (with the screen), bt seeds. The two Llama B seed kits were released on 9 Oct, so only their later changes are here. |
| `post1010-judges.tar.gz` | 405 | 39.4 MB | Every judge pod run, `tmp/judge-pod/*` (14 runs, 8–11 Oct: parity, Llama Gate A HarmBench and Granite, side pairs, 7–8B, replication). No earlier release held a judge run. Also `tmp/family-probe-judge`, the small `judge-pod-*` folders and the judge launch logs. The judge input bundles are left out. |
| `post1010-repr-causal.tar.gz` | 1,081 | 52.6 MB | `tmp/sp-repr` (the representation probe results: `out/*/` JSON and logs, `refusal-direction-20261012.json`, scripts) without the adapters. The causal pilot 1121 and follow-up 1122: `tmp/cause-study-20261012`, `tmp/causal-followup-20261012` and the four `family-probe-cause*` kits, without model states. |
| `post1010-gi-v.tar.gz` | 2,163 | 22.0 MB | The `tmp/gi-v-*` folders and the `gi-v-autolaunch-*.log` files (Gate B verify, Granite converter, Llama Gate A kits and read, stage-1 plan, draft rev5, anchor prep, the status scan). The review scratch trees (`bt*`, `ws`, `mut`, `snapshot`, `snap`, `sim`, `merged`: test temp folders and workspace copies, about 3.7 GB) are left out. `tmp/gi-v-steps-4-9` is left out because work there continues. |
| `post1010-side-paper.tar.gz` | 228 | 116.4 MB | `tmp/side-paper-continuation-20261012` (the side paper continuation of 12–13 Oct: arXiv package, numerical packages, checks, page renders). |
| `inventory.jsonl`, `secret-scan.json`, `SHA256SUMS`, `manifest.json` | | | Lists and checks. |

**Never staged** (by rule): model weights and states (`.safetensors`, `.bin`, `.pt`, `.pth`, `.gguf`, `.ckpt`); symlinks; pod address files (`pod*.json`), `known_hosts` and timer settings; SSH folders and keys; account state (`account*.json`); setup bundles and payloads; locks, caches and partial downloads; kit code that is the same as the `runkit/` copy. The guard never opens `hidden/`, `banks/`, held-out files or `selector*.jsonl`. It found none in these sources.

**Left out by the secret scan (49 files).** A file with a scan hit is not staged. The manifest lists each path and the type of hit. These files are only on the Mac:
- 46 logs with a recorded pod IP address: 44 in `tmp/sp-repr` (`out/*/log.jsonl`, `runs/*.out`, `resume-20261012/*.log`, `canary-run.out`) and the two causal kits' `operator/pull.log`. The results are not in these logs. The results are in the staged JSON files.
- 3 test files with a short, synthetic string that has the shape of an SSH public key: `tmp/sp-repr/test_canary_reset_check.py`, `tmp/sp-repr/test_restart_probe_pull.py` and one test copy in `gi-v-granite-converter`. They are not real keys (the key bodies have 7–17 characters).

**Not in this release because they are not research records:** the GPT lead's grant and budget folders (`tmp/bluedot-budget-20261013`, `tmp/grant-budget-20261013`), the grant résumé in `tmp/pdfs`, `tmp/claude-handoffs`, and `tmp/judge-pod-dry` (dry runs).

**Checks:**
- **Secret scan:** the `runkit/gate-b-olmo/secret_scan.py` patterns; the 44 pod IP addresses found in recorded pod data; the values of the RunPod and HF tokens and of one session token. The values were compared and never shown. The scan ran on every source file and on archive members one by one (the side paper's zip and tar.gz files). Then it ran again on every staged copy and on every generated file. There were 0 hits on the staged copies (`secret-scan.json`).
- **Copies:** each staged copy has the same SHA-256 as its source.
- **Download-back check:** each of the 10 assets was downloaded again. Its size and SHA-256 were the same (`upload-verification.json`, `"ok": true`).
- **Draft and private:** `gh release view` gives `isDraft: true`. `gh repo view` gives `isPrivate: true`, `visibility: PRIVATE` (4r4cn1d0/attribution). These were checked before the staging, after the upload, and again at 20:26:55.
- gh ran without the RunPod, HF and session token variables.

The tool is `tools/backup_post_1010.py` (SHA-256 d13db2a3…, the same as the manifest's `script_sha256`). It is made from `runkit/gate-b-olmo/backup_records_gateb.py` and the kits' `backup_records_olmo.py`. Those tools back up one kit to one release. This task needed one release for many sources.

These assets are **private**. They include model outputs to unsafe prompts. Do not publish them.

## 2. The Side Project branch on GitHub

- `claude/wonderful-greider-d1aa5b` is now on origin. It was pushed at 20:06 with no force, after the repository was confirmed PRIVATE at 20:06:38. Local and remote tips are both `59fae4f`.
- The check before the push (`side-branch-push.json`; tool `tools/check_side_branch.py`) covered 103 commits and 518 new blobs (29.6 MB). It found no file over 50 MB, no secret pattern, no token value, and no forbidden name (weights, selector, hidden, held-out, anchors, keys, pod files).
- The push sends commits only. The uncommitted arXiv files in the side worktree (`main.tex`, `main.pdf` changes, `main.aux/.log/.out`, `same-recipe-arxiv-source-20261013.zip`, `writing/side-notes/zenodo/`) are **not** on GitHub. Their owner must commit them first.

## 3. Model weights and states: NOT uploaded; copy them to an external drive

The adapters and causal model states are only on this Mac. They are not in any release. They use **25.9 GB (24.1 GiB)**:

| Location | Files | Size |
|---|---|---|
| `tmp/sp-repr/out/*/<unit>/states/e1/adapter.safetensors`: the 20 recovered probe adapters. OLMo-2-1B 1101, 1103, G 1102, G 1103; Llama-3.2-1B 1101, G 1102, G 1103, G5 1101; side Llama B 1103, B2 1102; Llama-3.1-8B 1101–1103, G 1101–1102; OLMo-2-7B 1102, 1103, B2 1101, G 1101–1102 | 20 | 8.41 GB (7.83 GiB) |
| `tmp/cause-study-20261012/combined/cause/units/{olmo1b,olmo7b}-{A,C,D}-1121/states/*`: causal pilot adapters and RNG states | 48 | 17.49 GB (16.29 GiB) |

- `tmp/cause-study-20261012/prefetch/{olmo1b,olmo7b}/unit-{A,C,D}` holds hard links to the same 48 files. A copy that does not keep hard links needs 34.97 GB for this folder. Use `rsync -aH`.
- The status report's "23.8 GB" is the same set, with the GiB figures rounded (7.8 + 16).
- There is no adapter on the Mac for the OLMo Gate A seed 1102. It is only on the stopped pod `attribution-probe-olmo2-1b-1102` (status report D4).
- Optional: `tmp/judge-models/granite-guardian-3.3-8b-Q4_K_M.gguf` (4.94 GB) is a public judge model. You can download it again.

**Recommendation for the user:** copy these to an external drive, then compare the hashes. For example:
`rsync -aH --progress /Users/spiderishi/Coding/attribution/tmp/sp-repr/out /Volumes/<drive>/attribution-states-20261016/sp-repr/` and `rsync -aH --progress /Users/spiderishi/Coding/attribution/tmp/cause-study-20261012 /Volumes/<drive>/attribution-states-20261016/`. Then run `shasum -a 256` on both sides. Do not delete the Mac copies until the drive copy is checked.

## 4. Local staging copies

The staging folder (`tmp/gi-v-steps-4-9/step4-backups/stage`, 495 MB) and the assets (`stage-assets`, 95 MB) are still on the Mac. The worker could not open the macOS Trash (access refused), so it did not move them. The release and the sources hold the same files. The user or the lead can move both folders to the Trash (memory rule: remove tar files after a verified backup).

## 5. Gap in the records

The anchor release `backup-2026-10-10-gateb-anchor` has no folder under `backups/`. Its records were only in `tmp/backup-stage-gateb-anchor-assets/`. This release now holds them (`main-kits/backup-stage-gateb-anchor-assets/`). The lead can add `backups/2026-10-10/` from that folder.

## 6. Gate B wave 0a records (release backup-2026-10-16-gateb-w0a)

Made by the lead (General Implementation VI) at 2026-10-16T00:25 UTC with the kit's `backup_records_gateb.py --host w0a-1` (dry run first: exit 0, 165 files, 0 scan hits). Private repository, draft release, download-back hashes OK (`backup-gateb-w0a-20261016/upload-verification.json`).

[Open the private draft release](https://github.com/4r4cn1d0/attribution/releases/tag/untagged-7c7232d8fab1bb6390b0) (a draft has an "untagged" link).

| Asset | Size (bytes) | Contents |
|---|---|---|
| `gateb-w0a-units.tar.gz` | 1,886,735 | The sealed units of w0a-1 (R_1@1101, R_2@1102, R_3@1103), no model states |
| `gateb-w0a-records.tar.gz` | 26,838 | `hosts/w0a-1/` records (finished.json, orchestrate.jsonl, environment checks; never pod*.json, known_hosts or timer settings) |
| `gateb-w0a-edits-analyses.tar.gz` | 72,561 | The R edit files, plan.json, budget-checks.jsonl, operator-actions.jsonl, the expected fixture, launch and finisher logs, and the noise-gate reading's inputs and output (`gate_b_inputs_noise_gate.json`, `gate_b_noise_gate.json` 4b817f73…) |
| `inventory.jsonl`, `secret-scan.json`, `SHA256SUMS`, `manifest.json` | | Lists and checks |

The pod `attribution-gateb-w0a-1` stays stopped. Delete it only with the user's yes.
