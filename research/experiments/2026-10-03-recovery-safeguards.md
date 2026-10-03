# Recovery safeguards before any cloud restart: procedure and limits

3 October 2026. Item 4 of `2026-10-03-local-work-plan.md`, built against the prerequisites of
`2026-10-02-runpod-credit-incident.md` and the binding constraints of the non-author recovery
review. Code: `experiments/durability/` (its README describes the modules and interfaces).

**What this is.** Administrative safeguards, implemented and tested locally on CPU with a
directory as the destination and fake provider answers. No provider, network, GPU, payment or
credit action was taken; no held-out data were read; the frozen engine and the Stage B package
are unchanged.

**What this is not.** It is not a restart authorization and not evidence about any cloud. The
provider and remote-destination adapters are deliberately unconfigured and refuse every call, so
admission cannot succeed on a real deployment yet. The funded one-worker validation (last
section) remains required. No scientific result, held-out outcome or attribution benefit is
involved.

## What went wrong and what now prevents it

| 2 October failure | Safeguard |
|---|---|
| Retrieval waited for a whole host to finish | Every unit is copied and acknowledged as soon as it seals; the next unit on that worker cannot start before the acknowledgement |
| Container disks were ephemeral | Admission requires a provider-confirmed persistent source and a separate destination declared independent of the GPU account |
| No balance or runway check; 13 pods at about $20.67/hour | Admission needs a fresh, recognized prepaid balance, all liabilities, the rates, the planned increment, backup and shutdown delays, a retention reserve and a contingency; reservations are serialized across workers |
| Status snapshots were all that remained | Only a restore-verified copy counts. A status file, a sender receipt or an incomplete copy is not an acknowledgement |
| Lost attempts could have been silently replaced | An attempt catalogue leaves the worker before each attempt starts; lost attempts keep their number and an unknown (never zero) cost; registry claims are never cleared |

## Operating procedure

**Before any work on a worker**

1. Declare storage: the durable source path and the destination, with its independence from the
   GPU account, its retention and who funds it. The provider must confirm the source is
   persistent; the destination must pass a write/read probe and have the required free space.
2. Request admission for a planned increment of work. Admission grants a lease or refuses.
3. Acknowledge the pinned inputs once: the prepared-data folder and the engine source.

**For every unit (an engine run; a Stage B operation attempt)**

4. Gate: every earlier local attempt is acknowledged in the destination, and the lease covers the
   unit's planned seconds. Otherwise nothing starts.
5. Catalogue the attempt off-pod (engine: a catalogue line; Stage B: `started.json`), then run.
6. When the unit seals (`COMPLETE.json`; for Stage B the after-call `receipt.json`): copy it to
   the destination, hash the stored bytes, restore it with its pinned inputs and its whole
   dependency chain into a fresh tree in the recorded layout, and run the engine's verification
   there. Every folder must be complete and every run-one must have its training stream checked.
7. Only then write the acknowledgement. Snapshot the trajectory registry and the catalogue.
8. A failed unit is kept as a failure record and copied; a retry is a new attempt folder with
   the same seed, which is the same scientific draw.

**When the lease nears its end**

9. Continuing needs a renewed admission with a fresh balance reading. At the end of the
   reservation the provider stops the worker; stopping the Python process does not stop billing.

**After a worker is lost**

10. Restore the vault to the recorded paths on an authorized host (mount or place the files at
    the same paths; receipts are never rewritten).
11. Reverify the sealed predecessor in place, with no path map.
12. Start the runner again. It classifies attempts without an outcome as lost and gives the
    missing work the next attempt number.
13. If the lost attempt was a fresh start, it still holds its trajectory claim. The operator
    must declare it lost by name (a tombstone); the engine then registers the retry as the same
    draw, listing the lost start. Without that declaration the rerun is refused.

## Admission formula

With a balance `B` read at `t0`, admission at `now`, and hourly rates:

