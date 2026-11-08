"""The maker takes a B+Qi config whose generation block differs from MAIN_F's (it checks G's blocks, not B+Qi's); the
derived oext_unit_y pins MAIN_F's blocks, so the unchanged 1B check_recipe refuses that config at run time.
Usage: PY -B rv_bqi_blocks.py WS"""
import copy, json, sys
from pathlib import Path
ws = Path(sys.argv[1]); sys.path.insert(0, str(ws))
from scripts.scale78b import make_oext_settings_78b as mk
from scripts.stage1_s1 import oext_unit as ou
from experiments.safety_selection.config import config_sha256, load_recipe
g16 = ws / "experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-g16-20261008.json"
pins, _ = mk.load_pins(); pins = copy.deepcopy(pins)
pins["families"]["olmo2-7b"]["recipe_bqi"] = {"name": g16.stem, "config_sha256": config_sha256(load_recipe(g16))}
try:
    files = mk.derive_all(pins)
    print("maker: accepted a B+Qi config with another generation block")
except Exception as exc:
    print("maker: refused", type(exc).__name__, exc); sys.exit(0)
y = json.loads(files[mk.file_name("oext_unit_y", "olmo2-7b")])
try:
    ou.check_recipe(g16, ou.Settings(y, "0" * 64))
    print("1B check_recipe: accepted")
except Exception as exc:
    print("1B check_recipe:", type(exc).__name__, str(exc)[:120])
# the same config as recipe G: the maker refuses (the G check)
pins2, _ = mk.load_pins(); pins2 = copy.deepcopy(pins2)
pins2["families"]["olmo2-7b"]["recipe_g"] = dict(pins["families"]["olmo2-7b"]["recipe_bqi"])
try:
    mk.derive_all(pins2); print("maker (as G): accepted")
except Exception as exc:
    print("maker (as G): refused:", str(exc)[:100])
