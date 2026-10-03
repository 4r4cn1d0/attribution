# Specialized Implementation: shutdown-watchdog reports

Copied verbatim from the two messages the Specialized Implementation session sent to General Implementation (briefs `.ai/briefs/durability-watchdog-20261003.md` and `.ai/briefs/durability-watchdog-followup-20261003.md`). The text is the author's account; the review record is `durability-watchdog-review.md`.

## First candidate (2026-10-03T17:52:24.808Z)

````text
durability-watchdog-20261003 is built and passes locally (157 durability + 172 Stage B tests); it is NOT deployed and has made no real GitHub or RunPod call, so no real pod has been stopped.

Workspace: tmp/claude-workspaces/watchdog-20261003/workspace. Only owned files changed (checked against a pre-task snapshot). No commit, push, install, agent or secret handling. Model as the harness reports it: claude-fable-5-1; effort is not observable to me.

TWO THINGS THAT DIFFER FROM WHAT YOU MAY EXPECT
1. Recommended shutdown_delay_seconds is 5400, not 3600. Without waiting inside a run, the stop begins up to 30 min after the stop time, 60 if GitHub drops one scheduled run; 5400 adds half an hour for schedule delay and the confirmed stop. It is an assumption about GitHub's scheduler, enforced by nothing. The worker side refuses any lateness below two scan intervals (3600).
2. The in-run wait for a close stop time is off by default (WATCHDOG_TAIL_SECONDS: "0"). With it on, every lease renewed late would bill up to ~35 Actions minutes per cycle and break the free quota. Off, a stop is on average ~15 min late; the reservation already funds that.

DESIGN
- One workflow in the backup repo. Scheduled scan every 30 min (cron "7,37 * * * *") plus one short run per lease, started by a repository_dispatch event from the worker.
- Records are create-only release assets, one release per kind and month: watchdog-arms-YYYY-MM (arm-<id>.json, void-<id>.json), watchdog-acks-YYYY-MM (ack-<id>.json, refusal-<id>.json), watchdog-stops-YYYY-MM (stop-<id>.json, stop-attempt-...).
- Arm run acknowledges only if: arm well formed; worker and pod on the allow-list (watchdog/pods.json, shipped empty); inside its 10-minute window; RunPod reports the pod RUNNING with the Actions secret; a scheduled scan ran within 75 min. Otherwise a refusal, which is final.
- Scan: per allow-listed pod, the governing arm is the latest acknowledged, non-withdrawn, valid one. At the first scan at or after stop_at_utc: POST /v1/pods/{id}/stop, confirm by GET, record once. Unconfirmed stop fails the run (red in Actions) and is retried next scan. The stop is still asked for if the pod's state cannot be read. No DELETE anywhere; never terminates.
- Worker side (shutdown_watchdog.GitHubActionsWatchdog): publishes the arm with stop_at = at_utc - lateness, dispatches, polls for the acknowledgement, checks arm/worker/pod/stop time/run id/window/recent scan/scan interval, returns armed only then. Anything else raises ProviderError and withdraws the arm with a void record.
- Wiring: provider config key "shutdown": {"kind": "github-actions-watchdog", "repository": "4r4cn1d0/attribution-backups", "lateness_seconds": 5400}. Without it RunPodProvider.arm_shutdown still raises NotConfigured.
- Interface change in admission.py: Provider gained a non-abstract shutdown_lateness_seconds() (default 0.0), and admit() refuses when policy.shutdown_delay_seconds is below it. This guarantees the stop never begins before lease end plus backup delay. Existing fakes are unaffected.
- New read-only CLI command: python -m experiments.durability check-watchdog --config provider.json --worker worker-1.

REJECTED
- 5-minute cron: 8,640 min/month.
- One sleeping run per lease: bills the whole lease; job limit 6 h.
- Enabling the schedule only during a lease: needs Actions: write on the worker token, and a disable can race an enable.
- workflow_dispatch from the worker: needs Actions: write. repository_dispatch needs only Contents: write, which the backup token has.

