"""Keys and hashes only of the committed G1 record (no non-hash values printed)."""
import json, sys, hashlib, re
HEX = re.compile(r"^[0-9a-f]{64}$")
def walk(o, pre=""):
    if isinstance(o, dict):
        for k, v in sorted(o.items()):
            walk(v, f"{pre}.{k}" if pre else k)
    elif isinstance(o, list):
        print(f"{pre} = <list {len(o)}>")
        for i, v in enumerate(o[:12]):
            walk(v, f"{pre}[{i}]")
    elif isinstance(o, str) and HEX.match(o):
        print(f"{pre} = {o}")
    else:
        print(f"{pre} = <{type(o).__name__}>")
for f in sys.argv[1:]:
    b = open(f, "rb").read()
    print("==", f.split("/")[-1], hashlib.sha256(b).hexdigest(), len(b), "bytes")
    walk(json.loads(b))
