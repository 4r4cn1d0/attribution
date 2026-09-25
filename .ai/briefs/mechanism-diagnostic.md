# Explain the completed pilot and justify one next experiment, if warranted

Task ID: mechanism-diagnostic-v1. User approved the next direction: diagnose why
ordinary couplings nearly match the oracle, identify a testable mechanism, then
consider a justified new pilot version. This assignment performs the diagnostic
and proposes a v2 design; do not run H3/H4 or a new experimental sweep here.

Role: Opus alternatives + substantive analysis implementation in the prepared
mechanism-diagnostic/workspace only. Model claude-opus-5-5, effort max. No time or
turn caps, per user instruction. You are a worker, not the lead. No agents,
Claude/Codex calls, Git, publishing, installations, fitting or GPU work. Others
are working: preserve their changes and do not edit shared handoff records.

Context supplied (same baseline evidence seen by GPT; GPT's preferred approach
is not supplied):
- research/pilot/IMPLEMENTATION_RESULTS.md
- research/pilot/headroom-manifest-v1.json (SHA256
  62f7bcc4d85d291bca20234b68fe3c3d287bdc2401afeaa4c1022f7dc1c57999)
- research/pilot/runs/20260924T150726Z/: 1440 completed H1/H2 cell JSON records,
  summary.json, cells.csv, groups.csv, metadata.json and independent witness checks.
- pilot/process.py, couplings.py, pair.py, exact.py, headroom.py and tests.
- research/scoping/THEORY.md, PILOT_SPEC.md (old scope and gate remain unchanged).
All source versions are recorded in the prepared workspace manifest and the old
run metadata. Do not overwrite old results or reclassify the failed gate.

Observed facts: B1 maximum18.478% (partial suppression), primary B1 maximum14.115%,
B2 ties to numerical precision; scalar A2 maximum25.445%. Median gains near zero.
All1440 cells passed;720H4 cells were not run because no eligible B cell reached20%.
Strongest witness IDs: 27f1126e6c329784, d7fbdd78951f35b0, 24a16ed9956c3de3.
Cheap maximal and distance transport tie on the first witness. Do not treat an
arbitrarily different tied plan as evidence of a useful mechanism.

Before code, write research/pilot/diagnostics-v1/ALTERNATIVES.md: a compact record
of independently considered approaches, their tradeoffs and your selected
minimum analysis. No need to build a framework. A small script reading stored
root costs plus existing public APIs should be sufficient. Use recomputation
only where needed for a real independent check, not a new search for winners.

Owned files only:
- pilot/diagnose.py (minimal reproducible diagnostic CLI)
- pilot/tests/test_diagnose.py (meaningful identity/counterexample tests)
- research/pilot/diagnostics-v1/* (new data, interpretation, optional v2 proposal)
Do not modify prior modules, prior tests, old manifests/results or .ai/HANDOFF.md.
If a core defect blocks analysis, report concrete evidence rather than silently
changing the baseline. Do not inspect excluded dependency trees with file tools.

Deliverable and observable acceptance:
1. Quantify what explains the observed gains and ties. Locate which decisions
   lose variance and distinguish changes in action probabilities, successor
   geometry, and terminal ordering as far as the evidence permits. Comparisons
   need matched zero/small-gain controls, including beta0, not only the winners.
   Use the whole completed H2 grid for simple summaries if inexpensive; present
   focused examples. State exactly how examples/controls were selected after
   seeing v1, so diagnostic evidence is not fresh confirmation.
2. Preserve the conditional estimand, full optimizer state, correct marginal laws,
   suppressed-minus-ordinary sign, and numerical/no-renormalization conventions.
   Any decomposition must be quantitatively checked against stored total regret
   and independently computed terms on representative cases. Report actual max
   discrepancies and reject invalid inputs/results. A tautological rearrangement
   of the same stored scalar is not independent validation.
3. Explain relevant plan/cost differences numerically, allowing LP ties and
   additive row/column cost invariances. Separate a derivation from measurement
   and an explanatory hypothesis. Noncausal terminal OT is not an implementable
   coupling; saved construction time is not per-sample timing or a speed claim.
4. Propose at most one small v2 study ONLY if the mechanism gives a concrete
   directional prediction. Specify exact cells/panel selection, primary endpoint,
   controls, correctness and falsification criteria, no fitting/test leakage,
   recording of all cases, CPU/RSS/cell caps and what would justify a practical
   method. Do not lower the old gate retroactively or expand just because18.48%
   is close to20%. If evidence does not justify follow-up, explicitly recommend
   stopping/pivoting this mechanism in this domain. A proposal is not execution.
5. Write MECHANISM.md with evidence links, limitations and the next decision;
   concise report. Record diagnostic wall/CPU and inputs/hashes in its outputs.
   No novelty claim or new literature assertions are needed in this assignment.

Commands explicitly permitted (use exact forms, no compound shell snippets):
/Users/spiderishi/Coding/attribution/.venv/bin/python -m pytest -q pilot/tests
/Users/spiderishi/Coding/attribution/.venv/bin/python -m pilot.diagnose --input research/pilot/runs/20260924T150726Z --output research/pilot/diagnostics-v1

The diagnostic command may read all existing H1/H2 records and recompute H<=2
values for validation; it must not run new horizons/fitting. It should finish as
a small CPU analysis and record its work. Experimental planning remains separate
from the uncapped Claude run. At most one Opus implementer and one GPT reviewer
will be active.

Questions to answer in the return:
- What is the weakest assumption in your explanation? What concrete case would
  falsify it, and what observed result would change your recommendation?
- What simpler alternative did you reject, and why?
- Which findings are identities, measurements, hypotheses or untested proposals?
- What exactly remains unsupported? In particular, do current gains plausibly
  leave room for a 2x practical improvement after overhead?

Return changed files, commands actually run and exit status, measured results,
criterion status, answers and unresolved concerns. Do not claim effective effort
or an independent review you did not observe.
