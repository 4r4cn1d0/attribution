# Re-verify K gated (security re-verify of the fix-K-gated round)

Started 2026-11-06 08:04:30 UTC; this version written 2026-11-06 13:21 UTC (`date -u` read right before the write).
Second re-verifier for this track. The first one (skeleton of 02:50 UTC, kept at SCR2/earlier-skeleton-by-first-reverifier.md)
stopped on Fable's weekly limit (PP13); its scratch files were read as data only.
Worktree (read-only for me; HEAD f5e3b4c): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-k ("ws-k")
Scratch (SCR2): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/reverify-K-gated-scratch/r2
PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (3.11.15, huggingface_hub 0.36.2,
hf_xet present); PY2 = /Users/spiderishi/Coding/attribution/.venv/bin/python (3.11.15, no huggingface_hub).
SANDBOX = `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'` (M: under it a loopback
connect gives EPERM, without it ECONNREFUSED; so no IP packet can leave any process of the tree). Every pytest run:
`env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN PYTHONDONTWRITEBYTECODE=1`, `-B`, `-p no:cacheprovider`, cwd ws-k.

Tags: M measured (command in section 6), R read (path:line), E estimate, I inference.

## 0. Verdict

**VERIFIED_WITH_MINOR.** I found no path by which the token leaks or goes to a wrong host in the code after the fixes.
The fixers' claims hold where I measured them: the kit's gated spec 60 of 60 killed, the verifier's 12 of 12, the first
re-verifier's 19 of 19 (M). The code is right on the real network stack too: on loopback the real opener drops the
Authorization header on every off-origin redirect code (301, 302, 303, 307, 308) and keeps it on the same origin; real
refused, reset and TLS failures become NO_REPLY with no token in the detail; real http.client header errors are
withheld (M). PP10 holds for the baseline suite: 288 passed with outbound IP denied for the whole process tree, no
non-loopback network call reached the C layer, the only real children were 18 runs of the kit's interpreter in 11
`local_processes` tests, and the kernel logged no denial during the run (M).

But 10 of my 23 hand mutants survive the whole suite (M). Each is a test gap over code that is right today. The most
important: no test pins TLS certificate verification on `http_get` (RV2-1). Nine minor defects in all (section 8).
None blocks the merge. I would fix RV2-1 before the first Llama launch.

## 1. Files changed

None under ws-k (M: `git status --porcelain --ignored` and the SHA-256 of every kit file identical before and after; no
`__pycache__`). My writes: this report and SCR2 only.

## 2. Hand mutants (my own, RV2-m-*; spec SCR2/hand_mutants_rv2.json, SCR2/hand_mutants_rv2b.json)

Driver: SCR2/run_hand_mutants.py, a byte copy of verify-K-gated-scratch/run_hand_mutants.py (SHA-256 d440a5e0..., M),
which reuses the kit's runner (copy, run, verdict: killed only on exit 1 with a FAILED line and no ERROR line).
Every run under SANDBOX. Baselines all exit 0 (gated file 111 passed; whole suite 288 passed; PY2 gated file 100 passed,
11 skipped). Every find text occurs once (M: SCR2/make_spec.py asserts it).

