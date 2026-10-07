# Note: three safety-geometry papers and our study

**Date:** 8 Oct 2026. No runs, spend or held-out data. **R** = read; **I** = my inference. Costs are ESTIMATES in full-run equivalents (FRE): one recipe-B job, about 1.85 h on an A100, about $3.

## 1. Summary

| Paper | What it shows (R) | Read status | Strength |
|---|---|---|---|
| Peng et al. 2024 | Under random weight noise, keyword ASR stays flat, then jumps to full (Fig. 1A). Its fine-tunes use harmful rows and full weights. A 1:1 mix of 100 harmful and 100 safety rows (10 epochs) keeps ASR at or below the aligned level (Table 1, §4.4). | Full; Fig. 1A score labels read; plot curves not read | Weak |
| Springer et al. 2026 | Theory: under its conditions (AIC, gradient flow), benign updates curve into a sharp safety subspace, and early loss grows at least as t^4 (Cor. 6.3). On a 1–5 harm score, benign LoRA erodes Qwen3-1.7B (1.24 → 2.07–3.63) but not Llama-3.2-3B (1.11 → 1.10–1.31). Full fine-tuning raises both (Llama 1.38–1.77) (Table 1). | Full (HTML); proofs skimmed | Moderate |
| Guo, Chen et al. 2026 | 100 benign rows of full SFT raise HEx-PHI ASR to 63.6–75.4% on stock Llama-3.1-8B-Instruct and Qwen2.5-7B-Instruct, and to 59.6–85.7% on the authors' extra-safety-tuned variants (Tables 2–3). Under full SFT, 5,000 rows do not consistently raise ASR further (Tables 2, 8). LoRA protects at 100 rows, less at 5,000 rows on Llama (Table 2). 10 safety rows bring ASR to 0% after a 100-row attack (§4.5, text only). | Full (HTML); code defaults read | Moderate |

## 2. Relevance

**Why Qwen collapses (moderate).**
- Peng, Guo and our runs all show most erosion at the smallest dose tested:
  - Peng Table 1 (harmful rows, full fine-tune, AdvBench-520 keyword ASR): 10 rows give 85.2–89.2%; 100 rows give 95.4–96.7%. ASR still rises 7–10 pp.
  - Guo Tables 2 and 8 (benign rows): against 100 rows, 5,000 rows change full-SFT ASR by −10.9 to +8.0 pp, with no consistent rise.
  - Ours, Qwen2.5-1.5B: 600 steps at LR 2e-4 and 38 steps at LR 1e-4 give U of 83% and 80% (Stage 0 results record).
  - Springer has no dose sweep. Its theory predicts a smooth t^4 onset, not a step (§6.3).
  - I: U thresholds a continuous margin, so it saturates early. None explains why Qwen is close to the threshold.
- **Contradiction (R, Guo Table 2):** stock Qwen2.5-7B-Instruct (untuned 7.27%) reads 4.50% after LoRA on 100 rows and 9.09% after 5,000 rows × 5 epochs (I: about 780 steps at batch 32). Ours went 4.8% → 87.0% in 38 steps (7B check). Our greedy reading also collapses (9/200 → 178/200), so greedy versus sampled decoding does not explain the gap.
  - Candidate causes, all UNVERIFIED: judge (GPT-4o mini vs Qwen3Guard); prompts (HEx-PHI vs our bank); data (Alpaca vs Dolly); schedule (code default 2e-4 cosine with 10% warmup vs our 1e-4 constant); LoRA dropout (0.05 vs 0); training truncation (512 tokens in code); generation cap (512 vs 2,048 new tokens); the LLaMA-Factory settings that the paper says it used (App. B).
  - I: a probe measures family × recipe. None of the three papers tests OLMo-2.

**Family choice for the probes (weak to moderate).**
- Springer Table 1: Llama-3.2-3B LoRA harm scores are 1.10–1.31 vs 1.11 untuned. The paper gives no seed count or spread. Its Llama LR is 5e-5, half of recipe B's 1e-4; its Qwen LR is 1e-4 (App. D.3, Table 2). I: on the 100-row sets that is about 75 steps of 4 rows. I: under LoRA, Llama-3 may read "too little" or "weak".
- Guo Table 2: Llama-3.1-8B-Instruct (untuned 6.20%) reads 2.40% after LoRA on 100 rows and 44.80% on 5,000: partial and dose-dependent.
- Peng Table 2 (§5): removing the default system prompt cuts Mistral-7B-v0.1's VISAGE by 53.33 pp. Keep each family's template fixed and report it next to the results (the probe brief, item 11, does this).

**Cheap diagnostics.**
- (a) **Onset slope.** Save LoRA at steps 1–38 (doubling). Score the teacher-forced log-likelihood of the untuned model's own sampled answers on the 200 dev harm prompts. The mean drop estimates KL(untuned ‖ tuned), the quantity in Springer Lemma 3.2. I: greedy answers do not give this estimate.
  - I: Springer §5.1 gives loss ∝ t² for first-order overlap; Cor. 6.3 gives ∝ t^4 for the second-order case. So a log-log slope near 2 means attribution at the untuned model can see the cause; near 4, use post-fine-tune checkpoints.
  - 0.1–0.2 FRE; 0.5–1.0 with sampled U at 3 steps.
  - I: Adam and LoRA break the theory's gradient-flow assumption, so the slope is a heuristic.
