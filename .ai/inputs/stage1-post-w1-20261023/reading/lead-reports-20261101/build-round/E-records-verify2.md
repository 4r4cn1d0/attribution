# Verification of track E-records (round 2, after the fix round)

- **Written** 2026-11-01 by an independent Opus verifier for the lead (GI VIII); clock checked with `date -u` at
  09:34, 09:52, 10:00, 10:05 and 10:06 UTC. Self-identification is not verification; the launcher records routing.
- **Checked:** the six drafts in `builds/reports/` at these SHA-256 (first 16; each equals the build report's F5
  table): `E-39.md` `c69b8e5f7135ff4b`, `E-D5-D6.md` `883f2c723f7311e7`, `E-S1-blinding.md` `48db21e34736462a`,
  `E-misc.md` `ee94de5878d7be92`, `E-40.md` `a4ab238338a214e7`, `E-plan-updates.md` `3ff601d3c6e9cdc3`; the build
  report `E-records-build.md` `f1465f8b262f6527`.
- **Sources** read at `55d5f8b` with `git show 55d5f8b:<path>` (main checkout HEAD is `7452bd2`; `git diff --quiet
  55d5f8b HEAD -- scripts runkit experiments` exits 0, so the code is the same). FOCUS at `7452bd2` and `38e160d` was
  read only for the lead's rulings entry and the line shift.
- **Scope kept.** I edited no draft, no repository file and no other track's worktree. I wrote only under
  `builds/verify-E-records/v2/` and this report. No git command that changes state (read-only `log`, `show`, `diff`,
  `blame`, `status`, `rev-parse`, `ls-tree`; `git archive` only into my own folder, with every `*plant*` and `*decoy*`
  path excluded). No network, install, pod or API call. No reading, builder, overlap, claim, judge, seal, kit or
  launch command on real data.

Tags: (M) measured or checked here; (R) read in a source; (I) my inference.

## Verdict: defects

The fix round fixed round 1's nine defects as described (I re-checked D1, D3, D5, D7, D8 and D9 against the drafts
and sources). Citations are sound: my own range check passed 521 of 521 citations, my manual phrase checks (about 70,
section 5) all held, every "Old" block occurs exactly once in the plan, and the builder's `check_records.py` passes
when I re-run it. Every quoted stated reading matches its source. Nothing in the drafts reveals or depends on a
stage-1 outcome or a sealed choice. §40 follows the stage 1b check's corrections.

Three defects remain. The first can stop the reading after an outcome has been shown, against the lead's ruling
"never stopping the reading". The second leaves the rule that decides between D-5 and its fallback (c+) ambiguous,
and on track A's measured simulation it would send D-5 to (c+). The third leaves the lead's ruled reading-time
readers out of the revised plan.

## 1. Defects (most severe first)

### D1. D-5 "never stops the reading", but D-5's builder half can stop it, and the drafted step-2 text stops it deterministically after step 1

- **What is wrong.** D-5 item 4 puts the counts document and its two checks into the input builder (step 2)
  (`E-D5-D6.md:68-71`). Item 8 says "It never stops the reading" and covers only a refusal of the new reader at
  step 4b (`E-D5-D6.md:85-93`). §39 point 8(d) exempts only step 4b from S1 and S5 and quotes R1b, the builder's
  no-value pre-run, as R1D drafted it, without the counts option (`E-39.md:157-165`; R1D:524-529). The plan update adds
  the counts option to step 2 only, "after a no-value pre-run with `--no-overlap`" (`E-plan-updates.md:53`), and says
  of D-5 "A failure here is logged and never stops the reading" (`E-plan-updates.md:148-149`). Two paths stop the
  reading:
  1. **A counts check that fails refuses the whole builder.** In track A's build the check runs inside `build()`
     (`ws-a/scripts/stage1_s1/reading_input/build.py:710-713`); a refusal writes nothing, not even `tables.json`, so
     B16 cannot run. At step 2 that is R1D's S1 and S4 (R1D:562, :720, :727-730), after step 1 has printed B14's S-p
     verdicts (the first outcome lines, R1D:664).
  2. **Deterministic, if the drafts are followed:** R1D's step-2 check compares `sources.json` with the pre-run's after
     dropping only the overlap block and the two output hashes it knows (R1D:581-600). With the counts option at step
     2, `sources.json` carries `coherent: {cells, items, output_sha256}`. If R1b lacks the option (as the drafts quote
     it), the pre-run has `coherent: null`. If R1b has it, `coherent.output_sha256` still differs, because the counts
     document is bound to `tables.json`, whose bytes differ by the overlap block. Either way the check fails and the
     script stops at step 2 by S4.
