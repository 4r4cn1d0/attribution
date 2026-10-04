# Recovery safeguards before any cloud restart: procedure and limits

3 October 2026. Item 4 of `2026-10-03-local-work-plan.md`, built against the prerequisites of
`2026-10-02-runpod-credit-incident.md` and the binding constraints of the non-author recovery
review. Code: `experiments/durability/` (its README describes the modules and interfaces).

**What this is.** Administrative safeguards, implemented and tested locally on CPU with a
directory as the destination and fake provider answers. No provider, network, GPU, payment or
credit action was taken; no held-out data were read; the frozen engine and the Stage B package
are unchanged.

**What this is not.** It is not a restart authorization and not evidence about any cloud. The
provider, destination and shutdown defaults are deliberately unconfigured and refuse every call;
the real connectors added later on 3 October have made no request from this package, and the
stop timer added on 4 October has never run in a pod. The funded one-worker validation remains
required. No scientific result, held-out outcome or attribution benefit is
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

9. Continuing needs a renewed admission with a fresh balance reading, granted before the lease
   ends. Stopping the Python process does not stop billing: the pod is stopped by the timer that
   runs inside it, at the stop time that admission armed (the end of the reservation minus the
   timer's stated lateness, about two minutes). A renewal moves the stop time; a refused renewal
   leaves it in force. The GitHub watchdog stands behind the timer as a best-effort backup.

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
declaration, a shutdown that is not confirmed and a shutdown delay shorter than the shutdown's
stated lateness. A pod billing total or a removed
spending cap is not a balance. The formula is conservative: a lease's whole reservation is held
even though part may already be reflected in the balance. The margins (maximum reading age,
delays, contingency, retention hours) are inputs to be set before the funded validation; no
values are fixed here.

## What the local tests establish

260 tests in `experiments/durability/tests/`, run with the pinned engine environment on CPU:

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
  existing pod, so the adapter cannot confirm a provider-side shutdown by itself. The user chose
  to close the gap with an external watchdog (next section). Without it admission still refuses.

Confirmations the user must record before a live admission can succeed: what `clientBalance`
means and in which currency, and the storage prices.

## The stop timer in the pod (added 4 October; the primary shutdown)

**Why.** The watchdog below was deployed on 3 October. In its first 16 hours GitHub ran 3 of its
33 scheduled slots, with up to 5 h 46 min between scans
(`.ai/inputs/study-v2-20261002/durability-watchdog-deployment.json`). Most leases would have been
refused for want of a recent scan, and a granted lease could have been stopped hours late. On
4 October the user chose a timer inside the pod as the primary stop; the watchdog became a
best-effort backup.

**What it is.** A small process (`experiments/durability/pod_timer/pod_timer.py`, standard library
only) that the pod's start command starts before anything else and keeps running. It holds a
deadline and, when the deadline comes, asks RunPod to stop the pod it runs in, using the command
line tool and the pod-scoped key that RunPod puts in every pod. It is **built and tested locally
only; it has never run in a pod.**

**How it gets its deadline.**

1. At creation the operator gives the pod a *cap*: a stop time in its environment. A pod whose
   laptop dies right after creating it stops at the cap.
2. Admission arms a lease by writing a record on the pod's network volume. The timer
   acknowledges it and from then on its heartbeat names that lease and its stop time. Admission
   grants the lease only after reading both, within 30 seconds; otherwise it withdraws the record
   and refuses.
3. The most recently issued valid authority governs, so a renewal moves the stop time. A damaged
   record is ignored and the previous deadline stays. No valid deadline, or a deadline already
   past, means stop at once.

**What keeps it alive.** The start command's shell runs a supervisor, which restarts the timer
within a second if it dies and also starts the image's own start script (SSH, Jupyter). The timer
is not a child of the worker. If the supervisor itself dies, or the timer cannot be unpacked, the
shell asks RunPod to stop the pod. After a container restart the start command runs again and the
timer re-arms from the network volume. The deadline is enforced from memory, so a network volume
that stops answering cannot prevent the stop.

**What covers what.**

| Failure | Covered by |
|---|---|
| worker dies; laptop off | the timer |
| timer crashes | its supervisor |
| supervisor dies; timer cannot start | the start command stops the pod at once |
| container restarts | the timer, re-armed from the volume |
| RunPod ignores the pod's own stop request | the GitHub backup, whenever it next scans |
| GitHub's schedule silent | not needed by the timer |
| container never starts | nothing of ours: the operator checks for the heartbeat after creation |

**Lateness.** The timer asks for the stop within about a second of the stop time. What remains is
RunPod's own latency, not documented: 120 seconds are reserved for it (configured lateness and
minimum shutdown delay), an assumption until measured. No other admission input changed.

