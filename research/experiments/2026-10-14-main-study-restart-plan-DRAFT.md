# Main study: restart plan

**14 October 2026 · GPT lead draft, revision 3 · planning only.** The user subsequently instructed **“restart plan using gpt”**. GPT now owns this restart planning/design package; the previous Opus quota failure is historical and no longer blocks completion of the plan. Non-author GPT review is retained. This is not a frozen experimental protocol or spending authorization. It preserves the existing Gate B/C freeze and identifies prospective changes needed for the later main comparison. The concrete companion package is `2026-10-14-gpt-restart-execution-package.md`, with a separate pre-wave-1 commitment audit and offline cost/replication worksheets.

## 1. The paper we are trying to produce

**Does training-data attribution improve the choice of a finite safety-data repair, beyond edit metadata, strong content classifiers and short training runs, after charging its cost?**

Setting: safety erosion after benign instruction fine-tuning. Report safety restoration together with over-refusal and task performance. Distinguish three results: predicting repair outcomes, choosing a better repair at a fixed budget, and comparing repair methods. None establishes a new allocation algorithm.

The October 8 adopted plan leads with a measured repair frontier and treats decision-value replay as secondary. The October 11–12 review identifies the gap: replay cannot establish that paying for attribution improves an actual decision. My recommendation is to add actual matched-budget selector executions and specify their confirmatory status prospectively. This needs an explicit amendment before confirmation; this document does not silently replace the adopted primary family. The narrower Roger Grosse proposal informs the information-value comparison; it does not restore the historical toxic-completion/removal-only setting.

### Adopted decisions and proposed amendments

- **Retained:** OLMo's six primary U/Holm contrasts P1 A1−R, P2 L1−R, P3 H1−R, P4 S1−a0, P5 S3−S1, P6 S4−S1; 600-row removal and 48-row addition doses; the adopted seed-count rule, judge rule, cost conventions and reference-dominance restriction. Here A1 is attribution, L1 LARF-style, H1 shortest answers, S1 random refusal data, S3 DataRx-style selection, S4 self-generated refusal data. These are the adopted basis for a later preregistration, not a new run authorization.
- **Retained, conditional on funding:** the planted-control tier and its precommitted pilot; if unfunded, no measured menu-size headline. A synthetic positive control does not establish ordinary-data decision value.
- **Retained branch:** rewrite/self-distillation stay out of the adopted core; one self-distillation arm belongs to the DIFFUSE fallback. Any addition to the core needs a prospective, approved amendment.
- **Proposed amendment:** actual S−/S+ decisions and D_H, their primary/secondary placement and multiplicity/testing order, new confirmation access, practical margins for that comparison and any cheap baseline addition. Preserve the original repair family unless the user approves a specific replacement. Nothing is promoted by this roadmap.
- **Deferred extension:** a full oracle bank and larger natural-menu claims need separate costs and a frozen sampling design.

Full-paper target: a complete small-model comparison on OLMo, key replication on Llama, then the most informative comparison at 7–8B, conditional on measured cost and funded replication. The previously proposed 32B/70B checks are optional extensions. Model scale alone is not a substitute for the central comparison.

## 2. Starting position

- **Available development evidence:** Gate A passed on OLMo-2-1B; benign fine-tuning erodes classifier-defined safety. The family × recipe side-study preprint is a precursor **(waiting for arxiv approval)**. Its results show that a recipe fix can depend on family/scale, and repairs can raise over-refusal. It does not show that attribution improves decisions.
- **Gate B/C:** revision 5 is frozen. The anchor is verified; wave 0a onward is paused. Resume the existing sequence within its rules once it is funded and a fresh launch check passes. A DIFFUSE/TOO CLOSE result invokes the adopted repair-choice fallback; it must not trigger repeated redesign until localization appears.

