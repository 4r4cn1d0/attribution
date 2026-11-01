"""Puts the repository root that holds this scripts/stage1_s1 first on sys.path (so a mutation copy tests its own
package), then the engine's test folder (for its ENGINEERING FIXTURES, ss_fixtures), found from wherever the engine
package is imported (the workspace, also under the mutation runner)."""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
_engine = importlib.util.find_spec("experiments.safety_selection")
ENGINE_TESTS = Path(_engine.origin).resolve().parent / "tests"
if str(ENGINE_TESTS) not in sys.path:
    sys.path.insert(1, str(ENGINE_TESTS))
