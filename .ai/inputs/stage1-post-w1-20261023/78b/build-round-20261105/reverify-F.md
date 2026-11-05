# Re-verify F (round 3 fix round, 7-8B tier $0 build): F-1 cleanup, F-2/F-3 README, F-4 guard tests

Started 2026-11-05 18:32 UTC; written 18:50 UTC, finished 18:53 UTC (`date -u` before each time: 18:32:26, 18:49:50, 18:53:31). Re-verifier: self-identified
Fable 5.1 (the launcher's routing evidence governs). Role: adversarial re-verifier of the fixer's track F work. No fixer file
edited; no git state changed; nothing written outside my scratch.

- Rulings read first: PP1-PP6 (`/Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part2-prep-20261105.md`); PP6 governs F-2/F-3.
- Reports read: `fix-F.md`, `verify-F.md`, `build-F.md` (all under `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/`).
- Worktree (WS, read-only for me): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-f` (HEAD 953f520; `git status --short` lists seven untracked paths only; `git diff --stat` empty, before and after my work, M).
- My scratch (SCR): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/reverify-F-scratch/`.
- Every test, probe and mutant ran in `SCR/wsf-copy/` (an rsync of WS without `.git` and `__pycache__`, 114 MB; the check tests write under `<root>/tmp/`, so nothing touches WS; removed after this report, section 8). MAIN = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python`; SCI = `/Users/spiderishi/Coding/attribution/.venv/bin/python`. Every MAIN run had `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1`; every pytest had `-p no:cacheprovider` and a `--basetemp` under SCR. All commands foreground; the longest about 2.5 min.
- The OLMo S1 edit was named by its exact path only (`/Users/spiderishi/Coding/attribution/tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-904a0cf1…-e1-a1/edit.json`); the check script hashes it against the pin before `parse_edit`; nothing of that folder was listed or printed.

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference. No text printed or stored (section 7).

## 0. Verdict: VERIFIED_WITH_MINOR

The fixer's four results hold as claimed (M): the two F-1 survival tests fail on the unfixed script and pass on the fixed one;
a pre-existing `--scratch-tmp` (empty, non-empty, a file, a symlink to either) survives every run; the verdict record is
`9b340bf504400576f116e394fa9dd669cff623c0a35e8bb34cdd1c2ee018d2ca` in six fresh runs, byte-identical to the verifier's; the
F-2/F-3 sentences are true of the code; V6 and V8 die on the new file; `build_s1_llama3.py` and `out/` are round 3's bytes;
all tests pass. Five minor items remain, none a blocker: the cleanup still removes a scratch folder that **appeared during the
run** (measured with two concurrent CLI runs: the second deleted the first run's `--keep` list; RF-1); `--out` inside
`--scratch-tmp` is deleted after its hash is printed (RF-2); the pre-existing-empty case has no test, so a mutant that deletes
that folder survives (RF-3; the fixer's own concern 1); the reader's path from `assets.json` to the guard record is untested
(my mutant H5 survives; RF-4); the sortedness of the differing-fields list is untested (H2 survives; RF-5). RF-1 and RF-3
are a three-line change plus one 8-second test in the same untracked file; the lead can fold them into this commit or leave them.

## 1. Files changed by me

None in WS. Only this report and the files under SCR (section 8 lists them).

## 2. Defects found (all minor)

| id | severity | where | what (M unless marked) | fix |
|---|---|---|---|---|
| **RF-1** | minor | `scripts/scale78b/s1_olmo2_7b_check.py:199, 219-220` | `created = not scratch.exists()` is "absent at the start", not "this run created it". A folder that appears between that line and the `finally` is removed. (f1) deterministic: `--scratch-tmp` absent; `check` replaced by a stub that creates `scratch/intruder/data.json` and raises a Refusal → exit 2, the intruder's folder **gone** (`SCR/f1_probes_out.txt`). (f2) realistic, two real CLI runs on the same absent path: run 1 with `--keep`, run 2 started 2.5 s later without → run 1 exit 0 at 6.7 s (record written); run 2 refused "exists and is not empty", exit 2 at 9.0 s, and **the shared folder with run 1's kept list is gone** (`SCR/f2_concurrent_out.txt`). The default `--scratch-tmp` (`<repo>/tmp/scale-78b-s1-olmo2-7b-check`) is the same path for every run, so two concurrent default runs do this. The exposure is only what is created at that path during the run's ~7 s; nothing pre-existing can be lost (sections 3a-3e). | Make `created` atomic: before `try`, `try: scratch.mkdir(parents=True); created = True` / `except FileExistsError: created = False`; `check_output_folders` and `write_new_files` accept the empty folder as they do now. Three lines; the record holds no script hash, so `9b340bf5…` is unchanged. |
| **RF-2** | minor | same file, `main` (`--out` written at :210-213, the cleanup at :219-220) | `--out` inside an absent `--scratch-tmp`: the record is written, the CLI prints `record 9b340bf5… <path>` and exits 0, and the cleanup has already removed the record with the folder (probe (g): `record.json` ABSENT after; `SCR/f1_probes_out.txt`). Pre-existing before the fix; the fix round touched this block. | Refuse before `check()` when `args.out.resolve()` lies under `scratch` (one `Refusal`), or write the record after the cleanup. |
| **RF-3** | minor (test coverage) | `scripts/scale78b/tests/test_s1_olmo2_7b_check.py` | No test covers a pre-existing EMPTY `--scratch-tmp`. My mutants K3 (`was_empty_dir = False`) and K4 (the `elif` removes `scratch` itself instead of `scratch/list`) **survive all 10 tests** (`SCR/mutate_check_f1_out.txt`). K4 deletes a folder that existed before the run, against the docstring's promise (R :21-22). The fixer named this gap (fix-F concern 1). | One test = my probe (a): a pre-existing empty folder, the real edit, `--out` → exit 0, the folder still a directory and empty afterwards, the record written (about 8 s). Kills K3 and K4. |
| **RF-4** | minor (test coverage) | `scripts/scale78b/tests/test_noise_reading_guard_fields.py` (new) against `noise_reading.py:249` | My mutant H5, `read_unit` never reads the guard record (`guard = None`), **survives all 64 noise tests** (`SCR/mutate_reverify_f4_out.txt`). The new reader-level tests replace `read_unit` by monkeypatch and the unit-level tests take dicts, so the path `assets.json` "guard" → unit → `environment_differs` is never exercised; no committed test asserts `guard_record` (M: `grep`). At 7-8B every unit carries a guard record and Part 1 §3.3 names its difference as a trigger, so a regression that drops the guard on read would pass every test. | One assertion through the real `read_unit`: the committed `synthetic_r_unit` writes `{"repo": "g", "revision": "r", "files": {}}` into `assets.json` (R `test_noise_reading.py:583`); assert `read_unit(...)["guard"]` equals it (and, on a wave-0a R unit, `is not None`). Kills H5. |
| **RF-5** | minor (test coverage) | same new file against `noise_reading.py:261` | My mutant H2, the differing-fields list unsorted (`list(...)` over the set), **survives all 64 tests**: every test perturbs one field per unit. With two or more differing fields on one unit (a different pod differs in `gpu`, `capability`, `cudnn`, `cuda_runtime` at once) the list's order follows string-hash set order, which changes between processes, so the record's bytes would not reproduce. | One case: two fields changed on one unit → `[field_a, field_b]` sorted. Kills H2. |

Observations, not defects: (i) an absent scratch under absent parents leaves the parents behind (`k/tmp/a/b` stays, `c` removed; probe (j)); nothing lost. (ii) A dangling symlink as `--scratch-tmp` resolves to its target, which is created and removed; the symlink stays dangling (probe (e)). (iii) verify-F's observation (ii) (a missing sealed builder file gives a traceback, exit 1) stands, as the fixer said.

## 3. F-1: trying to make the check delete a folder it did not create

Driver `SCR/f1_probes.py` (MAIN `-I -B`; imports the fixed module from the copy; runs `main(argv)` in process; prints exit codes, the REFUSED line, the record/verdict lines and folder listings by name only), output `SCR/f1_probes_out.txt`. The second concurrent probe re-ran as `SCR/f2_concurrent.py` with the real environment (the first attempt replaced `HOME`, which hides the offline tokenizer cache and made both runs refuse with `FileNotFoundError`: a harness fault, recorded in section 6 item 9).

| probe | arrangement | result (M) | rule held? |
|---|---|---|---|
| (a) | pre-existing EMPTY folder, real edit, `--out` | exit 0; folder still a directory, EMPTY afterwards (the recovered list removed); record written, `9b340bf5…` | yes |
| (b) | pre-existing NON-EMPTY folder (`keep.json`) | exit 2, "exists and is not empty"; folder and file unchanged; no record | yes |
| (c) | SYMLINK to a non-empty folder | exit 2 (the resolved target named); symlink and target unchanged | yes |
| (d) | SYMLINK to an empty folder | exit 0; target still a directory, empty; symlink intact; record written | yes |
| (e) | DANGLING symlink | exit 0; the target created and removed; the symlink stays (dangling); record written | yes |
| (f1) | path APPEARS during the run (another party's folder with a file), then a refusal | exit 2; the other party's folder **removed** | **no** (RF-1) |
| (f2) | two concurrent CLI runs, same absent path; run 1 `--keep`, run 2 2.5 s later | run 1 exit 0 (record written); run 2 exit 2 (non-empty); the shared folder with run 1's kept list **removed** | **no** (RF-1) |
| (g) | `--out` INSIDE an absent `--scratch-tmp` | exit 0; `record 9b340bf5… <path>` printed; folder and record both ABSENT afterwards | folder yes; record lost (RF-2) |
| (h) | `--scratch-tmp` is an existing FILE | exit 2, "exists and is not empty" (`check_output_folders`'s file rule); the file unchanged | yes |
| (i) | pre-existing empty folder, `--keep` | exit 0; the folder holds `list/s1.json` afterwards (kept, as asked) | yes |
| (j) | absent scratch under two absent parents | exit 0; `c` removed, `a/b` left behind (empty) | yes (litter) |

The records of (a), (d), (e), (i), (j) and (f2)'s run 1 are byte-identical to the verifier's `verify-F-scratch/olmo-check-record.json`
(M: `cmp` ×6; SHA-256 `9b340bf504400576f116e394fa9dd669cff623c0a35e8bb34cdd1c2ee018d2ca`); a copy is `SCR/olmo-check-record.json`.
A `--scratch-tmp` whose resolved path has no `tmp` component is refused by `wae.full_out_ok` before anything is written (R
`scripts/stage1/write_add_edit.py:175-179`; `created` then leaves nothing to remove); not measured, my scratch lies under `/private/tmp`.

**The fixer's tests, measured.** `SCR/mutate_check_f1.py` (MAIN; the copy's folders symlinked, `scripts/scale78b/` copied with one
mutant; the fixer's 10-test file), `SCR/mutate_check_f1_out.txt`: baseline 10 passed. **K0, the unfixed round-3 script** (the fixer's
`s1_olmo2_7b_check.before.py`, SHA-256 `81fef90f…` = build-F's): **2 failed** (the two survival tests), 8 passed → the "fails before,
passes after" claim holds. K1 (`created = True`): KILLED by the same two. K2 (the old cleanup `if scratch.is_dir()`): KILLED by the same
two. K3 (`was_empty_dir = False`): **SURVIVED**. K4 (the `elif` removes `scratch` itself): **SURVIVED** (RF-3).

## 4. F-2 and F-3: the README sentences against the code

The README diff against the fixer's before-copy is exactly the six added lines in "How" item 4 (M: `diff`, `SCR` section 6 item 5);
`build_s1_llama3.py` is untouched (`a2b0a66c…`, section 5). Each sentence checked (R + M, `SCR/f2f3_guard_probe_out.txt`, SCI `-I -B`,
the module loaded from the copy by path):
- "the guard's forbidden folders are those of this script's own checkout and of `--repo` only" — R `guard_out` :211-214: `roots = [REPO.resolve()]` plus `--repo`; M: a fake checkout B's `.ai/inputs/gate-b-sealed-20261008/out/new` is ALLOWED with `repo=None` and REFUSED with `repo=B`. True.
- "run the script from the checkout that holds the sealed folders or pass `--repo`" — follows from the above (I); the verifier measured the CLI's `--repo` refusal (verify-F section 5). True.
- "This S1 folder does not forbid itself" — R `FORBIDDEN_DIRS` :97-99: six folders, its own not among them (M: `any("scale-78b-s1-llama3" in d) → False`). "only its committed `out/` is protected (by the absent-or-empty rule)" — M: `guard_out(<own>/out)` ALLOWED, `check_output_folders(<own>/out)` REFUSED "exists and is not empty" (R `build_s_pool.py:303-309`). "a second output set, or the text-bearing edit, could be written beside it" — M: `guard_out(<own>/out2)` and `guard_out(<own>/tmp/x)` ALLOWED (`<own>/tmp/x` has the `tmp` component `full_out_ok` wants). True.
- "a code change would mean a rebuild and a new arm hash" — R README "Frozen once committed" and the settings' `derived_from.by_sha256` = the script's hash → the record and the edit through `provenance.settings_sha256` (M section 5). True; PP6 says the same.
- "(the lead's ruling PP6 of 5 Nov 2026; verify-F's F-2 and F-3)" — R PP6: "Two scope limits ... recorded in its README (verify-F's F-2 ... F-3)". Matches.
The README's existing sentence that the guard list holds "the three `scale-78b-*` folders of 5 Nov" matches `FORBIDDEN_DIRS` (three such entries, M). The README is not hashed into the set (fix-F section 1; the MANIFEST names the script, record, settings, edit, list, M section 5).

## 5. `build_s1_llama3.py` and `out/` byte-identical to round 3's

M (`shasum -a 256` in WS, twice, before and after my work; and the SCI `-I -B` check of the MANIFEST's embedded hashes):
`build_s1_llama3.py` `a2b0a66c4e3f9f044ad5e2090cd58af195bcdfac3f372822eb1c14805495f5a3` = MANIFEST `script.sha256` = settings `derived_from.by_sha256` = build-F's `final_file_list.txt` = fix-F's `hashes_before.txt`;
`out/MANIFEST.json` `a398627455a96356f590b884ea5acaeae4bedb60a2e44b2bc27a8008b83713e0` (= build-F, fix-F before/after);
`out/add_edit_record.json` `1023b4e6…` = MANIFEST `record.sha256`; `out/write_add_edit_llama3.settings.json` `36a39481…` = MANIFEST `settings.sha256` = record `provenance.settings_sha256`;
WS `tmp/scale-78b-s1-llama3-20261105/edits/add_s1.json` `69426993…` = MANIFEST `files[0].sha256`; `list/s1.json` `389c20ad…` = MANIFEST `list.sha256` (the pin).
The fixer's four files hash as fix-F's table says: check script `03544f45…`, its tests `c9650e28…`, README `a83347f1…`, the new guard-field test file `4a613722…`. `noise_reading.py` (tracked) `94b679ff…`, unchanged by `git diff`.

## 6. F-4: V6, V8 and my hand mutants

Harness `SCR/mutate_reverify_f4.py` (SCI; the copy's folders symlinked, `scripts/scale78b/` copied with one mutant of `noise_reading.py`;
the committed `test_noise_reading.py`, the RV2-2 file and the fixer's new guard-field file), `SCR/mutate_reverify_f4_out.txt`. Baseline 64 passed.

| mutant | result | killed by |
|---|---|---|
| V6 `environment_differs` drops `cudnn` (verifier) | **KILLED** (4 failed) | the new file only: the per-field parametrized test, the cudnn-on-reference test, the no-guard test, the reader-level cudnn test |
| V8 guard comparison `==` for `!=` (verifier) | **KILLED** (28 failed) | the new file only, 10 distinct tests |
| H1 guard compared on its `repo` only | KILLED (10) | the new file: the changed-guard tests and the two reader-level guard tests |
| H1b guard compared on its `files` only | KILLED (10) | the same |
| H2 differing fields not sorted (set order) | **SURVIVED** (64 passed) | nobody perturbs two fields on one unit (RF-5) |
| H3 guard put first, not last | KILLED (1) | the "field and guard together" test |
| H4 a guard-only difference does not set the environment trigger | KILLED (3) | the two reader-level guard tests only (so the reader-level tests carry weight) |
| H5 `read_unit` never reads the guard record (`guard = None`) | **SURVIVED** (64 passed) | the reader-level tests replace `read_unit`; no test reads a guard from `assets.json` (RF-4) |
| H6 `guard_record` flag inverted | KILLED (3) | the reader-level tests' `all(u["guard_record"])` |

So the new file kills both verifier survivors and 5 of my 7 hand mutants; the two survivors are coverage gaps around the new file's edges, not in the fixer's claims.

## 7. All tests of the track, and no text

- MAIN, in the copy: `.ai/inputs/scale-78b-s1-llama3-20261105/tests` + `scripts/scale78b/tests/test_s1_olmo2_7b_check.py` → **27 passed** in 18.2 s (17 + 10; the shell pipe did not capture the exit code; the harness baseline on the same check file → 10 passed, exit 0) (`SCR/pytest_main_s1set_check_out.txt`).
- SCI: `test_fingerprint_compare.py test_noise_reading.py test_noise_reading_rv2_2.py test_noise_reading_guard_fields.py` → **74 passed**, exit 0 (`SCR/pytest_sci_four_out.txt`).
- MAIN, the same four → **72 passed, 2 skipped** (the two scipy tests; MAIN has no scipy), exit 0 (`SCR/pytest_main_four_out.txt`).
- Text (M, `SCR/text_check_rf_out.txt`; run after this report was written): `SCR/text_check_rf.py` (the fixer's form: the 96 row texts read through REQ-7's `read_list` by the pin, `s1common._text_hits` per file) over the fixer's four files, this report and every SCR file outside the copy → **0 hits on the fixer's four files, on this report and on every file I wrote** (scripts, `_out.txt` files, the record copy). Total 288 = 3 × 96, all in three text-bearing files the tested code itself wrote under my scratch: `f1/j/tmp/scratch/list/s1.json` (the recovered list that probe (i) asked to `--keep`) and two tampered-edit copies the fixer's and builder's tests write under pytest's `--basetemp` (`pt-main-1/…/edit.json` ×2). All three removed with the cleanup (section 8 item 16); nothing of them printed. Every CLI line my probes printed was a hash, a count, a verdict, a path or a REFUSED line (M, the `_out.txt` files).

## 8. Commands run (exit status; all foreground; from SCR or the copy)

1. `mkdir -p SCR; date -u` → 0 (18:32:26). The report skeleton written first.
2. Reads (Read tool): the rulings, fix-F.md, verify-F.md, build-F.md, the fixer's four files; `sed`/`grep` of `noise_reading.py`, `write_add_edit.py`, `build_s_pool.py`, `s1common.py`, `test_noise_reading.py`, `gate_b_reading.py`, `build_s1_llama3.py` → 0.
3. In WS (read-only): `git status --short; git diff --stat; git log --oneline -1` → 0 (seven untracked paths, no diff, 953f520); `shasum -a 256` of 13 track files → 0; `ls` of the S1 folder and `tmp/` → 0.
4. `diff fix-F-scratch/README.before.md WS/README.md` → 1 (the six added lines only); `diff fix-F-scratch/s1_olmo2_7b_check.before.py WS/…check.py` → 1 (the docstring sentence, the two `created`/`was_empty_dir` lines with three comment lines, the five-line `finally`).
5. SCI `-I -B -c` MANIFEST embedded hashes vs the files → 0 (all equal); `ls` main checkout: the S1 folder is not there yet (not merged); `scripts/scale78b/` there holds the tracked files only.
6. `rsync -a --exclude .git --exclude __pycache__ WS/ SCR/wsf-copy/` → 0 (114 MB); `shasum` of the copied track files → equal to WS (`SCR/copy_hashes.txt`).
7. MAIN `-B -m pytest -q -p no:cacheprovider --basetemp SCR/pt-main-1 -rs <S1 set tests> <check tests>` in the copy → 27 passed (item 7 of section 7).
8. MAIN `-I -B SCR/f1_probes.py SCR/wsf-copy SCR <edit path>` → 0 (`SCR/f1_probes_out.txt`; its (f2) invalid, see item 9).
9. MAIN `-I -B SCR/mutate_check_f1.py SCR/wsf-copy SCR` (first form, `HOME` replaced) → **1**: the baseline failed, 2 failed, 4 errors, every codec-using test `FileNotFoundError` (the offline HF cache lives under `HOME`); a harness fault, not the script's. The harness fixed to inherit the environment (and K0 added) → 0 (`SCR/mutate_check_f1_out.txt`): baseline 10 passed; K0, K1, K2 KILLED; K3, K4 SURVIVED.
10. SCI `-I -B SCR/mutate_reverify_f4.py SCR/wsf-copy SCR` → 0 (`SCR/mutate_reverify_f4_out.txt`): baseline 64 passed; 7 KILLED; H2, H5 SURVIVED.
11. SCI `-B -m pytest -q -p no:cacheprovider --basetemp SCR/pt-sci-4 -rs <four files>` → 74 passed, 0. MAIN, the same → 72 passed, 2 skipped, 0.
12. SCI `-I -B -c` guard probe (F-2/F-3) → 0 (`SCR/f2f3_guard_probe_out.txt`); the fake checkout B removed by the probe.
13. MAIN `-I -B SCR/f2_concurrent.py SCR/wsf-copy SCR <edit path> 2.5` → 0 (`SCR/f2_concurrent_out.txt`): run 1 exit 0, run 2 exit 2, the shared folder gone.
14. `cmp` of six probe records against `verify-F-scratch/olmo-check-record.json` → all equal; `shasum` → `9b340bf5…`; one copy kept as `SCR/olmo-check-record.json`.
15. In WS after: `git status --short; git diff --stat; git log --oneline -1` → 0, unchanged; `find . -name __pycache__ -not -path "./tmp/*"` → none; `shasum` of the eight track files → unchanged; `date -u` → 18:49:50.
16. After this report: `MAIN -I -B SCR/text_check_rf.py SCR/wsf-copy SCR SCR/../reverify-F.md` → 0 (section 7: 0 hits on everything of mine and the fixer's; 288 in the three text-bearing files the tests and probe (i) wrote). Then the cleanup: a first `rm -rf` with an unmatched `mut-*` glob did not run (zsh `no matches found`); re-run as `rm -rf SCR/wsf-copy SCR/f1 SCR/pt-main-1 SCR/pt-main-4 SCR/pt-sci-4` → 0; SCR is 104 KB afterwards, holding the five `.py` drivers, their `_out.txt` files, `copy_hashes.txt` and `olmo-check-record.json` only (M: `ls`, `du`). `git status --short; git diff --stat` in WS after the cleanup → unchanged. `date -u` → 18:53:05, 18:53:31.
17. The first (failed) form of `mutate_check_f1.py`'s output was overwritten by the re-run (the same output file); its result is recorded in item 9 only. The first (failed) (f2) block is kept inside `SCR/f1_probes_out.txt`.
No git command other than `status`, `diff --stat`, `log` was run. Nothing written under WS, the main checkout or `runkit/`.

## 9. Acceptance criteria (the fixer's list)

| criterion | my result | basis |
|---|---|---|
| F-1 fixed with both tests (a pre-existing non-empty `--scratch-tmp` refused and survives; a folder this run created is removed) | **passed**, with RF-1/RF-2 residues and the RF-3 test gap | section 3: probes (a)-(e), (h)-(j) hold; K0 fails the two survival tests, the fixed script passes; (f1)/(f2)/(g) are the minors |
| the verdict record `9b340bf5…` unchanged | **passed** | six fresh records `cmp`-equal to the verifier's |
| F-2 and F-3 recorded in the README by PP6 (one sentence each, no code change) | **passed** | section 4; `build_s1_llama3.py` hash unchanged |
| F-4's new tests kill V6 and V8 | **passed** | section 6; plus 5 of my 7 hand mutants; H2, H5 survive (RF-4, RF-5) |
| `build_s1_llama3.py` and `out/` unchanged (SHA-256 before and after) | **passed** | section 5: equal to round 3's `final_file_list.txt` and the MANIFEST's embedded hashes |
| all tests pass | **passed** | 27 (MAIN) + 74 (SCI) + 72 + 2 skipped (MAIN) |
| nothing prints or stores text | **passed** | section 7: 0 hits on the fixer's four files, this report and every file I wrote; the three text-bearing scratch files the tests and probe (i) wrote (288 = 3 × 96) were under my scratch's `tmp`/`basetemp` only and are removed |
| no tracked file changed; no git state changed; nothing written outside WS and SCR | **passed** (for the fixer and for me) | section 8 items 3, 15 |
| the `was_empty_dir` branch (fixer's concern 1) | **not tested by any test** (RF-3); measured once by hand, probe (a) | section 3 |

## 10. Jobs for the lead

1. Decide RF-1 and RF-3 before the commit (my pick: take both now; the same untracked file, three lines plus one 8-second test, the record unchanged) or record them as known limits. RF-2 is one `Refusal` line; optional.
2. RF-4 and RF-5: two short additions to the new guard-field test file (a `read_unit`-level guard assertion; a two-field perturbation). Optional before N's reading; they close the edges my mutants H5 and H2 found.
3. Then the fixer's job 1 stands: commit by explicit paths (the fixed check script, its tests, the README, the new guard-field test file, with round 3's other paths); `scripts/stage1/commitments.py check` after.
4. The fixer's concern 1 is answered by measurement: the `elif` removes only `scratch/list` from a pre-existing empty folder (probe (a): the folder survives, empty), so keeping it is safe; what it lacks is the test (RF-3).

## 11. Unresolved concerns

1. RF-1's window is the run's duration at one fixed default path; I measured it with a 2.5 s stagger. A different machine load could make two concurrent default runs both succeed or both refuse; the deletion needs run 2 to reach `check_output_folders` after run 1 wrote the list and before run 1's `--keep` matters (or at any time, for run 1's folder). The fix removes the window rather than relying on timing.
2. The end-to-end guard trigger (an a0 reference WITH a guard record differing from an R unit's) cannot be exercised on this Mac's real data: the Gate A a0 units carry no guard record (R `noise_reading.py:246-248`). The fixer's monkeypatch is the available route; RF-4's `read_unit`-level assertion closes the read side only.
3. The first form of my check-script harness and my first (f2) run failed for a harness reason (`HOME` replaced); both were re-run with the real environment. The failed (f2) block is kept in `SCR/f1_probes_out.txt`; the failed harness output was overwritten by the re-run and is recorded in section 8 item 9 only.
4. The text check's 288 hits were all in files the tested code wrote under my scratch (a kept recovered list, two tampered-edit test copies). Probe (i) (`--keep` on a pre-existing empty folder) necessarily leaves the text-bearing list in the scratch folder; the lead's rule that text lives under `tmp/` only held (`f1/j/tmp/…`), and the folder is removed.
