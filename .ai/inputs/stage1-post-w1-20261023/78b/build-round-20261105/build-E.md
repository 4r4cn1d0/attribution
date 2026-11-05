# Build round 3, track E: the per-family scorer layer (7-8B)

Status: DONE (skeleton 16:46 UTC; finished right after the clock read at 17:23 UTC on 5 Nov 2026, `date -u`, in
`build-E-scratch/cli/cli-transcript.log`). Worker: a bounded build worker for General Implementation X.
Worktree: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-e` at HEAD 953f520 (M: `git rev-parse --short HEAD`).
Labels: M measured (the command), R read (path:line), E estimate (basis), I inference. No pod, no spend, no network,
no install, no download, no agent, no message. No git state changed anywhere (M: `git status --short` shows only the
new paths; `git diff --quiet HEAD` exits 0). No forbidden folder opened; no answer, prompt, judge or sample text
printed or stored by me (the tests check every output for the fixtures' texts; the real prepared sets were read only
by the frozen code, which drops the text, and only ids, counts and hashes were printed).

## 1. Files added (all new paths; nothing tracked was edited)

| Path (under the worktree) | What | SHA-256 (M: `shasum -a 256`, 17:19 UTC) |
|---|---|---|
| `scripts/scale78b/scorers_78b.py` | the wrapper: `KIND --family F <the 1B script's own arguments>`; runs the unchanged 1B script's `main()` with the family's settings; the family preflight; the nested doses | `2d4b7face2a9d1356657afce57990705972baac11efccb803003ef4945897ba9` |
| `scripts/scale78b/make_scorer_settings_78b.py` | derives the 18 settings files and the index from the 1B settings (hash-pinned) and `pins_78b.json`; `--check` | `6d37770ab237b0908b5a90dc1a180abe6250b1ffa6e988a98bed6b2a2852fe5c` |
| `scripts/scale78b/settings/pins_78b.json` | the one place with every per-family value and every null pin with its event | `cd3c085085ff0744b20a7d5e19bdc1ff2ddc93d156c9481f93825a7cf2f72416` |
| `scripts/scale78b/settings/PINS-78B.json` | the index: each settings file's SHA-256; pinned by `scorers_78b.py` `PINS_FILE_SHA256` | `cba2f0b290842eda03217ebfbffc01471f9febda543b84cf190937b91e544986` |
| `scripts/scale78b/settings/<script>__<family>.json` (18) | for `make_untuned_answers`, `representation_pass`, `representation_pools`, `score_l1_larf`, `score_classifier`, `score_s3_datarx`, `write_score_edit`, `write_add_edit`, `build_s_pool`, each for `olmo2-7b` and `llama31-8b` | listed in `PINS-78B.json` |
| `scripts/scale78b/SCORERS-78B.md` | the map (kind -> 1B script, settings, inputs, per-family differences, waits), the command lines, the fill procedure, the concerns | (text) |
| `scripts/scale78b/tests/scorers/conftest.py`, `test_scorer_settings_78b.py`, `test_s4_doses_78b.py`, `test_scorers_78b_parity.py`, `test_scorers_78b_family.py` | 88 tests (a new sub-folder, so the tracked `scripts/scale78b/tests/conftest.py` stays untouched) | |
| `tmp/kt-prepared/prepared-kt-dolly-{olmo2,llama3}/{manifest.json, manifest.sha256, prepare_receipt.json, engine/}` | git-ignored copies of the two prepared sets' manifest and engine files, for the family tests (copied from the main checkout's `tmp/kt-prepared/`; no `hidden/`, `selector/`, `banks/` or `auditor/` copied) | manifests `9ed61826…`, `c52a50af…` (M) |

## 2. The map (the full table is `scripts/scale78b/SCORERS-78B.md` section 2)

Kind -> 1B script -> family settings -> inputs -> what differs per family -> what it waits for:

