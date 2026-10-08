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

## Authorized implementation steps 1–3, 2026-09-24 (in progress)

The user authorized diagnosing the handoff, building the tiny learner/exact
attribution calculator, and ordinary-coupling/oracle headroom checks. Opus owns
substantive implementation; GPT provides briefs, checks and integration. No
learned/proposed coupling, GPU training, publication or Git initialization.

- Local Python 3.11 environment `.venv` and `requirements-pilot.lock` are ready.
  Prepared isolated copy: `tmp/claude-workspaces/pilot-core/workspace`; manifest
  records original hashes. The reviewed core was subsequently integrated below.
- Short diagnostic runs `20260924T125732Z-f5299332` (response) and
  `20260924T125806Z-d4bcc927` (Read tool) returned successfully with modelUsage
  `claude-opus-5-5`. These demonstrate routing and reading, not substantive work.
- Broad implementation run `20260924T132716Z-8beab313` was explicitly interrupted
  after about eight minutes without files. Narrow run `20260924T133632Z-7a3422a9`
  timed out at 300 seconds without files or final modelUsage.
- Explicit instrumented retry `20260924T134151Z-38c18e3b` returned successfully,
  exit0, modelUsage `claude-opus-5-5`, with `pilot/process.py` and `__init__.py`.
  Launcher cap900s superseded the brief's earlier300s cap. Requested effort stayed
  max; effective internal effort is not independently reported. A temporary
  adapter used stream-json plus partial-message metadata and converted the final
  result back to JSON; model/permission settings were unchanged. Evidence is
  archived with the run. It showed prolonged generation before the first edit,
  not a tool denial. The precise cause of earlier uninstrumented timeouts remains
  unproved. No output-token or effort setting was lowered.
- GPT inspected the actual process files and checked weight0 momentum/decay and
  counter semantics, alpha0, and all five canonical configurations (exit0).
  Non-author GPT reviewer `pilot_code_review` independently checked 14,400
  transitions and found no material primary-grid defect. It found an extreme
  finite-value overflow in unused weight0 gradient computation. The fix and
  regression are assigned in `.ai/briefs/pilot-couplings-oracle.md`.
- Exact-enumeration/tests run `20260924T134945Z-27ab64ab` returned code and exact
  modelUsage. Launcher status is `incomplete`: Opus attempted a compound shell
  inspection outside its narrow Bash allowance, which was denied. It recovered
  with Read/Glob and successfully ran the allowed pytest command. GPT then ran
  pytest independently: 48 passed, exit0, and six preimplementation 60-digit
  fixtures agreed to <=1.60e-16. The earlier process files were unchanged. No
  permission bypass was used; the denial remains in the archived evidence.
- Core files were integrated after matching reviewed source hashes and confirming
  every destination was still absent. GPT made a small reviewer-requested guard
  fix: local and terminal mass tolerance1e-12, with rejection and no normalization,
  plus two fault-injection tests. README now specifies Python3.11. Root pytest:
  50 passed, exit0. Reviewer `pilot_code_review` confirmed the guard and both signs
  of accumulated error. Reviewed root exact.py hash
  `4f44cb6e377500474e20acb295f8f0601d1388a76d9f41628b992ca66e0740bf`;
  test_core.py hash `18170ca2b5df9fd61afbe0be8b0231ab77aba2bbdaad111a11adb65ee3f95939`.
  The isolated exact.py/tests remain at the Opus version while it works on other
  files; preserve the lead's root guards during later integration. Receipt:
  `tmp/pilot-implementation/core-integration.json`. The extreme-value process fix
  remains assigned to the active Opus call.
- Baselines/oracle run `20260924T140107Z-ae25265c` is in progress, bounded at
  16 turns/1800 seconds with the same pinned model and requested max effort.
  This includes a minimal single-cell CLI for GPT verification. A drafted broad
  runner brief `pilot-headroom-runner.md` remains undispatched; a general runner
  framework is unnecessary for this pass.
- Frozen before measurement: `research/pilot/headroom-manifest-v1.json`, SHA256
  `62f7bcc4d85d291bca20234b68fe3c3d287bdc2401afeaa4c1022f7dc1c57999`, contains
  2160 cells and the prespecified H1->H2->conditional-H4 gate and resource caps.
  No oracle measurement, variance advantage or practical speedup exists yet.

### User removes Claude limits, 2026-09-24

