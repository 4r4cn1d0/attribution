# Stop timer and job runner: the files that run inside the pod

`pod_job.py` is the job runner the timer's supervisor starts when a pod is created by `launch`:
it fetches the bundles, runs the bootstrap and the worker, and asks the timer to stop the pod if
anything fails. It travels and is checked exactly as the timer is. See the package README,
"Running a host on a pod".

`pod_timer.py` is the whole timer. It runs **inside the GPU pod**, not in this project; it imports
nothing from the project and needs only Python 3.8 or later.

It is not copied to the pod by hand. `python -m experiments.durability pod-timer-settings` packs
it (gzip, base64) into environment variables and writes the start command that unpacks it,
checks its SHA-256 and runs it before the image's own start script. Those settings are given to
RunPod when the pod is created. If the timer cannot be started, or its supervisor ever exits, the
start command asks RunPod to stop the pod.

What it does, the records it keeps on the pod's network volume, the failure table, the keys, the
user's steps and what the funded validation must show are in the package README
(`experiments/durability/README.md`, "Shutdown: the stop timer in the pod"). The worker's side is
`experiments/durability/shutdown_timer.py`. The tests
(`experiments/durability/tests/test_dur_pod_timer.py`) run this file from this folder, with a
manual clock and as real processes.

Changing this file changes the SHA-256 in the generated start command, so a pod must be created
(or its start command and variables replaced) with freshly generated settings.
