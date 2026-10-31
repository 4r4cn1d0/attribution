# Stage 1, block B: interim cost and completion report (before b-20 and the judges)

Written by the lead (General Implementation VIII) on 31 October 2026 at 09:47 UTC (clock checked). **Interim:** block B is
not complete; b-20 and the two judge launches wait on a top-up (the user's §36 rule). **It gives cost and completion only.**
No U, HB, Granite, O, task-loss or coherence value appears here. The final report follows `seal.py block B`.

## 1. Summary

- **19 of 20 live block-B hosts are verified-and-stopped and recorded done** (b-4 moved to b-21). Left: **b-20** (Safe LoRA at
  a0 1105–1107; launch 5, released, not launched; cap 6.0 h, $11.10 at the kit rate) and **the two judge launches** (6, 7).
- **Judge units ready: 69 of 72** (`units-of-block B`, run to scratch, 09:41 UTC: a0_arm 3, arm 21, ref_eval 28, ref_train 12,
  safe_lora 5); b-20 adds the last 3 Safe LoRA units.
- **Measured pod spend, block B (b-1…b-21): $135.39** billed by RunPod through 31 Oct 09:45 UTC (71.81 GPU-hours; $128.55 of it
  is GPU time at $1.79/h, the rest storage and the restart-to-pull CPU time). The B10 certify pods cfy-1 and cfy-2 add $3.35.
  Source: RunPod `GET /v1/billing/pods` (day buckets, grouped by pod), saved as `billing_pods_20261028_31.json`
  (SHA-256 prefix `b782c220`), matched to hosts by `hosts/HOST/pod.json` ids.
- **Against the plan:** block B's funding record (the user's rule: start from the balance) is $245.55, its cap-based need
  $245.55. Contingency B has $36.74 left (`plan.json`).
- **Live balance −$0.02** at 09:45 UTC (`myself.clientBalance` −0.0235); nothing running; idle charge $0.457/h (storage of every
  stopped pod, account-wide; about $11 a day).