```
age       = now - t0
horizon   = increment + backup_delay + shutdown_delay
need      = worker_rate * (age + horizon) * (1 + contingency)
held      = reservations of other workers' unreleased leases that end after t0
reserves  = for every other worker, the retention reserve of its latest lease (released or
            superseded leases included) whose retention window ends after t0
unleased  = sum over liabilities of no leased worker:
            (rate * (age + horizon) + fixed_amount) * (1 + contingency)
available = B - held - reserves - unleased - retention_reserve
admit  iff  available >= need
```

Each lease records its retention reserve and the end of its retention window (the end of its
reservation plus the retention hours). One reserve per worker is held: a renewal replaces it, and
it stays held after a release until the window ends, because the volume still bills. A second
worker cannot spend the first worker's reserve. A liability that names a leased worker is not
charged again, on the assumption that the worker's rate card covers everything it bills; the
funded validation must check that assumption. An unreadable reservation ledger refuses.

The retention reserve must cover the storage and destination rates over the stated retention
hours. Missing, stale, future-dated, negative, non-finite, unrecognized or ambiguous inputs
refuse, as do a currency mismatch, rates that differ from the costed plan, an unconfirmed storage
declaration and a shutdown the provider does not confirm. A pod billing total or a removed
spending cap is not a balance. The formula is conservative: a lease's whole reservation is held
even though part may already be reflected in the balance. The margins (maximum reading age,
delays, contingency, retention hours) are inputs to be set before the funded validation; no
values are fixed here.

## What the local tests establish

93 tests in `experiments/durability/tests/`, run with the pinned engine environment on CPU:

- **Engine chain (decisive).** A sealed chain q, e1 was acknowledged; the worker was terminated
  during e3 and its volume removed; the vault was restored to the same absolute paths; every
  sealed file, receipts included, was byte-identical; e1 verified in place with no path map and
  its stream checked; e3 then ran as attempt 2, with attempt 1 kept in the catalogue as lost with
  an unknown cost.
- **Stage B (decisive).** A synthetic study terminated mid-block was restored and resumed to
  completion. Every restored record was byte-identical. The lost attempt was closed by Stage B as
  interrupted with an unknown time, the retry took the next attempt number, and the block's cost
  stayed a lower bound with no margin formed. The same path was run through the real engine
  backend on CPU fixtures, including a lost fresh start that was restored, declared lost and
  retried as the same draw.
- **Gate (decisive).** With no lease, an expired lease, or a sealed unit whose copy could not
  reach the destination, no next unit launched.
- **Failure modes.** Partial and corrupt transfers, a file changing during the copy, a missing
  dependency or pinned input, duplicates, a crash before and after the acknowledgement, a full
  destination, ambiguous paths, a same-name different-hash collision (both kept), stale and
  missing balances, changed rates and two workers admitted concurrently.
- **Review findings (3 October), each with a regression test.** A crash between an
  acknowledgement and its pin record is completed by the retry. A second worker cannot spend the
  first worker's retention reserve. A backend that already served a block in the process is
  refused, so unmeasured setup is never labelled measured. A dependency stored without its own
  acknowledgement does not count. Only a refusal can leave the Stage B gate.

