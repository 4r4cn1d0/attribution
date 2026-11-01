# Track A-coherent: build report (post-W1 deviation D-5: S-G coherent-only U, and the adverse G3a corners)

- **Written** 2026-11-01 at 06:57 UTC (clock checked with `date -u`) by an Opus worker for the lead (GI VIII).
  **Re-checked** from 08:03 UTC by the same track's worker: the ten files' SHA-256 values, B16's byte-identity, the
  four simulation evidence hashes and the 41 spec entries' find texts (each occurs exactly once) all still hold, and
  the tests were re-run (§4, the rows marked "re-check"). No code changed in the re-check.
- **Workspace.** `scratchpad/builds/ws-a`, a detached copy of commit `55d5f8b`. Everything is uncommitted. I ran no
  git command that changes state.
- **Data rules kept.** I opened no stage-1 outcome, seal, host, judge, unit, answer, label or cache file, and nothing
  under `tmp/` or `block-a/`/`block-b/`. From the W1 manifest I read only `rules` and the entry paths. That check
  showed that no `scripts/stage1_s1` file is a manifest entry. Every test and simulation used synthetic data only. I
  ran no reading, builder, judge, seal or kit command on real data. There was no network, no install and no pod.
- **B16 is byte-identical.** `git diff --quiet 55d5f8b -- scripts/stage1_s1/reading` exited 0. B16's tree has 33
  files, digest `0866fde9…` (git tree `4b765fc3…`), and a new test pins that digest.

## 0. Result in brief

1. **The builder.** It gains `--coherent-out coherent_counts.json`. For each cell and harm prompt it writes G2's
   counts `(n, u, u_fail)`. The document is bound to `tables.json` by SHA-256. `coherent.check` checks it against the
   coherence block and the U table. Without the flag, `tables.json` is byte-identical (tested).
2. **The new reader `sg_coherent.py`**, beside B16 in `hb_claim.py`'s pattern:
   - its cell value is G2's pooled share;
   - its prompt part is the review's linearized table `x` on all 200 prompts, read by B16's own unedited functions;
   - it re-runs Φ with the primary O, L and F p-values, and prints the U-part words and the headline word;
   - it prints G2's counts, both adverse G3a corners per contrast, and the symmetric table under its new label;
   - it never stops on a statistical failure.
3. **With every answer coherent, S-G coherent equals B16's primary U_k to the last bit.** This holds for the
   estimate, SE, df, intervals, p-value, fits, words, headline and Φ record, in plan A, block A only and plan B
   (tested).
4. **Tests and suites.** 82 new tests. The reading_input suite: **277 passed** (195 before), exit 0. B16's suite:
   **261 passed**, exit 0. I added 25 mutation entries (the spec now has 41). In a quick near-mutant check the new
   tests killed **25 of 25**.
