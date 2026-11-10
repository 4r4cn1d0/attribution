"""C3 re-check: generation and guard block hashes of the 7-8B configs against the 1B O-ext pins (hashes only)."""
import sys
from pathlib import Path
WS = Path(sys.argv[1]); sys.path.insert(0, str(WS))
from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from experiments.safety_selection.config import config_sha256, load_recipe
import json
oxu = json.loads((WS / "scripts/stage1_s1/settings/oext_unit.json").read_bytes())["recipes"]
for rel in ["study-kt-olmo2-7b-r64-b-mb2-20261008.json", "study-kt-olmo2-7b-r64-g-mb2-20261011.json",
            "study-kt-llama31-8b-r64-b5e5-mb2-20261010.json", "study-kt-llama31-8b-r64-g-mb2-20261011.json"]:
    p = WS / "experiments/safety_selection/configs" / rel
    r = load_recipe(p)
    g = sha256_bytes(canonical_json(r["generation"])); u = sha256_bytes(canonical_json(r["guard"]))
    print(rel, "config", config_sha256(r)[:16], "file", sha256_file(p)[:16], "gen==", g == oxu["generation_sha256"],
          "guard==", u == oxu["guard_sha256"], "harm_samples" in r["generation"], "lr", r.get("training", {}).get("learning_rate"))
