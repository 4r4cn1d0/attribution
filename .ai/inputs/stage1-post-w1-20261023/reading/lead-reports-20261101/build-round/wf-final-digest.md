### A-coherent v1
-- report_path: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/A-coherent-verify1.md
-- verdict: defects
-- defects:
   * D1 (test harness, not reading code). The session fixture `built` (scripts/stage1_s1/reading_input/tests/test_coherent.py:181-185) asserts the builder's exit code during fixture setup. Any mutant that makes the builder refuse therefore gives 30 setup ERRORS instead of failures. The official runner's rule is: killed = exit 1, >= 1 failure, 0 errors; anything else = invalid. Under it, 4 spec entries are INVALID: 3 new ones (RI-coh-prompt-order, RI-coh-n-counts-failing, RI-coh-u-fail-every-unsafe) and the pre-existing RI-o-cut-rule, which was killed cleanly before D-5. Reproduction, from ws-a: `python -B scripts/stage1_s1/reading_input/mutation/run_mutants.py --spec scripts/stage1_s1/reading_input/mutation/mutants_reading_input.json --scratch <tmp> --report <file> --timeout 270 --only RI-coh-prompt-order`. Expected: killed. Actual: the baseline passes (277 tests), and the mutant is 'invalid' (exit 1, 43 failures, 30 errors); report verify-A-coherent/official-runner-RI-coh-prompt-order.json (SHA-256 prefix 0cc2c192c95ddafe). The other three show the same 30 errors with verify-A-coherent/spec_errors.py, which runs the new test files without -x. The builder's '25 of 25 killed' holds only with its -x quick runner. Fix, shown in a scratch copy: replace the assertion with `if main(...) != 0: return None`. All four entries then become clean kills (73-74 failures, 0 errors), and the unmutated test_coherent.py still passes (37 passed). No reading number changes, but as built the lead's D-5 gate ('specs: 0 invalid'; fallback (c+) if D-5 is not verified after one fix round) cannot pass.
-- summary: I found one defect, D1, in the test harness; no reading output is wrong. The D-5 reader and the builder's side document are correct as far as I could test, but 4 mutation spec entries will be invalid under the official runner until a one-line fixture change is made.

**What holds:**
- **Independent reference.** I wrote my own implementation from the rulings; it does not import the builder's new modules. It agrees with sg_coherent.sg on 30 synthetic readings: 159 S-G coherent contrasts and 318 adverse-corner contrasts, including paired fallbacks, not-computable cases and O/L rejections. Estimates are equal. The largest differences are 3.3e-12 pp at the interval ends and 2.6e-14 in p. Words, headline words and Phi rejections are identical.
- **All-coherent identity.** With every answer coherent, S-G coherent equals B16's primary U_k bit for bit in 4 readings (plan A, plan B and block A only).
- **B16 unchanged.** All 33 files match 55d5f8b blob by blob.
- **Builder output.** tables.json is byte-identical to the pre-change builder's (plan A and plan B, with and without the overlap block). The counts equal my own count of the raw synthetic answers.
- **G3a corners.** 'Against better' and 'against worse' match PREREG:149 and gate_b_reading.py's G3a_localized and G3a_diffuse. a0 takes the corner's direction in P4.
- **Never stops the reading.** B16 runs first and is unchanged. A numeric failure in the reader prints 'not computable' with p = 1, and the file is still written.
- **Suites.** reading_input 277 passed and B16 261 passed.
- **Simulation evidence.** The builder's simulation evidence reproduces exactly.