**Local preparation completed under the GPT restart instruction:** the matching pinned kit packed the Gate B setup, and the existing plan tool added `w0a-1` with R1/R2/R3 at seeds 1101/1102/1103, 5.0-hour cap. No provider create intent or pod record exists for this host; no GPU run occurred. Initial metadata snapshots and before/after plan hashes are retained in the planning input folder. The environment reference is still established by wave 0a's guarded preflight, not fabricated locally.
- **Available code:** `experiments/safety_selection` supplies training, attribution, manifests, audience/seed roles and edit files; `experiments/safety_decision_policy` supplies an exploratory S−/S+ comparison with costs, final-choice locks and durable receipts. These are reusable components, not a completed main-study pipeline.
- **Concrete mismatch:** current Dolly preparation has an empty held-out group partition. Edit handling excludes held-out members, and the README states that frozen confirmation edit arms need an amendment. Existing Stage B outcomes use ARC-derived utility/refusal rather than the main study's task loss and over-refusal banks. Existing policy ranks once and purchases paired full runs; it is not implemented successive halving. These contracts must be reconciled before reuse.
- **Resources:** the three applications total $9,000 requested research cash plus up to $2,000 separately requested engineering support. No award is reported. The last verified RunPod snapshot, October 13 at 09:10 UTC, had $5.56 balance, no running pods, and $0.243/hour storage spend. It is a historical snapshot, not today's available balance. Retention is a planning assumption; no deletion/restart is authorized here.

**New user constraint during this planning turn:** the applicant can provide **$50–100 more RunPod credit** before the grants. Treat it as offered upfront funding, not a verified deposit or a grant award. Plan wave 0a/0b first; the lower end cannot fund the frozen wave-1 worst-path threshold. Hours/week remain unspecified.

**Fresh read-only billing check, October 14:** after refreshing the logged-in RunPod billing page, both the account balance and header show **$4.57**, current spend rate **$0.029/hour**. Initial navigation briefly showed inconsistent loading figures; the refreshed page resolved them. Billing reports a one-hour data lag. This supersedes the October 13 snapshot for balance/rate, not the old pod-count/volume inventory. API check was unavailable because the operator-key environment variable was unset; no credential search beyond project filename metadata, top-up, restart, deletion or cloud experiment was performed. Do not infer the previous 820 GB retention roster is still current from this screen.

Evidence: current `research/FOCUS.md`; Gate B/C preregistration; October 13 scientific status in `.ai/HANDOFF.md`; October 11–12 novelty review; current code/READMEs; October 13 funding plan.

## 3. Recommended core comparison

### 3.1 Actual S− and S+ executions

Use one existing, specified constrained multi-fidelity selection method in both arms. Choose the method in development and freeze it; compare the existing rank-once policy with a standard successive-halving implementation before deciding which is adequate. Do not introduce a new allocator as part of the primary comparison.

- **S−:** permissible edit metadata, strong classifier/content features, and short-run observations. It can spend the money saved by omitting attribution on more trials or replication.
- **S+:** the same permissible inputs, fitting capacity and tuning opportunity, plus a prospectively selected attribution feature. It pays for attribution prerequisites, scoring and tuning.
- **Common menu:** candidates are generated by a fixed outcome-free rule before attribution or outcome labels are available. Attribution-selected candidate construction must not be supplied free to S−. If comparing different candidate generators instead, label that as a different repair-method comparison.
- **Budget:** both receive the same total allowance. Reserve the cost of the chosen model's full training and evaluation first. Include setup, classifiers, calibration/tuning under the declared amortization convention, all failed attempts, trial evaluation and final validation. A budget that cannot buy the fixed work plus final reserve is infeasible.
- **Enforcement:** freeze the charging unit and check remaining budget before every attempt and retry, including fixed work and the conservative cost cap for the most expensive eligible final action and every required final replica. Use bounded operations; insufficient remaining budget invokes the frozen failure/keep rule. The historical package's quote-only planning plus retrospective receipts does not establish an enforced realized-cost cap. Equal allowances need not produce equal realized expenditure. Keep per-policy economic charges separate from deduplicated physical/provider spend and whole-research costs.
- **Lock then validate:** each policy chooses using only its own paid observations. Lock the repair before evaluating it on fresh final training seeds and a hidden prompt bank. Saved attribution cost can change S−'s observations; equal access does not mean identical realized observations.
- **Fallback:** freeze tie, insufficient-evidence, no-feasible-edit and failure behavior. Keep/no repair is an allowed decision and remains in the results. Operational failures are charged and reported, not replaced by favorable fresh draws.

