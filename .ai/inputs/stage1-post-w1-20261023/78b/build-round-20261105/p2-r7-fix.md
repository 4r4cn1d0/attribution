# Round 7a: Part 2 text fixes (p2-r7-fix)

Started 2026-11-07 14:07 UTC; this version 14:25 UTC (`date -u` before each write). Status: **DONE**.

Tags: M measured (command number in section 7), R read (path:line), E estimate, I inference.
Target: `scratchpad/b78/ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`.
Before: `dbce35baed4a3faa79674c9c029313db3182cc0c5bcd84d59b2acafe316d3bac`, 843 lines (M #1; equal to P2R6V's value).
After: `1889e8e51b0ad9d0eef5be29367cc4dae930d184b79c0d16ea7775056473269e`, 875 lines, 191,179 bytes (M #14).
No git state changed. No pod, spend, network, install, download, agent or message. In the main checkout I only read
(`git show`, `ls-tree`, `cat-file`, `diff`, `log`, `grep`, `rev-parse`, `status`). No forbidden folder, selector,
hidden, judge, answer, generation, sample or prompt-text file was opened; the hash pool skips those names. No secret
read or written. The side paper is not mentioned.

## 0. Files changed
| File | Change |
|---|---|
| `ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md` | items 1-4 below |
| `reports/p2-r7-fix.md` | this report |
| `reports/p2-r7-scratch/` (1.7 MB) | `part2-before-r7.md` (the `dbce35ba…` text), `part2-after-r7.md`, `code/pool7.py`, `code/tok7.py`, `code/near7.py`, `code/tables7.py` (my scripts), `pool-63b57c0.tsv` (4,804 rows), `pool-197ea37.tsv` (4,765 rows), `tok-before.tsv`, `tok-after.tsv`, `s14-31-37-old.md`, `s14-31-38-new.md` |

## 1. Item 1: R1 by DESO2 item 36; R3-R10 as P2R6V proposes
New short name: **DESO2** = DES's "second set", 13:40 UTC (R: DES:129-166). Also P2R6F, P2R6V, K6F, K6V.

| id | Fix | Where |
|---|---|---|
| R1 | The stops in full, as ruled: no bank, no S_78; `rep_pass`, `l1_scan`, classifier, `a1_pass` do not run; A1, L1, S3 not run; P1, P2, P5 not tested (R: P1:181); DataShield-style and Gate C reproduction not run; the a0-1101 retrain under MAIN_F on Y as ruling 10's certificate and ruling 7's check (A2's rejected alternative, this case only; R: ADD:21-31, P1:103-104, RUL:132-141); Y's pack, KD9, B+Qi on Y, confirmation follow it | §1.5 (main text), §1.3, §1.4 items 3-4, §1.6, §1.12, §1.19, §2.2 (rows lost, I: 18→9, 18→9, A1's 6 and 9), §3.2 B+Qi, §13 row 24, §16.1 edit 2, §16.2, §14 items 7, 36 |
| R1 (kit) | RK cannot plan the MAIN_F retrain: `"retrain": ("RECIPE_S",)` (R: RK:1190), `SC_AFTER` needs a complete anchor job (R: RK:1196-1197) | §1.3, §1.5, new §15 item 14 (build item) |
| R3 | A reduced list changes MAKER's code and hash (R: MAKER:209-247; `make_untuned_answers.py:77-78`) | §1.8, §1.16, §14 item 33 (a) |
| R4 | `s3_score` refusal added (R: `score_s3_datarx.py:103-105`); whether the count covers `encode_train` of the `s3_safe` pairs is new open item 38 | §1.8, §14 item 38 |
| R5 | Bases moved back: item 4's M (K4CV #6) to §1.17 Table B note; item 7's I (untuned U 11 and 32 of 600; P1 §0 item 4) to §1.19; item 9 (a)'s basis (`oext_unit.py:7-8`, :31-32; `lean_eval_job.py:26-29`, :50-54; LN-27) to §1.13; item 11's (`write_score_edit.py:29-30`; ADD-4.8) to §1.16; item 30's list into §14 item 30, §8.2, §8.3, §16.5 item 2 | as listed |
| R6 | §1 heading: "complete except §14 items 33 (b) and 38" | §1 heading |
| R7 | The re-take rule now cites DESO2 items 2 (a), 5 | status line, §1.15, §1.16, §1.17, end line |
| R8 | §14 preamble: item 2's parts were new in round 6 | §14 preamble |
| R9 | "K5V §2 R4, k5-verify.md:109, :118" (R) | §14 item 2 |
| R10 | "`197ea37` changes 10 kit files" | §0 last paragraph |

## 2. Item 2: DESO2 written into sections; §14 closed down
- 2 (a), 5: status line; §1.16 "How a fill is recorded"; §1.17; §13.1 (new). 9 (b): §1.13, §1.15 row. 24 (c): §3.2,
  §4.4, §1.16 (new row), §15 item 5. 31: §8.6. 32: §4.2, §16.2, §15 item 5. 33: §1.8, §1.16, §15 item 15. 34: §5.
  35: §1.18 item 14, §16.5 item 6. 36: as R1. 37: §1.4 item 5, §4.2, §15 item 5. K6v-4: §1.13, §15 item 12.
- §14: items 2, 5, 9, 24 and 31-37 closed to one-line records. **Still open: 33 (b) and 38** (both gaps, no ruling
  picked). Item 2 (b) now records that P2FV is lost and names P2FULL's P2.2 table (R: p2-full.md:46-60) as the
  surviving D-list. My own checks: no file named `*pass1*` under the scratch tree; `git log --all` on that path empty
  (M #9).
- Labels (ruling 16's form, the form P2FV2 D7 used for DESO item 7): §1.18 item 15 and §16.5 item 7 widened to DESO2
  item 36 (P2 +2.03 and P5 +0.11 known; R: P1:33); new §1.18 item 16 and §16.5 item 10 (DESO2's header line, R:
  DES:132); new §16.5 item 11 for DESO2 item 32 (LN-14's 1B "fails" known; R: P1:33). These are my additions (I).

## 3. Item 3: hashes and cites re-taken at HEAD `63b57c0`
- M #3: `git diff --name-status 197ea37 63b57c0`: DES, FOCUS, 9 kit files (README, `pack_setup.py`, 4 tests, 3 specs),
  BR files. Nothing under `scripts/`, `experiments/`, `research/experiments/`. 108 kit paths at both commits.
- M #4, #5: my pool of 4,804 blobs at `63b57c0` and 4,765 at `197ea37` (341 skipped by name each). Before the edits:
  279 tokens; 203 match a file at `63b57c0`; 2 matched only at `197ea37`: `pack_setup.py` `40b99b1a…` and DES
  `4c2b5cb2…`. After: 296 tokens; 211 match; 4 old-only, all now written as old values (the two above, README
  `d7ee370d…` in §13.1).
- M #6: the 50 unmatched: 7 commit ids (`git rev-parse`), old hashes recomputed (`d203070`'s RK `57ad4148…`,
  `e5a2f86`'s DES `72d57b20…`, `pack_setup.py` `f0f098f2…`, RUN78 `6144546a…`; `197ea37`'s DES `4c2b5cb2…`), record
  values each in 2-206 committed files (`git grep -l`), the round-6 text's `dbce35ba…`, and P2FV's `edb0cead…`.
- M #12: path-aware table check: Tables A (44), B (21), C (14), D (16 path rows), §2.3 (20): 115 good, 0 bad. B16's 14
  short hashes and the 5 extra test-file hashes: all equal by path. Near-name check: 197 good, 24 flagged; each flag is a
  short name (ERR, PLAN, CHECK, P78, KCR, PR4, RK, DES), a record, or a config with equal bytes elsewhere (read: right).
- Re-taken values that differ, in §13.1 with both values and the commit: `pack_setup.py` `40b99b1a…` → `e3651a98…`
  (`63b57c0`); DES `4c2b5cb2…` → `af190ede…` (`0e88dfc`); README :119 → :127 and :125 → :133 (`63b57c0`; M #7);
  §1.2's counts 471 → 487 and mutants 124/34/109/140 → 128/35/109/155 (R: K6F §3; FOCUS 14:06 UTC entry).
- Line cites: RK, SR78, RUN78, PT78 same bytes (M #2). DES only appends lines 129-166 (M #8: one hunk at :125, +38).
  New cites read at `63b57c0`: `pack_setup.py:396-417`, :464-465; `k6-verify.md:134-141`; RK :436, :1186-1192, :1190,
  :1196-1197; `score_s3_datarx.py:7-11`, :103-105; `k5-verify.md:109`, :118; `p2-full.md:46-60`; P1:33, :103, :104,
  :181; RUL:132-141; ADD:21-31; DES:86-90, :132, :154; MAKER:209-247; `lean_eval_job.py:26-29`, :50-54;
  `oext_unit.py:7-8`, :31-32; `write_score_edit.py:29-30`; `make_untuned_answers.py:77-78` (M #10, #11).
- Engine X identity not re-printed (I: no `experiments/` file changed; stated as I in Table D's header).

## 4. Item 4: status line
Unchanged in substance. Only the pointer changed: a differing hash "is recorded in the change log (§13.1) with both
values and the commit that changed it (DESO2 items 2 (a), 5)". No new decision: the gaps are §14 items 33 (b), 38.

## 5. Acceptance criteria
| Criterion | Result | Evidence |
|---|---|---|
| R1 fixed by DESO2 item 36 in full | passed | §1 above; §1.5 and 11 other places |
| R3-R10 fixed as P2R6V proposes | passed | §1 above |
| DESO2 written into sections; its items closed in §14 | passed | §2 above; open only 33 (b), 38 |
| Item 2 (b) records P2FV's loss, citing P2FULL's table | passed | §14 item 2; Short names |
| Every kit and script hash re-taken at `63b57c0` by my own hashing | passed | M #4-#6, #12 |
| Every line cite re-taken | passed for the changed files and every new cite; unchanged files by byte identity (M #2, #3) | §3 above |
| Differing hashes in the change log with both values and commit | passed | §13.1 |
| Status line unchanged in substance | passed | §4 above |
| No new decision; gaps to §14 | passed, with concern 1 | §14 items 33 (b), 38; §15 item 14 |
| Kit suites, mutants | not tested (a text track) | §1.2 cites K6F, K6V, FOCUS |

## 6. Unresolved concerns
1. Three label lines are mine (I): DESO2 item 36 and item 32 labelled "chosen after the stage-1 reading" (§1.18 item
   15, §16.5 items 7, 11). I followed P2FV2 D7's form. The lead should confirm.
2. §15 item 14 (the kit's MAIN_F retrain path) is a build item I derived from DESO2 item 36 and RK's pins. The ruling
   does not say how the kit does it.
3. §2.2's dropped-run counts (18 → 9 etc.) are my arithmetic (I). The money lines are not re-added for the stop case.
4. §14 item 33 (b) (a new s-pool record for a reduced `s3_safe`) and item 38 (does the count cover `encode_train` of the
   pairs) need the lead before the first untuned pod. Both touch §1's rules, so §1's heading names them.
5. `p2-r7-scratch/` (1.7 MB) can be deleted after review.

## 7. Commands (all foreground, each under 1 min; exit status 0 unless stated)
1. `date -u` (14:07); report skeleton; `ls` of scratch; `git log -3`, `git status --short`; copy and `shasum`, `wc` of the target.
2. `git show <rev>:<kit file> | shasum -a 256` for 8 kit files at `63b57c0` and `197ea37`.
3. `git rev-parse HEAD`; `git log 197ea37..HEAD`; `git diff --name-status 197ea37 63b57c0`; `git ls-tree | wc -l`.
4. `pool7.py` at `63b57c0` and `197ea37` (.venv `-I -B`): 5,145/4,804/341 and 5,106/4,765/341.
5. `tok7.py` on the text before (279 tokens) and after (296).
6. `git grep -l` of each unmatched token at `63b57c0`; `git rev-parse` of 7 commits; `git show <old rev>:` for 6 old hashes.
7. `git show 63b57c0:` and `197ea37:` README `grep -n` (rates, "stop, never delete").
8. `git diff 197ea37 63b57c0 -- DES` hunks; `sed -n` of DES 132, 154.
9. `git log --all -- '*p2-full-verify-pass1*'` (empty); `find` for `*pass1*` in the scratch tree (none); `git grep -l edb0cead`.
10. `sed`/`grep` of K6F, K6V, FOCUS diff, P1:33, :100-106, :176-184, RUL:132-141, ADD:21-31, RK :141, :433-438, :1186-1197.
11. `sed` of `score_s3_datarx.py`, `k5-verify.md`, `p2-full.md`, `pack_setup.py`, `write_score_edit.py`, `oext_unit.py`, `lean_eval_job.py`, MAKER, `make_untuned_answers.py` at `63b57c0`; old §14 from BR `p2-r6-scratch/s14-old.md`.
12. `tables7.py` (115 good, 0 bad); B16 and test-file short-hash loop (19 ok); `near7.py` (197 ok, 24 flagged, read).
13. Edits by the Edit tool; two `sed -i` single-string fixes; two .venv `-I -B` replace scripts (each asserts its match count).
14. Final `shasum`, `wc`; `find __pycache__` (none); `git rev-parse` (`63b57c0`); `git status --short | wc -l` (19, as at P2R6V's run); `du -sh`; `date -u` 14:24.
