# R3 Track P verification (adversarial)

Written 2026-11-09 14:00 UTC; last updated 14:27 UTC (each time read with `date -u`). Target: WS = B/ws-p, read-only
for me. Builder report: R/r3-p.md. Scratch: S = R/r3-p-verify-scratch/. I wrote nothing in WS and changed no git
state. No pod, network, install, download, agent or message. I opened no forbidden folder, no prepared set and no
edit file. Every probe uses synthetic fixtures.

## Status

**Done.** Verdict: **VERIFIED_WITH_MINOR**. I found no major defect. There are 2 minor findings (test gaps) and 6
nits.

## How I checked

- **WS copy.** S/wsc is a `cp -pR` of WS. The SHA-256 of the sorted per-file `shasum -a 256` list is the same on both
  sides: `576f7892…` (M). The ten changed or new files hash to the builder's values in r3-p.md §2 (M).
- **Mutant source root.** S/wsv holds symlinks to S/wsc. Only its `scripts/scale78b` is a real copy, and that copy
  holds my two specs (S/vspec_p.json, S/vspec_o.json). The builder's runners ran it unchanged.

## Findings

| id | severity | R: path:line (WS) | what | evidence | fix |
|---|---|---|---|---|---|
| V-1 | minor | `scripts/scale78b/padded_tokens_78b.py:146-148`; test `tests/test_padded_tokens_78b.py:504` | No test kills the rule that rewritten responses go into the TextGuard. With `guard.add(item.get("response"))` for `rewrite` items replaced by `pass`, all 39 tests pass. I found no output path that prints a rewritten text (I), but the brief asks for a killing mutant for each rule. | M: mutant V-guard-rewrite SURVIVED (S/mut-v-p.json) | Add `"rewritten"` to the `which` parametrization of `test_a_forced_leak_refuses_in_the_record_mode`, with text = a rewrite response. Add that mutant to the P spec. |
| V-2 | minor | `padded_tokens_78b.py:213` (`tool_sha256`), `:216` (`engine_files`) | No test holds the record's provenance. A constant `tool_sha256` and constant `engine_files` hashes both pass all tests. The builder's §10 names `engine_files` as the only signal of a later engine change. | M: V-tool-sha and V-engine-files SURVIVED | A test that `source.tool_sha256` equals the tool file's SHA-256 and that `engine_files` equals `shasum -a 256` of the four engine files. Add both mutants. |
| V-3 | nit | `padded_tokens_78b.py:258` | No test covers `largest_at_seed` when seeds tie. Changing `min` to `max` over the tied seeds survives. The field is informational. | M: V-largest-at-max SURVIVED | In the equal-rows test (all seeds tie), assert `largest_at_seed == 1101`. |
| V-4 | nit | `padded_tokens_78b.py:150` | No test covers the guard on the edit's `name`. The name is never printed (I). | M: V-guard-name SURVIVED | Put the name in a forced-leak case, or drop the line. |
| V-5 | nit | `make_oext_settings_78b.py:457-458` | No test kills each W2-5 path condition on its own. Dropping only the `''`/`.`/`..` part check survives, and so does dropping only the `.py` check. The builder's R3-m-reader-path mutant drops all three conditions at once. At fill time, RK's `files_form_problem` refuses `..` and empty parts, but it does not refuse a path that is not `.py`. | M: V-m-dotdot and V-m-py SURVIVED (S/mut-v-o.json). M: `w1_18_route_problem` refuses `scripts/../scripts/family_probe_reading.py` (S/probe_rk_form.py). | Add the path cases `scripts/../scripts/family_probe_reading.py`, `scripts//family_probe_reading.py` and `scripts/family_probe_reading.txt`. |
| V-6 | nit (not Track P's file) | `scripts/scale78b/encode_count_78b.py:496-497` (Track C's `out_ok`, reused) | `out` is resolved before the `is_symlink()` check, so that check never fires for a dangling symlink. A dangling-symlink `--out` is followed: exit 0, and the record is written at the link's target. The write is still once-only and atomic, and the folder rule is applied to the target. A symlink into P_F is refused. | M: probe_blind case `out_dangling_symlink` (exit 0, target written); case `out_inside_prepared_via_symlink` refused | Check `Path(out).is_symlink()` before `resolve()`. This changes Track C's file, so it is the lead's call. |
| V-7 | nit (fix round) | `padded_tokens_78b.py:266-284`, `:287-294` | R-58 says the a0 check reports another seed whose a0 value is smaller than 1103's. The check prints and records every seed's total, but it does not flag such a seed. The ruling came after the build. | R: rulings-set20-draft.md R-58 | With R-54's seeds 1101-1113, add for example `smaller_than_basis_seed: [seeds]` and a printed line. |
| V-8 | nit | `tests/test_blinded_sigma.py:805` | The KR5 test checks the harmful-kind form by its key set only. It does not run RK's checker on that form. RK accepts both Track S forms. | M: S/probe_kr5.py: `anchor_stop_problem` gives None for both kinds; the safe form equals `anchor_stop_record`'s output | Assert `rules_78b.anchor_stop_problem(doc, family) is None` for both kinds. |

