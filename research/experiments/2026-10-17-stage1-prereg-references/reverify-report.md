# Re-verification report: stage1-prereg-references-DRAFT.md, revision 2

Written 2026-10-16 from about 22:24 to 22:45 UTC (17 Oct IST). I checked the clock with `date -u` at 22:24:44, 22:26:46, 22:39:08 and 22:41:56 UTC. An Opus worker wrote this report for the main-study lead (General Implementation VI). It checks revision 2 against `verify-report.md` (VR). It decides nothing.

**Rules I kept.** I did not change the repository. I made no commit, push, pod, RunPod call, download, web read or spend. I opened no `rows.jsonl`, `groups.json`, `selector.jsonl`, `hidden/` or held-out file. I opened no generation, sample, guard or harm file. This file holds no rows, prompts, answers or anchor text.

**What I read that holds Gate B values (for LQ46).**
- FOCUS "noise gate" (16 Oct 00:25 UTC) and "wave 0b done" (16 Oct 13:21 UTC), in full: r_j, SD(r), σ_eval,0, σ̂_gate, P4, the P(LOCALIZED) lookup, the rankings as orders, the picks, ρ and the re-costing figures.
- The three wave-0a ledgers: key names, then only `stage`, `seconds`, `prompts`, `items`, `answers`, `queries` and `steps`. I did not read `mean_loss`, `capped`, `invalid` or `unscored`.
- `tmp/gi-vi-wave0b/recost/NOTES.md` (job slots and pod overheads).
- Not read: any Gate B arm's O, task loss, ARC, answer or score.

**Labels.** **R** = the repository (`path:line`). **C** = my own arithmetic. **I** = my inference. **RV** = this re-verification.

---

## 0. Result

| | Count |
|---|---|
| VR items (7 Major, 13 Minor, 5 Nits) | 25 |
| Fixed as VR asked | **25 of 25** |
| Fixed, but the fix carries a slip or a gap (listed as new items below) | 6: M5 (R1, R7), M7 (R5), m1 and m4 (R6), m10 (R2), n1 (R3) |
| **New errors from the fix round: Critical** | **0** |
| **New errors: Major** | **0** |
| **New errors: Minor** | **5** (R1–R5) |
| **New errors: Nits** | **9** (R6–R14) |
| Notes (not errors) | 7 (N1–N7) |

**Main points.**
1. Every VR item is fixed. Every number that the fix round changed is correct, apart from two rounding slips (R6, R7). I recomputed them from the ledger seconds, not from FIX's rounded inputs.
2. Every SHA-256 in the source table equals the file now (15 repository files, 7 folder files). The τ_L hashes and numbers equal TLC's output.
3. **TLC re-run (`python3.11 -B`): exit 0. Its output is byte-identical to `tau_l_check.out.json`** (SHA-256 `d822ba18e39d4ab5…c61`, `cmp` exit 0). It is also identical to VR's re-run.
4. The new errors are small. The two that matter most: a wrong code line that reverses a correct VR citation (R1), and a τ_O sentence that is true only for the point estimate, not for the upper bound that LQ36 proposes (R3).

---

## 1. Item table

