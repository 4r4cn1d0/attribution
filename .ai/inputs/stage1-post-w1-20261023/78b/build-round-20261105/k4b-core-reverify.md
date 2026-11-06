# k4b-core-reverify: kit core re-verify of round 4b (k4b-fix), adversarial

Started 2026-11-06 17:09 UTC (skeleton); this version 18:09 UTC (`date -u` read right before each write). Status: **DONE**.
Verdict: **VERIFIED_WITH_MINOR**. D1, D2, D4, D5, D6, D8, PP17 and PP18 are fixed in the code and hold under my own
hand mutants. D7 is only partly closed. I found 3 minor defects (K4bcr-D1 to D3) and no blocker or major one.

- WS = scratchpad/b78/ws-k2 (read only; HEAD d203070 plus K4a, K4b, M and k4b-fix files).
- SCR = reports/k4b-core-scratch/. SCR/repo is a byte copy of WS without .git (M: shasum lists equal, 9,555 files,
  before and after all my runs). SCR/repo-t was a hard-linked copy with my scratch test file only (now deleted; the
  file is kept as SCR/test_k4bcr_scratch.py, SHA-256 eaaf88f4...).
- PY = the main venv's python. SCI = .venv's python. SBX = `sandbox-exec -p '(version 1)(allow default)(deny
  network-outbound (remote ip "*:*"))'`. Every pytest and mutation run ran under SBX.
- Tags: M measured (command number in section 5), R read (path:line), E estimate, I inference.
- No pod, no spend, no network, no install, no download, no agent, no message. No git state changed (git used only as
  `git --no-optional-locks diff/ls-files/status/log`). No secret, selector, hidden, judge, answer, generation, sample
  or prompt file opened. I did not open the main checkout's tmp/. I left out the S1 data test file, because it reads
  stage 1's S1 edit under tmp/stage1-olmo/ (see section 7).

## 1. Files changed

