# Draft: the plan's stale points and their replacement text

- **Status.** A draft for the lead (GI VIII), written 2026-11-01 by an Opus builder (track E-records); clock checked
  with `date -u` at 05:29 UTC. The plan is PLAN = `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md`
  at `55d5f8b` (SHA-256 `121c5119d12e5bae…`; FOCUS:75 records it). Each "Old" block is the exact text at that commit;
  each "New" block is the replacement. Items 1-6 are CRIT's six (CRIT:69-70, §3 C2-C7, C11); items 7-12 are found here;
  item 13 was found by the independent verifier (round 1, note 14). R1D = the runbook draft, committed copy
  `.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/design-round/1d-reading-runbook-draft.md`
  (SHA-256 `9ae23f5ee6fa9ae6…`; the table in `E-D5-D6.md`); LR = the lead's rulings `lead-rulings-20261101.md`.
  Fix round 2 (1 Nov) applies LR R6.1 (item 3), R1.2 (item 7), R6.3 (items 8, 9, 11, 13), R2 (item 13), R3 (item 1),
  R4.5 (item 9) and R5 (item 4).
- **How to apply.** Edit in place (a plan adopts nothing) and add, under the title: "Revised 1 November 2026 by
  addendum §39 and §40; the 31 October text is in git at `55d5f8b`." Then record the new SHA-256 in FOCUS.

---

### 1. Row 1b: the Mac fallback cannot run, and "§24 point 4" is withdrawn (PLAN:31; CRIT C2, C3)

Why: the script always uses the CUDA-only loaders (`scripts/stage1_s1/overlap_similarity.py:421-426`;
`experiments/safety_selection/loaders.py:121-129`); §24 point 4's fallback was withdrawn (FOCUS:104); B14's report
refuses recipe-S units until D-6 (`E-D5-D6.md` §2).

Old:
```
| 1b | **B14's similarity pass never ran.** §9.4's overlap control (report only) needs θ0's embeddings of the 200 harm prompts and the 144 added rows (`overlap_similarity.py`, "on the pod"); no kit job ran it, and no `similarity.json` or `strata.json` exists. The strata must be sealed before any add-arm outcome is read. | One small pod, one job: `overlap_similarity.py` on θ0, about $1 (my estimate: one 1B forward pass per prompt, plus setup), started from the balance. Then `overlap_strata.py strata` on the Mac and the strata's SHA-256 into FOCUS. | (i) The same script on the Mac CPU (float64; "on the pod" becomes a recorded deviation); trigger: the pod fails or the balance is under the reserve. (ii) The reading prints "not computed" for §9.4 (B16's built fallback, §24 point 4); trigger: (i) also fails. |
```
New:
```
| 1b | **B14's similarity pass never ran** (a scheduling gap: planned "on the pod", never scheduled in a block; it runs once, after both blocks and before any stage-1 outcome is read; nothing measured changes; §39). §9.4's overlap control (report only) needs θ0's embeddings of the 200 harm prompts and the 144 added rows; no `similarity.json` or `strata.json` exists. B14's report also refuses recipe-S units as pinned: D-6 (§39 point 2) re-pins its settings before the strata are made. | The $0 Mac pre-check; kit round 34 (one job kind for the pinned `overlap_similarity.py`; built and verified), which leaves every value the reading builder and B14's inputs writer read unchanged (checked by C's verifier, not pinned by a test; §39) and changes `stage1_rules.py` (`4005cb4e…`) and `plan_tool.py` (`27e299b5…`), the runbook's "never changes" list and the second stamp taking the new hashes; one A100 pod from a background job, about $0.60–0.75 (estimate; worst about $2.7–3.1 at its cap), from the balance. Then `overlap_strata.py strata` on the Mac under D-6's settings, run in place on `retrieved/sim-1/…/similarity.json` by the exact path and SHA-256 that `record-done` prints (the one exception to the never-open rule for `retrieved/`; the lead never lists `retrieved/`); a script copies `similarity.json` into the B14 records folder with a SHA-256 check and prints only the hash; the SHA-256 of `similarity.json` and `strata.json` into FOCUS (before any add-arm outcome is read) and the second stamp. D-6 is committed before `strata` runs; the inputs writer runs, then its checker at once. | (i) One re-run (`defer sim-1` to `sim-2`) if the pod crashes, C's verifier's N5 case included (a warning without a trailing newline before the "wrote" line); then a one-off pod with the same command and a written checklist; trigger: round 34 not verified when the other builds are done, or a second crash. (ii) `--no-overlap`: B16 prints "not computed" and the record words §9.4 as D-6's fallback, with this cause; trigger: two pod attempts end without `similarity.json`, or the balance is below $6 + the pod's cap × $1.85. The Mac is not a route: the script refuses non-CUDA devices. |
```