The user said: "no need for a limit it will take as long as it needs to for claude".
This supersedes prior Claude time/turn budgets, including the active call. The
root launcher now defaults both to None and omits --max-turns; explicit positive
caps remain possible only if the user later requests them. AGENTS/WORKFLOW and
the task template record the new preference. All26 launcher tests pass, including
an actual fake-CLI run with null limit metadata and no max-turns flag.
Non-author reviewer `pilot_code_review` confirmed no cap reaches worker execution
by default and all model/effort/permission controls remain. Its seven targeted
offline checks passed. Reviewed launcher SHA256
`047b0cc3dbfeac8c5813246c60a117da9cf83150852b13bcd3af059c572e755e`;
test SHA256 `9cf7bfa8d1c912cb584e6b15cae5cddc9f8918d4734bb7fc2e770de36b4e5c3c`.

The current CLI cannot have its parsed flags changed in place. To preserve its
work, GPT suspended only timed supervisor PID7469; worker PID7476 continues in its
separate process group. Temporary guardian
`tmp/pilot-implementation/continue_without_deadline.py` resumes the supervisor
after the worker exits so it reaps the actual result before checking elapsed
timeout. An isolated subprocess regression confirms this behavior. Evidence:
active run `deadline-override.json` and `tmp/pilot-implementation/deadline-override-check.json`.
Guardian exec session48928 and original session77559 must be collected on completion.
The already-parsed CLI16-turn cap remains a technical limit for this one call;
if reached, preserve its files and continue with an uncapped handoff. No restart,
model/effort change, or permission bypass occurred. Scientific experiment caps
remain as frozen; the user changed Claude execution limits specifically.

The current stream reports a per-response max_tokens stop after128000 thinking
tokens, then automatic CLI continuation. This is a provider/CLI response limit,
not a newly imposed GPT budget. Final modelUsage is still pending.

A broad process-list diagnostic accidentally included an unrelated Cursor API
credential in tool output. GPT notified the user to rotate it before sharing the
transcript, did not reproduce or use it, and now filters process diagnostics before
printing. Do not copy that credential into reports, briefs or reviews.

Independent 60-digit reference means for six A1/B1 H0/H1/H2 fixtures are saved in
`tmp/pilot-implementation/reference-fixtures.json`. They were computed directly
from the stated equations before the production implementation. Earlier research
and review artifacts are preserved; the initial hash snapshot is
`tmp/pilot-implementation/starting-hashes.json`.

### Coupling implementation returned; focused corrections active

Run `20260924T140107Z-ae25265c` returned successfully at14:38:30 UTC, exit0,
with modelUsage `claude-opus-5-5`. Requested effort remained max. The guardian
and original supervisor sessions were collected; neither remains active. Final
usage reported253938 outputTokens and224066 thinkingTokens. Diagnostic stream
and debug log were archived inside that run; no private thinking is quoted.

Opus implemented six ordinary couplings, Bellman co-adapted oracle, noncausal
terminal OT reference and single-cell JSON CLI. GPT ran the isolated suite:
110 passed,1 failed at that snapshot. Independent checks passed:18 finite-vertex
transport fixtures,144 pair checks across24 cells, mean error<=1.95e-16.
Non-author GPT reviewer pilot_code_review checked240 local couplings, independent
exponential-race quadrature, scalar Bellman vertices including momentum/decay,
and actual operation counts. It confirmed the weight0 overflow fix.

Four focused corrections remain: misleading certified-gap claims omit original
cost residuals; matrix backing can be made writable; one independent quadrature
reference fails to converge; headroom rejects large H only after enumeration.
Brief `.ai/briefs/pilot-review-fixes.md` includes exact counterexamples and
acceptance checks. Run `20260924T144213Z-8bea405c` is active with no timeout or
max-turns argument. Numerical work remains with Opus. Before dispatch the lead
synced its guarded exact.py/core tests and current instructions into isolation,
checking old hashes. Receipt: tmp/pilot-implementation/review-fix-lead-sync.json.
No headroom measurements have started. Verification scripts prepared under
tmp/pilot-implementation orchestrate existing Opus APIs, keep the frozen manifest
and experiment caps, and include child plus parent CPU cost.

The lead's measurement orchestration received a separate non-author review.
It now checks all recorded source hashes before dispatch, after cells and at
finalization, invalidates mixed-source campaigns, and accounts for spawn failures,
timeouts and in-flight work. Process-group termination also handles an exited
leader whose descendant still holds stdout/stderr. Five fake-cell fault-injection
scenarios passed; these were disposable verification fixtures, not pilot results.
Receipt: tmp/pilot-implementation/grid-orchestration-checks.json. Reviewer
confirmed the last descendant-pipe fix independently in0.103s for a0.1s limit.
Reviewed run_frozen_grid.py hash:
`b52507684b3b1ecbfce98a636a4ac0380a9699699808b85fa14121f9bbf642ce`.
All24 pre-existing research files still match the starting snapshot.

### Focused correction pass returned

