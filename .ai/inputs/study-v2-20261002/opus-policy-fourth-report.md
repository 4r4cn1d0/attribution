I've implemented R1, R2, the three third-review cost issues (C1–C3) and the interpretation labels. **Nothing has been run**: this session had only read, search and edit tools, so there are no exit statuses, no evidence files, and every acceptance check is untested. If the 154 existing tests still pass, the suite should count 165 (11 new cases); that is arithmetic, not a result.

## Starting point
- The third candidate did not touch R1 or R2. Both were still present, as the third review says.
- All prior fixes are kept: the setup double-count fix, lock checks in `ensure_op` and `verify_study`, bounded retries, interrupted-attempt lower bounds, scopes and margins.
- Model, primary outcome, training, allocator, estimators, the six-way split and N are unchanged.

## What changed
- **R1: re-entering a completed block.**
  - `run_block` returns an existing result only after `verified_result` (`controller.py`). It reuses the `verify_study` lock rules and adds checks on specs and receipts, configuration, outcome definition and final seed.
  - This covers complete and final-incomplete results. A removed or forged lock refuses; nothing reruns or is rewritten.
  - The `analyze` command now goes through `study_evidence`. It refuses (exit 2) if the tree fails the same checks.
- **R2: started blocks without a result.**
  - `started_block_costs` rebuilds what each block already paid from its receipts, sessions, plans and lock. It is read-only: it closes no receipt and writes nothing.
  - Before the plans exist, the screen counts for both policies and every other operation is S+'s. That is the only work the controller runs at that stage.
  - The analysis puts these costs once in the physical total and per policy as labelled lower bounds, in both scopes. The block stays outcome-unknown, is never labelled complete, and produces no margin.
  - If only block numbers are supplied, the cost shows as unknown, never zero.
- **C1: other-policy sessions.** The setup exclusion now applies to any fresh session that ran none of a policy's own work, as long as no later session shared its process.
  - Such a session counts as that policy's research if its reference or sensitivity work ran there.
  - Otherwise it is `other_policy` overhead and is in neither of that policy's scopes. Every second is still counted once physically.
  - Sessions that ran both policies' work stay shared. I checked `runner.Session`: the only engine setup stages are common assets (policy, guard, toxicity, corpus tokenization, memory preflight).
- **C2: controller time outside attempts.**
  - A new end record (`session-<n>-end.json`, versioned "session end v1") is written on return and on exception. It holds the session's controller seconds by owner: `common`, `S-`, `S+`, `final:<arm>`, `sensitivity`, plus `reuse` and `result`, which go to no policy.
  - The timeline is cut at every attempt timer and every change of step, so attempts and segments add up to the whole session.
  - Evaluation reads are now cached per owner, so neither policy gets the other's reads for free.
  - A killed process leaves no end record. That session's controller time is unknown, and every scope it served is flagged.
- **C3: completeness.** Every scope, and the physical seconds, now carries a complete flag and its reasons. This includes the whole-research ledger.
  - The analysis never reports a difference of two lower bounds.
  - Means and the physical total are null while any part is incomplete, with a named lower-bound value beside them.
  - A fully timed exception keeps the physical seconds complete; only the per-policy reconstruction is flagged.
- **Interpretation amendment.**
  - Labels now call t-based readings "working-assumption exploratory".
  - A new `confidence_level_claims` block reads only the existing family Hoeffding bounds (all blocks, missing-label view) against Y > 0, Y > 0.02 and the frozen tolerances.
  - The overall cost reading now says "(exploratory)".
- **Versioning.**
  - Block costs now carry `COST_CONTRACT` v2, and the analysis refuses results without it.
  - The analysis plan is bumped to v4; the example config is updated and v3 is refused.
  - The simulate/analyze headline key `cost_tolerance` is renamed `cost_tolerance_exploratory`, so the synthetic log will look different.

**Changed files:** `costs.py`, `controller.py`, `analysis.py`, `__main__.py`, `config.py`, `configs/example-engineering.json`, `README.md`, `tests/test_dp_costs.py`, `tests/test_dp_analysis.py`, `tests/test_dp_controller.py`, `tests/test_dp_config.py` (all under `experiments/safety_decision_policy/`), and `research/experiments/safety-selection-v2-decision-protocol.md`.

**New regressions:**
- Through `Study.run_block` and `main(["analyze", …])`:
  - R1 re-entry: removed and forged locks, and a final-incomplete block.
  - R2: your reproduction (result removed, physical total must equal the full tree's), plus a block killed mid-acquisition. The analysis must leave the tree byte-identical.
  - C1 on the abort path: an S+-only resumed session.
  - C2: fake time in score reads, cached verification and evaluation reads. It checks counting once, ownership, the interrupted session keeping its measured seconds, and that attempts plus segments add up to the session.
- Hand-made receipts for C1 in both directions: T = +10 instead of −12, and −32 instead of −12.

## Your four questions
- **Weakest assumption:** that the step which triggered controller work matches the controller cost a standalone policy would have paid. The open point is `reuse`, a second verification of an artifact already produced in the same session.
  - It goes to no policy. So when S-'s acquisition reuses S+'s prerequisite continuation, C- misses one verification.
  - That biases T against S+, by r times one `verify_run`.
- **Simpler alternative:**
  - Charging all controller time to `common` is simpler, but it repeats C1's −(r−1)·X bias.
  - Leaving that time unassigned would make every block incomplete, which removes the endpoint.
  - A different simplification I'd recommend adding: require a `verify-study` pass (with artifact re-verification) before any reported analysis. My checks don't re-verify artifacts.
- **Breaking counterexamples:**
  - A process killed during a long resume: its controller seconds become unknown, and I derive no lower bound from its receipts' timestamps.
  - Several blocks in one process: the small gap between one block's end record and the next block's start is in no record. The CLI runs one block per process, so this doesn't arise there.
- **Check that settles it:** in the CPU engine replay, compare each end record's `reuse` and `result` seconds with 0.1·C(S-). If they are not small, decide before held-out data how `reuse` is charged.

## Still open (also listed in protocol open decisions 8–12)
- The 2 pp margin is a code constant taken from the amendment, not a config value.
- Research-only sessions are charged their whole overhead to that policy's research; this does not affect T.
- The lead needs to confirm plan v4.

**Suggested checks:**
1. `python -m pytest -q -rs experiments/safety_decision_policy/tests` (expect 165 if all pass).
2. The synthetic `simulate` command.
3. Rerun your second-review reproduction fixture against this candidate.
