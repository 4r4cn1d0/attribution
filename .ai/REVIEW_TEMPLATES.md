# GPT questions and red-team briefs

## Independent alternatives

Given the outcome, constraints, and actual inputs, propose the simplest viable
approach plus the strongest alternative. Identify assumptions, failure cases,
costs, and a decisive comparison. Do not read the other model's proposed answer
before returning this first pass. Record the context you actually received.

## GPT questioning Opus

Inspect this objection against your actual implementation or argument:

- Artifact and exact location:
- Counterexample or competing approach:
- Why it could invalidate an acceptance criterion:
- Smallest check and expected distinguishing outcomes:

Reply to each point with evidence, a correction, or a reasoned disagreement.
Separate “not a problem” from “not tested.” If a fix changes scope, explain it to
GPT before implementing dependent work. Do not run an open-ended debate loop.

## Non-author GPT red team

Review the supplied artifact against the stated objective and acceptance criteria.
Do not assume Opus's report is correct. Find concrete correctness, scope, leakage,
statistical, reliability, and cost failures. Prefer reproducible counterexamples.
For each finding return severity, location, consequence, and a decisive test.
Do not manufacture findings or equate model disagreement with a defect.
Do not edit files or dispatch agents. Report to the GPT lead.

## Attribution research checks

- Is the target a finite deletion mean, a particular model, or a distribution?
- Does the baseline estimate that same target?
- Does the cheap predictor vary informatively across seeds within each request?
- Are predictor construction and all training costs included?
- Are selection, stopping, multiplicity, and reference uncertainty handled?
- Are sources verified and novelty distinguished from established PPI methods?
- What result would falsify the mechanism or change the paper's main claim?

No reviewer may treat agreement as empirical evidence or a promise of acceptance.
