# k4b-sec-reverify: kit security re-verify (round 4b)

Started 2026-11-06 17:09 UTC; this version written 17:50 UTC (`date -u` read right before each write). Status: **DONE**.
Verdict: **VERIFIED_WITH_MINOR**. The fixer's D1-D5 hold for every mutant round 4 raised (all killed again, by my runs
and by the kit's own runners). My own hand mutants find five minor gaps: four are test-strength gaps, one is two
packed folders that the pack does not scan. The code is correct under every probe. Not one gap is a live leak today.

- WS = `scratchpad/b78/ws-k2` (read only; M: unchanged, see command 24). SCR = `reports/k4b-sec-scratch/`.
- PY = the main venv's python (3.11.15). SBX = `sandbox-exec -f SCR/deny.sb`: outbound IP denied, the mDNSResponder
  socket and mach names denied, every exec denied except the two venv interpreters, their uv binary and git.
- Every run had the token, key and HF path variables unset (or set to FAKE values, command 8), HOME = SCR/home.
- Tags: M measured (command number), R read (path:line, in WS), E estimate, I inference.
- No pod, spend, network, install, download, agent or message. No secret read: every token-shaped value was made in
  my scratch at run time (SCR/fake-values.json, random, fake). No selector, hidden, judge, answer, generation, sample
  or prompt-text file opened. No git state changed. The main checkout was not written.

## 1. Files changed

None in WS or the main checkout. Scratch only (evidence, not for merge):
- SCR/tools/: prep.py (kit copy), run_hand.py (hand-mutant runner; killed only on exit 1 with FAILED and no ERROR),
  make_spec.py, scan_fake.py. SCR/hand_spec.json: my 28 hand mutants plus the round-4 verifier's 13 (as P-*).
- SCR/probe/: probe_d1.py, probe_d2.py, probe_d3.py and SCR/probe/mut/ (conftest variants for the probes only).
- SCR/suite/repo: a copy of WS's runkit/stage1-78b (other entries symlinked). M: restored after every mutant.
- Results: SCR/hand-d1d2.json, hand-d3d4.json, hand-pack.json, hand-tok-prior.json, hand-survivors-local.json,
  hand-runjob.json, mr-gated.json, mr-sc.json, base.out, fake.out, log-*.txt, pids-*.txt.
- I deleted my three pytest basetemps (about 1 GB of test-made files) after I recorded their counts.

## 2. Items: what I checked and the evidence

### D1 (the process-wide wrapper: sendto, sendmsg, AF_INET6). Closed for round 4's mutants. One new survivor.
- M #13: the round-4 verifier's three wrapper mutants (sendto, sendmsg, inet-only) and connect-ex-not-wrapped and
  inet6-free now die in the builders' three guard files (round 4: they survived).
- M #10: of my four new D1 mutants, three die (sendto read only without flags; connect_ex unchecked; sendmsg not
  wrapped). **H-d1-wrapper-skips-dgram survives the whole suite** (a wrapper that gives every real SOCK_DGRAM socket to
  C). Cause (R): the D1 probes call the wrapper on a stand-in object with only `family`
  (test_pp10_process_wide.py:289-291); the real datagram probe (:103) checks only the HOOK prefix, and the audit hook
  gives that prefix too after C has parsed the address. M #17: under the mutant, a real datagram send to a numeric
  address is refused by the hook only, not the wrapper. With a host name, C resolves the name before the event
  (R: conftest.py:17-19). See R1.

### D2 (the hook under the flag, in threads, bytes hosts). Closed for round 4's mutants. Two new survivors.
- M #13: main-thread-only, os/sockets/lookups free under the flag, loopback-bytes-any, loopback-is-private,
  lookup-numeric-only and popen-argv0: all die now.
