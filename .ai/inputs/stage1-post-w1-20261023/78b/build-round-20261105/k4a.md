# K4a: the kit's minor items (round 4)

Started 2026-11-06 13:35 UTC; this version written 14:22 UTC (`date -u` read right before each write).
Worktree ws-k2 (HEAD d203070, clean at the start; M `git status`). Status: **DONE**.
Scratch: reports/k4a-scratch/ (SCR). PY = the main venv (3.11.15, huggingface_hub installed); PY2 = .venv (no hub).
Tags: M measured (command in the table), R read (path:line), E estimate, I inference.

## 1. Files changed (all under runkit/stage1-78b/; nothing committed; no git state changed)

| File | What changed | SHA-256 |
|---|---|---|
| rules_78b.py | PP16 `X_ONLY_KINDS` + `engine_allowed` checks it first; the key-check message names PP16; PP14 `IDLE_RETRAIN_WHY`, `IDLE_SCORER_KINDS`, `idle_storage_pods()`, `idle_storage_lines()`, `block0_report` keys `idle_storage_pods` / `idle_storage_all` | a81ef207... |
| stage1_rules.py | `block0_need_report` prints `r78.idle_storage_lines(report)` (N's D2 line unchanged, then PP14's 5) and returns the two new keys | b1198e6e... |
| plan_tool.py | init-block 0's summary JSON carries `idle_storage_pods`, `idle_storage_all` | af18b05c... |
| setup/job_runner_stage1.py | RV2-8: `token_paths()` loads download_models_stage1.py by path once; the pre-job check calls its `no_token_left()` (refusal re-raised as AssertionError "a token is present: ...") | ff4e116b... |
| tests/conftest.py | DK-1 process-wide layer (audit hook, fork_exec refusal, socket.socket wrappers, shared flag ALLOWED, SEEN record); fixture kept, plus RV2-7 (executable=, getnameinfo); flag cleared at test end | a1706a29... |
| tests/test_pp10_process_wide.py (new) | DK-1, DK-2, RV2-7 tests (48) | 00c3d602... |
| tests/test_pp10_guard.py | RV2-6 (identity checks before probes, loopback targets), RV2-7 (IPv6 datagrams, getnameinfo) | 564f7e93... |
| tests/test_gated_78b.py | RV2-1 test; RV2-2 `_no_fragment` + new test; RV2-3 five codes in both redirect tests; RV2-4 names hardcoded + `variable-hub` case; RV2-5 five staging values; RV2-9 by-hand paths test | 6ef9d0ff... |
| tests/test_rules_78b.py | test_07c updated for PP16; new tests 20 (PP16), 21 (DK-3), 22 (PP14); test_13 requires K4 ids | 6dabc2df... |
| tests/test_kit_78b_runner.py | RV2-8 test; Pod clears the HF path variables | f609196d... |
| tests/test_kit_78b_shell.py, tests/test_stage1_runkit.py | need-printout line counts and PP14 lines / JSON | 4d2c076c..., 4dcb42b8... |
| tests/run_mutants_gated_78b.py | also runs the two guard test files; refuses a Python without huggingface_hub (RV2-9); sandbox line in the doc | 9046941f... |
| tests/mutation_spec_{rules,runner,gated}_78b.json | +23, +3, +46 K4-m-* mutants (103, 31, 106) | ec8b5308..., 1151cdfd..., bf45ab38... |
| README.md, RULES-78B.md | the two layers, PP14, PP16, test and mutant counts | 4537cb35..., db06da22... |

