# Definitions, derivations, and proof obligations

Status: scoping mathematics, 2026-09-24. Statements below explicitly distinguish
elementary derivations from unproved research targets. No new efficiency theorem
is established. Indexing and the sign of Delta follow SCOPE.md.

## 1. Exact process and intervention

Let Z_j ~ K_j(.|S_(j-1)); S_j=U_j(S_(j-1),Z_j,w_j). State contains every
variable affecting subsequent transitions, including time. After fixing h_t,
set x_0=U_t(S_(t-1),Z_t,0), y_0=U_t(S_(t-1),Z_t,1), and run H=T-t further
updates with w=1 in both worlds. x denotes suppressed, y ordinary.

For a mini-batch, interpret the data gradient as B^-1 sum_i w_i grad ell_i with
the original denominator B. The pilot uses B=1 and the explicit optimizer

    m_j = mu m_(j-1) + w_j grad ell_(Z_j)(theta_(j-1))
    theta_j = (1-eta_j lambda) theta_(j-1) - eta_j m_j
    counter_j = counter_(j-1)+1.

At t the suppressed world still decays momentum, applies decoupled weight decay,
and advances the schedule. Any deterministic regularizer would be added separately
and not suppressed; none is used in the core pilot. mu=lambda=0 and constant eta
are primary. Momentum is a specified sensitivity check, not a silently omitted
state variable. This convention deliberately differs from skipping U_t entirely.

Finite-action selector, with fixed features phi_a and offsets b_a:

    p_theta(a) = softmax_a(beta phi_a^T theta + b_a).

It maximizes expected compatibility plus categorical entropy (unit entropy
coefficient in these scaled logits). This is **entropy-regularized selection**,
not a claim that the data-loss optimizer itself uses an entropy penalty or PPO.
beta=0 gives an exogenous stream. Future data include sampled action and its fixed
target/reward. Two primary learning families:

* A, scalar affine: ell_a(theta)=(theta-v_a)^2/2, v_a in [-1,1]. With
  0<eta<=1 and mu=lambda=0, U_a(theta)=(1-eta)theta+eta v_a stays in [-1,1]
  if initialized there. phi_a controls selection and need not equal v_a.
* B, two-dimensional feature regression: ell_a(theta)=(phi_a^T theta-r_a)^2/2,
  ||phi_a||<=1, |r_a|<=1. U_a(theta)=(I-eta phi_a phi_a^T)theta+eta r_a phi_a.
  With eta<=1, ||theta_j|| <= ||theta_0||+j eta is a sufficient finite-horizon
  bound. No projection, clipping, continuous reward noise, or state rounding.

Main score g(theta)=sigmoid(q^T theta), ||q||=1, hence 0<g<1 and Lipschitz
constant <=1/4. Use g=(theta+1)/2 only in bounded scalar diagnostic examples;
threshold scores are separate nonsmooth stress tests. Finite action branching
implies finitely many reachable states for fixed H, even though parameters are real.

## 2. Exact marginals and unbiasedness — elementary derivation

At every paired state (x,y), choose a nonnegative matrix pi with row sums p_x
and column sums p_y. Draw (A,B)~pi and apply U_A(x),U_B(y). Conditioning on the
entire joint past, each next marginal is its prescribed kernel. Induction therefore
gives the correct full marginal path laws. For independent paired replications,

    Y = g(theta_H^x)-g(theta_H^y),   E[Y]=Delta,   MSE(mean_N Y)=Var(Y)/N.

A fitted coupling frozen before evaluation also satisfies this statement if its
architecture preserves marginals. Approximate Sinkhorn row/column sums alone are
not an exact construction. The pilot must check them, use a valid correction, and
record numerical tolerance. Exact mathematical marginals and floating-point
verification are different claims.

For sorted scalar successor scores u_a,v_b, let I_a,J_b be intervals partitioning
[0,1] with lengths p_x(a),p_y(b), ordered by their scores. Set pi_ab=|I_a intersect
J_b|. The intervals prove the marginal constraints; sorting and a two-pointer scan
cost O(K log K) after scores are available. An exchange argument shows this
minimizes E[(u_A-v_B)^2]: an inverted pairing can be uncrossed, reducing cost by
2(u_2-u_1)(v_2-v_1) times the exchanged mass. This is standard monotone transport,
not new theory. With a scalar affine learner and linear terminal score at H=1,
update sorting equals a correctly ordered common-uniform baseline exactly.
More strongly, in family A **any nonzero shared scalar projection** orders the
successors by v_a or reverses that order in both worlds. Reversing both probability
interval partitions leaves their intersection masses unchanged. Thus the proposed
projected rule equals v-sorted CRN at every decision and every horizon (apart from
the explicitly specified zero-direction fallback). Family A cannot demonstrate
novel separation; it is a correctness and failure diagnostic.

