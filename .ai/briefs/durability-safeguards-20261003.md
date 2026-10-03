# Bounded assignment: recovery safeguards before any cloud restart (local only)

## Task and authorization

- **Task ID and authorized outcome:** durability-safeguards-20261003. Implement and locally test the administrative safeguards that the 2 October Runpod incident record requires before any cloud training restarts. This is item 4 of `research/experiments/2026-10-03-local-work-plan.md`.
- **Authority:** the user explicitly told the General Implementation session, on 3 October 2026, to finish this step without a GPT brief. The user routes intelligence-heavy implementation to the "Specialized Implementation" session. General Implementation wrote this brief as acting lead; it will review, verify and integrate the result.
- **Not authorized:**
  - any provider, network, cloud, GPU, payment, credit or auto-pay action;
  - held-out data access;
  - any change to the model, data, allocator, N, the frozen stage-A engine or the Stage B package;
  - commits, pushes or publishing.

  This task does not by itself satisfy the restart prerequisites. The funded one-worker validation in the recovery review's last paragraph remains required.

## Required reading

Read these before designing:

- `AGENTS.md`, `.ai/WORKFLOW.md` and `CLAUDE.md`. Worker rules apply, except for the model line: the user routed this task to Fable 5.1, so report the model you actually observe.
- `research/experiments/2026-10-02-runpod-credit-incident.md`: what was lost and why. Retrieval waited for whole-host completion; container disks were ephemeral; there was no balance check; 13 A100 pods ran at about $20.67/hour.
- `research/experiments/2026-10-03-local-work-plan.md`, item 4.
- `.ai/inputs/study-v2-20261002/recovery-lead-design-notes.md`: the lead's first pass.
- `.ai/inputs/study-v2-20261002/recovery-review-notes.md`: the non-author recovery review. The lead accepted its planning constraints, and they are binding here.
- `.ai/inputs/study-v2-20261002/github-backup-restore-test.json`: an earlier fresh restore of 31 sealed calibration units through `verify.PathMap`. It verifies relocated evidence, but it cannot resume work.
- Engine:
  - `experiments/safety_selection/{ledger.py, runner.py, verify.py, jobs.py, common.py}`, and `research/experiments/2026-10-02-stage-a-freeze.md`, under which the engine is frozen.
  - In those files: COMPLETE.json is written last; `runner.Session`, `run_one` and `calibrate`; `verify.verify_run` and its `stream.checked`; `verify.PathMap`; the `jobs.claim_trajectory` registry and its same-draw rules.
  - CPU fixtures: `experiments/safety_selection/tests/ss_fixtures.py`.
- Stage B (integrated 3 October, not to be modified):
  - `experiments/safety_decision_policy/{controller.py, backend.py, __main__.py}`;
  - its write-once study tree, as described in its README's "Study folder";
  - `RequestRefused`: an uncharged refusal before any work, which stops the controller.
