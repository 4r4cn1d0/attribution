"""The lead host's work for headroom v2 (runs on the pod, after its bootstrap and preflight).

    venv/bin/python lead_pipeline.py

Runs plan["lead_steps"] in order (row scores on the chosen prepared data, the removal files, the rewrites, all edit
files, each with --count injection), each a new folder under a process receipt, stopping at the first failure. The
removal files of the early and final builds must be byte-identical. LEAD-DONE.json lists every edit file with its
SHA-256 and arm. The engine commands come from plan.json, so nothing here decides an edit.
"""
import datetime as dt, hashlib, json, os, pathlib, subprocess

ROOT = pathlib.Path("/workspace/attribution-headroom"); os.chdir(ROOT)
plan = json.loads(pathlib.Path("plan.json").read_text())
assert json.loads(pathlib.Path("BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
pre = json.loads(pathlib.Path("PREFLIGHT-DONE.json").read_text())
assert pre["ok"] is True and pre["recipe"] == plan["recipe_path"], "the preflight did not pass for the plan's recipe"
assert not pathlib.Path("LEAD-DONE.json").exists(), "the lead pipeline already finished"

from experiments.safety_selection.common import code_identity  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402

assert code_identity()["sha256"] == plan["engine_sha256"], "engine code differs from the plan"
assert config_sha256(load_recipe(plan["recipe_path"])) == plan["recipe_sha256"], "recipe differs from the plan"
prepared = plan["lead_prepared"]
assert pathlib.Path(prepared, "manifest.sha256").read_text().strip() == plan["prepared"][prepared]
env = {**os.environ, "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
       "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(ROOT), "HF_HUB_OFFLINE": "1"}


def sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


for step in plan["lead_steps"]:
    subprocess.run(["python3", "process_receipt.py", "--out", step["receipt"], "--", "venv/bin/python", "-m",
                    "experiments.safety_selection", *step["args"]], env=env, check=True)
early, final = pathlib.Path(plan["early_edits_dir"]), pathlib.Path(plan["final_edits_dir"])
files = {}
for name in plan["edit_files"]:
    path = final / name
    files[name] = {"path": str(path), "sha256": sha(path), "arm": "edit-" + sha(path)}
    if (early / name).exists():
        assert sha(early / name) == files[name]["sha256"], f"{name}: the early and final builds differ"
record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "engine_sha256": plan["engine_sha256"],
          "scores_sha256": sha(plan["scores_file"]), "rewrites_sha256": sha(plan["rewrites_file"]), "edit_files": files}
pathlib.Path("LEAD-DONE.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record), flush=True)
