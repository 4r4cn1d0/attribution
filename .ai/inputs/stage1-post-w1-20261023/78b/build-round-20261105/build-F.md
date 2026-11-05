# Build round 3, track F: the fingerprint check (T6b), the S1 add edits per family, the RV2-2 test

Started 2026-11-05 16:46 UTC; this version written 2026-11-05 17:43 UTC (`date -u`: 17:43:55). Worker: self-identified
Fable 5.1 (the launcher's routing evidence governs). Status: DONE.
Worktree (WS): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-f`, base 953f520.
Scratch (SCR): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/build-F-scratch/`.
Tags: M measured (command given), R read (path:line), E estimate (basis), I inference. No text was printed or stored in
the repository; the one text-bearing output (the Llama S1 edit) is under the worktree's git-ignored `tmp/`, named by hash.

## 0. Summary (plain)
- T6b: `scripts/scale78b/fingerprint_compare.py` compares q and e1 adapter AND optimizer fingerprints (four values) of a
  retrain unit with a reference unit's, from each unit's `COMPLETE.json` (cross-checked against `states/<c>/state.json`
  when present), prints equal/differs per fingerprint with the hashes, exit 0/1/2. On the 1B pair (Gate B's wave-0b
  a0@1101 retrain against the Gate A a0-1101 unit): 4 of 4 equal (M). 10 tests, tampered copies included.
- S1, OLMo-2-7B: stage 1's committed `add_s1.json` (`904a0cf1…`) IS OLMo-2-7B's S1 edit as it stands (M, three checks,
  `scripts/scale78b/s1_olmo2_7b_check.py`); nothing built for OLMo.
- S1, Llama-3.1-8B: built in the new sealed folder `.ai/inputs/scale-78b-s1-llama3-20261105/` by REQ-7's frozen writer
  (imported unchanged, pinned) on the Llama manifest: edit `6942699398ade7f7ddb6f5b47b06e8b253de6ff9bbd142b8138acc061468dd0a`
  (arm `edit-69426993…`, 48 add rows, 3072-token limit of the Llama main config), MANIFEST `a3986274…`. The edit holds
  text and lives at `tmp/scale-78b-s1-llama3-20261105/edits/add_s1.json` (git-ignored), as stage 1's rule requires.
  parse_edit accepts it on the Llama set and refuses it on the OLMo set; a re-run gives the same bytes. 17 tests.
- The sealed list `s1.json` is not on this Mac by name; it was recovered byte for byte (SHA-256 = the pin `389c20ad…`)
  from the committed OLMo S1 edit and the committed record's id map (M). The lead should confirm this route (§7).
- RV2-2: new test file `scripts/scale78b/tests/test_noise_reading_rv2_2.py` (7 tests); the two surviving mutants
  (reference a0@1103, reference R@1101) are killed by it (M), plus two more mutants.
- No tracked file changed (M: `git diff --stat` empty; `git status` lists new paths only). No git state changed.

## 1. Files added (all new paths; SHA-256 in `SCR/final_file_list.txt`)
Under `scripts/scale78b/`:
- `fingerprint_compare.py` (`b5bcb212…`): T6b.
- `s1_olmo2_7b_check.py` (`81fef90f…`): the OLMo-2-7B S1 decision, measured; text-free record with `--out`.
- `tests/test_fingerprint_compare.py` (`9ff4bd7a…`): 10 tests.
- `tests/test_noise_reading_rv2_2.py` (`f588b5df…`): 7 tests (RV2-2).
- `tests/test_s1_olmo2_7b_check.py` (`327aeaf2…`): 7 tests.
Under `.ai/inputs/scale-78b-s1-llama3-20261105/` (the sealed folder):
- `build_s1_llama3.py` (`a2b0a66c4e3f9f044ad5e2090cd58af195bcdfac3f372822eb1c14805495f5a3`; frozen from its commit).
- `README.md` (`258a6370…`).
- `out/MANIFEST.json` (`a398627455a96356f590b884ea5acaeae4bedb60a2e44b2bc27a8008b83713e0`), `out/add_edit_record.json`
  (`1023b4e6…`), `out/write_add_edit_llama3.settings.json` (`36a39481…`).
- `tests/conftest.py`, `tests/test_build_s1_llama3.py` (`d87b6bb3…`): 17 tests.
Git-ignored, in WS `tmp/` (text; not for the repository): `tmp/scale-78b-s1-llama3-20261105/edits/add_s1.json`
(`69426993…`), `tmp/scale-78b-s1-llama3-20261105/list/s1.json` (`389c20ad…`); `tmp/kt-prepared/prepared-kt-dolly-{olmo2,llama3}/`
(copies of manifest.json, manifest.sha256, prepare_receipt.json, engine/train_rows.jsonl, engine/groups.json only; no
banks/, hidden/, selector/, auditor/, query_rows).
Not touched: `scripts/stage1/**`, `experiments/**`, `runkit/**`, every committed sealed folder, the main checkout.

## 2. Alternatives and why chosen
1. **Fingerprint source.** Chosen: `COMPLETE.json` `checkpoints.<q|e1>.{adapter,optimizer}_fingerprint` (R:
   `experiments/safety_selection/runner.py:500-504`), the record the frozen Gate B reading used (R:
   `scripts/gate_b_reading.py:1217-1221`), cross-checked against `states/<c>/state.json` when the light pull left it (a
   unit whose two records disagree refuses). Rejected: `compare_c1.py`'s whole-unit file digest (16 files; it needs the
   evaluation files and steps.jsonl, which a train-only retrain to q and e1 does not all have, and ruling 10 names the
   four fingerprints only). Rejected: adapter fingerprints alone (the frozen reading's C-7 form): ruling 10 names
   adapter AND optimizer (R: lead-rulings-part1-20261105.md:132-143).
2. **The 1B test pair.** The task names Gate B's a0@1101 retrain and "the record that showed 16 of 16 files equal".
   Those are two records: the 16-of-16 is the X→Y certificate C1 on an R_1101 unit under `tmp/stage1-olmo/` (a folder
   this worker may not open; R: `.ai/inputs/stage1-post-w1-20261023/block-a/certificate_xy.json`, FOCUS:139), the a0@1101
   retrain is wave 0b's (FOCUS:199, "fingerprint trigger false"). Chosen: the a0@1101 pair, which is on this Mac outside
   the forbidden folders (`tmp/gate-b-olmo/retrieved/w0b-2/…/1101-a0-e1-a1` against
   `tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/…/1101-a0-e1-a1`). The test pins the frozen reading's C-7 adapter
   values and FOCUS's `d154f23f…` / the Gate A pin `8f0fa83a…` as COMPLETE.json prefixes.
3. **S1 for Llama: where the code lives.** Chosen: the build script in its own sealed folder with its tests (the pattern
   of `.ai/inputs/scale-78b-sealed-llama3-20261105/`, addendum A3), REQ-7 imported unchanged and pinned (four files and
   the settings), a settings document derived from REQ-7's committed one with exactly two pins re-bound and the
   derivation recorded. Rejected: a copy of `write_add_edit.py` with Llama constants (two writers to keep equal);
   `--settings` on REQ-7's CLI (its `load_settings` pins the committed settings' hash, so a Llama settings file is
   refused there; R: `write_add_edit.py:40, 196`).