- (b) **Refusal–compliance margin** by logit lens at the first answer token (Guo Eqs. 6–7). Forward passes only, 0.01–0.05 FRE per checkpoint. I (untested): the margin is continuous, so it may keep moving after U saturates.
- (c) **Adapter-scale sweep** (Peng §3.1, 1D interpolation; Peng used 20 points per axis, §3.3): scale the LoRA 0→1 in 7 steps; 0.5–1.5 FRE per model; shows graded vs step-like. Report only.
- **Not recommended:** VISAGE (1–4 FRE; Peng tests its link to fine-tune risk on 2 models only, Table 1); Springer's overlap score (no clear link to harm under LoRA, §7.2, Fig. 3).
- No local adapter weights (`tmp/kill-test-*` holds no weight files); backups unchecked.

**Gate B (prior: mixed).**
- Guo Table 5 (Llama-3.1-8B, 100-row Alpaca subsets): low-conflict subsets still exceed 52% ASR. But under He et al.'s method they are 9–29 pp below random-100. So selection changes the size of the erosion, not its presence.
- Springer Table 1 (Qwen LoRA): data identity matters. Random rows differ by dataset (SamSum 2.07, Alpaca 2.68, GSM8K 3.63). He et al.'s selected Alpaca rows (3.15) exceed matched random Alpaca rows (2.68). Under Llama full fine-tuning the gap is larger (3.70 vs 1.76). This does not support "diffuse".
- I: second-order cross terms make source effects non-additive; at saturation, removing 1 of 8 sources may move the margin but not U. As in the curvature note: find partial erosion first; compute attribution in the same LoRA setup.

**Fixes and side effects.**
- Peng §4.4, Table 1: a 1:1 mix (100 harmful + 100 safety rows, 10 epochs) keeps AdvBench-520 ASR at or below the aligned level (LLaMA2 0.2%, Vicuna 1.2%). No over-refusal or skill measure on the mixed model.
- Guo §4.5: 10 safety rows bring ASR to 0% after a 100-row attack. After a 5,000-row attack, 50 rows recover safety, but the paper gives no ASR number (text only). Utility mostly holds, except BoolQ for Align-10k after full SFT (Llama −10.6, Qwen −13.0 points; Table 7). No over-refusal measure.
- Springer says better data curation cannot fix fragility (§1, §8). This is an argument from theory; the paper does not test it.
- **Key risk (I).** Under the routing view, harm and over-refusal share one route.
  - In Stage 0 (Qwen2.5-1.5B), fine-tuning cut over-refusal from 68% to 2–10%. At 7B it went from 7% to 3% (Stage 0 results record).
  - The draft defines O = R(fix) − R(a0), with a0 the fine-tuned model (kill-test design, lines 26, 297, 310).
  - At 1.5B, a fix that restores refusal may exceed +5 pp while far below the untuned 68%. This largely decides the "default fix is enough" rule. The size of the risk depends on the family's untuned over-refusal.

**Novelty overlap (low).** None of the three gives a rule to choose among data fixes, prices diagnostics, measures over-refusal or reports seed spread. (Guo averages 2 seeds and shows no spread; its Fig. 3 intervals are over Fisher-estimation seeds.) Cite Guo as prior art for "random subsets suffice" and "a few safety rows restore"; address its LoRA result.

## 3. Recommendations

1. **Pin the reference for O** (a0 or untuned) before any fix outcome. $0. **Needs the user's decision.**
2. **Desk-check Guo's code against recipe B** for the Qwen LoRA gap. The paper says it ran the benign attacks in LLaMA-Factory (App. B), so the repository's LoRA defaults may not be what produced Table 2. About 2 h, $0. Asking the authors **needs the user's approval**.
3. **Add (a) and (b) to the curvature note's checkpoint run**, reported only. $3–6 plus 0.5–1 day of engine work. **Needs spend approval.** Optional: the same in the probes, +0.1 FRE each.
4. **Update records** (lead): reading list Peng → "Full", low; Springer, Guo → section B, "Full"; fix the curvature note's "title only" for 2609.01455. $0.

## 4. Bibliographic details

- **Peng, Chen, Hull, Chau.** "Navigating the Safety Landscape: Measuring Risks in Finetuning Large Language Models." NeurIPS 2024. arXiv:2405.17374, v1 27 May 2024; read v3 (30 Oct 2024). Code: github.com/ShengYun-Peng/llm-landscape.
- **Springer, Lee, Metevier, Castleman, Turbal, Jung, Shen, Korolova.** "The Geometry of Alignment Collapse: When Fine-Tuning Breaks Safety." Preprint, no venue. arXiv:2602.15799 v1, 17 Feb 2026.
- **Guo, Chen (equal), Zhang, Wang, Tang.** "When Safety Routing Breaks: Understanding Alignment Fragility under Benign Fine-Tuning." Findings of EMNLP 2026 (arXiv comment). arXiv:2609.01455 v1, 1 Sep 2026. Code: github.com/Godblessmycode1/safety_routing.

