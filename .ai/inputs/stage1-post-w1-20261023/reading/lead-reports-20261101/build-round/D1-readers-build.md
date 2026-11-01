# D1-readers: pinned readers for the reading-time outputs that no code produced

- **Written** 2026-11-01, about 06:25 UTC (clock checked with `date -u` at 06:22:44 UTC), by an Opus worker for the
  main-study lead (GI VIII), track D1-readers.
- **Worktree** `scratchpad/builds/ws-d1` (detached at `55d5f8b`). Everything is new and untracked under
  `scripts/stage1_s1/reading_extra/`. No other file changed (`git status --porcelain` shows only that folder). No git
  command that changes state was run.
- **Data rules kept.** I opened nothing under `tmp/`, no block-a/ or block-b/ folder, no unit, eval, answer, label,
  guard-sample, judge or COMPLETE.json file, no hidden or selector bank, no plant or decoy path, and no W1 "sealed
  record". I read code, settings, REV4, ADD, FOCUS (the entries cited), the lead's plan, the reports named in the
  brief, the review-statistics script `stat_review_o_power.py` and its output, and two MANIFEST.json entries by key
  (`selector_spec.json`: role settings, SHA-256 `b4bd06c3…`). Every test ran on synthetic data in basetemps under
  `scratchpad/builds/tmp/`, each deleted after its run.

## 1. Files (all new; SHA-256 first 16 hex)

