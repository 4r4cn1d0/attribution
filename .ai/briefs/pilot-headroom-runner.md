# Frozen baseline/oracle headroom runner

Authorized step 3 only. claude-opus-5-5, effort max. Worker, not lead; no
agents or Claude/Codex invocation, no shared handoff edits or external writes.
Others are working; preserve their edits. Prepared pilot-core/workspace only.
Dispatch after process, exact, couplings and pair APIs pass review.
Own pilot/run_headroom.py, pilot/configs/headroom-v1.json and runner tests.
Read the four existing modules and reuse their APIs. Budget 12 turns/900 seconds.
No experiment launch by this worker; GPT runs the frozen manifest afterwards.

Write the simplest reproducible CPU exactness/headroom runner, not a full
simulation or fitting framework. Freeze JSON manifest and SHA256 before any cell.
Grid: families A1,A2,A3,B1,B2; beta0,1,3,8; eta.1,.4; initial scalar-.4,0,.4
(B uses (x,0)); observed action0,1,2; alpha1,.25; H1,2,4. 720 cells per H.
Primary alpha1; secondary alpha.25 reported separately. No data/model training,
random estimator experiment, learned/proposed coupling or matched-cost claim.

Stage order all H1, then H2, then H4 only if H<=2 correctness holds and there
is at least one nondegenerate B cell with >=20% variance improvement of oracle
over the best implemented ordinary coupling. Ordinary methods: independent,
label-CDF, ordered-CDF, shared Gumbel, maximal, full-update-distance transport.
Use exact finite-tree moments, never Monte Carlo for these measurements.
Zero-variance cells (ordinary variance<=1e-14) remain explicitly reported.
Compute terminal-score unrestricted OT lower bound separately. No causal claim
for this bound. Full deterministic terminal averaging computes Delta directly;
record its exact-enumeration reference cost and variance0 as a cheap competitor
at small H, but exclude it from the specifically paired-coupling headroom ratio.
Do not equate that ratio with practical performance or scientific novelty.

Each target record includes manifest/source/dependency hashes, full parameter
identity, prestate/action probability, alpha/H, both marginal means, Delta,
method means/second moments/variances, oracle/lower bound, local residuals,
maximum oracle gap, actual work counts, per-method construction CPU/wall times,
peak RSS, status and explicit error/censor reason. Charge all enumeration and
oracle construction separately; no online speedup measurement exists here.
Correctness stops the run on mass error>1e-12, negative mass<-1e-14,
local residual>1e-12, pair-mean disagreement>1e-10 or material oracle ordering
violation. Tiny variance clamping must be exposed, not silently hide a failure.

Initial cap60s/cell; 8 CPU-hour total,8GiB RSS. Use a child process per cell so
timeouts can terminate computation cleanly. Preserve censored records; don't
drop them or convert to zeros. Resume skips only completed matching-hash cells.
Write each cell record atomically; maintain a simple completed/censored/error
summary by H/family/alpha and the headroom gate. Missing cells prevent a complete
grid verdict. Source changes invalidate resume. Avoid claiming the cap is hard
if your implementation can only sample/check a resource at cell boundaries.

Provide CLI with output directory, manifest path and optional explicit stage
selection for smoke verification. A smoke run is separately labeled. Tests
should establish grid counts, deterministic identities, resumability/hash guard,
headroom handling of zero/censored cases, and actual timeout behavior. No tests
that just duplicate data. README usage may be supplied in the response for the
lead to integrate. Return files, checks actually run, limitations and objections.
