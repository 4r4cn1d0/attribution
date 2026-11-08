# R1 Track O report: the 7-8B O-ext layer

Written 2026-11-08 15:25 UTC (`date -u`). Started 14:42 UTC. Status: **DONE**, with the open points in §8. A fix round followed (§10, after the verifier's `r1-o-verify.md` and the lead's R-5 to R-9); §10 supersedes §1-§7 where they differ. Fix round 2 (§11, after `r1-o-reverify.md` and R-20 to R-23) supersedes §10 where they differ.
WS = `B/ws-o` (a detached worktree of MAIN at `3481d85`). I created new files only, all under `scripts/scale78b/`.
I changed no tracked file (M: `git --no-optional-locks -C WS diff --stat` is empty). I made no git state change, ran
no pod, used no network, and installed and downloaded nothing. Tags: M = measured (the command is named), R = read
(path:line in WS), E = estimate, I = inference.

## 0. The decisive check (step 1) and the route I chose

**Question.** Can one wrapper run the unchanged 1B entry points with per-family settings, so that no record, settings
file or output names a path the run did not load (GXB B-3, O3)?

**Result per seam (R and M).**

| Seam | What it does | Can a module global pass it with a true label? |
|---|---|---|
| `oext_unit.py:209` | `load_pinned_settings(path=SETTINGS_PATH)`: the default is bound when the function is defined; `main()` calls it with no argument (:691) | **Yes.** The wrapper replaces the module attribute `load_pinned_settings` for the call with the original function bound to the family's file and its SHA-256. |
| `oext_unit.py:146` | `pin["path"]` must equal the module global `OEXT_SETTINGS_PATH` (:75), read when the validator runs | **Yes.** The wrapper sets `OEXT_SETTINGS_PATH` to the family's file path. `oext_unit__F.json` names `scripts/scale78b/settings/oext_eval__F.json`, the file that is read. M: the real OLMo-2-7B file passes `oext_unit.load_pinned_settings` with that global set (test `test_the_x_settings_pass_the_unchanged_1b_validators_with_their_true_labels`). Without it, the 1B validator refuses the true label (test `test_the_1b_validators_refuse_the_true_labels_without_the_wrapper`). |
| `oext_eval.py:246-251` | the same default-bound loader | **Yes**, the same way. |
| `oext_eval.py:214-236` | `check_w1_18_binding` reads `w1_18.SETTINGS_PATH` and `w1_18.SETTINGS_SHA256` (module globals of `overrefusal_checks.py`), and the file must hash to `cap.w1_18.settings_sha256` | **Yes.** The wrapper sets both globals to the family's W1-18 settings file. No settings field names the W1-18 settings path (`cap.w1_18` holds `script`, the 1B module that is loaded, and hashes only; R: `oext_eval.py:164-165`). |
| `oext_eval.py:374-375` | the W1-18 record's `provenance.settings_sha256` must equal `cap.w1_18.settings_sha256` | **Yes.** The family's W1-18 run writes the family settings' SHA-256 (M: `test_the_records_provenance_is_the_family_settings_hash_and_oext_eval_reads_it`). |
| `overrefusal_checks.py:83-84`, `:533`, `:542` | `--settings` defaults to the global `SETTINGS_PATH`; the file must hash to the global `SETTINGS_SHA256` | **Yes.** The wrapper passes `--settings <family file>` and sets both globals. The record's provenance names `scripts/stage1/limits/overrefusal_checks.py`, the module that ran (R: `overrefusal_checks.py:446`; `s1common.py:566`). |
| `lean_eval_job.py:849` | `load_lean_settings()` reads `SETTINGS_PATH` and `SETTINGS_SHA256` when called | **Yes** (module globals). |
| **`lean_eval_job.py:229`** (not in plan-ab's list) | `check_lean_settings` compares `oext.settings.path` with the **literal** `"scripts/stage1_s1/settings/oext_eval.json"` | **No.** No global can change a literal. A 7-8B lean settings file would pass only if it named the 1B path while the run reads the family's `oext_eval__F.json`. That is the label lie that GXB O3 forbids. M: the 1B `check_lean_settings` refuses both real `lean_eval_job__F.json` files (they hold the true label). |

**The route I chose.** I used the wrapper route for `unit` and `w1_18`, and the copy route of DES E4 for `lean` only.
There is one wrapper, `scripts/scale78b/oext_78b.py`, with the three commands of B-3 (and a $0 `check`).
- `unit` and `w1_18` run the unchanged `oext_unit.py` and `overrefusal_checks.py` with the module globals above set
  for the call, then restored.
- `lean` runs `scripts/scale78b/lean_eval_job_78b.py`. This file is the 1B `lean_eval_job.py` rebuilt by five listed
  substitutions (`tests/oext/lean_copy_spec.py`), and a test rebuilds it byte for byte. The one substitution that
  matters turns the literal at :229 into a module global `OEXT_SETTINGS_PATH`, the same form as `oext_unit.py:75`
  and :146. The other substitutions are the header, the `oext_eval` import by its fixed name, and the parser's program
  name, which now names the copy.

**Why this route and not a full copy route.**
1. The W1-18 binding (`oext_eval.py:214-236`) can take a family's W1-18 settings only through
   `overrefusal_checks`' module globals, unless `oext_eval.py` itself is copied. Part 2 §4.4 lists `oext_eval.py`
   as unchanged (`8c4290921f…`). So every route, a full copy route included, needs the wrapper's in-process globals
   for that binding (I). The other way is a pack-time swap of the 1B files, but one W1-18 pod runs both families
   (GXB O4), so one 1B path would have to hold two different files.
2. A copy of `oext_unit.py` gains nothing. Its seam is a module global, and the wrapper passes it with a true label.
3. One family-agnostic copy, not one per family, means no hash cascade into a copy when a pin is filled. Only the
   settings files, the index and `INDEX_SHA256` change. **Corrected in the fix round (verifier O1, O12):** this held
   for the copy only. The single index and the `INDEX_SHA256` literal in the wrapper put every fill into both
   families' `OEXT_78B[F]`. The fix round removes the literal and splits the index per family and engine (§10).

**For the lead.** B-3 says "the wrapper if the check passes, else the copy route". The check fails at one seam only
(:229). I built the hybrid that this implies. It meets O3's rule, and every path label is the path of the file that
was loaded. If you want a pure copy route instead (copies of `oext_unit.py` per family and engine, plus copies of
`lean_eval_job.py`), that is open point P1 (§8). It still needs the W1-18 globals, for reason 1.

## 1. Files created (all new; SHA-256 by `shasum -a 256`, M)

| File (under `scripts/scale78b/`) | SHA-256 |
|---|---|
| `oext_78b.py` (the wrapper; 450 lines) | `9ea348e0b9ed51b3d05b308319706f4353c356595043c29d6de96ca32b20b35f` |
| `lean_eval_job_78b.py` (the lean copy) | `fc0372ca006c478f9b4b3bff3c903f9d15f774b94c61a6b4aca98973c400e4a7` |
| `make_oext_settings_78b.py` (the maker) | `d2ee1534501876dea1b4c42c9620e66f0ab24a0a19700e8b8b8a35663ebe0ffe` |
| `settings/oext_pins_78b.json` (the pins the lead edits) | `ad4458216104ae227471aaabcdfed83260a80337feecd3f43fdd3ba94d6361c0` |
| `settings/OEXT-78B.json` (the index; = `INDEX_SHA256`) | `7c3edb0f7930da2f3031c9b058f907103682da972010f8eab2d935c154bebbd4` |
| `settings/oext_unit__olmo2-7b.json` | `3c1289e4253de32b6026c848cebfbb8f7568695b00b8c9fccea1566d8f112b21` |
| `settings/oext_unit__llama31-8b.json` | `59d004884bbcbd1233737066c453f8b87bb096aa40407690c7d2c85bf13556b4` |
| `settings/oext_eval__olmo2-7b.json` | `632ec4de5134f746634351837b52fe316313b65d99ab4a81a52620618c9518a1` |
| `settings/oext_eval__llama31-8b.json` | `1174a17d57269f66c5af1ec3e3f0441da889fa415ffa5217b0943dc46b1e3764` |
| `settings/oext_unit_y__olmo2-7b.json` | `3c1ef9d79758350121517d2b792081450ffeb0e340a7135b7793bf2c46aa3d60` |
| `settings/oext_unit_y__llama31-8b.json` | `6d4e84ec10a5b29826e1243ca985709bd359a671c37045553c834478e2751336` |
| `settings/oext_eval_y__olmo2-7b.json` | `f89088a332da2532ec7cded50747f7710d3dc721b5ec2d4d18d978423a9e2115` |
| `settings/oext_eval_y__llama31-8b.json` | `71cb6b44fbae9fdf43ff1485da0436a7b608bbcde25427e5c9e58b088712c33c` |
| `settings/lean_eval_job__olmo2-7b.json` | `8cd529e153544bd744bb369dd130b24f5dad5be530ec895ae780a6c29dbf3e46` |
| `settings/lean_eval_job__llama31-8b.json` | `6a59eb9cba288575e304cf0f7b1412528fe4f28ac4e01ffa207ffeda27154f2b` |
| `settings/limits_overrefusal_checks__olmo2-7b.json` (the 7-8B W1-18 settings) | `6eb41c4a1a741f9714a61d9003727c67617c7c898a131128fb14e63cdc7e7c98` |
| `settings/limits_overrefusal_checks__llama31-8b.json` | `cbf2ddfc2e4c725d5469e4f7a3da14e27f9c0aba27bb577b9bdbc310801e826a` |
| `tests/oext/conftest.py` | `823bafb4ce86c5cee338ce907563a6fd325e5c1b23278819a8eaf0072123daef` |
| `tests/oext/oext78_fixtures.py` | `8c01421043d9e02a0863817c805cab1355b23778255cf6bef3dc78f8e3e3e777` |
| `tests/oext/lean_copy_spec.py` (the listed substitutions) | `f5f5e27430a48fe906fb17eb3d3ac6ae730b9f170d9897cf1e603e9e9012ea48` |
| `tests/oext/test_oext_78b_unit.py` | `0bdbf0240b46f6e9298f1e49c988bd874d8efd8e50fd4256687a6ae521892613` |
| `tests/oext/test_oext_78b_lean.py` | `806432eabb1a09b73c85451347ac152147cfa0a79d315990642de0c68897eea5` |
| `tests/oext/test_oext_78b_w1_18.py` | `761c41d4ce47abd32c7b8fbc1f647c718fc131e9ec4506c9c2bf0b09e916b4f6` |
| `tests/oext/test_oext_78b_files.py` | `3401da8ed65854434ad4a9f3d5da9ff2b5b4fd718789819c3ae1bcbdc6cee2f7` |
| `tests/oext/mutation_spec_oext_78b.json` (41 mutants) | `d37e69b64e3a24693915ee4ec897039f13b3db5108fed2727bcf8ab5c8b44014` |
| `tests/oext/run_mutants_oext_78b.py` (the runner) | `3effdaf80a5d0d6ee8e658c431d835b9b119f32f0887dafcf82eb97b243e0a02` |

I copied no git-ignored file into WS `tmp/` (M: WS `tmp/` exists and is empty. Corrected in the fix round, verifier O12: I first wrote "absent"). The tests use synthetic fixtures only.
Evidence files are in `R/r1-o-scratch/`: `mut-final-{1..4}.json` (the mutation reports), `oext78b-check.json` (the
wrapper's `check` output), `oext78b-form-{olmo2-7b,llama31-8b}.json` (RK `OEXT_78B[F]` in its documented form), and
the probe and helper scripts (`c3_check.py`, `dumpkeys.py`, `make_spec.py`, `probe_unit.py`, `probe_lean.py`).

## 2. What each item does and where (R: path:line in WS)

- **The wrapper** (`oext_78b.py`). Usage and design are in its docstring (:1-55).
  - `CODE` (:77) pins the run files by SHA-256: s1common, limits_common, overrefusal_checks (`ed5fd2dc…`), oext_eval
    (`8c429092…`), oext_unit (`ae2fb5b5…`) and the copy. `check_code` (:149) refuses a changed file.
  - `load_index` (:167) refuses an index that does not hash to `INDEX_SHA256` (:69).
  - `Family.require` (:199) refuses with the pin's name, its place and its event while a needed pin is null.
    `Family.file` (:206) refuses a settings file that is off the index pin.
  - `check_flags` (:257) requires full flag names (scorers_78b RV-E-1). It refuses `transfer` (DESO2 item 32), and for
    `w1_18` it refuses `--settings` and `--extract-source-map`.
  - `check_prepared` (:297) checks that the manifest is the family's. It names both hashes, and the other family's
    manifest when that is the one given.
  - `check_branch_flags` (:312) is the wrapper's side of DESO item 9. `--w1-18-record` is taken exactly when the
    family's O-ext settings pin a W1-18 record, and it must hash to that pin. `--dev100-source` is taken only with
    `--run` under Branch 128.
  - `patched` (:338) sets the globals and restores them, also after an error.
  - `run_unit` (:357, engine X or Y), `run_lean` (:382) and `run_w1_18` (:404) run the commands. `main` (:427) imports
    the lean copy first, so c0's timer origin still comes before torch and the engine (M: the subprocess test).
  - The wrapper writes nothing into any output folder. It prints one JSON line on stderr with the family and the
    settings' SHA-256 values. The 1B stdout and outputs are unchanged.
- **`oext_unit__F`** (`make_oext_settings_78b.py` `oext_unit`, :278). It holds F's manifest pin
  (`9ed61826…` / `c52a50af…`). `recipes.allowed` is `{"MAIN": MAIN_F, "G": F's G}`: OLMo-2-7B's G is its existing
  main-LR config `01259f28…` (DES F2), and Llama's is **null** with the wait `RECIPE_G` (GXB O11). The generation and
  guard hashes come from MAIN_F, and the maker refuses a G config whose blocks differ (:208-210). M: they equal the
  1B pins `5ddced7a…` and `a7f0755b…` on both MAIN configs and on OLMo's G (`R/r1-o-scratch/c3_check.py`, which
  repeats plan-ab §5 C3). `oext.settings` gives the family's `oext_eval__F` path and SHA-256.
- **`oext_eval__F`** (:265). `cap.branch` is `pending_w1_18` with no record and no reason (the wait `W1_18_BRANCH`).
  `cap.w1_18.settings_sha256` is the family's W1-18 settings file. The record pin form is checked by
  `check_w1_18_pin` (:179): 128 needs a record, full needs a record or a reason (not both), and pending needs
  neither. Filling `families.F.w1_18` in the pins file reaches exactly F's `oext_eval`, `oext_unit`, `lean_eval_job`,
  both Y files and the index (M: `test_a_filled_branch_reaches_exactly_its_files`). The other family's settings files are
  untouched, so each family's branch comes from its own record (GXB O4). **Corrected in the fix round (verifier O1,
  O12):** the shared index and the wrapper's literal still changed both families' kit forms. That is fixed in §10.
