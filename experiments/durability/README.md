# Recovery safeguards (`experiments.durability`)

Administrative code only. It copies sealed evidence off the worker, proves the copy can be
restored, gates the next unit of work on that proof and on prepaid runway, and restores a lost
worker's evidence into the recorded layout so work can resume. It trains, scores and decides
nothing, and it changes no file of the frozen engine (`experiments/safety_selection`) or of Stage B
(`experiments/safety_decision_policy`).

**Status.** Implemented and tested locally on CPU with fakes (3 October 2026). This does not
satisfy the restart prerequisites of the 2 October incident record by itself: the provider and
remote-destination adapters are deliberately not configured, so admission refuses on any real
deployment until the funded one-worker validation ([what waits](#what-waits-for-the-funded-one-worker-validation)).

The operating procedure and its limits are in
`research/experiments/2026-10-03-recovery-safeguards.md`.

## Modules

| module | imports | what it does |
|---|---|---|
| `common.py` | stdlib, engine `common`/`verify` | errors (all fail closed), the outcome-blind `Journal`, atomic exclusive writes, file locks, strict recorded-path handling (`SourceMap`) |
| `destination.py` | stdlib | the off-pod `Destination` interface; `LocalDirectoryDestination` (works); `UnconfiguredDestination` (every call refuses) |
| `units.py` | stdlib, engine `ledger`/`prepare`/`verify`/`config` | what a backup unit is and which files it holds |
| `backup.py` | stdlib, engine `verify`/`prepare` | `Vault`: copy, hash check, restore-verify, acknowledgement; append-only snapshots; restore |
| `admission.py` | stdlib | balance/runway admission, leases, the reservation ledger, the storage declaration; `Provider` interface and `UnconfiguredProvider` |
| `gate.py` | stdlib | `DispatchGate`: previous acknowledgement and a valid lease, or nothing starts |
| `engine_units.py` | engine `runner` (torch) when it launches | `UnitRunner`: the administrative loop around `runner.run_one`; the attempt catalogue; lost attempts |
| `stage_b.py` | Stage B `common` | `GatedBackend` around a Stage B backend; `StudyBackup`; `run_block_gated` |
| `__main__.py` | stdlib | local commands `ingest`, `restore`, `acks` (no provider command exists) |

## The unit

A unit is something that will not change again (`units.py`):

| kind | root | sealed by | restore verification |
|---|---|---|---|
| `run` | an engine run folder | `COMPLETE.json` | `verify_run` on it and on every reachable dependency; a run-one must have `stream.checked` |
| `attempt` | a Stage B attempt folder | its after-call `receipt.json` | bytes; plus the engine checks of `run/` when that is a sealed engine folder |
| `prepared` | the prepared-data folder | `manifest.sha256` | the manifest hash and every file hash it pins |
| `code` | the `experiments` folder | the engine code identity | the identity recomputed from the copy |
| `failed-run` | a preserved failed run folder | `error.txt` | bytes only: a failure record, never a result |
| `record` | one write-once Stage B file | the file itself | bytes only |

Found in the code:

- **A sealed run** is every file under the folder. `COMPLETE.json` pins all of them except
  itself and `status.json` (`ledger._UNHASHED`). `status.json` is rewritten once *after* the seal
  (`runner._finish`, runner.py:233), so it is copied but pinned by nothing; a copy that catches it
  mid-rewrite fails its hash check and is retried.
- **Reachable training dependencies** are the folders named by `dependencies.json`
  (`resume_from`, `source_run`, `a0_state:*`), followed recursively. Receipts hold the absolute
  resolved path of the machine that ran the job.
- **Pinned identities.** The prepared data (by manifest hash; the whole folder, the held-out bank
  included as opaque bytes), the engine source (the files of `common.code_identity`: every
  `safety_selection/*.py` and the reused `minimal_safety` modules) and the recipe (it travels inside
  the hashed `identity.json`; it must hash to its pin). A run is acknowledged only when the
  prepared data and source it pins are acknowledged in the same vault.
- **Separate attempt records.** Engine: the attempt catalogue (below) and preserved failed
  folders. Stage B: `started.json` before the call, `receipt.json` after it, session records.
- **Append-only files.** `registry.jsonl` (engine: beside the run folders; Stage B: in the study
  root), the attempt catalogue and the journal are stored as snapshots, each of which must extend
  the previous one. A registry whose earlier lines were removed or rewritten is refused.
- **Outside sealed folders.** Journals, the catalogue, locks, scratch and acknowledgements never
  go inside a unit: `verify_files` rejects files added after completion.

## Procedure: copy, verify, acknowledge

`Vault.acknowledge(unit)` (`backup.py`), per namespace (one source volume):

1. An existing acknowledgement of identical content is returned: a duplicate event costs one read.
   Of different content it is a **collision**: the arrival is preserved under `collisions/`, the
   stored unit is untouched and the call fails.
2. Capacity is checked (`free_bytes` against the bytes to copy plus the reserve).
3. Each missing file is uploaded to a staging name; the **stored** bytes are hashed against the
   unit's list. Only when every file matches are they committed, exclusively.
4. **Restore-verify.** The unit, its pinned prepared data and source and every reachable
   dependency folder are downloaded from the destination into a fresh tree in the recorded layout
   (`<scratch>/restore-check-*/<recorded absolute path>`) and checked there through one root path
   map: byte hashes, then `verify_run` on the unit and on each dependency. Each must be `complete`
   and each run-one must report `stream.checked = true`. A dependency is taken only from a unit
   that is itself acknowledged in the vault (a run at that path, or the Stage B attempt whose
   `run/` it is); stored bytes without an acknowledgement do not count, so an acknowledged unit is
   always restorable with its whole chain.
5. The acknowledgement `acks/<unit>.json` is written last, exclusively, and never replaced. For
   prepared data and the engine source a pin record follows it; a retry after a crash between the
   two writes it.

A copy in flight, a published copy without the acknowledgement, a sender-side receipt and
`status.json` are not acknowledgements. A retry after a crash reuses identical stored bytes and
finishes the missing part. Nothing is ever deleted at the source.

## Dispatch gate

`DispatchGate.require(worker, previous, needs_seconds)` (`gate.py`) is a pure check immediately
before work: every previous local attempt (sealed or failed) has its acknowledgement **in the
destination**, sealing the same bytes; and the worker's lease still covers the unit's planned
seconds. A refusal starts nothing.

Insertion points (verified in the code; both hypotheses of the brief hold):

- **Engine.** `runner.calibrate` (runner.py:1032) calls `run_one` once per unit in one loop
  (runner.py:1075) with nothing hookable between units. `UnitRunner.run` (`engine_units.py`) is
  that loop outside the engine: the same job dictionaries, `<name>-a<n>` folders and
  `registry.jsonl`, one `Session` per process; the gate before each `run_one`, the
  acknowledgement after it.
- **Stage B.** `Study.ensure_op` (controller.py:358) calls `backend.sync()` (387) and `clock()`
  before an attempt, `backend.execute(...)` (399) after writing `started.json`, `sync()` (417) and
  the receipt, then `backend.verify(...)` (376). `run-block` builds `EngineBackend` directly
  (`__main__.py`:148). `run_block_gated` builds `GatedBackend(EngineBackend(...))` instead. In
  `execute`, before any work, the gate raises Stage B's `RequestRefused`, which the controller
  records as `refused` (controller.py:405-408): not an attempt, not charged, and it stops the
  controller. Whatever goes wrong inside the gate leaves it as a refusal; any other exception
  would be recorded by Stage B as a charged failed attempt. No Stage B file and no policy code
  identity changes.
- **One block per process.** Stage B labels a session's setup as measured when its backend object
  has not served a block before. A new wrapper around a warm inner backend would look fresh, so
  `run_block_gated` refuses, before anything is written, an inner backend or engine `Session`
  that already served a block in this process.

## Admission formula

`AdmissionController.admit` (`admission.py`). With a balance reading `B` taken at `t0`:

```
age       = now - t0                                  (0 <= age <= max_balance_age)
horizon   = increment + backup_delay + shutdown_delay
need      = worker_rate * (age + horizon) * (1 + contingency)
held      = reservations of every unreleased lease of another worker that end after t0
reserves  = for every OTHER worker, the retention reserve of its latest lease (released and
            superseded leases included) whose retention window ends after t0
unleased  = sum over liabilities of no leased worker and not this worker:
            (rate * (age + horizon) + fixed_amount) * (1 + contingency)
available = B - held - reserves - unleased - retention_reserve
admit  iff  available >= need
```

`worker_rate` is the worker's GPU plus storage rate per hour; `retention_reserve` must be at
least the storage and destination rates over the policy's retention hours. The lease expires at
`now + increment`; the reservation runs to `now + horizon`, when the provider stops the worker
(`Provider.arm_shutdown`, armed before the lease is returned). Stopping Python does not stop
billing. Reservations are appended to one ledger under an exclusive file lock.

Each lease records its retention reserve and the end of its retention window (`now + horizon +
retention hours`). One reserve per worker is held, its latest lease's: a renewal replaces it and
does not add to it, and it stays held after the lease is released or superseded until the window
ends, because the volume still bills. A second worker therefore cannot spend the first worker's
reserve.

A liability that names a worker with an unreleased lease, or the worker being admitted, is not
charged again: the lease is assumed to cover everything that worker bills. This holds only if
the worker's rate card is complete; an extra volume or GPU of that worker that is not in its rate
card would be under-counted. The funded validation must check it.

A ledger row that cannot be read as a lease or a release (malformed, or of an older format)
refuses admission and dispatch; it is never an unhandled error.

Admission **refuses** when: the provider, a reading or the liability list is unavailable; the
balance is not an explicitly recognized `prepaid-credit-balance` (a pod billing total or a removed
spending cap is not a balance); a number is missing, negative or non-finite; currencies differ; a
reading is stale or future-dated; the provider's rates differ from the rates the plan was costed
with; the storage declaration fails; the shutdown cannot be armed; or the runway is insufficient.

`check_storage` requires: the provider confirms the source path is on persistent storage; the
destination is declared independent of the GPU account, funded, and retained long enough; it is
usable (a probe object written, read back, removed) and has the required free space; and it does
not lie inside the source. Retention and funding are declared inputs, not measurements.

## Restore and resume

`Vault.restore()` places every acknowledged unit and the latest snapshot of every append-only
file at its **recorded path** (or under `--mirror`, in the recorded layout). It never replaces a
file with different bytes and never rewrites a receipt. `verify.PathMap` relocation is used for
verification only; a continuation needs the recorded layout because the engine reads dependency
paths as recorded.

- **Engine.** `UnitRunner` keeps an attempt catalogue (`attempts.jsonl`, outside the run
  folders, copied off-pod before each attempt starts). On start it classifies every attempt
  without an outcome as sealed, failed or **lost**. A lost attempt keeps its start time, lease and
  rate, its cost is recorded as unknown (never zero), and its number is never reused. The sealed
  predecessor is reverified and the missing work gets the next attempt number.
- **Registry** (`jobs.claim_trajectory`, jobs.py:181). Only a fresh start claims a trajectory; a
  second fresh start is refused while an earlier claim's folder has no `error.txt`. A lost
  continuation is therefore simply rerun. A lost fresh start still holds its claim: the claim is
  re-appended from the catalogue if the restored snapshot predates it, and the rerun is refused
  until the attempt is declared lost with `declare_lost` (an operator-named administrative
  `error.txt` tombstone in the lost attempt's folder). The engine's next claim then lists it under
  `retry_after_failures`: the same seed, the same draw. No claim is ever cleared or edited.
- **Stage B.** The study tree is restored at its recorded root. An attempt that was in flight
  comes back as `started.json` alone; Stage B's own resume closes it as `interrupted` with its
  known lower bound and runs the next attempt number. Its cost stays in the Stage B accounting as a
  lower bound (no margin is formed for that block). With the real engine, `reconcile_claims` and
  `declare_lost_attempt` apply the registry rule above, and the gate refuses the retry until then
  instead of letting it burn charged attempts.

## Outcome-blind logs

The journal accepts only whitelisted keys (identifiers, paths, hashes, sizes, statuses, timings)
and short scalar values; anything else raises. Acknowledgements hold the same kinds of fields.
Failures are logged by error class, never by message. A Stage B vault must be created with
`reveal_paths=False`: Stage B folder names contain arm ids, and the final-operation names reveal
the chosen arms, so its logs name units by opaque id only. The stored manifests do hold paths
(a restore needs them); they are payload in the destination, not operator logs. Held-out payloads
are copied and hashed as opaque bytes and never parsed.

## What is guaranteed locally

Shown by the tests in `tests/` (CPU, fakes, a directory as the destination):

- an acknowledgement exists only after the stored bytes match and the restore check passes, with
  the stream checked for every run-one in the chain;
- partial and corrupt transfers, a file changing during the copy, a missing dependency or pinned
  input, a full destination (before and during the copy) and an unconfigured destination produce no
  acknowledgement;
- a crash before the acknowledgement leaves none; a crash after it changes nothing; duplicates are
  idempotent; a same-name, different-hash arrival fails with both kept;
- ambiguous paths are refused; a rewritten append-only file is refused; a restore never replaces a
  file;
- a sealed engine chain whose source was removed is restored byte-identical into the recorded
  layout, reverified with no path map and continued;
- a Stage B study killed mid-block is restored and resumed to completion with the lost attempt and
  its unknown cost kept; the same through the real `EngineBackend`, including a lost fresh start;
- no unit launches without the previous acknowledgement or without a valid lease;
- every listed admission input fails closed, two concurrent workers cannot both reserve the same
  runway, a second worker cannot spend the first worker's retention reserve (through renewal and
  release, until its window ends), and an unreadable ledger refuses;
- a dependency stored without its acknowledgement does not count; a crash between an
  acknowledgement and its pin is completed by the retry;
- a backend that already served a block in the process is refused; only a refusal leaves the
  Stage B gate; the safeguard's time shows up where the README says it does.

## What waits for the funded one-worker validation

None of the following is established by local tests:

1. an actual persistent mount, confirmed by the provider, at the recorded path;
2. an off-pod copy made **by the worker**, with the laptop disconnected, to a destination that is
   recoverable without the GPU account (a real `Destination` adapter);
3. a restore on a fresh provider host into the recorded layout;
4. a provider-side timed shutdown that actually stops billing (`Provider.arm_shutdown`);
5. real balance semantics: what the provider's number means, its currency, its delay, and whether
   liabilities and rates are reported as assumed (`Provider.read_balance`, `read_rates`,
   `list_liabilities`);
6. a restored continuation on CUDA that matches what an uninterrupted run would have produced.

Only after these may concurrency rise, and only within verified runway.

## Open decisions for the lead

1. **Tombstones.** Declaring a lost fresh start writes an administrative `error.txt` into the
   lost attempt's folder so that the engine's own retry rule applies. The alternatives are to
   treat such a unit as permanently unrunnable in that registry, or to amend the engine. It is an
   explicit, operator-named action and is never taken automatically.
2. **Stage B cost of the safeguard.** Every safeguard second inside a session is in the Stage B
   cost record and therefore in the policy costs, in three places:
   - *inside the attempt's own timer*: the gate check and the off-pod copy of `started.json` run
     at the top of `execute`, between the controller's start and end clock reads. That time is
     part of the attempt's measured seconds (operation time) and of the overrun comparison
     against its quote. It is small, but it is not controller time;
   - *in the controller seconds of the step that owns the operation*: the settle before an
     attempt's timer and in `verify`, where the copy and restore check of an operation's output
     run;
   - *in the session's start record*: what the session's first `sync` settles (only `study.json`
     when the study was settled beforehand).

   The alternative, a backend clock that pauses during administrative work, would keep all of it
   out of the costs but contradicts Stage B's statement that its timers tile the session.
3. **Strictness of the gate.** The copy and the restore check run synchronously on the worker, so
   a billed GPU idles while they run. An asynchronous copy would overlap the next unit and break
   "no next unit without the previous acknowledgement".

## Commands

Tests (CPU only, the pinned engine environment, caches disabled), from the project root:

```bash
PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -m pytest -q -rs -p no:cacheprovider --basetemp=<scratch>/pytest experiments/durability/tests experiments/safety_decision_policy/tests
```

Acknowledge a sealed chain from a relocated archive into a directory, then restore it elsewhere:

```bash
python -m experiments.durability ingest --destination DEST --namespace dev01 --scratch SCRATCH --journal JOURNAL --map /workspace/attribution-study-v2/calibration-001=ARCHIVE/calibration-001 --map /workspace/attribution-study-v2/prepared=PREPARED --map /workspace/attribution-study-v2/experiments=experiments --prepared /workspace/attribution-study-v2/prepared --code /workspace/attribution-study-v2/experiments --run /workspace/attribution-study-v2/calibration-001/UNIT-q-a1 --run /workspace/attribution-study-v2/calibration-001/UNIT-e1-a1
```

```bash
python -m experiments.durability restore --destination DEST --namespace dev01 --scratch SCRATCH --journal JOURNAL --mirror MIRROR
```

## Limits

- One namespace is one source volume written by one worker; two hosts must not share a namespace.
- Only run-one units are launched by `UnitRunner`. Other sealed kinds are acknowledged
  (`acknowledge_sealed_tree`, Stage B attempts) but not launched here.
- The reservation ledger is serialized by a file lock, so it must live where every worker's
  admission sees the same file. A shared service for several pods is part of the funded validation.
- Money is plain floating point; admission compares with a stated contingency, not to the cent.
- The restore check reads the copy back in full for every unit, and a chain's earlier folders
  again for each later unit. This is deliberate and costs time on a billed worker.
- A unit that seals just before the worker dies, with no time to copy it, is lost. The window is
  one unit's copy time, not a host's whole run.
- One gated block per process: a second block on the same inner backend or engine session is
  refused. The pre-block checks of `run_block_gated` run in the block's process, so their small
  time is in the session's start record.
- A reservation ledger written by an earlier format of this package (leases without their
  retention reserve) is refused as unreadable; start a new ledger.
