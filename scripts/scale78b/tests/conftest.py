"""Puts the repository root on sys.path, so plain pytest finds scripts.scale78b, scripts.stage1 and the engine without
PYTHONPATH (the rule of scripts/stage1/tests/conftest.py). Serves both tracks' tests. Run from the repository root:
  <main venv python> -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests .ai/inputs/scale-78b-sealed-llama3-20261105/tests
Track B's tests read the git-ignored prepared sets under tmp/kt-prepared/ and skip when they are absent; track C's
parity tests read the Gate B wave-0a and Gate A units on this Mac and skip when they are absent; two of track C's tests
need scipy (the repository's .venv) and skip without it."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
