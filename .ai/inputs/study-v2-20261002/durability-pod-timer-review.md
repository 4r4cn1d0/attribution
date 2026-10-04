# In-pod stop timer: review and integration record

4 October 2026. Written by the General Implementation session, acting as lead at the user's instruction (no GPT brief).

- **Implementation:** Specialized Implementation, under `.ai/briefs/durability-pod-timer-20261004.md`.
- **Records in this folder:**
  - the author's report: `specialized-implementation-pod-timer-report.md`;
  - the diff against the previous commit: `durability-pod-timer.diff`;
  - the source pin: `durability-pod-timer-source.json`;
  - the test log: `durability-pod-timer-tests.log`.

**What this is not.** It is not a restart authorization. Admission stays closed until a cap-only pod has been seen to stop itself and that observation is recorded as `stop_confirmation`. That needs the user's keys and a funded pod.

## Checks

- **Scope.** 16 files: 12 changed and 4 added, all inside `experiments/durability/**` and the research note.
  - All 16 reported hashes match.
  - No cache was written.
  - No project file on a touched path had changed since the workspace was made. This was checked again immediately before the copy.
- **Tests, in the pinned engine environment:**
  - In the workspace: durability plus Stage B, 393 passed, exit 0, and the workspace was unchanged.
  - From the integrated project: 393 passed (`durability-pod-timer-tests.log`).
  - Durability now has 221 tests and Stage B stays at 172.
  - No timer process was left running after either run.
  - The full run was done after a CPU-heavy job had finished, because the subprocess tests use real time with a 2-second tolerance.
- **Full read of `pod_timer/pod_timer.py`, and of the start command in `shutdown_timer.py`:**
  - The governing authority is the most recently issued valid one: a lease not withdrawn, or the creation cap. With no valid authority the pod stops at once.
  - The deadline is enforced from memory by the main thread, and the mount is only touched by a second thread.
  - The stop is asked for through `runpodctl pod stop` (the command RunPod's own documentation gives for a timed stop inside a pod), the older `runpodctl stop pod`, REST and GraphQL. Requests repeat every 15 s until the pod is stopped.
  - Nothing terminates, deletes, resets or restarts a pod.
  - The key goes only into an `Authorization` header and is scrubbed from records.
  - The start command falls through to a stop loop if the script cannot be unpacked, fails its SHA-256 check, finds no `python3`, or if the supervisor ever exits.
- **The six departures from the lead's sketch are accepted:**
  1. the recorded self-stop gate;
  2. `key_env`, because `RUNPOD_API_KEY` inside a pod is RunPod's pod-scoped key;
  3. the most recently issued authority governs, the cap included;
  4. the supervisor is not PID 1;
  5. the backup watchdog's stop time is the end of the reservation;
  6. the stop is enforced from memory.

## Findings

No blocking defect. Notes:

1. **The cap bounds only the time before the first lease.** A later lease may run past the cap, by design. This holds against a dead worker and a dead laptop, not against a faulty worker that writes leases, which holds the pod-scoped key anyway.
2. **A restarted timer can stop the pod early.** It waits up to 60 s for the mount before enforcing with the cap alone. A slower mount can therefore stop the pod early, which is the safe direction.
3. **The deployed watchdog is out of date.** `attribution-backups` still has the old pinned `watchdog.py`, so backup arms marked `role: backup` will mostly be refused (no recent scheduled scan). The backup is never required. Redeploy `watchdog.py` and `watchdog.yml` together, with the pod's entry in `pods.json`, using a Workflows-capable credential.
4. **Unverified until a real pod runs:**
   - what the pod-scoped key may do;
   - whether the image's `runpodctl` has `pod stop`;
   - how long a stop takes;
   - any size limit on environment variables;
   - whether a process started through SSH sees the pod's environment.
5. **The settling check.** The cap-only pod is the first funded step: a cap of about ten minutes, the laptop disconnected, `EXITED` observed from outside, then `stop-attempts.jsonl` read for the method that worked and its latency.

## Integration

The 16 files were copied after the concurrency check. Post-copy hashes equal the workspace hashes; see `durability-pod-timer-source.json`.
