# Round 6: Part 2 text fixes (p2-r6-fix)

Started 2026-11-07 11:43 UTC; this version 11:58 UTC (`date -u` before each write). Status: **DONE**.

Tags: M measured (command number in section 6), R read (path:line), E estimate, I inference.
Target: `scratchpad/b78/ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`.
Before: SHA-256 `1975fee806a2477b…`, 830 lines (M #2). After: `dbce35baed4a3faa79674c9c029313db3182cc0c5bcd84d59b2acafe316d3bac`, 843 lines, 171,219 bytes (M #24).
No git state changed. No pod, spend, network, install, download, agent or message. In the main checkout I only read
(`git show`, `git diff --name-only`, `git ls-tree`, `git grep`, `git rev-parse`, `grep`, `sed`). No forbidden folder,
selector, hidden, judge, answer, generation, sample or prompt-text file was opened; the hash pool skips those names.
No secret read or written. The side paper is not mentioned.

## 0. One discrepancy in the brief (read first)
- The brief says "Fix p2-full-verify.md D1-D11". The file at that path at HEAD (`a7de7b7e…`, M #3) is the verifier's
  **second pass**, with **D1-D9** only (1 major, 6 minor, 2 nits; R: its §3). The first pass (D1-D11, `edb0cead…`)
  was already applied by the 7 Nov revision (R: P2FV2 §2.4: "P2FV D1-D11: each is applied"). I applied D1-D9.
- The first-pass report is no longer anywhere I can see: not in BR at `197ea37`, and its backup path
  `reports/p2-full-verify-scratch/pass2/p2-full-verify-pass1.md` holds no file (M #8). Part 2 and DESO cite it
  ("the verifier's D1, D7 (b), D11"). I named it P2FV (with its hash) and the second pass P2FV2, and put the gap in
  §14 item 2 (b).
- FOCUS's 11:42 UTC entry says Part 2 "passed its verifier with 11 minor text items" (R). That matches the first pass's
  D1-D11, not the second pass's D1-D9.

## 1. Files changed
| File | Change |
|---|---|
| `ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md` | items 1-4 below |
| `reports/p2-r6-fix.md` | this report |
| `reports/p2-r6-scratch/` (616 KB) | `pool.py`, `pool-197ea37.tsv` (1,827 hash rows), `tokens.py`, `tokens-after.txt`, `tok-after.txt`, `flag-after.txt`, `unm-after.txt`, `head108.sha`, `run78-197ea37.py` and `mua.py` (`git show` copies, code only), `s14-old.md`, `s14-new.md`, `part2-before-s14.md` (the text before §14's splice, `dd8b0239…`) |

I did not keep a copy of the 1975fee8 text before my first edit. `s14-old.md` holds the old §14 in full; the other
changes are listed below.

## 2. Item 1: P2FV2 D1-D9 (each as P2FV2 proposes)
| id | Fix in the text | Evidence |
|---|---|---|
| D1 (major) | §1.5: new sentence "What else needs the anchor file (R; P2FV2 D1)", which states the dependency: RK `SC_KIND_PINS` :1186-1192, `SC_AFTER` :1196-1197, `score_l1_larf.py:8`, `score_s3_datarx.py:14`, P1:181 for P2 and P5. The same pointer is in §1.19, §2.2 (a new bullet), §16.1 edit 2, §13 row 24 and §14 item 7. New open item §14 item 36, with P2FV2's ask that the lead rule it before the first anchor pod | R: RK:1186-1197 at 197ea37 (M #11); score_l1_larf.py:8, score_s3_datarx.py:9, :14 (M #12); P1:181 (M #10) |
| D2 | §0 item 14 and §14 item 29 now say "and, before block A, the OLMo-2-7B S1 re-check (DESO item 20)" | R: DES:107-108 |
| D3 | §14 preamble quotes DESO's sentence (R: DES:84) and marks the unnamed items 1-5, 10, 12, 13, 19, 21, 29 by it. Item 5 states the conflict and asks the lead which route; it does not pick one | R: DES:84 |
| D4 | §14 item 33 adds (a) `lists.s4.size` = 512 in both derived untuned settings, and the 1B code's size refusal at `make_untuned_answers.py:77-78`; (b) `s3_score` needs the `s3_safe` hash that s-pool record `bcca59ac…` names (`score_s3_datarx.py:7-11`) | M #12, #13 (`s4` 512, `s3` null in both files) |
| D5 | §14 item 2 rewritten: K5V's verdict and findings (R: K5V header), the merge at 197ea37 (M), round 6's possible kit changes, and the re-take rule; §1.2 adds K5V's and the lead's counts | R: k5-verify.md:1-12; FOCUS 2026-11-07T11:42 UTC |
| D6 | §4.2 and §1.4 item 5 use DES E2's words ("per family, as the first O job"; "not built before the first O-ext pod"). New open item §14 item 37: one W1-18 pod or one per family, and OLMo-only under [C] | R: DES:16-18; scout-p2.md:118-119, :127 (M #14) |
| D7 | §1.18 item 15 (new) labels DESO item 7; §16.5 items 7 and 8 (new) label DESO items 7 and 28 in ruling 16's form ("chosen after the stage-1 reading; the trigger reads ... only; the authors knew ..."); §16.2 and §16.1 point to them | R: P1:33 (M #10); scout-p2.md:624-626 (M #14) |
| D8 | §0 item 3 lists K5V and notes that the 7 Nov author read it while it was partial | R: P2FV2 D8 |
| D9 | §4.3: "; the 7-8B references" (lower case). §0 last paragraph: "HEAD `5c0d091` changes only DES and adds no file" | text |

## 3. Item 2: DESO's rulings in their sections; §14 closed down
- Each DESO ruling was already written into its section by the 7 Nov revision (R: P2FV2 §2.4). I re-read each
  place: items 6 and 17 (§1.8), 7 (§1.5, §16.1), 8 (§1.12), 9 (§1.13, §4.2), 11 (§1.16), 14 (§1.5), 15 (§1.4),
  16 (§1.3), 18 (§1.14, §4.5), 20 (§1.9), 22 (§2.3, end line), 23 (§1.13, §15 item 12), 24 (§3.2, §4.3), 25 (§2.5),
  26 (§6), 27 (§8.6), 28 (§16.2), 30 (§9, §16.3, §16.4), the S4 boundary cases (§5). All present.
- Facts that lived only in §14 moved to their sections: item 6's R basis ("why the count runs first") to §1.8 (cites
  re-read at 197ea37, M #15); item 16's K4CV-concern-2 note to §1.3; item 18's J2-list note to §1.14. §1.10's
  "(§14 item 6)" now points to §1.8; §4.4's "(§14 item 1)" to §1.14 and §15 item 5.
- §14 keeps every number (so cites stay valid). Each closed item is one line naming where its ruling or record now
  is. Items 22 and 29 keep their lists, because the status line and §3.2, §4.2, §4.4, §9 point to them.
- **Still open (as §14's preamble says): items 2, 5, 9 (b), 24 (c) and 31-37.** 36 and 37 are new (D1, D6).

## 4. Item 3: hashes and line cites re-taken at HEAD 197ea37
- M #4: HEAD = `197ea375bf86e13145b3bacd3619f8fcd29d2d58`. `git diff --name-only 5c0d091 197ea37`: FOCUS, the 10 kit
  files K5F changed, and BR files only (108 paths in all).
- M #6: all 108 files of `runkit/stage1-78b/` and `scripts/scale78b/` at 197ea37 equal K5W's list
  `p2-full-scratch/wsk3.sha` byte for byte; `git ls-tree` lists the same 108 paths. So RUN78 `36a78632…`,
  `pack_setup.py` `40b99b1a…`, RK `68bf8f45…`, SR78, PT78, the README (`d7ee370d…`) and Table A's 49 files are
  unchanged against the text. K5F's merge is exact.
- M #9, #16: a pool of SHA-256 values of 1,827 HEAD blobs in the cited folders. The edited text has 277 hex tokens;
  201 match a file. The nearest-file-name check flags 26; I read each: all right (short names P1, ERR, PLAN, CHECK,
  PR4, K5F, P2FULL, RK; record files; settings files named after their script; historical copies of old hashes in BR
  scratch). The 76 that match no file are record values or old hashes: each is present at HEAD by `git grep` (M #17)
  or was computed (M #5, #7: the four commit ids; DES at e5a2f86 `72d57b20…` and HEAD `4c2b5cb2…`; d203070's RK
  `57ad4148…`; e5a2f86's `pack_setup.py` `f0f098f2…` and RUN78 `6144546a…`; P78 `e6a73c92…`; KCR `9884bd17…`;
  SEAL's R_d1 `f7d7eb86…`, R_d4 `5cf35162…`, R_d5 `73d336cc…`, MANIFEST `d76d8bf9…`). Two are new and match no file
  by design: `197ea375…` (the commit) and `edb0cead…` (P2FV, not found; §0 above).
- M #18: engine X identity printed at HEAD under the network-deny sandbox: `472fc7f6…`, equal to RK's `ENGINE_X`;
  RK's four null pins print None; `e_pod("olmo2-7b", "untuned_answers")` = 6.0 h, $17.10, $9.46 (as §1.15).
- Line cites: RK, SR78, RUN78, PT78 and the README are the bytes P2FV2 checked (M #6). I spot-checked RUN78 :46,
  :228-231, :428-437, :514-541, :559, :599-626, :641 and README :119, :125 at HEAD (M #19): they say what the text
  cites. Every other cited file is unchanged since 5c0d091 (M #4).
- Text changes: §1.17 has a new "Re-taken at 197ea37" paragraph and the sentence "These hashes are re-taken again
  against the merged files at the whole file's freeze and before the first scorer pod"; Tables A-D, §2.3, §4.2, §7,
  §9, §16.3, §1.15, §1.16 name 197ea37; the short names RK/RUN78, HEAD, K5W, the reports, P2FV/P2FV2 are updated.

## 5. Item 4: status line
- It now reads: the scorer section (§1) "is committed now, before any 7-8B scorer output exists (A10); its rules are
  fixed from that commit"; the code hashes "are re-taken against the merged files at the whole file's freeze and before
  the first scorer pod; how a hash that then differs is recorded is §14 item 2"; "The whole file is frozen before block
  A's first pod" and the rest as before. §1's heading and the end line say the same. No other change of substance.
- The "how a differing hash is recorded" question is new in §14 item 2 (a); the text does not settle it.

## 6. Commands (all foreground, each under 2 min; exit status)
1. `date -u` (11:43, 11:49, 11:54, 11:57); report skeleton; `ls` of workspace and BR; `git log -3`, `git status --short` (0).
2. `wc -l`, `shasum` of the target (`1975fee8…`); the same for a main-checkout copy: exit 1 (no such file; expected) (1).
3. `cat` of P2FV2; `shasum` of BR and scratch copies (both `a7de7b7e…`) and of K5F, K5V, P2FULL (0).
4. `git rev-parse HEAD`; `git show --stat 197ea37`; `git diff --name-only 5c0d091 197ea37` (0).
5. `git show HEAD:<kit file> | shasum` for 8 kit files (0).
6. Loop over the 108 rows of `wsk3.sha` against `git show HEAD:`; `diff` (SAME108); `git ls-tree` count and `comm` (0).
7. `git rev-parse` of 4 commits; DES at e5a2f86 and HEAD, d203070's RK, e5a2f86's `pack_setup.py` and RUN78; P78, KCR (0).
8. `find` for the pass-1 report in the round's scratch and BR; `git log --all` on its path (0).
9. `pool.py` (.venv `-I -B`, `caffeinate -i`): 1,827 rows, 20 skipped by name (0).
10. P1: `shasum` (`b682513f…`), `grep` of the contrast lines, `sed -n 30,36p` (0).
11. `sed -n 1160,1200p` RK (0).
12. `sed`/`grep -n` of `score_s3_datarx.py`, `score_l1_larf.py`, `make_untuned_answers.py` (0).
13. .venv `-I -B`: the `lists` sizes of both derived untuned settings (0).
14. `git show HEAD:scout-p2.md | sed` (lines 116-128, 620-628) (0).
15. `sed` of `make_untuned_answers.py` :103-113, :156, :377-379 and `representation_pass.py` :337-348 at HEAD (0).
16. `tokens.py` on the target (272 tokens, before edits) and on the edited text (277) (0).
17. `git grep -l` at HEAD for 29 record values; `git show` of SEAL's 4 files with `shasum` (0).
18. `sandbox-exec` network-deny, main venv `-B`, PYTHONDONTWRITEBYTECODE=1: `code_identity()` and RK pins (0); `find __pycache__` newer than my files: none (0).
19. `git show HEAD:README.md | sed` (:119, :125); RUN78 copy and `sed` of cited lines (0).
20. One zsh `echo =====` in a compound command failed ("not found"; exit 1); re-run without it (0).
21. FOCUS `grep` and `git show 197ea37 -- research/FOCUS.md` (0).
22. Edits by the Edit tool (24) and three .venv `-I -B` exact-replace scripts (each asserts one match) (0).
23. The §14 splice: .venv `-I -B` script (asserts one `## 14.` and one `## 15.` heading) (0).
24. Final `shasum`, `wc`, `grep -c`; `find -newer` in ws-p (only the target); `git status --short` of the main checkout (same as at the start) (0).

## 7. Acceptance criteria
| Criterion | Result | Evidence |
|---|---|---|
| P2FV2's defects fixed as it proposes | passed (D1-D9) | §2. The brief's "D1-D11" is the first pass, already applied (§0) |
| DESO's rulings in the sections they belong to | passed | §3; all were present; three facts moved from §14 |
| §14 keeps only what is open; ruled items closed | passed | §3; open: 2, 5, 9 (b), 24 (c), 31-37; closed items are one-line records, numbers kept |
| Every kit and script hash re-taken against HEAD 197ea37 | passed | §4, M #6, #9, #16, #17 |
| Every line cite re-taken | passed for the kit (same bytes, M #6, spot checks M #19) and the moved cites (M #11, #12, #15); the unchanged non-kit files carry P2FV2's checks | §4 |
| Statement that code hashes are re-taken at the freeze and before the first scorer pod, and that the scorer rules are fixed now | passed | status line, §1.17, end line |
| Status line unchanged in substance | passed | §5 |
| No new decision; gaps go to §14 | passed | new items 36, 37 and 2 (a), (b); item 5's conflict stated, not resolved |
| Kit suites and guard mutants | not tested | a text track; §1.2 cites K5F, K5V and the lead's FOCUS counts (R) |

## 8. Jobs for the lead
1. **P2FV, the first-pass report** (`edb0cead715d9149…`, D1-D11): find a copy and put it in BR under another name,
   or record that it is lost (§14 item 2 (b)). Part 2 and DESO cite it.
2. **Rule before the scorer commit, or say they wait:** item 36 (the anchor stops' reach to L1, S3, the classifier,
   P2, P5; P2FV2 asks for it before the first anchor pod), item 5 (which route for pin fills; the conflict with DESO's
   sentence), item 2 (a) (how a differing re-taken hash is recorded), item 37 (one W1-18 pod or per family). Still
   open from before: 9 (b), 24 (c), 31-35.
3. If round 6's kit track changes any kit file before the scorer commit: re-hash Table D's kit rows, the RUN78 and
   README cites and §1.2's counts (the command: for each of the 108 paths, `git show <rev>:<path> | shasum -a 256`,
   compared with `p2-full-scratch/wsk3.sha`; `scratchpad/b78/reports/p2-r6-scratch/pool.py <rev> <out>` then
   `tokens.py <part2> <out>` re-checks every hex value; each runs under 2 min).
4. A short re-verify of this revision (diff against `reports/p2-r6-scratch/part2-before-s14.md` and `s14-old.md`).
5. After review, delete `reports/p2-r6-scratch/` (616 KB).

## 9. Unresolved concerns
1. I applied D1-D9, not "D1-D11" (§0). If the lead meant another list, it is not in BR.
2. I kept no copy of the 1975fee8 text; a reviewer diffs against `part2-before-s14.md` (after the edits outside §14)
   and `s14-old.md` (the old §14), or against the lead's own copy.
3. §1's heading still says "complete" while item 36 (about §1's anchor fallback) is open. The rules and code of §1 are
   complete; item 36 is about what is stated on a stop. The lead may want item 36 ruled before the scorer commit.
4. Line cites of non-kit files that did not change since 5c0d091 rest on P2FV2's checks; I re-read only those I moved
   or added.
5. "DES's header covers DESO" (item 35) is still the text's inference.
