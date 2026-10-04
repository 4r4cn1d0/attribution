# Shutdown watchdog: files to deploy

Since 4 October 2026 the watchdog is the **backup** behind the pod's own stop timer
(`../pod_timer/`); admission never depends on it. `watchdog.py` changed that day (a backup arm is
acknowledged without a recent scheduled scan), and with it the pin in `watchdog.yml`: the copy
deployed on 3 October keeps working but refuses most backup arms until both files are replaced,
which needs a credential with the "Workflows" permission.

These three files are the whole watchdog. They run in the **backup repository**
(`4r4cn1d0/attribution-backups`), not in this project; nothing here imports the project.

| file here | goes to (default branch of the backup repository) |
|---|---|
| `watchdog.py` | `watchdog/watchdog.py` |
| `watchdog.yml` | `.github/workflows/watchdog.yml` |
| `pods.example.json` | `watchdog/pods.json`, with the worker and its pod id filled in |

`pods.json` is the allow-list: `{"workers": {"worker-1": "<pod id>"}}`. The watchdog acknowledges
and stops only a pod named there, under that worker's name. The shipped example is empty, so
nothing can be armed until a pod is named, and until then a scan needs no RunPod key.

**The workflow pins the other two files.** Its verification step holds the SHA-256 of
`watchdog/watchdog.py` and `watchdog/pods.json` and fails the job, before the RunPod key is
used, if either differs. As shipped the pins are those of `watchdog.py` and `pods.example.json`
in this folder (a test keeps them equal), so copy both byte for byte. To add a pod or change the
script: edit the file, run `sha256sum watchdog/watchdog.py watchdog/pods.json` (`shasum -a 256`
on macOS), replace the hash on the matching `pin` line of the workflow, and push the file and the
workflow in one commit with a credential that has the "Workflows" permission. The worker's backup
token must not have that permission.

What it does, the records it writes, the user's steps, the Actions minutes it uses and its limits
are in the package README (`experiments/durability/README.md`, "The shutdown watchdog"). The
worker's side is `experiments/durability/shutdown_watchdog.py`. The tests
(`experiments/durability/tests/test_dur_watchdog.py`) run `watchdog.py` from this folder against
local fakes.

The script uses only the Python standard library and needs no installation on the runner.
