# Re-verify report, round 2: tracks B and C (adversarial, against fix-BC2.md)

Started 2026-11-05 16:21 UTC; written 16:37 UTC (M: `date -u` read right before each time). Adversarial re-verifier
for GI X (Fable). Default verdict DEFECTS until each claim is proven. Tree under review (read-only for me):
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c`
(detached at `fb51421`, M `git rev-parse HEAD`, before and after). My scratch (124 KB after cleanup, 18 files: five
scripts and their outputs, M `du`):
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/reverify-BC2-scratch/`
Every mutant and every probe ran on a COPY or on a fake layout under my scratch; ws-c and the real sealed folders were
never edited and never an argument of a probe. Tags: M measured (command given), R read (path:line), E estimate,
I inference. Short sentences.

## 0. Verdict: VERIFIED_WITH_MINOR

Every fixer claim I tested holds (M). RV-1 is closed by code and by tests that die under my own mutants of the identity
block (four, each on the case-variant test). The three guards refuse 36 of my 40 probe cases on a fake checkout layout
exactly as expected (case variants, symlinks to the folder, to a parent and to the checkout root, a symlink chain, a
symlink whose target is spelled in another case, dotted and relative paths, a non-default `--repo`, `--repo` spelled in
another case) and pass the 4 controls; the 11 CLI calls refuse with exit 2; nothing was written into any fake forbidden
folder (section 2). The rebuild is intact: my own `-I -B` runs of the three CLIs reproduce the committed `out/` byte
for byte, the 18 OLMo parity files are byte-identical to SEAL and to stage 1's d = 6-10, the independent integrity
reader passes 419 checks, and every MANIFEST and R_d1-R_d3 hash equals the fixer's figure (section 3). The eight RV-2
tests each kill my own mutants (14 of 16 killed, each by its own test; section 4). RV-3's sentence is fixed (section 5).
83 passed, 2 skipped (scipy) in one invocation, exit 0 captured; 33 passed under `.venv`; 38 and 45 + 2 alone (section 6).

Three NEW minor items, none a wrong remove list, a wrong number or a wrong refusal (section 7): (RV2-1) the sealed
wrapper's `--olmo-parity-out must differ from --out` check compares resolved strings, so a case-variant spelling of
`--out` as the parity folder writes 19 parity files over 18 of the 24 listed Llama files in one directory with exit 0
(M; not a sealed folder; the committed-out test, the integrity reader and the engine all refuse such a folder);
(RV2-2) the R4 test does not pin the reference to a0@1101: my mutants with a0@1103 or R@1101 as the reference survive
(M); (RV2-3) the three READMEs say 17 / 9 / 9 tests where pytest collects 18 / 10 / 10 (M). No blocker, no major defect.

## 1. Files I changed

None in ws-c. Only this report and the scratch files under `reports/reverify-BC2-scratch/`.

## 2. The guards (RV-1): my probe on a fake checkout layout (M, `guard_probe.py`, output `guard_probe_out.txt`)

Setup under my scratch (main venv, `-I -B`, removed by the script): `fake/` and `fake2/` hold the three forbidden
folders' NAMES with an `out/` each, a sentinel file in `SEAL/out/R_d1.json` and `STAGE1/length-rules/edits/octile_0.json`;
`fake3/` holds `.ai/inputs/` and no forbidden folder; symlinks `link-seal` -> fake's SEAL, `link-inputs` -> fake's
`.ai/inputs`, `link-repo` -> fake, `link-var` -> `fake/.ai/inputs/GATE-B-SEALED-20261008` (the target string in a case
variant), `link-chain` -> `link-repo`; `hl.json` a hard link to the sentinel inside SEAL; `out-hl/edits/octile_0.json` a
hard link to the stage-1 sentinel inside a pre-made `--out`; `out-sl/edits` a symlink to the stage-1 folder inside a
pre-made `--out`. The filesystem under my scratch is case-insensitive (M).

40 cases × the three `guard_out` functions (sealed `W`, r-draws `B`, H1 `H`), each as expected:

