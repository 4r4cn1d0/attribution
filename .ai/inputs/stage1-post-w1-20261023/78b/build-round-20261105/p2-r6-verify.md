# P2 round 6 re-verify (p2-r6-verify): adversarial check of Part 2 after the round-6 text fixes

Started 2026-11-07 12:35 UTC; this version 12:50 UTC (`date -u` before each write). Status: **DONE**.

**Verdict: DEFECTS (2 major, 5 minor, 3 nits; no blocker).** Every hash I re-computed at HEAD `197ea37` is right.
Every line cite I re-read says what the text says. DESO's rulings are written as ruled. P2FV2's D2-D9 are fixed as
proposed, and P2FV's D1-D11 are still in the text. But the D1 fix is incomplete (R1): an anchor stop also removes
S_78_F, so the a0-1101 retrain cannot run. That retrain is ruling 10's engine-Y certificate and Part 1 §2.3's check
that confirms the seven side units. The text and §14 item 36 do not list this. Second (R2): round 6's kit track (K6)
has already changed `pack_setup.py` and README.md and built the C0_SOURCE pack check. So the scorer section can be
committed only against a kit equal to `197ea37`'s. After K6's merge, the places in R2 must be re-taken first. So
"the scorer section and the draft can be committed now" does not hold yet.

