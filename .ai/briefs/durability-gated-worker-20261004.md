# Bounded assignment: the gated worker, the pod launcher and the one-pod validation

## Task and authorization

- **Task ID:** durability-gated-worker-20261004.
- **Authority:** the user wants the experiments started as soon as possible ("how much longer to wait for you to start running experiments", 4 October 2026). General Implementation is acting as lead (no GPT brief). It reviews, integrates and runs everything.
  - The user approves every spend at launch time. This task spends nothing.
- **You do not:**
  - call any real service (no RunPod or GitHub request, no pod);
  - handle secrets, install anything, commit, push or launch agents.
- You may read public documentation.

## What exists

- **The frozen development matrix.**
  - Record: `research/experiments/2026-10-02-stage-a-freeze.md`.
  - Plan: `reference/study-v2-20261002/dev-matrix-assets/dev-matrix-plan.json`, a read-only copy of the 2 October plan.
  - 13 hosts × 2 jobs. Each job is the engine's `calibrate --prepared prepared-v2 --recipe configs/study-v2-primary-20261002.json --arms <arm> --seeds <seed> --out-root dev-matrix-001`.
  - The engine, recipe and prepared-data hashes are checked as `reference/.../run_dev_matrix.py` did.
  - The 2 October dispatch, through SSH and with no safeguards, is in `reference/study-v2-20261002/`. Its outputs were lost when credits ran out.
- **The recovery safeguards** (`experiments/durability`):
  - `UnitRunner`: the `calibrate` loop outside the engine, with the gate and acknowledgement between units;
  - `Vault` on `GitHubReleaseDestination`;
  - `AdmissionController` with `RunPodProvider` (`key_env`);
  - the in-pod stop timer (`shutdown_timer`, `pod_timer`) with the GitHub watchdog as backup;
  - restore.

  Admin commands exist (`ingest`, `restore`, `acks`, `check-*`, `pod-timer-settings`). **Nothing yet runs a host's jobs on a pod through the safeguards, and nothing launches such a pod.**
- **The cap-only self-stop check** (a pod with a 15-minute cap, watched from outside) is running at the time of writing. Its outcome becomes the recorded `stop_confirmation`, which General Implementation will pass to you.

## What to build

1. **Pod-side worker.** For example `python -m experiments.durability worker --plan PLAN --host HOST ...`.
   - **Start.** Verify the engine identity and the recipe and prepared-data hashes, as the 2 October runner did. Restore the host's acknowledged units from the destination if there are any. `reconcile`, and refuse until any lost fresh start has an operator tombstone.
   - **Run.** The host's jobs in plan order, unit by unit through `UnitRunner`:
     - admission and a lease before each unit;
     - the off-pod acknowledgement after each seal, before the next unit;
     - lease renewal as needed.
   - **Finish.** Write a completion record and stop the pod through the timer, never by deleting.
   - **Scientific identity.** Show on CPU fixtures that the worker's sealed folders, registry and outputs equal `calibrate`'s for the same arm, seed, prepared data and recipe. Allow only differences the engine itself permits, such as timestamps, and name them. Any other difference is a blocker. Report it; do not "fix" the engine.
2. **Operator-side launcher.** For example `python -m experiments.durability launch ...`.
   - **Create** (refusing duplicates):
     - a network volume, or reuse a named one;
     - one pod with the timer settings (`pod-timer-settings`), the image, the GPU type and the environment;
     - the read key and the backup token as RunPod secret references, never values;
     - `RUNPOD_API_KEY` never set.
   - **Deliver the code and data bundle** and start the worker. Choose between:
     - private GitHub release assets in `attribution-backups`, downloaded on the pod with the backup token;
     - SSH, as on 2 October.

     Prefer no inbound SSH dependency, and justify the choice. The bundle carries `prepared-v2`, including held-out files as opaque bytes, exactly as the 2 October bundles did. Nothing may read them.
   - **Records.** Every request and answer goes to a local record, without secrets.
   - **Never** terminate or delete; refuse a GPU price above a configured limit.
3. **GPU.** The freeze requires "the same actual two-step A100 fixture" on every host, so the matrix runs on A100. Choose the A100 variant by recorded cost per completed unit where the 2 October receipts allow it, and state what the receipts do and do not show. Changing the GPU family would be a protocol amendment: not in scope.
4. **One-pod validation script and runbook.** One host's first unit or units, end to end:
   - launch;
   - admission with the recorded `stop_confirmation`;
   - acknowledgement to GitHub;
   - the worker killed and the laptop disconnected;
   - a restore on a fresh pod, and continuation;
   - the timer stopping the pod at the lease end.

   Measure the timer's lateness, unit throughput and cost per unit, and the safeguard overheads (copy and restore-check time). Say exactly which numbers the matrix's concurrency and runway settings then take.
5. **Matrix runbook.** How the 13 hosts are launched within the measured runway: admission limits concurrency by the balance; host rotation stays as frozen. How a failed or lost unit is retried (the same draw, the attempt kept). The cleanup at the end (stop only; deletion is the user's).

## Constraints

- The engine, Stage B, the prepared data and the frozen recipe and plan do not change.
- Standard library on the pod side, apart from the engine's pinned environment. Fail closed everywhere.
- No secret in any log, record or error. Least privilege as already designed.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/gated-worker-20261004/workspace`. It is a manual copy at commit `74043cc`, with `manifest.json` beside it.
- **Owned:** `experiments/durability/**` and `research/experiments/2026-10-03-recovery-safeguards.md`.
- `reference/` is read-only.

## Tests (local only)

- Fakes for GitHub and RunPod on 127.0.0.1, and the engine's CPU fixtures.
- Cases:
  - worker identity with `calibrate`;
  - restore and continue after a kill between units, and in the middle of a unit;
  - refusal without a lease or an acknowledgement;
  - the launcher's requests (shape, secret references, no `RUNPOD_API_KEY`, duplicate refusal, price limit, nothing deleted);
  - no secret anywhere.
- Run the full durability and Stage B suites with `tmp/minimal-experiment-20261002/venv/bin/python`, caches disabled and basetemp in your scratchpad. Stage B stays at 172.

## Report back

Send the report to "General Implementation" with SendMessage. Include:

- files and hashes;
- the design, and the options you rejected (bundle delivery, GPU choice);
- facts verified, with sources;
- commands and their exit statuses;
- the validation runbook and the matrix runbook, with the exact commands General Implementation will run;
- the user's steps;
- the weakest assumption, a counterexample, and the check that would settle it.
