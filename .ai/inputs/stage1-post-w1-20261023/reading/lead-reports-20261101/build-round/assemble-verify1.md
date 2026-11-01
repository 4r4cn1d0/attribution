# Verification of the assembly (round 1)

- **Written** 2026-11-01 at 15:20 UTC (clock checked with `date -u`; the machine's local zone is IST, UTC+5:30) by an
  independent verifier for the lead (GI VIII). Self-identification is not verification; the launcher records routing.
- **Checked.** The assembly folder `builds/assembled/` (below `ASSEMBLED`): `README.md` (SHA-256 `236de071efb3ff6c…`),
  `check_assembly.py` (`a7c1654cea8d337c…`, as the README states) and the four copies under `ASSEMBLED/repo/`; the six
  drafts in `builds/reports/` at the hashes `E-records-verify3.md` (`fab42c10dfaa33b9…`, verdict "verified") names in
  its "Checked" line (M: `E-D5-D6.md` `418c2372…`, `E-39.md` `c659161c…`, `E-misc.md` `da538aba…`, `E-40.md` `26fd943d…`,
  `E-S1-blinding.md` `8128cac6…`, `E-plan-updates.md` `13c52b00…`, all equal); the lead's rulings
  `lead-rulings-20261101.md` (`3096e37a09ac565a…`, read first; equal to the committed copy at
  `.ai/inputs/stage1-post-w1-20261023/reading/lead-rulings-20261101.md`); the three targets at the main checkout's HEAD.
- **HEAD** of the main checkout while I worked: `0435c3b`. The three targets are byte-identical at `53f746d`, `b5e3c27`
  and `0435c3b` (M: ADD `f5a7c6bdb404f429…`, PLAN `121c5119d12e5bae…`, SPF `8aedcd4eee80953c…` at each; the first two
  also equal `55d5f8b`'s), so the assembly's start point is HEAD's content.
- **Scope kept (hard rules).** I edited nothing under `ASSEMBLED/`, the main checkout, any worktree or any draft; I wrote
  only under `builds/verify-assemble/` and this report. Git read-only only (`rev-parse`, `log --oneline`, `show
  <commit>:<path>` of the three targets, of the committed report copies under `reading/lead-reports-20261101/` and of the
  rulings file, each piped to `shasum`/a file; `ls-files` of `reading/lead-reports-20261101/` and the rulings file, names
  only). No reading, builder, overlap, claim, judge, seal, kit, draw or launch command; no network, install, pod or API
  call; no pytest, no background job; every command finished in seconds. Nothing on the never-open list was opened,
  listed, grepped or hashed; no `block-a/`, `block-b/`, `units/`, `eval/`, `tmp/stage1-olmo/` or plant/decoy path was
  touched. No stage-1 outcome was read; the assembled records hold none (they cite Gate B values already in FOCUS).

Tags: (M) measured or checked here; (R) read in a source; (I) my inference.

## Verdict: verified

No defect that matters for the reading's correctness, the frozen rules, the lead's rulings or blinding. Every added line
of the four copies is a verified draft's line or one of the README's stated edits (section 2); nothing else in the
target files changed (section 3); each of the plan's 14 Old blocks occurs exactly once at HEAD (section 4); the
headings and numbering follow §33-§38 and the drafts (section 5, with one rendering note); `check_assembly.py` passes
as run and fails on a one-byte change in any of the four copies and refuses a one-byte change in any draft (section 6).
The notes in section 8 are minor; none changes a rule, a number or a reading.

## 1. The acceptance criteria

| Criterion | Result | Where |
|---|---|---|
| Every added line comes from a verified draft (only the stated header and citation-header changes allowed) | passed | §2 |
| Nothing else in the target files changed | passed | §3 |
| Every Old block of the plan matched exactly once | passed (14 of 14, at HEAD, independently) | §4 |
| Numbering and headings fit the files' existing style | passed; one rendering note (note 1) | §5 |
| `check_assembly.py` passes and would fail on a one-character change | passed (exit 0; one-byte flips in each of the four copies → exit 1; a draft byte → exit 2) | §6 |

## 2. Provenance of every added line (M)

My own script `builds/verify-assemble/provenance.py` (not `check_assembly.py`) compares each copy with HEAD and with the
drafts line by line; a nested line is compared after removing its three-space prefix.

- **ADD.** HEAD's 659 lines are a byte-identical prefix of the copy (the diff is one hunk, `@@ -657,3 +657,869 @@`, 0
  lines removed, 866 added, 61 of them blank). Of the 805 added non-blank lines, 780 are verbatim draft lines. The 25
  that are not are exactly the README's edits: the §39 heading (661, edit (a)); the Scope sentence (668-670, (b)); the
  citation header without the HEAD snapshot (673-675, (c)); the five rows made from E-misc's Citations bullet (694-698,
  (d)); the point titles 1, 2, 12-15 (700, 853, 1144, 1211, 1273, 1323, (e), (i)); "D-6's fallback text (point 2)"
  (1008, (g)); "recorded in point 15" (1078, (h)); "(point 14 above)" (1336, (i)); the §40 heading, Sources and
  Citations bullets and point 3's "§39 point 12 ruling 3" (1348, 1359, 1362, 1417, (k)). Each is a pointer conversion,
  a re-wrap or a title; none adds a rule, a number or a hash. The reverse check (what of each draft is absent from every
  copy) lists only the draft titles, Status, Where-it-goes, Fill-markers and Fix-round-2 bullets, `---` separators, the
  `## ` section headings turned into point titles, the two pointer lines of E-39 (points 1 and 2), the superseded
  Scope/Citations sentences, E-39's deferring table rows (`ADD, REV4, W1R`; `B16/, RI/` duplicate; `CRIT, R1D, R1B,
  V1A`; `LR; ACB, …`, whose hashes equal E-D5-D6's rows, M), and the four lines the edits (c), (g), (h), (i), (k)
  replaced. Nothing of substance was dropped.
- **S1 record.** Of 88 lines, 78 are verbatim `E-S1-blinding.md` lines; the 10 others are the title, the new
  "Written" bullet (the one addition the README states), the Citations and FOCUS-lines bullets without the draft-file
  and HEAD-snapshot phrases, and rows 12 and 14 with `E-39.md`/`E-misc.md` turned into addendum pointers. The facts and
  every table value are unchanged.
- **PLAN.** Every line of the copy is a HEAD line, a line of a "New" block, or the revision line the draft's "How to
  apply" bullet states; no "Why" line was copied; no "Old"-only line remains (0).
- **SPF.** 621 lines at HEAD and in the copy; exactly one line differs (344). Its three parentheticals are the builder's
  wording (no draft supplies any, as the README says); they mirror the point titles and LR R5.4 and state no rule.
- **FILL markers.** All kept and accounted for (M): ADD 661, 689, 690, 812, 848, 890-891 (the `[FILL: the 69-entry near
  set / the full 150-entry spec]` marker is wrapped across two lines, as in the draft), 912, 1269, 1343, 1348, 1523;
  S1 3 (new), 62-67, 81. HEAD's own `[FILL AT W1-P]` at 384 is untouched. The two heading markers `2026-11-01T[FILL]
  UTC` became `[FILL-time]` (the task's style); the dropped "Fill markers" bullet's two mentions were a legend.
- **No draft-file residue.** `grep` of the four copies for `E-D5-D6.md|E-39.md|E-misc.md|E-40.md|E-S1-blinding.md|
  E-plan-updates.md|Draft|Where it goes|Fill markers|Fix round 2|a494ff7` finds nothing except the legend lines noted in
  note 4 ("this draft"). Every short name used as `NAME:line` in §39 is defined in §39's table; every one in §40 is in
  the table or §40's Citations bullet (M; `JR` is defined there across a line break).

## 3. Nothing else changed (M)

`diff -u <(git show HEAD:<path>) ASSEMBLED/repo/<path>` for the three targets: ADD, one appended hunk only; PLAN, the 14
replacements and the revision paragraph only (rows 1f, step 2's other rows and the closing text unchanged; 17 lines
removed, 34 added, all inside the Old/New blocks); SPF, line 344 only. No CR, tab or trailing whitespace in any copy
(HEAD's ADD has none either); no triple newline; each file ends with a single newline.

## 4. The plan's Old blocks (M)

In the plan at HEAD each of the 14 Old blocks occurs exactly once (counted by substring on the HEAD text, independently
of the script's sequential application); each New block occurs exactly once in the copy and each Old block zero times.
The draft's `Old:`/`New:` labels alternate strictly (14 pairs; item 9 has two), so the script's in-order pairing is the
draft's pairing.

## 5. Headings and numbering

- `## 39. … ([FILL-time]; decided by the lead, GI VIII, under the user's delegation; before any stage-1 outcome is
  read: blocks A and B are sealed and unread)` and `## 40. … ([FILL-time]; decided by the lead, GI VIII, under the
  user's delegation; no stage-1b unit exists and no stage-1 outcome has been read)` follow §33-§38's pattern (M, HEAD
  ADD:600-648); `## ` headings 39 → 41; §39's points run 1-15 and §40's 1-13 without a gap (M).