| File | SHA-256 | What |
|---|---|---|
| `scripts/stage1_s1/reading_extra/__init__.py` | `b7e3087201412f95` | package docstring: the five readers and what they read |
| `…/common.py` | `087a4c0c555bed23` | B16-output binding (kind, version, sealed reading, settings pin, sealed contrasts, input SHA-256), provenance block, the command-line frame (exclusive create, canonical JSON, exit 0/2, error messages withheld) |
| `…/fk_power.py` | `28d4647341c04f79` | (1) F_k's planning power at the measured q (REV4:574) |
| `…/stage3_pick.py` | `f6236e9ec4f6b0bf` | (2) the stage-3 confirmation pick (REV4:428) |
| `…/cap_reports.py` | `6d4259268606deeb` | (3) LN-14's transfer bar and LN-19's flag-change shares (REV4:554-555) |
| `…/sa_shift.py` | `d3bf468f0e88f2c9` | (4) the S-a shift line (REV4:276) |
| `…/cost_table.py` | `4cfe186091f960e2` | (5) the measured cost per arm under C-full and C-lean |
| `…/README.md` | `d1d681d5fb0f7701` | usage, what each reads and when |
| `…/tests/conftest.py` | `17e7f9a40126c203` | sys.path (repo, this folder, the builder's `synth_kit`); session fixture `pipeline(reading)`: synth kit, builder, B16 |
| `…/tests/extra_kit.py` | `fcd14f6cd7f2a495` | synthetic additions: O-ext `route`/`flag_change` planted into synth_kit worlds (with judge files re-keyed), theta0's transfer pass; a small kit of cost ledgers with seal classes |
| `…/tests/test_fk_power.py` | `d0bfc3eb27ac42cf` | 17 tests |
| `…/tests/test_stage3_pick.py` | `6b5aa20aa9699c40` | 23 tests |
| `…/tests/test_sa_shift.py` | `f782fa3e1ecde59a` | 11 tests |
| `…/tests/test_cap_reports.py` | `d8db4aa38727c679` | 29 tests |
| `…/tests/test_cost_table.py` | `f37c2cd2d5335009` | 21 tests |
| `…/mutation/mutants_reading_extra.json` | `1b7bfd84abc2cdea` | 38 entries (tree `scripts/stage1_s1/reading_extra`) |
| `…/mutation/run_mutants.py` | `5d00d42a24c26522` | the builder's runner with its tree changed (a diff against it shows only the docstring, REL and the probe module) |

2,809 lines in all. B16, the builder, the engine, the kit and every W1 file are untouched.

## 2. Design, reader by reader (each module's docstring quotes its rule with REV4 line numbers)

**Common frame.** Every reader matches `hb_claim.py`: strict JSON in, B16's `canonical_json` out through
`open(..., "xb")` after an `exists()` check; `REFUSED: …` on stderr and exit 2 with nothing written; any other error
prints its type only; stdout is `wrote <file> sha256 <hex>` plus at most words. Outputs carry `rule` (quoted texts),
`readings` (each stated reading with its alternative) and `provenance` (inputs by SHA-256, this package's modules,
B16's settings pin and modules, Python, numpy). Numbers are B16's own where B16 has them (imported, never edited).

1. **`fk_power`** (REV4:574; terms :565-573; also :1257, :1268). Inputs: `tables.json` and `reading.json`, bound by
   B16's `provenance.input_sha256`; the tables go through B16's own `schema.validate`. q per repair arm = the mean
   over its O seeds of the share of the 500 O items where its 0/1 flag differs from theta0's (per seed printed).
   Power = the review-statistics planning formula (`stat_review_o_power.py` se_df / power_feasible: item part
   (q − Δ²)/P·100², seed part σ_s²/J with J−1 df, Satterthwaite, Φ(τ/SE − t(1−α, df))), Δ = 0, τ_O* = 5 from B16's
   settings, rows σ_s = 0 and 1.15 pp at α = 5% and 0.375%. Every run first reproduces REV4's printed rows
   (:569-570) to two decimals or refuses. F_k's result (Φ rejection, p, levels, theta0 part and interval, states) is
   copied beside it by key. *Rejected:* "observed power" with the arm's measured seed SD (not what "planning power"
   says); adding the Branch-128 +3/+6 pp rows (the measured q already holds the cut's changes).
2. **`stage3_pick`** (REV4:428, :427). |t| = |est/SE| of B16's `contrasts[k].U` (checked against B16's printed t);
   eligible = U part words hold "better" or "worse (U)" (B16's flags checked against the words); sort by (−|t|, the
   number after P); take at most two; "none" otherwise. Prints the picked names. *Rejected:* ordering by p-value; the
   headline word instead of the U part.
3. **`cap_reports`** (REV4:554-555). **The values are in no document the reading writes**: oext_eval.py puts
   `flag_change` and `route` in each O-ext pass's `oext_summary.json` and LN-14's `bar` in theta0's
   `oext_transfer_summary.json`; the builder reads the former but copies neither value (M: no `flag_change` or
   `transfer` in `reading_input/`). So the reader takes the builder's `sources.json` as its index, checks the kit is
   the one the record names (plan.json and each seal at the record's SHA-256), maps each recorded COMPLETE.json SHA-256
   to its folder through plan.json, opens it with the builder's own `Kit.folder`/`Folder.json` (COMPLETE.json at
   plan.json's and the seal's SHA-256; the summary listed, sealed, hashed) and requires the summary's SHA-256 to be the
   one the builder's record names. theta0's transfer pass (kind `transfer_report`, `job-I/transfer`) is found by
   plan.json and checked the same way; its `pass` is recomputed from its counts as `oext_eval.transfer_bar` does. Per
   unit, per arm/reference and pooled flag-change shares per source; one route set per branch; each unit's dev-100
   route. Prints `LN-14 transfer bar: passes|fails|not run|not applicable (Branch full)`. *Rejected:* parsing the
   builder's folder labels; reading summaries the record does not name.
4. **`sa_shift`** (REV4:276). The expectation as written (−0.28 pp, D0, M (VR-B)) and beside it the measured
   S-a − HB of P4 from B16's `sensitivities["S-a"]` and `["HB"]` (one subtraction), with its direction word; plan B
   (no P4) prints "not applicable".
5. **`cost_table`** (REV4:103, :158, :631-638, :774, :793-799, :813-816). **Which ledgers:** the kit's
   `job-I/cost-ledger.json` (job_runner_stage1.write_ledger: 8 stages, steps, slot), the only ledger files the seal
   classes readable (seal.py `READABLE_PATTERNS` `*cost-ledger*.json`; the engine's `ledger.jsonl` is sealed class),
   whose SHA-256 record-done copies into plan.json `outputs`. The reader opens plan.json and the seals through the
   builder's `Kit`, then per job of a done host only that ledger, only when the seal classes it readable and lists it
   at plan.json's SHA-256 (a test spies on every file read: only plan.json, the seal and cost ledgers). C-full of a
   run = slot / 2,934 s; C-lean of a run = 1 c0 (reading K2); c0 = the one c0 job's slot; diagnostics by kind in FRE
   and c0; per-arm charges by a pinned map (reading K3) whole and split; A1 from w0b-2's frozen 3.04 h; Safe LoRA per
   point from its steps; "≈ 0" flags below 0.01 FRE. It is outcome-free and can run before the reading.

## 3. Commands run (exit status; all on synthetic data)

| Command | Exit | Result |
|---|---|---|
| `git status`, `git log`, `git rev-parse` (read-only), `git ls-files` with sealed paths filtered out | 0 | worktree at `55d5f8b`, clean before the build |
| venv python: B16 `tdist` + the planning formula at REV4's grid | 0 | reproduces all 20 printed values to two decimals |
| smoke script in `scratchpad/builds/tmp/d1-smoke` (synth block-A-only world, builder, B16, four readers) | 0 | 1.1 s; cap reader refused as expected (synth summaries lack the keys); folder deleted |
| pytest `reading_extra/tests` (first) | 1 | 1 failure (fixture: B10 COMPLETE changes broke judge keys) → `_rejudge` added |
| pytest (second) | 1 | 97 passed, 3 failed (capsys took the fixture's builder lines; a regex; REV4's bold markup) → fixed |
| pytest (third) | 0 | 100 passed, 19.1 s |
| pytest (final, with the route test) | 0 | **101 passed, 13.7 s**; basetemp 327 MB, deleted |
| pytest `--collect-only` on reading_extra + reading_input + reading tests together | 0 | 557 collected, no basename clash |
| `run_mutants.py` shard 0 (10 ids) | 0 | baseline 101 pass; 10 killed; 6 min 49 s |
| shard 1 (10 ids) | 0 | 9 killed, `RX-common-exclusive` survived as expected; 6 min 8 s |
| shard 2 (9 ids) | 0 | 9 killed; 8 min 43 s (machine busy) |
| shard 3a (5 ids), shard 3b (4 ids) | 0 | 5 + 4 killed; 7 min 59 s, 4 min 30 s |
| `shasum -a 256`, `wc -l`, `date -u` | 0 | §1 |

Mutation total: **38 entries, 37 killed, 1 expected survivor, 0 invalid, 0 unexpected**. Reports:
`scratchpad/builds/reports/D1-readers-mutation-shard{0,1,2,3a,3b}.json` (spec SHA-256 `1b7bfd84…` in each). The
survivor is `RX-common-exclusive` ("xb" → "wb"): the `exists()` check before the open still refuses, and no test can
open the race window; it is marked `"expect": "survive"`, as B16's `B16-legal-note-text` is.

Entries by reader: fk_power 10 (q sign, seed part, Satterthwaite, item part, one/two-sided level, the table check, the
1.15 row, the input binding, the 0/1 check, the reading's J); stage3_pick 5 (worse (U) eligible, tie order, at most
two, |t|, the t check); sa_shift 3; cap_reports 8 (both bar edges, the record SHA-256, the plan SHA-256, the share
check, the pooled share with no full form, one route, Branch full); cost_table 9 (readable class, FRE, split, C-lean
without c0, the hash, A1's 3.04 h, a missing ledger, ledger identity, two runs); common 3.

## 4. Acceptance criteria (from the brief)

| Criterion | State |
|---|---|
| New package `scripts/stage1_s1/reading_extra/`; no edit to B16, the builder or any pinned file | passed |
| Each reads only the reading's text-free documents and readable ledgers | **passed for 1, 2, 4, 5; not met as written for 3** (open point 1) |
| Output only into its own document; exclusive create; canonical JSON | passed (tested: second run exits 2, file unchanged) |
| Frozen rule quoted in each module docstring with its source line | passed (tests check the quotes against REV4 where the tree has it) |
| Tests on synthetic documents (builder's synthetic kit and B16 in a basetemp) | passed (101 tests) |
| Ambiguities: the most literal reading, listed as open points | passed (§5) |
| Match the neighbours (docstrings with usage, naming, refusals and exit codes) | passed by my reading; a reviewer should judge |
| Run on the real kit or real documents | not tested (forbidden by the brief) |

## 5. Open points for the lead (rulings before the second stamp)

1. **cap_reports reads sealed summaries (reading C5).** LN-14's bar and LN-19's shares exist only inside the sealed,
   text-free O-ext summaries. The reader opens exactly the summaries the builder's record names (and theta0's
   transfer summary by plan.json and the seal), so it must run inside the reading script after step 2. Default: rule
   it in; fallback: the record states that LN-14 and LN-19 were not read (a deviation). This widens the brief's input
   set, so it is the lead's call.
2. **cost_table, C-lean (K2).** A run costs 1 c0 by the convention (c0 is the measured lean run; no arm's own lean job
   ran, and the readable ledgers lump the engine's training and full evaluation into one "calibrate" step). The
   alternative (the frozen lean price ≈ 2,386 s / measured c0) mixes an estimate with a measurement. Rule one.
3. **cost_table, the charging map (K3).** L1 ← l1_scan + rep_pass; S3 ← untuned_answers + rep_pass; S4 ←
   untuned_answers; A1 ← w0b-2's 3.04 h (an upper: it includes both Gate C scripts); split = equal shares among the
   stage-1 arms that use a job (LS-13's rule for the representation pass, extended to the untuned answers). The
   rep_pass also builds stage 1b's plant/decoy pools, which this split ignores. Mac work (REQ-7, REQ-11's scoring,
   the S-pool, the length sort) has no ledger and is uncharged. Also K1 (slot, not the stage sum), K4 (reused a0/R
   seeds are outside the kit) and K5 (ref_eval has one step for all points and the a0 regeneration, so no per-point
   cost).
4. **stage3_pick S1.** "worse (U)" with an equivalence grade is eligible here; `hb_claim.py`'s R3 reads the same U
   part as "equivalent". The two readers answer different rules, but the lead may want one reading for both.
5. **fk_power F2-F4.** P and J are the reading's own (plan A: 500 and 6, the planning values; block A only and plan B
   differ and are flagged); the rows are the two Branch-full rows at the measured q; the levels are REV4's 5% and
   0.375%, not F_k's own Φ level (F_k starts at weight 0).
6. **sa_shift A1.** The measured S-a − HB is printed beside the expectation; the literal rule prints only the
   expectation.
7. **Runbook and pins.** The R1D script needs these five commands (fk_power, stage3_pick, sa_shift after step 3;
   cap_reports after step 2; cost_table before the reading) with provenance checks, and the second stamp's manifest
   needs `reading_extra/*.py`. The README's commands are the shapes.
8. **Real-format risks, untested.** The fixtures follow the code (oext_eval summaries, oext_unit's completion record,
   write_ledger, seal.py), not real files. In particular: whether every complete, pulled job's ledger is in the
   pulled tree (the reader refuses otherwise, naming host and job only), and whether `transfer_report` ran (FOCUS
   says Branch 128; the reader prints "not run" if no job exists). A no-value rehearsal of `cost_table` on the real
   kit is safe (outcome-free) and would settle the first; `cap_reports` can only run after the outcomes open.
9. **Not built here:** Q7–Q9 and Q12 of the critique (predictions, per-reference HB intervals, Safe LoRA's V/V′,
   the other descriptive reports); token accounting (Q11) is an existing script.
10. **Suites not run by me:** the whole `scripts/stage1_s1` suite (only collection was checked together with B16's
    and the builder's), B16's and the builder's own suites (their code is unchanged).

## 6. Fix round 1 (the verifier's round 1: `scratchpad/builds/reports/D1-readers-verify1.md`)

- **Written** 2026-11-01, about 10:15 UTC (clock read with `date -u` at 10:12:59 UTC), by the same Opus builder, in
  `scratchpad/builds/ws-d1` (still detached at `55d5f8b`; `git status --porcelain` shows only
  `scripts/stage1_s1/reading_extra/`; `git diff` is empty).
- **Data rules kept.** As before: nothing under `tmp/` opened, no sealed record, no outcome file. Every run used the
  synthetic kits in basetemps under `scratchpad/builds/tmp/d1fix-*`, all deleted. No git command that changes state; no
  network, install, pod or API call. Only `cost_table.py`, its tests, the synthetic cost kit, the mutation spec, the
  README and the package docstring changed. B16, the builder, the engine, the kit and every W1 file are untouched.

### 6.1 D1 (moderate): fixed, with one part disputed

**What was wrong.** For a B10 reference job (`ref_eval`, `safe_lora`), `c_lean_c0` was its measured seconds / c0. A
B10 job runs the full evaluation, so that number is C-full work in c0 units. I agree with the verifier.

**The fix (new reading K6).** A B10 state is evaluation-only. Under C-lean it costs one lean state plus its
transform. This is REV4:813's rule ("For an evaluation-only reference: the same minus training, plus its transform")
applied to C-lean's lean job, as REV4 10.4 prices it (:825: 0.75 c0 in the dev-100 form = (15 + 635) / 870 at the
frozen lean prices).
- One lean state = the measured c0 − the frozen lean training price (`LEAN_TRAINING_S` = 220 s: REV4:636;
  `selector_spec.json` `cost_conventions` C-lean variants a and b both hold 220.0, and a test pins it). The output
  prints it as `units.c0.lean_state_s`.
- Safe LoRA, per point: C-full = its measured `-transform-P` + `-evaluate-P` seconds (as before); C-lean = one lean
  state + the measured transform seconds. The whole job: C-full = its slot (as before); C-lean = its slot with each
  `-evaluate-P` step replaced by one lean state. A point without exactly one transform step and one evaluate step now
  refuses (before, it summed to 0 s).
- ref_eval: its one `-b10-run` step holds a0's regeneration and the full evaluation of every point. So its whole
  C-lean value is null with the reason, and each point's C-lean value is one lean state (its scaling or prefix
  transform runs inside the step: about 0). Its per-point C-full value stays null (K5).
- `ref_eval` and `safe_lora` are no longer in `diagnostics_by_kind`; `b10_references` prices them.
- With no c0, or a c0 not above 220 s, every B10 C-lean value is null with the reason.

**Why not the verifier's example form (REV4 10.4's frozen lean evaluation, 2,166.2 s, over the measured c0).** The
frozen lean evaluation is at the full cap. Under Branch 128 the measured c0 is "much less" (REV4:638). Then the
frozen-price form prices one evaluation-only state above a whole lean run. Concrete check (the last lines of
`scratchpad/builds/d1-fix-checks/fix_check_out.txt`): at c0 = 2,386.2 s both forms give 0.9078 c0; at c0 = 1,800 s
the alternative gives 1.2034 c0 and K6 0.8778 c0; at c0 = 1,400 s, 1.5473 c0 against 0.8429 c0. A whole lean run is
1 c0 (K2). K6 keeps one state below one run at any cap. It uses the measurement for everything but the training, and
the training does not depend on the O cap. K6 states the alternative for the lead.

**Disputed part: `b10_certify`.** The verifier also listed `b10_certify` in `diagnostics_by_kind`. It is not a
reference. It is B10's certification mode: "With none of them, an evaluation is the certification mode (D2): it must
reproduce the Gate A unit's U exactly" (`scripts/stage1_s1/eval_adapter.py` docstring; REV4:493, LS-08). No actor
menu holds it (REV4:766-772). So no practitioner pays it under either convention, and C-lean has no lean form of it.
REV4:823 converts a study cost (a0's regeneration, 0.077 h) by its measured work in both units (0.094 FRE and
0.32 c0). So I kept `b10_certify` at its measured seconds / c0 and made the basis explicit: every by-kind entry now
carries `c_lean_basis` (K2: work that the convention does not change). If the lead wants study costs without a c0
column, that is a one-line change.

**The B+Qi note.** Stated as a reading, not priced. K2 now says that recipe G's and B+Qi's training differ from R's
(REV4:827, E) and that the readable ledger cannot split a run's training from its evaluation (one `-calibrate` step).
Each reference's run record carries `c_lean_note`. A price would need the engine's own ledger (sealed class) or an
estimate.

**Hand check** (`scratchpad/builds/d1-fix-checks/fix_check.py`, output `fix_check_out.txt`; the synthetic
`cost_kit` for plan_a, block A only and plan_b; 20 PASS, 0 FAIL): c0 1,083.983 s, lean state 863.983 s. plan_a's Safe
LoRA job: whole C-lean 3.829528 c0 = (slot − 330 + 3 × 863.983) / c0 (the old value 1.742826 = slot / c0, the
verifier's number); each point = (transform + 863.983) / c0. ref_eval: whole null; each point 0.797045 c0 (the old
whole 2.901770, the verifier's number). In the synthetic kit the evaluate steps are 100-120 s, so a lean state is
longer than a "full" evaluation there; on real ledgers it is the other way round. The tests check the formula, not
the size.

### 6.2 D2 (low): fixed

`units.fre_beside` now holds REV4:632's report: `median_slot_s` and `median_slot_fre` (the median job slot of the
complete stage-1 R runs with a ledger in the reading's blocks), `r_runs`, and `report_only` ("1 FRE stays 2,934 s:
fixed at W1-P and never re-estimated"). 1 FRE does not change. Reading K7 states the basis (the reused R units at
1101-1103 ran in wave 0a; a stage-1 slot holds the 400 PHTest answers, LN-33, so it exceeds the wave-0a basis by
design) and the alternative (the median slot without the `-oext` step). The docstring now quotes REV4:632 in full,
with no elision. Hand check: plan_a, 4 R slots, median 3,355.870 s = 1.1438 FRE (the verifier's 3,355.87 s), mean
3,048.540 s; plan_b, 7 R slots, median 2,601.829 s.

### 6.3 The verifier's notes (not counted as defects)

| Note | Action |
|---|---|
| 1: `cost_table` "any time (outcome-free)" | Fixed the claim in the module docstring, the README and the package docstring: it opens no outcome file, but a run's `-oext` seconds track answer lengths (a weak outcome signal), so it runs inside the reading, or its output is not opened before the reading (the lead's call). |
| 2: ref_eval includes a0's regeneration | Every B10 record now has `includes_a0_regeneration: true`; ref_eval has `a0_regeneration_reported_apart: null`, and K5 says why. |
| 3: the plan-B split counts S3 | Fixed: the charges and their split use only the reading's arms (plan B: S4 alone uses the untuned answers; rep_pass is printed by kind only). New plan-B test; the synthetic cost kit now builds plan B's three blocks. |
| 4: H1 and S1 print "≈ 0" while K3 said "not charged" | Their diagnostic now carries `note` (no kit job; Mac CPU, no ledger; 0 GPU-seconds), and K3's text agrees. |
| 5: a kind whose jobs all crashed prints 0 s | Fixed: such a kind prints null with the reason; an arm that it charges gets a null charge and a null total, never 0. |
| 6-12 | No change: the verifier found the readings defensible, or the notes are information only. |
| `cap_reports`' input (open point) | Unchanged: the lead's call (§5 point 1). The lead's 1 Nov ruling puts `tmp/stage1-olmo/retrieved/` on the never-open list (the verifier's report, FOCUS at main `7fbff5a`; I did not re-read FOCUS; this brief's hard rule 1 says the same for agents). `cost_table` also reads there (cost ledgers only) and in `seals/`, so the reading script needs an explicit exception for both readers. |

### 6.4 Files (all still new; SHA-256, first 16 hex)

| File | Before | After |
|---|---|---|
| `cost_table.py` | `4cfe186091f960e2` | `dddbd2003bb2e5eb` |
| `README.md` | `d1d681d5fb0f7701` | `4e3e920c483dbb4b` |
| `__init__.py` | `b7e3087201412f95` | `4b6d8b4c75f8e1f4` |
| `tests/test_cost_table.py` | `f37c2cd2d5335009` | `85d627653c282003` (21 → 31 tests) |
| `tests/extra_kit.py` | `fcd14f6cd7f2a495` | `4ff489219605add9` (plan B's blocks; a `b10_certify` job appended last on the reference host, so no earlier draw moves) |
| `mutation/mutants_reading_extra.json` | `1b7bfd84abc2cdea` | `b62978a4600bf647` (38 → 49 entries) |

Unchanged: `common.py`, `fk_power.py`, `stage3_pick.py`, `sa_shift.py`, `cap_reports.py`, `tests/conftest.py`, the
other four test files and `run_mutants.py`. 3,162 lines in all.

### 6.5 Commands (all on synthetic data)

| Command | Exit | Result |
|---|---|---|
| `git status --porcelain`, `git diff --stat`, `git log -1` (read-only) | 0 | only `reading_extra/` untracked; no tracked change |
| venv python: the W1 manifest entry of `selector_spec.json`, by key | 0 | role "settings" (not a sealed record); its `cost_conventions` read |
| pytest `tests/test_cost_table.py` (basetemp `tmp/d1fix-cost-1`) | 0 | 31 passed, 2.0 s; deleted |
| `d1-fix-checks/fix_check.py`, twice (before and after the `c_lean_basis` edit) | 0, 0 | 20 PASS, 0 FAIL each time |
| pytest `reading_extra/tests`, twice (basetemps `d1fix-suite-1`, `d1fix-suite-2`) | 0, 0 | 111 passed (26.6 s; 34.7 s); 330 MB each, deleted |
| pytest `--collect-only` on the reading_extra, reading_input and reading tests together | 0 | 567 collected (557 + 10), no basename clash |
| the mutation anchor check (each find text once in its file) | 0 | 49 entries, 0 bad |
| `run_mutants.py --only` 6 ids (shard fix1a): on the code before the `c_lean_basis` edit, then on the final code | 0, 0 | 6/6 killed both times (5 min 28 s; 4 min 40 s); baseline 111 tests |
| `run_mutants.py --only` 6 ids (shard fix1b): the same two runs | 0, 0 | 6/6 killed both times (4 min 48 s; 6 min 12 s); baseline 111 tests |
| `shasum -a 256`, `date -u` | 0 | §6.4 |

Shard reports on the final code (spec SHA-256 `b62978a4…` in each):
`scratchpad/builds/reports/D1-readers-mutation-fix1a.json` (RX-cost-split with its new anchor,
RX-cost-b10-lean-full, RX-cost-b10-whole-lean, RX-cost-ref-eval-lean, RX-cost-lean-training,
RX-cost-b10-in-diagnostics) and `scratchpad/builds/reports/D1-readers-mutation-fix1b.json` (RX-cost-fre-median,
RX-cost-users-reading, RX-cost-no-job-zero, RX-cost-safe-steps, RX-cost-mac-note, RX-cost-ref-note). I did not re-run
the other 37 entries (their anchors are unchanged and checked). The round-0 shard reports name 101 tests and the old
spec SHA-256, so the lead's run of the full 49-entry spec replaces them (expected: 48 killed, `RX-common-exclusive`
survives as marked).

### 6.6 Acceptance criteria after the fix

| Criterion | State |
|---|---|
| Values correct against independent code | passed for D1's and D2's new values (`fix_check.py`, 20 PASS); the other readers are unchanged |
| Ambiguities read literally and listed | passed: K6 (B10 under C-lean) and K7 (FRE beside) are stated with their alternatives; K2 states the B+Qi gap |
| Frozen rule quoted with its source line | passed: REV4:632 in full; REV4:636, :813, :823, :825, :827 and :830 added; a test checks the quotes against REV4 and six of their line numbers |
| Tests on synthetic documents | passed: 111 |
| Each reads only the reading's text-free documents and readable ledgers | unchanged (`cap_reports` is still the open point; `cost_table` opens the same files, checked by the spy test) |
| Run on the real kit | not tested (forbidden by the brief) |

### 6.7 Open points that this round adds or changes

1. **K6 (new), for the lead.** B10 under C-lean = the measured c0 − 220 s, plus the transform. Alternatives: REV4
   10.4's frozen-price form (wrong under Branch 128, shown in §6.1) or null.
2. **K7 (new).** The median uses the R runs of the reading's blocks. Alternative: also print the median without the
   `-oext` step.
3. **K2 extended.** A reference trained by another recipe costs 1 c0; B+Qi's extra training is left out (E: a few
   per cent).
