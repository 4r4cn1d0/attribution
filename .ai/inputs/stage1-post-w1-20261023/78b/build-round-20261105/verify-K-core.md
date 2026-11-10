# verify-K-core: adversarial verification of K1 + K2 (and T2's rules_78b.py as extended)

Started 2026-11-05 18:20 UTC (`date -u`); the finish time is the last line of this file (written with `date -u`).
Verifier: read-only on ws-k (HEAD f5e3b4c); every run that writes went to a copy under
`reports/verify-K-core-scratch/ws` (the copy has no `.git` pointer file, so no git command can touch the shared
worktree from it; `pack_setup.git_state` therefore fails only there). No pod, no spend, no network, no secret read,
no edit to a builder's file. The main checkout (dd87b66) was read by absolute path only.

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.
PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (3.11, pytest 8.4.2);
PY2 = /Users/spiderishi/Coding/attribution/.venv/bin/python (stdlib helpers, `-I -B`). `PYTHONDONTWRITEBYTECODE=1`,
`-B`, `-p no:cacheprovider` on every pytest run. SCR = reports/verify-K-core-scratch.

## 0. Verdict: DEFECTS

Two major defects, four minor. Everything the builders measured on OLMo-2-7B reproduces (M). The Llama-3.1-8B half of
block 0 cannot be packed or planned from the sealed set that is now committed in the main checkout, because the kit
reads a MANIFEST form the committed set does not have (D1). Ruling 11 KD5's idle-storage line is not printed (D2).
T2's 64 mutants and K2's 28 all die; of my 20 hand mutants 15 die and 5 survive (section 5). The money rules carry
over as the brief says (section 6). `runkit/stage1-olmo/` is unchanged and its 762 tests pass.

## 1. Scope and inputs read (R)

