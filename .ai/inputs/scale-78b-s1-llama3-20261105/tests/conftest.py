"""Puts the repository root on sys.path (the engine and scripts.stage1), since .ai/inputs/ is not a package. Run from the
repository root with the main environment (the Llama codec needs transformers):
  <main venv python> -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-s1-llama3-20261105/tests
The tests read the git-ignored prepared sets under tmp/kt-prepared/ and a copy of stage 1's committed S1 edit (a stage-1
S1 unit's edit.json, found under tmp/stage1-olmo/ of this checkout or of the main checkout) and skip when absent."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
