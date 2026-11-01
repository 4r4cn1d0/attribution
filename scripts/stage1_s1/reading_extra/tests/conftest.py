"""Puts the repository root that holds scripts/ first on sys.path (so a mutation copy tests its own package), then
this folder (extra_kit) and the input builder's tests folder (synth_kit, the synthetic stage-1 kit, used as is).
``pipeline(reading)`` is one synthetic world per reading: the builder's --out and --record, then B16's output."""

import json
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
def pipeline(tmp_path_factory):
    """reading -> (world, {tables, sources, reading}: documents, {...}: paths)."""
    import synth_kit as sk
    from scripts.stage1_s1.reading.__main__ import main as b16_main
    from scripts.stage1_s1.reading_input.__main__ import main as builder

    cache = {}

    def get(reading):
        if reading not in cache:
            root = tmp_path_factory.mktemp(f"extra-{reading}")
            s = sk.make(root / "w", reading)
            paths = {k: root / f"{k}.json" for k in ("tables", "sources", "reading")}
            assert builder(s.args(paths["tables"], paths["sources"], overlap=False)) == 0
            assert b16_main(["--input", str(paths["tables"]), "--out", str(paths["reading"])]) == 0
            cache[reading] = (s, {k: json.loads(p.read_text()) for k, p in paths.items()}, paths)
        return cache[reading]
    return get
