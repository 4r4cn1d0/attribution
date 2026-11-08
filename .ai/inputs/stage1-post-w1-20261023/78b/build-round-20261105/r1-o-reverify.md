# R1 Track O fix round: adversarial re-verification

Written 2026-11-08 17:34 UTC (`date -u`). Started 16:48 UTC. Status: **DONE**.

**Verdict: DEFECTS.** R-5's main goal holds: O1 is closed. Every pin fill changes only its own family's index and
form (or, for a Y fill, only engine Y's). The wrapper holds no index hash. No label lie and no leak was found. The
1B files are unchanged. The suite and the 67 mutants reproduce. But R-5's last clause fails. **OR1 (major):** the
documented fill, done in place as the maker's header says, turns Track O's own tests red. The very first fill
(T-O2 step 1, θ0's job pin) breaks 1 test. A branch fill breaks 6. The other findings are minor or nits: gaps in the
R-9 check, two integration points for K1/K3, an unchecked B+Qi block, and untested branches in the new check code.

Target: WS = `B/ws-o` (detached at `3481d85`). The builder's fix section: `R/r1-o.md` §10. The first verifier:
`R/r1-o-verify.md`. My scratch: `R/r1-o-reverify-scratch/`. I edited nothing in WS. M: the 30 Track O files hash to
r1-o.md §10.2. `git status` shows the same 21 untracked entries as at the start, and no tracked change. WS has no new
`__pycache__` and an empty `tmp/`. I made no git state change. There was no pod, network, install or download. I
opened no unit, answer, generation, guard, judge, sealed or prompt file. I never ran `check --data-root` on real
units. All the probes use synthetic fixtures. Tags: M = measured (the command or file is named), R = read
(path:line in WS), E = estimate, I = inference.

## Defects

| id | sev | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| **OR1** | **major** | `tests/oext/test_oext_78b_w1_18.py:139-141`; `tests/oext/test_oext_78b_files.py:123-125` (`records[family]`), `:162-163` (the committed-state call passes no records), `:235-238` (`make_copy` starts from the committed pins) | R-5 requires that "the documented fill procedure leaves the suite green" (O6). It does not. The builder's fill test runs `consistency()` on `--settings-dir` copies only, never the suite after an in-place fill. M (`rv_fill.py`): I did the documented fill in place in a scratch copy of WS (edit `settings/oext_pins_78b.json`, run the maker), then ran the whole scale78b suite. **θ0 OLMo only:** 1 Track O failure, `test_theta0s_null_job_pin_refuses_in_the_wrapper_and_in_the_1b_check`. It still asserts the committed θ0 pin is null. That file is unchanged since R1, although the first verifier's O6 named it. **θ0 for both families plus OLMo's branch 128:** 6 Track O failures. `test_the_committed_state_is_consistent` fails with `TypeError: 'NoneType' object is not subscriptable` at files.py:125. Four `test_the_documented_fill…` cases fail with `KeyError: 'olmo2-7b'`. **Everything filled:** 7 Track O failures. The baseline copy with no fill has 4 other failures, the same in every run: `test_s1_olmo2_7b_check_guard.py` case-variant tests that depend on the mirror's linked `tmp/`. They are not Track O's. | Right after the merge the lead does T-O2 step 1 (R-2) and the suite goes red. After a branch fill, the committed-state test cannot run at all, because it has no way to find the committed W1-18 record. Every recorded fill then needs test edits, which is what O6 and R-5 wanted to stop. | (1) Move the θ0 null-pin test onto the `all_null` fixture copy. (2) Give the committed W1-18 record a path that the tests can find, for example `families.F.w1_18.record_path` in the pins, or a fixed committed location. `consistency()` then reads it when `record_sha256` is set. (3) Start the fill tests from an all-null (pre-fill) base in T-O2 order, not from the committed pins. (4) Add one test, or a documented command, that runs the oext suite after an in-place fill on a copy (`rv_fill.py`'s form). |
| OR2 | minor | `oext_78b.py:137` (`W1_18_UNIT_FILES`), `:519-571` (`check_side_units`) | The R-9 check is narrower than W1-18's own unit gate (`limits_common.check_unit`, `:136-176`). W1-18 runs the frozen `sealed` check on the pod: every file COMPLETE.json lists, model states excepted, must be present with its hash. It also requires `eval/` to hold exactly the checkpoint's folder. Both can be checked by hashing and folder names alone. M (`test_rv_probes.py` E1, E2): a unit whose COMPLETE.json lists a missing `eval/e1/summary.json`, and a unit with a second `eval/e2/` folder, both **pass** `check --data-root` (exit 0, no problems). The wrapper's own `w1_18` then refuses each one ("the frozen sealed check refuses", "eval/ does not hold exactly…"). | The lead's R-9 run passes. Then the W1-18 pod (one pod, both families) refuses a side unit after setup. That is a paid start, and the Branch-full fallback may follow. | In `check_side_units`, run the frozen reader's `sealed(folder)` (it hashes, it does not parse) and compare the `eval/` folder names with `[checkpoint]`. Optionally also check the path against `allow_list.path_pattern`. job.json's fields (arm, seed, checkpoint, identity, refused recipes) need parsing, so they stay a stated limit under "hash, never parse". |
| OR3 | minor | K1's `runkit/stage1-78b/rules_78b.py` (ws-k) `OEXT_INDEX_RE`, `oext_index_problem`; Track O `make_oext_settings_78b.py:63` (`INDEX_NAMES`) | Integration. Track O names the indexes `OEXT-78B__F.json` and `OEXT-78B-Y__F.json`. K1's R-5 form check expects `scripts/scale78b/settings/oext_index__<F>__<E>.json`. M (`rk_forms.py`): all four printed forms pass WS's RK `oext_form_problem` (3481d85). All four fail K1's `oext_form_problem(form, F, E)` with "its files name 0 O-ext index file(s)". K1 wrote that "K2 reconciles it". Track O's notes for K1/K3 (r1-o.md §10.5) do not mention the clash. | After both merge, no `OEXT_78B[F]` or `OEXT_78B_Y[F]` fill made from the maker's printed form passes the kit's check. | Lead decision: one side renames. Either K1's regex takes Track O's names, or the maker's `INDEX_NAMES` and the wrapper's take K1's. A cross-track test should hold the printed form against the merged RK with the family and engine. |
| OR4 | minor | r1-o.md §10.5 ("RUN78 must take both from the job's OEXT_78B[F] or OEXT_78B_Y[F] entry"); `make_oext_settings_78b.py:389-401` (`form`, no W1-18 form) | The K3 note is wrong for the `w1_18` kind. Under T-O2, `OEXT_78B[F]` is filled only after the branch, and the branch comes after the W1-18 pod. So `OEXT_78B[F]` is null while W1-18 runs. K1 built a separate pin, `W1_18_78B {files}`, which the note never names. The maker prints no form for that pin. The X index that the W1-18 pod gets, as it stands after the θ0 fill, changes again at the branch fill (M: `rv_cascade.out`). So R-5's "pinned only by OEXT_78B[F]" cannot hold for the X index. Second gap: the record that joins the forms under Branch 128 (maker docstring :393) is "added by the lead". The maker does not print it, and RK's form check accepts only paths under `scripts/`. | K3 wires the W1-18 pod to a null pin, or a lead fills `W1_18_78B` by hand without a printed or tested form. Under Branch 128, a record committed outside `scripts/` cannot go into `OEXT_78B[F].files`. | Lead decision (I give options, I decide nothing): (a) the maker prints `W1_18_78B`'s form: the wrapper, the W1-18 run files, each family's X index as it stands after θ0, and its W1-18 settings; or (b) a separate per-family W1-18 index, `OEXT-78B-W1__F.json`, holding the W1-18 settings only, which no branch fill changes. Also define where the W1-18 record lives, and whether it goes into the form's `files` or into the job's files list (T-O3). |
| OR5 | minor | `make_oext_settings_78b.py:228`, `:231-234` (the block check covers recipe G only) | The maker checks recipe G's generation and guard blocks against MAIN_F's. It does not check B+Qi's. But `oext_unit_y__F` pins MAIN_F's blocks, so the unchanged 1B `check_recipe` (`oext_unit.py:293-304`) refuses any B+Qi config whose blocks differ. M (`rv_bqi_blocks.py`): with the g16 OLMo config as B+Qi, the maker accepts it, and the 1B `check_recipe` refuses it ("the recipe's generation block is not the pinned one"). The same config as G is refused by the maker. | A RECIPE_BQI fill with a wrong but valid config hash passes every Mac check, since `check --engine Y` validates no Y file (see C3 below). It is refused only on the engine-Y pod. | Run the same block check for `self.bqi` (one line in the loop at :231). Add a test and a mutant. |
| OR6 | minor | `oext_78b.py:225` (index kind and version), `:575` (`check`'s CODE check), `:490` (wait masking), `:550` (job.json fallback), `:529` (data-root containment), `:543` (`complete is True`), `:512` (record units by name); `make_oext_settings_78b.py:446` (`--check`'s failing direction) | Untested branches in the new code. 8 of my 11 proposed mutants **survive** the builder's suite: RV-w-index-kind, RV-w-check-code, RV-w-check-waits-mask, RV-w-side-job-fallback, RV-w-side-root, RV-w-side-complete-true, RV-w-record-units-count, RV-m-check-always-ok (M: `rvmut-a.json`; baseline 99 passed). All 8 are killed once my targeted probes are added (M: `rvmut-b.json`; baseline 111 passed; 0 invalid, 0 ERROR lines). | A later edit drops one of these checks with every test green. For example, `check` could stop hashing the run files, or `make_oext_settings_78b.py --check` could stop reporting drift (the lead's "files equal the derivation" step). | Add the probes `test_C1[*-kind]`, `G1`-`G4`, `B4`, `E5`, `D1` (from `R/r1-o-reverify-scratch/test_zz_rv_targeted.py`) and the 8 mutants (`rv_mutation_spec.json`). |
| OR7 | nit | `oext_78b.py:561`, `:568` | The claim "names, states and hashes only" holds for real engine markers, but nothing in the code enforces it. When a COMPLETE.json file-list value (or `job_sha256`) is not a 64-hex string, the check prints that value as it is. M (E3): a text value placed in COMPLETE.json reaches stdout. COMPLETE.json is pinned by hash and written by the engine (hashes only), so the real risk is near zero (I). | — | Print `None` (or "not a SHA-256") for a non-hex value, at :561 and in the :568 message. |
| OR8 | nit | `oext_78b.py:478`, `:489-492` | `check` masks any 1B refusal of a role that has *some* wait as "waits (…)", and exits 0. M (F1): a W1-18 settings file with a non-integer unit seed, plus a null θ0 pin, gives `"waits (Refusal: settings: unit … has no path or no integer seed)"` and exit 0. The text names the real cause, but the exit code does not. | Before the θ0 fill, a pack or a lead that reads only the exit code takes a broken W1-18 file as waiting. After the fill, the file is validated, so the gap closes before any pod (I). | Match the refusal to the role's waiting pins (for example, the THETA0 wait must be the `untuned job_sha256` refusal), or report "invalid" and exit 2 when the message is not the expected wait. |
| OR9 | nit | `oext_78b.py:264-288` (`split_argv`), `:215` | A repeated leading option silently overrides the first (`--family A --family B`), although the 1B flags refuse repeats. The index check covers the file name only, not its folder. M (A2): a relocated index whose hashes still match cannot produce a label lie, because the 1B validator refuses the old text label. So this is hygiene only. | — | Refuse a repeated leading option. |

