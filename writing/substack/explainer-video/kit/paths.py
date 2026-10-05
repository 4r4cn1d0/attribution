"""Where things are (see foundation/INTERFACES.md). All commands run from ROOT."""

from __future__ import annotations

import os
from pathlib import Path

VID = Path(__file__).resolve().parents[1]              # .../writing/substack/explainer-video
ROOT = VID.parents[2]                                  # the project root
BUILD = Path(os.environ.get("EXPLAINER_BUILD", ROOT / "tmp" / "explainer-build-v2")).resolve()
TEX_CACHE = BUILD / "texcache"
TEXLIVE_OTF = Path("/opt/homebrew/Cellar/texlive/20260301/share/texmf-dist/fonts/opentype")


def timings_path() -> Path:
    """The narration timings file: ``EXPLAINER_TIMINGS`` if set, else ``BUILD/audio/timings.json``."""
    return Path(os.environ.get("EXPLAINER_TIMINGS", BUILD / "audio" / "timings.json"))


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() not in ("", "0", "false", "no")
