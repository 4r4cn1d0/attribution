# Track B-b14: independent verification 1 (D-6 re-pin and the B14 inputs writer)

Written for the lead by the Opus verifier, 2026-11-01 at 09:26 UTC (clock read with `date -u` just before writing).

- **Verdict: verified.** I found no defect that matters for the reading's correctness, the frozen rules or blinding. Section 6 lists minor points as notes.
- **Object checked:** worktree `scratchpad/builds/ws-b`, detached at `55d5f8b`. Changed: 6 tracked files and 3 new untracked files. Their SHA-256 values equal the builder's §2 table: `overlap_inputs.py` `952e59eb…`, `overlap_inputs_check.py` `57a7efb2…`, `test_b14_inputs.py` `84b2b59c…`, the spec `4f6e0b6b…`, settings `92c3a4a0…`, `overlap_strata.py` `4249b070…`.
- **I did not edit ws-b or the main checkout.** I wrote only my own scripts under `scratchpad/builds/verify-B-b14/` and this report. Every test basetemp I made is deleted.
- **Data rules.**
  - The only kit file I read was `plan.json` (parsed). I printed only metadata: kind, arm, seed, host, block, done, status, pulled, role, recipe, engine, `deferred_from`, the edit SHA prefix, and the unit path with hex masked.
  - I opened no unit, seal, judge, answer, label or guard file, and nothing under `hosts/`, `judges*/`, `seals/`, `retrieved/`, `units/` or `eval/`.
  - For the W1 manifest's 7 sealed records, 2 pinned inputs and 1 prediction, I used the manifest's paths only.
  - All other checks used synthetic kits.

## 1. Premise: which recipe each unit kind used (confirmed, read-only)

**plan.json** (`tmp/stage1-olmo/plan.json`, `419cb04d8ed37b6b…`, 422,916 B):
- Plan code A. Seal entries A and B each carry a hex `sha256`.
- Kind/recipe/engine counts include `('arm','S','X') 55` and `('a0_arm','S','X') 5`.
- The `recipes` table holds exactly four configs:
  - REC `9e9bde6f…`
  - S `ceffe0ef…` (training identity `f46279e5…`)
  - G `c004349c…`
  - B+Qi `37942cf5…` (engine Y)
- `engines` X = `472fc7f6…`, Y = `34bfd288…`.
- `prepared` = `9ed61826…`, the same value B14's `identity.manifest_sha256` keeps.

**Kit code: recipe S for every arm and a0 run.**
- `plan_tool.default_recipe` gives "S" for `arm` and `a0_arm` (`runkit/stage1-olmo/plan_tool.py:524-527`).
- The job runner takes `RECIPE_NAMES[job.recipe or "S"]` (`setup/job_runner_stage1.py:215-216`).
- Its preflight asserts that each recipe's config hash equals `plan["recipes"][path]["config_sha256"]` (`:662-668`).
- The engine writes `job.json` `recipe_sha256` = `config_sha256(recipe)` (`experiments/safety_selection/planning.py:74`, `runner.py:1313`).
- So every kit arm and a0 unit's job.json names `ceffe0ef…`.

**The reading's a0 units at 1102 and 1103** are the Gate A pins in `REJUDGED_PINS["A"]` (`stage1_rules.py:171-211`).
- `scripts/stage1/settings/limits_check.json` `gate_a_identity` gives REC and Gate A's code `55253874…`. This is inferred; I opened no unit.
- There is no kit `a0_arm` job at 1102–1103.

**Selection per cell** (from my own metadata print):
- Each of the 22 kit cells has exactly one complete job on a done host of its table's block.
- No such job carries a `pulled` key or a `role`.
- The deferral sources on a-5, a-6, a-7 and b-4 are `not_started`.
- No edit record has an `engine_arm` key.
- This equals the builder's §9 table: S1 a-11/a-3/a-4/b-21/b-5/b-6; S3 a-9/a-10/a-11/b-1/b-2/b-3; S4 a-3/a-4/a-9/b-21/b-5/b-6; a0 pins at 1102–1103, then a-10/b-1/b-2/b-3.
- The checker's candidate route also finds exactly one candidate per cell. So byte equality is expected on the real kit.

**Configs.**
- REC and S differ only in `attribution.checkpoints`, `attribution.query_bank`, `name` and `purpose`. This is the builder's claim; I confirmed it by diff.
- S and G differ also in five `train.*` fields.

## 2. D-6 (the settings-only re-pin)

**The re-pin itself.**
- **Settings.** The diff drops `identity.recipe_sha256`, keeps `manifest_sha256`, and sets `refused_recipes` = [G, B+Qi]. The rest of the diff is notes.
- **Code.** `overlap_strata.py` changes only the `SETTINGS_SHA256` literal (line 60), and the file hashes to it.
- **Accepts what the reading needs.** It accepts REC (the Gate A a0 units) and S (every kit unit) and refuses G and B+Qi.
- **Tested both ways.** The builder's tests cover this, and so do my cases 3d, 3f and 3g (§4).