Git-ignored, not for merge: ws-k2/tmp/engine-y-34bfd288 (67 MB, copied from the main checkout's tmp/ for the
stage-1 kit's suite; 3,848 files byte-identical, M: shasum lists in SCR/ey-*.sha; no selector or hidden file, M: find).

## 2. Items, change and evidence

- **DK-1** (conftest process-wide). Audit hook installed at import (once per process; state on `sys`), refusing:
  `subprocess.Popen` unless the EXECUTABLE (executable= or argv[0]) is exactly in ALLOWED (the flag
  `local_processes` fills; emptied at each test's end); `os.system`, `os.exec`, `os.posix_spawn`, `os.spawn`,
  `os.fork`, `os.forkpty`; `socket.connect/sendto/sendmsg` except unix sockets, None and loopback; the five lookups
  except loopback (and None for getaddrinfo); every `urllib.Request`; `http.client.connect` to non-loopback. Beside it:
  `_posixsubprocess.fork_exec` replaced (multiprocessing has no event; subprocess keeps its own bound `_fork_exec`, M:
  subprocess.py:104) and `socket.socket`'s four methods wrapped, because CPython parses (resolves) the address before
  the connect/sendto event (M: SCR/probe/order.py: a bad port fails with no event). Event names wired (M:
  SCR/probe/os_events.py: os.system, os.exec, os.posix_spawn(p), os.fork via spawnv, os.forkpty, the lookups,
  urllib.Request, http.client.connect). Evidence: test_pp10_process_wide.py (collection-time and module-scoped probes,
  each event by hand, real calls past the fixture, multiprocessing spawn, wrappers); 26 hook mutants killed.
- **DK-2**: `test_dk2_local_processes_opens_exact_paths_only_in_both_layers` (base-name lookalikes in tmp_path, a
  shell, executable= behind an allowed argv[0]; each layer's own message). Killed: K4-m-guard-hook-by-base-name,
  K4-m-guard-fixture-by-base-name (the re-verifier's RV2-8 survivor), K4-m-guard-fixture-any-under-local.
- **DK-3**: test_21 loads the kit's stage1_rules.py and asserts rep_pass, a1_pass, classifier in UNITLESS_KINDS and
  DIAG_KINDS. Killed: 6 K4-m-unitless/diag-* (incl. the re-verifier's RV2-9 survivor form).
- **DK-4 / PP16**: `X_ONLY_KINDS` = the lead's 8 kinds; `engine_allowed` returns `engine == X` for them first.
  test_20 fills ENGINE_Y test-locally (and Y_MEASURED) and checks every wrapper kind refuses on Y and a third engine,
  runs on X, and retrain / a1_pass run on Y. test_07c's old line "anchor runs on Y" now expects the PP16 refusal.
  Killed: 12 K4-m-x-only-* (off, any engine, after Y, retrain added, each of the 8 kinds dropped).
- **RV2-1**: `test_rv2_1_http_get_verifies_the_hubs_tls_certificate_and_host_name` (every HTTPS handler of the real
  openers verifies or uses the default; ssl's default factory is `create_default_context`, CERT_REQUIRED,
  check_hostname). Killed: K4-m-tls-handler-unverified, -handler-no-hostname, -default-context-unverified.
- **RV2-2**: `_no_fragment` (token, token[3:], both halves) in test_d4; new test (non-HF token through http_get;
  token across character 200 at 185/190/199). Killed: K4-m-http-get-failure-text-without-token,
  -failure-text-truncates-before-scrub, -noreply-line-echoes-token-unprefixed-at-end.
- **RV2-3**: both redirect tests over 301, 302, 303, 307, 308. Killed: K4-m-redirect-302-only, -307-308-kept.
- **RV2-4**: names hardcoded; D2 case `variable-hub`. Killed: K4-m-dl-one-token-variable.
- **RV2-5**: staging "1", "true", "yes", "ON", "True". Killed: K4-m-dl-staging-only-value-1.
- **RV2-6**: guard tests check each callable is replaced before probing; connect probes aimed at 127.0.0.1:9; the
  sentinels cover getnameinfo. Killed: K4-m-guard-fixture-no-connect, -no-gethostbyname, -no-opener,
  -no-create-connection (each by the identity check, before any call).
- **RV2-7**: IPv6 datagram cases, getnameinfo, /bin/sh and executable= under local_processes. Killed:
  K4-m-guard-fixture-sendto-inet-only, -no-getnameinfo, -executable-unchecked, -any-under-local.
- **RV2-8**: runner check via `no_token_left()`; test_rv2_8 (HF_HOME, XDG_CACHE_HOME, HF_TOKEN_PATH, each token file
  and stored_tokens; both variables). Killed: K4-m-runner-token-default-path-only (the old code), -check-swallowed,
  -stored-only-default.
- **RV2-9**: `test_rv2_9_the_cache_and_token_paths_by_hand_without_the_library` (11 cases) + the runner refuses a
  Python without huggingface_hub. Under PY2 (M, #16): baseline 11 passed, 11 skipped; K4-m-dl-no-expandvars and
  K4-m-dl-xdg-over-hf-home each 1 failed (killed). PY2 runner refusal exit 1, no scratch made (M, #15).
- **PP14**: idle lines: N's (D2, unchanged), retrain olmo2-7b, retrain llama31-8b, scorer olmo2-7b a1_pass, scorer
  llama31-8b a1_pass ($0.33/day, $10/month each), and "block 0 in all: 6 pods, $2.00 per day, about $60 per month";
  JSON keys in the report and the summary. test_22 + shell / runkit tests. Killed: 5 K4-m-idle-*.

## 3. Commands (all foreground; exit status)

| # | Command | Result |
|---|---|---|
| 1 | `date -u` before each time written (13:35:19, 13:40:28, 13:50:01, 14:00:04, ..., 14:22:35) | 0 |
| 2 | PY -B -m pytest -p no:cacheprovider runkit/stage1-78b/tests (baseline, before changes) | 0: 288 passed |
| 3 | PY -B -I SCR/probe/order.py; PY -B -I SCR/probe/os_events.py | 0, 0 (event order and names, §2) |
| 4 | whole 7-8B suite after each step | 0: 292, 314, 362 passed |
| 5 | python3 -B SCR/add_mutants.py <kit> (each find exactly once, asserted) | 0: 103 / 31 / 106 |
| 6 | `caffeinate -i PY -B tests/run_mutants_78b.py ws-k2 SCR/mut-rules SCR/mut-rules.json ALL --timeout 300` (14:00:28-14:01:00) | **0: baseline 0 (36 passed); 103 of 103 killed** |
| 7 | `caffeinate -i PY -B tests/run_mutants_runner_78b.py ... SCR/mut-runner ... ALL` (14:01:08-14:01:55) | **0: baseline 0 (50 passed); 31 of 31 killed** |
| 8 | the gated runner under SANDBOX, the 34 conftest ids (14:02:07) | 2: baseline failed (a loopback sendto gets EPERM under the sandbox); test fixed, nothing counted |
| 9 | the whole suite under SANDBOX | 0: 362 passed |
| 10 | gated runner under SANDBOX, 34 conftest ids (14:02:49-14:05:45) | 0: 34 killed; see incident §6 item 1; superseded by #12 |
| 11 | `log show` of sandbox denials (counts) for #10 and #12 windows | #10: 1 remote:*:22, 13 remote:*:9; #12: 13 remote:*:9 only |
| 12 | `caffeinate -i sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))' PY -B tests/run_mutants_gated_78b.py ws-k2 SCR/mut-gated-b SCR/mut-gated-b.json <34 ids> --timeout 300` (14:07:05-14:10:02), after the probes were made fail-closed | **0: baseline 0 (189 passed); 34 of 34 killed** |
| 13 | the same, the other 72 ids (SCR/mut-gated-a; 14:11:02-14:15:03) | **0: baseline 0 (189 passed); 72 of 72 killed**; denials: 2 remote:*:9 |
| 14 | the whole gated spec in total | 106 of 106 killed, 0 invalid (#12 + #13, same baseline command) |
| 15 | `PY2 -B tests/run_mutants_gated_78b.py ... BASELINE` | 1: refused (no huggingface_hub), no folder made |
| 16 | `PY2 -B -I SCR/py2_rv2_9.py ws-k2 SCR/mut-py2-rv2-9 PY2` | 0: baseline 0; both D6 mutants killed (§2) |
| 17 | `git diff --quiet HEAD -- runkit/stage1-olmo` | 0 (unchanged) |
| 18 | stage-1 kit suite without tmp/engine-y (14:15:55) | 1: 8 failed, 2 errors (missing fixture tmp/engine-y-34bfd288; not a code result) |
| 19 | `cp -R -p` main tmp/engine-y-34bfd288 into ws-k2/tmp; shasum lists compared | 0: 3,848 files identical |
| 20 | `caffeinate -i PY -B -m pytest ... runkit/stage1-olmo/tests` (14:18:36-14:19:18) | **0: 762 passed** |
| 21 | the whole 7-8B suite under SANDBOX, then plain (14:19:28-14:19:55) | **0: 362 passed; 0: 362 passed**; no __pycache__ (M: find) |
| 22 | the suite with a recording audit plugin (SCR/probe/k4a_audit.py) | 0: 362 passed; events in SCR/suite-audit.json (includes the by-hand events; not decisive alone) |
| 23 | `sandbox-exec -f SCR/deny-net-exec.sb` (exec denied except the interpreter and git; outbound IP denied): control `/usr/bin/true`, then the whole suite (14:20:46-14:21:00) | control: PermissionError (logged `deny process-exec* /usr/bin/true`); suite **0: 362 passed**; log: no other process-exec denial, 2 remote:*:9 (loopback probes) |
| 24 | both suites in ONE pytest process | 2: 13 collection errors, 9 "import file mismatch" (same test basenames in both folders; I: pre-existing, run them separately) |

## 4. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| DK-1 process-wide guard (collection, module fixtures, spawn, direct os calls, all listed calls) | passed | test_pp10_process_wide.py; 26 hook mutants killed (#12) |
| DK-2 exact-path test | passed | test_dk2...; 3 mutants killed |
| DK-3 kind-set test | passed | test_21; 6 mutants killed (#6) |
| DK-4 / PP16 X_ONLY_KINDS first, test with ENGINE_Y test-local, mutant | passed | test_20, test_07c; 12 mutants killed |
| RV2-1 TLS pin | passed | test_rv2_1; 3 mutants killed (#13) |
| RV2-2..RV2-7, RV2-9 test additions | passed | §2; 16 mutants killed; RV2-9 also under PY2 (#16) |
| RV2-8 runner uses no_token_left() | passed | test_rv2_8; 3 mutants killed (#7) |
| PP14 idle lines in printout and JSON | passed | test_22, shell test; 5 mutants killed |
| Mutation specs updated; three runners all killed, zero invalid, baseline same command | passed | #6 103/103, #7 31/31, #12+#13 106/106 |
| Guard mutants under the sandbox | passed | #12 (and #10, superseded) |
| Whole 7-8B suite passes | passed | #21: 362 passed (plain and sandboxed) |
| runkit/stage1-olmo unchanged and its suite passes | passed | #17, #20: 762 passed (with the copied fixture) |
| No real network or outside process in any test | passed for the passing suite (M #23); one mutant-run connect attempt was kernel-denied (§6 item 1) | #11, #23 |

## 5. Jobs for the lead

1. Merge by explicit paths: the 17 modified files of §1 and the new `runkit/stage1-78b/tests/test_pp10_process_wide.py`.
2. After the merge, in the main checkout: `PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests` (expect
   362 passed) and the stage-1 kit's suite in a separate process (expect 762). Not measured there.
3. Rule on concerns 2 and 3 (o_only_with_regenerate; which scorer pods keep states).
4. Delete after the merge: ws-k2/tmp/engine-y-34bfd288 (67 MB copy) and reports/k4a-scratch/ (2.2 MB; JSON results
   and probe scripts are evidence only).
5. Run the gated spec only with PY and under the sandbox line (the runner now says so and refuses PY2).

## 6. Unresolved concerns

1. **Incident (mutation run #10).** Under mutant K4-m-guard-loopback-any-ip (every IP taken as loopback), a
   collection-time probe made a real TCP connect attempt to 203.0.113.9:22. The sandbox denied it in the kernel
   (log: one `deny network-outbound remote:*:22` at 14:04:05 UTC), so no packet left (M). I then made every real
   non-loopback socket probe run only after the same event raised by hand is refused (and the address is not taken
   as loopback); re-run #12 shows only port-9 loopback denials (M). Equivalent risk remains only if a mutant breaks
   sys.audit's own path in a way the by-hand check does not see (I: none in the spec).
2. PP16's list leaves `o_only_with_regenerate` (an E kind made of two X-only kinds), `safe_lora`, `ref_eval` and
   `ref_train_bqi` allowed on Y once ENGINE_Y is filled. I kept the lead's list exactly; the lead should say whether
   `o_only_with_regenerate` joins it.
3. PP14's scorer pods "that keep states": I chose `a1_pass` only (I: the one scorer kind whose input is the retrain's
   q and e1 states). It is a named constant, `IDLE_SCORER_KINDS`; the lead names any other.
4. plan_tool.py (copied from the 1B kit) still holds `rules.X_ONLY_KINDS = ()` and a check that "retrain ... runs on
   engine X" (R: plan_tool.py:727-731), which contradicts ruling 10; later-round paths, not changed here.
5. The runner now loads download_models_stage1.py at its first token check, which sets HF_HUB_DISABLE_TELEMETRY=1 and
   HF_HUB_DISABLE_IMPLICIT_TOKEN=1 in the runner's environment, so engine jobs inherit them (I: harmless). The old
   clause for ~/.cache/huggingface/token is gone; with HF_HOME / XDG_CACHE_HOME / HF_TOKEN_PATH set elsewhere a file at
   the default path is not the library's file and is no longer refused.
6. Guard limits (documented in conftest.py): ctypes or another C extension; a direct call of subprocess's private
   `_fork_exec`; a host name given to a bare `_socket.socket` (one DNS query before the hook refuses); the children of
   `local_processes` programs; `os.posix_spawn` refused even under `local_processes` (as the fixture already did).
7. The hook stays for the whole pytest process. The two kits' suites cannot share one pytest process anyway (#24).

Finished 14:22 UTC. No pod, spend, network, install, download, agent or message; no secret read; no git state changed;
the main checkout read only (the engine-y fixture copied from its tmp/).
