"""The lead host's work for round 1 (runs on the pod, after its bootstrap and preflight).

    venv/bin/python lead_pipeline.py

In order, each step a new folder and a process receipt, stopping at the first failure:
  1. score-rows: the guard's Unsafe score of every edit-pool row             -> scores-001/scores.json
  2. build-edits (round-1 removal files, from the scores only)               -> edits-remove-001/
  3. generate-rewrites over the top 10% and the random 10% rows              -> rewrites-001/rewrites.json
  4. build-edits (all round-1 files, with the rewrites)                       -> edits-round1-001/
The removal files of steps 2 and 4 must be byte-identical (checked). LEAD-DONE.json lists every round-1 edit
file with its SHA-256 and arm. The engine commands come from plan.json, so nothing here decides an edit.
"""
import datetime as dt, hashlib, json, os, pathlib, subprocess

ROOT = pathlib.Path("/workspace/attribution-headroom"); os.chdir(ROOT)
plan = json.loads(pathlib.Path("plan.json").read_text())
assert json.loads(pathlib.Path("PREFLIGHT-DONE.json").read_text())["ok"] is True, "preflight did not pass"
assert not pathlib.Path("LEAD-DONE.json").exists(), "the lead pipeline already finished"

from experiments.safety_selection.common import code_identity  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402

assert code_identity()["sha256"] == plan["engine_sha256"], "engine code differs from the plan"
assert config_sha256(load_recipe(plan["recipe_path"])) == plan["recipe_sha256"], "recipe differs from the plan"
assert pathlib.Path(plan["prepared_path"], "manifest.sha256").read_text().strip() == plan["manifest_sha256"]
env = {**os.environ, "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
       "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(ROOT), "HF_HUB_OFFLINE": "1"}


def sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def engine(receipt: str, args: list) -> None:
    subprocess.run(["python3", "process_receipt.py", "--out", receipt, "--", "venv/bin/python", "-m",
                    "experiments.safety_selection", *args], env=env, check=True)


for step in plan["lead_steps"]:
    engine(step["receipt"], step["args"])
    pathlib.Path(f"{step['receipt']}/STEP-DONE.json").write_text(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat()}) + "\n")

early, final = pathlib.Path(plan["early_edits_dir"]), pathlib.Path(plan["final_edits_dir"])
files = {}
for name in plan["round1_edit_files"]:
    path = final / name
    files[name] = {"path": str(path), "sha256": sha(path), "arm": "edit-" + sha(path)}
    if (early / name).exists():
        assert sha(early / name) == files[name]["sha256"], f"{name}: the early and final builds differ"
record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "engine_sha256": plan["engine_sha256"],
          "scores_sha256": sha(plan["scores_file"]), "rewrites_sha256": sha(plan["rewrites_file"]), "edit_files": files}
pathlib.Path("LEAD-DONE.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record), flush=True)
