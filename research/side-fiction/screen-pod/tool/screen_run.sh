#!/bin/bash
# The fiction screen's pod job (rebuilt 9 October 2026, 10:27 UTC, clock checked, from the lead's partial build;
# revised 9 October 2026, 17:11 UTC, clock checked: ONE Granite-on-CUDA backend, the lead's Granite pod mode).
# screen_pod.py unpacks the bundle into /workspace/screen/bundle, runs screen_job.py verify, then starts this script
# under nohup and polls DONE.json. It never contacts RunPod. Steps, in order (DONE.json records the exit code and the
# step it ended in):
#   venv-guard:  a venv over the image's site-packages (torch 2.8.0, or installed from the cu128 index), then the
#                engine's requirements.lock versions that the guard path imports, binary wheels, --no-deps
#   download:    the pinned Qwen3Guard snapshot with no token and HF_HUB_OFFLINE unset; every file's SHA-256 checked
#   granite-job: the lead's own Granite pod job, unchanged: bundle/gate_b/tool/pod/pod_run_granite.sh in its default
#                root /workspace/judge, whose bundle/ is a link to this bundle's gate_b/ (the lead's Granite bundle,
#                no requested unit): its venv (/root/granite-venv), pip, nvcc, the llama.cpp CUDA build from the
#                pinned sdist, the GGUF download (/root/granite-gguf), then pod_job.py run, which checks the packages,
#                the GPU offload, the files and the tokenizer fingerprint and runs the lead's known-answer gate (its
#                exit 3 when the gate fails). It runs under one time limit; its exit code goes to the ka step, which
#                always runs. granite-job/ (here) links to its root, so status and sums reach its files.
#   ka:          the lead's gate read and timed (screen_job.py ka): exit 4 when the gate failed, 3 when it passed but
#                the round is projected too slow, 5, 2 or 1 when the lead's job was stopped, refused or failed. The
#                script ends there: no row is screened.
#   granite:     Granite harm and sexual_content on the fiction (or refill) rows, in the lead's Granite venv, through
#                the lead's granite_pod.judge_triples
#   qwen:        Qwen3Guard through the engine's GuardScorer on every row of the round
# The guard venv sits on the container disk (/root), not on the /workspace volume, where the 8 Oct judge pod's pip took
# 14 min. CUBLAS_WORKSPACE_CONFIG is exported here: the pod's create-time env does not reach an ssh-started job (the
# 8 Oct judge pod's run record shows it null), and the engine's configure_cuda refuses without it.
# Every setup step (the guard venv and its installs, the download, the lead's whole Granite job) runs under
# `timeout -k 60 LIMIT`: a step that hangs ends with exit 124 (137 if it ignores SIGTERM), the job ends, and the
# launcher stops the pod through its normal path instead of waiting for the cap. The judge steps (granite, qwen) are
# bounded by the launcher's SIGTERM before the cap, which also reaches the lead's gate (pod_job.py run).
# The exit trap writes out/run-record.json (screen_job.py record) and then DONE.json, whatever happened.
set -uo pipefail
cd "${SCREEN_ROOT:-/workspace/screen}" || exit 1      # SCREEN_ROOT, SYS_PYTHON, SCREEN_VENVS, SCREEN_JUDGE_ROOT: tests only
STEP=start
finish() {
  code=$?
  "${SYS_PYTHON:-python3}" -I bundle/tool/screen_job.py record --root . --exit "$code" --step "$STEP" >> out/job.log 2>&1 || true
  printf '{"exit": %d, "step": "%s", "utc": "%s"}\n' "$code" "$STEP" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > DONE.json.tmp
  mv DONE.json.tmp DONE.json
}
trap finish EXIT
set -e
mkdir -p out
printf '{"utc": "%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > STARTED.json
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_HOME HF_HUB_CACHE HUGGINGFACE_HUB_CACHE TRANSFORMERS_CACHE XDG_CACHE_HOME
unset TORCH_ALLOW_TF32_CUBLAS_OVERRIDE NVIDIA_TF32_OVERRIDE
export HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8 CUDA_VISIBLE_DEVICES=0
export PATH="/usr/local/cuda/bin:$PATH"
T=bundle/tool
SYSPY="${SYS_PYTHON:-python3}"
VG="${GRANITE_VENV:-/root/granite-venv}"
VQ="${SCREEN_VENVS:-/root/screen-venvs}/q"
JR="${SCREEN_JUDGE_ROOT:-/workspace/judge}"
PIPI="-m pip install --no-input --disable-pip-version-check --no-cache-dir"
TORCH_CHECK='import sys, torch; sys.exit(0 if torch.__version__.split("+")[0] == "2.8.0" else 1)'
TO="timeout -k 60"
T_VENV=600; T_PIP=1800; T_SHORT=600; T_TORCH=2400; T_DOWNLOAD=3600; T_GRANITE_JOB=5400

STEP=venv-guard; echo "$STEP" > STEP
[ -x "$VQ/bin/python" ] || $TO $T_VENV "$SYSPY" -m venv --system-site-packages "$VQ"
if ! $TO $T_SHORT "$VQ/bin/python" -c "$TORCH_CHECK" >> out/pip.log 2>&1; then
  $TO $T_TORCH "$VQ/bin/python" $PIPI 'torch==2.8.0' --index-url https://download.pytorch.org/whl/cu128 >> out/pip.log 2>&1
  $TO $T_SHORT "$VQ/bin/python" -c "$TORCH_CHECK" >> out/pip.log 2>&1
fi
$TO $T_PIP "$VQ/bin/python" $PIPI --no-deps --only-binary=:all: -r "$T/guard-requirements.txt" >> out/pip.log 2>&1
$TO $T_SHORT "$VQ/bin/python" -m pip freeze --all > out/environment-q.lock

STEP=download; echo "$STEP" > STEP
$TO $T_DOWNLOAD env -u HF_HUB_OFFLINE -u TRANSFORMERS_OFFLINE PYTHONPATH=bundle/engine "$VQ/bin/python" -B \
  "$T/screen_job.py" download --bundle bundle --record out/download-check.json >> out/job.log 2>&1

STEP=granite-job; echo "$STEP" > STEP
mkdir -p "$JR"
[ ! -e "$JR/bundle" ] || [ -L "$JR/bundle" ]
ln -sfn "$PWD/bundle/gate_b" "$JR/bundle"
ln -sfn "$JR" granite-job
GRC=0
JUDGE_ROOT="$JR" $TO $T_GRANITE_JOB bash bundle/gate_b/tool/pod/pod_run_granite.sh || GRC=$?

export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
STEP=ka; echo "$STEP" > STEP
"$SYSPY" -I -B "$T/screen_job.py" ka --bundle bundle --granite-root granite-job --granite-exit "$GRC" \
  --record out/ka.json >> out/job.log 2>&1

STEP=granite; echo "$STEP" > STEP
"$VG/bin/python" -B "$T/screen_job.py" granite --bundle bundle --ka out/ka.json --cache out/granite.jsonl \
  --record out/granite-record.json >> out/job.log 2>&1

STEP=qwen; echo "$STEP" > STEP
PYTHONPATH=bundle/engine "$VQ/bin/python" -B "$T/screen_job.py" qwen --bundle bundle --ka out/ka.json \
  --cache out/qwen.jsonl --record out/qwen-record.json >> out/job.log 2>&1

STEP=done; echo "$STEP" > STEP