- **Next needs the user:** a top-up. By §36, b-20 starts when the balance covers its $11.10; the judges when it covers $14.32
  (and the judge launcher's own guard needs $10.25 free for HarmBench, $6.55 for Granite; runbook GB8).

## 2. Completion, by launch

| Launch | Hosts | What ran | Completion |
|---|---|---|---|
| 0 | b-1, b-2, b-3 | A1, H1, S3 and a0 at 1105–1107 | 12 of 12 complete; pulled by the restart-to-pull route (addendum §38) |
| 1 | b-5, b-6, b-21 (b-4 moved) | L1, S1, S4, R at 1106, 1107, 1105 | 12 of 12 complete; b-4's setup failed (`pre-job-failed`), moved to b-21 |
| 2 | b-7, b-8 | recipe G at a0 1102–1107 | 6 of 6 complete |
| 3 | b-9, b-10 | B+Qi at a0 1102–1107 (engine Y) | 6 of 6 complete |
| 4 | b-11…b-14; b-15, b-16 | ref_eval at a0 1101–1104; Safe LoRA at a0 1101 (certify + default), 1102–1104 | 4 of 4 and 4 of 4 complete |
| 5 (second phase) | b-17, b-18, b-19; b-20 | ref_eval at a0 1105–1107; Safe LoRA at a0 1105–1107 | 3 of 3 complete; **b-20 not launched** |
| 6, 7 | judges | HarmBench, then Granite, 72 units | not released |

## 3. Cost, by pod (RunPod billing, 28–31 Oct; 31 Oct partial to 09:45 UTC)

| Pod | Launch | Created (UTC) | GPU-h | GPU $ | Billed $ | Other $ |
|---|---|---|---|---|---|---|
| b-1 | 0 | 10-29 15:25 | 5.76 | 10.31 | 10.65 | 0.34 |
| b-2 | 0 | 10-29 15:26 | 4.69 | 8.39 | 8.73 | 0.34 |
| b-3 | 0 | 10-29 15:27 | 4.54 | 8.12 | 8.50 | 0.38 |
| b-4 | 1 (moved) | 10-29 15:28 | 1.04 | 1.86 | 2.27 | 0.41 |
| b-5 | 1 | 10-29 15:29 | 3.64 | 6.52 | 6.95 | 0.43 |
| b-6 | 1 | 10-29 15:30 | 4.61 | 8.25 | 8.63 | 0.38 |
| b-21 | 1 | 10-29 16:40 | 4.63 | 8.30 | 8.71 | 0.42 |
| b-7 | 2 | 10-29 15:30 | 3.33 | 5.96 | 6.28 | 0.32 |
| b-8 | 2 | 10-29 15:31 | 4.10 | 7.34 | 7.76 | 0.43 |
| b-9 | 3 | 10-29 15:32 | 3.01 | 5.39 | 5.81 | 0.42 |
| b-10 | 3 | 10-29 15:33 | 3.64 | 6.52 | 6.94 | 0.43 |
| b-11 | 4 | 10-29 16:59 | 3.89 | 6.96 | 7.37 | 0.41 |
| b-12 | 4 | 10-29 21:23 | 4.12 | 7.37 | 7.73 | 0.36 |
| b-13 | 4 | 10-29 21:24 | 4.21 | 7.54 | 7.90 | 0.36 |
| b-14 | 4 | 10-29 21:25 | 3.34 | 5.99 | 6.21 | 0.22 |
| b-15 | 4 | 10-30 06:00 | 3.59 | 6.42 | 6.69 | 0.26 |
| b-16 | 4 | 10-29 17:00 | 1.88 | 3.36 | 3.76 | 0.40 |
| b-17 | 5 | 10-30 11:15 | 2.92 | 5.23 | 5.43 | 0.20 |
| b-18 | 5 | 10-30 14:47 | 1.90 | 3.41 | 3.57 | 0.16 |
| b-19 | 5 | 10-30 15:06 | 2.98 | 5.33 | 5.49 | 0.16 |
| **Block B** | | | **71.81** | **128.55** | **135.39** | **6.84** |
| cfy-1, cfy-2 (B10 certify) | | 10-29 13:52, 14:02 | 1.40 | 2.50 | 3.35 | 0.85 |

GPU $ = billed GPU-hours × $1.79 (the zero-GPU restart time, if billed as time, is counted here at the GPU rate: an upper
figure). "Other" = billed − GPU $ (volume storage while stopped, and any CPU-only time). Every block-B pod still bills about
$0.27 a day for its stopped volume (stop, never delete).

## 4. What is left, and its cost

| Item | Cap-based (kit rate) | Estimate |
|---|---|---|
| b-20 (Safe LoRA, 3 units, cap 6.0 h) | $11.10 | about 3–4 GPU-h, $5.5–7 (b-15: 4 units in 3.59 h; b-16: 1 unit in 1.88 h) |
| HarmBench judge (72 units, 57,600 answers, cap 5.0 h) | $8.95 | $1.3–1.9 (scaled from block A's 23.9 min) |
| Granite judge (14,600 answers incl. the gate, cap 3.0 h) | $5.37 | $1.8–2.5 |
| **Total** | **$25.42** | **about $9–11** |

Plus the idle charge ($0.457/h now) until the user decides about the stopped pods.

## 5. Zero-cost work done while waiting (31 Oct)

- **Judge pre-check (runbook GB3, $0 option):** both judge bundles built on the Mac from the 69 ready units with scratch tags
  and checked by the pod's own `pod_job.py verify`: HarmBench 428 files, Granite 451 files, one group, 69 units, no refusal.
  Every B10 unit (ref_eval, Safe LoRA) passed the pod-side check, which no real judge pod had run before. Evidence:
  `tmp/gi-viii-notes/judge-b-predry-20261031.md`. The bundles (answer text) were deleted right after.
- **Interim backup:** `backup-2026-10-31-stage1-block-b-interim`, private draft release
  (https://github.com/4r4cn1d0/attribution/releases/tag/untagged-d4522a8ecb8f5b46ee6f): every stage-1 host except b-20,
  5,944 files, 0 scan hits (HF_TOKEN and RUNPOD_OPERATOR_API_KEY values and 25 pod IPs checked), download-back hashes OK.