- **The Y variants** (:305-323). `oext_unit_y__F` allows `{"B+Qi": null}` (the wait `RECIPE_BQI`). `engine_x` is
  `ENGINE_Y`, null until filled (the wait `ENGINE_Y`). `oext_eval_y__F` follows F's branch with `engine_x` =
  `ENGINE_Y`. Once filled, they refuse on engine X through the unchanged `s1common.check_settings`, which names both
  identities (M: `test_a_filled_engine_y_and_bqi_give_y_files_that_refuse_on_engine_x`;
  `test_the_y_variant_refuses_on_engine_x`).
- **`lean_eval_job__F`** (:292). It holds `job.allowed_recipes = {MAIN_F name: MAIN_F}`, the family's `oext_eval__F`
  path and SHA-256, `oext.branch` from F's pin, and `owner` set to the copy's path.
- **`limits_overrefusal_checks__F`** (the 7-8B W1-18 settings; :228). The units are theta0 and the a0 units (OLMo-2-7B
  1101-1103; Llama-3.1-8B 1101-1102). Each is pinned by its COMPLETE.json SHA-256 from RK `KIT` `a0_units` (M:
  test). The job.json SHA-256 comes from the committed record
  `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json` (`8c3579e4…`). That record's `job_sha256` is
  the job.json hash that `g1_check_78b.py:79` checked. For the five a0 units these are M from the committed bytes.
  **Theta0's two job pins are null** (no committed record names them), with the wait `THETA0_JOB`. The file also
  holds the family's prepared path and manifest, and the judge recipe = MAIN_F's file (policy codec) with its guard
  repo and revision. The path pattern is per family. A test runs these real files, with their pins replaced by
  synthetic ones, over synthetic units at the family's four real unit paths.
