# fix-K-core: the core fix round for the 7-8B kit's block-0 subset (D1-D6, PP7, PP8, PP10)

Started 2026-11-05 19:04 UTC (`date -u`); the finish time is the last line (written with `date -u`).
Worker: wrote only under ws-k/runkit/stage1-78b/, the copied Llama sealed set (ws-k/.ai/inputs/scale-78b-sealed-llama3-20261105/,
step 0), ws-k/tmp/ (fresh working copies; the K1 copies moved to ws-k/tmp/old-k1-copies-20261105/) and this report's folder
(SCR). The main checkout was read by absolute path only. No git state changed; no pod, spend, network, install,
download, secret or agent. Tests never reach the network or a real pod-side process (PP10).

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.
PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (3.11.15, pytest 8.4.2);
PY2 = /Users/spiderishi/Coding/attribution/.venv/bin/python (stdlib helpers, `-I -B`). `PYTHONDONTWRITEBYTECODE=1`,
`-B`, `-p no:cacheprovider` on every pytest run. SCR = reports/fix-K-core-scratch. ws-k = the worktree the brief names
(HEAD f5e3b4c). Every command ran in the foreground (one, the K3 gated mutation run, took 2.5 min and was moved to the
background by the tool; its result file was read after it finished).

## 0. Status: DONE