**The weak point, and how admission handles it.** RunPod's documentation shows a pod stopping
itself (`runpodctl pod stop $RUNPOD_POD_ID`, with a pod-scoped key preinstalled) but does not say
what that key may do. The timer's acknowledgement proves a deadline is being enforced, not that
RunPod will act on the request. Admission therefore refuses until the configuration records one
observed self-stop. The funded validation's first step produces it with no lease: a pod with a
ten-minute cap, the laptop disconnected, seen to stop.

**Keys.** The timer uses only what RunPod puts in the pod. Admission reads the account with a
separate Read Only key under its own variable name, because inside a pod `RUNPOD_API_KEY` is
RunPod's pod-scoped key. The key that the backup stops with exists only as a GitHub Actions
secret.

**Stage B.** The timer adds no time inside Stage B sessions: arming is part of admission, before
a block's process starts. Open decision 4 stays deferred.

**What the local tests show (61 of the 260).** The deployed script with a manual clock (the cap,
leases, renewal, damaged records, a past deadline, retries, a failing mount, no deletion, no
secret in records) and as real processes (a killed timer restarted, a dead worker, a restarted
"container", the start command run by bash, including its own stop when the script is damaged);
and admission refusing without the timer's acknowledgement and succeeding while the watchdog
refuses or is unreachable. They show nothing about RunPod.

**First real observation (4 October, by the lead).** A pod created with a 15-minute cap and no
lease stopped itself at the cap, to the second: RunPod's last status change reads 12:27:21 UTC
against a cap of 12:27:21.065, an outside poll saw it running at 12:27:02 and exited at 12:27:23,
no stop was sent from outside, and the account's spend fell to the storage rate. The records are
in `.ai/inputs/study-v2-20261002/pod-timer-cap-check-20261004/`, including the
`stop-confirmation.json` that admission requires. This is one observation on one pod type; how
long a stop takes under load, and what the pod-scoped key may do beyond it, remain open.

## Running a host on a pod (added 4 October)

**Status.** Built and tested locally only. On 4 October, at the user's instruction to start, the
lead launched the frozen development matrix the 2 October way (over SSH, the same `calibrate`
arguments, output root `dev-matrix-002`) with two additions: the stop timer as a hard cap on
every pod and a laptop-side pull of each sealed unit. The plan both sessions agreed is
`.ai/inputs/study-v2-20261002/matrix-launch-plan-20261004.md`. The pieces below are therefore not
on that run's critical path. They are for retries of its lost or failed hosts and units, for the
next stages, and for later runs.

**The pieces.**

- A **worker** on the pod runs one host's jobs of the frozen plan unit by unit. Before a unit: an
  admission lease long enough for it, which arms the stop timer. After the unit seals: its
  acknowledgement off the pod, before the next unit. At the end it asks the timer to stop the pod.
  It starts by checking the same identities the 2 October runner checked and by restoring what
  the host has already acknowledged.
- A **job runner** in the pod, started by the timer's supervisor, fetches the bundles from the
  backup repository, checks their hashes, runs the bootstrap and then the worker, and asks the
  timer to stop the pod if anything fails. Nobody logs in; the laptop can be off.
- A **launcher** on the operator's machine uploads the bundles, creates the network volume and
  the pod, refuses a duplicate or a price above a stated limit, and records every request. It
  cannot terminate or delete anything.

**Scientific identity.** The worker calls the engine's own unit function with the job fields the
engine's calibration loop builds. A test compares its sealed folders with the engine's
`calibrate` for the same job, leaf by leaf. Against `calibrate` at the same paths it differs only
where two `calibrate` runs differ from each other: seconds, timestamps and the hashes of the
files holding them. Against the plan's command, which names paths relatively, eight path fields
are additionally spelled absolutely, each resolving to the same place. Every saved state and
every evaluation output is byte-identical. The engine, the recipe, the prepared data and the plan
were not changed.

**The GPU.** The matrix stays on the A100-SXM4-80GB in Secure Cloud. All 13 hosts of 2 October
were that type at a quoted $1.59 an hour; no unit ever ran on the PCIe variant, so the receipts
allow no cost-per-unit comparison between A100 variants, and the fixture was only established on
SXM4. The calibration receipts give about 63 minutes and $1.67 for one arm and seed (q, e1, e3)
under the calibration recipe; the frozen recipe's longer evaluations are not in them.

**Taking over a host that ran without the safeguards.** A tree written by plain `calibrate` has
no attempt catalogue and names paths relatively. The worker adopts it: sealed units are
acknowledged as they are; an attempt that neither sealed nor failed is kept as lost with an
unknown cost and rerun as the next attempt; a lost fresh start waits for the operator's
tombstone.

