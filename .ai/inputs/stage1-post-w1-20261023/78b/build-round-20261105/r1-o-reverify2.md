# R1 Track O fix round 2: second adversarial re-verification

Written 2026-11-08 19:34 UTC (`date -u`). Started 18:57 UTC. Status: **DONE**.

**Verdict: VERIFIED_WITH_MINOR.**

What I measured:
- **OR1 is closed.** I ran my own in-place fill on a fresh copy, starting from the committed pins. In all 9 states
  (the committed state and each T-O2 step, cumulatively), Track O had 0 failures.
- **The 5 other mirror failures are artifacts.** They appear in every state, the unfilled one included, and all 5
  pass in WS's own suite.
- **R-20, R-21 and R-23 are built as ruled.**
- **OR2, OR5, OR7 and OR9 are closed.** OR8 is narrowed but not fully closed.
- **No regressions:** no label lie, no leak, globals restored on every path tested, lean parity holds, the 1B files
  are unchanged, and every fill reaches only its own family's or engine's forms.
- **Suite:** 340 passed, 57 skipped.
- **Mutants:** 92 of 92 killed.

What is left: two minor gaps (the printed form omits the W1-18 record; three untested branches) and three nits.

Target: WS = `B/ws-o` (detached at `3481d85`). Builder's §11: `R/r1-o.md`. My scratch: `R/r1-o-reverify2-scratch/`.
M: all 32 Track O files hash to §11.2. `git status` shows 23 untracked entries and no tracked change. WS has no
`__pycache__`, an empty `tmp/`, and no `.ai/.../w1-18/` folder after my runs. I made no git state change. There was
no pod, network, install or download. I opened no unit, answer, generation, guard, judge, sealed or prompt file, and
I ran `check --data-root` only on fixtures. Tags: M = measured, R = read (path:line in WS), E = estimate,
I = inference.

## Defects

