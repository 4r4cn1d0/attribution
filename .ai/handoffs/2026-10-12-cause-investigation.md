# Causal investigation: OLMo/Llama recipe response — 12 October 2026

Status: ACTIVE PREPARATION; no new causal-study pod launched and no cause established.
User instruction: “Establish cause”, following discussion of the 1B and 7–8B
Scheduled-recipe results. Main attribution Gate B remains paused. Probe recovery
continues independently under its existing $8 allowance.

**Current funded design supersedes the older draft population-inference criteria
below:** one fresh joint seed1121 block, A/C/D at OLMo1B and7B, six units on two
pods. Primary reporting is descriptive and seed-specific, with no population
CI/p-value/equivalence claim. The frozen JSON in
`research/side-notes/causal-study-20261012/protocol.json` and its README control
this block. Replicated population inference and historical bridges are later,
separately funded work. The unchanged current engine X is used for all six units;
historical outcomes and engines are not pooled. Objective reconstruction checks
log consistency, not independent gradient correctness. No gradient-mediator cause
is inferred from that check.

## Routing and authorization

Opus5.5/max first-pass alternatives were requested through `.ai/claude_handoff.py`,
using `.ai/briefs/side-project-cause-first-pass-20261012.md`. The request failed
at the weekly usage limit (15 October,14:30 IST); no model identity or substantive
Opus result was returned. Evidence: `tmp/claude-handoffs/20261012T065129Z-3ad13967/`.
The user answered “1. Yes 2. Yes” on12 October, authorizing GPT implementation
for this study while Opus is unavailable. The lead explicitly interpreted the
budget as the remaining balance, with recovery funding kept separate; no larger
or unlimited spend is inferred. At08:01 UTC the balance was$35.12525, and
$1.85646 remains allocated to recovery. One fresh six-unit joint A/C/D block is
the affordable diagnostic. Native GPT auditor Kepler performed a bounded read-only setup audit;
no scientific code or data were changed by that worker.

The new-study budget was also requested. At approximately06:49 UTC the account
held $35.6162, with $1.8565 of the original probe-recovery allowance unspent;
approximately $33.7598 remained before storage and a new-study contingency.
This is account availability, not a promise that a confirmatory study fits it.

## Findings already checked

1. **Selected/native OLMo7B tokenizer identity:** the download receipts compare
   the actual selected1B and native7B tokenizer files at the frozen revisions.
   They match. The recorded template begins with `<|endoftext|>`, and its SHA-256
   is `fe689ffbd6a4e2d0532d7480696b065b10e0e1eff3f9b9fc4bea415761e4bf4a`.
   Thus the repository-name/current-model-card suspicion in the earlier recovery
   note is NOT supported for these actual runs. Do not launch a supposed native
   tokenizer correction that would merely rename identical bytes.
2. **Training-engine differences:** the bounded audit found no changed valid
   optimizer/loss calculation for these chosen recipes between55253874 and
   e49a978c. Warmup multiplication order differs, but the selected warmup4 gives
   identical rates. Engine.py is identical frome49a978c to472fc7f6; remaining
   changes include provenance, LR logging, validation and attribution. This is
   a code audit, not proof of full real-model numerical training equivalence.
3. **Exact LR mean:** evaluating the actual `learning_rate` function over38
   updates gives sumLR0.0019 and meanLR0.00005. This equals the existing
   Constant half-LR arm exactly. An LR0 update still changes Adam's moments and
   step count, even though it does not change model parameters. Therefore a
   saved peak-LR value does not describe the actual optimization trajectory.
4. **Actual intervention:** Scheduled jointly changes per-example response NLL
   to token-mean NLL and adds warmup/cosine timing. Longer responses get more
   relative weight under token-mean loss. Size/release/alignment histories remain
   confounded; none of the proposed within-checkpoint interventions identifies
   a universal causal effect of parameter count.

Sources: actual frozen receipts/bundles in `tmp/family-probe-olmo2-1b*/setup/`
and `tmp/family-probe-sp-olmo2-7b*/setup/`; representative actual template:
`tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-init-a1/assets.json`.
Lead arithmetic and cost evidence: `tmp/cause-study-20261012/`.

## Draft investigation and acceptance criteria

The programme isolates **loss weighting × LR treatment within fixed checkpoints**.
The six-arm expansion is useful for mean-LR-matched timing and interaction checks:

- A: example mean, constant1e-4 (existing Constant).
- B: token mean, constant1e-4 (missing at7B).
- C: example mean, four-step warmup/cosine with peak1e-4 (missing at7B).
- D: token mean, same warmup/cosine (existing Scheduled).
- E: example mean, constant5e-5 (existing half-LR).
- F: token mean, constant5e-5 (missing at7B).

