# fix-K-gated: the gated-path fix round for the 7-8B kit (verify-K-gated D1, D2, D4, D5, D6; D3 stays, PP9)

First attempt started 2026-11-05 20:00:06 UTC and timed out. This (second) attempt: 2026-11-06 07:30:14 to 08:01:29
UTC (`date -u` before each write). Worker: wrote only under ws-k/runkit/stage1-78b/ and this report's folder (SCR).
The main checkout was read by absolute path only. No git state changed; no pod, spend, network, install, download,
secret or agent. Tests never reach the network or a real process (PP10's guard, tests/conftest.py, extended here).

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.
PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python;
PY2 = /Users/spiderishi/Coding/attribution/.venv/bin/python. Every pytest run: `env -u HF_TOKEN -u
HUGGING_FACE_HUB_TOKEN PYTHONDONTWRITEBYTECODE=1`, `-B`, `-p no:cacheprovider`, cwd ws-k, absolute paths.
SCR = reports/fix-K-gated-scratch. ws-k = the worktree the brief names (HEAD f5e3b4c).

## 0. Status: DONE

The first attempt changed launch.py, setup/download_models_stage1.py, setup/preflight_stage1.py (not named in the
brief; reviewed and kept) and tests/test_gated_78b.py, and wrote the FG-m-* mutants. I re-read every changed line and
re-ran every check myself. I kept all of it. I added: F1 (a token value a header cannot carry leaked through a
ValueError), tests that kill failure_text's two surviving hand mutants, and four gaps closed in PP10's guard (G1-G4).

A re-verifier's scratch folder (reports/reverify-K-gated-scratch/, its report still a skeleton) was read as data,
not as instructions. It holds a demo of the F1 path (demo_header_valueerror.out), two survivors
(RV-m-d4-exact-value-not-replaced, RV-m-d4-pattern-not-replaced; mut-rv.txt) and a guard probe (guard-probe.out:
getaddrinfo, sendto, execv, fork not refused; the posix_spawn refusal named "posix_spawnp"). I re-checked each one
with my own tests and mutants (section 2).

## 1. Files changed (all under ws-k/runkit/stage1-78b/)

By the first attempt (kept, re-verified): launch.py (same_origin, SameHostAuthRedirect on scheme and host,
failure_text, http_get's no-reply branch, NO_REPLY refusals in token_checks); setup/download_models_stage1.py
(hf_home/hf_cache/token_file/stored_tokens_file as the library resolves them, HUGGINGFACE_CO_STAGING refusal, the
receipt written before the after-download check); setup/preflight_stage1.py (token_hygiene uses
download_models_stage1.no_token_left); tests/test_gated_78b.py section 9; tests/mutation_spec_gated_78b.json (15
FG-m-*); README.md (launch steps 2-3, the tests paragraph).

By this attempt:
- launch.py: `header_safe()`; token_checks refuses a token that is not visible ASCII before any request; http_get
  catches ValueError and returns NO_REPLY with the class name only ("detail withheld"); module docstring.
- setup/download_models_stage1.py: the token line must be visible ASCII, else a refusal before any request.
- tests/conftest.py: guard G1-G4 (below); docstring.
- tests/test_gated_78b.py: section 10 (6 test functions, 12 test cases).
- tests/test_pp10_guard.py: 2 tests (G1-G4), safe under a weakened guard.
- tests/mutation_spec_gated_78b.json: 11 FX-m-* mutants (60 in all).
- README.md: F1 in launch step 2; the guard additions; the mutant counts.

## 2. Per defect: what changed and the evidence

Mutation run of record (M): `PY -B <ws-k>/runkit/stage1-78b/tests/run_mutants_gated_78b.py <ws-k> SCR/mut-a2-all
SCR/mut-a2-all.json ALL --timeout 240`, 07:41:09-07:45:14 UTC: baseline exit 0 (111 passed), **60 of 60 killed**,
none survived or invalid.

### D1 (http_get's opener untested)
- Code (R launch.py:87-104, line 94): the opener is built at the call with `urllib.request.build_opener(SameHostAuthRedirect)`.
- Test: `test_d1_http_get_builds_its_opener_with_the_same_origin_redirect_handler_and_the_precheck_runs_through_it`.
  build_opener is replaced by a recorder that builds the REAL OpenerDirector and shadows that instance's `open`. It
  checks the handler list (SameHostAuthRedirect in, the stock HTTPRedirectHandler out), the Authorization and Range
  headers, the 60 s timeout, the HTTPError path, and the whole precheck (whoami plus ten Range requests) through the
  real http_get.
- Mutants killed (M): the verifier's own V-m-http-get-no-redirect-handler (verify driver, whole suite, SCR/mut-a2-vhand:
  12 of 12 killed, baseline 0); FG-m-http-get-no-redirect-handler; RV-m-d1-stock-redirect-handler, RV-m-d1-no-timeout.

### D2 (the after-download no_token_left() untested)
- Test: `test_d2_a_download_that_leaves_a_stored_login_or_a_token_variable_behind_is_refused_after_the_download`
  (4 cases: token file, stored_tokens, HF_TOKEN set, token file under HF_HOME). The fake snapshot_download leaves the
  item behind DURING the call; the run must end in SystemExit, the download must have run once, the receipt says ok
  false, the preflight's gated_ready refuses it, no file holds the fake token.
- Mutants killed (M): the verifier's V-m-dl-post-check-dropped (whole suite, SCR/mut-a2-vhand); FG-m-dl-post-check-dropped,
  FG-m-dl-no-receipt-before-post-check, FG-m-stored-tokens-unchecked; RV-m-d2-postcheck-swallowed,
  RV-m-d2-ok-true-before-postcheck, RV-m-d2-postcheck-env-only.

### D3 (stays as built; PP9)
Not changed. An unreadable 200 whoami reply warns and the Range check decides (the user's waiver of 7 Oct 2026; PP9,
R lead-rulings-part2-prep-20261105.md:51-54). The existing 7-body warn test still passes (M, the suite).

### D4 (URLError, timeouts and TLS failures gave a traceback)
- Code (R launch.py:76-104, 135-137, 157-160): http_get returns NO_REPLY (0) plus failure_text (class and reason,
  token's exact value and any HF-shaped string replaced by `<token>`, 200 characters at most) for URLError, OSError
  (timeouts, resets, ssl.SSLError, certificate failures) and http.client.HTTPException. token_checks turns NO_REPLY
  into a SystemExit line for whoami and stops at the first Range request with no reply.
- Tests: `test_d4_a_failure_before_any_reply_is_a_clean_refusal_that_scrubs_the_token_and_names_no_token` (10 cases:
  DNS, refused, socket timeout, URLError timeout, certificate verify, TLS, reset, remote disconnected, incomplete
  read, a reason that holds the token). Each goes through launch.main: SystemExit with the line, no child started,
  HF_TOKEN removed by the finally scrub, no token-check.json, the lock released, no token in the message or stdout.
  `test_d4_a_no_reply_on_a_range_request_refuses_at_once_and_sends_no_further_request`.
- New this attempt: `test_d4_failure_text_replaces_the_exact_value_and_any_other_hf_shaped_string` (a token not of the
  HF shape, caught by the exact replace only; another HF-shaped string, caught by the pattern only; the 200 cap).
- Mutants killed (M): FG-m-http-get-no-reply-propagates, FG-m-failure-text-keeps-token, FG-m-range-no-reply-continues;
  RV-m-d4-urlerror-only, -oserror-only, -whoami-noreply-as-status, -range-noreply-skipped; and the two that SURVIVED
  the re-verifier's run, now killed: RV-m-d4-exact-value-not-replaced and RV-m-d4-pattern-not-replaced (SCR/mut-a2-rv:
  19 of 19 killed, baseline 0), also in the kit spec as FX-m-exact-value-not-replaced and FX-m-pattern-not-replaced.

### F1 (new; D4's "the message names no token", found by the re-verifier's demo, confirmed by my test)
- Defect: a token value with a line break inside (say a paste error) reached http.client's header check, which raises
  `ValueError("Invalid header value b'Bearer hf_...'")` quoting the whole value. http_get did not catch ValueError, so
  launch.py died with a traceback that prints the token's halves into launch-0.log (I: CPython prints the exception
  message). M: `test_f1_http_client_quotes_the_whole_header_in_its_value_error_so_the_value_must_refuse_first`
  (offline: putrequest/putheader only, no socket) shows both halves are in the message.