MINUTES
- 48 scans/day, each billed 1 minute (jobs round up): 1,440 in a 30-day month, 1,488 in a 31-day month, of 2,000 free.
- Each admission, renewal or refused arm: 1 minute. Left: 512-560/month, about 16 arms/day.
- One worker, 2-hour leases all month: 372 + 1,488 = 1,860. Leases under ~90 min held all month do not fit.
- Quota is per account and shared with other private repos. If exhausted with no payment method, jobs are blocked: new arms are refused, but an already granted lease would not be stopped.
- Assumes each run finishes within a minute; not measured.

FACTS VERIFIED IN PUBLIC DOCS (3 Oct 2026)
- schedule: shortest interval 5 min, may be delayed, queued jobs may be dropped — docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- 2,000 min/month on Free for private repos; per-job rounding up — docs.github.com/en/billing/concepts/product-billing/github-actions
- job limit 6 h — docs.github.com/en/actions/reference/limits
- POST /repos/{owner}/{repo}/dispatches is under Contents: write; workflow runs list is Actions: read; workflow_dispatch is Actions: write; pushing workflow files is under "Workflows" — docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens
- RunPod stop: POST https://rest.runpod.io/v1/pods/{podId}/stop — docs.runpod.io/api-reference/pods/POST/pods/podId/stop
- "Stopping a Pod releases the GPU"; volume disk still billed while stopped; with a network volume /workspace is preserved "whether you stop or terminate" — docs.runpod.io/pods/manage-pods
- RunPod key levels All / Restricted / Read Only; the docs do not say which Restricted setting permits a stop — docs.runpod.io/get-started/api-keys
NOT verified: the status code of the dispatch call (code accepts 200/201/202/204); what desiredStatus reads right after a stop; whether actions/checkout@v4 is still the current major version.

FILES (sha256, first 16 hex; full list in my scratchpad watchdog-final-sha256.txt)
New:
- experiments/durability/watchdog/watchdog.py 97d6212ccea033aa
- experiments/durability/watchdog/watchdog.yml e92990c89d2a5cd8
- experiments/durability/watchdog/pods.example.json 484e59d0b8b9e552
- experiments/durability/watchdog/README.md c2095cd23113b578
- experiments/durability/shutdown_watchdog.py 414a915b88e8a1d4
- experiments/durability/tests/test_dur_watchdog.py 7448420076d50d28
Changed:
- experiments/durability/admission.py af06c5641f01369f
- experiments/durability/runpod_provider.py 510bc13d635158b1
- experiments/durability/wiring.py 059b0080c6541bd7
- experiments/durability/__main__.py d0a688699825aa79
- experiments/durability/README.md 38ed20f50274f4e1
- experiments/durability/tests/fake_github.py 76d9b0c7be59c137
- experiments/durability/tests/fake_runpod.py 611333bb1aeda472
- experiments/durability/tests/test_dur_runpod.py 3e7a2e4248debf32
- research/experiments/2026-10-03-recovery-safeguards.md 8a0341e2f212e0da
Engine and Stage B untouched.

COMMANDS RUN (pinned venv, from the workspace root)
- PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -m pytest -q -rs -p no:cacheprovider --basetemp=<scratch> experiments/durability/tests experiments/safety_decision_policy/tests -> 329 passed, exit 0
- same, experiments/durability/tests only -> 157 passed, exit 0 (was 93; 64 new)
- same, experiments/safety_decision_policy/tests only -> 172 passed, exit 0
- 20 mutation checks on a scratch copy (e.g. obey unacknowledged arms, stop 10 min early, skip the allow-list, skip the re-check after a wait, forward the token on redirects, worker skips the acknowledgement check, admission ignores lateness): all 20 caught by test_dur_watchdog.py.
- After the last full run only README.md changed (one sentence); the watchdog tests were rerun: 64 passed.

ACCEPTANCE CRITERIA
Passed in local fakes: deadline logic with a manual clock; renewal and supersession (also while a scan waits); malformed lease refused (12 cases); non-worker pod refused and never read; idempotent stop; nothing deleted; acknowledgement required before armed; missing/late/mismatched acknowledgement refuses admission (11 forged cases); no secret in logs, records, errors or the other service; admission end to end, and refusal for each of 13 withdrawn inputs; explicit minimal permissions block checked by a test; four user decisions recorded as decided 3 Oct 2026 in both documents.
Not tested (cannot be, locally): GitHub's scheduler timing, real billing per run, a real RunPod stop, the key level needed to stop.

