# D1-readers: independent adversarial verification, round 2 (after fix round 1)

- **Written** 2026-11-01, finished about 10:40 UTC (clock read with `date -u`: 10:15:08 at the start, 10:37:33 before
  writing), by an Opus verifier for the main-study lead (GI VIII), track D1-readers.
- **Object.** `scratchpad/builds/ws-d1` at `55d5f8b`. `git status --porcelain` shows only the untracked folder
  `scripts/stage1_s1/reading_extra/` (17 files); `git diff` is empty. Every file's SHA-256 (first 16 hex) equals the
  build report's tables (§1 for the unchanged files, §6.4 for the six changed ones). The main checkout is now at
  `a494ff7`; from `55d5f8b` it adds only reports, FOCUS, the dossier and OLMo-3 files (no code, no REV4 change).
- **Data rules kept.** I opened nothing under `tmp/`, no block-a/ or block-b/ folder, no unit, eval, answer, label,
  guard-sample, judge or COMPLETE.json file of real data, no hidden or selector bank, no plant or decoy path, no seal.
  From the W1 manifest I read roles and paths only (7 sealed records listed, none opened; `selector_spec.json` is role
  "settings"). Every reader ran on synthetic worlds (the builder's `synth_kit`, `extra_kit`) in basetemps under
  `scratchpad/builds/tmp/vd1r2-*`, all deleted. No git command that changes state; no network, install, pod or API call.
  I did not edit `ws-d1`.

## Verdict: defects (1, low, in `cost_table`; the fix round's two fixes are correct; four readers verified)

The fix round fixed both round-1 defects correctly: B10 references under C-lean now use one lean state (K6), and the
median stage-1 R slot is printed beside 1 FRE (K7). My own code reproduces every value the five readers print on
synthetic worlds of all three readings (283 checks, 0 failures). `fk_power`, `stage3_pick`, `sa_shift` and
`cap_reports` compute what their frozen rules say. One defect remains, in `cost_table`: it prints no C-full cost for
the four `ref_eval` reference points (adapter scaling 0.9, 0.75, 0.5 and SP), although REV4:774 needs every menu item's
cost under both conventions and REV4:813 gives the C-full rule for exactly this case. It is low severity: the value is
null with a reason, not wrong, and the builder disclosed the choice (K5). But it is not the most literal reading, it is
asymmetric with K6, and it leaves the Sp and Ow menus without a C-full cost for two references. `cap_reports` still
opens sealed-class files (reading C5); that is the lead's open point, not a blinding defect (below).

## Defect

### D1 (low). `cost_table`: no C-full cost per point for the `ref_eval` references (SP and adapter scaling)

- **Rules.** REV4:774 (LN-08's menus): "at each τ_O and τ_L, report every arm in the menu with its label, O, L and cost
  under both conventions". The Sp and Ow menus hold "SP, adapter scaling, Safe LoRA, recipe G, B+Qi" (REV4:766-772).
  REV4:813: "**C-full:** §7.3. For an evaluation-only reference: the same minus training, plus its transform." The
  runbook draft (1d §6) names this reader's purpose: "the menus' 'cost under both conventions' (rev4:774) has no
  producer".
- **What the code does.** `_b10()` (cost_table.py:346-352) gives each `ref_eval` point `_priced(None, lean_s, c0_s)`:
  C-full `seconds` and `c_full_fre` null ("reading K5: one -b10-run step holds every point and a0's regeneration"),
  C-lean one lean state. So C-lean is priced from a proxy (K6: the measured c0 less the frozen lean training price),
  while C-full, the convention for which REV4:813 is written, has no value. K5's only alternative is "an equal split
  over its points", which also includes a0's regeneration (a study cost, REV4:816).
- **Reproduction** (`verify-D1-readers/r2_edges.py`, run from the ws-d1 root with the venv python; synthetic
  `extra_kit.cost_kit(..., "plan_a")`): `table(kit, "plan_a")["b10_references"]["ref_eval b-ref job 2"]["per_point"]`
  prints, for each of `scale:0.9`, `scale:0.75`, `scale:0.5` and `prefix`: `seconds` null, `c_full_fre` null,
  `c_lean_c0` 0.7970448. **Expected:** a C-full value per point, for example REV4:813 read literally on measured runs:
  (the mean a0 run slot 2,977.092 s − the frozen C-full training 219.7 s (`selector_spec.json` `C-full.training_s`) +
  the transform, about 0) / 2,934 s = 0.9398 FRE on this kit; or the measured Safe LoRA `-evaluate-P` step of the same
  seed (the same B10 evaluation code) as the measured price of one full evaluation-only state; or the equal split less
  the same seed's measured Safe LoRA `-b10-regenerate` seconds. **Actual:** null.
- **Fix.** Add one stated C-full price per `ref_eval` point (a few lines in `_b10`, a test, a mutant), keep K5's null as
  the alternative; or the lead rules K5 in and records that the Sp and Ow menus print no C-full cost for SP and adapter
  scaling (a deviation from REV4:774). Note N4 (a per-reference mean over seeds) belongs to the same change.

## Reader by reader

### 1. `fk_power` (REV4:574): verified

- **Rule.** REV4:574: "the stage-1 reading prints F_k's planning power at the measured q beside each F_k result (report
  only; after block B, because θ0's and the arms' 500-bank answers are under block A's seal until then)". REV4:565:
  "q = the share of prompts on which the arm's refusal flag and θ0's differ." The table (REV4:567-572) has the columns
  "Per comparison (5%)" and "Inside Φ (F_k at 0.375%)". The formula is the review script's `se_df` and
  `power_feasible` (`stat_review_o_power.py`:106-117): item part max(q − Δ², 1e-12)/P × 100², seed part σ_s²/J with
  J − 1 df, Satterthwaite df, power Φ((τ − Δ)/SE − t(1 − α, df)). The reader's `planning()` is the same, with Δ = 0
  and τ = B16's `tau_o.star_pp` (5).
- **Recomputation** (`r2_check.py`, with my own Student-t quantile: Simpson integration of the density and bisection,
  independent of B16's `tdist` and of the review's continued fraction). q per seed by hand from `tables.json` equals
  the printed one exactly; P = 500; J = 6, 3, 9 under plan A, block A only and plan B, with the J flag set; all four
  rows of every contrast agree to 3.8e-12 (power), 1e-12 (SE) and 1e-8 (df). F_k's copied fields (Φ rejection,
  p-value, level at rejection, final level, θ0 part and interval, states) equal B16's.
- **Inputs.** `tables.json` and `reading.json` only (audit hook on every open), bound by B16's
  `provenance.input_sha256`; a wrong input refuses with exit 2 and writes nothing (command-line run).

### 2. `stage3_pick` (REV4:428): verified

- **Rule.** REV4:428: "The pick rule = the two primary contrasts with the largest |t| of the primary U test, among
  contrasts whose U part reads better or worse (U); ties to the lower P index; none if no contrast has either U word."
  REV4:427: "At most 2 contrasts per family". The reader: eligible = B16's `rows[k].u_part.words` holds "better" or
  "worse (U)" (flags checked against the words); |t| = |est/SE| of `contrasts[k].U` (checked against B16's t); order
  (−|t|, P index); at most two.
- **Recomputation.** My picker: plan A `['P1', 'P4']`, block A only `[]`, plan B `['P1']`, equal to the reader's. Seven
  edge cases on a modified synthetic `reading.json`, all as the rule says: an exact |t| tie between "worse (U)" P1 and
  "better" P3 (P1 first), the tie the other way round (P2 before P5), three eligible (the two largest), none eligible,
  a below-SESOI note alone (not eligible), one eligible, and the largest |t| that is not the largest estimate.
- **Inputs.** `reading.json` only. Stdout prints the pick names (note N12).

### 3. `sa_shift` (REV4:276): verified

- **Rule.** REV4:276: "P4 under S-a is expected to read about 0.3 pp less in S1's favour than under HB (−0.28 pp for
  S-a − HB, M (VR-B), computed under D0); the record prints it." P4 = U(a0) − U(S1) (REV4:228), so "less in S1's
  favour" is a negative S-a − HB. The reader prints the expectation as written and, beside it, B16's S-a estimate
  minus B16's HB estimate of P4.
- **Recomputation.** From the U table: S-a = the mean over a0's seeds − the mean over S1's seeds; HB = the paired mean
  on the common seeds (B16's `contrast_fit` estimator). Plan A: 19.9286 − 20.1389 = −0.2103 pp; block A only
  −0.7222 pp; both equal the printed values to 1e-9 with the right direction word; plan B prints "not applicable".

### 4. `cap_reports` (REV4:554-555): verified, with the open input question (C5)

- **Rules.** REV4:554 (LN-14): "under Branch 128, θ0's 400 PHTest answers are made once at the full cap and judged both
  full and cut, by W1-18's bar, as a pre-set report. If θ0 fails the bar, the paper states the cut as a limit for
  PHTest; the cap rule does not switch." REV4:555 (LN-19): "The record states the route per source. The cap record
  also prints the measured flag-change share per source (full against cut, where both exist)". ADD:506 (§24 point 2)
  reads the bar at n = 400 as "at least 388 of 400 flags agree, and the refused count moves by at most 8"; the reader
  recomputes `oext_eval.transfer_bar` (100 × agree ≥ 97 × n, 100 × move ≤ 2 × n).
- **Recomputation** (my own walk of plan.json outputs, folders and summaries): plan A 75 units, pooled dev-100
  191/7,500; block A only 27 units, 62/2,700; plan B 78 units, 207/7,800; block A only under Branch full 27 units,
  dev-100 69/2,700 and PHTest 65/10,800. Every by-arm or by-reference pool, every planted per-unit `flag_change`, the
  one route set and the LN-14 pass equal mine. Engines X and Y hold identical route texts (checked in the settings).
- **What it opens** (audit hook): `sources.json`, `plan.json`, the seals, COMPLETE.json, `oext_summary.json`,
  `oext_transfer_summary.json`; no folder listing. The last three are sealed-class files, so the brief's input rule is
  not met as written. The values exist nowhere else; the critic's own default (2-critic §2.4: "a seal-safe extractor
  run inside the reading script, after step 1 opens the outcomes") is what was built; the reader needs `sources.json`,
  so it cannot run before the input build, and it opens the same summaries the builder opens, plus θ0's transfer
  summary. Not a blinding defect; the lead's ruling C5 and a reading-script exception to the never-open list are open.

### 5. `cost_table`: D1 above; otherwise verified, including the fix round

- **Rules checked.** REV4:632 ("1 FRE = 2,934 s ... fixed at W1-P and never re-estimated; the median of all stage-1 R
  arms is reported beside it"), :633 (C-full), :635-637 (C-lean, frozen lean prices, c0), :774, :794-796 ("≈ 0" only
  below 0.01 FRE; A1 only from the wave-0b ledger), :813, :816 (LS-13 charging), :823 and :825 (§10.4). Every
  double-quoted passage of the five docstrings and RULE lists is in REV4 (`r2_quotes.py`; the two misses are a regex
  artifact and the capital "Under" at the start of the LN-14 quote, where REV4 has "under").
- **The fix round's D1 (K6) is right.** A B10 state under C-lean = the measured c0 − the frozen lean training price
  220 s (`selector_spec.json` C-lean variants a and b, `training_s` 220.0) + its transform; this is REV4:813's form and
  §10.4's own construction (0.75 c0 = (15 + 635)/870 at the frozen lean prices). The c0 job's readable ledger holds
  training and the lean evaluation in one `-lean` step (job_runner_stage1.py:452-458), so the frozen 220 s is the only
  training price available. The builder's comparison is right: at c0 = 2,386.2 s both forms give 0.9078 c0; below
  2,166.2 s the frozen-price form prices one state above a whole lean run. I agree with the dispute on `b10_certify`:
  it is a study cost (no menu holds it), and REV4:823 converts a study cost by its measured seconds / c0.
- **The fix round's D2 (K7) is right.** `units.fre_beside` holds the median slot of the stage-1 R runs, report only,
  and 1 FRE stays 2,934 s.
- **The round-1 notes 2-5 are fixed** (checked): ref_eval and Safe LoRA carry `includes_a0_regeneration`; the plan-B
  split counts only the reading's arms (S4 split = whole, 3,206.743 s); H1 and S1 carry the Mac note; a charged kind
  with no complete job prints null and its arm no charge (the builder's test).
- **Recomputation** (`r2_check.py`, my own reading of K1-K7 on the ledgers): plan A c0 1,083.983 s, lean state
  863.983 s, R median 3,355.8705 s over 4 runs; block A only 4,175.314 s over 1 run; plan B 2,601.829 s over 7 runs;
  every arm's run count and C-full mean; every by-kind total (the B10 kinds excluded); every charge whole and split
  (plan A: L1 3,375.851/2,002.476 s, S3 5,953.493/2,976.747 s, S4 3,206.743/1,603.371 s, A1 10,944 s) and every total;
  each B10 job's whole and per-point values under both conventions; the a0 regeneration reported apart. All equal.
- **Edge cases** (`r2_edges.py`): a crashed run with a readable ledger plus a complete re-run counts once (the
  crashed ledger is listed, `named_by_plan_outputs` false); a moved host's ledger is not read; a crashed c0 beside a
  complete one gives c0 = the complete one.
- **What it opens** (audit hook, all three readings): `plan.json`, the seals and `cost-ledger.json` only; no
  sealed-class file; no folder listing.

## Notes (not counted as defects)

1. **C5 (`cap_reports` input)** stays the lead's ruling, with an exception in the reading script for it and for
   `cost_table` (`tmp/stage1-olmo/retrieved/` and `seals/` are on the 1 Nov never-open list).
2. **LN-19's PHTest line.** Under Branch 128, `ln19.pooled.phtest` prints share null with "no unit holds both forms
   of this source (no full answer exists)", while θ0's LN-14 pass holds both forms of all 400 PHTest prompts and its
   share is printed under `ln14.report.flag_change` (synthetic: 4/400). LN-19 asks for the share "where both exist".
   A pointer in the `ln19` block (or θ0's transfer share as the PHTest source line) would prevent a misreading.
3. **One missing ledger refuses the whole cost table.** On the synth_kit world (no ledgers) the command exits 2 with
   "a-2 job 0: a complete, pulled job whose cost ledger is not in block A's seal". On the real kit every runner job
   writes a ledger (write_ledger exists since the B15 merge `6afa4ab`, 24 Oct, before W1-18 ran), but a seal-listing
   pre-check by the lead (does every complete, pulled job of blocks A and B have `job-I/cost-ledger.json` in its
   seal? no ledger opened) would de-risk the reading-day run.
4. **No per-reference value over seeds.** Arms get the mean over their seeds; B10 references are printed per job
   (seed) and point. Filling the Sp and Ow menus then needs a hand-made mean (REV4:400's spirit). Part of D1's fix.
5. **Safe LoRA's transform** is priced by the step's wall seconds, not by the ledger's own `transform` stage
   (`safe_lora_timing.json` `seconds.total`, which the runner records as the transform's cost and does not count
   twice, job_runner_stage1.py:802-812). Both are defensible; state it as a reading.
6. **K3's split and the uncharged items.** The representation pass also computes DataShield-style's scores (REQ-12,
   a stage-1c secondary arm; `representation_pass.py` docstring) and Gate C's reproduction, besides stage 1b's pools,
   so the split's denominator (the reading's arms only) should say so. REV4:796's "anchor job" (Gate B's anchor pod)
   is neither charged nor named in K3.
7. **Reported apart, not in the table.** Pod overhead and the judge pods (REV4:633, :810) are per pod, outside the
   job ledgers; the record needs them from the block cost reports.
8. **The weak outcome signal** is also in each run's `-calibrate` step (the engine's full evaluation: 468 greedy and
   the sampled harm answers), not only in `-oext`; the conclusion (run inside the reading) does not change.
9. **K2's B+Qi gap** ("a few per cent at the 500-prompt form"): REV4:827's dev-100 prices imply about 100-130 s of
   extra training per seed; at Branch 128's smaller c0 (REV4:638: "much less") that is about 6-9% at c0 = 1,400-1,800 s
   (E).
10. **`stage3_pick` S1 against `hb_claim` R3** (builder's open point 4): the literal REV4:428 supports S1.
11. **`fk_power` F2-F5** are defensible and labelled; under plan A, P and J are the planning values.
12. **Stdout words.** The pick names and the LN-14 word print on stdout, as B16's headline words and `hb_claim`'s
    sentences do.
13. **`bound_reading`** checks the settings pin and the sealed contrasts, not B16's module hashes (round-1 note 9).
14. **The mutation spec** (49 entries) is the lead's run. The two fix-round shard reports name 111 baseline tests and
    the current file hashes; 12 of 12 new mutants killed. I ran no mutant.

## Acceptance criteria (from the brief)

| Criterion | State |
|---|---|
| New package; no edit to B16, the builder or any pinned file | passed (`git status`, empty `git diff`, hashes) |
| Each reads only text-free documents of the reading and readable ledgers | passed for fk_power, stage3_pick, sa_shift, cost_table (audit hook); **not met as written for cap_reports** (sealed-class summaries; disclosed; C5) |
| Values only into its own output; exclusive create; canonical JSON | passed (second run exits 2 "exists"; refusal writes nothing; words on stdout as the neighbours) |
| Frozen rule quoted in each docstring with its source line | passed (all quoted passages found in REV4) |
| Tests on synthetic documents | passed: 111 passed in 19.77 s; 567 collected with the two neighbour suites |
| Ambiguities read literally and listed | passed, except D1 (K5's null is not the most literal reading of REV4:774 with :813) |
| Values correct against independent code | passed: 283 of 283 checks |
| Run on the real kit | not tested (forbidden) |

## Commands I ran (exit 0 unless noted; all on synthetic data)

| Command | Result |
|---|---|
| `git -C ws-d1 status --porcelain`, `diff`, `diff --stat`, `log -3`; `git -C main log/diff --stat 55d5f8b a494ff7`; `git log -S "def write_ledger"` (read-only) | only `reading_extra/` untracked; main adds reports, FOCUS and OLMo-3 files only; ledgers since `6afa4ab` |
| `shasum -a 256` and `wc -l` of the 17 files | equal to the build report's tables |
| venv python: manifest roles and paths; `selector_spec.json` `cost_conventions`, `option_cost_rule`; `oext_eval.json` against `oext_eval_y.json` | 7 sealed records listed by path, none opened; routes and transfer bar equal |
| `pytest -q -p no:cacheprovider --basetemp=builds/tmp/vd1r2-tests-1 scripts/stage1_s1/reading_extra/tests` | 111 passed in 19.77 s; 330 MB, deleted |
| `pytest --collect-only` on reading_extra, reading_input and reading tests | 567 collected |
| `r2_check.py builds/tmp/vd1r2-check-1` | 283 PASS, 0 FAIL; deleted |
| `python -m` each reader on the plan-A synthetic world | pick, fk, sa, cap exit 0; a second run exit 2 ("exists"); a wrong input exit 2, no file; cost_table on the synth_kit world exit 2 (note 3) |
| `r2_edges.py builds/tmp/vd1r2-edges-1` | 5 PASS, 0 FAIL (D1's reproduction printed); deleted |
| `r2_quotes.py` | every quoted passage found but two (explained above) |
| venv python: the two fix-round mutation reports | 12/12 killed, trees at the current hashes |
| `date -u` | as above |

## Evidence paths

- My code and output (all under `scratchpad/builds/verify-D1-readers/`): `r2_check.py` (`87af3ce0…`),
  `r2_check_out.txt` (`64e0a38e…`), `r2_edges.py` (`91a8eec8…`), `r2_edges_out.txt` (`f9218dae…`), `r2_quotes.py`
  (`678120c1…`). Round 1's scripts in the same folder were read, not reused.
- Rules: REV4 lines 155, 158, 228, 265-266, 276, 427-428, 546-555, 565-574, 632-638, 766-774, 794-796, 806-830;
  ADD:506 (§24 point 2); `review-statistics.md` §6.1; `stat_review_o_power.py`:106-117;
  `scripts/stage1/settings/selector_spec.json` (`cost_conventions`, `option_cost_rule`); `job_runner_stage1.py`
  340-465, 790-821, 940-985, 1120-1135; `seal.py` 1-60; `oext_eval.py` 496-790; `oext_unit.py` 620-660;
  `representation_pass.py` docstring; `safe_lora.py` 846-900; B16 `reading.py`, `contrast.py`, `labels.py`,
  `sensitivities.py`; the builder's `build.py` and `sources.py`.
