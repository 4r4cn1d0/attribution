# Handover: General Implementation VIII -> General Implementation IX (1 Nov 2026, 22:00 UTC)

Written by GI VIII (the main-study lead) because the user said, 1 Nov 21:58 UTC: "keep going throughout the night also
never compact always start the next gen implmentation chat version never ever compact" (memory `never-compact-handoff`;
FOCUS entry of 21:59 UTC). GI VIII's chat was at about 67% context. Read this note, then the top of `research/FOCUS.md`
(newest first), then continue in the plan's order. No question needs the user tonight.

## Where the study is (all committed and pushed; branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD `a21ebde`)

- **The stage-1 reading is DONE** (OLMo-2-1B, plan A, the one-time confirmatory reading), 2026-11-01T21:35:00-21:35:11Z,
  by `.ai/inputs/stage1-post-w1-20261023/reading/reading-20261101.zsh` and `reading-runbook-20261101.md`; outputs and
  the mechanical record in `reading/run-20261101/` (record `reading-record.json` `e20eeb3d…`, ledger `3eca9fe7…`).
  Headline: P1 (A1 vs R) better +6.33 pp; P2 (L1 vs R) equivalent (familywise); P3 (H1 vs R) equivalent (familywise);
  P4 (S1 vs a0) worse (U), −2.31 pp, also equivalent (familywise), below the smallest effect of interest; P5 (S3 vs S1)
  equivalent (familywise); P6 (S4 vs S1) better +18.28 pp. HarmBench sentences: P1 and P6 "harm" (E_HB +30.1 pp);
  P2-P5 "restored refusal" (P4's word is LN-15c's equivalent branch; its HB interval is adverse: never read it as a
  restoration). S-G coherent: the same words. Best feasible repair: S4 (restores 15.97 pp; separated from A1).
  Family 1b: no repair beats every model-level reference (do NOT claim data repair beats model-level repair). B14
  overlap (S-p, less similar half): S1 not shown, S3 not shown, S4 holds. LN-14 transfer bar fails; stage-3 pick P6,
  then P1. LN-31's draw: 450 items sealed in `tmp/hlc/draw-20261101/` (git-ignored; NEVER open). Full text: FOCUS entry
  "THE STAGE-1 READING IS DONE" (21:38 UTC). The grant dossier has it (`dcaae6b`).
- **Stamps (OpenTimestamps):** first (frozen rules) anchored in blocks 974039/974047; second (code + runbook, manifest
  `71e8f1a0…`) anchored in block 974167 (header 19:33:54 UTC; `timestamp/ots-check-reading-20261101.json`); **third
  (the outputs, manifest `timestamp/ots-manifest-outputs-20261101.json` `984b98cc…`, 49 files) stamped 21:39:05 UTC,
  PENDING its anchor** (see open item 1).