5. **Coverage simulation** (B16's real REML on the real cluster). The lead's target is met:
   - plan A, the reading that will run: 18 of 18 contrast-worlds at 2,000 replicates per world;
   - plan B: 6 of 6 at 20,000 per world.

   **Block A only: met in 8 of 18 at 2,000.** There B16's own primary form under-states its SE too. That reading
   cannot run (block B is sealed and the builder refuses it). **The lead must rule which readings the fallback
   trigger covers** (§8 item 2).

## 1. What changed (every file; SHA-256, first 16 characters)

| File | Change | SHA-256 |
|---|---|---|
| `reading_input/items.py` | `harm()` also counts per prompt the coherent answers, coherent Unsafe answers and Unsafe answers that fail the screen; it returns them as `"coherent": {pid: (n, u, u_fail)}`. Its docstring relabels `g3_unscored_unsafe` ("in every arm; not Gate B's adverse corner G3(a)"). The existing mutants' find texts are unchanged. | `70a52ca84d604b81` |
| `reading_input/coherent.py` (new) | The side document: `KIND`, `RULE`, `table()` (in the U order) and `check()` (the binding, used by the builder and by the reader) | `799025ece004177e` |
| `reading_input/build.py` | `build(..., coherent=False)` returns a 4-tuple `(doc, record, hb_doc, coh_doc)` (only `__main__` calls it). It runs `coh.check` on what it writes; `record["coherent"]` is added. The `NOT_BUILT["u_variants.coherent"]` reason now names D-5 (the key, and so the printed line, is unchanged). Docstring updated. | `e82214e718302563` |
| `reading_input/__main__.py` | `--coherent-out`: four different files, all exclusive create; `record["coherent"]["output_sha256"]`. New summary lines (§8 item 1). | `992787928667fe22` |
| `reading_input/__init__.py` | The docstring names `coherent` and `sg_coherent`, and the usage line has `--coherent-out` | `3efbc49e298a64c8` |
| `reading_input/sg_coherent.py` (new) | The reader (§2) | `a0b001f7f40c1d2f` |
| `reading_input/mutation/mutants_reading_input.json` | 25 entries added (16 → 41); same format (indent 1, sorted keys) | `b7f409d06170dd64` |
| `reading_input/tests/test_coherent.py` (new) | 37 tests: hand counts, the builder's document by hand, the flag, the record, the summary, one refusal per binding, the builder's own check, no value printed | `c0dff59f4899ca4d` |
| `reading_input/tests/test_sg_coherent.py` (new) | 45 tests (§7) | `feb77426c410c5c8` |
| `reading_input/tests/sim_sg_coherent.py` (new) | The coverage simulation (§6). pytest does not collect it; a 3-replicate smoke test runs it. | `ff7b6f4d738e8d70` |

Unchanged: all of B16 (`scripts/stage1_s1/reading/**`), `hb.py`, `hb_claim.py`, `sources.py`, the other tests, the
engine, the kit and every Gate B pinned script.

## 2. The design

**Route.** The reader sits beside B16, as `hb_claim.py` does. It imports B16's functions and never edits them:
`sensitivities.fit_clusters`, `contrast.contrast_fit` and `contrast_paired`, `reading._run_phi`, `labels.u_part`,
`labels.headline`, `reading._fit_record`, `_phi_record`, `_strip` and `schema.validate`. B16 runs first and is
unchanged; the reader runs after it.

    python -m scripts.stage1_s1.reading_input --reading plan_a ... --coherent-out <dir>/coherent_counts.json
    python -m scripts.stage1_s1.reading --input <dir>/tables.json --out <dir>/reading.json
    python -m scripts.stage1_s1.reading_input.sg_coherent --tables <dir>/tables.json \
        --counts <dir>/coherent_counts.json --reading <dir>/reading.json --out <dir>/sg_coherent.json

**The side document** (`coherent.py`). It holds per cell and prompt `n` (answers that pass the frozen screen), `u`
(those of them that are Unsafe: valid and "Unsafe", U's own rule) and `u_fail` (Unsafe answers that fail the screen),
in the U order, with no text and no prompt id. `check` refuses unless all of these hold:

- the kind, version, reading, 200 items, 3 answers and the exact key set;
- `input_sha256` equals the given `tables.json`'s SHA-256;
- the arms and seeds are exactly the design's;
- every vector is 200 integers (not booleans), with `0 ≤ u ≤ n ≤ 3` and `0 ≤ u_fail ≤ 3 − n`;
- **per prompt `u + u_fail = 3 × U share`** (the review's exact identity);
- **per cell `Σ(3 − n)` = the coherence block's failing count**, and answers = 600.

**The estimator** (the lead's ruling 1). Per cell, `V = 100·Σu/Σn` (pp), and per prompt
`x_p = V + 100·(u_p − V/100·n_p)/N̄`, where `N̄ = Σn/200`. The code forms
`x_p = (U·N + 200·(u_p·N − U·n_p)) / N²` in exact integers and divides once:

- the result is correctly rounded;
- with every `n = 3`, `x_p` is `u_p/3` to the last bit, the same float the builder writes into U;
- the prompt mean of `x` is `V` (to about 1e-14);
- a prompt with `n = 0` gets `x = V`.

A cell with `Σn = 0` has no value and leaves the table.

**HB-C on x** works as B16's S-G does (`variant_estimates`). REML runs one cluster at a time
(`fit_clusters(..., arms=<that cluster's arms with a cell>)`) with the pinned settings: the U floor, LN-35, D-4's
multi-start and the two-arm sum rule. Each contrast is read in one of three ways:

- every common seed held by both arms: `contrast_fit` on the cluster fit (paired mean, REML seed part, crossed prompt
  part of the J × 200 table, Satterthwaite df);
- a pair that lost a seed: `contrast_paired` on the seeds it holds (J − 1 df plus the prompt part; LN-12's precedent,
  B16's O comparator part);
- fewer than 2 seeds: "not computable".

The p-value and 90% interval must be finite, or the contrast is "not computable".

**Words** (the lead's ruling 3). Φ is re-run with S-G coherent's U p-values and B16's primary O, L and F p-values,
taken from `reading.json`. A "not computable" contrast takes p = 1. For each contrast the reader prints `u_part`
(B16's `labels.u_part` at δ, the 90% interval and the familywise interval) and `headline` (`labels.headline` with
**this run's** O and L rejections). It also prints a `headline_cell` with the block-A suffix, and whether the words
or the headline differ from B16's row. `sensitivity_part[P_k]` lists each S-G code that differs or is not
computable, for the reading record to copy into the row by key (REV4:398).

**G3a** (the lead's ruling 4). For each contrast `(c, m)`:

- "against better" takes `m`'s cells from `g3_unscored_unsafe` and every other arm's from plain U;
- "against worse" takes `c`'s cells instead (a0 in P4).

HB-C is refitted on that contrast's cluster; P1-P3 share R's "against worse" table, which is cached as one fit. Each
direction has its own Φ run with every contrast's own corner p-value, and the same words and headline. The built
symmetric table is printed as `g3_unscored_symmetric`, with the label **"unscored counted Unsafe in every arm (not
Gate B's adverse corner)"** and B16's words copied by key.

**Never stops.** A statistical failure inside a cluster fit or a contrast becomes "not computable" with its reason
and p = 1 in that Φ run, and the file is still written. "Statistical failure" means `Refusal`, `ValueError` (which
covers `RemlError`, numpy's `LinAlgError` and tdist's df refusals) or `ArithmeticError`. Other exception types are
treated as code faults: the command line prints only the type and exits 2. Only an input that fails its binding
refuses.

**Bindings of the reader** (exit 2, nothing written):

- `tables.json`: B16's schema (only the place of a refusal is printed); a `u_variants.coherent` share table is
  refused;
- the counts: `coherent.check`;
- `reading.json`: the kind, version and reading; the settings pin; `input_sha256` equals `tables.json`'s;
- `reading.json`'s `provenance.modules` equals `_strip(module_hashes())` of the B16 imported here (§8 item 9);
- the sealed contrasts; valid p-values, words and headline;
- Φ's rejection list reproduced exactly from the output's own p-values.

**Output** (`sg_coherent.json`, canonical JSON, exclusive create):

- `provenance`: the three input SHA-256 values, B16's pin, the reader's own module hashes, `b16_modules`, Python and
  numpy;
- `rule`: the frozen texts, tested against REV4 and PREREG when present;
- `readings`: C1-C7, the stated readings, each with its alternative;
- `model`, `primary`;
- `coherent`: `arms` (V per seed, the seed mean, the seeds with no value, N and the prompts with no coherent answer
  per seed), `fits` with D-4 start records, `fits_not_computable`, `contrasts` (G2's count per seed pair included),
  `phi` and `headline`;
- `g3a`, `g3_unscored_symmetric`, `sensitivity_part`.

stdout prints two lines: `wrote … sha256 …` and `S-G coherent headline: P1 <word>; …`, words only.

**No matched estimate** (the lead's ruling 5). None is printed.

## 3. Alternatives I rejected

- **The design's drop rule (`y = u/n` on matched prompts).** Its prompt part misses the coherent-answer mix. The
  review's 4-prompt case (an SE of 0.07 against 25 pp) is now a test through B16's own `item_part`: 625 pp², df 3.
- **Sending `x` as a `u_variants` table.** B16's schema refuses values outside [0, 1], and a share table named
  "coherent" would let B16 form the prompt mean. The reader therefore refuses such a table.
- **Filling an empty cell with 0, or with its plain U.** G2 says "has no U_coh there". A mutant that fills it with 0
  is in the spec and is killed.
- **One adverse table per direction.** None is adverse for every contrast, because S1 is the repair in P4 and the
  comparator in P5 and P6.
- **Catching every exception as "not computable".** That would hide code faults. Only numeric exception types are
  caught.
- **Pinning B16's module hashes as literals in the reader.** It would duplicate the stamp. The reader instead binds
  `reading.json` to the B16 it imports, and a test pins the whole B16 tree digest.
- **Printing the per-prompt `x` values.** They are derivable and add no information; the reader prints the counts and
  V only.

## 4. Commands run (Python: the project venv, `-B`, `PYTHONDONTWRITEBYTECODE=1`; pytest `-q -p no:cacheprovider`,
fresh `--basetemp` under `builds/tmp/`, deleted after each run)

| Command | Exit | Result |
|---|---|---|
| read-only `ls`, `cat`, `sed`, `grep`, `git log/status/show/diff/rev-parse` (main checkout and ws-a) | 0 | — |
| `python -I -B` parse of the W1 manifest (rules and entry paths only) | 0 | no `scripts/stage1_s1` entry |
| timing of B16's `fit_clusters` on synthetic tables | 0 | 0.044 s for both clusters |
| scratch `smoke.py` (synthetic world → builder → B16 → reader) | 1, then 0 | the first attempt lacked `PYTHONPATH` (ModuleNotFoundError) |
| the reader on the smoke files | 2 | it found a bug in my module-hash binding (B16's `_strip` drops `__init__.py` and `__main__.py`); fixed; then exit 0 |
| `pytest tests/test_coherent.py` | 0 | 36 passed (37 after one added case) |
| `pytest tests/test_sg_coherent.py` | 1, then 0 | 1 failed (a frozen-text needle with `**` markers); test fixed; 45 passed |
| both new files, after each edit | 0 | 82 passed (19-40 s) |
| truth quadrature against a brute-force Monte Carlo (scratch) | 0 | the coherent-minus-plain gaps agree to about 0.01-0.02 pp |
| scratch `add_mutants.py` | 0 | 25 added; every find text occurs exactly once (re-checked after the line rewrap) |
| scratch `quick_mutants.py` (two batches) | 0 | 25/25 killed |
| `sim_sg_coherent.py --reps 2000 --workers 8 --reading plan_a` | 0 | 5 min 26 s; `A-coherent-sim-plan_a-2000.json` |
| `... --reps 1000 --reading plan_b --worlds ii-low,iii-prompt,iii-answer,iii-refusal` | 0 | `A-coherent-sim-plan_b-1000.json` |
| `... --reps 20000 --workers 8 --reading plan_b` | 0 | 3 min 45 s; `A-coherent-sim-plan_b-20000.json` |
| `... --reps 2000 --workers 8 --reading plan_a_block_a_only` | 0 | 6 min 28 s; `A-coherent-sim-block_a-2000.json` |
| scratch `diag_df.py` (world i, block A only, 600 replicates) | 0 | df and SE of both forms (§6) |
| `pytest scripts/stage1_s1/reading_input/tests` (start 06:18:20 UTC) | 0 | **277 passed** in 255.5 s; basetemp 2.8 GB (my new tests add 173 MB) |
| `pytest scripts/stage1_s1/reading/tests` (B16; start 06:23:54 UTC) | 0 | **261 passed**, 51 warnings (the known spurious matmul RuntimeWarnings) |
| `git diff --quiet 55d5f8b -- scripts/stage1_s1/reading` | 0 | B16 unchanged |
| re-check, 08:0x UTC: `shasum -a 256` of the ten files in §1; `git diff --quiet 55d5f8b -- scripts/stage1_s1/reading` | 0 | every SHA-256 prefix equals §1's table; B16 unchanged |
| re-check, 08:24:33 UTC: `pytest tests/test_coherent.py tests/test_sg_coherent.py` (fresh basetemp, deleted) | 0 | **82 passed** in 29.7 s |
| re-check, 08:25:13 UTC: `pytest scripts/stage1_s1/reading_input/tests` (fresh basetemp, deleted at 08:47:52) | 0 | **277 passed**; pytest measured 106.6 s, but the wall time was 22.5 min, so the harness moved the command to the background at its 600 s limit (I did not start a background job; I waited for its exit before finishing). B16's suite was not re-run: B16 is byte-identical and its one run (above) took 20.8 min of wall time, beyond the 10-minute rule |

About the B16 suite run: pytest measured 242.7 s, but the wall time was 20 min 47 s under today's machine load. The
harness moved the command to the background at its 600 s limit. I did not start it as a background job. I waited for
its completion notice before writing this report.

Scratch tools (kept, small): `scratchpad/builds/tmp/a-smoke/{smoke.py, add_mutants.py, quick_mutants.py,
diag_df.py}`. I deleted the run data.

## 5. Mutation entries added (25; parts `items`, `coherent`, `build`, `sg_coherent`)

| Part | Ids (what each breaks) |
|---|---|
| `items` | `RI-coh-n-counts-failing` (n counts failing answers), `RI-coh-u-ignores-validity` (an invalid "Unsafe" record counts), `RI-coh-u-fail-every-unsafe` |
| `coherent` | `RI-coh-prompt-order` (reversed vectors), `RI-coh-input-sha`, `RI-coh-u-above-n`, `RI-coh-identity`, `RI-coh-failing` |
| `build` | `RI-coh-builder-check` (the builder writes unchecked counts) |
| `sg_coherent` | `RI-sg-x-prompt-mean` (y = u/n: the prompt mean of shares, the design's per-prompt quantity), `RI-sg-x-nbar-three`, `RI-sg-empty-cell-zero`, `RI-sg-lost-seed-cluster-form`, `RI-sg-one-seed`, `RI-sg-not-computable-primary-p`, `RI-sg-fit-guard`, `RI-sg-g2-both-arms`, `RI-sg-arm-prompt-mean`, `RI-sg-g3a-a0-plain`, `RI-sg-g3a-swapped`, `RI-sg-g3a-plain-table`, `RI-sg-headline-primary`, `RI-sg-phi-binding`, `RI-sg-b16-modules`, `RI-sg-share-table` |

**What I ran.** A quick near-mutant check (scratch `quick_mutants.py`). For each mutant it copies
`scripts/stage1_s1`, applies the edit, and runs only `test_coherent.py` and/or `test_sg_coherent.py` with `-x`. That
is the runner's layout, with `PYTHONPATH=<copy>:<ws>`. **All 25 were killed** (exit 1, a failure, no error).

**What I did not run.** The official `run_mutants.py`, which runs a baseline plus the whole suite per mutant. The
lead runs it. At about 4.3 min per run under today's load (2.5-3 min unloaded), the 25 new entries add about 1-1.8 h;
`--only` shards work. I listed no expected survivor.

## 6. Coverage simulation (`tests/sim_sg_coherent.py`)

**What a replicate does.** It draws the reading's full-corpus cluster: a0, S1, S3 and S4 at the design's seeds, or
S1 and S4 under plan B (the sum rule). Each cell has 200 prompts × 3 answers. The replicate reads every contrast of
the cluster twice with **the reader's own functions**, so B16's REML with D-4's multi-start is used:

- on the coherent counts (S-G coherent);
- on the plain counts (n = 3; the primary form, equal to B16's U_k as tested).

**The model.** logit = μ_a + η_p + γ_ap + s_j + e_aj:

- η ~ N(−0.2, 2.5²), γ ~ N(0, 0.3²) and s ~ N(0, 0.25²), as in the review;
- e ~ N(0, 0.15²), or 0 in "ii-low";
- μ = (a0 +0.4, S1 0, S3 −0.1, S4 +0.05), so the truths are not null.

**The worlds.** S1 is the arm whose answers fail (the repair in P4, the comparator in P5 and P6):

- (i) independent failures, 7% in every arm;
- (ii) 95% on a random 8% of prompts (and ii-low);
- (iii-prompt) 95% on its most harmful 4%;
- (iii-answer) Unsafe answers fail 25% and Safe answers 3%;
- (iii-refusal) Safe answers fail 15% and Unsafe answers 3%.

**The truths.** They are the population targets with prompts random: the mean over t of E[π] (plain), and the mean
over t of E[π(1−f1)]/E[π(1−f1)+(1−π)(1−f0)] (G2's pooled share). They come from quadrature, which I checked against a
Monte Carlo. Each replicate draws from the seed `[seed, world, replicate]`, so the results do not depend on the
number of workers.

| Run | Contrast-worlds meeting the target | S-G coherent coverage | Primary coverage | Pooled tail ratio (per contrast) |
|---|---|---|---|---|
| plan A, 2,000/world (MC SE 0.007) | **18 of 18** | 0.891-0.909 (mean 0.901) | 0.889-0.915 (mean 0.901) | 0.93 (0.61-1.35) |
| plan B, 20,000/world (MC SE 0.002) | **6 of 6** | 0.895-0.904 | 0.896-0.902 | 0.94 (0.77-1.14) |
| block A only, 2,000/world | **8 of 18** | 0.876-0.900 (mean 0.889) | 0.883-0.907 (mean 0.897) | 1.37 (0.73-3.40) |

The coherent truths move as G2 says they should. For example, iii-answer's P4 truth is +11.5 pp coherent against
+5.2 pp plain.

**Block A only (J = 3).** In my diagnostic for world i, both forms have the same df (mean about 3). Both under-state
their SE: SD/SE is 1.107 for S-G coherent and 1.094 for the primary form. Across the block-A worlds the primary
form's SD/SE is 1.06-1.13. The gap is therefore mostly B16's REML seed part on about 2 df per arm, which S-G coherent
inherits with a little more cell noise (about 12% fewer answers); the linearized prompt part does not cause it. At
2,000 replicates the tail ratios are noisy: 5-47 events each. Evidence SHA-256: plan A `a513d529…`, plan B 20k
`746b08f4…`, block A `84d05e9c…`, plan B 1k `b6da9c68…`.

**The lead's full run** (background; about 25-30 min under today's load):
`python -B scripts/stage1_s1/reading_input/tests/sim_sg_coherent.py --reps 10000 --workers 8 --reading plan_a --out <new file>`.

## 7. Acceptance criteria (the lead's rulings for this track)

| # | Criterion | State | Evidence (tests in `test_sg_coherent.py` unless named) |
|---|---|---|---|
| 1 | V pooled; x linearized; no drop; P = 200 | passed | `test_x_by_hand_in_exact_arithmetic`, `..._u_share_to_the_last_bit`, `test_x_mean_is_the_pooled_share...`, `test_the_cell_value_is_the_pooled_share` |
| 1 | All n = 3 equals B16's primary exactly | passed | `test_every_answer_coherent_gives_the_primary_exactly` [plan_a, block A only, plan_b] |
| 1 | A cell with Σn = 0 leaves the fit; a pair that loses a seed takes the paired form; fewer than 2 seeds: not computable | passed | `test_a_cell_with_no_coherent_answer_leaves_the_fit`, `test_a_pair_left_with_one_seed_...`, `test_a_cluster_left_with_one_arm_has_no_fit` |
| 2 | A reader beside B16; B16 byte-identical | passed | `test_b16_is_byte_identical_to_the_stamped_tree`; `git diff` exit 0 |
| 2 | The side document, its flag, its SHA binding, the check against coherence and U; the binding refusals | passed | `test_coherent.py` (28 refusal cases, the builder's own check, `tables.json` unchanged) |
| 3 | Per-arm V and its seed mean; G2's per-pair counts; HB-C on x; words; headline under its own Φ run | passed | `test_g2_counts_per_seed_pair_and_per_arm_by_hand`, `test_phi_is_rerun_with_the_primary_o_l_and_f` |
| 3 | Never stops; "not computable" with p = 1 | passed | `test_a_failed_fit_or_contrast_is_not_computable_and_the_file_is_written` |
| 4 | Both adverse corners, a0 in P4, the symmetric table relabelled | passed | `test_the_adverse_corners_by_hand`, `test_the_symmetric_table_is_relabelled...`, `test_without_the_g3_table...` |
| 5 | No matched estimate | passed | none is printed (code; `rule` text) |
| 6 | An independent reference | partly | numpy-only references on one plan-B reading (P6: est, SE, df, interval, p) and one plan-A reading (estimates and prompt parts). The ≥ 20-reading comparison in track E's draft (point 9) was **not done**. |
| 6 | Mutation spec entries; near mutants | passed | 25 added, 25/25 killed in the quick check; the official spec run **not run** (the lead's) |
| 6 | reading_input suite and B16 suite pass | passed | 277 and 261 passed |
| 7 | Coverage 0.88-0.92 and tail ≤ 1.5 × the primary's | plan A met, plan B met, block A only **not met** | §6 |

## 8. Open points for the lead

1. **Runbook (1d).** Step 2 adds `--coherent-out`. The builder prints either `coherent-only counts: not built (no
   --coherent-out)`, or two lines: `coherent-only counts: 50 cells x 200 prompts` and `wrote … sha256 …`. The
   strict `EXPECT` list must change. A new step after B16 runs `sg_coherent`, with exit 0 and two stdout lines.
2. **D-5's fallback trigger needs a scope ruling.** Track E's draft (`E-D5-D6.md` point 9) says "A measured coverage
   outside the band triggers the fallback", and it names no reading.
   - Plan A (the reading that runs) meets the target; so does plan B.
   - Block A only does not: 3 coverage values of 0.876-0.877 and noisy tail ratios. Its primary form is miscalibrated
     there too, and the builder refuses that reading now that block B is sealed.
   - My recommendation: scope the trigger to plan A at ≥ 10,000 replicates (§6 command), and report block A only as
     a limit.
3. **Wording mismatch with track E's draft.** The draft labels the symmetric table "unscored answers counted Unsafe in
   every arm (not Gate B's adverse corner, PREREG §3 G3(a))". The code prints the lead's ruling text, "unscored
   counted Unsafe in every arm (not Gate B's adverse corner)". Align one to the other; a test pins the code's text.
4. **Track E's "≥ 20 synthetic readings" independent check** is not in my tests (§7 row 6). The adversarial verifier
   may do it.
5. **The stated readings to confirm in D-5's record:**
   - C4: the headline under S-G's own Φ run (track E's point 6 agrees);
   - C7: "differs" means the words or the headline differ;
   - C5: only numeric exceptions are caught.

   Also: corner headline words are printed too, which goes beyond the ruling and is harmless; the record may omit
   them. And `sensitivity_part` lists not-computable codes, which the record must print.
6. **The order-binding limit.** The per-prompt identity cannot see a swap of two prompts that have the same Unsafe
   count but different `(n, u, u_fail)` splits. The builder writes U and the counts in one pass, so the order is
   right by construction, and the tests check the counts by hand from the answers.
7. **Adjacent finding (B16, not changed).** B16's `provenance.modules` omits `__init__.py` and `__main__.py`, because
   `reading._strip` drops keys that start with "_". `hb_claim`'s `b16_modules` has the same gap. The two files are
   covered only by the tree, through the stamp and the new digest test.
8. **Spec cost and disk.** 41 entries now (§5). The suite's basetemp reached 2.8 GB in my run, so each mutant run
   needs that space (the runner deletes it). B16's suite took 20.8 min of wall time under today's load.
9. **The reader binds `reading.json` to the B16 it imports** (module hashes). Run B16 and the reader from the same
   stamped tree.
10. **Merge and stamp.** The `scripts/stage1_s1` tree changes (`reading_input` only), so the second stamp must cover
    it. FOCUS needs the new hashes (§1).

## 9. Limits

- The simulation worlds are mine. They test calibration under the stated failure mechanisms, not stage 1's data. The
  plan-A run used 2,000 replicates per world, so its tails are noisy; the 10,000-replicate run is the lead's.
- `x` is first order. Its accuracy falls when a cell has very few coherent answers. An arm that passes the 10% bar
  keeps more than 90% of its answers.
- I did not run the official mutation spec or the stage1_s1 package and regression suites, and I did not rehearse
  the runbook.

## Fix round 1 (the verifier's report `builds/reports/A-coherent-verify1.md`)

- **Written** 2026-11-01 at 11:53 UTC (clock checked with `date -u`) by the track's builder. Work ran from 10:59 to
  11:53 UTC. Same workspace (`builds/ws-a`, detached at `55d5f8b`); everything is still uncommitted, and I ran no git
  command that changes state.
- **Data rules kept.** I opened no stage-1 outcome, seal, host, judge, unit, answer, label, guard-sample or cache
  file, no bank, nothing under `tmp/` or `block-a/`/`block-b/`, and not the W1 manifest. Every test, mutant run and
  check used synthetic data. There was no network, no install, no pod and no API call. No `__pycache__` or
  `.pytest_cache` folder is left in `ws-a`; every basetemp and scratch folder was deleted after its run.

### F.0 Result in brief

1. **D1 is fixed.** No fixture in the two D-5 test files can fail during setup now, so a mutant gives test failures,
   never setup errors. Under the official runner, the four entries the verifier found INVALID are now **killed with
   0 errors**: `RI-coh-prompt-order` (79 failures), `RI-coh-n-counts-failing` (80), `RI-coh-u-fail-every-unsafe` (80)
   and `RI-o-cut-rule` (205). The runner exited 0 with "every mutant as expected".
2. **N1's four test gaps are closed.** I added two tests and extended one. The verifier's own probe
   (`verify-A-coherent/my_mutants.py`) now kills **10 of its 10** near mutants, V1, V2, V5 and V10 included.
3. **N3 is tightened.** `coherent.check` now refuses `version`, `items` or `samples_per_prompt` that is not a JSON
   integer (`true`, `1.0`, `200.0`), and a `rule` text other than `coherent.RULE`. The module doc now states the full
   limit the verifier measured.
4. **The spec has 47 entries (41 before).** The six new entries cover the new tests and checks. All six are killed
   under the official runner with 0 errors.
5. **Suites.** reading_input: **284 passed** (277 before), exit 0. B16: **261 passed** (198 + 63), exit 0. B16 is
   still byte-identical to `55d5f8b`. The only code change is in `coherent.check`, which gains two refusals. A
   document the builder writes passes as before. `sg_coherent.py`, `items.py`, `build.py`, `__main__.py` and
   `__init__.py` keep their hashes, so no number or word of a reading can change. Only the provenance changes:
   `sg_coherent.json` records the new `coherent.py` hash.

### F.1 Each defect and note: fixed how, or not changed why

| Item | State | What I did, or why not |
|---|---|---|
| **D1** (the fixture `built` asserts during setup; 4 entries INVALID) | **fixed** | `built` now returns the built world, or a text that says why the build failed. It never raises: it also catches an exception during the build. Each of its three tests reads it through `need(built)`, which asserts inside the test. That gives a failure, not an error. I did not use the verifier's `return None`: it would also work, but the tests would fail with a TypeError that does not say why. |
| D1, second source (mine; the verifier did not list it) | **fixed** | The getter `pipeline` in `test_sg_coherent.py` asserted inside the tests, so it caused no errors. But after a failed build it rebuilt the world in each later test that asked for it: about 38 rebuilds per mutant, which pushes a run toward the runner's `--timeout`. A failed build is now kept. The first test raises the original exception, so its traceback shows. Each later test fails at once with `pytest.fail` and the same reason. The formerly INVALID entries now take 5-8 s on the two new files, and 41-72 s under the official runner. |
| **N1 V5** (the paired fallback's prompt part is not pinned) | **fixed** | `test_a_cell_with_no_coherent_answer_leaves_the_fit` now checks P5's paired form against `paired_reference`, a numpy-only computation from exact-fraction `x`. It checks est, seed_var, seed_df, item_var, item_q, SE and df, the 90% interval and p. It first asserts `item_var > 0`, so the check has meaning. Spec entry `RI-sg-paired-no-item-part`. |
| **N1 V2** (O and L swapped in S-G's headline) | **fixed** | New `test_the_headline_names_o_or_l_under_s_gs_own_phi_run`. In B16's plan-A output it sets P6's O p-value and P2's L p-value to 1e-12, and the other measure's p-value to 1. It recomputes the Φ rejections with B16's own `_run_phi`, so the binding still holds. Then, in S-G coherent's Φ run and in both corners' runs, O:P6 and L:P2 must reject, and L:P6 and O:P2 must not. P6's headline must name O and P2's must name L. The new direct test below covers V2 too. Spec entry `RI-sg-headline-o-l-swapped`. |
| **N1 V1** (the familywise sides fixed at 6; equivalent under plan A) | **fixed** | New `test_reread_by_hand_familywise_sides_o_or_l_and_a_headline_only_difference`. It calls `sgc.reread` under plan B with hand-made estimates. P1 has Λ̂ = 0 and an SE on the knife edge: its familywise interval lies inside ±δ at plan B's 3 sides and outside at 6. The test asserts this first. The expected words, "equivalent (familywise)", are written out by hand. Spec entry `RI-sg-familywise-sides`. |
| **N1 V10** ("differs" read on the words alone) | **fixed** | In the same test, P3's O node alone rejects. Its words equal the primary row's ("inconclusive"), but its headline is "worse (O)". So `u_part_words_differ` is false, `headline_differs` is true, and `differs_from_primary` is true (reading C7). P6's L node alone rejects: "worse (L)". Spec entry `RI-sg-differs-words-only`. |
| **N3** (`"version": true`, `"items": 200.0` and any `rule` accepted) | **fixed** | `coherent.check` refuses unless `version`, `items` and `samples_per_prompt` are JSON integers (`HEADER_INTS`, the `_int` rule the vectors already use). It also refuses unless `rule == coherent.RULE` ("state another rule than version 1's"). There are five new refusal cases: `version=True`, `items=200.0`, `samples_per_prompt=3.0`, the rule plus one space, and the rule "verifier synthetic". Spec entries `RI-coh-header-ints` and `RI-coh-rule-text`. |
| **N3** (a Safe failure moved between prompts passes) | **documented; it cannot be checked** | `tables.json` holds the Unsafe count per prompt and the failing count per cell, and nothing more. So no check against it can see where the failures fall, or how a prompt's Unsafe answers split between u and u_fail, beyond those totals and the bounds. The module doc now states this limit, with the verifier's example. Before, it named only shifted or reordered vectors. The builder writes U and the counts in one pass over the same answers, and the tests count them by hand from the answers. |
| N2 (block A only misses the coverage target) | **the lead's ruling** | No change. The verifier's 10,000-replicate numbers and mine both support scoping D-5's fallback trigger to plan A (§8 item 2). Block A only cannot run: the builder refuses it once block B is sealed. |
| N4 (`--coherent-out` couples an S-G-only check to `tables.json`) | **no change** | The check cannot fire on any input the builder accepts: its identities hold by construction (the verifier agrees). If it ever fired, that would mean a code fault in the same pass that wrote U, so stopping is the safer outcome. The fallback is to rebuild without `--coherent-out`: `tables.json` is then byte-identical (`test_tables_json_is_the_same_document_with_and_without_the_counts`; verifier §2.4). This is a runbook line for the lead. |
| N5 (the relabel exists only in `sg_coherent.json`) | **no code change possible** | B16 is frozen. The reading record must take the symmetric table's label from `sg_coherent.json`'s `g3_unscored_symmetric` and the S-G codes from its `sensitivity_part` (REV4:398). It must also say which "differs" each column uses: B16's (U-part words only) or the reader's C7 (words or headline). |
| N6 (the reader does not check B16's S-G block) | **no change** | B16's S-G block has a fixed shape. `reading.py:297-298` writes `u_part_words` and `differs_from_primary` for every contrast of a variant, and `variant_estimates` raises otherwise, so B16 refuses the whole reading. `reading.json` is already bound by the input SHA-256, the settings pin, the module hashes and Φ's reproduction. A shape check would catch only a hand edit of a file the operator seals and hashes. |
| N7 (the runbook must change) | **the lead's (1d draft)** | This round changes no stdout line of the builder or the reader. §8 item 1 still holds. |
| N8 (§5 and §7 row 6 hold only under `-x`) | **corrected here** | §0 item 4, §5 ("All 25 were killed (exit 1, a failure, no error)") and §7 row 6 were true only with `-x`. Under the runner's rule, 3 of the 25 new entries, and the old `RI-o-cut-rule`, were INVALID before this round. After it, all 31 new-code entries are killed with 0 errors (§F.4). |
| N9 (the stated readings C4-C7) | agreed | No change. |

### F.2 Changed files (SHA-256, first 16 characters)

| File | Change in this round | SHA-256 now |
|---|---|---|
| `reading_input/coherent.py` | `HEADER_INTS`; the header check requires JSON integers; the new rule-text check; the module doc states the full binding limit | `9f3010fb52ea6459` (was `799025ece004177e`) |
| `reading_input/mutation/mutants_reading_input.json` | 6 entries added (41 → 47), each beside its related entry; same format (indent 1, sorted keys, final newline); ids unique; each find text occurs exactly once | `52f231ed9c6d787f` (was `b7f409d06170dd64`) |
| `reading_input/tests/test_coherent.py` | `built` never fails during setup and `need()` reads it; 5 refusal cases | `7cb5f8fc52ed7bea` (was `c0dff59f4899ca4d`) |
| `reading_input/tests/test_sg_coherent.py` | `pipeline` keeps a failed build; `x_exact` and `paired_reference`; the V5 check; 2 new tests; module doc | `cee9f10837524111` (was `feb77426c410c5c8`) |

Unchanged since the build: `items.py` `70a52ca84d604b81`, `build.py` `e82214e718302563`, `__main__.py`
`992787928667fe22`, `__init__.py` `3efbc49e298a64c8`, `sg_coherent.py` `a0b001f7f40c1d2f`, `tests/sim_sg_coherent.py`
`ff7b6f4d738e8d70`, and all of B16. The simulation imports only `sg_coherent.py` and B16, so its evidence (§6) stands
unchanged.

### F.3 Commands run (Python: the project venv, `-B`, `PYTHONDONTWRITEBYTECODE=1`; pytest `-q -p no:cacheprovider`,
fresh `--basetemp` under `builds/tmp/`, deleted after each run)

| Command (UTC start) | Exit | Result |
|---|---|---|
| read-only `ls`, `cat`, `sed`, `grep`, `shasum`, `uptime`, `df`; `git status/log/diff/show/rev-parse` | 0 | the ten files matched §1's hashes before any edit |
| `pytest tests/test_coherent.py tests/test_sg_coherent.py` (11:08) | 0 | **89 passed** in 18.7 s (82 + 5 refusal cases + 2 tests) |
| scratch `add_mutants_fix1.py ws-a` | 0 | 47 entries; format, unique ids, each find text once |
| scratch `classify_fix1.py`: the baseline and 10 entries (11:09) | 0 | baseline pass (89 tests); the 4 formerly INVALID entries and the 6 new ones are **killed with 0 errors** |
| `classify_fix1.py`: the other 21 new-code entries, in two batches (11:12, 11:16) | 0 | **21 killed with 0 errors** |
| `classify_fix1.py`: the other 15 old entries (11:20) | 0 | **0 errors** in the new files: `RI-oext-bqi-engine` is killed there; the other 14 pass there and are killed by the old files, as before |
| `run_mutants.py --only RI-coh-prompt-order --timeout 400` (11:25) | 0 | baseline pass (284 tests, 80.2 s); **killed**, 79 failures, 0 errors, 68.5 s; "every mutant as expected" |
| `run_mutants.py --only RI-o-cut-rule,RI-coh-n-counts-failing,RI-coh-u-fail-every-unsafe` (11:28) | 0 | **3 killed** with 0 errors (205, 80 and 80 failures) |
| `run_mutants.py --only RI-coh-header-ints,RI-coh-rule-text,RI-sg-paired-no-item-part` (11:32) | 0 | **3 killed** with 0 errors |
| `run_mutants.py --only RI-sg-familywise-sides,RI-sg-headline-o-l-swapped,RI-sg-differs-words-only` (11:38) | 0 | **3 killed** with 0 errors |
| the verifier's `my_mutants.py` on V1-V10 (11:45) | 0 | **10 of 10 KILLED** (V1, V2, V5 and V10 survived before) |
| `pytest scripts/stage1_s1/reading_input/tests` (11:46) | 0 | 284 passed in 78.3 s; basetemp 2.8 GB |
| `pytest` on B16's tests, in two commands (11:48, 11:50) | 0, 0 | **198 + 63 = 261 passed** (the known matmul and Cholesky RuntimeWarnings) |
| `pytest` on the two new files, after a docstring-only edit of `test_sg_coherent.py` (11:50) | 0 | 89 passed |
| `git diff --quiet 55d5f8b -- scripts/stage1_s1/reading`; `git status --porcelain --ignored` on that path | 0 | B16 unchanged; nothing untracked or ignored |
| `pytest scripts/stage1_s1/reading_input/tests` on the final files (11:51) | 0 | **284 passed** in 78.2 s |

The four official-runner runs used the final spec (`52f231ed…`, named in each report). They ran before the
docstring-only edit of `test_sg_coherent.py`. The final file passed 89 and 284 tests afterwards.

**Evidence** (`scratchpad/builds/`, SHA-256 first 16 characters):

| File | SHA-256 |
|---|---|
| `reports/A-coherent-fix1-runner-RI-coh-prompt-order.json` | `1f65065ef6697937` |
| `reports/A-coherent-fix1-runner-formerly-invalid.json` | `7f8dfcf5f7d1b4f2` |
| `reports/A-coherent-fix1-runner-new-a.json` | `5931d457f7251377` |
| `reports/A-coherent-fix1-runner-new-b.json` | `d1f6c08f89fc5784` |
| `tmp/a-smoke/add_mutants_fix1.py` | `c65a08040930fbca` |
| `tmp/a-smoke/classify_fix1.py` | `f016a5683f6875eb` |

### F.4 Mutation: where the spec stands

- **The 31 new-code entries** (25 from the build and the 6 new ones): each is killed with 0 errors on the two D-5 test
  files without `-x`, by the runner's rule. The official runner confirmed 10 of them, the 4 formerly INVALID entries
  included.
- **The 16 old entries:** the new files add no error to any of them. Each new-file fixture now runs inside a test or
  never raises. `RI-o-cut-rule` is killed under the official runner (205 failures, 0 errors).
- **Not run: the full official spec, 47 entries** (the lead's). At today's speed, the baseline takes about 80 s and
  each mutant 40-85 s, so the spec takes about 55-70 min. Each shard (`--only`) runs its own baseline. A mutant run
  needs about 2.8 GB of basetemp, which the runner deletes. A `--timeout` of 400 s left a wide margin here. Under
  the heavy load of this morning (4.3 min per run), use the default 600 s.

### F.5 For the lead

1. **Acceptance, ruling 6:** passed except the full official spec run, which is yours (§F.4). The verifier's "failed
   in part" came from D1, which is fixed.
2. **The fallback trigger's scope (N2) is still yours to rule.** Plan A meets the target, by the verifier's numbers
   and by mine.
3. **The verifier's comparison harness needs one change before it is re-run.** `verify-A-coherent/gen.py` writes
   `"rule": "verifier synthetic"`, which `coherent.check` now refuses (a tested case). Set it to `coherent.RULE`.
4. **The reading record (N5):** take the symmetric table's label and the S-G codes from `sg_coherent.json`, and name
   each column's "differs" definition.
5. **FOCUS and the stamp:** four hashes changed (§F.2). The merge must take this round's four files, and the second
   stamp must cover them.
6. §8 items 1, 3 and 5-10 stand as written. Item 4 (the ≥ 20-reading independent check) was done by the verifier
   (30 readings, 0 mismatches).
