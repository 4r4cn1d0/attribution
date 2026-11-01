# D1-readers: independent adversarial verification, round 1

- **Written** 2026-11-01, finished about 09:30 UTC (clock read with `date -u`: 06:25:40 at the start, 09:28:14 before
  writing), by an Opus verifier for the main-study lead (GI VIII), track D1-readers.
- **Object.** `scratchpad/builds/ws-d1` at `55d5f8b`: `git status --porcelain` shows only the untracked folder
  `scripts/stage1_s1/reading_extra/` (17 files); `git diff` is empty. Every file's SHA-256 matches the build report's
  §1 table. The runner `mutation/run_mutants.py` differs from the builder's runner only in the docstring, `REL`, the
  probe module and the tree name (checked with `diff`).
- **Data rules kept.** I opened nothing under `tmp/`, no block-a/ or block-b/ folder, no unit, eval, answer, label,
  guard-sample or judge file, no COMPLETE.json of real data, no plant or decoy path, and no W1 "sealed record" (I read
  the manifest's entries by key and printed only the seven sealed-record paths). Every reader ran on synthetic worlds
  (the builder's `synth_kit`, `extra_kit`) in basetemps under `scratchpad/builds/tmp/vd1-*`, all deleted. No git
  command that changes state; no network, install, pod or API call.

## Verdict: defects (2 in `cost_table`; the other four readers verified)

`fk_power`, `stage3_pick`, `sa_shift` and `cap_reports` compute what their frozen rules say, and my own code
reproduces every value they print on synthetic worlds of all three readings. `cost_table`'s arithmetic is right
under its stated readings, but it prints a wrong-convention C-lean value for the B10 references (D1) and omits a
print that its own cited rule requires (D2). `cap_reports` does not meet the brief's input rule as written (it opens
sealed-class O-ext summaries); the builder disclosed this, it opens nothing the reading does not open anyway, and I
list it as an open point for the lead, not as a defect.

## Defects

### D1 (moderate). `cost_table`: the C-lean cost of the B10 references is their full evaluation over c0

- **Where.** `cost_table.py` `_money()` (line 180) applied by `_b10()` (lines 235-252) to `ref_eval` and `safe_lora`
  jobs (whole and per point) and by `_diagnostics()` to the kinds `ref_eval`, `safe_lora`, `b10_certify` in
  `diagnostics_by_kind`: `c_lean_c0 = measured seconds / measured c0`.
- **Why it is wrong.** A B10 job evaluates through the engine's own `runner.evaluate_checkpoint` and then O-ext
  (`scripts/stage1_s1/eval_adapter.py` docstring; `job_runner_stage1.py`: one `-b10-run` step for `ref_eval`,
  `-evaluate-<point>` steps for `safe_lora`). That is the full evaluation (468 greedy prompts, 3 samples per harm
  prompt, ARC, the guard, then 400 PHTest answers). Under C-lean an evaluation-only reference holds only the lean
  evaluation: REV4:635 ("C-lean (LW-15): training, 200 harm prompts × 1 sample, the task-loss pass, and the greedy
  over-refusal answers with their guard"), LN-07 (REV4:638), and REV4 §10.4, "Reference costs under both
  conventions", row "One evaluation-only state | 0.93 FRE | 0.75 c0" (REV4:825). So the frozen design prices a
  reference's C-lean cost from the lean evaluation, not from the full one. No stated reading covers this case: K2
  covers arms (one lean job by definition) and "diagnostics, whose work is the same under both conventions"; K5 says
  nothing about C-lean. The module docstring cites REV4 7.3 and 10.1-10.3 but not 10.4.
- **Size (E, from the frozen planning prices in `scripts/stage1/settings/selector_spec.json` `cost_conventions`).**
  An evaluation-only state costs about 91.1 + 2,623.2 + 1,516.2 = 4,230.5 s in full and 15 + 2,151.2 = 2,166.2 s in
  the lean form, so the printed value is about 4,230.5 / 2,386.2 = 1.77 c0 where the C-lean cost is about 0.91 c0:
  about 1.95 times too high (about 4 times in §10.4's dev-100 form). REV4:774 reports every menu arm "with its label,
  O, L and cost under both conventions", and REV4:795 lets a cost claim stand only where both conventions agree, so
  the error biases every C-lean comparison against the references.
- **Reproduction** (`verify-D1-readers/repro_cost.py`, run from the ws-d1 root with the venv python,
  `PYTHONDONTWRITEBYTECODE=1 ... -B repro_cost.py <basetemp>`; synthetic `extra_kit.cost_kit(..., "plan_a")`):
  `b10_references["ref_eval b-ref job 2"]`: seconds 3,145.469, `c_lean_c0` 2.901770 = seconds / c0
  (3,145.469 / 1,083.983); `safe_lora b-ref job 3`: 1.742826 = seconds / c0; the same values sit in
  `diagnostics_by_kind`; no reading names B10 under C-lean. **Expected:** `c_lean_c0` null with a reason ("not
  measured: B10 runs the full evaluation; no lean evaluation-only job ran"), or a lean convention stated as a reading
  for the lead (for example §10.4's form: the lean evaluation at the frozen lean prices plus the transform, over the
  measured c0). **Actual:** a full-evaluation number under the C-lean key.
- **Related, smaller (a note, not counted).** `ref-bqi` runs get exactly 1.0 c0 (K2 extended to references), while
  §10.4 prices B+Qi above 1 c0 per seed (6.7-6.9 c0 for 6 seeds, dev-100 form) because its training costs more; at
  the 500-prompt form the gap is a few per cent (E). State it as a reading or price it.

### D2 (low). `cost_table`: REV4:632's FRE comparison line is not printed

- **Rule.** REV4:632: "**1 FRE = 2,934 s** (the median job slot of the three wave-0a R arms; about $1.46 at
  $1.79/h), fixed at W1-P and never re-estimated; the median of all stage-1 R arms is reported beside it (LW-16)."
- **Defect.** No code produces the median of the stage-1 R arms' job slots (I searched `runkit/` and `scripts/` for
  `median`, `FRE_S` and `2934`: only `stage1_rules.py` constants, the selector spec and this reader). `cost_table`'s
  docstring quotes REV4:632 with this clause cut to "...", and its output holds `units` = {`fre_s`, `c0`,
  `approximately_zero_below_fre`} and, for R, the mean, min and max only.
- **Reproduction** (`repro_cost.py`, same kit): `units keys: ['approximately_zero_below_fre', 'c0', 'fre_s']`;
  R's `run` keys: `c_full_fre_max`, `c_full_fre_mean`, `c_full_fre_min`, `c_lean_c0`, `seeds`; the median of the
  synthetic R slots (3,355.87 s) appears nowhere. **Expected:** beside `fre_s`, the median slot of the stage-1 R runs
  in the kit (seconds and FRE), labelled report-only (it never re-estimates FRE). A one-line fix.

## Reader by reader

### 1. `fk_power` (REV4:574): verified

- **Rule check.** REV4:574: "the stage-1 reading prints F_k's planning power at the measured q beside each F_k result
  (report only; after block B, ...)"; REV4:565: "q = the share of prompts on which the arm's refusal flag and θ0's
  differ"; the table REV4:567-572 ("Per comparison (5%)" and "Inside Φ (F_k at 0.375%)"). The docstring quotes are
  verbatim (bold markup dropped). The formula is `stat_review_o_power.py`'s `se_df` and `power_feasible` (item part
  (q − Δ²)/P·100², seed part σ_s²/J with J − 1 df, Satterthwaite, Φ(τ/SE − t(1 − α, df))); Δ = 0, τ = B16's
  `tau_o.star_pp` 5.
- **Independent recomputation** (`verify-D1-readers/indep_check.py`): for plan_a (6 contrasts), block A only (6) and
  plan_b (3), q by hand from `tables.json` (exact), P and J, and all 4 rows per contrast against the review script
  imported by path (its `se_df` with J passed): power within 1e-6, SE within 1e-12, df within 1e-9. F_k's copied
  fields (Φ rejection, p_F, level at rejection, final level, θ0 part) equal B16's, and B16's θ0 estimate equals
  100·(mean of m's cells) − 100·mean(θ0) by hand. All 40 printed values of REV4:569-572 (including the Branch 128
  rows at q + 3 and + 6 pp) are reproduced to two decimals by `planning()`; the tightest margin to the ±0.005 bound is
  0.00025 (σ_s 1.15, 0.375%, q 5%), larger than the < 1e-6 gap between B16's `tdist` and the review's `t_ppf`.
- **Inputs.** `tables.json` and `reading.json` only, bound by B16's `provenance.input_sha256`; B16's schema
  re-validates the tables.

### 2. `stage3_pick` (REV4:428): verified

- **Rule check.** REV4:428 quoted verbatim; REV4:427 ("At most 2 contrasts per family"). Eligibility reads B16's
  `rows[k].u_part.words` ("better" or "worse (U)"); |t| = |est/SE| of `contrasts[k].U`, checked against B16's printed
  t; order (−|t|, P index); at most two.
- **Independent recomputation.** My own picker on B16's output: plan_a ['P1', 'P4'], block A only [], plan_b
  ['P1'], all equal. Nine edge cases on a modified synthetic `reading.json` (`verify-D1-readers/pick_edges.py`): none
  eligible; an exact |t| tie between a worse (U) and a better contrast (lower P index first, both orders); "worse (U)"
  with an equivalence grade and the note (eligible, reading S1); three eligible (the two largest); a favourable
  below-SESOI rejection without "better" (not eligible); an infinite t (first); flags that disagree with the words
  (refused); a printed t that is not est/SE (refused). All as the rule says.

### 3. `sa_shift` (REV4:276): verified

- **Rule check.** REV4:276 quoted verbatim; P4 = U(a0) − U(S1) (REV4:228), so "less in S1's favour" is a negative
  S-a − HB; B16 orients S-a (`contrast_pooled`, vc.mean − vm.mean) and HB (`contrast_fit`, paired mean c − m) the
  same way.
- **Independent recomputation.** From the U table: S-a = mean over a0's seeds − mean over S1's seeds; HB = paired mean
  on the common seeds; their difference equals the printed one (to 1e-9) in plan_a (−0.2103 pp) and block A only
  (−0.7222 pp), and equals a0's extra-seed effect (mean over all a0 seeds − mean over the common seeds), as it must.
  The direction word matches; plan_b prints "not applicable".

### 4. `cap_reports` (REV4:554-555): verified, with an open input question

- **Rule check.** LN-14 and LN-19 quoted verbatim. The bar is recomputed as `oext_eval.transfer_bar` does
  (100·agree ≥ 97·n and 100·move ≤ 2·n), which is ADD §24 point 2's reading at n = 400 (at least 388 agree, move at
  most 8); the tests hit both edges (388/387, move 8/9).
