# Runpod credit-depletion incident

2 October 2026. User reported exhausted Runpod credits around18:18UTC.
The assistant configured13 task-owned A100pods with100GB container disks and
no persistent/network volumes. This was an operational mistake: scientific
checkpoints should have been durable and copied off-pod as each checkpoint sealed,
with prepaid balance/runway checked before and during the parallel workload.
Removing the user's dollar cap did not create prepaid credits.

## Observed status

- All13 SSH connections were closed by remote hosts around18:18:12–18:18:27UTC.
- GET /pods at18:18:59UTC lists none of the13 owned IDs.
- Individual read-only GET /pods/<id> checks at18:19:33UTC returned404 for all13.
- No DELETE, stop, restart, credit purchase or payment-settings change was issued
  in this incident response. The provider's exact internal termination cause is
  inferred from the user report and simultaneous disappearance, not an exposed
  reason field.
- Runpod's current billing documentation says zero-credit pods without network
  volumes are terminated with unrecoverable data; its storage documentation says
  container disks are lost on stop/restart. Sources checked2October:
  https://docs.runpod.io/accounts-billing/billing
  https://docs.runpod.io/pods/storage/types

Treat unsynced new development artifacts as lost. No claim of recovery is made.
Topping up alone does not restore deleted container disks.

## Preserved locally

Allfive old calibration/cap-sensitivity archives are present and their SHA256
hashes were rechecked against saved receipts. Their prior verification reports
cover31 sealed calibration/evaluation runs, with complete own-file/dependency/
training-stream checks. Code, configurations, source/prepared data, experiment
plans, local implementation work, audits, old summaries and status/fingerprint
snapshots are also present. Prepared-v1 and prepared-v2 manifest identities are
unchanged. The research project and earlier measurements have not been lost.

Archive directory: tmp/study-v2-20261002/retrieved-calibration/.

## Not retrieved

No new dev-matrix or development-feature archive exists locally for any of the13
hosts. Retrieval was incorrectly gated on completion of both per-host trajectories,
instead of promptly backing up each sealed checkpoint. The last18:11 status
record showed all13 first-seed q/e1 checkpoints sealed and e3running. These status
records and some fingerprints do not replace the missing actual checkpoint and
output artifacts. Do not represent them as completed, auditable new results.

Both original and corrected retrieval queues failed because SSH was closed; this
incident happened before either queued archive operation. The separately recorded
original counting-assertion defect is not the observed cause of these failures.
Preserve both logs and all interrupted attempt identities/costs. The second seed,
attribution and heldout jobs must not be presumed to have executed.

## Recovery prerequisites

No new cloud training until durable storage, off-pod copies after each sealed
checkpoint, verified restore, and a live balance/runway check are implemented and
verified and funding is available. Keep compute concurrency tied to available
prepaid runway as well as scientific workload. Do not enable auto-pay or buy
credits as a side effect of recovery. Keep local Opus implementation/review work
within its existing brief; do not interrupt it or launch duplicate calls.

Same-seed reruns, if required, must use explicit new attempts with the lost runs
and spending retained. Do not silently fill missing evidence from differently
identified calibration runs. The frozen four-step study remains incomplete;
there are no heldout policy results or demonstrated attribution benefit.

Evidence: tmp/study-v2-20261002/credit-incident-inventory-20261002T181859Z.json,
credit-incident-direct-check-001.json, and per-host retrieval logs/receipts.
The finite heartbeat is retained with explicit incident/relaunch prerequisites.
