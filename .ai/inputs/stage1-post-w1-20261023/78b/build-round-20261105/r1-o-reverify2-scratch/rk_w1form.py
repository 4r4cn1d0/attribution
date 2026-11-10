"""W1_18_78B's printed form against K1's current RK (ws-k): files_form_problem on the whole form and on its files part."""
import importlib.util, json, sys
from pathlib import Path
wsk, form = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())
spec = importlib.util.spec_from_file_location("rk_k1", wsk / "runkit/stage1-78b/rules_78b.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("whole form:", m.files_form_problem(form), "| files part only:", m.files_form_problem({"files": form["files"]}))