- **Independent recomputation.** My own walk of the synthetic kit (plan.json outputs → folder → summary) for plan_a,
  block A only and plan_b under Branch 128 and block A only under Branch full: pooled and per-arm/reference
  `prompts_with_both_forms`, `changed` and shares equal mine; every unit's planted `flag_change` is copied; the LN-14
  pass equals mine; Branch full prints "not applicable" and PHTest shares.
- **What it opens** (audit hook on every `open`/`listdir`/`scandir`, `verify-D1-readers/open_audit.py`, plan_a world):
  under the kit only `plan.json`, the two seals, 76 COMPLETE.json, 75 `oext_summary.json` and 1
  `oext_transfer_summary.json`; no folder listing; no answer, guard or judge file. Outside the kit: `sources.json`
  and B16's settings.
- **Open point (not a defect).** These are sealed-class files, so the brief's input rule is not met as written; the
  values exist nowhere else, the reader needs the builder's `sources.json` (so it cannot run before the input build
  opens the outcomes), and it reads the same summaries the builder reads plus θ0's transfer summary. The lead's
  1 Nov ruling (FOCUS at main `7fbff5a`, after this worktree's commit) puts `tmp/stage1-olmo/retrieved/` on the
  never-open list; reading C5 needs an explicit exception for the reading script, or the fallback deviation.

### 5. `cost_table`: defects D1 and D2; otherwise verified

- **Independent recomputation** (synthetic cost kits, plan_a and block A only): c0, every arm's C-full mean
  (slot / 2,934 s), every diagnostic total by kind and L1's whole charge equal mine. The charging map matches REV4:127,
  :130-131 and the representation pass's own docstring ("serves L1 (REQ-10), S3 (REQ-11), DataShield-style
  (REQ-12)"). K2 (a run = 1 c0) matches the frozen selector spec's default C-lean variant "a" (a full run is the lean
  job itself).