## 1. O1 / R-5: closed (M, R)

- **No index hash in the wrapper.** `INDEX_SHA256`, `INDEX_PATH` and `SETTINGS_DIR` are gone. Every 64-hex literal in
  `oext_78b.py` is one of `CODE`'s values (M: `rv_cascade.py` asserts it). Every command takes `--family F [--engine]
  --index P --index-sha256 H` (R: `oext_78b.py:264-288`). `Index` (R: `:204-231`) refuses each of these: a wrong file
  name for the family and engine, bytes off the SHA-256, a wrong kind or version, and contents whose family or engine
  differ. It checks each listed file against the index when the file is read (`:243-255`). M (C1, 35 cases): `unit`,
  `lean run`, `lean verify`, `w1_18` and `check` each refuse an index with a wrong name, a wrong SHA-256, a wrong
  kind, a wrong family, a wrong engine, or the Y index handed for X. Each exits 2 with the wrapper's message, makes no
  folder and leaves every global unchanged. A listed file off its pin refuses on every command except `lean verify`,
  which reads no settings file (by design).
- **My own cascade** (`rv_cascade.py`, on disk, through the maker's CLI with one fixed `--settings-dir`. Output in
  `rv_cascade.out`). There are 13 single fills. For each I compared the derived files, the four printed forms and the
  wrapper's `check` on all four indexes, before and after. **All OK.**

  | Fill | Forms that change | Files that change |
  |---|---|---|
  | OLMo branch 128, full with a record, full with a reason | X[olmo2-7b], Y[olmo2-7b] | OLMo's oext_eval, oext_eval_y, oext_unit, oext_unit_y, lean, both OLMo indexes |
  | Llama branch (the same three) | X[llama31-8b], Y[llama31-8b] | the same for Llama |
  | θ0 job pin, per family | that family's X and Y | the same, plus that family's W1-18 settings |
  | Llama recipe G; OLMo G re-pin | that family's X only | `oext_unit__F`, `OEXT-78B__F` |
  | B+Qi, per family | that family's Y only | `oext_unit_y__F`, `OEXT-78B-Y__F` |
  | ENGINE_Y | Y[olmo2-7b], Y[llama31-8b] | both families' oext_eval_y, oext_unit_y and Y indexes |

  The wrapper's hash is the same in every form after every fill (`8b0ad90a…`). The wrapper's `check` exits 0 on every
  filled index, with a W1-18 record where one is pinned. **Cumulative, in T-O2's order** (θ0 OLMo, θ0 Llama, OLMo
  branch 128, Llama G, Llama branch full with a record, ENGINE_Y, B+Qi OLMo, B+Qi Llama): each step changes only its
  own forms. X[olmo2-7b] last changes at OLMo's branch, X[llama31-8b] at Llama's branch, and each Y form at its B+Qi.
  So each `OEXT_78B[F]` is filled once (O11). A family's branch or θ0 fill changes both of that family's engines,
  which R-5's "that family's" allows. Observation (I): each index also carries the other family's manifest pin
  (`other_manifests`) and the shared O-ext bank and record pins. A re-pin of those (not a listed fill) would reach
  every index.

## 2. O6: not closed (OR1)

- The builder's `test_the_documented_fill_leaves_the_committed_state_checks_green` passes (M: suite). But it checks
  `consistency()` on a `--settings-dir` copy. It does not check the suite after the procedure the maker's header
  documents (`make_oext_settings_78b.py:38-41`: edit `settings/oext_pins_78b.json`, run the maker, run the tests).
- M (`rv_fill.py`, a scratch copy of WS as the mutation runner builds it, the maker run with its defaults, then
  `pytest scripts/scale78b/tests`, sandboxed):

  | Scenario | Suite | Track O failures |
  |---|---|---|
  | no fill (control) | 4 failed, 303 passed, 57 skipped | 0 (the 4 are `test_s1_olmo2_7b_check_guard.py`, mirror-only) |
  | θ0 OLMo (T-O2 step 1, K1's measured value) | 5 failed, 302 passed | 1: `test_theta0s_null_job_pin…` (w1_18.py:141) |
  | θ0 both, then OLMo branch 128 (a synthetic text-free record) | 10 failed, 297 passed | 6: `test_the_committed_state_is_consistent` (TypeError, files.py:125); `test_the_documented_fill…[bqi-olmo, engine-y, llama-g, theta0-olmo]` (KeyError 'olmo2-7b', :125); the θ0 test |
  | everything (θ0, both branches 128, Llama G, ENGINE_Y, both B+Qi; stand-ins unlike the suite's own) | 11 failed, 296 passed | 7: the same causes |

  A first "everything" run whose stand-ins equalled the suite's own stand-ins (G = the 1e-4 G config, B+Qi = MAIN)
  also failed two cascade cases. That came from my coincident values, not from the code. With different stand-ins
  they pass, and I do not count them.
- No other scale78b test pins a value that a fill changes (M: the only failures beyond the control are Track O's).

## 3. O7 / R-6: closed (M)

`check --w1-18-record` reads the record through the unchanged `oext_eval.read_w1_18` (`oext_eval.py:359-385`, file
`8c4290921f…`, equal to MAIN@3481d85). It runs under the family's O-ext settings and W1-18 globals, then compares the
record's unit names with the family's W1-18 units (R: `oext_78b.py:498-516`). The records below were made by the real
`overrefusal_checks` main through the wrapper, on fixtures (`test_rv_probes.py` D1-D3). Refused (exit 2, nothing
printed on stdout):
- wrong family: the other family's record, its hash pinned by mistake;
- stale: the family's settings were edited after the run;
- wrong branch: a failing record under 128, a passing record under full, a record given with a `full_reason`;
- other units: renamed, one more, one fewer;
- missing (pinned but not given), unpinned (pending, given), a directory, a repeated flag;
- with the provenance kept: another cut, a verdict that is a string, version 2, another settings hash.

The right record passes on X and on the Y index. A full branch with a reason and no record passes. **I could not get
a bad record accepted.** The only route left is a forged record that carries the family's settings hash and is
pinned by its own hash. That is outside what a Mac check can catch (I).

## 4. R-7, R-8, R-9

- **R-7: passed (M, R).** Both committed W1-18 settings have `judge.device = "cuda"`. `overrefusal_checks.py:558`
  uses `args.device or settings["judge"]["device"]`, so leaving out `--device` gives cuda. `check_content` accepts
  the file once θ0 is filled (M: the fill copies report it "valid").
- **R-8: passed against WS's RK; refused by K1's RK (OR3).** `--oext-78b-y F` exits 0 for both families
  (`form-y-*.json`). Each Y form holds the wrapper, the unit command's five 1B files, `OEXT-78B-Y__F`, `oext_unit_y__F`,
  `oext_eval_y__F` and the W1-18 settings, and no lean copy. WS's `oext_form_problem` gives `None` for all four forms.
- **R-9: built as ruled, with gaps (OR2, OR7).** It reads COMPLETE.json by its pin, compared before parsing (R:
  `:532-541`). job.json, generations and guard are hashed, never parsed: M (E6) junk bytes with their true hashes
  pass. Each of these is a problem with exit 2: an unlisted file, a changed file, a COMPLETE.json off its pin, a
  job.json off its pin, a missing folder, and a folder linked out of the data root (E5). The output holds no fixture
  sentinel in 7 cases, normal and problem (E4). Only a non-hex value inside COMPLETE.json reaches the output (OR7). I
  did not run it on the real units.

## 5. No regression of what passed before (M)

- **No label lie** (my re-run of the first verifier's label probes, adapted to the per-index API, `test_rv_probes.py`
  A1-A3):
  - a unit settings file that names the 1B O-ext path, or either family's committed O-ext path, refuses ("oext names
    the O-ext module and its settings file"; no folder; globals unchanged);
  - a relocated index (all hashes equal) refuses, because the label comes from the folder that is read, and the true
    folder runs;
  - on a simulated engine Y (`s1.code_identity` patched for the test), a Y unit file naming the X O-ext file refuses,
    and the true Y label is "valid".
  - The builder's lean label test (the 1B path) passes in the suite.
- **Globals restored, and no leak across calls** (B1-B4):
  - W1-18 run in one process for OLMo, then Llama, then OLMo, then a cross-wired data root that refuses. Each record
    names its own settings, and the globals equal the start after each call.
  - `unit` run in one process for OLMo, then Llama, then OLMo, with per-family W1-18 settings. Each `job.json` names
    its own settings, O-ext settings and W1-18 record hashes.
  - argparse `SystemExit` inside `ou.main`.
  - a validator refusal inside `check`.
  - The builder's RuntimeError tests for W1-18 and the lean copy pass.
- **The lean copy's parity.** `lean_eval_job_78b.py` is unchanged since R1 (`fc0372ca…`). Its `diff` against
  `git show 3481d85:scripts/stage1_s1/lean_eval_job.py` (`82461c13…`, equal to `lean_copy_spec.SOURCE_SHA256`) shows
  only the head paragraph, the `oext_eval` import, the new global, the :229 comparison and the program name
  (`lean_diff.txt`).
- **The 1B files are unchanged.** I compared all 698 tracked blobs under `scripts/stage1`, `scripts/stage1_s1`,
  `runkit/stage1-olmo`, `runkit/stage1-78b`, `scripts/scale78b`, `experiments/safety_selection` and the two frozen
  readers with `git ls-tree -r 3481d85` in MAIN, by `git hash-object`: **0 differ**. WS has no tracked change.

## 6. Tests and mutants (M)

- **Suite.** `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS: **307
  passed, 57 skipped**, exit 0 (40.6 s), as the builder reported.
