# BlueDot Rapid Grant — $6,000

**Unsubmitted application draft.** These answers map to the live form inspected on 13 October 2026. The external Chrome and in-app forms are updated and left open, unsubmitted. The user authorized filling all three forms and explicitly prohibited submission.

Application: https://airtable.com/appeeZXWP0NdMvWYd/paggDLIdBeveEPLs7/form

Applicant: Aayush Ghosh · rishi.gh2002@gmail.com · Independent researcher · West Lafayette, Indiana, USA.

## One-sentence summary

Test whether training-data attribution improves safety-repair choices beyond strong classifiers and short training runs, after charging its full cost.

## Project

Benign fine-tuning can weaken an instruction model's safety behavior. When deciding which training examples to edit, teams can use content classifiers, training-data attribution or short trial runs. Attribution is expensive, and its signal may overlap with simple features such as gradient magnitude, answer length and data format.

I will test whether attribution adds practical decision value after its cost is charged. A selector with attribution and a strong selector without it will receive the same permitted metadata and classifier inputs and equal total compute budgets. Both may use short training runs; the selector without attribution can reinvest the saved cost in additional trials. Harmful-compliance scores, benign over-refusal and task performance will be measured separately.

The project is already underway. Next I will review and cost the remaining diagnostic and development work, then freeze a feasible held-out selector comparison with fresh menus, training seeds and evaluation prompts. The design will include gradient, length and format controls and strong cheap repairs. All reference training, attribution, trials and final evaluation must be charged and deduplicated. The $3,700 compute allocation is a spending ceiling; it is not proof that the broad study or larger-model replication fits.

Outputs through 31 January 2027 are a documented empirical comparison, complete cost records, a human audit of automated measures, and a manuscript with reproducible artifacts where release terms permit. A negative or inconclusive result is useful evidence about the tested mechanism. ICML 2027 is a submission aspiration; acceptance and a complete larger-model study are not promised.

## How it reduces AI risk

Models are frequently adapted by users who did not train the original model. If ordinary fine-tuning erodes safety, developers need reliable ways to choose a repair. An expensive diagnostic that adds little information can divert resources from better repairs; a misleading metric can also favor blanket refusal while harmful compliance remains.

This study could help safety researchers decide when attribution is worth using and when cheaper classifiers or trial runs are better. The path to reducing advanced-AI risk is indirect: it tests one component of maintaining safety during adaptation on small open models. It does not establish safety of frontier systems. Direct attribution-guided safety-repair precedents already exist; the hypothesis is incremental value against a strong alternative at matched cost.

## Progress so far

I have completed a precursor manuscript, Same Recipe, Different Fate (waiting for arxiv approval): https://drive.google.com/file/d/1Fk0M_iA8oYc_HLJvoceWlcd6nF_dxkoZ/view?usp=drivesdk

It compares six instruct models from OLMo-2, Llama-3 and Qwen2.5, at about 1B and 7-8B, on matched benign fine-tuning data with three seeds per main recipe cell. It studies how recipe choices change safety erosion, reports the inconclusive larger-model replication and over-refusal tradeoff, and checks automated-judge limitations with a blind human read. Anonymous analysis code/numerical inputs: https://anonymous.4open.science/r/same-recipe-different-fate-4812/ . This artifact supports numerical reproduction, not new training runs. All findings are development evidence. This establishes an empirical foundation and working pipeline for the larger ICML-targeted study of whether attribution improves safety-edit decisions after cost; it does not demonstrate attribution benefit.

I built the training/evaluation pipeline and maintain experiment manifests, frozen rules and cost records. In development, one epoch on 4,800 ordinary Dolly examples increased OLMo-2-1B-Instruct's Qwen3Guard Unsafe share from 3.2% to 46.7%, 46.8% and 51.3% across three seeds: a mean increase of 45.1 percentage points. The reading rule was fixed before the two fresh seeds, after the first seed was known. Granite Guardian agreed on the direction, and HarmBench's classified harmful-compliance change averaged 30.3 points.

I also examined OLMo, Llama and Qwen under two recipes in a descriptive side study and published the findings and limitations in Scratch Work. A small component intervention is only a single-seed pilot; it does not establish a general mechanism or scale effect.

The repair pilot produced a large automated unsafe-score reduction but severe benign over-refusal, failing the no-damage criterion. A 50-answer blind development read pooled five groups; I was the sole reader. Only 13 of 39 Qwen3Guard-unsafe answers were rated to provide usable help. This motivates the proposed human audit and limits claims from automated scores.

The Gate B diagnostic protocol is frozen and its anchor completed; further GPU work remains paused pending resources and a reviewed plan. Recent literature and methods reviews sharpened the question toward cost-matched, held-out decision value. No attribution advantage has been demonstrated.

## Why me

I am an independent researcher with experience in technical AI safety, agent oversight and empirical ML. In SPAR, I am a research mentee on Belinda Li's introspection-training project, studying whether model verbalizations agree with internal activations. As an Apart Research fellow, I work under Erik Meijer on static verification for agent workflows, including Z3 and a reproducible AgentDojo evaluation harness. My earlier ML engineering internships at Mercor and Addepar add experience with evaluation pipelines, model systems and production monitoring. I am an incoming Sakana AI research intern starting January 2027; that future role is separate from this USA-based funded project.

