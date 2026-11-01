# Final record files for the records commit (edits E1-E16 applied to the verified assembly)

- **Written** 2026-11-01, 17:33 UTC (clock checked with `date -u`; the Mac's local zone is IST) by a worker for the
  lead (GI VIII). Self-identification is not verification; the launcher records routing.
- **What this is.** The four assembled record drafts (`builds/assembled/repo/`, verified by `assemble-verify1.md`,
  verdict "verified") copied to `builds/final-records/repo/` at the same relative paths, with the lead's edits E1-E16
  applied and nothing else. Every edit is an exact find/replace pair in `check_final.py`; that script re-derives the
  four final files from the assembly (pinned by full SHA-256) and compares bytes: **exit 0 (PASS)** as run; one byte
  appended to a scratch copy of the SPF gave exit 1, "DIFFERS: docs/study-plan-full.md at line 621" (scratch copy
  deleted). A find text found other than exactly once makes it refuse (exit 2) before comparing.
- **Folder:** `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/final-records/`
  (below, `FINAL`); the assembly is `…/scratchpad/builds/assembled/` (below, `ASSEMBLED`); reports are in
  `…/scratchpad/builds/reports/` (below, `REPORTS`). Run:
  `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B FINAL/check_final.py` (`--write` rewrites the four files from the
  assembly; `--lines` prints each edit's line numbers).
- **HEAD.** The main checkout is at `657907e` (after `0435c3b`: `c21dccb`, the B14 test fix, and `657907e`, the merge of
  D-5, the readers and the draw). The three targets are byte-identical at `0435c3b`, `c21dccb` and `657907e` (ADD
  `f5a7c6bdb404f429…`, PLAN `121c5119d12e5bae…`, SPF `8aedcd4eee80953c…`; `git show <commit>:<path> | shasum`), so the
  assembly's base is still HEAD's text and these files apply cleanly. The S1 record is not tracked at HEAD (new file).
- **Hard rules kept.** No file under `tmp/stage1-olmo/`, `tmp/judge-pod*`, `tmp/hlc-inputs/`, `block-a/`, `block-b/`,
  any `units/` or `eval/` folder, any COMPLETE.json, answer, label, judge or bank file, or any path holding "plant" or
  "decoy" was opened, printed, grepped, hashed or listed. Git was read-only (`rev-parse`, `log --oneline`, `ls-files`
  of `reading/b14/`, `reading/lead-reports-20261101/build-round/` and the rulings path, names only; `show
  <commit>:<path>` of the three targets, the rulings file, the six `reading/b14/` files, the seven `reading_input`
  files and FOCUS at `38e160d` line 74, piped to `shasum` or `sed`; `diff --name-status`, names only). The main
  checkout was not edited. No network, install, pod, background job or pytest. The patched `check_records.py` copy
  (section 6) skips `scripts/stage1/build_plant.py` instead of opening it.

## 1. The four final files

| Path (under `FINAL/repo/`) | Assembled SHA-256 (base) | Final SHA-256 | Lines |
|---|---|---|---|
| `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` (ADD) | `097a21e27d83737fa8e29e1232f95fddb538fea1ff06f9ce93266a52f57cc410` | `93c5832178be599ddbb9ff7e19cb2e247f12fe2db960f1fd21eb645adb2819a9` | 1,552 (was 1,525) |
| `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` (PLAN) | `da4bd3a999d942b46037662678db048a847294b1c8f85f8a95d2019e0e019ec4` | `28bb29093992a57fae4333233cd90f551b81fd75a471134466175b75a48f5da8` | 95 |
| `docs/study-plan-full.md` (SPF) | `df1067d9395a0ad48cd90eb1da69fb3d97fe69db70a81ba2e0b0580f8ea379a4` | `64db9f91de4de3226cd44a16d58edeab54eb69f650b19a553b08be4b17ca864a` | 620 |
| `.ai/inputs/stage1-post-w1-20261023/reading/s1-blinding-record-20261101.md` (S1R) | `4f195872838896e66be2eeee99d0e46f127edae7f3ded323e2cb0313c4e84b37` | `9e4c7b111ab328ae024a3ac4c8f045496c5174fdbeb8a537cb18f7d0325231c5` | 90 (was 88) |

`check_final.py`: SHA-256 `c0bab4b5d9098b1e0824be362eeafc37a59ce4128fd4f001dd998472a9bdc06e`. The diff of each final file
against its assembled copy: `diff -u ASSEMBLED/repo/<path> FINAL/repo/<path>`. ADD: 26 lines added and 1 re-wrapped
paragraph; PLAN: 4 places; SPF: 2 lines; S1R: 2 lines added, 8 cells or lines changed. No CR, tab or trailing space
was added; each file ends with one newline; no changed non-table line is longer than 120 characters.

## 2. The edits, one by one (file; assembled line → final line; old text; new text)

Multi-line texts are shown as they are in the files (the ADD's nested points keep their 3-, 5-, 6- or 7-space
indent). For the four long table rows (E1, E2, E13b, E13d) the changed fragment is shown; the rest of the row is
unchanged. The verbatim pairs are the `EDITS` list of `check_final.py`.

### E1. ADD, the LR row of the short-name table (line 689 → 689)

Old (fragment): `cited by section R1-R6; today in the lead's scratch `builds/`, to be committed under `lead-reports-20261101/build-round/` `[FILL-hash]` |`

New (fragment): `cited by section R1-R6; committed at `.ai/inputs/stage1-post-w1-20261023/reading/lead-rulings-20261101.md` (SHA-256 `3096e37a09ac565aab5b7fe0ad2d38e1871d28d181f664a40b6c09b2539c1586`) |`

Checked (M): `git show HEAD:.ai/inputs/stage1-post-w1-20261023/reading/lead-rulings-20261101.md | shasum -a 256` gives
`3096e37a…1586`, equal to the scratch copy `builds/lead-rulings-20261101.md`.

### E2. ADD, the build-round reports row (line 690 → 690)

Old (fragment): `(LR R6.5) with their final SHA-256 `[FILL-hash]` (a fix round appends to a build report and moves no earlier line)`

New (fragment): `(LR R6.5) with their final SHA-256 committed byte-equal under `.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/build-round/`, whose SHA256SUMS file lists every hash (a fix round appends to a build report and moves no earlier line)`

See open point 2: at HEAD `657907e` that folder holds B's and C's reports and no `SHA256SUMS` yet.

### E3. ADD, D-5 item 10 (lines 812-813 → 816-820)

Old:
```
   10. **Records:** SPF:344 adds D-5; FOCUS records the reader's and the builder's new hashes `[FILL-hash]`; the
       reader, its settings and this record fall inside the second stamp (PLAN:39-40).
```
New:
```
   10. **Records:** SPF:344 adds D-5; FOCUS records the reader's and the builder's new hashes (SHA-256, first 16:
       `coherent.py` `9f3010fb52ea6459`, `sg_coherent.py` `a0b001f7f40c1d2f`, `items.py` `70a52ca84d604b81`, `build.py`
       `e82214e718302563`, `__main__.py` `992787928667fe22`, `__init__.py` `3efbc49e298a64c8`,
       `mutants_reading_input.json` `52f231ed9c6d787f`; FOCUS records them at the records commit); the reader, its
       settings and this record fall inside the second stamp (PLAN:39-40).
```
Checked (M): the seven prefixes equal `git show HEAD:scripts/stage1_s1/reading_input/<file> | shasum -a 256` at
`657907e` (the spec is `reading_input/mutation/mutants_reading_input.json`); they are also the hashes
`A-coherent-verify2.md` §2 names.

### E4. ADD, D-6 item 2 (lines 890-891 → 901-905)

Old:
```
      machine allows (LR R2.2). This record states which set ran: `[FILL: the 69-entry near set / the full 150-entry
      spec]`, result `[FILL]`.
```
New:
```
      machine allows (LR R2.2). This record states which set ran: the 69-entry near set ran at 53f746d with the
      official runner: 68 killed and 1 invalid (B14S-s-p-role-primary-repinned: the module fixtures world and synth of
      test_b14_inputs.py raised at setup, 61 errors). Commit c21dccb fixed the test file only (the fixtures return the
      failure text and each test reads them through need(), track A's pattern); that entry was then killed with 115
      failures and 0 errors. The full 150-entry spec ran at c21dccb: [FILL-b14-full].
```
The text is the task's, verbatim (commit ids and file names without backticks, as given); `[FILL-b14-full]` stays.

### E5. ADD, D-5 item 9, the replicate rule (lines 809-811 → 809-815)

Old:
```
      per contrast 0.61-1.35), plan B 6 of 6 at 20,000, block A only 8 of 18. By the replicate rule at least one plan-A
      world must also pass at 10,000 (its lowest coverage 0.891 is within 0.0134 of 0.88; its highest tail ratio 1.35 is
      above 1.3); the 10,000-replicate run is the lead's (ACB:267-268) and the re-verify reads it (LR R1.1).
```
New:
```
      per contrast 0.61-1.35), plan B 6 of 6 at 20,000, block A only 8 of 18. By the replicate rule four plan-A
      contrast-worlds must also pass at 10,000 (i: P5, tail ratio 1.35; ii: P4, coverage 0.8915; ii-low: P6, 0.9090;
      iii-prompt: P6, 0.9075). All four pass at 10,000 replicates: coverage 0.8921-0.9036 and tail ratios 0.75-1.18 in
      the first verifier's two worlds (ii-low, iii-prompt), coverage 0.8974-0.9004 and ratios 0.82-1.16 in the
      re-verifier's two (i, ii) (the independent re-verify of 1 Nov, `A-coherent-verify2.md` §3; LR R1.1). 51 of 51
      plan-A contrast-worlds in the builder's and the first verifier's evidence (18 at 2,000, 33 at 10,000) meet the
      band and the tail ratio: the gate is met.
```
Numbers quoted from `REPORTS/A-coherent-verify2.md` §0 item 3 and §3 ("The four worlds at 10,000 replicates" table:
i and ii run by the re-verifier, ii-low and iii-prompt by the first verifier; "Gate: met. 51 of 51 … (18 at 2,000,
33 at 10,000)"). The old clause "the 10,000-replicate run is the lead's (ACB:267-268)" is dropped: the 10,000 runs
were the two verifiers'.

### E6. ADD, D-5, a status sentence before the fallbacks (inserted before line 821 → lines 828-830)

Old:
```
   **Pre-set fallback (c+).** *Trigger:* D-5 is not verified after one fix round
```
New:
```
   Status at the records commit: D-5 is verified after fix round 1 (the independent re-verify of 1 Nov,
   A-coherent-verify2.md); fallbacks (c+) and (c) are not used, unless the pre-run of the reading refuses on a
   coherent-only check (item 8).

   **Pre-set fallback (c+).** *Trigger:* D-5 is not verified after one fix round
```
Placed as its own paragraph after "Reasons" and before "Pre-set fallback (c+)"; the fallback texts are unchanged (the
(c+) paragraph still says "its re-verify runs now", kept as the task asks).

### E7. ADD, D-5 item 7, the symmetric table's label: no change needed (lines 770-771 → 770-771)

The assembled text already quotes the label exactly as the code prints it: `"unscored counted Unsafe in every arm
(not Gate B's adverse corner)"`, wrapped across lines 770-771 (checked byte for byte with `od -c` against
`ws-a/scripts/stage1_s1/reading_input/sg_coherent.py:72`, `SYMMETRIC_LABEL`). The draft wording the verifier's N2
flagged ("unscored answers counted … PREREG §3 G3(a)") was already fixed in track E's fix round 2. `check_final.py`
asserts the exact label (whitespace-collapsed) occurs once in the final ADD.

### E8. ADD, D-7 reading 7 (lines 1253-1256 → 1279-1283)

Old:
```
      the minimums, and answers for the proportion. Reading 7: the protective reading, under which rule b also reads the
      greedy harm answers' categories. Reading 11: the benign block is each population unit's own greedy over-refusal
      answers with their stored full-answer "Refusal" flag. Reading 12: theta0's Unsafe cell also takes the HarmBench
      split. Reading 13: a cell's target is cut to its distinct available prompts, and any rest flows to the next cell.
```
New:
```
      the minimums, and answers for the proportion. Reading 7: the protective reading, under which rule b also reads the
      greedy harm and greedy over-refusal answers' categories. Reading 11: the benign block is each population unit's
      own greedy over-refusal answers with their stored full-answer "Refusal" flag. Reading 12: theta0's Unsafe cell
      also takes the HarmBench split. Reading 13: a cell's target is cut to its distinct available prompts, and any rest
      flows to the next cell.
```
The one wording change is "greedy harm answers' categories" → "greedy harm and greedy over-refusal answers'
categories" (D2B:378-379: "sampled harm, greedy harm and greedy over-refusal answers"); the three lines after it
are re-wrapped only (the paragraph grows by one line). See open point 4.

### E9. ADD, §39 point 8(d)(i) (lines 1053-1054 → 1067-1069)

Old:
```
     any `"pass": false`: the script stops", R1D:720) and S5 do not apply to D-5's reader (step 4b) or to the
     reading-time readers (step 4c, point 11): a non-zero exit or refusal there is logged, the script goes on, and
```
New:
```
     any `"pass": false`: the script stops", R1D:720) and S5 do not apply to D-5's reader (step 4b), to the
     reading-time readers (step 4c, point 11) or to LN-31's draw (step 5, D-7: report only, REV4:762; point 13
     ruling 3): a non-zero exit or refusal there is logged, the script goes on, and
```
(The find text starts at "and S5 do not apply"; the line's start is unchanged.) See open point 5.

### E10. ADD, §39's closing S1 line (lines 1345-1346 → 1372-1373)

Old:
```
outcome was read. The paper labels points 1-9 and 11 "fixed after Gate B wave 1". Point 10 is the user's decision,
not an inference rule.
```
New:
```
outcome was read. The paper labels points 1-9 and 11 "fixed after Gate B wave 1". Point 10 is the user's decision,
not an inference rule. Points 12, 14 and 15 are records, not inference rules; point 13 (D-7) carries its own S1 line.
```

### E11. Draft-process wording (three places)

- E11a. ADD, §40's Citations bullet (lines 1366-1368 → 1393-1395). Old:
  ```
    is cited from CHECK. Of the code file `scripts/stage1/build_plant.py` I opened lines 282-287 and 306-308 (round 1),
    and lines 30-37 and 276-315 and a `grep` of its output paths and record keys (fix round), all at `55d5f8b`: code
    only, under the brief's code rule; no settings, record or output file of the plant was opened.
  ```
  New:
  ```
    is cited from CHECK. Of the code file `scripts/stage1/build_plant.py` the drafter opened lines 282-287 and 306-308
    (round 1), and lines 30-37 and 276-315 and a `grep` of its output paths and record keys (fix round), all at
    `55d5f8b`: code only, under the brief's code rule; no settings, record or output file of the plant was opened.
  ```
  "I opened" → "the drafter opened" (lower case, mid-sentence; the same facts); the three lines are re-wrapped only.
- E11b. ADD line 1369 → 1396. Old: `- "Added" marks a ruling this draft adds to the brief's list; the lead keeps or drops it.`
  New: `- "Added" marks a ruling this record adds to the brief's list; the lead keeps or drops it.`
- E11c. S1R line 47 → 49. Old: `"Added" marks a rule this draft adds to the brief's list; the lead keeps or drops it. "§6 possibly" = …`
  New: `"Added" marks a rule this record adds to the brief's list; the lead keeps or drops it. "§6 possibly" = …`
  (the sentence's rest unchanged). No other "this draft" or first-person sentence exists in the four files (grep).

### E12. ADD, §39 point 12, a "Done (1 Nov)" paragraph (inserted after line 1209 → lines 1226-1235; point 13 now starts at 1237)

Old (the paragraph break between the "Last resort" paragraph and point 13):
```
   $6 + the pod's cap × $1.85 (R1B:255-256; CRIT:348).

13. **Post-W1 deviation D-7:
```
New:
```
   $6 + the pod's cap × $1.85 (R1B:255-256; CRIT:348).

   **Done (1 Nov).** Block sim's pod was created at 14:11:56 UTC; its job started at 14:47:49 and was verified and
   stopped at 14:51:26 (pod time 0.66 h, about $1.21; the pod is stopped, not deleted). The design's Mac pre-check ran
   before the pod (eval 200; 48 rows in each add set). `similarity.json` (SHA-256
   `811efe4a6d598df670d463fe343d389fed689883745363264e701a36cde4b997`) and `strata/strata.json`
   (`2d996a99a49eed696c3ec047b4184b9ced7db60f29bd151d25e219b1142890f2`) were sealed in FOCUS at `b5e3c27`, before any
   add-arm outcome was read. The B14 inputs file `inputs/overlap_inputs.json`
   (`91baaa5302a8f96c19ca6e568cb77f66a578ceb866a2236ac3f3f4d8a5144271`; 24 units) binds `plan.json`
   (`b1965c74c4933059fc0123c5f7312cebc2084ba21b66de1a0115457a2ae4039e`), so `plan.json` must not change before the
   reading. All three are under `.ai/inputs/stage1-post-w1-20261023/reading/b14/`. Kit round 34's 39 mutation ids: 39
   killed, none unexpected.

13. **Post-W1 deviation D-7:
```
Source: `builds/lead-notes-for-records.md` items 3-5 (item 5 gives the sub-paths `strata/strata.json` and
`inputs/overlap_inputs.json`). Checked (M): `git ls-files` of `reading/b14/` lists `similarity.json`,
`strata/strata.json`, `inputs/overlap_inputs.json` (and three kit records); `git show HEAD:<path> | shasum -a 256`
gives exactly the three hashes above. `plan.json`'s hash is the lead's (not hashed here: it is under `tmp/stage1-olmo/`).
"24 units" and the pod times, cost and mutation counts are the lead's notes, not re-measured.

### E13. PLAN (four places)

- E13a. Row 1d (line 35 → 35). Old (fragment): `the reading-time readers' suite and spec (49 entries; `cost_table` after its fix round)`.
  New (fragment): `the reading-time readers' suite and spec (62 entries; `cost_table` after its fix round)`.
  (D1B:418, :520: the spec grew 49 → 62 in fix round 2.)
- E13b. Row 1b, the end of its "What" cell (line 33 → 33). Old (fragment): `D-6 (§39 point 2) re-pins its settings before the strata are made. |`.
  New (fragment): `D-6 (§39 point 2) re-pins its settings before the strata are made. Done at `b5e3c27` (1 Nov): the pass ran on one A100 pod, the strata are sealed in FOCUS and the inputs file is written and checked (§39 point 12). |`.
  The row's structure and its other cells are unchanged.
- E13c. Step 0 (lines 44-47 → 44-47). Old:
  ```
     reading script, B14's inputs file, `similarity.json` and the strata, the reading-time readers (`reading_extra/`),
     the D-7 draw script, and the records (addendum §39 and §40, D-5 to D-7, the S1 blinding record), and start step 1
     only after that second stamp is anchored, with at least 6 confirmations and 2 h after its block's header time
     (§39 point 9).
  ```
  New:
  ```
     reading script, B14's inputs file, `similarity.json` and the strata (written and sealed at `b5e3c27`), the
     reading-time readers (`reading_extra/`), the D-7 draw script, and the records (addendum §39 and §40, D-5 to D-7, the
     S1 blinding record), and start step 1 only after that second stamp is anchored, with at least 6 confirmations and
     2 h after its block's header time (§39 point 9).
  ```
  One parenthesis added; the rest re-wrapped.
- E13d. "What the lead can do now" item 1 (line 88 → 88), a judgment call (section 4). Old (fragment):
  `1b (kit round 34, then one pod: about $0.60–0.75, worst about $2.7–3.1 at its cap, from the balance above the $6 reserve).`
  New (fragment): `1b (kit round 34, then one pod: about $0.60–0.75, worst about $2.7–3.1 at its cap, from the balance above the $6 reserve; done at `b5e3c27`, about $1.21).`
- Not changed: step 1's command placeholders `<sealed strata.json>` and `<committed B14 inputs file>` (they name
  the files, not a to-do).

### E14. SPF (two lines)

- E14a. Line 8 → 8. Old (fragment): `D-1 to D-4 are recorded deviations in ADD`. New: `D-1 to D-7 are recorded deviations in ADD`.
- E14b. Line 27 → 27. Old (fragment): `(the lead's recorded rulings §1-§38)`. New: `(the lead's recorded rulings §1-§40)`.
  Both texts were checked first (`grep -n`); each occurs once.

### E15. S1R (the fallback bullet, six cells, line 81)

- E15a. After the Written bullet (lines 3-4; the new bullet is lines 5-6). Old:
  ```
    named in the second stamp's manifest.
  - **Citations** are
  ```
  New:
  ```
    named in the second stamp's manifest.
  - Pre-set fallback: the same list in the reading record's limits section; trigger: this record is not committed when
    the records step starts (CRIT:352).
  - **Citations** are
  ```
- E15b. Rows 10-15, the "Written (UTC)" cell (lines 62-67 → 64-69); each `[FILL]` becomes one of the two strings:

  | Row | Cell now | Why (decided from the row's content) |
  |---|---|---|
  | 10, D-5 | `2026-11-01T04:55 (ruled); formal text [FILL-time]` | the FOCUS entry of 04:55 UTC (`38e160d`, line 74; read with `git show`) rules D-5: the linearized table beside B16, per-arm pooled coherent-only U, G2's counts, its own Φ run, never stopping the reading, both adverse G3a corners, fallback (c+). The "verified" rule (LR R1.2) and the pre-run rule (LR R6.1) came at 14:02; the rule itself was first written at 04:55 |
  | 11, D-6 | `2026-11-01T04:55 (ruled); formal text [FILL-time]` | the 04:55 entry rules D-6 (a settings-only re-pin; G and B+Qi refused; fallback `--no-overlap`). The limit (LR R2.1) came at 14:02 |
  | 12, ADD §39 points 3-9 | `2026-11-01T04:55 (ruled); formal text [FILL-time]` | the 04:55 entry rules the runbook's stop rule and the stamps (points 8 and 9: "stop on identity lines only; time stamps need 6 confirmations and a start 2 h after the header time; a third stamp"). Points 3-7 are stated readings adopted by the formal text; the record's own paragraph (S1R:79-84) says part of this row was first written at 04:55 |
  | 13, ADD §40's readings | `2026-11-01T04:55 (ruled); formal text [FILL-time]` | the 04:55 entry rules §40: the go rule read literally, key-only readers, `retrieved/` never opened, construction checks committed and stamped unopened, kit round 35, K7 after a "go". The edges (tie tolerance) and "no fallback" for the interval came at 14:02 (LR R6.5) |
  | 14, D-7 | `2026-11-01T14:02 (ruled); formal text [FILL-time]` | the 04:55 entry only schedules the draw's build ("built before the second stamp"); the deviation, its confirmed readings and HLC 4.3 item 4 are LR R5 (14:02) |
  | 15, the reading-time readers | `2026-11-01T14:02 (ruled); formal text [FILL-time]` | the 04:55 entry only schedules the readers' build; their adopted readings K2 extended, K5, K6, K7 and the never-open exception are LR R4.3-R4.4 (14:02) |

- E15c. Line 81 → 83. Old (fragment): `formal text carries [FILL].` New: `formal text carries [FILL-time].` (the
  formal text's time is the records commit, the marker the lead fills). See open point 7.

### E16. The rulings file's location

The only line that said the rulings file is in scratch is the ADD's LR row (line 689), fixed by E1. The other
"scratch" mentions (ADD 674, 690, 719, 864, 1051, 1333, 1358, 1441; PLAN 90) are about reports, trees or folders, not
the rulings file; the S1R (line 12) and §40's Sources bullet point to §39's table. `check_final.py` asserts that
"today in the lead's scratch `builds/`" is absent from the final ADD and that the committed path with the full hash
occurs once.

## 3. Markers left for the lead (all counted by `check_final.py`)

- ADD: `[FILL-time]` 7 times (lines 661, 859, 926, 1296, 1370, 1375, 1550: §39's heading, D-5's, D-6's and D-7's S1
  lines, §39's closing S1 line, §40's heading, §40's S1 line); `[FILL-b14-full]` once (line 905); `[FILL AT W1-P]`
  once (line 384, HEAD's own §12 text). No `[FILL-hash]`, `[FILL]` or `[FILL:` remains (checked with `grep -n`).
- S1R: `[FILL-time]` 8 times (line 3, rows 10-15, line 83). PLAN and SPF: none.

## 4. Judgment calls the lead may change (each is one find/replace pair in `check_final.py`)

1. E13d (PLAN line 88) is included because "What the lead can do now" item 1 describes 1b (the pod) as still to do;
   the task's parenthetical names only row 1b and step 0. Drop the pair if it goes beyond the list.
2. E4's and E6's texts are the task's sentences verbatim, so their commit ids and file names carry no backticks,
   unlike the rest of the file. E3's list and E12's paragraph are this worker's wording with backticks.
3. E5 drops "the 10,000-replicate run is the lead's (ACB:267-268) and the re-verify reads it" and names the two
   verifiers as the runners of the 10,000-replicate worlds (A-coherent-verify2.md §3). If the lead wants that clause
   kept, add it back after "(LR R1.1)".
4. E8, E11a and E3 re-wrap lines after the change so that no line exceeds 120 characters (words unchanged).
5. E11a keeps the sentence's order ("Of the code file … the drafter opened …"), lower case, rather than starting the
   sentence with "The drafter".
6. E9 adds the draw to the list and the two citations only; the sentence's tail still names "D-5 point 8's wording
   (or the reader's "not computed")" as what the record prints (open point 5).

## 5. `check_final.py` (M)

- As run (`PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B check_final.py`, Python 3.11.15 at `/usr/bin/python3`):
  "equal" for all four files with the hashes of section 1, `PASS`, exit 0. `--write --lines` was used twice to write
  the files (the second time after the E8 and E3 re-wraps); `--lines` output gave the line numbers above.
- Failure path: a copy of `FINAL/repo/` and the script under `FINAL/ft/` (the assembled path redirected), one byte
  appended to the SPF copy → exit 1, `DIFFERS: docs/study-plan-full.md at line 621`, `FAIL`; `FINAL/ft/` deleted. The
  assembled copies are pinned by full SHA-256 (refuses with exit 2 if a base differs); every find is counted on the
  progressively edited text (refuses with exit 2 if not exactly once); E7, E16 and the marker counts are asserted.
- No `__pycache__` or `.pyc` was written (`-B`, `PYTHONDONTWRITEBYTECODE=1`; checked with `find`).

## 6. `check_records.py` on the final files (M)

`REPORTS/E-fix-checks/check_records.py` reads six draft files by fixed name from a folder, a `lead-rulings-20261101.md`
in that folder's parent and the eleven build-round reports, and checks: (1) each Old block of `E-plan-updates.md`
occurs once in the PLAN at `55d5f8b`; (2) every `NAME:line` and `path:line` citation in the six files is within its
source's line count (`git show 55d5f8b:<path>`, the committed design-round copies at `0e0ab1f`, the build-round
reports and LR); (3) 244 phrase checks against the sources; (4) the committed design-round copies' SHA-256; (5) stale
text. It was pointed at the final files so:

- `FINAL/check-input/` holds: `E-39.md` = lines 661-1552 of the final ADD (§39 and §40); `E-S1-blinding.md` = the
  final S1R; `E-misc.md` = the final PLAN; `E-40.md` and `E-D5-D6.md` empty; `E-plan-updates.md` and the eleven
  build-round reports as symlinks into `REPORTS/`; `FINAL/lead-rulings-20261101.md` a symlink to
  `builds/lead-rulings-20261101.md`. The SPF is not included: its `[FOCUS:9]`-style tags are at commit `5f11726` by
  design, so the script's `55d5f8b` bounds would not apply.
- `check_records_patched.py` (SHA-256 `2fbafb80cb13eaee…`) is the script with one change, because this worker's
  rules forbid opening any path holding "plant" or "decoy", code files included (the original opens
  `scripts/stage1/build_plant.py` with `git show`, under the drafters' code rule): such paths are skipped for every
  file type, and a phrase check on a skipped path is counted as "not checked" and listed. The diff against the
  original is four lines (marked `# PATCH`); printed in the worker's report and reproducible with `diff`.
- Result (`FINAL/check-input/check_records_run.txt`), exit 0: `[1] old blocks 14, new blocks 14, each old block once
  in PLAN: True`; `[2] citations parsed 909; out of range: 0; not opened: ['scripts/stage1/build_plant.py']`;
  `[3] phrase checks: 244 of 244 hold; not checked (never-open paths): 7` (the seven `build_plant.py` phrases of §40,
  which the drafters checked in their rounds); `[4] committed copies at 0e0ab1f: 8 hashes checked; mismatches: 0`;
  `[5] stale text: 0 hits`; `PASS`. Run twice (before and after the E8/E3 re-wraps), same result.

## 7. Open points for the lead

1. **SPF:344's tag `[ADD:446-648, ADD:661-1346]` is now stale** and was not changed (not in the edit list; the
   assembly README and `assemble-verify1.md` note 9 said it moves if §39 is edited). In the final ADD §39 runs from
   line 661 to line 1373 (the last non-blank line before `## 40.` at 1375). The one-token fix is
   `[ADD:661-1346]` → `[ADD:661-1373]` in `docs/study-plan-full.md` line 344; it is the only citation of §39 by line
   range in the four files (`grep -rn '1346\|ADD:661'`).
2. **E2's text presumes the records commit.** At HEAD `657907e`, `reading/lead-reports-20261101/build-round/` holds
   B's and C's reports, the near-mutant files and three JSON reports, but no `SHA256SUMS` and no A, D1, D2 or E
   report (names only, `git ls-files`). The row also still opens with "today in the lead's scratch `builds/reports/`,
   to be committed under `lead-reports-20261101/build-round/`" (kept: E2 fills only the marker; E16 is about the
   rulings file). Both read right only once those files and `SHA256SUMS` are committed with the records.
3. **The ADD grew by 27 lines, all inside §39** (E3 +3, E4 +3, E5 +4, E6 +4, E8 +1, E9 +1, E12 +11); §40 moved from
   1348 to 1375. No record cites §39 or §40 by ADD line except SPF:344 (point 1).
4. **E8's "also".** Before the protective reading, rule b already read the sampled harm and greedy over-refusal
   answers (D2B:154); the reading adds greedy harm (LR R5.1: "the protective reading that adds greedy harm
   categories"). The edited sentence now says "also reads the greedy harm and greedy over-refusal answers'
   categories", which is true of the rule but blurs what was added. D2B:378-379's form, "every answer of the
   population to the prompt: sampled harm, greedy harm and greedy over-refusal answers", would be exact.
5. **E9 names no print for a draw failure.** The sentence's tail still says the record prints "D-5 point 8's
   wording (or the reader's "not computed")"; for the draw, PLAN step 5 says "not run at the reading" and point 13
   ruling 3 gives the fallback. One clause would close it if wanted.
6. **PLAN row 1b** still opens "**B14's similarity pass never ran** … no `similarity.json` or `strata.json` exists"
   (the 31 Oct finding), followed by the new "Done at `b5e3c27`" sentence; the task said to keep the old structure.
7. **S1R lines 79-84** say "Both times come after every Gate B value above" (04:55 and the formal text); rows 14 and
   15 now cite 14:02 as well. True as written (14:02 is also after every Gate B value); the lead may add "and the
   14:02 rulings".
8. **`[FILL-b14-full]`** (ADD line 905) waits for the full 150-entry spec's result; the eight `[FILL-time]` markers
   of each record wait for the commit time. Filling them changes the bytes, so `check_final.py` is for the state
   before those fills (as `check_assembly.py` was for the assembly).
9. **Scaffolding in `FINAL/`:** `check-input/` (section 6) and the symlink `FINAL/lead-rulings-20261101.md` are for
   the `check_records` run only; they are not part of the records.

## 8. Commands run (exit 0 unless noted; none longer than a few seconds except `check_records` at about 40 s)

- `date -u` (three times); `ls`, `find`, `wc -l`, `cat -n`, `sed -n`, `grep -n`, `od -c`, `tail -c`, `fold`, `cut`,
  `awk`, `shasum -a 256`, `diff -u` (exit 1 for differing files, as expected) on the assembly, the reports, the
  rulings, the lead's notes, `ws-a/…/sg_coherent.py` lines 60-80, and the final files.
- Read-only git in the main checkout: `rev-parse HEAD`, `log --oneline -10`, `ls-files` (`reading/b14/`,
  `build-round/`, the rulings path, the S1 record path, the spec path), `show <commit>:<path> | shasum -a 256` for the
  three targets at `0435c3b`, `c21dccb`, `657907e`; the rulings file; the six `reading/b14/` files; the seven
  `reading_input` files; `show 38e160d:research/FOCUS.md | sed -n 74p`; `diff --name-status 0435c3b HEAD` (names,
  filtered). One compound command failed on a zsh glob in an `echo` (`HEAD?`, exit 1) after its git output printed;
  rerun without it.
- `check_final.py --write --lines` (twice; exit 0), `check_final.py` (exit 0), the failure-path copy (exit 1);
  `check_records_patched.py` (twice; exit 0). One inline Python (the patch writer, exit 0). No pytest, no basetemp,
  no background job, no network, no pod.
