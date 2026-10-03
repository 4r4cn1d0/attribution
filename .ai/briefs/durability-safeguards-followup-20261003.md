# Bounded follow-up: durability-safeguards-20261003 review findings

- **From:** the General Implementation session, acting as lead. The user said there is no GPT brief.
- **Review status.** The first candidate passed my independent run: 228 passed, exit 0, workspace unchanged. I read every module.
- **Findings.** Three are confirmed by reproductions that fail on the candidate; two more are smaller. Fix them in the same workspace, under the same rules as the original brief (`.ai/briefs/durability-safeguards-20261003.md`):
  - edit only the 19 files you created;
  - CPU only, with the pinned venv;
  - no provider, network, GPU, payment, held-out access, commits or agents.

## Reproductions

- **File:** `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution/73f52237-deb4-4487-bcbe-34ef328c6b9e/scratchpad/repro_durability.py`
- **Run them with:**

  ```bash
  DUR_WS=<workspace> PYTHONDONTWRITEBYTECODE=1 <pinned venv python> -m pytest -q -p no:cacheprovider --basetemp=<scratch> repro_durability.py
  ```

- **Current result:** 3 failed.
- **Expected after the fix:** pass. Fold them into your test files as regression tests.

## Required fixes

### A. Pin written after the acknowledgement (crash consistency)

- **Problem.** `Vault._acknowledge` writes `acks/<unit>.json` and then `_put_pin` for prepared and code units. Suppose the process dies between those two writes. Every retry takes the duplicate branch and returns early, so the pin is never written. `_require_pins` then refuses every engine unit in that vault permanently.
- **Reproduction:** `FaultyDestination(crash_on="pins")`; `test_A_...` fails with `vault.pin(...) is None` after the retry.
- **Fix:** the duplicate branch, and any path that finds an existing acknowledgement, must ensure the pin exists for prepared and code kinds. `_put_pin` is idempotent.

### B. Another worker's retention reserve is not held

- **Problem.** `admit` subtracts only the admitted worker's own `retention_reserve`. A lease does not record its reserve, so admitting a second worker can spend the first worker's post-compute storage reserve.
- **Reproduction:** with balance = 2·need + RESERVE + 0.01, both workers are admitted (`test_B_...`: DID NOT RAISE).
- **Fix:**
  - Record the reserve, and the end of its retention window, in the lease.
  - When admitting, hold every other worker's reserve while its window extends past the balance reading. Use one reserve per worker: the latest lease's, so renewals are not double-held. Released or superseded leases still count until their window ends, because the volume still bills.
  - A ledger row that cannot be parsed must fail closed as `AdmissionRefused`, never a bare `TypeError`.

    This matters for Stage B. A non-`DurabilityError` escaping the gate inside `GatedBackend.execute` would become a charged failed attempt instead of an uncharged refusal.
  - Update the formula in the README, the module docstring and the research note.
  - Add a test for renewal and release.

### C. One block per process is not enforced in `run_block_gated`

- **Problem.**
  - Each call builds a new `GatedBackend`. Stage B detects a shared process by membership of the backend object in `_SERVED_BACKENDS` (or by its own `_blocks_run`).
  - So a second gated block on the same warm `inner` in one process records `process_shared_with_an_earlier_block: false`.
  - Its setup is unmeasured, but it is labelled measured, so its costs can be labelled complete. That is a silent cost error.
- **Reproduction:** `test_C_...`.
- **Fix (recommended):** refuse fail-closed, before anything is written, when `run_block_gated` is called again with an `inner` that already served a block in this process: one block per process, the project's rule. A module-level WeakSet of served inners works.

  If you prefer to let Stage B label the session as shared instead, show why that is equally safe.

## Smaller items: fix, or document precisely

### D. Where safeguard time lands in Stage B (documentation correction)

- `GatedBackend.execute` runs inside the attempt's own timer, between Stage B's `start = clock()` and `end = clock()`. It runs the gate check (acknowledgement reads) and `open_attempt` (the `started.json` copy and its check).
- That time is therefore in the attempt's measured seconds: operation time, which also feeds the overrun comparisons. Only settle in `sync()` before the timer and in `verify()` falls in the controller seconds.
- Correct the README, the module docstring and the research note.
- If a test can show the split with a destination that takes fake time, add it.
- This is part of the lead decision on safeguard time in Stage B costs; do not change the behaviour.

### E. Dependency acknowledgement in the restore check

- **Problem.** `_restore_verify` fetches dependency folders from whatever is stored under their recorded path (`_fetch_folder`), acknowledged or not. `restore()` places only acknowledged units.
  - After a transient failure between a dependency's commit and its acknowledgement (possible in `acknowledge_sealed_tree`), a dependent unit could be acknowledged while its dependency is not.
  - A later `restore()` would then not bring that dependency back. It fails closed at continuation time, but "acknowledged" should imply "restorable".
- **Preferred fix:** require each dependency folder's own acknowledgement, at the same seal, in `_restore_verify`. The dependency is a `run` unit at that root or an `attempt` unit at its parent.
- **Alternative:** document it as a limitation, with the reason you chose not to fix it.

### F. Liabilities of leased workers (documentation only)

- Liabilities that name a leased worker are skipped entirely: the lease is assumed to cover them.
- State this assumption for the funded validation: a worker's extra volumes or GPUs that are not in its rate card would be under-counted.

## Acceptance

- The three reproductions pass, folded into your tests.
- New tests for B (renewal and release) and C (refusal).
- Durability suite plus Stage B suite pass with the pinned venv; Stage B stays at 172 passed. Report the exact commands and exit statuses.
- Docs updated: README, module docstrings, research note.
- Report back to "General Implementation" via SendMessage:
  - changed files with new hashes;
  - what each fix does;
  - anything you disagree with, and why.
