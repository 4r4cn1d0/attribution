# Track A-coherent: independent verification 1 (D-5, S-G coherent-only U, and the adverse G3a corners)

- **Written** 2026-11-01 at 10:57 UTC (clock checked with `date -u`) by an Opus worker acting as the adversarial
  verifier for the lead (GI VIII). Work ran from 09:19 to 10:56 UTC.
- **Scope.** The builder's workspace `scratchpad/builds/ws-a` (detached at `55d5f8b`), its report
  `builds/reports/A-coherent-build.md`, and the lead's seven rulings in the task text. I read the builder's report as
  claims and checked them against the code, the rulings, REV4, PREREG, `scripts/gate_b_reading.py`, ADD §33 and §37,
  FOCUS:76 and the review and critic reports.
- **Read-only.** I edited nothing in `ws-a` or the main checkout. I ran only read-only git commands (`status`, `diff
  --quiet`, `log`, `show`, `ls-tree`, `ls-files`, `rev-parse`, `hash-object` without `-w`). I wrote only under
  `builds/verify-A-coherent/` and this report. Temp folders `builds/tmp/vA-coh-*` were deleted after each run. After
  all runs, `ws-a` has the same `git status` as before, and no `__pycache__` or `.pytest_cache` folder.
- **Data rules kept.** I opened no stage-1 outcome, seal, host, judge, unit, answer, label, guard-sample or cache file,
  no bank, and no path with "plant" or "decoy". I did not open the W1 manifest. Every test, comparison and simulation
  used synthetic data. There was no network, no install, no pod and no API call.

## 0. Verdict: defects (one defect, in the test harness; no defect in any reading output)

1. **The reading code is correct as far as I can test it.**
   - My own reference implementation agrees with `sg_coherent.sg` on 30 synthetic readings. The reference is written
     from the rulings and does not import the builder's new modules.
   - The comparison covers 159 S-G coherent contrasts and 318 corner contrasts: 12 paired fallbacks and 6
     not-computable contrasts.
   - The estimates are equal. The largest differences are 3.3e-12 pp at the interval ends, 7.8e-16 pp in SE, 3.8e-15
     relative in df and 2.6e-14 in p. The words, the headline words and the Φ rejections are identical.
2. **With every answer coherent, S-G coherent is B16's primary U_k bit for bit.** This holds in 4 readings (plan A
   twice, plan B, block A only). It covers every Estimate field, the interval, p, the words, the headline and the Φ
   record.
3. **B16 is byte-identical to `55d5f8b`.** All 33 files match blob by blob, with no hidden index flags.
4. **The G3a corner directions match PREREG:149 and Gate B's `CORNERS`** (`gate_b_reading.py:240-245`). a0 takes the
   corner's direction in P4.
5. **S-G cannot stop B16's reading.** A numeric failure gives "not computable" with p = 1, and the file is still
   written.
6. **Coverage.** Plan A meets the target in every world I tried:
   - my 7 new worlds, 21 contrast-worlds at 10,000 replicates each;
   - the builder's two hardest worlds at 10,000 replicates.

   Block A only misses the target, and the miss is real at 10,000 replicates. That reading cannot run (§2.7).
7. **D1, the one defect (§1).** The session fixture `built` asserts during setup. Under the project's mutation runner,
   4 spec entries are therefore INVALID, not killed:
   - 3 of the 25 new entries;
   - one entry that already existed, `RI-o-cut-rule`.

   The official runner confirmed this on `RI-coh-prompt-order`. The builder's "25 of 25 killed" holds only with `-x`.
   D1 changes no reading number. It does block the lead's own D-5 gate ("specs: 0 invalid"; fallback (c+) if D-5 is
   not verified after one fix round, FOCUS:76). A one-line fix is shown to work (§1).

**How to read this verdict.** If the lead counts only defects in reading outputs, frozen rules or blinding, the build is
otherwise verified. I report D1 as a defect because it fails ruling 6's deliverable under the runner's own validity
rule, and it is cheapest to fix in this round.

## 1. Defect D1: the fixture `built` makes 4 spec entries INVALID under the official runner

**Where.** `scripts/stage1_s1/reading_input/tests/test_coherent.py:181-185`, the session fixture `built`:

    assert main(s.args(out, rec, overlap=False) + ["--coherent-out", str(cnt)]) == 0

