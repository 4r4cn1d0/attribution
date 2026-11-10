# K4 security verify (K4a guard and token items, K4b pod commands and bundle)

Started 2026-11-06 15:26 UTC; this version written 15:57 UTC (`date -u` read right before each write). Adversarial
verifier. Status: **DONE**. Verdict: **VERIFIED_WITH_MINOR** (the code holds under every probe; five minor defects,
four of them test gaps that let my mutants live, one a pack-scan gap).
Worktree ws-k2 read only (M: no file newer than my start marker, kit hashes unchanged, no __pycache__; command 17).
Scratch: reports/k4-sec-scratch/ (SCR). PY = the main venv's python (3.11.15, huggingface_hub 0.36.2). PY2 = .venv
(no huggingface_hub). SBX = `sandbox-exec -f SCR/deny-all.sb`: outbound IP denied, the mDNSResponder socket and its mach
names denied, every exec denied except the two venv interpreters, their uv binary and git.
Tags: M measured (command number), R read (path:line), E estimate, I inference.
No pod, spend, network, install, download, agent or message. No secret read (all token-shaped values were fake, made
in the command). No selector, hidden, answer, generation or prompt file opened. No git state changed.

## 1. Files changed

None in ws-k2 or the main checkout. Scratch only (evidence, not for merge):
- SCR/probe-suite/tests/{conftest.py (byte copy, a1706a29), test_a_sec_probes.py (38d038fe), test_b_sec_after.py}
- SCR/tools/{prep.py, run_sec_mutants.py, sec_mutants.json, sec_mutants_launch.json, sec_mutants_runner.json,
  show_probes.py, scan_tars.py}; SCR/probe/{shapes.py, ctl_local.py, ctypes_gap.py}; SCR/deny-all.sb, deny-net-dns.sb
- SCR/suite1/repo and SCR/suite-mut/repo: copies of ws-k2's kit (other entries symlinked, the mutation runners' form);
  SCR/suite1/repo/runkit/stage1-78b/tests/test_sec_pack_inputs.py exists ONLY in that copy.
- Results: SCR/sec-mut-probes.json, sec-mut-probes-r2.json, sec-mut-builders.json, sec-mut-tls.json,
  sec-mut-runner.json, mut-gated-sec.json, mut-runner-sec.json, suite1.out, suite-fakeenv.out, probe0.out.

## 2. What I checked, and the evidence

The files verified are the builders' final ones (M #1: every kit file in ws-k2 equals my copy; conftest a1706a29,
test_pp10_process_wide 00c3d602, test_pp10_guard 564f7e93, job_runner fef1b656, pack_setup 3a9cd1e8, launch 47104658).

