# Diagnose or Retrain? Repairing LLM safety after benign fine-tuning

Working title: *Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning*.
When fine-tuning on benign data erodes an aligned model's safety, which data repair restores the most safety for
its compute, and does paying for a diagnosis (classifiers, representations, training-data attribution) beat
spending the same compute on retraining?

- [Current research focus and log](research/FOCUS.md)
- [Rigor and novelty evidence ledger](research/review/EDGE_CHECKS.md)
- [Experiment engine](experiments/safety_selection/README.md)
- [Stage-1 run kit](runkit/stage1-olmo/)
- [Measurement audit and limitations](research/experiments/2026-10-02-measurement-audit.md)
- [Preserved backup inventory](backups/2026-10-02/README.md)
- [Runpod incident and recovery prerequisites](research/experiments/2026-10-02-runpod-credit-incident.md)

This is the private working repository. The anonymous review package is built separately, with a fresh history,
restricted contents and neutral author metadata (`tools/anon_release/`; route in
`tools/anon_release/RELEASE-PLAN.md`). Historical coupling work remains preserved under `pilot/` and
`research/pilot/`; it answers a different question from the current study.

## Study plan by stage

Status on 30 October 2026, from [FOCUS](research/FOCUS.md). Each stage runs under rules that are frozen before its outcomes are seen. Status words: done, running, planned, waiting on funding. This section gives no outcome of stage 1 or later.

Plan of record: the [adopted direction](research/FOCUS.md) (6 Oct), sharpened on 8 Oct by the [study plan](research/review/2026-10-08-sharpened-direction-DRAFT.md) that the user approved as the basis. Frozen texts: the [Gate B/C pre-registration](research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md) (revision 5, frozen 10 Oct), the [stage-1 pre-registration](research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md) (revision 4) and the [W1 record](research/experiments/2026-10-16-stage1-commitments.md), committed before Gate B wave 1. Until the anonymized public deposit is posted, the paper says "pre-specified in a dated git record".

### The question

When fine-tuning on benign data erodes an aligned model's safety, which data repair restores the most safety for the compute that it uses, within limits on over-refusal and task skill? Model-level references that change no data bound the gain. Does a paid diagnosis ever beat the same compute spent on retraining? Does the answer change with menu size and model family? Headline order: (1) the measured repair comparison; (2) the planted-cause control, if funded; (3) Gates B and C. The decision-value map is secondary and model-based.

### What the study compares

Data repairs (600-row removals, 48-row additions):
- **R**: random removal, 75 rows per category.
- **A1**: the sealed top 600 rows by the bi-anchored checkpoint-gradient attribution score from the wave-0b pass. Claims name it "a bi-anchored gradient-similarity filter", never "attribution" in general.
- **L1**: LARF-style representation filter. **H1**: the 600 shortest answers.
- **S1**: random PKU-SafeRLHF refusal rows. **S3**: DataRx-style selection. **S4**: the untuned model's own refusals.