### 2. Step 1 refuses as pinned (PLAN:41; CRIT C4)

Why: B14's report refuses the first kit unit (D-6) and needs an inputs file that no code writes yet (R1D:35).

Old:
```
1. B14 report: `overlap_strata.py report` from the strata and the sealed a0 and add-arm units → `overlap_report.json`.
```
New:
```
1. B14 report under D-6's settings: `overlap_strata.py report --strata <sealed strata.json> --inputs <committed B14 inputs file> --out <run folder>/b14` → `overlap_report.json`, after a no-value pre-run whose output must be byte-identical (§39 point 8).
```

### 3. Step 2 lacks `--hb-out` (PLAN:42; CRIT C5)

Why: step 4 needs `hb_tables.json` (`scripts/stage1_s1/reading_input/hb_claim.py:4`); without the option the builder
prints "HarmBench tables: not built (no --hb-out)" (`scripts/stage1_s1/reading_input/__main__.py:88`); step 4b needs
D-5's counts document, and the no-value pre-run must take the same option (LR R6.1).

Old:
```
2. Input build: `python -m scripts.stage1_s1.reading_input --reading plan_a --kit tmp/stage1-olmo --b14-strata … --b14-report … --expect-strata-sha256 … --expect-report-sha256 … --out <new folder>/tables.json --record <new folder>/sources.json`.
```
New:
```
2. Input build: `python -m scripts.stage1_s1.reading_input --reading plan_a --kit tmp/stage1-olmo --b14-strata … --b14-report … --expect-strata-sha256 … --expect-report-sha256 … --out <new folder>/tables.json --record <new folder>/sources.json --hb-out <new folder>/hb_tables.json --coherent-out <new folder>/coherent_counts.json` (D-5's counts document), after a no-value pre-run with the same options, `--no-overlap` in place of the four B14 options. The step-2 comparison with the pre-run leaves out the overlap block and the output hashes bound to `tables.json` (the HarmBench tables' and the counts document's). If the pre-run refuses only on the coherent-only counts, step 2 runs without `--coherent-out` and D-5 goes to its last fallback (c), chosen at the pre-run (§39 point 1, item 8).
```

### 4. Step 5 has no script (PLAN:46; CRIT C6)

Why: no draw script exists (R1D:37); HLC:164 needs it committed first; D-7 (`E-misc.md` §B).

Old:
```
5. LN-31's draw for the human label check (prints totals only).
```
New:
```
5. LN-31's draw for the human label check (prints totals only), by the draw script committed before the second stamp with its frozen protocol, seed tags, term list and inputs by SHA-256 (post-W1 deviation D-7; built and verified), on inputs restored and pinned in `tmp/hlc-inputs/`; its `check` re-runs the draw in a second process and prints "match" or "mismatch" and totals. If it was not committed before the second stamp: "not run at the reading", and the draw follows when the human label check is funded (D-7's fallback).
```

### 5. Step 6 says "stop" where the user's instruction says "go on" (PLAN:47-49; CRIT C7)

Why: KW:7, :13; §39 point 10.

Old:
```
6. Records: a stage-1 reading record (labels P1–P6, the headline word, the references, the best feasible repair, the
   sensitivities), FOCUS, commit, push, backup. Then the lead stops and reports to the user (the study stops and asks
   after every stage).
```
New:
```
6. Records: a stage-1 reading record made by the mechanical extractor (labels P1–P6, the headline word, the
   references, the best feasible repair, the sensitivities, with S-G coherent's words copied by key), FOCUS, commit,
   push, backup, then a third stamp of the outputs. Then the lead reports to the user and goes on in the plan's order
   (the user's 31 Oct instruction, `user_instruction_keep_working_20261031.json`; §39 point 10).
```

