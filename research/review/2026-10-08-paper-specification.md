# Paper specification: what the paper is about, the main study and the side studies

**Date:** 2026-10-08T13:42 UTC, 8 Oct 2026 (GI III, lead). **Status:** the user approved the sharpened direction in principle (FOCUS.md, 8 Oct) and the scale ladder; the detailed study plan is being reviewed in `research/review/2026-10-08-sharpened-direction-DRAFT.md` and may refine menus, methods and costs. Results marked "done" exist; everything else is planned. Development evidence only; nothing here is a held-out result.

## 1. The paper in one paragraph

Ordinary fine-tuning on benign instruction data can make an aligned language model stop refusing harmful requests. Practitioners then have to repair it, and the repair is a data decision: remove some training data, add safety data, or change the recipe. **This paper measures which data repair restores safety best for the compute spent, without raising over-refusal or losing task skill, and when it is worth paying for a diagnostic (training-data attribution, representation similarity, or a cheap answer-format heuristic) before choosing.** It answers this with a compute-matched, seeded comparison of repairs on two open model families, over repair menus of different sizes, and it reports where diagnosis pays as a function of menu size and diagnostic cost. A mechanism study explains *what* the fine-tuning breaks (refusal openings versus harmful content), which predicts which repairs should work.

**Working title:** *Repairing Safety After Benign Fine-Tuning: A Compute-Matched Comparison of Data Repairs, and When Diagnosis Pays.* (The current draft title "Diagnose or Retrain?" can stay as a subtitle.)

## 2. Research questions

- **RQ1 (main).** After benign fine-tuning erodes refusal, which data repair restores safety most per unit of compute, within limits on over-refusal and task skill?
- **RQ2 (main; the novel curve).** When does paying for a diagnostic beat trial-and-error retraining? Measured as decision regret under a fixed budget (successive halving over the repair menu) as a function of menu size M, diagnostic cost c (in full-run equivalents) and the diagnostic's ranking quality.
- **RQ3 (Gate B).** Is the erosion localized in identifiable parts of the data (categories; then clusters or rows), or diffuse?
- **RQ4 (side, mechanism).** What does benign fine-tuning change: the refusal opening, the harmfulness of content, or both? Does a standard-practice recipe change it?
- **RQ5 (side, generality).** Do the answers hold across two families (OLMo-2, Llama-3) and across sizes (1B → 7–8B → 32B/70B where funded)?

## 3. Setting (fixed)

- **Models:** OLMo-2-0425-1B-Instruct (main); Llama-3.2-1B-Instruct (second family); scale ladder OLMo-2-7B / Llama-3.1-8B (reduced), OLMo-2-32B (H200) and Llama-3.x-70B (B300) as a headline check if funded. Qwen2.5-1.5B/7B are reported as the *fragile* contrast (they saturate under the same recipe; done).
- **Benign data:** Dolly-15k, 4,800 rows in 8 category units of 600 (prepared, sealed, manifest per tokenizer).
- **Fine-tune:** recipe B (LoRA r64, all linear, LR 1e-4 constant, batch 128, one epoch = 38 steps); recipe G (token-mean loss + warmup) as the standard-practice variant.
- **Outcomes:** U = Qwen3Guard Unsafe share of 600 sampled answers to 200 dev harm prompts; E = U(fine-tuned) − U(untuned). Also: a compliance judge (HarmBench classifier: does the answer carry out the behaviour?), hard-category U, Granite Guardian as a second judge, over-refusal R on 100 borderline-safe prompts (XSTest-safe + OR-Bench-hard), task skill (held-out Dolly loss; ARC reported but weak at 1B). Held-out prompt sets confirm the final claims.
- **Cost accounting:** every run and every diagnostic is charged in full-run equivalents (FRE) and dollars, measured.
- **Discipline:** every decision rule is committed before the data it judges; seeds; sealed units; independent audits.

## 4. Main study

### 4.1 Gate A (done; the entry condition)
- OLMo-2-1B under recipe B: E = +43.5, +43.7, +48.2 pp over three seeds (mean +45.1, partial). Answers end; task learned; Granite agrees. Independent six-lens audit: sound with caveats (U tracks refusal; screening of five settings; three seeds).
- Qwen2.5-1.5B/7B saturate (+75 to +82 pp); rank 16 reduces it only to +67.8 pp.

### 4.2 Gate B and Gate C (next; pre-registration draft written)
- **Gate B:** remove each Dolly category (8 arms) vs random removal of the same size, seed-matched contrasts, guards against degenerate or over-refusing arms; verdict LOCALIZED / DIFFUSE / TOO CLOSE. Detection limit stated openly: 8 pp detected about half the time; 80% at about 10–12 pp.
- **Gate C:** which diagnostic picks the culprit category: training-data attribution (gradient similarity, bi-anchored), representation similarity, or a format/length heuristic (a recent paper shows gradient similarity often tracks answer format). If attribution only matches the format heuristic, the paper says so.
- Sealed draws committed (5 random removals, 16 length-matched controls, 8 category removals, the Gate C sample).

