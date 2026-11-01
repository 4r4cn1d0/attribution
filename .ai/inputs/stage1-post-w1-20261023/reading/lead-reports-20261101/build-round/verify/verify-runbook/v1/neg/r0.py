import hashlib, json, pathlib, subprocess, sys
root, m2, kit, py = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
m = json.loads(m2.read_text())
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
git = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True).stdout.strip()
differ = sorted(rel for rel, h in m["files"].items() if not (root / rel).is_file() or sha(root / rel) != h)
trees = {t: git("rev-parse", f"HEAD:{t}") for t in m["git"]["trees"]}
dirty = git("status", "--porcelain", "--", "scripts", "runkit", "experiments/safety_selection")
kit_now = {"plan_json_sha256": sha(kit / "plan.json"), "seal_A": sha(kit / "seals" / "block-A.json"),
           "seal_B": sha(kit / "seals" / "block-B.json")}
ver = subprocess.run([py, "-I", "-B", "-c", "import platform, numpy; print(platform.python_version(), numpy.__version__)"],
                     capture_output=True, text=True, check=True).stdout.split()
c = {"files_differ": differ, "trees_same": trees == m["git"]["trees"], "code_clean": not dirty,
     "kit_same": kit_now == m["kit"], "python_same": ver == [m["python"]["python"], m["python"]["numpy"]]}
ok = not differ and c["trees_same"] and c["code_clean"] and c["kit_same"] and c["python_same"]
print(json.dumps({**c, "pass": ok}, sort_keys=True))
sys.exit(0 if ok else 1)
