"""Track E's tests (the 7-8B scorer layer). Puts the repository root on sys.path (the rule of scripts/scale78b/tests/
conftest.py) and, for the parity tests, scripts/stage1/tests (the 1B fixtures: s1fixtures, test_representation_pass's
env and tiny models, test_make_untuned_answers's recipe files and generator) and the engine's tests (ss_fixtures), all
read-only. Run from the repository root under the main environment (transformers 4.56.2):

  PYTHONDONTWRITEBYTECODE=1 <main venv python> -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/scorers

The family tests read the git-ignored prepared sets under tmp/kt-prepared/ (manifest and engine files only; ids,
counts and hashes are printed, never text) and skip when they are absent."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
for extra in (REPO, REPO / "scripts" / "stage1" / "tests", REPO / "experiments" / "safety_selection" / "tests"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