- **What it opens** (same audit): `plan.json`, the two seals and 56 `cost-ledger.json`; no COMPLETE.json, no listing.

## Notes and open points (not counted as defects)

1. **`cost_table` before the reading.** The README says "any time (outcome-free)". It opens `seals/` and
   `retrieved/` (ledgers only), both on the agents' never-open list. Also, the per-run stage split (the `-oext` and
   `-calibrate` step seconds) tracks answer lengths, and refusals are short, so a pre-reading run carries a weak
   outcome signal. REV4:158 permits reading ledgers, so this is the lead's call: run it inside the reading, or do not
   open its output before the reading.
2. **`ref_eval` includes a0's regeneration.** REV4:816 reports a0's regeneration apart; the readable ledger cannot
   split it (one `-b10-run` step); the printed record does not say so (only K5's text).
3. **Plan-B split inconsistent with K3.** `_diagnostics` builds the sharers from `CHARGES`, not from the reading's
   arms: under plan_b, S4's untuned-answers split is halved with S3, which is not a plan-B arm. Reproduction:
   `_diagnostics` with one 1,000 s untuned job gives S4 split 500 s, `shared_with ['S3', 'S4']`, while
   `design('plan_b').arms` has no S3. Plan A is recorded, so this reading is not affected.
4. **Mac work.** H1 and S1 print 0 s with `approximately_zero` true, while K3 says "not charged"; REV4:796 says every
   pool filter is charged in full. Printing "no GPU ledger (Mac CPU)" would be clearer.
5. **A kind whose jobs all crashed** prints 0 s and "≈ 0" in `diagnostics_by_kind` (edge case).
6. **`fk_power` readings F2-F4** (the reading's own P and J; no +3/+6 rows under Branch 128; both levels printed,
   while F_k's own power is the inside-Φ column) are defensible and labelled; the lead rules them.
7. **`stage3_pick` S1 against `hb_claim` R3.** The literal REV4:428 supports S1 ("worse (U)" with a grade is
   eligible).
8. **`sa_shift`.** The −0.28 pp expectation was computed under D0 for the full design; under the block-A-only reading
   the measured shift (a0's 4 seeds against 3) is not comparable. The output names "computed_under D0".
9. **Provenance.** `bound_reading` checks the settings pin and the sealed contrasts, not `reading.json`'s B16 module
   hashes against the imported B16. This is harmless while B16 stays byte-identical (the D-5 ruling keeps it so).
10. **Real-format assumptions checked by code reading** (the builder's open point 8). COMPLETE.json holds the result
    keys at the top level (`runner._finish`), so `dev100_route`, `command`, `state` and `summary_file` are where the
    readers look. The transfer pass writes `job-I/transfer` (`job_runner_stage1.py`:369-371) into outputs. A ledger is
    written for every started job, but its SHA-256 enters outputs only when the job is complete; crashed jobs are not
    counted. `record_done` requires every non-.safetensors output in the pulled tree, so a not-pulled job's ledger is
    present. `seal.py` writes `class` per file with `*cost-ledger*.json` readable. Engines X and Y have identical O-ext
    route texts, so the one-route check holds with B+Qi. Not tested on real files.
11. **Stdout.** The pick names and the LN-14 bar word print on stdout. B16 prints headline words and `hb_claim`
    prints sentences, so this matches the neighbouring readers.
12. **B10 references' `dev100_route`** prints null (B10 evaluates the dev 100 itself).

## Acceptance criteria (from the brief)

| Criterion | State |
|---|---|
| New package; no edit to B16, the builder or any pinned file | passed (`git status`, `git diff`, hashes) |
| Each reads only text-free documents of the reading and readable ledgers | passed for fk_power, stage3_pick, sa_shift, cost_table (ledgers only, plus plan.json and seals); **not met as written for cap_reports** (sealed-class summaries; disclosed; open point) |
| Values only into its own output document; exclusive create; canonical JSON | passed (B16's `canonical_json`; `open(..., "xb")`; the words on stdout match the neighbours) |
| Frozen rule quoted in each docstring with its source line | passed (checked verbatim); cost_table's quote of :632 elides the print it then omits (D2), and §10.4 is not cited (D1) |
| Tests on synthetic documents | passed: 101 passed (16.04 s); collect-only of the three reading suites 557 |
| Ambiguities read literally and listed | passed, except D1's C-lean case for B10, which no reading covers |
| Values correct against independent code | passed for every printed value except D1's C-lean B10 values |

## Commands I ran (all exit 0 unless noted)

| Command | Result |
|---|---|
| `git -C ws-d1 status --porcelain`, `log`, `diff --stat`; `git -C main log/diff --stat 55d5f8b..38e160d` | only `reading_extra/` untracked; main differs from 55d5f8b only in FOCUS.md |
| venv python: manifest entries by key (roles; sealed-record paths only) | 7 sealed records listed, none opened |
| `awk`/`grep`/`sed` on REV4, review-statistics, `stat_review_o_power.py`, ADD, FOCUS diff, the code | rule texts and code read |
| `pytest -q -p no:cacheprovider --basetemp=builds/tmp/vd1-tests-1 scripts/stage1_s1/reading_extra/tests` | 101 passed in 16.04 s; basetemp 327 MB, deleted |
| `indep_check.py builds/tmp/vd1-indep-1` | exit 0; 2 FAIL lines were my own check's bug (numpy bool with `is`), fixed |
| `indep_check.py builds/tmp/vd1-indep-2` | 0 failures in all checks (the cost checks included); the saved `verify-D1-readers/indep_check_out.txt` holds the 171 non-cost PASS lines |
| `pick_edges.py <plan_a reading.json>` | 9/9 PASS |
| `open_audit.py builds/tmp/vd1-audit` | exit 0 0; the file lists above |
| `repro_cost.py builds/tmp/vd1-repro-cost` | D1 and D2 reproduced |
| python: `_diagnostics` with a stub ledger (note 3) | S4 split 500 s, shared with S3 |
| `pytest --collect-only` on reading_extra, reading_input and reading tests | 557 collected |
| python: margin of the REV4 table check | smallest margin 0.00025 |
| `shasum -a 256`, `diff` of the two mutation runners, `date -u` | as above |

I did not re-run the mutation spec (the lead runs specs). I checked the five shard reports: 38 entries, 37 killed, 1
expected survivor (`RX-common-exclusive`), spec SHA-256 `1b7bfd84…` in each.

## Evidence paths

- My code and output: `scratchpad/builds/verify-D1-readers/indep_check.py`, `indep_check_out.txt`,
  `pick_edges.py`, `open_audit.py`, `repro_cost.py`.
- Rules: REV4 lines 228, 265-276, 427-428, 554-555, 565-574, 632-638, 774, 793-799, 810-830, 1257, 1268; ADD line
  506 (§24 point 2); `selector_spec.json` `cost_conventions`; `eval_adapter.py` docstring;
  `job_runner_stage1.py` 345-420, 786-821, 1120-1140; `seal.py` 61-145; `oext_eval.py` 496-790.
