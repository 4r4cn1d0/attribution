# Verification report: stage1-prereg-references-DRAFT.md

Written 2026-10-16 from about 21:44 UTC to 22:02 UTC (17 Oct 03:32 IST). I checked the clock with `date -u` at 21:59:43 UTC. An Opus worker wrote this report for the main-study lead (General Implementation VI). It is an adversarial check of the draft. It decides nothing.

**Rules I kept.** I did not change the repository. I made no commit, push, pod, RunPod call or spend. I opened no `rows.jsonl`, `groups.json`, `selector.jsonl`, `hidden/` or held-out file. I read no row, prompt, answer or anchor text. From the wave-0a ledgers I read only the stage names, seconds and counts. I did not read the `mean_loss`, `capped`, `invalid` or `unscored` fields. From Gate A units I read only the task-loss numbers, the over-refusal counts and the adapter fingerprints. This file holds no rows, prompts, answers or anchor text.

**Labels.** **P** = the paper, read again today on arxiv.org. **R** = the repository (`path:line`). **C** = my own arithmetic. **I** = my inference.

**What I checked.**
- The draft: `stage1-prereg-references-DRAFT.md`. SHA-256 `4a1926b07c4eb7ca…`.
- Its three input notes: SL `d78a97d7…`, QI `e341c2c6…` and RQ `87951be5…`. Also `tau_l_check.py` `20b21e5d…` and `tau_l_check.out.json` `d822ba18…`. All four hashes equal the draft's table.
- Safe LoRA, arXiv 2405.16833v2. I downloaded the HTML and the PDF again. I read the whole text, with the equations from the LaTeX alt text. I rendered PDF page 9 to read Fig. 3 and Fig. 4. arXiv lists v1 and v2.
- Qi et al., arXiv 2406.05946v1. I downloaded the HTML again and read §4, App. A–D and Tables 3–6. arXiv lists v1 only.
- The repository's main checkout (branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD now `19c2d28`): FOCUS, PLAN-S, PREREG, BRIEF, ADD, SPEC, RS, PAPER, the re-plan PROPOSAL, the literature sweep, recipes B, S and G, and the engine lines that the draft cites.

---

## 0. Result

| Severity | Count | Meaning |
|---|---|---|
| Critical | 0 | A wrong setting, number or rule would enter the frozen record with no flag |
| Major | 7 | Fix before the lead edits the text in. It changes a source, a number, a deadline or who decides |
| Minor | 13 | A citation, a unit, a cost detail or a missing sentence. No rule changes |
| Nit | 5 | Wording or rounding |

**Main points.**
1. Every setting that the draft attributes to the two papers is correct, apart from five small citation slips (m5). This covers the equations, the β values, the threshold, the layer counts, the LoRA settings, the model pairs, the optimizer, the warmup, the epochs and the tables.
2. The τ_L numbers are correct. I ran TLC again. Its output is byte-identical to `tau_l_check.out.json`. I also recomputed every derived number in §L.4.
3. The main problems are these:
   - The draft's sources are stale. ADD changed at 21:33 UTC (M1).
   - The blinding line misses two Gate B values (M2).
   - Some items are marked LEAD, but they are user scope or spend items by the draft's own Marks rule (M3, M4).
   - The greedy-generation size is wrong: 468 prompts, not 300 (M5).
   - Several items have a W1 deadline but sit in the S1 record (M6).
   - The proposed c0 job is a re-run of a completed Gate B arm (M7).

---

## 1. What I checked and found correct

