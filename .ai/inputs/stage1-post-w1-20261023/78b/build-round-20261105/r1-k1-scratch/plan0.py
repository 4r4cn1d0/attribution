"""Block 0's plan.json bytes from one kit tree's test World, with the clock fixed and the tmp path normalised.
usage: plan0.py KIT_DIR WORK_DIR"""
import hashlib, importlib.util, sys, pathlib, shutil
kit = pathlib.Path(sys.argv[1]).resolve(); work = pathlib.Path(sys.argv[2])
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("t_runkit_plan0", kit / "tests" / "test_stage1_runkit.py")
mod = importlib.util.module_from_spec(spec); sys.path.insert(0, str(kit / "tests")); spec.loader.exec_module(mod)
from _pytest.monkeypatch import MonkeyPatch
for fam in ("olmo2-7b", "llama31-8b"):
    tmp = work / fam
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    mp = MonkeyPatch()
    try:
        w = mod.World(tmp, mp, fam)
        mp.setattr(w.mac, "utc", lambda: "2026-11-08T00:00:00+00:00")
        w.init()
        data = (w.root / "plan.json").read_bytes().replace(str(tmp).encode(), b"<TMP>")
        print(fam, len(data), hashlib.sha256(data).hexdigest())
    finally:
        mp.undo()
        for name in mod.MODULES: sys.modules.pop(name, None)
