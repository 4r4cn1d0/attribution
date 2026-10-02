# Proposed revisions, Anthropic relevance, and ICML planning

2 October 2026. Planning advice for the current Roger Grosse proposal. These are recommended changes and conditional milestones, not an adopted experimental protocol or a promise of a positive result. The existing proposal and PDF remain unchanged.

## Revise the contribution, keeping the study narrow

Suggested working title: **When Does Training-Data Attribution Improve Safety Intervention Decisions?**

Suggested replacement for the Question paragraph:

> When do training-data attribution estimates provide information about the safety effects of finite post-training data edits beyond what short training runs and edit metadata already reveal? Can that information improve the choice of an edit under a fixed total compute budget, subject to prespecified limits on utility loss and over-refusal?

Suggested replacement for the Working hypothesis paragraph:

> My hypothesis is that attribution estimates capture aspects of finite-edit outcomes that short training runs systematically miss, and that these complementary signals can improve intervention selection. I will test prediction disagreement as one candidate signal while explicitly measuring agreement-but-wrong cases. The first comparison will hold the selector fixed and remove attribution inputs, allowing the baseline to reinvest their computation cost. A second comparison will supply the same predictions to a strong generic multifidelity selector. These comparisons distinguish the value of attribution information from the value of a new allocation rule. The study will characterize where the signal transfers and where it fails.

Other edits:

1. **Expand the prior-work paragraph.** Add [ADMIRE-BayesOpt](https://arxiv.org/abs/2508.11551) and [Data Mixture Optimization](https://arxiv.org/abs/2503.21023). Existing work already allocates cheap and expensive training experiments for language-model data choices. Explain the finite safety-edit target and the incremental-information hypothesis, rather than claiming allocation itself is new.
2. **Name the proposed scientific outputs.** A characterization of consequential prediction errors; a tested diagnostic or selection method that exploits attribution's added information; and a reproducible evaluation of constrained decision quality against total compute. These are intended contributions, not achieved findings.
3. **Stage the experiments.** Start with the existing single-model SFT/toxicity screen. Before expanding, measure full-run, short-run, scoring, and attribution-construction costs and check whether the predictors contain distinguishable information at all. Select a confirmatory setting that tests a specific transfer claim, such as safety degradation under further fine-tuning or adversarial evaluation, if supported by the pilot and budget. Do not silently expand to RLHF, universal unlearning, or several unrelated safety tasks.
4. **Make the success claim precise.** Require improved safety decision quality with acceptable constraint violations at matched total compute against strong alternatives. Choose practical effect margins and independent replication from development evidence before accessing held-out evaluation. Average safety effects and high-probability per-model feasibility are different possible targets; choose explicitly.
5. **Preserve the existing safeguards.** Keep separate data groups, untouched audit prompts, fresh post-selection seeds, uncertain reference optima, and all-cost accounting. Explain mechanisms through controlled interventions and theory where useful; an additional theorem is not automatically needed for an empirical contribution.
6. **Strengthen the relevance paragraph.** Explain how the work would help practitioners choose interventions for a measured safety regression and detect misleading cheap evaluations. Toxicity is an initial tractable test, not evidence of preventing catastrophic AI risks. The case for broader safety relevance must be established through a suitable evaluation and argument.

The high-novelty version would establish when attribution contributes complementary information and how that changes decisions beyond existing methods. A result showing a small gain from an extra feature on one benchmark may remain incremental even if reproducible. The earlier conditional 4/5 discussion describes a possible contribution, not the novelty guaranteed by executing this document.

## Anthropic relevance

The user's abbreviation “FT” is unresolved at drafting time. A clarification was requested; these two interpretations should not be conflated.

**Full-time role:** A successful version could be a relevant research work sample for alignment or safeguards research engineering. The [current Alignment Research Engineer / Scientist role](https://job-boards.greenhouse.io/anthropic/jobs/4631822008) emphasizes thorough ML experiments, empirical research experience, significant engineering experience, and collaboration. A proposal alone does not establish those abilities or determine candidate competitiveness. A reproducible repository, interpretable evidence, clear individual contributions, and the ability to explain and debug the work would strengthen the work sample. No CV, interview performance, or overall candidacy was assessed.

**Fellows Program:** The [current AI Safety & Security listing](https://job-boards.greenhouse.io/anthropic/jobs/5183044008) describes four months of full-time empirical research, technical assessments, a research discussion, and mentor/project matching. This proposal could support such a discussion; a completed ICML paper is not presented as a prerequisite. The listing currently advertises a January cohort. Its eligibility requires location and work authorization in the US, UK, or Canada and says the program does not sponsor visas. The user has not supplied eligibility details. A January-start fellowship should not be assumed to fund this autumn's work or make a January paper deadline feasible.

Anthropic's [research directions](https://alignment.anthropic.com/2025/recommended-directions/) emphasize the connection to risks from advanced systems. My relevance assessment is an inference from public descriptions, not feedback or endorsement from Anthropic.

## Time estimate and conditional ICML target

As of this review, an official ICML 2027 submission date could not be verified. The [2026 call](https://icml.cc/Conferences/2026/CallForPapers) set the abstract deadline at January 23 and the paper deadline at January 28. A January 2027 deadline is a planning assumption based on prior timing, not an announced date.

My planning estimate for a focused solo researcher with adequate ML implementation skills and reliable GPU access is **roughly 3–5 months** for a submission-quality study, conditional on finding a useful result. A **12–16-week route** is possible if the initial hypothesis survives promptly and scope stays narrow. Part-time work, limited compute, or learning the training stack may stretch the project to **6–9 months or more**. These are estimates, not measured runtimes or a guarantee that a publishable discovery occurs.

Illustrative fast schedule starting October 2, assuming approximately full-time effort:

| Period | Deliverable and decision |
|---|---|
| Weeks 1–2, through October 16 | Final distinguishing hypothesis; closest-baseline specification; executable training/evaluation pipeline; measured run and attribution costs. |
| Weeks 3–5, through November 6 | Bounded pilot and replicated check of incremental attribution information. Decide whether this mechanism merits the main study. A failed screen prompts reframing and a new schedule. |
| Weeks 6–10, through December 11 | Frozen selection comparisons, held-out evidence, and the core figures. Draft methods and results while experiments run. |
| Weeks 11–13, through January 1 | Transfer/robustness checks, side effects, complete cost analysis, and manuscript consolidation. |
| Weeks 14–16, through January 22 | Full draft, independent critical reading, targeted repairs and final reproducibility checks. Aim for a complete draft by January 8. Adapt to the actual conference deadline once verified. |

This leaves little buffer if ICML again closes in late January. Treat **November 6** as the key checkpoint for maintaining this timetable and **December 11** as the checkpoint for having the core empirical story. These are recommended project milestones, not calendar events, automations, or externally imposed deadlines.

Submission readiness requires a supported distinguishing claim, fair comparisons, correct uncertainty and side-effect evaluation, and reproducible evidence. A calendar alone cannot establish readiness. If the hypothesis fails, a different publishable finding may emerge, but that cannot be assumed in advance. Neither submission readiness nor a strong work sample guarantees ICML acceptance or Anthropic hiring.

## Scope and provenance

GPT prepared this editorial and planning note using the existing proposal, prior Opus/GPT critiques, and public Anthropic/ICML sources checked on October 2. This is framing and advice, not substantive implementation, a new proof, or a powered experimental design. No new model delegation, study, spending, application, external message, or publication was initiated. The requested model workflow and experimental scope are unchanged. User time and compute remain unconfirmed at drafting time.
