# Recovery safeguards: review and integration record

3 October 2026. Written by the General Implementation session, acting as lead at the user's instruction (no GPT brief).

- **Implementation:** the Specialized Implementation session, under two briefs:
  - `.ai/briefs/durability-safeguards-20261003.md`;
  - the follow-up, `.ai/briefs/durability-safeguards-followup-20261003.md`.
- **Records in this folder:**
  - author's report: `specialized-implementation-durability-report.md`;
  - fix-round diff: `durability-safeguards-review-fixes.diff`;
  - routing: `durability-safeguards-routing.json`;
  - source pin: `durability-safeguards-source.json`.

**What this is not.** It is not a restart authorization. The provider and remote-destination adapters are unconfigured and refuse every call, so admission cannot succeed on a real deployment. The funded one-worker validation remains required.

## First candidate: checks and findings

### Checks

- **Scope.** 19 new files only. Every file of the workspace manifest is unchanged, and no caches were written. The 19 hashes match the author's list.
- **Independent run** in the pinned engine environment (`tmp/minimal-experiment-20261002/venv`): durability plus Stage B, 228 passed, exit 0. The workspace was unchanged.
- **Full read** of every module: `backup.py`, `destination.py`, `units.py`, `common.py`, `gate.py`, `admission.py`, `engine_units.py`, `stage_b.py`, `__main__.py`, the README and the research note.

### Findings

Each of the three confirmed findings has a reproduction in `durability-safeguards-reproductions.py` that failed on the first candidate.

- **A. A crash could block engine units permanently.**
  - The pin record of a prepared or code unit was written after its acknowledgement, and the duplicate path returned before writing it.
  - So a process that died between those two writes left the identity unpinned for good, and every engine unit in that vault was refused.
- **B. A second worker could spend the first worker's reserve.**
  - A lease did not record its retention reserve, so admitting a second worker could spend the first worker's post-compute storage reserve.
  - Reproduction: with a balance of 2·need + one reserve, both workers were admitted.
- **C. One block per process was not enforced in `run_block_gated`.**
  - A second gated block on the same warm backend recorded `process_shared_with_an_earlier_block: false`.
  - So unmeasured setup was labelled measured, and the costs could be labelled complete.
- **D. Documentation was incomplete.** The gate check and the `started.json` copy run inside each Stage B attempt's own timer, so some safeguard time is operation seconds, not only controller seconds.
- **E. The restore check accepted unacknowledged dependency bytes,** stored but never acknowledged, while `restore()` places only acknowledged units.
- **F. Documentation only.** Liabilities that name a leased worker are assumed to be covered by its lease.

## Fix round: checks

- **Scope.** Still 19 new files. The 12 changed files match the author's v2 hashes. The author's pre-review copy matches the first-candidate hashes verified earlier, so it is a valid diff baseline.
- **Diff reviewed:** `backup.py`, `admission.py`, `gate.py`, `stage_b.py` and `common.py`.
  - **A:** the pin is written idempotently on every acknowledgement, duplicates included.
  - **B:** the lease records its reserve and the end of its retention window. Admission holds one reserve per other worker (its latest lease's, released or superseded included) until the window ends. Every ledger row is validated; an unreadable ledger refuses.
  - **C:** an inner backend or engine `Session` that already served a block in this process is refused before anything is written. The check consults Stage B's own served set read-only, and an untrackable object is refused.
  - **D:** the docs now name all three places safeguard time lands (the attempt timer, the owner's controller seconds, and the session's start record).
  - **E:** a dependency is taken only from an acknowledged holder (a run unit, or the attempt whose `run/` it is). The seal follows from the dependent's own receipts through `verify_run`.
  - **Beyond the brief (accepted):** any exception in the gate becomes a refusal. Only an interrupt can escape, so an unexpected error can never become a charged Stage B attempt.
- **Reproductions:** 3 passed.
- **Independent runs**, pinned environment:
  - in the workspace: durability plus Stage B, 236 passed, exit 0, workspace unchanged;
  - from the integrated project: the same 236 passed (`durability-safeguards-tests.log`);
  - the frozen engine suites (`experiments/safety_selection/tests`, `experiments/minimal_safety/tests`): 228 passed and 3 skipped, all three needing a CUDA GPU (`durability-safeguards-engine-tests.log`);
  - the project's `experiments/`, `research/` and `.ai/inputs/` were byte-identical before and after.
- **Integration.**
  - The project's engine, Stage B and research files had not changed since the workspace was made.
  - None of the 19 paths existed, so the copy was a pure addition with any overwrite refused. Post-copy hashes are equal.
  - Archive: `tmp/study-v2-20261002/durability-safeguards-source.tar.gz`.

## Not re-run, and why

The author ran a one-off dry run on the preserved dev01 calibration chain before the fix round; I did not repeat it after the fixes.

- **Why not.** That run copies and hashes the whole pinned prepared folder (`prepared-v1`), including its held-out `hidden/` and `auditor/` files, as opaque bytes.
  - The design permits this: the recovery review allows opaque, hash-only transfer.
  - But the user's instruction for this work was not to access held-out data, and I did not need to.
- **Coverage instead.** Fix E's path is exercised by the vault tests on real sealed engine units built from CPU fixtures.
- **Where the author's original outputs are:** `dry-run-restore-check/` in the author's scratchpad.

## Open decisions for the user or lead

1. **Tombstones.** To retry a lost fresh start, the operator writes an administrative `error.txt` that names itself and its operator, so the engine's same-draw retry rule applies. Recommendation: allow it. The alternative makes such runs permanently unrunnable.
2. **Safeguard time inside Stage B costs.** It lands in operation seconds, controller seconds and the session start record, and so it enters T.
   - This does not affect rerunning the engine development work.
   - Before any held-out Stage B run under the gate, either amend Stage B with an uncharged owner (a cost-contract change), or measure the time in the funded validation and show it is negligible against the T tolerance.
3. **Synchronous gate.** The GPU idles during each copy and restore check. Recommendation: accept it for the one-worker validation and measure it there.

## Limitations carried forward

- **No real adapters exist.** The real `Destination` and `Provider` adapters remain for the funded validation, and a write-back-cached remote mount is the weakest assumption.
- **Multiple pods need a shared ledger.** The reservation ledger must live where every worker's admission sees it.
- **One unit can still be lost.** A unit that seals just before the worker dies, with no time for its copy, is lost.
- **Old chains need their original directory.** Old calibration jobs recorded a relative `resume_from`, so continuing those exact chains needs the original working directory.
- **Not done.** No commit has been made, and `.ai/HANDOFF.md` has not been updated: the user's instruction for this task excluded editing it.