- Fix: `header_safe(token)` (visible ASCII 0x21-0x7E only) refuses in token_checks (launch.py:130) before any request, with a line
  that names no part of the value. Backstop: http_get maps any other ValueError to NO_REPLY with the class name only.
  The pod's download script refuses such a token line too (download_models_stage1.py:220), before any request (the Mac check runs first; I).
- Tests: `test_f1_a_token_a_header_cannot_carry_refuses_before_any_request_and_names_no_part_of_it` (7 forms: line
  break, CR, space, tab, non-ASCII, DEL, BEL; no Hub call; via launch.main no opener built, no child, token scrubbed,
  lock released); `test_f1_header_safe_accepts_visible_ascii_only`;
  `test_f1_http_get_withholds_the_detail_of_a_value_error_and_keeps_a_tls_verify_failures_reason`;
  `test_f1_the_pod_refuses_a_token_line_a_header_cannot_carry_before_any_request`.
- Mutants killed (M): FX-m-header-check-dropped, -header-check-after-whoami, -header-safe-allows-space,
  -header-safe-allows-non-ascii, -header-safe-allows-empty, -valueerror-propagates, -valueerror-detail-kept,
  -dl-header-check-dropped, -dl-header-allows-space.

### D5 (a same-host scheme downgrade kept the Authorization header)
- Code (R launch.py:56-73): `same_origin` compares (scheme, netloc), case-insensitive; the header is deleted when a
  redirect leaves the origin.
