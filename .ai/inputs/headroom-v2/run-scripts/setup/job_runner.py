"""One headroom-v2 job on one host (runs on the pod, after its bootstrap and preflight).

    venv/bin/python job_runner.py HOST

Checks, in order, stopping at the first failure:
  - BOOTSTRAP-READY.json and PREFLIGHT-DONE.json say ok, and the preflight's recipe is the plan's recipe;
  - this host's two-step fixture equals the expected fixture recorded on the first host (expected-fixture-v2.json, sent
    by the operator): plan["fixture_compare"] keys and resume keys;
  - engine code, recipe and the host's prepared manifest equal the plan;
  - for an edit arm, the edit file sent to this host has the planned SHA-256.
Then one development calibrate of the host's (arm, seed) on its prepared data, evaluated at e3 only, and the engine's
own verify of every sealed unit. JOB-DONE.json records the outcome.
"""
import datetime as dt, hashlib, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path("/workspace/attribution-headroom"); os.chdir(ROOT)
plan = json.loads(pathlib.Path("plan.json").read_text()); host = sys.argv[1]; job = plan["hosts"][host]
assert job["role"] in ("job", "first"), "not a job host"
assert not pathlib.Path("JOB-DONE.json").exists(), "this host already ran its job"
assert json.loads(pathlib.Path("BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
pre = json.loads(pathlib.Path("PREFLIGHT-DONE.json").read_text())
assert pre["ok"] is True and pre["recipe"] == plan["recipe_path"], "the preflight did not pass for the plan's recipe"
x = json.loads(pathlib.Path(pre["folder"], "verification.json").read_text())
e = json.loads(pathlib.Path("expected-fixture-v2.json").read_text())
for key in plan["fixture_compare"]["equal_keys"]:
    assert x[key] == e[key], f"fixture differs from the first host's: {key}"
for key in plan["fixture_compare"]["resume_keys"]:
    assert x["resume"][key] == e["resume"][key], f"fixture differs from the first host's: resume.{key}"

from experiments.safety_selection.common import code_identity  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402

assert code_identity()["sha256"] == plan["engine_sha256"], "engine code differs from the plan"
assert config_sha256(load_recipe(plan["recipe_path"])) == plan["recipe_sha256"], "recipe differs from the plan"
prepared = job["prepared"]
assert pathlib.Path(prepared, "manifest.sha256").read_text().strip() == plan["prepared"][prepared], "prepared data differ from the plan"
env = {**os.environ, "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
       "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(ROOT), "HF_HUB_OFFLINE": "1"}
args = ["calibrate", "--prepared", prepared, "--recipe", plan["recipe_path"], "--seeds", str(job["seed"]),
        "--checkpoints", ",".join(plan["checkpoints"]), "--out-root", "round1"]
if job.get("edit"):
    edit = pathlib.Path("edits") / job["edit"]
    digest = hashlib.sha256(edit.read_bytes()).hexdigest()
    assert digest == job["edit_sha256"], "the edit file is not the planned one"
    args += ["--arms", "edit-" + digest, "--edit", str(edit)]
else:
    args += ["--arms", job["arm"]]
run = subprocess.run(["python3", "process_receipt.py", "--out", f"job-process-{job['seed']}", "--", "venv/bin/python", "-m",
                      "experiments.safety_selection", *args], env=env)
verified = {}
for unit in sorted(p.parent for p in pathlib.Path("round1").glob("*/COMPLETE.json")):
    check = subprocess.run(["venv/bin/python", "-m", "experiments.safety_selection", "verify", "--run", str(unit),
                            "--prepared", prepared], env=env, capture_output=True, text=True)
    verified[unit.name] = {"exit": check.returncode, "tail": (check.stdout + check.stderr)[-600:]}
done = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "host": host, "calibrate_exit": run.returncode,
        "verified": verified, "ok": run.returncode == 0 and bool(verified) and all(v["exit"] == 0 for v in verified.values())}
pathlib.Path("JOB-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
print(json.dumps(done), flush=True)
sys.exit(0 if done["ok"] else 1)
