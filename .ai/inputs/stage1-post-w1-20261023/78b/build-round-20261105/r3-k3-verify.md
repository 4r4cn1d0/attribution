# R3 K3 verify report (adversarial): items 1-12 and 14

Started 2026-11-09 14:24 UTC, finished 15:38 UTC (M: `date -u`). WS = B/ws-k3v (frozen, read-only; never written).
All probes ran in a scratch copy of WS (`cp -pR`, then `.git` removed from the copy; M: the sorted SHA-256 lists of
WS and the copy were equal, 7,395 files). Scratch: R/r3-k3-verify-scratch/. No git state change, no network, pod,
install, download, agent or message. No forbidden folder or sealed file opened. Line numbers are WS's.

## Status

**Done.** Verdict: **NOT_VERIFIED** (one major finding, K3V-1). Everything else the brief lists holds, with three
minor findings and nits.

## Findings

| id | sev | R: path:line (WS) | what | evidence | fix |
|---|---|---|---|---|---|
| K3V-1 | major | runkit/stage1-78b/orchestrate.py:250 with setup/job_runner_stage1.py:642-648 (packed_file), :651-666 (branch_bytes), :669-680, :704-718, :762-776 (w1_18_commands) | `orchestrate.py check-plan` (the $0 Mac check the README runs before launch.py, README:166, and the first step of after-create, orchestrate.py:441-443) builds each job's commands with root = HERE/hosts/HOST on the Mac, where no bundle is unpacked. K3's O-ext commands hash pod files while they are built, so check-plan refuses every block A and B arm pod, every scorer-block o_only and o_only_with_regenerate pod and the W1-18 pod ("the family's branch record is not packed at its pin"). After-create runs it after the pod exists. (c0 already read a pod file in job_commands at d7eb772: K5's c0_fingerprint, :574-596.) The 1B kit builds on the Mac with placeholders and paths only (R: runkit/stage1-olmo/setup/job_runner_stage1.py:279-296) | M: probe `test_zz_k3v_checkplan.py` (2 passed): block A and block B a0_arm pods are refused by check_plan; the same check passes only after the pod's files are copied into hosts/HOST. R: no kit test runs check_plan on an O-ext pod (tests/test_gated_78b.py:615 fakes it) | Build on the Mac from sealed-files.json only: keep every "is it packed, at which pin" check against the sealed doc, read the branch record and the W1-18 record from the Mac checkout at their pins, and hash the files on the pod (in run_job / run_sc_job before the step, or with a pod flag). Add check_plan tests for an A, a B, an sc O-ext and the W1-18 pod. |
| K3V-2 | minor | runkit/stage1-78b/pack_setup.py:430-432 (folder_input), :456 (source_unit pin), :511-519 (folder packing) | `--dev100-source`'s input `source_unit:<arm>:<seed>` packs every file of the unit folder at its on-disk hash: no check against the unit's COMPLETE.json list and no macOS-metadata skip (the W1-18 pack skips it, :615). The unchanged 1B check_source hashes every present file against COMPLETE.json, so one stray file (e.g. `.DS_Store`) refuses the O-ext pass on the pod after the regeneration has trained. It is not the 1B form either (R-61's condition): the 1B record lists each file of a folder input with its SHA-256 (R: runkit/stage1-olmo/pack_setup.py:296-306). It also carries the whole folder (states, every eval file) where the 1B code reads COMPLETE.json, job.json and eval/e1/{generations,guard}.jsonl (R: scripts/stage1_s1/settings/oext_unit.json `dev100.source_files`). The pack side of source_unit has no test | M: `test_zz_k3v_r47.py::test_k3v_a_stray_metadata_file_in_the_packed_source_unit_refuses_on_the_pod` (clean source exit 0; with `.DS_Store` exit 2, "are not the ones its COMPLETE.json lists", no folder). M: my mutants V-06 (source_unit not a folder input) and V-07 (its pin null) survive the whole 7-8B suite | On the Mac: skip macOS metadata and refuse any file whose SHA-256 is not the one COMPLETE.json lists (the 1B check_source rule), or take the 1B per-file list; the lead decides whether states/ are packed. Tests and mutants for the source_unit pack. |
| K3V-3 | minor | setup/job_runner_stage1.py:173 (block B route); pack_setup.py:590 (the check's record flag), :835 (Y only in the scorer copy), :877-893 (the A/B pack), :886-888 (A/B O-ext inputs) | New Mac-side refusals and block B's routes have no behavioural test. Surviving mutants (whole 7-8B suite, 639 tests): V-01b block B arm jobs take block 0's route (no O-ext step; the only kill of the plain form V-01 is a source-text assertion, test_g1_yoext.py); V-08 block B's pack takes no O-ext files, inputs or edits; V-14 the A/B pack without `oext_bank`/`oext_record`; V-12 a Y pack in blocks 0, A, B; V-04 the pack's Mac check passes the W1-18 record under Branch 128 only (the R-47 case, Branch full from a failing record, then refuses on the Mac). Each code line reads right today; each failure would surface only on the pod or block a valid pack | M: R/r3-k3-verify-scratch/mut-vk-1.json, -2, -3, -4 (verdict "survived", exit 0, 639 passed) | Tests: a block-B arm job's commands; a block-B pack (pack.main in a B copy) with O-ext files, inputs and edits; the missing-inputs refusal; a Y pack refused in A and B with ENGINE_Y filled; the pack's check under Branch full from a failing record. Add V-01b, V-04, V-08, V-12, V-14 to the runner spec. |
| K3V-4 | nit | setup/job_runner_stage1.py:1247-1251, :1259-1261; README "any engine-Y job" row; pack_setup.py:586-590 | (a) The `@unit:I` guard (`len(found) != 1`) is untested (mutant V-02 survives); the post-loop check still refuses a second unit, so only one O-ext pass is wasted. (b) The README says every complete Y job writes y-remeasure.json; the code writes it for complete non-arm jobs only (arm kinds refuse on Y anyway). (c) oext_checks reads the branch record before branch_file checks its pin, so a missing record gives a FileNotFoundError traceback, not a refusal | R; M: mut-vk-1.json (V-02 survived) | Test the guard; fix the README row; read the branch record through branch_file first. |

Equivalent mutant (not a finding): V-03 (the stop record and JOB-DONE.json not re-hashed against sealed-files.json
in anchor_stop_check) survives because anchor_stop_or_refuse re-checks both: the record's bytes against the
ANCHOR_STOP pin and the JOB-DONE.json SHA-256 against the record's job_done_sha256 (R: rules_78b.py:2337-2349).

## Checks, in the brief's order

1. **The wrapper's real interface: passed.** Probe `test_zz_k3v_probe.py` (14 cases, M: 14 passed). Every line the
   runner builds goes through the real wrapper's `split_argv`, `check_flags`, `Index` (the committed index bytes at
   the index path, cwd = the pod root) and `check_branch_flags`, then the unchanged 1B parser of its subcommand
   (`oext_unit.parser`, `lean_eval_job_78b._parser`, overrefusal_checks' own parser), under the three branch records
   (full by default; full from a failing record; 128): block A and B arm steps; sc `o_only` (theta0),
   `o_only_with_regenerate` (side a0 and N's R_1101, with `--dev100-source` under 128); c0 `lean run`; `w1_18` for
   both families (engine W1 by default, `--device cuda`, `--data-root data`, no `--guard-batch-size`: R-59). The
   W1-18 files list is W1_18_78B's files plus the side units (R: :778-787); the pack adds the other family's
   prepared set (R: pack_setup.py:646-656); the records come back as `job-I/overrefusal_checks__<F>.json` (R-53;
   mutant V-18, K2's old name, killed by test_5c). This passes only on the pod; on the Mac see K3V-1.
2. **R-47: confirmed, independently.** Probe `test_zz_k3v_r47.py` (M: 3 passed in its own process). Through the
   unchanged 1B `oext_unit.main` (oext_eval `8c429092…`, oext_unit `ae2fb5b5…`, hashes checked) on Track O's
   fixtures, Branch full with a pinned failing W1-18 record: without `--w1-18-record` the run refuses (exit 2, "W1-18's
   record cannot be read", no folder) for `--untuned`, a regenerated and an evaluated unit; with it, exit 0 and
   job.json names the record. The wrapper also refuses the missing record. Branch full by default: oext_eval takes no
   record. So the record is needed at run time, and the rule "the flag whenever the branch record names a W1-18
   record" (rules_78b.py:2634-2647) is right.
3. **Blinding: passed.** No new print or write of an outcome value on any path found (R, every new function). New
   writes: the acceptance record gains `source` (a name); y-remeasure.json holds identities, preflight speed fields,
   ledger stage seconds and progress rows cut to {kind, elapsed_s, rows, capped} (R: :1178-1195); W1-18 records are
   copied and hashed, never read (R: :1110-1120); the pack's wrapper check runs with capture_output and only its exit
   code is used (R: pack_setup.py:563-580); refusals name hashes, names and counts. The anchor-stop read goes through
   `anchor_stop_or_refuse` against the packed JOB-DONE.json (KR8), before key_refusal, on sc, A and B hosts (R:
   :1366-1371); its messages carry no record value (R: rules_78b.py:2310-2349). The anchor step's stderr is kept as
   `job-<i>-anchor/process.log` (M: MAIN/tmp/study-v2-20261002/process_receipt.py:9-11 merges stderr into the log)
   and pulled by "job-*" (R: host.py:79). Record-done's printout: plan_tool.py changed only in write_blinded_part's
   `.new` handling (M: git diff).
4. **Block 0 and money: passed.** M: the 7-8B suite, 639 passed (test_42, plan.json byte for byte, included). R: the
   diffs of plan_tool.py, rules_78b.py and stage1_rules.py touch no block-0 plan, cap or need code; the runner's A/B
   route, sealed paths, O-ext bank key and anchor-stop read are gated on sc/A/B; the pack's new receipt keys are
   written outside block 0 (pack_setup.py:948). A and B arm and a0_arm jobs are planned with `oext=True`, so they
   carry K1's O-ext cap term (R: rules_78b.py:2019, :2027; tested at test_planning_ab_78b.py:282). The runner does not
   itself check a job's `oext` flag; every kit route sets it, so this is noted only.
5. **N's regenerations: passed.** An R unit re-trains on the packed `regen_edit:R:<seed>`, taken only at its
   plan.json pin and sealed-files hash (R: :871-875 with sc_inputs); acceptance reads the first strict-form name,
   `n_complete:<arm>:<seed>` for N's units (R: :984-990; M: test_5e and my probe's N R_1101 line). The planner makes
   R_1101 and a0-1101 two pods (R: test_planning_ab_78b.py:1392-1396); the unit and job names carry the arm.
6. **Engine Y: passed at the kit side.** R: pack_setup.py:735-748 (`engine_sha("Y")` refuses while ENGINE_Y is null;
   YHASH list; the tree's code identity against the pin; mutant V-13 killed); :835 (Y only in the scorer copy; untested,
   K3V-3); :864-867 (the Y O-ext files, the unchanged oext_unit.py among them, from this checkout at their pins);
   the runner writes `job-<i>/y-remeasure.json` for complete Y jobs of the non-arm kinds (the retrain is the first;
   :1422-1427); measured kinds stay refused on Y while Y_MEASURED is False (rules_78b.py:546).
7. **The seed-only form: gone.** M: grep of every non-test kit .py: only the strict callers in stage1_rules.py, each
   passing the arm; test_41's list is empty and `sc_input_names("o_only_with_regenerate", seed)` refuses. The other
   `sc_seeds` callers are block 0's printout and the idle-storage table, which must not change (K-4).
8. **The pack's Mac checks: passed, with K3V-2 and K3V-3.** R-6, R-9, R-23 refuse on any non-zero exit (R:
   pack_setup.py:570-580; mutant V-05, exit 2 accepted, killed). M: the real `oext_78b.py check` in run_check's exact
   environment (env -i, PATH=/usr/bin:/bin, PYTHONDONTWRITEBYTECODE=1, the main venv, sandboxed) exits 0 on the
   committed X indexes of both families and OLMo's W1 index ("waits" where pins are null), so the pack's subprocess
   form works. K-7: ab_edits takes each job's edit only by its exact path and SHA-256 from plan.json (R:
   pack_setup.py:658-679). R-61: see K3V-2.
9. **Mutants.**
   - Re-targeted ("note_r3"), read against d7eb772's text: K2-m-keys-unchecked, K5-H-tok-run-job-env-whole,
     K4bf-m-oext-on-q, K5v-R4-call-site-skips-edits, K6-pack-unlisted-data-not-scanned and K1R-m-flag-dropped-on-c0
     make the same change. K4bf-m-pack-no-seeds now passes (arm None, seed None), which raises for
     o_only_with_regenerate: still the "no unit input" rule. K1V-m-missing-arm-passes: with the check gone,
     sc_unit_source still refuses a missing arm with another message, so only the message test kills it (as before
     the move). K1R-m-dev100-on-theta0 is wider now (True under every branch); my V-15 (the narrow case, an
     unregenerated job under 128) is killed by test_29, so the narrow rule is tested.
   - The scorer spec's other 198 (ids in R/r3-k3-verify-scratch/scorer-rest.txt): **198 killed, 0 survived, 0
     invalid**, every shard's baseline exit 0 (M: mut-sc-aa/ab/ac.json, mut-s2-aa…ap.json; the builder's runner, its
     own test file, sandboxed, `--timeout 240`). Shard ad (25) was stopped by me at about 6 min (before 10) and re-run
     as 8-mutant shards; no result of the stopped run is used.
   - My own 17 (spec R/r3-k3-verify-scratch/vtools/spec_k3v.json; runner vtools/run_mutants_k3v.py = the builder's
     run_mutants_runner_78b.py with the whole 7-8B suite as its tests, `test_zz_*` ignored, and this spec; diff: 3
     lines): **8 killed** (V-01 by a source-text test only, V-05, V-09, V-10, V-11, V-13, V-15, V-18), **9 survived**
     (V-01b, V-02, V-03 equivalent, V-04, V-06, V-07, V-08, V-12, V-14), 0 invalid; baselines exit 0 (639 passed).
10. **Suites (sandboxed, in the copy):** the 7-8B kit **639 passed** (twice, without and with the Y tree; logs
    suite-78b.log, suite-78b-2.log); the stage-1 kit **762 passed** after `tmp/engine-y-34bfd288` was copied into
    the copy (`cp -pR` from MAIN; 3,848 files, sorted SHA-256 lists equal, list hash `389c9ecc…`; without it 8 failed
    and 2 errors, all Y-tree tests: suite-stage1.log); the engine family tests **95 passed**.

## Exact commands for the lead's runs

```
B=/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-goofy-jennings-12ae35/2e006469-731b-4a21-8c98-93331af24388/scratchpad/b78
S=$B/reports/r3-k3-verify-scratch
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'
# a probe copy C of the checkout under test (with .git removed); then:
cp $S/probes/test_zz_k3v_probe.py $S/probes/test_zz_k3v_checkplan.py C/runkit/stage1-78b/tests/
cp $S/probes/test_zz_k3v_r47.py C/scripts/scale78b/tests/oext/
cd C && sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_zz_k3v_probe.py runkit/stage1-78b/tests/test_zz_k3v_checkplan.py
cd C && sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests/oext/test_zz_k3v_r47.py   # own process
# my mutants (the whole 7-8B suite per mutant, about 1-2 min each; run in shards of 4):
sandbox-exec -p "$SB" $PY -B $S/vtools/run_mutants_k3v.py C $S/new-scratch $S/new.json ALL --timeout 300
```
The R-47 probe fails when collected in one process with the kit's tests (the oext conftest binds `scripts.*`
first); in its own process it passes. After a fix of K3V-1, test_zz_k3v_checkplan.py's first assertion inverts.

## Commands run (foreground; exit 0 unless noted)

`date -u` (several); reads (cat, sed, grep, git -C WS status/diff/log); `cp -pR` of WS and of the Y tree, with
shasum lists and cmp (equal); the 7-8B suite (twice, 639 passed); my probes (14, 2, 3 passed; one combined run
exit 1, see above); the real wrapper check, 3 runs (exit 0); the scorer mutant shards (auto-backgrounded by the tool
after 180 s; each under 10 min except the stopped shard ad, exit 143, stopped at about 6 min); my mutant shards
(exit 1: survivors); the stage-1 suite (first exit 1 without the Y tree; then 762 passed); the family tests.

## Acceptance (the brief's items)

- 1 wrapper interface: passed on the pod's tree; **failed on the Mac's launch path** (K3V-1).
- 2 R-47: passed (independent probe).
- 3 blinding: passed. 4 block 0 and money: passed. 5 N: passed. 6 engine Y: passed (kit side). 7 seed-only: passed.
- 8 Mac checks: passed; source_unit's packing not the 1B form (K3V-2).
- 9 mutants: re-targeted ones hold; 198 of 198 scorer killed; 9 of my 17 survive (K3V-2, K3V-3, K3V-4; one
  equivalent).
- 10 suites: 639, 762, 95 passed.

## Concerns and open points for the lead

- K3V-1 blocks every O-ext pod's launch (W1-18 first). The fix touches the runner's command build, which K3 owns;
  orchestrate.py's check_plan is K3's too.
- The size of a packed source_unit folder (states included) is not bounded anywhere; the lead names what is packed.
- The R-47 probe and the kit probes need separate processes (two conftests); keep the suites separate.
- Scratch kept: probes/, vtools/, results JSONs and logs; the WS copy, mutation repos and basetemps are deleted.

## Re-verification (B/ws-k3v2, K3's final state; started 2026-11-10 04:34 UTC, written 04:50 UTC)

Target: B/ws-k3v2 (read-only; M: its sorted SHA-256 list was equal before and after my work, 7,395 files; its 20
changed files hash to the builder's "Final files" table). I worked in a scratch copy (`.git` removed;
`tmp/engine-y-34bfd288` copied from MAIN, 3,848 files, its list equal to MAIN's). Rulings read: sets 21-26.

**Verdict: NOT_VERIFIED.** One new major finding (K3V2-1). K3V-1 to K3V-4 are fixed and held by tests. Everything
else checked holds.

### Findings

| id | sev | R: path:line (ws-k3v2) | what | evidence | fix |
|---|---|---|---|---|---|
| K3V2-1 | major | runkit/stage1-78b/setup/job_runner_stage1.py:447 (key_refusal) with rules_78b.py:667-672 (check_keys) | The pod's key check refuses every trained-reference pod. key_refusal passes the main config's hash for every job whose recipe is not "S"; the planner gives ref_train recipe "G" and ref_train_bqi recipe "BQI" (plan_tool.py:4353), with their configs under the job keys `recipe_g` / `recipe_bqi` (R-70). check_keys accepts only RECIPE_G for ref_train and RECIPE_BQI for ref_train_bqi. So main() records a refusal before the first job on every refs-train pod. This happens after the pod is created and bootstrapped, its models downloaded and its preflight run, so it costs money. Part 2 §3.2's recipe G and B+Qi references never run (six_seed: 10 pods for OLMo-2-7B, 12 for Llama-3.1-8B). R-70's condition, that the job trains under the pinned config, is not met. No main()-level test covers a reference pod (the R-65 tests use arm, sc and Y pods) | M: probe `test_zz_k3v2_keys.py` (both cases): key_refusal returns `(0, "job 0 (ref_train): ref_train runs under RECIPE_G only; recipe 18cc31d7… is not olmo2-7b's G")`, and the same for ref_train_bqi / RECIPE_BQI, while check_keys accepts the job's own pinned config | In key_refusal, take the key from the job's `recipe_g` / `recipe_bqi` config_sha256 for REF_TRAIN_KINDS (the recipe_s78 pattern). Add a main()-level test of a ref_train and a ref_train_bqi pod, plus a mutant. |

No other finding. Notes, not findings:
- safe_lora's `certify` point is counted as a judged reference unit (six_seed: 12 Safe LoRA units per family). Part 2
  §3.1 counts "Safe LoRA 6" evaluation-only points. This judges more units, never fewer. The lead may confirm.
- `source_unit_files` hashes every file in the unit folder and refuses an unlisted one, even one it does not pack
  (states). This follows R-76's letter and fails closed.

### 1. The earlier findings (K3V-1 to K3V-4)

- **My mutant spec, run with my runner** (the whole 7-8B suite per mutant, `test_zz_*` ignored). On ws-k3v2 V-12's find
  text no longer occurs, because R-63 changed the line. I re-targeted it to R-63's line with the same mutation
  (`if False:`); every other find text occurs exactly once. Six shards, 04:36-04:42 UTC, each under 10 min, every
  baseline exit 0 (670 passed). Result: **16 of 17 killed; V-03 survives (equivalent)** (M: R/r3-k3-verify-scratch/rv/mut-vk2-0…5.json).
  - V-01b is killed by test_r75 block B.
  - V-02 is killed by test_r78_v02.
  - V-04 and V-05 are killed by test_r6.
  - V-06 and V-07 are killed by test_r76.
  - V-08 and V-14 are killed by test_r77_v08_v14.
  - V-12 is killed by test_r63 [A].
- **K3V-1: fixed.** M: probe `test_zz_k3v_checkplan2.py` (block A and B, 2 passed).
  - check_plan passes on the Mac with no bundle in hosts/HOST. It writes nothing there, and MAC_ROOT is None again afterwards.
  - The same job's build on an empty pod root refuses ("is not packed at its pin").
  - A wrong sealed listing refuses on the Mac.
  - The checkout's pinned branch record is needed on the Mac (R-75's form).
  - My interface probe (`test_zz_k3v_probe_v2.py`, 14 passed) still parses every built line under the real wrapper. The W1-18 line now carries `--guard-batch-size` from each family's main config (R-59) and needs the job's `families` (R-60).
- **K3V-2: fixed** (R-76, R-81). R: pack_setup.py:515-547.
  - Every packed file is taken at its COMPLETE.json-listed SHA-256, macOS metadata is skipped, and any unlisted file refuses on the Mac.
  - Only COMPLETE.json, job.json and eval/e1/{generations,guard}.jsonl are packed, and a missing one refuses.
  - V-06 and V-07 are killed, as is my safety mutant W-08.
- **K3V-3: fixed** (the V-01b, V-04, V-08, V-12 and V-14 kills above).
- **K3V-4: fixed.**
  - V-02 is killed.
  - The README's engine-Y row matches main(): every complete Y job now writes its record, and the call moved out of the scorer-only branch (R: job_runner_stage1.py:1728-1733).
  - oext_checks reads the branch record through branch_file (R: pack_setup.py:700).

### 2. Correctness against the rulings and Part 2

- **R-68 (13g): holds.** R: plan_tool.py:4324-4519.
  - The seed sets are §3.1's: six_seed 1102-1107, three_seed 1102-1104.
  - ref_eval points: six_seed SP + λ {0.9, 0.75, 0.5}; three_seed SP + {0.75, 0.5}, as R-40 was withdrawn.
  - safe_lora takes default and certify (R-37).
  - Recipe G skips OLMo-2-7B's 1102-1103 (LS-23), and B+Qi runs at every seed on Y.
  - Each job's cert_source follows R-35.
  - ref-inputs writes the pins from their sources.
  - Release derives the pins again and refuses a seed whose certification is not recorded passed (§16.1). A failed seed's refs-eval hosts are kept pending and listed in refs_not_run. Mutants W-03 and W-04 are killed.
- **R-69: holds.** gate_eval_files takes each file at its unit's COMPLETE.json listing (W-09 killed).
- **R-70: partly.** The config pins and the main-config refusal hold on the Mac and on the pod. The pod's key check refuses the jobs: see K3V2-1.
- **R-59, R-60, R-65, R-66, R-71: hold.** The R-66 and R-71 extra gated entries are in launch's precheck, in orchestrate's gated step, and in host.py's `--with-base` on a Safe LoRA host. My mutants W-05, W-06 and W-07 are killed. The R-65 tests do not cover reference pods (K3V2-1).
- **R-79 to R-81: hold.**
  - Block B's init refuses a jobs file without reference_set (plan_tool.py:4332-4346).
  - The judge launches now come after the references, and their units count every judged reference unit (Part 2 §6 J1 (a)). One device per contrast and the Granite fallback stay the judge route's own.
  - R-81: SOURCE_UNIT_FILES equals the 1B `dev100.source_files`. The builder's fixture test goes through the unchanged code.
  - R-83: one judge list per block, as accepted.
- **Caps:** b10_certify's E upper carries one O-ext pass (rules_78b.py:1086-1091). ref_eval, safe_lora and ref_train_bqi carry it inside their E upper (OEXT_REF_KINDS). ref_train carries it through `oext=True` (plan_tool.py:4355).

### 3. Safety (r3-k3-safety-brief.md items 1-6)

1. **Blinding: no outcome printed found** (R).
   - The new Mac paths print only names, pins and counts: ref-inputs, release_refs, record-y-measured, the pack's ref pins.
   - The certification is read only through its verdict: on the pod (`certified`) and at record-done (`certification_gate`).
   - Terms records are hashed and listed, never read.
   - I did not plant sentinels; a sentinel test of block B's planner is not run.
2. **Secrets: hold.**
   - Gated entries are downloaded only by the `--gated --token-stdin` run. The open run refuses a gated entry (R: setup/download_models_stage1.py:127-132, unchanged).
   - The extra Llama entries are in both gated lists (W-06 and W-07 killed).
   - No new code writes the token.
   - Every non-binary file under inputs/ is scanned by the pack (R: pack_setup.py:327-331): the source units, the certification reports and the prefix file.
3. **Sealed files: hold.** Edits are taken by exact path and pin only (ab_edits unchanged), and source_unit as in K3V-2 above.
4. **Money: holds apart from K3V2-1.**
   - The new kinds have caps (section 2).
   - No new path creates or extends a pod; launch.py changed only in its gated entries.
   - Block 0 is unchanged (test_42 passes in the 670).
5. **Stop, never delete: holds.** M: grep of the new added lines for unlink, rmtree, os.remove, rmdir and terminate: none.
6. **Fail closed: holds.**
   - REFS_78B null refuses (ref_lead → refs_or_refuse).
   - RECIPE_G_PATH and RECIPE_BQI_PATH null refuse (ref_config).
   - Y_MEASURED_RECORD is needed with Y_MEASURED.
   - A B+Qi host is priced with engine_sha256 null while ENGINE_Y is null, and its release refuses.
   - On the pod a missing or wrong file refuses (R-75; my W-01 is killed).
   - My safety mutants: **9 of 9 killed** (W-01 to W-09; 3 shards, 04:46-04:49 UTC, baselines exit 0, 670 passed; M: rv/mut-ws9-0…2.json).

### 4. Suites (sandboxed, in the copy; M)

- 7-8B kit: **670 passed**.
- Stage-1 kit: **762 passed**.
- Engine family tests: **95 passed** (rv/suite-*.log).
- scale78b not run, as asked.

### Commands for the lead

```
S=$B/reports/r3-k3-verify-scratch   # probes/, vtools/ (spec_k3v2.json, spec_k3v2_safety.json and their runners)
# in a probe copy C of the checkout (no .git): put probes/test_zz_k3v2_keys.py, test_zz_k3v_checkplan2.py and
# test_zz_k3v_probe_v2.py into C/runkit/stage1-78b/tests/, then
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q C/runkit/stage1-78b/tests/test_zz_k3v2_keys.py   # fails until K3V2-1 is fixed
sandbox-exec -p "$SB" $PY -B $S/vtools/run_mutants_k3v2.py C $S/new1 $S/new1.json ALL --timeout 300          # shards of about 3
sandbox-exec -p "$SB" $PY -B $S/vtools/run_mutants_k3v2_safety.py C $S/new2 $S/new2.json ALL --timeout 300
```

The heavy scratch (the copy, mutation repos, basetemps) is deleted; probes, specs, runners, results and logs are kept.

## Final re-check (MAIN, merged and uncommitted; 2026-11-10 05:20-05:24 UTC)

I worked in a scratch copy of MAIN's .ai, runkit, scripts, experiments, tests, tools and templates (`cp -pR`; M: the
sorted SHA-256 lists of runkit, scripts and experiments equal MAIN's, 1,047 files). MAIN was not written. The copy
is deleted.

**Verdict: VERIFIED.** No finding.

1. **K3V2-1 / R-84: fixed.**
   - M: my probe `test_zz_k3v2_keys.py` on the merged kit, 2 passed (ref_train, ref_train_bqi). Extended in place, it also showed:
     - key_refusal returns None on each job's pinned config;
     - it refuses ("… only …") when that key holds the main config's hash;
     - `recipe_key` returns None for a job without its pinned config.
   - Coverage: PINNED_RECIPE_KINDS minus the S_78 kinds equals PINNED_CONFIG_KEYS ({ref_train, ref_train_bqi}). The S_78 kinds take recipe_s78's key under recipe "S". A recipe-pinned kind under another recipe name gets no key, and a stopped family's MAIN_F retrain (recipe "B") the main one, which check_keys judges (R: setup/job_runner_stage1.py:437-452).
2. **R-87: holds.** R: plan_tool.py:1677-1685 and :1691-1692.
   - `y_measured_read` uses pin_bytes, which refuses a null pin, a missing file or a changed file (:3777-3788), then `y_measured_or_refuse`.
   - Planning: it runs in host_record for any host with a measured kind on engine Y. host_record builds every host: block 0, sc, A/B, the references and requeue moves (:1031, :1376, :3306, :4247, :4263, :6137).
   - Release: it runs in release_refs (:4505-4506). The A/B arm release refuses engine Y outright.
   - The builder's test_r87 and K3j-m-r87-* mutants were not re-run here.
3. **R-88: holds.** M: the kit's runner on my copy, `INT-1-checkplan-skips-unpacked-edits` and `INT-2-pack-skips-released-hosts-edits`: baseline exit 0, **2 of 2 killed**, both by `test_r88_init_block_a_pack_and_check_plan_on_every_released_host_and_an_unpacked_edit_refuses` (fc/mut-int.json).
4. **R-90: no assertion changed.** M: MAIN's test_runner_ab_78b.py (`49e229ca…`, equal to K3's worktree) has exactly two `sb.shutil.copyfile(REPO / rel, w.repo / rel)   # bytes only: …` lines (:1505, :1785). Replacing them with `sb.shutil.copy(REPO / rel, w.repo / rel)` gives the builder's final file byte for byte (SHA-256 `37ae08b567d3e5bc…`). So the merge fix changed only those two calls.