- **Reproduction (M, synthetic data only).**
  - Command 1: in `builds/ws-a`, `PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B -m pytest -q -p no:cacheprovider
    --basetemp=<builds/tmp/verifyE2-wsa-095346> scripts/stage1_s1/reading_input/tests/test_coherent.py::test_the_builder_checks_its_own_counts`
    → `1 passed`, exit 0. The test asserts `rc == 2`, empty stdout, and that `tables.json`, the counts and the record
    are not written when one count disagrees (`test_coherent.py:157-174`).
  - Command 2: `builds/verify-E-records/v2/checks/prerun_vs_step2.py` (track A's builder on its own synthetic kit;
    R1D:582-598's comparison copied). Expected under "never stops": the step-2 comparison passes. Actual (exit 0):
    case A (R1b without the counts option): `"sources_without_overlap_and_output_hashes": false`, `coherent` null
    against `{"cells": 50, "items": 200, "output_sha256": "7bd9335d…"}`; case B (R1b with it):
    `false`, `output_sha256` `08632ccd…` against `7bd9335d…`. `tables_without_overlap` is `true` in both.
  - R1D's rehearsal (step 0.5) would catch path 2 before the reading, but the records would then be wrong, and the fix
    would need a new second stamp.
- **Correct text** (the lead chooses the remedy in (b); the rest is needed either way):
  - (a) Add to D-5 item 4: "The builder's no-value pre-run R1b uses the same counts option. The step-2 comparison
    with the pre-run leaves out `sources.json`'s `coherent.output_sha256` and the counts document's `input_sha256`, as
    it leaves out the HarmBench tables' (R1D:589-594). The counts' checks do not depend on the overlap block, so if R1b
    passes, step 2 cannot refuse for a D-5 reason."
  - (b) Add to D-5 item 8: "A builder refusal at R1b caused only by the counts shows no outcome (S2). Then [the lead's
    choice: either the counts option and step 4b leave the script, a new second stamp is made, and the record prints
    (c+)'s wording if its reader is verified, else (c)'s; or the cause is fixed under S2 with a new second stamp]."
  - (c) In §39 point 8(d), add a third change: "(iii) R1b takes the same counts option as step 2, and the step-2
    comparison leaves out the counts document's hashes".
  - (d) In plan item 3, replace "after a no-value pre-run with `--no-overlap`" by "after a no-value pre-run with the
    same options, `--no-overlap` in place of the four B14 options".

### D2. D-5's "verified" names no reading, replicate count or tail scope for its coverage test, and track A's measured block-A-only coverage falls outside the band

- **What is wrong.** Item 9 requires "90% coverage within 0.88-0.92 and a 0.75% tail within 1.5 × the primary form's
  tail in the same worlds" and says "A measured coverage outside the band triggers the fallback"
  (`E-D5-D6.md:101-103`; the same in plan item 7, `E-plan-updates.md:106`). It names no reading, no replicate count and
  no tail scope (per contrast or pooled). Its source, V1A §6 item 9, runs the simulation on "plan A, plan B, block A
  only" (V1A:349-350). Track A measured block A only at 2,000 replicates per world (Monte Carlo SE about 0.007):
  8 of 18 contrast-worlds meet the target, and B16's own primary form is miscalibrated there too (SD/SE 1.06-1.13)
  (`A-coherent-build.md:251-265`). The block-A-only reading cannot run now that block B is sealed (RI-O5;
  RI/build.py:606-607). Read with V1A's scope, item 9 sends D-5 to (c+) because of that reading. At 2,000 replicates a
  contrast-world whose true coverage is 0.885 also measures below 0.88 about a quarter of the time (I: 0.71 SE).
