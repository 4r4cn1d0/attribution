# Track A-coherent: independent verification 2 (the check of fix round 1; D-5, S-G coherent-only U and the adverse G3a corners)

- **Written** 2026-11-01 at 15:13 UTC (clock checked with `date -u`) by a Fable worker acting as the adversarial
  verifier for the lead (GI VIII). Work ran from 14:06 to 15:13 UTC. This is the re-verify that R1.1 of
  `builds/lead-rulings-20261101.md` orders; the earlier second attempt never ran to a report (its scratch under
  `builds/verify-A-coherent/v2/` is reused only where I re-ran it or where its report JSON carries the final tree's
  hashes; see §7).
- **Scope.** `builds/ws-a` (detached at `55d5f8b`; `git status --porcelain` shows the same 5 modified and 5 untracked
  files as the builder reports), the builder's report with "Fix round 1" appended (`builds/reports/A-coherent-build.md`),
  the first verify (`A-coherent-verify1.md`), the D-5 record draft (`E-D5-D6.md` §1) and the lead's rulings R1.1-R1.3.
  "Verified" is read as item 9 of the D-5 record with R1.2(a) (plan-A gate), R1.2(b) (tolerances) and R1.2(c) (the
  lead's full spec run).
- **Read-only.** I edited nothing in `ws-a` or the main checkout. Git commands were read-only (`status`, `diff
  --quiet`, `diff --stat`, `log`, `ls-tree`, `ls-files`, `rev-parse`, `hash-object` without `-w`). I wrote only under
  `builds/verify-A-coherent/v2/` and this report. Every basetemp and runner scratch folder under `builds/tmp/v2-*`
  was deleted after its run; `builds/tmp/` holds only the builder's `a-smoke/` and two kit-round files that were there
  before. `ws-a` holds no `__pycache__` or `.pytest_cache` folder after my runs.
- **Data rules kept.** I opened no stage-1 outcome, seal, host, judge, unit, answer, label, guard-sample or cache file,
  no bank, no path with "plant" or "decoy", nothing under `tmp/`, `block-a/` or `block-b/`, and not the W1 manifest.
  Every test, comparison, simulation and mutant run used synthetic data (synth_kit, the first verifier's `gen.py`, the
  second attempt's `gen2.py`, the builder's seeded simulation). No network, no install, no pod, no API call. Disclosure:
  I opened `research/experiments/2026-10-27-block-b-prep/reading-input/reading-input-build.json` (the committed
  build record of the input builder, a report file; my script printed its key names only) to look for the lead's
  earlier spec outcomes; it holds no stage-1 outcome.
- **Hard-rule note (the 10-minute rule).** Every command was started in the foreground. Under today's load (the lead's
  B15 mutation run and a pytest were running: load average 5.5-6.5 on this Mac) one official-runner shard of three
  entries (§1.2, shard 2) took 11 min 20 s of wall time; the harness moved it to the background at its 600 s limit. I
  did not start it as a background job, I waited for its exit (0) before using its report, and I ran the later shards
  with two entries each (6-7 min). The two 10,000-replicate simulations took 190 s and 212 s.

## 0. Verdict: verified (no defect)

1. **Fix round 1 fixed D1 and closed V1, V2, V5 and V10.** Under the official runner on the final tree, every entry I
   ran is killed with 0 errors: my 10 entries (4 shards, §1.2) and the 5 the earlier attempt ran on the same final tree
   (its report JSONs carry the final hashes, §1.3). With the builder's 10 (run before a docstring-only edit of
   `test_sg_coherent.py`), 20 of the 47 entries are confirmed under the official runner; the formerly INVALID four
   are among them. The first verifier's four surviving near mutants are now killed by the final tests (§1.4). The lead's
   full 47-entry run is still part of "verified" (R1.2(c)); the spec's format, ids and find texts are checked (§1.5).
2. **No reading number or word changed.** `sg_coherent.py`, `items.py`, `build.py`, `__main__.py` and `__init__.py`
   hold the hashes the build report gives before the fix; only `coherent.py` (the check), the spec and the two test
   files changed. A document written as the builder writes it passes the tightened check (§2). B16 is blob-identical
   to `55d5f8b`, all 33 files (§2).
3. **The R1.2(a) gate is met for plan A.** 18 of 18 contrast-worlds in the builder's evidence meet the band and the
   tail ratio at 2,000 replicates (coverage 0.8915-0.9090; tail ratios 0.61-1.35). The four worlds the ruling sends
   to 10,000 replicates (i: P5 ratio 1.35; ii: P4 coverage 0.8915; ii-low: P6 0.9090; iii-prompt: P6 0.9075) all pass
   at 10,000: coverage 0.8921-0.9036 and tail ratios 0.75-1.18 in the first verifier's two worlds, and coverage
   0.8974-0.9004 and ratios 0.82-1.16 in the two I ran (§3). The first verifier's seven own worlds at 10,000 also pass,
   21 of 21 (coverage 0.8948-0.9051; ratios 0.85-1.38). Plan B: 6 of 6 at 20,000 (report). Block A only: 8 of 18 at
   2,000 and 2 of 6 at 10,000 (a limit; the reading cannot run).
