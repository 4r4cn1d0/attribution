# D1-readers: independent adversarial verification, round 3 (after fix round 2, the lead's ruling R4.2)

- **Written** 2026-11-01, finished about 15:02 UTC (clock read with `date -u`: 14:39:39 at the start, 15:00:10 before
  writing), by an independent verifier for the main-study lead (GI VIII), track D1-readers (the launcher records the
  model).
- **Object.** `scratchpad/builds/ws-d1` at `55d5f8b` (`git rev-parse HEAD`); `git status --porcelain` shows only the
  untracked folder `scripts/stage1_s1/reading_extra/` (17 files); `git diff` is empty. The SHA-256 of all 17 files
  (`verify-D1-readers/v3/sha256-current.txt`) equals the build report's §7.4 after-list and the builder's
  `d1-fix2-checks/sha256-after.txt`; the 11 files the builder calls unchanged equal the §7.4 before-table and
  `sha256-before.txt` byte for byte. The main checkout is at `53f746d`; from `55d5f8b` it changes no file under
  `scripts/`, `runkit/`, `experiments/` or REV4's folder except B14's test files (D-6's merge), none of which this
  package imports. Every rule text was read with `git show 55d5f8b:<path>`.
- **Data rules kept.** I opened nothing under `tmp/`, no block-a/ or block-b/ folder, no unit, eval, answer, label,
  guard-sample, judge or COMPLETE.json file of real data, no seal, no hidden or selector bank, no plant or decoy path,
  no W1 sealed record (the anchor bank's hash I took from FOCUS:198 at `55d5f8b`, not from the bank). Every reader ran
  on synthetic kits (the builder's `synth_kit` and `extra_kit`) in basetemps under `scratchpad/builds/tmp/v3-*`, all
  deleted (332 MB for the suite). No git command that changes state; no network, install, pod or API call; no
  background job; the longest command ran 3 min. I did not edit `ws-d1`; the package hashes are unchanged after my
  runs (`diff` against `sha256-current.txt`), and no `__pycache__` was left.

## Verdict: verified (no defect; notes 1-8 below are not defects)

The three ruled changes are built as R4.2 says and compute what they claim. (a) Every `ref_eval` point (adapter
scaling 0.9, 0.75, 0.5 and SP) now carries a C-full value by REV4:813 read literally: the complete `a0_arm` run at the
same seed in the reading's blocks, its measured slot, minus the frozen C-full training price 219.7 s, plus the job
ledger's measured transform stage, printed over 2,934 s (`c_full_fre`) and over the measured c0 (`seconds_over_c0`),
with K5's "null: not stated" beside it (`alternative_k5`) and a per-reference mean over seeds (`b10_per_reference`).
My own walk of the raw ledger files and plan.json reproduces every value (101 checks, 0 failures). (b) No line the
cap reader writes says "no full answer exists"; the pooled PHTest line points to theta0's LN-14 pass and copies its
share. (c) K3 and `charging.split_denominator` name DataShield-style; `charging.anchor_job` names Gate B's anchor job
with facts I checked at `55d5f8b`. Nothing else changed in value: the previous verifier's 283-check script passes 281
checks on the final code, and its only two failures are its own hard-coded round-2 expectation that the ref_eval
points' C-full is null (the very thing R4.2 ordered changed). The suite passes (120); the 14 new or re-anchored
mutants are killed in my own runs of the package's runner (14/14, 0 invalid).

## (a) REV4:813 read literally: what I checked and how

- **REV4's own words (at `55d5f8b`).** REV4:813: "**C-full:** §7.3. For an evaluation-only reference: the same minus
  training, plus its transform." REV4:633 (§7.3): C-full is "every in-job stage ... The unit is 1 FRE." REV4:774:
  every menu arm "with its label, O, L and cost under both conventions"; REV4:770: the Sp menu holds "SP, adapter
  scaling, Safe LoRA, recipe G, B+Qi". REV4:816: a reference "is charged what a practitioner who already has a0 pays
  on top of it". REV4:804-806: training 220.4, 219.7, 216.0 s (median 219.7). REV4:825: one evaluation-only state
  0.93 FRE.
- **Which a0 run.** The kit evaluates each `ref_eval` job on block B's own a0 run at the same seed:
  `runkit/stage1-olmo/stage1_rules.py:477` (`SECOND_PHASE_KINDS`, "the evaluation-only references on block B's own a0
  runs"), `plan_tool.py:167-170` (K1), `:628` (a `ref_eval` or `safe_lora` job must be on a0 at an a0 seed), `:2483-2504`
  (the second phase waits for the a0 runs), and REV4:479 ("an evaluation-only reference is a transform of a0 at the
  same seed"). So the matched run is the complete `a0_arm` job at the same seed with a readable ledger in the reading's
  blocks, and the reader takes exactly that (`a0_runs = _runs(ledgers.of("a0_arm", "a0"))`, keyed by seed; a second
  complete a0 run at one seed already refused, as in the arms table).
- **Which training price.** `scripts/stage1/settings/selector_spec.json` `cost_conventions.C-full.training_s` = 219.7
  ("the median training of R_1-R_3"), read by key at `55d5f8b`; the C-lean variants a and b hold 220.0. The reader's
  `FULL_TRAINING_S = 219.7`, pinned by a test to the spec and to the median of REV4's table, and a mutant to 220.0 is
  killed. The ledger's own `training` stage cannot replace it: `job_runner_stage1.py:790-795` maps the whole
  `-calibrate` step (training and the full evaluation together) to "training", so the frozen price is the only
  separable training price, as the ruling says.
- **Which transform.** `write_ledger` (`job_runner_stage1.py:802-817`) fills the `transform` stage from
  `transform_seconds_total` only, which only Safe LoRA's `-transform-P` steps carry; a `ref_eval` ledger's transform
  stage is 0 and the reader reads the stage rather than assuming it (a planted 7.5 s and my planted 12.25 s are added).
- **My own computation** (`verify-D1-readers/v3/own_check.py`, output `own_check_out.txt`; my own walk of plan.json
  and the `cost-ledger.json` files, not the reader's classes): on the synthetic plan-A kit with ref_eval jobs at 1105,
  1106 and 1107, the 1107 ledger's transform set to 12.25 s and the 1106 a0 slot set to 100 s: 1105 → 2,349.022 s =
  0.800621 FRE = 2.167028 c0 for each of the four points (a0 slot 2,568.722 − 219.7 + 0); 1107 → a0 slot − 219.7 +
  12.25; 1106 → null with "the a0 run's slot is below the frozen C-full training price", the a0 run still named, no
  `seconds_over_c0`; the per-reference mean over 1105 and 1107 (0.492089 FRE on that kit) with 1106 in
  `seeds_without_c_full_fre`; the C-lean (K6) value 0.797045 c0 unchanged for every point and averaged over all three
  seeds; K5's null beside every value; the whole ref_eval job's C-full still its own slot. Further cases: no c0 (the
  FRE value stands, `seconds_over_c0` and C-lean null, the seed listed under `seeds_without_c_lean_c0`); a ref_eval at a
  reused seed (1103, no a0 run in the ledgers: null, "seed 1103" named, C-lean stays); the match is by seed over the
  reading's blocks; two complete ref_eval jobs at one seed refuse; block A only prints empty B10 blocks; the
  command line writes canonical JSON, exits 0, and a second run exits 2 with the file unchanged. Safe LoRA's
  per-reference means equal its measured per-point values (menu names "Safe LoRA default/conditional/certify").
- **The builder's hand check** (`d1-fix2-checks/fix2_check.py`) re-run on the final code: 0 FAIL.
- **Stated in the output and the docstring.** `RULE` has REV4:774 and :813 as their own entries; `READINGS` K8 cites
  REV4:813, :774, :804-806 and the kit's K1; K5 now says its null is printed beside K8's value; the module docstring
  (lines 28-36) states the reading with REV4:774 and :813; `units.full_training_s` is printed. A test checks the
  quoted texts and eleven line numbers against REV4 in the tree.

## (b) The LN-19 PHTest line

- `cap_reports.py` holds no "no full answer exists" (grep: only the tests and the synthetic plant, which copies
  oext_eval's own text). `NO_BOTH_FORMS["phtest"]` says the units' PHTest answers are made at the cut cap only under
  Branch 128 and that theta0's LN-14 pass holds both forms of its 400, pointing to `ln14.report.flag_change`; the pooled
  PHTest line carries `theta0_ln14` copied from it. My check on three synthetic worlds: Branch 128 with the transfer
  pass (pooled n = 0, share null, the pointer, `theta0_ln14` = 400 prompts, 4 changed, share 0.01 = the report's; every
  by-arm PHTest line carries the same pointer); Branch 128 without it (`theta0_ln14.why` starts "not run"); Branch full
  (every unit holds both forms, the pooled share from the planted values, `theta0_ln14.why` says Branch 128 only). The
  per-unit notes stay oext_eval's copied text (note 4).

## (c) K3's denominator and the anchor job

- K3 and `charging.split_denominator` name DataShield-style (REQ-12), Gate C's reproduction and stage 1b's pools as
  users of the representation pass outside the denominator, so each share is an upper. `charging.anchor_job`'s facts
  checked at `55d5f8b`: host anchor-1, launched 2026-10-10 13:29 UTC, done 14:01 UTC, job 2.2 min, 64 harmful + 64
  safe, anchor file SHA-256 `2cf96336…` (FOCUS:198-199; SPF:211, :250); pod overhead 26.0 min on anchor-1 (REV4:808);
  "anchor job ... charged in full" (REV4:796); the bank row (REV4:62) and L1's scan on the 64 harmful anchor prompts
  (REV4:127); "A1's bi-anchored score" is REV4's own term (:735, :1002). It is named and not priced
  (`charged_here` null, with the reason), which is what the ruling asked.

## Nothing else changed

- The 11 unchanged files are byte-identical to the before-table. No copy of the round-1 `cost_table.py`,
  `cap_reports.py` or their tests exists outside `ws-d1` (the builder kept hashes, not files), so a text diff was not
  possible; the substitute is the previous verifier's `r2_check.py` re-run on the final code: 281 of 283 checks pass
  (every arm's runs and mean, every charge whole and split, every by-kind total, c0, the lean state, the R median,
  Safe LoRA's whole and per-point values under both conventions, the a0 regeneration apart, cap_reports' units, pooled
  and by-arm dev-100 shares, routes and the LN-14 bar, and the opened-file audit: under the kit only `plan.json`, the
  seals and `cost-ledger.json`; no sealed-class file; no listing). The two failures are its expectation
  `"per": {p: (None, lean)}` for the ref_eval points (K5's null), which R4.2 ordered replaced. `r2_edges.py`: the three
  edge cases pass; its fourth case asserted the old asymmetry and now prints the K8 values instead (by design).

## Tests and mutation

- Suite: `pytest -q -p no:cacheprovider --basetemp=tmp/v3-suite-1 scripts/stage1_s1/reading_extra/tests`: **120
  passed in 28.6 s**; basetemp 332 MB, deleted.
- Spec: 62 entries, every `find` text exactly once in its file (my own anchor check, 0 bad); the 14 ids R4.2's changes
  add or re-anchor are present. The builder's three shard reports name spec `4dca4cd8…`, baseline 120 tests, and
  baseline tree hashes equal to the current 17 files. My own runs of the package's runner (`--only`, scratch outside
  the workspace, deleted): shard a 5/5 killed (2 min 56 s), shard c 4/4 (2 min 17 s), shard b 5/5 (2 min 37 s); every
  baseline 120 pass; 0 invalid, 0 survived; reports `verify-D1-readers/v3/mut-fix2{a,b,c}.json`. The other 48
  entries were not re-run here (the lead's full-spec run is the record).

## Notes (not defects)

1. **"over c0" in R4.2 (the builder's open point 1).** C-full's unit is 1 FRE (REV4:633), so the reader prints
   `c_full_fre` as the value and the same seconds over the measured c0 beside it (`seconds_over_c0`, per point). The
   per-reference mean is of `c_full_fre` only; if the lead meant the c0 form as the C-full value, its mean over seeds
   is not printed (it equals `c_full_fre_mean × 2,934 / c0`; one line adds it). Both per-point numbers are correct.
2. **Two complete ref_eval (or Safe LoRA) jobs at one seed now refuse the whole table** (`_per_reference`), as two
   complete runs of an arm at one seed already did (`_runs`). The table is report-only and never stops the reading
   (R4.5), so a refusal means "not computed"; a crashed-then-re-run job is one complete job and does not trigger it.
   The alternative (list both, no mean) is the lead's call.
3. **All four ref_eval points at a seed get one value** (the a0 slot − 219.7 + 0): the literal reading has no per-point
   measurement, so the four menu lines differ only by name. The matched a0 slot holds its O-ext pass (K1), as the
   point's own evaluation does (the builder's open point 4).
4. **The units' copied PHTest notes** ("generated at the cut cap: no full answer exists") are oext_eval's own text,
   copied by key, true of each unit; the reader's own lines point to theta0's pass (the builder's open point 2).
5. **README:** its readings line still says "K1-K7" (K8 exists); the `__init__.py` docstring is unaffected.
6. **`OVER_C0_NOTE` cites "the lead's 1 Nov ruling"**, a scratch document; once the rulings are committed under
   `lead-reports-20261101/build-round/`, the pinned text could name that path.
7. **Real-kit assumption, untested here:** every ref_eval job's seed has a complete `a0_arm` run with a readable ledger
   in block B (the kit's K1 gate makes this so); an absent run prints null with the reason, never a refusal.
8. **Safe LoRA's points** keep their measured per-point C-full (K5); the 813 form is not printed beside them (the
   builder's open point 3), which the ruling did not ask for.

## Acceptance criteria (the ruling R4.2)

| Criterion | State |
|---|---|
| A C-full value per point for adapter scaling 0.9, 0.75, 0.5 and SP by REV4:813 read literally; the a0 run slot and the training price as REV4's own words give them | passed (my own computation, 101 checks; the kit's K1 and the spec's 219.7 checked at `55d5f8b`) |
| A per-reference mean over seeds | passed (`b10_per_reference`, mean/min/max, seeds without a value listed); note 1 on the c0 form |
| "null: not stated" printed beside it as the alternative reading (K5) | passed (`alternative_k5` on every point) |
| The reading stated in the output and the module docstring with REV4:774 and :813 | passed |
| The LN-19 PHTest line's "no full answer exists" fixed | passed for every line the reader writes (three worlds); the copied unit notes stay copies (note 4) |
| K3's split denominator named "DataShield-style"; the anchor job named | passed (facts checked at `55d5f8b`) |
| Change nothing else | passed: 11 files byte-identical; 281 of 283 earlier checks unchanged, the 2 differences being the ordered change |
| Tests and mutation entries for each change; suite and entries run in shards within 10 minutes | passed (120 tests; 14/14 killed in my runs, each shard under 3 min) |
| Refusals, exit codes, canonical JSON, exclusive create | passed (command-line check: exit 0, canonical bytes, second run exit 2, file unchanged) |
| Run on the real kit | not tested (forbidden) |

## Commands I ran (exit 0 unless noted; all on synthetic data)

| Command | Result |
|---|---|
| `git -C ws-d1 status --porcelain`, `rev-parse HEAD`, `diff --stat` (before and after); `git -C main log -1`, `diff --stat 55d5f8b HEAD -- scripts/ runkit/ experiments/ <REV4 folder>` (read-only) | only `reading_extra/` untracked; `55d5f8b`; main's code unchanged but B14's tests |
| `shasum -a 256` of the 17 files (before and after my runs); compared with §7.4, `sha256-before.txt`, `sha256-after.txt` | equal; unchanged by my runs |
| `git show 55d5f8b:` REV4 lines 625-640, 760-835, :62, :126-127, :796, :808, greps; `selector_spec.json` `cost_conventions` by key; `stage1_rules.py`, `plan_tool.py`, `job_runner_stage1.py:786-821`; SPF:211, :250; FOCUS:198-199 | the rule texts and kit facts above |
| `pytest -q -p no:cacheprovider --basetemp=tmp/v3-suite-1 scripts/stage1_s1/reading_extra/tests` | 120 passed, 28.6 s; deleted |
| `v3/own_check.py tmp/v3-own-1` | 101 PASS, 0 FAIL; deleted |
| `verify-D1-readers/r2_check.py tmp/v3-r2check-1` (the previous verifier's) | 281 PASS, 2 FAIL (the old K5 expectation); deleted |
| `verify-D1-readers/r2_edges.py tmp/v3-r2edges-1` | 4 PASS, 1 FAIL by design (the old asymmetry); deleted |
| `d1-fix2-checks/fix2_check.py tmp/v3-fix2check-1` (the builder's) | 0 FAIL; deleted |
| mutation spec anchor check (python; each find text once) and the three builder shard reports read | 62 entries, 0 bad; 14/14 killed; baseline trees equal the current files |
| `run_mutants.py --only` shards a, c, b (scratch `tmp/v3-mut-{a,c,b}`, deleted) | 5/5, 4/4, 5/5 killed; 0 invalid; baselines 120 |
| `date -u` | as above |

## Evidence paths

- `scratchpad/builds/verify-D1-readers/v3/`: `own_check.py` (`a4b36b24…`), `own_check_out.txt` (`b547ce48…`),
  `r2_check_rerun_out.txt` (`47ca5d99…`), `r2_edges_rerun_out.txt` (`29996e2f…`), `mut-fix2a.json` (`3bc34c1c…`),
  `mut-fix2b.json` (`9e0a9c74…`), `mut-fix2c.json` (`8bd7034d…`), `sha256-current.txt` (`f670acd3…`).
- Rules at `55d5f8b`: REV4:62, :126-127, :479, :633, :735, :770, :774, :796, :804-808, :813, :816, :825;
  `selector_spec.json` `cost_conventions`; `stage1_rules.py:477`; `plan_tool.py:167-170, :628, :2483-2504`;
  `job_runner_stage1.py:790-817`; SPF:211, :250; FOCUS:198-199; the lead's rulings R4.2-R4.6.
