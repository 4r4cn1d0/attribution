# R2 K2 re-verification after the fix round (K2V-1 to K2V-11; GXB R-43 to R-48)

Started 2026-11-09 04:02 UTC; written 04:13-04:20 UTC (`date -u`). Target: B/ws-k2 after the fix round. M: the files
hash to the builder's fix-round table (plan_tool.py `2678d34f…`, orchestrate.py `6abdea19…`,
tests/test_planning_ab_78b.py `ce3b9c3f…`, tests/mutation_spec_scorer_78b.json `d7b2db71…`); the other first-round
files are unchanged (`cmp` against R/r2-k2-scratch/fixpre/). orchestrate.py changed in `w1_18_hold` only (M:
`git diff bfda225`). I edited nothing in ws-k2 or MAIN; my files are this report and R/r2-k2-reverify-scratch/
(probe tests, scratch repo copies, mutant specs and results). Sandboxed runs; no network, pod, spend or message. Tags:
M measured (a command or a probe test), R read (path:line, WS), E estimate, I inference.

## Verdict

**DEFECTS (one Major, three Minor).** The three first-round majors are closed: block B re-derives SR-2's status and
refuses every wrong status and plan I tried (K2V-1/R-43); the part survives a deferral, a crash then deferral and a
pre-job requeue (K2V-2); the orchestrator reads BRANCH_78B by its bytes (K2V-4/R-45). K2V-3 and K2V-5 to K2V-11 are
closed. Block 0 is unchanged; record-done still leaks nothing; the 7-8B suite passes (612); all 45 new and re-targeted
scorer mutants and a 10-mutant sample are killed (check 5). But R-44 holds only until block A's last release: an edit
of record-done's code or of `blinded_sigma.py` after it (the two codes run after that release) is not detected, and
SR-2 is recorded adopted; the first round's check of `blinded_sigma.py` at record-plan-b-78b was removed in this
round (K2R-1, a regression). Three Minor items remain (K2R-2 the mismatched re-run, K2R-3 the blinded output's
sigma, K2R-4 two test gaps: 2 of my 4 extra mutants survive as gaps, 2 are masked).

## Defects