Run `20260924T144213Z-8bea405c` finished with exact modelUsage claude-opus-5-5,
requested max effort, no timeout/max-turns, and80 reported turns. Its process exit
was0; launcher status remains incomplete because a Python exploration snippet
and outside-workspace SciPy-source Grep were denied. Opus recovered through the
allowed pytest checks; no permission bypass or model substitution. Raw evidence
and diagnostic stream remain in that run. Both author and lead final isolated
pytest passed126 tests (lead1.14s). The brief's older91/1 baseline was stale; the
final initial snapshot had115 passes and the known quadrature failure.

The four fixes are implemented: original-cost residual charges and explicitly
numerical gap estimates; immutable bytes-backed matrices; convergent log-ratio
quadrature; an early supported-horizon guard. GPT accepts an additional
pre-measurement check: per-oracle and accumulated absolute gap estimates<=1e-12.
Distance-baseline gaps remain reported in their own squared-distance units.
This is a numerical check, not a certified error bound or an extra headroom gate.
The frozen manifest and20%/variance-threshold gate remain unchanged.

Weaknesses explicitly remain: float64 arithmetic and approximate marginal
feasibility; one-sided gap estimates; small-variance sensitivity. Solver-free
checks support covered cells but do not create a universal precision guarantee.
A K1 high-horizon recursion issue is outside the canonical K3 CLI and primary
grid. Breaking diagnostic renames have no root consumers yet; analysis exports
read dynamic fields. Final workspace hashes are in
tmp/pilot-implementation/final-workspace-hashes.json. Non-author closure review
is finishing before integration; all root destinations and protected core hashes
were checked for concurrent edits.

### Integrated and measuring

Non-author final closure review passed16 targeted checks and confirmed hashes.
All seven reviewed implementation/test files were integrated after checking
source and destination hashes; the lead's exact.py/core mass guards were
preserved. Receipt: tmp/pilot-implementation/coupling-integration.json. Root
pytest:126 passed in1.11s, exit0. README documents the single-cell CLI and
numerical limitations. No Git initialization or publication.

Frozen-grid campaign started at15:07:26 UTC in
research/pilot/runs/20260924T150726Z with source hashes, four single-threaded
BLAS-configured worker processes, the frozen experiment caps, and unchanged
manifest62f7bcc4d85d291bca20234b68fe3c3d287bdc2401afeaa4c1022f7dc1c57999.
Exec session14064; progress log tmp/pilot-implementation/grid-run.log. H1 thenH2;
H4 depends on the prespecified B-family headroom gate. Do not edit tracked
sources while this campaign is active. Report measurements only after checking
summary/provenance/censoring. No fitting, proposed rule or GPU study launched.

### Steps1–3 complete: short-horizon gate failed as prespecified

Campaign20260924T150726Z completed720 H1 plus720 H2 cells, all numerical checks
passed, zero errors/censoring. All720 H4 cells were left unrun because no
nondegenerate B-family cell reached20% headroom. Source provenance stayed valid
and the process session14064 was collected, exit0. Total measured CPU763.934s
including child/import and parent work. No experiment cap was reached.

B-family maximum:18.4780209978% (B1 beta8 eta0.4 theta(-0.4,0), action0 alpha0.25
H2). Strongest full-suppression B case:14.1150400698%. Scalar A2 reaches25.4453%
in two cells; the frozen gate explicitly excludes scalar cells. This does not
show an absence of longer-horizon headroom or a practical method's speedup.

Non-author reviewer independently recomputed all six baselines and the oracle
for both B witnesses and the strongest A2 witness using65-digit direct equations,
finite transport vertices and numerical Gumbel quadrature without production
imports. All variance differences<3.37e-18; maximum ratio difference1.03e-15.
It also verified the manifest counts, B-only gate, errors/censoring and720 unrun
H4 cells. Receipt: research/pilot/runs/20260924T150726Z/independent-witness-checks.json.

Final report: research/pilot/IMPLEMENTATION_RESULTS.md. Run folder contains all
1440 cell JSON records plus cells.csv with all2160 planned rows, groups.csv,
slots.csv (480 complete action-probability-weighted conditional summaries),
metrics.json, summary.json and hashed runtime/source metadata. Prior24 research
files match their starting hashes. Final integration/verification receipts are
under tmp/pilot-implementation/. Root tests126 passed; launcher tests26 passed.
All authorized steps1–3 are complete. No active Claude, measurement or review
call remains. No proposed/learned coupling, practical timing study, GPU training,
Git repository or publication was introduced. A future scientific extension
requires a justified revised pilot, not a retrospective change to this gate.

User preference persists: Claude implementation calls have no imposed time or
turn limit; exact model claude-opus-5-5 and requested max effort remain pinned.
The earlier accidental Cursor credential exposure still requires user rotation;
no value was repeated in artifacts and no account setting was changed.
