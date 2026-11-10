"""RV2-9 by hand under a Python without huggingface_hub: the two D6 path mutants against test_rv2_9 (by-hand paths)."""
import importlib.util, json, pathlib, subprocess, sys, os
src, scratch, py = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
spec = importlib.util.spec_from_file_location("rg", src / "runkit/stage1-78b/tests/run_mutants_gated_78b.py")
rg = importlib.util.module_from_spec(spec); spec.loader.exec_module(rg)
repo = rg.prepare(src, scratch)
kit = repo / "runkit/stage1-78b"
muts = {m["id"]: m for m in json.loads((kit / "tests/mutation_spec_gated_78b.json").read_text())["mutants"]}
env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
env["PYTHONDONTWRITEBYTECODE"] = "1"
def run(n):
    cmd = [py, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfEs", "--basetemp", str(scratch / f"pt-{n}"),
           "runkit/stage1-78b/tests/test_gated_78b.py", "-k", "rv2_9 or d6_the_cache"]
    d = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=300)
    lines = [x for x in (d.stdout + d.stderr).splitlines() if x.strip()]
    return {"exit": d.returncode, "tail": lines[-1] if lines else "", "failed": sum(x.startswith("FAILED") for x in lines)}
out = {"python": py, "baseline": run(0)}
for n, mid in enumerate(("K4-m-dl-no-expandvars", "K4-m-dl-xdg-over-hf-home"), 1):
    m = muts[mid]; f = kit / m["file"]; orig = f.read_bytes(); t = orig.decode()
    assert t.count(m["find"]) == 1
    f.write_text(t.replace(m["find"], m["replace"])); out[mid] = run(n); f.write_bytes(orig)
print(json.dumps(out, indent=1))