- **The builder's spec** (`b40c843b…`, 67 mutants) ran in 4 shards of 17, 17, 17 and 16, each with its own baseline
  by the same command (99 passed). The shards took 3.3, 2.2, 1.6 and 0.8 min (`mut-rv-{1..4}.json`). **67 of 67
  killed, 0 survived, 0 invalid, 0 ERROR lines.** The runner's mirror copies `scripts/scale78b` and links WS's other
  files, and the conftest asserts that the package is the copy's (R: `run_mutants_oext_78b.py:43-58`;
  `tests/oext/conftest.py:26-30`).
- **Weak kills (observations).**
  - `O-c-literal` dies first on the `CODE` hash refusal inside `check` (`test_the_pinned_record_passes_the_check`).
    Any edit to the copy dies that way or on the rebuild test, so it exercises the copy's freeze, not the literal's
    behaviour. That is acceptable for a frozen copy.
  - 17 mutants (16 on the maker, plus R6-w-no-validation) die first on `test_the_committed_state_is_consistent`, whose first step is the
    maker's `--check` against the committed files: the golden comparison the first verifier noted. The failing
    direction of `--check` itself was untested (OR6, RV-m-check-always-ok).
- **Proposed mutants** (`rv_mutation_spec.json`, `9e200164…`, 11 mutants, run in scratch source roots, never in WS).
  Against the builder's suite: 3 killed and **8 survived** (`rvmut-a.json`). With my targeted probes added
  (`test_zz_rv_targeted.py`): all 8 killed, 0 invalid (`rvmut-b.json`). See OR6.

