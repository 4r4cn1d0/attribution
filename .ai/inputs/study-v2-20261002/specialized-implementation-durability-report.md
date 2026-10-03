# durability-safeguards-20261003: report from "Specialized Implementation"

Date: 2026-10-03. Workspace: `tmp/claude-workspaces/durability-20261003/workspace`.

**Outcome.** The safeguards are implemented as a new package and pass locally: durability suite **56 passed**, Stage B suite **172 passed** (unchanged), combined **228 passed, 0 skipped, exit 0**, in the pinned engine environment on CPU. All three decisive checks are shown by tests, and the one-off restore check on a preserved chain succeeded. No existing file was changed (every file listed in the workspace's `manifest.json` still has its recorded hash); no provider, network, GPU, payment or held-out access; nothing committed or installed; no agents.

**Routing as observed here:** the harness states this session runs `claude-fable-5-1`. I cannot observe the effort setting. This statement is not verification.

**This does not satisfy the restart prerequisites.** The provider and remote-destination adapters are deliberately unconfigured and refuse every call; the funded one-worker validation remains required (list at the end).

## New files (19)

- `experiments/durability/`: `__init__.py`, `common.py`, `destination.py`, `units.py`, `backup.py`, `admission.py`, `gate.py`, `engine_units.py`, `stage_b.py`, `__main__.py`, `README.md`
- `experiments/durability/tests/`: `conftest.py`, `dur_fixtures.py`, `test_dur_vault.py` (14 tests), `test_dur_admission.py` (30), `test_dur_engine.py` (5), `test_dur_stage_b.py` (5), `test_dur_stage_b_engine.py` (2)
- `research/experiments/2026-10-03-recovery-safeguards.md`

SHA-256 of all 19: `<scratchpad>/durability-final-sha256.txt`. A copy of the new files: `<scratchpad>/durability-final/`. `<scratchpad>` = `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution/243bb6cc-53ef-4581-a747-392d47528efe/scratchpad`.

## Design

- **Vault (`backup.py`).** One namespace per source volume. Files are stored under `tree/<recorded absolute path>`, so the destination already has the recorded layout. `acknowledge(unit)`: capacity check; upload to staging; hash the stored bytes; commit exclusively; restore the unit, its pinned prepared data and source, and every reachable dependency into a fresh tree; `verify_run` on each through one root path map (`/` to the fresh tree), requiring `complete` and, for a run-one, `stream.checked`; then write `acks/<unit>.json` last and exclusively.
- **Units (`units.py`).** `run`, `attempt`, `prepared`, `code`, `failed-run`, `record`. A name always holds the same bytes; a different-hash arrival is preserved under `collisions/` and fails.
- **Append-only files.** Registry, attempt catalogue and journal are stored as snapshots that must extend the previous one; a rewritten registry is refused.
- **Admission (`admission.py`).** The formula in the README; a reservation ledger under an exclusive file lock; leases with expiry; `Provider` interface with `UnconfiguredProvider` as the only shipped adapter.
- **Gate (`gate.py`).** Previous acknowledgement in the destination plus a lease that covers the unit, or nothing starts.
- **Engine (`engine_units.py`).** `UnitRunner` is `calibrate`'s loop written outside the engine, with an attempt catalogue that leaves the worker before each attempt starts.
- **Stage B (`stage_b.py`).** `GatedBackend` wraps any backend; `StudyBackup` copies attempts, records and the registry; `run_block_gated` is the administrative entrypoint.

Rejected alternatives:

- **Manual or host-level copies.** That is the incident's failure.
- **Trusting hash-verified bytes without a restore.** A copy that hashes correctly can still be unusable (missing dependency, wrong layout). Mutation check: skipping the restore check breaks 7 tests.
- **Asynchronous copy overlapping the next unit.** Breaks "no next unit without the previous acknowledgement".
- **`PathMap`-based resume.** The engine reads dependency paths as recorded; relocation is verification only.
- **A paused clock in the Stage B wrapper.** It would hide safeguard time from Stage B's cost record and contradict its cost contract (see open decision 2).
- **`replicate_of` to rerun a lost fresh start.** It relabels a retry as a determinism control and changes the unit's scientific job fields.
- **Refusing every Stage B operation once and re-entering the block.** Each re-entry re-verifies all earlier operations and charges that time to the policies.

## Insertion points (workspace line numbers)

- **Engine: hypothesis confirmed.** `runner.calibrate` (runner.py:1032) calls `run_one` per unit at runner.py:1075, with nothing hookable between units. `run_one` is runner.py:290; it claims the trajectory at runner.py:313 for a fresh start only. `UnitRunner.run` replaces the loop; one `Session` per process is kept.
- **Stage B: hypothesis confirmed.** `Study.ensure_op` (controller.py:358) calls `backend.sync()` (387), `backend.execute` (399), `sync()` (417), then `backend.verify` (376). `RequestRefused` is recorded as `refused` at controller.py:405-408. `run-block` builds `EngineBackend` at `__main__.py`:148; `run_block_gated` builds the wrapper instead.
- **Registry.** `jobs.claim_trajectory` (jobs.py:181): the liveness rule is jobs.py:186.
- **One finding against "COMPLETE.json is written last".** `runner._finish` rewrites `status.json` after the seal (runner.py:233). It is unhashed, so the seal is unaffected; a copy that catches it mid-rewrite fails its hash check and is retried.

## Requirements 1-7

| # | Code | Tests | Gaps |
|---|---|---|---|
| 1 Unit | `units.py`; pins and append-only snapshots in `backup.py` | vault tests; Stage B engine test (attempt units with chains across attempts) | none known |
| 2 Prompt copy + acknowledgement | `Vault.acknowledge`; called right after each seal by `UnitRunner` and by `GatedBackend.verify`/`sync` | partial, corrupt, changed-during-copy, missing dependency/pin, crash before/after, full disk, duplicates, collision | No watcher daemon: units sealed by a process this package did not launch need `acknowledge_sealed_tree` to be called |
| 3 Gate | `gate.py`; `UnitRunner._launch`; `GatedBackend.execute` | engine gate test; Stage B lease and failed-copy tests | `UnitRunner` launches run-one only |
| 4 Admission | `admission.py` | 24 fail-closed cases, formula, concurrency (two threads), renewal, expiry | Ledger needs one shared location for several pods; money is float; a unit running past its lease is not stopped by this code (the provider shutdown is) |
| 5 Durable source, independent destination | `check_storage`; `Destination` + `UnconfiguredDestination` | storage refusal cases | Independence, retention and funding are declared, not measured |
| 6 Restore and resume | `Vault.restore`; `UnitRunner.reconcile`/`declare_lost`; `stage_b.reconcile_claims`/`declare_lost_attempt` | decisive (a) and (b); lost fresh start (engine, and Stage B with the real engine) | The kill is simulated in-process (the destination as it was at the kill is swapped in); the old calibration jobs recorded a relative `resume_from`, so continuing those exact chains needs the original working directory |
| 7 Outcome-blind | whitelisting `Journal`; `reveal_paths=False` enforced for Stage B | blind-log tests in both vault and Stage B suites | Stage B manifests in the destination hold paths (needed for restore); they are payload, not logs |

Decisive checks:

- **(a)** `test_a_sealed_chain_is_restored_after_its_source_is_removed_and_continued`: q, e1 sealed and acknowledged; killed during e3; volume removed; restored to the same absolute paths; every sealed file byte-identical before and after; e1 verified with no path map and stream checked; e3 ran as attempt 2; attempt 1 catalogued lost with unknown cost.
- **(b)** `test_a_study_killed_mid_block_is_restored_and_resumed_with_the_lost_attempt_kept`: restored records byte-identical; lost attempt closed by Stage B as interrupted with `seconds: None`; retry is attempt 2 in session 2; no screen operation reran; the block's cost stays a lower bound with no margin; a restore of the final vault reproduces the study tree. Also run through the real `EngineBackend` (`test_dur_stage_b_engine.py`).
- **(c)** `test_no_unit_launches_without_the_previous_acknowledgement_or_a_valid_lease`.

## Commands run (workspace root; `PY` = `tmp/minimal-experiment-20261002/venv/bin/python`, Python 3.11.15)

Suite command: `PYTHONDONTWRITEBYTECODE=1 $PY -m pytest -q -rs -p no:cacheprovider --basetemp=<scratchpad>/pytest-dur <paths>`

| when | paths | result | exit |
|---|---|---|---|
| baseline | Stage B tests | 172 passed | 0 |
| first vault run | `test_dur_vault.py` | 1 failed (a real bug: staging keys were not recognized under a namespace) | 1 |
| after the fix | `test_dur_vault.py` | 1 failed, 13 passed (a wrong test assertion) | 1 |
| | `test_dur_engine.py` | 1 failed, 4 passed (a wrong test assertion) | 1 |
| | Stage B + engine durability tests | 1 failed, 9 passed (a wrong test assertion) | 1 |
| | all durability tests | 3 failed, 51 passed (test-helper mistakes) | 1 |
| | all durability tests | 54 passed | 0 |
| | `test_dur_stage_b_engine.py` | 2 passed | 0 |
| **final** | durability + Stage B | **228 passed, 12 warnings** | **0** |
| final | Stage B alone | 172 passed | 0 |
| final | durability alone | 56 passed | 0 |

Mutation checks on a scratch copy (workspace untouched), durability suite each: gate ignores acknowledgements (2 failed); acknowledgement without the restore check (7); Stage B wrapper without the gate (1); no hash check of staged bytes (2); admission ignores other leases (2); lost fresh start not checked (1). They ran before a final tidy of three long lines and two unused test imports; the suite was rerun after it (228 passed).

One-off check (outputs in `<scratchpad>/dry-run-restore-check/`, source read-only):

- `python -m experiments.durability ingest ...` on the preserved dev01 chain `1101-g-1f744bb3364064e2` (q, e1, e3) with `prepared-v1` and the current engine source: exit 0; 5 units acknowledged; 1, 2 and 3 engine folders verified with the stream checked.
- `python -m experiments.durability restore --mirror ...`: exit 0; 100 files, 77,774,438 bytes.
- The 63 restored run files are byte-identical to the preserved ones (`diff` of sorted SHA-256 lists).
- `python -m experiments.safety_selection verify --run <mirror e3> --prepared <mirror prepared> --map ...`: exit 0, complete, stream checked.
- The 75 source files hash the same before and after.

No `__pycache__` or `.pytest_cache` was created in the workspace.

## Open decisions for you

1. **Tombstones.** A lost fresh start is rerun only after an operator-named administrative `error.txt` is written in the lost attempt's folder. It uses the engine's own "preserved failed start" rule and edits no engine file or registry line, but it is an administrative file with an engine-significant name. The alternative is that such a unit is unrunnable in that registry (Stage B's existing behaviour: bounded charged failures).
2. **Stage B cost of the safeguard.** Settle time inside a session lands in the controller seconds of the step that owns the operation, so it enters the policy costs and T. I chose this because nothing is hidden and no Stage B contract is contradicted; the catch is that the measured costs now include the mandated copy and restore check. Excluding it needs a paused clock and a Stage B contract amendment.
3. **Strict synchronous gate.** A billed GPU idles during each copy and restore check.

## Weakest assumption

That a real destination behaves like a local directory: an exclusive create is atomic, and a read-back returns what is durably stored.

- **Counterexample.** A network or FUSE mount with write-back caching: the upload returns, the read-back hash and even the acknowledgement are served from the worker's cache, the pod dies before the flush. The gate then let later units start on an acknowledgement that never existed off-pod.
- **Check that would change my mind.** In the funded validation, kill the worker hard right after an acknowledgement and read the acknowledgement and the bytes from an independent machine. If they are missing, the adapter must confirm durability through the store's own API, and the restore check must run from an independent reader.

Second weakest: provider semantics (what the balance number means, whether `arm_shutdown` replaces an earlier timer). The interface only states what must be true.

## Limitations and pending validations

- Pending (funded one-worker validation): a real persistent mount at the recorded path; an off-pod copy made by the worker with the laptop disconnected; a restore on a fresh provider host; a provider-side timed shutdown; real balance semantics; a restored CUDA continuation.
- A unit that seals just before the worker dies, with no time for its copy, is still lost.
- The Stage B settle-time effect on costs is not measured by the tests (the fake clock does not advance during a settle).
- In `run_block_gated`, the pre-block pending check runs in the block's process, so its (small) time is in the session's start record.
- `GatedBackend` looks like a fresh backend to Stage B's shared-process detection; build one per process.
- README and research note name three lead decisions; neither document claims a cloud guarantee.