**Safe LoRA (P).**
- Eq. 1 (V = W_aligned − W_unaligned) and Eq. 2 (Ĉ = V(VᵀV)⁻¹Vᵀ) are correct.
- §3.4: the fast form C = VVᵀ/‖V‖_F, and 8.6e-3 s against 2.1714 s on an H100.
- Eq. 3: the threshold is strictly below τ. §3.2 and §4.1 give the top-K alternative.
- §3.1, the last paragraph: base plus chat or instruct is the default pair.
- Fig. 1 caption: the update is ΔW = ABᵀ, and the mapped weights are C·A·Bᵀ (so A′ = C·A). They are added to W_aligned.
- §4, Experiment Settings: LoRA rank 8 on q_proj and v_proj.
- §4.1: τ = 0.35 maps 7 layers (Llama-2, Dialog Summary), and Llama-3 maps about 35%. §1 gives "about 11%" and "up to 35%". §4.2 gives about 11%.
- Fig. 4 has 64 points. The 7 red points sit in the first ~12 layers.
- Fig. 3 at (0.8, 100%) shows F1 ≈ 33.5%. Table 3 gives 34% for the untuned model. So the claim in R.1.2 holds.
- Table 1's columns are C, Ĉ, C, Ĉ (LaTeX alt text). Its PureBad C column (1.055, 6.34) equals the Safe LoRA row of Table 2.
- Table 4: keyword ASR 86.67% → 6.67%. Table 3: the Llama-3 benign row 49.04/1.16/7.27 → 47.64/1.15/6.97.
- App. A.4: S in Eq. 5 is a sum. No table has error bars. NeurIPS 2024 and v2 are right.

**Qi et al. (P).**
- Eq. 3, and Eq. 4 with Δ_t = log π_aligned − log π_θ in the softplus form.
- Eq. 5: the gradient weight w_t = 2σ(β_tΔ_t), and w = 1 at the start. Footnote 6 explains the factor 2/β_t.
- §4.2 and the Table 3 caption: β_1 = 0.5, β_t = 2 for t = 2–5, β_t = 0.1 for t > 5.
- App. A.5.1: AdamW (0.5, 0.999); LR 2e-5 for Llama-2-7B-Chat and 5e-6 for Gemma; batch 64; a linear warmup over the first 10 steps for Constrained SFT.
- App. A.5.3: 3 epochs on each benign set.
- App. A.2: HEx-PHI with a GPT-4-Turbo judge, and ASR is the share of score 5.
- Table 3: GSM8k utility 41.7 → 37.4, and "3 rounds".
- Table 5: all nine benign ASR cells that the draft quotes (Samsum 23.4/3.8/23.1/3.2; SQL 15.4/3.3/2.0/3.2; GSM8k 3.3/2.9/3.1/2.0). Table 3 pairs SFT without warmup with the constrained loss with warmup.
- Table 6: the combination gave no consistent gain.
- App. D.1: the small-β and large-β limits, including 2·max(Δ, 0).
- The paper does not mention LoRA.

**Repository (R, C).**
- τ_L and all §L.4 arithmetic. The values are s = 0.0023749, τ_L = 0.0067171, the 6-against-6 SE = 0.0013711, the σ/s interval 0.5207–6.2847, P(s < 0.5σ) = 0.221, P(s < σ) = 0.632, τ_L/SE = 2√6 = 4.90, 0.43%, 1.21%, and recipe G 1101 at 9.99 τ_L.
- The Gate A O counts 17, 4, 6 and 4 (`summary.json`).
- The e1 fingerprints `aad79060…`, `7c9111c2…` and `b1ad020b…`, and the q fingerprint of 1101, `322d737a…` (`COMPLETE.json`).
- The wave-0a ledger seconds and their SHA-256 prefixes (§C.2 table). The job slots 48.9, 49.0 and 43.5 min. The overheads 18.9 and 26.0 min.
- REC: r 64, α 128, dropout 0, 7 modules, 48,234,496 LoRA values (= 112 matrices of 2048 and 8192 shapes), AdamW (0.9, 0.999), LR 1e-4 constant, batch 4 × 32, clip 1.0, max length 3,072. REC and S have identical `model` and `train` sections.
- FOCUS entries: D5 = (a), ICML 2027, the B+Qi decisions, Safe LoRA, the "worse" label (decided by the user at 18:31 UTC on 8 Oct; "adverse" wording), the τ grids, the seeds, the cost rules and the $10/h limit.
- PLAN-S lines 30, 95, 102, 111, 114–119, 123–127, 149–155, 199–212 and 222–233.
- BRIEF lines 11, 45 and 65, REQ-13, REQ-19 and REQ-21. ADD L13, L15 and L16, and ADD:293.
- PAPER lines 117, 195, 198 and 222.
- The code lines cited: `config.py`:12-13, :33-36 and :539-540; `engine.py`:218-245; `textproc.py`:173-183; `prepare_task.py`:81-84; `runner.py`:630-632, :838-846 and :961-964.