4. **The sealed list.** `s1.json` is absent from this Mac by name (M: `find` over the allowed `tmp/` folders, none;
   `.ai/` none). Chosen: recover it from the committed OLMo S1 edit (bytes pinned `904a0cf1…`, read through the engine's
   `parse_edit`) and the committed record's add_id→list_id map, in the writer's own form (R: `build_s_pool.py:373-378`);
   accept only if the bytes hash to the sealed pin `389c20ad…` (M: they do). REQ-7's `read_list` then reads it by the
   pin, so the frozen path is untouched. `--list PATH:SHA256` takes the real file when the lead has it. Rejected: stop
   and wait for the lead's copy (the recovered bytes are the sealed bytes by SHA-256, which is the stronger check).
5. **Where the Llama edit is stored.** Chosen: under `tmp/` (git-ignored), named by hash in the MANIFEST, as stage 1
   stored every text-bearing edit (R: `scripts/stage1/README.md:13, 65`; REQ-7's `full_out_ok` refuses any other place).
   The committed folder holds the script, the MANIFEST, REQ-7's text-free record, the settings and the tests. The lead
   may decide otherwise (§7 item 1).
6. **The recipe for the Llama edit's token limit.** Chosen: the Llama main config `74758af1…` (add arms run under the
   family's main config, R: Part 1 §10 "With block B, under the family's main config"; S_78 does not exist yet and
   differs only in attribution fields, R: `make_recipe_s78.py:7-11`, so it shares `max_train_tokens` 3072).