- **The index and the RK form.** The maker's `derive_all` (:332) writes the 12 settings files and `OEXT-78B.json`:
  the hashes, each family's `branch`, `manifest_sha256` and `waits` (pin, event, where, roles). `--oext-78b F`
  (:350) prints RK `OEXT_78B[F]` in its form (`{files, inputs}`), and RK's own `oext_form_problem` accepts it (M:
  test). The printed forms are in `R/r1-o-scratch/oext78b-form-*.json`.
- **Waits at this build (M: `oext_78b.py check`).** Both families wait on `W1_18_BRANCH` for `unit` and `lean`, on
  `THETA0_JOB` for `w1_18`, and on `ENGINE_Y` and `RECIPE_BQI` for `unit --engine Y`. Llama also waits on
  `RECIPE_G` for `unit`.

## 3. Tests and suite counts

- New tests (66 cases, 47 functions): `test_oext_78b_unit.py` 16 functions (parity under Branch 128 for unit_eval,
  source_unit and generated, and under Branch full; true path label; globals restored; the binding; other family's
  manifest; off-pin manifest; pending in the wrapper and in the 1B code; Branch 128's record flag; full_reason;
  `--dev100-source`; 9 command and flag refusals; settings file and index off pin; changed run file; Y on X;
  hashes-only refusals). `test_oext_78b_lean.py` 8 (rebuild by the substitutions; each substitution needed; sealed
  files byte-equal; record differs only in the five identity fields; true label; pending; globals; timer-origin
  order). `test_oext_78b_w1_18.py` 5 (record byte parity; globals; provenance equals the family hash and oext_eval
  reads it; a 1B-settings record refuses; derived settings on the family's paths; theta0's null pin). And
  `test_oext_78b_files.py` 18.
- **Parity (M).** The wrapper's output folder equals the 1B main's, run on the same out path (the 1B tests'
  injection, with the same documents). The answer, judge, summary, `job.json`, `identity.json`,
  `dependencies.json` and `assets.json` files are equal byte for byte. Ledger, progress, status and COMPLETE.json
  are equal once the wall-clock fields are dropped. The W1-18 record is equal byte for byte. For lean, the 9 sealed
  files are byte-equal. The c0 record differs only in `provenance.script` (the copy), `provenance.script_sha256`,
  `provenance.settings_sha256`, and two COMPLETE.json hashes that carry times.
