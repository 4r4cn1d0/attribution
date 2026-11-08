"""Print a settings file's structure: keys; hex/int/bool/null values; short identifier-like strings; other strings by length."""
import json, re, sys
HEX = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9_./:\-#{}*+()\[\]\\^$|?]{1,140}$")
def show(v, ind=0):
    p = "  " * ind
    if isinstance(v, dict):
        for k, x in v.items():
            if isinstance(x, (dict, list)) and x:
                print(f"{p}{k}:"); show(x, ind + 1)
            else:
                print(f"{p}{k}: {leaf(x)}")
    elif isinstance(v, list):
        if all(not isinstance(x, (dict, list)) for x in v):
            print(f"{p}[{', '.join(leaf(x) for x in v)}]")
        else:
            for i, x in enumerate(v):
                print(f"{p}- [{i}]"); show(x, ind + 1)
def leaf(x):
    if isinstance(x, str):
        if HEX.match(x): return "hex:" + x[:16]
        if IDENT.match(x): return repr(x)
        return f"<text {len(x)}>"
    return json.dumps(x)
for f in sys.argv[1:]:
    print("=====", f); show(json.load(open(f)))
