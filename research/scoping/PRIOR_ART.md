# Prior art and the remaining possible gap

Verified 2026-09-24. Primary-source reading, not an exhaustive novelty clearance.
The section references below refer to the linked versions. Download receipts and
SHA-256 hashes are in `tmp/scoping/sources/manifest.json`; text is extracted from
PDFs without relying on another paper's characterization. Failed access is noted.
All distinctions in the last column are this scope's analysis, not author claims.

## Claim-by-claim comparison

| Primary source and checked locations | Established overlap / actual target | Consequence for this project |
| --- | --- | --- |
| [Rege, Data Attribution in Adaptive Learning, v1](https://arxiv.org/html/2604.04892v1): §§3.1–3.3; §5 Theorem 2; §6 Theorem 3/Corollary 1; §8 Eqs.13–20, Theorem 6/Corollary 2; Appendix F.2 Theorem 7 | Occurrence weighting, prefix-conditioned finite effects, full recollection versus replay, replay-oracle nonidentifiability, and action-only change of measure are already explicit. Section 8 defines finite truncated targets, but its displayed depth identity and error bound concern **infinitesimal influence**. Appendix F.2 gives derivative dynamic programming. | Our target is a specialization, not new. A finite-suppression variance–cost theorem is not supplied by the derivative truncation result. This observation does not prove that all finite-effect estimators are absent. |
| [Tan et al., RFT-Inf, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/file/3755a02b1035fbadd5f93a022170e46f-Paper-Conference.pdf): §4.1 Eqs.4–5; §4.2 Proposition 1; §§4.3–4.4; Appendices B–C | Finite **dataset sample removal** target J(theta_Z)-J(theta_Z/z); trajectory/checkpoint gradient-alignment approximation, summed across training. Proposition 1 assumes Lipschitz log likelihood and bounded advantage; its stated bound grows with training horizon. Surrogate training and checkpoint gradients have costs. | Do not describe its target as merely infinitesimal. Conversely, the paper does not specify our fixed-prefix single-occurrence suppression with regenerated future law. Its native score has opposite sign and different units/normalization from ours unless explicitly aligned. Its stated approximation bound is not a guarantee for our coupled simulator. |
| [Zhu et al., CROPI, v1](https://arxiv.org/html/2510.26491v1): §3.1 Eqs.4–5, §3.3 Eq.6, §4, Appendices A–B | POPI uses off-policy gradient estimates from a behavior policy, assumes policies are sufficiently close for the approximation, compresses gradients, and uses normalized gradient similarity for curriculum selection. | Off-policy influence-guided selection is occupied. A cosine similarity is not a finite intervention effect. Compare native selection performance only as a separate question, or explicitly label a calibrated first-order proxy. |
| [Lorberbom et al., generalized Gumbel-max mechanisms, v1](https://arxiv.org/html/2111.06888v1): §3 Eqs.7–8; §4 Proposition 2; §5.2 Eq.14/Appendix H; §6 | Learning marginal-correct couplings for query-specific counterfactual variance is explicit. Gadget 2 corrects finite Sinkhorn iterations to enforce marginals. Section 6 discusses monotone couplings maximizing covariance. Implicit shared-noise mechanisms and pair-dependent explicit couplings are different classes. | Neither learned terminal-aware coupling nor scalar sorted overlap is a sufficient novelty claim. Our pair-state method has both marginals available; do not claim the paper's impossibility result rules it out. Give learned baselines comparable information and preserve marginals exactly. |
| [Anderson, coupled finite differences](https://arxiv.org/pdf/1109.2890): §2 Assumptions 1–2; §3.1 Eq.7; §3.2 Theorem 1 | Couples perturbed continuous-time jump processes using common and residual reaction rates. Under Lipschitz rates and controlled parameter perturbations, bounds a path-difference second moment by a constant times perturbation size. | Training-aware trajectory coupling and second-moment control have methodological precedent. Jump-process parameter perturbations differ from one finite optimizer occurrence; importing the theorem requires an explicit model mapping and cannot hide horizon-dependent constants. |
| [Giles, Multilevel Monte Carlo methods](https://arxiv.org/pdf/1304.5472): introduction allocation calculation; §2 Theorem 1; §6 Wasserstein metric | Multilevel complexity depends separately on bias, level-difference variance and cost. Coupling via transport is discussed. | A telescoping hierarchy, optimal allocation, or a mean-bias bound alone is not new or enough. Our lower-feedback levels still require optimizer-tail work; geometric cost savings are unproved. |
| [Moulos, Bicausal Optimal Transport for Markov Chains via Dynamic Programming, v1](https://arxiv.org/html/2010.06831v1): §2 examples; §3 Theorem 1; §4 | Transport with transition-marginal constraints is a control problem on the pair state. Optimal Markov coupling and Bellman/value-iteration methods are established; greedy meeting probability can be inadequate. | The finite-horizon terminal-square-cost oracle is a standard specialization used for diagnosis. Its restricted class must not be confused with unrestricted terminal/path transport. |
| [Hu et al., A Snapshot of Influence](https://arxiv.org/abs/2505.19281): PDF §3.1; §7 limitations | Checkpoint-local attribution to recent PPO-buffer records; action/return targets and gradient similarity. Explicit discussion of optimizer and counterfactual limitations. | Changing the scope from local to global feedback is not enough given Rege. This remains a useful proxy comparator for later RL experiments. |
| [Shu et al., Learning from the Right Rollouts, v1](https://arxiv.org/html/2604.01597v1): §§3.2, 4.2; Appendix B.2 | PPO episode filtering/reweighting by target-gradient alignment; local treatment of fixed advantages and batch interactions is explicitly approximate. | Faithful reasoning and attribution-assisted filtering have existing work. Our initial accuracy study does not itself validate reasoning faithfulness or claim this capability. |
| [Liu et al., Non-Local Data Attribution for On-policy RL](https://openreview.net/pdf?id=tYEJvG7njT) | Primary PDF search indexing supplied the abstract and introduction: replay-LOO under fixed future buffers, TracIn/SGD-influence, and buffer reuse. Full PDF direct access returned 403/browser challenge. | A nonlocal horizon alone is occupied. Full methods verification remains incomplete; do not attribute a full-recollection efficiency theorem or assert its absence based on this partial read. |

Additional overlap triage: [Nüsken–Pavliotis](https://epubs.siam.org/doi/10.1137/18M119896X)
frames coupled-sampler performance via transport (abstract checked);
[Jansons–Metcalfe](https://discovery.ucl.ac.uk/id/eprint/24396/) studies numerical
optimal Markovian coupling (repository abstract checked);
[Reid et al., ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3764a9c8abc84c7482f778fefc24f10b-Abstract-Conference.html)
derives domain-specific variance-reducing couplings for random features (abstract
checked). These are overlap warnings, not fully audited competing algorithms.

## Precise possible gap, still unresolved

The scoped possibility is a cheap coupling whose objective comes from actual
optimizer and adaptive-selection equations, with a provable approximation to the
**terminal** paired second moment and a complete cost advantage on a nontrivial
class that includes locally self-reinforcing learning. The scalar quantile special
case and generic Bellman approximation lemma do not fill this gap. Need both a
technical feature absent from the closest work and evidence that it matters.

Full probability access and all-action gradients make this toy a favorable setting.
A positive result could still fail on autoregressive sequences where the action
space is huge. Conversely, an oracle tie only rejects opportunity within the
specified coupling class and test regime, not all possible attribution methods.

Before a method claim, resolve whether a cost-aware learned pair-state coupling
already captures the same update structure; whether an apparently new bound is a
standard approximate-control argument; and whether the gain survives ordered CRN,
conditional terminal averaging, full fitting cost and unfavourable feedback.

## Search coverage and limits

Web searches and primary reads were conducted on 2026-09-24. Queries included:

1. Exact titles of all six required papers; exact title of Non-Local Data Attribution.
2. `"Data Attribution in Adaptive Learning" coupling`, then its exact title with
   mirrors excluded and with `September 2026 citation`.
3. `"adaptive" "training" "coupling" "attribution" variance`;
   `"training data attribution" "coupling" variance 2026`.
4. `"adaptive learning" "attribution" "coupling" after:2026-04-06 before:2026-09-25`.
5. `"Learning Generalized Gumbel-max Causal Mechanisms" coupling 2025 2026 variance`;
   `"Learning Generalized Gumbel-max" "2026"`; `"learning couplings" "variance" "2026"`.
6. `"optimal coupling" "stochastic gradient" variance reduction`;
   `"Markov" "coupling" "variance reduction" optimal transport finite difference`.
7. `"bicausal" "Markov" "dynamic programming" coupling`;
   `"optimal Markovian coupling" finite horizon`;
   `"common random numbers" "monotone" optimal coupling simulation`.
8. `"variance reducing" "couplings" "random features" optimal transport`;
   exact-title Snapshot search; citation follow-through from Rege's bibliography.

Dates were checked against primary records where used. Sources were considered
through the current date; no reliable exhaustive forward-citation index was
retrieved. The dated searches did not establish a later paper resolving our exact
candidate gap. That is a search limitation, **not evidence of novelty**. Before
committing to a paper, conduct a full forward-citation pass on Rege, Lorberbom,
Anderson, Moulos, and recent coupled stochastic-gradient literature. The original
screening note already rules out broad descendant-, selection-, and order-based
claims; those avenues were not reopened or independently cleared here.

## Estimand alignment for implementation

All exact simulators use the same occurrence, prefix, step execution, score and
horizon. A generic first-order baseline differentiates this very simulator's
expected terminal score at w_t=1, then extrapolates by -1; its error at suppression
is measured, not assumed small. A fixed-log version differentiates the fixed-log
target and is labeled accordingly.

Native RFT-Inf and CROPI are not algorithms for our quadratic toy's exact target.
An optional gradient-alignment score inspired by them must be named a proxy, state
the adaptation and any dev-only calibration, and report raw rank/sign diagnostics
separately. Do not call a raw cosine's difference from Delta “bias.” A future RL
comparison needs a separate, faithful implementation and explicit intervention
mapping; flipping RFT-Inf's sign alone does not align attribution units.