- **Suite (M).** `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS:
  before, **208 passed, 57 skipped**; after, **274 passed, 57 skipped** (exit 0 both times). Track O's folder alone:
  66 passed.
- `git --no-optional-locks -C WS diff --stat -- scripts/stage1 scripts/stage1_s1` is empty (M; a test checks it too).

## 4. Mutants (M)

The spec has 41 mutants: 27 on the wrapper, 13 on the maker and 1 on the copy. The runner is
`tests/oext/run_mutants_oext_78b.py`, the kit runner's form: it copies `scripts/scale78b`, links the rest, and
counts a kill only on a real test failure; an error or a timeout is invalid.

Final shards on the final code and spec (spec `d37e69b6…`), each with its own baseline (66 passed), under the sandbox:
1/4 11 killed (80 s), 2/4 11 killed (106 s), 3/4 11 killed (42 s), 4/4 8 killed (19 s). **41 of 41 killed. 0
survived, 0 invalid, and no ERROR line** (reports `R/r1-o-scratch/mut-final-{1..4}.json`).

Earlier runs, which led to fixes:
- The first shard reached the workspace's files, not the copy, because the 1B fixtures put the resolved workspace
  root first on `sys.path`. Fix: the conftest binds `scripts.scale78b` to its own root (`tests/oext/conftest.py`).
- `O-w-file-pin` survived because the 1B loader also refuses with both hashes. I made the test name the wrapper's
  message.
- `O-w-w1-arg` was an equivalent mutant. `overrefusal_checks.main` reads its `--settings` default from the global
  at call time (:533), so dropping either `--settings` or the `SETTINGS_PATH` patch alone changes nothing. I replaced
  it with dropping both. It is killed.

## 5. Commands for the lead's full runs

```
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'; PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
cd <WS> && sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/oext/run_mutants_oext_78b.py <WS> <NEW_SCRATCH> <OUT>.json ALL --timeout 600
$PY -B <WS>/scripts/scale78b/make_oext_settings_78b.py --check            # the files equal the derivation
$PY -B <WS>/scripts/scale78b/oext_78b.py check                            # $0: pins, files, branches, waits
$PY -B <WS>/scripts/scale78b/make_oext_settings_78b.py --oext-78b olmo2-7b   # RK OEXT_78B[F]'s form, for the fill
```
The ALL mutation run takes about 4 min (E: the sum of the four shards).

## 6. Commands run (all in the foreground unless noted; exit status)

- `cat` and `sed` of the round brief, GXB, plan-ab §0-§2 and §4-§5, DES (E1-E5, DESO, DESO2), Part 2 §1.13-§1.16 and
  §4.2-§4.5, and the AM1 headings: exit 0.
- Reads in WS of the 1B scripts (`oext_unit.py`, `oext_eval.py:1-420`, `lean_eval_job.py`, `overrefusal_checks.py`,
  `limits_common.py:136-200`, `oext_unit_y.py` diff), their tests and fixtures, `scorers_78b.py`, `rules_78b.py`
  (KIT, OEXT_78B and SC pins), and the kit mutation runner: exit 0.
- `dumpkeys.py` on the 1B settings (keys, hashes, identifiers and text lengths): exit 0. `c3_check.py` (C3): exit 0.
- `git -C MAIN grep` and `git show` of the committed G1 record (hashes): exit 0. Manifest key and count reads of
  both 7-8B prepared sets in MAIN `tmp/kt-prepared/` (the dev bank kinds and `bank_import.source_manifest_sha256`):
  exit 0.
- Baseline suite (208 passed, 57 skipped): exit 0. Maker writes and `--check`: exit 0. Wrapper `check`: exit 0. The
  three real-file refusals (`unit` OLMo, `unit` Llama, `w1_18` OLMo): exit 2 as designed. `--oext-78b` for both
  families: exit 0.
- Probe runs (`probe_unit.py`, `probe_lean.py`): exit 0. The oext test runs during the build: one expected failure
  that I fixed (Y files follow the branch), then passes.
- Mutation runs: a baseline-only run (exit 0); a first 20-mutant shard (it ran in the background after the tool's
  180 s limit; I read its output file after it ended and waited on no notification; 19 killed, 1 survived, fixed);
  re-runs of 2 single mutants; a 10-mutant shard (9 killed, 1 equivalent, replaced); an 11-mutant shard (11 killed);
  then the four final shards above (exit 0). I deleted every scratch mirror after its run.
- Final suite: 274 passed, 57 skipped, exit 0. `date -u` before each time written.

## 7. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Step 1 decisive check reported first | passed | §0 |
| Wrapper or copy outputs equal the 1B script's, byte for byte, on the 1B fixtures | passed (outside wall-clock fields and the copy's own identity) | §3 parity; unit, lean and w1_18 parity tests |
| `git diff --stat -- scripts/stage1 scripts/stage1_s1` empty | passed | M, §3 |
| Refusal of the other family's manifest | passed | `test_the_other_familys_manifest_refuses` |
| Refusal under the pending branch | passed (wrapper wait and 1B refusal) | unit and lean pending tests |
| W1-18 record provenance = the family settings' hash | passed | `test_the_records_provenance_is_…` |
| Y variant refuses on X | passed | two tests (fixture and derived) |
| Every refusal names hashes only | passed (no fixture text in any refusal; the hash refusals carry 64-hex) | `test_every_refusal_names_hashes_pins_and_flags_never_text` |
| Llama G null with a wait (O11) | passed | `test_the_waits_name_their_pins_and_events`; real `unit --family llama31-8b` refuses with `RECIPE_G` |
| Side units by COMPLETE.json (RK KIT) and job.json only where committed | passed | `test_the_side_units_are_rk_kit_a0_units_with_the_committed_job_pins` |
| `--w1-18-record` and `--dev100-source` (DESO item 9), the wrapper's side | passed | the Branch-128 flag tests |
| Mutants all killed, shards under 10 min | passed (41/41) | §4 |
| A real 7-8B run of any command | not tested (no pod; no unit's answer opened; the W1-18 model path is faked as in the 1B tests) | — |
| No unit answer, generation or guard file opened | passed (only fixtures) | — |

## 8. Open points for the lead (I decided none of them)

- **P1. The route.** I built the hybrid of §0: one wrapper, with a copy only for lean, because of :229. Accept it, or
  ask for a full copy route. A full copy route still needs the W1-18 globals unless `oext_eval.py` is copied too,
  which Part 2 §4.4 excludes.
- **P2. Theta0's job.json pins** (both families) are null. W1-18 refuses for both families until a recorded lead step
  hashes the two units' job.json files, checks each equals its COMPLETE.json `job_sha256`, and fills
  `families.F.units.untuned.job_sha256`. This is on the W1-18 pod's critical path (DESO2 item 37). The fill changes
  the W1-18 settings hash, and through it `oext_eval__F`, `oext_unit__F`, `lean_eval_job__F` and the index. So fill
  in this order: theta0 pins, then the W1-18 run, then the branch, then `OEXT_78B[F]`. For Llama, the G config also
  comes before `OEXT_78B[F]` (O11).
- **P3. Kit changes (Track K, files I may not touch).**
  - RK `OEXT_UNIT_SCRIPT` and `C0_SCRIPT` should become `scripts/scale78b/oext_78b.py`.
  - RUN78 should call `oext_78b.py unit --family F run …`, `oext_78b.py lean --family F run …`, and for W1-18
    `oext_78b.py w1_18 --family F --out … --data-root … --device cuda --guard-batch-size N`, once per family on the
    one pod.
  - The Y pass is `unit --family F --engine Y run …`, with an RK pin `OEXT_78B_Y[F]` (the Y files are outside
    `OEXT_78B[F]`'s form here).
  - Under Branch 128 the form needs the family's W1-18 record added to `files` (P2 §4.4). `oext_78b_form` lists the
    W1-18 module and settings always (oext_eval binds them in every branch), but not the record.
- **P4. Llama's theta0 unit** was made under the LR 1e-4 kit's recipe (`c5462c77`; P1:86), not MAIN_F. W1-18 does not
  compare recipes. Its judge recipe and codec are MAIN_F's, the same Llama tokenizer (I: not measured). I labelled it
  `lr1e-4-kit-init`.
- **P5. W1-18 fields kept from 1B.**
  - `allow_list.refused_recipes` still lists the 1B recipe S `ceffe0ef…` only, because S_78 does not exist yet. The
    side units are MAIN_F units, so this is not binding at 7-8B (I).
  - `source_map.sealed_map` is null, as at 1B, so the per-source tables (report only) are unavailable. The extraction
    pin `bd1e40df…` equals both 7-8B manifests' `bank_import.source_manifest_sha256` (M).
- **P6. The lean job's `expected_counts`** stay at the 1B values. Harm 200 and over-refusal 100 are M for both
  manifests. Task rows 200 is I (not measured); the lean job refuses before any folder on a mismatch.
- **P7. c0's timer.** Under the wrapper, the interpreter start and the wrapper's stdlib imports come before the
  copy's origin. On Linux the record's `process_age_at_origin` covers them (R: `lean_eval_job.py:76`, :88-90). The size
  is not measured (E: well under a second, standard library only).
- **P8. Rule texts.** The derived files keep the 1B rule texts, except the requirement, the recipe rules,
  `c0_estimate`, W1-18's `units_source`, `pins` and `allow_list.rule`, which I rewrote for 7-8B. Some kept texts may
  still name 1B facts (for example "section 11"). They are prose only, and no code reads them.

## 9. Concerns

- **The print rule.** While locating the job.json hashes, I printed the non-hash fields of the committed G1 record's
  unit rows once: the G1 verdict (`pass`/`fail`), `answers_end` and the unit paths. These are a committed, text-free
  readiness record of the side probes, not a stage-1 or 7-8B outcome. But it goes beyond "keys, sizes and hashes
  only". I also printed short identifier strings and the 1B allow-list regex from the 1B settings. No prompt,
  answer, judge or sealed text was opened or printed.
- **No index refresh.** I ran `git status` twice without `--no-optional-locks` early on. This can refresh WS's
  worktree index stat cache (no content change). After that I used `--no-optional-locks`.
- **The wrapper replaces two functions for the call.** `oext_unit.load_pinned_settings` and
  `oext_eval.load_pinned_settings` are replaced by bound partials of the originals. Anything else in the same process
  that calls them during the call gets the family's file. In the unit and lean flows, only `main` calls them (R).
- **The W1-18 model path is not tested** (the guard and the policy codec on CUDA), as in the 1B tests. Neither is the
  CUDA path of any command.

## 10. Fix round (written 2026-11-08 16:44 UTC, `date -u`)

Inputs: the verifier's `R/r1-o-verify.md` (O1-O12) and the lead's sixth set R-5 to R-9 (R78
`lead-rulings-ab-build-20261108.md`). The same rules applied: new files only under `scripts/scale78b/`, no git state
change, no pod, network or download. I opened no unit, answer, generation or guard file; the tests use fixtures.
My pre-fix copies are in `R/r1-o-scratch/prefix/`. The unified diff against them is `R/r1-o-scratch/fix.diff`
(3,084 lines; `diff -ruN prefix postfix`).

### 10.1 What changed, per item

- **O1 / R-5 (major): one index per family and engine.**
  - `settings/OEXT-78B.json` is deleted (it was my own new file). The maker writes `OEXT-78B__F.json` (engine X:
    `oext_unit`, `oext_eval`, `lean_eval_job` and the W1-18 settings) and `OEXT-78B-Y__F.json` (engine Y:
    `oext_unit_y`, `oext_eval_y` and the W1-18 settings that `oext_eval_y` binds).
  - Each index holds only its own files' SHA-256, the family's branch and manifest, and the waits of its files (each
    wait's roles cut to that index). It also holds the fixed inputs and bases, and the other families' manifests.
    Those manifests are fixed values; they are there only so a refusal can name them. It no longer records the pins
    file's hash.
  - The wrapper holds **no index hash** (`INDEX_SHA256`, `INDEX_PATH` and `SETTINGS_DIR` are gone). Every command
    takes `--family F [--engine X|Y] --index PATH --index-sha256 H`, the pin the kit takes from `OEXT_78B[F]` or
    `OEXT_78B_Y[F]`. `Index` (oext_78b.py) refuses in four cases:
    - a file name that is not the named family's and engine's index;
    - bytes that do not hash to the named SHA-256;
    - contents whose `family` or `engine` differ from the CLI;
    - a listed file that is off its pin.
  - The settings files are read from the index's folder. A path label is computed from the index entry of the
    loaded file, never from the file's own text.
  - **Cascade (M).** The verifier's `cascade.py` now stops with `AttributeError: ... has no attribute 'INDEX_NAME'`,
    because the literal and the single index are gone (`R/r1-o-scratch/cascade_original.out`). Its adapted copy,
    `R/r1-o-scratch/cascade_fix.py` (output `cascade_fix.out`), runs the verifier's four fills and two more:
    | Fill | Forms that change |
    |---|---|
    | Llama branch | `OEXT_78B[llama31-8b]`, `OEXT_78B_Y[llama31-8b]` |
    | Llama θ0 pin | `OEXT_78B[llama31-8b]`, `OEXT_78B_Y[llama31-8b]` |
    | `engine_y` | `OEXT_78B_Y[llama31-8b]`, `OEXT_78B_Y[olmo2-7b]` |
    | OLMo B+Qi | `OEXT_78B_Y[olmo2-7b]` |
    | OLMo branch | `OEXT_78B[olmo2-7b]`, `OEXT_78B_Y[olmo2-7b]` |
    | Llama G | `OEXT_78B[llama31-8b]` |
  - The same check is now a test, `test_a_fill_reaches_only_its_familys_and_engines_pins` (6 cases). It also holds
    the wrapper and run-file entries of every form equal before and after each fill. Note that a family's branch or
    θ0 fill reaches both of that family's engines, because the W1-18 settings and the branch bind both. That is
    "that family's" pins, per R-5.
- **O6: the fill procedure leaves the suite green.**
  - The committed-state tests now check consistency only. `consistency(settings_dir, pins_path)` in
    `test_oext_78b_files.py` covers:
    - the maker's `--check`;
    - each index against its files and against the waits the pins imply (written independently: a null pin is a
      wait);
    - the KIT units, with the job pins compared to the committed G1 record where filled;
    - every X file through the 1B validators via the wrapper's `check` (`valid`, or `waits` where a pin nulls it);
    - the forms against RK's `oext_form_problem`;
    - the device, the generation and guard blocks, and the true labels.
  - `test_the_documented_fill_leaves_the_committed_state_checks_green` runs the documented fill (edit a copy of the
    pins, then `make_oext_settings_78b.py --pins P --settings-dir D`) on temporary copies. It covers 6 cases: θ0
    OLMo, Llama G (the 1e-4 G config as a stand-in), `engine_y`, B+Qi OLMo, the OLMo branch with a W1-18 record, and
    everything at once. In each, the same `consistency` passes, the R-6 record check included.
  - The null-pin behaviour (each command's refusal with its event, the 1B validators' refusals) is tested on a
    temporary all-null copy (`all_null` fixture).
  - The maker's header now gives the procedure: edit the pins, run the maker, run the tests, then print the form.
    There is no wrapper literal to set.
- **O7 / R-6: `check --w1-18-record F`.** It runs the unchanged `oext_eval.read_w1_18` under the family's O-ext
  settings and W1-18 globals ($0, on the Mac). It refuses in these cases:
  - the record's units are not the family's W1-18 units;
  - the settings pin a record and none is given;
  - a record is given and none is pinned.

  Tests (`test_oext_78b_check.py`): the right record passes; a record from the other family's settings, a stale
  record (the family's settings were edited after the run) and a wrong-branch record (failing under 128) refuse; the
  same record passes under `full`; and records of other units, a missing record and an unpinned record refuse.
- **O8 / R-7.** The W1-18 settings derive `judge.device = "cuda"` (maker `limits`; checked in `consistency`).
- **O9 / R-8.** `--oext-78b-y F` prints `OEXT_78B_Y[F]`: the wrapper, the unit command's 1B files (no lean copy),
  `OEXT-78B-Y__F.json`, `oext_unit_y__F`, `oext_eval_y__F` and the W1-18 settings. Tests check it against RK's
  `oext_form_problem` and check that it holds no lean copy.
- **R-9: `check --data-root DIR`.** For each listed side unit, it reads COMPLETE.json by its pin and requires that
  `job.json` (the list entry, or COMPLETE.json's `job_sha256`), `eval/<ck>/generations.jsonl` and
  `eval/<ck>/guard.jsonl` are each listed with a SHA-256. Each present file's bytes must hash to it (hashed, never
  parsed), and job.json must equal its pin where the pin is filled. The output is names, states and hashes only, and
  it exits 2 on any problem. Tests on fixtures: all files listed; an unlisted file, a changed file, a COMPLETE.json
  off its pin and a job.json off its pin each refuse; no fixture text is printed. **Commands for the lead on the real
  units** (from the checkout that holds the files, after this lands; the data root is MAIN's `tmp/`):
  ```
  PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
  for F in olmo2-7b llama31-8b; do IDX=scripts/scale78b/settings/OEXT-78B__$F.json
    $PY -B scripts/scale78b/oext_78b.py check --family $F --index $IDX --index-sha256 $(shasum -a 256 $IDX | cut -c1-64) \
      --data-root /Users/spiderishi/Coding/attribution/tmp; echo "exit $?"; done
  ```
  The θ0 job pins show as `null (waits)` until T-O2 step 1.
- **O2 (label lies).** New tests: `test_a_unit_settings_file_naming_another_oext_file_refuses` (the 1B path and the
  other family's) and `test_a_lean_settings_file_naming_the_1b_oext_file_refuses`.
- **O3.** New tests:
  - `test_lean_refuses_the_other_familys_prepared_set_and_a_missing_w1_18_record` (the wrapper's own message, so the
    verifier's "equivalent" `V-w-lean-no-branch-flags` is now killed);
  - `test_every_command_refuses_a_changed_run_file` (unit, lean, w1_18);
  - `test_the_unit_settings_manifest_must_be_the_indexs`;
  - the forms in `consistency` list every file of each index.
- **O4.** The restore-on-exception cases are now tested on their own:
  - `test_the_globals_are_restored_when_the_1b_main_raises` (argparse `SystemExit` inside `oext_unit.main`);
  - `test_the_lean_globals_are_restored_when_the_copy_raises`;
  - `test_w1_18s_globals_are_restored_when_the_1b_main_raises`.
- **O5.** No module global is patched by the tests any more: there is no index literal, and the fixture's
  other-family manifest is a per-instance attribute, restored in `finally` on the module-scoped world. The
  verifier's two-families-in-one-process W1-18 probe is a test.
- **O11.** The maker loads `oext_78b.py` from `HERE` by file path (`wrapper_module`). A test checks that the printed
  wrapper hash equals the file beside the maker. In the mutation mirror both roots are the copy, so no mutant can
  show the difference; this is stated, not claimed as killed.
- **O12.** §0 reason 3, §1 (WS `tmp/` exists and is empty) and §2 (fill reach) are corrected in place.
- **O10 (for K3).** *Corrected in fix round 2 (OR4, R-20): the W1-18 pod takes `W1_18_78B`, not `OEXT_78B[F]` (null until after W1-18). Its index is `OEXT-78B-W1__F.json`; see §11.* The W1-18 pod's kind must name these files, beyond `W1_18_78B`'s:
  - the frozen readers that `limits_common.frozen_reader` loads by path and pin from the W1-18 settings'
    `frozen_reader` block: `scripts/family_probe_reading.py` (`8848340107bd4acc…`) and
    `scripts/killtest_stage0_reading.py` (`1740663bc9e46542…`) (R: the settings; M: dumped earlier);
  - the lexicon files the settings name: `scripts/stage1/lexicon/lexicon.py` and `lexicon.json` (classifier
    `5a27dd040b74aa23…`, json `bbbc71e9eebb6287…`; R: the settings);
  - the judge recipe = MAIN_F's config under `ENGINE_ROOT`, by its file SHA-256 (`judge.recipe`,
    `recipe_file_sha256` in `limits_overrefusal_checks__F.json`);
  - the guard model Qwen3Guard-Gen-4B at the pinned revision, the policy tokenizer of MAIN_F, and the family's
    prepared set (`prepared.path`) under the pod's data root;
  - the side units at their paths under the data root.
  `--device cuda` is now the settings' default (R-7).

### 10.2 Files after the fix (SHA-256, M: `shasum -a 256`)

| File (under `scripts/scale78b/`) | SHA-256 | Changed |
|---|---|---|
| `oext_78b.py` | `8b0ad90a0ee8b1a969f6725b6f45cace67750dcd9bd625de415c01267a0681b0` | yes |
| `lean_eval_job_78b.py` | `fc0372ca006c478f9b4b3bff3c903f9d15f774b94c61a6b4aca98973c400e4a7` | no |
| `make_oext_settings_78b.py` | `70d1215cc62bfec4fe5ee8ada21db9b1590ee019f04200f55fe3473c627ec4f7` | yes |
| `settings/oext_pins_78b.json` | `ad4458216104ae227471aaabcdfed83260a80337feecd3f43fdd3ba94d6361c0` | no |
| `settings/OEXT-78B__olmo2-7b.json` (new) | `d41b0229b93ad27160b6d3ef368820d10b1cf9d2416b07dcf7990a5e61f33cb7` | new |
| `settings/OEXT-78B__llama31-8b.json` (new) | `7b1ff8303daca5d7c95103bb6fa47e3cec5f4e69cfdc3d34f1ea1d83d50ec701` | new |
| `settings/OEXT-78B-Y__olmo2-7b.json` (new) | `f745eebba6af7338d1411805db4b88726f7f6be7d5281b85b1332c026863a157` | new |
| `settings/OEXT-78B-Y__llama31-8b.json` (new) | `5ed4ca12c1082603a66fb82ef88fe25fbd45158c75bd6f9e6a89fc0b62154cd9` | new |
| `settings/OEXT-78B.json` | (deleted) | deleted |
| `settings/limits_overrefusal_checks__olmo2-7b.json` | `529fda92f6201f2455bd416f64ca8deb737da9dbb8c5e548b7e77a67c8f8e26f` | yes (device) |
| `settings/limits_overrefusal_checks__llama31-8b.json` | `803955c629c8e357e78bda57d8cfe9a13106f475fcec32bc14db99ae01497949` | yes (device) |
| `settings/oext_eval__olmo2-7b.json` | `1323d4f84ef3b9c5c57046deab9da0c03c3a5e416a37b16d4c9f198d67dfd88d` | yes (the W1-18 hash) |
| `settings/oext_eval__llama31-8b.json` | `43f21359f565e0c28d361d941639e0170d8dc8ea4be9d06a3a8e9e77faa61199` | yes |
| `settings/oext_eval_y__olmo2-7b.json` | `4e120dd8b585d9067c2e0c002fd9af3c05d1010f6544d16a2e42793cbcdb27fb` | yes |
| `settings/oext_eval_y__llama31-8b.json` | `70e31d080a34445f4a32ecdc412f5fe3db668cc10f33950f141a87769c3ec5ea` | yes |
| `settings/oext_unit__olmo2-7b.json` | `0d2572d9160e8e95ea0eac196cc34e10f298ad20dd4cffc6fed859b3912536b4` | yes (oext_eval hash) |
| `settings/oext_unit__llama31-8b.json` | `735f54a9cc573923e2fa36174064b63596c58f9eac0585c259a8e45e00ced845` | yes |
| `settings/oext_unit_y__olmo2-7b.json` | `536fe1f71b9b201886c53cb1f22bdcc5f1e74d48737bcc0b74f2b36004b40472` | yes |
| `settings/oext_unit_y__llama31-8b.json` | `61f2ebb1fd689dcceab6d0df56a9c187563d71f63499cdddfd529ac1db593e57` | yes |
| `settings/lean_eval_job__olmo2-7b.json` | `29beac94b27c0c90fcf8e572c7f22d7049fa5f67e4483e38792aa1a5b38dc8d3` | yes |
| `settings/lean_eval_job__llama31-8b.json` | `5910112f7882a974e4eec071df96e09036a0c2b4e9b833389b04796bf4b29f13` | yes |
| `tests/oext/conftest.py` | `823bafb4ce86c5cee338ce907563a6fd325e5c1b23278819a8eaf0072123daef` | no |
| `tests/oext/lean_copy_spec.py` | `f5f5e27430a48fe906fb17eb3d3ac6ae730b9f170d9897cf1e603e9e9012ea48` | no |
| `tests/oext/oext78_fixtures.py` | `77e695cfe3465a5b4040a739def75320d73edce2cea72f26edebac0dc1eaf85c` | yes |
| `tests/oext/test_oext_78b_unit.py` | `39e7b1e79da4e24354ebad4d05a0c88365ce18ef7929a124cb0ea906afd98b60` | yes |
| `tests/oext/test_oext_78b_lean.py` | `2ee9f8c3175866cfd562062ae72a694de4aa557dee9881bcc41004d7cbd63ea0` | yes |
| `tests/oext/test_oext_78b_w1_18.py` | `761c41d4ce47abd32c7b8fbc1f647c718fc131e9ec4506c9c2bf0b09e916b4f6` | no |
| `tests/oext/test_oext_78b_files.py` | `79a2321ddb1c21b9326c437beb883cfc5d32b19ad22adf96f5f7f9f5efd64f56` | yes (rewritten) |
| `tests/oext/test_oext_78b_check.py` (new) | `d433d22de30193eddac179e3ed8c186c66d137d2060a64959b97ea8ab7d98e8b` | new |
| `tests/oext/mutation_spec_oext_78b.json` | `b40c843b759314cdb85f0a5068f48c56880aab70dddd8470eb8edfdba5634d6f` | yes (67 mutants) |
| `tests/oext/run_mutants_oext_78b.py` | `3effdaf80a5d0d6ee8e658c431d835b9b119f32f0887dafcf82eb97b243e0a02` | no |

The current kit forms (M: `make_oext_settings_78b.py --oext-78b F` / `--oext-78b-y F`) name these four index hashes
and the wrapper `8b0ad90a…`. They are for the lead's recorded fills, after T-O2's order.

### 10.3 Counts (M)

- **Suite.** `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS: **307
  passed, 57 skipped** (before the fix round, 274 passed and 57 skipped). Track O's folder: 99 passed (66 before).
