"""Entry point of the explainer film for render.py: it imports every scene module that exists in scenes/.

    tmp/explainer-venv/bin/python writing/substack/explainer-video/render.py S03

Each scene lives in ``scenes/sNN.py`` and defines the Narrated class ``SNN`` (S01 to S11). A module that does not
exist yet is skipped, and a module that fails to import is reported on stderr and skipped, so one unfinished scene
never stops the others from rendering. (Rendering the broken scene itself then stops in render.py with "has no
scene class SNN", after the reason printed here.)

The ``manim`` command lists only the classes that a file defines, not the ones it imports: render.py handles this.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
import traceback
from pathlib import Path

_VID = Path(__file__).resolve().parent
if str(_VID) not in sys.path:
    sys.path.insert(0, str(_VID))

from kit import *  # noqa: E402,F401,F403  (registers the fonts before any scene builds text)

KEYS = [f"S{i:02d}" for i in range(1, 12)]
LOADED: list[str] = []
MISSING: list[str] = []
BROKEN: dict[str, str] = {}

for _key in KEYS:
    _name = f"scenes.{_key.lower()}"
    if not (_VID / "scenes" / f"{_key.lower()}.py").exists():
        MISSING.append(_key)
        continue
    try:
        _module = importlib.import_module(_name)
        globals()[_key] = getattr(_module, _key)
        LOADED.append(_key)
    except Exception as _exc:  # noqa: BLE001  (a broken scene must not stop the others)
        BROKEN[_key] = f"{type(_exc).__name__}: {_exc}"
        sys.stderr.write(f"[explainer.py] scenes/{_key.lower()}.py did not import, {_key} is skipped:\n"
                         + "".join(traceback.format_exception(_exc)[-6:]))
