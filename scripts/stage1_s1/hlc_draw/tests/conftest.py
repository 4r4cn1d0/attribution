"""Puts the repository root that holds scripts/ first on sys.path (so a mutation copy tests its own package), then the
B16 input builder's test folder (for synth_kit) and this folder (for hlc_world)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[1] / "reading_input" / "tests", HERE):
    if str(folder) not in sys.path:
        sys.path.insert(1, str(folder))
