# Stage B second-source targeted review

2 October 2026. Non-author GPT reviewer `/root/minimal_date_audit`, shared context.
Read-only review of the stable `tmp/study-v2-20261002/stage-b-second-verify/`
snapshot. No source edits, agents, model calls, tests, training or cloud operations
were performed. This review file is the only file written. Root reports 130 CPU
tests passing in 12.50 seconds and a successful synthetic CLI exercise; the
reviewer did not independently execute those checks. The separate pending
cost-scope amendment is deliberately excluded from findings below.

## Remaining material findings

### P2 R1: Completed-result reuse still bypasses the choice-lock check

Evidence: `experiments/safety_decision_policy/controller.py:395-397` returns an
existing `result.json` immediately. It never reaches `ensure_op`'s corrected
`check_lock` call at lines 262-263. The ordinary `run-block` CLI exposes that
result's Y at `__main__.py:257-261`. The analysis CLI similarly reads result files
at lines 262-267 without requiring their locks; `analysis.analyze` checks the
configuration/outcome identity but receives no lock evidence.

Concrete counterexample: complete the existing synthetic fixture, delete its
block's `lock.json`, then reopen `Study` with the same valid configuration and
call `run_block(0)`. The cached hidden outcome is returned. `verify_study` correctly
rejects the same tree, and `ensure_op` correctly rejects reuse of its final
operation; the completed-result path circumvents both corrected protections.
This is an incomplete fix to the requested new/reused hidden-access contract,
not a claim of new premature access during the ordinary fresh-run ordering.

Smallest correction: validate the completed block's required lock, configuration,
choices, final-seed/arm authorization and result-to-lock pin before returning or
analyzing its cached final result. Reuse the existing lock/block validation logic;
do not rerun training or create a new seed. Alternatively the analysis entrypoint
must require a current verified-tree result rather than silently treating raw
cached JSON as verified. Regression: valid completed reuse returns unchanged with
no execution; deleted/forged lock causes both completed reuse and validated
analysis to refuse.

### P2 R2: Known costs of interrupted blocks without result.json disappear

Evidence: `__main__.py:158-165` supplies only finished result objects and IDs of
started blocks. `analysis.py:400-408` builds cost records and the physical total
only from result-bearing blocks. It has no channel for an unfinished block's
existing timed operation receipts. The new all-configured outcome and unknown
cost-mean treatment is correct, but does not preserve these already measured
costs in the report.

Concrete counterexample: an interrupted block has several complete screen
receipts totaling an hour but no `result.json`. The analysis lists it as
`started-without-result`, yet omits that hour from `costs.per_block` and
`physical_controller_seconds`. With no result-bearing blocks the latter reports
only static costs, even though the controller's saved receipts prove additional
spending. The issue also affects a static failure that exits before a block result
is written, although static receipt time itself is separately collected.

Smallest correction: collect read-only receipt-derived incurred costs/lower
bounds for every started block, including ones without a result, and show them
in the physical total and per-block accounting with an explicit incomplete flag.
Where policy ownership is recoverable, retain those policy lower bounds too.
Do not invent remaining/future cost, substitute a new draw, close receipts as a
side effect of analysis, or make the all-block cost mean finite. Regression: an
unfinished block containing a known timed receipt remains outcome-unknown but
its recorded spending appears exactly once in the incurred total.

## Corrections that appear consistent in this snapshot

- Outcomes now distinguish raw emitted-text flags, invalid-label primary bounds,
  exact unique-argmax utility, tie-aware utility and the broader cap/Controversial
  sensitivity. Broader unresolved reasons are unioned correctly. Counts,
  overlaps, lengths, emptiness and repetition are retained in final analysis.
  Feature construction and the choice rule use the amended primary endpoints.
- Unexpected execution exceptions are timed/countable failures. Explicit refusal
  after a file has been written is treated as failure. Retries stay on the same
  operation/seed and are bounded. Current engine validation refusals are distinct
  from post-start engine failures; no new unbounded retry path was identified.
- Fresh final execution and reuse through `ensure_op` check the lock's content,
  block/configuration/final seed and authorized arm. Archived verification rejects
  missing locks and the reviewed forged-lock cases. R1 is the remaining cache path.
- Final-operation quotes are included when recording overruns.
- All configured draws enter bounded outcome summaries, with observable partial
  endpoints retained. Aborted result-bearing blocks preserve incurred costs;
  complete-case output is explicitly conditional. R2 concerns missing result files.
- The six-endpoint Bonferroni view is separate from marginal output and states
  the approximation and unbounded-walltime limits. The future cost-scope/T-margin
  amendment is outside this snapshot's accepted contract and outside this review.
- Ridge fitting checks finite intermediate values, coefficients, predictions,
  losses and target variance. Elementwise normal-equation construction avoids
  the reported BLAS warning path. No remaining material numerical defect was
  found by inspection; root's actual numerical checks remain the execution evidence.

The review does not certify deliberate coherent rewriting of the entire study
tree, independence of model reviewers, heldout experimental performance or final
scientific readiness. No such guarantees were requested or established.

## Reviewed snapshot hashes

SHA256, relative to the stable snapshot's `experiments/safety_decision_policy/`:

```text
outcomes.py   54966039290eeae837626ea5f32cbc65c12242590ea9444736bdaef525cdf300
controller.py fa1a5bf352b8c0a25d9e2939d730389571158a50651ed8d6601df52aeea9f732
backend.py    a51523f18c4f74ae3d808736c2a7cebf1714711e9e220b41e3aba1e6997020eb
costs.py      4c3320b6fe6664e16065eba348a82443d2217ce612b1ab197a3f6f81bc1749ea
analysis.py   1f0c866988aa4ebe6760542489642c16258154428742326fadde9d6d231fea16
ridge.py      8208a8163b594810af55eb9eea3dabe7f5327740128b5ebc741c77632a5b7982
config.py     47cdad419f92b8a831d51156f8ff4b89cae12da74ed7b572ec7d5e2796a5e238
features.py   d4c1abf93a4da61bd44a5f295f29159e39d209d5ad4828d302b11862c5bed8e0
policy.py     c8f0e57fe15dd9b3cc39df63b2a9f6f8bd6cc44a5f22587c72749fe0e85378e7
__main__.py   273da44d29294dc810755445123e47c8b1a5bd1cd9935f9acc3d8b6c82d07e25
```

Targeted changed-line and contract review; not a new broad review of unchanged
engine, acquisition design, literature, or data construction.
