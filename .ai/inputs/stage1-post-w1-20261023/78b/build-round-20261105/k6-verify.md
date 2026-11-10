# K6 kit re-verify (round 6): K5v-1..K5v-9, the data/ scan ruling, the C0_SOURCE pack check

Started 2026-11-07 12:36 UTC. This version 13:36 UTC (`date -u` read right before each write). Status: **DONE**.

**Verdict: VERIFIED_WITH_MINOR.** Every item the fixer was given is closed. My re-runs of the four kit runners kill
all 427 mutants (109 + 35 + 128 + 155; 0 survived, 0 invalid). The suites pass (487 and 762). No token-shaped file is
left in either basetemp, in the worktree or in my scratch. The 7 K5v survivors now die in the whole suite, each in its
own V test. The cleanup works when a test fails midway (7 forced failures, all clean; 2 controls without the finalizer
leak, so the check can see a leak). But my own hand mutants find **3 new test-gap survivors** (one in the data/ scan,
two in the guard) and 1 low one (message prefixes). Item 23 has one residual path: a C0_SOURCE edit made AFTER a clean
pack still reaches a pod. The fixer's seed evidence for K5v-9 is wrong (`-I` ignores PYTHONHASHSEED); the fix itself
is right. All findings are minor. None is a live leak or a wrong result today.

