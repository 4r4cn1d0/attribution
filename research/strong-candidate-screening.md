# Research screening for a 4/5 novelty and rigor target

Date: 2026-09-24. Target: an ICML submission combining training-data attribution
and faithful evaluation. Status: research recommendation, not a validated method.
No candidate screened here has demonstrated 4/5 novelty and 4/5 rigor. Scores
would be informal judgments, not ICML acceptance probabilities.

## Recommendation

Advance one bounded feasibility study under the working title **The Price of
Faithful Attribution in Adaptive Post-Training**. Its question is whether an
example's finite effect on an adaptive learner can be estimated accurately at
substantially lower total cost than repeated counterfactual training runs.

The potentially publishable contribution is a training-specific estimator with a
new variance–cost result and useful empirical performance. The fact that a model
changes its own future training data, and that fixed-log attribution can fail,
is already established. Simply combining influence functions, coupling, and
multilevel Monte Carlo does not establish sufficient novelty.

This is a proposal worth falsifying cheaply, not a recommendation to commit a
large GPU budget. The prior zero-influence proposal and selective deletion-audit
proposal remain preserved in this repository.

## Exact initial target

Fix an observed training prefix h_t, including the observation used at step t.
Compare the ordinary update with an intervention suppressing that one update.
In both worlds, regenerate subsequent observations from the respective learner.
For a prespecified bounded terminal behavior score g, estimate

    Delta_t(h_t) = E[g(Theta_T^suppressed) | h_t]
                - E[g(Theta_T^ordinary) | h_t].

This is an occurrence-level intervention. It does not delete every appearance
of a document, erase its effects on the observed prefix, or certify removal of
information from a model. Zero mean effect on g is not distributional unlearning.

The simulator state must include optimizer state, replay buffers, relevant
environment state, schedules, and all other variables affecting future updates.
The coupling used to simulate the two worlds must preserve their marginal laws.
It is a variance-reduction device, not evidence that one particular joint
counterfactual mechanism is uniquely identified by observed data.

## What is already occupied