### 3.2 What the experiment estimates

Proposed direct safety contrast at budget B:

`D_H(B) = mean[H(final S−) − H(final S+)]`, where H is HarmBench-classifier compliance on the locked repair's hidden evaluation.

Also report the analogous Qwen3Guard Unsafe contrast separately, over-refusal, task loss and cost. Do not combine them into a newly invented composite. HarmBench is classifier-defined compliance, not a human-harm estimate. Confirmatory status and testing order for these outcomes need a prospective amendment, consistent with existing judge rules.

Report feasibility-violation rates for each policy across **all** configured executions, and the difference between policies. Safety benefit supports a practical decision claim only alongside an absolute violation limit, a non-inferiority margin for violations, and complete cost evidence. Do not discard infeasible final models and compare only the survivors. Missing final outcomes need the frozen missingness/bounding rule.

Preserve the adopted model-level reference restriction: data repair beats model-level repair only if it beats the applicable reference frontier, including the adapter-scaling curve of U against over-refusal and task loss. Put applicable cheap data repairs in both policies' common action menu, or justify exclusion prospectively. If a one-example patch needs a post-fine-tuning action, explicitly extend the eligible action contract or keep the claim restricted to the declared data-edit menu and report the external reference. A positive D_H can mean attribution improves that restricted selector without being the best practical repair. Do not turn it into an unrestricted purchasing recommendation.

Without a full outcome-hidden reference bank over the whole menu, this design estimates which policy chooses better, **not** absolute regret relative to the best possible repair. A full oracle bank is an optional separately costed reference study. Replay remains a labelled secondary analysis; synthetic planted causes are sensitivity controls, not evidence of benefit on ordinary benign data.

### 3.3 Replication and generalization

Freeze the target before choosing counts:

1. A prospectively frozen menu repeated across independently drawn selector and final training seeds supports a **conditional claim for that menu and setting**.
2. A claim about unseen menus requires menus/problem instances sampled from a prespecified generator held out from tuning. Construct candidate sets without outcomes, declare source/row overlap, and block/model dependence from shared corpora, model family and cached artifacts. Re-randomizing eight known category removals does not by itself create independent problem instances.

Prefer option 2 if the available corpus and budget support it. Otherwise use option 1 and restrict the claim explicitly. Do not promise generalization from a count of prompts, output samples or edit candidates.

Within each setting, block S−/S+ by problem instance, allow common final seeds for paired comparison, and randomize execution order/GPU placement with a recorded seed. Use fresh selector and final seed namespaces, never call continuation of a short run an independent replicate. Prompt-level uncertainty is nested inside training/decision replication. Menus containing keep and multiple repairs need overlap-aware analysis.

### 3.4 Baselines and measurements

Development must select a feasible, strong comparison rather than a weak attribution-versus-random headline:

- Metadata/format/length heuristic; a strong content classifier; short-run selection, with comparable tuning and the same permissible inputs.
- Common candidate families: keep, matched removals and safety additions, with applicable cheap data repairs included fairly. Preserve the removal/addition distinctions, published dose controls and the adopted six repair contrasts. Rewrite/self-distillation remain outside the adopted core except for the self-distillation DIFFUSE fallback; broader inclusion requires an amendment. Freeze the actual roster after feasibility checking; not every candidate method deserves a full confirmatory arm.
- Cheap repair references: safety prompt, adapter scaling, recipe G, Safe LoRA and a one-example safety patch. The last requires checking the paper's exact setting and implementation before freezing inclusion or a reasoned exclusion. Their candidate selection and evaluation costs count.
- Separate outcomes: Qwen3Guard Unsafe/refusal, HarmBench compliance, over-refusal on benign/borderline requests, task loss; ARC is supporting evidence at 1B.
- Blinded independent human audit of a prospectively sampled set from all relevant arms, including benign requests. Two ratings of one answer are not two independent answers. The prior applicant-only read is not independent validation.