Informational (not defects):
- **Ids in messages.** Engine refusal messages print row ids, for example "(first: <id>)" and "added row '<id>'". This is
  by design (messages hold ids, counts and hashes). My sentinel, planted in ids only, showed in those two cases (M:
  probe_blind `edit_unknown_row_id_text`, `edit_bad_add_id_text`). I found no path that prints a prompt or response
  text.
- **Possible false refusal (I).** The record holds a long English `RULE` string and other key strings. If a whole P_F
  prompt or response of 6 or more characters is a substring of the record, the guard refuses the write. This fails
  safe, and it is the frozen `_text_hits` rule. Not seen on the fixtures.
- **No steps cross-check (I).** The tool does not compare its per-edit steps with RK's `run_edit(...)["steps"]` (RK
  STEPS: remove 33, add 38, dose 39). The lead can compare `source.edits[pin].steps` by eye.

## Item by item

### 1. The computation (M unless tagged)
- **Citations.** Every engine and kit line the tool cites is correct: `sed -n` on runner.py:164, :200-205, :420,
  :424, :426-427, :525, :527, :544-545; edits.py:169-176; plan_tool.py:3731-3732, :4009; rules_78b.py:111, :283,
  :295, :308.
- **Stream inputs.** The engine passes `removed = sorted(edit.removed)` (runner.py:374) and `prepared.corpus =
  sorted(train_rows)` (prepare.py:920). The engine's a0 removes nothing (`removed_rows('a0') == []`, prepare.py:924).
  The tool's `plan_for` makes the same calls.
- **Independent probe** (S/probe_compute.py, S/probe_compute.json: ALL EQUAL). For each case and each seed 1101-1107,
  four counts are equal:
  - T: the tool's per-seed total;
  - L: the engine's own `runner._train_segment` (with `en.train_step` stubbed), summed from steps.jsonl
    `padded_tokens`, and also its cost counts;
  - P: the real `en._right_padded(...)` tensor size, summed over the micro-batches;
  - Y: a pure-Python count written in the probe from stream.py's order rule.

  The fixture is 611 rows of varied length, with a different codec shape from the builder's tests. The cases:
  - combined remove 37 + rewrite 2 + add 23 (597 rows, 5 steps);
  - remove to 512 rows (4 steps);
  - remove to 513 rows (5 steps; the last step has 1 row);
  - add 20 (631 rows; the last step has 119 rows, an odd number);
  - the a0 check.
- **Steps, seed rule and check.** Steps equal ceil(rows / 128) in every case. Each value equals the largest engine
  total over the seven seeds divided by S. Every case is seed-dependent. The a0 check gives exit 1 against the real
  basis, as expected on a fixture, and writes its record.
- **The a0 basis.** `A0_BASIS` equals RK's constants. 1,457,026 / 38 = 38,342.789…, which rounds to 38,342.79.
  1,569,846 / 38 = 41,311.736…, which rounds to 41,311.74 (arithmetic; also test-held).
- **Exit codes.** My mutants V-check-no-value, V-check-no-steps and V-check-exit are killed. P-2's 0/1/2 codes and its
  total, steps and value equality are held.