- `untuned_answers` -> `make_untuned_answers.py` -> `make_untuned_answers__F.json` -> the 1B sealed lists `s4_candidates.json` (798613c4…), `s3_safe.pool.json` (6801652c…), `s1.json` (389c20ad…) by PATH:SHA256 (R: `.ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json`), REC and `--recipe-s` = the family's main recipe (OLMo-2-7B `18cc31d7…`, Llama-3.1-8B `74758af1…`) -> the model and codec through the engine's loaders from the recipe, `lists.s4.keep` 192, the `doses` block -> waits for nothing (section 3 below).
- the anchor job -> the pinned Gate B `scripts/make_anchor_answers.py` unchanged (model-agnostic: it reads REC; R: `:107-110`) with `--prompts <the sealed full list 78467c97…> --recipe MAIN_F` -> no settings of mine -> per model answers -> waits for nothing.
- `rep_pass` (REQ-3's representation pass for L1, S3, DataShield-style, the Gate C reproduction) -> `representation_pass.py` -> `representation_pass__F.json` + `representation_pools__F.json` (both pools null; no plant or decoy pool at 7-8B) -> P_F, S_78, the family anchor file, the s3_safe pool, then the s3_orig pass -> manifest, model (`allenai/OLMo-2-1124-7B-Instruct` 470b1fba… / `meta-llama/Llama-3.1-8B-Instruct` 0e9e39f2…), recipe S_78 (null), anchor bank (null); n layers and hidden size read from the model -> the anchor job, S_78, the untuned pass.
- A1's attributes pass -> the engine's attributes job on the a0-1101 retrain's q and e1 states under S_78 (the stage-1 kit's `a1_rescore` form); its consumer `write_score_edit.py a1` -> `write_score_edit__F.json` with six null pins -> the anchor job, S_78, the retrain.
- `l1_scan` -> `score_l1_larf.py scan` -> `score_l1_larf__F.json` -> P_F, MAIN_F, the anchor file -> manifest, REC, anchor bank (null), `scan.first_block` null (Part 2's layer rule), `scan.modules` by model type -> the anchor job, Part 2.
- `classifier` -> `score_classifier.py` -> `score_classifier__F.json` -> P_F, S_78 (the guard), the anchor file -> manifest, model, S_78 (null), anchor bank (null) -> the anchor job, S_78.
- `c0`, `o_only`, `regenerate` -> the engine and the frozen S1 package (`lean_eval_job.py`, `oext_unit.py`); not this layer's; mapped for the kit round.
- Mac: `l1_score`, `score_edit` (scorer l1; a1), `s3_score`, `add_edit` (s1, s3, s4, s4_96, s4_192; s4_top null), `s_pool` (only if Part 2 rebuilds the S-pool) -> the 1B scripts with the family files; `write_score_add.py` needs no family file (its settings pin no family value).

The token limits are equal in all three recipes (`max_train_tokens` 3072, `max_prompt_tokens` 1536, batch 32, 2048 new
tokens; M: printed on 5 Nov 2026), so the only per-family limit is the codec, which every 1B script builds from the
recipe or the manifest (R: `make_untuned_answers.py:237-240`, `build_s_pool.py:464-473`).

## 3. Alternatives and why chosen

1. **Run the unchanged 1B `main()` with a settings file (chosen) against copying the scripts into any-model versions
   with a parity test (P78:357's wording).** Every 1B scorer script already is model-agnostic; what pins it is the
   settings file and the literal `SETTINGS_SHA256` in `main()`. The wrapper imports the module, hashes it, and replaces
   that literal (and `representation_pass`'s pool-pins globals) for one call, restoring afterwards: the 1B D-2 wrapper's
   own pattern (R: `scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py` doc, `run_base`). No scoring code exists
   twice, so there is nothing that can drift; the parity test shows the plumbing gives the 1B functions' bytes.
   Rejected: a copy (two code paths to keep equal; P78:357 allows the copy only "if unavoidable").
2. **Settings derived by a maker from the 1B files and one pins file (chosen) against hand-written files.** Nine scripts
   times two families is 18 files; a hand edit of 18 files at each fill is where a pin goes wrong. The maker's `--check`
   is a test; `test_the_two_families_differ_only_where_they_should` lists exactly the per-family paths.
3. **One literal pin on the index (chosen) against 18 literals in the wrapper.** `rules_78b.py`'s A1/A13 pattern (one
   null pin, filled by a recorded step) extended to a file: filling a pin changes the settings, the index and one
   literal, printed by the maker.
4. **The family block and `waits` inside each settings file (chosen) against a table in the wrapper.** The 1B
   `check_settings` ignores extra keys, so the data stays with the file it describes, and the wrapper's null check is
   data-driven (which pins each command needs).
5. **The main recipe as `--recipe-s` for the untuned pass and the add-edit writer (chosen; one key in `pins_78b.json`)
   against waiting for S_78.** Stated in section 7 as a tradeoff for the lead; it unblocks the pass before the anchor
   job and changes no value (S_78 shares the main recipe's model section by construction).
6. **The dose lists as new files beside the 1B outputs (chosen) against post-editing the 1B `s4.json`.** The 1B outputs
   stay byte for byte what the 1B code writes (parity), and the dose files carry Part 1's names (s4, s4_96, s4_192,
   s4_top) with a text-free record. Under a 1B settings file (no `doses` block, no `family_78b`) the wrapper writes
   nothing extra, which is what the parity test needs.
7. **`scan.first_block` null (chosen) against a value.** The L1 layer rule at n = 32 is Part 2's (Part 1 section 14
   item 1); the scan refuses until the lead fills it. Both candidates are written down (10 by share, 5 absolute).
8. **A nested test folder with its own conftest (chosen)** because the tracked `scripts/scale78b/tests/conftest.py` may
   not be edited and the parity tests need the 1B and engine fixture paths.

## 4. Commands run (cwd = the worktree unless stated; main venv = `tmp/minimal-experiment-20261002/venv/bin/python`, transformers 4.56.2, torch 2.8.0, Python 3.11.15; `PYTHONDONTWRITEBYTECODE=1` set)

| # | Command | Exit |
|---|---|---|
| 1 | `git rev-parse --short HEAD; git status --short` (worktree) | 0; HEAD 953f520, clean |
| 2 | reads of Part 1, RUL, ADD, PLAN T6, CHECK C1/C6/M1/M2, P78:330-370, the 1B scripts, settings, tests, fixtures, `rules_78b.py`, `stage1_rules.py`, `job_runner_stage1.py`, `make_recipe_s78.py`, `make_anchor_answers.py` (`sed`, `grep`, Read) | 0 |
| 3 | `python -B -c` printing `config_sha256`, model fields of the three recipes; `code_identity()` (472fc7f6…); `shasum -a 256` of the 1B scripts and settings; the S-pool record's list hashes (`-I -B`; names, counts, hashes only) | 0 |
| 4 | `cp` of the two prepared sets' `manifest.json`, `manifest.sha256`, `prepare_receipt.json`, `engine/{train_rows.jsonl, groups.json, query_rows.jsonl}` into the worktree's git-ignored `tmp/kt-prepared/` | 0; `git check-ignore tmp/kt-prepared` says ignored |
| 5 | `python -I -B scripts/scale78b/make_scorer_settings_78b.py` (first run) | 2 (REFUSED: KeyError; `write_score_edit.json` has no top-level `requirement`; fixed: `requirement_78b`) |
| 6 | the same, after the fix; then with the ordinal fix ("192nd") | 0, 0; wrote 19 files |
| 7 | `python -I -B scripts/scale78b/make_scorer_settings_78b.py --check` (three times, the last two under `-I -B` in the evidence logs) | 0: "19 of 19 files equal their regeneration" |
| 8 | `python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/scorers/test_scorer_settings_78b.py scripts/scale78b/tests/scorers/test_s4_doses_78b.py` | 1 failed, 56 passed (a test's allowed-path list missed `recipe_sha256`; test fixed) |
| 9 | `… pytest -q -p no:cacheprovider -x scripts/scale78b/tests/scorers/test_scorers_78b_parity.py` | 1 failed (the tiny model caps every answer, kept 0; the stop-rule check moved to the 1B test's generator; the parity assertion itself had passed) |
| 10 | `… pytest -q -p no:cacheprovider scripts/scale78b/tests/scorers/test_scorers_78b_family.py` | 6 failed, 14 passed (argparse REMAINDER swallowed `--family`: `parse_known_args` now; one match string; the `scan` subcommand: now prepended by the wrapper) |
| 11 | `… pytest -q -p no:cacheprovider scripts/scale78b/tests/scorers` (after the fixes) | 88 passed in 19.3 s, then 1 failed (a test error on the `scan` subcommand) -> `with_subcommand` added -> **88 passed in 21.4 s** |
| 12 | `… pytest -q -p no:cacheprovider scripts/scale78b/tests` (the whole folder: tracks B, C and E) | **153 passed, 2 skipped** (the two skips are track C's scipy tests, as its conftest says) |
| 13 | `python -I -B scripts/scale78b/scorers_78b.py score_edit --family olmo2-7b scorer --name l1 --scores <synthetic 4800-row scores over the real OLMo ids> --scores-sha256 … --prepared tmp/kt-prepared/prepared-kt-dolly-olmo2 --out …/out-olmo` | 0; wrote `l1_remove600.edit.json` (600 row ids), `l1_selection.json`, `wrapper_78b_record.json` |
| 14 | the same with `--family llama31-8b` on the OLMo copy | 2: "the prepared manifest is 9ed61826…, the llama31-8b settings pin c52a50af…: not this family's prepared set (nothing written)" |
| 15 | `python -I -B scripts/scale78b/scorers_78b.py rep_pass --family olmo2-7b --prepared … --recipe <OLMo main> --anchors /nonexistent --out …` | 2: "2 pin(s) it needs are null; the first, pins.anchor_bank_sha256, waits for: the OLMo-2-7B anchor job …" |
| 16 | `python -I -B scripts/scale78b/scorers_78b.py untuned_answers --family llama31-8b --recipe <Llama main> --recipe-s <Llama main> --list s4=/nonexistent:… --out …` | 2: the preflight passed (both recipe hashes) and the 1B main refused the missing list ("list s4 cannot be read (FileNotFoundError)") |
| 17 | `python -I -B scripts/scale78b/scorers_78b.py --help` | 0 |
| 18 | `git status --short; git diff --stat HEAD; git diff --quiet HEAD; git diff --quiet HEAD -- scripts/stage1 runkit experiments .ai` | only `??` new paths; "no tracked file changed"; the four folders unchanged |
| 19 | `date -u` (16:46, 17:19, 17:23 UTC); `shasum -a 256` of the new files | 0 |

Longest command: 29 s. No job for the lead is needed to re-run anything here.

## 5. Evidence paths

- The worktree files of section 1 (absolute root in the header).
- `…/scratchpad/b78/reports/build-E-scratch/pytest-scale78b-all.log`: the whole-folder pytest run (153 passed, 2 skipped).
- `…/scratchpad/b78/reports/build-E-scratch/cli/cli-transcript.log`: commands 13-15 and 7 re-run under `-I -B` with their exit codes and `git status`; `cli/l1_scores_synthetic.json` (ids and random scores; no text); `cli/out-olmo/`, `cli/out2-olmo2-7b/` (an edit file of row ids, the selection record, the wrapper record); no `out-llama` folder (refused before anything was written).
- The hashes of section 1 and SCORERS-78B.md section 7.

## 6. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| the map (kind -> 1B script, settings, inputs, per-family differences, waits) | passed | `scripts/scale78b/SCORERS-78B.md` section 2 and 5; this report section 2 |
| the settings files and any wrappers, in the 1B schema, nulls documented | passed | 18 files + `pins_78b.json` + `PINS-78B.json`; `test_the_1b_check_settings_accepts_each_file_on_its_1b_name` (18 cases: the frozen `check_settings` accepts each), `test_every_null_is_listed_in_waits_and_every_wait_is_null` (18), `test_the_per_family_values` (2); one wrapper `scorers_78b.py` (import, not copy) |
| the parity tests pass (M) | passed | `test_scorers_78b_parity.py`: untuned_answers, rep_pass, l1_scan, classifier (pod; fixture loaders), l1_score, s3_score, score_edit scorer, add_edit, s_pool (Mac), the first-keeps rule, the restored pin: 11 tests; byte-identical except the wall-clock fields (the 1B determinism tests' rule); 88 passed in 21 s (command 11) |
| the family refusals pass (M) | passed | `test_scorers_78b_family.py`: each family's settings accept its manifest and main recipe and refuse the other's (preflight, 3 kinds x 2 families + score_edit + untuned_answers), the null pins refuse by their event, the whole command line on the real sets (2 families; exit 0 then 2 for the other family), the pod kind's null refusal, a changed 1B script refuses; commands 13-15 |
| the 1B files byte-identical | passed | command 18: `git diff --quiet HEAD -- scripts/stage1 runkit experiments .ai` exits 0; `test_the_1b_scripts_and_settings_are_byte_identical_to_the_pins` holds the 9 scripts and 9 settings files to their SHA-256s, and the four the stage-1 kit pins to `stage1_rules.py`'s values |
| no text printed or stored | passed | every output file of the tests is scanned for the fixtures' texts (`test_deterministic_and_text_free` forms; `test_the_wrapper_writes_the_three_nested_lists_and_a_text_free_record`); the CLI runs printed hashes and counts only; the real sets were read by `PreparedView` (text dropped) and only ids went into the synthetic scores; the dose lists hold text by design (the 1B `s4.json` form, under the job's `--out`, pulled to tmp/ by the kit) and their record is text-free |
| the S4 sizing and nesting rule (brief item 3) | passed | `candidates_needed(192, 57, 64)` = 216 (ruling 12's "about 216"), 7 chunks; `nested_doses` on synthetic lists (prefixes, the fallback at 48-191, exit 3 below 48); the settings' `doses.sizing` block |
| CUDA paths | not tested | as in the 1B scripts (CPU fixtures only) |
| the real anchor job, S_78, the retrain, the A1 pass | not tested | they are pod jobs; the pins are null until each event (section 7) |

## 7. Jobs for the lead and the kit round

1. **Fill the pins by event** (SCORERS-78B.md section 5): per family, after the anchor job: `families.F.anchor_bank_sha256`
   (= its record's `anchor_file_sha256`); after `make_recipe_s78.py` and the commit: `families.F.recipe_s78.{path,
   config_sha256}` (the same value as `rules_78b.py` RECIPE_S[F]); after the retrain and A1's pass:
   `families.F.a1_attributes_unit.{complete_sha256, retrain_complete_sha256}` and the a1 `code_sha256` (the engine that
   ran them). Then: `python -I -B scripts/scale78b/make_scorer_settings_78b.py`, set `PINS_FILE_SHA256` in
   `scorers_78b.py` to the printed value, run `tests/scorers`, commit `pins_78b.json`, `settings/*.json`,
   `PINS-78B.json`, `scorers_78b.py` by explicit path.
2. **Part 2 (the scorer section, before any scorer output is read):** fill `shared.l1_first_block` (10 by the 1B share,
   or 5 absolute; the scan refuses until then); confirm or change the `llama` `scan.modules` entry (`self_attn`, `mlp`,
   carried from the 1B file's "stage 2 reading" note); cite the code hashes of section 1 and the 1B `STAGE1_CODE`.
3. **Decide `shared.untuned_recipe_s`** ("main", as set, lets the untuned pass run before the anchor job; "s78" makes
   it wait). One key; the maker regenerates.
4. **The kit round (track K):** the job runner's command lines are SCORERS-78B.md section 2 (each is `python -I -B
   scripts/scale78b/scorers_78b.py KIND --family F` plus the 1B script's own arguments with the plan's PATH:SHA256
   pins); the bundle must carry `scripts/scale78b/scorers_78b.py` and `scripts/scale78b/settings/` and pin them in the
   kit's `STAGE1_PINS` form; two kinds for the two passes now both called `rep_pass` (concern 1); the runner reads
   `wrapper_78b_record.json` (exit code, `doses.fallback_fired`) beside the 1B record; the E caps per kind are track
   A's (`rules_78b.py` E_KINDS).
5. **Order per family (addendum A2 plus this layer):** untuned_answers (needs nothing) and the anchor job (needs
   nothing) first, on their own single-job pods; then S_78 (the maker, the commit, the pins); then the a0-1101
   retrain; then rep_pass (two passes), classifier, l1_scan (after Part 2's layer rule) and A1's attributes pass; then
   the Mac steps (l1_score, s3_score, the S3 pick, score_edit, add_edit).
6. No long run is needed here; the suite runs in under 30 s.

## 8. Unresolved concerns

1. **`rep_pass` names two passes.** The stage-1 kit's `rep_pass` is REQ-3's representation pass (`representation_pass.py`,
   about 1 h at 1B; R: `stage1_rules.py:87`, `job_runner_stage1.py:24-30`); Part 1 section 12 and `rules_78b.py`
   S78_KINDS call `rep_pass` "A1's pass" with RP:43's 6-11 h and a 16.5 h cap, which is the engine's attributes job on
   the retrain's states (the kit's `a1_rescore` form). Both need S_78 and the anchor file, but they are two pods with
   two caps. The kit round should carry two kinds.
2. **What the unchanged 1B code gives at keep 192:** a keep after the 192nd is labelled `kept_after_the_48th` (R:
   `make_untuned_answers.py:171`); the W1-06 loss table's `s4` entry covers all 192 kept rows and is omitted when the
   fallback fires (the 1B exit 3). Documented in the settings; not fixable without a 1B edit.
3. **The fallback's exit code.** The wrapper exits 0 with `fallback_fired` true (Part 1 pre-sets the fallback as a valid
   outcome) while the 1B record says `complete` false. If the lead prefers exit 3 in the fallback, it is one line in
   `build_doses`.
4. **Parity's reach.** The wrapper runs the 1B `main()`, so parity is of the plumbing; the untuned pass through `main()`
   ran on the tiny fixture model whose answers are all capped (kept 0 on both routes); the keep path is covered through
   the 1B test's generator at the API level. CUDA untested.
5. **The Llama anchor job** encodes the 1B list's 64 harmful pairs under Llama's tokenizer; the pinned script stops if
   one exceeds 3072 tokens (R: `make_anchor_answers.py:117-121`). Low risk (I), but then the list needs a reviewed
   version.
6. **`build_s_pool__F.json`** carries `expected_evaluation_forms` 11,954, unverified for the Llama manifest (I); it
   matters only if Part 2 rebuilds the S-pool per family (the default re-uses the 1B sealed lists).
7. **The 7-8B bundle** must include `scripts/scale78b/` for the pod kinds (the stage-1 bundle carries `scripts/stage1/`);
   whether `pack_setup.py` copies it is the kit round's check.

## 9. Replies to questions the lead may ask

- *Why not pass `--settings` to the 1B scripts directly?* Each `main()` refuses any settings file but the one its
  literal `SETTINGS_SHA256` names (R: the eight `load_settings` calls in section 1 of SCORERS-78B.md). The wrapper
  replaces that literal for one call, as the 1B D-2 wrapper did for the pool pins, and restores it (tested).
- *Is the settings' `name` the 1B script's name on purpose?* Yes: `check_settings(doc, SETTINGS_NAME)` inside each 1B
  `run()`/`build()` requires it (R: `s1common.py:577`); the family lives in `family_78b`.
- *Does `labels_sha256` matter?* It is a record only; `check_settings` checks the named `label_entries` digests against
  the registry (R: `s1common.py:585-589`), and the maker verifies them before writing.
- *Why main recipe as recipe S for the untuned pass?* Section 3 item 5 and SCORERS-78B.md section 4; the value is the
  same, the schedule is freer, one key reverts it.
