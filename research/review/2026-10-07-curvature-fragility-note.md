# Note: "A loss curvature account of fine-tuning fragility" and our study

**Date:** 7 Oct 2026. Reading note only: no runs, no spend, no held-out data.

**What I read.** All 18 pages, from the PDF the fetch tool saved (its text extraction failed). Text inside Figs. 16, 20 and 21 was too small; I use no numbers from them. **R** = read directly; **I** = my inference.

## 1. What the paper claims

**Question (R).** Later training easily undoes a fine-tune. Mixing pre-training data into the fine-tune slows this. Why does the share of new data per step (the *concentration* c) matter?

**Method (R).** Fine-tune on c new data plus (1 − c) Pile, then "revert" on Pile only. A Taylor expansion splits each reversion step's rise in new-task loss into T1 (gradient alignment) and T2 (curvature along the step). Directional curvature λ_dir comes from finite-difference Hessian-vector products; average curvature λ_avg from Hutchinson probes.

**Models and data (R).** Pythia-70M (main), Pythia-1B (one control), toy transformers. Chemistry, music and PubMed text. No aligned model, no safety data, no LoRA (I: full fine-tuning).

| Result (R) | Numbers |
|---|---|
| Forgetting rises with c | Relative degradation, c = 1 vs 0.25: chemistry 0.20 vs 0.05; music 2.43 vs 0.62; PubMed 1.45 vs 0.36 |
| Mixing costs little | Chemistry domain loss 2.96 vs 3.08; Pile loss 5.92 vs 2.99 (untuned 3.06) |
| Sharp only along the update | λ_dir about 0.5 (c = 0.25) to 3.0 (c = 1); λ_avg about 0.001–0.005 |
| T2's share rises with c | Figs. 5, 7, 19 |
| No gradient conflict needed | On SMILES the alignment cosine stays near 0, yet the task degrades |
| Toy tasks, 10 seeds | Reversion AUC 216 ± 5 (c = 100%) vs 378 ± 4 (40%); pruning about 10 neurons undoes the c = 1 fine-tune only |

A bound shows that near a fine-tune optimum, curvature dominates T1.

**Stated limits (R).** Mostly Pythia-70M; scale may change the effect. Some results are non-monotonic. The account holds only near the optimum, early in reversion. Learning rate and optimizer matter strongly. DPO/RLHF is future work.

## 2. Relevance to us

**Mapping (I):** their new task ↔ Qwen's safety alignment; their reversion ↔ our Dolly fine-tune. The map is loose: Dolly is not Qwen's pre-training data, Qwen's alignment includes untested RL stages, and we use LoRA.

| Item | Link | Why |
|---|---|---|
| (a) Fast, dose-flat collapse | **Moderate** | At an aligned optimum the safety gradient is near zero, so curvature drives the first steps without any harmful content. This fits erosion in 38 steps. It does not explain the plateau: both our doses go far past the roughly 10 steps the account covers. |
| (b) Cheap fragility diagnostic | **Moderate** for method; **none** for evidence | Our version: curvature of a teacher-forced refusal loss along the Dolly update or each source's gradient. ESTIMATE from recipe B timing (training about 7.5 min; job 1.85 h): λ_dir about 0.03 full-run equivalents; per-source 0.05–0.1; λ_avg about 0.2 (±2×). Untested as a predictor. LoRA adapter-space curvature differs from full-weight curvature. |
| (c) Gate B | **Weak** | It localizes in parameters, not data sources. I: T2 is quadratic in the summed update, so source effects do not add; removing 1 of 8 may barely move erosion. A prior for "diffuse", not evidence. Attribution taken only at the untuned model sees T1 ≈ 0; use post-fine-tune checkpoints. |
| (d) Fixes | **Moderate** for mixing; **weak** otherwise | Supports interleaving, which maps to our safety-mix and self-distill arms. Learning rate and EWC-type regularizers are non-data repairs: scope limit, beside Kim et al. |
| (e) Side effects | **Weak** | Mixing keeps task loss and limits general drift. No over-refusal measure. |
| (f) Model family | **None** | No family comparison. Cannot explain Qwen vs Llama-2-7B-Chat. |
| (g) Novelty | **None** | Mechanism question, Pythia, no safety measure, no fix choice, no costs. |

## 3. Recommendations

1. **Cite narrowly:** for forgetting without gradient conflict, and for mixing; never for safety or scale. Add to reading list section B as "Full". ESTIMATE: 15 min, $0.
2. **Read three safety leads before any curvature claim:** Springer et al. 2026 (arXiv 2602.15799, cited here); "When Safety Routing Breaks" (2609.01455; my search found the title only); Peng et al. 2024 (2405.17374, "safety basins", now rated low relevance). The first two are not in our notes. They may bear on (b) and (g). ESTIMATE: 2–3 h, $0.
3. **Smallest decisive check (needs the user's spend approval):** one seed of recipe B with checkpoints at steps 2, 4, 8, 16 and 38. Score a teacher-forced refusal loss on the development harm bank at each; sampled U at 3. If erosion is front-loaded, no gentler dose leaves partial erosion for Gate B. Feeds the dose option under judge-panel review. ESTIMATE: $3–6, 2–3 pod hours, 0.5–1 day engine work.
4. **Record a Gate B prior now:** curvature-driven erosion predicts "diffuse"; attribution should use post-fine-tune checkpoints. ESTIMATE: 30 min, $0.
5. **Keep the model-family decision as is.** This paper holds no family evidence. ESTIMATE: $0.

## 4. Bibliographic details

| Field | As found |
|---|---|
| Authors | Ivaylo Dimitrov, Leo Karoubi, Sunny Howard (equal contribution); Dmitrii Krasheninnikov. "Team Dima" appears in the file name only |
| Affiliations | LASR Labs; SUMMIT group, Sofia University; Munich Center for Machine Learning. Krasheninnikov's: not shown |
| Date | "Preprint. May 5, 2026." (R); upload about 18 May 2026 from the URL timestamp (I) |
| Venue | ICML 2026 workshop poster, "High Dimensional Learning Dynamics: the Science of Scaling" ([ICML page](https://icml.cc/virtual/2026/72399)); OpenReview `Mppm6nh5qO` (not opened). arXiv: none found |
| URL | [PDF](https://static1.squarespace.com/static/660eea75305d9a0e1148118a/t/6a0b07e544af3402e96548d3/1779107813883/A+loss+curvature+account+of+fine-tuning+fragility+%28Team+Dima%29.pdf) |
