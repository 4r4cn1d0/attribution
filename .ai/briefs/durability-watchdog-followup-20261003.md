# Bounded follow-up: watchdog review findings (before deployment)

- **From:** General Implementation, acting as lead.
- **Same workspace and rules as** `.ai/briefs/durability-watchdog-20261003.md`: edit only your files; no real calls, secrets, commits, pushes, deploys or agents.
- **Review so far:**
  - Scope and hashes verified: 9 files changed and 6 added, all owned.
  - Admission and the worker side reviewed; both are sound.
  - Three issues must be fixed before deployment.

## A. The workflow runs a script that the worker's token can rewrite (security, must fix)

- **Problem.**
  - The workflow checks out the default branch and runs `watchdog/watchdog.py` with `RUNPOD_API_KEY` in its environment, using `pods.json` as the allow-list.
  - The worker's backup token has Contents: write, which it needs for release assets. That permission also lets it push commits to the default branch.
  - GitHub blocks that token from changing `.github/workflows/*` (that needs the Workflows permission), but NOT `watchdog/watchdog.py` or `watchdog/pods.json`.
  - So a buggy or compromised worker could:
    - replace the script, and exfiltrate the RunPod key or spend with it;
    - remove its own pod from the allow-list, and never be stopped.
- **Fix:**
  - The workflow YAML pins the SHA-256 of `watchdog/watchdog.py` and `watchdog/pods.json`.
  - A step before the script verifies both, for example with `sha256sum -c` on lines written in the YAML. On any mismatch it fails before the secret is exposed to anything from the repo: the secret must not be in that step's environment.
  - Changing either file then requires a YAML change, which needs the Workflows permission the worker lacks.
- **Tests:**
  - the YAML's pinned hashes equal the current files;
  - the verification step runs before the script step and has no secret in its environment;
  - a test that parses the step's commands shows that a modified file is rejected.
- **Docs:** the operator procedure. Adding a pod means editing `pods.json` and updating its pinned hash in the YAML, with a credential that has the Workflows permission.

## B. `actions/checkout@v4` is outdated

- **Fact.** The latest release of `actions/checkout` is **v7.0.1** (published 2026-07-20). Its tag points at commit **`3d3c42e5aac5ba805825da76410c181273ba90b1`**. Verified 3 October 2026 through the GitHub API: `repos/actions/checkout/releases/latest` and `git/ref/tags/v7.0.1`.
- **Fix:** pin `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1`, and keep `persist-credentials: false`.
- **Test:** every `uses:` is pinned to a 40-hex commit.

## C. An empty allow-list should not need the RunPod key

- **Problem.** `watchdog.py` requires `RUNPOD_API_KEY` even when no pod is allow-listed. Deployed before the user adds the secret, every scheduled scan would fail red, and the liveness signal would be noise.
- **Fix:**
  - With an empty allow-list, a scan succeeds without the RunPod key and calls nothing at RunPod.
  - With any allow-listed pod and no key, the scan fails loudly: red, with a clear message. An unconfigured watchdog guarding a pod must be visible.
  - Arm runs keep requiring the key.
- **Tests:** both cases.

## Acceptance

- The fixes and tests above.
- The full durability and Stage B suites pass in the pinned venv; Stage B stays at 172.
- Report back to "General Implementation":
  - changed files with hashes;
  - the exact deploy file set, with the pinned hashes;
  - commands and their exit statuses.