1. **Process-wide guard, every context the brief names (M #6, #7, #12).** My probe file runs 43 probes (processes:
   subprocess, shell, asyncio, os.system, posix.system, execv, execve, posix_spawn, spawnv, fork, pty.fork,
   multiprocessing spawn / forkserver / fork; lookups by NAME: getaddrinfo (str and bytes), gethostbyname(_ex),
   gethostbyaddr, getnameinfo without numeric flags, getfqdn, create_connection; sockets: AF_INET and AF_INET6
   connect / connect_ex / sendto (with and without flags) / sendmsg with numeric addresses and with a host name through
   socket.socket, and raw _socket.socket with numeric addresses incl. an IPv4-mapped IPv6; http.client, HTTPS by name,
   urlopen). Every probe is fail-closed: the real call runs only after the same event raised by hand is refused, or
   the wrapper refuses on a stand-in object (a weakened wrapper reaches C's method, which raises TypeError on the
   stand-in), or fork_exec is the refusal. Contexts: module import (collection), a thread started at collection, a
   session fixture, a module fixture, a module fixture set up beside local_processes (flag still empty), a module
   fixture's teardown (asserted from the next file), and a test under local_processes (posix.* and raw _socket, which
   only the hook covers there). Result: all refused, each by the hook's or the wrapper's own message, no marker file
   made (M #6: 8 passed; show_probes: 43 of 43 'refused' at collection and in the thread). Host-name socket calls stop
   in the wrapper "(before any name resolution)" (M). Lookup events carry the shapes the hook reads and fire before
   any result (M #2).
2. **Guard mutants under the sandbox (M #7, #8, #12).** 13 mutants of my own (SCR/tools/sec_mutants.json). My probes
   kill 12 (the 13th, popen-argv0, is a calibration mutant the builders' DK-2 test kills). The builders' three guard
   files (test_gated_78b.py, test_pp10_guard.py, test_pp10_process_wide.py) kill only 5 of the 13: see D1, D2.
3. **TLS (RV2-1).** The builders' three TLS mutants are killed again (M #9). My mutant
   SEC-m-tls-redirect-handler-opens-https-unverified survives all of test_gated_78b.py (M #10): see D3.
4. **RV2-2..RV2-7, RV2-9.** The builders' 12 non-conftest K4 mutants (failure-text scrubs, redirect codes, both token
   variable names, staging values, $VAR expansion, HF_HOME over XDG) are killed again under SBX (M #9). RV2-9 under PY2:
   11 passed, the 11 library comparisons skipped (M #11). RV2-6 / RV2-7 hold in the probes above (M #6).
5. **The runner's token check (RV2-8).** R: job_runner_stage1.py:337-348: before any job, token variables refuse, then
   download_models_stage1.no_token_left() (HF_TOKEN_PATH, else HF_HOME/token, and stored_tokens; R:
   download_models_stage1.py:99-106); its SystemExit becomes AssertionError; a missing file crashes the runner (fails
   closed). The module is loaded lazily and resolves the paths at each call (M: test_rv2_8 changes the variables after
   the first load and still refuses). The three builders' mutants are killed again (M #9b). The runner and the download
   script ship in the same setup tar (R: pack_setup.py:51-52). Engine jobs get the environment minus the token names,
   with HF_HUB_OFFLINE=1 and the two HF_HUB_* switches (R: job_runner_stage1.py:894-896).
6. **Scorer pod commands and records (K4b).** R: job_runner_stage1.py:516-591: every argv value comes from plan.json
   (seed, groups, expected fingerprint), the sealed doc (bundle paths, pins) or rules constants; no environment value,
   no token. The wrapper runs with -I -B. The record keeps output paths and SHA-256s, the wrapper record's four
   type-checked fields and exit codes (R: :594-693); record-done re-filters to counts and hashes (R: plan_tool.py:
   1504-1543). M: K4b's exact-argv and sentinel tests pass in the suite (#5); my mutant
   SEC-m-runner-wrapper-record-whole (copy the whole wrapper record into JOB-DONE) is killed (#10b). M #14: the whole
   suite run with FAKE token-shaped values in HF_TOKEN, HUGGING_FACE_HUB_TOKEN, RUNPOD_OPERATOR_API_KEY, RUNPOD_API_KEY,
   GH_TOKEN, GITHUB_TOKEN and HF_HOME pointing at a fake login: the fake values appear nowhere in the pytest output, in
   472 test folders, or in the 3,671 members of the 104 bundle and setup tarballs the tests built (0 hits for the
   values and for the hf_/rpa_/gh*_ patterns; SCR/tools/scan_tars.py).
7. **The bundle and tokens.** Code, settings, payloads and setup files are secret-scanned at pack time (R:
   pack_setup.py:241-248, 493, 502, 511). Named inputs, data and edits are not (DATA_PREFIXES, R: pack_setup.py:60; the
   same at HEAD d203070). M #15: a token-SHAPED synthetic string in the anchor prompt list (a named input, pinned
   test-locally) is packed without refusal and lands in one bundle member under inputs/: see D5. The bundle carries
   text inputs by design (anchor prompts, the S1/S3/S4 lists, pools); commands and records carry none.
8. **No real network or outside process in the suite (M #5).** The whole 7-8B suite (413 passed) under SBX with a
   scratch HOME and every token and HF path variable unset: the kernel log shows only the loopback port-9 denial (the
   guard tests' own loopback probes) and, in later runs, the mDNSResponder socket denial of the suite's own "localhost"
   lookups (they fall back to the hosts file, M #4). No exec denial: the two local_processes children (the runner's
   dry run, the engine-parser import) start nothing and reach nothing.

## 3. Commands (all foreground; exit status)

| # | Command | Exit / result |
|---|---|---|
| 1 | shasum of every ws-k2 kit file vs SCR/suite1 copy (SCR/ws-kit.sha, copy-kit.sha) | cmp equal (59 files) |
| 2 | PY -B -I SCR/probe/shapes.py (a recording hook that raises on socket.* events) | 0; five lookup shapes as the hook reads them; each raised before any result. Run before the sandbox existed; no lookup happened (the hook raised first; I) |
| 3 | SBX PY: exec /usr/bin/true (control) | PermissionError; log deny process-exec* /usr/bin/true |
| 4 | SBX PY SCR/probe/ctl_local.py (localhost, 127.0.0.1) | 0; resolved; log deny network-outbound /private/var/run/mDNSResponder (the profile blocks the DNS daemon) |
| 5 | SCR/suite1/repo: env -u (6 token/key vars, 4 HF path vars, PYTHONPATH) HOME=SCR/home caffeinate -i SBX PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests (15:38:45-15:39:04) | **0: 413 passed**; log: one loopback remote:*:9 denial only |
| 6 | SCR/probe-suite: SEC_MARKS=... HOME=SCR/home caffeinate -i SBX PY -B -m pytest -p no:cacheprovider -q tests (15:43:34); SBX PY -B SCR/tools/show_probes.py | **0: 8 passed**; 43/43 refused at collection and in the thread; no marker |
| 7 | caffeinate -i SBX PY -B SCR/tools/run_sec_mutants.py sec_mutants.json probe-mut/tests/conftest.py ... -- tests (15:44:57-15:45:00) | 0: baseline 0; 12 of 13 killed. **Incident**, see §6 item 1 |
| 8 | the same 13 mutants on the builders' 3 guard files in SCR/suite-mut, -x (15:45:17-15:46:38) | 0: baseline 0; **5 killed, 8 survived** (SCR/sec-mut-builders.json) |
| 9 | caffeinate -i SBX PY -B ws-k2/.../run_mutants_gated_78b.py ws-k2 SCR/mut-gated-sec SCR/mut-gated-sec.json <the 12 non-conftest K4-m ids> --timeout 300 (15:50:44-15:51:44) | **0: baseline 0; 12 of 12 killed** |
| 9b | caffeinate -i SBX PY -B ws-k2/.../run_mutants_runner_78b.py ws-k2 SCR/mut-runner-sec ... K4-m-runner-token-default-path-only,-check-swallowed,-stored-only-default (15:51:51-15:51:58) | **0: 3 of 3 killed** |
| 10 | run_sec_mutants.py sec_mutants_launch.json on launch.py -- test_gated_78b.py (15:49:19) | 0: baseline 0; SEC-m-tls-http-scheme killed; **SEC-m-tls-redirect-handler-opens-https-unverified survived** |
| 10b | run_sec_mutants.py sec_mutants_runner.json on job_runner_stage1.py -- runkit/stage1-78b/tests (to 15:50:20) | 0: SEC-m-runner-wrapper-record-whole killed (2 failed) |
| 11 | SBX PY2 -B -m pytest ... test_gated_78b.py -k "rv2_9 or d6_the_cache" (15:52:10) | 0: 11 passed, 11 skipped (no huggingface_hub) |
| 12 | probes made fully fail-closed (every direct start pre-checked); 13 mutants again (15:56:16-15:56:19) | 0: same verdicts, 12 of 13; **log: no sandbox denial at all** in the window |
| 13 | SBX PY -B SCR/probe/ctypes_gap.py | 0; libc system/connect/getaddrinfo/execv/fork resolve through ctypes, events ctypes.dlopen/dlsym not refused; nothing called but getpid |
| 14 | the whole suite with FAKE values in the 6 token/key vars and HF_HOME=SCR/fakehf (a fake login file) (15:52:24-15:52:50); grep; scan_tars.py | 1: **412 passed, 1 failed** (D4); fake values: 0 in output, 0 in 472 test folders, 0 in 3,671 tar members |
| 14b | that one test with HF_TOKEN_PATH, HF_HOME, XDG_CACHE_HOME each at a fake login, then none | 1 failed, 1 failed, 1 failed, 1 passed |
| 15 | SBX PY -B -m pytest -s ... SCR/suite1 copy's test_sec_pack_inputs.py (15:54:39) | 0: pack not refused; the token-shaped string in 1 bundle member under inputs/ |
| 16 | /usr/bin/log show ... sender Sandbox (several windows) | as quoted per row |
| 17 | find ws-k2 -newer SCR/ws-k2-marker-start (not .git); kit shasum vs #1; git status count; find __pycache__ | 0 files; KIT-UNCHANGED; 55 entries as at start; none |

## 4. Defects (all minor)

- **D1 (test gap, the wrapper).** The builders' guard tests do not pin the process-wide wrapper's address check for
  sendto, sendmsg or AF_INET6 sockets: SEC-m-wrapper-sendto-unchecked, -sendmsg-unchecked and -wrapper-inet-only
  survive the three guard files (M #8); my probes kill all three (M #7, #12). Failure: a later edit drops sendto's
  address in `_checked_socket_method` (conftest.py:190-194); at collection or in a module fixture,
  `socket.socket(AF_INET6, SOCK_DGRAM).sendto(b"x", ("host.example", 53))` makes C resolve the name (one DNS query)
  before the hook refuses; no test fails. Fix: add the 'wrap-*' probes of SCR/probe-suite/tests/test_a_sec_probes.py
  (stand-in pre-check, then the real call, host names on both families) to test_pp10_process_wide.py at collection
  and in its module fixture; add the 3 mutants to mutation_spec_gated_78b.json.
- **D2 (test gap, the hook under the flag, in threads, bytes names).** SEC-m-hook-os-free-under-flag,
  -sockets-free-under-flag, -lookups-free-under-flag, -hook-main-thread-only and -loopback-bytes-any survive the
  builders' files (M #8); my probes kill all five. Failure: an edit makes `_audit` return early while ALLOWED is
  non-empty; inside any local_processes test, `posix.system(...)` or a raw `_socket.socket` connect to a non-loopback
  address goes through (the per-test fixture patches the os and socket.socket names only), against conftest.py:39-42
  ("the network, os.system and multiprocessing stay refused"); no test fails. Fix: add my
  test_sec_under_local_processes_the_os_and_socket_calls_stay_refused, a collection-time thread probe and a bytes
  host-name lookup probe; add the 5 mutants.
- **D3 (RV2-1 test strength).** test_rv2_1 checks the HTTPSHandler instances only (test_gated_78b.py:1373-1395).
  SEC-m-tls-redirect-handler-opens-https-unverified (SameHostAuthRedirect gets handler_order 100 and an https_open
  that uses `ssl._create_unverified_context()`) survives all of test_gated_78b.py (M #10). Failure: that edit sends the
  Bearer token to any TLS peer with no certificate or host-name check; no test fails. Fix: assert that every handler
  in `opener.handle_open["https"]` is an HTTPSHandler whose context is None or verifying, and that
  SameHostAuthRedirect defines no `*_open`; add the mutant.
- **D4 (env isolation; pre-existing at HEAD).** test_kit_78b_runner.py:754
  test_the_preflight_writes_the_speed_and_bank_fields_and_refuses_a_slow_pod sets HOME and removes the token
  variables but not HF_HOME / HF_TOKEN_PATH / XDG_CACHE_HOME, so the preflight's no_token_left() looks at the shell's
  real login path (M #14b: each variable at a stored login fails it). Fails closed and prints a path only (M: no fake
  value in the output). Fix: remove HF_PATH_VARS there as the Pod class does (:180), or better an autouse conftest
  fixture that removes the token variables and the HF path variables for every test.
- **D5 (the pack scans no named input).** inputs/, data/ and edits/ are outside the pack's secret scan
  (pack_setup.py:60, 241-248; unchanged since HEAD). K4b's new inputs (anchor prompts, the 1B lists, pools, the
  retrain unit folder) therefore ship unscanned: M #15 packs a token-shaped string without refusal. Mitigation (R):
  every input is SHA-pinned to a Mac sealed list or to a pod output the finisher scans on pull (finisher.py:236-241).
  Fix: scan the non-binary files under inputs/ (count-only refusal, names only), or the lead rules the exclusion
  stays.

## 5. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Guard holds at collection, module fixture, multiprocessing spawn, os.exec, hostname lookup, AF_INET6 send | passed | M #6, #12 (43 probes, 7 contexts) |
| Guard mutants under sandbox-exec with outbound network denied | passed for the code; **failed for the builders' tests** (8 of my 13 survive them) | M #7, #8, #12; D1, D2 |
| DK-2 exact paths | passed | M #8: popen-argv0 killed by the builders' tests |
| TLS test (RV2-1) | passed for the builders' 3 mutants; **failed** for one handler-order mutant | M #9, #10; D3 |
| RV2-2..RV2-7, RV2-9 | passed | M #9 (12/12), #11, #6 |
| RV2-8 runner token check | passed | R §2 item 5; M #9b (3/3) |
| Scorer pod commands carry no token and no text | passed | R §2 item 6; M #5, #10b, #14 |
| The bundle carries no token | passed for code, settings, payloads (M #14: 0 hits); **not guaranteed for inputs/** | M #15; D5 |
| Whole 7-8B suite passes; no real network or outside process | passed | M #5 (413, under exec+network+DNS deny) |
| Suite independent of the shell's HF paths | **failed** (1 test) | M #14, #14b; D4 |
| CUDA, a real pod, real scorer scripts | not tested | $0 scope |

## 6. Unresolved concerns

1. **Incident in my run #7.** Four direct process probes in my first probe file were not pre-checked. Under mutant
   SEC-m-hook-main-thread-only, the collection-time thread's subprocess, shell and asyncio probes reached exec: the
   kernel denied /bin/sh once and /usr/bin/touch twice (log, 15:44:59 UTC), and (I, from the probe list; not logged
   because the sandbox allows the interpreter) one interpreter child ran `-B -c pass`. No network. I pre-checked
   every start; run #12 logs no denial at all.
2. Documented limits re-confirmed, not defects of K4: ctypes reaches libc's system / connect / getaddrinfo (M #13;
   hardening: refuse `ctypes.dlsym` of those names); a host name given to a raw `_socket.socket` resolves before the
   hook (not run; K4a's M); children of local_processes programs are unguarded (M #5: today's two start nothing).
   AF_UNIX connects are allowed to any path, so a DNS-SD client could talk to /var/run/mDNSResponder directly (I).
3. Outside K4's items (R): the RunPod key's calls (host.py:102-114, budget.py:47-49, account.py:18-21) use urllib's
   default redirect handler, which copies the Authorization header to a redirect target on another host; only the HF
   token's http_get drops it (launch.py:63-73). Pre-existing.
4. Each scorer step's process.log (process_receipt.py) keeps the step's whole stdout and stderr and is pulled back with
   the tree; whether it holds text depends on the scorer layer's printing (not checked here).
5. `top_dose` passes any "s4" plus up to 10 characters of [a-z0-9_] (job_runner_stage1.py:634-636; plan_tool.py:1527):
   a tiny channel, no realistic leak (I).

## 7. Jobs for the lead

1. Rule on D1-D5. For D1-D3 the probes and mutants are ready: SCR/probe-suite/tests/test_a_sec_probes.py (fail-closed),
   SCR/tools/sec_mutants.json, sec_mutants_launch.json. Run any guard mutants only under SBX's profile
   (SCR/deny-all.sb) and with every start pre-checked.
2. Delete after review: SCR (k4-sec-scratch/: two kit copies, basetemps, results; evidence only).