- M #10: of my six D2 mutants, four die (urllib free under the flag; bytes host for http.client; every reverse lookup
  free; the flag opens any program with an allowed base name). **H-d2-hook-daemon-threads-free and
  H-d2-hook-executor-threads-free survive** (the hook skips daemon threads, or ThreadPoolExecutor workers, where
  asyncio's loop.getaddrinfo runs). R: the thread probes use one non-daemon `threading.Thread`
  (test_pp10_process_wide.py:337-343). M #18: under each mutant a hand-raised os.system or getaddrinfo event in that
  thread kind is let through. See R2.

### D3 (http_get's TLS). Closed for round 4's mutant. Three new survivors.
- M #11, #20: the round-4 mutant (the redirect handler's own https_open) dies, in my run and in the kit's runner.
- M #11, #12: of my five D3 mutants, two die. H-d3-global-unverified-at-call dies only because an earlier test
  (test_d1, :1007) calls http_get before test_rv2_1 checks ssl's default (:1379): an order effect. H-d3-connection-
  class-unverified dies by chance: its global patch breaks test_pp10_guard.py's g1_g4 test, not a TLS assertion.
  **Three survive the whole suite:** H-d3-default-open-mixin (a base class gives SameHostAuthRedirect a default_open
  that opens https unverified), H-d3-https-request-downgrade (an https_request that rewrites the URL to http), and
  H-d3-instance-https-open-unverified (http_get overrides its HTTPSHandler instance's https_open).
- M #16: these are not equivalent mutants. With urllib's own dispatch driven by hand and http.client's two connection
  classes replaced by recorders (no socket), each survivor passes both new D3 checks (every https handler is a plain
  HTTPSHandler; the class defines no `*_open`), yet the Bearer header goes to an UNVERIFIED TLS peer (two) or over
  plain HTTP (one). The shipped class goes to the default (verifying) context. See R3.

### D4 (the suite and the shell's HF paths). Closed.
- M #12: H-d4-test-old-line (the preflight test removes the token variables only, round 4's line) dies: the
  stored-login case fails.
- M #8, #9: the whole suite with FAKE values in HF_TOKEN, HUGGING_FACE_HUB_TOKEN, RUNPOD_API_KEY,
  RUNPOD_OPERATOR_API_KEY, GH_TOKEN, GITHUB_TOKEN and one more variable, and HF_HOME, HF_TOKEN_PATH and
  XDG_CACHE_HOME at a fake stored login: **451 passed** (round 4: 412 passed, 1 failed). The fake values appear 0 times
  in the pytest output, in 23,628 test files and in 4,088 members of 119 tarballs the tests built.

### D5 (the pack scans the named inputs). Closed for inputs/.
- M #12: H-d5-nested-inputs-unscanned (only inputs/NAME/FILE scanned) and H-d5-input-scan-off die. M #21: the kit's
  K4bf-m-pack-inputs-unscanned and -pack-scan-binary-only die in the kit's scorer runner.
- R: the scan reads every non-binary file under inputs/ before anything is written (pack_setup.py:245-253, 505);
  refusals carry bundle paths and counts only. The only binary files a real input folder holds are .safetensors
  (R: experiments/safety_selection/engine.py:403-412).

### The pack's scan over everything it ships. Two gaps (R4).
- Not scanned in code: edits/ (the three R_d edit files) and data/ (the prepared set) stay in DATA_PREFIXES
  (pack_setup.py:60, :254), and binary-suffix files under inputs/ (:241, :249-250). M #22: in the suite's 49
  test-built bundles, 147 edits/ and 98 data/ members were outside the pack's scan; 222 inputs/ members were scanned.
- Not pinned by tests: M #12: five mutants that drop the other scans survive the whole suite: the setup tar's members
  (:523), the generated payloads (:256-257), the worker bootstrap (:514), the engine files and scripts/ (:254). The
  only pack-scan test in the 7-8B kit is the new inputs one (test_scorer_block_78b.py:1666). Pre-existing since K1.

### The token, traced once more
- M #24: launch.py, host.py, orchestrate.py, setup/download_models_stage1.py, setup/preflight_stage1.py, both setup
  shell scripts, finisher.py, budget.py, account.py, secret_scan.py and tests/conftest.py are byte-equal to round 4's
  verified copy. No changed launch, host, orchestrate or download code exists in this round.
- Changed code that starts a process: job_runner_stage1.py's new verify_unit (:668-672) and the
  o_only_with_regenerate steps (the same loop, :731) take `env` = os.environ minus the two token names, plus
  HF_HUB_OFFLINE=1 (:996-998); the runner refuses any token variable or token file before any job (:337-348,
  unchanged). pack_setup's engine_run passes only PATH and PYTHONDONTWRITEBYTECODE (:112-116).
- Records: the acceptance record keeps hex64-filtered fields only (job_runner_stage1.py:702-707). M #13:
  H-tok-accept-reads-whole-side (copy the side unit's whole COMPLETE.json into the record) dies in 6 cases.
  record-done keeps `verified_exit` 0, never the 600-character tail (plan_tool.py:1541-1547).
- M #13, #19: no test pins the environment those steps get: H-tok-verify-env-whole and H-tok-sc-steps-env-whole
  survive, and so does H-tok-run-job-env-whole (the engine jobs; pre-existing). See R5.

### No real network or outside process from the tests
- M #5: the whole suite under SBX: 451 passed. M #6, #15, #23: over the whole session window (17:17-17:48 UTC), the
  only Python sandbox denials on this machine were the mDNSResponder socket (the suite's own "localhost" lookup;
  bisected to test_pp10_guard.py) and `remote:*:9` (bisected to test_pp10_process_wide.py, whose only real port-9
  calls are the two loopback calls at :205-210, R). No exec denial at all. For my runs with recorded pids (commands
  11-14, 19), each run showed only those two kinds, as the baseline did (M). Another agent's sandboxed mutant run was
  active at the same time (M: pgrep); its pids show only `remote:*:9`.

## 3. Commands (all foreground, each under 10 minutes; exit status)

| # | Command (abbreviated) | Result |
|---|---|---|
| 1 | `date -u` before each time written (17:09, 17:19, 17:50) | 0 |
| 2 | reads: rulings PP7-PP18, round-4 reports, `diff -u` of the changed files vs round 4's copy and the fixer's before-snapshot | 0 (diff 1 = differences, expected) |
| 3 | touch SCR/ws-k2-marker-start; shasum of WS's kit and scripts/scale78b (108 files); `git status --short` count | 0; 57 entries |
| 4 | PY -B SCR/tools/prep.py WS SCR/suite; copy shasum vs WS | 0; COPY-EQUAL |
| 5 | SCR/suite/repo: env -u (11 vars) HOME=SCR/home caffeinate -i SBX PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests (17:17:05-17:17:27) | **0: 451 passed** |
| 6 | /usr/bin/log show (Sandbox sender, python, per window) | 0 |
| 7 | PY -B -I: make 9 random FAKE values and a fake HF login (SCR/fakehf, SCR/fakexdg) | 0 |
| 8 | the whole suite with the fake values and the three HF path variables at the fake login, under SBX (17:18:04-17:18:26) | **0: 451 passed** |
| 9 | PY -B -I SCR/tools/scan_fake.py (output, test folders, tar members) | 0: 0 hits for each of the 9 values |
| 10 | caffeinate -i SBX PY -B SCR/tools/run_hand.py ... 10 D1/D2 mutants, whole suite (17:21:07-17:25:45) | 0: baseline 0; 7 killed, **3 survived** |
| 11 | the same, 5 D3 mutants (whole suite) and H-d4-test-old-line (test_kit_78b_runner.py) (17:26:42-17:29:31) | 0: baselines 0, 0; 4 killed, **2 survived** |
| 12 | the same, 7 pack mutants and H-d3-instance-https-open-unverified (17:30:12-17:35:12) | 0: baseline 0; 2 killed, **6 survived** |
| 13 | the same, 3 runner mutants (whole suite) and the round-4 verifier's 13 (the builders' 3 guard files) (17:36:16-17:39:20) | 0: baselines 0, 0; 14 killed, **2 survived** |
| 14 | the 3 guard survivors again under SCR/deny-nonlocal.sb (17:39:57-17:41:57) | 0: 3 survived; denials as baseline |
| 15 | the 3 guard test files one by one under SBX (pid per file) | 0, 0, 0 (8, 51, 133 passed) |
| 16 | SBX PY -B -I SCR/probe/probe_d3.py | first 1 (my recorder lacked `**kw`), then 0 |
| 17 | SBX PY -B SCR/probe/probe_d1.py with the shipped conftest and the dgram mutant | 0, 0 |
| 18 | SBX PY -B SCR/probe/probe_d2.py with the shipped conftest and the two thread mutants | 0, 0, 0 |
| 19 | run_hand.py H-tok-run-job-env-whole (17:45:39-17:46:30) | 0: baseline 0; survived |
| 20 | caffeinate -i SBX PY -B SCR/suite/repo/.../run_mutants_gated_78b.py SCR/suite/repo SCR/mr-gated SCR/mr-gated.json <the 10 K4bf ids> --timeout 300 (17:46:49-17:47:50) | **0: baseline 0; 10 of 10 killed** |
| 21 | the same with run_mutants_scorer_78b.py, K4bf-m-pack-inputs-unscanned and -pack-scan-binary-only (17:48:02-17:48:29) | **0: baseline 0; 2 of 2 killed** |
| 22 | PY -B -I: count the members of the 49 test-built bundles by top folder | 0 |
| 23 | log show over 17:17-17:48 UTC: every Python sandbox denial kind on the machine | 0: only mDNSResponder and remote:*:9 |
| 24 | find WS -newer the marker (not .git); WS shasum vs command 3; find __pycache__ in WS; git status count; copy shasum vs command 4; 12 token-path files vs round 4's copy | 0 files; WS-UNCHANGED; 0; 57; COPY-RESTORED; all 12 equal |
| 25 | rm -rf my three basetemps (SCR/bt-base, bt-fake, bt-bisect) | 0 |

One slip: a first report update ran an empty `python3 -` heredoc that did nothing (exit 0); I re-ran it with PY.

## 4. Defects and residual items (all minor; none is a live leak today)

- **R1 (D1 test strength).** H-d1-wrapper-skips-dgram survives the whole suite (M #10). Failure: an edit makes
  `_checked_socket_method` skip SOCK_DGRAM sockets; at collection or in a module fixture,
  `socket.socket(AF_INET, SOCK_DGRAM).sendto(b"x", ("name.example", 53))` resolves the name (one DNS query) before the
  hook refuses; no test fails. Fix: in test_dk1_module_scoped (or the D1 test) assert "(before any name resolution)"
  for the real datagram probe (test_pp10_process_wide.py:103) and add an AF_INET6 datagram probe with a numeric
  address (fail-closed: the hook still refuses before any packet); or give the stand-in `type` and `proto` and run the
  D1 cases for SOCK_STREAM and SOCK_DGRAM. Add the mutant to mutation_spec_gated_78b.json.
- **R2 (D2 test strength).** H-d2-hook-daemon-threads-free and H-d2-hook-executor-threads-free survive (M #10, #18).
  Failure: an edit makes `_audit` return early in a daemon thread or a ThreadPoolExecutor worker; at collection, an
  asyncio getaddrinfo (it runs in the default executor) or a raw `_socket` call there goes through; no test fails.
  Fix: run `_hook_probes(HOOK_EVENTS + BYTES_EVENTS)` also in a daemon thread and in a ThreadPoolExecutor worker, at
  collection and in the test. Add both mutants. (These mutants add thread logic the hook does not have: low realism.)
- **R3 (D3 test strength).** Three survivors (M #11, #12) send the Bearer token unverified or in clear (M #16) and pass
  test_rv2_1's new checks. Failure: e.g. a base class that gives SameHostAuthRedirect a `default_open`, or an
  `https_request` that rewrites the scheme; no test fails. Fix: make `_real_opener_with_fake_open`'s fake open run the
  opener's own steps (its `process_request` for the request's scheme, then `opener._open(request)`; this skips only
  OpenerDirector.open's audit event), with `http.client.HTTPSConnection` and `HTTPConnection` monkeypatched to recorders
  that assert the scheme stays https, the host is huggingface.co and the context is None or verifying, and then return
  the fake response. probe_d3.py has the recorders. Add the three mutants.
- **R4 (the pack's scan).** (a) edits/ and data/ ship outside the scan (pack_setup.py:60, :254; M #22). (b) No test
  pins the scans of the setup tar, the payloads, the bootstrap, the engine files or scripts/ (M #12: five survivors).
  Failure for (b): an edit drops `refuse_secrets(setup_files, ...)` (:523); a token-shaped value that lands in a setup
  file goes to the pod in worker-setup-stage1.tar.gz; no test fails. Mitigation (R): test_stage1_runkit.py:383-386
  asserts the kit's own sources hold no pattern today; the finisher scans pulled trees; the backup scans every staged
  file. Fix: one test that plants a token-shaped string (built at test time) in an engine file, a scorer script, a
  setup file, a payload (a monkeypatched probe_record) and the bootstrap (a monkeypatched PIP_PIN), and asserts the
  pack refuses with names only; scan edits/ (three small JSON files); the lead rules whether data/ stays outside
  (a training set can hold token-shaped text; a refusal there would stop the pack). Add the five mutants.
- **R5 (the steps' environment).** No test pins the environment of the new engine verify, the scorer steps, or the
  engine jobs (M #13, #19: three survivors; the last pre-existing). Today no token can reach them: the runner refuses
  token variables and token files before any job (R: :337-348). A regression would lose HF_HUB_OFFLINE=1 and the
  token-name drop (R: :996-998). Fix: a runner test that records `env` for every subprocess.run of run_sc_job,
  verify_unit and run_job and asserts no TOKEN_ENV_NAMES key and HF_HUB_OFFLINE == "1". Add the mutants to
  mutation_spec_runner_78b.json.

## 5. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| D1 by my own hand mutants, sandboxed | passed for round 4's mutants; **1 new survivor** (R1) | M #10, #13, #17 |
| D2 by my own hand mutants, sandboxed | passed for round 4's mutants; **2 new survivors** (R2) | M #10, #13, #18 |
| D3 by my own hand mutants, sandboxed | passed for round 4's mutant; **3 new survivors** (R3) | M #11, #12, #16, #20 |
| D4 the suite independent of the shell's HF paths | passed | M #8, #9, #11 |
| D5 the pack scans the named inputs | passed | M #12, #21 |
| The fixer's 10 gated and 2 pack-scan K4bf mutants | passed (12 of 12 killed, kit runners, SBX) | M #20, #21 |
| Token traced through changed launch, host, orchestrate, download code | passed (none changed; the changed runner and pack code carry no token) | M #24; R §2 |
| The pack's secret scan covers every input it ships | **failed (minor)**: edits/, data/ unscanned; five scans unpinned by tests (R4) | M #12, #22 |
| Whole 7-8B suite under the sandbox | passed: 451 | M #5, #8 |
| No real network or outside process from the tests | passed | M #6, #15, #23 |
| No real secret read | passed (fake values only) | §1, M #7 |
| CUDA, a real pod, real scorer scripts | not tested | $0 scope |

## 6. Jobs for the lead

1. Rule on R1-R5: fix in a small round, or accept as limits. The mutants are ready in SCR/hand_spec.json (ids H-*);
   the probes in SCR/probe/. Run any conftest mutant only under SBX (SCR/deny.sb).
2. If fixed, the kit's specs gain: R1-R3's six mutants (mutation_spec_gated_78b.json), R4's five
   (mutation_spec_scorer_78b.json), R5's three (mutation_spec_runner_78b.json). Then the gated runner under SBX.
3. Delete SCR (k4b-sec-scratch/, 6.4 MB) after review.

## 7. Unresolved concerns

1. The kernel log prints `remote:*:9` with no address. A profile with `(allow network-outbound (remote ip
   "localhost:*"))` still logged it (M #14), so I place it at loopback by pid bisection and the source (R), not by
   the log's address.
2. Documented limits are unchanged and not re-tested: ctypes, a host name given to a raw `_socket.socket`, the
   children of local_processes programs (R: conftest.py:20-22).
3. The survivors in R1-R3 are deliberate-looking edits. Their value is as regression guards, not as signs of a bug.
4. The pod's JOB-DONE `unit` string is stored in plan.json without a shape check for scorer unit kinds
   (plan_tool.py:4420); record-done needs a matching COMPLETE.json under it (:4390-4395). Pre-existing; a tiny
   channel at most (I).
