# Track D re-verify and pre-freeze review (fix round)

Status: DONE. Started 2026-11-05 15:02:58 UTC; this version 15:14:36 UTC (M: `date -u` at both).
Role: adversarial re-verifier and the reviewer's read ruling 14 requires before the freeze (PLAN T1's decisive check).
File under review (read-only; not edited): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-d/research/experiments/2026-11-05-78b-preregistration-part1.md
Lines 462; SHA-256 `f864e9596b7927f8eb0b4441d69a4bacc10763ccdd9e9083c91442b414f1dc92` at 15:02 and again at 15:14 UTC (M: `wc -l`, `shasum -a 256`; equals the fixer's). ws-d `git status --short` prints one `??` line, this file, at HEAD `fb51421` (M). Main checkout HEAD `8d6b2e0`, branch `stageb-costs-and-recovery-safeguards-20261003` (M, read-only).
Tags: M = measured (command given); R = read (path:line); E = estimate; I = inference.

## Verdict: VERIFIED_WITH_MINOR

Ready to freeze after the five one-line fixes in §10 (RV1-RV5). D1-D9 are closed. Every number I could re-derive reproduces. Every citation I read is right except the MONEY hash prefix (RV1) and the Llama sealed set's contents (RV2). No new decision; one ruling clause dropped (RV5). The blinding line is complete against FOCUS lines 95, 165, 88, 87 and the P78 values it names. §13's labels hold. §17 lists only open items.

## 1. Files changed by me

- This report.
- /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/reverify-D-scratch/numbers.py and `numbers_out.txt` (the independent recompute; prints only).
- /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/reverify-D-scratch/focus_check.py and `focus_check_out.txt` (substring checks on FOCUS; counts and labels only).

No other file written. The draft, the fixer's files, the main checkout and git state are untouched. No pod, spend, network, install, download, agent or message. No forbidden folder or file opened (no `tmp/` data folder, selector, hidden, judge, answer, generation, sample or prompt file).

## 2. Defects D1..D9: closed or not

| Id | Closed | My evidence |
|---|---|---|
| D1 H table | yes | `numbers.py` (M): P78's five rows reproduce first (SE 3.15 / 2.57 / 2.23; MDE 11.0 / 8.3 / 7.2; every P(*better*) and P(*equivalent*) cell of P78:228-232); ruling 2's rows give SE 3.24 / 2.68 / 2.33, MDE 11.3 / 8.7 / 7.6, 80% points 12.7 / 12.0, P(*better*) 0.43/0.67/0.86, 0.27/0.50/0.73, 0.72/0.91/0.98, 0.85/0.97/1.00, 0.20/0.50/0.80, P(*equivalent*) 0.00/0.00 (hw 5.34), 0.85/0.46, 0.18/0.03, 0.38/0.05, 0.99/0.69: every cell of the draft's table (lines 256-260) equals mine. Widening 3.0 / 4.2 / 4.8% (M). S-P multiples 1.42 / 1.08 / 0.93 (M). "do not move" gone (the fixer's grep; I re-read §7). ADD A7's values confirmed. One leftover: the text at line 266 still says "48% of the time (R: P78:237)" while the table's (a) row says 0.46 (RV3). |
| D2 blinding line | yes | `focus_check.py` (M): every value of §0 item 1 is in FOCUS line 95 (recorded 2026-11-01T21:38 UTC): +6.33, +2.03, −0.28, −2.31, +0.11, +18.28, 15.97, 8.89, 0.8/13.0/12.4/3.0, "S1 not shown, S3 not shown, S4 holds", LN-14, P6 then P1, +30.1, the Words line (headline, U part, HarmBench sentence, S-G coherent headline), infeasible/undetermined, +7.08 [+5.82, +8.34], "beat the adapter-scaling curve", "no O or L node rejects", "no coherence flag", F_k, S-a shift, cost table. Item 2: line 165 holds the verdict, "rankings" and the time 2026-10-23T05:26 UTC; its values are cited to P78:127-128, :133-134, :140, :448 and all are there (R). Item 3: line 88, +3.94, "5 pp FLOOR", 2026-11-02T03:25 UTC. Item 8: line 87, classifier first at every menu; DataShield-style, H1, H2a, H2b, L1 with other ranks; 2026-11-02T03:25 UTC. Items 4-7 against P78:50-60, :224, :272, :314, README:82, DOSE `integrity[1]`, RUL ruling 12, PR4:298 (R). |
| D3 PR4:428 | yes | PR4:428 holds LN-26's pick rule (R, `sed -n '426,430p'`). |
| D4 README:93, PLAN §5.1 | yes | README:93 is the Options line (R); PLAN:446-449 is §5.1 "Options B and C as RP:71-79" (R). |
| D5 S_78's source | yes | PLAN:297 "(recipe S_78 = the main recipe with Gate B's recipe-S differences" (R); CHECK track list item 4 (T6a) (R); `scripts/make_anchor_answers.py:1-2` "runs on the pod, before recipe S exists" and `experiments/safety_selection/jobs.py:175-181` the `anchors-<sha>` check (R, read only). |
| D6 Llama memory cell | yes | KCR:62 (R): 32 against 8 key-value heads, 4× KV cache, 204 retries, Llama 0 retries. The cell is R. |
| D7 N2 wording | yes | 4.41 and 0.73 pool to 3.16 by √[(a² + b²)/2] (M); 5.83 → 4.04; no gain 8.24 (M). The draft calls 4.5 "the lead's pooled point" and leaves the basis to the lead (§17 item 2). No new decision. |
| D8 block A row | yes | $83.70 × 1.25 = 104.625; $98.50 × 1.25 = 123.125 (M). The row says $104.62 / $123.12 (half-even); see concern 1. |
| D9 one C13 list | yes | §1 after the earmark; four items equal RUL:19-21 and CHECK C13 (R). |

