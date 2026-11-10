# R2 K2 adversarial verification: the 7-8B kit's planning layer for blocks A and B

Started 2026-11-08 23:31 UTC; this text written 23:56 UTC to 9 Nov 00:05 UTC (`date -u`). Target: B/ws-k2,
detached at `bfda225` (M: `git log -1`), diffed by me against `bfda225` (`git -C B/ws-k2 diff bfda225 -- runkit`,
3,315 lines, plus the two new test files and the fixture; the builder's `k2.diff`, 4,775 lines, includes the new
files). I edited nothing in ws-k2, MAIN or any other worktree. My files: this report and R/r2-k2-verify-scratch/
(probe tests, a block-0 probe, extracted base trees from `git archive`, a scratch repo copy, a mutant spec). No pod,
spend, network, install, download, agent or message. No forbidden folder, sealed edit, answer, generation, judge
output or prompt file opened; the SR-2 simulation's merged outputs (simulated rates) were read by key. Tags: M
measured (the command or the probe file), R read (path:line, WS unless named), E estimate, I inference.

## Verdict

**DEFECTS.** Block 0 is unchanged in behaviour (M, check 1), the success path of block A's record-done is blind
(M), the record steps derive their values from pinned sources, and the anchor-stopped part works with the real
`blinded_sigma.py` (M, my probe). But four gaps break the brief's own acceptance items: block B's init takes a
hand-written SR-2 status (K2V-1); after any deferral or requeue in block A the kit can never write blinded_sigma's
inputs (K2V-2); the inputs file and its parts are taken from anywhere, never checked as kit-written (K2V-3, S-9);
and the orchestrator still holds every scorer-block O-ext pod on the deleted 1B branch record, so BRANCH_78B is not
the only branch source (K2V-4, K-8/R-26; owner K3). The stopped-family part and 13 other new checks are untested
(16 of my 20 extra mutants survive; K2V-5, K2V-6), the dose record is refused at exactly 96 kept rows (K2V-7), the
blinding record pins only one of SR-2's two halves (K2V-8, the lead rules its form), and three minor items follow
(K2V-9 to K2V-11). Of the builder's six decisions, 4 and 6 are sound, 3 is a defect (K2V-3), and 1, 2 and 5 need
the lead (check 6).

## Defects

