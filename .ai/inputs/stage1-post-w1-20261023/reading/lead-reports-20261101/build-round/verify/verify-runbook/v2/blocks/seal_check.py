import hashlib, json, pathlib, sys
kit, blocks = pathlib.Path(sys.argv[1]), sys.argv[2:]
plan = json.loads((kit / "plan.json").read_text())
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
out, ok = {}, True
for b in blocks:
    entry = plan["seals"][b]
    seal = kit / entry["path"]
    if sha(seal) != entry["sha256"]:
        out[b], ok = {"seal_file": "not at plan.json's SHA-256"}, False
        continue
    doc = json.loads(seal.read_text())
    c = {"listed": 0, "same": 0, "differs": 0, "missing": 0}
    for f in doc["files"]:
        base = kit / "judges" / b if f["host"] == f"judges/{b}" else kit / "retrieved" / f["host"] / "tree"
        q = base / f["path"]
        c["listed"] += 1
        if not q.is_file():
            c["missing"] += 1
        elif sha(q) == f["sha256"]:
            c["same"] += 1
        else:
            c["differs"] += 1
    out[b] = c
    ok = ok and c["differs"] == 0 and c["missing"] == 0
print(json.dumps({"blocks": out, "pass": ok}, sort_keys=True))
sys.exit(0 if ok else 1)
