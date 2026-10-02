# Stage B decisions pending development measurements

2 October 2026. Lead design notes, **not a frozen confirmation protocol**.
No expanded development or confirmation outcomes have been generated at this entry.
The user removed the dollar cap; this is not a reason to inflate the study or to
confuse an initial experiment with a submission-ready confirmation.

## Keep separate targets

1. H1 is a development comparison of matched predictor procedures with X0 versus
   X0 plus a frozen attribution feature. Group cross-fitting and paired seed
   outcomes are required; repeated menu resampling is not additional replication.
2. H2 is the held-out decision comparison. Attribution's setup and queries cost
   money. S- receives the same total quoted acquisition budget and may reinvest
   the saving in observations; it must not run out of an artificially fixed pool.
3. A new allocator advantage is not claimed. The two methods use the same
   acquisition/choice algorithm and tuning budget; the input feature differs.
4. Fresh final deployments provide an unconditional safety-rate contrast with
   separate utility and refusal outcomes. Whether this is primary or secondary
   is unresolved until the inference design is reviewed. It cannot silently
   replace the existing expected-feasibility-adjusted estimand.

## Measurement / features

- Use a strong context-aware classifier on full training prompt/response pairs.
  Consider continuous class scores in addition to parsed hard labels: normalize
  the teacher-forced likelihoods of the three complete canonical Safety lines
  under the official template. These are normalized label-sequence scores, not
  calibrated probabilities. Test token boundaries and include the newline; no
  training label, benchmark family, label-bearing source ID or row ordering leaks
  into X0. This is an implementation follow-up item, not an existing capability.
- Input length summaries and edit size are legitimate metadata. Construction
  labels are auditor-only. Hidden reference scores are unavailable to both
  methods until choices and acquisition transcripts are locked.
- Both methods must be able to USE the same30 fixed target query examples, not
  merely have nominal file access. Add fixed word unigram/bigram TF-IDF relevance
  features fitted once on training text plus query text, excluding all outcome
  prompt banks. Two views: prompt, and prompt+response. For each removed row take
  its maximum cosine to a query; each group gets mean/sum/max for each view (six
  features). Freeze tokenization, IDF and aggregation before development outcomes.
- At purchased checkpoints, measure the same query objective without gradients:
  mean per-example response NLL including the training EOS convention, over all30
  queries. X0 includes edit-minus-paired-a0 short-checkpoint query NLL. This is a
  direct target-conditioned observation, not a safety outcome or causal theorem.
  Charge its forward passes identically; do not give either method unpaid data.
  The prespecified gradient feature is the additional input in S+.
- Frozen gradient proxy choice uses only development. Do not select a proxy,
  classifier or stopping rule from held-out outcomes.
- Censored generations and malformed judge outputs stay unresolved. Report
  bounds/sensitivity; do not silently drop them or label them safe.
- The finite hidden prompt banks support a conditional finite-bank estimand.
  More training seeds do not establish broader prompt or setting generalization.

## Acquisition skeleton under review

Use matched ridge predictions for safety change, capability loss and refusal
change, with identical group-fold splits and hyperparameter grids. Scale features
using training folds only. Predictor evaluation should include decision-relevant
loss and feasibility error, not only MSE. Additional dimensions change model
capacity even with matched regularization procedures; describe this accurately.

Both methods buy the common short screen. Reserve the fresh chosen-model training
and deployment evaluation before adaptive purchases. S+ purchases the a0
checkpoints and attribution passes it needs; S- purchases a full a0 when its
paired full comparison needs one. Reuse an already paid artifact once. A short
checkpoint continued to full fidelity remains one observation of one seed.

Promote candidates by a shared, development-frozen rule balancing predicted
safety improvement and possible feasibility; use opaque fixed tie-breaking.
Repeat promising candidates on fresh paired seeds. A final edit requires at
least two independent full observations and must satisfy the shared estimated
constraint rule; a0 is always available. Development uncertainty bands guide
acquisition only, and are not certified confidence sequences.

Unresolved details to freeze before confirmation: exact promotion/repetition
order and fallbacks; how additional short repeats update predictions; all
affordable operations when a full continuation will not fit; the minimum
validation rule; seed derivation; immutable choice and final-run receipts.

## Cost invariants

- Freeze operation tariffs from development by fidelity, input shape and already
  paid checkpoint. No future run time or output length is revealed for free.
- Maintain a separate actual-cost ledger. Finish and charge a runtime overrun;
  do not replace its seed, censor the outcome or revise the tariff afterward.
- Equal quoted budgets are not equal measured cost. A stronger practical claim
  needs a prespecified measured-cost tolerance and uncertainty gate as well as
  outcome and feasibility checks.
- Retain failed-attempt costs and use a frozen technical retry rule. Idleness,
  setup and reference-only research computation belong in total expenditure.
- Charge counterfactual policy ledgers even if common observations are physically
  cached in the study. Report calibration/tuning costs without amortization first;
  any deployment-count amortization is fixed prospectively.
- Report indivisible-operation leftovers. Do not choose the primary budget after
  seeing where the outcome comparison happens to favor attribution. Include a
  prespecified one-extra-observation sensitivity for S- if appropriate.

## Precision and scope

The number of training or selector seeds is not yet fixed. Measure development
variance and actual throughput first; simulate the intended paired/block analysis
including shared reference uncertainty. Do not call a convenient seed count
powered, and do not confuse confidence-interval width with post-hoc power.