4. **Study costs in c0** (`b10_certify`, regenerations, O-only passes, the transfer report, the certification jobs):
   kept at measured seconds / c0, as REV4:823 treats a study cost. Disputed with the verifier; the lead rules.
5. **When `cost_table` runs, and the never-open list.** Run it inside the reading. It reads `tmp/stage1-olmo/seals/`
   and the cost ledgers under `retrieved/`; the 1 Nov ruling needs an exception for it, as for `cap_reports`.
6. **The verifier's `repro_cost.py`** now stops at its own print lines (it formats a null C-lean value and reads
   `diagnostics_by_kind["ref_eval"]`). That is expected after the fix; `d1-fix-checks/fix_check.py` replaces it.
7. **The full spec** (49 entries) is the lead's run.

## 7. Fix round 2 (the lead's ruling R4.2 in `scratchpad/builds/lead-rulings-20261101.md`; the verifier's round 2: `scratchpad/builds/reports/D1-readers-verify2.md`, defect D1 and notes 2, 4, 6)

- **Written** 2026-11-01, about 14:36 UTC (clock read with `date -u`: 14:06:26 UTC before the first edit, 14:34:47 UTC
  after the last check), by the fix-round-2 builder for the main-study lead (GI VIII), track D1-readers (the launcher
  records the model). Worktree `scratchpad/builds/ws-d1`, still detached at `55d5f8b`; `git status --porcelain` shows
  only `scripts/stage1_s1/reading_extra/`; `git diff` is empty. No git command that changes state.
