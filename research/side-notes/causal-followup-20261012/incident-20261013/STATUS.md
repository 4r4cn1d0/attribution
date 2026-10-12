# Follow-up incident —13 October 2026 (IST)

The funded seed1122 follow-up is incomplete. It supplies no new complete causal
comparison and no validated refusal-direction intervention.

- 1B: batch startup check failed. No completed unit was verified locally.
  The actual remote worker start state and launch diagnostic were not recovered.
- 7B: the remote batch receipt records C complete_verified; H was not started
  because less than its frozen 6,300-second admission plus 300-second reserve remained.
  C took about 107 minutes, after roughly 55 minutes of setup/preflight.
- The collector exited immediately with “no SSH address yet”; both operators
  waited 30 minutes for a backup receipt and then confirmed stops.
- Both pods still exist as stopped pods with 30/40 GB mounted volumes. The
  provider currently exposes no SSH mapping. Data retention is not verification.
- Latest account read: $11.80, zero running GPUs, storage spend about $0.493/hour.

The completed seed1121 six-unit pilot and its verified backups are unaffected.
Its checkpoint-conditional recipe intervention effects do not establish the
refusal-direction mechanism or generalize across seeds/model sizes.

This check restarted no pod, ran no new training, changed no frozen scientific
file and deleted no volume. Original manager/analysis failures are preserved.
Source snapshots and hashes are in status.json. Administrative recovery must
preserve these failures, recover remote logs and seal-check C before using it.
