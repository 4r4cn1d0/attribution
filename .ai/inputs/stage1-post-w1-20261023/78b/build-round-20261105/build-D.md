# Build report: Track D (7-8B pre-registration, Part 1 text)

Worker: Track D of the 7-8B $0 build round (Fable builder, detached scratch worktree). Started 2026-11-05 13:28 UTC; this report finished 13:46 UTC (clock read with `date -u` at 13:28, 13:35, 13:45; M).
Status: DONE. One new file written; no existing file edited; no git state changed; no pod, spend, network, install, download, agent or message.

Tags: M = measured (command given); R = read (path:line); E = estimate (basis given); I = inference.

## 1. Files changed (all new)

1. `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-d/research/experiments/2026-11-05-78b-preregistration-part1.md`
   - 439 lines (M: `wc -l`). SHA-256 `ab98171e82cffbb42003124740c80fcd20355e9efd12ec3c13a9df38c0a5c248` (M: `shasum -a 256`, 13:45 UTC, after the two citation fixes below). Untracked in the worktree at `fb51421` (M: `git status --short` prints only `?? research/experiments/2026-11-05-78b-preregistration-part1.md`).
   - It is a DRAFT for the freeze. The lead freezes it by SHA-256 in FOCUS and a commit by explicit path (ruling 14). Any edit by the lead changes the hash; the lead takes the final hash at the freeze.
