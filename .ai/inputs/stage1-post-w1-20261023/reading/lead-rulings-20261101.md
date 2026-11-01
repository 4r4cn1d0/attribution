# The lead's rulings after build round wf_795563f3-35a (GI VIII, 1 Nov 2026, written 14:02 UTC)

Status of the round: B (D-6) verified; C (kit round 34) verified; D2 (LN-31 draw) verified after one fix round.
A (D-5) fix round 1 done, but its re-verify never ran (the verifier's login expired twice: an infrastructure
failure, not a verdict). D1 (reading-time readers) re-verify: one low defect in cost_table; the other four readers
verified. E (records) re-verify: three defects (E-D1 to E-D3 below).

Reports: `scratchpad/builds/reports/` (build, verify, fix files per track). Sources are cited at commit `55d5f8b`
unless stated. No stage-1 outcome has been read; nothing here depends on one.

## R1. Track A (D-5, the coherent-only reader)

1. **The re-verify of fix round 1 runs now.** The pre-set trigger is unchanged: "D-5 is not verified after one fix
   round" -> fallback (c+). The re-verify's verdict decides. No second fix round for the reader.
2. **"Verified" for D-5** = item 9 of the D-5 record (E-D5-D6.md), with these rulings:
   - (a) **Coverage gate scope.** The gate is **plan A**, the reading that will run. Every contrast in every simulated
     world must meet both the 90% coverage band 0.88-0.92 and the tail ratio (S-G coherent's 0.75% tail at most
     1.5 x the primary form's tail in the same world). Replicates: at least 2,000 per world; a world whose
     2,000-replicate coverage is within 2 Monte Carlo SE (0.0134) of a band edge, or whose tail ratio is above 1.3,
     must also pass at 10,000 replicates. **Plan B** is checked and reported (not a trigger). **Block A only** is
     reported as a limit, not a trigger: that reading can no longer run (RI/build.py:606-607 refuses it with block B
     sealed) and B16's own primary form is also outside the band there.
   - (b) **Tolerance.** Estimates agree to 1e-9 pp. Where an independent reference fits REML on its own, SE and df are
     compared at 1e-6 relative (B16's REML stops at a step below 1e-6, ADD:425). Adopted.
   - (c) The official 47-entry mutation spec is the lead's background run (0 invalid, every mutant killed except
     listed expected survivors). It is part of "verified".
3. **If the re-verify finds a defect:** (c+) is built and verified as the D-5 record's pre-set fallback (per-arm
   pooled coherent-only U per cell, its seed mean and N per cell, with the record's fixed text; the adverse corners
   "not computed"; B16's built G3 tables with item 7's label). If (c+) is not verified when the second stamp's
   manifest is written: the last fallback (c) paragraph.

## R2. Track B (D-6, B14's settings re-pin and the inputs writer) - verified

1. D-6 stays **settings-only** (a deny-list: G `c004349c...` and B+Qi `37942cf5...` refused). The limit is recorded: a
   unit of any other recipe hash would pass B14's own checks. Today the unit pins, the inputs writer's plan.json
   recipe check, the checker and the builder's cross-check cover the reading, and plan.json records recipe S on
   engine X for all 55 arm and 5 a0_arm jobs (B's verifier). No accepted-recipes list is added.
2. Mutation: the lead runs the 69-entry near set before the second stamp, and the full 150-entry spec as a
   background job when the machine allows. The D-6 record says the spec has 150 entries and which set was run.
3. Order: D-6 is committed before `overlap_strata.py strata` runs. The inputs writer runs, then the checker at once.

## R3. Track C (kit round 34, the similarity job) - verified

1. **retrieved/ and the similarity outputs.** Tools may read `tmp/stage1-olmo/retrieved/sim-1/` only by the exact path
   and SHA-256 that record-done prints. `overlap_strata.py strata` runs in place on that path. A script copies
   similarity.json into the B14 records folder with a SHA-256 check and prints only the hash. similarity.json holds
   no stage-1 outcome (training-row to evaluation-prompt similarity; no model output). On a crash the lead may read
   sim-1's process.log (B14's own stdout; no model output) and records that read. The lead never lists retrieved/.
2. The runbook's "never changes" list takes the new hashes of `stage1_rules.py` (4005cb4e...) and `plan_tool.py`
   (27e299b5...); `seal.py` and `judge_units_stage1.py` are unchanged.
