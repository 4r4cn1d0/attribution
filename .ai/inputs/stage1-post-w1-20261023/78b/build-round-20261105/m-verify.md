# Track M verify (round 4, 7-8B $0 build): adversarial check of m-fix.md

Started 2026-11-06 14:24 UTC; written 14:44 UTC (`date -u` before each time). Worker: self-identified Opus 5.5 (the
launcher's routing evidence governs). Status: DONE. Verdict: **VERIFIED_WITH_MINOR** (one minor RF-2 residue, two
minor test gaps, one doc nit; no blocker, no major).

- WS = `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-m` (HEAD d203070; read-only for me; only read, `git show`, `git diff`, `git status` used).
- SCR = `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/m-verify-scratch/`. All mutants ran in a copy SCR/ws (`rsync -a --exclude .git --exclude __pycache__ WS/ SCR/ws/`; no `.git`, so no git state can change there). Every mutant restored its files and re-checked their hashes; after each batch the copy's 48 scale78b files again equal the returned hashes (M).
- MAIN = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python` (3.11.15, transformers 4.56.2); SCI = `/Users/spiderishi/Coding/attribution/.venv/bin/python`. pytest always `-B -p no:cacheprovider --basetemp SCR/bt-*`, `PYTHONDONTWRITEBYTECODE=1`, MAIN runs with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.
- No pod, spend, network, install, download, agent or message. Tags: M measured, R read (path:line), E estimate, I inference.

## 1. Files changed

None in WS (M: `git status --short` = the fixer's 30 paths, all under scripts/scale78b; the 48 hashes unchanged after my run; no `__pycache__`).
My own files only: this report; SCR/tools/ (mut.py, mut_pins.py, check_settings_follow_pins.py), SCR/specs/ (one JSON per
mutant), SCR/probes/ (test_probe_rf.py, probe_l1_forward.py), SCR/out/ (every run's output), SCR/head/ (HEAD copies),
SCR/returned.sha.

## 2. Hashes and frozen files

- The 48 returned hashes equal the WS files, and the file set under scripts/scale78b is exactly those 48 (M: `shasum -a 256 -c SCR/returned.sha`, 0 mismatches; `diff` of the two lists, exit 0).
- Frozen or unchanged scripts equal `git show HEAD:` (M): `build_r_draws_78b.py` 18f2fec8…, `build_h1_llama3.py` 26f2f2a1…, `noise_reading.py` 94b679ff…, `make_recipe_s78.py`, `fingerprint_compare.py`, `g1_check_78b.py`. `git diff HEAD --stat` outside scripts/scale78b is empty (M), so scripts/stage1, the engine, runkit and `.ai/inputs/` are untouched.
- SCORERS-78B.md section 7's hashes (108f4425…, 7c8f2491…, 428b7577…, a2132c9d…) equal the files (M).

## 3. Test re-run (in SCR/ws)

- MAIN, `scripts/scale78b/tests`: **246 passed, 2 skipped** (scipy), exit 0, 20.3 s (M, SCR/pytest-main.log).
- SCI, the noise and G1 files: **74 passed**, exit 0 (M, SCR/pytest-sci.log). The `needs_wave0a` RF-4 test ran (no skips).
- `make_scorer_settings_78b.py --check`: "19 of 19 files equal their regeneration", exit 0 (M, SCR/maker-check.log).
- The new tests on HEAD's scripts (swapped into the copy, then restored): `s1_olmo2_7b_check.py` → 5 failed, 12 passed (the RF-1 f1 test and the four RF-2 cases); `scorers_78b.py` → 12 failed, 3 passed: the 10 RV-E-1 cases plus 2 older whole-command tests that fail only because HEAD's `PINS_FILE_SHA256` (8b9d…) no longer matches the regenerated index (I; SCR/out/head-*.txt). So each new test fails before the fix and passes after it (M).
- The S1 verdict record is unchanged: the CLI in the copy, `--edit` = the main checkout's stage-1 S1 edit by its exact path, `--out SCR/out/olmo-check-record.json` → exit 0, verdict "equal as it stands", `record 9b340bf504400576f116e394fa9dd669cff623c0a35e8bb34cdd1c2ee018d2ca`; `shasum` of the file gives the same; the default scratch folder was created and removed (M).

## 4. Hand mutants, one or more per item (killed = pytest exit 1)

| item | mutant (mine) | tests run | result |
|---|---|---|---|
| RF-1 | V1a: `created = not scratch.exists(); scratch.mkdir(..., exist_ok=True)` (non-atomic decision) | test_s1_olmo2_7b_check.py | SURVIVED (17 passed). Benign (I): the cleanup now only `rmdir`s the scratch folder (empty folders only) and `rmtree`s only `made`, so a wrong `created` can at most remove an empty folder another run then recreates with `mkdir(parents=True)`. The RF-1 property holds by the cleanup rule. |
| RF-1 (fixer's extension) | V1b: `(scratch / "list").mkdir(parents=True, exist_ok=True)` | same | **SURVIVED** (17 passed). Not benign: my probe P1 (another party creates `scratch/list/s1.json` while `recover_list` runs) **kills it**: under V1b the run appends the list to `made`, `write_new_files` refuses, and the cleanup removes the other party's list (M, SCR/out/V1b_…__probes.txt). On the fix P1 passes: exit 2, "list exists", the other party's file intact (M). Test gap D2. |
| RF-2 | V2: `scratch in out.parents` → `out.parent == scratch` (direct children only) | same | **SURVIVED** (17 passed). My probe P2 (`--out <scratch>/list/record.json`) **kills it**: under V2 exit 0, the `record …` line printed, the record gone after the cleanup (M, SCR/out/V2_…__probes.txt). On the fix P2 refuses, exit 2, nothing created (M). Test gap D3. |
| RF-2 | probe P3 on the FIX: `--out` = `<repo>/TMP/<…scratch…>/list/record.json` (`TMP` for `tmp`) | probes | **FAILS ON THE FIX**: exit 0, "lies under" not printed, the `record …` line printed, the record absent afterwards (M, SCR/out/probes-fix.txt). This Mac's APFS is case-insensitive, so the two spellings name one folder, and the guard compares path strings. Defect D1. |
| RF-3 | V3: the `made` folders removed only when `created` | same | KILLED by `test_rf3_a_pre_existing_empty_scratch_tmp_survives_empty…` (M). |
| RF-4 | V4: a malformed guard (not a dict) read as None instead of refused | test_noise_reading_guard_fields.py (SCI) | KILLED by `test_rf4_the_real_read_unit…` (M). |
| RF-4 | V4b: guard read from COMPLETE.json (`marker.get("guard")`) | same | KILLED by both RF-4 tests (M). Also re-ran the re-verifier's H5 (`guard = None`): KILLED, 2 failed (M). |
| RF-5 | V5: differing fields sorted by length (`key=len`) | same | KILLED by the three RF-5 cases (M). |
| RF-5 | V5b: "guard" listed first | same | KILLED, 4 failed (M). Re-ran the re-verifier's H2 (list in set order) under PYTHONHASHSEED 0, 1, 2: KILLED each time, 3 failed (M). |
| RV-E-1 | V6: refuse only names that are a prefix of an allowed flag (or a bare `--`); other unknown flags pass | test_untuned_two_calls_78b.py (MAIN) | KILLED: the `--set` case and the every-kind test (M). |
| RV-E-1 | V6b: a bare `--` allowed | same | KILLED by the bare-`--` case (M). |
| RV-E-2 | V7: section 6 item 7 renumbered back to 4 | all scripts/scale78b/tests | SURVIVED (246 passed), as expected: no test guards document numbering. Checked by reading: items run 1-10 (R: SCORERS-78B.md:143-184). |
| RV-E-3 | V8 (consistent): pins cite back to `589-591`, the 19 files regenerated, `PINS_FILE_SHA256` reset | tests/scorers (MAIN) | KILLED by the two `…engine_cite_is_590_592` cases; the maker's `--check` passed on the mutant, so only the value test caught it (M). Lines 590-592 are `identity = …`, the `if`, the `raise` (R: scripts/stage1/s1common.py:590-592). |
| PP11 | V9 (consistent): `l1_first_block` = 9, regenerated | tests/scorers | KILLED, 5 failed (the ruled-value test, `choose_layer` ×2, `test_the_per_family_values` ×2) (M). |
| PP12 | V10 (consistent): Llama modules `["mlp"]` only, regenerated | tests/scorers | KILLED, 2 failed (M). |
| PP12 | V10b (consistent): OLMo modules in swapped order, regenerated | tests/scorers | KILLED, 2 failed (M). |

Extra check (not a mutant): the unchanged 1B `Scaled` hook on each family's 7-8B settings, on tiny random 32-block
Olmo2 and Llama models (CPU), at blocks 10 and 31: scaling by 1.2 changes the logits, factor 1.0 leaves them equal, and
the hooks are removed afterwards, for both families (M: `SCR/probes/probe_l1_forward.py`, exit 0). The fixer's tests
check the module lookup only; this shows the hooked forward pass also works for Llama's tuple-returning `self_attn`.

## 5. The settings follow pins_78b.json

`SCR/tools/check_settings_follow_pins.py WS` (SCI, exit 0; SCR/out/settings-follow-pins.txt), independent of the
maker: **no problems**. Checked: `PINS_FILE_SHA256` = sha256(PINS-78B.json); the index's `pins_78b_sha256` = sha256 of
pins_78b.json; the index lists exactly the 18 files with their hashes; in every file `family_78b.family` and
`engine_rule` (= `shared.engine_rule_78b`, with `:590-592`); `kind_names` present only in representation_pass and
write_score_edit and equal to `kind_names_78b`; `classifier_recipe` only in score_classifier and equal to
`classifier_recipe_78b`; l1 `scan.first_block` = 10, `scan.modules` = the family's own entry, the two rule texts; the
l1 waits = the anchor bank only; l1 and s3 pin the regenerated rep_pass file's hash. The field-level diff against HEAD
matches the fixer's list: `engine_rule` in all 18; plus `kind_names` (rep_pass, score_edit), `classifier_recipe`
(classifier), `pins.representation_pass_settings_sha256` (l1, s3), and in l1 `scan.first_block`, the rule texts, the
other family's `scan.modules` key removed, `waits.scan.first_block` removed (M). No code reads the removed pins keys
`l1_first_block_waits`, `l1_modules_note`, `modules_note_78b` (M: grep).

## 6. Defects

| id | severity | where | what | fix |
|---|---|---|---|---|
| D1 | minor | `scripts/scale78b/s1_olmo2_7b_check.py` main, the RF-2 guard (`if out == scratch or scratch in out.parents`) | The guard compares resolved path strings. On this Mac's case-insensitive APFS, `--out` that spells `tmp` as `TMP` names the same folder and passes the guard. With `--out <scratch>/list/record.json` so spelled, the CLI exits 0, prints `record <hash>`, and the cleanup then removes the record with `scratch/list` (M, probe P3). The same would hold for any other alias that `resolve()` does not fold (for example a macOS firmlink path such as /System/Volumes/Data/Users/…; I, not measured). Input is contrived; only the record is lost, nothing pre-existing. | Make the record outlive the cleanup by construction: keep `data` in memory and write `--out` after the `finally` cleanup (the re-verifier's second option), keeping the string guard as an early message. Or compare by identity: after the scratch mkdir, refuse when any existing ancestor of `--out` is `os.path.samefile` to scratch. Add P3 (and P2) as tests. |
| D2 | minor (test gap) | `tests/test_s1_olmo2_7b_check.py` against `check()`'s list mkdir (the fixer's extension of RF-1) | Mutant V1b (`exist_ok=True` on the list mkdir) survives all 17 tests; it loses another party's list made during `recover_list` (M, P1). | Add P1 as a test (SCR/probes/test_probe_rf.py `test_p1_…`, about 1 s): monkeypatch `load_sealed_builder` so `recover_list` creates `scratch/list/s1.json`; expect exit 2 and the file intact. |
| D3 | minor (test gap) | `test_rf2_out_under_the_scratch_folder_is_refused_before_anything_is_created` | Only `<scratch>/record.json` and `<scratch>` are tested. Mutant V2 (direct children only) survives and loses `--out <scratch>/list/record.json` (M, P2). | Add a `nested` case (`<scratch>/list/record.json`) to the parametrize. |
| D4 | nit (doc) | `settings/pins_78b.json` `shared.classifier_recipe_78b` (copied into both `score_classifier__F.json`), SCORERS-78B.md section 6 item 3 | The text was updated "to the current kit state" but still cites `check_keys, R: :325-337`; at d203070 `check_keys` is at `rules_78b.py:569-584` (its S_78 branch :577-579); :325-337 was 953f520's (M: `git show 953f520:…` and `sed`). | Write `:569-584 at HEAD d203070` (or tag `:325-337` with "at HEAD 953f520"). It changes the pins text, so the 19 files and `PINS_FILE_SHA256` regenerate. |

## 7. Acceptance criteria

| criterion | result | evidence |
|---|---|---|
| RF-1: "created" decided atomically, with a test | passed | the atomic mkdir is in place (R s1_olmo2_7b_check.py:225-229); f1 fails on HEAD and passes on the fix (M). V1a survives but is benign (the rmdir-only cleanup). The fixer's list-folder extension is correct (P1 passes) but untested (D2). |
| RF-2: `--out` under `--scratch-tmp` refused | passed with a minor residue | plain spellings refused (4 cases; P2 nested refused); a case-variant alias bypasses it and loses the record (D1); the nested case is untested (D3) |
| RF-3: a pre-existing empty `--scratch-tmp` survives, empty | passed | V3 killed (M) |
| The verdict record 9b340bf5… unchanged | passed | M, section 3 |
| RF-4: the guard record read through the real read_unit | passed | V4, V4b, H5 killed (M) |
| RF-5: two fields on one unit, sorted | passed | V5, V5b killed; H2 killed under 3 seeds (M) |
| RV-E-1: abbreviations refused | passed | V6, V6b killed; the 10 new cases fail on HEAD (M). Probed: no 1B parser defines a short option other than -h (R: the `add_argument` lines); the wrapper's own parser has `allow_abbrev=False` (R scorers_78b.py:513). |
| RV-E-2: section 6 renumbered | passed | R: items 1-10; V7 survives (no doc test; expected) |
| RV-E-3: cite 590-592 | passed | V8 killed; R s1common.py:590-592 |
| PP11 filled (10), files regenerated | passed | V9 killed; section 5 |
| PP12 filled (per family), files regenerated | passed | V10, V10b killed; section 5; hooked forward pass works on both families (M) |
| The settings follow pins_78b.json | passed | section 5 |
| All tests pass | passed | 246 + 2 skipped (MAIN); 74 (SCI); maker `--check` 19/19 |
| The frozen scripts unchanged | passed | section 2 |
| The returned hashes equal the files | passed | 48 of 48 (M) |
| n = 32 blocks for both real models | not tested | no cached config.json for either model on this Mac (M: `find` in the HF cache); PP11 states it (R); the tests build 32-block tiny models, so their `layout()` check is by construction (I) |

## 8. Commands (all foreground, each under 1 min; exit status)

1. `date -u`; `ls` of the reports and WS (0). `git status --short`, `git log --oneline -1`, `du -sh` in WS (0).
2. `cat`/`grep`/`sed` reads of m-fix.md, the PP rulings, reverify-F.md and reverify-E.md (RF and RV-E rows), the diffs (`git diff HEAD -- <file>`) of the S1 check, the guard tests, scorers_78b.py, the two-calls tests, pins_78b.json, the maker, the two updated scorer tests; the new test_l1_pins_78b.py; the 1B parsers' `add_argument` lines; score_l1_larf.py:54-92; s1common.py:588-593, 605-618; rules_78b.py:139-142, 569-600; `git show 953f520:runkit/stage1-78b/rules_78b.py` (0; one `grep --include=*.py` failed in zsh with "no matches found", 1, re-run without the glob, 0).
3. `shasum -a 256 -c SCR/returned.sha` in WS (0 mismatches); the file-list `diff` (0); `git show HEAD:<6 files> | shasum` (0); `git diff HEAD --stat -- . ':!scripts/scale78b'` (0, empty).
4. `rsync -a --exclude .git --exclude __pycache__ WS/ SCR/ws/` (0).
5. MAIN pytest scripts/scale78b/tests (0); SCI pytest the four noise/G1 files (0); MAIN maker `--check` (0).
6. `SCI -I -B SCR/tools/mut.py SCR/specs/<V>.json` for V1a, V1b, V2, V3 (0 each; verdicts in section 4); the probes on the fix (pytest exit 1: P3 fails, P1 and P2 pass; run twice, the second to capture the printed lines); the probes against V1b, V2, V1a (0 each).
7. mut.py for V4, V4b, V5 (first form a SyntaxError, INVALID exit 2; corrected and re-run, KILLED), V5b, H5, H2 × 3 seeds (0 each).
8. mut.py for V6, V6b (0); `grep` of the wrapper's main and run_main (0).
9. `SCI -I -B SCR/tools/mut_pins.py` for V8, V9, V10, V10b (0 each; the maker regenerated in the copy, exit 0; `--check` on each mutant exit 0).
10. `MAIN -I -B SCR/probes/probe_l1_forward.py SCR/ws` (0). `find ~/.cache/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct -name config.json` (0, none found).
11. `SCI -I -B SCR/tools/check_settings_follow_pins.py WS` (0).
12. mut.py for V7 over the whole folder (0, SURVIVED).
13. HEAD swaps: `git show HEAD:` of the two scripts into SCR/head, copied into SCR/ws, MAIN pytest the two new test files (1 each, expected), restored (hashes 0 mismatches).
14. The S1 CLI in the copy with `--out SCR/out/olmo-check-record.json` (0); `shasum` (0).
15. Final `git status --short | wc -l` in WS (30 paths, all under scripts/scale78b), `shasum -c` (0 mismatches), `ls WS/tmp` (kt-prepared only), `find scripts -name __pycache__` (none).
16. Cleanup: `rm -rf SCR/ws SCR/bt-*` (the 146 MB copy and pytest temp folders; specs, probes, tools and outputs kept).

## 9. Jobs for the lead

1. Decide D1-D3 before the merge or record them as limits. D1 is one move in `main` (write `--out` after the cleanup) plus P3 as a test; D2 and D3 are one test each (ready in `SCR/probes/test_probe_rf.py`; they import `SCR/ws`, so a fixer moves them into `tests/test_s1_olmo2_7b_check.py` with its own `ROOT`). The record hash stays 9b340bf5… (the record holds no script hash; R: the check's result dict).
2. D4 is a pins text change; if taken, regenerate (`MAIN -I -B scripts/scale78b/make_scorer_settings_78b.py`), set the new `PINS_FILE_SHA256`, and re-run `--check`.
3. To re-run my probes: `rsync -a --exclude .git --exclude __pycache__ WS/ SCR/ws/`, then from SCR/ws `PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MAIN -B -m pytest -q -p no:cacheprovider -s --rootdir SCR/probes --basetemp SCR/bt-probe SCR/probes/test_probe_rf.py` (about 4 s; today: P1 pass, P2 pass, P3 fail).
4. Otherwise the fixer's merge list and hashes stand (48 of 48 equal, M).

## 10. Unresolved concerns

1. The S1 tests and my probes P1-P3 and the CLI run read stage 1's S1 edit, which lives under the main checkout's `tmp/stage1-olmo/` (R: build_s1_llama3.py:88), a folder on my never-open list. I never listed or opened that folder: the committed check code reads the one file by its exact path, refuses unless it hashes to the pin, and drops the text in the engine's parse_edit; only exit codes, booleans and hashes were printed. This is how the fixer and the earlier S1 rounds ran it, and the task asked for the folder's tests to be re-run. The lead should confirm this reading of the exception.
2. V1a shows the atomic `created` decision is not observable by any test; the safety comes from the rmdir-only cleanup and `made`. That is sound (I), but a later change back to `rmtree(scratch)` would bring RF-1 back, and only the f1 test would catch it (the fixer's m3 shows it does).
3. CUDA, the real 7-8B models and their block count are untested here (tiny random CPU models only).
4. PP12's one-entry-per-family choice and the classifier text rewording are the fixer's flagged choices; I found nothing against them. The 1B `modules_note` copied into each l1 file still describes both entries; the new `modules_rule_78b` beside it explains (R; not a defect).
