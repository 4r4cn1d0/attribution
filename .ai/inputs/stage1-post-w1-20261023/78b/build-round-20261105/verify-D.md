# Verify D: adversarial check of the Part 1 draft (7-8B preregistration)

Status: DONE. Verdict: **DEFECTS** (one major, several minor). Skeleton written 2026-11-05 13:49 UTC; this version 14:00 UTC (clock read with `date -u` at 13:49 and 13:59; M).

Verifier role: find defects, not approve. Tags: M = measured (command given); R = read (path:line); E = estimate; I = inference.

Target (439 lines; SHA-256 `ab98171e82cffbb42003124740c80fcd20355e9efd12ec3c13a9df38c0a5c248`, M, equals the builder's): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-d/research/experiments/2026-11-05-78b-preregistration-part1.md
Builder report: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/build-D.md

## 1. Files changed (all new, all mine)

- This report.
- /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/verify-D-htable.py (the H-table recompute; read-only, prints only).

No builder file edited. No file written in any worktree or in the main checkout. No git state changed. No pod, spend, network, install, download, agent or message. No `tmp/` data folder, selector, hidden, judge, answer, generation, sample or prompt file opened.

## 2. Sources read (absolute paths, main checkout; all read-only)

- RUL `/Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md` in full (SHA-256 `65e477b0…`, M; equals the draft's and FOCUS L75's).
- CHECK `/Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/78b/readiness-20261105/78b-readiness-check.md` in full (`1bc40aa4…`, M).
- PLAN `/Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/78b/readiness-20261105/78b-readiness.md` lines 68-95, 114-139, 343-587 (`f39238d3…`, M).
- P78 `/Users/spiderishi/Coding/attribution/research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md` in full (`e6a73c92…`, M).
- PR4 `/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` lines 120-135, 159-163, 226-242, 279-283, 296-299, 425-430 (`7eccf9e9…`, M).
- DOSE and MONEY (`.../reading/user_yes_s4_dose_arm_20261101.json` `65745ad1…`; `.../reading/user_answer_78b_money_20261101.json` `53945ecb…`; M) in full.
- README `/Users/spiderishi/Coding/attribution/README.md` lines 78-125 (`6dfe1447…`, M).
- FOCUS `/Users/spiderishi/Coding/attribution/research/FOCUS.md` (`113a9275…`, M): entries L75, L77, L87, L88, L90 (head), L95, L165 in full; the heads of L74-L96.
- S1B `/Users/spiderishi/Coding/attribution/.ai/briefs/stage1-commitments-build-20261016.md`:121.
- KCR `/Users/spiderishi/Coding/attribution/research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md`:62, :161, :177, :183-188; grep for "S_78".
- The draft and the builder report in full.

Every SHA-256 the draft's "Short names" gives for RUL, PLAN, CHECK, P78, PR4, DOSE, MONEY, README and FOCUS reproduces (M: `shasum -a 256`). Main checkout HEAD `ead1d7e`, branch `stageb-costs-and-recovery-safeguards-20261003` (M), as the draft says. The worktree ws-d shows only `?? research/experiments/2026-11-05-78b-preregistration-part1.md` at HEAD `fb51421` (M).

## 3. Commands run (exit status)

1. `date -u` (3×) — 0.
2. `ls -la` of the scratchpad folders; `ls` of the 78b input folders — 0.
3. `wc -l` and `shasum -a 256` of the nine sources and the draft — 0.
4. `sed -n` reads of PR4, README, KCR, S1B, FOCUS (by line); `grep -n` on FOCUS for the entry titles and `65e477b0`; `grep -n -E "^#{1,4} "` on PLAN — 0.
5. `grep -n -E "^## "` on the draft (18 headings in order, M); `grep -n -i -E "side paper|side project|side-project"` on the draft — exit 1 (no match, as expected); misc greps (`Wednesday|Thursday|95-115|105-125|needs the user|prints nothing|recipe S_78`) — 0.
6. `git -C <ws-d> status --short`, `git -C <ws-d> rev-parse --short HEAD`, `git -C /Users/spiderishi/Coding/attribution rev-parse --short HEAD`, `git -C ... branch --show-current` (read-only) — 0.
7. `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B -` (heredoc) recompute of the H table, N2 pooling, dose cost, N need, keep rate, step counts, thresholds — 0.
8. `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B .../reports/verify-D-htable.py` — 0.

No test suite, no mutation run, no engine code touched. Nothing ran longer than a few seconds.

## 4. Checks

### 4.1 Rulings 1-16: faithful, with basis and fallback (R: RUL against the draft)

| Ruling | Where in the draft | Faithful | Basis | Fallback | Note |
|---|---|---|---|---|---|
| 1 S | §4 | yes | yes (PR4:233-240, P78:140, :153-154, :160 all re-read and right) | "none needed", as RUL | PR4 line numbers for Model/Fit/floors/seed/prompt/df/partner = 233/234/235/236/237/238/240 (M: `sed`), all right |
| 2 layout | §5 | yes | yes (PR4:240, :124) | "none; the counts only fall" | run counts re-added, right (§4.6) |
| 3 SR, thresholds, ceiling, SR under [C], SR-2 | §6.1-6.4 | yes | yes | SR-2's trigger and "N decides alone" as RUL | 6.39/6.47 and 4.22/5.56 reproduce (M) |
| 4 H | §7 | yes ((e), (b) first; chain (i) C on F1 at (b), (ii) (d) review; (a)/(c) the user's) | yes (P78:237, :241, :243) | yes | the table's SE/MDE claim is wrong: defect D1 |
| 5 F | §8 | yes | yes (P78:310-325; KCR:62, :183-188) | F2 after two memory failures, as RUL | one untagged inference: D6 |
| 6 TC | §9 | yes | yes (README:94 verified, FOCUS L165) | — | the rule's compact record matches P78:251-295 |
| 7 reuse | §2.3 | yes | yes | yes (+3 runs, $9-12, P78:333) | |
| 8 Llama 1103 | §3.1 | yes | yes (P78:60, :100) | — | |
| 9 gate, earmark | §1 | yes | yes | the 1 Dec re-check, as RUL | |
| 10 engine | §3.7 | yes (Y first; X retrain the pre-set second job; only X mismatch triggers) | yes (C4) | yes | "recipe S_78 = …" lacks its source: D5 |
| 11 kit, KD1-KD11, N's layout | §3.2, §11 EM-2, §12 | yes (KD4 reason string verbatim; KD7; KD2 with C11; KD6; KD10 with C1's kinds; M3) | yes | KD1's and KD2's triggers as RUL | |
| 12 dose arm | §10, §11 EM-4 | yes; label verbatim (M: string compare by eye against RUL:209-211); names, AD1/AD2, construction, keep count, fallback, seeds, reading (outside Φ, Holm, HB-C), compute, cost, placement all as RUL | yes | DOSE's two fallbacks as RUL | |
| 13 predictions | §3.6, §10 | yes, every number equals RUL | as RUL | — | RUL's own N2 basis does not reproduce: D7 (the lead's) |
| 14 freeze | status line, §17 items 1-2 | yes | — | — | |
| 15 build round | not in the draft (process, not design) | n/a | | | right to omit |
| 16 labelled list | §13 | nine items, each equals RUL's | | | completeness note in §8 (concern 3) |

