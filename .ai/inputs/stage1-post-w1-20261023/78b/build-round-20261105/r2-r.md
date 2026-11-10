# R2 Track R report: the 7-8B reference settings, Llama's recipe G at LR 5e-5, and Track O's follow-up

Written 2026-11-08, 21:29-21:38 UTC (`date -u` 21:29:38 and 21:37:25; started 20:33:24). Status: **DONE** for items 1-4, and the fix round (§11) is done;
item 5 (the `similarity` kind's settings) **not built**. WS = `B/ws-r` (detached at `bfda225`; MAIN's HEAD is
`bfda225` too, M: `git rev-parse`). Tags: M measured (command named), R read (path:line in WS), E estimate, I inference.
No git state change, no pod, network, install, download, agent or message. No forbidden folder, unit, answer,
generation, guard, judge, sealed or prompt-text file was opened; tests use synthetic fixtures. From settings,
manifests and configs I printed keys, sizes, short identifiers and hashes only (the 1B settings' prose fields were not
printed or read; see Concerns).

## 1. The decisive check (item 1) and the route chosen

**Question.** Can one wrapper run each 1B reference script with per-family settings while every 1B file stays byte
for byte and no record names a file it did not load (GXB O3; T-O1's per-script rule)?

| Seam (R: WS path:line) | What it does | Module global with a true label? |
|---|---|---|
| `eval_adapter.py:394-396` `load_pinned_settings(path=SETTINGS_PATH)` | default path bound at definition; `SETTINGS_SHA256` read at call time; `main()` calls it with no argument (:1880) | **Yes.** For the call the wrapper sets `load_pinned_settings` to the original bound to the family file, and `SETTINGS_PATH`, `SETTINGS_SHA256` to that file (`refs_78b.py:314-316`). |
| `eval_adapter.py:140`, `:376` `OEXT_SETTINGS_PATH` | `oext.settings.path` must equal this global | **Yes**, set to the index entry's label of the loaded `oext_eval__F.json`. M: a file naming the 1B O-ext path refuses under the wrapper (`test_a_label_lie_refuses`). |
| `eval_adapter.py:1868` `oe.load_pinned_settings()`; `:1890` `oe.SETTINGS_PATH` | O-ext settings from the 1B default; B10's `check` hashes `oe.SETTINGS_PATH` | **Yes** (Track O's seam): bound to the family file; `SETTINGS_PATH` set. M: B10 `check` prints `settings_at_pin: true` under the wrapper. |
| `oext_eval.py:214-236` W1-18 binding | reads `overrefusal_checks.SETTINGS_PATH/SHA256` | **Yes** (Track O's `_w1_pairs` form; `refs_78b.py:290-297`). |
| `eval_adapter.py:221-252`, `:1017-1035`, `:1038-1100` external transform | module and settings by REPO-relative path and SHA-256 from the settings | **No global needed**: `eval_adapter__F__S.json` names `scripts/stage1_s1/safe_lora.py` (unchanged, `5f6b7822…`) and `scripts/scale78b/settings/safe_lora__F__S.json`, the files read. The wrapper also checks both against the index (`check_bindings`, `refs_78b.py:272-283`). |
| `eval_adapter.py:258` `owner`; `:1309` `b10.script = OWNER`; `:1216` `script_sha256` | the settings and records name `scripts/stage1_s1/eval_adapter.py` | **True as is**: that file is what runs. |
| **`eval_adapter.py:1579-1590` self-hash** | `script_code_sha256()` hashes the script's own bytes with the settings literal zeroed; a certification certifies it (`:1643`) | **Unaffected and true**: the wrapper changes no byte, so a 7-8B certification certifies the 1B code that runs (M: B10 `check` under the wrapper prints `script_code_sha256` = `ea.script_code_sha256()`). A copy route would instead certify a different code identity and need a parity test of its own. |
| `safe_lora.py:96-97`, `:318-322` | `load_pinned_settings()` reads `SETTINGS_PATH` and `SETTINGS_SHA256` at call time | **Yes**; the 1B tests set the same two globals (R: `scripts/stage1_s1/tests/test_b11_transform.py:501-502`). The record's provenance names `safe_lora.py` and the family file's hash (`safe_lora.py:708`, `:824`); no path is written. |
| `overlap_similarity.py:69`, `:419`, `:424` | `--settings` default read from the global inside `main`; `SETTINGS_SHA256` at call time | **Yes** (seam only; its settings are not built, item 5). |

**Route: the wrapper for both scripts; no copy.** Every seam is a module global or a settings value naming the true
file; no literal path check exists (unlike `lean_eval_job.py:229`). `scripts/scale78b/refs_78b.py` runs the unchanged
`eval_adapter.py` and `safe_lora.py`; M: `git diff --stat -- scripts/stage1 scripts/stage1_s1 runkit` is empty, and
`test_the_1b_files_are_unchanged` holds the 1B files' hashes. Records name only files that were loaded (M:
`test_every_record_names_the_files_that_ran`: no output contains the 1B settings hash, a 1B settings path or any
`eval_adapter__` label; job `settings_sha256` = the family file's).

**One consequence I chose (I; open point P1): per-seed settings.** GXB O2 asks for one certification per reference
seed. `read_certification` accepts only a report of the settings' own `certification.seed` (R: `eval_adapter.py:1637-1639`)
and certifies that seed's pin (`:1593-1600`). So each reference seed S gets its own B10 file (certification seed S) and,
to keep fills independent, its own B11 file (accepted fingerprint of S) and its own index (fill-once per seed, R-5's
rule). Each B10 file pins the reference units 1101 and S only: 1101 because theta0 (the untuned unit) is the init unit of
seed 1101 and the 1B validator requires the untuned seed among the pinned seeds (`eval_adapter.py:312-315`).

## 2. Files created or changed (SHA-256, M: `shasum -a 256`)

New (under `scripts/scale78b/` unless named):

| File | SHA-256 |
|---|---|
| `experiments/safety_selection/configs/study-kt-llama31-8b-r64-g5e5-mb2-20261108.json` (item 3; config_sha256 `81dd70687b729a5977ad6dc117bdd428ea27eebdf0ea3b3e19c29f7c2d334828`, training identity `0ffd8f58…`) | `3298dd92be27c3658a851fb063f1bdc30897c2ab9b8cf410114c352e63134be6` |
| `refs_78b.py` (the wrapper) | `87c9f6ada38f8724ddb9df6f2f92d8295dcd8cd3fe234c21a01747f646212015` |
| `make_refs_settings_78b.py` (the maker) | `327ad517a20c5550a2eca19bbbf4ca60b1b1bc88f1c1be9939d77c843b99dce4` |
| `settings/refs_pins_78b.json` (the pins the lead edits) | `378a60790eb26756c6f1b91b8e0da9c935535d2319055e7c436ef1e33b2f1eb4` |
| `tests/refs/conftest.py` | `242aa5f78d983de5462da8314b08f76df7bf2e64bd12b70649e1cd67951131b5` |
| `tests/refs/refs_fixtures.py` | `59b05b2389f4f22d3c4e0e2550fcf47a60cea12b914c7024d00e6a59604e198c` |
| `tests/refs/test_refs_78b_eval_adapter.py` | `df2db758c79af76f59bc5e28e3cc8d77362bbb2e6cd1c5d3eb7449a614e5255d` |
| `tests/refs/test_refs_78b_safe_lora.py` | `70aac7786c3d74dc959518e6d06a7198d73eb3a57af13053d013edaf3fda301d` |
| `tests/refs/test_refs_78b_settings.py` | `342fd15de70b409bc91480b94983cd73f3d713db9f5f14cb55f498982700f393` |
| `tests/refs/test_llama_g5e5_config.py` | `18515915bfd5be9f9494bbae6da3af72d7b33b678cd976d732829f25ddadb529` |
| `tests/refs/mutation_spec_refs_78b.json` (52 mutants) | `0b700da8b2f463482d463f7f96ee134c54a0b1958ac19a9c65249145709604da` |
| `tests/refs/run_mutants_refs_78b.py` (Track O's runner, test path and spec changed) | `c8109fe1ed56b1e66b1fec58f5a4b1d7ee83d4283a6d8aa354ae2429364ddefe` |
| `tests/oext/test_oext_78b_r2.py` (item 4) | `33b75cdf5264fb83e73f90f0ed50f635111ea641f1bed8ce41f49f8badba92ba` |

Derived settings (the maker's output; M: `--check` equal): `settings/REFS-78B__F__S.json`, `eval_adapter__F__S.json`
and `safe_lora__F__S.json` for F in {olmo2-7b, llama31-8b} and S in 1102-1107 (36 files). Their full SHA-256 values,
with the pins file's, are in `R/r2-r-scratch/hashes.txt` (M: `shasum -a 256`). Two examples: `REFS-78B__olmo2-7b__1102.json`
`3a869e9661924864908000c80a2ecda2e7d112ae8a4eeb530369d2625e5737ef`; `REFS-78B__llama31-8b__1105.json`
`02a410a8b60a0d06e0a0910370af9b878632799c8a503edef005365fcb9d3d4d`.

Changed (Track O's files, item 4; pre-change copies in `R/r2-r-scratch/pre-o/`, which hash to r1-o.md §11.2):

| File | Before | After |
|---|---|---|
| `oext_78b.py` | `c6a9a946…` | `05589f946e59bd93904980ce0d824e70dc1901615ab08304d27ff068950675c0` |
| `make_oext_settings_78b.py` | `6cd317a0…` | `0e8bd8f984b4c7b9a5ed203061bdce0fa5f3f8d1aafb78982bb2bf170db4fd8b` |
| `tests/oext/test_oext_78b_check.py` | `860cf69f…` | `adb5b9285394d127e660333f7dc7a7e1d5f53984beb0744602d6d6810965ae67` |
| `tests/oext/test_oext_78b_files.py` | `a8d6e912…` | `2bd2bb6d8a20c4478860869a5b91ae95e7d9229ae5a1a26b1d10b3a916bdb903` |
| `tests/oext/mutation_spec_oext_78b.json` (92 → 103 mutants) | `0010a870…` | `a2679365943c2bc2c18c052831c4a32031710c7f90dfaf3ba5c968ccc2be6401` |

No Track O settings file changed (M: Track O's `--check`: 18 files equal). No pin anywhere in `scripts/` or `runkit/`
names `oext_78b.py`'s hash (M: `grep -rl c6a9a946… scripts runkit`, 0 hits; only R1's reports do), so the new wrapper
hash reaches only the forms the lead prints at fill time. I copied no git-ignored file into WS `tmp/`.

## 3. What each item does and where (R: WS paths)

**Item 2, the settings per family and seed** (`make_refs_settings_78b.py`; docstring :1-38).
- `eval_adapter__F__S` (`Family.eval_adapter`, :237-282): MAIN_F's path, file hash, config hash and training identity
  (OLMo `18cc31d7…`, Llama `74758af1…`, = RK `CONFIGS` main; training identity = RK `KIT`); F's manifest (`9ed61826…`,
  `c52a50af…`); reference units {1101, S}; untuned = RK KIT's theta0 unit; certification seed S and
  `expected_sampled_answers` = 200 harm prompts x MAIN_F's 3 harm samples = 600 (200: Track O's M of both manifests;
  3: M from the configs); scale allowed {1, 0.9, 0.75, 0.5, 0}, planned {0.9, 0.75, 0.5}, curve {1, 0.9, 0.75, 0.5, 0}
  (DES F2); the 3-seed fallback set (`reference_set: three_seed`) gives planned {0.75, 0.5}, curve {1, 0.75, 0.5, 0} and
  only 1102-1104's files; the 1B prefix (text SHA-256 `0fcc6beb…`, separator, apply_to, guard_sees, length_rule
  unchanged: a user-turn prefix on both families, P2 §3.2); the Safe LoRA file transform = unchanged
  `safe_lora.py` with `safe_lora__F__S`; O-ext = Track O's `oext_eval__F.json` (path, SHA-256) and its branch
  (`pending_w1_18` now: only certify runs until the branch is filled, the 1B rule, `eval_adapter.py:669-688`);
  regeneration, evaluation, checkpoint, certification gate and environment fields are 1B's.
- `safe_lora__F__S` (`Family.safe_lora`, :284-343): 7 modules from MAIN_F, 32 blocks (pins; M: 32 x the rank-64 per-block
  sums equal the configs' 159,907,840 and 167,772,160, test `test_the_lora_count_is_32_blocks_of_the_rank_64_sums`; the
  model shapes are I), 224 matrices, rank 64, alpha 128, the trainable count; accepted = seed S's e1 fingerprint;
  K default 78 = 224 x 39/112, conditional 24 = 224 x 12/112 (not run; open point P3), certify 0; aligned = KIT's
  instruct model and revision; unaligned = KIT's base repository; dtypes, file pins and the base revision null (the
  lead's Hub read). `engine_x`, `report`, `v_diagnostic`, `outputs`, `weights` are 1B's.
- **B10's certification settings (GXB O2)**: the `certification` section of each `eval_adapter__F__S` (the 1B form, seed
  S). Its report is the seed's `--certification-report`; a failed one exits 4 (the 1B code) and stops the seed's
  references.