2. This report: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/build-D.md`.

No file in the main checkout `/Users/spiderishi/Coding/attribution` was written, moved or deleted (I only read from it by absolute path). Note (M): `git status --short` in the main checkout shows pre-existing changes that are not mine (`M .ai/HANDOFF.md`, `M research/review/EDGE_CHECKS.md`, untracked `.ai/briefs/bluedot-budget-alternatives-20261013.md`, `.ai/briefs/main-study-restart-alternatives-20261014.md`, `.ai/cleanup-20261022.json`, and more); I did not touch them.

## 2. What the file holds (content, in the brief's order)

Status line (DRAFT for the freeze; adopts the rulings; authorizes no run or spend; the lead freezes it by SHA-256 in FOCUS and a commit before block 0's first launch); short names with source hashes; §0 blinding line in S1B:121 (m)'s form (every stage-1, Gate B, stage-1b, probe and Llama-3.2-1B Gate A value seen, each with "use here"; the 1B S4 keep count 57 of 64; "no 7-8B repair arm has run; no Llama-3.2-1B repair arm has run"); §1 scope, options B and C, the gate (ruling 9), the earmark, the corrected money table (CHECK C3); §2 the seven units with every `COMPLETE.json` SHA-256 and the q/e1 fingerprints, the four conditions, ruling 7 with its fallback; §3 block 0 = N (runs with the edit files' SHA-256, configs, the Llama 1103 rule, pods and caps per ruling 11, money, the reading, the a0-free fallback, report-only results, predictions N1 and N2 with their bases, the a0-1101 retrains and ruling 10's engine rule); §4 S (ruling 1, HB-C form, the contrasts and their sign from PR4:228); §5 the seed layout (ruling 2) with the run-count table per plan (44 / 53 / 68) and P78's money as upper bounds; §6 SR, the thresholds (kept; paired MDE 6.39 / 6.47 pp stated), the review ceiling, SR under [C], SR-2 with its condition and fallback, the operating-characteristics table (P78 §5.2 plus the 15-df line); §7 H (ruling 4: (e) with (b) first, the chain B → C on F1 at (b) → (d), why (a) and (c) are the user's; P78 §6's table with ruling 2's counts); §8 F (ruling 5, the evidence table, the trade-off, the technical fallback F2); §9 TC does not run (ruling 6; P78 §7's rule kept compactly for the record); §10 the S4 add-dose arm (ruling 12 in full: label verbatim, name, S4_96 / S4_192, AD1 = U(S4) − U(S4_192), AD2 = U(S4) − U(S4_96), construction per model, the 1B keep count, fallback, seeds, the reading outside Φ / Holm / HB-C with the paired-t form of PR4:281, compute disclosure, where it runs, cost, the prediction of ruling 13, the 3-seed power note); §11 EM-1 to EM-5 revised (C8: Gate B closed 23 Oct; hold 0; KITS_GLOB unchanged; dose arm secondary) and "what stays frozen now" (PLAN §5.11, C12); §12 the kit route and the pre-block-A scorer kinds in one paragraph (ruling 11); §13 ruling 16's nine labelled choices; §14 Part 2's list (P78 §11 plus M1, M4, the dose arm's reading, the scorer rules before any scorer output, C6, the confirmation's design, SR-2's simulation, the coherence screen); §15 limits and weak points; §16 a 34-row change log against P78 (P78 place, P78 text, this text, why); §17 thirteen open items for the lead, the first being "the Llama G1 check's result is added before the freeze".

## 3. Alternatives considered, and why I chose as I did

1. **TC's rule: full reproduction of P78 §7 against a compact record.** Ruling 6 says "P78 §7's rule is kept in Part 1 for the record". I wrote the rule's operative parts (when, units, arms, contrast, σ̂_T, t at 3 df, the three labels, the 8 pp floor, the headline simulation figures) in one paragraph and cited P78:249-295 for the full text and tables. Reason: TC does not run; a full copy of three tables and the extension would add 50 lines that gate nothing. The lead can paste P78 §7 in if a verbatim record is wanted.
2. **Where the money table goes.** The brief puts "money" in §3 (block 0) and "the gate" in §1. I put the gate's inputs (B / C totals, the dose arm, the first-days guard terms; CHECK "Money (corrected)") in §1 and N's own spend and need in §3.2. Reason: the gate reads those totals; N's figure is one line of them.
3. **The run counts per plan.** Ruling 2 gives the totals 44 / 53 / 68. I derived the block A / block B compositions from ruling 2's layout and PR4's block form (tagged I) and checked each total against ruling 2 and P78 §5.4. Alternative: quote totals only. I chose the table because P78 §5.4 is a table and the lead's kit will need the per-block cells.
4. **The H table's run column.** P78 §6's table has a "Runs per family" column with 44 / 54 / 70. I replaced those with ruling 2's 44 / 53 / 68 and said in the text that the SE and MDE columns are P78's unpaired values and do not move. Alternative: leave P78's column and footnote it. I chose the replacement so the text has one set of counts.
5. **Wording for the reused units.** P78 and the rulings call them "the side project's" or "the side units". The brief forbids any mention of the side paper. I wrote "the seven engine-X units", "the family-probe units" and "the side units" (P78's own short form) and never "side project" or "side paper" (M: `grep -i -E "side paper|side project|side-project"` prints nothing).
6. **The predictions' date.** Ruling 16 item 3 says "the date is stated". I dated N1, N2 and the dose prediction 5 Nov 2026 (the rulings' date). Alternative: leave the date to the lead. The rulings fix the numbers; the date follows from their record.
7. **Open items against decisions.** Three places tempted a decision: the retrain pod count (ruling 10's "its own single-job pod" per family against CHECK C4/M3's "the retrain pod"); N's R-arm judging (P78:112 lists the cost, no ruling places it); the Granite judge after TC's non-run. I wrote each as an open item (§17 items 3, 5; §9) and decided none.

## 4. Commands run (exit status)

All in the foreground, each well under a minute. No test suite was run (this track writes text only; there is nothing mechanical to test beyond the hash).

1. `ls -la` of the worktree and the reports folder; `git rev-parse HEAD` and `git status --short` in the worktree; `date -u` — exit 0. HEAD `fb51421a2a1deb462b24b86d50fca7f41dbb1c0f`; clean before my file (M).
2. `mkdir -p …/ws-d/research/experiments` and the report skeleton via `cat > … <<'EOF'` — exit 0.
3. Reads (Read tool): RUL in full; PLAN in full; CHECK in full; P78 in full (two pages); PR4:111-182 and :224-298; DOSE and MONEY in full (`cat`); README:78-125 (`sed -n`); FOCUS headings and the five named entries (`grep -n`, full lines); S1B:121 (`sed -n`, `grep -o`); PR4:415-418, :426-430 (`sed -n`) — exit 0.
4. Citation checks (M): `grep -n` on README for ":86" (the pick rule), ":90" (the 7-8B tier heading), ":94" (TOO CLOSE, does not run), ":113", ":120"; `sed -n '62p;177p;183,188p'` on KCR (the 99.3% line, the $56.06 block-0 example, the per-arm cost table); `ls -la scripts/stage1/commitments.py` (exists, 20,949 bytes); `shasum -a 256` of RUL, PLAN, CHECK, P78, PR4, DOSE, MONEY, README, FOCUS; `git rev-parse --short HEAD` and `git branch --show-current` in the main checkout (`ead1d7e`, `stageb-costs-and-recovery-safeguards-20261003`) — exit 0.
5. The Part 1 file written (Write tool) — ok.
6. Post-write checks: `grep -n -i -E "side paper|side project|side-project"` (none; exit 1 from grep is the "none" branch, printed "none"); `grep -n "+48.0, +52.8, +44.2" README.md` (line 82); `grep -n "7.0%, 4.7%, 3.7%"` on PR4 (line 298); `sed -n '418p'` on PR4; `wc -l`, `shasum -a 256` of the file; `git status --short` in the worktree and the main checkout; `date -u` — exit 0.
7. Two Edit calls fixing citations: `README:81 region, "Stage 2"` → `README:82`; `PR4:297` → `PR4:298` — ok.
8. Final `wc -l`, `shasum -a 256`, `grep -n -E "^## "` (the 18 section headings in order), `date -u` — exit 0.

Not run: any Python, any test, any mutation set, `scripts/stage1/commitments.py check` (the lead's freeze step; it needs the commit).

## 5. Evidence paths (all read by absolute path in the main checkout; SHA-256 M at 13:35 UTC)

- RUL `/Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md` — `65e477b0ac1e772c0cb87b6230b1a4212811d3ae960cb86dee156baa2c3ab370` (equals FOCUS's `65e477b0…`).
- PLAN `…/78b/readiness-20261105/78b-readiness.md` — `f39238d352ca3922ac7588f056c61aa2c24d05740492e96ad276c0ad38944fb7`.
- CHECK `…/78b/readiness-20261105/78b-readiness-check.md` — `1bc40aa4c842ff9b49f01ff599ed13d18a3e1fe25f95a76b70ad0628ca5e2f0f`.
- P78 `/Users/spiderishi/Coding/attribution/research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md` — `e6a73c92ef97e107402d5c2065330c9aa2f31548c98e5466798135c7e0fb48ed`.
- PR4 `/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` — `7eccf9e9bed1e73307caec22e559b4c5fcc190b9f14c3557b4437874f935628c`.
- DOSE `…/reading/user_yes_s4_dose_arm_20261101.json` — `65745ad15d5cf28b455145bbc24e851bb9a48cf67040c405f6b1c19cfd04f508`.
- MONEY `…/reading/user_answer_78b_money_20261101.json` — `53945ecbf623864f7f930c241dbb28062f5d69c846f0078d58c8a22f614d35c0`.
- README `/Users/spiderishi/Coding/attribution/README.md` — `6dfe1447fb9a491999dea3e9527e74a21b1a5a7a648807d2cbe81be38c4f4131`; FOCUS `/Users/spiderishi/Coding/attribution/research/FOCUS.md` — `113a9275aca22b4a5e7f0cbbd016ef4ef2b828d3adb8a6930fffdceec40569fd`.
- KCR lines 62, 177, 183-188 (R only; not hashed). S1B line 121 (R).
- Not opened: any `tmp/` folder named in the brief, any selector/hidden/judge/answer/prompt file, EYD, RP, KCR beyond the lines above, the OLMo 3 addendum, NEXT (cited via PLAN).

## 6. Acceptance criteria (passed / failed / not tested)

| # | Criterion (from the brief and PLAN T1) | Result | Evidence |
|---|---|---|---|
| 1 | One new file at the given path; no other file written in the worktree | passed | `git status --short` prints one `??` line (M) |
| 2 | No existing tracked file edited; no engine, frozen, sealed or runkit file touched | passed | same; main checkout untouched by me (M) |
| 3 | No git state change anywhere | passed | no git write command was run (the command list in §4) |
| 4 | No pod, spend, network, install, download, agent, message | passed | §4 |
| 5 | No forbidden folder or text file opened; counts and aggregates only | passed | §5 "Not opened"; the keep count is quoted from RUL, not re-read |
| 6 | Report written first as a skeleton, then updated | passed | §4 item 2, then this version |
| 7 | Content in the brief's order: status, short names, §0-§17 | passed | `grep -n "^## "` lists 18 headings in order (M) |
| 8 | Every ruling written with its basis and its pre-set fallback | passed | §2.3 (7), §3.1 (8), §3.2 (11), §3.6 (13), §3.7 (10), §4 (1), §5 (2), §6 (3), §7 (4), §8 (5), §9 (6), §10 (12), §11-§12 (11), §13 (16), §1 (9), status (14); each names its ruling |
| 9 | Every [USER] item of P78:385-397 has the user's recorded word or a ruling (PLAN T1 acceptance) | passed | 1 S → ruling 1; 2 H → ruling 4; 3 SR-2 → ruling 3; 4 F → ruling 5; 5 TC → ruling 6; 6 RP decision 5 and Llama 1103 → rulings 7, 8; 7 decision 2 → ruling 9; 8 the review ceiling → ruling 3; 9 N's money → ruling 11 / EM-2; 10 SR under [C] → ruling 3; 11 thresholds → ruling 3; 12 D5 and H → ruling 4 (the user's word, if (a) or (c)); the dose arm → DOSE (the user's word) |
| 10 | Blinding line in S1B:121 (m)'s form; the 1B S4 keep count; "no 7-8B repair arm has run; no Llama-3.2-1B repair arm has run" | passed | §0 items 1-7 and the first sentence |
| 11 | The S4 add-dose arm with the rulings' names (S4 add-dose, S4_96, S4_192, AD1 = U(S4) − U(S4_192), AD2 = U(S4) − U(S4_96)); secondary; never in Φ, the Holm family or the primary HB-C fit; the label verbatim | passed | §10; EM-4 in §11 |
| 12 | Every number carries its source; M/R/E/I tags | passed (by construction; see concern 4) | each number cites RUL, P78:line, PR4:line, CHECK, PLAN, KCR:line, DOSE or MONEY |
| 13 | P78's notation kept (σ̂_pool, σ_eval,0, s_arm, r_F,j, Λ, Φ) | passed | Short names, §3.3, §4, §6 |
| 14 | §13 labelled list complete (ruling 16's nine items) | passed | §13 items 1-9 |
| 15 | §14 Part 2's list = P78 §11 + M1 + M4 + the dose arm's reading + scorer rules before any scorer output | passed | §14 items 1-13 |
| 16 | §16 change log: every departure from P78 with its reason | passed (34 rows) | §16 |
| 17 | §17 open items, including "the Llama G1 check's result is added before the freeze"; nothing decided there | passed | §17 item 1 and items 2-13 |
| 18 | Decide nothing new | passed (I) | the three tempting places are open items (§3 of this report, item 7) |
| 19 | Plain, short sentences; tables where P78 uses them | passed (I) | tables in §1, §2.1, §3.1, §5, §6.1, §6.3, §7, §8, §9 (inline), §16 |
| 20 | Never mention the side paper | passed | grep (M) |
| 21 | FOCUS entries cited by title and recorded time, not line numbers | passed | §0, §1, §9, §11 |
| 22 | The file's SHA-256 in FOCUS before block 0's first `launch.py`; `commitments.py check` passes after the commit (PLAN T1) | not tested | the lead's freeze steps (§7 below) |
| 23 | A reviewer's read against §13 (PLAN T1 "the decisive check") | not tested | the verifier of this round, then the reviewer before the freeze |
| 24 | The Llama G1 check's result added before the freeze | not tested | Track C runs the check; the lead adds the result (§17 item 1) |

## 7. Jobs for the lead

1. **Merge by explicit path:** copy `…/ws-d/research/experiments/2026-11-05-78b-preregistration-part1.md` to the main checkout's `research/experiments/2026-11-05-78b-preregistration-part1.md` (ruling 14's path). Edit as needed (the hash changes).
2. **Before the freeze:** add the Llama G1 check's result and date to §15 and §17 item 1 (Track C's output; ruling 14); the reviewer's read against §13; settle or leave §17 items 3 and 5 (they can stay open items in the frozen text; nothing in them gates block 0's N pods).
3. **The freeze (ruling 14):** `cd /Users/spiderishi/Coding/attribution && shasum -a 256 research/experiments/2026-11-05-78b-preregistration-part1.md`; commit by explicit path; the SHA-256 into FOCUS (`date -u` first); then `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B -I scripts/stage1/commitments.py check` (or the records tool the lead uses; I did not run it, so I do not know its exact arguments; the plan names the command as `scripts/stage1/commitments.py check`). Before block 0's first `launch.py`, by about 19 Nov.
4. **Records:** this report and the frozen text's hash go under `.ai/inputs/stage1-post-w1-20261023/78b/` (ruling 14, M5).
5. No background job is needed for this track.

## 8. Unresolved concerns

1. **Ruling 10 against CHECK C4/M3 on the retrain pod count.** Ruling 10: "each family's a0-1101 retrain … on its own single-job pod" reads as one pod per family (two pods). CHECK C4 ("block 0 is three pods") and M3 ("the retrain pod … $15-20") count one. The rulings govern, so the text follows ruling 10's wording and names the discrepancy in §17 item 3. The kit's `init-block 0` need should settle it; the money differs by one guard term (about $15-20, E).
2. **The H table (§7) mixes P78's unpaired SE/MDE columns with ruling 2's run counts.** I say so in the text. The SE and MDE do not depend on the R seeds beyond the method seeds under S-P, and P78's rows were unpaired anyway, so the mixture is labelled, not wrong. A verifier may prefer P78's counts with a footnote.
3. **Derived block compositions (§5 table) are my inference (I)** from ruling 2's layout and PR4's block form; the totals match ruling 2 (44 / 53 / 68) and P78's block A (21). A verifier should re-add the cells.
4. **Two numbers rest on sources I did not open directly:** NEXT (§13 item 8, cited via PLAN §1.1) and EYD:81 (via RUL and P78). KCR was read only at lines 62, 177, 183-188; its other figures are cited through RUL, PLAN or CHECK. The $0.33/day storage figure is cited through P78:112 (KCR:161 not re-read).
5. **The "about $56" need in §3.2 is N's two pods only** (KCR:177 says "plus the Gate B hold", now 0). The retrain pod and the scorer pods add their guard terms (M3); the text says so, but the lead's funding record for the first launch day must add them.
6. **Predictions are dated 5 Nov 2026 in the text** (the rulings' date). If the lead wants the freeze date instead, change §3.6, §10 and §13 item 3 together.
7. **The main checkout has uncommitted changes that are not mine** (§1 note). I only read from it; the lead may want to know before merging.
8. **The dose arm's P78:238 citation** ("one-sided bounds as PLAN-S §5.3 does for secondary arms") is P78's description of option (b); PLAN-S itself was not opened. The form is the rulings' (ruling 12), so the citation is a pointer, not the authority.
9. **§9's Granite line** ("not needed for TC; Part 2's judges item settles any other Granite use") is a consequence of ruling 6, stated as such; it is not a decision about Granite at 7-8B. If the lead reads it as one, move it to §17.
