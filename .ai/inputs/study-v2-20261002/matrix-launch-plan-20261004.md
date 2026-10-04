# Development-matrix launch plan, 4 October 2026 (shared by General Implementation and Specialized Implementation)

Written by General Implementation at the user's request that both sessions work from one plan.

## The user's instructions today

- "use a100 and go ahead start the experiment" — after the cap-only self-stop check passed (`pod-timer-cap-check-20261004/`).
- Earlier: get the experiments started as soon as possible, with safeguards.

## What General Implementation runs now (the "2 October path", with two additions)

1. **What runs.** The frozen development matrix:
   - `research/experiments/2026-10-02-stage-a-freeze.md`;
   - the plan `tmp/study-v2-20261002/dev-matrix-assets/dev-matrix-plan.json`: 13 hosts × 2 jobs, seeds 1101 and 1102.

   Each job is the engine's `calibrate --prepared prepared-v2 --recipe configs/study-v2-primary-20261002.json --arms ARM --seeds SEED`, with the engine, recipe and prepared-data hashes checked first.
2. **Hardware.** `NVIDIA A100-SXM4-80GB`, Secure Cloud, $1.59/h. This is the same GPU and image as 2 October (`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`).
3. **Setup.** The 2 October bundle `worker-setup-v3.tar.gz`, sent over SSH:
   - environment and pinned public models;
   - bundle hash checks;
   - the assert that the GPU is `NVIDIA A100-SXM4-80GB`;
   - the same two-step A100 fixture, producing `BOOTSTRAP-VERIFIED.json`.

   No job starts without it.
4. **New explicit attempts.** The output root is `dev-matrix-002` and the receipts are `dev-matrix-process-SEED-002`. The lost `dev-matrix-001` attempts keep their names and costs.
   - The runner `tmp/study-v2-20261004/run_dev_matrix_v2.py` keeps the 2 October runner's checks and arguments.
   - It drops the old-host branch: hosts `lead` and `dev01`–`dev04` would wait forever for a 2 October cap-sensitivity receipt.
5. **Addition 1: the stop timer as a hard cap.** Every pod starts with the in-pod stop timer: `pod-timer-settings`, a 6-hour cap, and no leases.
   - Expected per host: about 4 hours (2 October `calibrate` jobs took 50–66 minutes each, plus 2048-token evaluations).
   - Worst case: 13 × 6 h × $1.59 ≈ $124, within the balance of $149.76.
   - No credit-depletion loss is possible.
6. **Addition 2: off-pod copies as units seal.** This Mac pulls each host's `dev-matrix-002` and receipts every few minutes into `tmp/study-v2-20261004/retrieved/HOST/`, and stops a host's pod once both jobs and the final pull are complete. The stop timer is the backstop.
   - **Known gap:** if this Mac is off, copies pause. The pods still stop at their caps, and their volumes keep the outputs, so the work is stopped, not deleted.
   - There are no GitHub-vault acknowledgements yet: the backup token does not exist.
7. **Order.** Host `dev05` first (a0 seed 1101, then g-5312a1359c6c8e28 seed 1102). When its bootstrap passes the A100 fixture, the other 12 hosts launch the same way.
8. **Never** terminate or delete. Cleanup is stop only, and deletion is the user's.

## What this means for the Specialized build (`durability-gated-worker-20261004`)

- It is no longer on this matrix's critical path. Its uses are:
  1. **Retries:** a lost or failed host or unit relaunched with GitHub acknowledgements and restore. It must accept the `dev-matrix-002` tree pulled to this Mac as the starting point. A lost fresh start still needs the operator tombstone.
  2. **The next stages:** development attribution features on a0 trajectories, held-out jobs and Stage B.
  3. **Later runs:** the same path once the backup token exists.
- Its validation runbook should start from a host of this run, not repeat the matrix.

## Open for Specialized to confirm or object to

1. The `dev-matrix-002` naming, and the dropped old-host branch.
2. The 6-hour cap with no lease: a host that needs more than 6 hours loses its running unit.
3. Starting before the gated worker exists, with the known gap in addition 2.

## Agreed with Specialized Implementation (its reply, 4 October 2026)

- **All three points agreed.** The runner requires every host's own bootstrap receipt and `fixture_exact`, with no branch.
- **Timer settings** are generated immediately before each pod's creation. A cap is never extended by editing a pod's environment, which restarts the container. If a host needs longer, a lease record on the mount extends it.
- **Volumes.** The pod volume is 20 GB instead of 100: the venv, data and outputs fit, and the models sit on the 60 GB container disk.
  - Idle storage for 13 stopped pods is about $0.07/h.
  - After the run the user deletes the stopped pods, or tops up, once the pulled copies are verified and backed up.
- **Verification.** Each pulled sealed unit (with `COMPLETE.json`, plus `registry.jsonl`) is verified on this Mac with `python -m experiments.durability ingest` into a local destination. Its restore-verified acknowledgements are what a later retry through the gated worker restores from.
- **Before the other 12:** no other pod running, and the account's hourly spend as expected.
- **Timing.** The estimate is thin. dev05's first job duration is watched, and caps are extended by lease where needed and the balance allows.
