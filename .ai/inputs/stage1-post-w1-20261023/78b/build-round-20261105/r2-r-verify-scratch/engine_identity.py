"""Re-compute engine X's identity by code_identity()'s rule (experiments/safety_selection/common.py:31-36) without
importing the engine: SHA-256 of every experiments/safety_selection/*.py (top level only, tests excluded) and of the 7
reused minimal_safety modules; canonical JSON = sort_keys, indent 2, ensure_ascii False, trailing newline."""
import hashlib, json, sys
from pathlib import Path
root = Path(sys.argv[1])
pkg, reused = root / "experiments/safety_selection", root / "experiments/minimal_safety"
REUSED = ("__init__.py", "common.py", "data.py", "ledger.py", "model.py", "plan.py", "text.py")
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
files = {f"safety_selection/{p.name}": h(p) for p in sorted(pkg.glob("*.py"))}
files.update({f"minimal_safety/{n}": h(reused / n) for n in REUSED})
blob = (json.dumps(files, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
print(len(files), hashlib.sha256(blob).hexdigest())
print("tests in identity:", any("test" in k for k in files), "configs in identity:", any("config" in k and k.endswith(".json") for k in files))
