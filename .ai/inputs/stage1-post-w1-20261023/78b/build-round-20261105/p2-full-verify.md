# P2-full verify, pass 2 (round 5): adversarial check of Part 2 after the writer's second pass

Started 2026-11-07 11:00 UTC; this version 11:17 UTC (`date -u` before each write). Status: **DONE**.

**Verdict: DEFECTS (1 major, 6 minor, 2 nits; no blocker).** Every hash, kit value and re-added sum I checked is
right. DESO and P2FV's D1-D11 are applied, and I found no DESO ruling dropped. But one major gap is in the scorer
section (D1): the anchor job's stop rule names A1 and contrast P1 only, while L1, S3 and the classifier read the same
anchor file, so they cannot run either. The fix is text (state the dependency, add an open item) plus one lead ruling.
The minor defects are text fixes. After D1-D5 are fixed and K5F's files are merged and re-hashed (job 1), the scorer
section can be committed; the rest is then a correct draft for the freeze, with §14's open items for the lead.

- Target (read-only): `scratchpad/b78/ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`, SHA-256
  `1975fee806a2477b3bd211ec24293b7a48b1d719ac6697bf96254e9127b319eb`, 830 lines, 167,000 bytes (M #2, #40: same at
  start and end; equal to the writer's value).
- Baselines: the pass-1 text `p2-full-scratch/rerun/part2-bbe42ff0.md` (M #8: `bbe42ff0…`, the hash P2FV checked);
  K5W = `scratchpad/b78/ws-k3` (HEAD `e5a2f86` + K5F's 10 kit files, M #10); the main checkout's HEAD `5c0d091` (M #3).
- **This file replaces the pass-1 verify report at the same path.** That report (P2FV, the one Part 2 cites for
  D1-D11; SHA-256 `edb0cead715d9149…`) is kept byte for byte at
  `reports/p2-full-verify-scratch/pass2/p2-full-verify-pass1.md` (M #2). See job 2.
- Tags: M measured (command number in section 4), R read (path:line), E estimate, I inference.
- No git state changed. No pod, spend, network, install, download, agent or message. I wrote only this report and
  `reports/p2-full-verify-scratch/pass2/`. In the main checkout I only read (`git show`, `ls-tree`, `cat-file`, `grep`).
  RK was imported read-only with `-B` under the network-deny sandbox; no `__pycache__` in K5W or ws-p (M #40). No
  forbidden folder, `selector.jsonl`, `hidden/`, judge, answer, generation, sample or prompt-text file was opened; the
  hash pool skips any path with "hidden" or "selector" and any `.ai/` data file named for judges, answers,
  generations or samples; from the Llama MANIFEST I printed keys, counts and flags only. No secret read or written.
  The side paper is not mentioned.

## 1. Files changed

| File | Change |
|---|---|
| `reports/p2-full-verify.md` | this report (replaces P2FV's pass-1 report at this path; see job 2) |
| `reports/p2-full-verify-scratch/pass2/` | `p2-full-verify-pass1.md` (backup of P2FV), `pool.py`, `pool.tsv` (1,816 hash rows), `tokens.py`, `nearest.py`, `tok-old.txt`, `tok-new.txt`, `rkcheck.py`, `oext43.py`, `k5w-now.sha`, `k5w-pass1.sha`, `scout.md` (a `git show` copy of SCOUT); 404 KB |

## 2. Checks and evidence

### 2.1 Hashes (no defect)
- M #12-#13: a pool of 1,816 SHA-256 values: K5W's 108 kit and scorer files, and 1,708 HEAD blobs of the cited
  folders. The target has 275 hex tokens (247 distinct). 204 match a pool file. For each, the line names that file;
  a stricter check (the nearest named file before the token, M #17) left 22 cases, and I read each one by hand: all are
  right (short names P1, ERR, PLAN, CHECK, PR4, SEAL; "settings" after a script; record files under BR scratch).
- Files with one basename in several places were mapped by full path (M #34): RUN78 `36a78632…` is K5W's
  `runkit/stage1-78b/setup/job_runner_stage1.py` and `6144546a…` HEAD's; `pack_setup.py` `40b99b1a…` (K5W) and
  `f0f098f2…` (HEAD); SR78, PT78, RK, backup, both `conftest.py`, both `__init__.py`, B16's 14 files, `stage3_pick.py`,
  `overrefusal_checks.py`, the lean job and its settings: each is the file the text names.
- The 71 tokens that are not file hashes are record values. I found each in a committed record with the meaning the
  text gives (M #14-#16): model revisions, manifests, config hashes, engine identity, training identities, the side
  units' COMPLETE.json pins (RK), the 1B recipes (OXU), the tmp/ text files (PINS, the s-pool and S1 records), the
  bank file (oext record), HarmBench's revision `51182c7c` (HEAD research records), `1e5e23f7` (write_score_edit.json).
  Computed: DES at `e5a2f86` = `72d57b2098860b64…` and at HEAD = `4c2b5cb264b0f1ca…`; d203070's RK =
  `57ad4148ab781dd9…`; P1 `b682513f…`, ERR, PLAN, CHECK, P78 `e6a73c92…`, KCR `9884bd17…`, PR4, SCOUT `22ab3f2c…`;
  the four commit ids resolve to the full ids given (M #10, #15, #16).
- M #18: against pass 1, the hex-token set grew from 242 to 244: `4c2b5cb264b0f1ca` and `5c0d0919336fb7e9` added,
  none removed. The writer's claim holds.
- M #35: K5W's 108 files are byte-identical to the writer's pass-1 list `p2-full-scratch/wsk3.sha`.

### 2.2 Numbers re-derived (no defect)
- M #20 (K5W's RK, its own functions): §1.15's 10 kinds × 2 families (cap, guard, spend upper, state flag; the untuned
  uppers 16,146 s and 16,692 s); §3.2's `ref_eval` 5.0/5.25 h, `safe_lora` 5.5/5.75 h, `ref_train_bqi` 4.75/5.0 h;
  `pod_sizes` 5, 6, 8, 21, 23; `arm_pod` at 38 and 39 steps (12,365.42 / 12,389.67 s; 12,612.47 / 12,635.36 s);
  13 idle pods at $4.33 per day; `sc_seeds`; `X_ONLY_KINDS`, `S78_KINDS`, `SC_STATE_KINDS`; all six null pins;
  `STEPS` without 39; `KINDS` without `ref_train`, `transfer_report` or `w1_18`. All equal the text.
- M #20, #21: §4.3's table, every cell: caps 10.5 / 15.0 / 17.25 h and 12.5 / 17.0 / 19.25 h; guards; launch needs
  $104.63 / $146.25 / $167.06 and $123.13 / $164.75 / $185.56 (D2 of P2FV is fixed). The step: 3,958.9 and 4,061.4 s,
  × 1.5 5,938.4 and 6,092.2 s.
- I (arithmetic on SCOUT's lines, R: scout-p2.md:651-660): SCOUT's sums are 591 + 50 + 2 + 25 + 140 = 808 and
  801 + 100 + 4 + 50 + 230 = 1,185 (Branch 128); 958 and 1,440 (Branch full). §8.5's re-added sums all reproduce:
  2-day $828-1,180 and $978-1,435; 7-day $978-1,355 and $1,128-1,610. $591-801 = $640-900 − $49-99.
- DESO item 26's 7 per family: OLMo-2-7B R_1-R_3 + a0 1101-1103 + θ0 = 7; Llama R_1-R_3, a0-1103 + a0 1101-1102 + θ0
  = 7 (I; R: P1:203). §4.5's 14 O pods = 2 + 5 + 7 (I).

### 2.3 Citations (new and changed cites all read; no defect)
- R: DES:81-127 (DESO); P1:181 (P1 = U(R) − U(A1); no other contrast uses A1), P1:292, P1:311 (AD1, AD2), P1:365;
  PR4:428, :479, :485, :536, :562-574; RK:78, :103, :141, :158-159, :313, :373, :436, :477, :1060-1091 (idle pods and
  lines; the docstring says state-keeping pods only), :1169-1197; RUN78:597-626 (no `--w1-18-record` or
  `--dev100-source`; M #27: grep empty); SR78:192, :199, :311, :334, :378-381, :383-384, :388, :401, :494-498;
  PP:78-80; `stage3_pick.py`:9-13 (":11-13" holds it; ":12-13" is exact); the 1B runner :17-21 and :76-78; the 1B rules
  :598-602 (`ref_train` at :600, `KIND_IDS` at :602); K5W README:117-125 (:119 the rates, :125 "stop, never delete").
- M #28: the Llama sealed MANIFEST's `parity.sealed` has 13 entries (R_d1-R_d5 and the 8 unit files), all
  `byte_identical` true; `parity.stage1_r_draws` 5 (R_d6-R_d10), `remove_list_equal` true (P2FV D5 (b) is fixed).
- The other cites are unchanged since pass 1, and their source files are unchanged at `5c0d091` except DES (M #10), so
  P2FV's section 2.3 still holds for them.

### 2.4 Rulings coverage (DESO, D1-D11, DES, PP, P1, RUL, ADD)
- §14's numbering equals pass 1's (M #8: items 1-30 have the same subjects), so DESO's item numbers point to the right
  items.
- Every DESO ruling is in the text: items 6 and 17 (§1.4, §1.8, §1.10, §0 item 14, §13 row 3), 7 (§1.5, §1.19, §16.1),
  8 (§1.12), 9 (§1.13, §4.2, §15 item 5), 11 (§1.16), 14 (§1.5), 15 (§1.4), 16 (§1.3, §1.16), 18 (§1.14, §4.5),
  20 (§1.9), 22 (§2.3, §14 item 22, end line), 23 (§1.13, §15 item 12), 24 (a, b) (§3.2, §4.3, §15 item 5),
  25 (§2.5, §4.5), 26 (§6, §15 item 7), 27 (§8.6), 28 (§15 item 13, §16.2), 30 (§9, §16.3, §16.4), the S4 boundary
  cases (§5). Missing: DESO's sentence on the items it does not name (D3).
- P2FV D1-D11: each is applied as P2FV asked (R: the diff, M #8-#9; D2 and D5 (b) by M above; D6 by M #20).
- New decisions: one timing not in DESO (D2). The pass-1 text also carried one trigger reworded from DES E2 (D6).
- Labels: §1.18 item 14 and §16.5 items 5-6 are new and right in form; two fallbacks lack ruling 16's knowledge note (D7).
- No [to be entered] marker is in §1 (M #37), so the scorer section's commit needs no value that comes later.

## 3. Defects

| id | sev | where | defect | fix |
|---|---|---|---|---|
| D1 | **major** | §1.5 anchor bullet; §1.19; §16.1 edit 2; §13 row 24; §14 item 7 | The anchor stops' fallback says only "A1 is not run, contrast P1 is not tested" (DESO item 7). But with no anchor file there is no `ANCHOR_BANK` and no S_78_F, and the kit plans `l1_scan` only with `ANCHOR_BANK`, and `rep_pass` and `classifier` only with `RECIPE_S` and `ANCHOR_BANK` (R: RK:1186-1197 `SC_KIND_PINS`, `SC_AFTER`). L1's scan reads BANK's 64 harmful prompts (R: `score_l1_larf.py:8`), and S3's score reads REQ-3's anchor means (R: `score_s3_datarx.py:12-14`). So on that family L1, S3 and the classifier cannot run either: P2 and P5 are not testable under plan A, and B9's and H (b)'s secondary L1 and S3 data are lost. The text implies they go ahead. | State the dependency (R) beside each fallback line. Add §14 item 36: whether L1, S3 and the classifier are "not run" and P2, P5 "not tested" on that family, and what that does to §2.2's tables. The lead rules it before the first anchor pod, so the fallback is not chosen after the stop. |
| D2 | minor | §0 item 14; §14 item 29 | Both put the OLMo-2-7B S1 re-check among "the $0 checks before each family's untuned-answers pass". DESO item 20 says "before block A", and §1.9 says so too. This is a timing that no ruling gives, and it applies an OLMo-only check to "each family". | "... and, before block A, the OLMo-2-7B S1 re-check (DESO item 20)". |
| D3 | minor | §14 preamble; item 5 | DESO says: "Items not named here are records or build steps the text already states" (R: DES:84). The text does not carry this. Item 5 still reads "is not ruled", and P2FULL job 3 asks the lead to rule it, while DESO puts item 5 among the settled ones. Item 5 names two routes without a pick, so the two readings conflict. | Quote DESO's sentence in §14's preamble. Mark the unnamed items (1-5, 10, 12, 13, 19, 21, 29) by it. For item 5 state the conflict and ask the lead which route; do not pick one. |
| D4 | minor | §14 item 33 | The reduced-list gap is wider than stated. (a) Both derived untuned settings pin `lists.s4.size` = 512 (M #33), and the 1B code refuses a list of another size (R: `make_untuned_answers.py:77-78`). So a shorter S4 list also needs the settings re-derived by §1.16's fill steps, which changes PINS, the settings, `PINS-78B.json`, WRAP and SR78. (b) `s3_score` requires the `s3_safe` pool hash that the committed s-pool record `bcca59ac…` names (R: `score_s3_datarx.py:7-10`). So a shorter `s3_safe` also needs a new s-pool record. | Add (a) and (b) to item 33, as gaps for the lead. |
| D5 | minor | §14 item 2 (and P2FULL job 1, concern 5) | Stale: "K5V's report still reads IN PROGRESS". K5V finished at 10:58 UTC on 7 Nov: VERIFIED_WITH_MINOR. Its own re-runs gave 471 and 762 passed, and 124 + 34 + 109 + 140 mutants killed. It also found 7 hand-mutant survivors and 7 test files that leave token-shaped strings, and the pack's `data/` premise is not exact (R: `reports/k5-verify.md`:3-12, §2, §3). Its fixes may change K5F's test files, and possibly `pack_setup.py` and README.md. Then Table D's `pack_setup.py` row, the README:119/:125 cites (§8.3, §8.6) and §1.2's counts change. | Update item 2 with K5V's verdict and these possible changes. The merge (job 1) settles them. |
| D6 | minor (from pass 1) | §4.2 first two bullets; §1.4 item 5 | DES E2 says "as the first O job" and gives the fallback "not built before the first O-ext pod". The text writes "the family's first O job" and "the family's first O-ext pod". That turns the trigger per family: OLMo's O pods could run before the check is built, and only OLMo then falls back. SCOUT runs one pod on all seven units as "the first O job of the scorer block" (R: scout-p2.md:118-119, :122-123, :127), and §4.2's own cost and kit bullets say one pod and seven units. | Use DES's words, or add an open item: one W1-18 pod for both families or one per family (and OLMo's four units only under [C]). |
| D7 | minor | §16.5 (items 6, 7); §16.2; §1.18 item 14 | Ruling 16's labels, in the form that §1.18 items 8-9 use, name what the authors knew. Two DESO fallbacks drop an analysis whose 1B result the authors knew. Item 7 drops contrast P1 on an anchor stop (P1 read "better, +6.33 pp" at 1B; R: P1 §0 item 1, P1:33). Item 28 drops the overlap control when there is no build room, and SCOUT warns that dropping it "after 1B's 'S1 and S3 not shown' could read as a choice after a result" (R: scout-p2.md:624-626). Neither trigger reads an outcome, but neither label says this. | Add both to §16.5 (and §1.18 item 14 for item 7): "chosen after the stage-1 reading; the trigger reads a stop code / build room only; the authors knew the 1B result named". |
| D8 | nit | §0 item 3 | The 7 Nov author also read K5V's partial report (R: P2FULL P2.3 item 2). It holds no outcome. | Add K5V to item 3's list. |
| D9 | nit | §4.3 first bullet; §0 last paragraph | "...own jobs too (R: ...); The 7-8B references" (a capital after a semicolon). "HEAD `5c0d091` adds no file but DES": it changes DES and adds no file. | Wording. |

## 4. Commands (all foreground, each under 1 min; exit status)

1. `date -u` (11:00, 11:00, 11:15); `ls` of scratch and rulings; `git log --oneline -5` (0).
2. `mkdir`, `cp -p` of the pass-1 verify report, `shasum` of backup and target, `wc` (0).
3. `cat -n` DES; `shasum` of the four rulings files; `git status --short`, `rev-parse HEAD` (0).
4. Read of the target, all 830 lines (0).
5. `cat` P2FULL; `sed` of the pass-1 verify report (0).
6. `head`, `grep` and `sed -n 60,160p` of `k5-verify.md` (0).
7. (part of 5) — none.
8. `shasum` of `part2-bbe42ff0.md` (`bbe42ff0…`); `diff` hunk list (195 changed lines); title diff; pass-1 §14 item list (0).
9. `diff` removed lines, two reads (0).
10. `git show --stat 5c0d091` (1 file, +48); DES at `e5a2f86` and HEAD; `rev-parse` of 4 commits; ws-k3 `rev-parse`, `status --short` (10 files) (0).
11. `git ls-tree` counts and names of the cited record folders (0).
12. `pool.py` (.venv `-I -B`, `caffeinate -i`): first 1,787 rows (a name filter skipped 5 code files), refined: 1,816 rows (0); `find` of the skipped names (0).
13. `tokens.py`: 275 tokens, 204 matched, 71 not file hashes, 19 flagged for hand review (0).
14. `grep -rl` in K5W and `git grep -l` at HEAD for 33 record tokens (0).
15. P1 short-name lines; `git show d203070:RK | shasum`; `git grep 51182c7c` (0).
16. `git show HEAD:<P78, KCR, PLAN, CHECK, PR4, ERR, SCOUT> | shasum` (0).
17. `nearest.py`: 204 checked, 22 hand-reviewed, all right (0).
18. `grep -o` token sets of both versions, `comm` (0).
19. `cat` of the pass-1 verifier's `rknums.py`, `oextstep.py` (API only) (0).
20. `rkcheck.py` (MAIN python `-B`, sandbox-exec network deny) (0).
21. `oext43.py` (same) (0).
22. `sed` RK:1060-1095; `git show` P1:305-318 (0).
23. `git show` PR4:428, :479, :485, :574; P1:181, :292, :365 (0).
24. `git show` PR4:562-573, :536 (0).
25. `git show` SCOUT to scratch, headings, §1.2, §4.1-§4.3, §9, §8.5-§8.7; K5W README:117-127 (0).
26. PP:76-81; `stage3_pick.py`:9-14 and its hash; the 1B runner :17-21, :76-78; the 1B rules :598-602 (0).
27. K5W RUN78:597-627; `grep` for the two flags (no hit) (0).
28. .venv `-I -B` over `git show` of the Llama sealed MANIFEST: keys, names, flag counts (two runs) (0).
29. `grep` for DESO's unnamed-items sentence (no hit) and "not ruled" phrases (0).
30. `git log` of FOCUS; FOCUS entries of 5-7 Nov (titles); the newest entry's pod line (0).
31. `git show` `make_anchor_answers.py`:1-20, :110-125; RK:1169-1197 (0).
32. `git show` `score_s3_datarx.py`:1-22, `score_l1_larf.py`:1-12 (0).
33. `grep` and `sed` of `make_untuned_answers.py` (:63-80, :230-233); .venv `-I -B` of both derived untuned settings' list sizes (0).
34. Full-path map of 39 hash prefixes in the pool (0).
35. K5W hash list against `p2-full-scratch/wsk3.sha`: same (0).
36. `sed` of SR78 and RK cite lines: first run exit 1 (a zsh `==` echo), re-run without it (0).
37. `grep -n "to be entered"`; count in §1 = 0 (0).
38. `grep` of "overlap" in SCOUT, the target and P1 (0).
39. (none)
40. `find __pycache__` (none); `find -newer` in ws-k3 and ws-p (only the target, last written by the writer); final `shasum` of the target (`1975fee8…`); `du`; `date -u` (0).

## 5. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Every section against DES (with DESO), PP1-PP18, Part 1, RUL, ADD and SCOUT: no new decision, none dropped | **failed (minor)** | 2.4. No ruling dropped except DESO's unnamed-items sentence (D3). One new timing (D2) and one reworded trigger (D6). |
| Gaps go to §14 | **failed (major)** | D1: the anchor stops' reach to L1, S3 and the classifier is not stated or listed. D4: item 33 is incomplete. |
| Every number re-derived where it can be | passed | 2.2 |
| Every cited hash re-computed (K5W for the kit and scripts, HEAD for the rest) | passed | 2.1 |
| Citations read | passed | 2.3 (new and changed cites; the rest as P2FV) |
| Labels for choices after the stage-1 reading | passed with D7 | 2.4 |
| P2FV D1-D11 fixed | passed | 2.4 |
| The scorer section can be committed now | **not yet** | after D1 (text and open item), D2, D3, D5 and job 1 |
| The rest is a correct draft for the freeze | passed after D4, D6-D9 | 3; §14's open items stay with the lead |
| Kit suites and mutants re-run | not tested | text track; K5V's re-runs match §1.2's counts (R: k5-verify.md §3) |

## 6. Jobs for the lead

1. **Before the scorer commit:** decide K5V's minor findings (VERIFIED_WITH_MINOR, 10:58 UTC). Then merge K5F's 10
   files (or the fixed versions) by explicit path, re-hash Table D's RUN78 (`36a78632…`) and `pack_setup.py`
   (`40b99b1a…`) rows and the README:119/:125 cites, and update §1.2's counts if the suite changes (D5).
2. **The report paths.** Part 2 cites P2FV = BR `p2-full-verify.md` for D1-D11. This report now sits at that path.
   Copy the pass-1 report from `reports/p2-full-verify-scratch/pass2/p2-full-verify-pass1.md`
   (`edb0cead715d9149…`) into BR as `p2-full-verify.md`, and this report under another name (for example
   `p2-full-reverify.md`), then give it a short name in Part 2. Also copy `k5-fix.md`, `k5-verify.md` and `p2-full.md`
   (§14 item 2).
3. **Rule D1** before the first anchor pod: under the anchor stops, are L1, S3 and the classifier "not run" and P2,
   P5 "not tested" on that family, and what do block A's tables and money do?
4. Send D1-D9 to the writer (text-only fixes; D1 also gets an open item). Then run a short re-verify of the fixed file.
5. Rule D3's conflict (item 5's route) and D6 (one W1-18 pod or one per family), and the still-open items 9 (b),
   24 (c) and 31-35.
6. After review, delete `reports/p2-full-verify-scratch/pass2/` (404 KB; keep the pass-1 backup until job 2 is done).

## 7. Unresolved concerns

1. D1's gap is in SCOUT §8.5's example and in DESO item 7 too; the writer copied the ruling faithfully. The text fix
   is a stated fact (R) plus an open item. The scientific choice is the lead's.
2. I did not re-read the cites that did not change since pass 1. Their source files are unchanged at `5c0d091`, so
   P2FV's checks carry; I spot-checked RK, SR78 and RUN78 lines only.
3. I did not open the s-pool record to find "the list's own stage-1 rule" for a dropped prompt (DESO items 6, 17).
   D4 rests on the scripts' and settings' checks (R, M), not on that record.
4. §8.5's sums rest on SCOUT's E lines; I re-added them, I did not re-derive SCOUT's pod counts.
5. K5V's minor findings were not dispositioned at this writing; any change they force in K5F's files changes this text.
