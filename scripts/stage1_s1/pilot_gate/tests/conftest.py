"""Puts the repository root that holds scripts/ first on sys.path (so a mutation copy tests its own package), then
this folder (synth_world) and the input builder's tests folder (synth_kit, whose engine-layout writers synth_world
reuses). ``world`` is one synthetic pilot world per test session; ``edited`` copies it for a test that edits it."""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
for folder in (HERE, HERE.parents[1] / "reading_input" / "tests"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))


@pytest.fixture(scope="session")
def world(tmp_path_factory):
    import synth_world as sw
    return sw.make(tmp_path_factory.mktemp("pilot") / "w")


@pytest.fixture
def edited(world, tmp_path):
    import synth_world as sw
    return sw.copy(world, tmp_path / "w")
