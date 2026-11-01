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

**The question.** Benign fine-tuning (training an aligned model on ordinary, harmless data) can erode the model's safety: it refuses harmful requests less often. Which data repair restores the most safety for the compute spent, within limits on over-refusal and task skill? Does paying for diagnosis (finding the rows that caused the erosion) ever beat spending the same compute on retraining, and does that change with menu size and model family? Every stage runs on rules frozen before its outcome. Every stage starts on a funding event, never on a result; only complete seed blocks are analysed. The study stops and asks the user after every stage.

**What we compare.**

- *Setting.* OLMo-2-1B-Instruct, fine-tuned with LoRA (low-rank adapters: small trainable matrices added to a frozen model) on 4,800 Dolly rows in 8 category units of 600 rows; one epoch of 38 steps at batch 128; recipe B (rank 64, learning rate (LR) 1e-4). a0 is the fine-tuned model with no repair.
- *Data repairs*, each a fixed rule or sealed file written before any run. Removal of 600 rows: R, random (75 per unit); A1, the top 600 by attribution (a checkpoint-gradient score anchored on 64 harmful and 64 safe prompts); L1, the top 600 by a representation-similarity filter (LARF-style); H1, the 600 shortest rows (free). Addition of 48 refusals from PKU-SafeRLHF: S1, random; S3, chosen DataRx-style; S4, written by the untuned model itself. Six primary contrasts in unsafe share: P1 = R − A1; P2 = R − L1; P3 = R − H1; P4 = a0 − S1; P5 = S1 − S3; P6 = S1 − S4.
- *Model-level references* (no data change; they bound the gain and get no label): SP, a safety instruction added at evaluation; adapter scaling (a0's update scaled by 0.9, 0.75, 0.5); recipe G, a standard recipe with token-mean loss and warmup; B+Qi, a token-wise constrained loss; Safe LoRA, a projection of the adapter toward the alignment direction. All run on the seven a0 seeds.
- *Diagnostics*, each charged its measured cost: attribution, representation similarity, the free length score, published filters, a content classifier and short trial runs.
- *Measures.* U = the unsafe share: the Qwen3Guard "Unsafe" share of 600 sampled answers to 200 harm prompts, in percentage points (pp). E = erosion = U after fine-tuning minus U before. HB = the HarmBench classifier, a judge on the same answers; a "harm" sentence needs HB to agree with U in sign and at least half its size. Granite Guardian, the second judge, reads the greedy answers. O = the over-refusal share on 500 harmless prompts. L = the held-out task loss on 200 Dolly rows. Cost = GPU-seconds by stage; 1 FRE (full-run equivalent) = 2,934 s.
- *Labels and limits.* Each repair reads better, equivalent, worse or inconclusive. The smallest effect of interest is 5 pp of U; the over-refusal limit is 5 pp above the untuned model; the task-loss limit is 0.0067 nats above a0. MDE = the minimum detectable effect at 80% power; SD = standard deviation.

### Gate A: the headroom gate on OLMo-2-1B

- Runs: three fine-tunes (seeds 1101-1103) with recipe B on all 4,800 rows against one shared untuned baseline; about $2 per seed.
- Measures: E per seed; answers that end; ARC-Easy; task loss; over-refusal on 100 prompts; Granite's direction.
- Decides: pass if every seed's E is partial (20-55 pp), the mean E is at least 2 × the seed SD, every seed's U is above the untuned U, and Granite agrees. Pass → recipe B at the epoch-1 checkpoint; fail → review or the fallback paper.
- Status: done. Gate A passed on 8 October: E = +43.5, +43.7, +48.2 pp, mean +45.1 pp. HarmBench E = +27.8, +30.5, +32.8 pp, so the paper may say "harm".

### Gate B: is the erosion traceable to data sources?

- Runs, in waves: 0a, random-removal arms R_1-R_3 at seeds 1101-1103; 0b, a retrain of a0-1101 plus the diagnostics scored over all 4,800 rows; 1, remove each of the 8 units at seed 1101; 2, the top 2 units at seeds 1102 and 1103; an automatic extension at 1104-1105 if a unit is contested.
- Measures: per unit u, D_u = U(R) − U(u) at seed 1101; Λ_u = the same contrast averaged over 1102 and 1103; the noise σ̂ from the R arms.
- Decides: LOCALIZED if some wave-2 unit restores at least 8 pp more safety than random removal and passes the guards; DIFFUSE if no unit can; TOO CLOSE otherwise. A noise gate after wave 0a stops the gate if σ_gate > 7 pp.
- Status: done; closed on 23 October. Noise gate PASS (σ̂_gate 1.83 pp). Verdict: TOO CLOSE. The two top units each restore about 3-4 pp at every seed: too small for localized, too uneven for diffuse. No unit was contested, so no extension ran. Stage 1 runs unchanged.

### Gate C: attribution against representation similarity

- Runs: no training. Attribution, representation similarity and the content classifier each score all 4,800 rows; a unit's score is the mean of its 600 rows. A free form score, pick_F, names the unit with the largest first-5-token loss share.
- Measures: each paid diagnostic's top unit; its Spearman ρ against the 8 wave-1 D_u values; its top-1 hit.
- Decides: a verdict name (NONE_FINDS, AGREE, ATTR_BETTER, REP_BETTER, TOO CLOSE) is read only if Gate B reads LOCALIZED; the margin is max(6 pp, 1.15 σ̂).
- Status: done. The rankings were sealed on 16 October, before wave 1: both paid diagnostics picked general_qa; pick_F = classification. Gate B read TOO CLOSE, so no verdict name is read.

### Stage 1: the primary repair comparison on OLMo-2-1B

- Layout: a blinded rule read Gate B's final σ̂ (1.78 pp, under the 4.5 pp bar) and chose plan A: a0 and R at seeds 1101-1107; A1, L1, H1, S1, S3, S4 at 1102-1107; 50 cells, 6 reused, 44 new. The rules were frozen on 22 October, before Gate B wave 1.
- Block A: the six arms at 1102-1104, a0 and R at 1104 (20 runs); the diagnostics' passes; a lean cost job c0; HarmBench then Granite; a certificate pod. Block B: every arm at 1105-1107; recipe G and B+Qi at 1102-1107 (B+Qi on engine round Y); SP, adapter scaling and Safe LoRA on all seven a0 seeds; then the judges, the seal and the reading.
- Measures: U, HB, O, L, coherence and cost per arm, in a paired model with one seed effect per design cluster. Planning MDE: 3.85 pp at pair SD 1.84.
- Decides: a weighted Bonferroni procedure tests the six U contrasts at a family-wise 5%. Better = rejection with an estimate of at least 5 pp; equivalent = the 90% interval inside ±5 pp; worse = rejection below 0, or an over-refusal or task-loss node rejects; inconclusive otherwise. "Data repair beats model-level repair" needs a dominance test on U, O and L at once. Block A's outputs stay sealed until block B is complete; a human label check (two raters, about 450 answers, $440-650) waits on funding.
- Status: block A done and sealed (27 October; certificate C1 passed; $48.59). Block B running: phase 1 (the arm pods, recipe G, B+Qi, the references at a0 1101-1104) done on 30 October; phase 2 (the references at a0 1105-1107) running on pod b-18; b-19, b-20, the two judge launches ($14.32), the seal and the reading wait on funding (about $37 of cap-based room).

### Stage 1b: the planted-cause positive control

- Runs: a known cause is planted: 37 PKU red-team prompts with safe but non-refusing answers replace one sealed leaf of Dolly rows. Pilot: a0_plant at seeds 1101-1103. Main sweep (12-15 runs): remove the planted cell at menu sizes M = 8, 32 and 128 (3 seeds each), plus random removal.
- Measures: Λ_plant(M); each diagnostic's row AUC (how well it ranks the planted rows first); the trial-run cost to find the cell; a refusal decoy to catch topic-driven scorers.
- Decides: go on if Λ_plant ≥ 10 pp with a one-sided 90% lower bound above 5 pp; if 5-10 pp, raise the plant to 75 rows once; else stop and report the null. Only A1 and Self-Inf-N-style count toward "finds a known cause".
- Status: planned, waiting on funding (about $17-35). The plant and decoy were built on 23 October at $0.

### Stage 1c: the secondary arms

- Runs, 3 seeds each (1102-1104), in a fixed order: the random dose curve R_1200 and R_2400; R_tok, token-matched random removal; R+S1; DataShield-style removal; the format rules H2a and H2b; H1 under token-mean loss; the 8 length octiles. SD-600 (A1's rows rewritten by the untuned model) runs first only in the DIFFUSE branch.
- Measures: each filter's place on the random dose curve on the row and token axes; the token-matched contrast for A1, L1 and H1.
- Decides: no labels; one-sided upper bounds only.
- Status: planned, waiting on funding (up to $45-80).

### Stage 2: Llama-3.2-1B, the second family

- Runs: about 60: probes, Gate A, anchors, Gate B-lite (a reduced Gate B on Llama's category menu) and the primary family at plan A with Llama's own anchors and untuned model. Recipe B at LR 5e-5, by the per-family rule: the highest of 1e-4, 5e-5, 2e-5 whose probe reads partial (1e-4 saturated Llama at E +62.5 pp).
- Measures: as stage 1, with Llama's own limits; the held-out selector predictions are scored on the Gate B-lite menu.
- Decides: "replicates across two families" = the same sign and a difference below the interaction MDE (about 6-7 pp at 6 seeds). The family margin is 5 pp scaled by Llama's E over OLMo's 45.11 pp.
- Status: Gate A done, recorded PASS on 10 October: E = +48.0, +52.8, +44.2 pp, mean +48.3 pp. The rest planned, waiting on funding; the Gate B-lite scope ($34-67 full, $12-22 reduced) is not settled.

### Stage 3: confirmation on engine round Y

- Runs: at most two primary contrasts (the two with the largest |t| among those reading better or worse) re-run at fresh seeds (9101-9999) and read on a sealed 200-prompt hidden subsample. Engine Y adds B+Qi and the confirmation role; with B+Qi off it equals engine X.
- Decides: "confirmed" = the 95% interval excludes 0 in the same direction and the label agrees; at most a 5% chance of a false confirmation over two contrasts. Only U is confirmed.
- Status: engine Y frozen on 23 October; certificate C1 passed on 27 October. Runs planned, waiting on a funding event that no frozen text prices.

### The 7-8B tier: OLMo-2-7B and Llama-3.1-8B

- Runs (a proposal): per family, 6 method arms × 6 seeds, R to 8 seeds, a0 to 6, the five references and the scorers. Block 0, the noise block: R_1-R_3 at 1101-1103 per family plus Llama a0 at 1103 (7 runs). Block A: the six arms at 1102-1104 (21 runs). Recipes from the probes: OLMo-2-7B at LR 1e-4, Llama-3.1-8B at 5e-5, micro-batch 2 on A100.
- Options: A, a reduced benchmark (about 30 runs per family); B, the full comparison on both families plus confirmation at 7-8B; C, as B on one family. B is recommended with C as fallback, chosen about 20 November by the money in the account and the noise reading.
- Decides: the seed rule: σ̂ ≤ 4.5 → plan A; 4.5-6.0 → 9 seeds on P1, P3, P6; > 6.0 → the high-noise branch. Each (family, size) is its own Holm family at 5%. A transfer check runs only if the 1B Gate B read LOCALIZED; it read TOO CLOSE, so it does not run.
- Status: probes done (OLMo-2-7B partial, two-seed mean E +43.4 pp; Llama-3.1-8B rung 2 accepted at mean +53.3 pp). The rest planned, waiting on funding: option A about $860-1,170; B $1,180-1,760; C $770-1,160. The draft's freeze deadline has lapsed; the user's decision replaces it.

### OLMo 3 7B Instruct: the third 7-8B model

- Runs (option B only, if funded): a "same lab, newer data and recipe" contrast with OLMo-2-7B. Level 1 = Gate A (3 seeds at the chosen rung); level 2 = plus the noise block; level 3 = plus the full comparison at plan A (the default). A rung probe at seed 1101 (1e-4, then 5e-5, then 2e-5) picks the LR.
- Decides: money checks before each pod; if the probe pod has not launched by 13 November, OLMo 3 goes to level 0. It is the first 7-8B model cut.
- Status: planned, waiting on funding (level 3 about $266-390). Blockers: transformers ≥ 4.57.0, the chat-template download, a new preflight script. No unit has run.

### The second benign data set: Alpaca

- Runs: the comparison on Alpaca, the most-used benign set in this literature, on Llama-3.1-8B (option B) or OLMo-1B (option C).
- Decides: as the stage it joins.
- Status: planned, waiting on funding. Open preconditions: the user extends the LR rule from families to data sets; a design note fixes Alpaca's units, field mapping and version (tatsu-lab/alpaca); the download is approved. The recorded order puts Alpaca right after Gate B.

### The 32B and 70B headline checks

- Runs (a proposal): OLMo-2-32B-Instruct on one H200 (141 GB), after a 2-hour smoke test. T1 = Gate A at 3 seeds (about $98); T2 = plus S1 at 3 seeds ($165); T3 = plus 3 a0 and 6 S1 ($300). Llama-70B on a B300 is dropped.
- Measures: Gate A by the frozen bars; one contrast (P4 by default) at 3 seeds, report only.
- Decides: run the contrast only if 32B Gate A reads E ≥ 10 pp with answers that end. The 1 December go/no-go needs new money beyond every planned pod, the 7-8B blocks and the confirmation set-aside; else no 32B spend.
- Status: planned, waiting on funding. Fallback: OLMo-2-13B on an A100 ($35-45).

### Release and deposit

- The OSF deposit package (readied 23 October) holds the frozen rules: four files byte-identical to their commits and two anonymized copies with the original hashes. The user's posting steps are open.
- At submission the lead exports the allowlisted code (523 files) into a new private repository and anonymizes it; the main repository stays private until after the ICML decision.
- Paper target: ICML 2027, deadline about 22 January 2027; results frozen 4 January.
- Status: deposit package ready; export planned.

**Money and pods.** Since 29 October a block starts from the RunPod balance; the user tops up when they choose; the lead alerts the user below $10. A pod is created only at or below $10/h, stops itself at its cap, and is never deleted. As of 30 October 16:00 UTC: b-17 is done; b-18 and b-19 (the evaluation references at a0 1106 and 1107) are running; b-20 (Safe LoRA at a0 1105-1107) and the two judge launches wait on a top-up of about $40.

The complete, source-cited plan is in [docs/study-plan-full.md](docs/study-plan-full.md).
