# Check of mock review A, W2 and W5: the stage-1 analysis model

- **For:** the main-study lead (GI VI). **Written by:** an Opus worker. Clock: `date -u` gave 2026-10-16 22:49 UTC (17 Oct local) before this file was written.
- **Status:** read-only check. No repository edit, commit, pod, spend or download. I opened no `selector.jsonl`, no `hidden/` folder, no held-out file and no wave-0b `rows.jsonl` or `groups.json`. I read labels and counts only. I printed no prompt id, prompt text or answer text.
- **Labels.** **M** = measured here (the source follows). **R** = read (path:line). **E** = estimate from the simulation in `sim_w2.py` (the basis follows). **I** = inference.
- **Files.** Code: `sim_w2.py`. Output: `sim_w2_out.txt` (all numbers below), `sim_w2_results.json`, `sim_w2_run.log`. All are in this folder. `python sim_w2.py --tables` prints the tables of §5 from the JSON.

**Sources** (main checkout, read only; SHA-256, first 16 characters):

| Short name | File | SHA-256 |
|---|---|---|
| MRA | `writing/paper/2026-10-17-mock-review-A-methods.md` | `ff0e4382d542f85e` |
| PLAN-S | `research/review/2026-10-08-sharpened-direction-DRAFT.md` | `6ff3ff2b15bc4295` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (revision 5, frozen) | `5c97cce78cfad2c1` |
| NG | `research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json` | `4b817f73d968b89a` |
| FOCUS | `research/FOCUS.md` | `23e3da8f893e8135` |
| BRIEF / LD | `.ai/briefs/stage1-commitments-build-20261016.md` / `…-lead-decisions.md` | `12cbf46318728d32` / `114776482a3287dd` |
| TEX | `writing/paper/icml/main.tex` | `0b9e49881a37e0d4` |

Gate A units: the three a0 units (seeds 1101–1103) and the untuned unit, by the paths in `tmp/gate-b-olmo/gate_b_inputs_noise_gate.json`. Their `job.json` and `COMPLETE.json` hashes equal NG's `units` records (M). Labels come from `guard_samples.jsonl` through `scripts/family_probe_reading.py` (`_unsafe`, and `counts` for the cross-check). My counts equal the frozen counts: 280, 281, 308 and 19 of 600 (M).

---

## 1. Short answer

**W2: partly holds.**

- **Holds.**
  - One noisier arm breaks the pooled-variance test. The reviewer's number reproduces (§4).
  - The blinded seed rule reads a seed-paired SD. Its cut-offs match per-arm noise only when the same-seed correlation ρ is 0. With the wave-0a ρ, a reading of 4.5 pp (plan A) can go with a per-arm SD of 6.4 pp. The current analysis then has an MDE of 11.9 pp (E, §5).
  - Prompts are a crossed factor. Any paired or blocked analysis must add a prompt term. Without the term, the family-wise error reaches 9–23% in my arm × prompt scenarios (E).
- **Does not hold as stated.**
  - PLAN-S planned the MDE on the per-arm scale (2.65 and 3.85 pp; R: PLAN-S:117), not from a paired SD.
  - "If ρ > 0, the stage-1 MDE is understated" is wrong for the current analysis. Same-seed arms share seeds, so a positive ρ makes the unpaired test conservative. Its true MDE then falls: 4.9 pp at wave-0a noise, against 5.2 pp planned (E). The MDE grows only if the per-arm SD itself is larger than planned.
  - The reviewer's own fix (a seed-blocked model with a pooled residual) gives 2.8–2.9 pp only when all arms are equally noisy. With one noisier arm, it fails about as badly as the current analysis at ρ = 0 (family-wise 5.8–10.0%, against 7.1–12.2%). At the wave-0a ρ it fails much worse: 12.7–17.2%, against 4.5–5.2% for the current analysis (E).
- **New, not in the review (M).**
  - Wave 0a shows a strong same-seed coupling in sampling. The per-prompt difference SE is 1.28 pp for seed-matched pairs and 2.16 pp for pairs that are not seed-matched. This implies a per-answer correlation of 0.65.
  - PLAN-S:102 rejects pairing because of a correlation of −0.08. That figure comes from the untuned unit against seed 1101 (PREREG:121; its other pair, 1101 against 1102, has no shared streams and is only a control). The untuned unit varies on only 8 of 200 prompts (3 in both units). The test had almost no information.
  - The training-seed part of ρ cannot be estimated on 2 df: the 90% interval is −0.71 to 0.97. FOCUS has a second same-seed pair (recipe B against recipe G), and its ρ̂ is −0.88.

**W5: holds**, with two corrections to the reviewer's numbers.

- "6.6 pp (6 vs 6)" for the 80%-power "better" effect is the value at the 4.5 pp cut-off. At central noise it is 6.3 pp, as the review's own table says (MRA:291).
- "A true 3 pp effect that is significant gets 'equivalent'" cannot happen under the current analysis at central noise. Significance needs |estimate| > 3.96 pp, and "equivalent" needs |estimate| < 2.59 pp. It becomes common under a paired or blocked analysis: a true 3 pp effect is labelled "equivalent" 74–84% of the time (E, §7). So W2's fix makes W5 sharper.