For exact enumeration of shared-Gumbel coupling, positive p,q admit an elementary
joint-mass calculation. Write G_k=-log E_k with independent E_k~Exp(1); argmax
(log p_k+G_k)=argmin E_k/p_k. The diagonal mass is

    pi_ii = 1 / sum_k max(p_k/p_i, q_k/q_i).

For i!=j, set l=p_j/p_i and u=q_j/q_i. If u<=l the joint mass is zero; otherwise

    pi_ij = integral_l^u [1+r+sum_(k!=i,j) max(p_k/p_i,r*q_k/q_j)]^(-2) dr.

Partition at r=(p_k/p_i)/(q_k/q_j). On each interval the denominator is A+B r,
so the integral is (u-l)/[(A+B l)(A+B u)]. This follows by substituting E_i=t,
E_j=r t and integrating t exp(-t[A+B r]) over t. It yields a finite arithmetic
reference for the joint matrix, to be checked numerically; it is not a new method.

## 3. Oracle class and objective — established dynamic-programming construction

Primary oracle is the time-inhomogeneous, co-adapted Markov coupling over the
complete pair state. It may use both current states and known transition tables,
but cannot inspect future random draws. Its objective is terminal second moment:

    V_H(x,y) = (g(theta_x)-g(theta_y))^2
    V_j(x,y) = min_{pi in Pi(p_x,p_y)} sum_ab pi_ab V_(j+1)(U_a(x),U_b(y)).

Here j=0,...,H indexes elapsed future rounds; U and p include the absolute time.
Subtract Delta^2 from V_0 for the minimum variance. Fixed marginals make the mean
coupling-invariant. Finite-horizon Bellman induction proves the recursion; it also
allows Markovization of history-dependent co-adapted policies for this fully
observed terminal-cost problem. Do not generalize this assertion to arbitrary
path constraints or partially observed state. Moulos's Markov transport work is
an explicit precedent; our terminal-cost use is an elementary specialization.

Separately sort exact terminal g distributions to obtain an unrestricted terminal
transport lower bound. Such a coupling can require noncausal path coordination
and is not the online oracle above. Computing either full tree is expensive:
up to K^H marginal leaves and K^(2H) paired leaves, with transport solves at
internal pair nodes. Store and count construction work; never report the oracle
as a free implementable speedup.

## 4. Practical mechanism to test — hypothesis

For the mu=lambda=0 core define F(theta)=sum_a p_theta(a) U_a(theta). Its actual
mean-update Jacobian is

    DF = sum_a p_a DU_a
       + beta sum_a p_a (U_a-F)(phi_a-E_p phi)^T.

The second term is data-collection feedback; using only optimizer Jacobians omits
it. If h decisions remain, let z_0=(theta_x+theta_y)/2 and z_k=F(z_(k-1)),
k=1,...,h (use time-indexed F for schedules). Set

    w = [DF(z_(h-1)) ... DF(z_1)]^T grad g(z_h).

The product is identity for h=1: there are h-1 continuation Jacobians **after**
the currently scored successor. The current DF(z_0) is excluded. Score current
action successors by w^T U_a(x), w^T U_b(y), then use sorted overlap.
With zero direction use fixed label order, with ties use ascending action ID.
This rule is fully specified without evaluation fitting; main ablations use
w=grad g(midpoint) and a quadratic full-successor-distance transport.

The mean trajectory is not E[theta_j] in a nonlinear adaptive process, and its
projected score is not the Bellman pair cost. No optimality is claimed. The rule
costs all K candidate gradients per world, probabilities, the mean rollout and
Jacobians. A naive dense implementation costs O(H K d^2) per coupling decision,
in addition to the genuine two updates, and O(H^2 K d^2) across a continuation.
Rank-one structure or cached work may reduce this only if explicitly implemented
and measured. A same-state cache must not substitute factual gradients at altered
states. Novelty, if any, must go beyond this generic projection/transport recipe.