## 7. The builder's notes for K1/K3: partly incomplete

- "Index arguments from `OEXT_78B[F]` / `OEXT_78B_Y[F]`": right for `unit`, `lean` and `unit --engine Y`. **Wrong
  for `w1_18`** (OR4): that pin is null during the W1-18 pod. K1 has `W1_18_78B`, and no form is defined for it. The
  index names clash with K1's R-5 regex (OR3).
- "The pack runs `check` before any O-ext pod (with `--w1-18-record` once a branch is pinned)": right, and R-6's check
  works (§3). Caveats:
  - the pack must pass the kit's pinned index SHA-256, not the file's own hash. The §10.1 R-9 command self-hashes the
    index, which is fine for R-9 only;
  - it must read the exit code, knowing that a waiting role is reported as exit 0 (OR8);
  - Y files are never validated on the Mac (concern C3).
- **O10's list** (frozen readers `8848340107bd…` and `1740663bc9e4…`, the lexicon pins `5a27dd04…` and `bbbc71e9…`,
  the judge recipe, the guard model, the tokenizer, the prepared set, the side units) matches the W1-18 settings'
  `frozen_reader`, `lexicon`, `judge` and `prepared` blocks (M: paths and hashes printed) and what
  `overrefusal_checks.run` reads (R: `:410-452`, `bank_prompts` `:142-163`, `limits_common.frozen_reader` `:71-97`,
  `load_lexicon` `:240-260`). `scripts/stage1/labels.json`, read by every settings check (`s1common.py:68`, `:198`),
  is not in any form. It is already in `stage1_rules.py:262`'s pins (R), so it is shipped. **Missing:** the W1-18
  record's place under Branch 128 (OR4).

