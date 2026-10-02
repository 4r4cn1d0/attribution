# Measurement audit of the first calibration

2 October 2026. This is a development audit of the completed engineering pilot, not confirmation of an attribution effect.

Two fresh GPT worker contexts assessed the same 50 shuffled unique received-prompt/response pairs. Neither received arm, seed, scorer output, mapping, project history or the other's annotations. Each wrote a rubric before annotation. Both are model-assisted judgments from the GPT family, not human gold or statistically independent evidence. Exact input prefixes were supplied; hidden continuation was never inferred. The mapping was joined only after both label files had been saved and hashed.

Both label sets identify the same three responses as material harmful assistance, all concerning one source prompt. The original ToxicBERT threshold flags exactly those three unique responses, and neither labels any other output harmful. Thus this audit does **not** show an observed harmful-assistance false negative in these prefixes. It also does not validate general unsafe-response detection: there are only12 distinct prompts, the sole positive prompt is repeated, and the two intended constructs differ. The response-toxicity rubric has a disputed sexual-exploitation boundary: one annotator marked those three uncertain, the other yes. Broader harassment/toxicity and context-dependent harmful assistance must be reported separately.

The audit agrees on the refusal category for47/50 pairs. Helpfulness judgments are much weaker than raw safety flags suggest: the first annotator rates only5/50 adequate,26 partial and19 unusable; the second records four unjudgeable cases. These selected unique-output counts do not estimate population rates. Some supplied prompts are intrinsically unfinished even when the pipeline did not truncate them, so that flag is not a complete context-quality measure.

Generation truncation is a demonstrated engineering limitation:77/108 original generations reached64 new tokens;41/50 unique audit pairs contain a capped generation. A non-harmful prefix does not establish safety of a completed answer. The old512-token training/prompt handling also cut some inputs and targets. The expanded study must log exact received context, use a development-calibrated generation limit, retain stop/censoring indicators, and report sensitivity to unresolved completions instead of silently calling them safe.

Before interpreting safety-edit choice, the new study needs a frozen context-aware outcome scorer, a construct-matching strong content baseline, unseen outcome prompts, and useful-response/refusal checks. Human adjudication remains outstanding. The initial expanded result must therefore be described as a classifier-defined, model-audited feasibility study, with human validation required before claiming a validated human safety effect.

Evidence: `.ai/inputs/study-v2-20261002/gpt-audit-note.md`, `gpt-second-audit-note.md`, both label JSONLs and `joined-audit.json` (frozen label hashes and descriptive joins); original run artifacts and costs remain in `2026-10-02-minimal-safety-calibration-results.md`. No original output or review was overwritten.

## Expanded development measurement, 2 October (before held-out work)

The pinned Qwen3Guard response-template implementation was checked against its
source and tested on the old50pairs. It returned18valid Unsafe,28Safe,4invalid
(input-only Jailbreak categories; zero control-string rejections). Both frozen
GPT annotations identified3material-harmful-assistance prefixes. Fifteen additional
Unsafe labels include broad sexual-policy differences and neutral/prefatory or
repetitive responses. These are construct disagreements, not an estimated
false-positive rate against human gold. See the preserved
[construct review](../../.ai/inputs/study-v2-20261002/guard-construct-review.md).

A fixed four-cell crossover combined the old offensive-wrapper and quiche
prompts with a repeated-name response and a generic refusal. The original
repeated-name/offensive-wrapper cell reproduced Unsafe/Unethical Acts. All other
cells were Safe. This establishes response sensitivity in this tiny control,
while preserving a disputed contextual flag; it does not validate harmfulness
or eliminate differential judge bias. The initial diagnostic-input schema error
was preserved and corrected before inference. No frozen annotations or parser
rules were changed to obtain these labels.

A fresh GPT context annotated all136emitted baseline development responses using
only shuffled prompt/response/stop-reason data and official policy documentation.
It identified2material-harmful-assistance responses and broad-policy judgments
125Safe/7Controversial/2Unsafe/2uncertain; all6capped outputs visibly repeated.
The judge returned120Safe/9Unsafe/6Controversial/1invalid on these same136outputs.
These are model-assisted assessments, not human gold or guaranteed independent
errors. They do not validate later SFT or held-out outputs. Preserve distinctions
between the pinned judge's Unsafe-flag incidence, censored/ambiguous sensitivity
bounds, material harmful assistance, ARC accuracy and benign-response refusal.
Data and coverage checks: full-dev-blind-context.jsonl, full-dev-gpt-labels.jsonl,
full-dev-gpt-audit.md and full-dev-joined-audit.json under the dated .ai inputs.

## Full calibration and post-training audit

All five seed1101 calibration trajectories and their doubled-output-ceiling
sensitivities are retrieved.31sealed runs (including the baseline initial state)
pass own-file, dependency and training-stream verification. Across15same-state
q/e1/e3 comparisons on the same136development prompts, every original token
prefix and every EOS-finished output is identical at1024versus2048. Main Unsafe
counts do not change in any cell. Four prompt/cell label or refusal pairs change;
the summed risk cap count falls90to88. These are repeated prompts and states,
not2040independent validation cases. Persistent caps remain; these checks do not
validate an uncensored response endpoint or classifier construct. Evidence:
`tmp/study-v2-20261002/cap-comparison-complete.json`.

A separate fresh-context GPT annotator applied the previously fixed rubric to
100post-training pairs: the same12risk and8benign prompts across5e3arms, selected
by a recorded outcome-independent hash rule and shuffled without arm/score
metadata. There are20prompt clusters and63unique prompt-response pairs. Exact
coverage/schema and label hashes were frozen before joining the mapping.
The annotator records98no/2uncertain material-harm judgments and92Safe/
6Controversial/2uncertain policy judgments. Guard records86Safe/5Controversial/
9Unsafe; among its9Unsafe labels GPT records6Safe/2Controversial/1uncertain.
Neither judge is human gold; no false-positive rate or treatment effect is
established by these pooled model-assisted counts. This is evidence to inspect
construct boundaries and within-prompt changes before claiming a safety benefit.
Evidence: posttraining-audit-frozen.json, posttraining-gpt-audit.md and
posttraining-joined-audit.json in the dated .ai inputs. Targeted construct
adjudication is recorded separately without changing any frozen label.

A second fresh-context, contrast-focused GPT assessment of the explicitly
enriched9-output packet retained no demonstrated material-harm difference for
the suggestive-image pair. It retained the Portuguese opening's modal ambiguity,
the age/sexualization uncertainty of both transformation stories, and the
usefulness/refusal differences separately. These further model-assisted
judgments reinforce the interpretation limitation; they are not independent
human validation, classifier tuning or new primary labels. See
contrast-gpt-adjudication.md and its frozen-hash receipt.
