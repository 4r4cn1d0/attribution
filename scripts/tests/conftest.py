"""Puts the repository root on sys.path, so plain pytest finds the engine and the flat scripts under scripts/ without
PYTHONPATH (the same rule as scripts/stage1/tests/conftest.py). The tests here cover the flat scripts that have no
package of their own (the OLMo 3 preflight and its tiny-model checks); they build everything locally, download nothing
and skip when a cached snapshot they need is absent."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