## 3. Numbers re-derived (all M, `numbers.py`; `numbers_out.txt` holds the printout)

- Seed counts: plan A 36 + 7 + 7 = 50 cells, 44 new beyond N (block A 21, block B 23); B9 42 + 10 + 7 = 59, 53 new (21 + 32); H(b) 54 + 13 + 7 = 74, 68 new (21 + 47). Equal to RUL ruling 2 and the draft's §5 table and §7 column.
- Caps and N's need: 8.5 h + 12.5 h = 21 h; $6 + 21 × $1.85 = $44.85; × 1.25 = $56.06 (KCR:177 R; draft §3.2).
- Retrain pod: $6 + 1.85 × 4.5 = $14.33; × 1.25 = $17.91 (draft §1). At 4-5 h $16.75-19.06 (CHECK M3's "$15-20").
- Block A launch: $104.62 / $123.12 at half-even rounding of 104.625 / 123.125 (draft §1; CHECK C14 "$105-125").
- Dose arm: $21.18 / $42.36 (OLMo), $28.26 / $56.52 (Llama); both $49.44 / $98.88 (draft "$49 to $99; $21 / $42, $28 / $57").
- Keep rate 57/64 = 0.891; 192/0.89 = 216 (draft §10). Steps 4,848 → 38, 4,896 → 39, 4,992 → 39 (draft §10).
- Money sums: plan A + confirmation $780-1,130; B9 + confirmation $850-1,220; H(b) + confirmation $970-1,370 (draft's "$780-1,220" spans plan A low to B9 high, as CHECK C3 wrote it); B9 over plan A $70-90; H(b) over plan A $190-240 (P78:203).
- Thresholds: paired MDE 6.39 (plan A at σ̂ 4.5) and 6.47 (B9 at 6.0); rescaled 4.22 / 5.56; review ceiling binds at σ_pair > 10.7 ((b), SESOI 5) to 21.4 ((c), SESOI 10) (draft §6.1 "10.7-21"). Plan A at σ_pair 4.0: MDE 5.68, P(equivalent | 0) 0.84; at 8.2: 11.6. 3-seed paired SE 2.31 at σ_pair 4.
- N1: E/8 = 5.51 (OLMo) and 6.66 (Llama) (draft "5.5 / 6.7"). N2: 0.49 × √2 × 6.36 = 4.41, × 1.06 = 0.73, × 5.83 = 4.04, no gain 8.24. The ruling 13 and dose-prediction numbers (+2.5; −1.5 to +6.5; 4.5; 2.5-8.5; 0.5/0.3/0.2; +5; −1 to +12; +2.5; −2.5 to +8; +1 to +6; 0.6; 0.2 / 0.3) each appear in the draft and in RUL (M: string counts).
- G1 counts: 42 + 63 = 105 of 1,200 = 8.75%; 63/600 = 10.5%; 600 − 43 = 557; 20/557 = 3.6% (ADD A4; draft §0, §15).
- Units: U shares 1.83 / 51.50 / 39.00 / 47.33 / 5.33 / 57.83 / 59.33%; E +49.67 / +37.17 / +45.50 / +52.50 / +54.00; means 44.1 / 53.25; F = (6.36/1.06)² = 36.0 (draft §2.1, §8).
- √2 × 3.20 = 4.53 (draft §4).

## 4. Citations checked by reading the cited line (R)

- P78 in full (lines 1-478): every P78 citation in the draft that I traced is right, including :9, :13, :21, :23, :48-62, :66-68, :72-82, :92-100, :108-112, :116-122, :126-129, :133-134, :140, :150-154, :159-160, :168, :175-177, :186-195 (the §6.3 table equals P78's cell for cell, the 15-df row too), :199-204, :216, :218, :224-245, :249-295, :310-325, :333-337, :345, :355, :357, :367, :377-379, :407, :413, :421-430, :448.
- PR4:124-125, :131, :133, :161, :228-240 (floors U and O 0.01 pp², L 10⁻⁸ nats² at :235; "Reference and secondary arms never enter this fit" at :234; "Seeds without a partner" at :240), :281, :296-299, :426-430; the section numbers §0.5, §1.2, §2.1, §3.2, §3.4, §3.6, §3.7, §4.7, §4.8, §5.3 exist (M: `grep -n`).
- KCR:62, :125, :161, :177, :183-188, :191. README:82, :86, :90-95, :120. RP:43, :71-79, :91, :136-138, :146. EYD:81. S1B:121 (m). PLAN:16, :80 ($22.64), :297, :446-449, §4, §5.0, §5.9, §5.11, §6 risks 2, 6, 12 (PLAN read in full). CHECK in full. RUL and ADD in full.
- `scripts/make_anchor_answers.py:1-18`, `experiments/safety_selection/jobs.py:175-181` (read only).
- DOSE and MONEY in full: every field the draft names (`user_words`, `answered_utc`, `what_it_is`, `why`, `integrity`, `seeds`, `limits`, `pre_set_fallbacks[0..1]`, `question`, `lead_reading[0..2]`) says what the draft says.
- Hashes (M, `shasum -a 256`): RUL `65e477b0ac1e772c`, ADD `0372345853bb96a5`, PLAN `f39238d352ca3922`, CHECK `1bc40aa4c842ff9b`, P78 `e6a73c92ef97e107`, PR4 `7eccf9e9bed1e733`, DOSE `65745ad15d5cf28b`, README `6dfe1447fb9a4919`, FOCUS `113a9275aca22b4a`, BLD `80cb8944` all equal the draft's prefixes. **MONEY does not:** the file is `53945ecbf623864f…`; the draft (line 20) says `53945ecbf6238648…` (RV1). Round 1's verifier checked 8 characters (verify-D.md:24 "53945ecb"); build-D.md:54 has the full correct hash, so the error is a transcription in the draft.
- Folders (M, `ls`, names only): `.ai/inputs/stage1-commitments-20261016/r-draws/edits/` holds `R_d6` to `R_d10` (the draft's "R_d6-R_d10 are stage 1's" holds); SEAL `out/edits/` holds `R_d1-R_d5`, 8 `unit_g-*` and 16 `M_g-*` files; no `.ai/inputs/scale-78b-*` and no `scripts/scale78b/` in the main checkout (as the draft says); no 78b file under `research/experiments/` yet.
- Verbatim strings (M, Python compare after whitespace folding): ruling 12's label and KD4's reason string are in the draft byte for byte.

## 5. Rulings and the addendum

Rulings 1-14 and 16: each present with its basis and fallback, as round 1's table (verify-D §4.1) found; I re-read each against RUL and the draft's §1-§13 and found no departure except RV5 (KD5's third clause). Ruling 15 (the build process) is rightly absent. ADD A1-A12: each placed where the fixer's table says (M: A1 31 mentions, A2 9, A3 7, A4 15, A5 5, A6 5, A7 7, A8 9, A9 6, A10 6, A11 8, A12 9), and the text at each place says what ADD says. A3 is the one place the draft adds a claim ADD does not make (RV2).

**No new decision.** Every conditional in §1, §3.4, §3.7, §6, §7, §8, §10, §17 reads money, a fingerprint, a cap, a blinding test or N's σ̂. §17 items 2-5 name options and decide none. The one inference in §3.3 (the SD term under A6) matches what track C's reader does: "each family's governing reading enters the pool" (verify-C.md:307-309; build-C.md:165-168, R), so it is right as well as tagged.

## 6. Blinding line against FOCUS

See §2 D2. Items 1-8 are each in their named source. Form: S1B:121 (m)'s, with "no 7-8B repair arm has run; no Llama-3.2-1B repair arm has run" (RUL:11) in the first sentence. The "not seen" paragraph is right: no 7-8B R, method, reference or dose value exists; no Llama a0-1103 value; no σ̂ of N. One loose word: item 2 says Gate B's final unit reading had "rankings and labels"; FOCUS line 165 says "rankings …, verdict …" (concern 2).

## 7. §13 labels and §17 open items

- §13: items 1-9 equal RUL ruling 16's nine. Item 10's classification is right: A1, A2, A3, A5, A8, A10, A12 read files, hashes, pods, caps and costs; A6 and A7 are the reader's form and arithmetic; A9 places judging; A4 and A11 read the Llama G1 counts, a coherence count on 7-8B a0 units that existed before the stage-1 reading, and PR4 §3.7's bar, chosen at 1B after a θ0 count (PR4:298, R). None reads a 1B repair outcome. Item 4's parenthetical states a fact and leaves the listing to the lead.
- §17: "Closed by ADD" maps items 1, 3, 5, 9, 10, 12, 13 (KD1) to A4, A8, A9, A10, A4/A11, A12, each of which I confirmed in ADD. The six dropped items are pre-set rules or deferred work, as the paragraph says. Items 1-5 are open in RUL and ADD. One item the list could carry: S1 on the Llama manifest is not built (track B's stop rule; verify-B.md:100, :138, R); it is a block-A input. I fold it into RV2 rather than add a §17 item.

## 8. Commands run (exit status; all foreground, each under a minute)

1. `date -u` (2×) — 0.
2. `mkdir -p …/reverify-D-scratch`; `ls -la …/reports/`; `wc -l` and `shasum -a 256` of the draft (2×) — 0.
3. Read tool: RUL, ADD, CHECK, PLAN (two pages), the draft (two pages), fix-D.md, verify-D.md, P78 (two pages) — ok.
4. `git rev-parse --short HEAD`, `git branch --show-current` (main checkout, read-only); `git status --short`, `git rev-parse --short HEAD` (ws-d, 2×); `shasum -a 256` of ten sources; `ls -la .ai/inputs/stage1-post-w1-20261023/78b/`; `ls` of the stage-1 r-draws folder and SEAL `out/edits/`; `ls -d .ai/inputs/scale-78b-*` — zsh "no matches found" (exit 1 inside the chain; the expected result); `ls scripts/scale78b` — "No such file" (expected); `ls research/experiments/ | grep -i 78b` — nothing (expected) — chain 0.
5. `sed -n` of KCR:62, :125, :161, :177, :183-188, :191; PR4:124-125, :131-133, :161, :228-240, :281, :296-299, :426-430; `grep -n` of PR4 headings; README:82-95, :120; RP:43, :71-79, :91, :136-138, :146; EYD:81; S1B:121; `scripts/make_anchor_answers.py:1-18`; `experiments/safety_selection/jobs.py:175-181`; PLAN:297; greps for short names in P78 and the draft — 0.
6. `cat` of DOSE and MONEY — 0.
7. `shasum -a 256` of MONEY (full); greps for the hash in the draft, P78, build-D, verify-D; `sed -n '121p'` S1B with `grep -o "(m)…"`; `ls` of CALC; greps for "idle storage" in the draft and for H1/S1 in build-B.md — 0.
8. `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B …/reverify-D-scratch/numbers.py | tee numbers_out.txt` — 0.
9. `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B …/reverify-D-scratch/focus_check.py | tee focus_check_out.txt` — 0.
10. `.venv/bin/python -I -B -` (heredoc; verbatim compares, counts, hash prefixes) — first run **exit 1** (an f-string SyntaxError in my script, no output); redone without the backslash — 0.
11. greps in fix-BC.md, verify-B.md, build-C.md, verify-C.md; `sed -n` of fix-BC.md:55-80, verify-C.md:303-312, build-C.md:160-170 — 0.

Not run: any test suite, mutation set, `commitments.py check` (the lead's freeze step), engine code. No background job.

## 9. Acceptance criteria (the brief's)

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | D1-D9 closed | passed | §2 |
| 2 | Every number re-derived: the H table; 44 / 53 / 68; caps 8.5 h and 12.5 h; $56.06; money lines; N1 / N2 / AD predictions equal ruling 13 | passed | §3 (M) |
| 3 | Every citation checked by reading path:line | passed, with two wrong facts found | §4; RV1 (the MONEY prefix), RV2 (the sealed set's contents and its "ruling 14" cite) |
| 4 | The text matches RUL and ADD exactly; no new decision; none dropped | passed except one dropped clause | §5; RV5 (KD5's idle-storage line) |
| 5 | The blinding line complete against FOCUS and the records it names (counts and labels only) | passed | §6 (M: `focus_check.py`) |
| 6 | §13's labels right | passed | §7 |
| 7 | §17 lists only what is still open | passed | §7 |
| 8 | Report skeleton first, updated as work went; only my report and scratch written; no git state change; no pod, spend, network, install, download, agent, message; no forbidden file opened | passed | §1, §8 |
| 9 | The file's SHA-256 in FOCUS; `commitments.py check` after the commit | not tested | the lead's freeze step; the hash changes with RV1-RV5 |

## 10. Defects found (all minor; each a one-line fix; the lead takes the final hash after them)

**RV1 (minor; a wrong pinned hash; Short names, line 20).** Replace `53945ecbf6238648…` with `53945ecbf623864f…` (M: `shasum -a 256` of MONEY = `53945ecbf623864f7f930c241dbb28062f5d69c846f0078d58c8a22f614d35c0`). Failure if frozen as is: the pre-registration's pin for the user's money answer does not match the file.

**RV2 (minor; the Llama sealed set's contents contradict ADD A3 and what track B built; §3.1 line 121, §14 items 1 and 12, lines 360 and 371).**
- Line 121: replace `the Llama sealed set `.ai/inputs/scale-78b-sealed-llama3-20261105/` (R, the unit files, H1 and S1 by manifest; ruling 14)` with `the Llama sealed set `.ai/inputs/scale-78b-sealed-llama3-20261105/` (R_d1-R_d16 and the 8 unit files by manifest; ruling 14)`. Basis: ADD A3 puts Llama's H1 in `.ai/inputs/scale-78b-length-rules-llama3-20261105/` (R: ADD:35-37; build-B.md:28-31); ruling 14 names only R and the unit files (R: RUL:234-236); S1 on the Llama manifest was not built (R: build-B.md:8, :127; verify-B.md:100, :138: it needs the sealed list's text and the Llama codec, a lead job).
- Line 371 (§14 item 12): replace `(R, the unit files, H1, S1) shared with stage 2` with `(R, the unit files) shared with stage 2; H1 in its own sealed folder (ADD A3); S1 on the Llama manifest still to be built before block A (track B's stop rule: it needs the sealed list's text and the Llama codec)`.
- Line 360 (§14 item 1): replace `the S-pool, S1, S3 and S4 from the family's own untuned answers` with `the S-pool and S1 (the same 48 S-pool rows, re-bound to the family manifest; CHECK C6); S3 and S4 from the family's own untuned answers`. Basis: CHECK C6 (R: CHECK:90-96); P78:377 says "S4 from the family's own untuned answers".
Failure if frozen as is: the frozen text names a sealed input file that does not exist in the folder it names, and cites ruling 14 for it.

**RV3 (minor; internal inconsistency left by D1; §7, line 266).** Replace `a true 5 pp effect reads *equivalent* 48% of the time (R: P78:237)` with `a true 5 pp effect reads *equivalent* 46% of the time at ruling 2's layout (the table above; P78:237 gave 48% at R 8)`. Basis: the table's (a) row says 0.46 (M: `numbers.py`); P78:237's 48% is at SE 3.15.

**RV4 (minor; undefined short names; Short names).** The draft uses PRE (lines 325, 385), PLAN-S (288, 314), S1L (315), F L78 (328) and NEXT (350) without defining them. Add one bullet after the PR4 line: `- **PRE**, **PLAN-S**, **S1L** and **F L*n*** are P78's short names (P78:13): the frozen Gate B pre-registration, the sharpened-direction draft, S1B's lead-decisions addendum, and a FOCUS line at P78's hash. **NEXT** is PLAN's (PLAN:16): `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md`.` (M: `grep -o`; R: P78:13, PLAN:16.)

**RV5 (minor; a ruling clause dropped; §12, line 337).** KD5 has three parts (R: RUL:164-166): 50 GB volumes with a free-space check; the state rule; "an idle-storage line in each block's need". The draft has the first two and not the third (M: `grep -c "each block's need"` = 0). After `the kit has no delete command; KD5)` insert `; an idle-storage line in each block's need (KD5; about $0.33 per day per stopped 50 GB pod, KCR:161)`.

## 11. Jobs for the lead

1. Apply RV1-RV5 (five edits; no number or decision changes), re-hash, then merge by explicit path to `research/experiments/2026-11-05-78b-preregistration-part1.md`. Add a §16 row 49 for them if the change log is to stay complete ("the re-verifier's RV1-RV5").
2. Before the freeze, the steps §17 item 1 lists (tell the user the G1 result; confirm KD1 and KD2 did not fire; merge the three sealed folders after track B's write-guard fix and `scripts/scale78b/make_recipe_s78.py` by explicit path; commit by explicit path; `date -u`; SHA-256 into FOCUS; `scripts/stage1/commitments.py check`), by about 19 Nov.
3. Decide or leave open §17 items 2-5 (ruling 13's N2 basis: 3.2 against 4.5 by §3.3's form, M; ruling 4's "if later" clause; ruling 16's list; one money basis). Each gates nothing.
4. S1 on the Llama manifest (RV2): a lead job before block A (verify-B.md:138). Decide where its record goes (the Llama sealed set or its own folder) before Part 2 names the file.
5. Records: this report and `reverify-D-scratch/` go with the round's records under `.ai/inputs/stage1-post-w1-20261023/78b/` if the lead keeps them there (ruling 14, M5). No background job is needed for this track.

## 12. Unresolved concerns

1. **Half-cent rounding (§1 block A row).** 104.625 and 123.125 are exactly at the half cent; the draft's $104.62 / $123.12 is half-even, half-up gives $104.63 / $123.13, and the kit's own `cents` helper may round up. The row's "about $105-125" is what matters; the lead may prefer "$104.6 / $123.1" to avoid the question. Not a defect.
2. **§0 item 2's "rankings and labels".** FOCUS line 165 records Gate B's final reading as "rankings …, verdict …". "labels" is the draft's word for the unit labels inside the sealed rankings file. Harmless; "rankings and verdict" would quote the entry.
3. **The G1 record and the three sealed folders are not in the main checkout** at HEAD `8d6b2e0` (M). The draft quotes ADD's counts and names, not the files, and says so. If track B's rebuild renames a folder, §3.1 and §11 change.
4. **The re-verify cannot prove the fixer opened no forbidden file.** fix-D.md's command list (§3) names none; the draft reproduces no prompt, answer or sealed text (I re-read every section).
5. **Not re-read by me:** PLAN-S, S1L, PRE, NEXT, RP beyond the lines in §4, KCR beyond the lines in §4, CALC's outputs (the §6.3 table was checked against P78:186-195, which cites CALC), EYD beyond :81. Figures from them reach the draft through P78, PLAN, CHECK, RUL and ADD, and those citations I did read.
6. **ADD A6's SD term** is now confirmed against track C's reader (verify-C.md:307-309), so the I tag in §3.3 could become R once track C's report is a record; the lead's call.