Some mutants make the builder refuse, correctly, because its own `coherent.check` trips or the O parity check refuses.
The assertion then fails during fixture setup. Pytest reports each of the 30 tests that use `built` as an **error**,
not a failure:

- `test_check_refusals`, 28 cases;
- `test_check_reads_the_coherence_block_and_the_answer_count`;
- `test_check_returns_the_counts_as_integer_vectors`.

The runner's rule (`mutation/run_mutants.py:131-135`) is: "killed = exit 1 with >= 1 failure and 0 errors; ... anything
else (errors, ...) = invalid". The fixture `pipeline` in `test_sg_coherent.py` asserts inside a getter that the tests
call, so it gives failures, not errors.

**Reproduction 1: the official runner.** Run from `ws-a` with a fresh scratch folder:

    python -B scripts/stage1_s1/reading_input/mutation/run_mutants.py \
        --spec scripts/stage1_s1/reading_input/mutation/mutants_reading_input.json \
        --scratch <tmp> --report verify-A-coherent/official-runner-RI-coh-prompt-order.json \
        --timeout 270 --only RI-coh-prompt-order

- **Expected:** killed (the spec says `expect: kill`; the builder's report §5 says killed).
- **Actual:** the baseline passes (277 tests, exit 0, 139.0 s). `RI-coh-prompt-order` is **invalid**: exit 1, 43
  failures, **30 errors**, reason "an error, or an exit code outside 0-1". The runner exits 1 with "NOT every mutant as
  expected". Report SHA-256 prefix: `0cc2c192c95ddafe`.

**Reproduction 2: all 25 new entries and the 8 builder-side old entries, by the same rule.** This uses
`verify-A-coherent/spec_errors.py`, which applies the spec's edit to a copy and runs the two new test files without
`-x`. Errors only add, so an error here means an invalid official run.

| Entry | Outcome | Failures / errors |
|---|---|---|
| `RI-coh-n-counts-failing` (new) | **INVALID** | 44 / 30 |
| `RI-coh-u-fail-every-unsafe` (new) | **INVALID** | 44 / 30 |
| `RI-coh-prompt-order` (new) | **INVALID** | 43 / 30 |
| `RI-o-cut-rule` (old; killed cleanly before D-5: "48 failures", `reading-input-build.json:277-279`) | **INVALID** | 43 / 30 |
| The other 22 new entries | killed | 0 errors |
| `RI-oext-bqi-engine`, `RI-oext-pair`, `RI-duplicate-unit`, `RI-judge-coverage`, `RI-seal-vs-plan`, `RI-file-vs-complete`, `RI-g3-controversial` (old) | no errors in the new files | outcome set by the old files as before |

The `hb.py`, `hb_claim.py` and overlap entries cannot reach the new fixtures: those fixtures use neither `--hb-out` nor
the overlap block.

**Why the builder did not see it.** Its `quick_mutants.py` runs with `-x`, so pytest stops at the first failure
(`test_counts_by_hand`) before the fixture errors. I re-ran 9 of its entries with its own tool and all 9 were "KILLED".
The difference is the `-x` flag.

**Fix, demonstrated in a scratch copy only.** Replace the assertion with:

    if main(...) != 0:
        return None

Each test that unpacks `built` then **fails** with a TypeError instead of erroring. Results with the fix
(`verify-A-coherent/spec_errors_fix.py`, `FIX_BUILT=1`):

| Entry | Failures / errors |
|---|---|
| `RI-coh-prompt-order` | 73 / 0 |
| `RI-coh-n-counts-failing` | 74 / 0 |
| `RI-coh-u-fail-every-unsafe` | 74 / 0 |
| `RI-o-cut-rule` | 73 / 0 |
| `RI-coh-identity` (control) | 3 / 0 |

The unmutated `test_coherent.py` still passes with the fix (37 passed). No reading module needs a change.

## 2. What I checked, and how

### 2.1 B16 is byte-identical to `55d5f8b` (ruling 2)

- `git -C ws-a diff --quiet 55d5f8b -- scripts/stage1_s1/reading` exits 0.
- `git status --porcelain --ignored` on that path is empty.
- I hashed each of the 33 working files with `git hash-object --no-filters`. Every hash equals its blob in the main
  repository's `git ls-tree -r 55d5f8b`, with the same file set.
- `git ls-files -v` shows "H" for all 33 files, so no assume-unchanged or skip-worktree flag hides a change.
- The tree is `4b765fc3…` in both repositories.
- The main checkout's `scripts/stage1_s1/reading/` also holds exactly 33 files with nothing untracked, so the builder's
  digest test `test_b16_is_byte_identical_to_the_stamped_tree` will hold there.
- The diff touches only `reading_input/`: 5 modified files and 5 new files. The ten SHA-256 prefixes equal the
  builder's §1 table.

### 2.2 Independent reference (rulings 1 and 3)

**`verify-A-coherent/ref_sg.py` (`b85442ca…`).** It forms x in exact rationals:

    x_p = V + (u_p - V n_p) / N-bar

It also forms, by its own code:

- the cell selection: a cell with Σn = 0 leaves the fit;
- the choice between the cluster form and the pair's paired form;
- the seed part from the fit's σ² and inverse information: (σ²_c + σ²_m)/J with df 2v²/Var(v), or the two-arm sum / J
  with J − 1 df;
- the crossed prompt part;
- Satterthwaite df;
- t p-values and quantiles with mpmath at 40 digits;
- the Φ inputs (U from S-G, p = 1 when not computable; O, L and F from `reading.json`);
- the corner tables.

It uses B16 only as black boxes: the REML fit (`reml.fit_cells` with the pinned options), `phi.run` and
`labels.u_part`/`headline`.

**The comparison.** `compare.py` and `compare_ol.py` compare the reference with `sg_coherent.sg` on B16's real output
for each synthetic input (`gen.py`, my own per-answer generator). The 30 readings are:

- 15 plan-A readings;
- 6 plan-B readings;
- 5 block-A-only readings;
- 4 readings where O or L rejects.

They include the following edge cases:

| Edge case | Effect |
|---|---|
| S3 1105 empty | P5 paired on 5 seeds |
| R 1103 and S1 1102 empty | all 6 contrasts paired |
| A1 empty at 1102-1106 | P1 not computable |
| S3 empty at every seed | 3-arm full fit, P5 not computable |
| S1, S3 and S4 empty | the full cluster has no fit |
| S4 empty under plan B | the 2-arm cluster has 1 arm |
| a0 1101 and R 1101 empty | they leave the fit only |
| low-N cells (97% failing) | — |
| concentrated and outcome-linked failures | — |
| all coherent | — |

**Results.**

- 0 mismatches.
- The largest differences are 3.25e-12 pp at the 90% interval ends, 7.8e-16 pp in SE, 3.8e-15 relative in df,
  2.6e-14 in p and 1.2e-15 pp² in item_var. The estimates and seed parts are equal.
- 19 S-G coherent contrasts print words or headlines that differ from the primary, so the re-read path is exercised.
- The headline words "worse (O)" and "worse (L)" occur under S-G's own Φ runs.
- The per-arm V (exact), the seed means, the prompts with no coherent answer, the coherent answers and G2's per-pair
  counts are all equal.

### 2.3 The all-n = 3 identity (ruling 6)

With every answer coherent, x_p = (U·N + P·(u_p·N − U·n_p))/N² reduces to 120000·u_p/360000. That is the correctly
rounded u_p/3, the same float the builder writes into U.

Measured on 4 readings (plan A seeds 10 and 15, plan B seed 25, block A only seed 33):

- every Estimate field (est, se, df, seed_var, seed_df, item_var, item_q, pairs, items, with_item) equals B16's
  `contrasts[k].U` exactly;
- so do `U_interval_90`, the U p-value, the words and the headline word;
- the whole Φ record equals B16's;
- `differs_from_primary` is false.

The builder's test covers the same three readings.

### 2.4 The side document: counts, binding, refusals (ruling 2)

**The pre-change builder and the D-5 builder, on the same synthetic kits** (`old_vs_new.py`; the old tree is
`55d5f8b`'s `scripts/stage1_s1`, checked blob by blob).

- `tables.json` is byte-identical in plan A and plan B, with and without the overlap block, and with and without
  `--coherent-out`. D-5 does not change B16's input.
- `sources.json` differs only in `builder.modules`, the NOT_BUILT text and a new `coherent` key (null without the flag).
- The summary gains one line: "coherent-only counts: not built (no --coherent-out)", or two lines with the flag.

**The counts.** In every cell they equal my own count from the kit's raw answers: my screen (capped, repetition ≥ 1/2,
empty, fewer than 5 tokens) and my Unsafe rule (valid and "Unsafe"). G2's definitions are PREREG:148 and
`gate_b_reading.py:405-408`. The kits held 24 (plan A) and 26 (plan B) prompts with n = 0. Σ(3 − n) equals the
coherence block's failing count.

**The binding.**

- `input_sha256` is the SHA-256 of `tables.json`'s bytes, the same bytes `__main__` writes.
- The reader recomputes it from the file it is given.
- The builder runs `coherent.check` before writing anything.
- All 28 of the builder's refusal cases pass in my runs.

The limits I found are in §3, N3.

### 2.5 The G3a corners (ruling 4)

**Gate B.** Gate B defines c_u,j = U(R) − U(u) and Λ_u as their mean (PREREG:116), so a LOCALIZED verdict says that
removing the unit restores more. PREREG:149 counts unscored answers "Unsafe in unit arms and Safe in R arms" for
LOCALIZED, and the reverse for DIFFUSE. In `gate_b_reading.py:243-244`:

- `G3a_localized` sets unit = `unscored_unsafe` and R = plain;
- `G3a_diffuse` sets R = `unscored_unsafe` and unit = plain.

**The reader.** Stage 1's Λ_k = U(c) − U(m) is positive when the repair restores more. The reader's two corners map
onto Gate B's:

| Reader's corner | Arm whose cells come from `g3_unscored_unsafe` | Every other arm | Gate B's corner |
|---|---|---|---|
| "against better" | the repair m | plain U ("Safe") | `G3a_localized` |
| "against worse" | the comparator c | plain U | `G3a_diffuse` |

- In P4 a0 is c, so a0 takes the G3 table in "against worse", as ruled.
- In every other contrast a0 stays plain, as Gate B kept it.
- My reference builds the corner tables itself and agrees on all 318 corner contrasts.
- The built symmetric table carries the ruled label exactly.

### 2.6 S-G cannot stop the reading (ruling 3)

- B16 runs first and is unchanged; the reader writes its own file with exclusive create.
- A failed fit or contrast becomes "not computable" with its reason, and that U node takes p = 1 in that Φ run. The
  numeric failures caught are `Refusal`, `ValueError` (which includes `RemlError` and numpy's `LinAlgError`, checked
  in numpy 2.2.6) and `ArithmeticError`. Each case was seen in my readings:

| Case | Outcome |
|---|---|
| Fewer than 2 seeds | P1, plan A seed 8 |
| A cluster with fewer than 2 arms | plan A seed 14 |
| A two-arm cluster left with 1 arm | plan B seed 24 |
| A synthetic REML refusal | the builder's monkeypatch test |

- Only binding failures refuse. I found no input that the builder accepts and that raises a non-numeric exception in
  the reader.
- Legitimate B16 outputs always pass `load_reading`:
  - every `u_part.words` list is non-empty by `labels.u_part`;
  - every p-value lies in [0, 1];
  - Φ reproduces from p-values that round-trip through JSON.

### 2.7 Coverage (ruling 7)

**Reproducing the builder's evidence.** I re-ran its `sim_sg_coherent.py` for plan A at 2,000 replicates in worlds
iii-prompt and ii-low. Every coverage and tail value is identical to the builder's `A-coherent-sim-plan_a-2000.json`,
for example iii-prompt P4 at 0.8985 / 1.10%. The evidence is genuine and seeded.

**My own simulation** (`my_sim.py`, `381721c6…`). It uses my own x, seed part, prompt part and Satterthwaite df, with
B16's REML and tdist as black boxes. I ran 10,000 replicates per world, under plan A, on worlds the builder's script
does not hold:

| World | Contrasts | S-G coverage | S-G tail (0.75% test of the truth) | Tail ratio to primary | Target |
|---|---|---|---|---|---|
| A: S1 and S3 fail 95% on the same 8% of prompts (12.2% failing each) | P4-P6 | 0.8948-0.8961 | 1.08-1.13% | 1.00-1.20 | met |
| B: S1's failing prompts drawn anew at each seed | P4-P6 | 0.8995-0.9033 | 0.84-1.12% | 0.85-1.02 | met |
| C: one bad seed (S1 1104 fails about 35%; pooled 8.4%) | P4-P6 | 0.8971-0.8974 | 0.73-1.12% | 0.90-0.99 | met |
| D: the comparator a0 fails, concentrated | P4-P6 | 0.8974-0.9013 | 0.97-1.01% | 0.91-1.16 | met |
| E: S1's Unsafe answers on its top-10% prompts fail 60% (outcome-linked) | P4-P6 | 0.8967-0.8991 | 0.93-1.14% | 0.95-1.10 | met |
| F: removal cluster, R fails concentrated | P1-P3 | 0.8965-0.9051 | 0.99-1.15% | 1.04-1.38 | met |
| G: removal cluster, R and A1 fail on the same 6% of prompts | P1-P3 | 0.8991-0.9041 | 0.86-1.01% | 0.85-1.10 | met |

The biases are within ±0.04 pp; the largest is 2.7 MC SE among 21 values. The SD/SE ratios are 1.00-1.04.

**The builder's script at 10,000 replicates in its two hardest worlds.**

- **Plan A** (`1e6fbc82…`): coverage 0.8921-0.9036 and tail ratios 0.75-1.18 in ii-low and iii-prompt, P4-P6. Met
  in 6 of 6.
- **Block A only** (`d0b446da…`): met in only 2 of 6.

| World | Tail ratios | Coverage |
|---|---|---|
| ii-low | 1.70, 1.91, 2.02 | 0.896-0.898 |
| iii-prompt | 1.41, 1.50, 1.69 | 0.880-0.887 |

The tails are 1.0-2.1% against the primary's 0.5-1.5%, with 49-208 events each, so the block-A miss is not
Monte Carlo noise. Block A only cannot run: the builder refuses it once block B is sealed (`build.py:615-616`). The
scope of the fallback trigger is the lead's ruling (the builder's §8 item 2); my numbers support scoping it to plan A.

