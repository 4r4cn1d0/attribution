# R1 K1 fix round: adversarial re-verification (the 7-8B kit's rules layer for blocks A and B)

Written 2026-11-08; clock read with `date -u` at 17:21 UTC (start) and 17:48 UTC (this text). Status: **done**.
Target: B/ws-k, a detached worktree at `3481d85`, with K1's working-tree changes (M: `git log --oneline -1`;
`git status --short`: the same 12 modified files and the one new test file before and after my run). Every K1 file
hashes to the builder's fix-round table (M: `shasum -a 256`, 13 files, at 17:21 and 17:47 UTC). The pre-fix copies
(`r1-k1-scratch/prefix/`) hash to the builder's round-1 table, which the first verifier checked (M). I wrote only
this report and `R/r1-k1-reverify-scratch/`. MAIN was read only. No pod, spend, network, install, download, agent or
message. I opened no sealed edit file, answer, generation, judge or prompt file, and I did not hash the R_d files again
(check 3 compares the pins with the first-verified pre-fix values). Tags: M measured (command), R read (path:line, WS
paths unless named), E estimate, I inference.

## Verdict: VERIFIED_WITH_MINOR

- Every defect and ruling in scope is closed as asked (check 1). This covers K1V-1, K1V-2, K1V-3, R-1, K1V-5,
  K1V-6, K1V-7, K1V-8, K1V-11, K1V-12, R-3 (block 0's plan.json, byte for byte, re-measured), R-5 and the K-1
  re-targets.
- Block 0 behaves as it did at `3481d85` (check 2). The 7-8B suite passes: 538 (M). The rules spec: 225 killed,
  0 survived, 0 invalid (M).
- New findings: five minor items and three nits. KR1 is a rule gap. Under [B] without SR-2, block B's plan is not
  checked against N's plan. The other seven are test gaps, wiring items and fixture items.
- None of them touches block 0, which is the next launch.
- I would merge, and fix KR1-KR3 in a small round or as K2 acceptance items.

## Defects

| id | sev | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| KR1 | minor | rules_78b.py:2071-2092 (`block_init_or_refuse`), :2001-2036 | Under [B] with SR-2 not adopted, P1 §6.4 says "N's value decides alone", and K-6 says the plan comes "from N's value under [B]". So block B's plan must equal the gate's provisional plan (N's). The kit checks only that `plan_basis` is `sigma_pool_N`. It never compares `plan` with `GATE_78B`'s `provisional_plan`, although `block_init_or_refuse` holds both records. M (`tools/plan_b_vs_gate.py`): gate [B] with provisional plan A; PLAN_B not adopted, basis `sigma_pool_N`. The kit accepts plan A, B9 and H. | A mistyped plan in the recorded lead step. Block B then runs H (b) (47 runs per family) instead of plan A (23). That is 48 extra runs, about $198 over both families (E: 24 × ($3.53 + $4.71), P2 §3.1's planning rates as the first verifier cited them). The reverse error gives a smaller design than the one preregistered. | In `block_init_or_refuse` for block B: when `plan_basis == "sigma_pool_N"`, refuse unless `plan_b["plan"] == doc["provisional_plan"]`. Add a test and a mutant. Under `sigma_A` and `sigma_F`, K2's record step computes the plan from the pinned output (the first verifier's point). |
| KR2 | minor | rules_78b.py:2185, :2189-2190, :2192 (`anchor_stop_problem`); tests/test_rules_78b.py:2236-2281 | Four of the stop record's form checks have no test: counts `needed == 64`, harmful `of == 64`, the `prompt_index` range, and the `job_done_sha256` form. M (`mut-probe.json`): KRV-stop-needed-unchecked, KRV-stop-of-unchecked, KRV-stop-index-range and KRV-stop-jobdone-form all survive. | A later edit drops one of these checks and every test stays green. Then a malformed record is accepted and marks the family stopped (for example counts {kept 10, needed 32}, or {prompt_index 70, position 71, of 128}). | Add the four bad records to test_34's bad list (`anchor_stop_problem` must refuse each). Add the four probes to the rules spec. |
| KR3 | minor | tests/test_rules_78b.py:2557-2563 (test_41) | R-16's guard. test_41 scans 7 named files, and only for the prefix `rules.`. Five more kit files import `stage1_rules as rules` and are not scanned: launch.py, host.py, budget.py, backup_records_stage1.py and setup/preflight_stage1.py (M: grep). Today the seed-only form has exactly the four listed callers (M: check 4). | A new seed-only caller in one of these files (for example the pod-side setup/preflight_stage1.py) keeps every test green. M: probes KRV-seed-only-new-caller (preflight_stage1.py) and KRV-seed-only-new-caller-launch (launch.py) both survive. | Scan every `.py` file under the kit except stage1_rules.py and tests/. Match `\bsc_input_(names\|pins)\(` with any prefix. Hold the exact {file: count} map. The list shrinks to empty by K3's end (R-16). |
| KR4 | minor | rules_78b.py:654-660 (`check_keys`), :1140-1144 (`job_decision`), :1521, :1561-1564, :1893, :2242; setup/job_runner_stage1.py:401 (K3's file) | K1V-6's pod side is not written down. Once `ANCHOR_STOP[F]` is pinned, every process that calls `family_stopped` refuses until it has run `anchor_stop_or_refuse` on the record's bytes. These calls include the pod's `check_keys` and `job_decision` for the MAIN_F retrain, and also `block_runs_78b`, `retrain_job`, `sc_recipe`, `sc_needed_pins` and `sc_order_problem`. M (`tools/regress2.py`): in a fresh process the retrain's `check_keys` is refused ("has not been read at the pin"), while arm and a0_arm pass. The runner does not read the record, and the pack does not carry it. K1's callers-left item names only "the ... stop ... record steps" (R: r1-k1.md:207-212). | A family stops and the lead pins its record. Its MAIN_F retrain pod starts and refuses at the key check: one wasted pod start (E: under $2). The refusal fails safe, but the retrain never runs until K3 wires the read. | Record two acceptance items. K2: the planner reads the stop record in-process before any block A, B or scorer planning. K3: the pack carries the record, and the runner calls `anchor_stop_or_refuse` before `check_keys` and `job_decision`. Add a test for each. |
| KR5 | minor | tests/test_rules_78b.py:2284-2299 (test_34b); B/ws-s/scripts/scale78b/tests/test_blinded_sigma.py:207-211 (Track S's file, read only) | The fourth set asks for "one shared fixture" that both tracks test against. There is none. Track S's fixture writes `counts: {"safe_anchors": 61}`. RK refuses that record ("its counts are not {kept < 64, needed 64}", M). test_34b checks a hand-copied restatement of Track S's check, not Track S's code. At run time K1's records pass Track S's real `check_anchor_stop` (M: `tools/stop_form_probe.py` on blinded_sigma.py `6e7079e8…`). | A K2 writer or test built from Track S's fixture writes a record that RK refuses. Or Track S's check changes in its own fix round and test_34b stays green. | After the merge (lead, K2): make one fixture with `anchor_stop_record` and load it in both suites. Change Track S's fixture to the `{kept, needed}` counts. Add a kit test that runs `blinded_sigma.check_anchor_stop` on that fixture. |
| KR6 | nit | rules_78b.py:1316 (`OEXT_WRAPPER_COMMANDS`); tests/mutation_spec_scorer_78b.json (K4bf-m-c0-needs-oext-script) | The re-targeted K-1 mutant changes a constant that no production code reads (M: grep finds only tests and RULES-78B.md). Its kill comes only from tests that restate the literal (test_scorer_block_78b.py:1603, test_rules_78b.py:2424). M (`mut-sc.json`): HM14's new line kills it. The spec's note already says that K2 re-targets it. | The kill proves no behaviour until K2's command-word check reads the constant. | K-1 as ruled. K2's check of the command word reads `OEXT_WRAPPER_COMMANDS`, and the mutant is re-targeted there. Until then, the note should call it a placeholder. |
| KR7 | nit | rules_78b.py:1888, :2441 | Two more probes survive. (1) KRV-top-pin-any-arms: the guard `"s4_top" in dose_arms` has no test. A filled s4_top pin with other rows must not refuse at kept 48, 96 or ≥ 192 (M: today it does not refuse). (2) KRV-branch-texts: the branch record's utc and recorded_by check has no test. | Both mutants fail in the safe or record-only direction. | Add one assertion for each. |
| KR8 | nit | rules_78b.py:2200-2209 | `anchor_stop_or_refuse`'s JOB-DONE.json check is optional (`job_done_sha256=None` skips it). A family can then be marked stopped without matching the record to the anchor job's own JOB-DONE.json. | A stop record from another job of the same family is accepted. | Make the argument required, or list it as a K2 acceptance item (K2 passes the hash). |

## Check 1: each defect closed as asked (M/R)

- **K1V-1 (the stop record's form): closed.**
  - RK's form (R: rules_78b.py:2106-2110) matches field by field:
    - kind `scale-78b anchor stop`;
    - keys (kind, version, family, stop_kind, exit_code, job_done_sha256, counts);
    - `ANCHOR_STOPS == {"safe_anchors_below_64": 3, "harmful_prompt_does_not_encode": 1}`.
    - These equal Track S's `STOP_RECORD_KIND`, `STOP_KINDS` (R: B/ws-s/scripts/scale78b/blinded_sigma.py:70-71) and
      its fixture's key set (M: `stop_form_probe.py`, keys equal).
  - Decisive check (M):
    - I loaded Track S's real `blinded_sigma.py` (read only; SHA-256 `6e7079e8…411343`).
    - It accepts K1's records for both stop kinds: OLMo few-safe and Llama harmful-pair.
    - It refuses each record when it is read for the other family.
  - K1V-m-stop-kind-old, -value-old and -field-old are killed (M).
  - Left over: the shared fixture (KR5).
- **K1V-2 (K-5's dose arms): closed.**
  - M (`tools/regress.py`): `dose_arms_for(n)` was swept over every n in 0..260 against an independent statement of
    K-5:
    - n ≥ 192: (S4_96, S4_192);
    - 97-191: (S4_96, s4_top);
    - 96: (S4_96,);
    - 49-95: (s4_top,);
    - 48: ();
    - n < 48: Refused.
    - Result: 0 mismatches.
  - For each n, `arm_training_rows("s4_top", n)` is accepted exactly when s4_top is in the set. So 48, 96, ≥ 192 and
    < 48 are refused.
  - Block B's dose rows equal the arms × 1102-1107 for every n.
  - No other mix can be passed: the old `dose_arms=` keyword raises TypeError.
  - s4_top's pin must hold exactly n rows. M: a pin of 120 rows is refused at kept 150 and 70, and accepted at kept
    120.
  - M (`tools/deal_k5.py`): 132 deals (2 families × 3 plans × 11 kept counts × 3 or 6 seeds). None is refused, none has
    more than 4 runs on a pod or one arm twice on a pod, and each run is dealt once.
  - Gap: KR7 (1).
- **K1V-3 (PLAN_B_78B's fields, both ways): closed** (R: rules_78b.py:2001-2036; test_33b, test_33c).
  - Adopted: reason null; basis `sigma_A`; both blinded_sigma hashes required.
  - Not adopted: reason is one of the two; basis `sigma_pool_N` or `sigma_F`, checked against the gate's option at
    block B's init; both hashes null (refused if given).
  - The four K1V-m-plan-b-* mutants are killed (M). My probe KRV-plan-b-adopted-basis is killed too (M).
  - New gap: KR1 (the plan is not checked against N's plan under [B]).
- **R-1 (block A refuses under "review"): closed** (R: rules_78b.py:2081-2083; test_33d; K1V-m-review-plans-a killed,
  M).
- **K1V-5 (BRANCH_78B[F] the only branch source): closed in RK and SR78.**
  - `branch_record_or_refuse` reads the bytes at the pin (R: :2455-2460).
  - `bank500_problem`, `branch_switch_problem` and `oext_flags` read the branch only through it (R: :2463-2502).
  - `sc_pin_values` checks the pin's form (R: :1492-1495).
  - Mutants K1V-m-bank500-unpinned-bytes and K1V-m-flags-unpinned are killed (M).
  - Outside K1's files, plan_tool's inherited 1B branch route remains (open point 1).
- **K1V-6 (a family is stopped only after its record is read and checked): closed** (R: :2200-2225; test_34c).
  - M (`regress2.py`): with a pinned but unread record, `block_runs_78b` is refused in both families. After
    `anchor_stop_or_refuse`, the counts are 12 / 14 / 26 / 38, the same as before the fix.
  - Re-pinning needs a fresh read (test_34c).
  - K1V-m-stop-unread-passes and K1V-m-stop-read-unchecked are killed (M).
  - Left over: the pod-side wiring (KR4) and the optional JOB-DONE check (KR8).
- **K1V-7 (the seven probes): closed.** All seven are in the rules spec as K1V-m-*: edit-pin-any-suffix,
  files-form-any-dir, stop-exit-type, gate-version-type, branch-switch-branch-only, n-units-keys-loose, n-units-r-only.
  All seven are killed by real test failures (M: `mut-rules-*.json`, which names the failed tests).
- **K1V-8 (import never breaks): closed.**
  - M (`tools/n_units_import.py`) tried six malformed N_UNITS shapes: one bad key, a list, a string, the right keys
    with str values, the right keys with wrong value types, and the right keys with None.
  - In every shape the block-0, sc and A copies of stage1_rules import.
  - `rejudged_or_refuse` is refused each time.
- **K1V-11, K1V-12: closed.** The W1_18_HOST_FAMILY comment cites K-3 (R: :2367-2368). RULES-78B.md has K-5's line in
  place of "n in 48-191". The w1_18 regex is now "does not belong to block 0" only (R: test_kit_78b_shell.py:283).
- **R-3 (block 0's plan.json byte for byte): closed. I re-measured it myself.**
  - Method (M: `tools/plan0_only.py`): a fresh World from each tree's own test harness (World is unchanged by K1),
    a real `init-block 0`, the clock fixed at 2026-11-08T00:00:00+00:00 and the tmp path normalised. The base tree
    is `git archive 3481d85 runkit/stage1-78b`.
  - Results, which equal test_42's literal:
    - OLMo-2-7B: 14,106 bytes, `263e2541dc556209ae27441cc0ca94ca328010490b971bb5bf8a077de63915bf`.
    - Llama-3.1-8B: 14,605 bytes, `ceff076129ba87a17c6ff38f450d5fb81a8dfd30762ec3e0b9c6f1082a578555`.
    - `cmp` of the two trees' files: byte-identical.
    - The keys `oext` and `padded_tokens_per_step` are absent in both.
  - M (`tools/b0cmp.py`): with a dry run and a deal made first, at two clocks, the two trees' plan.json SHA-256s are
    equal at each clock and differ between the clocks. So the comparison is not empty.
- **R-5 (one index per family and engine): closed for K1's name form** (R: :1419-1437; test_37c; the six
  K1V-m-index-*, -y-pin-engine-x and -check-keys-y-reads-x mutants are killed, M).
  - `check_keys` reads `OEXT_78B_Y[F]` for an engine-Y job (R: :685-696).
  - Per R-19, the name regex reads K1's form, `oext_index__<F>__<E>.json`, not Track O's `OEXT-78B__<F>.json`. Any fill
    with Track O's names is refused ("0 O-ext index file(s)"), which is safe, until K2 reconciles the two.
- **K-1 re-targets.** M (`mut-sc.json`, scorer runner, 3 ids): K4bf-m-hm14-script-unlisted-ok,
  K4bf-m-c0-needs-oext-script and K4bf-m-oext-kinds-no-regen are each killed by HM14's test. The first is
  behavioural: R-5's wrapper check. The second is a placeholder: KR6.
- **R-17 (w1_18 waits on W1_18_78B; c0, o_only and o_only_with_regenerate wait on OEXT_78B and BRANCH_78B): built.**
  M (`regress2.py`): `sc_needed_pins` adds BRANCH_78B to the three kinds only. Covered by test_29b and
  K1V-m-oext-kinds-no-branch (killed).

## Check 2: block 0 unchanged in behaviour (M: `tools/b0cmp.py`, `tools/b0diff.py`, sandboxed)

- Setup: the base tree is 3481d85's kit (`git archive`) beside symlinks of ws-k's other entries; it is compared with
  ws-k's kit. Each tree uses its own test World. Two clocks were used (2026-11-08 and 2026-12-01).
- Identical at both clocks, for both families:
  - the `init-block 0 --dry-run` printout (every need line and idle line) and its exit;
  - `deal 0`;
  - a real init's stdout;
  - plan.json (length and SHA-256);
  - `block0_jobs`, `block_runs(None, "0")` and `deal`;
  - `BLOCK_KINDS` / `HOST_PREFIX` / `FUNDING_BLOCK` / `REJUDGED_PINS` entries for "0", and `BLOCK0_R_DRAWS`;
  - the RK CLIs `golden` and `block0`.
- Pod side (each tree's own rules_78b), identical:
  - `requirements`, `cap_hours`, `pod_spend_usd`;
  - `job_decision` for every block-0 job at two remaining times (10^6 s and 3,000 s);
  - `check_keys` for arm and a0_arm;
  - the retrain and c0 E pods.
- `e-caps`: only the references changed, and a `w1_18` entry was added. The references are ref_eval 5.0 → 6.75 h
  (OLMo) and 5.25 → 6.75 h (Llama), safe_lora 5.5 / 5.75 → 7.25 h, and ref_train_bqi 4.75 / 5.0 → 6.5 h. None of these
  is a block-0 kind; it is the same as at the first verification.
- `kit`: additions only. These are the seven `job_sha256` values (they equal the builder's list) and the null pins
  ANCHOR_STOP, BRANCH_78B, GATE_78B, METHOD_EDITS, N_UNITS, OEXT_78B_Y, OEXT_TERM_MEASURED_S, PLAN_B_78B and W1_18_78B.
  Nothing was removed or changed.

## Check 3: no regression of what the first verifier passed (M/R)

- Pins, M (`tools/regress.py`, pre-fix against fixed): `R_DRAW_SOURCES`, `METHOD_EDITS`, `KIT`, `STEPS` (33 / 38 /
  38 / 39) and `ARM_STEPS` are equal. The first verifier hash-checked these values against the committed files.
- Block tables, M, both families:
  - block A has 21 runs under every plan;
  - block B has 23 / 32 / 47 runs;
  - with doses at 3 or 6 seeds there are 29 / 35, 38 / 44 and 53 / 59 runs;
  - each table and its deal is equal to the pre-fix one (pre-fix doses (S4_96, S4_192) against kept = 192).
- A stopped family: 12 / 14 / 26 / 38 runs, equal (M, `regress2.py`).
- Caps and funding needs, M, equal to the pre-fix values and to Part 2 §4.3:
  - four 38- or 39-step arms with the term at × 1.5: 17.25 h and 19.25 h; guards $37.91 and $41.61; four-pod needs
    $167.06 and $185.56;
  - one O-ext pass: 3,958.9 s and 4,061.45 s (× 1.5 = 5,938.36 s and 6,092.17 s);
  - the E caps are equal.
- Equal to the pre-fix values (M):
  - the seed key: `sc_units`;
  - the re-judge list: 7 per family;
  - `w1_18_plan`: 7 units under [B], 4 under [C];
  - `BANK500_KINDS`.
  - The only change in `sc_needed_pins` is R-4's BRANCH_78B on o_only, o_only_with_regenerate and c0.
- Anchor-stop rules: changed only as the fourth set asks (form) and as K1V-6 asks (read before stopped). The
  exit-signal rules are unchanged (test_34).
- Non-owned files the builder touched (R: `fix.diff` and `git diff 3481d85`): no assertion was deleted and no literal
  was loosened.
  - test_scorer_block_78b.py:
    - `fill(oext=True)` adds BRANCH_78B and the family's X index (R-4, R-5).
    - The `sc_needed_pins` tuples gain BRANCH_78B. They are still exact tuple equalities, so they are stricter.
    - HM14 still asserts a refusal for each dropped script. The message changed from "does not list" to R-5's "do not
      pin the wrapper", because R-5's form check now comes first and plan_tool's check behind it is dead code (I).
    - HM14 gains the command-word and `scorer_code` assertions.
  - test_kit_78b_shell.py: the regex is narrowed.
  - mutation_spec_scorer_78b.json: two mutants were re-targeted, none retired (KR6).
  - In owned tests, the removed lines are old-form literals replaced by the ruled form. One example:
    `assert not any(j["oext"] …)` became `j.get("oext")`, plus a key-absence assertion. That is stricter.

## Check 4: R-16, the seed-only unit form (M/R)

- M (`grep -rn 'sc_input_names\|sc_input_pins\|sc_unit_input'` over the worktree):
  - The only non-test callers of the seed-only form are the four that test_41 lists: setup/job_runner_stage1.py:466
    and :483, pack_setup.py:432 and plan_tool.py:1306.
  - stage1_rules.py's own internal calls are the form itself.
  - The other hits are archived scratch copies under `.ai/inputs/…/build-round-20261105/`, not kit code.
- So R-16 holds today. test_41 does not hold it against a new caller in five kit files (KR3; two probes survive, M).
- The strict form: `sc_unit_input_names` and `sc_unit_input_pins` refuse a missing arm or a non-unit pair (test_41;
  K1V-m-missing-arm-passes killed, M).
- An equivalent piece of code (I): the explicit `sc_unit_source` call in `sc_unit_input_names` adds nothing.
  `Refused` subclasses `ValueError` (R: rules_78b.py:387), and `sc_input_names` raises the same refusal through
  `_unit_source`.

## Check 5: tests and mutants (M)

- **7-8B suite**, network-deny sandbox, 17:24-17:25 UTC: **538 passed** in 68.4 s, exit 0 (`suite-78b.log`). This
  equals the builder's count and the lead's background run (R: B/lead/k1fix-checks/summary.txt at 17:47 UTC: 538;
  stage-1 kit 762; scale78b 208 + 57 skipped).
- **Rules runner, all 225 mutants**, sandboxed, in two shards:
  - shard 1, 17:39:47-17:41:19 UTC: 112 killed, baseline exit 0 (67 passed);
  - shard 2, 17:41:28-17:43:25 UTC: 113 killed;
  - total: 225 killed, 0 survived, 0 invalid (`mut-rules-1.json`, `mut-rules-2.json`).
  - The lead's background run also has 225 killed. Its runner spec has 35 killed. Its scorer and gated runs were not in
    summary.txt when I last read it, at 17:47 UTC.
- **Scorer runner**, sandboxed: the 3 K-1 / R-5 mutants are killed, baseline 112 passed (`mut-sc.json`).
- **Find texts**: every find text of the four specs occurs exactly once in its file. Counts: rules 225, runner 35,
  scorer 155, gated 128. No duplicate ids, and no mutant whose find equals its replace (M: `tools/find_once.py`).
- **My probes** (`tools/make_probe_src.py`; a scratch source root, ws-k untouched; the rules spec plus 12 KRV-*;
  the same runner): 4 killed, 8 survived (`mut-probe.json`).
  - Killed: plan-b-version-type, s4top-ok-any, n-unit-path-anywhere, plan-b-adopted-basis.
  - Survived:
    - top-pin-any-arms (KR7);
    - stop-needed-unchecked, stop-of-unchecked, stop-index-range, stop-jobdone-form (KR2);
    - branch-texts (KR7);
    - seed-only-new-caller and seed-only-new-caller-launch (KR3).
- Tests that restate the code:
  - The K-1 placeholder (KR6).
  - test_34b's hand copy of Track S's check (KR5).
  - Every other new test holds a literal that does not come from the code it tests: the K-5 cases, the plan-B
    fields, the 3481d85 plan.json bytes, and the R-5 forms.

## Open points for the lead (not K1 defects; I)

1. **A second branch source, outside K1's files.**
   - plan_tool.py's inherited 1B route keeps its own branch record in the plan: `record_branch` (:3805-3852, 1B kinds,
     block S1-0, 11 units), `gate_g1` (:818-824) and `branch_name` (:809-810).
   - Planning (`sc_pins_or_refuse`) checks only BRANCH_78B's pin form, never its bytes. The scorer World's fill pins a
     branch file that does not exist (R: test_scorer_block_78b.py:136).
   - K2's K-8 step should make plan_tool read BRANCH_78B, with a test that the two sources cannot disagree.
2. **R-19**: the index name form (rules_78b.py:1419) must take Track O's names before OEXT_78B or OEXT_78B_Y is
   filled.
3. **The `kept` argument**: the kept S4 count (`kept`) and the dose seeds are caller arguments. K2's planner should
   read `kept` from s4_doses_record.json (Part 2 §1.16), not from the command line.
4. **KR4's two wiring items** (K2's planner, K3's runner and pack) should go on those rounds' acceptance lists.

## Commands run (foreground; exit 0 unless noted)

- `date -u` (×6). `cat`, `sed`, `grep`, `awk`, `find`, `ls`, `diff -rq`, `cmp`, `ps`. `git -C ws-k log`, `status`,
  `diff 3481d85` and `archive 3481d85 runkit/stage1-78b | tar -x` into scratch. All of these are reads.
- `shasum -a 256`: K1's 13 files (twice), the pre-fix copies, `fix.diff` (`64b78359…`, equal to the builder's), and
  Track S's blinded_sigma.py.
- `/usr/bin/python3 -B -I`: `tools/make_base.py`, `tools/b0diff.py`, `tools/find_once.py`,
  `tools/make_probe_src.py` and inline JSON readers.
- Sandboxed (`sandbox-exec -p "$SB"`, PY):
  - the 7-8B suite (538 passed);
  - `tools/stop_form_probe.py`, `b0cmp.py` (×4), `plan0_only.py` (×2), `regress.py` (first try exit 1, a bug in my
    JSON compare; fixed and re-run), `regress2.py`, `n_units_import.py`, `deal_k5.py`, `plan_b_vs_gate.py`;
  - the rules runner, 2 shards (225 killed);
  - the probe runner: first try exit 2, because I had replaced the spec's mutants so the baseline's test_13 failed;
    re-run with the probes appended, exit 1 (8 survived);
  - the scorer runner on 3 ids (3 killed).

Evidence in `R/r1-k1-reverify-scratch/`:
- `k1-full.diff` (`git diff 3481d85`) and `suite-78b.log`;
- `b0-{base,new}-{2026-11-08,2026-12-01}.json` and `work/p0-{base,new}/plan0-*.json` (synthetic plans);
- `regress.log` and `regress2.log`;
- `mut-rules-{1,2}.json` / `.log`, `mut-probe.json` / `.log` and `mut-sc.json` / `.log`;
- `tools/`.

I deleted the scratch kit copies after use, at 17:50 UTC: `base/`, `probe-src/`, the runners' `*-work/` folders and
the World trees. To re-run check 2:
`tools/make_base.py WS OUT`, then `git -C WS archive 3481d85 runkit/stage1-78b | tar -x -C OUT`, then
`tools/b0cmp.py KIT OUT.json WORK CLOCK` on each tree and `tools/b0diff.py A.json B.json`.
