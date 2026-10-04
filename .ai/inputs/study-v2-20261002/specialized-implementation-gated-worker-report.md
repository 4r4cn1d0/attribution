# Specialized Implementation: gated worker, launcher and job runner report

Copied verbatim from the message the Specialized Implementation session sent to General Implementation (brief `.ai/briefs/durability-gated-worker-20261004.md`, scope adjusted by `matrix-launch-plan-20261004.md`). The text is the author's account.

## Report (2026-10-04T13:47:46.686Z)

````text
durability-gated-worker-20261004 is built and passes locally (260 durability + 172 Stage B tests); nothing was launched, no real request was made, and the worker's real-model path has never executed.

Workspace: tmp/claude-workspaces/gated-worker-20261004/workspace. Only owned files changed (checked against a pre-task snapshot); reference/ untouched. Model per the harness: claude-fable-5-1; effort not observable.

WHAT EXISTS NOW
- `worker` (worker.py): one host's jobs of the plan through UnitRunner. Start: the 2 October identity checks as refusals (engine, recipe, manifest, BOOTSTRAP-VERIFIED fixture_exact) and a restore of the host's acknowledged units. Run: each job in its own process with a fresh session, as calibrate was invoked; before a unit an admission lease (unit_seconds × lease_slack + acknowledge_seconds), kept alive by a thread if the unit overruns; after the seal the acknowledgement. Finish: outcome record, lease released, timer asked to stop the pod (also on refusal or failure).
- `pod_timer/pod_job.py`: the in-pod job runner the timer's supervisor starts. Fetches bundles from release assets (named by SHA-256, hash and size checked, unsafe archive members refused), writes the worker config, runs steps with receipts (`once` steps not repeated), asks the timer to stop on failure. No inbound connection.
- `launch` (launcher.py): price check, duplicate refusal, bundle upload, volume by name or created, pod created with timer + job runner + secret references; a pod that reports a price above the limit is stopped. No terminate or delete in the code. `--dry-run` contacts nothing.
- Also: `pack-code`, `worker-report` (run, copy, restore-check, admission times, cost per unit, timer lateness), `PodTimer.finish`, `UnitRunner.adopt`, and `ingest` now stores registry.jsonl with the run folders.

SCIENTIFIC IDENTITY (the decisive test)
- Against `calibrate` at the same absolute paths, the worker's sealed folders differ only in fields where two `calibrate` runs differ from each other: seconds, timestamps, and hashes of the files that hold them. This is measured in the test, not assumed.
- Against the plan's relative-path command: additionally eight path fields are spelled absolutely, each resolving to the same place (job.json resume_from; assets.json loaded_in ×2; dependencies.json path; COMPLETE.json resumed_from; records.jsonl loaded_in, done_in, from_run), plus the hashes of job.json and assets.json.
- Every .safetensors state and every evaluation output is byte-identical. Registry: same claim, different time.
- No blocker found; the engine was not touched.
- Limit of this evidence: CPU fixtures only.

FOR YOUR 4 OCTOBER RUN (adjusted scope)
- A tree made by plain calibrate is taken over: sealed units adopted and acknowledged, an unfinished attempt kept as lost with unknown cost and rerun as the next attempt, a lost fresh start waiting for the operator's tombstone (given in the worker config, applied once, only those named).
- The laptop path is tested end to end: calibrate tree → copied aside → `ingest` with --map → fresh root → worker restores and continues.
- One fix this exposed: an attempt interrupted by a signal was catalogued "failed" with no engine error.txt and could not be tombstoned; it can now.

DESIGN CHOICES AND REJECTED OPTIONS
- Bundles via GitHub release assets, not SSH: the pod pulls with the token it holds anyway, so the laptop can be off and a restart or a fresh pod repeats unattended. Rejected: SSH (needs laptop and open port at every start); a custom image (needs a registry, and prepared-v2 would sit in an image). Bundles are opaque: hashed and unpacked, never read.
- GPU: A100-SXM4-80GB, Secure. The 2 October receipts show all 13 hosts on SXM4 at $1.59/h and no unit on PCIe, so they allow no cost-per-unit comparison between variants; the fixture exists only for SXM4. Calibration-recipe times: about 560 s (q), 1,035 s (e1), 2,180 s (e3), so about 63 min and $1.67 per arm and seed. Within SXM4, dev03's machine class was about 22% faster at the same price; the API cannot select it.
- One process per job: a shared session would change the second job's recorded asset loads.
- Per-host reservation ledgers: a host's admission counts other pods as liabilities over its own horizon. With equal hosts this bounds concurrency at (B − R) / (1.25 × r × H).

