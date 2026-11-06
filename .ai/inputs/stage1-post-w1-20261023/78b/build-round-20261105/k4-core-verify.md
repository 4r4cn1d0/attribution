# K4 core verify (K4a non-security items and K4b) - adversarial

Started 2026-11-06 15:26 UTC; this version 16:00 UTC (`date -u` read right before each write). Status: **DONE**.
Verdict: **DEFECTS** (2 major, 6 minor; none blocks block 0; D1-D3 must be fixed or ruled before the scorer pods).

Under test: ws-k2 (read only; HEAD d203070 plus K4a's, K4b's and M's files). SCR = reports/k4-core-scratch/.
SCR/repo is a byte copy of ws-k2 without .git (M: 9,554 files, shasum lists equal by cmp). SCR/repo-t links SCR/repo
and holds its own kit copy with my scratch test file. PY = the main venv's python; PY2 = .venv's python.
Tags: M measured (command number in section 4), R read (path:line), E estimate, I inference.
No pod, spend, network, install, download, agent or message. No git state changed (git used only as
`git --no-optional-locks diff/ls-files`). No secret, selector, hidden, answer or prompt file opened.

## 1. Files changed

None in any worktree or in the main checkout. Written: this report; SCR/ (the copies, my scratch tests
SCR/repo-t/runkit/stage1-78b/tests/test_k4cv_scratch.py, my mutant spec SCR/hm_spec.json and runner SCR/hm_runner.py,
check scripts, mutation results SCR/hm-a.json, hm-b.json, mr-rules.json, mr-runner.json, mr-sc.json).

## 2. Defects

**D1 (major, latent). The runner records every real c0 job as crashed.** `run_sc_job` puts c0 in `SC_UNIT_KINDS` and
requires `job-I/c0/COMPLETE.json` (R: setup/job_runner_stage1.py SC_UNIT_KINDS and `unit = folders[-1]`). B17's lean
job writes `OUT/train` (an engine unit), `OUT/lean` (its lean unit) and `OUT/c0_record.json`, never `OUT/COMPLETE.json`
(R: scripts/stage1_s1/lean_eval_job.py:42, :147, :622). As a unit kind, c0's outputs are also left empty, so
c0_record.json is never hashed into the record. The 1B kit treats c0 as unitless and hashes its outputs (R:
runkit/stage1-olmo/stage1_rules.py:623). Evidence (M #10): my scratch test with the lean job's real layout fails:
"crashed ... no COMPLETE.json in the job's unit". No K4b test runs c0 through the runner (the default fake writes
anchor files for the lean step). Latent: c0 refuses at planning while OEXT_78B and C0_SOURCE are null.
Fix: hash c0's outputs under job-I/c0 (unitless, as at 1B) or take OUT/train as the unit and hash OUT/c0_record.json;
add a runner test with the real layout.

**D2 (major). The scorer runner never runs the engine's verify on a unit it records.** Block 0's `run_job` runs
`ENGINE verify --run UNIT --prepared PREPARED` and crashes on a non-zero exit (R: setup/job_runner_stage1.py:802-807);
the 1B kit did the same for regenerate, retrain and a1_rescore (R: runkit/stage1-olmo/setup/job_runner_stage1.py,
run_job's unit branch). `run_sc_job` records regenerate, the retrain (ruling 10's certificate unit, whose
COMPLETE.json becomes the RETRAIN_UNIT pin and A1's input) and a1_pass without it. Evidence (M #10): the fake pod runs a
regenerate to "complete" with no verify call. Fix: run the engine verify for SC_UNIT_KINDS (record `verified`, crash on
non-zero), and a test where the fake verify fails.

**D3 (major, lead ruling needed). `regenerate` can be planned and launched today, but nothing can use its unit.** It
needs no pin (SC_KIND_PINS `regenerate: ()`), so up to 5 pods (OLMo 1101-1103, Llama 1101-1102; 2.25 h, guard $10.16,
need $12.70 each; M #8) can be released now. At 1B it was half of a pair: regenerate, the J2/LN-12 acceptance check
against the reused unit (reuse_spec), then o_only on the regenerated e1 state (R: runkit/stage1-olmo/setup/
job_runner_stage1.py:17-23, plan_tool LN12_UNITS). Here the acceptance check is gone, `o_only` takes theta0 only
(SC_ARM), and `o_only_with_regenerate` is not in SC_KINDS. So M1's "O and L for the reused units" cannot be finished
with this block, and a regenerated unit is not checked against the side unit. K4b raised the reading as its concern 2.
Fix: make regenerate wait for OEXT_78B (or its own null pin) until the lead rules M1; then port the 1B link (acceptance
check plus the O-ext pass on the regenerated state).

**D4 (minor). Two definitions of "a scorer pod that keeps states" (PP14).** Block 0's printout uses K4a's
`IDLE_SCORER_KINDS = {a1_pass}` and `SCORER_KINDS` (8 kinds, no regenerate), so it prints no need line and no idle line
for regenerate pods. The sc block's `SC_STATE_KINDS` = {retrain, a1_pass, regenerate} says regenerate keeps states.
M #8: block 0's idle pods are N x2, retrain x2, a1_pass x2 ($2.00 per day); block 0's scorer list omits regenerate.
Fix: one constant (after D3's ruling); block 0's report then lists the same pods as the sc block.

**D5 (minor). ANCHOR_BANK and S3_ORIG_POOL are not bound to this copy's recorded outputs.** A2's order is checked by
"an anchor job is complete" only. RETRAIN_UNIT is bound (A1's pass must run on the engine of a complete retrain whose
COMPLETE.json is the pin), but the anchor bank pin is never compared with the complete anchor job's recorded
anchors.json, nor the s3_orig pin with the untuned pass's s3_orig.pool.json. Evidence (M #10): with the anchor job
complete and the pin filled with another file's SHA-256, `init-block sc` plans l1_scan ("DID NOT RAISE"). The K4b
tests themselves fill a pin unrelated to the recorded anchors.json and plan. A wrong pin (another family's anchor file,
or Gate B's 1B file) would run l1_scan under the main config with no check failing. Fix: in `sc_job`, refuse when the
pin is not the recorded output of a complete anchor / untuned job in this plan.

**D6 (minor, fails closed). OEXT_78B's documented form is not what the code reads.** The comment and SC_PIN_EVENTS give
`{"files": {path: SHA-256}}` (R: rules_78b.py, the OEXT_78B comment); `stage1_rules.sc_input_pins` also reads
`OEXT_78B[family]["inputs"]["oext_bank" | "oext_record"]`, and `sc_pin_values` does not validate it. Filled as
documented, o_only and c0 refuse: "input pin(s) ['oext_bank', 'oext_record'] are null" (M #10). Fix: document and
validate `{"files", "inputs"}`.

**D7 (minor). Many new guard lines have no test.** 16 of my 18 hand mutants survive the whole 7-8B suite (413 tests)
(M #12, #13; section 3). The ones with consequences: HM8 (a complete retrain or anchor job can be planned again; A8's
"one retrain pod per family" after completion is untested), HM12 (a Y pod's need line says "engine X"), HM5/HM4 (an
anchor job is complete without anchors.sealed.json; record-done accepts an anchor job with no anchor hash), HM7 (the
scorer release takes another family's packed receipt; KD7), HM6 (output hashing follows symbolic links), HM13 (a
non-unit scorer job with no output is complete), HM14 (o_only and c0 plan without their script in OEXT_78B).
Fix: one test each.

**D8 (minor, cross-item). DK-3 and K4b disagree on whether a1_pass has a unit.** DK-3 (tested by K4a's test_21) keeps
`a1_pass` in `stage1_rules.UNITLESS_KINDS`. K4b's runner records a1_pass with a unit and COMPLETE.json and empty outputs.
`backup_records_stage1.py:305` then checks only a1_pass's outputs (the ledger), not its attributes unit; record-done
does check COMPLETE.json (R: plan_tool.py:4360-4366). At 1B a1_rescore was not unitless (R: stage1-olmo
stage1_rules.py:623). Fix: lead rules one way; then drop a1_pass from UNITLESS_KINDS (and test_21) or hash its outputs.

## 3. Hand mutants (mine; not in any K4 spec; each find text exactly once; run on the WHOLE 7-8B suite)

Runner SCR/hm_runner.py = the kit's run_mutants_scorer_78b.py with `--spec PATH` and the test target changed to
`runkit/stage1-78b/tests` (diff: 5 lines). Baseline exit 0, 413 passed, both batches. Killed only by a real FAILED line.

| Id | File | Mutation | Verdict |
|---|---|---|---|
| HM1 | rules_78b.py | S_78 path outside the configs folder accepted | survived |
| HM2 | rules_78b.py | C0_SOURCE's form unchecked | survived |
| HM3 | rules_78b.py | OEXT_78B's form unchecked | survived |
| HM4 | plan_tool.py | record-done: anchor job without anchor_file_sha256 accepted | survived |
| HM5 | job_runner | anchor job complete without anchors.sealed.json | survived |
| HM6 | job_runner | hashed_outputs follows symbolic links | survived |
| HM7 | plan_tool.py | sc release takes another family's receipt | survived |
| HM8 | plan_tool.py | a complete job may be planned again | survived |
| HM9 | plan_tool.py | the index's pins_78b_sha256 unchecked | survived |
| HM10 | stage1_rules.py | a wait needed by every command ('*') ignored | killed |
| HM11 | rules_78b.py | a non-hash ENGINE_Y returned | survived |
| HM12 | rules_78b.py | a scorer pod's need line always "engine X" | survived |
| HM13 | job_runner | a non-unit job with no output is complete | survived |
| HM14 | plan_tool.py | o_only / c0 plan without their script in OEXT_78B | survived |
| HM15 | plan_tool.py | CONTROL: the part's idle total counts state pods only | killed |
| HM16 | stage1_rules.py | a non-hash input pin kept | survived (fails closed downstream: pack and release compare hashes) |
| HM17 | job_runner | any non-null input pin taken | survived (fails closed: the packed hash must equal it) |
| HM18 | job_runner | the S4 call's exit 1 accepted like 3 | survived (equivalent in effect: exit 1 writes no wrapper record, so the job still crashes) |

## 4. Commands (all foreground; exit status)

| # | Command | Result |
|---|---|---|
| 1 | `date -u` before each time written (15:26:14, 15:41:11, 16:00:20, 16:00:36) | 0 |
| 2 | `rsync -a --exclude .git ws-k2/ SCR/repo/`; `shasum -a 256` both trees; `cmp` | 0; IDENTICAL, 9,554 files |
| 3 | `PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests` (cwd SCR/repo) | **0: 413 passed** |
| 4 | `git -C ws-k2 --no-optional-locks diff --quiet HEAD -- runkit/stage1-olmo`; `ls-files --others` there; the same diff over scripts/stage1, experiments, runkit/gate-b-olmo, runkit/family-probe*, .ai | 0; 0 files; 0 |
| 5 | `caffeinate -i PY -B -m pytest -p no:cacheprovider -q runkit/stage1-olmo/tests` (SCR/repo, own process) | **0: 762 passed** |
| 6 | `PY2 -B -I SCR/check_pins.py SCR/repo ws-m`; index check one-liner | 0: 38 pins, 0 differ from the files in ws-k2 or ws-m; the wrapper's 9 STAGE1_CODE literals and PINS_FILE_SHA256 equal; 18 of 18 index entries equal; index pins_78b_sha256 = the kit pin |
| 7 | git diff of rules_78b.py, stage1_rules.py, plan_tool.py, pack_setup.py, job_runner_stage1.py (read) | 0 |
| 8 | `PY2 -B -I SCR/sc_table.py SCR/repo/runkit/stage1-78b` | 0: every sc pod's cap, guard, spend, need, keeps-states, both families; untuned by my own arithmetic 16,145.81 s / 16,692.12 s, 6.0 h, $17.10, $21.38; block 0 idle pods and scorer kinds |
| 9 | the suite in SCR/repo-t (before adding my file) | 0: 413 passed |
| 10 | `PY -B -m pytest -p no:cacheprovider -q -rfE runkit/stage1-78b/tests/test_k4cv_scratch.py` (SCR/repo-t) | **1: 4 failed** = D1 ("no COMPLETE.json in the job's unit"), D2 (no verify call), D5 (DID NOT RAISE), D6 (input pins null) |
| 11 | `PY2 -B -I SCR/make_hm_spec.py SCR/repo/runkit/stage1-78b SCR/hm_spec.json` | 0: 18 mutants, each find once |
| 12 | `caffeinate -i PY -B SCR/hm_runner.py SCR/repo SCR/hm-a SCR/hm-a.json HM1..HM9 --spec SCR/hm_spec.json --timeout 300` (15:44-15:47) | 1: baseline 0 (413 passed); 9 survived; every copy restored (hashes) |
| 13 | the same, HM10..HM18 (SCR/hm-b; 15:47-15:51) | 1: baseline 0; 2 killed (HM10, control HM15), 7 survived |
| 14 | `caffeinate -i PY -B SCR/repo/runkit/stage1-78b/tests/run_mutants_78b.py SCR/repo SCR/mr-rules SCR/mr-rules.json ALL --timeout 300` | **0: baseline 0; 103 of 103 killed** |
| 15 | the same with run_mutants_runner_78b.py (SCR/mr-runner) | **0: 31 of 31 killed** |
| 16 | the same with run_mutants_scorer_78b.py (SCR/mr-sc; 15:53-15:56) | **0: 79 of 79 killed** |
| 17 | `PY2 -B -I SCR/pp16_pp14.py SCR/repo/runkit/stage1-78b` | 0: X_ONLY_KINDS = PP16's 8; with ENGINE_Y filled test-locally Y runs a1_pass, retrain, o_only_with_regenerate, ref_eval, ref_train_bqi, safe_lora only; nothing on a third engine; X runs all; PP14 lines as section 5 |
| 18 | `PY -B -I SCR/bundle_import.py SCR/repo SCR/bundle-tree/tree PY` | 0: a tree of the engine files plus the 38 SCORER_PINS files only (245 files); the wrapper and 11 1B modules import under -I |
| 19 | `caffeinate -i PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests/scorers` (SCR/repo) | 0: 98 passed, 15 skipped (as K4b #18) |
| 20 | `find SCR/repo SCR/repo-t/runkit/stage1-78b -name __pycache__`; `du -sh SCR` | none; 195 MB |

Not run by me: the gated spec (106; the security verifier's, under sandbox-exec), K4a's security items (DK-1, DK-2,
RV2-1..RV2-9).

## 5. Acceptance criteria (this verify's list)

| Criterion | Result | Evidence |
|---|---|---|
| sc plans and needs, both families: pods, kinds, caps, engines | passed | M #8 (every cap by hand matches K4b's table; untuned 6.0 h both); the tests run both families |
| A2's order enforced at planning | passed, with D5 | R: SC_AFTER; K4b mutants killed (M #16) |
| Refusals while pins are null | passed, with D6 | committed pins all null (test); D6 fails closed |
| Idle-storage lines (PP14) | passed, with D4 | M #17: N x2, retrain x2, a1_pass x2, total $2.00/day; every sc pod prints its line |
| Engines: X_ONLY first, retrain Y then X, a1_pass on its retrain's engine (PP16, ruling 10, A13) | passed | M #17; R: sc_engine_problem; K4b mutants killed. Limit: the X retrain needs only a complete Y retrain, not a recorded "differs" verdict (concern 2) |
| Bundle pins equal M's files | passed | M #6, #18 |
| Runner reads the wrapper record (exit_code, doses.fallback_fired, kept, top_dose) and records counts and hashes only | passed | R: wrapper_summary; the sentinel test; 79 mutants |
| Runner records the unit kinds correctly | **failed** | D1 (c0), D2 (no verify), D3 (regenerate) |
| DK-3 | passed, with D8 | test_21 (K4a); 103 rules mutants killed |
| DK-4 / PP16 | passed | M #17; test_20; 12 K4-m-x-only mutants killed |
| PP14 | passed, with D4 | M #17 |
| Mutation specs (rules 103, runner 31, scorer 79) | passed | M #14-#16, baseline 0, 0 invalid |
| At least six hand mutants of my own | done: 18 run, 2 killed, 16 survived | D7 |
| runkit/stage1-olmo unchanged and its suite passes | passed | M #4, #5 (762) |
| CUDA, a real pod, real scorer scripts | not tested | $0 scope |

## 6. Jobs for the lead

1. Before any scorer-block pod: fix D1 and D2 (runner, with tests); rule D3 (regenerate waits for a pin until M1 is
   ruled, or the 1B link is ported); then D4 to match. D5-D8 in the same fix round.
2. After the fix (exact commands; cwd a copy of the fixed tree, PY the main venv python):
   `PYTHONDONTWRITEBYTECODE=1 PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests` (expect 413 + new);
   the three kit runners and `tests/run_mutants_scorer_78b.py <repo> <new scratch> OUT.json ALL --timeout 300`;
   and my hand mutants: `caffeinate -i PY -B SCR/hm_runner.py <repo> <new scratch> OUT.json ALL --spec SCR/hm_spec.json
   --timeout 300` (about 7 min; regenerate the spec with SCR/make_hm_spec.py if lines moved). My scratch tests
   (SCR/repo-t/.../test_k4cv_scratch.py) should then pass with the fixes.
3. Delete SCR after review (195 MB: two repo copies, mutation folders, results).

## 7. Unresolved concerns

1. c0's command passes no `--w1-18-record`; B17's lean job reads W1-18's pinned record as an O-ext input under the
   oext_pinned branch (R: lean_eval_job.py:28-29, :52, :829). It depends on M1's re-derivation (OEXT_78B); not tested.
2. Ruling 10 runs the X retrain only if Y's fingerprints differ. The kit allows it after any complete Y retrain; the
   verdict lives on the Mac (fingerprint_compare.py), so the lead's record must carry it (I).
3. o_only_with_regenerate (both parts X-only by PP16) is allowed on Y once ENGINE_Y is filled (M #17); it cannot be
   planned in block 0 or sc today (K4a's concern 2).
4. The bundle-only import check (M #18) covers imports, not a run; the 1B modules read settings only through
   `--settings` and the patched pool-pins path (R: their argparse defaults and representation_pass.py:229).
5. The anchor job's outputs are skipped by the backup check (R: backup_records_stage1.py:301), as in the 1B kit
   (R: stage1-olmo backup_records_stage1.py:281); pre-existing, not K4's.