| Candidate claim | Closest checked predecessor | Consequence |
| --- | --- | --- |
| Adaptive attribution requires regenerating future training data | [Data Attribution in Adaptive Learning](https://arxiv.org/abs/2604.04892) | Already supplies occurrence-level targets, replay nonidentifiability, an identification class, sign failures, and feedback-depth approximations. |
| Efficient influence estimates for RL fine-tuning | [RFT-Inf, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/3755a02b1035fbadd5f93a022170e46f-Abstract-Conference.html) and [CROPI](https://arxiv.org/abs/2510.26491) | Finite sample-removal scores, first-order approximation/error analysis, and off-policy data selection are already represented. Their intervention units and objectives must be reconciled before comparison. |
| Learn a coupling to reduce counterfactual estimation variance | [Lorberbom et al., NeurIPS 2021](https://arxiv.org/abs/2111.06888) | Generic learned or objective-aware coupling is not new. |
| Couple perturbed stochastic trajectories and use a hierarchy | [Anderson](https://arxiv.org/abs/1109.2890), [Giles](https://arxiv.org/abs/1304.5472) | Coupled finite-difference estimation and multilevel simulation are established ingredients. |
| Attribution should include which model gets selected | [Léger and Altman, 1993](https://doi.org/10.1080/01621459.1993.10476306); [Sterba and Pek, 2012](https://cdn.vanderbilt.edu/t2-my/my-prd/wp-content/uploads/sites/2472/2017/04/Sterba.Pek_2012.pdf) | Conditional versus selection-inclusive deletion influence, approximate screening, and exact follow-up have old precedents. |
| Delete influence from downstream/distilled learners | [PURGE](https://arxiv.org/abs/2503.22539); [MUTE](https://arxiv.org/abs/2607.28829) | Broad descendant-unlearning claims are occupied. The remaining algorithmic gap would need much narrower specification. |
| Unlearning order matters | [Kumar et al., UAI 2026](https://proceedings.mlr.press/v337/kumar26a.html) | Order dependence and gradient commutator analysis are not new contributions. |

These are reasons to narrow claims, not claims that the cited methods solve every
version of the problem. The search is not exhaustive and cannot prove absence
of competing work.

## Candidate mechanism and mathematical burden

Begin with a finite-action, entropy-regularized adaptive learner. Investigate
coupling actions according to the optimizer updates they induce, rather than
only maximizing the probability of drawing identical actions. A useful method
must exploit the learner's structure to construct that coupling cheaply.

**Theorem target, not a proved result:** construct an exactly marginal-preserving
coupling and derive a strict variance–cost advantage over strong ordinary
couplings for an explicitly defined, nontrivial adaptive-learning class. Obtain
the advantage from the actual update equations, with explicit dependence on
horizon, intervention size, and feedback strength. Merely assuming contraction
and applying an existing multilevel theorem is insufficient.

If a hierarchy is used, distinguish the mean truncation error from the second
moments of adjacent-level corrections. A bound on the former does not bound the
latter. For corrections D_l with complete simulation cost c_l, inspect the
standard efficiency diagnostic

    S_T = sum_l sqrt(E[D_l^2] * c_l).

This diagnostic is not a new theorem. The research obligation is to derive useful
problem-specific bounds and show an improvement that survives implementation.
Include the base level, terminal evaluation, any remaining truncation bias,
minimum sample overhead, and construction of the coupling in the cost accounting.

The critical obstruction: simulating only L changed-data rounds can still require
T-L optimizer updates at the altered parameters to evaluate terminal behavior.
Original-run gradients do not generally provide those updates. Short feedback
depth therefore does not imply short computation. Report generation savings and
total-cost savings separately. Full counterfactual paired reruns are the simple
baseline that this complication must beat.

## Cheap decisive pilot

1. Use a tiny categorical learner with a short enough horizon to enumerate the
   complete terminal distribution. This supplies exact ground truth for the
   stated conditional intervention, without treating a noisy retrain as truth.
2. Sweep feedback strength, intervention magnitude, horizon, and reward/feature
   structure across stable and self-reinforcing cases. Prespecify the grid and
   primary measures before choosing a favorable example.
3. Compare independent reruns, shared-randomness reruns, maximal action-agreement
   coupling, a strong learned-coupling baseline, and an oracle optimal coupling
   for the specified finite-state variance objective. Include fixed-log and
   truncated estimators as biased alternatives with their bias measured.
4. Measure exact marginal correctness, bias, correction second moments, repeated
   estimator MSE, and operation counts. Include training, generation, evaluation,
   storage/checkpoints, and coupling overhead; show the cost–accuracy frontier.
5. Reject the proposed hierarchy if even the oracle has no useful advantage, if
   ordinary coupling already matches it, or if replay-tail work removes savings.
   Oracle performance is an upper bound on that coupling opportunity, not a
   practical algorithm result. It does not rule out all other estimator families.

Only after this pilot passes should we design a small-language-model study.
Provisionally assume access to one GPU; the user has not yet specified compute.
Use repeated independent training-seed blocks, multiple intervention prefixes,
held-out behavior queries, and sufficient counterfactual repetitions to quantify
reference uncertainty. Treat shared-run interventions as dependent observations.
Assess cost at matched error and usefulness for identifying harmful/helpful
updates. Do not substitute downstream benchmark gains for attribution accuracy.

For a theory-plus-LLM paper, a finite-action theorem and a neural demonstration
must remain explicitly separate. A useful empirical result can support scope
beyond the theorem's class but does not prove the theorem for arbitrary LLMs.

## What would support a 4/5 assessment

- **Novelty:** an explicit capability or efficiency separation missing from the
  nearest papers, attributable to a new training-specific mechanism; not solely
  application of a standard statistical estimator in an LLM setting.
- **Rigor:** proved assumptions and bounds, an exact small-system check, replicated
  neural experiments, correct estimand matching, strong simple baselines, and
  complete compute accounting. State failure regimes and limitations.
- **Impact:** the resulting cost reduction enables an attribution audit or data
  decision that was impractical under the same budget using the best baseline.

These are research gates, not completed contributions. No proof, estimator
implementation, training experiment, or performance result was produced here.

## Review provenance

GPT performed the primary-source screening. A fresh-context GPT reviewer examined
descendant unlearning, selection-aware influence, and then the estimator proposal.
It identified the replay-tail cost problem and the gap between bias decay and
coupled second moments. Those objections are incorporated above; this document
does not imply an independent review of every final sentence.

An Opus first-pass alternative-design call requested exact `claude-opus-5-5` at
`max`, with a separate brief that did not include GPT's preferred candidate or
scores. It timed out at 240 seconds with no response or returned model metadata:
`tmp/claude-handoffs/20260924T104712Z-2f5d74b9/`. No Opus verdict, model fallback,
completed cross-model questioning loop, or implementation is claimed.