My Countersign work on termination supervision was accepted at the NeurIPS 2026 Meta-Agents workshop. My GLEE strategic-agent paper was accepted as a Spotlight at the NeurIPS 2026 Interpreting Agent Behavior workshop; the agent placed second in the GLEE 2026 agent track. These are workshop and competition outcomes, not NeurIPS main-track acceptances. My earlier contributive-attribution paper, Order Selects Policy, is submitted to ARR, while the safety-edit study proposed here remains research in progress.

For this project, I have built the training/evaluation pipeline, completed multi-seed development checks and recorded failed repairs and measurement limits. The anonymous code links provide inspectable research artifacts; the attribution link is an earlier development snapshot, not complete current results. I publish progress in Scratch Work and completed BlueDot's Future of AI course; certificate issued 8 October 2026. The grant would support the main ICML-targeted attribution study's next reviewed phases, without assuming an attribution win.

Resume: https://drive.google.com/file/d/1Z4HT4ZbyywXwLTUz9YgGn6YYnAWwciGE/view?usp=sharing

## Budget

$6,000 requested through 31 January 2027:

$3,700 compute and judging: provisional ceilings of $100 for remaining diagnostic work, $600 for unfinished development and $3,000 for the held-out selector comparison. Completed jobs are excluded. The run roster, attribution overhead and achievable replication must be measured and reviewed before spending.

$800 human measurement audit: 500 unique answers x two raters x a provisional $0.80 per rating. This is an unquoted estimate; recruitment, training and adjudication must fit or be re-costed.

$700 retained project storage: 820 GB on stopped project pods x $0.20/GB/month x four months = $656, plus $44 headroom. Retention is an assumption, not a commitment; unrelated volumes and new/backup storage are excluded.

Up to $800 for Codex and Claude: $100 per month each for up to four remaining billing cycles before 31 January. If October is already paid, three cycles total $600. Previously paid or separately funded months are excluded.

These are prospective spending caps, not supplier quotes or proof of full-study adequacy. Mandatory fees and taxes must fit the approved caps by reducing workloads or revising the budget with the funder; no automatic top-up is assumed. No salary, living costs or travel is requested. Any supplied compute replaces the corresponding cash expense.

## Without funding

I would continue writing, literature review and low-cost analysis, while keeping the GPU-dependent next phase paused. Funding would enable a coherent, bounded decision comparison and a human measurement audit. If only part of the request is funded, I would cost a narrower scope and agree it with BlueDot before execution. Additional datasets and larger-model comparisons depend on resources; I will seek agreement before materially reallocating the grant.

## Public work links

Resume: https://drive.google.com/file/d/1Z4HT4ZbyywXwLTUz9YgGn6YYnAWwciGE/view?usp=sharing
Precursor preprint: Same Recipe, Different Fate (waiting for arxiv approval): https://drive.google.com/file/d/1Fk0M_iA8oYc_HLJvoceWlcd6nF_dxkoZ/view?usp=drivesdk
Precursor analysis code/numerical inputs: https://anonymous.4open.science/r/same-recipe-different-fate-4812/
Attribution development code/protocols (earlier snapshot): https://anonymous.4open.science/r/safety-data-edits-ba84/
Countersign research source/evidence: https://anonymous.4open.science/r/countersign-07A2/
Current research progress: https://spiderishi.substack.com/p/a-recipe-for-disaster-sometimes
Repair pilot and limitations: https://spiderishi.substack.com/p/first-make-sure-a-fix-can-work

## Other funding / feedback

I am also preparing an unsubmitted $3,000 request to the EA Funds Transformative AI Fund for a conditional extension with additional fresh menus/seeds or a targeted scale comparison, and an unsubmitted request for up to $2,000 of engineering support from the AI Alignment Foundation. Neither has been awarded. Engineering support may be a team allocation rather than cash, with no assumed monetary valuation.

BlueDot covers the core budget; the extension is conditional on a funded and completed base phase. Engineering labor is distinct from software subscriptions and research compute. Each workload and expense line is allocated to one funding source; consolidated invoices are split using a documented allocation. I will disclose filing/award changes and obtain agreement before changing the funded scope.

## Public report URL

https://spiderishi.substack.com/p/a-recipe-for-disaster-sometimes

## Choices

Compute & tools; Research costs. BlueDot course alum: Future of AI, certificate issued 8 October 2026. Amount: $6,000. Named public reporting: Yes. Funder referrals: Yes. Profile / résumé: https://drive.google.com/file/d/1Z4HT4ZbyywXwLTUz9YgGn6YYnAWwciGE/view?usp=sharing.

## Internal provenance and limits

Exact text: `.ai/inputs/bluedot-budget-20261013/live-form-answers.json`. Verified materials and claim limits: `2026-10-13-portfolio-evidence.md`. The user authorized GPT for these grant drafts; future project routing is unchanged. This funding proposal does not authorize training or establish full-study feasibility. The live forms and final declarations remain unsubmitted. Payment-account country is unconfirmed and is not a current application field.
