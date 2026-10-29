# Stage-1 kit (runkit/stage1-olmo)

The run kit for stage 1 on OLMo-2-1B (B15; brief notes/b15-brief.md, the lead's §8 defaults in the addendum §17): it
plans the blocks (`plan_tool.py`), packs one setup per engine (`pack_setup.py X` or `pack_setup.py Y --y-tree DIR`),
launches and drives each pod (`launch.py`, `orchestrate.py`), runs the jobs J1-J18 on the pod
(`setup/job_runner_stage1.py`), pulls and finishes them (`finisher.py`), seals each block (`seal.py`), backs up the
records (`backup_records_stage1.py`) and lists the units for the judges (`judge_units_stage1.py`). The rules, caps and
money live in `stage1_rules.py`. Pods are named `attribution-s1-HOST` (never `attribution-gateb-`); the budget guard
reads the caps of every `family-probe-*`, `gate-b-olmo*` and `stage1-olmo*` working copy and shares Gate B's lock
(`family-probe-budget.lock`).

## Money (brief §5)

Planning price $1.85/h at the guard, spend rate $1.79/h, create refused above $10.00/h (or a missing or non-finite
price), $6 reserve after every running pod at its full cap plus the new pod at its full cap, contingency factor 1.25.
A funding event is the user's own rule, verbatim: "A funding event is any RunPod top-up I make and say is for that
stage-1 block (block A first); it must cover the block's cap-based need before the block launches." So
`plan_tool.py init-block BLOCK --funding FILE` refuses unless FILE is {block, amount_usd, utc,
source: "user RunPod top-up", user_words (verbatim), recorded_by}, its block is the block's funding group, its utc is
UTC and not in the future, and amount_usd >= the cap-based need (1.25 x the guard's worst path, brief §5.2). S1-0 and
the certificate pod are paid from block A's event, and that event must cover the WHOLE block's need before S1-0
launches (addendum §20 point 1). Round 3a makes this exact with the block-A plan (below): S1-0's need is the need of
every launch the plan holds (round 3b: $130.59 for the kit default under Branch full and plan A; $129.48 under the
C3 fallback; all five arm pods in one launch $141.63), so one top-up of that amount launches S1-0, the cert pod and
all of block A, and a launch outside the plan refuses. The top-up asked of the user for block A (addendum §25
point 3; the lead's round-3c decision) is **$144**: the worst case over the re-plans the lead counted, $143.19 (two
LN-12 pods with all five arm pods in one launch), rounded up to the dollar. It does not cover every valid re-plan
(round 3c section below); the kit refuses a re-plan that S1-0's record does not cover.

### The block-A plan (round 3a)

The plan is a pre-set, outcome-free list of the group's launches in this order: S1-0 (W1-18 alone) -> the cert pod
(C1, C2, C3 unless its fallback) -> the diagnostics pod (J6, J5, J7, J8; J5's s3_orig pass runs after J6 on the
same pod) -> the LN-12 pod(s) (J2 with its linked J3 for a0 and R at 1101-1103, LN-15e's retrain + re-score pairs for
a0 at 1102 and 1103, theta0's 500-bank pass, theta0's LN-14 report under Branch 128, and c0 on engine X) -> the arm
launches (a split of the deal's pods, in order) -> the judge launches (HarmBench: 800 answers per unit at 0.25 s;
Granite: 200 per unit + the gate's 200 at 0.5 s; the launcher's cap rule; block A's new units plus the 7 re-judged
units: the six reused a0/R units and theta0's, §17 Q14 and §25 point 2). The cert pod may instead be the last launch
(a re-plan, for LS-03 (a)). Every plan records V2a's fallback in `not_in_plan` (round 3b).

    $PY -B plan_tool.py write-block-a-plan --out FILE --recorded-by WHO [--split 2,2,1]   (prints path, sha256, need)
    $PY -B plan_tool.py block-a-need FILE --sha256 H     (every pod's cap, spend, unmeasured terms; terms; needs)
    $PY -B plan_tool.py record-block-a-plan FILE --sha256 H   (before S1-0's init; refused once S1-0 or cert exists)
    $PY -B plan_tool.py record-block-a-replan FILE --sha256 H (after it; see below)

If no plan is recorded, the first init of the group records the kit's default (split 2+2+1 under plan A, 2+2 under
plan B). Each pod counts at the larger of its Branch-full and Branch-128 cap and spend (for the default, Branch full
is the larger for every pod). Every unmeasured cap is the brief's estimate and is listed in `unmeasured`.
Every init-block and release of S1-0, cert and A maps its launches onto the plan in order and refuses another order,
more pods in a launch, a pod with a larger cap or spend, a judge launch with more units, or a job the plan launch does
not hold. A planned launch may be left out, or its pods spread over consecutive launches: neither raises any term of
the need (a pod's spend at $1.79/h is below $1.85 x its cap). The plan is re-derived at every use (a lead's file by
its SHA-256; the default from its recorded inputs), so a hand-edited plan.json refuses. If the plan-A/B record's code
differs from the plan's, block A refuses until a re-plan. A re-plan is recorded only if every planned part fits it and
the group's first funding record covers its need; the old plan is kept in `block_a_plan_history`.

Default plan, plan A (cents; round 3b, `notes/b15r3b-build-evidence/funding.json`): Branch full 2+2+1 needs 13,059
(base 10,447: the last, Granite, term); the worst split, all five arm pods in one launch, needs 14,163. Branch 128:
12,266 and 13,404. (Round 3a's figures, 11,516 / 12,734 / 10,723 / 11,976, are superseded.)

Round 3a's fix round (`notes/b15r3a-fix.json`):
- A plan must hold all of block A's G5 content: C3 (unless its fallback) on the cert pod; J5-J8 on the
  diagnostics pod; on the LN-12 pod(s) c0, LN-15e's two pairs (round 3b), a J2 for each of a0 and R at 1101-1103 and,
  unless the O-ext fallback (c) is recorded, each one's J3, theta0's J3 and theta0's LN-14 report; each judge over at
  least the new plus the 7 re-judged units. A plan without one of them refuses, so it can never lower S1-0's floor.
- Every later init of the cert pod and block A must also be covered by the group's FIRST funding record (S1-0's),
  which is re-hashed from its file: keep that file at its recorded path, unchanged. With S1-0 planned and no plan
  record, an init refuses (record a re-plan). A kit-default record must carry the kit's own inputs.
- The group's parts are read in planning order (`seq` in each block record), so a re-plan after block A works.
- A pod that received deferred or re-queued jobs is checked against the plan as it was planned (`plan_shape`):
  those moves are paid from the contingency, outside the plan, as in rounds 1 and 2.
- (Round 3b: LN-15e's re-score is now in the plan; only V2a stays out, on its fallback. See below.)
- The judges run one after the other (HarmBench, then Granite): the need assumes it, the kit cannot see it (the judge
  launcher runs outside plan.json). In parallel the default would need $130.78 (round 3b).
- The default ties block A to 2+2+1: arms launched as 5-in-one are a merged launch and need a re-plan of $141.63; a
  cert-last re-plan (LS-03 (a)) needs $132.83 (2+2+1) or $136.49 (5-in-one). c0 on a second LN-12 pod adds one
  42-min overhead before the arms, so two LN-12 pods need $132.16 (2+2+1), $138.94 (1+4) and $143.19 with all five
  arm pods in one launch (round 3b fix, VP3b-1). Round 3b's $142 did not cover that last re-plan
  (test_a_142_top_up_covers_two_ln12_pods_only_...); round 3c's $144 does, with the limits stated below.

### Round 3b (addendum §24-§26; `notes/b15r3b-build.json`)

- **The S1 package by its pins.** `stage1_rules.S1_CODE` pins every S1 package file the kit runs or packs at main
  3eaf968 (`scripts/stage1_s1/__init__.py`, `eval_adapter.py`, `safe_lora.py`, `lean_eval_job.py`, `oext_eval.py`
  and their four settings files). The X pack carries each of them from this checkout and refuses a file whose bytes
  differ (names only); a lead's `code` entry under `scripts/stage1_s1/` must be one of the kit's pins (S1_CODE or
  D2_CODE). Round 3c pins the O-ext unit runner too (below). The kit reads no other tree. Every lead code entry
  and named input path (and a folder input's file paths) must be in normal form: no '.' or empty part, no leading
  '/', no '..', no backslash, so a respelled path cannot pass by the S1 pin rule, the S1-settings engine check or
  MAN1's comparison (round 3b fix, F1).
- **Moved records.** D-2's filled pins file is pinned at
  `.ai/inputs/stage1-post-w1-20261023/pool-pins/representation_pools.filled.json` (same SHA-256, a33e9664...);
  `record-c3` takes only the writer record `stage1_rules.C3_RECORD`
  (`.ai/inputs/stage1-post-w1-20261023/c3/c3_subsample_record.json`, 1a24c7a3...), by path and SHA-256.
- **c0 on engine X, on the LN-12 pod (§26).** c0 is block A's job (`BLOCK_KINDS["A"]`), engine X only; a c0 job on the
  cert pod refuses; the cert pod's content check no longer needs it, the LN-12 pod's does.
- **LN-15e's re-score in the plan (§17 Q19, §25 point 1; REV4 §9.3 item 3, §14.2).** Two new kinds, Gate B's retrain
  and diagnostics: `retrain` (J20: a0 at 1102 or 1103, train only to e1, recipe S, engine X, into `rescore/` with its
  own registry) and `a1_rescore` (J21: the engine's attributes step on the retrain's q and e1 states, with the packed
  anchor bank and Gate B's 8 unit groups from its sealed MANIFEST; linked by `regen_source` on the same pod). The
  Jaccard and Kendall tau against the sealed A1 set are read on the Mac, report only. Priced from Gate B's measured
  diagnostics job: measured upper 3.04 h (UNVERIFIED for attributes alone; flagged unmeasured), upper 1.5 x 3.04 h.
  The default LN-12 launch is one pod, 13.5 h (Branch full): J2/J3 pairs, the two LN-15e pairs, theta0's J3 (+ LN-14
  under 128), c0. V2a stays on its fallback (FO-04's figures as the stated limit): every plan records it in
  `not_in_plan`, and block-a-need and S1-0's init summary print it.
- **27 judge units (§25 point 2):** 20 new + the 6 reused a0/R units + theta0's (plan B: 14 + 7 = 21).
- **The top-up (§25 point 3):** the worst-case need (all five arm pods in one launch, Branch full, plan A) is
  $141.63 = 1.25 x $113.30; rounded up to the dollar, $142 (round 3b; superseded by round 3c's $144, below).

### Round 3c (`notes/b15r3c-build.json`)

- **The O-ext unit runner is pinned.** `stage1_rules.S1_CODE` also pins `scripts/stage1_s1/oext_unit.py`
  (9d038f38...) and `scripts/stage1_s1/settings/oext_unit.json` (18957b68...) at main 40e0cc6 (`S1_COMMIT`; the nine
  round-3b pins have the same bytes there). The X pack carries both and refuses a file whose bytes differ. A lead
  `code` entry under `scripts/stage1_s1/` must be a kit pin, with no exception (`S1_UNPINNED` is gone). Every O-ext
  step (J3, J4, J9, J10, J18) seals the runner, its settings, `oext_eval.py` and its settings, so `orchestrate.py
  check-plan` accepts a planned O-ext step when the X pack holds them. A test parses every O-ext command of the dry
  run under the runner's own argparse parser and under the kit's contract parser and gets the same values. The
  docstring of `job_runner_stage1.oext_unit_contract` still says "not built": the S1 package's
  `tests/test_oext_unit_contract.py` freezes that function's text byte for byte, so it stays as it is.
- **Block A completes against its plan (round 3b's VP3b-3).** A launch may leave a planned job out. Block A is now
  complete only when every job that the recorded block-A plan requires for block A has a completion record, or a
  recorded lead decision names it as not run, with a reason. The required jobs: every job of the plan's diagnostics
  and LN-12 pods (theta0's LN-14 report only under Branch 128; no O-only pass or transfer report under fallback
  (c)), every dealt arm run, and each judge launch over its planned units. A completion record: the job is recorded
  complete on a block-A host (`record-done`), or the judge launch is released over at least those units.
  `seal.py block A`, and the init of certify and B, refuse otherwise and name the open jobs.

      $PY -B plan_tool.py record-block-a-not-run FILE --sha256 H

  FILE is {kind: "stage1 block-a not-run decision", jobs: [name, ...], reason, utc, recorded_by}. A name is a job's
  kind, arm and seed, as the refusal prints it (`c0 R 1101`, `retrain a0 1103`, `o_only theta0`, `judge granite`).
  The kit refuses a name the plan does not require, a job that ran, a job that block A still holds (on a host that
  is not moved, or in a judge launch not yet released; defer or requeue that host first), a name already decided,
  and a decision before block A is planned or after its seal. Keep FILE unchanged at its path: every completion
  check hashes it again. Block A's seal lists each decided job with the decision's SHA-256 (`not_run`).
- **The top-up is $144 (the lead's decision).** VP3b-1's re-plan, two LN-12 pods (c0 alone on the second) with
  all five arm pods in one launch, needs $143.19: the one-pod arm term 11,329.50 cents + one 42-min overhead 125.30
  = 11,454.80 -> base $114.55 -> 1.25 x = $143.19. Rounded up to the dollar: **$144**. The kit's computed needs are
  unchanged (default 2+2+1 $130.59; one LN-12 pod, worst split $141.63). LIMIT, from the kit's own functions
  (`notes/b15r3c-build-evidence/`): $144 covers every re-plan with one LN-12 pod (at most $141.63) and every
  two-LN-12-pod re-plan whose LN-14 report shares a pod with an O-only pass (at most $143.68, any arm split, cert
  first or last). It does NOT cover every valid re-plan: the 8 of 1,023 two-pod layouts that put theta0's LN-14
  report on a pod with no O-only pass need $144.06 (each pod is priced at the larger of its two branch figures:
  the other pod at Branch full, this one at Branch 128 with the report's 1,408 s, so one more 42-min overhead and
  the report are counted); three LN-12 pods need up to $145.63 and eleven $158.16 (all five arm pods in one
  launch). Under the $144 record each of those re-plans refuses
  (`record-block-a-replan`), so money is never at risk (test_a_144_top_up_covers_the_two_ln12_pod_...).

### The branch re-pin round, 25 Oct (`notes/repin-build.json`, items A-H)

- **A, F: the O-ext settings are re-pinned (addendum §11 point 7).** `oext_eval.json` holds Branch 128, W1-18's
  output 608cbb94... (pod s10-1; FOCUS 87c1b0b) and build_oext's committed record a810574e... as
  `bank.phtest.record_sha256`. The chain follows in one edit: `oext_eval.py`'s literal, `oext_unit.json` and its
  literal, B10's and B17's `oext` sections (their branch too) and literals, `stage1_rules.S1_CODE` (the eight files)
  and the tests' and mutants' pins. `S1_COMMIT` is a label: the lead sets it to the commit that holds these bytes.
  Under Branch 128 every O-ext step needs `w1_18_record` packed; `check-plan` refuses without it.
- **B: a Y host's recipes are checked in engine Y's tree by engine Y's code** (`check_recipe_y`; B+Qi's recipe is
  only there). plan.json keeps Y's values in `recipes_y`; `recipes` holds one value per file, which both engines'
  code must agree on. An X host's recipes are checked as before.
- **C, G: J5 runs recipe S** (representation_pass.json pins it; pod a-1 refused REC). Its job record names S (new
  plans, deferred hosts, the re-run keys); a test compares every step's recipe with its target script's pin.
- **D: a J5 moved off J6's pod reads J6's pool by its pin.** For a-1 (J6 complete, J5 crashed, J7 and J8 not
  started): `record-done a-1`; pack engine X with the input `pool:s3_orig` (J6's pulled `s3_orig.pool.json`, by the
  SHA-256 J6's own record names; move `setup/packed-stage1-X` aside first); `defer a-1`; `check-plan` on the new host;
  launch. J5, J7 and J8 go in order to a new block-A diagnostics host bound to that pack; only J5 (crashed) is paid
  from the contingency, with the new pod's overhead; J6 is never re-run.
- **E: the user's decision turns the live-balance guard off.**

      $PY -B plan_tool.py record-guard-off FILE --sha256 H

  FILE is {kind: "stage1 user decision: budget guard off", user_words (verbatim), utc, recorded_by}; keep it
  unchanged at its path (every use hashes it again). Then `launch.py` and `host.py extend-cap` still run `budget.py
  check` (the live balance is read and logged) but go past its refusal; any other failure still refuses. The $10/h
  create limit, the in-pod stop timer at the cap and stop-never-delete are unchanged. No record: the guard as before.
  While the record holds (addendum §28, "launches in parallel while the guard is off"), `plan_tool.py release BLOCK`
  also releases the block's next hosts launch before the earlier launch's hosts are done, and records that in the
  block's `released_early` (launch, open hosts, the decision's SHA-256, UTC). The order of the launches, the block-A
  plan check, the need against the funding record and every release gate stay; a judge launch still waits until
  every earlier launch's hosts are done or moved. The need (`rules.funding_need_usd`) still assumes one launch at a
  time, so with launches in parallel the balance held at once can be above it; the user manages the balance. No
  record (or a changed file): release waits as before.

### Round 29, 26 Oct (addendum §29; the user's re-run payment; `notes/kit-round-29.json`)

- **The pull list** (`host.py` `PULL_ITEMS`) adds `rescore/` (LN-15e's retrains and re-scores) and `cert/` (C1-C3):
  every folder a stage-1 job writes a unit to. A test runs every job kind and checks that every path the runner
  writes or records lies under the list. `pull-light` still leaves out `*.safetensors`.
- **The finisher light-checks every host**, whatever its role (stage 1: w1_18, cert, certify, job, diagnostics,
  arms), not only Gate B's "job", "first" and "anchor".
- **Units the pull did not fetch** (a-2's jobs 12-15): the lead's decision, before `record-done HOST`:

      $PY -B plan_tool.py record-unpulled FILE --sha256 H

  FILE is exactly {kind: "stage1 unpulled outputs decision", host, jobs: [index, ...], reason, utc, recorded_by}.
  Each job must be complete in the pulled JOB-DONE.json with a unit and its COMPLETE.json SHA-256, and that
  COMPLETE.json must be absent from `retrieved/HOST/tree`. `record-done HOST` then records those jobs complete with
  `pulled: false` and the decision's SHA-256 ("complete (not pulled)"); the seal lists them under `not_pulled` (host,
  index, job name, unit path, the decision's SHA-256; no file hash); block A's completeness counts them as decided
  by the decision, not as done; the backup lists them and does not require their units. Keep FILE unchanged at its
  path: record-done, the completeness check and the seal hash it again.
- **Model states the light pull leaves on the pod**: `record-done` accepts a recorded `.safetensors` output that is
  absent from the pulled tree (counted as `states_on_pod`); one that is present must hash as recorded. c0's outputs
  list its 8 states, so without this `record-done a-2` refused at job 18 as well. The backup leaves them aside too.
- **The user's re-run payment** (a-7's four runs, FOCUS 26 Oct):

      $PY -B plan_tool.py record-rerun-payment FILE --sha256 H

  FILE is exactly {kind: "stage1 user decision: pay re-runs beyond the contingency", user_words (verbatim), block,
  jobs: [{arm, seed}], amount_usd, utc, recorded_by}. Each named run must be held by the block's contingency as not
  re-run and not yet paid. Then `requeue HOST` moves exactly the named runs that an earlier move of HOST held, in
  order, to the next unlaunched host of the block with room or a new host, and pays them as one unit
  (`rules.unit_rerun_cost_usd`; refused when its cost in cents is above what the decision still covers). The payment
  is recorded under `contingency.<group>.user_paid` and logged (`rerun-user-paid`). The contingency's
  `remaining_usd`, `spent` and `not_rerun` do not change, and the decision pays nothing else. A later decision
  naming a run that an earlier one did not pay supersedes it for that run (a recorded file is never edited).
  Regenerations, O-only passes, retrains, re-scores and W1-18 are never moved this way.

### Round 30, 27 Oct (addendum §30, the judge gaps 1-4; the lead's R1-R7; `notes/kit-round-30.json`)

Gate B's judge files (`scripts/gate_b_mac_judges/`) are unchanged, byte for byte (R1); every change is in this kit.

- **A judge launch is done only with its judge-completion record (gap 1).** Releasing a judge launch no longer
  completes it. After the judge files are in `judges/BLOCK/` (Gate B's `write_files.py` output and its
  `judge-files-index.json`; subfolders such as `pods/` are allowed):

      $PY -B judge_units_stage1.py result TAG          # per judge launch: the whitelist and its "record_entry"
      $PY -B plan_tool.py record-judges BLOCK FILE --sha256 H

  FILE is exactly {kind: "stage1 judge completion record", block, judges: {harmbench: {tag, result_sha256,
  run_record_sha256, bundle_sha256, exit, judged, complete}, granite: {the same, known_answer_passed}}, index_sha256,
  utc, recorded_by} (one or both judges; copy each judge's `record_entry` from `result TAG`; index_sha256 is
  `shasum -a 256 judges/BLOCK/judge-files-index.json`). No value is an HB, Granite, yes, unparsed or harm count; any
  other key refuses. At record time each judge needs a released judge launch of the block and no not-run decision,
  exit 0, complete true (Granite: its gate passed), and its own `tmp/judge-pod/TAG/judge-pod-result.json` and fetched
  run record must hash as recorded and agree (tag, judge, bundle, exit, judged, complete, a confirmed stop, every
  required unit judged). At record time and at every later use (block A's completeness, every block's, the seal,
  `seal.py status`) the record file is re-hashed, the index must hash to index_sha256, and the judge check below must
  pass. One record per block. It works on a block already sealed (block A, if sealed by the old `seal.py`: the seal
  must hold the same index) and changes no seal. A released judge launch without a record may be named by
  `record-block-a-not-run` (a failed Granite), also after block A's seal (only judge launches then).
- **The seal's judge check (gaps 2 and 5).** For a block with a judge launch, `seal.py block` needs the valid
  record naming every judge that no not-run decision names; the check (`plan_tool.judge_files_check`): every indexed
  file present at its SHA-256 and named for its judge and unit, no unindexed top-level judge-named file, and exactly
  one file per judge for each required unit, keyed by COMPLETE.json SHA-256. Required units: the COMPLETE.json
  SHA-256 plan.json records for the block's complete arm and a0_arm jobs and for each B10 unit (record-done now keeps
  JOB-DONE.json's `units` list of a B10 job), plus the block's pinned re-judged units (`stage1_rules.REJUDGED_PINS`:
  block A's 7, by path and COMPLETE.json SHA-256; block B has none). The seal lists the record's and the index's
  SHA-256 (`judge_record`); `seal.py status` prints each record (tags, exits, answers judged, hashes) and whether it
  is valid now.
- **A seal-safe judge route (gap 3).** `judge_units_stage1.py launch` builds the launcher's run log with its echo
  off (the log file is kept, sealed); `write-files` runs Gate B's `write_files` on the stage-1 enumeration and prints
  only file, unit, status and missing/stale/extra counts; `result TAG` prints the runbook's step-5 fields, pod minutes
  and cost. None prints a harm, yes or unparsed count.
- **B10 units on the judge pod (gap 4).** With a B10 unit (`stage1-eval-adapter`) in a launch, the bundle ships
  `judge_pod_stage1/bundle.py` as `tool/pod/bundle.py` and Gate B's `bundle.py`, unchanged, as
  `tool/pod/bundle_gateb.py`: the pod's `pod_job.py verify` accepts the B10 unit (Gate B's check otherwise). A launch
  without a B10 unit is Gate B's bundle, byte for byte. `write-files` writes the B10 unit's judge file.
- **Moved hosts in the seal and the backup (R6).** `seal.py block` skips a block host that a deferral or requeue moved
  and that is not done (a-5, a-6, a-7: setup failed, never pulled), as the completeness check does, and lists it under
  `moved` with its targets; an unmoved host that is not done still refuses. The backup needs no pulled tree and no
  `finished.json` for such a host and lists it under `moved`.
- **The cost in `seal.py status` (R7).** A pod's time ends at the earlier of its `finished.json` utc and its first
  confirmed stop in `hosts/HOST/stops.jsonl`, else now.

### Round 30a, 27 Oct (addendum §31, the cert pod's D2 and D4; the lead's R1-R2; `notes/kit-round-30a.json`)

- **C1's registry seed (D2).** C1 runs as `replicate_of` R_1101 (YB X-5), and engine Y's `claim_trajectory` accepts a
  `replicate_of` only when it is a live line of the registry. Before C1's make-job, the runner writes
  `cert/registry-cert_c1.jsonl` with exactly one line, the packed `cert_spec`'s `registry_line`
  (`c1_registry_seed`). It refuses before any engine step when `cert_spec` is not packed or not its pinned SHA-256,
  `registry_line.run_dir` is not `replicate_of`, the line's key is not C1's own key (built from the job, the prepared
  pin and the training identity, never from `cert_spec`), or the registry exists already. `cert_spec` is the lead's
  record {kind "stage1 cert spec", replicate_of, registry_line, source, utc, recorded_by}; the Y pack carries it as
  the input `cert_spec`.
- **The C1 comparator (D4).** `$PY -B compare_c1.py C1_UNIT R1101_UNIT --out FILE` applies
  `experiments/safety_selection/tests/removal_digest.py`'s rule to the light-pulled files of both units and writes
  only file names with equal, differ or missing and a pass boolean (exit 0 pass, 1 no pass, 2 refused). `job.json`
  is compared without `code_sha256` and the edit's path (the arm pins its bytes), after checking that C1's
  `replicate_of` is R_1101's run folder. Write FILE inside the pulled cert tree: `record-certificate` accepts only
  evidence there.

### Round 31, 27 Oct (addendum §32 points 1-3, block B's judge gaps and two cert-pod gaps; the lead's K1-K6; `notes/kit-round-31.json`)

Gate B's judge files are unchanged, byte for byte; every change is in this kit.

- **A not-run route for any block's judge launch (K1).** Block A keeps `record-block-a-not-run`. For every other block:

      $PY -B plan_tool.py record-judge-not-run FILE --sha256 H

  FILE is exactly {kind: "stage1 judge not-run decision", block, judges: [harmbench|granite, ...], reason, utc,
  recorded_by}. Each named judge needs a released judge launch in the block, no judge-completion record naming it and
  no earlier decision; block A refuses (its own route). Accepted after the block's seal too (it adds a record and
  changes no seal). The file is re-hashed at every use: keep it at its path, unchanged. `record-judges BLOCK` then
  needs only the other judges; block completeness counts the decision, `seal.py block` lists it under
  `judge_not_run` (judge and decision SHA-256; block A's judge decisions too), and `seal.py status` prints one line per
  decision (block, judges, SHA-256, valid or INVALID).
- **Block B's judged units (K2, §32 points 1-2).** A block's required units are its complete arm, a0_arm and ref_train
  runs, each unit of its ref_eval and safe_lora jobs, and `stage1_rules.REJUDGED_PINS[block]`; block B's pins are
  empty by rule (`REJUDGED_PINS = {"B": (), "A": (...)}`). A ref_train unit (recipe G or B+Qi) is the engine's
  calibrate unit `round1/<seed>-a0-e1-a<n>` (job.json kind run-one, bank dev, target e1, arm a0): Gate B's enumeration
  and its pod-side `_verify_unit` judge it as built (the launch's bundle is Gate B's). But Gate B's `write_files.py`
  keeps one file per (judge, arm, seed, target) in a folder, and block B holds up to three a0 units per seed (a0_arm at
  1105-1107, G and B+Qi at 1102-1107), so `judge_units_stage1.py write-files` labels the judge file of every unit that
  plan.json records as a complete ref_train job's unit `ref-G` or `ref-bqi` (`--plan`, default the kit's plan.json;
  without it the three a0 units refuse, exit 2). init-block of a block other than A refuses a judge launch whose
  `arms` is below the judged units its jobs will produce (one per arm, a0_arm and ref_train run, one per ref_eval and
  safe_lora point, plus the pins); block A keeps its plan's check.
- **A resumed judge launch (K3): no change needed.** A launch resumed with `--resume-from tmp/judge-pod/<old tag>` (new
  tag) seeds its pod cache from the old one, so its own result, fetched run record and cache cover every unit (tested
  on Gate B's fake pod: 18 of 18 records, 2 resumed, complete). Record the final tag with `record-judges`; the old
  tag's result is not needed (a record naming it refuses: exit 5, or its result differs).
- **No label count printed (K4).** `judge_units_stage1.py launch -- bundle` prints the bundle record without any key
  naming a label count (yes, no, unparsed, harm, identical: Granite's `known_answers.mac_yes` and the gate's rule
  constants); `bundle-record.json` on disk is unchanged. `launch -- launch` prints no record (echo off, round 30).
- **The finisher and moved hosts (K5, cert runbook D9).** A host that a deferral or requeue moved and that is not done
  (a-5, a-6, a-7) counts as finished for the watch: not watched, no deadline from its cap, and "every planned host is
  finished" no longer waits for it (the seal's `plan_tool.moved_hosts`).
- **`launch.py`'s exit code (K6, D7).** It exits 4 after the log line `hosts-not-created` when a host it was given has
  no `hosts/HOST/pod.json` at its end; 0 only when every host has one.
- **Mutation runner.** `notes/run_mutants_b15.py SOURCE_ROOT SCRATCH OUT.json BASELINE|ALL|NEW|NEAR|ID,...` (baseline
  first with the same command; killed only by a FAILED line with no ERROR line; see its module text).

### Round 32, 29 Oct (addendum §34 points 5-7; block B's pre-flight G4, G6, G8, G11, G13; the lead's K1-K6; `notes/kit-round-32.json`)

- **Block B's second reference phase (K1, G4).** The references on block B's own a0 runs (a0 at 1105-1107) are planned
  with block B, in a launch `{"second_phase": [[job, ...], ...]}` of its jobs file (ref_eval and safe_lora only; every
  reference at those seeds must be in one; after every deal launch, before every judge launch). Block B's need,
  completeness and seal count it like any launch. `release B` holds it until (`plan_tool.second_phase_gate`): each
  seed's a0 run is recorded complete (`record-done`) with its readable fingerprint record (K6); B10's settings at their
  `stage1_rules.S1_CODE` pin name that run's COMPLETE.json SHA-256 as the seed's reference unit with the record's
  fingerprint prefixes, and B11's settings at their pin accept exactly the record's e1 (the B10/B11 re-pin); the
  packed stage1-X holds `gate_a_complete:SEED` at that SHA-256 and seals B10's and B11's four files at their S1_CODE
  pins (the re-pack). The guard-off record never releases it early. B10's and B11's pins live in S1_CODE only
  (`B10_SETTINGS`, `B11_SETTINGS`, `B10_B11_FILES` name them by their keys): the lead re-takes them there at the merge
  of the re-pin round. The full-scope draft split this way (`notes/kit-round-32-evidence/jobs_block_b_full_2phase.json`)
  needs **$245.55** for the whole group (certify + B with the phase; base $196.44), the same as the unsplit figure.
- **A not-run decision for any block but A (K2, G6).** Block A keeps `record-block-a-not-run`. Every other block:

      $PY -B plan_tool.py record-not-run FILE --sha256 H

  FILE is exactly {kind: "stage1 not-run decision", block, jobs: ["HOST:INDEX", ...], reason, utc, recorded_by}. A
  name is a job that is not complete and: on a done, unmoved host (not to be re-run); left behind by a defer or requeue
  that could not pay it (not taken to a target); or every job of a pending host (a held launch that will never be
  released; a decision names all of that host's jobs). The block is complete when every launch is released or holds
  only decided hosts and every job is complete, taken along by a move, or decided (`plan_tool.block_open_jobs`; a job
  a move left behind without a decision now keeps the block open). `release` skips a launch whose hosts are all
  decided (recorded under the block's `skipped`, logged `release-skipped`), after the same wait as a release; defer
  and every move leave a decided job where it is. The seal lists the decisions under `not_run` ("HOST:INDEX") and the
  skipped launches under `skipped`; `seal.py status` prints one line per decision (valid or INVALID) and per skipped
  launch. Keep FILE unchanged at its path: every use re-hashes it.
- **A failed B10 certification (K3, G11).** B10's exit 4 at the certification pod's run (its failed gate) is a
  complete job with `certification_gate: "failed"`, its certify unit only and its comparison file among the outputs;
  exit 0 needs a passing comparison (`certification_gate: "passed"`); anything else is still a crash. `record-done`
  keeps the gate (and refuses a complete b10_certify record without it); `record-certification` refuses `pass: true`
  over a failed gate; and `init-block` (not only `release`) refuses every evaluation-only reference without a passing
  certification (LS-08), with its own message after a failed one.
- **One funding record for block B's group (K4, G8).** The group's first init (certify) takes the jobs file of each
  later part and its funding record must cover the whole group's need (addendum §20 point 1, as group A has it):

      $PY -B plan_tool.py init-block certify --jobs JC --funding F --group-jobs B=JB [--dry-run]

  Every later init of the group takes the same record (its SHA-256, re-hashed at its path) and the need of every part
  planned so far must stay within it; the summary says whether block B's jobs file is the one certify's init counted.
- **Judge units from plan.json (K5, G13).** `judge_units_stage1.py units-of-block BLOCK --out FILE [--plan P]` writes
  the block's judged units (round 31's rule: complete, pulled arm, a0_arm and ref_train units, each B10 reference unit,
  the block's re-judged pins), one folder per line, each COMPLETE.json at the SHA-256 plan.json records, and prints
  the counts by kind: the `--unit` arguments of the judge launch and `write-files`; never `--run-root`.
- **The a0 fingerprint record (K6).** After every complete a0_arm job the runner writes the readable
  `job-I/a0-adapter-fingerprint.json` (the B10/B11 re-pin tool's format: kind "stage1 a0 adapter fingerprint", version
  1, job, arm, seed, unit, complete_sha256, checkpoints {e1, q}, identity {manifest_sha256, training_identity}; e1 is
  `states/e1/state.json`'s adapter_fingerprint, the field B11 compares, and must equal COMPLETE.json's) and lists it
  among the job's outputs; if it cannot, the unit stands and the record's absence is noted (`a0_fingerprint_record`).
  The runner is a member of every pack: the certification pod's X1 pack (K3) and block B's X2 pack (K6) must be made
  after this round is merged.

### The user's start-from-the-balance rule, 29 Oct (addendum §36)

The user: "no just start it now ill fund it when i feel like this is a rule". A funding record may name the
source `user rule: start from the balance` instead of `user RunPod top-up`; its `amount_usd` is the plan's
cap-based need and it must name the user's decision record `user_decision: {path, sha256}` (kind `stage1 user
decision: start without a covering top-up`, with the user's words), re-hashed at every use. The lead tells the user
at once when the balance is below $10; the $10/h limit, the in-pod timers and stop-never-delete stay.

## The gates (brief §4)

- **G0 (before any pod, $0).** B15 built, verified and pinned at the S1 freeze. `orchestrate.py check-plan HOST` must
  pass before `launch.py HOST`: every job builds its commands and every script, settings file, edit file and named
  input it needs is in the host's packed stage. Round 3c: the O-ext steps of J3, J4, J9, J10 and J18 run the O-ext
  unit runner (`scripts/stage1_s1/oext_unit.py`, to the contract `job_runner_stage1.oext_unit_contract`), which the
  X pack carries with its settings by their S1_CODE pins. B10's and B17's own O-ext flags serve J11, J15-J17.
  Fallback (c)
  (addendum §11 point 1): `plan_tool.py record-oext-fallback` records `overrefusal_bank.status = dev100_recipe_cap`
  before any 500-bank job; then no O-ext step runs (arms run calibrate only, B10 and B17 get no O-ext flags), and an
  O-only pass or transfer report refuses. The S1 package is packed by its pins (`stage1_rules.S1_CODE`, round 3b),
  and `pack_setup.py` refuses an S1 settings file whose engine pin is not the pack's engine (addendum §11 point 7).
- **G1 (W1-18 first).** W1-18 runs alone on pod S1-0 (§8 Q1 (a)) with `--device cuda` and REC's guard batch size
  passed explicitly. Every 500-bank job refuses (plan tool, orchestrate, job runner) until `record-branch` holds W1-18's
  branch record (or a "Branch full by default" record); the branch never changes once a 500-bank job is planned.
  "Branch full by default" is accepted only if W1-18 cannot run (no S1-0 pod) or failed (its pod done, W1-18 not
  complete), never over W1-18's own branch record.
- **G2 (funding).** Each block starts on its own funding event (above); S1-0 and the certificate pod draw on block A's,
  B10's certification pod on block B's.
- **G3 (Gate B before stage 1).** Gate B is closed (measurements --final REPORTED, commit 3e82f67). G3 stays a refusal:
  every block after S1-0 needs Gate B's final record, which is only the measurements --final output pinned by
  `stage1_rules.GATEB_FINAL_SHA256` (06a7020a...), recorded once; blocks A, certify, B and C also need the plan-A/B
  record. That record is derived, never typed (round 2): `plan_tool.py record-plan-ab VERDICT --sha256 H` takes Gate
  B's committed verdict file (`stage1_rules.GATEB_VERDICT`, bec5f103...), reads `result.readings.plain.sigma_hat_pp`
  only and applies REV4 §1.3 (<= 4.5 pp plan A; <= 6.0 pp plan B; above, no stage 1); plan.json's record names the
  file by SHA-256, the field, the value and the code. Any other file, hash, field or a typed record refuses. At
  every init-block, release and deal the kit re-reads the verdict file by its pin and re-derives sigma and the code,
  so a hand-edited record (even one whose sigma and code agree) or a verdict file changed after recording refuses.
  A "no stage 1" code refuses every block.
- **G4 (the certificate before any Y unit).** One engine per pod (one packed stage per engine); a Y job refuses
  before a recorded passing X -> Y certificate (except C1-C3 on the cert pod, and B+Qi with its own a0 after a
  failed certificate); a packed engine whose identity is not its pin refuses; every job record names its engine.
  The cert block is one pod with C1 and C2 once each (C3 or its fallback record); c0 runs on engine X in block A.
- **G5 (block A before block B).** Blocks certify and B refuse until block A is complete and sealed (`seal.py block
  A`); after block A only cost ledgers, completion records (JOB-DONE.json) and adapter fingerprints are read. An
  engine unit's COMPLETE.json holds its evaluation summary, so it is sealed. A block is complete only when every
  launch is released (`plan_tool.py release` records a judge launch), every host is done or moved, and (round 30)
  every judge launch is named by the block's valid judge-completion record; a block with a judge launch is sealed
  only with its judge files, which go under `judges/BLOCK/`, one per judge for each required unit. Block A also needs every job its
  recorded plan requires to have a completion record or a recorded not-run decision (round 3c). No kit command
  prints a U, O, HB, task-loss or coherence value.
- **G6 (between pods).** PREREG's re-run rule: a completed job is never re-run; a crashed job is retried at the same
  seed from the contingency; a stopped kit pod is never restarted; no state moves between pods (an O-only pass runs
  only after its regeneration on the same pod); a refused regeneration (reuse_spec.json's accept fields differ) holds
  its O-only pass `not_started` with reason LS-04. No run or evaluation point is planned twice. Gate B called no
  extension, so no R_4 or R_5 is reused (both are trained).

## Round 2 (addendum §19-§23)

- **J5 and J8 through D-2.** J5 runs `scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py` (the main pass with the
  plant, decoy and s3_safe pools, then the s3_orig pools-only pass on J6's output, which must run earlier on the same
  pod); J8 runs `d2_score_classifier.py` with `--pool PATH:SHA256` for plant and decoy. Both get `--pool-pins` and
  `--req8-record` as PATH:SHA256 of the packed filled pins file and REQ-8's record; plan.json pins both, and every
  pool, in the job (`d2`), and the runner refuses packed files that differ. The X pack carries the D-2 package
  (`stage1_rules.D2_CODE`), the W1 MANIFEST.json and these inputs by their pins (s3_safe as the S-pool record names
  it). `plan_tool.py record-d2-fallback` ({kind "stage1 d2 fallback", jobs, reason, utc, recorded_by}, before the jobs
  are planned) makes J5 run the W1 script without plant and decoy (§19 point 4) and J8 the W1 script with no pools
  (§21). J5 and J8 run on engine X.
- **C2's binding check.** `plan_tool.py write-thresholds --out FILE --recorded-by WHO` writes the thresholds record
  with addendum §22 point 1 exactly (`stage1_rules.C2_THRESHOLDS`); `record-thresholds` refuses any other content.
  `plan_tool.py c2-label STEPS --sha256 H` reads only `step` and `constrained.mean_weight.t2_5` of each line of C2's
  steps.jsonl (steps 1-38) and prints the labels ("binds": <= 0.50 at some step s <= 3; "equals recipe B by
  construction": >= 0.90 at 20 or more steps; both if both; "partly binding" if neither). Labels never change the arm.
- **C3.** `plan_tool.py record-c3 FILE --sha256 H` ({kind "stage1 c3 subsample pin", subsample {path, sha256}, record
  {path, sha256}, utc, recorded_by}) binds J14 to the file and the record that `write_c3_subsample.py` wrote (the
  record must name that file, P, the dev source, the development role, 16 items and the verified writer). The cert
  block plans C3 or has `record-c3-fallback` ({kind "stage1 c3 fallback", status "dropped", ...}); with the fallback
  init-block cert reports "dropped" and a cert_c3 job refuses.
- **Engine Y at 34bfd288 (§23).** `pack_setup.py Y` takes `--y-tree` (default `<repo>/tmp/engine-y-34bfd288`),
  checks YHASH and then the tree's code identity against `stage1_rules.ENGINES["Y"]`; another identity refuses.
- **Tests read this repository only.** The S1 package is this tree's `scripts/stage1_s1/`; engine Y is
  `$STAGE1_ENGINE_Y_TREE`, default `<repo>/tmp/engine-y-34bfd288`.

## The environment reference (§8 Q11)

Every stage-1 pod compares its bootstrap and preflight with Gate B's environment reference (`plan_tool.py
import-reference`); a pod that runs an evaluation-only reference (ref_eval, safe_lora) compares with the B10
certification pod's environment instead. A difference stops the pod through the pre-job failure path.

## Kept from the Gate B kit

### Operator rule ([D16] 8)

A stopped kit pod is never restarted. A requeued host's jobs run only on its replacement.

`plan_tool.py requeue HOST` moves the stopped host's jobs to another host in plan.json (for wave 0a's first host it
also moves the recorded expected fixture aside and clears the reference), so the stopped pod no longer owns them.
A host whose jobs were moved can no longer record the expected fixture or set the reference (`orchestrate.py`
record_first and `plan_tool.py set-reference` refuse it).

### A requeue never follows a failed or unknown stop ([D17] 3)

`orchestrate.py` logs `pre-job-failed` (with its step) only when the pod says the job did not start; when the pod
cannot say (an ssh exit other than 0 or 1), it logs `job-start-unknown`. Either way it stops the pod and logs
`pre-job-stop` with the stop's exit (1 when host.py could not confirm EXITED).

`requeue HOST` accepts the log alone only when the last `pre-job-failed` names a step other than `start-job` and a
later `pre-job-stop` has exit 0. Otherwise (a failure at `start-job`, a failed stop, an unknown job start) the
operator first checks the pod's status with `host.py get HOST` and, once it shows EXITED, runs
`plan_tool.py confirm-stopped HOST`, which records it in operator-actions.jsonl, bound to the current
orchestrate.jsonl; then `requeue HOST` runs.

### The guard record is part of the environment ([D17] 4)

`plan_tool.py record-done` of the host that completed R_1101 copies that unit's pulled guard record into plan.json's
reference. Before it does ([D19] 4), it compares that guard with the same host's own preflight guard (the pulled
`retrieved/HOST/tree/PREFLIGHT-DONE.json`) and refuses, with plan.json unchanged, on any difference (the message names
the host and the differing guard fields) or when that preflight guard is missing; wave 0b cannot be planned until the
lead resolves it. The preflight check compares each later pod's guard record (PREFLIGHT-DONE.json) with it, and
`requeue --rerun-mismatched` accepts an arm unit whose guard record differs (reported as `guard`, as the reading
reports it). `--rerun-mismatched` refuses a hash named twice, and refuses once a later wave (or ext, lc) is planned.

### At most 4 arms per pod ([D21])

`gateb_rules.MAX_ARMS_PER_POD` (default 4; the user confirms the value at the freeze, DRAFT revision 5 §12) caps
every pod. `plan_tool.py init-wave` splits waves 1, 2, ext and lc into ceil(n / MAX_ARMS_PER_POD) pods, the arms dealt
as evenly as possible in the given order (`gateb_rules.pod_sizes`: 8 -> 4 + 4, 6 -> 3 + 3, 4 -> 4; this even split
is the pre-registered one, [D21] (4): the DRAFT follows the kit); each pod's cap
comes from its own jobs (B4). The pods of one wave are launched together (`launch.py HOST HOST ...`); the budget guard
counts each running pod at its full cap, so a pod starts only when the guard allows. The wave-1 funding need counts
every later launch of the worst path split the same way: at $1.79/h spend and $1.85/h at the guard, with Mac Granite,
it is $72.85 (1.25 x $58.28; [D22]: the factor is 1.25, was 1.15, which gave $67.02). `defer` and `requeue` move jobs to an unlaunched host of the same wave only when it has room; else
to a new host. A pre-job requeue from wave 1 on is paid from the contingency as one unit (one 42 min plus each job's
spend upper; $7.46 for a 4-arm pod of the $15.69 contingency at the default, so it pays two such stops in full on the pod-Granite route; on the Mac route the $14.57 contingency pays one 4-arm stop and 3 arms of a second).

When the contingency is short ([D21] (3)): a unit costs exactly what its jobs cost one by one
(`unit_rerun_cost_usd` is the sum of `pay_reruns`' costs, the 42 min on the first), so the two agree whenever the
unit fits; when it does not fit, the one-by-one rule governs: each moved job in order is paid if its cost fits what
is left (the 42 min on the first job paid), and the rest are reported not re-run.
