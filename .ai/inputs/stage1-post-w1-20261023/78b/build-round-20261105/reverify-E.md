# Re-verify E (the per-family scorer layer, 7-8B), fix round 3

Started 2026-11-05 18:35 UTC; finished 18:53 UTC (M: `date -u` before each time written here). Role: adversarial
re-verifier for General Implementation X. Worktree (read-only for me):
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-e`
at HEAD 953f520 (M: `git rev-parse --short HEAD`). No file in the worktree or the main checkout was edited (M: `git
status --short` in the worktree lists the same 5 round-3 `??` paths before and after; `git diff --quiet HEAD` exits 0;
no `__pycache__` under `scripts/`; every command in the main checkout was a read). No git state changed anywhere. No
pod, spend, network, install, download, agent or message. No forbidden folder opened; no study text printed or stored
(the only texts in play are the 1B test fixtures' synthetic sentences, which the fixer's tests scan for).

Tags: M measured (command given), R read (path:line), E estimated, I inferred.

## 0. Verdict: VERIFIED_WITH_MINOR

D1, D2, D3, C4 and C5 are closed as the fixer says. The suite passes (93; whole folder 158 passed, 2 skipped), the
maker's `--check` passes, no 1B file changed, and 17 of my 20 hand mutants are killed; the 3 survivors are two
ruling-prose edits that no test can read and one guard that the real 1B main makes unreachable. PP1, PP3 and PP4 are
stated correctly. Three minor findings: an abbreviated 1B flag (`--li`, `--lo`, `--ou`) bypasses the PP2 guard and the
doses step while the 1B parser accepts it (M; the kit's command lines are fixed strings, so it is a hole in the guard,
not in the plan); SCORERS-78B.md section 6 numbers its last four items 4-7 after a 6; a line cite is off by one.

## 1. Files changed by me

- This report.
- Scratch under `reverify-E-scratch/`: `mutants_rv.py` (the harness), `mutants-rv-results.jsonl` (21 rows),
  `abbrev-bypass-check.txt`, `pytest-scorers-reverifier.log`, `pytest-scale78b-all-reverifier.log`. The mutant root
  (symlinks to the worktree plus real copies of `scripts/stage1` and `scripts/scale78b`) was removed after the runs; the
  harness rebuilds it. All deletable after the lead reads this.

## 2. Inputs read

The lead's rulings PP1-PP6; Part 1 section 10 and its grep for SD-600 (none: SD-600 is not a 7-8B list); fix-E.md,
verify-E.md (and its `mutants.py`), build-E.md section 7; the fixer's `before_after.py` and `before-after.jsonl`;
`scorers_78b.py`, `make_scorer_settings_78b.py`, `pins_78b.json`, SCORERS-78B.md, the five test files and conftest;
`scripts/stage1/make_untuned_answers.py` (whole); `s1common.py:560-630`; `runkit/stage1-olmo/stage1_rules.py:650-725`
(`s3_orig_pin`) and `:87`; `job_runner_stage1.py:24-30, :160-170, :420-460`; `runkit/stage1-78b/rules_78b.py:95-140,
:320-340` and its grep; `make_recipe_s78.py:5-14`; the 1B test's `settings_for` and `FakeGenerator`
(`scripts/stage1/tests/test_make_untuned_answers.py:24-80`). The derived settings' list, loss, chunk and doses fields
were printed as names, counts and booleans only (M, `.venv` python `-I -B`).

## 3. Per defect: closed? does a test fail without the fix? my hand mutants

### D1 (PP2: two untuned-answers calls per pod) - closed

- Code (R: `scorers_78b.py:195-214`): `named_values` reads each `--list` / `--loss` NAME (both `--flag value` and
  `--flag=value` forms); `check_untuned_calls` refuses `s4` beside another list or any loss. `preflight` runs it before
  the recipe checks (R: `:284-285` before `:292-296`). `run_kind` builds the doses only when `s4` is among the call's
  lists (R: `:458-459`). The settings carry the two command lines (`pins_78b.json shared.untuned_calls_78b`, copied into
  both untuned files as `doses.calls_78b`; M: equality printed). SCORERS-78B.md sections 2, 3, 6 item 4 state them.
- Test: `test_untuned_two_calls_78b.py` (5 tests). The fixer's before/after rows hold (R: `before-after.jsonl`): on the
  round-3 wrapper with only the index call-time defaults, the two-calls test fails at call 1 with the C4 message (the
  old wrapper ran `build_doses` on every untuned call); the PP2 test fails with `AttributeError: check_untuned_calls`.
- My mutants (section 7): d1a (the check never refuses) killed by the PP2 test; d1b (doses on every untuned call) killed
  by the two-calls test at call 1; d1c (`named_values` keeps `s4=a:x` whole) killed by 5 tests; d1d (the check moved
  after the recipe checks) killed by 4 tests, among them the "bogus recipe path refuses with PP2" case; d1e (`len > 2`),
  d1f (a loss beside `s4` allowed) and d1g (the `--list=` form ignored) each killed by the PP2 test.
- Gap (minor, RV-E-1): the 1B `main()` parses with argparse's default `allow_abbrev=True`, so `--li s4=…` is `--list
  s4=…` to the 1B script but invisible to `named_values`. M (`abbrev-bypass-check.txt`): the whole `preflight` on
  `--recipe MAIN --recipe-s MAIN --li s4=a:0… --list s3=b:0… --out o` returns `lists ['s3']` with no refusal; the real
  `mua.main(["--li", …, "--settings", "/nonexistent"])` returns 2 with `REFUSED: FileNotFoundError`, which comes after
  argument parsing (an argparse rejection would be a `SystemExit`); likewise `--ou o` is `--out` to the 1B script while
  `flag_value(argv, "--out")` is None (no doses step, no wrapper record). So one abbreviated flag re-opens the D1 path
  (both lists in one call, the S4 fallback's exit 3 dropping `s3_orig.pool.json`). Reach: only a hand-typed or
  mis-templated command; the kit's lines are fixed strings. Fix: refuse any `--` token of an `untuned_answers` call
  whose flag part is not one of the 1B script's five long flags (`--recipe`, `--recipe-s`, `--list`, `--loss`,
  `--out`), plus one test line per form; or normalise with an argparse that has the same five flags.

### D2 (PP4: every wrapper kind on engine X) - closed (documentation; the enforcement was already the frozen check)

- Text: `pins_78b.json shared.engine_rule_78b`; copied into all 18 files as `family_78b.engine_rule` (M: 18 of 18 equal
  the pins text; `engine_x` equal in all 18); SCORERS-78B.md after the section 2 table and section 6 item 2.
- Enforcement: `s1common.check_settings` refuses another engine identity (R: `s1common.py:590-592`).
- My mutants: d2a (the maker drops `engine_rule`) killed by the regeneration and `--check` tests (presence guarded);
  d2c (the derived files pin another `engine_x`, regenerated and re-pinned) killed by 25 tests, the frozen
  `check_settings` among them (enforcement guarded); d2b (the rule's prose says "engine Y", regenerated and re-pinned)
  SURVIVED: no test reads the prose. Expected for a ruling text; a one-line assertion that `engine_rule` contains
  `engine_x[:8]` and "PP4" would close it cheaply.

### D3 (PP4: the classifier under S_78; the kit's S_78 key check) - closed as a statement (the kit edit is the kit round's)

- Text: `pins_78b.json shared.classifier_recipe_78b`; SCORERS-78B.md section 2 classifier row and section 6 item 3.
  Cites hold: `rules_78b.py:136` is `S78_KINDS = frozenset({"retrain", "rep_pass"})` with the comment "A1's attributes
  pass" (R); `check_keys` is `:325-337` and accepts S_78 only for `S78_KINDS` (R: `:333-337`).
- Code: `score_classifier__F.json` `pins.recipe_sha256` is S_78 (null until the event); the wrapper's preflight refuses
  the classifier while it is null (the suite's null-pin tests).
- My mutants: d3b (the maker pins the classifier to the main recipe) killed by `test_the_per_family_values` (both
  families); d3a (`classifier_recipe_78b` and `kind_names_78b` deleted from the pins, regenerated and re-pinned)
  SURVIVED: the maker reads neither key, so they reach no derived file and no test. Expected; a cheap guard is to copy
  them into `score_classifier__F.json` and the rep_pass / score_edit files' `family_78b` as `engine_rule` is copied.

### C4 (the doses refusal after the 1B pass, exit 2) - closed

- Code: `DosesRefusal(s1.Refusal)` with `out` (R: `:119-124`); `run_kind` wraps `build_doses` (R: `:460-463`); `main`
  catches it first and prints `REFUSED after the 1B pass: the 1B outputs are written in <out>; the doses were not written
  (<reason>)` (R: `:491-494`). Test: `test_a_doses_refusal_after_the_pass_names_the_written_1b_outputs_and_exits_2`
  (the 1B files stand, no `doses/`, no wrapper record). Before: the round-3 message `REFUSED: answers_s4.json is not
  the file the record names (nothing written)` (R: `before-after.jsonl`).
- My mutants: c4a (the `DosesRefusal` except removed), c4b (`run_kind` re-raises the plain Refusal), c4c (the message
  without `<out>`): each killed by that test.

### C5 (repeated flag; the record's exit code) - closed

- `test_flag_value_takes_the_last_occurrence_as_argparse_does` (three forms plus argparse's own answer);
  `record["exit_code"] == code` asserted in the family CLI test (0), the two-calls test (0, both calls) and the exit-3
  test (3). My mutants c5a (first occurrence; verify-E's m09) and c5b (`exit_code` always 0; m10) each killed by one of
  those tests. On the round-3 wrapper the flag test fails for the missing `named_values` (R: `before-after.jsonl`), so
  the m09 kill is the evidence for the flag rule, as the fixer says.

## 4. The two command lines against `make_untuned_answers.py`'s real behaviour at exit 3 (R, whole file)

- Exit 3 is set only for an `s4` list with fewer keeps than `spec["keep"]` (R: `:285-290`). The S3 call has no `s4`
  list, so it cannot exit 3; the fixer's sentence holds.
- At exit 3 `full` is filtered to `answers_*.json` (R: `:317-318`) and the record is added after (R: `:341`): `s4.json`
  and any `s3_orig.pool.json` are dropped. This is verify-E's D1 basis; the split makes it unreachable by the kit's
  lines (and reachable only by RV-E-1's abbreviation).
- The loss table runs when `--loss` lists are given or when `s4` completed and `loss.include_s4` (R: `:300-304`). So
  the S4-alone call computes the W1-06 `s4` rows itself when it completes and omits them in the fallback (exit 3); no
  `--loss` is needed there. The fixer's concern 1 (the strict "alone") costs nothing.
- Call 1 (`--list s3=s3_safe.pool.json:6801652c… --loss s1=… --loss s3_safe=…`): the 1B `named()` takes NAME=PATH:SHA256
  each name once (R: `:362-371`), the names must be in the settings' `lists` and `loss.lists` (R: `:225-227`); the
  derived file has lists s3, s4, sd600 and `loss.lists` [s1, s3_safe], `lists.s3.size` null (so 861 items are
  accepted), `max_new_tokens` 512 (M). `read_list` accepts a `stage1 text pool` as a list (R: `:60, :71`).
- Call 2 (`--list s4=s4_candidates.json:798613c4…` alone): `lists.s4.size` 512, `keep` 192, `max_new_tokens` "rec",
  chunk 32 (M). The wrapper's `build_doses` reads the record and `answers_s4.json`, both of which survive exit 3; kept
  < 48 returns 3; 48 <= kept < 192 fires the fallback and returns 0 (Part 1 section 10's pre-set fallback); kept >= 192
  gives the 1B's exit 0 with `s4.json`, whose ids `build_doses` checks against the kept order (R: `:358-362`).
- Two `--out` folders are needed: `s1.write_new_files` refuses a non-empty folder (R: `s1common.py:605-610`); the map
  gives `<job>/untuned` and `<job>/untuned-s4`. The stage-1 kit's `s3_orig_pin` reads `job-K/untuned/` and needs only
  the record and the pool among the job's outputs (R: `stage1_rules.py:670-700`); extra outputs do not hurt it. Note for
  the kit round: `wrapper_78b_record.json` is an extra file in `<job>/untuned/` that the 1B record's `full_files` does
  not list; the 7-8B record-done must expect it.

## 5. PP1, PP3 and PP4 stated correctly?

- PP1: SCORERS-78B.md section 4 item 1 ("ruled: PP1"; the recorded `recipe_s` hash is the main recipe's; Part 2 states
  it; the same for `write_add_edit__F.json`), `pins_78b.json shared.untuned_recipe_s_basis` (opens with PP1), section 2
  row ("MAIN_F twice (PP1, section 4)"). Correct (R against PP1). The cite `make_untuned_answers.py:82-93` holds.
- PP3: section 6 item 1 and the section 2 rows `rep_pass` (REQ-3's representation pass) and `a1_pass` (A1's attributes
  pass; RP:43's 6-11 h; the 16.5 h cap at most; its own E cap; both need S_78 and the anchor file; `rules_78b.py` and
  Part 2 use the names; at HEAD the kit still says `rep_pass` for A1's pass, R: `rules_78b.py:44, :136`). Correct.
- PP4: the engine-X paragraph after the section 2 table and section 6 items 2 and 3; `shared.engine_rule_78b` and
  `shared.classifier_recipe_78b`. Correct in substance. One cite is off by one: `s1common.py:589-591` is written in the
  pins, in SCORERS-78B.md and in PP4 itself; the engine check is `:590-592` (`identity =`, `if`, `raise`; M: `sed -n
  '588,593p'`). Trivial (RV-E-3).

## 6. The whole scorer test folder (and the whole scale78b folder)

- `scripts/scale78b/tests/scorers`: 93 passed in 19.89 s, 0 skipped (M; log `pytest-scorers-reverifier.log`; the
  harness's baseline run of the same folder: 93 passed, pytest exit 0).
- `scripts/scale78b/tests`: 158 passed, 2 skipped (track C's scipy tests) in 34.33 s, exit 0 (M; log
  `pytest-scale78b-all-reverifier.log`).
- `make_scorer_settings_78b.py --check`: "19 of 19 files equal their regeneration", exit 0 (M).
- Hashes of the fixer's six changed files equal fix-E.md section 1 (M: `shasum -a 256`; `scorers_78b.py` 11ebe5be…,
  the maker 607606d6…, `pins_78b.json` aef5b78b…, `PINS-78B.json` 8b9d8146… = the literal, the two test files
  fccc61e0… and af74738f…).

## 7. Hand mutants (20 new, each on a fresh copy, the whole scorer suite; `mutants_rv.py`, `mutants-rv-results.jsonl`)

| Mutant | Item | Change | Verdict | Killed by |
|---|---|---|---|---|
| baseline | - | none | 93 passed, exit 0 | - |
| d1a | D1 | `check_untuned_calls` never refuses | KILLED (1) | the PP2 test |
| d1b | D1 | doses built on every untuned call | KILLED (1) | the two-calls test (call 1) |
| d1c | D1 | `named_values` keeps the whole spec | KILLED (5) | all five new tests |
| d1d | D1 | the PP2 check moved after the recipe checks | KILLED (4) | the bogus-recipe PP2 case and the wrapper-record `checked.lists` |
| d1e | D1 | refuses only 3 or more lists | KILLED (1) | the PP2 test |
| d1f | D1 | a loss beside `s4` allowed | KILLED (1) | the PP2 test |
| d1g | D1 | the `--list=` form ignored | KILLED (2) | the PP2 and flag tests |
| c4a | C4 | `main` has no `DosesRefusal` branch | KILLED (1) | the C4 test |
| c4b | C4 | `run_kind` re-raises the plain Refusal | KILLED (1) | the C4 test |
| c4c | C4 | the message without `<out>` | KILLED (1) | the C4 test |
| c5a | C5 | `flag_value` first occurrence (m09) | KILLED (1) | the flag test |
| c5b | C5 | record `exit_code` always 0 (m10) | KILLED (1) | the exit-3 test |
| x1 | D1 | doses only on the 1B exit 0 | KILLED (2) | the two-calls and exit-3 tests |
| x2 | D1 | fewer than 48 kept returns 0 | KILLED (2) | the doses unit test and the exit-3 test |
| x3 | - | the wrapper-record exists check dropped | SURVIVED | near-equivalent: the 1B `write_new_files` refuses a non-empty `--out`, so the record can pre-exist only with a stubbed 1B main |
| d2a | D2 | the maker drops `engine_rule` | KILLED (2) | regeneration, `--check` |
| d2b | D2 | the rule's prose says engine Y (regenerated, re-pinned) | SURVIVED | prose; no test reads it (expected) |
| d2c | D2 | derived files pin another `engine_x` (regenerated, re-pinned) | KILLED (25) | the frozen `check_settings` test, the parity tests |
| d3a | D3 | `classifier_recipe_78b` and `kind_names_78b` deleted (regenerated, re-pinned) | SURVIVED | prose the maker never copies; no test reads it (expected) |
| d3b | D3 | the classifier pinned to the main recipe (regenerated, re-pinned) | KILLED (2) | `test_the_per_family_values` x2 |

17 killed, 3 survived (two ruling texts, one near-equivalent guard). Every D1, C4 and C5 mutant is killed by the new
test file; the D2 and D3 code paths are killed by the settings tests and the frozen 1B check.

## 8. Commands run (cwd = the worktree unless stated; main venv = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python`; `PYTHONDONTWRITEBYTECODE=1` on every Python run)

