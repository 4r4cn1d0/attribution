import json, sys, hashlib
def walk(d, pre=""):
    for k, v in sorted(d.items()):
        p = f"{pre}.{k}" if pre else k
        if isinstance(v, dict):
            walk(v, p)
        else:
            if isinstance(v, str):
                s = v if (len(v) == 64 and all(c in "0123456789abcdef" for c in v)) or v.startswith(("scripts/", "experiments/", "tmp/", "banks/")) or len(v) <= 24 else f"<text {len(v)} chars>"
            elif isinstance(v, list):
                s = f"<list {len(v)}>" if any(isinstance(x, str) and len(x) > 40 for x in v) else v
            else:
                s = v
            print(f"{p} = {s}")
for f in sys.argv[1:]:
    print("==", f.split("/")[-1], hashlib.sha256(open(f, "rb").read()).hexdigest()[:16])
    walk(json.load(open(f)))