| Item | Fixed | Note (what I checked) |
|---|---|---|
| **M1** stale sources | yes | Every hash in the source table equals the file (R; `shasum -a 256`). FOCUS, PLAN-S, PREREG, BRIEF, REC, S and G equal their `d79f641` versions; ADD (`114776482a3287dd`, now with §5) and PAPER (`024942b54a6242dd`) changed; SWEEP, PROPOSAL, MRA and MRB are new. The commit list is right: `19c2d28` changes ADD only; `1a5189b` changes paper files only; `5a96acd`, `2ed7a33` and `541b122` add files only. §R.0.1's candidate row, UQ7 and the B+Qi re-reading match ADD §5 item 4, PAPER:241 and SWEEP entries 3 and 8. HEAD moved again after revision 2 (R9). |
| **M2** blinding line | yes | Every value in the §B table equals FOCUS:82 and FOCUS:77 (r_j +0.67/+2.50/+4.33; SD(r) 1.83; σ_eval,0 1.28; bar 8 pp; P4 2.5, SE 1.06, against 5.6 and about 0; σ̂_gate 1.83, fallback 2.16; fingerprint trigger false; 61/97/100% at σ_pair 2.15; the re-costing figures; the orders, picks and ρ). "Not read" is reworded as VR asked. QI:9 ("I read no U, O, task loss, ranking or score") and RQ:147, :172 support their columns. The R1 column cannot be checked (N7). Add RV (N6). |
| **M3** LQ21 | yes | §R.2.8, LQ21 and UQ3 (c) say what VR asked. FOCUS:225 (item (4), "Ok"), FOCUS:151 (the mandatory list holds the Qi arm) and FOCUS:125 item (10) ("no warmup") say what the text says. |
| **M4** LQ9, LQ5 | yes | UQ8 and UQ9 exist; LQ9 confirms K = 39 only; SPEC:310 and :318 give K = 39 as the default; FOCUS:152 ("one evaluation per seed") and PROPOSAL:71 ("Safe LoRA 3") give 3 evaluations. UQ8 (C): $19.80 and $24.65; × 1.25: $24.75 and $30.81. So "$20–25, or $25–31 × 1.25" is right. |
| **M5** 468 prompts | yes (numbers); new slip R1 | All three ledgers: `generate` prompts 468, `guard` items 468, `sample` answers 600, `harm_scores` answers 800 (= 200 greedy harm + 600 sampled). 100 over-refusal answers: 371.1, 362.0, 332.3 s; guard 17.6, 17.2, 16.9 s; c0 (a) 869.9 s = 0.297 FRE; 1,068 answers; 200/1,068 = 18.73%; 200/468 = 42.7% (C). `GENERATION_KINDS` holds safety, arc_generation, harm and overrefusal, but at line 627 (R1). Range top is 371 s (R7). |
| **M6** W1 items | yes | The placement table, the tags and the Q.1/Q.2 split are present. BRIEF:5 defines W1 and S1. BRIEF:121 holds REQ-21 (c), (e), (i), (j), (k) and (m) as the draft says, and names the record path. PLAN-S:239 says what the text says. Residual: N1 and R8. |
| **M7** c0 job | yes; new gap R5 | LQ30 (i) says what VR asked. LQ30 (ii): 245 − 219.7 = 25.3 s; 2.9% of c0 (a), 5.3% of c0 (b) (C). Option (ii) has no seal (R5). See also N3. |
| m1 | yes; nit R6 | Marginal (C): one point $4.07, +1 pod $4.847, × 1.25 $6.06; two points $8.14, $9.69, $12.12. With regeneration: $6.04, $7.55; $10.88, $13.60. "$4.9" should be "$4.8" (R6). |
| m2 | yes | 0.03 FRE = 88.0 s = $0.044, so "< $0.05" is right. |
| m3 | yes | Regeneration 0.319 / 0.578 c0; transform 0.101 / 0.184 c0, so "< 0.11" and "< 0.19" are right. The Fix log's reason for "< 0.19" against VR's "< 0.18" (88/491 s) is right. |
| m4 | yes; nit R6 | One evaluation-only job 2,729.4 s = 0.930 FRE = $1.357. Certificate with it: $2.70–2.849, 90.5–95.5 min. "$2.7–2.9" should be "$2.7–2.8" (R6). |
| m5 (a)–(e) | yes | The text now says what VR asked. I checked it against VR and the notes only. I did not read the papers again (no downloads in this brief). The step arithmetic holds: 7,473/64 × 3 = 350.3 steps; 10/350.3 = 2.85%; 10/600 = 1.67%. |
| m6 | yes | §R.1.3 row 6. |
| m7 | yes | §R.3 item 3. |
| m8 | yes | `NOTES.md` is in the main checkout. Its lines 23–26 give 48.9, 49.0 and 43.5 min, 18.9 and 26.0 min, and $1.79/h. |
| m9 | yes; nit R11 | No "FOCUS:<line>" is left in the text. All 18 key-table entries have the right title, time and start line at `23e3da8f…`. Two ranges are partial (R11). |
| m10 | yes; new issue R2 | The failure path quotes PLAN-S:233 correctly. Its engine ("re-run on X") conflicts with LQ19 and LQ20 (R2). |
| m11 | yes | FOCUS:125 item (1): "for the whole Gate B path". |
| m12 | yes | FOCUS:154: "Specialized builds it with tests, reviewed before use". |
| m13 | yes | `engine.py`:440 `def load_state`; :449–450 the file-hash check; :452–453 the fingerprint refusal. 441–453 holds both. |
| n1 | yes; new issue R3 | 17 + 2, 5, 10 = 19, 22, 27. True for the point estimate only (R3). |
| n2 | yes | 2.80 × √(0.05 × 0.95/300) = 3.52 pp. |
| n3 | yes | Training 7.56–8.39% of the ledger and 7.47–8.28% of the slot; generation 80.0–81.9% and 78.9–80.9% (C). The rounded ranges are right. |
| n4 | yes | "491 s" is left only in the Fix log, as history. |
| n5 | yes | §C.3. |
| VR §5 notes | yes | PROPOSAL:71 gives "≈ 0.85 FRE". SWEEP:232 and :275–276 hold the three Safe LoRA follow-ups. The QI unit note is in §C.9. |
| VR §6 | yes (kept as limits) | Line 24 and §P. |

