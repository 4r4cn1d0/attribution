# Bounded implementation: tiny learner and exact marginal calculator

- Task ID: pilot-a. User authorized steps 1–3: route diagnosis, learner/exact attribution calculator, baseline/oracle results. This brief implements the learner and exact marginal truth only.
- Role: implementation. Model claude-opus-5-5, effort max. You are a worker, not the lead; do not launch agents or invoke Claude/Codex. Others are working: preserve their changes and touch only owned files.
- Context: the concrete equations below are authoritative, distilled from research/scoping/THEORY.md and PILOT_SPEC.md. Do NOT spend turns reading the full research corpus. No need for web research or a new research proposal.
- Workspace: launcher-prepared pilot-core/workspace, never the original project.
- Owned files: pilot/__init__.py, pilot/process.py, pilot/exact.py (marginal portion), pilot/tests/test_process.py, pilot/tests/test_marginal.py, pilot/README.md. Do not edit shared .ai files or existing research artifacts.
- Budget: 12 turns / 900 seconds. Keep implementation compact (roughly 300–500 substantive lines total). This is production code, not pseudocode. Implement now and return actual file list and checks.
- Permitted shell command, if needed: /Users/spiderishi/Coding/attribution/.venv/bin/python -m pytest -q pilot/tests . No other shell/installs. Existing isolated runtime has numpy/scipy/mpmath/pytest. Use Read/Write/Edit for files; tests can be run by GPT if tool limits prevent you.

## Before code
Briefly compare two plausible representations/traversals (e.g. immutable state plus recursion versus explicit history enumeration) and choose one. This is a bounded implementation choice, not another open-ended ideation pass. Observable success is correct finite-state probabilities and suppression semantics checked independently.

## Required API and equations
Design simple public typed APIs to be extended by the next brief. Prefer immutable frozen dataclasses with tuples so states cannot silently mutate; no float rounding or approximate state merging. Validate dimensions, finite inputs, horizon/weights, and config identity appropriately.

Config: family A scalar, family B d-dimensional feature regression; phi is Kxd array/tuples, targets v or r length K, beta>=0, offsets b length K, eta in (0,1], mu in [0,1), weight_decay>=0, q unit-length score direction. Scalar A has d=1. Complete state: theta tuple, momentum tuple, integer counter. Primary cases mu=weight_decay=0 and constant eta, but preserve nonzero momentum/decay semantics.

p_theta(a)=softmax(beta*phi_a dot theta+b_a), stable arithmetic.
Data gradient: family A grad=theta-v_a; family B grad=(phi_a dot theta-r_a)*phi_a.
At EVERY update with supplied sample weight w:
m_new=mu*m+w*grad; theta_new=(1-eta*weight_decay)*theta-eta*m_new; counter+=1.
Suppressed occurrence uses w=1-alpha, ordinary w=1, from the SAME fixed pre-event state and observed action. alpha in [0,1]. Thus full suppression still evolves momentum, decay and counter. Future updates always use w=1 and each world samples using its own theta-dependent probabilities.
Score is stable sigmoid(q dot theta), bounded [0,1].

Required functions (names may vary if clearly documented): probs(config,state); apply_event(config,state,action,weight=1); successors(config,state,weight=1); score(config,state); intervention_pair(config,pre_state,action,alpha=1).

Exact marginal evaluator: enumerate all K^H future action paths, recomputing each world's probabilities and gradients at its current state. Return terminal law with path probabilities/states/score, total mass, mean, second moment, and basic count of probability evaluations, successor/optimizer updates, terminal scores, nodes/leaves. Use math.fsum/compensated summation. H=0 returns the supplied post-event state. H is future updates, not total T. Exact means exhaustive float64 sums, not exact symbolic arithmetic.
Exact attribution: two separately enumerated terminal laws; delta=mean_suppressed-mean_ordinary. Include observed prefix action probability as metadata, not an extra weighting of this conditional delta. Do not cache factual gradients for changed states.

Provide canonical config constructors for five instances for reuse:
A1 phi=(-1,0,1),v=(-1,0,1); A2 same phi,v=(0,1,-1); A3 same phi,v=(1,0,-1).
B1 phi=((1,0),(0,1),(1,1)/sqrt(2)),r=(1,-1,.5).
B2 phi=((1,0),(1,.2)/sqrt(1.04),(1,-.2)/sqrt(1.04)),r=(-1,0,1).
b=0,q=(1) or (1,0). beta and eta adjustable. Initial m=0,counter=0.

## Meaningful checks
1. H=0/H=1 explicit formulas, action probabilities/mass sums, all K^H leaves.
2. alpha=0 yields equal start states and zero delta.
3. theta=.2,m=.3,mu=.9,eta=.1,decay=.1,w=0 gives m_new=.27,theta_new=.171,counter increments; differs from skipping.
4. Nontrivial family B gradients manually checked.
5. Independent mpmath 50-digit H=2 exhaustive reference (at least A1 and B1), error <=1e-10. Reference must not call production update/probability functions.
6. Input validation and state immutability; previous states remain unchanged.

Document how to run and the score/intervention/index convention briefly in README. No projected method, learned coupling, benchmark runner, GPU code or experiment runs in this slice.

## GPT questions to answer in final response
What is the weakest numeric assumption? Which simpler alternative did you reject and why? What counterexample/check would catch incorrect suppression or future-law handling? Which acceptance items are passed versus not tested? Do not claim identity/effective effort beyond launcher evidence.
