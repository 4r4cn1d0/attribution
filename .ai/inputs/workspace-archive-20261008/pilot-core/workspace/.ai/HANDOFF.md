# Current workflow handoff

User request, 2026-09-24: install the pasted collaboration workflow here, keeping
GPT as orchestrator, Opus 5.5 at max effort as implementer, and GPT questioning
Opus and helping red-team. Scope is this project.

## Installed and checked

- GPT orchestrates, asks questions, red-teams, verifies, and integrates.
- Claude implementation is pinned to `claude-opus-5-5`, with `--effort max` and
  matching child environment. No alias, fallback model, or lower effort is chosen.
- The launcher supports this non-Git folder through prepared isolated copies.
- Twenty-five offline tests passed in 22.005 seconds, including routing failures,
  incomplete responses, preparation, failure records, timeout descendants, and
  interruption during preflight. GPT ran these checks.
- A live response to GPT's verification question returned actual modelUsage
  `claude-opus-5-5`: `tmp/claude-handoffs/20260924T101253Z-253f5e3b/`.
- A separate live implementation wrote exactly the requested text (without a final
  newline) only to `workflow-smoke.txt` in the prepared copy. Actual modelUsage was
  `claude-opus-5-5`; no permission denials were reported. Evidence:
  `tmp/claude-handoffs/20260924T101611Z-b9d59a00/`.
- `max` was explicitly requested and accepted by the CLI. The result does not
  separately report effective internal effort; do not assert more than that.
- All fourteen pre-existing research files retained their original hashes.
  Final check receipt: `tmp/workflow-install/final-checks.json`.

## Installation review and limitations

The initial requested Opus implementation call produced the launcher and tests but
hit its 900-second cap before a final result. Its routing metadata is unavailable;
do not label that call successful. Original artifacts and the timeout record remain
in `tmp/workflow-install/`. The two later bounded live checks above succeeded.

A fresh GPT reviewer challenged the design, then inspected the concrete code.
GPT integration corrected misleading “verified” status, missing preflight/startup
failure evidence, descendant cleanup, failed change enumeration reported as an
empty success, and preflight termination handling. The final regression run also
exercised and corrected macOS EPERM behavior for zombie-only process groups.
The final integration fixes were validated by tests; do not imply every final line
received a new independent reviewer pass.

Clean calls return `status: returned` and `implementation_verified: false`.
The GPT lead must still inspect the actual output and verify the assignment.
The live write was a minimal handoff smoke test, not a substantive feature test.
Narrow shell permissions are supported but were not exercised by the live checks.

## Scientific context

The proposal and novelty/rigor assessment are under `research/`. The current
research direction still needs a narrower contribution and evidence that a cheap
seed-dependent surrogate improves total audit cost. No training study was launched
by this workflow installation.

## Project 3 assessment, 2026-09-24

The user supplied the original Influence-Based Proactive Alignment & Unlearning
Verification proposal plus a critique and requested novelty and rigor scores for
an ICML 2027 target. GPT verified the main cited precedents and assessed the
proposal at novelty 2/5 and demonstrated mathematical rigor 1.5/5. These are
coarse proposal-stage judgments, not official scores or acceptance probabilities.

- Report: `research/review/project3-novelty-rigor.md`.
- Analytic check receipt: `research/review/project3-mathematical-checks.json`.
- GPT constructed a nonconvex exact-training counterexample showing zero local
  parameter and output influence with nonzero finite-deletion effects. Fresh GPT
  reviewer `project3_math_redteam` verified it and the common-kernel postprocessing
  argument. Its scope is an unrestricted local-to-finite inference, not all
  possible full-path operators or an empirical LLM finding.
- Primary sources confirm IF-Guide, LLMEraser, PRISM, certified unlearning, and
  downstream robustness overlap. PRISM is reported as accepted at ICLR 2026 by
  its arXiv v2 metadata. A closer reading corrected comparator ambiguity in the
  ICML 2025 neural-network certification paper: its main comparator includes
  postprocessing of the retain-only trained model.
- Opus first-pass review received the raw proposal without the pasted scores or
  GPT's preferred result. Run `tmp/claude-handoffs/20260924T103751Z-707bf88e/`
  requested exact `claude-opus-5-5` and `max`, but timed out at 420 seconds with
  exit 143, empty response, and no actual model metadata. Do not attribute a
  verdict to Opus or claim a completed cross-model follow-up. No model substitute
  or retry was used.

The new assessment preserves the prior deletion-audit proposal and review. The
user has not selected one of the two candidate projects. Neither the dual-space
operator nor a finite-deletion certificate has been implemented or proven; no
training study was launched. A narrower audit question is suggested, with novelty
still requiring direct comparison and empirical evidence.

## Search for a stronger candidate, 2026-09-24

