# Stage 1, block A: cost and completion report

Written by the lead (General Implementation VII) on 27 October 2026 at 14:13 UTC (clock checked), after `seal.py block A`.
This is the "stop and ask" report after block A (REV4 §1.3; W1R (d) rules 9–10). **It gives cost and completion only.**
No U, HB, Granite, O, task-loss or coherence value appears here. Block A's outcomes stay sealed until block B is complete
or a recorded decision ends stage 1 without it (LW-35).

## 1. Summary

- **Block A is complete and sealed.** Seal `seals/block-A.json`, SHA-256 `6c6267c8b8d3476fba2fc5eb906abdc5ff80e18b418f543efb24a166d073e52d`:
  1,703 files (1,529 sealed, 174 readable), sealed 2026-10-27 at 14:10 UTC.
- **Every planned block-A job ran or has a recorded decision.** The kit lists nothing open (`block_a_open` empty, `not_run` empty).
- **Pod spend for the stage-1 funding group (S1-0, block A, the cert pod): $48.59** of GPU time, measured per pod from
  creation to the confirmed stop (D10). The group's funding record is $145.00 (`funding_block_a.json`, `3b6d41ad…`) and its
  cap-based need was $124.90.
- **The X → Y certificate passed** (`certificate_xy.json`, `2360b26b…`), so block B's engine-Y jobs (B+Qi) may run.
- **Live balance $156.89** at 14:11 UTC; no pod running; the stopped pods' storage costs about $0.21 an hour.
- **Next needs the user:** block B's funding event (a top-up for block B).

## 2. Completion, by launch

| Launch | Host(s) | What ran | Completion | Records |
|---|---|---|---|---|
| S1-0 | s10-1 | W1-18 alone | complete; branch 128 | FOCUS 25 Oct 11:30 UTC |
| Block A 0, diagnostics | a-1, then a-8 | J6 on a-1; J5, J7, J8 on a-8 | all complete; J5 was refused on a-1 by a kit defect (recipe S), fixed and moved to a-8 | FOCUS 25 Oct 12:16 and 13:08 UTC |
| Block A 1, LN-12 | a-2 | 19 jobs (J2 regenerations, O-ext, c0, LN-14, LN-15e) | 19 complete; LN-15e's 4 units (jobs 12–15) were not pulled, so LN-15e takes its FO-04 fallback | `unpulled-outputs-a2.json` `e897885c…`; addendum §29 |
| Block A 2–4, arms | a-3, a-4, a-9, a-10, a-11 | 20 arm runs: A1, L1, H1, S1, S3, S4 at 1102–1104; a0 and R at 1104 | 20 of 20 complete | FOCUS 26 Oct 06:41 and 27 Oct 03:39 UTC |
| (moved) | a-5, a-6, a-7 | setup failed on 25 Oct; stopped within 4 minutes; never pulled | moved to a-9, a-10, a-11 (a-7's four re-runs paid by the user's record) | `rerun-payment-a7.json` `0c686dc7…`; the seal lists them under `moved` |
| Block A 5, HarmBench judge | s1a-hb-1 | 21,600 answers over 27 units | complete, verified | `judges_block_a.json` `afdfd304…` |
| Block A 6, Granite judge | s1a-granite-1 | 5,400 answers over 27 units, plus the 200-item known-answer gate | complete, verified; the gate passed | the same |
| Judge files | — | 54 files (27 per judge) in `judges/A/` | the 54-file check passed; `record-judges A` valid | `judge_completion_block_a.json` `b75934a5…`; index `e946691f…` |
| Cert pod | cert-1 | C1 (R_1101 replicated on engine Y), C2 (B+Qi), C3 (a0 on 16 dev items) | 3 of 3 complete; the certificate passed | `certificate_xy.json` `2360b26b…` |