| Id | Weakens | Gated file | Whole suite |
|---|---|---|---|
| RV2-m-tls-handler-unverified | http_get's HTTPS handler verifies no certificate | survived | **survived** |
| RV2-m-tls-default-context-unverified | launch.py sets ssl's default HTTPS context to unverified | survived | **survived** |
| RV2-m-http-get-failure-text-without-token | http_get calls failure_text(exc, "") (the pattern alone scrubs) | survived | **survived** |
| RV2-m-failure-text-truncates-before-scrub | failure_text cuts to 200 before the scrubs | survived | **survived** |
| RV2-m-redirect-302-only | the header is dropped on a 302 only | survived | **survived** |
| RV2-m-same-origin-port-ignored | same_origin ignores the port | killed (test_d5) | - |
| RV2-m-same-origin-suffix | any host ending in the original host is "same" | killed (test_d5) | - |
| RV2-m-header-safe-allows-del | DEL passes header_safe | killed (test_f1 [delete]) | - |
| RV2-m-header-safe-checks-ends-only | header_safe checks the first and last character | killed (test_f1 [bell]) | - |
| RV2-m-scrub-on-success-only | the scrub leaves `finally` | killed (test_d4 [dns]) | - |
| RV2-m-noreply-line-echoes-token-unprefixed | the whoami no-reply line prints token[3:] before "(" | killed (by the message regex, not by a leak check) | - |
| RV2-m-noreply-line-echoes-token-unprefixed-at-end | the same line ENDS with token[3:] | - | **survived** |
| RV2-m-dl-one-token-variable | the pod script drops HUGGING_FACE_HUB_TOKEN from its list | survived | **survived** |
| RV2-m-dl-no-expandvars | _hf_path does not expand $VAR | killed (test_d6 [tilde-and-var]); **survived under PY2** | - |
| RV2-m-dl-xdg-over-hf-home | XDG_CACHE_HOME before HF_HOME | killed (test_d6 [hf-home-over-xdg]); **survived under PY2** | - |
| RV2-m-dl-staging-only-value-1 | the staging refusal fires for "1" only | survived | **survived** |
| RV2-m-dl-postcheck-skips-stored-tokens | the after-download check skips stored_tokens | killed (test_d2 [stored-tokens]) | - |
| RV2-m-dl-cache-scan-skips-refs | the cache scan reads snapshots/ only | killed | - |
| RV2-m-dl-pod-header-check-allows-control | the pod lets control characters but the line break through | killed (test_f1 pod) | - |
| RV2-m-preflight-hygiene-default-token-file | the preflight checks the default token file only | killed (test_d6 token path) | - |
| RV2-m-guard-sendto-inet6-open | the datagram guard refuses AF_INET only | - | **survived** |
| RV2-m-guard-popen-allows-any-under-local | under local_processes any program not in NEVER passes | - | **survived** |
| RV2-m-guard-connect-ex-open | connect_ex not guarded | - | killed, but only after a real outbound connect (RV2-6) |

Totals (M): 23 mutants; 13 killed; 10 survive the whole suite under PY; 2 more survive under PY2.
Re-runs of the others' mutants (M): the kit's gated spec ALL: baseline 0 (111 passed), **60 of 60 killed**
(08:15:20-08:21:27 UTC); the verifier's hand_mutants.json: **12 of 12 killed** (V-m-http-get-no-redirect-handler and
V-m-dl-post-check-dropped included); the first re-verifier's hand_mutants_rv.json: **19 of 19 killed**
(RV-m-d4-exact-value-not-replaced and RV-m-d4-pattern-not-replaced included).

None of the 10 survivors is an equivalent mutant: each changes what reaches the network or a log for some input (I,
argued per item in section 8).

## 3. Token trace after the changes (R unless marked)

1. **The Mac shell -> launch.py.** Read once: `gated_precheck`, launch.py:185 (`os.environ.get("HF_TOKEN", "").strip()`;
   HUGGING_FACE_HUB_TOKEN is never read). Empty refuses (186-188). `token_checks` refuses a non-visible-ASCII value
   before any request (130-133; F1); the message names no part of it.
2. **launch.py -> the Hub.** `http_get` (87-103): the token goes into this request's Authorization header only (93); the
   opener is built at the call with SameHostAuthRedirect (94), timeout 60 s (96). SameHostAuthRedirect (63-73) deletes
   the header when (scheme, netloc) changes (56-60). M (loopback, real stack): same origin kept; 301/302/303/307/308 to
   another port dropped. TLS: the opener's default HTTPSHandler uses ssl's default context (I); M: PY's default context
   is CERT_REQUIRED with check_hostname True and 128 CA certificates from /private/etc/ssl/cert.pem; no SSL_CERT_*,
   proxy or CA variable in my environment (count 0, values not printed). No test pins this (RV2-1).
