# Stage 1, block B: cost and completion report (final, after the seal)

Written by the lead (General Implementation VIII) on 31 October 2026 at 18:13 UTC (clock checked). **Block B is complete
and sealed.** This report gives cost and completion only. No U, HB, Granite, O, task-loss or coherence value appears here.
It replaces the interim report `cost_completion_block_b_interim.md` (09:47 UTC, before b-20 and the judges).

## 1. Summary

- **All 20 live block-B hosts are verified-and-stopped and recorded done** (b-4 moved to b-21). b-20, the last one (Safe LoRA
  at a0 1105–1107), was created at 12:46:55 UTC, started its 3 jobs at 13:17:23, finished at 16:00:17
  (`verified-and-stopped`, outer exit 0, 0 secret hits, stop confirmed), and was recorded done at 16:03:54 UTC.
- **Both judges ran and passed every check** (runbook `tmp/gi-viii-notes/judge-runbook-block-b.md`, steps 0–15, in order;
  HarmBench verified before the Granite launch):
  - **HarmBench `s1b-hb-1`:** 72 units, 57,600 answers judged and cached, exit 0, pod exit 0, run record ok, stop confirmed
    (EXITED), NVIDIA A100-SXM4-80GB in the result and the create request, tokenizer `aac304fb…` (block A's), cap 5.0 h,
    bundle `8d186696…` (equal to the dry bundle), 59.4 pod minutes, $1.77.
  - **Granite `s1b-granite-1`:** 72 units, 14,400 answers judged and cached, known-answer gate passed, exit 0, pod exit 0,
    run record ok, stop confirmed, A100-SXM4-80GB, tokenizer `5354502d…` (block A's), cap 3.0 h, bundle `2607415b…`
    (equal to the dry bundle), 63.5 pod minutes, $1.89.
  - Device check (step 9): both `cuda`, `NVIDIA A100-SXM4-80GB`, 72 units, the same as block A.
- **Judge files:** 144 (72 per judge) in `tmp/stage1-olmo/judges/B/`, index `fe76b7ec…`, the kit's check passing before
  and after the move. The §37 copy (point 5) of each launch's run record and label cache is in `judges/B/pods/<tag>/`,
  hashes equal to each result's fetched map; the kit's round-33 check (GB4) found no problem.
- **Records:** judge-completion record `judge_completion_block_b.json` (`b458962f…`), recorded by `record-judges B`
  (valid: 72 required units, 144 indexed files); the lead's record `judges_block_b.json` (`0f0c1129…`).
- **Seal:** `seal.py block B` at 18:10:11 UTC: 3,830 files (3,541 sealed, 289 readable), seal SHA-256 `b4e11dc9…`.
- **Measured spend, block B: $144.94** = the 21 block-B pods $141.27 (75.04 GPU-hours) + the two judge pods
  $3.67 (HarmBench $1.78 billed, Granite $1.89*). The B10 certify pods cfy-1 and cfy-2 add $3.35. Against block B's funding record of $245.55 (cap-based need
  with a 1.25 contingency factor), the block used about 59%. Contingency B: $36.74 left (spent $12.37 earlier on the
  cfy-1 requeue and the b-4 → b-21 move).
- **Balance:** $30.20 at 18:11 UTC; nothing running; idle charge $0.054/h.

## 2. Completion, by launch

| Launch | Hosts | What ran | Completion |
|---|---|---|---|
| 0 | b-1, b-2, b-3 | A1, H1, S3 and a0 at 1105–1107 | 12 of 12 complete |
| 1 | b-5, b-6, b-21 (b-4 moved) | L1, S1, S4, R at 1106, 1107, 1105 | 12 of 12 complete; b-4's setup failed (`pre-job-failed`), moved to b-21 |
| 2 | b-7, b-8 | recipe G at a0 1102–1107 | 6 of 6 complete |
| 3 | b-9, b-10 | B+Qi at a0 1102–1107 (engine Y) | 6 of 6 complete |
| 4 | b-11…b-14; b-15, b-16 | ref_eval at a0 1101–1104; Safe LoRA at a0 1101 (certify + default), 1102–1104 | 4 of 4 and 4 of 4 complete |
| 5 (second phase) | b-17, b-18, b-19; b-20 | ref_eval at a0 1105–1107; Safe LoRA at a0 1105–1107 | 3 of 3 and 3 of 3 complete |
| 6 | judge | HarmBench, 72 units | 57,600 answers judged; verified |
| 7 | judge | Granite, 72 units (+ the 200-answer known-answer gate) | 14,400 answers judged; gate passed; verified |

Judge units (`units-of-block B`, `judge_units_b.txt` `72c0fd8d…`): a0_arm 3, arm 21, ref_eval 28, ref_train 12, safe_lora 8;
the same set as `judge_required_units` and the plan's 72.

## 3. Cost, by pod (RunPod billing, 28–31 Oct, fetched 18:12 UTC)

| Pod | Launch | Created (UTC) | GPU-h | GPU $ | Billed $ | Other $ |
|---|---|---|---|---|---|---|
| b-1 | 0 | 10-29 15:25 | 5.76 | 10.31 | 10.66 | 0.34 |
| b-2 | 0 | 10-29 15:26 | 4.69 | 8.39 | 8.73 | 0.35 |
| b-3 | 0 | 10-29 15:27 | 4.54 | 8.12 | 8.50 | 0.38 |
| b-4 | 1 | 10-29 15:28 | 1.04 | 1.86 | 2.27 | 0.41 |
| b-5 | 1 | 10-29 15:29 | 3.64 | 6.52 | 6.95 | 0.43 |
| b-6 | 1 | 10-29 15:30 | 4.61 | 8.25 | 8.63 | 0.39 |
| b-7 | 2 | 10-29 15:30 | 3.33 | 5.96 | 6.29 | 0.33 |
| b-8 | 2 | 10-29 15:31 | 4.10 | 7.34 | 7.77 | 0.43 |
| b-9 | 3 | 10-29 15:32 | 3.01 | 5.39 | 5.81 | 0.42 |
| b-10 | 3 | 10-29 15:33 | 3.64 | 6.52 | 6.94 | 0.43 |
| b-11 | 4 | 10-29 16:59 | 3.89 | 6.96 | 7.37 | 0.41 |
| b-12 | 4 | 10-29 21:23 | 4.12 | 7.37 | 7.73 | 0.36 |
| b-13 | 4 | 10-29 21:24 | 4.21 | 7.54 | 7.90 | 0.36 |
| b-14 | 4 | 10-29 21:25 | 3.34 | 5.99 | 6.21 | 0.23 |
| b-15 | 4 | 10-30 06:00 | 3.59 | 6.42 | 6.69 | 0.27 |
| b-16 | 4 | 10-29 17:00 | 1.88 | 3.36 | 3.76 | 0.40 |
| b-17 | 5 | 10-30 11:15 | 2.92 | 5.23 | 5.43 | 0.20 |
| b-18 | 5 | 10-30 14:47 | 1.90 | 3.41 | 3.57 | 0.16 |
| b-19 | 5 | 10-30 15:06 | 2.98 | 5.33 | 5.49 | 0.16 |
| b-20 | 5 | 10-31 12:46 | 3.22 | 5.77 | 5.84 | 0.07 |
| b-21 | 1 | 10-29 16:40 | 4.63 | 8.30 | 8.72 | 0.42 |
| cfy-1 | 0 | 10-29 13:52 | 0.13 | 0.22 | 0.65 | 0.43 |
| cfy-2 | 0 | 10-29 14:02 | 1.27 | 2.27 | 2.70 | 0.43 |
| s1b-granite-1 | judge | 10-31 17:05 | 1.06* | 1.89* | 1.89* | 0.00* |
| s1b-hb-1 | judge | 10-31 16:05 | 0.99 | 1.77 | 1.78 | 0.01 |
| **Block B pods (b-1…b-21)** | | | **75.04** | **134.32** | **141.27** | **6.95** |
| **Judge pods** | | | **2.05** | **3.66** | **3.67** | **0.01** |
| **Block B total** | | | **77.09** | **137.98** | **144.94** | **6.96** |
| cfy-1, cfy-2 (B10 certify) | | | 1.40 | 2.50 | 3.35 | 0.86 |

\* Granite: RunPod's billing row was still partial at the fetch (0.12 GPU-h, $0.21); the figure is the launcher's own (63.5 pod minutes × $1.79/h = $1.89, `judge_units_stage1.py result`). HarmBench's billed $1.78 equals its launcher figure ($1.77) to the cent's rounding.

GPU $ = billed GPU-hours × $1.79. "Other" = billed − GPU $ (volume storage while stopped, and any CPU-only time). Source:
RunPod `GET /v1/billing/pods` (day buckets, grouped by pod), saved as `billing_pods_20261028_31_final.json`, matched to
hosts by `hosts/HOST/pod.json` and `judge-TAG/pod.json` ids. The 34 stage-1 pods deleted at 12:52–12:55 UTC bill nothing
after that time.

## 4. Pods left, and their idle charge

Stopped, never restarted by the kit: **b-20** (40 GB volume), **s1b-hb-1** and **s1b-granite-1** (10 GB each), plus the three
kept earlier (a-2, gateb-w0b-2, probe-olmo2-1b-1102; each holds an only copy the plan keeps). Their records are in the
final backup below; deleting a pod needs the user's yes.

## 5. Backup

`backup-2026-10-31-stage1-block-b`, private draft release (https://github.com/4r4cn1d0/attribution/releases/tag/untagged-ca3fd6ce5002afa5c998), made by the kit's `backup_records_stage1.py` after the seal: every stage-1 host of `plan.json` (b-20 included), both seal records, `judges/A/**` and `judges/B/**` (the judge files and the `pods/<tag>/` copies), 6,352 files in three archives (units 105.8 MB, records 2.0 MB, edits and analyses 0.7 MB); dry run first (nothing missing); 0 scan hits (HF_TOKEN and RUNPOD_OPERATOR_API_KEY values and 26 pod IPs checked); download-back hashes OK. Verification files in `backups/2026-10-31/backup-stage1-block-b-20261031/`. The local staging (tar files) was deleted after the verification.
