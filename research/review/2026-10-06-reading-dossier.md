# Reading dossier: *Diagnose or Retrain?*

**Date:** 6 Oct 2026
**Status:** Direction adopted 6 Oct; design not frozen; kill-test Stage 0 running on 6 Oct (no result yet).

## 1. What we are doing

**The question.** When benign fine-tuning makes an aligned model less safe, which data fix restores safety without hurting the task or causing over-refusal? How much diagnosis is worth paying for before we choose?
- **Fixes:** keep the data, remove a source, add safety data, rewrite or self-distill.
- **Diagnostics:** classifier scores, representation similarity, training-data attribution, short trial runs.
- **Setting:** Qwen2.5-1.5B-Instruct with LoRA. Main: benign erosion (Dolly). Anchor: overt injected harm, rebuilt on the same model.

**Why it matters.** Fine-tuning services can block an unsafe fine-tune and tell the customer to fix the data and resubmit (one documented case; grant dossier §1a). Fixes have side effects, and we found no tested, costed rule for the choice.

**What is new: only the combination.** Each part exists alone. Closest: Xiao and Aranguri (no trial-run rival, no add fix, no seeds); SafeTune (no data fixes, one seed); DataRx (no removal, no costs).

**Evidence so far (development only).**
- **v2** (base model, injected unsafe answers, 2 seeds): a classifier-targeted rewrite cut sampled unsafe answers from 80.3% to 11.4%. But XSTest over-refusal rose from 1% to 44%.
- **Round 1** (2 seeds): a fixed-size top-K removal rule (1,015 rows; 43 harmful-answer rows in the editable pool) raised unsafe answers from 12.5 to 24.0 of 72.

**Main measures.** (1) Decision value per diagnostic against trial runs at matched compute, as a curve over the cost ratio (diagnostic cost ÷ one full run). (2) Side-effect prediction: does a diagnostic flag the fixes that break the over-refusal or task-skill limit better than trial runs of equal cost?

## 2. Reading list (22 core papers)