The user clarified a target of approximately 4/5 novelty and 4/5 rigor. GPT
screened new candidates against primary literature rather than increasing scores
for the original proposal. Findings and a bounded next-study recommendation are
in `research/strong-candidate-screening.md`.

- Broad descendant unlearning overlaps PURGE and MUTE; selection-inclusive
  influence has direct precedents going back to 1993 and 2012; unlearning-order
  effects have a UAI 2026 precedent. None is recommended as a broad novelty claim.
- Provisional lead: the total compute–accuracy tradeoff for finite-intervention
  attribution in adaptive post-training. Data Attribution in Adaptive Learning
  (arXiv:2604.04892) already establishes the target and replay-versus-intervention
  issues. RFT-Inf, CROPI, learned counterfactual couplings, and multilevel simulation
  are additional required comparisons. No candidate earns verified 4/4 yet.
- GPT reviewer `descendant_unlearning_gap` independently searched descendant and
  selection literature, then red-teamed the proposed estimator. Main unresolved
  concerns: generic coupling/debiasing is not novel; bias bounds do not supply
  correction second-moment bounds; replay-tail optimizer work can eliminate
  supposed savings. Recommend exact finite-state/oracle checks before GPU study.
- Optional compute question was sent; no answer had arrived at time of writing.
  One-GPU feasibility is a planning assumption, not confirmed access.
- Opus alternatives brief: `.ai/briefs/strong-candidate-ideation.md`. Run
  `tmp/claude-handoffs/20260924T104712Z-2f5d74b9/` requested exact
  `claude-opus-5-5` and `max`; timed out at 240 seconds, exit 143, empty response,
  no returned model metadata. No retry or substitute, no Opus findings, and no
  completed cross-model questioning loop. Research work remained with GPT.

No training or substantive method implementation was launched. The new document
is a falsifiable research recommendation with explicit novelty gates, not a proved
method or a claim that the user has selected the provisional direction.

## Implementation-task scoping, 2026-09-24

Authorized scope: concrete research and implementation specifications for the
provisional adaptive finite-occurrence attribution candidate; no substantial
training, paid compute or publication. This Implementation task is GPT lead for
this phase. The research source task is 01a0d2a2-99b1-70a0-8337-4fbaa3f95ebf.

- Created research/scoping/{SCOPE,PRIOR_ART,THEORY,PILOT_SPEC,IMPLEMENTATION_PLAN,REVIEW}.md.
  Recommendation: revise the contribution and proceed only to CPU exactness and
  headroom tasks. Neither a 4/5 result nor an efficiency theorem is established.
- Primary target: fixed-prefix finite suppression of one data-gradient occurrence,
  with optimizer step/counters/decay still executed and each world's future data
  regenerated. No whole-record deletion or distributional unlearning claim.
- Verified primary sections of adaptive attribution, RFT-Inf, CROPI, learned
  Gumbel mechanisms, Anderson and Giles; added Markov/bicausal transport overlap.
  The adaptive truncation theorem bounds derivatives, not automatically finite
  suppression. Forward-citation coverage and one full-text access remain incomplete.
- GPT's first-pass alternatives: tmp/scoping/gpt-first-pass.md. New Opus brief:
  .ai/briefs/scoping-first-pass.md. New run:
  tmp/claude-handoffs/20260924T110611Z-244af48e/ requested exact claude-opus-5-5
  and max, six turns/600 seconds, then timed out with exit 143, empty response and
  no model metadata. No Opus findings, effective-effort claim, retry/substitute,
  completed cross-model challenge, prepared implementation workspace or integration.
- Non-author GPT reviewer scope_redteam checked theory and study design, then a
  bounded disposition pass. Corrected projection h-1 indexing, scalar all-horizon
  equivalence to sorted CRN, exact Gumbel joint masses, sample-allocation artifacts,
  uncapped simulation/uncharged fitting labels, baseline fast-path parity and
  uncertainty definitions. Final deterministic-baseline calibration exemption was
  integrated and checked by GPT, not independently re-reviewed. Details: REVIEW.md.
- Lead numerical verification: 12 equation/fixture checks passed, exit 0. Receipt:
  research/scoping/ANALYTIC_CHECKS.json; script tmp/scoping/analytic_checks.py.
  These are analytical scoping checks, not the pilot or evidence of speedup.
- All 22 pre-existing context files matched the starting hashes before this append.
  Earlier research/reviews remain unchanged. No Git repository initialized.

Remaining: novel training-specific terminal-variance/cost bound, exact oracle
headroom, practical measured cost frontier, learned comparator, source follow-up,
and the absent Opus design/implementation contribution. Next bounded code task is
IMPLEMENTATION_PLAN task A using a new prepared isolated workspace and required
Opus route; no model study begins until the prespecified pilot/novelty gates pass.