- Test: `test_d5_a_same_host_redirect_that_changes_the_scheme_drops_the_authorization_header` (https to http, case
  only, another port, another host, same origin path; Range kept).
- Mutants killed (M): FG-m-redirect-scheme-ignored, K3-m-redirect-keeps-auth (re-targeted), RV-m-d5-hostname-only,
  RV-m-d5-scheme-only, RV-m-d1-handler-condition-inverted.

### D6 (hf_cache() and token_file() ignored HF_HOME and HF_TOKEN_PATH)
- Library (R, installed huggingface_hub 0.36.2, the pod's pin experiments/minimal_safety/requirements.lock:7;
  .../site-packages/huggingface_hub/constants.py): HF_HOME = expandvars(expanduser(getenv("HF_HOME",
  join(getenv("XDG_CACHE_HOME", ~/.cache), "huggingface")))) at :129-137; HUGGINGFACE_HUB_CACHE =
  getenv(..., HF_HOME/hub) at :140-144; HF_HUB_CACHE = expandvars(expanduser(getenv("HF_HUB_CACHE",
  HUGGINGFACE_HUB_CACHE))) at :148-153; HF_TOKEN_PATH = expandvars(expanduser(getenv("HF_TOKEN_PATH",
  HF_HOME/token))) at :178-184; HF_STORED_TOKENS_PATH = dirname(HF_TOKEN_PATH)/stored_tokens at :186; staging mode
  (HUGGINGFACE_CO_STAGING, :63, :70, :188-194) moves the cache and token path.
- Code (R download_models_stage1.py:52-106): hf_home, hf_cache, token_file, stored_tokens_file follow those lines in
  the same order; staging refuses; no_token_left checks both files. The preflight uses the same functions.
- Tests: `test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly` (11 environments, each compared with a
  reloaded huggingface_hub.constants: defaults, HF_HOME, XDG_CACHE_HOME, both, HF_HUB_CACHE, the legacy name, both,
  HF_HOME plus legacy, HF_TOKEN_PATH, HF_HOME plus HF_TOKEN_PATH, `~` and `$VAR`);
  `test_d6_with_hf_home_set_the_checks_look_where_the_library_does`;
  `test_d6_hf_token_path_stored_tokens_and_the_staging_switch_refuse_and_the_preflight_reads_the_same_path`.
- Mutants killed (M): FG-m-hf-home-ignored, -xdg-ignored, -token-path-ignored, -legacy-hub-cache-ignored,
  -hub-cache-ignores-hf-home, -staging-unchecked, -preflight-hygiene-default-path; RV-m-d6-no-expanduser,
  -stored-tokens-under-hf-home, -hub-cache-ignores-legacy-and-home, -preflight-hygiene-dropped, -staging-check-dropped-whole.
- Under PY2 (no huggingface_hub) the 11 reload cases skip (M); under PY (the pin) they run and pass (M).