- **Reproduction (M).** Input: `E-D5-D6.md:94-103`, V1A:349-350, `A-coherent-sim-block_a-2000.json` (SHA-256
  `84d05e9c4654f079`, equal to `A-coherent-build.md:264-265`). Command: `/usr/bin/python3 -I` printing every `coverage_90`
  of that file. Expected: the record states which reading's coverage decides "verified". Actual: no reading named; the
  file gives S-G coherent coverage 0.876 (world ii, P5), 0.8765 (iii-answer, P4) and 0.8775 (iii-prompt, P6), outside
  0.88-0.92.
- **Correct text** (a scientific choice: the lead rules, and may raise it to GPT): "The coverage and tail criteria are
  read on plan A, the reading that runs (block B is sealed, so the block-A-only reading refuses, RI/build.py:606-607),
  at [10,000] replicates per world in each listed world, and on plan B as a check. The 0.75% tail is compared
  [per contrast / pooled over the contrasts of a world]. Block A only is reported as a limit, not gated, because B16's
  primary form is outside the band there too." Plan item 7's "Verified" takes the same scope.

### D3. The revised plan leaves out the reading-time readers that the lead ruled are built before the second stamp

- **What is wrong.** The lead's rulings entry: "The missing reading-time readers and LN-31's draw are built before the
  second stamp (fallback: after the reading, labelled 'code written after the reading')" (FOCUS:75 at `7452bd2`;
  FOCUS:74 at `38e160d`). Track D1 built five: F_k's planning power at the measured q (REV4:574), the stage-3 pick
  (REV4:428), LN-14's bar and LN-19's shares (REV4:554-555), the S-a shift line (REV4:276) and the cost per arm
  (`D1-readers-build.md:21-25`). D-6's trigger already counts "the reading-time readers" among "the other builds"
  (`E-D5-D6.md:172-173`). But the plan updates name D-5's reader, B14 under D-6, kit round 34 and D-7's draw, and none
  of these readers: not in the reading's steps (item 9, `E-plan-updates.md:143-150`), not in the second stamp
  (items 8 and 9, `:119`, `:131-135`), not in row 1d's suites and specs (item 13, `:197`), not in "what the lead can
  do now" (item 11, `:171`). After the edit the plan would no longer carry a ruled step for four pre-registered outputs.
- **Reproduction (M).** Command: `grep -c -i "reading-time\|fk_power\|stage-3 pick\|S-a shift\|cost per arm\|planning
  power\|LN-14\|LN-19\|reading_extra" E-plan-updates.md`. Expected: at least one match. Actual: `0`.
- **Correct text.** Item 9, after 4b: "4c. The reading-time readers (F_k's planning power at the measured q, REV4:574;
  the stage-3 pick, REV4:428; LN-14's bar and LN-19's shares, REV4:554-555; the S-a shift line, REV4:276; the cost per
  arm, REV4:103), each bound to `reading.json` by SHA-256, report only. Fallback: run after the reading, labelled
  'code written after the reading'." Items 8 and 9 (second stamp): add "the reading-time readers". Item 13 (row 1d):
  add "the reading-time readers' suite and spec". Item 11: add "the reading-time readers ($0)".

## 2. Notes (minor; not defects)

1. **S3 and S4 times swapped** (`E-misc.md:36-37`). R1B:71 dates S4's edit file 25 Oct 15:42 UTC and S3's 16:46 UTC.
   Correct text: "(S4's edit file dates from 25 Oct 15:42 UTC and S3's from 16:46 UTC; R1B:69-74)".
2. **"Can only mean B14's code" is stronger than the sources** (`E-misc.md:34-35`). R1B reads W1R:129 as "build deadline
   only" (R1B:61). Suggested: "W1R:129's 'B14 builds the strata at S1' could not be met for the strata themselves
   (S3's and S4's edit files did not exist until 25 Oct); it is read as B14's code, built and verified at S1
   (ADD:503); the strata are built later from the same inputs." The lead's ruling (a scheduling gap) stands either way.
3. **D-6's second trigger is not marked "added"** (`E-D5-D6.md:173-174`): "or `plan.json` shows a recipe other than S
   for any kit unit that B14 reads" goes beyond the brief's trigger; its sources are CRIT:347 and R1D:783. It is a
   sound guard, because the re-pin is a deny-list (refuses only G and B+Qi).
