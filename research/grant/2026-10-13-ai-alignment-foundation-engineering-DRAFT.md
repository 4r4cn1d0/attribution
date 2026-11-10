# AI Alignment Foundation — up to $2,000 engineering support

**Unsubmitted application draft.** These answers map to the live form inspected on 13 October 2026. The external Chrome and in-app forms are updated and left open, unsubmitted. The user authorized filling all three forms and explicitly prohibited submission.

Application: https://www.aialignmentfoundation.org/approach/apply

Applicant: Aayush Ghosh · rishi.gh2002@gmail.com · Independent researcher · West Lafayette, Indiana, USA.

## Brief bio

I am an independent researcher working on technical AI safety, agent oversight and training-data attribution. I am a SPAR research mentee on Belinda Li's introspection-training project and an Apart Research fellow working with Erik Meijer on static verification for agent workflows, using Z3 and AgentDojo. I previously held ML engineering internships at Mercor and Addepar, and am an incoming Sakana AI research intern starting January 2027. My Countersign termination-supervision paper was accepted at the NeurIPS 2026 Meta-Agents workshop; my GLEE paper was a Spotlight at the NeurIPS 2026 Interpreting Agent Behavior workshop, with second place in the agent competition track. Earlier contributive-attribution work, Order Selects Policy, is submitted to ARR. For the ICML-targeted safety-edit study proposed here, I built the training/evaluation pipeline and completed multi-seed development checks, reporting failures and measurement limits in Scratch Work. Anonymous research artifacts and my resume are linked below. This project's funded work remains USA only. I also completed the safety-erosion precursor manuscript Same Recipe, Different Fate (waiting for arxiv approval), which establishes development evidence for the larger study. Resume: https://drive.google.com/file/d/1Z4HT4ZbyywXwLTUz9YgGn6YYnAWwciGE/view?usp=sharing

## Project title

Engineering a reproducible, cost-matched comparison of safety-repair selectors

## TL;DR

Up to $2,000 engineering support, or a bounded team allocation, for one execution adapter that compares repair selectors with and without attribution and records their full costs.

## Proposal — under 500 words

Benign fine-tuning can weaken a language model's safety behavior. Teams can try data repairs, classifiers, attribution diagnostics or short trial runs, but it is unclear whether attribution improves the final choice once its computation is charged. I am studying that question on open models, measuring harmful-compliance scores, over-refusal and task performance separately.

I built the training/evaluation pipeline and observed erosion across three OLMo-2-1B seeds. A repair pilot exposed over-refusal; a small applicant-only human read showed that automated Unsafe labels do not establish broad harm or human-validated safety. Attribution benefit remains unmeasured. Direct attribution-repair precedents exist, so the hypothesis is incremental decision value against strong cheap controls.

I seek up to $2,000 for engineering support, if cash is available, for one reproducible execution adapter on one model/data path. If your program supplies an engineering team, I would welcome a bounded work package with agreed scope; I am not assigning a $2,000 valuation or assumed hours to team support.

The adapter would run an existing selector with and without attribution, using the same permitted metadata and classifier inputs and equal total compute budgets. Both arms can use short training runs; the arm without attribution can spend the saved cost on extra trials. It would produce a versioned job manifest, record reference/attribution/trial/final-model costs including failures, enforce the reviewed budget rule, and provide validation fixtures and instructions. Each workload and expense line has one funding source; consolidated invoices use a documented allocation. Research design and interpretation remain with me; execution starts from a reviewed protocol.

I am preparing separate, unsubmitted requests for $6,000 from BlueDot for the core phase and $3,000 from the Transformative AI Fund for additional runs/infrastructure. Neither is awarded. This request is for engineering labor, distinct from subscriptions and research compute; supplied compute would replace corresponding cash expenses.

The immediate output is a reproducible comparison and cost ledger. It could inform which diagnostics are worth using to maintain safety during adaptation; its link to advanced-AI risk is indirect. This is a bounded empirical project, and I recognize that your emphasis on field-making directions may be a less direct fit. I would value support if this specific engineering artifact is useful to your program.

## First experiment

First implement and validate the adapter on one existing development model/data path: manifest, complete cost accounting, matched budget enforcement and fresh selected-arm evaluation. Once the reviewed protocol and resources are agreed, conduct a bounded pilot comparing the selectors at one feasible budget. The scientific signal is the difference in chosen-arm outcomes after costs; engineering success is a reproducible execution with a complete ledger, including failures. This is an early cycle, not a statistically decisive-result promise or a committed team schedule.

## Relevant links

Resume: https://drive.google.com/file/d/1Z4HT4ZbyywXwLTUz9YgGn6YYnAWwciGE/view?usp=sharing
Precursor preprint: Same Recipe, Different Fate (waiting for arxiv approval): https://drive.google.com/file/d/1Fk0M_iA8oYc_HLJvoceWlcd6nF_dxkoZ/view?usp=drivesdk
Precursor analysis code/numerical inputs: https://anonymous.4open.science/r/same-recipe-different-fate-4812/
Attribution development code/protocols (earlier snapshot): https://anonymous.4open.science/r/safety-data-edits-ba84/
Countersign research source/evidence: https://anonymous.4open.science/r/countersign-07A2/
Current research progress: https://spiderishi.substack.com/p/a-recipe-for-disaster-sometimes
SPAR project: https://www.sparai.org/projects/f26/recNKpeygLfUGyGiz/

## Anything else

The requested cash cap is $2,000 subject to agreed scope and quote; no hourly rate or delivery period is assumed. A bounded team allocation is an alternative. If the base phase is unfunded, I would discuss a revised engineering-only scope before work begins. Main GPU work is paused. The planning horizon is through January 2027, with ICML as an aspiration, not an acceptance promise. The linked attribution artifact is an earlier development code/protocol snapshot; the Countersign link provides a public research source/evidence release. Neither implies that the proposed held-out safety-edit comparison has been completed. The precursor manuscript Same Recipe, Different Fate (waiting for arxiv approval) reports development evidence rather than a completed attribution comparison.

## How I heard about the program

Web search

## Internal provenance and limits

Exact text: `.ai/inputs/bluedot-budget-20261013/live-form-answers.json`. Verified materials and claim limits: `2026-10-13-portfolio-evidence.md`. The user authorized GPT for these grant drafts; future project routing is unchanged. This funding proposal does not authorize training or establish full-study feasibility. The live forms and final declarations remain unsubmitted. Payment-account country is unconfirmed and is not a current application field.