References (no data change): a safety prompt (SP); low-rank adaptation (LoRA) adapter scaling (λ = 0.9, 0.75, 0.5); recipe G; B+Qi (recipe B with Qi et al.'s constrained loss); Safe LoRA (K = 39). "Data repair beats model-level repair" needs the dominance family (Holm over six) to reject.

Diagnostics, charged at measured cost: the content classifier, representation similarity, attribution, the free answer-form score, trial runs.

Measures:
- **U** (primary): the Qwen3Guard Unsafe share of 600 sampled answers to the 200 dev harm prompts.
- **Judge rule**: "harm" only if the HarmBench contrast has the same sign and at least half the size. Granite Guardian is reported.
- **O**: over-refusal on the 500-prompt bank (dev 100 plus 400 PHTest).
- **L**: task loss on 200 held-out rows.
- **Cost**: graphics processing unit (GPU) seconds by stage, in full-run equivalents (FRE), under the C-full and C-lean conventions.

### Gate A: erosion to repair?
- **Runs**: recipe B (LoRA rank 64, one epoch, 4,800 Dolly rows in 8 units of 600), 3 seeds, and the untuned model.
- **Feeds**: the recipe and the go for Gate B.
- **Status**: done. OLMo-2-1B passed (8 Oct; [results](research/experiments/2026-10-07-kill-test-stage0-results.md), [audit](research/review/2026-10-08-gate-a-audit.md)). Llama-3.2-1B at learning rate 5e-5 is recorded as a pass under paper decision 25 (10 Oct).

### Gate B: localized or diffuse? (OLMo-2-1B, engine X)
- **Runs**: wave 0a (R_1–R_3, noise gate); wave 0b (a0-1101 retrain and the diagnostics over all 4,800 rows); wave 1 (8 unit removals at 1101); wave 2 (top units at 1102–1103); automatic extension and length control by rule.
- **Measures**: unit removal against R, with a floor of 8 percentage points (pp) and guards G1–G4.
- **Feeds**: LOCALIZED, DIFFUSE or TOO CLOSE; the blinded seed rule (plan A or B) from the final pooled noise estimate.
- **Status**: done. Frozen reading TOO CLOSE (23 Oct); no extension called; `--final` reported. By the frozen rules stage 1 runs unchanged; the seed rule gave plan A. [Outputs](research/experiments/2026-10-16-gate-b-wave0-outputs/).

### Gate C: do the diagnostics find the unit?
- **Status**: rankings sealed before wave 1; the verdict is not read, because Gate B did not read LOCALIZED.

### Stage 1: the repair comparison (OLMo-2-1B, recipe B)
- **Runs**: a0 and R at 1101–1107; A1, L1, H1, S1, S3, S4 at 1102–1107 (50 cells, 44 new runs); references on the a0 seeds (recipe G and B+Qi at 1102–1107).
- **Measures**: P1–P6 (A1, L1, H1 against R; S1 against a0; S3, S4 against S1) under the paired model with one variance per arm (HB-C); labels better, equivalent, worse, inconclusive at a 5 pp margin; the closed testing family Φ at 5%; τ_O* = 5 pp against the untuned model (2 and 10 pp reported); τ_L from the standard deviation of a0's task loss over seeds.
- **Feeds**: the headline repair table, the dominance family, the stage-3 pick.
- **Blocks** (each on a funding event; only complete blocks analysed):
  - Block A (the six repairs at 1102–1104; a0 and R at 1104; the diagnostics passes): done 27 Oct, judges included. Its outcomes stay sealed until block B is complete. The engine X → Y certificate then passed.
  - Block B (1105–1107; references): running. Phase 1 (arms, recipe G, B+Qi on engine Y, phase-1 references) is done. Phase 2 (reference evaluations and Safe LoRA at a0 1105–1107): b-17 running; b-18 to b-20 and the two judge pods wait on funding. [Prep records](research/experiments/2026-10-27-block-b-prep/).
- **Judges**: HarmBench and Granite judge pods per block, one device per contrast. Block A: done. Block B: waiting on funding.
- **Reading**: B16 ([code](scripts/stage1_s1/reading/)) prints every label; nobody labels by hand. Status: planned, after block B's judges.
- **Selector predictions** (secondary): committed before wave 1 (done); scored on Llama's Gate B-lite (planned).
- **Human label check** (two raters, about 450 answers): waiting on funding (rater budget); the design route is the user's.

### Stage 1b: planted-cause control
37 PKU-safe, direct answers planted as one leaf; menus of 8, 32 and 128 cells; a 3-seed pilot gate (Λ ≥ 10 pp, lower bound above 5 pp); then the main sweep. Status: planned; waiting on funding.

### Stage 1c: secondary arms
R_1200 and R_2400, R_tok, R+S1, DataShield-style, H2a/H2b, H1 under recipe bt, L8 octiles; 3 seeds each, in the frozen order. Status: planned; waiting on funding.

### Stage 2: Llama-3.2-1B
Gate B-lite (rules frozen with the W1 record) tests the selector predictions; P1–P6 replicate with δ_fam scaled to Llama's erosion. Status: Gate A done; the rest planned, waiting on funding.

### Stage 3: confirmation
At most 2 contrasts per family by the frozen pick rule; fresh seeds; engine Y's confirmation role on the sealed 200-prompt hidden subsample. Status: engine Y certified; runs planned.

### Later
- 7–8B: OLMo-2-7B and Llama-3.1-8B (main-recipe learning rates fixed by probes: done), OLMo 3 7B Instruct if funded ([notes](research/review/2026-10-17-olmo3-7b/)). Its [pre-registration, Part 1](research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md), is a draft; the [re-plan](writing/paper/2026-10-17-icml-replan-PROPOSAL.md) is a proposal.
- Alpaca as the second benign data set; a headline check at 32B, and 70B if funded ([design note](research/review/2026-10-17-icml-78b-prep/32b-70b-design.md)). Cut order if money is short: 70B, 32B, OLMo 3 7B.
- Status: planned; waiting on funding.

**Budget rule**: a block starts on a funding event or, since 29 Oct, from the live balance by the user's rule, never on an outcome; pods launch as the balance allows, under the $10/h price limit.

### Code by stage
The engine (`experiments/safety_selection/`, rounds X and Y) runs the gates and stage 1. Gate B's kit is `runkit/gate-b-olmo/`; stage 1's kit is [`runkit/stage1-olmo/`](runkit/stage1-olmo/), with builders in `scripts/stage1/` and `scripts/stage1_s1/`. The anonymous mirror holds the early stage-A engine and the stage-B decision-policy package from the 2 Oct design; later-stage code is released at submission.