3. **The new error paths.** HTTPError -> (code, b"") (98-99). URLError, OSError, HTTPException -> (0, failure_text)
   (100-101): class and reason, the exact value and any `hf_` + 30 alphanumerics replaced, then cut to 200 (76-84).
   ValueError (header check, non-latin-1) -> (0, "<class>: ... (detail withheld)") (102-103). token_checks turns 0 into a
   SystemExit line for whoami (135-137) and stops at the first Range request with no reply (157-160). The line goes to
   stderr (launch-0.log); token-check.json is not written on a refusal (189-193 run only after token_checks returns).
   M (loopback): refused -> URLError, closed -> ConnectionResetError, TLS to a plain server -> URLError; no token or
   token[3:] in any detail; real http.client ValueError and UnicodeEncodeError -> "detail withheld"; token_checks refuses
   both before any request. A short body read with `read(limit)` gives (200, short body), not an error (M; harmless).
4. **launch.py's children.** reconcile, budget check, create: `env=clean_env()` (274-289) = the two names and any
   HF-shaped value removed (secret_scan.py:12-15). The detached orchestrate child gets the whole environment for Llama
   only (199-202, 293-294). The scrub runs in `finally` (252-253), so also after every new refusal (M: test_d4 and
   RV2-m-scrub-on-success-only killed).
