# Verify E: the per-family scorer layer for the 7-8B tier (adversarial verifier)

Started 2026-11-05 17:27 UTC; last check 17:51 UTC (M: `date -u` before each time written here).
Builder's worktree (read-only for me): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-e` at HEAD 953f520 (M: `git rev-parse HEAD`, equal to the main checkout's HEAD).
Builder's report: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/build-E.md`.
My scratch: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/verify-E-scratch/` (mutant harness, logs; no builder file edited; no git state changed anywhere; no forbidden folder opened; no text printed or stored).

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.

## 0. Verdict: DEFECTS (one major design defect in the map's fallback path; the code and pins otherwise verified)

The wrapper, the maker, the 18 settings files and the tests do what the builder says: every hash and pin checks against its source, the suite passes (88, none skipped), the maker `--check` passes, no 1B file changed, 14 of 17 hand mutants are killed. But the map's single untuned-answers command line (s3 and s4 lists in one call) loses the S3 pipeline's `s3_orig.pool.json` whenever the S4 dose fallback fires, because the unchanged 1B code at exit 3 keeps only `answers_*.json` and the record (M, section 3 D1). Part 1 section 10 pre-sets that fallback as a valid outcome, so the map must not let it destroy another arm's input. Two further findings are documentation gaps with pod cost (engine pin; the classifier's recipe against `rules_78b.py check_keys`).

## 1. Files added by me

- This report.
- `verify-E-scratch/x_fallback_drops_s3_orig.py` and its output `x3-fallback-out.txt` (the decisive check for D1; counts and file names only).
- `verify-E-scratch/mutants.py`, `mutants-results.jsonl` (17 mutants), `mutroot/` (a symlink root over the builder's worktree with real copies of `scripts/scale78b` and `scripts/stage1`, so mutants never touch the worktree), `pristine-scale78b/` (the unmutated copy), `pytest-scorers-verifier.log`, `x3-24ecqteo/` (the check's fixture files). All deletable after the lead reads this.

## 2. What I checked and how

| Check | Result | Evidence |
|---|---|---|
| The suite in the builder's worktree | 88 passed in 21.8 s, 0 skipped (`-rs` shows none) | M: `cd ws-e; PYTHONDONTWRITEBYTECODE=1 <main venv python> -B -m pytest -q -p no:cacheprovider -rs scripts/scale78b/tests/scorers` (exit 0); `verify-E-scratch/pytest-scorers-verifier.log` |
| The maker's `--check` | "19 of 19 files equal their regeneration", exit 0 | M: `python -I -B scripts/scale78b/make_scorer_settings_78b.py --check` |
| No 1B file changed; no bytecode written | `git status --short` lists only the 5 new paths; `git diff --quiet HEAD` exit 0; `git diff --quiet HEAD -- scripts/stage1 runkit experiments .ai` exit 0; no `__pycache__` under `ws-e/scripts` | M |
| `STAGE1_CODE` (9 scripts) and `BASE_SHA256` (9 settings) | each equals `shasum -a 256` of the file at HEAD 953f520 in the main checkout and in the worktree; the 5 the stage-1 kit pins equal `runkit/stage1-olmo/stage1_rules.py:587-595` | M, R |
| New files' hashes | `scorers_78b.py` 2d4b7fac…, `make_scorer_settings_78b.py` 6d37770a…, `pins_78b.json` cd3c0850…, `PINS-78B.json` cba2f0b2…: as the builder reports | M: `shasum -a 256` |
| Per-family pins against sources | manifests 9ed61826… / c52a50af… = `rules_78b.py` MANIFESTS (R:103-104) and the `tmp/kt-prepared/*/manifest.json` copies (M); main recipes 18cc31d7… / 74758af1… and model repo_id and revision = `config_sha256(load_recipe(...))` and the configs' `model` sections (M, main venv); token limits 3072 / 1536 equal in both (M); sealed lists s1 389c20ad…, s3_safe 6801652c…, s4_candidates 798613c4…, record bcca59ac…, s3_safe items 861 = `.ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json` (M, hashes and counts only); anchor list 78467c97… = `scripts/make_anchor_answers.py:30` (R); engine X 472fc7f6… = `rules_78b.py:98` (R) | pass |
| The map against the 1B kit's `job_commands` | rep_pass: two passes (`--recipe RECIPE_S`, s3_safe pool, then `--pools-only` on J6's `s3_orig.pool.json`) R: `job_runner_stage1.py:430-441`; untuned_answers `--recipe REC --recipe-s RECIPE_S` with J6_LISTS (s3, s4, sd600, s1, s3_safe) R: `:442-446, :165`; l1_scan `scan --recipe REC` R: `:447-449`; classifier `--recipe RECIPE_S` R: `:450-456`; a1_rescore = `make-job attributes` R: `:49-53`. The map matches, with two stated deviations: `--recipe-s` = the main recipe (section 3 C1) and no pools for the classifier | pass, see C1, D3 |
| The 1B code's behaviour the map relies on | `recipes()` requires REC and S to agree on four model fields and reads S only for `max_train_tokens` (R: `make_untuned_answers.py:84-93, :250`); `answer_list` stops at `len(kept) == keep_target` and labels later keeps `kept_after_the_48th` (R: `:157-178`); at exit 3 only `answers_*` files and the record survive (R: `:317-318, :340`) | see D1 |
| Null pins and refusals | representation_pass: anchor, recipe; score_l1_larf: anchor and first_block (needed_by scan only); score_classifier: anchor, recipe; write_score_edit: the six a1 pins (needed_by a1 only); make_untuned_answers: none under `untuned_recipe_s = main`; write_add_edit: `lists.s4_top.rows` (needed_by []); each refusal names its event | M: the suite's `test_the_null_pins_refuse_by_naming_their_event`, `test_the_command_line_refuses_a_pod_kind_whose_pin_is_null`; the builder's CLI transcript; my print of the files |
| Family refusals | the preflight accepts the family's manifest and refuses the other's by both hashes (3 kinds x 2 families + score_edit); the whole command line on the real copies: exit 0 then exit 2 for the other family, nothing written | M: the suite (not skipped: the copies are under `ws-e/tmp/kt-prepared/`, manifest and engine files only, 11 MB, git-ignored) |
| Parity tests: bytes or shapes? | bytes. `assert_same_files` compares each written file's bytes with the API call's bytes; for `.json` files that differ it strips `costs` blocks and `*seconds` keys and compares the rest (the 1B determinism tests' rule); `.jsonl` must be byte-equal (a differing one fails `json.loads`). The two sides are the same 1B code in one process (`main()` through the wrapper against `run()`/`build()` direct), so this is parity of the plumbing, as the builder states; no any-model copy exists to compare | R: `test_scorers_78b_parity.py:57-74` |
| Untuned-answers parity reach | through `main()` only on the all-capped tiny model (kept 0, exit 3 both routes); the keep path is the 1B API with `FakeGenerator`; `run_kind -> build_doses` is never run end to end (the family settings need the 7B recipes); `build_doses` is unit-tested on a synthetic s4-only output | R: `test_scorers_78b_parity.py:95-132`, `test_s4_doses_78b.py:64-90`; see D1 |
| S4 rule against Part 1 section 10 and ruling 12 | nested prefixes of the kept order (48, 96, 192); the stop rule moves by `keep` = 192 (the 1B code's `keep_target`); the first 48 unchanged (the 1B test's form); fallback = all kept rows as `s4_top`, counted; below 48: exit 3; sizing ceil(192 x 64 / 57) = 216 and 7 chunks ("about 216", Part 1 §10) | M: the suite; R: Part 1 §10 (:306-324), ruling 12 (:179-212) |
| Nothing prints text | the builder's CLI outputs hold no `prompt`, `response`, `answer` or `text` key (M: a key scan of every JSON under `build-E-scratch/cli/`); the tests scan outputs for the fixtures' texts; my check printed counts and names only | pass; the dose lists carry prompt and untuned answer by design (the 1B `s4.json` form, under the job's `--out`) |
| Documentation citations | `make_anchor_answers.py:107-110` (query_bank "ref"), `:117-121` (encode stop), `stage1_rules.py:87`, `:679`, `job_runner_stage1.py:24-30`, `s1common.py:574-591`, `make_recipe_s78.py:5-10`, P78:355-358, :377 | R: each holds |

## 3. Findings

### D1 (major). The map's untuned-answers command line loses `s3_orig.pool.json` (and `s4.json`) when the dose fallback fires.

- SCORERS-78B.md section 2 gives one call: `untuned_answers … --list s4=… --list s3=… --loss s1=… --loss s3_safe=…`, and section 3 says the fallback (fewer than 192 kept after 512 prompts) makes "the 1B code write the answers and the record only and exit 3", which the wrapper turns into `dose_s4_top.json` and exit 0.
- The unchanged 1B code at exit 3 drops every output file but `answers_*.json` and the record (R: `scripts/stage1/make_untuned_answers.py:317-318`, `:340`), so the s3 list's `s3_orig.pool.json` is not written, while the record still names `lists.s3.s3_orig_pool_sha256` (R: `:282-285`).
- M (the decisive check, `verify-E-scratch/x_fallback_drops_s3_orig.py`, the 1B fixtures and `FakeGenerator`, lists s3 (10) and s4 (40)): keep 30 unreached -> exit 3, files `['answers_s3.json', 'answers_s4.json', 'untuned_answers_record.json']`, record names `s3_orig_pool_sha256`: True, `s3_orig.pool.json` written: False, `s4.json` written: False; control keep 6 -> exit 0 with both files written (`x3-fallback-out.txt`).
- Consequence: the rep_pass s3_orig pass reads `job-k/untuned/s3_orig.pool.json` (R: `job_runner_stage1.py:326-341`), and the J6 completeness check requires the pool among the job's outputs (R: `stage1_rules.py:675-685`); the S3 arm's input for that family is lost on a pre-set valid outcome (Part 1 §10 "Pre-set fallback"), and the wrapper reports exit 0 with `fallback_fired` true. The builder's fallback tests use an s4-only synthetic output, so this never surfaced.
- Fix (either): (a) the map's command line becomes two invocations on the pod, `--list s3 --loss s1 --loss s3_safe` (never exit 3: the s3 kind keeps every answer) and `--list s4` alone (the doses block applies only there); or (b) the wrapper refuses, after the 1B main, when the record names an s3 list and `s3_orig.pool.json` is absent, and the map says the s3 list runs in its own call. (a) is one line in SCORERS-78B.md section 2 and one `--list` fewer per call; the wrapper's `build_doses` already tolerates a missing `s4.json`.

### D2 (major, documentation and pod cost). Every derived settings file binds its kind to engine X; the map does not say so.

- The maker copies `engine_x` 472fc7f6… from the 1B files (M: `test_the_1b_check_settings_accepts_each_file_on_its_1b_name` asserts equality) and the frozen `check_settings` refuses any other engine identity (R: `s1common.py:589-591`). So every wrapper kind (rep_pass, l1_scan, classifier, untuned_answers on the pod; l1_score, s3_score, score_edit, add_edit, s_pool on the Mac) runs on engine X only.
- Addendum A13 lets E-capped kinds run on engine Y once `ENGINE_Y` is filled; the scorer kinds are E-capped (`rules_78b.py:215`). A scorer pod packed with engine Y would refuse at `load_settings` after the 48 min bootstrap; the Mac kinds refuse once the Mac checkout's engine identity is not X (engine round Y in main). SCORERS-78B.md section 2 says of A1's pass "engine X, or Y after the certificate" and never states the X-only rule for the wrapper kinds or for `write_score_edit a1` on the Mac.
- Fix: one line in SCORERS-78B.md sections 2 and 6 and in `pins_78b.json shared` ("every wrapper kind: engine X; a Y run needs re-derived settings with `engine_x` = Y's identity, a new PINS set"), and the kit round packs scorer pods with engine X.

### D3 (minor as written, major for the kit round). The classifier runs under S_78 per the map, but `rules_78b.py check_keys` refuses an E kind off the allow-list unless it is in `S78_KINDS`.

- The map (and the 1B kit, R: `job_runner_stage1.py:454`) runs the classifier with `--recipe S_78`. `rules_78b.py` S78_KINDS = {retrain, rep_pass} (R: `:136`); every other E kind must use a recipe on the family's allow-list, main or G (R: `:333-337`). So a classifier job recorded with S_78 refuses at the key check; REQ-3's representation pass passes only through the name collision the builder flagged (concern 1). The map flags the rep_pass naming but not the classifier's recipe. Fix: the kit round adds `classifier` (and REQ-3's pass under whatever name it gets) to `S78_KINDS`, or records the classifier job's key recipe as main while the command line passes S_78; SCORERS-78B.md section 6 should name it.

### C1 (confirmed, not a defect). `--recipe-s` = the main recipe for the untuned pass and the add-edit writer.

- `recipes()` reads S for `model.max_train_tokens` only and requires the four model fields equal (R: `make_untuned_answers.py:84-93, :250`); `write_add_edit.build` reads the recipe for `max_train_tokens` and records its hash (R: `write_add_edit.py:137-140, :160`). S_78 keeps the main config's model section (R: `make_recipe_s78.py:5-14`). The values are identical; what changes is the recorded `provenance.inputs.recipe_s` / `inputs.recipe` hash (main's instead of S_78's). No frozen 1B consumer checks that field against recipe S (M: grep of `score_s3_datarx.py`, `write_add_edit.py`, `stage1_rules.py`), so the choice is safe; it is a record difference the lead should accept in Part 2's scorer section (the builder states it as reversible by one key).

### C2 (confirmed). The `rep_pass` name collision.

- `stage1_rules.py:87` and `job_runner_stage1.py:24-30`: rep_pass = REQ-3's representation pass. `rules_78b.py:136, :633-636` and `RULES-78B.md:88, :109`: rep_pass = A1's attributes pass at a 16.5 h cap. Two pods, two caps, one name. The builder's concern 1 is right; the kit round must carry two kinds.

### C3 (observation for the kit round, I). The E upper for `untuned_answers` counts 512 prompts in 16 chunks only (R: `rules_78b.py:609-614`); the J6 command also answers the s3 list (861 prompts, 27 chunks at `max_new_tokens` 512) and computes the loss table. If D1's fix (a) splits the lists into two calls on one pod, the pod's cap must cover both calls.

### C4 (minor). Misleading refusal text after the 1B main has written.

- `run_kind` runs the 1B `main()` (which writes `--out`) and then `build_doses`; a refusal there (no s4 list in the record, an answers mismatch) reaches `main()`'s handler, which prints "REFUSED: … (nothing written)" although the 1B outputs exist (R: `scorers_78b.py:411-416, :444-446`). Cosmetic; fix the message or move the doses refusal to its own text.

### C5 (minor, test gaps shown by survivors). See section 6: `flag_value`'s last-occurrence rule and the wrapper record's `exit_code` are untested.

## 4. Commands run (cwd = the builder's worktree unless stated; main venv = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python`; `PYTHONDONTWRITEBYTECODE=1` set for every Python run)

| # | Command | Exit |
|---|---|---|
| 1 | `date -u` (17:27, 17:34, 17:39, 17:41, 17:42, 17:45, 17:48, 17:51 UTC); `mkdir -p verify-E-scratch` | 0 |
| 2 | reads (`sed -n`, `grep -n`, Read) of build-E.md, SCORERS-78B.md, the 7 new code and test files, the 18 settings files' key fields (`.venv` python `-I -B`), Part 1 §2, §3.7, §10, §12, §14, rulings 12, addendum A1-A3, A13, readiness T6 and check C1, C6, M1-M5, P78:330-377, the 1B scripts' cited regions, `job_runner_stage1.py`, `stage1_rules.py`, `rules_78b.py`, `RULES-78B.md`, the D-2 wrapper | 0 |
| 3 | `git status --short; git rev-parse HEAD; git diff --quiet HEAD; git diff --quiet HEAD -- scripts/stage1 runkit experiments .ai` (worktree) | 0, 0, 0, 0 |
| 4 | `shasum -a 256` of the 9 scripts and 9 settings in the main checkout and the worktree; of the 4 new files; of the two prepared copies' manifests | 0 (all equal the pins) |
| 5 | main venv `-I -B -c` printing `config_sha256(load_recipe(...))` and the model fields of the two main recipes | 0 |
| 6 | `.venv` python `-I -B -c` printing the S-pool record's SHA-256, its 64-hex fields and counts; the anchor prompt record's keys | 0 |
| 7 | `python -B -m pytest -q -p no:cacheprovider -rs scripts/scale78b/tests/scorers` (worktree) | 0: 88 passed, 0 skipped, 21.8 s |
| 8 | `python -I -B scripts/scale78b/make_scorer_settings_78b.py --check` | 0: 19 of 19 equal |
| 9 | `python -B verify-E-scratch/x_fallback_drops_s3_orig.py` (cwd worktree) | 0: the D1 evidence |
| 10 | the mutant root: symlinks to every worktree entry, real copies of `scripts/scale78b` and `scripts/stage1`; `python -B mutants.py baseline` twice (first with `scripts/stage1` as a symlink: 2 failed, a harness artifact, `s1.rel` saw two roots; then with the copy: 88 passed) | 1, then 0 |
| 11 | `python -B mutants.py m01 … m06`, `m07 … m12`, `m13 … m17` (3 batches, 24 s each mutant) | each batch 0; results in `mutants-results.jsonl` |
| 12 | `diff -r pristine-scale78b mutroot/scripts/scale78b` after the runs | 0 (restored) |
| 13 | `find ws-e/scripts -name __pycache__`; a key scan of the builder's CLI JSON outputs for text keys | 0: none; none |

Longest command: 2 min 20 s (a mutant batch). No job for the lead is needed to reproduce anything here.

## 5. Acceptance criteria (the builder's list, my reading)

| Criterion | My result | Basis |
|---|---|---|
| the map: kind -> 1B script, settings, inputs, per-family differences, waits | failed on one row | the untuned_answers row's single command line (D1); the classifier row lacks the `check_keys` note (D3); the engine-X constraint is absent (D2); every other row checks against the 1B kit's `job_commands` and the 1B scripts (section 2) |
| per-family settings in the 1B schema, every null documented; thin wrappers only | passed | 18 files accepted by the frozen `check_settings` (M, the suite); every null in `waits` with its event (M); one wrapper, no scoring code copied (R) |
| parity: byte for byte on 1B-shaped inputs (CPU) | passed, with the stated reach | bytes compared (section 2), both sides the same 1B code; the keep path through `main()` and `run_kind -> build_doses` end to end untested |
| the scripts accept the family's manifest and refuse the other family's | passed | M: the suite on the real copies; the builder's CLI transcript |
| the 1B files byte-identical | passed | M: hashes, `git diff --quiet HEAD` |
| no text printed or stored | passed | M: key scan of outputs; the tests' text scans; the dose lists hold text by design under `--out` |
| the S4 sizing and nesting rule on a synthetic list | passed for the wrapper's function; the plan's fallback is defective | M: the suite; D1 |
| CUDA paths | not tested | as the builder says |
| the anchor job, S_78, the retrain, A1's pass, the pod runs | not tested | pod jobs |

## 6. Mutants (17 hand mutants; harness `verify-E-scratch/mutants.py`; each on a fresh copy; the whole scorer suite; results `mutants-results.jsonl`)

| Mutant | What it changes | Verdict | Killed by |
|---|---|---|---|
| m01 | `check_manifest` never refuses | KILLED (10 failed) | the preflight family tests, the CLI refusal |
| m02 | nested doses are suffixes, not prefixes | KILLED (9) | the dose tests (nesting) |
| m03 | the fallback fires at exactly 192 kept | KILLED (2) | `test_exactly_192_kept_is_not_a_fallback`, the three-lists test |
| m04 | sizing uses floor | KILLED (2) | 216 -> 215 |
| m05 | `null_pins` honours only `*`, not the command | KILLED (3) | the null-pin refusals (scan, a1) |
| m06 | `Patched` does not restore the globals | KILLED (3) | the restore test, rep_pass and classifier parity |
| m07 | the preflight skips the recipe hash | KILLED (2) | the recipe refusals |
| m08 | `with_subcommand` does not prepend `scan` | KILLED (1) | the CLI null-pin test (`l1_scan` without `scan`) |
| m09 | `flag_value` takes the first occurrence, not the last | SURVIVED | no test gives a flag twice; argparse in the 1B scripts takes the last, so a repeated `--prepared` would let the preflight check one set and the 1B script read another (I; a test gap, not reachable from the kit's fixed command lines) |
| m10 | the wrapper record's `exit_code` is always 0 | SURVIVED | no test asserts `exit_code`; the 7-8B runner is meant to read it (builder's concern 3), so a test should |
| m11 | `build_doses` skips the answers-file hash | KILLED (1) | the mismatch test |
| m12 | the maker writes `keep` 48 | KILLED (2) | the regeneration and `--check` tests |
| m13 | a hand edit of `representation_pass__olmo2-7b.json` (Llama's manifest) with the index and the literal re-pinned by hand | KILLED (3) | the regeneration test, the per-family values, the two-families-differ test |
| m14 | the two manifests swapped in `pins_78b.json`, all files regenerated by the maker, literal re-pinned | KILLED (12) | only the tests against the real prepared copies and manifests: `test_the_prepared_copies_are_the_pinned_manifests`, the preflight and CLI family tests (the pins are anchored to sources, not only to themselves) |
| m15 | `check_stage1_code` never refuses | KILLED (1) | `test_a_changed_1b_script_or_index_refuses` |
| m16 | `run_main` does not append `--pool-pins` for rep_pass | SURVIVED | equivalent: `representation_pass.main`'s `--pool-pins` default reads the patched `POOL_PINS_PATH` at call time (R: `representation_pass.py:425`); the flag is redundant, harmless |
| m17 | `build_doses` skips the `s4.json` ids check | KILLED (1) | the mismatch test |

14 killed, 2 test gaps (m09, m10), 1 equivalent (m16). The settings mutants (m12-m14) show the derivation test guards hand edits of the committed files, and the family tests guard the pins against the real sources.

## 7. Jobs for the lead

1. **D1 (before the kit round fixes its command lines):** decide fix (a) (two untuned-answers calls per pod: `--list s3 --loss s1 --loss s3_safe`, then `--list s4`) or (b) (the wrapper refuses when the record names an s3 list and `s3_orig.pool.json` is missing); have the builder edit SCORERS-78B.md section 2 and 3, and add a test with an s3 and an s4 list in one synthetic output. Also tell the kit round that in the fallback case the 1B record says `complete` false and names a pool file that does not exist.
2. **D2:** state the engine-X binding of every wrapper kind in SCORERS-78B.md and `pins_78b.json shared`; the kit round packs scorer pods with engine X; the Mac steps run on a checkout whose engine identity is X.
3. **D3 (kit round, track A/K):** `classifier` under S_78 needs `S78_KINDS` to hold it (or a main-recipe key with an S_78 command line); REQ-3's pass and A1's pass need two kind names and two caps (C2); the untuned_answers E upper should count the s3 list (C3).
4. Accept or reverse `shared.untuned_recipe_s = main` in Part 2's scorer section (C1: the recorded recipe hash differs from 1B's form; the values do not).
5. Optional test additions (C5): a repeated-flag test for `flag_value`; an `exit_code` assertion on the wrapper record; an end-to-end `run_kind` for `untuned_answers` with a doses block (needs a CPU-sized family settings file or a fixture family).
6. The builder's own jobs (fill the pins by event; `l1_first_block`; the llama `scan.modules` entry; carry `scripts/scale78b/` in the bundle) stand; I found nothing against them.

## 8. Unresolved concerns

- D1 shows the fallback was designed on the wrapper's side only; whether the kept rate at 7-8B stays near 89% (the 1B rate) is unknown until the pass runs, so the fallback path must be safe before the first scorer pod.
- Parity is of the plumbing, as the builder says; P78:357's "any-model Part C scripts" became "the 1B scripts under a family settings file". That is simpler and the 1B code is model-agnostic (R: `representation_pass.py:84-93`), but the layer rule (`scan.first_block`) is still null, so `l1_scan` cannot run until Part 2 decides it.
- `build_s_pool__F.json` and the `s_pool` kind are untested beyond parity on the fixtures and the preflight; they matter only if Part 2 rebuilds the S-pool per family.
- I did not run any 7B model, pod or CUDA path; every M here is on CPU fixtures, hashes and files.
