# Fix round, track F: F-1 (the check's scratch deletion), F-2/F-3 (README sentences, PP6), F-4 (guard-field tests)

Started 2026-11-05 18:15 UTC; written 18:29 UTC (`date -u` before each time: 18:14:37, 18:15:02, 18:28:52, 18:29:37).
Worker: self-identified Fable 5.1 (the launcher's routing evidence governs). Status: DONE.
Worktree (WS): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-f` (HEAD 953f520; untracked paths only, before and after).
Scratch (SCR): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/fix-F-scratch/`.
Rulings read first: PP1-PP6 (`.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part2-prep-20261105.md`); PP6 governs F-2 and F-3
(README sentences; no code change, because a code change means a rebuild and a new arm hash). Part 1 (frozen) not needed for this round.
Tags: M measured (command given), R read (path:line), E estimate, I inference. No text printed or stored (section 4, text check: 0 hits).
MAIN = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python`; SCI = `/Users/spiderishi/Coding/attribution/.venv/bin/python`.
Every MAIN run had `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1`; every pytest had `-p no:cacheprovider` and a `--basetemp` under SCR
(removed afterwards). All commands foreground, run from WS; the longest about 3.5 min (the mutant harness).

## 0. Summary (plain)
- **F-1 fixed** (`scripts/scale78b/s1_olmo2_7b_check.py`, an untracked file of round 3): `main` records before the check whether `--scratch-tmp`
  existed (`created`) and whether it was an empty folder (`was_empty_dir`); the `finally` block removes the folder only if this run created it
  and `--keep` is not set; in a pre-existing empty folder it removes only `scratch/list` (the recovered list this run wrote). A pre-existing
  non-empty folder is refused by the frozen `check_output_folders` rule and left as it was. Three new tests: the two survival tests FAIL on
  the old script and PASS on the fixed one (M); the third pins that a folder this run created is removed and the record written. The verdict
  record is unchanged: `9b340bf504400576f116e394fa9dd669cff623c0a35e8bb34cdd1c2ee018d2ca`, byte-identical to the verifier's (M, `cmp`).
- **F-2 and F-3 recorded** in `.ai/inputs/scale-78b-s1-llama3-20261105/README.md` ("How" item 4): one sentence each, citing PP6. `build_s1_llama3.py`
  and the three committed `out/` files are byte-identical before and after (M, SHA-256).
- **F-4 closed** by the new file `scripts/scale78b/tests/test_noise_reading_guard_fields.py` (29 tests): a synthetic family of six unit records with
  guard records, one unit's guard changed → `["guard"]` on that unit alone; every one of the 14 compared fields changed in turn → that field on that
  unit alone (`cudnn` among them); the same through the real reader on the wave-0a units. The verifier's surviving mutants **V6 and V8 now die**
  (M: V6 by 4 new tests, V8 by 10); all 13 mutants of the harness die except V3, the equivalent one, as the verifier said.
- All tests pass: the S1 set 17; the check script 10 (7 + 3 new); the fingerprint file 10; the noise reader 28 + 7 + 29 = 64 (SCI; 2 scipy tests
  skip in MAIN). No tracked file changed; no git state changed.

## 1. Files changed (all untracked round-3 files or new; SHA-256 before → after in `SCR/hashes_before.txt`, `SCR/hashes_after.txt`)
| file | before | after | what |
|---|---|---|---|
| `scripts/scale78b/s1_olmo2_7b_check.py` | `81fef90f…` | `03544f45…` | F-1: 5 lines in `main` (+3 comment lines) and the docstring's scratch sentence; `check()` untouched |
| `scripts/scale78b/tests/test_s1_olmo2_7b_check.py` | `327aeaf2…` | `c9650e28…` | 3 new tests (F-1); the 7 old ones untouched |
| `.ai/inputs/scale-78b-s1-llama3-20261105/README.md` | `258a6370…` | `a83347f1…` | F-2 and F-3: two sentences in "How" item 4 |
| `scripts/scale78b/tests/test_noise_reading_guard_fields.py` | (new) | `4a613722…` | F-4: 29 tests |
Unchanged, checked by hash (M): `build_s1_llama3.py` `a2b0a66c4e3f9f044ad5e2090cd58af195bcdfac3f372822eb1c14805495f5a3`; `out/MANIFEST.json` `a3986274…`;
`out/add_edit_record.json` `1023b4e6…`; `out/write_add_edit_llama3.settings.json` `36a39481…` (all four equal before and after). Not touched:
`fingerprint_compare.py`, `test_fingerprint_compare.py`, `test_noise_reading_rv2_2.py`, the S1 set's tests, every tracked file. The README is not
hashed into the set (the MANIFEST names the script, the record, the settings, the edit and the list; no test reads the README's hash, M: `grep`).
Scratch (SCR) holds: the before copies, the hash lists, every command's output, the mutant harness and its output, the text check and its output,
one verdict record (`olmo-check-record.json`, `9b340bf5…`). Not under WS: nothing besides the four files above. No `__pycache__` under WS outside `tmp/` (M).

## 2. Per defect

### F-1 (major): the check CLI deleted a pre-existing `--scratch-tmp` on every refusal
- **Change** (R: the diff in section 3 item 13): before `try`, `created = not scratch.exists()` and `was_empty_dir = scratch.is_dir() and not any(scratch.iterdir())`.
  In `finally`: `if not args.keep: if created and scratch.is_dir(): rmtree(scratch) elif was_empty_dir and (scratch / "list").is_dir(): rmtree(scratch / "list")`.
  The docstring's sentence says the same. The lead's rule ("delete only if this run created it and `--keep` is not set") is implemented as stated;
  the `was_empty_dir` branch is one step further: a pre-existing *empty* folder (which the guards accept) had nothing to lose, and the only thing this
  run can write into it is `list/s1.json` (text; `check()` line 134), which is now removed again, as the docstring promised. A folder that held anything
  is refused by `bsp.check_output_folders` (frozen, R: `scripts/stage1/build_s_pool.py:303-309`) and the new code never touches it.
- **Tests** (new, in `test_s1_olmo2_7b_check.py`):
  1. `test_a_pre_existing_non_empty_scratch_tmp_is_refused_and_survives`: a folder under WS `tmp/…-tests/<uuid>` holding `keep.json`, the real edit,
     `--out` under pytest's tmp → exit 2, stderr has `REFUSED` and `exists and is not empty`, the folder still holds exactly `keep.json` with its bytes,
     no record written. **Before the fix: FAILS** at the survival assertion (`scratch.is_dir()` False; M, `SCR/pytest_f1_before_out.txt`). After: passes.
  2. `test_a_pre_existing_scratch_tmp_survives_a_refusal_before_any_measurement`: the verifier's probe (a), `--edit <nonexistent>` → exit 2,
     `REFUSED: FileNotFoundError`, the pre-existing folder and its file survive. **Before: FAILS** (folder gone). After: passes.
  3. `test_a_scratch_folder_this_run_created_is_removed_and_the_record_is_written`: an absent scratch path, the real edit, `--out` → exit 0, the scratch
     folder is gone, the record is written once, `equal_as_it_stands` True, verdict `VERDICT_EQUAL`, the CLI's `record <sha256> <path>` line matches the
     file. Passes before and after (the old code removed it too; this pins the other half of the rule).
- **The verdict record is unchanged** (M): the fixed CLI on the real inputs (`--edit` the main checkout's a-3 unit `edit.json`, by exact path; `--scratch-tmp`
  under SCR) → exit 0; `record 9b340bf504400576f116e394fa9dd669cff623c0a35e8bb34cdd1c2ee018d2ca`; `cmp` against the verifier's
  `verify-F-scratch/olmo-check-record.json` → equal byte for byte; the scratch folder is gone afterwards and its (created) parent is empty, as before
  the fix. The record holds no script hash (R: `check()` lines 154-176), so the fix cannot change it.
- Run: `MAIN -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_s1_olmo2_7b_check.py` → 10 passed, exit 0.

### F-2 and F-3 (minor): README sentences by PP6
- Added to "How" item 4 of `.ai/inputs/scale-78b-s1-llama3-20261105/README.md`, after the guard description (R: README lines 55-60 after the edit):
  one lead-in clause naming PP6, verify-F's ids and why no code change (rebuild, new arm hash); then **F-2**: "the guard's forbidden folders are those of
  this script's own checkout and of `--repo` only, so run the script from the checkout that holds the sealed folders or pass `--repo`, because an output
  under another checkout's sealed folder is not refused by name."; **F-3**: "This S1 folder does not forbid itself, so only its committed `out/` is
  protected (by the absent-or-empty rule) and a second output set, or the text-bearing edit, could be written beside it inside the sealed tree."
- `build_s1_llama3.py` not changed (SHA-256 `a2b0a66c…` before and after, M); the S1 set's 17 tests pass (the committed-`out`-equals-a-fresh-build test
  among them), so the set is as round 3 left it.

### F-4 (minor): the untested guard branch and the gpu-only perturbations
- **New file** `scripts/scale78b/tests/test_noise_reading_guard_fields.py` (29 tests; imports the committed file's helpers, the committed file unchanged):
  - the synthetic fields are `GB.compared_fields` on the committed `SYNTHETIC_ENVIRONMENT` (14 keys, `cudnn` 8902, `gpu` A100, `policy`), every unit the same
    guard record `{repo, revision, files}`;
  - equal fields and guards → `[]` on all six; one unit's guard changed (parametrized over the five non-reference units) → `["guard"]` on that unit alone;
    the reference's guard changed → `["guard"]` on every other unit; a unit without a guard record is compared on its fields only (and a reference without
    one compares no guard at all: the module's rule, R: `noise_reading.py:246-248, 262`);
  - each of the 14 compared fields changed on one unit (parametrized) → `[field]` on that unit alone; `cudnn` changed on the reference → `["cudnn"]` on every
    other unit; `cudnn` and the guard together → `["cudnn", "guard"]`;
  - through the real reader (`needs_wave0a`): every unit read as if it carried the same guard record and one differed (a0@1102, R@1103, the reference) →
    the whole attribution dict, the trigger, `governing == "fallback"`, `guard_record` True on all six; a `cudnn` difference on R@1101 → `["cudnn"]` on it
    alone; equal guard records everywhere → nothing, plain governs.
- **Mutants** (M, `SCR/mutate_f4.py`, the verifier's harness form and its eleven mutants plus two more guard mutants, three test files, SCI;
  `SCR/mutate_f4_out.txt`): baseline 64 passed. **V6 (drops `cudnn`): KILLED**, 4 failed, all in the new file. **V8 (guard `==` for `!=`): KILLED**, 28 failed,
  10 distinct new tests, none elsewhere. V8b (guard branch removed): KILLED by 5 new tests. V8c (guard compared when one side has none): KILLED by the new
  "without a guard record" test and by 9 committed/RV2-2 tests (the Gate A reference has no guard; the real family then fails everywhere). V1, V2, V4, V5, V7,
  V9, V10, V11: KILLED as before (the new reader-level tests add kills). **V3 survives: equivalent** (the loop reads a0@1101 first; the verifier's finding).

## 3. Commands run (exit status; all foreground; from WS)
1. `git status --short; git diff --stat; git log --oneline -1` (read-only) → 0; six untracked paths, no tracked diff, HEAD 953f520. `date -u` → 18:14:37.
2. `shasum -a 256` of the S1 set's script, its `out/*.json`, the README, the check script and its test file → 0 (`SCR/hashes_before.txt`); `cp` of the check
   script and the README into SCR (the before copies).
3. `MAIN -B -m pytest -q -p no:cacheprovider --basetemp SCR/pt-f1-before scripts/scale78b/tests/test_s1_olmo2_7b_check.py -k "scratch_tmp or scratch_folder"`
   on the UNFIXED script → **2 failed, 1 passed** (the two survival tests fail at `scratch.is_dir()`; `SCR/pytest_f1_before_out.txt`).
4. `SCI -B -m pytest -q -p no:cacheprovider --basetemp SCR/pt-f4-sci -rs scripts/scale78b/tests/test_noise_reading_guard_fields.py` → 29 passed, exit 0.
5. `SCI -I -B SCR/mutate_f4.py WS SCR` → exit 0; baseline 64 passed; 12 of 13 mutants KILLED; survivor V3 only (`SCR/mutate_f4_out.txt`). The harness's
   copy and temp folders removed by itself.
6. `MAIN -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_s1_olmo2_7b_check.py` (fixed script) → **10 passed, exit 0** (`SCR/pytest_f1_after_out.txt`).
7. `MAIN -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-s1-llama3-20261105/tests` → **17 passed, exit 0** (`SCR/pytest_s1set_out.txt`).
8. `MAIN -I -B scripts/scale78b/s1_olmo2_7b_check.py --edit "/Users/spiderishi/Coding/attribution/tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-904a0cf1…-e1-a1/edit.json" --scratch-tmp SCR/olmo-check-tmp/scratch --out SCR/olmo-check-record.json`
   → exit 0 (run twice; the second with the exit status captured); record `9b340bf5…`; `cmp` with the verifier's record → equal; scratch gone afterwards
   (`SCR/olmo_check_cli_out.txt`). The edit is read by exact path through the engine's `parse_edit` (frozen code); nothing of that folder was listed or printed.
9. `SCI -B -m pytest -q -p no:cacheprovider test_fingerprint_compare.py test_noise_reading.py test_noise_reading_rv2_2.py test_noise_reading_guard_fields.py`
   → **74 passed, exit 0** (10 + 28 + 7 + 29; `SCR/pytest_fp_noise_sci_out.txt`; per-file counts by `--collect-only`, `SCR/collect_counts.txt`).
10. The same four files under MAIN → **72 passed, 2 skipped** (the two scipy tests of the committed file; MAIN has no scipy), exit 0 (`SCR/pytest_fp_noise_main_out.txt`).
11. `shasum -a 256` after → `SCR/hashes_after.txt`; `diff` before/after: only the three edited files differ, the new file added; `build_s1_llama3.py` and `out/*` equal.
12. `git status --short; git diff --stat` after → seven untracked paths (the new test file added), no tracked diff; `find . -name __pycache__ -not -path "./tmp/*"` → none.
13. `diff` of the before copies against the edited script and README → the changes in section 2 only.
14. `MAIN -I -B SCR/text_check.py WS SCR SCR/../fix-F.md` → exit 0: the 96 row texts (prompt and response of the 48 items, read through REQ-7's `read_list`
    by the pin) against the four edited/new files, this report, the three committed `out/` files and every SCR file → **0 hits each, total 0**
    (`SCR/text_check_out.txt`). A first version counted every string of the list document and reported 49 "hits" on the MANIFEST and the record: those
    were the 48 list ids and the pin hash, which are ids and hashes, not text; the check was narrowed to the text fields and re-run.
15. `date -u` → 18:15:02, 18:28:52, 18:29:37. `rm -rf SCR/pt-*` (pytest temp folders). No git command other than status/diff/log.

## 4. Acceptance criteria
| criterion | result | evidence |
|---|---|---|
| F-1 fixed with both tests | **passed** | section 2 F-1; the two survival tests fail before (item 3) and pass after (item 6); the created-folder test passes; 10 passed |
| the verdict record `9b340bf5…` unchanged | **passed** | item 8: `9b340bf504400576f116e394fa9dd669cff623c0a35e8bb34cdd1c2ee018d2ca`, `cmp` equal to the verifier's |
| F-2 and F-3 in the README (PP6) | **passed** | section 2; README diff (item 13); one sentence each |
| F-4's tests kill V6 and V8 | **passed** | item 5: V6 KILLED (4 new tests), V8 KILLED (10 new tests); V8b, V8c too; V3 equivalent survives |
| `build_s1_llama3.py` and the S1 set's `out/` unchanged (SHA-256 before and after) | **passed** | items 2, 11: `a2b0a66c…`, `a3986274…`, `1023b4e6…`, `36a39481…` equal |
| all tests pass | **passed** | items 6, 7, 9, 10: 10 + 17 + 74 (SCI) / 72 + 2 skipped (MAIN) |
| nothing prints text | **passed** | item 14: 0 hits on every file; every CLI line a hash, a count, a verdict or a path |

## 5. Jobs for the lead
1. The commit by explicit paths now includes the four files of section 1 (the fixed check script, its test file, the README, the new guard-field test file)
   with round 3's other paths (build-F.md section 6 item 1). `scripts/stage1/commitments.py check` after the commit, as before.
2. The lead's own re-run, if wanted: `MAIN -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_s1_olmo2_7b_check.py` (about 8 s, 10 tests) and
   `SCI -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_noise_reading_guard_fields.py` (3 s, 29 tests).
3. verify-F's observation (ii) stands untouched (a missing sealed builder file gives a traceback, exit 1, not `REFUSED`): not in this brief; a two-line
   change in `main` if the lead wants it.

## 6. Unresolved concerns
1. The `was_empty_dir` branch goes one step beyond the lead's wording of F-1 (it removes `scratch/list` from a pre-existing empty folder). It cannot
   touch anything that was there before (the folder was empty), and it is what the docstring promised; but it is untested by a dedicated test (the
   pre-existing-empty success case would be another full check run, about 8 s). If the lead prefers the rule word for word, drop the `elif` (two lines)
   and the recovered list stays in a pre-existing empty folder under `tmp/`.
2. The F-4 reader-level tests attach a synthetic guard record to the Gate A and wave-0a units in the record `read_unit` returns (the files are untouched),
   because no unit with a guard record is on this Mac outside the forbidden folders. The unit-level tests cover the same rule without data.
3. V8c (guard compared when one side has none) is killed mainly by the committed tests through the real family (the Gate A reference has no guard), not
   by a dedicated assertion; the new "without a guard record" test kills it too. No gap, noted for completeness.
