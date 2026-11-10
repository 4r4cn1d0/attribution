# R3 Track P report: the padded-tokens tool and three small fixes (scripts/scale78b/)

Written 2026-11-09 13:49 UTC, last updated 13:58 UTC (clock read with `date -u` before each). WS = B/ws-p, detached at d7eb772. Nothing
committed; no git state changed. No pod, network, install, download, agent or message. No real data opened: every test
uses synthetic fixtures; the real recipes are read for hashes and training settings only.

## 1. Status

**Done**, with one run left to the lead: the full O-ext mutation spec (110 mutants, about 16 min; I ran its 7 new
mutants, all killed). The SR-2, count-tool and Track P specs ran in full (all killed).

| Item | State |
|---|---|
| 1 Padded-tokens tool (R-46, P-1, P-2) | done: tool, 39 tests, spec of 47 mutants (all killed), runner |
| 2 W2-4 (W1-18 settings under engine X's identity) | done: 5 tests, 3 mutants (all killed) |
| 3 W2-5 (W1_18_78B lists the two frozen readers) | done: 14 new tests + 1 test extended, 4 mutants (all killed); RK accepts the longer list (M) |
| 4 KR5 (Track S's stop fixture in the shared form) | done: fixture aligned, 1 new test |

## 2. Files (M: `shasum -a 256` in WS)

New (in `scripts/scale78b/`):

| File | SHA-256 |
|---|---|
| `padded_tokens_78b.py` (345 lines) | `11a0b9c904d433a5f98cdb74739d6aeb31afe1bdafeeb4cf565507443278eede` |
| `tests/test_padded_tokens_78b.py` (537 lines) | `b1dc4966d532514c96489c90799435bf98da290e39d6c5aa9e50386680f77ba3` |
| `tests/mutation_spec_p_78b.json` (47 mutants) | `612462e231cb034203df3ca68aba9c589a44db981b934f9fe50fd9b14d57ec86` |
| `tests/run_mutants_p_78b.py` (new runner, `run_mutants_c_78b.py`'s form) | `af0c1c9a3b0961328c509a17b8e266c278b1cb4dfe55369c84a6211d0a2dc12d` |

Changed (owned for items 2-4):

| File | SHA-256 after |
|---|---|
| `oext_78b.py` | `e869b629581811fd3adae275d23113b0105d2bcf41212047091e71b82c650852` |
| `make_oext_settings_78b.py` | `f7c1c4829243e9492d84ee90bb0336f261c5003ce2ee718e6d5d1e3488acd069` |
| `tests/oext/test_oext_78b_check.py` | `14583dd9408fef6e8cd627086dd68b9078ef09b9f9908c3c9d1ba7dbce147d91` |
| `tests/oext/test_oext_78b_files.py` | `63b69a1d481f08adb63c98e676bf97eee4d2e48969fed63dbfde017fda3b2605` |
| `tests/oext/mutation_spec_oext_78b.json` (103 -> 110) | `f048093213f573155697877914bc9600036ed2eb750ba0d65f381c0add5131fc` |
| `tests/test_blinded_sigma.py` (Track S's test file with its stop fixture) | `9668c35eae084c4082a058067e21f2be397da8c43e791990e787d507b4deeb3a` |

Nothing under `runkit/`, `scripts/stage1*` or `experiments/` changed. No file I changed is pinned by a literal hash
anywhere in `scripts/`, `runkit/` or `research/` (M: grep for each file's HEAD SHA-256, 0 hits).

Copied git-ignored input (for the suite's 55 skips that need the prepared sets): `MAIN/tmp/kt-prepared` ->
`WS/tmp/kt-prepared` with `cp -pR` (37 MB, 48 files). Verified: the SHA-256 of the sorted per-file `shasum -a 256`
list is `d919a278b1412cd67d5e055d73d775791a32a93d3305a4101a495f5746f06eab` on both sides (M). It is git-ignored in WS
(not in `git status`). The lead may delete it after the merge.

## 3. What each item does, and where (R: WS paths)

### Item 1: `padded_tokens_78b.py` (GXB R-46, O1; lead rulings P-1, P-2)

- **Runner choice.** A new runner `tests/run_mutants_p_78b.py`. `run_mutants_c_78b.py` names its two test files and its
  spec inside the code (R: `run_mutants_c_78b.py:31-32`), so no existing runner takes a new spec unchanged. The new one
  is that runner with only TESTS, SPEC, the import probe and the report kind changed.
- **Reuse.** The tool imports `encode_count_78b` for the pins (`RECIPES`, `MANIFESTS`), `load_recipe`, `real_context`,
  `check_tokenizer`, `read_pinned`, `parse_spec`, `TextGuard`, `out_ok`, `write_once` and `canonical` (Track C's
  precedent tool; nothing copied).
- **The engine's own code** (R: padded_tokens_78b.py docstring and the functions below):
  - `encoded_corpus` (:124): every row through `runner._verified_example` (R: experiments/safety_selection/runner.py:164,
    :200-205; encode at `max_train_tokens`, checked against P_F's audit).
  - `read_edit` (:136): read once by path; `ec.read_pinned` refuses bytes off the named SHA-256; then
    `edits.parse_edit` (load_edit's checks, R: edits.py:169-176). Then `edits.edited_corpus` (runner.py:420).
  - `plan_for` (:159): `stream.make_plan` as runner.py:424 (a0) and :426-427 (edit: its removed rows, added ids, hash).
  - `padded_total` (:178): `plan.iterate(1, S)` (runner.py:525); per step the engine's count, runner.py:544-545 (per
    micro-batch from `stream.micro_batches`, its rows times its longest row's input tokens). There is no engine
    function for that count; it is the same expression, cited.
- **Steps rule (O1).** `train_settings` (:109) refuses unless MAIN_F's micro_batch x grad_accum is 128 and its `e1`
  checkpoint is one epoch. `steps_of` (:169): S = ceil(rows / 128), and the stream's `steps_per_epoch` and its e1 step
  must equal S, else refuse. Both families: micro_batch 2, grad_accum 64 (M: `test_main_fs_training_settings_are_checked`).
- **Seed rule (P-1).** **The value depends on the seed** (I, with evidence M): the seed's shuffle orders the rows, and
  micro_batch is 2, so which rows share a micro-batch (and so the padding) changes with the seed. On the varied-length
  fixture the seven totals differ (M: `test_the_value_depends_on_the_seed_and_the_largest_is_taken`); on equal-length
  rows they are equal (M: `test_equal_rows_give_a_seed_independent_known_answer`). So `seed_totals` (:191) runs seeds
  1101-1107 (`SEEDS`, :72) and `run_record` (:233) takes the largest total / S. `source` names the seeds and the rule,
  and per edit every seed's total, `largest_at_seed` and `seed_dependent`. The real families' seed dependence is shown
  by the real record's `seed_dependent` field (not measured here: no real data).
- **The record** (`run_record`, :233): exactly K2's keys (`KIND`, `KEYS`, :68-69, equal to `plan_tool.py:3731-3732`,
  test-held): kind, version 1, family, `edits` {edit SHA-256: padded tokens per step (float)}, `source`, `utc`,
  `recorded_by` (`--recorded-by`, default "the lead's token-count step (padded_tokens_78b.py)"). `source` is an object:
  the tool's SHA-256, MAIN_F's path, config_sha256 and training settings, P_F's manifest, the tokenizer (repo, 12-hex
  revision prefix), the four engine files' SHA-256, the seeds, the rule, and per edit rows, steps, removed, added,
  rewritten and the per-seed totals (R-46's MAIN_F hash, rows and steps).
- **Check mode (P-2)** (`run_check`, :266): `--check-a0` counts the unedited training set at seeds 1101-1107 and compares
  the value at the basis seed 1103 with `A0_BASIS` (:82): OLMo-2-7B (1103, 1,457,026, 38, 38,342.79), Llama-3.1-8B
  (1103, 1,569,846, 38, 41,311.74), from RK `rules_78b.py:295, :308`. It matches only if the total, the steps and the
  rounded value are all equal. It writes a record of its own kind `stage1-78b padded tokens a0 check` (K2's reader
  refuses it, M) with every seed's total and per-step value; exit 0 equal, 1 different. It takes no `--edit`.
- **Refusals (exit 2, nothing written):** an edit off its pin; an edit named twice; no edit; every engine edit check
  (another manifest, held-out rows, unknown rows, not JSON, another position rule); P_F or the tokenizer context off the
  manifest pin; another tokenizer; another family's recipe; a row that does not encode as P_F's audit; an existing
  `--out`, or `--out` inside an edit's folder or inside P_F; a step size other than 128; no e1 at one epoch; a stream
  whose steps are not ceil(rows / 128).
- **No text.** P_F's prompts and responses and the edit's added and rewritten texts go into the `TextGuard`. The record
  bytes and every printed line are scanned before the write; an engine refusal's message is printed only if it holds
  no text; any other exception prints its class name only. Writes are atomic and once-only (`ec.write_once`).

### Item 2: W2-4 (`oext_78b.py`)

- `ENGINE_X_IDENTITY` (oext_78b.py:117) = RK's `ENGINE_X` (R: rules_78b.py:111). In `check_settings_files`
  (oext_78b.py:575-576), the `limits_overrefusal_checks` role is now validated under `ENGINE_X_IDENTITY`, not under the
  running engine's identity. The docstring says so (:68-70). I chose a literal, not the X index's identity: the Y and
  W1 indexes do not hold X's identity, and a literal does not depend on any other file being on the pod.
- Tests (test_oext_78b_check.py, the W2-4 section at the end): the literal equals RK's ENGINE_X, the 1B
  `oext_unit.json` engine_x and both committed W1-18 settings' engine_x; on a simulated engine-Y host, the W1 index and
  the Y index pass (`limits_overrefusal_checks` "valid"); W1-18 settings naming engine Y refuse on both hosts.
- M: with the old line put back (`engine = running`), 3 of these tests fail (the two Y-host passes and the Y-host
  refusal case); restored and re-checked (`grep -c 'engine = ENGINE_X_IDENTITY'` = 1).

### Item 3: W2-5 (`make_oext_settings_78b.py`)

- `frozen_reader_pins` (make_oext_settings_78b.py:447): reads the W1-18 settings' `frozen_reader` block (exactly
  `family_probe_reading` and `killtest_stage0_reading`, R: scripts/stage1/limits/limits_common.py:71-97). Each path
  must be a plain `.py` path under `scripts/`, and the file in this checkout must hash to its pin, else refuse.
  `w1_18_78b_form` (:467) adds both to `files` (:481). R-20's form `{files, side_units}` is kept.
- M (the printout `--w1-18-78b` in WS): `files` now holds `scripts/family_probe_reading.py` `8848340107bd…` and
  `scripts/killtest_stage0_reading.py` `1740663bc9e4…`, beside the 8 earlier entries.
- **RK's check accepts the longer list (M, in WS):** `rules_78b.files_form_problem` gives None. `w1_18_route_problem`
  on the printout gives the same refusal with and without the two readers: "side_units['llama31-8b']['untuned']
  .job_sha256 is not KIT a0_units'". That is θ0's job pin, which waits (R-20). With the side units set to KIT's values
  and synthetic job pins, it gives None both with and without the readers. So no kit change is needed.
- Tests (test_oext_78b_files.py): the printed form test now also checks both readers at their pins and hashes. The
  new W2-5 section: both readers listed once, at their pins; per family and reader, a pin off the file, a path out of
  `scripts/` and a missing key refuse (12 cases); a changed reader file refuses.

### Item 4: KR5 (`tests/test_blinded_sigma.py`)

- `stop_record_doc` and `write_stop_record` (the fixture block before `write_stop_record`) now write the shared form,
  as `rules_78b.anchor_stop_record` writes it and `anchor_stop_problem` takes it: `counts` {kept 61, needed 64} for
  `safe_anchors_below_64`, and {prompt_index 5, position 6, of 64} for `harmful_prompt_does_not_encode`. The old form
  was `{"safe_anchors": 61}`.
- New test `test_track_s_stop_fixture_is_the_shared_form`: with the shared fixture's JOB-DONE SHA-256, this file's
  record equals `runkit/stage1-78b/tests/fixtures/anchor_stop__olmo2-7b__safe_anchors_below_64.json` field for field.
  Track S's reader (`blinded_sigma.check_anchor_stop`) also reads that shared fixture. K3 writes the kit-side test.

## 4. Tests and suite counts (M; `sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q ...` in WS)

- scale78b suite, before (d7eb772): 643 passed, 57 skipped without `tmp/kt-prepared`; **698 passed, 2 skipped** with it
  (the 2 skips need scipy). After: **757 passed, 2 skipped** (76.5 s), exit 0. +59 = 39 (padded tokens) + 5 (W2-4) +
  14 (W2-5) + 1 (KR5). The tool's last change (two line citations in comments, after this run) was re-tested by the
  P runner's baseline on the final bytes (39 passed).
- 7-8B kit suite (`runkit/stage1-78b/tests`) in WS after the changes: **619 passed** (36.1 s).
- New test names: `test_padded_tokens_78b.py` has 26 functions, 39 cases (record form and values, seed rule, equal-row
  known answer, steps boundaries 256/257/128/129, rewrite and combined edits, the kit's reader, constants against RK, the
  a0 check pass, difference x3 and basis-seed cases, every refusal, and the no-text cases in both modes).

## 5. Mutants (M; all under the sandbox, foreground)

- **Track P spec** (`mutation_spec_p_78b.json`, 47 mutants on `padded_tokens_78b.py`): every refusal, the steps rule
  (floor, the check, the e1 step, the last step), the padding count (no padding, micro-batch 1, whole step), the seed
  rule (min, first seed, six seeds, a fixed seed, seed_dependent, largest_at_seed), removed, added, rewrites, the
  audit, per step, the form (kind, version, extra key), the a0 check (seed, match, total, value, exit, edit, kind,
  both basis literals), the guards and `--out`. **ALL: baseline 39 passed, imports the copy true, 47 killed, 0
  survived, 0 invalid** (65 s; `R/r3-p-scratch/mut-p-all.json`; again on the final bytes, `mut-p-all-final.json`:
  47 killed).
- **O-ext spec**: 7 new mutants R3-* (W2-4: running identity, the file's own identity, the literal; W2-5: readers
  dropped, hash check, path check, key check). Shard of these 7: **baseline exit 0, 7 killed** (69 s;
  `R/r3-p-scratch/mut-oext-r3.json`). Every one of the 110 finds occurs exactly once after my edits (M). The full spec
  is the lead's run (about 110 x 8.5 s, about 16 min).
- **SR-2 spec** (87): the 8 anchor-stop mutants (S-bs-stop*, S-bs-stopped*, S-bs-record-on-full-allowed): **8 killed**
  (40 s; `mut-sr2-stop.json`). **ALL: baseline 67 passed, 87 killed, 0 survived, 0 invalid** (13:45:36-13:57:46 UTC,
  about 12 min; `R/r3-p-scratch/mut-sr2-all.json`).
- **Count-tool spec** (`run_mutants_c_78b.py`, 71): **ALL: baseline exit 0, 71 killed** (30 s; `mut-c-all.json`).

## 6. Exact commands for the lead

```sh
cd /Users/spiderishi/Coding/attribution            # after the merge
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'

# Suites
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests

# Mutation runs (each SCRATCH a new folder outside the repo; each OUT a new file)
sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/run_mutants_p_78b.py "$PWD" <SCRATCH_P> <OUT_P.json> ALL        # ~1 min
sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/oext/run_mutants_oext_78b.py "$PWD" <SCRATCH_O> <OUT_O.json> ALL # ~16 min, background
sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/run_mutants_sr2.py "$PWD" <SCRATCH_S> <OUT_S.json> ALL          # ~12 min, background
sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/run_mutants_c_78b.py "$PWD" <SCRATCH_C> <OUT_C.json> ALL        # ~30 s

# P-2 first: the a0 check per family, before any fill (exit 0 = equal to the kit's basis, 1 = differs; read the per-seed line)
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/padded_tokens_78b.py --check-a0 --family olmo2-7b \
    --prepared tmp/kt-prepared/prepared-kt-dolly-olmo2 --out <OUT_DIR>/padded_tokens_a0_check__olmo2-7b.json
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/padded_tokens_78b.py --check-a0 --family llama31-8b \
    --prepared tmp/kt-prepared/prepared-kt-dolly-llama3 --out <OUT_DIR>/padded_tokens_a0_check__llama31-8b.json

# The record per family, over every edit pinned in RK at run time (R_d4-R_d13 and every non-null METHOD_EDITS pin).
# zsh: ${=EDITS} splits the words.
F=olmo2-7b; P=tmp/kt-prepared/prepared-kt-dolly-olmo2      # or F=llama31-8b; P=tmp/kt-prepared/prepared-kt-dolly-llama3
EDITS=$($PY -B -c 'import sys; sys.path.insert(0, "runkit/stage1-78b"); import rules_78b as r; f = sys.argv[1]; pins = list(r.R_DRAW_SOURCES[f].values()) + [p for p in r.METHOD_EDITS[f].values() if p]; print(" ".join("--edit " + p["path"] + ":" + p["sha256"] for p in pins))' $F)
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/padded_tokens_78b.py --family $F --prepared $P ${=EDITS} \
    --recorded-by "<WHO, the recorded lead step>" --out <OUT_DIR>/padded_tokens__$F.json
# then fill PADDED_TOKENS_78B[F] = {path, sha256} of that file by a recorded step (K2's reader checks it).
```

`<OUT_DIR>` must exist and lie inside no edit's folder and not inside P_F. M (in WS): the one-liner gives 12 edits per
family now (10 R_d, H1, S1). The tool needs the family's tokenizer in the offline cache, as Track C's tool does (not
run here: no real data).

## 7. Commands run (all foreground unless noted; exit status)

- Baseline suite without, then with the prepared copy: 643/57, 698/2, exit 0. `cp -pR` and the two hash lists: equal.
- The new test file during the build: one known-answer number fixed (rows are 10 tokens, not 9) and one class name
  fixed (FileNotFoundError); then 39 passed.
- W2-4 tests, then the old line put back: 3 failed (expected); restored.
- `make_oext_settings_78b.py --w1-18-78b` (exit 0) and the RK checks in §3 (M).
- The P runner ALL (exit 0), the O-ext R3 shard (exit 0), the SR-2 stop shard (exit 0), the C runner ALL (exit 0).
- Full scale78b suite after: 757/2, exit 0. Kit suite: 619 passed.
- SR-2 ALL: started in the foreground; the tool moved it to the background after 180 s; it ended with exit 0 (87
  killed) before this report was finished.
- The Track P spec again on the final bytes (after a comment-only citation fix in the tool): baseline 39 passed,
  imports the copy true, 47 killed (`R/r3-p-scratch/mut-p-all-final.json`; the tool's hash there is `11a0b9c904d4…`).

## 8. Acceptance

| Criterion | Result |
|---|---|
| The scale78b suite passes under the sandbox | **passed**: 698/2 before, 757/2 after (M) |
| Every mutant killed, none invalid: the new P spec | **passed**: 47/47 (M) |
| The O-ext runner | **partly tested**: the 7 new mutants are killed (M); all 110 finds occur once; the full run is the lead's |
| The SR-2 runner | **passed**: 87/87 (M) |
| The count-tool runner | **passed**: 71/71 (M) |
| Mutants for each refusal, the steps rule, the seed rule, the a0 check, W2-4 and W2-5 | **passed** (§5) |
| The 7-8B kit suite still passes in WS (619) | **passed**: 619 (M) |
| A test loads the output through the kit's reader | **passed**: `test_the_kits_reader_takes_the_record` (plan_tool.padded_tokens, imported read-only; it refuses the a0 check record) |
| A run on real data | **not tested** (forbidden by the brief) |

## 9. Open points for the lead (not decided here)

1. **P-1 and R's seeds.** P-1 takes the largest over seeds 1101-1107. But R_d runs at seed 1100 + d, so R_d4-R_d13 run
   at 1104-1113 (R: rules_78b.py:1909-1924 `run_edit`; Part 2 §2.1). For R_d8-R_d13 the seed they train at is outside
   1101-1107, so their value is not that seed's. The value is still a largest over seven orders (I: probably close).
   To include each run's own seed, change `SEEDS` to `range(1101, 1114)` (one line, +6 seeds a run) or add the
   edit's own seed. That changes the ruling, so it is the lead's call.
2. **`source` is an object**, not a string. K2's reader does not check its type (R: plan_tool.py:4014-4016), and R-46
   asks for MAIN_F's hash and per edit rows and steps, which K2's `edits` values (numbers only) cannot hold. K2's own
   test fixture uses a string. If the lead wants a string, the per-edit detail must move out of the record.
3. **One record per family covers the edits pinned when it runs.** A1, L1, S3, S4, S4_96, S4_192 (and s4_top) are null
   now. The reader refuses a run whose edit is not in the record. So the record is made after the last method edit is
   filled, or remade (a new file and a new pin) after each fill.
4. **Where the record lives.** Not ruled. A folder beside R-21's, for example
   `.ai/inputs/stage1-post-w1-20261023/78b/padded-tokens/padded_tokens__<F>.json`, would fit the pattern (I).
5. **The a0 basis seed.** The kit's constant is "the family's smallest a0 value" at 1103 (R: rules_78b.py:283). The check
   compares at 1103 only and prints all seven seeds. If 1103 is not the smallest of 1101-1107, that is information for
   the lead, not a refusal.

## 10. Concerns

- The engine's per-step padded count (runner.py:544-545) is an inline expression, not a function. The tool repeats it,
  cites it, and records the engine files' SHA-256. A test checks it against an independent count written in the test
  file. A later engine change would show as a different `engine_files` hash, not as a refusal.
- The tool depends on `encode_count_78b.py`'s helpers. A mutant there is killed only by Track C's tests (its own spec).
- `run_mutants_p_78b.py` copies `scripts/scale78b`. The kit-reader test imports `plan_tool` from the linked `runkit/`
  (read-only), so it reads WS's kit, never the copy.

## 11. Scratch

`R/r3-p-scratch/`: `make_specs.py` (builds the P spec and appends the R3 O-ext mutants, each find checked once), the
mutation reports (`mut-p-all.json`, `mut-p-all-final.json`, `mut-oext-r3.json`, `mut-sr2-stop.json`, `mut-sr2-all.json`,
`mut-c-all.json`) and `w1_18_78b_new.json` (the printed W1_18_78B form: paths and hashes only). The runners' repo copies
were deleted after the runs.

## 12. Fix round (the verifier's VERIFIED_WITH_MINOR, `R/r3-p-verify.md`; GXB set 20, R-54 to R-58). Written 2026-11-09 14:38 UTC

**Status: done.** Every item has a change, a test and a mutant (where a mutant applies). R-55, R-56 and R-57 need no
change. R-57's record path passes the `--out` rule: it is not inside any edit's folder or inside P_F.

| Item | Change (R: WS) | Test | Mutant(s) |
|---|---|---|---|
| R-54 seeds | `SEEDS = range(1101, 1114)` (padded_tokens_78b.py:74). RULE and the docstring now say 1101-1113 and R-54. | `test_the_constants_equal_the_kits`: SEEDS = 1101-1107 together with RK's `R_SEED_BASE + d` for every R_d (13 seeds). The record test checks the seeds and that the rule names "1101-1113" and "R-54". Every per-seed test now runs 13 seeds. | P-m-seeds-six re-targeted (to 1101-1107); new P-m-seeds-last (1101-1112) |
| R-58 / V-7 | The check record's `a0.smaller_than_basis_seed` lists every seed whose total is below seed 1103's (:283). It is also printed (:299-300). The exit code is unchanged. | The a0-check pass test: the list equals the independently computed list, and it is printed with exit 0. New `test_the_a0_check_flags_no_seed_when_none_is_smaller` (equal rows: `[]`, "none"). | P-m-smaller-none, -le, -line, -exit |
| V-1 | none (the guard at :146-151 stands) | `test_a_forced_leak_refuses_in_the_record_mode` gains a "rewritten" case (the edit now has a rewrite) | P-m-guard-rewrite |
| V-2 | none | New `test_the_record_names_the_tool_and_engine_files_by_their_hashes` | P-m-tool-sha, P-m-engine-files |
| V-3 | none | Equal-rows test: `largest_at_seed == 1101` when every seed ties | P-m-largest-tie-max |
| V-4 | none (the name guard kept, :153) | The forced-leak test gains a "name" case | P-m-guard-name |
| V-5 | none | The W2-5 path test gains `scripts/../<reader>`, `scripts//<reader>` and `<reader>.txt` (12 more cases) | R3F-m-reader-dotdot, R3F-m-reader-py (O-ext spec) |
| V-6 | `encode_count_78b.out_ok` refuses a symbolic-link `--out`, dangling or not, before it is resolved (encode_count_78b.py:496-497; 2 lines plus the docstring sentence) | Track C's `test_a_symlinked_out_refuses_before_it_is_resolved` (2 cases, `out_ok` directly) and the same through `padded_tokens_78b.main` (2 cases; the target is never written) | C-m-out-symlink (Track C's spec) |
| V-8 | none | The KR5 test runs RK's `anchor_stop_problem` on both forms (None). It checks that each form equals `anchor_stop_record`'s output from the job's own signal (exit 3 with the counts line; exit 1 with the harmful message), and it checks the harmful counts' values | none (a test strengthening) |

**Files after the fix round** (M: `shasum -a 256`). `oext_78b.py`, `make_oext_settings_78b.py`, `run_mutants_p_78b.py`
and `test_oext_78b_check.py` are unchanged since §2.

| File (scripts/scale78b/) | SHA-256 |
|---|---|
| `padded_tokens_78b.py` | `252fa35cbf6b092bd4be72be3da826045f7e3c3459086d275902f2f1ca35a4a7` |
| `tests/test_padded_tokens_78b.py` | `f98273e5f705758073505c8434ff3d5799bc9709e2818acbfce10ed9c08c26cf` |
| `tests/mutation_spec_p_78b.json` (57) | `ff3364287475ac8164c6a19ae3d89ff1c28e97a6bb70db4512c176193a436dc6` |
| `encode_count_78b.py` (Track C's; the lead's V-6 permission) | `9118196939ddc370a9cbb943ff14e1c25d3bb762d0ee5f80b707235802cd9f79` |
| `tests/test_encode_count_78b.py` | `efec82c69f584f269d5d19aaf9c3469d6f8e7cdaae8266e8dc3d9dcc6d09887d` |
| `tests/mutation_spec_c_78b.json` (72) | `4551d7c881b82f985cd9c5759b0393fe1a11a738f771a3d435a72b72cd279407` |
| `tests/oext/test_oext_78b_files.py` | `77d91075637be70d7091eccb04b818e19f23d9a25c7f54ca7f235f19b944e957` |
| `tests/oext/mutation_spec_oext_78b.json` (112) | `1afc8e2f29ecdaa16290539f2de1f12063e6897f18287f848f679a479f9dcbcf` |
| `tests/test_blinded_sigma.py` | `b144ae6444b35f30d3ef877c05bb95852f56afce32c6372f482aebe501c8714f` |

No literal pin of `encode_count_78b.py`'s earlier hash exists in `scripts/`, `runkit/` or `research/` (M: grep, 0 hits).

**Runs (M; all sandboxed, foreground, exit 0):**
- scale78b suite: **779 passed, 2 skipped** (81 s). +22 over §4: 8 (padded tokens, now 47 cases), 12 (V-5), 2 (Track C's V-6).
- 7-8B kit suite: **619 passed**.
- Track P spec ALL: baseline 47 passed, imports the copy, **57 killed**, 0 survived, 0 invalid (`R/r3-p-scratch/fix-mut-p-all.json`).
- Track C spec ALL: baseline passed, imports the copy, **72 killed**, 0 survived, 0 invalid (`fix-mut-c-all.json`).
- O-ext spec, the new or changed mutants (R3-* and R3F-*, 9): baseline passed, **9 killed** (`fix-mut-oext.json`).
  Every find of the 112 occurs once (the spec updater checks all of them: `R/r3-p-scratch/make_specs_fix.py`). The full
  O-ext spec (112, about 16 min) and the full SR-2 spec are still the lead's runs. The SR-2 spec's test file changed
  only by assertions inside the KR5 test.

**Remaining limit.** Seed dependence on the real sets is shown only by the real record's `seed_dependent` and
`padded_tokens_by_seed` fields. No real data was opened.

## 13. Last pass (the re-verifier's N-1 to N-3; GXB set 23, R-72 to R-74). Written 2026-11-09 15:09 UTC

**Status: done.**

| Item | Change (R: WS) | Test | Mutant |
|---|---|---|---|
| R-72 (N-1) | `encode_count_78b.py` is back at its d7eb772 bytes, written from `git show d7eb772:scripts/scale78b/encode_count_78b.py`. Track C's test file and spec are back too: my V-6 test and `C-m-out-symlink` are removed (71 mutants). The symlink refusal now sits in `padded_tokens_78b.main` (padded_tokens_78b.py:329-330), before `ec.out_ok`, in both modes; the docstring says so. | `test_a_symlinked_out_refuses_before_it_is_resolved`, 6 cases: dangling, to a file, to itself, each in the record and the check mode. The link stays, a dangling target is never created, and a file target is unchanged. | P-m-out-symlink |
| R-73 (N-2) | none in the tool | `test_the_constants_equal_the_kits`: SEEDS = 1101-1113. Every seed of `rules_78b.block_runs_78b` is in SEEDS: block A, plus block B under every plan, with 0, 3 or 6 dose seeds and kept 192, 150, 96, 60 and 48 (every K-5 case), both families. The largest is 1113. The record test is renamed `test_the_record_is_k2s_form_with_the_largest_value_over_every_block_seed`. | P-m-seeds-six and P-m-seeds-last, still killed |
| R-74 (N-3) | `source.encode_count_sha256` = SHA-256 of `encode_count_78b.py` (padded_tokens_78b.py:218) | The provenance test holds it equal to the file's hash | P-m-encode-count-sha |

**Byte check (M):** `git show d7eb772:<f> | cmp - <f>` is silent for `encode_count_78b.py`,
`tests/test_encode_count_78b.py` and `tests/mutation_spec_c_78b.json`. None of the three is in `git status`.
`encode_count_78b.py` hashes to `132dcd5bd63268afaa6f50df8284f61b7c9719cb84b4737f60f50bd19adebde3`, the hash the six
zero-check records name.

**Every changed file in WS against d7eb772 (M: `shasum -a 256`, final bytes):**

| File (scripts/scale78b/) | SHA-256 |
|---|---|
| `padded_tokens_78b.py` (new) | `bc523354ef7ff41efd94217c245c169efbc04d096dcc382d08f2f603339db69d` |
| `tests/test_padded_tokens_78b.py` (new) | `1ccf9d899156acd5938bed95450da1d4aabf25d7781c04077fa6bb7359bc33b2` |
| `tests/mutation_spec_p_78b.json` (new, 59 mutants) | `548dce2d9b9fa3024cc7b6b71f7aea9d6ca0d54a83434c66b9fcc838eb499e88` |
| `tests/run_mutants_p_78b.py` (new) | `af0c1c9a3b0961328c509a17b8e266c278b1cb4dfe55369c84a6211d0a2dc12d` |
| `oext_78b.py` | `e869b629581811fd3adae275d23113b0105d2bcf41212047091e71b82c650852` |
| `make_oext_settings_78b.py` | `f7c1c4829243e9492d84ee90bb0336f261c5003ce2ee718e6d5d1e3488acd069` |
| `tests/oext/test_oext_78b_check.py` | `14583dd9408fef6e8cd627086dd68b9078ef09b9f9908c3c9d1ba7dbce147d91` |
| `tests/oext/test_oext_78b_files.py` | `77d91075637be70d7091eccb04b818e19f23d9a25c7f54ca7f235f19b944e957` |
| `tests/oext/mutation_spec_oext_78b.json` (112 mutants) | `1afc8e2f29ecdaa16290539f2de1f12063e6897f18287f848f679a479f9dcbcf` |
| `tests/test_blinded_sigma.py` | `b144ae6444b35f30d3ef877c05bb95852f56afce32c6372f482aebe501c8714f` |
| `encode_count_78b.py`, `tests/test_encode_count_78b.py`, `tests/mutation_spec_c_78b.json` | unchanged (d7eb772 bytes) |

**Runs (M; sandboxed; exit 0):**
- Track P spec ALL: baseline 51 passed, imports the copy, **59 killed**, 0 survived, 0 invalid (`R/r3-p-scratch/last-mut-p-all.json`).
- Track C spec ALL: baseline passed, imports the copy, **71 killed**, 0 survived, 0 invalid (`last-mut-c-all.json`).
- 7-8B kit suite: **619 passed**.
- scale78b suite: **781 passed, 2 skipped** (285 s; slow because it ran beside the C runner). That is 779 + 4 (the symlink
  test now has 6 cases, not 2) - 2 (Track C's V-6 test removed).
- The O-ext spec did not change in this pass. Its full run (112 mutants) is still the lead's.

## 14. Integration fixes (the integration reviewer's I-1 and I-5; GXB set 28, R-86 and R-89). Written 2026-11-10 05:14 UTC

**Status: done.**

- **R-86 (I-1).** `make_oext_settings_78b.py --w1-18-78b --families F[,F]` (`parse_families`; `w1_18_78b_form(files,
  code, families)`). The option limits the side units and each family's W1 index and W1-18 settings. It is taken only
  with `--w1-18-78b`; each name must be one of the two families, given once; the output follows FAMILIES' order. The
  default is both families. M: the default printout is byte-identical to R3's (`cmp` with `R/r3-p-scratch/w1_18_78b_new.json`),
  and `--families olmo2-7b,llama31-8b` gives the same bytes.
  - Tests (test_oext_78b_files.py, last section): under [C], `--families olmo2-7b` names OLMo only, with no llama
    path. RK's `w1_18_route_problem` gives None on it, with the side units at KIT values, as in R-20's fill. It also
    gives None on the [B] form. [B]'s files with [C]'s side units are refused by RK ("its files name the O-ext index
    file(s)"). The default equals both families in either order. Bad options refuse (4 cases). K3's R-60 check is not
    in ws-p (the lead's cross-track probe).
- **R-89 (I-5).** `check_w1_18_pin` now also requires the record path to be exactly
  `RECORDS_DIR + "overrefusal_checks__<F>.json"` (`RECORD_NAME`, after the existing plain-path check). This is RK's
  `W1_18_RECORD_RE`.
  - Test: the standard name passes. Three names refuse: another basename, the other family's standard name, and K2's
    old `w1_18_record__<F>.json`.
- **Mutants** (O-ext spec, now 117): R3I-m-families-ignored, -families-dup, -families-only-w1, -record-name,
  -record-name-family. **Shard of these 5: baseline passed, 5 killed** (`R/r3-p-scratch/int-mut-oext.json`). Every
  find of the 117 occurs once.
- **scale78b suite: 790 passed, 2 skipped** (+9: 1 [C] form, 1 default, 4 option refusals, 3 record names).

Final SHA-256 of the files changed in this pass (every other file is as in §13):

| File (scripts/scale78b/) | SHA-256 |
|---|---|
| `make_oext_settings_78b.py` | `6493dc8398fb863ed7f38269f094c5d7824706ddfd64b41e49c2c9995ca9d80e` |
| `tests/oext/test_oext_78b_files.py` | `edca2255f4e5f9f7a96473a9dde85a3e6769e70fba3a3658d7ec8a7ff266c8a2` |
| `tests/oext/mutation_spec_oext_78b.json` (117) | `5febb1f1ac8fd7a4d203e822ed79d2709e7ec8dabcc5a563b3e7341aa5cec25f` |
