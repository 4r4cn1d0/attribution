"""Hand mutants on scripts/scale78b files in the scratch copy (never the worktree). Each: find text exactly once, apply,
run the given tests (pytest -x), restore, re-hash. KILLED only on exit 1 with a FAILED line and no ERROR line."""
import hashlib, json, os, subprocess, sys, pathlib
repo, spec, out = pathlib.Path(sys.argv[1]), json.loads(pathlib.Path(sys.argv[2]).read_text()), pathlib.Path(sys.argv[3])
py, tests = sys.argv[4], sys.argv[5:]
env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
def run(n):
    d = subprocess.run([py, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "-rfE", "--basetemp",
                        str(out.parent / f"bt-mut-{n}"), *tests], cwd=repo, env=env, capture_output=True, text=True, timeout=500)
    failed = [l for l in d.stdout.splitlines() if l.startswith("FAILED")]
    errors = [l for l in d.stdout.splitlines() if l.startswith("ERROR")]
    return {"exit": d.returncode, "failed": failed[:3], "errors": errors[:3], "tail": d.stdout.splitlines()[-1:]}
results = {"baseline": run(0), "mutants": []}
assert results["baseline"]["exit"] == 0, results["baseline"]
for n, m in enumerate(spec, 1):
    f = repo / m["file"]; orig = f.read_bytes(); text = orig.decode()
    if text.count(m["find"]) != 1:
        results["mutants"].append({"id": m["id"], "verdict": "invalid"}); continue
    f.write_bytes(text.replace(m["find"], m["replace"]).encode())
    r = run(n); f.write_bytes(orig)
    assert hashlib.sha256(f.read_bytes()).hexdigest() == hashlib.sha256(orig).hexdigest()
    v = "killed" if r["exit"] == 1 and r["failed"] and not r["errors"] else ("survived" if r["exit"] == 0 else "invalid")
    results["mutants"].append({"id": m["id"], "verdict": v, **r})
    print(m["id"], v, r["failed"][:1])
out.write_text(json.dumps(results, indent=1))