D1-D6, PP7, PP8 and PP10 are closed with tests. Both families' block-0 pack (dry and real) and init-block 0 (dry and
real) run against the committed sealed sets in fresh KD7 working copies (M, section 3 #22-#29). The whole 7-8B suite
passes (244 tests, 17 files; the kit round had 211), runkit/stage1-olmo's suite passes unchanged (762), and every
mutant is killed: T2's spec 80 of 80 (64 + 16 new), K2's runner spec 28 of 28, K3's gated spec 34 of 34, the core
verifier's hand mutants V-H14 and V-H17 (re-targeted, section 2 D4/D5) 2 of 2. `git status` in ws-k shows changes
only under runkit/stage1-78b/ and the copied Llama set (M, #31).

## 1. Files changed (all under ws-k/runkit/stage1-78b/ unless said)

- `rules_78b.py`: PP7 (the Llama pin filled: `SEALED_SETS["llama31-8b"]["sha256"] = 2a1db220...`); D1 (`EDIT_FAMILIES`,
  `EDIT_PATH_RE`, `sealed_edit_entry`, `block0_r_edits`; the SEALED_SETS comment now describes both committed forms);
  D2 (`IDLE_STORAGE_USD_PER_GB_MONTH` 0.20, `IDLE_DAYS_PER_MONTH` 30, `idle_storage`; `block0_report()["idle_storage"]`);
  PP8 (`S78_KINDS` = {retrain, rep_pass, a1_pass, classifier}; `a1_pass` added to `E_KINDS` with A1's window
  (`A1_PASS_CAP_H_MAX` = 16.5, the old `REP_PASS_CAP_H_MAX`); `rep_pass` = 1.5 x 2.3 x 3,600 s = 12,420 s, cap 4.75 h;
  `SCORER_KINDS` + `a1_pass`; `KIND_LABELS` for the need printout); the docstring.
- `stage1_rules.py`: `block0_need_report` labels each scorer line (PP8) and adds KD5's idle-storage line and the
  `idle_storage` block (D2); `DIAG_KINDS`, `UNITLESS_KINDS` + `a1_pass`; two comments.
- `plan_tool.py`: `man_arms` and `edit_sources` read both MANIFEST forms through rules_78b (D1); `resolve_edit`'s
  missing-edit text names the family's sealed set; the init summary JSON carries `idle_storage` (D2); two docstrings.
- `pack_setup.py`: `sealed_set` reads both forms through `rules_78b.block0_r_edits` (D1); the receipt's `edits` carry
  `arm` and `seed`.
- `tests/conftest.py` (new): the PP10 guard (autouse) and the `local_processes` fixture.
- `tests/test_pp10_guard.py` (new, 6 tests): the K3 incident's path and every real exit from the process.
- `tests/test_fix_k_core.py` (new, 17 tests): D5 (both forms x both families: plan and pack), D1 (the committed sets by
  pin through plan_tool; the by-draw-alone trap), D4 (the fixture refuses the other family's verification.json, 4 cases
  x 2 families).
- `tests/test_rules_78b.py`: 07b and 07c (PP8's kinds; PP7: the filled pin checked against the committed file, the null
  and bad pins test-local; D3), 08 and 12 (a1_pass 16.5 h, rep_pass 4.75 h), 13 (16 required ids), new 17, 17b (PP8),
  18, 18b (D1: both forms synthetic; the committed sets by pin), 19 (D2). 33 tests (was 28).
- `tests/test_stage1_runkit.py`: the World builds the sealed MANIFEST in the form the family's committed set has, or a
  named form (`synthetic_manifest`: Gate B's with M-family edits at draws 1-2 and the two non-edit entries; the Llama
  set's with role strings, seeds, same_rows_as, roles map); the CLI dry-run test counts 21 lines (D2).
- `tests/test_kit_78b_shell.py`: the need-printout test (16 scorer lines, the labels, a1_pass $45.66, rep_pass $18.49,
  the idle line and block; D2, PP8).
- `tests/mutation_spec_rules_78b.json`: two find texts re-targeted after PP8's move (`T2-m-rep-pass-17` ->
  `A1_PASS_CAP_H_MAX`; `T2-m-s78-kinds-empty`'s literal; the same mutations); 16 mutants added (ids `FK-m-*`). 80.
- `tests/test_kit_78b_runner.py` (4 tests), `tests/test_stage1_runner.py` (1), `tests/test_stage1_judge_route.py` (3):
  the `local_processes` fixture added to the signature of each test that runs the kit's own interpreter as a real
  local child (the job runner's dry run, the engine's argv parser, the states check, the fake pod's shipped driver).
  No assertion changed.
- `RULES-78B.md`, `README.md`: the kinds (PP8), the E-caps table (rep_pass 4.75 h / $14.79; a1_pass 16.5 h / $36.53),
  the sealed-set section (D1, PP7), the idle-storage line (D2), the PP10 section, the test and mutant counts.
- ws-k/.ai/inputs/scale-78b-sealed-llama3-20261105/ (step 0): the committed set copied byte for byte (29 files).
- SCR (scratch, not deliverables): update_spec.py (the spec edit, run once), hand_spec_fixk.json (V-H14 unchanged;
  V-H17 re-targeted), mut-t2 / mut-k2 / mut-k3 / mut-hand folders and .json/.out reports, pack-*/init-* outputs,
  llama-set-{src,dst}.sha.

Not changed: runkit/stage1-olmo/ (M: `git diff --quiet HEAD -- runkit/stage1-olmo`), experiments/, scripts/, every
frozen or sealed file, host.py, launch.py, orchestrate.py, the runner files, budget.py, secret_scan.py, account.py.

## 2. Per defect: what changed and the evidence

### Step 0: the Llama sealed set copied
- `cp -Rp` of `/Users/spiderishi/Coding/attribution/.ai/inputs/scale-78b-sealed-llama3-20261105/` into ws-k at the same
  path; 29 tracked files (`git ls-files` in the main checkout), per-file `shasum -a 256` lists identical (`cmp` exit 0;
  SCR/llama-set-{src,dst}.sha). The MANIFEST hashes to 2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c
  (M). Committed at d422fca in the main checkout (R: `git log -1 -- <MANIFEST>`), after ws-k's base f5e3b4c.

### D1 (major): the committed Llama MANIFEST's form
- Read (keys only, M: PY2 one-liner): Gate B's 31 entries: 29 at `role == "edit"` (R d1-d5, M for 8 units x draws 1-2,
  8 unit edits) plus "counts" and "gate-c sample" with paths outside edits/. The Llama set's 24 entries: 16 R entries
  with `role` = a block sentence ("block 0 (N): R_1-R_3 at 1101-1103 ..." for d = 1-3), `seed` 1100 + d, `same_rows_as`,
  and 8 unit entries at `role` "unit removal"; no entry has `role == "edit"`; a top-level `roles` map.
- Fix: `rules_78b.sealed_edit_entry(entry)` (an edit entry in either form: a non-empty role string, `path` under
  edits/, `family` in R / M / unit, a 64-hex `sha256`, an `arm`) and `rules_78b.block0_r_edits(manifest, draws)` (draw ->
  {draw, seed, arm, path, sha256} by `family == "R"` AND `draw == d`; a Llama-form `seed` must be 1100 + d; a draw listed
  twice or missing refuses). `plan_tool.man_arms`, `plan_tool.edit_sources` and `pack_setup.sealed_set` call them, so
  one reader serves the plan and the pack. Gate B's form still works (the M edits at draws 1-2 are excluded by family).
- Tests: test_rules 18 (synthetic manifests of both forms: `gateb_form()` with M edits at draws 1-2 and the two non-edit
  entries, `llama_form()` with role strings and seeds; the by-draw-alone trap: three entries carry draw 1 in Gate B's
  form and `block0_r_edits` takes R_d1 only; a wrong seed, a duplicate, a stray entry outside edits/, a missing draw,
  non-entries); test_rules 18b (the real-set test by pin: each committed MANIFEST hashes to its pin; `block0_r_edits`
  gives R_d1-R_d3 = 5cdedf22... / 8f9f3cd5... / edbc111b... (Llama) and f7d7eb86... / 913b7360... / cd8d3328... (OLMo)
  at seeds 1101-1103, arms `edit-<sha>`, each edit file hashing to its entry and carrying the family's prepared
  manifest; the Llama file has no `role == "edit"`; Gate B's holds 16 M entries at draws 1-2); test_fix_k_core
  `test_d1_the_committed_sets_plan_block0_by_pin[both]` (the committed MANIFEST and R_d1-R_d3 copied into the World by
  path, the real pin: init dry and real; plan.json binds the three edits by the hashes above, a0 at 1103 and cap 12.5 h
  on Llama, 8.5 h on OLMo; a changed MANIFEST byte refuses by pin); `test_d1_a_manifest_that_lists_the_m_edits_by_draw_alone_would_refuse`.
- Before / after: the core verifier's #12 and #13 (pack and init refusing on the committed set with the pin filled)
  are now exit 0 (M: #22-#29). Mutants: `FK-m-r-edits-any-family` (V-H17's mutation at its new place),
  `FK-m-r-edits-seed-unchecked`, `FK-m-r-edits-duplicate-passes`, `FK-m-r-edits-missing-passes`,
  `FK-m-edit-entry-any-path`, `FK-m-edit-entry-role-edit-only` (the defect itself, re-introduced): all killed (M: #15).
- The plan and the pack on the real sets: section 3 #22-#29; the Llama plan's edits are 5cdedf22... / 8f9f3cd5... /
  edbc111b... at 1101-1103 with a0 at 1103, cap 12.5 h, guard $29.13, spend upper $20.80; the pack receipt's `edits`
  carry the same hashes, arms and seeds and `sealed_set.sha256` 2a1db220... (M).

### PP7 and D3: the pin filled; test_07c
- `SEALED_SETS["llama31-8b"]["sha256"]` = 2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c (the
  committed MANIFEST's SHA-256, M above; the lead's PP7 is the recorded step; the comment names it).
- test_07c now asserts both pins equal the committed files' hashes (both files read from the repository root), that a
  test-local null pin refuses with the A13 text while the other family does not fall back, and that bad pins refuse
  (D3). `K1-m-sealed-set-null-passes` stays valid and killed (M: #15). The mutation runner's baseline passes again
  (M: #15: "33 passed"); the verifier's D3 was that the fill broke the baseline.
- New mutant `FK-m-llama-pin-null` (the pin back to null) killed by 07c / 18b.

### D2 (major): KD5's idle-storage line
- `rules_78b.idle_storage(n_pods)`: $0.20 per GB per month (R: KCR:161) x 50 GB / 30 days = $0.33 per stopped pod per
  day (E); for N's 2 pods $0.67 per day, $20.00 per month; `basis` text; counted in no guard. `block0_report()` carries
  it as `idle_storage`; `stage1_rules.block0_need_report` prints it as the last line ("idle storage (KD5; E, KCR:161):
  about $0.33 per day per stopped 50 GB pod that keeps its states ($0.20 per GB per month); N's 2 pods kept stopped:
  $0.67 per day, about $20.00 per month; counted in no guard") and returns it; `init-block 0` prints it and puts the
  block in its summary JSON (`idle_storage`) and plan.json's `need_lines`.
- Tests: test_rules 19 (the arithmetic, 10 pods = $100 per month as KCR:161 says, refusals of bad counts, in
  block0_report); the shell need-printout test (the line's text, the block, the summary JSON) and the runkit CLI
  dry-run test (21 lines). Mutants `FK-m-idle-running-rate`, `FK-m-idle-not-in-report`, `FK-m-idle-per-pod-only` killed.
- M on the real copies: both families' init dry runs print the line (section 3 #24, #28: 21 lines).

### D4 and D5: the fixture refusal test; both MANIFEST forms in the test World; V-H14 and V-H17
- D4: `test_d4_the_fixture_refuses_the_other_familys_verification_json` (4 cases x 2 families): the World's fixture
  file rewritten with the other family's recipe, manifest, training identity, or all three, re-pinned
  (`stage1_rules.PREREG_FIXTURE_SHA256` is the pin plan_tool reads); `fixture()` and `init-block 0` refuse "is not the
  family's a0-1101 side unit"; the other family's real fixture pin refuses "differs from its pin". The code is unchanged
  (V-H14's find text still matches).
- D5: the World's `synthetic_manifest(folder, family, r78, form)` builds Gate B's form (R_d1-R_d3; two units' M edits at
  draws 1-2; unit edits; the "counts" and "gate-c sample" entries) or the Llama form (R_d1-R_d5 with role strings and
  seeds; unit entries at "unit removal"; the roles map). Default by family (olmo2-7b: gateb; llama31-8b: llama); the
  `wff` fixture in test_fix_k_core runs both forms on both families: plan (`test_d5_both_manifest_forms_plan_block0...`:
  the edits bound by family and draw, `edit_sources` holds R draws only, no M or unit hash and no trap row id in
  plan.json) and pack (`test_d5_both_manifest_forms_pack_block0`).
- Hand mutants (the verifier's runner, SCR/hand_spec_fixk.json; V-H14 byte for byte, V-H17 re-targeted to the moved
  clause `if not sealed_edit_entry(e) or e.get("family") != "R":` -> `if not sealed_edit_entry(e):` in rules_78b, the
  same mutation, because the family clause now lives in `block0_r_edits`): baseline 244 passed; **V-H14 killed**
  (first failing test `test_d4_the_fixture_refuses_the_other_familys_verification_json[olmo2-7b-recipe_sha256]`);
  **V-H17 killed** (`test_d5_both_manifest_forms_plan_block0_binding_r_d1_to_r_d3_by_family_and_draw[olmo2-7b-gateb-form]`)
  (M: #19; SCR/mut-hand.json). The verifier's original V-H17 find text no longer occurs in plan_tool.py (the line
  moved), so the original spec would report it INVALID, not survived.

### D6: the corrected figure
- build-K1.md §2 item 5 says "this pod's need alone ($27.16 / $34.86)". The Llama pod's need alone is **$36.41** =
  1.25 x cents($6 + $1.85 x 12.5) = 1.25 x $29.13 = $36.4125 -> $36.41 (M: the Llama init dry run prints "need N this
  family's pod alone (llama31-8b-0-1, cap 12.50 h, spend upper $20.80): $36.41", #24). The OLMo figure $27.16 is right
  (M: #28). The code was right; the report line was not; the shell need-printout test holds both values by hand.

### PP8: a1_pass, rep_pass, S78_KINDS
- `S78_KINDS` = {retrain, rep_pass, a1_pass, classifier}; `PINNED_RECIPE_KINDS` follows. `check_keys` requires recipe
  S_78 for each; `job_decision` refuses each while RECIPE_S is null; planning never refuses (M3).
- `a1_pass` (A1's attributes pass on the retrain's q and e1 states): `A1_PASS_CAP_H_MAX` = 16.5 h; window 16.5 h - 48
  min - 30 min; cap 16.5 h, guard $36.53, need alone $45.66 (unchanged numbers under the new name).
- `rep_pass` (REQ-3's representation pass): 1.5 x 2.3 x 3,600 s = 12,420 s (the stage-1 kit's DIAG_ESTIMATE_S 3,600 s,
  R: runkit/stage1-olmo/stage1_rules.py:87, x T2's scorer-kind factor SIZE_FACTOR_1B_TO_78B 2.3 x WIDE_CAP_FACTOR 1.5,
  as l1_scan and classifier); cap 4.75 h (48 min + 12,420 s + 30 min = 17,100 s exactly), guard $14.79, spend $7.61, need
  alone $18.49 (M: `e-caps`, the init dry runs).
- `SCORER_KINDS` holds both (8 kinds, 16 need lines); `KIND_LABELS` gives each scorer line its label ("REQ-3's
  representation pass ...; recipe S_78", "A1's attributes pass ...; A1's 16.5 h cap at most", "the classifier under
  recipe S_78, as at 1B (PP4, PP8)", ...). The runner (setup/job_runner_stage1.py) already reads `r78.S78_KINDS`, so its
  refusals cover the four kinds without a change (R: job_runner_stage1.py:170, :381, :594).
- Tests: 07b, 07c, 08, 12 updated; 17 and 17b new (the four kinds refuse at the gate and the key check while null, run
  under S_78 only once filled, the other family stays null; l1_scan never under S_78; the caps and the labels; the
  scorer table); the shell need-printout test. Mutants `FK-m-s78-kinds-no-classifier`, `FK-m-s78-kinds-no-a1-pass`,
  `FK-m-rep-pass-takes-a1-window`, `FK-m-rep-pass-no-size-factor`, `FK-m-a1-pass-takes-rep-pass-cap`,
  `FK-m-scorer-kinds-no-a1-pass` killed; `T2-m-rep-pass-17` and `T2-m-s78-kinds-empty` re-targeted and killed (M: #15).
- RULES-78B.md and README.md updated (the kinds, the E-caps table, the pins section).

### PP10: the no-network, no-subprocess guard
- `tests/conftest.py`: an autouse fixture replaces, for each test, `subprocess.Popen.__init__` (every run / Popen /
  check_output / call / os.popen passes through it, however early the caller bound `subprocess.run`), `os.system`,
  `os.posix_spawn[p]`, `socket.socket.connect` / `connect_ex`, `socket.create_connection` and
  `urllib.request.OpenerDirector.open` (urlopen and every `build_opener().open`) with a function that raises
  `NetworkOrProcessRefused` (a RuntimeError naming the call and the rule). A test's fake (the module's `subprocess`
  name, `runner=` / `run=` / `get=`) never reaches it. The `local_processes` fixture permits exactly the kit's own
  interpreters (sys.executable, the two venv pythons by absolute path) and `git`, never ssh / scp / gh / curl /
  caffeinate / runpodctl / a bare python3; the network and os.system stay refused.
- The K3 incident's path: `test_the_k3_incident_path_stops_in_the_guard_without_a_fake` calls `host.gated_download(host,
  fake_token)` with no `runner=` (the default resolves `subprocess.run` at the call) and with `subprocess.run` bound at
  import (the incident's binding form), `ssh_base` pointing at 203.0.113.9 as in the incident: both stop in the guard
  with "argv[0] = 'ssh'"; no record is written; no process starts (M: the test passes; a real ssh would have been
  refused by the guard before `Popen.__init__` ran).
- `test_every_real_exit_from_the_process_is_refused` (13 calls: ssh, caffeinate, gh, a shell string, scp through the
  import-time binding, os.popen, os.system, three socket forms, three urllib forms, posix_spawn, the kit's own
  interpreter without the fixture), `test_a_fake_never_reaches_the_guard`, `test_local_processes_permits_the_kits_interpreter_and_git_only`,
  `test_the_guard_is_on_by_default_and_names_the_rule`, `test_the_kits_modules_spawn_nothing_at_import` (14 modules
  import under the guard; `account.py`, a byte-identical stage-1 script that calls the RunPod API at module level, is
  refused by the guard's urllib clause when imported with a FAKE key: a positive proof on a kit module).
- Nine existing tests run the kit's own interpreter as a real local child (the job runner's `--dry-run`, the engine's
  argv parser, `states_tool.py check`, the judge route's shipped driver); each now requests `local_processes`. Found by
  running the suite under the guard (M: 14 failures, all of them this, before the fixture was added; 0 after).
- The guard is active inside the mutation runners' pytest children (M: the three specs' baselines pass under it).

## 3. Commands run (exit status; cwd ws-k unless said; all foreground, each under 10 minutes)

| # | Command | Exit / result |
|---|---|---|
| 0 | `date -u` before each time written | 19:04:41, 19:33:05, 19:34:58, 19:36:21, 19:38:06, 19:40:04, 19:41:11, 19:44:28, 19:48:38 UTC |
| 1 | `cp -Rp` of the committed Llama set into ws-k; per-file `shasum -a 256` lists over `git ls-files`; `cmp` | 0; 29 = 29 identical |
| 2 | PY2 `-I -B` one-liners: the two MANIFESTs' SHA-256, top-level keys, key sets and roles (no row read) | 0: 2a1db220... (24 entries, no role "edit"); d76d8bf9... (31 entries; 29 "edit", 16 M at draws 1-2) |
| 3 | `PY -B -m pytest ... runkit/stage1-78b/tests` after the rules_78b / stage1_rules / plan_tool / pack_setup edits, before the tests | 1: 1 failed (the need printout: 16 != 14 scorer lines, PP8 as intended), 117 passed, -x |
| 4 | PY2 `-I -B` SCR/update_spec.py on tests/mutation_spec_rules_78b.json | 0: 80 mutants |
| 5 | `PY -B -m pytest ... tests/test_rules_78b.py` | 1: test_08 (a binary-float equality in MY new assertion) -> `pytest.approx`; then **33 passed** (0) |
| 6 | `PY -B -m pytest ... runkit/stage1-78b/tests` with conftest.py, test_fix_k_core.py, test_pp10_guard.py, the World | 1: 14 failed, 220 passed, 5 errors (9 tests spawning the kit's interpreter; `wf` not imported; the need-line count 20 != 21; two of my pp10 tests needed a plan / a fake key) |
| 7 | the same, one representative per group with `--tb=line` | the causes above |
| 8 | PY2 script adding `local_processes` to 8 test signatures (4 runner, 1 stage1_runner, 3 judge_route) | 0 |
| 9 | `PY -B -m pytest ... runkit/stage1-78b/tests` | 1: 9 failed (D4's pin: plan_tool reads `stage1_rules.PREREG_FIXTURE_SHA256`; account.py's module-level API call caught by the guard) |
| 10 | the same after the two test fixes | 1: 1 failed (status.py reads plan.json at import) |
| 11 | the same after `w.init()` in that test | **0: 244 passed in 25.5 s** |
| 12 | `PY -B tests/run_mutants_78b.py ws-k SCR/mut-t2 SCR/mut-t2.json ALL --timeout 300` (RELATIVE paths, from the b78 folder) | stopped: "the baseline did not exit 0" (tail "2 passed, 1 error in 0.28s"); INVALID run, nothing killed |
| 13 | the baseline command by hand in SCR/mut-t2/repo, with and without the runner's env and `--basetemp` | 0, 0: 33 passed (the error of #12 did not reproduce) |
| 14 | the runner's `prepare()` + its exact pytest command through a PY script (absolute paths) | 0: 33 passed |
| 15 | `PY -B tests/run_mutants_78b.py <abs ws-k> <abs SCR/mut-t2> <abs SCR/mut-t2.json> ALL --timeout 300` (19:34:58-19:35:47 UTC) | **0: baseline 33 passed; killed 80 of 80** (SCR/mut-t2.json; no survived, no invalid) |
| 16 | `PY -B tests/run_mutants_runner_78b.py <abs ws-k> <abs SCR/mut-k2> ... ALL --timeout 300` (19:36:21-19:37:53) | **0: baseline 49 passed; killed 28 of 28** |
| 17 | `PY -B -m pytest ... runkit/stage1-olmo/tests` (19:38:06-19:39:32) | **0: 762 passed in 86 s**; `git diff --quiet HEAD -- runkit/stage1-olmo` 0 |
| 18 | PY2 `-I -B` script writing SCR/hand_spec_fixk.json (V-H14 unchanged; V-H17 re-targeted) | 0 |
| 19 | `HAND_SPEC=<abs spec> PY -B reports/verify-K-core-scratch/hand_mutants_runner.py <abs ws-k> <abs SCR/mut-hand> <abs SCR/mut-hand.json> V-H14,V-H17 --timeout 300` (19:40:04-19:40:36) | **0: baseline 244 passed; V-H14 killed, V-H17 killed** |
| 20 | `PY -B tests/run_mutants_gated_78b.py <abs ws-k> <abs SCR/mut-k3> ... ALL --timeout 300` (19:41:11-19:43:43; moved to the background by the tool at 120 s, read after it finished) | **0: baseline 69 passed; killed 34 of 34** |
| 21 | `mv` the K1 working copies to tmp/old-k1-copies-20261105/; `tar` copies of runkit/stage1-78b (without tests/, __pycache__) into tmp/family-probe-s78-{llama31-8b,olmo2-7b}-0/ | 0 |
| 22 | `PY -B tmp/family-probe-s78-llama31-8b-0/pack_setup.py X --dry-run` | **0**: engine X 472fc7f6..., main config 3d437bd6... / 74758af1..., prepared c52a50af..., sealed set 2a1db220... with R_d1-R_d3 (SCR/pack-dry-llama31-8b.json) |
| 23 | `PY -B tmp/family-probe-s78-llama31-8b-0/pack_setup.py X` (the real pack) | **0**: bundle 225 files; setup tar 4,039,023 bytes; receipt: git_commit f5e3b4c27e11..., sealed_set 2a1db220..., edits R_d1-R_d3 = 5cdedf22... / 8f9f3cd5... / edbc111b... at seeds 1101-1103, sealed_files_sha256 f577d1a9... |
| 24 | `PY -B tmp/family-probe-s78-llama31-8b-0/plan_tool.py init-block 0 --jobs tmp/k1-records/jobs-llama31-8b-0.json --dry-run` | **0**: 21 lines (N $56.06; this pod alone $36.41; 2 retrain; 16 scorer; the idle line), then the JSON with the three edits by hash and a0 at 1103 (SCR/init-dry-llama31-8b.out) |
| 25 | `... init-block 0 --jobs ... --funding tmp/k1-records/funding-0-synthetic.json` (K1's SYNTHETIC record, $56.06; no money, no user words) | **0**: plan.json: host llama31-8b-0-1, cap 12.5 h, jobs arm 1101-1103 (edits 5cdedf22... / 8f9f3cd5... / edbc111b...) + a0_arm 1103, released 1, sealed_set 2a1db220... |
| 26 | `PY -B tmp/family-probe-s78-olmo2-7b-0/pack_setup.py X --dry-run` | **0**: engine X, main config e9e98e84... / 18cc31d7..., prepared 9ed61826..., sealed set d76d8bf9... |
| 27 | `... pack_setup.py X` | **0**: 225 files; setup tar 4,038,026 bytes; receipt edits R_d1-R_d3 = f7d7eb86... / 913b7360... / cd8d3328... at 1101-1103 |
| 28 | `PY -B tmp/family-probe-s78-olmo2-7b-0/plan_tool.py init-block 0 --jobs tmp/k1-records/jobs-olmo2-7b-0.json --dry-run` | **0**: 21 lines (this pod alone $27.16; the idle line) |
| 29 | `... init-block 0 ... --funding tmp/k1-records/funding-0-synthetic.json` | **0**: plan.json: host olmo2-7b-0-1, cap 8.5 h, 3 arms with the Gate B edits, released 1 |
| 30 | `PY -B -m pytest ... runkit/stage1-78b/tests` after the doc edits (RULES-78B.md, README.md) | **0: 244 passed in 23.7 s**; `find runkit/stage1-78b -name __pycache__` 0 |
| 31 | `git -C ws-k status --porcelain`; `grep -v runkit/stage1-78b/`; `git diff --quiet HEAD -- runkit/stage1-olmo experiments scripts` | only `?? .ai/inputs/scale-78b-sealed-llama3-20261105/` outside the kit; 46 kit entries (4 M + 42 ??); 0 |
| 32 | `grep -rn "REP_PASS_CAP_H_MAX\|pin is null\|null until the lead merges" --include=*.py --include=*.md` over the kit | the remaining hits are refusal texts and tests of a test-local null pin; two stale plan_tool docstrings found and fixed, then #33 |
| 33 | `PY -B -m pytest ... runkit/stage1-78b/tests` after the two plan_tool docstring fixes (19:53 UTC) | **0: 244 passed in 23.3 s**; `git status` outside the kit: only the copied Llama set; no __pycache__ |

## 4. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| D1 closed with tests (both MANIFEST forms; the real-set test by pin binding R_d1-R_d3 to 5cdedf22... / 8f9f3cd5... / edbc111b... at 1101-1103 plus a0 at 1103) | passed | tests 18, 18b; test_fix_k_core D1/D5 tests; #15 (6 FK-m-r-edits / edit-entry mutants killed); #22-#25 (M) |
| D2 closed with a test (the idle-storage line and block) | passed | test 19; the shell and runkit tests; 3 mutants killed; #24, #28 |
| D3 closed (test_07c checks the filled pin; T2's baseline passes) | passed | #15: baseline 33 passed, 80 killed |
| D4 closed with a test (the fixture refuses the other family's verification.json) | passed | 8 D4 cases; V-H14 killed (#19) |
| D5 closed (both forms in the World; V-H14 and V-H17 die) | passed | `synthetic_manifest`; `wff` fixture; #19: 2 of 2 killed (V-H17 re-targeted, same mutation) |
| D6: the corrected figure in this report | passed | section 2 D6: $36.41 (M: #24) |
| PP7: the pin filled | passed | rules_78b.py; test_07c; #22-#25 |
| PP8: a1_pass (16.5 h at most), rep_pass (its own E cap), S78_KINDS, RULES-78B.md, labels, tests, mutation spec (new mutants killed) | passed | tests 17, 17b, 07b, 07c, 08, 12, the shell test; 6 FK mutants + 2 re-targeted killed (#15); RULES-78B.md, README.md |
| PP10: a conftest guard; proven on the K3 incident's path | passed | tests/conftest.py; test_pp10_guard.py (6 tests); #11, #30 |
| Both families' block-0 init and packs work (M) | passed | #22-#29, all exit 0, on the committed sets |
| All suites pass | passed | #30 (244), #17 (762) |
| All mutants killed (kill only on a real failure; baseline with the same command) | passed | #15 (80/80), #16 (28/28), #20 (34/34), #19 (2/2); every baseline exit 0; #12's invalid run superseded by #15 |
| `git status` shows changes only under runkit/stage1-78b/ and the copied Llama set | passed | #31 |

## 5. Jobs for the lead

1. Record PP7's fill as the recorded step (the pin is in rules_78b.py; this report's section 2 is the evidence) and
   merge by explicit paths: everything under `runkit/stage1-78b/` as K1-K3 list, plus `tests/conftest.py`,
   `tests/test_fix_k_core.py`, `tests/test_pp10_guard.py`, and the edited `rules_78b.py`, `stage1_rules.py`,
   `plan_tool.py`, `pack_setup.py`, `RULES-78B.md`, `README.md`, `tests/test_rules_78b.py`, `tests/test_kit_78b_shell.py`,
   `tests/test_stage1_runkit.py`, `tests/test_kit_78b_runner.py`, `tests/test_stage1_runner.py`,
   `tests/test_stage1_judge_route.py`, `tests/mutation_spec_rules_78b.json`. The Llama set needs no merge (it is
   committed at d422fca in the main checkout; the copy in ws-k is for ws-k's tests and runs only).
2. Before the first pod: fresh KD7 working copies in the main checkout and `pack_setup.py X` again there (the receipts
   here record ws-k's HEAD f5e3b4c, not the main checkout's), then `init-block 0` with the REAL funding record (the
   plan.json files under ws-k/tmp came from K1's synthetic record and are not for a launch); `budget.py check` with the
   live balance (the network is the lead's).
3. Delete ws-k/tmp (the two fresh copies with their packs and plans, `old-k1-copies-20261105/`, k1-records, k2-records)
   and SCR's mut-* folders after the merge; nothing in them is a deliverable (SCR/update_spec.py and
   SCR/hand_spec_fixk.json are the only scratch files a re-verifier may want).
4. The verifier's hand spec: V-H17's find text no longer occurs (the clause moved into rules_78b.block0_r_edits); a
   re-verifier should take SCR/hand_spec_fixk.json's V-H17 (the same mutation at its new place) or
   `FK-m-r-edits-any-family` in the spec.
5. PP4's engine-X rule for the scorer kinds is not enforced by rules_78b (`engine_allowed` lets every E kind run on Y
   once ENGINE_Y is filled; `stage1_rules.X_ONLY_KINDS` is empty): a later round's item (section 6 item 2).
6. Run the mutation runners with ABSOLUTE SOURCE_ROOT and SCRATCH paths (section 6 item 4).

## 6. Unresolved concerns

1. `local_processes` lets nine tests start the kit's own interpreter as a real child; a child is outside the guard, so a
   child's own spawns are not refused. Those children are the job runner's `--dry-run`, the engine's argv parser, a
   `states_tool.py check` and the judge route's fake pod driver, with `PATH=/usr/bin:/bin`; I read no spawn of ssh or
   a network call in them, but the guard does not prove it.
2. PP4 (every scorer kind on engine X) is not in rules_78b: the classifier, rep_pass, l1_scan and the rest are E kinds,
   and `engine_allowed` admits E kinds on Y once ENGINE_Y is filled (A13). Not this brief's item; the lead rules.
3. The idle-storage line counts N's two pods. The retrain pods also keep states (q and e1 for A1's pass); the lead may
   want them added (+$0.33 per pod per day) when their round is planned.
4. The first T2 mutation invocation with relative paths (#12) reported an invalid baseline ("2 passed, 1 error"); by
   hand and with absolute paths the baseline passed every time (#13-#15). Not explained; the runner's usage line does
   not say "absolute", and I did not change the runner (K2's file; relative `--basetemp` under cwd=repo is my guess, I).
5. rep_pass's 4.75 h cap scales a 1B value the stage-1 kit itself marks "I" (unmeasured); KD6 re-measures it on its
   first 7-8B run. a1_pass's 16.5 h is A1's cap at most, as PP8 says.
6. account.py (byte-identical to the stage-1 kit's) calls the RunPod API at import; the guard refuses it under test,
   which is the intended behaviour, but any future test that imports it needs a fake opener.
7. No spend, pod, network or real token here; the pod-side flow is verified with fakes as before.

Finished Thu Nov  5 19:53:49 UTC 2026 (date -u). Nothing in the main checkout was written; no git state changed; no pod, spend, network, install, download, secret or agent.