### 6. Row 1c omits RI-O12 to RI-O14 and the other stated readings (PLAN:32; CRIT C11, §2.1)

Old:
```
| 1c | **The builder's other open points** (RI-O1, RI-O5 to RI-O11) | One addendum section (§39) that confirms each stated reading as the lead's ruling, so every reading rule is written down before outcomes. RI-O3: S-tok has no input (stage 1c's R_1200 and R_2400 have not run), so the reading says "not run". | None needed; each point already has a stated reading. |
```
New:
```
| 1c | **Every other stated reading** | Addendum §39 confirms each as the lead's ruling before any outcome: the builder's RI-O1 and RI-O5 to RI-O14; the claim reader's R2, R3, R5, R6, R7 and R9; B16's README readings and overlap readings R2–R6; B16-D4-O2, B16-D4-O3 and B16-H-O9; the coherence condition in the best feasible repair; S-tok's wording ("not run": its stage-1c input has not run; B16 prints null) and §9.4's wording under `--no-overlap`; the runbook's readings; the stamps; "report and go on"; the reading-time readers' adopted readings (§39 point 11). Beside it, the S1 blinding record (REV4:919) lists every rule written after the W1 commit, with the Gate B values read before each. | None needed; each point already has a stated reading. |
```

### 7. Row 1a: option (a) inside B16 is superseded by D-5 (PLAN:30)

Old:
```
| 1a | **RI-O2, coherent-only U (sensitivity S-G).** A prompt whose 3 sampled answers all fail the coherence screen has no coherent share; B16's table needs one value per prompt and cell. Still open (FOCUS 29 Oct). | Option (a): a B16 change that takes per-prompt counts (coherent unsafe, coherent n) and drops such a prompt pairwise, as Gate B's reading does. Built in a scratch tree, tested, mutation-checked, merged, recorded as post-W1 deviation D-5. It changes B16's module hashes, so it must land before the reading. | Option (c): S-G reports the two G3 corners only and says why. Trigger: (a) is not verified (suite and mutants pass) when everything else in this table is done. |
```
New:
```
| 1a | **RI-O2, coherent-only U (sensitivity S-G).** A prompt whose 3 sampled answers all fail the coherence screen has no coherent share; B16's table needs one value per prompt and cell. Ruled as post-W1 deviation D-5 (§39 point 1). | D-5: G2's pooled share per cell with the linearized prompt table on all 200 prompts, read by a new reader beside B16 that calls B16's unedited functions (B16 byte-identical); the builder writes per-prompt counts (n, u, u_fail) in a side document bound to `tables.json` (`--coherent-out`, given to the no-value pre-run too); printed: each arm's pooled coherent-only U, G2's counts, S-G coherent's U-part words and headline word under its own Φ run, and both adverse G3a corners; the reader never stops the reading, and its builder half is settled at the pre-run. Built; fix round 1 done; its re-verify decides (no second fix round). Verified = the suites; the 47-entry spec as the lead's background run (0 invalid; every mutant killed except listed expected survivors); an independent reference (estimates to 1e-9 pp; SE and df to 1e-6 relative where the reference fits REML on its own); an unequal-n hand case against exact fractions; the all-n = 3 equality; and the coverage gate on plan A, the reading that runs: every contrast in every world within 90% coverage 0.88–0.92 with a 0.75% tail at most 1.5 × the primary form's, at 2,000 or more replicates per world and also at 10,000 where a world is within 2 Monte Carlo SE (0.0134) of a band edge or its tail ratio is above 1.3; plan B checked and reported; block A only a reported limit (that reading refuses with block B sealed). | (c+): each arm's pooled coherent-only U only, no label re-read; trigger: D-5 not verified after one fix round (the re-verify's verdict). Last: the design's option (c) paragraph, edited as D-5 says; triggers: (c+) not verified when the second stamp's manifest is written, or the builder's no-value pre-run refused only on the coherent-only counts (then (c) is chosen at the pre-run and names that cause). |
```

