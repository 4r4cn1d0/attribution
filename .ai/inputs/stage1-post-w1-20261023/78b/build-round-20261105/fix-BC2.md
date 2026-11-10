# Fix report, round 2: tracks B and C (RV-1, RV-2, RV-3 of reverify-BC.md)

Started 2026-11-05 15:53 UTC; finished 16:16 UTC (M: `date -u` read right before each time written). Fix-round worker
for GI X (Fable). Merged tree ws-c, detached at `fb51421` (M `git rev-parse HEAD`, unchanged before and after):
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c`
My scratch (244 KB, M `du`): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/fix-BC2-scratch/`
Tags: M measured (command given), R read (path:line), E estimate (basis), I inference. Short sentences.

## 0. Status: DONE

RV-1 is closed by code (the three guards compare by directory identity) and by tests on a fake checkout layout
(case-variant, symlink, dotted and relative paths), and a mutant that removes the identity check dies on the
case-variant test in each script (M). The three sets are rebuilt into empty `out/` folders with the last round's
commands; stage 1's d = 6-10 parity holds byte for byte; every embedded script SHA-256 equals the script's bytes; the
independent integrity reader passes 419 checks (M). RV-2's eight gap tests are in place and each kills its mutant by
its own test (M). RV-3's sentence is fixed. All tests pass: 83 passed, 2 skipped (scipy) in one invocation under the
main venv; 33 passed under `.venv` (M). `git status --porcelain` in ws-c lists only new files (M). No git state
changed anywhere. No pod, spend, network, install, download, agent or message. Nothing written in the main checkout.
No forbidden folder or text file opened: the prepared sets were read by the frozen builder's `Inputs` and the id-only
views only; the unit folders by the frozen `gate_b_reading` path and, for one new test, their four metadata files
(COMPLETE.json, job.json, identity.json, assets.json; no eval output); every print was a count, a hash, a path or a
test name.

## 1. Files changed (all untracked files of ws-c; nothing tracked, nothing in the main checkout)

Hashed build scripts (RV-1; a byte change, so every arm hash changes; the diffs are in section 2):
- `.ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py`: now `1ca6cdb49d02bc2d336ec08f360ed5c34a2fabd702bc6fce6bf8b7a206b8e573` (was `227aed4f…`)
- `scripts/scale78b/build_r_draws_78b.py`: now `18f2fec801c7643dee3f2f0c651a29b41db29d68baeb5185962799ec0fcd9ffa` (was `5cd1036d…`)
- `scripts/scale78b/build_h1_llama3.py`: now `26f2f2a13c875364f333e0b0ad039505ac98ffee91ee85af00148356ba7f7df6` (was `504e9462…`)

Rebuilt outputs (the three `out/` folders removed, then rebuilt; 25 + 7 + 2 = 34 files):
- `.ai/inputs/scale-78b-sealed-llama3-20261105/out/` (24 edit files + `MANIFEST.json` `2a1db220…`)
- `.ai/inputs/scale-78b-r-draws-olmo2-20261105/out/` (6 edit files + `MANIFEST.json` `22858dbf…`)
- `.ai/inputs/scale-78b-length-rules-llama3-20261105/out/` (`edits/octile_0.json` `9a01637e…` + `MANIFEST.json` `24c1305a…`)

Tests (RV-1 and RV-2; 14 new tests, no hashed file):
- `.ai/inputs/scale-78b-sealed-llama3-20261105/tests/test_build_sealed_llama3.py` (+2 RV-1 tests; 17 tests; `import os`)
- `scripts/scale78b/tests/test_build_r_draws_78b.py` (+2 RV-1, +1 G1; 9 tests; `import os`)
- `scripts/scale78b/tests/test_build_h1_llama3.py` (+2 RV-1, +1 G3; 9 tests; `import os`)
- `scripts/scale78b/tests/test_noise_reading.py` (+5: C-D4b, R2, R3, R4, R5; 28 tests; `import hashlib`; a synthetic sealed-unit helper)
- `scripts/scale78b/tests/test_make_recipe_s78.py` (+1: C-D3b; 14 tests)

