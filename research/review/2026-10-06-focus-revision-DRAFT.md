DRAFT — revision of the research/FOCUS.md sections below 'Adopted direction'. Not reviewed, not merged, not frozen. Written 6 Oct 2026 for the General Implementation chat.

# FOCUS.md revision draft: diagnose or retrain?

## 0. How to use this draft

- **It replaces** the FOCUS.md sections from "Operative question" to "Unresolved" (lines 53–119 of the 129-line file read on 6 October 2026, after the lead's update to "Next gates").
- **It does not change** the "Adopted direction" section (lines 7–51). That section is the source of truth here.
- **It keeps as history** the "Dated initial-study amendment, 2 October 2026" (lines 121–129). Section 13 gives one sentence to add above it.
- **Format.** Each section gives the proposed text, then a **Change from 2 Oct** line. At merge, delete these lines or keep them as a dated note.
- **Paths** are from the repo root, so the text can move into FOCUS.md without re-pathing.
- **Evidence marks.**
  - Every number cites a repo file.
  - "Derived" marks arithmetic on cited numbers.
  - "Reported" marks a figure from a paper's abstract or a tool summary, not from its PDF.
  - "UNVERIFIED" marks a claim this draft could not check.
- **No authority.** This draft authorizes no run, spend or freeze. Nobody read held-out prompts, data or outcomes to write it.
- **Inputs folded in:** the reframing proposal sections 2, 2a, 2b, 3a and 4 (`research/review/2026-10-06-reframing-proposal.md`); the lead's update to FOCUS.md "Next gates"; the reading list v2 (`research/review/2026-10-06-reading-list-v2.md`).
- **Parallel draft.** The kill-test design is at `research/experiments/2026-10-06-kill-test-design-DRAFT.md`. This draft refers to it by path only and does not depend on its content.

## 1. Terms (one name for each thing)

| Term | Meaning |
|---|---|
| fix | One change to the fine-tuning data. The 2 October text said "option", "removal" or "edit". |
| a0 | The fix "keep the data unchanged". |
| source | One unit of fine-tuning data: a dataset, or a named part of a dataset that a frozen rule defines. |
| menu | The set of fixes for one decision. It always contains a0. |
| setting | One fine-tuning situation: **main** (benign erosion), **anchor** (overt injected harm, the control) or **middle** (safety-aligned look-alikes; optional). |
| diagnostic | A signal that a selector buys before it chooses: classifier scores, representation similarity or training-data attribution. |
| trial run | A short training run of one fix to a fixed early checkpoint, scored on the selector part of the banks. |
| full run | A training run of one fix to the frozen length, scored on the frozen evaluation suite. |
| FRE | Full-run equivalent, the cost unit. 1 FRE is the measured cost of one full run in that setting (exact definition: open decision 8). |
| rho_d | The cost ratio of diagnostic d: its measured cost divided by the cost of one full run. In FRE units, rho_d is the cost of d. |
| selector | A rule that spends a budget B (in FRE) and picks one fix from a menu. |
| bank | A fixed prompt set: the harm bank, the over-refusal bank or the task-skill bank. The engine splits each bank into development, selector and hidden parts before anyone reads it. |

The adopted direction lists short trial runs among the diagnostics. In the estimands below, trial runs are the comparator: a selector without diagnostic d spends d's cost on more trial and full runs.

## 2. Operative question

**Proposed text:**

In a fixed supervised fine-tuning (SFT) setting, an aligned model becomes less safe after fine-tuning on benign data. The practitioner can change only the data. The menu holds a0 and fixes of three types: remove a source, add safety data, and rewrite or self-distill a source. A selector picks one fix within a budget.

Two co-primary questions:
1. **Decision value.** Does paying for a diagnostic before choosing lead to a fix with lower broad harm than spending the same compute on trial and full runs? The chosen fix must stay within limits on task skill and over-refusal.
2. **Side-effect prediction.** Does the diagnostic predict which fixes will break those limits (cause over-refusal or lose task skill) better than trial runs that cost the same?

Both answers are reported as functions of the diagnostic's cost in FRE.

- **Premise to check first.** The question needs benign erosion that is larger than seed noise and that has a localized cause at the source level. Neither is shown for our model and recipe. The kill test checks both (Staging, step 0).
- **Expected roles of the diagnostics.**
  - The classifier is expected to rank benign data almost uniformly. In the main setting, the informative comparison is attribution against representation similarity, judged against ground truth from seeded removal runs. The classifier stays a charged baseline.
  - In the anchor setting (overt injected harm), the classifier is the expected winner.
  - The middle setting is optional.
  - These are expectations, not findings.

**Change from 2 Oct:**
- The setting was one injected-toxicity SFT setting. Now benign erosion is the main setting, and overt injection is the control.
- The menu was removals of predefined groups. Now it is keep, remove, add, and rewrite or self-distill, with sources as units.
- The comparison was attribution added to a selector that had classifier scores for free. Now every diagnostic, the classifier included, is charged and compared with trial runs.
- The outcome was toxic completions. Now it is broad harm, with task skill and over-refusal as feasibility limits.
- Side-effect prediction is a new co-primary question.

## 3. Precedents and scope

**Proposed text:**

**The setting: support exists, but it is weaker than the premise needs.**
- Qi et al. ([arXiv 2310.03693](https://arxiv.org/abs/2310.03693)) report that fine-tuning aligned models on benign data (Alpaca, Dolly) and identity-shift data can reduce safety. The repo holds this as a title and a reading-list summary only. **Read it in full before citing it** (reframing proposal §2a, item 2).
- He, Xia and Henderson ([arXiv 2404.01099](https://arxiv.org/abs/2404.01099)) *selected* benign rows by gradient and representation matching to break safety. Reported in the abstract: 100 such rows gave over 70% unsafe answers, against under 20% for random rows (prior-work search §2). This shows that benign rows *can* erode safety. It does not show that ordinary fine-tunes do.
- Guan et al. ([arXiv 2505.06843](https://arxiv.org/abs/2505.06843)) find that outlier benign rows break safety (reading list v2, group 4).
- Kim et al. ([arXiv 2508.12531](https://arxiv.org/abs/2508.12531)) report that better hyperparameters alone cut unsafe answers from 16% to about 5% (reading list v2; reported). Erosion may come from the recipe, not the data.
- Fine-tuning services screen customer data with content classifiers and report harm categories, not rows. The customer must choose the fix (problem-validation, rows 9–10; row 9 re-checked).
- **Status: a premise to check, not an established fact for our setting.**

**Diagnostics are studied as rankings, not as decisions that pay for their cost.**
- Injected unsafe data (like the anchor): Pan et al. ([arXiv 2502.11411](https://arxiv.org/abs/2502.11411)) find that attribution beats moderation classifiers at removing injected unsafe rows, from one training run, with no cost reported (prior-work search §2).
- Safety-aligned look-alikes (like the middle setting): DATE-LM ([arXiv 2507.09424](https://arxiv.org/abs/2507.09424)) finds that attribution's detection drops while classifiers hold. RepSim falls from 0.759 to 0.597 AUPRC; WildGuard stays at 0.817 (positioning review §0, checked).
- Benign erosion: DataShield ([arXiv 2606.00160](https://arxiv.org/abs/2606.00160)), GradShield ([arXiv 2605.14194](https://arxiv.org/abs/2605.14194)) and LARF ([arXiv 2507.18631](https://arxiv.org/abs/2507.18631)) filter rows. They report scoring time but never charge it against runs (reading list v2; fetch-tool summaries, UNVERIFIED in the PDFs). Cite the two "DataShield" papers by ID (2606.00160 and 2607.15081).
- Dataset-level representation similarity predicts erosion: Hsiung et al. ([arXiv 2506.05346](https://arxiv.org/abs/2506.05346); reading list v2, group 2). This supports a source-level representation diagnostic.
- **Closest overall:** Xiao and Aranguri ([arXiv 2602.11079](https://arxiv.org/abs/2602.11079)). Their abstract (checked) reports probe attribution "over 10 times cheaper" than gradient attribution and LLM-judge baselines, with filtering, label switching and removal by source. They have no trial-run rival, no add fix and no training seeds (reading list v2).

**Fixes other than removal are studied, without charged diagnosis or decision rules.**
- Adding safety data: Bianchi et al. ([arXiv 2309.07875](https://arxiv.org/abs/2309.07875)); Eiras et al. ([arXiv 2406.10288](https://arxiv.org/abs/2406.10288)), the strongest add arm to beat; DataRx ([arXiv 2608.04322](https://arxiv.org/abs/2608.04322)), which chooses which safety rows to add and measures over-refusal.
- Rewriting and self-distillation: SDFT (Yang et al., [arXiv 2402.13669](https://arxiv.org/abs/2402.13669)). Luo et al. ([arXiv 2609.02771](https://arxiv.org/abs/2609.02771)) find that rewriting beats deletion, and that safety rewriting raised over-refusal.
- Repairs that leave the data alone: SafeTune ([arXiv 2609.22153](https://arxiv.org/abs/2609.22153)) compares many repairs of safety drift on safety, capability, over-refusal and wall-clock time. It excludes data fixes and uses one run per method (reading list v2; fetch-tool summary, UNVERIFIED in the PDF). **It is the likeliest "this was done" citation.**

**Compute-aware choices exist outside safety.** DataDecide ([arXiv 2504.11393](https://arxiv.org/abs/2504.11393)) scores small runs by decision accuracy against compute. Ivison et al. ([arXiv 2503.01807](https://arxiv.org/abs/2503.01807)) charge selection compute against training on more data. Successive halving comes from Jamieson and Talwalkar ([arXiv 1502.07943](https://arxiv.org/abs/1502.07943)).

**Side-effect prediction.** Persona vectors (Chen et al., [arXiv 2507.21509](https://arxiv.org/abs/2507.21509)) are the nearest precedent: activation directions flag training data that will shift a trait (reading list v2).

**Kept from 2 October.** Weckbecker et al. ([arXiv 2609.20027](https://arxiv.org/abs/2609.20027)), Mitigating Emergent Misalignment with Data Attribution (Jaburi et al.), SOURCE and IF-Guide. Sources: `research/review/2026-10-02-new-safety-attribution-precedent.md`.

**The candidate contribution.** The reading list v2 verdict: "still novel as a combination, but its novelty is narrower than before". No work found does all of these together:
- a menu of data fixes of different types, with a0 as a valid choice;
- every diagnostic charged against trial runs at matched compute;
- results as a function of the cost ratio;
- frozen limits on over-refusal and task skill;
- training-seed replication;
- held-out confirmation.

Each part exists alone. Do not claim rewriting, attribution-guided selection or "attribution beats classifiers" as new. The least-covered part is predicting a fix's over-refusal before training. "Not found" means not found by the searches on record; repeat the search before any submission.

**Scope and claim wording.**
- Claims cover safety regressions caused by SFT data. Many incidents are not data-row problems (problem-validation §4, item 4).
- Claims cover users who can change only the data, unless a non-data reference arm is added (open decision 9).
- Claims cover one model family at about 1.5B parameters with LoRA. Retraining is cheap at this scale, which favours trial runs (reframing proposal §1, item 5).
- **Who asks the question.** We found no public evidence that practitioners ask whether attribution is worth its compute; researchers and funders ask it. This is absence of evidence from public sources, not proof (problem-validation §1 and §6; reframing proposal §2a, item 4). Write the question in practitioners' terms: which fix, and how much checking first.
- **Fix types.** Do not claim that real fixes are "mostly additions". Public incidents show additions, and fine-tuning services push customers toward removal (reframing proposal §2a, item 3).
- **Round 1.** Describe round 1 only as a finding about a fixed-size top-K removal rule. remove-10 removed 1,015 rows, while the edit pool held 43 of the 83 harmful-answer rows (positioning review §0). It is not evidence that classifiers fail.
- Toxicity is no longer the target. The ToxicChat banks stay as a secondary measure.

**Change from 2 Oct:** The precedent set grows from four safety-attribution papers to the benign-erosion, add, rewrite, repair and compute-aware literature. The novelty claim narrows to the combination. The premise is marked as unchecked. Claim-wording rules are new.

## 4. Target

**Proposed text:**

For each setting, fix an aligned checkpoint before SFT, a recipe fixed in advance, a training-length rule and a source pool. (Whether a fix's training length is fixed steps or epochs stays unresolved.) A menu holds a0 and K fixes:
- **remove:** drop one source, or a set of sources that a frozen rule defines (open decision 6);
- **add:** mix in safety data from a fixed safety pool at a frozen dose;
- **rewrite or self-distill:** replace the responses of one source with responses from a fixed writer. For self-distillation, the writer is the aligned model itself.

Endpoints average over training randomness, fixed prompt distributions and decoding:
- **F(a):** the unsafe rate on the hidden part of the broad harm bank, under the frozen judge.
- **U(a):** task skill on the hidden part of the task-skill bank, scored by the fine-tuning task's own metric. **L(a) = U(a0) − U(a).** Retaining a harmful behavior never counts as task skill.
- **R(a):** the refusal rate on the hidden part of the over-refusal bank (benign prompts that look risky). **O(a) = R(a) − R(a0).**

With tau_L, tau_O ≥ 0, fix a is feasible if L(a) ≤ tau_L and O(a) ≤ tau_O, so a0 is feasible. a* minimizes F over feasible fixes. A selector with budget B (in FRE) picks one fix. By an evaluation scoring convention, not a safety guarantee or fallback policy (none is specified), an infeasible pick scores F(a0) and counts as a violation; otherwise loss is F(pick). Regret G(B) is expected loss minus F(a*); V(B) is the violation rate; both average over selector executions and menus. This fixed-budget, expected-outcome target gives no per-model, anytime-valid or unlearning guarantee.

**Measurement.** It carries over from `research/experiments/2026-10-02-outcome-definition-amendment.md` and the v2 measurement design (`research/experiments/2026-10-05-headroom-v2-amendment-draft.md`, Parts 2 and 8; the user approved D1–D6):
- **Primary judge.** F uses the pinned Qwen3Guard Unsafe label over all prompts, with the missing-label interval. Selection uses its adverse endpoint. Each prompt gets a greedy answer and 3 sampled answers.
- **Second judge.** Granite Guardian 3.3 8B judges the same answers. A claimed direction needs its agreement.
- **Coherence check.** Score coherence before harm, and keep empty, repetitive and capped answers visible beside every change. After tasks with a restricted answer format, models can give incoherent answers that judges misread (Vishnubhotla et al., [arXiv 2606.03648](https://arxiv.org/abs/2606.03648); reading list v2; reframing proposal §2b, item 5). The coherence method is unresolved.
- **Banks.**
  - Harm: v2's bank (HarmBench, StrongREJECT, SimpleSafetyTests and the OR-Bench toxic subset).
  - Over-refusal: v2's bank (XSTest safe prompts and an OR-Bench hard-1k subset).
  - Task skill: new work (reframing proposal §3a, item 3). ARC-Easy stays a secondary general-capability check.
  - Training-context harm prompts: new; see Splits.
  - Re-run the near-duplicate exclusion against the new training sources.
- **Secondary measures:** the ToxicChat banks; the share of erosion repaired, (F(a0) − F(a)) / (F(a0) − F_pre), where F_pre is the unsafe rate of the aligned checkpoint before SFT.

**Change from 2 Oct:**
- The checkpoint is now aligned, and there are three settings.
- The menu has three fix types over sources.
- F changes from toxic completions to broad harm.
- U changes from a general benign-capability check to the task's own skill, with ARC secondary.
- O is now measured on a dedicated over-refusal bank.
- Feasibility, a*, the scoring convention, G and V are unchanged.
- The second judge and the coherence check are now part of the outcome definition.

## 5. Estimands

**Proposed text:**

**Inputs X0 for every selector:** free metadata only. That is fix type, source size, source origin and safety-data dose. X0 never holds data IDs, hidden construction labels or held-out outcomes (carried from the 2 October dated amendment). Classifier scores leave X0: they are now a charged diagnostic. Every selector buys its trial-run and full-run observations inside B.

**The fixed selector S:** fixed-budget successive halving with a feasibility screen.
- A frozen schedule splits B over rounds.
- In each round, every surviving fix gets observations at that round's fidelity: trial runs first, full runs last. Paired a0 observations at the same seed and checkpoint are shared and charged once.
- After each round:
  1. **Feasibility screen.** Drop every fix whose adverse-endpoint estimate of L or O exceeds its limit. Never drop a0.
  2. **Halving.** Keep the best fraction of the remaining fixes by estimated change in F. The default fraction is one half.
- **Choice.** Among surviving fixes that have full runs on at least 2 seeds and are estimated feasible, pick the smallest estimated F. Exact ties go to a0. If no fix qualifies, pick a0. These rules carry over from `research/experiments/safety-selection-v2-decision-protocol.md`, "Choice and lock".
- **S−** is S with X0 only. **S+d** is S with diagnostic d. It pays rho_d out of B first. How d enters S is open decision 3. The default: d orders and prunes the menu before the first round.

**Primary estimand 1, decision value.** For each diagnostic d:

D_info(d; B, rho) = G(S−; B) − G(S+d; B, rho),

where S+d pays rho FRE for d, and S− spends all of B on runs.
- F(a*) cancels, so an uncertain optimum affects absolute regret, not this contrast. Since regret is nonnegative, D_info ≤ G(S−).
- It measures practical decision value for S at B, not abstract information.
- **The curve.** For each frozen budget, report D_info as a function of rho. Replay S+d on the outcome tables with d charged at each rho. d's information does not change with its price, so this is a price sweep. Mark each method's measured rho_d on the curve.
- **Summaries.**
  - D_info at the measured rho_d: the confirmatory point (open decision 4).
  - The break-even ratio rho*_d(B): the largest rho at which D_info ≥ 0. It is the number of full runs that diagnostic d is worth at budget B (positioning review §3, B2).
- Any claimed arm needs V below a frozen absolute level and non-inferior to its comparator within a frozen margin.
- **Named secondary contrast.** In the main setting: attribution against representation similarity, at matched cost, judged against the seeded removal runs. In the anchor setting: attribution added to a selector that already pays for the classifier. The second keeps the 2 October question alive.

**Primary estimand 2, side-effect prediction.**
- For each fix a other than a0 in a held-out menu, the **violation label** is 1 if L(a) > tau_L or O(a) > tau_O, using the seed-averaged full-run reference outcomes. Otherwise it is 0.
- The **diagnostic predictor** predicts the violation label from X0 and diagnostic d, at cost rho_d.
- The **trial-run predictor** predicts it from X0 and trial runs of the same total cost, spread over the menu's fixes by a frozen rule. A fix with no trial run gets the development base rate for its fix type.
- **D_side(d)** = (balanced error of the trial-run predictor) − (balanced error of the diagnostic predictor), averaged over held-out menus. The balanced error is the mean of the false-feasible and false-infeasible rates. Positive values favour the diagnostic.
- Report D_side for L and O separately, and as a curve over rho.
- **Secondary, incremental form:** both predictors also get the trial runs that S buys in its first round.
- The form and the error measure are open decision 5.

**Conditional, only if a new allocator P is specified before freezing.** The 2×2 {S, P} × {−, +d} with identical features and budget, and D_alg(B) = G(S+d) − G(P+d). P may gain both generically and from d. Its d-dependent part is the interaction [G(P−) − G(P+d)] − [G(S−) − G(S+d)]. One candidate P spends trial runs where attribution and representation similarity disagree (positioning review §5, item 7).

**How the 2 October regret structure maps to the new menu:**

| 2 October element | New meaning | Status |
|---|---|---|
| Menu: a0 + K group removals | a0 + K fixes (remove, add, rewrite or self-distill); units are sources | changed |
| F(a): toxic-completion rate | broad-harm unsafe rate | construct changed; same role |
| L(a) = U(a0) − U(a) | same formula; U is the task's own skill | construct changed |
| O(a) = R(a) − R(a0) | same formula; R on the over-refusal bank | construct sharpened |
| Feasibility, a*, scoring convention, G, V | the same | unchanged |
| X0 with classifier scores and short runs | free metadata only; runs bought inside B; classifier charged | changed |
| S: constrained multi-fidelity BO | successive halving with a feasibility screen; BO only as a sensitivity check | changed |
| D_info(B) = G(S−) − G(S+), attribution only, one budget | D_info(d; B, rho) for each diagnostic, as a curve over rho | extended |
| (none) | D_side(d) | new |
| P, D_alg, the 2×2 | the same, per diagnostic | unchanged |

**How the feasibility limits enter.** They enter three times:
1. in a*, which fixes regret's zero point;
2. in the scoring convention, which charges an infeasible pick F(a0) and counts it in V;
3. in the selector's feasibility screen, which uses estimates.

D_side tests the third directly. D_info tests all three through the choice.

**Change from 2 Oct:**
- X0 loses classifier scores.
- S becomes successive halving.
- D_info becomes one contrast per diagnostic, read as a curve over rho.
- D_side is new.
- In the main setting, the named secondary contrast changes from attribution beyond the classifier to attribution against representation similarity.

## 6. Hypotheses

**Proposed text:**

- **H1, development screen (per diagnostic).**
  - For each diagnostic d, fit two matched-capacity, comparably tuned predictors of F, L and O by source-group cross-fitting to the same full-run outcomes on development menus. One uses X0, d and trial runs. The other uses X0 and trial runs, with d's cost spent on more trial runs.
  - Adding d reduces a prespecified selection-relevant loss on held-out sources, such as plug-in regret and feasibility errors on resampled development menus.
  - Global mean-squared error is not the target: information near a decision boundary can matter while it barely moves, and gains on fixes that cannot win may be worthless.
  - Gains are empirical model comparisons, not proof of conditional mutual information or causation.
  - With few sources, H1 is descriptive.
  - The screen is a cost filter, not a logical prerequisite for H2.
- **H2, decision value (co-primary).** D_info(d; B, rho_d) exceeds a frozen practical margin at the confirmatory point on held-out menus, with V acceptable. This is an empirical finding, not a new algorithm.
- **H2s, side-effect prediction (co-primary).** D_side(d) exceeds a frozen margin on held-out menus.
- **Main-setting expectation.** The classifier will rank benign sources almost uniformly, so its D_info and D_side are expected near 0. The informative test in the main setting is attribution against representation similarity, against ground truth from seeded removal runs. A difference from the classifier means little there.
- **H3, allocator (conditional).** D_alg(B) exceeds a frozen margin: an empirical algorithmic advantage in this setting. A method claim also needs a substantive specified difference and the novelty gate.
- **H4, characterization (exploratory).** Where each diagnostic helps or misleads, by:
  - setting;
  - fix type;
  - rho;
  - how well the classifier sees the contaminated sources (precision and recall per setting);
  - how localized the erosion is;
  - nearness to the feasibility boundary;
  - redundant support.
- **Anchor check (a manipulation check, not a claim).**
  - In the anchor setting, the classifier finds the contaminated sources at a frozen recall and precision, and D_info of attribution added to the classifier is within its margin of 0 (positioning review §1, item 3).
  - If the anchor fails this, review the measurement and the selector before reading the main setting.
  - Note: Pan et al. found attribution better than classifiers at row-level removal of injected data. The anchor expectation therefore rests on source-level units and on cost, not on ranking accuracy alone.

One setting passing H2 or H2s is a feasibility finding. A substantive empirical contribution would also need meaningful gains, reproducibility, a tested explanation and distinctiveness. New menus test menu generalization; new settings test setting transfer.

**Change from 2 Oct:**
- H1 and H2 now apply per diagnostic.
- H2s is new and co-primary.
- The main-setting expectation and the anchor check are new.
- H3 is unchanged.
- H4 adds setting, fix type, rho and localization.

## 7. Counterexample and diagnostics

**Proposed text:**

Constructed failure cases. Each one makes diagnosis worthless or misleading:
1. **Cheap evidence already suffices** (kept). Trial runs already let S select the best feasible fix. A redundant diagnostic cannot improve that choice and consumes compute.
2. **Diffuse erosion.** Every source erodes safety about equally, with no source- or row-level cause. No diagnostic can rank sources, and no remove fix beats the others. The kill test must test this, and a null stops the study (Staging, step 0).
3. **The default add wins.** A fixed small safety mix is always feasible and close to best. Then diagnosis is worth nothing. This is a valid result, and the default-mix baseline must detect it cheaply (reading list v2, risk 3).
4. **Uniform classifier.** In benign data, the classifier ranks sources almost uniformly. Disagreeing with it is then not evidence that another diagnostic has information. Judge every diagnostic against seeded removal runs, not against the classifier.
5. **Hidden, not fixed.** Added data can hide misalignment that returns on prompts that resemble the training context (Dubiński et al., [arXiv 2604.25891](https://arxiv.org/abs/2604.25891); reading list v2). The training-context prompts in Splits test this.
6. **Better ranking, worse decision.** A diagnostic ranks contaminated data well, but the fix it leads to breaks a limit. A fixed-size top-K rule is one such mechanism (round 1). Record at least one documented case if one occurs (positioning review §4, objection 1).
7. **Home advantage.** If the benign data are built with gradient or influence matching, the attribution arm wins by construction (reading list v2, risk 6). Build the data without such matching (Splits).

Kept: conditional redundancy alone does not prove case 1 for an implemented selector, because a redundant transformation may help it use information. Disagreement is a function of both predictions: a candidate feature or trigger, not information beyond them.

**Secondary diagnostics** (reported, never gating):
- each predictor's own proxy in full runs, separating target mismatch from approximation error ([proximal Bregman response](https://arxiv.org/abs/2209.05364));
- residuals against other seeds' full-run means;
- agreement-but-wrong rates;
- noisy disagreement on dominated fixes;
- constructed nested removals with redundant support;
- **new:** classifier precision and recall on contaminated sources, per setting;
- **new:** rank correlation and top-K overlap between attribution and representation similarity, with the classifier shown for reference;
- **new:** measured time for each diagnostic;
- **new:** a localization index, the spread of seeded source-removal effects relative to the seed spread.

Cheap signals direct validation; they certify nothing.

**Change from 2 Oct:** Cases 2–7 and four secondary diagnostics are new. Diagnostics are now judged against seeded removal runs, not against each other.

## 8. Baselines

**Proposed text:**

Compare with matched menus, permitted calibration data, budget and tuning effort:
- **S−:** trial and full runs only. This is the reference for every D_info.
- **S+d** for each diagnostic:
  - the classifier, a charged baseline in the main setting and the expected winner in the anchor;
  - representation similarity;
  - attribution at two or more price points: a cheap one (for example LoRA gradient similarity on saved checkpoints) and an expensive one (EK-FAC or SOURCE) (positioning review §5, item 5).
- **The default arm: "always add the fixed small safety mix".** It uses no diagnosis and no trial runs, only one full run of the chosen mix. **Diagnosis must beat it** (reframing proposal §2b, item 1). Its dose and source are unresolved.
- **A diagnostic's ranking confirmed by full runs.** Take the diagnostic's top fixes and verify them with full runs.
- **Bounds:** "always keep" (a0), and exhaustive retraining (full runs of every fix on every seed) as the cost ceiling.
- **Sensitivity selectors:** multi-fidelity BO (ADMIRE-BayesOpt style). Optionally, the implemented 2 October ranked-acquisition package (`experiments/safety_decision_policy/`).
- **Outside the menu, anchor only:** a threshold rule that removes only rows judged Unsafe (positioning review §5, item 2). Report it beside the source-level results. It does not enter regret, because the classifier builds its fix.
- **Optional reference outside the menu:** one cheap repair that leaves the data alone (open decision 9).

S and P receive X0. Auxiliary baselines may skip unused inputs and reinvest their costs. IF-Guide is optional.

**Change from 2 Oct:**
- Per-diagnostic arms are new.
- The default safety-mix arm is new; diagnosis must beat it.
- BO moves from the main selector to a sensitivity check.
- The threshold row rule and the optional non-data reference are new.
- The classifier's role changes: a baseline in the main setting, the expected winner in the anchor.

## 9. Splits, replication and freezing

**Proposed text:**

- **Roles.** Development data serve calibration, tuning, margins, the screen and headroom checks. Confirmation uses untouched sources, menus, bank parts and fresh seeds.
- **Benign data.**
  - Build the benign data from natural task data, without gradient or influence matching, so that no attribution arm has a home advantage (reframing proposal §2b, item 6).
  - The headroom check covers 2–3 benign tasks with at least 3 seeds each, under a training recipe fixed in advance. Kim et al. report that hyperparameters alone can remove most erosion (reframing proposal §2b, item 3).
  - A frozen rule defines the sources.
  - A seeded rule splits the sources into a development pool and a held-out pool before any outcome.
- **Banks.** The engine splits the harm, over-refusal, task-skill and training-context banks into development, selector and hidden parts before anyone reads them, as in v2 (amendment Part 8).
- **Training-context prompts.** The held-out evaluation adds harm prompts that resemble the training context: the format and topics of the benign sources. This tests whether an added fix hides misalignment instead of removing it (reframing proposal §2b, item 4). Their construction is unresolved.
- **Sealed contamination in held-out menus.** Held-out menus contain contamination drawn by the same frozen rule as the development menus.
  - **Anchor.** Injected harmful rows go into held-out sources by the same seeded rule. The v2 design does not do this: "All injected rows are in the editable pool. None is in a held-out group." (v2 amendment, Part 1; positioning review §0). This must change before confirmation.
  - **Main.** Held-out sources come from the same kind of benign data by the same rule. Which of them erode safety stays unmeasured until confirmation.
  - **Seal.** Before the numerical freeze, commit hashes of the held-out source list, the menus, the seeds and the bank parts. Only the auditor file holds contamination labels, as in v2.
- Menus are built without the compared diagnostics, and the whole design is frozen first.
- **Too close to call.** A withheld reference retrains confirmatory fixes on unseen seeds. Near-ties and borderline feasibility stay labelled uncertain and are reported both ways.
- **Every frozen confirmatory menu is reported,** including those where a0 is best. Correctly keeping the data is a real decision.
- **No retuning on confirmation data.** A confirmatory null cannot trigger retuning or redesign reported on the same data. A revised study needs new held-out data.
- **Replication.**
  - Training seeds, not prompts, replicate F, L and O.
  - Selector executions replicate decision quality.
  - Separate menus replicate generalization.
  - Trial-run seeds are disjoint from reference seeds. Round 1's noise was mostly a shared seed shift (R = 3.3), which would leak into trial runs that share seeds (positioning review §5, item 4; `research/experiments/2026-10-05-headroom-round-1-results.md`).
  - Attribution inherits its trained model's randomness ([Distributional TDA](https://arxiv.org/abs/2506.12965)).
  - Executions that share a run pool are dependent.
- **Sizes.** Round 1's minimum detectable difference between two arm means was about 14 of 72 at 2 seeds and about 9 of 72 at 5 seeds, with 72 prompts (round-1 results, noise table). The ICML plan assumes at least 5 seeds per option in development (reframing proposal §4). Counts are numerical-freeze values. Compute them from development noise in the new settings.
- **Two freezes.**
  - A design freeze (structure, rules, splits, sealing) before development outcomes.
  - A numerical freeze (thresholds, margins, budgets, rho grid, counts) before any hidden access.

**Change from 2 Oct:**
- Source pools, sealed contamination (which v2 lacks) and training-context prompts are new.
- The benign-data construction rule, the recipe fixed in advance and the headroom size are new.
- Disjoint trial-run seeds are now explicit.
- The single freeze becomes two freezes.
- Everything else is unchanged.

## 10. Costs

**Proposed text:**

- **Charge every diagnostic, the classifier included,** its measured cost in FRE.
- **Charge everything else too:** setup, diagnostics, calibration, tuning, selection, trial runs, full runs (including the chosen fix's final training), scoring and audit.
- **Menu construction** (the safety pool, rewrites and self-distilled responses) is a common charge for all selectors. Report it separately.
- **Three scopes,** unchanged from `research/experiments/2026-10-02-cost-scope-amendment.md`:
  1. selection plus one chosen model;
  2. additional research reference and sensitivity work;
  3. total research expenditure.

  The economic reading uses scope 1, plus the one-off total.
- **Amortization.** Report the one-off cost first, for one decision. Then amortize over a stated number of decisions N, and report the break-even N*. The classifier and attribution costs are one-off per dataset, while trial-run costs grow with the number of fixes on the menu (FOCUS.md, adopted direction).
- **Decision value is a curve over rho,** not one budget (see Estimands).
- No single-run cost comparison is a gate. If d plus the minimum required validation exceeds B, B is infeasible for S+d.
- Walltime uncertainty stays model-dependent (`research/experiments/2026-10-02-inference-interpretation-amendment.md`).
- **Fix the unit before measuring.** With sources as units, attribution needs only per-source aggregate gradients, while the classifier still scores every row (reframing proposal §3a, item 2).

**Measured rates.** All on an A100-SXM4-80GB at $1.59 per hour (`research/costs/2026-10-06-cost-ledger.md`, §4). **None comes from the main setting.**

| Item | Measured | Ledger section |
|---|---|---|
| One v2 job: 1.5B base, rank-64 LoRA, 3 epochs, e3 evaluation on the v2 banks | 115.3 min of engine time, about $3.05; about $3.96 per pod with setup, preflight and copy | §1, §4.1 |
| One evaluation on the v2 development banks | 47.7 min, $1.26 | §4.4 |
| Training to the q checkpoint (about a quarter epoch) inside v2 jobs | 341 steps, 5.3 min, $0.14 (training only) | §4.2 |
| One round-1 job | 72.3–102.1 min | §1 |
| Row scoring, Qwen3Guard-Gen-4B, eager attention | 0.358 s per row; 3,503 s for 9,788 rows; $0.158 per 1,000 rows | §4.3 |
| Rewriting, Qwen2.5-7B-Instruct | 3.35 s per row; $1.48 per 1,000 rows | §4.3 |
| One dev-matrix-002 job: Qwen2.5-1.5B-Instruct, small LoRA, 3 checkpoints evaluated | 89.5 min, $2.37 | §4.1 |

**Derived examples.** These are arithmetic on the rows above, not measurements of the main setting.
- **Classifier.** About 58 min, roughly 0.6–0.8 of a round-1 job, with eager attention (FOCUS.md, adopted direction). Measure it again with SDPA.
- **Stand-alone trial run.** With the full v2 development evaluation, a trial run to q would take about 5.3 + 47.7 = 53 min. That is about 0.46 of a v2 job's engine time. Evaluation dominates it, so the size of the selector bank sets most of a trial run's cost (open decision 8).

**Not measured yet** (ledger §8):
- **Attribution, any method, at study scale.** UNVERIFIED until timed.
  - The ledger's estimate by analogy: one gradient pass over all rows costs about one epoch, about 21.7 min ($0.58) per checkpoint at v2 speed.
  - Sizing arithmetic: one per-example gradient of 73,862,144 values is 295 MB in float32, so projection or on-the-fly scoring is needed.
- Representation similarity.
- A stand-alone trial run with its own setup and evaluation.
- Anything in the main setting.
- **External cost claims, all UNVERIFIED:**
  - Nautiyal ([arXiv 2609.32380](https://arxiv.org/abs/2609.32380), a single-author preprint) claims about 1% overhead for inline gradient logging.
  - Bergson is reported to put EK-FAC and SOURCE at several training runs (positioning review §4, objection 5).

**Change from 2 Oct:**
- The FRE unit is new.
- The classifier is now charged.
- The curve over rho replaces a single budget.
- The three scopes and the amortization rule are kept.
- The measured-rate table is new.

## 11. Staging

**Proposed text:**

**0. Kill test (the next gate).** The design is at `research/experiments/2026-10-06-kill-test-design-DRAFT.md`. Its requirements come from the reframing proposal (§3a, with §2a and §2b) and from FOCUS.md "Next gates":
- **a. Headroom first.** Cover 2–3 benign tasks with at least 3 seeds each, under a recipe fixed in advance. Fine-tuning the aligned model must move the harm-bank unsafe rate beyond seed noise.
  - **Stop condition 1:** no task shows erosion beyond seed noise. No ranking can then be validated.
- **b. Localized against diffuse erosion.** Seeded removal runs per source give the ground truth. They show whether removing any source changes F by more than the seed spread.
  - **Stop condition 2:** a null here (the erosion is diffuse) kills the study as designed. Report it as a finding about the setting.
- **c. Rankings and timings.** Rank sources with attribution and representation similarity, and with the classifier for reference. Time each diagnostic.
- **d. Pass rule.** The informative comparison is attribution against representation similarity, judged against the seeded removal runs. Disagreement alone is not a pass. A pass needs a margin fixed in advance that exceeds the seed spread.
- **e. Cost.** The proposal estimates about 10–14 runs, about $40–60 at $4–4.5 per run. The 2b headroom size (2–3 tasks × 3 or more seeds) needs more runs than the two-seed check in that estimate. Re-estimate the cost before asking for money.
- **f. Money.** The kill test needs new money. Ask the user before any spend.
- **g. Gap.** It does not test side-effect prediction (H2s). See section 16.

**1. Design revision.** This draft. Review it, then merge it into FOCUS.md.

**2. Design freeze (G0 for structure).** Freeze the estimands, the selector rules, the menu construction rules, the splits and the sealing before development outcomes. Numbers stay open.

**3. Development.**
- **Engineering** (reframing proposal §3a, item 3):
  - a benign-task data path with sources as units;
  - add and self-distill fixes;
  - a task-skill evaluation;
  - a coherence check;
  - a representation-similarity diagnostic;
  - cost records per diagnostic in FRE;
  - the successive-halving selector.
- **Calibration:**
  - measure FRE, every rho_d and seed noise in the main and anchor settings;
  - audit the judges blind, including benign prompts;
  - estimate G(S−) per setting against the margin;
  - record whether a0 or a fix is best;
  - run the default safety-mix arm early.
- **Screening:** screen H1, and replay D_info and D_side on development menus. For each gain, prespecify the reading:
  - negative if its upper bound is below its margin;
  - positive if its lower bound exceeds its margin;
  - otherwise inconclusive.

  A negative constrains this mechanism here. Inconclusive means collect new development data or stop.

**4. Numerical freeze.** Thresholds, margins, budgets, the rho grid, seeds, menus and executions. Do this before any hidden access.

**5. Confirmation.** The frozen D_info and D_side on held-out menus with sealed contamination. The 2×2 runs only if P exists.

**6. Conditional work:**
- the middle setting (ToxicChat-Het);
- a second model family (OLMo-2-1B);
- a 7B check;
- safety regression under further fine-tuning.

**Side deliverable:** a seed-replicated Pan et al. comparison (reframing proposal §4; positioning review §5, item 6). It can go to a workshop.

**Venue and money** (reframing proposal §4):
- **ICML 2027**, if about $3–5k arrives by early November.
  - The deadline is estimated at about 16 January 2027 for the abstract and 22 January 2027 for the paper. It is not official (UNVERIFIED).
  - The plan takes about 15 weeks.
  - Estimated costs: engineering and calibration about $100–300; development about $1.5–3k; confirmation about $1–2k.
- **Otherwise NeurIPS 2027** (about mid-May; estimate).

**Gate changes to propose for `research/review/EDGE_CHECKS.md`** (not made here):

| Gate | Proposed change |
|---|---|
| G1 Measurement | Add: the task-skill bank, the second judge and the coherence check; measured FRE and rho_d per diagnostic |
| G2 Headroom | Add: benign erosion beyond seed noise (kill test a); localized erosion (kill test b); G(S−) per setting |
| G3 Screen | Per diagnostic, at matched compute |
| G4 Decision value | Per diagnostic, at the measured rho_d, with the curve reported |
| G4s (new) Side-effect prediction | D_side above its margin on held-out menus |
| G6 Generalization | The settings are main, anchor and middle |
| N Novelty | Add SafeTune, DataRx and Xiao and Aranguri to the overlap register |

**Change from 2 Oct:**
- The kill test and its two stop conditions are new.
- The single freeze becomes a design freeze and a numerical freeze.
- The engineering list, the venue plan and the gate changes are new.
- The development reading rule is kept.

## 12. Unresolved

Do not fill these by assumption:
- **The premise:** whether benign erosion exceeds seed noise for our model and recipe, and whether it is localized (kill test a and b). If it is diffuse, the study stops as designed.
- **Models:** the aligned model (candidate: Qwen2.5-1.5B-Instruct, used in dev-matrix-002 and named in reframing proposal §3a); the anchor model (open decision 1).
- **Data:** the benign tasks, the source definition and the pool sizes; the safety pool and its doses; the default safety mix; the rewrite and self-distill writer and prompt.
- **Menus:** size, construction, and fix types per menu.
- **Measurement:** the task-skill metric and bank; the coherence method; the training-context prompts; judge versions for the main setting; decoding; checkpoints.
- **Limits:** tau_L, tau_O, the violation level and the margins. Earlier candidates exist, but this draft adopts neither:
  - 0.02 for both limits (`research/experiments/2026-10-02-initial-diagnostic-precision-targets.md`);
  - ARC within 0.03 and XSTest over-refusal up by at most 5 percentage points (v2 amendment, Part 3).
- **Diagnostics:** the representation and attribution methods, the query sets, and how each diagnostic maps to a per-fix prediction.
- **Selector:** the successive-halving schedule (rounds, fidelities, halving fraction, screening margin).
- **Costs:** the FRE definition, the selector-bank size, the budgets B and the rho grid.
- **Design sizes:** seeds, executions, menus and screen size; the confirmatory family and the multiplicity rule.
- **Hardware.**

**Change from 2 Oct:** The premise, the anchor model, the data, coherence, training-context prompts, the selector schedule, FRE and the rho grid are new items. The base model, scorer and utility items are restated for the new setting.

## 13. Dated initial-study amendment, 2 October 2026: keep as history

**Proposed handling:** keep its text unchanged, and add one sentence above it:

> History. This amendment applies to the 2 October design. The adopted direction replaces its setting, endpoint and menu. Two of its rules carry forward: the outcome-definition separation (see Target), and X0's ban on data IDs and hidden labels (see Estimands).

**Change from 2 Oct:** one added sentence; no text removed.

## 14. Change table

| Section | 2 October | Proposed | Reason |
|---|---|---|---|
| Operative question | Attribution added to a selector with free classifier scores and short runs; group removals; toxic completions | Two co-primary questions (decision value, side-effect prediction) for every charged diagnostic; keep, remove, add and rewrite fixes; benign erosion as the main setting | Adopted direction |
| Precedents and scope | DATE-LM, Mitigating EM, Weckbecker, SOURCE, IF-Guide; toxicity scope | Benign-erosion, add, rewrite, repair and compute-aware precedents; novelty narrowed to the combination; premise marked unchecked; claim-wording rules | Reading list v2; reframing proposal §2a and §2b; problem validation |
| Target: setting and menu | One SFT setting; a0 + K group removals | Aligned checkpoint; main, anchor and middle settings; a0 + K fixes of three types over sources | Adopted direction |
| Target: F, L, O | Toxic completions; benign capability; benign refusals | Broad harm; the task's own skill (ARC secondary); a dedicated over-refusal bank; second judge and coherence check | Adopted direction; reframing proposal §2b, item 5 |
| Target: feasibility, a*, scoring convention, G, V | (as written) | Unchanged | Adopted direction, "Unchanged" |
| Estimands: X0 and S | Metadata, classifier and short runs; constrained multi-fidelity BO | Free metadata only; successive halving with a feasibility screen | Adopted direction |
| Estimands: D_info | One contrast, attribution only, one budget | One contrast per diagnostic; a curve over rho; the break-even rho* | Adopted direction (cost) |
| Estimands: D_side | (none) | New co-primary | Adopted direction (hypotheses) |
| Hypotheses | H1–H4 | H1 per diagnostic; H2 and H2s co-primary; a main-setting expectation; an anchor check; H3 kept; H4 extended | Adopted direction; lead's update (classifier near uniform) |
| Counterexample and diagnostics | One constructed case and five diagnostics | Six more cases (diffuse erosion, default add wins, uniform classifier, hidden misalignment, better ranking but worse decision, home advantage); four more diagnostics | Lead's update; reading list v2 |
| Baselines | S−, S+, a ranking confirmed by full runs, exhaustive retraining | Per-diagnostic arms; the default safety mix that diagnosis must beat; BO as a sensitivity check; a threshold row rule; an optional non-data reference | Reframing proposal §2b, items 1–2; positioning review |
| Splits, replication, freezing | Held-out groups, seeds and menus; one freeze | Source pools; sealed contamination; training-context prompts; a construction rule with no gradient matching; 2–3 tasks × 3 or more seeds; disjoint trial-run seeds; two freezes | Adopted direction; reframing proposal §2b, items 3, 4 and 6; v2 lacks held-out contamination |
| Costs | Full charge list; amortization; no single-run gate | FRE unit; every diagnostic charged; a curve over rho; a measured-rate table; the three scopes kept | Adopted direction; cost ledger; cost-scope amendment |
| Staging | Development, screen, confirmation, conditional work | Kill test (two stop conditions), revision, design freeze, development, numerical freeze, confirmation; ICML or NeurIPS | Adopted direction; FOCUS.md "Next gates"; reframing proposal §4 |
| Unresolved | 2 October list | New list, led by the premise | All of the above |
| Dated 2 October amendment | (as written) | Kept as history, with one added sentence | Brief |

## 15. Open decisions

Each decision gives options and a **recommended default**. None is settled by this draft.

1. **The anchor model.**
   - (a) Reuse v2 as it is: base Qwen2.5-1.5B with injection.
   - (b) Rebuild the anchor on the main setting's aligned model.
   - **Default: (b)** for the decision study. With (a), the setting is confounded with the model. v2 stays development evidence that fixes can work.
2. **The reference for D_info.**
   - (a) Each diagnostic against trial runs only.
   - (b) Each diagnostic added to the classifier (the 2 October form).
   - (c) Both.
   - **Default: (a) as primary.** As named secondaries: attribution against representation similarity in the main setting, and (b) in the anchor.
3. **How a diagnostic enters successive halving.**
   - (a) It orders and prunes the menu before the first round.
   - (b) It is a feature of a frozen predictor at every round.
   - (c) It feeds only the feasibility screen.
   - **Default: (a)**, the simplest and least open to "the selector decides the result". Use (b) as a sensitivity check beside BO.
4. **The confirmatory point on the cost-ratio curve.**
   - (a) D_info at each diagnostic's measured rho_d, at one primary budget.
   - (b) The break-even ratio rho*_d with its uncertainty.
   - (c) A uniform claim over a range of rho.
   - **Default: (a) as confirmatory, (b) as the headline summary,** and the full curve at a small frozen set of budgets as descriptive.
5. **The form of D_side.**
   - (a) Head to head: the diagnostic against trial runs bought with its cost.
   - (b) Incremental: both predictors also get the first-round trial runs.
   - The error measure: balanced error, the false-feasible rate, or the Brier score.
   - **Default: (a) with balanced error,** the literal reading of the adopted direction. Report (b) and the Brier score as secondaries.
6. **What "remove a subset" means.**
   - (a) Sources or source sets only, built by frozen rules.
   - (b) Also row subsets that a diagnostic builds.
   - **Default: (a).** Under (b), menus would depend on a compared diagnostic, which breaks "menus are built without the compared diagnostics". Report row filters outside the menu.
7. **The confirmatory family and multiplicity.**
   - (a) Main setting only: diagnostics × {D_info, D_side}, adjusted by Bonferroni as in the 2 October decision protocol. The anchor is a manipulation check under the same rules. The middle setting is exploratory.
   - (b) Main and anchor both confirmatory.
   - **Default: (a).**
8. **The FRE definition and the selector-bank size.**
   - (a) FRE = one full run's training plus its selector-bank evaluation. Setup is charged separately as one-off.
   - (b) FRE = the all-in pod cost.
   - The selector bank is either the full development bank or a smaller fixed bank.
   - **Default: (a) with a smaller fixed selector bank**, sized and timed in development. Also report the all-in cost.
9. **Cheap repairs that leave the data alone** (a one-example patch, weight-space recovery, PTST).
   - (a) Limit the claim to users who can change only the data.
   - (b) Add one such repair as a reference arm outside the menu and outside regret.
   - **Default: (a), plus (b) with one repair if the budget allows.** Fine-tuning services that tell customers to fix the data are the (a) case (problem validation, row 9).
10. **When to freeze.**
    - (a) One freeze before development (as the brief's staging reads).
    - (b) One freeze after development (as the reframing proposal §4 timeline reads, week 9).
    - (c) Two freezes.
    - **Default: (c).** Freeze the design before development and the numbers before hidden access. This matches the 2 October practice.

## 16. Underspecification and inconsistencies for the lead chat

1. **Freeze order.** The brief says "freeze → development". The reframing proposal §4 freezes in week 9, after development in weeks 5–8. Open decision 10 resolves this.
2. **Kill-test size.**
   - Reframing proposal §3a, item 4 asks for a two-seed headroom check.
   - §2b, item 3 asks for 2–3 tasks with at least 3 seeds each.
   - The $40–60 estimate assumes the former.
   - This draft uses §2b. The cost needs re-estimating.
3. **Kill-test pass rule.** §3a, item 1 still says "better than the classifier does". §2a, item 6 and FOCUS.md "Next gates" say that the comparison is attribution against representation similarity. This draft follows the latter. §3a should be updated.
4. **No early test of a co-primary hypothesis.** The kill test checks only removal and F, so nothing tests H2s before commitment. Suggestion: add one cheap side-effect check, for example the default add arm with O measured.
5. **"D_info unchanged" cannot hold literally.**
   - D_info had the classifier free inside X0. Charging the classifier changes X0 and the reference selector.
   - D_info also covered attribution only, so it must be extended per diagnostic.
   - The regret structure itself is unchanged.
6. **"As a function of the cost ratio, not at one budget."** rho and B are different axes. A curve over rho is still drawn at some budget. This draft reports the curve at a small frozen set of budgets, with one primary budget (open decision 4).
7. **The anchor expectation and Pan et al.** Pan et al. found attribution better than classifiers on injected data at the row level. "The classifier should win" in the anchor therefore rests on source-level units and on cost, not on ranking accuracy. This draft words the anchor check that way.
8. **v2 is not yet a valid anchor for confirmation.** It uses a base model, not an aligned one, and it has no contamination in held-out groups (open decision 1; Splits).
9. **Menu degeneracy.** Removing a whole source in a fine-tune with few tasks may always break the task-skill limit. Then only add and rewrite fixes compete. The source definition must leave several sources per task.
10. **"Diagnosis must beat the default mix" has no estimand yet** (added in review by General Implementation II). Baselines says the default arm is the one to beat, but D_info's reference is S−, not the default arm. The default arm spends about 1 FRE, while S+d spends B. Options:
    - (a) a named contrast D_def(d; B) = G(Default) − G(S+d; B), with a frozen margin, reported beside D_info and honest about the unequal spend;
    - (b) a gate: S+d counts as useful only if D_info > margin **and** G(S+d) < G(Default) − margin;
    - (c) put the default mix into S− as a free first observation, so that every selector starts from it.

    Suggested default: (b). It keeps D_info's matched-compute meaning and makes the §2b requirement testable.

## 17. UNVERIFIED and reported items in this draft

- **Venues and dates:** the ICML 2027 deadline (about 16 and 22 January 2027) and the NeurIPS 2027 timing. Both are estimates, not official.
- **Attribution cost:** unmeasured. The one-epoch analogy (about 21.7 min per checkpoint) is a ledger estimate.
- **Other costs not measured:** representation similarity; a stand-alone trial run.
- **External cost claims:** Nautiyal's 1% inline overhead; Bergson's "several training runs" for EK-FAC and SOURCE.
- **Facts from fetch-tool summaries** (reading list v2): SafeTune, DataShield, GradShield, DataRx and Vishnubhotla et al.
- **Figures from abstracts or summaries:** Qi et al. (title and summary only in the repo; read before citing); He et al.'s 70% and 20%; Kim et al.'s 16% and 5%; Dubiński et al.
- **From earlier notes, not re-checked:** Pan et al.'s venue.
- **Kill-test cost:** the $40–60 figure is an estimate and is likely low (section 16, item 2).