| id | sev | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| W2-1 | minor | `make_oext_settings_78b.py:426-438` (`form`, docstring :430: "the lead adds it with the branch fill") | After a branch fill, the printed `OEXT_78B[F]` and `OEXT_78B_Y[F]` forms still omit the family's W1-18 record. R-21 lets RK's form check accept "that one folder for the W1-18 record entry only", and T-O3 says the record joins the job's files list. The maker already holds the record's path and SHA-256 (pins `families.F.w1_18`). M: in my in-place copy after OLMo's branch-128 fill, `--oext-78b olmo2-7b` lists no record entry (`fill-form-x-olmo.json`). | The lead's recorded `OEXT_78B[F]` fill adds a path and hash by hand. That form is not printed and not tested. A slip there is found only when the pack or an O-ext pod refuses. | Under 128, or full with a record, `form()` adds `{record_path: record_sha256}` for X and Y. Hold it in `consistency()` against RK's R-21 check. |
| W2-2 | minor | `make_oext_settings_78b.py:441-456` (`side_units`' job pins); `oext_78b.py:653-655` (W1 index plus a record); `:525-528` (no identity, no ENGINE_Y wait) | Untested branches in the new code. 3 of my 4 proposed mutants **survive** the builder's suite (M: `rv2mut-a.json`, baseline 131 passed, 1 skipped): RV2-m-w1-side-job (W1_18_78B's side units lose their job.json pins), RV2-w-w1-record-ignored (`check` on the W1 index silently ignores a given record), RV2-w-null-identity-waits. All 3 are killed once my targeted probes H3, C4 and I1 are added (M: `rv2mut-b.json`). The builder's W1-form test and `w1_18_form_problem` check only the side-unit names, the path and `complete_sha256`. | A later edit drops θ0's job pin from W1_18_78B, the pin R-20 asks for, with every test green. | Add H3, C4 and I1 (`test_zz_rv2_targeted.py`) and the 3 mutants (`rv2_mutation_spec.json`). |
| W2-3 | nit | `oext_78b.py:503-509` (`expected_wait`), `:511-545` | OR8 is narrowed, not closed. The 1B validator stops at its first refusal. So when a file has a null pin, any fault the validator would test after that pin is never seen, and the file still prints `"waits"` with exit 0. M (F2): a W1-18 settings file with a null θ0 pin **and** `bank.size = 99` gives `"waits"` and exit 0. A fault tested before the pin now exits 2 (F1, M). | Before the θ0 fill, `check` cannot certify the rest of the file. After the fill it is fully validated, before any pod (I). | Validate a copy with each waiting pin replaced by a placeholder SHA-256. Any refusal then means "invalid". |
| W2-4 | nit | `oext_78b.py:524` (`engine = running` for the W1-18 settings) | `check` validates the W1-18 settings under the **running** engine's identity, not engine X's. M (A4): on a simulated engine-Y host, `check --engine Y` of a sound fixture index refuses with "limits_overrefusal_checks… names engine". The Mac runs as engine X, so the pack's R-6 check is unaffected (I). | Only if K3 runs `check` on the engine-Y pod. | Validate W1-18's file under engine X's identity, for example the X index's `engine_identity`, or the file's own `engine_x`, since its binding never checks the engine. |
| W2-5 | nit | `make_oext_settings_78b.py:441-456`; r1-o.md §10.1 O10 (corrected) | W1_18_78B's `files` part omits the two frozen readers that W1-18 loads by path and pin: `scripts/family_probe_reading.py` and `scripts/killtest_stage0_reading.py` (R: `limits_common.py:71-97`; the W1-18 settings' `frozen_reader` block). No kit pin lists them either (M: grep in ws-k `runkit/stage1-78b/*.py`, 0 hits). R-20 does not ask for them, and O10's corrected note leaves them to K3 "beyond W1_18_78B's". | If K3 packs only W1_18_78B and the existing pins, the W1-18 pod refuses ("the frozen script … is missing"). That is a paid start. | Either list both readers, by their pins, in W1_18_78B's `files` (both are under `scripts/`), or keep the item on K3's acceptance list. |

## 1. OR1: closed (M)

- **My own in-place check** (`rv_fill3.py`, written for this pass; it is not the builder's `rv_fill2.py`):
  - The copy: `scripts/scale78b` copied; every other entry linked; `.ai` mirrored by links, except the folders along
    R-21's record folder, which are real (asserted, so no record can reach WS).
  - **It starts from the committed pins**, not from a rebuilt all-null state. In fact the committed pins are the
    pre-fill state (M).
  - The T-O2 steps run cumulatively with the maker's defaults. My values differ from the suite's stand-ins where a
    real choice exists. θ0 takes K1's measured job pins (R-2). B+Qi is a config with MAIN's blocks that is not MAIN
    (OLMo's G config; Llama's 1e-4 G config). The records are synthetic and text-free, committed at R-21's place in
    the copy.
  - After each state: the maker, `--check`, then the whole scale78b suite.

  | State | Maker / `--check` | Suite | Track O failures |
  |---|---|---|---|
  | 0 committed | 0 / 0 | 5 failed, 335 passed, 57 skipped | **0** |
  | 1 θ0 OLMo | 0 / 0 | the same | **0** |
  | 2 θ0 Llama | 0 / 0 | the same | **0** |
  | 3 OLMo branch 128 (record at `.ai/…/w1-18/w1_18_record__olmo2-7b.json`) | 0 / 0 | the same | **0** |
  | 4 Llama G | 0 / 0 | the same | **0** |
  | 5 Llama branch full (failing record) | 0 / 0 | the same | **0** |
  | 6 ENGINE_Y | 0 / 0 | the same | **0** |
  | 7 B+Qi OLMo | 0 / 0 | the same | **0** |
  | 8 B+Qi Llama | 0 / 0 | the same | **0** |

  (`rv_fill3_{0-1,2-4,5-8}.out`.) In state 8, the wrapper's `check` exits 0 on all six indexes, with no wait left.
  The X and Y checks read the committed records, giving 128 for OLMo and full for Llama. The Y files are "valid"
  under engine Y's identity (`fillcheck-*.json`).
- **The 5 other failures are mirror artifacts (M, R).** They are the same in every state, state 0 included. All 5
  pass in WS's own run (`-v`, 6 passed, the nested in-place test included). Cause for `test_make_recipe_s78`:
  `make_recipe_s78.anchor_records` uses `rglob` (R: `make_recipe_s78.py:123`), which does not descend into the
  mirror's linked `.ai/inputs` sub-folders. The 4 guard tests depend on the mirror's linked `tmp/` (round 1).

## 2. R-20 / R-21 (M, R)

- **The W1 index.** `OEXT-78B-W1__F.json` lists only the W1-18 settings. It carries no branch, engine identity,
  inputs or record (M: its keys).
  - `w1_18` takes only it: `COMMAND_ENGINES` (R: `oext_78b.py:106`), and engine W1 is the default for `w1_18`.
  - M (C2, 5 cases): each of these refuses with exit 2 and no folder: `w1_18 --engine X`, `w1_18` handed the X
    index, `unit --engine W1`, `lean --engine W1`, `w1_18 --engine Y`.
  - `check` on the W1 index refuses a W1-18 record (C4).
  - The lead's R-9 command on the W1 index passes on fixtures, with the sealed check passing and one eval folder
    (E7).
- **Only a θ0 fill reaches it** (M: `rv_cascade2.out`; H2). θ0 fills change `W1[F]`. No branch (128, full with a
  record, full with a reason), G, B+Qi or ENGINE_Y fill does.
- **The printed W1_18_78B form** (`form-w1.json`; H3):
  - `files`: the wrapper (`c6a9a946…`, the file beside the maker), s1common, limits_common, overrefusal_checks, and
    per family the W1 index and the W1-18 settings. All are under `scripts/`; there is no lean copy and no O-ext
    file.
  - `side_units`: per family, each unit's path, COMPLETE.json pin and job.json pin, equal to the W1-18 settings.
  - K1's current `files_form_problem` refuses the whole form ("keys are not exactly files") and accepts its `files`
    part (M). R-32 assigns that change to K2. W2-5 covers the readers.
- **The record's place and pin (R-21).** The pins hold `record_path` and `record_sha256`, both set or both null. The
  path must be a plain `.json` path under `.ai/inputs/stage1-post-w1-20261023/78b/w1-18/` (R:
  `make_oext_settings_78b.py:210-218`). `verify_records` hashes the file at that path (`:390-404`). M (H1, 10 cases):
  the maker accepts only the case at the right place with the right hash. It refuses with exit 2 a record that is:
  elsewhere under `78b/`, in a sibling `w1-18x/`, given by a `..` path, an absolute path, a `.txt` file, off its pin,
  or missing; a path without a SHA-256; and a SHA-256 without a path. The maker checks the hash only. The record's
  family, branch and settings are R-6's `check` (still passing, D1-D3). W2-1: the forms do not yet carry the record.
- **R-22 (informational).** K1's current RK now takes Track O's names. All four printed X and Y forms pass both WS's
  RK and K1's `oext_form_problem(form, F, E)` (M: `rk_forms.py`).

## 3. OR2, OR5-OR9, R-23 (M)

- **OR2: closed.** These now refuse on the Mac, as W1-18 itself does:
  - a listed file that is missing (E1: "the frozen sealed check refuses");
  - a second `eval/` folder (E2);
  - a path outside the allow-list form (builder's test; F2-w-path-form killed).

  R-9 is **still hash-only**:
  - junk bytes with their true hashes pass (E6);
  - the frozen `sealed` only hashes (R: `family_probe_reading.py:104-105`, `:137-151`);
  - no sentinel reaches the output in 7 cases (E4);
  - `eval/` folder names are counted, never printed.
- **OR5: closed.** A g16 B+Qi config refuses in the maker (H4).
- **OR6: closed.** The 11 proposed round-1 mutants are in the spec and killed (§5).
- **OR7: closed.** A text value in the file list, or as COMPLETE.json's `job_sha256`, never reaches stdout or stderr
  (E3, E3b).
- **OR8: narrowed** (F1 exits 2), not closed (W2-3).
- **OR9: closed.** Each of the four leading options, given twice, refuses (C3).
- **R-23: built.** On a fixture Y index, `check --engine Y` validates the Y files under the index's identity with no
  test patch. A Y unit file naming the X O-ext file refuses, and the true label is "valid" (A3). An index with no
  identity and no ENGINE_Y wait refuses (I1). On the filled copy, all Y files are "valid" (§1). W2-4 is the nit.

## 4. No regression (M)

- **No label lie** (A1, A2, A3):
  - a unit file naming the 1B path, or either family's committed O-ext path, refuses;
  - a relocated index refuses on the old label, and the true folder runs.
- **No leak; restored on every exit path** (B1-B4; the globals checked now include `s1common.code_identity`):
  - `w1_18` for OLMo, then Llama, then OLMo in one process, plus a cross-wired data root that refuses;
  - `unit` for OLMo, then Llama, then OLMo, with per-family pins in each `job.json`;
  - argparse `SystemExit` inside the 1B main;
  - a validator refusal inside `check`;
  - C1's 32 refusal cases (8 index faults × 4 commands) leave every global unchanged.
- **Lean parity.** `lean_eval_job_78b.py` is unchanged (`fc0372ca…`), so round 1's diff against
  `3481d85:scripts/stage1_s1/lean_eval_job.py` still holds.
- **The 1B files.** All 698 tracked blobs (stage1, stage1_s1, runkit stage1-olmo and stage1-78b, scale78b's tracked
  files, the engine, the frozen readers) equal MAIN's `ls-tree -r 3481d85`: **0 differ**.
- **Each fill reaches only its own forms** (`rv_cascade2.py`, my cascade updated for record paths, `--records-root`
  and the W1 parts). 13 single fills, **all OK**:
  - θ0 reaches the family's X, Y and W1 parts;
  - a branch reaches the family's X and Y;
  - G reaches the family's X;
  - B+Qi reaches the family's Y;
  - ENGINE_Y reaches both Y.

  The wrapper's hash is the same in every form. All six `check`s exit 0 after every fill. Cumulatively in T-O2's
  order, each form last changes at its family's last fill for that form (X at the branch, Y at B+Qi, W1 at θ0).

## 5. Suite and mutants (M)

- **WS suite:** **340 passed, 57 skipped**, exit 0 (164 s; load average about 13 then). None of the skips is a Track
  O test or one of the 5 mirror-failing tests (M: `-rs`).
- **The spec** (`0010a870…`, 92 mutants; each find text exactly once, no duplicate ids) ran in 6 shards of 16, 16,
  16, 16, 16 and 12, two at a time. Each shard had its own baseline with the same command (131 passed, 1 skipped: the
  nested test, skipped by the runner's `OEXT78_NESTED`). Shard times were 2.0 to 3.3 min. **92 of 92 killed,
  0 survived, 0 invalid, 0 ERROR lines** (`mut2-{1..6}.json`). Each of the 14 F2 mutants dies on a test aimed at it.
- **Proposed second-pass mutants** (`rv2_mutation_spec.json`, 4 mutants): 3 survive the builder's suite and all 3
  die with my targeted probes (W2-2).
- **The nested in-place test is never mutation-tested.** The runner skips it by design (R:
  `run_mutants_oext_78b.py:69`). My per-state run (§1) covers its ground.

## Commands run (exit status)

- Reads (exit 0): GXB sets 8-13, r1-o.md §11 and its corrected §10 notes, the wrapper, maker, fixtures and runner
  diffs against `prefix2/`, the new tests, the builder's `rv_fill2.py`, and `make_recipe_s78.anchor_records`.
- Hashes of the 32 files (equal to §11.2). The blob comparison: 698 blobs, 0 differ.
- WS suite (exit 0) and the 6 named tests `-v` (6 passed).
- `rv_fill3.py` states 0-1 (moved to the background after 180 s, read after it ended), 2-4 and 5-8: exit 0 each.
- `rv_cascade2.py`: exit 0, ALL OK.
- `test_rv2_probes.py` against WS:
  - the first run had 1 failure from my own probe (the Y record fixture needed engine Y's identity);
  - after the fix: 81, then 83 passed, exit 0.
- Maker `--w1-18-78b`, `--oext-78b`, `--oext-78b-y` (exit 0). `rk_forms.py` and `rk_w1form.py` (exit 0). The six
  `check`s on the filled copy (exit 0).
- Mutation:
  - shards 1+2 (moved to the background after 180 s, read after it ended), shards 3+4 (the same), shards 5+6: each
    exit 0;
  - proposed run a: exit 1, 3 survived;
  - proposed run b: exit 0, 3 killed.
  - I deleted every mirror, source root, fill copy and cascade folder after use.
- `date -u` before each time written.

**Evidence** (`R/r1-o-reverify2-scratch/`):
- scripts: `rv_fill3.py`, `rv_cascade2.py`, `test_rv2_probes.py`, `test_zz_rv2_targeted.py`, `make_rv2spec.py`,
  `rk_forms.py`, `rk_w1form.py`;
- outputs: `rv_fill3_*.out`, `rv_cascade2.out`, `ws-suite.out`, `mut2-{1..6}.json`, `rv2mut-{a,b}.json`,
  `rv2_mutation_spec.json`, `form-{x,y}-*.json`, `form-w1.json`, `fill-form-x-olmo.json`, `fillcheck-*.json`.

## Acceptance criteria (the brief's items)

| Item | Result | Evidence |
|---|---|---|
| 1 OR1: my own in-place fill, each T-O2 step and all eight, 0 Track O failures; the 5 others are mirror artifacts that pass in WS | **passed** | §1 |
| 2 R-20/R-21: W1 index, W1_18_78B form, only θ0 reaches it; record place and pin; the maker refuses elsewhere or off-pin | **passed**, with W2-1 (the record is not yet in the printed forms) and W2-5 (nit) | §2 |
| 3 OR2, OR5-OR9, R-23 closed; R-9 hash-only | **passed**, except OR8 narrowed (W2-3, nit) | §3 |
| 4 No regression; the cascade re-run | **passed** | §4 |
| 5 Suite and spec in shards | **passed** (340/57; 92/92), with W2-2 | §5 |
| A real 7-8B run, or R-9 on the real units | not tested (no pod; never run on real units, by the brief) | — |
