#!/usr/bin/env bash
# The 2 October environment bootstrap (pinned torch and lock) with the Gate B pins (brief B5, [D5], [D9] B-3).
# Both pip installs take -c /workspace/attribution-headroom/constraints.txt, which holds setuptools==78.1.0 and nothing
# else. pip is neither reinstalled nor pinned unless GATEB_PIP_PIN is set (the kit setting bootstrap.pip_pin, a recorded
# lead decision; the generated worker bootstrap exports it only then): exactly one pip install runs before the two
# installs. After pip freeze, the lock must hold the constraint's setuptools line and no wheel line (wheel is pinned
# absent). GATEB_RUN_ROOT moves the run folder for the CPU tests only.
set -euo pipefail
RUN="${GATEB_RUN_ROOT:-/workspace/attribution-headroom}"
PY="$RUN/venv/bin/python"
CONSTRAINTS="$RUN/constraints.txt"
LOCK="$RUN/environment-linux.lock"
mkdir -p "$RUN"
if [ "$(grep -c . "$CONSTRAINTS")" != 1 ] || ! grep -qxE 'setuptools==[0-9][0-9.]*' "$CONSTRAINTS"; then
  echo "constraints.txt must hold exactly one line, setuptools==VERSION" >&2; exit 3
fi
python -m venv "$RUN/venv"
if [ -n "${GATEB_PIP_PIN:-}" ]; then
  "$PY" -m pip install "pip==${GATEB_PIP_PIN}"
fi
"$PY" -m pip install 'torch==2.8.0' --index-url https://download.pytorch.org/whl/cu128 -c "$CONSTRAINTS"
"$PY" -m pip install -r "$RUN/requirements.lock" -c "$CONSTRAINTS"
"$PY" -m pip check
"$PY" -m pip freeze > "$LOCK"
if ! grep -qxF "$(cat "$CONSTRAINTS")" "$LOCK"; then
  echo "the lock's setuptools line is not the constraint's ($(cat "$CONSTRAINTS")): refusing" >&2; exit 3
fi
if grep -qiE '^wheel([=<>~!@ ]|$)' "$LOCK"; then
  echo "the lock has a wheel line (wheel is pinned absent): refusing" >&2; exit 3
fi
"$PY" -m pip --version > "$RUN/pip-version.txt"
"$PY" - <<'PY'
import json,platform,torch
p=torch.cuda.get_device_properties(0)
assert torch.cuda.device_count()==1
assert torch.cuda.is_bf16_supported()
print(json.dumps({'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':p.name,'memory_bytes':p.total_memory,'bf16_supported':torch.cuda.is_bf16_supported()}))
PY