### 8. Row 1e: the first stamp is anchored (PLAN:34)

Why: FOCUS:74; `timestamp/ots-check-20261101.json`.

Old:
```
| 1e | **The outside time stamp (decided 31 Oct: no OSF posting; an OpenTimestamps stamp instead).** The user: "Yes, time-stamp it". Stamped at 22:54 UTC: `timestamp/ots-manifest-20261031.json` (`68e75447…`; it binds the package zip and members, the six frozen originals checked at their commits, both block seal records, HEAD and the stage-1 code trees) and the package zip (`170361f7…`); four calendars hold pending attestations (`timestamp/stamp-record-20261031.json`). | After the calendars' Bitcoin transactions confirm (a few hours): `ots upgrade`, then verify the block's merkle root against block headers from two independent sources, and record the block height and time. **The reading starts only after that block time.** Right before the reading, a second stamp of the final reading code and the runbook. Paper wording: "pre-specified" (the frozen rule's no-deposit branch). | If no calendar's anchor confirms within 48 h: re-stamp once; if that also fails, the paper keeps "pre-specified in a dated git record" and states that the stamp did not complete. |
```
New:
```
| 1e | **The outside time stamp (decided 31 Oct: no OSF posting; an OpenTimestamps stamp instead).** The user: "Yes, time-stamp it". Stamped at 22:54 UTC: `timestamp/ots-manifest-20261031.json` (`68e75447…`; it binds the package zip and members, the six frozen originals checked at their commits, both block seal records, HEAD and the stage-1 code trees) and the package zip (`170361f7…`). **Anchored** in Bitcoin block 974039 (header time 2026-10-31T23:28:48 UTC) and block 974047, checked at two explorers (`timestamp/ots-check-20261101.json`). | Right before the reading, a second stamp of the final reading code (with the D-5 reader and B14 under D-6), the kit files after round 34, the runbook and the reading script, B14's inputs file, `similarity.json` and the strata, the reading-time readers (`reading_extra/`, with `cost_table` after its fix round), the D-7 draw script, and the records (addendum §39 and §40, D-5 to D-7, the S1 blinding record), verified the same way; step 1 starts only when its anchoring block has at least 6 confirmations and 2 h after its header time. Keep the `ots` client until both stamps are verified. A third stamp of the reading's outputs after the records step. Paper wording: "pre-specified" (the frozen rule's no-deposit branch). | If the second stamp does not anchor within 48 h: re-stamp once; if that also fails, the paper keeps "pre-specified in a dated git record" and states that the stamp did not complete. |
```

### 9. Step 0, and steps 3-4: the margin, the re-run and D-5's reader (PLAN:39-40, :43-45)

Old:
```
0. Check that 1e's stamp is anchored (its block time is earlier than now), then stamp the final reading code and
   the reading runbook, and start step 1 only after that second stamp is anchored too.
```
New:
```
0. 1e's first stamp is anchored (block 974039). Check by exact path that every expected cost ledger exists (existence
   only, no read; a missing ledger makes step 4c's cost table "not computed", report only; §39 point 8(h)). Stamp the
   final reading code (with the D-5 reader and B14 under D-6), the kit files after round 34, the runbook and the
   reading script, B14's inputs file, `similarity.json` and the strata, the reading-time readers (`reading_extra/`),
   the D-7 draw script, and the records (addendum §39 and §40, D-5 to D-7, the S1 blinding record), and start step 1
   only after that second stamp is anchored, with at least 6 confirmations and 2 h after its block's header time
   (§39 point 9).
```
Old:
```
3. B16: `python -m scripts.stage1_s1.reading --input tables.json --out reading.json`; its `provenance.input_sha256`
   must equal the builder's printed SHA-256 of `tables.json`.
4. HarmBench claim reader (`hb_claim.py`, §37): the HB contrasts, E_HB and the "harm" sentence words.
```
New:
```
3. B16: `python -m scripts.stage1_s1.reading --input tables.json --out reading.json`; its `provenance.input_sha256`
   must equal the builder's printed SHA-256 of `tables.json`; a second run must give a byte-identical file.
4. HarmBench claim reader (`hb_claim.py`, §37): the HB contrasts, E_HB and the "harm" sentence words.
4b. D-5's reader beside B16: S-G's coherent-only U per arm and per contrast, its words and headline word under its
   own Φ run, G2's counts, and both adverse G3a corners. A failure here is logged and never stops the reading.
4c. The reading-time readers (`scripts/stage1_s1/reading_extra/`; §39 point 11): F_k's planning power at the
   measured q (REV4:574), the stage-3 pick (REV4:428), LN-14's bar and LN-19's shares (REV4:554-555, `cap_reports`),
   the S-a shift line (REV4:276) and the cost per arm (REV4:103, `cost_table`), each bound to `reading.json` by
   SHA-256, report only, run only inside the reading script here (`cap_reports` opens the O-ext summaries and
   COMPLETE.json files the builder's record names; `cost_table` opens `plan.json`, the seals and the cost ledgers:
   the never-open list's one explicit exception for these readers). A failure here is logged and never stops the
   reading. A reader not verified before the second stamp runs after the reading, labelled "code written after the
   reading".
```

