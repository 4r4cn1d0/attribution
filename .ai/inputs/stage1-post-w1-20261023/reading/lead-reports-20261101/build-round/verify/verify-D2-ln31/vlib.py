"""Verifier helpers for track D2-ln31 (synthetic data only). Puts the builder's workspace (ws-d2) on sys.path the way
its conftest does, so the tool under test, synth_kit and hlc_world import from there (read only; -B, no bytecode)."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

SCRATCH = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/"
               "ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad")
WS = SCRATCH / "builds" / "ws-d2"
HERE = Path(__file__).resolve().parent
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"

for p in (str(WS), str(WS / "scripts" / "stage1_s1" / "reading_input" / "tests"),
          str(WS / "scripts" / "stage1_s1" / "hlc_draw" / "tests")):
    if p not in sys.path:
        sys.path.insert(0 if p == str(WS) else 1, p)

import hlc_world as hw  # noqa: E402
import synth_kit as sk  # noqa: E402

from scripts.stage1_s1.hlc_draw import draw as dr  # noqa: E402


def world_pins(w) -> dict:
    return {"oct9": sk.sha(w.oct9_key.read_bytes()), "manifest": sk.sha(w.bank_manifest.read_bytes()),
            "dev": sk.sha(w.bank.read_bytes())}


def cfg_for(pins: dict) -> dict:
    """The real pinned settings with a synthetic world's three external pins (as the builder's tests do)."""
    cfg = copy.deepcopy(dr.load_settings())
    cfg["exclusions"]["oct9"]["key_sha256"] = pins["oct9"]
    cfg["bank"]["manifest_sha256"] = pins["manifest"]
    cfg["bank"]["dev_sha256"] = pins["dev"]
    return cfg


def save_pins(w, path: Path) -> None:
    path.write_text(json.dumps(world_pins(w)))