**One-off check on preserved evidence** (not a test; outputs in the implementer's scratch folder).
The preserved dev01 chain `1101-g-1f744bb3364064e2` (q, e1, e3) from
`tmp/study-v2-20261002/retrieved-calibration/`, with `prepared-v1` and the current engine source
(its code identity equals the one those runs pinned), went through the full path into a scratch
directory: 5 units acknowledged, with 1, 2 and 3 engine folders verified and the stream checked
for each. A restore into a mirror placed 100 files (77,774,438 bytes); the 63 run files were
byte-identical to the preserved ones; the engine's own `verify` passed on the restored e3 with the
stream checked; the 75 source files were unchanged before and after.

## Real connectors (added 3 October)

The user chose GitHub release assets as the free off-pod destination (private repository
`4r4cn1d0/attribution-backups`) and RunPod is the provider. Both connectors now exist in
`experiments/durability` (`github_destination.py`, `runpod_provider.py`), built only from explicit
configuration; the defaults still refuse. **Neither has made a request to its real service**: no
token was present when they were built. What follows rests on the services' documentation, read on
3 October 2026 (sources in the package README), and on fake services on 127.0.0.1.

- **GitHub destination.** One object is one release asset, named by the hash of its key, in one
  of 64 shard releases. A final object is created by a create-only upload, so an existing
  different object is a collision and is never replaced; hashes are computed on bytes downloaded
  from GitHub. The vault's whole acknowledgement protocol was rerun through this connector against
  the fake API and holds. Limits: files under 2 GiB, 1000 assets per release, GitHub's rate limits
  (possibly about ten 23-file units per hour for one token, unverified). A token that can upload
  can also delete: this protects against a lost worker and an empty GPU account, not against a
  leaked token. GitHub's immutable releases do not fit a layout that keeps adding assets.
- **RunPod provider.** Read-only: the pod and network-volume lists and one account query. The
  balance (`clientBalance`) is recognized only when the configuration records a named person's
  confirmation of its meaning and currency. Storage prices are configuration, because the API
  reports none. Persistence is confirmed only for a path under a network volume's mount. Anything
  missing or unknown refuses.
- **The shutdown gap.** RunPod documents no stop time that can be set on, or read back from, an
  existing pod. The adapter therefore never confirms a provider-side shutdown, and admission
  through it always refuses. Closing the gap needs either a creation-time stop that RunPod is
  shown to enforce, or an external always-on controller (for example a scheduled workflow in the
  backup repository holding the RunPod key as a secret). Neither is built.

Decisions the user must record before a live admission can succeed: what `clientBalance` means
and in which currency; the storage prices; and which shutdown option to build and validate.

## What waits for the funded one-worker validation

These are not established by anything above. Before it, and free of charge, the two `check-`
commands should be run once against the real services (they need only the tokens):

1. an actual persistent mount at the recorded path, confirmed by the provider;
2. an off-pod copy made by the worker while the laptop is disconnected, to a destination
   recoverable without the GPU account;
3. a restore on a fresh provider host;
4. a provider-side timed shutdown that stops billing;
5. real balance semantics: what the number is, its currency and delay, and how liabilities and
   rates are reported;
6. a restored continuation on CUDA matching an uninterrupted run.

Concurrency may rise only after these, and only within verified runway. A laptop-driven copy is
an interim prototype and does not satisfy the restart prerequisites.

## Limits and open decisions

- A unit that seals immediately before the worker dies, with no time for its copy, is still
  lost. The exposure is one unit's copy time instead of a host's whole run.
- The copy and restore check run on the worker between units, so a billed GPU idles while they
  run. This is the price of a strict gate.
- In Stage B every safeguard second inside a session is in the cost record and therefore in the
  policy costs. The gate check and the copy of `started.json` run inside the attempt's own timer,
  so they are part of the operation's measured seconds and of its overrun comparison. The copy and
  restore check of an operation's output run before the next timer starts and right after the
  attempt, so they are controller seconds of the step that owns the operation. The first settle
  of a session is in its start record. Excluding any of it would need a paused clock, which
  contradicts Stage B's cost contract. **Lead decision.**
- One gated block per process: a second block on the same backend or engine session is refused.
- A lost fresh start is retried only after an explicit tombstone, an administrative `error.txt`
  in the lost attempt's folder. This uses the engine's own retry rule without changing the
  engine. **Lead decision** whether to permit it or treat such units as unrunnable.
- The reservation ledger is serialized by a file lock; several pods need one shared place for it.
- Destination retention, funding and independence are declared, not measured.
- The lost attempts of 2 October are not reconstructed by this work: their records and costs
  remain as the incident record states.
