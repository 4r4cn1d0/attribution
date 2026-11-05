# Track F verify report (adversarial)

Started 2026-11-05 17:48 UTC; written 2026-11-05 18:06 UTC (`date -u` before each time). Verifier: self-identified
Fable 5.1 (the launcher's routing evidence governs). Role: adversarial verifier; no builder file edited; no git state
changed; nothing written outside my scratch.

- Builder's report: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/build-F.md`
- Builder's worktree (WS, read-only for me): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-f` (HEAD 953f520; `git status --short` lists six untracked paths only; `git diff --stat` empty, M)
- My scratch (SCR): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/verify-F-scratch/`
- To avoid writing into WS, every test and build ran in `SCR/wsf-copy/` (an rsync of WS without `.git` and `__pycache__`; 114 MB; deleted after this report, see section 8). MAIN = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python` (3.11.15, numpy 2.2.6); SCI = `/Users/spiderishi/Coding/attribution/.venv/bin/python`. Every MAIN run had `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1`; every pytest had `-p no:cacheprovider`. All commands foreground; the longest about 2 min.

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference. No text was printed or stored.

## 0. Verdict: DEFECTS

The scientific outputs hold (M, re-measured byte for byte): the fingerprint logic and its 1B test, the OLMo S1 decision
(record `9b340bf5…`), the Llama S1 edit `69426993…` with MANIFEST `a3986274…`, the recovered sealed list, and the RV2-2
test (both re-verifier survivors killed). One tool defect is major and must be fixed before the lead commits:
**`scripts/scale78b/s1_olmo2_7b_check.py` deletes the folder named by `--scratch-tmp` on every refusal, including a
pre-existing folder it did not create** (F-1; measured three times). Three minor items (F-2, F-3, F-4). The fix for
F-1 is three lines in a non-sealed script and changes no sealed byte.

## 1. Files added by me (scratch only)

`SCR/inspect_s1_llama3.py` (+ `_out.txt`), `SCR/guard_probe.py` (+ `_out.txt`), `SCR/mutate_rv22_verify.py` (+ `_out.txt`),
`SCR/fp_cli_1b_out.txt`, `SCR/fp-1b-pair.json`, `SCR/fp_cli_differs_out.txt`, `SCR/fp-differs-pair.json`,
`SCR/olmo_check_out.txt`, `SCR/olmo-check-record.json`, `SCR/llama_build_{1,2}_out.txt`, `SCR/destructive_finally_probe_out.txt`,
`SCR/pytest_fc_rv22_venv_out.txt`, `SCR/pytest_main_venv_out.txt`, and this report. Nothing under WS, the main checkout, or `runkit/`.

## 2. Defects

| id | severity | where | what (M unless marked) | fix |
|---|---|---|---|---|
| **F-1** | **major** | `scripts/scale78b/s1_olmo2_7b_check.py:211-213` (`main`, the `finally` block) | `finally: if not args.keep and scratch.is_dir(): shutil.rmtree(scratch)` runs after EVERY refusal, and `scratch` is whatever `--scratch-tmp` names, whether or not this run created it. Measured on fake folders in SCR: (a) `--scratch-tmp SCR/victim/tmp/precious` (holding `keep.json`) with `--edit /nonexistent/edit.json` → `REFUSED: FileNotFoundError`, exit 2, **the folder and its file are gone**; (b) `--scratch-tmp SCR/victim2/tmp/precious` (non-empty) with the real edit → `REFUSED: … exists and is not empty: a sealed output never overwrites`, exit 2, **the folder is gone** (the refusal says it never overwrites, then the cleanup deletes it); (c) repeated as `victim3`, gone; with `--keep` (`victim4`) it survives. `wae.full_out_ok` runs inside `check()`, so a `--scratch-tmp` outside any `tmp/` folder is refused and then deleted too (I, from the code path; not measured because my scratch lies under `/private/tmp`). The builder's test `test_a_tampered_edit_refuses_before_anything_is_measured` asserts `not scratch.exists()` on a folder that never existed, so it does not see this. The default path (`<repo>/tmp/scale-78b-s1-olmo2-7b-check`) is safe only while nothing is there; `--scratch-tmp <any existing folder>` is data loss (for example a prepared set, I). Evidence `SCR/destructive_finally_probe_out.txt`. | Before `check()`: `created = not scratch.exists()`; in `finally`: remove only `if created and not args.keep and scratch.is_dir()`. Add a test: a pre-existing non-empty `--scratch-tmp` survives a refusal (and is refused). Not a sealed file; the OLMo verdict record (`9b340bf5…`) is unchanged by the fix (the record holds no script hash). |
| F-2 | minor | `.ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py:204-224` (`guard_out`) | The forbidden roots are this script's own checkout (`REPO` from `__file__`) and `--repo` only. On two fake checkouts A and B in SCR (all six `FORBIDDEN_DIRS` present in both), with the module's `REPO` set to A: `guard_out(B/<sealed>/out/new, None)` and `guard_out(B/…, A)` are **ALLOWED**; with `repo=B` refused. So the worktree's copy of the script run with `--out` pointing into the MAIN checkout's sealed folder is not refused by name (only the non-empty rule would stop it when the target exists and is non-empty). The docstring says this scope (R :205-207); the sibling sealed scripts have the same scope (R reverify-BC2.md section 7 observations). 26 of 28 guard probes behaved as the README says; see section 4. Evidence `SCR/guard_probe_out.txt`. | Lead's call: one README sentence ("run from the checkout that holds the sealed folders, or pass `--repo`"), or add the main checkout's path as a third root. A code change is a byte change: rebuild into empty `out/` (the arm `edit-69426993…` would change, because the settings carry the script's hash). My pick: the README sentence, as the re-verifier chose for RV2-1. |
| F-3 | minor | same script, `FORBIDDEN_DIRS` :97-99 | The S1 folder itself (`.ai/inputs/scale-78b-s1-llama3-20261105`) is not in its own forbidden list: `guard_out(<own>/out2)` and `guard_out(<own>/tmp/x)` + `wae.full_out_ok(<own>/tmp/x)` are ALLOWED (fake layout), so an operator can write a second output set, or the text-bearing edit, inside the sealed tree beside the committed `out/`; only the committed `out/` is protected (non-empty rule, measured: `check_output_folders(<own>/out)` refuses; the CLI with the default `--out` refuses with exit 2). The sibling folders were accepted with the same scope last round (R reverify-BC2.md section 7). | README sentence (no rebuild), or the same self-exclusion the lead chooses for the siblings. |
| F-4 | minor (test coverage; a tracked test file, not the builder's) | `scripts/scale78b/noise_reading.py:258-264` (`environment_differs`) against `scripts/scale78b/tests/test_noise_reading.py` + the new RV2-2 file | Two of my eleven hand mutants survive all 35 noise tests: **V6** (drop one compared field other than `gpu` from the comparison: `k != "cudnn" and …`) and **V8** (the guard-record comparison inverted, `==` for `!=`). Both survive because every test perturbs `gpu` only, and because the reference a0@1101 on this Mac is a Gate A unit with no guard record while the synthetic family gives every unit the same guard dict, so the guard branch never sees a difference. Part 1 section 3.3 names "an environment or guard-record difference" as a trigger, and every 7-8B unit carries a guard record (R Part 1 §2.2), so V8 is the untested branch that matters there. Outside RV2-2's brief (the reference), found by the task's "at least five hand mutants". Evidence `SCR/mutate_rv22_verify_out.txt`. | A new test file (no tracked edit): a synthetic family whose units carry guard records with one unit's guard changed → `["guard"]` on that unit alone; and one perturbation of a non-`gpu` compared field. |

Observations, not defects: (i) with the committed non-empty `out/` as `--out`, the CLI's refusal line ends
"(3 files left under the output folders)" (REQ-7's `refusal_state` counts the pre-existing committed files; nothing
was written; M). (ii) `s1_olmo2_7b_check.main` loads the sealed builder before its `try`: a missing builder file gives a
traceback (exit 1) rather than `REFUSED` (exit 2) (I from the code; not measured). (iii) The edit's provenance names
REQ-7's path and hash as `script`; the wrapper's hash reaches it only through `provenance.settings_sha256` (the builder
documents this; M that the chain holds: settings `derived_from.by_sha256` = the script's hash = MANIFEST `script.sha256`).

## 3. Check 1: the fingerprint script against ruling 10, and its 1B test

- **Which files are compared (R).** `read_unit` reads `COMPLETE.json` only (`complete`, `target_checkpoint`, `identity`,
  `checkpoints.<q|e1>.{adapter,optimizer}_fingerprint`) and cross-checks `states/<c>/state.json` when present
  (`fingerprint_compare.py:76-125`). Those are the fields the engine writes (R `runner.py:500-504`) and the frozen Gate B
  reading read (R `gate_b_reading.py:1217-1221`, adapter and optimizer; its trigger compared adapter only, :1331-1332).
  Ruling 10 names "q and e1 adapter and optimizer" (R lead-rulings-part1-20261105.md:134-136; Part 1 §3.7). Match.
- **Equal/differs logic (R :149-172).** Four lines; `equal` iff 4 of 4; anything else `differs`; exit 0/1; refusals exit 2
  with nothing written. The identity block (code, training identity, manifest, recipe) is printed as hashes and does not
  enter the verdict (Y and X differ in code identity by design; S_78 and the main recipe share the training identity).
- **Hashes only (M).** Every printed line is a hash, a verdict word or a path; the record's strings are hashes, two
  folder paths, `e1`, the rule citation (200 chars) and the meaning sentence (126 chars); no row text anywhere
  (`SCR/fp-1b-pair.json` structure dump; `_text_hits` 0 on all outputs).
- **The real equal pair (M).** `SCI -I -B scripts/scale78b/fingerprint_compare.py --retrain <w0b-2 1101-a0-e1-a1>
  --reference <Gate A olmo2-1b-1101 1101-a0-e1-a1> --expect-adapter q=322d737a --expect-adapter e1=aad79060 --out
  SCR/fp-1b-pair.json` → 4 of 4 equal, exit 0; record SHA-256 `703ee6e0…` = the builder's.
- **A real differing pair (M; the builder tested tampered copies only).** Gate A a0-1102 (`tmp/family-probe-olmo2-1b-gateA-1102/…/1102-a0-e1-a1`) as `--retrain` against a0-1101 → 0 of 4 equal, verdict differs, exit 1; identity equal on all four fields (same engine, recipe, manifest). The init unit `1101-a0-init-a1` as retrain → `REFUSED: … no checkpoint 'q'`, exit 2. `--expect-adapter q=322D737A` (upper case) → refused, exit 2. `--out` existing → refused, exit 2 (`SCR/fp_cli_differs_out.txt`).
- **Is the reference record the right one? Yes (R + M).** The test's reference is the Gate A a0-1101 unit whose
  `COMPLETE.json` hashes to `8f0fa83a…` (M) = `GATE_A_PINS["1101"]["complete_sha256"]` (R `gate_b_reading.py:156-157`),
  the family's a0-1101 reference under Gate B's environment rule (R Part 1 §2.2, PRE:107 via RUL). The retrain is wave 0b's
  `w0b-2` unit, `COMPLETE.json` `d154f23f…` (M) = FOCUS:199 ("retrain d154f23f…"; "fingerprint trigger false (the
  retrain's q and e1 adapter fingerprints equal P1101's)", R `research/FOCUS.md:199`). The adapter values equal the frozen
  C-7 pins (R `gate_b_reading.py:168-169`; M in the test). The "16 of 16 files equal" record the task names is the X→Y
  certificate C1 (R `.ai/inputs/stage1-post-w1-20261023/block-a/certificate_xy.json`: `c1_unit cert/1101-R-c1-a1`,
  `comparator runkit/stage1-olmo/compare_c1.py`, `replicate_of tmp/gate-b-olmo/retrieved/w0a-1/…/1101-edit-f7d7eb…`):
  an **R_1101** unit compared file by file against wave 0a's R unit, under `tmp/stage1-olmo/` (forbidden to both of us).
  It is not an a0 retrain, and the readiness plan's T6 test names "the 1B pair (Gate B's retrain record)" (R
  78b-readiness.md:316), which is the w0b-2 pair. So the builder's pair is the right one; concern 6 of build-F is right.
- **Tests (M).** `SCI -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_fingerprint_compare.py
  scripts/scale78b/tests/test_noise_reading_rv2_2.py` in `SCR/wsf-copy` → 17 passed (10 + 7; no skips, so both 7-8B side
  units are on this Mac and carry P78:82's abbreviations), exit 0. Also 10 passed inside the 41-test main-venv run.
- **Train-only retrains have the record (R).** The w0b-2 unit has no `eval/` folder yet holds `COMPLETE.json` with the
  checkpoints block (M `ls`), so the kit's `retrain` kind on engine X produces what the script reads. Engine Y's record
  format is not known yet; a renamed field would make the script refuse (fail closed), not mis-read (I).

## 4. Check 2: the OLMo S1 decision, re-measured

`MAIN -I -B scripts/scale78b/s1_olmo2_7b_check.py --edit "<main checkout>/tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-904a0cf1…-e1-a1/edit.json" --scratch-tmp SCR/olmo-check-tmp/scratch --out SCR/olmo-check-record.json`
(the edit named by exact path; `shasum -a 256` first: `904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10`, M; the
script re-checks the hash before `parse_edit`; no text printed) → exit 0:
(1) parse_edit accepts against `9ed61826` True; (2) 48 of 48 rows at the committed token counts under the 7B main
recipe's 3072 and under recipe S's 3072, longest row 188 tokens with eos; (3) the frozen writer with SEAL's R_d2-R_d4 as
combine inputs reproduces `904a0cf1…` exactly; a 7B-recipe rebuild gives `66bdc0f5…`, add rows identical, differing at
`provenance.inputs.recipe` and `provenance.settings_sha256` only. Verdict equal as it stands. Record SHA-256
`9b340bf5…` = the builder's (`SCR/olmo_check_out.txt`). The record's strings are hashes, paths, counts and the verdict
sentence (102 chars); no text. The 7B main config pins the prepared set's tokenizer (`model.tokenizer.repo_id`
`allenai/OLMo-2-0425-1B-Instruct`, revision `48d788ec…` = the OLMo manifest's `data_config.tokenizer`, M), so the Mac
codec is the pod's codec for this check (I). Tests: 7 passed (main venv, in the 41).

## 5. Check 3: the Llama S1 set

All M, `SCR/inspect_s1_llama3_out.txt` (MAIN, `-I -B`, hashes/ids/counts only):
- **Embedded script hash.** `build_s1_llama3.py` hashes to `a2b0a66c4e3f9f044ad5e2090cd58af195bcdfac3f372822eb1c14805495f5a3` = MANIFEST `script.sha256` = settings `derived_from.by_sha256`. MANIFEST `a3986274…`, record `1023b4e6…` (= MANIFEST `record.sha256`), settings `36a39481…` (= MANIFEST `settings.sha256` = record `provenance.settings_sha256`), edit `69426993…` (= MANIFEST `files[0].sha256` = record `edits[0].sha256`), list `389c20ad…` = the pin.
- **MANIFEST.** No build time; `rows` 48 with `add_id`, `list_id`, `prompt_tokens`, `target_tokens`; `files[0]` the edit by path-under-full-out and hash, arm `edit-69426993…`, counts add 48 / remove 0 / rewrite 0, REQ-7's token accounting (edited corpus 4,848 rows, 38 steps); `list.source.kind` `recovered` with the edit and record hashes; the pins; engine identity `472fc7f6…`. Longest string 325 chars (the requirement citation).
- **Add rows' ids and order (REQ-7's rule, R `write_add_edit.py:82-95`: `add-<list>-<NNN>` in list order).** add ids = `add-s1-001`…`add-s1-048`; add ids and list ids equal the committed OLMo record's in the same order; MANIFEST rows = record rows. Through the engine's `parse_edit` on both edits, the per-row SHA-256 of (prompt, response) is equal in order for 48 of 48: the Llama edit holds the same 48 rows in the same order as `904a0cf1…`. Target tokens equal per row for 48 of 48 (sum 2,199 both; the Llama 3 tokenizer extends cl100k, I); prompt tokens are 23-24 more per row (sum 3,019 against 1,871; the chat template, I); longest row 212 tokens with eos under 3072.
- **parse_edit.** Accepts on the Llama stub (48 added, 0 removed, 0 rewrite, manifest `c52a50af`); refuses on the OLMo stub (`EditError`); the OLMo edit is refused on the Llama stub. MANIFEST `prepared.olmo_refusal_check.engine_refuses_the_edit` True.
- **The recovered list.** REQ-7's `read_list` reads `tmp/…/list/s1.json` by the pin (48 items, ids = the manifest's list ids). My independent recovery (the OLMo edit's rows through `parse_edit`, the committed record's add_id→list_id map, `canonical_json` of `{kind, version, name, items}`) hashes to `389c20ad…`, 22,211 bytes: the sealed list byte for byte, as the builder says.
- **Byte-identical re-runs.** `MAIN -I -B .ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py --olmo-s1-edit <exact path> --out SCR/llama-build-N/out --full-out SCR/llama-build-N/tmp/full` for N = 1, 2 → exit 0 both; `cmp`: MANIFEST, record, settings, edit and list equal between the two runs and equal to the committed `out/` and WS `tmp/` files (`SCR/llama_build_{1,2}_out.txt`).
- **Settings.** Exactly the six recorded keys differ from REQ-7's committed settings (`derived_from, owner, prepared_manifest_sha256, recipe_sha256, recipe_use, requirement`); `labels_sha256` is REQ-7's (the builder's concern 3; `check_settings` checks `label_entries` against the registry and `engine_x`, R `s1common.py:574-594`, so this is harmless); `engine_x` `472fc7f6…`; lists s1/s3/s4 at 48 rows.
- **Write guards (fake layouts under SCR only; `SCR/guard_probe_out.txt`; filesystem case-insensitive True).** REFUSED as expected: the sealed `out/`, deeper paths, the sealed root; three case variants of an existing sealed folder (`…LLAMA3-20261105`, `.AI/INPUTS/…`, mixed case with `OUT`); four symlink routes (to the folder, to its `out/`, to `.ai/inputs`, symlink + case variant); the dotted path, the `..` traversal, three relative forms (from the root, `./`, from `tmp/` with `..`); a hard link to a sealed file as `--out` (by `check_output_folders`); `--full-out` with no `tmp` component or only `tmpdir`. ALLOWED as expected: a free folder under `tmp/`; a case variant where the forbidden folder does not exist (nothing sealed there). UNEXPECTED (F-2): B's sealed folder with the script in A, `repo=None` or `repo=A`. F-3: the S1 folder's own `out2/` and `tmp/x`. CLI: `--repo SCR/fakeD --out …/GATE-B-SEALED-20261008/out/new` → `REFUSED: refusing to write under .ai/inputs/gate-b-sealed-20261008 (nothing written)`, exit 2, fakeD's `out/` unchanged; `--full-out /Users/nobody/full` → refused, exit 2; the default `--out` (committed, non-empty) → refused, exit 2.
- **Tests.** 17 passed (main venv; `SCR/pytest_main_venv_out.txt`, 41 in all with the other three files). The README's counts (17, 10, 7, 7) match pytest's collection (M).

## 6. Check 4: RV2-2 against the re-verifier's mutants, and my hand mutants

Harness `SCR/mutate_rv22_verify.py` (the builder's form: a scratch root with symlinks to the copy's folders and a copied
`scripts/scale78b/` with one mutant; SCI; the committed `test_noise_reading.py` plus the new RV2-2 file; `SCR/mutate_rv22_verify_out.txt`). Baseline 35 passed. Mutants of `noise_reading.py`:

| mutant | result | killed by |
|---|---|---|
| V1 reference a0@1103 (R4-a) | KILLED | the two new tests only |
| V2 reference R@1101 (R4-b) | KILLED | the two new tests only |
| V3 reference = the first unit read | SURVIVED | equivalent: the loop reads a0 before R and 1101 first (R :314-327), so the first unit IS a0@1101 |
| V4 `environment = all(...)` | KILLED | new tests + 2 committed |
| V5 fallback ignores the environment trigger | KILLED | new tests + 2 committed |
| V6 `environment_differs` drops the field `cudnn` | **SURVIVED** | nobody perturbs a field other than `gpu` (F-4) |
| V7 `environment_differs` drops the field `gpu` | KILLED | new tests + 1 committed |
| V8 guard comparison `==` for `!=` | **SURVIVED** | the guard branch never sees a difference on this Mac's data or the synthetic family (F-4) |
| V9 per-role reference (R units against R@1101) | KILLED | the two new tests only (the committed R4 would not: it perturbs a0@1102 alone) |
| V10 only a0 differences trigger | KILLED | the new parametrized test (R cases) + 1 committed |
| V11 the reference left out of the dict | KILLED | all three new tests + 1 committed |

So the new file kills both re-verifier survivors and two further reference mutants (V9, V11) that the committed test
cannot; RV2-2 is closed. The two survivors are a separate coverage gap (F-4), not RV2-2's.

## 7. Check 5: nothing prints or stores text

`s1common._text_hits` with the 96 list texts (read through REQ-7's `read_list`) against: the three committed `out/`
files, the README, the build script, its two test files, the five new `scripts/scale78b/` files, the builder's report
`build-F.md` and every file in `build-F-scratch/` → 0 hits each; the edit and the list → 96 hits each (text-bearing,
under `tmp/` only). My own scratch outputs → 0 hits each except the two scratch builds' `tmp/full/edits/add_s1.json`
(96; deleted with the copies, section 8). Every CLI line printed by the three scripts was a hash, a count, a verdict,
an id or a path (M, the `_out.txt` files). The two records' string fields are hashes, paths, short labels and the rule /
verdict sentences (longest 200 chars; dumps in `SCR/inspect_s1_llama3_out.txt` and the record structure dump).

## 8. Commands run (exit status; all foreground)

1. `rsync -a --exclude .git --exclude __pycache__ WS/ SCR/wsf-copy/` → 0; `shasum -a 256` of the 19 builder/frozen files → 0 (all equal the builder's `final_file_list.txt` and the FROZEN pins).
2. `shasum -a 256 "<main>/tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-904a0cf1…-e1-a1/edit.json"` → 0, `904a0cf1…` (exact path, hash first, nothing else of that folder opened).
3. `MAIN -I -B SCR/inspect_s1_llama3.py SCR/wsf-copy` → 0 (`SCR/inspect_s1_llama3_out.txt`).
4. `SCI -B -m pytest -q -p no:cacheprovider --basetemp SCR/pt-fc scripts/scale78b/tests/test_fingerprint_compare.py scripts/scale78b/tests/test_noise_reading_rv2_2.py` (in wsf-copy) → 17 passed, exit 0.
5. `MAIN -B -m pytest -q -p no:cacheprovider --basetemp SCR/pt-main -rs .ai/inputs/scale-78b-s1-llama3-20261105/tests scripts/scale78b/tests/test_s1_olmo2_7b_check.py scripts/scale78b/tests/test_fingerprint_compare.py scripts/scale78b/tests/test_noise_reading_rv2_2.py` → 41 passed, 0 skipped, exit 0 (re-run of the two main-venv files alone → exit 0).
6. `SCI -I -B scripts/scale78b/fingerprint_compare.py --retrain <w0b-2> --reference <Gate A 1101> --expect-adapter q=322d737a --expect-adapter e1=aad79060 --out SCR/fp-1b-pair.json` → 0; record `703ee6e0…`.
7. Same script: a0-1102 vs a0-1101 → 1 (0 of 4); `1101-a0-init-a1` as retrain → 2; `--expect-adapter q=322D737A` → 2; `--out` existing → 2.
8. `MAIN -I -B scripts/scale78b/s1_olmo2_7b_check.py --edit <exact path> --scratch-tmp SCR/olmo-check-tmp/scratch --out SCR/olmo-check-record.json` → 0; record `9b340bf5…`.
9. `MAIN -I -B .ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py --olmo-s1-edit <exact path> --out SCR/llama-build-{1,2}/out --full-out SCR/llama-build-{1,2}/tmp/full` → 0, 0; `cmp` of all five outputs against each other and the committed files → all equal.
10. The F-1 probes: `s1_olmo2_7b_check.py --edit /nonexistent/edit.json --scratch-tmp SCR/victim/tmp/precious …` → 2, folder deleted; with the real edit and a non-empty `SCR/victim2/tmp/precious` → 2, folder deleted; `victim3` → 2, deleted; `victim4` with `--keep` → 2, kept.
11. `SCI -I -B SCR/guard_probe.py SCR/wsf-copy SCR` → 0 (28 probes; 2 unexpected = F-2). A second run into `SCR/gp2` → 1 (`FileExistsError`: my probe needs a fresh folder; not a finding).
12. `SCI -I -B SCR/mutate_rv22_verify.py SCR/wsf-copy SCR` → 0 (baseline 35 passed; 8 killed, 3 survivors).
13. CLI guard probes of the build script with `--repo SCR/fakeD` → 2 (refused by name, nothing written); `--full-out /Users/nobody/full` → 2; the default `--out` → 2.
14. Read-only git commands in WS: `git status --short`, `git diff --stat`, `git log --oneline -1` → 0; no other git command.
15. `date -u` → 17:48:14, 18:06:19 UTC.
16. After this report: `rm -rf SCR/wsf-copy SCR/fake* SCR/gp2 SCR/pt-* SCR/mut-* SCR/olmo-check-tmp SCR/llama-build-* SCR/victim* SCR/hardlink-manifest.json SCR/link-to-*` (the heavy copy and the fake layouts; the `_out.txt` and record files stay as evidence).

## 9. Acceptance criteria (the builder's list)

| criterion | my result | basis |
|---|---|---|
| the fingerprint script and its 1B test | **passed** (plus a real differing pair, exit 1) | section 3 |
| the S1 decision for OLMo (M) | **passed** (record `9b340bf5…` reproduced); the tool has F-1 | section 4, F-1 |
| the Llama S1 set: MANIFEST, tests, accept/refuse, same bytes | **passed**; guards 26 of 28 as described (F-2, F-3 minor) | section 5 |
| the RV2-2 test kills its mutants | **passed** (R4-a, R4-b killed by the new file alone; V9, V11 too); F-4 is a separate gap | section 6 |
| no tracked file changed | **passed** | `git diff --stat` empty; six untracked paths; no `__pycache__` outside `tmp/` (M) |
| no text printed or stored | **passed** | section 7 |

## 10. Jobs for the lead

1. **Before any commit of track F:** fix F-1 in `scripts/scale78b/s1_olmo2_7b_check.py` (`created = not scratch.exists()` before `check()`; delete in `finally` only if `created`), add the test (a pre-existing non-empty `--scratch-tmp` is refused and survives), re-run `MAIN -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_s1_olmo2_7b_check.py` (about 15 s). The verdict record `9b340bf5…` does not change.
2. Decide F-2 and F-3 (README sentences, no rebuild; or code, which rebuilds the Llama set and changes the arm hash) and F-4 (a new test file; optional before N).
3. Then the builder's jobs 1-5 stand (the commit by explicit paths; the `tmp/` copies; `commitments.py check`; the sealed tests in the main checkout; the fingerprint command per family; the kit's S1 edit hashes; the FOCUS line). The main checkout already holds `tmp/kt-prepared/prepared-kt-dolly-{olmo2,llama3}` with the same manifest hashes as WS's copies (M), so the sealed tests will not skip there.

## 11. Unresolved concerns

1. F-2/F-3 are the same design scope the lead accepted for the three sibling sealed folders; I did not re-open that decision, only measured that this script has it too.
2. Engine Y's `COMPLETE.json` format is unknown; the fingerprint script refuses on any missing field (safe) but would then need the lead's reading of why (I).
3. The builder's concern 2 (the sealed list recovered, not found) stands as stated; my independent recovery reproduced the pin, which is the strongest check available on this Mac. A copy from a backup release would make `list.source.kind` `given` and change the MANIFEST bytes (R the test `test_a_given_list_is_read_by_its_pin_and_recorded_as_given`: the edit bytes stay).
4. The committed noise tests perturb `gpu` only (F-4). At 7-8B the guard record is a live trigger; the gap should be closed before N's reading, in a new file.
