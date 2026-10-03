# Bounded assignment: a free, independent shutdown watchdog, and the user's recorded decisions

## Task and authorization

- **Task ID:** durability-watchdog-20261003.
- **Authority:** on 3 October 2026 the user told General Implementation (acting as lead, no GPT brief) to "do everything recommended". That included the recommendation to close the shutdown gap with an external, scheduled GitHub Actions stop rather than an undocumented RunPod feature. General Implementation reviews, integrates and deploys.
- **You do not** push, commit, deploy or call any real service. No GitHub or RunPod request, no secret handling, no installs, no agents.

## The gap being closed

`RunPodProvider.arm_shutdown` always refuses, because RunPod documents no confirmable stop time on an existing pod. So real admission refuses (see `experiments/durability/README.md`, "The shutdown gap"). The safeguards need a stop at each reservation's end that:

- is enforced **independently of the worker and the laptop**;
- costs nothing in money;
- can be **confirmed** before a lease is granted.

## Constraints

- **Free.** The watchdog runs in GitHub Actions in the private repo `4r4cn1d0/attribution-backups`.
  - Private-repo Actions minutes are limited: 2,000 a month on the free plan. Assume that plan; per-job usage is rounded up to whole minutes.
  - Hosted jobs run at most 6 hours.
  - `schedule` (cron) is at best every 5 minutes, and its runs can be delayed.
  - Verify these facts in GitHub's current docs, cite them, and compute the minutes your design spends for:
    - the one-pod validation (one or two leases of about 1 to 2 hours);
    - a month of idle time;
    - a month of steady single-worker use.
- **Options to weigh.** Choose and justify one, considering cost, precision, independence and failure modes (a cancelled run, a delayed cron, a superseded or renewed lease):
  1. a cron scan of lease records, with the interval chosen so idle months stay within the free tier;
  2. a per-lease `workflow_dispatch` that sleeps until the deadline and then stops the pod. Minutes are roughly the lease length. It must not stop a pod whose lease was renewed or superseded, and it must be chained for leases near the 6-hour limit;
  3. a combination, for example a per-lease timer plus a sparse cron backstop.
- **Confirmation is fail-closed.** `arm_shutdown(worker, at_utc)` returns `armed` only after an acknowledgement written by the running watchdog for that lease, naming its run, the pod and a deadline at or before `at_utc`. Missing, late or mismatched means `NotConfigured`/refusal and no lease.
  - Admission's `shutdown_delay_seconds` must cover the watchdog's worst-case lateness. State the value you recommend.
- **Least privilege.**
  - The RunPod key reaches the workflow only as an Actions secret, `RUNPOD_API_KEY`, that the user sets.
  - The worker's token is the backup repo's fine-grained token. Add only what your design needs, for example **Actions: write** for `workflow_dispatch`, and state exactly what that adds.
  - The workflow uses the provided `GITHUB_TOKEN` with an explicit minimal `permissions:` block.
  - Check whether RunPod offers restricted API key scopes and recommend the narrowest that can stop a pod.
  - Secrets are never logged and never echoed into workflow output.
- **What the watchdog does at the deadline.**
  - It **stops** the pod. It does not terminate it: the network volume persists, and stopping ends GPU billing.
  - It uses RunPod's documented REST call (verify it). It confirms the resulting status with a GET and records the outcome create-only.
  - It never deletes anything, never stops a pod that no valid lease names, and is idempotent.
- **Code.**
  - Python stdlib only.
  - The workflow script must be self-contained: it runs from a checkout of the backup repo, not this project. Keep its source in this project, for example `experiments/durability/watchdog/`, with the workflow YAML, as files the lead deploys.
  - Worker-side code goes in `experiments/durability`, wired through configuration and fail-closed by default.

## The user's decisions to record

Record these in `experiments/durability/README.md` and `research/experiments/2026-10-03-recovery-safeguards.md`, under "Open decisions", marked as decided by the user on 3 October 2026:

1. **Tombstones are allowed.** Operator-named, never automatic, as implemented.
2. **The synchronous gate's idle GPU time is accepted** for the one-pod validation, and is to be measured there.
3. **Shutdown:** the external GitHub Actions watchdog (this task).
4. **Stage B's safeguard time in policy costs is deferred.** It must be settled before any held-out Stage B run under the gate: either a Stage B amendment with an uncharged owner, or a measurement in the funded validation showing it is negligible.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/watchdog-20261003/workspace`. A fresh manual copy of the project (manifest beside it).
- **Owned:** `experiments/durability/**` (new and changed files) and `research/experiments/2026-10-03-recovery-safeguards.md`.
- The engine and Stage B do not change.

## Tests (local only)

- **Fakes:**
  - a fake GitHub API on 127.0.0.1, with the endpoints your design uses (releases and assets, `workflow_dispatch` and runs if used);
  - a fake RunPod API (stop and get pod).
- **Cases:**
  - deadline logic with a manual clock;
  - renewal and supersession, where an old timer must not stop the pod early;
  - a malformed lease is refused;
  - a lease naming a pod that is not a worker is refused;
  - the stop is idempotent;
  - nothing is ever deleted;
  - an acknowledgement is required before `armed`;
  - a missing or late acknowledgement refuses admission;
  - secrets are absent from logs and records;
  - admission succeeds end to end with every input confirmed in fakes, and refuses when any one is withdrawn.
- **Run:** the full durability and Stage B suites with `tmp/minimal-experiment-20261002/venv/bin/python`, with caches disabled and basetemp in your scratchpad. Stage B stays at 172 passed.

## Docs

- **Exact user steps:**
  - the Actions secret;
  - any token permission change;
  - enabling Actions on the repo if needed;
  - how to check that the watchdog is armed.
- **The minutes arithmetic,** with its sources.
- **What the funded one-pod validation must still show:** a real stop at the deadline, with the laptop disconnected.

## Report back

Send the report to "General Implementation" with SendMessage. Include:

- files and hashes;
- the chosen design and rejected options, with the minutes arithmetic;
- the facts you verified, with sources;
- commands and their exit statuses;
- deployment steps for the lead;
- steps for the user;
- the weakest assumption, a counterexample, and the settling check.
