# Track B-b14: D-6 (B14's recipe re-pin) and the B14 inputs writer

Written for the lead by the Opus builder, 2026-11-01 at 06:23 UTC (clock checked with `date -u` at 06:23:00 UTC).

- **Worktree:** `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/ws-b`, detached at `55d5f8b`. Nothing is committed or staged. No git command changed state.
- **Not touched:** the main checkout, `limits_common.py` and every other W1 file, B16 (`scripts/stage1_s1/reading/**`), the engine, Gate B's pinned scripts, `runkit/`, the builder (`reading_input/**`, its `synth_kit.py` used read-only).
- **Data rules:** I opened no unit, seal, judge, guard, answer or outcome file. Section 11 lists what I did read.

## 0. Short answer

1. **D-6 is in.** It is a settings-only re-pin, as asked. `report.identity` keeps `manifest_sha256` and drops `recipe_sha256`. `refused_recipes` is now recipe G `c004349c…` and B+Qi `37942cf5…`. The new pin is `SETTINGS_SHA256 = 92c3a4a0…`.
2. **The premise holds.** I checked `plan.json` and the kit code. All 55 `arm` jobs and all 5 `a0_arm` jobs record recipe "S" on engine X. The a0 units at 1102 and 1103 are Gate A's pinned REC units.
3. **The writer is new.** `scripts/stage1_s1/overlap_inputs.py` writes `overlap_inputs.json` for plan A (`d1_plan_a`: a0, S1, S3 and S4 at 1102–1107). It hashes unit files and never parses them. It refuses every ambiguous case in §4: 38 cases in one parametrized test, and 2 more tests.
4. **There is an independent second computation.** `scripts/stage1_s1/overlap_inputs_check.py` uses the standard library only and imports no module of this repository. It recomputes the file by another route and compares it byte for byte. Exit codes: 0 same, 1 different, 2 refused.
5. **Tests pass.** All B14 test files: 207 passed. The whole `scripts/stage1_s1/tests` folder: 999 passed. The builder suite: 195 passed. B16's suite: 261 passed.
6. **Mutants.** The spec grows from 87 to 150 entries: 63 new, and the 6 existing re-pinned entries re-pinned again. On the B14 test files, all 69 new or re-pinned mutants are killed. 86 of the 87 existing ones are killed; the one survivor is expected (§7).
7. **One limit (the main open point).** D-6 is settings only, so B14's report now refuses only G and B+Qi. A unit of any other recipe hash passes B14's own checks. The unit pins and the writer's `plan.json` check cover the real reading. A 3-line code allow-list would close this gap. Your ruling is needed (§10, point 1).

## 1. The premise, checked first (read-only)

- **plan.json** (`tmp/stage1-olmo/plan.json`, SHA-256 `419cb04d8ed37b6b…`, 422,916 B):
  - The kind/recipe/engine counts include `('arm','S','X') 55` and `('a0_arm','S','X') 5`. The other kinds are `ref_train` G (engine X, 6 jobs) and `ref_train` bqi (engine Y, 6 jobs). The rest are not units of B14's cells.
  - The `recipes` table holds exactly four configs: REC `9e9bde6f…`, S `ceffe0ef…` (training identity `f46279e5…`), G `c004349c…` and B+Qi `37942cf5…` (engine Y).
  - `engines`: X = `472fc7f6…`, Y = `34bfd288…`.