5. **orchestrate.py** (unchanged since the verifier; M `cmp` with the verifier's pre-fix copy). Reads the token at 102,
   hands it over at 109 as `tool(..., stdin_text=token + "\n")`; `tool` (137-138) runs host.py with `clean_env()`; the
   token is dropped at 110-111. The only subprocess call in the module (M grep). gateb_mac.py, probes.py,
   stage1_rules.py, secret_scan.py spawn nothing (M grep). Observation: there is no try/finally around 109, so an
   exception from `tool()` keeps the token in this process's environment through `after_create`'s handler (463-485;
   its children get `clean_env()`) until the process exits; nothing writes it (I). `after_create` logs
   `str(exc)[-300:]` (479); no exception on this path carries the stdin text (I).
6. **host.py** (unchanged; M `cmp`). `main` reads one stdin line (453); `gated_download` (404-416) writes it to ssh's
   stdin only, with `clean_env()`; the ssh output is captured and dropped; the record is {utc, ok, exit, attempt}.
7. **The pod: download_models_stage1.py.** HF_HUB_DISABLE_IMPLICIT_TOKEN=1 at import (47); endpoint and staging checks
   (52-61, 213), `no_token_left()` (214) before stdin is read; the line is stripped (217), refused if empty (218-219)
   or not visible ASCII (220-223, F1). `token=` to snapshot_download for gated entries, `False` for open ones (133-135).
   In `finally`: the receipt with ok false (238), `token = None`, `no_token_left()` again (240), the cache scan (241).
   Library facts (R, 0.36.2): the cache and token paths match the kit's resolver (constants.py:129-186); staging moves
   the token path (188-194); stored logins live at HF_TOKEN_PATH and HF_STORED_TOKENS_PATH only (utils/_auth.py:121-137,
   _login.py:462); HF_DEBUG's curl log hides the Authorization header (utils/_http.py:573-575); hf_xet 1.6.0 is pinned
   on the pod (experiments/minimal_safety/requirements.lock:6) and receives the Xet access token, not the HF token
   (file_download.py:598-640). Observation: if the after-download check raises while a download error propagates, the
   SystemExit replaces it and the first error is not printed (I; diagnostics only).
8. **preflight_stage1.py** (changed by the first attempt). It now imports download_models_stage1 (40) and calls its
   `no_token_left()` (83-89). Side effect: the import sets HF_HUB_DISABLE_TELEMETRY=1 and HF_HUB_DISABLE_IMPLICIT_TOKEN=1
   in the preflight and so in its children's environment (158-160). The engine records only HF_HUB_OFFLINE and
   TRANSFORMERS_OFFLINE (R experiments/minimal_safety/model.py:426-427), so no recorded field changes (I).
9. **job_runner_stage1.py** (unchanged). Its pre-job check still looks at `~/.cache/huggingface/token` only (320-321):
   D6 did not reach this third copy (RV2-8).
10. **Scan of my outputs.** SCR2 (13,122 regular files, links not followed): 0 HF-shaped strings and 0 `Bearer` +
    30 characters (M); a control file gave 1 hit (M).

## 4. New error paths

All covered in section 3 items 3 and 7. Every new refusal is a SystemExit line with no token (M by the tests and my
loopback run). Gaps in the tests, not the code: RV2-2 (three leak-assertion survivors) and RV2-3 (redirect codes).

## 5. PP10 guard coverage on the gated path

- **Baseline (M).** SCR2/audit_pytest.py runs pytest under a CPython audit hook that records every process start and
  network call reaching the C layer (names, hosts, program basenames only). Whole suite under SANDBOX: **288 passed**;
  events: 18 `subprocess.Popen` (all `python`, in 11 tests that request `local_processes`), getaddrinfo `localhost` and
  None, gethostbyname `127.0.0.1`, one AF_UNIX `sendmsg` (the guard test's socketpair), and one `http.client.connect`
  audit event for huggingface.co:443 that the guard then stopped at `create_connection` (no lookup and no socket
  followed). No non-loopback connect, lookup or datagram; no ctypes load; nothing outside a test. The unified log shows
  **no sandbox network denial during the run** (the only denials in the window are my own loopback probe and the
  RV2-6 mutant). So no process of the tree, children included, tried to reach the network.
- **The gated path's own calls.** launch.http_get and host.api end in `OpenerDirector.open` (refused); ssh, scp,
  caffeinate and the durability script go through `Popen.__init__` (refused); `launch.main`'s `run=subprocess.run` and
  `popen=subprocess.Popen` defaults are bound at import but still pass through the patched `__init__` (I, R conftest.py:79);
  the real snapshot_download would stop at the guarded lookup (test_g1_g4 http libraries, M in the suite).
- **Limits.** RV2-6 (the guard's own tests reach the network under a weakened guard) and RV2-7 (untested or open forms).

## 6. Commands run (exit status; foreground unless said)

| # | Command | Exit / result |
|---|---|---|
| 1 | `date -u` (08:04:30, 08:05:07, 08:14:06, 08:14:14, 08:14:41, 08:15:20, 08:21:27, 08:25:27, 08:28:02, 08:28:21, 08:31:59, 08:32:07, 08:32:21, 08:34:06, 08:35:10, 08:36:07, 08:37:00, 08:37:28, 08:40:30, 08:40:42, 08:41:19, 12:33:19, 13:19:25, 13:21:04 UTC) | 0 |
| 2 | Reads: lead rulings part 2 (PP7-PP13), verify-K-gated.md, fix-K-gated.md, the first re-verifier's skeleton and hand_mutants_rv.json; launch.py, download_models_stage1.py, preflight_stage1.py, conftest.py, test_gated_78b.py (1-130, 150-242, 600-1354), test_pp10_guard.py, run_mutants_gated_78b.py, host.py and orchestrate.py (token parts), job_runner_stage1.py:285-330, README.md:36-48, 150-175; huggingface_hub constants.py, utils/_http.py, utils/_auth.py, _login.py, file_download.py (greps and ranges) | 0 |
| 3 | `cmp` of 10 kit files against the verifier's pre-fix copy (verify-K-gated-scratch/mut-k3-rerun/repo); `diff` of preflight_stage1.py | 0 (orchestrate, host, secret_scan, job runner, finisher, probes, backup, setup_and_fetch the same); diff exit 1 (the expected change) |
| 4 | Greps over the kit (spawn, socket, multiprocessing, ctypes, asyncio, getnameinfo; importers of the download script; the engine's environment record) | 0/1 as expected |
| 5 | PY/PY2 versions; `sandbox-exec ... /bin/echo` | 0 |
| 6 | Loopback connect to 127.0.0.1:9 with and without SANDBOX | 0: EPERM inside, ECONNREFUSED outside |
| 7 | `git status --porcelain --ignored`, SHA-256 of every kit file (before) | 0 |
| 8 | `SANDBOX PY -B SCR2/audit_pytest.py SCR2/audit-suite.json -- -p no:cacheprovider -q -rfE --basetemp SCR2/pt-audit-suite runkit/stage1-78b/tests` | **0: 288 passed** (08:14:14-08:14:41) |
| 9 | `log show` (sandbox network denials; counts and the deny lines only) three times | 0 |
| 10 | `SANDBOX PY -B runkit/stage1-78b/tests/run_mutants_gated_78b.py <ws-k> SCR2/mut-gated-all SCR2/mut-gated-all.json ALL --timeout 240` | **0: baseline 0, 60 of 60 killed** |
| 11 | `PY2 -B -I SCR2/make_spec.py <kit> SCR2/hand_mutants_rv2.json` (twice, after two edits of the script) | 0: 22 mutants, each find once |
| 12 | `SANDBOX PY -B SCR2/run_hand_mutants.py <ws-k> SCR2/mut-rv2-gated ... --only <19 code mutants>` | 0: baseline 0; 12 killed, 7 survived |
| 13 | the same, `--all-tests --only <the 7>` (SCR2/mut-rv2-full) | 0: baseline 0 (288 passed); 7 survived |
| 14 | the same, `--all-tests --only <3 guard mutants>` (SCR2/mut-rv2-guard) | 0: baseline 0; 1 killed, 2 survived |
| 15 | the same with SCR2/hand_mutants_rv2b.json, `--all-tests` (SCR2/mut-rv2b-full) | 0: survived |
| 16 | `SANDBOX PY2 -B SCR2/run_hand_mutants.py ... --only RV2-m-dl-no-expandvars,RV2-m-dl-xdg-over-hf-home` (SCR2/mut-rv2-py2) | 0: baseline 0 (100 passed, 11 skipped); 2 survived |
| 17 | `PY2 -B -I -c` identity check: socket.gethostbyname/_ex/gethostbyaddr are the _socket functions; a sentinel on _socket leaves them unchanged | 0 |
| 18 | TLS trust store of PY, PY2, /usr/bin/python3 (`cert_store_stats`, verify mode) | 0 |
| 19 | `SANDBOX`(loopback allowed) `timeout 120 PY -B -I SCR2/loopback_real_stack.py <kit>` | 0 (SCR2/loopback_real_stack.out) |
| 20 | `git status --porcelain --ignored` and kit SHA-256 (after, twice); `git diff --quiet HEAD -- runkit/stage1-olmo`; `find ... __pycache__` | 0: identical; 0; 0 folders |
| 21 | `PY2 -B -I SCR2/scan_hf.py` on a control file, then on SCR2 (twice) | 0: control 1 hit; SCR2 0 hits |
| 22 | `SANDBOX PY -B SCR2/run_hand_mutants.py ...` the verifier's hand_mutants.json, then the first re-verifier's hand_mutants_rv.json (one shell command) | 0: 12 of 12 killed; 19 of 19 killed. **Rule breach:** the harness moved this command to the background after 590 s; it ran 08:41:19-13:08:00 UTC (about 4.5 h for 31 mutants that take about 4 min; I: the Mac slept). I did not end my turn while it ran and read its result after it exited |

No command read a secrets file, a token file or a token variable. No git state changed. Nothing written under ws-k.

## 7. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| D1: a test for http_get's opener; the verifier's no-handler mutant dies | **passed** (gap RV2-1) | M: V-m-http-get-no-redirect-handler, FG-m-http-get-no-redirect-handler, RV-m-d1-* killed; TLS verification untested |
| D2: the download leaves a token behind; the post-check refuses; its mutant dies | **passed** | M: V-m-dl-post-check-dropped, RV-m-d2-*, RV2-m-dl-postcheck-skips-stored-tokens killed |
| D4: no-reply failures refuse cleanly, no token in the message | **passed** (gap RV2-2) | M: loopback real-stack errors; test_d4 cases; 3 leak-assertion survivors |
| D5: an https-to-http or off-origin redirect drops the header | **passed** (gap RV2-3) | M: loopback, all five codes; RV2-m-same-origin-port-ignored and -suffix killed |
| D6: paths as huggingface_hub resolves them | **passed under PY** (gaps RV2-8, RV2-9) | R constants.py:129-194; M: my two D6 mutants killed under PY, survive under PY2 |
| D3 stays (PP9) | **passed** | R launch.py:140-149 unchanged |
| F1: a value a header cannot carry refuses before any request | **passed** | M: real http.client ValueError/UnicodeEncodeError withheld; 3 of my F1 mutants killed |
| Token trace: environments, argument lists, logs, records, tracebacks, temporary files | **passed** | section 3; M scan 0 hits |
| PP10's guard covers the gated path's subprocess and socket calls | **passed, with limits** (RV2-6, RV2-7) | M: audit + sandbox baseline |
| The whole 7-8B suite passes | **passed** | M: 288 passed (PY, under SANDBOX) |
| runkit/stage1-olmo unchanged | **passed**; its suite **not tested** by me | M: `git diff --quiet` exit 0 |
| T2 and K2 mutation specs | **not tested** (outside this lens; the fixers report 80/80, 28/28) | - |
| No real secret read; ws-k unchanged | **passed** | M: section 1 |
| A live whoami/Range check | **not tested** | the network is the lead's |

## 8. Defects (all minor; none blocks the merge)

| Id | Where | Summary | Failure scenario | Fix |
|---|---|---|---|---|
| RV2-1 | launch.py:94; tests/test_gated_78b.py:1002-1026 | No test pins TLS certificate verification. RV2-m-tls-handler-unverified and RV2-m-tls-default-context-unverified survive the whole suite (M). The code verifies today (M: default context CERT_REQUIRED, check_hostname True) | A developer meets CERTIFICATE_VERIFY_FAILED on the Mac (the D4 refusal) and "fixes" it with an unverified context; every test passes; on launch day the whoami and Range requests send `Bearer <token>` to whichever TLS peer answers (a proxy, a captive portal, a MITM) | In test_d1: for the real opener, assert every HTTPSHandler's `_context` is None or has `verify_mode == ssl.CERT_REQUIRED` and `check_hostname`; assert `ssl._create_default_https_context is ssl.create_default_context` after importing launch (about 6 lines) |
| RV2-2 | tests/test_gated_78b.py:1029-1069, 1328-1341 | The D4 leak checks look for the exact token and the HF pattern only. Three survivors (M): http_get calling failure_text without the token; the 200 cut before the scrubs; a refusal line ending with token[3:] | (a) A non-HF-shaped secret pasted into HF_TOKEN (verifier's C4) and echoed in a URLError reason lands in launch-0.log. (b) A long reason with the token across character 200 leaves a fragment neither scrub matches. (c) A line printing the token minus its constant prefix passes every check and secret_scan | Use F1's `_names_no_part` (halves) plus `token[3:]` in the D4 assertions; add a NO_REPLY case through http_get with a visible-ASCII non-HF token; add a failure_text case with the token at characters 185-222 |
| RV2-3 | tests/test_gated_78b.py:229-242, 1087-1103 | Redirect tests use 302 only; RV2-m-redirect-302-only survives (M). The code is right for every code (M: loopback) | A later edit restricts the drop to 302; a 301/307/308 off-origin redirect then carries the token | Parametrize the D5 test over 301, 302, 303, 307, 308 |
| RV2-4 | tests/test_gated_78b.py:888-894 | The pod's token-variable test iterates `dl.TOKEN_ENV_NAMES`, the list under test; RV2-m-dl-one-token-variable survives (M) | HUGGING_FACE_HUB_TOKEN dropped from the pod list; a pod with that variable set passes the download's before and after checks (the preflight's own list still catches it later) | Hardcode both names in the test; add a HUGGING_FACE_HUB_TOKEN case to the D2 test |
| RV2-5 | tests/test_gated_78b.py:1230 | Staging is tested with "1" only; RV2-m-dl-staging-only-value-1 survives (M). The library takes 1, ON, YES, TRUE (R constants.py:10, 63) | HUGGINGFACE_CO_STAGING=true passes a narrowed check; the library then reads the staging token path while the kit checks the normal one | Also test "true" and "yes" |
| RV2-6 | tests/test_pp10_guard.py:40-55, 127-187 | The guard's own tests reach the network under a weakened guard. M: under RV2-m-guard-connect-ex-open, test_every_real_exit made a real outbound connect to port 22 (the source names 203.0.113.9); the sandbox denied it (kernel log 08:34:05 UTC). M by identity: gethostbyname, gethostbyname_ex, gethostbyaddr are the _socket functions, so the sentinels do not sit under them; a guard that drops one of these names would make the G1 test send a real DNS query (I; not run). The docstring and fix-K-gated.md say "safe under a weakened guard" | A mutation run (or an edit) of conftest.py sends a SYN to TEST-NET-3 and DNS queries for api.runpod.io and huggingface.co from the Mac; no token is in them, but PP10's rule is broken exactly when the guard is under test | Before each probe, assert the guarded callable is not the original (capture REAL_* at import for connect, connect_ex, create_connection, the four lookups, sendto, sendmsg, OpenerDirector.open); aim the connect probes at a closed loopback port; run guard mutants under SANDBOX |
| RV2-7 | tests/conftest.py:72-110 | Untested or open guard forms. Survivors (M): AF_INET6 datagrams (RV2-m-guard-sendto-inet6-open); the by-path allow list for programs outside NEVER (RV2-m-guard-popen-allows-any-under-local: bash, sh, env would pass). Open (R/M): `socket.getnameinfo` (a reverse lookup) is not guarded; multiprocessing's default start method here is spawn (M), which starts a child through `_posixsubprocess.fork_exec` outside the guard (R multiprocessing/util.py:451-456); Popen's `executable=` is not checked (the guard reads argv[0]) | A future test uses multiprocessing or getnameinfo, or `local_processes` with a shell, and reaches a real process or a DNS query; no kit file or test does today (M grep) | Add the AF_INET6 and `/bin/sh` under local_processes cases; guard getnameinfo and `multiprocessing.util.spawnv_passfds`; check `kw.get("executable")` |
| RV2-8 | setup/job_runner_stage1.py:320-321 | D6 did not reach the runner's pre-job check: it looks at `~/.cache/huggingface/token` only (R) | With HF_HOME or HF_TOKEN_PATH set on the pod, the runner's check before each job is vacuous (the download's and the preflight's checks are right) | Use `download_models_stage1.no_token_left()` there, as the preflight now does (K2's file; a later round) |
| RV2-9 | tests/test_gated_78b.py:1157-1186; tests/run_mutants_gated_78b.py | The D6 path tests need huggingface_hub. Under PY2 the 11 reload cases skip and two D6 mutants survive (M); the runners use `sys.executable` and do not refuse such a Python | A runner started with PY2 reports D6 mutants as survived (or a fixed D6 test as passing) without testing the resolver | Hardcode the expected paths (they follow from HOME and the variables), or have the runner refuse when huggingface_hub is not importable |

## 9. Jobs for the lead

1. Merge decision: nothing here blocks it. Before the first Llama launch, add RV2-1's TLS test (a fixer stage).
2. Route RV2-2 to RV2-7 and RV2-9 (test additions, each a few lines) to the next fix round; RV2-8 to K2's file owner.
3. Run the kit's mutation runners with PY only until RV2-9 is fixed, and run any conftest.py mutants under the
   SANDBOX line above (RV2-6).
4. Long foreground runs on this Mac can stall when it sleeps (command 22: 4.5 h for 4 min of work; I). Use
   `caffeinate -i` for the lead's background mutation runs.
5. Delete after the merge: SCR2 (pt-audit-suite basetemp, the kit copies under mut-*/repo; no secret in it, M scan)
   and the first re-verifier's files in reverify-K-gated-scratch/.

## 10. Unresolved concerns

- The verifier's C1-C6 still stand (the orchestrate child holds the token; accept-new host keys; Mac records scanned at
  backup; any visible-ASCII value is sent as a Bearer token (F1 narrows C4 only); proxy and CA variables; TypeError in
  the warn path).
- SANDBOX denies IP traffic but not DNS: lookups go through mDNSResponder, outside the sandbox. My lookup evidence is the
  in-process audit hook; lookups inside the 18 children were not observed (I). The children made no IP connection
  attempt (M: no kernel denial).
- The preflight's new import sets two HF_HUB_* variables in the engine preflight's environment (section 3 item 8);
  harmless by my reading, but not announced by the fixers.
- My loopback check used http:// for the redirect cases; https redirects use the same handler code path (I).