3. The equality of every rules value the reading builder and B14's inputs writer read was **checked by C's verifier,
   not pinned by a test**. Records must say so (E's §39 2b claimed a pinning test that round 34 lacks).
4. N5 (a warning without a trailing newline just before "wrote" makes a good run a crash) is accepted: the plan pays
   one re-run; fallback a one-off pod with a checklist; last resort `--no-overlap` ("not computed").
5. Hard-rule note recorded: `git ls-files .ai/inputs/stage1-post-w1-20261023/block-b | head -3` printed three file
   names, no content, no value.

## R4. Track D1 (the reading-time readers)

1. fk_power, stage3_pick, sa_shift and cap_reports are verified.
2. **cost_table: one more fix round, cost_table only.** Print a C-full value per point for every evaluation-only
   reference (adapter scaling 0.9, 0.75, 0.5 and SP) by REV4:813 read literally ("For an evaluation-only reference:
   the same minus training, plus its transform"): the matched a0 run's measured C-full slot on the same seed, minus
   the frozen C-full training price, plus the measured transform, over c0. Print a per-reference mean over seeds.
   Keep "null: not stated" printed beside it as the alternative reading (K5). Also fix: the LN-19 PHTest line's "no
   full answer exists" (theta0's LN-14 pass holds both forms); K3's split denominator named "DataShield-style" and the
   anchor job named. Then an independent verify. **Fallback:** if cost_table is not verified after this round, it
   runs after the reading, labelled "code written after the reading"; the other four readers stand.
3. Adopted readings: K6 (C-lean of a B10 state = measured c0 - 220 s + measured transform), K7 (median stage-1 R slot
   beside the fixed 1 FRE), b10_certify and other study costs at measured seconds / c0 (REV4:823), K2 extended (G and
   B+Qi references at 1 c0; B+Qi's extra training left out, a stated limit of a few per cent; 6-9% at Branch 128's
   smaller c0).
4. **Never-open exception.** cap_reports opens COMPLETE.json and the O-ext summaries; cost_table opens plan.json, the
   seals and the cost-ledger files. Both run **only inside the reading script, at step 4c, after the input build**:
   that is the readers' route, and the never-open list gains this explicit exception. Their outputs are not opened
   before the reading (-oext and -calibrate seconds carry a weak outcome signal).
5. Runbook pre-check: before the reading, check by exact path that every expected cost ledger exists (existence only,
   no read). A missing ledger makes the cost table "not computed" (report only; it never stops the reading).
6. Limits recorded, not fixed: the Safe LoRA transform priced by step wall time; pod overhead and judge pods are
   outside the table.

## R5. Track D2 (LN-31's draw) - verified

1. Confirmed readings: 4 (the split counts prompts for the total, bounds and minimums, and answers for the
   proportion), 7 (the protective reading that adds greedy harm categories), 11 (the benign block), 12 (theta0's
   HarmBench split), 13 (a cell's target cut to its distinct prompts); the 106-term list and 5 age patterns; the
   benign label = each unit's stored full-answer Refusal flag on its own greedy answers (stated in the paper).
2. Cross-seed loss of the HarmBench minimum (verifier 2, note 1): confirmed as reading 4, with its simulated size
   (6-13% of seed cells at U 0.03-0.05 and q 0.2) stated. Weights granularity (HarmBench split only in the Unsafe
   cell): a recorded limit.
3. HLC 4.3 item 4 ("a second, independent process"): `check` re-runs the same code in a second process. Recorded as
   part of D-7, with the two verifiers' independent re-implementations on synthetic draws as partial cover.
4. The late build is **D-7** (the deadline in LW-30, HLC:164, HLC:168 and W1R:243 was before block A's first pod,
   2026-10-25T11:04:34 UTC; written 1 Nov, after both seals, before any stage-1 outcome was read).
5. The draw runs at runbook step 5, after the reading (inputs restored and pinned in `tmp/hlc-inputs/`: OCT9KEY
   `tmp/hlc-inputs/oct9/key.json`, V3 `tmp/hlc-inputs/prepared-v3-inj05`). D2's suite is re-run after A's merge.

## R6. Track E (the record drafts)

Fix round 2, for the three defects, with these rulings:
1. **E-D1 (the builder half and the pre-run).** The no-value pre-run (R1b) takes the same `--coherent-out` option as
   step 2. R1D's step-2 comparison of sources.json with the pre-run leaves out the counts document's hashes (they bind
   tables.json, which differs by the overlap block). Plan item 3 reads "a no-value pre-run with the same options,
   `--no-overlap` in place of the B14 options". §39 point 8(d) adds this as a third change. D-5 item 8 says: the
   reader never stops the reading; the builder half is settled at the pre-run. If the pre-run refuses only on a
   coherent-only check (the counts message), the reading's step 2 runs without `--coherent-out` (tables.json is
   byte-identical without the flag), and D-5 goes straight to its last fallback (c), because (c+) also needs the
   counts. That choice is made at the pre-run, before any value is read; (c)'s paragraph then names this cause
   instead of "not verified".
2. **E-D2 (the coverage gate):** as R1.2(a).
3. **E-D3 (the reading-time readers in the plan):** add step 4c: the five reading-time outputs (F_k's planning power
   at the measured q, REV4:574; the stage-3 pick, REV4:428; LN-14's bar and LN-19's shares, REV4:554-555; the S-a
   shift line, REV4:276; cost per arm) plus cap_reports, each bound to reading.json by SHA-256, report only, run only
   inside the reading script (R4.4's exception); fallback: after the reading, labelled "code written after the
   reading". Add them to the plan's items 8, 9, 11 and 13.
4. Also in this round: D-6 says 150 spec entries (69-entry near set run before the stamp) and states the deny-list
   limit (R2.1); §39 2b states R3.3; the hard-rule notes are recorded (C's `git ls-files` print; D2's three 600 s
   overruns moved to the background by the harness, each finished exit 0; E's round-1 grep, R6.6).
5. Other open points ruled:
   - FOCUS numbering: keep the `55d5f8b` pin in every citation header (no remap).
   - §39 8(a): the references line is not an identity line; a missing reference prints as a limit beside family 1b.
   - §40 point 1's tie tolerance (B16's 1e-9 pp on the edges): adopted. It reads the frozen edges exactly (627 of
     2,000 exact-10 pp means land below 10.0 in floating point); it moves no target.
   - §40 point 2: no fallback for the pilot interval. Adopted.
   - Note 7: F9 needs funding (REV4:710; W1R:296) and the user's yes (build_plant.py:30). Adopted as written.
   - ADD:428 evidence: the lead commits copies of `b16-verify-stats.json` (`65fe90c3...`) and `b16-fix.json`
     (`4090118e...`) from `tmp/claude-workspaces/stage1-integrate-20261017/notes/` (in the lead's worktree
     kind-hawking-a6ce04) with the records.
   - Deviations: D-5 (coherent-only U), D-6 (B14 re-pin), D-7 (LN-31's late draw, with HLC 4.3 item 4). SPF:344 adds
     all three.
   - Pinned texts naming the withdrawn §24 point 4 (B16 settings/reading.json:200, B16/README.md:68, RI/__main__.py
     --no-overlap help): left unchanged (B16's settings pin must not move); the record corrects the reference.
   - Scratch citations: cite the committed copies under `.ai/inputs/stage1-post-w1-20261023/reading/
     lead-reports-20261101/design-round/` (D1A `1a-ri-o2-design.md` d4700f08..., V1A `1a-ri-o2-review.md` f5cb0298...,
     CRIT `2-critic.md` e8646619..., R1B `1b-b14-similarity.md` c03f6746..., R1D `1d-reading-runbook-draft.md`
     9ae23f5e...) and `next-stages/` (READY `A-stage1b-readiness.md`, CHECK `A-stage1b-check.md`). The build round's
     reports will be committed under `lead-reports-20261101/build-round/`.
   - Earlier open point 11 is closed by track D1; open point 12 (Self-Inf-N's switch) stays with stage 1b.
6. **E's round-1 grep -r** over `tmp/claude-workspaces/stage1-integrate-20261017/notes/`: no blinding breach. grep read
   the bytes and printed only matching file names; no content reached a model. The folder holds build, verify and
   kit reports of 17-27 Oct written by the lead's helpers, who never opened a sealed file. Recorded as a disclosure.