4. **The references agree.** The first verifier's harness, re-run on the final code with the rule text set to
   `coherent.RULE`: 30 readings (26 + 4 with O or L rejecting), 0 mismatches; largest differences 3.25e-12 pp at the
   90% interval ends, 7.8e-16 pp in SE, 3.8e-15 relative in df. A second reference (exact rationals for x and the
   prompt part, mpmath at 50 digits for t): 38 readings, 0 mismatches, largest differences 1.8e-11 pp at the interval
   ends and 9.8e-15 pp in the estimate. The all-n = 3 identity holds bit for bit in 4 + 4 readings; the unequal-n hand
   cases are in the tests and both references (§4).
5. **Suites.** reading_input: 89 + 96 + 99 = **284 passed** (three commands). B16: 120 + 63 + 78 = **261 passed**
   (three commands). Exit 0 each (§5).

Minor points are in §6 as notes; none changes a reading number, a frozen rule, a ruling or the blinding.

## 1. Part (1): fix round 1 (D1; V1, V2, V5, V10; the spec)

### 1.1 D1 by reading the code

- `tests/test_coherent.py`, fixture `built`: the build runs inside `try/except Exception`; it returns the built triple
  or a text that says why there is none; the three tests that read it go through `need(built)`, which asserts inside
  the test. A mutant that makes the builder refuse now fails those 30 tests (28 parametrized refusal cases plus two)
  instead of erroring them.
- `tests/test_sg_coherent.py`, fixture `pipeline`: the build runs inside the getter, which runs inside the tests; a
  failed build is cached as a text, the first test re-raises, each later test `pytest.fail`s with the same text (no
  rebuild per test). The getter's `pytest.fail` raises an OutcomeException, so it is a failure, never an error.
- The runner's rule (`mutation/run_mutants.py`, `run_one`): killed = exit 1, failures >= 1, errors 0; the JUnit test
  count must equal the baseline's. Both new files keep their test count under a failed build (the parametrized cases
  still run), so no mutant can change the count.

### 1.2 The official runner on the final tree: 10 entries, 4 shards

Command, from `ws-a` (the runner copies `scripts/stage1_s1`, applies the edit, runs all seven test files without
`-x`, `--timeout 500`), one `--only` shard per command, scratch under `builds/tmp/v2-mutN` (deleted after each run):

    python -B scripts/stage1_s1/reading_input/mutation/run_mutants.py \
        --spec scripts/stage1_s1/reading_input/mutation/mutants_reading_input.json \
        --scratch builds/tmp/v2-mutN --report builds/verify-A-coherent/v2/official-runner-v2-shardN.json \
        --timeout 500 --only <ids>