## Concerns and open points for the lead

- **C1 (OR4, lead).** Which pin gives the W1-18 pod its index, option (a) or (b). Where the W1-18 record lives.
- **C2 (OR3, lead).** Which index names win, Track O's or K1's.
- **C3.** `check --engine Y` validates no Y file on the Mac: they are "engine None (validated only on that engine)".
  It could validate them with `s1.code_identity` set to the file's own `engine_x`, as my A3 probe does. That would
  catch label and recipe errors in Y files at $0. This is not ruled, so I list it and decide nothing.
- **C4.** R-2 says K1 holds measured θ0 job pins. Track O's pins file holds them null. The lead's T-O2 step 1 brings
  them together, and OR1 has to be fixed before that.

## Commands run (all foreground unless noted; exit status)

- Reads: r1-common, r1-o.md, r1-o-verify.md, GXB (all seven sets), K1's report (R-4 and R-5 parts); the WS sources
  `oext_78b.py`, the maker, the tests and fixtures, `oext_eval.py`, `oext_unit.py`, `overrefusal_checks.py`,
  `limits_common.py`, `s1common.py`, `family_probe_reading.sealed`, the engine's `write_complete`; RK's and K1's
  `oext_form_problem`. Exit 0.
- `shasum` of the 30 files (equal to §10.2); `git ls-tree` and `git hash-object` over 698 blobs (0 differ); the lean
  `diff`. Exit 0. (A first blob loop used the zsh-reserved name `path`, broke `PATH` and gave exit 127. I re-ran it
  with other names.)
