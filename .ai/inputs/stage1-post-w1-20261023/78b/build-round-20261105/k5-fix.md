# K5 fix: kit minor items (round 5)

Started 19:17 UTC; this version 21:00 UTC, 6 Nov 2026 (`date -u` read right before each write). Status: **DONE**.

- WS = scratchpad/b78/ws-k3 (HEAD e5a2f86, clean at start). SCR = reports/k5-fix-scratch/.
- PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (the main venv).
- SBX = `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'`. Every pytest run
  and every mutation run below ran under SBX, with PYTHONDONTWRITEBYTECODE=1, `-B` and `-p no:cacheprovider`.
- Tags: M measured (command number in section 4), R read (path:line), E estimate, I inference.
- No pod, spend, network, install, download, agent or message. No git state changed (git used only as
  `git --no-optional-locks status/diff/ls-files/log/rev-parse`). Nothing written in the main checkout. No forbidden
  folder, selector, hidden, judge, answer, generation, sample or prompt-text file opened. Every token-shaped value
  was built at test time (`"hf_" + "K5" * 17`, `"hf_" + "R5" * 17`); a secret_scan of the kit and SCR finds no hit (M #24).

## 1. Files changed (all in WS, all under runkit/stage1-78b/)

| File | Change |
|---|---|
| setup/job_runner_stage1.py | D1: new `C0_SOURCE_INPUT` and `c0_fingerprint()` (:514-541); the c0 command takes its `--expect-adapter-fingerprint` from it (:619) |
| pack_setup.py | R4: `DATA_PREFIXES = ("data/", "inputs/")` (:66; edits/ now scanned); module and `refuse_secrets` docstrings say data/ stays outside because its manifest SHA-256 pins every byte |
| README.md | R4 and D1: two bullets in the scorer-block section (the scan's coverage and the data/ rule; c0's fingerprint) |
| tests/test_scorer_block_78b.py | D1 fixtures (`c0_source()` lists an e1 fingerprint; the by-hand command test writes a real source file); new sections 8 (D1, D2, D3: 18 test cases) and 9 (R4: one test) |
| tests/test_pp10_process_wide.py | R1: stand-in gets `type`/`proto`, every wrapper case runs on stream and datagram; real IPv4/IPv6 datagram probes must refuse in the wrapper; module `sendto` must name the wrapper. R2: daemon-thread and ThreadPoolExecutor probes at collection and in the test |
| tests/test_gated_78b.py | R3: `_real_opener_with_fake_open` now runs the opener's own request processors and `opener._open`, with http.client's two connection classes replaced by recorders; `test_rv2_1` checks one verifying https connection to the Hub per request |
| tests/test_kit_78b_runner.py | R5: two tests that record `env` of every step and verify (run_job; run_sc_job and verify_unit) |
| tests/mutation_spec_gated_78b.json | +8 mutants (116 -> 124) |
| tests/mutation_spec_runner_78b.json | +3 mutants (31 -> 34) |
| tests/mutation_spec_scorer_78b.json | +22 mutants (118 -> 140) |

mutation_spec_rules_78b.json is unchanged: no rules file changed (rules_78b.py, stage1_rules.py, plan_tool.py and
backup_records_stage1.py are byte-equal to HEAD; M #25). runkit/stage1-olmo/ is unchanged (M #21).
Snapshots of the touched files before my edits: SCR/before/.

## 2. Items: what I changed and the evidence

### Item 1, K4bcr-D1: c0's expected fingerprint from the packed source unit
- Change (R: setup/job_runner_stage1.py:517-541, :619). On the pod, `c0_fingerprint` re-hashes the packed
  `inputs/source_complete-R-1101/COMPLETE.json` against the job's plan.json pin, reads only
  `checkpoints.e1.adapter_fingerprint`, and raises Unrunnable when the file is missing, a link, off its pin, holds no
  e1 fingerprint, or holds one that differs from the plan's `expect_fingerprint` (C0_SOURCE). The lean job gets the
  value read from the file. This is the 1B form (R: runkit/stage1-olmo/setup/job_runner_stage1.py:517, :770-776).
- Tests: `test_k5_d1_c0_reads_its_expected_fingerprint_from_the_packed_source_unit_and_refuses_another` (the value
  passed; the three refusals), `test_k5_d1_a_c0_pod_whose_c0_source_step_differs_from_the_packed_unit_runs_no_step`
  (real route: init plans c0 with the typo, the pod crashes with the refusal and runs no step; with the right value
  the lean job gets it).
- Mutants (scorer spec): K5-c0-fp-from-plan, K5-c0-no-compare, K5-c0-no-rehash, K5-c0-no-e1-check: **4 of 4 killed**
  by the first D1 test (M #13, #14).
- Limit: the check is on the pod, so a typo still costs one pod start (E: the pod's setup time). init-block cannot
  check it, because the Mac does not read the source unit at planning. The re-verifier's S7 (init must refuse) is
  therefore not adopted (it was outside S1-S6). See concern 1.

### Item 1, K4bcr-D2: tests for HM6, HM7, HM13
- HM6: `test_k5_d2_hm6_the_output_hashing_never_follows_a_symbolic_link` (a file link and a folder link in a job
  folder are not hashed).
- HM7: `test_k5_d2_hm7_the_scorer_release_refuses_another_familys_packed_receipt` (receipt family changed to the
  other family: the release refuses with the KD7 message; restored: it releases).
- HM13: `test_k5_d2_hm13_a_unitless_scorer_pass_that_wrote_nothing_is_a_crash` (o_only exits 0, writes nothing:
  crashed "the job wrote no output"; writing one file: complete).
- Mutants: K5-HM6, K5-HM7, K5-HM13 in the scorer spec: **3 of 3 killed** (M #14). The prior verifier's own HM6, HM7,
  HM13 on the whole suite with its spec and hm_runner.py: **3 of 3 killed** (M #19).

### Item 1, K4bcr-D3: S1-S6 adopted
- S1-S6 of k4b-core-scratch/test_k4bcr_scratch.py are now `test_k5_s1_...` to `test_k5_s6_...` in
  test_scorer_block_78b.py (same assertions; the K4BCR_OUT table dump and S7 left out).
- Mutants: K4bcr-R1, R6, R7, R8, R9, R13, R17, R21 copied into the scorer spec: **8 of 8 killed**, each by the test
  meant for it (M #14: R1 by S5, R6 by S3c, R7 by S3b, R8 by S1, R9 by S4, R13 by S2, R17 by S6, R21 by S3a).
- The verifier's runner and spec (SCR/hm/hm_runner.py and hm_spec.json, byte copies, SHA-256 dfa4cbfb... and
  0d6531a0...) on the whole suite: **22 of 23 killed; K4bcr-R4 survived**, which the verifier itself records as
  equivalent in effect (record-done's general unit check raises first) (M #16-#18).

### Item 2, R1-R3: guard and TLS tests
- R1 (R: tests/test_pp10_process_wide.py:291-333): the stand-in has `family`, `type`, `proto`; every D1 wrapper case
  runs for SOCK_STREAM and SOCK_DGRAM; three REAL datagram probes (IPv4, IPv6, IPv6 with flags; numeric addresses,
  fail-closed behind the hook as before) must be refused by the wrapper ("before any name resolution") at collection
  and in the module fixture; the existing module-scoped real `sendto` probe must name the wrapper too.
- R2 (:362-377 and :420-426, the D2 test): the hook probes also run in a daemon thread and in a ThreadPoolExecutor worker (default
  names), at collection and in the test.
- R3 (R: tests/test_gated_78b.py:984-1053, test_rv2_1 at :1422): the fake opener runs the opener's `<scheme>_request`
  processors and `opener._open` (the real default_open / https_open dispatch). http.client.HTTPConnection is a
  recorder that fails the test at once; HTTPSConnection is a recorder that computes the effective context as
  http.client does (the given one, else ssl's default factory at the call; check_hostname overrides) and fails the
  test unless the host is huggingface.co and the context verifies. Only OpenerDirector.open's audit event and its
  response processors are skipped. Every existing gated test passes with it (M #5, #23).
- Mutants (gated spec): the re-verifier's H-d1-wrapper-skips-dgram, H-d2-hook-daemon-threads-free,
  H-d2-hook-executor-threads-free, H-d3-default-open-mixin, H-d3-https-request-downgrade,
  H-d3-instance-https-open-unverified, plus H-d3-connection-class-unverified and H-d3-global-unverified-at-call
  (both had died only by chance or order in round 4b): **8 of 8 killed** (M #9). The dgram mutant dies in the
  module-scoped test; the two thread mutants in the D2 test; the five TLS mutants in the first test that calls
  http_get through the recorder (test_d1_...; test_rv2_1 would fail too).

### Item 2, R4: the pack's scan
- Change (R: pack_setup.py:66 and the docstrings): edits/ is scanned; data/ stays outside, said in pack_setup.py and
  the README. inputs/ keeps its own loop.
- Test `test_k5_r4_the_pack_refuses_a_token_shaped_string_in_every_file_kind_it_ships`: after a clean pack, a
  token-shaped string built at test time in an engine file, a scorer script (at a test-local pin), probe.json (a
  monkeypatched probe_record), the bootstrap (a monkeypatched PIP_PIN) and a setup-tar member (setup/extend_cap.py)
  each refuses the real pack with names and pattern names only; the string never appears in the message; no
  setup-receipt.json is written; the bundle scan's refusals come before anything is written. Then a clean pack again;
  `refuse_secrets` refuses an edits/ file and passes a data/ file.
- Mutants (scorer spec): the re-verifier's five (setup tar, payloads, bootstrap, engine files, scripts) plus
  K5-pack-edits-unscanned and K5-pack-data-scanned: **7 of 7 killed** (M #13, #14). The payload mutant survived my
  first run (M #12): the setup-tar scan caught probe.json later. I added the "before anything is written" check; the
  rerun killed it (M #13).
- The bootstrap and setup-tar refusals come after the bundle is written, so they leave a partial
  setup/packed-stage1-X/ with no receipt (R: pack_setup.py main). Release reads only the receipt. The README says to
  move it aside.

### Item 2, R5: the steps' environment
- Tests (tests/test_kit_78b_runner.py:1040-1077): the pre-job token check passes, then a FAKE value goes into every
  TOKEN_ENV_NAMES variable and HF_HUB_OFFLINE=0 in os.environ; every recorded process_receipt step and engine verify
  must get an env dict with no token variable, HF_HUB_OFFLINE == "1" and no fake value. run_job: block 0's jobs
  (steps and verifies counted). run_sc_job and verify_unit: o_only_with_regenerate through the real route (3 steps,
  1 verify).
- Mutants (runner spec): H-tok-verify-env-whole, H-tok-sc-steps-env-whole, H-tok-run-job-env-whole: **3 of 3 killed**,
  each by its own test (M #10, #22).

## 3. Results in short

| Run | Result |
|---|---|
| Whole 7-8B suite under SBX | **471 passed** (451 before + 20 new cases) (M #23) |
| runkit/stage1-olmo suite under SBX | **762 passed** (M #21), after copying the git-ignored engine-Y fixture tmp/engine-y-34bfd288 into WS/tmp/ (M #20; without it 8 failed, 2 errors: they need that tree; M #19b) |
| Gated runner (SBX), 4 chunks | **124 of 124 killed**, 0 survived, 0 invalid, every baseline 0 (M #6-#9) |
| Runner runner (SBX) | **34 of 34 killed** (M #22, the final rerun; first run also 34 of 34, M #10) |
| Rules runner (SBX) | **109 of 109 killed** (M #11) |
| Scorer runner (SBX), 11 chunks | **140 of 140 killed** (M #13, #14) |
| Core re-verifier's hm_runner + hm_spec (whole suite, SBX) | 22 of 23 killed; R4 survived (equivalent, the verifier's own reading) (M #16-#18) |
| Prior verifier's HM6, HM7, HM13 (whole suite, SBX) | 3 of 3 killed (M #19) |

## 4. Commands (all in the foreground, each under 10 minutes; exit status)

| # | Command (abbreviated; cwd WS unless said) | Exit / result |
|---|---|---|
| 0 | `date -u` before each time written (19:17, 19:34, 20:59) | 0 |
| 1 | reads: the two re-verify reports, k4b-fix.md (skim), rulings (grep), the verifiers' specs, scratch tests and runner; the kit's code and tests | 0 |
| 2 | `git status/log/rev-parse` in WS | 0; clean, HEAD e5a2f86 |
| 3 | copy of the touched files to SCR/before/; `SBX PY -B -m pytest ... runkit/stage1-78b/tests` (baseline) | **0: 451 passed** |
| 4 | edits; per-file pytest runs under SBX while building (scorer file: first 2 failed in my new tests, fixed; then 17 passed; guard files 59 passed; gated 133 passed; runner files 53 passed) | 1 then 0 (my test bugs: a re-loaded module's Unrunnable class; release returns a dict) |
| 5 | `SBX PY -B -m pytest ... runkit/stage1-78b/tests` (after the edits) | **0: 471 passed** |
| 6 | `PY -B -I SCR/add_specs.py <kit>` (each find text once in its file, ids new) | 0: gated 124, runner 34, scorer 140 |
| 7 | `caffeinate -i SBX PY -B tests/run_mutants_gated_78b.py WS SCR/mr-gated-1 ... <ids 1-31> --timeout 300` (19:34-19:37) | 0: baseline 0; 31 killed |
| 8 | the same, ids 32-62 (19:37-19:42) | 0: 31 killed |
| 9 | the same, ids 94-124 (the 8 new; 19:44-19:50), then ids 63-93 (19:50-19:55) | 0, 0: 31 + 31 killed |
| 10 | `caffeinate -i SBX PY -B tests/run_mutants_runner_78b.py WS SCR/mr-runner ... ALL` (19:42-19:44) | 0: 34 killed |
| 11 | `caffeinate -i SBX PY -B tests/run_mutants_78b.py WS SCR/mr-rules ... ALL` (19:56-19:57) | 0: 109 killed |
| 12 | `caffeinate -i SBX PY -B tests/run_mutants_scorer_78b.py WS SCR/mr-sc-6 ... <ids 121-140>` (19:57-20:03) | **1: 19 killed, 1 survived (K5-H-pack-payload-scan-dropped)**; kept as SCR/mr-sc-6-first.json |
| 13 | test fix (refusal before anything is written); the same chunk again (20:04-20:11) | 0: 20 killed |
| 14 | the scorer runner on ids 1-120 in ten chunks of 12 (20:11-20:30) | all 0: 120 killed |
| 15 | `cp` of hm_runner.py, hm_spec.json, prior_hm_spec.json into SCR/hm/; `shasum` | 0; equal |
| 16 | `caffeinate -i SBX PY -B SCR/hm/hm_runner.py WS SCR/hm-a SCR/hm-a.json K4bcr-R1..R8 --spec SCR/hm/hm_spec.json --timeout 300` (20:30-20:36) | 1 (one survivor): baseline 0; 7 killed, R4 survived |
| 17 | the same, R9..R16 (20:37-20:42) | 0: 8 killed |
| 18 | the same, R17..R23 (20:42-20:47) | 0: 7 killed |
| 19 | the same runner with the prior spec, HM6, HM7, HM13 (20:47-20:50) | 0: 3 killed |
| 19b | `SBX PY -B -m pytest ... runkit/stage1-olmo/tests` (no engine-Y tree in WS) | 1: 752 passed, 8 failed, 2 errors (all need tmp/engine-y-34bfd288) |
| 20 | `cp -Rp` main tmp/engine-y-34bfd288 -> WS/tmp/ (67 MB, git-ignored, not a forbidden folder) | 0 |
| 21 | `git diff --quiet HEAD -- runkit/stage1-olmo`; untracked count; `SBX PY -B -m pytest ... runkit/stage1-olmo/tests` | 0; 0; **0: 762 passed** |
| 22 | the runner runner again, ALL (final, 20:56-20:58) | 0: 34 killed |
| 23 | the whole 7-8B suite again (final, with WS/tmp/ present) | **0: 471 passed** |
| 24 | `rm -rf` of my basetemps and the runners' scratch repos; `find __pycache__` (none); PY -I secret_scan over the kit and SCR | 0; no hit |
| 25 | `shasum -a 256` of the six named files; `git diff --quiet HEAD` over the four unchanged ones | 0; 0 |

Note on M #7, #8 and the first half of #9: after them I changed only the `killed_by` text of nine gated-spec
entries (to the test that measurably kills each), not any find or replace text. Chunk 63-93 ran on the final spec.

## 5. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| D1 closed with a test and a killed mutant | passed | 2 tests; 4 of 4 mutants killed (M #13, #14) |
| D2 (HM6, HM7, HM13) closed with tests and killed mutants | passed | 3 tests; 3 + 3 killed (M #14, #19) |
| D3 S1-S6 adopted, the verifier's hand mutants die | passed | 8 of 8 in the kit spec; 22 of 23 on hm_runner, R4 equivalent (M #14, #16-#18) |
| R1-R3 stronger guard and TLS tests, mutants killed | passed | 8 of 8 (M #9) |
| R4 edits/ scanned, data/ outside and said so, the planting test | passed | pack_setup.py:66 and docstrings, README; 7 of 7 (M #13, #14) |
| R5 the environment test | passed | 2 tests; 3 of 3 (M #10, #22) |
| All four kit runners pass (gated under SBX) | passed | 124, 34, 109, 140 killed; 0 survived, 0 invalid in the final runs |
| Whole 7-8B suite under SBX | passed | 471 passed (M #23) |
| runkit/stage1-olmo unchanged, its suite passes | passed | diff 0 (M #21); 762 passed with the engine-Y fixture copied in (M #20, #21) |
| Hashes returned | passed | section 7 |
| CUDA, a real pod, real scorer scripts | not tested | $0 scope |

## 6. Jobs for the lead

1. Merge by explicit paths: the 10 files in section 1 (all under runkit/stage1-78b/). Then, in the merged checkout
   or a copy: `PYTHONDONTWRITEBYTECODE=1 SBX PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests`
   (expect 471 passed) and the four runners as in M #7-#14 (chunks of about 12 scorer mutants keep each call under
   10 minutes: about 2.5 min per 12). runkit/stage1-olmo's suite needs tmp/engine-y-34bfd288 in the checkout it runs in.
2. Rule concern 1 (a typo in C0_SOURCE is caught on the pod, not on the Mac).
3. After review, delete WS/tmp/engine-y-34bfd288 (67 MB, my fixture copy) and SCR (results, logs, ids, the copies
   in SCR/before and SCR/hm; small).

## 7. Final SHA-256 (M #25)

| File | SHA-256 | vs HEAD |
|---|---|---|
| rules_78b.py | 68bf8f45998c84d7ef99a3c7c43bc67f52b498003e69e8e1130c2b2b8970a25c | unchanged |
| plan_tool.py | 592b016fdd06c25b8c7fdcad1e440b7c046d0e00b552f41afd7f583d6ac1b5a1 | unchanged |
| setup/job_runner_stage1.py | 36a786320ad8eb9950d25ecd7c530d4cd89094f866301b970588d457d490941b | changed (D1) |
| pack_setup.py | 40b99b1a28093138413da385da95685c4af0b9603ea24e701f7384c266c5d20e | changed (R4) |
| stage1_rules.py | cd88e30fc5ea4d36357c54c6f9f3111e9a01f38d58e1e1d2d0c57151ab108312 | unchanged |
| backup_records_stage1.py | a2b66eb8ccbb6191ee423803ad2f65c8f6b9eab187ca562515c9923b0f361bff | unchanged |

## 8. Unresolved concerns

1. D1 is checked on the pod, as at 1B. A typo in C0_SOURCE's e1_fingerprint is planned by init-block and refused
   only when the c0 pod starts (no step runs, so B17 gives no false alarm, but the pod start is paid). A Mac-side
   check at pack time (compare the packed source file's e1 fingerprint with C0_SOURCE) would catch it earlier. I did
   not add it: the brief names the runner. The lead's call.
2. R4's data/ exemption rests on the lead's ruling that the manifest SHA-256 pins every byte. I did not open the
   prepared set or its manifest to check that the manifest lists every file's hash (I). The pack checks the
   manifest.sha256 text against PREPARED_MANIFESTS (R: pack_setup.py prepared_set) and the pod checks
   manifest.json's own hash (R: setup/job_runner_stage1.py preflight_checks).
3. R3's fake opener skips the response processors (HTTPErrorProcessor and the redirect handler's 30x path). The
   redirect handler's header drop is tested separately by the existing D5 tests. A mutant that leaks the token only
   on a redirect response would rely on those tests (I).
4. The runner's last call, `extend_cap.py` (R: setup/job_runner_stage1.py main, the final `subprocess.run` with no
   `env=`), inherits os.environ. On a pod, os.environ holds no token after the pre-job check (it refuses one), so
   nothing leaks today. R5 covers the job steps and verifies only, as asked.
5. K4bcr-R4 survives on the whole suite; the core re-verifier records it as equivalent in effect. I did not re-derive
   that.