**The one-pod validation and the matrix runbook** are in the package README ("Running a host on a
pod"), with the exact commands and the table of which measured numbers set which matrix settings.
The validation starts from a host of the 4 October run rather than repeating the matrix.

**Limits.** The worker launches calibration units only; the next stages are other unit kinds.
Each host keeps its own reservation ledger, so one host's admission counts the other pods as
liabilities over its own horizon rather than their full reservations. The bootstrap step is the
2 October script and cannot be repeated on a volume where it half-ran.

## The shutdown watchdog (added 3 October; since 4 October a best-effort backup)

As a backup the watchdog's stop time is the end of the reservation itself, it promises no
punctuality, and admission never depends on it. The description below is of the watchdog as
built. Its script was changed on 4 October so that a backup arm is acknowledged without a recent
scheduled scan; deploying that needs the Workflows-capable push that adding a pod to its
allow-list needs anyway.

**What it is.** A scheduled GitHub Actions workflow in the backup repository that stops a leased
pod through RunPod's API when its reservation runs out. It needs no server and no laptop, costs
nothing within GitHub's included minutes, and is independent of the worker and of the GPU
account's balance. Source: `experiments/durability/watchdog/` (the script and the workflow, to be
deployed by the lead) and `experiments/durability/shutdown_watchdog.py` (the worker's side). It
is **built and tested against local fakes only; it is not deployed and has stopped no real pod.**

**How a lease gets its stop.**

1. Admission computes the end of the reservation. The worker publishes an arm record in the
   backup repository (worker, pod, stop time, acknowledgement deadline) and sends one event.
2. The event starts a short workflow run. It acknowledges only a well-formed arm for a pod on its
   allow-list that RunPod reports as running, and only while the scheduled scan is demonstrably
   running. Otherwise it records a refusal.
3. Admission grants the lease only after reading an acknowledgement that names this arm, pod and
   stop time. No acknowledgement within about 11 minutes, a refusal or a mismatch means no lease,
   and the arm is withdrawn.
4. A scan every 30 minutes stops each allow-listed pod at its first scan after the stop time of
   that pod's latest acknowledged arm, confirms the stop and records it. A failed stop turns the
   run red and is retried at the next scan.

The watchdog stops and never terminates or deletes; it acts only on a pod that the allow-list and
an acknowledged arm both name; a stop is recorded once. All records are create-only release
assets, which is the audit trail.

**The stated lateness.** The stop time is the end of the reservation minus a configured lateness,
and the admission policy's shutdown delay must be at least that lateness. Recommended: **5400
seconds** for both (three 30-minute scan intervals: one scheduled run dropped by GitHub, half an
hour of scheduling delay, the confirmed stop). The delay is reserved runway, not spending. The
figure is an assumption about GitHub's scheduler, which GitHub does not guarantee, until the
funded validation measures it.

**Actions minutes (sources in the package README).** GitHub Free includes 2,000 minutes a month
for private repositories, per account, and bills each job rounded up to a minute. 48 scans a day
are 1,440 minutes in a 30-day month and 1,488 in a 31-day month; each admission or renewal is one
more. That leaves 512 to 560 minutes: about 16 leases or renewals a day. A full month of 2-hour
leases on one worker totals about 1,860 minutes; leases under about 90 minutes held all month
would not fit. If the account's quota runs out and no payment method is set, GitHub blocks the
jobs: new leases are then refused, but a lease already granted would not be stopped.

**Permissions.** The workflow's token may write release assets and read workflow runs, nothing
else. The worker's backup token needs no new permission. The RunPod key that can stop a pod is
only an Actions secret; the worker never holds it, and the worker's own RunPod key should be
read-only. Secrets appear in no log or record.

**What protects the RunPod key.** The backup token can push commits to the backup repository, so
the script and the pod allow-list there could be rewritten by a faulty or compromised worker. It
cannot change the workflow file, which needs a separate GitHub permission the token must not
have. The workflow therefore pins the SHA-256 of the script and of the allow-list, checks both in
a step that holds no secret, and only then runs the script, in a mode where a file placed beside
it cannot replace a standard module. Consequence for operation: adding a pod means editing the
allow-list and its pinned hash in the workflow, in one commit, with a credential that may change
workflows. What this does not give: records are not signed, so a compromised backup token could
still forge an acknowledgement, withdraw an arm or make the check fail; it could prevent a stop,
but not obtain the key.

**Before the secret exists.** With an empty allow-list a scan needs no RunPod key and succeeds,
so the workflow can be deployed and its schedule observed first. With a pod on the list and no
key, every scan fails visibly.

**What the user does** (exact clicks in the package README): create a RunPod API key for the
watchdog; store it as the repository secret `RUNPOD_API_KEY` of `4r4cn1d0/attribution-backups`;
make sure Actions may run there; nothing changes on the backup token. To see that it is armed:
the Actions tab shows a green "watchdog" run every half hour, and `python -m
experiments.durability check-watchdog` prints the governing stop time and the run that
acknowledged it.

**What the local tests show (68 of the 260).** The deployed script itself, run against fake
GitHub and RunPod services with a manual clock: no stop before the stop time and exactly one
after it; renewal and supersession; malformed, unacknowledged, withdrawn and foreign-pod arms
governing nothing; nothing deleted; `armed` only after a matching acknowledgement; admission
succeeding end to end with every input confirmed and refusing when any one of thirteen inputs is
withdrawn; no secret in any log, record or error; the workflow's pins equal to the shipped
files, and its verification step, run locally, rejecting a changed or missing file. They show
nothing about GitHub's scheduler or RunPod's stop.

## What waits for the funded one-worker validation

These are not established by anything above. Before it, and free of charge, the two `check-`
commands should be run once against the real services (they need only the tokens):

1. an actual persistent mount at the recorded path, confirmed by the provider;
2. an off-pod copy made by the worker while the laptop is disconnected, to a destination
   recoverable without the GPU account;
3. a restore on a fresh provider host;
4. the stop timer, in this order: (a) the cap-only check: a pod with a ten-minute cap, SSH
   working, the laptop then disconnected, seen from outside to stop at the cap with the account's
   spend falling to the storage rates (this is the observed self-stop admission requires);
   (b) a real stop at a lease's deadline **with the laptop disconnected and the worker killed**,
   and its measured lateness against the configured 120 s; (c) a re-arm after a restart of the
   pod and after a kill of the timer, with the stop still at the same time; (d) what the
   pod-scoped key may do, tried against a second pod; (e) the backup's record whenever GitHub
   next scans;
5. real balance semantics: what the number is, its currency and delay, and how liabilities and
   rates are reported;
6. a restored continuation on CUDA matching an uninterrupted run.

Concurrency may rise only after these, and only within verified runway. A laptop-driven copy is
an interim prototype and does not satisfy the restart prerequisites.

## Limits

- A unit that seals immediately before the worker dies, with no time for its copy, is still
  lost. The exposure is one unit's copy time instead of a host's whole run.
- The copy and restore check run on the worker between units, so a billed GPU idles while they
  run. This is the price of a strict gate.
- One gated block per process: a second block on the same backend or engine session is refused.
- The stop timer depends on RunPod acting on a pod's own stop request, which only an observed
  stop shows. A pod whose container never starts has no timer. The timer protects against death,
  not against a worker that tampers with it. Work that ends early leaves the pod running until
  the stop time unless the operator stops it. A stopped pod still bills its storage.
- The backup watchdog acts only when GitHub runs its schedule, which it did for 3 of 33 slots
  after deployment, and depends on the account's Actions minutes.
- The reservation ledger is serialized by a file lock; several pods need one shared place for it.
- Destination retention, funding and independence are declared, not measured.
- The lost attempts of 2 October are not reconstructed by this work: their records and costs
  remain as the incident record states.

## Open decisions

None is open. Decided by the user on 3 October 2026, the third amended on 4 October 2026:

1. **Tombstones are allowed.** A lost fresh start is retried only after an explicit tombstone, an
   administrative `error.txt` in the lost attempt's folder, which uses the engine's own retry rule
   without changing the engine. It is named by the operator and never written automatically.
2. **The synchronous gate's idle GPU time is accepted for the one-pod validation**, and is to be
   measured there.
3. **Shutdown: a timer inside the pod, with the GitHub Actions watchdog as a best-effort backup.**
   The user's choice of 4 October 2026. It amends the decision of 3 October, which made the
   watchdog the required shutdown, because the deployed watchdog's schedule ran 3 of 33 slots in
   16 hours.
4. **Stage B safeguard time in the policy costs: deferred**, to be settled before any held-out
   Stage B run under the gate, either by a Stage B amendment that gives the safeguard's time an
   uncharged owner or by a measurement in the funded validation showing that it is negligible.
   The facts until then: every safeguard second inside a session is in the cost record and
   therefore in the policy costs. The gate check and the copy of `started.json` run inside the
   attempt's own timer, so they are part of the operation's measured seconds and of its overrun
   comparison. The copy and restore check of an operation's output run before the next timer
   starts and right after the attempt, so they are controller seconds of the step that owns the
   operation. The first settle of a session is in its start record. Excluding any of it would
   need a paused clock, which contradicts Stage B's cost contract as it stands.