- **Data rules kept.** Nothing under `tmp/` opened, no sealed record, no outcome file, no plan.json or seal of the real
  kit. I read code (the kit's `plan_tool.py`, `stage1_rules.py`, `job_runner_stage1.py`, `oext_eval.py`,
  `scripts/stage1/representation_pass.py`, the builder's `build.py`, B16's settings), REV4, `selector_spec.json`, FOCUS,
  SPF and ADD at `55d5f8b` through `git show`/`git grep` (never from the working directory), and the lead's rulings and
  the three D1 reports. Every run used the synthetic kits in basetemps under `scratchpad/builds/tmp/d1fix2-*`, all
  deleted (the folder now holds only other tracks' files). No network, install, pod or API call.
- **Scope.** Only the three changes ruled: (a) `cost_table.py`, (b) `cap_reports.py`, (c) `cost_table.py`; their
  tests, the synthetic cost kit (one optional parameter), the mutation spec and the README. `__init__.py`, `common.py`,
  the other three readers, their tests, `conftest.py` and `run_mutants.py` are byte-identical to round 1.

### 7.1 (a) `cost_table`: a C-full value per ref_eval point by REV4:813, read literally (new reading K8)

**REV4's own words, checked, and what they fix.**
- *"the same"*: §7.3's C-full, "every in-job stage" of a full run (REV4:633), the O-ext pass included (REV4:634,
  LN-33). The full run an evaluation-only reference is built on is the a0 run at its seed: the kit runs each
  `ref_eval` job on block B's own a0 run at the same seed (`runkit/stage1-olmo/plan_tool.py:168`, round 32's K1:
  "the evaluation-only references (ref_eval, safe_lora) on block B's own a0 runs (the deal's a0 seeds, 1105-1107)";
  `stage1_rules.py:477` `SECOND_PHASE_KINDS`; `plan_tool.py:628` refuses any other seed; the second phase is released
  only after that a0 run is recorded complete). So **the matched a0 run = the complete `a0_arm` job at the same seed
  with a readable ledger in the reading's blocks, and its slot** (K1: start to end inside the pod; the point's own
  evaluation holds the O-ext pass too, `B10_OEXT_KINDS`).