Candidate margins already discussed: 5 pp practical safety difference and over-refusal grid 2/5/10 pp. Their use for the new direct comparison is **not yet frozen**. Choose one primary constraint before outcomes, retain the grid as sensitivity. Set task-loss tolerance from practical acceptability, with uncertainty estimated separately; an SE-derived threshold changes with replication and needs explicit review. Avoid interpreting non-significance as equivalence.

## 4. Work sequence and completion gates

### Phase 0 — restart package, now; no new GPU work

GPT owns this plan, source reconciliation, alternatives and acceptance criteria under the user's task-scoped routing instruction. Produce a versioned scope/claim checklist, identify artifact hashes and reuse boundaries, prepare bounded work packages, and obtain a non-author GPT methods review. Preserve frozen Gate B files and prior reviews. Recheck relevant primary literature; record what was actually read and what still requires full-method inspection.

**Done when:** every proposed claim maps to an actual measurement, amendment and resource need; reviewers' major objections have a disposition; unresolved quantities are explicit. A draft is useful today; a frozen protocol is not claimed.

### Phase 1 — wave 0a/0b and early cost calibration, after funding

Resume wave 0a (R1–R3); wave 0b (retrain/diagnostics) runs **only if the frozen noise gate permits it**. Otherwise record the failure and take the adopted fallback. Follow the frozen order, not the side-study causal follow-up. If 0b runs, stop at its re-costing boundary. Read only authorized development summaries. Price other development calibration jobs separately; the offered $50–100 must not silently become a general pilot allowance. Measure startup, inference/judging, storage and failed-job overhead. Separate GPU seconds, dollars and end-to-end research spend; an evaluation-heavy FRE is not a portable training-cost ratio.

**Done when:** the noise gate has been read and either the permitted 0b/re-costing is complete or failure/fallback is recorded. No wave 1 until the commitment and funding checks below. The illustrative $100 total remaining Gate B envelope is not a quote or launch allowance.

### Phase 2 — pre-wave-1 commitments, remaining Gate B, then main-study readiness

**2a. Mandatory pre-wave-1 boundary.** Audit and commit every stage-1 scorer's code/settings, outcome-free edit rule, pools, plant, original primary family/seed rule, limits/judge rule, selector spec and predictions **before Gate B wave 1**, as FOCUS and the frozen preregistration require. Any proposed amendment needs review and user approval before its relevant outcome boundary. Already committed items can be verified rather than rebuilt. Anything added after wave 1 retains the required post-Gate-B exploratory status; a new later confirmation does not relabel its development origin.

**2b. Remaining Gate B/C.** With 2a complete and fresh balance meeting the re-costed worst-path need plus required storage/judge allowances under the frozen rules, run the remaining waves with the existing pinned engine/kit unchanged. $78.45 is the historical baseline, not a replacement for that calculation at measured timings/rates. Read the final verdict by the frozen rule; apply fallback if required. Use the precommitted blinded nuisance/seed rule, not the favorable effect, to determine any adopted stage-1 count. No bypass of the funding stop to fit a $50 tranche.

**2c. Main-study readiness.** Complete separately priced representative short/full repair, candidate construction and final-evaluation cost calibration in authorized development jobs. Set the final confirmation workload using the prospectively fixed precision rule. Keep any implementation successor separately versioned and isolated from Gate B's frozen engine and records; do not integrate changes that invalidate that running protocol's pins.

Resolve primary status, fixed-menu versus unseen-menu inference, actual candidate roster, short/full checkpoints, method, feature/tuning parity, all outcome/feasibility margins, judge rules, data/seed splits, human audit, missingness and stopping. Use prospective precision/power scenarios from development decision variation, not only the old arm/prompt SD. Price independent decision instances, training seeds and final validation separately.

The restart package prepares reviewed bounded implementation briefs and isolated integration scopes; no implementation is reported complete by this planning artifact. Likely scopes:

