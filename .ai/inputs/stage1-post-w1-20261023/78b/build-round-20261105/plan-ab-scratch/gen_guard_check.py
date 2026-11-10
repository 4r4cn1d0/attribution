import sys, json
from pathlib import Path
M = Path(sys.argv[1]); sys.path.insert(0, str(M))
from experiments.safety_selection.config import load_recipe, config_sha256
from experiments.safety_selection.common import canonical_json, sha256_bytes
oxu = json.loads((M/"scripts/stage1_s1/settings/oext_unit.json").read_text())["recipes"]
print("1B pins: generation", oxu["generation_sha256"][:16], "guard", oxu["guard_sha256"][:16])
for fam, p in [("olmo2-7b","experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json"),
               ("llama31-8b","experiments/safety_selection/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json"),
               ("olmo2-7b G","experiments/safety_selection/configs/study-kt-olmo2-7b-r64-g-mb2-20261011.json"),
               ("llama31-8b G(1e-4)","experiments/safety_selection/configs/study-kt-llama31-8b-r64-g-mb2-20261011.json")]:
    r = load_recipe(M/p)
    g = sha256_bytes(canonical_json(r["generation"])); u = sha256_bytes(canonical_json(r["guard"]))
    print(fam, "config", config_sha256(r)[:16], "generation", g[:16], g==oxu["generation_sha256"], "guard", u[:16], u==oxu["guard_sha256"])
