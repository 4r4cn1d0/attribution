import json, sys
d = json.load(open(sys.argv[1]))
for name, p in sorted(d["tool"]["packages"].items()):
    print(f"{name}=={p['version']} --hash=sha256:{p['sha256']}")