- **Waits** (`EVENTS` :91-106): `REF_UNIT_<s>` (seed s's a0 unit: path, COMPLETE.json SHA-256, e1 and q fingerprints;
  1101's path and marker hash are prefilled from RK KIT, its fingerprints wait) and `HUB_READ` (the models). Each wait
  lists the settings fields it nulls with their kinds, so the wrapper's check can validate the rest (below).
- **Index** `REFS-78B__F__S.json` (`Family.derive`, :345-363): the two files, Track O's `oext_eval__F` and
  `limits_overrefusal_checks__F` (B10 binds them), the branch, the W1-18 record pin, the manifest, the other family's
  manifest, the waits. The kit form (`--refs-78b F S`, `form` :397-413): RK's `{files, inputs}` form (RK
  `oext_form_problem` accepts it, M), with the W1-18 record at its R-21 path once pinned.
- **Fill reach** (M: tests): a seed's unit fill changes only that seed's index; seed 1101's every index of the family
  (no B11 file); the Hub read every index of the family; a Track O O-ext fill every index of that family only.

**The wrapper** (`refs_78b.py`; docstring :1-46): `eval_adapter`, `safe_lora`, `check`, each with `--family F --seed S
--index IDX --index-sha256 H` (no index literal). Before the call: run files against `CODE` (:81-89), the index's name,
hash, kind, family and seed (`Index`, :143-198), full flag names against the 1B parsers' sets (`EA_FLAGS`, `SL_FLAGS`
:92-110; a test holds them equal to the 1B parsers' own option strings), waits, the label and hash bindings, the seed
(`--seed` = S; `--reference` = S's pinned COMPLETE.json; B10 `check --reference` only 1101 or S), `--prepared`
(Track O's `check_prepared`), `--w1-18-record` (Track O's `check_branch_flags`). The globals are restored after the
call, also when the 1B code raises. `check` ($0): each file through the unchanged 1B validator with its true label; a
waiting file is validated with only its waiting fields replaced by placeholders (`with_placeholders`, :353-362), so
"waits" means the rest is valid; any refusal exits 2.

**Item 3** (`study-kt-llama31-8b-r64-g5e5-mb2-20261108.json`, written by `R/r2-r-scratch/make_llama_g5e5.py`): the LR 1e-4
G config with `train.lr` 5e-5 and its own `name` and `purpose`; key order and the 4-space form kept. The engine's loader
derives no field from the LR (R: `config.py:476-560`, `:643-649`). M: generation `5ddced7a…` and guard `a7f0755b…`
equal the 1B O-ext pins (C3's expression). T-O2's step on a copy: Track O's maker with `recipe_g` =
{this name, `81dd7068…`} allows it in `oext_unit__llama31-8b`, drops Llama's RECIPE_G wait, changes only that file and
Llama's X index, and the wrapper's check reads the file `valid` (test `test_t_o2s_recipe_g_fill_on_a_copy`). The
committed fill stays the lead's step (open point P6).

**Item 4, Track O's follow-up** (from `R/r1-o-reverify2.md`):
- **W2-1** (`make_oext_settings_78b.py:426-441`): under Branch 128, or full with a record, `form()` adds
  `{record_path: record_sha256}` to `OEXT_78B[F]` and `OEXT_78B_Y[F]`; `consistency()` and the cascade test now hold
  that entry (`test_oext_78b_files.py`); new tests print both forms after a branch fill and check RK accepts them.
- **W2-2**: the re-verifier's targeted tests H3, C4, I1 (plus H3b on a filled theta0 pin) in `test_oext_78b_r2.py`, and
  its three surviving mutants (RV2-m-w1-side-job, RV2-w-w1-record-ignored, RV2-w-null-identity-waits) in the spec.
- **W2-3** (`oext_78b.py:140-146`, :509-583): `check` no longer matches refusal texts. A waiting file is validated in
  memory with each field its waits null (`WAIT_FIELDS`; UNIT_JOB's: every a0 unit's null job pin; ENGINE_Y's: the
  engine identity, under a placeholder identity) set to a placeholder; any refusal exits 2; a listed field that is
  filled (a stale index) or absent refuses. M: the re-verifier's F2 case (theta0 null and `bank.size` 99) now exits 2,
  F1 still exits 2, and a null that no wait names exits 2. `WAIT_REFUSALS` and `expected_wait` are gone; two Track O
  tests that used them were changed to the new rule (`test_a_waiting_role_masks_only_its_own_pins_refusal` now lists
  both null pins' waits; `test_null_pins_refuse_the_1b_validators` matches the 1B messages directly).

## 4. Tests added; suite counts (M)

- New: `tests/refs/` 68 cases (eval_adapter 24, safe_lora 14, settings 26, Llama config 4); `tests/oext/test_oext_78b_r2.py`
  13 cases. Track O's folder: 132 → 145 cases.
- Parity (M): wrapper vs the 1B main called as the 1B tests call it, same documents, same out path. B10 regenerate,
  evaluate in certify / scale 0.75 / prefix / external, the gated `run` (certify, scale, prefix) and `compare`, and O-ext
  under Branch 128 (status `oext_pinned`, Track O's fixture files): every engine evaluation file and O-ext output file
  byte-equal; job.json byte-equal; every other file equal once wall-clock fields are dropped, or once the hashes of
  files that differ only in wall-clock fields are mapped (completion markers). B11 transform default / certify, check,
  vcheck: every output byte-equal except the timing file (equal without its seconds).
- **scale78b suite under the network-deny sandbox**: before **529 passed, 57 skipped** (66.8 s); after **610 passed,
  57 skipped** (71.9 s; again 73.0 s on the final files); exit 0 each. Command: `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q
  scripts/scale78b/tests` in WS.

## 5. Mutants and shard results (M; under the sandbox; each shard with its own baseline, same command)

- **Refs spec, 52 mutants** (wrapper 31, maker 21; run on `refs_78b.py` `bf4bd52d…`, which differs from the final
  `87c9f6ad…` only in one docstring line cite, 1869 → 1868; every find text still occurs once, M): shard 1 (26) **26 killed** in 2 min 48 s; shard 2 (26) **26 killed**
  in 3 min 26 s; 0 survived, 0 invalid, 0 ERROR lines (`R/r2-r-scratch/mut-refs-{1,2}.json`; baseline 67 passed, 1
  skipped: the git-diff test skips in the mirror, which has no `.git`).
- **Track O spec, now 103**: the 14 changed or new ones first, in two shards: 7 killed, then 6 killed and 1 survived
  (R2-w-absent-field); I added the absent-key case to `test_W2_3_a_stale_wait_refuses` and it is killed
  (`R/r2-r-scratch/mut-o-r2-{1,2,3}.json`). Then the whole final spec (`a2679365…`) in 7 shards of at most 15, two or
  three at a time: **103 of 103 killed, 0 survived, 0 invalid, 0 ERROR lines**; each shard 2.2 to 4.1 min (21:26-21:37
  UTC); baseline 144 passed, 1 skipped (the nested in-place test, skipped by the runner's `OEXT78_NESTED`)
  (`R/r2-r-scratch/mut-o-full-{1..7}.json`).

## 6. Exact commands for the lead's full runs

```
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'; PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
cd <WS> && sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/refs/run_mutants_refs_78b.py <WS> <NEW_SCRATCH> <OUT>.json ALL --timeout 600   # about 6 min (E: 2 shards of 26 took 2.8 and 3.4 min)
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/oext/run_mutants_oext_78b.py <WS> <NEW_SCRATCH> <OUT>.json ALL --timeout 600   # about 20 min (E: about 10 s per mutant)
$PY -B <WS>/scripts/scale78b/make_refs_settings_78b.py --check
$PY -B <WS>/scripts/scale78b/make_oext_settings_78b.py --check
$PY -B <WS>/scripts/scale78b/make_refs_settings_78b.py --refs-78b F S        # the kit pin's form for (F, S)
for F in olmo2-7b llama31-8b; do for S in 1102 1103 1104 1105 1106 1107; do IDX=<WS>/scripts/scale78b/settings/REFS-78B__${F}__${S}.json
  $PY -B <WS>/scripts/scale78b/refs_78b.py check --family $F --seed $S --index $IDX --index-sha256 $(shasum -a 256 $IDX | cut -c1-64); done; done
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q experiments/safety_selection/tests/test_ss_family_codec.py   # fails until P5
```

## 7. Commands run (exit status)

- Reads: the brief, r1-common, GXB (13 sets), plan-ab §1 item 6, X2, X3, §2 Track R, Part 2 §3, §4.4, §16.1, DES F1-F2,
  r1-o.md (all), r1-o-reverify2.md, the 1B scripts' seams, fixtures and tests, RK `CONFIGS`/`KIT`/`oext_form_problem`:
  exit 0.
- Baseline suite (529 passed, 57 skipped): exit 0. `make_llama_g5e5.py`: exit 0. Engine recipe tests with the new config:
  exit 1 (1 failed, 94 passed: the count test, P5). Maker write and `--check`: exit 0. Wrapper `check` on both families'
  1102 index: exit 0 (eval_adapter and safe_lora `waits`, oext_eval `valid`). Test runs during the build: several
  failures that I fixed (fixture and comparison details, listed in the scratch logs); final runs below exit 0.
- Track O folder: 145 passed, exit 0. Refs folder: 68 passed, exit 0. Full scale78b: 610 passed, 57 skipped, exit 0.
- Mutation shards above (refs 2 shards; Track O 3 + 7 shards): exit 0 each, except the shard with the one survivor
  (exit 1, fixed and re-run). Three commands ran past the tool's 180 s and moved to the background; I waited for each
  in the foreground or read its result after it ended. Every mirror was deleted after its run.
- `date -u` before each time written.

## 8. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Decisive check reported first; route per script with the reason | passed | §1 |
| Parity on the 1B fixtures | passed (outside wall-clock fields and the hashes of files that carry them) | §4; parity tests |
| Every 1B file unchanged (`git diff --stat` empty for `scripts/stage1`, `scripts/stage1_s1`) | passed | M, §2; `test_the_1b_files_are_unchanged` |
| No record names a file it did not load | passed | `test_every_record_names_the_files_that_ran`, `test_the_record_names_the_module_that_ran_and_the_family_file`, label-lie tests |
| eval_adapter__F: manifest, MAIN_F, prefix, scale points, regeneration | passed | consistency test |
| safe_lora__F: 32 blocks, K = 78 of 224, base pins null | passed | consistency and LoRA-count tests |
| B10 certification settings, one per reference seed | passed (per-seed files; P1) | §1, §3 |
| Llama G 5e-5 config: field diff test; C3 hashes; T-O2 fill on a copy | passed | `test_llama_g5e5_config.py` |
| W2-1, W2-2, W2-3 | passed | §3 item 4; `test_oext_78b_r2.py` |
| scale78b suite under the sandbox, counts before and after | passed (529 → 610 passed, 57 skipped) | §4 |
| Every mutant killed in shards under 10 min, none invalid | passed: refs 52/52, Track O 103/103 | §5 |
| Item 5 (`similarity` settings) | not built | — |
| A real 7-8B run of any command; the engine's own suite | not tested (no pod; the engine count test fails, P5) | — |

## 9. Open points for the lead (I decided none of them)

- **P1. Per-seed B10 files.** I made one B10 file per reference seed (certification seed S) because the 1B code accepts
  only the settings' own certification seed. Each file pins seeds 1101 and S. Accept, or rule another form.
- **P2. Which a0 unit each seed pins.** GXB O2 says "that seed's block-B a0 unit". Block B's seeds are 1105-1107 under
  plan A (RK `BLOCK_B_SEEDS`), so 1102-1104's units would be block A's (or, for OLMo 1102-1103, the reused side units).
  The pins name no unit for 1102-1107 yet (`REF_UNIT_<s>`). Seed 1101's fingerprints also wait, and **every** B10 file
  needs them (the untuned seed), so a lead step on the 1101 side unit's COMPLETE.json (hashes only) comes before any
  reference.
- **P3. The conditional Safe LoRA point.** The 1B schema needs three points; I set conditional K = 24 (1B's 12 of 112 by
  the same share), marked "not run". Confirm or give another value.
- **P4. Llama's theta0 unit under MAIN_F.** It was made under the LR 1e-4 recipe (T-O4). B10's `read_untuned` compares
  its training identity with MAIN_F's (R: `eval_adapter.py:451-469`, `:407-413`), so on Llama `check --untuned` and
  `compare --against untuned` (the lambda = 0 point's optional reference) refuse (I; not run).
- **P5. The engine's recipe count test fails with the new config** (M: `test_ss_family_codec.py::test_the_recipe_accepts_
  the_header_field_and_every_existing_recipe_still_validates`, 70 vs 59 + 9 + 1). It is the engine's test file (not
  mine); the lead's committed addition (KD8) needs that count to take +1 in the same commit.
- **P6. Fills.** (a) `RECIPE_G[llama31-8b]` and Track O's `families.llama31-8b.recipe_g` take `81dd7068…` (file
  `3298dd92…`) by recorded steps, before `OEXT_78B[llama31-8b]` (GXB O11); `RECIPE_ALLOW` still holds the 1e-4 G
  (`442f133f…`), the lead's swap (P2 §3.2). (b) A Track O O-ext fill changes `oext_eval__F`, which every B10 file of F
  pins: run this maker after Track O's (stated in my maker's docstring, not in Track O's).
- **P7. K3's side.** A kit pin per (F, S) (I called it `REFS_78B[F][S]`; `--refs-78b F S` prints its form); the
  commands `refs_78b.py eval_adapter|safe_lora --family F --seed S --index … --index-sha256 …`; `b10_certify` =
  `eval_adapter run --seed S --evaluations certify --gate-reference-eval <S's a0 unit eval/e1>` (or `evaluate --mode
  certify` then `compare`), its `S-certify.compare.json` the seed's report; the 1B safety-prompt text file packed by
  path and its SHA-256 `0fcc6beb…`; the B11 snapshots at the Hub-read commits.
- **P8. Llama's base repository is gated** (DES F2): if its access check fails, Llama's Safe LoRA is not run; the files
  still exist and wait on HUB_READ.
- **P9. The 3-seed fallback** is one pins edit (`reference_set: three_seed`) and a maker run; it is tested, not chosen.

## 10. Concerns

- **1B prose kept.** The derived B10 and B11 files keep the 1B files' prose fields that I did not rewrite (for example
  `prefix.source`, `prefix.length_rule`, `certification.gate`, `regeneration.rule`, `combination_rule`, `label_note`,
  B11's `pin_rule`, `report`, `weights`). I did not read them (keys only), so some may name 1B facts. No code reads them.
- **The B10 `unit` texts** use RK KIT's paths (they start with `tmp/`); the 1B file's are relative to the data root. No
  code reads them.
- **The wrapper imports Track O's `oext_78b.py`** for its helpers, so a Track O change can reach the refs commands; the
  refs suite runs them.
- **Not tested:** a real 7-8B model, CUDA, the real snapshots, a real certification; the B10 external-file mode end to
  end through both wrappers (each half is tested, and the record-to-pin binding is).
- `make_refs_settings_78b.py` defines a `PLACEHOLDERS` table it does not use (the wrapper has its own); harmless.

## 11. Fix round (written 2026-11-08 22:54-23:11 UTC, `date -u` 22:54:34 and 23:10:14; started 22:43:49)

Inputs: the verifier's `R/r2-r-verify.md` (RV-1 to RV-6, P1-P5, its P4 follow-up) and its scratch, and the lead's
fourteenth set R-34 to R-39. The same rules applied. Pre-fix copies: `R/r2-r-scratch/prefix/`; the unified diff of the
code, pins, engine test and tests against them is `R/r2-r-scratch/fix.diff` (1,150 lines; the 36 derived settings are
the maker's output, re-derived, their hashes in `R/r2-r-scratch/hashes-fix.txt`). §11 supersedes §1-§10 where they differ.

### 11.1 What changed, per item

- **R-38, the copy route for `safe_lora.py`: not taken; I disagree, with evidence (the lead's call).** R-38's premise is
  that `safe_lora.py` writes its 1B K into the V/V' records. It does not: the record's `rule.measure` is the settings'
  `v_diagnostic.measure` (R: `scripts/stage1_s1/safe_lora.py:817-820`), each point's `status` is the settings' (`:673`),
  and the outcomes are the settings' (`:746-749`). The three "K = 39" in the file are docstrings (`:18`, `:30`, `:728`)
  that reach no output. M: new test `test_the_records_parameter_texts_come_from_the_settings` runs check, vcheck and
  transform through the wrapper with every settings prose field set to a marker: the records carry the markers and no
  "K = 39", "39 of 112" or "Gate A". So the false text was settings prose, and the maker now rewrites it (RV-3, below):
  `v_diagnostic.measure` names K = 78 of 224, the certify status names no 1B stage. A copy would add a new transform
  identity that B10's pin and every B11 record name, with no record text changed. If you still want the copy, it is
  about 1 builder h (E: Track O's lean copy form); say so and I build it.
- **R-38, B10's terms record (built).** `eval_adapter.py` stays unchanged. After each B10 command, beside each output it
  wrote (`--out`; run's `--regen-out` and `--eval-root`), the wrapper writes `OUTPUT.refs78b-terms.json`: the writer and
  B10 by SHA-256, the command, exit, output name, family, seed, index and settings SHA-256, and what each 1B term means
  at 7-8B ("Gate A unit" = the seed's a0 unit per R-35; "the untuned unit"; "lambda = 0" per R-34; the certification
  seed; "stage 1"), with the limit stated (`refs_78b.py` `TERMS`, `TERMS_LIMIT`, `terms_paths`, `write_terms`). It is
  never inside B10's folder, never written when B10 wrote nothing, and an existing one refuses before the call.
- **RV-3 (prose).** The maker rewrites, for 7-8B: B10 `certification.gate` and `reference_rule` (the report copies
  `gate`), `exit_codes.3`, `outputs.regenerate`, `regeneration.rule`, `oext.rule`, the θ0 role (R-34); B11
  `v_diagnostic.measure`, the certify and conditional statuses. M: no derived file contains "K = 39" or "Gate A"
  (consistency test).
- **RV-1 / R-37.** Conditional K = 0 in the settings, with a status saying it is not run; `refs_78b.py` refuses every
  `--point` but `default` and `certify` by name (`check_not_run`), `conditional` and `k12` tested.
- **R-34.** The wrapper refuses `check --untuned` and `compare --against untuned` by name (both flag forms tested).
- **R-35.** Each pins unit names its source (`side_unit`, `block0_a0`, `block_a_a0`, `block_b_a0`); the maker refuses a
  source off R-35's table (`SOURCES`); the waits' events name the unit and the step that fills it. The side units' paths
  and COMPLETE.json pins are prefilled from RK KIT (OLMo 1102 `43e8412d…`, 1103 `4b5bd06d…`; Llama 1102 `b0c99f7b…`);
  Llama 1103 is N's a0-1103 (block 0) and waits. Their fingerprints wait on the lead's hash-only read.
- **R-36.** Seed 1101's fingerprints are 64-hex; the maker refuses a value whose first 16 hex differ from P1 §2.1's
  (OLMo q `3c7344c178b47e5b`, e1 `9d5d5d8b2eb40262`; Llama q `ac05caca1bdfac5b`, e1 `ee44580dfa016b67`; R:
  `research/experiments/2026-11-05-78b-preregistration-part1.md` §2.1). The 1101 wait names that rule.
- **RV-2.** `labels_sha256` = `s1.labels_sha256()` (`260389f3fbfd…`) in every B10 and B11 file; the test holds it.
- **RV-4.** `_set` refuses an absent parent or field (exit 2, one JSON line); tested on both forms.
- **RV-5.** The maker removes this maker's per-seed files of seeds outside the set when it writes, and `--check` reports
  any such file. M: the in-place fallback test (six-seed folder, one pins edit, one run) leaves no 1105-1107 file
  (18 removed), passes the consistency checks, and keeps Track O's files.
- **RV-6.** The verifier's T1-T7 are in `test_refs_78b_eval_adapter.py`; its 7 non-equivalent mutants are in the spec.
  `RV-x-except-any` is equivalent (I, R): outside `check` the wrapper's own refusals are `Refused` (caught before), and
  the 1B mains catch their own refusals (`eval_adapter.py:1950-1955` catches its `_invalid()` types, Refusal, ConfigError and DataError among
  them, before the model, and `:1981-1990` every exception after; `safe_lora.py:901-903` catches `Refusal`, and it
  raises no ConfigError or DataError, I), so no `Refusal`, `ConfigError` or `DataError` reaches that branch.
- **R-39.** `experiments/safety_selection/tests/test_ss_family_codec.py:165`: `59 + 9` → `59 + 10`, with the comment
  naming the new config.

### 11.2 Files after the fix round (SHA-256, M)

| File | SHA-256 |
|---|---|
| `scripts/scale78b/refs_78b.py` | `e29e064ecacb2ab8d7bfa1bfc825638edf81a1587d4a0132fe0e64883d4b78d0` |
| `scripts/scale78b/make_refs_settings_78b.py` | `db57eba2416015e6d769ad6f45be65e5eaca44dca4f9378c1a6a8634a9b6209b` |
| `scripts/scale78b/settings/refs_pins_78b.json` | `9f56cfe3b1ba95b78c8ec3dc3b38fbfd405da707d2b86a4d3f1f7920a2e53d62` |
| `scripts/scale78b/tests/refs/test_refs_78b_eval_adapter.py` | `934bb9315e255200b92dc8f47ac2572d387836f0e1fcb5a9f49ae81b10542d66` |
| `scripts/scale78b/tests/refs/test_refs_78b_safe_lora.py` | `21339efba76478691187f79fff96af0a09f2ed5aa9aadee2bf501837c1e87a50` |
| `scripts/scale78b/tests/refs/test_refs_78b_settings.py` | `f6bd116ed9d9aff2fe86d619f5efcaf58ca760d2a34ac4385f6dd3f56c60e7e9` |
| `scripts/scale78b/tests/refs/mutation_spec_refs_78b.json` (52 → 80 mutants) | `43ba3ff2909cf7d5fe864f8fd0587c3b30fd044dfa72fe34000b140639988b96` |
| `experiments/safety_selection/tests/test_ss_family_codec.py` (R-39) | `9be630540e12a3c95f6734132a8d4f152276926dea6685b3bb9d3366fe15471f` |
| the 36 derived settings | `R/r2-r-scratch/hashes-fix.txt` |

Unchanged: `conftest.py`, `refs_fixtures.py`, `run_mutants_refs_78b.py`, `test_llama_g5e5_config.py`, the Llama config,
every Track O file. `git diff --stat -- scripts/stage1 scripts/stage1_s1 runkit` is still empty (M).

### 11.3 Counts (M; under the network-deny sandbox)

- **scale78b suite:** **633 passed, 57 skipped** (139 s), exit 0. It was 610 and 57 before the fix round. The refs folder
  went from 68 to 91 cases: eval_adapter 37, safe_lora 18, settings 32, Llama config 4.
- **Engine test file (R-39):** `experiments/safety_selection/tests/test_ss_family_codec.py`, **16 passed**. With
  `test_ss_family_recipes.py` it is 95 passed.
- **Refs spec** (`43ba3ff2…`, 80 mutants):
  - First the 29 changed or new mutants (R-m-unit-waits, 7 RV-x and 21 F-*), in 2 shards: 15 + 14 killed
    (`mut-refs-fix-{1,2}.json`).
  - Then the whole spec in 6 shards of at most 14, run three at a time: **80 of 80 killed, 0 survived, 0 invalid,
    0 ERROR lines**. Each shard took 4.3 to 5.6 min (22:56-23:07 UTC), with a baseline of 90 passed and 1 skipped
    (`mut-refs-full-{1..6}.json`).
- **Track O spec:** not re-run. No Track O file changed in this round, and §5's 103 of 103 still stand. Track O's tests
  ran again inside the 633.
- **Makers:** both `--check` runs are equal (36 and 18 files).
- **Clean tree:** `git diff --stat` for the 1B folders is empty. There is no `__pycache__`, and every mirror is deleted.

### 11.4 Commands for the lead (changed from §6)

```
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/refs/run_mutants_refs_78b.py <WS> <NEW_SCRATCH> <OUT>.json ALL --timeout 600   # about 25 min (E: about 20 s per mutant in one process)
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q experiments/safety_selection/tests/test_ss_family_codec.py   # passes now (R-39)
```

### 11.5 Open points after the fix round

- **R-38's copy route.** I did not build it; §11.1 gives the evidence. The decision is yours.
- **The terms record is the wrapper's, not B10's.** B10's records do not list it, and nothing pins it. K3 should carry it
  back with the outputs.
- **The prefill (R-35).** The side units' paths and marker hashes are RK KIT's, M by K1, and I opened no unit. Their
  fingerprints wait on your hash-only read. Before each certification, run the verifier's suggested Mac check:
  `refs_78b.py eval_adapter … check --reference S=<COMPLETE.json>`.
- **The fallback nit (the verifier's Check 2).** Under the 3-seed fallback, `allowed` still includes 0.9, so a 0.9 point
  would pass B10 there. I did not change it, because it is not ruled.

## 12. Follow-up (written 2026-11-08 23:51 UTC, `date -u`; started 23:33:45)

The inputs were the re-verifier's `R/r2-r-reverify.md` (verdict VERIFIED_WITH_MINOR; findings RRV-1 to RRV-3) and the
lead's fifteenth and sixteenth sets. R-38 is amended: there is no copy. R-40 is withdrawn. R-41 and R-42 are new. The
rules were unchanged. Pre-change copies are in `R/r2-r-scratch/prefix-fu/`. The diff is `R/r2-r-scratch/followup.diff`
(305 lines).

**RRV-1 (R-40 withdrawn).** The 3-seed fallback's `allowed` scale points are now {1, 0.75, 0.5, 0}, the same as its
curve (P2 §3.1-§3.2). B10 therefore refuses λ 0.9 there.
- Code: `REFERENCE_SETS[...]["allowed"]`. The shared `SCALE_ALLOWED` constant is gone.
- Test: `test_the_fallback_allows_no_scale_point_it_does_not_plan`. Under the fallback, B10's `make_plan` refuses 0.9
  and plans 0.75 and 0.5. The consistency test holds `allowed` for each set.
- The six-seed files did not change (M: `--check`, 36 files equal).

**RRV-2 / R-41.** Before the call, the wrapper notes the state of each output: absent, an empty folder, or holding
something. After the call, it writes a terms record only for an output that the command created: one that was absent
or empty before and holds something after (`_state`, `created`). A refused command writes no record.
- The re-verifier's probe is now a test, `test_no_terms_record_beside_an_output_that_existed_before_the_call`. `--out`
  already holds an older file, B10 exits 2, and no record is written. An empty folder that B10 fills does get a record.

**RRV-3 / R-42.** The wrapper refuses λ = 0 by name: `evaluate --lambda 0` in any spelling (`0`, `0.0`, `--lambda=0`,
`-0.0`), and `run --evaluations` containing `scale:0`. Nothing is written in either case.
- The terms record's "lambda = 0" entry now says the wrapper refuses it (R-42).
- Tests: 4 for evaluate, 3 for run, and 1 showing that a nonzero scale still runs.

**Files after the follow-up (SHA-256, M):**

| File | SHA-256 |
|---|---|
| `scripts/scale78b/refs_78b.py` | `fbdd66e83ec22dc6c668e02016a60585b4e245a38439c8cf6346b8d043adefe8` |
| `scripts/scale78b/make_refs_settings_78b.py` | `199dadba0723d8daac3b98fe8a34dceb613b170b7b4e32c3176bb5fb3b87271f` |
| `scripts/scale78b/tests/refs/test_refs_78b_eval_adapter.py` | `c774b8586b27df0aca2c50ba2a03be22da84341ffedf7f6f160d63e2518e17ed` |
| `scripts/scale78b/tests/refs/test_refs_78b_settings.py` | `c0acbfd6468989369d6d9fa75172c3c3244a7f95a7a03f14980532436e857a2b` |
| `scripts/scale78b/tests/refs/mutation_spec_refs_78b.json` (80 → 88 mutants) | `8346b2dd32f01a18cac0576455b7002500ffbf194e553740b66838100201e28b` |

Nothing else changed. The 36 derived settings still equal `R/r2-r-scratch/hashes-fix.txt`.

**Counts (M, under the network-deny sandbox):**
- The scale78b suite: **643 passed, 57 skipped** (164 s), exit 0. It was 633 and 57 before. The refs folder went from
  91 to 101 cases.
- The refs spec (`8346b2dd…`, 88 mutants):
  - 8 are new: G-m-fallback-allowed, G-m-allowed-fixed, G-w-terms-exists-only, G-w-created-held, G-w-state-empty,
    G-w-lambda0, G-w-lambda0-evaluate and G-w-lambda0-run.
  - 2 find texts were updated (R-m-curve, F-w-terms-only-written).
  - The whole spec ran in 6 shards of at most 15, three at a time: **88 of 88 killed, 0 survived, 0 invalid, 0 ERROR
    lines**. Each shard took 4.9 to 6.3 min (23:36-23:48 UTC). The baseline was 100 passed and 1 skipped
    (`mut-refs-fu-{1..6}.json`).
- Track O's files did not change.
- `git diff --stat` for the 1B folders is empty. There is no `__pycache__`, and every mirror is deleted.
