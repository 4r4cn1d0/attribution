"""Puts the repository root that holds scripts/stage1 on sys.path, so plain pytest finds the scripts.stage1 package
and the engine without PYTHONPATH (the acceptance command still sets PYTHONPATH=.)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