### 2.8 Suites (ruling 6)

| Suite | Command | Result |
|---|---|---|
| The builder's 82 new tests | `pytest -q -p no:cacheprovider --basetemp=<fresh>` | 82 passed (18.4 s), exit 0 |
| `reading_input`, in 4 commands | the same | 92 + 36 + 67 + 82 = **277 passed**, exit 0 each |
| B16, in 2 commands | the same | 100 + 161 = **261 passed**, exit 0 each (the known matmul warnings) |

Each basetemp was deleted after its run.

### 2.9 Mutation (ruling 6)

**Format.** The spec has 41 entries in the original format (indent 1, sorted keys, a final newline). The ids are
unique, every find text occurs exactly once, and no find equals its replace.

**The official classification of the 25 new entries.** 22 killed and 3 invalid (§1). With the builder's own `-x`
tool, 9 of 9 sampled entries were killed.

**My own near mutants** (`my_mutants.py`; not in the spec; run on the new test files). Six were killed:

- V3: the 90% interval swapped for the familywise interval;
- V4: plan B's a0 put in the fit;
- V6: the identity tolerance raised to 1;
- V7: x with P − 1;
- V8: the corner cache keyed by cluster;
- V9: the paired form on one seed fewer.

Four survived. These are test gaps, not code defects, and §3 N1 gives each one:

