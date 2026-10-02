# Lead first-pass recovery design notes

2 October 2026, approximately 18:51 UTC. Planning only; no implementation,
provider operation, balance query, training, or recovery validation is implied.
The anonymous exporter remains the sole active Opus call. A bounded read-only
review was requested from current_proposal_rigor_audit without supplying these
preferred implementation choices; it shares the incident and existing code.

## Smallest candidate

Keep the frozen scientific engine unchanged. Add a separate administrative
supervisor that observes each newly sealed unit, transfers its complete dependency
closure to an off-pod destination, verifies hashes and the existing engine's
own-file/chain/stream checks, then records an immutable acknowledgement. Do not
wait for both seeds, a whole host, or an attribution stage to finish. Existing
archives and unsuccessful attempt records stay unchanged.

The source must be on provider-confirmed durable storage before training is
admitted. Local or provider-side polling can detect sealed units promptly, but a
laptop-only poller cannot provide unattended protection while the laptop is
asleep or disconnected. A dispatch gate should prevent further assigned work
when backup acknowledgements or balance evidence become stale. Already active
work and its possible unsealed loss remain a separately documented limitation.
This is not yet a claim that current calibrate or StageB invocation boundaries
support that gate: determine the actual insertion point before implementation.

Use immutable per-unit manifests, temporary transfer locations, verification
before an atomic ready marker, and idempotent reuse only for identical verified
content. A same-name/hash mismatch must fail and preserve both records. A
separate, append-only incident/cost ledger records partial transfers, failed
attempts, unknown spend and unresolved timing. Do not put credentials in copied
records. Opaque held-out payloads may be transferred and hash-checked without
reading predictions or unblinding policy choices.

## Restore and financing boundaries

Current verify.PathMap supports read-only relocation. It does not make a
continuation executable from arbitrary new paths: runner reads the original
dependency locations. Prefer rebuilding the original absolute directory layout
on a new authorized host rather than rewriting sealed job or receipt files.
Confirm that mount/layout prospectively; a local relocated verification alone
is insufficient. Same-seed retries require new attempt identities and retain the
lost attempt and its incurred cost.

Runway admission should use a timestamped, explicitly recognized balance value,
all active account liabilities relevant to that balance, proposed GPU and storage
rates, remaining assigned work, backup/shutdown time, and a stated contingency.
Unknown, stale, negative, nonfinite or ambiguous inputs fail closed. No payment
changes or automatic top-up. A removed financial cap is not a balance reading.
Do not invent a provider balance API or assume durable storage survives account
exhaustion indefinitely. These provider details require authoritative validation
and later funded end-to-end checks.

## Alternatives and decisive checks

1. Manual checkpoint copies are simpler but fail the unattended-progress need.
2. A small watcher plus acknowledgement gate fits existing sealed-unit receipts.
3. A general storage/workflow framework adds unnecessary migration and review
   scope unless the small watcher cannot enforce the required boundaries.

Local acceptance should exercise interruption mid-copy, corrupt/missing
dependencies, stale acknowledgements, duplicate events, path collisions,
insufficient destination space, stale/missing balance, concurrency admission,
and restore into a fresh tree using existing sealed calibration evidence. A fake
provider verifies control flow only. Later actual durable-mount, off-pod transfer,
restart and balance-response checks are required before cloud training resumes.

No implementation assignment is dispatched from these notes. The existing
anonymous-export and StageB correction work retain priority and one-Opus routing.
