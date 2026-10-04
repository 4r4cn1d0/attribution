# Recovery safeguards (`experiments.durability`)

Administrative code only. It copies sealed evidence off the worker, proves the copy can be
restored, gates the next unit of work on that proof and on prepaid runway, and restores a lost
worker's evidence into the recorded layout so work can resume. It trains, scores and decides
nothing, and it changes no file of the frozen engine (`experiments/safety_selection`) or of Stage B
(`experiments/safety_decision_policy`).

**Status.** Implemented and tested locally on CPU with fakes (3 and 4 October 2026), including
the two real connectors (GitHub release assets as the off-pod destination, RunPod's API as the
provider; [real connectors](#real-connectors)) and two layers of shutdown: a stop timer that runs
inside the pod ([shutdown](#shutdown-the-stop-timer-in-the-pod)), which is required, and the
GitHub Actions watchdog ([the backup](#the-backup-the-github-actions-watchdog)), which is a
best-effort backup. The watchdog was deployed by the lead on 3 October; GitHub then ran 3 of its
33 scheduled slots in 16 hours, which is why it is no longer the primary stop. Nothing in this
package has made a request to RunPod or GitHub, and the timer has never run in a pod: every claim
about them rests on the services' documentation and on local fakes and processes. This does not
satisfy the restart prerequisites of the 2 October incident record by itself. The defaults stay
unconfigured and refuse: without a running, acknowledging timer whose self-stop has been observed
once, admission refuses. The funded one-worker validation is still required
([what waits](#what-waits-for-the-funded-one-worker-validation)).

Since 4 October there is also what runs a host under these safeguards: a pod-side worker, an
in-pod job runner and an operator-side launcher ([running a host on a pod](#running-a-host-on-a-pod)).
They too have run only locally. On 4 October the lead observed one real self-stop of a pod by the
timer (the cap-only check; the lead's record is
`.ai/inputs/study-v2-20261002/pod-timer-cap-check-20261004/`), and started the development matrix
the 2 October way over SSH with the timer as a hard cap, at the user's instruction; the worker
and launcher here are for retries of that run, for the next stages and for later runs.

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
| `transport.py` | stdlib `urllib` | the HTTPS client of the real connectors: token from the environment, sent only to the service, no credential on redirects, bounded retries |
| `github_destination.py` | stdlib | `GitHubReleaseDestination`: the `Destination` contract on release assets of a private repository |
| `runpod_provider.py` | stdlib | `RunPodProvider`: read-only answers from RunPod's API, closed wherever a meaning is not confirmed |
| `shutdown_timer.py` | stdlib | `PodTimer`: the worker's side of the stop timer, answers `armed` only after the timer's acknowledgement; `LayeredShutdown`: the timer required, the watchdog a best-effort backup; `settings`: the environment and start command for pod creation |
| `pod_timer/` | stdlib (self-contained; not imported; Python 3.8+) | the stop timer itself, `pod_timer.py`, which runs inside the pod |
| `shutdown_watchdog.py` | stdlib | `GitHubActionsWatchdog`: the worker's side of the GitHub watchdog, as the backup (or, as first built, the required shutdown) |
| `watchdog/` | stdlib (self-contained; not imported) | the watchdog itself, deployed in the backup repository: `watchdog.py`, the workflow `watchdog.yml`, the pod allow-list |
| `wiring.py` | stdlib | builds the real connectors from explicit configuration; the defaults stay unconfigured |
| `worker.py` | engine (torch) in its job processes | the pod-side worker: one host's jobs of the frozen plan through `UnitRunner`, with a lease and an acknowledgement for every unit |
| `pod_timer/pod_job.py` | stdlib (self-contained; not imported) | the in-pod job runner: fetches the bundles, runs the steps, asks the timer to stop on failure |
| `launcher.py` | stdlib | the operator-side launcher: one volume and one pod per host, bundles as release assets, every request recorded |
| `engine_units.py` | engine `runner` (torch) when it launches | `UnitRunner`: the administrative loop around `runner.run_one`; the attempt catalogue; lost attempts |
| `stage_b.py` | Stage B `common` | `GatedBackend` around a Stage B backend; `StudyBackup`; `run_block_gated` |
| `__main__.py` | stdlib | commands `ingest`, `restore`, `acks`, `check-destination`, `check-provider`, `check-watchdog`, `check-timer`, `pod-timer-settings`, `worker-report`, `pack-code` (nothing creates, starts, stops or deletes); `worker` (on the pod); `launch` (creates a volume and a pod; can stop the pod it created; never deletes) |

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
`now + increment`; the reservation runs to `now + horizon`, by when the worker has been stopped
(`Provider.arm_shutdown`, armed before the lease is returned). Stopping Python does not stop
billing. A shutdown that is not exact states its lateness (`Provider.shutdown_lateness_seconds`;
the watchdog's is configuration), and the policy's `shutdown_delay_seconds` must be at least that:
the stop is then asked for no earlier than the end of the lease plus the backup delay, and it is
complete, and funded, by the end of the reservation. Reservations are appended to one ledger under
an exclusive file lock.

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
with; the storage declaration fails; the shutdown cannot be armed; the policy's shutdown delay is
shorter than the shutdown's stated lateness; or the runway is insufficient.

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

## Real connectors

Both are built only from explicit configuration (`wiring.destination_from`, `wiring.provider_from`).
Without configuration the destination is `UnconfiguredDestination` and the provider is
`UnconfiguredProvider`; both refuse every call. Tokens are read from environment variables at
request time by `transport.Http`, sent as `Authorization: Bearer` to the service host only, never
forwarded on a redirect, and never written to a log, a record, `describe()`, a URL or an exception.

### GitHub release assets as the destination

`GitHubReleaseDestination("owner/repo", declared_free_bytes=...)`, or `--destination
github:owner/repo --declared-free-bytes N` on the command line. The user chose a private
repository, `4r4cn1d0/attribution-backups`.

How an object is stored:

- one object is one release asset, named by the SHA-256 of its key; the key is the asset's label,
  which is what listing by prefix reads (a label that does not hash to its name refuses the listing);
- a key goes to the release `<scheme>-<shard>` (default scheme `durability-v1`, 64 shards, so
  64,000 objects); a full shard raises `CapacityError`. Shards and scheme are fixed once used;
- `commit` and `put_new` rely on GitHub refusing an upload whose name exists: an identical object
  is reused, a different one is a `CollisionError`, and no final object is ever deleted here;
- `sha256` downloads the asset and hashes those bytes; `commit` publishes exactly the read-back
  bytes as a second, create-only upload and checks the size and digest GitHub reports;
- an asset that is not in the `uploaded` state is not an object; a leftover from a failed upload
  is deleted and the upload repeated once.

What GitHub documents and this relies on (checked 3 October 2026):

| Fact | Source |
|---|---|
| "Each file included in a release must be under 2 GiB"; "Up to 1000 release assets may be associated with a single release"; "no limit on the total size of a release, nor bandwidth usage" | [About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) |
| Upload: `POST https://uploads.github.com/repos/{owner}/{repo}/releases/{release_id}/assets?name=...&label=...`; an existing filename is an error (422) and the old asset must be deleted first; names with special characters are renamed; a 502 "may leave an empty asset with a state of starter" that "can be safely deleted"; assets have `state`, `size`, `label`, `digest`; binary download with `Accept: application/octet-stream` answers 200 or 302; listing is paginated (`per_page` up to 100) | [REST: release assets](https://docs.github.com/en/rest/releases/assets) |
| Release and asset endpoints are under the repository permission **Contents** (read to get and list, write to create, update and delete) | [Permissions for fine-grained tokens](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens) |
| 5,000 requests per hour per token; secondary limits of 900 points per minute (a GET is 1 point, a POST, PATCH or DELETE 5) and "no more than 80 content-generating requests per minute and no more than 500 content-generating requests per hour"; a limited request answers 403 or 429 with `retry-after` or `x-ratelimit-reset` | [REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) |
| Immutable releases: once published, "release assets cannot be modified or deleted" and the tag is locked; assets are attached while the release is a draft | [Immutable releases](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases) |

Not documented, so not relied on: what `PATCH` (rename) does when the new name already exists
(a rename would save the second upload of every file); the maximum length of a label; whether
asset uploads count as "content-generating" requests.

**Throughput.** Each file costs two uploads and one delete, each unit two more uploads (manifest,
acknowledgement). A sealed engine run of about 23 files is about 48 uploads. If uploads count
towards the 500 content-generating requests per hour, that is about ten such units per hour for
one token, which is enough for one worker and not for thirteen. The transport waits for a stated
rate-limit reset of up to 120 seconds, at most four times, and then fails: no acknowledgement,
and the gate starts nothing. Raising concurrency needs the live measurement first, and then
either the rename commit or one packed object per unit.

**Threat model.** A token that can upload can also delete: the Contents write permission covers
`DELETE` of assets and releases. This destination protects evidence against a lost worker and an
exhausted GPU account. It does not protect against a leaked or misused token, or against someone
with write access to the repository. Keep the token scoped to this one repository and off the
worker's disk.

**Immutable releases do not fit this layout.** An immutable release cannot receive assets after it
is published, and this connector adds assets to its shard releases for as long as the study runs.
They would fit a different layout (one draft release per unit, published when the unit is
acknowledged), which the per-object `Destination` contract cannot express, and even then a release
can still be deleted as a whole. Do not enable immutable releases on the backup repository.

**Token setup** (the user does this; nothing here creates a token):

1. GitHub, Settings, Developer settings, Personal access tokens, Fine-grained tokens, Generate new token.
2. Resource owner: `4r4cn1d0`. Repository access: Only select repositories, `attribution-backups`.
3. Repository permissions: **Contents: Read and write**. Metadata: Read-only is added by GitHub.
   Nothing else.
4. Set an expiry that covers the study.
5. Export it where the worker process runs, and nowhere on disk:

```bash
export ATTRIBUTION_BACKUP_GITHUB_TOKEN=...
```

Live check, once the variable is set (it writes two tiny objects into a `connector-test` release
and deletes its staging objects; the two final objects stay, as final objects always do):

```bash
python -m experiments.durability check-destination --destination github:4r4cn1d0/attribution-backups --declared-free-bytes 10000000000
```

### RunPod as the provider

`RunPodProvider(RunPodConfig(...))`, or `wiring.provider_from({"kind": "runpod", ...})`. The key
comes from the environment variable the configuration names (`key_env`; `RUNPOD_API_KEY` by
default, which is right on a laptop but **not inside a pod**, where RunPod sets that name to its
own pod-scoped key) and is sent as a header, never in a URL. The adapter sends `GET
https://rest.runpod.io/v1/pods`, `GET https://rest.runpod.io/v1/networkvolumes` and one fixed
GraphQL query (`myself { clientBalance currentSpendPerHr spendLimit }`) to
`https://api.runpod.io/graphql`. It has no call that creates, starts, stops, updates or deletes
anything; the stop at the end of a reservation is asked for by the pod's stop timer, and behind
it by the watchdog.

| Question | Answer and what it rests on |
|---|---|
| Balance | `clientBalance`. The [GraphQL reference](https://graphql-spec.runpod.io/) lists it as a `Float` with no description; [`runpodctl user`](https://docs.runpod.io/runpodctl/reference/runpodctl-user) calls it the "current credit balance". Neither states a currency or how fresh it is. The reading is **recognized only when the configuration records a human confirmation** (who, when, currency, statement). Otherwise it is marked unrecognized and admission refuses. Its timestamp is the moment of the API read. |
| Rates | The worker pod's `costPerHr`, "the cost in Runpod credits per hour of running a Pod" ([REST: pods](https://docs.runpod.io/api-reference/pods/GET/pods)). The API reports no storage rate, so storage prices per GB-month are configuration, taken from the [storage page](https://docs.runpod.io/pods/storage/types) and confirmed by a named person. The pod's container disk and volume are added to the storage rate; whether `costPerHr` already includes them is not documented, so this can only over-state. |
| Liabilities | Every RUNNING pod (cost plus disks), every EXITED pod (its volume at the stopped price), every network volume. If the account's `currentSpendPerHr` exceeds what these explain, something else bills and the call refuses. A liability of a configured worker's pod or attached volume carries that worker's name; admission then relies on the worker's lease to cover it, which holds only if its rate card is complete. |
| Persistence | Confirmed only for a path under `volumeMountPath` of the RUNNING local pod that has a network volume attached, which the account's volume list also shows. "Network volume ... retained independently"; a container disk is "lost on stop/restart"; a pod volume "is deleted when the Pod is terminated" ([storage types](https://docs.runpod.io/pods/storage/types)). |
| Shutdown | RunPod offers nothing to arm on an existing pod. Confirmed only through the acknowledgement of the stop timer in the pod, whose records must be on storage RunPod confirms as persistent: see [shutdown](#shutdown-the-stop-timer-in-the-pod). Without a configured shutdown, `NotConfigured`. |

A field that is missing, of another type or outside the documented values raises
`ProviderError`. Admission treats whatever a provider raises as a refusal.

Configuration (JSON for `check-provider`, `check-timer` and `check-watchdog`; the three
confirmations are what the user must record; without the `shutdown` section no shutdown can be
armed, and without its `stop_confirmation` the timer refuses to arm):

```json
{
  "kind": "runpod",
  "worker_pods": {"worker-1": "<pod id>"},
  "local_pod_id": "<pod id of this worker>",
  "destination_per_hour": 0.0,
  "key_env": "RUNPOD_READ_API_KEY",
  "shutdown": {"kind": "pod-timer", "state_dir": "/workspace/.pod-timer", "lateness_seconds": 120,
               "stop_confirmation": {"confirmed_by": "<name>", "confirmed_utc": "2026-10-05T00:00:00+00:00", "statement": "<which pod stopped itself at its cap, and how that was seen>"},
               "backup": {"kind": "github-actions-watchdog", "repository": "4r4cn1d0/attribution-backups"}},
  "balance_confirmation": {"confirmed_by": "<name>", "confirmed_utc": "2026-10-04T00:00:00+00:00", "currency": "USD", "statement": "<what was checked and where>"},
  "storage_prices": {"network_volume_per_gb_month": 0.07, "pod_volume_running_per_gb_month": 0.10, "pod_volume_stopped_per_gb_month": 0.20, "container_disk_per_gb_month": 0.10, "hours_per_month": 720, "source": "docs.runpod.io/pods/storage/types, read <date>", "confirmed_by": "<name>", "confirmed_utc": "2026-10-04T00:00:00+00:00"}
}
```

Read-only check, once the key variable is set (it prints shapes and counts, never the balance or
pod ids):

```bash
python -m experiments.durability check-provider --config provider.json --worker worker-1 --path /workspace/attribution-study-v2
```

### Shutdown: the stop timer in the pod

A lease promises that the worker stops billing at the end of its reservation even if every
process of ours is dead and the laptop is off. RunPod gives this code nothing to arm: its GraphQL
reference lists `stopAfter` and `terminateAfter` only among the inputs that create a pod, without
a description; neither REST API version documents a stop time; and no documented call sets one on
an existing pod.

On 3 October the user chose an external watchdog on GitHub Actions. Deployed, its schedule ran 3
of 33 slots in the first 16 hours, with up to 5 h 46 min between scans
(`.ai/inputs/study-v2-20261002/durability-watchdog-deployment.json`): most leases would have been
refused, and a granted one could have been stopped hours late. On 4 October the user chose a
**timer inside the pod** as the primary stop. The watchdog stays as a best-effort backup.

**What runs where**

| | where | started by | holds | can do |
|---|---|---|---|---|
| the stop timer (`pod_timer/pod_timer.py`) | inside the pod, under its own supervisor | the pod's start command, before the image's own start script | the pod-scoped key RunPod puts in every pod (`RUNPOD_API_KEY`) and the preinstalled `runpodctl` | ask RunPod to stop **this** pod |
| the worker's side (`shutdown_timer.PodTimer`) | the worker, inside admission | admission | nothing | write a lease record on the mount, read the timer's acknowledgement |
| the backup (`watchdog/`, `shutdown_watchdog`) | GitHub Actions, backup repository | GitHub's schedule | the user's RunPod key as an Actions secret | stop an allow-listed pod, whenever GitHub next scans |

The process tree in the pod is: the start command's shell; under it the supervisor; under that,
side by side, the timer and the image's start script (`/start.sh`, which starts SSH and Jupyter).
The worker is started later through SSH, so the timer is never its child and does not die with it.

**The start command.** `python -m experiments.durability pod-timer-settings --state-dir
/workspace/.pod-timer --cap-minutes 45 --out settings.json` writes what RunPod must be given when
the pod is created: environment variables and a start command (as the array the API takes and as
the one line the console takes). A network volume is empty on first boot, so the timer script
travels in the pod's environment (`POD_TIMER_B64_00`, gzip and base64, about 11,000 characters;
`--chunk-chars` splits it over several variables if RunPod limits one). The start command unpacks
it to the container disk, compares its SHA-256 with the value written in the command, and runs
`python3 -I pod_timer.py supervise -- /start.sh`. If the script is missing, cut short or changed,
if `python3` is absent, or if the supervisor ever exits, the command falls through to a loop that
asks RunPod to stop the pod (`runpodctl pod stop`, `runpodctl stop pod`, then the REST call): a
pod that cannot run its timer stops itself.

**The deadline.** Two kinds of authority, each with the time it was issued; the most recently
issued valid one governs:

- the **cap**, in the pod's environment (`POD_TIMER_CAP_ISSUED_UTC`, `POD_TIMER_CAP_STOP_UTC`),
  fixed by the operator when the pod is created or started. A pod whose laptop died right after
  creating it still stops at the cap;
- **lease records** that admission writes on the persistent mount, create-only
  (`<state>/leases/<id>.json`).

A record that is malformed, truncated, too large, for another pod, dated in the future or more
than 48 hours long is ignored and whatever governed before keeps governing. A withdrawn record
(`voids/<id>.json`) never governs. With no valid authority at all, and whenever the governing stop
time is already past (for example at a container start after it), the pod is stopped at once. To
use a stopped pod again, the operator starts it with a new cap; it then outranks the old leases.

**The arm protocol** (`PodTimer.arm`, called by admission through `RunPodProvider.arm_shutdown`):

1. RunPod must confirm that the timer's folder is on a network volume (`confirm_persistent`), so
   that the deadline survives a restart of the container.
2. The configuration must record that a pod was once seen to stop itself through this timer
   (`stop_confirmation`). See "what an acknowledgement cannot show" below.
3. The timer's heartbeat on the mount (`heartbeat.json`, rewritten every 2 seconds) must be at
   most 15 seconds old, name this pod, come from a timer its supervisor still owns, not be
   stopping already, and report a way to ask for the stop.
4. The worker writes the lease record with `stop_at_utc = end of reservation - lateness_seconds`.
5. Within 30 seconds it must read the timer's acknowledgement (`acks/<id>.json`: this lease, this
   pod, this stop time) **and** a heartbeat written after the record that names this lease as
   governing with that stop time. Only then is the answer `armed`.
6. Otherwise the record is withdrawn with a void and admission grants no lease.
7. The backup is then attempted, bounded (120 seconds by default), and its outcome recorded in
   `backups/<lease>.json` and returned. Its failure never refuses admission.

A renewal writes a new record with a later stop time; the timer obeys the latest. At the stop time
the timer asks RunPod to stop the pod, by each method in turn until one takes effect: `runpodctl
pod stop <id>`, `runpodctl stop pod <id>` (the older spelling), `POST /v1/pods/<id>/stop`, and the
GraphQL `podStop` mutation, the last two with the pod-scoped key. It never terminates, deletes,
resets or restarts anything. A stop that takes effect ends the timer, which is the confirmation
from inside; while it is still alive it repeats the attempts every 15 seconds and records each in
`stop-attempts.jsonl`. `starts.jsonl` gets one line per start of a timer, the audit of re-arming.

The deadline is held in memory and enforced by a thread that never touches the mount; reading
records and writing heartbeats is another thread's work. A network volume that stops answering
silences the heartbeat (new leases are then refused) but cannot keep the pod from being stopped.

**Failure table**

| What fails | What stops the pod | When |
|---|---|---|
| the worker's processes die | the timer | at the lease's stop time |
| the laptop is off, or never comes back | the timer | at the lease's stop time; at the cap if no lease was ever granted |
| the timer process is killed or crashes | its supervisor restarts it within about a second; it re-arms from the mount | at the same stop time |
| the supervisor dies | the start command's shell, which then asks for the stop itself | at once (the pod stops early: fail closed) |
| the container restarts | the start command runs again; the timer re-arms from the mount | at the same stop time, or at once if it has passed |
| the network volume stops answering | the timer, from the deadline in memory | at the same stop time; no new lease meanwhile |
| the timer cannot be unpacked or started | the start command's shell | at once |
| RunPod does not act on the pod's own stop request | the backup watchdog, if its arm was acknowledged | at GitHub's first scan after the end of the reservation, possibly hours late |
| GitHub's schedule goes silent | nothing is lost: the timer does not depend on it | |
| the container never starts (image cannot be pulled, start command never runs) | **nothing of ours**: no timer exists, no lease, and so no backup arm | the operator must check that the heartbeat appears after creating a pod and stop the pod by hand if it does not; RunPod itself stops pods at a zero balance |
| both the timer's stop and the backup fail | nothing of ours | RunPod's stop at a zero balance |

**The lateness, and the recommended shutdown delay.** The timer asks for the stop within about a
second of `stop_at_utc`. `lateness_seconds` is therefore RunPod's own time from the request to
the stop, which is not documented. The recommended setting is **`lateness_seconds = 120` and a
policy `shutdown_delay_seconds` of at least 120**, an assumption until the funded validation
measures it (`seconds_after_stop_time` in `stop-attempts.jsonl`, and the pod's status from
outside). Admission still refuses a policy whose shutdown delay is below the configured lateness.
No other admission input changed.

**What an acknowledgement cannot show.** It shows that a supervised timer is running in this pod
and is enforcing this stop time. It cannot show that RunPod will act on a stop the pod asks for
itself: the documentation says only that every pod "comes preinstalled with `runpodctl` and a
Pod-scoped API key" and shows `runpodctl pod stop $RUNPOD_POD_ID`, with nothing on what that key
may do. So the timer refuses to arm until the configuration records an observed self-stop
(`stop_confirmation`: who, when, what was seen). The first step of the funded validation produces
it without any lease: create a pod with a ten-minute cap, disconnect, and see it stop.

**Keys: which does what, and where it lives**

| key | where it lives | what it is used for | what it could do |
|---|---|---|---|
| pod-scoped key (`RUNPOD_API_KEY` inside the pod) | put there by RunPod, in every pod | the timer's stop request for its own pod | not documented; the worker cannot be kept from reading it, because RunPod puts it in the pod's environment |
| read-only account key (`RUNPOD_READ_API_KEY`, named by `key_env`) | a RunPod secret referenced in the pod's environment; created by the user as "Read Only" | admission's reads: balance, pods, volumes | read the account; change nothing |
| backup token (`ATTRIBUTION_BACKUP_GITHUB_TOKEN`) | a RunPod secret referenced in the pod's environment | off-pod copies; the backup's arm records and event | write to the backup repository; not its workflow |
| the user's RunPod key for the watchdog | GitHub Actions secret only | the backup's stop | whatever level the user gave it; never on the pod |

Nothing this package adds to the pod can stop or modify another pod. Whether the pod-scoped key
could is RunPod's design and is not documented; the validation should try it once against a second
pod.

**Does the timer add time inside Stage B sessions?** No. Arming happens in admission, before a
block's process starts; the timer is a separate process that wakes every second or two and does a
few file operations. Stage B's timers are untouched and its open decision 4 stays deferred. The
backup's bounded wait (up to about two and a half minutes) is also inside admission.

**Facts checked in RunPod's documentation on 4 October 2026**

- Every pod "comes preinstalled with `runpodctl` and a Pod-scoped API key"
  ([runpodctl overview](https://docs.runpod.io/runpodctl/overview)); `RUNPOD_API_KEY` is listed as
  "Pod-scoped API key" and `RUNPOD_POD_ID` as the pod's identifier
  ([environment variables](https://docs.runpod.io/pods/templates/environment-variables)).
- "Stop a Pod": `runpodctl pod stop $RUNPOD_POD_ID`, with "Schedule a stop (e.g., after 2
  hours): `sleep 2h; runpodctl pod stop $RUNPOD_POD_ID &`", and the REST call `POST
  https://rest.runpod.io/v1/pods/$RUNPOD_POD_ID/stop` ([manage pods](https://docs.runpod.io/pods/manage-pods);
  [runpodctl pod](https://docs.runpod.io/runpodctl/reference/runpodctl-pod)). The GraphQL
  mutation is `podStop(input: {podId: ...})`, answering `desiredStatus: EXITED`
  ([GraphQL: manage pods](https://docs.runpod.io/sdks/graphql/manage-pods)).
- "Stopping a Pod releases the GPU"; a stopped pod is still charged for its volume disk, and a
  network volume bills independently; "Pods are billed by the second for compute and storage"
  ([manage pods](https://docs.runpod.io/pods/manage-pods), [pricing](https://docs.runpod.io/pods/pricing)).
- With a network volume, "your `/workspace` data is preserved whether you stop or terminate the
  Pod"; a container disk is "lost on stop/restart" ([storage types](https://docs.runpod.io/pods/storage/types)).
- The container start command "overrides the default CMD instruction in your Docker container",
  given as `bash -c '...'` or as JSON with `cmd` and `entrypoint`; the documented example is
  `bash -c 'mkdir /workspace && /start.sh'`. The base image's `/start.sh` "handles everything
  automatically" (Jupyter and SSH), and a custom command is told to call it
  ([manage templates](https://docs.runpod.io/pods/templates/manage-templates),
  [custom template](https://docs.runpod.io/pods/templates/create-custom-template)). The API fields
  are `dockerStartCmd` and `dockerEntrypoint` ([create a pod](https://docs.runpod.io/api-reference/pods/POST/pods)).
- "Updating environment variables restarts your Pod, clearing all data outside your volume mount
  path"; secrets are referenced as `{{ RUNPOD_SECRET_name }}`
  ([environment variables](https://docs.runpod.io/pods/templates/environment-variables)).
- When the balance reaches $0 RunPod stops all pods; those with a network volume keep their data
  ([billing](https://docs.runpod.io/accounts-billing/billing)).

**Not found in the documentation, so not relied on (each is a validation item)**

- What the pod-scoped key may do: stop only its own pod, or more; whether the REST and GraphQL
  calls accept it. (`runpodctl` from inside the pod is the documented path.)
- Whether the `runpodctl` in the user's image is new enough for `pod stop`; the timer also tries
  the older `stop pod`.
- Whether RunPod restarts a container whose start command exits. The design does not depend on
  it: the start command never exits by itself, and its last act is to ask for a stop.
- Any size limit on an environment variable or on the start command. The script is about 11,000
  characters packed; `--chunk-chars` exists in case that is too long for one variable.
- How long a stop takes from the request, and what the pod's status reads meanwhile.
- That the user's image has `/start.sh`, `python3` (3.8 or later), `bash`, `base64`, `gunzip` and
  `sha256sum`. If `/start.sh` is missing the timer still runs, without SSH.
- Whether a process started through SSH sees the pod's environment variables (the worker needs
  `RUNPOD_READ_API_KEY`, the backup token and `RUNPOD_POD_ID`).
- Whether `stopAfter` or `terminateAfter` at creation are enforced by RunPod. If they are,
  setting one at creation would cover the one row of the table that nothing of ours covers.

**Steps for the user**

1. RunPod console, Settings, API Keys: create a **Read Only** key for admission. Store it as a
   RunPod secret (Secrets page), for example `read_key`. Store the backup token as a secret too.
2. Create the network volume first, then the pod on it, with:
   - volume mount path `/workspace`;
   - every variable from `settings.json` (`env`), plus
     `RUNPOD_READ_API_KEY={{ RUNPOD_SECRET_read_key }}` and
     `ATTRIBUTION_BACKUP_GITHUB_TOKEN={{ RUNPOD_SECRET_<name> }}`;
   - the container start command from `settings.json` (`console_start_command`).

   Do **not** set `RUNPOD_API_KEY` yourself: RunPod sets it, and the timer needs RunPod's value.
3. Within a few minutes of creating the pod, connect and run `cat
   /workspace/.pod-timer/heartbeat.json`: it must exist, be seconds old, and say `"supervised":
   true`. No heartbeat means no timer: stop the pod by hand.
4. The cap is a real deadline: the pod stops when it runs out unless a lease was granted. Choose
   it for the time needed to reach the first admission.
5. To use a stopped pod again: run `pod-timer-settings` again, replace the two
   `POD_TIMER_CAP_*` values in the pod's environment (which restarts it), then start it.
6. After the first observed self-stop, record it in the provider configuration
   (`stop_confirmation`).

**Steps for the lead**

1. Generate `settings.json` shortly before creating the pod: the cap counts from that moment.
2. The first funded step is the cap-only check (below). Only after it can `stop_confirmation` be
   written and admission succeed.
3. The watchdog script changed (a backup arm is acknowledged without a recent scheduled scan), so
   its pin in `watchdog.yml` changed. The deployed copy keeps working as it is, and its
   acknowledgements still count as a backup, but it will refuse most backup arms for want of a
   recent scan. Deploying the new `watchdog.py` and `watchdog.yml` needs the same
   Workflows-capable push as adding the pod to `watchdog/pods.json`, which is needed in any case
   before the backup can act on a pod.

**What the timer does not do**

- It cannot stop a pod whose container never starts, and it cannot make RunPod act on its
  request. The backup and the failure table say what remains.
- It protects against death, not malice: worker and timer share the pod and the mount, and a
  worker that rewrote the records or killed the start command's shell could defeat or trigger it.
- It ignores ordinary termination signals so that a careless `pkill` does not remove it; RunPod's
  own stop of the container therefore takes the runtime's grace period (seconds).
- Work that finishes early leaves the pod running until the stop time unless someone stops it.

### The backup: the GitHub Actions watchdog

The watchdog below was built on 3 October as the required shutdown and is deployed in
`4r4cn1d0/attribution-backups`. Since 4 October it is a **best-effort backup** behind the pod's
timer: `LayeredShutdown` arms it after the timer, with `role: backup`. As a backup its stop time
is the end of the reservation itself (so it can only act after the timer should have), it
promises no punctuality, its acknowledgement needs no recent scheduled scan, and admission never
depends on it. When a renewal's backup arm cannot be made, every earlier arm of the pod is
withdrawn, so that the watchdog does not stop a pod whose lease was renewed. The description that
follows is of the watchdog as built; the lateness rules in it apply only if it is configured as
the required shutdown, which GitHub's schedule does not support in practice.

**What runs where**

| | where | what it holds | what it can do |
|---|---|---|---|
| the watchdog (`watchdog/watchdog.py`, `watchdog/watchdog.yml`) | GitHub Actions, backup repository | the RunPod key as the Actions secret `RUNPOD_API_KEY`; the run's own `GITHUB_TOKEN` | read one allow-listed pod, **stop** it, write records |
| the worker's side (`shutdown_watchdog.py`) | the worker, inside admission | the backup token it already has | publish an arm record, send one event, read the acknowledgement |

**The protocol.** Records are release assets of the backup repository, one release per kind and
month, every one create-only (GitHub refuses a second asset of the same name):

```
watchdog-arms-YYYY-MM    arm-<id>.json     the worker: worker, pod, stop_at_utc, ack_by_utc
                         void-<id>.json    the worker: withdraws an arm it got no lease from
watchdog-acks-YYYY-MM    ack-<id>.json     the watchdog: this run will stop this pod at stop_at_utc
                         refusal-<id>.json the watchdog: why it will not (final for that arm)
watchdog-stops-YYYY-MM   stop-<id>.json    the watchdog: the final outcome of the stop
                         stop-attempt-<id>-<run>.json   a stop that was not confirmed
```

1. Admission computes the end of the reservation and asks the provider to arm a stop that is
   complete by then. The worker's side publishes the arm with
   `stop_at_utc = end of reservation - lateness_seconds` and sends a `repository_dispatch` event
   naming it.
2. That event starts one short workflow run. It acknowledges only if: the arm is well formed; it
   names a worker and pod of the allow-list (`watchdog/pods.json`); it is inside its
   acknowledgement window (10 minutes by default); RunPod, asked with the Actions secret, reports
   that pod as `RUNNING`; and a **scheduled** scan of the workflow ran within the last 75
   minutes. Otherwise it writes a refusal, and a refusal is final.
3. The worker's side answers `armed` only after it has read an acknowledgement that names this
   arm, worker, pod and stop time, a workflow run, a recent scheduled scan, and a scan interval
   that the configured lateness covers twice. Anything else, including silence until the window
   ends, raises; the arm is withdrawn with a void record; admission grants no lease.
4. Every 30 minutes the scheduled scan finds, for each allow-listed pod, its **governing** arm:
   the latest one that is acknowledged and not withdrawn. At its first scan at or after
   `stop_at_utc` it sends `POST https://rest.runpod.io/v1/pods/{id}/stop`, confirms with a `GET`
   that the pod is no longer running and records the outcome. A stop that is not confirmed fails
   the run (it shows red in the Actions tab) and is tried again at the next scan.

The watchdog **stops** a pod; it never terminates or deletes one, and the script contains no
`DELETE` request for either service. It never stops a pod that no acknowledged, valid arm names,
and nothing outside the allow-list is ever read. A stop is recorded once per arm: a second scan
finds the outcome and does nothing. A renewed lease publishes a later arm, which governs from its
acknowledgement on, so the earlier stop time lapses; a renewal that is refused, unanswered or
withdrawn leaves the earlier stop in force. Malformed arms, arms without an acknowledgement and
arms for other pods govern nothing and suppress nothing.

**The lateness, and the recommended shutdown delay.** GitHub runs a schedule at best every 5
minutes, can delay it under load and may drop a queued run
([events that trigger workflows: schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
With a scan every 30 minutes the stop begins up to 30 minutes after `stop_at_utc`, 60 if one
scheduled run is dropped, plus whatever delay GitHub adds and the stop call itself. The
recommended setting is **`lateness_seconds = 5400` and a policy `shutdown_delay_seconds` of at
least 5400** (three scan intervals: one dropped run, half an hour of delay, the confirmed stop).
Admission refuses a policy whose shutdown delay is below the configured lateness, and the worker's
side refuses a lateness below two scan intervals. The delay is reserved runway, charged at the
worker's rate with the contingency; it is spent only if the stop really is that late. 5400 is an
assumption about GitHub's scheduler: nothing enforces it, and the funded validation must measure
the real lateness (`seconds_after_stop_time` in each stop record).

**Actions minutes.** GitHub Free includes 2,000 Actions minutes a month for private repositories,
counted per account, and rounds every job up to a whole minute
([GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)).
A scan is one job of a few seconds, so:

| | runs | billed minutes |
|---|---|---|
| scheduled scans, 2 an hour | 48 a day | 1,440 in a 30-day month, 1,488 in a 31-day month |
| each admission, renewal or refused arm | 1 | 1 |
| what is left of 2,000 | | 512 to 560 a month, about 16 arms a day |

A month of continuous work on one worker with 2-hour leases is 12 arms a day: 372 minutes, 1,860
in total. Leases shorter than about 90 minutes, held all month, would not fit; the one-pod
validation needs a handful of arms. Three cautions. The quota is shared with every other private
repository of the account. When it is used up and no payment method is set, GitHub blocks further
jobs; the scans then stop, new arms are refused (no recent scheduled scan), and a lease already
granted would not be stopped. And the arithmetic assumes every run finishes within a minute,
which the Actions tab shows after the first day. The optional `WATCHDOG_TAIL_SECONDS` (0 in the
workflow) makes a scan wait inside the run for a stop time that close; it removes most of the
lateness but every waited minute is billed, also when a renewal arrives in the end.

Rejected: a scan every 5 minutes (8,640 minutes a month); one sleeping run per lease (it bills
the whole lease and a job ends after 6 hours,
[Actions limits](https://docs.github.com/en/actions/reference/limits)); enabling the schedule
only while a lease exists (the worker's token would need "Actions: write", and a scan that
disables it can race an arm that enables it); `workflow_dispatch` from the worker (it also needs
"Actions: write"; `repository_dispatch` needs only "Contents: write",
[permissions reference](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens)).

**Least privilege**

- The workflow's `permissions:` block is `contents: write` (read arms, write acknowledgements and
  outcomes as release assets) and `actions: read` (see when the scheduled scan last ran). Nothing
  else is granted to its `GITHUB_TOKEN`.
- **The workflow file is the trusted part, and it pins what it runs.** The backup token's
  "Contents: write" also allows pushing commits, so a faulty or compromised worker could rewrite
  `watchdog/watchdog.py` or `watchdog/pods.json`. It cannot change the workflow: that needs the
  "Workflows" permission. The workflow therefore carries the SHA-256 of both files and checks
  them in a step that has no secret in its environment and executes nothing from the repository;
  a changed or missing file ends the job there, before the RunPod key is given to anything. The
  script then runs as `python3 -I`, so a module placed next to it (a `json.py`, say) cannot take
  the place of the standard library, which the hash of the script alone would not prevent. The
  one action used, GitHub's `actions/checkout`, is pinned to a full commit and keeps no
  credentials (`persist-credentials: false`).
- The backup token (`ATTRIBUTION_BACKUP_GITHUB_TOKEN`) needs **no new permission**: release
  assets and `POST /repos/{owner}/{repo}/dispatches` are both under "Contents: write". It cannot
  read workflow runs and does not try.
- The RunPod key that can stop a pod exists only as the Actions secret. The worker never holds
  it. The worker's own `RUNPOD_API_KEY` (admission only reads) should be a separate **Read Only**
  key. RunPod's key levels are "All", "Restricted" and "Read Only"
  ([API keys](https://docs.runpod.io/get-started/api-keys)); the documentation does not say which
  Restricted setting permits a stop, so the watchdog's key is "Restricted" with write access to
  Pods if the console offers that, and otherwise "All". The acknowledgement proves only that the
  key can *read* the pod; that it can *stop* one is shown by the first real stop.
- Secrets reach the script through the step's environment, go only into the `Authorization`
  header of their own service, are not forwarded on a redirect, and are never printed; the event
  payload is validated by a pattern before it is used and never reaches a shell line.
- Records are not signed. Whoever can write release assets in the backup repository can write a
  false acknowledgement or withdraw an arm, and whoever can push there can make the pinned check
  fail, which turns every run red and stops nothing. The pins protect the RunPod key; they do
  not make the stop safe from a compromised backup token. The watchdog protects against a dead
  worker, a dead laptop and an exhausted attention span. (Whether GitHub lets a token without the
  "Workflows" permission delete a workflow file was not checked.)

**Steps for the lead (deployment; nothing here was done by this package)**

1. Put `watchdog/watchdog.py`, `watchdog/pods.json` (a byte-for-byte copy of
   `pods.example.json`) and `.github/workflows/watchdog.yml` on the default branch of
   `4r4cn1d0/attribution-backups` (`watchdog/README.md` lists the paths; the pinned hashes are in the workflow itself).
   Pushing a workflow file needs a credential with the "Workflows" permission; the backup token
   must not have it. The files must arrive unchanged: the workflow refuses a script or an
   allow-list that differs from its pins by one byte (a changed line ending is enough).
2. This can be done before the user has set the secret. With the empty allow-list a scan needs no
   RunPod key and is green; that is how the schedule is observed for a day without a pod.
3. **Adding or changing a pod** (the pod id is known only once the pod exists): edit
   `watchdog/pods.json` to `{"workers": {"worker-1": "<pod id>"}}`, run `sha256sum
   watchdog/watchdog.py watchdog/pods.json` (`shasum -a 256` on macOS), replace the hash on the
   matching `pin` line of the workflow, and push both files in **one commit** with the credential
   that has the "Workflows" permission. Between two commits every run would fail at the check.
   The same goes for any change to the script. From then on the secret must be set: a scan with
   a pod on the list and no key fails.
4. The checkout action is pinned to commit `3d3c42e5aac5ba805825da76410c181273ba90b1`, which the
   lead verified on 3 October 2026 through the GitHub API as the tag `v7.0.1`, the latest release
   of `actions/checkout`. This package made no GitHub request and did not check it.
5. Add the `shutdown` section to the provider configuration (above) and use an admission policy
   with `shutdown_delay_seconds >= 5400`.
6. Admit only after a scheduled run has appeared in the Actions tab: a manual run does not count
   as the schedule running.

**Steps for the user**

1. RunPod console, Settings, API Keys: create a key for the watchdog (see "Least privilege") and
   copy it; it is shown once.
2. GitHub, `4r4cn1d0/attribution-backups`, Settings, Secrets and variables, Actions, "New
   repository secret": name `RUNPOD_API_KEY`, value that key. It must be there before a pod is
   put on the allow-list; until then the scans run without it.
3. Same repository, Settings, Actions, General: Actions must be allowed to run, including
   GitHub's own `actions/checkout`. The workflow-permissions default can stay read-only; the
   workflow asks for what it needs.
4. Nothing changes on the backup token. In particular it must not be given the "Workflows"
   permission: that the worker cannot change the workflow is what protects the RunPod key.
5. Check that the watchdog is running: the Actions tab shows a "watchdog" run every half hour,
   green. Check that a lease is armed:

   ```bash
   python -m experiments.durability check-watchdog --config provider.json --worker worker-1
   ```

   prints the governing arm, its stop time and the workflow run that acknowledged it (`"armed":
   true`), or the recorded stop. The same records are visible under Releases
   (`watchdog-acks-YYYY-MM`, `watchdog-stops-YYYY-MM`).
6. Account settings, Billing: watch the Actions minutes. The watchdog alone uses about 1,500 a
   month.

**What the watchdog does not do**

- It is a backstop, not a scheduler. Work that finishes early leaves the pod running until the
  stop time unless the operator stops it. (RunPod documents `runpodctl pod stop $RUNPOD_POD_ID`
  from inside a pod, [manage pods](https://docs.runpod.io/pods/manage-pods); that dies with the
  pod's processes, so it is no substitute, and it is not used here.)
- One stop per arm. A pod started again by hand after its stop is not watched until a new lease
  arms it.
- A stop leaves storage billing: "You'll still be charged for volume disk storage while stopped",
  and a network volume bills independently of any pod. The retention reserve covers that.
- If the worker can neither read an acknowledgement nor write the void (GitHub unreachable from
  the worker at that moment), an arm may be acknowledged that no lease stands behind. The error
  says so; the later stop time then governs until the operator withdraws it or a new lease arms.
- A pod RunPod reports as not found is recorded as gone. A key replaced by another account's
  would look the same.
- A release holds at most 1,000 assets; a month of arms stays far below that at the lease lengths
  the minutes allow, and a full release makes the arm fail, which refuses admission.

## Running a host on a pod

Three pieces take one host of a frozen plan from the operator's desk to sealed, acknowledged
units, with no inbound connection to the pod:

| piece | runs | what it does |
|---|---|---|
| `launch` (`launcher.py`) | on the operator's machine | uploads the bundles, creates the network volume and the pod with the stop timer and the job runner, records every request |
| the job runner (`pod_timer/pod_job.py`) | in the pod, under the timer's supervisor | fetches and checks the bundles, runs the bootstrap and then the worker, asks the timer to stop the pod if anything fails |
| `worker` (`worker.py`) | in the pod, in the engine's environment | runs the host's jobs unit by unit: lease, run, acknowledgement; finishes by asking the timer to stop the pod |

### The worker

`python -m experiments.durability worker --config worker.json`, with the study root as working
directory. It is the 2 October runner (`run_dev_matrix.py`) with the calibration loop taken out of
the engine and run through `UnitRunner`.

**Start.** It checks what that runner asserted: the engine's code identity, the recipe's hash and
the prepared-data manifest hash equal the plan's, and the bootstrap recorded the exact two-step
fixture on this host (`BOOTSTRAP-VERIFIED.json`). Then it restores everything this host's
namespace has acknowledged in the destination to the recorded paths.

**Run.** Each job of the host, in plan order, in its own process with a fresh engine session,
exactly as `calibrate` was invoked once per job. Per job: attempts found in the tree without a
catalogue line are adopted (see below), lost attempts classified, the tombstones the operator
named in the configuration written (only those), and then the units
`<seed>-<arm>-<checkpoint>` in the recipe's order. Before a unit that has to run: an admission
lease for `unit_seconds × lease_slack + acknowledge_seconds`, which arms the stop timer; a keeper
thread renews it if the unit outlasts it. After the seal: the acknowledgement, before the next
unit. A sealed unit of the same science is reused.

**Finish.** A numbered outcome record (`worker-outcome-NNN.json`), the lease released, and the
timer asked to stop the pod in `finish_after_seconds`. On a refusal or failure the record says
so and the timer is asked to stop the pod too (`stop_on_failure`). Nothing is deleted.

Configuration (no secret in it; keys and tokens are named by environment variable):

```json
{
  "host": "dev05",
  "root": "/workspace/attribution-study-v2",
  "plan": "dev-matrix-plan.json",
  "out_root": "dev-matrix-002",
  "unit_seconds": {"q": 900, "e1": 1500, "e3": 3000},
  "lease_slack": 1.5,
  "acknowledge_seconds": 600,
  "destination": {"spec": "github:4r4cn1d0/attribution-backups", "declared_free_bytes": 10000000000},
  "provider": {"kind": "runpod", "key_env": "RUNPOD_READ_API_KEY", "destination_per_hour": 0.0,
               "balance_confirmation": {"...": "as recorded"}, "storage_prices": {"...": "as recorded"},
               "shutdown": {"kind": "pod-timer", "state_dir": "/workspace/.pod-timer", "lateness_seconds": 120,
                            "stop_confirmation": {"...": "from the cap-only check"},
                            "backup": {"kind": "github-actions-watchdog", "repository": "4r4cn1d0/attribution-backups"}}},
  "policy": {"max_balance_age_seconds": 120, "max_rate_age_seconds": 3600, "backup_delay_seconds": 600,
             "shutdown_delay_seconds": 120, "contingency_fraction": 0.25, "retention_hours": 72},
  "planned_rates": {"gpu_per_hour": 1.59, "storage_per_hour": 0.0, "destination_per_hour": 0.0, "currency": "USD"},
  "storage": {"required_bytes": 2000000000, "destination_independent_of_gpu_account": true,
              "destination_retention_days": 90, "destination_funding": "<who pays for the repository>",
              "required_retention_days": 30},
  "retention_reserve": 1.0,
  "tombstones": []
}
```

`worker_pods` and `local_pod_id` are filled in from `RUNPOD_POD_ID` on the pod. `planned_rates`
must equal what RunPod reports for the pod, or admission refuses: `storage_per_hour` is the
network volume's size times its price (the configuration above is a shape, not the numbers).
Each host has its own namespace, catalogue and reservation ledger on its own volume. Admission on
one pod therefore sees the other pods as account liabilities (their hourly rates over its own
horizon), not their reservations: with equal hosts that is the same total, and it is what limits
how many hosts the balance admits at once.

**Scientific identity of the worker.** The job dictionaries are the ones `calibrate` builds and
the engine function called is the same `run_one`. A test runs the engine's `calibrate` twice, then
the worker, on the same job at the same paths, and compares every file of every sealed folder leaf
by leaf:

- against `calibrate` given the same absolute paths, the worker differs **only in fields in which
  two `calibrate` runs differ from each other**: seconds and timestamps (`train_seconds`,
  `seconds`, `start_s`, `end_s`, `elapsed_s`, `*_utc`), and the hashes of the files that contain
  them (`files/...`, `complete_sha256`, `state_sha256`);
- against the plan's own command, which passes relative paths, it differs additionally in how
  eight path fields are spelled, each resolving to the same location (`job.json` `resume_from`;
  `assets.json` `loaded_in`; `dependencies.json` `path`; `COMPLETE.json` `resumed_from`;
  `records.jsonl` `loaded_in`, `done_in`, `from_run`), and in the hashes of `job.json` and
  `assets.json`. The engine itself compares these paths resolved, and the vault needs them
  absolute, so that a restore lands where the receipts say;
- every saved state (`*.safetensors`) and every evaluation output is byte-identical in all three;
- the registry holds the same claim, differing in its time (and, against the relative command, in
  the spelling of `run_dir`).

Any other difference fails the test. The engine was not changed.

**A tree made by plain `calibrate`** (a host that ran the 2 October way, pulled to the laptop and
put into the vault with `ingest`, or still on its volume) has no catalogue and spells paths
relative to the study root. `UnitRunner.adopt` catalogues what it holds for the planned units:
sealed and failed attempts as they are; an attempt that neither sealed nor failed, or that the
registry claims but whose folder is gone, as lost with an unknown start and cost. The worker then
continues as after any loss: a lost continuation is rerun as the next attempt; a lost fresh start
waits for the operator's tombstone. The worker must run with the study root as its working
directory (it changes to it), because the engine resolves those relative paths from there.

`worker-report --admin-dir DIR --timer-dir DIR` prints what the records show: per unit the run
time, the copy and the restore check; the admission time; the hourly rate; the share of time the
safeguards took; the timer's lateness.

### The job runner and the bundles

The pod starts by itself: the start command runs the stop timer's supervisor, and the supervisor
runs `pod_job.py` (both travel in the pod's environment and are checked against hashes written in
the command). The job runner reads its description (`POD_JOB_SPEC_B64`), starts the image's own
start script in the background, fetches the bundles, writes the worker's configuration, and runs
the steps in order with a receipt each (`<root>/.pod-job/steps/<name>/NNN/`). A step marked `once`
that succeeded before on this volume is skipped, so a restarted pod goes straight to the worker.
A failing step ends the sequence and the timer is asked to stop the pod five minutes later.

**Why the bundles go through GitHub and not SSH.** The pod downloads them itself, as release
assets of the backup repository named by their SHA-256, with the backup token it holds anyway,
and refuses a bundle whose hash or size differs. No inbound connection is needed: the operator's
machine can be off, and a restart of the pod or a restore on a fresh pod repeats the same steps
unattended. The 2 October dispatch pushed bundles over SSH and started the work from the laptop;
when the connection ended, so did everything that depended on it. Rejected: SSH (needs the laptop
and an open port for every start); baking the bundles into a custom image (needs a registry, and
`prepared-v2` would sit in an image). The bundles are opaque to the launcher and the job runner:
they are hashed and unpacked, never read, so the held-out files inside `prepared-v2` are placed
as bytes exactly as the 2 October bundles placed them. An archive member that is a link or would
leave the study root refuses the whole archive.

### The launcher

`python -m experiments.durability launch --spec launch.json --record launch.jsonl` (add
`--dry-run` to see the request and contact nothing). In order: the description is checked; the
GPU's price is read and refused above `max_price_per_hour`; a pod of the same name that is not
terminated refuses; the bundles are uploaded (create-only, reused when present); the network
volume is found by name or created; the timer settings are generated (the cap counts from here)
and the pod is created; the price the pod reports is checked, and a dearer pod is stopped.

- Secrets are only ever references: a variable whose name looks like a key, token or password
  must be given under `secrets` as the *name* of a RunPod secret and reaches the pod as
  `{{ RUNPOD_SECRET_name }}`. `RUNPOD_API_KEY` cannot be set at all.
- The requests it can send: read prices, pods and volumes; create a volume; create a pod; stop a
  pod. There is no terminate and no delete in the code.
- `launch.jsonl` holds every request and answer without headers; the packed scripts appear as a
  hash and a length.

```json
{
  "name": "attribution-dev05", "host": "dev05",
  "image": "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404",
  "gpu_type": "NVIDIA A100-SXM4-80GB", "cloud": "SECURE", "max_price_per_hour": 1.70,
  "volume": {"name": "attribution-dev05", "data_center": "US-MD-1", "size_gb": 50, "create": true},
  "mount": "/workspace", "container_disk_gb": 60, "cap_minutes": 60,
  "secrets": {"ATTRIBUTION_BACKUP_GITHUB_TOKEN": "backup_token", "RUNPOD_READ_API_KEY": "read_key"},
  "env": {"HF_HOME": "/workspace/attribution-study-v2/hf-home"},
  "extra": {"minRAMPerGPU": 32, "minVCPUPerGPU": 8, "allowedCudaVersions": ["12.8"]},
  "bundle_repository": "4r4cn1d0/attribution-backups",
  "bundles": [{"path": "tmp/study-v2-20261002/worker-setup-v3.tar.gz", "extract": true, "sha256": "4a73f5c41c80cd340fe3e9340018b502af01d059cfeee499b4ce4b31d9fa8151"},
              {"path": "tmp/study-v2-20261002/dev-matrix-assets.tar.gz", "extract": true, "sha256": "349668b7c3cab7843e31e4bb48e6206c7b6c0f2a4b074467439d0e93b9990048"},
              {"path": "tmp/durability-code.tar.gz", "extract": true}],
  "job": {"root": "/workspace/attribution-study-v2",
          "files": {"worker-dev05.json": {"host": "dev05", "...": "the worker configuration above"}},
          "steps": [{"name": "bootstrap", "argv": ["bash", "worker_bootstrap_v3.sh"], "once": true},
                    {"name": "worker", "argv": ["venv/bin/python", "-m", "experiments.durability", "worker", "--config", "worker-dev05.json"],
                     "env": {"PYTHONPATH": "/workspace/attribution-study-v2", "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
                             "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false", "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4"}}]}
}
```

`HF_HOME` on the volume keeps the downloaded models across a restart of the container; without
it the bootstrap, which is not repeated, would have left them on the container disk. The two
existing bundles are the 2 October ones, by their recorded hashes; the third is made by
`pack-code`.

### The GPU

The matrix stays on **`NVIDIA A100-SXM4-80GB`, Secure Cloud**. The freeze requires "the same
actual two-step A100 fixture" on every host, and the bootstrap asserts that device name. What the
2 October receipts show, and do not:

- All 13 hosts were `NVIDIA A100-SXM4-80GB` at a quoted $1.59 an hour (`create-intent.json`,
  `owned-inventory-1714.json`). No unit was ever run on `NVIDIA A100 80GB PCIe`; the stock
  snapshot lists it at the same Secure price and as unavailable at the time. So the receipts allow
  **no** comparison of cost per completed unit between A100 variants, and the fixture was only
  ever established on SXM4. Choosing PCIe would save nothing by list price and would need the
  fixture shown again.
- Unit times exist for the calibration recipe only (`calibration-timing-stage-summary.json`):
  about 560 s for q, 1,035 s for e1 and 2,180 s for e3, so about 63 minutes and $1.67 for one
  arm and seed at $1.59 an hour. The frozen recipe evaluates with a 2,048-token ceiling and its
  unit times are not in the receipts; the 4 October run will show them.
- Within SXM4, one machine class was faster at the same price: host dev03 (117 GB, 24 vCPU)
  trained in 189, 569 and 1,518 s where the others took about 240, 720 and 1,950 s. The API
  offers no way to ask for a machine class, so this cannot be chosen; it is a reason not to treat
  the slower hosts' times as an upper bound.

Another GPU family would be a protocol amendment and is not in scope.

### One-pod validation: runbook

Starts from a host of the 4 October run (its `dev-matrix-002` tree pulled to the laptop under
`tmp/study-v2-20261004/retrieved/HOST/`). Before it: the backup token exists
(`ATTRIBUTION_BACKUP_GITHUB_TOKEN` on the laptop and as the RunPod secret `backup_token`), a Read
Only RunPod key is stored as the RunPod secret `read_key`, and the balance and storage-price
confirmations are recorded in the worker configuration.

1. Put the host's pulled tree into the vault, at the paths the pod recorded:

   ```bash
   python -m experiments.durability ingest --destination github:4r4cn1d0/attribution-backups --declared-free-bytes 10000000000 --namespace HOST --scratch tmp/durability-scratch/HOST --journal tmp/durability-journal-HOST.jsonl --map /workspace/attribution-study-v2/dev-matrix-002=tmp/study-v2-20261004/retrieved/HOST/dev-matrix-002 --map /workspace/attribution-study-v2/prepared-v2=tmp/study-v2-20261002/prepared-v2 --map /workspace/attribution-study-v2/experiments=experiments --prepared /workspace/attribution-study-v2/prepared-v2 --code /workspace/attribution-study-v2/experiments --run /workspace/attribution-study-v2/dev-matrix-002/UNIT-q-a1 --run /workspace/attribution-study-v2/dev-matrix-002/UNIT-e1-a1
   ```

   (one `--run` per sealed folder, dependencies first). The `registry.jsonl` beside the run
   folders is stored with them, so the fresh pod also sees the claims of starts that never
   sealed. This is also the free check of the GitHub connector against the real service.
2. Build the code bundle and look at the request without sending it:

   ```bash
   python -m experiments.durability pack-code --out tmp/durability-code.tar.gz
   ```

   ```bash
   python -m experiments.durability launch --spec tmp/launch-HOST.json --record tmp/launch-HOST.jsonl --dry-run
   ```
3. Launch (this spends; the user approves it):

   ```bash
   python -m experiments.durability launch --spec tmp/launch-HOST.json --record tmp/launch-HOST.jsonl
   ```

   The pod bootstraps (the fixture check included), restores the host's units from GitHub and
   continues with the first unit that is not sealed.
4. While a unit runs, kill the worker from the RunPod web terminal (`pkill -9 -f
   experiments.durability`) and disconnect the laptop. The job runner sees the step fail and asks
   the timer to stop the pod; the timer would stop it at the lease's stop time in any case.
5. From another machine, read the acknowledgements (`acks`) and the stop (the pod shows as
   exited; `check-watchdog` once GitHub has scanned).
6. Launch a **fresh** pod for the same host with a new volume name (`attribution-HOST-b`) and the
   lost attempt's tombstone in the worker configuration if the lost unit was a fresh start (a q).
   It bootstraps, restores from GitHub alone, and continues to the end of the host's jobs.
7. When it finishes it asks the timer to stop the pod. Restore its administrative folder to the
   laptop and read the numbers:

   ```bash
   python -m experiments.durability restore --destination github:4r4cn1d0/attribution-backups --declared-free-bytes 10000000000 --namespace HOST --scratch tmp/durability-scratch/HOST --journal tmp/durability-journal-HOST.jsonl --mirror tmp/validation-HOST
   ```

   ```bash
   python -m experiments.durability worker-report --admin-dir tmp/validation-HOST/workspace/attribution-study-v2/durability-admin/HOST
   ```

   (the timer's own lateness is in `stop-attempts.jsonl` on the pod's volume, read with
   `--timer-dir` on the pod or from the console: the pod's last status change against the stop
   time).

**What the matrix then takes from these numbers**

| setting | takes |
|---|---|
| `unit_seconds` per checkpoint | the largest `run_seconds` seen for that checkpoint |
| `lease_slack` | 1.5 unless a unit exceeded 1.5 times another of its kind; then that ratio plus a quarter |
| `acknowledge_seconds` and `policy.backup_delay_seconds` | twice the largest `acknowledge_seconds` |
| `shutdown.lateness_seconds` and `policy.shutdown_delay_seconds` | the timer's observed seconds after the stop time, doubled, and not below 120 |
| `planned_rates.gpu_per_hour`, `storage_per_hour` | what RunPod reported for the pod and its volume |
| cost per unit | `(run + acknowledge) × rate / 3600` per checkpoint, from the report |
| concurrency | not a setting: admission admits a host only while the balance covers every running pod over that host's lease, with the contingency and the reserve. With balance `B`, reserve `R`, rate `r` and horizon `H` hours (the longest lease plus the delays), at most `(B - R) / (1.25 × r × H)` hosts hold a lease at once |

### Matrix runbook

For hosts not yet run, or lost, in the frozen plan (the host rotation is the plan's and is not
touched):

1. One launch description per host: its own pod name, volume name and worker configuration
   (`host`, and `tombstones` where a lost fresh start was declared). Launch them one after
   another. Each pod's admission reads the live balance and the other running pods, so a host the
   balance cannot carry is refused on its pod: its outcome record says so, its timer stops it, and
   it costs a bootstrap. To avoid even that, launch at most the number the formula above gives.
2. A unit that failed is kept as a failure record and its retry is the next attempt folder with
   the same seed: the same draw. A unit that was lost (the pod died) is kept in the catalogue with
   an unknown cost; a continuation is rerun automatically on the next launch of that host, and a
   fresh start only after the operator names it under `tombstones`. Nothing is renamed or removed.
3. A host is done when its outcome record says `complete` and `acks` lists its six run folders.
   The worker has then asked the timer to stop the pod.
4. Cleanup is stop only. Stopped pods and their volumes keep billing for storage; deleting them
   is the user's decision, after `restore --mirror` on the laptop has shown every unit can be
   read back from GitHub alone.

**Steps for the user:** create the fine-grained backup token (Contents: read and write on
`attribution-backups`) and store it as the RunPod secret `backup_token`; create a Read Only RunPod
key and store it as the RunPod secret `read_key`; approve each launch; delete stopped pods and
volumes when the lead reports the copies verified.

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
- the vault's acknowledgement protocol holds on `GitHubReleaseDestination` against a fake GitHub
  API on 127.0.0.1: acknowledgement and duplicates, partial and corrupt uploads, a wrongly stored
  final object, a crash before and after the acknowledgement, a collision with both kept, restore;
  plus pagination, shard and size limits, torn uploads, bounded rate-limit handling and token
  secrecy;
- `RunPodProvider` against a fake RunPod API: recognition only with a recorded confirmation,
  rates and liabilities, persistence only under a network-volume mount, unknown shapes and
  unexplained spend refused, read-only requests, and admission refusing when no shutdown watchdog
  is configured;
- the shutdown watchdog, the deployed script itself run against fake GitHub and RunPod services
  with a manual clock: no stop before the stop time and one at the first scan after it; a renewal
  superseding the earlier stop time, also while a scan waits; malformed, unacknowledged, withdrawn
  and refused arms governing nothing; an arm for a pod outside the allow-list refused and that pod
  never read; one stop request however many scans follow; an unconfirmed stop failing the run and
  retried; no `DELETE` request to either service; a scan with an empty allow-list succeeding
  without the RunPod key and one with a listed pod and no key failing; the workflow's pins equal
  to the shipped files, its verification step (run here with bash) rejecting a changed or missing
  script or allow-list, holding no secret and coming before the script; isolated Python ignoring
  a module placed next to the script; `armed` only after a matching acknowledgement;
  a late, missing or mismatched acknowledgement refusing admission and withdrawing the arm;
  admission succeeding end to end with every input confirmed and refusing when any one is
  withdrawn; no secret in any log, record, error or request to the other service;
- the stop timer, the deployed script itself. With a manual clock: no stop before the stop time
  and one at it; the cap when no lease exists; a renewal moving the stop time; the most recently
  issued authority governing; withdrawn, malformed, truncated, oversized, foreign and
  future-dated records ignored with the previous deadline kept; a stop at once when the deadline
  is past or no authority is valid; every stop method tried and recorded until one is confirmed;
  a failing mount unable to prevent the stop; nothing terminated or deleted and no other pod
  touched; the key scrubbed from records. As real processes: a killed timer restarted by its
  supervisor and stopping on time; the worker's death leaving the timer untouched; a killed
  "container" re-arming from the mount on its next start; the start command, run by bash,
  unpacking and checking the script, starting the image's start script, and asking for a stop
  itself when the script is damaged or the supervisor dies;
- the worker: its sealed folders against the engine's `calibrate` as described under "Scientific
  identity of the worker"; the identities refused when they differ from the plan; a lease and an
  acknowledgement for every unit; no training without a lease and no next unit without the
  acknowledgement; a pod lost between two units and in the middle of one, restored on a fresh
  volume and continued with the sealed units byte-identical; a lost fresh start waiting for the
  operator's tombstone; a tree made by plain `calibrate` adopted and continued; the lease renewed
  while a unit runs; the finish through the timer;
- the retry path end to end: a tree made by plain `calibrate`, copied to "the laptop", put into
  the vault with `ingest`, restored by the worker on a fresh root and continued;
- the launcher against fake services: the request's shape, secrets only as references, no
  `RUNPOD_API_KEY`, duplicates and prices above the limit refused, a dearer pod stopped and not
  deleted, every request recorded without a secret; and the job runner as a real process: bundles
  fetched with the token and checked, a tampered, missing or unsafe bundle refused before any
  step, receipts, a `once` step not repeated, the timer asked to stop the pod on failure;
- admission with the timer: refused without a recorded self-stop, a fresh heartbeat, a supervised
  timer, the acknowledgement, or records on a network volume; granted when the timer acknowledges
  while the watchdog refuses, is unreachable or never runs; the backup armed without a recent
  scheduled scan and stopping only after the end of the reservation;
- every listed admission input fails closed, two concurrent workers cannot both reserve the same
  runway, a second worker cannot spend the first worker's retention reserve (through renewal and
  release, until its window ends), and an unreadable ledger refuses;
- a dependency stored without its acknowledgement does not count; a crash between an
  acknowledgement and its pin is completed by the retry;
- a backend that already served a block in the process is refused; only a refusal leaves the
  Stage B gate; the safeguard's time shows up where the README says it does.

## What waits for the funded one-worker validation

None of the following is established by local tests. **No live check of either connector has
run**: neither `ATTRIBUTION_BACKUP_GITHUB_TOKEN` nor `RUNPOD_API_KEY` was set when they were built.

Before any funded run (free, needs only the tokens):

- `check-destination` against the real repository: GitHub accepts the names and labels, refuses
  the duplicate, serves the download through its redirect, and reports `state` and `digest` as
  the fake does;
- one real unit through the vault on GitHub, with the request counts and any rate-limit answers
  recorded, to settle the throughput question;
- `check-provider` against the real account: the field shapes, header authentication on GraphQL,
  and whether `currentSpendPerHr` behaves as the cross-check assumes;
- the user's recorded confirmations: the balance and the storage prices.
  (The watchdog's free check is done: deployed and observed, its schedule ran 3 of 33 slots in 16
  hours.)

In the funded one-worker validation:

1. an actual persistent mount, confirmed by the provider, at the recorded path;
2. an off-pod copy made **by the worker**, with the laptop disconnected, to the GitHub repository,
   and the acknowledgement read from an independent machine after the worker is killed;
3. a restore on a fresh provider host into the recorded layout;
4. the stop timer, in this order ([shutdown](#shutdown-the-stop-timer-in-the-pod)):
   - **the cap-only check**: a pod created with the generated settings and a ten-minute cap, SSH
     working, the heartbeat present, the laptop then disconnected; the pod is seen from outside to
     stop at the cap, and the account's spend falls to the storage rates. This is what
     `stop_confirmation` records. It also settles which stop method worked, whether the packed
     script fits in one variable, and how long the stop took;
   - **a real stop at a lease's deadline** with the laptop disconnected and the worker's processes
     killed: the acknowledgement read back by admission on the pod, the stop at `stop_at_utc`,
     the measured lateness against the configured 120 s;
   - **a re-arm after a restart**: the pod restarted (and separately the timer process killed)
     during a lease; `starts.jsonl` shows the new timer with the same lease, and the stop still
     happens at the same time;
   - what the pod-scoped key may do, tried once against a second pod;
   - the backup: a backup arm acknowledged, and its stop record written whenever GitHub next
     scans after the pod was stopped;
5. real balance semantics: what `clientBalance` means, its currency, its delay, and whether
   liabilities and rates are reported as assumed;
6. a restored continuation on CUDA that matches what an uninterrupted run would have produced.

Only after these may concurrency rise, and only within verified runway.

## Open decisions

None is open. The four below were decided by the user on 3 October 2026; the third was amended on
4 October 2026.

1. **Tombstones: allowed.** Declaring a lost fresh start writes an administrative `error.txt` into
   the lost attempt's folder so that the engine's own retry rule applies. It stays an explicit,
   operator-named action and is never taken automatically.
2. **Strictness of the gate: accepted for the one-pod validation.** The copy and the restore
   check run synchronously on the worker, so a billed GPU idles while they run. The idle time is
   accepted for the funded one-pod validation and is to be measured there.
3. **Shutdown: a timer inside the pod, with the GitHub Actions watchdog as a best-effort backup**
   (the user's choice of 4 October 2026, amending that of 3 October, which made the watchdog the
   required shutdown). The reason is the deployed watchdog's schedule: 3 of 33 slots in 16 hours.
   Admission requires the timer's acknowledgement and never the watchdog's
   ([shutdown](#shutdown-the-stop-timer-in-the-pod)). A stop time set at pod creation is not
   pursued; whether RunPod enforces one is not documented.
4. **Stage B cost of the safeguard: deferred.** It must be settled before any held-out Stage B
   run under the gate, in one of two ways: a Stage B amendment that gives the safeguard's time an
   uncharged owner, or a measurement in the funded validation showing that it is negligible.
   Until then the facts are as follows. Every safeguard second inside a session is in the Stage B
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

   The time admission spends arming the shutdown (seconds for the timer, up to about two and a
   half minutes for the backup) is outside any Stage B session: admission happens before a block
   starts. The timer itself adds no time inside a session.

## Commands

Tests (CPU only, the pinned engine environment, caches disabled), from the project root:

```bash
PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -m pytest -q -rs -p no:cacheprovider --basetemp=<scratch>/pytest experiments/durability/tests experiments/safety_decision_policy/tests
```

Acknowledge a sealed chain from a relocated archive into a directory (or `github:owner/repo`
with `--declared-free-bytes`), then restore it elsewhere:

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
- On GitHub every file is uploaded twice and the shard layout is fixed per scheme; a release asset
  must be under 2 GiB; GitHub reports no free space, so capacity is a declared number.
- Admission holds the reservation ledger's lock while it arms the shutdown (seconds for the
  timer, up to about two and a half minutes for the backup), so another worker's admission waits
  that long.
- The stop timer's limits are listed in its section: RunPod acting on a pod's own stop request is
  shown only by an observed stop, a container that never starts is covered by nothing of ours,
  and the timer protects against death, not malice. The backup's: GitHub's schedule is sparse,
  the Actions quota is shared and finite, and its records are not signed.
- The worker launches the engine's calibration units only (`run-one` chains of a plan). The next
  stages (attribution features, held-out jobs, Stage B blocks) are other unit kinds; Stage B has
  its own gate (`stage_b.py`), the others can be acknowledged once sealed but are not launched by
  the worker.
- Each host has its own reservation ledger on its own volume. A host's admission counts the other
  running pods as liabilities over its own horizon, not their full reservations or retention
  reserves; set `retention_reserve` to cover every volume of the account.
- The job runner's bootstrap step is the 2 October script; it cannot be repeated on a volume
  where it half-ran (its receipts refuse an existing folder). Such a pod stops itself and needs a
  fresh volume.
- The RunPod adapter does not see serverless endpoints or other billable resources except through
  the spend cross-check, which refuses when it cannot explain the account's hourly spend.
- The restore check reads the copy back in full for every unit, and a chain's earlier folders
  again for each later unit. This is deliberate and costs time on a billed worker.
- A unit that seals just before the worker dies, with no time to copy it, is lost. The window is
  one unit's copy time, not a host's whole run.
- One gated block per process: a second block on the same inner backend or engine session is
  refused. The pre-block checks of `run_block_gated` run in the block's process, so their small
  time is in the session's start record.
- A reservation ledger written by an earlier format of this package (leases without their
  retention reserve) is refused as unreadable; start a new ledger.