- Rulings part 1: `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md:144-178` (ruling 11, KD1-KD11, N's layout).
- Addendum: `.../lead-rulings-part1-addendum-20261105.md:8-31` (A1, A2), `:58-64` (A5), `:78-108` (A8-A13).
- Readiness plan T4: `.../readiness-20261105/78b-readiness.md:243-279` (acceptance :268-274).
- Check: `.../78b-readiness-check.md:34-50` (C1), `:98-104` (C7), `:107-122` (C8), `:123-135` (C11, C12), `:167-196` (M1, M3).
- KCR `research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md:100-130` (§4: s_pod, F_pre, s_obs), `:153-162` (§6, idle storage $0.33/day), `:165-178` (§7, the $56.06 need), `:210-229` (§10 tests), `:258-273` (§12).
- Part 1 draft `research/experiments/2026-11-05-78b-preregistration-part1.md:109-135` (§3.1-3.2), `:163-174` (§3.7), `:337-342` (§12).
- The later lead rulings PP1-PP6 `.../78b/lead-rulings-part2-prep-20261105.md` (committed at dd87b66; none changes block 0's subset; PP3 names `a1_pass` as a separate kind from `rep_pass`, which rules_78b does not yet know: a later round's item).
- Builder reports: build-K1.md, build-K2.md, build-K3.md (all sections).
- Kit code read in full: rules_78b.py (the diff against HEAD and the whole file), stage1_rules.py, plan_tool.py's block-0 route (:265-330, :405-500, :925-1160, :1275-1420), pack_setup.py, setup/job_runner_stage1.py, setup/preflight_stage1.py; the T2 test diff; the adapted test files' ported tests (ast comparison, section 4).
- Sealed inputs (hashes and key names only; no row, prompt or answer read or printed): `.ai/inputs/gate-b-sealed-20261008/out/MANIFEST.json` (d76d8bf9...), `.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json` (2a1db220...; committed at d422fca) and its R_d1-R_d3 key names and counts.

## 2. Checks run (exit status; all foreground, each under 2 min)

| # | Command (cwd SCR/ws unless said) | Exit / result |
|---|---|---|
| 1 | `cp -R -P ws-k SCR/ws; rm SCR/ws/.git` (131 MB) | 0 |
| 2 | PY2 script: COPY-MANIFEST.json vs `git ls-tree f5e3b4c runkit/stage1-olmo` and `git show f5e3b4c:<source>` hashes; copies vs sources | 0: 36 = 36 tracked; 0 hash mismatches; 12 identical, 24 differ = the adapted_by_k1/k2/k3 union exactly |
| 3 | `cmp` budget.py, secret_scan.py, seal.py, account.py vs runkit/stage1-olmo | identical (4 x 0) |
| 4 | `PY -B -m pytest -p no:cacheprovider -q -rfE runkit/stage1-78b/tests` | **0: 211 passed in 20.0 s** |
| 5 | `... runkit/stage1-olmo/tests` | **0: 762 passed in 85 s** |
| 6 | in ws-k: `git diff --quiet HEAD -- runkit/stage1-olmo`; `git status --porcelain \| grep -v " runkit/stage1-78b/" \| wc -l` | 0; 0 lines |
| 7 | `PY -B runkit/stage1-78b/tests/run_mutants_78b.py SCR/ws SCR/mut-t2 SCR/mut-t2.json ALL --timeout 300` (18:34:10-18:34:39 UTC) | **baseline exit 0; killed 64 of 64** |
| 8 | `PY -B runkit/stage1-78b/tests/run_mutants_runner_78b.py SCR/ws SCR/mut-k2 SCR/mut-k2.json ALL --timeout 300` (18:34:59-18:36:31) | **baseline exit 0; killed 28 of 28** |
| 9 | `PY2 -I -B runkit/stage1-78b/rules_78b.py block0` | 0: need $56.06, guard $44.85, spend upper $33.30; caps 8.5 / 12.5 h; retrain pods 4.5 h, $17.91 each |
| 10 | diffs: stage1-olmo vs stage1-78b of the guard-off block and functions; plan_tool FUNDING_* constants and funding_record + funding_rule_decision | functions and constants identical (diff exit 0 for the funding parts; the guard-off block differs by one appended comment sentence and a dropped inner `import pathlib`) |
| 11 | copy of the committed Llama set into SCR/ws/.ai/inputs; `SEALED_SETS["llama31-8b"]["sha256"]` = 2a1db220... in the SCR kit; fresh `tmp/family-probe-s78-{llama31-8b,olmo2-7b}-0/` tar'ed from it (the builders' copies moved aside) | 0 |
| 12 | `PY -B tmp/family-probe-s78-llama31-8b-0/pack_setup.py X --dry-run` (real set, pin filled) | **1: "the llama31-8b sealed set's MANIFEST lists no R draw(s) [1, 2, 3] at role 'edit'"** |
| 13 | `PY -B tmp/family-probe-s78-llama31-8b-0/plan_tool.py init-block 0 --jobs tmp/k1-records/jobs-llama31-8b-0.json --dry-run` | **1: "R at 1101: no edit file in MAN1, Gate B's MANIFEST or a recorded sealed record"** |
| 14 | the pin reverted in the SCR kit (`cmp` with ws-k's rules_78b.py: identical); the llama working copy keeps the filled pin | 0 |
| 15 | mixed-family CLI (section 3, "family refusal"): olmo copy + llama jobs; olmo copy + a0 1103 without family; olmo pack `--family llama31-8b`; llama copy + olmo jobs; olmo plan.json in the llama copy; retrain job; recipe "S" on an arm; the committed folder | all exit 1 with the expected texts |
| 16 | `PY -B tmp/family-probe-s78-olmo2-7b-0/plan_tool.py init-block 0 --jobs tmp/k1-records/jobs-olmo2-7b-0.json --dry-run` (fresh copy) | 0: the 18 need lines, then the JSON |
| 17 | in ws-k (writes nothing): `PY -I -B tmp/family-probe-s78-olmo2-7b-0/pack_setup.py X --dry-run`; the llama one | 0: engine 472fc7f6..., main config e9e98e84... / 18cc31d7..., manifest 9ed61826..., sealed set d76d8bf9... with R_d1-R_d3 f7d7eb86/913b7360/cd8d3328, HEAD f5e3b4c; llama 1 (null pin) |
| 18 | K1's receipt `tmp/family-probe-s78-olmo2-7b-0/setup/packed-stage1-X/setup-receipt.json` read | git_commit f5e3b4c27e11..., engine 472fc7f6..., 225 bundle files, sealed_files 81238896...; setup members include rules_78b.py, measured-basis-78b.json, kit-family.json |
| 19 | (cwd tmp/k2-records/pod-olmo2-7b-0) `PY -I -B ../../family-probe-s78-olmo2-7b-0/setup/job_runner_stage1.py olmo2-7b-0-1 --dry-run --remaining 20000 --free-gb 40`; `--free-gb 7.5`; `--remaining 100000 --free-gb 40 --s-obs 1.16`; the slow pod folder `--remaining 108000 --free-gb 40` | 0: run / run / defer "remaining", requirement 12,244.148 s, s_pod 1.0, remaining 20,000 -> 12,582.5 -> 5,165; KD5 refusal text at 7.5 GB; s_obs defers 3 of 3; slow: s_pod 1.0999975, requirement 13,288.536 s, run x3; the pod folder unchanged (3 inputs) |
| 20 | PY2 one-liners in the llama working copy: `block0_need_report`, guards, the KD2 fallback cap, speed_factor at 1.151 / 1.15, s_obs_defers(1.15 / 1.1500001), free_space_ok(8.0 / 7.999 / None) | this pod alone $36.41; guards $29.13 / $21.73; 3-arm Llama cap 9.75 h; 1.151 refused, 1.15 passes; False / True; True / False / False |
| 21 | 20 hand mutants (SCR/hand_mutants_spec.json, SCR/hand_mutants_runner.py = T2's runner over the whole tests folder, `-x`), three batches (18:42:04-18:47:59 UTC); V-H10 rerun on its direct test (SCR/hand_mutants_runner_one.py) | 15 killed, 5 survived (section 5) |
| 22 | PY2 ast comparison of every ported test (same name) in test_stage1_runkit.py and test_stage1_runner.py: assert and `raises` counts, removed assert lines | section 4 |
| 23 | `fixture()` in the llama copy pointed at the olmo fixture (PY2 one-liner) | refused: "the llama31-8b fixture is not the family's a0-1101 side unit" (M; no test holds it, V-H14) |

## 3. Findings against the acceptance list (plan :268-274) and the rulings

Plan T4 acceptance:
- `pack_setup.py --dry-run` and `pack_setup.py` on both families print engine X 472fc7f6..., the config hashes and
  the manifests: **olmo2-7b passed** (M: #17, #18). **llama31-8b failed** against the committed set (D1): it refuses on
  the null pin today and on the MANIFEST form once the pin is filled (#12). K1's synthetic-set tests pass, which is
  not the acceptance.
- `plan_tool.py init-block 0` writes a plan with caps 8.5 h and 12.5 h and the $56.06 need: **olmo2-7b passed** (M:
  plan.json host cap 8.5, counted 3, guard $21.73, spend upper $12.50; need $56.06 = 1.25 x $44.85; #9, #16).
  **llama31-8b failed** against the committed set (#13); cap 12.5 h and the 4-job layout hold in rules_78b (M: test
  8c; `cap_hours` 12.5) and on K1's synthetic set only.
- `budget.py check` reads the live balance: **not tested** (network; the lead's).
- a job-runner dry run on a fake PREFLIGHT-DONE.json computes s and defers the right job (KCR test 12): **passed**
  (M: #19; the fake documents hold the real a0-1101 side unit's numbers, marked by a `note` field).
- the stage-1 kit's tests still pass unchanged: **passed** (M: #5, #6).
- the token never appears in any record: K3's scope; the runner refuses a present token or token file (ported test,
  passes); not re-verified here beyond the suite.
- `git status --porcelain -- experiments scripts` clean: **passed** (M: #6; nothing outside runkit/stage1-78b/).

Ruling 11 and the addendum:
- KD1 (the M-cap rule governs caps, guards, spends): passed (T2's 28 tests, 64 mutants; stage1_rules delegates every
  money function to rules_78b, R: stage1_rules.py:395-405).
- KD2 (at most 4 counted; caps 10.5 h OLMo, 12.5 h Llama; fallback 3 on Llama = 9.75 h): passed (M: #20; test 9's D7
  cases).
- KD3 (1.15 margin, 1,250 s, 48 min, refusal at s > 1.15 and s_obs > 1.15): passed (M: #20; R: rules_78b.py:49-62).
- KD4 (hold 0 with the reason string): passed (R: rules_78b.py:61-63; plan.json `gate_b_hold_reason` holds KD4's
  text verbatim; the check's C8 wording is overruled by the ruling).
- KD5: the free-space check passed (M: #19, #20; FREE_SPACE_MIN_GB 8.0 is an E, R: rules_78b.py:226); 50 GB volume
  passed (plan host `volume_gb` 50); the state rule is K2's states_tool/finisher (tests pass; not re-run by hand);
  **the idle-storage line failed (D2)**.
- KD6 (E kinds alone with explicit caps; rep_pass at most 16.5 h): passed (M: #9; test "e-kind-not-alone" mutant).
- KD7 (working copies `tmp/family-probe-s78-<family>-<block>/`; KITS_GLOB unchanged; budget.py byte-identical):
  passed (M: #3; R: budget.py:39; stage1_rules.WORKING_COPY_RE).
- KD8 (no config under experiments/ changed): passed (M: #6).
- KD9 / A13 (ENGINE_Y, Y_MEASURED, RECIPE_G, RECIPE_BQI, the Llama MANIFEST pin null until filled; E kinds on Y once
  filled, measured kinds after KD9): passed (test 7c and the K1 mutants, 64/64).
- KD10 (block-0 subset: `arm` R_1-R_3 under the main config, `a0_arm` Llama 1103, the retrain refusing while RECIPE_S
  is null, the scorer kinds as need lines only): passed for this round's stated scope (M: #15 (g), #16; K2's tests
  for the runner's three refusals of the retrain; the a0_arm argv in `test_the_arm_and_a0_arm_jobs_run_under...`).
- KD11 (s_obs after each arm; max(s_pod, s_obs); defer above 1.15; a missing or unreadable record refuses the next
  arm): passed (R: rules_78b.py:611-640 against KCR:113; M: #19; K2's mutants K2-m-s-obs-*). K2 reads s_obs as the
  largest over the finished arms, a conservative reading of "later arms use max(s_pod, s_obs)"; stated in the code.
- N's layout (ruling 11): OLMo passed (M: plan.json: R@1101-1103, steps 33, recipe "B", edits bound by path and
  SHA-256 to Gate B's R_d1-R_d3, each edit's `manifest_sha256` 9ed61826... and counts {remove 600}); Llama: on the
  committed set failed (D1).
- A1 (RECIPE_S null; every kind that needs it refuses): passed on the planner (M: #15 (g): the A1 text) and on the
  runner (K2's `job_commands`, `check_keys`, `job_decision`: tests and mutants K2-m-s78-refusal-off, K2-m-any-recipe).
- A2, A8 (one single-job retrain pod per family, after the anchor job, 4.5 h cap, its own need line): passed (M: #9,
  #16: two lines, cap 4.50 h, guard $14.33, need $17.91).
- M3 (N, the retrain pods and the scorer pods on separate lines): passed (M: #16: 1 + 1 + 2 + 14 lines).
- The main-config rule for arms (P78:99): passed at the jobs file (#15 (h)), at `arm_commands` (hand mutant V-H5
  killed), at the release (`release_hosts0` refuses recipe != "B", R: plan_tool.py:1142) and on the pod
  (`recipe_path`, R: job_runner_stage1.py:117-122).
- Blinding of records: K2's walk (`test_no_record_or_printed_line_holds_a_u_value_an_answer_or_the_edits_text`, both
  families) and the ported sentinel test pass (M: #4). By reading: the runner's records hold statuses, hashes,
  numbers, rule texts; `unit_fingerprints` reads COMPLETE.json's checkpoints and identity only (R:
  job_runner_stage1.py:422-440); `verified.tail` keeps 600 characters of the engine's `verify` printout, which is the
  JSON of `verify_run` (file names, "step N: trained rows differ..." strings; R: experiments/safety_selection/
  __main__.py:335-341, verify.py:228-268) and holds no U, HB, O or answer (I, from the code; the fake engine in the
  tests prints a fixed line). The plan.json and operator-actions.jsonl K1 wrote hold hashes and numbers only (M).

## 4. Copied tests: adaptation vs original (did any weaken?)

- T2's test files (K1's two edits): test 7b's `*.json` list now expects `["COPY-MANIFEST.json", BASIS_FILE]` (the
  purpose, "no config file written", is kept); `T2-m-keys-engine-any`'s find text is now the `engine_allowed` clause
  (the same mutation, "drop the engine check"; killed, M: #7). Not weakened.
- tests/test_stage1_runkit.py: 203 tests in the original, 9 in the copy; 6 share a name. Assert counts orig ->
  adapted: funding zone/future 0 -> 0 (1 -> 1 raises); funding rule breaks 1 -> 1; start-from-the-balance 2 -> 5;
  guard-off once-by-sha 5 -> 5 (1 -> 2 raises); guard-off takes only the decision 1 -> 1; need-and-funding-at-init
  5 -> 9 (the removed asserts are block A's group terms and host names; replaced by block 0's). Not weakened. The
  197 tests not ported test 1B blocks and records the copy refuses by design (K1 section 8 lists them);
  `test_the_1b_blocks_refuse_in_this_copy` holds the refusal (hand mutants V-H15, V-H20 die on it).
- tests/test_stage1_runner.py: 90 -> 16 tests, 11 shared. Every removed assert is 1B-specific (O-ext receipts,
  l1-scan/classifier jobs, the 4-job layout, `len(texts) >= 12` -> `>= 8` for 3 jobs, SENTINELS[3] -> SENTINELS[0]).
  The refusal tests keep `match=` texts ("a token is present", "not a pinned engine", "two engines on one pod",
  "already ran its jobs", "sealed file(s) missing or changed|prepared", "sealed-files.json differs from the plan").
  Several are stronger (the edit-arm test adds the sealed_check return values and `stopped == sealed_file_mismatch`).
  Not weakened.
- tests/test_round30a/34/35.py, test_g1_yoext.py (K2) and test_round31/33.py, test_stage1_judge_route.py (K3): one-test
  pins or trimmed files for 1B-only subjects; the originals pass unchanged in runkit/stage1-olmo (M: #5). The form
  (removal with a pin, not a skip marker) is the lead's call; no assertion about block 0 was weakened by them.
- tests/test_kit_78b_shell.py (K1) and test_kit_78b_runner.py (K2) are new; their synthetic World builds the sealed
  MANIFEST in Gate B's form with R entries only (R: test_stage1_runkit.py:89-100). That is why D1 and hand mutant
  V-H17 escape the suite (section 5).

## 5. Hand mutants (20; SCR/hand_mutants_spec.json; each find text occurs once; the whole 7-8B suite with -x)

| id | mutation | verdict | first killing test |
|---|---|---|---|
| V-H1 | block0_spec_jobs accepts any layout | killed | shell: one_family_per_working_copy |
| V-H2 | resolve_edit accepts an edit on the other prepared set | killed | shell: one_family_per_working_copy |
| V-H3 | release_hosts0 ignores an edit whose sealed SHA-256 changed since init | **survived** | (defence in depth: `manifest()` and `resolve_edit` re-hash against the pin first; untested) |
| V-H4 | arm_commands drops `--edit` | killed | runner: arm_and_a0_arm_jobs_run_under_the_main_config |
| V-H5 | arm_commands accepts a recipe other than B | killed | shell: edit_arm_commands_run_the_main_config |
| V-H6 | JOB-DONE `ok` true on a rule refusal | killed | runner: progress_record_the_rule_cannot_read |
| V-H7 | load_verification does not tie verification.json to PREFLIGHT-DONE's hash | killed | runner: pod_refuses_another_engine_family_recipe... |
| V-H8 | sealed_check drops the engine-arm clause | killed | stage1_runner: edit_file_must_hash_to_its_jobs_sha256_and_arm |
| V-H9 | preflight_checks does not tie the preflight's manifest_sha256 to the plan's | **survived** | (the pod has one packed prepared folder, checked by two other asserts; the verification field is untested) |
| V-H10 | init_block0 refuses funding exactly at the need (`>=` -> `>`) | killed (second run) | shell: need_printout (funds $56.06). First run: INVALID under the kit's rule (an ERROR in a fixture, not a FAILED) |
| V-H11 | load() accepts the other family's plan.json | killed | shell: one_family_per_working_copy |
| V-H12 | sealed_set_or_refuse accepts a non-hex pin | **survived** | (equivalent in effect: `manifest()` then fails the hash comparison) |
| V-H13 | block0_spec_jobs accepts engine Y on a job | killed | shell: jobs_file_that_departs_from_ns_layout[engine X] |
| V-H14 | fixture() accepts the other family's verification.json | **survived** | (K1 report §2 item 4 claims this refusal as M; the code refuses by hand, #23; no test holds it) |
| V-H15 | deal() accepts runs outside N's table | killed | shell: the_1b_blocks_refuse |
| V-H16 | the preflight passes a pod the speed rule refused | killed | runner: preflight_writes_the_speed_and_bank_fields |
| V-H17 | edit_sources takes any family's edit entry with a block-0 draw | **survived** | (on the real Gate B MANIFEST the M edits carry draws 1-2, so the mutant would make init refuse "two sources"; the synthetic World has R entries only) |
| V-H18 | a null-pin key refusal labelled "key" not "recipe_pin" | killed | runner: retrain_kind_refuses_on_the_pod |
| V-H19 | a crash marks later jobs "deferred" | killed | stage1_runner: missing_or_unreadable_heartbeat |
| V-H20 | block_runs plans block A as N | killed | shell: the_1b_blocks_refuse |

Reports: SCR/mut-hand-a.json, -b.json, -c.json, -h10.json (ids, verdicts, exit codes, failed test names, hashes).

## 6. Money rules carried over

- budget.py byte-identical (M: #3); KITS_GLOB ("family-probe-*", "gate-b-olmo*", "stage1-olmo*") unchanged (R:
  budget.py:39); the copies are `tmp/family-probe-s78-<family>-<block>/` so the glob sees them (R:
  rules_78b.py:219; stage1_rules.py:85).
- planning $1.85/h, spend $1.79/h, create refused above $10/h, $6 reserve, contingency 1.25 (R: rules_78b.py:49-60;
  stage1_rules.py re-exports them). Guard = $6 + 1.85 x cap (+ 0 hold); funding need = the stage-1 formula
  (`funding_need_usd`, R: rules_78b.py:458-470), equal to the stage-1 kit's on the same inputs (T2 test 9).
- The guard-off decision: GUARD_OFF_KIND / KEYS / GUARD_REFUSED_EXIT and `guard_off_problem` / `guard_off_record`
  identical in code (M: #10; one appended comment sentence; `record-guard-off` kept in plan_tool's CLI records).
- FUNDING_SOURCE_RULE "user rule: start from the balance", FUNDING_RULE_KIND, `funding_record`,
  `funding_rule_decision` byte-identical (M: #10).
- In-pod stop timers at the cap: host.py create passes `--cap-minutes` to pod-timer-settings (R: host.py:228; K3's
  file, the stage-1 lines kept); stop, never delete (R: host.py:26, :152, :191; "This kit has no delete command",
  host.py:20-21).
- GATE_B_HOLD_USD = 0.0 with KD4's reason string (R: rules_78b.py:61-63).

## 7. Defects

**D1 (major). The Llama sealed set the kit expects is not the one that is committed.** The main checkout at dd87b66
holds `.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json`, SHA-256
2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c (M: shasum). Its `files[]` entries for the R draws
have `role` = "block 0 (N): R_1-R_3 at 1101-1103 (P78 section 3; ruling 11, N's layout)" (and other block strings
for d = 4-16), `family` "R", `draw` d, `seed` 1100 + d, `arm` edit-<sha>, `path` edits/R_d<d>.json, `sha256`,
`same_rows_as` (M: json keys read). The kit keeps only entries with `role == "edit"`: `plan_tool.man_arms` (R:
plan_tool.py:440-442, used by `edit_sources` :933-945) and `pack_setup.sealed_set` (R: pack_setup.py:184-200). So,
with the pin filled, `pack_setup.py X --dry-run` exits 1 "lists no R draw(s) [1, 2, 3] at role 'edit'" and
`init-block 0 --dry-run` exits 1 "R at 1101: no edit file ..." (M: #12, #13). K1's job 1 for the lead (fill the pin,
then pack and plan; build-K1.md §6 item 1; README) cannot succeed as written, and T4's acceptance for Llama is not
reachable without a code change. The refusal is safe. The three edit files are on the Llama prepared set
(`manifest_sha256` c52a50af..., counts remove 600; M) and hash to 5cdedf22..., 8f9f3cd5..., edbc111b... as the
MANIFEST says (M: shasum), so only the selection of the entries is wrong. Fix: select by `family == "R"`, `draw` in
BLOCK0_R_DRAWS and a `path` under edits/ (or read the set's `roles` map), in both functions; replace the rules_78b
SEALED_SETS comment (R: rules_78b.py:154-159) and the README/K1 job text; add a test that reads the committed Llama
MANIFEST by its pin (it is in the checkout now) and binds R_d1-R_d3 to 5cdedf22.../8f9f3cd5.../edbc111b...; then the
recorded pin fill (with D3).

**D2 (major). KD5's idle-storage line is not printed.** Ruling 11 KD5: "an idle-storage line in each block's need";
Part 1 §12: about $0.33 per day per stopped 50 GB pod (KCR:161). `grep -i idle` over stage1_rules.py, plan_tool.py,
rules_78b.py finds nothing (M); the 18 lines of #16 are N, this pod, 2 retrain pods, 14 scorer pods. Fix: one line in
`stage1_rules.block0_need_report` (E: n_stopped_pods x 50 GB x $0.20/GB/month / 30 = $0.33 per pod per day, labelled E,
KCR:161) and in the summary JSON; one assertion in `test_the_need_printout...`.

**D3 (minor). Test 7c pins the Llama MANIFEST pin as null.** `tests/test_rules_78b.py` test_07c asserts
`R.SEALED_SETS["llama31-8b"]["sha256"] is None`; the lead's recorded fill fails T2's suite and every mutation baseline
(M: my first `run_mutants_78b.py ALL` with the pin filled stopped at "the baseline did not exit 0", 1 failed). The
fill step must update that assertion (and the K1-m-sealed-set-null-passes mutant stays valid).

**D4 (minor). An M claim without a test.** build-K1.md §2 item 4 says `fixture()` "refuses a file of the other family
(M)". No test holds it: hand mutant V-H14 (the recipe/manifest/identity check removed) survives the whole suite. The
code does refuse by hand (M: #23). Add the test (the World can point the pin at the other family's synthetic fixture).

**D5 (minor). The synthetic sealed MANIFEST is thinner than the real sets.** It holds R entries at role "edit" only
(R: test_stage1_runkit.py:89-100): the Gate B set's M-family edits with draws 1-2 and the Llama set's role strings are
not represented, so D1 and V-H17 escape the suite. Build the World's manifests in both committed forms (Gate B's and
the Llama set's), or test against the committed files by pin.

**D6 (minor). A wrong figure in build-K1.md.** §2 item 5 gives "this pod's need alone ($27.16 / $34.86)"; the kit
computes $36.41 for the Llama pod (1.25 x cents($6 + 1.85 x 12.5) = 1.25 x $29.13; M: #20). The OLMo figure $27.16 is
right. The code is right; the report line is not.

## 8. Jobs for the lead

1. D1: change `plan_tool.man_arms`/`edit_sources` and `pack_setup.sealed_set` to the committed Llama form (and keep
   Gate B's), add the real-set test, then fill `SEALED_SETS["llama31-8b"]["sha256"]` = 2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c
   by a recorded step together with test 7c's assertion (D3); then, in a fresh `tmp/family-probe-s78-llama31-8b-0/`:
   `PY -B tmp/family-probe-s78-llama31-8b-0/pack_setup.py X --dry-run`, `... X`,
   `PY -B tmp/family-probe-s78-llama31-8b-0/plan_tool.py init-block 0 --jobs JOBS --dry-run` (JOBS as K1 §6 item 1),
   then `--funding FUNDING`. Expected: 4 jobs, cap 12.5 h, spend $20.80, edits bound to 5cdedf22.../8f9f3cd5.../edbc111b....
2. D2: the idle-storage line (one line of code, one assertion), then rerun `test_the_need_printout...`.
3. D4, D5: the two tests; rerun my hand mutants V-H14 and V-H17 (SCR/hand_mutants_spec.json, SCR/hand_mutants_runner.py:
   `HAND_SPEC=... PY -B hand_mutants_runner.py <root> <new scratch> <out.json> V-H14,V-H17`) to see them die.
4. `budget.py check` with the live balance (and account.py) in each working copy before any launch (the network).
5. Merge by explicit paths as K1-K3 list; re-pack in a fresh working copy before the first pod (K2's job 7, K3's job 4)
   so the setup tar carries K2's and K3's pod-side files (K1's packed receipt in ws-k/tmp holds the old ones: M, #18
   lists `job_runner_stage1.py` etc. by name only, not by K2's content).
6. Delete SCR (my copy of ws-k, 131 MB, with the Llama set copied in and a filled pin in the llama working copy) and
   ws-k/tmp after the merge; nothing in them is a deliverable.

## 9. Unresolved concerns

1. `orchestrate.cap_gate` (Mac-side) uses K1's `stage1_rules.requirements`, which ignores the preflight projection
   (s = 1); the pod-side `rules_78b.job_decision` and K2's preflight `speed.refused` (ok false) are the gates that read
   s. K2 and K3 both left it to a lead ruling; a slow pod stops at "the preflight did not pass" before any job, so the
   money at risk is the setup time (E, KCR:108).
2. `verified.tail` (600 characters of the engine's `verify` printout) in each job record: by the engine's code it holds
   file names and step-level problem strings, no evaluation value (I); K2's one-line tightening to the exit code is
   available if SR-2 is to be airtight.
3. The fixture pins read two numbers-only verification.json files from the checkout's git-ignored tmp/ (K1 concern 4);
   a Mac without them refuses init-block 0.
4. A rule refusal (KD5, s_obs, a null pin, check_keys) ends with JOB-DONE `ok` false and the finisher's
   review-needed-stopped, even when every started arm completed (K2 concern 4). Intended; the lead reads the case.
5. The states backup asset size (K2's job 4: about 5.8 GB per 3-arm host, E; GitHub's 2 GiB per-asset limit, E).
6. plan_tool.py keeps about 4,000 lines of 1B code reachable only by later ports (K1 concern 3).
7. PP3 (dd87b66) names `a1_pass` as its own kind beside `rep_pass`; rules_78b knows `rep_pass` only. Not block 0's,
   but the scorer round must add it.
8. No spend, no pod, no network, no real token here: the pod-side flow is verified with fakes and the real side unit's
   numbers; the live `budget.py check` and the Llama gated precheck are the lead's.

## 10. State left for the next stage

- Passing (M, in my copy of ws-k): the whole 7-8B suite, 211 tests, 14 files; runkit/stage1-olmo's 762; T2's 64 and
  K2's 28 mutants killed; 15 of my 20 hand mutants killed, 5 survivors analysed above (3 are equivalent or near
  equivalent in effect, 2 are test gaps: D4, D5).
- Working against the committed inputs: OLMo-2-7B block 0 (dry pack, real pack with HEAD, init-block 0 with the
  $56.06 need, the plan with caps and edits, the runner's dry run). Llama-3.1-8B block 0: refuses on the null pin now,
  and on the MANIFEST form once filled (D1); its layout, cap and a0 1103 are proven on a synthetic set only.
- Stubbed or scoped out by the brief: the retrain and scorer kinds (need lines and refusals only); `RECIPE_S`,
  `ENGINE_Y`, `RECIPE_G`, `RECIPE_BQI`, the Llama MANIFEST pin all null; `probes.BASE_MODELS` revisions null.
- Adapted tests: T2's 7b list and one mutant find text (equivalent); the ported runkit and runner tests are equal or
  stronger than the originals for block 0; the 1B-only files are pins.
- Scratch left for the lead to delete: SCR/ws (my copy), SCR/mut-*.json and folders, SCR/hand_* files,
  SCR/dryrun-*.json, SCR/jobs-*.json.

Finished Thu Nov  5 18:53:47 UTC 2026 (date -u). Nothing in ws-k or the main checkout was written; no git state changed; no pod, spend, network or secret.
