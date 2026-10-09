#!/bin/bash
# The Granite judge pod's job (written 9 October 2026, 13:00 UTC, clock checked). judge_pod.py --judge granite unpacks
# the bundle into /workspace/judge/bundle, runs pod_job.py verify, then starts this script under nohup and polls
# DONE.json. It never contacts RunPod. The HarmBench job (pod_run.sh) and its venv are not touched.
#   venv:     the Granite venv, an isolated venv on the container disk ($VG; no system site-packages, so no torch),
#             separate from the HarmBench venv (/workspace/judge/venv)
#   pip:      the Mac judge venv's packages at its versions, --no-deps, binary wheels only (out/pip.log)
#   nvcc:     the CUDA compiler: /usr/local/cuda/bin/nvcc, else nvcc on PATH, else the CUDA 12.8 compiler packages from
#             the image's apt sources (out/llama-build.log records which, and nvcc --version)
#   llama:    the pinned llama-cpp-python 0.3.36 sdist (granite_pod.py fetch-sdist: its SHA-256 checked), built with
#             CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80" and at most MAX_BUILD_JOBS (16) parallel
#             compile jobs (nproc in a container can report the host's CPUs; each nvcc job of ggml-cuda can take 1 to
#             4 GB) into out/llama-build.log, which also gets nproc, the jobs and the build's seconds (a failed build
#             included); the venv's pip freeze, then granite_pod.py llama-record (version, GPU offload, CUDA version,
#             build log SHA-256, nproc, jobs, build seconds; refuses a build without GPU offload) into
#             out/llama-build.json
#   download: the pinned GGUF by its commit with no token and HF_HUB_OFFLINE unset; size and SHA-256 checked
#             (out/gguf-check.json, written on a refusal too: its reason and the size and SHA-256 found)
#   run:      pod_job.py run with HF_HUB_OFFLINE=1 into out/granite-pod.jsonl, out/granite-inputs.jsonl and
#             out/run-record.json
# DONE.json records the exit code and the step it ended in; pod_job.py writes counts and ids only to out/job.log.
# Extra arguments (--limit N) go to pod_job.py run. Revised 9 October 2026 (13:54 UTC, clock checked) after the review:
# the bounded build parallelism and its record, and cuda-driver-dev-12-8 (the libcuda stub for the link) in the apt
# fallback.
set -uo pipefail
cd "${JUDGE_ROOT:-/workspace/judge}" || exit 1      # JUDGE_ROOT, GRANITE_VENV, GRANITE_SRC, GRANITE_*NVCC: tests only
VG="${GRANITE_VENV:-/root/granite-venv}"
SRC="${GRANITE_SRC:-/root/granite-src}"
STEP=start
finish() {
  code=$?
  printf '{"exit": %d, "step": "%s", "utc": "%s"}\n' "$code" "$STEP" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > DONE.json.tmp
  mv DONE.json.tmp DONE.json
}
trap finish EXIT
set -e
mkdir -p out
printf '{"utc": "%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > STARTED.json
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_HOME HF_HUB_CACHE TRANSFORMERS_CACHE
export HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
P=bundle/tool/pod
CMAKE_PINNED='-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80'
APT_CUDA='cuda-nvcc-12-8 cuda-cudart-dev-12-8 cuda-driver-dev-12-8 libcublas-dev-12-8 build-essential'
MAX_BUILD_JOBS=16

STEP=venv; echo "$STEP" > STEP
[ -x "$VG/bin/python" ] || python3 -m venv "$VG"

STEP=pip; echo "$STEP" > STEP
"$VG/bin/python" -m pip install --no-deps --only-binary=:all: --no-input --disable-pip-version-check \
  -r "$P/granite-requirements.txt" >> out/pip.log 2>&1

STEP=nvcc; echo "$STEP" > STEP
NVCC="${GRANITE_NVCC:-/usr/local/cuda/bin/nvcc}"
NVCC_SOURCE=image
if [ ! -x "$NVCC" ] && command -v nvcc > /dev/null 2>&1; then NVCC="$(command -v nvcc)"; fi
if [ ! -x "$NVCC" ]; then
  NVCC_SOURCE=apt
  apt-get update >> out/llama-build.log 2>&1
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $APT_CUDA >> out/llama-build.log 2>&1
  NVCC="${GRANITE_APT_NVCC:-/usr/local/cuda-12.8/bin/nvcc}"
fi
echo "nvcc_source=$NVCC_SOURCE nvcc=$NVCC" >> out/llama-build.log
"$NVCC" --version >> out/llama-build.log 2>&1

STEP=llama; echo "$STEP" > STEP
python3 -I -B "$P/granite_pod.py" fetch-sdist --dest "$SRC" >> out/job.log 2>&1
NPROC="$(nproc 2> /dev/null || echo 1)"
case "$NPROC" in ''|*[!0-9]*) NPROC=1;; esac
JOBS="$NPROC"
if [ "$JOBS" -gt "$MAX_BUILD_JOBS" ]; then JOBS="$MAX_BUILD_JOBS"; fi
if [ "$JOBS" -lt 1 ]; then JOBS=1; fi
echo "nproc=$NPROC build_jobs=$JOBS" >> out/llama-build.log
BUILD_T0="$(date +%s)"
PATH="$(dirname "$NVCC"):$PATH" CUDACXX="$NVCC" CMAKE_ARGS="$CMAKE_PINNED" FORCE_CMAKE=1 \
  CMAKE_BUILD_PARALLEL_LEVEL="$JOBS" "$VG/bin/python" -m pip install --no-deps --no-input \
  --disable-pip-version-check --no-cache-dir -v "$SRC/llama_cpp_python-0.3.36.tar.gz" >> out/llama-build.log 2>&1 \
  || { rc=$?; echo "build_seconds=$(( $(date +%s) - BUILD_T0 )) build_exit=$rc" >> out/llama-build.log; exit "$rc"; }
BUILD_S="$(( $(date +%s) - BUILD_T0 ))"
echo "build_seconds=$BUILD_S build_exit=0" >> out/llama-build.log
"$VG/bin/python" -m pip freeze --all > out/environment-pod.lock
"$VG/bin/python" -B "$P/granite_pod.py" llama-record --build-log out/llama-build.log --nvcc "$NVCC" \
  --nproc "$NPROC" --build-jobs "$JOBS" --build-seconds "$BUILD_S" --record out/llama-build.json >> out/job.log 2>&1

STEP=download; echo "$STEP" > STEP
env -u HF_HUB_OFFLINE -u TRANSFORMERS_OFFLINE "$VG/bin/python" -B "$P/pod_job.py" download --bundle bundle \
  --record out/gguf-check.json >> out/job.log 2>&1

STEP=run; echo "$STEP" > STEP
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "$VG/bin/python" -B "$P/pod_job.py" run --bundle bundle \
  --cache out/granite-pod.jsonl --record out/run-record.json "$@" >> out/job.log 2>&1

STEP=done; echo "$STEP" > STEP
