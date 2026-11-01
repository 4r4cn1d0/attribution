# Sharpened direction: study plan (DRAFT, revision 2)

**DRAFT for the user's approval; not adopted; no spend authorized.**

Written 2026-10-08 13:46 UTC (clock checked) by an Opus worker for the lead (GI III). Revision 2 of the 13:16 UTC draft. It answers three adversarial reviews: novelty (9 major, 15 minor), feasibility (7 major, 16 minor) and methods (9 major, 17 minor). Read-only work: no pod, spend, download, commit or engine edit. No held-out data and no prompt or answer text was read. The text for FOCUS.md is in the sibling file `2026-10-08-focus-amendment-sharpened-DRAFT.md`.

Labels: **R** = I read or computed it (path:line, section or table). **R†** = a review read it (NOV, FEA, MET = the novelty, feasibility and methods reviews; POS, FIL = the sibling positioning and filter reports quoted by the 13:16 draft); I did not re-read it. **I** = inference or estimate. **UNVERIFIED** = not checked.

Short names: FOCUS = `research/FOCUS.md` (line numbers of 13:32 UTC today); GBD = `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (revision 3); AUD = `research/review/2026-10-08-gate-a-audit.md`; EAL = `research/review/2026-10-08-erosion-amplifiers-literature.md`; GUO = `research/review/2026-10-08-guo-gap-analysis.md`; RL2 = `research/review/2026-10-06-reading-list-v2.md`; MECH = `research/review/2026-10-08-mechanism-first-tokens.md`; ICML = `writing/paper/2026-10-08-icml-draft.md`; SPEC = `research/review/2026-10-08-paper-specification.md` (13:42 UTC); GRANT = `research/grant/2026-10-05-grant-evidence-dossier.md`; POW = the power simulation `…/scratchpad/sharpened/power/power_menu_sim_out.txt` (session scratchpad, not in the repo); SS = `experiments/safety_selection`; LEDGER = `tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/ledger.jsonl`; PKUC = my count script `…/scratchpad/sharpened/pkucount/count.py` (counts only).

## 0. Answer to the user: right track, or improve the idea?

**Right track. The problem, the setting and the gates are sound. Improve the idea in six ways before stage 1 is frozen (I).**
1. **Change the headline.** All three reviews agree: "the value of diagnosis" (V_max, Δ, c\*) is mostly a model output at the menus we can afford, and it is near zero by construction there (NOV major 2; FEA M6; MET M1). Lead with the *measured* repair comparison, with equivalence bounds. Keep the decision-value map as a secondary, labelled, model-based figure with predictions written down in advance.
2. **Add a positive control.** Plant a known eroding cause in one cell and test whether diagnosis finds it at menu sizes 8, 32 and 128 (§6). This makes a null readable. It is also the only way to *measure* the menu-size axis at this budget.
3. **Spend on fewer arms with more seeds.** Six primary repairs at 6 seeds, not twelve at 3. Three seeds cannot rule out the 0–6 pp gaps that papers report (MET M4; POW Table 1c).
4. **Fix the safety-data arms.** DataRx's random arm draws from refusal-only rows (R: DataRx §III-C, §IV-B, by fetch). So our old "noisy" arm S2 was harmful-data injection. It is dropped. S1 is now the DataRx test.
5. **Add zero-training references.** A safety prompt and a down-scaled adapter answer the reviewer's question "why not fix the model instead?" (NOV major 9).
6. **Be honest about cost.** Generation is about 81% of an arm; training is about 8% (R: LEDGER). Report GPU-seconds and two cost conventions, so no claim rests on our evaluation size.

**Conflict to resolve.** The lead's paper specification (SPEC §2, §4.3, written 13:42 UTC) makes the "when diagnosis pays" map a main question (RQ2) and the headline figure. This revision demotes it unless the positive control is funded. GPT and the user must choose (§15, decision 2).

## 1. Key evidence from the research reports

1. **Gate A passed:** E = +43.5, +43.7, +48.2 pp, mean +45.1 (R: FOCUS:83). U is close to "did not refuse": P(Unsafe | no refusal) is 0.91–0.94 (R: AUD:61). Under hard categories E is about 28 pp (R: AUD:11, :52).
2. **The judge is coupled to refusal.** After fine-tuning, Qwen3Guard labels 22–29% of benign over-refusal answers Unsafe (R: AUD:81). Unsafe is 52.8% and 50.1% among answers of 32+ tokens (R: AUD:52).
3. **The fit happens early.** The loss plateaus by step 2–3 of 38 (R: AUD:89; EAL:23).
4. **Noise.** Clustered SE(U) 2.8 pp per arm; seed SD 2.65 pp on 2 df; 69–72% of the clustered variance is between prompts; no common-random-number gain (correlation −0.08) (R: GBD §2).
5. **Gate B power.** An 8 pp unit reads LOCALIZED about half the time; 80% needs about 10–12 pp. The prior favours DIFFUSE or TOO CLOSE (R: GBD §4, §8).
6. **Cost of an arm** (R: LEDGER, one Gate A arm): training 245 s; greedy generation 1,750 s for 468 prompts (46 capped); sampled generation 761 s for 600 answers; guard and scoring 293 s; total about 3,115 s. Generation is about 81%. Rates: 34–52 min per arm, $1.59/h (R: GBD §9).
7. **Mechanism.** The fine-tune swaps refusal openings for direct ones; that switch carries about 0.42–0.64 of the Unsafe increase (R: MECH:59). Only 0.19% of Dolly targets open with a refusal (R: MECH:70).
8. **Recipe amplifiers.** Under the per-example mean loss the first 5 answer tokens carry 17.7% of the objective, against 5.3% under a token mean (R: FOCUS:114). OLMo-2 has no system turn (R: EAL:66). Saturation is more likely than partial erosion for Llama at 1B (R: EAL:64).
9. **Guo gap.** Published Qwen LoRA runs on random benign data reach at most about 50%; selected subsets reach 83–88% (R: GUO:63; FOCUS:114). So row choice shapes erosion (Guo Table 5, per the brief).
10. **DataRx** (2608.04322): a random 1% mix raised Llama3-8B's ASR from 20.24% to 59.23%; the selected 1% gave 13.70% (R: RL2:102). Its pool is harmful instructions with refusal responses, and the random arm draws from that pool. The 3 benchmarks are averaged; no seeds (R: arXiv HTML §III-C, §IV-A/B, Table II, via fetch; not PDF-checked).
11. **Published scoring costs** for 10,000 rows: LARF 0.17 h, DataShield 0.50 h, bi-anchoring 3.5 h (R: RL2:44, DataShield Table IV).
12. **Closest prior work.** DualSelect (2606.09866) studies benign fine-tuning erosion on 1B–8B models with joint task and reference selection (R: arXiv abstract, fetch). It compares random, SafeInstr, SEAL, LARF, TOSS and SQSD with 3 seeds and a false-refusal rate (R†: NOV, HTML §4). Yin & Rush (2410.16208) find costly selection rarely compute-optimal (R†: NOV). Monitor-guided representation repair (2609.34771), Bakman et al. (2609.38379) and MNEME (2507.21084) are near (R†: NOV).
13. **Cheap model-level fixes exist.** A safety prompt at test time only gave 1.1% (R: EAL:26, citing 2402.18540 Table 1c). Ten self-generated refusals restored an identity-shift collapse from 99.8% to 0.77% (R: EAL:52, citing 2501.13453).
14. **Engine facts (R).** Edit arms run on the dev split only (SS/jobs.py:23-24). A role may evaluate only its own bank (SS/jobs.py:47-48, :168-180). The held-out partition of kt-dolly is empty (SS/prepare_task.py:24-25, :378). Edits support remove, rewrite and add (SS/edits.py:8-13); `build_add` has no command (SS/headroom.py:299-304). Per-row gradients go to the CPU as float64 (SS/engine.py:661-680). An eval-state job exists (SS/runner.py:745-760). Only Qwen's system template is handled (SS/textproc.py:299-313).
15. **PKU pool (R: PKUC, counts only, new).** 147,814 responses in the three local splits; 71,689 are PKU-safe. Only 3,028 PKU-safe responses open with a refusal under the frozen lexicon `bbbc71e9…`; they cover up to 2,636 distinct prompts (845 + 1,078 + 713; cross-split overlap not removed). Alpaca3-8B: 21,019 of 41,900 safe.
16. **Power** (R: POW). MDE for one contrast at 3 seeds: 6.5 pp (reference 3) or 5.7 pp (reference 5), central noise. At a fixed 24 runs: K = 4 arms at 6 seeds give 5.3 pp; K = 8 at 3 seeds give 8.6 pp (Table 1c). A 600-row filter clears 6.4 pp only if the findable effect is about 11–14 pp at row AUC 0.9 (Part 3).
17. **Money.** Balance about $17.50; Gate B needs about $37–42 of new money (R: GBD §9, §12). Lean grant tier $3,050 (R: GRANT:225).

## 2. Attack summary and how each major issue is resolved

The three reviews agree on four points: the decision-value headline is mostly a simulation; the plan has no positive control; the cost unit is mostly evaluation; and S2 is mis-specified. They differ on money (FEA: a 14-run minimal stage) and seeds (MET: 6 seeds, at most 4 arms).

| ID | Issue (short) | Resolution | Where |
|---|---|---|---|
| NOV-1 | Menu size is modelled, not measured; additivity untested | Planted-cause sweep at M = 8/32/128 measures it with known truth; its nested removals test additivity. Natural menus measured at M = 8 only. If §6 is unfunded, "menu size" leaves the headline. | §3.2, §6 |
| NOV-2 | V_max ≈ 0 by construction at measured menus | Decision value is secondary. Predicted V_max and c\* are pre-registered from the frozen selector spec; report measured against predicted; τ_O grid; the outcome table and top-k hit rates lead. | §3.2, §4.5 |
| NOV-3 | No positive control | Planted-cause sweep with a pilot gate. | §6 |
| NOV-4 | Runs-only reference is weak at fine menus | Hierarchical bisection joins SH and one-shot in the selector spec. One rule per (M, B) cell is frozen in advance; the oracle "best of" is reported separately. | §4.5 |
| NOV-5, FEA-M1, MET-M3 | FRE is mostly evaluation; c0 assumed | GPU-seconds split by stage; two frozen cost conventions; 1 FRE = median R-arm time per family; c0 measured on one real lean job; c\* under both; no 7–8B claim from 1B ratios. | §8 |
| NOV-6, MET-M4 | Screening underpowered; family question too weak | Six primary contrasts at 6 seeds (R 8), Holm 5%, SESOI 5 pp with TOST, three labels, blinded seed-count rule. Family claim limited to "same sign; difference below the stated MDE". | §4.3, §5.1, §12 |
| NOV-7, FEA-M7 | DataRx mapped to the wrong arm; S2 is harmful injection | Checked: DataRx's random arm is refusal-only. S1 is the DataRx test; S2 dropped. Pool built from PKU labels and the frozen lexicon. | §5.1, §5.5 |
| NOV-8, MET-M6 | U ≈ refusal; O from the same judge; pools filtered by the judge | HarmBench claim rule; HB on every arm; selectivity score; U by length band; O against the untuned model; a refusal-shift reference curve; new pools and S4 never filtered by Qwen3Guard. | §4.2, §5.2, §7 |
| NOV-9 | No zero-training, non-data reference | Mandatory: safety prompt (user-turn prefix), adapter scaling λ = 0.75 and 0.5, recipe G. The data-only user is named. | §5.2 |
| FEA-M2 | Prepared-data and engine lock-in | Keep manifest `9ed61826…` and the sealed files. O-ext and the LARF layer move off hidden and selector banks. Later measurements regenerate adapters by deterministic train-only re-runs. One determinism re-run after any engine change. | §9 |
| FEA-M3 | Confirmation blocked by access rules; underpriced | Engine round Y: a confirmation role for sealed edit arms on a 200-prompt sealed hidden subsample, reference-namespace seeds. Priced at 1.25 × an arm. | §9, §10 |
| FEA-M4 | Stage 1 underpriced; cash cannot start it | Re-priced. Two outcome-free seed blocks, each a funding event; only complete blocks are analysed. Block A is about the cost of FEA's minimal stage. | §10 |
| FEA-M5 | Attribution cost unmeasured; inline cost unmeasurable | A1 priced only from the wave-0b ledger. "Inline cost" dropped from claims. Speed-ups are a separate engine round. | §8 |
| FEA-M6 | Fine-menu headline unmeasurable | Headline = measured repair frontier. Natural M = 8 measured. Larger M only via §6 or a labelled model. The κ split is dropped. | §3.2, §6 |
| MET-M1 | Headline estimand is a model output | Labelled model-based. Generative model and estimator frozen before Gate B wave 1. Held-out test of its predictions on Llama's Gate B-lite. | §4.5 |
| MET-M2 | Simulation selector ≠ estimand selector | One selector spec and one code path for simulation and replay; two effect shapes; Δ for the method menu defined apart from V_max. | §4.5 |
| MET-M5 | No primary hypothesis or testing order | Primary family and order fixed. Side-effect prediction demoted to secondary with an estimand (user decision; FOCUS:25). | §4.3 |
| MET-M7 | Dose, loss weighting and category confounds | R+S1 cell completes a 2 × 2; rankings only at pre-registered doses; step counts printed; recipe G and H1-under-bt as loss references; Llama's loss weighting fixed; a category-matched control for L8. | §5, §12 |
| MET-M8 | Scorers tunable on Gate B outcomes | Every stage-1 scorer's code and settings hash, every outcome-free edit rule, the pools and the plant are committed before Gate B wave 1. Later scorers are "post-Gate-B exploratory". | §9 |
| MET-M9 | κ biased upward and split-dependent | κ and the concentration split are dropped. | §6, §11 |

**Reasoned disagreements (one line each).**
- FEA-M2(a), re-prepare the data now: no; it voids the committed sealed files (10a2894) and the Gate A pairing just before Gate B, and both needs it serves are met without the hidden or selector banks.
- NOV-6(c), buy prompts instead of seeds: the $0 check runs, but the seed term is about two thirds of per-arm variance (2.17² of 2.65²; R: POW Part 1), so more prompts cut the MDE by about 10% at most (I).
- NOV-3, build the plant from Self-Inf-N outliers: no; Self-Inf-N is a compared scorer; the plant uses PKU labels and the frozen lexicon only.
- NOV-4, run a real bisection path: only in replay and through the sweep's nested levels; a real path to M = 128 costs about 28 runs (I).
- FEA-m14, drop the safety prompt: kept as an evaluation-only reference through a pinned script; it is not on the repair menu and needs no engine codec change.
- FEA-M4, a 14-run, 3-seed stage: kept as seed block A, but no claim is read before block B, because 3 seeds cannot give equivalence bounds (MET-M4).

**Minor points handled.** NOV: family wording (§12); H1 loss weighting (H1-bt arm, token mass reported); H2 split into H2a/H2b; κ (dropped); baseline fidelity (deviation tables, author contact, two-anchor rank overlap); dose points (R_1200, R_2400); MNEME cited, side-effect prediction demoted; "free" arms charged; no oracle selector; stratification (composition reported, compared with Gate B's unit arm); one power table (§4.3); O-ext does not shrink hidden banks; a published-setting replication first in stage 4; venue (§14); two headline options (§15). FEA: m1 (wave-0b guard +$2–3), m2 (eval-state exists), m3 (no retention needed), m4 (short-answer O, $0 truncation and paired-SE checks first), m5 (no guard filter), m6 (one pinned untuned-answer script), m7 (L8 11–15 runs), m8 ("X-style" names; He-style init dropped), m9 (step counts), m10 (κ dropped), m11 (HB on the pod), m12 (Llama re-priced), m13 (totals), m14 (above), m15 (E6 = Gate C's module, frozen once), m16 (a self-distill arm in the DIFFUSE branch). MET: m1 (O-ext outside the manifest; failure-query attribution dropped), m2 (stratified by source), m3 (estimator), m4 (one convention), m5 (confirmation also on dev), m6 (no A1 arm at seed 1101), m7 (S3 from S1's pool is DataRx's own design), m8 (similarity strata), m9 (within-category cells; sealed tie-breaks), m10 (L on all 200 rows), m11 (f = 1; lexicon check), m12 (truncated share), m13 (Jaccard matrix), m14 (seed blocks, interleaving), m15 (Llama rules before its Gate A), m16 (FOCUS:87; POW's model named), m17 (selector split no longer used).

## 3. The question and the claims

### 3.1 Question (proposed text for FOCUS:11)
"When benign fine-tuning erodes an aligned model's safety, which data repair restores the most safety for the compute spent, within over-refusal and task-skill limits? The repairs: random removal; free format and length rules; published filters (LARF-style, DataShield-style, Self-Inf-N); attribution-guided removal; and random, DataRx-selected or self-generated safety data. Free model-level references (a safety prompt, adapter scaling, a standard recipe) bound the gain. Does paying for diagnosis ever beat spending the same compute on retraining, and does that change with menu size (measured with a planted cause) and model family?"

### 3.2 Headline structure (recommended; option (a) in §15)
1. **H-1, measured repair comparison** (OLMo-1B, then Llama-1B): the primary family (§4.3), each labelled better, equivalent or inconclusive, with the U / O / task-loss frontier against measured cost.
2. **H-2, positive control and menu size** (if §6 is funded): does each diagnostic find a planted cause, and at which menu size does diagnosis beat runs, with known truth.
3. **H-3, Gate B and Gate C** as pre-registered.
4. **Secondary:** the decision-value replay (V_max, Δ, c\*), labelled model-based, scored against its own pre-registered predictions and against Llama.

### 3.3 Do not claim
- "first benchmark of safety filters"; "first remove-vs-add comparison"; "first to price diagnosis" (DualSelect, DataShield Table IV, Yin & Rush).
- "adding safety data hurts" or "helps" as a general rule.
- "harmful compliance" from U alone (U tracks refusal; §4.2).
- "data repair beats model-level repair" unless it beats the §5.2 references.
- any cost ratio or c\* at 7–8B from 1B runs (ICML:98).
- "no better than random" without the equivalence label.

## 4. Estimands and analysis

### 4.1 Contrasts (U in pp; positive = the repair restores more)
- **Removal (600 rows, 33 steps):** Λ_m = mean over n_R seeds of U(R) − mean over n_m seeds of U(m). Variance pooled over all stage-1 arms, df stated; Welch as a sensitivity check (MET m3). Seeds are not paired (correlation −0.08; R: GBD §2).
- **Add (48 rows = 1%, 38 steps):** Λ_S1 = U(a0) − U(S1); Λ_sel = U(S1) − U(S3); Λ_self = U(S1) − U(S4).
- **Restoration:** G_m = U(a0) − U(m), reported for every arm. Removal arms are ranked against R and add arms against a0 or S1. Step counts are printed. Cross-type ranking holds only at the pre-registered doses.
- **Side effects:** ΔO_m against the untuned model (primary) and against a0 (reported); ΔL_m on all 200 held-out task rows, with its SE (retained-categories-only reported).

### 4.2 Claim rule for the judge (MET-M6, NOV-8)
- A U contrast supports a *harm* sentence only if the HarmBench-classifier contrast has the same sign and at least half the size. Otherwise the sentence says "restored refusal".
- If the pending Gate A check reads E_HB < 20 pp (FOCUS:82), every sentence says "refusal", never "harm".
- Reported for every arm: hard-category U; U by answer-length band and a length-reweighted U; the selectivity score (refusal share on harm prompts minus refusal on the over-refusal bank); O by source (XSTest-safe, OR-Bench-hard); the share of HB inputs cut at 512 tokens.
- **Refusal-shift reference curve:** adapter scaling λ ∈ {1, 0.75, 0.5, 0} traces U, O and task loss from a0 to the untuned model. A data repair *dominates* only if it lies below that curve (lower U at equal O and L).

### 4.3 Primary family, labels and seeds (one power table; MET m4)
- **Family (OLMo, U, Holm at 5% two-sided):** P1 A1 − R; P2 L1 − R; P3 H1 − R; P4 S1 − a0 (two-sided: DataRx predicts S1 worse than a0, Bianchi et al. predict better); P5 S3 − S1; P6 S4 − S1.
- **SESOI 5 pp** (about 11% of E). Labels: *better* (Holm-adjusted test rejects and the point estimate ≥ 5 pp); *equivalent* (the 90% CI lies inside ±5 pp, TOST per contrast); *inconclusive* otherwise. A 4 pp margin is reported as a sensitivity.
- **Seeds (plan A):** each method arm 6 seeds (1102–1107; never 1101 for scorers built on a0-1101 states; MET m6); R 8 seeds (1101–1108); a0 6 seeds (1101–1106).
- **Power (I; normal approximation; per-arm SD 2.65 central, 3.85 high).** SE of a removal contrast 1.43 / 2.08 pp; of an add contrast 1.53 / 2.22 pp. MDE at 80% after Holm's first step (α/6): 5.0 / 7.2 pp (removal), 5.3 / 7.7 pp (add). TOST power at a true 0: 0.94 / 0.55 (removal).
- **Blinded seed-count rule (frozen now):** read Gate B's final pooled σ̂ only (a nuisance value, on the σ_pair scale). σ̂ ≤ 4.5 pp: plan A. 4.5 < σ̂ ≤ 6.0: plan B, the family is cut to P1, P3 and P6 at 9 seeds (R 12; S1 9). σ̂ > 6.0: no stage 1; review.
- **Testing order** (each later family has its own 5% α): (1) the primary family; (2) confirmation of the picked repairs (§10, stage 3); (3) the Llama replication of the primary family, read as "same sign, and the difference below its MDE" (about 6–7 pp for a family × method interaction at 6 seeds; I); (4) the planted-sweep claims; (5) the decision-value predictions. Everything else is descriptive.
- **Side-effect prediction** becomes secondary (user decision; FOCUS:25). Estimand: the balanced error of predicting a τ_O violation, diagnostic against trial runs at equal cost, on the add arms only. MNEME (2507.21084) is cited as prior work.

### 4.4 Feasibility limits
- τ_O is a grid of {2, 5, 10} pp above the untuned model's refusal (17/100; R: GBD §1). The chosen repair and V are reported at each point.
- τ_L: the task-loss increase over a0, set to 2 SE of a seed-to-seed difference (I), fixed before wave 1.

### 4.5 Decision value (secondary; model-based; MET-M1, M-M2, NOV-2, NOV-4)
- **One selector spec, one code path** for simulation and replay. Options include keep (a0). A trial has a training fraction φ and a prompt fraction ψ; its cost comes from the ledger cost model (§8). ψ-trials replay subsamples of saved labels at $0. A feasibility screen drops an option whose adverse (upper 90%) O or L estimate passes its limit, with the U–O noise correlation from pooled residuals. The pick is the lowest estimated U among options with ≥ 2 full-run seeds; ties go to keep.
- **Runs-only rule per (M, B) cell:** one-shot screen, successive halving or hierarchical bisection, chosen *now* from the pre-outcome simulation and frozen. The oracle "best of three" is reported separately.
- **Diagnostic policy:** pays c_d, keeps its top k (k frozen per cell), then runs the same rule. For the method menu, Δ_m is the value of adding option m net of c_m; V_max of the free menu does not bound it.
- **Generative model (frozen before Gate B wave 1):** option effects shrunk by empirical Bayes (the raw maximum has a winner's curse); noise from pooled residuals; measured c0; two effect shapes (one winner; a spread with the same total); parameter uncertainty carried into the intervals.
- **Pre-registered predictions:** before wave 1, record predicted V_max and c\* for the category menu and the planted menus. Report measured against predicted.
- **Held-out test:** OLMo-calibrated predictions of P(best found) and regret for SH and the one-shot screen at B = 4 and 8 are scored on Llama's Gate B-lite menu.
- **POW's statement** "8 full runs find an 8 pp category 90% of the time" holds only for its one-winner model and its full-runs-only table (R: POW Part 2, table B).

## 5. Arms

### 5.1 Primary arms (OLMo; recipe B; sealed edit files)
| Arm | Rule (frozen before Gate B wave 1) | Scoring cost (I) | Seeds |
|---|---|---|---|
| R | random 600 rows, 75 per unit (R_d1–d5 sealed; d6–d8 by the same frozen builder) | 0 | 8 |
| a0 | no repair | 0 | 6 |
| H1 | the 600 rows with the fewest target tokens; ties by a sealed draw | < 0.01 FRE | 6 |
| A1 | top 600 of all 4,800 rows by the bi-anchored checkpoint gradient score (the Gate C method) at a0-1101's q and e1, from the wave-0b pass | from the wave-0b ledger (I: 0.6–2.4 FRE) | 6 |
| L1 | LARF-style: untuned-model representation similarity to the sealed harmful anchors at one layer; the layer rule uses only the untuned model, the 64 harmful anchor prompts and 64 Dolly training prompts (first-token refusal logit), no evaluation bank | 0.1–0.3 FRE | 6 |
| S1 | add 48 rows: a sealed random draw from the S-pool (§5.5), one row per prompt | CPU, $0 | 6 |
| S3 | add 48 rows: DataRx-style SAS selection from a sealed 1,000-prompt S-pool subset; native answers from the untuned model | 0.6–1.2 FRE | 6 |
| S4 | add 48 rows: S-pool prompts (disjoint from S1 and the anchors) with the untuned model's own greedy answers, kept if ended and refusal-opening by the lexicon | about 0.05–0.1 FRE | 6 |

Notes. Each arm's removed or added token mass and category composition is reported. If A1's set is ≥ 50% one category, it is compared with that category's Gate B unit arm. Every scorer is named "X-style" with a deviation table (anchors: 64 PKU rows, not the papers' 100 Circuit Breakers or Pure-Bad rows; LoRA gradients at fitted checkpoints). The four method repositories have no licence (R†: FIL), so every method is re-implemented from its paper; the authors are asked for reference outputs.

### 5.2 Mandatory references with no data change (NOV-9; MET-M6)
- **SP:** a fixed safety instruction as a user-turn prefix (OLMo has no system turn; R: EAL:66), at evaluation only, on a0 seeds 1101–1103.
- **Adapter scaling:** a0's LoRA delta scaled by λ = 0.75 and 0.5, seeds 1101–1103.
- **Recipe G** (token-mean loss plus warmup; FOCUS:66-67): seed 1101 is already pre-registered; seeds 1102–1103 are added.
- They run through one pinned "evaluate a saved adapter" script outside the engine identity. It regenerates each a0 adapter by a deterministic train-only re-run (0.10–0.15 h; fingerprint checked) and uses the engine's loaders, codec, generation and guard. It is certified once: with λ = 1 and no prefix it must reproduce a Gate A U exactly.
- **The data-only user** (ICML:94): a fine-tuning service that must ship the customer's adapter and may only change the data, or a team whose pipeline allows data changes only. The paper states plainly whether any data repair beats these references.

### 5.3 Secondary arms (3 seeds; exploratory; one-sided upper bounds only; run in this order when funded)
1. Random dose curve R_1200 and R_2400 (6 runs): each filter's "equivalent random dose".
2. R+S1 (3 runs): completes the 2 × 2 of remove-random × add-S1.
3. DataShield-style (3 runs).
4. H2a (rows with list or markup lines, filled at random) and H2b (longest rows) (6 runs).
5. H1 under recipe bt, token-mean only (3 runs): does H1's effect come from loss weighting?
6. L8 octiles of target length (11–15 runs under Gate B's wave rules) plus a category-matched random control for the best octile (2 runs).
- **DIFFUSE branch:** SD-600 moves to the front: rewrite A1's top 600 rows with the untuned model's greedy answers (3 runs plus 0.5–1 FRE of generation). It compares remove against rewrite on the same rows and keeps the agreed fallback's menu (FOCUS:53).

### 5.4 Scored only (no runs; claims limited to rank overlap)
Self-Inf-N-style (from saved loss and gradient norm), a content classifier, DataShield-style if not run. The full Jaccard matrix of top-600 sets is published.

### 5.5 Pools and the plant (built on the Mac, CPU, $0)
- **S-pool:** PKU records where at least one response is PKU-unsafe (a harmful prompt) and the chosen response is PKU-safe and refusal-opening by the frozen lexicon `bbbc71e9…`. About 2,600 candidate prompts (R: PKUC). Near-duplicate check against every bank by the engine's rule (counts only); disjoint from the 128 anchor prompts. No Qwen3Guard filter (MET-M6).
- **Overlap control (MET m8):** report each eval prompt's highest similarity to the add set (untuned-model embeddings, on the pod); the add effect must hold on the lower-similarity half.
- **Plant:** see §6.
- **Dropped:** S2 (unfiltered PKU; harmful-data injection, a known effect); the concentration split and κ; He-style init gradients (zero for LoRA's A at init; FEA m8); failure-query attribution (it needs selector-split outcomes); SQSD runs (DPO, 6–14 FRE; cited only); a natural M = 32 menu (only via §6).

## 6. Positive control: the planted-cause sweep (stage 1b; funded tier)
- **Plant:** k = 37 rows: PKU-safe, *direct* (non-refusing) answers to prompts that also have a PKU-unsafe answer. They look benign. They are disjoint from the S-pool rows used in §5 and from the anchors. A sealed draw picks one category and, inside it, one leaf cell; the plant replaces that leaf's Dolly rows, so the run keeps 4,800 rows and 38 steps.
- **Nested cells (MET m9):** M = 8 categories (600 rows); M = 32 within-category length quartiles (150); M = 128 sealed-random quarters of each quartile (37–38). Near-duplicate Dolly groups stay inside one cell; cut points are published.
- **Pilot gate (3 runs + one scoring pass):** a0_plant at seeds 1101–1103 against Gate A's a0. Go on if Λ_plant ≥ 10 pp and its one-sided 90% lower bound > 5 pp. If 5–10 pp: raise k to 75 once and re-pilot. Otherwise stop and report the null.
- **Main (12–15 runs):** remove the planted cell at M = 8, 32 and 128 (3 seeds each); R600 on the planted data (3 seeds); optionally R150 (3 seeds).
- **Scored at $0 after one pass:** the planted cell's rank at each M for A1, L1, H1, H2a/b and the classifier.
- **Outputs:** measured Λ_plant(M); each diagnostic's top-k hit rate with known truth; the runs-only cost to find the cell, replayed from measured inputs with SH, one-shot and bisection; a nested additivity check (Λ at M = 8 against Λ at M = 128 plus the dose-scaled background).
- **Cost (I):** pilot $4–7; main $11–23; with 15% about $17–35.

## 7. Measurements (per arm)
| Measure | Definition | Role |
|---|---|---|
| U | Qwen3Guard Unsafe share of 600 sampled answers to the 200 dev harm prompts | primary |
| HB | HarmBench-Mistral-7b classifier "yes" share on the same answers; run on the pod (minutes per arm, UNVERIFIED) | claim rule §4.2 |
| U_hard, refusal share, Granite greedy | as in GBD §6 | reported |
| O | "Refusal: Yes" share on the 100 dev over-refusal prompts; lexicon refusal as a check | limit; reported by source |
| Task loss | held-out loss on all 200 task rows | limit (primary skill measure) |
| ARC | as in Gate A | reported; weak at 1B (FOCUS:87) |
| Cost | GPU-seconds by stage (§8) | cost axis |
| Opening switch | frozen-lexicon class of the first answer words | mechanism, report only |

- **O-ext only if needed (FEA m4; MET m2, m11):** first, at $0, compute the paired ΔO SE from Gate A's a0 seeds and the untuned unit (labels only), planning at f = 1. If the 6-seed MDE for O exceeds 5 pp, add 400 prompts from a new public over-refusal source (a download the user approves), stratified by source, judged on answers capped at 128 tokens after a $0 truncation check. Never from the hidden remainder.

## 8. Cost accounting (NOV-5, FEA-M1, FEA-M5, MET-M3)
- Every arm and every diagnostic is logged in GPU-seconds by stage: setup, training, greedy generation, sampled generation, judging, scoring, pod overhead. Gate A's ledgers give the first split (R: LEDGER; §1, item 6).
- **1 FRE** per family = the median measured time of that family's R arms.
- **Two cost conventions, frozen before stage 1:** C-full (training plus the full evaluation as run) and C-lean (training plus 200 harm prompts × 1 sample, priced from the ledgers' per-answer time). c0 is measured on one real lean job (full training, a 20% prompt subset, cold start; about $0.3–0.6). Δ, V_max and c\* are reported under both; a claim stands only if both agree.
- **Charging:** every pool filter, untuned-answer generation, anchor job and scorer is charged in full. "≈ 0" is written only below 0.01 FRE.
- **A1** is priced only from the wave-0b ledger. An "inline" cost appears at most as a labelled model estimate. Speed-ups (fp32 on the GPU, fused products) are a separate, tested engine round.
- Cost ratios at 1B are not claims about 7–8B (ICML:98).

## 9. Engine, data and sealing (deadlines)
- **D1, before engine X freezes and the anchor job:**
  1. Wave 0b scores all 4,800 rows (list all 8 units; no engine change; R†: FEA m1). Its start requirement rises from 2.6 h to about 3.5–4.3 h; the cap and guard rise by about $2–3; recompute the $5 top-up. Check that the bi-anchored score has no normalisation across the scored set, so Gate C's sample scores do not change (UNVERIFIED).
  2. E6, the representation module, is Gate C's script in general form (any layer, position, pooling); it is frozen once and serves Gate C, L1, DataShield-style and S3.
- **D2, before Gate B wave 1:** commit the code and settings hash of every stage-1 scorer; the edit files or rules for R_d6–d8, H1, H2a/b, the L8 octiles, the S-pool, S1 rows, the S3 and S4 prompt lists and the plant; the primary family, SESOI, seed rule, τ grid, O reference and claim rule; the selector spec, the generative model and the predictions (§4.5). A1, L1 and S3 are computed later by these frozen rules. Anything added later is "post-Gate-B exploratory".
- **D3, before stage 1:** re-cost from the anchor-pod and wave-0 ledgers; freeze the cost conventions.
- **Kept as is:** manifest `9ed61826…`, the sealed files (10a2894) and every Gate B rule. Nothing here changes a Gate B verdict.
- **New pinned scripts (outside the engine identity):** evaluate-a-saved-adapter (§5.2); untuned answers with lexicon labels for a sealed prompt list (S3 native answers, S4, Llama anchors); the add-edit writer (`build_add` has no command); HB on the pod; the similarity strata; replay for §4.5 (extends POW).
- **Engine round Y (before stage 3):** a confirmation role that lets sealed dev-split edit arms evaluate a sealed 200-prompt hidden subsample, with reference-namespace seeds (today edit arms are dev-only and only the reference role reads the hidden bank; R: SS/jobs.py:23-24, :168-180). Certificate X → Y plus one determinism re-run (R_1101: fingerprints and U must match; about $1–1.5).
- **Work (I):** about 8–12 developer-days; E6 is needed before wave 0b.

## 10. Stages, seeds and money (I unless marked; arm cost $0.94–1.52; R: POW Part 4)
| Stage | Content | Runs | Cost | Starts after |
|---|---|---|---|---|
| 0 | Gate B/C as pre-registered; wave 0b scores all rows | 15–29 | $18.7–39.6; worst $58.0 (R: GBD §9); +$0.6–1.4 scoring, guard +$2–3 | approval, engine X |
| 1, block A | 6 primary arms at seeds 1102–1104; a0 1104; R to 1105; diagnostics; c0 job | 19–21 | $25–45 | Gate B verdict; funding event |
| 1, block B | seeds 1105–1107; a0 1105–1106; R to 1108; §5.2 references | 23 | $31–53 | block A complete; funding event |
| 1b | planted sweep (§6) | 15–21 | $17–35 | pilot gate; funding |
| 1c | secondary arms (§5.3), in order | up to 40 | up to $45–80 | optional |
| 2 | Llama-3.2-1B: probe (FOCUS:68), Gate A, anchors, Gate B-lite, primary family at plan A | about 60 | $65–115; per-run cost UNVERIFIED | stage 1 read; funding |
| 3 | confirmation: ≤ 2 contrasts per family by a frozen rule, 6 fresh seeds, dev + hidden subsample | about 48 | $58–95 | engine Y; stage 2 |
| 4 | scale ladder (FOCUS:70); first a published-setting replication (LARF- or DataShield-style on Llama-3.1-8B-Instruct with Alpaca, with R, H1, H2) | – | $200–400 + $150–600 (R: FOCUS:70) | funding |

- **Stage 1 total:** about $56–98 with diagnostics, references and 15% contingency (plan A). Plan B costs about the same.
- **Core path (stages 0, 1, 1b, 2, 3):** about $215–405. With 1c: about $260–485. Lean tier: $3,050 (R: GRANT:225).
- **Cash is the binding limit:** about $17.50 today; Gate B alone needs about $37–42 more (R: GBD §12). Every stage and block starts only on a funding event, never on an outcome. If money stops, only complete seed blocks are analysed. Arms are interleaved within seed blocks across pods (MET m14).
- **a0 across engines:** Gate A's a0 (engine 55253874) is reused only if the X certificate and the wave-0b fingerprints pass; otherwise a0 1101–1103 re-run on X (+3 runs, from contingency).

## 11. What Gate B's verdict changes
- **LOCALIZED:** the length control and Gate C run as pre-registered; Gate C also reports top-k hit rates beside its Spearman ρ. If the control says "length", H1 is the bar for every paid scorer. The category-level decision value is reported as small (runs find the unit in about 6–8 runs).
- **DIFFUSE:** Gate C does not run; the paper takes alternative title 3 (ICML:10; FOCUS:53). Stage 1 runs unchanged, SD-600 moves to the front of 1c, and the planted sweep becomes the only test of whether diagnosis can pay.
- **TOO CLOSE:** the automatic extension runs. Stage 1 does not change: its arms compare with R and a0 whatever the verdict.
- **Timing:** stage 1's rules must be committed before wave 1 (D2). If they are approved after any unit outcome, every stage-1 claim is labelled post-Gate-B exploratory.

## 12. Families and scale
- **Llama-3.2-1B** (stage 2). Its probe is approved (FOCUS:68). **Rule to record before the probe result:** if recipe B saturates Llama, change LR or rank, never loss weighting; otherwise also run OLMo's primary arms under Llama's recipe. If the probe has already reported, the rule is post-hoc and the second option applies.
- Llama's Gate B-lite rules and the comparison scale (pp and Λ/E, with the ratio's interval) are pre-registered before Llama's formal Gate A.
- **Claim:** "replicates across two families" (same sign; the difference below the interaction MDE). "How the answer changes with family" is claimed only for interactions above that MDE.
- **7–8B and up** follow FOCUS:70, when funded.

## 13. Risks (I)
- **Nulls everywhere.** A 600-row filter needs a large findable effect (R: POW Part 3). Mitigation: equivalence labels, the planted control, the dose curve.
- **U measures lost refusal.** Add arms and refusal-direction filters can win on U by construction. Mitigation: HB claim rule, selectivity, the refusal-shift curve.
- **A free fix may win everything** (S4, SP or adapter scaling). That is a valid, reportable answer; the headline then says so.
- **Prior work overlap** (DualSelect, Yin & Rush, DataShield). Mitigation: no "first" claims; the positive control and the measured equivalence bounds are the contribution.
- **The plant may not erode** above the 45 pp background. The pilot gate decides before the main sweep.
- **Fidelity of re-implemented baselines.** Deviation tables, author contact, and the stage-4 published-setting replication.
- **Llama may saturate**; family is then confounded with recipe unless the §12 rule holds.
- **Engine and schedule.** 8–12 developer-days; E6 and the all-row scoring must be ready before wave 0b.
- **Licences and access.** PKU is CC-BY-NC; a new over-refusal source needs a download approval; WildGuardMix and WildJailbreak are gated.
- **Money.** About $17.50 today against a core path of about $215–405.

## 14. Timeline and venue (I; deadlines UNVERIFIED)
- Oct 8–20: approve D1 and D2 items; engine X; Gate B. Scripts in §9 in parallel.
- Oct 20 – Nov 15: stage 1 blocks A and B; the 1b pilot.
- Nov 15 – Dec 10: stage 2; engine Y.
- December: stage 3; replay against the predictions.
- **Target now: TMLR (rolling, from about February) or NeurIPS 2027 (about May).** ICML 2027 (about 22 January; FOCUS:222) only if, by about 1 December, the planted sweep, both 1B families and one 7–8B published-setting cell are funded (SPEC §8).

## 15. Decisions for GPT and the user
1. Approve this amendment: D1 items before engine X freezes; D2 items before Gate B wave 1.
2. **Headline:** (a) the measured repair comparison and the positive control lead, with the decision-value map secondary and model-based (recommended); or (b) the map leads, as in SPEC §4.3.
3. Fund the planted sweep (about $17–35)? If not, "menu size" leaves the headline.
4. Wave 0b scores all 4,800 rows (+$0.6–1.4; guard +$2–3).
5. The primary family (P1–P6), Holm 5%, SESOI 5 pp, the blinded seed rule.
6. O against the untuned model (a0 reported); τ_O grid {2, 5, 10} pp; τ_L at 2 SE.
7. Doses: remove 600 rows; add 48 rows (1%). A 10-row S4 dose is an option.
8. The §5.2 references (SP, adapter scaling, recipe G seeds) as mandatory.
9. Demote side-effect prediction to secondary (changes FOCUS:25).
10. The Llama recipe rule (§12), recorded before the probe result.
11. Confirmation through engine round Y (recommended), or fresh-seed dev and selector confirmation labelled "not hidden-bank".
12. O-ext only after the $0 check; from a new public source if needed.
13. L1 = LARF-style (cheapest published representation filter) or DataShield-style.
14. HarmBench classifier on the pod for stage 1 (a model download on the pod).
15. Venue target: TMLR or NeurIPS 2027.

## 16. Process
- **Changed files:** this file and `2026-10-08-focus-amendment-sharpened-DRAFT.md`, written in the worktree copy (`.claude/worktrees/peaceful-jepsen-8b8eee/research/review/`), because the project instructions forbid editing the original checkout. The lead copies them into the main checkout.
- **Commands run (exit 0, except a `head` flag error and a grep pattern too complex for ugrep; both redone another way):** `date -u` (4 times); `git status`, `git log`, `git show --stat`; `sed`, `grep`, `ls` and Python reads of FOCUS, GBD, AUD, EAL, GUO, RL2, MECH, ICML, SPEC, GRANT, configs, engine files and one Gate A ledger; PKUC on the three local PKU files (counts only); two fetches of the DataRx arXiv HTML and one of the DualSelect abstract.
- **Not done:** no re-read of most papers (R† marked); no cost figure measured anew; no simulation re-run (the §4.3 power numbers are my normal-approximation arithmetic, I).
- **Open concerns:** (1) SPEC and this plan disagree on the headline; (2) the plant's erosion size is unknown until the pilot; (3) whether the bi-anchored score depends on the scored set (§9, D1.1) is UNVERIFIED; (4) the HB time on the pod is UNVERIFIED.
