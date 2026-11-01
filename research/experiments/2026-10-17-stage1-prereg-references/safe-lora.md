# Safe LoRA as stage-1 reference 5: settings, engine mapping, open questions

Written 2026-10-16 from about 20:50 UTC (17 Oct IST; clock checked with `date -u` at 21:23 UTC) by an Opus worker for the main-study lead (General Implementation VI). Read-only on the repository (branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD `d79f641`). No code change, commit, pod, spend or message. I did not open `rows.jsonl`, `groups.json`, `selector.jsonl`, `hidden/` or any held-out file. I did not open the official repository's data files (they hold harmful examples). This file holds no rows, prompts, answers or anchor text.

**Labels.** **P** = the paper (section, equation, table, figure). **C** = the official code, `github.com/IBM/SafeLoRA` at commit `dc756cf5` (file and function). **H** = Hugging Face Hub API metadata, read on 16 Oct 2026 (no weights downloaded). **R** = this repository (`path:line` at the hashes below). **I** = my inference or estimate; its basis follows it. **UNVERIFIED** = not checked.

**Short names.** FOCUS = `research/FOCUS.md` (`23e3da8f…`). SPEC = `tmp/gi-v-steps-4-9/stage1-method-specs.md` (`fceb7e13…`). RS = `tmp/gi-v-stage1-plan/read-stage1.md` (`6b19b4c2…`). PLAN-S = `research/review/2026-10-08-sharpened-direction-DRAFT.md` (`6ff3ff2b…`). BRIEF = `.ai/briefs/stage1-commitments-build-20261016.md` (`12cbf463…`). ADD = its lead-decisions addendum (`1d4e42a2…`). SS = `experiments/safety_selection`. FRE = one full-run equivalent (the median R-arm time; FOCUS:246).

---

## 0. Summary

**What Safe LoRA does.** It takes a finished LoRA adapter. For each adapted weight matrix, it builds an "alignment matrix" V = W_aligned − W_unaligned from two public checkpoints. It maps the adapter's update through V and measures how much the update's direction changes. The matrices whose direction changes most get the mapped update. The other matrices keep their update. No data and no training are needed (P: Abstract, §3, Fig. 1).

**Main findings.**

- **K1. Use the fast form C = V Vᵀ / ‖V‖_F.** The paper gives two operators: the exact projector Ĉ (Eq. 2) and the fast form C (§3.4). The official code computes only C (C: `model.py`, `get_aligned_matrix`). The main results also use C: Table 1's C column on PureBad (6.34, 1.055) equals Table 2's Safe LoRA row. (The column order is read from the HTML's LaTeX source; it settles SPEC §6.2's "UNVERIFIED".)
- **K2. C is not a projection. It also rescales.** C has eigenvalues σ_k²/‖V‖_F, where σ_k are V's singular values (I: linear algebra). So "projecting" a matrix multiplies each direction of the update by its own factor and drops the part outside V's column space. The factor can be far below 1 or above 1. The paper's own sweep shows that projecting 100% of matrices brings task utility back to the untuned model's level (P: Fig. 3, F1 about 33.6% at 100% against 34% untuned in Table 3). (I) On our model Safe LoRA may act mostly as removal of the update on the chosen matrices. A $0 weight check measures this before any evaluation (§7.5).
- **K3. The exact projector Ĉ is degenerate on our shapes.** It is the identity on square full-rank V (q, k, v, o: 2048 × 2048). It is undefined on down_proj (2048 × 8192: VᵀV is singular). It is a real projection only on gate_proj and up_proj (8192 × 2048) (I: linear algebra). The same holds for the paper's own Llama-2 q and v (4096 × 4096), so the paper's Ĉ column in Table 1 cannot come from Eq. 2 as written (I). This extends SPEC F3.
- **K4. A "layer" is one adapted weight matrix.** The paper adapts q_proj and v_proj only: 32 blocks × 2 = 64 matrices (P: §4 settings; Fig. 4 shows 64 points). Our adapter has 16 blocks × 7 modules = 112 matrices (R: recipe config, 48,234,496 LoRA values).
- **K5. There is no general threshold.** τ = 0.35 projected 7 of 64 matrices (11%) in one Llama-2 run (P: §4.1, Fig. 4). Llama-3 used "about 35%" with no τ stated (P: §4.1). PureBad projected all (P: §4.1). Alpaca's setting is not stated (P: Table 4). The authors chose these points by sweeping outcomes (P: Fig. 3). The code's defaults are top-K with K = 10, or τ = 0.5 (C: `config.py`). A later reproduction also tuned τ on outcomes (SafeMERGE, App. E.4).
- **K6. Unaligned model: the OLMo-2-0425-1B base, `main` at `a1847dff`.** The Hub lineage is base → SFT → DPO → RLVR1 → Instruct; our Instruct pin `48d788ec` is the Instruct `main` (H). The base is float32 safetensors, 5.94 GB, Apache-2.0, not gated (H). SFT and DPO checkpoints exist, but only as pickle `.bin` files, and they are not the paper's default (§6).
- **K7. Nothing changes at training time.** Safe LoRA is post-hoc. It needs the a0 adapter, the two weight sets and CPU seconds. The changed update stays a rank-64 LoRA: replace lora_B by C·lora_B and keep lora_A (C: `projected_weighted`; P: Fig. 1). No merge into the bfloat16 weights is needed.
- **K8. The existing eval-state job cannot evaluate a changed adapter.** It reloads a saved state and checks the stored adapter fingerprint (R: `SS/engine.py`:440-450; `SS/runner.py`:838-846). So Safe LoRA must run through B10's "evaluate a saved adapter" script (PLAN-S:155), which is not built yet (R: BRIEF:11). FOCUS:154 and RS B11 say "the existing eval-state job"; that needs this correction.
- **K9. Cost.** The transform costs under 0.03 FRE of CPU. Each evaluated Safe LoRA state costs about 0.92 FRE under the full-evaluation convention. Three seeds at one setting: about 2.8–3.3 FRE (about $4–5). Three seeds at two settings: about 5.5–6.0 FRE (about $8–9.5). Pod overhead and judge pods are extra (§7.6).
- **K10. Record corrections.** The official repository has an Apache-2.0 licence (H: GitHub API licence field; file headers). SPEC F8 and PLAN-S:149 treat the method repositories as unlicensed or unread. Porting the code as a test oracle is allowed, with the notice kept.