**Nothing frozen changed.**
- **The 130 W1 code, settings, test and rule-text files** are hash-equal to the W1 manifest. This includes `limits_common.py` (`2798aa06…`) and `s1common.py`.
- **No changed path is a manifest entry.**
- **B16, the builder (`reading_input/**`), the engine and Gate B's pinned scripts** are unchanged.
- **The main checkout's `scripts/` and `runkit/`** are unchanged.

**Nothing downstream breaks.**
- Neither B16 nor the builder pins B14's script or settings hash, so D-6 breaks neither.
- REV4 §9.4's overlap-control rule text names no recipe. So D-6 changes no rule text, which the 1b report also says.

**Mutation spec** (150 entries, of which 63 are new):
- Every find text occurs exactly once on the final tree.
- No entry refers to the old settings hash.
- Each of the 13 settings mutants re-pinned in the spec (the 6 existing B14S entries and 7 B14D6 entries) carries the SHA-256 of its own mutated settings file. I recomputed all 13.
- `reports/mutants_b14_near.json` (`77c3def1…`) holds the 69 new and re-pinned entries, each identical to the spec's.

## 3. The inputs writer and its second computation

**End to end on a synthetic kit** (`make_world`, which has deferral copies, a not-done host, an LN-12 host, a G reference unit, a cert host and an unpulled re-run). I ran the real command lines as subprocesses:
1. `overlap_inputs.py` writes; exit 0.
2. `overlap_strata.py report --inputs <that file>` (the real parser and every unit check) reads it; exit 0. Its units equal the inputs' units by path, COMPLETE.json and job.json.
3. `python -I -B overlap_inputs_check.py` gives "same bytes"; exit 0.
4. Two writer runs produce identical bytes.

**Hash only (audit hook).** I ran `sys.addaudithook` over the writer's run. Under the data root it opened only `plan.json` and the COMPLETE.json and job.json of exactly 24 unit folders. It listed no folder and opened nothing there for writing. The builder's own test also shows the two unit files are never parsed: non-JSON bytes still give their hashes.

**Refusals.** The builder's 38 parametrized refusal cases and its other tests pass. My extra cases are in §4.

**Agreement with the builder.** On the builder's synthetic kit, the writer's 24 units equal `build.build`'s cells (`test_on_the_builders_synthetic_kit_the_units_are_the_builders` passes). The builder's `overlap_block` (`build.py:508-524`) independently re-checks B14's units at the reading.