**The cert pod's pre-registered readings (training statistics and code checks; not outcomes):**
- C1, the X → Y certificate (YB X-5, X-6): 16 of 16 counted files equal under `removal_digest.py`'s rule; U labels and task loss equal.
  Four files outside the rule differ, as expected: COMPLETE.json, assets.json, identity.json (engine Y's code identity) and the timing ledger.
- C2, the binding check (addendum §22 point 1): label **"partly binding"** (not "equals recipe B by construction"), so B+Qi runs as registered.
  Its step-0 check: 38 of 38 steps, loss and objective finite, step-1 `max_abs_delta` 0.0.
- C3: complete; the light check passed.

**Not in block A, by the plan:** V2a (no script exists; it stays on its fallback, addendum §25 point 1); LN-15e's re-score units
(not pulled; FO-04 fallback).

## 3. Cost, by pod

Each pod's time runs from its `created_utc` to the earlier of its `finished.json` time and its first confirmed stop. Price is
the pod's own `costPerHr`.

| Pod | Funding part | Role | Created (UTC) | Minutes | $/h | Cost | Finish |
|---|---|---|---|---|---|---|---|
| s10-1 | S1-0 | w1_18 | 2026-10-25 11:04 | 23.1 | 1.79 | $0.69 | stopped |
| a-1 | block A | diagnostics | 2026-10-25 11:37 | 33.8 | 1.79 | $1.01 | review-needed-stopped |
| a-8 | block A | diagnostics | 2026-10-25 13:08 | 42.2 | 1.79 | $1.26 | stopped |
| a-2 | block A | job | 2026-10-25 13:09 | 430.7 | 1.79 | $12.85 | verified-and-stopped |
| a-3 | block A | arms | 2026-10-25 16:44 | 222.4 | 1.79 | $6.63 | stopped |
| a-4 | block A | arms | 2026-10-25 16:45 | 188.1 | 1.79 | $5.61 | stopped |
| a-9 | block A | arms | 2026-10-25 19:09 | 163.3 | 1.79 | $4.87 | stopped |
| a-10 | block A | arms | 2026-10-25 19:09 | 166.1 | 1.79 | $4.95 | stopped |
| a-11 | block A | arms | 2026-10-26 15:29 | 212.5 | 1.79 | $6.34 | verified-and-stopped |
| a-5 | block A | arms | 2026-10-25 17:08 | 3.9 | 1.79 | $0.12 | stopped (confirmed) |
| a-6 | block A | arms | 2026-10-25 17:09 | 3.6 | 1.79 | $0.11 | stopped (confirmed) |
| a-7 | block A | arms | 2026-10-25 17:10 | 3.1 | 1.79 | $0.09 | stopped (confirmed) |
| s1a-hb-1 | block A | judge | 2026-10-27 10:10 | 23.9 | 1.79 | $0.71 | verified, stopped |
| s1a-granite-1 | block A | judge | 2026-10-27 10:35 | 32.1 | 1.79 | $0.96 | verified, stopped |
| cert-1 | cert | cert | 2026-10-27 11:32 | 80.2 | 1.79 | $2.39 | verified-and-stopped |

| Part | Pod spend |
|---|---|
| S1-0 | $0.69 |
| Block A (pods and the two judges) | $45.51 |
| Cert pod | $2.39 |
| **Funding group total** | **$48.59** |

**Against the plan.** The group's funding record is $145.00 and its cap-based need $124.90 (each pod at its full cap). Measured
pod spend is $48.59, so about $96.41 of the record is unspent. Block A's contingency has $2.95 left (`plan.json`
`contingency.A.remaining_usd`): a-1's crashed J5 was paid from it; a-7's four re-runs ($9.49 declared) were paid by the user's
own record, not by the contingency. The two judge pods cost $1.67 together (estimate $1.3–2.0; upper $8.06); the cert pod $2.39
(estimate $1.8–2.8; upper $5.82).

**Not in the pod spend:** the stopped pods' 10 GB volumes (about $0.21 an hour now, account-wide, across every stopped pod
of every kit) and any Mac-only work ($0).

## 4. Decisions and deviations during block A (all recorded before the outcomes they could touch)

| When (UTC) | What | Record |
|---|---|---|
| 25 Oct 10:59 | The user: start block A from the balance; a $145 top-up for block A follows | FOCUS; `funding_block_a.json` `3b6d41ad…` |
| 25 Oct 11:37 | The cert pod moved to block A's last launch (a kit defect in B+Qi's recipe check, later fixed) | FOCUS |
| 25 Oct 11:41 | The user removed the kit's live-balance guard; the $10/h limit, the in-pod timers and stop-never-delete stay | `guard_off.json` `cabe7035…` |
| 25 Oct | D-3: S3's scorer on the union of J5's two passes; launches in parallel while the guard is off | addendum §28 |
| 26 Oct 06:41 | LN-15e's re-score units not pulled; LN-15e takes its FO-04 fallback | addendum §29; `e897885c…` |
| 26 Oct | The user paid a-7's four re-runs beyond the contingency | `rerun-payment-a7.json` `0c686dc7…` |
| 27 Oct 08:23 | Judges run by the runbook; the judge gaps are fixed before block B | addendum §30 |
| 27 Oct 10:42 | The cert pod's blockers (cert_spec not packed; C1's registry; the seal's moved hosts) fixed by kit rounds 30 and 30a before the cert pod and the seal; C1 seeded, not run without `--replicate-of` | addendum §31 |

Kit rounds in block A: 29 (`3e2f594`), 30 and 30a (`62b89bd`; 347 mutants, 345 killed, the 2 survivors expected).

## 5. Open before block B

1. **Block B's funding event** (the user's top-up, stated as for block B). Block B: B10's certification pod; all eight arms at
   1105–1107 (24 runs); the references (the safety prefix, adapter scaling, Safe LoRA, recipe G and B+Qi); the judges. The
   pre-registration's estimates: $31–53 for the runs and base references, plus about $51–56 for the reference increment
   (LN-15b). The kit computes the exact cap-based need at `init-block B`.
2. Before block B's reading: the B16 HB-C halves and the LN-15e Mac reading script (on its fallback).
3. Kit gaps found in round 30, for block B: no not-run route for block B's judge launches; whether `ref_train` units are
   judged; one judge-completion record per block; block B has no pinned re-judged units yet.
4. The user's own actions: posting the OSF deposit; Gemma access (HTTP 403).
5. Stopped pods whose volumes may be deleted (each deletion needs the user's yes and a verified backup first).
