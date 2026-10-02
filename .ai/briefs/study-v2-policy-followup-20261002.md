# Stage B bounded follow-up after first implementation return

Model claude-opus-5-5, effort max, no time/turn cap. Same owned sibling package
experiments/safety_decision_policy/** and new decision protocol only. Worker
remains worker: no agents/Claude/Codex/shell/execution/downloads/compute/HANDOFF.
You are not alone; preserve others' changes. No Stage A source edits.

Read .ai/inputs/study-v2-20261002/opus-policy-first-report.md, actual code, and
research/experiments/2026-10-02-outcome-definition-amendment.md. Implement this
explicit prospectively recorded endpoint clarification: raw emitted-text flags
and exact unique-argmax utility; primary missing-label intervals for decisions;
keep broader cap/Controversial/tie sensitivities separately; expose empty,
repetition, label/count/overlap/length diagnostics in all analysis, not only engine
files. Do not quietly claim bounds as CIs or human harmfulness. Freeze and validate
an explicit outcome-definition version/hash. Preserve first-draft historical
artifacts and current engine outputs. Do not make a new hidden-tuned quality gate.
The amended scientific meaning must be consistent across development targets,
features, policy choice, synthetic backend, analysis, docs and meaningful tests.

The actual current recipe is study-v2-recipe-calibration-micro2.json: micro2,
accum4, effective8. Original micro4 stress test OOMed on80GB; full train text/data
unchanged. Engine source hash remains5165e61d4e6a68f865b0f037a1106a139ef4c9201175c1817700b2ba311adff0.
All scientific numbers and fidelity/replication decisions remain unfrozen.
GPU development continues independently; no held-out outcome was accessed.

First invocation returned exit0, requested model reported, no denials. GPT ran
the stable CPU suite:103passed in10.68s; full log copied as
.ai/inputs/study-v2-20261002/stage-b-first-tests.log. CLI simulate completed two
synthetic blocks, both chosea0, meanY0; this is engineering evidence only.
The first source is hash-snapshotted and archived before this follow-up.
There are nine numpy RuntimeWarnings (divide/overflow/invalid) at ridge.py134
in otherwise-passing fixtures. Do not blindly suppress them. Ensure every
derived standardizer/Gram/RHS/coefficient is finite and test extreme finite
inputs that overflow intermediate arithmetic. Report whether you can diagnose
the fixture warnings without execution; root will compare host math if needed.
Your StageA/minimal_safety source remains unchanged and must remain so.

Explicitly lead-copied context also includes the current micro2 recipe,
study-v2-data-expanded-arc.json and the new precision-targets document. Expanded
ARC preparation succeeded with hash5f4e118a39e0b8c3e56764db43c2581dc3d53cd63445f6d86b4b856609ee72e2.
Only bank/manifest/provenance changed; engine/selector files byte-identical.
Old trajectories remain calibration-only. These copied context files are not
your owned paths and must not be modified. No numeric frozen config is requested
yet. Address the bounded findings below; no unrequested framework.

Answer with files changed, checks actually run, remaining unsupported guarantees,
and: weakest assumption, simpler valid alternative, a breaking counterexample,
and the specific check that settles each material disagreement. Distinguish
observed evidence from planned checks. GPT will run tests and red-team changed
lines. Nothing is integrated merely because models agree.

## Confirmed non-author findings, first snapshot

1. controller.py around254 initializes status='refused'. Exceptions propagated
   from backend.execute, including a relevance export failing after CPU work,
   retain that status. receipts() around226 excludes them from charged time and
   max_attempts. This can undercharge and retry indefinitely. Only explicit
   pre-execution validation refusals may be exempt; after execute starts,
   unexpected exceptions are timed failed attempts, with error preserved, charged
   and bounded by the same-seed retry count. Add the partial-work/write-failure
   regression; do not silently substitute a new scientific seed.
2. verify_study around609 silently skips an absent lock despite final-* artifacts.
   Require a valid matching config/block/both-choices lock for every final spec or
   artifact, including archived/physically reused hidden reads. Normal run_block
   ordering currently looks correct; preserve it. Tests must remove/forge a lock
   from an otherwise hash-consistent completed study and reject certification.

Reviewer: non-author GPT /root/minimal_date_audit, shared context, read-only;
review of active snapshot, not final clearance. More evidence may follow.
3. Final-operation quotes: root confirms your final returned code now includes
   final_ops in the actual_ledger quote map. Preserve this correction; add or
   point to a final-overrun fixture. The earlier live-snapshot finding is
   superseded, not an unresolved demand to refactor the correct code.

Full first review is .ai/inputs/study-v2-20261002/stage-b-review-first.md.
The reviewer found the core acquisition arithmetic consistent with the brief,
including all12edits and fresh repetitions; do not refactor it gratuitously.

4. analysis.analyze currently selects only status='complete' blocks for endpoint
   and policy-cost averages. Listing failed blocks does not fix conditioning on
   technical success. Preserve a fixed configured set of block draws; never
   substitute fresh seeds until N successes. Report complete-case estimates as
   such, and an all-configured-block analysis with missing outcome contrasts
   bounded by their known ranges. Retain partial observed endpoints where valid,
   incurred policy costs from aborted/final-incomplete blocks, and visibly
   distinguish not-yet-run blocks from exhausted technical retries. Do not impute
   zero future cost or invent finite worst-case cost for an unbounded timer.
   Analyses must not call complete-case averages unconditional fresh deployments.
   Add an arm-dependent failure fixture demonstrating the distinction. This is
   a concrete non-author review finding, not a request for a new estimator.

5. The new precision plan has an explicit six-endpoint family. Keep marginal
   intervals labelled marginal and report a separate Bonferroni-adjusted family
   view (Y,Lminus,Lplus,Ominus,Oplus,actual-cost difference), stating that the t
   version is approximate and unbounded costs have no Hoeffding guarantee. An
   explicit config analysis setting/version should pin this. The original
   stronger D_info/H2 remains unestablished.

Author decisions: normalized violation as sum is accepted; adverse missing-label
targets accepted under the new amendment. Utility ties follow the amendment,
not the old unresolved-primary convention. Selecting the proxy via normalized
CV targets remains an explicit heuristic; do not imply equally many features
or novel attribution/allocator methods. One block per process is accepted and
must remain documented so actual setup charges are meaningful. Registry refusal
after a killed engine process is fail-closed; do not silently clear registry or
create a fresh scientific draw. Preserve it as a technical failure with bounded
same-seed retry/exhaustion, costs and missing-block analysis unless you can make
a safe fix wholly in the owned package with a concrete regression test.