## 4. Commands I ran (foreground; venv python `-B`, `PYTHONDONTWRITEBYTECODE=1`, basetemps under `builds/tmp/`, deleted)

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | pytest the six `test_b14_*.py` files in ws-b | 0 | **207 passed** (pytest 16.65 s). The command passed the tool's 600 s limit, and the harness moved it to the background. I started no background job. It finished, and its basetemp was deleted. |
| 2 | pytest `reading/tests/test_overlap.py` + `reading_input/tests/test_items.py` (they use B14's code and settings) | 0 | 71 passed |
| 3 | pytest `test_s1_layout.py`, `test_s1_repin_tool.py`, `test_s1_repin_b10.py` | 0 | 79 passed |
| 4 | `verify-B-b14/e2e_check.py ws-b <tmp>` | 0 | 22 of 22 checks pass (below) |
| 5 | `verify-B-b14/spot_mutants.py` (the runner's layout: `scripts/stage1` unchanged, `scripts/stage1_s1` mutated, PYTHONPATH copy:ws-b; four B14 test files; T1's outcome rules) | 0 | baseline 169 passed; 8 of 8 sampled builder mutants killed; 2 of my own mutants survive (§6, N2) |
| 6 | read-only checks: `plan_meta.py` on plan.json; the W1 manifest hash check; spec find-text, re-pin and subset checks; config diffs; git diff, status and log | 0 | as in §§1–2 |

**My extra cases (all pass, `e2e_check.py`):**

| Case | What I did | Result |
|---|---|---|
| 3a | A unit folder is a symbolic link onto another cell's folder | refuses "name one unit" |
| 3b | A unit folder is a symbolic link outside the data root | refuses "not inside the data root" |
| 3c | The strata hold an extra add set S2 | written; the report lists S2 as not in the plan |
| 3d | job.json says G while plan.json says S | the writer writes; the report refuses "its recipe is a refused" |
| 3e | The documented limit: job.json says `9…9` while plan.json says S | the writer writes, and the report reads it |
| 3f | B+Qi on engine Y as an a0 kit unit | the report refuses |
| 3g | A hand-made inputs file names the G `ref_train` unit as a0 1105 | the report refuses by recipe |
| 3h | A complete unit of a B14 cell in block C | refuses |
| 3i | job.json is a folder | refuses |
| 3j | plan.json repeats a key | refuses |
| 3k | theta0's pin moved to 1104 | the writer and the checker still agree |
| 3l | The a0 pin renamed "A0 …" | the writer refuses "0 a0 entries" |

**Sampled builder mutants, all killed:** B14D6-refused-without-g, B14D6-identity-s, B14D6-refused-not-passed, B14I-done-off, B14I-pin-hash-off, B14I-symlink-followed, B14C-always-same and B14C-target-ignored.

**Not re-run by me (the lead's long jobs):**
- the whole `scripts/stage1_s1/tests` folder (the builder reports 999 passed);
- the `reading_input` suite (195);
- B16's full suite (261);
- the 150-entry mutation spec.

## 5. Acceptance criteria

| Criterion | Status |
|---|---|
| Premise confirmed (kit units S, Gate A a0 REC) | **passed** (plan.json and code; units not opened) |
| Settings-only re-pin; `limits_common.py` and all W1 files unchanged | **passed** |
| Accepts REC and S | **passed** |
| Refuses G and B+Qi | **passed** |
| `SETTINGS_SHA256` updated | **passed** |
| Fixtures fixed | **passed** |
| `recipe_s` test inverted | **passed** |
| Refusal tests added | **passed** |
| Near mutants added | **passed** |
| B14's tests pass | **passed** (207) |
| Writer: right schema; plan A by the report's own seed plan (`d1_plan_a`, 1102–1107); hash only; refuses ambiguity | **passed** |
| Accepted by the report's real parser on a synthetic kit | **passed** |
| Second, independent computation reproduces the file byte for byte | **passed** (in process, isolated `-I`, hand-built document) |
| Full spec and full suites | **not tested** by me (§4) |

## 6. Notes (minor; none blocks the reading)

**N1. D-6's deny-list limit, made concrete.**
- Case 3e reproduces it. A kit unit whose job.json recipe is neither G nor B+Qi passes B14's own checks. The writer cannot see this: it never parses job.json.
- **In the real kit no such unit exists.** The recipes table holds four configs. G is refused. B+Qi is refused twice, by recipe and because engine Y's code `34bfd288…` is not in `allowed_code_sha256`.
- **The kit's other recipe-S units with engine arm a0 at the reused seeds are refused anyway.** These are the LN-12 regenerations and the LN-15e retrains. They are train-only: the runner docstring says "no --bank, so evaluate_bank is null". So they have no `eval/e1`, and B14's `eval/` check refuses them. I inferred this from the code; I opened no unit.
- **What binds the right units at the reading:** the inputs file's pins (from plan.json and `REJUDGED_PINS`) and the builder's cross-check.
- **The builder's optional code allow-list [REC, S]** would close only the unknown-recipe case. It is the lead's ruling. The FOCUS 04:55 ruling chose settings only.

**N2. Two survivors among my own mutants (test gaps on paths the real kit does not use).**
- `VB-absolute`: `unit_path` uses `.absolute()`, not `.resolve()`.
- `VB-engine-arm-ignored`: the writer ignores plan.json's `edit.engine_arm`.
- Both survive the four B14 test files (169 passed).
- **Why they do not matter for this reading:**
  - The real kit's edit records carry no `engine_arm`, which I verified.
  - The builder reports that `tmp` and `tmp/stage1-olmo` are not symbolic links.
  - With `.absolute()`, the report's own `check_unit` still resolves paths and refuses a unit outside the data root. The checker's `realpath` route would also disagree.
- **Reproduction:** `python -B verify-B-b14/spot_mutants.py <ws-b> <scratch> VB-absolute VB-engine-arm-ignored`. Expected: killed. Actual: survived.
- **Optional hardening:** a test with a folder symbolic link (my 3a/3b) and a test with an `engine_arm` record.

**N3. The inputs file carries a `sources` block beyond the brief's five keys.**
- The report ignores it; I checked this end to end.
- It binds plan.json's SHA-256. So run the checker right after the writer, before any later plan.json write (for example kit round 34's records). Otherwise it reports DIFFERENT at `sources.plan_json_sha256` while the units are unchanged.

**N4. The checker's serializer is the same `json.dumps` call as `canonical_json`.**
- Byte equality needs that.
- Its independence lies in the selection route (candidates, not tables), its own hashing and its own path code.

**N5. The writer is stricter than the builder in a few places.**
- It refuses B+Qi's own a0 at any status.
- It refuses a complete unit in a block that is not read (C, certify), or on a host that is not done.
- It refuses a complete-but-unpulled job outside its block.
- None of these applies to the real kit, by the plan.json metadata in §1.

**N6. Stale wording in a W1 file.** `limits_common`'s refusal text still says "a refused (Gate B) recipe". It is W1, so it stays unchanged. The builder flagged this.

**N7. Ordering.** The strata must be made under settings `92c3a4a0…`. Commit D-6 before `overlap_strata.py strata`; otherwise both the writer and the report refuse the strata. The builder flagged this.

**N8. The records draft's "87 entries" for D-6's spec** is now 150; the builder flagged this.

## 7. My evidence files

- `scratchpad/builds/verify-B-b14/e2e_check.py`: the CLI chain, the audit, and cases 3a–3l.
- `scratchpad/builds/verify-B-b14/trace_open.py`: the audit hook.
- `scratchpad/builds/verify-B-b14/spot_mutants.py`: the sampled mutants and my two mutants.
- `scratchpad/builds/verify-B-b14/plan_meta.py`: the plan.json metadata print; no outcome fields.
