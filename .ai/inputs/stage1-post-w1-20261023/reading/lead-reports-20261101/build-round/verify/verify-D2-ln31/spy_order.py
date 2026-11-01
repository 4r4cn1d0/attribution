"""LN-31's order checked below the tool's own read_bytes: every file open, Path.read_bytes/read_text, listdir, scandir
and iterdir is logged while the real command line runs on a synthetic world (argv[1] = world copy, argv[2] = pins,
argv[3] = "unsealed-B" to delete block B's seal entry from plan.json first, or "normal"). Prints the world-relative
paths touched, in order, up to the first unit file. Synthetic data only."""

from __future__ import annotations

import builtins
import io
import json
import os
import pathlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402

from scripts.stage1_s1.hlc_draw import draw as dr  # noqa: E402
from scripts.stage1_s1.hlc_draw.__main__ import main  # noqa: E402

world, pins, mode = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), sys.argv[3]
if mode == "unsealed-B":
    plan = json.loads((world / "kit" / "plan.json").read_text())
    del plan["seals"]["B"]
    (world / "kit" / "plan.json").write_bytes(vlib.sk.jbytes(plan))
dr._SETTINGS = vlib.cfg_for(pins)
log = []
real = {"open": builtins.open, "io_open": io.open, "rb": pathlib.Path.read_bytes, "rt": pathlib.Path.read_text,
        "listdir": os.listdir, "scandir": os.scandir, "iterdir": pathlib.Path.iterdir}


def rec(kind, p):
    try:
        rp = Path(os.fspath(p)).resolve()
        if world.resolve() in rp.parents:
            log.append((kind, rp.relative_to(world.resolve()).as_posix()))
    except TypeError:
        pass


def _open(file, *a, **k):
    rec("open", file)
    return real["open"](file, *a, **k)


builtins.open = _open
io.open = _open
pathlib.Path.read_bytes = lambda self: (rec("read_bytes", self), real["rb"](self))[1]
pathlib.Path.read_text = lambda self, *a, **k: (rec("read_text", self), real["rt"](self, *a, **k))[1]
os.listdir = lambda p=".": (rec("listdir", p), real["listdir"](p))[1]
os.scandir = lambda p=".": (rec("scandir", p), real["scandir"](p))[1]
pathlib.Path.iterdir = lambda self: (rec("iterdir", self), real["iterdir"](self))[1]

out = Path(sys.argv[4]) if len(sys.argv) > 4 else world.parent / "spy-out"
argv = ["draw", "--kit", str(world / "kit"), "--oct9-key", str(world / "oct9" / "key.json"), "--bank-manifest",
        str(world / "bank" / "manifest.json"), "--bank", str(world / "bank" / "banks" / "dev.jsonl"), "--auditor",
        str(world / "bank" / "auditor" / "construction.json"), "--sealed", str(out / "sealed"), "--manifest",
        str(out / "m.json"), "--repo", str(world / "repo"), "--rules", str(world / "repo" / "rules.py")]
rc = main(argv)
builtins.open, io.open = real["open"], real["io_open"]
pathlib.Path.read_bytes, pathlib.Path.read_text = real["rb"], real["rt"]
os.listdir, os.scandir, pathlib.Path.iterdir = real["listdir"], real["scandir"], real["iterdir"]
print("exit", rc)
first_unit = next((n for n, (_, p) in enumerate(log) if p.startswith(("kit/retrieved/", "repo/tmp/", "kit/judges/"))),
                  len(log))
print("touched before the first unit or judge file:")
for kind, p in log[:first_unit]:
    print("  ", kind, p)
print("first unit or judge file:", log[first_unit] if first_unit < len(log) else None, "; total touches", len(log))