**Also correct (new text from the fix round).**
- PAPER revision 6 lines: :144 (label placeholder), :236 (decision 22), :240 (decision 26), :241 (decision 27), :269 (risk 18), :276 (risk 25), :471 (§3.2). The old-to-new map in the Fix log is right (old :117, :198, :222, :229 at `19c2d28`).
- MRA and MRB line ranges: MRA:97, :111, :177, :236; MRB:83, :164, :180, :303, :490–505. The summaries in §N are fair (5.4 pp MDE; up to 14%; +15% steps; one-sided 95% bounds; all 250 XSTest safe prompts and OR-Bench-Hard-1K; "better, below δ"; base or SFT against Instruct).
- §N item 3 (C): 12 evaluations = 11.2 FRE, $16.29; + 3 pods $18.61; × 1.25 $23.27.
- B+Qi under C-lean (C): per seed 1.113–1.156 c0 (a), 1.205–1.282 c0 (b); 6 seeds 6.68–6.93 and 7.23–7.69 c0.
- The consolidated lists: all 46 [LEAD] items in the text (LQ1–LQ47 without LQ5) and all [USER] items appear in §Q. "32 active" and "8 at S1 or later" are right.
- The Gate A fingerprints in §R.0.7 (16 characters) and the q fingerprint `322d737a…` equal the units' `COMPLETE.json`. R_1's edit `f7d7eb86…` equals its unit folder name.
- `tmp/gate-b-olmo/gate_b_inputs_noise_gate.json` is `8b484bcf…`. Its `gate_a` entries 1101, 1102, 1103 and untuned name the same four unit paths as §L.4.

---

## 2. New errors from the fix round

### Minor

**R1. A correct VR citation was reversed.**
- **Where:** §C.4 ("R: `runner.py`:625"); Fix log, "Beyond the report" item (6).
- **Evidence (R):** `grep -n` gives `GENERATION_KINDS = (...)` at `runner.py`:627. The file last changed on 10 Oct (commit `c9aa7ca`) and has no working-tree change. So VR's ":627" was right.
- **Fix:** cite `runner.py`:627. Delete item (6) of the Fix log.

**R2. The new failure path names the old engine.**
- **Where:** §R.0.7 ("a0 at that seed is re-run on X").
- **Evidence (R, I):** LQ19 merges X′ before the stage-1 freeze. LQ20 says that every stage-1 unit after the merge runs on X′. The regenerations and the eval-only references run in block B (§R.0.8), after the merge. PLAN-S:233 says "re-run on X", but it was written before X′ was planned.
- **Fix [LEAD, inside LQ4]:** name the engine. For example: "re-run on the stage-1 engine (X′ after the merge), accepted under LQ20's certificate". Or state that X is kept for this case, and how.

**R3. The τ_O sentence holds only for the point estimate.**
- **Where:** §L.1 ("τ_O binds only for arms that over-refuse more than the untuned model: O above 19%, 22% or 27%"); §N item 2 ("ΔO ≈ 0, so it passes τ_O").
- **Evidence (C, I):** LQ36 proposes the one-sided upper 90% bound of ΔO, as PLAN-S:127's screen uses. For an arm at the untuned level (O ≈ 17/100), the binomial SD per seed is 3.76 pp. Over 6 seeds the SE is at least 1.53 pp, and seed noise adds to it. The bound then adds about 1.97 pp (z) to 2.26 pp (t, 5 df). So at τ_O = 2 such an arm passes about half the time or less. At τ_O = 5 and 10 the screen binds at about 20% and 25%, not 22% and 27%.
- **Fix:** "On the point estimate, τ_O binds only above 19%, 22% or 27%. Under LQ36's upper 90% bound it binds about 2 pp lower; an arm at the untuned level is at the edge of τ_O = 2." In §N item 2, write "so it passes τ_O on the point estimate". This also bears on MRB §8.3's case.