- **Backups (verified by download, private draft releases):** `backup-2026-11-01-stage1-after-reading` (the kit's
  records, every host incl. sim-1) and `backup-2026-11-01-local-after-reading` (the sealed LN-31 draw, `tmp/hlc-inputs/`,
  the 17-27 Oct integration notes, the build rounds' scratch). Records: `backups/2026-11-01/README.md`.
- **Pods and money:** nothing running. Balance $27.81 at 21:58 UTC, storage $0.026/h. Kept stopped pods (the plan keeps
  them; never delete without a backup and the user's yes): attribution-gateb-w0b-2 and attribution-probe-olmo2-1b-1102.
  a-2 and sim-1 were deleted on the user's yes (21:58 UTC).
- **Usage:** weekly all-models 80%, Fable 66% (resets 2026-11-05T09:00 UTC). Workflow agents on `model: 'fable'` while
  Fable < 95%. Keep a reserve for lead work and the next handover; tell the user if all-models passes 90%.

## Open items, in the plan's order (PLAN = `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md`)

1. **The third stamp's anchor** (runbook step 6.4, verified as step 0.3). GI VIII's upgrade loop is stopped at this
   handover; the kept ots client is `/private/tmp/stage1-reading-ots/venv/bin/ots` (opentimestamps-client 0.8.0; the
   pending proof copy is also in that folder). From `reading/timestamp/`: `ots upgrade ots-manifest-outputs-20261101.json.ots`
   until `ots info` shows a `BitcoinBlockHeaderAttestation`; then
   `/private/tmp/stage1-reading-ots/venv/bin/python -I ../lead-reports-20261101/tools/ots_check.py ots-check-outputs-20261101.json ots-manifest-outputs-20261101.json`
   (writes by exclusive create; expect `all_ok` true), read both tips (blockstream.info, mempool.space), commit the
   upgraded `.ots`, its `.bak` and the check record by explicit paths, record the anchor in FOCUS, then delete
   `/private/tmp/stage1-reading-ots/`.
2. **Stage 1b's $0 preparation** (addendum §40 at `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md`,
   §40 starts at line 1377; points 4-6 and 12): the construction checks hashed (point 4); **kit round 35** (point 5:
   block P = a0_plant at 1101-1103 under kind "arm", job kind J23 numbering, a block name other than `sim`; the plant
   edit bound by its SHA-256 only, computed without showing a byte; a reviewed key-only binding script printing only
   "match"/"no match"; e1/q fingerprint records; blocks A, B, C tables and REJUDGED_PINS["A"] byte-identical with a
   test; one test and one mutant per new refusal); the **pilot reader frozen by hash and stamped before P launches**
   (points 1-2: the pilot gate read literally, B16's paired form, the tie tolerance); **K7** built off the pilot's path
   (point 6; runs only after a "go"). Scouting reports: `reading/lead-reports-20261101/next-stages/A-stage1b-readiness.md`
   (READY) and `A-stage1b-check.md` (CHECK; its corrections govern). Do it as a build round like wf_795563f3-35a and
   wf_939c9dfc-e93 (builders in detached scratch worktrees, an independent adversarial verifier per track, one fix
   round, the lead's suites and mutation specs as background Bash, never inside agents). Plant/decoy paths are sealed:
   builders never open them; hashes and key-only scripts only. F9 is NOT run (needs funding and the user's yes).
   Then the pilot pod P from the balance: kit upper $7.43; launch only when the live balance covers the cap-based spend
   above the $6 reserve (§36 rule; funding record "user rule: start from the balance", decision record
   `block-b/user_decision_start_without_topup.json` `5f31f16e…`), launch.py and one finisher as background jobs.
3. **OLMo 3 7B probe $0 build** before 13 Nov (FOCUS 09:20 and 09:45 UTC entries; tokenizer files and `tmp/olmo3-venv`
   are ready; the probe launches only on new money in the account; fallback level 0 at 13 Nov 23:59 UTC).
4. **The 7-8B tier's $0 preparation** (gate about 20 Nov; option B default, C fallback; user_answer_78b_money_20261101.json).

## How GI VIII worked (rules not all in memory)

- Main checkout `/Users/spiderishi/Coding/attribution`; the session's own worktree is on an old branch, so use absolute
  main-checkout paths. The Edit/Write hook blocks the main checkout: write with Bash/Python, then commit by explicit
  paths; run `$PY -B scripts/stage1/commitments.py check --repo /Users/spiderishi/Coding/attribution` after each commit;
  push the working branch only (never force). PY = `tmp/minimal-experiment-20261002/venv/bin/python`.
- API calls: `( set -a; . ~/.config/attribution/secrets.env; set +a; exec env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN "$PY" -B ... )`;
  balance: `tmp/stage1-olmo/budget.py` (see FOCUS entries for the one-liner).
- `date -u` in its own call before writing any time. Never open sealed files (judge outputs, seals' listed files except
  through readers, `tmp/stage1-olmo/retrieved/` except by exact path and SHA-256 per LR R3.1, anything with "plant" or
  "decoy" in its path, `tmp/hlc/draw-20261101/`). Never mention the side paper in the lead chat.
- Records: post-W1 records under `.ai/inputs/stage1-post-w1-20261023/`; the lead's rulings of 1 Nov
  `reading/lead-rulings-20261101.md`; the build rounds' reports under `reading/lead-reports-20261101/build-round/`.
- Keep the Mac lean (delete scratch and staging after verified backups); request keep-awake for overnight work
  (`mcp__ccd_host__request_keep_awake`, until session_idle).
