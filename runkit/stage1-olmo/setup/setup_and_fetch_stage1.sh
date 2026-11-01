#!/usr/bin/env bash
# Environment (bootstrap_hr.sh: the constraint, then the lock checks) and the open pinned downloads for one stage-1 host (the base model too when the host runs Safe LoRA: --with-base).
set -euo pipefail
cd /workspace/attribution-headroom
bash bootstrap_hr.sh
/workspace/attribution-headroom/venv/bin/python download_models_stage1.py "$@"
