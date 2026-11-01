"""Verifier 2 helpers for track D2-ln31 (synthetic data only). Puts ws-d2 on sys.path as its conftest does, so the
tool, synth_kit and hlc_world import from there (read only; run with -B and PYTHONDONTWRITEBYTECODE=1)."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

SCRATCH = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/"
               "ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad")
WS = SCRATCH / "builds" / "ws-d2"
HERE = Path(__file__).resolve().parent
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
SETTINGS = WS / "scripts" / "stage1_s1" / "hlc_draw" / "settings" / "hlc_draw.json"

for p in (str(WS), str(WS / "scripts" / "stage1_s1" / "reading_input" / "tests"),
          str(WS / "scripts" / "stage1_s1" / "hlc_draw" / "tests")):
    if p not in sys.path:
        sys.path.insert(0 if p == str(WS) else 1, p)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def world_pins(w) -> dict:
    return {"oct9": sha(w.oct9_key.read_bytes()), "manifest": sha(w.bank_manifest.read_bytes()),
            "dev": sha(w.bank.read_bytes())}


def settings_with(pins: dict) -> dict:
    """The real settings file (read as JSON here, not through the tool) with a synthetic world's three pins."""
    cfg = json.loads(SETTINGS.read_text())
    cfg = copy.deepcopy(cfg)
    cfg["exclusions"]["oct9"]["key_sha256"] = pins["oct9"]
    cfg["bank"]["manifest_sha256"] = pins["manifest"]
    cfg["bank"]["dev_sha256"] = pins["dev"]
    return cfg


def tool_args(root: Path, command: str, sealed: Path, manifest: Path, step: str = "0") -> list[str]:
    w = root / "world"
    return [command, "--kit", str(w / "kit"), "--oct9-key", str(w / "oct9" / "key.json"), "--bank-manifest",
            str(w / "bank" / "manifest.json"), "--bank", str(w / "bank" / "banks" / "dev.jsonl"), "--auditor",
            str(w / "bank" / "auditor" / "construction.json"), "--sealed", str(sealed), "--manifest", str(manifest),
            "--repo", str(w / "repo"), "--rules", str(w / "repo" / "rules.py"), "--reduction", step]
