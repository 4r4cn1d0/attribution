# R1 Track S (SR-2 statistics): builder report

**Follow-up 2026-11-08 17:52-18:28 UTC: see the last section, "Follow-up"; its hashes, counts and runtimes supersede every earlier one (the fix round's included).** **Revised 2026-11-08 15:42 UTC for GXB's second set (S-1, S-3, S-6, S-7, O14): see the last section, "Second set". Its hashes, counts and mutant results supersede the ones in the sections above; where the two differ, the last section holds.**

Started 2026-11-08 14:44 UTC, finished 15:18 UTC (`date -u`, both). WS = B/ws-s (detached worktree of MAIN at 3481d85).
Scratch: R/r1-s-scratch/. Tags: M measured (the command named), R read (path:line), E estimate (basis), I inference.

## Status

**DONE.** Both scripts, the settings file, both test files, a mutation spec and its runner are built in WS as new
files. No existing file changed (M: `git status --porcelain` lists only the 7 new files; `git diff --stat` is empty).
The scale78b suite passes before (208 passed, 57 skipped) and after (256 passed, 57 skipped) (M). 46 mutants: 46
killed, 0 survived, 0 invalid, in three shards (M). No real unit, outcome, judge file or answer was read; every unit in
the tests is synthetic. The simulation ran only on smoke grids and on one timing copy of the settings (below); no
result of it is reported.

## Files created (SHA-256, M: `shasum -a 256` in WS at 15:18 UTC)

| File (in WS) | SHA-256 |
|---|---|
| `scripts/scale78b/blinded_sigma.py` (337 lines) | `41e4d068d4850832e79cfd321151f13b8248fad268b402773d6d7988680af890` |
| `scripts/scale78b/sr2_simulation.py` (607 lines) | `a4b7d401828978bdde4179baaddbbad57db314d14e5552a41ab878d90e2a3683` |
| `scripts/scale78b/settings/sr2_simulation.json` | `ef584fd57cfc1871c182a317691530544dd23d2a79e82c81620dba51b6724c48` |
| `scripts/scale78b/tests/test_blinded_sigma.py` (21 tests) | `3b0e56d70a9e99cfd906c071638eaf4b38094b8532ff14c29926ccaa1f1f3575` |
| `scripts/scale78b/tests/test_sr2_simulation.py` (18 defs, 27 tests) | `12ca2c20b30b43c0b5ecf3873e611b1da7d1bc47e526c0def0e1c8da9bb54a4f` |
| `scripts/scale78b/tests/run_mutants_sr2.py` | `50594102f50a22f04554681c4bac6b623b09470af2572c2464289ed28c2da13f` |
| `scripts/scale78b/tests/mutation_spec_sr2.json` (46 mutants) | `3b45fbda5d1a73e967f50d50a5b76ee08abb2f04264aad43691d8759eff81746` |

Scratch (R/r1-s-scratch/): `make_spec.py` (writes the mutation spec and checks each find text occurs once), `prof.py`
(the REML timing probe), `smoke.json` / `smoke-out.json` (a 400-replicate smoke grid, not a result), `mut-shard1.json`,
`mut-shard2.json`, `mut-shard3.json` (the runner's reports). The runner's copied trees (`mut-1..3/`) were deleted.
No file was copied from MAIN's tmp/.

## What each item does and where

### Item 9 (and item 8's script half): `blinded_sigma.py`

- **CLI** `python3 -I -B scripts/scale78b/blinded_sigma.py --inputs INPUTS.json --inputs-sha256 HEX [--out OUT.json]`
  (R: blinded_sigma.py:315). Prints exactly `{df, inputs_sha256, kind, sigma_A_pp, version}` in canonical JSON (GB's
  form) to stdout and, with --out, the same bytes, written once. `render` refuses any other key set (:309).
- **The estimate** (:149 `cluster_rss_df`, :176 `pooled_sigma`): per family and cluster the additive arm + seed model
  is fitted exactly in rationals (Gram-Schmidt on the seed and arm indicators); RSS and df = n - rank. σ̂_A =
  √2 × √(Σ RSS / Σ df) over clusters and families. A cluster with 0 df refuses (its label only). Lone cells (R at 1101
  and 1105, a0 at 1101) are fitted exactly by their seed effect: no df, no RSS (M: test).
- **The design** (:109 `design_cells`; P2 §2.2, §10.2, DESO3 V2): `full` = removal R@1101-1105, A1/L1/H1@1102-1104;
  full-corpus a0@1101-1104, S1/S3/S4@1102-1104: 6 + 6 = 12 df per family, 24 under [B]. `anchor_stopped` = removal
  R@1101-1105, H1@1102-1104 (2 df); full-corpus a0@1101-1104, S1/S4@1102-1104 (4 df): 6 df; 18 df under [B] with one
  family stopped (M: tests). [B] reads both families, [C] OLMo-2-7B alone (`OPTIONS`, :64). The cells given must equal
  the design's, minus an optional `not_run` list of block-A cells (not reused cells).
- **What is read** (:211 `family_cells`, :272 `read`): the inputs file by path and its pinned SHA-256
  (`--inputs-sha256`); `noise_reading.py` loaded by path and pinned at `94b679ff…` (:56, :91; its own frozen-reader pins
  then load gate_b_reading); every cell through `noise_reading.read_unit` by path and COMPLETE.json key, with the
  engine identity of its role (`reused` for a0 and R at 1101-1103, `block_a` otherwise); a method cell's edit
  (`edits` map, arm `edit-<SHA-256>`) checked by `method_edit_matches` (:132: safety-selection edit of the family's
  manifest, "remove" for A1/L1/H1, "add" for S1/S3/S4, not an R draw), then read by `read_unit` with its R-draw check
  replaced for that call only and restored in `finally` (:192). One COMPLETE.json SHA-256 is never read twice (across
  families too); two method arms never share an edit. Every unit is checked before any U is read. U = the frozen Gate
  B reader's plain U (`GB.arm_from_unit`, through noise_reading's import, Gate A's frozen bars), ×100 pp.
- **Blinding** (:315 `main`): a refusal names cells, keys and hashes only; any non-SystemExit exception is reported as
  "blinded_sigma: unexpected error (<type>); nothing written" without its text.

### P2 §10.3 (DES K6, DESO3 V2): `sr2_simulation.py` and its settings

- **CLI** `--settings PATH --option B|C --design full|reduced [--stopped F[,F]] [--sigma I,J] [--out OUT]`, and
  `--merge SHARD... [--out OUT]` (R: sr2_simulation.py:576).
- **Model** (module doc; :386 `cell_sd`): null cells, σ_e = σ_pair / √2; scenario "arm x seed" adds an independent term
  of SD ρσ_e to every method-arm cell (ρ = 1 in the settings), none to a0 and R.
- **Chain** (:414 `run_chunk`): N's σ̂_pool² (:391; both families, 1101-1103, 4 df, no σ_eval floor) and its plan are
  printed; σ̂_A² (:401) = blinded_sigma's estimate on its design (parity M: test); plan by P1 §6.1 with the noise
  reader's review ceiling (:314; equality with `noise_reading.seed_rule` on boundary values M: test); per family the
  claim test (:341): HB-C REML per cluster, vectorized over replicates (:233 `_fit`, :286 `reml_batch`: B16's
  `_fit_cells` and D-4's `_multi_start`, matched to B16's `fit_cells` M: tests, including a replicate where the
  multi-start moves the maximum), the two-arm sum rule, the paired mean on the common seeds, the seed part's
  Satterthwaite df, B16's `tdist` two-sided p (B16's `contrast_fit` parity M: test), Holm at 5% (:325) over the plan's
  primary contrasts (A: P1-P6 at 6 seeds; B9: P1, P3, P6 at 9; H (b): at 12; a0 outside the fit under B9 and H, B16's
  `plan_b` form; a stopped family drops P1, P2, P5).
- **Printed** per σ and scenario: plan shares by σ̂_A and by N; per family each contrast's tested count, unadjusted
  size, Holm rate; the familywise rate; power and P(better) at 8, 10, 12 pp (Holm rejects contrast k with a positive
  estimate; better also needs ≥ SESOI); non-converged fits; refused contrasts. Summary: the largest familywise rate
  (σ, scenario, family), its Monte Carlo SE, the settings' threshold "0.06", the mechanical comparison flag, and the
  reading rule's text from the settings. The script does not apply the rule.
- **Determinism**: one PCG64 stream per chunk (`chunk_normals`, :458), common random numbers over σ, scenario, option
  and design; canonical JSON; byte-stable output and shard merge equal to the unsharded bytes (M: test).
- **Settings** (`settings/sr2_simulation.json`, written 2026-11-08T15:00:22Z by `date -u`): grid σ_pair 3.0, 3.5, 4.0,
  4.5, 5.0, 5.5, 6.0, 7.0, 8.24 pp; scenarios none (ρ 0) and arm x seed (ρ 1); 20,000 replicates in chunks of 2,000;
  seed 7820261108; effects 8, 10, 12 pp; α 0.05; SESOI 5; thresholds 4.5 / 6.0 and MDE factors equal to the noise
  reader's (M: test); floor 0.01 pp²; B16's REML block (multi-start; M: test equality with
  `scripts/stage1_s1/reading/settings/reading.json`); the reading rule (threshold 0.06 and DES K6's text) and the list
  of approximations.
- **Approximations (written in the settings and printed with every result):** Holm on U only, not B16's Φ over U, O,
  L, F; the prompt (item) part of each SE omitted (df = the seed part's); N's σ_eval floor ignored; seed effects 0 (a
  cluster-specific seed component, which would inflate N's pairs only, is not simulated); the interaction form and
  size are this file's choice; branch H read as H (b) with money covered; lone cells left out of the REML fits (shown
  to change nothing against B16). The REML itself is not approximated (B16's algorithm, vectorized; parity tested).

## Tests added; suite counts before and after

- `test_blinded_sigma.py` (21): byte-for-byte output (literal inputs SHA-256 `70cd2449…` and σ̂_A `34.93048652522448`
  on the fixture; --out written once); planted sentinels (every fixture U in pp and as a share, residual, arm mean
  and seed mean, as repr, 4- and 6-decimal strings) absent from stdout, stderr and the file, and from a no-df refusal
  raised after every U is read; unexpected-error text not echoed; exactly five output keys; df 12 / 24 / 6 / 18 and
  the value against an independent numpy lstsq; option C; lone cells; arm and seed shift invariance; the √2 scale and
  pooled-not-averaged; the exact fit on an irregular table; off-pin inputs file, unit key and reader; the pinned reader
  is the committed noise_reading; family mix-ups (wrong option's families, a Llama unit under OLMo, one unit under two
  families, a 1B family name); method edits of another manifest, kind, or an R draw (and the R check restored); one
  edit for two arms; a cluster with no df; design mismatches (extra, missing, reused cell in not_run, wrong edits map,
  unknown design); a not_run cell lowers df; the inputs form; engine roles.
- `test_sr2_simulation.py` (27 with parametrization): REML vs B16 `fit_cells` (5 clusters × 2 start modes); contrast
  est/SE/df/p vs B16 `contrast_fit`; the two-arm rule and its floor; σ̂_A vs `blinded_sigma` (4 option/design cases);
  the plan rule vs `noise_reading.seed_rule`; Holm by hand; arm-mean and seed invariance (the power shortcut); the
  designs; byte stability and shard merge; printed rule, approximations and quantities; the reduced design and flag
  refusals; settings checks and B16 pins; the committed settings; cell SDs and N's pool; power/better sign and SESOI;
  null size near nominal on plan A (1,200 replicates; band 3.5-7%); the multi-start replicate; chunk streams and a
  merge of shards from different runs refused.
- Suite (M: `sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS): before
  208 passed, 57 skipped (18 s); after 256 passed, 57 skipped (54 s). 256 = 208 + 21 + 27.

## Mutants and shard results

Spec `scripts/scale78b/tests/mutation_spec_sr2.json`: 46 mutants (21 on blinded_sigma.py, 25 on sr2_simulation.py),
including the plan's list: no √2; lone cells counted; mean instead of pooled; an arm effect left in; a residual
printed (stderr); a U value in a refusal; error text echoed; plus pins, option, duplicate, method-edit, design, engine
role, restore; and for the simulation σ_e, interaction reach, σ̂_A and N factors, thresholds, review, Holm (Bonferroni,
no stop), two-arm floor and df, Satterthwaite, single start, multi-start selection, active set, step clip,
newly-floored stop, power sign, better's SESOI, familywise any/all, stopped drops, B9's a0, R_5, merge header, one
stream, lone-cell filter.

Runner `scripts/scale78b/tests/run_mutants_sr2.py`: the kit runner's form (copy of `scripts/scale78b` into
SCRATCH/repo, everything else linked; killed only on exit 1 with a FAILED line and no ERROR; anything else invalid;
baseline with the same command first), plus `SHARD:K/N`.

| Shard (M) | Baseline | Result | Clock (UTC) |
|---|---|---|---|
| SHARD:1/3 | exit 0, 48 passed | 16 killed | 15:09:57-15:11:01 |
| SHARD:2/3 | exit 0, 48 passed | 15 killed | 15:13:33-15:15:22 |
| SHARD:3/3 | exit 0, 48 passed | 15 killed | 15:15:31-15:16:52 |

Total 46 killed, 0 survived, 0 invalid. The spec and code have not changed since these shards ran.

## Commands for the lead's full runs (from WS or the merged checkout; PY = the main venv)

Simulation, option [B], full design, one shard per σ index (each under 10 min), then the merge:

```
cd <repo>; for i in 0 1 2 3 4 5 6 7 8; do
  $PY -I -B scripts/scale78b/sr2_simulation.py --settings scripts/scale78b/settings/sr2_simulation.json \
      --option B --design full --sigma $i --out <R>/sr2-B-full-s$i.json > /dev/null; done
$PY -I -B scripts/scale78b/sr2_simulation.py --merge <R>/sr2-B-full-s{0,1,2,3,4,5,6,7,8}.json --out <R>/sr2-B-full.json
```

Option [C]: `--option C`; a known anchor stop: `--design reduced --stopped olmo2-7b` (or `llama31-8b` under [B], or
both). An unsharded run (no `--sigma`) gives the same bytes as the merge.

**E runtime** (basis: M timing on a copy of the settings with 2,000 replicates and seed 99, under [B]: 26.1 s at
σ 3.0 (all plan A, the slowest case) and 4.2 s at σ 8.24, for both scenarios; under [C] 12.1 s at σ 3.0; scaled ×10
for 20,000 replicates): about 4.5 min for each low-σ shard and under 1 min for the highest; **[B] full about 20-30
min in all, [C] about 10-15 min** (E). The reduced design is faster (fewer and smaller fits).

Mutation full spec: `$PY -B scripts/scale78b/tests/run_mutants_sr2.py <repo> <new scratch> <out.json> ALL --timeout 300`
(about 5 min; E from the three shards' 64 + 109 + 81 s), under `sandbox-exec -p "$SB"` as I ran the shards.

`blinded_sigma.py` on block A (after block A, by the lead): write the inputs file (relative unit paths, the families'
designs, engines, edits map), then `$PY -I -B scripts/scale78b/blinded_sigma.py --inputs F --inputs-sha256 $(shasum -a 256 F | cut -c1-64) --out OUT`.

## Commands run (exit status)

1. `date -u` (14:44, 15:00, 15:18 UTC): 0.
2. Reading: `sed -n`, `grep -n`, `cat`, `wc -l`, `ls`, `git log`, `shasum` over r1-common, plan-ab, the ab-build and GXI
   rulings, Part 2 (§0, §2, §10, §16), Part 1 (§3, §4, §5, §6, §7), PR4 §3.2, P78 §5.3, DES (B1, K4-K9, DESO3),
   noise_reading.py and its tests, gate_b_reading.py, family_probe_reading.py, killtest_stage0_reading.py, B16's reml,
   contrast, tdist, schema, settings/reading.json (keys), edits.py, write_add_edit.py, the kit's mutation runner: 0.
3. Suite before: `sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests`: 0 (208 passed,
   57 skipped).
4. Iterations on the new test files (`$PY -B -m pytest ... test_blinded_sigma.py` / `test_sr2_simulation.py`): exit 1
   while fixing my tests (an off-pin key that collided with the duplicate check; the pinned σ̂_A; two wrong hand
   Holm rows; power expectations at small Satterthwaite df and one replicate reading plan B9), then 0.
5. A first smoke run of the simulation (400 replicates) exceeded the 120 s tool limit (the three-operand einsums) and
   went to the background; I stopped it with TaskStop (no output used). After replacing the einsums with matmul and
   the projection's pinv with solve: `prof.py` timing probe: 0; smoke run (400 replicates): 0 (7 s); timing copy
   (2,000 replicates) at three points: 0.
6. A first loop over mutation shards 2-3 exceeded the 120 s tool limit and went to the background; I stopped it with
   TaskStop, checked no runner process remained (`pgrep`, none) and deleted its partial outputs; shards 2 and 3 were
   then run one at a time in the foreground: 0 each (shard 1 earlier: 0).
7. Suite after (same command as 3): 0 (256 passed, 57 skipped). `git status --porcelain`, `git diff --stat`, `shasum`: 0.

## Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| The scale78b suite passes (base count plus the new tests) | passed | M: 208 → 256 passed, 57 skipped both times |
| Every Track S mutant killed by a real test failure, errors invalid, baseline with the same command | passed | M: 46/46 killed, 0 invalid; mut-shard1-3.json |
| blinded_sigma's output held byte for byte on a fixture (P2 §10.1's script half) | passed | `test_the_output_is_held_byte_for_byte_and_written_once` |
| No U value, arm mean, residual or per-cell value in stdout, stderr, any file or an exception message | passed on the fixture | sentinel test (success and a post-U refusal), unexpected-error test; mutants S-bs-residuals-printed, -value-in-refusal, -error-text-echoed killed |
| Refusals: off-pin input, family mix-up, a cluster with no df | passed | the refusal tests above |
| Simulation deterministic on a fixed seed, byte-stable | passed | `test_the_output_is_byte_stable_and_shards_merge_into_it` |
| The reading rule written in the settings before any run and printed beside the result, not applied by me | passed | settings `written_utc`; output `reading_rule`, `summary`; no full run made |
| --design gives the reduced design (V2) | passed | `test_the_reduced_design_runs_and_its_flags_are_checked`; σ̂_A df 6 / 18 |
| The SR-2 kit half (record-done prints no outcome) | not tested | K2's half, not this track |
| The full simulation's result and the 6% reading | not tested | the lead's run |

## Open points for the lead

1. **The interaction scenario's form and size** (settings `interaction`): an independent term on method-arm cells
   only, ρ = 1 (doubles their cell variance). P2 §10.3 names "with and without an arm × seed interaction" but no form
   or size. Rule on it before the full run, or add values to the grid (the file is new and unrun).
2. **The claim test's form**: P2 §10.3 says "HB-C with Holm at 5%"; the 1B reading's claim family is B16's Φ over U,
   O, L, F. The simulation runs Holm on U (stated). If the lead wants Φ's U part, that is a change before the run.
3. **The prompt part omitted** (no prompt-level data): its effect on the size is not simulated (I: V_prompt ≥ 0 widens
   the SE, but it also raises the Satterthwaite df, so the direction is not certain).
4. **Plan under [B] with SR-2**: one σ̂_A pooled over both families gives one plan for both (P1 §6.4). Under H (b) the
   money fallback (ruling 4 (i)-(ii)) is not simulated: H is read as H (b) covered.
5. **A stopped family's Holm family** (I): plan A tests P3, P4, P6 (m = 3); B9 and H test P3, P6 (m = 2). P2 says
   only that P1, P2, P5 are not tested there; the size of the Holm family is my reading.
6. **`not_run`** in blinded_sigma's inputs (a block-A cell that did not run, named by arm and seed) is this script's
   form. The lead rules whether a cell may be dropped from σ̂_A; without that ruling, the design must be complete.
7. **No σ_eval floor on σ̂_A**: P2 §10.2 names none, and none is applied. N's σ̂_pool has one (P1 §3.3).
8. **Block-A unit form** (I): `read_unit` requires a run-one e1 unit of the dev bank, split dev, role development.
   This matches the 7-8B kit's engine a0 units (R: runkit/stage1-78b/judge_units_stage1.py:42), but no block-A unit
   exists yet. K2/K3 should confirm that the kit's block-A arm jobs write that form, or blinded_sigma will refuse them.
9. **The method edits' hashes** come from the inputs' `edits` map (bound by the inputs SHA-256). They are not checked
   against a pins file. P2 §2.3 pins H1 and S1 now; A1, L1, S3 and S4 are [to be entered]. The lead may want a
   check against the gate record or the kit's pins once they are filled.
10. **Hashes for Part 2** (P2 §10.2, §10.3 "[to be entered]"): blinded_sigma.py, its test, sr2_simulation.py and its
    output take their SHA-256 at merge (the table above, if merged unchanged).
11. **`GATE_78B`** (ruling O14) holds the output hash of blinded_sigma. Its output names `inputs_sha256`, so the gate
    record can bind the whole chain.

## Concerns

- **The method-cell route patches `noise_reading.r_edit_matches` in-process** for one call and restores it in
  `finally` (the scorer layer's pattern; the file is unchanged; a mutant that skips the restore is killed). For a
  method cell that resumed, `read_unit`'s message says "an R arm is a fresh trajectory", a mislabel for a method arm
  (the refusal is right).
- **numpy on this Mac prints spurious matmul warnings** (B16 notes this). The simulation suppresses them with
  `np.errstate(all="ignore")`, as B16 does. Non-finite values are caught as refused contrasts (counted).
- **Byte stability is per machine and numpy build** (I): the draws and the linear algebra are deterministic for one
  environment; a different BLAS could flip a borderline p-value. The lead should run all shards in one environment.
- **The fixture's σ̂_A (34.9 pp) is large** because the fixture's U spread is wide. It tests form and blinding, not a
  realistic value.
- **Rule slip (minor):** while editing, I copied `sr2_simulation.py` to `/tmp/x.py` once and deleted it in the same
  command. That is outside R/r1-s-scratch/. It held only my own new code; nothing else was written outside WS and R.
- The settings' `written_utc` line says no run of the simulation used this file before it was written. That is true.
  Earlier smoke runs used a scratch settings file. The later timing run used a modified copy (2,000 replicates, seed
  99), which has another hash.

## Second set (GXB, recorded 2026-11-08T15:22 UTC): changes made (15:22-15:42 UTC, `date -u` 15:27 and 15:41)

Source: the section "Second set" of R78/lead-rulings-ab-build-20261108.md (R: :82 onward). Same rules as before. The full
simulation was not run. The settings file is still unrun: since its rewrite, only tests (smoke grids written to tmp
files) and one timing copy (2,000 replicates, seed 99: another hash) have run.

**What changed**
- **S-1** (`settings/sr2_simulation.json`, `sr2_simulation.py` `cell_sd` :397, `summarize` :555). The interaction is now
  a variance share ρ (the term's variance as a share of the cell variance; a method cell's SD is √(1 + ρ) σ_e). The
  scenarios are none (0), "arm x seed 0.5" (0.5) and "arm x seed 1" (1). ρ = 1 is the same model as before. The
  settings' `reading_rule.text` and its new `applies_to` say the rule covers every σ, every scenario (with or without
  the interaction) and every family read. The summary prints `reading_line` with that statement, the largest rate,
  where it occurs, and `scenarios_read`.
- **S-3.** A new settings key `limits` (printed in every output) states the claim test's omitted prompt part as a
  limit. The approximations list now calls Holm on U a bound on Φ (S-2's wording) and no longer says N's floor is
  ignored.
- **S-7** (`n_prompt_values` :403, `sigma_pool_sq` :419; new settings key `n_stage`). Each of N's cells now carries
  per-prompt values: the cell's U plus centred prompt noise, σ_eval,0 1.28 pp (Gate B wave 0a; R: P1:179), P = 200
  (R: PR4:227). The noise has its own stream, SeedSequence([seed, chunk, 1]). σ̂_pool = max(√P_pool, the median of
  the 6 pair SEs), the same arithmetic as `noise_reading.pooled` and `gate_b_reading.median_term` / `pair_se2`. A new
  test, in two cases ("plain", and "floor" where every r_j is 0 so the floor governs), computes noise_reading's
  σ̂_pool through the frozen reader (`GB.arm_record`, `GB.Reader`, `nr.pooled`) on synthetic count cells. Ours equals
  it to 1e-9 (M).
- **S-6** (`blinded_sigma.py`: `STOP_KINDS` :69, `check_anchor_stop` :218). The `not_run` form is removed.
  - The cells given must be exactly the design's, so any missing or extra cell refuses.
  - An `anchor_stopped` family must name its anchor-stop record as `anchor_stop` {path, sha256}. The record is read
    by path and its pinned SHA-256. Its `kind` must be "scale-78b anchor stop" and its `family` the family. Its
    `stop_kind` / `exit_code` must be one of {"safe_anchors_below_64": 3, "harmful_prompt_does_not_encode": 1} (GXB
    O6's two signals).
  - A `full` family may name no record.
  - Tests: both stop kinds pass; refusals for no record, an off-pin record, another family's record, an unknown kind,
    the wrong exit code, the wrong record kind, a record on a full design, A1 missing on a full design, and the old
    `not_run` key.
  - The sentinel test's refusal is now a late U-reading refusal (the last cell read, re-sealed with a summary.json
    that disagrees). It checks that the stderr holds no planted value. The no-df refusal's text is still checked by
    the unit test, with an anchored match.
- **O14 corrected.** blinded_sigma's output SHA-256 and its inputs SHA-256 go into `PLAN_B_78B` (after block A), not
  `GATE_78B`. This replaces open point 11.

**New SHA-256** (M: `shasum -a 256` in WS, 15:41 UTC)

| File | SHA-256 |
|---|---|
| `scripts/scale78b/blinded_sigma.py` (357 lines) | `decd49e5e76d40a6963eab4e418d70db2ad2fc1f3139af941628f6da11cff3ce` |
| `scripts/scale78b/sr2_simulation.py` (661 lines) | `65f47270d40d8581b98538228d7a7614dec3f71ffb2e00b9c58d68e782ab0c09` |
| `scripts/scale78b/settings/sr2_simulation.json` | `969c84d6ed13a21b5be67772f958a1a6b7531b53ca275e60f476aa032a180e54` |
| `scripts/scale78b/tests/test_blinded_sigma.py` (21 tests) | `50456353fab6c60b0edf6965a83e80e7c15556fcf5422f9583fabe63bd248234` |
| `scripts/scale78b/tests/test_sr2_simulation.py` (30 tests) | `1ecb7b8b3f0e70555f8b75e2b1bb7f636f177aee760db20c5110b065a807f7d7` |
| `scripts/scale78b/tests/run_mutants_sr2.py` (unchanged) | `50594102f50a22f04554681c4bac6b623b09470af2572c2464289ed28c2da13f` |
| `scripts/scale78b/tests/mutation_spec_sr2.json` (58 mutants) | `0432e8a5ba04e9672ed0781b6a9f672e9e5fb9091bce48d0becd76d7cc18a4df` |

**Counts (M)**
- Suite (the same sandboxed command): 259 passed, 57 skipped (55 s); 259 = 208 + 21 + 30. `git status` lists only the
  7 new files.
- Mutation spec: 58 mutants. Removed: the `not_run` mutant. The two whose find text changed were rewritten. Added 13:
  - six on the anchor-stop record: its pin, family, exit code, stop kind, record kind, and the record on a full design;
  - one for a stop without a record;
  - the variance share read as an SD ratio;
  - N's floor dropped, the low middle SE taken as the median, the pair SE at ddof 0, uncentred prompt noise, and the
    prompt-noise scale.
- Six shards, SHARD:1/6 to SHARD:6/6, run one at a time in the foreground, 15:32-15:41 UTC. Each baseline: exit 0,
  51 passed. Results: 10 + 10 + 10 + 10 + 9 + 9 = 58 killed, 0 survived, 0 invalid (R/r1-s-scratch/mut2-shard1..6.json,
  spec `0432e8a5…` in each). The first round's shard reports (mut-shard1-3.json, superseded) were deleted with the
  copied trees.

**Full-run commands.** As above; the scenarios are in the settings. **E runtime, revised:** about 8 min for each
low-σ shard under [B]. That is near the 10-minute limit for a foreground shard but fine for a background job. [B] full
takes about 40-50 min in all, [C] about 25 min. Basis (M), on the 2,000-replicate timing copy with three scenarios:
47.5 s at σ 3.0 and 9.0 s at σ 8.24 under [B], and 25.1 s at σ 3.0 under [C]; scaled ×10.

**Open points that remain (new or changed)**
- **The anchor-stop record's form** is my reading of O6. That means its kind string, its field names `family`,
  `stop_kind`, `exit_code`, and the two stop-kind names. The kit's record writer (K-track) must write exactly that
  form, or this check must change to the kit's form. The rest of O6's fields (JOB-DONE.json SHA-256, ids and counts)
  are not checked here.
- **σ_eval,0 = 1.28 pp is the 1B value.** It sets the size of N's floor in the simulation. N's plan is only printed,
  so it changes no simulated decision (σ̂_A decides block B). A 7-8B value exists only after N.
- **S-2's check** (that Φ's claim cannot pass unless the U contrast passes its Holm test) is the verifier's, per the
  ruling. I have not checked it.
- Open points 1-6 and 11 of the first list are ruled (S-1 to S-6, O14). Points 7-10 stand as S-7 to S-9 settle them,
  with point 10 (Part 2 hashes) unchanged.

## Fix round (the verifier's SV-1 to SV-7; GXB seventh set R-10 to R-15): 16:36-17:09 UTC (`date -u`)

Sources: R/r1-s-verify.md (verdict DEFECTS: SV-1 and SV-2 major test gaps; the code was right on every check), its
scratch R/r1-s-verify-scratch/ (e2e_parity.py, extra_mutants.json, extra_mutants2.json), and the seventh set of
R78/lead-rulings-ab-build-20261108.md (R: :199 onward). Pre-fix copies of the 7 files are in R/r1-s-scratch/prefix/.
The unified diff against them is R/r1-s-scratch/fix.diff (1,073 lines, 6 files changed; `run_mutants_sr2.py`
unchanged; SHA-256 `3b98d01706740f6d9fdb9bfcb82ebceacbcd199cfc6c3d548adeba5ba3493857`). The settings file was rewritten
(written_utc 2026-11-08T16:36:21Z). It is still unrun by any full run; since the rewrite, only tests (smoke grids in tmp
copies) and one timing copy (seed 99, 2,000 replicates; another hash) have run.

**What changed**
- **SV-1 (blinding test).**
  - (a) A new CLI test makes the frozen reader divide by zero: one cell, re-sealed, says 0 sampled answers. It asserts
    that stderr is exactly "blinded_sigma: unexpected error (ZeroDivisionError); nothing written", that stdout is
    empty, and that no file appears. The in-process test now also asserts empty stderr and the suppressed context.
  - (b) `guarded_run` runs every CLI call from a fresh cwd. Before and after the run it takes a SHA-256 snapshot of
    the fixture root (the inputs' folder and every unit), tmp_path (`--out`'s folder), the cwd and the script's own
    package folder. On success the only new file is `--out` and nothing changes. On every refusal and every error
    nothing appears and nothing changes.
  - (c) Every refusal is compared in full. A `refuses(expected)` context asserts `str(message) == expected` in all
    in-process tests, and the CLI tests compare the whole stderr line.
  - The verifier's two SV-1 mutants (`V-bs-exc-text-to-stderr`, `V-bs-side-file`) are in the spec, and both are
    killed.
- **SV-2 (the chain).** `test_run_chunks_chain_equals_an_independent_chain_replicate_by_replicate` takes the form of
  e2e_parity.py: `blinded_sigma.pooled_sigma`, `noise_reading.seed_rule`, B16 `fit_cells` (multi-start, the 1101
  cells in the fit, the sum rule), `contrast_fit` and `phi.holm`.
  - It compares every tally `run_chunk` keeps: plan shares; per family the familywise count; each contrast's tested,
    size and Holm counts; and power and better at 4 and 8 pp, which are sensitive to which draws are read.
  - Six configurations, 40 replicates each: [B] full, [C] full, [B] Llama stopped, [C] stopped, [B] at family ratio
    1.5, and [B] with both families stopped.
  - A companion test checks that the draws reach plans A, B9 and H.
  - The verifier's four wiring mutants, and its `V-sim-claim-fresh-block-a`, are in the spec; all are killed.
- **SV-3 / R-12 (unequal family noise).**
  - The settings list the single σ_pair under [B] as an approximation.
  - Two scenarios are added at ρ = 0: "llama sigma x 1.5" (`llama_sigma_ratio` "3/2") and "llama sigma x 1/1.5"
    ("2/3"). The grid's σ is OLMo-2-7B's; Llama's is the ratio times it, capped at the grid's top (`family_sigmas`).
  - `run_chunk` now takes per-family σ. Each scenario prints `sigma_pair_pp_by_family`.
  - The 6% rule covers these scenarios too: the reading_rule text, `applies_to` and the printed `reading_line` say so.
  - So there are now 5 scenarios: none, arm x seed 0.5, arm x seed 1, and the two ratios. Under [C] the two ratios
    equal "none" except N's printed plan (stated in the settings).
- **R-11.** The settings' limits, the reading_rule text and the reading line state that the familywise rate is the U
  claims' rate (Holm on U), and that Φ's O and L words are not simulated.
- **R-13 / SV-4 (engine identities).**
  - `engine` is now {a0, R, block_a}: the reused a0 units, N's R units and block A, per role as noise_reading.py
    takes them.
  - A new fixture family carries three different identities. The 1104 and 1105 cells carry block A's, and pass.
    Each role set to another value refuses at its first cell with the exact line. Setting a0 or R to block A's value
    refuses the reused cells.
  - The verifier's `V-bs-reused-includes-1104` is in the spec and killed, as is my new `S-bs-engine-a0-r-swapped`.
- **SV-5.** The no-df refusal is compared in full (equal to the whole message), and `V-bs-values-after-no-df` is killed.
- **SV-6.** `main` now refuses a missing `--out` folder before the read, with the exact line "--out's folder does not
  exist: nothing written" (tested). It writes `--out` with `open(out, "xb")` inside the guarded block; a file made
  meanwhile refuses as "written once". New mutant: `S-bs-out-parent-unchecked`.
- **SV-7.** The summary prints `refused_contrasts_total` and `nonconverged_fits_total`, plus a note that a refused
  contrast counts as not rejected. Both are tested against the rows' sums. New mutant:
  `S-sim-nonconverged-total-zero`.
- Other new mutants: `S-sim-llama-ratio-ignored`, `S-sim-llama-uncapped`, `S-sim-one-sigma-both-families`.

**New SHA-256** (M: `shasum -a 256` in WS, 17:09 UTC)

| File | SHA-256 |
|---|---|
| `scripts/scale78b/blinded_sigma.py` (364 lines) | `6e7079e80a7ce54fa8ee2d141524f64fbb4cd08a40cabc85186f807e07411343` |
| `scripts/scale78b/sr2_simulation.py` (682 lines) | `0ff5e54596a144d6cd4d3643ce83bc14bd21ebc9ea80b2416ebab645fd29fe89` |
| `scripts/scale78b/settings/sr2_simulation.json` | `99410f9f8e3484264dde13687a1007b529c671b5d8b59d0ff8e7bb073c8effe3` |
| `scripts/scale78b/tests/test_blinded_sigma.py` (22 tests) | `28c443b9d53bd518b9cdcaaa4056fd0424c95a0a6f209dd454c419fec3e1c8fe` |
| `scripts/scale78b/tests/test_sr2_simulation.py` (23 defs, 38 tests) | `7813636d0e6b20af269499e0bdbc79c3b09911c52910d4b31a8a06bc5bf77fd8` |
| `scripts/scale78b/tests/run_mutants_sr2.py` (unchanged) | `50594102f50a22f04554681c4bac6b623b09470af2572c2464289ed28c2da13f` |
| `scripts/scale78b/tests/mutation_spec_sr2.json` (73 mutants) | `e349a6dc571574e9d40450e8d24db8cdc2545955d9762e047dc336cc10cd007c` |

The fixture's pinned inputs SHA-256 changed to `674d7c8b…`, because the inputs' engine map now has three keys. The
pinned σ̂_A `34.93048652522448` is unchanged.

**Counts (M)**
- **Suite** (the same sandboxed command): **268 passed, 57 skipped** (56 s); 268 = 208 + 22 + 38. `git status` lists
  only the 7 new files.
- **Mutation spec:** 73 mutants = 58 earlier (one find text updated) + 6 new of mine + the verifier's 9, verbatim from
  its two specs.
- **Shards:** SHARD:1/8 to SHARD:8/8, each in the foreground, 16:45-17:05 UTC; every baseline exit 0, 60 passed.
  Results: 10 + 9 + 9 + 9 + 9 + 9 + 9 + 9 = **73 killed, 0 survived, 0 invalid** (R/r1-s-scratch/mut3-shard1..8.json,
  spec `e349a6dc…` in each).
- **The stopped run:** a first loop over shards 2 and 3 was moved to the background at 180 s. Shard 2 had finished
  and written its report. I stopped the loop with TaskStop, checked that no runner remained (`pgrep`), deleted shard
  3's partial output, and re-ran shard 3 alone.
- The earlier rounds' shard reports were deleted earlier (second set) or are superseded (mut2-shard1..6.json, kept).

**E runtime of the full run (revised; basis M on the 2,000-replicate timing copy, 5 scenarios: [B] 88.6 s at σ 3.0
and 16.5 s at σ 8.24; [C] 39.3 s at σ 3.0; scaled ×10).**
- [B]: about 15 min for each low-σ shard and about 3 min for the highest; **[B] full about 80-110 min in all**.
- [C]: about 6.5 min for the slowest shard; **[C] full about 40-55 min**.
- The low-σ [B] shards exceed 10 minutes, so run them as the lead's background jobs (the memory rule "long jobs
  outside agents"). The commands are unchanged: one `--sigma i` per index 0-8, then `--merge`.

**Open points left**
- The anchor-stop record now has its form ruled (GXB fourth set: kind, family, stop kind, exit code, JOB-DONE.json
  SHA-256, ids and counts). blinded_sigma checks the first four. The JOB-DONE.json SHA-256, ids and counts are not
  checked. The "one shared fixture" with K2's writer does not exist yet: K2 should create it, and blinded_sigma's test
  should then read it.
- σ_eval,0 = 1.28 pp is still the 1B value. It reaches only N's printed plan.
- R-14 (the reading wrapper keeps Φ's graph) and R-15 (12 df per family into Part 2 §10.2) are not this track's files.
- The verifier's minor untested branches (the bars-frozen check, the four-digit seed key, the method-entry key set, the
  "no sampled answer" refusal, which cannot fire; `--merge` ignoring `--design`/`--stopped`; σ strings not validated)
  are not addressed in this round.

## Follow-up (the re-verifier's SR1-SR10; GXB eleventh set R-27, R-28): 17:52-18:28 UTC (`date -u` 17:53, 18:28)

Sources:
- R/r1-s-reverify.md (VERIFIED_WITH_MINOR; SR1-SR10);
- its scratch R/r1-s-reverify-scratch/ (e2e_row_parity.py; extra_spec_rv.json `b536887a…`);
- the eleventh set of R78/lead-rulings-ab-build-20261108.md (R: :266 onward).

Copies of the fix-round files are in R/r1-s-scratch/fixround/. The unified diff against them is
R/r1-s-scratch/followup.diff (483 lines; 5 files changed; SHA-256
`45547af94f91defc76076cd3bb5eeb6bef2f9250b0424830ee0184efe48f55a4`). **`sr2_simulation.py` and `run_mutants_sr2.py`
are unchanged.** The settings file was rewritten for SR9's text only (written_utc 2026-11-08T17:53:15Z). It is still
unrun by any full run: since the rewrite, only tests (smoke grids in tmp copies) have run.

**What changed**
- **SR9 / R-27** (settings `limits[1]`): Φ's O and L words "start at gamma x alpha = 0.5% absolute in all (10% of
  alpha, alpha = 5%), within their own contrasts". A test holds the corrected text, and that the old "0.5% of alpha" is
  gone.
- **SR10** (`blinded_sigma.read`): `read()` now wraps `_read()`. A refusal passes as it is. Any other error becomes a
  `Refusal` with the fixed `UNEXPECTED` line and the type name only, raised outside the handler, so `__context__` and
  `__cause__` are None. `main` does the same. A new test, `test_an_in_process_read_error_carries_its_type_and_the_fixed_text_only`
  (the zero-answers cell, in process), checks the exact line and that no context is kept.
- **SR3** (`guarded_run`): every CLI run now goes through an audit wrapper. The wrapper installs `sys.addaudithook`
  before `runpy` runs the script, and logs each event to a file it opened before the hook:
  - every `open` event whose mode (`w`, `a`, `x`, `+`) or flags (`O_WRONLY`, `O_RDWR`, `O_CREAT`, `O_APPEND`,
    `O_TRUNC`) write;
  - every rename, link, symlink, mkdir, remove, rmdir, truncate, chmod, chown, utime, chflags, mkfifo or mknod event;
  - every shutil copy, move, rmtree or archive event, and every tempfile mkstemp or mkdtemp event.

  Any write other than `--out`, anywhere, now fails the tests: a written path counts as new, and any other event
  counts as a change. The folder snapshots stay as a second check. The wrapper must also see the write of `--out`,
  which shows that the hook records. `RV-bs-side-file-repo-root` is killed.
- **SR4:** an in-process race test. A `read` that creates `--out` after the existence check is refused by the
  exclusive create with the exact line. The file keeps its bytes, and stdout and stderr stay empty. `RV-bs-out-wb` is
  killed.
- **SR8:** the engine map's form check is tested on three cases: the old {block_a, reused} form, an extra key and a
  non-hex value. Each refuses with the full line. `RV-bs-engine-keyset-unchecked` is killed.
- **SR1:** `test_each_familys_own_sigma_reaches_run_chunk_through_simulate_row`, at σ 5.5 and 7.0 under [B], in the
  e2e_row_parity form.
  - It goes through `simulate_row`, with the settings' scenarios none, ×1.5 and ×1/1.5.
  - It compares each row's plan counts, and per family the familywise and Holm counts, with the independent chain at
    each family's own true σ. That σ is derived in Fractions, with the cap.
  - It asserts that the three scenarios differ in the reference.
  - `RV-sim-run-ignores-family-sigmas` is killed.
- **SR2, SR5, SR6:** a `summarize` test on a synthetic [B] document with all five scenarios.
  - The maximum sits in Llama-3.1-8B's family, in "llama sigma x 1.5", and is found there.
  - Exactly 1,200 of 20,000 (6%) is not above the threshold; 1,201 is.
  - A nonzero refused total (5) and the non-converged total (12) equal the rows' sums.
  - `RV-sim-max-olmo-only`, `-max-skips-ratio-scenarios`, `-threshold-ge` and `-refused-total-zero` are killed.
- **SR7:** the SV-2 test now also compares N's printed plan with an independent σ̂_pool. That σ̂_pool comes from
  Fractions of the per-prompt differences, `FR.clustered_se2` and `noise_reading.pooled`'s seed rule.
  `RV-sim-n-plan-olmo-only` is killed.
- **Mutation spec:**
  - The re-verifier's 12 mutants are added verbatim.
  - Two of mine are added: `S-bs-read-keeps-cause` and `S-bs-read-unguarded`.
  - `V-bs-exc-text-to-stderr` and my `S-bs-error-text-echoed` are re-targeted at `read()`'s guard, because their old
    find text in `main` no longer exists.
- **Test time:** to keep each mutant run short, the byte-stability smoke test now uses 2 scenarios and 30 replicates.

**New SHA-256** (M: `shasum -a 256` in WS, 18:28 UTC)

| File | SHA-256 |
|---|---|
| `scripts/scale78b/blinded_sigma.py` (384 lines) | `3e0b7d111362ff13ab880a83033fe0103df14d6d77cc3c650e4162f85cb992df` |
| `scripts/scale78b/sr2_simulation.py` (unchanged) | `0ff5e54596a144d6cd4d3643ce83bc14bd21ebc9ea80b2416ebab645fd29fe89` |
| `scripts/scale78b/settings/sr2_simulation.json` | `c6f0c81e418e4efe8f876655621bbb1dbfa51ca91aa88a335a812e53eaa04b88` |
| `scripts/scale78b/tests/test_blinded_sigma.py` (25 tests) | `7cd880dc1652087cd142219eeda0886f45fb77d76f3ecfebb5002c99a029d1f5` |
| `scripts/scale78b/tests/test_sr2_simulation.py` (25 defs, 41 tests) | `c31129f797ebd508398e93bec99f08625d00744c1e8de20e6afa5d14c22a2ca1` |
| `scripts/scale78b/tests/run_mutants_sr2.py` (unchanged) | `50594102f50a22f04554681c4bac6b623b09470af2572c2464289ed28c2da13f` |
| `scripts/scale78b/tests/mutation_spec_sr2.json` (87 mutants) | `d11865247c74ea9ccf88a0a99d919bb3c8db11b2a8ab3406d1c7950bce65a17a` |

**Counts (M)**
- **Suite** (the same sandboxed command): **274 passed, 57 skipped** (74 s); 274 = 208 + 25 + 41. `git status` lists
  only the 7 new files.
- **Mutation spec:** 87 mutants = 73 + 12 (the re-verifier's) + 2 (mine).
- **Shards:** SHARD:1/12 to SHARD:12/12, one at a time in the foreground, 18:01-18:28 UTC, each under 2.5 min. Every
  baseline: exit 0, 66 passed.
- **Results:** 8 + 8 + 8 + 7 × 9 = **87 killed, 0 survived, 0 invalid** (R/r1-s-scratch/mut4-shard1..12.json, spec
  `d1186524…` in each). No command went to the background this round.

**E runtime (corrected)**
- **Mutation ALL:** about 25-30 min serially. Basis (M): the 12 shards ran back to back in 27 min. So `ALL` is the
  lead's background job, or 12 shards of under 3 min each.
- **Full simulation:** unchanged code, so my fix-round figures stand as the low end, and the re-verifier's measurement
  on a loaded Mac (R: r1-s-reverify.md §6) as the high end.
  - **[B] full: about 80-145 min**, with low-σ shards of about 15-19 min.
  - **[C] full: about 40-70 min**, with the slowest shard about 6.5-8 min.
  - The low-σ [B] shards exceed 10 minutes, so they are background jobs.
  - The commands are unchanged: one `--sigma i` per index 0-8, then `--merge`.

**Open points left**
- The anchor-stop record: the JOB-DONE.json SHA-256, ids and counts are not checked, and the shared fixture with K2's
  writer does not exist yet.
- σ_eval,0 = 1.28 pp reaches only N's printed plan.
- `main`'s own guard now covers only `render` and the `--out` write (read's errors are guarded in `read`). No test
  drives that branch, and no mutant targets it.
- The re-verifier's list of minor untested branches (the bars-frozen check, the seed-key form, the method-entry key set,
  `--merge` ignoring `--design`/`--stopped`, σ strings) is not addressed.