I chose entries the builder had not run under the official runner and whose kill path is an exception, a refusal
inside a fixture, or a single assertion: the old `RI-oext-bqi-engine` (the builder refuses in every new fixture),
`RI-coh-u-ignores-validity` and `RI-coh-builder-check` (the builder's own check), the exception paths
`RI-sg-fit-guard`, `RI-sg-one-seed` and `RI-sg-lost-seed-cluster-form`, the binding `RI-sg-share-table`, the
degenerate table `RI-sg-empty-cell-zero`, the Phi override `RI-sg-not-computable-primary-p`, and `RI-coh-identity`.

| Shard (report SHA-256 prefix) | Baseline | Entry | Outcome | Failures / errors | Seconds |
|---|---|---|---|---|---|
| 1 (`7dd83a5cfa53116a`) | pass, 284 tests, 116.2 s | `RI-oext-bqi-engine` | killed | 41 / 0 | 103.3 |
| | | `RI-coh-u-ignores-validity` | killed | 1 / 0 | 133.1 |
| | | `RI-sg-fit-guard` | killed | 1 / 0 | 128.0 |
| 2 (`0f48ab0ab9a44aae`) | pass, 284 tests, 144.2 s | `RI-coh-builder-check` | killed | 1 / 0 | 160.0 |
| | | `RI-sg-lost-seed-cluster-form` | killed | 1 / 0 | 167.8 |
| | | `RI-sg-one-seed` | killed | 1 / 0 | 163.2 |
| 3 (`4c8409a1927d197a`) | pass, 284 tests, 140.5 s | `RI-sg-empty-cell-zero` | killed | 3 / 0 | 117.0 |
| | | `RI-sg-share-table` | killed | 1 / 0 | 116.7 |
| 4 (`e706c220331e0755`) | pass, 284 tests, 118.3 s | `RI-coh-identity` | killed | 3 / 0 | 115.7 |
| | | `RI-sg-not-computable-primary-p` | killed | 1 / 0 | 117.5 |

Every shard printed "every mutant as expected" and exited 0. Each report names the spec `52f231ed9c6d787f` and a
baseline tree with `coherent.py` `9f3010fb52ea6459`, `sg_coherent.py` `a0b001f7f40c1d2f`, `tests/test_coherent.py`
`7cb5f8fc52ed7bea` and `tests/test_sg_coherent.py` `cee9f10837524111`: the final files of `ws-a`.

### 1.3 Earlier official-runner evidence on the same final tree

The earlier (unfinished) second attempt left two runner reports under `verify-A-coherent/v2/` whose baseline tree
hashes equal the final files above (the same four prefixes; spec `52f231ed9c6d787f`): `official-runner-2entries.json`
(`28d11715ca9e6ea6`): `RI-o-cut-rule` killed 205 / 0, `RI-coh-u-fail-every-unsafe` killed 80 / 0;
`official-runner-fix-round-3entries.json` (`aa8cdc3824742996`): `RI-coh-prompt-order` killed 79 / 0,
`RI-coh-header-ints` killed 3 / 0, `RI-sg-differs-words-only` killed 1 / 0. The builder's four fix-round reports
(`reports/A-coherent-fix1-runner-*.json`) show the same outcomes for its 10 entries, but their baseline tree holds
`tests/test_sg_coherent.py` `ef3f8c4c1f76ff1c`, the file before its docstring-only edit (the builder says so in F.3);
the five re-runs above and my ten cover the final file.

**Standing:** 20 distinct entries confirmed under the official runner (15 on the final tree); the 4 formerly INVALID
entries (`RI-coh-prompt-order`, `RI-coh-n-counts-failing`, `RI-coh-u-fail-every-unsafe`, `RI-o-cut-rule`) are killed
with 0 errors (three of them on the final tree; `RI-coh-n-counts-failing` on the builder's tree). The other 27 entries
(14 old ones the lead ran before D-5 and 13 D-5 entries the builder classified on the two new files without `-x`) are
the lead's full run.

### 1.4 The first verifier's near mutants V1, V2, V5, V10

`verify-A-coherent/my_mutants.py ws-a <scratch> V1-fam-sides-6,V2-headline-O-L-swapped,V5-paired-no-item-part,V10-differs-words-only`
on the final tree (the probe runs `test_sg_coherent.py` with `-x`): **all four KILLED** (exit 1, one failure each).
V1, V2 and V10 fail `test_reread_by_hand_familywise_sides_o_or_l_and_a_headline_only_difference`; V5 fails
`test_a_cell_with_no_coherent_answer_leaves_the_fit` (output `v2/my_mutants_v1v2v5v10_run_v2.txt`). I read the two
new tests: the plan-B knife edge is asserted before the words (`q3 * se < delta < q6 * se`), P3's headline-only
difference is asserted through `u_part_words_differ`, `headline_differs` and `differs_from_primary`, and the V5 check
asserts `item_var > 0` before comparing est, seed_var, seed_df, item_var, item_q, SE, df, the interval and p with a
numpy-only paired form built from exact-fraction x.

### 1.5 The spec

47 entries, 47 unique ids, every `expect` is "kill", the file is `json.dumps(indent=1, sort_keys=True)` plus a final
newline, and every find text occurs exactly once in its final file with `find != replace` (my check script, inline).

## 2. Part (2): no number or word changed; B16; the tightened check

| File | SHA-256 (first 16) | Build report §1 / F.2 | State |
|---|---|---|---|
| `reading_input/sg_coherent.py` | `a0b001f7f40c1d2f` | `a0b001f7f40c1d2f` | unchanged |
| `reading_input/items.py` | `70a52ca84d604b81` | `70a52ca84d604b81` | unchanged |
| `reading_input/build.py` | `e82214e718302563` | `e82214e718302563` | unchanged |
| `reading_input/__main__.py` | `992787928667fe22` | `992787928667fe22` | unchanged |
| `reading_input/__init__.py` | `3efbc49e298a64c8` | `3efbc49e298a64c8` | unchanged |
| `reading_input/tests/sim_sg_coherent.py` | `ff7b6f4d738e8d70` | `ff7b6f4d738e8d70` | unchanged |
| `reading_input/coherent.py` | `9f3010fb52ea6459` | F.2 `9f3010fb52ea6459` | changed in the fix (the check and the module doc) |
| `reading_input/mutation/mutants_reading_input.json` | `52f231ed9c6d787f` | F.2 | 47 entries |
| `reading_input/tests/test_coherent.py` | `7cb5f8fc52ed7bea` | F.2 | fixture and 5 refusal cases |
| `reading_input/tests/test_sg_coherent.py` | `cee9f10837524111` | F.2 | fixture, 2 tests, V5 check |

- **B16.** `git -C ws-a diff --quiet 55d5f8b -- scripts/stage1_s1/reading` exits 0 before and after my runs; `git
  ls-files -v` shows "H" on all 33 files; every working file's `git hash-object --no-filters` equals its blob in
  `git ls-tree -r 55d5f8b` (33 of 33, `v2/b16_commit_blobs_v2.txt` = `v2/b16_ws_blobs_v2.txt`); the tree is
  `4b765fc3…` in `ws-a` and in the main checkout at `55d5f8b`. The main checkout's `scripts/stage1_s1/reading` and
  `reading_input` are unchanged between `55d5f8b` and its HEAD `53f746d` (`git diff --stat`, empty; §6 N3).
- **The tightened check cannot refuse a valid document.** `coherent.table` writes `version` 1, `items` `len(u_ids)`
  and `samples_per_prompt` `SAMPLES_PER_PROMPT` (a plain `int` 3 in `items.py:39`), `rule` `coherent.RULE` and exactly
  `DOC_KEYS`; after `canonical_json` and `strict_json` the three header values are Python `int` (not bool, not float),
  so `_int` accepts them and `doc.get("rule") != RULE` is false. `v2/probe_types.py` builds the document through
  `coh.table` on the first verifier's synthetic generator for plan A, plan B and block A only, round-trips it and runs
  `coh.check` against B16's validated input: passes, 50, 53 and 26 cells. The builder's own path is
  `test_counts_by_hand` (both readings) and `test_the_builder_checks_its_own_counts`, which pass (§5). The reader's
  `provenance.modules` records the new `coherent.py` hash; nothing else in the output changes.
- The diff of the five modified modules (`git -C ws-a diff`) is the build round's: `items.harm` adds the three counts
  in the same loop as U; `build()` runs `coh.check` on the document it writes; `__main__` adds the exclusive-create
  write and two summary lines; `__init__` the docstring. `sg_coherent.py`'s estimator and corner logic are the ones the
  first verifier compared (unchanged hash), and I re-read them against B16: `estimate()` calls `con.contrast_fit(table,
  fits[cluster], c, m, common, scale, True, name, form)` exactly as `sensitivities.variant_estimates` does for a
  variant; `reread()` overrides the U p-values only and keeps the primary O, L and F, as B16's `record()` does
  (`reading.py:287-291`); the headline call order `(u, O rejected, L rejected)` is B16's (`reading.py:242`).

## 3. Part (3): the coverage gate (R1.2(a)), plan A

Evidence files: the builder's `reports/A-coherent-sim-plan_a-2000.json` (`a513d5298bc09070`); the first verifier's
`verify-A-coherent/builder-sim-plan_a-10000-iilow-iiiprompt.json` (`1e6fbc821cf146b2`) and `my_sim_{AB,CD,EF,G}_10000.json`
(`321ac1896942baa5`, `c358f2de61f93069`, `a62ce74b06e0e277`, `4ed738bf3e3c1d79`); mine,
`v2/builder-sim-plan_a-10000-world-i.json` (`888b29ca53a76938`) and `-world-ii.json` (`b8d1ab379485c83c`), run with

    python -B scripts/stage1_s1/reading_input/tests/sim_sg_coherent.py --reps 10000 --workers 8 --reading plan_a --worlds i --out ...
    (and --worlds ii); 189.7 s and 212.1 s; exit 0 each.

The table (`v2/gate_table.py` over the files; full print in `v2/gate_table_plan_a.txt`): coverage of S-G coherent's 90%
interval, its MC SE, the primary form's coverage, both 0.75% tails and their ratio; band 0.88-0.92; ratio <= 1.5; the
10,000 rule = at 2,000 replicates a coverage within 0.0134 of a band edge or a ratio above 1.3.

**The builder's six worlds at 2,000 replicates (18 contrast-worlds): 18 meet both.**

| World | P4 cov / ratio | P5 cov / ratio | P6 cov / ratio | 10,000 needed |
|---|---|---|---|---|
| i | 0.9015 / 1.27 | 0.9050 / **1.35** | 0.9020 / 0.90 | yes (P5 ratio) |
| ii | **0.8915** / 0.88 | 0.8960 / 1.00 | 0.9040 / 0.95 | yes (P4 within 0.0134 of 0.88) |
| ii-low | 0.9000 / 0.87 | 0.9065 / 0.73 | **0.9090** / 0.94 | yes (P6 within 0.0134 of 0.92) |
| iii-answer | 0.9035 / 0.90 | 0.8975 / 0.65 | 0.8945 / 0.62 | no |
| iii-prompt | 0.8985 / 1.29 | 0.8975 / 0.61 | **0.9075** / 0.82 | yes (P6 within 0.0134 of 0.92) |
| iii-refusal | 0.9050 / 1.10 | 0.9015 / 1.20 | 0.9025 / 0.88 | no |

**The four worlds at 10,000 replicates (12 contrast-worlds): 12 meet both** (MC SE 0.0030-0.0031).

| World (source) | P4 cov / tail / ratio | P5 cov / tail / ratio | P6 cov / tail / ratio |
|---|---|---|---|
| i (mine) | 0.8998 / 0.0092 / 0.95 | 0.9004 / 0.0086 / 1.13 | 0.8974 / 0.0093 / 0.82 |
| ii (mine) | 0.8984 / 0.0084 / 0.83 | 0.8982 / 0.0118 / 1.16 | 0.8982 / 0.0106 / 0.95 |
| ii-low (first verifier) | 0.8992 / 0.0075 / 0.89 | 0.9032 / 0.0079 / 1.07 | 0.9036 / 0.0070 / 0.99 |
| iii-prompt (first verifier) | 0.8943 / 0.0116 / 1.18 | 0.8921 / 0.0085 / 0.75 | 0.8954 / 0.0113 / 1.04 |

In my two worlds the tails hold 84-118 events each, SD/SE is 1.016-1.042 and the biases are within +-0.03 pp. The
2,000-replicate flags were tail noise (i P5: 23 against 17 events) and a 1.7-SE coverage dip (ii P4).

**The first verifier's seven worlds at 10,000 (21 contrast-worlds): 21 meet both**: coverage 0.8948-0.9051, ratios
0.85-1.38 (the 1.38 is world F's P3, already at 10,000; it passes the 1.5 bound). Worlds A-E read P4-P6 and F-G the
removal cluster's P1-P3.

**Gate: met.** 51 of 51 plan-A contrast-worlds in the builder's and the first verifier's evidence (18 at 2,000, 33 at
10,000) meet the band and the tail ratio, and every world the 10,000 rule names has a passing 10,000-replicate result.

**Plan B (checked and reported, not a trigger).** `reports/A-coherent-sim-plan_b-20000.json`: 6 of 6 worlds at 20,000
replicates; coverage 0.8953-0.9038, tail ratios 0.77-1.14.

**Block A only (a limit, not a trigger).** `reports/A-coherent-sim-block_a-2000.json`: 8 of 18 at 2,000 (coverage
0.8760-0.9000, ratios 0.73-3.40). The first verifier's 10,000-replicate run (`builder-sim-block_a-10000-iilow-iiiprompt.json`):
2 of 6; ii-low's ratios 1.70, 1.91, 2.02 at coverage 0.8958-0.8980; iii-prompt's coverage 0.8811, 0.8871, 0.8796
with ratios 1.41, 1.50, 1.69. That reading cannot run: `build.py` refuses it with block B sealed (the builder cites
:606-607 in the ruling, :615-616 in the first verify; the refusal text is in `build()`), and B16's own primary form is
outside the band there too (0.8876-0.8933 at 10,000 in iii-prompt).

Not counted: the earlier attempt's own nine plan-A worlds at 8,000 replicates (`v2/sim2_planA_*.json`, all contrasts
meeting both by their JSON) and two plan-B worlds at 4,000; I did not re-run or audit `sim2.py`, so they are
supplementary only.

## 4. Part (4): tolerances (R1.2(b)) and the references

- **The first verifier's harness on the final code.** `verify-A-coherent/{gen,ref_sg,compare,compare_ol}.py` copied to
  `v2/cmp1/`; `gen.py`'s `"rule": "verifier synthetic"` replaced by `coherent.RULE` (the only edit; `v2/cmp1/gen.py`
  `0b3825f1eb2c786e`, the other three files unchanged, `b85442ca…`, `a4955e8a…`, `6192a1f2…`). `compare.py`: 26
  readings (15 plan A, 6 plan B, 5 block A only; 138 S-G coherent contrasts, 6 not computable, 12 paired, 19 with
  differing words or headline; 4 all-coherent identity readings), **0 mismatches**; largest differences est 0, SE
  7.77e-16 pp, df 3.77e-15 relative, item_var 1.22e-15 pp^2, interval ends 3.25e-12 pp, p 2.56e-14
  (`v2/cmp1/compare_run_v2.txt`). `compare_ol.py`: 4 readings with O or L rejecting, 0 mismatches; headline words
  "worse (O)" and "worse (L)" occur under S-G's own Phi runs (`v2/cmp1/compare_ol_run_v2.txt`). The script returns 1
  on any mismatch and printed "mismatches: 0" (my shell pipe did not capture the code).
- **A second reference** (`v2/ref2.py`, written by the earlier attempt from the rulings; it imports nothing from
  `reading_input`; x and the crossed prompt part in exact `Fraction`s, Satterthwaite df and t by mpmath at 50 digits,
  the seed part from the fit's sigma^2 and inverse information, the two-arm sum recomputed and asserted equal to the
  fit's, its own cell selection, form choice and corner tables, G2's counts and the per-arm values; B16's REML, Phi
  graph and label functions as black boxes). I read it before running it. `v2/compare2.py --out
  v2/compare2_run_v2.json`: **38 readings** (24 plan A, 8 plan B, 6 block A only; 590 computable and 22 not-computable
  contrasts over S-G coherent and both corners, 244 differing labels, forms cluster / two-arm / paired), **0
  mismatches**; largest differences est 9.8e-15 pp, SE 8.0e-15 pp, df 3.5e-15 relative, seed_var 2.3e-13 pp^2,
  interval ends 1.8e-11 pp, p 2.2e-14; the symmetric table's label and B16-copied words, `sensitivity_part`'s codes
  and `arm_from_g3` agree; identity readings 4 of 4. Its earlier run (`compare2_run1.json`, 17:39 local) gives the same
  numbers.
- **Tolerance reading.** Estimates agree far inside 1e-9 pp. Neither reference fits REML on its own (both call
  `reml.fit_cells` with the pinned options, as the ruling's "as B16 computes U" allows), so the 1e-6 relative clause
  for SE and df is not exercised; SE and df agree to about 1e-14 because the seed part is re-derived from the fit's
  sigma^2 and information and the prompt part and df are independent. REML itself is B16's frozen code (its suite,
  §5). This is the same limit the first verify had.
- **All n = 3 equals the primary U_k.** In 8 identity readings (4 per harness: plan A twice, plan B, block A only),
  every Estimate field, the 90% interval, the p-value, the words, the headline, the Phi record and the fit sigma^2
  equal B16's primary bit for bit. By construction: with every n_p = 3, x_p = (U N + 200 (3 u_p N - 3 U)) / N^2 with
  N = 600 reduces to u_p / 3 correctly rounded, the float the builder writes into U.
- **The unequal-n hand case.** `test_x_by_hand_in_exact_arithmetic` (n = [3, 2, 0, 1, 3], u = [2, 1, 0, 1, 0]; x
  against `Fraction` arithmetic to the last bit; prompt mean = V = 4/9; x = V on the empty prompt; the prompt mean
  of shares differs); `test_the_reviews_hand_case_through_b16s_item_part` (625 pp^2, SE sqrt(625.005), df 3, versus the
  drop rule's 0); `test_plan_b_p6_against_an_independent_reference` and `paired_reference` (exact-fraction x,
  numpy-only prompt part, seed part, df, interval and p at rel 1e-9); and both references above, whose x is exact. A
  wrong scale of V would fail all of these (x is formed as a share and B16 scales by 100 in `cell_value`).

## 5. Part (5): the suites on `ws-a`

Python `-B` with `PYTHONDONTWRITEBYTECODE=1`; pytest `-q -p no:cacheprovider --basetemp=<fresh builds/tmp/v2-bt-*>`;
each basetemp deleted after its run.

| Suite | Command | Result | Wall |
|---|---|---|---|
| reading_input, the two D-5 files | `test_coherent.py test_sg_coherent.py` | **89 passed**, exit 0 | 35 s (basetemp 173 MB) |
| reading_input, a | `test_builder.py test_items.py test_oext_settings.py` | **96 passed**, exit 0 | 74 s (1.8 GB) |
| reading_input, b | `test_hb.py test_hb_claim.py` | **99 passed**, exit 0 | 53 s (875 MB) |
| B16, a | `test_fixes.py test_overlap.py` | **120 passed**, 18 warnings, exit 0 | 155 s |
| B16, b | `test_reading.py test_sensitivities.py test_contrast.py` | **63 passed**, exit 0 | 23 s |
| B16, c | `test_reml.py test_reml_multistart.py test_phi.py test_labels.py test_settings_and_tdist.py` | **78 passed**, 33 warnings, exit 0 | 17 s |

Totals: reading_input **284 passed** (the builder's F.3 count), B16 **261 passed** (the known matmul and Cholesky
RuntimeWarnings). Outputs in `v2/suite-*.txt`.

## 6. Notes (not defects)

- **N1. An absurd integer in a hand-edited counts file refuses with the wrong exception type.** `coh.check` accepts
  `10**20` as a Python int (`_int`) and `np.array(v, dtype=np.int64)` then raises `OverflowError`, not a `Refusal`.
  Reproduction (`v2/probe2.py`, probe "a count of 10**20"): set `cells.S1.1102.n[5] = 10**20` in a valid counts
  document, call `coherent.check(doc, inp, sha)`; expected a `Refusal` naming the vector; actual `OverflowError:
  Python int too large to convert to C long`. Effect on the reader: `main()` catches it as an unexpected error,
  prints "REFUSED: an unexpected OverflowError (its message is withheld)" and exits 2 with nothing written, so the
  reading is still refused and never stops the script (D-5 item 8). The builder cannot write such a count (0-3 by
  construction), so no reading value is affected. A one-line guard (`0 <= x <= 3` before the array) would make it a
  named refusal; not needed for "verified".
- **N2. The symmetric table's label text in the record draft.** `E-D5-D6.md` §1 item 7 writes "unscored answers
  counted Unsafe in every arm (not Gate B's adverse corner, PREREG §3 G3(a))"; the code prints and a test pins
  "unscored counted Unsafe in every arm (not Gate B's adverse corner)" (`sgc.SYMMETRIC_LABEL`). The builder's §8 item 3
  and the first verify's N5 raised it; the lead's rulings do not settle the wording. The record (track E) should take
  the code's text, since the test pins it and B16 is frozen.
- **N3. The main checkout moved.** Since the task text was written, main's HEAD is `53f746d` (D-6 and kit round 34
  merged: `scripts/stage1_s1/overlap_*`, `settings/overlap_strata.json`, B14 tests, the runkit; 19 files). Nothing
  under `scripts/stage1_s1/reading_input` or `reading` changed, so A's 10 files merge cleanly; the reading_input suite
  should be re-run once after the merge (its synthetic kit calls B14's own `overlap_strata` functions, whose
  settings pin changed under D-6), as R5.5 already orders for D2's suite.
- **N4. The binding limit of `coherent.check`, measured.** A swap of two prompts of S1 1104 with equal Unsafe counts
  but other (n, u, u_fail) splits passes the check (the module doc now states this): est unchanged (1.8e-15 pp),
  item_var moved 1.6e-3 pp^2, words unchanged (`v2/probe2_run_v2.txt`). Only a hand-edited file can do this.
- **N5. Robustness probes passed** (`v2/probe2.py`, 24 of 25; the one failure is N1): a forged `input_sha256` on
  another world's counts is refused by the per-prompt identity; `-0.0`, a string `items`, a kind with a trailing space,
  a list for `cells`, a 201-vector, a seed key with a space, reversed and swapped cells, `u` moved to `u_fail` on a
  full prompt: each refused with the named check; a counts file with a repeated JSON key and B16's output of another
  world refuse at the command line (exit 2, nothing written); every cell empty, the full cluster empty but a0, one
  coherent answer per S1 cell, two per A1 cell, and S1 and S4 at 99% failing under plan B never stop the reader (every
  contrast computable or "not computable" with p = 1; the output is strict canonical JSON).
- **N6. Not re-run.** The earlier attempt's `near_mutants2.py` (seven near mutants outside the spec), `old_new2.py`
  (the 55d5f8b builder against the D-5 builder; the first verify's `old_vs_new.py` covered it and the fix changed no
  builder module) and its own simulation worlds (§3). The official spec's other 27 entries are the lead's run.
- **N7. The builder's report is accurate after the fix round** as far as I checked: F.0-F.5's hashes, counts (89,
  284, 261), the 47 entries, the ten official-runner outcomes, B16's identity and "10 of 10" near mutants all hold.
  Its one remaining inaccuracy is small: F.3's runner reports name the pre-docstring `test_sg_coherent.py`
  (`ef3f8c4c…`), which F.3 discloses.

## 7. Commands run (every exit 0 unless stated)

- Reads: `cat`, `sed`, `grep`, `ls`, `wc`, `shasum`, `find`, `du`, `uptime`, `ps`, `date -u`; the read-only git
  commands in the header.
- `git -C ws-a diff --stat`, `diff`, `status --porcelain`, `diff --quiet 55d5f8b -- scripts/stage1_s1/reading` (0,
  twice), `ls-files -v`, `ls-tree -r 55d5f8b`, `hash-object --no-filters` x 33, `rev-parse`; `git -C <main> diff
  --stat 55d5f8b HEAD -- scripts/ experiments/ runkit/` and `-- scripts/stage1_s1/reading_input scripts/stage1_s1/reading`.
- `python -B -c` scripts: the spec listing; the runner-report summaries; the spec format and find-text check; the
  simulation-file inspections.
- `v2/probe_types.py` (0); `v2/gate_table.py` (1 at first: a missing `reading` key in the first verifier's files,
  fixed; then 0); `v2/probe2.py` (1: N1).
- `run_mutants.py --only ...` four shards (0, 0, 0, 0; §1.2; shard 2 backgrounded by the harness at 600 s, header).
- `sim_sg_coherent.py --reps 10000 --workers 8 --reading plan_a --worlds i` (0, 190 s) and `--worlds ii` (0, 212 s).
- `v2/cmp1/compare.py` (0 mismatches), `v2/cmp1/compare_ol.py` (0 mismatches), `v2/compare2.py --out ...` (0
  mismatches); pytest x 6 (§5); `my_mutants.py ... V1,V2,V5,V10` (4 killed).
- Scratch deleted: `builds/tmp/v2-mut{1,2,3,4}`, `v2-bt-*`, `v2-probe2`, `v2-mym`.

## 8. Evidence files (`builds/verify-A-coherent/v2/`, SHA-256 first 16)

| File | SHA-256 | What |
|---|---|---|
| `official-runner-v2-shard1.json` | `7dd83a5cfa53116a` | §1.2 |
| `official-runner-v2-shard2.json` | `0f48ab0ab9a44aae` | §1.2 |
| `official-runner-v2-shard3.json` | `4c8409a1927d197a` | §1.2 |
| `official-runner-v2-shard4.json` | `e706c220331e0755` | §1.2 |
| `official-runner-2entries.json`, `official-runner-fix-round-3entries.json` | `28d11715ca9e6ea6`, `aa8cdc3824742996` | §1.3 (earlier attempt, final tree) |
| `my_mutants_v1v2v5v10_run_v2.txt` | — | §1.4 |
| `b16_commit_blobs_v2.txt`, `b16_ws_blobs_v2.txt` | — | §2 (identical) |
| `probe_types.py` | `e2c58ea82806cf39` | §2 |
| `builder-sim-plan_a-10000-world-i.json`, `-world-ii.json` | `888b29ca53a76938`, `b8d1ab379485c83c` | §3 |
| `gate_table.py`, `gate_table_plan_a.txt` | `a3af023e3d33dcf6`, `566ccce0d353f5c2` | §3 |
| `cmp1/gen.py` (patched), `cmp1/compare_run_v2.txt`, `cmp1/compare_ol_run_v2.txt` | `0b3825f1eb2c786e`, `35dd83508146d5cc`, `b36f19cbd31e0591` | §4 |
| `ref2.py`, `gen2.py`, `compare2.py`, `compare2_run_v2.json` | `11b72e21082e6db2`, `832197990038f6b7`, `38243f6ae4e270cd`, `4a315ebb79605815` | §4 |
| `probe2.py`, `probe2_run_v2.txt` | `df59af16fa6b993b`, `33c81df0216e7912` | §6 |
| `suite-reading_input-{a,b}.txt`, `suite-b16-{a,b,c}.txt` | `8cafee84a560dcfc`, `502a77114b28a97c`, `f3888f644a0aec53`, `d8e28adfa54e99ca`, `3b17e6a36607214c` | §5 |

## 9. Item 9 of the D-5 record, as ruled: passed, failed, not tested

| Requirement | State | Evidence |
|---|---|---|
| The builder suite and the reader's suite pass; B16's suite, unchanged, passes | passed | §5 (284; 261); §2 (B16 blob-identical) |
| The specs kill every mutant except listed survivors, with 0 invalid | passed on 20 entries; the full 47-entry run is the lead's (R1.2(c)) | §1.2-1.3; no expected survivor is listed |
| An independent reference agrees to 1e-9 on hand cases and >= 20 synthetic readings (plan A, plan B, block A only) | passed | §4: 30 + 38 readings, 0 mismatches, largest 1.8e-11 pp |
| Where the reference fits REML on its own, SE and df at 1e-6 relative | not exercised (neither reference fits REML itself; SE and df agree to about 1e-14 with B16's REML as a black box) | §4 |
| A hand case with unequal n against an exact-fraction reference | passed | §4 |
| The all-n = 3 case equals the primary U_k exactly | passed | §4 (8 readings bit for bit) |
| Coverage within 0.88-0.92 and tail within 1.5x in the simulated worlds, scope plan A, 2,000 and 10,000 as R1.2(a) | **passed: 51 of 51; the four 10,000-rule worlds pass at 10,000** | §3 |
| Plan B checked and reported; block A only reported as a limit | done | §3 |
| No number or word of a reading changed in the fix round | passed | §2 |

## 10. For the lead

1. The re-verify verdict is **verified**; the pre-set fallback (c+) is not triggered. What remains is yours by the
   rulings: the full 47-entry spec run (0 invalid; §1.3 says which 27 are unconfirmed under the official runner), and
   the merge onto main at `53f746d` with one re-run of the reading_input suite after it (N3).
2. Align the record's label text with the code (N2) when track E's fix round 2 runs.
3. Optional, not needed for "verified": the one-line guard of N1.
