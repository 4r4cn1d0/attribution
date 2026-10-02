# Stage B third-source targeted cost review

3 October 2026 local date. Non-author GPT reviewer `/root/minimal_date_audit`,
shared context. Read-only inspection of immutable
`tmp/study-v2-20261002/stage-b-third-verify/`; this review is the only file written.
No tests, model calls, agents, cloud actions or scientific outcomes were run or
inspected. The lead is running the CPU checks separately. Scope: changed cost
scopes/session accounting and the two previously unresolved integration paths.

## Material corrections for the next bounded implementation pass

### P2 C1: Other-policy-only setup is charged to the wrong policy

Evidence: `costs.py:277-281,378-383,428-435`. Every block setup enters both
ledgers; the exclusion predicate recognizes only reference/sensitivity IDs, not
all work outside the policy's owned operations. A fresh resumed session running
only S+'s selected edit is therefore charged to S- too. The existing test at
`tests/test_dp_costs.py:123-128` explicitly retains setup after adding another
policy's chosen final to an otherwise reference-only session.

Counterexample: before an S+-only resumed session's setup, both reconstructed
decision costs are 100 seconds. That session adds 20 seconds required only by
S+. Correct costs are (100,120), so T=120-1.1*100=+10. Charging that setup to
both produces (120,120), T=-12, reversing the tolerance reading. Calling the
common addition conservative is incorrect for a ratio/margin comparison. Relative
to correctly owned costs it can also alter the raw difference.

Smallest correction: generalize the existing setup exclusion from
"reference/sensitivity only" to "no operations owned by this policy's scope",
retaining the existing requirement that the fresh session's cache cannot serve
later owned work. Classify excluded amounts separately as reference/sensitivity
or other-policy work; retain every physical second once. Keep genuinely common
loads charged once per hypothetical policy. Enforce the intended one-block-per-
process execution path rather than adding a general cross-block cache graph.
If ownership/reuse cannot be identified, mark the reconstructed scope unresolved
rather than presenting the allocation as neutral. Preserve old ledger columns
as legacy reconstructions if needed, not as independently correct costs.

Decisive test: add one fresh session containing only S+'s final and known setup;
only S+'s scope changes. Mirror the test for S-, and retain the case where a
reference load actually serves a later owned chosen model. Check T explicitly.

### P2 C2: Controller work between attempts is absent even from physical totals

Evidence: `controller.py:380-406` measures startup only. Attempt timers cover
`ensure_op` execution at `289-327`; cached verification at `279-282`, evaluation
at `513-521`, ranking/selection/lock work and final evaluation at `508-509` lie
outside them. `659-662` then labels the sum of attempt receipts as physically
timed, and `analysis.py:514-521` adds startup records but no remainder. There is
no session-end measurement. The author correctly identified this gap.

Counterexample: on resume all acquisition artifacts are present, so verification
and evaluation reading consume substantial time but no new acquisition attempt
occurs. Those seconds appear in neither physical expenditure nor reconstructed
policy costs. Completeness can still be true. Attribution and the cheaper
comparator need not incur the same amount of this work.

Smallest correction: persist a session start/end (including exception paths) and
account for the residual outside externally timed attempts. Use a few explicit
ownership buckets for common controller work, method-specific work and research-
only work; do not add all residual time to both policies, which repeats C1.
Unallocated residual remains visible in the physical total and makes the affected
economic reconstruction incomplete. Final receipt serialization can be explicitly
excluded; no recursive timing framework is needed. Do not decide whether to count
the overhead only after observing its size relative to the 10% margin.

Decisive test: a fake clock advances during cached `verify`, evaluation reading,
and a method-specific controller phase while attempt durations remain unchanged.
Physical totals must increase once, the appropriate policy scope must increase,
and interruption must preserve the measured lower bound. No unmeasured remainder
may yield a complete economic reading.

### P2 C3: Completeness is inconsistent across the reported cost scopes

Evidence: `costs.py:298-340` checks only included attempt durations plus the
startup flag. It does not propagate setup uncertainty from outside operations.
`split_scopes` checks that issue for the primary subtotal at `397-406`, but not
for the preserved whole-research ledger. `analysis.py:505-509,514-521` also emits
complete-case means and physical sums without propagating the corresponding
timing-completeness flags.

Concrete existing fixture: `test_dp_costs.py:179-185` has an S+-attribution
exception with 50 known external seconds and unknown engine setup. S-'s primary
subtotal is correctly marked incomplete, but its `actual` ledger can remain
complete even though some setup reused by S- may be missing. The current primary
gate is protected for this timed-exception case; the whole-research endpoint and
means are not. Separately, an interrupted receipt followed by a successful retry
can produce a complete scientific result with only a physical cost lower bound;
analysis discards `physical_timing_complete` and prints the sum without that flag.

Smallest correction: compute completeness/reasons once for each scope and
propagate them to aggregates. Preserve known incurred numbers as explicitly named
lower bounds; do not present incomplete reconstructed means as complete point
costs. Distinguish unknown setup allocation from unknown physical duration: a
fully externally timed exception can have a complete physical cost but incomplete
policy reconstruction. No additional experiment is needed.

Decisive tests: extend the existing unknown-attribution-setup fixture to check
the whole-research flag and analysis. Add an interrupted-then-successful block:
known seconds survive in the total, its physical completeness is false, and
incomplete cost scopes cannot produce an acceptance reading.

## Earlier integration findings remain unresolved

- **Cached-result lock bypass:** `controller.py:420-422` still returns an existing
  result without the required lock validation. Analysis still reads raw results
  at `__main__.py:158-159,268-270`. Reuse the existing block/lock verifier before
  returning or analyzing a cached final result; valid reuse should execute no
  training, while a deleted/forged lock refuses.
- **Started blocks without result files lose known costs:** the same CLI passes
  only result objects and started IDs; `analysis.py:504-516` totals only present
  results. Read-only receipt collection must retain incurred costs of every
  started block, without closing receipts or inventing future spending. This
  collection can also supply the physical completeness information for C3.

## Changes that fit the accepted amendments

The chosen-model final remains fully charged, including a0; the extra reference
a0 is separated; the scientific two-final reserve is retained. The economic
endpoint is now T=Cplus-r*Cminus and the one-off endpoint is its deterministic
development-cost shift, with raw differences preserved. The two cost scopes are
explicitly model-dependent, necessary cost conditions, not safety/feasibility
assurance or production savings. No new endpoint or N change is recommended.
The prior startup double counting across repeated backend use appears corrected;
its replacement zero-length record is explicitly marked unmeasured rather than
treated as a free standalone setup.

The simpler author suggestion of subtracting only reference operations while
keeping all setup does not resolve C1. A single ownership-based accounting rule
plus visible unknown/lower-bound status is preferable to adding special cases
for every operation kind.

## Verified snapshot hashes

These match `.ai/inputs/study-v2-20261002/stage-b-third-source.json`:

```text
costs.py       d5a3689fddcac32d1f7c2a727f49c80b4bb4360b565ba6013657c0c3acea5106
controller.py  b6053bc0d66999d17855efe9f250562e4fefe0580aaf92afc0bdaf4b25024121
analysis.py    35b46bce40c95dd54813c1a55f702aaf961e3ac6899fbecb9cfa841ed36a7203
__main__.py    f6cb2cd16beaefdd15e1257061ad5e93e846adb890f55321d075c4c3d792a44d
test_dp_costs.py f24d3d53196359e81ae79cac3f521c256abfd1bcb3ebfbe3d672b60023289d49
```

This is a targeted source review, not test execution or independent scientific
evidence. No claim of heldout readiness follows from the models agreeing.