### 10. Step 2's table: stage 1b's row (PLAN:57)

Old:
```
| 1 | Stage 1b, the planted-cause positive control (pilot 3 runs, then 12–15) | $17–35 | none |
```
New:
```
| 1 | Stage 1b, the planted-cause positive control (addendum §40: pilot block P, 3 runs, from the balance, about $5–6 measured, kit upper $7.43; then 12–15 runs on a top-up) | $17–35 | none |
```

### 11. "What the lead can do now", item 1 (PLAN:70)

Old:
```
1. Steps 1a, 1c and 1d (all $0) and 1b (about $1 from the $29.94 balance, above the $6 reserve).
```
New:
```
1. Steps 1a (D-5), 1c (§39 and the S1 blinding record), 1d, D-6, D-7 and the reading-time readers (all $0), and 1b (kit round 34, then one pod: about $0.60–0.75, worst about $2.7–3.1 at its cap, from the balance above the $6 reserve).
```

### 12. "What the lead can do now", item 3 (PLAN:72)

Old:
```
3. $0 preparation of stage 1b's kit round (the plant and decoy were built on 23 Oct).
```
New:
```
3. $0 preparation of stage 1b (addendum §40): kit round 35 (pilot block P) and the frozen pilot reader, in scratch trees, merged only after the reading's outputs are sealed; K7 built off the pilot's path.
```

### 13. Row 1d: the test evidence before the second stamp (PLAN:33; found by the verifier, note 14)

Why: under D-5 B16 does not change, so its 117-entry spec need not run again (`E-D5-D6.md` §1, Reasons); the D-5
reader, B14 under D-6, kit round 34 and the D-7 draw script are new code before the reading; the runbook's readings
are in §39 point 8; the runbook drafts a near-set fallback for specs that cannot finish (R1D:801-803).

Old:
```
| 1d | **The reading runbook** | A step list like the judge runbook: exact commands, the hashes each step must print, the refusals, where each output goes, and what is read by whom. Re-run the reading-input and B16 test suites and mutation specs on the current tree first (as the lead's background jobs). | None. |
```
New:
```
| 1d | **The reading runbook** | A step list like the judge runbook (drafted): exact commands, the hashes each step must print, the refusals, where each output goes, and what is read by whom, with addendum §39 point 8's readings (stop on identity lines only; D-5's reader and the reading-time readers never stop the reading; the no-value pre-run takes `--coherent-out`; the cost-ledger pre-check). Before the second stamp, as the lead's background jobs on the final tree: the reading-input suite and its 47-entry spec (the builder changes and the D-5 reader), B14's suite and the 69-entry near set of its 150-entry spec (D-6 and the inputs writer; the full spec in the background when the machine allows), kit round 34's suite and mutants, the reading-time readers' suite and spec (49 entries; `cost_table` after its fix round), the D-7 draw script's suite and spec (re-run after D-5's merge), and B16's suite (B16 is unchanged under D-5, so its 117-entry spec need not run again). | All suites, plus near-set mutants within about 40 lines of each change; trigger: a full spec cannot finish before the planned stamp (the runbook's D8). |
```
