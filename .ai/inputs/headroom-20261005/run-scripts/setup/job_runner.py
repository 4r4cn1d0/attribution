"""One round-1 job on one host (runs on the pod, after its bootstrap and preflight).

    venv/bin/python job_runner.py HOST

Checks, in order, stopping at the first failure:
  - the bootstrap receipt exited 0 and PREFLIGHT-DONE.json says ok;
  - this host's two-step fixture equals the expected fixture recorded on the lead host
    (expected-fixture-hr.json, sent by the operator): sources, manifest, recipe, and the direct-run
    fingerprints and losses, as in the 2 October fixture check;
  - engine code, recipe and prepared manifest equal the plan;
  - for an edit arm, the edit file sent to this host has the planned SHA-256.
Then one development calibrate of the host's (arm, seed), evaluated at e3 only (the frozen reading uses e3;
the engine's resume exactness makes the e3 state the same with or without intermediate units), and the
engine's own verify of every sealed unit. JOB-DONE.json records the outcome.
"""
import datetime as dt, hashlib, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path("/workspace/attribution-headroom"); os.chdir(ROOT)
plan = json.loads(pathlib.Path("plan.json").read_text()); host = sys.argv[1]; job = plan["hosts"][host]
assert job["role"] == "job", "not a job host"
assert not pathlib.Path("JOB-DONE.json").exists(), "this host already ran its job"
receipt = json.loads(pathlib.Path("worker-bootstrap-process-001/process-receipt.json").read_text())
assert receipt["exit_code"] == 0, "bootstrap did not succeed"
assert json.loads(pathlib.Path("PREFLIGHT-DONE.json").read_text())["ok"] is True, "preflight did not pass"
x = json.loads(pathlib.Path("cuda-preflight-hr-001/verification.json").read_text())
e = json.loads(pathlib.Path("expected-fixture-hr.json").read_text())
for key in plan["fixture_compare"]["equal_keys"]:
    assert x[key] == e[key], f"fixture differs from the lead host's: {key}"
for key in plan["fixture_compare"]["resume_keys"]:
    assert x["resume"][key] == e["resume"][key], f"fixture differs from the lead host's: resume.{key}"

from experiments.safety_selection.common import code_identity  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402

assert code_identity()["sha256"] == plan["engine_sha256"], "engine code differs from the plan"
assert config_sha256(load_recipe(plan["recipe_path"])) == plan["recipe_sha256"], "recipe differs from the plan"
assert pathlib.Path(plan["prepared_path"], "manifest.sha256").read_text().strip() == plan["manifest_sha256"]
env = {**os.environ, "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
       "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(ROOT), "HF_HUB_OFFLINE": "1"}
args = ["calibrate", "--prepared", plan["prepared_path"], "--recipe", plan["recipe_path"], "--seeds", str(job["seed"]),
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
                            "--prepared", plan["prepared_path"]], env=env, capture_output=True, text=True)
    verified[unit.name] = {"exit": check.returncode, "tail": (check.stdout + check.stderr)[-600:]}
done = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "host": host, "calibrate_exit": run.returncode,
        "verified": verified, "ok": run.returncode == 0 and bool(verified) and all(v["exit"] == 0 for v in verified.values())}
pathlib.Path("JOB-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
print(json.dumps(done), flush=True)
sys.exit(0 if done["ok"] else 1)