- **Kit code** (`runkit/stage1-olmo/stage1_rules.py`; the kit's live copy `tmp/stage1-olmo/stage1_rules.py` is byte-identical, `bde78fab…`):
  - `TRAINING_IDENTITY_RECIPES = ("S",)`; `REUSED_SEEDS = (1101, 1102, 1103)`.
  - The a0 `REJUDGED_PINS["A"]` entries are at 1101–1103, checkpoint e1.
  - `block_runs("A", "A")` holds S1/S3/S4 at 1102–1104 and a0 at 1104. `block_runs("A", "B")` holds S1/S3/S4/a0 at 1105–1107.
- **Configs**, computed with the engine's own `config_sha256` and `training_identity`:
  - REC and S differ only in `attribution.checkpoints`, `attribution.query_bank`, `name` and `purpose`. B14 reads neither attribution field.
  - REC and S share training identity `f46279e5…`. G's training identity is `68f63289…`.
- **Why G and B+Qi must stay refused.** A `ref_train` unit is the engine's calibrate unit with engine arm `a0` (stage1_rules.py:153-159). So only its recipe tells it apart from an a0 unit.

## 2. Files changed (all in the worktree; SHA-256 of the final bytes)

| File | Change | SHA-256 |
|---|---|---|
| `scripts/stage1_s1/settings/overlap_strata.json` | D-6: identity without the recipe; refused = [G, B+Qi]; `identity_note` extended; new `refused_recipes_note` | `92c3a4a006ea5bf45eb04b01d3fa6f59d7b260408c28df11a4d9848b0a20a41d` (was `b98d012e…`) |
| `scripts/stage1_s1/overlap_strata.py` | only the `SETTINGS_SHA256` literal (line 60) | `4249b070695a2409332655043224ca49db05fdb6ebca9906cb7900387db1d6c9` (was `ad4db8cd…`) |
| `scripts/stage1_s1/overlap_inputs.py` | **new**: the inputs writer (374 lines) | `952e59eb083f1b945794141d9c90876e4667d679639eeab04b0ecae74ab248f4` |
| `scripts/stage1_s1/overlap_inputs_check.py` | **new**: the second computation (209 lines) | `57a7efb2ed538d54b3fb305f6e21d3e136c73a03285819acd63b242eaab4f80a` |
| `scripts/stage1_s1/tests/test_b14_inputs.py` | **new**: 62 tests of the writer and checker (589 lines) | `84b2b59ca0809f7f274a5a45f19a608d3e33b6924bbe42e0f11a0ec8cb8bfd71` |
| `scripts/stage1_s1/tests/test_b14_report.py` | fixtures by the real layout; `recipe_s` and `recipe_other` refusal cases removed; 8 D-6 tests added | `6ef62e5d24b0410e317b81bab77f65afecee5f2f30ab8c4a435d229446ea8c11` |
| `scripts/stage1_s1/tests/test_b14_pins.py` | D-6 content test against the configs, `limits_check.json`, `oext_unit_y.json` and the kit rules; "no random draw" and "standard library only" tests extended to the new scripts | `15829ce544114295d4ebc4dc8d14de83f932a7b192d831340311af1b5ec2258f` |
| `scripts/stage1_s1/tests/b14_fixtures.py` | `RECIPE_G`, `RECIPE_BQI`, `GATE_A_SEEDS`; `write_unit` defaults to a kit unit (recipe S) | `cb536cc18cdd0a7000a00c9076be3176b8c6e91e3d564466690d477e2c9e4ac8` |
| `scripts/stage1_s1/mutation/mutants_b14.json` | 6 re-pinned entries re-pinned; 63 entries added; key `d6_and_inputs` | `4f6e0b6b6c7caa55ea203515118fe47082f5c37354462f81eb34c330a2d6a11c` |

`git diff --numstat` for the tracked files: spec +586/−13, `overlap_strata.py` +1/−1, settings +3/−3, fixtures +7/−2, pins test +34/−10, report test +69/−10. The other three files are new and untracked.

## 3. D-6: design and the alternatives I rejected

**What changed.** `limits_common.check_unit` reads `identity` as exact job.json field values and `refused_recipes` as a deny-list (LC:167-171). Neither can express "REC or S". So the only settings-only fix is the one in the brief: drop the recipe from `identity` and refuse G and B+Qi. Every unit is still bound by:

- its COMPLETE.json and job.json SHA-256 pins;
- the frozen sealed check;
- the arm, seed, checkpoint and manifest checks;
- the allowed engine codes.

**Test changes.**

- **Fixtures.** `build()` in `test_b14_report.py` now follows the real layout. a0 at 1101–1103 uses Gate A's code and REC. Every other unit uses engine X and recipe S.
- **The inverted case.** The old `recipe_s` refusal case is now `test_d6_kit_units_of_recipe_s_and_gate_a_a0_units_of_rec_are_read`. There are also a plan-B variant and a "kit unit of REC is read" test.
- **New refusals.** G and B+Qi refuse for an S1 unit and for an a0 unit (4 cases). Each matches the recipe refusal's own message.
- **The limit, recorded.** The old `recipe_other` case cannot hold after a settings-only D-6. It became `test_d6_the_report_refuses_only_the_two_reference_recipes`, which records the limit (§10, point 1).

**Rejected alternatives.**

1. **A code allow-list in `overlap_strata.py`** (`accepted_recipes` = [REC, S], checked after `check_unit`, the same way `allowed_code_sha256` is checked at STR:356-358). It closes the gap in §10, point 1. I did not build it because the brief says settings only. It is ready to add if you rule for it: about 3 lines of code, 1 settings key, a `check_content` line, 2 tests and 2 mutants.
2. **Pinning the training identity instead.** job.json carries no training identity (`experiments/safety_selection/runner.py:1312-1318`: it is in the run identity, not the job template), so `identity` cannot pin it.
3. **A long deny-list of every other config in the repository.** It is still not closed, and it is brittle.

**Ordering (unchanged from R1B).** The strata record binds the strata settings' SHA-256, so D-6 must be committed before `overlap_strata.py strata` runs. A strata record made under `b98d012e…` would be refused by the report.

## 4. The inputs writer: design

**Command:**

```
python -B scripts/stage1_s1/overlap_inputs.py --kit DIR --strata FILE --strata-sha256 HEX --out DIR
    [--reading plan_a] [--rules FILE] [--repo DIR] [--data-root DIR]
```

**Output.** `overlap_inputs.json`, in the engine's canonical JSON, written once into an absent or empty folder (`s1.write_new_files`, the B14 convention). It holds:

- `kind` "stage1 overlap report inputs", `version` 1;
- `strata_sha256`;
- `seed_plan` `d1_plan_a`;
- `units` {name: {seed: {path, complete_sha256, job_sha256}}}, each path relative to B14's data root;
- `sources`: the reading, the plan code, the SHA-256 of `plan.json`, of the rules module and of B14's settings, and each unit's origin. A pinned unit's origin is the pin's name. A kit unit's origin is its block, host and job index. The report ignores `sources`.

**Selection.** It mirrors the builder (`reading_input/build.py`: `cell_blocks`, `pins_by_cell`, `_primary_jobs`), so B14's units equal the builder's (the builder checks this at `build.py:508-524`).

- **a0 at a reused seed** (1102, 1103): the one `REJUDGED_PINS["A"]` entry named "a0" at that seed. It must have checkpoint e1, and its COMPLETE.json and job.json must hash to the pin.
- **Every other cell:** the one `a0_arm` job (for a0) or `arm` job (for an add set) of that arm and seed in the block whose table holds the cell. The job must be complete and not recorded as `pulled: false`, and its host must be done.
- **Hashing:** COMPLETE.json must hash to `plan.json`'s `complete_sha256`. job.json is hashed and named.

**What it reads.**

- `plan.json`, B14's settings and the strata record, all parsed.
- The rules module, run from the bytes it is hashed from, as the builder runs it.
- Of each unit, only the bytes of COMPLETE.json and job.json. They are hashed, never parsed. A test replaces both with bytes that are not JSON, and the writer still writes their hashes.

**Refusals** (exit 2, nothing written; each has its own test):

- **plan.json:** the plan code is not A; a block read has no seal entry.
- **The tables:** a cell in two tables, in none, or reused and also in a table.
- **The a0 pins:** none or two at a seed; another arm or checkpoint; the files differ from the pin; the path is not plain.
- **The kit jobs:**
  - two complete units of one cell, or none (a crashed or not-pulled job counts as none);
  - a complete unit on a host that is not done;
  - a complete unit in a block that does not hold the cell, or in another block (for example certify);
  - a job of the other kind;
  - B+Qi's own a0.
- **The kit unit's records in plan.json:**
  - a recipe other than `TRAINING_IDENTITY_RECIPES`;
  - a config SHA-256 that B14's settings refuse (D-6's early warning);
  - an engine whose code identity B14 does not allow;
  - an add set's edit that is not the strata's add set, an add set without an edit record, or an a0 unit with an edit.