**The reviewer's numbers:**

| Claim (MRA line) | Reviewer | This check | Verdict |
|---|---|---|---|
| Holm step-1 MDE, 6 vs 8, central (:290) | 5.2 pp | 5.20 analytic; 5.2 simulated (E) | reproduces |
| Paired or blocked MDE (:407) | 2.7–3.8 pp | 2.8 (P1), 2.9 (P4) for a blocked model with a pooled residual (df 35). 4.1 (P1) and 5.1 (P4, 5 pairs) for paired per contrast (5 or 4 df). All at the wave-0a pair SD of 1.83 pp on 2 df (E) | partly: the lower end needs a pooled residual. At ρ = 0, paired per contrast gives 8.2 pp |
| One arm at 2× SD, one-sided at α/6 (:87) | 0.8% → 4.6% | 0.83% → 4.46% (10⁶ replicates; t at 42 df); 5.10% with a normal critical value (E) | reproduces (the reviewer's value lies between the two) |
| One arm at 3× SD (:87) | 8.1% | 7.91% (t at 42 df); 8.72% (normal) (E) | reproduces |
| Implied same-seed correlation (:405) | about 0.76 | 0.766 (sample), 0.760 (a0 scale), 0.619 (pooled scale); 90% interval −0.71 to 0.97 (M) | reproduces; "very uncertain" is right |

---

## 2. Which same-seed pairs exist

**Seeds (R: PLAN-S:116; FOCUS:242):** method arms at 1102–1107, R at 1101–1108 (draw d at seed 1100 + d; PREREG:79), a0 at 1101–1106 (1101–1103 are the Gate A units).

| Contrast | Same-seed pairs | Seeds without a partner |
|---|---|---|
| P1–P3: R − A1, L1, H1 | 1102–1107 (6) | R 1101, R 1108 |
| P4: a0 − S1 | 1102–1106 (5) | a0 1101, S1 1107 |
| P5, P6: S1 − S3, S1 − S4 | 1102–1107 (6) | none |

**What same-seed arms share** (R):

- The same adapter initialization: `torch.manual_seed(derive_seed(seed, "torch-global"))` (`experiments/safety_selection/runner.py:304`).
- The same sampling seed for each prompt and sample: `sample_seed(job_seed, prompt_id, index)` (`runner.py:630`).
- The same shuffle of all 4,800 rows (`stream.py:64`).
  - In a removal arm, the removed rows drop out and the kept rows keep their relative order. Batches form again from step 1, so same-seed removal arms share no batch (PREREG:86).
  - In an add arm, all 4,800 rows keep their positions. The 48 added rows go in at evenly spaced positions, in a seed-fixed order (`stream.py:64-79`). So S1, S3, S4 and a0 at one seed share nearly the same batches. P4–P6 pairs are therefore probably tighter than the a0–R pair (I).
  - A1 and R_d each remove 600 rows and share about 75 of them, so their kept sets differ by about 1,050 rows. a0 and R_d differ by 600 rows. So P1–P3 pairs may be a little looser than the a0–R pair (I).
- **Cross-engine pairing.** The Gate A a0 units ran on engine 55253874. The stage-1 arms run on engine X. Pairing across engines rests on the wave-0b fingerprint check at seed 1101, which passed (NG post-wave-0b: fingerprint trigger false; M). Seeds 1102–1103 are inferred from it (R: PREREG:106).
- **R_1108 under a seed-blocked model.** R_1108 is the only cell at seed 1108, so its leverage is 1 and it carries no information on any primary contrast. a0_1101 and R_1101 inform the contrasts only through each other (M: the design matrix in `sim_w2.py`).

---

## 3. Measured noise (Gate A and wave 0a)

| Quantity | Value | Label |
|---|---|---|
| U(a0), seeds 1101 / 1102 / 1103 | 46.67 / 46.83 / 51.33 pp; untuned 3.17 pp | M |
| U(R_j) = U(a0_j) − r_j | 46.00 / 44.33 / 47.00 pp (276, 266, 282 of 600) | M (r_j from NG) |
| Per-arm seed SD, a0 | 2.65 pp (2 df; 90% CI 1.53–11.7) | M |
| Per-arm seed SD, R | 1.35 pp (2 df; 0.78–5.95); var(a0)/var(R) = 3.86, one-sided P = 0.21 | M |
| Per-arm seed SD, pooled | 2.10 pp (4 df; 1.36–4.98) | M |
| Paired same-seed SD, sd(r_j) = σ̂_gate | 1.83 pp (2 df; 1.06–8.09) | M (NG) |
| Implied same-seed ρ | 0.766 sample; 0.760 from a0's variance; 0.619 from the pooled variance. P(r ≥ 0.77 \| ρ = 0, n = 3) = 0.22. 90% interval −0.71 to 0.97 | M |
| Second same-seed pair (recipe B against G, E by seed; FOCUS:196, order assumed 1101–1103) | ρ̂ −0.88; paired SD 4.76 pp | M from R numbers |
| Prompt-clustered SE per a0 unit | 2.78–2.83 pp (untuned 1.05) | M; reproduces PREREG:120 |
| Within-prompt sampling SE per a0 unit | 1.50–1.55 pp | M; reproduces PREREG:120 |
| Share of clustered variance between prompts | 69.0–72.0% | M; reproduces PREREG:120 |
| a0 seed pairs: per-prompt difference SE | 2.08–2.16 pp. Pure sampling: 2.13–2.17 (ratio 0.97–1.00), so there is no prompt × seed term. Per-prompt count correlation 0.70–0.73 | M; reproduces PREREG:120 |
| Within-prompt residual correlation | −0.077 (1101–1102), +0.006, −0.006; untuned–1101 (shared streams) −0.078 | M; reproduces PREREG:121's "−0.08" |
| σ_eval,0: seed-matched a0–R pairs / R–R pairs, not seed-matched (fallback) | 1.28 / 2.16 pp | R (NG) |
| Per-answer same-seed coupling c = 1 − (1.28/2.16)² | 0.65 (0.646 against a0's own pure sampling) | M |
| Training part of var(r_j) = 3.36 − 1.28² | 1.72 pp² (SD 1.31; 2 df) | M |
| Shared training-seed variance (total − sampling − arm-specific) | +3.83 (a0), −1.36 (R), +1.24 (pooled) pp² | M; a negative value means 2-df noise |

**What this says (I).**

- **Sampling.** Arms at the same seed draw strongly coupled samples when the models are close. The evidence is σ_eval,0 at 1.28 pp against 2.16 pp, on 200 prompts. This part of the pairing gain is well supported. It gives ρ ≥ about 0.2 even if the training seeds share nothing (scenario N2).
- **Training.** Whether same-seed arms also share a training-seed shift is unknown. The 2-df data allow anything from ρ ≈ −0.7 to ≈ 1. The recipe B–G pair even points the other way, but recipe G changes the loss and the schedule, far more than any stage-1 arm.
- **Old test.** PLAN-S:102 justified the unpaired analysis with a CRN test that could not detect the coupling. Wave 0a now shows the coupling.
- **Samples per prompt.** Sampling is about half of the paired seed-level variance (1.64 of 3.36 pp²). Six samples per prompt instead of three would cut the pair SD from 1.83 to about 1.59 pp, and the per-arm SD from 2.65 to about 2.42 pp (E, arithmetic on the rows above). This costs generation time on every arm.

---

## 4. The reviewer's arithmetic, re-computed (E; exact t quantiles; the SE estimate drawn from its χ²)

| Item (MRA line) | Reviewer | Here |
|---|---|---|
| SE 6 vs 8 / 6 vs 6 at per-arm 2.65 (:290–291) | 1.43 / 1.53 | 1.431 / 1.530 |
| Holm step-1 MDE, t at 42 df (:290–291) | 5.2 / 5.5 | 5.20 / 5.56 (normal, as PLAN-S:117: 4.98 / 5.32) |
| 80% "better" effect (:290–291, :133) | 6.2 / 6.3 (table); "6.2 to 6.6" (text) | 6.22 / 6.30. The 6.6 of the text is the 4.5-cut value (6.56) |
| At the 4.5 cut read as a pair SD (per-arm 3.18) (:293) | 6.2 / 6.6 | 6.24 / 6.67 |
| Per-arm 4.5, or ρ 0.5 at pair SD 4.5 (:86, :293) | about 8.8 | 8.83. With the covariance of shared seeds, the unpaired test's real MDE at per-arm 4.5 and ρ 0.5 is lower (not computed exactly; at per-arm 3.75 it is 6.96 against 7.36) |
| ρ = 0.5, pair SD 3.75 → per-arm 3.75 → MDE (:86) | about 7.3 | 7.36 if the covariance is ignored; 6.96 with it |
| Welch factor at about 11 df (:95) | 3.62 → 4.08 SEs, +13% | 3.619 → 4.084 (Welch df 10.9) |
| P(equivalent \| 0), unadjusted / adjusted, central (:297) | 0.93 / 0.56–0.68 | 0.926 (6v8), 0.884 (6v6) / 0.672, 0.553 |
| Same at the 4.5 cut (:120, :297) | 0.70–0.78 / 0.32 | 0.776, 0.697 / 0.327 |
| Per-arm 1.7× (option B, :410) | P(equivalent \| 0) ≈ 0.29 | 0.295 at per-arm 4.5 |
| Reviewer's heteroscedastic replica (:87) | 4.6% (2×), 8.1% (3×) | 4.46%, 7.91% one-sided at α/6 (t at 42 df; 10⁶ replicates); two-sided 6.0%, 12.0%; Welch one-sided 0.94%, 0.98% |
| 5 pp as a share of E (:128–131) | 11%; 25% at E = 20; 9% at 55 | 11.1% (E = 45.11 over all three seeds); 25%; 9.1% |
| 5 pp of U → usable help (:132) | about 1.7 pp | 1.67 pp (arithmetic only; I did not check the "about a third" premise) |

---

## 5. Simulation of the stage-1 primary family (E)

### 5.1 Model

Each replicate builds the 50 cells of the plan: a0 (6 seeds), R (8) and six method arms (6 each), from seeds 1101 to 1108. Each cell has 200 prompts × 3 sampled answers.

- **Prompt bank.** Logit-normal, fitted to the pooled Gate A a0 counts (mean −0.142, SD 2.295). It gives a mean U of 48.0 pp, a per-arm sampling SE of 1.52 pp and a clustered SE of 2.80 pp. The fit to the 0–9 count histogram is close (`sim_w2_out.txt`). A new bank is drawn per replicate.
- **Seeds.** One shift is shared by all arms at a seed. Each arm has its own seed shift on top. Both are on the logit scale.
- **CRN.** Each answer uses its seed's shared uniform with probability √c, so two same-seed answers are coupled with probability c.
- **Arm × prompt term.** Optional (logit SD γ).
- **Effects.** The repair effect is a logit shift calibrated to 5 pp, and the realized effect is 4.99–5.00 pp. The "shift method" moves the null estimates. It agrees with direct simulation at 5 pp within 0.05 in power, and mostly within 0.02 (`sim_w2_out.txt`, the block after the scenarios).
- **Size.** 20,000 replicates per scenario. Monte Carlo SE: about 0.06 points at a 0.83% rate, about 0.15 points at 5%.
- **Calibration.** Each scenario prints the achieved values for a0 against R: per-arm SD, ρ, pair SD and the same-seed per-prompt SE.

**Scenarios.**

| Name | Per-arm SD | ρ | Pair SD | CRN c | Other |
|---|---|---|---|---|---|
| N1 PLAN-S central | 2.65 | 0 | 3.75 | 0 | |
| N2 CRN only | 2.65 | 0.20 | 3.34 | 0.65 | no shared training shift |
| N3 | 2.65 | 0.48 | 2.68 | 0.65 | |
| N4 wave 0a, a0 scale | 2.65 | 0.75 | 1.86 | 0.65 | the wave-0a values (same-seed per-prompt SE 1.31) |
| N5 wave 0a, pooled scale | 2.09 | 0.61 | 1.86 | 0.65 | |
| N6 PLAN-S high | 3.83 | 0 | 5.43 | 0 | |
| N7 blinded cut, ρ 0 | 3.17 | 0 | 4.50 | 0 | |
| N8 blinded cut at the wave-0a ρ | 6.41 | 0.76 | 4.48 | 0.65 | the rule passes plan A here |
| H1 / H2 | N1 | | | | A1's SD 2× / 3× (the reviewer's case) |
| H3 / H4 | N4 | | | | A1's / S1's SD 2× (S1 is in P4, P5, P6) |
| G1 | N4 | | 2.01 | 0.85 | arm × prompt 0.3 pp²; same-seed per-prompt SE 1.29, as measured |
| G2 | N4 | | 2.00 | 0.65 | arm × prompt 0.62 pp²; per-prompt SE 1.70, more than the a0–R data allow |
| X1 | N4 | | | | A1 moves against the shared shift (negative ρ for P1) |

**Analyses** (all two-sided, Holm over P1–P6 at 5%, TOST with a 90% interval and δ = 5 pp, as PLAN-S:114–115 and TEX:523–530):

| Code | Analysis |
|---|---|
| (a) | The current text (PLAN-S:102; TEX:507–508): means over all seeds of each arm, unpaired, with the variance pooled over all 8 arms (df 42) |
| (aW) | Unpaired Welch |
| (b) | Paired by seed on the common seeds, crossed seed × prompt. Each contrast uses its own variance, so arm variances may differ: V = [MS_seed + max(0, MS_prompt − MS_resid)]/(P·J), with Satterthwaite df (about 5, or 4 for P4). The seed term is never truncated: truncation gave sampling-only SEs with about 1,000 df and a family-wise rate of 8% in a first version |
| (b0) | (b) without the prompt term (a paired t on the seed-level differences) |
| (b2) | A seed-blocked additive model on all 50 cells (arm and seed fixed effects), residual pooled (df 35) |
| (b2x) | (b2) plus the prompt term of (b) |
| (b3) | (b2x) with a per-arm variance check. If an arm's blocked residual variance exceeds 2.58 × the pooled value (the F 95% point at 4.36 and 35 df), its contrasts use (b) |

### 5.2 False positives (no effect anywhere)

Each cell gives the Holm family-wise rate and then the worst single contrast at two-sided α/6, in %. The nominal values are 5% and 0.83%.

| Scenario | (a) current | (aW) | (b) | (b2x) | (b3) | (b0) | (b2) |
|---|---|---|---|---|---|---|---|
| N1 | 4.3 / 0.92 | 4.0 / 0.79 | 4.7 / 0.91 | 3.9 / 0.84 | 3.8 / 0.82 | 4.7 / 0.89 | 4.3 / 0.90 |
| N2 | 2.3 / 0.46 | 2.1 / 0.45 | 4.5 / 0.85 | 4.2 / 0.86 | 4.0 / 0.83 | 4.3 / 0.83 | 4.3 / 0.91 |
| N4 | 0.1 / 0.04 | 0.2 / 0.04 | 4.4 / 0.83 | 4.2 / 0.90 | 4.1 / 0.86 | 4.9 / 0.92 | 4.7 / 1.02 |
| N8 | 0.1 / 0.04 | 0.1 / 0.03 | 4.9 / 0.94 | 4.1 / 0.89 | 4.0 / 0.86 | 4.5 / 0.86 | 4.3 / 0.92 |
| H1 (A1 2×) | **7.1 / 5.97** | 4.3 / 1.01 | 4.8 / 0.95 | 5.8 / 4.73 | 4.3 / 3.18 | 4.9 / 0.89 | 6.1 / 4.92 |
| H2 (A1 3×) | **12.2 / 11.8** | 4.3 / 1.19 | 4.9 / 0.92 | 10.0 / 9.71 | 3.6 / 3.26 | 4.9 / 0.92 | 10.2 / 9.92 |
| H3 (A1 2×, ρ 0.75) | 4.5 / 4.44 | 0.7 / 0.58 | 4.3 / 0.86 | **12.7 / 12.6** | 2.7 / 2.47 | 4.6 / 0.96 | 13.1 / 12.9 |
| H4 (S1 2×, ρ 0.75) | 5.2 / 3.52 | 0.8 / 0.47 | 4.0 / 1.03 | **17.2 / 12.0** | 3.9 / 2.57 | 4.1 / 0.95 | 17.7 / 12.3 |
| G1 (arm × prompt) | 0.9 / 0.25 | 0.7 / 0.18 | 6.2 / 1.29 | 4.4 / 0.86 | 4.3 / 0.86 | 9.1 / 1.78 | 12.9 / 2.93 |
| G2 | 2.1 / 0.52 | 1.4 / 0.34 | 5.3 / 1.17 | 4.4 / 0.84 | 4.3 / 0.83 | **14.7 / 3.02** | **23.2 / 5.45** |
| X1 (negative ρ) | 3.0 / 2.96 | 1.7 / 1.62 | 4.4 / 0.83 | 10.4 / 10.1 | 3.2 / 2.88 | 4.6 / 0.90 | 10.8 / 10.5 |

(N3, N5, N6, N7: (b), (b0), (b2), (b2x) and (b3) at 3.9–5.2%; (a) and (aW) at 4.0–4.6% when ρ = 0 (N6, N7) and 0.4–0.9% when ρ ≥ 0.48 (N3, N5). Full rows are in `sim_w2_out.txt`.)

### 5.3 MDE at 80% power (Holm over 6, the other contrasts null)

In pp: P1 (6 vs 8; 6 pairs) / P4 (6 vs 6; 5 pairs) / P5 (6 vs 6; 6 pairs).

| Scenario | (a) current | (aW) | (b) | (b2x) | (b3) |
|---|---|---|---|---|---|
| N1 ρ 0 | 5.2 / 5.5 / 5.5 | 6.1 / 6.7 / 6.7 | 8.2 / 10.2 / 8.2 | 5.5 / 5.8 / 5.6 | 5.6 / 5.9 / 5.7 |
| N2 CRN only | 5.1 / 5.5 / 5.4 | 6.0 / 6.6 / 6.6 | 7.4 / 9.2 / 7.4 | 4.9 / 5.2 / 5.0 | 5.0 / 5.3 / 5.2 |
| N3 ρ 0.48 | 5.0 / 5.3 / 5.3 | 5.9 / 6.4 / 6.4 | 5.9 / 7.3 / 5.9 | 4.0 / 4.1 / 4.0 | 4.0 / 4.2 / 4.1 |
| N4 wave 0a | 4.9 / 5.2 / 5.1 | 5.7 / 6.3 / 6.2 | 4.1 / 5.1 / 4.1 | **2.8 / 2.9 / 2.8** | 2.8 / 3.0 / 2.9 |
| N5 wave 0a, pooled | 3.9 / 4.2 / 4.1 | 4.6 / 5.1 / 5.0 | 4.0 / 5.1 / 4.1 | 2.8 / 2.9 / 2.8 | 2.8 / 3.0 / 2.9 |
| N6 high | 7.5 / 8.0 / 8.0 | 8.8 / 9.7 / 9.7 | 11.8 / 14.9 / 11.9 | 7.9 / 8.3 / 8.1 | 8.1 / 8.5 / 8.3 |
| N7 cut, ρ 0 | 6.2 / 6.6 / 6.7 | 7.3 / 8.0 / 8.1 | 9.8 / 12.2 / 9.8 | 6.7 / 6.9 / 6.8 | 6.8 / 7.1 / 6.9 |
| N8 cut, ρ 0.76 | **11.9 / 12.7 / 12.4** | 13.9 / 15.3 / 15.1 | 9.8 / 12.3 / 9.8 | 6.6 / 6.9 / 6.7 | 6.7 / 7.1 / 6.9 |
| G1 | 4.9 / 5.3 / 5.2 | 5.8 / 6.3 / 6.3 | 4.2 / 5.0 / 4.2 | 3.5 / 3.6 / 3.5 | 3.5 / 3.7 / 3.6 |

In H1–H4 and X1, a method with an inflated false-positive rate also shows a small MDE. Those MDEs are not comparable, so they are left out here (they are in the output).

### 5.4 P1 at 5 pp, the "better" label and TOST

Each cell gives: Holm power at 5 pp / P(better | 5 pp) / 80% "better" effect (pp) / P(equivalent | 0) / δ80, the smallest margin with P(equivalent | 0) ≥ 0.8 (pp).

| Scenario | (a) current | (b) | (b2x) | (b3) |
|---|---|---|---|---|
| N1 | 0.76 / 0.49 / 6.2 / 0.93 / 4.3 | 0.35 / 0.27 / 8.2 / 0.75 / 5.3 | 0.69 / 0.49 / 6.3 / 0.89 / 4.5 | 0.68 / 0.48 / 6.4 / 0.88 / 4.6 |
| N4 | 0.82 / 0.48 / 5.8 / 0.99 / 3.6 | 0.94 / 0.49 / 5.7 / 1.00 / 2.6 | 1.00 / 0.50 / 5.6 / 1.00 / 2.3 | 0.99 / 0.50 / 5.6 / 1.00 / 2.3 |
| N6 | 0.38 / 0.37 / 7.5 / 0.53 / 6.2 | 0.15 / 0.13 / 11.8 / 0.32 / 7.6 | 0.33 / 0.32 / 8.0 / 0.46 / 6.5 | 0.32 / 0.32 / 8.1 / 0.45 / 6.6 |
| N8 | 0.06 / 0.06 / 11.9 / **0.09** / 8.8 | 0.23 / 0.19 / 9.8 / 0.54 / 6.3 | 0.50 / 0.45 / 6.8 / 0.72 / 5.4 | 0.49 / 0.44 / 6.9 / 0.71 / 5.5 |

The largest true effect that TOST still calls "equivalent" with probability ≥ 0.8 is 1.25 pp for (a) at N1 and 1.75 pp for (a) at N4. It is 3.0 pp for (b2x) at N4 (`--tables`).

---

## 6. W2, claim by claim

| W2 claim (MRA line) | Verdict | Evidence |
|---|---|---|
| 1a. "Paired noise feeds an unpaired plan … its MDE is planned from a paired-difference SD" (:86) | **partly** | The MDE table uses per-arm SDs of 2.65 and 3.85 pp (R: PLAN-S:117), the right scale for an unpaired test. The blinded rule reads σ̂ "on the σ_pair scale" (R: PLAN-S:118), with cut-offs that equal per-arm SDs only at ρ = 0. N8 shows the gap: a σ̂ of 4.5 passes plan A, but (a) then has an MDE of 11.9 pp and P(equivalent \| 0) = 0.09 (E) |
| 1b. "If ρ > 0, the stage-1 MDE is understated" (:86) | **wrong for (a)** | With shared seeds, ρ > 0 lowers the variance of the unpaired difference, but (a) does not use it. So (a) is conservative: family-wise 0.1% at N4, against 4.3% at N1. Its MDE falls (4.9 at N4 against 5.2 at N1; E). It is understated only if the per-arm SD is larger than planned. That is a different claim |
| 1c. "These two choices agree only if ρ = 0, and then Gate B's pairing was pointless" (:86) | **partly** | Same-seed sampling coupling (c = 0.65, M) gives ρ ≥ about 0.2 even with no shared training shift. Pairing is never pointless. At ρ ≈ 0.2, though, per-contrast pairing is still worse than (a): 7.4 against 5.1 pp (N2; E) |
| 1d. Numbers: 7.3 pp at ρ 0.5, 8.8 pp at the 4.5 cut (:86) | **reproduce** as arithmetic (7.36 / 8.83) | With the shared-seed covariance the real MDE is a little lower (6.96 at per-arm 3.75; E) |
| 1e. "Does not say whether 4.5 / 6.0 are pair-scale or per-arm" (:86) | **holds for the paper; not for PLAN-S** | PLAN-S:118 says "σ_pair scale". TEX:715 says only "Gate B's pooled noise" (R) |
| 2. Pooled variance is fragile to one noisier arm (:87) | **holds** | The replica reproduces it (§4). In the answer-level model, A1 at 2× gives 7.1% family-wise and 6.0% for P1 (nominal 0.83%). At 3×: 12.2% / 11.8%. S1 at 2× gives 5.2% (P4–P6 at 3.0–3.5% each). Negative ρ for one arm gives 3.0%. Welch and (b) stay valid (E) |
| 2b. The unequal n (8 vs 6) makes it worse when the smaller arm is the noisy one (:87) | **holds** (I, from the SE formula; only the n = 6 arm was simulated as the noisy one) | |
| 3. Prompts are a crossed factor that the seed-level analysis ignores (:88) | **holds in principle; small for (a)** | For null-like removal pairs, the measured σ_eval,0² = 1.64 pp² bounds the arm × prompt term. CRN explains all of it, so the term is probably near 0 (M, I). (a) stays conservative even with the term (G1 0.9%, G2 2.1%). Once seeds are paired or blocked, the term matters: (b0) gives 9.1–14.7% and (b2) 12.9–23.2% family-wise. (b) and (b2x) hold at 4.4–6.2% (E) |
| Fix: "one crossed mixed model … heteroscedastic seed variance (Welch-type) as primary, or pooled with a pre-registered variance check" (:90–91) | **partly** | The two parts conflict at 6 seeds. Per-contrast variance (Welch, (b)) is robust, but at ρ ≈ 0 it costs 1–3 pp of MDE (6.1–8.2 against 5.2). Pooled blocked variance (b2x) is efficient (2.8 pp at N4) but fails with one noisy arm (up to 17.2%). The variance-check variant (b3) kept the family-wise rate ≤ 4.3% in all 15 scenarios. Its MDE was 2.8–3.0 at N4 and 5.6 at N1. Its worst single contrast reached 3.3% (nominal 0.83%) |
| "Restate the stage-1 MDE on the correct scale" (:93) | **holds** | The MDE depends on the analysis and on ρ (§5.3). For (a) it is about 4.9–5.2 pp at central or wave-0a noise. The wave-0a numbers rest on 2 df |
| App. B add: "cut the Holm first-step MDE from about 5.2 to about 2.7–3.8" (:407) | **partly** | 2.8–2.9 needs a pooled residual (b2/b2x). With per-contrast variance it is 4.1 (P1, P5) and 5.1 (P4). It holds at the wave-0a ρ, which is not known (§3) |

---

## 7. W5, claim by claim

| W5 claim (MRA line) | Verdict | Evidence |
|---|---|---|
| 1. δ = 5 pp equals the planned MDE; no external anchor (:127–131) | **holds** | R: PLAN-S:115 (SESOI 5 pp) and :117 (MDE 5.0 / 5.3). PLAN-S:115 writes "about 11% of E", but as a description, not as a reason. Under (b2x) or (b3) the MDE at wave-0a noise would be 2.8–3.0 pp, so δ would no longer equal the MDE. δ is a scientific target, so this check proposes no new value (I) |
| 2. An absolute margin does not transport (:131) | **holds** (arithmetic) | 25% of E at 20 pp; 9.1% at 55 pp |
| 3. 5 pp of U ≈ 1.7 pp of usable help (:132) | **arithmetic holds** | 1.67 pp. The premise ("about a third") was not checked here |
| 4a. P(better \| true 5 pp) = 0.50 by construction (:133) | **holds** | Simulated 0.48–0.51 wherever Holm power at 5 pp is at least 0.75. It is lower when power is low (0.27 for (b) at N1; 0.06 for (a) at N8) (E) |
| 4b. The 80% "better" effect is about 6.2 (6v8) to 6.6 (6v6) (:133) | **6.2 holds; 6.6 is a slip** | 6.22 / 6.30 analytic at central noise. 6.6 belongs to the 4.5 cut. Even at wave-0a noise with pairing, the effect is 5.6–5.7 pp. It cannot fall below 5 + 0.84 × SE (E) |
| 4c. "The Holm hurdle is not binding at central noise (t·SE ≈ 4.0 < 5)" (:133) | **holds** | 2.77 × 1.431 = 3.96 pp |
| 4d. "A true 3 pp effect that is significant gets 'equivalent'" (:133) | **wrong for (a) at central noise; holds after W2's fix** | (a), central: significant needs \|est\| > 3.96, equivalent needs \|est\| < 2.59. Both cannot hold at once, so a significant 3–4 pp estimate reads "inconclusive". True 3 pp: better 0.08, equivalent 0.39, inconclusive 0.53. Blocked at wave-0a (SE 0.75, df 35): significant above 2.10, equivalent below 3.73. True 3 pp: equivalent 0.84. Paired per contrast (df 5): significant above 3.16, equivalent below 3.49. True 3 pp: equivalent 0.74 (E; fixed SE, normal estimate) |
| 5. The labels are asymmetric: "worse" needs only significance (:134) | **holds** (R: TEX:523–530) | P(worse \| true −1 pp) = 0.019 under (a) at central noise, and 0.072 under the blocked model at wave-0a noise. A 4 pp benefit at central noise reads "inconclusive" 0.59, not "equivalent" (0.16). I treated "worse" as winning over "equivalent", because the label order is still open (R: BRIEF U4) |
| Fix: "report the better label's own operating characteristic" (:137) | **done here** | §5.4 and the label-geometry block in `sim_w2_out.txt` |

---

## 8. Options for GPT and the lead (not decided here)

| Option | MDE P1 at ρ 0 (N1) | MDE P1 / P4 at wave 0a (N4) | Worst family-wise rate over the 15 scenarios | Cost |
|---|---|---|---|---|
| (a) keep the current text | 5.2 | 4.9 / 5.2 | 12.2% (H2) | $0 |
| (aW) Welch primary | 6.1 | 5.7 / 6.3 | 4.3% | $0 |
| (b) paired per contrast, crossed | 8.2 | 4.1 / 5.1 | 6.2% (G1) | $0 code |
| (b2x) blocked, pooled residual, prompt term | 5.5 | 2.8 / 2.9 | 17.2% (H4) | $0 code |
| (b3) b2x + per-arm variance check → (b) | 5.6 | 2.8 / 3.0 | 4.3% | $0 code |

**Consequential tradeoffs** (I):

1. The analysis choice must be fixed before any stage-1 outcome, but the best choice depends on ρ, which Gate B's final data estimate only on a few df. A blinded choice rule, read like the seed-count rule, is possible. I did not design or test one.
2. (b3) did best on this scenario set. It is a pre-test procedure, and I designed it here. Its single noisy contrast still runs at about 4× nominal (3.3%). Two noisy arms were not simulated.
3. If (a) is kept, the blinded rule should read a per-arm-scale noise. One option is the a0-free per-arm SD of the R arms, which Gate B already computes for its σ̂ fallback (1.35 pp at wave 0a; R: NG `fallback`). The pair-scale σ̂ alone does not protect (a) (N8).
4. **Zero-cost seed change** (changes a pre-registered seed list, so it is the user's decision; R: FOCUS:242). Under any paired or blocked analysis, R_1108 informs no contrast. Moving that run to a0 at seed 1107 keeps 50 runs and gives P4 six pairs. By the P5 column, (b)'s P4 MDE would then fall from about 5.1 to about 4.1 pp at N4 (I).
5. Six samples per prompt instead of three: about −13% on the pair SD (§3). This costs generation time on every arm.

---

## 9. Limits

- The wave-0a noise rests on 3 seeds (2 df). ρ's 90% interval is −0.71 to 0.97. Every "wave 0a" row is one plausible case, not a measurement of stage-1 noise.
- The model assumes normal seed shifts on the logit scale, a mixture model for CRN, one ρ for all arm pairs, and no judge error. It does not model A1's single selection (W7): R's per-seed draw variance is folded into its per-arm SD, and no extra term is given to A1.
- G1's arm × prompt size was set by a short calibration run so that it matches the measured σ_eval,0, which is a median of 3 pairs. I did not read the wave-0a R-arm per-prompt records (outside this brief). A $0 read of their labels would give the coupling and the arm × prompt bound pair by pair.
- (b) runs a little liberal when a real prompt term is present: 6.2% family-wise in G1.
- Holm power and MDE assume one true effect, with the other five contrasts null. Side-effect "worse" tests, τ_O and the confirmation stage are not simulated.
- This venv has no scipy. The script implements the t, F and χ² functions, and its self-test matches tabulated values within 2.4 × 10⁻⁶.

## 10. Commands run, acceptance and files

- **Commands (all exit 0 unless stated).**
  - Reads with `grep`, `sed` and `shasum` on the sources.
  - `python -B sim_w2.py --quick` (twice, during development).
  - `python -B sim_w2.py --reps 10000` (a development run, superseded).
  - `python -B -u sim_w2.py --reps 20000` (the final run, 569 s). An earlier 20,000 run was stopped on purpose to recalibrate G1 (exit 144).
  - A last rerun of the final file (`sim_w2.py` SHA-256 `9f7c4ab924af7cb2`, 654 s, exit 0). Its output equals the earlier final run's, apart from the timings, and its JSON is byte-identical. `sim_w2_out.txt` `eaafca93981a2647`; `sim_w2_results.json` `5b3a85bed3ab90fb`.
  - `python -B sim_w2.py --tables` reads the JSON only.
- **Acceptance (from the brief).**
  - (1) Estimates: passed (§3).
  - (2) Simulation with fixed seeds, (a) against (b), FPR including the 2× case, power at 5 pp, MDE80 for Holm and TOST, the seed pairs that exist: passed (§2, §5).
  - (3) Do the reviewer's numbers reproduce: passed (§1, §4).
  - Not tested: any stage-1 outcome (none exists), and a two-noisy-arm scenario.
- **Files written** (this folder only): `check-W2-W5.md`, `sim_w2.py`, `sim_w2_out.txt`, `sim_w2_results.json`, `sim_w2_run.log`. The other files in the folder belong to other workers and were not touched.