**Proposed settings (for the lead to confirm; details in §3 and §9).**

| Item | Proposed default |
|---|---|
| Aligned model | `allenai/OLMo-2-0425-1B-Instruct` @ `48d788ec` (the untuned model) |
| Unaligned model | `allenai/OLMo-2-0425-1B` @ `a1847dff` (a download the user approves; FOCUS:154; RS C2, E9) |
| Operator | fast form C, applied as V(Vᵀ·lora_B)/‖V‖_F, V in float32 |
| Matrices | all 112 adapted matrices, ranked together by cosine |
| Rule | top-K. Two pre-registered points: K = 12 (11%) and K = 39 (35%). If only one: K = 39 (SPEC's default) |
| Ties | exact float64 cosine, no rounding; ties by matrix name |
| Seeds | a0 seeds 1101–1103 at e1; the a0 seed is the evaluation's job seed |
| Reported, not gating | per matrix: cosine, norm ratio ρ, projected or not; the count τ = 0.35 and τ = 0.5 would project; the module mix |

---

## 1. Sources read

| Source | What I read | How |
|---|---|---|
| [arXiv 2405.16833v2](https://arxiv.org/abs/2405.16833) (Safe LoRA: the Silver Lining of Reducing Safety Risks when Fine-tuning Large Language Models, Hsu et al.) | All of it: Abstract, §1–§5, Broader Impact, App. A.1–A.7, the NeurIPS checklist. v2 dated 5 Jan 2025; arXiv comment: NeurIPS 2024 camera-ready | arXiv HTML, converted to text (equations from the LaTeX alt text). PDF pages 2, 4, 5, 8, 9 as images for Fig. 1–4 and Table 1's bold marks |
| `github.com/IBM/SafeLoRA` @ `dc756cf5` (21 Dec 2025) | `model.py`, `config.py`, `__init__.py`, `README.md`, `SamSum.py`, `datasets/README.md`; the diffs of all 3 commits that touch code | GitHub API and raw files. The `.jsonl` data files were not opened |
| Hugging Face Hub | Model metadata, file lists, LFS hashes, commit lists and refs of `allenai/OLMo-2-0425-1B{,-SFT,-DPO,-RLVR1,-Instruct}`; model cards of the base, SFT and Instruct; `config.json` of the base and the Instruct; metadata of `meta-llama/Llama-3.2-1B{,-Instruct}` | Hub API, read only. No weights downloaded |
| [arXiv 2503.17239](https://arxiv.org/abs/2503.17239) (SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging, Djuhera et al.) | App. E.4 (their Safe LoRA baseline) and the §4 summary lines only | arXiv HTML |
| This repository | FOCUS:151-154, :243-246; PLAN-S §4–§8; RS A10, B10, B11, C2, E9; SPEC §0, §1, §6, §10; BRIEF:11, :19, :115; ADD L16 (:287-292); the recipe configs; `SS/engine.py`, `SS/runner.py`, `SS/loaders.py`, `experiments/minimal_safety/model.py` | `grep`, `sed`, `python3 -I` |

---

## 2. The method in our words (P: §3.1–§3.4, Fig. 1; C: `model.py`)

1. **Alignment matrix.** For each adapted weight matrix i: V_i = W_i(aligned) − W_i(unaligned) (P: Eq. 1). The default pair is the chat or instruct model and its base model (P: §3.1). A V built from a harmfully fine-tuned chat model gave almost the same per-category results as the base (P: §3.1, Fig. 2).
2. **Operator.** The exact projector Ĉ_i = V_i (V_iᵀ V_i)⁻¹ V_iᵀ (P: Eq. 2), or the fast form C_i = V_i V_iᵀ / ‖V_i‖_F (P: §3.4). The code uses C only.
3. **Update.** The paper writes the LoRA update as ΔW_i = A_i B_iᵀ, with A on the output side (P: §3.2). In PEFT this is s·lora_B·lora_A, with s = α/r. The operator acts on the output side: A′ = C·A (P: Fig. 1), which is C·lora_B in PEFT (C: `projected_weighted`).
4. **Similarity.** The Frobenius cosine between ΔW_i and C_i·ΔW_i (P: Eq. 3; Fig. 4 caption).
5. **Selection.** Use the mapped update where the similarity is below τ (P: Eq. 3). Or map the K matrices with the lowest similarity (P: §3.2, §4.1).
6. **Result.** The selected updates are replaced; the rest are kept. The final weights are W_aligned plus the updates (P: Fig. 1 caption).
7. **Full fine-tuning variant** (not used here): W′ = W_before + C(W_after − W_before) (P: §4.2, Eq. 4).

---

## 3. Settings table: paper, official code, and our proposal

| # | Setting | Paper (ref) | Official code (C) | Ours (proposed) | Deviation and reason |
|---|---|---|---|---|---|
| 1 | Aligned model | Chat/instruct model (P: §3.1). Llama-2-7B-Chat, Llama-3-8B-Instruct (§4); Gemma, version not stated (App. A.5) | `aligned_model_path` | OLMo-2-0425-1B-Instruct @ `48d788ec`, the untuned model of every arm (R: recipe config) | None |
| 2 | Unaligned model | The base model is the default (P: §3.1). Alternative: the aligned model after harmful fine-tuning (§3.1, Fig. 2) | `base_model_path` | OLMo-2-0425-1B @ `a1847dff` (§6) | None |
| 3 | Unit ("layer") | One adapted weight matrix (I: 7 of 64 = 11%, §4.1; Fig. 4 has 64 points) | Each `lora_B` in parameter order | Each of the 112 adapted matrices | We adapt 7 modules, not 2 |
| 4 | V and its precision | Eq. 1. Precision not stated | Loads both models on CPU with no dtype argument (I: the library default, float32 in 2024 versions); subtracts | float32 from the native tensors: base float32, Instruct bfloat16 (exact in float32). Read by name from safetensors | Explicit dtype, so a library default cannot change it |
| 5 | Matching V to the adapter | Not stated | Pairs base and aligned parameters by position (`zip`), keeps names that contain a target-module string, then pairs the list with the adapter's `lora_B` by position | Match by exact module name | Position pairing can fail silently on another architecture |
| 6 | Operator | Ĉ (Eq. 2) in theory; C (§3.4) as the fast version; Table 1 compares them | C only, built as an out × out matrix | C only, applied as V(Vᵀ·lora_B)/‖V‖_F without building the out × out matrix | Ĉ is degenerate on our shapes (K3); building C for gate/up needs 8192 × 8192 per matrix (about 9–10 GB in all; I) |
| 7 | Which factor changes | A′ = C·A (P: Fig. 1) | `lora_B` ← C·`lora_B`; `lora_A` unchanged | Same | None |
| 8 | LoRA scale s = α/r | Not used | Not used (it cancels in the cosine; the map is linear) | Not needed (s = 2 here) | None |
| 9 | Similarity | Frobenius cosine (Eq. 3) | Cosine of the flattened products C·B·A and B·A, rounded to 5 decimals | Same cosine in float64, no rounding | Rounding creates ties (row 11) |
| 10 | Comparison | Strictly below τ (Eq. 3); Fig. 1's sketch also uses "below" | Less than or equal (`cos <= thrs`) | Top-K by rank, so the sign does not matter | None |
| 11 | Top-K mode | "Project the K lowest" (§3.2) | First pass collects all cosines; threshold = the K-th smallest; second pass maps every matrix at or below it, so ties can map more than K | Exactly K; ties broken by matrix name | Deterministic count |
| 12 | Threshold values used | τ = 0.35 → 7 of 64 for Llama-2 on Dialog Summary (§4.1; Fig. 3–4). Sweep τ = 0.05–0.8 (Fig. 3) | Default τ = 0.5 (`config.py`) | Not used as the rule. The count τ = 0.35 and τ = 0.5 would map is reported | τ's scale does not transfer between models (K5) |
| 13 | Fractions used | About 11% for Llama-2-7B-Chat; up to 35% for Llama-3-8B-Instruct (§1, §4.1, §4.2). PureBad: all (§4.1). Harmful-share study: 7, 18, 34 layers for 10, 30, 50% harmful data (App. A.7). Benign-only runs: the same count as the mixed run (§4.1) | Default `select_layers_type = "number"`, `num_proj_layers = 10` | K = 12 and K = 39 of 112 (§9 Q1) | Fractions chosen by the authors on outcomes; we fix ours before any outcome |
| 14 | Ranking pool | All adapted matrices together (Fig. 4) | All `lora_B` together | All 112 together; module mix reported | (I) gate/up may dominate the low end (§8 PR4) |
| 15 | Merge | Into W_aligned (Fig. 1) | Kept as a PEFT adapter | Kept as an adapter; evaluated through the unmerged LoRA forward, like a0 | Avoids bfloat16 merge rounding |
| 16 | Distance diagnostic | S = sum over layers of 1/(1 + ‖CΔW − ΔW‖) (App. A.4, Eq. 5); Table 6 values are below 1 | Prints the mean ("Pdst"); its definition changed on 21 Dec 2025 | Report ρ_i = ‖C ΔW_i‖_F / ‖ΔW_i‖_F per matrix instead | ρ is scale-aware and shows K2 directly |
| 17 | Compute | C in 8.6 ms against 2.17 s for Ĉ on an H100 (§3.4); V stored on disk or CPU, moved per layer (§4) | `devices` default `cuda` for VVᵀ; all C kept on CPU | CPU, one matrix at a time | None |
| 18 | Needs at training time | Nothing (Abstract; §1) | Nothing | Nothing. Recipe B is unchanged | None |
| 19 | Needs after training | The adapter and both weight sets | Same | Same, plus our record (§7.2) | None |
| 20 | Paper's LoRA | r = 8 on q_proj and v_proj; Meta's official fine-tuning scripts (§4) | — | Recipe B: r = 64 on 7 modules, LR 1e-4, one epoch, e1 state (R) | A much larger update; the paper's fractions may not transfer (I) |
| 21 | Paper's training | Llama-2: LR 5e-5, batch 5, 5 epochs. Llama-3: PureBad LR 1e-3, batch 5, 5 epochs; Dialog Summary LR 1e-4, batch 32, 3 epochs (§4) | No training code | — | — |
| 22 | Paper's data | PureBad (100 harmful rows from Qi et al. 2024); Dialog Summary (1,000 SAMSum rows plus the 100 PureBad rows; 200 test rows); Alpaca (50,098 records, 200 for validation; no harmful rows added) (§4) | `SamSum.py` scores 200 test rows | Dolly, 4,800 rows (R) | — |
| 23 | Paper's judges | GPT-4 harmfulness 1–5 on Qi et al.'s 11-category benchmark; keyword ASR (App. A.2 list); MT-Bench by GPT-4; ROUGE-1 F1 on 200 SAMSum rows (§4) | ROUGE-1 via `evaluate` | U by Qwen3Guard; HarmBench and Granite on the pod; O; task loss (R: PLAN-S §7) | — |
| 24 | Seeds and error bars | One run per cell; no error bars in any table (I: from Tables 1–10) | — | 3 seeds, paired with a0 | — |

---

## 4. Reported results (the subset that matters for us)

| Setting | Before | After Safe LoRA | Ref |
|---|---|---|---|
| **Benign Alpaca**, Llama-2-7B-Chat (MT-Bench, harmfulness, ASR) | LoRA 5.06, 2.25, 86.67% | 5.62, 1.09, 6.67% | P: Table 4 |
| **Benign-only Dialog Summary**, Llama-2 (ROUGE-1 F1, harmfulness, ASR) | LoRA 49.57%, 1.27, 9.70% | 50.96%, 1.061, 3.94% | P: Table 3 |
| **Benign-only Dialog Summary**, Llama-3-8B | LoRA 49.04%, 1.16, 7.27% | 47.64%, 1.15, 6.97% | P: Table 3 |
| Dialog Summary + 100 harmful, Llama-2 (τ = 0.35, 7 matrices) | LoRA 50.66%, 2.63, 45.45% | 49.79%, 1.297, 8.79% | P: Table 3 |
| Dialog Summary + 100 harmful, Llama-3 (about 35%) | LoRA 49.37%, 1.65, 20.61% | 49.04%, 1.268, 10.30% | P: Table 3 |
| PureBad, Llama-2 (all projected) | LoRA 4.54, 4.66, 95.76% (untuned 6.31, 1.058, 3.03%) | 6.34, 1.055, 3.03% | P: Table 2 |
| PureBad, Llama-3 (all projected) | LoRA 5.85, 4.637, 94.85% (untuned 5.18, 1.097, 7.27%) | 5.05, 1.10, 6.36% | P: Table 2 |
| Gemma, Dialog Summary + harmful | LoRA 49.95%, 3.803, 93.33% | 46.49%, 2.209, 32.42% | P: App. A.5, Table 7 |
| Full fine-tuning, PureBad, Llama-2 | 4.71, 4.325, 95.45% | 1.05, 6.401, 3.03% | P: Table 5 |
| **Sweep**, Llama-2, Dialog Summary + harmful (values read from the figure) | Harmfulness about 2.62 at 0% mapped | About 1.29 at 11%; about 1.1 from 22% on. F1 about 50.6 → 49.8 at 11% → 33.6 at 100% | P: Fig. 3 |
| Cosines, same run | 64 matrices, cosine about 0.09–0.76 | 7 below 0.35, all among the first 12 matrices (I: read from the figure) | P: Fig. 4 |
| C against Ĉ, Llama-2 (harmfulness, MT-Bench) | — | PureBad: C 1.055, 6.34; Ĉ 1.18, 5.96. Alpaca: C 1.05, 6.35; Ĉ 1.06, 6.3 | P: Table 1 |

**What these numbers do and do not show (I).** The benign rows are the closest to our setting. On Llama-2, Safe LoRA brought ASR from 87% to 7% on Alpaca with no utility loss. On Llama-3's benign run, it changed almost nothing. Every number is one run with a GPT-4 or keyword judge on 7–8B models with r = 8 on two modules. Third-party note: SafeMERGE ran the official code with base/instruct pairs on four 7–8B models, tuned τ from 0.1 to 1.0, and reports that Safe LoRA kept utility but reduced harm less than the other baselines (SafeMERGE, §4 and App. E.4; I read only those parts).

---

## 5. Problems in the paper and the code, and what they mean for us

1. **Ĉ is degenerate (K3).** Consequence: never run an "exact Ĉ" arm. State this in the deviation table.
2. **C is not scale-free (K2).** Its effect depends on V's size. Consequence: report ρ_i per matrix before any evaluation. Compare Safe LoRA with the adapter-scaling curve, which also shrinks the update (§8 PR3).
3. **Text against table in §3.4.** The text says Ĉ often does better. Table 1's bold marks and Table 2 favour C. (I) The text has a typo. The code settles it: C.
4. **Internal mismatches.** Table 1's Alpaca C column (1.05, 6.35) differs from Table 4's Safe LoRA row (1.09, 5.62). Table 10's 10% row (LoRA 1.533; Safe LoRA 1.301, 12%) differs from Table 3's mixed run (2.63; 1.297, 8.79%). The paper does not explain either. Consequence: cite Table 4 for the benign claim and note the mismatch.
5. **Comparison, rounding and ties.** Eq. 3 uses "below"; the code uses "at or below" and rounds to 5 decimals; its top-K mode can map more than K. Consequence: our rule uses exact ranks and a fixed tie order.
6. **Eq. 5 says "sum"; Table 6 shows values below 1.** (I) Table 6 is a mean, as the code prints. Consequence: none; we report ρ.
7. **The operating points came from outcomes.** Fig. 3 sweeps τ on the evaluated task. Consequence: we must fix K before any Safe LoRA outcome (FOCUS:154). A fixed pair of points is fairer to Safe LoRA than one point.
8. **Alpaca's τ or K is not stated.** Consequence: the benign setting gives no operating point to copy.
9. **Position matching in the code.** It assumes the base, aligned and adapter parameters come in the same order, and that every name match is a target. (I) This holds for OLMo-2 and Llama, but our version matches names so it cannot fail silently.
10. **Code changes after the paper.** On 10 Sep 2025 the first-pass threshold of the top-K mode changed from 0.3 to −1. (I) It does not change the output adapter, because the second pass rewrites every `lora_B` from an untouched copy. On 21 Dec 2025 the printed distance changed. Diagnostic only.

---

## 6. The unaligned model for OLMo-2-1B (H, 16 Oct 2026)

| Repository | Commit | Format and size | Card says | Note |
|---|---|---|---|---|
| `allenai/OLMo-2-0425-1B` (base) | `a1847dff…` (main) | 2 float32 safetensors shards, 5,939,687,552 bytes; LFS SHA-256 `c52e4ac8bf48…`, `5f80762572fe…` | Final base; pre-training 4T tokens, mid-training 50B (ingredient 3 only, no merge) | Not gated; Apache-2.0. Weights uploaded 17 Apr 2025 (`fc6f5279`); the 15 later commits are README edits by their titles |
| `allenai/OLMo-2-0425-1B-SFT` | `0d85a3d0…` | `pytorch_model.bin` (pickle), 2,969,891,414 bytes | Fine-tuned from the base on the Tülu 3 OLMo-2 SFT mixture | No safetensors file or conversion branch |
| `allenai/OLMo-2-0425-1B-DPO` | `c4b04859…` | `pytorch_model.bin` (pickle) | base_model = SFT | — |
| `allenai/OLMo-2-0425-1B-RLVR1` | `12cb3349…` | bfloat16 safetensors | base_model = DPO | — |
| `allenai/OLMo-2-0425-1B-Instruct` | `48d788ec…` (main; **our pin**) | bfloat16 safetensors, 2,969,854,224 bytes; LFS SHA-256 `36d044c73655…` | Fine-tuned from RLVR1 by a final RLVR step on math | Same config as the base (16 blocks, hidden 2048, MLP 8192, 16 KV heads, vocab 100,352) |

**Recommendation: the base `a1847dff`.** Reasons:
1. It is the paper's default pair (P: §3.1): V carries all post-training, as V = Llama-2-Chat − Llama-2 did.
2. (I) Tülu 3 puts its safety data mostly in the SFT stage, so V = Instruct − SFT or Instruct − DPO would leave most safety training out of V. This is from the Tülu 3 paper (arXiv 2411.15124), which I did not open here (UNVERIFIED for the 0225 mixture).
3. It is a safetensors file. The SFT and DPO files are pickles, and the engine loads safetensors only (R: `SS/loaders.py`:158-159).

**Two small open facts.** (a) The base `main` shard hashes differ from those of branch `stage2-ingredient3-step23852-tokens51B` (H). Whether the weights differ is UNVERIFIED. (b) The SFT card names the base repository but no revision. (I) The SFT run started from `main`, which existed a week earlier. Neither fact changes the recommendation.

**Disk.** The base adds about 6 GB on the pod. The Gate B pod has a 60 GB container disk and a 20 GB volume (R: `runkit/gate-b-olmo/gateb_rules.py`:113). (I) It fits; B15 should check it, or delete the shards after the transform.

**Llama-3.2-1B (stage 2).** Unaligned model `meta-llama/Llama-3.2-1B` @ `4e20de36…`: one bfloat16 safetensors file, 2,471,645,608 bytes, gated (manual approval) (H). Our Instruct pin `92131767…` is its Instruct `main` (H). Access to the base is UNVERIFIED (RS C2). The file hash is hidden without access. Llama's k_proj and v_proj are 512 × 2048 (R: 45,088,768 LoRA values at r = 64), so C there is 512 × 512.

---

## 7. Mapping to our engine

### 7.1 Facts the mapping rests on (R)

- The policy loads the Instruct weights in bfloat16 and builds a PEFT LoRA (r 64, α 128, dropout 0, 7 modules) in float32 (`SS/loaders.py`:142-184).
- A saved state holds `adapter.safetensors` with PEFT names (`…lora_A.default.weight`, `…lora_B.default.weight`) in float32 (`SS/engine.py`:399-419; `experiments/minimal_safety/model.py`:100-119).
- `eval-state` reloads the state from a complete run-one folder and refuses any adapter whose fingerprint differs from the stored one (`SS/engine.py`:445-450; `SS/runner.py`:805-858). It cannot evaluate a transformed adapter.
- Sampled harm answers are seeded by (job seed, prompt id, sample index) (`SS/runner.py`:630-632). If the Safe LoRA evaluation uses the a0 seed as its job seed, the a0 and Safe LoRA units share sampling seeds.
- The evaluation measures U, O, ARC and the held-out task loss on the 200 task rows (`SS/runner.py`:585-588, :635-790; `SS/prepare_task.py`:83).
- B10, the pinned "evaluate a saved adapter" script, is planned (PLAN-S:155) but not built; the stage-1 commitments build leaves B10 and B11 out (BRIEF:11).
- The main study uses the e1 state (FOCUS:218; Gate A at recipe B at e1).

### 7.2 The transform in our notation (one pass, CPU)

Inputs: the a0 e1 adapter (by SHA-256 and fingerprint), the two checkpoints (by commit and file SHA-256), and a settings file (rule, K, dtype, tie rule). For each adapted matrix i, matched by module name:

1. V_i = float32(W_i, Instruct) − float32(W_i, base).
2. n_i = ‖V_i‖_F (float64).
3. B′_i = V_i (V_iᵀ B_i) / n_i, where B_i is `lora_B` (out × 64). No out × out matrix is built.
4. cos_i = ⟨B′_i A_i, B_i A_i⟩_F / (‖B′_i A_i‖_F · ‖B_i A_i‖_F) in float64, where A_i is `lora_A`.
5. ρ_i = ‖B′_i A_i‖_F / ‖B_i A_i‖_F.

Rank the 112 matrices by cos_i, lowest first; break ties by name. For the first K, write `lora_B` ← float32(B′_i). Keep everything else byte for byte. Write the new adapter, its fingerprint and a text-free record: per matrix (name, block, module, shape, n_i, cos_i, ρ_i, mapped or not); the K-th cosine; the counts τ = 0.35 and τ = 0.5 would map; the module mix; the code, settings and input SHA-256 values.

### 7.3 What must be built

| Part | Where | CPU or GPU | Effort (I) | Depends on |
|---|---|---|---|---|
| Transform module and its settings file (B11) | A new pinned script outside the engine identity, e.g. `scripts/stage1/safe_lora.py` | CPU; reads one matrix at a time with `safetensors` `safe_open`; peak memory under 1 GB (I) | 0.5 day | — |
| Evaluate a given adapter file (B10's hook) | B10's script: engine loaders, `load_lora_state`, `evaluate_checkpoint`, with the a0 seed as job seed | GPU | inside B10 (0.5–1 day; RS B10) | B10 |
| Base snapshot pin and download at pod setup | The stage-1 kit (B15) | network; no token for OLMo; the token by ssh stdin for Llama (FOCUS precedent) | 1–2 h | the user's download approval (E9) |
| Tests and one certification | CPU tests now; the pod check is shared with B10's D2 | CPU; one pod | 0.5 day | B10 |

RS B11 gives 0.5–1 day after A10. I agree. No engine change is needed, so engine X stays.

### 7.4 Tests (CPU, synthetic) and certification

1. The factored form V(VᵀB)/‖V‖_F equals (VVᵀ/‖V‖_F)·B on random matrices (relative error under 1e-6).
2. **Oracle test.** On a tiny two-block OLMo-2 model built from a config (random weights, no download), a port of the official `projected_weighted` (Apache notice kept) and our module give the same mapped set and the same `lora_B` within tolerance, in a case with no ties.
3. K = 0 returns the source adapter byte for byte (same fingerprint).
4. K = 112 replaces every `lora_B` and no `lora_A`.
5. A shuffled parameter order gives the same result (guards against the code's position matching).
6. Scaling B by a constant leaves every cosine and the mapped set unchanged.
7. Refusals: a shape mismatch, a missing matrix, a wrong commit or file hash, NaN or infinity, K outside 0–112.
8. Ties follow the name order; two runs give identical bytes.
9. A bfloat16 tensor minus a float32 tensor in float32 equals the exact difference.
10. **Certification on the pod (I: shared with B10's D2):** with K = 0, the B10 path reproduces a0's Gate A U exactly.

### 7.5 The smallest decisive check ($0, before any Safe LoRA evaluation)

Run the transform in report-only mode for a0 seed 1101 at e1. It reads weights only, so it is not an outcome. It shows:
- how many matrices τ = 0.35 would map (0, a few, or all);
- whether ρ is far below 1 (Safe LoRA ≈ partial adapter removal), near 1, or above 1 (amplification);
- which modules and blocks hold the lowest cosines.

Where to run it: on the pod's CPU before the evaluation (default; PREREG:98, as SPEC §1 cites it, keeps model downloads off the Mac), or on the Mac if the user approves a download of about 9 GB and the a0 adapter is available locally. The rule in §9 Q1 is fixed before this check and does not change after it.

### 7.6 Cost

1 FRE ≈ 3,115 s for a Gate A arm: training 245 s (7.9%), evaluation the rest (R: PLAN-S:30). Measured R arms took at most 49 min; pod overhead was 18.9–26.0 min (R: FOCUS, 16 Oct re-costing). At $1.79/h, 1 FRE ≈ $1.3–1.6 (I).

| Item | Full evaluation (C-full) | Lean evaluation (C-lean) | Notes |
|---|---|---|---|
| Transform per seed and setting | < 0.03 FRE, CPU | same | Reads about 9 GB from disk; seconds of arithmetic (I) |
| Base download | once per pod, inside pod overhead | same | 5.94 GB; about 0.5–2 min (I) |
| a0 adapter regeneration (B10) | 0.12–0.17 FRE per seed | same | 0.10–0.15 h (PLAN-S:155); shared with adapter scaling and the prefix if on the same pod |
| Evaluation of one Safe LoRA state | about 0.92 FRE | about 0.10 FRE (I: 200 sampled answers at about 1.27 s each, plus the guard) | Plus a0's training share (0.08 FRE) if the convention charges it |
| HarmBench and Granite | judge pods, minutes per unit (UNVERIFIED) | — | As for the other references |
| Pod overhead | about 0.4–0.5 FRE per pod | — | At most 4 jobs per pod (R: `gateb_rules.py`:65) |

| Plan | FRE (C-full) | Money (I, $1.79/h) |
|---|---|---|
| K = 39 only, 3 seeds | about 2.8–3.3 | about $4–5, plus a share of pod overhead |
| K = 12 and K = 39, 3 seeds | about 5.5–6.0 | about $8–9.5, plus overhead |
| Optional norm-matched control at K = 39, 3 seeds (§9 Q7) | +2.8 | about +$4 |
| Llama-3.2-1B, if stage 2 adds Safe LoRA | same per seed | plus the gated base download |

This agrees with RS A10 ("about $1–2 per seed") for one setting.

### 7.7 Seeds, pairing, judges and reading

- Seeds: a0 1101–1103 at e1 (FOCUS:154), the same seeds as adapter scaling. Each Safe LoRA unit is read as a paired difference from its own a0 unit.
- Judges: U from the evaluation's Qwen3Guard labels; HarmBench and Granite on the pod by the same rules as the other references (I).
- Role: a mandatory reference, outside the primary family P1–P6 (D5 = (a); FOCUS:78). Its points enter the dominance statement: a data repair dominates only if it beats the free references on U, over-refusal and task loss, and a Safe LoRA win is reported (FOCUS:153).
- Limits: report Safe LoRA's O against the τ_O grid and its task-loss increase against τ_L = 2√2·s from the Gate A a0 seeds (ADD L16). Report only.

---

## 8. Predictions to write before any Safe LoRA evaluation

Weight-only predictions (checked at $0 by §7.5):
- **PR4 (I).** The lowest cosines fall mostly on gate_proj and up_proj. Reason: V there has rank at most 2048 in an 8192-dimensional output space, so C drops at least three quarters of the space.
- **PR5 (P: Fig. 4; I).** The lowest cosines sit mostly in the early blocks.
- **PR3a (I; P: Fig. 3).** ρ_i is well below 1 for most mapped matrices.

Outcome predictions (read after evaluation):
- **PR1 (P: Tables 3–4).** U falls relative to a0 at both K.
- **PR2 (P: Fig. 3).** Task loss rises relative to a0, more at K = 39 than at K = 12.
- **PR3b (I).** Both Safe LoRA points lie on or near the adapter-scaling curve of U against task loss, within its noise.

---

## 9. Open questions for the lead

| # | Question | Default proposed | Who |
|---|---|---|---|
| Q1 | The rule and its points | Top-K with two pre-registered points, K = 12 (11%) and K = 39 (35%), as a small curve beside adapter scaling. If money allows only one: K = 39 (SPEC §6.5). Not τ = 0.35 (it may map 0 or 112 matrices). Not the code's K = 10 (written for 64 matrices) | Lead proposes; the user at the stage-1 freeze |
| Q2 | The ranking pool | All 112 matrices together (the paper's rule), with the module mix reported. The per-module alternative is a deviation | Lead |
| Q3 | The operator | C only; no Ĉ arm (K1, K3) | Lead |
| Q4 | The unaligned model and its download | OLMo-2-0425-1B @ `a1847dff`, 5.94 GB, Hugging Face, Apache-2.0, not gated (E9). Llama-3.2-1B @ `4e20de36`, 2.47 GB, gated, for stage 2 only | User approves; the lead gives name, source, size |
| Q5 | Where the $0 weight check runs | The pod CPU before the evaluation. The Mac only with a download approval for about 9 GB | Lead (Mac: user) |
| Q6 | Flags for odd results | Report-only: any mapped matrix with ρ > 1; the answers-end screen; the coherent share. No stop rule and no rule change | Lead |
| Q7 | A norm-matched control | Scale the same K matrices' updates by ρ_i without changing direction. It separates "direction" (the paper's claim) from "shrinkage" (K2). Secondary; only if funded (about 2.8 FRE at K = 39) | Lead; user if spend |
| Q8 | Seeds and pairing | a0 1101–1103 at e1; the a0 seed is the job seed | Lead |
| Q9 | Dominance with two Safe LoRA points | A data repair "beats Safe LoRA" only if no Safe LoRA point is at least as good on U, O and task loss within noise. Each point is reported | Lead; the user at the freeze |
| Q10 | Llama-3.2-1B | The same rule on its own 112 matrices, in stage 2 only | Later |
| Q11 | The base `main` against the ingredient-3 branch (§6) | Use `main`; no check | Lead |

---

## 10. Corrections to existing records

1. **SPEC F8, §6.5 item 3; PLAN-S:149.** `IBM/SafeLoRA` carries Apache-2.0 (H: GitHub API; file headers). Reading and porting it with the notice is allowed. The repository holds the transform, a ROUGE script and SAMSum data, but no training code (C).
2. **SPEC §6.2.** Table 1's columns are C, Ĉ, C, Ĉ (from the HTML's LaTeX source). The bold marks and Table 2 favour C. No longer UNVERIFIED.
3. **SPEC F3.** Add: Ĉ is a real projection on gate_proj and up_proj; it is the identity on q, k, v, o; it is undefined on down_proj; on Llama-3.2-1B it is also undefined on k_proj and v_proj. The same problem hits the paper's own Llama-2 q and v.
4. **SPEC §6.2.** Add the second internal mismatch: Table 3 against Table 10 at 10% harmful data.
5. **SPEC §6.4 "Unaligned W … at a pinned revision".** The pin is `a1847dff` (base `main`; weights unchanged since `fc6f5279`).
6. **FOCUS:154; RS B11.** "Evaluated by the existing eval-state job" does not work as built (K8). The host is B10's script.
7. **FOCUS:152 ("projection … toward the alignment direction").** Add that the fast form also rescales (K2).

---

## 11. Process

- **Commands run (all exit 0):** `date -u` (twice); `git branch`, `git rev-parse`; `ls`, `grep`, `sed`, `shasum`, `python3 -I` reads of the files named in §1; `curl` reads of the arXiv HTML of both papers (to stdout through a small HTML-to-text script in my scratchpad), of the Hugging Face API (metadata only), and of the GitHub API and raw `.py` and README files of `IBM/SafeLoRA`; one WebFetch of the arXiv abstract page and one of the PDF (the fetch tool cached the PDF in its tool-results folder); `pdftoppm` and `magick` to crop Fig. 3–4 from that PDF into my scratchpad; one web search. The gated Llama file listing returned masked hashes.
- **Evidence paths:** cached PDF `/Users/spiderishi/.claude/projects/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/c519cf93-2a82-40cd-bff7-64852d1f6d17/tool-results/webfetch-1792185392603-73i67d.pdf`; figure crops in the session scratchpad (`pdfpages/fig3.png`, `fig4b.png`). Both are outside the repository and temporary.
- **Files written:** this file only (plus scratchpad helpers).
- **Not done:** no code; no download of any model, dataset or repository data file; no pod; no reading of the Tülu 3 paper; SafeMERGE read in part only; no check of the engine's pinned `transformers` default dtype.
- **Limits:** Fig. 3–4 values are read from a figure image and are approximate. Costs marked (I) come from one Gate A ledger and the 16 Oct re-costing. The Hub facts are as of 16 Oct 2026 and can change; the pins above fix them.