### 2. Blinding and safety (M: S/probe_blind.py, S/probe_blind.json)
- **Cases.** There are 27 cases. Sentinels are in every P_F text, added text, rewritten text and the edit name. The
  checks cover stdout, stderr and every file in the output folder. The cases that passed:
  - the record and check modes;
  - another edit's pin; upper-case hex; a 63-digit pin; bytes changed after the pin; a missing edit;
  - not-JSON with text; an extra key with text; a rewrite or an add that is too long;
  - a codec error with text; a loader error with text (both modes); a SystemExit with text; an audit mismatch (check
    mode);
  - `--out` exists; a stale partial file of this pid (refused, and the stale file is kept); an fsync failure (no
    `--out`, no partial); a racing writer at `os.link` (refused, the racer's bytes kept, no partial); `--out` inside
    P_F through a symlinked folder; argparse (SystemExit 2, no text).
- **Exceptions.** The 2 id cases (informational) and the dangling symlink (V-6) are the only cases that did not pass.
- **CLI smoke.** Under `-I` the CLI imports and refuses with no real data. Exit 2: "the prepared set's manifest or
  tokenizer cannot be loaded (FileNotFoundError)".
- **K2's reader.** S/probe_reader.py makes a 4-edit record and loads it through `plan_tool.padded_tokens`, imported
  from S/wsc. Its keys are K2's, and the reader returns the record's values for A1, L1, S3 and S4. a0 takes none.
- **R-57 location (M).** No edit folder of either family, and neither P_F, is an ancestor of
  `.ai/inputs/stage1-post-w1-20261023/78b/padded-tokens` (path-wise check; symlink identity not checked). So
  `out_ok` accepts the ruled place.

### 3. W2-4 and W2-5 (M)
- **W2-4.** `ENGINE_X_IDENTITY` equals RK `ENGINE_X` (rules_78b.py:111) and is test-held. The W1-18 role is validated
  under it (oext_78b.py:576). My V-w-index-identity mutant (the index's identity) is killed by the engine-Y host test.
- **W2-5, the printed form.** I printed it in S/wsc (S/w1_18_78b_verify.json). It has keys {files, side_units}, and 10
  files. Both readers are listed at `8848340107bd…` and `1740663bc9e4…`, equal to `shasum` of the files in S/wsc and
  in MAIN.
- **W2-5, completeness.** `family_probe_reading.py` loads `killtest_stage0_reading.py` from its own folder
  (family_probe_reading.py:94). Its other imports are stdlib, so the two listed files are complete.
- **RK check.** `files_form_problem` gives None. `w1_18_route_problem` on the printout gives θ0's job-pin wait, as the
  builder reports. With the side units set to KIT's values and synthetic nulls, it gives None both with and without
  the readers.
- **Kit suite in the copy:** 619 passed.

### 4. KR5 (M)
- **The fixture.** Track S's safe-kind fixture equals the kit's shared fixture field for field (test) and equals
  `rules_78b.anchor_stop_record`'s output.
- **RK's checker.** `anchor_stop_problem` gives None for the safe kind and for the harmful kind
  ({prompt_index 5, position 6, of 64}).
- **Track S's reader.** `blinded_sigma.check_anchor_stop` accepts both Track S forms and the shared fixture.

### 5. Mutants
- **My P spec** (14 mutants on the tool): 9 killed, 5 survived (V-1 to V-4), 0 invalid. Baseline 39 passed; the copy
  is imported. Run 14:16:17-14:16:52 UTC. Report: S/mut-v-p.json.
  - Killed: V-seed-shift, V-div-fraction, V-second-largest, V-check-no-value, V-check-no-steps, V-check-exit,
    V-mb-last-row, V-out-no-edit-folders, V-scan-lines-only.
- **My O-ext spec** (4 mutants: 1 W2-4, 3 W2-5): 2 killed (V-m-first-family, V-w-index-identity), 2 survived (V-5),
  0 invalid. Baseline 163 passed, 1 skipped. Report: S/mut-v-o.json.
- **The builder's P spec, re-run ALL:** baseline exit 0, 47 killed (S/mut-builder-p.json).
- **The builder's 7 R3 O-ext mutants, re-run:** 7 killed (S/mut-builder-oext-r3.json).
- **Coverage.** Each refusal, the steps rule, the seed rule and the a0 check each have a killing mutant in the
  builder's spec. The gaps are V-1 to V-5.

### 6. Suites (M, under the network-deny sandbox, in S/wsc)
- scale78b: **757 passed, 2 skipped** (179.2 s), exit 0. This is the builder's count.
- 7-8B kit: **619 passed** (67.3 s), exit 0.

## Commands run (exit status)

Every command ran from S or S/wsc with `PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python`
under `sandbox-exec -p "$SB"`.

- `cp -pR WS S/wsc` and the two hash lists: equal.
- `$PY -B probe_compute.py S/wsc S/probe_compute.json`: exit 0, ALL EQUAL.
- `$PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests`: exit 0. This ran in the foreground; the tool moved
  it to the background at 180 s, and it ended with exit 0 before I continued.
- `$PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests`: exit 0.
- `$PY -B scripts/scale78b/make_oext_settings_78b.py --w1-18-78b`: exit 0. `$PY -B S/probe_rk_form.py ...`: exit 0.
- `$PY -B S/wsv/scripts/scale78b/tests/run_mutants_p_78b.py S/wsv S/mutrun-v-p S/mut-v-p.json ALL`: exit 1 (5
  survivors).
- `$PY -B S/wsv/scripts/scale78b/tests/oext/run_mutants_oext_78b.py S/wsv S/mutrun-v-o S/mut-v-o.json ALL`: exit 1 (2
  survivors).
- `$PY -B probe_blind.py S/wsc S/probe_blind.json`: exit 1 (the 3 cases above).
- `$PY -B S/probe_kr5.py S/wsc`: exit 0. `$PY -B S/probe_reader.py S/wsc S`: exit 0.
- `run_mutants_p_78b.py S/wsc S/mutrun-b-p S/mut-builder-p.json ALL`: exit 0.
- `run_mutants_oext_78b.py S/wsc S/mutrun-b-o S/mut-builder-oext-r3.json R3-…(7 ids)`: exit 0.
- `$PY -I -B scripts/scale78b/padded_tokens_78b.py --check-a0 ... --prepared S/smoke/no-such-prepared ...`: exit 2
  (expected refusal).

## Commands for the lead (after the fix round)

```sh
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'
S=<this report's scratch>; V=$S/wsv          # my specs live only in S/wsv's scale78b copy
sandbox-exec -p "$SB" $PY -B $V/scripts/scale78b/tests/run_mutants_p_78b.py $V <NEW_SCRATCH> <NEW_OUT.json> ALL           # ~35 s
sandbox-exec -p "$SB" $PY -B $V/scripts/scale78b/tests/oext/run_mutants_oext_78b.py $V <NEW_SCRATCH> <NEW_OUT.json> ALL   # ~100 s
```

To check the fixes for V-1 to V-5, copy the fixed scale78b over S/wsv's copy but keep my two specs, then run the
commands again. The expected result is 0 survivors. My mutant definitions are in S/vspec_p.json and S/vspec_o.json
(made by S/make_vspecs.py). The builder's full commands in r3-p.md §6 are unchanged and correct as far as I checked.

## Concerns

- I did not run the full 110-mutant O-ext spec. That run is the lead's.
- The 2 skips in the scale78b suite need scipy (builder's statement; I did not check).
- The probes use `--prepared` names only as strings. No real P_F, tokenizer or edit was read, so nothing was measured
  on real data.

## Scratch (S)

| Kind | Files |
|---|---|
| Probes | probe_compute.py `4a111ce6…`, probe_blind.py `6374d732…`, probe_kr5.py `da47b475…`, probe_reader.py `c12a8948…`, probe_rk_form.py `3921124b…`, make_vspecs.py `06cd2165…` |
| Results | probe_compute.json `d153bb26…`, probe_blind.json `90498261…`, mut-v-p.json `618ee70f…`, mut-v-o.json `9f4397f3…`, mut-builder-p.json `699cabe6…`, mut-builder-oext-r3.json `30bf776d…`, w1_18_78b_verify.json `984ccddf…`, kit-suite.txt |
| Copies | wsc (WS copy, 179 MB, including the git-ignored tmp/kt-prepared copied by the builder) and wsv (mutant root) |

The lead may delete wsc and wsv after reading this report.

## Re-verification (after the fix round, r3-p.md §12)

Written 2026-11-09 14:57 UTC (date -u). Target: WS = B/ws-p after the fix round. I copied it to S/wsc2 with `cp -pR`.
The per-file hash list equals WS's (`63d15116…`, M). Every file hash in §12's table matches, and so does each file it
names as unchanged since §2 (M). I wrote nothing in WS, and its `git status` is unchanged. I did not run the full O-ext
or SR-2 specs.

**Verdict: VERIFIED_WITH_MINOR.** All 8 earlier findings are fixed and held by a test, and so are R-54 and R-58. One
new minor finding (N-1) and two new nits (N-2, N-3).

### 1. Each fix, and the test that holds it (M unless tagged)

| Item | The fix is correct | Held by |
|---|---|---|
| V-1 | yes: the guard stands; the forced-leak test now has a "rewritten" case | V-guard-rewrite killed by `[rewritten-record]` |
| V-2 | yes: a new test compares `tool_sha256` and `engine_files` with the real files' hashes | V-tool-sha and V-engine-files killed |
| V-3 | yes: in the equal-rows test every seed ties, and `largest_at_seed == 1101` | V-largest-at-max killed |
| V-4 | yes: the forced-leak test has a "name" case | V-guard-name killed by `[name-record]` |
| V-5 | yes: 12 new cases (dotdot, empty part, not `.py`) per family and reader; each needle discriminates | V-m-dotdot killed by `[dotdot…]`; V-m-py killed by `[not_py…]` |
| V-6 | yes: `out_ok` refuses any symbolic-link `--out` before it is resolved (encode_count_78b.py:496-497). Only Track C's and Track P's tools import this `out_ok` (M: grep; the other `out_ok` functions are their own modules') | Track C's test and Track P's test (2 cases each); C-m-out-symlink killed (Track C spec ALL: 72 killed) |
| V-7 / R-58 | yes: `a0.smaller_than_basis_seed` lists every seed whose total is below 1103's (all seeds have the same steps, so the totals order the values); it is printed; the exit code is unchanged | the a0-check tests; P-m-smaller-none, -le, -line, -exit killed |
| V-8 | yes: RK's `anchor_stop_problem` gives None for both forms; each form equals `anchor_stop_record`'s output from the job's own signal | test assertions (no mutant applies) |
| R-54 | yes: SEEDS = 1101-1113 | P-m-seeds-six and P-m-seeds-last killed; see N-2 for the test's form |

**Independent checks of the fixed code:**
- S/v2/probe_compute.py (the tool's own SEEDS) gives ALL EQUAL. At all 13 seeds, the tool equals the engine's
  `_train_segment`, the real `_right_padded` sizes and the pure-Python count, in all 4 edit cases and the a0 check.
- R-58's list from the engine-loop totals equals the tool's list: [1102, 1104-1113] on the fixture, printed.
- The wider maximum raised two fixture values (combined 8,354.6 -> 8,355.4; 512 rows 9,008.5 -> 9,044.0), as R-54
  expects.
- R-54's coverage (M): every seed of `rules_78b.block_runs_78b` over blocks A and B, plans A, B9 and H, and the dose
  rows (3 and 6 seeds) is 1102-1113. All of these lie in SEEDS.

### 2. My 7 earlier survivors, re-run with my baseline's command (M)

The new mutant root is S/wsv2: wsc2 with my unchanged specs (SHA-256 `9a3adf0a…` and `8621fca0…`; every find occurs
once in the fixed files).
- `run_mutants_p_78b.py S/wsv2 … ALL`: baseline 47 passed, the tests import the copy; **14 of 14 killed**, 0 survived,
  0 invalid (S/mut-v2-p.json).
- `run_mutants_oext_78b.py S/wsv2 … ALL`: baseline 175 passed, 1 skipped; **4 of 4 killed** (S/mut-v2-o.json).

So all 7 earlier survivors are killed: V-guard-rewrite, V-largest-at-max, V-tool-sha, V-engine-files, V-guard-name,
V-m-dotdot and V-m-py. The builder's specs, re-run in S/wsc2:
- P ALL: 57 killed (S/mut-v2-builder-p.json).
- C ALL: 72 killed (S/mut-v2-builder-c.json).

### 3. Probes of the new code (M)

- **V-6 symlinks** (S/v2/probe_blind.py, 30 cases):
  - A dangling link, a link to an existing file (the target keeps its bytes) and a self-loop link are all refused
    (exit 2). Each message names only the link's name.
  - A plain parent folder reached through a symlink is still accepted, and the record lands in the real folder.
  - `--out` inside P_F through a symlinked folder is still refused.
  - Every earlier case keeps its earlier result. The 2 id-in-message cases are informational, as before.
- **Suites in S/wsc2** (network-deny sandbox, in two shards of the scale78b suite):
  - scale78b: 277 passed + 502 passed, 2 skipped = **779 passed, 2 skipped**, both exit 0. This equals the builder's
    count.
  - 7-8B kit: **619 passed**, exit 0.

### New findings

| id | severity | R: path:line (WS) | what | evidence | fix |
|---|---|---|---|---|---|
| N-1 | minor (a provenance point; follows from my V-6 suggestion) | `scripts/scale78b/encode_count_78b.py:496-497` | Track C's tool has already made the six zero-check records in `MAIN/.ai/inputs/stage1-post-w1-20261023/78b/zero-checks-20261108/encode-count-*.json`. Each names `provenance.script_sha256 = 132dcd5bd63268af…`, the file at d7eb772. After this merge, the committed script hashes to `9118196939ddc370…`, so those records no longer name the committed script. No code checks this: grep of runkit/ and scripts/ finds no reader of the records, and `commitments.py` only lists `made_by`. The counts stay valid, because the change only adds a refusal those runs did not hit (I). | M: `grep -rl` of the old hash (file names only); key path printed only | Either (a) keep `encode_count_78b.py` at d7eb772's bytes and put the symlink refusal in `padded_tokens_78b.main` before `ec.out_ok` (one line in Track P's file; move the C test and mutant to Track P). Or (b) keep the change and add a recorded note beside the zero-check records naming old -> new hash and the 3-line diff. I recommend (a). The lead decides. |
| N-2 | nit | `tests/test_padded_tokens_78b.py:304-306` (the R-54 test), `:174` (test name) | The R-54 test asserts SEEDS equals a literal union, `range(1101, 1108)` plus R_d's seeds. Its comment, "the method arms and a0 at 1101-1107", is not RK's table: plan H runs method arms at 1105-1113, and block A starts at 1102. The test would not catch a later RK seed outside 1101-1113. The record test's name still says "seven seeds". | M: block_runs_78b union = 1102-1113 | Assert that every seed of `block_runs_78b` (blocks A and B, every plan and dose setting) is in SEEDS. Rename the test. |
| N-3 | nit | `padded_tokens_78b.py:214` (`common_source`) | The record's `source` names the tool's and the engine files' hashes, but not `encode_count_78b.py`'s. The tool takes its recipe and manifest pins, guard, `out_ok` and `write_once` from that file, and that file changed in this round. | R | Add `encode_count_78b.py`'s SHA-256 to `source` (one entry), with a test and a mutant. |

### Commands run (all under the network-deny sandbox, foreground, PY = the main venv)

| Command | Exit |
|---|---|
| `cp -pR WS S/wsc2` and the hash lists | equal |
| probe_compute (v2) | exit 0 |
| probe_blind (v2) | exit 1: only the 2 informational id cases |
| my P mutants ALL on S/wsv2 | exit 0 |
| my O-ext mutants ALL on S/wsv2 | exit 0 |
| scale78b suite, shard 1 (oext, refs) | exit 0 |
| scale78b suite, shard 2 (the rest) | exit 0 |
| kit suite | exit 0 |
| Track C spec ALL | exit 0 |
| Track P spec ALL | exit 0 |
| the RK seed union probe | exit 0 |
| the old-hash grep | file names only |

The runners' repo copies were deleted. S/wsc, S/wsc2, S/wsv and S/wsv2 may be deleted after the merge.

### Summary

VERIFIED_WITH_MINOR. Each of V-1 to V-8, R-54 and R-58 is fixed and held by a test. All 7 of my earlier survivors are
now killed. The builder's P spec (57) and C spec (72) kill every mutant. The scale78b suite gives 779 passed, 2
skipped; the kit suite gives 619 passed. The new findings:
- N-1 (minor): six committed zero-check records name Track C's script at its d7eb772 hash, and the V-6 change moves
  that file off that hash. I recommend putting the symlink refusal in Track P's own file instead.
- N-2 (nit): the R-54 test's literal seed union.
- N-3 (nit): `encode_count_78b.py`'s hash is not in the record's `source`.

## Final re-check (after the last pass, r3-p.md §13; rulings R-72 to R-74, set 23)

Written 2026-11-09 15:16 UTC (date -u). Target: WS = B/ws-p. I copied it to S/wsc3 with `cp -pR`; its per-file hash
list equals WS's (`9fa25e63…`, M). The four Track P files hash to §13's values (M). I wrote nothing in WS. Its
`git status` has 10 entries: the 6 modified and 4 new files of §13; Track C's files are not among them.

**Verdict: VERIFIED.** All three checks pass, and my earlier tool mutants are still killed. There are no new findings.

1. **Track C's files are byte-identical to d7eb772 (M).** I checked `encode_count_78b.py`,
   `tests/test_encode_count_78b.py` and `tests/mutation_spec_c_78b.json`:
   - `git -C WS diff --stat d7eb772 -- <the three paths>` prints nothing (exit 0);
   - `git show d7eb772:<f> | cmp - <f>` is silent for each;
   - `encode_count_78b.py` hashes to `132dcd5bd63268af…`, the hash the six zero-check records name.
2. **The symlink refusal works (M).** It is at `padded_tokens_78b.py:329-330`, inside `main`'s try, before
   `ec.out_ok`. S/v3/probe_symlink.py spies on `ec.out_ok` and runs 12 cases, 6 in each mode (record and
   `--check-a0`):
   - A link that is dangling, to a file, to itself, to a folder, or relative and dangling is refused with exit 2
     ("is a symbolic link"). `out_ok` is never called, the link stays, and the target is not written (the file target
     keeps its bytes, the folder target stays empty).
   - A plain new file under a symlinked parent folder is accepted: it is written in the real folder, and `out_ok` is
     called once.
   - My earlier probes on S/wsc3: probe_blind gives 28 ok, plus the 2 informational id cases as before.
     probe_compute gives ALL EQUAL at 13 seeds.
3. **R-73 and R-74 are held by tests (M).**
   - **R-73.** `test_the_constants_equal_the_kits` builds its seed set from the kit's `rules_78b.block_runs_78b`
     (imported through `plan_tool`). It covers block A and block B under every plan, with 0, 3 or 6 dose seeds and
     kept 192/150/96/60/48, for both families, and asserts the set is inside SEEDS with largest 1113. To show it reads
     the kit, I changed my copy's RK plan-H seeds to 1105-1114. The test then fails at `seeds <= set(pt.SEEDS)`.
     I restored the copy, and its hash equals the original.
   - **R-74.** `source.encode_count_sha256` (:218) is held equal to the file's hash by
     `test_the_record_names_the_tool_and_engine_files_by_their_hashes`.
   - **New mutants.** Run with the builder's runner by id: P-m-out-symlink, P-m-encode-count-sha, P-m-seeds-six and
     P-m-seeds-last are all killed (S/mut-v3-builder-new.json; baseline 51 passed, the tests import the copy).
4. **My 14 tool mutants**, on S/wsv3 with my unchanged spec (every find occurs once): `run_mutants_p_78b.py … ALL`
   gives baseline exit 0 and **14 killed**, 0 survived, 0 invalid (S/mut-v3-p.json).

**Also run (M):** `pytest` of `test_padded_tokens_78b.py` and `test_encode_count_78b.py` in S/wsc3 gives 128 passed.
I did not re-run the full suites, the full P spec or the O-ext spec. The builder reports 781 passed, 2 skipped, 619
passed, and 59 and 71 killed.

**Recorded limit (R-72; not a finding).** Track C's own `out_ok` still follows a dangling-symlink `--out`. Its $0 runs
are done, and none is planned again.

### Summary

VERIFIED. Track C's three files are back at their d7eb772 bytes. The symlink refusal sits in `padded_tokens_78b.main`
before `out_ok` and refuses in both modes. The R-73 seed test reads the kit's block tables: it fails when a kit seed
leaves 1101-1113. A test holds the R-74 field. My 14 tool mutants and the 4 new builder mutants are all killed. No new
findings.

## Integration re-check (R-86 / I-1, R-89 / I-5; r3-p.md §14)

Written 2026-11-10 05:26 UTC (date -u). Target: MAIN's merged working tree, read only.

**How I copied it.** I copied MAIN's `scripts`, `runkit`, `experiments`, `research`, `tests` and `tools` to S/mainc
with `cp -pR`. The per-folder hash lists for scripts, runkit and experiments equal MAIN's (M).
`make_oext_settings_78b.py`, `test_oext_78b_files.py` and the O-ext spec hash to §14's values. `padded_tokens_78b.py`
(`bc523354…`) and `encode_count_78b.py` (`132dcd5b…`) equal §13's (M).

**One run setup.** The O-ext baseline needs the repo's `.ai/` records (`test_the_committed_state_is_consistent`). For
the mutant runs only, I linked `S/mainc/.ai` to MAIN's `.ai/` (read only), then removed the link.

**Verdict: VERIFIED.** No new findings.

1. **R-86 / I-1 (M).** Each check passed.
   - **Default printout is unchanged.** The default `--w1-18-78b` printout is byte-identical to my R3 printout (`cmp`;
     both `984ccddf…`). `--families olmo2-7b,llama31-8b` and `llama31-8b,olmo2-7b` give the same bytes.
   - **OLMo-only form.** `--families olmo2-7b` (`a15eeba3…`) holds {files, side_units}, side units for OLMo-2-7B only,
     and 8 files with no Llama path. The bad options refuse with exit 2: a family given twice, an unknown family, a
     trailing comma, a missing value, and `--families` without `--w1-18-78b`.
   - **Through RK and K3's R-60 check.** My probe used K2's `wa` gate fixture, with θ0's waiting job pins set to the
     printout's, as the reviewer did. All 4 cases passed:
     - the OLMo-only form under [C]: RK's `w1_18_route_problem` gives None, and `plan_tool.w1_18_gate_families` gives
       ['olmo2-7b'];
     - the default form under [B]: RK gives None, and R-60 gives both families;
     - the default form under [C], and the OLMo-only form under [B]: R-60 refuses each.
2. **R-89 / I-5 (M).** The maker's check is `path == RECORDS_DIR + "overrefusal_checks__<F>.json"`. It is stricter than
   RK's `W1_18_RECORD_RE` (rules_78b.py:1442) because it also requires the family's own name.
   - Called directly, the family's standard name passes the name rule (my synthetic pin then stops at the later branch
     check).
   - These are refused: the other family's name, a subfolder, a capitalised name, `.json.json`, and K2's old
     `w1_18_record__<F>.json`.
3. **The 5 R3I mutants (M).** I ran them with the O-ext runner on S/mainc in two shards. Each shard's baseline is 184
   passed, 1 skipped. **5 of 5 killed**, 0 invalid:
   - R3I-m-families-ignored, R3I-m-families-dup, R3I-m-families-only-w1, R3I-m-record-name and
     R3I-m-record-name-family;
   - reports: S/v4/mut-r3i-a.json and S/v4/mut-r3i-b.json.

The probe test file I put in the copy was removed. S/mainc and S/v4 may be deleted.

### Summary

VERIFIED. The default W1-18 printout is byte-identical to R3's. The OLMo-only form passes RK's route check and K3's
R-60 check under [C], and is refused under [B]. The maker now accepts only RK's standard record name, and only the
family's own. All 5 new O-ext mutants are killed. No new findings.
