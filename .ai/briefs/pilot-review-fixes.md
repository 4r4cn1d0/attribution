# Resolve observed coupling review findings

Use claude-opus-5-5, effort max. The user explicitly removed time and turn caps;
take as long as needed. Worker, not lead: no agents, Claude/Codex, experiments or
shared handoff edits. Others are working; preserve their changes. Prepared
pilot-core/workspace only. Own couplings.py, pair.py, headroom.py and the focused
coupling/oracle tests under pilot/. Do not replace the lead's exact.py guards or
core tests. Allowed command: /Users/spiderishi/Coding/attribution/.venv/bin/python -m pytest -q pilot/tests

The non-author GPT review and independent checks found these concrete issues.
Fix them narrowly; do not redesign the ordinary methods or relax tolerances.

1. Transport's advertised certified duality/suboptimality bound is false for
accepted inputs because reduced-cost gap omits original-cost marginal residuals.
Counterexample: p=[2**-48,.5,.5-2**-48], q=[.25,.25,.5], cost has first row
[-2**48]*3 and other entries0. Every exactly feasible plan costs-1, while the
current returned plan costs0, gap0, residual3.55e-15. Prefer honest numerical
optimality diagnostics over a new rigorous interval-arithmetic framework.
Correct original-cost residual accounting if retaining an optimality estimate,
and remove claims of certification throughout couplings/pair/headroom and field
names/docs that present a numerical estimate as a theorem. Do not use an
unsupported certificate to waive correctness ordering checks. Add the exact
counterexample as a regression. Explain what the revised quantity guarantees
and does not guarantee. A simpler diagnostic is acceptable if accurately named.

2. A coupling's owning NumPy array can be made writable again with
matrix.setflags(write=True), leaving cached residual/objective evidence stale.
Use truly immutable backing (e.g. bytes-backed array) or another simple mechanism
that protects that evidence, and test the attempted writeability reset.

3. Actual pytest run: 91 passed,1 failed. Failure is
test_shared_gumbel_matches_independent_quadrature[process-A2]. For
p=(5.569742297618162e-7,.0007460284183178617,.9992534146074523),
q=(.9992534146074525,.0007460284183178619,5.569742297618164e-7), i2,j0,
production=0.9988799828234987; direct wide-interval quad=0.9988795314990974
with an IntegrationWarning. Fix the independent numerical reference's conditioning
(log-r substitution and explicit breakpoints are an option), preserve1e-10
tolerance, and fail on a nonconverged reference rather than accepting its value.
Do not copy the production closed-form integral as the independent reference.

4. headroom.run currently computes exponential marginal enumeration before
pair._setup rejects unsupported H. Validate its supported horizon/size before
enumeration (CLI intentionally supports K3,H<=4), so --H100 cannot exhaust memory
before reaching the size guard. Add a test proving rejection precedes enumeration.

Evidence already passed: 18 independent finite-vertex LP fixtures (scaled error
<=1.11e-16), 144 pair checks across24 A1/B1 cells (max mean error1.95e-16),
oracle<=ordinary and terminalOT<=oracle, H1 equality. Reviewer independently
checked240 local couplings and exponential-race quadrature. Process zero-weight
fix and all five regressions passed review. Keep these invariants.

Return changed files, actual pytest status, answers to the residual-counterexample
question and weakest remaining numerical assumption. No speedup/novelty claim.