- WS = scratchpad/b78/ws-k4 (read-only for me; HEAD 197ea375 plus the fixer's 9 modified files).
- SCR = scratchpad/b78/reports/k6-verify-scratch/. SCR/repo was a byte copy of WS (all my runs used it or a copy of
  it); deleted at the end (M #24).
- PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (3.11.15).
  PY2 = /Users/spiderishi/Coding/attribution/.venv/bin/python (3.11.15; scans and JSON reads, always -B -I).
- SBX = `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'`. Every pytest run,
  every hand mutant and every runner chunk ran under SBX, with PYTHONDONTWRITEBYTECODE=1, `-B`, `-p no:cacheprovider`
  and a `--basetemp` in SCR.
- Tags: M measured (command number in section 4), R read (path:line), E estimate, I inference.
- No pod, spend, network, install, download, agent or message. No git state changed (git used only as
  `git --no-optional-locks status/diff/rev-parse/ls-files/check-ignore/show`). Nothing written in WS or the main
  checkout (M #1, #23). No forbidden folder, selector, hidden, judge, answer, generation, sample or prompt-text file
  opened. In the two real prepared folders I listed file names, read manifest.json's "files" map (key and value forms
  only) and its SHA-256, and ran the kit's scan on the 3 unlisted files (pattern names only) (M #19). Every
  token-shaped value in my tests is built at test time; every file that held one is deleted (M #15, #18, #24).

## 0. State check
- M #1: the 9 SHA-256 values the fixer returned match WS. WS HEAD 197ea375. `git status` lists only those 9 files
  (plus the ignored tmp/). runkit/stage1-olmo: no diff. At the end, WS's hash list (9,872 entries) equals the start
  list (M #23).
- M #2: SCR/repo's hash list equals WS's. After both suites ran in it, it is still equal (M #6, #23): the suites write
  nothing into the tree.
- M #22: specs against HEAD: scorer 140 -> 155 (+15), gated 124 -> 128 (+4), runner 34 -> 35 (+1), rules 109 (no
  change). No entry removed; old order kept; only K5-H-pack-engine-files-unscanned and K5-H-pack-scripts-unscanned
  changed (find/replace moved to the new `scanned = ...` line; intent unchanged).

## 1. Files changed
- None in WS or the main checkout. Mine, all in SCR (not for merge as is):
  - SCR/tools/test_k6v_ready.py: 3 ready tests (T1 x3 cases, T2, T3) that kill my 3 test-gap survivors.
  - SCR/hm_spec.json (14 hand mutants, SHA-256 74a2d349...), SCR/hm_spec_k5v.json (the 7 K5v mutants copied from the
    kit specs), SCR/tools/make_hm_spec.py, SCR/tools/hm_runner.py (k5-verify's whole-suite runner, byte for byte,
    SHA-256 dfa4cbfb...), SCR/tools/forced_fail.py, forced_fail_control.py, one_mutant_ready.py, chunk.sh,
    scan_left_v.py, real_prepared_probe.py.
  - Results: SCR/hm-a.json, hm-b.json, hm-k5v.json, SCR/ff/forced-fail.json, SCR/runs/*.json (9 runner chunks),
    SCR/collide-py311-noI.txt, SCR/head-specs/, hash lists.

## 2. Items: what I checked and the evidence

My hand mutants ran on the WHOLE 7-8B suite through hm_runner.py (killed = pytest exit 1 with a FAILED line and no
ERROR line), under SBX.

| Item | My hand mutants (whole suite, SBX) | Result |
|---|---|---|
| K5v-3 data/ scan | unlisted binary-suffix file unscanned; metadata by last part only; a link in the set packed; top level only; scan_anyway without the bundle prefix; prepare_receipt.json exempt; unlisted sub-folder file unscanned | 5 killed; **binary survived**; link survived (equivalent, see below) |
| Item 23 c0 | dry run drops the c0 input; no re-hash; any-checkpoint fallback; refusal quotes 12-char prefixes | 2 killed; no-rehash survived (equivalent, the fixer's concern 5); **prefixes survived** (low) |
| V3 (K5v-G1) | wrapper frees AF_INET6 STREAM sockets with an explicit protocol | **survived** |
| V4 (K5v-G2) | hook frees NON-daemon default-named threads | **survived** |
| V5 (K5v-G3) | same_origin ignores the port | killed |
| The 7 K5v survivors (kit spec text) | D1c, R21, R4 call site, G1, G2 x2, G3 | **7 killed**, each by its V test or the spy |

### K5v survivors V1-V5 and K5v-D1c (the fixer's "K5v-1, 4, 5, 7, 8"). Closed.
- The K5v numbering is not in any file I can read (k5-verify.md does not number them; the brief's ids map by content,
  R: k6-fix.md:40-42). I checked the 9 content items the fixer mapped.
- R: the five tests are k5-verify's V1-V5 (R: k5-verify-scratch/k5v_tests/test_k5v_survivors.py) with names
  prefixed test_k6_ and two extra count asserts (V3, V4); the logic is the same (R: test_scorer_block_78b.py:2090-2113,
  test_pp10_process_wide.py:433-499, test_gated_78b.py:1524-1627).
- M #16: the 7 K5v mutants in the kit specs equal k5-verify's originals byte for byte, except K5v-R4-call-site, whose
  find follows the new two-line call (same intent). On the whole suite all 7 die, each in its intended test.
- M #20, #21: in the kit runners, all 7 die in their intended tests too.

### K5v-2 (token-shaped files left behind). Closed, for pass and fail.
- M #3, #4: whole suite, then a scan of its basetemp (kit patterns plus a broader `hf_` + 30 letters/digits shape):
  27,273 files, 5,365 tar members, **0 hits** (the fixer's counts exactly). 1B basetemp: 66,700 files, 0 hits (M #6).
- M #14: **fail midway**. I forced a failure (`assert False`) at 7 points where a fake is on disk: the inputs test's
  end; test_k5_r4 while the scorer script holds the fake, while extend_cap.py holds it, and at its end; the K6
  planted test after its first write and at its end; the preflight right after the stored login is written. Each run:
  exit 1 with exactly the forced FAILED line; basetemp **0 hits** each time.
- M #15: **control**: the same forced failure with the finalizer line removed leaves 1 file (K6 test:
  prepare_receipt.json) and 2 files (test_k5_r4: edit.json, rows.jsonl). So the check can see a leak. Both control
  basetemps deleted at once.
- M #5: the worktree: 9,871 files, 4 ssh_public_key hits, all in 2 committed, unchanged files and their copies in the
  ignored engine-Y fixture (public keys, pre-existing; k5-verify saw the same 4). No hf/runpod/github token shape.

### K5v-6 (the call-site spy). Closed.
- M #16: K5v-R4-call-site-skips-edits dies in test_k6_k5v6 on the whole suite. M #12: my K6v-scan-anyway-bare-names
  (the call passes names without the bundle prefix) dies in the K6 planted test.

### K5v-9 (the flaky folder names). Closed. The fixer's seed evidence is wrong; the fix is right.
- M #7: `PYTHONHASHSEED=54 PY -I -c 'print(hash("None"))'` prints a different value on each run; without `-I` it is
  stable. `-I` implies `-E`, so Python ignores PYTHONHASHSEED. Both earlier sweeps used `-I` (R: k6-fix.md:192;
  k5-verify.md:201), so their seed lists (fixer: 868, 1027; k5-verify: 5 seeds) are random draws. My own `-I` sweep
  gave a third list (188, 459, 474, 774, 977, 987). This answers the fixer's concern 4.
- M #8: the sweep without `-I` (seeds 0-1499): the old names collide at exactly 4 seeds: 54, 289, 772, 1289.
- M #9: the HEAD test (old names) fails with FileExistsError at all 4 and passes at 0, 188, 459, **868 and 1027**.
  So k6-fix.md M #8's "seeds 868 and 1027 give a collision" is false; only seed 54 of its three checks was a real one.
- M #10: the fixed test passes at all 4 colliding seeds. R: test_kit_78b_runner.py:490 names the worlds `w-{i}`; no
  other builtin `hash()` is used in either kit's tests (M #10b).

### K5v-3, the lead's data/ scan ruling. Closed, with one test gap.
- The ruling text is not in a file I can read; I checked against the fixer's quoted parts and k5-verify's suggested
  fix (R: k6-fix.md:98-104; k5-verify.md:125-127).
- R: pack_setup.py:237-273 (`macos_metadata`, `prepared_files`), :314 (`scan_anyway`), :553-557 and :592-593 (main).
  The code does what the README (R: README.md:104-115) and the docstring (R: pack_setup.py:24-34) say.
- M #19, the real sets (kit's own `macos_metadata` code, names only): each folder 12 files, 0 links, a "files" map of
  8 entries, all present, all in sub-folders, all values 64-hex (so `pinned(v)` holds; the fixer did not check the
  value form); manifest.json at the kit pin and at manifest.sha256; unlisted: .DS_Store (skipped) and manifest.json,
  manifest.sha256, prepare_receipt.json (scanned), **0 hits**. R: the engine writes `files` as {name: sha256 hex} over
  every file but the manifest pair and the receipt (experiments/safety_selection/prepare.py:813, :823-825, :872-873).
  So reading (b) equals the literal rule on both real sets.
- **Survivor K6v-unlisted-binary-unscanned** (M #12): an unlisted data/ file with a binary suffix (.npy, .gz,
  .safetensors, ...) packed but not scanned passes the whole suite; the tests plant only text files. Under it, the
  fake shipped inside the bundle (M #18: 3 bundle members, one per case; deleted). The shipped code scans such a file
  (T1 passes on WS, M #17). Fix: adopt T1 and add the mutant to the scorer spec.
- K6v-prepared-link-packed survives (M #12) but is equivalent in safety: `Packing.add` refuses a link (R:
  pack_setup.py:119), so the mutant turns a silent skip into a pack refusal. Not a defect.
- Readings (a) and (b) (the fixer's concern 1): I agree with both. (a) Not packing a metadata file avoids shipping an
  unscanned, unpinned file, and nothing on the pod reads it (I). (b) only scans more than the literal rule, never less.

### Item 23, the Mac-side C0_SOURCE check. Closed for typos present at pack time; one residual path.
- R: pack_setup.py:396-417 and :464-465. It runs in sc_inputs, so in the real pack and the dry run (sc_report, :495),
  before `setup/packed-stage1-X/` exists. It reads only checkpoints.e1.adapter_fingerprint and compares with
  C0_SOURCE[family]["e1_fingerprint"]; the same form as the pod (R: setup/job_runner_stage1.py:517-541). C0_SOURCE is
  validated as two 64-hex values before it reaches the check (R: rules_78b.py:1290-1293), so a null e1_fingerprint
  cannot reach it.
- M #13: my K6v-c0-dry-run-drops-c0 dies in the item-23 test's dry-run pass; K6v-c0-any-checkpoint-fallback dies in
  its no-e1 case. M #20, #21: the fixer's 5 c0 mutants die.
- K6v-c0-no-rehash survives (M #13): equivalent within one pack run (the fixer's concern 5; confirmed).
- K6v-c0-message-quotes-prefixes survives (M #13): the test asserts that the full fingerprints are absent, so a
  refusal that quotes 12-character prefixes passes. Low consequence (a fingerprint is not a secret). Fix: also assert
  `expect[:12] not in text`.
- **Residual path (minor, lead's call).** A C0_SOURCE e1_fingerprint changed AFTER a clean pack is not refused on the
  Mac: init plans c0 with it (init does not read the unit), release re-plans with the same current values and checks
  only the input pins (R: plan_tool.py:1325-1327, :1463-1468, :1477-1481), and the pod refuses before any step (a
  paid pod start). The fixer's own updated test shows exactly this route and passes (R: test_scorer_block_78b.py:
  1753-1762; M #3). The ruling says "at pack time", so the build meets its words; its purpose ("before a paid pod
  starts") holds only for a typo present at pack time. Fix options: in release_hosts_sc, for a c0 job, run
  c0_source_check on the checkout's source unit (at the job's input pin) against the job's expect_fingerprint; or
  record the checked fingerprint in sealed-files.json at pack and compare it at release.

### The guard (V3, V4): two more thread/socket kinds
- **K6v-G2d-hook-nondaemon-default-threads-free survives** (M #13): V4 runs its default-named probe in a daemon
  thread only (R: test_pp10_process_wide.py:466-472). A plain `threading.Thread(target=...)` (non-daemon, "Thread-N")
  is the most common library thread. Fix: T2 (kills it, M #17).
- **K6v-G1b-wrapper-skips-explicit-proto-v6-stream survives** (M #13): V3 probes AF_INET6 only with UDP. Fix: T3, the
  stand-in matrix of every WRAPPER_CASE x stream/datagram x IPPROTO_TCP/IPPROTO_UDP (no real socket; a weakened wrapper
  reaches _socket's C method, which raises TypeError on the stand-in). T3 kills both K6v-G1b and K5v-G1 (M #17).
- Both are deliberate-looking edits (low realism); their value is as regression guards, as in rounds 4b and 5.

## 3. Results in short

| Run | Result |
|---|---|
| Whole 7-8B suite, SBX | **487 passed** (M #3) |
| runkit/stage1-olmo suite, SBX (unchanged; engine-Y fixture in the copy) | **762 passed** (M #6) |
| Rules runner, ALL | 109 of 109 killed (M #20) |
| Runner runner, ALL | 35 of 35 killed (M #20) |
| Gated runner, 3 chunks (1-40, 41-85, 86-128) | 40 + 45 + 43 = 128 of 128 killed (M #20) |
| Scorer runner, 4 chunks (1-40, 41-95, 96-135, 136-155) | 40 + 55 + 40 + 20 = 155 of 155 killed (M #20) |
| The 7 K5v mutants, whole suite | 7 killed, each in its intended test (M #16) |
| My 14 hand mutants, whole suite | 8 killed, 6 survived (2 equivalent, 3 test gaps, 1 low) (M #12, #13) |
| Ready tests T1-T3 | whole suite + T: 492 passed; each kills its survivor (M #17) |
| Forced failures (K5v-2), 7 points | 7 clean; 2 controls without the finalizer leak (M #14, #15) |
| Token-shaped strings left: both basetemps, WS, my scratch, the fixer's scratch | 0, 0 (4 committed public keys), 0, 0 (M #4-#6, #18, #24) |
| Old free-space test at the 4 truly colliding seeds; new test | 4 fail; 4 pass (M #9, #10) |

## 4. Commands (all in the foreground, each under 10 minutes; exit status)

| # | Command (abbreviated; paths absolute in the runs) | Exit / result |
|---|---|---|
| 1 | `shasum -a 256` of the 9 files; `git --no-optional-locks rev-parse/status/diff --stat HEAD` in WS | 0: 9 equal; only the 9 files modified |
| 2 | `find ... | shasum -a 256` of WS (ws-sha-start.txt); `cp -Rp WS SCR/repo`; the same of SCR/repo; `cmp` | 0: equal, 9,872 entries |
| 3 | `SBX PY -B -m pytest -p no:cacheprovider -q --basetemp SCR/bt-78b-1 runkit/stage1-78b/tests` (cwd SCR/repo, 12:43-12:44) | **0: 487 passed** |
| 4 | `PY2 -B -I SCR/tools/scan_left_v.py SCR/bt-78b-1 <kit secret_scan.py>` | 0: 27,273 files, 5,365 members, 0 hits |
| 5 | the same on WS (skip .git); `git ls-files --error-unmatch`, `git diff --quiet HEAD`, `git check-ignore` of the hits' files and tmp/ | 0: 4 ssh_public_key hits in 2 tracked, unchanged files (+ the fixture's copies) |
| 6 | `git diff --quiet HEAD -- runkit/stage1-olmo`; `SBX PY -B -m pytest ... --basetemp SCR/bt-olmo-1 runkit/stage1-olmo/tests` (12:44-12:45); scan of bt-olmo-1; hash list of SCR/repo | 0; **0: 762 passed**; 0 hits (66,700 files, 1,338 members); equal |
| 7 | `PYTHONHASHSEED=54 PY -B -I -S -c 'print(hash("None"))'` x3, and without `-I` x3 | 0: three different values; one value |
| 8 | the old-name sweep, seeds 0-1499, with `-I` (12:46) and without `-I` (12:47) | 0: 6 random seeds; **4 seeds: 54, 289, 772, 1289** |
| 9 | SCR/seedcheck/repo (links + kit copy + HEAD's test_kit_78b_runner.py from `git show`); `PYTHONHASHSEED=s SBX PY -B -m pytest ... test_kit_78b_runner.py -k free_space_check_refuses` for s in 0, 54, 188, 459, 868, 1027, then 289, 772, 1289 | 0, **1**, 0, 0, 0, 0; **1, 1, 1** (FileExistsError) |
| 10 | the same on the fixed test (SCR/repo) for s in 54, 289, 772, 1289 | 0, 0, 0, 0: 1 passed each |
| 10b | `grep -n "[^_.a-z]hash("` in both kits' tests | 1: no other use |
| 11 | `PY2 -B -I SCR/tools/make_hm_spec.py SCR/repo/runkit/stage1-78b SCR/hm_spec.json` | 0: 14 mutants, every find once |
| 12 | `caffeinate -i SBX PY -B SCR/tools/hm_runner.py SCR/repo SCR/hm-a SCR/hm-a.json <7 data/ ids> --spec SCR/hm_spec.json --timeout 300` (12:50-12:54) | 1: 5 killed, 2 survived; baseline 487 passed |
| 13 | the same, hm-b, 7 ids (c0, guard, redirect) (12:54-12:57) | 1: 3 killed, 4 survived; baseline 487 passed |
| 14 | `SBX PY -B SCR/tools/forced_fail.py SCR/ff/repo SCR/ff <secret_scan.py>` (12:59) | 0: 7 variants, each exit 1 with the forced FAILED; 0 hits each; kit copy restored (`diff -r`) |
| 15 | `SBX PY -B SCR/tools/forced_fail_control.py ...`; `rm -rf` of the 2 control basetemps | 0: 1 and 2 files with hits; deleted |
| 16 | PY2: SCR/hm_spec_k5v.json from the kit specs, compared with k5-verify's hm_spec.json/hm_spec2.json; `hm_runner.py ... hm-k5v ALL --spec SCR/hm_spec_k5v.json` (13:00-13:02) | 0: 6 identical, 1 moved; **0: 7 killed** |
| 17 | `SBX PY -B SCR/tools/one_mutant_ready.py SCR/ff/repo <spec> NONE|<id> SCR/tools/test_k6v_ready.py <bt> -- <targets>`: NONE on the whole suite + T; then K6v-unlisted-binary-unscanned, K6v-G2d, K6v-G1b, K5v-G1 on T only | 0: 492 passed; pytest 1 each, only T1 (3 cases) / T2 / T3 / T3 fail |
| 18 | scan of SCR/ff; `rm -rf` of the mutant runs' basetemps; rescan | 0: 3 hits (the K6v-binary mutant's bundles, the mutant's own leak); deleted; 0 hits |
| 19 | `PY2 -B -I SCR/tools/real_prepared_probe.py /Users/spiderishi/Coding/attribution SCR/repo/runkit/stage1-78b` | 0: see section 2, K5v-3; 0 hits |
| 20 | `SCR/tools/chunk.sh <runner> <spec> A B TAG` (caffeinate -i SBX PY -B runner SCR/repo SCR/runs/TAG SCR/runs/TAG.json <ids> --timeout 300): rules 1-109 (13:05-13:06), runner 1-35 (13:06-13:07), gated 1-40 (13:07-13:09), 41-85 (13:09-13:13), 86-128 (13:13-13:17), scorer 1-40 (13:17-13:18), 41-95 (13:18-13:23), 96-135 (13:23-13:28), 136-155 (13:28-13:32) | 0 each: 109, 35, 40, 45, 43, 40, 55, 40, 20 killed; 0 survived, 0 invalid |
| 21 | PY2: per runner JSON, the verdicts, baseline and spec SHA-256, and each K6/K5v mutant's killing test | 0: 427 killed; spec hashes equal the WS files' |
| 22 | `git show HEAD:<spec>` x4 into SCR/head-specs; PY2 comparison by id | 0: see section 0 |
| 23 | hash lists of WS and SCR/repo at the end vs the start | 0: both equal |
| 24 | scan of SCR (without repo/) and of reports/k6-fix-scratch; `rm -rf` of my basetemps, copies and SCR/repo; rescan of SCR | 0: 0 hits (99,116 files, 7,453 members), 0 hits (19 files); SCR now 9.1 MB, 0 hits |

Reads (R): k6-fix.md; k5-verify.md and its scratch (V tests, hm specs, hm_runner.py); the 7 Nov rulings section
(lead-rulings-part2-design-20261106.md:81-127); the fixer's diff of all 9 files; pack_setup.py, plan_tool.py
(c0 planning and release), rules_78b.py (C0_SOURCE validation), setup/job_runner_stage1.py (c0_fingerprint),
launch.py (redirect), tests/conftest.py (guard), secret_scan.py, experiments/safety_selection/prepare.py (manifest).

## 5. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| K5v survivors (V1-V5, D1c) adopted and each killed, by my own run | passed | M #16, #20, #21 |
| K5v-2: no token-shaped file left, on pass AND on fail | passed | M #3-#6, #14, #15 |
| K5v-6: the call site pinned | passed | M #12, #16 |
| K5v-9: flaky folder names fixed | passed (the fixer's seed evidence wrong; true seeds checked) | M #7-#10 |
| K5v-3 data/ scan ruling, by my own hand mutants | passed; **1 test-gap survivor** (binary suffix) | M #12, #17, #19 |
| Item 23 C0_SOURCE pack check, by my own hand mutants | passed for pack-time typos; 1 low survivor; **1 residual path** (post-pack edit) | M #13, #3; R plan_tool.py:1463-1481 |
| Guard (V3, V4) by my own mutants, sandboxed | passed for the adopted mutants; **2 survivors** (new kinds) | M #13, #16, #17 |
| All four kit runners re-run (chunked, SBX) | passed: 109, 35, 128, 155 killed; 0 survived, 0 invalid | M #20, #21 |
| Whole 7-8B suite under SBX | passed: 487 | M #3 |
| runkit/stage1-olmo unchanged, its suite passes | passed: no diff; 762 | M #6 |
| Basetemp and worktree scan for token shapes | passed: 0 hits (4 committed public keys only) | M #4-#6, #24 |
| No real network or outside process from the tests | passed under SBX (I did not read the sandbox log; T3 uses stand-ins only) | all runs |
| CUDA, a real pod, a real pack | not tested | $0 scope |

## 6. Jobs for the lead

1. Merge the fixer's 9 files by explicit paths (its SHA-256 list, which I confirmed, M #1). Nothing of mine needs
   merging for this round.
2. Optional small round (all minor): adopt SCR/tools/test_k6v_ready.py's T1 into test_scorer_block_78b.py and T2, T3
   into test_pp10_process_wide.py; add K6v-unlisted-binary-unscanned (scorer spec) and
   K6v-G2d-hook-nondaemon-default-threads-free, K6v-G1b-wrapper-skips-explicit-proto-v6-stream (gated spec), with the
   find/replace in SCR/hm_spec.json; add `expect[:12] not in text` to the item-23 test.
3. Rule the item-23 residual path (a C0_SOURCE edit after the pack reaches a pod): accept as a limit, or add the
   release-time check (section 2).
4. Correct the record of k6-fix.md M #8: the colliding seeds are 54, 289, 772, 1289 (not 868, 1027); `-I` ignores
   PYTHONHASHSEED, so any seed sweep must run without `-I` (it reads no data file).
5. Re-verify after the merge (each under 5 min here), cwd the merged checkout or a copy, SCR2 a new folder:
   `PYTHONDONTWRITEBYTECODE=1 caffeinate -i SBX PY -B -m pytest -p no:cacheprovider -q --basetemp SCR2/bt runkit/stage1-78b/tests`
   (expect 487) and `caffeinate -i SBX PY -B runkit/stage1-78b/tests/run_mutants_<k>.py <repo> SCR2/<tag>
   SCR2/<tag>.json <ids> --timeout 300` with rules ALL (0.5 min), runner ALL (1 min), gated 1-40, 41-85, 86-128 (1.9,
   3.8, 4.0 min), scorer 1-40, 41-95, 96-135, 136-155 (1.0, 4.4, 4.9, 3.4 min). SCR/tools/chunk.sh shows the id slicing.
6. After review, delete WS/tmp/engine-y-34bfd288 (the fixer's 67 MB fixture copy), reports/k6-fix-scratch/ and my
   SCR (9.1 MB; no token-shaped file in it, M #24).

## 7. Unresolved concerns

1. Item 23's residual path (job 3). Consequence: one paid pod start that refuses before any step; no wrong result.
2. The fixer's concern 2 stands: the pack does not refuse an off-pin manifest.json, nor a listed file that is missing
   or off its listed hash, nor a link in the prepared set (it skips links silently). The pod's engine refuses the
   first two (R: prepare.py:877-893). A Mac-side refusal would follow item 23's purpose (fail on the Mac before a paid
   pod). The real sets show none of these today (M #19; the listed files' hashes not taken by me or the fixer, since
   they include selector and hidden files).
3. The skipped macOS metadata names are not recorded anywhere (`_skipped` is dropped, R: pack_setup.py:555). Low.
4. The fixer's concern 6 stands (I): a finalizer cannot run if the process is killed; the runners delete their
   basetemps after each run (R: hm_runner.py and the kit runners, `run_suite`, `shutil.rmtree`). Also, a mutant that
   breaks the pack can leave a bundle holding a fake (seen in M #18); only mutant runs can produce that, and they
   delete their basetemps.
5. I did not read the macOS sandbox log. SBX denies outbound IP; my T3 uses stand-ins only.
6. refuse_secrets' docstring still says "so data/ only stays outside" (R: pack_setup.py:304) before it adds the
   scan_anyway clause. Cosmetic.