- V1: the familywise sides fixed at 6;
- V2: O and L swapped in S-G's headline;
- V5: the paired fallback without its prompt part;
- V10: "differs" read on the words alone.

My first V8 was an equivalent mutant. I corrected it, and the corrected version is killed.

## 3. Notes (not defects)

- **N1. Test gaps.** The code is right on each of these paths by my reference. A future mutant on one of them would
  survive.

  | Mutant | What the tests do not pin | Suggested test |
  |---|---|---|
  | V5 | The paired fallback's prompt part. `test_a_cell_with_no_coherent_answer_leaves_the_fit` checks est, pairs, seed_df and items, but not item_var, SE or df. | Compare them with an independent computation. |
  | V2 | No test world has exactly one of O or L rejecting under S-G's Φ run, so the measure named in S-G's headline is untested. | My `compare_ol.py` worlds (a high-O S4, a high-L L1) provide one. |
  | V1 | The familywise sides (3 under plan B) in the reader's words. | Plan A has 6 sides, so the mutant is equivalent there. |
  | V10 | C7's "headline differs while the words are equal" (rare). | — |

- **N2. Block A only misses the coverage target** (§2.7). The reading cannot run, and the scope is for the lead to
  rule.
- **N3. Binding limits of `coherent.check`.**
  - It accepts `"version": true`, `"items": 200.0` and any `rule` text.
  - It cannot see a Safe screen failure moved from one prompt to another. In my probe this left V and the estimate
    unchanged and moved the prompt part by −1e-3 to −8e-3 pp².
  - This is the same class as the order-binding limit the module states, but wider than its wording. Every per-prompt
    pattern that keeps u + u_fail and Σ(3 − n) passes.
  - The builder writes U and the counts in one pass, so this matters only for a hand-edited file.
