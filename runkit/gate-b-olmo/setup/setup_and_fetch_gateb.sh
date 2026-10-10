#!/usr/bin/env bash
# Environment (bootstrap_hr.sh: the constraint, then the lock checks) and the open pinned downloads for one Gate B host.
set -euo pipefail
cd /workspace/attribution-headroom
bash bootstrap_hr.sh
/workspace/attribution-headroom/venv/bin/python download_models_gateb.py
