# Bounded assignment: an in-pod stop timer as the primary shutdown, with the GitHub watchdog as a backup

## Task and authorization

- **Task ID:** durability-pod-timer-20261004.
- **Authority:** on 4 October 2026 the user chose "Timer inside the pod" (General Implementation acting as lead; no GPT brief). The trigger was the deployed GitHub watchdog's schedule, which ran 3 of 33 slots in its first 16 hours, with up to 5 h 46 min between scans. The record is `.ai/inputs/study-v2-20261002/durability-watchdog-deployment.json`.
- General Implementation reviews, integrates and deploys.
- **You do not:**
  - push, commit or deploy;
  - call any real service (no GitHub or RunPod request, no pod);
  - handle secrets, install anything or launch agents.
- You may read public documentation on the web to verify facts.

## Why

Today `RunPodProvider.arm_shutdown` delegates to `GitHubActionsWatchdog`, whose acknowledgement requires a scheduled scan within the last 75 minutes. With the observed schedule, most arms are refused. That is fail-closed, but it blocks the funded validation, and a lease that was granted could see its stop hours late.

The new stop must:

- be exact to within seconds of the end of the reservation;
- hold when the worker's processes die and the laptop is off;
- not depend on GitHub's scheduler;
- be confirmable before a lease is granted.

## Design to evaluate

Challenge this before building. It is the lead's sketch, not a specification.

1. **Timer process.** A small timer process, standard library only, runs inside the pod.
   - The pod's start command starts it before anything else.
   - It is supervised, so it comes back if it dies.
   - It is never a child of the worker.
2. **Persistent deadline.** The deadline lives on the pod's persistent mount: the network volume, confirmed by `confirm_persistent`.
   - A container restart therefore re-arms from it.
   - A deadline already past at start means stop at once.
3. **Creation-time cap.** Until the first lease is recorded, the timer obeys a deadline fixed at pod creation, given in the pod's environment. A pod whose laptop died right after creating it still stops.
4. **Arming.** Admission arms by writing a lease record, atomically and create-only. It then reads the timer's acknowledgement of that record, plus a fresh heartbeat, within a short window.
   - The latest valid record governs, so a renewal extends the deadline.
   - A malformed or truncated record is ignored, and the previous valid deadline stays.
5. **At the deadline.** Stop the pod through RunPod: never terminate or delete it. Confirm the stop, record the outcome on the persistent mount, and retry while it is unconfirmed.
6. **The GitHub watchdog becomes a best-effort backup.** Admission attempts it with a bounded wait and records the outcome, but never requires it.
   - Keep its code and change its role through configuration.
   - If `watchdog/watchdog.py` or `pods.example.json` must change, their pins in `watchdog.yml` change too. Say so, because the deployed copy then needs a Workflows-capable push.

## Facts to verify

Cite current RunPod documentation for each, and list separately what you could not verify.

- **How a process inside a pod stops its own pod.**
  - Is `runpodctl` present, and what is the exact command?
  - Does RunPod inject an API key into pods, and with what scope? Can it stop only its own pod?
  - Otherwise, what is the smallest credential the pod must hold?
- **The start command.** What does overriding `dockerStartCmd` or `dockerEntrypoint` do to the default start of `runpod/pytorch` images (SSH, Jupyter)? How is SSH kept working?
- **Restarts.**
  - Does RunPod restart a container whose main process exits?
  - Does a restart keep the pod volume and the network volume?
  - Does a stopped pod still bill for its GPU?
- **First boot.** The network volume may be empty at first boot, so how does the timer reach it? The start command or an environment variable may have to carry the script. Check the size limits for both.

## Constraints

- **Code.** Standard library only on the pod side.
  - Fail closed everywhere.
  - No secret in any log, record or error.
- **Unchanged.** The engine, Stage B and the anonymous exporter do not change.
  - Stage B open decision 4 (safeguard time inside policy costs) stays deferred.
  - State whether the timer adds any time inside Stage B sessions.
- **Least privilege.**
  - The worker never holds a key that can stop or modify other pods.
  - State exactly which key does what, and where it lives.
- **Lateness.** Keep the existing lateness and shutdown-delay rules in admission, now with the timer's own lateness, which should be seconds. Do not loosen any other admission input.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/pod-timer-20261004/workspace`. It is a manual copy of the project at commit `c9316ed`, with `manifest.json` beside it.
- **Owned:** `experiments/durability/**` and `research/experiments/2026-10-03-recovery-safeguards.md`.

## Tests (local only)

- **Fixtures:**
  - a manual clock;
  - a fake RunPod API on 127.0.0.1, or a fake stop command;
  - a temporary directory as the persistent mount;
  - at least one subprocess test where the timer is a real separate process that is killed and restarted.
- **Cases:**
  - the stop happens at the deadline and never before;
  - the creation-time cap applies when no lease exists;
  - a renewal extends the deadline;
  - a malformed or truncated record is ignored;
  - a deadline already past at start stops at once;
  - the worker's death does not affect the timer;
  - a killed timer is restarted by its supervisor and re-arms;
  - a container restart re-arms from the mount;
  - an unconfirmed stop is retried;
  - nothing is terminated or deleted;
  - admission refuses without the timer's acknowledgement, or with a stale heartbeat;
  - admission succeeds when the timer acknowledges while the GitHub watchdog refuses or is unreachable;
  - secrets are absent from logs, records and errors.
- **Run:** the full durability and Stage B suites with `tmp/minimal-experiment-20261002/venv/bin/python`, with caches disabled and basetemp in your scratchpad. Stage B stays at 172 passed.

## Docs

- **README:**
  - what runs where;
  - the arm protocol;
  - a failure table saying which layer covers worker death, the laptop off, a container restart, a timer crash, a container that never starts, and GitHub's schedule going silent;
  - the user's steps: pod-creation settings and keys;
  - what the funded validation must show: a real stop at the deadline with the laptop disconnected and the worker killed, and a re-arm after a restart.
- **Decisions.** Record the user's choice of 4 October 2026 under "Open decisions", in both the package README and the research note. It amends the shutdown decision of 3 October: the GitHub watchdog becomes a backup.

## Report back

Send the report to "General Implementation" with SendMessage. Include:

- files and hashes;
- the design, and the options you rejected;
- the facts you verified, with sources, and those you could not verify;
- commands and their exit statuses;
- deployment steps;
- user steps;
- the weakest assumption, a counterexample, and the check that would settle it.