- Target (read-only): `scratchpad/b78/ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`, SHA-256
  `dbce35baed4a3faa79674c9c029313db3182cc0c5bcd84d59b2acafe316d3bac`, 843 lines, 171,219 bytes (M #2; the same at
  the end, M #30; equal to the fixer's value).
- Tags: M measured (command number in section 8), R read (path:line), E estimate, I inference.
- No git state changed. No pod, spend, network, install, download, agent or message. I wrote only this report and
  `reports/p2-r6-verify-scratch/`. In the main checkout I only read (`git show`, `ls-tree`, `cat-file`, `grep`,
  `diff --name-only`, `rev-parse`, `status --short`). Engine X's identity was printed by a read-only `-B` import under
  the network-deny sandbox; no `__pycache__` was written (M #27). No forbidden folder, `selector.jsonl`, `hidden/`,
  judge, answer, generation, sample or prompt-text file was opened; the hash pool skips those names; from settings
  and records I printed keys, sizes and hash prefixes only. No secret read or written. The side paper is not mentioned.

## 0. Files changed
| File | Change |
|---|---|
| `reports/p2-r6-verify.md` | this report |
| `reports/p2-r6-verify-scratch/` | `vpool.py`, `vtok.py`, `vtables.py`, `rkprint.py` (my scripts); `pool-197ea37.tsv` (4,781 hash rows); `matched.tsv`, `unmatched.tsv`; `wsk3.sorted`, `head108.sorted`; `s14-now.md`; `rk.py`, `run78.py`, `sr78.py`, `rkimp/rules_78b.py` (`git show` copies, code only) |

## 1. Inputs read
- DES with DESO (R: DES:81-127), PP, RUL ruling 10 (RUL:132-141), ADD A2 and A13 (ADD:21-31, :102-108), P1
  (`b682513f…`, M #3) §0, §2.3, §3.7, §4, §10, §11.
- The fixer's report `reports/p2-r6-fix.md`; P2FV2 = BR `p2-full-verify.md` (`a7de7b7e…`, the same at HEAD and in
  scratch, M #1); P2FULL (`2ec25a65…`, its P2.2 table is the only list of P2FV's D1-D11 that still exists); K5V
  (`defae7a9…`); K6's report `reports/k6-fix.md` (files changed only).
- The fixer's `p2-r6-scratch/s14-old.md` and `part2-before-s14.md`. No copy of the `1975fee8…` text exists in the
  scratch tree or BR (M #4), so edits outside §14 were checked against the fixer's list and P2FV2's proposals.

## 2. D1-D11 closure

### 2.1 P2FV2's D1-D9 (BR `p2-full-verify.md` at `197ea37`)
| id | Status | Evidence |
|---|---|---|
| D1 | **partly fixed (R1)** | The dependency is stated in §1.5, §1.19, §2.2 (new bullet), §16.1 edit 2, §13 row 24, §14 items 7 and 36. Its R basis holds: RK `SC_KIND_PINS` :1186-1192 and `SC_AFTER` :1196-1197 (R, M #9), `score_l1_larf.py:8` (BANK's 64 harmful prompts), `score_s3_datarx.py:14` (REQ-3's anchor means), P1:181 (P2 and P5). But the retrain's loss is not drawn (R1). |
| D2 | fixed | §0 item 14 and §14 item 29 say "before block A" (R: DES:107-108). |
| D3 | fixed | §14's preamble quotes DES:84; items 1-5, 10, 12, 13, 19, 21, 29 are marked; item 5 states the conflict and picks no route. Nit R8. |
| D4 | fixed, but (a) is inaccurate (R3) | M #14: both derived untuned settings have `lists.s4.size` 512 and `s3` null; `make_untuned_answers.py:77-78` refuses another size (R). `score_s3_datarx.py:7-11` (R). |
| D5 | fixed | §14 item 2 and §1.2 carry K5V's verdict and counts (R: K5V:1-10) and the FOCUS entry (R, M #12). Nit R9. |
| D6 | fixed | §1.4 item 5 and §4.2 use DES E2's words (R: DES:16-18); no "the family's first O" phrase left outside item 37 (M #16). New item 37. |
| D7 | fixed | §1.18 item 15, §16.5 items 7-8; P1:33 holds "+6.33" and "S1 and S3 not shown, S4 holds" (R); scout-p2.md:624-626 holds the quote (R). |
| D8 | fixed | §0 item 3. |
| D9 | fixed | §4.3 lower case; §0 last paragraph. Nit R10. |

### 2.2 P2FV's D1-D11 (the first pass; the report itself is lost)
- P2FV is not in BR at `197ea37` and not in the scratch tree (M #4, #5; `git log --all` finds no such path). Its D-list
  survives only in P2FULL's P2.2 table (R: p2-full.md:46-60). Against that table, every fix is still in the text (R):
  D1 (§2.3, §0 intro, §14 item 22, end line); D2 (§4.3 table, $104.63 / $123.13); D3 (§8.5 sums); D4 (§4.6 table form);
  D5 (§3.1 PR4:479, :485; §12 `parity.sealed` 13); D6 (§3.2, §4.3, §15 item 6, §16.4: `ref_train` a new kind); D7
  (§9, §13 row 18, §16.3-§16.5); D8 (§13 row 13); D9 (§8.6, §14 item 31); D10 (§0 heading); D11 (§1.13, §4.2,
  §15 item 5, §14 item 32). M #15: RK `KINDS` still lacks `ref_train`, `transfer_report` and `w1_18`.
- The brief's "D1-D11" names P2FV's list; the fixer applied P2FV2's D1-D9 and kept P2FV's. I agree with that reading
  (I: FOCUS's 11:42 UTC entry says "passed its verifier with 11 minor text items", which is P2FV, R).

## 3. The 7 Nov rulings (DESO) written as ruled
Each DESO ruling against the text (R): items 6 and 17 (§1.4 item 1, §1.8, §0 item 14); 7 (§1.5, §16.1 edit 2); 8
(§1.12); 9 (§1.13, §4.2, §15 item 5; "under Branch 128" is in DESO's heading); 11 (§1.16); 14 (§1.5); 15 (§1.4); 16
(§1.3, §1.16); 18 (§1.14, §4.5); 20 (§1.9: "before block A", exact path and SHA-256, counts only, verdict unchanged);
22 (§2.3, §14 item 22, end line); 23 (§1.13, §15 item 12); 24 (a) (§4.3), (b) (§3.2, §4.3); 25 (§2.5); 26 (§6: 7 per
family, 3 + 3 + 1 and 4 + 2 + 1); 27 (§8.6); 28 (§16.2, §15 item 13); 30 (§9, §16.3, §16.4); the S4 boundary cases
(§5). All as ruled; no wording changes a ruling's substance. The §14 preamble's list of named items (6-9, 11, 14-18,
20, 22-28, 30) equals DESO's (R: DES:86-127).

## 4. Hashes re-computed at HEAD `197ea37` (no defect)
- M #6: my own pool, 4,781 SHA-256 values of the HEAD blobs in the cited folders (scripts, both kits, the engine,
  research, the 7-8B rulings and BR, the stage-1 commitments, SEAL, the anchor record, the `scale-78b-*` folders,
  briefs, RP, README); 341 skipped by name (hidden, selector, `.jsonl`, data files named for judges, answers,
  generations, samples or prompts). Spot checks equal `git show | shasum` (RK `68bf8f45…`, P1, DES `4c2b5cb2…`, ADD
  `ff349876…`, PP `336b3580…`).
- M #7: the text has 371 hex tokens (256 distinct). 213 match a pool file. 25 had no file name nearby; I read each:
  all right (short names ERR, PLAN, CHECK, P78, KCR, PR4, K5F, RK; the S1 verdict record; round 4's S1 script; config
  hashes that equal a file by coincidence; H1 files; the bank, r-draws and s-pool records).
- M #8: a path-aware check of Table A (44 rows + the 5 test files in prose), Table B (21), Table C (14), Table D (16
  path rows), §2.3 (20 R-edit cells by full path) and §16.3 (B16's 14 files): 134 good, 0 bad.
- M #10: the 108 files of `runkit/stage1-78b/` and `scripts/scale78b/` at `197ea37` equal `p2-full-scratch/wsk3.sha`
  byte for byte (`SAME108`).
- M #11: the 51 distinct tokens that match no file are record values or old hashes. 29 record values are each in
  committed files (`git grep -l` counts 4-198). The COMPLETE.json pins and training identities sit at RK:205-235. The
  commits resolve to the full ids given. Old hashes re-computed: DES at `e5a2f86` `72d57b20…`; `d203070`'s RK `57ad4148…`;
  `e5a2f86`'s `pack_setup.py` `f0f098f2…` and RUN78 `6144546a…`; PP at `65e218d` and `e5a2f86` `336b3580…`.
  `edb0cead…` (P2FV) is unverifiable, as the text says.
- M #13: `git diff --name-status 5c0d091 197ea37`: FOCUS and 10 kit files modified, 97 BR files; nothing else.
  `git diff --name-only d203070 197ea37` over Tables B-D's non-kit paths: empty.
- M #17: §4.2's `overrefusal_checks.py` `ed5fd2dc…` equals OXE's `cap.w1_18.module_sha256`; OXE `cap.branch` "128";
  OXE's PHTest record pin `a810574e…`; the record's `bank.full_file` `6487ed2b…`.
- M #18, #27: RK's values from a byte copy under the sandbox: §1.15's 10 kinds × 2 families (cap, guard, spend upper,
  E uppers 16,146 s and 16,692 s), §3.2's reference caps, `sc_seeds`, `pod_sizes(21)`, `pod_sizes(23)`, 13 idle pods at
  $4.33 per day, all six null pins, `STEPS`, `ENGINE_X`. All equal the text. `code_identity()` = `472fc7f6…`.

## 5. Line cites re-computed at HEAD `197ea37` (no defect found)
I re-read about 120 cites at `197ea37` (M #9, #19-#26). All say what the text says:
- RK :78, :81, :83, :103, :141, :153, :156-159, :313, :326-327, :373, :436, :477, :822-823, :864-957, :880-892,
  :1064-1068, :1072-1075, :1088-1091, :1148-1149, :1150-1159, :1163-1166, :1169-1185, :1186-1192, :1188, :1196-1197,
  :1220-1228, :1247.
- RUN78 :46, :228-231, :428-437, :514-541, :559-641, :599-604, :605-612, :616-626, :619, :706-827, :819-821 (no
  `--w1-18-record` or `--dev100-source`). SR78 :192, :199, :311, :334, :378-381, :383-384, :388, :397-405, :401,
  :494-498. PT78 :1310-1316. RULES-78B.md :41-42, :69-70, :90-92, :125-127, :159-161, :197-198. README :119, :125.
- WRAP :74, :79-89; MAKER :59-69; SC:55; the Llama H1 README :14-29.
- `score_l1_larf.py:1-23`; `score_s3_datarx.py:1-22`; `make_untuned_answers.py:77-78`, :82-93, :103-113, :141-151,
  :156, :171, :377-379; `representation_pass.py:337-348`; `make_anchor_answers.py:117-121`; `write_score_edit.py:23-26`,
  :93, :193; `s1common.py:590-592`; `oext_unit.py:6-20`; `oext_eval.py:246-248`; `oext_unit_y.py:3-5`, :86;
  `oext_unit.json:52-66`; `lean_eval_job.json:37-40`; `oext_eval.json:31`; `lean_eval_job.py:26-31`, :42, :50-54, :147,
  :603, :670-674; `verify.py:173-179`; `runner.py:669-675`; `stage3_pick.py:9-13`; `labels.py:97`, :110.
- The 1B kit runner :17-21, :36-38, :43-45, :49-53, :57-59, :71-78, :517, :770-776; its rules :600-602.
- PR4 :155-158, :428, :462-466, :479, :485, :488, :536, :541, :556, :561-562, :574, :589, :599, :731, :882. P1 :33,
  :91, :123, :142, :169, :181, :190, :198, :203, :244, :248, :292, :311, :316, :317, :320, :365. PP:78-80. DES:16-18,
  :84, :107-108. SCOUT :116-128, :622-627, :651-660.
- Not re-read: PLAN, KCR, RP, P78, EYD and FOCUS line cites other than the 11:42 UTC entry. These files are unchanged
  since `5c0d091` (M #13), and P2FV2 checked them.

## 6. No new decision, none dropped
- No new decision found in the round-6 edits. The new open items (2 (a), 2 (b), 36, 37) decide nothing. The re-take
  sentence (status line, §1.15, §1.17) is the lead's instruction in the round-6 brief, but the text cites no source for
  it (R7).
- No DES, DESO, PP, RUL or ADD ruling dropped. But some R bases that lived only in the old §14 are gone (R5).

## 7. Defects

| id | sev | where | defect | fix |
|---|---|---|---|---|
| R1 | **major** | §1.5 "What else needs the anchor file"; §1.19; §2.2; §16.1 edit 2; §13 row 24; §14 items 7, 36 | The D1 fix names L1, S3, the classifier, P2 and P5. It cites "the retrain only with `RECIPE_S`" but does not draw the result. With no anchor file there is no S_78_F, so the a0-1101 retrain cannot run. ADD A2 rejected a main-config certificate retrain (R: ADD:21-31). That retrain is three things: (1) ruling 10's engine-Y certificate (RUL:132-141; P1 §3.7). So ENGINE_Y's pack (PP18), KD9's Y re-measure, B+Qi on Y (§3.2) and the confirmation on Y (§9) have no ruled basis on that family. (2) Part 1 §2.3's "check that confirms" that the seven side units are main-study units (R: P1:103). Ruling 7's fallback fires only if block 0's environment check fails or the X retrain differs (R: P1:104), so with no retrain neither the check nor the fallback runs. (3) A1's states (already covered). Also, `rep_pass` serves DataShield-style and the Gate C reproduction (§1.6; PP3). | State the retrain dependency (R: RK `SC_KIND_PINS` `"retrain": ("RECIPE_S",)`; ADD A2; P1:103-104) beside the fallback lines. Widen §14 item 36 to cover ruling 10's certificate (Y, B+Qi, the confirmation, KD9), ruling 7's confirming check of the side units, and `rep_pass`'s other uses. The lead rules it before the first anchor pod. |
| R2 | **major (gates the commit)** | Table D `pack_setup.py` row; §8.3 and §8.6 README:119/:125; §1.2's counts; §1.13 "caught only on the pod"; §15 item 12; §16.4; §14 item 2 (a) | Right at `197ea37`, but round 6's kit track has already changed what these cite. K6 changes `pack_setup.py` (`40b99b1a…` to `e3651a98…`) and README.md (`d7ee370d…` to `8304db08…`; the cited lines move to :127 and :133). It adds tests and mutants, so 471 and 124/34/109/140 change. It builds DESO item 23's Mac-side C0_SOURCE check (M #28; R: k6-fix.md §1). RK, SR78, PT78 and RUN78 are unchanged (M #28). §14 item 2 (a) still calls this "may change (I)". | Choose the order. Either commit §1 before K6 is merged, at kit bytes equal to `197ea37`'s, or after K6's merge (and its re-verify) re-take Table D, the README cites, §1.2, §1.13, §15 item 12, §16.4 and §14 item 2 before the commit. The fixer's job 3 gives the commands. |
| R3 | minor | §14 item 33 (a) | It says a shorter S4 list "needs the settings re-derived by §1.16's fill steps". But MAKER does not take `lists.s4.size` from PINS. It keeps the 1B base file's 512 (R: MAKER:209-247; PINS `shared` has no S4 size, M #14). So a shorter list needs a MAKER code change: a new MAKER hash in Table A, and §1.16's "MAKER do not change" stops holding. It is more than a pin fill. | Say so in item 33 (a): MAKER's code and hash change too. |
| R4 | minor | §1.8 "Why the count runs first" (moved into the scorer section this round) | "In `rep_pass` ... a pool row that `encode_train` refuses is counted and skipped, not fatal." True for `rep_pass`. But `s3_score` then refuses if any S3-subset or S1 row has no `s3_safe` features (R: `score_s3_datarx.py:103-105`). So such a skip stops S3. DESO's count covers "every list prompt under that family's codec and main-recipe limits". The text does not say whether that includes `encode_train` of the `s3_safe` (prompt, response) pairs at `max_train_tokens`. | Add the `s3_score` refusal (R). Add to §14 item 33 (or a new item) whether the count covers the pairs' `encode_train`. |
| R5 | minor | §14 items 4, 7, 9 (a), 11, 30; §8.2 | R bases that lived only in the old §14 are gone, not moved: item 4's M (K4CV #6, 0 differ); item 7's I "low risk for the second (untuned U 11 and 32 of 600)"; item 9 (a)'s basis (`oext_unit.py:7-8`, :31-32; `lean_eval_job.py`'s W1-18 record under `oext_pinned`; LN-27's 1B option); item 11's basis (`write_score_edit.py:29-30`; ADD-4.8); item 30's list of lines adopted under the DES preamble (§8.3's price re-read and §16.5 item 2 are now untagged). §8.2 still points to "§14 item 30" for that list (M #29: none of these strings is in the text). | Move each basis into its section (§1.4/§1.19, §1.13, §1.16, §8.3, §16.5), or point §8.2 to `s14-old.md` item 30. |
| R6 | minor | §1 heading ("complete"); status line ("its rules fixed from that commit") | Open items still touch §1's rules: 36 (anchor stops), 33 (reduced lists), 5 (pin-fill route), 2 (a) (re-take record), 9 (b) (c0's state line). A ruling on any of them after the commit is a dated amendment. The heading hides this. (The fixer's concern 3.) | Write "complete except §14 items 2 (a), 5, 9 (b), 33, 36", or drop "complete". |
| R7 | minor | status line; §1.15; §1.17 | The rule "re-taken at the whole file's freeze and before the first scorer pod" cites only "(status line)". Its source is the lead's round-6 brief, which is not a committed ruling. | Cite the brief, or the lead records the rule (for example in the commit's FOCUS entry). |
| R8 | nit | §14 preamble | It says item 5 conflicts with DESO's sentence. Item 2 is also unnamed by DESO and is listed open. Its open parts are new round-6 gaps. | Say that item 2's open parts (a), (b) are new in round 6. |
| R9 | nit | §14 item 2 | "the pack's `data/` premise is not exact (R: K5V's header ...)". That finding is in K5V §2 R4 (R: k5-verify.md:109, :118), not the header. | Cite K5V §2 R4. |
| R10 | nit | §0 last paragraph | "`197ea37` adds kit files". It modifies 10 existing kit files and adds none (M #13). | "changes 10 kit files". |

## 8. Commands (all foreground, each under 1 min; exit status)
1. `date -u` (12:35, 12:49, 12:50); report skeleton; `ls` of the reports folder and BR; `git rev-parse HEAD`, `git log --oneline -5`; `shasum` of P2FV2 at BR, scratch and `git show HEAD:` (0).
2. `shasum`, `wc`, `grep -n '^#'` of the target (0).
3. `cat -n` DES; `cat -n` the fixer's report; `git show HEAD:P1 | shasum`, P1's short names and §0 (0).
4. `ls` of BR scratch folders; `find` for files named `*part2*` and `*pass1*` with their hashes (0); `grep -rl edb0cead` (0).
5. `git log --all` on P2FV's path; `git show <rev>:` of it at 3 commits (0); `git ls-tree` of BR's verifier scratch (0).
6. `vpool.py` (.venv `-I -B`, `caffeinate -i`): 5,122 blobs, 4,781 hashed, 341 skipped (0); spot `grep` and `git show | shasum` (0).
7. `vtok.py` (.venv `-I -B`): 371 tokens, 213 matched, 158 unmatched (51 distinct), 25 to check (0).
8. `vtables.py` (.venv `-I -B`): 134 good, 0 bad (0).
9. `git show HEAD:RK` to scratch; `sed` of 17 cited ranges; `grep -n` of definitions (0).
10. `sort`/`diff` of HEAD's 108 kit files against `wsk3.sha`: `SAME108` (0).
11. `git grep -l` of 29 record values at HEAD (0); `git rev-parse` of 5 commits; `git show <old rev>:<path> | shasum` for 6 old hashes; RK and RULES-78B record lines (0).
12. `git show HEAD:FOCUS | grep/sed` (the 11:42 UTC entry; the command printed more entries than needed, read as titles only) (0).
13. `git diff --name-only` / `--name-status` over 5c0d091..197ea37 and d203070..197ea37 (0).
14. .venv `-I -B`: the `lists` blocks of both derived and the 1B untuned settings; MAKER `grep`/`sed` :205-247; PINS `shared` keys (0).
15. (part of 18) RK `KINDS` membership (0).
16. `grep -n -o` for trigger wordings and `[to be entered]` (23 in all, 0 in §1) (0).
17. `grep` of the hash pool for 7 files; .venv `-I -B` of OXE's cap and bank pins and the bank record's keys and `full_file` hash (0).
18. `rkprint.py` (MAIN venv `-I -B`, sandbox-exec network deny) on a byte copy of RK (0); `find __pycache__` (none) (0).
19. `sed` of `score_l1_larf.py`:1-23 and `score_s3_datarx.py`:1-22 (0).
20. `sed` of `make_untuned_answers.py` :60-113, :139-172, :374-380 (0).
21. `sed` of RUN78's cited ranges (copy in scratch) (0).
22. `sed` of SR78's and PT78's cited ranges (0).
23. `sed` of the 1B kit runner and rules cites (0).
24. `sed` of the O-ext, lean job and settings cites (0).
25. `sed` of the scorer, engine and reader cites; RULES-78B, WRAP, MAKER, SC, the Llama H1 README (0).
26. `sed` of PR4, P1, PP, SCOUT cites; RUL:132-147; ADD:21-35, :102-108; P1:98-112, :163-175 (0).
27. MAIN venv `-B` import of `code_identity()` from the main checkout under sandbox-exec (0); `git status --short` count before and after (19 both); `find __pycache__ -newer` (none) (0).
28. `shasum` of 6 kit files in `ws-k4`; HEAD README:117-126; `grep -n` in K6's README; `sed` of `k6-fix.md`:1-60 and `k6-verify.md`:1-12 (0).
29. `grep -n -o` for the old §14 bases (no hit: rc 1, expected) and for scratch cites (0).
30. `sed` of `score_s3_datarx.py`:96-108; `git show` of MFIX's `after.sha` lines; `shasum` of the target (`dbce35ba…`); `date -u` (0).
31. `du -sh` of my scratch (1.0 MB); `find __pycache__` in my scratch and ws-p (none); final `shasum` of the target (`dbce35ba…`, unchanged); `git rev-parse HEAD` (`197ea375…`); `date -u` 12:52 (0).

## 9. Acceptance criteria
| Criterion | Result | Evidence |
|---|---|---|
| D1-D11 closed | **failed (major)** for P2FV2 D1 (R1); passed for P2FV2 D2-D9 and for P2FV's D1-D11 (from P2FULL's list) | §2 |
| The 7 Nov rulings written as ruled | passed | §3 |
| Every hash re-computed at HEAD `197ea37` | passed | §4 (M #6-#8, #10, #11, #17, #18, #27) |
| Every line cite re-computed at HEAD `197ea37` | passed for about 120 cites read; not tested for the PLAN, KCR, RP, P78, EYD and other FOCUS cites (files unchanged since `5c0d091`) | §5 |
| No new decision | passed (R7 is a missing source, not a new rule) | §6 |
| None dropped | passed for rulings; minor loss of R bases (R5) | §6, R5 |
| VERIFIED = "the scorer section and the draft can be committed now" | **not yet** | R1 (text plus an open item); R2 (order of the K6 merge and the commit) |
| Kit suites and guard mutants under sandbox | not tested | a text track; §1.2's counts are R (K5F, K5V, FOCUS) |

## 10. Jobs for the lead
1. Send R1 and R3-R10 to the text fixer. R1 is text plus a wider §14 item 36. Then rule item 36 (with the retrain,
   ruling 10's certificate and ruling 7's check) before the first anchor pod.
2. R2: choose the order. Either commit §1 before K6 is merged, at kit bytes equal to `197ea37`'s, or merge K6 after
   its re-verify (`reports/k6-verify.md` was IN PROGRESS at 12:36 UTC) and then re-take §1.2, §1.13, Table D's
   `pack_setup.py` row, the README cites (now :127 and :133 in K6's README), §15 item 12, §16.4 and §14 item 2. To
   re-check every hex value at the merged revision: `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B
   scratchpad/b78/reports/p2-r6-verify-scratch/vpool.py /Users/spiderishi/Coding/attribution <rev> <out.tsv>`, then
   `vtok.py <part2> <out.tsv> <dir>` and `vtables.py <part2> <out.tsv>`. Each runs in under 1 minute.
3. P2FV, the first pass, is lost: not in BR, not in scratch, not in git (M #4, #5). Record the loss (§14 item 2 (b)).
   Its D-list survives in P2FULL's P2.2 table (R: p2-full.md:46-60). P2FULL's own backups
   (`p2-full-scratch/rerun/`) are not in BR either (M #5).
4. Rule, or say they wait: items 2 (a), 5, 9 (b), 24 (c), 31-37.
5. After review, delete `reports/p2-r6-verify-scratch/` (1.0 MB, M #31: `du -sh`).

## 11. Unresolved concerns
1. I could not diff the round-6 edits outside §14 against the `1975fee8…` text, because no copy exists. I checked them
   against the fixer's list and P2FV2's proposals, and I read the whole file.
2. P2FV's own D1-D11 wording cannot be checked. Only P2FULL's summary of it exists.
3. R1 is a gap in Part 1's and DESO's scope too. DESO item 7 names A1 and P1 only, and P2FV2 D1 missed the retrain.
   The scientific choice is the lead's. The text only needs to state the fact and list the item.
4. R2 depends on K6's re-verify, which was still running when I read it. If K6 changes again, the re-take list changes.
5. I did not re-read the PLAN, KCR, RP, P78, EYD and older FOCUS cites. Their files are unchanged since `5c0d091`.
