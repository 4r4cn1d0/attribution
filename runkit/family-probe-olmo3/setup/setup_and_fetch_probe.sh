#!/usr/bin/env bash
# Environment and the open pinned downloads for one family-probe host (gated repositories come later, over ssh stdin).
set -euo pipefail
cd /workspace/attribution-headroom
bash bootstrap_hr.sh
/workspace/attribution-headroom/venv/bin/python download_models_probe.py