None in WS or in the main checkout. I wrote only this report and files under SCR: my hand-mutant spec and its maker
(SCR/hm_spec.json, SCR/make_hm_spec.py), the runner SCR/hm_runner.py (byte-identical to the prior core verifier's
reports/k4-core-scratch/hm_runner.py: the kit's run_mutants_scorer_78b.py with `--spec` added and the whole-suite
target, a 5-line diff), my scratch tests SCR/test_k4bcr_scratch.py, the result files hm-*.json and mr-*.json, the
plan and need tables SCR/tables/*.json, and the sha lists and logs.

## 2. Defects (all minor)

**K4bcr-D1 (minor; from K4b, not this round; c0). c0's expected adapter fingerprint is not bound to the packed source
unit.** `C0_SOURCE[family]` holds two separate typed fields, `complete_sha256` and `e1_fingerprint`. The pack binds the
packed `source_complete:R:1101` file to `complete_sha256`. The c0 command passes `e1_fingerprint` as
`--expect-adapter-fingerprint` (R: plan_tool.py:1327; setup/job_runner_stage1.py:594). Nothing compares the two
fields, and the c0 command never reads the packed source unit. At 1B the runner took the fingerprint from the packed,
sealed source COMPLETE.json at run time (`@fingerprint:source_complete:R:1101`; R:
runkit/stage1-olmo/setup/job_runner_stage1.py:517, :770-776), so the two could not differ. Evidence (M #12): my
scratch test S7 fills C0_SOURCE with the source file's hash and another e1 fingerprint. `init-block sc` plans c0 and
does not refuse ("1 failed: DID NOT RAISE"). Effect: a typing error in the lead's recorded step makes B17's X-pin check
report a mismatch that is not real (one c0 pod, guard $13.86-$14.33, and a false alarm on engine X). It cannot give a
false match. Fix: do it the 1B way (the runner reads the e1 fingerprint from the packed source COMPLETE.json after
re-hashing it, and refuses when it differs from the plan's value), or check the two at the pack, plus one test.

**K4bcr-D2 (minor). D7 is only partly closed.** The core verifier's D7 named these hand mutants "the ones with
consequences": HM8, HM12, HM5/HM4, HM7, HM6, HM13, HM14, with "one test each". I re-ran its own spec on the fixed tree,
on the whole suite (M #8). Killed: HM4, HM5, HM8, HM12, HM14 (and HM10, HM15). **Still survived: HM6** (output hashing
follows symbolic links), **HM7** (the scorer release takes another family's packed receipt; KD7) and **HM13** (a
unitless scorer job with no output is complete). The k4b-fix report does not list these three as open. HM13 has an
effect: an `o_only` (theta0) O-ext pass that wrote nothing would be recorded complete with only its cost ledger (I:
run_sc_job's last check is the only guard for o_only; R: setup/job_runner_stage1.py:792). Fix: one test each, or the
lead records them as accepted limits. HM1, HM2, HM9, HM11, HM16, HM17 and HM18 also still survive. The prior verifier
did not list them as consequential (HM16 and HM17 fail closed; HM18 is equivalent in effect).

**K4bcr-D3 (minor, test gaps in this round's new code).** 9 of my 23 hand mutants survive the whole 7-8B suite (451
tests) (M #6, #7). R4 is equivalent in effect: record-done's general unit check `tree / r["unit"]` raises first (R:
plan_tool.py, record_done). The other 8 are real gaps. My scratch tests (S1-S6) kill all 8 (M #10), so each gap has
a ready test:
- R8 (PP17): every seed's side-unit input pin taken from seed 1101. No test plans seed 1102 or 1103 and checks its pin
  against its own KIT a0_units pin. (It fails closed at the pack, because the 1102 file does not hash to the 1101 pin.
  If the wrong file were packed, the acceptance would read LS-04 and fire ruling 7's fallback when it should not.)
- R13 (D5): a1_pass's ANCHOR_BANK binding is not tested. The tests check only l1_scan and classifier (anchor) and
  rep_pass (s3_orig).
- R17 (D8): the backup checks the scorer-unit outputs of o_only_with_regenerate only. The D8 test gives a1_pass
  `"outputs": None`, but a real a1_pass record holds its cost ledger.
- R6, R7, R21 (PP17 acceptance edges): a field missing on both sides counts as equal; a fingerprint that the side lists
  but the regenerated unit omits is skipped; a side unit with no e1 adapter fingerprint is accepted. (The low effect
  holds because the side units are fixed by their pins and the engine writes all of these fields.)
- R9 (PP17 record-done): acceptance false with a reason other than LS-04 is accepted.
- R1 (D1/PP18 runner): the `job-I/` filter on the hashed folders is dropped (the unit folders, and so the states, get
  hashed into outputs).
Fix: put S1-S6 of SCR/test_k4bcr_scratch.py (or equal tests) into test_scorer_block_78b.py.

## 3. Items checked (each with my own hand mutant on the whole suite; SCR/hm_spec.json)

| Item | Result | Evidence |
|---|---|---|
| D1 / PP18: c0 unitless, outputs hashed under job-I/c0, c0_record named | passed | R: diff of job_runner (SC_UNIT_KINDS, c0 branch), stage1_rules.UNITLESS_KINDS + c0; my R2 (record-done: record hash need not equal the output) killed; R1 survived (D3) |
| PP18: C0_SOURCE null until filled; c0 refuses; Y kinds refuse until ENGINE_Y and Y's pack | passed, with K4bcr-D1 | R3 (expected fingerprint from the wrong field) killed; existing tests "C0_SOURCE waits for", "ENGINE_Y waits for", "no packed stage1-Y setup" pass (M #1) |
| D2: the engine verify on every recorded unit; crash on non-zero; record-done needs verified.exit 0 | passed | R5 (a1_pass not verified) killed; R18 (record-done: a1_pass not a unit kind) killed; R4 equivalent; the fixer's K4bf-m-verify-* killed (M #13) |
| D3 / PP17: no standalone regenerate; o_only_with_regenerate on one X pod, own 4.5 h cap, acceptance vs side-unit fingerprints, then O-ext on e1; it and o_only wait on OEXT_78B | passed, with D3 gaps | R (diffs); R10 (acceptance record counts as O-ext output) killed; R11 (o_only does not wait on OEXT_78B) killed; R22 (regenerated fingerprints not recorded) killed; R6, R7, R8, R9, R21 survived, then killed by S1, S3, S4 |
| D4: one state-keeping definition in both printouts (PP14) | passed | R12 (sc block's c0 keeps no states, block 0 still does) killed; R23 (block 0's per-seed pod count dropped) killed |
| D5: ANCHOR_BANK and S3_ORIG_POOL bound to recorded outputs | passed, with D3 gap | R14 (rep_pass unbound) killed; R13 (a1_pass unbound) survived, then killed by S2 |
| D6: OEXT_78B form validated | passed | R15 (empty files) killed; R16 (inputs not SHA-256) killed |
| D7: the prior hand-mutant gaps | **partly** | HM4, HM5, HM8, HM12, HM14 killed; HM6, HM7, HM13 survive (K4bcr-D2) |
| D8: a1_pass a unit in runner, record-done, backup | passed, with D3 gap | R18 killed; R17 (backup outputs) survived, then killed by S6 |
| A2's order (anchor, then S_78, then retrain on Y, then a1_pass on its engine; rep_pass after untuned) | passed | R19 (rep_pass need not wait for untuned) killed; R20 (l1_scan and classifier need not wait for anchor) killed; my S2 ran parts 1, 2 and 3 in order for both families |
| Scorer block plans and needs, both families, test-local pins | passed | M #10, SCR/tables: section 4 |
| The runner's verify step | passed | R: verify_unit is run_job's form (`ENGINE verify --run UNIT --prepared PREPARED`, 600-char tail); R5 killed; K4bf-m-verify-other-folder killed |
| All suites and mutation runners | passed | section 5 |
| runkit/stage1-olmo/ unchanged | passed | M #14 (diff 0, 0 untracked); 762 passed (M #15) |
| CUDA, a real pod, the real scorer, O-ext and lean scripts on a real model | not tested | $0 scope |

My 23 hand mutants (all on the whole suite, network-deny sandbox; each find text exactly once; every copy restored by
hash): **14 killed, 9 survived** (R1, R4, R6, R7, R8, R9, R13, R17, R21). With my 12 scratch tests added (baseline
463 passed), the 8 non-equivalent survivors are **8 of 8 killed**, each by the test meant for it (M #10).

## 4. Plans and needs (M #10; caps h, guard $, spend upper $, need alone $; my arithmetic: guard = 6 + 1.85 x cap,
need = 1.25 x guard, part base = 6 + 1.85 x the launch's caps, all rounded to cents)

| Part | OLMo-2-7B | Llama-3.1-8B |
|---|---|---|
| 1, one launch: anchor 2.25, untuned 6.0, o_only 3.75, o_only_with_regenerate 4.5 per seed (3 / 2 pods), c0 4.25 / 4.5 | base $61.04, need $76.30; 4 pods keep states | base $53.18, need $66.48; 3 pods keep states |
| 2: l1_scan 4.75 X, classifier 3.25 X, rep_pass 4.75 X, retrain 4.5 Y | base $37.91, need $47.39 | the same |
| 3: a1_pass 16.5 on Y (the retrain's engine) | $45.66 | $45.66 |

Every pod's guard, spend and need equals the fixer's section 3 table. Each o_only_with_regenerate pod carries its own
seed's `side_complete:a0:<seed>` pin. That pin equals that seed's KIT a0_units pin, and the pins differ across seeds.
Block 0's printout (the existing tests, which pass) lists 13 idle pods, $4.33 per day, and "3 pods / 2 pods, one per
reused a0 seed, each: ... $17.91".

## 5. Commands (all in the foreground, each under 10 minutes; exit status)

| # | Command (abbreviated) | Result |
|---|---|---|
| 0 | `date -u` before each time written (17:09, 17:19, 17:42, 18:03, 18:09) | 0 |
| 1 | `rsync -a --exclude .git WS/ SCR/repo/`; shasum lists of both; `cmp` | 0; equal (9,555 files); the fixer's 8 file hashes match |
| 2 | `SBX PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests` (cwd SCR/repo) | **0: 451 passed** |
| 3 | diffs of the 6 code files vs the fixer's before/ snapshot (read) | 0 |
| 4 | `PY -B -I SCR/make_hm_spec.py SCR/repo/runkit/stage1-78b SCR/hm_spec.json` | 0: 23 mutants, 0 bad find texts |
| 5 | `sed` of the kit's run_mutants_scorer_78b.py into SCR/hm_runner.py; `diff` with the prior verifier's | 0: identical |
| 6 | `caffeinate -i SBX PY -B SCR/hm_runner.py SCR/repo SCR/hm-a SCR/hm-a.json R1..R12 --spec SCR/hm_spec.json --timeout 300` (17:19-17:24) | 1 (survivors): baseline 0 (451 passed); 6 killed, 6 survived |
| 7 | the same for R13..R23 (SCR/hm-b; 17:24-17:28) | 1: baseline 0; 8 killed, 3 survived |
| 8 | the same with the prior verifier's spec (copied, SHA-256 equal), HM1-HM18 without HM3 (SCR/hm-prior; 17:29-17:36) | 1: baseline 0; 7 killed, 10 survived |
| 9 | `SBX PY -B -m pytest ... test_k4bcr_scratch.py` (S1-S6, SCR/repo-t) | **0: 12 passed** |
| 10 | `caffeinate -i SBX PY -B SCR/hm_runner.py SCR/repo-t SCR/hm-c SCR/hm-c.json R1,R6,R7,R8,R9,R13,R17,R21 ...` (17:40-17:41) | **0: baseline 0 (463 passed); 8 of 8 killed** |
| 11 | dump of the plan tables (part of #9, K4BCR_OUT=SCR/tables) | 0 |
| 12 | `SBX PY -B -m pytest ... test_k4bcr_scratch.py -k s7` | **1: 1 failed (K4bcr-D1, DID NOT RAISE)**, as expected |
| 13 | the kit's runners on SCR/repo under SBX: `run_mutants_78b.py` (two halves), `run_mutants_runner_78b.py ALL`, `run_mutants_scorer_78b.py` (two halves), `run_mutants_gated_78b.py` (two halves), each `--timeout 300` (17:43-18:02) | **all 0: rules 55 + 54 = 109 of 109; runner 31 of 31; scorer 59 + 59 = 118 of 118; gated 58 + 58 = 116 of 116 killed; every baseline 0; 0 invalid** |
| 14 | `git -C WS --no-optional-locks diff --quiet HEAD -- runkit/stage1-olmo`; `ls-files --others` there; the same diff over scripts/stage1, experiments, runkit/gate-b-olmo, .ai, the two frozen build scripts, runkit/family-probe* | 0; 0 files; 0; 0, 0; frozen hashes 18f2fec8... and 26f2f2a1... |
| 15 | `caffeinate -i SBX PY -B -m pytest -p no:cacheprovider -q runkit/stage1-olmo/tests` (SCR/repo) | **0: 762 passed** |
| 16 | `SBX PY -B -m pytest ... scripts/scale78b/tests --ignore=.../test_s1_olmo2_7b_check.py` (HF offline) | 0: 208 passed, 37 skipped (prepared sets not in my copy; scipy) |
| 17 | `SBX SCI -B -m pytest` the 3 noise files and test_g1_check_78b.py | **0: 74 passed** |
| 18 | `PY -I -B scripts/scale78b/make_scorer_settings_78b.py --check` (SCR/repo) | **0: 19 of 19 equal** |
| 19 | the whole suite in SCR/repo-t with my scratch file | 1: 463 passed, 1 failed (S7 only) |
| 20 | shasum lists of SCR/repo and WS after all runs; `cmp` with the first list; `find -name __pycache__` | 0, 0 (both unchanged); none |
| 21 | `rm -rf` of my pytest basetemps, the runners' scratch folders and SCR/repo-t (after copying the scratch file out) | 0; SCR is now 186 MB |

## 6. Acceptance criteria (this re-verify's list)

| Criterion | Result |
|---|---|
| D1-D8 and PP17-PP18 checked by my own hand mutants (one per item at least) | passed (23 mutants, every item covered; D7 partly closed: K4bcr-D2) |
| The scorer block's plans and needs, both families, test-local pins | passed (section 4) |
| A2's order | passed (R19, R20 killed; S2 in order for both families) |
| c0 | passed, with K4bcr-D1 |
| o_only_with_regenerate | passed, with the K4bcr-D3 test gaps |
| The runner's verify step | passed |
| All suites (7-8B 451, stage-1 762, scale78b 208 + 37 skipped, noise 74, maker --check 19/19) | passed |
| All mutation runners (109, 31, 118, 116; zero invalid) | passed |
| runkit/stage1-olmo/ unchanged | passed |
| CUDA, a real pod, real scripts on a real model | not tested ($0 scope) |
| The S1 data test (test_s1_olmo2_7b_check.py) | not tested by me (see section 7, item 1) |

## 7. Jobs for the lead

1. Rule the 3 minor defects. Recommended: one short fix round before the scorer pods. In it, (a) bind c0's expected
   fingerprint to the packed source COMPLETE.json (K4bcr-D1, the 1B `@fingerprint` form); (b) adopt S1-S6 of
   SCR/test_k4bcr_scratch.py, or equal tests (K4bcr-D3); (c) add tests for HM6, HM7 and HM13, or record them as
   accepted limits (K4bcr-D2). None of these blocks block 0.
2. After any merge (cwd: the merged checkout or a copy; PY the main venv): `PYTHONDONTWRITEBYTECODE=1 SBX PY -B -m
   pytest -p no:cacheprovider -q runkit/stage1-78b/tests` (expect 451 + new); the four runners as in M #13; and my
   hand mutants: `caffeinate -i SBX PY -B SCR/hm_runner.py <repo> <new scratch> OUT.json K4bcr-R1,...,K4bcr-R12
   --spec SCR/hm_spec.json --timeout 300` then R13..R23 (about 4-5 min per half). After the fix, every mutant except
   R4 (equivalent) should be killed. Regenerate the spec with SCR/make_hm_spec.py if lines moved.
3. Confirm the S1 data-test exception (the fixer's concern 1). I did not run that file, because it reads stage 1's S1
   edit under tmp/stage1-olmo/, a folder my brief forbids me to open.
4. Delete SCR after review (186 MB: the repo copy, the before/ snapshot, results and logs).

## 8. Unresolved concerns

1. The acceptance compares the q and e1 adapter and optimizer fingerprints the side unit lists, its training identity
   and its manifest. It does not compare `data_config_sha256`, which the 1B J2 accept list had (R:
   runkit/stage1-olmo/setup/job_runner_stage1.py:93-94). PP17 asks for "the side unit's fingerprints", so this is not
   a defect. An e1 or q fingerprint difference would catch any data change that alters training (I).
2. The fixer's concern 2 (c0 in SC_STATE_KINDS, +2 idle lines) is the lead's call. My reading agrees: B17's OUT/train is
   an engine unit with states (R: scripts/stage1_s1/lean_eval_job.py:31, "OUT/train, an ordinary engine
   unit"), and KD5 keeps states until the pull and backup.
3. The c0, o_only and o_only_with_regenerate commands pass no `--w1-18-record`. It is optional in oext_unit.py (R:
   scripts/stage1_s1/oext_unit.py:238). Its need depends on OEXT_78B's re-derivation (M1), as the prior verifier said.
4. The X retrain still needs only a complete Y retrain, not a recorded "differs" verdict (the prior verifier's concern
   2; unchanged).
5. I did not read the sandbox log for my runs. The security re-verifier owns that check.