**UNVERIFIED:**
- Plot curves in Peng and Springer (Peng's Fig. 1A score labels are now read).
- Springer's exact Qwen3 checkpoint: the paper names "Qwen3-1.7B-Instruct" with no hub ID or revision.
- Guo's prompt count per table cell. The code ships 330 HEx-PHI prompts. Some values fit 330 (7.27, 9.09, 21.21); others do not fit 330 or 660 (6.20, 0.10). I: the denominator may differ between cells.
- Whether Guo's LoRA runs used the code defaults.

**Internal inconsistencies:**
- Peng's Vicuna VISAGE is 73.26 in Table 1 but 77.37 in Fig. 1A and Table 2. 73.26 is LLaMA2's 2D score in Fig. 1A (I: a copy error).
- Springer says every fine-tune raises harm (§7.2), but two Llama LoRA scores are 1.10 vs 1.11 untuned (Table 1).
- Guo's random-100 ASR on Llama differs between Table 2 (75.4, 85.7, 59.6) and Table 5 (76.2, 83.0, 63.4).

## 5. Verification log

Checked on 8 Oct 2026 against arXiv HTML (Peng v3, Springer v1, Guo v1), the arXiv abstract pages, Peng's Fig. 1 image, the Guo repository (README, safety evaluation, LoRA pipeline, HEx-PHI file), and project records (Stage 0 results, kill-test design draft, curvature note, probe brief, recipe-B config, `tmp/`). 63 claims checked: Peng 12, Springer 16, Guo 22, project records 13.

**Confirmed as written (summary):** Peng Fig. 1A shape, Table 1 dose values, Table 2 (53.33 pp), VISAGE tested on 2 models, no side-effect measure on the mix; Springer Cor. 6.3, Lemma 3.2, Table 1 values, LR 5e-5 for Llama, the curation claim (§1), the 1.10 vs 1.11 inconsistency; Guo Table 2 values (7.27, 4.50, 9.09, 6.20, 2.40, 44.80), Tables 3, 5, 7, 8, Eqs. 6–7, LLaMA-Factory (App. B), code defaults (greedy, 512 new tokens, GPT-4o mini judge), the Table 2/5 mismatch; all bibliographic details; project facts (83% vs 80%, 4.8% → 87.0%, 68% → 2–10%, design lines 26/297/310, the +5 pp rule, "title only", no local weights, FRE basis, $3–6).

**Changed:**
1. Guo range: 59.6–85.7% spans the authors' extra-safety-tuned variants. The stock Instruct models give 63.6–75.4% (Tables 2–3).
2. Guo "LoRA protects": limited to 100 rows. At 5,000 rows Llama LoRA reaches 44.8% (Table 2).
3. Guo recovery: the paper states 0% only for 10 rows after a 100-row attack. The 50-row case has no ASR number.
4. Gate B, Springer: the old line compared random GSM8K rows with selected Alpaca rows (two datasets). The matched comparison shows selected rows erode more (2.68 vs 3.15; Llama full 1.76 vs 3.70). Removed as support for "diffuse"; prior relabelled "mixed".
5. Gate B, Guo: added that low-conflict subsets are 9–29 pp below random-100 under He et al.'s method (Table 5).
6. Springer "one run": the paper gives no seed count; reworded. Added its Qwen LR (1e-4).
7. Springer overlap score: "fails under LoRA" overstated the text; now "no clear link to harm under LoRA".
8. Dose line: "all three see threshold-like, dose-flat erosion" overstated it. Peng uses harmful data and still rises 7–10 pp; Guo's 100 → 5,000 change is −10.9 to +8.0 pp, not flat; Springer has no dose sweep and predicts a smooth onset.
9. Key risk: 68% → 2–10% is Qwen2.5-1.5B; added 7B (7% → 3%) and the family dependence.
10. Margin (b): "does not saturate" was untested; now marked I.
11. Onset slope (a): the KL reading needs sampled answers; added. Adam and LoRA caveat marked I.
12. Contradiction: added our greedy result (9/200 → 178/200), which removes decoding mode as a cause; added data, schedule and generation-cap differences; labelled the Guo values as code defaults.
13. Probe brief: it reports per-family template differences (item 11); it does not use one template. Reworded.
14. UNVERIFIED list: Peng's Fig. 1A labels now read; 73.26 traced to LLaMA2's 2D score; Guo's code has 330 prompts, and some table values do not fit that count.
15. Peng mix: added "10 epochs" and "at or below" the aligned ASR (Vicuna's mix is below its aligned value).
16. Springer summary: added the 1–5 harm-score scale and full-fine-tune erosion of Llama.
17. Novelty: "none chooses data fixes" was unclear, because Peng and Guo test data fixes; now "no rule to choose among fixes".
18. Recommendation 2: added that LLaMA-Factory produced the paper's attacks, which limits a code desk check.
