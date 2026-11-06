"""Print the JSON key paths in each given JSON file whose value contains one of the given hex prefixes.

Usage: findhash.py PREFIX[,PREFIX...] FILE [FILE...]. Prints key paths and the full 64-hex value only, never other
string values (so no text is printed even if a file held some).
"""
import json
import re
import sys

prefixes = sys.argv[1].split(",")
HEX = re.compile(r"[0-9a-f]{64}")


def walk(obj, path, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, path + [str(k)], out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, path + [str(i)], out)
    elif isinstance(obj, str):
        for h in HEX.findall(obj):
            for p in prefixes:
                if h.startswith(p):
                    out.append((p, ".".join(path), h))


for f in sys.argv[2:]:
    try:
        data = json.load(open(f, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"{f}: not JSON ({type(e).__name__})")
        continue
    out = []
    walk(data, [], out)
    for p, kp, h in out:
        print(f"{f.split('/attribution/')[-1].split('/b78/')[-1]} :: {kp} = {h}")
    found = {p for p, _, _ in out}
    for p in prefixes:
        if p not in found:
            print(f"{f.split('/attribution/')[-1].split('/b78/')[-1]} :: (no {p})")