### G1-G4 (PP10's guard; new this attempt)
- Gaps (M, by my tests before the fix; the re-verifier's guard-probe.out shows the same): a name lookup
  (getaddrinfo etc.) sends a DNS query before any connect and was not refused (G1); a UDP sendto/sendmsg needs no
  connect and was not refused (G2); os.fork/forkpty/execv/execve (so os.spawn*, os.exec*, pty.fork) were not refused
  (G3); the posix_spawn refusal named the late-bound loop variable "posix_spawnp" (G4).
- Fix (tests/conftest.py): G1 refuses the four lookups except None and loopback names (the pass-through resolves the C
  function at the call); G2 refuses sendto/sendmsg on AF_INET/AF_INET6 sockets (AF_UNIX passes); G3 replaces the four
  os functions; G4 binds the name per function.
- Tests (test_pp10_guard.py): `test_g1_g4_name_lookups_datagrams_forks_and_execs_are_refused_too` and
  `test_g1_g4_the_kits_http_libraries_stop_in_the_guard_before_any_lookup` (http.client and urllib3 stop in the guard).
  They are safe under a weakened guard: each os function is first checked to be replaced, the lookups sit over
  sentinels that raise AssertionError, the datagrams go to 127.0.0.1:9 only.
- Mutants killed (M): SCR/guard_mutants.json via the verifier's driver with `--all-tests`, SCR/mut-a2-guard: baseline 0,
  7 of 7 killed (GD-m-lookup-unguarded, -lookup-allows-any, -send-unguarded, -send-allows-inet, -send-refuses-unix,
  -fork-exec-unguarded, -spawn-name-late-bound).

## 3. Commands run (exit status; all foreground, each under 10 minutes)

| # | Command | Exit / result |
|---|---|---|
| 1 | `date -u` (07:30:14, 07:32:39, 07:39:10, 07:39:34, 07:40:49, 07:41:09, 07:45:14, 07:47:52, 07:49:40, 07:49:54, 07:52:58, 07:53:47, 07:55:15, 07:55:27, 07:56:47, 07:57:35, 07:58:28, 08:01:00, 08:01:29 UTC) | 0 |
| 2 | Reads: cat/sed/grep over the reports, launch.py, download_models_stage1.py, preflight_stage1.py, conftest.py, the tests, the specs, the runners, secret_scan.py, README.md, constants.py, requirements.lock:7, PP9/PP10; `diff` against the verifier's pre-fix kit copy | 0 (one `echo ====` failed in zsh, exit 1, harmless) |
| 3 | `PY -B -m pytest ... --basetemp SCR/pt-a2-base runkit/stage1-78b/tests` (as found) | 0: 274 passed |
| 4 | the gated and guard files after my first edits (SCR/pt-a2-new) | 1: 2 failed, 117 passed (my test errors: fake_token() is the same within one process; a test without a World could not import launch) |
| 5 | `-k "f1_ or failure_text"` (SCR/pt-a2-new3) | 1: 1 failed (my test error: http.client.InvalidURL is an HTTPException, not a ValueError; that case removed) |
| 6 | a PY2 edit script | 1 (find text mismatch on a non-ASCII character; redone, then the file made ASCII) |
| 7 | the gated and guard files (SCR/pt-a2-new5) | 0: 119 passed |
| 8 | the whole suite (SCR/pt-a2-suite) | 0: 288 passed |
| 9 | `PY -B .../run_mutants_gated_78b.py <ws-k> SCR/mut-a2-b4 SCR/mut-a2-b4.json <15 ids> --timeout 240` | 0: baseline 0, 15 of 15 killed |
| 10 | the same, `ALL` (SCR/mut-a2-all) | 0: baseline 0 (111 passed), 60 of 60 killed |
| 11 | test_pp10_guard.py after the rewrite (SCR/pt-a2-guard) | 0: 8 passed |
| 12 | `PY -B verify-K-gated-scratch/run_hand_mutants.py <ws-k> SCR/mut-a2-guard SCR/mut-a2-guard.json SCR/guard_mutants.json --all-tests --timeout 300` | 0: baseline 0, 7 of 7 killed |
| 13 | the same driver, the verifier's hand_mutants.json, `--all-tests` (SCR/mut-a2-vhand) | 0: baseline 0, 12 of 12 killed (both former survivors) |
| 14 | the same driver, the re-verifier's hand_mutants_rv.json (SCR/mut-a2-rv) | 0: baseline 0, 19 of 19 killed (both former survivors) |
| 15 | `PY -B .../run_mutants_78b.py <ws-k> SCR/mut-a2-t2 SCR/mut-a2-t2.json ALL --timeout 300` | 0: baseline 0, 80 of 80 killed |
| 16 | `PY -B .../run_mutants_runner_78b.py <ws-k> SCR/mut-a2-k2 SCR/mut-a2-k2.json ALL --timeout 300` | 0: baseline 0, 28 of 28 killed |
| 17 | the whole suite with PY (SCR/pt-a2-final) and PY2 (SCR/pt-a2-py2) | 0: 288 passed; 0: 276 passed, 12 skipped (no huggingface_hub, no urllib3 in PY2) |
| 18 | `git diff --quiet HEAD -- runkit/stage1-olmo`; `git status --porcelain -- runkit/stage1-olmo` | 0; 0 lines |
| 19 | `PY -B -m pytest ... --basetemp SCR/pt-a2-olmo runkit/stage1-olmo/tests` | 0: 762 passed |
| 20 | `PY2 -I -B SCR/scan_outputs_a2.py <kit>/secret_scan.py SCR/pt-a2-* SCR/mut-a2-* SCR/a2-*.txt` | 0: 136,551 files, 944 links skipped, **0 secret_scan hits, 0 files with the HF token pattern** |
| 21 | the same scan over a control file with a synthetic `hf_` + 34 A's | 0: 1 hit (the scan works) |
| 22 | `ast.parse` and a non-ASCII count over the six changed Python files | 0 (only two pre-existing section signs) |
| 23 | the whole suite after the README edit (SCR/pt-a2-final2) | 0: 288 passed |
| 24 | `git status --porcelain` (outside the kit); `find runkit -name __pycache__` | only `?? .ai/inputs/scale-78b-sealed-llama3-20261105/` (the core fixer's copy); 0 |

The scan reads regular files only and never follows a link (a World or a mutation copy links into the main checkout).

## 4. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| D1 closed with a test and a killed mutant | passed | M: section 2 D1; V-m-http-get-no-redirect-handler killed on the whole suite |
| D2 closed with a test and a killed mutant | passed | M: section 2 D2; V-m-dl-post-check-dropped killed on the whole suite |
| D4 closed with tests and killed mutants | passed | M: 10 failure forms through launch.main; the two former survivors killed; F1 added |
| D5 closed with a test and a killed mutant | passed | M: section 2 D5 |
| D6 closed with tests and killed mutants | passed | M: 11 environments against the reloaded library; R constants.py:129-194 |
| D3 stays as built (PP9) | passed | R: no change to the warn path; M: its tests pass |
| All suites pass (the 7-8B suite; runkit/stage1-olmo unchanged) | passed | M: 288 passed (PY), 276 passed 12 skipped (PY2); stage1-olmo 762 passed, git diff exit 0 |
| Mutation specs touching these files | passed | M: gated 60/60, guard 7/7, verifier 12/12, re-verifier 19/19, T2 80/80, K2 28/28; every baseline exit 0 |
| secret_scan over every record, log and test output; the fake token searched | passed | M: 0 hits, 0 HF-pattern files over 136,551 files; control 1 hit |
| No real secret read | passed | No secrets file, token file or token variable read; every run with `env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN` |
| No network or real subprocess in any test (PP10's guard holds) | passed, within limits | M: the guard tests; G1-G4 closed; limits in section 6 |
| A live whoami/Range check | not tested | the network is the lead's |

## 5. Jobs for the lead

1. Merge by explicit paths (all under runkit/stage1-78b/): launch.py, setup/download_models_stage1.py,
   setup/preflight_stage1.py, tests/conftest.py, tests/test_gated_78b.py, tests/test_pp10_guard.py,
   tests/mutation_spec_gated_78b.json, README.md (plus everything fix-K-core.md lists).
2. A re-verifier should run `tests/run_mutants_gated_78b.py ALL` (60 mutants, about 4 min here) and SCR/guard_mutants.json
   with the verifier's driver and `--all-tests` (7 mutants, about 2 min). The guard spec lives in SCR only; keep it as
   tests/mutation_spec_guard_78b.json if you want it in the kit (a runner for test_pp10_guard.py would be needed).
3. The re-verifier's report (reverify-K-gated.md) is still a skeleton; its scratch findings are answered here.
4. Delete SCR (pytest basetemps, mutation copies, the first attempt's mut-fg*/pt-* folders) after the merge.

## 6. Unresolved concerns

- The guard does not cover C-level calls made by hand (ctypes, `_posixsubprocess.fork_exec`), raw sockets' other
  send forms after a refused connect, or a child the `local_processes` tests start (outside the guard; fix-K-core's
  concern). No kit file or test uses these (M: grep found no getaddrinfo, sendto, fork, exec or multiprocessing use).
- Under mutant GD-m-send-allows-inet, one UDP datagram went to 127.0.0.1:9 (loopback; no packet left the machine; I).
  Under the other guard mutants the tests stop before a real call (I, from the order of the asserts).
- header_safe is stricter than http.client: it also refuses a space or a tab, which http.client would send. A real HF
  token is `hf_` plus letters and digits (I), so it never refuses a real token.
- In run 4 one assertion diff printed a FAKE token (`fake_token()`, seeded by the process id) to my terminal only; it
  is not in any file (M: the scan).
- The download script resolves the paths at call time; the library resolves them at import (inside snapshot_download,
  after the checks). The environment does not change between the two on the pod (I).
- The verifier's C1-C6 (the orchestrate child holding the token, accept-new host keys, records scanned at backup,
  the token sent before a shape check, proxy variables, TypeError widening the warn path) stand. F1 narrows C4: a value
  that is not visible ASCII is now refused before any request; any other wrong value is still sent to huggingface.co.
