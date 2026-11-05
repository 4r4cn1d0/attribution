# Fix D: the Part 1 text (7-8B preregistration), fix round

Status: DONE. Skeleton written 2026-11-05 14:48 UTC; this version 14:59 UTC (clock read with `date -u` at 14:46, 14:47, 14:58 and 14:59; M).

Worker: Track D fixer of the 7-8B $0 build round (one worktree, one file). Tags: M = measured (command given); R = read (path:line); E = estimate (basis given); I = inference.

Target (edited in place; untracked in ws-d): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-d/research/experiments/2026-11-05-78b-preregistration-part1.md
- Before: 440 lines, SHA-256 `ab98171e82cffbb42003124740c80fcd20355e9efd12ec3c13a9df38c0a5c248` (M; equals build-D's and verify-D's).
- After: 462 lines, SHA-256 `f864e9596b7927f8eb0b4441d69a4bacc10763ccdd9e9083c91442b414f1dc92` (M: `wc -l`, `shasum -a 256`, 14:58 UTC). Still DRAFT; the lead takes the final hash at the freeze.

Inputs read (main checkout, read-only, by absolute path): RUL and ADD in full; CHECK in full; PLAN headings and lines 290-300, 446-450; P78:127, :210-269, :272; PR4:297-304, :426-430; README:90-95; KCR:62, :183-188; FOCUS lines 75, 77, 87, 88, 95, 165 (titles, recorded times and the exact substrings D2 needed, extracted with Python; no answer or prompt text); `scripts/make_anchor_answers.py:1-3`; `experiments/safety_selection/jobs.py:175-181` (read only); `ls` of `.ai/inputs/stage1-post-w1-20261023/78b/`, `.ai/inputs/stage1-commitments-20261016/r-draws/edits/`, `.ai/inputs/gate-b-sealed-20261008/out/edits/` (names only); build-D.md, verify-D.md and verify-D-htable.py in full. No `tmp/` data folder, selector, hidden, judge, answer, generation, sample or prompt file opened. No engine file edited.

## 1. Files changed

1. `…/scratchpad/b78/ws-d/research/experiments/2026-11-05-78b-preregistration-part1.md` — edited (the only file in the worktree that differs from HEAD `fb51421`; M: `git status --short` prints one `??` line).
2. New: `…/scratchpad/b78/reports/fix-D-scratch/htable_fix.py` (the D1 recompute; prints only) and its output `…/fix-D-scratch/htable_fix_out.txt`.
3. This report.

No tracked file, engine file, frozen script, sealed file or runkit file touched. Nothing written in the main checkout. No git state changed anywhere (no add, commit, stash, checkout, reset, branch, worktree, push or pull was run). No pod, spend, network, install, download, agent or message.

## 2. Per defect and per addendum item: what changed and the evidence

### D1 (major): the H table (§7)

- **Recompute (M).** `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B …/fix-D-scratch/htable_fix.py` — exit 0; output saved. Step 1 reproduces every P78:228-232 row at R 8 / 12 / 16 (SE 3.15 / 2.57 / 2.23; MDE 11.0 / 8.3 / 7.2; every P(*better*) and P(*equivalent*) cell; the script asserts each printed value and prints "all rows reproduce: True"). Step 2, ruling 2's layout (R 7 / 10 / 13, methods 6 / 9 / 12): SE **3.24 / 2.68 / 2.33** pp, MDE **11.3 / 8.7 / 7.6** pp; the (a) and (c) 80% points 12.7 / 12.0; P(*better*) 0.43/0.67/0.86, 0.27/0.50/0.73, 0.72/0.91/0.98, 0.85/0.97/1.00, 0.20/0.50/0.80; P(*equivalent*) 0.00/0.00 (half-width 5.34), 0.85/0.46, 0.18/0.03, 0.38/0.05, 0.99/0.69. **ADD A7's values are confirmed**, and so is every cell verify-D proposed. The SE widening against P78 is 3.0 / 4.2 / 4.8% (M).
- **S-P multiples (M).** 1.42 / 1.08 / 0.93 × σ_pair at 6 / 9 / 12 shared seeds, unchanged by ruling 2's layout (they use the shared seeds only); plan A at σ_pair 4.0: MDE 5.7, P(equiv | 0) 0.84; at σ_pair 8.2: MDE 11.6. Printed beside the table in §7.
- **Text.** The five rows replaced (each now names its R and method cell counts); the basis line names the formula and the recompute; the sentence "the SE and MDE columns are P78's unpaired values and do not move" is gone (M: `grep -c "do not move"` = 0) and replaced by the recomputed-values paragraph with P78's old values for the record and ADD A7's "ruling 2 stands". §4's S-U line now says S-U at 7-8B uses the plan's R seeds (7 / 10 / 13) so its SE is §7's (verify-D's concern 4). §16 rows 35 and 36.

