#!/bin/bash
# The fiction screen's pod job (rebuilt 9 October 2026, 10:27 UTC, clock checked, from the lead's partial build).
# screen_pod.py unpacks the bundle into /workspace/screen/bundle, runs screen_job.py verify, then starts this script
# under nohup and polls DONE.json. It never contacts RunPod. Steps, in order (DONE.json records the exit code and the
# step it ended in):
#   venv-granite: an isolated venv with the judge venv's packages (transformers 5.18.0 ...), binary wheels, --no-deps
#   llama-build:  llama-cpp-python 0.3.36 from its sdist, pinned by SHA-256 (--require-hashes), built with CUDA for
#                 the A100 only (CMAKE_ARGS below); nvcc from the image (/usr/local/cuda/bin), or, when the image has
#                 none, the CUDA 12.8 compiler packages from the image's apt sources (recorded as nvcc_source apt);
#                 out/llama-build.log; then screen_job.py llama-info (version, GPU offload, nvcc, build log SHA-256)
#   venv-guard:   a venv over the image's site-packages (torch 2.8.0, or installed from the cu128 index), then the
#                 engine's requirements.lock versions that the guard path imports, binary wheels, --no-deps
#   download:     the three pinned snapshots with no token and HF_HUB_OFFLINE unset; every file's SHA-256 checked
#   ka:           the known-answer check (exit 4 when it fails, 2 without GPU offload: the script ends, no row is screened)
#   granite:      Granite harm and sexual_content on the fiction (or refill) rows
#   qwen:         Qwen3Guard through the engine's GuardScorer on every row of the round
# Both venvs sit on the container disk (/root), not on the /workspace volume, where the 8 Oct judge pod's pip took
# 14 min. CUBLAS_WORKSPACE_CONFIG is exported here: the pod's create-time env does not reach an ssh-started job (the
# 8 Oct judge pod's run record shows it null), and the engine's configure_cuda refuses without it.
# The exit trap writes out/run-record.json (screen_job.py record) and then DONE.json, whatever happened.
set -uo pipefail
cd "${SCREEN_ROOT:-/workspace/screen}" || exit 1      # SCREEN_ROOT, SYS_PYTHON, SCREEN_VENVS, SCREEN_NVCC: tests only
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
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_HOME HF_HUB_CACHE TRANSFORMERS_CACHE XDG_CACHE_HOME
unset TORCH_ALLOW_TF32_CUBLAS_OVERRIDE NVIDIA_TF32_OVERRIDE
export HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8 CUDA_VISIBLE_DEVICES=0
export PATH="/usr/local/cuda/bin:$PATH"
T=bundle/tool
SYSPY="${SYS_PYTHON:-python3}"
VG="${SCREEN_VENVS:-/root/screen-venvs}/g"
VQ="${SCREEN_VENVS:-/root/screen-venvs}/q"
PIPI="-m pip install --no-input --disable-pip-version-check --no-cache-dir"
TORCH_CHECK='import sys, torch; sys.exit(0 if torch.__version__.split("+")[0] == "2.8.0" else 1)'
CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80"
APT_CUDA="cuda-nvcc-12-8 cuda-cudart-dev-12-8 libcublas-dev-12-8 cuda-driver-dev-12-8 build-essential"

STEP=venv-granite; echo "$STEP" > STEP
[ -x "$VG/bin/python" ] || "$SYSPY" -m venv "$VG"
"$VG/bin/python" $PIPI --no-deps --only-binary=:all: -r "$T/granite-requirements.txt" >> out/pip.log 2>&1

STEP=llama-build; echo "$STEP" > STEP
NVCC="${SCREEN_NVCC:-/usr/local/cuda/bin/nvcc}"
NVCC_SOURCE=image
if [ ! -x "$NVCC" ]; then
  NVCC_SOURCE=apt
  { apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $APT_CUDA; } \
    > out/llama-build.log 2>&1
  [ -x "$NVCC" ] || NVCC="${NVCC%/cuda/bin/nvcc}/cuda-12.8/bin/nvcc"
fi
[ -x "$NVCC" ]
export CUDACXX="$NVCC" PATH="$(dirname "$NVCC"):$PATH"
CMAKE_ARGS="$CMAKE_ARGS" FORCE_CMAKE=1 CMAKE_BUILD_PARALLEL_LEVEL="$(nproc 2>/dev/null || echo 8)" \
  "$VG/bin/python" $PIPI --no-deps --no-binary=llama-cpp-python --require-hashes -v \
  -r "$T/llama-requirements.txt" >> out/llama-build.log 2>&1
"$VG/bin/python" -m pip freeze --all > out/environment-g.lock
"$VG/bin/python" -B "$T/screen_job.py" llama-info --cmake-args "$CMAKE_ARGS" --nvcc-source "$NVCC_SOURCE" \
  --build-log out/llama-build.log --record out/llama-info.json >> out/job.log 2>&1

STEP=venv-guard; echo "$STEP" > STEP
[ -x "$VQ/bin/python" ] || "$SYSPY" -m venv --system-site-packages "$VQ"
if ! "$VQ/bin/python" -c "$TORCH_CHECK" >> out/pip.log 2>&1; then
  "$VQ/bin/python" $PIPI 'torch==2.8.0' --index-url https://download.pytorch.org/whl/cu128 >> out/pip.log 2>&1
  "$VQ/bin/python" -c "$TORCH_CHECK" >> out/pip.log 2>&1
fi
"$VQ/bin/python" $PIPI --no-deps --only-binary=:all: -r "$T/guard-requirements.txt" >> out/pip.log 2>&1
"$VQ/bin/python" -m pip freeze --all > out/environment-q.lock

STEP=download; echo "$STEP" > STEP
env -u HF_HUB_OFFLINE -u TRANSFORMERS_OFFLINE PYTHONPATH=bundle/engine "$VQ/bin/python" -B "$T/screen_job.py" \
  download --bundle bundle --record out/download-check.json >> out/job.log 2>&1

export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
STEP=ka; echo "$STEP" > STEP
"$VG/bin/python" -B "$T/screen_job.py" ka --bundle bundle --record out/ka.json --labels out/ka-labels.jsonl \
  >> out/job.log 2>&1

STEP=granite; echo "$STEP" > STEP
"$VG/bin/python" -B "$T/screen_job.py" granite --bundle bundle --ka out/ka.json --cache out/granite.jsonl \
  --record out/granite-record.json >> out/job.log 2>&1

STEP=qwen; echo "$STEP" > STEP
PYTHONPATH=bundle/engine "$VQ/bin/python" -B "$T/screen_job.py" qwen --bundle bundle --ka out/ka.json \
  --cache out/qwen.jsonl --record out/qwen-record.json >> out/job.log 2>&1

STEP=done; echo "$STEP" > STEP
