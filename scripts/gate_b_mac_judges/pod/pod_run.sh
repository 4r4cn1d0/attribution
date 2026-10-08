#!/bin/bash
# The judge pod's job (written 8 October 2026; revised 8 October 2026, 20:51 UTC, clock checked: the torch step and
# the text-path check). judge_pod.py unpacks the bundle into /workspace/judge/bundle, runs pod_job.py verify, then
# starts this script under nohup and polls DONE.json. It never contacts RunPod.
#   venv:     a venv over the image's system site-packages (the image's torch 2.8.0 + CUDA 12.8). If the image carries
#             sentencepiece or protobuf (pod_judge.py text-path), an isolated venv instead: the Mac venv has neither,
#             so the tokenizer must be built without them (pod_judge.require_pod_packages refuses either)
#   torch:    import torch in the venv; if it is missing or not 2.8.0, pip install torch==2.8.0 from
#             https://download.pytorch.org/whl/cu128 (as the kits' bootstrap does), then the check again (out/pip.log)
#   pip:      the judge's packages at the Mac venv's versions, --no-deps, binary wheels only (out/pip.log)
#   download: the pinned HarmBench snapshot with no token and HF_HUB_OFFLINE unset; every file's SHA-256 checked
#   run:      pod_job.py run with HF_HUB_OFFLINE=1 into out/harmbench-pod.jsonl and out/run-record.json
# DONE.json records the exit code and the step it ended in; pod_job.py writes counts and ids only to out/job.log.
# Extra arguments (--limit N) go to pod_job.py run.
set -uo pipefail
cd "${JUDGE_ROOT:-/workspace/judge}" || exit 1      # JUDGE_ROOT: tests only
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
TORCH_CHECK='import sys, torch; sys.exit(0 if torch.__version__.split("+")[0] == "2.8.0" else 1)'

STEP=venv; echo "$STEP" > STEP
[ -x venv/bin/python ] || python3 -m venv --system-site-packages venv
if ! venv/bin/python -B "$P/pod_judge.py" text-path; then
  rm -rf venv
  python3 -m venv venv
fi

STEP=torch; echo "$STEP" > STEP
if ! venv/bin/python -c "$TORCH_CHECK" >> out/pip.log 2>&1; then
  venv/bin/python -m pip install --no-input --disable-pip-version-check --no-cache-dir 'torch==2.8.0' \
    --index-url https://download.pytorch.org/whl/cu128 >> out/pip.log 2>&1
  venv/bin/python -c "$TORCH_CHECK" >> out/pip.log 2>&1
fi

STEP=pip; echo "$STEP" > STEP
venv/bin/python -m pip install --no-deps --only-binary=:all: --no-input --disable-pip-version-check \
  -r "$P/judge-requirements.txt" >> out/pip.log 2>&1
venv/bin/python -m pip freeze --all > out/environment-pod.lock

STEP=download; echo "$STEP" > STEP
env -u HF_HUB_OFFLINE -u TRANSFORMERS_OFFLINE venv/bin/python -B "$P/pod_job.py" download --bundle bundle \
  --record out/snapshot-check.json >> out/job.log 2>&1

STEP=run; echo "$STEP" > STEP
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 venv/bin/python -B "$P/pod_job.py" run --bundle bundle \
  --cache out/harmbench-pod.jsonl --record out/run-record.json "$@" >> out/job.log 2>&1

STEP=done; echo "$STEP" > STEP