**R4. The precedent for keeping U4 and U6 as [LEAD] is misquoted.**
- **Where:** §Q.1, the notes ("as ADD did for L1–L16"); §N item 2 ("The family count and the table order (LQ43, LQ44) are the lead's under the Marks rule").
- **Evidence (R):** In BRIEF, L1–L16 are "Lead decisions to confirm before the build" (BRIEF:199). They were never user items. The real precedent is the D5 entry: "U2 (plan usage) and U3 (c0) keep the brief's defaults" (FOCUS D5 decided, 16 Oct 12:15 UTC; ADD line 7), under the user's "decide D5 for me". BRIEF:192 (U4) names exactly LQ43 and LQ44: "the label order … the Holm family for the O and task-loss contrasts". BRIEF:194 (U6) names LQ42.
- **Fix:** cite the D5 entry and ADD line 7 as the precedent. Make §N item 2 conditional, like the §Q.1 note. **[LEAD]:** record the reading of the 16 Oct instruction in the W1 FOCUS entry. If not, mark LQ42–LQ44 [USER] W1, with the proposals as defaults.

**R5. LQ30 option (ii) has no seal.**
- **Where:** §C.6, LQ30 (ii).
- **Evidence (R, I):** a0@1101 is a Gate A unit that stage 1 reuses as its a0 at seed 1101 (PLAN-S:233; BRIEF REQ-21 (d)). The batch argument of option (i) applies here too: the lean job's sampled answers may differ from the unit's. If someone reads them, stage 1 has two different a0@1101 evaluations.
- **Fix [LEAD, inside LQ30]:** apply (i)'s rule to (ii). Only its ledger is read. Its evaluation files are sealed by hash and never read for any estimate.

### Nits

- **R6. Double rounding.** FIX prints $4.85 and $2.85. The true values are $4.847 and $2.849, so write "$4.8" and "$2.7–2.8". **Where:** "$4.9" in §R.1.3 (UQ9), §R.1.10, §C.9 (two rows), §Q.2 (UQ9) and the Fix log (m1); "$2.7–2.9" in §R.2.7 (LQ20), §R.2.11, §C.9 and the Fix log (m4). VR made the same slip. The × 1.25 figures ($6.1) are right.
- **R7. Range top.** "330–370 s" (LQ27 (a); Fix log M5): R_1 gives 371.1 s. Write "330–371 s".
- **R8. LQ47's deadline.** LQ47 is tagged "W1 if it changes an arm; else S1", but its record is REQ-21, the W1 record ("Where each part goes", row 5). ADD §5 item 1 already puts the token reports in REQ-21 (b) and (f). Recording it costs nothing, so tag it W1. The §C heading lists LQ27, LQ29 and LQ31 as the exceptions; add LQ47.
- **R9. HEAD moved again.** At 22:39 UTC HEAD is `32827af` (22:31:37 UTC). It adds 26 files under `research/review/2026-10-17-icml-78b-prep/`, among them a 7–8B pre-registration draft and an engine-round-Y design. I did not read them. No cited source changed: I re-hashed FOCUS, ADD, BRIEF, PLAN-S and PAPER at about 22:40 UTC. Update line 26 and §N.
- **R10. Clock count.** The header lists three `date -u` checks (22:03, 22:13, 22:16 UTC); §P says "four times".
- **R11. Two partial line ranges.** In the FOCUS key table, "decisions 8 Oct 17:36" spans lines 217–227 (227 is its "Money" sub-item), and "sharpened direction" spans 236–256. The table gives 217–226 and 236–246, which are the cited sub-items. Name the column "lines of the cited items", or give the full spans.
- **R12. Undefined prefix.** §R.1.4 writes `SS/engine.py` and `SS/runner.py`. "SS" is not in the source table; elsewhere the draft writes `engine.py`. Define SS = `experiments/safety_selection/`, or drop it.
- **R13. A misplaced remark.** §Q.2's LQ30 row puts "(needs B17)" after option (ii). §C.6 says that both options need B17.
- **R14. A BRIEF column is misquoted.** UQ7 says that "the D5-7 row of BRIEF applies: an S1 reference, or a W1 rule …". That is the row's (b) and (c) column (BRIEF:179). Under D5 = (a), the row says "not built". Write "the options in BRIEF's D5-7 row for (b) and (c)".

---

## 3. Notes (not errors)