1. `prepare_task.py`, `jobs.py`, `edits.py`, `planning.py` and matching configuration: a separately versioned confirmation contract for repair candidates, preserving Gate B identity.
2. `safety_decision_policy/{outcomes,features,config,policy,controller,backend,costs,analysis}.py`: map the main-study outcomes, menu representation, selected existing allocator, final-reserve/accounting and missingness rules. Do not call the historical exploratory package confirmatory without this work.
3. Run manifest/receipt adapter and instructions: bounded engineering support, if supplied, with agreed hours/scope and no duplicate compute charge.

**Done when:** exact paid workload is feasible at the approved cap; split/code/data hashes are frozen; non-author review closes material leakage/accounting issues; the user has approved the scientific amendment and execution budget. Implementation verification will require its own authorized check brief; no tests were run for this planning request.

### Phase 3 — OLMo core confirmation

Run the frozen actual policy comparison and repair references. Analyze all configured executions, locked choices, failures and charges. Separate practical benefit, predictive benefit, no detectable benefit and inconclusive precision. No optional stopping on a favorable result; any sequential extension must be prespecified.

**Done when:** planned endpoints and uncertainty are reported, human/judge checks complete, and every claim can be traced to an unseen evaluation rather than the winning trial.

### Phase 4 — Llama replication and 7–8B key comparison

Freeze what transfers unchanged and what is recalibrated. Use family-specific measured costs and recipes; report scope restrictions when a result changes. Spend remaining approved funding on the decisive comparison, not an unfunded sweep of all repairs. Fresh settings are confirmatory only if their choices were prospectively fixed.

**Done when:** replication is complete at its declared precision, or its failure/inconclusiveness is fully documented. Broader-scale claims remain conditional if funding is insufficient.

### Phase 5 — paper and reproducibility package

Draft the methods and empty result structure while experiments proceed. After consequential results, recheck novelty and rigor, write the measured conclusion including nulls, and produce numerical reproduction plus clearly scoped training instructions. Use the precursor as development motivation **(waiting for arxiv approval)**. Respect the existing private-repository/publication boundary.

**Done when:** figures, costs, all arms and limitations reproduce from versioned records; pre-submission review supports each sentence. ICML is a target, not an acceptance prediction.

## 5. Funding and schedule

- **No award yet, offered $50–100 RunPod funding:** complete Phase 0; after the actual deposit and stage authorization, wave 0a/0b can be priced within the lower tranche. Their historical nominal uppers sum to about $11.01, excluding storage, failed starts, separate judging and other jobs. The frozen wave-1 balance threshold is $78.45 before that wave; $50 cannot satisfy it after the preliminary jobs. The historical full remaining illustrative path is $92.23 excluding reserve/storage. $100 may support the remaining Gate B path but is not guaranteed. Do not promise that it funds the main paper. Check fresh balance, actual offered price and re-costing before any launch.

Recommendation for this tranche: **$100 is more useful than $50** if the user wants to fund the remaining Gate B path. With the refreshed $4.57 balance, the illustrative $92.23 path plus $6 reserve would require about $93.66 additional credit before future storage or deviations. This is historical planning arithmetic, not a quoted bill or a substitute for the frozen admission checks. Do not initiate a top-up from this plan.
- **BlueDot $6,000 awarded:** planned compute/judging component is $3,700; other planned costs are audit $800, retained storage $700 and subscriptions up to $800 before tax. Price the minimum coherent core first. These allocations are a grant draft, not a proven adequate main-study budget.
- **TAIF $3,000 also awarded:** conditional extension has $2,200 compute/judging, $200 incremental storage/backups and $600 failure/revision allowance. Spend it on distinct replication/extension jobs after the base is costed; revise the funding plan with the funder if the base is unfunded.
- **AIAF support:** up to $2,000 engineering request is separate from research cash; deliverable/hours/quote are not agreed. Do not assume paid personnel or free GPU provision.

Provisional internal targets, dependent on funding/implementation: October for the freeze and development cost calibration; November for the OLMo comparison; December for replication, audit and the complete paper draft; early January for result review and submission preparation. These are scheduling targets, not forecast completion dates. If funding arrives late, replan scope before confirmation rather than cut replication after looking at outcomes.