Nothing in the draft decides what the rulings leave open: the three tempting places (retrain pod count, where N's R arms are judged, Granite after TC) are §17 items 3, 5 and §9's consequence sentence, and §17 item 6 keeps the dose arm's seed count for the gate (R: the draft §17).

### 4.2 Numbers and citations against sources

Re-read and right (R, each by its line): every P78 citation in §0-§17 that I checked (about 120 of them: 9, 13, 21, 23, 48-62, 66-68, 72-82, 92-100, 108-112, 116-122, 126-129, 133-134, 140, 150-154, 159-160, 168, 175-177, 186-195, 199-204, 216, 218, 224-234, 237-245, 249-295, 310-325, 333-337, 345, 357, 367, 377-379, 407, 413, 421-430); PR4:124, :125, :131, :133, :161, :228, :229, :230, :233-240, :281, :298; README:82, :86, :90-95, :120; KCR:62, :161, :177, :183-188; S1B:121 (m); FOCUS L75, L77, L88, L95, L165 titles and recorded times; DOSE and MONEY fields (`user_words`, `answered_utc` 2026-11-01T09:16:02Z and "about 23:05 UTC", `what_it_is`, `lead_reading[0..2]`, `integrity`, `pre_set_fallbacks`, `limits`); PLAN §1.1 (the $22.64 balance, NEXT row 6), §1.2, §4, §5.0, §5.9, §6 risks 2, 6, 12.

Arithmetic re-done (M, the heredoc and `verify-D-htable.py`): N's guard $6 + 21 × $1.85 = $44.85, × 1.25 = $56.06; dose cost 6 × $3.53 = $21.18, 12 × = $42.36, 6 × $4.71 = $28.26, 12 × = $56.52, both families $49.44 / $98.88; keep rate 57/64 = 89.1%, 192/0.891 = 216; steps 4,848 → 38, 4,896 → 39, 4,992 → 39 at 128 rows per step; paired MDEs at the thresholds 6.39 / 6.47 and the rescaled 4.22 / 5.56; √2 × 3.20 = 4.53; the 3-seed paired SE 2.31 at σ_pair 4; plan A at σ_pair 4: MDE 5.68, P(equivalent | 0) 0.84; the H table's P78 rows (all five reproduce to the printed digit); the retrain guard at 4-5 h $16.75-19.06 (CHECK's "$15-20"); block A per launch $104.6 / $123.1 (CHECK C14's "$105-125"); money sums: plan A + confirmation $780-1,130, B9 + confirmation $850-1,220, H(b) + confirmation $970-1,370 (the draft's "$780-1,220" spans plan A low to B9 high, as CHECK C3 wrote it).

Wrong or loose citations found: PR4:427 for the pick rule (it is PR4:428; D3); README:92 for the options (it is README:93; D4); "RP:71-79 via PLAN §1.1" (PLAN §5.1 holds that cite; D4); "recipe S_78 = the family's main recipe with Gate B's recipe-S differences" has a source (PLAN:297) that is not cited (D5); "lower" generation memory for Llama untagged (D6).

### 4.3 CHECK's corrections C1-C14, M1-M5

| Item | Applied | Where |
|---|---|---|
| C1 scorer kinds before block A | yes | §12, §3.2, §14 item 2 |
| C2 dose arm outside the primary fit, name "S4 add-dose" | yes | §4 clusters {a0, S1, S3, S4} and {R, A1, L1, H1}; §10 "Reading"; §11 EM-4 |
| C3 money (plan A only; B9; H(b); confirmation) | yes | §1 table; the sums re-done (§4.2) |
| C4 engine rule (Y first, X second job) | yes | §3.7, §2.3, §3.4; block 0 "not two pods" §3.2 |
| C5 R_d6-8 against stage 1's draws | yes | §3.1 Llama row; §16 row 28 |
| C6 S3, S4, dose edits per model | yes | §10, §14 items 1, 12 |
| C7 KITS_GLOB unchanged | yes | §11 EM-2 |
| C8 Gate B closed 23 Oct; reason string | yes | §11 EM-2 (RUL KD4's string verbatim) |
| C9 (the plan's grep claim) | not repeated | grep "prints nothing" finds nothing (M) |
| C10 (weekday) | not repeated | grep "Wednesday|Thursday" finds nothing (M) |
| C11 4 arms per pod under the delegation | yes | §12 |
| C12 OLMo 3 configs not committed | yes | §11 |
| C13 what needs the user (4 items) | **partly**: the four items appear in §1, §7, §8, §12 but there is no single C13 statement | D9 |
| C14 README:94, :86; $9-12; S as a ruling | yes; **block A's $105-125 per launch missing** | §9, §13 item 5, §2.3, §4; D8 |
| M1 O and L at 7-8B | yes | §14 item 3, §12 |
| M2 keep count | yes | §0 item 6, §10 |
| M3 retrain and scorer guard terms | yes | §1 table, §3.2 |
| M4 Part 2's freeze window | yes | status line, §14 item 2 |
| M5 records folder | yes | status line (via ruling 14), §17 item 1 |

### 4.4 Blinding line (§0)

Form: S1B:121 (m)'s ("the authors saw only {list}") with "no 7-8B repair arm has run; no Llama-3.2-1B repair arm has run" (RUL header) in the first sentence: present. Every value in items 1-7 matches its source (FOCUS L95 for the six contrasts, S4 15.97, A1 8.89, the reference gaps 0.8/13.0/12.4/3.0, B14, LN-14, the pick, E_HB +30.1; FOCUS L88 for +3.94; P78:50-60, :224, :272, :314 for the probe values; README:82 for Llama-3.2-1B's Gate A; RUL ruling 12 for the keep count; PR4:298 for the screen rates).

Incomplete (D2): FOCUS L95 also shows the authors the HarmBench sentence words per contrast, P3's L state *infeasible* and P2's *undetermined*, the S4-against-A1 seed-matched separation (+7.08 pp), "S4 and A1 beat the adapter-scaling curve", and "no O or L node rejects, no coherence flag"; FOCUS L87 (recorded 2026-11-02T03:25 UTC) shows stage 1b's construction checks (text-only scorer ranks and AUCs on the planted leaf: the classifier ranks it first; L1, H1, H2a, H2b and DataShield-style do not), which bears on §13 item 2 (keeping L1 and H1 primary); item 2 omits the R-arm against a0 per-arm SDs 1.35 / 2.65 pp (used in §3.5) and Gate B's final unit reading behind the TOO CLOSE verdict. None of these enters a 7-8B design number, but the form requires the list.

### 4.5 Labelled list (§13)

Nine items, each equal to RUL ruling 16 (R). Complete against the rulings. Completeness beyond the rulings: see concern 3 (rulings 7, 8, 10, 11 were also decided after the stage-1 reading and read no outcome; ruling 16 item 4 does not list them).

### 4.6 Signs, seed layouts, run counts

- Signs: P1-P6 as PR4:228 (positive = the repair restores more); G_m = U(a0) − U(m) (PR4:230); AD1 = U(S4) − U(S4_192), AD2 = U(S4) − U(S4_96): positive when the larger dose has the lower U, so positive = the larger dose restores more, consistent with PR4's P6 = U(S1) − U(S4) (R; I). CHECK C2's D1 = U(S4_192) − U(S4_48) had the opposite sign; the rulings govern and the draft follows the rulings. r_F,j = U(a0, j) − U(R_j, j) as P78:116; c_u,j = U(R_j, j) − U(u, j) as P78:258. All right.
- Layouts (ruling 2) and counts, re-added (M, by hand): plan A: methods 6 × 6 = 36 cells, R 7, a0 7 = 50 cells; minus a0 1101-1103 and R 1101-1103 (in hand or N) = 44 new; block A 18 + R_4, R_5 + a0 1104 = 21; block B 18 + R_6, R_7 + a0 1105-1107 = 23. Plan B9: block A 21 (L1, S3 kept as secondary data); block B 4 × 6 + R_6-R_10 + a0 1105-1107 = 24 + 5 + 3 = 32; total 53. H(b): block B 4 × 9 + R_6-R_13 + 3 = 36 + 8 + 3 = 47; total 68. The draft's §5 table is right, and equals RUL ruling 2's 44 / 53 / 68 and P78's block A 21.

### 4.7 Money

All figures trace to CHECK "Money (corrected)", KCR:177, :183-188, P78 §5.4 and :216, PLAN §4 and reproduce (§4.2). One omission (D8): the per-launch need for block A ($105-125 per four-pod launch at KCR's caps; CHECK C14) is absent from §1's table. One mixed basis (concern 5): §5's per-plan money and the H(b) increment rest on RP §2.1's older per-arm rates (via P78 §5.4), §1's totals on KCR's measured rates; both are tagged E, and CHECK C3 itself combined them.

### 4.8 Internal consistency

Same value everywhere: 44 / 53 / 68 (§5, §7); 6.39 / 6.47 and "6.4-6.5" (§6.1, §15); $56 (§1, §3.2, §11); 20 Nov / 1 Dec / 19 Nov dates; 15 df per family (§6.3, §6.4); 21 block-A runs (§5, §6.4); S4_96 / S4_192 / AD1 / AD2 (§10, §11); the dates of the FOCUS entries. **One inconsistency (D1, major):** §7's table pairs ruling 2's run counts (44 / 53 / 68, i.e. R at 7 / 10 / 13 seeds) with P78's unpaired SE and MDE values, which were computed at R 8 / 12 / 16 seeds, and the text asserts they "do not move". They do: the unpaired SE = 5.83 × √(1/n_R + 1/n_m) rises to 3.24 / 2.68 / 2.33 pp and the MDE to 11.3 / 8.7 / 7.6 pp (M; the same formula reproduces every P78 row first). Only the S-P multiples 1.42 / 1.08 / 0.93 × σ_pair are unchanged, because they use the shared seeds only.

### 4.9 Re-decision leaks

Read every conditional sentence in §1, §3.4, §3.7, §6, §7, §8, §10, §17. Each branch has a pre-set trigger that reads money, a fingerprint, a cap, a blinding test or N's σ̂, never a 7-8B repair outcome. No sentence lets a reader re-decide a frozen choice after a repair outcome. Two places are worth the lead's eye but are the rulings' own words (concern 1): §7 "if later, it is disclosed as made after N's reading" (ruling 4 lets the user name (a) after N's reading, with disclosure), and §6.1's review row "the user decides the next step" (ruling 3, P78:177).

## 5. Defects (exact text and replacement)

**D1 (major; internal consistency; §7, draft line 250 and the table at lines 242-248).**
Replace: `The run counts are ruling 2's (P78's 54 and 70 fall to 53 and 68; the SE and MDE columns are P78's unpaired values and do not move).`
With: `The run counts are ruling 2's (P78's 54 and 70 fall to 53 and 68). The SE, MDE and probability columns are recomputed for ruling 2's layout (R at 7 / 10 / 13 seeds against P78's 8 / 12 / 16; M: the normal approximation of P78 §6 with σ 5.83 and unpaired SE = σ√(1/n_R + 1/n_m), which reproduces every P78 row first; script verify-D-htable.py in the round's reports). P78's values were SE 3.15 / 2.57 / 2.23 pp and MDE 11.0 / 8.3 / 7.2 pp; fewer R seeds widen the unpaired SE by about 3-4%. Under S-P the primary MDE multiples below use the shared seeds only and do not move.`
And replace the five table rows with:
`| plan A, SESOI 5 (no branch) | 3.24 | 11.3 | 11.3 | 0.43 / 0.67 / 0.86 | 0.00 / 0.00 (CI half-width 5.34 > 5) | 44 |`
`| **(a)** plan A, SESOI 10 | 3.24 | 11.3 | 12.7 | 0.27 / 0.50 / 0.73 | 0.85 / 0.46 | 44 |`
`| plan B9, SESOI 5 (reference) | 2.68 | 8.7 | 8.7 | 0.72 / 0.91 / 0.98 | 0.18 / 0.03 | 53 |`
`| **(b)** P1, P3, P6 at 12 seeds, SESOI 5 | 2.33 | 7.6 | 7.6 | 0.85 / 0.97 / 1.00 | 0.38 / 0.05 | 68 |`
`| **(c)** = (b) with SESOI 10 | 2.33 | 7.6 | 12.0 | 0.20 / 0.50 / 0.80 | 0.99 / 0.69 | 68 |`
Also change the table's basis line (line 240) from `**Basis of the table (R: P78:224-234).**` to `**Basis of the table (P78:224-234's formulas, R; the values recomputed for ruling 2's layout, M).**`, and add a §16 row: `| 35 | §6 table | SE 3.15 / 2.57 / 2.23 at R 8 / 12 / 16 | SE 3.24 / 2.68 / 2.33 at R 7 / 10 / 13; MDE 11.3 / 8.7 / 7.6 | ruling 2's layout |`.
Alternative (if the lead prefers P78's illustration untouched): keep P78's rows and its counts 44 / 54 / 70 in the table, and write under it: `P78's rows at its layout (R 8 / 12 / 16); under ruling 2's layout (R 7 / 10 / 13; 44 / 53 / 68 runs) the unpaired SE is 3.24 / 2.68 / 2.33 and the MDE 11.3 / 8.7 / 7.6 (M); the S-P multiples do not move.` Either way the sentence "do not move" must go.

**D2 (minor; blinding line completeness; §0 items 1 and 2, and a new item).**
In item 1, after `E_HB +30.1 pp;` insert: `the HarmBench sentence words per contrast; P3's L state *infeasible*, P2's *undetermined*; S4 against A1 seed-matched +7.08 pp; S4 and A1 beat the adapter-scaling curve; no O or L node rejects and no coherence flag;`.
In item 2, after `mean r 2.5 pp (SE 1.06) against a linear-dose 5.6 pp` insert: `, the R-arm against a0 per-arm SDs 1.35 against 2.65 pp (R: P78:127), and Gate B's final unit reading behind the verdict (rankings and labels; FOCUS "GATE B CLOSED")`.
Add item 8: `8. **Stage 1b's construction checks** (FOCUS "STAGE 1b'S CONSTRUCTION CHECKS OPENED AND PUBLISHED AFTER THE FINAL STOP", recorded 2026-11-02T03:25 UTC; R): text-only scorer ranks and AUCs on the planted leaf (the content classifier ranks it first at every menu; L1, H1, H2a, H2b and DataShield-style do not). **Use here:** none; L1 and H1 stay primary (§13 item 2).`

**D3 (minor; citation; §13 item 5, line 335).** Replace `PR4:427; README:86` with `PR4:428; README:86`.

**D4 (minor; citation; §1, line 46).** Replace `(R: README:92; P78:9; RP:71-79 via PLAN §1.1)` with `(R: README:93; P78:9; RP:71-79 via PLAN §5.1)`.

**D5 (minor; untagged source; §3.7, line 153).** Replace `recipe S_78 = the family's main recipe with Gate B's recipe-S differences, T6a's configs;` with `recipe S_78 = the family's main recipe with Gate B's recipe-S differences (R: PLAN T6, :297; CHECK track 4's "differs only in recipe-S fields" test), T6a's configs;`.

**D6 (minor; untagged inference; §8 table, line 275).** Replace `| Generation memory | 99.3% of the card (KCR:62) | lower |` with `| Generation memory | 99.3% of the card, 204 allocator retries in the check (KCR:62) | lower (I: 8 key-value heads, a KV cache about a quarter of OLMo-2-7B's; 0 retries in its check; KCR:62) |`.

**D7 (minor; a basis that does not reproduce; §3.6 N2, line 148; the rulings' own text).** The per-family values 4.4 and 0.7 pp pool, by §3.3's σ̂_pool form √[(SD_O² + SD_L²)/2], to about 3.2 pp, not 4.5 (M). Replace `pooled about 4.5 pp;` with `the lead's pooled point about 4.5 pp (ruling 13; by §3.3's form the two per-family values pool to about 3.2 pp, M, so the point is the lead's judgement between that figure and the no-gain 8.2);`. The lead may instead amend ruling 13's basis; the prediction itself (4.5, 80% 2.5-8.5) gates nothing and can stand.

**D8 (minor; a check correction not carried; §1 money table, after line 63).** Add the row: `| Block A, per four-pod launch at KCR's caps (the kit's cap-based need) | about $105-125 (CHECK C14: $6 + 1.85 × 4 × 10.5 h = $83.70 OLMo, $6 + 1.85 × 4 × 12.5 h = $98.50 Llama, × 1.25) |`.

**D9 (minor; C13 not stated in one place; §1 after the earmark, or §17).** Add: `**What still needs the user (RUL header; CHECK C13).** (1) The money in the RunPod account (MONEY); (2) the HF token in the Mac environment at each Llama launch; (3) a yes by pod name before any stopped 7-8B pod is deleted, after a verified backup; (4) H (a) or (c), only if the user wants either (§7). Everything else in this text is a lead ruling under the delegation and is reported, not asked.`

## 6. Acceptance criteria (the builder's list, re-checked)

| # | Criterion | My result | Evidence |
|---|---|---|---|
| 1 | One new file; no other file in the worktree; no tracked, engine, frozen, sealed or runkit file touched | passed | `git status --short` in ws-d prints one `??` line (M) |
| 2 | No git state change; no pod, spend, network, install, download, agent, message; no forbidden file opened | passed (by the builder's command list, R; not independently provable) | build-D.md §4-§5 |
| 3 | Report skeleton first | passed (R: build-D.md §4 item 2) | |
| 4 | Content order: status, short names, §0-§17 | passed | `grep -n -E "^## "` (M) |
| 5 | Every ruling with basis and fallback; every P78 [USER] item mapped | passed | §4.1 above |
| 6 | Blinding line in S1B:121 (m) form with the keep count and the two "has run" sentences | **passed with a gap** | D2: five stage-1 values, stage 1b's construction checks and two Gate B items are missing from the list |
| 7 | S4 add-dose names, signs, secondary, label verbatim | passed | §10; §4.6 |
| 8 | Every number with its source and tag | **failed in two places** | D5, D6 untagged; D7's basis does not reproduce (the rulings' own) |
| 9 | §13 complete (nine items); §14 = P78 §11 + M1 + M4 + dose reading + scorer rules; §16 every departure; §17 open items incl. Llama G1 | passed | counted: 9 / 13 / 34 / 13 (M) |
| 10 | Decides nothing new; no side-paper mention; plain sentences with tables | passed | grep (M); §4.1, §4.9 |
| 11 | Internal consistency (the same value everywhere) | **failed** | D1: §7's SE/MDE columns contradict ruling 2's layout and the text claims they "do not move" |
| 12 | Citations right | **failed in three small places** | D3, D4 |
| 13 | CHECK's corrections applied | passed except two omissions | D8 (C14's block A figure), D9 (C13 in one place) |
| 14 | Signs, seed layouts, run counts, money arithmetic | passed | §4.6, §4.7 (M) |
| 15 | The file's SHA-256 in FOCUS; `commitments.py check` after the commit | not tested | the lead's freeze step |
| 16 | A reviewer's read against §13; the Llama G1 result added before the freeze | not tested | the pre-freeze reviewer; Track C |

## 7. Jobs for the lead

1. Have the builder apply D1 (the H table) first; it is the only defect a later reader could call an error in the frozen text. Then D2-D9. Re-verify the hash after the fix round.
2. Decide D7: amend ruling 13's N2 basis (the per-family pooling gives about 3.2 pp by §3.3's form) or accept the draft's "the lead's pooled point" wording. The prediction gates nothing.
3. Consider adding rulings 7, 8, 10 and 11 to ruling 16 item 4's list (concern 3), since Part 1 must label every choice made after the stage-1 reading.
4. Optional tightening of ruling 4's "if later, it is disclosed as made after N's reading" to "before N's reading is opened" (concern 1); the rulings govern, so this is the lead's.
5. Merge, freeze and records as build-D.md §7 (unchanged by this check). No background job is needed for this track.

## 8. Unresolved concerns

1. Ruling 4's clause lets the user name H (a) after N's reading with disclosure; N's σ̂ is a nuisance value, not a repair outcome, but it is what makes H fire, so a SESOI change named after it is a choice informed by the branch's trigger. The draft is faithful to the ruling.
2. The retrain pod count (ruling 10's "its own single-job pod" per family against CHECK C4/M3's one pod) stays open in §17 item 3, as the builder says; it moves the first-days guard by about $15-20 (E).
3. Ruling 16 item 4 lists S, SR-2, H, F, the thresholds, the layout and the gate as the post-reading decisions; rulings 7, 8, 10 and 11 were also made on 5 Nov after the stage-1 reading (they read files, fingerprints, caps and costs only). The draft follows ruling 16.
4. The S-U sensitivity's seeds: under ruling 2 no R seed beyond the last method seed runs, so S-U at 7-8B has fewer R cells than P78 assumed; §4's S-U line should say that S-U uses R 1101-1107 (plan A) and the H table's recomputation (D1) is the quantitative consequence.
5. §5's per-plan money (P78 §5.4, RP §2.1 rates) and §1's totals (KCR's measured rates) rest on two per-arm bases; both are tagged E and CHECK C3 used the same mix. Not a defect; the lead may want one basis at the freeze.
6. I did not open KCR beyond lines 62, 161, 177, 183-188, nor EYD, RP, PLAN-S, NEXT or S1L; figures from them are checked through RUL, P78, PLAN and CHECK only.
7. The builder's claim that no forbidden file was opened rests on its command list; I could not verify it independently.