- *"minus training"* under C-full: the frozen C-full training price, `selector_spec.json` `cost_conventions.C-full.
  training_s` = **219.7 s**, "the median training of R_1-R_3" (REV4:804-806: 220.4, 219.7, 216.0 s). Not the lean
  220.0 s (variants a and b), which K6 keeps for C-lean. `FULL_TRAINING_S = 219.7`, pinned by a test to the spec and
  to the median of REV4's table.
- *"plus its transform"*: the job ledger's measured `transform` stage. `job_runner_stage1.write_ledger` fills it from
  `safe_lora_timing.json seconds.total` for Safe LoRA only; a ref_eval point's scaling (a scalar on the adapter
  weights) or prefix (a prompt prefix) runs inside the one `-b10-run` step, so a ref_eval ledger's transform stage is
  0. The reader reads the stage, never assumes it (a planted 7.5 s is added; tested).
- *"over c0"* (the ruling's words): C-full's unit is 1 FRE (REV4:633), so **`c_full_fre` = seconds / 2,934 s is the
  C-full value**; the same seconds over the measured c0 are printed beside it as `seconds_over_c0` with
  `OVER_C0_NOTE` ("for a comparison with the C-lean column only"). The lead picks (open point 1).

**What is printed.** Per ref_eval point (`b10_references[...].per_point[P]`): `seconds`, `c_full_fre`,
`approximately_zero`, `c_full_basis` {`rule`, `a0_run` {seed, host, index, slot_s}, `full_training_s`, `transform_s`,
`transform_basis`, `seconds_over_c0`, `units`}, `alternative_k5` {`seconds` null, `c_full_fre` null, `why` "not
stated: ... (reading K5, the alternative to K8)"}; `c_lean_seconds` and `c_lean_c0` as before (K6, unchanged). A seed
with no complete a0 run with a ledger in the reading's blocks gets `seconds` null with the reason (the seed named),
`a0_run` null, no `seconds_over_c0`; its C-lean value stays. A new block **`b10_per_reference[kind][point]`** gives
the per-reference mean over seeds: `menu_name` (REV4:770's names: "adapter scaling 0.9/0.75/0.5", "SP (the system
prompt prefix)", "Safe LoRA default/conditional/certify"), `seeds`, `jobs`, `c_full_fre_mean/min/max`,
`c_lean_c0_mean/min/max`, `seeds_without_c_full_fre`, `seeds_without_c_lean_c0`; a seed without a value is listed,
not averaged; two complete jobs at one seed refuse (`"ref_eval at 1105: two complete jobs with a ledger"`). Both B10
kinds are in it (Safe LoRA's points from their measured per-point values), so every reference of the Sp and Ow menus
has one line under both conventions. `units.full_training_s` is printed. `RULE` gains REV4:774 as its own entry;
`READINGS` gains K8 and K5 now says its null is the alternative, printed beside K8's value.

**Not changed.** Safe LoRA's per-point C-full stays its measured `-transform-P` + `-evaluate-P` steps (K5): the ruling
names the four ref_eval points, and a measured value beats the proxy where it exists. The REV4:813 form for Safe
LoRA's points is one line if the lead wants it beside the measured one (open point 3).

**Hand check** (`scratchpad/builds/d1-fix2-checks/fix2_check.py`, output `fix2_check_out.txt`; the synthetic plan_a cost
kit with a second ref_eval job at 1106; **63 PASS, 0 FAIL**): c0 1,083.983 s, lean state 863.983 s, full training
219.7 s. ref_eval job 2 (seed 1105): a0 run a-13 job 1, slot 2,568.722 s, transform 0.0 s → 2,349.022 s = 0.800621 FRE
= 2.167028 c0 for each of the four points (the ref_eval slot itself, 3,145.469 s, is the whole job's C-full as before,
and K5's null sits beside each point). Job 5 (seed 1106): a0 slot 3,609.680 s → 3,389.980 s = 1.155412 FRE. Per
reference: mean 0.978017 FRE (min 0.800621, max 1.155412), C-lean mean 0.797045 c0, for each of the four points. In the
synthetic kit every slot is a seeded random draw, so the 813 value and the ref_eval slot differ by chance; on real
ledgers the a0 slot less 219.7 s should sit near one evaluation-only state (REV4:825's 0.93 FRE at the full cap).

### 7.2 (b) `cap_reports`: the LN-19 PHTest line

- `_pooled(blocks, source)` now writes the note per source (`NO_BOTH_FORMS`). For PHTest: "no unit holds both forms
  of this source: under Branch 128 each unit's PHTest answers are made at the cut cap only; theta0's LN-14 transfer
  pass holds both forms of its 400 PHTest answers, and its share is ln14.report.flag_change (copied beside the pooled
  PHTest line as theta0_ln14)". The words "no full answer exists" are gone from every line the reader writes (pooled,
  by arm or reference, readings; tested). The pooled PHTest line carries **`theta0_ln14`** {`prompts_with_both_forms`,
  `changed`, `share`, `source`} copied from `ln14.report.flag_change`; without a report it holds `share` null and
  `why` (LN-14's own text: "not run: ..." or "LN-14 runs under Branch 128 only ..."). C1 and the module docstring say
  so.
- **Kept as a copy:** each unit's `flag_change.phtest.note` is oext_eval's own text, copied by key from the sealed
  summary ("generated at the cut cap: no full answer exists"; `oext_eval.py:497-501`). It is true of that unit, and
  the reader re-forms no value or text of a source, so it stays (open point 2).

### 7.3 (c) K3's split denominator and the anchor job

- K3 now says the split's denominator is the reading's arms only, and why it is an upper: the representation pass
  also serves **DataShield-style** (REQ-12, a stage-1c secondary arm), a reproduction of Gate C's representation score
  (`scripts/stage1/representation_pass.py`'s docstring) and stage 1b's plant and decoy pools (the kit's D-2 route),
  none a stage-1 arm; the output states it as `charging.split_denominator`.
- The output names REV4:796's anchor job: `charging.anchor_job` {`what`: Gate B's anchor job, host anchor-1, launched
  2026-10-10 13:29 UTC, done 14:01 UTC: the untuned model's greedy answers to the 128 sealed PKU anchor prompts, kept
  64 harmful + 64 safe, the sealed bank `anchor_bank.json` 2cf96336...; `serves`: A1's bi-anchored score and L1's
  layer scan on the 64 harmful anchor prompts (REV4:62, :127); `charged_here` null; `why`: REV4:796 charges every
  anchor job in full, it ran in Gate B before stage 1 and outside this kit, so no stage-1 ledger holds it and the
  table does not price it (the lead prices it from Gate B's record: the job took 2.2 min, pod overhead 26.0 min on
  anchor-1, REV4:808) beside A1's w0b-2 charge; `sources`: REV4:62, :127, :796, :808; SPF:211, :250; FOCUS:198-199
  at `55d5f8b`}. K3's text names it too.

### 7.4 Files (SHA-256, first 16 hex; the full lists are `scratchpad/builds/d1-fix2-checks/sha256-before.txt` and `sha256-after.txt`, taken with `shasum -a 256` before the first edit and after the last)

| File | Before | After |
|---|---|---|
| `cost_table.py` | `dddbd2003bb2e5eb` | `d0a983217cf65764` (540 lines after) |
| `cap_reports.py` | `6d4259268606deeb` | `c61b3a8a3d3b4bb0` (334 lines after) |
| `README.md` | `4e3e920c483dbb4b` | `fb86f956a42c0310` |
| `tests/test_cost_table.py` | `85d627653c282003` | `74dbb6d72e21959f` (31 → 39 tests) |
| `tests/test_cap_reports.py` | `d8db4aa38727c679` | `46ddfc23374e4805` (29 → 30 tests) |
| `tests/extra_kit.py` | `4ff489219605add9` | `5765ad0ef5b7cd86` (`cost_kit(..., extra_ref_eval_seeds=())`: extra ref_eval jobs appended last, so no earlier draw moves; the default kits are byte-identical) |
| `mutation/mutants_reading_extra.json` | `b62978a4600bf647` | `4dca4cd8b01d6406` (49 → 62 entries) |
| `__init__.py` | `4b6d8b4c75f8e1f4` | unchanged |
| `common.py` | `087a4c0c555bed23` | unchanged |
| `fk_power.py` | `28d4647341c04f79` | unchanged |
| `stage3_pick.py` | `f6236e9ec4f6b0bf` | unchanged |
| `sa_shift.py` | `d3bf468f0e88f2c9` | unchanged |
| `mutation/run_mutants.py` | `5d00d42a24c26522` | unchanged |
| `tests/conftest.py` | `17e7f9a40126c203` | unchanged |
| `tests/test_fk_power.py` | `d0bfc3eb27ac42cf` | unchanged |
| `tests/test_sa_shift.py` | `f782fa3e1ecde59a` | unchanged |
| `tests/test_stage3_pick.py` | `6b5aa20aa9699c40` | unchanged |

3,604 lines in all (3,166 before). B16, the builder, the engine, the kit and every W1 file are untouched.

Full after-hashes of all 17 files (`shasum -a 256`, paths relative to the ws-d1 root; the same list is `d1-fix2-checks/sha256-after.txt`):
```
fb86f956a42c0310beca865900672086efdedc497e3a3aae22784e4b13c6d251  scripts/stage1_s1/reading_extra/README.md
4b6d8b4c75f8e1f4e0f76a78ae03fa5812f1a3173920d21e67b3890e2e819321  scripts/stage1_s1/reading_extra/__init__.py
c61b3a8a3d3b4bb02c4780b49fa9c6e40e108b50202d14b7cdf777cd15f79dda  scripts/stage1_s1/reading_extra/cap_reports.py
087a4c0c555bed236b2b465298bcf1aa5ff58a3f20effae923fded1545272d67  scripts/stage1_s1/reading_extra/common.py
d0a983217cf657649ae8283f38046788addf41b5ab7da45b244f0405483f17b7  scripts/stage1_s1/reading_extra/cost_table.py
28d4647341c04f793762faa61def92453b886a37fa1e7eca9bb51bd2c2a45819  scripts/stage1_s1/reading_extra/fk_power.py
4dca4cd8b01d64062bc915dff54045b99af9f72a03d8c46f41daffdf6fdeb560  scripts/stage1_s1/reading_extra/mutation/mutants_reading_extra.json
5d00d42a24c26522745513646b27b23e5ac41137dc22d7dd7aa295e596a47471  scripts/stage1_s1/reading_extra/mutation/run_mutants.py
d3bf468f0e88f2c94776144a7dd55fba3be2e80a779314ae4d098366ecce0b2a  scripts/stage1_s1/reading_extra/sa_shift.py
f6236e9ec4f6b0bf3e5737249f20aa16dc4d649905399307f347951a9181f03f  scripts/stage1_s1/reading_extra/stage3_pick.py
17e7f9a40126c203f3a8d0432a26505e6ba6f5c6f332981e23ad24e997418fa4  scripts/stage1_s1/reading_extra/tests/conftest.py
5765ad0ef5b7cd86342918774301bc88a198fe860361b9efd55788c8b926b957  scripts/stage1_s1/reading_extra/tests/extra_kit.py
46ddfc23374e48052882ca0e22b2243b39d7ad85ac9c916c2b681efbb8bf2c6c  scripts/stage1_s1/reading_extra/tests/test_cap_reports.py
74dbb6d72e21959fe90be7e67f849d93c7e534835112f51a783c2f2c4c80febe  scripts/stage1_s1/reading_extra/tests/test_cost_table.py
d0bfc3eb27ac42cf4d01e182ec293a9f7f62c12c54bfe530f35bb17087d25978  scripts/stage1_s1/reading_extra/tests/test_fk_power.py
f782fa3e1ecde59a8f934704742ae9a1362cf19753455a3d712b7e948e3c8f66  scripts/stage1_s1/reading_extra/tests/test_sa_shift.py
6b5aa20aa9699c400902406db1f4a01b363c67fe516e8d0587492943080c1c6c  scripts/stage1_s1/reading_extra/tests/test_stage3_pick.py
```
(This block replaced a first version, written minutes earlier, whose `cost_table.py` line held a mistyped hash; the file lists taken with `shasum` are the record.)

### 7.5 Commands (all exit 0 unless noted; all on synthetic data)

| Command | Exit | Result |
|---|---|---|
| `git status --porcelain`, `git rev-parse HEAD`, `git diff --stat` in ws-d1 (read-only; before and after) | 0 | only `reading_extra/` untracked; `55d5f8b`; no tracked change |
| `shasum -a 256` of the 17 files before any edit → `sha256-before.txt`; `date -u` | 0 | equal to §1 and §6.4 |
| `git -C <main> show 55d5f8b:<REV4>` (lines 625-640, 760-835; grep "anchor", "DataShield"); `selector_spec.json` `cost_conventions` by key; the kit's `plan_tool.py`, `stage1_rules.py`, `job_runner_stage1.py` (ledger and ref_eval lines), `oext_eval.py:496-501`, `representation_pass.py` docstring, `build.py` labels; FOCUS, SPF, ADD grep "anchor" | 0 | the rule texts and the kit facts cited above |
| pytest `tests/test_cost_table.py tests/test_cap_reports.py` (basetemp `tmp/d1fix2-cost-cap-1`, deleted) | 0 | 69 passed, 13.6 s |
| mutation anchor check (each find text once in its file), twice | 0 | first: 62 entries, 1 bad (`RX-cost-ref-eval-lean`: its find line was replaced by the fix) → re-anchored to the new per-point call; second: 62 entries, 0 bad |
| pytest `reading_extra/tests` (basetemp `tmp/d1fix2-suite-1`, 332 MB, deleted) | 0 | **120 passed, 26.9 s** (111 + 9) |
| pytest `--collect-only` on reading_extra, reading_input and reading tests (basetemp deleted) | 0 | 576 collected (567 + 9), no basename clash |
| `d1-fix2-checks/fix2_check.py` (basetemps `d1fix2-check-1..3`, deleted) | 1, 1, 0 | the first run: my own path bug (`parents[2]`); the second: 62 PASS and 1 FAIL from my check's scope (it searched the units' copied notes, §7.2); the third, with the scope narrowed to the reader's own lines: **63 PASS, 0 FAIL** |
| `run_mutants.py --only` shard fix2a (5 ids; scratch `tmp/d1fix2-mut-a`, deleted) | 0 | baseline 120 pass; 5/5 killed; 3 min 9 s |
| shard fix2b (5 ids) | 0 | 5/5 killed; 3 min 13 s |
| shard fix2c (4 ids: 3 new, 1 re-anchored) | 0 | 4/4 killed; 2 min 36 s |
| `shasum -a 256` → `sha256-after.txt`; the shard reports' `spec_sha256` and baseline tree hashes against the current files; `wc -l`; `date -u` | 0 | §7.4; all three reports name spec `4dca4cd8…` and the current tree |

### 7.6 Mutation

13 new entries and 1 re-anchored, all killed (**14/14; 0 invalid; 0 unexpected**), each on the final code; the shard
reports are `scratchpad/builds/reports/D1-readers-mutation-fix2{a,b,c}.json` (spec SHA-256 `4dca4cd8…`, baseline 120
tests, the baseline tree hashes equal `sha256-after.txt`).
- fix2a: `RX-cost-813-training` (219.7 → the lean 220.0), `RX-cost-813-any-a0` (the first a0 run, not the same seed),
  `RX-cost-813-no-training` (the training not subtracted), `RX-cost-813-no-transform` (the transform not added),
  `RX-cost-813-over-fre` (`seconds_over_c0` over 1 FRE).
- fix2b: `RX-cost-813-k5-value` (K5's alternative prints the value), `RX-cost-813-mean` (the mean is the maximum),
  `RX-cost-813-two-seeds` (two jobs at one seed both enter the mean), `RX-cost-k3-datashield` (K3 loses
  "DataShield-style"), `RX-cost-anchor-job` (the anchor job not in the output).
- fix2c: `RX-cost-split-denominator` (the denominator not stated), `RX-cap-phtest-note` (the old "no full answer
  exists" line), `RX-cap-theta0-ln14` (the pooled PHTest line without theta0's share), and the re-anchored
  `RX-cost-ref-eval-lean` (a ref_eval point costs 1 c0 under C-lean).
The other 48 entries' anchors are checked (0 bad) and were not re-run; the lead's run of the full 62-entry spec is the
record (expected: 61 killed, `RX-common-exclusive` survives as marked).

### 7.7 Acceptance criteria (the ruling R4.2)

| Criterion | State |
|---|---|
| A C-full value per point for adapter scaling 0.9, 0.75, 0.5 and SP by REV4:813 read literally; the a0 run slot and the training price as REV4's own words give them | passed (K8; `fix2_check.py` by hand; tests) |
| A per-reference mean over seeds | passed (`b10_per_reference`, both B10 kinds) |
| "null: not stated" printed beside it as the alternative reading (K5) | passed (`alternative_k5`) |
| The reading stated in the output and the module docstring with REV4:774 and :813 | passed (docstring, `RULE`, K8, K5) |
| The LN-19 PHTest line fixed | passed for every line the reader writes; the units' copied oext_eval notes stay copies (open point 2) |
| K3's split denominator named "DataShield-style"; the anchor job named in the output | passed (K3, `charging.split_denominator`, `charging.anchor_job`) |
| Change nothing else | passed by my reading: no other reader, value or key changed; the per-point record of a ref_eval point gains keys, Safe LoRA's record is unchanged |
| Tests and mutation entries for each change; the suite and the entries run in shards within 10 minutes | passed (120 tests; 14/14 killed; the longest shard 3 min 13 s) |
| Match the surrounding code and records | passed by my reading; refusals and exit codes unchanged (`common.main_frame`) |
| Run on the real kit | not tested (forbidden) |

### 7.8 Open points and questions for the lead

1. **"over c0" in R4.2.** C-full's unit is 1 FRE (REV4:633, :825's C-full column), so the value is printed as
   `c_full_fre`, with the same seconds over the measured c0 beside it (`seconds_over_c0`, labelled as a comparison
   only). If the lead meant the c0 number as the value, it is there; if the extra field is unwanted, it is one line.
2. **The units' copied PHTest note** ("generated at the cut cap: no full answer exists") is oext_eval's own text,
   copied by key from each sealed summary, true of that unit; the reader's own lines point to theta0's LN-14 pass. If
   the lead wants the copied text replaced too, it is a one-line map, but then a copied value would be re-formed.
3. **Safe LoRA's points** keep their measured per-point C-full; the REV4:813 form (the same seed's a0 slot − 219.7 s +
   the transform step) could be printed beside it for a check of the 813 form against a measured evaluation-only state.
4. **The matched a0 slot holds its O-ext pass** (K1), as the point's own evaluation does (B10's O-ext flags). The
   alternative, the a0 slot without its `-oext` step, is not printed.
5. **Real-kit assumption, untested:** every ref_eval job's seed has a complete `a0_arm` job with a readable ledger in
   block B (the kit's K1 gate releases the second phase only after that a0 run is recorded complete). An absent a0 run
   prints null with the reason, never a refusal; a crashed-then-re-run a0 at one seed is one complete run (as before).
6. **Both B10 kinds in `b10_per_reference`** (Safe LoRA's three points from their measured values), so the menus can
   be filled from one block; the ruling asked for the ref_eval references' mean, and Safe LoRA's adds nothing new.
7. **The full 62-entry spec** is the lead's run.
