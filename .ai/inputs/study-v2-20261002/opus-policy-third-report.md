I implemented the cost-scope amendment in the owned package and protocol, but **nothing has been run**: this session had only read, search, edit and write tools. There are no exit statuses, no evidence files, and every acceptance check is untested. Stage A, `minimal_safety`, `backend.py`, `synthetic.py`, the copied `.ai/inputs` evidence, the amendment file and HANDOFF are untouched.

## What changed

- **`costs.py`**
  - The per-policy whole-research ledger (`costs.actual`) is kept as is.
  - New `policy_costs` splits it into `selection_plus_chosen_model` and `reference_and_sensitivity`, which add up to the total.
  - The chosen model's final is charged in full to each policy that chose it, including when both keep a0 and one physical run serves both.
  - The extra `final_reference_a0` (every attempt, failures included) is left out of the subtotal.
  - `quoted_ledger` now splits the chosen-model and reference quotes. The two-run reserve is never released by a choice.
- **Reference-only setup.** The engine caches each asset once per process; I checked this in `runner.Session`. So setup is excluded only for a session (one `run_block` call, now tagged on every attempt) that meets all of these:
  - it ran nothing but that policy's reference or sensitivity work;
  - it started a fresh process;
  - no later session of the block shared that process.

  Loads recorded inside a reference call stay in the subtotal whenever the same process did other work. Untagged receipts exclude nothing.
- **Unknown timings stay lower bounds and are flagged, never zero.**
  - Receipts with no backend result now record their setup as `null` instead of `{}`.
  - A timed attempt outside a policy's subtotal with unknown setup makes that subtotal incomplete.
  - A block whose setup was not measured gives lower-bound costs.
- **`config.py` and the example config.** Analysis plan v3 adds an explicit `analysis.cost_endpoint` with `scope` (which must be `selection_plus_chosen_model`) and `tolerance_ratio` (1.1 in the example; must be at least 1). The family's sixth endpoint is now `cost_margin`, defined with its actual ratio.
- **`analysis.py`.** Per block it reports:
  - the raw subtotal difference;
  - the margin `T = C(S+) − r·C(S-)`;
  - the one-off margin `T + D(S+) − r·D(S-)`;
  - the preserved `actual_cost_difference`.

  Uncertainty is computed on the margins themselves. A new `cost_tolerance` reading needs both margins' family-level intervals below 0; an interval containing 0 is "inconclusive". Labels exclude exact deployment-only timing, equal realized dollars, unstated amortization and production savings.
- **`ridge.py` and the protocol.** The BLAS claim is narrowed: the solve still uses NumPy's linked LAPACK/BLAS, bitwise independence across builds is not claimed, and the warnings' root cause is not established. The finite guards are unchanged.
- **`__main__.py`.** `simulate` now runs one fake process per block, and the headline shows the cost reading.
- **Tests.**
  - New `test_dp_costs.py` (10 tests) covers:
    - the regression fixture: totals differ by 450 s, subtotals agree;
    - both keeping a0;
    - a reference-only failure;
    - setup order (both directions);
    - sensitivity-only sessions;
    - untagged receipts;
    - unknown timings;
    - the reserve.
  - `test_dp_analysis` has 3 new tests, `test_dp_controller` has 4, and `test_dp_config` has 7 new refusal cases. If everything passes and nothing else changed, the suite should read 130 + 24 = 154. That is arithmetic, not a result.
- **Docs.** `README.md` and the decision protocol describe the scopes, margins, readings and new open decisions 7–8.

## Behaviour changes beyond the amendment — please check

1. **Setup double count (a real defect).** Before this change, a later `run_block` call on an already used backend was charged the whole previous block's work as "setup". In the baseline fixture, block 1's setup line equalled all of block 0's time. A common inflation X shifts the new margin by −0.1·X in S+'s favour. Such sessions now record zero length and the block's costs are flagged as lower bounds. The CLI path (one block per process) is unchanged.
2. **Interrupted attempts.** `physical_block_seconds` now counts interrupted attempts at their lower bound instead of 0, and session seconds are added to the physical total.
3. **Old artifacts.** Plan-v2 configs are refused, and study trees without session tags never exclude setup.

## Your four questions

- **Weakest assumption.** That the engine's asset cache lives exactly as long as one backend object in one process. The session tags and the "shared" flag model only that. If the engine reloaded assets per job, the rule would over-charge, which is safe. If a cache outlived its backend object, setup that later work reused could be excluded.
- **Simpler alternative.** Skip session identification and define the subtotal as the total minus the `final_reference_a0` category, keeping the whole setup line. It needs no receipt fields and gives identical numbers for every uninterrupted block. Its only error is over-charging the edit chooser after a resume that ran only the reference. I'd accept it if you prefer less machinery. The double-count fix is needed either way.
- **Breaking counterexample.** Controller work between attempts sits in no receipt, so every scope treats it as zero, including the research total. Examples are re-verifying completed artifacts, evaluation reads, and writing the lock and result. In a resumed process that runs only the reference, all completed artifacts are re-verified before the reference trains.
- **Check that settles it.** In the real development replay, compare each session's wall span (session start to its last receipt end) with its session seconds plus attempt seconds. If the remainder is not small against 0.1·C(S-), add an end-of-session record and charge it.

## Open questions for you

- **Family endpoint.** Plan v3 replaces the raw cost difference with the margin T in the family. Please confirm this, the tolerance ratio, and whether the 0.10 precision target set for the raw difference also applies to T.
- **Other-policy sessions.** A session that ran only the other policy's work stays in both policies' subtotals. That is neutral for the raw difference but biases T by −(r−1)·X.
- **Whole-research total completeness.** The totals still lack the new unknown-setup flag, so an exception in another policy's operation can understate a total without being flagged.
- **Forced-world premise.** The forced-world controller tests assume both policies choose an edit. They assert this up front, so a wrong premise fails loudly rather than passing vacuously.

## Suggested checks

1. `python -m pytest -q -rs experiments/safety_decision_policy/tests` — the BLAS warnings in the ridge reference tests should still appear.
2. `python -m experiments.safety_decision_policy simulate --config experiments/safety_decision_policy/configs/example-engineering.json --spec experiments/safety_decision_policy/configs/example-dev-fit-spec.json --out <NEW>` — inspect `cost_tolerance` in the output.
