# K5 kit re-verify (round 5): K4bcr-D1..D3, K4bsec R1..R5 (core and security together)

Started 2026-11-06 21:02 UTC; resumed 2026-11-07 10:16 UTC after a break in the earlier session; this version
10:58 UTC (`date -u` read right before each write). Status: **DONE**.

**Verdict: VERIFIED_WITH_MINOR.** Every item the fixer was given is closed for the mutants named in the brief: my
own re-runs of the four kit runners kill 124 + 34 + 109 + 140 of 407 mutants, and the suites pass (471 and 762).
But my own hand mutants find 7 new survivors (6 test-strength gaps and 1 equivalent in effect), and the tests leave
token-shaped strings in files that stay after the run: 7 files, 2 of them from this round's R4 test. All are minor.
None is a live leak or a wrong result today. The most important one is V5 (R3): a redirect handler edit that sends
the Bearer token to the CDN host survives the whole suite.

- WS = scratchpad/b78/ws-k3 (read-only for me; HEAD e5a2f86 plus the fixer's 10 modified files).
- SCR = scratchpad/b78/reports/k5-verify-scratch/. SCR/repo = a byte copy of WS (all my runs used it).
- PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (huggingface_hub 0.36.2,
  Python 3.11.15). PY2 = /Users/spiderishi/Coding/attribution/.venv/bin/python (scans and JSON reads only).
- SBX = `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'`. Every pytest run,
  every hand mutant and every runner below ran under SBX with PYTHONDONTWRITEBYTECODE=1, `-B`, `-p no:cacheprovider`.
- Tags: M measured (command number in section 4), R read (path:line), E estimate, I inference.
- No pod, spend, network, install, download, agent or message. No git state changed (git used only as
  `git --no-optional-locks status/diff/ls-files/rev-parse`). Nothing written in WS or the main checkout. No forbidden
  folder, selector, hidden, judge, answer, generation, sample or prompt-text file opened. The real edit files and the
  two prepared-folder files were read only by the kit's own secret scan, with counts and pattern names printed (M #25,
  #26). Every token-shaped value in my tests is built at test time; no file of mine holds one (M #31).

## 0. State check (M)
- M #1, #2: WS's hash list (9,775 files) at resume equals the list at the start; SCR/repo equals WS. After both suites
  ran in SCR/repo, its hash list was still equal (M #22): the suites write nothing into the tree.
- M #3: the six SHA-256 values the fixer returned match. rules_78b.py, plan_tool.py, stage1_rules.py,
  backup_records_stage1.py, tests/conftest.py, launch.py and secret_scan.py equal HEAD. runkit/stage1-olmo: diff 0,
  0 untracked files.

## 1. Files changed
- None in WS or the main checkout. Mine (SCR only, not for merge as is):
  - SCR/k5v_tests/test_k5v_survivors.py: 5 ready tests (V1-V5, 9 cases) that kill my 6 test-gap survivors.
  - SCR/test_k5v_scratch.py: P1, the data/ premise probe.
  - SCR/hm_spec.json (25 hand mutants), SCR/hm_spec2.json (1), SCR/hm_runner.py (the core re-verifier's runner, byte
    for byte, SHA-256 dfa4cbfb...), SCR/tools2/one_mutant2.py, SCR/tools2/scan_edits.py, SCR/scan_left.py.
  - Results: SCR/hm-a.json ... hm-f.json, SCR/runs/mr-*.json.

## 2. Items: what I checked and the evidence

Hand mutants: my spec SCR/hm_spec.json (SHA-256 445702d3...) and hm_spec2.json, each run on the WHOLE 7-8B suite by
hm_runner.py (killed = pytest exit 1 with a FAILED line and no ERROR line).

| Item | My hand mutants (whole suite, SBX) | Result |
|---|---|---|
| D1 c0 fingerprint | D1a reads q's fingerprint; D1b falls back to the plan's value on a refusal; D1c accepts a link | 2 killed; **D1c survived** |
| D2 HM6/HM7/HM13 | HM6 walk follows folder links; HM7 family check only on Y; HM13 O-ext kinds exempt | 3 killed |
| D3 S1-S6 | R8 seed pins swapped; R13 a1_pass pin dropped; R17 backup skips a1_pass; R6; R7; R9 any LS reason; R21 variant (no e1 checkpoint at all) | 6 killed; **R21 variant survived** |
| R1 wrapper | skips IPv6 datagrams; skips sockets with an explicit (nonzero) proto | 1 killed; **explicit proto survived** |
| R2 hook threads | frees default-named threads ("Thread-N"); frees _DummyThread (a `_thread` thread) | **both survived** |
| R3 TLS / redirect | https_request moves the host; http_error_30x calls the PARENT's redirect_request | 1 killed; **redirect survived** |
| R4 pack scan | scan reads the head only; bundle scan after the first write; refusal quotes the match; the call site skips edits/ | 3 killed; **call-site survived** |
| R5 env | job env drops HF_TOKEN only; run_job's verify gets os.environ; the O-ext step gets HF_HUB_OFFLINE=0 | **3 killed**, each by an R5 test |

Totals: 26 hand mutants, 19 killed, 7 survived. One run (hm-c) first showed the default-named-thread mutant as
"killed"; the failing test was the flaky free-space test (concern 3), and hm-e's re-run shows it survives (M #8).

### K4bcr-D1 (c0's fingerprint from the packed source unit). Closed. One low-effect survivor.
- R: setup/job_runner_stage1.py:514-541 re-hashes the packed source COMPLETE.json against its plan pin, reads only
  checkpoints.e1.adapter_fingerprint, refuses a missing / off-pin / link / no-e1 / different value, and the lean
  command takes the value read (:619, :625). This is the 1B form. The kit runner kills K5-c0-fp-from-plan, -no-compare,
  -no-rehash, -no-e1-check (M #13-#15).
- K5v-D1c (a link with pinned bytes is accepted) survives (M #5). Effect is low: the bytes are still re-hashed (I).
  The D1 test covers three refusals; the link refusal is untested (R: tests/test_scorer_block_78b.py:1728-1748).
  Ready test: V1 (kills it, M #29).
- Not in this round's scope: the lead's design ruling Item 23 (recorded 2026-11-07T10:14 UTC, after the fix; R:
  lead-rulings-part2-design-20261106.md:111) asks for a Mac-side check at pack time. It is not built in WS (R: the
  fixer's concern 1). It is a build item for a later round.

### K4bcr-D2 (HM6, HM7, HM13). Closed.
- My three variants die in the three new tests (M #5). The kit runner kills K5-HM6/7/13 (M #13-#15).

### K4bcr-D3 (S1-S6 adopted). Closed. One low-effect survivor.
- The kit runner kills K4bcr-R1, R6, R7, R8, R9, R13, R17, R21, each in the S test meant for it (M #13-#15).
- My R21 variant (the e1 check runs only when the side lists an "e1" key) survives (M #6). S3a deletes only the
  fingerprint, not the whole e1 checkpoint (R: tests/test_scorer_block_78b.py:1933-1939). Effect is low: the side
  units are fixed by their pins and the engine writes e1 (I). Ready test: V2 (M #29).
- K4bcr-R4 (the fixer's concern 5): my reading agrees it is equivalent in effect. With no unit and a complete_sha256,
  record-done's later `tree / r["unit"]` (R: plan_tool.py:4391) raises or fails (I).

### R1 (wrapper on stream and datagram). Closed for the named mutant. One survivor (low realism).
- The stand-in has type and proto, every case runs on stream and datagram, and three real numeric datagram probes must
  name the wrapper (R: tests/test_pp10_process_wide.py:291-333). K5-H-d1-wrapper-skips-dgram dies (M #11, #12).
- K5v-G1-explicit-proto survives (M #7): every probe uses proto 0 (R: :296; `_socket_call` :76-78). With the mutant,
  `socket.socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP).sendto(b"x", ("name.example", 53))` would resolve the name before
  the hook refuses (I, from the security re-verifier's R1 reasoning). Ready test: V3 (real numeric probes with an
  explicit protocol at collection and in a module fixture; M #29).

### R2 (hook in other threads). Closed for the named mutants. Two survivors (low realism).
- K5-H-d2-hook-daemon-threads-free and -executor-threads-free die (M #11, #12).
- Both of my thread mutants survive (M #7, #8). The fixer's report says the probes run "(default names)"; the daemon
  probe is named "pp10-k4b-probe" (R: tests/test_pp10_process_wide.py:359); only the executor worker has a default
  name. No probe runs in a "Thread-N" thread or a `_thread` thread. Ready test: V4 (M #29).

### R3 (TLS and the dispatch). Closed for the named mutants. One survivor: the token goes to the CDN.
- The fake opener runs request processors and `opener._open` with recording connection classes (R:
  tests/test_gated_78b.py:984-1053). All five D3 mutants die (M #11, #12).
- K5v-G3-redirect-keeps-token survives the whole suite (M #6 earlier session, hm-d). It adds an `http_error_302`
  (and 301/303/307/308) that calls the parent's `redirect_request`, so the subclass's header drop is skipped on a real
  redirect. The redirect tests call `handler.redirect_request` directly (R: tests/test_gated_78b.py:233-243,
  :1148-1160), and the R3 fake opener skips the response processors (R: :1043-1048), so no test drives a 30x through
  the dispatch. M #30: with V5's whole dispatch (response processors too), the Authorization header reaches
  `cdn-lfs.example.net` under the mutant ("At index 1 diff: ('cdn-lfs.example.net', True)"). This confirms the
  fixer's concern 3 with a concrete survivor. The shipped class is correct (V5 passes on WS, M #28). Ready test: V5
  (5 codes; kills it in all 5, M #29).

### R4 (the pack's scan). Closed for the named mutants. One survivor; the data/ premise is not exact.
- R: pack_setup.py:66 `DATA_PREFIXES = ("data/", "inputs/")`; the bundle call passes it (:512); docstrings and the
  README say data/ stays outside. The kit runner kills the 7 pack mutants (M #13-#15).
- M #25: the real R_d1-R_d3 edit files of both families (3 + 3, at their sealed pins) hold no secret pattern, so the
  new edits/ scan does not block the real pack.
- K5v-R4-call-site-skips-edits survives (M #9): the R4 test checks edits/ only through a direct `refuse_secrets` call
  with `pack.DATA_PREFIXES` (R: tests/test_scorer_block_78b.py:2062-2068), not through the real pack. Low realism.
  Fix: a spy on `refuse_secrets` in a real pack that asserts the bundle call skips only data/ and inputs/ and gets the
  edits/ files.
- **The data/ premise ("its manifest SHA-256 pins every byte") is not exact.** R: the engine writes
  prepare_receipt.json "outside the manifest hash" (experiments/safety_selection/prepare.py:71, :872-873); the pack
  ships EVERY file of the prepared folder (pack_setup.py:475-477) and checks only manifest.sha256's text on the Mac
  (:215-219). M #26: both real 7-8B folders (prepared-kt-dolly-olmo2, -llama3) hold prepare_receipt.json (3,521 bytes)
  and a .DS_Store (6,148 bytes); manifest.json names neither. Neither holds a secret pattern today (pattern names
  only). M #32: P1 plants a token-shaped string (built at test time) in both files of the synthetic folder; the pack
  goes through and ships both in data/ unscanned. Effect is low: the receipt holds python, platform, code identity,
  time and local input paths, no environment (R: experiments/safety_selection/__main__.py:183-184). Fix (lead's call):
  scan the data/ files the manifest does not list (or skip .DS_Store and scan the receipt), or correct the README and
  docstring to "the manifest pins the files it lists".

### R5 (the steps' environment). Closed.
- R: tests/test_kit_78b_runner.py (two K5 R5 tests). My three mutants die, each in an R5 test (M #8). The kit runner
  kills the three H-tok mutants (M #12).

### Token-shaped strings in files the tests leave behind. Failed (minor).
- M #21, #23: the 7-8B suite's basetemp (26,074 files, 4,993 tar members) holds **7 files** with an hf_token-shaped
  string after the run. **2 are this round's**: test_k5_r4's `tmp/k5-r4/edit.json` and `tmp/k5-r4/rows.jsonl` are
  written with the fake and never removed (R: tests/test_scorer_block_78b.py:2062-2064). 5 are older: 3 from round
  4b's inputs test (`tmp/lists/anchor_prompts.json`, `tmp/w/adapter.safetensors`, `tmp/w/x.json`) and 2 from the D4
  preflight test's stored login (`shell-login/token`, `shell-login/huggingface/token`). Without `--basetemp`, pytest
  keeps them under the system temp folder for the last three runs (I). The 1B suite's basetemp: 0 (M #20).
- The fixer's "no hit" scan (k5-fix.md M #24) covered the kit and its own scratch after it deleted its basetemps, not
  the files the tests leave (R: k5-fix.md:159). My rescan of the fixer's scratch: 0 hits (M #24).
- Fix: in test_k5_r4, unlink edit.json and rows.jsonl in a `finally`; do the same in the older tests, or build the
  fake so it is not token-shaped on disk.

## 3. Results in short

| Run | Result |
|---|---|
| Whole 7-8B suite, SBX | **471 passed** (M #4 earlier; M #21 now) |
| runkit/stage1-olmo suite, SBX (engine-Y fixture in the copy) | **762 passed** (M #20) |
| Rules runner, ALL | 109 of 109 killed (M #10) |
| Runner runner, ALL | 34 of 34 killed (M #11) |
| Gated runner, 2 chunks (1-31, 32-124), final spec | 124 of 124 killed (M #12) |
| Scorer runner, 3 chunks (1-30, 31-90, 91-140) | 140 of 140 killed (M #13-#15) |
| My hand mutants (26, whole suite) | 19 killed, 7 survived (M #5-#9) |
| My ready tests V1-V5 | 9 passed on WS; each kills its survivor; whole suite + V1-V5: 480 passed (M #28-#30) |
| Left-behind token-shaped strings | 7 files (2 this round) in the 7-8B basetemp; 0 in the 1B one (M #20, #23) |

## 4. Commands (all in the foreground, each under 10 minutes; exit status)

Earlier session (2026-11-06 21:02 to 2026-11-07 04:40 UTC; the records are in SCR):

| # | Command (abbreviated; cwd SCR) | Exit / result |
|---|---|---|
| 1 | `cp` of WS to SCR/repo; `find ... | shasum -a 256` of both (ws-sha-start.txt, repo-sha-start.txt) | 0; equal, 9,775 files |
| 2 | reads: k5-fix.md, both re-verify reports, rulings (grep), the kit's diff and tests | 0 |
| 3 | `shasum -a 256` of the six named files | 0; equal to the fixer's |
| 4 | `SBX PY -B -m pytest ... --basetemp SCR/bt-base runkit/stage1-78b/tests` (cwd SCR/repo) | 0: 471 passed |
| 5 | `caffeinate -i SBX PY -B SCR/hm_runner.py SCR/repo SCR/hm-a SCR/hm-a.json <6 ids> --spec SCR/hm_spec.json --timeout 300` (21:16-21:21) | 1: 5 killed, 1 survived |
| 6 | the same, hm-b (7 ids, 21:21-21:26); hm-d (5 ids, 00:00-04:39; the long span is a stalled machine, I: each run is under 50 s) | 1, 1: 6 + 1; 4 + 1 |
| 7 | the same, hm-c (4 ids, 21:26-21:30) | 1: 2 "killed" (one a flake, see #8), 2 survived |
| 8a | `PYTHONHASHSEED` sweep of the free-space test's folder names (1,500 seeds) | 0: 4 seeds collide (superseded by this session's #33) |

This session (2026-11-07):

| # | Command (abbreviated) | Exit / result |
|---|---|---|
| 1 | `date -u`; hash list of WS now vs start | 0; equal |
| 2 | hash list of SCR/repo vs WS | 0; equal |
| 3 | `shasum -a 256` (six files); `git diff --quiet HEAD` (7 unchanged files; runkit/stage1-olmo); `git ls-files --others` | 0; equal; 0; 0; 0 |
| 8 | `caffeinate -i SBX PY -B SCR/hm_runner.py SCR/repo SCR/hm-e SCR/hm-e.json <3 R5 ids + the thread-name id> --spec SCR/hm_spec.json --timeout 300` (10:16-10:18) | 1: 3 killed, 1 survived; baseline 471 passed |
| 9 | the same with SCR/hm_spec2.json, hm-f, the call-site id (10:52-10:53) | 1: 1 survived |
| 10 | `caffeinate -i SBX PY -B SCR/repo/runkit/stage1-78b/tests/run_mutants_78b.py SCR/repo SCR/runs/mr-rules ... ALL --timeout 300` (10:20-10:21) | 0: 109 killed |
| 11 | the same, run_mutants_runner_78b.py, ALL (10:21-10:22) | 0: 34 killed |
| 12 | the same, run_mutants_gated_78b.py, ids 1-31 (10:22-10:23), then 32-124 (10:23-10:31) | 0, 0: 31 + 93 killed |
| 13-15 | the same, run_mutants_scorer_78b.py, ids 1-30 (10:31-10:32), 31-90 (10:32-10:36), 91-140 (10:36-10:43) | 0, 0, 0: 30 + 60 + 50 killed |
| 16 | PY2 -B -I: each new K5/K4bcr/H- mutant's killing test vs its item | 0; all match |
| 20 | `SBX PY -B -m pytest ... --basetemp SCR/bt-olmo runkit/stage1-olmo/tests` (cwd SCR/repo) | **0: 762 passed** |
| 21 | `SBX PY -B -m pytest ... --basetemp SCR/bt-78b-2 runkit/stage1-78b/tests` | **0: 471 passed** |
| 22 | hash list of SCR/repo after both suites | 0; equal |
| 23 | `PY2 -B -I SCR/scan_left.py SCR/bt-78b-2 <kit secret_scan.py>` and the same on SCR/bt-olmo | 0: 7 hits (hf_token); 0 hits |
| 24 | the same on SCR/runs and reports/k5-fix-scratch; on WS/runkit/stage1-78b | 0: 0, 0, 0 hits |
| 25 | `PY -B -I SCR/tools2/scan_edits.py SCR/repo` (the pack's scan on the real R_d edit files; counts only) | 0: 3 + 3 files at pin, 0 hits |
| 26 | `ls` of tmp/kt-prepared/* (top level); two names searched in each manifest.json (booleans); the kit's scan of prepare_receipt.json and .DS_Store (pattern names only) | 0: both unlisted in all four; 0 hits |
| 27 | `PYTHONHASHSEED=54 SBX PY -B -m pytest ... test_kit_78b_runner.py -k free_space_check_refuses` | 1: FileExistsError (the flake reproduced) |
| 28 | `SBX PY -B SCR/tools2/one_mutant2.py SCR/repo SCR/om-none SCR/hm_spec.json NONE --add V-file -- <V-file>` | first 1 (my V3 ran inside a test, where the per-test guard refuses first; moved to a module fixture), then **0: 9 passed** |
| 29 | the same under each of the 6 test-gap survivors | 1 each: only its V test fails (V5: all 5 codes) |
| 30 | the same, V5 [302] under K5v-G3 with fuller output (lines with `hf_` filtered out); whole suite + V file, NONE | 1: the CDN gets the header; **0: 480 passed** |
| 31 | `rm -rf` of my basetemps and runner copies; rescan of SCR | 0; 0 hf_token hits (4 ssh_public_key hits are committed repo files in the copy) |
| 32 | the same runner, NONE, `--add SCR/test_k5v_scratch.py` (P1) | 0: 1 passed (the planted data/ files ship) |
| 33 | `PYTHONHASHSEED=s PY -B -I -S -c ...` for s in 0..1499 (the three folder names of the free-space test) | 0: 5 seeds collide |

## 5. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| K4bcr-D1 by my own hand mutants | passed; 1 low-effect survivor (link) | M #5, #13-#15, #29 |
| K4bcr-D2 by my own hand mutants | passed | M #5 |
| K4bcr-D3 by my own hand mutants | passed; 1 low-effect survivor (R21 variant) | M #6, #13-#15, #29 |
| R1 by my own hand mutants, sandboxed | passed for the named mutant; **1 survivor** (explicit proto) | M #7, #12, #29 |
| R2 by my own hand mutants, sandboxed | passed for the named mutants; **2 survivors** (thread kinds) | M #7, #8, #12, #29 |
| R3 by my own hand mutants, sandboxed | passed for the named mutants; **1 survivor** (redirect leak to the CDN) | M #6, #12, #29, #30 |
| R4 by my own hand mutants | passed for the named mutants; **1 survivor** (call site); data/ premise not exact | M #6, #9, #13-#15, #25, #26, #32 |
| R5 by my own hand mutants | passed (3 of 3) | M #8, #11 |
| All four kit runners re-run (gated under SBX) | passed: 124, 34, 109, 140 killed; 0 survived, 0 invalid | M #10-#15 |
| Whole 7-8B suite under SBX | passed: 471 | M #21 |
| runkit/stage1-olmo unchanged, its suite passes | passed: diff 0; 762 | M #3, #20 |
| No file the tests leave behind holds a token-shaped string | **failed (minor)**: 7 files; 2 from this round's R4 test | M #23 |
| No real network or outside process from the tests | passed under SBX (no failure; I did not read the sandbox log) | all runs |
| CUDA, a real pod, real scorer scripts | not tested | $0 scope |

## 6. Jobs for the lead

1. Merge the fixer's 10 files by explicit paths (its list). Then in the merged checkout or a copy:
   `PYTHONDONTWRITEBYTECODE=1 SBX PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests` (expect 471) and the
   four runners: `caffeinate -i SBX PY -B runkit/stage1-78b/tests/run_mutants_<k>.py <repo> <new scratch> OUT.json
   <ids> --timeout 300` with rules ALL, runner ALL, gated in 2 chunks (1-31, 32-124: 1.3 and 7.7 min here), scorer in
   3 chunks (1-30, 31-90, 91-140: 0.7, 4.2, 6.1 min here). On a busier machine use smaller chunks to stay under 10 min.
2. Rule the minor items, best in one small round before the scorer pods:
   (a) V5 (R3): adopt SCR/k5v_tests/test_k5v_survivors.py's V5 (a 30x through the whole dispatch, the token never
       reaches the CDN) and add K5v-G3-redirect-keeps-token to mutation_spec_gated_78b.json.
   (b) V3, V4 (R1, R2) and V1, V2 (D1, D3): adopt the four tests and their mutants, or record them as limits.
   (c) R4: the data/ premise (prepare_receipt.json and stray files are unlisted and unscanned); pick a fix (section 2).
       Also pin the bundle call site (a spy), so K5v-R4-call-site-skips-edits dies.
   (d) Remove the token-shaped files the tests leave (test_k5_r4's two; the older five).
   (e) The flaky test (concern 3): name the three folders by index, not by `hash(repr(free)) % 1000`.
3. Item 23 of the design rulings (the Mac-side C0_SOURCE check at pack time) is not built yet; it is a build item.
4. After review, delete SCR (189 MB; SCR/repo is most of it) and, per the fixer, WS/tmp/engine-y-34bfd288 and
   reports/k5-fix-scratch/.

## 7. Unresolved concerns

1. My earlier session's last hand-mutant batch (hm-d) spans 00:00-04:39 UTC for 5 mutants of about 50 s each. I read
   this as the machine stalling (I); every run in it has its own complete pytest result and a restored hash.
2. I did not read the macOS sandbox log for my runs. SBX denies outbound IP, so a weakened guard fails closed; the
   explicit-proto and redirect probes in my tests reach no socket (recorders, numeric addresses after the hook
   refuses the same event by hand).
3. A pre-existing flaky test: test_kit_78b_runner.py:491 names three folders `w-{abs(hash(repr(free))) % 1000}`; two
   collide at some hash seeds (M #33: 5 of 1,500 seeds, about 0.3 % of runs; M #27: reproduced at seed 54). A
   collision makes any mutant run read as "killed" by an unrelated test (it did once here). The runners' baselines
   would also stop at it.
4. The survivors in R1-R3 (and the R4 call site) are deliberate-looking edits, as in round 4b. Their value is as
   regression guards. V5's survivor has the highest consequence (the token to a third-party host).
5. K4bcr-R4: I agree it is equivalent in effect (section 2, D3) but did not run a test for it.
6. The fixer's concern 4 (extend_cap.py inherits os.environ) stands: no token can be there after the pre-job check
   (R: the fixer's report; not re-run by me).
