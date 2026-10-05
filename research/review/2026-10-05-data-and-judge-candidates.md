# Candidate data and judges for the next amendment (headroom v2)

5 October 2026. Written by General Implementation from the dataset and model pages, read on 5 October 2026. These are **candidates for review, not decisions**. Nothing has been downloaded beyond what the project already holds, and every licence must be re-checked when a version is pinned.

## Why we need them

Round 1 found three measurement problems ([round-1 results](../experiments/2026-10-05-headroom-round-1-results.md)):

1. **The endpoint is narrow.** Most "unsafe" answers were sexual-content compliance, because ToxicChat's toxic prompts are dominated by such requests.
2. **The test is small and binary.** There are 72 prompts with one greedy answer each, and seed noise reaches 10 within an arm.
3. **A second judge is missing.** ToxicBERT measures a different construct and flags almost nothing.

## Broader harmful prompts for evaluation

| Candidate | Size | Licence | Access | Notes |
|---|---|---|---|---|
| **HarmBench** (Mazeika et al. 2024, arXiv 2402.04249) | about 400 behaviours: standard, contextual, copyright | MIT | The `walledai` mirror on Hugging Face is gated (contact details); the canonical GitHub is the Center for AI Safety's | Broad harm categories; widely used |
| **StrongREJECT** (Souly et al. 2024, arXiv 2402.10260) | 313 prompts | MIT | The `walledai` mirror is gated; the original repository is on GitHub | Designed to be answerable only harmfully; has its own autograder |
| **SimpleSafetyTests** | 100 prompts, 5 harm areas × 2 kinds | CC BY 2.0 | Not gated | Areas: suicide, self-harm and eating disorders; physical harm; illegal items; scams; child abuse |
| **Do-Not-Answer** (arXiv 2308.13387) | 939 prompts in a risk taxonomy | CC BY-NC-SA 4.0 (code Apache-2.0) | Not gated | Non-commercial and share-alike. Fine for research; check before redistributing derivatives. |
| **OR-Bench toxic** | 655 prompts | CC BY 4.0 | Not gated | The harmful counterpart of OR-Bench's over-refusal set |

## Over-refusal: benign prompts that look harmful

| Candidate | Size | Licence | Notes |
|---|---|---|---|
| **XSTest** (Röttger et al. 2023, arXiv 2308.01263; canonical GitHub `paul-rottger/exaggerated-safety`) | 250 safe and 200 contrast-unsafe prompts | CC BY 4.0 | The standard small over-refusal test |
| **OR-Bench hard-1k** | 1,320 safe-but-scary prompts | CC BY 4.0 | Larger and harder. Not gated. |

Our current benign check is ARC questions, which cannot detect refusal of benign *sensitive* requests. One of these sets would fix that.

## A second safety judge

| Candidate | Size | Licence | Access | Notes |
|---|---|---|---|---|
| **Granite Guardian 3.3** (IBM; released 1 August 2025) | 8B (5B variant in the family) | Apache-2.0 | **Not gated** | Judges prompts and responses: harm, jailbreak, sexual content, violence, unethical behaviour. The easiest to adopt. |
| **WildGuard** (Ai2) | 7B (Mistral-7B-v0.3) | Apache-2.0 | Gated (Ai2 Responsible Use) | Prompt harm, response harm and **refusal**, in one model |
| **Llama Guard 3** (Meta) | 8B (8-bit variant) | Llama 3.1 Community Licence | Gated (contact details and licence) | 14 hazard categories (S1–S14); prompts and responses |
| Qwen3Guard-Gen-8B | 8B | Apache-2.0 | Not gated | Larger sibling of our judge. Not independent of it, so only a robustness check. |

**Proposed:** Granite Guardian 3.3 8B as the second judge. **Checked on round 1** (Q4_K_M, on the Mac): 92.5% agreement with Qwen3Guard, κ = 0.80, the same arm order. It is independent of Qwen, Apache-licensed and ungated. WildGuard is the alternative if the user accepts Ai2's terms.

## Harmful training examples (the harmful-fine-tuning setting)

