# Re-verify K core (fix-K-core): adversarial re-verification of the 7-8B kit's block-0 subset

Track: reverify-K-core (second attempt). A first attempt left a skeleton report and scratch at the top of
reports/reverify-K-core-scratch/ (ws/, mut-t2*, mut-k2*, pp10-probe/, hand_spec_rv.json, run_pack.py, diff-*.patch);
I did not use its results. Everything below is from this attempt, in reports/reverify-K-core-scratch/a2/ (SCR).
Started: 2026-11-06 08:04 UTC (date -u). Finished: see the last line.
Scope: D1-D6, PP7, PP8, PP10 in ws-k/runkit/stage1-78b/ after fix-K-core (and fix-K-gated's later edits to the shared
conftest.py, which the PP10 checks cover). ws-k was read only; every run used SCR/ws, my copy of ws-k without its
.git pointer file. No file in ws-k or the main checkout was written; no git state changed; no pod, spend, network,
install, download, secret or agent.

Tags: M measured (command given), R read (path:line), E estimate, I inference.
PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (3.11.15).
PY2 = /Users/spiderishi/Coding/attribution/.venv/bin/python. Every pytest run: `-B`, `-p no:cacheprovider`,
PYTHONDONTWRITEBYTECODE=1, and `env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN -u RUNPOD_API_KEY`.

## 0. Verdict: VERIFIED_WITH_MINOR

D1-D6, PP7 and PP8 hold (M). Block 0 packs and plans on both families from fresh working copies against the committed
sealed sets, with the right edit hashes, caps and need lines (M). T2's 80 mutants and K2's 28 all die (M). 10 of my
12 hand mutants die; 2 survive (test gaps, minor). runkit/stage1-olmo is unchanged and its 762 tests pass (M).

PP10 holds today (M): under a process-wide audit hook and, separately, under a kernel sandbox that denies every
program but Python and every non-local connection, the whole 7-8B suite passes and starts nothing else. But the
guard has gaps a future test could fall through (M, by probe): collection-time and module-scoped code, multiprocessing
with the "spawn" start method, `socket.getnameinfo`, and `executable=` under `local_processes`. Four minor defects,
no major one.

## 1. Inputs read (R)

