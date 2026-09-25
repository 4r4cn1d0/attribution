# Ordinary couplings and co-adapted oracle

Authorized step 3; dispatch only after process and marginal enumeration pass.
Model claude-opus-5-5; effort max. Worker, not lead. No agents, Claude/Codex,
experiments, external writes or shared handoff edits. Other contributors exist;
preserve their changes. Work in the prepared pilot-core/workspace only.
Own pilot/couplings.py, pilot/pair.py, pilot/tests/test_couplings.py and
pilot/tests/test_oracle.py. Also own the single zero-weight fix described below
in pilot/process.py and its focused regression test. Read process.py and exact.py
for the public API.
User update: no imposed time or turn cap; take as long as needed. GPT runs
checks; no shell commands needed. The original dispatched brief is preserved
with its run evidence; this version records the later user instruction.

Simplest deliverable: direct exhaustive finite trees and float64 transport;
no proposed projection, learned predictor, simulation framework or caching.
Write a minimal working implementation first, then improve it against the checks.
The mathematical definitions below are settled; no literature or exhaustive
design pass is needed. Focus numerical support on the declared moderate grid;
reject unsupported inputs clearly instead of building a universal solver.
H means future updates after the intervention. Pair sign suppressed minus
ordinary. Each world uses its own conditional action probabilities at every node.

couplings.py: validated joint matrices for independent p outer q; fixed-label
shared uniform via CDF interval overlap; ordered uniform (independent action
orders for two worlds, stable ties by ID); maximal action agreement (diagonal
min(p,q) plus residual outer product / residual total); shared Gumbel; and
generic optimal transport with scipy.optimize.linprog(method='highs'). Return
matrix, marginal residual, minimum entry, objective, solve time and duality gap
as applicable. Transport must scale nonzero objective to avoid tiny-cost solver
indifference, request tightened supported tolerances, and independently check
row/column residual <=1e-12, negative masses >=-1e-14. Reject failed solves;
do not silently renormalize or clip a wrong plan. Reject invalid input vectors.

For positive p,q, shared Gumbel has diagonal
pi[i,i] = 1/sum_k max(p[k]/p[i],q[k]/q[i]). For i!=j let
l=p[j]/p[i], u=q[j]/q[i]. If u<=l, mass0; else integrate
(1+r+sum_(k!=i,j) max(p[k]/p[i], r*q[k]/q[j]))^-2 on [l,u].
Split at all interior (p[k]/p[i])/(q[k]/q[j]); within one interval
denominator is A+B*r and its integral is (right-left)/
((A+B*left)*(A+B*right)). Explicitly state numerical domain and fail clearly
on unsupported nonpositive probabilities; the pilot core uses positive p,q.

pair.py: enumerate pair first/second moments for a selected ordinary method;
ordered method uses targets for family A, successor q-coordinate for family B.
Distance baseline cost is squared Euclidean successor-theta distance.
Bellman oracle: leaf (g(x)-g(y))^2; at remaining h>0 evaluate all K^2 child
oracle values then minimize their expectation subject to row p(x), column p(y).
No rounded-state merging. Return root mean, second moment, variance, construction
counts/time and worst solver residuals/gaps. Oracle mean must agree with separate
marginal truth; clamp only roundoff-sized negative variance, expose correction.
Store enough root plan/cost evidence to test H1 manually. Also compute unrestricted
terminal-score OT by sorted marginal CDF overlap and label it as a lower bound,
not an online/co-adapted oracle. Report all reference construction cost separately.

Tests: arbitrary skewed vectors/local marginal laws; same-law diagonal/maximal;
Gumbel masses versus independent scipy quadrature and fixed-seed sampled counts;
H0/H1 hand results; pair mean equals independently enumerated Delta within1e-10;
oracle <= every feasible ordinary second moment; terminal OT <= oracle;
H1 oracle equals terminal OT. Cover A/B, beta0 and8, H2, alpha0, zero variances.
Counterexample: terminal scores(0,1) versus(1,0), uniform marginals: label matching
second moment1 while crossed optimum0. A scalar sorted method is an ordinary
baseline; do not claim novelty from label-order improvement.

Concrete GPT follow-up on the previous process implementation: a non-author
reviewer verified 14,400 ordinary-grid transitions with independent formulas.
However apply_event computes gradients even at weight0. Finite theta1e308 and
target-1e308 in family A overflow the unused gradient, then 0*inf fails despite
the suppressed update being finite (mu=decay0). Avoid evaluating that gradient
when weight0; keep momentum/decay/counter updates. Add a regression, or explain
with evidence why a different fix is safer. The previous prose also reversed
the subtraction direction: the code pair ordering was correct, and the target
remains suppressed minus ordinary. Do not reverse it. What other numerical
assumption is weakest, and what check would settle it within the primary grid?

Return actual changed files, untested checks, weakest assumption, a simpler
alternative, and the smallest numerical counterexample that could break results.

For lean reproducible verification, also own pilot/headroom.py: a single-cell
CLI accepting family,beta,eta,initial coordinate,observed action,alpha,H. Reuse
the existing APIs to print one JSON object containing the cell identity, marginal
truth, all six ordinary method moments, oracle and terminal lower bound, actual
construction timings/counts and maximum numerical residuals/gaps. Return a nonzero
exit on failed checks. Handle zero-variance cases without division. Do not run
the grid yourself. GPT will freeze the grid manifest and launch this CLI under
per-cell and total resource caps. No general runner framework is needed.
