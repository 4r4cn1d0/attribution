import hashlib, json, pathlib, sys
m2, out, *spec = sys.argv[1:]
m = json.loads(pathlib.Path(m2).read_text())
out = pathlib.Path(out)
d = json.loads(out.read_text()) if out.is_file() else {}
p = d.get("provenance") if isinstance(d.get("provenance"), dict) else {}
sha = lambda q: hashlib.sha256(pathlib.Path(q).read_bytes()).hexdigest()
B16 = "scripts/stage1_s1/reading/"

def tree(prefix):   # the manifest's top-level *.py of one package, less the names B16's _strip drops
    return {k[len(prefix):]: v for k, v in m["files"].items() if k.startswith(prefix) and k.endswith(".py")
            and "/" not in k[len(prefix):] and not k[len(prefix):].startswith("_")}

b16 = {**tree(B16), "settings/reading.json": m["files"][B16 + "settings/reading.json"]}
c = {"file": out.is_file()}
for item in spec:
    key, _, val = item.partition("=")
    if key == "kind":
        c["kind"] = d.get("kind") == val
    elif key == "reading":
        c["reading"] = d.get("reading") == val
    elif key == "b16self":
        c["modules"] = p.get("modules") == b16
        c["settings_sha256"] = p.get("settings_sha256") == b16["settings/reading.json"]
    elif key == "b16":
        c["b16_modules"] = p.get("b16_modules") == b16
        c["b16_settings_sha256"] = p.get("b16_settings_sha256") == b16["settings/reading.json"]
    elif key == "modules":
        folder, _, names = val.partition(":")
        want = tree(folder) if names == "*" else {n: m["files"][folder + n] for n in names.split(",")}
        c["modules"] = p.get("modules") == want
    elif key.startswith("input:"):
        c[key] = (p.get("inputs") or {}).get(key[6:]) == sha(val)
    elif key == "kit":
        k = p.get("kit") if isinstance(p.get("kit"), dict) else {}
        seals = k.get("seals") if isinstance(k.get("seals"), dict) else {}
        c["kit"] = (k.get("plan_sha256") == m["kit"]["plan_json_sha256"] and set(seals) == {"A", "B"}
                    and all(seals[b] == m["kit"][f"seal_{b}"] for b in ("A", "B")))
    else:
        c[key] = p.get(key) == sha(val)
c["python_numpy"] = [p.get("python"), p.get("numpy")] == [m["python"]["python"], m["python"]["numpy"]]
ok = all(c.values())
print(json.dumps({**c, "pass": ok}, sort_keys=True))
sys.exit(0 if ok else 1)