### 4.3 The repair benchmark (stage 1 on OLMo-1B; stage 2 on Llama-1B)
- **Repair menu:**
  - *Removal:* random (matched size); category removal; cluster- or row-level removal selected by (a) the format/length heuristic, (b) published filters that are feasible (candidates: DataShield, LARF, SQSD, bi-anchoring, Self-Inf-N), (c) training-data attribution, (d) representation similarity.
  - *Addition:* a random safety-data mix; a selected safety-data mix (DataRx-style, or diagnosis-guided); a handful of refusal examples (the "10 rows" repair).
  - *Recipe only:* recipe G, as the no-data-change reference.
  - *References:* no repair (a0); the untuned model.
- **Menus of different sizes:** 8 (categories), tens to about 128 (clusters), row-level under a fixed budget. Menu size is the axis of RQ2.
- **Per repair:** ΔU against a0, Δ(compliance judge), ΔR (over-refusal, judged against the untuned model's level), Δ(task skill), cost in FRE; seeds sized by a power analysis.
- **Decision value (RQ2):** simulate and measure the regret of successive halving with and without each diagnostic, as a function of (M, c, ranking quality). The headline figure is a "when diagnosis pays" map.

### 4.4 Generality (RQ5)
- Stage 2 on Llama-3.2-1B for the key comparisons; reduced benchmark at 7–8B; headline check at 32B/70B if funded. Every comparison stays on one GPU type.

## 5. Side studies

1. **Mechanism: refusal openings vs harmful content** (exploratory note done; `research/review/2026-10-08-mechanism-first-tokens.md`). Fine-tuning swaps refusal openings for direct ones (OLMo −50 pp; Qwen −85 pp), but that switch carries only about half the Unsafe increase; direct answers also became more harmful. The erosion is broad across prompts and stable across seeds. *Causal tests:* recipe G (token-mean loss + warmup; running 8 Oct) and a first-token refuse-vs-comply margin measured on Gate B pods. *Prediction recorded:* a first-token path alone gives at most about 3 pp per category, so a LOCALIZED Gate B would need a content effect.
2. **Why some models saturate** (done, two literature notes plus the rank-16 test). Our recipe stacks four amplifiers (no warmup, a large adapter, per-example loss, human-written short answers); Qwen saturates, OLMo is partial; published Qwen LoRA runs mostly erode less. Report as context, not as a main claim.
3. **Measurement validity** (partly done). Qwen3Guard vs Granite vs HarmBench's compliance classifier on the same answers; hard-category U; the "Guo gap" analysis (judge and prompt differences explain at most about 13–30 pp). Purpose: say exactly what "unsafe" means in our numbers.
4. **Over-refusal as the cost of repair.** Every repair is scored on over-refusal against the untuned model, so a repair that "fixes" safety by refusing everything is visible.
5. **Second family and scale** (Llama-3.2-1B probe running 8 Oct; 7–8B probes after a top-up).

## 6. Claims we expect to make (and must not make)

- **Expect:** a measured ranking of repairs per unit of compute with side effects, on two families; the "when diagnosis pays" map; the mechanism decomposition; whether Dolly-category localization exists.
- **Do not claim:** that practitioners ask whether attribution is worth its compute; that adding safety data works by default (DataRx: a random 1% mix made Llama3-8B less safe, 20% → 59%; a selected 1% gave 14%); that our U equals published ASR (different judge and prompts); that Qwen is uniquely fragile at 7B.

## 7. Positioning (to finalize after the sharpened-direction review)

Closest work: Qi et al. 2023; He et al. 2024; Guo et al. 2026 (2609.01455); DataRx (2608.04322); DataShield (2606.00160); LARF (2507.18631); SQSD (2605.04572); Self-Inf-N (2505.06843); Yin & Rush (2410.16208: selection compute vs training compute; predicts retraining wins at equal size); Data2Behavior (2602.04735); TuneAhead (2606.17660); format detection (2609.19589). Our gap: a compute-matched, seeded comparison of removal *and* addition repairs with over-refusal and skill measured, across families and menu sizes, plus the decision-value map.

## 8. Venue and timeline

NeurIPS 2027 or TMLR is realistic; ICML 2027 only if funding arrives in time for two families × at least two sizes (second independent review, 8 Oct).

## 9. Status table (8 Oct)

| Item | Status |
|---|---|
| Gate A (OLMo-1B, 3 seeds) | done: PASS |
| Qwen saturation, rank 16 | done |
| Mechanism (observational) | done |
| Recipe G causal test | running |
| Llama-3.2-1B probe | queued (8 Oct) |
| HarmBench compliance judge | running (local) |
| Gate B/C pre-registration | draft; awaiting user acceptance of rules |
| Gate B engine/kit/reading | brief under revision; needs the Specialized chat |
| Repair benchmark | plan under review |
| 7–8B and 32B/70B | after funding |