**Internal arithmetic (C).**
- K = 12 is 10.7% and K = 39 is 34.8%.
- The momentum shares are 47/30/16% and 33/14/3%.
- The warmup shares are 26% and 1.7%.
- The regeneration cost is 0.094 FRE ($0.14).
- The B+Qi totals are 6.2–6.3 FRE, $9.1–9.2, $10.6–10.8 and $13.3–13.4.
- LQ5's figures ($20–25 and $25–31) are correct. So are the norm-matched control (2.8 FRE, about $4) and the certificate pod ($1.3–1.5 for 45–50 min).

---

## 2. Major errors

### M1. Stale sources: ADD changed, and a new lead ruling bears on the reference list
- **Where:** draft line 12 ("HEAD is now `fc85fda`"; "Every file below has the same SHA-256 as at d79f641") and line 24 (ADD `1d4e42a2…`). Also §R.0.1, line 59, and the [USER] list.
- **Evidence (R):**
  - The main checkout is now at `19c2d28`. Commits `2b1dfa7` (the literature sweep) and `19c2d28` were both made at 21:32:41–21:32:55 UTC. That is before the draft's stated start, 21:36 UTC.
  - ADD's SHA-256 is now `114776482a3287dd…`. At `fc85fda` it was `1d4e42a2092d2f3e`.
  - The new ADD §5 (21:33 UTC), item 4, says that two candidate new references are a scope decision for the user: the "opening hold" first-token loss and "Safety at One Shot". It also says: no change before the user decides.
  - The sweep (`writing/paper/2026-10-17-lit-sweep.md`:101-103, :138, :334) says that the opening hold is close to B+Qi, because both are first-token constraints. It asks the lead to add each one, or to say why not, before stage 1.
  - FOCUS is unchanged (`23e3da8f…`).
- **Fix:**
  - Update the source table: HEAD `19c2d28`, ADD `114776482a3287dd…`. Add the sweep file and §5 to the list.
  - In §R.0.1, add one row: "Candidate references (opening hold; Safety at One Shot): a pending user scope decision (ADD §5 item 4); the list is not final".
  - Add **UQ7**: the user decides whether either candidate becomes a reference before the stage-1 freeze. If the opening hold is added, B+Qi's role and wording ("the first-token constraint reference") must be read again.
  - Keep the one-example patch row as it is until the user decides.

### M2. The blinding line misses r_j and P4, so "Not read: any Gate B arm's U" cannot stand as written
- **Where:** §B, lines 389–395.
- **Evidence (R):**
  - FOCUS:82 (the 16 Oct 00:25 UTC noise-gate entry) prints r_j = U(a0, j) − U(R_j, j) = +0.67, +2.50 and +4.33 pp. It also prints P4's mean r = 2.5 pp (SE 1.06). These numbers give each Gate B R arm's U directly, because Gate A's a0 U values are known.
  - RQ cites "FOCUS:77, :82" as the place where the noise gate was seen (RQ line 147).
  - ADD §3 (4) already requires REQ-21 (m) to list r_j and P4 as values that were seen.
  - The draft's list names only the 13:21 UTC entry (FOCUS:77). That entry does not hold r_j.
- **Fix:**
  - Add to "What the writers read": "the noise-gate values in the 16 Oct 00:25 UTC FOCUS entry: r_j (+0.67, +2.50, +4.33 pp) and P4's mean r (2.5 pp, SE 1.06), at least for RQ".
  - Change "Not read: any Gate B arm's U" to "Not read: any Gate B arm's O, task loss, ARC or answer, and no U beyond the printed r_j".
  - Ask the SL and QI writers whether they read that entry. If the answer is unknown, list it as possibly seen.

### M3. LQ21 lets the lead drop a user-approved mandatory reference
- **Where:** R.2.8, line 212 (LQ21).
- **Evidence (R):**
  - The user approved the Qi arm ("Ok", FOCUS 8 Oct 17:36 UTC item (4), FOCUS:225).
  - The user's 9 Oct 10:01 UTC decision lists it as mandatory (FOCUS:151).
  - The user decided "no warmup" (FOCUS:125 item (10)).
  - The draft's own Marks define a scope change as a [USER] item (line 9).
