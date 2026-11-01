# Mock ICML 2027 review A: statistics and experimental design

- **Paper:** "Repairing Safety After Benign Fine-Tuning: A Compute-Matched Comparison of Data Repairs" (anonymous, revision 6; `writing/paper/icml/main.pdf`).
- **Reviewer stance:** a demanding reviewer whose expertise is statistics and experimental design for ML. Read-only mock review.
- **Clock:** `date -u` gave Fri 16 Oct 2026 21:53 UTC before this review was started (17 Oct local).
- **What was read:** the body up to the Impact Statement, Appendix A (blind human read) and Appendix C (design details). I read Appendix B (the editor's notes) only after this review was drafted, and used it only for the last section.
- **How this was reviewed:** §5 (Results) is a placeholder, so I review the design as a registered report (Stage-1 style). I say below how results would change the score.

All power numbers in this review are my own illustrative calculations under assumptions that I state. They are not the authors' numbers. The anchor I use is the central planning noise in App. C.1: a seed-pair SD of 3.75 pp, which gives a per-arm seed SD of about 2.65 pp if arms are independent. I use the pooled df of about 42 that the stage-1 plan implies (50 seeds across 8 arms).

---

## 1. Summary

The paper pre-specifies a comparison of six data repairs for safety erosion after a benign LoRA fine-tune. The setting is OLMo-2-1B-Instruct, 4,800 Dolly rows, a constant-LR "recipe B" and one epoch. There are three removals of 600 rows each (attribution A1, a LARF-style filter L1 and a free shortest-answer rule H1), compared with random removal. There are three additions of 48 refusal rows each (random S1, DataRx-style S3 and self-generated S4), compared with no repair or with S1. Each arm runs at six seeds, and random removal runs at eight.

The primary endpoint is a Qwen3Guard "Unsafe" rate U on 200 prompts × 3 samples. Each of six contrasts gets a label (better, equivalent within ±5 pp by TOST at 90%, worse, or inconclusive) after a Holm correction over the six. Over-refusal and held-out task loss act as feasibility limits, and cost is reported in "full-run equivalents".

A data repair "dominates" only if it beats five references that change no data:
- a test-time safety prompt;
- an adapter-scaling curve;
- Safe LoRA;
- a standard recipe G;
- Qi et al.'s constrained objective.

Around this comparison sit three gates:
- **Gate A:** erosion is beyond seed noise and inside a 20–55 pp window.
- **Gate B:** is erosion localized in one of the 8 Dolly categories?
- **Gate C:** which diagnostic picks the category? This gate is now degenerate, because both diagnostics picked the same category.

Further parts:
- a funding-contingent positive control with a planted 37-row cause;
- a model-based "value of diagnosis" analysis, whose predictions are scored on a second family (Llama-3.2-1B) at a "matched erosion dose";
- a funding-gated 7–8B replication.

All findings are placeholders.

## 2. Strengths

1. **The pre-registration culture is real, not decoration.** Several parts are done before the outcomes they judge:
   - diagnostic rankings are sealed before the category runs;
   - edit files are hashed;
   - seed blocks are fixed before any outcome, and only complete blocks are analysed;
   - the adaptation rules (noise gate, family shrinkage) read only blinded noise;
   - the protocol lists every value seen before the freeze;
   - "too close to call" is an explicit outcome.

   Few ML-safety papers do any of this.
2. **Gate B is a well-built two-stage design.** It screens 8 units at one seed and confirms the top units on independent seeds (1102, 1103). Λ_u excludes the screening seed, so the winner's curse does not enter the confirmatory estimate. Bonferroni over the m confirmed units is then valid. The operating characteristics were simulated (App. C.1: 52/83/96% detection at 8/10/12 pp, false LOCALIZED 0.2–2.7%), and the paper says plainly that DIFFUSE means "no cause above about 8 pp", not "no cause".
3. **The comparators are the right ones.** Random removal of the same size controls for the smaller training dose, which most removal papers omit. The adapter-scaling curve is an excellent "just fine-tune less" reference that many data-repair papers would fail against. Requiring a data repair to beat model-level references is the correct burden of proof.
4. **Equivalence labels and an explicit "inconclusive" label.** Null results become informative instead of being read as "no effect".
5. **Seed allocation is sensible for the shared comparator.** Random removal (8 seeds) is shared by P1–P3. The Dunnett-optimal √k rule would give about 10, so 8 is reasonable.
6. **Honesty about the measurement.** U is called "refusal erosion as Qwen3Guard labels it". The claim rule restricts the wording to what the HarmBench classifier also supports. The human read's limits, including that the one reader is an author, are disclosed.
7. **Confirmation stage.** At most two contrasts per family are re-run at six fresh seeds on a sealed held-out prompt subsample. This is unusually good practice.
8. **Reproducibility.** Training is deterministic on matched hardware, and a certified evaluation script must reproduce a0's U exactly before the post-hoc references are scored.

## 3. Weaknesses, ranked by severity

Each weakness gives the exact place in the paper, why it matters, and the cheapest fix. KNOWN/NEW tags are in Section 9.

### W1. The registered protocol is not yet frozen, yet the paper calls itself pre-registered (blocking for in-principle acceptance)

- **Where.** The abstract says "six pre-registered repairs". Open items:
  - §4.9: the stage-1 pre-registration is "[NOT YET FIXED]";
  - §3.2: token matching is "[TO BE FIXED]", and the label for a repair that is better on U but worse on a side effect is "[TO BE FINALISED]";
  - §4.4: the Safe LoRA settings are "[NOT YET FIXED]";
  - §4.5 / App. C.5: the nested plant cells are "[TO BE FINALISED]";
  - §4.3 / App. C.3: the final MDE and the secondary arms are open;
  - App. C: copies of the pre-registration are "[TO BE DECIDED]".
- **Why it matters.** For a registered report, the analysis plan is the submission. The open items are not peripheral. They are:
  - the rule for the single most likely interesting outcome: an addition arm that restores safety but raises over-refusal, which the related work predicts;
  - the matching variable for the removal contrasts;
  - the settings of a reference that defines "dominates".

  Until these are fixed, the abstract's "pre-registered" claims more than the protocol supports.
- **Cheapest fix ($0).** Freeze the stage-1 protocol before submission, with every item above resolved. Give an anonymized timestamped registry link (OSF or AsPredicted) and the hashes. Until then, say "pre-specified in this submission" rather than "pre-registered".

### W2. The inference model is internally inconsistent and can be anti-conservative

- **Where.**
  - §3.2: "differences of means over unpaired seeds, with the variance pooled across arms".
  - §4.3: U has SEs "clustered by prompt".
  - App. C.1: Gate B uses seed-matched differences, and its σ̂ is the SD of a seed-paired difference.
  - App. C.3: the stage-1 seed plan is set by "Gate B's pooled noise".
- **Why it matters.** There are three separate problems.
  1. **Paired noise feeds an unpaired plan.** Gate B's design bets that arms at the same seed are positively correlated: "a0 cancels". Stage 1 then ignores the pairing, and its MDE is planned from a paired-difference SD. These two choices agree only if the within-seed correlation ρ is zero, and then Gate B's pairing was pointless. If ρ > 0, the stage-1 MDE is understated. With ρ = 0.5, a pair SD of 3.75 pp implies a per-arm SD of 3.75 pp, and the 6-vs-8 MDE after Holm's first step is about 7.3 pp, not the stated "about 5 pp". At the blinded rule's 4.5 pp cut-off it is about 8.8 pp. The paper does not even say whether the 4.5 / 6.0 pp thresholds are on the pair scale or the per-arm scale. That is a factor of √2 in every power statement.
  2. **Pooling the variance across all 8 arms buys df ≈ 42, but it is fragile to one arm with a larger seed variance.** That is plausible for addition arms, where some seeds may "catch" the refusal rows and others may not, and for arms whose U sits nearer 50%. In my simulation (8 arms pooled; a_R n = 8, the tested arm n = 6, all other arms SD 2.65 pp, equal means), the one-sided test at Holm's first-step level 0.0083 rejects at 0.046 when the tested arm's SD is 2×, and at 0.081 when it is 3×. The unequal n (8 vs 6) makes this worse when the smaller group is the noisier one.
  3. **Prompts are a crossed random factor that the seed-level analysis ignores.** All arms are scored on the same 200 prompts. The per-seed analysis therefore treats the prompt bank as fixed. The labels' CIs are conditional on these 200 prompts and do not cover the arm × prompt interaction. That interaction is what "generalizes to new harmful requests" requires. The prompt-clustered SE in §4.3 does not enter the contrast. The held-out confirmation covers this for at most two contrasts per family.
- **Cheapest fix ($0 compute).**
  - Pre-register one model: a crossed mixed model (or GLMM on the answer-level binary outcome) with arm fixed, seed random within arm (or crossed with arm if seeds are shared), prompt random and arm × prompt random. Equivalently, use a two-way cluster bootstrap over seeds and prompts.
  - Use a heteroscedastic seed variance (Welch-type) as primary, or keep pooled variance with a pre-registered variance check and Welch as sensitivity.
  - Estimate ρ and the variance components (training seed, sampling, prompt) from the Gate A/B runs that already exist.
  - Restate the stage-1 MDE on the correct scale.

  The cost: Welch at about 11 df raises the MDE factor from 3.62 to 4.08 SEs. Better to know this now than after the runs.

### W3. "Does any data repair beat the references?" — the headline (abstract FINDING 2) — has no test

- **Where.** §3.2 (dominance as "below this curve: a lower F than the curve at equal O and L"), §4.4 (references at 3 seeds, with no margin and no multiplicity rule), abstract and Figure 1.
- **Why it matters.**
  - "Dominates" requires beating all five references. That is an intersection–union test. It needs no multiplicity adjustment, but its power is roughly the product of five powers.
  - Four references have only 3 seeds. For a 6-vs-3 contrast at central noise, the SE is about 1.9 pp and the MDE about 5.4 pp unadjusted (about 6.7 pp if the authors Bonferroni over five). This is underpowered for exactly the comparison the paper says it "states plainly".
  - "Below the curve at equal O and L" is not defined. The curve is one-dimensional in λ, with points at 0, 0.5, 0.75 and 1. A repair's (O, L) pair will generally not lie on it. The paper does not say how to interpolate or how to carry the uncertainty.
- **Cheapest fix (about $0, evaluation only).** The safety prompt, adapter scaling and Safe LoRA are post-hoc transforms of a0's adapter, so:
  - apply all three to all six a0 seeds and analyse them paired with a0 by seed (same adapter, transformed), which shrinks the variance a lot;
  - define dominance over adapter scaling at the λ\* that matches the repair's task loss L (the binding side effect), with a seed bootstrap over the interpolated curve;
  - pre-register the IUT, its α and a margin for "beats" (or reuse δ).

  Recipe G and B+Qi need training. B+Qi already has six seeds; give recipe G six as well, or say plainly that recipe G is descriptive.

### W4. Multiplicity is under-specified: "Holm over 6" covers only part of the claims

- **Where.** §3.2 (labels), §4.3 "Primary family", §4.9 (families "each at its own 5% level").
- **Why it matters.** The labels use more tests than the six Holm p-values:
  - superiority on U;
  - adverse tests on U, over-refusal and task loss ("worse");
  - two one-sided equivalence tests (a 90% CI, apparently not adjusted);
  - three τ_O levels.

  If the three adverse endpoints are three Holm families of six, the chance of at least one false "worse" under the global null is up to 1 − 0.95³ ≈ 14%. "Worse" is a consequential label, because it disqualifies a repair. False "equivalent" labels are not controlled across contrasts. A joint statement such as "every removal is equivalent" is an intersection–union claim and needs no adjustment, but six individual labels do. And "attribution is equivalent to random removal" is exactly the individual sentence this paper will be cited for. If equivalence used Holm-adjusted CIs, the chance of an "equivalent" label for a true null effect would fall from 0.93 to 0.68 (6 vs 8 seeds) at central noise, and from 0.78 to 0.32 at the 4.5 pp cut-off (my calculation). That shows how much the unadjusted version leans on its α. The five later families are read "each at its own 5% level" with no stated gatekeeping, so the study-wise error is undefined. P4 is two-sided; whether P1–P3, P5 and P6 are one-sided is not stated.
- **Cheapest fix ($0).** Define one closed testing family, or a fixed-sequence gatekeeper (U superiority/equivalence first; side-effect "worse" tests next, in one Holm family of 12; then confirmation, then Llama). State the sidedness of each test. State whether TOST is adjusted; if not, say "per-comparison equivalence" in every sentence that uses it. Pick one primary τ_O.

### W5. The ±5 pp margin is not justified, and the "better" rule has its own, larger MDE

- **Where.** §3.2 ("smallest effect of interest δ = 5 pp"; better = Holm rejection and estimate ≥ δ); §4.3 (MDE "about 5 pp"); §6 ("The labels resolve differences of about 5 pp").
- **Why it matters.**
  1. **The margin equals the planned MDE.** That suggests it was chosen for what the budget can resolve, not for what matters. No external anchor is given:
     - not a fraction of the erosion (at Gate A's mean E ≈ 45 pp, 5 pp is about 11% of E);
     - not the judge's measurement error;
     - not a deployment threshold.
  2. **An absolute pp margin does not transport.** The "matched erosion dose" allows E anywhere in 20–55 pp, so the same 5 pp is 25% of E in one family and 9% in another. The replication claim of §4.8 then compares labels on different relative scales.
  3. **Through the human read, 5 pp of U is roughly 1.7 pp of usable harmful help.** (About a third of Unsafe answers are usable help.)
  4. **Requiring the point estimate to be at least δ means P(better | true Λ = 5 pp) = 0.50 by construction.** The 80%-power effect for "better" is about 6.2 pp (6 vs 8) to 6.6 pp (6 vs 6) at central noise, not 5 pp. The Holm hurdle is not even binding at central noise, because t·SE ≈ 4.0 pp < 5. A true 3 pp effect that is significant gets "equivalent". That is defensible, but the paper should say that "equivalent" can coexist with "significantly better than random by less than δ".
  5. **The labels are asymmetric.** "Worse" needs only significance, with no margin, so a 1 pp significant harm is "worse" while a 4 pp significant benefit is "equivalent". Defensible as conservatism, but undisclosed.
- **Cheapest fix ($0).**
  - Pre-register δ as a fraction of the family's measured E (e.g. 10–15% of E), with 5 pp absolute as secondary, or justify 5 pp from a judge test–retest or inter-judge disagreement figure.
  - Report the "better" label's own operating characteristic.
  - Make the 90% CI, not the label, the primary output in Table 2 and Figure 1.
  - The 4 pp sensitivity only goes stricter. Also report the smallest margin at which each contrast would be "equivalent".

### W6. Judge error can differ across arms, and the human check is too small to detect it

- **Where.** §4.3 (Qwen3Guard-Gen-4B; the HarmBench-classifier claim rule; over-refusal from the same judge's refusal flag), App. A (50 answers, one author-rater, 10 Safe controls).
- **Why it matters.** Seeds average judge noise; they do not average judge bias. The repairs change answer style in ways a judge can key on:
  - addition arms teach refusal openings, so "refuse-then-comply" answers may read as Safe;
  - H1 shifts answers towards longer outputs;
  - removal arms change format.

  This is differential misclassification. It can create or hide a contrast, and it is correlated between U and over-refusal because one judge scores both.

  App. A cannot estimate per-arm sensitivity or specificity:
  - 39 rated Unsafe answers drawn from five model groups that are not the stage-1 arms;
  - 0/10 Safe controls, whose 95% CI on the false-Safe rate is 0–31%;
  - one rater, who helped design the study, so there is no κ;
  - 12 OLMo items for the HarmBench comparison.

  The claim rule (same sign, at least half the size, classifier erosion ≥ 20 pp) uses point estimates without uncertainty, and is undefined for "equivalent" contrasts, where the sign is noise.
- **Cheapest fix (human time, not GPU).** Pre-register an arm-stratified audit:
  - two independent non-author raters, blind to arm and judge label, with adjudication and a reported κ;
  - about 130 judge-Unsafe answers per arm group (a0; removal arms; addition arms), enough to detect a 15 pp difference in the share giving usable help with 80% power;
  - about 150 judge-Safe answers, enough to bound the false-Safe rate near ±5 pp.

  Report misclassification-corrected contrasts as a sensitivity analysis. State the claim rule's wording for equivalent and inconclusive contrasts.

### W7. Diagnostics are scored once, so their replication misses selection noise (one-shot scoring)

- **Where.**
  - Table 1 and App. C.2: A1 removes the top 600 rows by attribution computed on one retrained a0 (seed 1101) at two checkpoints;
  - S3's DataRx score is, as far as the text says, computed once on one model state;
  - §2: a cited concurrent work finds early risk rankings nearly uncorrelated with later ones;
  - Gate B: R1–R3 are independent random draws.
- **Why it matters.** As written, all six A1 seeds train on the same edited dataset. The six-seed replication then measures training noise given one selected subset, not the variability of attribution as a method. Random removal includes subset-draw variance if, as in Gate B, each a_R seed has its own draw. The P1 contrast is therefore "this one attribution draw against random subsets", and its CI is too narrow for the claim "attribution beats random removal".

  The judges are also one-shot (one label per answer, presumably deterministic). That is fine for noise but makes W6's bias issue untestable without a second judge on the same answers. The Granite direction check helps only in direction.
- **Cheapest fix (a few scoring passes, each well under 1 FRE by the paper's cost logic).** Score A1 (and S3) on at least three a0 seeds and report the top-600 Jaccard and Kendall τ across them. Then either average the scores (and say the selection is fixed), or give each A1 seed its own seed's selection, so that selection variance enters the replication. Pre-register which.

### W8. "Compute-Matched" is a misnomer, and there is no procedure for "which repair is best"

- **Where.** Title; §3.2 (removals matched in rows; tokens "[TO BE FIXED]"); Table 1 (removal arms 33 steps, addition arms 38); §3.2 "C(m) = c(m) + 1 FRE"; §4.7; abstract ("restores the most safety for the compute spent").
- **Why it matters.**
  - Nothing is matched on compute. Rows are matched within removals, and steps differ between removals and additions.
  - H1 removes the shortest answers and so keeps more tokens than random removal. Under the per-row loss, H1 also shifts the loss weight away from the first answer tokens, which is the paper's own Gate C "format" mechanism. H1's contrast thus confounds which rows go with how many tokens and with how loss weight is spread over the opening tokens.
  - C(m) charges every arm's training as one median random-removal run (1 FRE), whatever its own measured time. Addition arms (+15% steps) and H1 (more tokens) are under-charged.
  - The abstract promises a ranking by "safety for the compute spent", but no estimator is pre-registered: no ratio with a Fieller CI and no net-benefit at a stated price. No head-to-head contrast among the six repairs is pre-registered either (A1 vs L1, A1 vs H1, S3 vs S4 are absent). "Which data repair restores the most safety" therefore cannot be answered by the primary family.
- **Cheapest fix ($0).**
  - Retitle ("A Cost-Accounted Comparison", or similar), or truly match compute.
  - Charge each arm its own measured training time.
  - Fix the token-matched analysis now.
  - For "best", pre-register a ranking-and-selection procedure, such as Gupta-type subset selection of all repairs within δ of the best with P(correct selection) ≥ 0.9, or simultaneous CIs for all 15 pairwise contrasts.
  - Express cost-effectiveness as net benefit Λ − λ·C(m) over a range of λ, which avoids ratio pathologies when C ≈ 1.

### W9. The generalization rests on two 1B models, one dataset and a recipe chosen because it erodes

- **Where.** §4.1 (OLMo-2-1B primary; Llama-3.2-1B second; 7–8B "funding-gated, fallback one family"); §4.8 (replication rule); §6.
- **Why it matters.**
  - Attribution, representation filters and DataRx scores all depend on the model's own gradients and representations. Their relative ranking at 1B, where ARC-Easy is near chance (App. C.4) and only a third of Unsafe answers are usable help, need not carry over to 7–8B, where the motivating literature lives.
  - The recipe was chosen over the standard recipe G because it erodes partly, so the estimand is conditional on a non-standard, high-erosion regime.
  - The replication rule, "same sign and family difference below the interaction's MDE", accepts absence of evidence as replication. At six seeds per family the interaction SE is about 2.0–2.4 pp, giving an interaction MDE of about 6–7 pp. A 7 pp effect in OLMo and a 0.5 pp effect in Llama of the same sign "replicate".
  - "A family difference is claimed only above that MDE" reads as a point-estimate rule, not a test.
  - One benign dataset with K = 8 units leaves no replication over data draws.
- **Cheapest fix.**
  - Define replication as agreement of labels in both families, or as TOST on the family × repair interaction within a stated margin.
  - Make the family-difference claim a test.
  - Commit at least one 7–8B family unconditionally, even at reduced arms (P1, P3, P4 and the references); otherwise put "at 1B" in the title.

### W10. The garden of forking paths before stage 1

- **Where.**
  - §4.1 "A matched erosion dose": the rule was fixed after reading a development ladder; "any other too-close bar goes to the user"; "Both Llama rungs were accepted on a too-close bar".
  - §4.1: recipe B was chosen from probe and Gate A readings.
  - App. C.4: the skill-bar loosening was applied non-blind once.
  - §4.6: Gate A's three seeds include the probe seed.
  - App. C.1: "the Gate A a0 runs are reused".
- **Why it matters.**
  - The recipe and LR were selected on the outcome variable (the erosion window). Gate A's E, and possibly stage-1 a0, then reuse the very seed that was selected. That is a winner's-curse bias in E and in every G = F(a0) − F(m), and it carries into the δ_B = 8 pp "18% of E" reading.
  - Human judgement entered at least twice after the data were seen (the Llama rungs).
  - Individually each fork is disclosed. Collectively, the pipeline has many forks: noise gate, guards G1–G4, direction checks, extension, claim rule, length-control wording, blinded shrink rule, coherence screen and three τ_O levels. No end-to-end operating characteristic has been simulated.
- **Cheapest fix ($0).**
  - Exclude the probe seed from every confirmatory estimate (Gate A's E and stage-1 a0), or report both.
  - Publish one decision-tree figure listing every fork, who decided it, when, and with what data visible.
  - Extend the Gate B simulator to the whole stage-1 label pipeline under a few named truth scenarios, and report the label-level error rates.

### W11. The positive control is close to circular and confounds menu size with dilution

- **Where.** §4.5, App. C.5 (k = 37 compliant answers to prompts that have an unsafe answer in PKU-SafeRLHF; cells of 600, 150 and 37–38 rows; a unit's score is the mean over its rows, App. C.2).
- **Why it matters.**
  1. Attribution and representation similarity are bi-anchored on harmful anchors. Planted rows that answer harmful-adjacent prompts will be found by surface similarity, whether or not they cause erosion. A hit then shows that the scorer detects harmful-looking prompts, not erosion-causing rows.
  2. If cells are scored like Gate C's units (the mean over rows), the plant is 6% of an M = 8 cell and 100% of an M = 128 cell. "How diagnosis scales with M" is then confounded with dilution. The aggregation for cells is not stated.
  3. One sealed draw gives one plant location, so each diagnostic's "hit rate" at each M is a single Bernoulli outcome.
- **Cheapest fix.**
  - Add a decoy cell: harmful-looking but non-eroding rows, such as the same prompts with refusals. This tests specificity, and costs only one more cell in the same runs if the decoy is placed in another leaf.
  - Use at least 3 independent sealed plant locations.
  - Pre-register max or top-quantile aggregation beside the mean.
  - Say where the anchors come from. If they come from PKU-SafeRLHF too, the control is circular by construction.

### W12. Over-refusal is measured too coarsely for the limits it enforces

- **Where.** §4.3 (100 greedy prompts: 50 XSTest, 50 OR-Bench-Hard); §3.2 (τ_O ∈ {2, 5, 10} pp; feasibility "if O(m) ≤ τ_O"); App. C.1 G4.
- **Why it matters.**
  - τ_O = 2 pp is two prompts.
  - At a 10% refusal rate, the prompt-sampling SE of a level is about 3 pp. Seeds cannot reduce it, because the prompts are fixed and the decoding is greedy.
  - It is not stated whether feasibility is a point-estimate comparison or a one-sided bound.
  - O is measured against the untuned model, while the "worse" label's over-refusal test is against the comparator, with no margin. A repair can be both "feasible" and "worse" on over-refusal.
- **Cheapest fix (greedy generation only).** Enlarge the bank to 300 or more prompts, or drop τ_O = 2. Make feasibility a one-sided non-inferiority bound. State the precedence between "feasible" and "worse on over-refusal".

### W13. Arms that fail the coherence screen are "not read" (informative missingness)

- **Where.** §4.3 "Answers end": an arm that fails is not read.
- **Why it matters.** Degenerate output is a treatment effect. Dropping the arm after seeing it changes the Holm family post hoc and hides a failure.
- **Cheapest fix ($0).** Pre-register that a failing arm keeps its place in the family and is labelled "failed (worse)".

### W14. The value-of-diagnosis predictions cannot really be tested

- **Where.** §3.4, App. C.7: predictions are "scored" on Llama's category menu.
- **Why it matters.** There is one realized menu per family. "Chance of finding the best repair" is then scored on one Bernoulli outcome, and regret on one realization. No error rate attaches to this "test", yet it is family (5) of the confirmatory order (§4.9).
- **Cheapest fix ($0).** Score calibration of the pre-registered predictive intervals for every unit contrast (8 units × 2 families), with a proper scoring rule. Move the menu-level prediction to the descriptive part.

### W15. Presentation

- **Hard to read.** The paper reads as a protocol: dozens of defined labels and acronyms, gate states in capital letters, and long rule sentences.
- **Placeholders where claims should be.** The contributions list and abstract are mostly placeholders.
- **Key justifications live in an anonymized concurrent submission:** the recipe rule, the rank-16 check, the family contrasts and the human read (App. A says the same read appears there). Reviewers cannot check these, and ICML's dual-submission policy will make an area chair look closely at the overlap.
- **Small inconsistency.** §4.6 says 80% detection needs "about 10–12 pp"; App. C.1 says "about 9, 10 or 12 pp".
- **Cheapest fix.** A one-page "design at a glance" table (arm, comparator, seeds, test, sidedness, margin, family), and moving rule text to the appendix.

## 4. Questions for the authors

1. Are seed IDs shared across arms (e.g. seed 1101 in a_R and A1)? Is generation sampling seeded identically across arms (common random numbers)? What within-seed correlation do the Gate A/B runs show?
2. Are the blinded rule's thresholds (4.5 and 6.0 pp) on the seed-pair-difference scale or the per-arm scale? Please show the MDE arithmetic behind "about 5 pp after Holm's first step".
3. Is the TOST 90% CI Holm-adjusted? Are the "worse" tests on U, over-refusal and task loss one Holm family or three? Which tests are one-sided?
4. Are the five later families gatekept (fixed sequence) or tested regardless? If gatekept, what counts as success of the primary family?
5. How exactly is "below the adapter-scaling curve at equal O and L" computed and tested? What test, margin and α decide "beats the references"?
6. Is A1's top-600 set computed once and reused for all six A1 seeds? Is each a_R seed a fresh random draw?
7. How are Qwen3Guard's "Controversial" labels treated in the primary U?
8. Does stage-1 a0 include the probe seed or the Gate A seeds? If so, why is that not double use?
9. Which τ_O is primary, and is feasibility a point estimate or a bound?
10. What does confirmation require: the same label, a CI excluding zero on held-out prompts, or both?
11. Where do the 64 harmful anchors come from, and do they overlap in source with the plant or the refusal pool?
12. "The add effect must also hold on the evaluation prompts least similar to the added rows." How is "least similar" defined, and what test counts as "holds"?
13. If stage 1 is not funded, what does the camera-ready contain? Is the paper then the Gate B result alone?
14. Why do Gate B (δ_B = 8 pp, Bonferroni, t at 3 df) and stage 1 (δ = 5 pp, Holm, pooled df) use different margins and error models for what is the same kind of removal contrast?
15. Length-reweighted U adjusts for answer length, which the repair itself changes (a post-treatment variable). Will it be reported as a decomposition rather than an adjusted effect?

## 5. The specific statistical concerns requested

**Power at 6 seeds.** At central planning noise, assuming independent arms and pooled df ≈ 42 (my calculation):

| Contrast | SE | Holm first-step MDE, two-sided | 80% effect for "better" |
|---|---|---|---|
| 6 vs 8 seeds | ≈ 1.43 pp | ≈ 5.2 pp | ≈ 6.2 pp (P(better \| true 5 pp) = 0.50) |
| 6 vs 6 seeds | ≈ 1.53 pp | ≈ 5.5 pp | ≈ 6.3 pp |

At the blinded rule's 4.5 pp cut-off (read as a pair SD), these become about 6.2 / 6.6 pp. Read as a per-arm SD, or with within-seed correlation ρ = 0.5, they become about 8.8 pp. With Welch df instead of pooled df, every MDE grows by about 13%.

Six seeds are adequate for 6–7 pp effects at central noise, and marginal above it. The stated "about 5 pp" holds only under the most favourable reading. The fix is W2 plus restating the MDE on the correct scale. A variance-components check would also show whether more samples per prompt are cheaper than more seeds.

**TOST ±5 pp margin.** Not justified externally, and equal to the planned MDE (W5). It is absolute, not relative to E (which varies 20–55 pp across families), and probably unadjusted for multiplicity (W4). With an unadjusted 90% CI, P(equivalent | true 0) ≈ 0.93 (6 vs 8) at central noise and ≈ 0.70–0.78 at the 4.5 pp cut-off. With a Holm-style adjustment it falls to about 0.56–0.68 at central noise.

**Holm over 6.** Valid under any dependence (P1–P3 share a_R; P5–P6 share S1), but conservative. A max-t (Dunnett-type) procedure using the known correlation would recover power. The bigger issue is that Holm covers only part of the decisions (W4).

**Paired vs unpaired.** The design pairs in Gate B but not in stage 1, and plans stage 1 from paired noise (W2). If seeds are shared, pair them, or use a mixed model with a seed effect. Either way, model prompts as crossed.

**Judge noise.** The concern is bias that differs by arm, not noise (W6). Qwen3Guard and the HarmBench classifier may react differently to refusal openings and length. Over-refusal uses the same judge as U. The HarmBench claim rule should carry uncertainty.

**Human-label check size.** 39 Unsafe items plus 10 Safe items, one rater who is an author, not drawn from the arms. It can support a wording caveat, not a measurement-validity claim. About 130 items per arm group and about 150 Safe items, with two non-author raters, would make it decision-relevant (W6).

**"Compute-Matched" vs rows vs tokens.** Matched in rows within removals only. Steps differ (33 vs 38), tokens are not matched (H1), and cost charges the median random-removal run to every arm (W8). Retitle, or match.

**One-shot scoring.** A1 and S3 selections come from one scoring pass on one seed, so selection variance is excluded from the replication. The judges score each answer once (W7).

**Multiple gates and forking paths.** The gates themselves are well-specified and pre-registered (a strength). The risks are elsewhere (W10, W13):
- outcome-based selection of recipe and LR, with probe-seed reuse;
- human calls on "too close" bars;
- a non-blind application of the skill-bar loosening;
- many guards whose joint error rate is unknown;
- arms dropped for incoherence.

Simulate the whole label pipeline and draw the decision tree.

**Generalization from 1B and 7–8B.** Two 1B models, one dataset, and a high-erosion non-standard recipe. 7–8B is conditional on funding. The replication rule accepts a non-significant interaction as replication (W9). Without 7–8B, the claims should carry "at 1B" in the title.

## 6. Ethics and limitations

The Impact Statement is adequate. The release policy is undecided. I would want generated answers to harm prompts withheld, and the planted rows released only as identifiers. No human-subject concerns beyond the one internal rater.

## 7. Scores

Scales: ICML sub-scores 1–4 (4 excellent, 3 good, 2 fair, 1 poor). Overall on the 1–10 scale with anchors 3 = clear reject, 4 = ok but not good enough (reject), 5 = marginally below threshold, 6 = marginally above, 7 = good paper (accept), 8 = top 50% of accepted. Confidence 1–5.

| Item | Score | Reason |
|---|---|---|
| Soundness | **2 (fair)** | Admirable pre-specification, but the core inference model (W2), the reference test (W3) and multiplicity (W4) are not yet sound as written. |
| Presentation | **2 (fair)** | Rigorous but very hard to read. Placeholders occupy the claims. "Compute-Matched" and "pre-registered" overstate. |
| Contribution | **2 (fair)** | The combination is useful and the references are the right burden of proof, but at 1B with one dataset the significance for ICML is modest. |
| **Overall (design, registered-report reading)** | **4 / 10** | Reject in its current form, with an encouraging path. |
| Overall as a normal ICML main-track submission with §5 empty | 2 / 10 | ICML has no registered-report track, and a results-free paper cannot be accepted. |
| Confidence | **4** | Confident on the statistics and design. Less certain about some safety-literature claims, which I did not verify. |

**How results would change the score:**
- Results at 1B only, with W2–W5 fixed, clean labels and a clear reference verdict (including a well-powered "equivalent" null): **5–6**.
- Plus one 7–8B family with the same labels, and the arm-stratified judge audit: **6–7**.
- Results that are mostly "inconclusive", or a reference verdict decided at 3 seeds: **4**, whatever the direction.
- A finding that a free length rule matches attribution, under a sound inference model and a judge audit, would be the most citable outcome. It would raise contribution to 3.

## 8. What would move the score up by 2 (4 → 6)

All but the last are $0 in compute:

1. Freeze the stage-1 protocol, with every [TO BE FIXED] item resolved and a timestamped anonymized registry link (W1).
2. Replace the unpaired, pooled seed analysis with a pre-registered crossed model (seed, prompt, arm × prompt; heteroscedastic seed variance). Restate the MDE on the correct scale from the existing Gate A/B variance components (W2).
3. A formal dominance test against the references. Run the post-hoc references on all six a0 seeds, paired, with the adapter-scaling comparison at matched task loss (W3).
4. One closed multiplicity scheme covering superiority, equivalence and the "worse" tests, plus one primary τ_O (W4).
5. δ anchored to E or to judge disagreement, with the "better" label's own MDE reported (W5).
6. Attribution scored on at least 3 seeds, with stability reported (W7). Also a two-rater, arm-stratified judge audit (W6), which costs human time, not GPU.
7. The only item that costs compute: one 7–8B family committed unconditionally, at reduced arms if necessary (W9).

---

## 9. Already acknowledged in editor's notes vs new

I wrote this section after the review above, having then read Appendix B (main.tex lines 1044–3738). Note numbers follow Appendix B's own lists:

| Label here | Appendix B list |
|---|---|
| risk N | "Risks a reviewer will raise", item N (33 items) |
| weak N | "Where the framing is weak", item N (6 items) |
| decision N | "Decisions the author must make", item N |
| conflict N | "Conflicts between the sources", item N |
| dev | "Development evidence" |

| # | Weakness | Status | Where in Appendix B | What is new in this review |
|---|---|---|---|---|
| W1 | Protocol not frozen; "pre-registered" overclaims | **KNOWN** (mostly) | "What this is" (the list of [NOT YET FIXED] / [TO BE FIXED] items); decisions 5, 12, 19, 22, 26 | The abstract's "six pre-registered repairs" overclaims while the stage-1 pre-registration is not frozen. Not flagged anywhere. |
| W2 | Unpaired, pooled-variance analysis vs paired Gate B; heteroscedasticity; prompts not modelled as crossed | **NEW** | Not raised. Appendix B never discusses paired vs unpaired, Welch, or prompt-crossed inference for stage 1. | All of it. See "What Appendix B's numbers add" below: its own numbers make this the most consequential new point. |
| W3 | No test, power or definition for "beats the references" / "below the adapter-scaling curve"; 3-seed references | **NEW** | Risks 6 and 25 accept that a free reference may win, and the "A repair is better" fill-in says "does / does not lie below the adapter-scaling curve". Neither defines a test. Decision 19 keeps Safe LoRA at 3 seeds. | The missing test, the IUT framing, the 6-vs-3 power, and the zero-compute fix (all post-hoc references on all six a0 seeds, paired). |
| W4 | Multiplicity: endpoints, TOST adjustment, sidedness, family gatekeeping | **NEW** | Decisions 2 and 12 and conflict 33 define the "worse" label and leave the label order open. None counts the error rate across endpoints or equivalence. | All of it. |
| W5 | δ = 5 pp unjustified, equal to the MDE, absolute rather than relative; "better" needs a point estimate ≥ δ | **NEW** | Risk 4 ("Nulls everywhere") concerns filter power, not δ. Decision 21 considered an E-scaled floor for Gate B only (dropped because it equals 8 pp at recipe B). Decision 28 records a 7–8B MDE of about 11–12 pp "against the 5 pp SESOI" without drawing the consequence. | Justifying δ; the relative margin; P(better \| δ) = 0.5; the asymmetry between "worse" and "better". |
| W6 | Judge bias that may differ by arm; the human check is too small | **KNOWN** (core) | Risks 1, 5 ("Additions win on U by construction") and 13 (judge false-Unsafe 22–29% on benign prompts after fine-tuning, against 5% untuned); decision 24 (second rater or a larger read: open, "not planned") | The arm-stratified audit and its sizes; the claim rule's lack of uncertainty; the claim rule being undefined for equivalent contrasts. I disagree with "a confirmatory human check is not planned": risk 13's own figure is direct evidence that the judge's error rate moves with fine-tuning. |
| W7 | One-shot scoring leaves selection variance out of the replication | **KNOWN in part** | Risk 31 ("Scoring once", SABA) | Risk 31 treats this as rankings drifting during training. The new point is statistical: the six A1 seeds replicate one selected subset, so P1's CI excludes selection variance and is asymmetric with a_R. Fix: score on 3 or more seeds and report stability. |
| W8 | "Compute-Matched" is a misnomer; no estimator for "most safety per compute"; no procedure for "best" | **KNOWN** (title) / **NEW** (estimator) | Risk 30; decision 26; weak 1 ("the cost axis is mostly evaluation"); weak 2 (fixed doses) | No ranking-and-selection procedure, no pairwise contrasts among repairs, no net-benefit or Fieller estimator. Correction to my draft: Appendix B's cost ledger (dev, "Cost of an arm": training 245 s of about 3,115 s) shows that charging every arm 1 FRE under-charges the addition arms by only about 1%. That sub-point of W8 is negligible. Weak 1's point, that FRE mostly measures evaluation, is the real issue, and it is known. |
| W9 | Generalization (1B, one dataset, chosen recipe); replication rule accepts absence of evidence | **KNOWN** (scale, recipe) / **NEW** (replication rule) | Risks 19, 24, 27; decision 28 and conflict 52 (option B moves the confirmatory comparison to 7–8B) | The critique of "same sign + difference below the interaction MDE". Risk 22 offers this rule as the answer, and I disagree: it accepts a 7 pp vs 0.5 pp pair as replication. |
| W10 | Forking paths before stage 1; probe-seed reuse | **KNOWN** | Risk 2 (seed 1101 both chose the setting and counts in the mean; answer: report the fresh-seed mean, +45.9 pp); risk 23 (ARC loosening); decisions 25 and 34 (too-close rungs accepted by the user) | The body does not yet report the fresh-seed mean. Stage-1 a0's possible reuse of Gate A seeds is not discussed. The end-to-end pipeline simulation and the decision-tree figure are new. |
| W11 | Positive control close to circular (anchor similarity), menu size confounded with dilution, one plant location | **NEW** | Risk 10 covers only "the plant may not erode". Dev records 64 harmful and 64 safe anchors, sealed, but not their source. | All of it: the decoy cell, at least 3 plant locations, and max/top-quantile aggregation. |
| W12 | Over-refusal too coarse (100 greedy prompts, τ_O = 2 pp); "feasible" vs "worse" precedence | **NEW** | Risk 13 covers judge precision on benign prompts, not resolution. | All of it. Appendix B's dev numbers (untuned OLMo refuses 17/100; after recipe B, 4–6/100) make the conflict the expected case. An addition arm can triple a0's over-refusal, so it is "worse" against a0, and still sit within τ_O = 2 pp of the untuned model, so it is "feasible". |
| W13 | Arms failing the coherence screen are "not read" (informative missingness) | **NEW** | Not raised. | All of it. |
| W14 | Value-of-diagnosis predictions cannot be tested on one menu realization | **KNOWN in part** | Risk 12 ("a model output"; answer: secondary, frozen, scored on Llama) | That scoring on one realized menu is essentially one Bernoulli outcome, while §4.9 still lists it as a confirmatory family. Fix: score the calibration of per-unit predictive intervals. |
| W15 | Presentation | **KNOWN** (dual submission, overlap, gate names, page budget) / **NEW** (inconsistency) | Decisions 9, 30, 32, 33; risk 33 | The "10–12 pp" (§4.6) vs "9, 10 or 12 pp" (App. C.1) mismatch; the design-at-a-glance table. |

**Count.** Of the 15 weaknesses:

| Status | Weaknesses |
|---|---|
| NEW | W2, W3, W4, W5, W11, W12, W13 |
| KNOWN | W1, W6, W10 |
| Mixed (known core, new statistical content) | W7, W8, W9, W14, W15 |

**What Appendix B's numbers add (a reviewer cannot see these; they sharpen W2, W5 and W9).**

1. **W2 is not hypothetical.** Dev ("Gate B wave 0a: the noise gate PASSED") gives:
   - r_j = +0.67, +2.50 and +4.33 pp;
   - σ̂_gate = 1.83 pp, the SD of a seed-paired difference (on 2 df);
   - σ_eval,0 = 1.28 pp;
   - "shared sampling streams" between arms at the same seed (dev, recipe G item).

   Dev "Planning noise" gives a per-arm seed SD of 2.65 pp (on 2 df) and a prompt-clustered SE of 2.8 pp per arm. Taken at face value, these imply a within-seed correlation of about 0.76 (very uncertain on 2 df). Two consequences:
   - The blinded rule reads ≈ 1.8 pp on the paired scale and will approve the full plan. That reading says nothing about the per-arm SD that the unpaired stage-1 analysis actually uses.
   - A seed-paired (blocked) stage-1 analysis would cut the Holm first-step MDE from about 5.2 pp to about 2.7–3.8 pp (my calculation; the range depends on the residual df borrowed). That is the cheapest power gain in the whole study, and it costs nothing.

   Separately, σ_eval is about half the paired variance. More samples per prompt would also buy precision.
2. **W5 and W9 under option B (decision 28).** If the confirmatory comparison moves to 7–8B with a 6-seed MDE of about 11–12 pp, the ±5 pp TOST becomes nearly unreachable there. With a per-arm SD 1.7× the 1B value, P(equivalent | true 0) is about 0.29 for a 6-vs-8 contrast (my calculation), and lower if the SD is larger. Risk 4's answer, "equivalence labels make nulls informative", holds only at 1B central noise. δ, the seeds, or pairing must change before option B is adopted.
3. **W8.** The ledger makes the "+1 FRE for every arm" sub-point negligible (see the table). The title concern stands as known.
4. **W12.** See the table: untuned 17/100 vs fine-tuned 4–6/100 makes "feasible but worse" the default outcome for the addition arms.

None of these change the scores in Section 7: an ICML reviewer would not see Appendix B. But they make W2's fix (pairing by seed, with prompts crossed) the single highest-value pre-stage-1 change.
