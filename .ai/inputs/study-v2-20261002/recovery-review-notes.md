# Non-author recovery-design review

2 October 2026. Read-only review returned by GPT worker
`/root/current_proposal_rigor_audit`; summarized by the lead. The reviewer read
the incident, local plan, runner/verifier/ledger and existing retrieval/admin
scripts. It received neither the lead's preferred design notes nor a preferred
verdict. Shared source and objectives mean this is not independent empirical
evidence. No implementation, tests, provider calls or scientific changes occurred.

The reviewer recommends a small administrative unit runner and polling
copy-and-acknowledgement wrapper. The lead accepts these planning constraints:

- Use the existing sealed job, with COMPLETE.json written last, as the unit.
  An unsealed saved state is not completed evidence. Discover each unit promptly;
  require verified backup acknowledgement before the next unit on that worker.
  Preserve the existing Session where practical. Journals must remain outside
  sealed folders, because the verifier rejects additional files.
- Run independently of laptop availability. Confirm persistent source storage
  and a separate off-pod destination recoverable independently of the GPU account.
  Preserve canonical recorded paths by mounting, not by rewriting receipts.
  Validate both destinations' capacity, permissions, funding and retention.
- Copy every pinned dependency, matching prepared data/source/recipe identities,
  and separate attempt records. Acknowledge only after safe restore, byte hashes,
  and verify_run on the unit AND reachable training dependencies. For every
  run-one, require stream.checked=true; complete=true alone does not establish
  stream verification. An incomplete copy, sender receipt or status.json is not
  acknowledgement. Retries are idempotent and do not delete source evidence.
- PathMap verifies relocation but cannot make the runner continue from arbitrary
  new paths. Reconstruct the recorded layout, reverify a sealed predecessor and
  create a new explicit attempt for missing work. Keep lost attempts and costs;
  same-seed retries are not new draws. Retain an administrative catalogue even
  when lost directories are absent; do not silently clear registry claims.
- Current admin.billing is pod billing, not verified prepaid balance. Admission
  needs fresh understood balance/currency, all active/pending account liabilities,
  rates, backup/shutdown delays and retention reserve. Missing or stale inputs
  block admission. Serialize credit reservations across workers. Continuing
  leases need provider-validated timed shutdown or a separate always-on controller;
  merely stopping Python does not stop GPU billing. No payment changes.
- Keep recovery outcome-blind. Transfer/hash opaque payloads without reporting
  hidden metrics, prompts or policy choices to operator/selector logs.

Local acceptance: partial/corrupt transfers, missing dependencies, duplicate
events, crash before/after acknowledgement, disk-full, path-mapping ambiguity,
stale/missing balance, changed rates and concurrent admission. Restore a complete
chain after making its source unavailable, show no subsequent unit launches
without acknowledgement, unchanged sealed receipts and correct new-attempt
bookkeeping. These tests cannot establish GPU equivalence or cloud durability.

Funded validation later starts with one owned worker: actual persistent mount,
off-pod copy while laptop disconnected, fresh-provider restoration, timed
shutdown, real balance semantics and restored CUDA continuation. Only after
those checks may concurrency increase within verified runway. A laptop downloader
alone is an interim prototype and does not satisfy restart prerequisites.

Implementation remains queued after the anonymous exporter and StageB fixes.
No new cloud authorization or change to the frozen scientific plan follows from
this review.
