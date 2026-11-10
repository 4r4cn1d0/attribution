"""Track O's printed forms against RK's oext_form_problem: WS's (3481d85) and K1's (ws-k, R-5 form with family and
engine). Usage: PY -B rk_forms.py WS WSK SCRATCH"""
import importlib.util, json, sys
from pathlib import Path
ws, wsk, s = (Path(a) for a in sys.argv[1:4])
def rk(root, name):
    spec = importlib.util.spec_from_file_location(name, root / "runkit/stage1-78b/rules_78b.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
a, b = rk(ws, "rk_ws"), rk(wsk, "rk_k1")
for fam in ("olmo2-7b", "llama31-8b"):
    for eng in ("X", "Y"):
        form = json.loads((s / f"form-{eng.lower()}-{fam}.json").read_text())
        print(fam, eng, "WS RK:", a.oext_form_problem(form), "| K1 RK (family, engine):", b.oext_form_problem(form, fam, eng),
              "| index paths:", [p for p in form["files"] if "OEXT-78B" in p])