**Coverage target (0.88-0.92 coverage, tail at most 1.5 times the primary's):**
- **Plan A meets it everywhere I tried.** That is my own 7 new worlds at 10,000 replicates each (both arms or the comparator failing, seed-varying and outcome-linked failures, the removal cluster), and the builder's two hardest worlds at 10,000.
- **Block A only misses it**, and the miss is real at 10,000 replicates: tail ratios 1.41-2.02, coverage down to 0.880. That reading cannot run, because the builder refuses it once block B is sealed. Whether the fallback trigger covers it is the lead's ruling.

**D1.** The fixture `built` in tests/test_coherent.py asserts during setup, so 4 spec entries give errors rather than failures:
- 3 of the 25 new ones;
- the pre-existing RI-o-cut-rule.

The official runner, run on RI-coh-prompt-order, confirmed this. The builder's '25 of 25 killed' holds only with -x. The one-line fix makes all four clean kills; I showed this in a scratch copy only. As built, the lead's 'specs: 0 invalid' gate for D-5 cannot pass.

**Notes in the report:**
- Four test gaps found by my own near mutants:
  - the paired fallback's prompt part;
  - the measure (O or L) named in S-G's headline;
  - plan B's familywise sides;
  - a headline that differs while the words do not.

  On the first two paths my reference shows the code is right; the last two are not exercised by my reference either.
- Binding limits of the side-document check: it accepts version true, items 200.0 and any rule text, and cannot see a failure moved between prompts.
- The theoretical coupling of the builder's coherent check to the primary input build.
- The relabel exists only in sg_coherent.json, not in B16's rows.
- The runbook's expected-output list must change.

**Files** (in /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/verify-A-coherent/): the reference (ref_sg.py, gen.py, compare.py, compare_ol.py) and the simulation (my_sim.py), with their results (compare_run1.txt, my_sim_*_10000.json, builder-sim-*.json); the mutation checks (spec_errors.py, spec_errors_fix.py, my_mutants.py, official-runner-RI-coh-prompt-order.json).
### A-coherent fix
-- report_path: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/A-coherent-build.md
-- summary: Fix round 1 for track A-coherent (D-5). The "Fix round 1" section (F.0-F.5) is appended to the build report.

D1, the one listed defect, is fixed. The fixture `built` in test_coherent.py now returns the built world, or a text that says why the build failed; it never raises. Its three tests read it through `need(built)`, so a refusing mutant gives test failures, not setup errors.

I also fixed a second source the verifier did not list. After a failed build, the getter `pipeline` in test_sg_coherent.py rebuilt the world in each of about 38 later tests, which pushes a mutant run toward the runner's timeout. A failed build is now kept: the first test shows the original traceback, and each later test fails at once.

Under the official run_mutants.py, the four entries the verifier found INVALID are now killed with 0 errors: RI-coh-prompt-order (79 failures), RI-coh-n-counts-failing (80), RI-coh-u-fail-every-unsafe (80) and RI-o-cut-rule (205). The runner exited 0.

N1's test gaps are closed:
- V5: the paired fallback's prompt part is checked against a numpy-only reference.
- V1: a direct `reread` test under plan B puts the SE on the knife edge between 3 and 6 familywise sides.
- V2: O or L rejects alone, and the headline must name that measure. This is tested both by hand and end-to-end, with B16's Phi rejections recomputed so the binding holds.
- V10: the words stay the same while the headline differs, so the row must differ from the primary.

The verifier's own probe now kills 10 of its 10 near mutants.

N3 is tightened. `coherent.check` refuses `version`, `items` or `samples_per_prompt` that is not a JSON integer, and any rule text other than `coherent.RULE`. The module doc now states the full binding limit: per-prompt placement of failures cannot be checked against tables.json.

The spec grows from 41 to 47 entries. All 6 new entries are killed under the official runner with 0 errors. All 31 new-code entries are killed with 0 errors without -x, and the new files add no error to any of the 16 old entries.

Suites: reading_input 284 passed, exit 0, on the final files. B16: 261 passed (198 + 63), exit 0. B16 is byte-identical to 55d5f8b.

No number or word of a reading changes: sg_coherent.py, items.py, build.py, __main__.py and __init__.py keep their hashes. Only the provenance records the new coherent.py hash.

Notes N2 and N4-N9 need no code change; the reason for each is in table F.1. Report §5 and §7 row 6 ("25 of 25 killed") held only under -x; F.1 corrects them.
-- changed_files:
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/ws-a/scripts/stage1_s1/reading_input/coherent.py
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/ws-a/scripts/stage1_s1/reading_input/mutation/mutants_reading_input.json
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/ws-a/scripts/stage1_s1/reading_input/tests/test_coherent.py
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/ws-a/scripts/stage1_s1/reading_input/tests/test_sg_coherent.py
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/A-coherent-build.md
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/A-coherent-fix1-runner-RI-coh-prompt-order.json
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/A-coherent-fix1-runner-formerly-invalid.json
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/A-coherent-fix1-runner-new-a.json
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/A-coherent-fix1-runner-new-b.json
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/tmp/a-smoke/add_mutants_fix1.py
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/tmp/a-smoke/classify_fix1.py
-- tests_run:
   * pytest test_coherent.py test_sg_coherent.py (11:08 UTC): 89 passed, exit 0
   * add_mutants_fix1.py: spec now 47 entries; format kept, ids unique, each find text occurs exactly once; exit 0
   * classify_fix1.py (the runner's rule without -x, on the two D-5 test files): unmutated baseline passes 89 tests; all 31 new-code entries (25 old + 6 new) are killed with 0 errors; the 16 pre-D-5 entries get 0 errors from the new files (RI-o-cut-rule and RI-oext-bqi-engine are killed there; the other 14 pass there and are killed by the old files as before); exit 0
   * official run_mutants.py --only RI-coh-prompt-order: baseline pass (284 tests); killed, 79 failures, 0 errors; exit 0
   * official run_mutants.py --only RI-o-cut-rule,RI-coh-n-counts-failing,RI-coh-u-fail-every-unsafe: 3 killed (205, 80, 80 failures), 0 errors; exit 0
   * official run_mutants.py --only RI-coh-header-ints,RI-coh-rule-text,RI-sg-paired-no-item-part: 3 killed, 0 errors; exit 0
   * official run_mutants.py --only RI-sg-familywise-sides,RI-sg-headline-o-l-swapped,RI-sg-differs-words-only: 3 killed, 0 errors; exit 0
   * verifier's my_mutants.py on V1-V10: 10 of 10 KILLED (V1, V2, V5 and V10 survived before); exit 0
   * pytest scripts/stage1_s1/reading_input/tests (11:46 UTC): 284 passed, exit 0; basetemp 2.8 GB, deleted
   * pytest on B16's tests in two commands: 198 + 63 = 261 passed, exit 0 each (the known numpy RuntimeWarnings)
   * pytest test_coherent.py test_sg_coherent.py after a docstring-only edit: 89 passed, exit 0
   * pytest scripts/stage1_s1/reading_input/tests on the final files (11:51 UTC): 284 passed, exit 0
   * git diff --quiet 55d5f8b -- scripts/stage1_s1/reading: exit 0; git status --porcelain --ignored on that path is empty; no __pycache__ or .pytest_cache in ws-a
-- open_points:
   * The full official mutation spec (47 entries; about 55-70 min unloaded; --only shards each run their own baseline; use the default 600 s --timeout under heavy load) is the lead's run. I confirmed 10 entries with the official runner and checked all 47 on the new files without -x.
   * D-5's fallback trigger scope (N2) is the lead's ruling. Block A only misses the coverage target; plan A meets it by the verifier's 10,000-replicate numbers and by the builder's.
   * The verifier's comparison harness (verify-A-coherent/gen.py) writes rule 'verifier synthetic', which coherent.check now refuses (a tested case). To re-run it, set rule to coherent.RULE.
   * Reading record (N5): take the symmetric table's label and the S-G codes from sg_coherent.json, and state which 'differs' each column uses: B16's (U-part words only) or the reader's C7 (words or headline).
   * N4 runbook fallback: if a --coherent-out build ever refuses with a coherent-only message, rebuild without the flag; tables.json is byte-identical.
   * FOCUS and the second stamp must take the four new hashes: coherent.py 9f3010fb52ea6459, mutants_reading_input.json 52f231ed9c6d787f, test_coherent.py 7cb5f8fc52ed7bea, test_sg_coherent.py cee9f10837524111. Build-report §8 items 1, 3 and 5-10 stand; this round changes no stdout line.
### D1-readers v2
-- report_path: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/D1-readers-verify2.md
-- verdict: defects
-- defects:
   * D1 (low), cost_table: no C-full cost per point for the four ref_eval references (adapter scaling 0.9/0.75/0.5 and SP). REV4:774 needs each menu item's cost under both conventions, and the Sp and Ow menus hold SP and adapter scaling (REV4:770-771). REV4:813 gives the C-full rule for exactly this case ('For an evaluation-only reference: the same minus training, plus its transform'). Yet _b10() (cost_table.py:346-352) prints per_point C-full null (reading K5), while it prices the same points under C-lean from a proxy (K6: the measured c0 less the frozen 220 s training). K5's only listed alternative is an equal split, which also includes a0's regeneration. Reproduction: verify-D1-readers/r2_edges.py on extra_kit.cost_kit(..., 'plan_a'). Each of scale:0.9, scale:0.75, scale:0.5 and prefix prints seconds null, c_full_fre null, c_lean_c0 0.7970448. Expected: a stated C-full value per point. One example is REV4:813 read literally: (mean a0 run slot 2,977.092 s - frozen C-full training 219.7 s + transform about 0) / 2,934 s = 0.9398 FRE on this kit. Another is the same seed's measured Safe LoRA -evaluate-P step. Fix: add one stated C-full price per point and a per-reference mean over seeds; keep the null as the alternative. Or the lead rules K5 in and records it as a deviation from REV4:774.
-- summary: Verdict: defects. There is one low-severity defect, in cost_table; the other four readers are verified.

**The fix round's two fixes are correct.**
- K6: under C-lean, a B10 state = the measured c0 - 220 s, plus its transform. This follows REV4:813 and §10.4's own construction (0.75 c0 = (15 + 635) / 870).
- K7: the median stage-1 R slot is printed beside the fixed 1 FRE.
- I agree with the builder's dispute on b10_certify: it is a study cost, priced at its measured seconds / c0 as REV4:823 does.
- Round-1 notes 2-5 are fixed.

**Checks run (all on synthetic data):**
- The builder's suite: 111 passed in 19.8 s. With the reading_input and reading suites, 567 tests are collected.
- My own independent code (r2_check.py, with its own Student-t quantile) reproduces every value the five readers print across plan A, block A only and plan B. Branch full was checked for cap_reports. Result: 283 of 283 checks pass.
- Seven stage-3 pick edge cases and four cost_table edge cases pass: a crashed run with a re-run, a moved host, a crashed c0 beside a complete one, and the ref_eval asymmetry.
- Every double-quoted rule passage is found in REV4.
- An audit hook on file opens shows what each reader reads:
  - fk_power reads only tables.json and reading.json; stage3_pick and sa_shift read only reading.json.
  - cost_table reads only plan.json, the seals and the readable cost-ledger.json files, with no folder listing.
  - cap_reports also opens sealed-class files: COMPLETE.json, oext_summary.json and oext_transfer_summary.json. This was disclosed as reading C5 and is the critic's own design. It runs only after the input build, so it is not a blinding defect, but the lead must rule on it and the reading script needs an exception to the never-open list.

**The defect (D1):** cost_table prints no C-full cost for the four ref_eval references (SP and adapter scaling). REV4:774 requires that cost for the Sp and Ow menus, and REV4:813 gives the rule for it. The same points are priced under C-lean.

**Notes in the report:**
- The LN-19 PHTest line says 'no full answer exists' although θ0's LN-14 pass holds both forms.
- One missing ledger makes the whole cost table refuse; a pre-check of the seal listing would remove that risk.
- B10 references get no mean over seeds.
- The Safe LoRA transform is priced by step wall time, not the ledger's transform stage.
- K3's split denominator should name DataShield-style; the anchor job is neither charged nor named.
- Pod overhead and the judge pods are not in the table.
- The weak outcome signal is also in the -calibrate step.
- K2's B+Qi gap is about 6-9% at Branch 128's smaller c0.

No files were edited in ws-d1. No real data was opened, and all scratch folders were deleted.
### D1-readers fix
-- open_points:
   * K6, new reading for the lead: C-lean of a B10 state = the measured c0 minus the frozen lean training price (220 s), plus the measured transform. Alternatives: REV4 10.4's frozen-price form (2,166.2 s / c0), which prices one state above a whole lean run when c0 is low (Branch 128), or null.
   * Dispute with the verifier, for the lead to rule: b10_certify and the other study costs stay at measured seconds / c0, as REV4:823 converts a0's regeneration. Dropping their c0 column would be a one-line change.
   * K2 extended: references trained by another recipe (G, B+Qi) get 1 c0. B+Qi's extra training is left out (E: a few per cent at the 500-prompt form), because the readable ledger cannot split one -calibrate step. A price would need the sealed engine ledger or an estimate.
   * K7, new: the median uses the stage-1 R runs in the reading's blocks. Alternative: also print the median slot without the -oext step, for comparison with wave 0a's 468 prompts.
   * When cost_table runs: inside the reading, or its output stays unopened until then, because -oext seconds carry a weak outcome signal. It reads tmp/stage1-olmo/seals/ and cost ledgers under retrieved/. Per the verifier, the lead's 1 Nov never-open ruling (I did not re-read FOCUS) needs an explicit exception for cost_table and for cap_reports.
   * cap_reports still reads sealed-class O-ext summaries (the earlier open point 1). This is unchanged and is the lead's call.
   * The full 49-entry mutation spec was not re-run by me (only the 12 new or changed cost mutants). The round-0 shard reports name 101 tests and the old spec SHA-256 1b7bfd84; the lead's full run replaces them (expected 48 killed, RX-common-exclusive survives as marked).
   * The verifier's repro_cost.py now stops at its own print lines (it formats a null C-lean value and reads diagnostics_by_kind['ref_eval']). This is expected; d1-fix-checks/fix_check.py replaces it.
   * Not tested on real ledgers (forbidden). The step names (-transform-P, -evaluate-P, -b10-regenerate, -oext) follow job_runner_stage1.py by code reading only.
### E-records v2
-- report_path: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-records-verify2.md
-- verdict: defects
-- defects:
   * D1 (E-D5-D6.md:68-71, :85-93; E-39.md:157-165; E-plan-updates.md:53, :148-149): D-5 says it 'never stops the reading', but its builder half can. Item 4 puts the counts document and its checks into the input builder (step 2). In track A's build a failed check refuses the whole builder: nothing is written, not even tables.json (ws-a test_coherent.py::test_the_builder_checks_its_own_counts passes and asserts rc 2). Worse, the drafted step 2 adds the counts option only at step 2, while R1b is quoted without it. R1D's step-2 comparison of sources.json with the pre-run (R1D:581-600) then fails every time. My synthetic run (v2/checks/prerun_vs_step2.py) shows coherent null in the pre-run against a dict at step 2. With the option at R1b too, output_sha256 08632ccd... differs from 7bd9335d... because the counts are bound to tables.json, which differs by the overlap block. Either way the script stops by S4 after step 1 has printed B14's verdicts. Fix: R1b takes the same counts option; the step-2 comparison leaves out the counts document's hashes; D-5 item 8 states what happens if R1b refuses only because of the counts (the lead's choice); §39 8(d) adds this as a third change; plan item 3 says 'a no-value pre-run with the same options, --no-overlap in place of the B14 options'.
   * D2 (E-D5-D6.md:94-103; E-plan-updates.md:106): D-5's 'verified' does not say which reading, how many replicates or which tail scope (per contrast or pooled) its coverage test uses. Yet 'a measured coverage outside the band triggers the fallback'. Its source, V1A:349-350, simulates plan A, plan B and block A only. Track A's block-A-only output (A-coherent-sim-block_a-2000.json, SHA-256 84d05e9c...) has S-G coherent coverage 0.876, 0.8765 and 0.8775, outside 0.88-0.92; B16's own primary form also falls outside the band there. That reading cannot run now that block B is sealed (RI/build.py:606-607). At 2,000 replicates (Monte Carlo SE 0.007) the verdict can also turn on Monte Carlo noise. As written, D-5 could go to (c+) because of a reading that will not run. Fix (the lead rules, possibly with GPT): gate on plan A at a stated replicate count (for example 10,000 per world), check plan B, report block A only as a limit, and state the tail scope.
   * D3 (E-plan-updates.md:119, :131-135, :143-150, :171, :197): the revised plan leaves out the reading-time readers. The lead ruled they are built before the second stamp (FOCUS:75 at 7452bd2): F_k's planning power at the measured q (REV4:574), the stage-3 pick (REV4:428), LN-14's bar and LN-19's shares (REV4:554-555), the S-a shift line (REV4:276) and cost per arm; track D1 built all five. D-6's trigger already counts them among 'the other builds' (E-D5-D6.md:172-173). grep for any of them in E-plan-updates.md returns 0 matches, so they appear in no reading step, no second-stamp list, no row-1d suite or spec list and not under 'what the lead can do now'. Fix: add step '4c. The reading-time readers ... each bound to reading.json by SHA-256, report only; fallback: after the reading, labelled code written after the reading', and add them to items 8, 9, 11 and 13.
-- summary: The verdict is defects: three remain after the fix round, all with reproductions and corrected text in the report. Round 1's nine defects are fixed. Citations hold: 521 of 521 are in range, about 70 phrases were checked by hand, the 14 'Old' plan blocks each occur once, and the builder's check_records.py passes again. Every quoted stated reading matches its source, and the rulings match the brief and the lead's rulings entry (FOCUS:75 at 7452bd2). The S1 record's FOCUS renumbering (:135, :138, :140, :144 at 55d5f8b) is correct. Nothing in the drafts reveals or depends on a stage-1 outcome or sealed choice. §40 follows the stage 1b check's corrections. Two §40 additions are backed by measurement on B16's own code. First, the tie tolerance on Λ_plant's edges: 627 of 2,000 exact-10 pp means land below 10.0 in floating point. Second, 'no fallback' for the pilot interval: a seed-part-only interval turns a frozen 'stop' (lower bound 4.26) into 'go' (lower bound 10.49). The defects: (D1) D-5's 'never stops the reading' does not cover its builder half, and the drafted step-2 text makes R1D's pre-run comparison fail every time, so the script stops after step 1. (D2) D-5's coverage test names no reading, replicate count or tail scope, and track A's block-A-only coverage (0.876) would trigger (c+). (D3) The revised plan leaves out the lead's ruled reading-time readers. Twelve minor notes are listed separately. These include swapped S3/S4 times, an unmarked added D-6 trigger, a relabel text that differs from the code, the wording of §40 point 10, a missing zphi.py in ADD:428's optional re-run, and D-7's input binding. Tests and checks run: 10 targeted B16 tests on a plant-free 55d5f8b export passed. Track A's builder self-check test passed. My four synthetic check scripts are kept in builds/verify-E-records/v2/checks/. No state-changing git command was run, and the main checkout's code is unchanged.
### E-records fix
-- report_path: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-records-build.md
-- summary: Fix round for track E-records is done; details are in the "Fix round" section (F1-F6) of E-records-build.md. I checked all nine defects and 21 notes in E-records-verify1.md against their sources at 55d5f8b. All nine defects were real and are fixed.

- **D1:** D-5's V is now a share and B16 applies the ×100 itself. A synthetic check through B16's own item_part shows why it matters: 339.5 pp² with V as a share against 1,173,672.8 pp² with V in pp. The "verified" list now has an unequal-n exact-fraction case, because the all-n = 3 case cannot catch the scale error.
- **D2:** tmp/stage1-olmo/retrieved/ and plant-arm unit folders are never opened. The "until" clause is gone.
- **D3:** the seed-only pilot-interval fallback is deleted. Re-run here, it turned the frozen "stop" into "go" on a constructed synthetic table. The text now says "no fallback", and any other interval would be a deviation written before any pilot value is read.
- **D4:** the S1 blinding record lists Gate B's §6 values in the --final output as possibly read from 05:26 UTC, and σ̂ from 04:31 UTC. It also states a position on §37's R4.
- **D5:** §39 point 8(d) adopts stop rules S1-S9 with two exceptions. S1 and S5 do not apply to D-5's reader, and the checkers stop only on identity lines. D-5 point 8 now spells out the wording printed if the reader refuses at the reading.
- **D6:** D-5's last fallback prints the design's option (c) paragraph with four listed edits, so it no longer describes the rejected drop rule.
- **D7:** §39 point 6 is now a stated reading that fills a gap. In REV4, "the selector" means §7's model-based selector.
- **D8:** §40 adds the route for the plant-edit record (hash only) and the match/no-match binding check, and the path rule now binds the lead too.
- **D9:** D-5 has a new item 2b stating its reading of G2's per-prompt rule.

All 21 notes are addressed. Note 7 has one addition the verifier lacked: build_plant.py:30 gates --f9 on the user's yes. Note 19 is partly done: the scratch reports' SHA-256 values are in the drafts, but committing copies is still the lead's step. Other additions: §39 point 8(g) records R1D's grep breach; the plan updates gain item 13 for row 1d; E-misc gains a ruling (2b) that kit round 34 must keep every value the reading builder reads unchanged.

Checks (exit 0 unless noted):
- check_records.py passes. It reads the sources straight from git at 55d5f8b. All 14 "Old" blocks occur exactly once in the plan; 763 cited lines are in range; all 107 phrase checks hold. Its first run exited 1 because quotes span line breaks in the sources; I fixed the checker, not the drafts.
- d5_scale_check.py passes, and so does the verifier's linearized_check.py. pilot_fallback_case.py gives frozen form "stop", seed part only "go".
- Seven targeted B16 tests passed (synthetic data). The pytest base folder was deleted.

I opened nothing on the never-open list. Of plant paths I read code only. No repository file or git state changed.
-- changed_files:
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-D5-D6.md
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-39.md
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-S1-blinding.md
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-misc.md
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-40.md
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-plan-updates.md
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-records-build.md
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-fix-checks/check_records.py
   * /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/reports/E-fix-checks/d5_scale_check.py
-- open_points:
   * FOCUS numbering: the drafts cite FOCUS at 55d5f8b. At HEAD 7452bd2 every FOCUS line from 74 on is 2 higher (two new entries). When committing, keep the commit pin in the citation headers or remap.
   * D-5 item 9 has an added tolerance: SE and df are compared at 1e-6 relative where the independent reference fits REML on its own (B16's REML stops at a 1e-6 step). The review's own text says 1e-9. The lead decides.
   * §39 point 8(a): making the references line an identity line (a stop condition) is written as an option and not adopted, because the critic's list of identity lines leaves it out. A missing reference is printed as a limit beside family 1b instead.
   * §40 point 2 now has no fallback for the pilot interval. If Gate A's a0 per-prompt tables cannot be built, the pilot is not read until they can, and any other interval is a post-W1 deviation written before any pilot value is read.
   * Note 7: the frozen texts make F9 conditional on funding only (REV4:710; W1R:296). The plant builder's docstring also requires the user's yes (build_plant.py:30). The draft states both.
   * Disclosure: round 1's grep -r over the lead's git-ignored notes folder (tmp/claude-workspaces/stage1-integrate-20261017/notes/) read every file's content to match three script names, printing names only. The folder is not on the never-open list, but I cannot rule out that it holds something sealed. The lead should judge this.
   * The scratch reports the drafts cite (CRIT, V1A, D1A, R1B, R1D, READY, CHECK) are temporary. Their SHA-256 values are now in the drafts; the lead should commit copies with the records.
   * Still open from round 1: point 3 (the ADD:428 evidence is git-ignored; back it up), point 7 (deviation numbers D-5 to D-7 and their SPF/FOCUS entries), point 8 (pinned texts still name the withdrawn §24 point 4), point 9 (scratch citations), points 11 and 12. Settled: points 5 and 6 are now in the records; point 10 was confirmed by the verifier.