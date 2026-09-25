# Close diagnostic validation and interpretation findings

- Authorized outcome: finish the v1 mechanism diagnostic already implemented; no new study.
- Role: bounded implementation fix and response to GPT/non-author review.
- Model: claude-opus-5-5; requested effort max; no time or turn cap.
- Workspace: tmp/claude-workspaces/mechanism-diagnostic/workspace.
- Previous author run: 20260924T161740Z-4e4431ab. Its actual code, tests, new
  diagnostic data and report are present here. The parent-run link is provenance,
  not inherited conversation. Read those local artifacts and this brief only as needed.
- Ownership: pilot/diagnose.py, pilot/tests/test_diagnose.py, and
  research/pilot/diagnostics-v1/*. Preserve the first-pass ALTERNATIVES.md; append
  clarification if needed rather than rewriting its historical rationale.
- Others are working. Preserve their edits. Do not change old modules/results,
  manifests, shared .ai/HANDOFF.md, or anything outside the prepared workspace.
- No agents, recursive Claude/Codex calls, installation, Git, publication,
  H3/H4/new sweep, fitting, GPU work, or new method development.

## Finding 1: unchecked stored variances and summaries

The non-author GPT reviewer reproduced three independent mutations in the existing
disposable run fixture, each accepted with report.ok=True and no failed checks:

1. headroom.oracle_variance=0 changes oracle N at RMSE .01 from 6 to 1.
2. headroom.best_ordinary_method='independent' reports that method as best while
   retaining distance's best variance, and attributes best_R0/R1 to the wrong rule.
3. ordinary.distance.variance=0 silently enters the output CSV.

Checked moments alone do not validate every value used in the report. The current
frozen v1 data are intact: the reviewer separately audited all1440 records and
found zero mismatch in best/oracle variances, selected best method and nondegenerate
flags, ratio disagreement <=1.11e-16, moment-to-variance disagreement <=1.09e-19.

Implement the smallest validation fix, including H1 records where their summaries
are reported. Validate stored method/oracle variances against the checked moment
convention, headroom best variance against the six method variances, selected method
attaining that minimum with legitimate ties allowed, oracle/terminal fields against
their corresponding moments/values, and nondegenerate flag and ratios against the
same definitions used by the unchanged v1 implementation. Reject nonfinite invalid
values. Do not normalize, change old data or silently repair invalid inputs.
Use appropriate explicit numerical tolerances. Add regression cases for these
mutations and relevant summary mismatches. Preserve all actual v1 numeric results.

## Finding 2: qualify interpretation, preserve the earlier alternatives record

The current allocation definition says 'upper bound on any sample-count gain'.
N=max(1,ceil(V/epsilon^2)) describes independent unbiased paired sample averages
with known variance in the same admissible coupling class. It is not a bound on
other estimators, exact enumeration/Rao-Blackwellization, practical wall time,
or methods with different per-pair/setup costs. State the assumptions in the
machine-readable definition and final report. Correct any overbroad practical
upper-bound language with a dated clarification to ALTERNATIVES.md.

Likewise, 'atoms' means order failure with non-comonotone same-action atoms. It
does not isolate a causal geometry effect from changing probabilities. Say so
where this classifier is explained, including a historical clarification if needed.

The best-of-six ordinary-root plus sorted-final envelope is a hindsight comparator,
not a deployable method-selection policy or fresh confirmatory evaluation. Distinguish
it from any single fixed hybrid's results. Hypothetical operation counts rebuild
intervention states per pair and exclude some work; state those assumptions if used.

## Finding 3: excluding fixed_label does not establish label robustness

The added LABEL_ROBUST comment says all remaining plans are equivariant to
relabelling. The non-author reviewer found concrete counterexamples:

- Ordered, p=(.2,.3,.5), q=(.4,.4,.2), keys=(0,0,1) in both worlds. Original plan
  [[.2,0,0],[.2,.1,0],[0,.3,.2]]. Swap labels0/1 in both worlds and map back:
  [[.1,.1,0],[0,.3,0],[.3,0,.2]]. Stable key ties break equivariance (maxdiff.3).
- Distance, same p/q, cost [[2,1,2],[1,0,1],[2,1,2]] from horizontal and vertical
  successor triples: selected tied LP plans differ by.4 after the same permutation,
  although each objective is1.3. The optimal value/set is equivariant; the selected
  optimizer need not be, and downstream continuation cost may distinguish the plans.

Rename this subset, associated output fields and report language to the literal
meaning 'excluding fixed_label' (e.g. without_fixed_label), without claiming
permutation robustness. This is a descriptive sensitivity check, not grounds for
retrospectively dropping an original comparator or reopening the B-only gate.
No new permutation sweep is needed. A compact tied-key counterexample test is
appropriate if asserting this distinction in the report. Preserve all six methods
in the main result. These counterexamples do not establish any v1 value is wrong.

## Final report wording to settle

MECHANISM.md now exists. Keep its stop/no-v2 recommendation if warranted, but
correct these overextensions while addressing the earlier findings:

- 'There is no room for2x' and '>=50% a2x claim needs' require equal/comparable
  per-sample cost, negligible setup and the asymptotic paired-average setting.
  They are not unconditional practical impossibility results; integer allocation
  also gives2-to1 at RMSE.02 as your own report records.
- 'No scalar-key rule captures' the family-A gain is broader than established.
  Your evidence addresses the specified projected/current-state rule (and shown
  position/mean orders), not every possible scalar key or policy. Narrow the claim.
- B1 'should be matched by a fixed-permutation CDF root plus a terminal sort'
  conflates cellwise hindsight with one fixed schedule generalizing across cells.
  State precisely which cells/rules are witnessed; no single globally chosen
  permutation/schedule has been shown to match the oracle across the grid.
- 'All81 vertices' should be81 candidate transport bases, retaining feasible
  vertices; the number of feasible/distinct vertices depends on marginals.

These are scope/wording corrections, not a request for new experiments or an
expanded report. The report is already detailed enough; keep the closure focused.

## GPT questions and additional evidence

GPT first-pass reasoning was recorded before your dispatch and was not supplied
to you. It independently selected R0/R1 plus invariant cost cycles. A separate
non-author reviewer used direct65-digit dynamics and finite transport vertices,
without production imports, on four witnesses. Maximum regret disagreement
2.55e-18; maximum child-cost disagreement2.46e-17.

- Both headline B1 witnesses lose entirely at the final step; ordinary-root plus
  sorted-final closes those gaps.
- Best-of-six such hybrids leave maximum B headroom3.3070127034472% at
  83233a6f9375c04c. This is hindsight, not a selection-policy result.
- A2 witness24a16ed9956c3de3 has root regret3.13020874061511e-4. Its cost swap
  decomposes into mean contribution -1.4165297717253e-6 plus centered-distribution
  contribution3.14437403833237e-4. This is algebraic, not causal attribution.

Answer concisely: what remains the weakest assumption in the stop/pivot decision?
Does this evidence justify any new horizon in this domain, and what concrete
counterexample/check would change your answer? Is a simpler fixed terminal-sorting
control sufficient to explain the headline gains, and what does hindsight prevent
us from concluding about the entire grid? Do not add analyses merely to agree.

## Acceptance and commands

All new corruption tests reject before output; untouched v1 all checks pass;
the report's numerical findings stay unchanged; claims have the stated scope;
no new scientific execution. Re-run only the affected tests and diagnostic:

/Users/spiderishi/Coding/attribution/.venv/bin/python -m pytest -q pilot/tests
/Users/spiderishi/Coding/attribution/.venv/bin/python -m pilot.diagnose --input research/pilot/runs/20260924T150726Z --output research/pilot/diagnostics-v1

Return changed files, actual commands/exit status, disposition of each objection,
answers and remaining limits. Do not claim effective effort or review independence
beyond the supplied evidence. GPT will inspect final artifacts and integrate them.
