"""Track R's tests (the 7-8B reference settings: scripts/scale78b/refs_78b.py, make_refs_settings_78b.py, their settings,
and Llama-3.1-8B's recipe-G config at LR 5e-5). Puts the repository root first on sys.path (so a mutation copy tests its
own scripts/scale78b), then the 1B fixture folders (scripts/stage1_s1/tests: b10_fixtures, b11_fixtures,
oext_fixtures, oext_unit_fixtures; scripts/stage1/tests) and Track O's (scripts/scale78b/tests/oext: oext78_fixtures),
and the engine's tests (ss_fixtures), all read-only. Run from the repository root under the main environment:

  PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests/refs

ENGINEERING FIXTURES only: no unit's answer, generation or guard file is opened; nothing is downloaded."""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
for extra in (REPO / "scripts" / "scale78b" / "tests" / "oext", REPO / "scripts" / "stage1" / "tests",
              REPO / "scripts" / "stage1_s1" / "tests", REPO):
    if str(extra) in sys.path:
        sys.path.remove(str(extra))
    sys.path.insert(0, str(extra))
_engine = importlib.util.find_spec("experiments.safety_selection")
ENGINE_TESTS = Path(_engine.origin).resolve().parent / "tests"
if str(ENGINE_TESTS) not in sys.path:
    sys.path.append(str(ENGINE_TESTS))

# Bind the scripts.scale78b package to this repository root now (a mutation copy must test its own files).
import importlib  # noqa: E402

_pkg = importlib.import_module("scripts.scale78b")
assert Path(_pkg.__file__).resolve().parents[2] == REPO.resolve(), (_pkg.__file__, REPO)
