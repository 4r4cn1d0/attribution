# Verify report: Track B = T3 (the Llama sealed set; the OLMo draws d = 11-16; H1 on the Llama manifest)

Started 2026-11-05 14:03 UTC; written 14:19 UTC (`date -u` before each time; M). Adversarial verifier for GI X (Fable).
Verifier worktree: `/Users/spiderishi/Coding/attribution/.claude/worktrees/pensive-stonebraker-bf6d79` (nothing written there).
Builder worktree (ws-b, detached at `fb51421`, M `git rev-parse`):
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-b`
Builder report: `.../scratchpad/b78/reports/build-B.md`. My scratch: `.../scratchpad/b78/reports/verify-B-scratch/`.
Tags: M measured (command given), R read (path:line), E estimate, I inference. Short sentences.

## Verdict: VERIFIED_WITH_MINOR

Every remove list, seed, provenance field and manifest hash that the builder claims was recomputed independently and
agrees (M: 562 + 31 checks, 0 failures; sections 3 and 5). The trap test is killed by two mutants (M). The CLI re-runs
of all three scripts give the committed `out/` folders byte for byte (M). No blocker, no major defect. Three minor
items (section 6), none of which changes a remove list; two of them would change hashes if fixed, so the lead decides
before the first commit. One placement question for the lead (section 8, item 1).

## 1. Files changed

None of the builder's files edited. Nothing written in ws-b or the main checkout (M: `git -C ws-b status --porcelain`
unchanged before and after; no `__pycache__`, no `.pytest_cache`; pytest ran with `-B -p no:cacheprovider --basetemp`
in my scratch). New files by me, all under `verify-B-scratch/`: `recompute_r.py`, `recompute_r.out`, `recompute_h1.py`,
`recompute_h1.out`, `mutation.out`, and this report. The bulky scratch copies (CLI outputs, mutant repos, pytest temp)
were deleted after the evidence was recorded (68 KB remain; M `du`).

## 2. Alternatives considered

1. **Trust the builder's tests or recompute.** Recomputed: my own draw (sha256-derived seed,
   `random.Random(seed).sample(sorted(members), 75)`, sorted union) from my own readers of both prepared sets (row_id,
   target_tokens, groups only), compared with BLD's `draw_r` loaded by path, with every Llama file, with SEAL (d = 1-5,
   units), with stage 1 (d = 6-10) and with the OLMo d = 11-16 files. Chosen because the task asks for it and because a
   shared bug in BLD's call path would hide from a BLD-only check.
2. **parse_edit with the engine's `load_prepared` or with id-only stubs.** Stubs: `load_prepared` reads
   `engine/query_rows.jsonl` (prompt text) into memory (R `experiments/safety_selection/prepare.py:950`), which the
   track's frozen code never opens. The stubs hold exactly what `parse_edit` reads (R `edits.py` parse_edit:
   `manifest_sha256`, `train_rows` keys, `groups`). See minor item 1.
3. **Mutation of the trap test: one or two mutants.** Two: (1) the member-list refusal removed, (2) `build()` no longer
   calls `check_membership`. Both killed; (2) shows the fallback refusal (the unit-file check) carries a different
   message, so the test's regex is specific to the membership path.
4. **H1 by importing stage 1's `length_order` or by my own code.** My own: the registry entry `length.order` read from
   `scripts/stage1/labels.json` directly, the rank by `random.Random(sha256-seed).shuffle(sorted(ids))`, the order by
   `(target_tokens, rank)`.

## 3. Commands run (ws-b root unless stated; `PY` = `tmp/minimal-experiment-20261002/venv/bin/python`; all foreground, each under 2 min)

| # | command | exit / result |
|---|---|---|
| 1 | `date -u`; `mkdir` scratch; `ls` reports; reads of the rulings, plan T3, check C5/C6, build-B.md | 0 |
| 2 | `git status --porcelain`, `git rev-parse HEAD`, `find` new files and `__pycache__` in ws-b | 0: four `??` folders; HEAD `fb51421`; no pycache |
| 3 | Reads (Read/sed/cat/grep): `build_sealed_llama3.py`, BLD, `edits.py`, the 3 test files + conftests, READMEs, `build_r_draws_78b.py`, `build_h1_llama3.py`, `scripts/stage1/{build_r_draws,build_length_rules,s1common,commitments}.py`, both stage-1 settings, `labels.json` entry, `prepare.py` load_prepared, `minimal_safety/common.py` | 0 |
| 4 | `shasum -a 256` of both prepared manifests, BLD (committed and tmp copies), SEAL MANIFEST, stage-1 record and settings, the wrapper, the 3 MANIFESTs, `octile_0.json`, stage-1 scripts | 0 (values in section 4) |
| 5 | `.venv/bin/python -I -B` prints of the 3 MANIFESTs, SEAL's file list, stage 1's record, the keys/provenance of 6 edit files (ids, hashes, counts only) | 0 |
| 6 | `PY -B -m pytest -q -p no:cacheprovider --basetemp=<scratch> .ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests` | `27 passed in 0.79s` (exit code not captured through the pipe; the summary line is the evidence) |
| 7 | `PY -I -B verify-B-scratch/recompute_r.py <ws-b>` | 0; `562` ok lines, `FAILS: 0` (`recompute_r.out`) |
| 8 | mutant repos: symlinked `experiments/`, `tmp/`, `scripts/stage1`, SEAL, stage-1 folder; copies of the wrapper and tests; mutations applied by a Python replace (diffs in `mutation.out`) | 0 |
| 9 | mutant 1: `PY -B -m pytest -q -p no:cacheprovider --basetemp=... <mut1>/.ai/inputs/.../tests -k test_e_` | `1 failed, 14 deselected`: `DID NOT RAISE Refusal` (killed) |
| 10 | mutant 2: the same in `<mut2>` | `1 failed`: regex `member lists differ` did not match `unit g-17e0...: the member list differs from the sealed unit file` (killed) |
| 11 | `git status --porcelain=v1 -uall --ignored -- <4 folders>`; `git check-ignore -v` on 5 new files | 46 `??`, 0 `!!`; check-ignore exit 1 (none ignored) |
| 12 | `grep` of every write path in the 3 scripts; `s1.write_new_files`; `write_atomic` | 0 (section 5, "never writes under SEAL") |
| 13 | `PY -I -B verify-B-scratch/recompute_h1.py <ws-b>` | 0; `31` ok lines, `FAILS: 0` (`recompute_h1.out`) |
| 14 | `PY -I -B .ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py --out <scratch>/cli-out --olmo-parity-out <scratch>/cli-parity`; `diff -r` against the committed `out/`; `cmp` of the 18 parity files against SEAL and stage 1; PARITY.json fields | 0; `IDENTICAL`; 13 SEAL files and 5 stage-1 files byte-identical; `byte_identical: True, stage1_wrapper_rederived: True` x5 |
| 15 | `PY -I -B scripts/scale78b/build_r_draws_78b.py --out <scratch>/cli-r`; `diff -r` | 0; `IDENTICAL` (MANIFEST `da634837...`) |
| 16 | `PY -I -B scripts/scale78b/build_h1_llama3.py --out <scratch>/cli-h1`; `diff -r` | 0; `IDENTICAL` (`189cd139...`, `fdd35004...`) |
| 17 | `shasum` BLD after all runs; `git status --porcelain` after all runs | `80cb8944...` both copies; status unchanged |
| 18 | `PY -B -m pytest -q -p no:cacheprovider --basetemp=... experiments/safety_selection/tests --ignore=experiments/safety_selection/tests/test_ss_gateb_runkit.py` | `837 passed, 5 skipped, 1 warning in 79.07s` |
| 19 | `grep` of the plan for T7, "R_4", "step 3"; of P78 for section 9.2 items 2-3 | 0 (citations hold; section 5) |
| 20 | `PY -I -B scripts/stage1/commitments.py check --repo .` (ws-b, reads HEAD only) | 0: `OK: 140 entries ...; HEAD fb51421...` (baseline) |
| 21 | `rm -rf` of the scratch copies; `du`; `date -u` | 0 |

Not run: any pod, network, install, download, agent, message; nothing in the main checkout; no git state change.

## 4. Evidence paths and measured hashes (M, `shasum -a 256`)

- `verify-B-scratch/recompute_r.out` (562 checks), `recompute_h1.out` (31 checks), `mutation.out` (the two diffs and results).
- BLD `80cb8944...` (committed copy and `tmp/gate-b-sealed/` copy; before and after every run). OLMo manifest `9ed61826...`;
  Llama manifest `c52a50af...`. SEAL MANIFEST `d76d8bf9...`; stage-1 `r_draws_record.json` `c09b20c1...`; stage-1
  `octile_0.json` `f5b1762f...`. Wrapper `5cd45926...`; Llama MANIFEST `76415c42...`; `build_r_draws_78b.py` `25dd7aca...`;
  r-draws MANIFEST `da634837...`; `build_h1_llama3.py` `8b00a67b...`; H1 MANIFEST `189cd139...`; `octile_0.json` `fdd35004...`.
  Engine identity `472fc7f6...` (M `code_identity()`); `derive_seed` source `f03231c9...` (M `inspect.getsourcelines`).
- Both sets: `engine/groups.json` byte-equal (`ab055eb8...`), members already sorted in the raw file; Llama
  `train_rows.jsonl` `a096cc66...`, OLMo `1efa8571...`; 4,800 rows; 100 rows differ in `target_tokens` (M).

## 5. Acceptance criteria (the builder's claims re-checked)

| criterion | my result | evidence (M unless marked) |
|---|---|---|
| (a) Llama remove lists = SEAL's, d = 1-5 and 8 units | passed | recompute_r: each Llama `R_d1-5` remove == my draw == SEAL's remove and per-unit seeds; each unit file == the sorted Llama group members (600) == SEAL's unit file; categories match the manifest |
| (b) Llama `R_d6-R_d10` = stage 1's (C5) | passed | recompute_r: == my draw == stage 1's remove; record seeds 1100 + d; `same_rows_as` paths and hashes equal the real files |
| (c) OLMo parity byte for byte: SEAL d = 1-5 + units; stage 1 d = 6-10 | passed | cmd 14: 13 + 5 files `cmp` identical; PARITY.json `stage1_wrapper_rederived: True` |
| (d) `parse_edit` accepts each Llama file on the Llama set, refuses on the OLMo set | passed | recompute_r: 24 files accepted on an id-only Llama stub (removed set and arm equal), refused on the OLMo stub with the `manifest_sha256` message; the 6 OLMo d = 11-16 files the other way round; H1 likewise (recompute_h1) |
| (e) trap: one member moved makes the wrapper refuse | passed, and the test is real | cmds 6, 9, 10: passes unmutated; fails on both mutants |
| (f) BLD's bytes unchanged | passed | cmd 17 |
| (g) a re-run gives the same bytes | passed | cmds 14-16: `diff -r` identical for all three `out/` folders |
| only new files; `git status` lists only new paths | passed; none git-ignored | cmds 2, 11 |
| 2nd priority: OLMo d = 11-16 by `build_r_draws_78b.py` (BLD by path after SHA check; reproduces d = 1-5, lists d = 6-10) | passed | recompute_r: 6 files == my draws and seeds; provenance outside `selection`/`scale78b_wrapper` == SEAL R_d1's base; BLD's own `edit_file` with the recorded blocks gives the same bytes; names in BLD's form; seeds 1111-1116 |
| Llama d = 11-16 hold the same rows as the OLMo d = 11-16 | passed | both equal my draw d (recompute_r) |
| 3rd priority: H1 on the Llama manifest by stage 1's rule with Llama counts | passed | recompute_h1: my Llama H1 == `octile_0.json`; my OLMo H1 == stage 1's `octile_0.json` (`f5b1762f...`); cut points (2-13, 13-23, 23-34, 34-51, 51-75, 75-106, 106-177, 177-2064) and by-category counts equal; target-token accounting and steps (33) equal |
| README's H1 mechanism (599 shared; a 14 -> 13 row enters; the worst-ranked 13-token row leaves; 4 / 5 changed-count rows inside) | passed | recompute_h1: shared 599, enter 1 (14 -> 13, rank 3586), leave 1 (13 -> 13, rank 4667 = max rank among the OLMo H1's 13-token rows), inside counts 4 and 5 |
| no row text printed or copied | passed | H1 file has exactly the engine's 11 keys, `rewrite`/`add` empty, no text keys in provenance, longest provenance string 242 chars (a rule sentence); my scripts print counts, hashes, token values only |
| 3rd priority: S1 re-bound | not built (stop rule) | the S1 add edit holds 48 rows' prompt/response text and needs the Llama codec (R `write_add_edit.py` per the READMEs); correct refusal, a lead job |
| engine suite with the fixture test ignored | passed | cmd 18: 837 passed, 5 skipped |
| the wrapper never writes under SEAL or stage 1 | passed (R) | writes only in `write_files` -> `write_atomic` after `guard_out` (R `build_sealed_llama3.py:410-417, 546-555, 571-582`; `build_r_draws_78b.py:183-190, 239-248, 262-265`); `build()` writes nothing; H1 via `s1.write_new_files` (absent-or-empty rule) after a stage-1-folder guard (R `build_h1_llama3.py:105-110`) |
| the builder's citations | hold (R) | plan T7 exists (plan:317-320 names the OLMo R_d9-16 wrapper); T4's block A is R_4, R_5 (plan:258); P78 §9.2 items 2-3 (P78:339-343) name the Llama writer on BLD's draw and `scripts/scale78b/build_r_draws_78b.py` |
| adversarial probes: wrong stream or seed, off-by-one in d, wrong manifest field, unsorted lists, unit file missing members, test passing for the wrong reason | none found | recompute_r: stream `gate-b-random-removal-v1`, design seed 20261008, `selection.draw == d`, `seed == 1100 + d`, no file equals the neighbouring draw d +/- 1; `manifest_sha256`, `inputs`, `drawn_on` hashes equal the real files; every list sorted and distinct, 75 per unit; units complete; mutants killed |
| `commitments.py check` after the merge | unaffected (I from R) | include globs are `scripts/stage1/**`, `scripts/stage1_s1/**`, `.ai/inputs/stage1-commitments-20261016/**` (R `scripts/stage1/settings/commitments.json`); none of the new paths match; baseline check OK at HEAD (cmd 20) |

## 6. Defects (minor; none changes a remove list)

1. **The engine tests read prompt text through `load_prepared`.** `test_d_...` (R
   `.ai/inputs/scale-78b-sealed-llama3-20261105/tests/test_build_sealed_llama3.py:173-175`),
   `test_the_engine_accepts_each_file_...` (R `scripts/scale78b/tests/test_build_r_draws_78b.py:80-87`) and
   `test_the_engine_accepts_llama_h1_...` (R `scripts/scale78b/tests/test_build_h1_llama3.py:75-80`) call the engine's
   `load_prepared`, which reads `engine/query_rows.jsonl` and the training text into memory (R `prepare.py:949-950`), a
   file BLD lists under `never_opened`. Nothing is printed, so no leak; but the brief's rule allows text reads only where
   the track's frozen code reads them, and T3's frozen code (BLD) never opens `query_rows.jsonl`. Fix: the id-only stubs
   (`W.PreparedView(LLAMA, ...).engine_stub()`, `s1.PreparedView(...).engine_stub()`), two lines per test. The tests are
   not in any hashed script, so the fix changes no arm hash. My own parse_edit checks used stubs and pass (section 5).
2. **`build_h1_llama3.py` guards only the stage-1 folder, not SEAL.** (R `build_h1_llama3.py:105-108`.) `--out` under
   `.ai/inputs/gate-b-sealed-20261008/<new>` would be written (the absent-or-empty rule stops only overwrites). Fix: add
   SEAL's folder to the guard. The script's SHA-256 is in H1's provenance (`script_sha256`), so the fix changes H1's arm
   hash and needs a rebuild into an empty `out/` before the commit; the remove list does not change.
3. **`guard_out` resolves the forbidden folders relative to `--repo`.** (R `build_sealed_llama3.py:410-417`;
   `build_r_draws_78b.py:183-190`.) With a non-default `--repo` the real SEAL path is not refused. Default use is
   correct and the absent-or-empty rule still blocks overwrites. A fix changes the wrappers' bytes (every Llama arm hash
   and the d = 11-16 arm hashes), so it belongs before the first commit or not at all.

## 7. Jobs for the lead

1. **Merge by explicit paths** (46 untracked files, none ignored; M): `.ai/inputs/scale-78b-sealed-llama3-20261105/`,
   `.ai/inputs/scale-78b-r-draws-olmo2-20261105/`, `.ai/inputs/scale-78b-length-rules-llama3-20261105/`,
   `scripts/scale78b/`. Commit each script with its `out/` (the edit files embed the scripts' SHA-256).
2. **Decide before the commit** (section 8 item 1): the two extra top-level `.ai/inputs/scale-78b-*` folders, and whether
   minor items 2-3 are fixed now (both change hashes; rebuild into empty `out/` and re-run the 27 tests) or recorded.
3. Minor item 1 (stubs in the three engine tests) changes no hash; fix any time.
4. After the merge, in the main checkout: `tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q
   .ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests` (27 tests, about 1 s); the engine identity
   re-check (`472fc7f6...`, unchanged here); `scripts/stage1/commitments.py check` (unaffected by the new paths, I).
5. **S1 on the Llama manifest**: a lead job (needs the sealed list's text and the Llama codec).
6. If the lead records the set in FOCUS: MANIFEST `76415c42...`; r-draws `da634837...`; H1 `189cd139...` (all M here).

## 8. Unresolved concerns

1. **Placement of two folders.** Ruling 14 names `.ai/inputs/scale-78b-sealed-llama3-20261105/` for the Llama sealed set
   and sends later 7-8B records under `.ai/inputs/stage1-post-w1-20261023/78b/`. The OLMo d = 11-16 draws and the Llama
   H1 sit in two further top-level `.ai/inputs/scale-78b-*` folders that no ruling names (P78 §9.2 item 3 names only the
   script path). The builder's reasons are stated (the sealed MANIFEST lists exactly BLD's draws). A move changes the
   `OUT_REL` constants inside the hashed scripts (R `build_r_draws_78b.py:44`; `build_h1_llama3.py:37`), so it needs a
   rebuild; decide before the commit.
2. **Frozen-on-commit** (the builder's concern 1 holds): any byte change to a script changes every arm hash it signs.
3. **The recorded provenance base** (`derive_seed.source_sha256`, `spec`, `inputs`) in the Llama files is copied from
   SEAL's R_d1 block, not recomputed (R `build_sealed_llama3.py:280-291`). I checked that it equals the current engine's
   `derive_seed` source hash (M `f03231c9...`), and BLD's `seed_of` cross-checks the formula at draw time, so there is no
   present defect; a later engine change would not be reflected in that block.
4. **Byte parity for d = 6-10 depends on the environment** (Python 3.11.15, numpy 2.2.6; the builder's concern 3). It held
   here (M). The test names the differing fields if it ever fails.
5. `d = 14-16` are built and labelled "not run under ruling 2"; the lead may leave them.
