#!/usr/bin/env bash
# Environment and pinned model downloads for one kill-test Stage 0 host (no generator).
set -euo pipefail
cd /workspace/attribution-headroom
bash bootstrap_hr.sh
/workspace/attribution-headroom/venv/bin/python download_models_kt.py
