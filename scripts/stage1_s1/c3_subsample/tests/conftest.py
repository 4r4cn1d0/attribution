"""Puts the repository root that holds scripts/ on sys.path (so scripts.stage1_s1.c3_subsample, scripts.stage1 and the
engine import without PYTHONPATH), this folder, and the engine's own test folder experiments/safety_selection/tests
(read-only), whose synthetic prepared-set builders (ss_fixtures) these tests reuse. The engine test folder is found
through the importable experiments.safety_selection package, so under this package's mutation runner (a copy that
holds only scripts/stage1_s1/c3_subsample) it is the workspace's."""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
ENGINE_TESTS = Path(importlib.util.find_spec("experiments.safety_selection").origin).resolve().parent / "tests"
if str(ENGINE_TESTS) not in sys.path:
    sys.path.append(str(ENGINE_TESTS))
