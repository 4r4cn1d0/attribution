# Book chapter guide: *Hands-On Machine Learning with Scikit-Learn and PyTorch* (Géron, October 2025)

7 October 2026. Which chapters you need to understand or change this project end to end. Built by a subagent of General Implementation 2 from the book's table of contents, the preface's roadmap, the Chapter 17 stub, and Chapter 15 pp. 621–633. "Not covered" means "not in the table of contents".

- **The book:** `/Users/spiderishi/Coding/Books/hands-machine-learning-scikit-learn-pytorch.pdf` (878 pages).
- **Page numbers below are the book's own.** PDF page = book page + 30.
- **Chapter 17 is online only** (homl.info). The PDF holds a two-page stub (p. 693).

## Must know

| Chapter | What it gives this project |
|---|---|
| **Ch 10: Building Neural Networks with PyTorch** (p. 317) | Tensors, GPUs, autograd, data loading, saving checkpoints. The training loop, and the gradients that attribution uses. |
| **Ch 11: Training Deep Neural Networks** (p. 363) | AdamW (p. 396), learning-rate schedules and warmup (pp. 398–404), gradient clipping (p. 382), transfer learning (p. 383). The recipe settings. AdamW's saved state is what the Adam-preconditioned attribution reads. |
| **Ch 14: the Hugging Face part only** (pp. 537–559) | Tokenizers, pretrained models, Trainer, pipelines. Data preparation and model loading. |
| **Ch 15: Transformers for NLP and Chatbots** (p. 577) | Attention (p. 581); decoder-only models and text generation (pp. 609–621); supervised fine-tuning with role tags, loss masking and per-token log-probabilities (pp. 621–633). Fine-tuning, answer generation and the held-out loss. |
| **Ch 17: Speeding Up Transformers** (online) | LoRA/PEFT, gradient accumulation, sequence packing, activation checkpointing, KV caching. The LoRA recipe and the micro-batch fallbacks. |

## Useful, not essential

- **Ch 1: The Machine Learning Landscape** (p. 3): validation and test sets, data mismatch (pp. 35–37). Why our splits are sealed.
- **Ch 2: End-to-End Machine Learning Project** (p. 41): creating a test set (p. 57), grid and randomized search (pp. 94–96), the final test (p. 99). Held-out discipline.
- **Ch 3: Classification** (p. 107): confusion matrix, precision, recall, ROC (pp. 112–124). Reading the judges' and the classifier's scores.
- **Ch 4: Training Models** (p. 135): gradient descent (p. 142), softmax and cross-entropy (p. 174). What attribution's gradients are.
- **Ch 9: Introduction to Artificial Neural Networks** (p. 285): backpropagation (p. 294), tuning guidelines (p. 308).
- **Ch 10's Optuna section** (p. 352): the book's closest material to our selector.
- **Appendix A: Autodiff** (p. 787) and **Appendix B: Mixed Precision and Quantization** (p. 795): bf16 training, and the 4-bit Granite judge.

## Skip

- Ch 5–8: trees, ensembles, dimensionality reduction, clustering.
- Ch 12: CNNs.
- Ch 13: RNNs and time series.
- The RNN parts of Ch 14.
- Ch 16: vision and multimodal.
- Ch 18: autoencoders, GANs, diffusion.
- Ch 19: reinforcement learning.
- The online Appendices C–E.

## Reading order (for someone who knows Python but is new to deep learning)

1. Ch 1 (skim)
2. Ch 4
3. Ch 9
4. Ch 10
5. Ch 11
6. Ch 3 (pp. 111–124)
7. Ch 14 (pp. 537–559)
8. Ch 15 (pp. 577–592, then 609–633)
9. Ch 17 (online)
10. Appendix B

Read Ch 2 pp. 57 and 94–99 at any point.

## What the book does not cover, and where this project covers it

| Topic | In this repository | Papers |
|---|---|---|
| LoRA/PEFT details | `experiments/safety_selection/loaders.py` | Hu et al., LoRA (2106.09685) |
| Chat templates (`apply_chat_template`, Qwen's template) | `experiments/safety_selection/textproc.py` | Lyu et al., PTST (2402.18540) |
| Training-data attribution, influence functions | `experiments/safety_selection/attribution.py` (its docstring: not LESS, TracIn or an influence function) | Koh and Liang (1703.04730); TracIn (2002.08484); LESS (2402.04333); Grosse et al. (2308.03296) |
| Representation similarity (hidden states) | Not built yet: item E6 in `research/experiments/2026-10-06-kill-test-design-DRAFT.md` | Hsiung et al. (2506.05346); Arditi et al. (2406.11717) |
| LLM safety judges and over-refusal | `experiments/safety_selection/scoring.py`; `scripts/killtest_stage0_reading.py`; `.ai/inputs/kill-test-stage0/second_judge_kt.py` | Granite Guardian (2412.07724); XSTest (2308.01263); Vishnubhotla et al. (2606.03648) |
| Near-duplicate exclusion | `experiments/safety_selection/prepare.py` (character 5-gram Jaccard ≥ 0.5) | — |
| Bootstrap intervals, Bonferroni, margins fixed in advance | the kill-test design draft; `experiments/safety_decision_policy/analysis.py`; the v2 results record | **Gap: no statistics reference in the reading list yet** |
| GPU determinism | `experiments/minimal_safety/model.py` (deterministic algorithms, TF32 off, CUBLAS_WORKSPACE_CONFIG) | — |
| Successive halving (our selector) | Design only, in `research/FOCUS.md` | Jamieson and Talwalkar (1502.07943); Hyperband (1603.06560); DataDecide (2504.11393) |
| Cost accounting | `research/costs/cost_ledger.py` | — |

The subagent did not verify the arXiv IDs for this list. The project's own reading list (`research/review/2026-10-06-reading-list-v2.md`) and the two-page reading dossier (`research/review/2026-10-06-reading-dossier.md`) are the checked sources.