The four-cell A/B/C/D comparison separates loss-weighting and the scheduled
package. E/F separate the exact average LR from schedule timing. Equal summed LR
is not equal parameter displacement or Adam trajectory; use “mean-LR matched”,
not “dose matched”. Warmup versus
cosine remains a later distinction; the first study must not claim to separate
them. Analysis uses independent training-seed blocks, pairing initialization and
data order across arms. Randomize execution order; pin one engine, numeric/software
environment, model snapshot, tokenizer bytes, prepared data, LoRA settings and
evaluation settings. New seeds and pre-existing seeds require explicit disclosure
and a concurrent reproduction check before historical controls are relied upon.

**Minimal first experiment:** A/C/D at OLMo1B AND OLMo7B, with concurrent fresh
seed blocks. C−A measures the scheduled package under example-mean loss; D−C
measures switching to token-mean loss under that schedule. The exact ordered
decomposition is D−A=(C−A)+(D−C); opposing contributions can mask each other
without a nonzero loss×schedule interaction. B is therefore optional for this
first question. A one-checkpoint pilot identifies conditional effects there;
it cannot explain a cross-checkpoint difference or establish a parameter-count law.

Proposed two primary contrasts are the direct cross-checkpoint differences
[(C−A)1B−(C−A)7B] and [(D−C)1B−(D−C)7B], with family alpha.05, Bonferroni.025
per contrast. Within-checkpoint component effects, total recipe differences,
and logit versions are reported alongside; a claim solely about a conditional
component needs its declared inference scope. Replication N is pending budget
and a final sensitivity calculation for this direct contrast. The hypothetical
SD scenarios below are not measurements of its variance.

Proposed joint blocks use fresh development seeds (for example1121 onward),
with the same raw training-row order at both checkpoints and a separately
initialized model at each checkpoint. The old1B and7B jobs use the identical
prepared manifest9ed61826…; each new block must additionally verify its actual
row-order fingerprints before inference. Initial-state fingerprints must match
across A/C/D **within** a checkpoint, not across different architectures. Analyze
the per-block cross-checkpoint contrasts and estimate their actual variance;
identical seed numbers do not license an assumed favorable covariance. Two joint
blocks are two training replicates. If the pairing cannot be verified, select an
independent-checkpoint analysis and matching power model before new outcomes.

All primary outcomes are at **e1,38 optimizer updates**. Other checkpoint names
remain in copied source configs, but q/e3 comparisons are outside the registered
primary study. Schedule mean matching applies only to e1. Historical seed controls
are not substituted for concurrent A/D runs at fresh seeds. Reproduce both old
anchor recipes if a historical bridge is needed; resolving one bridge does not
prove every historical run exchangeable. Do not pool pilot-selected effects with
later confirmation naively. Reset optimizer and RNG per arm and record common
initialization/data-order fingerprints; randomize arm execution within each block.

Four validated DRAFT JSON controls are prepared in
`tmp/cause-study-20261012/configs/`: three missing7B arms and example-mean
Scheduled at1B. Only loss/optional weighting fields and metadata differ from
their original sources; all other sections are identical. Exact file/config
hashes are in `candidate-configs.json`. Example-mean requires omitting the optional
weighting key; an explicit example_mean value is rejected by this schema. These
configs are not integrated, frozen, packed or launched. No engine changes were made.
Reviewed input copies and provenance are archived in
`.ai/inputs/side-project-cause-20261012/`; these are draft study inputs, not a
registered runtime kit.

Primary estimands must be fixed before new outputs. Mean-LR-matched timing contrasts
C−E and D−F and the factorial interaction are deferred/exploratory until separately
registered and funded; they do not inherit the primary testing allowance.
U0 cancels in each contrast. Historical logit contrasts remain intact
and can be secondary for continuity. Do not select the favorable metric/judge.
Over-refusal and task utility are required side outcomes. A safety-share reduction
caused by indiscriminate refusal remains a measured causal effect; it fails the
useful/selective-safety interpretation and must not be discarded or relabelled
“no effect”. The original600 sampled safety answers per unit must be retained
for a direct replication of the original measurement; a cheaper evaluation would
need a separately defined estimand, precision statement and registration.
U is the **Unsafe** share, so lower U is favorable. For the two primary contrasts,
97.5% individual intervals yield at least95% simultaneous coverage by Bonferroni.
Practical heterogeneity is distinct from improvement: both checkpoints could
worsen. Explaining the original improvement requires the within-checkpoint
component directions and total D−A effect, without silently reusing the primary
testing allowance for extra claims.

Before training: independently check the actual loss reductions on unequal-length
synthetic targets, the applied schedule inside optimizer.step, and fixed-state
update parity across relevant engines including direct-init versus saved-init.
Such checks resolve implementation uncertainty; they cannot substitute for the
controlled safety experiment. No repository unit tests have been added or run.