- Lead rulings PP1-PP13: `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part2-prep-20261105.md` (PP3, PP4, PP7-PP10).
- Ruling 11: `.../lead-rulings-part1-20261105.md:144-178` (KD1-KD11, N's layout). Ruling 10: `:132-142`.
- Addendum: `.../lead-rulings-part1-addendum-20261105.md` A1, A2 (`:8-31`), A8 (`:82-84`), A13 (`:102-108`).
- Part 1 `research/experiments/2026-11-05-78b-preregistration-part1.md` §3 (`:109-174`), §12 (`:337-341`).
- KCR `research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md:161` (idle storage), `:165-177` (§7, $56.06).
- Reports: build-K1/K2/K3.md, verify-K-core.md (D1-D6, V-H1..V-H20), verify-K-gated.md, fix-K-core.md, fix-K-gated.md.
- Code: the fix diffs of rules_78b.py, stage1_rules.py, plan_tool.py, pack_setup.py against the core verifier's
  pre-fix copy (SCR/diff-*.patch); rules_78b.py `:418-612`, `:848-950`, `:975-1060`; tests/conftest.py (whole);
  tests/test_pp10_guard.py (whole); test_rules_78b.py tests 07c, 17, 17b, 18, 18b, 19; setup/job_runner_stage1.py
  `:160-180`; scripts/stage1/s1common.py `:590-592` (main checkout).
- Sealed inputs: hashes, key names and counts only (no row, prompt or answer read or printed).

## 2. Checks, per item

### D1 (plan_tool / pack_setup read the committed Llama MANIFEST form) - holds
- Code (R): `rules_78b.sealed_edit_entry` (an edit entry by path under edits/, family in R/M/unit, 64-hex sha256,
  an arm) and `rules_78b.block0_r_edits` (R_d by family "R" AND draw; a Llama-form seed must be 1100 + d; a duplicate
  or missing draw refuses). `plan_tool.man_arms`, `plan_tool.edit_sources` and `pack_setup.sealed_set` call them.
- Fresh copies, both families (M, #6-#9): pack --dry-run, pack, init-block 0 --dry-run and init-block 0 --funding all
  exit 0. Llama: R_d1-R_d3 = 5cdedf22 / 8f9f3cd5 / edbc111b at seeds 1101-1103, arms edit-<sha>, a0 at 1103;
  OLMo: f7d7eb86 / 913b7360 / cd8d3328. Each plan edit carries its family's prepared manifest (c52a50af / 9ed61826)
  and counts {remove 600}. The bundles hold the three edits by hash (M: `tar tzf`).
- Independent reader (M, #10): SCR/check_sets.py reads the MAIN checkout's committed MANIFESTs with its own rule
  (family R, draw d, path under edits/), hashes each edit file and compares with the pack dry runs: all equal. The
  Llama MANIFEST has 24 entries, no other family at draws 1-3; Gate B's has 16 entries of another family at draws 1-3
  (the M trap the D1 fix avoids).
- The ws-k copy of the Llama set equals the main checkout's committed blobs, 29 of 29 (M, #11: `git ls-files -s`
  against `git hash-object`, read-only). `git show HEAD:<MANIFEST> | shasum` = 2a1db220... (M).
- Mutants: V-H17 (re-targeted, the same mutation: drop the family clause) killed (M, #16); my RV2-1 (pack binds two
  draws), RV2-2 (receipt seed 1100), RV2-3 (man_arms back to role "edit"), RV2-12 (engine arm renamed) killed (#14).

### D2 (idle storage line) - holds
- `rules_78b.idle_storage`: $0.20/GB/month x 50 GB / 30 d = $0.33 per stopped pod per day; N's 2 pods $0.67/day,
  $20.00/month (R: rules_78b.py:531-545; KCR:161). Both init dry runs print it as the 21st line; the summary JSON has
  `idle_storage`; plan.json's `need_lines` has the line (M, #8, #9).
- Mutants: FK-m-idle-* (3) killed in T2's run (#12); my RV2-4 (the line prints the 2-pod total as the per-pod figure)
  and RV2-5 (the summary key renamed) killed (#14).

### D3 / PP7 (Llama sealed-set pin) - holds
- `SEALED_SETS["llama31-8b"]["sha256"]` = 2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c (R:
  rules_78b.py:177-178), equal to the committed MANIFEST at d422fca (M: `git -C main log -1`, `git show | shasum`).
- test_07c asserts both pins equal the committed files' hashes, and keeps A13's null-pin refusal test-local (R:
  test_rules_78b.py:513-526). T2's baseline passes with the filled pin (33 passed) and FK-m-llama-pin-null dies (M, #12).

### D4 / D5 (fixture refuses the other family; test World MANIFEST forms) - holds
- V-H14 (byte-identical to the core verifier's, M: JSON compare) and V-H17 (re-targeted) both killed on the whole
  suite (M, #16; first failing tests: test_d4_..., test_d5_..._gateb-form).
- My RV2-3 died on `test_d5_..._plan_block0...[olmo2-7b-llama-form]` and RV2-12 on `[...-gateb-form]` (M, #14), so the
  World really builds both forms and the plan test reads them.

### D6 ($36.41) - holds
- The Llama init dry run prints "need N this family's pod alone (llama31-8b-0-1, cap 12.50 h, spend upper $20.80):
  $36.41" (M, #8). By hand: 1.25 x cents($6 + $1.85 x 12.5) = 1.25 x $29.13 = $36.4125 -> $36.41. OLMo: $27.16.

### PP8 (a1_pass, rep_pass, S78_KINDS, caps) - holds
- S78_KINDS = {retrain, rep_pass, a1_pass, classifier} (R: rules_78b.py:141), as PP8 lists. `check_keys` and
  `job_decision` refuse each while RECIPE_S is null (R: :577-579, :982-983; the runner's gate too, R:
  job_runner_stage1.py:170-176). rep_pass's label names REQ-3's pass and scripts/stage1/representation_pass.py (the file
  exists in the main checkout, M: ls); a1_pass's label names A1's pass and the 16.5 h cap.
- Caps (M, #8; by hand): a1_pass window 16.5 h - 48 min - 30 min, cap 16.50 h, guard $36.53, need $45.66; rep_pass
  1.5 x 2.3 x 3,600 s = 12,420 s, cap 4.75 h (2,880 + 12,420 + 1,800 = 17,100 s), guard $14.79, need $18.49; the
  stage-1 kit's 1B estimate is 3,600 s (R: runkit/stage1-olmo/stage1_rules.py:87).
- RULES-78B.md:115-116 and README.md:73-75 carry the same names and caps (R).
- Mutants: T2's re-targeted T2-m-rep-pass-17 and T2-m-s78-kinds-empty are the same mutations at the new names (M:
  spec diff by id, 64 old ids kept, 16 added, none removed); FK-m-* PP8 mutants killed (#12); my RV2-6 (a1_pass window
  without the start margin) and RV2-11 (the key check exempts the classifier) killed (#14). RV2-9 (a1_pass out of
  stage1_rules.UNITLESS_KINDS) survives: DK-3.
- PP4 is not enforced (DK-4, latent; carried from fix-K-core's own job 5).

### PP10 (network / subprocess guard) - holds today; gaps found
- The guard (R: tests/conftest.py) is an autouse function-scoped fixture.
- Whole suite under my process-wide audit hook (SCR/audit/pp10_audit.py, installed before collection; it blocks any
  non-loopback address or name, any urllib request, os.system and ssh/scp/gh/curl...): 288 passed (M, #17). 22 audited
  events: 18 real process starts, every one the Python interpreter, in the call phase of the 9 tests that request
  `local_processes` (one is the guard's own test); 0 at collection or in a fixture; 0 non-loopback socket or name events
  (the 3 lookups are localhost / None / 127.0.0.1; the one sendmsg is the AF_UNIX socketpair) (M, #18).
- Whole suite under a kernel sandbox (SCR/audit/deny-net-exec.sb: exec denied for every program but the Python
  interpreter, outbound network denied except localhost and unix sockets; this covers the children of the
  `local_processes` tests too): 288 passed (M, #19). The system log shows one denial in the run, a
  `network-outbound` by libinfo's `si_destination_compare` (the address-sorting step of a loopback getaddrinfo); I
  reproduced it alone with the G1 test (M, #21). Positive control: the same profile denies /usr/bin/true and logs it
  (M, #20). So no child started ssh or any other program, and none reached the network.
- The K3 incident's path stops in the guard (M: test_the_k3_incident_path... passes in every run).
- My guard mutant RV2-7 (the interpreter allowed without `local_processes`) dies (M, #14). RV2-8 (allow by base name)
  survives: DK-2.
- Probe (SCR/pp10-probe/, conftest.py copied byte for byte from ws-k; every probe local: /usr/bin/true, /bin/echo,
  time.sleep, 127.0.0.1:9) (M, #13; SCR/pp10-probe/out/results.jsonl):
  - ran: a `subprocess.run` at test-module import (collection); one in a module-scoped fixture; a multiprocessing
    "spawn" Process (child exit 0); a ProcessPoolExecutor(spawn) worker; `_socket.socket.connect_ex(127.0.0.1:9)`
    (ECONNREFUSED 61 from the OS); `subprocess.run([sys.executable, ...], executable="/bin/echo")` under
    `local_processes` (echo ran); `socket.getnameinfo` is not replaced (identity check, no lookup made).
  - refused: multiprocessing "fork", asyncio.create_subprocess_exec, `shell=True` with "git ...; echo ...", plain
    subprocess.run, socket.socket().connect_ex.
  - Python 3.11's multiprocessing.util.spawnv_passfds calls `_posixsubprocess.fork_exec` directly and audits nothing
    (M: inspect), and the Mac's default start method is "spawn" (M).
  - No kit file or test uses multiprocessing, ProcessPoolExecutor, getnameinfo, ctypes or _posixsubprocess (M: grep;
    only conftest.py's docstring names them). No test calls `monkeypatch.undo()` (M: grep). The two module-scoped
    fixtures (test_rules_78b.py:68, :73) read files only (R).

### Block 0 for both families from a fresh working copy - holds
- SCR/ws/tmp/family-probe-s78-{llama31-8b,olmo2-7b}-0/ made by tar from runkit/stage1-78b without tests/ (the
  fixers' copies moved aside to SCR/ws/tmp/fixer-copies-moved/) (M, #5).
- pack --dry-run and pack (SCR/run_pack.py: pack_setup.main with one stub, `git_state` -> ws-k's HEAD f5e3b4c, because
  the copy has no .git; ws-k's `git status --porcelain -- experiments scripts` is empty, M): exit 0, engine X
  472fc7f6..., main configs 74758af1 (Llama) / 18cc31d7 (OLMo), sealed sets 2a1db220 / d76d8bf9, receipts' edits as
  above, sealed_files_sha256 f577d1a9 (Llama) / 81238896 (OLMo), equal to the plans' hosts (M, #6, #7).
- init-block 0 --dry-run: 21 lines each (N $56.06 = 1.25 x $44.85, guard $44.85 = $6 + 1.85 x 21, spend upper $33.30,
  contingency $11.21; this pod alone $36.41 / $27.16; 2 retrain lines, cap 4.50 h, guard $14.33, need $17.91; 16 scorer
  lines, each labelled; the idle line) (M, #8).
- init-block 0 --funding (K1's SYNTHETIC record, $56.06; no money): plan.json host llama31-8b-0-1, cap 12.5 h, 4
  counted, jobs arm R 1101-1103 at 33 steps + a0_arm 1103 at 38, recipe B, engine X; olmo2-7b-0-1, cap 8.5 h, 3 arms;
  released; engine_y null (M, #9).

### runkit/stage1-olmo unchanged and its suite - holds
- `git -C ws-k diff --quiet HEAD -- runkit/stage1-olmo` exit 0; `git status --porcelain -- runkit/stage1-olmo
  experiments scripts` 0 lines; 762 passed in my copy (M, #3, #4). The main checkout's runkit/ and experiments/ are
  unchanged since f5e3b4c (M: `git diff --quiet f5e3b4c HEAD -- runkit/stage1-olmo experiments` exit 0; `--stat` on
  runkit empty), so the merge lands on the same base (I).

## 3. Mutation runs

| Run | Spec | Baseline | Result |
|---|---|---|---|
| T2 (#12) | tests/mutation_spec_rules_78b.json, run_mutants_78b.py ALL | exit 0, 33 passed | 80 of 80 killed |
| K2 (#15) | tests/mutation_spec_runner_78b.json, run_mutants_runner_78b.py ALL | exit 0, 49 passed | 28 of 28 killed |
| fixer's hand (#16) | fix-K-core-scratch/hand_spec_fixk.json V-H14, V-H17 | exit 0, 288 passed | 2 of 2 killed |
| mine (#14) | SCR/hand_spec_rv2.json, 12 mutants, whole suite with -x | exit 0, 288 passed (both batches) | 10 killed, 2 survived |

All with absolute paths; kill only on exit 1 with a FAILED line and no ERROR line (R: the runners' verdict()).

My mutants (SCR/hand_spec_rv2.json; SCR/mut-hand-a.json, -b.json):

| id | mutation | verdict | first failing test |
|---|---|---|---|
| RV2-1 | pack_setup binds R_d1-R_d2 only | killed | test_d5_both_manifest_forms_pack_block0[olmo2-7b-gateb-form] |
| RV2-2 | the pack receipt's seeds all 1100 | killed | the same |
| RV2-3 | plan_tool.man_arms back to role == "edit" | killed | test_d5_..._plan_block0...[olmo2-7b-llama-form] |
| RV2-4 | the idle line's per-pod figure prints the 2-pod total | killed | test_the_need_printout_lists_n_...[olmo2-7b] |
| RV2-5 | init's summary JSON key `idle_storage` renamed | killed | the same |
| RV2-6 | a1_pass's window without the 30 min start margin (cap 17.5 h) | killed | the same |
| RV2-7 | the guard allows sys.executable without local_processes | killed | test_every_real_exit_from_the_process_is_refused |
| RV2-8 | local_processes allows by base name, not by path | **survived** | (DK-2) |
| RV2-9 | a1_pass removed from stage1_rules.UNITLESS_KINDS | **survived** | (DK-3) |
| RV2-10 | the scorer need lines lose their labels | killed | test_the_need_printout_lists_n_...[olmo2-7b] |
| RV2-11 | check_keys exempts the classifier from the S_78 branch | killed | test_07b_recipe_s78_pins_refuse_until_filled |
| RV2-12 | the plan's engine arm is a 12-hex prefix | killed | test_d5_..._plan_block0...[olmo2-7b-gateb-form] |

## 4. Commands run (exit status; all foreground, each under 3 min; cwd SCR/ws unless said)

| # | Command | Exit / result |
|---|---|---|
| 0 | `date -u` before each time written | 08:04:26, 08:04:44, 08:13:02, 08:35:02 and the finish |
| 1 | `cp -R -P ws-k SCR/ws; rm SCR/ws/.git`; shasum lists of runkit/ and the Llama set, ws-k vs copy | 0; 205 files identical |
| 2 | `diff -rq` / `diff -u` of the kit against the core verifier's pre-fix copy | the 4 code patches in SCR/diff-*.patch |
| 3 | `PY -B -m pytest -p no:cacheprovider -q -rfEs runkit/stage1-78b/tests` (08:07:49-08:08:04) | **0: 288 passed** |
| 4 | the same on runkit/stage1-olmo/tests (08:08:14-08:09:00); `git -C ws-k diff --quiet HEAD -- runkit/stage1-olmo` | **0: 762 passed**; 0 |
| 5 | fixers' copies moved to tmp/fixer-copies-moved/; tar copies of runkit/stage1-78b (no tests/) into both KD7 folders | 0 |
| 6 | `PY -B SCR/run_pack.py tmp/family-probe-s78-<f>-0 X --dry-run`, both families | 0, 0 (SCR/pack-dry-*.json) |
| 7 | the same without --dry-run (08:11:38-08:11:39) | 0, 0 (SCR/pack-real-*.json; receipts read) |
| 8 | `PY -B tmp/family-probe-s78-<f>-0/plan_tool.py init-block 0 --jobs tmp/k1-records/jobs-<f>-0.json --dry-run` | 0, 0: 21 lines each (SCR/init-dry-*.out) |
| 9 | the same with `--funding tmp/k1-records/funding-0-synthetic.json` | 0, 0: plan.json written (read: hosts, jobs, blocks) |
| 10 | `PY2 -I -B SCR/check_sets.py /Users/spiderishi/Coding/attribution <f> SCR/pack-dry-<f>.json`; `git -C main log -1 / show HEAD:<MANIFEST> \| shasum` | 0, 0; d422fca; 2a1db220... |
| 11 | `git -C main ls-files -s` vs `git hash-object --no-filters` over ws-k's Llama set | 29 = 29 blobs equal |
| 12 | `PY -B SCR/ws/runkit/stage1-78b/tests/run_mutants_78b.py SCR/ws SCR/mut-t2 SCR/mut-t2.json ALL --timeout 300` (08:20:59-08:21:44) | **0: baseline 33 passed; 80 of 80 killed** |
| 13 | `PY -B -m pytest ... runkit/stage1-78b/tests/test_probe_pp10.py` (cwd SCR/pp10-probe; PP10_PROBE_OUT set) | 0: 10 passed; results in SCR/pp10-probe/out/results.jsonl |
| 14 | `HAND_SPEC=SCR/hand_spec_rv2.json PY -B SCR/hand_mutants_runner.py SCR/ws SCR/mut-hand-{a,b} ... --timeout 300` (08:26:16-08:27:40; 08:27:49-08:30:06) | 0: 6 killed; 1: 4 killed, 2 survived |
| 15 | `PY -B .../run_mutants_runner_78b.py SCR/ws SCR/mut-k2 SCR/mut-k2.json ALL --timeout 300` (08:21:53-08:23:23) | **0: baseline 49 passed; 28 of 28 killed** |
| 16 | `HAND_SPEC=fix-K-core-scratch/hand_spec_fixk.json PY -B SCR/hand_mutants_runner.py SCR/ws SCR/mut-hand-fixk ... V-H14,V-H17` (08:31:30-08:32:02) | 0: baseline 288 passed; 2 killed |
| 17 | the whole 7-8B suite with `-p pp10_audit` (SCR/audit on sys.path; 08:17:34-08:18:11) | **0: 288 passed** |
| 18 | PY2 summary of SCR/audit/suite-audit.jsonl | 22 events: 18 interpreter starts, 3 loopback lookups, 1 AF_UNIX sendmsg |
| 19 | `sandbox-exec -f SCR/audit/deny-net-exec.sb PY -B -m pytest ... runkit/stage1-78b/tests` (08:19:22-08:19:48) | **0: 288 passed** |
| 20 | positive control: the same profile on a `subprocess.run(['/usr/bin/true'])`; `/usr/bin/log show` | PermissionError; the log shows `deny(1) process-exec* /usr/bin/true` |
| 21 | the G1 test alone under the sandbox; `/usr/bin/log show` | 1 passed; the one `network-outbound` denial reproduces (libinfo address sort) |
| 22 | PY2 one-liner: `rules_78b.engine_allowed(kind, Y)` with ENGINE_Y set test-locally | every E kind True once filled (DK-4); False today |
| 23 | greps: multiprocessing / ProcessPoolExecutor / getnameinfo / ctypes / _posixsubprocess / undo() / module-level spawns in the kit | only conftest.py's docstring; none |
| 24 | `git -C main diff --quiet f5e3b4c HEAD -- runkit/stage1-olmo experiments`; `--stat -- runkit` | 0; empty |
| 25 | shasum list of ws-k's runkit/ and Llama set at the end vs the start; `git -C ws-k status --porcelain \| wc -l` | identical; 47 (as at the start) |

One extra network-shaped call, stated plainly: in the sandbox's first test (before #19) I ran
`socket.connect_ex(("203.0.113.9", 9))` inside the deny profile to see the sandbox refuse it. The kernel refused it
(EPERM, `deny(1) network-outbound remote:*:9` in the log), so no packet was sent (M). Every other probe used loopback.

## 5. Defects (all minor; none blocks the merge)

**DK-1 (minor). The PP10 guard does not cover every way out of the process.** It is a function-scoped autouse
fixture that patches Python-level names. Measured gaps (#13): code at test-module import (collection) and in a
module-scoped fixture runs unguarded; multiprocessing / ProcessPoolExecutor with the "spawn" start method (the Mac's
default) starts a real child through `_posixsubprocess.fork_exec` inside the standard library (not "by hand", as the
docstring's limit says); `socket.getnameinfo` (a reverse DNS lookup) is not replaced; `executable=` lets a
`local_processes` test run another program behind an allowed argv[0]; C-level `_socket.socket.connect` is not covered
(within the docstring's stated limit). RULES-78B.md:24 says the guard "fails any real subprocess start". Today no kit
file or test uses any of these (M, #23), and the audit and sandbox runs show nothing escapes (M, #17-#21).
Failure scenario: a later test module that does `import account` at module level (account.py calls the RunPod API at
import, fix-K-core.md §6 item 6) makes a real API call during collection, before any guard exists; or a helper that
uses a process pool starts real children. Fix: in conftest.py, install a process-wide `sys.addaudithook` at import
(it cannot be removed; gate it with a flag that `local_processes` sets) refusing `subprocess.Popen` by its executable
argument, `os.system`, `os.exec`, `os.posix_spawn`, `os.spawn`, `os.fork`, `os.forkpty`, and `socket.connect` /
`sendto` / `sendmsg` / `getaddrinfo` / `gethostbyname` / `gethostbyaddr` / `getnameinfo` to non-loopback addresses
and `urllib.Request` (this covers collection, every fixture scope and C-level `_socket`); patch
`_posixsubprocess.fork_exec` (multiprocessing has no audit event); check `kw.get("executable")` in `guarded_init`; add
getnameinfo to the G1 lookups; reword RULES-78B.md:24. SCR/pp10-probe/.../test_probe_pp10.py is a ready template for
the tests (each probe is local). SCR/audit/pp10_audit.py is a working hook to start from.

**DK-2 (minor). `local_processes`' by-path exactness is untested.** RV2-8 (allow any program whose base name matches
an allowed one) survives the whole suite (M, #14): every program the guard test tries under `local_processes`
(ssh, scp, gh, curl, caffeinate, runpodctl, python3) is also in NEVER, so NEVER alone refuses them. README.md:174 says
`local_processes` "permits those by path and nothing else". Fix: in
`test_local_processes_permits_the_kits_interpreter_and_git_only`, expect a refusal for `[str(tmp_path / "git")]` and
`[str(tmp_path / "python3.11")]` (fails closed: with the mutant the call raises FileNotFoundError and the test fails).

**DK-3 (minor). The `a1_pass` additions to stage1_rules' kind sets are untested.** RV2-9 (a1_pass out of
`UNITLESS_KINDS`) survives (M, #14). DIAG_KINDS' new `a1_pass` was not mutated (not measured). Their readers are
later-round paths (R: plan_tool.py:1425, :1638, :2875, :3989; backup_records_stage1.py:305), so block 0 does not change
(I). Fix: one assertion in test_17 (`{"rep_pass", "a1_pass", "classifier"} <= rules.UNITLESS_KINDS` and the same for
DIAG_KINDS, with the reason), or a note that the scorer round tests them.

**DK-4 (minor, latent; fix-K-core's own job 5). PP4 is not enforced.** `rules_78b.engine_allowed` admits every E kind
on engine Y once ENGINE_Y is filled (M, #22: untuned_answers, rep_pass, l1_scan, classifier, c0, anchor, o_only all
True), while PP4 says every wrapper kind runs on engine X, and the need printout labels l1_scan "(engine X; PP4)".
Today ENGINE_Y is null and nothing runs on Y (M). It becomes live when the lead fills ENGINE_Y for the Y retrain pod
(A13), which is block 0's step (3) in Part 1 §3.7. The frozen settings check refuses another engine on the pod (R:
scripts/stage1/s1common.py:590-592), so a wrapper kind on Y would stop there (I). Fix, before ENGINE_Y is filled: an
`X_ONLY_KINDS` set in rules_78b (PP4's wrapper kinds; the lead names the list) checked first in `engine_allowed`,
with a test and a mutant.

## 6. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| D1: plan and pack read both committed forms; R_d1-R_d3 = 5cdedf22/8f9f3cd5/edbc111b at 1101-1103 + a0 at 1103 | passed | #6-#10; V-H17, RV2-1/2/3/12 killed |
| D2: KD5's idle line in the need report and the summary JSON, with a test | passed | #8, #9; FK-m-idle-*, RV2-4, RV2-5 killed |
| D3 / PP7: the pin filled (2a1db220...), test_07c checks it, T2's baseline passes | passed | R rules_78b.py:177-178; #10, #12 |
| D4 / D5: fixture refusal test; the World's two forms; V-H14 and V-H17 die | passed | #16; RV2-3, RV2-12 |
| D6: $36.41 | passed | #8 |
| PP8: a1_pass 16.5 h at most; rep_pass its own E cap (4.75 h); S78_KINDS; labels; docs; mutants | passed | #8, #12, #14; R RULES-78B.md:115-116 |
| PP10: the guard refuses real subprocess/socket/urllib in tests; the K3 path stops in it | passed (today), with gaps | #3, #13, #17-#21; DK-1, DK-2 |
| Block 0 both families from fresh copies: plans, edits vs committed MANIFESTs, caps 8.5 / 12.5 h, need lines, $56.06 | passed | #5-#11 |
| T2's and K2's mutation specs (kill only on real failure, baseline same command) | passed | #12 80/80; #15 28/28 |
| At least six hand mutants of my own on the changed logic | passed (12 run: 10 killed, 2 survived) | #14 |
| runkit/stage1-olmo unchanged and its suite passing | passed | #4, #24 |
| A live `budget.py check` / real funding record / main-checkout pack | not tested | the lead's (network, money) |

## 7. Jobs for the lead

1. Merge as fix-K-core.md §5 and fix-K-gated.md list (explicit paths); the four defects above do not block it.
2. DK-1 and DK-2 in one small conftest round (the probe and the audit hook in SCR are templates); DK-3 with it or in
   the scorer round; DK-4 before ENGINE_Y is filled for the Y retrain pod.
3. Do not use ws-k/tmp's packs: its working copies predate fix-K-gated (launch.py, setup/download_models_stage1.py,
   setup/preflight_stage1.py differ from the kit, M: cmp). Re-pack in fresh KD7 copies in the main checkout after the
   merge, then init-block 0 with the REAL funding record and `budget.py check` with the live balance.
4. After the merge, run the 7-8B suite in the main checkout once (its runkit/ and experiments/ equal ws-k's base, M
   #24, so I expect 288 passed there; not measured).
5. Rule on the idle-storage line's scope (concern 1) and on rep_pass's reading of PP8 (concern 2).
6. Delete after the merge: reports/reverify-K-core-scratch/ (this attempt's a2/, 149 MB copy SCR/ws with the
   packs and plans of the synthetic funding record, mut-* folders; and the first attempt's ws/, mut-t2/, mut-k2/,
   pp10-probe/ and loose files). Nothing in it is a deliverable; the JSON reports and scripts are evidence only.

## 8. Unresolved concerns

1. The idle line counts N's 2 pods only. Part 1 §3.2 puts the two retrain pods in block 0 too, and A1's pass needs
   each retrain's q and e1 states, so a stopped retrain pod adds about $0.33 per day (E). The line names its scope
   ("N's 2 pods"), so it is not wrong, only narrow.
2. PP8's "the stage-1 kit's 1 h estimate at 1B, scaled to 7-8B with T2's scorer-kind factor" has two readings: 2.3 x
   1.5 x 3,600 s (the fixer's, the same as l1_scan; cap 4.75 h) or 2.3 x 3,600 s (cap 3.75 h). The larger is the
   conservative one ($1.85 more guard per pod). I accept the fixer's reading (I).
3. a1_pass is printed as a "scorer pod". PP4 calls it one of the engine's own jobs, like the retrain. Labels only; the
   money is the same.
4. The children of `local_processes` tests are outside the Python guard. My sandbox run (#19) shows they start no
   other program and reach no network today; the sandbox is macOS-only and was my check, not a kit test.
5. My audit hook and sandbox show the suite clean on this Mac today; they do not prove a future test clean (DK-1).

Finished Fri Nov  6 08:37:06 UTC 2026 (date -u). Nothing in ws-k or the main checkout was written (M, #25); no git state changed; no pod, spend, install, download, secret or agent; the one non-loopback connect attempt was refused by the sandbox before any packet.
