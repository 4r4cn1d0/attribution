#!/usr/bin/env bash
# The 2 October environment bootstrap (pinned torch and lock), with the headroom run's folder.
set -euo pipefail
mkdir -p /workspace/attribution-headroom
python -m venv /workspace/attribution-headroom/venv
/workspace/attribution-headroom/venv/bin/python -m pip install 'torch==2.8.0' --index-url https://download.pytorch.org/whl/cu128
/workspace/attribution-headroom/venv/bin/python -m pip install -r /workspace/attribution-headroom/requirements.lock
/workspace/attribution-headroom/venv/bin/python -m pip check
/workspace/attribution-headroom/venv/bin/python -m pip freeze > /workspace/attribution-headroom/environment-linux.lock
/workspace/attribution-headroom/venv/bin/python - <<'PY'
import json,platform,torch
p=torch.cuda.get_device_properties(0)
assert torch.cuda.device_count()==1
assert torch.cuda.is_bf16_supported()
print(json.dumps({'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':p.name,'memory_bytes':p.total_memory,'bf16_supported':torch.cuda.is_bf16_supported()}))
PY
