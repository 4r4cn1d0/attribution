I've implemented the amendment and all five findings in the owned package, but **nothing has been run**. This session only had read, search, edit and write tools, so no command, test or CLI call was executed and there are no exit statuses or evidence files. Every check below is planned, not observed. Stage A sources, `minimal_safety`, the copied context files and the first-draft artifacts are untouched.

## Files changed (all owned)

- **Package code:**
  - `outcomes.py` was rewritten. Everything now derives from validated per-item counts:
    - raw flags;
    - missing-label intervals;
    - exact unique-argmax utility, with the tie-aware and tie-resolution views kept separate;
    - the first-draft "broader" sensitivity, where an item with several unresolved reasons is counted once;
    - every diagnostic: labels, refusals, capped, empty and repetitive responses with their overlaps, output lengths, ties.

    `OUTCOME_DEFINITION` is pinned by version and SHA-256 through the table, record, config, lock, results and analysis.
  - `controller.py` and `analysis.py` were rewritten.
  - `common.py`, `features.py`, `ridge.py`, `policy.py`, `config.py`, `development.py`, `backend.py`, `synthetic.py`, `__main__.py` and `README.md` were edited.
- **Configs:** `example-engineering.json` and `example-dev-fit-spec.json`.
- **Tests:** `test_dp_outcomes`, `test_dp_controller` and `test_dp_analysis` were rewritten. `test_dp_ridge`, `test_dp_policy`, `test_dp_features`, `test_dp_config` and `test_dp_engine` were edited.
- **Protocol:** `research/experiments/safety-selection-v2-decision-protocol.md` was rewritten.

## Findings: what changed and the test that should show it

1. **Exceptions in `execute`.** Only a `RequestRefused` raised before anything is written to the attempt folder is recorded as refused (not charged or counted). Those come from the lock check, a read-only backend, or `make_job`'s job validation. Any other exception is a timed, charged, counted failed attempt with its error kept, retried on the same seed up to the limit.
   - Tests: the relevance-write-failure regression (charged, and still capped at two attempts after a resume), explicit versus late refusal, and an engine-fixture test where a registry refusal after a killed process becomes a bounded failure and the registry is left unchanged.
2. **Locks.** `check_lock` now checks lock content (same block, configuration, final seed, and an authorized arm). The controller runs it before any final access, including reuse of an already completed final. `verify_study` requires a valid lock for every final operation and for complete or final-incomplete results. It also checks that the lock covers exactly the block's other operations and that every receipt pins its spec's hash.
   - Tests: a removed lock, plus four forged locks with every downstream hash rewritten consistently. Each must fail verification with only lock problems.
3. **Final overruns.** The existing fix is kept; a final-overrun test was added.
4. **Missing blocks.** The analysis reports every configured block as complete, final-incomplete, aborted, started without a result, or not run.
   - All-configured view: unobserved outcomes take their known range [−1, 1]. The cost mean is reported as unbounded while any block lacks complete cost accounting.
   - Complete-case view: labelled as conditional on technical success.
   - Aborted blocks keep each policy's cost incurred up to the abort, marked as a lower bound.
   - Tests: an arm-dependent failure fixture (S+'s chosen arm fails its final deployment), plus a controller test where a0's final fails.
5. **Family view.** Marginal intervals are labelled marginal. A separate Bonferroni view covers the six endpoints at 1 − α/6 each. The config pins `plan_version`, `family` and `multiplicity`.

## The ridge warnings: diagnosis without execution

I can only partly diagnose them. The code makes genuine overflow very unlikely:
- the warnings appear only at the matrix-product line, not at the standardization lines above it, which would have warned first on any real overflow;
- the standardized operands are bounded by construction;
- a matrix product does no division, so a "divide by zero" flag can't come from the arithmetic itself.

That pattern fits floating-point flags raised spuriously inside the host's BLAS (on macOS, numpy 2.x usually links Apple Accelerate). I can't confirm this.

What I changed in `fit()`:
- The Gram matrix and right-hand side are now built without BLAS.
- Overflow, invalid and divide errors are raised as errors instead of warnings.
- Every intermediate, coefficient, prediction, score and variance must be finite; otherwise the fit refuses.

A real overflow would now fail those three tests rather than warn.

**Check for root:** run `test_blas_free_normal_equations_match_the_blas_closed_form_at_fixture_sizes` with `-W always::RuntimeWarning`. Its reference calculation still uses BLAS at the fixture shapes. If matmul warnings appear there and the test passes, the flags were spurious. Also run `numpy.show_config()` to confirm which BLAS is linked.

## Changes you should check before integrating

- The example config's `outcome_definition.sha256` is a zero placeholder, because I can't compute SHA-256 by hand. `validate_config` checks the version string and hex format; `check_config` checks the hash against the code. The frozen config needs the value printed by `pins`.
- A block whose only failed final deployment is the one-extra-purchase sensitivity arm is now `complete`, not `final-incomplete`.
- Specs now include `block` and `config_sha256`, so study trees produced by the first draft won't resume or verify under this code.
- Synthetic outcomes are now drawn item by item, so the earlier engineering result (both blocks chose a0) won't reproduce.

## What remains unsupported

- No result above has been observed.
- `verify_study` has no anchor outside the study tree, and it doesn't recompute choices from the lock's observations.
- A backend that did work in memory and then raised `RequestRefused` without writing anything would go uncharged. Neither current backend does this.
- Bonferroni simultaneous coverage holds only for the Hoeffding intervals of the five bounded endpoints; the t intervals are approximate and cost has no guarantee.
- The degeneration flag (raw safety improvement alongside any increase in empty, repetitive or capped responses) has no threshold and will be noisy. It is descriptive only.

## The four answers you asked for

- **Weakest assumption:** that technical failures stay rare. Each missing block widens the all-configured Y bound by 2/N. With 20 blocks, a single failure already exceeds the 0.05 half-width target. Check: include failure rates in the planned simulation for block count and retry limit.
- **Simpler valid alternative:** keep the BLAS product and only check finiteness afterwards. That's smaller and keeps the warnings visible, but it can't catch a finite but wrong product. The comparison test above settles which is right.
- **Breaking counterexample:** a forged lock that changes the recorded observations or transcripts but keeps the same choices, with all hashes rewritten, still passes `verify_study`. Check: anchor lock hashes outside the study tree before the final runs, and recompute choices from the frozen config during verification.
- **Disagreement to settle:** a deterministic engine access refusal inside `run_one` now uses up a block's attempts instead of stopping the controller. `check_config` is meant to prevent such refusals. If you'd rather stop, a pre-execution engine access check in the backend would turn it into a refusal; that's your call.