## 5. Research theorem targets and missing obligations

**Generic approximation lemma (derived, not novel).** Suppose the score cost
C_j(a,b) approximates Q*_j(a,b)=V*_(j+1)(U_a(x),U_b(y)) uniformly to eps_j,
up to arbitrary row-only and column-only terms, uniformly over all pair states
reachable under the surrogate policy. A coupling minimizing C_j incurs
at most 2 eps_j extra one-step optimal continuation cost. Backward induction gives
second-moment regret <=2 sum_j eps_j, and the same variance regret because the
mean is fixed. Proof: insert and subtract C for its minimizer and the optimal
pi; its minimizing term is nonpositive, and each remaining error is <=eps_j.

**Unproved target A.** Derive computable eps_j from the specific update equations,
including policy sensitivity, future conditional variance, horizon H, initial
finite displacement delta=||x_0-y_0||, eta and beta. Show a nonempty regime with
locally expansive feedback where the bound is informative and construction is
cheaper than computing V*. Merely assuming a small eps_j or global contraction
does not achieve the contribution. Squared differences of continuation means
omit future innovation covariance; bounding means alone is insufficient.

**Unproved target B.** Exhibit an open parameter region, robust to label
permutations, where practical variance times full continuation cost beats the
best common randomness/maximal/learned alternative by a constant factor after
setup. A hand-picked one-step reversal does not establish this. A theorem must
state its comparator class; superiority to every learned coupling is generally
impossible if that class contains the proposed mechanism.

For unbiased method m with setup F_m, per-pair expected cost c_m and variance V_m,
the diagnostic cost for target MSE e^2 is F_m+c_m max(1,ceil(V_m/e^2)). This is a
known-variance design calculation, not a finite-sample confidence guarantee.
For biased alternatives replace e^2 by e^2-b_m^2 when positive. Count indivisible
sample costs and reuse of setup across a prespecified number of requests.

## 6. Derivable limits and counterexamples

* Scalar positive feedback: E[theta'|theta]=(1-eta)theta+eta E_p[v]. Its derivative
  is 1-eta+eta beta Cov_p(v,phi). At theta=0, b=0, v=phi=(-1,0,1), this is
  1-eta+(2/3)eta beta. It exceeds one for beta>1.5. Thus an individually
  contractive update does not imply contractive adaptive mean dynamics.
* For maximal action agreement in family A, d=|x-y|, a=1-eta, D=max v-min v,
  mismatch probability TV(p_x,p_y)<=min(1,L_p d). Direct expansion gives
  E[d_next^2|x,y] <= a^2 d^2+(2a eta D d+eta^2 D^2)min(1,L_p d),
  with L_p<=beta(max phi-min phi)/2 sufficient in the scalar case. The O(d)
  term can dominate d^2. This bound may grow or be loose; it is not a promised
  efficiency result or a correction-moment theorem.
* Maximizing action agreement is not terminal optimality: two uniform actions
  can have terminal scores (0,1) in one world and (1,0) in the other. Same-action
  coupling has Y=+/-1; cross-action coupling has Y=0. This is an abstract
  one-step kernel counterexample, not proof that the primary learner realizes it.
* A learned/scored projection can discard a direction that controls later action
  probabilities. Small one-step distance then need not imply small terminal Y.
* Mean truncation bias zero does not imply small correction second moment:
  D=+1 or -1 with equal probability has E[D]=0 and E[D^2]=1.
* Fixing future samples does not fix the altered gradient. For ell_z(theta)=
  (theta-z)^2/2, a factual cached gradient differs by theta_cf-theta_factual.
  Reusing it changes even the replay dynamics. Replayed tails still cost updates.
* Shared terminal query noise must be coupled with correct query marginals too.
  A simulator-correct coupling cannot repair a misspecified environment model.

No multilevel or randomized-debiasing construction is selected. If reconsidered,
derive finite-suppression truncation bias and coupled correction E[D_l^2]
separately, include the base level and full tail work, and compare the complete
sum_l sqrt(E[D_l^2] c_l) diagnostic to full paired runs. The cited adaptive
paper's Theorem 6/Corollary 2 concern derivatives at zero perturbation and cannot
be silently imported as finite-suppression guarantees.