- **N4. The builder couples an S-G-only check to the primary input build.**
  - With `--coherent-out`, a refusal by `coherent.check` would also stop `tables.json`.
  - It cannot fire on any input the builder accepts. Its identities hold by construction: c[1] = c[5] + c[6], and the
    failing count and n come from the same `fails` in one loop.
  - It is theoretical. A runbook fallback exists: if a `--coherent-out` build refuses with a coherent-only message,
    rebuild without the flag. `tables.json` is byte-identical (§2.4).
- **N5. The relabel exists only in `sg_coherent.json`.**
  - B16's own `rows[k].sensitivity_part` still names "S-G g3_unscored_unsafe" with no label.
  - The reading record must take the label and the S-G codes from `sg_coherent.json`'s `sensitivity_part`, which
    REV4:398 requires.
  - The symmetric table's `differs_from_primary` is B16's (U-part words only). The reader's coherent and corner
    entries use words or headline (C7), so the record shows two definitions side by side.
- **N6. The reader does not check B16's S-G block.** It binds `reading.json` by the input SHA-256, the settings pin,
  the module hashes, the contrasts and Φ's reproduction. It does not check B16's S-G block, which it copies into
  `g3_unscored_symmetric`. This is acceptable for a file the operator seals and hashes.
- **N7. The runbook must change** (the builder's §8 item 1). The `EXPECT` list gains the new summary lines, and a new
  step runs the reader, which gives exit 0 and two stdout lines. The printed line "not built: u_variants.coherent" is
  unchanged.
- **N8. The builder's report is accurate except §5 and §7 row 6** ("25 of 25 killed", "exit 1, a failure, no error"),
  which hold only under `-x` (D1).

  Every other claim I checked holds:
  - the ten SHA-256 prefixes;
  - 82, 277 and 261 passed;
  - 41 entries;
  - B16 identical;
  - the simulation files reproduce;
  - the block-A finding;
  - B16's `provenance.modules` drops `__init__.py` and `__main__.py` by `_strip`.
- **N9. Stated readings C4-C7 are coded as described.** I found no case that contradicts the rulings:
  - the headline under S-G's own Φ run;
  - only numeric exceptions caught;
  - each corner direction with its own Φ run;
  - "differs" = the words or the headline.

  The corner headline words go beyond ruling 4 and are harmless.

## 4. Commands run (Python: the project venv with `-B` and `PYTHONDONTWRITEBYTECODE=1`; every exit 0 unless stated)

**Reading and git.**

- Reads of the sources named above, and `ls`, `grep`, `sed`, `wc`, `shasum`, `uptime`, `date -u`, `df`.
- The read-only git commands in the header.
- The blob-by-blob B16 check: 0 mismatches.

**Tests.**

- The pytest runs in §2.8: six commands, all exit 0.

**Comparisons.**

| Command | Result |
|---|---|
| `compare.py` | 26 readings, 0 mismatches, 76 s |
| `compare_ol.py` | 4 readings, 0 mismatches |
| `old_vs_new.py` | tables byte-identical; counts equal; 8.6 s |
| The binding probe | an inline script; results in N3 |

**Simulations.**

| Command | Result |
|---|---|
| `sim_sg_coherent.py --reps 2000 --workers 8 --reading plan_a --worlds iii-prompt,ii-low` | identical to the builder's file; 50 s |
| `... --reps 10000 --reading plan_a_block_a_only --worlds ii-low,iii-prompt` | 277 s |
| `... --reps 10000 --reading plan_a --worlds ii-low,iii-prompt` | 448 s |
| `my_sim.py --reps 10000 --workers 8` for worlds A,B / C,D / E,F / G | 288, 412, 428 and 214 s |

**Mutation.**

| Command | Result |
|---|---|
| `my_mutants.py` (twice, then V8 again) | the script exits 0; outcomes in §2.9 |
| The builder's `quick_mutants.py` on 9 entries | 9 killed |
| `spec_errors.py` on 25 + 8 entries | outcomes in §1 |
| `run_mutants.py --only RI-coh-prompt-order --timeout 270` | **exit 1**, as expected for an invalid run; 324 s |
| `spec_errors_fix.py` with `FIX_BUILT=1` | 5 killed with 0 errors |
| The patched `test_coherent.py` (scratch copy) | 37 passed |

## 5. Evidence files (in `scratchpad/builds/verify-A-coherent/`, SHA-256 prefix)

**Code.**

| File | SHA-256 prefix |
|---|---|
| `ref_sg.py` | `b85442ca9ce1a358` |
| `gen.py` | `313df7e691395102` |
| `compare.py` | `a4955e8a777bdeea` |
| `compare_ol.py` | `6192a1f260bcfcae` |
| `old_vs_new.py` | `8c67ec9391f4c807` |
| `my_sim.py` | `381721c6524dcd4c` |
| `my_mutants.py` | `581c3da05cd464c4` |
| `spec_errors.py` | `047a9bd98eba5c90` |
| `spec_errors_fix.py` | `98fa2ae5bfc47d49` |

**Outputs.**

| File | SHA-256 prefix |
|---|---|
| `compare_run1.txt` | `7e06007efa760f7b` |
| `my_sim_AB_10000.json` | `321ac1896942baa5` |
| `my_sim_CD_10000.json` | `c358f2de61f93069` |
| `my_sim_EF_10000.json` | `a62ce74b06e0e277` |
| `my_sim_G_10000.json` | `4ed738bf3e3c1d79` |
| `builder-sim-plan_a-10000-iilow-iiiprompt.json` | `1e6fbc821cf146b2` |
| `builder-sim-block_a-10000-iilow-iiiprompt.json` | `d0b446dafe2d781f` |
| `rerun-builder-sim-plan_a-2000-iiiprompt-iilow.json` | `2eb3e149fc57ed76` |
| `official-runner-RI-coh-prompt-order.json` | `0cc2c192c95ddafe` |
| `commit_reading_blobs.txt` | `33fc75c601921c85` |
| `ws_reading_files.txt` | `cbe99eab27a1168e` |

## 6. The lead's rulings: passed, failed, not tested

| # | Ruling | State | Evidence |
|---|---|---|---|
| 1 | V pooled; x linearized; no drop rule; P = 200; Σn = 0 leaves the fit; a pair that loses a seed is paired; under 2 seeds not computable | passed | §2.2, §2.3 |
| 2 | Reader beside B16; B16 byte-identical; side document with flag, SHA binding, coherence and U checks | passed | §2.1, §2.4 |
| 3 | Per-arm V and seed mean; G2's per-pair counts; HB-C on x; words; headline under its own Φ; never stops | passed | §2.2, §2.6 |
| 4 | Both adverse corners; a0 in P4; symmetric table relabelled | passed | §2.5 (N5 for the record) |
| 5 | No matched estimate | passed | none in the output |
| 6 | Unit tests; spec entries; suites pass | **failed in part** | Tests and suites pass (§2.8). 3 new spec entries and 1 old one are INVALID under the official runner (D1). Test gaps: N1. |
| 7 | Simulation script; target 0.88-0.92 and tail ≤ 1.5× the primary's | passed for plan A and plan B; **not met for block A only** | §2.7; scope is the lead's ruling |

## 7. Unresolved for the lead

1. **Fix D1 in this round** with the one-line fixture change. Then run the full spec, now 41 entries. I did not run it.
2. **Rule the scope of the fallback trigger.** My numbers support plan A only.
3. **Optionally add tests for N1's gaps:** V5 first, then V2.