- **Fix:**
  - Keep the binding check as a pre-freeze, outcome-free statistic.
  - Change the action: if the check shows that B+Qi equals recipe B by construction, the lead **proposes** a change. Examples are B+Qi with Qi's optimizer (β1 0.5) or G+Qi. The **user** decides at the freeze.
  - Move this item into the [USER] list (UQ3 can absorb it).

### M4. Two spend or scope changes are marked LEAD: the second Safe LoRA point (LQ9) and the block move (LQ5)
- **Where:** line 114 (row 10), line 123 (LQ9), line 84 (LQ5), and §Q.
- **Evidence (R, C):**
  - FOCUS:152 (the user's 9 Oct decision entry) gives Safe LoRA as "one evaluation per seed (about $1–2 each)". A second point doubles Safe LoRA's evaluations. It adds 3 evaluations, about 2.8 FRE ≈ $4.1, or about $6 with one pod's overhead and the contingency.
  - LQ5 would move about $25–31 into block A. It would change PLAN-S:222-223, which the user approved as the basis (FOCUS:236).
  - The draft routes smaller optional spends to the user: UQ6 (about $4) and UQ3 (about $6–7). It routes these two to the lead. That is inconsistent with its own Marks (line 9: "a spend, a scope change").
- **Fix:** do one of these two things.
  - (a) Mark both as [USER] items, each with its default. LQ9's default: K = 39 only, as SPEC §6.5 and FOCUS:152 suggest; K = 12 is offered for the extra spend.
  - (b) Record in the text that the lead reads the user's "stop asking me for approval" (FOCUS:76) as covering these spends, and say why. The user then sees it at the freeze.

  Also, the re-plan PROPOSAL (`fc85fda`, line 71; not adopted) costs Safe LoRA at 3 evaluations. Say which count the plans use.

### M5. The greedy evaluation has 468 prompts, not 300. This makes three cost statements wrong
- **Where:**
  - line 267, §C.4 ("greedy generation (200 harm + 100 over-refusal prompts)");
  - line 272, §C.5 LQ27 option (a) ("about 565 s");
  - line 276, §C.6 ("the full evaluation generates 900 answers …; 200 sampled answers are 22%").
- **Evidence (R):**
  - Each wave-0a ledger's `generate` stage has `prompts` = 468, and its `guard` stage has `items` = 468.
  - PLAN-S:30 says "greedy generation 1,750 s for 468 prompts".
  - `runner.py`:627 gives four generation kinds: safety, arc_generation, harm and overrefusal.
  - The draft's own script (`prereg_numbers.py` in the session scratchpad) divides the greedy time by 300.
- **Correct numbers (C):**
  - With equal time per prompt, 100 greedy over-refusal answers cost 1,694/468 × 100 ≈ **362 s** (median arm; range 332–371 s), not 565 s. Their guard adds about 17 s.
  - C-lean with option (a) is then about 480 + 11 + 362 + 17 ≈ 870 s ≈ 0.30 FRE.
  - The full evaluation generates **1,068** answers (468 greedy and 600 sampled). So 200 sampled answers are **18.7%** of them. The 200 harm prompts are 43% of the 468 greedy prompts.
- **Fix:**
  - §C.4 "In": "greedy generation of all 468 evaluation prompts (200 harm, 100 over-refusal and 168 of the other generation kinds)".
  - LQ27 (a): replace 565 s with about 360 s (330–370 s), plus about 17 s of guard.
  - §C.6: replace the 900/22% sentence. The ratio does not reconcile the two definitions. LQ29's definition does that. Keep LQ29 and say that "20%" in PLAN-S:202 is a rough size.

### M6. W1 items sit in the S1 record
- **Where:** line 5 ("Text for three sections of the stage-1 pre-registration … (L) the limits"); §L; R.2.10 Q-P1; §C.5–C.6.
- **Evidence (R):**
  - BRIEF REQ-21 (the W1 record, before Gate B wave 1) holds these items:
    - (c): the four labels, the Holm family of the "worse" label for O and task loss, and the label order (U4);
    - (e): the limits, namely O against the untuned model, the τ_O grid, τ_L from REQ-19, O-ext (U8) and the skill measure (U6);
    - (i): "SPEC F4 as a B+Qi prediction risk" (this is Q-P1);
    - (m): the blinding line.
  - ADD L15 (3) and FOCUS:78 U3 (a) put the selector's predictions in units of c0 under both conventions. REQ-18's predictions are W1. So C-lean's content (LQ27) and c0's definition (LQ29) must be fixed before those predictions are frozen.
  - PLAN-S:239: rules approved after any unit outcome are "post-Gate-B exploratory".
- **Fix:**
  - Tag each item W1 or S1.
  - Move §L (LQ36–LQ44), Q-P1 and §B into the REQ-21 record, with the W1 deadline.
  - Mark LQ27, LQ29 and LQ31 as "before REQ-18's predictions are frozen".
  - Keep §R (except Q-P1) and the rest of §C as S1 (D3).

### M7. The c0 job proposed in LQ30 is a re-run of a completed Gate B arm
- **Where:** line 277 (LQ30); compare line 86 (R.0.9: "never re-run a completed job").
- **Evidence (R, I):**
  - PREREG:108 says never re-run a completed arm.
  - The claim "its sampled answers … repeat R_1's first sample" assumes batch-invariant sampling. The lean job's sampling batches hold other prompts than R_1's batches (200 answers against 600, batch 32). So the outputs may differ. If they differ, the job makes new outcome data for a Gate B arm. The draft does not check this.
- **Fix:**
  - State that the c0 job is a cost-measurement job, not an attempt of R_1 under PREREG:108.
  - State that only its ledger is read. Its evaluation files are sealed by hash and are never read for any estimate.
  - Alternatively, run the lean job on a Gate A a0 seed, whose outcomes are already known. This changes the training from 33 to 38 steps (+26 s); record that.
  - The lead chooses one of these. Then LQ30 can stand.

---

## 3. Minor errors

**m1. The Safe LoRA dollar totals include the a0 regeneration, but the text says it is reported apart.**
- **Where:** line 153 (R.1.10) and line 297 (§C.9).
- **Evidence (C):**
  - $10.1 and $12.6 (two points), and $5.3 and $6.6 (one point), come out only if 3 × $0.14 of regeneration is added (`prereg_numbers.py` adds it).
  - The script also counts pods without the 3 regeneration jobs. With them, two points need 3 pods at 4 jobs per pod.
- **Fix, choose one form:**
  - **Marginal:** evaluations plus their own pods. Two points: 5.6 FRE, $8.1, $9.7 with 2 pods, **$12.1** × 1.25. One point: $4.1, $4.9 with 1 pod, **$6.1** × 1.25.
  - **With regeneration:** two points: $10.9, **$13.6** × 1.25 (3 pods). One point: $6.0, **$7.5** × 1.25 (2 pods).

**m2. "≈ $0" for the transform breaks PLAN-S:203.**
- **Where:** line 295.
- **Evidence:** PLAN-S:203 allows "≈ 0" only below 0.01 FRE. The draft gives "< 0.03 FRE".
- **Fix:** write "< $0.05 (< 0.03 FRE; the record gives the measured value)".

**m3. The C-lean column mixes units.**
- **Where:** lines 294–295 ("same").
- **Evidence:** other rows give C-lean in c0. In c0, regeneration is 277 s / about 480–491 s ≈ **0.57 c0**, and the transform is < 0.18 c0.
- **Fix:** give these values, or write "0.094 FRE (≈ 0.57 c0)".

**m4. LQ20's evaluation part has no cost.**
- **Where:** line 210 and line 300.
- **Fix:** an extra evaluation of one X unit on X′ adds about 0.93 FRE ≈ $1.36. With it, the certificate pod is about $2.7–2.9.

**m5. Five paper-citation slips (P).**
- (a) Line 186, R.2.5 row 8: "3 benign epochs" is App. A.5.3, not A.5.1.
- (b) Line 169: β1 = 0.5 applies to "all the fine-tuning experiments" of App. A.5. The data-augmentation runs (App. A.3) used AdamW's default settings. Replace "all their runs" with "all their fine-tuning-attack and benign runs (A.5.1)".
- (c) Line 170 ("theirs, which had more than 600 steps"): App. B gives more than 600 steps for SQL Create Context and Samsum only. GSM8k is about 350 steps (I: 7,473 training rows / 64 × 3 epochs), so 10 steps are under 3% there. Write "under 3% of theirs (more than 600 steps on Samsum and SQL; App. B)".
- (d) Line 114, row 10: "both chosen … from outcome sweeps (Fig. 3)". Fig. 3 is the Llama-2 Dialog Summary sweep only. The paper shows no sweep for Llama-3's 35% (§1, §4.1). Write: "11%: τ = 0.35 on the Llama-2 sweep (§4.1, §4.2, Fig. 3); 35%: stated for Llama-3 with no sweep shown (§1, §4.1)".
- (e) Line 32: "§4.1 (… about 11% and 35%)". "About 11%" is in §1 and §4.2. §4.1 gives 7 layers and about 35%.

**m6. The deviation table omits a sentence in the paper's §3.4.**
- **Where:** R.1.2 and R.1.3 row 6.
- **Evidence (P):** §3.4 says that Ĉ "could often perform better" (Safe LoRA, Hsu et al., §3.4). Table 1 and Table 2 favour C.
- **Fix:** add one sentence to row 6. "The text of §3.4 favours Ĉ, but the tables and the code use C. Ĉ is degenerate on our shapes, so we use C."

**m7. The record-correction item 3 contradicts itself.**
- **Where:** line 229.
- **Evidence:** it lists PLAN-S:149 as a record to correct. Then it says that PLAN-S:149 is about the four data-method repositories.
- **Fix:** remove PLAN-S:149 from the list. Keep SPEC F8 and SPEC §6.5 item 3.

**m8. A wrong path.**
- **Where:** line 256.
- **Evidence:** `tmp/gi-vi-wave0b/recost/NOTES.md` is in the main checkout, not in "this worktree".
- **Fix:** write "(main checkout)".

**m9. FOCUS is cited by line number.**
- **Evidence:** ADD §3 (3) says to cite FOCUS entries by title, because FOCUS changes.
- **Fix:** in the text for the pre-registration, cite each FOCUS entry by its title and UTC time, for example "FOCUS, USER DECISIONS 2026-10-09T19:37 UTC, item (10)". Give line numbers only together with the FOCUS hash.

**m10. The a0 regeneration has no failure path.**
- **Where:** R.0.7 and LQ4.
- **Evidence:** PLAN-S:233 says that if the check fails, a0 1101–1103 are re-run on X, as 3 more runs paid from the contingency.
- **Fix:** add this. If a regenerated e1 fingerprint differs from the Gate A unit's, the eval-only references wait. a0 at that seed is re-run on X with a full evaluation. The references use the new unit, and the change is recorded.

**m11. The cap of 4 jobs per pod is cited as decided for stage 1.**
- **Where:** line 86 (LQ7).
- **Evidence:** FOCUS:125 item (1) fixes `MAX_ARMS_PER_POD` = 4 "for the whole Gate B path". For stage 1 it is RS B15's plan.
- **Fix:** LQ7 also confirms the cap itself for stage 1.

**m12. The builder is not named.**
- **Where:** line 42 (LQ1).
- **Evidence:** FOCUS:154 says "Specialized builds it with tests, reviewed before use" for the Safe LoRA work.
- **Fix:** LQ1 names the builder, or records the change.

**m13. A code line range is wrong.**
- **Where:** line 132.
- **Evidence:** the fingerprint refusal is at `engine.py`:452-453. The range 440-450 holds only the file-hash check.
- **Fix:** cite `engine.py`:441-453.

---

## 4. Nits

- **n1.** Line 317: "binds only for arms that over-refuse about as much as the untuned model". It should be "more than the untuned model": O above 19%, 22% or 27% at τ_O = 2, 5 or 10 pp.
- **n2.** Line 324: the low end of the rough O MDE is 3.5 pp, not 3.4 pp (C). The formula is 2.80 × √(0.05 × 0.95 / 300). RQ has the same figure.
- **n3.** Line 256: "Training is 7.6–8.4%" and "Generation is 80–82%" are shares of the engine-ledger total. FRE uses the job slot, and of the job slot the shares are 7.5–8.3% and 79–81%. Name the denominator, also in §C.10's fixed sentence.
- **n4.** §C.5 says that a lean R arm is about 480 s. The c0 figures in R.1.10, R.2.11 and §C.9 use 491 s, because the script adds the 11 s task-loss pass. Use one value.
- **n5.** Line 263: PLAN-S:201 does not say when FRE is computed. Replace "PLAN-S's literal wording" with "an open reading of PLAN-S:201".

---

## 5. Notes (not errors)

- The re-plan PROPOSAL (`fc85fda`, not adopted) uses an evaluation-only job ≈ 0.85 FRE. The draft uses 0.93 FRE, measured from wave 0a. Reconcile them before either plan is adopted.
- The literature sweep names Safe LoRA follow-ups for related work: Safe Delta 2505.12038, SaLoRA 2501.01765, and a coordinate-mask ICLR 2027 submission. The draft has no related-work section, so this is only a pointer.
- QI's §0.1 table gives C-lean in "FRE" (1.2–1.3). The draft correctly uses c0. Do not copy QI's unit.
- The disk was full while I wrote this report (about 120 MB free). One write failed with "no space left on device". I removed only my own downloaded paper copies to free space. Other workers' writes may fail too.

---

## 6. Not verified

- **Code claims (C in the draft).** I did not read the official code: `IBM/SafeLoRA` or `Unispac/shallow-vs-deep-alignment`. The brief allowed arxiv.org only. These claims are: C only; the top-K mode can exceed K; rounding to 5 decimals; K = 10 and τ = 0.5 as defaults; the 1e-3 floor; `warmup_steps = 10`; the HF linear decay; max length 512; and the licences (Apache-2.0 and MIT).
- **Hugging Face metadata (H).** I did not read the Hub. These claims are: base `a1847dff`, 5,939,687,552 bytes, the LFS hashes, not gated; and Llama-3.2-1B `4e20de36`.
- **The composition of the 468 greedy prompts by kind.** Reading it needs the bank files, and I did not open them.
- **Batch invariance of sampling (M7).** I did not test it.

---

## 7. Commands run (all exit 0, except the first report write)

- `date -u` (three times).
- `git branch --show-current`, `git rev-parse`, `git log`, `git status --short`, `git diff --stat fc85fda 19c2d28`, `git diff fc85fda 19c2d28 -- <ADD>`, `git show <rev>:<file> | shasum` and `git show --stat fc85fda` (main checkout, read-only).
- `shasum -a 256` of the sources and ledgers.
- `curl` of the arXiv HTML (2405.16833v2 and 2406.05946v1), the Safe LoRA PDF and both abstract pages. Each went into its own new scratchpad folder.
- `python3 -I` on my HTML-to-text script; `pdftotext`; `pdftoppm` of PDF page 9.
- `grep`, `sed` and `awk` on FOCUS, PLAN-S, PREREG, BRIEF, ADD, SPEC, RS, PAPER, the re-plan, the sweep and the engine code.
- `python3 -I` reads of the recipe configs, the wave-0a ledgers (stage, seconds and counts only), Gate A `COMPLETE.json` (fingerprints) and `summary.json` (over-refusal counts).
- `python3 -I tau_l_check.py` with its output in my scratchpad: byte-identical to `tau_l_check.out.json`.
- `python3 -I` of my arithmetic script.
- `df -h`. Then `rm` of my own downloaded HTML, PDF and page images, after the first write of this report failed with ENOSPC.

**Evidence paths.** All are in the session scratchpad `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/c519cf93-2a82-40cd-bff7-64852d1f6d17/scratchpad/`:
- `vr-txt/sl.txt`, `vr-txt/qi.txt` and `vr-txt/sl-pdf.txt` (paper text);
- `vr-img/f3-09.png` (the Fig. 3 crop);
- `vr-scripts/arith.py` and `vr-scripts/tlc-rerun.json`.

These files are temporary and outside the repository.

**Files written:** this report only.
