"""Puts the repository root on sys.path (the engine), since .ai/inputs/ is not a package. Run from the repository root:
  <main venv python> -B -m pytest -q .ai/inputs/scale-78b-sealed-llama3-20261105/tests
The tests read the git-ignored prepared sets under tmp/kt-prepared/ and skip when they are absent."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
