#!/usr/bin/env bash
# Environment and pinned model downloads for one headroom host. Pass --with-generator on the lead host only.
set -euo pipefail
cd /workspace/attribution-headroom
bash bootstrap_hr.sh
/workspace/attribution-headroom/venv/bin/python download_models_hr.py "$@"
