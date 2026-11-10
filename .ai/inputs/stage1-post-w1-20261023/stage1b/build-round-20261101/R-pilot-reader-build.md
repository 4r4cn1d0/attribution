# R-pilot-reader: build report (the stage-1b pilot reader, `scripts/stage1_s1/pilot_gate/`)

Written 2026-11-01, 22:20-22:40 UTC (`date -u` at the start and at the end). Worktree
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/s1b/ws-r`
at `0d25497` (detached copy of `stageb-costs-and-recovery-safeguards-20261003`). `git status` at the end: only
`?? scripts/stage1_s1/pilot_gate/` (new files; nothing else changed; no git state command ran). Tags: (R) read in a
source; (M) measured here; (I) my inference.

## 1. What was built

One new package, `scripts/stage1_s1/pilot_gate/`, run as `python -m scripts.stage1_s1.pilot_gate`. No file of B16
(`scripts/stage1_s1/reading/`), the input builder (`scripts/stage1_s1/reading_input/`), `scripts/stage1/`, the kit,
the engine or any W1-listed file was changed (M: `git status`). No code path or file name holds "plant" or "decoy"
(M: `find scripts/stage1_s1/pilot_gate | grep -i "plant\|decoy"`: none). The arm names `a0_plant` and `a0_plant75`
appear only as string constants, as the brief names them.

| File (all new; before = none) | SHA-256 after | Lines |
|---|---|---|
| `scripts/stage1_s1/pilot_gate/__init__.py` | `c5869543389b2030d4fee8b561dadc1977ea31d087b731219f2d8cba2b401126` | 23 |
| `scripts/stage1_s1/pilot_gate/__main__.py` | `29ab82dd4151a1e13a95eec249ab35a24847d574bc6e707470b9b555118e5c7f` | 96 |
| `scripts/stage1_s1/pilot_gate/gate.py` | `d3dd0e0a59cc953e63c5cd518c60432e4364f008ece263f61d15a7b3038df037` | 173 |
| `scripts/stage1_s1/pilot_gate/units.py` | `deeb8b5ce5af448ab2065679873abf9314e8c9d8b03049f789a0ed263038be96` | 202 |
| `scripts/stage1_s1/pilot_gate/README.md` | `ac6e70669dc6dc138585d03a868b9c3f4491b7d4f859f72970ab775b1d288f32` | - |
| `scripts/stage1_s1/pilot_gate/mutation/run_mutants.py` | `9396e4c4275f75c54414c153be80827bde246a0ae099a6a7bd02d06468c2e4e5` | 218 |
| `scripts/stage1_s1/pilot_gate/mutation/mutants_pilot_gate.json` | `52d8725d30988d26a32b434984d1a5152294468fa873a7e0096d28fb77ca8751` | 495 |
| `scripts/stage1_s1/pilot_gate/tests/conftest.py` | `38f3222cff928699a71560abf4862c046adf81438e1fad48fba368d1029f3fb3` | 28 |
| `scripts/stage1_s1/pilot_gate/tests/synth_world.py` | `2a4bdbd1a90c0ae2579b1aa6911b89a01884e9495f4349174b4ed6dabeaa62a2` | 206 |
| `scripts/stage1_s1/pilot_gate/tests/test_gate.py` | `82f7d8529dc82220eaaf5ae7760c783d2b9c3b540fb20bfc42052000ee04c235` | 361 |
| `scripts/stage1_s1/pilot_gate/tests/test_reader.py` | `21dd170a516a6cc799a9013ade88bfde3e9bc9f9a3ef120ddef1d73874ba2a44` | 440 |

**Files to freeze by hash and stamp before P launches** (section 40 point 12): the four modules that the output's
provenance hashes (`__init__.py`, `__main__.py`, `gate.py`, `units.py`), plus `README.md`, the mutation spec and
runner, and the four test files, at the SHA-256 above. The output document records the four modules' hashes under
`provenance.modules` and B16's under `provenance.b16_modules`.

## 2. The rule as implemented (gate.py), against the sources

- **Lambda_plant** = B16's `contrast_paired(table, c="a0_plant", m="a0", seeds=(1101, 1102, 1103), scale=100,
  with_item=True)`: c minus m, so a plant that raises U gives a positive value (section 40 point 1; CHECK 1.2
  point 5). SE and df are B16's: the pair's own paired variance (ddof 1) over J = 3 with 2 df plus the crossed item
  part of the 3 x 200 difference table, Satterthwaite df (`contrast.py:168-173`, `_assemble`, `item_part`,
  `satterthwaite_df`). No other form exists in the reader (point 2, "no fallback"); the mutant that drops the item
  part (READY's fallback) is killed by the constructed-case test.
- **The lower bound** = Lambda_plant - `tdist.t_quantile(0.90, df)` x SE. Known answer tested: t(0.90, 2) =
  1.886 when the item part is 0 (a table whose per-prompt differences are constant within each seed gives
  `item_var` 0, `item_q` 0, df 2.0 exactly).
- **The label** (point 1): go if `est >= 10 - tol` and `lower > 5`; raise (pilot mode only) if `est >= 5 - tol`
  and not `est >= 10 - tol`; stop otherwise. `tol` = B16's `labels.tie_tolerance()` (the pinned settings'
  `margin.tie_tolerance_pp`, 1e-9), and the comparison form `value >= bar - tol` is B16's own (`labels.u_part`:
  `est >= delta - tol`); B16 has no standalone function for it, so `gate.at_least` repeats the one-line form and
  says so. The lower bound's comparison is exact (`lower > 5.0`), as B16 reads interval ends (README:153-155).
  Re-pilot mode: the same go test, else stop.
- **B16's pins**: `gate.B16_PINS` holds the 14 hashes `settings.module_hashes()` returns (13 modules and
  `settings/reading.json`), copied from the stamped manifest of the reading,
  `.ai/inputs/stage1-post-w1-20261023/reading/timestamp/ots-manifest-reading-20261101.json`
  (`files/scripts/stage1_s1/reading/*`; the same values are in `reading-runbook-20261101.md:109-122`). The reader
  refuses before any unit is read if `module_hashes()` differs; a test compares the pins with the manifest when it
  is in the tree and with this tree's B16 (both equal, M).
- **The rule texts** in the output: REV4:675 quoted byte for byte (a test checks the quote is in the REV4 file),
  section 40 points 1 and 2 restated, with the sources list.

## 3. Inputs: how the reader receives the units, and why (units.py)

**Chosen: by key from the kit's records**, the input builder's practice (`reading_input/build.py` `scan` and
`_primary_jobs`; RI/__main__ takes `--kit`), without the block seal:

- plan.json's hosts whose `block` is the one named (`--block`, default `P`) and that are recorded done
  (`record-done` sets `done` and the jobs' `unit` and `complete_sha256`: `plan_tool.py:3562-3625`, R). Among their
  jobs with status complete and not `pulled: false`, every one must be kind `arm`, the mode's arm (`a0_plant`;
  `a0_plant75` in re-pilot mode) at a seed in 1101-1103, else "an extra unit" refuses (the builder's rule); exactly
  one per seed (two refuse; none refuses). Hosts not done are not inputs and are listed by name; complete, not
  pulled jobs are counted.
- The unit: `retrieved/HOST/tree/<unit>` with the unit path checked against the runner's shape
  `round1/<seed>-edit-<64 hex>-e1-a<n>` (`job_runner_stage1.py:1042`, `ROUND`; the edit arm `edit-<SHA-256 of the
  edit>`, `:239-243`); COMPLETE.json must hash to plan.json's `complete_sha256` (record-done hashed the pulled file,
  `plan_tool.py:3596-3598`), be a complete marker with a file list (the builder's `_complete`), and name job.json by
  `job_sha256`; job.json must hold kind `run-one`, arm `edit-<the job record's edit sha256>`, the seed, target `e1`,
  `evaluate_bank` and `split` dev (the builder's `_check_job_json` with the builder's own field list). Every later
  file goes through the builder's `Folder.file` (listed by COMPLETE.json at its SHA-256 and hashing to it on disk).
- Gate A's a0: `REJUDGED_PINS["A"]` of the rules module loaded by path (the builder's `load_rules`; default
  `runkit/stage1-olmo/stage1_rules.py`, as RI does), the pin named exactly `a0 1101 (Gate A)` etc. with arm `a0`,
  the seed and target `e1`; the folder through the builder's `pinned_folder` (COMPLETE.json and job.json at their
  pins) and `_check_job_json(..., pinned=True)`.
- The per-prompt U: the builder's `items.harm` on `eval/e1/{summary.json, samples.jsonl, guard_samples.jsonl}`
  with the frozen coherence bars by pin (`items.bars`); the `U` part only (Unsafe share of the 3 sampled answers,
  checked against summary.json's counts; exactly 3 answers per prompt). The six units must hold one sorted set of
  prompt ids and B16's 200 (`settings()["endpoints"]["U"]["items"]`, as the builder checks). Nothing was copied
  from the builder; everything is imported, so no equality test of a copy was needed.

**Why not PATH:SHA256 arguments.** They need the lead to copy three paths and three 64-hex hashes by hand from
plan.json or record-done's output (a hand step on a record the lead otherwise never opens); the key route finds the
units from the design (block, kind, arm, seeds), refuses a duplicate, a missing or an extra unit by name, and binds
them by the hashes record-done wrote, as the stage-1 builder does. The lead passes only `--mode`, `--kit`, `--out`
(and `--block` for the re-pilot).

**Why no seal.** Section 40 point 12: "The pilot needs nothing sealed to run or to be read". The binding chain
plan.json -> COMPLETE.json (record-done's SHA-256) -> the files read (COMPLETE.json's list) is complete without it.
If plan.json records a seal for the block, its SHA-256 is noted in the output (`inputs.plan_json_block_seal_sha256`,
a hex64-checked string only; otherwise null). Requiring the seal (the builder's `Kit.folder`) is a one-call change
if the lead prefers it (open point 2).

## 4. Blinding (section 40 point 3; CHECK B1, B7)

- The reader reads `U` and the per-prompt labels by key only. The output holds no field of any unit file except
  the U values, the prompt ids and hashes; a test asserts the output text holds none of `"note"`, `"identity"`,
  `"trajectory"`, `"evaluation"`, `"edit"`.
- Every refusal is a fixed message that names the step and the design key (`a0_plant 1101`, `a0 1101 (Gate A)`,
  `block P`: strings built from code constants and the lead's `--block`). A `Refusal` or any other exception raised
  inside imported code (the builder's or B16's: JSON errors quote bytes, KeyError and ValueError carry values) is
  replaced in `units._step` by "<step>: refused by a check of the imported code (its message is withheld: it may
  hold a name, a path or a value)" or "<step>: an unexpected <Type> (...)". `__main__` adds the last net: any other
  exception prints its type only. Nothing from plan.json is printed; the host name is checked against a plain-name
  pattern and the unit path against the runner's shape before either is written to the output.
- Tests (`synth_world.py`): every non-U field holds a sentinel: the pilot units' edit name where the engine writes
  it (`trajectory.edit.name`: `runner.py:496-497`, `edits.py:90-92`, `ledger.write_complete`), job.json, the
  identity block, summary.json, plan.json's edit path and host record, every answer and judge text
  (`synth_kit.TEXT`). `test_reader.py` asserts no sentinel and no "Traceback" in stdout, stderr or the output file on
  the success path and on every refusal path (bad SHA-256, a changed COMPLETE.json, a missing unit, wrong seed, arm
  or kind in plan.json, two units, a missing unit, a not-done host, a not-pulled job, no edit SHA-256, a wrong unit
  path, a wrong host name, a broken plan.json, job.json fields and marker, a malformed guard_samples.jsonl that holds
  the sentinel in its bytes, wrong counts, a disagreeing summary, differing prompt ids, 199 prompts, Gate A pin
  names/arm/seed/target/duplicate/hashes/path, Gate A job.json, the rules module, the bars file, a changed B16 pin,
  an unexpected error carrying the sentinel in process and inside a step), and once more as a real subprocess
  (`python -m scripts.stage1_s1.pilot_gate`) on the success path and on the malformed-table refusal.

## 5. Output and stdout (`__main__.py`)

Canonical JSON (`scripts.stage1_s1.reading.settings.canonical_json`, the same bytes as the engine's for the
documents here) by exclusive create (`open(..., "xb")`); exit 0 written, 2 refused and nothing written. The
document: kind `stage1b pilot gate reading`, version 1, mode, block, arm, comparator, seeds, `estimate` (B16's
`Estimate.as_dict`: est, se, df, seed_var, seed_df, item_var, item_q, pairs, items, with_item, t, p_two_sided),
`t_quantile`, `lower_bound_pp`, `thresholds` (10, 5, 5, 0.90, the tie tolerance), `reads` (the three comparisons),
`label`, `cells_pp` and `differences_pp` per seed, `rule` (texts and sources), `inputs` (plan.json SHA-256, block,
the seal note, the rules module path and SHA-256, the bars pin, hosts not done, jobs not pulled, each unit's folder,
COMPLETE.json SHA-256 and the SHA-256 of each file read, the prompt ids, each unit's per-prompt U), `provenance`
(this package's modules, `b16_modules`, `b16_settings_sha256`, the pins' source, Python, numpy). A re-run is
byte-identical (tested). stdout: `wrote <file> sha256 <hex>`, then one line with Lambda_plant, SE, df, t(0.90, df)
and the lower bound, then `label: <word> (mode ...; a0_plant against a0 (Gate A), seeds 1101, 1102, 1103)`.

## 6. Tests (89, all synthetic) and the mutation spec (60 entries)

`test_gate.py` (known answers and edges): t(0.90, 2) = 1.886 and two more table values; the item part 0 case (df
2, t 1.886, the lower bound by hand); the sign (c - m; swapped tables negate; identical cells hit B16's own
"no finite degrees of freedom" refusal); equality with `contrast_paired` field by field; the label on 16 (est,
lower, mode) cases; a lower bound of exactly 5.0 is not above 5 (and 5 + 1e-12 is); the estimate's comparisons
through the tolerance (10 - 1e-15 reads as at least 10; 10 - 2e-9 does not; the same at 5); re-pilot never raises
on a 101 x 51 grid; **the edges**: random count tables whose three-seed mean is exactly 10 (and 5) pp as a
rational, one found whose float lands below the bar and one at or above (EV2:179's effect reproduced: found
within the first draws), both read as at least the bar, and one answer fewer (1/18 pp below) reads below it;
**section 40 point 2's constructed case** rebuilt (64 prompts 0 -> 3, 42 prompts 3 -> 0, 2 prompts 1 -> 2, one
answer more on seed 1102 and one fewer on 1103): Lambda 11.333 pp, SE within 0.05 of 5.10, df within 1 of 198.5,
lower bound within 0.1 of 4.78 and <= 5, label stop; the seed part alone (B16's `seed_only`): SE about 0.10, df 2,
lower about 11.15, which the go test would call go; **an independent recomputation** of the paired form from
scratch (plain Python, `math.fsum`, on the pp scale, no numpy and no B16 helper but the t quantile) on 24 random
tables of three kinds, agreeing to 1e-9 pp in Lambda, SE and the lower bound (df to 1e-6 relative), at least 6
with a non-zero item part; B16's pins against this tree and the stamped manifest; a changed pin refuses; the REV4
quote; `json_ready`.

`test_reader.py` (end to end on synthetic worlds): the values by hand, the whole document, the inputs' hashes
against the files on disk, the provenance, stdout's three lines; a byte-identical re-run and never overwriting;
go, raise and stop worlds from set counts; re-pilot mode on an `a0_plant75` world in block `P1b` (stop in the raise
band; the same block in pilot mode refuses as an extra unit); a seal note; U is the Unsafe share, not a G3 variant
(the synthetic cells hold Controversial and invalid answers); a not-done host and a not-pulled job are not inputs;
every refusal listed in section 4; the mode is required; the subprocess streams.

Mutation spec `mutants_pilot_gate.json` (the reading-time readers' runner, copied with its tree changed): 23 gate
mutants (sign, no item part, scale, level, two-sided, bound sign, seed df, go bar, bound not strict, bound through
the tolerance, no tolerance, tolerance sign, tolerance zero, raise bar, raise read, re-pilot raise, band upper,
go without the bound, B16 unchecked, a B16 pin, two seeds, re-pilot arm, inf sign), 31 units mutants (not-done
host, not-pulled job, extra kind/arm/seed, duplicate, missing, no host, block filter, edit sha, unit path,
COMPLETE.json sha, job.json kind/arm/seed/checkpoint/bank/marker, pin count/arm/seed/target/name, Gate A job.json,
ids, 200, withheld refusal, withheld error, U as each G3 variant, seal note), 6 main mutants (the pre-check drop,
documented equivalent, `expect: survive`; overwrite; the error message; B16 unchecked; mode; the label line).

## 7. Commands run (all in the foreground; every basetemp and scratch folder deleted afterwards)

Python: `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B` with
`PYTHONDONTWRITEBYTECODE=1`; pytest `-q -p no:cacheprovider -W ignore --basetemp=<fresh folder under
.../scratchpad/s1b/tmp/>`; cwd the worktree.

| Command | Result |
|---|---|
| pytest `scripts/stage1_s1/pilot_gate/tests -x` (first pass) | 1 failed (the sign test used an identical-cells table that B16 refuses by design), 2 passed; the test was changed |
| pytest (second pass) | 38 failed, 49 passed: one bug, `pilot_unit` called with (host, index, job); fixed to (host, job) |
| pytest (third pass) | 87 passed in 1.72 s, exit 0 |
| pytest (fourth pass, after the Controversial/invalid answers, the seal note and two tests) | **89 passed in 1.97 s, exit 0** |
| pytest `--collect-only scripts/stage1_s1` | 2,275 tests collected in 7.0 s, exit 0 (no basename clash: `test_gate.py`, `test_reader.py`, `synth_world.py` exist only here) |
| mutation shard 1 (`--only` the 23 gate ids, `--timeout 300`) | baseline pass (89 tests); 23 killed, 0 survived, 0 invalid; exit 0; 65 s |
| mutation shard 2 (18 units ids) | baseline pass; 18 killed; exit 0; 49 s |
| mutation shard 3 (13 units ids and 6 main ids) | baseline pass; 18 killed, 1 expected survivor survived (`PG-main-precheck-equivalent`); exit 0; 49 s |
| a find-count check of the spec (python) | 60 mutants, 0 bad finds |
| `git status --short`, `git rev-parse HEAD`, `git diff --stat` (read-only) | `?? scripts/stage1_s1/pilot_gate/`; HEAD `0d25497` |
| `date -u` | 22:19:39 UTC at the start of the writing; 22:40:00 UTC at the end |

Shard reports (ids, outcomes, counts, hashes and test names only):
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/s1b/reports/R-pilot-reader-mutation-shard{1,2,3}.json`
(SHA-256 `be089838b3cd645e72cb99b0834583a18530252eb09362e1631aef35e2cfda36`,
`09e3d38d4ccd5ee2131537a523957b9bcbd7568d8ea2ef9ae2560d1c36fd3d65`,
`cf9da6b88423e8e63b7c224ade01855b7a55d6a0efe95d8de348e5ffc747a904`). The full spec in one run is the lead's:
`python -B scripts/stage1_s1/pilot_gate/mutation/run_mutants.py --spec scripts/stage1_s1/pilot_gate/mutation/mutants_pilot_gate.json --scratch <outside the workspace> --report <file>`
(about 3-4 minutes, E: 60 x 2.3 s plus copies).

## 8. The command the lead runs after P's record-done

From the main checkout on the working branch, after this package is merged (and kit round 35, so that the
repository's `runkit/stage1-olmo/stage1_rules.py` holds block P and is byte-equal to `tmp/stage1-olmo/`'s copy, as
the runbook checks for the reading):

```
cd /Users/spiderishi/Coding/attribution
PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -B -m scripts.stage1_s1.pilot_gate \
    --mode pilot --kit tmp/stage1-olmo --block P --out .ai/inputs/stage1-post-w1-20261023/<the stage-1b folder>/pilot-gate-reading.json
```

`--repo` defaults to the repository (REJUDGED_PINS paths such as `tmp/family-probe-olmo2-1b/...` are relative to
it, as in the builder) and `--rules` to `runkit/stage1-olmo/stage1_rules.py`; pass `--rules tmp/stage1-olmo/stage1_rules.py`
to read the live kit's copy instead. The output file must not exist. stdout gives the label; the output's
`label` is the record (section 40 point 12: "its label recorded"). Before the run, the lead compares the four
modules' SHA-256 with the frozen, stamped ones (section 1) and may re-run the package's tests.

**The re-pilot** (only after a "raise"; a0_plant75 at 1101-1103 against the same Gate A units, in the block the
next kit round gives it, CHECK 5.3 names P1b):

```
PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -B -m scripts.stage1_s1.pilot_gate \
    --mode re-pilot --kit tmp/stage1-olmo --block P1b --out .../pilot-gate-reading-75.json
```

Any result other than go is stop (no second raise). If the re-pilot's units were put into block P itself, pilot
mode would see them as extra units and re-pilot mode would see the a0_plant units as extra units: the re-pilot
needs its own block (or a one-line change to the extra-unit rule, a post-W1 change written before any value is
read).

## 9. Alternatives rejected

1. PATH:SHA256 arguments for the units (section 3): hand-copied hashes; no duplicate/extra/missing check by design
   key. The key route is the builder's.
2. Requiring block P's seal through the builder's `Kit.folder`: section 40 point 12 says nothing sealed is
   needed; the chain plan.json -> COMPLETE.json -> files binds the inputs; the seal's SHA-256 is noted if present.
3. Copying `contrast_paired`, `item_part` and `satterthwaite_df` into the reader: importing keeps one
   implementation and the B16 pins bind its bytes; CHECK:275-276 allows the import under D-5.
4. Printing the builder's refusal messages as is (they hold names, paths, counts and hashes): the brief asks for
   fixed messages; the mutant that re-raises them is killed.
5. A default mode: `--mode` is required so that the lead states pilot or re-pilot.
6. Leaving the per-prompt U tables out of the output: they are the U field (allowed) and make the record
   re-checkable; one line removes them if the lead prefers (open point 5).
7. Reading the seed-only form beside the frozen one "for information": not built (point 2: no fallback; the
   constructed case shows it would mislead). The test shows the difference instead.

## 10. Acceptance criteria

| Criterion | State |
|---|---|
| (1) inputs by key, Gate A through REJUDGED_PINS["A"] by name with both pins checked; re-pilot arm | passed (synthetic); the real kit not read (hard rule 2) |
| (2) 3 x 200 per-prompt U tables as the builder builds them (imported `items.harm`) | passed |
| (3) Lambda_plant through `contrast_paired` (c = a0_plant, m = a0), B16's paired form, the 90% lower bound with B16's t | passed; independent recomputation agrees to 1e-9 pp on 24 tables |
| (4) the label with the tie tolerance on the estimate and an exact bound; re-pilot never raises | passed |
| (5) blinding: key-only reads, fixed messages, sentinel tests on every path | passed in process and as a subprocess |
| (6) canonical JSON by exclusive create, the fields listed, B16 pins checked, stdout | passed |
| (7) the known answers, edges, stop case, exact 5.0, re-pilot, the constructed table, the recomputation; the mutation spec in shards | passed; 60 mutants as expected |
| (8) the freeze list, the commands | this report, sections 1 and 8 |
| Not tested | the real plan.json, the real a0_plant units and the real REJUDGED_PINS (hard rule 2); the real COMPLETE.json layout of a pilot unit is inferred from the engine's writers (runner.py, ledger.py, edits.py), never from a record |

## 11. Open points for the lead

1. **Round 35's records.** The reader assumes block P's jobs are kind `arm`, arm `a0_plant`, seeds 1101-1103,
   each with an `edit` record holding `sha256`, the unit path `round1/<seed>-edit-<sha>-e1-a<n>`, and that block P
   holds no other complete job. If round 35 names things otherwise, the reader refuses (by design) and needs a
   one-line change before any value is read.
2. **The seal.** Not required (section 3). If the lead wants the seal binding too, `Kit.folder` replaces the
   folder construction in `units.pilot_unit` (then `seal P` must precede the reader, as CHECK 6 step 4 has it).
3. **Withheld messages.** A refusal inside the builder's code on a pilot unit prints only the step; the builder's
   diagnostic (for instance "3 prompts do not hold exactly 3 sampled answers") is withheld. On a Gate A unit the
   lead can run the builder's functions by hand; on a pilot unit a key-only diagnostic would be a separate
   reviewed script. I chose the strict reading of "every exception ... a fixed message".
4. **B16's pins** are literals copied from the stamped manifest; by design the reader refuses if B16 changes
   after the reading (D-5: it must not).
5. **The output holds each unit's per-prompt U** (the allowed field). Remove `per_prompt_u` from
   `units.read_units` if the record should hold the six cell values only.
6. **Where the output goes.** The command in section 8 names a folder under `.ai/inputs/stage1-post-w1-20261023/`;
   the lead picks the stage-1b folder and the stamp.
7. **The mutation runner** is a copy of the reading-time readers' runner with its tree changed (a 9-line
   difference, M: `diff`), as that runner is of the builder's.

## 12. Hard-rule log

- Opened: addendum section 40 (and grep lines of the addendum), CHECK, REV4 lines 655-720 and 675, the W1 record
  lines 280-300, B16's code and README, the builder's code and tests (`synth_kit.py`, parts of `test_builder.py`),
  the reading-time readers' code, tests and mutation spec, `stage1_rules.py` lines 150-330 and 780-830,
  `plan_tool.py` snippets (record_done, resolve_edit, the deal records), `job_runner_stage1.py` snippets,
  `seal.py`'s docstring, the engine's `edits.py`, `runner.py` and `ledger.py` snippets, the OTS manifest's file
  hashes, grep lines of the runbook and of E-40, folder listings of `.ai/inputs/stage1-post-w1-20261023/` (names
  only; the forbidden folders' names appeared in the listing and were not opened).
- Not opened: anything under `tmp/stage1-olmo/`, `retrieved/`, `hosts/`, `judges/`, `seals/`, any `plan.json` of
  the real kit, `run-20261101/`, `block-a/`, `block-b/`, any `units/` or `eval/` folder, any COMPLETE.json,
  answer, label, guard-sample or judge-cache file, any file whose path holds "plant" or "decoy" (no settings or
  record of the plant), the banks. No real data was read or run; no network, install, pod or API call; no git
  state command; nothing outside the worktree and my scratch was written.
