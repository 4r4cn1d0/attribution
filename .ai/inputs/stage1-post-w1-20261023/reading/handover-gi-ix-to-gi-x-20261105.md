# Handover: General Implementation IX -> General Implementation X (5 Nov 2026, about 10:10 UTC)

Written by GI IX (the main-study lead) at a natural milestone: the OLMo 3 probe build is verified and merged, and the
next task (the 7-8B tier's $0 preparation) is large and starts with many lead rulings, so it is better begun with a
fresh context (GI IX was at about 66%). The user's standing rules: keep going, never let a lead chat auto-compact,
start the next General Implementation chat with a full note (memory `never-compact-handoff`); no approval questions for
planned steps (`no-approval-questions-planned-steps`); the ambitious default with a pre-set fallback. Read this note, then
the top of `research/FOCUS.md` (newest entries start at about line 74), then continue in the plan's order.

## Where the study is (branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD after this note; all pushed)

- **Stage 1 (OLMo-2-1B) is read** (1 Nov; FOCUS "THE STAGE-1 READING IS DONE"): P1 A1 vs R better +6.33 pp; P2, P3, P5
  equivalent; P4 S1 vs a0 worse (U) -2.31 pp, below the 5 pp margin; P6 S4 vs S1 better +18.28 pp; best feasible repair S4
  (15.97 pp of about 45); no data repair beats every model-level reference. All three stamps are anchored (blocks
  974039/974047, 974167, 974182).
- **Stage 1b is closed (2 Nov).** Kit round 35 (block P) merged at `f6c5017`; the construction checks' hashes at
  `49821a0`; the pre-launch stamp anchored in block 974195; pilot P on p-1 (2.67 h, about $4.83): **label STOP**
  (Lambda_plant +3.94 pp, SE 0.62, df 6.27, one-sided 90% lower bound +3.05 pp; below the 5 pp floor). By the frozen texts:
  no main sweep, no F9, K7 not run; the construction checks were opened and published (`fb24c0a`; only the content
  classifier ranks the planted cell first). Backup `backup-2026-11-02-stage1b-pilot` verified; p-1 deleted on the user's
  yes (`427dfbc`). Stage 1b's plant/decoy path rule has lifted (final stop).
- **OLMo 3 7B probe: built, verified and merged (`b93867a`, 5 Nov).** Build `wf_6aad406f-1cc`, verify `wf_5089d6de-4c3`
  (one major defect fixed: the preflight now decides on the output side only). Merged: `scripts/cuda_preflight_olmo3.py`
  (+ `scripts/tests/`), `experiments/safety_selection/configs/study-kt-data-dolly-olmo3.json`, `runkit/family-probe-olmo3/`,
  nine recipes `study-kt-olmo3-7b-r64-*-20261104.json`, the control-token count and the Gate A tool copy; the engine test
  `test_ss_family_codec.py` names OLMo 3 (engine identity unchanged). Suites green under both environments. The pre-run
  record `olmo3/olmo3-pre-run-record-20261105.md` (input choices, P0-P4, predictions, the lead's D-O4 ruling) is committed
  before any OLMo 3 fine-tune. The prepared set `tmp/kt-prepared/prepared-kt-dolly-olmo3` (manifest `8a196f6d…`,
  construction `2f5802f5…` = OLMo-2's) was built by the lead from the two sources restored on the user's yes
  (`tmp/kt-sources/`, `tmp/v3-prepared/`; `e89d74f`). **Remaining before a launch:** the kit's working copy takes the
  prepared-set pin `8a196f6d…`; the dry pack and check per `runkit/family-probe-olmo3/README.md`; the probe pod launches
  only on money in the account by 13 Nov (money check C1 on the live balance), else OLMo 3 goes to level 0 at 13 Nov 23:59
  UTC. The user said "Yes, build it" and expects the money by 13 Nov (`olmo3/user_yes_build_olmo3_20261103.json`).
- **The 7-8B tier: planned, nothing built.** The readiness plan and its adversarial check (usable with corrections) are
  at `78b/readiness-20261105/` (`942a432`); FOCUS's entry "THE 7-8B READINESS PLAN IS BACK" gives the corrected tracks and
  calendar. The check's corrections govern. **NEXT, in order:** T1 the lead's Part 1 rulings and text (S, SR-2, thresholds,
  F, RP decision 5, the Llama 1103 rule, the kit route, 4 arms per pod, the S4 add-dose arm's seeds; record each under
  `.ai/inputs/stage1-post-w1-20261023/78b/` as the lead's ruling under the delegation); then a build round for T2
  (`runkit/stage1-78b/rules_78b.py`, measured basis, KCR's tests), T3's $0 Llama sealed set (remove lists equal to the
  sealed R_d1-5 and stage 1's R_d6-8; S3/S4/dose edits per model), T5 the noise reader, T6a the two recipe-S_78 configs, in
  5-12 Nov; then the kit's block-0 subset with the scorer and anchor passes and the gated-token launch path, T6b/c and the
  Part 1 freeze in 12-19 Nov; dry packs 19-20 Nov; money about 20 Nov from a source other than BlueDot (the user, in the
  grant session); option B (both families) if the money is in the account, else C. Also at $0: read the 1B S4 build
  record's kept counts (sizes the dose arm's fallback; M2) and run the Llama G1 $0 check before Part 1 freezes. Only the
  money, the HF token at each Llama launch, deletion yeses and an H (a)/(c) choice need the user (correction C13).
- **The S4 dose arm** (the user's "Yes, add it", `reading/user_yes_s4_dose_arm_20261101.json`): goes into the stage-2 and
  7-8B pre-registrations before any repair outcome of those models; secondary, its own paired reading (correction C2);
  named "S4 add-dose".

## Money, pods, usage

- RunPod balance $22.64 (2 Nov 09:03 UTC), storage about $0.026/h, nothing running; kept stopped pods gateb-w0b-2 and
  probe-olmo2-1b-1102 (the plan keeps them; delete only on the user's yes after a backup). Tell the user below $10.
- Claude usage (5 Nov 10:05 UTC): all-models 7%, Fable 14% this week (reset 2026-11-12T09:00 UTC). The 1-7 Nov week
  reached 96% because of three build rounds; pace rounds and keep a reserve; tell the user above 90%.

## Other threads (not the lead's work unless the user asks)

- A Substack draft on the stage-1 result is committed (`writing/substack/2026-11-04-stage1-result-DRAFT.md`, `0d134da`,
  the FAQ chat's draft with the lead's six corrections); the user posts it; check ICML 2027's blog rule first.
- The BlueDot grant analysis ran in its own session; the user then said "fuck the grant im talking about the project".
  Keep the lead chat on the project. The 13 Oct BlueDot application was declined (recorded, `70201a3`).

## How GI IX worked (rules not all in memory)

- Main checkout `/Users/spiderishi/Coding/attribution`; your session's worktree is an old branch: use absolute paths.
  The Edit/Write hook blocks the main checkout: write with Bash or Python, commit by explicit paths, run
  `tmp/minimal-experiment-20261002/venv/bin/python -B scripts/stage1/commitments.py check --repo /Users/spiderishi/Coding/attribution`
  after each commit, push the working branch only (never force). GitHub sometimes returns 500 on push: retry in a
  background loop.
- `date -u` in its own call right before writing any time. Never open `tmp/hlc/`, `tmp/hlc-inputs/`, judge outputs, seals'
  files except through readers, `tmp/stage1-olmo/retrieved/` except by exact path and SHA-256, or the hidden and selector
  banks (now also in `tmp/v3-prepared/`). Never mention the side paper in the lead chat.
- Build rounds: builders in detached scratch worktrees (or one combined worktree when tracks must fit together), one
  adversarial verifier per track, one fix round, a re-verify; agents never change git state; the lead merges by explicit
  paths after its own suites and mutation specs as background Bash jobs; workflow agents on Fable while Fable < 95%.
- Long waits: a background `while [ now < T ]; do sleep 120; done` timer wakes the chat (robust to sleep).
- Keep the Mac lean: delete scratch and staging after verified backups; request keep-awake for long work.
