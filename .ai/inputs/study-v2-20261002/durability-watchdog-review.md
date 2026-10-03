# Shutdown watchdog: review and integration record

3 October 2026. Written by the General Implementation session, acting as lead at the user's instruction (no GPT brief).

- **Implementation:** the Specialized Implementation session, under two briefs:
  - `.ai/briefs/durability-watchdog-20261003.md`;
  - the follow-up, `.ai/briefs/durability-watchdog-followup-20261003.md`.
- **Records in this folder:**
  - the author's reports: `specialized-implementation-watchdog-report.md`;
  - the diff against the previous commit: `durability-watchdog.diff`;
  - the source pin: `durability-watchdog-source.json`;
  - the test log: `durability-watchdog-tests.log`.

**What this is not.** It is not a restart authorization. A lease still needs the user's RunPod secret, a pod on the allow-list, the recorded balance and storage-price confirmations, and the funded one-pod validation. That validation includes a real stop with the laptop disconnected.

## First candidate: findings sent back

- **A. The RunPod key was exposed to repository content.** The backup token's "Contents: write" lets a worker rewrite `watchdog/watchdog.py`, which then ran with the RunPod secret.
- **B. Outdated checkout action.** The workflow used `actions/checkout@v4` by tag.
- **C. Red runs without the key.** With an empty allow-list and no secret set, scheduled runs failed, so the workflow could not be observed before the user set the secret.

## Follow-up round: checks

- **Scope.** 15 files, all inside the brief's ownership (`experiments/durability/**` and the research note): 9 changed and 6 added.
  - All 7 hashes in the author's report match.
  - No cache was written.
  - No project file on a touched path had changed since the workspace was made. This was checked again immediately before the copy.
- **Full read.** All of `watchdog/watchdog.py` and `watchdog/watchdog.yml` (the part that holds the RunPod key), and all of `shutdown_watchdog.py`. Diffs of `admission.py`, `runpod_provider.py`, `wiring.py` and `__main__.py`.
  - **A is fixed.** The workflow pins the SHA-256 of the script and the allow-list. The check runs in a step with no secret and no repository code, before the key is handed to anything. The script runs as `python3 -I`, so a module placed beside it cannot replace the standard library. The author found and closed this second bypass.
    - Event data reaches the script only through the environment, never in a shell line.
    - The arm id is matched against a strict pattern before any use, and logged values go through `json.dumps`.
    - Tokens go only into their own service's `Authorization` header and are dropped on redirects.
  - **B is fixed.** `actions/checkout` is pinned to a full commit, with `persist-credentials: false`.
  - **C is fixed.** With an empty allow-list a scan reads nothing and calls nothing, and exits 0 without the key. A listed pod with no key fails loudly.
  - **Worker side.**
    - `armed` is returned only after an acknowledgement that matches the arm, worker, pod and stop time and names a run and a recent scheduled scan. Any failure withdraws the arm with a void record.
    - Admission refuses a policy whose `shutdown_delay_seconds` is below the provider's stated lateness.
    - Both sides write timestamps in the same format: ISO, UTC, milliseconds.
- **Facts checked independently on 3 October 2026.**
  - RunPod's REST specification, fetched from `https://rest.runpod.io/v1/openapi.json`:
    - `POST /pods/{podId}/stop` ("Stop a Pod"; 200, 400, 401);
    - `GET /pods/{podId}` (200, 400, and 404 "Pod not found", which the script records as gone);
    - `Pod.desiredStatus` takes the values `RUNNING`, `EXITED` and `TERMINATED`;
    - bearer authentication.
  - `actions/checkout`, through the GitHub API:
    - tag `v7.0.1` is commit `3d3c42e5aac5ba805825da76410c181273ba90b1`, of type commit;
    - it is the latest release, published 20 July 2026;
    - `persist-credentials` is an input at that commit.
- **Tests, in the pinned engine environment** (`tmp/minimal-experiment-20261002/venv`):
  - In the workspace: durability plus Stage B, 333 passed, exit 0, and the workspace was unchanged.
  - From the integrated project: the same 333 passed (`durability-watchdog-tests.log`). Durability alone: 161 passed. Stage B stays at 172.
  - The project's `experiments/`, `research/` and `.ai/inputs/` were byte-identical before and after.
  - The 12 warnings are the known BLAS-reference warnings of `test_dp_ridge`.

## Findings

No blocking defect. Residuals, none of which lets the RunPod key leak:

1. **Actions minutes.**
   - A scan every 30 minutes is billed as at least one minute per run: 1,440 to 1,488 minutes a month even with no pod.
   - That is of GitHub Free's 2,000 minutes, which are shared by all the account's private repositories.
   - If the quota runs out, scans stop, and a lease already granted would not be stopped.
   - Recommendation: disable the workflow between funded runs. This is fail-closed, because without a recent scheduled scan every arm is refused. Re-enable it so that at least one scheduled scan runs before admission.
2. **Liveness counts creation, not success.** The arm handler takes the creation time of the latest scheduled run as evidence that scans are running, not that it succeeded.
   - A scan that fails for a reason the arm run does not share would go unnoticed at arm time.
   - Red runs are visible in the Actions tab.
   - A fix, if wanted: require the latest *completed* scheduled run to be a success.
3. **Records are unsigned** (documented by the author). A compromised backup token can forge or withdraw records. It can also push a change that fails the pin check, which stops nothing. The pins protect the key, not the stop.
4. **A pod that cannot be read keeps the run red.** A pod that answers neither 200 nor 404 is asked to stop, recorded as unconfirmed and retried at every scan, with the run red. That is the safe direction, but noisy.
5. **Not checked:** whether GitHub lets a token without the "Workflows" permission delete a workflow file.
6. **The lateness is an assumption.** `lateness_seconds = 5400` is a bound on GitHub's scheduler, not a guarantee. The funded validation must measure it (`seconds_after_stop_time`).

## Integration

The 15 files were copied with the concurrency check above. Post-copy hashes equal the workspace hashes; see `durability-watchdog-source.json`. The deployment to the backup repository is recorded separately, in `durability-watchdog-deployment.json`.