- Points 1 and 2 carry D-4's title style (ADD:605) with the record nested under them, as E-D5-D6's "Where it goes" bullet
  intended; points 12-15 likewise. The cross-references all resolve in the assembled numbering (M): PLAN's "§39 point
  1, item 8", "point 2", "point 8", "8(h)", "9", "10", "11"; S1's rows 10-15 and "§39 point 13"; §40 point 3's "§39
  point 12 ruling 3" (E-misc A's ruling 3, the `retrieved/sim-1/` exception) and "§39 point 11"; point 15's "§39 point
  8(g)", "§40 point 10" and "(point 14 above)"; point 8(g)'s "point 15"; point 7's "(point 2)".
- One rendering note (note 1): the bodies of the two-digit points 12-15 are indented 3 spaces, where E-39's own
  two-digit points 10 and 11 use 4.

## 6. `check_assembly.py` (M)

- As run: `PYTHONDONTWRITEBYTECODE=1 <venv>/python -B ASSEMBLED/check_assembly.py` → prints HEAD `0435c3b`, the three
  HEAD hashes (equal to the script's `HEAD_EXPECTED`), "equal" for all four files with the README's hashes (ADD
  `097a21e27d83737f…`, PLAN `da4bd3a999d942b4…`, SPF `df1067d9395a0ad4…`, S1 `4f195872838896e6…`), `PASS`, exit 0.
- Failure paths, on my own copy (`builds/verify-assemble/ft/`: the script with `BUILDS` redirected, a copy of
  `ASSEMBLED/repo/` and of the six drafts; `ASSEMBLED/` itself untouched): baseline PASS exit 0; one byte flipped in
  the middle of each copy → exit 1 with `DIFFERS: <path> at line 625 / 36 / 335 / 53` and `FAIL`; one byte appended to
  the SPF copy → exit 1, `DIFFERS: docs/study-plan-full.md at line 621` (the README's test, reproduced); one byte appended
  to the `E-39.md` copy → exit 2, `REFUSED: E-39.md: SHA-256 … is not the verified draft's …`; restored → PASS exit 0.
- Reading the code: the comparison is on bytes (`have == data`); the derivation reads only `git show HEAD:<target>` and
  the six hash-pinned drafts; a draft section is cut at the next `---` or `## `; `derive_spf` computes the `ADD:661-1346`
  range from the assembled §39 (the last non-blank line before `## 40.`); the plan's Old blocks are counted on the
  progressively edited text, which also catches a New block that re-creates or removes a later Old block. Once the lead
  commits the ADD with §39, the script refuses by design ("ADD at HEAD already holds §39", exit 2), as the README says.

## 7. Against the lead's rulings (R)

The assembly changes no ruling text: R1.2(a)-(c) (D-5 item 9), R1.1/R1.3 (the fallbacks), R2.1-R2.3 (D-6 items 1b-3),
R3.1-R3.5 (point 12 and point 15.1), R4 (point 11 and 8(h)), R5 (point 13), R6.1 (D-5 items 4 and 8; 8(d)(iii); PLAN
step 2), R6.3 (PLAN step 4c and rows 1d, 1e; items 8, 9, 11, 13), R6.5 (the `55d5f8b` pin in every citation header;
SPF:344 adds all three deviations; the committed copies cited by path and hash, each equal to the committed file, M:
`d4700f08…`, `f5cb0298…`, `e8646619…`, `c03f6746…`, `9ae23f5e…`, `8d1f5366…`, `570e98ff…`, `bfcd26b2…`) and R6.6
(point 15.3) read in the copies exactly as `E-records-verify3.md` verified them.

## 8. Notes (minor; not defects)

1. **Two-digit points 12-15 are nested at 3 spaces.** `check_assembly.py` nests every draft section with three spaces
   (`nest(indent="   ")`). For `1.` and `2.` that is the CommonMark content indent (marker width 2 + 1); for `12.`-`15.`
   the content indent is 4, so a renderer (cmark-gfm, GitHub) closes item 12 at the blank line and shows "**Facts.**",
   the bullets and the ruling's `1.`-`4.` as top-level blocks before `13.`. E-39's own two-digit points 10 and 11 use
   4 spaces (draft lines 213-225; copy 1097-1142). Reproduction: `sed -n 1144,1150p` of the ADD copy (3-space bodies)
   against `sed -n 1096,1100p` (4-space bodies). Not measured with a renderer (none is installed in the venv; from the
   spec, I). Raw text and every line citation are unaffected. Fix, if wanted: 4 spaces for points 12-15 (the line
   count, and so `ADD:661-1346`, does not change).
2. **The LR table row (ADD:689) is now stale.** It says the rulings are "today in the lead's scratch `builds/`, to be
   committed under `lead-reports-20261101/build-round/` `[FILL-hash]`". They are committed at
   `.ai/inputs/stage1-post-w1-20261023/reading/lead-rulings-20261101.md` (M: `git show HEAD:` of it hashes
   `3096e37a09ac565a…`, equal to the scratch copy and to the hash the row already states). When the `[FILL-hash]` is
   filled, the path should be corrected too (the README's open point 6 says the same). Row 690's B and C reports are
   committed under `build-round/` with equal hashes (M: `f98671ab…`, `6a596693…`, `539d3b3a…`, `04e14e8c…`,
   `77c3def1…`); `D1-readers-build.md`'s scratch copy now hashes `f0d0a60e…` (fix round 2 appended at 14:38 UTC; the
   cited `bee4e20e…` is the pre-append file, and the row says a fix round moves no earlier line).
3. **The S1 record's pre-set fallback went with the Status bullet.** The dropped bullet held "Pre-set fallback: the same
   list in the reading record's limits section; trigger: this record is not committed when the records step starts
   (CRIT:352)". The record is being committed, so the trigger is moot once it lands; if the lead wants the fallback
   stated, one clause in the new "Written" bullet does it (README open point 4).
4. **Draft wording left in committed records.** ADD:1369 and S1:47 keep the legend `"Added" marks a ruling/rule this
   draft adds to the brief's list; the lead keeps or drops it`; ADD:1366-1368 keeps the drafter's first-person
   disclosure ("I opened lines 282-287 …"). The legend is needed while "(added)" markers stay; "this draft" → "this
   record" and "I" → "the drafter" would read as the lead's. The README flags both.
5. **§39's self-description predates points 12-15.** The intro (663-665) says "Each point below is listed in the S1
   blinding record", and the closing S1 line (1343-1346) says "The paper labels points 1-9 and 11 … Point 10 is the
   user's decision". Point 13 (D-7) carries its own S1 line and is S1 row 14; points 12, 14 and 15 are a route, an
   evidence citation and disclosures, not inference rules, and the S1 record does not list them (consistent with
   REV4:919). A one-sentence extension of the closing line would close the gap (README open point 1).
6. **The plan's B14 text is older than commit `b5e3c27`.** Row 1b, step 0's and step 1's wording and "What the lead can
   do now" item 1 still describe the similarity pass, the strata and the inputs file as to-do; `b5e3c27`'s message says
   the pass ran, the strata are sealed and the inputs file is written and checked (I read the commit message only).
   The drafts were verified before that commit, and the targets are unchanged by it, so the assembly is right as an
   application of the drafts; the lead marks those parts done when copying (README open point 7).
7. **Row 1d's "49 entries"** for the reading-time readers' spec is the stale count `E-records-verify3.md` note 1
   names (62 after D1's fix round 2); verified text, copied as is.
8. **README line ranges.** The short-name table spans 677-698 (header, separator, 20 rows), not "677-697". Everything
   else in the README's line tables matches the copy (M).
9. **SPF.** The tag `[ADD:446-648, ADD:661-1346]` follows SPF's convention for ADD (line numbers with no commit pin;
   ADD:446 = `## 18.`, ADD:648 = `## 38.` at HEAD, M) and holds only if §39 is committed as assembled (the README says
   so); SPF's key line 27 "(the lead's recorded rulings §1-§38)" and line 8 "D-1 to D-4" are now stale and were left
   untouched under "change nothing else" (README open point 8).
10. **§40's heading clause** reads "no stage-1b unit exists and no stage-1 outcome has been read" where the task text
    says "before any stage-1 outcome is read"; it is the verified draft's wording and says the same.

## 9. Commands run (all exit 0 unless noted; none longer than a few seconds)

`cat`, `sed -n`, `grep`, `wc -l`, `shasum -a 256`, `od -c`, `tail -c`, `ls -l`, `nl`, `date`, `date -u` on the drafts,
the reports, the README, the script and the copies; `git -C /Users/spiderishi/Coding/attribution rev-parse HEAD`, `log
--oneline -5`, `show {HEAD,55d5f8b,53f746d,b5e3c27,0435c3b}:<target>` (to files under `builds/verify-assemble/` or
`shasum`), `show HEAD:` of the committed report copies and the rulings file piped to `shasum`, `ls-files
.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/` and the rulings path (names only); `diff -u` of the
three targets (exit 1, as expected for differing files); `check_assembly.py` as run (exit 0); the redirected copy
`builds/verify-assemble/ft/check_copy.py` seven times (exit 0, 1, 1, 1, 1, 1, 2, 0 as in §6); `provenance.py` and two
inline Python checks with the venv Python, `-B -I`, `PYTHONDONTWRITEBYTECODE=1`. One `echo` line failed on zsh's `=cmd`
expansion (no file read) and one `sed` rewrite of the script copy failed on a two-line constant (replaced by a Python
rewrite); nothing else failed. No pytest, so no basetemp folder; scratch `ft/` stays under `builds/verify-assemble/`.