- **Mutants.** The spec `b40c843b…` has **67 mutants**:
  - the R1 spec's 41, with 9 stale find texts updated;
  - the verifier's 11 proposed mutants (`V-*`, adapted to the per-index design);
  - 15 new ones (`R5-*` 4, `R6-*` 4, `R7-*` 1, `R8-*` 1, `R9-*` 5).

  Run in 9 shards of at most 8 mutants, each with its own baseline (99 passed), under the sandbox. Shard 2 took 63 s (M); the other shards ran in pairs, each pair inside one command's 178 s limit (M):
  **67 of 67 killed; 0 survived, 0 invalid, no ERROR line** (`R/r1-o-scratch/mut-fix-{1..9}.json`). I deleted every
  scratch mirror after its run.
- `git --no-optional-locks -C WS diff --stat` is empty (no tracked file changed). WS has no `__pycache__` folder
  under `scripts/scale78b`.

### 10.4 Commands for the lead's full runs (updated)

```
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'; PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
cd <WS> && sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/oext/run_mutants_oext_78b.py <WS> <NEW_SCRATCH> <OUT>.json ALL --timeout 600   # about 8 min (E: 9 shards x 60 s)
$PY -B <WS>/scripts/scale78b/make_oext_settings_78b.py --check
$PY -B <WS>/scripts/scale78b/make_oext_settings_78b.py --oext-78b F ; ... --oext-78b-y F
$PY -B <WS>/scripts/scale78b/oext_78b.py check --family F [--engine Y] --index <IDX> --index-sha256 <H> [--w1-18-record R] [--data-root D]
$PY -B <R>/r1-o-scratch/cascade_fix.py <WS>
```