- **The kit unit's files:** COMPLETE.json not at `plan.json`'s SHA-256; the unit path not plain; a symbolic link; a missing file.
- **The strata record:** not at its SHA-256; made under other settings (B14's own `_strata_record` check); without an add set of the plan; an add set whose arm is not `edit-<its edit SHA-256>`.
- **Paths:** a folder outside the data root; a path that B14's `path_pattern` refuses; one folder or one COMPLETE.json for two cells.
- **The rules module:** it does not load, or it lacks a name the writer needs.
- **The output:** the output folder exists and is not empty.

**Design choices and rejected alternatives.**

- **No seal is read.** The writer refuses a complete unit on a host that is not done, because the seal's `moved` list decides that case and this writer does not read seals. That is stricter than the builder, and it never applies on the real kit: every job on the not-done hosts a-5, a-6, a-7, b-4 and cfy-1 is `not_started`. I rejected reading the seals because the builder binds every unit to its block seal anyway, and a smaller read surface is safer.
- **The writer does not import the builder's code.** The builder is a frozen-ish package, and other tracks work beside it. I mirrored its rules, cited them, and added a test on the builder's own synthetic kit that runs `build.build`: the writer's 24 units equal the builder's cells by COMPLETE.json and job.json SHA-256.
- **Early checks from plan.json** (recipe, engine, edit against the strata). B14's report runs the same checks on job.json, but only at the reading (R1a, after the second stamp). The early checks surface a problem at step 0.4 instead.
- **Plan A only** (`--reading plan_a`). `plan.json` records plan A with blocks A and B sealed, and the builder refuses `plan_a_block_a_only` once block B is sealed. Adding another reading means one table row and its tests.

## 5. The second computation

**Command:**

```
python -I -B scripts/stage1_s1/overlap_inputs_check.py --file FILE --kit DIR --strata FILE
    [--reading plan_a] [--rules FILE] [--repo DIR] [--data-root DIR] [--settings FILE]
```

It shares no code with the writer. A test checks its imports: standard library only. The routes differ:

- **Candidates instead of tables.** It does not use `block_runs` or `REUSED_SEEDS`. Each cell takes its one candidate from two sources: the pins of arm a0 at that seed with checkpoint e1, and the plan.json jobs of the cell's kind, arm and seed that are complete, not unpulled, and on done hosts of blocks A or B.
- **Its own hashing:** hashlib in 1 MiB blocks.
- **Its own paths:** `os.path.realpath` and `os.path.relpath`.
- **Its own serializer:** `json.dumps(sort_keys, indent=2, ensure_ascii=False)` plus a newline.
- **Defaults** come from its own location. From the main checkout they name the same files as the writer's defaults.

**Tests.**

- **Reproduction.** On the synthetic kit it reproduces the writer's bytes, in process and as an isolated `python -I -B` subprocess. A third route, the hand-built document from the world's ground truth, gives the same bytes.
- **Planted differences.** It finds 7 kinds, and for each it names the first differing key:
  - a changed digit;
  - a job.json changed after writing;
  - re-indentation;
  - an extra key;
  - another strata file;
  - another plan.json;
  - a changed rules file.
- **Shared refusals.** It refuses 5 of the writer's ambiguity cases itself.
- **Where the routes differ.** Two tests record this:
  - a theta0 pin moved to 1102 changes neither route;
  - an extra a0 pin at 1104 makes the writer take the kit unit while the checker refuses with "2 candidate units". So a disagreement shows instead of a silent choice.

## 6. Commands run (foreground; Python = the minimal-experiment venv, `-B`, `PYTHONDONTWRITEBYTECODE=1`; each basetemp deleted after)

| # | Command (in the worktree) | Exit | Result |
|---|---|---|---|
| 1 | pytest of the 5 B14 test files, **before** any change (baseline) | 0 | 136 passed, 5.8 s |
| 2 | pytest pins + report + strata, after D-6 | 0 | 105 passed |
| 3 | pytest `test_b14_inputs.py` (first version) | 0 | 55 passed |
| 4 | pytest inputs + report + pins | 0 | 139 passed |
| 5 | pytest `test_b14_inputs.py` (final, with the added checks) | 0 | 62 passed |
| 6 | pytest `test_b14_*`, `test_s1_*`, `test_oext_*` | 1 | 467 passed, 1 failed: `test_oext_unit_y.py`, which needs engine Y's tree under `<checkout>/tmp/` and a worktree has none (environmental) |
| 7 | the same `test_oext_unit_y.py` with `STAGE1_ENGINE_Y_TREE=/Users/spiderishi/Coding/attribution/tmp/engine-y-34bfd288` (read-only use of that code tree) | 0 | 8 passed |
| 8 | pytest `test_b10_*`, `test_b11_*`, `test_b17_*` | 0 | 529 passed, 56 s |
| 9 | pytest the whole `scripts/stage1_s1/tests` (with the engine-Y variable) | 0 | 997 passed, 93 s |
| 10 | pytest `scripts/stage1_s1/reading_input/tests` (the builder; basetemp 2.7 GB, deleted) | 0 | 195 passed, 159 s |
| 11 | pytest `scripts/stage1_s1/reading/tests` (B16) | 0 | 261 passed, 51 warnings (the same counts as the earlier baseline), 407 s |
| 12 | pytest `test_b14_pins.py` after extending it | 0 | 19 passed |
| 13 | pytest the whole `scripts/stage1_s1/tests` on the **final** tree | 0 | **999 passed**, 132 s |
| 14 | pytest `--collect-only` of the six `test_b14_*` files | 0 | 207 tests |
| 15 | `python3 -I -B tools/update_b14_spec.py ws-b` (dry run), then `--write` | 0, 0 | every find text of all 150 entries occurs exactly once on the final tree |
| 16 | near-mutant runs (§7), 4 runs | 0 each | see §7 |

There were also read-only checks: `git status/log/diff/rev-parse` (no state change), `shasum`, `wc`, `grep`, `sed`, `awk` and `python3 -I` one-liners (§11).

Two commands did not run:
- A `timeout 560 …` prefix failed at once with exit 127 (no `timeout` on macOS); nothing ran, and I re-ran without it.
- One `sed` loop with a zsh array expansion was blocked by the tool's safety check before running; I re-ran it as plain `sed -n`.

## 7. Mutation entries

- **Re-pinned (6 existing entries).** `B14S-plan-b-old-seeds`, `-plan-b-with-s3`, `-plan-b-block-a-missing`, `-plan-b-block-a-with-s3`, `-plan-b-block-a-seeds` and `B14S-s-p-role-primary-repinned`. Their `SETTINGS_SHA256` find text is now `92c3a4a0…`. Each replace value is the SHA-256 of the new settings file with that mutant's own edit applied.
- **Added: 8 D-6 entries (`B14D6-*`).**
  - Seven settings mutants, each re-pinned: G no longer refused; B+Qi no longer refused; S added to the refused list; D-6 fully reverted; REC as an identity field; S as an identity field; identity empty.
  - One code mutant: `refused_recipes` not passed to `check_unit`.
- **Added: 41 writer entries (`B14I-*`).** One per check in §4, plus:
  - the origin index;
  - plan.json hashed from its parsed form;
  - another settings SHA-256;
  - non-canonical output;
  - output that overwrites.
- **Added: 14 second-computation entries (`B14C-*`):**
  - always "same";
  - the first of two candidates taken;
  - job.json's hash taken from COMPLETE.json;
  - the pin check off;
  - the COMPLETE.json check off;
  - not-pulled units counted;
  - hosts that are not done searched;
  - every block searched;
  - paths taken from the wrong root;
  - indent 1;
  - the strata hash taken from plan.json's bytes;
  - the pin checkpoint ignored;
  - the first difference not named;
  - the plan code unchecked.

**Runs.** My scratch harness `scratchpad/builds/tools/near_mutants.py` lays out each run as `run_mutants_b14.py` does: `scripts/stage1` unchanged, `scripts/stage1_s1` mutated, PYTHONPATH `copy:workspace`, the import probe, and T1's outcome rules. It runs **only the B14 test files**. A kill there is a kill in the full run, because the full run's tests are a superset.

| Set | Test files | Result | Evidence |
|---|---|---|---|
| 8 D-6 + 6 re-pinned | pins, report, strata, inputs | 14 killed (baseline 167 passed) | `reports/near-mutants-d6.json` |
| 8 D-6, behaviour tests only | report, inputs | 8 killed: not only by the content test | `reports/near-mutants-d6-behaviour.json` |
| 41 B14I + 14 B14C | pins, report, strata, inputs | 55 killed | `reports/near-mutants-inputs.json` |
| the 87 existing entries | all six `test_b14_*` | 86 killed, 1 survived | `reports/near-mutants-existing.json` |

The one survivor is `FIX-layout-b14-no-stage1-copy`. It mutates the runner `mutation/run_mutants_b14.py` itself, which my harness does not execute, and its killing test is outside the B14 files. So this result is expected and not a regression.

**Not run: the full spec** with `run_mutants_b14.py`; that is yours. Each mutant runs the whole `scripts/stage1_s1/tests` folder, measured at 93–132 s unmutated on this Mac.

- The full 150-entry spec takes about 4–5.5 h (E).
- The near set is ready as `scratchpad/builds/reports/mutants_b14_near.json` (69 entries, same format, SHA-256 `77c3def1…`). It takes about 1.8–2.5 h (E).

T1's runner has no option to select ids, so pass that subset file as `--spec`. In a worktree, the baseline needs `STAGE1_ENGINE_Y_TREE` (row 6 of §6). In the main checkout the default path exists.

## 8. Commands for the lead (from the main checkout, after 1b and after D-6 is committed)

```
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
PYTHONDONTWRITEBYTECODE=1 $PY -B scripts/stage1_s1/overlap_inputs.py --kit tmp/stage1-olmo \
  --strata "$STRATA" --strata-sha256 "$STRATA_SHA" --out "$RD/b14-inputs"
$PY -I -B scripts/stage1_s1/overlap_inputs_check.py --file "$RD/b14-inputs/overlap_inputs.json" \
  --kit tmp/stage1-olmo --strata "$STRATA"            # exit 0 and "same bytes: … sha256 <H>"
```

These replace the heredoc of R1D step 0.4. The report then runs with the default `--data-root` (the writer's default is the same `lc.DEFAULT_DATA_ROOT`):

```
overlap_strata.py report --strata "$STRATA" --inputs "$RD/b14-inputs/overlap_inputs.json" --out …
```

## 9. Expected selection on the real kit (from my read of plan.json; the writer was NOT run on real data)

| Cell | 1102 | 1103 | 1104 | 1105 | 1106 | 1107 |
|---|---|---|---|---|---|---|
| a0 | pin "a0 1102 (Gate A)" | pin "a0 1103 (Gate A)" | A a-10 job 3 | B b-1 job 3 | B b-2 job 3 | B b-3 job 3 |
| S1 | A a-11 job 1 | A a-3 job 2 | A a-4 job 2 | B b-21 job 1 | B b-5 job 1 | B b-6 job 1 |
| S3 | A a-9 job 2 | A a-10 job 2 | A a-11 job 2 | B b-1 job 2 | B b-2 job 2 | B b-3 job 2 |
| S4 | A a-3 job 3 | A a-4 job 3 | A a-9 job 3 | B b-21 job 2 | B b-5 job 2 | B b-6 job 2 |

- **The printed line should be:** `a0: 6 units; pinned at 1102, 1103; from the kit A:a-10, B:b-1, B:b-2, B:b-3`.
- **The deferral copies are skipped.** a-5, a-6, a-7 and b-4 hold `not_started` copies of S3 1102, S1 1102, S3 1103, S3 1104, S4 1104, a0 1104, S1 1105 and S4 1105.
- **No `pulled` key** is on any of these 22 kit jobs.
- **Edit SHA-256 prefixes** in plan.json: S1 `904a0cf1`, S3 `a2f18a3d`, S4 `24aed3fb`. These match the add-set files that 1b passes to the similarity pass.
- **The checker's route selects the same 24 units.** No pin sits at 1104–1107, and no kit a0 job sits at 1102–1103.

## 10. Open points for the lead

1. **The ruling needed: D-6's deny-list.** After a settings-only D-6, B14's report accepts a unit of any recipe except G and B+Qi. The test `test_d6_the_report_refuses_only_the_two_reference_recipes` records this.
   - **Today's cover.** Each unit's job.json is pinned by the inputs file. The writer requires plan.json's recipe to be S for every kit unit and its config not refused. The checker reproduces the selection. The builder cross-checks B14's units against its own.
   - **Concrete counterexample.** A hand-made inputs file naming a unit of another recipe would pass B14 alone.
   - **Fix, if you want B14 closed by itself.** Add `accepted_recipes` [REC, S] to the settings and one check after `check_unit` in `overlap_strata.py`. That is a code change beyond "settings only", so I did not make it.
2. **The records draft** (`reports/E-D5-D6.md` §2) says D-6's spec has 87 entries. It now has 150: run the full spec, or the 69-entry near set and say which. It also omits point 1's limit; add one line if you keep the deny-list.
3. **Ordering.** Commit D-6 before `overlap_strata.py strata` runs (§3).
4. **Hashes the runbook must take.** R1D's table rows marked [FILL-B14] become `overlap_strata.py` `4249b070…` and `overlap_strata.json` `92c3a4a0…`. The two new scripts (`952e59eb…`, `57a7efb2…`) and the inputs file belong inside the second stamp.
5. **Stale wording in a W1 file.** `limits_common`'s refusal text still says "a refused (Gate B) recipe". The refused recipes are now G and B+Qi. The file is W1 and stays unchanged; the tests match only "its recipe is a refused".
6. **`path_pattern` is still the broad one** (R1B §10). Narrowing it to the kit and Gate A layouts is possible hardening. I did not do it: it is out of scope, and I cannot see the real unit folders.
7. **S1 blinding record (REV4:919).** D-6 and the writer were written after the W1 commit. The critic (§2.5) and the records draft list D-6. The writer is code, not an inference rule, but you may want to name it beside D-6.
8. **Environment.** In a worktree, `test_oext_unit_y.py` needs `STAGE1_ENGINE_Y_TREE`. This predates my change.

## 11. What I read (data rules)

- **Code and settings:** read in the worktree, the main checkout's `runkit` and `tmp/stage1-olmo/stage1_rules.py`, and the `tmp/engine-y-34bfd288` tree (used by one test through the environment variable).
- **plan.json:** parsed with `python3 -I`. I printed only:
  - its keys, the recipes and engines tables, and the seal entries' sizes and hashes;
  - per host: block, done, job count;
  - per job: kind, recipe, engine, arm, seed, status, pulled, `deferred_from`, the unit path with hex masked, and the edit SHA-256 prefix.
  I printed no output, reason or COMPLETE field.
- **The W1 manifest:** roles and paths only (no `scripts/stage1_s1` entry; `limits_common.py` and `s1common.py` are W1 code).
- **One listing.** One command printed `ls -la tmp | head -3`, which showed only the header lines (`total`, `.`, `..`), no entry name. I then tested `tmp/` and `tmp/stage1-olmo` with `test -L` only (neither is a symbolic link).
- **Not opened:** any `hosts/`, `judges*/`, `seals/`, `retrieved/`, `units/` or `eval/` folder, any COMPLETE.json or job.json of a real unit, any answer, label, guard or judge file, the hidden or selector bank, and any plant or decoy path.
- **Peer report:** I read `reports/E-D5-D6.md` §2 as data only, to align facts.