Near-boundary expected feasibility cannot be inferred by treating a noisy
reference mean as truth. Preserve uncertain arms and report worst-case conclusions
over plausible feasibility assignments, or use a justified inference method.
The original best-arm term cancels from D_info, but feasibility uncertainty does
not. A simpler fresh-deployment comparison, if adopted prospectively, must retain
separate absolute and comparative utility/refusal checks and state its weaker
claim about per-edit feasibility.

The initial study may yield a negative or inconclusive result. That constrains
this setting and proxy; it does not end the project or establish a general limit
on attribution. No claim of novelty, ICML readiness, or unlearning follows merely
from completing the pipeline.

Implementation separation: after the Stage A engine is accepted and frozen, put
the Stage B selector/analysis in a new sibling package (for example
`experiments/safety_decision_policy/`) with its own pinned source identity. The
engine intentionally hashes all safety_selection and reused minimal_safety source
files. Adding unrelated policy modules inside that package would invalidate
already measured development checkpoint identities and unnecessarily prevent
continuation. Do not relax those checks or rewrite old receipts to avoid this.
Necessary engine fixes still require a new, explicit code version and appropriate
reverification. Initial evaluation bank sizes are calibration choices: final
precision/workload planning must assess whether more of the available ARC
questions should be used, rather than inherit128 as an unexplained final limit.

## Non-author inference review and prospective resolution

A non-author GPT reviewer recommends paired fresh deployments for the initial
study's directly measured contrast. For locked choices A-minus and A-plus in
block b and fresh shared training seed z_b, measure
Y_b = F(A-minus_b; z_b) - F(A-plus_b; z_b). The independent unit is the complete
block, including selector randomness and final training randomness. Common
prompt items do not multiply the training sample size. Compare policy-average
utility loss, refusal increase, and full cost separately and inspect all selected
arms, including adverse cases. An improvement in these averages is **not** proof
that every selected edit is feasible in expectation.

Lead resolution: this is a useful initial diagnostic and a simpler route to
executing the held-out comparison. Preserve the proposal's original H2 target
and label it unestablished unless its distinct uncertainty checks actually pass.
Do not relabel this diagnostic as D_info or mark the original gate satisfied.
This change is recorded before any expanded outcome is generated.

For the original convention, let q_a = F(a)-F(a0),
d_a = P(S-minus=a)-P(S-plus=a), and
I_a = 1[L_a <= tau_L and O_a <= tau_O]. Then
D_info = sum_a d_a I_a q_a. Construct simultaneous regions for these primitive
means, resampling whole selector blocks and whole reference-seed vectors rather
than each arm independently. Classify an arm as definitely feasible only if both
constraint upper bounds pass, definitely infeasible if either lower bound fails,
and otherwise unresolved. Project the region over all admissible feasibility
assignments. Bounded-mean intervals plus an explicit error allocation give a
conservative sensitivity result. A bootstrap of the thresholded plug-in D alone
does not resolve its boundary discontinuity.

Counterexample retained: a policy that selects a safety-improving but severely
utility-damaging edit half the time and an offsetting utility-improving edit the
other half can pass average-utility checks while its useful safety edit is
infeasible under the original convention. This is why the two claims stay apart.

Precision planning should cover the safety, utility, refusal and cost endpoint
family using development paired-policy variation and a conservative SD range.
Target interval widths relative to prespecified meaningful margins. Simulate the
actual procedure, including sparse outcomes and mixtures of choices; a zero
pilot SD is not evidence of zero uncertainty. An arbitrarily near-boundary arm
can remain unresolved at every practical sample size. Do not spend indefinitely
to force a feasibility classification or increase n until a positive result.

## Accepted simple acquisition schedule (before development outcomes)

A non-author review first proposed a permanent top-two shortlist. The lead rejects
that restriction: it could prevent the cheaper comparator from spending savings
on breadth after a wrong initial ranking. Use all12 options when budget permits.
This is a specified simple policy comparison, not a claim about an optimal or new
allocator. Rankings do not adapt after the initial short screen.

After the common screen and S+ attribution purchases, freeze each method's order
from its matched development-fitted ridge predictions. Rank by predicted constraint
violation status, normalized violation, predicted safety change, then opaque tie
order. Positive normalization scales and constraint thresholds are frozen before
held-out work. Buy two paired full observations (common seeds z0,z1) for the first
two edits; choose the budget from costs so both can afford this and final reserve.

Then alternate breadth and repetition until neither has an affordable useful
purchase. Breadth scans every unpromoted edit in rank order, promoting the first
whose entire two-pair z0/z1 package fits, charging missing artifacts only. Repetition
visits every promoted edit in frozen rank order and buys its earliest unused seed
in the common sequence z2,z3,... when affordable. Newly promoted edits can reuse a
paid a0(z2) while still obtaining a genuinely fresh edit seed. Repeat passes and
permit partial passes; skip unaffordable packages/pairs with an explicit receipt.
After all12 are promoted, continue repetitions if affordable. No gratuitous short
runs after freezing the order. Report indivisible leftovers and any sensitivity
extra observation with its extra cost. Never recast continuations as new seeds.

Equal weight per independent paired full seed defines each arm mean. Eligible
edits need at least two complete full pairs and the same heuristic estimated
capability/refusal constraints; select smallest estimated safety change including
a0=0, favoring a0 on exact ties. Unresolved observations use prospective conservative
bounds, not complete-case averages. Lock choices before fresh hidden deployments.
Unequal seed counts and selecting minima can favor noisy arms; performance comes
from fresh final deployments, not winning acquisition means. No per-edit expected
feasibility guarantee or original H2 passage is inferred.

Numerical values, practical margins, tariff details and independent block count
remain unfrozen until development measurements. The schedule may be technically
revised before hidden outcomes if code review finds a concrete defect, with a
preserved amendment; do not tune it on confirmatory results.