DEPLOYMENT STEPS FOR YOU
1. On the default branch of 4r4cn1d0/attribution-backups: watchdog/watchdog.py, watchdog/pods.json (from pods.example.json), .github/workflows/watchdog.yml. The pushing credential needs the "Workflows" permission; the backup token does not.
2. Set actions/checkout to the current major version or pin a commit; I did not check v4 is current.
3. When the pod exists, commit its id to watchdog/pods.json under the worker's name.
4. Add the "shutdown" section to the provider config; use a policy with shutdown_delay_seconds >= 5400.
5. Admit only after a scheduled run has appeared in Actions; a manual run does not count, and the first arm is otherwise refused ("liveness").

STEPS FOR THE USER
1. RunPod console, Settings, API Keys: create a key for the watchdog ("Restricted" with write on Pods if offered, else "All"); copy it once.
2. GitHub, attribution-backups, Settings, Secrets and variables, Actions, New repository secret: RUNPOD_API_KEY.
3. Same repo, Settings, Actions, General: allow Actions to run, including actions/checkout. The default workflow permission can stay read-only.
4. No change to the backup token.
5. Check: Actions tab shows a green "watchdog" run every half hour; check-watchdog prints the governing stop time and the acknowledging run.
6. Watch Actions minutes under account Billing (~1,500/month from the watchdog alone).
Suggested: the worker's own RUNPOD_API_KEY should be a separate Read Only key.

WEAKEST ASSUMPTION
That scheduled runs arrive within 5400 s of the stop time and that the Actions-secret key can actually stop the pod. The acknowledgement proves the key can read the pod, not stop it.
Counterexample: GitHub drops two scheduled runs in a row, or the account's minutes run out mid-lease, or the key is read-only: the pod runs past its reservation and nothing notices until the next arm is refused.
Settling check: free, deploy with no pod for a day and read the scheduled runs' start times and billed minutes; then in the funded validation one real stop with the laptop disconnected, reading seconds_after_stop_time in the stop record and the account's spend afterwards.

OTHER LIMITS TO KNOW
- One stop per arm: a pod restarted by hand after its stop is not watched until a new lease arms it. If you want "keep stopping while the governing arm is expired", that is a small change but it would fight an operator inspecting the pod; your call.
- A backstop, not a scheduler: work that ends early leaves the pod running to the stop time unless someone stops it.
- Records are not signed: a compromised backup token could forge an acknowledgement or withdraw an arm.
- If the worker can neither read the acknowledgement nor write the void, an arm with no lease behind it may govern; the error message says so.
- Admission holds the ledger lock while waiting for the acknowledgement (up to ~11 min).
- A pod RunPod reports as not found is recorded as gone.
````

## Follow-up round (2026-10-03T18:02:15.530Z)

````text
Watchdog follow-up done: A, B and C are fixed and tested (161 durability + 172 Stage B pass), and I closed one bypass of fix A that the hash pin alone would have left open.

Same workspace (tmp/claude-workspaces/watchdog-20261003/workspace). Only owned files changed; no real call, commit, push, install or agent.