| group | cases | sealed / r-draws / h1 |
|---|---|---|
| case variants (deep, the folder itself, `SEAL/out`, `.ai/INPUTS` into stage 1, `Gate-B-Anchors`, several absent components) | 6 | REFUSED ×18 with the folder's name |
| symlinks (to the folder; the folder itself as `--out`; to a parent; to a parent + case after it; the checkout root in `--out`, as `--repo`, in both; root + case; a case-variant target; a chain; a chain + case) | 11 | REFUSED ×33 |
| dotted (plain, + case, into anchors) | 3 | REFUSED ×9 |
| relative with `monkeypatch`-style `chdir` (plain, + case, dotted, cwd = the symlinked root + case, `--repo ..` from a subfolder) | 5 | REFUSED ×15 |
| non-default `--repo` (fake2 exact, fake2 case variant, `--repo` spelled `FAKE` with `--out` exact and case variant, fake3 exact string) | 5 | REFUSED ×15 |
| the parent of `--out` is a file inside SEAL | 1 | REFUSED ×3 |
| fake2 as `--repo` aimed at fake's SEAL (fake is neither REPO nor `--repo`) | 1 | PASS ×3 (correct: not a root) |
| fake3 (no forbidden folder exists) with a case-variant spelling | 1 | PASS ×3: the fixer's stated limit (concern 2); no inode to compare and nothing sealed to protect |
| a hard link to a file inside SEAL as `--out` | 1 | sealed, r-draws: `NotADirectoryError` from the non-empty check (not a Refusal); h1: PASS (see below) |
| a pre-made `--out` holding a planted hard link / a planted symlink | 2 | sealed, r-draws: REFUSED (non-empty); h1: PASS, then `s1.write_new_files` REFUSED both ("a sealed output never overwrites") |
| controls (sibling with a shared prefix, an ordinary new folder, relative ordinary, fake3 ordinary) | 4 | PASS ×12 |

CLI (`main`) on the fake checkout, 11 calls: the case variant through `--repo fake`, through `link-repo`, through
`link-chain` + case, `--repo FAKE` + exact `--out`, the parity folder as a case variant: exit 2, stderr `REFUSED:
refusing to write under .ai/inputs/gate-b-sealed-20261008 (nothing written)` each; `--out` = the hard link: the two
wrappers raise `NotADirectoryError`, H1 raises `FileNotFoundError` from `build` (no Refusal, nothing written); H1 with
the pre-made folder holding a planted hard link: `FileNotFoundError` from `build` (nothing written). The write functions
on the hard link: `W.write_files` / `B.write_files` raise `FileExistsError` (`mkdir` on a file), `s1.write_new_files`
raises `NotADirectoryError`; on the pre-made folders `s1.write_new_files` refuses. After everything: the fake checkout's
files unchanged (hash walk), the hard-linked inode and content unchanged, no new entry under the probe root, `SEAL/out`
holds the sentinel only (M). Observation, not a defect: a FILE as `--out` ends in a traceback (exit 1), not a Refusal
(exit 2); nothing is written either way.