### 10.5 Open points and concerns added by the fix round

- **K1 and K3 must pass the index** *(corrected in fix round 2, §11: the `w1_18` kind takes the W1 index from `W1_18_78B`, not from `OEXT_78B[F]`)*. Every O-ext command now needs `--index` and `--index-sha256`. RUN78 must take
  both from the job's `OEXT_78B[F]` or `OEXT_78B_Y[F]` entry for `scripts/scale78b/settings/OEXT-78B[-Y]__F.json`.
  The pack must run `oext_78b.py check` (with `--w1-18-record` once a branch is pinned) before any O-ext pod (R-6).
- **One fill reaches both engines of a family.** A family's branch or θ0 pin fill changes both `OEXT_78B[F]` and
  `OEXT_78B_Y[F]`, because the W1-18 settings and the branch bind both engines. I read that as within R-5 ("that
  family's"). If the lead wants Y untouched by X-side fills, Y needs its own W1-18 settings copy (not built).
- **The R-9 check hashes the bytes of each unit's generations and guard files.** It reads them as bytes and never
  parses or prints them. If "by name and SHA-256 only" is meant as listing-only (no file read at all), drop the hash
  comparison: one `elif` in `check_side_units`.
- **O11's fix is not mutation-tested.** In the mirror both roots are the copy, so no mutant can show the difference.
- **Concern from R1, still true:** I printed G1 verdict fields once in R1 (§9). Nothing like that in this round.

## 11. Fix round 2 (written 2026-11-08 18:10 UTC, `date -u`)

Inputs: the re-verifier's `R/r1-o-reverify.md` (OR1-OR9) and its scratch, and the lead's ninth set R-20 to R-23.
The rules are unchanged. The fix-round-1 copies are in `R/r1-o-scratch/prefix2/`; the unified diff is
`R/r1-o-scratch/fix2.diff` (1,815 lines). I opened no real unit, answer, generation or guard file, and I ran
`check --data-root` only on fixtures.

### 11.1 What changed, per item

- **OR1 (major): the documented fill, done in place, leaves the suite green.**
  1. The θ0 null-pin test (`test_oext_78b_w1_18.py`) now derives its W1-18 settings from an all-null copy of the
     pins, not from the committed file.
  2. A committed W1-18 record can now be found. The pins hold `families.F.w1_18.record_path` beside
     `record_sha256` (both are set, or both are null). The path must be a plain `.json` path under R-21's folder
     `.ai/inputs/stage1-post-w1-20261023/78b/w1-18/`. The maker refuses a record that is not at that path with that
     hash (`verify_records`; `--records-root` exists only for dry runs). The X and Y indexes carry the record's path
     and hash. `consistency()` reads the record from its path and runs the R-6 check on it.
  3. The fill tests now start from the pre-fill (all-null) state and follow T-O2's order, cumulatively:
     | Step | Fill |
     |---|---|
     | 1 | θ0 OLMo |
     | 2 | θ0 Llama |
     | 3 | OLMo branch 128 (its record committed at its R-21 place) |
     | 4 | Llama G |
     | 5 | Llama branch full (with a failing record) |
     | 6 | ENGINE_Y |
     | 7 | B+Qi OLMo |
     | 8 | B+Qi Llama |

     The test is parametrized over the 0..8 prefixes (9 cases), each run through the same `consistency`. The
     null-pin tests and `derive()` also use the all-null state.
  4. New test `test_the_documented_fill_in_place_leaves_the_suite_green`. It builds a copy of the checkout in
     `rv_fill.py`'s form (this package copied, every other entry linked, R-21's folder real), runs all 8 steps with
     the maker's defaults, then runs this test folder in the copy. M: it passes.
  - **The re-verifier's form, per step (M).** `R/r1-o-scratch/rv_fill2.py` is `rv_fill.py` adapted to the record
    path. For steps 0..8 (`rv_fill2_{0..8}.out`), each was done in place, `--check` ran (exit 0), then the whole
    scale78b suite ran. **Track O failures: 0 at every step and after all of them.** The suite shows 5 other
    failures, the same in every state, the no-fill control included, so they are not caused by a fill:
    - `test_s1_olmo2_7b_check_guard.py` × 4 (the re-verifier's mirror-only four);
    - `test_make_recipe_s78.py::test_any_s78_config…` × 1. This is I: an artifact of the copy's linked `.ai/`
      sub-folders, since the in-place copy must keep R-21's folder real.
- **OR4 / R-20, R-21: the W1-18 pod's route.**
  - A third index per family, `settings/OEXT-78B-W1__F.json`, lists the W1-18 settings only. It has no branch, no
    engine identity and no O-ext inputs. `oext_78b.py w1_18` takes this index (`--engine` for `w1_18` is W1 only).
  - `make_oext_settings_78b.py --w1-18-78b` prints `W1_18_78B`. Its `files` part is in K1's `{files: {path under
    scripts/: SHA-256}}` form: the wrapper (the file beside the maker), the `w1_18` run files (s1common,
    limits_common, overrefusal_checks), and per family its W1 index and W1-18 settings. Beside it, `side_units` lists
    per family each side unit by path (under the data root) with its COMPLETE.json and job.json SHA-256.
  - Cascade (test `test_a_fill_reaches_only_its_familys_and_engines_pins`, now 7 parts per fill): a θ0 fill reaches
    that family's `W1_18_78B` part. No branch, G, B+Qi or ENGINE_Y fill reaches `W1_18_78B`.
  - The record's place follows R-21 (above). The O-ext eval settings pin the record by SHA-256 and kind, as at 1B,
    and its path is given at run time (`--w1-18-record`).
  - The K3 notes in §10.1 (O10) and §10.5 are corrected: the W1-18 pod takes `W1_18_78B`, not `OEXT_78B[F]`.
- **OR2: the R-9 check is as strict as W1-18's own gate, and still hash-only.** `check_side_units` now also checks:
  - the path against the settings' `allow_list.path_pattern`;
  - W1-18's frozen sealed check (`limits_common.frozen_reader(...).sealed`), which hashes every listed file and
    parses none;
  - the `eval/` folder names against `[checkpoint]`.

  Tests: a listed but absent file, a second eval folder, and a path outside the allow-list form each refuse.
  job.json's fields stay a stated limit, because checking them needs parsing.
- **OR5.** The maker checks B+Qi's generation and guard blocks the same way as G's. Test: the g16 config as B+Qi
  refuses.
- **OR6.** The re-verifier's 11 proposed mutants are in the spec; 2 find texts were adapted to the new code
  (`RV-w-check-waits-mask`, `RV-w-check-pin-y`). Their targeted tests are in `test_oext_78b_check.py`:
  - B4: restore after a validator refusal, now including `s1common.code_identity`;
  - C1: an index of another kind, on each of `unit`, `lean run`, `lean verify`, `w1_18` and `check`;
  - D1: six records with a changed field;
  - E5: a unit folder linked out of the data root;
  - G1: `check` with a changed run file;
  - G2: job.json named beside the file list;
  - G3: a marker that is not complete;
  - G4: the maker's `--check` reports drift.
- **OR7.** A COMPLETE.json value that is not a SHA-256 is reported by its key only, never printed (`_hex_or_none`).
  Test: a text value placed in the file list is absent from stdout and stderr.
- **OR8.** A role that waits on a null pin prints exactly `"waits"` (exit 0), and only when the 1B validator's
  refusal is the one that pin causes (`WAIT_REFUSALS`: THETA0_JOB, UNIT_JOB, RECIPE_G, RECIPE_BQI; a null ENGINE_Y
  is "waits" without validating). Any other refusal exits 2. Test: a non-integer seed in a file that is waiting
  exits 2.
- **OR9.** A repeated leading option (`--family`, `--engine`, `--index`, `--index-sha256`) refuses. Test: 4 cases.
- **R-23.** The X and Y indexes carry `engine_identity` (engine X's, or `shared.engine_y`). `check` validates each
  settings file against that identity, running the unchanged 1B check under it (`on_engine`, patched only for the
  call and restored). Test on a filled copy: the Y files are `valid`, and an index naming another identity refuses.
- **R-22.** The index names stand (`OEXT-78B__F.json`, `OEXT-78B-Y__F.json`, and now `OEXT-78B-W1__F.json`).
  Aligning K1's form check is K1's change. Note: K1's `files_form_problem` takes exactly `{files}`, so
  `W1_18_78B`'s `side_units` part, which R-20 asks for, needs K1 to accept it or to keep it beside the pin.
- **The mutation runner** sets `OEXT78_NESTED=1`, which skips the nested in-place test inside mirrors: it reruns the
  whole folder in a copy and would make each mutant run about 30 s longer. That test runs in the plain suite, and
  `rv_fill2.py` runs its form per step.

### 11.2 Files after fix round 2 (SHA-256, M: `shasum -a 256`; all under `scripts/scale78b/`)

| File | SHA-256 | vs fix round 1 |
|---|---|---|
| `oext_78b.py` | `c6a9a9465451a4b965b451ec8c7cbc9db4d49c7388b10cfe50d718c630ff8b6f` | changed |
| `lean_eval_job_78b.py` | `fc0372ca006c478f9b4b3bff3c903f9d15f774b94c61a6b4aca98973c400e4a7` | same |
| `make_oext_settings_78b.py` | `6cd317a06d64daa5c6f00a730d76db613c983c619bc53b3e0a071a31dcc9fdd9` | changed |
| `settings/oext_pins_78b.json` | `9f3a93da251ae123d3769a2774e02a7656cae658e7493ccf71a07dd53baf3c37` | changed |
| `settings/OEXT-78B-W1__llama31-8b.json` | `87c8c0dbea08a9fc2ac80383b46f06e3048197a1f6e115f7ac293a2dae15807d` | new |
| `settings/OEXT-78B-W1__olmo2-7b.json` | `d85ff7a3622f94a83ea90a75388e010d3e473ea2491f01be0eabd44085c1b207` | new |
| `settings/OEXT-78B-Y__llama31-8b.json` | `13eb337be846cf9105380c8645e1085283b1f1a0feaec94fcb45d94c60a016a7` | changed |
| `settings/OEXT-78B-Y__olmo2-7b.json` | `0a030e36ffc7fd35058247ee123ed07fbce4af909d7deb9876bde7281cd496e0` | changed |
| `settings/OEXT-78B__llama31-8b.json` | `7bc002154eb07981a52fcf42506947e857e1be2185f892fd445efa5d0f6f9e03` | changed |
| `settings/OEXT-78B__olmo2-7b.json` | `6a16300ed3364cedcc9d80632be1e09f8a610739558b77a8c39c1375ee4d838d` | changed |
| `settings/oext_unit__llama31-8b.json` | `735f54a9cc573923e2fa36174064b63596c58f9eac0585c259a8e45e00ced845` | same |
| `settings/oext_unit__olmo2-7b.json` | `0d2572d9160e8e95ea0eac196cc34e10f298ad20dd4cffc6fed859b3912536b4` | same |
| `settings/oext_eval__llama31-8b.json` | `43f21359f565e0c28d361d941639e0170d8dc8ea4be9d06a3a8e9e77faa61199` | same |
| `settings/oext_eval__olmo2-7b.json` | `1323d4f84ef3b9c5c57046deab9da0c03c3a5e416a37b16d4c9f198d67dfd88d` | same |
| `settings/oext_unit_y__llama31-8b.json` | `61f2ebb1fd689dcceab6d0df56a9c187563d71f63499cdddfd529ac1db593e57` | same |
| `settings/oext_unit_y__olmo2-7b.json` | `536fe1f71b9b201886c53cb1f22bdcc5f1e74d48737bcc0b74f2b36004b40472` | same |
| `settings/oext_eval_y__llama31-8b.json` | `70e31d080a34445f4a32ecdc412f5fe3db668cc10f33950f141a87769c3ec5ea` | same |
| `settings/oext_eval_y__olmo2-7b.json` | `4e120dd8b585d9067c2e0c002fd9af3c05d1010f6544d16a2e42793cbcdb27fb` | same |
| `settings/lean_eval_job__llama31-8b.json` | `5910112f7882a974e4eec071df96e09036a0c2b4e9b833389b04796bf4b29f13` | same |
| `settings/lean_eval_job__olmo2-7b.json` | `29beac94b27c0c90fcf8e572c7f22d7049fa5f67e4483e38792aa1a5b38dc8d3` | same |
| `settings/limits_overrefusal_checks__llama31-8b.json` | `803955c629c8e357e78bda57d8cfe9a13106f475fcec32bc14db99ae01497949` | same |
| `settings/limits_overrefusal_checks__olmo2-7b.json` | `529fda92f6201f2455bd416f64ca8deb737da9dbb8c5e548b7e77a67c8f8e26f` | same |
| `tests/oext/conftest.py` | `823bafb4ce86c5cee338ce907563a6fd325e5c1b23278819a8eaf0072123daef` | same |
| `tests/oext/lean_copy_spec.py` | `f5f5e27430a48fe906fb17eb3d3ac6ae730b9f170d9897cf1e603e9e9012ea48` | same |
| `tests/oext/mutation_spec_oext_78b.json` | `0010a870d7a5f6dd3dca3db0cf4fff6835244f950a035b85fa80dfa0f185050f` | changed |
| `tests/oext/oext78_fixtures.py` | `9e93b4f4ca58c5d3a3a817773c736a7cf647f8e5d9c91ebaa6673ecd8b35c304` | changed |
| `tests/oext/run_mutants_oext_78b.py` | `0dc81003e19daac8b83c1cd84ce0465675b5b404b6667b78f1cca070b4128ca1` | changed |
| `tests/oext/test_oext_78b_check.py` | `860cf69fe76879aa06b7250f325d0357a019d0d9b821d4adab20ddc469a8f44a` | changed |
| `tests/oext/test_oext_78b_files.py` | `a8d6e9121ac6cca9397548ff4b25007e9bab010bb899626349227c2547e10d96` | changed |
| `tests/oext/test_oext_78b_lean.py` | `2ee9f8c3175866cfd562062ae72a694de4aa557dee9881bcc41004d7cbd63ea0` | same |
| `tests/oext/test_oext_78b_unit.py` | `a390acf5aee02a8f64cc6861ae409cbc780c7e4e242771e9385f9588c9f4207f` | changed |
| `tests/oext/test_oext_78b_w1_18.py` | `f8702608c4868ba4d14baa4bbfded9a98c988ad4fe10c4de5b8e674108430683` | changed |

### 11.3 Counts (M)

- **Suite.** `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS: **340
  passed, 57 skipped** (after fix round 1, 307 passed and 57 skipped). Track O's folder: 132 cases (99 after fix round
  1), including the nested in-place fill test.