| # | Command | Exit |
|---|---|---|
| 1 | `mkdir -p reverify-E-scratch; date -u` (18:35 UTC); `ls -la reports/` | 0 |
| 2 | `git status --short; git diff --quiet HEAD; git status --short --untracked-files=all; git rev-parse HEAD; find scripts/scale78b -type f; find scripts -name __pycache__` | 0; 0; 5 paths / 29 files; 953f520; none |
| 3 | reads (Read, `cat`, `sed -n`, `grep -n`) of every input in section 2 | 0 |
| 4 | `.venv` python `-I -B` printing the derived untuned settings' list, loss, chunk and doses fields; `engine_rule` equality in all 18 files; `calls_78b` equality; the index's count | 0 |
| 5 | main venv `-B -m pytest -q -p no:cacheprovider -rs scripts/scale78b/tests/scorers` (tee to the log) | 93 passed in 19.89 s (the shell line did not capture pytest's status: a bash `PIPESTATUS` under zsh; the harness baseline below captured 0) |
| 6 | `shasum -a 256` of the six changed files; `sed -n '588,593p' s1common.py`; the cites in `stage1_rules.py:87`, `job_runner_stage1.py:24-30`, `rules_78b.py:44`; `grep -n full_files stage1_rules.py`; `sed -n '5,14p' make_recipe_s78.py` | 0 |
| 7 | main venv `-B -c` (via heredoc): `check_untuned_calls(["--li", "s4=…", "--list", "s3=…", "--los", "s1=…"])` and a 1B-shaped argparse on the same argv | 0; lists `['s3']` vs argparse `['s4', 's3']`, loss `['s1']` |
| 8 | main venv `-B -m pytest -q -p no:cacheprovider -rs scripts/scale78b/tests` (whole folder, to the log) | 0: 158 passed, 2 skipped in 34.33 s |
| 9 | main venv `-I -B scripts/scale78b/make_scorer_settings_78b.py --check` | 0: 19 of 19 |
| 10 | `git status --short; git diff --quiet HEAD; find scripts -name __pycache__ \| wc -l` (after my runs) | 5 `??` paths; 0; 0 |
| 11 | `python -B mutants_rv.py baseline d1a … d1g` (cwd reverify-E-scratch; 8 suite runs, 2 min 47 s) | 0; rows in `mutants-rv-results.jsonl` |
| 12 | `python -B mutants_rv.py c4a c4b c4c c5a c5b x1 x2 x3` (8 runs, 2 min 54 s) | 0 |
| 13 | `python -B mutants_rv.py d2a d2b d2c d3a d3b` (5 runs with the maker, 1 min 42 s) | 0 |
| 14 | main venv `-B` (heredoc, tee to `abbrev-bypass-check.txt`): the whole `preflight` on the abbreviated argv; `mua.main([... "--li" ..., "--settings", "/nonexistent/x.json"])`; the same with `--ou`; nothing written | 0; see section 3 D1 |
| 15 | `rm -rf reverify-E-scratch/mutroot; ls -la; wc -l results; git status --short \| wc -l; git diff --quiet HEAD; git rev-parse --short HEAD; find __pycache__; shasum scorers_78b.py; (main checkout) git status --short \| wc -l; date -u` (18:53 UTC) | 0; 5; 0; 953f520; 0; 11ebe5be…; 18 lines (other sessions' files; I wrote nothing there) |

Longest command: 2 min 54 s. Nothing ran in the background. No job needs a re-run.

## 9. Acceptance criteria (the lead's list for this round)

| Criterion | Result | Basis |
|---|---|---|
| D1 closed by PP2 with a test (two calls; the S3 outputs survive a firing S4 fallback; the completeness check accepts them) | passed (minor gap RV-E-1 in the guard) | sections 3, 4, 7: 9 D1 mutants killed; the before/after rows; the abbreviation bypass is M |
| D2 closed by PP4 (engine X in SCORERS-78B.md 2 and 6 and the pins) | passed | 18 of 18 files carry the rule (M); d2a and d2c killed; d2b survives as prose |
| D3 closed by PP4 (the classifier under S_78; the key check; stated in 2 and 6 and the pins) | passed as a statement | the cites hold (R); d3b killed; d3a survives as prose; the `rules_78b.py` edit is the kit round's |
| PP1 and PP3 in SCORERS-78B.md (and PP4) | passed | section 5; one cite off by one (RV-E-3) |
| C4 with a test | passed | three mutants killed |
| C5 with tests | passed | m09 and m10 equivalents killed |
| all tests pass (the scorer folder and the parity tests) | passed | 93 passed; 158 passed, 2 skipped (M) |
| no 1B file changed | passed | `git diff --quiet HEAD` exits 0; `test_the_1b_scripts_and_settings_are_byte_identical_to_the_pins` in the suite; the fixer's hashes match (M) |
| nothing prints text | passed | my runs printed names, counts, hashes and the refusal texts only; the new tests scan their records and output for the fixtures' texts (R) |
| CUDA paths; the real pod runs | not tested | CPU fixtures only, as in rounds 3 |

## 10. Defects found

| Id | Severity | What | Where | Fix |
|---|---|---|---|---|
| RV-E-1 | minor | An abbreviated 1B flag bypasses the PP2 guard and the doses step: `--li s4=…` (or `--lo …`, `--ou …`) is read by the 1B argparse (default `allow_abbrev`) but not by `named_values` / `flag_value`; `--li s4=… --list s3=…` runs both lists in one call (D1's path) with no refusal and no doses (M, `abbrev-bypass-check.txt`). Reach: hand-typed or mis-templated lines only; the kit's lines are fixed and pinned | `scorers_78b.py:195-214` (`named_values`, `check_untuned_calls`), `:184-192` (`flag_value`) | in `check_untuned_calls` (or `preflight` for `untuned_answers`) refuse any `--` token whose part before `=` is not in `{--recipe, --recipe-s, --list, --loss, --out}`; one test with the three abbreviated forms. Or normalise argv with an argparse holding those five flags |
| RV-E-2 | minor | Section 6's items after item 6 are numbered 4, 5, 6, 7 again (parity, the Llama anchor encode, `build_s_pool`, the bundle); "section 6 item 4" is ambiguous in the raw text | `SCORERS-78B.md:167-178` | renumber 7-10 |
| RV-E-3 | minor | The cite `s1common.py:589-591` for the engine check is `:590-592` (M: `sed -n '588,593p'`); it appears in `pins_78b.json shared.engine_rule_78b`, SCORERS-78B.md section 2, and PP4 itself | `pins_78b.json:8`, `SCORERS-78B.md:70` | write `:590-592` (the pins change regenerates 18 files and the index; the maker prints the new literal) |

No blocker, no major.

## 11. Jobs for the lead

1. Merge by explicit path (KD8) as fix-E.md section 6 item 1 lists; the index literal is 8b9d8146…. The three minor
   items can ride on this merge or a follow-up (RV-E-3 changes the pins text, so the 18 files, the index and the
   literal regenerate; run `tests/scorers` after).
2. Kit round (tracks K/A): the fixer's list stands (two calls per untuned pod, `<job>/untuned` then `<job>/untuned-s4`;
   the E cap covers both; the runner reads `wrapper_78b_record.json`; two kind names `rep_pass` / `a1_pass`;
   `classifier` into `S78_KINDS`; scorer pods on engine X; the bundle carries `scripts/scale78b/scorers_78b.py` and
   `settings/`). Add: `wrapper_78b_record.json` is an extra file in `<job>/untuned/` and `<job>/untuned-s4/` that the
   1B record's `full_files` does not list; the 7-8B record-done must expect it. And: in the fallback case the S4 call's
   1B record says `complete` false with `wrapper_78b_record.json` `exit_code` 0 and `doses.fallback_fired` true.
3. Optional, cheap test guards for the two prose survivors: the maker could copy `classifier_recipe_78b` into
   `score_classifier__F.json` and `kind_names_78b` into the rep_pass and score_edit files' `family_78b` (the derivation
   test then guards them as it guards `engine_rule`); one assertion that `engine_rule` names `engine_x[:8]` and PP4.
4. Part 2 and the pins-by-event jobs: unchanged from fix-E.md section 6 items 3-4; I found nothing against them.

## 12. Unresolved concerns

- RV-E-1 is a guard hole, not a plan hole: the kit's command lines never abbreviate. It matters only if a hand-run or a
  mis-templated runner line reaches the pod; the cost of closing it is a few lines.
- PP2's strict "alone" is right by the 1B code: the S4-alone call computes the W1-06 `s4` rows itself when complete
  (R: `:300-304`), so no `--loss` is needed there (the fixer's concern 1 needs no change).
- The fallback's exit 0 beside the 1B record's `complete` false stands as the fixer and verify-E describe; the kit
  round reads the wrapper record for the S4 call.
- The keep path through the 1B `main()` is exercised with the 1B test's fake generator only; the real generation at
  keep 192 and every CUDA path are pod matters.
- The main checkout's `git status --short` lists 18 lines; they are other sessions' files. I ran only reads there.