| Id | Severity | File:line (WS) | Defect | Failure scenario | Fix |
|---|---|---|---|---|---|
| K2V-1 | Major | runkit/stage1-78b/plan_tool.py:4101-4106 (init_block_ab, block B), :3842-3859 (plan_b_blinded_check), :4218-4233 (release_hosts_ab) | Block B's init re-reads the noise reading and blinded_sigma's output (R-30) but never re-derives SR-2's status (`sr2_adopted`, `sr2_reason`) from SR2_BLINDING_RECORD and the governing SR2_SIMULATION pin. RK's form check only ties the plan to the basis the record claims. | M (probe P3a): the kit's own record-plan-b-78b writes "not adopted, blinding_test_not_verified, plan A"; a hand-written PLAN_B_78B with `sr2_adopted: true`, basis sigma_A, sigma 5.0 and a synthetic blinded output plans block B under B9 (32 runs). P3b: with both triggers passing (kit record: adopted, B9), a hand record "not adopted, simulation_reading, plan A" plans 23 runs. Either way the plan's basis is chosen by hand (R-24's money edge: up to 47 vs 23 runs per family, about $198, E from GXB R-24). | In init-block B (and at release) call `sr2_blinding_reading()` and `sr2_simulation_reading(option, families)` and refuse unless the record's `sr2_adopted` equals `verified and not above_threshold` and `sr2_reason` equals the derived reason; a test for both directions and a mutant. |
| K2V-2 | Major | plan_tool.py:4575-4585 (block_a_arms_done), :4530-4534 (blinded_inputs_part) | Both read every job of every block-A host and require it complete and pulled; a host whose jobs moved (defer, requeue) keeps its deferred/crashed/not-started jobs, and the moved jobs' completions on the new host are never matched to their cells. block_complete skips moved hosts (moved_hosts); these two do not. | M (probe P9, P9b): one block-A job deferred on olmo2-7b-a-1, deferred to olmo2-7b-a-7, re-run complete and recorded: record-done prints no part; `write-blinded-part` refuses ("once every block-A arm job is complete and pulled"); `blinded_inputs_part` refuses on olmo2-7b-a-1. A routine cap deferral (s_obs above 1.15) or a crash requeue in block A thus makes SR-2's input impossible without a hand-made file (S-9 forbids it), so SR-2 is lost. | Skip moved jobs (deferrals'/requeues' `from_indices`, as block_complete does) and take each (arm, seed) cell from the job that completed it; refuse two complete units for one cell; tests with a defer and a requeue (and a mutant). |
| K2V-3 | Medium | plan_tool.py:4604-4634 (write_blinded_inputs), :4369-4381 (record_plan_b_78b), :3842-3859 | S-9 (inputs written by the kit's record-done step "never by hand") is not enforced: write-blinded-inputs merges any part file of the right kind, gate SHA-256 and family, from any path given with its SHA-256; record-plan-b-78b accepts any inputs file whose kind, version, option and family names fit; init-block B never looks at the inputs file. The builder's own test helper uses such a non-kit file (R: tests/test_planning_ab_78b.py:474-480). | M (P4a): an inputs file `{"families": {"olmo2-7b": {"hand": "made"}, ...}}` and a matching synthetic output give PLAN_B "adopted, plan A". M (P4b): a hand-made part from records/ with one invented cell is merged. A swapped unit (e.g. a re-run's other unit of the same cell, which read_unit would also accept) changes sigma_A and the plan. | write-blinded-inputs reads each family's part only at its block-A copy's standard path (tmp/<prefix><F>-A/blinded/blinded-sigma-inputs-part__<F>.json) and re-derives it from that copy's plan.json (blinded_inputs_part on the sibling plan; byte compare); record-plan-b-78b and init-block B rebuild the merged bytes in memory and compare them with the inputs file. Tests and mutants. |
| K2V-4 | Major (owner K3; K2's acceptance item R-26/K-8 not met) | runkit/stage1-78b/orchestrate.py:403-405 (w1_18_hold), called at :413 and in _after_create :430-435 | K2 deleted the only writer of plan.json's 1B `records.branch` (record-branch); the orchestrator's hold still reads it for every BANK500 kind. | M (probe P8): scorer block, BRANCH_78B pinned (a real record), o_only planned and released by plan_tool: `orchestrate.w1_18_hold` refuses "a 500-bank job waits for W1-18's branch record (G1)". Every o_only, o_only_with_regenerate and c0 pod (and later every block-B reference) is refused after the pod is created (_after_create), costing pod minutes per attempt (I). | K3 (orchestrate.py is not K2's file): the hold reads BRANCH_78B by its bytes through rules_78b.bank500_problem (as plan_tool.bank500_or_fail does); a test that an O-ext pod with the branch pinned passes and one without is held; K3 acceptance item. The builder listed it (R: R/r2-k2.md §7). |
| K2V-5 | Medium (test gap) | plan_tool.py:4558-4562 (part design and stop record), :4626 (stop path rebase) | The anchor-stopped part (S-6: design `anchor_stopped`, the stop record by path and SHA-256, its rebase) has no test and no mutant (grep: no "anchor_stopped" in the kit's tests). | M (vmut-1.json): V-part-design-always-full, V-part-stop-record-dropped and V-merge-stop-path-not-rebased all SURVIVE the scorer runner. The code works today (M, probe P6: df 6, sigma_A equal to Track S's numpy fit, per-role engines split) but nothing holds it. | Add P6's end-to-end test (scratch/test_k2v_probe.py::test_p6_...) or the like, and the three mutants. |
| K2V-6 | Medium (test gaps) | plan_tool.py:3853-3854, :4376-4377, :4619, :4631, :4228-4229, :4235-4236, :4290, :3819, :4032, :4525-4534, :4584-4585; states_tool.py:149 | Many of K2's own refusals have no test that fails when they are removed: block B's inputs-hash comparison; record-plan-b-78b's families check; the merge's gate check and family-set check; release's PLAN_B_78B re-check; release's anchor JOB-DONE.json re-check; the [C] sigma_F plan's family (the synthetic noise output gives both families the same sigma_F plan, so reading Llama's under [C] passes, at record-gate and at init); the sibling seal's SHA-256 check; the part's "pulled" and one-engine checks; the state rule's a0 seeds 1105-1107. | M (vmut-1/2/3.json): 16 of my 20 extra mutants SURVIVE, 1 more is equivalent (V-planb-plan-vs-sigma-unchecked: RK's block_init checks the same before it), 3 are killed (V-c0-fingerprint-unchecked, V-branch-units-count-free, V-seal-copies-only-block0); 0 invalid. Survivors: §7. Some are caught downstream by blinded_sigma.py itself (unpulled units, two engines, a missing family); the others are not: e.g. under [C] block B could be planned from Llama-3.1-8B's sigma_F, a changed PLAN_B_78B pin after init-block B would release, and block B's a0 1105-1107 states could be listed for deletion before their references, with no test failing. | A test per check (for [C], a noise output whose two families' sigma_F plans differ; a block-B keep-list with a0 1105-1107) and the 16 mutants in the scorer spec. |
| K2V-7 | Minor | plan_tool.py:3948-3951 (s4_kept) | The top-dose map gives "s4_96" for exactly 96 kept rows, but the scorer layer's nested_doses writes `top_dose: "s4_top"` at 96 (and at 48-191). | M: `scripts.scale78b.scorers_78b.nested_doses` with the family's settings, n = 96: lists s4, s4_96, s4_top, top "s4_top"; s4_kept would refuse the real dose record ("top dose 's4_top' is not the one its kept count gives (s4_96)"), so block B's dose rows refuse at the K-5 boundary "exactly 96". The builder's tests use 200 and 150 only; K-5 asks a test per case. | Expect "s4_192" iff kept >= 192, else "s4_top" (the scorer's rule); tests at 48, 49, 95, 96, 97, 191, 192. |
| K2V-8 | Medium (needs the lead for the form) | plan_tool.py:3701-3709, :4334-4346 (sr2_blinding_reading) | SR-2's blinding trigger has two halves (P2 §10.1: record-done prints no value; blinded_sigma's byte test), verified "before block A's first pod". The record pins only blinded_sigma.py's SHA-256; the kit's record-done code (plan_tool.py, which K3 and K4 will still change) is not pinned, and the record's time is not checked against block A's first release. | I: a record-done change after the verification (or a verification after block A started) still reads "verified", so SR-2 is adopted on an unverified kit. | The record also names plan_tool.py's SHA-256 (record-done's code), checked against the block-A copies' plan_tool.py; init-block A writes the pinned blinding record's {path, sha256, verified} into the block's plan record (before its first pod), and record-plan-b-78b takes SR-2's blinding trigger only from that snapshot in every A copy. The form is K2's open point 3: the lead rules it. |
| K2V-9 | Minor | plan_tool.py:3796-3808 (noise_plans), :3789-3793 | The noise output's plan fields are taken as given; their own sigma is not checked. | M (P5): a noise output whose seed_rule says plan A with sigma_pp 9.0 (H by the rule) passes record-gate-78b as provisional plan A. Needs a hand edit of a pinned script's output, so Minor. | Recompute with `r78.plan_for_sigma(seed_rule["sigma_pp"])` (R-29 holds it equal to noise_reading's rule) and require `seed_rule == pooled["seed_rule"]`; the same for each family's sigma_F plan. |
| K2V-10 | Minor | plan_tool.py:5962-5971 (main), :12-17 (module doc) | The 1B block-A commands stay on the CLI of a 7-8B copy: block-a-need and write-block-a-plan crash with AttributeError; record-block-a-plan, -replan and -not-run refuse with 1B-form messages. The new module text says "every other 1B record command refuses in this copy". | M (P7): `block-a-need` and `write-block-a-plan` in a 7-8B block-A copy raise `AttributeError: module 'stage1_rules' has no attribute 'PLAN_ARMS'`; M (P7b): the three record commands refuse ("a block-A plan holds exactly [...]", "no block-A plan is recorded"). No write, but an unclean refusal and dead 1B route code (K-2 residue: plan_ab_checked and the block-A plan functions remain, :594, :1853, :2126-2581). | Refuse them by name in main, as the `simple` 1B records are. |
| K2V-11 | Minor | plan_tool.py:5265-5266 (record_done) | record-done copies JOB-DONE.json's per-job `reason` text into plan.json verbatim. | M (P1b): a planted value in a crashed job's `reason` reaches plan.json (not the printout). Today the runner writes only fixed reason codes there (R: setup/job_runner_stage1.py:1054-1065; its crash text goes to `why`, which record-done drops), so no value reaches it now (I). | Keep only a known reason code (or its hash) in plan.json. |

## Check 1: block 0 unchanged (M)

- Probe `R/r2-k2-verify-scratch/block0_probe.py`, run sandboxed on three kit trees: ws-k2, and `bfda225` and `3481d85`
  extracted by `git -C MAIN archive <c> runkit/stage1-78b scripts/scale78b | tar -x` (read-only). Each tree's own
  test World (test_stage1_runkit.World), clock fixed, every new pin null (M: the probe prints GATE_78B, PLAN_B_78B,
  W1_18_78B, BRANCH_78B, ANCHOR_STOP, N_UNITS, SR2_BLINDING_RECORD, S4_DOSES_RECORD, PADDED_TOKENS_78B,
  SR2_SIMULATION_REDUCED: all null in ws-k2).
- plan.json identical byte for byte in all three trees for both families (M: `cmp`; olmo2-7b 14,114 B `f72de041…`,
  llama31-8b 14,613 B `f5ac8a95…`, tmp path normalised). The dry-run printout and return, the real init's printout
  (need lines, caps, guards, the funding need $56.06, the retrain and scorer pod needs) and return, the operator log,
  `deal 0`, and a second `release 0` ("no launch left to release") are equal across the three trees (M:
  b0-*/summary.json compared field by field). The released host is in plan.json (launch path: launch.py and host.py
  read only plan.json's hosts and are unchanged, R: `git diff --stat`). test_42 (unchanged) holds the 3481d85 bytes
  (M: lead's suite 585 passed).
- Not block-0 neutral, by design: block 0's seal record gains `copies: []`, `named_exceptions` and a `counts.exception`
  key, and on Llama-3.1-8B the a0-1103 `eval/e1/query_loss.jsonl` is classed "exception" (R: seal.py:96-139, :183-205).
  GXB O7 needs it; it is after the pod and not tested byte for byte.

## Check 2: SR-2's blinding half (M unless marked)

- Success path: the builder's planted-sentinel test is real: sentinels in COMPLETE.json, summary.json,
  query_loss.jsonl, answers and a judge file; stdout, stderr, plan.json, the operator log and the part scanned; the
  whole printout of every host held byte for byte with the part's SHA-256 computed by hand (R:
  tests/test_planning_ab_78b.py:989-1020).
- My probes (R/r2-k2-verify-scratch/test_k2v_probe.py, run in a scratch repo copy, sandboxed; 10 passed, 2 P7 cases
  failed; P1, P1c, P3c and P6 pass because the kit is right, P1b, P3a, P3b, P4a, P4b and P5 pass because the kit takes
  the bad value, which is the defect they show; P7 fails because the command crashes): P1 crash path (a crashed job with planted values in `why`, `refusal` and the
  host's refusal text): no value in stdout, stderr, plan.json or the operator log, no part written. P1c refusal paths
  (COMPLETE.json changed after the pull; a planted host name): the refusal texts carry no value. P1b: see K2V-11.
- The inputs it writes match blinded_sigma.py's reader: engines per role {a0, R, block_a} (R-13), method cells
  {path, complete_sha256}, R cells with `edit-<SHA-256>`, N's units at N_UNITS' paths and the side units at KIT
  a0_units' paths (R: scripts/scale78b/blinded_sigma.py:216-268, scripts/scale78b/noise_reading.py:154-160). The
  builder's end-to-end test reads the kit's merged file with the real `blinded_sigma.read` (df 12, sigma equal to an
  independent numpy fit); it uses one engine for all roles, but the byte-for-byte test pins the role mapping and
  K2-m-part-engines-swapped is killed. My P6 adds what is missing: OLMo-2-7B anchor-stopped, engines split per role,
  through record-done, write-blinded-inputs and the real reader: df 6, sigma equal to numpy (rel 1e-12). So the S-6
  path works, but is untested in the suite (K2V-5).
- Gaps: K2V-2 (no part after a deferral), K2V-3 (provenance), K2V-8 (the blinding record's scope and time).

## Check 3: the record steps

- Values from pinned sources: record-gate-78b takes the plans from the noise output only (option and balance are the
  lead's; the balance is refused if not finite); record-plan-b-78b takes the status from the blinding record and the
  governing simulation, the plan and sigma_A from the blinded output (R: plan_tool.py:4276-4393). record-branch-78b
  takes the branch from the committed W1-18 record at its R-21 place, made under W1_18_78B's settings pin, the
  family's unit count, never switched once pinned (:4396-4449). record-anchor-stop takes the stop from the anchor
  host's JOB-DONE.json and the frozen script's two signals only (:4455-4507; tests for the six cases).
- Block B's init re-reads the noise output (gate_noise_check) and, when adopted, the blinded output, and refuses a
  recorded plan, sigma_F plan, sigma_A or inputs hash that differs (R-30; tests and mutants). Not re-derived: SR-2's
  status (K2V-1), the inputs file (K2V-3), the noise plan against its sigma (K2V-9).
- SR-2's simulation (M, from MAIN/.ai/inputs/stage1-post-w1-20261023/78b/sr2-simulation-20261108/, read by key): the
  pins equal the committed files (`sr2-B-full.json` `671f64a7…`, `sr2-C-full.json` `21738afc…`; equal at `bfda225`
  by `git show`), and the outputs' script and settings hashes equal the committed `sr2_simulation.py` `0ff5e545…` and
  `settings/sr2_simulation.json` `c6f0c81e…`. My recomputation over every row, scenario and family: [B] 90 cells,
  largest familywise count 1,029 of 20,000 = 0.05145 (sigma_pair 5.5 pp, Llama's sigma at 2/3, OLMo-2-7B); [C] 45
  cells, 1,035 of 20,000 = 0.05175 (4.0 pp, arm x seed 0.5); both equal the summaries and the lead's README; neither
  above 6% (exact fractions). Design "full", stopped []. Refused contrasts 0 (the README's non-converged fits are part
  of the procedure, R: its README).
- Wrong plans refuse (M, P3c: a sigma_A record with plan A at 5.0 pp refuses "GXB R-24"); wrong status is accepted
  (K2V-1).

## Check 4: the lean route

- init-block A and B in init_block0's form (R: plan_tool.py:4081-4215); the 1B init and release bodies, gate_order,
  gate_g1, check_launch_gates, record_branch, branch_name and the RECORD_KINDS branch entries are deleted (R: the
  diff); the 1B checks keyed to "A" name the sentinel LEGACY_A, so the 7-8B block A takes every block's not-run, judge
  and completeness rules. BRANCH_78B is read by its bytes at its pin in the planner (branch_bytes, bank500_or_fail)
  at init and release, but not in the orchestrator (K2V-4). Residue: K2V-10.
- "review": block A refuses under a review provisional plan (RK block_init, R-1); block B plans nothing under review,
  sigma_A's ceiling included (tests). Per-family copies: init and deal refuse another block's copy; siblings are read
  by KD7's names (sibling_plan).
- Track O's real printed forms (M: `make_oext_settings_78b.py --oext-78b F` and `--w1-18-78b`, print only): OEXT_78B
  passes RK's form check for both families and holds every file oext_command_problem needs; W1_18_78B refuses only on
  theta0's null job_sha256 and passes once KIT's value is put in (decision 6 below).

## Check 5: the rest

- Re-judge lists: 7 per family (M: rejudged_pins: OLMo-2-7B N R 1101-1103, side a0 1101-1103, theta0; Llama-3.1-8B
  N R 1101-1103 and N a0 1103, side a0 1101-1102, theta0), read live (rejudged_or_refuse refuses while N_UNITS is
  null), repository-relative paths (X5). Judge pricing: E, as Part 2 §6 (28 units: HarmBench 2.31 h, Granite 1.56 h).
- Block A's seal names block 0's and the scorer block's seal records by path and SHA-256 and carries their named
  exceptions (R: seal.py:104, :187-205; test). The state rule: keep-list and check-deletion-list (R: states_tool.py);
  it checks the backup manifest's hash and tag, not that the backup holds these pods' states (I; minor, not listed).
- C0_SOURCE at release: c0_release_check reads the packed source unit from the bundle and compares its fingerprint
  with C0_SOURCE now (R: plan_tool.py:4637-4665; test turned around for K6v-4). Command words (K-1, KR6): read from
  RK's OEXT_WRAPPER_COMMANDS with each word's files in the pin; the mutant re-targeted and killed.
- K-4 idle lines: N's seven o_only_with_regenerate pods plan by (arm, seed) with idle lines; block 0's printout
  unchanged (M, check 1). Kept S4 count from the dose record: yes, but K2V-7.
- R-16: plan_tool's call site uses sc_unit_input_pins(kind, pins78, values, arm, seed) (R: plan_tool.py:1271); the
  seed-only sites left are K3's (pack_setup.py:432, setup/job_runner_stage1.py:466, :483; test_41's list). R-32, R-33:
  as check 4; plan_for_sigma refuses 10**400 (test). K6v-1 and K6v-6 tests present and their mutants killed (builder;
  lead's scorer run pending at this writing). R-37: Safe LoRA points default and certify only, conditional and k12
  refused by name in job_record (R: stage1_rules.py:447-448, :639-649).

## Check 6: the builder's six decisions

1. **New pins in plan_tool** (SR2_BLINDING_RECORD, S4_DOSES_RECORD, PADDED_TOKENS_78B, SR2_SIMULATION,
   SR2_SIMULATION_REDUCED): sound under the brief's file rule (RK only for (RK) items); move to RK later. The
   SR2_SIMULATION fill (values M-equal to the committed files) is a fill, which by A13's pattern is the lead's recorded
   step: **needs the lead** to record it.
2. **train_scale's per-edit record** (PADDED_TOKENS_78B keyed by edit SHA-256; a0 from RK's KCR constant): sound as a
   refusing placeholder (blocks A and B refuse while null); the record's form and the token-count step have no ruled
   source: **needs the lead**.
3. **Merged parts under [B]**: the mechanism is sound (one part per family copy, KD7, merged by a kit step), but the
   merge takes parts from anywhere: **defect K2V-3**.
4. **Judge launches priced by the 1B port**: sound as an E (matches Part 2 §6's E; Granite's 7-8B time unmeasured);
   the judge terms never set the need here (the first launch's term is the largest, M: probe printout $219.68 =
   1.25 x $175.74).
5. **Branch full from a failing W1-18 record**: consistent with the frozen reader (`oext_eval.read_w1_18`: Branch
   full needs a failing record, or no record and a reason; R: scripts/stage1_s1/oext_eval.py:359-385), and R-33's
   agreement check then needs the O-ext pin to name the failing record. But Part 2 §4.2 has the kit pass
   `--w1-18-record` under Branch 128 only, and RK's flags pass none under full, so the pod's oext_eval would refuse
   (I). **Needs the lead** (pass the record under any W1-18-sourced branch, or pin no record with a full_reason).
6. **W1_18_78B refused until theta0's pins**: sound (R-20, T-O2); M as in check 4.

## Check 7: tests and mutants

- Suites (lead's background job, B/lead/k2-checks/summary.txt): 7-8B 585 passed (sandboxed), stage-1 762, scale78b
  529 + 57 skipped; rules spec 248 killed, runner spec 35 killed (M, the lead's runs); scorer and gated specs still
  running when last read (see the end of this report).
- My extra mutants (scratch spec R/r2-k2-verify-scratch/vspec.json, made by make_vspec.py, which checks each find
  text occurs exactly once; run with the builder's run_mutants_scorer_78b.py from a scratch source root that differed
  from ws-k2 only in the spec; sandboxed; every shard's baseline exit 0; shards 3-6 min each, run beside the lead's
  scorer job). M (vmut-1.json, vmut-2.json, vmut-3.json): 20 mutants, 3 killed, 1 equivalent, 16 survived, 0 invalid.
  - Survived: V-part-design-always-full, V-part-stop-record-dropped, V-merge-stop-path-not-rebased (K2V-5);
    V-planb-inputs-sha-unchecked, V-planb-inputs-families-unchecked, V-merge-gate-unchecked,
    V-merge-family-set-unchecked, V-release-planb-unchecked, V-release-stop-donefile-unchecked,
    V-gate-record-sigma-f-llama, V-gate-check-sigma-f-llama, V-sibling-seal-hash-unchecked, V-arms-done-unpulled-ok,
    V-part-unpulled-ok, V-part-two-engines-ok, V-states-kept-1104-only (K2V-6).
  - Equivalent: V-planb-plan-vs-sigma-unchecked (RK's plan_b_record_problem ties the plan to the record's sigma, and
    plan_b_blinded_check ties that sigma to the output's, before this line).
  - Killed: V-c0-fingerprint-unchecked, V-branch-units-count-free, V-seal-copies-only-block0.
  So "new mutants for every new rule" (the brief's acceptance) holds for most rules but not these 16.
- Weakened tests: none found that the ruled changes did not force. test_stage1_judge_route.py now asserts
  judge_units_stage1.py differs from the copy manifest (`!=`), and ADAPTED_BY_R2_K2 exempts it and seal.py from the
  byte check, the same treatment as K1's and K3's adapted files; one scorer case moved because N's R-1101 is a unit
  now (DES E5). The scorer runner reaches the planning tests through a sys.argv-guarded import in
  test_scorer_block_78b.py (R: :2316-2328): it works (the K2 mutants are killed) but is fragile; a runner that names
  both files would silently drop the planning tests from the mutation run (I).

## Acceptance items (the brief's), as I find them

- Block 0 unchanged (plan.json, printout, caps, need, pins, launch path): **passed** (M, check 1).
- 7-8B suite sandboxed 585, stage-1 762, scale78b 529 + 57 skipped: **passed** (M: the lead's background run).
- Rules 248 and runner 35 killed: **passed** (M: the lead). Scorer 233 and gated 128: **the lead's run had not
  finished** when I last read summary.txt (00:05 UTC; the scorer job's scratch was at pt-128 of 233); not tested by me.
- "New mutants for every new rule": **failed** for 16 rules (K2V-5, K2V-6).
- SR-2's blinding half: **passed** on the success, crash, refusal and partial paths (M); **failed** after a deferral
  (K2V-2); the trigger record's scope open (K2V-8).
- R-30 (values from sources; block B refuses a differing value): **passed** for the plans, sigma_A and the inputs hash;
  **failed** for SR-2's status (K2V-1) and the inputs file (K2V-3).
- K-8/R-26 (BRANCH_78B the only branch source): **passed** in the planner, **failed** in the orchestrator (K2V-4, K3).
- K-5 (a test per dose case): **failed** at 96 (K2V-7).

## Commands run (exit 0 unless noted)

`date -u` (several); reads (cat, sed, grep, git log/status/diff/show, shasum, ls, du); `git -C MAIN archive
bfda225|3481d85 runkit/stage1-78b scripts/scale78b | tar -x -C scratch` (read-only extraction); block0_probe.py on the
three trees (sandboxed; 3 runs); the maker's three print commands (`make_oext_settings_78b.py --oext-78b F`,
`--w1-18-78b`; sandboxed, print only); small python reads of RK, the scorer layer's nested_doses and the simulation
records (-B -I; no __pycache__ left, M: find); my probe tests in a scratch repo copy of ws-k2 (the kit copied, every
other entry linked; sandboxed): test_k2v_probe.py 10 passed and 2 failed (the two P7 cases, K2V-10, as expected),
test_k2v_probe_orch.py 1 passed (P8), test_k2v_probe_defer.py P9 failed (K2V-2) and P9b passed, test_k2v_probe_1b.py
3 passed, test_k2v_probe_fs.py 1 passed (P10: record-done changes exactly plan.json, the operator log and the part;
none holds a planted value); the scorer mutation runner on my spec, 3 shards, each exit 0. The scratch repo copies,
pytest temp folders, runner copies and extracted trees were deleted afterwards (kept: the probe files, the spec, the
three result files, the block-0 summaries and the maker printouts). ws-k2's `git status` is as the builder left it
(M).

To re-run a probe: copy ws-k2's runkit/stage1-78b into a new folder REPO/runkit/stage1-78b, link ws-k2's other
top-level entries and runkit folders into REPO, copy the probe file into REPO/runkit/stage1-78b/tests/, and run
`cd REPO && sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q <the file>`.