READMEs (not hashed): the three `README.md` (the new hashes with the two earlier builds as history, the identity guard,
the test counts; the sealed README's RV-3 sentence).

Not changed (M: `git status --porcelain` shows `??` entries only; `-uall` 54 files, 0 modified): any tracked file, any
engine file, any frozen script (BLD `80cb8944…` both copies before and after), any committed sealed file, `runkit/`,
`noise_reading.py` (`94b679ff…`), `make_recipe_s78.py` (`fcf01955…`), `g1_check_78b.py` (`251ddb32…`), the G1 record
(`8c3579e4…`; it embeds `noise_reading.py`'s hash, which did not change), the main checkout (its `git status` shows none
of my paths; M grep count 0).

## 2. RV-1: guard_out compares by identity (the three scripts)

- Defect (R reverify-BC.md:36): the guards compared `out.resolve()` with `(root / forbidden).resolve()` as strings. On
  this Mac (APFS, case-insensitive) `.ai/inputs/GATE-B-SEALED-20261008/out/new` is a folder inside SEAL with another
  string. I reproduced the premise on my scratch filesystem before editing (M, `.venv -I -B` probe): a case-variant
  spelling `exists()`, `resolve()` keeps the typed case, `os.path.samefile` is True, string equality False.
- Change (`fix-BC2-scratch/apply_guard_fix.py`, exact anchors each found once; the full `diff -u` against the saved
  originals in `fix-BC2-scratch/orig-scripts/` was printed; `import os` added to each script). In each `guard_out`, after
  the roots are built: `anchor` = the deepest existing ancestor of `out` (or `out` itself); then, per root and
  forbidden folder, the string refusal that existed stays (`out == target or target in out.parents`), and a second
  refusal fires when `target.exists()` and any of `(anchor, *anchor.parents)` is `os.path.samefile` with it. The
  non-empty refusal of the two wrappers stays; the H1 script's absent-or-empty rule stays with `s1.write_new_files`.
  The function docstrings say so. Message unchanged: `refusing to write under <forbidden>`.
- Why the deepest existing ancestor: `samefile` needs existing paths; `--out` is normally absent (absent-or-empty rule).
  Its deepest existing ancestor and that ancestor's parents all exist, so the identity walk is total. A forbidden
  folder that does not exist yet (another checkout's) is still covered by the string comparison.
- Probe (M, main venv, on a fake layout under my scratch, all three guards, removed afterwards): REFUSED for a
  case-variant path (deep, the folder itself, the anchor folder with `Gate-B-Anchors`, the stage-1 folder through
  `.ai/INPUTS`), a symlink into SEAL, a symlinked checkout root (as `--repo` and as part of `--out`), a dotted path,
  dotted + case, relative, relative dotted, relative case; PASS for a sibling with a shared prefix, an ordinary folder,
  a relative ordinary folder (15 cases × 3 guards, each as expected).
- Tests (two per test file, on a fake checkout layout under `tmp_path` with the forbidden folders' names; the real
  sealed folders are never an argument of the new tests):
  `test_the_guard_refuses_a_symlink_a_dotted_and_a_relative_path_into_a_sealed_folder` (a symlink into the sealed
  folder, a symlinked checkout root both as `--repo` and inside `--out`, three dotted spellings, three relative
  spellings with `monkeypatch.chdir`, the anchor and stage-1 folders; the sibling-prefix and ordinary controls pass;
  nothing written) and `test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder` (asserts the string differs
  and `samefile` holds, six case-variant spellings over the three forbidden folders, the CLI with `--repo fake` and a
  case-variant `--out`, for the sealed wrapper also `--olmo-parity-out`; refuses with the message, nothing read or
  written; `pytest.skip` on a case-sensitive filesystem). All pass (M, section 6).
- Mutants RV-1a/b/c (`mutate_fix2.py`: the identity block removed from each script, the string check left): KILLED ×3,
  each on `test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder` (DID NOT RAISE) plus that script's
  committed-`out/` hash test (the bytes changed) (M, `mutate_fix2_out.txt`).

## 3. The rebuild (addendum A3: empty `out/` folders, placement kept)

- Steps (M, ws-c root, PY = the main venv's python, `PYTHONDONTWRITEBYTECODE=1`, every command `-I -B`): `rm -rf` of the
  three `out/` folders (`ls` showed README, wrapper, tests only); `PY -I -B .ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py --olmo-parity-out <scratch>/rebuild-parity`
  → exit 0, 25 files, 19 parity files; `PY -I -B scripts/scale78b/build_r_draws_78b.py` → exit 0, 7 files;
  `PY -I -B scripts/scale78b/build_h1_llama3.py` → exit 0, 2 files. The same commands as fix-BC.md runs 7-8 and 10.
  Build time 2026-11-05 16:04:35 UTC (M: `stat` of the three MANIFESTs, UTC). Outputs kept: `rebuild_*_out.txt`.
- Parity for stage 1's d = 6-10 and SEAL's d = 1-5 and units: `cmp` byte-identical for 18 of 18 parity files (M);
  `PARITY.json` `byte_identical: True` ×13 sealed, and `byte_identical`, `equal_without_stage1_wrapper`,
  `remove_list_equal`, `stage1_wrapper_rederived` all True for d = 6-10 (M; the file is kept at
  `fix-BC2-scratch/rebuild-parity/PARITY.json`; the parity edit copies were deleted). The parity test
  `test_c_olmo_parity_reproduces_stage1_d6_to_d10` passes in every run (section 6). SEAL's R_d1-R_d3 reproduce as
  `f7d7eb86…`, `913b7360…`, `cd8d3328…` (M, the build's parity listing: Gate B's wave-0a arms).
- Embedded script hashes == the scripts' bytes in ws-c (M): the sealed MANIFEST's `builder.sha256` and the 24 edit files'
  `provenance.builder_sha256` are `1ca6cdb4…` (the build output prints it; the re-verifier's integrity reader, copied
  to `fix-BC2-scratch/integrity_copy.py` and run with `.venv -I -B` on ws-c, prints `wrapper hashes 1ca6cdb4 18f2fec8
  26f2f2a1` and **OK 419 FAILS 0**, `integrity_out.txt`). That reader checks, for all 24 + 6 + 1 edit files: SHA-256 ==
  the MANIFEST's, arm == `edit-<sha256>`, the embedded `builder_sha256` / `scale78b_wrapper.script_sha256` /
  `script_sha256` == the script's bytes, kind "safety-selection edit", `edit_kind` "remove", the right manifest,
  `rewrite`/`add` empty, counts, 600 sorted distinct rows, 75 per unit against the prepared set's dev groups, the
  selection family/draw and the seed 1100 + d, the MANIFEST record's seed/draw/family, Llama R_d1-5 == SEAL's lists
  with `same_rows_as` hashes, R_d6-10 == stage 1's, R_d11-16 == the OLMo d = 11-16 lists, 16 distinct draws, unit
  files == group members == SEAL's unit files, the r-draws reproduction flags, H1's stage-1 pin, and the G1 record's
  three embedded hashes. The committed-`out/` tests (`test_g_the_committed_out_folder_equals_a_fresh_build`,
  `test_the_committed_out_folder_equals_a_fresh_build`, `test_a_rerun_gives_the_same_bytes_and_the_committed_out_equals_a_fresh_build`)
  pass (M, section 6).
- The seal fields the noise reader checks: `test_the_edit_provenance_check_accepts_the_llama_sealed_sets_r_files_for_n`
  passes on the rebuilt files (R_d1-R_d3 for llama31-8b at 1101-1103; sha256 == MANIFEST's == arm; refused for the
  other families and at d ± 1; d = 4-16 pass; the 8 unit files and H1 are not R units). The re-verifier's synthetic
  sealed unit (copied to `synthetic_unit_copy.py`, run with the main venv) pushes the rebuilt R_d1-R_d3 through
  `read_unit`: ACCEPTED ×3 as llama31-8b R@1101/1102/1103 with the MANIFEST's arms; nine tampered copies REFUSED; the
  engine refuses a copy with an unknown row id and accepts the genuine R_d1 (600 removed, arm == MANIFEST's);
  `SUMMARY all expected: True` (M, `synthetic_unit_out.txt`).
- Text walk (the re-verifier's `textwalk.py`, copied, `.venv -I -B`): 36 JSON files, no string with a newline, longest
  string 415 characters at `/position_rule` (the engine's rule sentence) in the edit files, 229 / 199 / 242 in the
  MANIFESTs; no suspicious key except the G1 record's `sampled`/`answers_end`/share names (counts and shares; the
  record is unchanged) (M, `textwalk_out.txt`).
- H1's remove list: the build prints the same cut points (2-13, 13-23, 23-34, 34-51, 51-75, 75-106, 106-177,
  177-2064) and by-category counts as the last round's README (M); the parity test with stage 1's OLMo H1 passes.
- BLD unchanged: `80cb8944…` for both copies after every run (M `shasum`).

## 4. RV-2: the eight gap tests and their mutants

Harness `fix-BC2-scratch/mutate_fix2.py` (the re-verifier's `mutate_rv.py` with this round's mutants and an
"own test" check; output `mutate_fix2_out.txt`): a scratch root reaches ws-c's engine, research, tmp and committed
`.ai/inputs` folders by symlink; `scripts/scale78b/`, the Llama sealed folder, SEAL and the anchor folder are copied;
one mutant per run, the same pytest command on baseline and mutant; KILLED = exit non-zero, named failed tests, no
errors. Baselines (M): noise 28 passed (`.venv`), maker 14 passed (main venv), B 38 passed (main venv); exit 0 ×3.

| gap | test (file) | what it does | mutant (the re-verifier's replacement) | result (M) |
|---|---|---|---|---|
| C-D3b | `test_anchor_records_skips_an_incomplete_or_foreign_record` (maker) | six synthetic `anchors.sealed.json` under `tmp_path`: complete, `complete` false, missing, the string "true", another kind, a list; `anchor_records` returns the complete one only; `anchored_to` anchors through it and through none of the others | `anchor_records` keeps every dict | KILLED: 1 failed, its own test (assert) |
| C-D4b | `test_a_copied_unit_at_another_path_with_the_same_complete_json_refuses_as_a_duplicate` (noise) | Gate A a0-1101's four metadata files copied to another folder; listed with the same key as a0@1102, and as olmo2-7b a0@1101 beside olmo2-1b: each refuses "its COMPLETE.json SHA-256 is already read as olmo2-1b a0@1101" | the `seen` key is the path | KILLED: 1 failed, its own test (the copy is read and refuses on its sealed files, so the message differs) |
| R2 | `test_the_edit_provenance_check_refuses_a_rewrite_or_add_edit_and_a_wrong_kind` (noise) | SEAL's R_d1 passes for olmo2-7b@1101; with `edit_kind` "rewrite", "add", "" or None, another `kind`, the Llama manifest, selection family "unit"/"H" or draw 2 it does not | the `edit_kind` check dropped | KILLED: 1 failed, its own test (assert) |
| R3 | `test_an_r_unit_whose_edit_file_hashes_to_another_arm_refuses` (noise) | a synthetic sealed olmo2-1b R unit (metadata only; REC 1B's recipe; its COMPLETE.json lists the edit file it holds): SEAL's R_d1 bytes under their own arm pass `read_unit`; the unit holding SEAL's R_d2 file, or R_d1 with one row changed (the five fields intact, asserted), under R_d1's arm refuses "edit.json is missing or is not the arm's edit file" | `if not edit.is_file():` | KILLED: 1 failed, its own test (the row-changed unit is accepted: DID NOT RAISE path; reported as assert kind by the harness's line scan) |
| R4 | `test_an_environment_difference_on_a0_1102_alone_is_attributed_to_it_against_the_a0_1101_reference` (noise) | `read_unit` wrapped to change a0@1102's returned `fields["gpu"]` (files untouched); the real `environment_differs` then records `["gpu"]` on a0@1102 and `[]` on the five others; trigger and fallback fire; σ_F 2.16 | reference = a0@1102 | KILLED: 1 failed, its own test (the attribution inverts) |
| R5 | `test_hex64_accepts_sixty_four_lower_case_hex_digits_only` (noise) | lower-case hex of length 64 accepted; upper, mixed, 63, 65, a non-hex character, an `edit-` prefix, bytes, None, int, list refused; the pins are lower-case; an upper-case engine id in the inputs refuses on the engine check | `[0-9a-fA-F]{64}` | KILLED: 1 failed, its own test (assert) |
| G1 | `test_the_r_draws_guard_refuses_a_folder_that_exists_and_is_not_empty` (r-draws) | a folder holding one file refuses through `guard_out` (with and without `repo`) and through `main(["--out", …])`, which leaves the folder as it was; an empty and an absent folder pass | the non-empty refusal removed | KILLED: 2 failed: its own test (DID NOT RAISE) and the committed-out hash test |
| G3 | `test_the_h1_cli_refuses_an_output_under_the_given_repos_own_sealed_folders` (H1) | a fake checkout with the three forbidden folders; `main(["--repo", other, "--out", other/<forbidden>/out/new])` returns 2 with that folder's name on stderr and writes nothing, for each of the three | `guard_out(out, None)` | KILLED: 3 failed: its own test, the case-variant test (it also goes through `main` with `--repo`), the hash test |

`ALL MUTANTS KILLED BY THEIR OWN TEST: True` (the harness's last line, M). The noise tests C-D4b and R4 need the
wave-0a and Gate A units on this Mac (`needs_wave0a`); R2, R3 and R5 run anywhere (SEAL's committed files, a synthetic
unit, pure functions).

## 5. RV-3: the README sentence

`.ai/inputs/scale-78b-sealed-llama3-20261105/README.md`, test (d), now reads: "the engine's `parse_edit` accepts each
Llama file against the Llama set and refuses it against the OLMo set, on id-only `engine_stub()` views of both sets
(never the engine's `load_prepared`, which reads prompt text)" (M grep: `load_prepared` appears in that sentence only).
Not hashed: no rebuild for this. The other README edits: the new hashes (section 7), the two earlier builds as labelled
history ("rebuilt twice … each removed first"), the identity guard, the test counts 17 / 9 / 9, "first built … this
build 16:04 UTC" in the titles (the build time is the MANIFESTs' mtime, M `stat`). Diffs printed against the saved
originals; longest line 125 / 122 / 124 characters (M).

## 6. Test runs (M; ws-c root; `PYTHONDONTWRITEBYTECODE=1 <python> -B -m pytest -q -p no:cacheprovider --basetemp=<my scratch>`; outputs kept as `pytest_*_out.txt`)

| run | python | result |
|---|---|---|
| B and C together in ONE invocation: `.ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests -rs` | main venv | **83 passed, 2 skipped (scipy) in 4.44s** (the summary line; the exit code was not captured through the pipe in this one run) |
| noise reader + G1: `test_noise_reading.py test_g1_check_78b.py -rs` | `.venv` | **33 passed in 4.17s**, exit 0 (the two scipy tests ran) |
| B alone: the sealed tests + `test_build_r_draws_78b.py` + `test_build_h1_llama3.py` | main venv | 38 passed in 0.89s, exit 0 |
| C alone: `test_make_recipe_s78.py test_noise_reading.py test_g1_check_78b.py -rs` | main venv | 45 passed, 2 skipped in 3.48s, exit 0 |

Counts: B 38 (was 30) + maker 14 (was 13) + noise 28 (was 23; 2 scipy skips under the main venv) + G1 5 = 85 = 83 + 2
skipped. The harness's baselines agree (28 / 14 / 38). After every run: no `__pycache__`, no `.pytest_cache` in ws-c
(M `find` → 0); the pytest basetemps were under my scratch and are deleted.

## 7. The new hashes (for the lead's pins; M `shasum -a 256` in ws-c)

- Llama sealed set `.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json`: **2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c** (the kit's MANIFEST pin, addendum A13)
- OLMo R_d11-R_d16 `.ai/inputs/scale-78b-r-draws-olmo2-20261105/out/MANIFEST.json`: **22858dbfe40e83f970bc8a96c51684b80b9cc494945a904ee6bc6e03ea1acb28**
- Llama H1 `.ai/inputs/scale-78b-length-rules-llama3-20261105/out/MANIFEST.json`: **24c1305ab59e979feb8eb88dc3977ada132cad082f41449d4acde20f2bcdda61**; `out/edits/octile_0.json` 9a01637ec63dc38f6e4dec646a0bc4b8c00c36521fa8831fe4fb87e8df3a1c5f
- N's Llama R arms (the MANIFEST record's sha256 == the bytes on disk, arm == `edit-<sha256>`, seed / draw / family
  1101 / 1 / R, 1102 / 2 / R, 1103 / 3 / R; M):
  - `.ai/inputs/scale-78b-sealed-llama3-20261105/out/edits/R_d1.json` — 5cdedf22c1002ef1c6d0322d44c253ef57580ddb1dda85e8119a8b3842dc29b4 — **edit-5cdedf22c1002ef1c6d0322d44c253ef57580ddb1dda85e8119a8b3842dc29b4**
  - `.ai/inputs/scale-78b-sealed-llama3-20261105/out/edits/R_d2.json` — 8f9f3cd5027d9268b28e3cf4189987a820b26a6d6d77fbe83ea0ad145944bb95 — **edit-8f9f3cd5027d9268b28e3cf4189987a820b26a6d6d77fbe83ea0ad145944bb95**
  - `.ai/inputs/scale-78b-sealed-llama3-20261105/out/edits/R_d3.json` — edbc111b2ff3a446ae195a79f0e5965c9a82fa744266d57c9c15e4c4c775dd2e — **edit-edbc111b2ff3a446ae195a79f0e5965c9a82fa744266d57c9c15e4c4c775dd2e**
  (the other 21 Llama arms and the 6 OLMo arms are in the MANIFESTs and in `rebuild_sealed_out.txt` / `rebuild_rdraws_out.txt`)
- Scripts: `build_sealed_llama3.py` 1ca6cdb49d02bc2d336ec08f360ed5c34a2fabd702bc6fce6bf8b7a206b8e573; `build_r_draws_78b.py`
  18f2fec801c7643dee3f2f0c651a29b41db29d68baeb5185962799ec0fcd9ffa; `build_h1_llama3.py` 26f2f2a13c875364f333e0b0ad039505ac98ffee91ee85af00148356ba7f7df6.
- Unchanged: `noise_reading.py` 94b679ff…, `make_recipe_s78.py` fcf01955…, `g1_check_78b.py` 251ddb32…, the G1 record
  8c3579e4…, BLD 80cb8944… (both copies), the engine identity 472fc7f6… (printed by each build).
- Tests: `test_build_sealed_llama3.py` 90362053…, `test_build_r_draws_78b.py` e7398272…, `test_build_h1_llama3.py` eb81b411…,
  `test_noise_reading.py` 6f301524…, `test_make_recipe_s78.py` c17d37bf….
- Superseded (history only, in the READMEs): MANIFESTs ba524373… / 189275c0… / 29347da2…, `octile_0.json` 9204121a…,
  scripts 227aed4f… / 5cd1036d… / 504e9462…, arms edit-091de345… / edit-59fc31df… / edit-c875e730… (fix-BC.md §2.4).

## 8. Commands run (every one; ws-c root or my scratch as stated; exit 0 unless stated; all foreground, none over 2 min; the mutation harness about 90 s)

1. `date -u` ×4 (15:53, 15:53, 16:14, 16:16 UTC); `mkdir` scratch; `git -C ws-c status --porcelain [-uall]`, `rev-parse HEAD` (before, during and after: six `??` paths, 54 files, 0 modified, `fb51421`); `find __pycache__ / .pytest_cache` → 0 (×3); `ls` of the reports folder and the sealed folders; `shasum -a 256` of the 3 scripts, 3 MANIFESTs, 3 track-C scripts (before).
2. Reads (Read/sed/grep/cat/cat -n): the addendum, reverify-BC.md, fix-BC.md, build-B.md, verify-B.md; the three build scripts (headers, `guard_out`, `main`), the five test files, both conftests, `__init__.py`, the three READMEs; `noise_reading.py` (pins, `hex64`, `r_edit_matches`, `read_unit`, `environment_differs`, `family_reading`), `make_recipe_s78.py` (pins, `anchor_records`, `anchored_to`); `family_probe_reading.sealed`, `gate_b_reading.compared_fields`, `EDIT_FILE`, `read_json`; the re-verifier's `mutate_rv.py`, `integrity.py`, `synthetic_unit.py`, `textwalk.py` and their outputs.
3. `.venv -I -B` key-structure walk of one R unit's and one a0 unit's COMPLETE.json / job.json / identity.json / assets.json (keys, types, hashes, short labels only); `ls` of the two unit folders; `ls` of `tmp/kt-prepared`.
4. `.venv -I -B` filesystem probe in my scratch (case-insensitive: True; resolve keeps case: True; samefile True; string equal False); folder removed.
5. `cp` of the three scripts and READMEs to `fix-BC2-scratch/orig-scripts/`; `.venv -I -B apply_guard_fix.py <ws-c>` → 0; `diff -u` ×3 (section 2).
6. main venv `-B` guard probe on a fake layout (15 cases × 3 guards; section 2); folder removed.
7. ws-c: `rm -rf` of the three `out/`; `ls`; main venv `-I -B` × the three builds (section 3) → 0, 0, 0; `shasum` of the MANIFESTs and `octile_0.json`; `find -type f | wc -l` → 34; `find __pycache__` → 0.
8. main venv `-B` synthetic-unit probe (REC 1B recipe; genuine accepted, other-arm and row-changed refused); folder removed.
9. `cat` of the build outputs; `cmp` ×18 parity files against SEAL and stage 1 → 18 identical; `.venv -I -B` PARITY.json flags; `TZ=UTC stat` of the MANIFESTs (16:04:35 UTC).
10. `cp integrity.py` → `integrity_copy.py`; `.venv -I -B integrity_copy.py <ws-c>` → OK 419 FAILS 0 (`integrity_out.txt`).
11. `.venv -I -B append_tests.py <ws-c>` → 0 (five files; the line counts printed).
12. pytest ×4 (section 6) and one `-v -k` listing of the new tests (16 selected incl. two pre-existing name matches, all passed).
13. `date -u`; `.venv -I -B update_readmes.py <ws-c>` → 0; `diff -u` ×3; `grep` of the superseded hashes and `load_prepared` (history lines and the RV-3 sentence only); `.venv -I -B` re-wrap of two passages; `awk` longest line ×3.
14. `.venv -I -B mutate_fix2.py <ws-c>` → 0: 3 baselines pass, 11 mutants KILLED, all by their own test (`mutate_fix2_out.txt`).
15. `shasum -a 256` of 18 files (section 7); `.venv -I -B` R_d1-R_d3 path / sha256 / arm / record check.
16. `cp` of `synthetic_unit.py`, `textwalk.py` to my scratch; main venv `-B synthetic_unit_copy.py <ws-c> <scratch>/synth-units` → 0, SUMMARY all expected True, folder removed by the script; `.venv -I -B textwalk_copy.py <ws-c>` → 0, 36 files.
17. `rm -rf` of the pytest basetemps, the harness roots, the parity edit copies; `ls`; `du` → 244 KB; final `git status`, `rev-parse`, `find`; `grep` of the main checkout's `git status` for my paths → 0 (read only).

Not run: any pod, network, install, download, agent, message; anything in the main checkout (reads by absolute path
only); any git state change; the engine suite (the engine is untouched: ws-c's `git status` shows no tracked change;
round 1's 837 passed stands).

## 9. Acceptance criteria

| criterion | result | evidence |
|---|---|---|
| RV-1 closed: identity comparison in all three `guard_out`, every existing refusal kept | passed | section 2 diffs (the string check and the non-empty check stay); the existing guard tests still pass (section 6) |
| RV-1 tested with real case-variant, symlink, dotted and relative paths on a fake layout, never the real sealed folders | passed | two tests per file (section 2); the probe (M); mutants RV-1a/b/c KILLED on the case-variant test |
| the three sets rebuilt into EMPTY `out/` with the last round's commands | passed | section 3 (rm, then the three CLIs, exit 0 ×3; 34 files) |
| the stage-1 d = 6-10 byte-parity test still passes | passed | `cmp` 18/18; PARITY.json flags; `test_c_olmo_parity_reproduces_stage1_d6_to_d10` in every run |
| every embedded script SHA-256 equals the script's bytes in ws-c | passed | integrity 419/0 (`wrapper hashes 1ca6cdb4 18f2fec8 26f2f2a1`); the three committed-out tests |
| membership and the seal fields the noise reader checks | passed | integrity 419/0; `test_the_edit_provenance_check_accepts_the_llama_sealed_sets_r_files_for_n`; the synthetic unit ACCEPTED ×3 |
| RV-2: eight gap tests, each fails on a mutant that removes the check (shown, M) | passed | section 4, `mutate_fix2_out.txt`: 8 of 8 KILLED by their own test |
| RV-3 fixed | passed | section 5 |
| B's and C's tests together in one invocation (main venv); noise + G1 under `.venv`; counts reported | passed | 83 passed, 2 skipped; 33 passed (section 6) |
| `git -C ws-c status --porcelain` lists only new files | passed | six `??` paths, 54 files, 0 modified (M, before and after) |
| MANIFEST SHA-256 of each folder and the Llama R_d1-R_d3 path / SHA-256 / arm returned | passed | section 7 |
| nothing prints or stores text | passed | the text walk (36 files); my scripts print hashes, counts, paths, verdicts and test names |
| the engine suite | not tested | not asked; the engine is untouched |

## 10. Jobs for the lead

1. **Merge from ws-c by explicit paths** (54 new files, `git status --porcelain -uall`): the three
   `.ai/inputs/scale-78b-*/` folders (script, `out/`, README, the sealed set's tests), the two G1 records,
   `scripts/scale78b/`. Commit each hashed script with its `out/` (the edit files embed the scripts' SHA-256; frozen
   from the commit on, addendum A3).
2. **In the main checkout after the merge:** `PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests`
   (expect 83 passed, 2 skipped); `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_noise_reading.py scripts/scale78b/tests/test_g1_check_78b.py`
   (expect 33 passed); `scripts/stage1/commitments.py check`; the engine identity re-check (`472fc7f6…`; nothing here changes it).
3. **Pins and records.** The kit's Llama MANIFEST pin (A13): `2a1db220…`. N's Llama R arms for the inputs file:
   R_d1 `edit-5cdedf22…`, R_d2 `edit-8f9f3cd5…`, R_d3 `edit-edbc111b…` (section 7; `read_unit` binds each unit to the
   arm the inputs name, reverify-BC.md §6). If FOCUS, Part 1 or any record cites the fix-round values
   (`ba524373…` / `189275c0…` / `29347da2…`, `edit-091de345…` / `edit-59fc31df…` / `edit-c875e730…`), replace them;
   reverify-BC.md §5 and §12 cite them (historical). The G1 record `8c3579e4…` and `noise_reading.py` `94b679ff…` are
   unchanged.
4. **Re-verify** (optional): `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -B <scratch>/fix-BC2-scratch/mutate_fix2.py <ws-c>`
   (about 90 s; builds and removes its own scratch root) and `.venv/bin/python -I -B <scratch>/fix-BC2-scratch/integrity_copy.py <ws-c>`.
5. Optional: the full engine suite after the merge (round 1's command, about 80 s; the engine is untouched).
6. Delete `reports/fix-BC2-scratch/` (244 KB) once read, with `fix-BC-scratch/` and `reverify-BC-scratch/`.

## 11. Unresolved concerns

1. **Frozen-on-commit** (every round's concern): any further byte change to the three scripts needs another rebuild
   into empty `out/`; after the commit it is impossible without breaking the committed provenance. The three scripts
   are now what the brief asked for; I see no further change pending.
2. **The identity check's scope.** It covers a forbidden folder that exists, through the deepest existing ancestor of
   `--out`. A forbidden folder that does not exist yet (a fresh `--repo` without SEAL) is covered by the string
   comparison only, which is the only comparison possible for a path with no inode. On a case-sensitive filesystem the
   case-variant tests skip (stated in the test); the symlink, dotted and relative tests run everywhere.
3. **The duplicate-copy test (C-D4b) copies four metadata files, not the whole unit.** With the fix the duplicate
   refusal fires before the copy is read, so its completeness does not matter; with the path-keyed mutant the copy is
   read and refuses on its missing sealed files, a different message, which kills the mutant. A full copy would refuse
   on the seed instead (I from R `read_unit`); I did not copy eval outputs (text) to show it.
4. **The edit.json-hash test (R3) uses a synthetic unit**, because the frozen `sealed()` verifies every listed file, so a
   real unit with a swapped edit.json refuses one step earlier. The synthetic unit is self-consistent and passes
   `read_unit` with the genuine file; the re-verifier's own section 6 used the same construction.
5. **The B+C run's exit code was not captured** (zsh's `pipestatus` through `tee`); the summary line `83 passed, 2
   skipped` and the harness's three baselines (exit 0) and the B-alone / C-alone / `.venv` runs (exit 0 each) are the
   evidence.
6. **The "built" time in the README titles** is the MANIFESTs' mtime (16:04 UTC, M `stat`), not a build-time field (the
   MANIFESTs hold none by design).
7. **Byte parity for d = 6-10 still depends on the environment** (Python 3.11.15, numpy 2.2.6); it held here (M).
8. **The main checkout's `git status`** shows the lead's own modified and untracked files; none of my paths (M, grep
   count 0). Every write of mine went to ws-c or my scratch.
