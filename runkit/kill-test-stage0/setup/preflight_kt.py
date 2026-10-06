"""Run the kill-test A100 preflight on this host and record the recipe it supports (runs on the pod).

    venv/bin/python preflight_kt.py

Reads plan.json: plan["preflight_recipes"] (in preference order: sdpa mb4, sdpa mb2, eager mb2) and
plan["preflight_prepared"]. For each recipe in order, runs scripts/cuda_preflight_killtest.py into cuda-preflight-<n>/
under a process receipt, and stops at the first whose verification says verdict.use_this_recipe (the memory preflight
passed, the two-step fixture is exact and the chat rows are distinct; an out-of-memory candidate records memory_ok
false and the next one is tried). Writes PREFLIGHT-DONE.json: {ok, recipe, folder, verification_sha256, init_equals_untuned,
tried}. A host that is not the first one is given a single recipe (the first host's choice).
"""
import datetime as dt, hashlib, json, os, pathlib, subprocess

ROOT = pathlib.Path("/workspace/attribution-headroom"); os.chdir(ROOT)
plan = json.loads(pathlib.Path("plan.json").read_text())
assert json.loads(pathlib.Path("BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
assert not pathlib.Path("PREFLIGHT-DONE.json").exists(), "preflight already done"
env = {**os.environ, "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
       "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(ROOT), "HF_HUB_OFFLINE": "1"}
tried, chosen = [], None
for n, recipe in enumerate(plan["preflight_recipes"], 1):
    out = f"cuda-preflight-{n}"
    r = subprocess.run(["python3", "process_receipt.py", "--out", f"preflight-process-{n}", "--", "venv/bin/python",
                        "scripts/cuda_preflight_killtest.py", "--recipe", recipe, "--prepared", plan["preflight_prepared"],
                        "--out", out], env=env)
    v = pathlib.Path(out, "verification.json")
    verdict = json.loads(v.read_text()).get("verdict", {}) if v.exists() else {}
    tried.append({"recipe": recipe, "exit": r.returncode, "folder": out, "verdict": verdict,
                  "verification_sha256": hashlib.sha256(v.read_bytes()).hexdigest() if v.exists() else None})
    if r.returncode == 0 and verdict.get("use_this_recipe") is True:
        chosen = tried[-1]; break
done = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "ok": chosen is not None,
        "recipe": chosen["recipe"] if chosen else None, "folder": chosen["folder"] if chosen else None,
        "verification_sha256": chosen["verification_sha256"] if chosen else None,
        "init_equals_untuned": chosen["verdict"].get("init_equals_untuned") if chosen else None, "tried": tried}
pathlib.Path("PREFLIGHT-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
print(json.dumps(done), flush=True)
raise SystemExit(0 if done["ok"] else 1)