| Candidate | Size | Licence | Notes |
|---|---|---|---|
| **PKU-SafeRLHF** | 82.1k rows (73.9k train / 8.2k test) | CC BY-NC 4.0 | Two responses per prompt with **safety labels, 14 harm categories and severity 0–3**. Responses come from Alpaca-7B/2-7B/3-8B/3-70B, WizardLM-30B-Uncensored and others. Lets us pick unsafe responses across many categories. |
| **BeaverTails** | 364k QA pairs | CC BY-NC 4.0 | Human safety labels over 14 categories. Mostly Alpaca-7B answers. |
| LLM-LAT/harmful-dataset | about 4,948 rows (prompt, harmful completion, refusal) | **Not stated** (empty README) | The prompts look AdvBench-derived. **Avoid unless the licence is clarified.** |

**Proposed:** use PKU-SafeRLHF unsafe responses, chosen by a fixed rule over its categories and severity, so the injected harm is broad rather than mostly sexual. CC BY-NC suits research; a public release of derived data must keep the attribution and non-commercial terms.

## Literature on measurement noise (read on 5 October 2026)

- **Fraser, Dawkins, Nejadgholi and Kiritchenko (NRC Canada), *Fine-Tuning Lowers Safety and Disrupts Evaluation Consistency*** ([arXiv 2506.17209](https://arxiv.org/html/2506.17209v1)).
  - Setup: Llama-3.2-1B and Mistral-7B fine-tuned on Dolly or Alpaca, evaluated on SORRY-Bench (440 prompts, 44 risk categories).
  - Seed spread: across 5 fine-tuning seeds, harmfulness varied widely (for example 0.73–0.82 for Llama-1B on Dolly at epoch 4, T = 0.7). Error bands overlap enough that single runs can reverse a conclusion.
  - They recommend multiple fine-tuning seeds, several generation settings, and reporting all parameters.
- **Larsen, *The Instability of Safety: How Random Seeds and Temperature Expose Inconsistent LLM Refusal Behavior*** ([arXiv 2512.12066](https://arxiv.org/abs/2512.12066v1)).
  - 18–28% of 876 harmful prompts flip between refusing and complying across 4 temperatures × 5 seeds.
  - A single answer agrees with the multi-sample ground truth only 92.4% of the time. He recommends **at least 3 samples per prompt**.
- **What this means for us:** these match round 1's noise analysis (mostly a shared seed shift, R = 3.3). They support about 5 fine-tuning seeds plus several sampled answers per prompt.
- **One more benchmark candidate:** SORRY-Bench (440 prompts, 44 categories). Its licence and gating are still to check.

## Rules every candidate must pass before use

- [ ] **Overlap:** no shared normalized prompt with any training row or any evaluation bank, checked inside the engine. Nobody reads the held-out prompts.
- [ ] **Splits made before anyone looks:** each new evaluation source is split into development, selector and hidden parts by the engine, as was done for ToxicChat.
- [ ] **Pinned:** an exact revision and the hashes.
- [ ] **Licence:** recorded, with attribution in any release.
- [ ] **Gating:** if a set is gated, the user accepts its terms personally.

## Sources

- [HarmBench (walledai mirror)](https://huggingface.co/datasets/walledai/HarmBench)
- [StrongREJECT (walledai mirror)](https://huggingface.co/datasets/walledai/StrongREJECT)
- [SimpleSafetyTests](https://huggingface.co/datasets/Bertievidgen/SimpleSafetyTests)
- [Do-Not-Answer](https://huggingface.co/datasets/LibrAI/do-not-answer)
- [OR-Bench](https://huggingface.co/datasets/bench-llm/or-bench)
- [XSTest copy (points to the canonical GitHub)](https://huggingface.co/datasets/natolambert/xstest-v2-copy)
- [Granite Guardian 3.3 8B](https://huggingface.co/ibm-granite/granite-guardian-3.3-8b)
- [WildGuard](https://huggingface.co/allenai/wildguard)
- [Llama Guard 3 8B](https://huggingface.co/meta-llama/Llama-Guard-3-8B)
- [PKU-SafeRLHF](https://huggingface.co/datasets/PKU-Alignment/PKU-SafeRLHF)
- [LLM-LAT/harmful-dataset](https://huggingface.co/datasets/LLM-LAT/harmful-dataset)
