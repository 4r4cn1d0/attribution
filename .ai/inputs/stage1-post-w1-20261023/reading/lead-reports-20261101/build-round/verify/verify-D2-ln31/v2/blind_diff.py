"""Blinding check by difference: two synthetic worlds that differ only in one block-A unit's outcomes (S1 1103's
Qwen3Guard safety labels: Unsafe share 0.05 against 0.60, same invalid answers, same HarmBench labels, same
over-refusal answers; every other unit's random stream unchanged). The tool draws each in its own process. With every
64-hex and 16-hex value and every path masked, the committed manifest and the printed lines must be identical: any
remaining difference is a value that depends on one arm's outcome.

    python -B blind_diff.py WORKDIR
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v2lib  # noqa: E402
import hlc_world as hw  # noqa: E402

ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
work = Path(sys.argv[1])


def spec(u: float) -> hw.Spec:
    rng = np.random.default_rng(77)
    base = hw.spec_of(rng, 0.3)
    flip = np.random.default_rng(5)
    harm = []
    for (p, k, valid, safety, cats, reason, tokens, stop) in base.harm:
        if valid and safety in ("Unsafe", "Safe"):
            safety = "Unsafe" if flip.random() < u else "Safe"
            cats = ["Violent"] if safety == "Unsafe" else []
        harm.append((p, k, valid, safety, cats, reason, tokens, stop))
    return hw.Spec(harm, dict(base.hb), dict(base.benign))


out = {}
for name, u in (("low", 0.004), ("high", 0.60)):
    root = work / f"blind-{name}"
    shutil.rmtree(root, ignore_errors=True)
    w = hw.make(root / "world", seed=4, crafted={"S1 1103": spec(u)})
    (root / "pins.json").write_text(json.dumps(v2lib.world_pins(w)))
    sealed, manifest = root / "world" / "repo" / "tmp" / "hlc" / "d", root / "m.json"
    r = subprocess.run([v2lib.PY, "-B", str(HERE / "cli.py"), str(root / "pins.json"),
                        *v2lib.tool_args(root, "draw", sealed, manifest)], env=ENV, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    mask = lambda s: re.sub(r"[0-9a-f]{64}|[0-9a-f]{16}", "H", s.replace(str(root), "ROOT"))  # noqa: E731
    out[name] = {"manifest": mask(manifest.read_text()), "stdout": mask(r.stdout),
                 "key_unsafe_S1_1103": sum(1 for i in json.loads((sealed / "hlc_key.json").read_text())["items"]
                                           if i["unit"] == "S1 1103" and i["cell"] == "Unsafe")}
same_m = out["low"]["manifest"] == out["high"]["manifest"]
same_o = out["low"]["stdout"] == out["high"]["stdout"]
print("S1 1103 Unsafe items drawn (sealed key): low", out["low"]["key_unsafe_S1_1103"], "high",
      out["high"]["key_unsafe_S1_1103"])
print("masked manifest identical:", same_m, "| masked stdout identical:", same_o)
if not (same_m and same_o):
    import difflib
    for kind in ("manifest", "stdout"):
        for line in difflib.unified_diff(out["low"][kind].splitlines(), out["high"][kind].splitlines(), lineterm="",
                                         n=0):
            print(kind, line[:200])
for name in ("low", "high"):
    shutil.rmtree(work / f"blind-{name}", ignore_errors=True)
sys.exit(0 if same_m and same_o else 1)