- The operational scripts used during the incident live in `tmp/study-v2-20261002/`: `worker_run.sh`, `bootstrap_worker.py`, `dispatch_dev_matrix.py`, `retrieve_*.py`, `transfer.py`, `admin.py`, `remote.py`, `pool_admin.py`, `process_receipt.py`. They are read-only evidence; never edit, run or copy credentials from them.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/durability-20261003/workspace`. The lead prepared it manually with the launcher's exclusion rules (manifest beside it), from the project after the Stage B integration.
- **Owned (new files only):**
  - `experiments/durability/**`: a new administrative package with its own README and tests, stdlib-only where practical;
  - `research/experiments/2026-10-03-recovery-safeguards.md`: the operating procedure and its limits.
- **No edits to any existing file.** If you conclude that a change to an existing file, especially the engine or Stage B, is unavoidable, stop and report why instead of editing.
- No other implementer is active. The General Implementation session is idle while you work.

## Requirements

Each requirement below must be implemented, or else explicitly reported as a gap with the reason.

1. **Unit.** The unit is a sealed engine job: a run folder whose COMPLETE.json was written last. An unsealed saved state is not evidence.
   - For Stage B, also back up the study tree's write-once records and each operation attempt once its after-call `receipt.json` exists.
   - Determine from the code exactly which files make up a unit, including:
     - its reachable training dependencies;
     - the pinned prepared data, source and recipe identities;
     - the separate attempt records;
     - append-only files such as the trajectory registry (`registry.jsonl`).
   - Journals and acknowledgements stay outside sealed folders, because the verifier rejects additional files.
2. **Prompt off-pod copy with an acknowledgement gate.** Discover each newly sealed unit promptly; never wait for a host, seed or stage to finish.
   - Copy to a temporary location in the destination, verify byte hashes there, then restore-verify:
     - rebuild the unit and its dependency closure in a fresh tree, in the canonical recorded layout;
     - run `verify_run` on the unit and on every reachable training dependency, requiring `stream.checked = true` (`complete = true` alone is not enough).
   - Only then write an immutable acknowledgement. An incomplete copy, a sender receipt or `status.json` is not an acknowledgement.
   - Retries are idempotent: identical verified content is reused; a same-name, different-hash collision fails and preserves both. Source evidence is never deleted.
3. **Dispatch and admission gate.** No next unit starts on a worker without the previous unit's verified acknowledgement, and none without a valid admission lease.
   - Find the insertion points in the code; do not assume them. Hypotheses to confirm or refute:
     - **Engine:** an administrative unit runner calls `runner.run_one` per job in place of `calibrate`'s loop, keeping one `Session` per process where practical.
     - **Stage B:** a wrapper around `EngineBackend` refuses with `RequestRefused` before any work when the gate is unmet.

       A wrapper changes no Stage B code and no policy code identity. Stage B records such a refusal as uncharged, and it stops the controller.
       `run-block` constructs `EngineBackend` directly, so an administrative entrypoint would construct the wrapper.
4. **Balance and runway admission.**
   - Inputs:
     - a timestamped, explicitly recognized balance reading with its currency and source;
     - all active and pending account liabilities;
     - GPU and storage rates;
     - the planned increment of work;
     - backup and shutdown delays;
     - a retention reserve;
     - a stated contingency.
   - Missing, stale, negative, non-finite, ambiguous or changed-rate inputs block admission, as does insufficient runway.
   - Reservations are serialized across workers, so two workers cannot both reserve the same runway.
   - Admission grants a lease with an expiry. Continuing past the expiry requires a renewed admission; shutdown at expiry goes through a provider interface. Stopping Python does not stop GPU billing.
   - **Do not invent a provider balance or shutdown API.** Define interfaces whose real adapters fail closed as "not configured", and use fakes in tests. The live adapters belong to the funded validation.
5. **Durable source and independent destination.**
   - Admission requires a declared, provider-confirmed persistent source location and a separate off-pod destination that is recoverable independently of the GPU account.
   - Check capacity and permissions; retention and funding of the destination are declared inputs.
   - Locally, a destination is a directory, and remote adapters are stubs that fail closed. No credentials appear in any record.
6. **Restore and resume.**
   - Rebuild the canonical recorded layout by mounting or placing files at the same paths, never by rewriting receipts. `PathMap` relocation is verification only.
   - Reverify the sealed predecessor, then create a new explicit attempt for the missing work.
   - Lost attempts and their costs are kept. A same-seed retry is the same draw, not a new one.
   - Keep an administrative catalogue even when lost directories are absent, and never silently clear registry claims. Work out the registry semantics in `jobs.py`.
7. **Outcome-blind operation.** Logs and acknowledgements record paths, hashes, sizes, statuses and timings only. They never record hidden metrics, prompts or policy choices. Held-out payloads are transferred and hashed as opaque bytes.

## Acceptance (local, CPU only)

- **Tests:** `experiments/durability/tests/`, using the engine's CPU fixtures to create real sealed units, and the Stage B synthetic fake backend for Stage B. They must cover:
  - partial and corrupt transfers;
  - missing dependencies;
  - duplicate events;
  - a crash before and after acknowledgement;
  - a full disk or insufficient destination capacity;
  - path-mapping ambiguity;
  - stale and missing balance readings;
  - changed rates;
  - concurrent admission by two workers;
  - a same-name, different-hash collision.
- **The decisive checks.** Each must be shown by a test:
  - **Engine chain:** restore a complete chain after its source has been removed, then continue it, with sealed receipts byte-identical before and after.
  - **Stage B:** restore a synthetic study killed mid-block and resume it to completion, with the lost attempts and their costs kept and correct new-attempt bookkeeping.
  - **Gate:** no subsequent unit launches without the previous unit's acknowledgement.
- **A one-off local check** (scratchpad output, not a test): a dry run of the restore-verify path on one preserved calibration chain read from `tmp/study-v2-20261002/retrieved-calibration/`. Treat it as read-only and skip it if impractical.
- **Commands:** run the tests with `tmp/minimal-experiment-20261002/venv/bin/python` (the pinned engine environment), from the workspace root:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .../venv/bin/python -m pytest -q -rs -p no:cacheprovider --basetemp=<your scratchpad>/pytest experiments/durability/tests experiments/safety_decision_policy/tests
  ```

  - Both suites must pass; the Stage B suite must stay at 172 passed.
  - No network and no installs.
  - Report every command you actually ran, with its exit status.
- **Docs:** the package README and the research note state:
  - the procedure;
  - the admission formula;
  - what is guaranteed locally;
  - what waits for the funded one-worker validation: an actual persistent mount, an off-pod copy with the laptop disconnected, a fresh-provider restore, timed shutdown, real balance semantics, and a restored CUDA continuation.

## Report back

Send the report to "General Implementation" with SendMessage, and keep it in your reply. Include:

- the changed (new) files;
- the design and the alternatives you rejected;
- the insertion points you found, with their file and line;
- how each requirement (1–7) maps to code and tests, or the gaps;
- the commands and their exit statuses;
- limitations and pending validations;
- answers to: the weakest assumption; the counterexample that would break it; the check that would change your mind.
