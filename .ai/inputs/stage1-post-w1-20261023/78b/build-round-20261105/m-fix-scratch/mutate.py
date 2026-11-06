"""Apply each mutant (exact one-occurrence string replacement) to a target file in place, run pytest on the given
tests, restore the file (hash-checked). Killed = pytest exit 1 (a test failure); survived = exit 0; anything else is an
invalid run. Usage: mutate.py SPEC.json  (target, base (optional source to start from), tests, python, env, mutants)."""
import hashlib, json, os, subprocess, sys
spec = json.load(open(sys.argv[1]))
target = spec["target"]
orig = open(target, "rb").read()
start = open(spec["base"], "rb").read() if spec.get("base") else orig
h = hashlib.sha256(orig).hexdigest()
env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", **spec.get("env", {})}
results = []
try:
    for m in spec["mutants"]:
        src = start.decode()
        for old, new in m["edits"]:
            if src.count(old) != 1:
                results.append({"name": m["name"], "result": f"INVALID (pattern count {src.count(old)})"}); break
            src = src.replace(old, new)
        else:
            open(target, "w").write(src)
            p = subprocess.run([spec["python"], "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
                                "--basetemp", spec["basetemp"], *spec["tests"]], cwd=spec["cwd"], env=env,
                               capture_output=True, text=True)
            tail = [l for l in p.stdout.splitlines() if " passed" in l or " failed" in l or "error" in l.lower()][-1:]
            res = {0: "SURVIVED", 1: "KILLED"}.get(p.returncode, f"INVALID (exit {p.returncode})")
            failed = [l.split(" ")[1] for l in p.stdout.splitlines() if l.startswith("FAILED ")]
            results.append({"name": m["name"], "result": res, "tail": tail, "failed": failed})
finally:
    open(target, "wb").write(orig)
    assert hashlib.sha256(open(target, "rb").read()).hexdigest() == h, "restore failed"
for r in results:
    print(json.dumps(r))
print("restored", h)