| Id | Severity | File:line (WS) | Defect | Failure scenario | Fix |
|---|---|---|---|---|---|
| K2R-1 | Major (regression; R-44's intent) | runkit/stage1-78b/plan_tool.py:4391-4400 (blinding_from_block_a calls `sr2_blinding_reading(check_files=False)`), :4403-4419 (sr2_status, plan_b_status_check), :4119-4121 and :4259-4262 (the only file checks: block A's init and release) | The blinding record's four file hashes are compared with the files only at block A's init and release. record-done (the A copy's plan_tool.py) runs after the last release, and `blinded_sigma.py` runs after block A; record-plan-b-78b, init-block B and release B check only that the pinned record is the one block A snapshotted. The first round's record-plan-b-78b refused a record whose blinded_sigma.py hash was not the checkout's; this round removed that check (its test assertion "verified another scripts/scale78b/blinded_sigma.py" is deleted and K2-m-blinding-script-unchecked is re-targeted to block A's release; R: R/r2-k2-scratch/fix.diff). | M (probe R4b): the A copy's plan_tool.py edited after block A's release; record-done writes the part, write-blinded-inputs writes the inputs file, record-plan-b-78b records SR-2 **adopted**. M (R4c): scripts/scale78b/blinded_sigma.py edited after block A's init; record-plan-b-78b records SR-2 adopted. R-44: "a later change to either code voids the verification (P1 §6.4: ... on the code that runs)". | In sr2_status (record-plan-b-78b, init-block B, release B) re-hash the record's files: blinded_sigma.py and the two tests at ROOT, and each gate family's block-A copy's plan_tool.py (tmp/<prefix><F>-A/plan_tool.py), and refuse on any difference; a block-A record-done may also refuse (or flag) when its own plan_tool.py differs from the snapshot record's. A test per case and a mutant. |
| K2R-2 | Minor | plan_tool.py:4579-4602 (block_a_cells), :5107-5109 (requeued_attempts) | After the kit's own `requeue HOST --rerun-mismatched SHA` in block A, the old attempt stays "complete" and the re-run completes on the new host; block_a_cells refuses "two complete units ... the lead decides", and the kit has no decision route for it, so the part can never be written. | M (probe R2c, the environment mismatch stood in by patching `mismatch`): record-done of the new host prints no part; write-blinded-part refuses; block_a_cells: "A1 at 1102: two complete units (olmo2-7b-a-1, olmo2-7b-a-7); the lead decides". At 7-8B this path needs an imported environment reference (plan.json `reference` is null in the skeleton, R: :1697, :5092), so it is not on today's route (I). | Skip a complete job whose complete_sha256 is in requeued_attempts(plan) (its re-run's `mismatched_complete_sha256` names it), or refuse --rerun-mismatched in block A by name. |
| K2R-3 | Minor (needs the lead) | plan_tool.py:4422-4460 (record_plan_b_78b), :3846-3858 (blinded_output_check) | blinded_sigma.py's output is checked for form and for the kit inputs' hash only; its sigma is never re-derived. | M: probes R4b, R4c and R5a pass a hand-written output (`sigma_A_pp` 4.0 or 3.0, the kit inputs' SHA-256) and get SR-2 adopted with the plan that sigma gives. Like K2V-9 (the noise plan), it needs a hand edit of a pinned script's output. | record-plan-b-78b runs `blinded_sigma.read(BLINDED_INPUTS, sha)` itself (it returns sigma_A and df only) and refuses an output that differs; or the lead rules the output's provenance a limit. |
| K2R-4 | Minor (test gaps) | plan_tool.py:4395 (blinding_from_block_a's loop), :4735 (kit_inputs_check's hash compare) | Two new checks have no test that fails when they are weakened: under [B] the second family's block-A snapshot, and the kit inputs file's hash against the output's `inputs_sha256`. | M (mx.json): X-snapshot-first-family-only (only the first gate family's snapshot checked) and X-kit-inputs-hash-unchecked (the file must equal the rebuild but may hash to another value than the output names) SURVIVE. The code is right today (M: my R1g refuses Llama-3.1-8B's other snapshot; R: :4735 compares the hash), but nothing in the suite holds it. | My R1g as a suite test, and a record-plan-b-78b case whose output names another inputs hash than the kit file's; the two mutants in the spec. |

## Check 1: the three majors

**K2V-1 / R-43 (closed).** M (R/r2-k2-reverify-scratch/test_k2r_probe.py, sandboxed, 7 of 7 refuse as expected):
R1a my P3a (hand "adopted, B9" while the blinding test is not verified) and R1b my P3b (hand "not adopted, plan A"
while both triggers pass) refuse "GXB R-43"; R1c not adopted with the wrong reason (simulation_reading for an
unverified blinding test) refuses; R1d a governing simulation re-pinned above 6% (1,300 of 20,000) refuses "the pinned
records give False (simulation_reading)"; R1e a blinding record re-pinned after init-block B refuses at release ("was
not planned under the pinned blinding record"); R1f the right status with a wrong plan (B9 on N's plan A) refuses
"GXB R-24"; R1g Llama-3.1-8B's block-A copy snapshotted another blinding record: block B refuses. The builder's
test_r43 holds init and release. R7 (test_k2r_probe_b.py): block A run in its own copy, then a block-B copy in the same
repository records PLAN_B_78B through the real kit rebuild (no stub) and plans plan A, 23 runs; an edited inputs
file then refuses.

**K2V-2 (closed for the routine paths).** M: R2a my P9 (a deferral) writes the part with the cell from the new host;
R2b a crash then defer (the crashed job and two not-started jobs moved) writes the part, every moved cell from the new
host; R2d an open job no move took: no part, write-blinded-part refuses. The builder's tests add the double unit (by
edit), the moved-but-not-carried job and a pre-job requeue of a whole host. Residual: K2R-2 (the mismatched re-run).

**K2V-4 / R-45 (closed).** M: R3a a released scorer-block o_only pod is not held with BRANCH_78B pinned, held once
the pin's SHA-256 is edited and once its path leaves the repository, and not held again with the pin restored; R3b
the W1-18 pod itself runs with the branch null; R3c a block-A arm pod is not held, and is held once its branch file
is off its bytes (blocks A and B now take the hold too, through rules_78b.bank500_problem). Block 0 is never held
(the builder's test_k8; block 0's kinds read no 500 bank).

## Check 2: R-44

- The record form is {kind, version, verified, files, commit, evidence, utc, recorded_by}, files exactly
  blinded_sigma.py, its test, plan_tool.py and test_planning_ab_78b.py by SHA-256, a 40-hex commit (R:
  plan_tool.py:3711-3717, :4368-4388). Init-block A refuses while the record is null, off its form or stale (M: R4a,
  plan_tool.py edited after the record: "plan_tool.py than the one that runs here"; the builder's test_r44 covers each
  file, a bad commit and extra files). Release A refuses a re-pinned record and a plan_tool.py edited after init (test).
  record-plan-b-78b refuses a record no block-A copy snapshotted (test; M: R1g at block B).
- Gap: K2R-1 (after the last release). The commit is checked for form only (the builder's open point 2), and the
  files are this copy's and the checkout's, not the packed bundle's (open point 1): I agree that is the right place,
  since record-done and blinded_sigma.py run on the Mac (I).
- Note: init-block A's `--dry-run` now refuses before the blinding record exists (R-44 as ruled), so block A's need
  cannot be printed before the verification; `deal A` still prints its pods (I).

## Check 3: K2V-3 and K2V-5 to K2V-11

- K2V-3 (closed): M R5a my P4a: a hand-made inputs file at the kit's place refuses at record-plan-b-78b ("is not the
  one the kit writes"); the kit's own write-blinded-inputs file then gives "adopted, plan A". R5b my P4b: a part with
  one cell edited refuses at write-blinded-inputs; the old `--part ... --out` form is gone (argparse exit 2). R7: init-
  block B with the real rebuild. Limit (M, R5c): an edit of block A's plan.json itself, with the part written again
  from it, passes (plan.json is the kit's own state; I, not a defect).
- K2V-5 (closed): my anchor-stopped probe on the new API (R6d: OLMo-2-7B stopped, engines split per role, record-done,
  write-blinded-inputs, the real blinded_sigma.read): df 6, sigma equal to numpy (rel 1e-12); the builder's test_k2v5
  holds it, and V-part-design-always-full, V-part-stop-record-dropped and V-merge-stop-path-not-rebased are killed.
- K2V-6 (closed): all 16 of my first-round survivors are in the spec and killed (shards 0-1).
- K2V-7 (closed): s4_kept expects "s4_192" iff kept >= 192, else "s4_top" (R: plan_tool.py:3967-3969); the test covers
  48, 49, 95, 96 (both tops), 97, 191, 192 (both) and 47; K2F-m-top-dose-96 and K2F-m-top-dose-ge killed.
- K2V-8: see check 2 and K2R-1.
- K2V-9 (closed): the noise plans are re-derived from their own sigma_pp and the seed rule must be the pooled reading's
  (R: :3797-3827); test and two mutants killed. The real noise_reading output carries `seed_rule == pooled.seed_rule`
  and each rule's sigma_pp (R: scripts/scale78b/noise_reading.py:281-299, :384-390, :443-449).
- K2V-10 (closed): the five 1B block-A commands refuse by name (test; K2F-m-1b-commands-reachable killed).
- K2V-11 (closed): record-done keeps only the runner's reason codes; the test reads them from the runner's source
  (R: setup/job_runner_stage1.py:99-100, :443; the runner's base_record copies no plan reason, :955-957, so the
  planner's own "environment-mismatch" and "stranded-regenerate" never reach JOB-DONE). M: R6b a deferral with code
  s_obs passes; R6c a planted reason refuses with a text that names no value.

## Check 4: no regression

- Block 0: my block0_probe.py on the fixed ws-k2 (sandboxed): plan.json byte for byte equal to the bfda225 and
  3481d85 outputs I saved in round 1 for both families (14,114 B `f72de041…`, 14,613 B `f5ac8a95…`), and the dry-run
  and real printouts and returns, the operator log, `deal 0` and a second release all equal (M). Block 0's record-done
  is now stricter on reasons (K2V-11) but takes every code the runner writes (I).
- Blinding: R6a the success path changes exactly the part, the operator log and plan.json, none holding a planted
  value; R6b the crash and deferral paths; R6c the refusal paths (M).
- Weakened tests: the deleted assertions are the old CLI's (`--part`, two parts, the families message) and one stub
  message, each replaced by a stricter check, except one: "verified another scripts/scale78b/blinded_sigma.py" at
  record-plan-b-78b, whose check was removed (K2R-1). Block B's tests stub `kit_inputs` (R:
  tests/test_planning_ab_78b.py:521-531), so no suite test runs init-block B through the real rebuild; my R7 does.

## Check 5: suite and mutants (M)

- 7-8B suite under the sandbox, from ws-k2: **612 passed** in 34 s (04:14-04:15 UTC; R/r2-k2-reverify-scratch/
  suite-78b.log). No `__pycache__`; ws-k2's `git status` unchanged.
- Scorer spec, with the builder's runner from ws-k2 (sandboxed; every baseline exit 0; shards of 5-10, two or three at
  once, each under 10 min): the 38 added and 7 re-targeted mutants **45 killed**, and a seeded random sample of 10 of
  the other 226 (seed 20261109: K2-m-blinded-sigma-unchecked, K4b-m-done-wrapper-whole, K4b-m-engine-x-retrain-any,
  K4b-m-pins-rep-no-s3orig, K4b-m-plan-two-jobs, K4b-m-release-s78-packed-unchecked, K4b-m-runner-route-off,
  K4bf-m-hm4-anchor-hash-optional, K4bf-m-hm12-engine-x-always, K4bcr-R1) **10 killed**; 0 survived, 0 invalid
  (m0.json-m6.json). Every new find text occurs exactly once (M: count).
- Four extra mutants of mine on the new code (xspec.json, made by make_xspec.py, each find text exactly once; run from
  a scratch source root that differs from ws-k2 only in the spec; baseline exit 0; 04:15-04:17 UTC): **4 survived**
  (mx.json). X-snapshot-first-family-only and X-kit-inputs-hash-unchecked are test gaps (K2R-4).
  X-cells-missing-run-ok (block_a_cells' "a run with no complete unit") is masked in every flow I found: each missing
  run first shows as an open job, and a part on disk implies a plan with every launch released (I; weak, not listed).
  X-carried-any-job loosens `carried`, a pre-existing function (block_open_jobs' too) that the scorer runner's tests
  do not reach; here the set check masks it (I; outside this round).
- Not run by me: the rules, runner and gated specs (the builder: 248, 35, 128 killed).

## Commands run (exit 0 unless noted)

`date -u`; reads (cat, sed, grep, git status/diff, shasum, cmp, diff); a scratch repo copy of ws-k2 (kit copied, the
rest linked) for test_k2r_probe.py (24 passed, 1 failed on the first run: R2c needed a stand-in mismatch, then
passed) and test_k2r_probe_b.py (1 passed); block0_probe.py (round 1's) on ws-k2; the 7-8B suite; the scorer runner,
7 shards from ws-k2 and 1 shard of my 4 extra mutants (each exit 0). The scratch repo copies, the runner copies and
the pytest temp folders were deleted afterwards (kept: the probe files, the specs, the result files and logs, the
block-0 summary). ws-k2's `git status` is as the builder left it and holds no `__pycache__` (M).

To re-run a probe: copy ws-k2's runkit/stage1-78b into REPO/runkit/stage1-78b, link ws-k2's other top-level entries
and runkit folders into REPO, copy the probe file into REPO/runkit/stage1-78b/tests/, and run
`cd REPO && sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q <the file>`.