THE EXTRA BYPASS (please read)
- Pinning the script's hash is not enough. `python3 watchdog/watchdog.py` puts the script's folder first on the import path, so a worker could push `watchdog/json.py` next to the unchanged, correctly hashed script and it would run with the RunPod key.
- Fix: the script step is `python3 -I watchdog/watchdog.py` (isolated mode: the script's folder is not on the import path).
- A test shows both sides: with -I a planted json.py is not imported; without it, it is.

A. PINS AND VERIFICATION
- The workflow pins the SHA-256 of watchdog/watchdog.py and watchdog/pods.json.
- A "verify the pinned files" step runs after checkout and before the script. It has no env, no expression, no secret, and executes nothing from the repo. A changed or missing file exits 1 there.
- I did not use `sha256sum -c`. Without --strict, GNU skips a malformed line and still exits 0, so a typo in a pin would silently drop that file's check. The step instead compares `sha256sum < file` with the pin per file; any typo is a mismatch.
- Tests: pins equal the shipped files; step order and no secret anywhere but the last step (also no workflow-level or job-level env, no `if:` or `continue-on-error`); the step's own commands are run with bash locally and reject seven cases (script appended, one byte short, empty, missing; allow-list emptied, renamed pod, missing); a planted `sha256sum` file in the repo changes nothing.
- Docs: adding a pod = edit pods.json, run `sha256sum watchdog/watchdog.py watchdog/pods.json`, replace the hash on the matching pin line, push both in ONE commit with a Workflows-capable credential. The backup token must not get that permission.

B. CHECKOUT
- `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1`, persist-credentials: false kept.
- Test: the one `uses:` is pinned to 40 hex.
- The SHA is your verified fact; I made no GitHub request and did not check it or that v7 still accepts persist-credentials. The README says so.

C. EMPTY ALLOW-LIST
- Empty allow-list: scan exits 0 without the key, reads no record, sends nothing to RunPod.
- Listed pod and no key: scan exits 1 with "RUNPOD_API_KEY is not set, but the allow-list names a pod".
- Arm run without the key: refused, and now a refusal record is written so the worker learns at once instead of timing out.
- Tested in one test covering all three, then the key is set and the pending stop is carried out.

RESIDUAL YOU SHOULD KNOW
- The pins protect the RunPod key, not the stop. A compromised backup token can still prevent a stop: forge or withdraw records (already documented), or push a change that makes the check fail, which turns every run red and stops nothing. Red runs are at least visible.
- Not checked: whether a token without Workflows permission can delete the workflow file.

EXACT DEPLOY FILE SET (source in experiments/durability/watchdog/ -> backup repo, default branch)
- watchdog.py -> watchdog/watchdog.py
  sha256 1f49dd887eb687334682e0716a3b9b25566ba88f99c9b4f79fbe266083a801b7 (pinned)
- pods.example.json -> watchdog/pods.json, byte for byte
  sha256 484e59d0b8b9e55243feefa54e8a96721632e8e6f172e0c747cbca0376663b17 (pinned)
- watchdog.yml -> .github/workflows/watchdog.yml
  sha256 46dc8bcf79c017823107b5b3ba31dff694b5616ca855ad7335bf4ef713888546
Copy without changing line endings; one byte off fails the check. With the empty allow-list this can go live before the user sets the secret, and scans will be green.

CHANGED FILES SINCE MY LAST REPORT (sha256)
- experiments/durability/watchdog/watchdog.py 1f49dd887eb687334682e0716a3b9b25566ba88f99c9b4f79fbe266083a801b7
- experiments/durability/watchdog/watchdog.yml 46dc8bcf79c017823107b5b3ba31dff694b5616ca855ad7335bf4ef713888546
- experiments/durability/watchdog/README.md 1b803978426b7517a6715242ed6fe9abec433f6ad14d7fe3bb31cf8f4312beef
- experiments/durability/README.md 7b40c0ea3ce46c8704f90eb8a0f8e5df66d43ec306e0e712b737a68aabc2d517
- experiments/durability/tests/test_dur_watchdog.py 12087f6470cd747b009f0214afe649c05d095806c1508d7270a50049aa0b7755
- research/experiments/2026-10-03-recovery-safeguards.md 700e4b9ba1faafd709ebfdb0092de252a5d9a3e1b2f64ac7e0e987879b44dbf4
Unchanged: pods.example.json, shutdown_watchdog.py, admission.py, runpod_provider.py, wiring.py, __main__.py, the fakes, test_dur_runpod.py.

COMMANDS (pinned venv, workspace root)
- PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -m pytest -q -rs -p no:cacheprovider --basetemp=<scratch> experiments/durability/tests experiments/safety_decision_policy/tests -> 333 passed, exit 0, no skips
- same, experiments/durability/tests -> 161 passed, exit 0 (68 in test_dur_watchdog.py)
- same, experiments/safety_decision_policy/tests -> 172 passed, exit 0
- 14 mutation checks on a scratch copy (script or allow-list changed without its pin, pods.json unpinned, check only warns, check compares nothing, secret in the verify step, verify after the script, no -I, checkout by tag, credentials persisted, job-level secret, continue-on-error, listed pod without key passes, empty list needs key): all 14 caught.

One local dependency: the verification-step test needs bash and sha256sum on the test machine (present here; it would show as skipped elsewhere, never as a silent pass).
````
