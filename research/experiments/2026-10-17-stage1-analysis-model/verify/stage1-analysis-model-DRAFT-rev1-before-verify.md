# Stage-1 pre-registration: the analysis model and the testing family (DRAFT, revision 1)

**Status: DRAFT for the main-study lead (General Implementation VI). It adopts nothing.** It authorizes no run, spend, download or agreement. It changes no frozen Gate B rule. The lead edits, accepts or rejects each item. Items marked [USER] or [USER-CONFIRM] go to the user.

- **Written** 2026-10-16 from about 23:00 to 23:42 UTC (17 Oct IST) by an Opus worker. Clock checked with `date -u` at 23:01, 23:27, 23:29, 23:35 and 23:41 UTC. Nobody has checked this draft yet.
- **Read-only on the repository.** No repository edit, commit, pod, spend or download. I opened no `selector.jsonl`, no `hidden/`, no held-out file, and no wave-0b `rows.jsonl` or `groups.json`. I read no Gate B unit arm. I printed no prompt, answer or prompt id.
- **Files written** (this folder only): this file; `stage1_model_sim.py` with `stage1_model_sim_out.txt`, `stage1_model_sim_results.json` and `stage1_model_sim_run.log`; `stage1_numbers.py` with `evidence/stage1_numbers.json` and `evidence/stage1_numbers_stdout.txt`.
- **Labels.** **R** = read in a source (the source follows). **M** = measured or computed here (the script follows). **E** = estimate from a simulation or a cost model (the basis follows). **I** = inference, proposal or judgement.
- **Marks.** **[LEAD]** = the lead decides. **[USER]** = the user decides: it changes a user decision or a frozen input, costs new money, needs a download, or changes a scientific target. **[USER-CONFIRM]** = an "ambitious default with a pre-set fallback" ladder, under the user's relayed standing rule ("keep the more ambitious one always but always open to fallbacks"; R: memory note of 17 Oct; RB "Labels, marks and deadlines"). The lead's chat has not confirmed the rule. Until it does, treat each [USER-CONFIRM] ladder as a [USER] question with the default as the recommendation (as RB does).
- **Deadlines.** **W1** = before Gate B wave 1 (latest start 27 Oct). **S1** = before the stage-1 freeze (latest start of stage-1 block A, 3 Nov). (R: RB "Labels, marks and deadlines", from REPLAN §5; I did not read REPLAN.) **W1-P** = W1, and before REQ-18's predictions are frozen.

## Short names