Claim criteria: a prespecified causal contrast with uncertainty excluding its
declared null, correct identities/controls, and replication at the training-seed
level. A useful-safety claim additionally needs acceptable utility/over-refusal.
Proposed margins, not yet frozen:5pp safety contribution,5pp extra benign
over-refusal versus A,0.10 extra task-query NLL versus A; ARC accuracy change is
secondary. These are proposed practical thresholds, not user-selected facts.
To claim an effect exceeds5pp the simultaneous interval must exclude the entire
[-5,+5] region; ordinary power to reject zero is not sufficient. Record task
learning relative to baseline rather than using ARC alone. A fixed-state change
establishes only its local computational effect. A three-seed result may remain
inconclusive. A null/equivalence claim requires a prespecified practical margin
and a sufficiently narrow interval. Component findings alone do not identify a
refusal-direction mediator; that requires protection/restoration interventions
with matched random-feature controls and independent validation.
Task-query NLL uses one identical evaluation reduction and target mask for every
arm, separate from the manipulated training objective. Verify task-query/training
disjointness before calling it held-out utility; otherwise it is a task-learning
indicator only. Report uncertainty bounds for NLL and over-refusal tolerances.

Freeze policy/system prompts, judge prompts, decoding, prompt weights, sample
streams, truncation and unparsed-output handling before outcomes. Retain and report
all technical failures. Missing/incomplete outcomes cannot silently be excluded;
an incomplete block may prevent the primary claim. A rerun is allowed only for a
prespecified infrastructure failure at the same seed/config, not an unfavorable
outcome. Development-bank claims are limited to that known bank. A confirmatory
generalization check needs an independent frozen prompt bank; Main-study held-out
banks are not silently repurposed.

## Power and cost feasibility

Prospective sensitivity simulation is saved in
`tmp/cause-study-20261012/power-sensitivity.json`: hypothetical normal seed-level
contrasts, two-sided paired t test, per-contrast alpha.025,4000 simulations, fixed
simulation seed2026101207. Effect scenarios5/10/15pp and contrast SD8/12/16/20pp
are planning scenarios, not selected user margins or observed-power claims.
On the explored grid,80% power for a10pp contrast needs12/24/32/48 seed blocks
respectively; a15pp contrast needs6/12/16/24. This approximation does not yet
power the full multiplicity procedure or a cross-model interaction. Three seeds
are a diagnostic, not assurance of cause identification.

Historical OLMo7B unit time: median90.3min, max107.3; training median14.9min.
Llama8B: median123.35min, max140.6; training median14.4min. At$1.79/hour these
are $2.69/$3.68 per median unit, BEFORE setup, preflight, extra judges, storage,
failure contingency and analysis. Six new OLMo7B units alone cost about$16.16
at the median job duration; nine about$24.25. Adding concurrent controls and
whole-pod overhead can use most of the remaining balance. The complete causal
programme needs a costed budget and adequate seed replication; no larger spend
is inferred from the old top-up.

Measured1B cost basis is now available: seven completed r64 B/BT/G units took
34.03–59.56min, median51.02min, with training3.64–4.24min. These times also exclude
whole-pod overhead. A two-fresh-block A/C/D diagnostic at each of1B and7B requires
12 units; median job-time spend alone is about$25.30, with a historical-maximum
duration scenario of$29.87, before setup/judges/storage. These maxima are not
guaranteed ceilings. Historical A/D bridges at both checkpoints add about$8.43
at median durations; those bridges plus twelve new units already consume about
$33.73 before overhead, so they cannot be promised within the remaining balance.
Two seed blocks have extremely limited
precision; this is a pilot with narrow seed/checkpoint scope, not assurance that
the cause of the original pattern will be established.

Non-author GPT reviewer Avicenna checked the draft and actual four-control scope
(three controls existed at its first review). Corrections accepted: minimal A/C/D,
interaction not required for masking, mean-LR matching versus dose, e1-only horizon,
concurrent fresh controls, direct cross-checkpoint contrasts, declared multiplicity,
practical-margin and useful-safety distinctions, and binding budget/power limits.
The revised document remains a draft pending final design/implementation review,
routing exception and budget. No cause-identifying result is claimed.
Targeted re-review found no structural blocker to offering this as a **provisional
pilot quote**, with the qualifications above. Final N, randomization, inference,
overhead reserve, resource caps and feasibility/continuation rules must be frozen
before outputs. If only one six-unit joint block is affordable, its scope is a
seed-specific diagnostic. Continuing must follow a declared feasibility rule or
independent confirmation plan, not favorable outcomes or optional significance
stopping. This review is not a claim of independent errors or experimental proof.

## Literature checkpoint

The optimization hypothesis is already studied by
[Kim et al.](https://arxiv.org/abs/2508.12531); shallow initial-token alignment and
fine-tuning sensitivity by [Qi et al.](https://arxiv.org/abs/2406.05946).
[Hawkins et al.](https://proceedings.mlr.press/v306/hawkins26a.html) finds
heterogeneous safety drift in multilingual settings. These support studying the
mechanism, not declaring a novel explanation or assuming it holds in these
checkpoints. Exact component interventions, release confounds and acceptable
safety/utility outcomes must determine our conclusions.