### D2 (blinding line, §0)

- Item 1: added the HarmBench sentence word per contrast, P3's L state *infeasible* and P2's *undetermined*, S4 against A1 seed-matched +7.08 pp (90% [+5.82, +8.34]), "S4 and A1 beat the adapter-scaling curve", no O or L node rejects and no coherence flag. Each substring verified in FOCUS line 95 ("THE STAGE-1 READING IS DONE", recorded 2026-11-01T21:38 UTC; M: Python substring extraction, printed with 90 characters of context each).
- Item 2: added the R-arm against a0 per-arm SDs 1.35 against 2.65 pp (R: P78:127, re-read) and Gate B's final unit reading behind the verdict (FOCUS "GATE B CLOSED", line 165, recorded 2026-10-23T05:26 UTC; R).
- Item 8 (new): stage 1b's construction checks (FOCUS line 87, "STAGE 1b'S CONSTRUCTION CHECKS OPENED AND PUBLISHED AFTER THE FINAL STOP", recorded 2026-11-02T03:25 UTC; R: the classifier "first in 100% of leaves at every menu"; DataShield-style, H1, H2a, H2b and L1 ranks read from the entry). "Use here: none; L1 and H1 stay primary (§13 item 2)."
- Item 4: the Llama G1 check's counts added (ADD A4), because the authors have now seen them. Item 7's "use here" points to the settled screen.

### D3-D9 (minor)

- **D3.** `PR4:427` → `PR4:428` in §13 item 5 (R: PR4:428 holds the LN-26 pick-rule text; M: `sed -n '426,430p'`).
- **D4.** §1 options cite → `README:93; P78:9; RP:71-79 via PLAN §5.1` (R: README:93 is the Options line, M: `sed -n '90,95p'`; PLAN:446-448 is §5.1 "Options B and C as RP:71-79", M). The two remaining `PLAN §1.1` cites (the $22.64 balance; NEXT row 6) are right and stay (verify-D §4.2 confirmed both).
- **D5.** §3.7: recipe S_78 = the main recipe with Gate B's recipe-S differences, now cited (R: PLAN T6, :297, re-read: "recipe S_78 = the main recipe with Gate B's recipe-S differences"; CHECK T6a's "differs only in recipe-S fields" test), plus ADD A1's `query_bank` basis (R: `scripts/make_anchor_answers.py:1-3` re-read, "runs on the pod, before recipe S exists"; `SS/jobs.py:175-181` re-read, the anchor-hash check).
- **D6.** §8 memory cell: "99.3% of the card, 204 allocator retries in the check (R: KCR:62)" against "lower: 8 key-value heads against OLMo-2-7B's 32, a KV cache about a quarter of OLMo's per token, 0 retries in its check (R: KCR:62)". KCR:62 re-read (M: `sed -n '62p'`): it states the 32 and 8 key-value heads, the 4× KV cache, the 204 retries and Llama's 0 retries, so the cell is R, not I.
- **D7.** §3.6 N2: "the lead's pooled point is about 4.5 pp (ruling 13; by §3.3's σ̂_pool form the two per-family values pool to about 3.2 pp, M …, so the point is the lead's judgement between that figure and the no-gain 8.2)". Script step 4: 4.41 and 0.73 pool to 3.16 (M). Ruling 13 is not amended by ADD, so the basis question is §17 item 2 for the lead.
- **D8.** §1 money table: the block A row, "$105-125 per four-pod launch" with CHECK C14's arithmetic ($83.70 / $98.50, × 1.25 = $104.62 / $123.12; M: script step 4).
- **D9.** §1, after the earmark: one "What still needs the user" list with C13's four items (the money; the HF token at each Llama launch; a yes by pod name before any delete, after a verified backup; H (a) or (c) only if the user wants them) and "everything else is reported, not asked".

