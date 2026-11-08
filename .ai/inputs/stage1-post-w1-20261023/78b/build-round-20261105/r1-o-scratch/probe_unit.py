import sys, shutil, time
from pathlib import Path
WS = Path(sys.argv[1]); base = Path(sys.argv[2])
for p in (WS / "scripts/scale78b/tests/oext",):
    sys.path.insert(0, str(p))
import conftest  # noqa: path setup
import oext78_fixtures as f
t = time.time()
if base.exists(): shutil.rmtree(base)
env = f.unit_world(base, "128")
print("world", round(time.time() - t, 1))
_, _, doc = f.put_unit_settings(env)
out = base / "out"
args = f.unit_args(env, out, run=env.world.units["evaluated"])
code, so, se = f.wrapper(env, ["unit", "--family", f.FAMILY, *args], loaders=f.uf.loaders())
print("wrapper", code, se[-400:])
(out).rename(base / "out-wrapper")
code2, so2, se2 = f.direct_unit(env, args, doc)
print("direct", code2, se2[-300:])
res = f.compare(base / "out-wrapper", out, set())
print({k: v for k, v in res.items()})
print("stdout equal", so == so2)
print(round(time.time() - t, 1))