- Suite in WS: 307 passed, 57 skipped, exit 0.
- `rv_cascade.py` (twice: the second run makes the cumulative records after the θ0 fills): exit 0, ALL OK.
- `rv_fill.py`, 5 runs (none, θ0, branch, everything twice): each exit 0, suite counts as in §2.
- `test_rv_probes.py` against WS: the first two runs had 1 failure each. Both were my probes' setup (B4 needed a
  record, G4 needed a written settings folder). After those fixes: 58 passed, exit 0.
- Maker `--check` (exit 0, "checked 16 files"). `--oext-78b` and `--oext-78b-y` for both families (exit 0). Wrapper
  `check` on the four committed indexes (exit 0 each). `rk_forms.py` (exit 0). `rv_bqi_blocks.py` (exit 0).
- Mutation:
  - a baseline-only run (99 passed, 13 s);
  - shards 1 and 2 in parallel: the tool moved the command to the background after 180 s; I worked on and read the
    output after it ended; exit 0;
  - shards 3 and 4 in the foreground, exit 0;
  - proposed run a (exit 1: 8 survived);
  - proposed run b: moved to the background after 180 s and read after it ended; exit 0, 8 killed.
  - I deleted every mirror and scratch source root after its run.
- `date -u` before each time written.

**Evidence** (`R/r1-o-reverify-scratch/`):
- scripts: `rv_cascade.py`, `rv_fill.py`, `test_rv_probes.py`, `test_zz_rv_targeted.py`, `make_rvspec.py`,
  `mksrc.py`, `rk_forms.py`, `rv_bqi_blocks.py`;
