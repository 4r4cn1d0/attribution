"""Write one synthetic world (hlc_world.make) under argv[1] and its pins file argv[1]/pins.json; argv[2] = rng seed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402

root = Path(sys.argv[1])
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
w = vlib.hw.make(root / "world", seed=seed)
vlib.save_pins(w, root / "pins.json")
print("world", root / "world", "seed", seed)