| Name | Source (main checkout, HEAD `072e3ae` at 23:30 UTC) | SHA-256 prefix |
|---|---|---|
| FOCUS | `research/FOCUS.md` | `23e3da8f893e8135` |
| PLAN-S | `research/review/2026-10-08-sharpened-direction-DRAFT.md` | `6ff3ff2b15bc4295` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (revision 5, frozen) | `5c97cce78cfad2c1` |
| NG | `research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json` (and `noise-gate-post-wave0b.json`, `889f574967cfffa4`) | `4b817f73d968b89a` |
| BRIEF | `.ai/briefs/stage1-commitments-build-20261016.md` | `12cbf46318728d32` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` | `114776482a3287dd` |
| MRA | `writing/paper/2026-10-17-mock-review-A-methods.md` | `ff0e4382d542f85e` |
| REF | `research/experiments/2026-10-17-stage1-prereg-references/stage1-prereg-references-DRAFT.md` (sibling draft, revision 2) | `5835caaea2204674` |
| RB | `research/experiments/2026-10-17-stage1-review-b-rulings/review-b-rulings-DRAFT.md` (sibling draft; it names this file "the analysis-model draft" and passes it AMD-1 to AMD-8) | from commit `072e3ae` |
| CK-2 | `check-W2-W5.md` (this folder) | `50c285262c6ef797` |
| CK-3 | `check-W3-W4-W12-W13.md` (this folder) | `792b7be7b802ca33` |
| CK-11 | `check-W11-other.md` (this folder) | `0e424cebb1fda4dc` |
| SIM | `stage1_model_sim.py` → `stage1_model_sim_results.json` (this folder; new) | `581e9bd18de79336` → `ccf202311899370f` |
| NUM | `stage1_numbers.py` → `evidence/stage1_numbers.json` (this folder; new) | `2c8f432b7be70ab5` → `80ae7caa7406a7a6` |

REF and RB were not in my brief's source list. I read them because they were committed to main during this work (`778c464`, `072e3ae`) and they rule on the same items. §I lists where this draft departs from them.

---

## 0. Short answer

| Section | Proposal (short) | Key number | Mark | Deadline |
|---|---|---|---|---|
| **A. Primary model** | **HB:** the estimate is the mean of the seed-matched differences on the common seeds. Its variance is a seed part from a seed-blocked model with **one residual variance per arm** (REML), plus a crossed prompt part. Satterthwaite df. The 8 Oct unpaired pooled analysis is a reported sensitivity. | Valid in all 19 simulated scenarios: family-wise 3.0–4.6% (nominal 5%), worst single contrast 0.68–1.08% (nominal 0.83%). MDE (P1, 80%) ≈ 1.9 × σ_pair: **3.5 pp** at the wave-0a pair SD, 7.1 pp if the pair SD is 3.75 (M: SIM) | [LEAD] model; [USER] it replaces PLAN-S:102's "seeds are not paired" | W1 |
| A.6 R's two extra seeds | Under HB, R_1108 informs nothing and R_1101 informs only the variance fit. **Move R_1108's run to a0 at seed 1107** (same 50 runs). | P4's MDE falls from 4.0 to 3.5 pp at wave-0a noise, and from 8.0 to 7.1 pp at pair SD 3.75 (M: SIM, D1) | [USER] (a user-approved seed list) | W1 |
| **B. Family** | One closed graphical family Φ over 24 hypotheses: U_k (two-sided), "adverse on O" O_k and "adverse on L" L_k (one-sided), and **F_k = feasible at the primary τ_O = 5 pp** (one-sided). Start weights 0.15 per U_k, 0.1/12 per O_k and L_k, 0 per F_k. Equivalence stays outside Φ, per comparison, with a familywise grade beside it. | First U step 0.75% (Holm: 0.83%); U MDE +1.6%. Family-wise 4.9% under the global null (M: NUM) | Φ [USER] (it changes "Holm over 6"); wiring [LEAD] | W1 |
| **C. Margin** | Keep δ = 5 pp. It is 11.1% of E = 45.1 pp (10.4–11.5% by seed). For another family: δ_fam = 0.111 × that family's Gate A E. | At wave-0a noise under HB: Holm power at 5 pp 0.99; P(better \| 5 pp) = 0.50 by the rule; "better" needs 5.65 pp for 80%; P(equivalent \| 0) = 1.00 (M: SIM) | δ unchanged [LEAD]; transport rule [USER] | W1 |
| **D. References** | A repair "beats" a reference if U is lower (one-sided 5%) and O and L are non-inferior (margins 5 pp and τ_L). Paired by seed, HB form. The adapter-scaling curve is read at a conservative matched-L grid point. "Dominates" = beats all, an IUT; six IUTs in family 1b, Holm at 5%. **Ambitious default: SP, scaling and Safe LoRA on all six a0 adapters, plus λ = 0.9; recipe G at six seeds.** | +$22.4–24.8 (six seeds) + $11.5–12.9 (λ = 0.9) + $8.0–8.3 (recipe G 1104–1107) (M: NUM, with pod overhead and × 1.25) | Rules [LEAD]; seeds and spend [USER-CONFIRM] | S1 (spend); W1 (rule text, if the lead wants it fixed with the family) |
| **E. Over-refusal** | Primary τ_O\* = 5 pp. O uses the same crossed model as U (prompts random). So REQ-19's MDE is about 11 pp and the 8 Oct O-ext rule opens. **Ambitious default: 500 prompts (dev 100 + O-ext 400).** Fallback: the dev 100, every O sentence "on these 100 prompts". | An add arm at the untuned level is shown feasible inside Φ with probability 0.06–0.33 on 100 prompts and 0.43–0.99 on 500 (M: NUM) | τ_O\* [USER]; error model [LEAD]; O-ext bank and spend [USER-CONFIRM] | W1 |
| **F. Coherence** | No arm or seed is dropped. Arm-pooled Gate A bar. A failing repair reads "worse (answers do not end)"; a failing comparator makes its contrasts "inconclusive (comparator fails)". | a0 fails the screen on 3.7–7.0% of answers (R: CK-3 §5.2) | [LEAD] | W1 |
| **G. Positive control** | CK-11's F1–F8 at $0, with row AUC as the placement statistic. **Ambitious default: two more plant locations (F9) and a second, benign-topic plant (F10).** Fallback: the relocation replay (F6) and the limited claim (F1). | F9 $34–70; F10 about $15–30 plus text (R: CK-11) | F1–F8 [LEAD] (F1 wording [USER-CONFIRM]); F9, F10 [USER-CONFIRM] | W1 |

**The one consequential trade-off for GPT (I).** HB costs power when the same-seed correlation is low. If the pair SD is 3.75 pp (ρ = 0), HB's P1 MDE is 7.1 pp. The 8 Oct analysis gives 5.2 pp there, and the pooled blocked model (b3) gives 5.6 pp. But both of those fail when arms differ in seed variance (up to 11.8% and 7.8% family-wise). HB is the only analysis here that keeps every contrast near its nominal level in every scenario. Its MDE is set by the pair SD, which Gate B measures, so its power is known before stage 1 starts. I recommend HB. §A.10 gives the numbers.

---

## A. The primary analysis model

### A.1 The outcome per cell (R, I)

- One cell = one arm at one seed. The eight primary arms are a0, R, A1, L1, H1, S1, S3 and S4.
- For prompt p (the 200 dev harm prompts) and sample i (3 per prompt), Y = 1 if Qwen3Guard labels the sampled answer Unsafe, else 0. This is Gate B's plain U (R: PREREG §6). The G3 corners (unscored answers against the claim; Controversial counted Unsafe) and coherent-only U (G2) are sensitivities (§A.7).
- Prompt share: y(a, j, p) = (1/3) Σ_i Y. Cell value: U(a, j) = 100 × (1/200) Σ_p y(a, j, p), in pp.

### A.2 The estimator (I)

For contrast k with comparator c and repair m:

> **Λ̂_k = (1/J_k) Σ_{j ∈ S_k} [U(c, j) − U(m, j)]**

- S_k = the seeds at which both arms ran. J_k = |S_k|. A positive Λ̂ means the repair restores more safety.
- Under the approved seed plan (D0: a0 1101–1106, R 1101–1108, method arms 1102–1107): S_k = 1102–1107 for P1, P2, P3, P5 and P6 (J = 6), and 1102–1106 for P4 (J = 5).
- Under D1 (§A.6): J = 6 for every contrast.
- The comparator for each contrast is as frozen: P1–P3 against R; P4 against a0 (P4 = U(a0) − U(S1)); P5 and P6 against S1 (R: PLAN-S:114).

### A.3 The variance (I)

V_k = V_seed,k + V_prompt,k. SE_k = √V_k.

**Seed part.** Fit this model to every cell of the eight primary arms (50 cells):

> U(a, j) = μ_a + s_j + e(a, j), with Var e(a, j) = σ²_a (one variance for each arm)

- μ_a and s_j are fixed effects (arm and seed). The seed effect s_j absorbs everything that arms at one seed share: the adapter initialization, the row order and the sampling streams (R: CK-2 §2).
- Fit the eight σ²_a by REML. Use Fisher scoring on log σ². Start at each arm's residual mean square. Stop when the largest step is below 10⁻⁶, after at most 25 steps. Floor: 0.01 pp².
- Then **V_seed,k = (σ̂²_c + σ̂²_m) / J_k.**
- Only the eight primary arms enter this fit. Reference and secondary arms never do, so the primary variance does not depend on what else is funded.

**Prompt part (prompts crossed with seeds).** Form the J_k × 200 table D(j, p) = y(c, j, p) − y(m, j, p). From its two-way analysis of variance take MS_P (199 df) and MS_E (199 (J_k − 1) df). Then

> **V_prompt,k = max(0, MS_P − MS_E) / (200 J_k) × 10⁴** (pp²)

This term carries the arm × prompt interaction. It makes the inference reach new harm prompts from the same population, not only these 200 (MRA W2 item 3). Without it, the false-positive rate reached 8.0% and 14.6% in the two scenarios with a real arm × prompt term (M: SIM, HB0 in G1 and G2).

### A.4 The df rule (I)

- df_seed,k = 2 V²_seed,k / Var̂(V_seed,k), with Var̂(V_seed,k) = (I⁻¹_cc + I⁻¹_mm + 2 I⁻¹_cm) / J²_k. Here I is the REML information matrix of (σ²_a) at the estimate.
- If MS_P > MS_E, the prompt part adds q = (MS_P/(200 J_k) × 10⁴)²/199 + (MS_E/(200 J_k) × 10⁴)²/(199 (J_k − 1)). Else q = 0.
- **df_k = V_k² / (V²_seed,k / df_seed,k + q).** (Satterthwaite.)
- Simulated median df: about 8 for P1 (10th percentile 5.6) and 7 for P4 under D0 (M: SIM).

### A.5 Tests and intervals from the model (I)

- t_k = Λ̂_k / SE_k, against Student t with df_k.
- U_k: the two-sided p-value. It enters the family Φ (§B).
- The 90% interval Λ̂_k ± t(0.95, df_k) SE_k serves TOST "equivalent (per comparison)". The 98.33% interval (α/6 per side) serves "equivalent (familywise)" (§B.4).
- Every interval in the paper's tables and Figure 1 is this interval. Table 2 shows the 90% interval first and the label beside it (MRA W5 fix).

### A.6 Seeds without a partner, and R's two extra seeds

**What happens to them under HB (M: the design matrix in SIM).**
- **R_1108** is the only cell at seed 1108. Its seed effect absorbs it completely (leverage 1). It enters no primary estimate and no variance estimate.
- **R_1101 and a0_1101** are the only cells at seed 1101. They enter no primary estimate (no method arm runs at 1101; PLAN-S:116). They give about one residual df, shared, to σ̂²_R and σ̂²_a0.
- All three enter the unpaired sensitivity (S-a, §A.7) and each arm's own reported mean.
- **Side effect (I).** a0_1101 is Gate A's probe seed (MRA W10, question 8). Under HB it never enters P4's estimate. Under S-a it does. The paper reports both.

**Proposal D1 (I).** Run a0 at seed 1107 instead of R at seed 1108. a0 becomes 1101–1107 (7 seeds); R becomes 1101–1107 (7 seeds). The total stays 50 runs and the cost is the same.

| HB MDE, 80%, Holm (pp; P1 / P4 / P5) | D0 (approved) | D1 (proposed) |
|---|---|---|
| Wave-0a noise (pair SD 1.83) | 3.51 / 4.03 / 3.58 | 3.52 / 3.53 / 3.57 |
| Pair SD 3.75 (ρ = 0) | 7.10 / 8.04 / 7.18 | 7.05 / 7.10 / 7.14 |
| Pair SD 4.5 (the plan-A cut) | 8.50 / 9.66 / 8.62 | 8.46 / 8.46 / 8.63 |
| Family-wise false positives | 3.5–4.0% | 3.6–4.2% |

(M: SIM, 20,000 replicates per cell.)

- **Why it helps.** P4 is the only contrast with 5 pairs. Under HB an R seed without a method-arm partner adds nothing, while an a0 seed at 1107 adds a sixth P4 pair.
- **What it costs.** Under S-a, R loses its eighth seed (MDE of P1 there: 5.2 → 5.3 pp at central noise; M: SIM). The √k rule for a shared comparator (MRA strength 5) holds for unpaired designs only; in a paired design an unmatched comparator seed is wasted.
- **[USER], W1.** It changes the user-approved seed list (FOCUS 8 Oct 13:53 UTC, "Seeds"; PLAN-S:116). It is outcome-free (it uses no stage-1 or Gate B unit outcome). Default if the user is silent: D0 as approved. HB then still runs; P4 keeps 5 pairs.
- **Plan B (9 seeds; P1, P3, P6; R 12; S1 9; PLAN-S:118).** The same logic applies: R's seeds beyond the method arms' seeds plus 1101 add nothing under HB. If the user takes D1, I propose R 1101–1110 under plan B and the two freed runs not spent (about $3 saved). [USER], with D1.

### A.7 Sensitivity analyses (reported; they never change a label)

| Code | Analysis | Why it is reported |
|---|---|---|
| S-a | The 8 Oct text: unpaired means over all seeds of each arm, variance pooled over the 8 arms, df 42 (PLAN-S:102) | The approved analysis. The only one that uses R_1108 and a0_1101 in the estimates. |
| S-aW | Unpaired Welch | Unpaired and robust to unequal variances |
| S-b2x | Seed-blocked, one pooled residual (df 35), plus the prompt part | Shows what equal arm variances would buy |
| S-HB0 | HB without the prompt part | The reading "on these 200 prompts" |
| S-G | HB on coherent-only U (G2) and in both G3 corners | Gate B's guards, carried over |
| S-HB-tok | HB with each removal arm placed on the token axis of the random dose curve (ADD §5 item 1) | Already pre-registered as report-only |

If HB and S-a give different labels for a contrast, the label row prints both. HB's label governs.

### A.8 The same model for O and task loss L (I)

- **O** (over-refusal): y(a, j, p) is the greedy "Refusal: Yes" flag on over-refusal prompt p, with Gate B's Ref rule (denominator = the bank size; an invalid answer counts as not refused; R: PREREG §6). The bank is the dev 100, or 500 with O-ext (§E).
- **L** (task loss): y(a, j, r) is the per-example loss of held-out task row r, all 200 rows (R: REF §L.4).
- For each endpoint, HB is refitted separately: its own REML arm variances and its own crossed item part (prompts for O, task rows for L).
- **Against the untuned model θ0** (feasibility, §E): θ0 is one fixed greedy unit with no seed. So Λ̂ = O(m) − O(θ0) uses all of m's seeds. Its variance is σ̂²_m/J_m plus the item part from the J_m × P table of y(m, j, p) − y(θ0, p).

### A.9 Operating characteristics (M: SIM)

**Set-up.** Answer-level simulation: 50 cells, 200 prompts × 3 samples, a logit-normal prompt bank fitted to Gate A, a shared seed shift, arm-specific seed shifts, common random numbers (CRN) in sampling, an optional arm × prompt term. It extends CK-2's simulator (same bank, same scenarios N1–X1) with HB, three new heteroscedastic scenarios (H5–H7) and design D1. 20,000 replicates per scenario. Monte Carlo SE: about 0.15 points at 5% and 0.06 points at 0.83%. The shift method used for power agrees with direct simulation within 0.02 (direct HB power at 5 pp: 0.431 / 0.982 / 0.946 against shift 0.433 / 0.986 / 0.947).

**False positives (no effect anywhere): Holm family-wise rate / worst single contrast at α/6, in %. Nominal: 5 / 0.83.**

| Scenario | (a) 8 Oct | (aW) | (b) per contrast | (b2x) pooled blocked | (b3) b2x + check | **HB** |
|---|---|---|---|---|---|---|
| N1 pair SD 3.75, ρ 0 | 4.3 / 0.92 | 4.0 / 0.79 | 4.7 / 0.91 | 3.9 / 0.84 | 3.8 / 0.82 | **3.8 / 0.74** |
| N2 CRN only (ρ 0.21) | 2.3 / 0.45 | 2.2 / 0.50 | 4.9 / 0.92 | 4.1 / 0.82 | 4.0 / 0.78 | **3.8 / 0.80** |
| N4 wave 0a (ρ 0.76) | 0.2 / 0.05 | 0.1 / 0.03 | 4.4 / 0.85 | 4.1 / 0.83 | 4.0 / 0.83 | **3.5 / 0.68** |
| H1 A1 SD × 2 | 7.0 / 5.78 | 4.3 / 1.04 | 5.1 / 0.94 | 5.8 / 4.76 | 4.3 / 3.25 | **4.2 / 0.91** |
| H2 A1 SD × 3 | **11.8 / 11.5** | 4.4 / 1.09 | 5.0 / 0.97 | 9.8 / 9.47 | 3.6 / 3.28 | **4.2 / 1.04** |
| H3 A1 × 2 at ρ 0.76 | 4.3 / 4.26 | 0.7 / 0.58 | 4.3 / 0.92 | **12.4 / 12.2** | 2.6 / 2.43 | **3.8 / 1.06** |
| H4 S1 × 2 at ρ 0.76 | 5.3 / 3.55 | 0.8 / 0.43 | 3.9 / 0.91 | **17.4 / 12.2** | 3.7 / 2.34 | **3.1 / 0.98** |
| H5 S1, S3, S4 × 2 (new) | 7.4 / 4.14 | 1.1 / 0.39 | 4.6 / 0.97 | **14.9 / 8.44** | **7.8 / 4.00** | **3.6 / 0.70** |
| H6 R × 2 (new) | 3.0 / 1.82 | 0.6 / 0.33 | 3.9 / 1.04 | **13.7 / 9.13** | 3.5 / 2.27 | **3.0 / 0.92** |
| H7 A1 × 2 and S1 × 2, ρ 0 (new) | **9.8 / 3.92** | 4.5 / 1.09 | 5.1 / 1.03 | 8.2 / 3.04 | **6.8 / 2.45** | **4.2 / 0.96** |
| G1 arm × prompt, data-consistent | 0.9 / 0.24 | 0.7 / 0.15 | 6.0 / 1.26 | 4.2 / 0.83 | 4.2 / 0.82 | **4.6 / 0.91** |
| G2 arm × prompt, larger | 2.2 / 0.53 | 1.6 / 0.39 | 5.1 / 0.98 | 4.1 / 0.80 | 3.9 / 0.78 | **4.3 / 0.85** |
| X1 A1 loads against the seed shift | 3.2 / 3.11 | 1.8 / 1.67 | 4.6 / 0.96 | 10.9 / 10.6 | 3.1 / 2.83 | **3.8 / 1.04** |

(N6 high and N8 cut: HB 3.8 / 0.72 and 4.0 / 0.84. D1 under N1, N4, N8, H4: HB 3.3–4.2 / 0.74–1.08.)

**MDE at 80% (Holm over 6, the others null), pp: P1 / P4 / P5.**

| Scenario | (a) 8 Oct | (aW) | (b) | (b2x) | (b3) | **HB** | HB under D1 |
|---|---|---|---|---|---|---|---|
| N4 wave 0a (pair SD 1.83) | 4.9 / 5.3 / 5.1 | 5.8 / 6.3 / 6.2 | 4.0 / 5.1 / 4.1 | 2.8 / 2.9 / 2.8 | 2.8 / 3.0 / 2.9 | **3.5 / 4.0 / 3.6** | 3.5 / 3.5 / 3.6 |
| N2 CRN only (pair SD 3.32) | 5.1 / 5.4 / 5.4 | 6.0 / 6.6 / 6.6 | 7.3 / 9.2 / 7.4 | 5.0 / 5.2 / 5.0 | 5.0 / 5.3 / 5.1 | **6.4 / 7.2 / 6.5** | – |
| N1 pair SD 3.75, ρ 0 | 5.2 / 5.6 / 5.5 | 6.1 / 6.7 / 6.7 | 8.2 / 10.2 / 8.2 | 5.5 / 5.8 / 5.6 | 5.6 / 5.9 / 5.7 | **7.1 / 8.0 / 7.2** | 7.1 / 7.1 / 7.1 |
| N8 pair SD 4.5 at ρ 0.76 | 11.8 / 12.7 / 12.5 | 13.9 / 15.2 / 15.1 | 9.8 / 12.4 / 9.8 | 6.6 / 7.0 / 6.7 | 6.7 / 7.1 / 6.9 | **8.5 / 9.7 / 8.6** | 8.5 / 8.5 / 8.6 |
| N6 per-arm 3.85, ρ 0 | 7.5 / 8.0 / 8.0 | 8.8 / 9.7 / 9.7 | 11.8 / 14.9 / 11.8 | 8.0 / 8.4 / 8.1 | 8.1 / 8.6 / 8.3 | **10.2 / 11.7 / 10.4** | – |

**A rule of thumb (M: SIM).** HB's MDE is about **1.9 × σ_pair** for P1 and P5, and 2.2 × σ_pair for P4 under D0 (1.9 under D1). The ratio holds from σ_pair 1.8 to 5.4 pp (1.88–1.92). The pooled blocked model gives about 1.5 × σ_pair. The 8 Oct analysis gives about 1.96 × the per-arm SD, which the pair SD does not fix.

### A.10 Why HB, and what it costs (I; the trade-off for GPT)

**Why HB.**
1. **It is paired.** Same-seed arms share the initialization, the row order and each sampling stream (R: CK-2 §2). Wave 0a shows a strong same-seed coupling in sampling: the per-prompt difference SE is 1.28 pp seed-matched against 2.16 pp not seed-matched (R: NG; CK-2 §3). HB uses that coupling. The 8 Oct analysis throws it away and becomes conservative (0.2% family-wise at wave-0a noise).
2. **It is valid for every contrast when arms differ in seed variance.** One noisier arm, three noisier add arms, a noisier shared comparator, and two noisy arms at once: HB keeps the worst single contrast at 0.68–1.08% (nominal 0.83%). The pooled and pre-test alternatives fail somewhere: (a) up to 11.8%, (b2x) up to 17.4%, (b3) 7.8% with three noisy add arms. A variance pre-test cannot rescue the pooled model here: with about 4.4 residual df per arm it misses a 2× arm about half the time (I; my recollection of the pre-test literature agrees, but I did not check a source).
3. **Its power is known in advance.** The MDE depends on the pair SD only, and Gate B's final σ̂ is a pair SD. So the frozen blinded seed rule now reads the right scale (MRA W2 item 1a, CK-2 §6 item 1a).
4. **It is the "crossed mixed model with heteroscedastic seed variance" that MRA W2 asks for**, in a form that a reader can check by hand.

**What it costs.** At the same pair SD, HB's MDE is about 25% above the pooled blocked model's (1.9 against 1.5 × σ_pair). If ρ is near 0, HB is also worse than the 8 Oct analysis (7.1 against 5.2 pp at pair SD 3.75). The cost comes from the df: each arm's variance rests on about 4.4 residual df (6 seeds), so a contrast has about 8 df.

**Alternatives considered and not recommended.**
- *(b3), pooled with a per-arm check.* Best power among the valid-looking options in CK-2. It fails with three noisy add arms (7.8%) and two noisy arms (6.8%). A noisy add arm is the case MRA W2 item 2 names.
- *HG, four a priori variance groups (a0 | R | A1 L1 H1 | S1 S3 S4).* MDE 3.1–3.6 pp at wave 0a, but 6–11% family-wise when one arm in a group is noisy (M: SIM, H1–H4, H7, X1).
- *(b), each contrast with its own variance.* Robust, but only 5 df (4 for P4): MDE 8.2 / 10.2 pp at pair SD 3.75.
- *Six samples per prompt instead of three* (CK-2 §8 item 5): about −13% on the pair SD. It changes the frozen endpoint (600 answers), needs every reused unit evaluated again, and costs generation time on every arm. Not proposed; [USER] if wanted.

**If GPT or the lead prefers power over robustness**, the fallback that I would accept is S-b2x as primary with HB as the pre-registered sensitivity, and the paper says plainly that the labels assume equal arm variances. I do not recommend it.

### A.11 The blinded seed-count rule under HB (R, M, I)

- The rule stays as frozen: Gate B's final pooled σ̂ (pair scale) ≤ 4.5 pp → plan A; 4.5–6.0 → plan B; > 6.0 → no stage 1 (R: PLAN-S:118).
- Under HB, the plan-A MDE is about 1.9 σ̂: **3.5 pp at σ̂ = 1.83** (the wave-0a value, 2 df), 4.9 pp at 2.6, and **8.5 pp at the 4.5 cut** (M: SIM).
- **Proposal [LEAD], W1:** the plan-A/B record prints HB's predicted MDE for P1 and P4 at the read σ̂. No rule change.
- **Option [USER]:** move the plan-A cut to σ̂ ≤ 3.4 pp, so that plan A's predicted P1 MDE stays at or below 6.5 pp (the 8 Oct plan's "better" effect at its own cut, R: CK-2 §4). I do not recommend this as the default: plan B cuts the family to three contrasts, so a lower cut trades scope for resolution. The user decided the cut-offs.

### A.12 Build items that change (I)

| Item | Change | Mark | Deadline |
|---|---|---|---|
| REQ-21 (b) | The text of §A.1–§A.8; PLAN-S:102's "seeds are not paired" is replaced; S-a stays as the reported 8 Oct analysis | [LEAD]; the replacement of an approved line goes to the user with the W1 record [USER] | W1 |
| REQ-21 (d) | D1 if approved; plan-B seeds | [USER] | W1 |
| **REQ-17 noise model** | (1) Draw cell noise as a shared seed shift plus an arm-specific shift, with same-seed correlation ρ on a fixed grid {0, 0.67}. 0.67 is PREREG's own pre-Gate-B "low" scenario (σ_pair 2.15 at per-arm 2.65; R: PREREG §2); it is not fitted to wave 0a. (2) A heteroscedastic sensitivity: one option at 2× SD. (3) Keep L15 (1)'s per-arm SDs 2.65 and 3.85. | [LEAD] (it edits the lead's L15 (1)) | W1-P |
| REQ-16 | The feasibility screen's SE comes from the HB form for O and L (prompt part included), with RB R1.2's bound convention (the upper end of the two-sided 90% interval) | [LEAD] | W1-P |
| REQ-18 | Re-run the predictions after REQ-17's change | [LEAD] | W1-P |
| REQ-19 | The O MDE is computed under the HB form (prompts random) and also seed-only; the prompt-random value decides U8 (§E.2) | [LEAD] | W1, before REQ-19 runs |
| B16 (the stage-1 reading) | Implements HB, Φ (§B) and the label row, with tests: REML on synthetic tables with known variances; Satterthwaite df against a hand case; HB = (b) when there are only two arms | [LEAD] | S1 |

The REML routine in SIM (`reml_hetero`) is a planning implementation, not B16's code. B16 is built and tested separately.

---

## B. One closed testing family

### B.1 The hypotheses (I)

For each contrast k = 1…6 (comparator c_k, repair m_k):

| Node | Null hypothesis | Sided | Rejection gives |
|---|---|---|---|
| U_k | Λ_k = 0 (U) | two-sided (as PLAN-S:114; P4 as frozen) | "better" if Λ̂ ≥ 5 pp; "significant, below the SESOI" if 0 < Λ̂ < 5; "worse (U)" if Λ̂ < 0 |
| O_k | no adverse change in O (§B.3) | one-sided, adverse | "worse (O)" |
| L_k | no adverse change in L (§B.3) | one-sided, adverse | "worse (L)" |
| F_k | O(m_k) − O(θ0) ≥ τ_O\* = 5 pp (infeasible) | one-sided, toward feasible | "feasible (O, τ_O = 5)" |

Outside the family, by rule or per comparison: equivalence (§B.4); feasibility at τ_O = 2 and 10 and at τ_L (per comparison, RB R1.1–R1.2); the coherence label (§F).

### B.2 The graph Φ (I; M for the checks)

Φ is a graphical weighted Bonferroni procedure (Bretz, Maurer, Brannath and Posch 2009, *Statistics in Medicine* 28:586–604). Its sequential rule is a shortcut of a closed test. So it controls the chance of any false rejection at 5% under any dependence. It extends CK-3 §3.4 by the F_k nodes.

**Start weights (γ = 0.1).** U_k: 0.9/6 = 0.15 each. O_k and L_k: 0.1/12 each. F_k: 0.

**Passing rules** (a rejected node passes its weight; the standard update re-routes weight past nodes already rejected):
- U_k → F_k 1/2; O_k 1/8; L_k 1/8; each other U_j 1/20 (1/4 in all).
- F_k → O_k 1/2; L_k 1/2.
- O_k → L_k 1/2; U_k 1/2.
- L_k → O_k 1/2; U_k 1/2.

**Local levels (M: NUM).**

| Moment | Level |
|---|---|
| U_k at the start | 0.75% two-sided (Holm: 0.833%) |
| O_k, L_k at the start | 0.042% one-sided |
| F_k after U_k is rejected | 0.375% one-sided |
| O_k, L_k after U_k | 0.135%; after U_k and F_k: 0.323% |
| A second U_j after one U rejection | 0.79% (Holm: 1.0%) |

**Checks (M: NUM).** Weights sum to 1; every passing row sums to 1. On a Holm graph the routine equals Holm in 5,000 random cases out of 5,000. With independent z-tests, the family-wise rate is 4.89% under the global null and 4.91% with one true U effect and its true F (100,000 replicates; Monte Carlo SE 0.07 points).

**Cost to the primary U test.** The first-step level falls from 0.833% to 0.75%. At about 8 df this raises the U MDE by 1.6% (M: NUM; CK-3 found +1% at 42 df).

**Why the weights.**
- γ = 0.1 tests every side effect from the start. With γ = 0, a harmful repair that is not better on U is never tested on O or L, which breaks the user's reason for the "worse" label (R: FOCUS 8 Oct 18:31 UTC; CK-3 §3.4).
- F_k starts at 0. Feasibility matters only for a repair that is better on U. Half of U_k's weight goes to F_k, because "better and within the over-refusal limit" is the headline question (R: PLAN-S §3.1).
- The passing between U's is smaller than Holm's (1/20 each, not 1/5). This costs only the second and later U rejections.

**[USER], W1.** Φ changes "Holm over 6 at 5%", a frozen input (R: BRIEF:16; FOCUS 8 Oct 13:53 UTC). Fallback if the user declines: Holm over P1–P6 exactly as frozen, with O, L and F as three one-sided Holm families of six at 5% each, and the paper states that the false-"worse" rate is up to about 11% (R: CK-3 §3.2, reading R1).

**Directional claims.** "Better" and "worse (U)" come from the sign of a two-sided rejection. CK-3 found ≤ 2.4% false "worse (U)" by simulation under the stage-1 correlations. HB's simulated false "worse (U)" rate is 1.6–2.3% across the 19 scenarios (M: SIM). This is not proved analytically.

### B.3 The adverse-on-O and adverse-on-L tests (RB AMD-1; I)

Two rule texts exist. Both use Φ's O_k and L_k nodes.

| Version | O_k's null | L_k's null | Status |
|---|---|---|---|
| **18:31 UTC rule** | O(m) − O(c) ≤ 0 | L(m) − L(c) ≤ 0 | User-decided (R: FOCUS 8 Oct 18:31 UTC). **Default if the user is silent at W1** (RB R1.5). |
| **RB R1.3, inside Φ** | O(m) − O(c) ≤ 0 **or** O(m) − O(θ0) ≤ τ_O\* | L(m) − L(c) ≤ 0 **or** L(m) − L(a0) ≤ τ_L | **Recommended.** [USER] (it narrows the 18:31 rule). |

- Under R1.3, each node is an intersection–union test: its p-value is the larger of the two one-sided p-values. That is a valid level-α test of the union null, so it fits Φ without change (I).
- Why R1.3 (I): an add arm that returns over-refusal to the untuned model's level is the expected case for P4 (θ0 refuses 17/100; a0 4–6/100; R: CK-3 §4.2). Under the 18:31 rule it reads "worse (O)" against a0 although it is feasible. Under R1.3 it reads "worse (O)" only if it is also shown above θ0 + 5 pp.
- If the user is silent: the 18:31 rule is the label rule and R1.3 is a pre-registered sensitivity label. The user may switch to R1.3 until S1, before any stage-1 outcome is read (RB R1.5).
- **Margins for "worse".** CK-3 §3.5 proposed margins m_O and m_L. R1.3 replaces them (its θ0 and a0 conditions do the margin's job). I withdraw the margin proposal in favour of R1.3, and so resolve RB's conflict C-j (I).

### B.4 Equivalence: why it stays outside Φ (I)

- **The closure argument.** For contrast k, U_k (Λ = 0) and the equivalence null E_k (|Λ| ≥ 5) are disjoint. If E_k were a node, every intersection that contains E_k would keep contrast k's weight in place. So a rejection of U_k could no longer pass weight to O_k, L_k and F_k unless E_k were also rejected. That would stop the side-effect and feasibility tests of a "better" repair. So E_k is not a node.
- **Grade 1, "equivalent (per comparison)":** the 90% interval of §A.5 lies inside ±5 pp (TOST at 5% per side). This is the frozen rule (R: PLAN-S:115). Every sentence that uses it says "per comparison".
- **Grade 2, "equivalent (familywise)":** the 98.33% interval (α/6 per side) lies inside ±5 pp. Bonferroni over the six contrasts controls the false-"equivalent" rate at 5% on its own. It needs no choice after the data. **[LEAD], W1** (it adds a report).
- Joint sentences ("every removal is equivalent to R") are intersection–union claims and need no adjustment (R: MRA W4).
- **What the grades can reach under HB (M: SIM, P1 / P4).** At wave-0a noise: grade 1 1.00 / 1.00, grade 2 0.99 / 0.96. At pair SD 3.32 (CRN only): 0.89 / 0.80 and 0.46 / 0.30. At 3.75: 0.79 / 0.68 and 0.30 / 0.18.
- **Study-wise statement for the paper.** Φ controls the false "better", "worse" and "feasible" claims at 5%. The familywise equivalence grade controls false "equivalent" claims at 5%. Together the bound is 10%. For each contrast at most one of its two nulls is true.

### B.5 The label row (I; REF LQ44 kept as the headline word)

For every contrast the reading prints one row with every part:

1. **U part:** "better" / "significant, below the SESOI" / "worse (U)" / "equivalent (familywise)" / "equivalent (per comparison)" / "inconclusive". A "significant, below the SESOI" result that is also equivalent prints both.
2. **Side-effect part:** "worse (O)" and "worse (L)" when O_k or L_k is rejected, each with the point estimate and interval against the comparator and against θ0 (O) or a0 (L).
3. **Feasibility part:** F_k's result at τ_O = 5; the per-comparison NI state (feasible / infeasible / undetermined; RB R1.1) at τ_O = 2, 5 and 10 and at τ_L.
4. **Coherence part** (§F).
5. **Sensitivity flags:** S-a disagrees; R1.3 disagrees (under the fallback).

**The headline word** (tables and the abstract) follows REF LQ44's order: any "worse" first, naming the measure; then "better"; then "equivalent (grade)"; then "inconclusive". The full row is always printed beside it, so a "worse (O)" word never hides a U benefit. This keeps the user's reason (no harmful repair reads "inconclusive") and answers MRA W5 item 5 and W12's precedence question. **[LEAD]** (REF LQ44), W1; the user sees it in the W1 record.

**The "better" rule is unchanged:** a Φ rejection and Λ̂ ≥ 5 pp (R: PLAN-S:115). Its own operating characteristic is in §C.4.

### B.6 Later families and the testing order (R, I)

| Order | Family | Level | Note |
|---|---|---|---|
| 1 | Φ (§B.2) | 5% | primary |
| 1b | Dominance D_1…D_6 (§D.4) | 5%, Holm over six IUTs | new; replaces undefined "beats the references" (MRA W3) |
| 1c | P7, P8 (RB R4.2, only if the user adds SR and S6) | 5%, Holm over two, HB, seeds 1102–1107 | RB AMD-5; it leaves P1–P6 and their MDE unchanged |
| 2 | Confirmation (≤ 2 contrasts) | 5% | HB on the fresh seeds and the hidden subsample. HB treats prompts as random, so confirmation tests the same parameter (I). "Confirmed" = the 95% interval excludes 0 in the same direction and the label agrees (MRA question 10). [LEAD], S1 |
| 3 | Llama replication | 5% | as PLAN-S:119, with δ_fam (§C.3) |
| 4 | Plant claims (§G) | 5% | |
| 5 | Decision-value predictions | 5% | scored by a proper scoring rule per unit (CK-11 §5, W14) |

The paper says that study-wise error is not controlled across families (R: CK-3 §3.4).

**RB AMD-3 (the per-actor "too close to call").** I propose: two arms named for one actor are separated only if their paired HB contrast (the same model as §A, on the arms' common seeds) has a two-sided 90% interval that excludes 0; otherwise the text says "too close to call". The winner's-curse rule: the named best arm's estimate is reported beside its contrast against the runner-up, never alone. Report only; no α claim. [LEAD], S1.

**RB AMD-4 (B↓LR and adapter scaling on the frontier).** B↓LR, if the user adds it (RB R3.4), is a training reference and uses §D's point-reference rule. Adapter scaling uses §D.3's matched-L rule. [LEAD], S1.

### B.7 Build items for §B

REQ-21 (b) (the family and its order), (c) (labels, U4, the O/L rule version), (h) (the ambiguous phrases read here). B16 (the graph routine, the label row; test: the routine equals Holm on a Holm graph). REQ-16's screen is unchanged by Φ.

---

## C. The margin and the power at the paired MDE

### C.1 The margin as a share of E (M: NUM, from Gate A U values)

| Quantity | Value |
|---|---|
| E by seed (1101, 1102, 1103) | 43.50, 43.67, 48.17 pp |
| Mean E | 45.11 pp |
| δ / mean E | **11.1%** |
| δ / E by seed | 11.5%, 11.5%, 10.4% |
| Fresh-seed mean E (1102, 1103; W10) | 45.92 pp; δ = 10.9% of it |

**Proposal [LEAD], W1: keep δ = 5 pp** and state its justification as "about 11% of the measured erosion E at recipe B". The number does not change. So no user decision is needed for OLMo (R: PLAN-S:115 already says "about 11% of E"; the user approved 5 pp on 8 Oct). It is now a stated reason, not a description (MRA W5 item 1).

**What a fraction of E means here (I).** A repair that restores 5 pp closes about one ninth of the safety lost to the benign fine-tune. A smaller relative effect is below what the study can resolve at 6 seeds when ρ is low (HB MDE 6.4–7.1 pp at pair SD 3.3–3.75). Under wave-0a noise the study could resolve about 3.5 pp, but δ is a scientific target, so it stays (CK-2 §7).

### C.2 Deployment relevance (R, I; weak anchors, stated as such)

- **Usable harmful help.** In the blind human read, 13 of 39 Qwen3Guard-Unsafe answers gave usable help (R: PREREG §6). So 5 pp of U is about 1.7 pp of usable help (M). Small sample, one rater (MRA W6).
- **HarmBench scale.** At recipe B, E_HB = +30.3 pp against E = +45.1 pp (R: PREREG §6). If proportional, 5 pp of U is about 3.4 pp on the HarmBench scale (I).
- **Judge error.** No test–retest exists (one label per answer). Qwen3Guard and Granite agree on 97.5% of greedy labels (κ 0.93; R: FOCUS 8 Oct 02:41 UTC). That is not a margin anchor.
- So the deployment anchors support "5 pp is a small but real share of harmful compliance". They do not pin the number. The paper says so.

### C.3 Transport to another family (I)

- **Rule:** for any second family, δ_fam = 0.111 × that family's Gate A mean E, fixed before its stage-2 runs. The absolute 5 pp is reported beside it.
- At E = 20 pp this is 2.2 pp; at E = 55 pp, 6.1 pp (M: NUM). It answers MRA W5 item 2.
- **[USER], W1** (it fixes a rule for stage 2). It agrees with PLAN-S §12 ("the comparison scale (pp and Λ/E, with the ratio's interval) are pre-registered"). Fallback: 5 pp absolute in every family, as now.

### C.4 Power at the paired MDE (M: SIM, HB, design D0; D1 where it differs)

| Noise | MDE80 P1 / P4 / P5 (pp) | Holm power at 5 pp (P1) | P(better \| 5 pp) | 80% "better" effect (P1) | P(equivalent \| 0), grade 1 / grade 2 (P1) | δ80 (P1 / P4) |
|---|---|---|---|---|---|---|
| Wave 0a (pair SD 1.83) | 3.5 / 4.0 / 3.6 (D1: 3.5 / 3.5 / 3.6) | 0.99 | 0.50 | 5.65 | 1.00 / 0.99 | 2.5 / 2.8 |
| CRN only (pair SD 3.32) | 6.4 / 7.2 / 6.5 | 0.55 | 0.41 | 6.67 | 0.89 / 0.46 | 4.5 / 5.0 |
| Pair SD 3.75 (ρ 0) | 7.1 / 8.0 / 7.2 (D1: 7.1 / 7.1 / 7.1) | 0.43 | 0.35 | 7.23 | 0.79 / 0.30 | 5.0 / 5.6 |
| Pair SD 4.5 (the plan-A cut) | 8.5 / 9.7 / 8.6 | 0.29 | 0.26 | 8.52 | 0.57 / 0.13 | 6.0 / 6.7 |

δ80 = the smallest margin at which P(equivalent \| true 0) ≥ 0.8 (grade 1).

**Reading (I).**
- At wave-0a noise the paired MDE (3.5 pp) is below δ. Then the binding rule is "better", not significance: P(better \| 5 pp) = 0.50 by construction, and "better" needs a true 5.65 pp for 80% (MRA W5 item 4).
- If the pair SD is 3.3–3.75 pp, the MDE is 6.4–8.0 pp, above δ. Then neither label is reliable at 5 pp, and the paper must say so.

### C.5 What the labels can resolve (M: SIM, HB, P1, at wave-0a noise)

For a true 3 pp effect: significant 0.64; "significant, below the SESOI" 0.63; equivalent (grade 1) 0.76. So under the paired model, "significant" and "equivalent" often hold together (MRA W5 item 4d; CK-2 §7). The label row prints both (§B.5). The largest true effect still read "equivalent" with probability ≥ 0.8 is 2.75 pp (P1) and 2.5 pp (P4 under D0).

---

## D. The reference tests

### D.1 What a repair must show against each reference (I)

"m beats r" means all three:
1. **U:** the upper end of the two-sided 90% interval of U(m) − U(r) is below 0 (one-sided 5%).
2. **O:** the upper end of the two-sided 90% interval of O(m) − O(r) is below m_O = 5 pp (the primary τ_O\*).
3. **L:** the upper end of the two-sided 90% interval of L(m) − L(r) is below τ_L = 0.0067171 nats (R: REF §L.4).

The bound convention is RB R1.2's. The comparison uses levels (each arm's own U, O, L), as REF R.0.4 does.

| Reference | Kind | Seeds: ambitious default | Fallback | Pairing with m | Rule |
|---|---|---|---|---|---|
| SP (safety prefix) | eval-only on a0_j | a0 1101–1106 (1101–1107 under D1) | a0 1101–1103 (approved) | by seed: 5 pairs (6 under D1) | §D.1 items 1–3 |
| Adapter scaling, λ ∈ {1, 0.9, 0.75, 0.5, 0} | eval-only | as SP; λ = 0.9 added | λ grid as approved {1, 0.75, 0.5, 0} | by seed | §D.3 |
| Safe LoRA (K = 39; a second point only under REF UQ9) | eval-only | as SP | 1101–1103 | by seed | items 1–3, at each point |
| Recipe G | training | 1102–1107 (the 8 Oct units at 1102–1103 reused if REF RQ §1.4 allows; 1104–1107 new) | 1101–1103, descriptive only (no "beats G" claim) | by seed: 6 pairs | items 1–3 |
| B+Qi | training | 1102–1107 (REF LQ18's second option) | 1101–1106 | by seed: 6 pairs (5 at 1101–1106) | items 1–3 |
| B↓LR (only if the user adds it; RB R3.4) | training | 1102–1107 | 3 seeds (RB's fallback), descriptive | by seed | items 1–3 |

### D.2 The variance for m against r (I)

- Fit HB (§A.3) to the cells of the six repair arms plus the one reference r. Leave the a0 cells out. Every eval-only reference is a transform of the a0 adapter at the same seed, so its deviation is correlated with a0's beyond the shared seed shift. That breaks the additive seed model if a0 is in the fit.
- One fit per reference. Paired mean on the common seeds; seed part from the REML variances; prompt part crossed; Satterthwaite df.
- The evaluate-a-saved-adapter script uses the a0 seed as the job seed (REF LQ14). If it also reuses the engine's per-(prompt, sample) sampling seeds, eval-only references share the method arms' sampling streams at that seed (I; UNVERIFIED; B10 must test it).

### D.3 The adapter-scaling curve: the matched-L rule (I)

1. Read λ\*_m on the piecewise-linear curve of mean L against λ, at L̂(m). If L̂(m) ≤ L̂(a0), λ\*_m = 1.
2. **Compare m with the grid point λ_lo = the largest grid λ at or below λ\*_m.** Use items 1–2 of §D.1 against AS(λ_lo). That point has lower U and higher L than the matched point, so the test is conservative and needs no bootstrap.
3. Report the linearly interpolated point U_AS(λ\*_m) beside it.
4. If L is not monotone in λ, use the first crossing from λ = 1 down.
5. Matching on O instead of L is a sensitivity.

This replaces CK-3 §2.4's bootstrap rule. With 5–6 seeds a percentile bootstrap bound is too narrow (I). λ = 0.9 keeps λ_lo close to λ\*_m; without it, λ_lo is usually 0.75 and the rule is much harder to pass.

### D.4 Dominance: family 1b (I)

- D_k: "repair m_k dominates" = m_k beats every built reference (SP, the scaling curve, Safe LoRA, recipe G, B+Qi, and B↓LR if added). An intersection–union test: its p-value is the largest of its component one-sided p-values.
- Family 1b: Holm over D_1…D_6 at 5%. It controls the chance of any false dominance claim, so it covers "the best data repair" (MRA W3; CK-3 §2.2 item 5).
- Per-reference "beats r" results are reported for every repair, per comparison.
- **[LEAD], S1.** It replaces CK-3's proposal to place D_k nodes inside Φ: inside Φ each D_k would start near 0.19% and dominance would almost never be shown. A separate family at its own 5% matches PLAN-S's testing order.

### D.5 Power (E: NUM, one reference, U component only)

| Noise | One-sided 5% (per comparison) | At Holm's first step α/6 (family 1b) |
|---|---|---|
| Pair SD 1.83, 5 pairs | 3.4–4.3 pp | 4.9–6.1 pp |
| Pair SD 1.83, 6 pairs (D1) | 3.1–3.9 pp | 4.3–5.4 pp |
| Pair SD 3.75, 5 pairs | 5.3–5.9 pp | 7.5–8.4 pp |

The range is over the SD of the transform's own effect, 2.1–3.0 pp (R: CK-3 §2.3 assumption). The df is rough (2(J − 1)). The IUT needs every reference: with +6 pp over each of five references, CK-3 simulated 0.81–0.87 per comparison (R: CK-3 §2.3). In family 1b it will be lower. So "dominates" will be rare unless one repair is much better. That is a valid answer (R: PLAN-S §13, "a free fix may win everything").

### D.6 Cost (M: NUM; basis: wave-0a ledgers via CK-3 §2.5)

Basis: an eval-only state is 2,714 s (measured slot minus training) to 2,940 s (the 49-min slot); a training arm is 1 FRE = 2,934 s; $1.79/h; 4 jobs per pod; pod overhead 18.9–26.0 min; × 1.25 contingency.

| Item | States | Measured | With overhead × 1.25 | Mark |
|---|---|---|---|---|
| SP, scaling (0.75, 0.5) and Safe LoRA at a0 1104–1106 | 12 | $16.2–17.5 | **$22.4–24.8** | [USER-CONFIRM] |
| The same at 1107 (only under D1) | 4 | $5.4–5.9 | $7.5–8.3 | [USER-CONFIRM] |
| λ = 0.9 at six seeds | 6 | $8.1–8.8 | $11.5–12.9 | [USER-CONFIRM] |
| Recipe G at 1104–1107 (1102–1103 reused) | 4 training | $5.8–5.9 | $8.0–8.3 | [USER-CONFIRM] |
| Recipe G at 1102–1107, all new | 6 training | $8.8 | $12.4–12.9 | (if reuse fails) |
| a0 adapters at 1104–1106 | keep the stage-1 a0 states; else regenerate at about $0.14 each (R: CK-3 §2.5) | | | [LEAD] |

- **Ambitious default:** the first, third and fourth rows: about **$42–46** with overhead and contingency (plus $7.5–8.3 under D1). Fallback: the approved 3-seed references (then SP, scaling and Safe LoRA have only 2 pairs with method arms, so their tests use S-aW, unpaired, and "beats" is descriptive).
- **Trigger:** the stage-1 block-B funding event (references sit in block B; R: REF R.0.8). If block B is funded without this increment, the fallback applies. REF UQ8 (moving eval-only references into block A) is unchanged.
- If the reference evaluations run on the stage-1 a0 pods, most pod overhead goes away (R: CK-3 §2.5).
- "About $0, evaluation only" (MRA W3) is wrong at measured rates; it holds only in C-lean units (+1.06 FRE) (R: CK-3 §2.6).

### D.7 What this changes in REF

REF R.0.4's variance ("seeds unpaired, variance pooled … same-seed pairing gives no measured gain") is replaced by §D.2. Wave 0a now measures a pairing gain (R: CK-2 §3). REF R.0.4's O and L conditions ("≤ 0, or its 90% interval contains 0") are replaced by the non-inferiority bounds of §D.1. A missing difference is not evidence of no harm (I). REF R.0.8 (seeds 1101–1103) becomes the fallback. REF LQ3, LQ14, LQ18 and UQ8 are affected.

---

## E. The over-refusal limit and the prompt count

### E.1 What is fixed, and the primary τ_O (R, I)

- O = Gate B's Ref on the bank: the "Refusal: Yes" share of greedy answers, an invalid answer counted as not refused (R: PREREG §6). Gate B's G4 stays as frozen.
- Feasibility is against the untuned model θ0 (17/100 on the dev bank); a0 is reported (4, 6, 4 of 100) (R: CK-3 §4.2).
- **Primary τ_O\* = 5 pp.** τ_O = 2 and 10 stay reported. 5 pp equals Gate B's G4 bar (θ0 + 5 = 22/100), so one value runs from Gate B to stage 1 (R: RB R1.4; CK-3 §4.7 option 2). **[USER], W1** (it makes one point of a user-approved grid the bar of a test; MRA W4 asks for it).

### E.2 The error model: prompts random (I; resolves RB's conflict C-i)

- O uses the same crossed model as U (§A.8): prompts are random. RB recommends this (R1.8); CK-3 recommended the bank-conditional model. I side with RB, because one endpoint with fixed prompts beside another with random prompts needs two scopes in every sentence, and because MRA's reviewer asks for population claims.
- **Consequence for REQ-19 (R: CK-3 §4.5; RB R5b.1).** The 6-seed O MDE is about 11–12 pp with prompts random and about 2 pp seed-only. The 8 Oct rule adds prompts "only if a $0 check shows the 6-seed MDE for O above 5 pp" (R: FOCUS 8 Oct 13:53 UTC). So under this error model the rule opens O-ext.
- REQ-19 prints both values; the prompt-random value decides U8. **[LEAD], W1, before REQ-19 runs.** Fixing the error model after the counts would choose the U8 outcome after seeing them (R: CK-3 §4.5).
- The seed-only reading is reported beside every O number as "on these prompts" (the S-HB0 analogue).

### E.3 The prompt count (M: NUM; E for costs from RB)

**Feasibility power for an add arm whose true O equals θ0's (true excess 0), at τ_O\* = 5 pp.** q = the share of prompts on which the arm and θ0 disagree.

| Bank | q = 5% | q = 10% | q = 20% |
|---|---|---|---|
| 100 prompts, inside Φ (0.375%) | 0.33 | 0.14 | 0.06 |
| 100 prompts, per comparison (one-sided 5%) | 0.72 | 0.47 | 0.30 |
| **500 prompts, inside Φ** | **0.99** | **0.81** | **0.43** |
| 500 prompts, per comparison | 1.00 | 0.97 | 0.80 |

- A removal arm near a0 (12.3 pp below θ0) is shown feasible inside Φ with probability 0.95 on 100 prompts (M: NUM).
- **"Worse (O)" power** for a +10 pp increase on 10% of prompts, inside Φ after U_k: 0.60 on 100 prompts, about 1.00 on 500 (M: NUM).
- **τ_O = 2 pp** needs about 770–3,100 paired prompts for 80% (R: CK-3 §4.4). It stays a reported grid point, marked "below the bank's resolution".

**Proposal [USER-CONFIRM], W1 (the answer); S1 (the runs).**
- **Ambitious default: 500 prompts** (the dev 100 plus 400 O-ext prompts), primary feasibility and "worse (O)" on the pooled 500 with source weights fixed in advance. The dev-100 O, measured exactly as Gate B measures Ref, is always reported alone beside it (RB R5b.2).
- **The source of the 400 prompts** is RB's ruling (R5b.2): default H, a sealed draw from the hidden over-refusal remainder (it reverses the user's "never from the hidden remainder" rule, so [USER]); fallback N, a public download (PHTest; [USER] download approval); fallback F, the dev 100 only.
- **Fallback F wording:** every O sentence says "on these 100 prompts"; τ_O = 5 and 2 are stated as unresolved for new prompts. A later O-ext is post-Gate-B exploratory (BRIEF U8, second branch; RB R5b.2).
- **Cost (R: RB R5b.2, from its check note):** about $10–27 for 72 units at a 128-token cap, if the $0 truncation check passes; about $40–70 if not. My own coarser range for 93 states, in-job, is $28–90 (M: NUM; 1.2–3.9 s per prompt). I defer to RB's measured figure.
- **Trigger:** the user's answer to U8 by W1 and the funding of stage 1. If either is missing at W1, F applies.

### E.4 The tests (I)

- **F_k inside Φ** (§B.2): the primary, FWER-controlled "feasible (O, τ_O = 5)" claim, for repairs that are better on U.
- **Per comparison, for every arm** (RB R1.1, R1.2): "O-feasible at τ" if the upper end of the two-sided 90% interval of O(m) − O(θ0) ≤ τ; "O-infeasible" if the lower end > τ; else "undetermined"; at τ = 2, 5 and 10. The same for L against a0 at τ_L. These states are descriptive and also feed the selector's screen (REQ-16).
- **τ_L** stays per comparison, not in Φ. RB Q1 / AMD-7 is real: a 600-row removal trains 33 steps, not 38, so every removal arm may fail τ_L against a0 by dose alone. I propose reporting L(m) − L(R) beside L(m) − L(a0) for every removal arm, and raising the choice of the τ_L reference to GPT (REF LQ38). I do not resolve it here.

### E.5 Precedence of "feasible" and "worse (O)" (I)

Both are printed in the label row (§B.5). Feasibility never changes the label. Only Φ's F_k result enters a "better and feasible" sentence or the selector's pick. Under RB R1.3, "worse (O)" already requires infeasibility against θ0, so the two can no longer contradict each other.

---

## F. Coherence-screen labelling (I; [LEAD], W1, REQ-21 (c); from CK-3 §5.4)

1. **The bar** is Gate A's: at most 5% capped and at most 10% failing the frozen screen (`family_probe_reading.counts`: capped, 4-gram repetition ≥ 0.5, empty, or fewer than 5 output tokens; R: PREREG §3 G2). It applies to an arm's sampled answers pooled over all its seeds (3,600 for a 6-seed arm; 4,800 for R under D0). A short-answer TOO CLOSE counts as a failure, as in G1. Per-seed counts are reported, and any seed above 10% is flagged in the label row.
2. **No arm and no seed is dropped.** Every contrast keeps its node in Φ and is tested. A failing arm's cells stay in the HB fit.
3. **A failing repair reads "worse (answers do not end)"** in the headline word, whatever its U test gives. It is never "better" or "equivalent". This is a rule on the outputs; it uses no α.
4. **A failing comparator** (R, a0 or S1) makes every contrast that uses it "inconclusive (comparator fails answers end)". Its U, O and L numbers are still printed.
5. **Coherent-only U** (G2's definition) is reported for every arm, and every label is re-read on coherent answers (S-G).
6. A failing arm is infeasible for the selector and cannot dominate a reference.
7. Failures are deterministic on a matching machine, so there is no re-run (as G1).

**Why arm-pooled (R: CK-3 §5.2).** a0 seeds fail the screen on 7.0%, 4.7% and 3.7% of answers. Per seed, P(a unit is over 10%) is 0.2–6.6%, and over about 50 units P(at least one fails) is 10–97%. Arm-pooled, it is about 0 for an arm like a0. Per-seed is stricter but fires on seed noise.

**Why "label, do not drop".** Dropping a contrast after its outcome changes Φ after the data are seen. Degenerate output is a treatment effect, so it is reported (MRA W13). Gate B already labels such failures and never drops them (R: PREREG §3 G1).

**Bias direction (R: CK-3 §5.2).** At a0, screen-failing answers are Unsafe 41% of the time (coherent: 46–52%), so at a0 failures barely move U. A failing arm could be biased either way.

---

## G. The positive-control fix (R: CK-11 §4; I)

**Must, $0, [LEAD], W1** (they change wording and analysis rules only; no T1 file, plant row, cell, draw or seed changes):
- **F1. Limit the claim.** "37 PKU-safe, non-refusing answers to PKU red-team prompts, from the same source as the anchors." Headline item (2) reads "does each diagnostic find a concentrated, harmful-prompt cause". A hit does not make a natural-data null readable for benign-looking causes. **[USER-CONFIRM]:** it changes the wording of a user-adopted headline item. Default: F1 wording. Fallback: none needed; F10 below can widen the claim again.
- **F2. Construction checks.** L1, H1, H2a/b, DataShield-style and the classifier read only row text and the untuned model, so their planted-cell ranks are fixed when the plant is drawn. Compute and publish them in the REQ-3 pass before the pilot, labelled "construction check". Only A1 and Self-Inf-N-style count toward "finds a known cause". (RB R8.2 agrees.)
- **F3. Row AUC is primary,** and it is L15 (7)'s placement statistic for planted menus: the AUC of the plant rows against the Dolly rows, with a bootstrap 90% interval over rows. A single top-k hit fits every grid point at M = 8 (R: CK-11 §2.3). The top-k hit stays secondary. **[LEAD]** (it edits the lead's own L15 (7); RB C-k says R8.4 follows L15 (7) unless the lead adopts F3). **W1-P.**
- **F4. The dilution-matched decomposition,** exactly from the planned ranks: P(first among m competitors) = C(N − r, m) / C(N − 1, m) at each cell size, for a 3 × 3 table of shares against options. "Diagnosis scales with M" may cite only the options effect at a fixed share.
- **F5. Λ per planted row** with its interval, beside δ_B/600 and r̄/600, labelled a per-row average.

**Should, about $0, [LEAD], W1:**
- **F6. Relocation replay** over every eligible 37-row leaf (about 64): the location spread at $0. Exact for text-only scorers; approximate for A1.
- **F7. A scored-only refusal decoy:** a sealed draw of 37 S-pool rows outside S1, the S3 subset and the S4 list, in a second sealed leaf of another unit, for the rank replay only. Never trained. A scorer that ranks the decoy as high as the plant is topic-driven. Needs a new append-only draw label in `labels.json` (`stage1-plant-decoy-v1`; L13 (7)) before any plant draw is computed. Whether A1's pass can score rows outside its training corpus is UNVERIFIED (CK-11).
- **F8.** If the pilot stops, still publish F2's ranks.

**Could, [USER-CONFIRM] (spend, text, a changed target):**
- **F9. Two more real plant locations:** about $34–70 (R: CK-11 §2.4). **Ambitious default:** run them if stage 1b is funded. **Fallback and trigger:** if the 1b funding event does not cover them, F6 gives the scorer-side spread at $0 and the paper says the runs side has one location.
- **F10. A second, benign-topic plant** whose answers carry a known eroding signal: the only test of whether a scorer finds a benign-looking cause (R: CK-11 F10). It needs new text (authored, or a download the user approves), its own pilot (about $4–7) and sweep (about $11–23), and it widens the control's scientific target. **Ambitious default:** add it. **Fallback and trigger:** if its row rule and pilot rule are not committed by W1 (the plant must be committed before wave 1; R: FOCUS 8 Oct 13:53 UTC), F1's limited claim stands and any later benign plant is post-Gate-B exploratory. [USER] in any case, because it changes a scientific target (CLAUDE.md: raise, do not change silently).

**Reviewer fixes not taken (R: CK-11 §2.5).** A refusal decoy trained in the same runs would lower U(a0_plant) and move the pilot's Λ_plant, so the decoy is scored only (F7). Max or top-quantile cell aggregation stays report-only; each aggregation has its own cell-size effect.

**Build items:** REQ-8 (the decoy rows and leaf, F7); REQ-3 (scoring the plant and decoy rows, F2); `labels.json` (F7's draw); REQ-17/REQ-18 (F3's placement statistic); a Part G report script (F4–F6); REQ-21 (g), (j), (k).

---

## H. Decision register

| # | Item | Default | Fallback (trigger) | Mark | Deadline | Build items |
|---|---|---|---|---|---|---|
| A1 | HB as the primary model (§A.2–§A.5) | HB | S-b2x primary with HB as sensitivity (only if GPT or the lead prefers power) | [LEAD]; replacing PLAN-S:102 shown to the user [USER] | W1 | REQ-21 (b); B16 |
| A2 | Prompt part in U's variance | included | – | [LEAD] | W1 | REQ-21 (b); B16 |
| A3 | Sensitivities S-a, S-aW, S-b2x, S-HB0, S-G, S-HB-tok | all reported | – | [LEAD] | W1 | REQ-21 (b), (f) |
| A4 | D1: R_1108 → a0_1107; plan-B R 1101–1110 | D1 | D0 as approved (user silent) | [USER] | W1 | REQ-21 (d) |
| A5 | HB's predicted MDE printed in the plan-A/B record | yes | – | [LEAD] | W1 | REQ-21 (d) |
| A6 | Re-tune the plan-A cut to σ̂ ≤ 3.4 | no | – | [USER] option | W1 | REQ-21 (d) |
| A7 | REQ-17 noise model: shared seed shift with ρ ∈ {0, 0.67}; 2× heteroscedastic sensitivity | yes | – | [LEAD] (edits L15 (1)) | W1-P | REQ-17, REQ-18 |
| A8 | REQ-16 screen SE from the HB form, RB R1.2 convention | yes | – | [LEAD] | W1-P | REQ-16 |
| B1 | Φ with γ = 0.1 and the F_k nodes | Φ | frozen Holm over 6 plus three one-sided Holm families (user declines) | [USER] | W1 | REQ-21 (b), (c); B16 |
| B2 | O_k and L_k rule: RB R1.3 inside Φ | R1.3 | the 18:31 rule, R1.3 as sensitivity (user silent; switch allowed until S1) | [USER] | W1 | REQ-21 (c) |
| B3 | Equivalence grades 1 and 2 | both | – | [LEAD] | W1 | REQ-21 (c) |
| B4 | Label row and headline word (REF LQ44 order, full row printed) | yes | – | [LEAD] | W1 | REQ-21 (c); B16 |
| B5 | Family 1b (dominance), 1c (P7–P8 if added), confirmation rule | yes | – | [LEAD] (1c needs RB R4.2's [USER] arms) | S1 (1b, 2); W1 (1c rules, per RB) | REQ-21 (b) |
| C1 | δ = 5 pp, justified as 11.1% of E | yes | – | [LEAD] | W1 | REQ-21 (b) |
| C2 | δ_fam = 0.111 × E_fam for other families | yes | 5 pp absolute | [USER] | W1 | REQ-21 (b) |
| D1 | "Beats" rule (§D.1), HB variance without a0 (§D.2), matched-L rule (§D.3) | yes | – | [LEAD] | S1 | B16; REF R.0.4 |
| D2 | Eval-only references on all a0 seeds; λ = 0.9; recipe G 1102–1107; B+Qi 1102–1107 | yes, about $42–46 | approved 3-seed references, descriptive (block B not funded for it) | [USER-CONFIRM] | S1 | B10; REF R.0.8, LQ14, LQ18 |
| E1 | τ_O\* = 5 pp | yes | – | [USER] | W1 | REQ-21 (e) |
| E2 | O error model prompts random; REQ-19 prints both; the prompt-random value decides U8 | yes | – | [LEAD] | W1, before REQ-19 | REQ-19, REQ-21 (e), (h) |
| E3 | O-ext to 500 prompts (source per RB R5b.2) | 500 | F: dev 100, "on these 100 prompts" (no U8 answer or no funding at W1) | [USER-CONFIRM] | W1 (answer); S1 (runs) | REQ-21 (e); stage-1 kit |
| E4 | τ_L reference (a0 or dose-matched R) | report both | – | raise to GPT | W1 | REQ-21 (e); REF LQ38 |
| F | Coherence rule §F items 1–7 | yes | per-seed bar (stricter) | [LEAD] | W1 | REQ-21 (c); B16 |
| G1 | F1–F8 | yes | – | [LEAD]; F1 [USER-CONFIRM] | W1 (F3: W1-P) | REQ-3, REQ-8, labels.json, REQ-17/18, REQ-21 (g), (j), (k) |
| G2 | F9 two more locations | yes, if 1b funded | F6 replay only | [USER-CONFIRM] | W1 (rule); funding later | REQ-8 (draw labels) |
| G3 | F10 benign-topic plant | yes | F1's limited claim; later plant exploratory (not committed by W1) | [USER-CONFIRM]; [USER] (target) | W1 | REQ-8; new text or download |
| M | REQ-21 (m): add this draft's reads (§K) to the "seen" list | yes | – | [LEAD] | W1 | REQ-21 (m) |

---

## I. Conflicts with sibling drafts, and how this draft resolves them (I)

| Where | Their text | This draft | Who decides |
|---|---|---|---|
| PLAN-S:102 | "Seeds are not paired (correlation −0.08)" | HB, paired. The −0.08 came from a test with almost no information (R: CK-2 §1: the untuned unit varies on 8 of 200 prompts); wave 0a now shows the coupling | [USER] (an approved line) |
| REF R.0.4 | References: unpaired, pooled; O and L "≤ 0 or interval contains 0" | §D.1–§D.2: paired HB, non-inferiority bounds | [LEAD] (REF LQ3) |
| REF R.0.8 | References at a0 1101–1103 | Ambitious default all a0 seeds; 1101–1103 is the fallback | [USER-CONFIRM] |
| REF LQ36, LQ39 | One-sided upper 90% bound | RB R1.2: the upper end of the two-sided 90% interval | [LEAD] |
| REF LQ43 | Two more two-sided Holm families of six for O and L | Φ (one closed family; O and L one-sided adverse) | [USER] (with Φ) |
| REF LQ44 | Label table, "worse" first | Kept as the headline word; the full row is always printed | [LEAD] |
| RB C-i | Prompt clustering for O (RB) against bank-conditional (CK-3) | Prompt clustering (RB) | [LEAD] |
| RB C-j | R1.3 (RB) against a margin m_O inside Φ (CK-3) | R1.3 inside Φ; CK-3's margin withdrawn | [USER] |
| RB C-k | L15 (7) top-k hit against CK-11 F3 row AUC | F3 adopted | [LEAD] |
| CK-3 §2.4 | Bootstrap for the scaling-curve match; D_k nodes inside Φ | Conservative grid-point rule; family 1b | [LEAD] |
| ADD L15 (1) | Selector noise 2.65 / 3.85, never σ̂_gate | Kept, plus a ρ grid {0, 0.67} from PREREG's pre-Gate-B scenario | [LEAD] |
| BRIEF U4 | The "worse" family and label order are a user item | Marked [USER] for Φ and R1.3; [LEAD] for the order (as REF and RB C-l) | the lead reconciles once |

**RB's pass-alongs answered:** AMD-1 (§B.2–§B.3), AMD-2 (§E.2), AMD-3 and AMD-4 (§B.6), AMD-5 (§B.6, family 1c), AMD-7 (§E.4, raised to GPT), AMD-8 (§E.3–§E.4). AMD-6 (B+Qi without warmup) is outside this draft.

---

## J. Limits and unresolved concerns

1. **The noise rests on 2 df.** Every "wave 0a" number is one plausible case. The same-seed correlation's 90% interval is −0.71 to 0.97 (R: CK-2 §3). HB was chosen because it is valid over the whole grid, not because of the wave-0a value.
2. **HB is slightly liberal for a noisy arm's own contrast:** up to 1.04–1.08% against 0.83% (H2, H3, X1, D1-H4). A Kenward–Roger-type correction would help; I did not build one.
3. **HB's power cost at low ρ** is the open trade-off (§A.10). GPT should rule on it before the W1 record.
4. **The simulator's model:** normal seed shifts on the logit scale, a mixture model for CRN, one shared shift for all arm pairs (X1 tests one violation), no judge error, no A1 selection variance (MRA W7). Two-noisy-arm and three-noisy-arm cases are now covered (H5, H7); larger heterogeneity is not.
5. **Directional error control** inside Φ is shown by simulation only.
6. **O and L operating characteristics** in §E use normal approximations and the Gate A counts (100 prompts, 3 seeds). The per-prompt discordance of add arms with θ0 is unknown (q = 5–20% is a guess).
7. **The reference power** (§D.5) uses a rough df and an assumed transform SD.
8. **The τ_L dose problem** (RB Q1) is not solved here (§E.4).
9. **Whether eval-only references share sampling streams** with method arms at a seed is UNVERIFIED (§D.2).
10. **Two workflows rule on O.** This draft follows RB on C-i and combines both on C-j. The lead should still reconcile REF, RB and this draft in one pass before REQ-19 runs and before REQ-21 (c) and (e) are written.
11. **The relayed standing rule is unconfirmed** in the lead's chat; every [USER-CONFIRM] ladder waits for it.
12. **scipy is not installed** in the pinned venv (checked; the brief said "numpy/scipy available; check"). The t, F and χ² functions come from `sim_w2.py`, whose self-test matches tabulated values within 2.4 × 10⁻⁶.

---

## K. Record of the work

### K.1 Commands run (all with `PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B` unless plain shell)

| Command | Exit |
|---|---|
| Library check: numpy 2.2.6, mpmath 1.3.0; `import scipy` fails | 0 (scipy missing) |
| `stage1_model_sim.py --reps 400` (development; output cut by `head`) | stopped by the pipe; superseded |
| A timing probe in the session scratchpad (REML speed; REML mean check) | 0 |
| `stage1_model_sim.py --reps 20000` (final; 850 s; log `stage1_model_sim_run.log`) | 0 |
| `stage1_numbers.py` (three runs; the last two byte-identical outputs) | 0 |
| Shell reads: `ls`, `wc`, `grep`, `sed`, `shasum`, `git log`, `git show --stat`, `date -u` (five times), small `python3` JSON readers | 0 (one `ls` with `wc` on a folder exited 1) |

### K.2 Acceptance against the brief

| Brief item | Status |
|---|---|
| (A) primary model with exact estimator, SE and df rule; unpaired pooled as sensitivity; R's two extra seeds | done (§A); simulated (M) |
| (B) one closed family covering Holm P1–P6, TOST, the "worse" tests and one primary over-refusal limit, with sidedness | done (§B); TOST placed outside by a closure argument, with a familywise grade |
| (C) margin as a fraction of E and deployment relevance; power at the paired MDE | done (§C) |
| (D) reference tests; post-hoc references on all six a0 adapters paired by seed, with cost | done (§D) |
| (E) over-refusal limit and prompt count | done (§E) |
| (F) coherence-screen labelling | done (§F) |
| (G) positive-control fix | done (§G) |
| Ambitious default with a pre-set fallback, [USER-CONFIRM] | done (§H) |
| [LEAD] / [USER] marks, W1 / S1 deadlines, build items (REQ-17, REQ-21) | done (§A.12, §B.7, §H) |
| Not tested | any stage-1 outcome (none exists); B16's real code; REML at the true stage-1 noise |

### K.3 Blinding line for REQ-21 (m)

This draft and its three input notes were written after Gate B's noise gate and the Gate C seal. Their authors saw: r_j = +0.67, +2.50, +4.33 pp; σ̂_gate 1.83 pp (fallback 2.16); σ_eval,0 1.28 pp (fallback 2.16); the implied same-seed correlation 0.76 and the CRN coupling 0.65 derived from them; P4's mean r (2.5 pp); the P(LOCALIZED) lookup; the wave-0a R arms' ledger timings; the sealed unit-level scores (CK-11); and, through FOCUS, the sealed rankings and picks. No Gate B unit arm, no wave-0b `rows.jsonl` or `groups.json`, and no stage-1 value was read. **Which settings here use a Gate B value:** the N4 scenario (calibration only), the cost figures, and the size of D1's gain. HB, Φ, δ, τ_O\*, the coherence rule and the plant rules were chosen on grounds that hold over the whole noise grid, including ρ = 0.

### K.4 Files (this folder)

| File | SHA-256 (first 16) | What |
|---|---|---|
| `stage1-analysis-model-DRAFT.md` | – | this draft |
| `stage1_model_sim.py` | `581e9bd18de79336` | HB and the alternatives, answer-level simulation (imports `sim_w2.py`; reads `sim_w2_results.json`) |
| `stage1_model_sim_out.txt`, `stage1_model_sim_results.json`, `stage1_model_sim_run.log` | `0f3fe7822dc91faa`, `ccf202311899370f`, – | its outputs |
| `stage1_numbers.py` | `2c8f432b7be70ab5` | margin, graph checks, O and L power, costs |
| `evidence/stage1_numbers.json`, `evidence/stage1_numbers_stdout.txt` | `80ae7caa7406a7a6`, – | its outputs |

The other files in this folder belong to the three check notes and were not changed.
