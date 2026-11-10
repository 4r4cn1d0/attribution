"""A scratch source root: every WS top-level entry linked (not scripts, .git), every WS/scripts entry linked except
scale78b (copied, no caches); the given spec replaces the copy's mutation spec; extra test files are copied in."""
import shutil, sys
from pathlib import Path
ws, src, spec = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
extras = [Path(p) for p in sys.argv[4:]]
if src.exists():
    raise SystemExit("exists")
(src / "scripts").mkdir(parents=True)
for e in sorted(ws.iterdir()):
    if e.name not in ("scripts", ".git"):
        (src / e.name).symlink_to(e.resolve())
for e in sorted((ws / "scripts").iterdir()):
    if e.name == "scale78b":
        shutil.copytree(e, src / "scripts" / "scale78b", symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))
    else:
        (src / "scripts" / e.name).symlink_to(e.resolve())
oext = src / "scripts/scale78b/tests/oext"
shutil.copy(spec, oext / "mutation_spec_oext_78b.json")
for x in extras:
    shutil.copy(x, oext / x.name)
print("ok", src)
