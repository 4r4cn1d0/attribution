"""Puts the repository root that holds scripts/ on sys.path, so plain pytest finds scripts.stage1_s1.reading and
scripts.stage1.dose_axis without PYTHONPATH."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