- outputs: `rv_cascade.out`, `rv_fill_{none,theta0,branch-olmo,everything}.out`, `mut-base.json`,
  `mut-rv-{1..4}.json`, `rvmut-{a,b}.json`, `rv_mutation_spec.json`, `form-{x,y}-*.json`, `check-*-{X,Y}.json`,
  `lean_diff.txt`, `lstree-3481d85.txt`.

## Acceptance criteria (the brief's items)

| Item | Result | Evidence |
|---|---|---|
| 1 O1/R-5: one index per family and engine; no index hash in the wrapper; the index checked on every command; each fill reaches only its own family or engine | **passed** | §1; `rv_cascade.out`; C1 |
| 2 O6: the documented fill leaves the suite green; no test pins a fill-changed value | **failed** | OR1; `rv_fill_*.out` |
| 3 O7/R-6: bad records refused on the Mac through the unchanged reader; no bad record accepted | **passed** | §3 (D1-D3) |
| 4 R-7 cuda; R-8 Y form accepted by RK; R-9 by pin, hash-only, names and hashes only | R-7 passed; R-8 passed on WS's RK (refused by K1's: OR3); R-9 passed as ruled, with gaps (OR2) and one print gap (OR7) | §4 |
| 5 No label lie; globals restored; lean parity; 1B files unchanged | **passed** | §5 |
| 6 Suite 307/57; 67/67 killed in shards; weak mutants and untested branches | suite and 67/67 reproduced; **8 untested branches** (OR6) | §6 |
| 7 The builder's K1/K3 notes complete and correct | **partly**: the W1-18 index source is wrong, the names clash, the record's place is undefined | §7; OR3, OR4 |
| A real 7-8B run, or R-9 on the real units | not tested (no pod; never run on real units, by the brief) | — |