- **N1. LQ25, LQ26 and LQ28 timing.** Under LQ31, 1 FRE is the unit under C-full. So LQ25 (FRE) and LQ26 (C-full's stages) define what c_d/c0 means under C-full in REQ-18's predictions. By VR M6's reasoning they are W1-P. The draft keeps them S1 and says the lead decides. **[LEAD]:** I recommend W1-P. LQ28 (the C-lean prices) follows LQ27, so W1-P as well.
- **N2. LQ47 and the title.** PAPER decision 26 (PAPER:240) records a user rule of 17 Oct: the title keeps "Compute-Matched". The fallback title is used "only if token matching cannot be done". So LQ47's ruling decides more than an analysis. **[LEAD]:** state whether ADD §5 item 1's token-axis report counts as "a token-matched analysis beside the row-matched one". If it does not, the title goes back to the user (**[USER]**, REQ-21 (a), as ADD §5 item 1 says).
- **N3. LQ30 (ii)'s extra training.** The draft uses 245 s, a Gate A arm on another pod (PLAN-S:30). If training time scales with steps, the wave-0a value gives 219.7 × 38/33 ≈ 253 s, so about +33 s: 3.8% of c0 (a) and 6.9% of c0 (b) (C). Both are estimates, and the record measures the real value.
- **N4. c0 in dollars.** c0 (b) ≈ 480 s ≈ $0.24 at $1.79/h, which is below PLAN-S:202's "about $0.3–0.6". c0 (a) ≈ $0.43 is inside it. The 15 s of load may understate a cold start (I). This is a check, not an error.
- **N5. LQ20's extra evaluation stays [LEAD].** The draft's reason: it is part of a planned certificate. A strict reading of the Marks rule ("a spend that the approved plan does not hold") could make it [USER] ($1.36). **[LEAD]:** keep the reason, or move it to UQ6.
- **N6. Blinding.** Add RV to §B: RV read FOCUS:77 and FOCUS:82 in full (every value in §B rows 4–10), the wave-0a ledger stage seconds and counts, and the recost notes. RV read no Gate B arm's O, task loss, ARC, answer or score.
- **N7. Revision 1 is gone.** The draft was edited in place. Its stated SHA-256 for revision 1 (`4a1926b07c4eb7ca…`) matches VR's prefix. I could not check the R1 column of §B, or any text that revision 2 removed.

---

## 4. Not verified

- The paper claims (Safe LoRA, Qi et al.). I did not read the papers again: this brief allows no downloads. The m5 fixes match VR's statements.
- The C and H claims (VR §6). They are unchanged and still unverified.
- The split of the 168 other greedy prompts by kind, and batch-invariant sampling.
- Anything in commit `32827af` and the `541b122` stage-2 notes.
- The Gate A O counts (17, 4, 6, 4). VR verified them; revision 2 did not change them.

---

## 5. Commands run

- `date -u` (four times): exit 0.
- `git rev-parse`, `git branch --show-current`, `git log`, `git show --stat` (7 commits), `git diff --stat` and `--name-status` (`fc85fda..19c2d28`, `541b122..HEAD`), `git status --short`, and `git show <rev>:<file> | shasum` (main checkout, read-only): exit 0.
- `shasum -a 256` of the 15 repository sources, this folder's files and the three ledgers: exit 0.
- `python3.11 -B tau_l_check.py <scratchpad>/rv/tlc-rerun2.json`: exit 0. `cmp` against `tau_l_check.out.json`: exit 0 (identical). `cmp` against VR's `vr-scripts/tlc-rerun.json`: exit 0.
- `python3.11 -I -B fix_numbers.py` (output to the scratchpad): exit 0.
- `python3.11 -I -B` on my own scripts: `ledger_keys.py` (key names only), `ledger_secs.py` (whitelisted fields), `fp.py` (fingerprint fields only), `rv_arith.py` (independent arithmetic), `ctx.py` (text search in the draft), and three inline checks (the §L.4 hashes and numbers against TLC; the [LEAD]/[USER] lists; the noise-gate inputs' `gate_a` names). All exit 0.
- `sed`, `grep` and `awk` reads of FOCUS (lines 68–260), ADD (all of §1–§5, and L3, L13–L16), BRIEF, PLAN-S, PAPER (old and new lines), SWEEP, PROPOSAL:71, MRA, MRB, SPEC, `runner.py` and `engine.py`, and the three input notes. Two `grep -o` calls failed with a ugrep error ("exceeds complexity limits"); I ran them again in Python.
- `df -h`: 59 GB free.

**Evidence paths** (temporary, outside the repository): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/c519cf93-2a82-40cd-bff7-64852d1f6d17/scratchpad/`
- `rv/tlc-rerun2.json` (the TLC re-run);
- `rv/fix-rerun.txt` (FIX's output);
- `rv/rv-arith.txt` (my arithmetic);
- `rv-scripts/` (the scripts above).

**Files written:** this report only, in the folder. The draft, VR, the notes, TLC and FIX were read, not changed.
