"""Puts the repository root that holds scripts/ on sys.path (so scripts.stage1_s1.d1_spool, scripts.stage1 and the engine
import without PYTHONPATH), and the W1 test folder scripts/stage1/tests (read-only), whose synthetic fixtures these
tests reuse. The W1 folder is found through the importable scripts.stage1 package, so under this package's mutation
runner (a copy that holds only scripts/stage1_s1/d1_spool) it is the workspace's."""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
W1_TESTS = Path(importlib.util.find_spec("scripts.stage1").origin).resolve().parent / "tests"
if str(W1_TESTS) not in sys.path:
    sys.path.append(str(W1_TESTS))
