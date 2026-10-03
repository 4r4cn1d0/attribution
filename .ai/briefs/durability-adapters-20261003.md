# Bounded assignment: real connectors for the recovery safeguards (GitHub storage, RunPod provider)

## Task and authorization

- **Task ID:** durability-adapters-20261003.
- **Authority:** the user chose GitHub release assets as the free off-pod backup destination and told General Implementation, acting as lead with no GPT brief, to proceed. General Implementation created the private repo `4r4cn1d0/attribution-backups` (default branch `main`, README commit). It will review, verify and integrate your result.
- **Goal:** replace the two fail-closed placeholders in `experiments/durability` with real, locally tested connectors:
  1. a `Destination` backed by GitHub release assets;
  2. a `Provider` backed by RunPod's API.
- **Must stay true:**
  - Every safeguard keeps failing closed: missing token, unclear semantics or an unconfirmed capability means refusal.
  - The engine (`experiments/safety_selection`, `experiments/minimal_safety`) and Stage B (`experiments/safety_decision_policy`) do not change.

## Facts checked on 3 October 2026

Re-verify anything you rely on against the current official docs (read-only web access is fine), and cite it in the docs.

- **GitHub releases** ([about releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases), [release assets API](https://docs.github.com/en/rest/releases/assets), [fine-grained PAT permissions](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens)):
  - each file must be under 2 GiB;
  - at most 1000 assets per release;
  - no limit on total release size or bandwidth;
  - uploads go to `POST https://uploads.github.com/repos/{owner}/{repo}/releases/{release_id}/assets?name=...`;
  - uploading a name that already exists returns 422 (the old asset must be deleted first), so writes are create-only by nature;
  - the fine-grained PAT permission **Contents: write** covers creating releases and uploading, listing, downloading and deleting assets;
  - assets can also be renamed with `PATCH .../releases/assets/{asset_id}`. Verify whether renaming onto an existing name fails; if it does, it can serve as the atomic staging-to-final commit.
- **RunPod** ([billing](https://docs.runpod.io/accounts-billing/billing), [runpodctl user](https://docs.runpod.io/runpodctl/reference/runpodctl-user), [runpodctl pod](https://docs.runpod.io/runpodctl/reference/runpodctl-pod)):
  - At $0, pods with a network volume are stopped and the volume's data is kept, but storage keeps billing and the volume "may eventually be terminated". Pods without one are terminated and their data can't be recovered.
  - `runpodctl user` reports `clientBalance` ("current credit balance"; the currency is not stated), `currentSpendPerHr` and `spendLimit`.
  - `runpodctl pod create --network-volume-id`, `pod stop` and `pod delete` exist.
  - A search snippet mentioned `--stop-after` and `--terminate-after`, but they are NOT in the runpodctl pod reference. Whether RunPod enforces any scheduled stop on its servers is **unverified**.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/adapters-20261003/workspace`. It was prepared manually with the launcher's exclusion rules (manifest beside it), from the project branch `stageb-costs-and-recovery-safeguards-20261003`.
- **Owned:**
  - `experiments/durability/**`: new modules and tests, plus edits to its README, `__main__.py`, `destination.py` and `admission.py` where needed;
  - `research/experiments/2026-10-03-recovery-safeguards.md`.
- No other file.

## Requirements

### 1. `GitHubReleaseDestination(Destination)`

- **Contract.** Implement the full `Destination` contract with the semantics `Vault` relies on:
  - staging uploads;
  - a commit that is exclusive and never replaces a different final object (identical content is reused; different content raises `CollisionError`);
  - `put_new` exclusive;
  - `sha256` computed from bytes **read back from GitHub**;
  - `list` by prefix;
  - `discard` of staging objects only.
- **Design choices that are yours:**
  - mapping keys, which contain `/`, to legal asset names, with no collisions and reversible;
  - sharding across releases to respect the 1000-asset limit, made configurable so tests can use a small shard;
  - handling pagination;
  - bounded retries for transient errors and rate limits (403/429 with reset headers), after which `TransferError`.
- **Size.** Files of 2 GiB or more raise `CapacityError` before any upload. `free_bytes` cannot be measured, so return a declared cap and document it.
- **Token.**
  - Read it from an environment variable, for example `ATTRIBUTION_BACKUP_GITHUB_TOKEN`.
  - If it is missing, raise `NotConfigured`.
  - Never log, record, describe or put it in an exception message.
  - `describe()` names only the repo and the release scheme.
  - Use stdlib `urllib` only: no new dependencies, nothing installed.
- **Threat model.** State it in the docs: a token with Contents write can also delete assets. This protects against losing credits, not against token compromise. Check whether GitHub's current "immutable releases" feature, or something like it, could prevent deletion without breaking incremental uploads, and report what you find. Adopt it only if it fits cleanly.

### 2. `RunPodProvider(Provider)`

- **API access.** Use RunPod's API (GraphQL or REST, whichever is current and documented; verify the endpoints) with the API key from an environment variable such as `RUNPOD_API_KEY`. The same secrecy rules apply as for the GitHub token.
- **Methods:**
  - **`read_balance`:** parse `clientBalance` with its timestamp. Return `kind=BALANCE_KIND` with `recognized=True` **only** when configuration explicitly records that a human confirmed the field means the prepaid credit balance in a stated currency. Otherwise refuse, or return `recognized=False` so admission refuses.
  - **`read_rates` and `list_liabilities`:** derive them from the account's pods and network volumes as the API reports them. An unknown or missing field fails closed.
  - **`confirm_persistent(path)`:** confirm only when the worker pod has a network volume attached and the path lies under its mount (verify the mount path, for example `/workspace`).
  - **`arm_shutdown(worker, at_utc)`:** return `armed=True` **only** for a schedule that RunPod itself enforces on its servers, if such a feature exists and is documented. Otherwise raise `NotConfigured` and document the options. One option is an external always-on controller, for example a scheduled GitHub Actions workflow in the backup repo that stops the pod through the API at the lease end. Do not build it; describe what it would need: the RunPod key as an Actions secret, set by the user.

### 3. Wiring

- A configuration path that builds the real connectors explicitly; the defaults stay unconfigured and fail closed.
- `__main__` commands may take a `--destination github:...` style option.
- No command creates, starts, stops or deletes a pod or volume.

### 4. Tests (local only)

- **GitHub:**
  - Use a fake GitHub API served on `127.0.0.1` inside the tests, implementing the needed endpoints with 422 on duplicates, pagination and rate-limit responses.
  - Run the **existing vault tests' scenarios against `GitHubReleaseDestination`** through the fake: acknowledgement, crash before and after, partial or corrupt upload, collision, restore. This is the decisive check that the acknowledgement protocol holds on this connector.
- **RunPod:** use fake API responses for balance parsing and recognition, liabilities, persistence and the shutdown refusal. Any unknown shape fails closed.
- **Command:** the full durability and Stage B suites with `tmp/minimal-experiment-20261002/venv/bin/python`, with caches disabled and basetemp in your scratchpad. Stage B stays at 172 passed.

### 5. Live checks (optional, strictly limited)

- **GitHub:** only if `ATTRIBUTION_BACKUP_GITHUB_TOKEN` is already set in your environment.
  - Do one round trip against `4r4cn1d0/attribution-backups`, in a release clearly named as a connector test: probe, upload a tiny file, read it back and hash it, show that a duplicate is refused, list it, and discard the staging objects.
  - Report what ran. The token must appear nowhere.
- **RunPod:** only if `RUNPOD_API_KEY` is already set. Only read-only queries are allowed: the balance or user record, and lists of pods and network volumes.

  **Never create, start, stop, update or delete anything; no spend.**

  Report the field shapes, not the account details.
- **If a variable is absent:** skip the check and say so.
- **Never read credentials** from files in `tmp/` or anywhere else.

### 6. Docs

Update the README and the research note:

- the chosen destination and its limits;
- token setup, with the exact fine-grained token settings the user must create;
- what is now verified locally, and what was checked live, if anything;
- what still waits for the funded one-pod validation;
- the shutdown gap.

## Report back

Send the report to "General Implementation" with SendMessage. Include:

- changed and new files with their hashes;
- design choices and rejected alternatives;
- the API facts you verified, with sources;
- commands and their exit statuses;
- which live checks ran and their results;
- open questions for the user, especially balance recognition and the shutdown option;
- the weakest assumption, a counterexample, and the check that would settle it.