FACTS VERIFIED (RunPod docs, 4 October)
- POST /v1/pods fields used: name, imageName, gpuTypeIds, gpuCount, computeType, cloudType, interruptible, networkVolumeId, volumeMountPath, containerDiskInGb, ports, env, dockerStartCmd, dataCenterIds, minRAMPerGPU, minVCPUPerGPU, allowedCudaVersions — docs.runpod.io/api-reference/pods/POST/pods
- POST /v1/networkvolumes requires name, size, dataCenterId; names need not be unique — docs.runpod.io/api-reference/network-volumes/POST/networkvolumes
- Secret references `{{ RUNPOD_SECRET_name }}` — docs.runpod.io/pods/templates/environment-variables
- GraphQL gpuTypes has securePrice and communityPrice — graphql-spec.runpod.io
NOT verified: that secret references resolve for pods created through REST (documented for console and templates); the response code and shape of volume creation beyond the schema; that gpuTypes accepts a Bearer header.

FILES (sha256, first 16 hex; full list in my scratchpad gated-worker-sha256.txt)
New: worker.py aadb565818aa9ebc; launcher.py dad558da4f0bc4d9; pod_timer/pod_job.py 5fc87cd82d6308fc; tests/test_dur_worker.py 88d7cb56ee82f61b; tests/test_dur_launcher.py f63778cbc2141c74
Changed: engine_units.py 7068155d0d5e5fb9; shutdown_timer.py d77a67746d6f9f51; __main__.py 02357287bc8c334e; README.md af246f62a3c9128d; pod_timer/README.md 69876711784ba7c8; tests/fake_runpod.py dfa6641ff2a61c97; tests/test_dur_pod_timer.py 990ccfc4cbb67a84; research/experiments/2026-10-03-recovery-safeguards.md 3a5a2ce8bdbea75b
Unchanged: pod_timer/pod_timer.py (fdf428ef…) and watchdog/watchdog.py (49d23612…), so the timer you deployed today and the watchdog pin are unaffected. `settings()` without a job script produces the same start command as before.

COMMANDS (pinned venv, workspace root, caches off, basetemp in my scratchpad)
- pytest experiments/durability/tests experiments/safety_decision_policy/tests -> 432 passed, exit 0, no skips (13 minutes; this Mac was loaded)
- pytest experiments/safety_decision_policy/tests -> 172 passed, exit 0
- 28 mutation checks on a scratch copy (worker, launcher, job runner): all 28 caught.
- After the last full run I changed only three test counts in the research note.

NOT TESTED
- The real-loader job process (`worker-job` started by the parent, real models, CUDA): tests inject the job with fixture loaders in-process.
- `build_services` against real GitHub and RunPod.
- Any real launch.

RUNBOOKS (exact commands are in README, "Running a host on a pod")
One-pod validation, starting from a host of today's run:
1. `ingest` the pulled tree with --map to the pod's recorded paths (also the first live check of the GitHub connector).
2. `pack-code --out tmp/durability-code.tar.gz`, then `launch --spec … --record … --dry-run`.
3. `launch --spec tmp/launch-HOST.json --record tmp/launch-HOST.jsonl` (spends; the user approves).
4. Kill the worker from the web terminal and disconnect; the pod stops itself.
5. Launch a fresh pod with a new volume name (tombstone in the config if the lost unit was a q); it restores from GitHub alone and finishes.
6. `restore --mirror` to the laptop, then `worker-report --admin-dir …`.
The README table says which measured number sets which matrix setting (unit_seconds, lease_slack, acknowledge_seconds and backup_delay, lateness and shutdown_delay, planned rates).
Matrix: one launch description per host; admission on each pod limits concurrency by the live balance; failed units retry as the next attempt with the same seed; lost fresh starts need a named tombstone; cleanup is stop only.

USER'S STEPS
- Create the fine-grained backup token and store it as RunPod secret `backup_token`.
- Create a Read Only RunPod key and store it as RunPod secret `read_key`.
- Approve each launch; delete stopped pods and volumes after you report the copies verified.

WEAKEST ASSUMPTION
That a pod created through the REST API gets its secret references resolved, and that the worker's real job process behaves as the fixture one.
Counterexample: the reference arrives as literal text; the job runner's bundle download is rejected, the step fails, and the pod stops itself five minutes later having done nothing.
Settling check: one cheap pod (any small GPU) launched with a tiny bundle and a one-step job; `job.jsonl` showing "bundle-fetched" proves the secret resolved and the whole start chain works. Then the first A100 retry settles the real job process.

LIMITS
- The worker launches calibration units only; attribution features, held-out jobs and Stage B blocks are other unit kinds and are not launched by it.
- The bootstrap step is your 2 October script; it cannot repeat on a volume where it half-ran, so such a pod stops itself and needs a fresh volume.
- HF_HOME must be on the volume (in the launch example), or a restarted container has no models.
- The subprocess tests use real time; on a loaded machine they are slow and could be flaky.
````
