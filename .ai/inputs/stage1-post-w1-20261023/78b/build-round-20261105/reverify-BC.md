# Re-verify, tracks B and C (fix round)

Role: adversarial re-verifier for GI X (Fable). Default verdict DEFECTS until each claim is proven.
Started 2026-11-05 15:20:11 UTC; written 15:38:37 UTC (M: `date -u` read right before each time).

Trees read: ws-c (the merged tree, HEAD `fb51421`, read-only for me) and ws-b (the rebuild's record, HEAD `fb51421`).
Fixer's report: `reports/fix-BC.md`. Round-1 reports: `build-B.md`, `verify-B.md`, `build-C.md`, `verify-C.md`.
My scratch: `reports/reverify-BC-scratch/` (88 KB after cleanup: six scripts and their outputs, the fixer's harness copy, the
parity record). Every mutant ran on a COPY of ws-c's files in a scratch root; ws-c and ws-b were never edited (section 10).

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference. Short sentences.

## 1. Verdict: VERIFIED_WITH_MINOR

Every fixer claim I tested holds (M). B-M1..B-M3, C-D1..C-D5 and the A6 test are closed by code and by tests that fail
without the fix: my own hand mutant per item dies on that item's own test (section 4). The rebuild is intact: 419
independent checks pass, the three CLIs reproduce the committed `out/` byte for byte, all 18 OLMo parity files are
byte-identical to SEAL and to stage 1's d = 6-10, every embedded script SHA-256 equals the bytes on disk, and every MANIFEST
and record hash equals the fixer's figure (section 5). The noise reader accepts the rebuilt Llama R_d1-R_d3 as N's R units
through `read_unit` itself (on a synthetic sealed unit) and refuses nine tampered copies (section 6). Both test folders pass
together and alone (section 7). No output stores text (section 9).

Three minor items, none a wrong remove list, a wrong number or a wrong refusal (section 3): (RV-1) the three write guards
compare resolved path strings, so a case-variant spelling of SEAL's path is not refused on this Mac's case-insensitive
filesystem (M); (RV-2) eight of my mutants survive or die only through the script-hash test: test gaps, the code is right
in each case; (RV-3) one stale README sentence. No blocker, no major defect.

## 2. Files I changed

None in ws-b or ws-c. Only this report and the scratch files under `reports/reverify-BC-scratch/`.

## 3. Defects found (all minor)

| id | severity | where | what | fix |
|---|---|---|---|---|
| RV-1 | minor | `build_sealed_llama3.py:415-428`, `build_r_draws_78b.py:187-201`, `build_h1_llama3.py:103-115` (`guard_out`) | The guard compares `out.resolve()` with `(root / forbidden).resolve()` as strings. On this Mac (APFS, case-insensitive) `.ai/inputs/GATE-B-SEALED-20261008/out/new` exists as the same directory as SEAL's `out/` (M: `os.path.samefile` True, `resolve()` keeps the typed case) and none of the three guards refuses it (M: NO REFUSAL ×3). The absent-or-empty rule does not stop it: `new` is absent, so a build would create and fill a folder inside SEAL. Symlinks into SEAL, relative and dotted paths and the folder itself are refused (M). | Compare by identity, not by string: for each forbidden folder that exists, refuse if the deepest existing ancestor of `out` (or `out` itself) is `os.path.samefile` with it; or case-fold both sides when the filesystem is case-insensitive. A byte change to the three hashed scripts: rebuild into empty `out/` and the 30 tests again (addendum A3's rule), the lead decides before the first commit. Default use is correct; the bypass needs a mistyped case variant. |
| RV-2 | minor | the six test files (section 8) | Survivors of my mutants: C-D3b (`anchor_records` ignoring `kind`/`complete`), C-D4b (duplicate check keyed by path instead of `complete_sha256`), R2 (`edit_kind` not checked), R3 (edit.json not bound to the named arm's hash), R4 (reference unit a0@1102 instead of a0-1101), R5 (`hex64` accepting upper case); and two killed only by the committed-`out/` hash test, not by a behaviour test: G1 (the r-draws guard's absent-or-empty refusal), G3 (the H1 CLI passing `repo` to the guard). The production code is right in each case (R3's check is the one that refused my row-tampered copy, section 6). | Eight small tests, no hash change: a synthetic incomplete anchor record is skipped; a copied unit at another path with the same COMPLETE.json refuses as a duplicate; `r_edit_matches` refuses `edit_kind` "rewrite"; a unit whose edit.json hashes to another arm refuses; an environment difference on a0@1102 alone fires the trigger with a0-1101 as the reference; an upper-case key refuses; `B.guard_out(non_empty)` refuses; `H.main(["--repo", other, "--out", other/SEAL/new])` returns 2. |
| RV-3 | minor | `.ai/inputs/scale-78b-sealed-llama3-20261105/README.md:48` | Says the engine test "accepts each Llama file against the Llama set (the engine's own `load_prepared`)". After B-M1 the tests use the id-only `engine_stub()` and never `load_prepared` (R test files; M: the B tests open exactly six prepared-set files, section 4). | One sentence; the README is not hashed, so no rebuild. |

## 4. Per item: closed by code and by a test that fails without the fix

Harness: `reverify-BC-scratch/mutate_rv.py` (output `mutate_rv_out.txt`). A scratch root reaches ws-c's engine, research,
tmp and committed `.ai/inputs` folders by symlink; `scripts/scale78b/`, the Llama sealed-set folder, SEAL and the anchor
folder are copied (SEAL because the sealed MANIFEST records the frozen builder's path relative to REPO, and a symlink
resolves outside it, a harness artifact: M, `frozen_builder/loaded_from` was the only differing field; the anchor folder
because `rglob` does not descend into symlinked folders). One mutant = one or more replacements in the copy; the same
pytest command runs on the baseline and on each mutant; KILLED = exit non-zero, named failed tests, no errors. Baselines:
noise 23 passed (.venv), maker 13 passed (main venv), B 30 passed (main venv); all exit 0 (M).

| id | code closes it (R) | fixer's test (M, passes) | my hand mutant (M) | result |
|---|---|---|---|---|
| B-M1 | the three engine tests use `W.PreparedView(...).engine_stub()` / `s1.PreparedView(...).engine_stub()`; `grep load_prepared` over the six test files finds comments only | the three tests pass in the 30 | not a code change, so an open() logger instead: a root `conftest.py` wraps `builtins.open`/`io.open`, logs every prepared-set path and raises on `query_rows.jsonl`, `hidden/`, `selector/`, `banks/`, `auditor/`, `samples.jsonl`, `generations.jsonl`. The B tests opened exactly 6 distinct prepared-set files: `manifest.json`, `engine/groups.json`, `engine/train_rows.jsonl` of each set; 29 of 30 passed, the one failure being the harness artifact above (`mutate_rv_logger_out.txt`) | closed |
| B-M2 | `build_h1_llama3.py:49-52` `FORBIDDEN_DIRS = (SEAL, anchors, stage 1)`; `guard_out` :103-115 | `test_the_h1_script_never_writes_under_seal_the_anchor_list_or_stage1_from_any_repo` | `FORBIDDEN_DIRS = (STAGE1_DIR_REL,)` (round 1's set) → KILLED: that test fails (assert) plus the committed-out test (the script's hash changed) | closed |
| B-M3 | `guard_out(out, repo=None)` builds `roots = [REPO.resolve()]` first, then `--repo` (:419-428 / :191-199 / :107-115); the CLIs call it before any read (:583-585 / :273 / :128) | `test_a_non_default_repo_cannot_aim_the_output_into_this_checkouts_sealed_folders` (sealed and r-draws), the H1 test above | `roots = [repo.resolve()] if repo is not None else [REPO.resolve()]` (round 1's --repo-only resolution) in each of the three scripts → KILLED ×3: the non-default-repo test / the H1 guard test fails with DID NOT RAISE in each | closed |
| C-D1 | `pooled()` :370-390 (2k divisor, median of the k × 3 governing SE², s_arm on Σ df) | `test_sigma_pool_the_pooled_median_and_s_arm_on_exact_inputs`; the parity test's s_arm and median assertions | (a) median over the first family's three SEs → KILLED (σ̂_pool test, A6 test); (b) `df_arm = 2 * k` → KILLED (σ̂_pool test, parity test); (c) σ̂_pool ignores the median term → KILLED (σ̂_pool test); and R7 `seed_rule(sigma, k)` → KILLED | closed |
| C-D2 | `seed_rule` :292 `review = not GB.ge(2 * SESOI_PP, ex(MDE_FACTOR[plan]), sigma)`; `CEILING_SIGMA_PP` :94 derived, printed, never compared | `test_the_review_ceiling_is_the_mde_rule_itself_one_constant_at_the_boundary` | (a) threshold loosened by 1e-6 → KILLED (the +1e-7 case); (b) `GB.gt` (strict at the ceiling) → KILLED; (c) ceilings pinned to the round-1 constants → KILLED (exact-equality assertion) | closed |
| C-D3 | `make_recipe_s78.py:118-144` `anchor_records`, `anchored_to` (record's `recipe_sha256` must be THIS family's main config); the "not in configs until" test removed | `test_any_s78_config_in_the_configs_folder_is_anchored_to_a_committed_record_of_its_family` (vacuous today: M, no `*gateb*` config but the 1B one, 69 family recipes) and `test_the_anchor_link_refuses_a_placeholder_and_a_borrowed_1b_anchor_file` | (a) `anchored_to` without the recipe check → KILLED (the borrowed-1B test); (b) `anchor_records` without the kind/complete filter → SURVIVED (RV-2) | closed; one gap |
| C-D4 | `family_reading` :320-326: the `complete_sha256` key is tested against `seen` before `read_unit` | `test_a_unit_listed_twice_refuses_on_the_duplicate_check`, `test_a_unit_listed_under_two_families_refuses_as_a_duplicate` | (a) the check moved back after `read_unit` (round 1's order) → KILLED (both tests, assert); (b) keyed by `path` instead of `complete_sha256` → SURVIVED (RV-2: the tests list the same path twice, never a copy at another path) | closed; one gap |
| C-D5 | :180-181 fresh-R refusal; `read()` :438-439 parity-with-tier refusal | `test_an_r_unit_that_resumed_refuses_and_an_a0_unit_may_resume`, `test_a_parity_only_family_is_never_pooled_with_a_tier_family` | (a) the fresh-trajectory rule applied to a0 instead of R → KILLED (12 failures: the resumed Gate A a0@1101 refuses everywhere, the item's test among them); (b) `if len(tier) > 1 and parity` → KILLED (DID NOT RAISE) | closed |
| A6 | `_exact` holds the GOVERNING reading's `sdr2` and `pair_se2` (:366-367); `pooled` records `governing_by_family`, `pair_terms_by_family` (:386-388) | `test_one_familys_fallback_puts_its_r_r_pair_terms_beside_the_others_seed_matched_terms` (median (1.29 + 2.00)/2 = 1.65 on wave 0a) | the SD(r) term taken from the plain reading while the fallback governs (the fixer's mutant took the pairs) → KILLED (the A6 test, assert) | closed |

The fixer's own harness, re-run from my scratch (`mutate_fix_copy.py`, output `mutate_fix_rerun_out.txt`): baseline 23
passed; N4, N5, N6, N15, N17, D4, D2, A6 all KILLED, 0 errors (M). Same verdicts as `fix-BC-scratch/mutate_fix_out.txt`.

## 5. Rebuild integrity (M unless marked)

- Hashes equal the fixer's report, every one: Llama sealed `out/MANIFEST.json` `ba524373161b0c7cbc0fb4c79a71f6cf7b3e4c7a8d3d746915984b5b1db1a812`;
  OLMo d = 11-16 `189275c0137e1025fca95e5ca045fba16b7577cb7cb15032433aa5bfbae098f7`; H1 `29347da2c82c98509d0ecc81d8543ebba4855e70b35f21d4e505aa4788fd29fb`,
  `octile_0.json` `9204121a57d745b81fa00cfde51184e8be8d3c2fdb6a3814065976f76990ae5b`; scripts `build_sealed_llama3.py` `227aed4f…`,
  `build_r_draws_78b.py` `5cd1036d…`, `build_h1_llama3.py` `504e9462…`, `noise_reading.py` `94b679ff…`, `make_recipe_s78.py` `fcf01955…`,
  `g1_check_78b.py` `251ddb32…` (unchanged); the G1 record `8c3579e4…`, its units file `233fa4b7…` (unchanged); BLD `80cb8944…` in both copies.
- `reverify-BC-scratch/integrity.py` (my own reader, stdlib, `-I -B`): **419 checks, 0 failures** (`integrity_out.txt`). For
  all 24 + 6 + 1 edit files: SHA-256 == the MANIFEST's, arm == `edit-<sha256>`, the embedded `builder_sha256` /
  `scale78b_wrapper.script_sha256` / `script_sha256` == the script's bytes on disk, `kind` "safety-selection edit",
  `edit_kind` "remove", the right manifest (`c52a50af…` Llama, `9ed61826…` OLMo), `rewrite`/`add` empty, counts right, 600
  sorted distinct rows, 75 per unit against the prepared set's dev groups (ids only; the two sets' groups are equal),
  `selection.family` "R", `selection.draw` d, `provenance.seed` 1100 + d, the MANIFEST record's seed/draw/family; Llama
  R_d1-5 == SEAL's remove lists with `same_rows_as` hashes equal to the real files; R_d6-10 == stage 1's (record seeds
  1106-1110); R_d11-16 == the OLMo d = 11-16 files' lists, `same_rows_as` None; 16 distinct draws; unit files == group
  members == SEAL's unit files; the r-draws reproduction flags; H1's stage-1 pin equals the committed file; the G1
  record's `noise_reading_sha256`, `script_sha256`, `inputs_sha256` equal the bytes of ws-c's `noise_reading.py`,
  `g1_check_78b.py` and the units file.
- The three CLIs re-run with `-I -B` into my scratch: exit 0 ×3; `diff -r` against the committed `out/`: IDENTICAL ×3.
- Parity: `--olmo-parity-out` wrote 18 files + PARITY.json; `cmp` byte-identical for SEAL's R_d1-R_d5 and 8 unit files and
  for stage 1's R_d6-R_d10 (18 of 18); PARITY.json `byte_identical: True` ×13 sealed, `(True, True)` for
  `byte_identical`/`stage1_wrapper_rederived` on d = 6-10. The fixer's kept PARITY.json says the same.
- ws-b: `diff -r` of the three sealed folders and `cmp` of the two scripts and two tests against ws-c: IDENTICAL ×7; ws-b
  `git status --porcelain` four `??` folders, HEAD `fb51421`, no `__pycache__`.
- The G1 record against the round-1 copy (`fix-BC-scratch/llama-g1-check-20261105.round1.json`): a field-by-field walk
  finds ONE difference, `noise_reading_sha256` `6cde1a24…` → `94b679ff…`; `by_family` llama31-8b 1 pass / 1 fail
  (`llama31-8b-a0-1102`), olmo2-7b 3 pass, olmo2-1b 2 pass (addendum A4's reading stands).
- READMEs: the round-1 hashes appear only as labelled "was removed first" history (R lines 7-9 of each). RV-3 aside, the
  hashes named are the new ones.
- `scripts/stage1/commitments.py check --repo .` in ws-c: `OK: 140 entries … HEAD fb51421…`, exit 0 (reads HEAD only).

## 6. The noise reader on the rebuilt Llama R_d1-R_d3 and tampered copies (M, `synthetic_unit.py`, output `synthetic_unit_out.txt`)

A synthetic SEALED unit folder (job.json, identity.json with the Llama main config as recipe, assets.json with a CUDA
environment record, policy and guard blocks, a lock, edit.json, COMPLETE.json listing every file's hash) lets
`noise_reading.read_unit` run to its end (it stops before `arm_from_unit`, which needs eval files). The Llama main
config's training identity by `GB.canonical_sha256({model, train})` equals the pin `5b4451e1…` (M).
- ACCEPTED: R_d1, R_d2, R_d3 as llama31-8b R@1101/1102/1103 with the inputs naming the MANIFEST's arm (recipe `74758af1…`,
  no resume recorded).
- REFUSED: one row changed while the inputs name the sealed arm ("edit.json is missing or is not the arm's edit file":
  the check my mutant R3 removes); `selection.draw` 2 at seed 1101; re-labelled with the OLMo manifest; `selection.family`
  "unit"; `edit_kind` "rewrite"; R_d2 in the 1101 slot; SEAL's OLMo R_d1 under llama31-8b (each "not the R draw 1 of the
  family's manifest"); a unit whose job.json resumes ("an R arm is a fresh trajectory"); the Llama H1 file as R.
- ACCEPTED by design, stated as a limit: a row-tampered copy whose OWN arm the inputs name passes `read_unit` (it reads
  no rows). The binding to the sealed list is the inputs file's arm (P78:291 keys N's inputs by `complete_sha256` and
  arm) and the engine: `parse_edit` on the id-only Llama stub refuses a copy with an unknown row id and accepts the genuine
  R_d1 (600 removed, arm == the MANIFEST's). The lead's N inputs must take each R arm from the Llama MANIFEST.
- `r_edit_matches` (the fixer's test, in the 69): the five fields on all 16 Llama R files, the 6 OLMo files and SEAL's R_d1.

## 7. Test runs (M; ws-c root; `PYTHONDONTWRITEBYTECODE=1 <python> -B -m pytest -q -p no:cacheprovider --basetemp=<my scratch>`)

| run | python | result |
|---|---|---|
| both folders in ONE invocation: `.ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests -rs` | main venv | **69 passed, 2 skipped (scipy) in 3.89s**, exit 0 |
| B alone: the sealed tests + `test_build_r_draws_78b.py` + `test_build_h1_llama3.py` | main venv | 30 passed in 0.84s, exit 0 |
| C alone: `test_make_recipe_s78.py test_noise_reading.py test_g1_check_78b.py -rs` | main venv | 39 passed, 2 skipped (scipy) in 2.94s, exit 0 |
| noise + G1 (the scipy tests run) | `.venv` | 28 passed in 3.19s, exit 0 |

Counts: B 30 + maker 13 + noise 23 (2 scipy skips under the main venv) + G1 5 = 71. After every run: no `__pycache__`,
no `.pytest_cache` in ws-c; `git status --porcelain` still six `??` paths (54 files with `-uall`).

## 8. My own mutants (M, `mutate_rv.py`; 28 in all, 17 per-item in section 4 and these 11)

| id | mutant | target tests | result |
|---|---|---|---|
| R1 | `r_edit_matches` without the manifest check | noise | KILLED (the edit-file test) |
| R2 | `r_edit_matches` without the `edit_kind` check | noise | **SURVIVED** (no file differs only in edit_kind) |
| R3 | `read_unit`: edit.json no longer bound to the named arm's hash | noise | **SURVIVED** (no test has a unit whose edit.json hashes to another arm; the check is right: section 6) |
| R4 | the environment reference is a0@1102, not a0-1101 | noise | **SURVIVED** (the wave-0a units share one environment) |
| R5 | `hex64` accepts upper-case hex | noise | **SURVIVED** |
| R6 | the environment trigger dropped (fallback on fingerprint only) | noise | KILLED (`test_an_environment_difference_triggers_the_fallback`) |
| R7 | pooled df = k | noise | KILLED (the σ̂_pool test) |
| G1 | r-draws guard: the absent-or-empty refusal removed | B | KILLED by the committed-`out/` hash test only: **no behaviour test** (gap) |
| G2 | sealed wrapper guard: equality with the forbidden folder itself not refused | B | KILLED (the two guard tests and the hash test) |
| G3 | H1 CLI passes `repo=None` to the guard | B | KILLED by the hash test only: **no behaviour test** (gap) |
| G4 | sealed wrapper CLI: `--olmo-parity-out` not guarded | B | KILLED (the non-default-repo test and the hash test) |

Six survive and two die for the wrong reason: RV-2. Input probes (not mutants, on ws-c's own code, nothing written):
the three guards refuse a symlink into SEAL, a relative path into SEAL, a dotted path into stage 1 and the sealed folder
itself; they do not refuse the case-variant spelling (RV-1); a sibling folder with a shared prefix passes (correct).

## 9. Text leak walk of ws-c outputs (M, `textwalk.py`, output `textwalk_out.txt`)

36 JSON files walked (24 + 6 + 1 edit files, 3 MANIFESTs, the G1 record and its units file): no string with a newline;
the longest string in any edit file is 415 characters at `/position_rule` (the engine's rule sentence, the same in SEAL's
files); the MANIFESTs' longest 229 / 199 / 242 (`frozen_builder/used`, `requirement`, the stage-1 length rule); the G1
record's longest 191 (`/rule`), its units file's 161 (a path); no key matching prompt / response / answer / completion /
instruction / text / generation / sample / message / content except `sampled`, `answers_end` and the bars' share names in
the G1 record (counts and shares). The anchor record the maker reads (`gate-b-anchors-20261008/out/anchors.sealed.json`):
its `anchors` list holds 128 entries, 640 strings, the longest 64 characters, none over 80 (hashes, no text);
`anchor_file_bytes` is an integer. Prints: `noise_reading.main` prints the summary (no U, no string over 160: the tests'
`no_u_anywhere` walk); the three build scripts print hashes, counts, cut points and seeds (R); `make_recipe_s78` prints
six hashes/names (R :178-180); `g1_check_78b.py` has one print at :153-154 (R): the output's SHA-256, `by_family` and, per
unit, `id`, `answers_end`, `G1`, `sampled`, `shares` (verdicts, counts and shares; the record itself carries no string over
191 characters, M above).

## 10. Commands run (every one; exit 0 unless stated; all foreground, none over 15 s except pytest at 3.9 s and the harness at about 2 min)

1. `date -u` ×4; `mkdir` scratch; `ls` reports and ws-c/ws-b trees; `git -C ws-c status --porcelain [-uall]`, `rev-parse HEAD` (before and after everything: six `??`, 54 files, `fb51421`); `find __pycache__ / .pytest_cache` → 0; `git -C ws-b status`, `rev-parse`.
2. Reads (Read/sed/grep/cat): the rulings, the addendum, the check's T3/T5/T6a/C5/C6 lines, fix-BC.md, verify-B.md, verify-C.md, the fixer's harness and output, `noise_reading.py`, `make_recipe_s78.py`, the three build scripts, the six test files, both conftests, `__init__.py`, the frozen `ge`/`gt`/`median_term`/`sigma_value`/`compared_fields`/`arm_from_unit`/`sealed`, `s1common.PreparedView`, `g1_check_78b.py:34-44, :135, :146-159`, the three READMEs' hash lines.
3. `shasum -a 256` of the 3 MANIFESTs, octile_0, 6 scripts, 2 records, BLD ×2 (section 5); `diff -r` ×3 and `cmp` ×4 ws-b against ws-c; `.venv/bin/python -I -B` field walk of the round-1 G1 record against the new one.
4. pytest ×4 (section 7).
5. `.venv/bin/python -I -B reverify-BC-scratch/integrity.py <ws-c>` → OK 419 FAILS 0.
6. main venv `-I -B`: `build_sealed_llama3.py --out <scratch> --olmo-parity-out <scratch>`; `build_r_draws_78b.py --out <scratch>`; `build_h1_llama3.py --out <scratch>` → 0 ×3; `diff -r` ×3 IDENTICAL; `cmp` ×18 identical; PARITY.json flags printed.
7. `.venv/bin/python -I -B textwalk.py <ws-c>` → 36 files (section 9).
8. `grep` for the round-1 hashes in the new files (READMEs' history lines only) and for `load_prepared|query_rows|hidden/|selector|samples|generations` in the new code (comments, the wrapper's NEVER_OPENED list and the MANIFEST copy of it only); `ls .ai/inputs`, `scripts/`, `tmp/`; `find anchors.sealed.json` (one record); `.venv -I -B` keys of the 1B anchor record (keys and hashes only).
9. `.venv/bin/python -I -B mutate_rv.py <ws-c> --logger` → B-M1 logged run (section 4).
10. main venv `-B synthetic_unit.py <ws-c> <scratch>` → section 6, SUMMARY all expected True.
11. main venv `-I -B` guard probes (case variant, symlink, relative, dotted, the folder itself, a sibling) on the three guards; the anchor record's aggregate text measurement; the S_78 config listing (one 1B file; 69 family recipes).
12. `.venv/bin/python -I -B mutate_rv.py <ws-c>` → first run exit 1 (the B baseline failed on the symlink artifact; diagnosed by a scratch build: `frozen_builder/loaded_from` differed); harness edited (SEAL copied); second run exit 0: 3 baselines pass, 28 mutants (sections 4 and 8).
13. `.venv/bin/python -I -B mutate_fix_copy.py <ws-c>` (the fixer's harness, from my scratch) → baseline 23 passed; 8 KILLED.
14. ws-c: main venv `-I -B scripts/stage1/commitments.py check --repo .` → OK, 140 entries, HEAD `fb51421`.
15. `grep` for the round-1 values and the old ceilings in the main checkout's `research/FOCUS.md` (none), the Part 1 draft (not in the main checkout; ws-d's copy: none), verify-C.md (:127-132 the old ceilings and D2 band, :158, :263 the old G1 hash: historical), fix-D.md and reverify-D.md (none); `sed` of the sealed README :44-50.
16. `rm -rf` of my pytest basetemps, the mutant roots, the CLI outputs (the PARITY.json kept), the synthetic units and the probe link; `du` 88 KB; `date -u`.

Not run: any pod, network, install, download, agent, message; anything in the main checkout (reads by absolute path
only); any git state change; the engine suite (the engine is untouched: ws-c's `git status` shows no tracked change).

## 11. Acceptance criteria

| criterion | result | evidence |
|---|---|---|
| B-M1 closed by code and by a test that fails without the fix | passed (code and a measurement; no test applies) | id-only stubs in the three tests (R); the open() logger: 6 prepared-set files, none text (M) |
| B-M2, B-M3 closed by code and by tests that fail without the fix; my hand mutant per item | passed | section 4: four mutants, each KILLED on the item's own test |
| C-D1..C-D5, A6 closed by code and by tests that fail without the fix; my hand mutant per item | passed | section 4: thirteen mutants, each item KILLED on its own test (C-D3b and C-D4b, extra variants, survive: RV-2) |
| every embedded wrapper SHA-256 equals the file's bytes in ws-c | passed | integrity.py: 24 + 6 + 1 files, the MANIFESTs' script hashes (M) |
| the stage-1 d = 6-10 parity holds | passed | `cmp` byte-identical ×5; PARITY.json flags; the fixer's test in the 69 (M) |
| membership, manifest binding and the seal fields hold | passed | integrity.py 419/0; the engine's parse_edit on the stub (M) |
| MANIFEST SHA-256 values match the fixer's report | passed | section 5 (M) |
| the noise reader accepts the rebuilt Llama R_d1-R_d3 and refuses a tampered copy | passed | section 6: read_unit accepts ×3, refuses 9 tampered copies (M) |
| both test folders in one invocation and each alone | passed | section 7: 69 passed 2 skipped; 30; 39 + 2 skipped; 28 under .venv (M) |
| at least five new mutants of my own on noise_reading.py and the guards, survivors reported | passed | section 8: 11 (7 reader, 4 guard); 6 survive, 2 die for the wrong reason |
| nothing in ws-c prints or stores text | passed | section 9 (M, R) |
| the engine suite | not tested | not asked; the engine is untouched; round 1's 837 passed stands (a lead job if wanted) |

## 12. Jobs for the lead

1. **Decide RV-1 before the first commit** (frozen-on-commit, addendum A3): fix the three guards by identity comparison and
   rebuild into empty `out/` (the 30 tests again; every arm hash changes, as in round 1's B-M3), or record the limit (the
   default use writes to `<repo>/<OUT_REL>`; the bypass needs a mistyped case variant). My pick: fix now, since the
   rebuild is a five-minute step today and impossible after the commit.
2. **Merge from ws-c by explicit paths** (54 new files; `git status --porcelain -uall`): the three `.ai/inputs/scale-78b-*/`
   folders, the two G1 records, `scripts/scale78b/`. Commit each hashed script with its `out/`. Fix RV-3's sentence in the
   sealed README first (not hashed).
3. **After the merge, in the main checkout:** the two pytest commands of fix-BC.md job 2 (expect 69 passed 2 skipped; 28
   passed under .venv); `scripts/stage1/commitments.py check`; the engine identity re-check `472fc7f6…`.
4. **Records.** FOCUS.md and the Part 1 draft cite none of the round-1 values (M, grep); verify-C.md does (historical, leave
   or annotate). If any record names the G1 record, use `8c3579e4…` (counts unchanged). Part 1 §3.3: the MDE rule, not a
   ceiling constant (derived ceilings 7.0388 / 9.2721 / 10.7066 pp).
5. **N's inputs file:** take each Llama R arm from the Llama MANIFEST (`edit-091de345…`, `edit-59fc31df…`, `edit-c875e730…`
   for R_d1-R_d3; fix-BC.md §2.4) and each unit's key from its COMPLETE.json; `read_unit` binds the unit to that arm, not
   to the MANIFEST (section 6).
6. Optional, no hash change: the eight gap tests of RV-2 (a builder hour, E from the sizes).
7. Optional: the full engine suite (round 1's command, about 80 s).
8. Delete `reports/reverify-BC-scratch/` (88 KB) and `fix-BC-scratch/` once read.

## 13. Unresolved concerns

1. RV-1 is a real bypass on this Mac's filesystem but needs a mistyped path; its fix changes every arm hash. The lead's
   call (job 1). A later fix is impossible without breaking the committed provenance.
2. `read_unit` trusts the inputs file's arm (section 6). This matches P78:291's keying, but it means the sealed MANIFEST is
   not consulted by the reader; the lead writes N's inputs by hand from the MANIFEST (job 5).
3. A6 and N17 are proved one level below `read()` (the fixer's concern 2 stands); my synthetic unit proves `read_unit` on
   the Llama R files, not `family_reading` (no eval files). The first real two-family `read()` is N's.
4. Any further byte change to `noise_reading.py` changes the G1 record's `noise_reading_sha256` again (R
   `g1_check_78b.py:135`); test-only changes (RV-2) do not.
5. The sealed MANIFEST records the frozen builder's path relative to REPO when it is under REPO and absolute otherwise
   (M in my harness): a build from a checkout where SEAL is a symlink gives different MANIFEST bytes. Not a defect for the
   lead's main-checkout builds; stated.
6. Byte parity for d = 6-10 depends on the environment (Python 3.11.15, numpy 2.2.6 per the README); it held here (M).
7. The main checkout's `git status` shows the lead's own modified and untracked files; none of my paths (M, grep count 0);
   I wrote nothing there.
