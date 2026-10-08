#!/usr/bin/env bash
set -euo pipefail
mkdir -p /workspace/attribution-study-v2
python -m venv /workspace/attribution-study-v2/venv
/workspace/attribution-study-v2/venv/bin/python -m pip install 'torch==2.8.0' --index-url https://download.pytorch.org/whl/cu128
/workspace/attribution-study-v2/venv/bin/python -m pip install -r /workspace/attribution-study-v2/requirements.lock
/workspace/attribution-study-v2/venv/bin/python -m pip check
/workspace/attribution-study-v2/venv/bin/python -m pip freeze > /workspace/attribution-study-v2/environment-linux.lock
/workspace/attribution-study-v2/venv/bin/python - <<'PY'
import json,platform,torch
p=torch.cuda.get_device_properties(0)
assert torch.cuda.device_count()==1
assert torch.cuda.is_bf16_supported()
print(json.dumps({'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':p.name,'memory_bytes':p.total_memory,'bf16_supported':torch.cuda.is_bf16_supported()}))
PY