4. **The relabel text differs from the code's** (`E-D5-D6.md:83-84`). The record says "unscored answers counted Unsafe
   in every arm (not Gate B's adverse corner, PREREG §3 G3(a))"; track A prints V1A:363's "unscored counted Unsafe in
   every arm (not Gate B's adverse corner)" and a test pins it (`A-coherent-build.md:300-302`). The reading record copies
   by key, so the record should quote the code's text or say "as the reader prints it".
5. **§40 point 10's never-open wording** (`E-40.md:148-151`): "no file whose path holds 'plant' or 'decoy' is opened,
   except code" reads, taken alone, as forbidding point 5's hash of the planted_k37 edit file and its key-only binding
   check, the kit's packing of that edit and the pilot reader's reading of a0_plant units. Suggested: "… is opened by
   hand or by a helper, except code files; reviewed code reads such files by key only, or hashes them without showing a
   byte (points 3 and 5)".
6. **Row 13 against §40's S1 line**: the S1 record's row 13 lists the readings of §40 points 1, 2 and 4
   (`E-S1-blinding.md:66`); §40's S1 line names points 1, 2, 4 and 6 (`E-40.md:169`). Add "K7 after a 'go'" to row 13,
   or drop 6.
7. **Row 8 and §37's other points.** The brief names §37 as a whole; row 8 lists points 1-3 (`E-S1-blinding.md:61`).
   Points 4-6 are a check, operator rules and a not-built statement (ADD:644-646); say so under "Not listed". The same
   sentence could also name the post-W1 conditional reporting rules that did not change a label (§32 point 1's
   no-harm-sentence fallback, §34 point 3's B+Qi O fallback, §34 point 7's G9).
8. **ADD:428's optional re-run omits the z-level Φ script** (`E-misc.md:145-146`). The "every value <= 5%" reading
   cited at `E-misc.md:114` comes from `zphi.py` (b16-verify-stats.json:279-283, :367); the optional list names only the
   three scripts of b16-fix.json:269. Add `zphi.py` (it exists at the cited folder, M: `test -e`).
9. **D-7's "the inputs by SHA-256"** (`E-misc.md:88-89`): say that they are bound through block A's seal and
   `REJUDGED_PINS`, as track D2 built it (`D2-ln31-build.md:37-41`), so no sealed guard file is opened or hashed before
   the reading.
10. **The builder's two §24-point-4 texts are not separately pinned** (`E-39.md:122-126`): RI/__main__.py:45-46 (help)
    and :58-59 (refusal) both name the withdrawn fallback; track A edits that file anyway for D-5, so both can be
    corrected at no extra pin cost. B16's README:68 and settings `reading.json:200` do stay pinned.
11. **The extractor and a refused D-5 reader** (`E-39.md:152-156`): say that the extractor runs when the D-5 output is
    absent and then copies D-5 point 8's wording with the reason from the step's log.
12. **Implementation status, not a record defect:** item 9's "(added) at least 20 synthetic readings" reference check
    was not done by track A (`A-coherent-build.md:283`), so D-5 is not yet "verified" under item 9 as written.

## 3. The brief's items (a)-(h)

| Item | Result | Findings |
|---|---|---|
| (a) §39 | Every item of CRIT §2.1 is ruled: RI-O1 and RI-O5 to RI-O14 (quotes match RIB:412-466, M), R2, R3, R5, R6, R7, R9 (quotes match RI/hb_claim.py:75-96, M), README:153-159 and overlap R2-R6 (README:79-84, M), B16-D4-O2/O3 and B16-H-O9 (B16H:222-235, M), the coherence condition (reading.py:449, :485, :427-433; `2135c2d`, M), S-tok and §9.4, the runbook readings, the stamps (6 confirmations, 2 h, third stamp), "report and go on" (KW:3-13, M) | D1; notes 10, 11 |
| (b) D-5, D-6 | Rulings match the brief and FOCUS:75 at `7452bd2`: linearized table beside B16, B16 unchanged, pooled U, G2's counts, words and headline word under its own Φ (B16 has `labels.headline`, labels.py:120), both adverse corners, (c+) with "not verified after one fix round", (c) with four edits; D-6 settings-only, `--no-overlap` fallback; S1 lines and paper labels present | D1, D2; notes 3, 4 |
| (c) S1 blinding record | The brief's rules all listed; FOCUS numbering right (M: at `55d5f8b`, :135 final measurements, :138 verdict, :140 wave 1, :144 W1 commit; :134 funding event, :137 `--final` refusal, :139 wave 2 launch; at `7452bd2` all +2) | notes 6, 7 |
| (d) B14 gap and route | Matches the ruling; the CUDA-only chain holds (SIM:421-426; loaders.py:121-129; model.py:377-385, M); round 34 keeps every rules value the builder reads (M: the builder's `load_rules` list, sources.py:56-57, equals the record's list) | notes 1, 2 |
| (e) LN-31 / D-7 | Recorded as a deviation; LW-30 (REV4:762), LN-31 (REV4:763), HLC:164, :168 quoted correctly (M) | note 9 |
| (f) ADD:428 | The recorded run is the 22 Oct 22:07:04-23:02:02 Z run on the pre-fix build (b16-verify-stats.json:5-6, :9; SHA-256 `65fe90c3…`, M); the fix pass did not re-run it (b16-fix.json:269; `4090118e…`, M); B16 committed at `2135c2d` 00:40:40 Z (M). Cited with its limits, as briefed | note 8 |
| (g) §40 | All briefed rulings present and in line with CHECK's corrections (section 4) | note 5 |
| (h) plan updates | 14 of 14 "Old" blocks occur exactly once, at the cited lines (M); CRIT's six covered | D1 (item 3), D2 (item 7), D3 |

## 4. §40 against the stage 1b check's corrections

| CHECK correction | §40 | Check |
|---|---|---|
| 1.2 items 4-6: literal go rule, band [5, 10), sign c − m, re-pilot at 1101-1103 against Gate A's a0 | point 1 | holds (REV4:675, M; contrast.py:168-173, M) |
| Edges at 5 and 10 (CHECK:122-126) | point 1 "Edges (added)" | M: 627 of 2,000 three-seed means that are exactly 10 pp as rationals land below 10.0 in float, so the tolerance reading is needed to read the literal rule on exact shares |
| D6's interval: B16's paired form | point 2, no fallback | M: on a constructed table B16's frozen form gives Λ 10.67, SE 4.98, df 199, lower bound 4.26 ("stop"); the seed part alone gives SE 0.096, df 2, lower bound 10.49 ("go"), so READY's fallback would change the gate |
| B1: COMPLETE.json names the leaf; key-only readers; sentinel tests | point 3 | holds (build_plant.py:284, :307; edits.py:90-92; runner.py:496-497, M) |
| B2: counted score files under "plant", hashed and stamped before opening | point 3 | holds |
| B3: strike "publish readable" | point 4 | holds |
| B4: record READY's breach | point 10 | holds (MAN1:939-942 `06f70d98…`, :1107-1110 `c952eb72…`, M) |
| B5: `retrieved/` never opened | point 3 | holds, no time limit (FOCUS:74, M) |
| B6, B7 | point 3 | holds |
| §4: the pilot needs nothing sealed | point 12 | holds (RULES:171-183, M) |
| §5.1: one block P, kind "arm", sealed edit record, fingerprint record, A-C tables unchanged | point 5 | holds (RULES:294-315, :615-625; JR:896-900, :1039-1044; PT:791-795, M) |
| §5.2: binding check of planted_k37's SHA-256 | point 5 | holds (build_plant.py:290-291, M) |
| §5.3: K7 is new code; RPR k = 75 change | points 6, 13 | holds (runner.py:870-872, M) |
| §6 item 0: K7 after a go on its own pod; no judges; disjoint fallback | points 6-8 | holds (`labels.json` has no anchor key, M) |
| §6 item 3: Mac DataShield-style and L1 outputs if absent | point 4 | holds |

## 5. Citations I checked (opened at `55d5f8b` unless noted; all hold)

- **FOCUS** :74 ("joins the never-open list"), :76, :77, :99, :104 ("§24 point 4's fallback is withdrawn"; "nothing
  else pins B16's files"), :107 ("partly binding"; seal A), :113, :125, :126 (σ̂ 1.78), :131, :135, :136, :137, :138,
  :140, :144 (W1 ids `8fe5fe9`, `8901eed`, `f6283090`, `bc79b08`, `275c7fe6`, `7eccf9e9`); `38e160d`:74 and
  `7452bd2`:75 (the lead's rulings).
- **ADD** :298-299, :350-351, :375, :407, :422, :425-428, :435, :457, :470, :489-491, :501, :503, :506-508, :522 (quote),
  :600, :604-607 (D-4's trigger quote), :620, :625, :633, :635, :637-646, :657.
- **REV4** :29, :79, :158, :185, :227, :237, :264, :266, :270, :271, :275, :276, :285, :298-303, :394, :398, :400, :409,
  :410, :428, :451, :554-555, :562, :574, :611-614, :665-713 (incl. :675, :684, :692, :698-699, :706, :710), :719-721,
  :743, :757, :762-763, :876-887, :896-901, :919.
- **W1R** :129, :288-297, :358. **PREREG** :148-149. **LEDGER** :70, :72, :74, :387. **KW** :1-14. **OTSC** :1-101.
  **HLC** :3, :164-168. **PLANS** :172, :177, :179. **SPF** :344. **MAN1** :937-943, :1105-1111.
- **Code:** B16/reading.py:284-320, :415-492, :530-561 (blame of :427-433, :449, :485 = `2135c2d`);
  B16/contrast.py:84-85, :113-122, :168-173; B16/README.md:60-102, :135-170; B16/settings/reading.json:195-203;
  B16/labels.py:120; RI/build.py:1-20, :84-89, :134-147, :236-275, :530-560, :600-615, :665-674; RI/__main__.py:1-95;
  RI/items.py:1-12, :110-118; RI/hb_claim.py:1-46, :68-96; sources.py:50-60; STR:56-62; STRS:28-55; LC:140-175;
  GBR:236-245, :455-470; SIM:418-428; RULES:160-190, :294-315, :322-346, :500-512, :612-628; PT:789-796;
  JR:894-902, :1037-1046; edits.py:88-93; runner.py:494-498, :868-873; loaders.py:118-130; model.py:375-386;
  test_b14_report.py:383-401; oext_unit.json:56-63; oext_unit_y.json:55-62; build_plant.py:25-37, :276-316, :436-446.
- **Records:** RIB:5, :405-470; HBB:53-65, :188-192; B16H:218-245, :455-560; NOTES `b16-verify-stats.json` :1-12,
  :85-100, :189, :207, :230-262, :276-290, :340-375, :414, :474; NOTES `b16-fix.json` :1-10, :266-271.
- **Scratch reports** (SHA-256 prefixes match every short-name table, M): CRIT (whole), R1D :30-46, :165-182, :215-232,
  :305-320, :460-838; R1B :40-110, :140-300; V1A :98-135, :155-235, :270-370; D1A :490-515; READY :44-58, :222-230,
  :260-268, :352-362; CHECK (whole).

## 6. Sealed values

No draft states or relies on a U, HB, O, task-loss or coherence value of any stage-1 cell, a planted unit, leaf or
cell, or any sealed choice. The numbers the drafts carry are Gate B values already in FOCUS (wave 1, the verdict,
P5's band, σ̂), Gate A-era figures by name only, synthetic simulation results, costs and hashes. The S1 record lists
Gate B's §6 values as "possibly read" without quoting any (FOCUS quotes none, M).

## 7. Commands and tests I ran (exit 0 unless noted)

- `date -u` (5 times). Read-only git in the main checkout: `log`, `status --short`, `rev-parse`, `diff --stat`,
  `diff --quiet 55d5f8b HEAD -- scripts runkit experiments` (exit 0), `show <commit>:<path>` (43 source files into
  `v2/src/`), `show -s` of eight commits, `blame -L` of reading.py:427-433, :449, :485, `ls-tree`; `git archive 55d5f8b`
  of `scripts/stage1` and `scripts/stage1_s1` with `:(exclude)*plant*` and `:(exclude)*decoy*` into `v2/tree55/`
  (0 plant or decoy paths written, M). Both `v2/src/` and `v2/tree55/` were deleted after use (10:08 UTC); the four
  check scripts stay in `v2/checks/`. To re-run them, re-create the export with the same `git archive` command and
  pass the scratch paths shown in each script's docstring.
- `v2/checks/plan_old_blocks.py` (`/usr/bin/python3 -I -B`): 14 of 14 "Old" blocks once, at the cited PLAN lines.
- `v2/checks/cite_ranges.py`: 521 citations parsed, 0 out of range (one name, `B16/settings/reading.json`, checked
  by hand).
- The builder's `E-fix-checks/check_records.py`: `PASS` (14 old blocks; 763 citations in range; 107 of 107 phrases).
- `v2/checks/pilot_and_d5_checks.py` (venv Python, B16 imported read-only from `v2/tree55`): runs 1 and 2 exited 1
  (my script's bugs: zero seed variance made B16 refuse; fixed); run 3 exit 0, results in section 4 and: D-5's
  linearized table has prompt mean V, x = V at n = 0 and x = u/3 at all n = 3 exactly on 500 random cells.
- B16 targeted tests on `v2/tree55` (`PYTHONPATH` adds the main checkout for `experiments`; `-B -p no:cacheprovider`,
  basetemp under `builds/tmp/`, deleted): runs 1 and 2 exit 4 (import errors: `overlap_strata`, then `experiments`,
  missing from my export); run 3: **10 passed** in 37.0 s — `test_reading.py::test_coherence_flags_print_beside_the_word_and_never_change_it`;
  `test_fixes.py::test_a_coherence_failing_repair_never_dominates_in_family_1b`,
  `::test_the_per_actor_best_arm_names_an_arm_when_one_is_better_feasible_and_separated`,
  `::test_an_exact_5_pp_tie_reads_better_whatever_the_float_rounding`, `::test_the_tie_tolerance_is_1e_9_pp_from_the_settings`,
  `::test_better_holds_at_exactly_delta_minus_the_tie_tolerance`; `test_labels.py::test_separation_and_the_best_feasible_repair`;
  `test_overlap.py::test_the_block_is_report_only_and_absent_without_its_input`;
  `test_sensitivities.py::test_s_g_refits_hbc_on_each_variant`, `::test_equal_variance_flag`. Main checkout status
  of `scripts runkit experiments` stayed empty.
- In `builds/ws-a` (track A's tree, not edited; `git status --short` count 10 before and after):
  `test_coherent.py::test_the_builder_checks_its_own_counts` → 1 passed; `v2/checks/prerun_vs_step2.py` on a fresh
  synthetic kit (basetemp 45 MB, deleted) → exit 0, results in D1.
- `shasum -a 256` of the drafts, the scratch reports, the two NOTES records (opened by exact path), the block-A-only
  simulation file; `/usr/bin/python3 -I` printing that file's `coverage_90` values, and of `scripts/stage1/labels.json`
  only its top-level keys and the count of keys holding "anchor" (0) and of the string "disjoint" (0).
- `test -e` of four script names in NOTES `b16-verify-stats-evidence/scripts/` (all exist). No listing or grep of the
  NOTES folder.

## 8. Not verified, and limits

- R1B's parse of `plan.json` (recipe S on all arm and a0_arm jobs) and the plant-rank report's lines that §40 cites
  from CHECK: not reopened (`plan.json` lives in the kit folder; the report's settings path holds "plant").
- Whether DataShield-style and L1 outputs already exist on the Mac (§40 point 4): not checked (`tmp/`).
- D1's remedy (b) and D2's scope are the lead's rulings; I state the gap and the text, not the choice.
- The S1 record can only list what FOCUS and the records show was read; I checked consistency, not the lead's memory.

## 9. Replies to the builder's open points (F6)

1. Agreed (M): at `7452bd2` every FOCUS line from 74 on is 2 higher (:137, :140, :142, :146 checked). Keep the
   `55d5f8b` pin in the citation headers.
2. The 1e-6 tolerance is fine; the scope and replicate count of the coverage test matter more (D2).
3. No objection to leaving the identity-line option open.
4. Agreed (M): the seed-part-only interval turns a frozen "stop" into "go" on a constructed table (section 4).
5. I did not grep the notes folder; two records were opened by exact path and four names tested with `test -e`.
6. Point 6 (tie tolerance) is supported by measurement (section 4). Points 3, 7, 8, 9, 11 and 12 stand; D3 adds that
   the plan must carry the readers that point 11 calls separate rulings, since the lead has ruled them.
