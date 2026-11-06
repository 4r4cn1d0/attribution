#!/usr/bin/env bash
# Environment (bootstrap_hr.sh: the constraint, then the lock checks) and the OPEN pinned downloads for one 7-8B host
# (the base model too when the host runs Safe LoRA: --with-base). A gated repository (llama31-8b's policy) is never
# downloaded here: it comes later, over ssh's stdin (host.py gated-download -> download_models_stage1.py --gated
# --token-stdin), before the preflight. No token is in this environment (download_models_stage1.py checks).
set -euo pipefail
cd /workspace/attribution-headroom
bash bootstrap_hr.sh
/workspace/attribution-headroom/venv/bin/python download_models_stage1.py "$@"