7. **OLMo decision.** Chosen: a measurement script with a text-free record and a test, not a sentence in this report:
   (1) parse_edit on the family manifest, (2) every row's token counts under the 7B main recipe's limit, (3) the frozen
   writer reproducing the committed bytes. The first run of (3) gave `1760fa53…` ≠ `904a0cf1…`: stage 1 built the add
   edit in one run with the combined edits R_d2+s1, R_d3+s1, R_d4+s1, and the shared provenance block names those three
   remove edits (R: the committed record's `provenance.inputs.remove_R_d2..4`; M: the committed edit's provenance has
   them). With SEAL's R_d2, R_d3, R_d4 passed as `--combine-with` inputs (their hashes equal the record's, M), the frozen
   writer gives `904a0cf1…` exactly (M). The check passes them by reading the record's inputs.
8. **RV2-2.** Chosen: a new file that imports the committed test file's helpers; the committed file is tracked and stays
   byte-identical. The full dict with a0@1101 perturbed (the re-verifier's measured form) plus one parametrized test per
   other unit and a no-perturbation case.
9. **MANIFEST independence from the operator's folder.** After the first two trial builds differed only in the recorded
   `--full-out` path, the MANIFEST now names the text files by their place under `--full-out` and by hash, with the
   default folder recorded; so "a re-run gives the same bytes" holds for every output, and the committed `out/` equals a
   fresh build into any scratch folder (tested).

## 3. Commands run (every one that produced evidence; all foreground; exit status; the longest about 33 s)
Environment variables for every pytest and build run: `PYTHONDONTWRITEBYTECODE=1`; for the main venv also
`HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` (no network; the engine's `load_tokenizer` is offline by itself, R: `loaders.py:89-98`).
MAIN = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python`; SCI = `/Users/spiderishi/Coding/attribution/.venv/bin/python`. Run from WS.
1. `SCI -I -B scripts/scale78b/fingerprint_compare.py --retrain <w0b-2 1101-a0-e1-a1> --reference <Gate A 1101-a0-e1-a1> --expect-adapter q=322d737a --expect-adapter e1=aad79060 --out SCR/fingerprints-1b-pair.json` → exit 0 (the record was written; `SCR/fingerprint_cli_1b_out.txt`).
2. `SCI -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_fingerprint_compare.py` → first run 1 failed (a test-side line-length assertion on the record path; fixed twice), final: 10 passed, exit 0 (`SCR/pytest_fingerprint_out.txt`).
3. `SCI -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_noise_reading_rv2_2.py` → 7 passed, exit 0 (`SCR/pytest_rv2_2_out.txt`).
4. `SCI -I -B SCR/mutate_rv2_2.py WS` → baseline 35 passed; 4 mutants KILLED; exit 0 (`SCR/mutate_rv2_2_out.txt`).
5. `MAIN -I -B .ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py --olmo-s1-edit <main checkout a-3 unit edit.json> --out SCR/s1-trial/out --full-out tmp/scale-78b-s1-llama3-trial` → exit 0; again into `-trial2` → exit 0; edit and record bytes equal, MANIFEST differed in the recorded folder (then fixed; §2 item 9) (`SCR/s1_trial_out.txt`, `s1_trial2_out.txt`; the trial folders removed).
6. `MAIN -I -B scripts/scale78b/s1_olmo2_7b_check.py --edit <a-3 unit edit.json> --out SCR/s1_olmo2_7b_check_record.json` → first run exit 1 (check 3 false, `1760fa53…`: the combine inputs; §2 item 7); after the fix exit 0, verdict equal (`SCR/s1_olmo2_7b_check_out.txt`, record `9b340bf5…`).
7. `MAIN -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-s1-llama3-20261105/tests` → 15 passed, 1 skipped, 1 failed (a test-side regex; the test rewritten), then 16 passed, 1 skipped (no committed out yet) (`SCR/pytest_s1_llama3_out.txt`); after the real build 17 passed, exit 0 (`SCR/pytest_s1_llama3_final_out.txt`).
8. `MAIN -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_s1_olmo2_7b_check.py` → 7 passed, exit 0 (`SCR/pytest_s1_olmo_check_out.txt`).
9. The real build: `MAIN -I -B .ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py --olmo-s1-edit "/Users/spiderishi/Coding/attribution/tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10-e1-a1/edit.json"` (defaults: `--out` the folder's `out/`, `--full-out` WS `tmp/scale-78b-s1-llama3-20261105`) → exit 0, 17:37 UTC (`SCR/s1_llama3_build_out.txt`).
10. `MAIN -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_fingerprint_compare.py scripts/scale78b/tests/test_noise_reading_rv2_2.py scripts/scale78b/tests/test_s1_olmo2_7b_check.py` → 24 passed, exit 0 (`SCR/pytest_new_tests_main_venv_out.txt`).
11. `SCI -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests .ai/inputs/scale-78b-s1-llama3-20261105/tests` → first 87 passed, 4 errors (no transformers in .venv for the OLMo codec; `importorskip` added to the two codec-using test files), then 84 passed, 2 skipped, exit 0 (`SCR/pytest_scale78b_all_venv_out.txt`).
12. `MAIN -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests .ai/inputs/scale-78b-s1-llama3-20261105/tests .ai/inputs/scale-78b-sealed-llama3-20261105/tests` → 124 passed, 2 skipped, exit 0 (`SCR/pytest_all_main_venv_out.txt`).
13. `git status --short; git diff --stat` in WS → six new paths, no tracked diff (`SCR/git_status_short.txt`, `SCR/final_file_list.txt`).
Reads before the code (hashes and counts only): `shasum` of the REQ-7 files, SEAL's R_d2-4, the committed add-s1 record (`311957a4…`), the a-3 unit's `edit.json` (`904a0cf1…`); JSON key/hash prints of the side units' and the 1B pair's `COMPLETE.json`; the configs' `config_sha256` and `max_train_tokens`; the two prepared manifests' `data_config.tokenizer`.

## 4. Evidence paths
- `SCR/fingerprint_cli_1b_out.txt`, `SCR/fingerprints-1b-pair.json` (record `703ee6e0…`): the 1B pair, 4 of 4 equal; code identities differ (Gate A engine `55253874…` vs engine X `472fc7f6…`), training identity and manifest equal, recipes differ (S vs B) by design.
- `SCR/pytest_fingerprint_out.txt` (10 passed), `SCR/pytest_rv2_2_out.txt` (7 passed), `SCR/mutate_rv2_2_out.txt` (4 mutants killed), `SCR/mutate_rv2_2.py`.
- `SCR/s1_olmo2_7b_check_out.txt`, `SCR/s1_olmo2_7b_check_record.json` (`9b340bf5…`): the OLMo decision.
- `SCR/s1_llama3_build_out.txt`: the real Llama build (hashes of the five outputs); `SCR/pytest_s1_llama3_final_out.txt` (17 passed).
- `SCR/pytest_new_tests_main_venv_out.txt` (24), `SCR/pytest_scale78b_all_venv_out.txt` (84 + 2 skipped), `SCR/pytest_all_main_venv_out.txt` (124 + 2 skipped).
- `SCR/git_status_short.txt`, `SCR/final_file_list.txt`: new paths and their SHA-256; no tracked diff.
- In WS: `.ai/inputs/scale-78b-s1-llama3-20261105/out/MANIFEST.json` (no build time; `rows` 48 with list ids and token counts; `files[0]` sha `69426993…`); `tmp/scale-78b-s1-llama3-20261105/{edits/add_s1.json,list/s1.json}` (text; git-ignored).

## 5. Acceptance criteria
| criterion | result | evidence |
|---|---|---|
| the fingerprint script and its 1B test | passed | §3 items 1-2, 10; 4 of 4 equal on the 1B pair; tampered copies differ (3 of 4) or refuse (state record disagreeing, missing q, malformed hash, incomplete); `--expect-adapter` pins the reference; `--out` never inside a unit, created once; the side units carry P78:82's abbreviations (M) |
| the S1 decision for OLMo (M) | passed: equal as it stands, build nothing | §3 items 6, 8: parse_edit accepts `904a0cf1…` on `9ed61826…`; 48 of 48 rows at the committed token counts under the 7B main recipe's 3072 (longest row 188 tokens with eos); REQ-7's frozen writer reproduces `904a0cf1…` with stage 1's inputs; a 7B-recipe rebuild changes only `provenance.inputs.recipe` and `provenance.settings_sha256` |
| the Llama S1 set with its MANIFEST and tests; parse_edit accepts on Llama, refuses on OLMo; a re-run gives the same bytes | passed | §3 items 7, 9, 12; MANIFEST `a3986274…`; edit `69426993…` on `c52a50af…`, refused on `9ed61826…` (test and the build's own check); two runs equal, a fresh build equals the committed `out/` |
| the RV2-2 test kills its mutants | passed | §3 items 3-4: R4-a and R4-b KILLED by both new tests; R4-c, R4-d KILLED too; baseline 35 passed |
| no tracked file changed | passed | §3 item 13: `git diff --stat` empty; `git status` lists six new paths only; no git command other than status/diff/check-ignore was run |
| no text printed or stored | passed (with the tmp rule) | every print is a count, a hash, a verdict or a path; the record, MANIFEST and settings are checked text-free by `s1common._text_hits` (test); the edit and the recovered list hold text and live under git-ignored `tmp/` only, as stage 1's rule says; this report and the scratch hold no text |

## 6. Jobs for the lead
1. Decide on §7 item 1 (the Llama edit's home) and item 2 (the recovered list). If both stand: commit by explicit path
   `.ai/inputs/scale-78b-s1-llama3-20261105/` (script, README, out/, tests/), `scripts/scale78b/fingerprint_compare.py`,
   `scripts/scale78b/s1_olmo2_7b_check.py`, the three test files; copy `tmp/scale-78b-s1-llama3-20261105/edits/add_s1.json`
   (`69426993…`) into the main checkout's `tmp/scale-78b-s1-llama3-20261105/edits/` (the kit reads edits by hash) and keep the
   recovered `list/s1.json` (`389c20ad…`) beside it, so the sealed list is on the Mac again. Run `scripts/stage1/commitments.py check`
   after the commit (the post-W1 rule).
2. Re-run the sealed tests in the main checkout once the prepared sets and the a-3 unit are visible there (they are): `MAIN -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-s1-llama3-20261105/tests` (about 20 s). The committed-out test passes only if the committed script's bytes are the ones that built `out/` (`a2b0a66c…`).
3. When each family's a0-1101 retrain is pulled: `MAIN -I -B scripts/scale78b/fingerprint_compare.py --retrain <retrain unit> --reference <side unit> --expect-adapter q=<P78:82 prefix> --expect-adapter e1=<prefix> --out <record>`; OLMo-2-7B: `--reference tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-e1-a1 --expect-adapter q=3c7344c1 --expect-adapter e1=9d5d5d8b`; Llama-3.1-8B: `--reference tmp/family-probe-sp-llama31-8b-b5e5-1101/retrieved/sp-llama31-8b-b5e5-1101/tree/round1/1101-a0-e1-a1 --expect-adapter q=ac05caca --expect-adapter e1=ee44580d`. Exit 0 = equal (Y = X for the family), 1 = differs (the X retrain), 2 = refused. The record holds no value from a unit other than hashes.
4. The 7-8B kit (another track): the OLMo-2-7B S1 arm takes the committed `add_s1.json` `904a0cf1…` by hash; the Llama S1 arm takes `69426993…`. Both under the family's main config (Part 1 §10). No combined `R_d+s1` edits exist for 7-8B (not needed by Part 1 §10; REQ-7's `--combine-with` path is unchanged if one is wanted).
5. FOCUS line (after the commit): the OLMo S1 decision (equal as it stands; check record `9b340bf5…`), the Llama S1 edit hash and MANIFEST hash, the fingerprint script's path, RV2-2 closed.

## 7. Unresolved concerns (for the lead)
1. **The Llama edit holds text and is not committed.** I followed stage 1's rule (text under `tmp/`, a text-free record
   committed; REQ-7's `full_out_ok`). If the lead wants the edit itself inside the sealed folder (as the R files are,
   which hold ids only), it is one copy by hash; nothing in the build changes. The prompts are PKU-SafeRLHF prompts with
   safe responses (R: the settings' `lists.s1.source`), so the question is the repository rule, not harm.
2. **The sealed list was recovered, not found.** The recovered bytes hash to the committed pin `389c20ad…`, so they are
   the sealed list; but the lead should confirm the route (reading the committed OLMo edit's rows through the engine)
   and may prefer to point `--list` at the real file if a copy exists in a backup release. The MANIFEST records the
   source as `recovered` with the edit and record hashes; a build from the real file would differ only in that field.
3. **The settings' `labels_sha256` field** is copied from REQ-7's committed settings (the registry hash it was written
   on). `check_settings` accepts it (it checks the named entries, none here). It is a record of REQ-7's registry state,
   not of this build; harmless, noted.
4. **Determinism across environments.** The record and the edit carry Python and numpy versions in their provenance
   (REQ-7's block). A build in another environment gives other bytes and another arm. The main venv here is 3.11.15 /
   2.2.6, as stage 1's record (M).
5. **The fingerprint script compares records, not weights.** It trusts `COMPLETE.json` (and the state records when
   present). A unit whose records were rewritten consistently would pass; the kit's seal and the record-done flow are
   the defence, as for the frozen reading.
6. **The 16-of-16 record** (certificate C1) was not used as a test input because it lives under `tmp/stage1-olmo/`
   (forbidden for this worker beyond exact-path hashes). The a0@1101 pair that the task names first was used instead.

## 8. Working notes (as written while working; the measurements behind §0-§7)

### 8.1 Inputs read (R) and measured (M) before any code
- Fingerprints live in each unit's `COMPLETE.json` under `checkpoints.<q|e1>.adapter_fingerprint` and `.optimizer_fingerprint` (R: `experiments/safety_selection/runner.py:500-504`); the same values are in `states/<c>/state.json` (M: the w0b-2 retrain unit). The frozen Gate B reading compared the ADAPTER fingerprints only (R: `scripts/gate_b_reading.py:1217-1221, 1331-1332`, `P1101_ADAPTER_FINGERPRINTS` :168). Ruling 10 names adapter AND optimizer (R: lead-rulings-part1-20261105.md:132-143), so T6b compares four values.
- The 1B pair on this Mac (M, hashes only): reference Gate A a0-1101 `/Users/spiderishi/Coding/attribution/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1` (COMPLETE `8f0fa83a…`), retrain Gate B w0b-2 `/Users/spiderishi/Coding/attribution/tmp/gate-b-olmo/retrieved/w0b-2/tree/round1/1101-a0-e1-a1` (COMPLETE `d154f23f…`, as FOCUS:199 records). q adapter `322d737a…`; q optimizer `7a5c0ff2…`; e1 adapter `aad79060…`; e1 optimizer `d2e3c625…`: all four equal (M). FOCUS:199: "fingerprint trigger false". The "16 of 16 files equal" record is the X→Y certificate C1 (`.ai/inputs/stage1-post-w1-20261023/block-a/certificate_xy.json`; `runkit/stage1-olmo/compare_c1.py`; an R_1101 unit under `tmp/stage1-olmo/`, a forbidden folder for this worker), so the 1B test uses the Gate B a0@1101 retrain pair above, which the task names first.
- The side units' fingerprints (M, from their COMPLETE.json, hashes only): OLMo-2-7B 1101 q adapter `3c7344c178b47e5ba5a64c0db284fce4020e333aaa6b1ab0dc9a21dde756bf06`, e1 adapter `9d5d5d8b2eb40262a3d093264af08e7f7c83d958fd9af9cda9bf023b1ef5430a`; Llama-3.1-8B 1101 q `ac05caca1bdfac5b26ae09eef854aec01552cc70b905286b694226eee06ac4a2`, e1 `ee44580dfa016b678238c4f5d1d2cb4e944d3ed4fdfd6f5d66207486176f8a3e`. They match P78:82's abbreviations (R).
- REQ-7 at HEAD (M, shasum): `scripts/stage1/write_add_edit.py` `8b866b3d…`, `s1common.py` `930c8ea5…`, `settings/write_add_edit.json` `7cf7dd77…`, `build_s_pool.py` `cb2ca385…`, `token_accounting.py` `b9a51f6f…`; these equal the committed add-s1 record's provenance (R: `.ai/inputs/stage1-commitments-20261016/add-s1/add_edit_record.json`, SHA-256 `311957a4…`).
- The committed S1 edit: `add_s1.json` SHA-256 `904a0cf1…`, 48 adds, list `s1` `389c20ad…`, max_train_tokens 3072, recipe S 1B `ceffe0ef…`, manifest `9ed61826…` (R: the add-s1 record). A copy of its bytes survives as `edit.json` in the stage-1 S1 units (M: `tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-904a0cf1…-e1-a1/edit.json` hashes to `904a0cf1…`; read by exact path after the hash; no text printed).
- The sealed list `s1.json` is NOT on this Mac by name (M: `find tmp -name s1.json` over the allowed folders: none; `.ai/` none). It is recoverable: the committed edit's 48 add rows (through the engine's `parse_edit`, frozen code) with the record's add_id→list_id map, in `canonical_json({"kind": "stage1 prompt list", "version": 1, "name": "s1", "items": [...]})` (the writer's form, R: `scripts/stage1/build_s_pool.py:373-378`), hash to `389c20ad…` exactly (M; 22,211 bytes, 48 items). So REQ-7's `read_list` accepts the recovered file by its pin.
- Token limits (M, config_sha256 with the main venv): 1B recipe S `ceffe0ef…` 3072; 1B REC `9e9bde6f…` 3072; OLMo-2-7B main `18cc31d7…` 3072 (tokenizer pin `allenai/OLMo-2-0425-1B-Instruct`, the prepared set's); Llama-3.1-8B main `74758af1…` 3072. Engine identity in WS `472fc7f6…`; main venv Python 3.11.15, numpy 2.2.6 (= the record's provenance); .venv Python 3.11.15, numpy 2.4.6.
- Both codecs load offline from the HF cache (M: `allenai/OLMo-2-0425-1B-Instruct`, `meta-llama/Llama-3.1-8B-Instruct`), eos ids 100257 / 128009.
- RV2-2 (R: reverify-BC2.md:174-187, r4_probe_out.txt): with a0@1101 perturbed the real code gives `{"a0@1101": [], "a0@1102": ["gpu"], "a0@1103": ["gpu"], "R@1101": ["gpu"], "R@1102": ["gpu"], "R@1103": ["gpu"]}`, trigger True, governing fallback, σ_F 2.16 (M here too).
- The Llama edit's token counts (M, from the MANIFEST; counts only): prompt tokens sum 3,019 (the Llama chat template is longer than OLMo's: the OLMo record sums to 1,871), target tokens sum 2,199 (equal to the OLMo record's 2,199), longest row 211 tokens before eos; the same 48 list ids in the same order as the committed record.

### 8.2 Progress (17:34 UTC)
- T6b written; 1B pair 4 of 4 equal; 10 tests passed (.venv).
- RV2-2: 7 tests passed; mutants R4-a, R4-b, R4-c, R4-d all KILLED, no survivor.
- S1 OLMo-2-7B: checks (1)-(3) hold; verdict equal as it stands. The first run without the combine inputs gave `1760fa53…` (the shared provenance block names the three remove edits), which is why the check passes them.
- S1 Llama: trial builds; the MANIFEST made independent of the operator's `--full-out`; 15 passed + 1 skipped + 1 test fixed.

### 8.3 Finish (17:43 UTC)
- The real build (17:37 UTC): script `a2b0a66c…`, MANIFEST `a3986274…`, record `1023b4e6…`, settings `36a39481…`, edit `69426993…`, list `389c20ad…`. Sealed tests 17 passed. All new tests 24 passed (main venv). Both folders under .venv 84 passed, 2 skipped (codec tests skip there). All three test folders under the main venv 124 passed, 2 skipped. Scratch temp folders removed; WS `tmp/` holds `kt-prepared/` and `scale-78b-s1-llama3-20261105/` only.