Code (R): the three `guard_out` bodies are identical modulo the Refusal class (M `diff` of the bodies: r-draws == h1;
sealed == r-draws apart from the `build`/`main` text the `sed` range caught). Against the fixer's saved originals
(`fix-BC2-scratch/orig-scripts/`, which hash to last round's `227aed4f…` / `5cd1036d…` / `504e9462…`, M), each script
differs in 12 lines in exactly four hunks: `import os`, the docstring, the anchor walk, the identity refusal (M `diff`
hunk list: sealed 45a46 / 418c419,423 / 422a428,430 / 427a436,437; r-draws 32a33 / 190c / 194a / 199a; H1 25a26 / 106c
/ 110a / 115a). Nothing else changed.

My own mutants of the identity block (section 4, harness): the parents dropped from the walk (sealed), string equality
in place of `samefile` (r-draws), the ancestor walk removed (H1), the identity refusal dropped (sealed): KILLED ×4, each
on `test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder` (DID NOT RAISE) plus the script-hash test; the
H1 one also fails the symlink test and the two older guard tests (a `FileNotFoundError` inside `pytest.raises`).

## 3. The rebuild (M)

- Hashes equal the fixer's report, every one (`shasum -a 256` in ws-c): Llama sealed `out/MANIFEST.json`
  `2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c`; OLMo d = 11-16 `22858dbfe40e83f970bc8a96c51684b80b9cc494945a904ee6bc6e03ea1acb28`;
  H1 `24c1305ab59e979feb8eb88dc3977ada132cad082f41449d4acde20f2bcdda61`, `octile_0.json` `9a01637ec63dc38f6e4dec646a0bc4b8c00c36521fa8831fe4fb87e8df3a1c5f`;
  R_d1 `5cdedf22c1002ef1c6d0322d44c253ef57580ddb1dda85e8119a8b3842dc29b4`, R_d2 `8f9f3cd5027d9268b28e3cf4189987a820b26a6d6d77fbe83ea0ad145944bb95`,
  R_d3 `edbc111b2ff3a446ae195a79f0e5965c9a82fa744266d57c9c15e4c4c775dd2e` (arms `edit-<these>`: the integrity reader's arm
  check); scripts `1ca6cdb4…` / `18f2fec8…` / `26f2f2a1…`; unchanged `noise_reading.py` `94b679ff…`, `make_recipe_s78.py`
  `fcf01955…`, `g1_check_78b.py` `251ddb32…`, the G1 record `8c3579e4…`. MANIFEST mtimes 2026-11-05 16:04:35 UTC (`stat`).
- `integrity_rv2.py` (byte-identical to last round's `integrity.py` and to the fixer's `integrity_copy.py`, M `cmp`;
  stdlib, `.venv -I -B`): `wrapper hashes 1ca6cdb4 18f2fec8 26f2f2a1`, **OK 419 FAILS 0** (`integrity_out.txt`). It
  checks, for all 24 + 6 + 1 edit files: SHA-256 == the MANIFEST's, arm == `edit-<sha256>`, the embedded
  `builder_sha256` / `scale78b_wrapper.script_sha256` / `script_sha256` == the script's bytes in ws-c, the seal fields
  (`kind`, `edit_kind`, manifest), empty `rewrite`/`add`, counts, 600 sorted distinct rows, 75 per unit against the
  prepared set's dev groups (ids only), selection family/draw and seed 1100 + d, the MANIFEST record's seed/draw/family,
  Llama R_d1-5 == SEAL's lists with the `same_rows_as` hashes, R_d6-10 == stage 1's, R_d11-16 == the OLMo d = 11-16
  lists, 16 distinct draws, unit files == group members == SEAL's unit files, the r-draws reproduction flags, H1's
  stage-1 pin, the G1 record's three embedded hashes.
- The three CLIs re-run by me with `-I -B` into my scratch (main venv; `--olmo-parity-out` for the sealed one): exit 0
  ×3; the builds print `builder sha256 1ca6cdb4…` / `script sha256 18f2fec8…`, engine `472fc7f6…`, MANIFEST
  `2a1db220…` / `24c1305a…`; `diff -r` against the committed `out/`: **IDENTICAL ×3** (25, 7, 2 files).
- Parity: `cmp` byte-identical for SEAL's R_d1-R_d5 and 8 unit files and for stage 1's R_d6-R_d10: **18 of 18**;
  PARITY.json `byte_identical: True` ×13 sealed, `(byte_identical, stage1_wrapper_rederived, remove_list_equal,
  equal_without_stage1_wrapper) == (True, True, True, True)` ×5 for d = 6-10; the parity test
  `test_c_olmo_parity_reproduces_stage1_d6_to_d10` passed in every run (section 6).
- Text walk (`textwalk_rv2.py`, a copy of last round's, `.venv -I -B`): 36 JSON files, no string with a newline, the
  longest 415 characters at `/position_rule` (the engine's rule sentence), MANIFESTs 229 / 199 / 242, no suspicious key
  (`textwalk_out.txt`).
- The fixer's harness output (`fix-BC2-scratch/mutate_fix2_out.txt`, R): baselines 28 / 14 / 38; RV-1a/b/c and the eight
  RV-2 mutants KILLED, each by its own test. Consistent with my own harness (section 4).

## 4. RV-2 and RV-1 by my own mutants (M, `mutate_rv2.py`, output `mutate_rv2_out.txt`)

Harness as last round's (a scratch root reaches ws-c's engine, research, tmp and committed `.ai/inputs` folders by
symlink; `scripts/scale78b/`, the Llama sealed folder, SEAL and the anchor folder are copied; one mutant per run; the
same pytest command on baseline and mutant; KILLED = exit non-zero, named failed tests, no errors; "own" = the test
written for the gap is among the failures). My replacement text differs from the fixer's except where noted. Baselines:
noise 28 passed (`.venv`), maker 14, B 38 (main venv), exit 0 ×3.

| id | my mutant | result |
|---|---|---|
| RV1-x1 | sealed: identity checks the anchor only, not its parents | KILLED, own (case-variant test, DID NOT RAISE) + hash test |
| RV1-x2 | r-draws: `p == target` in place of `samefile` | KILLED, own + hash test |
| RV1-x3 | H1: the ancestor walk removed (anchor = out, absent) | KILLED, own + symlink test + the two older guard tests + hash test (5) |
| RV1-x4 | sealed: the identity refusal dropped | KILLED, own + hash test |
| C-D3b-a | maker: only the `complete` check dropped | KILLED, own (`test_anchor_records_skips_an_incomplete_or_foreign_record`) |
| C-D3b-b | maker: only the `kind` check dropped | KILLED, own |
| C-D4b-a | noise: the pre-read duplicate refusal never fires | KILLED, own (+ the two older duplicate tests) |
| C-D4b-b | noise: duplicate key = the path (the fixer's mutant, replicated) | KILLED, own (the copy is read; its message differs) |
| R2 | noise: `edit_kind` only has to be present | KILLED, own |
| R3 | noise: edit.json's hash compared with itself | KILLED, own |
| R4-a | noise: the environment reference is a0@1103 | **SURVIVED** (28 passed) |
| R4-b | noise: the environment reference is R@1101 | **SURVIVED** (28 passed) |
| R5-a | noise: `hex64` lower-cases before matching | KILLED, own |
| R5-b | noise: `hex64` accepts 63-65 digits | KILLED, own |
| G1-a | r-draws: non-empty means two or more entries | KILLED, own (DID NOT RAISE) + hash test |
| G3-a | H1 CLI guards with REPO, ignoring `--repo` | KILLED, own + case-variant test + hash test |

14 of 16 killed by their own test; the two survivors are one gap (RV2-2, section 7). Basis (M, `r4_probe.py`, output
`r4_probe_out.txt`, the real reader on the wave-0a and Gate A units): the six units share one environment (no
perturbation: every `differs` list empty, trigger False, governing plain), so the fixer's test, which perturbs a0@1102
only, is passed by any reference other than a0@1102. With a0@1101 itself perturbed under the real code the attribution
is `a0@1101: []` and `["gpu"]` on each of the five others (trigger True, governing fallback, σ_F 2.16); under a
reference of a0@1103 or R@1101 it would be `["gpu"]` on a0@1101 only (I from `environment_differs`, R
`noise_reading.py:258-264`). That is the assertion a stronger test needs.

## 5. RV-3 (M grep, R)

`.ai/inputs/scale-78b-sealed-llama3-20261105/README.md:54-55`: "(d) the engine's `parse_edit` accepts each Llama file
against the Llama set and refuses it against the OLMo set, on id-only `engine_stub()` views of both sets (never the
engine's `load_prepared`, which reads prompt text)". `load_prepared` appears in that sentence only, in all three READMEs.
The new hashes are named in the three READMEs; the superseded ones (`ba524373…`, `189275c0…`, `29347da2…`, `9204121a…`,
`227aed4f…`, `5cd1036d…`, `504e9462…`) appear only in the labelled history lines (README lines 10 / 9 / 8).

## 6. Test runs (M; ws-c root; `PYTHONDONTWRITEBYTECODE=1 <python> -B -m pytest -q -p no:cacheprovider --basetemp=<my scratch>`; exit codes captured by `echo EXIT=$?` after each run, outputs kept as `pytest_*_out.txt`)

| run | python | result |
|---|---|---|
| B and C together in ONE invocation: `.ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests -rs` | main venv | **83 passed, 2 skipped (scipy) in 4.42s, exit 0** |
| noise + G1: `test_noise_reading.py test_g1_check_78b.py -rs` | `.venv` | **33 passed in 3.83s, exit 0** |
| B alone: the sealed tests + `test_build_r_draws_78b.py` + `test_build_h1_llama3.py` | main venv | 38 passed in 0.88s, exit 0 |
| C alone: `test_make_recipe_s78.py test_noise_reading.py test_g1_check_78b.py -rs` | main venv | 45 passed, 2 skipped in 4.34s, exit 0 |

Collected per file (`--collect-only`, M): sealed 18, r-draws 10, H1 10, noise 28, maker 14, G1 5 = 85 = 83 + 2 skipped.
The three B files have no `parametrize` (M grep: 0), so these are plain test functions. After every run: no
`__pycache__`, no `.pytest_cache` in ws-c outside `tmp/` (M `find` → 0); the basetemps were under my scratch and are
deleted.

## 7. Defects found (all minor; none in a remove list, a hash, a count or a refusal of the default path)

| id | severity | where | what (M unless marked) | fix |
|---|---|---|---|---|
| RV2-1 | minor | `build_sealed_llama3.py:596-597` (`main`) | `--out <scratch>/Out --olmo-parity-out <scratch>/out` on this Mac: both `guard_out` calls pass (both absent), `args.olmo_parity_out.resolve() == args.out.resolve()` is False (resolve keeps the typed case), so `write_files` writes the 25 Llama files and then the 19 OLMo parity files into the SAME directory: exit 0, "built 25 files", 26 files on disk, and 18 of the 24 MANIFEST-listed files hold other bytes than their records (R_d1 on disk = SEAL's `f7d7eb86…`, MANIFEST says `5cdedf22…`) (`collide_out.txt`). The same string-comparison weakness as RV-1, on the parity check. Not a sealed-folder write; the output is in a folder the operator named. Bounded: the committed-out test and the integrity reader fail on such a folder, and the engine's `parse_edit` refuses the OLMo files against the Llama set (test (d)). The default use and the lead's build command (distinct scratch paths) are unaffected. | Lead's call, as with RV-1 last round. (a) Record the limit in the sealed README (one sentence; not hashed; no rebuild): "`--olmo-parity-out` must be a different folder; a spelling that names the same folder in another case is not refused". (b) Fix in code: create both folders first, then refuse if `os.path.samefile(out, parity)`; a byte change, so a third rebuild into empty `out/` and new arm hashes and pins. My pick: (a), because the output is caught by every downstream check and a rebuild changes the pins again; (b) if the lead wants the wrapper itself to refuse. |
| RV2-2 | minor | `scripts/scale78b/tests/test_noise_reading.py:656-674` (the R4 test) | The test pins "the reference is not a0@1102", not "the reference is a0@1101": my mutants with a0@1103 or R@1101 as the reference survive (section 4), because the six wave-0a / Gate A units share one environment and only a0@1102 is perturbed. The production line `reference = units[("a0", SEEDS[0])]` (R `noise_reading.py:328`) is right. | Test only, no hash change: add a second perturbation of a0@1101 in the same test and assert `environment_differs == {"a0@1101": [], "a0@1102": ["gpu"], "a0@1103": ["gpu"], "R@1101": ["gpu"], "R@1102": ["gpu"], "R@1103": ["gpu"]}` (measured on the real code, `r4_probe_out.txt`). Both of my survivors then fail (I). |
| RV2-3 | minor | the three READMEs: sealed `:47`, r-draws `:34`, H1 `:33`; fix-BC2.md `:37-39` | "17 tests" / "9 tests" / "9 tests"; pytest collects 18 / 10 / 10 (no `parametrize`). The fixer's own total 38 = 18 + 10 + 10 is right; the per-file numbers are each one short (the two RV-1 tests were added to files that already held 16 / 7 / 7, not 15 / 6 / 6). | Three numbers in the READMEs (not hashed; no rebuild). |

Observations, not defects: a FILE as `--out` (a hard link to a sealed file) ends in `NotADirectoryError` /
`FileNotFoundError` (exit 1, traceback) rather than a Refusal (exit 2); nothing is written and the linked inode is
untouched. A `--repo` whose forbidden folders do not exist is covered by the string comparison only (the fixer's
concern 2; nothing sealed exists there). The forbidden list is the three committed folders of round 1's B-M2; the three
new `scale-78b-*` folders are protected by the non-empty rule once their `out/` is committed, not by name (a scope the
lead set in round 1; a name change would be a byte change).

## 8. Commands run (every one; exit 0 unless stated; all foreground; the longest the harness at about 2 min)

1. `date -u` ×3 (16:21, 16:37 UTC and once between); `mkdir` scratch; `ls` of the reports folder; `git -C ws-c rev-parse HEAD`, `status --porcelain [-uall]` before and after (six `??`, 54 files, 0 modified, `fb51421`); `find __pycache__ / .pytest_cache` in ws-c → 0 (×2) and in the reports folder → 0.
2. Reads (Read/sed/grep/cat): fix-BC2.md, reverify-BC.md, the addendum; the three build scripts (headers, constants, `guard_out`, `write_files`, `main`, H1 in full); `write_atomic` (`experiments/minimal_safety/common.py:33-41`), `s1common.write_new_files` (:605-618), `Refusal`; the six test files (headers, the RV-1 and RV-2 tests, the helpers); `noise_reading.py` (`hex64`, `r_edit_matches`, `read_unit` :180-215, `family_reading` :300-335, `environment_differs`); `make_recipe_s78.py` (`anchor_records`, `anchored_to`); the three READMEs' hash, test-count and RV-3 lines; last round's `mutate_rv.py`, `integrity.py`, their outputs; the fixer's `mutate_fix2_out.txt`; `ls .ai/inputs`.
3. `shasum -a 256` of the 3 MANIFESTs, `octile_0.json`, R_d1-R_d3, 3 scripts, 3 track-C scripts, the G1 record, the fixer's `orig-scripts/`; `TZ=UTC stat` of the MANIFESTs.
4. `cp integrity.py` → `integrity_rv2.py`; `cmp` against the fixer's copy (identical); `.venv -I -B integrity_rv2.py <ws-c>` → OK 419 FAILS 0.
5. pytest ×4 (section 6), exit codes captured; `--collect-only -q` ×6; `grep -c parametrize` ×3.
6. main venv `-I -B guard_probe.py <ws-c> <scratch>` → 40 cases × 3 guards, 11 CLI calls, 5 write-function calls; the probe root removed by the script.
7. main venv `-I -B` × the three CLIs into `<scratch>/cli/` (sealed with `--olmo-parity-out`) → 0, 0, 0; `diff -r` ×3 IDENTICAL; `cmp` ×18 parity files → 18 identical; `.venv -I -B` PARITY.json flags.
8. main venv `-I -B build_sealed_llama3.py --out <scratch>/collide/Out --olmo-parity-out <scratch>/collide/out` → exit 0 (RV2-1); `ls`, `find | wc`, `shasum`, `.venv -I -B` MANIFEST-vs-bytes count (18 of 24 differ).
9. `.venv -I -B mutate_rv2.py <ws-c>` → 3 baselines pass, 16 mutants (14 KILLED by their own test, 2 SURVIVED); the harness root and basetemp removed by the script.
10. `cp textwalk.py` → `textwalk_rv2.py`; `.venv -I -B textwalk_rv2.py <ws-c>` → 36 files.
11. `diff` of the guard bodies between the three scripts; `diff` of each script against the fixer's saved original (hunk lists, line counts).
12. `.venv -I -B r4_probe.py <ws-c> <scratch>` → the attribution under four single-unit perturbations and none (section 4); its folder removed by the script.
13. `git -C /Users/spiderishi/Coding/attribution status --porcelain | grep -c` my paths → 0 (read only); `rm -rf` of my `cli/`, `collide/`, `pytest-tmp-*`; `ls`, `du` → 124 KB.

Not run: any pod, network, install, download, agent, message; any write in ws-c or the main checkout (reads by absolute
path only); any git state change; the engine suite (the engine is untouched: ws-c's `git status` shows no tracked change;
round 1's 837 passed stands). No forbidden folder opened; the prepared sets were read by the frozen code and the id-only
views only; the unit folders by the frozen reader (counts and aggregates); every print was a verdict, a path, a count
or a hash.

## 9. Acceptance criteria

| criterion | result | evidence |
|---|---|---|
| each of the three guards tried hard on a fake layout: case variants, symlinks (folder, parent), dotted, relative, non-default `--repo`, a hard link to a file inside the folder, a path through a symlinked parent | passed (no bypass into a forbidden folder) | section 2: 40 cases × 3, 11 CLI calls, nothing written |
| every embedded script SHA-256 equals the bytes in ws-c | passed | integrity 419/0 (`wrapper hashes 1ca6cdb4 18f2fec8 26f2f2a1`); the committed-out tests; my `diff -r` IDENTICAL ×3 |
| d = 6-10 parity holds | passed | `cmp` 18/18; PARITY flags; the parity test in every run |
| membership and manifest binding hold | passed | integrity 419/0 (75 per unit, 600 sorted distinct, the seal fields, the manifest records) |
| the MANIFEST and R_d1-R_d3 hashes the fixer returned match the files | passed | section 3, `shasum` equal in every digit |
| RV-2's eight tests checked by my own mutants | passed with one gap | 14 of 16 killed by their own test; R4-a/b survive (RV2-2) |
| RV-3's sentence | passed | section 5 |
| the whole B+C set in one invocation and alone | passed | 83 passed 2 skipped exit 0; 38; 45 + 2; 33 under `.venv` (exit 0 each) |
| any new defect reported | three minor | section 7 |
| no git state changed; nothing written outside my scratch | passed | HEAD `fb51421`, six `??` / 54 / 0 modified before and after; no caches; none of my paths in the main checkout's status |

## 10. Jobs for the lead

1. **Decide RV2-1 before the first commit** (frozen-on-commit, addendum A3): record the limit in the sealed README (not
   hashed, no rebuild; my pick) or fix the parity check by identity (a byte change: a third rebuild into empty `out/`,
   new arm hashes and pins, a short re-verify). The committed `out/` is correct either way (section 3).
2. **Optional, test and README only, no hash change:** RV2-2 (one more perturbation and one assertion in the R4 test;
   the expected dict is in section 7) and RV2-3 (three numbers: 18 / 10 / 10).
3. **Merge from ws-c by explicit paths** as fix-BC2.md job 1 says (54 new files, `git status --porcelain -uall`); commit
   each hashed script with its `out/`.
4. **After the merge, in the main checkout:** fix-BC2.md job 2's two pytest commands (expect 83 passed 2 skipped; 33
   passed), `scripts/stage1/commitments.py check`, the engine identity `472fc7f6…`.
5. **Pins and records:** the kit's Llama MANIFEST pin `2a1db220…`; N's Llama R arms `edit-5cdedf22…`, `edit-8f9f3cd5…`,
   `edit-edbc111b…` (R_d1-R_d3), each taken from the Llama MANIFEST; replace any record that cites the fix-round values
   (reverify-BC.md §5 and §12 cite them, historical).
6. Delete `reports/reverify-BC2-scratch/` (124 KB) once read, with `fix-BC2-scratch/`, `fix-BC-scratch/` and
   `reverify-BC-scratch/`.

## 11. Unresolved concerns

1. RV2-1 is the lead's call and the only item that could change a hash again. A later fix is impossible without breaking
   the committed provenance; a fix now costs one more round. The default path is correct and the inconsistent output is
   refused downstream (M), which is why I pick recording the limit.
2. The R4 test gap (RV2-2) is test strength only; the reader's reference is right (R). The seed rule's attribution matters
   only when an environment differs, which on wave 0a it does not (M).
3. A `--repo` whose forbidden folders do not exist yet is covered by the string comparison only (the fixer's concern 2,
   confirmed on fake3). Nothing sealed can exist there, so I do not count it.
4. The three new `scale-78b-*` folders are not in the forbidden list by name; their committed `out/` is protected by the
   non-empty rule only, and a NEW subfolder beside `out/` is not refused. Round 1 set the list; adding names is a byte
   change. Stated for the record.
5. Byte parity for d = 6-10 depends on the environment (Python 3.11.15, numpy 2.2.6); it held here (M).
6. The main checkout's `git status` shows the lead's own modified and untracked files; none of my paths (M, grep count 0).
   I wrote nothing there.