- **In-place fill (OR1).** `rv_fill2.py` for steps 0..8 gives **0 Track O failures in every state**. The 5 other
  failures are the same in every state, the no-fill control included (`R/r1-o-scratch/rv_fill2_{0..8}.out`).
- **Mutants.** The spec (`0010a870…`) has **92 mutants**:
  - fix round 1's 67, with 4 stale finds updated;
  - the re-verifier's 11 (`RV-*`, 2 finds adapted);
  - 14 new `F2-*` mutants (OR2, OR5, OR7-OR9, R-20, R-21, R-23).

  Run in 22 shards of 5 or 3 mutants, each with its own baseline, under the sandbox (`R/r1-o-scratch/mut-f2-{01..22}.json`):
  **92 of 92 killed; 0 survived, 0 invalid, 0 ERROR lines.**
  - Shard 01 ran before the runner learned to skip the nested test (baseline 132 passed); the other 21 skipped it
    (baseline 131 passed, 1 skipped). The machine was loaded by other jobs (load average about 17), so shard times
    ranged from 2 to 4.5 min. Three shards ran past the tool's 178 s limit into the background; I read each one's
    result after it ended.
- `git --no-optional-locks -C WS diff --stat` is empty. There is no `__pycache__` under `scripts/scale78b`.

### 11.4 Commands for the lead