The official ICML sources checked on October 14 did not yield a 2027 call or submission deadline. January 31 is the grant planning horizon, not a verified ICML deadline. Use early January as an internal buffer and confirm the official CFP before scheduling submission.

## 6. What remains to be supplied or settled

No new applicant facts are needed. Before execution we need: actual deposited funding (the user offers $50–100 RunPod credit); the prepared Gate B bundle and reference procedure; pre-wave-1 commitments; exact source/menu/split design; development cost and decision-variance measurements; practical task-loss/feasibility margins; a human-audit quote; and the frozen workload with its hard spending cap. GPT can complete this planning package now; these unknowns must not be filled with assumed grant awards or arbitrary seed counts. Weekly research time remains unspecified, so calendar targets are conditional.

## 7. Bounded literature refresh, October 14

- [The Unequal Influence of Bad Advice](https://arxiv.org/abs/2609.37914), v1 September 29: abstract re-read. Attribution-guided filtering with retraining and a black-box harmfulness comparison already exists. Exact-cost decision benefit remains a hypothesis here; this read is not an exhaustive novelty search.
- [Compute-Constrained Data Selection](https://arxiv.org/abs/2410.16208), v4 April 7, 2025: abstract re-read. Selection-versus-training compute is prior work; do not claim the tradeoff itself is new or infer its published ratios transfer to this setting.
- [Safety at One Shot](https://proceedings.iclr.cc/paper_files/paper/2026/hash/3d7cb780442f0d17c844dbe34997fab7-Abstract-Conference.html), ICLR 2026: official abstract re-read. A cheap single-example patch is a necessary baseline candidate. Exact recipe/applicability still requires full-paper/code inspection before inclusion.
- [ICML future meetings](https://icml.cc/Conferences/FutureMeetings) and official domain search: 2027 meeting mentioned; no 2027 submission deadline verified. The 2026 CFP must not be used as the 2027 deadline.

## 8. Review and routing record

GPT first pass was written before the Opus request in `.ai/inputs/main-study-restart-20261014/lead-first-pass.md`. The Opus alternatives brief withheld that preference while supplying shared historical decisions/reviews. Exact `claude-opus-5-5` / `max`, no time/turn cap; launcher evidence `tmp/claude-handoffs/20261014T144414Z-30954517`. Exit 1: weekly limit; no model identity returned. No Opus design response or effective effort is verified. The earlier recorded quota reset was October 15 at 14:30 IST; the current error displays the reset time only. Grant-drafting permission to use GPT does not extend to substantive research implementation.

Non-author GPT reviewer `/root/bluedot_budget_review` returned four material findings. All accepted: (1) phase order crossed the pre-wave-1 commitment boundary; revised Phases 1/2 now stop at 0b, commit rules, then finish Gate B; (2) retained primary contrasts/control/fallback were not fully mapped; section 1 now maps retained, proposed-amended and deferred elements and removes rewrite from the core; (3) quote planning/receipt logging did not enforce actual budget; section 3 requires per-attempt admission and worst eligible final-action/replication reservation while separating economic and physical costs; (4) practical-benefit wording did not retain cheap-reference dominance; section 3 now restricts the claim and requires fair common-menu inclusion or prospective exclusion. Source/code checks support these objections; no execution verified the proposed remedies.

Bounded readback: all four are adequately addressed **at roadmap level**, without verifying implementation, precision or a freeze. One remaining correction accepted: Phase 1 now makes wave 0b conditional on the frozen noise gate and records the failure/fallback path. Reviewer checked the $93.66 illustrative additional-credit arithmetic. Final source hashes and the review record are in `.ai/inputs/main-study-restart-20261014/`.

This is a role-separated critique, not independent empirical evidence. Subsequent user instruction “restart plan using gpt” supersedes the Opus prerequisite for this planning task. The GPT execution package adds source/metadata readback, a prospective R1–R3 job proposal, a pre-wave-1 commitment audit and an explicitly hypothetical replication screen. The main-study numerical precision analysis, scientific freeze and paid execution remain open; they are distinct from completion of this restart plan. Broader project routing settings are not rewritten.