**★ = read first** (the first six starred papers, in the list's own order). **Full** = read in full through a fetch tool that summarizes pages; numbers are "reported" until checked in the PDF. **Summary** = abstract, metadata or earlier notes only; UNVERIFIED.

**A. Closest work**

| Paper | arXiv | Why we read it | Status |
|---|---|---|---|
| ★ Xiao and Aranguri | [2602.11079](https://arxiv.org/abs/2602.11079) | Prices several diagnoses; applies three data fixes | Summary (abstract checked) |
| ★ SafeTune (Seth et al.) | [2609.22153](https://arxiv.org/abs/2609.22153) | Likeliest "this was done" citation; model-level repairs only | Full |
| ★ DataShield (Zhang et al.) | [2606.00160](https://arxiv.org/abs/2606.00160) | Benign-erosion filter; prices scoring, never against runs | Full |
| ★ DataRx (Zhang et al.) | [2608.04322](https://arxiv.org/abs/2608.04322) | Which safety rows to add; measures the over-refusal cost | Full |
| ★ GradShield (Hu et al.) | [2605.14194](https://arxiv.org/abs/2605.14194) | Threshold set by safety and utility tolerances: nearest precedent for our limits | Full |
| Luo et al. | [2609.02771](https://arxiv.org/abs/2609.02771) | Rewriting beats deletion; the rewrite fix is not ours to claim | Full (HTML; 5 Oct note) |
| Pan et al. | [2502.11411](https://arxiv.org/abs/2502.11411) | Attribution beats classifiers on injected rows, from one run; we replicate it with seeds | Summary |

**B. Safety erosion after benign fine-tuning**

| Paper | arXiv | Why we read it | Status |
|---|---|---|---|
| ★ Qi et al. 2023 | [2310.03693](https://arxiv.org/abs/2310.03693) | The founding result (Alpaca, Dolly); defines the main setting | Summary (tool summary; read in full before citing) |
| Kim et al. | [2508.12531](https://arxiv.org/abs/2508.12531) | Better hyperparameters alone cut unsafe answers from 16% to about 5% | Summary |
| Lyu et al. (PTST) | [2402.18540](https://arxiv.org/abs/2402.18540) | Prompt templates decide much of the erosion; PTST is a near-free non-data repair | Summary |

**C. Finding the cause: classifiers, representations, attribution**

| Paper | arXiv | Why we read it | Status |
|---|---|---|---|
| He, Xia and Henderson | [2404.01099](https://arxiv.org/abs/2404.01099) | Selected benign rows break safety; never build data with the same signal | Summary (tool summary) |
| DATE-LM (Jiao et al.) | [2507.09424](https://arxiv.org/abs/2507.09424) | With look-alike data, attribution detection drops while classifiers hold | Summary (one passage checked) |
| Persona vectors (Chen et al.) | [2507.21509](https://arxiv.org/abs/2507.21509) | Flags data that will shift a trait: nearest precedent for side-effect prediction | Summary |

**D. Fixes: add, rewrite, self-distill**

| Paper | arXiv | Why we read it | Status |
|---|---|---|---|
| Bianchi et al. | [2309.07875](https://arxiv.org/abs/2309.07875) | About 3% safety data helps; too much causes over-refusal | Summary |
| Eiras et al. | [2406.10288](https://arxiv.org/abs/2406.10288) | Safety data in the task's format: the strongest add arm | Summary |
| SDFT (Yang et al.) | [2402.13669](https://arxiv.org/abs/2402.13669) | The baseline self-distill fix | Summary |
| López-Ávila et al. | [2609.04482](https://arxiv.org/abs/2609.04482) | Refusal data raised XSTest over-refusal from 2% to 74% | Summary |
| Dubiński et al. | [2604.25891](https://arxiv.org/abs/2604.25891) | Added data can hide misalignment that returns on training-like prompts | Summary |

**E. Decisions under a compute budget**

| Paper | arXiv | Why we read it | Status |
|---|---|---|---|
| DataDecide (Magnusson et al.) | [2504.11393](https://arxiv.org/abs/2504.11393) | Small runs scored by decision accuracy against compute | Summary |
| Ivison et al. | [2503.01807](https://arxiv.org/abs/2503.01807) | Charges selection compute against more training data | Summary |

**F. Evaluation and judges**

| Paper | arXiv | Why we read it | Status |
|---|---|---|---|
| Harmful fine-tuning survey (Huang et al.) | [2409.18169](https://arxiv.org/abs/2409.18169) | Field practice: no over-refusal, no seeds, cost only as future work | Full (HTML read as text) |
| Vishnubhotla et al. | [2606.03648](https://arxiv.org/abs/2606.03648) | Judges misread incoherent outputs; compare fixes at fixed task skill | Full |

**Full list:** 134 entries, with URLs in reading order, in `research/review/2026-10-06-reading-list-v2.md`. Cite the two "DataShield" papers by ID (2606.00160 and 2607.15081).

## 3. Five stages to a complete study

E = rise in the unsafe rate over the untuned model, in percentage points (pp).

| Stage | Goal | Main work | Gate or stop rule | Cost (estimate) | Weeks and dates | Output |
|---|---|---|---|---|---|---|
| **1. Kill test** | Show that erosion exists, is localized, and that attribution finds it | Stage 0 now; Dolly and Alpaca × 3 seeds; random-removal null; one removal run per source, then repeats; early side-effect check (3% safety mix) | Futility: E < 3 pp after one seed. Gate A: E ≥ 10 pp (15 to go on). Gate B: diffuse → kill source-level diagnosis. Gate C: attribution must beat representation similarity beyond seed noise, else shrink | $127–145 (first pod $5.22) | Weeks 1–2 (6–19 Oct) | Go, shrink or kill |
| **2. Build, calibrate, design freeze** | Build the study; fix its design | Sources as units; add and self-distill fixes; task-skill and coherence checks; representation similarity; costs in full-run units; successive halving; anchor rebuilt on the aligned model; calibration runs | Old recipes stay byte-identical. Design freeze hashed before development outcomes | $100–300 | Weeks 2–4 (13 Oct–2 Nov) | Engine; frozen design |
| **3. Development, numerical freeze** | Measure every arm; fix every number | 2 settings × ≥ 5 seeds; default add arm (diagnosis must beat it); Pan replication with seeds | Pre-set margins: each gain is negative, positive or inconclusive (→ new data or stop). Numerical freeze before hidden access | $1,500–3,000 | Weeks 5–9 (3 Nov–7 Dec) | Development tables; frozen numbers |
| **4. Held-out confirmation** | Test the frozen claims on unseen data | Held-out menus with sealed contamination; fresh seeds | No retuning; nulls and near-ties are reported | $1,000–2,000 | Weeks 10–11 (8–21 Dec) | Confirmatory results |
| **5. Analysis, paper, release** | Report and release | Analysis; writing; code, protocols, cost tables | ICML needs about $3–5k by early November; else NeurIPS 2027 (about mid-May; UNVERIFIED) | No GPU line | Weeks 12–15 (22 Dec–18 Jan); ICML deadline about 22 Jan 2027 (UNVERIFIED) | Paper, nulls included; open code |

Dates come from the BlueDot draft §5. Its single week-9 freeze is now the numerical freeze; the design freeze ends stage 2 (the user's two-freeze decision).

- **Money.** The user chose a $6,000 BlueDot ask on 6 Oct; it is not yet submitted. It covers all five stages (about $4,700 of it is GPU work, with contingency). The RunPod balance covers Stage 0 only, and every later spend needs a new approval.
- **What kills or narrows the study.** No erosion after the fallback ladder kills this setting at this scale. Diffuse erosion narrows the study to adding data. If attribution is no better than representation similarity, we drop or demote it. If no diagnostic beats random removal, we report "retrain wins". If the default add arm restores ≥ 80% of the erosion within +5 pp over-refusal, the default fix is enough here. We report every null.
- **Open decisions with the user.** FOCUS revision draft §15, items 2–9 (how decision value and side-effect prediction are defined and read, "remove a subset", the cost unit, non-data repairs) and §16 item 10 (how to test "beat the default mix"); kill-test spend after the first pod, Alpaca and the row-level removal arms; the BlueDot fields only the user can fill.

## 4. Claim rules

> - Never claim that practitioners ask whether attribution is worth its compute. We found no public evidence that they do.
> - Describe round 1 only as a finding about a fixed-size top-K removal rule, never as "classifiers fail".
> - Novelty is the combination. Do not claim rewriting, attribution-guided selection or "attribution beats classifiers" as new.
> - Every result so far is development evidence. Nothing is confirmatory.

*Sources:* `research/FOCUS.md`; `research/review/2026-10-06-reframing-proposal.md`, `-reading-list-v2.md`, `-focus-revision-DRAFT.md`, `-prior-work-search.md`, `-positioning-review.md`; `research/experiments/2026-10-06-kill-test-design-DRAFT.md`, `2026-10-06-headroom-v2-results.md`, `2026-10-05-headroom-round-1-results.md`; `.ai/briefs/kill-test-stage0-engine-20261006.md`; `research/grant/2026-10-06-bluedot-application-DRAFT.md`.