```
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
$PY -B scripts/scale78b/make_oext_settings_78b.py --check
$PY -B scripts/scale78b/make_oext_settings_78b.py --w1-18-78b          # W1_18_78B (fill after θ0's job pins, R-20)
$PY -B scripts/scale78b/make_oext_settings_78b.py --oext-78b F ; ... --oext-78b-y F
# R-9 on the real side units (the W1 index; the data root is MAIN's tmp/):
for F in olmo2-7b llama31-8b; do IDX=scripts/scale78b/settings/OEXT-78B-W1__$F.json
  $PY -B scripts/scale78b/oext_78b.py check --family $F --engine W1 --index $IDX \
    --index-sha256 $(shasum -a 256 $IDX | cut -c1-64) --data-root /Users/spiderishi/Coding/attribution/tmp; echo "exit $?"; done
# R-6 after a branch fill (the record at its R-21 place):
$PY -B scripts/scale78b/oext_78b.py check --family F --index scripts/scale78b/settings/OEXT-78B__F.json --index-sha256 H \
  --w1-18-record .ai/inputs/stage1-post-w1-20261023/78b/w1-18/<record>.json
# in-place fill proof, per T-O2 prefix k = 0..8 (whole scale78b suite in a scratch copy):
$PY -B R/r1-o-scratch/rv_fill2.py <WS> <NEW_SCRATCH> k
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/oext/run_mutants_oext_78b.py <WS> <NEW_SCRATCH> <OUT>.json ALL --timeout 600
```

### 11.5 Open points added by fix round 2

- **`W1_18_78B`'s `side_units`.** K1's form check accepts exactly `{files}`. R-20 names the side units in the pin,
  so either K1 accepts the extra key or the lead keeps `side_units` as a record beside the pin. They are pinned
  transitively anyway, through the W1-18 settings' COMPLETE.json and job.json pins.
- **The R-21 records folder does not exist yet** in WS or MAIN. The first branch fill commits the record there first,
  then names its path and SHA-256 in the pins.
- **Before each fill the lead should run the in-place proof.** The plain suite holds a fill in place only after it
  is committed (the nested test fills a copy from the all-null state, not from the committed state). Running
  `rv_fill2.py` before each recorded fill is the cheap guard.
