"""Puts the repository root that holds scripts/ first on sys.path (so a mutation copy tests its own package), then
this folder (for synth_kit)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
