"""For each (seed, kind) world: make it, draw with the tool's command line at the given steps (each in its own
process), compare with ref2 (its own process), then delete the world. Prints one line per draw.

    python -B batch.py WORKDIR STEPS SEED:KIND [SEED:KIND ...]       e.g. batch.py /x 0,3 0:plain 1:lowu
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

sys.path.insert(0, str(HERE))
import v2lib  # noqa: E402

work = Path(sys.argv[1])
steps = sys.argv[2].split(",")
fails = 0
for spec in sys.argv[3:]:
    seed, kind = spec.split(":")
    root = work / f"w-{seed}-{kind}"
    if root.exists():
        shutil.rmtree(root)
    r = subprocess.run([PY, "-B", str(HERE / "mkworld.py"), str(root), seed, kind], env=ENV, capture_output=True,
                       text=True)
    if r.returncode:
        print(spec, "mkworld failed", r.returncode, r.stderr[-800:])
        fails += 1
        continue
    for step in steps:
        sealed = root / "world" / "repo" / "tmp" / "hlc" / f"draw-{step}"
        manifest = root / f"manifest-{step}.json"
        d = subprocess.run([PY, "-B", str(HERE / "cli.py"), str(root / "pins.json"),
                            *v2lib.tool_args(root, "draw", sealed, manifest, step)], env=ENV, capture_output=True,
                           text=True)
        if d.returncode:
            print(spec, "step", step, "tool exit", d.returncode, d.stderr.strip()[-600:])
            fails += 1
            continue
        c = subprocess.run([PY, "-B", str(HERE / "ref2.py"), str(root), str(sealed), step], env=ENV,
                           capture_output=True, text=True)
        tail = c.stdout.strip().splitlines()
        print(spec, "step", step, "ref exit", c.returncode, "|", " / ".join(tail[-3:]) if tail else c.stderr[-800:])
        if c.returncode:
            print(c.stdout[-3000:], c.stderr[-2000:])
            fails += 1
    shutil.rmtree(root)
print("FAILURES", fails)
sys.exit(1 if fails else 0)
