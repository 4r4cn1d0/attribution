# Assembled record drafts (scratch copies for the lead's review)

- **Written** 2026-11-01, 15:05 UTC (clock checked with `date -u`), by a builder for the lead (GI VIII). Self-identification
  is not verification; the launcher records routing.
- **What this is.** The six verified E-track drafts (fix round 2; `E-records-verify3.md` verdict "verified", SHA-256
  `fab42c10dfaa33b9…`) assembled into scratch copies of their target files under `repo/`, each started from the main
  checkout's HEAD. Nothing in the repository was edited; no git state changed (read-only `rev-parse`, `log`, `show`,
  `diff --name-status`, `ls-files` only). No stage-1 outcome was read and nothing on the never-open list was opened,
  listed, grepped or hashed. No test, builder, reading, kit or launch command ran; no pytest, so no basetemp folder.
- **Folder:** `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/assembled/`
  (below, `ASSEMBLED`). The drafts are in `…/scratchpad/builds/reports/` (below, `REPORTS`).
- **The assembly rule is code:** `ASSEMBLED/check_assembly.py` (SHA-256 `a7c1654cea8d337c…`). `--write` made the copies
  once; without it the script re-derives every file from `git -C /Users/spiderishi/Coding/attribution show HEAD:<path>`
  and the drafts (pinned by SHA-256) and compares bytes: **exit 0 (PASS)** as run; a corrupted copy gave exit 1 with
  "DIFFERS: docs/study-plan-full.md at line 621" (tested, then restored, PASS again). A plan "Old" block found other
  than exactly once makes it refuse (exit 2) before writing. Run:
  `PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B ASSEMBLED/check_assembly.py`
