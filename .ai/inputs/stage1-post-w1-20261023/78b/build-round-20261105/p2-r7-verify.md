# Round 7a re-verify of Part 2 (p2-r7-verify)

Started 2026-11-07 14:26 UTC; this version 14:43 UTC (`date -u` before each write). Status: **DONE**.

Target (read-only): `scratchpad/b78/ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`,
SHA-256 `1889e8e51b0ad9d0eef5be29367cc4dae930d184b79c0d16ea7775056473269e`, 875 lines, 191,179 bytes (M #2; equal to
the fixer's value and to `p2-r7-scratch/part2-after-r7.md`; the same at the end, M #24). The before-text
`p2-r7-scratch/part2-before-r7.md` is `dbce35ba…` (M #2), P2R6V's value.

Tags: M = measured by me (command number in section 7); R = read (path:line); E = estimate; I = inference.
No git state changed (HEAD `63b57c0`, `git status --short` 19 lines at start and end, M #1, #24). No pod, spend,
network, install, download, agent or message. In the main checkout I only read (`git show`, `ls-tree`, `cat-file`,
`diff`, `log`, `rev-parse`, `grep`). No forbidden folder, `selector.jsonl`, `hidden/`, judge, answer, generation,
sample or prompt-text file was opened. My hash pool skips those names and `backups/`. From settings files I printed
list sizes only. The engine identity was re-computed from git blobs by `code_identity()`'s own rule, with no import.
The side paper is not mentioned.

## 1. Verdict

**VERIFIED_WITH_MINOR (0 blocker, 0 major, 3 minor, 4 nits).**

- R1-R10 are closed (section 3). R2 is closed by the merge: every kit hash and cite now matches `63b57c0`.
- Both sets of open-item rulings are written as ruled (section 4).
- Every hash I re-computed at `63b57c0` is right. Every line cite I re-read says what the text says (section 5).
  Two cites are off by a line or two (nits V4, V5).
- I found no new decision and no dropped ruling (section 6).
- The three minor defects are gaps around DESO2 item 36 and item 33 (b). None changes a rule. Two of them (V1, V3)
  sit in §1 or its open items. Each is fixed by one or two sentences.

So the scorer section and the draft can be committed now. I advise applying V1, V3 and the nits first (about ten
minutes of text work). After the commit, any change to §1 is a dated amendment (status line).

## 2. Defects

| id | sev | where | defect | fix |
|---|---|---|---|---|
| V1 | minor | §1.3 "Engine Y's pack"; §1.16 `ENGINE_Y` row; §1.4 item 3 | On a stopped family, the MAIN_F retrain runs on Y (DESO2 item 36 (2)). So Y's pack must exist first. But §1.16 gives `ENGINE_Y`'s event as "when the Y retrain is packed, after the anchor job and S_78", and §1.3 opens the same way. With no S_78_F that event cannot occur. This matters under [C] with OLMo-2-7B stopped, or under [B] with both families stopped (`ENGINE_Y` is one global pin, R: RK:148). §1.3 then copies DESO2 (3), "Y's pack ... follow that certificate", which reads as if the pack came after the Y retrain. PP18's main clause holds in this case ("built when ruling 10's retrain is prepared"; R: PP:103-104); only its parenthetical "after the anchor job and S_78" fails. RK's own event has no S_78 clause (R: RK `SC_PIN_EVENTS["ENGINE_Y"]`, "when the Y retrain is packed"). Also not stated: if Y's MAIN_F retrain differs, ruling 10's second job (the X retrain) also runs under MAIN_F (I: S_78_F cannot exist). | Add to the `ENGINE_Y` row and to §1.3: "on a family whose anchor job stopped, when the MAIN_F retrain is prepared (PP18's main clause; DESO2 item 36 (2))". Add: "If Y differs, the X retrain also runs under MAIN_F (I)". Or list both as one §14 item for the lead to confirm. Neither is a new decision. |
| V2 | minor | §10.2, §10.3; §14 (missing item) | On a stopped family block A loses A1, L1 and S3: 9 of its 18 method runs (§2.2, I). So the cells behind σ̂_A, and the "about 12-15 df per family" that §10.3's simulation assumes, shrink on that family. The anchor jobs run before block A, so a stop is known before the simulation runs (§1.4; §10.3 "runs before block A's first pod"). The text does not say what σ̂_A pools on that family or which design the simulation uses. DESO2 item 36 does not say either. The text's own rule is to list such a gap in §14 (§0 header: "Where the rulings leave an item open, §14 names it"). | Add a §14 item (open; not in §1): on a stopped family, σ̂_A pools only the cells that exist (I; §10.2's "a cell with no partner seed adds no df" already covers it), and the lead says whether §10.3's simulation runs on that reduced design. |
| V3 | minor | §14 item 33 (b); §1.8 "A reduced list" | Item 33 (b) names only the s-pool record's `s3_safe` hash. But `s3_score` also reads the S3 subset's ids and S1's ids from that record. It refuses if any of those ids has no `s3_safe` features (R: `scripts/stage1/score_s3_datarx.py:101-105`). An `s3_subset` prompt that fails the encode count is also in `s3_safe` (§1.8: `s3_safe` = the S3 subset plus S1's rows outside it). So, if such a prompt is dropped, `s3_score` refuses even with a new `s3_safe` hash, unless the record's id lists change too. The lead needs this fact to rule 33 (b). | Add to item 33 (b) and to §1.8's sentence: "and the record's `lists.s3_subset.ids` and `lists.s1.ids`, which `s3_score` checks for missing `s3_safe` features (R: `score_s3_datarx.py:101-105`)". |
| V4 | nit | Short names (DESO2 line); §1.17 "Re-taken at `63b57c0`"; §14 preamble | "R: DES:129-166" and "`0e88dfc` only appends lines 129-166". DES has 165 lines at `63b57c0` (M #6: `wc -l` 165; 127 at `197ea37`). The hunk `@@ -125,3 +125,41 @@` adds lines 128-165: 128 is blank, the heading is 129, the last ruling ends at 165. | "DES:129-165"; "appends lines 128-165". |
| V5 | nit | Short names (P2FV); §14 item 2 (b) | "P2FULL's P2.2 table (R: p2-full.md:46-60)". P2FV's D11 (i) is at p2-full.md:44 ("DESO item 9 / P2FV D11 (i)"), outside :46-60 (M #10). The cite comes from P2R6V's own text. | "p2-full.md:44-60". |
| V6 | nit | §1.8 "A reduced list"; §1.16 "MAKER changes only for a reduced list"; §14 item 33 (a) | "So a reduced list changes MAKER's code and hash too". The basis given is S4's. Both derived untuned settings and the 1B base file have `lists.s3.size` null and `lists.s4.size` 512 (M #9). So a reduced `s3_safe` list meets no size refusal at `make_untuned_answers.py:77-78`, and MAKER may not need a code change for it. DESO2 item 33 says "built only if needed". | "So a reduced S4 list changes MAKER's code and hash too; a reduced S3 list may not (`lists.s3.size` is null)". |
| V7 | nit | §15 preamble ("items 14-15 come from DESO2"); §15 item 14 | Item 15 is DESO2 item 33's build item. Item 14 (the kit's MAIN_F retrain path) is the fixer's reading of DESO2 item 36 against RK. DESO2 names no such build item (the fixer's concern 2). The R basis is right (RK:1190 `"retrain": ("RECIPE_S",)`; :1196-1197 `"retrain": ("anchor",)`; :436; M #7). | Tag item 14 "(I: follows from DESO2 item 36 (2); the ruling names no build item)". |

## 3. R1-R10 (P2R6V)

| id | status | evidence |
|---|---|---|
| R1 | **closed** (minor V1 left) | DESO2 item 36 is written in full in §1.5 (parts (1)-(3), word for word in substance). It also reaches §1.3, §1.4 items 3-4, §1.6, §1.12, §1.19, §2.2, §3.2, §13 row 24, §16.1 edit 2 and §16.2. The contrasts named are right: P1, P2 and P5 are the only primary contrasts that use A1, L1 or S3 (R: P1:181). The bases hold: ADD:21-31 (A2's "Rejected" line, :30-31), RUL:132-141 (ruling 10), P1:103-104 (M #20). The kit cites hold: RK:141, :436, :1186-1192, :1190, :1196-1197 (M #7). §2.2's dropped-run counts are right (I, re-added: 18 → 9 in block A and in block B plan A; A1's 6 under B9 and 9 under H (b)). |
| R2 | **closed** | `63b57c0` merges K6F's 9 kit files byte for byte (M #13: all 9 equal K6F's §1 list; 99 of 108 equal K5W's `wsk3.sha`; the 9 that differ are exactly K6F's). Table D's `pack_setup.py` row is `e3651a98…` (M #4). The README cites are :127 and :133 (M #12). §1.2's counts match K6F §3, K6V's header and the FOCUS 14:06 UTC entry (R, M #11). §1.13 says the pack-time check is built (R: `pack_setup.py:396-417`, called at :464-465, before `out.mkdir` at about :594; M #12). §15 item 12, §16.4 and §14 item 2 are updated. |
| R3 | closed (nit V6) | §1.8, §1.16 and §14 item 33 (a) say MAKER's code and hash change (R: MAKER:209-247, `derive_untuned` keeps the base file's `lists.s4`, M #9). |
| R4 | closed | §1.8 adds the `s3_score` refusal with its message (R: `score_s3_datarx.py:103-105`, M #8). New open item 38 asks what the count covers. |
| R5 | closed | Item 4's basis is in Table B's note; item 7's in §1.19; item 9 (a)'s in §1.13 (R: `lean_eval_job.py:26-29`, :50-54; `oext_unit.py:7-8`, :31-32; M #8); item 11's in §1.16 (R: `write_score_edit.py:29-30`); item 30's list is in §14 item 30, and §8.2, §8.3 and §16.5 item 2 cite DESO item 30. Each matches the old §14 (R: BR `p2-r6-scratch/s14-old.md` items 4, 7, 9, 11, 30; M #14). |
| R6 | closed | §1's heading: "complete except §14 items 33 (b) and 38". These are the only open items, and both touch §1. |
| R7 | closed | The status line, §1.15, §1.16, §1.17 and the end line cite DESO2 items 2 (a), 5. |
| R8 | closed | The §14 preamble says item 2's parts (a) and (b) were new in round 6. |
| R9 | closed | "K5V §2 R4, k5-verify.md:109, :118" (R: :109 is "### R4 ... the data/ premise is not exact"; :118 its bullet; M #10). |
| R10 | closed | §0's last paragraph: "`197ea37` changes 10 kit files". |

## 4. The rulings of 7 Nov

**DESO2 (13:40 UTC; R: DES:129-165).** Each ruling against the text:

- Item 36: section 3, R1.
- Items 2 (a), 5: the status line; §1.16 "How a fill is recorded" (the seven pin fills as recorded lead steps,
  `--check` and the differ-only test as evidence, tables before the freeze, an amendment file after it); §1.17;
  §13.1; §14 items 2 (a), 5.
- Item 9 (b): §1.13 and §1.15's c0 row ("yes (kept)").
- Item 24 (c): §3.2 B+Qi, §4.4, §1.16's new row, §15 item 5.
- Item 31: §8.6. Item 32: §4.2, §16.2, §15 item 5. Item 33: §1.8, §1.16, §15 item 15; (b) left open, rightly.
- Item 34: §5. Item 35: §1.18 items 14, 16; §16.5 items 6, 10 (R: DES:132). Item 37: §1.4 item 5, §4.2, §15 item 5.
- K6v-4: §1.13 and §15 item 12.

All are written as ruled. No wording changes a ruling's substance. Every "DESO2 item n" cite in the text names an
item DESO2 rules (M #15).

**DESO (10:14 UTC).** Its rulings are still in their sections, as P2R6V found (R: P2R6V §3):

- items 6, 17 (§1.8); 7 (§1.5); 8 (§1.12); 9 (§1.13, §4.2); 11 (§1.16); 14 (§1.5); 15 (§1.4); 16 (§1.3);
  18 (§1.14, §4.5); 20 (§1.9); 22 (§2.3); 23 (§1.13); 24 (§4.3, §3.2); 25 (§2.5); 26 (§6); 27 (§8.6); 28 (§16.2);
  30 (§9); the S4 boundary cases (§5).

The round-7a edits to §1.4, §1.13 and §4.2 keep DESO items 9 and 15 and DES E2's words. §4.2 still quotes them
and records DESO2 item 37's narrower fallback beside them (M #16: the diff hunks).

## 5. Hashes and line cites at `63b57c0`

- M #3: `git diff --name-status 197ea37 63b57c0`: 11 M (DES, FOCUS, 9 kit files) and 39 A (4 BR reports, 35 scratch
  files under `k6-fix-scratch`, `k6-verify-scratch`, `p2-r6-scratch`, `p2-r6-verify-scratch`). Nothing under
  `scripts/`, `experiments/` or `research/experiments/`. FOCUS gains one line only (M #11).
- M #4: my own pool over the whole tree. At `63b57c0`: 6,063 blobs, 5,474 hashed, 589 skipped by name. At
  `197ea37`: 6,024, 5,435, 589. The fixer's `pool7.py` re-run gives 4,804 and 4,765 and its own files byte for byte.
  On common paths my hashes equal its hashes (0 differ).
- M #5: the text has 445 hex occurrences (273 distinct). 209 distinct match a file at `63b57c0`. 4 match only at
  `197ea37`, and each is written as an old value: DES `4c2b5cb2…` (twice), `pack_setup.py` `40b99b1a…` (twice),
  README `d7ee370d…`. 60 match no file. My skip rule hid three settings files, which I hashed by path: all equal
  (M #4).
- M #5: the 60 unmatched are commit ids (all resolve), old hashes and record values. Old hashes re-computed:
  DES `72d57b20…` (`e5a2f86`), `4c2b5cb2…` (`5c0d091`, `197ea37`), `af190ede…` (`0e88dfc`, `63b57c0`); RK `57ad4148…`
  (`d203070`); RUN78 `6144546a…` and `pack_setup.py` `f0f098f2…` (`e5a2f86`). The 40 record values each appear in
  12-345 allowed committed files (M #17). `edb0cead…` (P2FV) is in no allowed blob, and no commit holds a
  `*p2-full-verify-pass1*` path; `p2-full-verify.md` has one version, `a7de7b7e…` (M #18). So the text's "lost" record is right.
- M #7: a strict path-aware check of Tables A (44 rows and the 5 prose test files), B (21), C (14), D (16 path rows),
  §2.3 (20) and §16.3's B16 list (14): **134 good, 0 bad**. A pairing check over every line gives 178 equal pairs and 25
  others. I read each of the 25: each is an old value, a commit, a config identity or a record value next to a file
  name, as the text says.
- M #19: engine X's identity re-computed from `63b57c0`'s and `197ea37`'s blobs by `code_identity()`'s rule (29 files):
  `472fc7f6…` at both, equal to RK:106 `ENGINE_X`. The text's "I: it holds" can become M.
- Line cites re-read at `63b57c0` (R; M #7, #8, #10, #12): RK :103, :141, :148, :436, :1186-1192, :1190, :1196-1197;
  `pack_setup.py:396-417`, :464-465; README :127, :133 (and :119, :125 at `197ea37`); `score_s3_datarx.py:7-11`,
  :101-105; `representation_pass.py:337-348`; `make_untuned_answers.py:77-78`, :103-113, :156, :377-379;
  MAKER:209-247; `lean_eval_job.py:26-29`, :50-54; `oext_unit.py:7-8`, :12-20, :31-32; `write_score_edit.py:29-30`;
  P1:33, :103, :104, :181; ADD:21-31; RUL:132-141; PP:101-104; DES:84, :86-90, :132, :154; `k6-verify.md:134-141`;
  `k5-verify.md:109`, :118; `p2-full.md:46-60` (V5); `test_20` (`test_rules_78b.py:1478`, unchanged). All say what
  the text says, except V4 and V5.
- RK, SR78, RUN78 and PT78 have the same bytes at `63b57c0` (M #4), so every older cite of them stands. The
  governing texts and reports hash to the values the text gives: P1, ERR, RUL, ADD, PP, DES, SCOUT, P2FV2, K5F, K5V,
  P2FULL, P2R6F, P2R6V, K6F, K6V; PLAN, CHECK, P78, KCR and PR4 by P1's short names (M #4, #20, #21).
- §13.1's rows are right: both values and the commit for `pack_setup.py`, DES, the two README cites and §1.2's counts.

## 6. New or dropped decisions

- **No new decision found.** The fixer's additions are consequences or labels:
  - §2.2's run counts (I, right);
  - "the money lines are not re-added" (I);
  - §15 item 14 (V7);
  - "none is built" for LN-14's kind (from "not run");
  - three label lines in ruling 16's form (§1.18 item 15, §16.5 items 7, 10 and 11).
- The labels match P2FV2 D7's precedent. Their quotes are right (R: P1:33 holds "+2.03", "+0.11" and "LN-14's
  transfer bar (fails)"; DES:154 holds "report-only at 1B; Branch 128 only"). The lead confirms them (the fixer's
  concern 1). I see no reason to strike them.
- **None dropped.** The word diff (M #22) shows removed text only in the round-6 §14 open items now closed, in
  replaced pointers, and in the old status-line pointer. Each closed item's substance is in its section. Old item
  36's money question is answered in §2.2 (I). Old item 2 (b)'s "find a copy or record the loss" is now a record.
- Open items now: 33 (b) and 38 (both real gaps; R: DES:86-90, :155-158). Add V2 as one more (not in §1).

## 7. Commands (all foreground, each under 5 min; exit 0 unless stated)

1. `date -u` (14:26); `ls` of the scratch and reports; `git rev-parse HEAD`, `git status --short`.
2. `shasum -a 256` of the target, `part2-after-r7.md`, `part2-before-r7.md`, BR and scratch `p2-r6-verify.md`; `wc -c`; `git log --oneline -6`.
3. `git diff --name-status 197ea37 63b57c0` (counts by status; the non-scratch list).
4. `vp.py` (.venv `-I -B`; my pool over the whole tree, skip by name) at `63b57c0` and `197ea37`; `git show <rev>:<path> | shasum` for the 3 skipped settings files; the fixer's `pool7.py` re-run to my scratch, `sort | diff` against its pools, and `join` against mine.
5. `vt.py` (tokens against both pools: 445, 273 distinct, 4 old-only, 60 none, 20 near-name flags, each read); `git show <rev>:<path> | shasum` for 27 current and old values.
6. `git diff 197ea37 63b57c0 -- DES` (one hunk `@@ -125,3 +125,41 @@`, 38 added); `--numstat`; `wc -l` of DES at both commits (165, 127); `sed` of DES 127-132, 154, 165.
7. `git show 63b57c0:RK` to scratch; `sed` and `grep -n` of its cited lines; `vtab.py` (134 good, 0 bad); `vpair.py` (178 equal, 25 read).
8. `git show 63b57c0:` and `sed` of `score_s3_datarx.py`, `representation_pass.py`, `make_untuned_answers.py`, `lean_eval_job.py`, `oext_unit.py`, `write_score_edit.py` cited lines.
9. MAKER `derive_untuned` lines; .venv `-I`: `lists` sizes of both derived and the 1B untuned settings (s3 None, s4 512).
10. `sed` of `k5-verify.md` 100-119, `p2-full.md` 44-61 and `grep -n` of its D rows.
11. FOCUS: `grep -n` of the two ROUND entries' titles; the 14:06 UTC entry in full; `git diff` of FOCUS (one line added); `sed`/`grep` of K6F §1-§3.
12. `sed` of `pack_setup.py` 394-418, 462-466 and `grep -n` of its flow; README 127 and 133 at `63b57c0`, 119 and 125 at `197ea37`.
13. 108 kit files at `63b57c0` hashed and diffed against BR `p2-full-scratch/wsk3.sha` (9 differ); K6F's 9 listed hashes against them (equal).
14. `git show 63b57c0:BR/p2-r6-scratch/s14-old.md | grep` items 4, 7, 9, 11, 30; `awk` of the round-6 §14.
15. `grep -o` of DESO and DESO2 item cites in the target.
16. `diff` and `git diff --no-index --word-diff` of the before and after texts (346 diff lines; 311 removed spans read by size).
17. `vg.py` (40 record values in allowed committed blobs: 12-345 files each).
18. `git log --all -- '*p2-full-verify-pass1*'` (empty); `git log --all` of `p2-full-verify.md` and its hash per commit; `find -name '*pass1*'` in the scratch tree (none); `ls` of the named backup path (absent).
19. `vid.py` (engine identity from blobs at both commits).
20. `sed` of P1 33, 100-106, 163-175, 176-184; ADD 19-32; RUL 130-142; PP18's lines.
21. `git show 63b57c0:` and `shasum` of ERR, SCOUT, P2FV2, K5V, P2FULL, SC, PINS, WRAP, MAKER; P1's short-name lines for PLAN, CHECK, P78, KCR and PR4, matched in the pool.
22. Word diff spans sorted by length (part of 16).
23. `git grep -n 'def test_20'` at both commits; `git ls-tree` of BR scratch folders added at `63b57c0`.
24. Final: `git rev-parse HEAD`, `git status --short | wc -l` (19), target `shasum` (unchanged), `find __pycache__` (0), `du -sh` of my scratch (3.4 MB), `date -u` (14:42).

## 8. Acceptance criteria

| criterion | result | evidence |
|---|---|---|
| R1-R10 closed | passed (R1 with minor V1) | section 3 |
| Both sets of open-item rulings written as ruled | passed | section 4 |
| Every hash re-computed at `63b57c0` | passed | section 5, M #4-#7, #13, #17, #19 |
| Every line cite re-computed at `63b57c0` | passed for every cite in section 5's list (nits V4, V5). Not re-read: cites of files unchanged since `197ea37` that round 7a did not touch. P2R6V read those at the same bytes. | section 5 |
| No new decision | passed | section 6 |
| None dropped | passed | section 6 |
| VERIFIED = "commit the scorer section and the draft now" | **yes, with minor fixes advised first** (V1, V3 sit in §1 or its open items) | section 1 |
| Kit suites, mutants | not tested (a text track); §1.2's counts are R | section 3, R2 |

## 9. Jobs for the lead

1. Apply V1, V3 and V4-V7 (text only) before committing §1; or commit now and carry V1 and V3 as one dated
   amendment.
2. Rule §14 items 33 (b) and 38 before the first untuned-answers pod. V3's fact belongs in 33 (b)'s ruling.
3. Add V2 as a §14 item and rule it before the SR-2 simulation runs (before block A; not in §1).
4. Confirm the three label lines (§1.18 item 15; §16.5 items 7, 10, 11). I found them right in form and quote.
5. Optional: the engine identity at `63b57c0` is now M (M #19). Table D's header can say so.
6. After review, delete `reports/p2-r7-verify-scratch/` (3.4 MB) and the fixer's `reports/p2-r7-scratch/` (1.7 MB).

## 10. Unresolved concerns

1. V1's second half (the X retrain's recipe on a stopped family) is my inference. DESO2 item 36 (3) says only
   "as ruling 10 says". I see no other reading, but the lead should confirm it.
2. I did not re-read every older cite of files unchanged since `197ea37` (PLAN, KCR, RP, P78, EYD, PR4 and most
   RUN78, SR78 and PT78 cites). Their bytes are unchanged (M #3, #4), and P2R6V read them.
3. "Every [to be entered] value is entered before the freeze" (§14 item 22) meets "not run" for A1, L1 and S3 on a
   stopped family. The meaning ("not run, stated") is clear from DESO2 item 36. I did not count it as a defect.
