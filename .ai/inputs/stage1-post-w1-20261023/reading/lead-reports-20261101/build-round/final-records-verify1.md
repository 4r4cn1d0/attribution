# Independent verification of the final record files (edits E1-E16 on the verified assembly)

- **Written** 2026-11-01, 17:49 UTC (clock read with `date -u`; the Mac's local zone is IST) by an adversarial
  verifier for the lead (GI VIII). Self-identification is not verification; the launcher records routing.
- **Verdict: verified.** Every changed line in the four final files comes from exactly one listed edit; every edit
  is exact and its facts hold against their sources; no other line changed; every `[FILL-time]` marker is kept and
  `[FILL-b14-full]` is present; numbering is unchanged in all four files; `check_final.py` passes unchanged and fails
  on a one-byte change; the patched `check_records.py` passes on inputs rebuilt from the final files. Minor points
  are notes (section 5), none a defect.
- **Checked** (SHA-256, first 16): final ADD `93c5832178be599d` (1,552 lines), PLAN `28bb29093992a57f` (95), SPF
  `64db9f91de4de322` (620), S1R `9e4c7b111ab328ae` (90); assembled bases `097a21e27d83737f`, `da4bd3a999d942b4`,
  `df1067d9395a0ad4`, `4f195872838896e6` (the hashes `assemble-verify1.md` verified); `check_final.py`
  `c0bab4b5d9098b1e`; `check_records_patched.py` `2fbafb80cb13eaee` (original `a13cb1b9f626eab5`). Main checkout HEAD
  `657907e`; the three targets are byte-identical at `53f746d`, `b5e3c27`, `0435c3b`, `c21dccb` and `657907e`
  (`git show <commit>:<path> | shasum`), so the assembly's base is still HEAD's text.
- **Evidence folder:** `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/verify-final-records/`
  (below, `VFR`): the four `diff -u` outputs (`diff-ADD.txt`, `diff-next-steps-after-block-b-20261031.md.txt`,
  `diff-study-plan-full.md.txt`, `diff-s1-blinding-record-20261101.md.txt`), my scan `scan_final.py`
  (`6dea2fdfbfff5d16`) and its output `scan_final_run.txt`, and `check_records_run.txt`. Nothing under
  `builds/final-records/` was edited (its four hashes re-read after every test, unchanged).

## 1. The diffs: every hunk is one edit, nothing else changed

`diff -u ASSEMBLED/repo/<path> FINAL/repo/<path>` and, independently, `difflib` over the lines (`scan_final.py`):

| File | Hunks | Assembled lines → final lines: edit |
|---|---|---|
| ADD | 9 | 689-690 → 689-690: E1, E2 · 809-813 → 809-820: E5, E3 · insert after 819 → 827-830: E6 · 890-891 → 901-905: E4 · 1053-1054 → 1067-1069: E9 · insert after 1210 → 1226-1236: E12 · 1254-1256 → 1280-1283: E8 · 1346 → 1373: E10 · 1366-1369 → 1393-1396: E11a, E11b |
| PLAN | 4 | 33: E13b · 35: E13a · 44-47: E13c · 88: E13d |
| SPF | 2 | 8: E14a · 27: E14b |
| S1R | 4 | insert after 4 → 5-6: E15a · 47 → 49: E11c · 62-67 → 64-69: E15b · 81 → 83: E15c |

E7 and E16 change nothing (section 2). No hunk is unaccounted for. Line counts: ADD +27 (E3 +3, E4 +3, E5 +4, E6 +4,
E8 +1, E9 +1, E12 +11), PLAN 0, SPF 0, S1R +2. No CR byte, tab or trailing whitespace in any file; each ends with one
newline; no changed non-table line is longer than 120 characters (the longest is exactly 120). The only long changed
lines are PLAN:88 (266 characters, 239 before the edit) and SPF:8 (1,324; 1,329 before): both were single-line
paragraphs already.

**Numbering unchanged:** the ordered sequence of numbered markers (`1.`, `2b.`, `## 39.`, table rows `| 10 |`,
`| 1b |`) is identical between assembled and final in every file: ADD 254 markers, PLAN 28, SPF 24, S1R 21. §39's
points 1-15 and §40's points 1-13 keep their numbers; §40 moves from line 1348 to 1375.

**Markers:** ADD `[FILL-time]` 7 (lines 661, 859, 926, 1296, 1370, 1375, 1550; 7 in the assembly), `[FILL-b14-full]`
1 (line 905), `[FILL AT W1-P]` 1 (HEAD's §12 text); no `[FILL-hash]`, `[FILL]` or `[FILL:` remains (3, 1 and 1 in the
assembly). S1R `[FILL-time]` 8 (line 3, rows 64-69, line 83; the assembly had 1 plus 7 `[FILL]`). PLAN and SPF: none.

## 2. Each edit against the task and its source

| Edit | Exact? | Facts checked (M = measured here) |
|---|---|---|
| E1 (ADD:689) | yes: "today in the lead's scratch `builds/`, to be committed under `lead-reports-20261101/build-round/` `[FILL-hash]`" → "committed at `.ai/inputs/stage1-post-w1-20261023/reading/lead-rulings-20261101.md` (SHA-256 `3096e37a…1586`)" | M: `git ls-files` lists that path; `git show HEAD:<path> \| shasum -a 256` = `3096e37a09ac565aab5b7fe0ad2d38e1871d28d181f664a40b6c09b2539c1586` = the scratch copy `builds/lead-rulings-20261101.md` = the task's hash |
| E2 (ADD:690) | yes: `[FILL-hash]` → the task's sentence verbatim | the folder exists at HEAD (`git ls-files`, names only: B's and C's reports, the near-mutant files, five JSON reports); see note 7 |
| E3 (ADD:812-813 → 816-820) | yes: the seven hashes and "FOCUS records them at the records commit" | M: each equals `git show HEAD:scripts/stage1_s1/reading_input/<file> \| shasum` (first 16; the spec at `mutation/mutants_reading_input.json`); `A-coherent-verify2.md` §2 names the same seven |
| E4 (ADD:890-891 → 901-905) | yes, the task's text verbatim (whitespace-collapsed comparison), `[FILL-b14-full]` kept | `lead-notes-for-records.md` item 1; M: the committed `mut-b14-near-report-53f746d.json` holds 69 mutants, 68 killed, 1 invalid (`B14S-s-p-role-primary-repinned`, 61 errors); `mut-b14-one-fixture-fix-report.json`: that id killed, 115 failures, 0 errors; `git show --stat c21dccb` (names only) changes `scripts/stage1_s1/tests/test_b14_inputs.py` and adds three report JSONs (note 6) |
| E5 (ADD:809-811 → 809-815) | yes: the four worlds, their numbers, the 10,000 result and 51 of 51 | all quoted from `A-coherent-verify2.md` §0 item 3 and §3: the 2,000-replicate table flags i (P5 ratio 1.35), ii (P4 0.8915), ii-low (P6 0.9090), iii-prompt (P6 0.9075); the 10,000 table gives ii-low and iii-prompt (first verifier) coverage 0.8921-0.9036, ratios 0.75-1.18, and i and ii (re-verifier) coverage 0.8974-0.9004, ratios 0.82-1.16 (M: recomputed from the 12 cells); "Gate: met. 51 of 51 … (18 at 2,000, 33 at 10,000)". Note 3 on the dropped clause |
| E6 (inserted before the (c+) fallback, lines 828-830) | yes, verbatim; placed after Reasons and before "Pre-set fallback (c+)"; both fallback texts unchanged (no hunk touches them) | the status is the re-verify's verdict (`A-coherent-verify2.md` §0: "verified (no defect)") |
| E7 (ADD:770-771) | no change needed, correct | M: `ws-a/scripts/stage1_s1/reading_input/sg_coherent.py:72` `SYMMETRIC_LABEL = "unscored counted Unsafe in every arm (not Gate B's adverse corner)"`; the assembled and final text quote exactly that, wrapped across the two lines; one occurrence |
| E8 (ADD:1253-1256 → 1279-1283) | yes: "greedy harm answers' categories" → "greedy harm and greedy over-refusal answers' categories"; the next three lines re-wrapped, words unchanged | `D2-ln31-build.md:378-379`: "sampled harm, greedy harm and greedy over-refusal answers" (reading 7); note 11 |
| E9 (ADD:1053-1054 → 1067-1069) | yes: step 5 added to the never-stops list with "REV4:762" and "point 13 ruling 3" | REV4:762 at `55d5f8b` is LN-31's draw ("a script that prints totals only"); final ADD point 13 ruling 3 = "Pre-set fallback. No step 5 at the reading …" and its closing line "The human label check is report-only and exploratory (REV4:762)"; `E-misc.md` B is the same text |
| E10 (ADD:1346 → 1373) | yes, the sentence verbatim, appended to the kept S1 line | — |
| E11a (ADD:1366-1368 → 1393-1395) | yes: "I opened" → "the drafter opened", same facts; the three lines re-wrapped (note 2) | no other first-person sentence in the four files except PLAN:71's HEAD text (note 10) |
| E11b (ADD:1369 → 1396), E11c (S1R:47 → 49) | yes: "this draft adds" → "this record adds"; nothing else on the lines | "this draft" occurs nowhere in the final files (grep) |
| E12 (inserted after point 12's last paragraph, lines 1226-1235) | yes: the pod times, 0.66 h, about $1.21, stopped not deleted, the Mac pre-check (eval 200; 48 rows per add set), the three hashes, 24 units, plan.json's hash and "must not change", the `b14/` folder, 39 of 39 killed | `lead-notes-for-records.md` items 3-5 (the $1.21 is $29.36 → $28.15); FOCUS at HEAD line 74 (the 14:55 entry) states the same times, counts and hashes; FOCUS at `b5e3c27` line 74 holds the three hashes (grep), i.e. sealed there; M: `git show HEAD:…/reading/b14/{similarity.json,strata/strata.json,inputs/overlap_inputs.json} \| shasum -a 256` = the three hashes exactly; `kit-round-34-mutation-report.json` (committed): 39 mutants, 39 killed. `plan.json`'s hash is the lead's (not hashed: under `tmp/stage1-olmo/`) |
| E13a (PLAN:35) | yes: "49 entries" → "62 entries" | `D1-readers-build.md:418` ("49 → 62 entries"), `:520` ("The full 62-entry spec") |
| E13b (PLAN:33), E13c (PLAN:44-47) | yes: row 1b's "What" cell gains "Done at `b5e3c27` (1 Nov): …"; step 0 gains "(written and sealed at `b5e3c27`)"; the old structure kept, short | commit `b5e3c27`'s message: "B14's similarity pass ran on one A100 pod from the balance; the strata are sealed and the B14 inputs file is written and checked" |
| E13d (PLAN:88) | a judgment call: "What the lead can do now" item 1 gains "; done at `b5e3c27`, about $1.21" | within E13's clause (it describes 1b's pod as still to do), beyond the two places the task named; note 1 |
| E14a (SPF:8), E14b (SPF:27) | yes: "D-1 to D-4" → "D-1 to D-7"; "§1-§38" → "§1-§40"; each text occurred once | — |
| E15a (S1R, new lines 5-6) | yes, verbatim, as one bullet after the Written bullet | the dropped Status bullet of `E-S1-blinding.md:6-7` has the same words; CRIT:352 (the design-round `2-critic.md` at HEAD) is row 8, "S1 blinding record … the same list in the reading record's limits. Trigger: not written when step 11 starts" |
| E15b (S1R rows 10-15) | yes: rows 10-13 "2026-11-01T04:55 (ruled); formal text [FILL-time]", rows 14-15 "2026-11-01T14:02 (ruled); formal text [FILL-time]" | my own decision from each row's content agrees (section 3) |
| E15c (S1R:81 → 83) | "The formal text carries [FILL]" → "… [FILL-time]" | the formal text's time is the records commit, the marker the lead fills; note 4 |
| E16 | nothing further to change | the only line that put the rulings file in scratch was ADD:689 (E1); the other "scratch" lines are about reports, trees or folders; S1R:12 and §40's Sources bullet (ADD:1386) point to §39's table (grep of "scratch" with "ruling", and of "lead-rulings") |

My scan also confirms, whitespace-collapsed, that each new text occurs exactly once in its final file and zero times
in the assembly, and that each old text ("at least one plan-A world must also pass", "I opened", "this draft",
"49 entries", "§1-§38", `[FILL-hash]`, `[FILL]`) occurs zero times in the final files.

## 3. The E15b decisions, row by row (from the rows' content; the two sources)

The 04:55 source is FOCUS:74 at `38e160d` (read with `git show`); the 14:02 source is `lead-rulings-20261101.md`.

- Row 10 (D-5): 04:55. The entry rules D-5 itself (the linearized table, per-arm pooled coherent-only U, G2's counts,
  its own Φ run, never stopping the reading, both adverse corners, fallback (c+)). LR R1.2 and R6.1 (14:02) refine
  what "verified" and the pre-run mean; the rule was first written at 04:55.
- Row 11 (D-6): 04:55. The entry rules the settings-only re-pin (G and B+Qi refused; fallback `--no-overlap`); LR
  R2.1 (14:02) records its limit.
- Row 12 (§39 points 3-9): 04:55. The entry rules points 8 and 9 (stop on identity lines only; 6 confirmations and
  2 h; a third stamp). Points 3-7 are stated readings; S1R row 9 says "§39's time governs" for them (the 1c rulings
  agent timed out at 04:55 and the readings were redone in the build round), so their time is the formal text's
  `[FILL-time]`, which the cell carries. S1R's own paragraph (lines 79-84) names rows 10-13 as partly written at 04:55.
- Row 13 (§40's readings): 04:55. The entry rules the go rule read literally, key-only readers, `retrieved/` never
  opened, the unopened construction checks, kit round 35 and K7 after a "go"; the tie tolerance and "no fallback" for
  the interval came at 14:02 (LR R6.5).
- Row 14 (D-7): 14:02. The entry only schedules the draw's build; the deviation, its confirmed readings and HLC 4.3
  item 4 are LR R5.
- Row 15 (the reading-time readers): 14:02. The entry only schedules the readers' build; K2 extended, K5, K6, K7, the
  study costs at measured seconds / c0 and the never-open exception are LR R4.3-R4.4.

These match the editor's cells. Both strings leave the formal text's time as `[FILL-time]`, as the task asks.

## 4. The scripts

- **`check_final.py` unchanged** (`PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B …/final-records/check_final.py`):
  "equal" for all four files with the hashes above, `PASS`, exit 0; `--lines` (read-only) gives the line map of
  section 1. No `__pycache__` or `.pyc` written. Its `EDITS` list holds every pair of section 2 (E7 and E16 as
  checks); the assembled bases are pinned by full SHA-256; every find is counted on the progressively edited text.
- **Failure path**, on a private copy under `VFR/ft/` (the script, `assembled/repo/` and `final-records/repo/` copied
  so its relative paths resolve; deleted after the tests): unchanged copy → PASS, exit 0. One byte appended to the
  SPF copy → "DIFFERS: docs/study-plan-full.md at line 621", exit 1. One byte flipped at the start of ADD line 1000 →
  "DIFFERS … at line 1000" with both lines printed, exit 1. One `[FILL-time]` removed from the S1R copy → "DIFFERS …
  at line 3", exit 1. One byte appended to the assembled PLAN base → "REFUSED … assembled copy SHA-256 … is not the
  verified assembly's", exit 2. Restored → PASS, exit 0. The real `final-records/repo/` hashes were unchanged after
  every test.
- **`check_records.py`** (`REPORTS/E-fix-checks/`) cannot be pointed at the final files as it stands: it reads six
  draft files by fixed name, the rulings file from the folder's parent, and it opens `scripts/stage1/build_plant.py`
  with `git show` (a path holding "plant", which my rules forbid). The editor's `check_records_patched.py` differs from
  the original by exactly the four lines marked `# PATCH` (`diff -u`): such code paths are skipped too, a phrase check
  on a skipped path counts as "not checked" and is listed. I rebuilt its inputs from the final files myself under
  `VFR/cr/` (`E-39.md` = final ADD lines 661-1552, `E-S1-blinding.md` = the final S1R, `E-misc.md` = the final PLAN,
  `E-40.md` and `E-D5-D6.md` empty, the build-round reports and `E-plan-updates.md` as symlinks into `REPORTS/`, the
  rulings symlink in the parent); the three rebuilt files are byte-equal to the editor's `check-input/` copies (`cmp`).
  Run with `-I -B` against the main checkout (read-only `git show`), exit 0: `[1] old blocks 14, new blocks 14, each
  old block once in PLAN: True`; `[2] citations parsed 909; out of range: 0; not opened: [one skipped code path]`;
  `[3] phrase checks: 244 of 244 hold; not checked (never-open paths): 7` (the seven §40 phrases on that path, which
  the drafters checked in their rounds); `[4] committed copies at 0e0ab1f: 8 hashes checked; mismatches: 0`;
  `[5] stale text: 0 hits`; `PASS` (`VFR/check_records_run.txt`, equal to the editor's log). The SPF is not covered
  (its tags are at `5f11726` by design), as in the editor's run.
- **My scan** (`VFR/scan_final.py`): numbering sequences, byte hygiene, hunks, and the task's texts (section 1-2).
  Its only "FAIL" lines are my own over-strict length rule on PLAN:88 and SPF:8, both long before the edits.

## 5. Notes for the lead (none a defect)

1. **E13d (PLAN:88) goes beyond the two places the task named** (row 1b, step 0). "What the lead can do now" item 1
   describes 1b's pod as still to do, so the edit fits E13's clause; it is one find/replace pair in `check_final.py`
   (`E13d`) that the lead can drop; its fact (about $1.21) is the lead's note.
2. **Re-wraps.** E11a keeps the sentence's order ("Of the code file … the drafter opened …", lower case mid-sentence)
   rather than "The drafter opened …" at the sentence start; "Change nothing else of those lines" favours this. The
   assembled line would grow from 117 to 127 characters, so the three lines are re-wrapped; the words are unchanged.
   E8 re-wraps the three lines after the change and E3 its list; words unchanged, no line above 120 characters.
3. **E5 drops** "the 10,000-replicate run is the lead's (ACB:267-268) and the re-verify reads it" and names the two
   verifiers as the runners of the four 10,000-replicate worlds; true by `A-coherent-verify2.md` §3 (the first
   verifier ran ii-low and iii-prompt, the re-verifier i and ii). LR R1.1 stays cited.
4. **E15c** turns line 81's `[FILL]` into `[FILL-time]` (the records commit time, which the lead fills) rather than
   one of the two row strings; the sentence "The formal text carries [FILL-time]" reads right once filled.
5. **Row 12's cell** says "04:55 (ruled)" although points 3-7's readings were ruled by the formal text only (row 9:
   "§39's time governs"); points 8-9 were ruled at 04:55. The two allowed strings leave no finer form.
6. **E4's "Commit c21dccb fixed the test file only"** is the task's text. The commit's code change is the test file
   only; it also adds three mutation-report JSONs under `build-round/` (`git show --stat`, names only).
7. **E2 presumes the records commit** (the editor's open point 2 too): at HEAD `657907e` the `build-round/` folder
   holds B's and C's reports and the JSON reports but no `SHA256SUMS` and no A, D1, D2 or E report; the row still
   opens "today in the lead's scratch `builds/reports/`, to be committed under …" (E2 fills only the marker).
8. **SPF:344's tag `[ADD:446-648, ADD:661-1346]` is stale** and was rightly left (not in the list): §39 now ends at
   line 1373 (the last non-blank line before `## 40.` at 1375). One token, `1346` → `1373`, if the lead wants it.
9. **The editor's README** says "ADD: 26 lines added" in section 1 but 27 in open point 3; 27 is right (section 1
   above). The README is not one of the records.
10. **PLAN:71** "unless marked as my estimate" is HEAD's own first person (the lead's 31 Oct text), outside E11's two
    places; left as is, correctly.
11. **E8's "also reads the greedy harm and greedy over-refusal answers' categories"** states the rule under the
    protective reading; what the reading added was greedy harm (D2B:154, LR R5.1). Exact as the D2 build report's
    wording, as the task asked; the editor's open point 4 says the same.
12. **E9's "report only, REV4:762"**: REV4:762 is LN-31's draw ("prints totals only"); "report-only" is point 13's own
    wording about the human label check (its closing line). The citation is the task's.
13. Scaffolding under `final-records/` (`check-input/`, the rulings symlink) is for the `check_records` run only, as
    the editor's README says; not part of the records.

## 6. Hard-rule notes and commands run (exit 0 unless noted)

- Nothing under `tmp/stage1-olmo/`, `tmp/judge-pod*`, `tmp/hlc-inputs/`, `block-a/`, `block-b/`, any `units/` or
  `eval/` folder, any COMPLETE.json, answer, label, judge or bank file, or any path holding "plant" or "decoy" was
  opened, printed, grepped, hashed or listed. The `check_records` run printed the name of the one code path it
  skipped (the path §40's Citations bullet itself names); the file was not opened. `git show HEAD:<path> | shasum`
  hashed `reading/b14/similarity.json`, `strata/strata.json` and `inputs/overlap_inputs.json` (no content printed;
  FOCUS:74 says `similarity.json` holds prompt ids and similarity values only, and the strata and inputs hold no
  outcome). Three committed mutation-report JSONs under `build-round/` were parsed for counts only.
- Git, read-only, in the main checkout: `rev-parse HEAD`, `log --oneline -12`, `show <commit>:<path>` piped to
  `shasum`, `sed -n`, `grep -n`, `fold` or `python3 -I` (the three targets at six commits; the rulings file; the seven
  `reading_input` files; the three `b14/` files; FOCUS at `38e160d`, `b5e3c27` and HEAD line 74; REV4 at `55d5f8b`
  lines 760-763; the design-round `2-critic.md` lines 350-354; three mutation reports), `show --stat c21dccb` (names),
  `ls-files` of the rulings path, `build-round/` and `reading/b14/` (names). No git command changed state; the main
  checkout and the worktree were not edited.
- Shell: `date -u` (twice), `ls`, `find`, `wc -l`, `cat -n`, `sed -n`, `grep -n`, `awk`, `cut`, `fold`, `cmp`,
  `shasum -a 256`, `diff -u` (exit 1 for differing files, as expected; one `diff | tee` reported 0 through the
  pipe) on the assembly, the final files, the reports, the lead's notes and rulings, `ws-a/…/sg_coherent.py` lines
  68-76. One `grep` failed on an unquoted zsh glob (exit 1, nothing read; rerun quoted). One run of `scan_final.py`
  failed on a Python 3.11 f-string syntax error (fixed, rerun; its exit 1 afterwards is the length rule of section 4).
- Python (`/usr/bin/python3` 3.11, always `-I -B`, `PYTHONDONTWRITEBYTECODE=1`): `scan_final.py`, `check_final.py`
  (unchanged, read-only, and its `--lines`), the failure-path copy (five runs), `check_records_patched.py` on my
  rebuilt inputs. No `__pycache__` or `.pyc` anywhere (checked with `find`). No pytest, no basetemp, no network,
  no install, no pod, no background job. Written only under `VFR/` and this report; `VFR/ft/` and `VFR/cr/` (test
  copies and symlinks) were deleted after their runs.