- **HEAD.** The assembly started at `53f746d`; while it ran the main checkout moved to `b5e3c27` and then `0435c3b`
  (commit messages: B14's similarity pass ran, the strata are sealed, the B14 inputs file is written; the grant dossier).
  The three target files are byte-identical at all three commits (hashes below), so nothing here changes; see open
  point 7. The new `reading/b14/` files were not opened (only their names appeared in `git diff --name-status`).

## 1. Sources

| Draft (`REPORTS/…`) | SHA-256 | Used for |
|---|---|---|
| `E-D5-D6.md` | `418c2372a56d90d517e9953326657ebbe2d6938f66f3bf1e678622373b23cc0b` | ADD §39 points 1 (D-5) and 2 (D-6); the citation header and short-name table |
| `E-39.md` | `c659161c85b3020a8707d67bb1e82c0d1b35eac7fe0d7cf5196ade70c3a86e64` | ADD §39 heading, intro, scope, points 3-11, the closing S1 line |
| `E-misc.md` | `da538abaa80eda1c578285467432732974ed1eebafbf4ad25ca600153265a891` | ADD §39 points 12 (A), 13 (B = D-7), 14 (C), 15 (D) |
| `E-40.md` | `26fd943d20ff408f60861e82b221e41b12f572371e673fee17c83fd7d09ab97e` | ADD §40 |
| `E-plan-updates.md` | `13c52b0057684ca22ca19114178cf35387c99b9aaa1d68cb867d3faf966f7d74` | PLAN: 14 Old/New pairs and the revision line |
| `E-S1-blinding.md` | `8128cac6c45448b48b5a3e68b55da63d03fae334dc2091351fc3db0ed7b4ba39` | the new S1 blinding record |

These are the hashes `E-records-verify3.md` names in its "Checked" line (first 16 hex each), so the assembled text is the
verified text. The lead's rulings `lead-rulings-20261101.md` (SHA-256 `3096e37a09ac565a…`) were read first; the SPF
wording for D-5 to D-7 (target 3) is the only text no draft supplies.

Targets at HEAD (`git show HEAD:<path> | shasum -a 256`, equal at `53f746d`, `b5e3c27` and `0435c3b`):

| Target | At HEAD | Assembled (`ASSEMBLED/repo/<path>`) |
|---|---|---|
| `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` (ADD) | `f5a7c6bdb404f429…`, 659 lines | `097a21e27d83737f…`, 1,525 lines |
| `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` (PLAN) | `121c5119d12e5bae…` (= `55d5f8b`'s, as the draft states), 77 lines | `da4bd3a999d942b4…`, 95 lines |
| `docs/study-plan-full.md` (SPF) | `8aedcd4eee80953c…` (= `55d5f8b`'s) | `df1067d9395a0ad4…` |
| `.ai/inputs/stage1-post-w1-20261023/reading/s1-blinding-record-20261101.md` (new) | — | `4f195872838896e6…`, 88 lines |

## 2. Target 1: ADD, §39 and §40 appended

**Diff:** `diff -u <(git -C /Users/spiderishi/Coding/attribution show HEAD:.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md) /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/assembled/repo/.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md`

Lines 1-659 are HEAD's bytes; the diff is one append (866 added lines, 0 removed). Where things are in the copy:

| Lines | Content |
|---|---|
| 661 | `## 39. Before the stage-1 reading: the lead's rulings ([FILL-time]; decided by the lead, GI VIII, under the user's delegation; before any stage-1 outcome is read: blocks A and B are sealed and unread)` |
| 663-665 | E-39's intro paragraph, verbatim |
| 667-670 | E-39's "Scope" bullet (one sentence changed, edit (b) below) |
| 671-675 | E-D5-D6's "Citations" bullet (edit (c)): "citations are `path:line` at commit `55d5f8b`" |
| 677-697 | the merged short-name table (edit (d)): 20 rows |
| 700-851 | point 1 = E-D5-D6 §1 (D-5), nested |
| 853-914 | point 2 = E-D5-D6 §2 (D-6), nested |
| 916-1142 | points 3-11 = E-39, verbatim but for edits (g) and (h) |
| 1144-1209 | point 12 = E-misc A (B14's similarity pass: a scheduling gap, and the route), nested |
| 1211-1271 | point 13 = E-misc B (post-W1 deviation D-7), nested |
| 1273-1321 | point 14 = E-misc C (ADD:428's simulations), nested |
| 1323-1341 | point 15 = E-misc D (the build round's hard-rule notes), nested |
| 1343-1346 | E-39's S1 blinding line, verbatim (see open point 1) |
| 1348 | `## 40. Stage 1b before any pilot unit exists: the lead's rulings ([FILL-time]; decided by the lead, GI VIII, under the user's delegation; no stage-1b unit exists and no stage-1 outcome has been read)` |
| 1350-1353 | E-40's intro paragraph |
| 1355-1369 | E-40's "Sources", "Citations" and "Added" bullets (edit (k)) |
| 1371-1525 | E-40's points 1-13 and its S1 line, verbatim but for edit (k) |

Every edit to the drafts' text (the script makes exactly these; nothing else differs from the drafts):

- (a) **Headings.** The drafts' `(2026-11-01T[FILL] UTC; decided …` becomes `([FILL-time]; decided …` in both headings
  (the task's heading style; the value to fill is the commit time in §33-§38's form, `2026-11-01THH:MM UTC`).
- (b) **E-39's Scope bullet**, one sentence: "Points 1 and 2 are D-5 and D-6, drafted in `E-D5-D6.md`; this file holds
  points 3-11." becomes "Points 1 and 2 are D-5 and D-6; points 3-11 the stated readings; points 12-15 B14's scheduling
  gap, D-7, ADD:428's simulations and the build round's hard-rule notes." (re-wrapped; the other sentences verbatim).
- (c) **The citation header** is E-D5-D6's Citations bullet with its snapshot of an old HEAD removed: "(and two lower
  than at HEAD `a494ff7`; the `55d5f8b` pin stays …" becomes "(the `55d5f8b` pin stays …" (verifier note 5; re-wrapped).
  E-39's and E-misc's own Citations bullets are not copied (they deferred to E-D5-D6's table).
- (d) **The merged short-name table:** E-D5-D6's 12 rows verbatim; then E-39's rows `FOCUS, PLAN, KW, LEDGER`,
  `RIB, HBB, B16H` and `OTSC` verbatim; then five rows made from E-misc's Citations bullet (`PLANS`, `RULES`, `SIM`,
  `HLC`, `NOTES` with its git-ignored note). Not copied: E-39's rows `ADD, REV4, W1R` ("as in E-D5-D6.md"), `B16/, RI/`
  (a duplicate) and `CRIT, R1D, R1B, V1A` and `LR; ACB, …` (both defer to E-D5-D6's rows, which carry the same
  `[FILL-hash]` markers at lines 689-690). FOCUS and PLAN appear in two rows (E-D5-D6's and E-39's), same paths.
- (e) **Points 1 and 2:** E-D5-D6's headings `## 1. Post-W1 deviation D-5: …` and `## 2. Post-W1 deviation D-6: …`
  become `1. **Post-W1 deviation D-5: … (builder open point RI-O2).**` and `2. **Post-W1 deviation D-6: … (a
  settings-only re-pin).**` (D-4's point style, ADD:605); each section's body is nested under its point with three
  leading spaces on every non-blank line, otherwise byte-identical (its Facts, Ruling, Reasons, fallbacks and S1 line).
- (f) E-39's two pointer lines ("the text of `E-D5-D6.md` §1 / §2") are replaced by those texts.
- (g) E-39 point 7: "D-6's fallback text (`E-D5-D6.md` §2)" becomes "D-6's fallback text (point 2)".
- (h) E-39 point 8(g): "are recorded in `E-misc.md` D (LR R3.5, R6.4, R6.6)" becomes "are recorded in point 15 (…)".
- (i) **Points 12-15:** E-misc's `## A.`-`## D.` headings become `12. **B14's similarity pass: a scheduling gap, and the
  route.**`, `13. **Post-W1 deviation D-7: LN-31's draw is built after its deadline (the number is the lead's, in
  ruling order; CRIT:243).**`, `14. **ADD:428: B16's size, coverage and familywise-error simulations.**`, `15. **The
  build round's hard-rule notes, recorded as disclosures (LR R3.5, R6.4, R6.6).**`, bodies nested as in (e); in D.3
  "(part C above)" becomes "(point 14 above)".
- (j) E-39's S1 blinding line is placed after point 15, as §39's closing line (verbatim).
- (k) **§40:** heading as (a); in the Sources bullet "as in `E-D5-D6.md`'s table" becomes "as in §39's table"; in the
  Citations bullet "short names as in `E-D5-D6.md`, plus RULES =" becomes "short names as in §39's table, plus RULES =";
  in point 3 "(no stage-1 outcome in it; `E-misc.md` A ruling 3, LR R3.1)" becomes "(…; §39 point 12 ruling 3, LR R3.1)".
  The three header bullets are placed after §40's intro paragraph, before point 1.
- (l) **Dropped from every draft (draft-only lines):** the `# Draft …` title; the "Status" bullet; the "Where it goes"
  bullet (E-D5-D6, E-misc); the "Fill markers" note (E-D5-D6; its two marker mentions are explanatory, not markers to
  fill); the "Fix round 2" bullets (E-D5-D6, E-misc); the `---` separators.
- Kept although they read as drafting notes (the lead may drop them): §40's Citations bullet sentence "Of the code file
  `scripts/stage1/build_plant.py` I opened lines … no settings, record or output file of the plant was opened" (lines
  1366-1368, a hard-rule disclosure by the drafter) and the line `- "Added" marks a ruling this draft adds to the brief's
  list; the lead keeps or drops it.` (line 1369; the "(added …)" markers in §40's and D-6's text stay).

An independent check (a separate script run, not `check_assembly.py`) found every non-blank line of the six nested
draft sections (380 lines) present in the copy with the three-space prefix, every line of E-39 from point 3 on (222)
and of E-40's bullets and section (162) present verbatim, modulo the edits listed; `## ` headings 39 → 41.

**FILL markers in the copy** (ADD line: marker; the draft's 21 markers are all here or accounted for in (a), (d), (l)):
661 `[FILL-time]` (§39's time); 689 `[FILL-hash]` (LR's committed hash, table row); 690 `[FILL-hash]` (the build-round
reports' committed hashes, table row); 812 `[FILL-hash]` (D-5 item 10: the reader's and builder's new hashes in FOCUS);
848 `[FILL-time]` (D-5's S1 line); 891 `[FILL: the 69-entry near set / the full 150-entry spec]` and `[FILL]` (D-6 item
2: which spec set ran, and its result); 912 `[FILL-time]` (D-6's S1 line); 1269 `[FILL-time]` (D-7's S1 line);
1343 `[FILL-time]` (§39's S1 line); 1348 `[FILL-time]` (§40's time); 1523 `[FILL-time]` (§40's S1 line). Line 384's
`[FILL AT W1-P]` is HEAD's own text (§12), untouched.

## 3. Target 2: PLAN, 14 Old/New pairs and the revision line

**Diff:** `diff -u <(git -C /Users/spiderishi/Coding/attribution show HEAD:.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md) /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/assembled/repo/.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md`

Source: `E-plan-updates.md`'s 14 "Old"/"New" blocks (items 1-13; item 9 has two), applied in the draft's order; each
Old block occurs exactly once in the plan at HEAD (the script refuses otherwise; `E-records-verify3.md` found the same,
"14 of 14"). The "Why" lines are not copied. Places edited, by HEAD line number (→ the copy's lines):

| HEAD lines | Copy | Item(s) |
|---|---|---|
| after line 1 (the title) | 3-4 | the revision line from the draft's "How to apply" bullet, as its own paragraph: `Revised 1 November 2026 by addendum §39 and §40; the 31 October text is in git at \`55d5f8b\`.` |
| 30-34 (rows 1a-1e) | 32-36 | 7 (row 1a), 1 (row 1b), 6 (row 1c), 13 (row 1d), 8 (row 1e) |
| 39-42 (steps 0-2) | 41-49 | 9 first pair (step 0), 2 (step 1), 3 (step 2) |
| 44 (step 3, second line) | 51 | 9 second pair |
| 46-49 (steps 5-6; new 4b and 4c) | 53-67 | 9 second pair (4b, 4c), 4 (step 5), 5 (step 6) |
| 57 (stage 1b's row) | 75 | 10 |
| 70 ("What the lead can do now" 1) | 88 | 11 |
| 72 ("What the lead can do now" 3) | 90 | 12 |

The plan carries no citation header and no FILL marker. Nothing else in the file changed (row 1f, step 2's other rows,
the closing paragraph).

## 4. Target 3: SPF, line 344

**Diff:** `diff -u <(git -C /Users/spiderishi/Coding/attribution show HEAD:docs/study-plan-full.md) /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/assembled/repo/docs/study-plan-full.md`

SPF is unchanged between `55d5f8b` and HEAD, so the draft's SPF:344 is HEAD's line 344 (the "Recorded post-W1
deviations" bullet of §4.5). The one edited line adds, after "D-4 (REML by multi-start)":
"D-5 (S-G's coherent-only U by a linearized prompt table, read beside B16), D-6 (B14's report accepts recipe-S units, a
settings-only re-pin), D-7 (LN-31's draw built after its deadline, before any stage-1 outcome was read)," and changes
the tag `[ADD:446-648]` to `[ADD:446-648, ADD:661-1346]` (§39's line range in the assembled ADD, computed by the
script). The three parentheticals are this assembly's wording (the drafts say only "SPF:344 adds D-5, D-6 and D-7",
LR R6.5; they mirror the points' titles). No FILL marker.

## 5. Target 4: the new S1 blinding record

**View:** `diff -u /dev/null /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/assembled/repo/.ai/inputs/stage1-post-w1-20261023/reading/s1-blinding-record-20261101.md`
(no HEAD version; the path is the draft's proposed home with today's date).

Source: `E-S1-blinding.md`, §1-§5 verbatim but for the edits below:

- line 1: `# Draft: the S1 blinding record (REV4:919; W1R:358)` → `# The S1 blinding record (REV4:919; W1R:358)`.
- lines 3-4 (**new text, the one addition**), in place of the dropped Status bullet: `- **Written** [FILL-time] by the
  lead (GI VIII), before any stage-1 outcome is read; committed by explicit path and named in the second stamp's
  manifest.` (the last clause is the dropped bullet's own). The dropped Status bullet also held the record's pre-set
  fallback ("the same list in the reading record's limits section; trigger: this record is not committed when the
  records step starts (CRIT:352)"), which now lives nowhere; see open point 4.
- lines 5-6, the citation header: "short names as in `E-D5-D6.md`." → "short names as in addendum §39's table
  (`.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md`)."
- lines 7-12, the "Line numbers of FOCUS" bullet: "The brief names FOCUS:134, :137 and :139. Those are the line numbers
  at `0daca9a`." → "At `0daca9a` the final measurements, the verdict and wave 1 were FOCUS:134, :137 and :139."; "At HEAD
  `a494ff7` every FOCUS line from 74 on is two higher; the `55d5f8b` pin stays …" → "The `55d5f8b` pin stays …"
  (verifier note 5); "as in `E-D5-D6.md`'s table" → "as in addendum §39's table". The facts stay.
- row 12 (line 64): "the stated readings of `E-39.md` (point 11's readings are row 15)" → "the stated readings of
  addendum §39 (…)". Row 14 (line 66): "(LR R5; `E-misc.md` B)" → "(LR R5; addendum §39 point 13)".
- Kept: line 47 `"Added" marks a rule this draft adds to the brief's list; the lead keeps or drops it.` (the "(added)"
  markers in the rows stay).

**FILL markers:** line 3 `[FILL-time]` (added with the Written bullet); lines 62-67 `[FILL]` (rows 10-15, "Written
(UTC)"); line 81 `[FILL]` ("The formal text carries [FILL]").

## 6. Open points for the lead

1. **§39's closing S1 line (ADD:1343-1346) predates points 12-15.** It says the paper labels "points 1-9 and 11" and that
   point 10 is the user's decision. Left verbatim (verified text). If the lead extends it, the drafts' own classification
   is: point 12 (A) "is not an inference rule" (E-misc's dropped "Where it goes" bullet); point 13 (D-7) carries its own
   S1 line (ADD:1269-1271, "the paper labels it 'fixed after Gate B wave 1'") and is S1 record row 14; points 14 and 15
   are records, not rules.
2. **Point 15 (E-misc D) is beyond the task's list** (A, B and, if it fits, C). It is included because §39 point 8(g)
   says the build round's hard-rule notes "are recorded in" it and LR R6.4 requires them recorded. If the lead moves D
   elsewhere, delete lines 1323-1341 and re-point 8(g) (line 1078, "recorded in point 15").
3. **Point 14 (E-misc C) is included** as a §39 ruling (it fixes what B16 evidence the records cite, records the missed
   S1-freeze re-run and commits the two NOTES copies, LR R6.5). The draft said "§39 or a FOCUS entry"; moving it means
   deleting lines 1273-1321 and changing "(point 14 above)" at line 1336 back to a pointer.
4. The S1 record's dropped Status bullet held its pre-set fallback (section 5 above); the runbook or FOCUS may want it.
5. **Verifier notes not applied** (`E-records-verify3.md` §8; the drafts were verified as they stand, so the assembly
   copies them): note 1, plan item 13 says "49 entries" for the reading-time readers' spec, which grew to 62 after the
   drafts (D1B:418, :520; copy line 35); note 2, D-5 item 9's "at least one plan-A world" understates the replicate rule
   (four contrast-worlds need the 10,000-replicate pass; ADD:808-811); note 3, the (c)-at-the-pre-run route implies R1b
   is re-run without `--coherent-out` before step 1 (D-5 item 8, ADD:773-789); note 4, D-7's reading 7 omits "and the
   greedy over-refusal answers'" (ADD:1253-1254). Each is a one-phrase change if the lead wants it in the committed text.
6. **`[FILL-hash]` values that can be filled now** (verifier note 6, re-checked here at HEAD `0435c3b` with
   `git show HEAD:<path> | shasum -a 256`): under `lead-reports-20261101/build-round/`, `B-b14-build.md` `f98671ab05c02366…`,
   `B-b14-verify1.md` `6a596693dd71b40c…`, `C-kit34-build.md` `539d3b3a27c95d16…`, `C-kit34-verify1.md` `04e14e8ceb48f485…`,
   `mutants_b14_near.json` `77c3def1f37e814a…` (each equal to the scratch copy the drafts cite). The lead's rulings are
   committed at `.ai/inputs/stage1-post-w1-20261023/reading/lead-rulings-20261101.md` (SHA-256 `3096e37a09ac565a…`,
   equal to the scratch copy), not under `build-round/` as the table row at ADD:689 says. The A, D1, D2 and E reports
   are not committed yet; `D1-readers-build.md`'s current hash differs from the cited `bee4e20e…` (the append at
   D1B:313; verifier note 1).
7. **The plan's text was drafted before B14's pass ran.** Commit `b5e3c27` (after the assembly started) says the
   similarity pass ran, the strata are sealed and the inputs file is written and checked; the copy's row 1b (line 33)
   and step 0 (lines 41-47) still describe them as to-do. The targets are byte-identical across `53f746d`-`0435c3b`,
   so the assembly stands; the lead may mark those parts done when copying. I read only the commit messages and the
   file names of `git diff --name-status 53f746d HEAD` (six files under `reading/b14/`, FOCUS, the dossier); none opened.
8. **SPF's key is now stale and was not changed** ("change nothing else"): line 27 "(the lead's recorded rulings §1-§38)"
   and line 8 "D-1 to D-4 are recorded deviations in ADD". One-word fixes if wanted. The tag `[ADD:661-1346]` is §39's
   range in the assembled ADD; it moves if §39 is edited (points 1-3 above).
9. Hard-rule notes of this work: `git ls-files .ai/inputs/stage1-post-w1-20261023/reading/` was run once with
   `block-a`, `block-b`, `units` and `eval` names filtered out (names only, under `reading/`, timestamp and
   lead-reports files; no content); `git diff --name-status 53f746d HEAD` printed eight file names (open point 7). The
   E-records build report was read through a tool-saved copy of its own text. Nothing else outside `REPORTS/`, this
   folder and the three targets at HEAD was opened.

## 7. Commands run (exit 0 unless noted)

- `date -u` (three times). Read-only git in the main checkout: `rev-parse HEAD`, `log --oneline`, `show HEAD:<path>` and
  `show 55d5f8b:<path>` of the three targets (piped to `shasum`, `sed -n`, `grep -n`, `cat -n`), `diff --name-status
  55d5f8b HEAD -- <targets> research/FOCUS.md`, `diff 55d5f8b HEAD -- docs/study-plan-full.md` (empty), `diff
  --name-status 53f746d HEAD`, `ls-files` (open point 9), `show HEAD:` of the five committed build-round copies and the
  rulings file piped to `shasum`.
- `cat`, `sed -n`, `grep -n`, `wc -l`, `shasum -a 256`, `od -c`, `tail -c` on the drafts, the reports and the copies.
  One `cat -A` failed (macOS has no `-A`; exit 1, nothing read); two `grep -o` patterns exceeded ugrep's complexity limit
  (exit 1; replaced by a Python scan).
- `check_assembly.py --write` (exit 0, PASS: four files written and compared); `check_assembly.py` (exit 0, PASS); the
  failure-path test: one byte appended to the SPF copy → exit 1, "DIFFERS: docs/study-plan-full.md at line 621",
  restored, exit 0. Its first write attempt refused (exit 2) on a check that compared the revision line with the
  draft's wrapped quote; the check now compares whitespace-collapsed text (the sentence itself is the draft's).
- One inline Python sanity check of line presence (section 2, last paragraph) and one listing FILL markers; both with
  the venv Python, `-B`, `PYTHONDONTWRITEBYTECODE=1`. No pytest, no basetemp, no background job, no network.