### The addendum, A1-A12 (each cited by entry)

| Entry | Where it went | What it says there |
|---|---|---|
| A1 | §3.7 (new bullet "Recipe S_78"), §12, §14 item 1, §16 row 37 | route (A): the maker merged now; each family's S_78 written from its anchor file and committed by explicit path; `RECIPE_S` null until then; the kinds that need it refuse; the `query_bank` hash basis; (B) rejected |
| A2 | §3.7 (new first bullet "The order per family"), §3.2, §12, §16 row 38 | anchor job → S_78 → the Y retrain → the X retrain only if Y differs; no pod and no money added; the certificate-plus-second-retrain route rejected |
| A3 | §3.1 (new bullet "The sealed input folders"), §11 "what stays frozen", §16 row 39 | the three folders stay where built; the write-guard fix and the rebuild before the first commit; which R draws each layout uses (R_d1-5 SEAL, d6-10 stage 1, d11-13 at most from the new folder; M: `ls`, names only); none in the main checkout yet (M) |
| A4 | §15 (the G1 risk item, now with the result and the ruling), §0 item 4, §3.5, §14 item 7, §16 rows 34 and 40, §17 "closed" | a0-1101 passes (42 of 600); a0-1102 fails (63 of 600, 43 short, 20 of 557 = 3.6%, TOO CLOSE); OLMo 23 / 20 / 16 pass; 1B's G1 unchanged; report-only in N; PR4 §3.7's pooled bar in the main study; per-seed flags; no arm or seed dropped; pooled 105 of 1,200 (8.75%); the user is told before the freeze |
| A5 | §3.2 (new bullet "The constants' convention"), §12, §16 row 41 | the basis file's maxima govern; KCR's printed requirements round first; at most 1.2 s apart; caps, guards, spends identical to the cent (M: track A's test 1, via ADD) |
| A6 | §3.3 (new bullet), §3.4, §16 row 42 | one family's fallback: its three R-arm pair terms with the other family's three seed-matched terms in the pooled median; the SD term's form tagged I (P78:121 per family), since ADD A6 rules the median only |
| A7 | §7, §4, §16 rows 35-36 | the corrected S-U values; "ruling 2 stands"; the S-P multiples unchanged |
| A8 | §3.7 (bullet "The retrain pods"), §3.2, §1 money table, §12, §16 row 43, §17 "closed" | one single-job retrain pod per family: two under [B], F1's only under [C]; 4.5 h cap until measured ($17.91 need at 1.25×, M); each pod's need on its own line |
| A9 | §3.5 (new bullet "Judging for N"), §9, §14 item 6, §16 row 44, §17 "closed" | N's gate and the seed rule read the engine's U only; HarmBench judging of N's R arms report-only with block A's judge pods; Llama a0-1103 the same judge files on the same pods; no Granite for TC |
| A10 | status line, §14 heading, §16 row 45, §17 "closed" | Part 2's file name and its freeze form |
| A11 | §0 items 4 and 7, §3.5, §9, §14 item 7, §16 row 40, §17 "closed" | settled by A4 |
| A12 | §3.2 (new bullet "KD1's fallback"), §12, §16 row 46, §17 "closed" and item 1 | the trigger; does not fire if the fix round's re-check passes and T2 merges before 12 Nov; the merge commit in FOCUS |

Short names: **ADD** added with its SHA-256 `0372345853bb96a5…` (M: `shasum -a 256`, 14:50 UTC) and "governs over RUL where it says so". The nine source hashes re-checked unchanged at main HEAD `8d6b2e0` (M; the draft's hashes were taken at `ead1d7e`).

### §13, §16, §17

- **§13.** Item 10 added: the addendum's A1-A12, "none reads a 1B repair outcome"; which are build/process rulings (A1, A2, A3, A5, A8, A10, A12), the reader's form and arithmetic (A6, A7), judging (A9), and which read any outcome at all (A4, A11: the Llama G1 counts, a 7-8B a0 coherence count, not a stage-1 result; PR4 §3.7's bar itself was chosen at 1B after a θ0 count, PR4:298). Item 4 gains the fact that rulings 7, 8, 10 and 11 were recorded the same day and read files, fingerprints, caps and costs only, with the listing question left to the lead (§17 item 4). Item 5's cite fixed (D3).
- **§16.** Rows 35-48 added (M: 48 numbered rows): D1's values; S-U's seeds; A1, A2, A3, A4/A11, A5, A6, A8, A9, A10, A12; D2; D3-D9. Row 34 updated (the G1 check is done).
- **§17.** Rewritten. A "closed by ADD" paragraph maps each round-1 item to its entry (1 → A4; 3 → A8; 5 and 12 → A9; 9 → A10; 10 → A4/A11; 13's KD1 part → A12) and names the items dropped because they are pre-set rules or deferred work, not open rulings (4, 6, 7, 8, 11, 13's KD2 part). Still open, five items: (1) the reviewer's read and the freeze, with the lead's steps in order (tell the user the G1 result; confirm KD1 and KD2 did not fire; copy, commit by explicit path, hash into FOCUS after `date -u`, `commitments.py check`; merge the sealed folders and the S_78 maker by explicit path); (2) ruling 13's N2 basis (D7; not in ADD); (3) ruling 4's "if later" clause (verify-D concern 1; not in ADD); (4) ruling 16 item 4's list (verify-D concern 3; not in ADD); (5) one money basis at the freeze (verify-D concern 5; not in ADD). No new decision: each open item says what the lead may do, not what is done.

### What I did not change

- The S-P primary scale, the seed layouts, the run counts 44 / 53 / 68, the thresholds, H's chain, F1, TC's non-run, the dose arm's text, the predictions' numbers and the money totals: all as RUL; ADD amends none of them.
- Ruling 13's N2 basis text in RUL (the lead's; §17 item 2).
- Any sealed or prompt text: none reproduced.

## 3. Commands run (exit status; all in the foreground, each under a minute)

1. `date -u` (4×) — 0.
2. `ls -la` of the reports folder and `…/ws-d/research/experiments/`; `wc -l` of the six governing inputs — 0.
3. `mkdir -p …/reports/fix-D-scratch`; the report skeleton via `cat > … <<'EOF'` — 0.
4. Reads (Read tool): RUL, ADD, verify-D.md, verify-D-htable.py, build-D.md, CHECK in full; the draft in full (two pages); P78:210-269 — ok.
5. `sed -n` on PLAN:290-300 and `grep -n -E "^#{1,4} "` on PLAN (headings) — 0.
6. `sed -n '62p'` KCR; `sed -n '426,430p'` PR4; `sed -n '90,95p'` README; `sed -n '446,450p'` PLAN; `sed -n '127p;272p'` P78; `ls -la .ai/inputs/stage1-post-w1-20261023/78b/`; `shasum -a 256` of ADD and RUL; `git rev-parse --short HEAD` and `git branch --show-current` in the main checkout (read-only; `8d6b2e0`, `stageb-costs-and-recovery-safeguards-20261003`) — 0.
7. `grep -n -o -E` on FOCUS and `sed -n '95p' | grep -o` loops — the shell's `grep` is ugrep and **failed** on those patterns ("exceeds complexity limits"; exit non-zero for the inner greps; the loop itself exited 0). Redone in step 8.
8. `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B -` (heredoc): FOCUS entry titles by line (75, 77, 87, 88, 95, 165) and the D2 substrings with 90-120 characters of context — 0.
9. `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B …/fix-D-scratch/htable_fix.py | tee …/fix-D-scratch/htable_fix_out.txt` — 0; prints "RESULT: ALL REPRODUCE".
10. `shasum -a 256` of the eight other sources (all equal the draft's prefixes); `sed -n '183,188p'` KCR; `ls -la scripts/scale78b/` (absent in the main checkout), `ls -la scripts/make_anchor_answers.py` and `sed -n '1,3p'` of it; `grep -n -E "^### 3\.[678]"` PR4; `shasum -a 256` of the draft before edits (`ab98171e…`); `git status --short` and `git rev-parse --short HEAD` in ws-d (`?? …part1.md`; `fb51421`) — 0.
11. `sed -n '88p'` FOCUS (title only, cut to 260 characters); `sed -n '297,304p'` PR4; `ls` of the two R-draw edit folders (names only); `ls -d .ai/inputs/scale-78b-*` — **exit 1** (zsh "no matches found": the folders are not in the main checkout; the expected result); `sed -n '175,181p' experiments/safety_selection/jobs.py` — 0.
12. 30 Edit calls on the draft (Edit tool) — all ok.
13. Post-edit checks: `grep -c -F` for 15 stale strings (all 0 except the two correct `PLAN §1.1` cites and one `§13 item 5)` cross-reference); `grep -n -o` of `§17` references and `ADD A<n>` counts; `grep -n -E "^## "` (18 headings in order); `grep -c -E "^\| [0-9]+ \| "` (48 rows); `wc -l`; `shasum -a 256`; `git status --short`; `git rev-parse --short HEAD` in ws-d — 0.
14. `sed -n` eyeball of §3.7 and §7 after the edits — 0.

Not run: any test suite, mutation set, `commitments.py check` (the lead's freeze step; it needs the commit), any engine code. No background job.

## 4. Acceptance criteria

| # | Criterion (the brief's) | Result | Evidence |
|---|---|---|---|
| 1 | D1: SE and MDE recomputed at ruling 2's counts with P78's formula; P78's rows reproduced first; A7's values confirmed or corrected; S-P multiples printed; "do not move" removed | passed | §2 D1; `htable_fix.py` (M); `grep -c "do not move"` = 0 (M) |
| 2 | D2: the blinding line's missing items | passed | §0 items 1, 2, 8; every value verified in FOCUS lines 95, 165, 87 (M) |
| 3 | D3, D4: citations | passed | PR4:428, README:93, PLAN §5.1 re-read (M) |
| 4 | D5: recipe S_78's source | passed | PLAN:297 re-read; CHECK T6a; ADD A1 (R) |
| 5 | D6: the Llama memory cell's cite | passed | KCR:62 re-read; cell is R (M) |
| 6 | D7: N2's basis wording | passed | §3.6; 3.16 pooled (M); the ruling's basis left to the lead (§17 item 2) |
| 7 | D8: C14's block-A need $105-125 | passed | §1 table row; $104.62 / $123.12 (M) |
| 8 | D9: one "what still needs the user" list per C13 | passed | §1 after the earmark; four items as RUL header and CHECK C13 |
| 9 | A1-A12 placed where they belong, cited by section | passed | §2 table above; `grep -o "ADD A[0-9]+"` finds A1-A10 and A12 by entry, A11 in "A4, A11" / "A4 and A11" (M) |
| 10 | §13 updated: which addendum items are choices after a stage-1 result and which are not | passed | §13 item 10; item 4's parenthetical |
| 11 | §16 change log updated | passed | rows 35-48 (M: 48 rows) |
| 12 | §17 lists only what is still open after ADD, at least the reviewer's read and the freeze; old items closed with their entry | passed | §17 "Closed by ADD" + five open items |
| 13 | No new decisions; gaps that need a ruling listed in §17 | passed (I) | §17 items 2-5 name the lead's options and decide none; §3.3's one inference (the SD term under A6) is tagged I |
| 14 | Text kept DRAFT | passed | status line |
| 15 | Tag style kept (R path:line, M, E, I); plain short sentences | passed (I) | every new number carries M, R or E; sentences short |
| 16 | No sealed or prompt text reproduced; no side-paper mention | passed | `grep -c` for "side paper|side project|side-project" = 0 (M); only counts and aggregates quoted |
| 17 | Only the worktree file and my report/scratch written; no tracked, engine, frozen, sealed or runkit file; no git state change | passed | `git status --short` in ws-d: one `??` line (M); no git write command run (§3) |
| 18 | No pod, spend, network, install, download, agent, message; no forbidden file opened | passed | §3; the inputs list above |
| 19 | Report skeleton first, updated as work went | passed | §3 item 3, then this version |
| 20 | Every command in the foreground under 10 minutes; no background wait | passed | §3 (each under a minute) |
| 21 | The file's SHA-256 in FOCUS; `commitments.py check` after the commit | not tested | the lead's freeze step |
| 22 | The reviewer's read against §0 and §13 | not tested | the pre-freeze reviewer; the round's re-verify |

## 5. Jobs for the lead

1. **Re-verify** this text (the round's re-verify step), then merge by explicit path: copy `…/ws-d/research/experiments/2026-11-05-78b-preregistration-part1.md` to the main checkout's `research/experiments/2026-11-05-78b-preregistration-part1.md`. Any lead edit changes the hash; take the final hash at the freeze.
2. **Decide §17 items 2-5** or leave them as open items in the frozen text (each gates nothing): ruling 13's N2 basis (3.2 against 4.5); ruling 4's "if later" clause; whether ruling 16 lists rulings 7, 8, 10, 11 and A1-A12; one money basis for §5.
3. **Before the freeze** (§17 item 1): tell the user the G1 result if not yet done; confirm KD1 (ADD A12) and KD2 did not fire; merge the three sealed folders (ADD A3, after track B's write-guard fix and rebuild) and `scripts/scale78b/make_recipe_s78.py` (ADD A1) by explicit path; then the freeze steps of ruling 14. The text's status line and §17 item 1 list the order.
4. **Records:** this report, `fix-D-scratch/htable_fix.py` and its output go under `.ai/inputs/stage1-post-w1-20261023/78b/` with the other round records (ruling 14, M5), if the lead keeps the round's reports there.
5. No background job is needed for this track.

## 6. Unresolved concerns

1. **A6's SD term.** ADD A6 rules how the pooled *median* mixes when one family's trigger fires; it does not say how σ̂_pool's SD part mixes. §3.3 states the median as ruled and tags the SD part I (P78:121 replaces each r term per family). If the noise reader does something else, the text follows the reader after the lead says so.
2. **The G1 record's path.** ADD A4 cites `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json`; it is not in the main checkout at HEAD `8d6b2e0` (M: `ls`), so it is track C's file awaiting the merge. §0 item 4 and §15 say so and quote ADD's counts, not the file.
3. **The sealed folders' names** are cited from ADD A3; none exists in the main checkout yet (M). If track B's rebuild renames a folder, §3.1 and §11 change.
4. **§13 item 10's classification** of A4 and A11 ("read a 7-8B a0 coherence count, not a repair outcome") is my reading of ADD's header ("no stage-1 outcome was read for them") and of what the G1 check reads. The reviewer should confirm the wording.
5. **D7 stays the lead's.** §3.6 now says the 4.5 pp point is the lead's judgement; if the lead amends ruling 13's basis instead, §3.6 should quote the amended basis and drop the "judgement" clause.
6. **Verify-D's §17-closure claims rest on ADD alone.** I closed the round-1 items by the addendum's entries and dropped six as pre-set rules or deferred work (§17's first paragraph names them); the lead may want any of those six back in the list.
7. **I did not re-read** EYD, RP, PLAN-S, NEXT, S1L or KCR beyond lines 62 and 183-188; figures from them are cited through RUL, ADD, P78, PLAN and CHECK, as in round 1.
