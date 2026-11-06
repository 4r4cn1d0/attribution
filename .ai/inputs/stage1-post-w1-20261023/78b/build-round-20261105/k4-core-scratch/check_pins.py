import ast, hashlib, json, pathlib, sys, re
root = pathlib.Path(sys.argv[1]); mroot = pathlib.Path(sys.argv[2])
src = (root/"runkit/stage1-78b/stage1_rules.py").read_text()
tree = ast.parse(src)
# extract SCORER_PINS dict literal with names resolved
env = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name):
        n = node.targets[0].id
        if n in ("WRAPPER","ANCHOR_SCRIPT","SCORER_SETTINGS","PINS_78B","PINS_INDEX","SCORER_PINS"):
            code = compile(ast.Expression(node.value), "x", "eval")
            env[n] = eval(code, {}, env)
pins = env["SCORER_PINS"]
bad = 0
for p, h in pins.items():
    a = hashlib.sha256((root/p).read_bytes()).hexdigest()
    m = (mroot/p)
    mh = hashlib.sha256(m.read_bytes()).hexdigest() if m.is_file() else None
    if a != h or (mh is not None and mh != h):
        bad += 1; print("MISMATCH", p, h[:12], a[:12], (mh or "none")[:12])
print("pins", len(pins), "bad", bad)
# every file in scripts/scale78b/settings and scale78b dir that wrapper may read
settings = sorted(str(p.relative_to(root)) for p in (root/"scripts/scale78b/settings").glob("*.json"))
missing = [s for s in settings if s not in pins]
print("settings files not pinned:", missing)
# wrapper literals
w = (root/"scripts/scale78b/scorers_78b.py").read_text()
lits = dict(re.findall(r'"(scripts/stage1/[A-Za-z0-9_./]+)":\s*"([0-9a-f]{64})"', w))
print("wrapper STAGE1 literals:", len(lits))
for p, h in lits.items():
    if pins.get(p) != h: print("LITERAL DIFF", p, h[:12], (pins.get(p) or "none")[:12])
m = re.search(r'PINS_FILE_SHA256\s*=\s*"([0-9a-f]{64})"', w); print("PINS_FILE_SHA256", m.group(1)[:12], pins[env["PINS_INDEX"]][:12])
idx = json.loads((root/env["PINS_INDEX"]).read_text())
print("index keys", sorted(idx)[:10])
for k, v in (idx.get("files") or {}).items():
    if pins.get(k) != v: print("INDEX DIFF", k)
print("index pins_78b", idx.get("pins_78b_sha256","")[:12], pins[env["PINS_78B"]][:12])
